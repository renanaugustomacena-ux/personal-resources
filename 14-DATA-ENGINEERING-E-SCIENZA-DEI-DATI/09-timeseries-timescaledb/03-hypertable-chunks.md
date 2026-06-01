# Hypertable, Chunk e Partizionamento

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-06  
> Versione: 1.0.0  
> Stato: draft

## Indice
1. Anatomia di una Hypertable
2. Gestione dei Chunk
3. Selezione del chunk_time_interval
4. Partizionamento Spaziale
5. Operazioni Avanzate sui Chunk

---

## 1. Anatomia di una Hypertable

### 1.1 Struttura Interna

Una hypertable TimescaleDB è una tabella PostgreSQL ordinaria dal punto di vista dell'applicazione: supporta INSERT, SELECT, UPDATE, DELETE, JOIN, indici, constraint, trigger, e qualsiasi altra funzionalità PostgreSQL. Internamente, però, ogni hypertable è associata a una serie di **chunk**: tabelle fisiche reali memorizzate nello schema `_timescaledb_internal`, ognuna corrispondente a un intervallo temporale preciso.

La mappatura tra la hypertable logica e i chunk fisici è gestita da tabelle di catalogo in `_timescaledb_catalog`. Quando arriva una query, il planner di PostgreSQL consulta questi metadati per determinare quali chunk sono rilevanti e genera un piano di esecuzione che opera solo su quei chunk. Dal punto di vista del catalogo PostgreSQL, ogni chunk è una "child table" che eredita la struttura dalla parent (la hypertable), sfruttando il meccanismo di table inheritance di PostgreSQL.

```sql
-- Visualizzazione dei chunk di una hypertable
SELECT
    c.chunk_schema,
    c.chunk_name,
    c.range_start,
    c.range_end,
    c.is_compressed,
    pg_size_pretty(c.total_bytes) AS size_totale
FROM timescaledb_information.chunks c
WHERE c.hypertable_name = 'telemetria_sensori'
ORDER BY c.range_start DESC;

-- Equivalente: query sul catalogo interno
SELECT
    h.schema_name   AS chunk_schema,
    h.table_name    AS chunk_name,
    ds.range_start,
    ds.range_end
FROM _timescaledb_catalog.chunk h
JOIN _timescaledb_catalog.chunk_constraint cc ON h.id = cc.chunk_id
JOIN _timescaledb_catalog.dimension_slice ds ON cc.dimension_slice_id = ds.id
WHERE h.hypertable_id = (
    SELECT id FROM _timescaledb_catalog.hypertable
    WHERE table_name = 'telemetria_sensori'
)
ORDER BY ds.range_start DESC;
```

### 1.2 Chunk come Tabelle PostgreSQL

Ogni chunk è una tabella PostgreSQL a tutti gli effetti. Questo ha implicazioni pratiche importanti: ogni chunk ha i suoi file fisici sul filesystem, il suo insieme di blocchi nella page cache, i suoi indici. PostgreSQL può operare su ciascun chunk in parallelo (usando parallel workers), e operazioni come `VACUUM`, `ANALYZE`, e il background writer lavorano naturalmente a livello di chunk.

Gli indici definiti sulla hypertable vengono automaticamente duplicati su ogni nuovo chunk creato. Se si aggiunge un indice alla hypertable dopo che alcuni chunk esistono già, TimescaleDB aggiunge l'indice ai chunk esistenti in background (con `CREATE INDEX CONCURRENTLY` per non bloccare le operazioni).

```sql
-- Gli indici sulla hypertable vengono propagati automaticamente ai chunk
CREATE INDEX ON telemetria_sensori (dispositivo, tempo DESC);

-- Verifica degli indici sui singoli chunk
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename LIKE '_hyper_%'
  AND indexname LIKE '%telemetria%'
ORDER BY tablename, indexname;
```

---

## 2. Gestione dei Chunk

### 2.1 Creazione e Ciclo di Vita

I chunk vengono creati automaticamente da TimescaleDB al primo INSERT nel corrispondente intervallo temporale. Non è possibile (né necessario) creare chunk manualmente in condizioni normali. Il numero di chunk attivi (non compressi) nella cache delle relazioni aperte è limitato dal parametro `timescaledb.max_open_chunks_per_insert`, il cui default varia con la versione ma è tipicamente nell'ordine di qualche centinaia.

```sql
-- Statistiche sui chunk
SELECT
    COUNT(*)                                    AS num_chunk_totali,
    SUM(CASE WHEN is_compressed THEN 1 ELSE 0 END) AS chunk_compressi,
    pg_size_pretty(SUM(total_bytes))            AS size_totale,
    pg_size_pretty(SUM(compressed_total_size))  AS size_compressa,
    MIN(range_start)                            AS chunk_piu_vecchio,
    MAX(range_end)                              AS chunk_piu_recente
FROM timescaledb_information.chunks
WHERE hypertable_name = 'telemetria_sensori';
```

### 2.2 Drop di Chunk

L'eliminazione dei chunk è l'operazione preferita per la gestione della retention dei dati nelle serie temporali. A differenza di un `DELETE` su tabella ordinaria (che lascia "dead tuples" e richiede VACUUM), il drop di un chunk elimina fisicamente i file corrispondenti dal disco in modo atomico e istantaneo.

```sql
-- Drop manuale di chunk specifici
SELECT drop_chunks('telemetria_sensori', 
    older_than => INTERVAL '1 year');

-- Drop di chunk prima di una data specifica
SELECT drop_chunks('telemetria_sensori',
    older_than => TIMESTAMPTZ '2025-01-01');

-- Drop con verifica preventiva (list chunks to drop)
SELECT chunk_schema, chunk_name, range_start, range_end,
       pg_size_pretty(total_bytes) AS size
FROM timescaledb_information.chunks
WHERE hypertable_name = 'telemetria_sensori'
  AND range_end < NOW() - INTERVAL '1 year'
ORDER BY range_start;
```

### 2.3 Spostamento di Chunk su Tablespace Diverse

TimescaleDB supporta la strategia di tiered storage: i chunk recenti (caldi) restano sul tablespace veloce (SSD NVMe), mentre i chunk più vecchi (freddi) vengono spostati su storage più economico (HDD, S3 tramite tablespace estensione).

```sql
-- Creazione di tablespace per storage freddo
CREATE TABLESPACE cold_storage LOCATION '/mnt/hdd_lento/pgdata';

-- Spostamento manuale di un chunk
SELECT move_chunk(
    chunk       => '_timescaledb_internal._hyper_1_42_chunk',
    destination_tablespace => 'cold_storage',
    index_destination_tablespace => 'cold_storage',
    reorder_index => '_hyper_1_42_chunk_tempo_idx'
);

-- Politica automatica di tiering
SELECT add_tiering_policy('telemetria_sensori',
    tablespace    => 'cold_storage',
    older_than    => INTERVAL '90 days');
```

---

## 3. Selezione del chunk_time_interval

### 3.1 Regola Pratica e Calcolo

La selezione del `chunk_time_interval` è la decisione di configurazione più impattante nelle prestazioni di TimescaleDB. Il principio guida di TimescaleDB è che ogni chunk dovrebbe occupare circa **25% della RAM disponibile** quando è attivamente in uso (per i chunk più recenti che ricevono INSERT continui). Questa regola garantisce che i chunk recenti stiano interamente nella page cache di PostgreSQL, eliminando gli I/O di lettura durante le scritture (ogni INSERT deve leggere l'indice per aggiornarlo).

```
Calcolo del chunk_time_interval ottimale:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Dimensione target del chunk  = RAM × 0.25
Rate di ingestione          = bytes/unità_tempo

chunk_time_interval = Dimensione_target / Rate_ingestione

Esempio:
  RAM = 64 GB → target = 16 GB
  Rate = 5 GB/giorno
  chunk_time_interval = 16 GB / 5 GB/giorno ≈ 3 giorni
  → Usare INTERVAL '3 days'
```

### 3.2 Impatto sulla Query Performance

Un `chunk_time_interval` troppo piccolo crea molti chunk piccoli. Il problema principale è il planning overhead: per ogni query, il planner deve enumerare tutti i chunk potenzialmente rilevanti e creare un piano di esecuzione. Con migliaia di chunk (anche se la maggior parte viene esclusa), il planning time può superare l'execution time per query su finestre temporali brevi. Inoltre, più chunk significano più file aperti sul filesystem e più entrate nel buffer pool di PostgreSQL.

Un `chunk_time_interval` troppo grande crea pochi chunk enormi. Il problema in questo caso è la perdita di granularità nella retention policy (non si può eliminare "un giorno" di dati, si deve eliminare l'intero chunk), la ridotta efficacia della compressione incrementale (un chunk di 6 mesi non si può comprimere un giorno alla volta), e potenziali problemi di lock durante la creazione del nuovo chunk.

```sql
-- Verifica della dimensione media dei chunk esistenti
SELECT
    AVG(total_bytes) / (1024^3) AS size_media_gb,
    MIN(total_bytes) / (1024^3) AS size_min_gb,
    MAX(total_bytes) / (1024^3) AS size_max_gb,
    COUNT(*) AS num_chunk
FROM timescaledb_information.chunks
WHERE hypertable_name = 'telemetria_sensori'
  AND NOT is_compressed;

-- Modifica del chunk_time_interval (applicata ai futuri chunk)
SELECT set_chunk_time_interval('telemetria_sensori', INTERVAL '7 days');
```

---

## 4. Partizionamento Spaziale

### 4.1 Quando Usare il Partizionamento Spaziale

Il partizionamento spaziale (hash partitioning su una seconda colonna) è principalmente utile in due scenari: il deployment **multi-nodo distribuito** di TimescaleDB (dove permette di distribuire i dati su nodi fisici diversi), e il caso in cui il volume di dati per unità di tempo è così elevato da rendere ogni chunk singolo troppo grande anche con il partizionamento temporale da solo.

In un deployment single-node standard, il partizionamento spaziale aggiunge overhead senza benefici concreti: crea più tabelle fisiche (un chunk per ogni combinazione intervallo-temporale × partizione-spaziale), aumenta il numero di file aperti, e complica la gestione operativa (compressione, retention, statistiche). La regola pratica è: non usare il partizionamento spaziale su single-node a meno di avere una ragione tecnica specifica documentata.

```sql
-- Partizionamento spaziale su dispositivo (4 partizioni hash)
SELECT create_hypertable(
    'telemetria_sensori',
    'tempo',
    partitioning_column => 'dispositivo',
    number_partitions   => 4,
    chunk_time_interval => INTERVAL '1 day'
);

-- Verifica della distribuzione dei chunk per partizione
SELECT
    c.chunk_name,
    c.range_start,
    c.range_end,
    ds_space.range_start AS hash_start,
    ds_space.range_end   AS hash_end
FROM timescaledb_information.chunks c
JOIN _timescaledb_catalog.chunk ch ON c.chunk_name = ch.table_name
JOIN _timescaledb_catalog.chunk_constraint cc ON ch.id = cc.chunk_id
JOIN _timescaledb_catalog.dimension_slice ds_space ON cc.dimension_slice_id = ds_space.id
WHERE c.hypertable_name = 'telemetria_sensori'
ORDER BY c.range_start, ds_space.range_start;
```

---

## 5. Operazioni Avanzate sui Chunk

### 5.1 Reorder e Clustering

Poiché i dati vengono inseriti in ordine temporale ma spesso non in ordine per altre colonne (es. dispositivo), i dati all'interno di un chunk possono essere fisicamente disorganizzati rispetto agli indici secondari. TimescaleDB può rordinare fisicamente i dati all'interno di un chunk basandosi su un indice specifico, migliorando le prestazioni delle query che filtrano per quella colonna.

```sql
-- Reorder manuale di un chunk specifico
SELECT reorder_chunk(
    chunk  => '_timescaledb_internal._hyper_1_42_chunk',
    index  => 'telemetria_sensori_dispositivo_tempo_idx'
);

-- Policy automatica di reorder per chunk vecchi
SELECT add_reorder_policy('telemetria_sensori',
    index_name => 'telemetria_sensori_dispositivo_tempo_idx');
```

### 5.2 Attach e Detach di Chunk

È possibile scollegare un chunk dalla sua hypertable (rendendolo una tabella ordinaria independente) e successivamente ricollegarlo. Questo meccanismo è utile per l'archiviazione a lungo termine: i chunk molto vecchi possono essere distaccati, spostati su storage di archivio, e eventualmente ricollegati se serve rielaborare dati storici.

```sql
-- Detach di un chunk (diventa tabella ordinaria)
SELECT detach_chunk('_timescaledb_internal._hyper_1_42_chunk');

-- Riattach di un chunk precedentemente distaccato
SELECT attach_chunk('telemetria_sensori', 
    '_timescaledb_internal._hyper_1_42_chunk');

-- Verifica della dimensione per tablespace
SELECT
    t.spcname AS tablespace,
    pg_size_pretty(SUM(pg_relation_size(c.oid))) AS size_totale
FROM pg_class c
JOIN pg_tablespace t ON c.reltablespace = t.oid
WHERE c.relname LIKE '_hyper_%'
GROUP BY t.spcname;
```

---

*Questo documento fa parte del modulo 09 "Time Series & TimescaleDB" della Data Encyclopedia.*

---

## 6. Chunk Management for High-Performance Workloads

### 6.1 Chunk Exclusion Monitoring

```sql
-- Verify chunk exclusion is working
EXPLAIN (ANALYZE, COSTS OFF, BUFFERS)
SELECT AVG(valore) FROM telemetria_sensori
WHERE tempo >= NOW() - INTERVAL '1 day';
-- Look for: "Chunks excluded by runtime exclusion: XX"

-- If too many chunks are scanned, check for functions wrapping the time column
-- These prevent exclusion:
-- BAD:  WHERE date_trunc('day', tempo) = '2026-01-01'
-- BAD:  WHERE extract(epoch FROM tempo) > 1234567890
-- GOOD: WHERE tempo >= '2026-01-01' AND tempo < '2026-01-02'
```

### 6.2 Chunk Size and Count Monitoring Dashboard

```sql
-- Comprehensive chunk health report
SELECT
    h.hypertable_name,
    COUNT(*) AS total_chunks,
    SUM(CASE WHEN c.is_compressed THEN 1 ELSE 0 END) AS compressed,
    SUM(CASE WHEN NOT c.is_compressed THEN 1 ELSE 0 END) AS uncompressed,
    pg_size_pretty(SUM(c.total_bytes)) AS total_size,
    pg_size_pretty(AVG(c.total_bytes)::bigint) AS avg_chunk_size,
    pg_size_pretty(SUM(CASE WHEN c.is_compressed THEN c.total_bytes ELSE 0 END)) AS compressed_size,
    MIN(c.range_start) AS oldest_data,
    MAX(c.range_end) AS newest_data,
    MAX(c.range_end) - MIN(c.range_start) AS data_span
FROM timescaledb_information.chunks c
JOIN timescaledb_information.hypertables h 
    ON c.hypertable_schema = h.hypertable_schema 
    AND c.hypertable_name = h.hypertable_name
GROUP BY h.hypertable_name
ORDER BY SUM(c.total_bytes) DESC;
```

### 6.3 Chunk Index Management

```sql
-- List all indexes per chunk (useful for troubleshooting)
SELECT
    c.chunk_name,
    i.indexname,
    pg_size_pretty(pg_relation_size(i.indexrelid)) AS index_size,
    i.indexdef
FROM timescaledb_information.chunks c
CROSS JOIN LATERAL (
    SELECT indexname, indexrelid::oid, indexdef
    FROM pg_indexes
    WHERE tablename = c.chunk_name
) i
WHERE c.hypertable_name = 'telemetria_sensori'
ORDER BY c.range_start DESC, i.indexname
LIMIT 20;

-- Total index overhead
SELECT
    hypertable_name,
    pg_size_pretty(SUM(index_bytes)) AS total_index_size,
    pg_size_pretty(SUM(total_bytes - table_bytes - index_bytes - toast_bytes)) AS overhead
FROM timescaledb_information.chunks
GROUP BY hypertable_name;
```

---

## 7. Distributed Hypertables

### 7.1 Multi-Node Chunk Distribution

In a multi-node setup, chunks are distributed across data nodes using the space partition dimension:

```sql
-- View chunk distribution across nodes
SELECT
    c.chunk_name,
    c.data_node,
    c.range_start,
    c.range_end,
    pg_size_pretty(c.total_bytes) AS size
FROM timescaledb_information.chunks c
WHERE c.hypertable_name = 'distributed_metrics'
ORDER BY c.range_start, c.data_node;

-- Verify balanced distribution
SELECT
    data_node,
    COUNT(*) AS num_chunks,
    pg_size_pretty(SUM(total_bytes)) AS total_data
FROM timescaledb_information.chunks
WHERE hypertable_name = 'distributed_metrics'
GROUP BY data_node;
```

### 7.2 Rebalancing Chunks

```sql
-- Move a chunk to a different data node
CALL timescaledb_experimental.move_chunk(
    chunk => '_timescaledb_internal._dist_hyper_1_42_chunk',
    source_node => 'dn1',
    destination_node => 'dn2'
);

-- Copy a chunk for redundancy
CALL timescaledb_experimental.copy_chunk(
    chunk => '_timescaledb_internal._dist_hyper_1_42_chunk',
    source_node => 'dn1',
    destination_node => 'dn2'
);
```

---

## 8. Tiered Storage Architecture

### 8.1 Hot/Warm/Cold Strategy

```
Time Axis:
  Now ←─── 7 days ───→ 90 days ────→ 1 year ────→ Archive
  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
  │   HOT    │  │   WARM   │  │   COLD   │  │ ARCHIVE  │
  │ NVMe SSD │  │ Compressed│  │ HDD/S3   │  │ Detached │
  │ Raw data │  │ Columnar  │  │ Columnar  │  │ Dumped   │
  │ Full idx │  │ Segment   │  │ Minimal   │  │ No idx   │
  └──────────┘  └──────────┘  └──────────┘  └──────────┘
```

```sql
-- Implement tiered storage
-- 1. Create tablespaces
CREATE TABLESPACE hot_storage LOCATION '/data/nvme/pgdata';
CREATE TABLESPACE cold_storage LOCATION '/data/hdd/pgdata';

-- 2. Set default tablespace for new chunks (hot)
ALTER TABLE telemetria_sensori SET TABLESPACE hot_storage;

-- 3. Compression policy (warm: 7 days → compressed)
ALTER TABLE telemetria_sensori SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'dispositivo',
    timescaledb.compress_orderby = 'tempo DESC'
);
SELECT add_compression_policy('telemetria_sensori', INTERVAL '7 days');

-- 4. Tiering policy (cold: 90 days → move to HDD)
-- Manual approach (scheduled via pg_cron)
DO $$
DECLARE chunk_rec RECORD;
BEGIN
    FOR chunk_rec IN
        SELECT chunk_schema || '.' || chunk_name AS chunk_full_name
        FROM timescaledb_information.chunks
        WHERE hypertable_name = 'telemetria_sensori'
          AND is_compressed = true
          AND range_end < NOW() - INTERVAL '90 days'
    LOOP
        EXECUTE format('ALTER TABLE %s SET TABLESPACE cold_storage', chunk_rec.chunk_full_name);
    END LOOP;
END $$;

-- 5. Retention policy (archive/delete: 1 year)
SELECT add_retention_policy('telemetria_sensori', INTERVAL '1 year');
```

---

## 9. Chunk Maintenance and VACUUM

### 9.1 Autovacuum Tuning for Hypertables

```sql
-- Per-hypertable autovacuum settings
ALTER TABLE telemetria_sensori SET (
    autovacuum_vacuum_scale_factor = 0.0,      -- disable percentage-based threshold
    autovacuum_vacuum_threshold = 100000,       -- vacuum after 100K dead tuples
    autovacuum_analyze_scale_factor = 0.0,
    autovacuum_analyze_threshold = 50000,
    autovacuum_vacuum_cost_delay = '5ms'
);

-- Monitor autovacuum on chunks
SELECT
    relname,
    n_tup_ins, n_tup_upd, n_tup_del,
    n_dead_tup, n_live_tup,
    last_vacuum, last_autovacuum,
    last_analyze, last_autoanalyze
FROM pg_stat_user_tables
WHERE relname LIKE '_hyper_%'
ORDER BY n_dead_tup DESC
LIMIT 10;
```

### 9.2 Manual Chunk Maintenance

```sql
-- VACUUM a specific chunk
VACUUM (VERBOSE) _timescaledb_internal._hyper_1_42_chunk;

-- ANALYZE to update statistics for the query planner
ANALYZE _timescaledb_internal._hyper_1_42_chunk;

-- REINDEX a specific chunk index
REINDEX INDEX CONCURRENTLY _timescaledb_internal._hyper_1_42_chunk_tempo_idx;
```

---

## Troubleshooting

### 1. create_hypertable Fails with "Not Empty"

**Symptom**: `ERROR: table is not empty` when converting existing table.

**Fix**: Use `migrate_data => true`:
```sql
SELECT create_hypertable('existing_table', 'tempo',
    chunk_time_interval => INTERVAL '1 day',
    migrate_data => true
);
```

### 2. Chunk Count Growing Too Fast

**Symptom**: Thousands of chunks created per day.

**Root cause**: `chunk_time_interval` too small for the ingest rate.

**Fix**: Increase chunk interval:
```sql
SELECT set_chunk_time_interval('telemetria_sensori', INTERVAL '7 days');
-- Only affects future chunks
```

### 3. Query Planning Time Exceeds Execution Time

**Symptom**: EXPLAIN shows planning time > execution time.

**Root cause**: Too many chunks causes planner overhead (enumerating and filtering chunks).

**Fix**: Reduce chunk count by increasing interval. Alternatively, use prepared statements to cache the plan. Target: <500 active chunks per hypertable.

### 4. INSERT Latency Spike When New Chunk Created

**Symptom**: Periodic latency spikes every `chunk_time_interval`.

**Root cause**: Creating a new chunk involves creating the table, copying indexes, and acquiring locks.

**Fix**: Pre-create chunks before they are needed:
```sql
-- Pre-create chunks for the next 7 days
SELECT _timescaledb_functions.create_chunk(
    'telemetria_sensori',
    jsonb_build_object('start', (NOW() + i * INTERVAL '1 day')::text,
                       'end', (NOW() + (i+1) * INTERVAL '1 day')::text)
)
FROM generate_series(0, 6) AS i;
```

### 5. Detached Chunk Cannot Be Re-attached

**Symptom**: `ERROR: could not find chunk` when calling `attach_chunk`.

**Fix**: The chunk must still exist as a regular table and its schema must match the hypertable exactly:
```sql
-- Verify chunk exists
SELECT * FROM pg_tables WHERE tablename = '_hyper_1_42_chunk';
-- Check column compatibility
SELECT column_name, data_type FROM information_schema.columns
WHERE table_name = '_hyper_1_42_chunk'
ORDER BY ordinal_position;
```

### 6. Tablespace Move Fails for Compressed Chunks

**Symptom**: `ERROR: cannot move compressed chunk`.

**Fix**: Decompress first, move, then recompress:
```sql
SELECT decompress_chunk('_timescaledb_internal._hyper_1_42_chunk');
ALTER TABLE _timescaledb_internal._hyper_1_42_chunk SET TABLESPACE cold_storage;
SELECT compress_chunk('_timescaledb_internal._hyper_1_42_chunk');
```

### 7. Parallel Workers Not Used on Chunks

**Symptom**: Queries scan chunks sequentially despite available parallel workers.

**Fix**: Ensure parallel query is enabled:
```sql
SET max_parallel_workers_per_gather = 4;
SET parallel_tuple_cost = 0.001;
SET parallel_setup_cost = 100;
-- Also set per table:
ALTER TABLE telemetria_sensori SET (parallel_workers = 4);
```

### 8. Space Partitioning Creates Too Many Chunks

**Symptom**: Chunk count = time_intervals x space_partitions, growing exponentially.

**Fix**: Reduce `number_partitions` or remove space partitioning entirely:
```sql
-- On single-node, space partitioning is usually unnecessary
-- Create new hypertable without space partitioning
SELECT create_hypertable('new_table', 'tempo',
    chunk_time_interval => INTERVAL '1 day');
-- Do NOT set partitioning_column
```

### 9. chunk_time_interval Change Not Taking Effect

**Symptom**: New chunks still use old interval.

**Root cause**: `set_chunk_time_interval` only affects future chunks.

**Fix**: This is expected. Existing chunks retain their original interval. The change applies to the next chunk created after the setting change.

### 10. Hypertable Shows Wrong Size

**Symptom**: `hypertable_size()` returns different value than `pg_total_relation_size()`.

**Fix**: Use TimescaleDB's own size functions:
```sql
-- Correct way to get hypertable size
SELECT * FROM hypertable_detailed_size('telemetria_sensori');
-- Shows: table_bytes, index_bytes, toast_bytes, total_bytes
-- For all chunks combined

-- Per-chunk sizes
SELECT chunk_name, pg_size_pretty(total_bytes)
FROM timescaledb_information.chunks
WHERE hypertable_name = 'telemetria_sensori'
ORDER BY total_bytes DESC LIMIT 10;
```

---

## FAQ

### 1. How many chunks should a hypertable have?

There is no hard limit, but 100-500 active (uncompressed) chunks per hypertable is the sweet spot. Beyond 1000, planner overhead becomes noticeable. Compressed and dropped chunks do not count toward this.

### 2. Can I change chunk_time_interval without recreating the hypertable?

Yes. `SELECT set_chunk_time_interval('table', INTERVAL 'new_value')` changes the interval for future chunks. Existing chunks are not affected.

### 3. What happens if I INSERT data with an old timestamp?

TimescaleDB creates a new chunk for that time range (or inserts into an existing chunk if it still exists). If the chunk was dropped by a retention policy, a new chunk is created. If the chunk was compressed, the insert decompresses the chunk (or fails on versions before 2.11).

### 4. Can chunks be on different PostgreSQL tablespaces?

Yes. Each chunk can be individually moved to a different tablespace using `move_chunk()` or `ALTER TABLE ... SET TABLESPACE`. This enables tiered storage strategies.

### 5. How does reorder_chunk work?

`reorder_chunk` physically rearranges the rows in a chunk to match the order of a specified index. This improves sequential scan performance for queries that filter on that index's columns. It requires an exclusive lock on the chunk during the operation.

### 6. Can I have multiple hypertables in one database?

Yes. Each hypertable is independent and has its own chunks, policies, and settings. There is no performance penalty for having multiple hypertables.

### 7. What is the relationship between chunks and PostgreSQL partitions?

TimescaleDB chunks are implemented using PostgreSQL's inheritance mechanism (not declarative partitioning). Each chunk is a child table inheriting from the hypertable parent. TimescaleDB manages the partitioning logic, constraint exclusion, and chunk lifecycle internally.

### 8. How do I recover a dropped chunk?

You cannot recover a dropped chunk — the data is permanently deleted. This is why retention policies should be carefully configured and tested. Always maintain backups for data you might need later.

### 9. Can I run VACUUM on the hypertable directly?

Yes. `VACUUM telemetria_sensori` will VACUUM all chunks of the hypertable. For targeted maintenance, VACUUM individual chunks by name. PostgreSQL's autovacuum also processes chunks independently.

### 10. What is the overhead of the hypertable abstraction?

Minimal for queries (the planner adds microseconds for chunk routing). For INSERTs, routing to the correct chunk adds ~1-5% overhead compared to a plain table. This is offset by the benefits of chunk exclusion, compression, and retention management.

Hypertables and chunks are the foundation of TimescaleDB's performance model. The automatic partitioning by time, combined with chunk exclusion, compression, tiered storage, and lifecycle management, transforms PostgreSQL's general-purpose storage into a time-series-optimized engine — without sacrificing SQL compatibility or transactional guarantees.

---

## 10. Dimension Builder API (TimescaleDB 2.13+)

```sql
-- Create hypertable with dimension builder for more control
CREATE TABLE metrics (
    time TIMESTAMPTZ NOT NULL,
    device_id INT NOT NULL,
    metric_name TEXT NOT NULL,
    value DOUBLE PRECISION
);

SELECT create_hypertable('metrics', by_range('time', INTERVAL '7 days'));
-- Optionally add a space dimension
SELECT add_dimension('metrics', by_hash('device_id', 4));

-- View dimensions
SELECT * FROM timescaledb_information.dimensions
WHERE hypertable_name = 'metrics';
```

---

## 11. Integer-Based Time Columns

```sql
-- Use integer columns as time dimension (useful for sequence numbers)
CREATE TABLE event_log (
    event_id BIGINT NOT NULL,
    event_type TEXT,
    payload JSONB
);

SELECT create_hypertable('event_log', by_range('event_id', 1000000));
-- Each chunk covers 1 million event IDs

-- Also works with epoch timestamps stored as integers
CREATE TABLE unix_metrics (
    epoch_ms BIGINT NOT NULL,
    sensor_id INT,
    value FLOAT
);

SELECT create_hypertable('unix_metrics', by_range('epoch_ms', 86400000));
-- Each chunk = 1 day in milliseconds
```

---

## 12. Chunk Lifecycle Automation with pg_cron

```sql
-- Install pg_cron for custom scheduling
CREATE EXTENSION pg_cron;

-- Schedule chunk maintenance
SELECT cron.schedule('chunk-maintenance',
    '0 3 * * *',  -- 3 AM daily
    $$
    -- Move old compressed chunks to cold storage
    DO $body$
    DECLARE chunk_rec RECORD;
    BEGIN
        FOR chunk_rec IN
            SELECT c.chunk_schema || '.' || c.chunk_name AS chunk_fqn
            FROM timescaledb_information.chunks c
            WHERE c.hypertable_name = 'telemetria_sensori'
              AND c.is_compressed
              AND c.range_end < NOW() - INTERVAL '90 days'
        LOOP
            EXECUTE format('ALTER TABLE %s SET TABLESPACE cold_storage', chunk_rec.chunk_fqn);
            RAISE NOTICE 'Moved % to cold_storage', chunk_rec.chunk_fqn;
        END LOOP;
    END $body$;
    $$
);

-- Verify scheduled jobs
SELECT * FROM cron.job ORDER BY jobid;

-- View job execution history
SELECT * FROM cron.job_run_details ORDER BY start_time DESC LIMIT 10;
```

---

## Additional FAQ

### 11. Can I alter the schema of a hypertable?

Yes. Standard ALTER TABLE operations work: add columns, rename columns, change defaults. Schema changes propagate to all existing and future chunks automatically.

### 12. How do I back up a single hypertable?

```bash
pg_dump -d telemetria -t telemetria_sensori -Fc > hypertable_backup.dump
# This includes the hypertable and all its chunks
```

### 13. What is the maximum number of dimensions?

Hypertables support up to 2 dimensions (1 time + 1 space). This is a TimescaleDB design constraint, not a PostgreSQL limitation.

### 14. Can I use BRIN indexes instead of B-tree on chunks?

Yes. BRIN indexes are very space-efficient for time-ordered data:
```sql
CREATE INDEX ON telemetria_sensori USING brin (tempo);
-- Much smaller than B-tree but slower for random lookups
-- Best for time-range scans on large chunks
```

