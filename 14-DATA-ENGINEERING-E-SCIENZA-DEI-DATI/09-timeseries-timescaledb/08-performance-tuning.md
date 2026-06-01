# Performance Tuning in TimescaleDB

> Autori: Team Data Encyclopedia  
> Ultimo aggiornamento: 2026-05-06  
> Versione: 1.0.0  
> Stato: draft

## Indice
1. Tuning del Sistema PostgreSQL
2. Ottimizzazione delle Query
3. Indici per Serie Temporali
4. Parallel Query e Worker
5. Anti-Pattern e Diagnostica

---

## 1. Tuning del Sistema PostgreSQL

### 1.1 Parametri Fondamentali

`shared_buffers` è il parametro più impattante: definisce la quantità di memoria condivisa che PostgreSQL usa come cache per le pagine del database. Per TimescaleDB, il valore raccomandato è 25% della RAM disponibile. Su un server con 64 GB, si imposta a 16 GB. I chunk più recenti (in scrittura attiva) e i chunk interrogati frequentemente risiederanno in questa cache.

`effective_cache_size` non è memoria allocata, ma è la stima che il planner usa per decidere se un index scan è preferibile a un sequential scan. Deve essere impostato al totale della memoria disponibile per la cache del filesystem + shared_buffers, tipicamente 75% della RAM. Un valore basso porta il planner a sottostimare l'efficacia degli indici.

```ini
# postgresql.conf — configurazione raccomandata per TimescaleDB

# Memoria
shared_buffers = 16GB           # 25% della RAM
effective_cache_size = 48GB     # 75% della RAM
work_mem = 256MB                # per sort e hash join (per sessione)
maintenance_work_mem = 2GB      # per CREATE INDEX, VACUUM, etc.

# WAL e checkpoint
wal_buffers = 64MB
checkpoint_completion_target = 0.9
max_wal_size = 4GB

# Background workers (per compression, continuous aggregate refresh)
max_worker_processes = 16
max_parallel_workers = 8
max_parallel_workers_per_gather = 4
timescaledb.max_background_workers = 8

# TimescaleDB specifici
timescaledb.max_open_chunks_per_insert = 100
```

### 1.2 Tuning con timescaledb-tune

Lo strumento `timescaledb-tune` analizza le risorse hardware e propone una configurazione ottimale. È disponibile come tool CLI separato.

```bash
# Analisi e applicazione automatica
timescaledb-tune --quiet --yes

# Analisi con output senza modificare (dry-run)
timescaledb-tune --dry-run

# Tuning per configurazione specifica
timescaledb-tune \
    --memory=32GB \
    --cpus=16 \
    --max-bg-workers=8
```

---

## 2. Ottimizzazione delle Query

### 2.1 EXPLAIN ANALYZE per Serie Temporali

L'analisi dei piani di esecuzione è lo strumento fondamentale per il tuning delle query TimescaleDB. L'output di `EXPLAIN (ANALYZE, BUFFERS)` mostra quali chunk vengono inclusi/esclusi, quante pagine vengono lette da disco vs dalla cache, e dove il tempo viene speso.

```sql
-- Query di esempio: temperatura media oraria nell'ultimo giorno
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT
    time_bucket('1 hour', tempo) AS ora,
    dispositivo,
    AVG(temperatura)
FROM telemetria_sensori
WHERE tempo >= NOW() - INTERVAL '1 day'
  AND dispositivo = 'sensore-42'
GROUP BY 1, 2
ORDER BY 1;

-- Output key da cercare:
-- "Chunks excluded by runtime exclusion: N" → chunk saltati
-- "Buffers: shared hit=X read=Y" → hit rate della cache
-- "actual time=0.xxx..Y.ZZZ rows=N loops=1" → tempo reale
-- "Custom Scan (ChunkAppend)" → scan parallelo dei chunk
```

### 2.2 Chunk Exclusion: Assicurarsi che Funzioni

Il chunk exclusion è automatico solo se il predicato temporale usa `tempo` (la colonna di partizionamento) direttamente. Funzioni che trasformano il timestamp possono impedire il pruning.

```sql
-- CORRETTO: il planner può fare chunk exclusion
WHERE tempo >= NOW() - INTERVAL '7 days'
WHERE tempo BETWEEN '2026-01-01' AND '2026-01-08'

-- SBAGLIATO: la funzione impedisce il chunk exclusion
WHERE DATE_TRUNC('day', tempo) = '2026-01-01'  -- usa: tempo >= '2026-01-01' AND tempo < '2026-01-02'
WHERE EXTRACT(MONTH FROM tempo) = 1            -- non esclude chunk

-- SBAGLIATO: subquery sul tempo impedisce la staticizzazione
WHERE tempo > (SELECT MAX(tempo) - INTERVAL '7 days' FROM altra_tabella)
-- meglio: calcolare il valore in applicazione e passarlo come parametro
```

---

## 3. Indici per Serie Temporali

### 3.1 Indice Default e Indici Aggiuntivi

TimescaleDB crea automaticamente un indice su `(tempo DESC)` per ogni hypertable. Questo indice è sufficiente per query che filtrano solo per range temporale, ma insufficiente per query che filtrano anche per dispositivo, metrica, o altri attributi.

La regola generale per gli indici nelle serie temporali: creare un indice composito che includa le colonne usate come filtro nelle WHERE clause più comuni, con il timestamp come **ultima** colonna (per sfruttare il range scan temporale dopo aver filtrato per valore esatto delle altre colonne).

```sql
-- Indice ottimale per "dammi i dati del dispositivo X negli ultimi 7 giorni"
CREATE INDEX ON telemetria_sensori (dispositivo, tempo DESC);

-- Per query che filtrano per (dispositivo, metrica)
CREATE INDEX ON telemetria_sensori (dispositivo, metrica, tempo DESC);

-- Indice parziale per query su dati di qualità alta
CREATE INDEX ON telemetria_sensori (dispositivo, tempo DESC)
    WHERE qualita >= 90;

-- Indice BRIN per scan su range temporale senza predicate su altre colonne
-- (molto compatto, utile per chunk molto grandi su soli range temporali)
CREATE INDEX ON telemetria_sensori USING BRIN (tempo)
    WITH (pages_per_range = 128);
```

### 3.2 Indici sulle Continuous Aggregate

Le continuous aggregate sono hypertable e possono avere i loro indici. Questo è importante per query analitiche che operano sulla vista aggregata.

```sql
-- Indice sulla continuous aggregate per query per dispositivo
CREATE INDEX ON telemetria_oraria (dispositivo, ora DESC);
CREATE INDEX ON telemetria_oraria (ora DESC, dispositivo);
```

---

## 4. Parallel Query e Worker

### 4.1 Parallelismo nei Chunk

TimescaleDB sfrutta il parallelismo di PostgreSQL per interrogare i chunk in parallelo. Il piano `Custom Scan (ChunkAppend)` mostra l'esecuzione parallela su più chunk. Il numero di worker paralleli è controllato da `max_parallel_workers_per_gather`.

```sql
-- Abilita il parallelismo per query analitiche pesanti
SET max_parallel_workers_per_gather = 4;
SET timescaledb.enable_chunk_skipping = ON;

-- Verifica che una query stia usando parallelismo
EXPLAIN (ANALYZE)
SELECT time_bucket('1 day', tempo), COUNT(*)
FROM telemetria_sensori
WHERE tempo >= NOW() - INTERVAL '30 days'
GROUP BY 1;
-- Cercare "Parallel Seq Scan" o "Workers Launched: N"
```

### 4.2 Background Workers per Policy

I job automatici di TimescaleDB (compression, retention, continuous aggregate refresh) girano come background workers. Il parametro `timescaledb.max_background_workers` limita il numero di questi worker. Se ci sono molte policy o la policy di refresh delle continuous aggregate è frequente, può essere necessario aumentare questo valore.

```sql
-- Monitoraggio dei background worker attivi
SELECT pid, application_name, state, query
FROM pg_stat_activity
WHERE application_name LIKE 'TimescaleDB%'
   OR application_name LIKE 'timescaledb%';
```

---

## 5. Anti-Pattern e Diagnostica

### 5.1 Anti-Pattern Comuni

**SELECT senza filtro temporale**: la query più distruttiva su una hypertable è quella senza predicate sul tempo. Scansiona tutti i chunk, inclusi quelli compressi che devono essere decompressi, e può durare ore su grandi dataset.

```sql
-- ANTI-PATTERN: scansiona tutto
SELECT COUNT(*) FROM telemetria_sensori WHERE dispositivo = 'abc';

-- CORRETTO: limita sempre per range temporale
SELECT COUNT(*) FROM telemetria_sensori
WHERE dispositivo = 'abc'
  AND tempo >= NOW() - INTERVAL '30 days';
```

**Mancanza di indice sul campo di filtro più selettivo**: se le query filtrano frequentemente per `dispositivo` ma esiste solo l'indice su `tempo`, PostgreSQL farà un sequential scan sull'intero chunk prima di filtrare per dispositivo. Creare l'indice composito `(dispositivo, tempo DESC)` elimina il problema.

**INSERT singoli in loop**: inserire record uno alla volta genera un overhead enorme (WAL sync per ogni INSERT). Usare sempre `INSERT ... VALUES (a), (b), (c)` in batch o il protocollo COPY.

### 5.2 Diagnostica con le Viste di Sistema

```sql
-- Le 10 query più lente (richiede pg_stat_statements)
SELECT query,
       calls,
       total_exec_time / calls AS avg_ms,
       rows / calls AS avg_rows
FROM pg_stat_statements
WHERE query LIKE '%telemetria_sensori%'
ORDER BY total_exec_time DESC
LIMIT 10;

-- Utilizzo degli indici
SELECT
    indexrelname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE relname LIKE '_hyper_%'
ORDER BY idx_scan DESC;

-- Cache hit rate (dovrebbe essere > 99%)
SELECT
    SUM(heap_blks_hit) / NULLIF(SUM(heap_blks_hit + heap_blks_read), 0) AS cache_hit_ratio
FROM pg_statio_user_tables
WHERE relname LIKE '_hyper_%';
```

---

*Questo documento fa parte del modulo 09 "Time Series & TimescaleDB" della Data Encyclopedia.*
