# Compressione Nativa in TimescaleDB

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-06  
> Versione: 1.0.0  
> Stato: draft

## Indice
1. Architettura della Compressione
2. Configurazione della Compressione
3. Compression Policy Automatica
4. Prestazioni e Rapporti di Compressione
5. Operazioni su Dati Compressi

---

## 1. Architettura della Compressione

### 1.1 Compressione Column-Oriented nei Chunk

La compressione di TimescaleDB trasforma i chunk da un formato **row-oriented** (come tutte le tabelle PostgreSQL ordinarie) a un formato **column-oriented**. In un chunk non compresso, ogni riga è memorizzata come un'unità: `(timestamp, device_id, valore1, valore2, valore3)` in successione sul disco. In un chunk compresso, i valori di ogni colonna sono raggruppati e memorizzati insieme: tutti i timestamp in un segmento, tutti i device_id in un altro, tutti i valore1 in un altro ancora.

Questo layout colonnare è particolarmente efficace per le serie temporali per due ragioni. Prima, le colonne temporali tendono ad avere alta ridondanza locale: timestamp successivi differiscono solo per pochi millisecondi, e algoritmi come il delta-encoding o Gorilla compression (usato da Facebook per le metriche) sfruttano questa regolarità per ottenere rapporti di compressione straordinari. Seconda, le query analitiche su serie temporali spesso accedono solo a un sottoinsieme delle colonne — aggregare `temperatura` non richiede leggere `umidita` o `pressione` — e il layout colonnare permette di leggere solo le colonne necessarie.

```sql
-- Abilitazione della compressione su una hypertable
ALTER TABLE telemetria_sensori SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'dispositivo',
    timescaledb.compress_orderby   = 'tempo DESC'
);

-- Verifica della configurazione di compressione
SELECT
    hypertable_name,
    compression_enabled,
    segmentby_columns,
    orderby_columns,
    orderby_column_direction,
    orderby_nullsfirst
FROM timescaledb_information.compression_settings;
```

### 1.2 Segment e Order: Parametri Chiave

I parametri `compress_segmentby` e `compress_orderby` determinano come i dati vengono organizzati all'interno di ogni segmento compresso. Comprendere la loro semantica è fondamentale per ottenere buone prestazioni sia in compressione che in decompressione.

`compress_segmentby` specifica le colonne su cui i dati vengono **raggruppati** prima della compressione. Se si specifica `segmentby = 'dispositivo'`, ogni segmento compresso conterrà dati di un solo dispositivo. Questo è vantaggioso quando le query filtrano frequentemente per dispositivo: durante la decompressione, TimescaleDB può leggere solo i segmenti dei dispositivi richiesti, ignorando il resto.

`compress_orderby` specifica l'ordine all'interno di ogni segmento. Di default è l'inverso del tempo (`tempo DESC`), il che è ottimale per query che leggono i dati più recenti prima. L'ordinamento migliora la compressione (valori vicini nel tempo sono simili) e la performance delle query con predicati di range temporale.

```sql
-- Configurazione ottimale per un sistema IoT con query per dispositivo
ALTER TABLE telemetria_iot SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'dispositivo,metrica',  -- un segmento per (dispositivo, metrica)
    timescaledb.compress_orderby   = 'tempo DESC'            -- più recente prima
);

-- Per dati finanziari: segmenta per strumento, ordina per tempo
ALTER TABLE tick_data SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'strumento',
    timescaledb.compress_orderby   = 'tempo DESC'
);
```

---

## 2. Configurazione della Compressione

### 2.1 Compressione Manuale di Chunk

Dopo aver abilitato la compressione sulla hypertable, è possibile comprimere manualmente singoli chunk o tutti i chunk più vecchi di un certo intervallo.

```sql
-- Compressione di un singolo chunk per nome
SELECT compress_chunk('_timescaledb_internal._hyper_1_42_chunk');

-- Compressione di tutti i chunk più vecchi di 7 giorni
SELECT compress_chunk(c.chunk_schema || '.' || c.chunk_name)
FROM timescaledb_information.chunks c
WHERE c.hypertable_name = 'telemetria_sensori'
  AND c.range_end < NOW() - INTERVAL '7 days'
  AND NOT c.is_compressed;

-- Decompressione di un chunk (per modifiche o debug)
SELECT decompress_chunk('_timescaledb_internal._hyper_1_42_chunk');
```

### 2.2 Algoritmi di Compressione per Tipo di Dato

TimescaleDB usa algoritmi diversi in base al tipo di dato della colonna:

- **TIMESTAMPTZ / timestamp**: delta encoding con compressione secondaria (differenze tra timestamp successivi, tipicamente pochi millisecondi — alta compressibilità)
- **FLOAT4 / FLOAT8**: algoritmo Gorilla (XOR-based, ideale per serie di float con variazioni lente)
- **INTEGER / BIGINT**: delta encoding con Gorilla o Simple8b per delta uniformi
- **TEXT / VARCHAR**: dictionary encoding per colonne a bassa cardinalità (come `dispositivo`, `metrica`), compressione LZ per testo arbitrario
- **BOOLEAN**: bitpacking

```sql
-- Statistiche dettagliate sulla compressione per chunk
SELECT
    chunk_name,
    pg_size_pretty(before_compression_total_bytes)  AS size_prima,
    pg_size_pretty(after_compression_total_bytes)   AS size_dopo,
    ROUND(
        (1 - after_compression_total_bytes::numeric /
             NULLIF(before_compression_total_bytes, 0)) * 100, 1
    ) AS riduzione_pct
FROM chunk_compression_stats('telemetria_sensori')
ORDER BY range_start DESC;
```

---

## 3. Compression Policy Automatica

### 3.1 Aggiunta di una Policy

Le compression policy permettono a TimescaleDB di comprimere automaticamente i chunk che superano una certa soglia di età. La policy viene eseguita periodicamente da un job in background.

```sql
-- Comprimi automaticamente i chunk più vecchi di 7 giorni
SELECT add_compression_policy('telemetria_sensori',
    compress_after => INTERVAL '7 days');

-- Verifica delle policy attive
SELECT j.job_id,
       j.application_name,
       j.schedule_interval,
       j.config,
       j.next_start
FROM timescaledb_information.jobs j
WHERE j.proc_name = 'policy_compression'
ORDER BY j.next_start;

-- Rimozione della policy
SELECT remove_compression_policy('telemetria_sensori');
```

### 3.2 Monitoraggio e Tuning dei Job

I job in background di TimescaleDB (compressione, continuous aggregate refresh, retention) sono schedulati e monitorati attraverso il framework dei job interni. È possibile visualizzare la cronologia delle esecuzioni, i tempi, e gli eventuali errori.

```sql
-- Storico delle ultime esecuzioni dei job
SELECT
    j.application_name,
    jh.started,
    jh.finished,
    jh.succeeded,
    jh.config,
    EXTRACT(EPOCH FROM (jh.finished - jh.started)) AS durata_sec
FROM timescaledb_information.job_history jh
JOIN timescaledb_information.jobs j ON jh.job_id = j.job_id
WHERE j.proc_name = 'policy_compression'
ORDER BY jh.started DESC
LIMIT 20;

-- Esecuzione manuale forzata di un job
SELECT run_job(1000);  -- job_id dalla vista jobs
```

---

## 4. Prestazioni e Rapporti di Compressione

### 4.1 Benchmark Tipici

I rapporti di compressione ottenibili con TimescaleDB dipendono fortemente dalla natura dei dati. Per serie temporali tipiche:

- **Dati di sensori IoT** (temperatura, umidità, pressione campionati ogni secondo): rapporto 15:1 - 30:1 rispetto allo storage non compresso. Un chunk da 10 GB diventa 300-700 MB.
- **Metriche di infrastruttura** (CPU%, memory%, network_bytes campionati ogni 15 secondi): rapporto 10:1 - 20:1.
- **Log strutturati** (con campi TEXT/JSONB ad alta cardinalità): rapporto 3:1 - 8:1.
- **Tick data finanziario** (prezzo, volume per strumento): rapporto 8:1 - 15:1.

```sql
-- Report di compressione complessivo sulla hypertable
SELECT
    hypertable_name,
    pg_size_pretty(SUM(before_compression_total_bytes)) AS size_originale,
    pg_size_pretty(SUM(after_compression_total_bytes))  AS size_compressa,
    ROUND(
        (1 - SUM(after_compression_total_bytes)::numeric /
             NULLIF(SUM(before_compression_total_bytes), 0)) * 100, 1
    ) AS risparmio_pct,
    COUNT(*) AS chunk_compressi
FROM chunk_compression_stats(NULL)  -- NULL = tutte le hypertable
GROUP BY hypertable_name
ORDER BY risparmio_pct DESC;
```

### 4.2 Impatto sulle Query

I chunk compressi vengono decompresso on-the-fly durante le query. La decompressione è parziale: TimescaleDB decomprime solo le colonne richieste dalla query e solo i segmenti corrispondenti ai filtri di `segmentby`. Una query che filtra per `dispositivo = 'ABC'` su una hypertable con `segmentby = 'dispositivo'` decomprimerà solo i segmenti del dispositivo ABC, ignorando completamente i dati degli altri dispositivi.

L'overhead di decompressione è tipicamente trascurabile rispetto al risparmio di I/O: leggere 300 MB compressi e decomprimerli in memoria è molto più veloce che leggere 8 GB non compressi dal disco, anche considerando il tempo CPU per la decompressione.

---

## 5. Operazioni su Dati Compressi

### 5.1 INSERT in Chunk Compressi

Quando si inserisce un record in un chunk già compresso, TimescaleDB gestisce la situazione in modo trasparente. Internamente, crea una piccola struttura "staging" non compressa adiacente al chunk compresso. Questo staging area raccoglie i nuovi inserimenti finché non viene decompresso e ri-compresso l'intero chunk da un job in background. Il comportamento è visibile nell'output delle statistiche di compressione come "partially compressed chunks".

```sql
-- Verifica chunk parzialmente compressi
SELECT
    chunk_name,
    is_compressed,
    pg_size_pretty(compressed_heap_size)    AS heap_compresso,
    pg_size_pretty(uncompressed_heap_size)  AS heap_non_compresso
FROM chunk_compression_stats('telemetria_sensori')
WHERE uncompressed_heap_size > 0
  AND is_compressed = TRUE;
```

### 5.2 UPDATE e DELETE su Dati Compressi

UPDATE e DELETE su chunk compressi richiedono la decompressione del segmento interessato, la modifica delle righe, e la ri-compressione. Questa operazione è gestita automaticamente da TimescaleDB ma è significativamente più lenta rispetto a UPDATE/DELETE su dati non compressi. Per questo motivo, l'architettura raccomandata per le serie temporali è **append-only**: non si aggiornano mai i dati storici, si inseriscono solo nuovi record.

Se si deve correggere un valore storico, la pratica raccomandata è inserire un nuovo record con un flag di "correzione" o con un campo di versione, piuttosto che modificare il record originale. Le query poi usano `DISTINCT ON` o window functions per selezionare la versione più recente di ogni osservazione.

```sql
-- Pattern per correzione di dati storici (append-only)
-- Invece di: UPDATE telemetria SET valore = 25.3 WHERE tempo = '...' AND dispositivo = 'abc'
-- Usare:
INSERT INTO telemetria_sensori (tempo, dispositivo, valore, versione, corretto)
VALUES ('2026-01-15 14:23:00+01', 'sensore-42', 25.3, 2, TRUE);

-- Query per recuperare il valore più recente per ogni (tempo, dispositivo)
SELECT DISTINCT ON (tempo, dispositivo)
    tempo, dispositivo, valore
FROM telemetria_sensori
WHERE tempo >= '2026-01-15' AND tempo < '2026-01-16'
ORDER BY tempo, dispositivo, versione DESC;
```

---

*Questo documento fa parte del modulo 09 "Time Series & TimescaleDB" della Data Encyclopedia.*
