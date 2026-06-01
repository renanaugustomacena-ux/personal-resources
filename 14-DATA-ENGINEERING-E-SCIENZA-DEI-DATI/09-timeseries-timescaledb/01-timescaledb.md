# Introduzione a TimescaleDB e ai Database per Serie Temporali

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-06  
> Versione: 1.0.0  
> Stato: draft

## Indice
1. Il Problema delle Serie Temporali
2. Architettura di TimescaleDB
3. TimescaleDB vs Soluzioni Alternative
4. Installazione e Configurazione Iniziale
5. Concetti Fondamentali e Terminologia

---

## 1. Il Problema delle Serie Temporali

### 1.1 Caratteristiche dei Dati Temporali

I dati di serie temporali rappresentano una delle categorie più comuni e allo stesso tempo più problematiche nel panorama dei database moderni. Una serie temporale è, nella sua essenza, una sequenza di osservazioni ordinate temporalmente: la temperatura di un sensore rilevata ogni cinque secondi, il prezzo di un'azione registrato a ogni tick di mercato, il numero di richieste HTTP al secondo su un server web. La caratteristica definitoria è che il tempo è sia una chiave che una dimensione fondamentale dell'informazione: non si tratta di un campo tra i tanti, ma dell'asse portante attorno al quale ruota l'intero modello di accesso.

Questa natura crea sfide specifiche per i database relazionali tradizionali. PostgreSQL puro è progettato attorno al concetto di aggiornamento e lettura casuale di righe; le sue strutture di indicizzazione (B-tree) sono ottimizzate per ricerche puntuali e range scan. Le serie temporali presentano quasi sempre un pattern di scrittura monotono (i nuovi record hanno timestamp crescenti) e un pattern di lettura orientato al range temporale (dammi tutti i valori tra t1 e t2). Questa asimmetria tra il modello di accesso reale e quello per cui i RDBMS tradizionali sono ottimizzati si traduce in degrado delle prestazioni all'aumentare del volume.

Il problema di scala è altrettanto significativo. Un impianto industriale con mille sensori che campionano a 1 Hz produce 86,4 milioni di righe al giorno. Un cluster Kubernetes con cento pod che espongono cinquanta metriche ciascuno e viene campionato ogni quindici secondi produce 28,8 milioni di punti al giorno. Una piattaforma di trading che registra ogni tick di mercato per cento strumenti può superare il miliardo di eventi al giorno. PostgreSQL puro in questi scenari si scontra con limiti pratici: le tabelle diventano enormi, le query rallentano, e le operazioni di manutenzione (VACUUM, ANALYZE) impattano la disponibilità.

### 1.2 Pattern di Accesso Specifici

Le query su serie temporali seguono pattern ben precisi che differiscono significativamente dalle query OLTP tradizionali. Il pattern più comune è la **query di range temporale**: selezionare tutti i punti in un intervallo di tempo, eventualmente filtrati per uno o più tag (dispositivo, host, metrica). Queste query beneficiano enormemente del partizionamento temporale perché la maggior parte dei dati storici può essere esclusa a livello di storage prima ancora di caricarli in memoria.

Il secondo pattern comune è la **downsampling query**: aggregare dati ad alta frequenza in bucket temporali di granularità minore. Un dashboard che mostra il trend di temperatura nell'ultimo mese non ha bisogno dei valori al secondo — ha bisogno della media oraria o giornaliera. TimescaleDB offre la funzione `time_bucket()` e le **continuous aggregate** per gestire questo pattern in modo efficiente, pre-calcolando e materializzando automaticamente le aggregazioni più costose.

Il terzo pattern è il **last-value query**: recuperare l'ultimo valore noto per ogni dispositivo o chiave. Questo pattern è comune nei sistemi di monitoring (qual è lo stato corrente di ogni host?) e nei sistemi IoT (qual è la temperatura attuale di ogni sensore?). TimescaleDB gestisce questo pattern con indici specializzati e la sintassi `DISTINCT ON` in PostgreSQL che, combinata con gli indici su `(dispositivo, tempo DESC)`, risulta estremamente efficiente.

---

## 2. Architettura di TimescaleDB

### 2.1 TimescaleDB come Estensione PostgreSQL

TimescaleDB è implementato come estensione PostgreSQL (file `.so` caricato a runtime tramite `shared_preload_libraries`), non come un database separato. Questa scelta architetturale è deliberata e comporta implicazioni importanti. TimescaleDB eredita l'ecosistema PostgreSQL: compatibilità SQL completa, transazioni ACID, tutti i tipi di indice (B-tree, GIN, GiST, BRIN), stored procedure, trigger, replicazione streaming, e tutti i driver client esistenti. Non è necessario imparare un nuovo linguaggio di query né adattare le applicazioni esistenti.

L'estensione si aggancia al lifecycle di PostgreSQL attraverso i **hooks**: punti di estensione definiti nel codice sorgente di PostgreSQL che permettono alle estensioni di intercettare e modificare il comportamento del planner, dell'executor, e degli utility commands. TimescaleDB usa questi hook per intercettare le operazioni DDL (CREATE TABLE, INSERT, SELECT) sulle hypertable e trasformarle nelle operazioni appropriate sui chunk sottostanti.

### 2.2 Hypertable e Chunk

Il concetto centrale è l'**hypertable**: una tabella virtuale che appare all'utente come una normale tabella PostgreSQL ma che internamente è suddivisa in **chunk**, ognuno dei quali è una tabella PostgreSQL fisica indipendente. Ogni chunk copre un intervallo temporale definito da `chunk_time_interval`.

```sql
-- Creazione di una tabella e conversione in hypertable
CREATE TABLE metriche_sensori (
    tempo        TIMESTAMPTZ      NOT NULL,
    dispositivo  TEXT             NOT NULL,
    temperatura  DOUBLE PRECISION,
    umidita      DOUBLE PRECISION,
    pressione    DOUBLE PRECISION
);

SELECT create_hypertable('metriche_sensori', 'tempo',
    chunk_time_interval => INTERVAL '1 day');

-- Verifica dei chunk creati
SELECT chunk_schema, chunk_name, range_start, range_end
FROM timescaledb_information.chunks
WHERE hypertable_name = 'metriche_sensori'
ORDER BY range_start;
```

Ogni `INSERT` viene automaticamente instradato al chunk corrispondente. Se il chunk non esiste, TimescaleDB lo crea on-demand senza bloccare le operazioni in corso. Ogni chunk è una tabella PostgreSQL ordinaria visibile in `pg_tables` con il prefisso `_hyper_` e può essere gestita indipendentemente: compressa, spostata su tablespace diverse, eliminata in modo atomico.

### 2.3 Chunk Exclusion e Ottimizzazione Query

Il meccanismo di **chunk exclusion** è la chiave delle prestazioni di TimescaleDB. Quando si esegue una query con un predicato temporale, il planner di PostgreSQL — grazie ai metadati di partizionamento gestiti da TimescaleDB — può escludere staticamente tutti i chunk fuori dall'intervallo di interesse prima di iniziare l'esecuzione. Questo significa che una query su una settimana di dati in una tabella con due anni di storia non toccherà mai i chunk al di fuori di quella settimana.

```sql
-- Questa query scansiona solo i chunk rilevanti per la finestra temporale
EXPLAIN (ANALYZE, BUFFERS)
SELECT time_bucket('1 hour', tempo) AS ora,
       dispositivo,
       AVG(temperatura) AS temp_media
FROM metriche_sensori
WHERE tempo >= NOW() - INTERVAL '7 days'
  AND dispositivo = 'sensore-42'
GROUP BY 1, 2
ORDER BY 1;

-- L'output EXPLAIN mostrerà "Chunks excluded by runtime exclusion: N"
-- dove N è il numero di chunk saltati dall'esecutore
```

La distinzione tra **static chunk exclusion** (a compile time del piano) e **runtime chunk exclusion** (durante l'esecuzione per predicati parametrizzati) è importante: la prima avviene per predicati con costanti letterali, la seconda per predicati con parametri ($1, prepared statements). TimescaleDB 2.x gestisce entrambi i casi in modo ottimale.

### 2.4 Partizionamento Spaziale

Oltre al partizionamento temporale primario, TimescaleDB supporta un partizionamento secondario su una colonna aggiuntiva, tipicamente un identificatore di dispositivo o sensore. Questo partizionamento permette di distribuire i dati dello stesso intervallo temporale su chunk diversi in base al valore della seconda dimensione.

```sql
-- Hypertable con doppio partizionamento: tempo + hash del dispositivo
SELECT create_hypertable('metriche_sensori', 'tempo',
    partitioning_column => 'dispositivo',
    number_partitions    => 4,
    chunk_time_interval  => INTERVAL '1 day');
```

Il partizionamento spaziale è principalmente utile in ambienti **TimescaleDB distribuiti** (multi-nodo) dove permette di distribuire fisicamente i dati su nodi diversi. In un deployment single-node, aggiunge overhead amministrativo senza benefici evidenti nella maggior parte dei casi ed è generalmente sconsigliato a meno di esigenze specifiche di parallelizzazione.

---

## 3. TimescaleDB vs Soluzioni Alternative

### 3.1 TimescaleDB vs InfluxDB

InfluxDB è il database time-series più diffuso, nato nativamente per questo scopo. InfluxDB 2.x e 3.x usano un modello dati basato su "measurements", "fields" e "tags" — fondamentalmente diverso dal modello relazionale. Il motore di storage nativo (TSM in InfluxDB 1.x, Apache Parquet-based in InfluxDB 3.x IOx) è ottimizzato esclusivamente per serie temporali e offre throughput di ingestione e compressione superiori a TimescaleDB su carichi puri.

Lo svantaggio principale di InfluxDB è la rottura con il mondo SQL. Flux (il linguaggio di InfluxDB 2.x) è potente ma richiede un apprendimento significativo, e la compatibilità con i tool BI (Grafana con datasource SQL, Metabase, Superset) e gli ORM esistenti è limitata. InfluxDB 3.x ha reintrodotto SQL come linguaggio principale, avvicinandosi a TimescaleDB, ma resta un database specializzato senza la generalità di PostgreSQL.

**Quando preferire InfluxDB:** ingestione di milioni di punti al secondo su un singolo nodo, team già formato su InfluxQL/Flux, ecosistema Telegraf già in uso, carichi puramente time-series senza necessità di JOIN con tabelle relazionali.

**Quando preferire TimescaleDB:** organizzazione con competenze PostgreSQL esistenti, necessità di correlare serie temporali con dati anagrafici tramite JOIN, requisiti di conformità che richiedono transazioni ACID complete, utilizzo di ORM/librerie che parlano SQL standard.

### 3.2 TimescaleDB vs Prometheus

Prometheus è un sistema di monitoring e alerting, non un database a uso generale. Il suo storage TSDB locale è ottimizzato per metriche di monitoring a granularità di secondi/minuti con retention breve (giorni/settimane). La forza di Prometheus è nell'integrazione con l'ecosistema Kubernetes/cloud-native, nel modello di scraping pull-based, e in PromQL.

TimescaleDB e Prometheus si usano tipicamente **insieme**: Prometheus come front-end di raccolta metriche in real-time, TimescaleDB come backend per retention a lungo termine e query analitiche. Il connettore Promscale (ora deprecato) e l'adapter `remote_write` verso TimescaleDB realizzano questo pattern. In alternativa, la stack completa con Victoria Metrics o Thanos offre soluzioni simili.

### 3.3 TimescaleDB vs QuestDB

QuestDB è un database time-series scritto in Java e C++ con focus estremo sulle prestazioni. Il suo motore column-oriented e le strutture di indicizzazione specializzate permettono throughput di ingestione nell'ordine di milioni di righe al secondo su hardware commodity. QuestDB supporta un sottoinsieme di SQL con estensioni time-series native (`SAMPLE BY`, `LATEST ON`).

Il vantaggio di QuestDB è puramente prestazionale per carichi estremi. Lo svantaggio è un ecosistema più giovane, funzionalità transazionali più semplici, e un sottoinsieme SQL non completo. Per la maggior parte delle applicazioni industriali e di monitoring, TimescaleDB offre il miglior bilanciamento tra prestazioni e ricchezza funzionale.

---

## 4. Installazione e Configurazione Iniziale

### 4.1 Installazione su Linux

```bash
# Ubuntu 22.04/24.04 con PostgreSQL 16
sudo apt install -y gnupg postgresql-common apt-transport-https lsb-release wget
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh

# Repository TimescaleDB
echo "deb https://packagecloud.io/timescale/timescaledb/ubuntu/ \
  $(lsb_release -c -s) main" \
  | sudo tee /etc/apt/sources.list.d/timescaledb.list
wget --quiet -O - \
  https://packagecloud.io/timescale/timescaledb/gpgkey | sudo apt-key add -

sudo apt update
sudo apt install -y timescaledb-2-postgresql-16

# Tuning automatico del postgresql.conf
sudo timescaledb-tune --quiet --yes

sudo systemctl restart postgresql
```

### 4.2 Docker

```yaml
# docker-compose.yml
services:
  timescaledb:
    image: timescale/timescaledb:latest-pg16
    environment:
      POSTGRES_PASSWORD: password_sicura
      POSTGRES_DB: telemetria
    ports:
      - "5432:5432"
    volumes:
      - timescale_data:/var/lib/postgresql/data
    command: >
      postgres
      -c shared_preload_libraries=timescaledb
      -c timescaledb.max_background_workers=8

volumes:
  timescale_data:
```

### 4.3 Attivazione dell'Estensione

```sql
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Verifica versione installata
SELECT extversion FROM pg_extension WHERE extname = 'timescaledb';

-- Parametri di configurazione importanti
SHOW timescaledb.max_background_workers;
SHOW timescaledb.telemetry_level;

-- Disabilita telemetry in ambienti privati
ALTER SYSTEM SET timescaledb.telemetry_level = 'off';
SELECT pg_reload_conf();
```

---

## 5. Concetti Fondamentali e Terminologia

### 5.1 Glossario Operativo

**chunk_time_interval**: la dimensione temporale di ogni chunk. La regola pratica consiglia di scegliere un intervallo tale che ogni chunk comprima circa il 25% della RAM disponibile. Con 16 GB di RAM e 100 MB/ora di ingestione: `4 GB / 100 MB/ora = 40 ore → interval di 1 giorno`.

**Continuous aggregate**: vista materializzata incrementale specifica di TimescaleDB. Equivale a un `GROUP BY time_bucket(...)` pre-calcolato che si aggiorna automaticamente in modo incrementale al variare dei dati sottostanti. Fondamentale per dashboard real-time su grandi volumi.

**Retention policy**: regola automatica di eliminazione dei chunk più vecchi di una soglia. Lavora a livello di chunk (eliminazione atomica) senza impattare le operazioni sugli altri chunk. Meccanismo preferito per TTL su serie temporali.

**Compression policy**: regola automatica di compressione dei chunk più vecchi di una soglia. La compressione converte il formato row-oriented del chunk in formato column-oriented, tipicamente ottenendo rapporti di compressione del 90%+.

### 5.2 Schema di Produzione Completo

```sql
-- Schema IoT production-ready
CREATE TABLE telemetria_iot (
    tempo        TIMESTAMPTZ        NOT NULL,
    dispositivo  TEXT               NOT NULL,
    metrica      TEXT               NOT NULL,
    valore       DOUBLE PRECISION   NOT NULL,
    qualita      SMALLINT           DEFAULT 100 CHECK (qualita BETWEEN 0 AND 100),
    metadati     JSONB
);

-- Hypertable con 1 giorno per chunk
SELECT create_hypertable('telemetria_iot', 'tempo',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists       => TRUE);

-- Indici per i pattern di query più comuni
CREATE INDEX ON telemetria_iot (dispositivo, metrica, tempo DESC);
CREATE INDEX ON telemetria_iot (metrica, tempo DESC) 
    WHERE qualita >= 90;  -- indice parziale per dati di qualità

-- Policy di compressione: comprimi chunk più vecchi di 7 giorni
ALTER TABLE telemetria_iot SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'dispositivo,metrica',
    timescaledb.compress_orderby   = 'tempo DESC'
);
SELECT add_compression_policy('telemetria_iot', INTERVAL '7 days');

-- Policy di retention: elimina dati più vecchi di 1 anno
SELECT add_retention_policy('telemetria_iot', INTERVAL '1 year');

-- Verifica dello stato complessivo
SELECT * FROM timescaledb_information.hypertable_detailed_size('telemetria_iot');
SELECT * FROM timescaledb_information.jobs
WHERE application_name LIKE '%telemetria_iot%';
```

---

*Questo documento fa parte del modulo 09 "Time Series & TimescaleDB" della Data Encyclopedia.*

---

## 6. TimescaleDB Internal Architecture

### 6.1 Write Path

When an INSERT arrives at a hypertable, TimescaleDB intercepts it via PostgreSQL hooks:

1. **Chunk routing**: The timestamp value is extracted and mapped to the appropriate chunk. If the chunk does not exist, it is created atomically.
2. **Index maintenance**: Each chunk maintains its own local indexes. The B-tree on `(device, time DESC)` is local to the chunk, keeping index size manageable.
3. **WAL writing**: The INSERT is written to PostgreSQL's Write-Ahead Log for durability.
4. **Visibility**: MVCC visibility rules apply per-chunk, same as regular PostgreSQL tables.

```sql
-- Observe the write path with EXPLAIN
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
INSERT INTO telemetria_iot (tempo, dispositivo, metrica, valore)
VALUES (NOW(), 'sensor-42', 'temperature', 23.5);
-- Shows: Insert on _hyper_X_Y_chunk
```

### 6.2 Read Path and Chunk Exclusion

```sql
-- Static chunk exclusion (constant predicate)
EXPLAIN (ANALYZE, COSTS OFF)
SELECT * FROM telemetria_iot
WHERE tempo >= '2026-01-01' AND tempo < '2026-01-08';
-- Output shows: "Chunks excluded: N"

-- Runtime chunk exclusion (parameterized query)
PREPARE recent_data AS
SELECT * FROM telemetria_iot
WHERE tempo >= $1 AND tempo < $2 AND dispositivo = $3;

EXPLAIN (ANALYZE, COSTS OFF)
EXECUTE recent_data('2026-01-01', '2026-01-08', 'sensor-42');
-- Runtime exclusion also prunes irrelevant chunks
```

### 6.3 Background Workers

TimescaleDB uses PostgreSQL background workers for automated tasks:

```sql
-- View active background worker jobs
SELECT * FROM timescaledb_information.jobs
ORDER BY next_start;

-- Job types:
-- Policy: compression     — compresses old chunks
-- Policy: retention       — drops expired chunks  
-- Policy: reorder         — physically reorders chunk data
-- Policy: continuous_agg  — refreshes materialized views
-- Telemetry               — sends anonymous usage stats (can disable)

-- Manually run a job
CALL run_job(1001);  -- job_id from the jobs view

-- Alter job schedule
SELECT alter_job(1001, schedule_interval => INTERVAL '1 hour');
```

---

## 7. Advanced Configuration

### 7.1 postgresql.conf Tuning for TimescaleDB

```properties
# Core settings (timescaledb-tune sets these automatically)
shared_buffers = '8GB'                    # 25% of RAM
effective_cache_size = '24GB'             # 75% of RAM
work_mem = '64MB'                         # per-operation sort memory
maintenance_work_mem = '2GB'              # for VACUUM, CREATE INDEX
max_worker_processes = 16                 # total background workers
max_parallel_workers_per_gather = 4       # parallel query workers
max_parallel_workers = 8                  # total parallel workers

# TimescaleDB specific
timescaledb.max_background_workers = 8    # for policies (compress, retain, cagg)
timescaledb.max_insert_batch_size = 1000  # batch INSERT optimization
timescaledb.telemetry_level = 'off'       # disable telemetry in production

# WAL settings for high-ingest workloads
wal_level = 'replica'
max_wal_size = '4GB'
min_wal_size = '1GB'
wal_compression = 'lz4'
checkpoint_timeout = '15min'
checkpoint_completion_target = 0.9

# Connection pooling (use pgbouncer for >100 connections)
max_connections = 100
```

### 7.2 Chunk Size Tuning by Workload

| Workload | Ingest Rate | Recommended Interval | Chunk Size |
|----------|-------------|---------------------|------------|
| IoT (1K sensors, 1Hz) | ~500 MB/day | 7 days | ~3.5 GB |
| Monitoring (10K metrics, 15s) | ~2 GB/day | 3 days | ~6 GB |
| Financial ticks (100 instruments) | ~5 GB/day | 1 day | ~5 GB |
| Log aggregation | ~20 GB/day | 12 hours | ~10 GB |

```sql
-- Check actual chunk sizes to verify tuning
SELECT
    hypertable_name,
    chunk_time_interval,
    pg_size_pretty(AVG(total_bytes)::bigint) AS avg_chunk_size,
    COUNT(*) AS num_chunks
FROM timescaledb_information.chunks c
JOIN timescaledb_information.hypertables h USING (hypertable_schema, hypertable_name)
WHERE NOT c.is_compressed
GROUP BY 1, 2;
```

---

## 8. Multi-Node TimescaleDB

### 8.1 Architecture

```
┌─────────────────────────────────┐
│         Access Node             │
│   (receives queries, routes)    │
│                                 │
│   Distributed Hypertable:       │
│   telemetria_iot                │
└──────────┬──────────┬───────────┘
           │          │
    ┌──────┴──┐  ┌───┴──────┐
    │ Data    │  │ Data     │
    │ Node 1  │  │ Node 2   │
    │ chunks  │  │ chunks   │
    │ 1,3,5.. │  │ 2,4,6.. │
    └─────────┘  └──────────┘
```

```sql
-- On the access node: add data nodes
SELECT add_data_node('dn1', host => 'data-node-1', port => 5432);
SELECT add_data_node('dn2', host => 'data-node-2', port => 5432);

-- Create distributed hypertable
SELECT create_distributed_hypertable(
    'telemetria_iot', 'tempo',
    partitioning_column => 'dispositivo',
    number_partitions => 4,
    data_nodes => ARRAY['dn1', 'dn2']
);

-- Check data distribution
SELECT * FROM timescaledb_information.data_nodes;
SELECT * FROM timescaledb_information.chunks
WHERE hypertable_name = 'telemetria_iot'
ORDER BY data_node, range_start;
```

### 8.2 Query Routing in Multi-Node

The access node pushes down predicates and aggregations to data nodes. Only results are sent back:

```sql
-- This query is pushed down to data nodes
EXPLAIN (VERBOSE)
SELECT time_bucket('1 hour', tempo) AS hora,
       AVG(valore)
FROM telemetria_iot
WHERE tempo >= NOW() - INTERVAL '1 day'
  AND dispositivo = 'sensor-42'
GROUP BY 1;
-- Plan shows: Foreign Scan on data nodes with pushed-down WHERE and GROUP BY
```

---

## 9. Connection Pooling with PgBouncer

```ini
# pgbouncer.ini for TimescaleDB
[databases]
timescaledb = host=localhost port=5432 dbname=telemetria

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction   # MUST be transaction mode for TimescaleDB
max_client_conn = 1000
default_pool_size = 50
min_pool_size = 10
reserve_pool_size = 5
server_lifetime = 3600
server_idle_timeout = 600

# Important: session mode is NOT compatible with TimescaleDB
# because hypertable operations use prepared statements
```

---

## Troubleshooting

### 1. Extension Fails to Load

**Symptom**: `ERROR: could not open extension control file "timescaledb.control"`.

**Fix**:
```bash
# Verify the package is installed
dpkg -l | grep timescaledb
# Check shared_preload_libraries
grep shared_preload_libraries /etc/postgresql/16/main/postgresql.conf
# Must include: shared_preload_libraries = 'timescaledb'
# Restart PostgreSQL after changing
sudo systemctl restart postgresql
```

### 2. Chunk Creation Extremely Slow

**Symptom**: First INSERT into a new time range takes seconds.

**Root cause**: Too many indexes on the hypertable (each chunk creates copies of all indexes).

**Fix**: Remove unnecessary indexes. For high-ingest tables, keep only essential indexes.

### 3. Query Does Not Use Chunk Exclusion

**Symptom**: EXPLAIN shows all chunks being scanned.

**Fix**: Ensure the WHERE clause references the time column directly:
```sql
-- WRONG: function on column prevents exclusion
WHERE date_trunc('day', tempo) = '2026-01-01'

-- CORRECT: range predicate enables exclusion
WHERE tempo >= '2026-01-01' AND tempo < '2026-01-02'
```

### 4. OOM During Bulk INSERT

**Symptom**: PostgreSQL OOM killer kills the process during large COPY.

**Fix**: Use `timescaledb.max_insert_batch_size` or split the COPY:
```bash
# Split large CSV into 1M row chunks
split -l 1000000 large_file.csv chunk_
for f in chunk_*; do
    psql -c "\\copy telemetria_iot FROM '$f' CSV HEADER"
done
```

### 5. Compression Policy Not Running

**Symptom**: Old chunks remain uncompressed.

**Fix**: Check the background job:
```sql
SELECT * FROM timescaledb_information.jobs
WHERE proc_name = 'policy_compression'
  AND hypertable_name = 'telemetria_iot';

-- Verify the policy exists
SELECT * FROM timescaledb_information.compression_settings
WHERE hypertable_name = 'telemetria_iot';

-- Manually compress to test
SELECT compress_chunk(chunk_name::regclass)
FROM timescaledb_information.chunks
WHERE hypertable_name = 'telemetria_iot'
  AND NOT is_compressed
  AND range_end < NOW() - INTERVAL '7 days'
ORDER BY range_start
LIMIT 1;
```

### 6. Cannot INSERT into Compressed Chunk

**Symptom**: `ERROR: insert/update/delete not permitted on compressed chunk`.

**Fix**: Decompress the chunk, perform the operation, recompress:
```sql
SELECT decompress_chunk('_timescaledb_internal._hyper_1_42_chunk');
-- Perform INSERT/UPDATE/DELETE
SELECT compress_chunk('_timescaledb_internal._hyper_1_42_chunk');
```
Note: TimescaleDB 2.11+ supports direct INSERT into compressed chunks.

### 7. High Memory Usage from Too Many Chunks

**Symptom**: PostgreSQL shared memory exhausted, connection errors.

**Root cause**: Too many small chunks creating excessive catalog entries.

**Fix**: Increase `chunk_time_interval` to reduce chunk count:
```sql
SELECT set_chunk_time_interval('telemetria_iot', INTERVAL '7 days');
-- Future chunks will be larger; existing chunks remain unchanged
```

### 8. Continuous Aggregate Refresh Fails

**Symptom**: `ERROR: cannot refresh continuous aggregate "xxx"`.

**Fix**: Check if the underlying hypertable has data in the refresh window:
```sql
SELECT * FROM timescaledb_information.continuous_aggregates
WHERE materialization_hypertable_name LIKE '%xxx%';
-- Verify refresh policy
SELECT * FROM timescaledb_information.jobs
WHERE proc_name = 'policy_refresh_continuous_aggregate';
```

### 9. timescaledb-tune Makes Wrong Recommendations

**Symptom**: Tune script sets values too high for shared VM.

**Fix**: Run with explicit memory constraint:
```bash
timescaledb-tune --memory=8GB --cpus=4 --quiet --yes
```

### 10. Data Node Unreachable in Multi-Node Setup

**Symptom**: Queries fail with `could not connect to data node`.

**Fix**: Verify network connectivity and pg_hba.conf on data nodes:
```bash
# From access node, test connectivity
psql -h data-node-1 -p 5432 -U postgres -c "SELECT 1"
# Ensure pg_hba.conf on data node allows connection from access node
```

---

## FAQ

### 1. Can I use TimescaleDB with my existing PostgreSQL application?

Yes. TimescaleDB is a PostgreSQL extension, not a separate database. Your existing tables, queries, indexes, functions, and drivers work unchanged. You only need to convert time-series tables to hypertables.

### 2. What is the maximum data volume TimescaleDB can handle?

Single-node deployments commonly handle 10-100 TB with proper compression and retention. Multi-node deployments scale to petabytes across data nodes. The practical limit is determined by hardware, chunk tuning, and query patterns.

### 3. Does TimescaleDB support UPDATE and DELETE?

Yes, full UPDATE and DELETE are supported on uncompressed chunks. Compressed chunks require decompression first (automatic in TimescaleDB 2.11+). However, time-series workloads rarely need UPDATEs — the insert-only pattern is strongly recommended.

### 4. How does TimescaleDB compare to partitioned PostgreSQL tables?

TimescaleDB automates chunk creation, adds chunk exclusion optimizations, provides compression, continuous aggregates, retention policies, and hyperfunctions. Manual PostgreSQL partitioning requires writing all this infrastructure yourself and lacks the query planner optimizations.

### 5. Can I JOIN hypertables with regular PostgreSQL tables?

Yes. Hypertables are PostgreSQL tables — all JOINs work normally. This is one of TimescaleDB's key advantages over standalone time-series databases.

### 6. What happens if I run out of disk space?

PostgreSQL will refuse new writes with `ERROR: could not write to file`. TimescaleDB does not handle disk exhaustion differently. Monitor disk usage and set retention policies proactively. Compression reduces disk usage by 90%+ for most workloads.

### 7. Is TimescaleDB open source?

TimescaleDB Community Edition is open source (Apache-2 License). The enterprise features (multi-node, tiered storage, advanced compression) require the Timescale License. Timescale Cloud is the managed service.

### 8. How do I migrate from InfluxDB to TimescaleDB?

Use the `outflux` tool (Timescale-maintained) to migrate data from InfluxDB to TimescaleDB. It reads InfluxDB measurements and writes them as hypertable rows. Schema mapping: InfluxDB tags become TEXT columns, fields become value columns.

### 9. Can I use TimescaleDB with Grafana?

Yes. Use the PostgreSQL data source in Grafana. TimescaleDB supports all PostgreSQL query syntax. Time-series queries with `time_bucket()` map directly to Grafana's time grouping. Grafana 10+ includes TimescaleDB-specific query helpers.

### 10. What is the recommended PostgreSQL version?

Use the latest stable PostgreSQL version supported by TimescaleDB. As of 2025, PostgreSQL 16 is recommended. TimescaleDB typically supports the latest 2-3 PostgreSQL major versions.

TimescaleDB transforms PostgreSQL from a general-purpose RDBMS into a competitive time-series platform by adding automatic partitioning, columnar compression, continuous aggregates, and domain-specific functions — all while preserving full SQL compatibility and the PostgreSQL ecosystem.

---

## 10. Upgrading TimescaleDB

### 10.1 Minor Version Upgrade

```bash
# Update the package
sudo apt update
sudo apt install -y timescaledb-2-postgresql-16

# Restart PostgreSQL
sudo systemctl restart postgresql

# Update the extension in each database
psql -d telemetria -c "ALTER EXTENSION timescaledb UPDATE;"
```

### 10.2 Major PostgreSQL Version Upgrade

```bash
# 1. Backup
pg_dumpall > backup_full.sql

# 2. Install new PostgreSQL + TimescaleDB
sudo apt install -y postgresql-17 timescaledb-2-postgresql-17

# 3. Use pg_upgrade
sudo pg_upgrade \
    --old-datadir=/var/lib/postgresql/16/main \
    --new-datadir=/var/lib/postgresql/17/main \
    --old-bindir=/usr/lib/postgresql/16/bin \
    --new-bindir=/usr/lib/postgresql/17/bin \
    --old-options '-c shared_preload_libraries=timescaledb' \
    --new-options '-c shared_preload_libraries=timescaledb'

# 4. Update extension
psql -d telemetria -c "ALTER EXTENSION timescaledb UPDATE;"
```

---

## 11. Security Configuration

```sql
-- Create read-only role for analytics
CREATE ROLE ts_reader LOGIN PASSWORD 'strong_password';
GRANT CONNECT ON DATABASE telemetria TO ts_reader;
GRANT USAGE ON SCHEMA public TO ts_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ts_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA _timescaledb_internal TO ts_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ts_reader;

-- Create write role for ingestion services
CREATE ROLE ts_writer LOGIN PASSWORD 'another_strong_password';
GRANT CONNECT ON DATABASE telemetria TO ts_writer;
GRANT USAGE ON SCHEMA public TO ts_writer;
GRANT INSERT ON TABLE telemetria_iot TO ts_writer;
-- No UPDATE/DELETE for ingestion service (principle of least privilege)

-- Row-Level Security for multi-tenant
ALTER TABLE telemetria_iot ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON telemetria_iot
    USING (tenant_id = current_setting('app.tenant_id')::text);
```

---

## Additional Troubleshooting

### 11. High WAL Generation During Compression

**Symptom**: WAL volume spikes during compression.

**Fix**: Schedule compression during off-peak hours and increase `max_wal_size`:
```sql
ALTER SYSTEM SET max_wal_size = '8GB';
SELECT pg_reload_conf();
```

### 12. timescaledb-tune Overrides Manual Settings

**Symptom**: Custom postgresql.conf values reset after running tune.

**Fix**: Run tune with `--dry-run` to review recommendations, then apply selectively:
```bash
timescaledb-tune --dry-run --memory=32GB --cpus=8
```

---

## Additional FAQ

### 11. Can I use TimescaleDB with Django/SQLAlchemy?

Yes. TimescaleDB is PostgreSQL — all ORM frameworks that support PostgreSQL work unchanged. For hypertable creation, use raw SQL migrations. For `time_bucket` queries, use raw SQL or custom expressions.

### 12. How do I handle late-arriving data?

TimescaleDB accepts INSERT at any timestamp. If the chunk was compressed, decompression happens automatically (2.11+). If the chunk was dropped by retention, a new chunk is created. Design continuous aggregate refresh windows to account for late data by extending `start_offset`.

### 13. What is the write throughput of TimescaleDB?

Single-node: 100K-1M rows/sec depending on hardware, batch size, and schema complexity. Multi-node: scales linearly with data nodes. Use COPY instead of INSERT for maximum throughput.

### 14. How do I export data from TimescaleDB?

Use standard PostgreSQL tools:
```bash
# CSV export
psql -c "\\copy (SELECT * FROM telemetria_iot WHERE tempo >= '2026-01-01') TO 'export.csv' CSV HEADER"
# pg_dump for schema + data
pg_dump -Fc -d telemetria > telemetria.dump
```

