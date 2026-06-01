# ClickHouse — Casi d'Uso e Pattern Applicativi

## Web Analytics: Piattaforma Tipo Mixpanel/Amplitude

Il caso d'uso fondante di ClickHouse — analisi di eventi utente a larga scala.

### Schema degli Eventi

```sql
CREATE TABLE user_events (
    -- Identificatori
    event_id    UUID DEFAULT generateUUIDv4(),
    session_id  String,
    user_id     UInt64,
    anonymous_id String,

    -- Timing
    event_date  Date       DEFAULT toDate(event_time),
    event_time  DateTime64(3),

    -- Evento
    event_name  LowCardinality(String),
    page_url    String,
    page_title  String,
    referrer    String,

    -- Contesto
    country     LowCardinality(FixedString(2)),
    city        String,
    device_type LowCardinality(String),
    os          LowCardinality(String),
    browser     LowCardinality(String),
    screen_res  LowCardinality(String),

    -- Propertà custom (struttura flessibile)
    properties  Map(String, String),

    -- Revenue (se applicabile)
    revenue     Decimal(10, 2) DEFAULT 0,
    currency    LowCardinality(FixedString(3)) DEFAULT 'EUR'
) ENGINE = ReplicatedMergeTree('/clickhouse/tables/shard{shard}/user_events', '{replica}')
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_date, user_id, event_time)
TTL event_date + INTERVAL 2 YEAR DELETE
SETTINGS index_granularity = 8192;
```

### Query Analitiche Tipiche

```sql
-- DAU/WAU/MAU
SELECT
    toStartOfDay(event_time) as day,
    uniq(user_id) as dau
FROM user_events
WHERE event_date >= today() - 30
GROUP BY day ORDER BY day;

-- Cohort Analysis: retention degli utenti per mese di acquisizione
WITH first_seen AS (
    SELECT user_id, toStartOfMonth(min(event_date)) as cohort_month
    FROM user_events GROUP BY user_id
)
SELECT
    cohort_month,
    period,
    uniq(user_id) as users,
    uniq(user_id) / max(cohort_size) as retention_rate
FROM (
    SELECT
        f.cohort_month,
        dateDiff('month', f.cohort_month, toStartOfMonth(e.event_date)) as period,
        e.user_id,
        count() OVER (PARTITION BY f.cohort_month) as cohort_size
    FROM user_events e
    JOIN first_seen f ON e.user_id = f.user_id
    WHERE event_date >= '2024-01-01'
)
GROUP BY cohort_month, period
ORDER BY cohort_month, period;

-- Funnel: view → add_to_cart → checkout → purchase
SELECT
    step,
    users,
    round(users / max(users) OVER () * 100, 1) as conversion_pct
FROM (
    SELECT
        arrayJoin([1, 2, 3, 4]) as step,
        [
            uniqIf(user_id, has(events_arr, 'page_view')),
            uniqIf(user_id, has(events_arr, 'add_to_cart')),
            uniqIf(user_id, has(events_arr, 'checkout_started')),
            uniqIf(user_id, has(events_arr, 'purchase'))
        ][step] as users
    FROM (
        SELECT user_id, groupArray(event_name) as events_arr
        FROM user_events
        WHERE event_date = today()
        GROUP BY user_id
    )
);
```

---

## Monitoring e Observability: Metriche di Sistema

```sql
CREATE TABLE system_metrics (
    collected_at  DateTime DEFAULT now(),
    host          LowCardinality(String),
    service       LowCardinality(String),
    metric_name   LowCardinality(String),
    value         Float64,
    labels        Map(LowCardinality(String), String)
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(collected_at)
ORDER BY (host, service, metric_name, collected_at)
TTL collected_at + INTERVAL 90 DAY DELETE;

-- Dashboard: utilizzo CPU per host nelle ultime 2 ore
SELECT
    toStartOfMinute(collected_at) as minute,
    host,
    avg(value) as avg_cpu
FROM system_metrics
WHERE metric_name = 'cpu_usage_pct'
  AND collected_at >= now() - INTERVAL 2 HOUR
GROUP BY minute, host
ORDER BY minute;

-- Anomaly detection: z-score per identificare outlier
SELECT
    host,
    minute,
    value,
    avg_baseline,
    stddev_baseline,
    (value - avg_baseline) / nullIf(stddev_baseline, 0) as z_score
FROM (
    SELECT
        host,
        toStartOfMinute(collected_at) as minute,
        avg(value) as value,
        avg(avg(value)) OVER (
            PARTITION BY host
            ORDER BY minute
            ROWS BETWEEN 60 PRECEDING AND 1 PRECEDING
        ) as avg_baseline,
        stddevPop(avg(value)) OVER (
            PARTITION BY host
            ORDER BY minute
            ROWS BETWEEN 60 PRECEDING AND 1 PRECEDING
        ) as stddev_baseline
    FROM system_metrics
    WHERE metric_name = 'cpu_usage_pct'
      AND collected_at >= now() - INTERVAL 4 HOUR
    GROUP BY host, minute
)
WHERE abs(z_score) > 3
ORDER BY abs(z_score) DESC;
```

---

## Analisi di Log ad Alto Volume

```sql
CREATE TABLE access_logs (
    log_date     Date DEFAULT toDate(request_time),
    request_time DateTime64(3),
    client_ip    IPv4,
    method       LowCardinality(String),
    path         String,
    status       UInt16,
    bytes_sent   UInt32,
    duration_ms  UInt32,
    user_agent   String,
    geo_country  LowCardinality(FixedString(2)),
    INDEX idx_status status TYPE set(20) GRANULARITY 4,
    INDEX idx_path   path   TYPE bloom_filter(0.01) GRANULARITY 4
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(log_date)
ORDER BY (log_date, request_time)
TTL log_date + INTERVAL 30 DAY DELETE;

-- Top endpoint per error rate
SELECT
    path,
    count() as total,
    countIf(status >= 500) as errors,
    round(countIf(status >= 500) / count() * 100, 2) as error_pct,
    avg(duration_ms) as avg_ms,
    quantile(0.95)(duration_ms) as p95_ms
FROM access_logs
WHERE log_date = today()
GROUP BY path
HAVING error_pct > 1
ORDER BY error_pct DESC, total DESC
LIMIT 50;

-- Top IP per richieste (rilevamento DDoS)
SELECT
    client_ip,
    count() as requests,
    uniq(path) as unique_paths,
    countIf(status >= 400) as errors
FROM access_logs
WHERE request_time >= now() - INTERVAL 5 MINUTE
GROUP BY client_ip
ORDER BY requests DESC
LIMIT 20;
```

---

## Data Warehouse Operativo: Reporting Finanziario

```sql
-- Tabella ordini con ReplacingMergeTree per upsert
CREATE TABLE orders (
    order_id     UInt64,
    updated_at   DateTime,
    customer_id  UInt64,
    status       LowCardinality(String),
    total_amount Decimal(12, 2),
    currency     LowCardinality(FixedString(3)),
    country      LowCardinality(String),
    channel      LowCardinality(String),
    items_count  UInt16,
    created_at   DateTime
) ENGINE = ReplicatedReplacingMergeTree('/ch/tables/s{shard}/orders', '{replica}', updated_at)
PARTITION BY toYYYYMM(toDate(created_at))
ORDER BY order_id;

-- Report: revenue mensile per canale e paese (con FINAL per deduplicazione)
SELECT
    toStartOfMonth(created_at) as month,
    channel,
    country,
    count() as orders,
    uniq(customer_id) as customers,
    sum(total_amount) as revenue,
    avg(total_amount) as aov  -- average order value
FROM orders FINAL  -- deduplicazione ReplacingMergeTree
WHERE status = 'completed'
  AND created_at >= toStartOfYear(today())
GROUP BY month, channel, country
ORDER BY month DESC, revenue DESC;

-- Running revenue YTD
SELECT
    month,
    revenue,
    sum(revenue) OVER (ORDER BY month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as ytd_revenue,
    revenue / lag(revenue) OVER (ORDER BY month) - 1 as mom_growth
FROM (
    SELECT toStartOfMonth(created_at) as month, sum(total_amount) as revenue
    FROM orders FINAL
    WHERE status = 'completed' AND toYear(created_at) = toYear(today())
    GROUP BY month
);
```

---

## IoT e Dati Sensori

```sql
CREATE TABLE sensor_readings (
    reading_time  DateTime,
    sensor_id     UInt32,
    sensor_type   LowCardinality(String),
    location_id   UInt16,
    temperature   Nullable(Float32) CODEC(Gorilla, LZ4),
    humidity      Nullable(Float32) CODEC(Gorilla, LZ4),
    pressure      Nullable(Float32) CODEC(Gorilla, LZ4),
    battery_level UInt8
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(reading_time)
ORDER BY (sensor_id, reading_time)
TTL reading_time + INTERVAL 1 YEAR TO VOLUME 'cold';

-- Downsampling: media per ora (aggregazione retrospettiva)
INSERT INTO sensor_readings_hourly
SELECT
    toStartOfHour(reading_time) as hour,
    sensor_id,
    avg(temperature) as avg_temp,
    min(temperature) as min_temp,
    max(temperature) as max_temp,
    avg(humidity) as avg_humidity
FROM sensor_readings
WHERE reading_time >= yesterday() AND reading_time < today()
GROUP BY hour, sensor_id;

-- Sliding window: trend degli ultimi 5 minuti
SELECT
    sensor_id,
    reading_time,
    temperature,
    avg(temperature) OVER (
        PARTITION BY sensor_id
        ORDER BY reading_time
        ROWS BETWEEN 4 PRECEDING AND CURRENT ROW
    ) as moving_avg_5
FROM sensor_readings
WHERE reading_time >= now() - INTERVAL 1 HOUR
ORDER BY sensor_id, reading_time;
```

---

## Ricerca Full-Text con N-gram Index

ClickHouse può fare ricerca full-text di base tramite n-gram bloom filter, adeguato per ricerche substring su log e testo strutturato.

```sql
CREATE TABLE product_catalog (
    product_id  UInt64,
    name        String,
    description String,
    brand       LowCardinality(String),
    sku         String,
    INDEX idx_name_ngram name TYPE ngrambf_v1(4, 65536, 3, 0) GRANULARITY 4,
    INDEX idx_desc_token description TYPE tokenbf_v1(32768, 3, 0) GRANULARITY 4,
    INDEX idx_sku sku TYPE bloom_filter(0.001) GRANULARITY 4
) ENGINE = MergeTree() ORDER BY product_id;

-- Ricerca substring (beneficia di ngrambf_v1)
SELECT product_id, name, brand
FROM product_catalog
WHERE name LIKE '%scarpe running%' OR description LIKE '%ammortizzazione%'
ORDER BY brand;

-- Ricerca esatta su SKU (beneficia di bloom_filter)
SELECT * FROM product_catalog WHERE sku = 'NK-AIR-MAX-001-42';
```

**Nota**: per full-text search avanzata (stemming, rilevanza, multilingual), Elasticsearch rimane la scelta migliore. ClickHouse è ottimale quando la ricerca è un requisito secondario rispetto all'analisi aggregata.

ClickHouse eccelle in tutti questi casi d'uso grazie alla combinazione di storage colonnare, esecuzione vettorizzata e un optimizer SQL che evita i colli di bottiglia I/O tipici dei database row-oriented.
