# ClickHouse — Best Practices e Anti-Pattern

## Best Practices per la Modellazione dei Dati

### 1. Scegliere la Chiave di Ordinamento in Base alle Query Reali

La scelta di `ORDER BY` è la decisione di design più impattante. Analizzare le query effettive prima di creare la tabella.

```sql
-- SBAGLIATO: ordinamento per timestamp senza considerare i filtri più comuni
ORDER BY event_time
-- Una query WHERE user_id = 1001 legge TUTTI i granule

-- CORRETTO: i filtri più selettivi prima
ORDER BY (user_id, event_date, event_time)
-- WHERE user_id = 1001 → legge solo i granule per quel user

-- Per query miste (sia per user che per date range):
ORDER BY (event_date, user_id, event_time)
-- Compromesso: pruning efficiente per date, accettabile per user
```

### 2. Usare LowCardinality per Colonne Categoriche

```sql
-- SBAGLIATO
country     String,
device_type String,
status      String,
event_name  String

-- CORRETTO
country     LowCardinality(FixedString(2)),
device_type LowCardinality(String),
status      LowCardinality(String),
event_name  LowCardinality(String)
-- Compressione 3-5x migliore, filtri più veloci
-- Usare quando cardinality < ~10.000 valori distinti
```

### 3. Partizionamento Corretto

```sql
-- SBAGLIATO: partizioni troppo granulari
PARTITION BY toYYYYMMDD(event_time)  -- 365+ partizioni/anno, overhead eccessivo

-- SBAGLIATO: partizioni troppo grandi
PARTITION BY toYear(event_time)  -- 1 partizione/anno, nessun pruning utile

-- CORRETTO: partizioni mensili per la maggior parte dei casi
PARTITION BY toYYYYMM(event_date)  -- 12 partizioni/anno, buon pruning

-- Per volumi molto alti: settimanali
PARTITION BY toYearWeek(event_date)
```

### 4. Evitare Nullable dove Non Necessario

```sql
-- SBAGLIATO: ogni colonna Nullable aggiunge overhead (flag null separato)
value  Nullable(Float64),
status Nullable(String),

-- CORRETTO: usare valori sentinella
value   Float64 DEFAULT 0,    -- 0 = assente
status  LowCardinality(String) DEFAULT '',  -- stringa vuota = assente

-- Nullable SOLO dove il NULL ha significato semantico distinto
sensor_reading Nullable(Float32)  -- NULL = sensore offline vs 0 = valore reale
```

### 5. Codec di Compressione per Tipo di Dato

```sql
-- Timestamp monotoni (sequenze crescenti)
ts DateTime CODEC(DoubleDelta, LZ4)

-- Serie temporali float (IoT, metriche)
value Float64 CODEC(Gorilla, ZSTD(3))

-- Interi piccoli e moderati
status_code UInt16 CODEC(T64, LZ4)

-- Stringhe testuali
description String CODEC(ZSTD(9))

-- ID casuali (UUID, hash) — nessun vantaggio da codec specifici
user_id UInt64 CODEC(LZ4)  -- o semplicemente omettere = LZ4 default
```

---

## Anti-Pattern e Come Evitarli

### Anti-Pattern 1: INSERT di Righe Singole

```python
# SBAGLIATO: crea N parti su disco, merge non stare dietro
for event in stream:
    client.execute("INSERT INTO events VALUES", [event])

# CORRETTO: accumula e invia in batch
BATCH_SIZE = 50_000
buffer = []
for event in stream:
    buffer.append(event)
    if len(buffer) >= BATCH_SIZE:
        client.execute("INSERT INTO events VALUES", buffer)
        buffer.clear()
```

### Anti-Pattern 2: SELECT * su Tabelle Grandi

```sql
-- SBAGLIATO: legge tutte le 50 colonne anche se ne servono 3
SELECT * FROM events WHERE event_date = today();

-- CORRETTO: colonne esplicite
SELECT event_time, user_id, event_name, revenue
FROM events WHERE event_date = today();
```

### Anti-Pattern 3: JOIN con Tabella Distribuita a Destra

```sql
-- SBAGLIATO: ClickHouse invia un broadcast della tabella left a tutti i shard
SELECT e.*, u.name
FROM users u  -- grande, distribuita
JOIN events e ON u.user_id = e.user_id;  -- grande, distribuita

-- CORRETTO: la tabella grande a sinistra, piccola/lookup a destra
SELECT e.*, dictGet('user_dict', 'name', e.user_id) as name
FROM events_local e;  -- usa Dictionary invece del JOIN
```

### Anti-Pattern 4: OPTIMIZE TABLE FINAL in Produzione

```sql
-- SBAGLIATO in produzione: blocca e riscrive l'intera tabella
OPTIMIZE TABLE events FINAL;  -- occupa CPU/I-O per ore su tabelle grandi

-- CORRETTO: lasciare che il merge background avvenga organicamente
-- o ottimizzare solo partizioni specifiche quando necessario
OPTIMIZE TABLE events PARTITION '202401';  -- solo una partizione
```

### Anti-Pattern 5: Usare FINAL Senza Necessità

```sql
-- SBAGLIATO: FINAL forza la deduplicazione a query time, degrada performance
SELECT * FROM user_profiles FINAL;  -- O(n) scan completo

-- CORRETTO: quando possibile, usare argMax per ottenere l'ultima versione
SELECT user_id, argMax(email, updated_at) as email
FROM user_profiles
GROUP BY user_id;
```

### Anti-Pattern 6: Mutation Frequenti

```sql
-- SBAGLIATO: mutation per update frequenti riscrivono le parti
ALTER TABLE events UPDATE revenue = revenue * 1.1 WHERE event_date = today();
-- → riscrive tutte le parti della partizione di oggi

-- CORRETTO: usare ReplacingMergeTree per upsert
-- o progettare lo schema per evitare UPDATE
INSERT INTO user_state SELECT ..., now() as updated_at;
-- La versione più recente "vince" al momento del FINAL/argMax
```

---

## Checklist pre-Produzione

### Schema Design

- [ ] `ORDER BY` riflette i filtri delle query più frequenti
- [ ] Tutte le colonne categoriche usano `LowCardinality`
- [ ] Partizioni mensili o settimanali (mai giornaliere se >2 anni di dati)
- [ ] TTL configurato per la retention dei dati
- [ ] Codec di compressione appropriati per ogni tipo di dato
- [ ] Nessun `Nullable` non necessario

### Ingestione

- [ ] INSERT in batch di almeno 10.000-50.000 righe
- [ ] Async insert abilitato per client con throughput variabile
- [ ] Buffer table o Kafka engine per smoothing dei picchi

### Query

- [ ] Nessun `SELECT *` su tabelle di produzione
- [ ] Filtri sulla partition key in tutte le query
- [ ] Dictionary per lookup su dimension tables
- [ ] `GLOBAL IN`/`GLOBAL JOIN` per query distribuite

### Cluster

- [ ] ReplicatedMergeTree con ≥2 repliche per shard
- [ ] ClickHouse Keeper con 3+ nodi per quorum
- [ ] Backup giornalieri via `BACKUP ... TO S3`
- [ ] `system.query_log` abilitato e monitorato
- [ ] Alert su `unassigned_shards`, `is_readonly`, repliche in lag

### Sicurezza

- [ ] TLS abilitato su porta HTTP (8443) e nativa (9440)
- [ ] Utenti con profili di quota appropriati
- [ ] Nessun accesso diretto con utente `default` senza password
- [ ] Row-level security tramite profili con `SELECT ... WHERE tenant_id = X`

---

## Sizing dell'Infrastruttura

| Carico | CPU | RAM | Disco | Note |
|--------|-----|-----|-------|------|
| Dev/test | 4 core | 16 GB | 500 GB SSD | Singolo nodo |
| Small prod | 16 core | 64 GB | 2 TB SSD | 1 shard × 2 repliche |
| Medium prod | 32 core | 128 GB | 10 TB SSD | 2 shard × 2 repliche |
| Large prod | 64 core | 256 GB | 50 TB (NVMe) | 4+ shard × 2 repliche |

**Regola memoria**: allocare 1-2 GB RAM per shard attivo, più cache non compressa (10-20% RAM totale) e cache mark (5% RAM).

**Regola disco**: ClickHouse comprime tipicamente 5-10x. Per 1 TB di dati raw, pianificare 100-200 GB su disco. Preferire NVMe per workload con alta concorrenza di scrittura.

Seguire queste linee guida riduce i problemi operativi del 90%. Il resto del tuning è specifico per i pattern di query del singolo progetto.
