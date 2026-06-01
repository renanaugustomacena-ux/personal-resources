# ClickHouse — Aggregazioni e Funzioni Analitiche

## Funzioni Aggregate Fondamentali

ClickHouse offre decine di funzioni aggregate ottimizzate per il modello colonnare. La vectorized execution opera su intere colonne simultaneamente, sfruttando le istruzioni SIMD del processore.

```sql
-- Standard SQL aggregates
SELECT
    count()                    as total_rows,
    count(DISTINCT user_id)    as unique_users_exact,    -- O(n) memoria
    uniq(user_id)              as unique_users_approx,   -- HyperLogLog, ~2% error
    uniqExact(user_id)         as unique_users_exact_2,  -- identico a count(DISTINCT)
    sum(revenue)               as total_revenue,
    avg(revenue)               as avg_revenue,
    min(revenue)               as min_revenue,
    max(revenue)               as max_revenue,
    stddevPop(revenue)         as stddev_revenue,
    varPop(revenue)            as var_revenue,
    median(revenue)            as median_revenue         -- O(n) approssimato
FROM events
WHERE event_date >= today() - 30;
```

### Funzioni di Conteggio Condizionale

```sql
SELECT
    countIf(event = 'buy')                        as purchases,
    countIf(event = 'buy' AND revenue > 100)      as high_value_purchases,
    sumIf(revenue, event = 'buy')                 as purchase_revenue,
    avgIf(revenue, event = 'buy' AND revenue > 0) as avg_purchase_value,
    maxIf(revenue, event = 'buy')                 as max_purchase,
    uniqIf(user_id, event = 'buy')                as buyers
FROM events
WHERE event_date = today();
```

### Quantili e Percentili

```sql
SELECT
    quantile(0.5)(revenue)   as median,
    quantile(0.75)(revenue)  as p75,
    quantile(0.95)(revenue)  as p95,
    quantile(0.99)(revenue)  as p99,
    quantile(0.999)(revenue) as p999,
    -- Multipli percentili in una query (più efficiente che chiamate separate)
    quantiles(0.5, 0.75, 0.95, 0.99)(revenue) as percentiles_array
FROM events
WHERE event = 'buy';

-- quantileTDigest: algoritmo t-digest, miglior approssimazione per code della distribuzione
SELECT quantileTDigest(0.99)(revenue) FROM events WHERE event = 'buy';

-- quantileDeterministic: deterministico per sampling consistente
SELECT quantileDeterministic(0.5)(revenue, user_id) FROM events;
```

---

## Funzioni Aggregate per Analisi Avanzata

### argMin e argMax: Valore Correlato al Min/Max

```sql
-- Per ogni utente: l'evento più recente e il valore di revenue associato
SELECT
    user_id,
    argMax(event, event_time) as last_event,
    argMax(revenue, event_time) as revenue_at_last_event,
    argMin(event_time, event_time) as first_seen,
    max(event_time) as last_seen
FROM events
GROUP BY user_id
LIMIT 1000;
```

### topK: Elementi più Frequenti

```sql
-- Top 10 pagine per visite (approssimato, efficiente)
SELECT topK(10)(page) as top_pages FROM events;

-- topKWeighted: considera un peso
SELECT topKWeighted(10)(product_id, revenue) as top_revenue_products
FROM orders;
```

### groupArray e groupArrayIf

```sql
-- Array di tutti i valori per gruppo
SELECT
    user_id,
    groupArray(event) as event_sequence,
    groupArray(event_time) as timestamps
FROM events
WHERE user_id = 1001 AND event_date = today()
GROUP BY user_id
ORDER BY user_id;

-- Array limitato + ordinato
SELECT
    user_id,
    groupArrayMovingSum(revenue) as cumulative_revenue,  -- moving sum
    groupArray(10)(event) as last_10_events              -- solo gli ultimi 10
FROM events
GROUP BY user_id;
```

### Funzioni per Sequenze (windowFunnel, retention)

```sql
-- windowFunnel: funnel analysis
-- Quanti utenti hanno completato view → add_cart → buy in 24 ore
SELECT
    level,
    count() as users
FROM (
    SELECT
        user_id,
        windowFunnel(86400)(   -- finestra 24 ore in secondi
            toUnixTimestamp(event_time),
            event = 'view',
            event = 'add_cart',
            event = 'buy'
        ) as level
    FROM events
    WHERE event_date >= today() - 7
    GROUP BY user_id
)
GROUP BY level
ORDER BY level;

-- retention: calcola retention giorno per giorno
SELECT
    cohort_date,
    retention
FROM (
    SELECT
        user_id,
        min(event_date) as cohort_date,
        groupArray(event_date) as active_dates
    FROM events
    WHERE event = 'buy'
    GROUP BY user_id
)
ARRAY JOIN retention(
    active_dates,
    ['2024-01-01'::Date, '2024-01-08'::Date, '2024-01-15'::Date]
) WITH OFFSET AS offset, retention
GROUP BY cohort_date, offset;
```

---

## Aggregazioni su Array

ClickHouse supporta aggregazioni direttamente su array tramite `ARRAY JOIN` o funzioni higher-order.

```sql
-- ARRAY JOIN: esplode un array in righe
SELECT event_date, tag, count() as tag_count
FROM events
ARRAY JOIN tags  -- espande l'array tags in righe separate
GROUP BY event_date, tag
ORDER BY event_date, tag_count DESC;

-- arraySum, arrayAvg, arrayMap, arrayFilter
SELECT
    product_id,
    arraySum(prices) as total,
    arrayAvg(prices) as avg_price,
    arrayFilter(x -> x > 100, prices) as premium_prices,
    arrayMap(x -> x * 1.22, prices) as prices_with_vat
FROM product_variants;
```

---

## GROUP BY: Ottimizzazioni e Pattern

### ROLLUP e CUBE

```sql
-- ROLLUP: totali gerarchici
SELECT
    country,
    device,
    count() as events
FROM web_events
WHERE event_date = today()
GROUP BY ROLLUP(country, device)
ORDER BY country NULLS LAST, device NULLS LAST;
-- Produce: (IT, mobile), (IT, desktop), (IT, NULL), (DE, mobile), ..., (NULL, NULL)

-- CUBE: tutte le combinazioni di subtotali
GROUP BY CUBE(country, device)
-- Produce: (IT, mobile), (IT, NULL), (NULL, mobile), (NULL, NULL), ...

-- GROUPING SETS: subtotali specifici
GROUP BY GROUPING SETS (
    (country, device),
    (country),
    ()  -- grand total
)
```

### WITH TOTALS

```sql
SELECT country, sum(revenue) as revenue
FROM orders
WHERE event_date = today()
GROUP BY country WITH TOTALS
ORDER BY revenue DESC;
-- Aggiunge una riga finale con il totale complessivo
```

### Ottimizzazione della Memoria per GROUP BY

```sql
-- Per GROUP BY ad alta cardinalità che potrebbe sforare la RAM
SET max_bytes_before_external_group_by = 10000000000;  -- 10 GB prima di spill su disco
SET group_by_two_level_threshold = 100000;
SET group_by_two_level_threshold_bytes = 50000000;

-- Aggregazione parallela su più thread
SET max_threads = 16;
```

---

## Window Functions

ClickHouse supporta window functions dal 2021. Sintassi compatibile con SQL standard.

```sql
-- Row number, rank, dense_rank
SELECT
    user_id,
    event_time,
    revenue,
    row_number()   OVER (PARTITION BY user_id ORDER BY event_time) as rn,
    rank()         OVER (PARTITION BY user_id ORDER BY revenue DESC) as rev_rank,
    dense_rank()   OVER (PARTITION BY user_id ORDER BY revenue DESC) as rev_dense_rank,
    lag(revenue, 1, 0)  OVER (PARTITION BY user_id ORDER BY event_time) as prev_revenue,
    lead(revenue, 1, 0) OVER (PARTITION BY user_id ORDER BY event_time) as next_revenue
FROM events
WHERE event = 'buy' AND event_date >= today() - 7;

-- Running totals e medie mobili
SELECT
    event_date,
    daily_revenue,
    sum(daily_revenue) OVER (ORDER BY event_date
                             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as cumulative,
    avg(daily_revenue) OVER (ORDER BY event_date
                             ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as ma7
FROM (
    SELECT event_date, sum(revenue) as daily_revenue
    FROM events
    GROUP BY event_date
);
```

---

## Aggregazioni Incrementali con Materialized Views

Il pattern per dashboard real-time che aggiornano aggregati senza ricalcolare tutto:

```sql
-- Tabella raw
CREATE TABLE page_views_raw (
    ts      DateTime,
    page    String,
    country LowCardinality(FixedString(2)),
    user_id UInt64
) ENGINE = MergeTree()
ORDER BY ts;

-- Tabella aggregata per minuto
CREATE TABLE page_views_1min (
    minute    DateTime,
    page      String,
    country   LowCardinality(FixedString(2)),
    views     AggregateFunction(count),
    users     AggregateFunction(uniq, UInt64)
) ENGINE = AggregatingMergeTree()
PARTITION BY toYYYYMM(minute)
ORDER BY (minute, page, country);

CREATE MATERIALIZED VIEW mv_pv_1min TO page_views_1min AS
SELECT
    toStartOfMinute(ts) as minute,
    page,
    country,
    countState() as views,
    uniqState(user_id) as users
FROM page_views_raw
GROUP BY minute, page, country;

-- Query finale: combina stati parziali
SELECT
    minute,
    page,
    countMerge(views) as views,
    uniqMerge(users) as unique_users
FROM page_views_1min
WHERE minute >= now() - INTERVAL 1 HOUR
GROUP BY minute, page
ORDER BY minute DESC, views DESC;
```

---

## Funzioni Speciali per Analisi Temporale

```sql
-- Bucket temporali
SELECT
    toStartOfHour(event_time)   as hour,
    toStartOfDay(event_time)    as day,
    toStartOfWeek(event_time)   as week,
    toStartOfMonth(event_time)  as month,
    toMonday(event_time)        as monday_of_week,
    toDayOfWeek(event_time)     as day_of_week,
    toHour(event_time)          as hour_of_day
FROM events;

-- Confronto periodi: questo mese vs mese scorso
SELECT
    countIf(toMonth(event_date) = toMonth(today())) as this_month,
    countIf(toMonth(event_date) = toMonth(today() - 31)) as last_month
FROM events
WHERE event_date >= toStartOfMonth(today() - 31);

-- Funzione date_diff
SELECT
    user_id,
    min(event_time) as first_seen,
    max(event_time) as last_seen,
    dateDiff('day', min(event_time), max(event_time)) as days_active
FROM events
GROUP BY user_id
HAVING days_active > 0;
```

Le aggregazioni di ClickHouse combinano la velocità di esecuzione vettorizzata con una libreria di funzioni specializzate per l'analisi di dati di eventi, metriche e log — rendendolo ideale per piattaforme analytics, dashboard real-time e data warehouse operativi.
