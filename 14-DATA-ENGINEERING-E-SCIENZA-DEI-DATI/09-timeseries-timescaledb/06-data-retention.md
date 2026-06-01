# Data Retention e Lifecycle Management

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-06  
> Versione: 1.0.0  
> Stato: draft

## Indice
1. Retention Policy
2. Drop Chunks e Gestione Manuale
3. Tiered Storage
4. Retention e Continuous Aggregate
5. Conformità GDPR e Cancellazione Selettiva

---

## 1. Retention Policy

### 1.1 Concetto e Funzionamento

Una retention policy in TimescaleDB è una regola automatica che elimina periodicamente i chunk più vecchi di una soglia configurabile. L'eliminazione avviene a livello di chunk — non di singole righe — il che la rende estremamente efficiente: il sistema rilascia i file fisici del chunk in modo atomico senza dover scansionare milioni di righe e senza generare dead tuples che richiederebbero poi un VACUUM.

```sql
-- Aggiungi retention policy: elimina dati più vecchi di 1 anno
SELECT add_retention_policy('telemetria_sensori',
    drop_after => INTERVAL '1 year');

-- Retention con data assoluta (meno comune, utile per migrazioni)
SELECT add_retention_policy('telemetria_storico',
    drop_after => TIMESTAMPTZ '2025-01-01');

-- Visualizza le policy attive
SELECT
    hypertable_name,
    config->>'drop_after'    AS drop_after,
    schedule_interval,
    next_start
FROM timescaledb_information.jobs j
WHERE proc_name = 'policy_retention'
ORDER BY next_start;

-- Rimozione di una policy
SELECT remove_retention_policy('telemetria_sensori');
```

### 1.2 Interazione con Chunk Parziali

La retention policy elimina solo i chunk il cui **intero intervallo temporale** è più vecchio della soglia. Un chunk che copre da ieri a oggi non viene eliminato anche se parte dei suoi dati supera la soglia. Questo è corretto: si vuole eliminare solo i chunk completamente "scaduti".

Il vantaggio è che la policy è sicura da applicare: non rischia mai di eliminare dati che potrebbero ancora essere parzialmente recenti. Lo svantaggio è che l'ultimissimo chunk nel periodo di retention viene mantenuto fino al suo completamento naturale.

---

## 2. Drop Chunks e Gestione Manuale

### 2.1 drop_chunks

La funzione `drop_chunks()` è lo strumento per la gestione manuale della retention. Permette di specificare una soglia temporale e opzionalmente un nome di schema.

```sql
-- Elimina tutti i chunk più vecchi di 6 mesi
SELECT drop_chunks('telemetria_sensori', INTERVAL '6 months');

-- Preview: visualizza i chunk che verrebbero eliminati
SELECT chunk_schema, chunk_name, range_start, range_end,
       pg_size_pretty(total_bytes) AS size
FROM timescaledb_information.chunks
WHERE hypertable_name = 'telemetria_sensori'
  AND range_end < NOW() - INTERVAL '6 months'
ORDER BY range_start;

-- Drop con range esplicito
SELECT drop_chunks('telemetria_sensori',
    older_than => TIMESTAMPTZ '2025-06-01',
    newer_than => TIMESTAMPTZ '2024-01-01'
);
```

### 2.2 Archiviazione Prima del Drop

In molti contesti di produzione, non si vuole semplicemente eliminare i dati — si vuole archiviarli su storage a lungo termine (S3, GCS, Azure Blob) prima di rimuoverli dal database. Il pattern tipico prevede: export del chunk in formato Parquet o CSV → upload su object storage → drop del chunk.

```sql
-- Script di archiviazione (eseguito da uno script esterno o pg_cron)
-- Passo 1: Export del chunk più vecchio su filesystem locale
COPY (
    SELECT * FROM telemetria_sensori
    WHERE tempo >= '2024-01-01' AND tempo < '2024-02-01'
) TO '/tmp/archivio_2024_01.csv' CSV HEADER;

-- Passo 2: (da shell) upload su S3
-- aws s3 cp /tmp/archivio_2024_01.csv s3://mio-archivio/telemetria/2024/01/

-- Passo 3: Drop del chunk una volta confermato l'upload
SELECT drop_chunks('telemetria_sensori',
    older_than => TIMESTAMPTZ '2024-02-01',
    newer_than => TIMESTAMPTZ '2023-12-31'
);
```

---

## 3. Tiered Storage

### 3.1 Tablespace per Dati Freddi

TimescaleDB supporta lo spostamento di chunk su tablespace diverse, permettendo di implementare una strategia di tiered storage dove i dati recenti (caldi) risiedono su SSD veloci e i dati storici (freddi) su storage più economico.

```sql
-- Creazione del tablespace per storage freddo
CREATE TABLESPACE storage_freddo
    LOCATION '/mnt/hdd_archivio/pgdata';

-- Spostamento manuale di chunk specifici
SELECT move_chunk(
    chunk                        => '_timescaledb_internal._hyper_1_42_chunk',
    destination_tablespace       => 'storage_freddo',
    index_destination_tablespace => 'storage_freddo'
);

-- Policy automatica di tiering
SELECT add_tiering_policy('telemetria_sensori',
    tablespace => 'storage_freddo',
    older_than => INTERVAL '3 months');

-- Verifica della distribuzione dei chunk per tablespace
SELECT
    t.spcname AS tablespace,
    COUNT(*) AS num_chunk,
    pg_size_pretty(SUM(c.total_bytes)) AS size_totale
FROM timescaledb_information.chunks c
JOIN pg_class cl ON cl.relname = c.chunk_name
JOIN pg_tablespace t ON cl.reltablespace = t.oid
WHERE c.hypertable_name = 'telemetria_sensori'
GROUP BY t.spcname;
```

---

## 4. Retention e Continuous Aggregate

### 4.1 Ordine di Applicazione

Quando si usano sia la retention policy sulla hypertable raw che una continuous aggregate, l'ordine di applicazione è critico. La retention sul raw data deve essere configurata in modo che i dati raw vengano eliminati **solo dopo** che le continuous aggregate corrispondenti sono state materializzate.

La regola pratica: il `drop_after` della retention policy deve essere maggiore del `start_offset` della continuous aggregate policy. Se la continuous aggregate viene refreshata con `start_offset = 3 days` (ricalcola gli ultimi 3 giorni), la retention non dovrebbe eliminare dati prima che siano trascorsi almeno 3 giorni.

```sql
-- Configurazione sicura: retention > start_offset della continuous aggregate
SELECT add_continuous_aggregate_policy('telemetria_oraria',
    start_offset    => INTERVAL '3 hours',
    end_offset      => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour'
);

-- Retention: elimina dopo 90 giorni (la continuous aggregate conserva i dati aggregati)
SELECT add_retention_policy('telemetria_sensori',
    drop_after => INTERVAL '90 days'
);

-- La continuous aggregate può avere una retention separata (più lunga)
SELECT add_retention_policy('telemetria_oraria',
    drop_after => INTERVAL '2 years'
);
```

---

## 5. Conformità GDPR e Cancellazione Selettiva

### 5.1 Il Problema delle Serie Temporali e il GDPR

Il GDPR impone il "diritto all'oblio": su richiesta, i dati personali di un utente devono essere eliminati. Le serie temporali pongono una sfida specifica: i dati non sono organizzati per utente ma per timestamp, quindi non esiste un chunk "per utente" da eliminare atomicamente. La cancellazione richiede di identificare e aggiornare o eliminare singole righe sparse in molti chunk, compresi quelli compressi.

```sql
-- Cancellazione selettiva per utente/dispositivo (operazione costosa!)
-- Passo 1: Decompressione dei chunk che contengono dati dell'utente target
SELECT decompress_chunk(c.chunk_schema || '.' || c.chunk_name)
FROM timescaledb_information.chunks c
WHERE c.hypertable_name = 'telemetria_sensori'
  AND c.is_compressed = TRUE
  AND EXISTS (
      SELECT 1 FROM telemetria_sensori t
      WHERE t.tempo >= c.range_start
        AND t.tempo < c.range_end
        AND t.dispositivo = 'dispositivo_utente_target'
  );

-- Passo 2: Eliminazione delle righe
DELETE FROM telemetria_sensori
WHERE dispositivo = 'dispositivo_utente_target';

-- Passo 3: Ri-compressione dei chunk modificati
SELECT compress_chunk(c.chunk_schema || '.' || c.chunk_name)
FROM timescaledb_information.chunks c
WHERE c.hypertable_name = 'telemetria_sensori'
  AND NOT c.is_compressed
  AND c.range_end < NOW() - INTERVAL '7 days';
```

### 5.2 Pseudonimizzazione come Alternativa

Per ridurre la complessità delle operazioni GDPR, si può applicare la pseudonimizzazione: sostituire l'identificativo diretto dell'utente con un token pseudonimo memorizzato in una tabella di mapping separata. Per "dimenticare" un utente, basta eliminare il mapping — i dati storici rimangono ma sono irriconducibili all'individuo.

```sql
-- Tabella di mapping pseudonimo (separata, protetta)
CREATE TABLE mapping_pseudonimi (
    utente_reale   TEXT PRIMARY KEY,
    pseudonimo     TEXT NOT NULL DEFAULT gen_random_uuid()::text,
    creato_il      TIMESTAMPTZ DEFAULT NOW()
);

-- Query: unisci pseudonimo con dati
SELECT t.tempo, t.valore
FROM telemetria_sensori t
JOIN mapping_pseudonimi m ON t.dispositivo = m.pseudonimo
WHERE m.utente_reale = 'mario.rossi@example.com';

-- Cancellazione GDPR: basta eliminare il mapping
DELETE FROM mapping_pseudonimi
WHERE utente_reale = 'mario.rossi@example.com';
-- I record in telemetria_sensori rimangono ma sono irriconducibili
```

---

*Questo documento fa parte del modulo 09 "Time Series & TimescaleDB" della Data Encyclopedia.*
