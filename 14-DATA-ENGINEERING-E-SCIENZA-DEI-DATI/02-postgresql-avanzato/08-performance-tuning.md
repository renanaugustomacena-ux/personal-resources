# PostgreSQL Performance Tuning

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-04  
> Versione: 1.0.0  
> Stato: draft

## Skip list
- [ ] Bozza iniziale
- [ ] Review tecnica
- [ ] Formattazione
- [ ] Pubblicazione

## Indice
1. Memory Configuration
2. Query Planning
3. EXPLAIN ANALYZE Deep Dive
4. Connection Pooling
5. Checkpoint Tuning
6. WAL Tuning
7. Autovacuum Configuration
8. Statistics e ANALYZE
9. Shared Buffers Tuning
10. Work Memory e Maintenance

---

## 1. Memory Configuration

### 1.1 shared_buffers

Il parametro **shared_buffers** definisce la dimensione della cache del database in memoria condivisa. È il parametro più importante per le performance.

```sql
-- Regola generale: 25% della RAM per server dedicato
-- Per server con 32GB RAM:
shared_buffers = 8GB

-- Per server con 128GB RAM:
shared_buffers = 32GB

-- Valori estremi: non meno di 128MB, non più di 8GB per sistemi piccoli
-- Valori più alti non sempre meglio: >40% può degradare le performance
```

**Impatto**: Cache più grande = più dati in memoria = meno I/O su disco. Ma memoria usata per PostgreSQL non è disponibile per altre cache del sistema operativo.

### 1.2 effective_cache_size

Il parametro **effective_cache_size** fornisce un hint all'optimizer sulla cache totale disponibile (PostgreSQL + OS + altre cache):

```sql
-- Stimare: 75% della RAM totale
-- Per server con 32GB:
effective_cache_size = 24GB

-- Questo influisce le stime di costo dell'optimizer
-- Cache grande -> optimizer preferisce scansioni sequenziali
```

Questo parametro non alloca memoria, ma influenza i piani di query scelti.

### 1.3 work_mem

Il parametro **work_mem** definisce la memoria disponibile per operazioni di sorting e hashing per ogni operazione:

```sql
-- Default: 4MB
-- Per operazioni complesse:
work_mem = 256MB

-- Per sessioni specifiche (query pesanti):
SET work_mem = '512MB';
```

**Nota**: Questo valore è per operazione, non totale. Una query con multiple operazioni di sort può usare multiple work_mem.

### 1.4 maintenance_work_mem

Il parametro **maintenance_work_mem** è la memoria per operazioni di manutenzione:

```sql
-- Per server dedicato:
maintenance_work_mem = 1GB

-- Per operazioni di manutenzione pesanti:
SET maintenance_work_mem = '2GB';

-- Operazioni che usano maintenance_work_mem:
-- VACUUM, CREATE INDEX, REINDEX, ALTER TABLE
```

### 1.5 temp_buffers

Memoria per tabelle temporanee per sessione:

```sql
-- Default: 8MB
temp_buffers = 256MB  -- per sessioni con grandi temp tables
```

---

## 2. Query Planning

### 2.1 Planner Cost Constants

Cost settings:
```sql
-- postgresql.conf
random_page_cost = 1.1  -- for SSD
seq_page_cost = 1.0
```

### 2.2 enable_*

Planner controls:
```sql
SET enable_seqscan = off;  -- force index usage
SET enable_nestloop = off;  -- disable nested loop
```

### 2.3 constraint_exclusion

Constraint exclusion:
```sql
SET constraint_exclusion = partition;  -- for partitioned tables
```

### 2.4 join_collapse_limit

Join ordering:
```sql
SET join_collapse_limit = 8;  -- up to this many, reorders
```

---

## 3. EXPLAIN ANALYZE Deep Dive

### 3.1 ANALYZE vs EXPLAIN

ANALYZE esegue, EXPLAIN stima:
```sql
EXPLAIN (ANALYZE, BUFFERS, TIMING) SELECT * FROM tab WHERE col = 'x';
```

### 3.2 Interpreting Output

Output:
- **Execution time**: tempo reale
- **Rows**: righe effettive
- **Buffers**: pagine lette/scritte
- **Shared hit/read/written**: buffer stats

### 3.3 Cost Values

Costi:
- **startup**: setup cost
- **total**: execution cost
- **rows**: righe stimate
- **width**: byte per row

### 3.4 Problem Identification

Identificare problemi:
- Seq Scan su grandi tabelle
- Nested loop senza index
- High buffer reads
- Sorting su disco

---

## 4. Connection Pooling

### 4.1 PgBouncer

PgBouncer per pooling:
```sql
[databases]
mydb = host=localhost dbname=mydb

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
```

### 4.2 Pool Modes

Modalità:
- **Session**: connection per session
- **Transaction**: connection per transazione
- **Statement**: connection per statement

### 4.3 PgPool-II

PgPool-II features:
- Load balancing
- Connection pooling
- Automatic failover

---

## 5. Checkpoint Tuning

### 5.1 Checkpoint Parameters

Checkpoint settings:
```sql
-- postgresql.conf
checkpoint_timeout = 10min
checkpoint_completion_target = 0.9
checkpoint_warning = 30s
```

### 5.2 Checkpoint Completion Target

Target:
- Distribuisce writes
- Riduce I/O spikes
- 0.9 = 90% del tempo tra checkpoint

### 5.3 Monitoring Checkpoints

Monitor:
```sql
SELECT * FROM pg_stat_bgwriter;
```

### 5.4 Tuning Strategy

Tuning:
- Smaller checkpoints more frequent
- Adjust based on write workload

---

## 6. WAL Tuning

### 6.1 wal_buffers

WAL buffer size:
```sql
wal_buffers = 16MB  -- 1/32 of shared_buffers
```

### 6.2 wal_writer_delay

Writer delay:
```sql
wal_writer_delay = 200ms  -- sleep between writes
```

### 6.3 synchronous_commit

Sync mode:
```sql
synchronous_commit = on  -- default, durabile
-- off: async, rischio piccola perdita
-- local: solo disco locale
```

### 6.4 wal_compression

Compression:
```sql
wal_compression = on  -- reduce WAL size
```

---

## 7. Autovacuum Configuration

### 7.1 autovacuum

Enable:
```sql
autovacuum = on
autovacuum_max_workers = 4
```

### 7.2 Per-Table Settings

Per tabella:
```sql
ALTER TABLE big_table SET (
    autovacuum_vacuum_threshold = 10000,
    autovacuum_vacuum_scale_factor = 0.01,
    autovacuum_analyze_scale_factor = 0.005
);
```

### 7.3 Vacuum Cost Delay

Cost-based vacuum:
```sql
vacuum_cost_delay = 2ms
vacuum_cost_limit = 200
```

### 7.4 Manual Vacuum

Manual operations:
```sql
VACUUM VERBOSE ANALYZE big_table;
VACUUM FULL big_table;  -- blocks, shrinks
```

---

## 8. Statistics e ANALYZE

### 8.1 statistics

Statistics collection:
```sql
shared_preload_libraries = 'pg_stat_statements'
track_activities = on
track_counts = on
track_io_timing = on
```

### 8.2 ANALYZE

Analyze updates stats:
```sql
ANALYZE table_name;  -- update statistics
```

### 8.3 pg_stat_statements

Monitor queries:
```sql
SELECT query, calls, total_exec_time, mean_exec_time, rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```

### 8.4 Extended Statistics

Extended stats:
```sql
CREATE STATISTICS my_stats (dependencies) ON a, b FROM tab;
```

---

## 9. Shared Buffers Tuning

### 9.1 Sizing Guidelines

Linee guida:
- 25% RAM per shared_buffers (8-32GB typical)
- Too large = diminishing returns
- Too small = disk thrashing

### 9.2 Huge Pages

Huge pages:
```sql
huge_pages = try  -- reduce TLB pressure
```

### 9.3 buffer manager

Buffer manager internals:
- Clock sweep
- Buffer usage tracking

### 9.4 Tuning Example

Example per 32GB RAM:
```sql
shared_buffers = 8GB
effective_cache_size = 24GB
```

---

## 10. Work Memory e Maintenance

### 10.1 work_mem

Per sort/hash:
```sql
SET work_mem = '512MB';  -- for big sorts
```

### 10.2 maintenance_work_mem

Per maintenance:
```sql
SET maintenance_work_mem = '1GB';  -- before VACUUM
```

### 10.3 Memory Preloading

Preload:
```sql
-- shared_preload_libraries for extensions
```

### 10.4 Temporary Memory

Temp buffers:
```sql
temp_buffers = 8MB  -- per temp tables
```

---

*Questo documento fa parte del modulo 02 "PostgreSQL Avanzato" della Data Encyclopedia.*