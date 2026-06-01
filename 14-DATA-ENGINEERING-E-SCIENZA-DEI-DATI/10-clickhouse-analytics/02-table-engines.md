# ClickHouse — Motori di Tabella (Table Engines)

## La Famiglia MergeTree

Il motore MergeTree e le sue varianti sono il cuore di ClickHouse per le tabelle di produzione. Ogni variante aggiunge comportamento specifico al ciclo write-merge.

### MergeTree Base

Il motore fondamentale. Scrive parti, le fonde in background, mantiene i dati ordinati per la chiave di ordinamento.

```sql
CREATE TABLE metrics (
    ts          DateTime,
    host        LowCardinality(String),
    metric_name LowCardinality(String),
    value       Float64,
    tags        Map(String, String)
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(ts)
ORDER BY (host, metric_name, ts)
TTL ts + INTERVAL 90 DAY DELETE
SETTINGS
    index_granularity = 8192,
    merge_with_ttl_timeout = 86400;
```

**TTL (Time-To-Live)**: elimina righe o sposta dati su storage alternativo automaticamente.

```sql
-- TTL per colonna (azzera il valore invece di eliminare la riga)
CREATE TABLE events (
    ts          DateTime,
    user_id     UInt64,
    event       String,
    pii_data    String TTL ts + INTERVAL 30 DAY
) ENGINE = MergeTree()
ORDER BY (ts, user_id);

-- TTL con azione MOVE TO VOLUME (tiered storage)
ALTER TABLE metrics
    MODIFY TTL ts + INTERVAL 7 DAY TO VOLUME 'cold';
```

### ReplacingMergeTree: Deduplicazione per Chiave

Permette di simulare UPDATE: quando due righe hanno la stessa chiave di ordinamento, ReplacingMergeTree ne mantiene solo l'ultima (o quella con il version number più alto).

```sql
CREATE TABLE user_profiles (
    user_id      UInt64,
    updated_at   DateTime,
    name         String,
    email        String,
    country      LowCardinality(String),
    is_active    UInt8
) ENGINE = ReplacingMergeTree(updated_at)
ORDER BY user_id;

-- Insert iniziale
INSERT INTO user_profiles VALUES (1001, now(), 'Mario Rossi', 'mario@example.com', 'IT', 1);

-- "Update" via insert con timestamp più recente
INSERT INTO user_profiles VALUES (1001, now(), 'Mario Rossi', 'mario.nuovo@example.com', 'IT', 1);
```

**Importante**: la deduplicazione avviene durante il merge, che è asincrono. Prima del merge, entrambe le righe coesistono. Per query consistenti:

```sql
-- FINAL forza la deduplicazione a query time (più lento)
SELECT * FROM user_profiles FINAL WHERE user_id = 1001;

-- Alternativa con argMax: prende il valore più recente per user_id
SELECT
    user_id,
    argMax(name, updated_at) as name,
    argMax(email, updated_at) as email,
    argMax(country, updated_at) as country,
    argMax(is_active, updated_at) as is_active
FROM user_profiles
GROUP BY user_id;
```

### SummingMergeTree: Pre-Aggregazione Automatica

Somma automaticamente le colonne numeriche per le righe con la stessa chiave di ordinamento durante il merge. Ideale per contatori e metriche pre-aggregate.

```sql
CREATE TABLE page_views_hourly (
    event_hour   DateTime,
    page         String,
    country      LowCardinality(String),
    views        UInt64,
    unique_users UInt64,
    revenue      Decimal(15, 2)
) ENGINE = SummingMergeTree((views, unique_users, revenue))
PARTITION BY toYYYYMM(event_hour)
ORDER BY (event_hour, page, country);

-- Insert multipli per la stessa chiave
INSERT INTO page_views_hourly VALUES ('2024-01-15 10:00:00', '/home', 'IT', 100, 80, 0);
INSERT INTO page_views_hourly VALUES ('2024-01-15 10:00:00', '/home', 'IT', 150, 120, 500.00);

-- Dopo il merge: views=250, unique_users=200, revenue=500.00
-- Con FINAL per forzare la somma a query time:
SELECT * FROM page_views_hourly FINAL WHERE event_hour = '2024-01-15 10:00:00';
```

### AggregatingMergeTree: Aggregazioni Incremetali

Il motore più potente per pre-aggregazioni. Memorizza **stati parziali** di funzioni aggregate (invece dei valori finali), che vengono poi combinati al query time.

```sql
CREATE TABLE user_stats_hourly (
    event_hour   DateTime,
    country      LowCardinality(String),
    -- AggregateFunction memorizza lo stato parziale
    total_users  AggregateFunction(uniq, UInt64),       -- HLL sketch
    total_events AggregateFunction(count, UInt64),       -- contatore
    revenue_sum  AggregateFunction(sum, Decimal(10, 2)), -- somma
    revenue_p99  AggregateFunction(quantile(0.99), Float64)  -- t-digest
) ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(event_hour)
ORDER BY (event_hour, country);

-- Insert con funzioni *State
INSERT INTO user_stats_hourly
SELECT
    toStartOfHour(event_time) as event_hour,
    country,
    uniqState(user_id) as total_users,
    countState() as total_events,
    sumState(revenue) as revenue_sum,
    quantileState(0.99)(toFloat64(revenue)) as revenue_p99
FROM web_events
WHERE event_date = today()
GROUP BY event_hour, country;

-- Query con funzioni *Merge per combinare gli stati
SELECT
    event_hour,
    country,
    uniqMerge(total_users) as users,
    countMerge(total_events) as events,
    sumMerge(revenue_sum) as revenue,
    quantileMerge(0.99)(revenue_p99) as p99_revenue
FROM user_stats_hourly
GROUP BY event_hour, country
ORDER BY event_hour DESC;
```

### CollapsingMergeTree: Pattern Delete/Update

Usa un campo `sign` (Int8, valori +1/-1) per marcare righe come "valide" (+1) o "cancellate" (-1). Durante il merge, le coppie +1/-1 con stessa chiave si annullano.

```sql
CREATE TABLE order_states (
    order_id     UInt64,
    updated_at   DateTime,
    status       LowCardinality(String),
    amount       Decimal(10, 2),
    sign         Int8   -- +1 = record attivo, -1 = cancellazione
) ENGINE = CollapsingMergeTree(sign)
ORDER BY (order_id, updated_at);

-- Inserimento
INSERT INTO order_states VALUES (100, '2024-01-15 10:00:00', 'pending', 299.99, 1);

-- "Update": prima cancella la vecchia versione, poi inserisce la nuova
INSERT INTO order_states VALUES
    (100, '2024-01-15 10:00:00', 'pending',   299.99, -1),  -- cancella
    (100, '2024-01-15 10:05:00', 'confirmed', 299.99,  1);  -- inserisce

-- Query: somma i sign per ottenere solo i record attivi
SELECT order_id, status, amount
FROM order_states
GROUP BY order_id, status, amount
HAVING sum(sign) > 0;
```

**VersionedCollapsingMergeTree**: variante che aggiunge un campo version per gestire l'ordine di arrivo out-of-order.

```sql
CREATE TABLE order_states_versioned (
    order_id  UInt64,
    version   UInt64,
    status    String,
    amount    Decimal(10, 2),
    sign      Int8
) ENGINE = VersionedCollapsingMergeTree(sign, version)
ORDER BY order_id;
```

---

## Motori di Tipo Log

Per dati di sola scrittura con query semplici, a basso overhead.

### TinyLog

Nessun indice, nessun sort, append-only. Adatto solo per piccole tabelle temporanee (<1M righe).

```sql
CREATE TABLE temp_data (id UInt64, value String) ENGINE = TinyLog;
```

### Log e StripeLog

- **Log**: un file per colonna, con marks per random access. Meglio di TinyLog per tabelle medie
- **StripeLog**: tutte le colonne in un unico file, accesso parallelo limitato

---

## Motori Speciali

### Memory

Tabella interamente in RAM. Nessuna persistenza, nessuna compressione. Utile per caching temporaneo e CTE materializzate.

```sql
CREATE TABLE cache_table (
    key   String,
    value Float64
) ENGINE = Memory;
```

### Null

Scarta tutto ciò che viene scritto. Utile come endpoint per trigger materialize view senza persistenza dei dati sorgente.

```sql
CREATE TABLE events_raw (
    ts     DateTime,
    data   String
) ENGINE = Null;

-- La Materialized View processa i dati prima che vengano scartati
CREATE MATERIALIZED VIEW events_parsed TO events_clean AS
SELECT ts, JSONExtractString(data, 'user_id') as user_id, ...
FROM events_raw;
```

### Buffer

Accumula INSERT in RAM e li flushes periodicamente nella tabella target. Riduce il numero di parti create.

```sql
CREATE TABLE events_buffer AS events
ENGINE = Buffer(currentDatabase(), 'events', 16, 10, 100, 10000, 1000000, 10000000, 100000000);
-- 16 shards, flush ogni 10-100 sec, flush se >10k-1M rows o >10MB-100MB
```

### Dictionary

Carica dati da sorgenti esterne (MySQL, PostgreSQL, HTTP, file) in memoria per lookup veloci.

```sql
-- Definizione dizionario
CREATE DICTIONARY country_names (
    code  FixedString(2),
    name  String
)
PRIMARY KEY code
SOURCE(CLICKHOUSE(TABLE 'ref_countries'))
LAYOUT(FLAT())
LIFETIME(MIN 300 MAX 3600);

-- Utilizzo in query
SELECT
    country,
    dictGet('country_names', 'name', country) as country_name,
    count()
FROM web_events
GROUP BY country;
```

---

## Motori di Integrazione (Table Functions + Engines)

### MySQL Engine

```sql
CREATE TABLE mysql_orders (
    id        UInt32,
    status    String,
    amount    Decimal(10, 2),
    created_at DateTime
) ENGINE = MySQL('mysql-host:3306', 'mydb', 'orders', 'clickhouse_user', 'password');

-- Query passate direttamente a MySQL (pushdown)
SELECT status, sum(amount) FROM mysql_orders WHERE created_at > now() - INTERVAL 7 DAY
GROUP BY status;
```

### S3 Engine e Table Function

```sql
-- Lettura diretta da S3 (Parquet, CSV, JSON)
SELECT count() FROM s3(
    'https://my-bucket.s3.amazonaws.com/data/2024/01/*.parquet',
    'AKIAIOSFODNN7EXAMPLE',
    'wJalrXUtnFEMI/K7MDENG',
    'Parquet'
);

-- Tabella permanente su S3
CREATE TABLE events_s3 (
    event_date Date,
    user_id    UInt64,
    event      String
) ENGINE = S3('https://my-bucket.s3.amazonaws.com/events/*.parquet', 'access_key', 'secret', 'Parquet')
PARTITION BY event_date;
```

### Kafka Engine

```sql
CREATE TABLE kafka_events (
    event_time  DateTime,
    user_id     UInt64,
    event       String,
    payload     String
) ENGINE = Kafka
SETTINGS
    kafka_broker_list = 'kafka1:9092,kafka2:9092',
    kafka_topic_list  = 'user-events',
    kafka_group_name  = 'clickhouse-consumers',
    kafka_format      = 'JSONEachRow',
    kafka_num_consumers = 4,
    kafka_max_block_size = 65536;

-- La tabella Kafka è solo un consumer — i dati non vengono persistiti
-- Usare con Materialized View per persistere
CREATE TABLE events_persistent (
    event_time DateTime,
    user_id    UInt64,
    event      LowCardinality(String),
    payload    String
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(event_time)
ORDER BY (event_time, user_id);

CREATE MATERIALIZED VIEW kafka_to_persistent TO events_persistent AS
SELECT event_time, user_id, event, payload
FROM kafka_events;
```

---

## Scelta del Motore: Guida Pratica

| Scenario | Motore Raccomandato |
|----------|---------------------|
| Dati immutabili, analytics puri | MergeTree |
| Dati che cambiano (upsert) | ReplacingMergeTree |
| Contatori pre-aggregati | SummingMergeTree |
| Aggregazioni incrementali complesse | AggregatingMergeTree |
| Pattern delete/update esplicito | CollapsingMergeTree |
| Lookup dizionari | Dictionary |
| Ingestione da Kafka | Kafka + MV → MergeTree |
| Query su file S3/GCS/Azure | S3/GCS/AzureBlobStorage |
| Cache temporanea | Memory |
| Cluster distribuito | Distributed + ReplicatedMergeTree |

La combinazione più comune in produzione è **Kafka Engine → Materialized View → ReplicatedMergeTree** per l'ingestione in real-time con alta disponibilità.
