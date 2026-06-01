# ClickHouse — Performance Tuning e Ottimizzazioni

## Profilazione delle Query

Prima di ottimizzare, misurare. ClickHouse offre strumenti di profilazione dettagliati.

```sql
-- EXPLAIN: analisi del piano di esecuzione
EXPLAIN SELECT country, sum(revenue) FROM events WHERE event_date = today() GROUP BY country;

-- EXPLAIN PIPELINE: visualizza il grafo di esecuzione parallela
EXPLAIN PIPELINE SELECT country, sum(revenue) FROM events GROUP BY country;

-- EXPLAIN indexes = 1: mostra quali indici vengono usati
EXPLAIN indexes = 1
SELECT user_id, sum(revenue)
FROM events
WHERE event_date = today() AND event = 'buy'
GROUP BY user_id;
-- Output mostra: parti totali, parti dopo partition pruning, granule totali,
-- granule dopo primary key pruning, granule dopo skip index

-- Query con statistiche dettagliate
SELECT country, sum(revenue) as rev
FROM events
WHERE event_date = today()
GROUP BY country
SETTINGS log_queries = 1, log_query_threads = 1;

-- Leggere il log della query appena eseguita
SELECT
    query_duration_ms,
    read_rows,
    read_bytes,
    memory_usage,
    result_rows,
    formatReadableSize(read_bytes) as data_read,
    formatReadableSize(memory_usage) as memory
FROM system.query_log
WHERE type = 'QueryFinish'
ORDER BY event_time DESC
LIMIT 5;
```

---

## Configurazione del Server

```xml
<!-- /etc/clickhouse-server/config.d/performance.xml -->
<clickhouse>
    <!-- Memoria -->
    <max_server_memory_usage>0</max_server_memory_usage>  <!-- 0 = usa tutto -->
    <max_server_memory_usage_to_ram_ratio>0.9</max_server_memory_usage_to_ram_ratio>
    <max_memory_usage>10000000000</max_memory_usage>  <!-- 10 GB per query singola -->
    <max_bytes_before_external_group_by>5000000000</max_bytes_before_external_group_by>
    <max_bytes_before_external_sort>10000000000</max_bytes_before_external_sort>

    <!-- Concorrenza -->
    <max_concurrent_queries>200</max_concurrent_queries>
    <max_concurrent_insert_queries>100</max_concurrent_insert_queries>
    <max_concurrent_select_queries>100</max_concurrent_select_queries>

    <!-- Thread pool -->
    <max_thread_pool_size>10000</max_thread_pool_size>

    <!-- Background merges -->
    <background_pool_size>16</background_pool_size>
    <background_merges_mutations_concurrency_ratio>2</background_merges_mutations_concurrency_ratio>
    <background_move_pool_size>8</background_move_pool_size>

    <!-- Uncompressed cache (per granule decodificati) -->
    <uncompressed_cache_size>8589934592</uncompressed_cache_size>  <!-- 8 GB -->

    <!-- Mark cache (per marks file) -->
    <mark_cache_size>5368709120</mark_cache_size>  <!-- 5 GB -->

    <!-- Index uncompressed cache -->
    <index_uncompressed_cache_size>1073741824</index_uncompressed_cache_size>  <!-- 1 GB -->
</clickhouse>
```

---

## Ottimizzazioni per l'Ingestione

### INSERT in Batch

L'anti-pattern più comune è inserire righe una alla volta. Ogni INSERT crea una nuova parte su disco. Con inserti frequenti e piccoli, il numero di parti esplode e le merge non riescono a stare dietro.

```python
# Anti-pattern: un INSERT per riga
for row in data:
    client.execute("INSERT INTO events VALUES", [row])  # SBAGLIATO

# Pattern corretto: batch di 50k-1M righe
BATCH_SIZE = 100_000
buffer = []
for row in data:
    buffer.append(row)
    if len(buffer) >= BATCH_SIZE:
        client.execute("INSERT INTO events VALUES", buffer)
        buffer.clear()
if buffer:
    client.execute("INSERT INTO events VALUES", buffer)
```

### Impostazioni per Bulk Load

```sql
-- Disabilita sync del fsync durante bulk load (dati già replicati)
SET fsync_metadata = 0;
SET fsync_after_insert = 0;

-- Riduce il numero di parti piccole da mergiare
SET min_insert_block_size_rows = 1048576;  -- 1M righe per parte
SET min_insert_block_size_bytes = 268435456;  -- 256 MB per parte

-- Insert asincrono (client non aspetta la scrittura su disco)
SET async_insert = 1;
SET wait_for_async_insert = 0;
SET async_insert_max_data_size = 10485760;  -- 10 MB buffer
SET async_insert_busy_timeout_ms = 1000;    -- flush ogni 1 secondo
```

**Async Insert** (da 21.11): ClickHouse accumula inserti piccoli in un buffer e li flushes come un'unica parte, risolvendo il problema dei troppi INSERT piccoli da client multipli.

---

## Query Optimization

### Selezionare Solo le Colonne Necessarie

```sql
-- Sbagliato: legge tutte le colonne
SELECT * FROM events WHERE event_date = today();

-- Corretto: legge solo le colonne necessarie
SELECT event_date, user_id, event, revenue
FROM events
WHERE event_date = today();
```

### Prewhere: Filtro Prima della Decompressione

ClickHouse ha una clausola `PREWHERE` che applica il filtro prima di decomprimere le altre colonne. L'optimizer lo usa automaticamente in molti casi.

```sql
-- Manuale: filtra su revenue prima di leggere user_id e event
SELECT user_id, event, revenue
FROM events
PREWHERE revenue > 1000  -- legge solo revenue, poi filtra
WHERE event_date >= today() - 7 AND event = 'buy';

-- La maggior parte dei casi: l'optimizer applica PREWHERE automaticamente
-- su colonne numeriche e LowCardinality
```

### Evitare NOT IN con Subquery Grandi

```sql
-- Lento: materialize la subquery completa
SELECT user_id FROM events
WHERE user_id NOT IN (SELECT user_id FROM blacklist);

-- Veloce: anti-join
SELECT e.user_id FROM events e
LEFT ANTI JOIN blacklist b ON e.user_id = b.user_id;

-- Oppure: GLOBAL NOT IN per distribuito
SELECT user_id FROM events_local
WHERE user_id GLOBAL NOT IN (SELECT user_id FROM blacklist);
```

### Sampling per Query Esplorative

```sql
-- Legge solo 1/10 dei dati (campione deterministico per stesso user_id)
SELECT uniq(user_id) * 10 as approx_users
FROM events SAMPLE 0.1;  -- 10% delle righe

-- Sample con seed deterministico
SELECT count() * 100 as estimate FROM events SAMPLE 1/100 OFFSET 42;
```

---

## Gestione delle Parti

```sql
-- Troppe parti piccole = lentezza nelle merge e nelle query
SELECT
    table,
    count() as parts_count,
    sum(rows) as total_rows,
    formatReadableSize(sum(bytes_on_disk)) as size
FROM system.parts
WHERE database = 'analytics' AND active = 1
GROUP BY table
HAVING parts_count > 100
ORDER BY parts_count DESC;

-- Forzare il merge di una partizione (operazione pesante, usa con cautela)
OPTIMIZE TABLE events PARTITION '202401' FINAL;  -- FINAL: merge fino a parte singola

-- Verificare le parti in stato errato
SELECT * FROM system.parts
WHERE database = 'analytics' AND table = 'events'
AND active = 0 AND removal_time IS NULL;
```

### Mutations (ALTER UPDATE/DELETE)

Le mutation sono operazioni pesanti — riscrivono le parti su disco.

```sql
-- DELETE (crea una mutazione asincrona)
ALTER TABLE events DELETE WHERE event_date < '2023-01-01';

-- UPDATE (crea una mutazione asincrona)
ALTER TABLE events UPDATE revenue = revenue * 1.22 WHERE event_date = '2024-01-15';

-- Monitorare lo stato delle mutation
SELECT
    database,
    table,
    mutation_id,
    command,
    create_time,
    is_done,
    parts_to_do,
    latest_fail_reason
FROM system.mutations
WHERE is_done = 0
ORDER BY create_time;
```

**Alternativa alle mutation**: per delete frequenti, usare TTL (elimina righe per età) o CollapsingMergeTree (elimina per sign).

---

## Compressione dei Dati

```sql
-- Codec di compressione per colonna
CREATE TABLE metrics_compressed (
    ts          DateTime    CODEC(DoubleDelta, LZ4),    -- ottimale per timestamp monotoni
    value       Float64     CODEC(Gorilla, ZSTD(3)),    -- ottimale per time series float
    host        String      CODEC(ZSTD(9)),              -- alta compressione
    status_code UInt16      CODEC(T64, LZ4),             -- ottimale per interi piccoli
    payload     String      CODEC(ZSTD(3))
) ENGINE = MergeTree() ORDER BY ts;
```

| Codec | Adatto per | Ratio tipico |
|-------|------------|-------------|
| `LZ4` | Default, velocità | 2-4x |
| `ZSTD(N)` | Miglior compressione (N=1-22) | 3-8x |
| `DoubleDelta` | Timestamp monotoni | 5-20x (delta dei delta) |
| `Gorilla` | Float time series | 3-10x |
| `T64` | Interi piccoli in colonne Int/UInt | 5-15x |
| `Delta` | Valori che crescono linearmente | 3-8x |

---

## Monitoraggio Continuo

```sql
-- Query più lente dell'ultima ora
SELECT
    normalized_query_hash,
    any(query) as sample_query,
    count() as executions,
    avg(query_duration_ms) as avg_ms,
    max(query_duration_ms) as max_ms,
    avg(read_rows) as avg_rows_read,
    avg(memory_usage) as avg_memory
FROM system.query_log
WHERE type = 'QueryFinish'
  AND event_time >= now() - INTERVAL 1 HOUR
  AND query_duration_ms > 1000
GROUP BY normalized_query_hash
ORDER BY avg_ms DESC
LIMIT 20;

-- Uso risorse per utente
SELECT
    user,
    count() as queries,
    sum(query_duration_ms) / 1000 as total_seconds,
    formatReadableSize(sum(read_bytes)) as total_read,
    formatReadableSize(sum(memory_usage)) as total_memory
FROM system.query_log
WHERE type = 'QueryFinish' AND event_time >= today()
GROUP BY user
ORDER BY total_seconds DESC;
```

Il performance tuning di ClickHouse si riduce a tre principi: progettare il partizionamento e l'ordinamento per le query più frequenti, inserire in batch grandi per ridurre il numero di parti, e selezionare solo le colonne necessarie per sfruttare al massimo il vantaggio colonnare.
