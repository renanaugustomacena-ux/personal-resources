# Query Optimisation in the Data Warehouse

Query optimisation in a data warehouse is a different discipline from OLTP optimisation. In
a DW you work with billions of rows, joins between fact tables with hundreds of millions of
records and dimension tables with millions, and queries that must complete in seconds for
interactive BI. The principles are: minimise the data read (predicate pushdown, partition
pruning, projection), minimise data movement (join colocation, hash distribution), and
reuse computation (materialised views, result caching).

---

## Table of Contents

1. Execution Plans — Reading EXPLAIN Output
2. Join Algorithms
3. Partition Pruning
4. Predicate Pushdown and Filter Propagation
5. Materialised Views
6. Result Caching
7. Query Rewriting Techniques
8. Statistics and the Query Planner
9. Window Functions — Performance Patterns
10. Common Anti-Patterns
11. Platform-Specific Optimisation
12. Troubleshooting
13. Frequently Asked Questions
14. Exercises

---

## 1. Execution Plans — Reading EXPLAIN Output

The execution plan is the most important tool for query optimisation. It shows exactly how
the database engine will (or did) execute a query: which tables are scanned, which indexes
are used, which join algorithm is chosen, and where time is spent.

### 1.1 PostgreSQL EXPLAIN

```sql
-- Basic explain (estimated plan, does not execute the query)
EXPLAIN
SELECT d.year, p.category, SUM(f.net_revenue) AS revenue
FROM fact_sales f
  JOIN dim_date    d ON f.date_key    = d.date_key
  JOIN dim_product p ON f.product_key = p.product_key
WHERE d.year = 2024
GROUP BY d.year, p.category;

-- Explain with execution (runs the query, shows actual timing and rows)
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT d.year, p.category, SUM(f.net_revenue) AS revenue
FROM fact_sales f
  JOIN dim_date    d ON f.date_key    = d.date_key
  JOIN dim_product p ON f.product_key = p.product_key
WHERE d.year = 2024
GROUP BY d.year, p.category;
```

### 1.2 Reading the Plan — Key Fields

```
HashAggregate  (cost=1234.56..1234.78 rows=50 width=48) (actual time=45.2..45.5 rows=48 loops=1)
  Group Key: d.year, p.category
  Buffers: shared hit=1200 read=300
  ->  Hash Join  (cost=100.00..1100.00 rows=50000 width=24) (actual time=5.1..40.0 rows=49800 loops=1)
        Hash Cond: (f.product_key = p.product_key)
        ->  Hash Join  (cost=10.00..900.00 rows=50000 width=16) (actual time=1.2..25.0 rows=49800 loops=1)
              Hash Cond: (f.date_key = d.date_key)
              ->  Seq Scan on fact_sales f  (cost=0.00..800.00 rows=1000000 width=16) (actual time=0.01..15.0 rows=1000000 loops=1)
                    Buffers: shared hit=800 read=200
              ->  Hash  (cost=8.00..8.00 rows=365 width=8) (actual time=0.5..0.5 rows=365 loops=1)
                    ->  Seq Scan on dim_date d  (cost=0.00..8.00 rows=365 width=8) (actual time=0.01..0.3 rows=365 loops=1)
                          Filter: (year = 2024)
                          Rows Removed by Filter: 3287
        ->  Hash  (cost=50.00..50.00 rows=5000 width=20) (actual time=2.0..2.0 rows=5000 loops=1)
              ->  Seq Scan on dim_product p  (cost=0.00..50.00 rows=5000 width=20) (actual time=0.01..1.0 rows=5000 loops=1)
```

**Key fields to interpret:**

| Field                     | Meaning                                                    |
|---------------------------|------------------------------------------------------------|
| `cost=start..total`       | Estimated cost in arbitrary units (lower is better)        |
| `rows=N`                  | Estimated row count (compare with `actual rows`)           |
| `actual time=start..total`| Real wall-clock time in milliseconds                       |
| `actual rows`             | Real row count (if very different from estimated → stale stats)|
| `loops=N`                 | How many times this node was executed                      |
| `Buffers: shared hit`     | Pages read from the buffer cache (fast)                    |
| `Buffers: shared read`    | Pages read from disk (slow — high values = I/O bottleneck) |
| `Rows Removed by Filter`  | Rows scanned but discarded by a filter (high = inefficient)|

### 1.3 Warning Signs in Execution Plans

| Warning sign                             | What it means                                 | Action                              |
|------------------------------------------|-----------------------------------------------|-------------------------------------|
| `Seq Scan` on large fact table           | Full table scan — no index or pruning engaged | Add index, partition, or fix filter  |
| `estimated rows` ≫ `actual rows`         | Stale or missing statistics                   | Run ANALYZE                         |
| `estimated rows` ≪ `actual rows`         | Underestimate → bad join plan choice          | Run ANALYZE, add histogram stats    |
| `Nested Loop` with large inner table     | O(n×m) — extremely slow for large tables      | Force hash join or add index         |
| `Sort` with large data and no index      | Spills to disk                                | Add index on sort column             |
| High `Rows Removed by Filter`            | Scanning data that is immediately discarded   | Push filter earlier / add index      |
| `Buffers: shared read` ≫ `shared hit`    | Cold cache or working set exceeds memory      | Increase shared_buffers or reduce scan|

### 1.4 BigQuery Execution Plan

```sql
-- BigQuery does not have EXPLAIN; instead, inspect completed query details

-- Method 1: Query execution details in the BigQuery console
-- (Job Information → Execution Details → shows stages, slots, bytes shuffled)

-- Method 2: INFORMATION_SCHEMA
SELECT
  job_id,
  ROUND(total_bytes_processed / POW(1024, 3), 3)  AS gb_scanned,
  ROUND(total_bytes_billed / POW(1024, 3), 3)      AS gb_billed,
  total_slot_ms / 1000                              AS slot_seconds,
  TIMESTAMP_DIFF(end_time, start_time, SECOND)      AS wall_clock_s,
  cache_hit,
  query
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE start_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
  AND job_type = 'QUERY'
ORDER BY total_bytes_processed DESC
LIMIT 20;

-- Key metrics:
-- total_bytes_processed: raw bytes scanned (drives on-demand cost)
-- total_slot_ms: compute used (drives flat-rate utilisation)
-- cache_hit: if TRUE, query result was served from cache (no bytes billed)
```

### 1.5 Snowflake Query Profile

```sql
-- Snowflake provides a graphical Query Profile in the web UI
-- (query_id → Profile tab → shows operator tree with timing, partitions, spilling)

-- Programmatic access:
SELECT
  query_id,
  query_text,
  total_elapsed_time / 1000 AS elapsed_s,
  bytes_scanned / 1024 / 1024 AS mb_scanned,
  partitions_scanned,
  partitions_total,
  ROUND(partitions_scanned * 100.0 / NULLIF(partitions_total, 0), 2) AS pct_partitions,
  bytes_spilled_to_local_storage / 1024 / 1024 AS mb_spilled_local,
  bytes_spilled_to_remote_storage / 1024 / 1024 AS mb_spilled_remote
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY(
  date_range_start => DATEADD('hours', -24, CURRENT_TIMESTAMP())
))
WHERE execution_status = 'SUCCESS'
ORDER BY total_elapsed_time DESC
LIMIT 20;

-- Key warning signs in Snowflake:
-- pct_partitions > 50%  → poor clustering, consider CLUSTER BY
-- mb_spilled_local > 0  → query needs more memory, increase warehouse size
-- mb_spilled_remote > 0 → severe memory pressure, definitely increase warehouse
```

---

## 2. Join Algorithms

The choice of join algorithm has a dramatic impact on query performance. Understanding how
each algorithm works helps you write queries that the optimiser can execute efficiently.

### 2.1 Nested Loop Join

```
Algorithm:
  for each row in outer_table:
    for each row in inner_table:
      if join_condition matches:
        emit combined row

Complexity: O(n × m)
Best for: inner table has very few rows (< 1000) or is indexed
Worst for: both tables are large (quadratic explosion)
```

```sql
-- Nested loop is fine here: dim_channel has 10 rows
SELECT f.*, ch.channel_name
FROM fact_sales f
  JOIN dim_channel ch ON f.channel_key = ch.channel_key;
-- The planner will scan fact_sales once and, for each row, do a quick lookup in
-- the 10-row dim_channel. Total: 10M × 10 lookups ≈ 10M operations.
```

### 2.2 Hash Join

```
Algorithm:
  Phase 1 (Build): scan the smaller table, build a hash table on the join key
  Phase 2 (Probe): scan the larger table, probe the hash table for matches

Complexity: O(n + m)  (linear)
Best for: large tables without useful indexes (the DW default)
Requirement: the build table must fit in memory (otherwise spills to disk)
```

```sql
-- Hash join: the workhorse of DW query engines
-- The planner builds a hash table on dim_product (5K rows), then probes with fact_sales
SELECT p.category, SUM(f.net_revenue) AS revenue
FROM fact_sales f
  JOIN dim_product p ON f.product_key = p.product_key
GROUP BY p.category;

-- If the build side is too large for memory, the engine spills to disk.
-- Snowflake's Query Profile shows "bytes_spilled_to_local_storage" for this.
```

### 2.3 Merge Join (Sort-Merge Join)

```
Algorithm:
  Phase 1: sort both tables on the join key (if not already sorted)
  Phase 2: walk through both sorted lists in parallel, matching rows

Complexity: O(n log n + m log m) for sorting; O(n + m) for merging
Best for: both tables are already sorted on the join key (sort key / cluster key)
Advantage: handles very large tables without building a hash table
```

```sql
-- Merge join benefits from sort keys
-- If fact_sales is sorted by date_key and dim_date is sorted by date_key,
-- the merge join can proceed without any sorting step.
-- In Redshift, SORTKEY(date_key) enables this.
```

### 2.4 Broadcast Join (Map-Side Join)

```
In distributed systems (Spark, BigQuery, Snowflake):
  If one table is small enough, broadcast it to all compute nodes.
  Each node then joins its partition of the large table with the full small table locally.

This avoids shuffling the large table across the network.

When it fires:
  - BigQuery: automatic (BQ decides based on table sizes)
  - Snowflake: automatic
  - Spark: broadcast hint or autoBroadcastJoinThreshold
  - Redshift: DISTSTYLE ALL on the small table achieves the same effect
```

```sql
-- Spark: explicit broadcast hint
SELECT /*+ BROADCAST(dim_product) */
  f.date_key,
  p.category,
  SUM(f.net_revenue) AS revenue
FROM fact_sales f
  JOIN dim_product p ON f.product_key = p.product_key
GROUP BY f.date_key, p.category;
```

### 2.5 Join Algorithm Selection Guide

```
┌────────────────────────────────────┬──────────────────────────────────────────┐
│ Scenario                           │ Best join algorithm                      │
├────────────────────────────────────┼──────────────────────────────────────────┤
│ Small dimension (< 10K rows)       │ Broadcast / Nested loop with index       │
│ Medium dimension (10K – 10M rows)  │ Hash join                                │
│ Two large tables, both sorted      │ Merge join                               │
│ Two large tables, unsorted         │ Hash join (may spill)                    │
│ Fact-to-fact join (both huge)      │ Hash join with partition-wise join        │
│ Star schema (fact × N dimensions)  │ Hash join per dimension (default in DWs) │
└────────────────────────────────────┴──────────────────────────────────────────┘
```

---

## 3. Partition Pruning

Partition pruning eliminates entire partitions (directories of files, or segments of a
table) from a query scan based on the WHERE clause. It is the single most effective cost
and performance lever for time-series data.

```sql
-- BigQuery: partition by date
CREATE TABLE `analytics.fact_sales`
PARTITION BY DATE(created_at)
OPTIONS (require_partition_filter = TRUE);

-- This query scans 1 partition (1 day) instead of 365
SELECT SUM(net_revenue)
FROM `analytics.fact_sales`
WHERE DATE(created_at) = '2024-06-15';

-- WARNING: wrapping the partition column in a function can defeat pruning
-- BAD: EXTRACT(YEAR FROM created_at) = 2024
--   → Some engines cannot prune because the expression is not a range on the column
-- GOOD: created_at >= '2024-01-01' AND created_at < '2025-01-01'
--   → Direct range on the partition column → pruning works

-- Snowflake: cluster keys serve a similar purpose (micro-partition pruning)
ALTER TABLE fact_sales CLUSTER BY (date_key);
-- Queries with WHERE date_key BETWEEN 20240601 AND 20240630
-- will scan only the micro-partitions that overlap this range.
```

### 3.1 Partition Pruning Verification

```sql
-- BigQuery: check bytes scanned with and without partition filter
-- Query 1 (with filter): scans ~27 GB (one day of a 10 TB table)
SELECT SUM(revenue) FROM fact_sales WHERE DATE(created_at) = '2024-06-15';

-- Query 2 (without filter): scans all 10 TB
SELECT SUM(revenue) FROM fact_sales;

-- Snowflake: check partitions_scanned vs partitions_total
SELECT
  partitions_scanned,
  partitions_total,
  ROUND(partitions_scanned * 100.0 / NULLIF(partitions_total, 0), 2) AS pct
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
WHERE query_id = '<your_query_id>';
-- If pct is close to 100%, pruning is not effective → check cluster keys.

-- Redshift: check zone-map effectiveness
EXPLAIN
SELECT * FROM fact_sales WHERE date_key = 20240615;
-- Look for "Filter" vs "Seq Scan" — if the sort key is date_key,
-- zone maps skip blocks outside the range.
```

---

## 4. Predicate Pushdown and Filter Propagation

### 4.1 Predicate Pushdown

The optimiser pushes WHERE conditions as close to the data source as possible — to the
storage layer (Parquet row groups, micro-partitions, zone maps) rather than filtering after
a full scan.

```sql
-- GOOD: predicate on dimension propagated to fact table via join
SELECT p.category, SUM(f.net_revenue)
FROM fact_sales f
  JOIN dim_product p ON f.product_key = p.product_key
WHERE p.category = 'Electronics'
GROUP BY p.category;

-- The optimiser should:
-- 1. Scan dim_product WHERE category = 'Electronics' → find matching product_keys
-- 2. Use those product_keys to prune fact_sales (semi-join / hash filter)
-- This avoids scanning the entire fact table.

-- BAD: function on the join key blocks pushdown
SELECT *
FROM fact_sales f
  JOIN dim_date d ON CAST(f.date_key AS VARCHAR) = d.date_key_str;
-- The CAST prevents the optimiser from using statistics on date_key.
-- Fix: join on the raw integer key.
```

### 4.2 Filter Propagation Through Joins

```sql
-- The optimiser can propagate filters through equi-joins.
-- If f.date_key = d.date_key AND d.year = 2024, the optimiser infers:
-- f.date_key must be in the range of date_keys where d.year = 2024.

-- Some optimisers do this automatically. Others benefit from explicit rewriting:

-- Explicit filter on fact table (helps less sophisticated optimisers)
SELECT d.year, p.category, SUM(f.net_revenue)
FROM fact_sales f
  JOIN dim_date    d ON f.date_key = d.date_key
  JOIN dim_product p ON f.product_key = p.product_key
WHERE d.year = 2024
  AND f.date_key BETWEEN 20240101 AND 20241231  -- redundant but helps pruning
GROUP BY d.year, p.category;
```

### 4.3 Semi-Join Reduction

```sql
-- Instead of a full join, use EXISTS / IN for filtering when you don't need
-- columns from the filter table:

-- Full join (reads all columns from dim_product into the result)
SELECT f.*
FROM fact_sales f
  JOIN dim_product p ON f.product_key = p.product_key
WHERE p.category = 'Electronics';

-- Semi-join (only uses dim_product for filtering, does not materialise it)
SELECT f.*
FROM fact_sales f
WHERE f.product_key IN (
  SELECT product_key FROM dim_product WHERE category = 'Electronics'
);

-- The semi-join avoids the overhead of hash-building the full dim_product table
-- and avoids potential row duplication if the join is not 1:1.
```

---

## 5. Materialised Views

Materialised views store the precomputed result of a query. When a user query can be
satisfied by the materialised view, the engine reads the view instead of recomputing from
the base tables.

### 5.1 PostgreSQL

```sql
CREATE MATERIALIZED VIEW mv_daily_revenue AS
SELECT
  date_key,
  product_key,
  SUM(net_revenue) AS daily_revenue,
  COUNT(*)         AS transaction_count,
  SUM(quantity)    AS units_sold
FROM fact_sales
GROUP BY date_key, product_key;

-- Create indexes on the materialised view for fast lookups
CREATE UNIQUE INDEX idx_mv_daily_revenue_pk ON mv_daily_revenue(date_key, product_key);
CREATE INDEX idx_mv_daily_revenue_date ON mv_daily_revenue(date_key);

-- Refresh (must be done manually or via cron / scheduler)
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_revenue;
-- CONCURRENTLY: updates without locking readers (requires a unique index)

-- Use the materialised view
SELECT date_key, SUM(daily_revenue) AS total
FROM mv_daily_revenue
WHERE date_key BETWEEN 20240101 AND 20240131
GROUP BY date_key
ORDER BY date_key;
```

### 5.2 BigQuery

```sql
-- BigQuery materialised views are automatically maintained
CREATE MATERIALIZED VIEW `analytics.mv_daily_product_revenue`
PARTITION BY date_key
CLUSTER BY product_key
OPTIONS (
  enable_refresh = TRUE,
  refresh_interval_minutes = 60,
  max_staleness = INTERVAL '4' HOUR   -- queries tolerate up to 4h stale data
)
AS SELECT
  DATE(created_at) AS date_key,
  product_key,
  SUM(net_revenue) AS revenue,
  COUNT(*)         AS transactions
FROM `analytics.fact_sales`
GROUP BY 1, 2;

-- BigQuery automatically uses the materialised view when a query matches.
-- No explicit reference needed — the optimiser rewrites the query.
```

### 5.3 Snowflake Dynamic Tables

```sql
-- Dynamic tables replace materialised views in Snowflake
-- They support arbitrary SQL (not just aggregations) and auto-refresh.

CREATE DYNAMIC TABLE mart.customer_lifetime_value
  TARGET_LAG = '30 minutes'
  WAREHOUSE = etl_wh
AS
SELECT
  c.customer_key,
  c.first_name || ' ' || c.last_name AS customer_name,
  c.segment,
  COUNT(*)               AS total_orders,
  SUM(f.net_revenue)     AS lifetime_value,
  MIN(f.date_key)        AS first_order_date,
  MAX(f.date_key)        AS last_order_date,
  DATEDIFF('day',
    TO_DATE(MIN(f.date_key)::VARCHAR, 'YYYYMMDD'),
    TO_DATE(MAX(f.date_key)::VARCHAR, 'YYYYMMDD'))
                         AS customer_tenure_days
FROM fact_sales f
  JOIN dim_customer c ON f.customer_key = c.customer_key
WHERE c.is_current = TRUE
GROUP BY c.customer_key, customer_name, c.segment;

-- Snowflake handles refresh scheduling automatically.
-- Check refresh status:
SELECT * FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
  NAME => 'mart.customer_lifetime_value',
  DATA_TIMESTAMP_START => DATEADD('hours', -24, CURRENT_TIMESTAMP())
));
```

### 5.4 When to Materialise

| Situation                                        | Materialise? |
|--------------------------------------------------|--------------|
| Dashboard query runs every 5 minutes, scans 1 TB | Yes          |
| Ad-hoc exploration query, run once               | No           |
| Nightly report, runs once per day                 | Maybe (if it takes > 5 min) |
| Shared CTE used by 10 downstream queries          | Yes          |
| Aggregation over the last 24 hours, used by API   | Yes          |

---

## 6. Result Caching

### 6.1 How Result Caching Works

Most cloud DWs cache query results. If the same query is run again and the underlying data
has not changed, the cached result is returned instantly without consuming compute.

```sql
-- BigQuery: automatic result caching (free, lasts 24 hours)
-- Run query → BigQuery caches the result
-- Run same query again → cache_hit = TRUE, total_bytes_billed = 0

-- Snowflake: result cache (lasts 24 hours, per-warehouse)
-- Run query → Snowflake caches the result
-- Run same query again → returns in milliseconds (warehouse not resumed)

-- Redshift: result cache enabled by default
-- enable_result_cache_for_session = on (default)
SET enable_result_cache_for_session TO on;
```

### 6.2 Cache Invalidation

Caches are invalidated when:
- The underlying table's data changes (INSERT, UPDATE, DELETE, MERGE).
- The table's metadata changes (ALTER TABLE, REFRESH MATERIALIZED VIEW).
- The cache TTL expires (24 hours in most platforms).
- The query contains non-deterministic functions (CURRENT_TIMESTAMP, RANDOM).

```sql
-- BAD: this query will never cache because CURRENT_TIMESTAMP changes every call
SELECT * FROM fact_sales WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '7 days';

-- GOOD: fix the date boundary to enable caching
SELECT * FROM fact_sales WHERE created_at > '2024-06-08';
-- Same result, but now the query is deterministic and can be cached.
```

---

## 7. Query Rewriting Techniques

### 7.1 Aggregate Before Join

```sql
-- BAD: join first, then aggregate (processes all rows through the join)
SELECT c.segment, SUM(f.net_revenue) AS revenue
FROM fact_sales f
  JOIN dim_customer c ON f.customer_key = c.customer_key
WHERE c.country = 'US'
GROUP BY c.segment;

-- BETTER: filter the dimension first (reduce join input)
SELECT c.segment, SUM(f.net_revenue) AS revenue
FROM fact_sales f
  JOIN (
    SELECT customer_key, segment FROM dim_customer WHERE country = 'US'
  ) c ON f.customer_key = c.customer_key
GROUP BY c.segment;

-- BEST (for very large fact tables): pre-aggregate the fact, then join
SELECT c.segment, SUM(agg.total_revenue) AS revenue
FROM (
  SELECT customer_key, SUM(net_revenue) AS total_revenue
  FROM fact_sales
  GROUP BY customer_key
) agg
  JOIN dim_customer c ON agg.customer_key = c.customer_key
WHERE c.country = 'US'
GROUP BY c.segment;
-- This reduces the number of rows entering the join from 100M to ~1M
```

### 7.2 Avoid the Fan Trap

```sql
-- The fan trap occurs when joining two fact tables through a shared dimension,
-- causing row multiplication.

-- BAD: joining fact_sales and fact_returns through dim_customer
-- If a customer has 50 sales and 3 returns, the join produces 150 rows.
-- SUM(sales.net_revenue) is inflated 3x.
SELECT
  c.customer_key,
  SUM(s.net_revenue) AS total_sales,       -- WRONG: inflated by returns
  SUM(r.refund_amount) AS total_refunds    -- WRONG: inflated by sales
FROM dim_customer c
  JOIN fact_sales   s ON c.customer_key = s.customer_key
  JOIN fact_returns r ON c.customer_key = r.customer_key
GROUP BY c.customer_key;

-- CORRECT: aggregate each fact table independently, then join the results
WITH sales_agg AS (
  SELECT customer_key, SUM(net_revenue) AS total_sales
  FROM fact_sales
  GROUP BY customer_key
),
returns_agg AS (
  SELECT customer_key, SUM(refund_amount) AS total_refunds
  FROM fact_returns
  GROUP BY customer_key
)
SELECT
  c.customer_key,
  COALESCE(s.total_sales, 0) AS total_sales,
  COALESCE(r.total_refunds, 0) AS total_refunds
FROM dim_customer c
  LEFT JOIN sales_agg   s ON c.customer_key = s.customer_key
  LEFT JOIN returns_agg r ON c.customer_key = r.customer_key;
```

### 7.3 Replace Correlated Subqueries

```sql
-- BAD: correlated subquery (executed once per row of the outer query)
SELECT
  f.order_id,
  f.net_revenue,
  (SELECT SUM(f2.net_revenue)
   FROM fact_sales f2
   WHERE f2.customer_key = f.customer_key) AS customer_lifetime_value
FROM fact_sales f
WHERE f.date_key = 20240615;
-- This runs the inner SUM once for EACH row in the outer query.

-- GOOD: rewrite as a join with a pre-aggregated CTE
WITH clv AS (
  SELECT customer_key, SUM(net_revenue) AS lifetime_value
  FROM fact_sales
  GROUP BY customer_key
)
SELECT
  f.order_id,
  f.net_revenue,
  clv.lifetime_value AS customer_lifetime_value
FROM fact_sales f
  JOIN clv ON f.customer_key = clv.customer_key
WHERE f.date_key = 20240615;
```

### 7.4 Use QUALIFY Instead of Subquery for Window Filters

```sql
-- BAD: nested subquery to filter by window function result
SELECT * FROM (
  SELECT
    product_key,
    category,
    net_revenue,
    ROW_NUMBER() OVER (PARTITION BY category ORDER BY net_revenue DESC) AS rn
  FROM fact_sales f
    JOIN dim_product p ON f.product_key = p.product_key
) sub
WHERE rn <= 3;

-- GOOD (Snowflake, BigQuery, DuckDB): QUALIFY clause
SELECT
  product_key,
  category,
  net_revenue
FROM fact_sales f
  JOIN dim_product p ON f.product_key = p.product_key
QUALIFY ROW_NUMBER() OVER (PARTITION BY category ORDER BY net_revenue DESC) <= 3;
-- Simpler, and the optimiser can sometimes avoid materialising the window result.
```

### 7.5 APPROX Functions for Large-Scale Aggregations

```sql
-- Exact COUNT(DISTINCT) on a billion-row table is expensive (requires hashing all values)
SELECT COUNT(DISTINCT customer_key) FROM fact_sales;  -- slow

-- Approximate count (HyperLogLog): ~1% error, much faster
-- BigQuery:
SELECT APPROX_COUNT_DISTINCT(customer_key) FROM fact_sales;

-- Snowflake:
SELECT APPROX_COUNT_DISTINCT(customer_key) FROM fact_sales;
-- Equivalent: SELECT HLL(customer_key) FROM fact_sales;

-- Approximate percentiles
SELECT APPROX_QUANTILES(net_revenue, 100)[OFFSET(50)] AS median_revenue
FROM fact_sales;   -- BigQuery syntax
```

---

## 8. Statistics and the Query Planner

### 8.1 Why Statistics Matter

The query planner uses table statistics (row counts, column cardinality, value
distribution) to estimate the cost of different execution strategies. With bad statistics,
the planner makes bad choices (e.g., nested loop on a large table, wrong join order).

### 8.2 Collecting Statistics

```sql
-- PostgreSQL: manual statistics collection
ANALYZE fact_sales;                        -- all columns
ANALYZE fact_sales(date_key, customer_key); -- specific columns

-- Check column statistics
SELECT
  attname,
  n_distinct,
  most_common_vals,
  most_common_freqs,
  correlation        -- how well the physical order matches the logical order
FROM pg_stats
WHERE tablename = 'fact_sales'
  AND attname IN ('date_key', 'customer_key');

-- Increase statistics target for columns with skewed distributions
ALTER TABLE fact_sales ALTER COLUMN customer_key SET STATISTICS 1000;
-- Default is 100; increase for columns where the planner underestimates cardinality.
ANALYZE fact_sales(customer_key);

-- Redshift: ANALYZE (runs automatically for RA3/Serverless, manual for DC2)
ANALYZE fact_sales;
ANALYZE PREDICATE COLUMNS fact_sales;  -- only columns used in WHERE/JOIN

-- BigQuery: automatic (no manual statistics collection needed)
-- Snowflake: automatic (metadata maintained on every DML operation)
```

### 8.3 Stale Statistics Symptoms

```sql
-- Symptom: estimated rows wildly different from actual rows
EXPLAIN ANALYZE SELECT * FROM fact_sales WHERE customer_key = 42;

-- If plan says "rows=1" but actual is "rows=50000":
-- → Statistics think customer_key=42 appears once, but it appears 50K times.
-- → The planner may choose a nested loop join instead of a hash join.

-- Fix: re-run ANALYZE after loading data.
-- Automate: schedule ANALYZE after every ETL batch.
```

---

## 9. Window Functions — Performance Patterns

### 9.1 Running Totals (Year-to-Date)

```sql
SELECT
  d.year,
  d.month_number,
  SUM(f.net_revenue) AS monthly_revenue,
  SUM(SUM(f.net_revenue)) OVER (
    PARTITION BY d.year
    ORDER BY d.month_number
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) AS ytd_revenue
FROM fact_sales f
  JOIN dim_date d ON f.date_key = d.date_key
GROUP BY d.year, d.month_number
ORDER BY d.year, d.month_number;
```

### 9.2 Year-over-Year Comparison

```sql
SELECT
  d.year,
  d.month_number,
  SUM(f.net_revenue) AS monthly_revenue,
  LAG(SUM(f.net_revenue)) OVER (
    PARTITION BY d.month_number
    ORDER BY d.year
  ) AS prev_year_revenue,
  ROUND(
    (SUM(f.net_revenue) - LAG(SUM(f.net_revenue)) OVER (
      PARTITION BY d.month_number ORDER BY d.year
    )) * 100.0
    / NULLIF(LAG(SUM(f.net_revenue)) OVER (
      PARTITION BY d.month_number ORDER BY d.year
    ), 0)
  , 2) AS yoy_growth_pct
FROM fact_sales f
  JOIN dim_date d ON f.date_key = d.date_key
WHERE d.year IN (2023, 2024)
GROUP BY d.year, d.month_number
ORDER BY d.year, d.month_number;
```

### 9.3 Cohort Retention Analysis

```sql
WITH first_purchase AS (
  SELECT
    customer_key,
    MIN(date_key) AS first_purchase_date_key
  FROM fact_sales
  GROUP BY customer_key
),
cohort_assigned AS (
  SELECT
    fp.customer_key,
    d_first.year  AS cohort_year,
    d_first.month_number AS cohort_month
  FROM first_purchase fp
    JOIN dim_date d_first ON fp.first_purchase_date_key = d_first.date_key
),
monthly_activity AS (
  SELECT DISTINCT
    f.customer_key,
    d.year  AS activity_year,
    d.month_number AS activity_month
  FROM fact_sales f
    JOIN dim_date d ON f.date_key = d.date_key
)
SELECT
  ca.cohort_year,
  ca.cohort_month,
  (ma.activity_year - ca.cohort_year) * 12
    + (ma.activity_month - ca.cohort_month) AS month_offset,
  COUNT(DISTINCT ma.customer_key) AS active_customers,
  ROUND(
    COUNT(DISTINCT ma.customer_key) * 100.0
    / MAX(COUNT(DISTINCT ma.customer_key)) OVER (
      PARTITION BY ca.cohort_year, ca.cohort_month
    )
  , 2) AS retention_pct
FROM cohort_assigned ca
  JOIN monthly_activity ma ON ca.customer_key = ma.customer_key
GROUP BY ca.cohort_year, ca.cohort_month, month_offset
ORDER BY ca.cohort_year, ca.cohort_month, month_offset;
```

### 9.4 Top-N Per Category

```sql
-- Top 3 products per category by revenue
SELECT category, product_name, revenue, rank_in_category
FROM (
  SELECT
    p.category,
    p.product_name,
    SUM(f.net_revenue) AS revenue,
    RANK() OVER (PARTITION BY p.category ORDER BY SUM(f.net_revenue) DESC)
      AS rank_in_category
  FROM fact_sales f
    JOIN dim_product p ON f.product_key = p.product_key
  GROUP BY p.category, p.product_name
) ranked
WHERE rank_in_category <= 3
ORDER BY category, rank_in_category;
```

---

## 10. Common Anti-Patterns

### 10.1 SELECT * in Production Queries

In columnar databases, `SELECT *` reads every column. In BigQuery, this directly
increases cost. In all columnar engines, it wastes I/O.

### 10.2 Functions on Filter Columns

```sql
-- BAD: function on the indexed/partitioned column
WHERE EXTRACT(YEAR FROM created_at) = 2024
-- The engine cannot use partition pruning or index seeks.

-- GOOD: range predicate on the raw column
WHERE created_at >= '2024-01-01' AND created_at < '2025-01-01'
```

### 10.3 Cartesian Products from Missing Join Conditions

```sql
-- BAD: accidental cross join (missing ON clause)
SELECT * FROM fact_sales, dim_product;
-- If fact_sales has 100M rows and dim_product has 5K, this produces 500 BILLION rows.

-- GOOD: always verify JOIN conditions
SELECT * FROM fact_sales f JOIN dim_product p ON f.product_key = p.product_key;
```

### 10.4 ORDER BY Without LIMIT

```sql
-- BAD: sorting a billion rows just to display in a dashboard
SELECT * FROM fact_sales ORDER BY net_revenue DESC;

-- GOOD: always limit sorted output
SELECT * FROM fact_sales ORDER BY net_revenue DESC LIMIT 100;

-- BETTER: filter first, then sort
SELECT * FROM fact_sales
WHERE date_key = 20240615
ORDER BY net_revenue DESC
LIMIT 100;
```

### 10.5 Using DISTINCT Instead of GROUP BY

```sql
-- BAD: DISTINCT on a large table (materialises all distinct combinations)
SELECT DISTINCT customer_key, date_key FROM fact_sales;

-- BETTER: if you need aggregations, use GROUP BY from the start
SELECT customer_key, date_key, SUM(net_revenue)
FROM fact_sales
GROUP BY customer_key, date_key;

-- If you truly need distinct values, GROUP BY is equivalent but gives the optimiser
-- more flexibility in choosing an execution strategy.
```

### 10.6 Repeated CTE Evaluation

```sql
-- In most engines, CTEs are NOT materialised — they are inlined and re-evaluated
-- each time they are referenced.

-- BAD: expensive CTE referenced multiple times
WITH expensive AS (
  SELECT customer_key, SUM(net_revenue) AS total
  FROM fact_sales
  GROUP BY customer_key
)
SELECT * FROM expensive WHERE total > 1000
UNION ALL
SELECT * FROM expensive WHERE total <= 1000;
-- The CTE is computed TWICE.

-- GOOD: materialise explicitly
CREATE TEMP TABLE temp_clv AS
SELECT customer_key, SUM(net_revenue) AS total
FROM fact_sales
GROUP BY customer_key;

SELECT * FROM temp_clv WHERE total > 1000
UNION ALL
SELECT * FROM temp_clv WHERE total <= 1000;
```

---

## 11. Platform-Specific Optimisation

### 11.1 BigQuery

```sql
-- 1. Use clustering to speed up filtered queries
-- Clustering sorts data within partitions by specified columns.
-- Effect: only blocks containing the filtered value are scanned.

-- 2. Prefer approximate aggregations for large cardinality
SELECT APPROX_COUNT_DISTINCT(user_id) FROM events;

-- 3. Avoid cross-region queries (data transfer fees)
-- Ensure tables and queries are in the same region.

-- 4. Use table expiration for temporary tables
CREATE TABLE `analytics.temp_results`
OPTIONS (expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR))
AS SELECT ...;
```

### 11.2 Snowflake

```sql
-- 1. Right-size warehouses: start with XS, increase only if queries spill
-- Check spilling in Query Profile:
-- bytes_spilled_to_local_storage > 0 → try MEDIUM
-- bytes_spilled_to_remote_storage > 0 → try LARGE or XL

-- 2. Use query tags for cost attribution
ALTER SESSION SET QUERY_TAG = 'team=marketing;pipeline=daily_report';

-- 3. Use search optimisation for point lookups on large tables
ALTER TABLE fact_sales ADD SEARCH OPTIMIZATION ON EQUALITY(customer_key);
-- Enables sub-second point lookups on a 10B-row table.

-- 4. Use Snowflake query acceleration service (QAS) for burst workloads
ALTER WAREHOUSE bi_wh SET
  ENABLE_QUERY_ACCELERATION = TRUE
  QUERY_ACCELERATION_MAX_SCALE_FACTOR = 8;
```

### 11.3 Redshift

```sql
-- 1. Choose distribution key to co-locate join partners
-- fact_sales DISTKEY(customer_key) + dim_customer DISTSTYLE ALL
-- → Join on customer_key happens locally on each node (no network shuffle)

-- 2. Use compound sort keys for prefix-filtered queries
CREATE TABLE fact_sales (...) COMPOUND SORTKEY(date_key, customer_key);

-- 3. Run VACUUM and ANALYZE regularly
VACUUM SORT ONLY fact_sales;
ANALYZE fact_sales;

-- 4. Use COPY command for bulk loading (much faster than INSERT)
COPY fact_sales
FROM 's3://my-bucket/data/sales/'
IAM_ROLE 'arn:aws:iam::123456789:role/redshift-load'
FORMAT AS PARQUET;
```

---

## 12. Troubleshooting

### Query runs slowly but scans few bytes

**Cause**: bottleneck is in compute, not I/O. Common reasons:
- Complex window functions on large result sets (spilling to disk).
- Many small joins (nested loop chosen by mistake).
- High concurrency causing queue wait.

**Diagnosis**:
- Snowflake: check `bytes_spilled_to_local_storage` in Query Profile.
- BigQuery: check `total_slot_ms` — high slot-ms with low bytes = compute-bound.
- Redshift: check `stl_query` for high `elapsed` with low `bytes_scanned`.

**Fix**: increase warehouse/cluster size, simplify window functions, materialise
intermediate results.

### Query scans much more data than expected

**Cause**: partition pruning or clustering not effective.

**Diagnosis**:
- Snowflake: `partitions_scanned` / `partitions_total` ratio.
- BigQuery: `total_bytes_processed` in INFORMATION_SCHEMA.
- Redshift: `rows_pre_filter` vs `rows` in `stl_scan`.

**Fix**: add partition filter, improve cluster keys, rewrite functions on filter columns.

### Query returns wrong results (aggregation too high)

**Cause**: fan trap — joining two fact tables through a shared dimension causes row
multiplication.

**Diagnosis**: check row count at each join stage.
```sql
-- Step-by-step row count debugging
SELECT COUNT(*) FROM fact_sales;                       -- 100M
SELECT COUNT(*) FROM fact_sales f JOIN dim_customer c
  ON f.customer_key = c.customer_key;                   -- should be ~100M, not 500M
```

**Fix**: pre-aggregate each fact table before joining (see Section 7.2).

---

## 13. Frequently Asked Questions

**Q: Should I always use EXPLAIN ANALYZE?**

Use `EXPLAIN` (without ANALYZE) for estimated plans when you want to check the plan
without executing the query (e.g., before running a query that might take hours). Use
`EXPLAIN ANALYZE` when you need actual execution times and row counts, and the query is
fast enough to run.

**Q: How do I force a specific join algorithm?**

In PostgreSQL: `SET enable_hashjoin = off;` (not recommended for production). In most
cloud DWs, you cannot directly control the join algorithm — the optimiser decides based on
statistics. Improve statistics, rewrite the query, or materialise intermediate results
instead.

**Q: When should I use a materialised view vs a temp table vs a CTE?**

- **Materialised view**: persistent, auto-refreshed, shared across users. Use for
  frequently computed aggregations.
- **Temp table**: session-scoped, materialised once. Use for intermediate results
  referenced multiple times in a session.
- **CTE**: not materialised (in most engines). Use for readability, not for performance.

**Q: How much does partition pruning actually save?**

For a 365-day partitioned table, a query on one day scans 1/365th of the data — a 365x
reduction. For BigQuery on-demand pricing at $6.25/TB, scanning 10 TB without pruning
costs $62.50. With pruning on one day: ~$0.17.

**Q: What is the biggest performance mistake in DW queries?**

`SELECT *` on a columnar database. It reads every column and eliminates all columnar
benefits. Always select only the columns you need.

---

## 14. Exercises

### Exercise 1: Execution Plan Analysis

Given this PostgreSQL EXPLAIN output, identify the performance bottleneck and propose a fix:

```
Nested Loop  (cost=0.00..999999.00 rows=50000000 width=32) (actual time=0.1..450000.0 rows=48000000)
  ->  Seq Scan on fact_sales  (cost=0.00..50000.00 rows=10000000 width=16) (actual time=0.01..5000.0 rows=10000000)
  ->  Index Scan on dim_customer  (cost=0.00..0.50 rows=1 width=16) (actual time=0.01..0.03 rows=5 loops=10000000)
        Index Cond: (customer_key = fact_sales.customer_key)
```

### Exercise 2: Join Optimisation

Rewrite this query to avoid the fan trap:

```sql
SELECT
  c.segment,
  SUM(s.net_revenue)    AS total_sales,
  SUM(r.refund_amount)  AS total_refunds,
  COUNT(DISTINCT t.ticket_id) AS support_tickets
FROM dim_customer c
  JOIN fact_sales           s ON c.customer_key = s.customer_key
  JOIN fact_returns          r ON c.customer_key = r.customer_key
  JOIN fact_support_tickets  t ON c.customer_key = t.customer_key
GROUP BY c.segment;
```

### Exercise 3: Cost Estimation

A BigQuery table has 5 TB of data, partitioned by date (365 partitions, ~14 GB each),
clustered by customer_id. Estimate the bytes scanned and approximate cost for:

1. `SELECT SUM(revenue) FROM sales WHERE date = '2024-06-15'`
2. `SELECT * FROM sales WHERE date = '2024-06-15' AND customer_id = 'C00042'`
3. `SELECT customer_id, SUM(revenue) FROM sales GROUP BY customer_id`
4. `SELECT COUNT(*) FROM sales`

### Exercise 4: Materialised View Design

You have a BI dashboard that runs these queries every 5 minutes against a 500M-row fact
table:
1. Total revenue by day for the last 30 days.
2. Revenue by product category for the last 7 days.
3. Top 10 customers by revenue for the last 30 days.

Design materialised views (or dynamic tables) to serve these queries. Specify the
aggregation level, refresh strategy, and indexes.

### Exercise 5: Anti-Pattern Correction

Identify and fix all optimisation anti-patterns in this query:

```sql
SELECT *
FROM fact_sales f
JOIN dim_customer c ON CAST(f.customer_key AS VARCHAR) = c.customer_key_str
JOIN dim_date d ON f.date_key = d.date_key
WHERE EXTRACT(YEAR FROM d.full_date) = 2024
  AND c.country = 'US'
ORDER BY f.net_revenue DESC;
```
