# SQL for Analytics — Advanced Queries, Window Functions, and Data Analysis

## Table of Contents

1. [Analytical SQL Foundations](#1-analytical-sql-foundations)
2. [Window Functions](#2-window-functions)
3. [Common Table Expressions (CTEs)](#3-common-table-expressions-ctes)
4. [Advanced Aggregation](#4-advanced-aggregation)
5. [Time Series Analysis in SQL](#5-time-series-analysis-in-sql)
6. [Modern SQL Features](#6-modern-sql-features)
7. [Performance Optimization](#7-performance-optimization)
8. [Analytics Engines](#8-analytics-engines)
9. [SQL Security](#9-sql-security)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. Analytical SQL Foundations

### OLTP vs OLAP Query Patterns

The fundamental distinction between operational and analytical workloads drives every architectural decision in data engineering.

**OLTP (Online Transaction Processing)** queries are characterized by:
- Point lookups on primary keys (`SELECT * FROM orders WHERE id = 12345`)
- Small row counts per query (typically 1-100 rows)
- High concurrency (thousands of simultaneous users)
- Short transaction lifetimes (milliseconds)
- Write-heavy workloads with INSERT/UPDATE/DELETE dominance
- Normalized schemas (3NF or higher) to minimize write anomalies

**OLAP (Online Analytical Processing)** queries are characterized by:
- Full table scans or large range scans
- Aggregation over millions/billions of rows
- Low concurrency (tens of analysts, not thousands of users)
- Long-running queries (seconds to minutes)
- Read-heavy workloads — append-only or batch-loaded data
- Denormalized or star/snowflake schemas to minimize JOINs

```sql
-- OLTP pattern: point lookup, small result set
SELECT order_id, status, total_amount
FROM orders
WHERE customer_id = 42 AND status = 'pending';

-- OLAP pattern: full scan, aggregation, large data volumes
SELECT
    date_trunc('month', order_date) AS month,
    product_category,
    COUNT(*) AS order_count,
    SUM(total_amount) AS revenue,
    AVG(total_amount) AS avg_order_value
FROM orders
JOIN order_items USING (order_id)
JOIN products USING (product_id)
WHERE order_date >= '2024-01-01'
GROUP BY 1, 2
ORDER BY 1, 3 DESC;
```

### Columnar vs Row Storage Implications

**Row-oriented storage** (PostgreSQL default, MySQL, Oracle) stores each row contiguously on disk. Reading a full row is one sequential I/O operation. This benefits OLTP where queries typically fetch all columns for a small number of rows.

**Columnar storage** (DuckDB, ClickHouse, Parquet files, Redshift) stores each column contiguously. Benefits for analytics:

1. **Projection pushdown** — reading only 3 of 50 columns means reading 6% of the data
2. **Compression** — same-type values compress dramatically (dictionary encoding, run-length encoding, delta encoding)
3. **Vectorized execution** — SIMD operations on column vectors
4. **Late materialization** — filter on compressed columns before assembling full rows

```sql
-- In a columnar engine, this query only reads 2 columns from disk
-- regardless of how many columns the table has
SELECT product_category, SUM(revenue)
FROM sales
GROUP BY product_category;
```

DuckDB demonstrates this effectively — queries on a 100-column Parquet file that only touch 3 columns run at nearly the same speed as a 3-column file.

### Query Execution Plans

Every SQL query passes through these stages:

1. **Parsing** — lexical analysis, AST construction
2. **Semantic analysis** — name resolution, type checking
3. **Logical optimization** — predicate pushdown, projection pruning, join reordering
4. **Physical planning** — choosing operators (hash join vs merge join vs nested loop)
5. **Execution** — iterator model (Volcano) or vectorized batch execution

```sql
-- PostgreSQL: view the execution plan
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT c.name, COUNT(o.id), SUM(o.total)
FROM customers c
JOIN orders o ON o.customer_id = c.id
WHERE o.created_at >= '2024-01-01'
GROUP BY c.name
ORDER BY SUM(o.total) DESC
LIMIT 10;
```

Key plan nodes to understand:

| Node | Meaning |
|------|---------|
| Seq Scan | Full table scan — no index used |
| Index Scan | B-tree traversal + heap fetch |
| Index Only Scan | Answered entirely from the index (covering index) |
| Bitmap Index Scan | Build bitmap of matching pages, then fetch |
| Hash Join | Build hash table on smaller relation, probe with larger |
| Merge Join | Both inputs sorted, merge-intersect |
| Nested Loop | For each row in outer, scan inner (good for small outer) |
| Sort | Explicit sort (check if index could eliminate this) |
| HashAggregate | GROUP BY via hash table |
| GroupAggregate | GROUP BY on pre-sorted input |

### Cost-Based Optimization

The query planner estimates cost using statistics about data distribution:

- **n_distinct** — number of distinct values in a column
- **null_frac** — fraction of NULL values
- **most_common_vals / most_common_freqs** — top values and their frequencies
- **histogram_bounds** — equal-depth histogram for range selectivity

```sql
-- View PostgreSQL statistics for a table
SELECT
    attname,
    n_distinct,
    null_frac,
    most_common_vals,
    most_common_freqs
FROM pg_stats
WHERE tablename = 'orders'
ORDER BY attname;

-- Force statistics refresh after bulk loads
ANALYZE orders;

-- Increase statistics target for columns with high cardinality
ALTER TABLE orders ALTER COLUMN customer_id SET STATISTICS 1000;
```

The optimizer uses these statistics to estimate selectivity. A predicate `WHERE status = 'shipped'` on a column where 'shipped' appears in most_common_vals with frequency 0.4 estimates 40% of rows will match. This drives the decision between sequential scan (if 40% of rows match, index is pointless) and index scan (if 0.1% match, index is essential).

---

## 2. Window Functions

Window functions compute values across a set of rows related to the current row without collapsing the result set. They are the single most important analytical SQL feature.

### The OVER Clause

Every window function requires an `OVER()` clause that defines the window:

```sql
-- Empty OVER() = entire result set is the window
SELECT
    employee_id,
    salary,
    AVG(salary) OVER() AS company_avg,
    salary - AVG(salary) OVER() AS diff_from_avg
FROM employees;
```

### PARTITION BY

Divides rows into groups (partitions). The window function resets for each partition:

```sql
SELECT
    department,
    employee_id,
    salary,
    AVG(salary) OVER(PARTITION BY department) AS dept_avg,
    salary - AVG(salary) OVER(PARTITION BY department) AS diff_from_dept_avg,
    salary::numeric / SUM(salary) OVER(PARTITION BY department) AS pct_of_dept_total
FROM employees;
```

### ORDER BY Within Windows

Defines the logical ordering of rows within each partition. Critical for ranking and running calculations:

```sql
SELECT
    department,
    employee_id,
    hire_date,
    salary,
    SUM(salary) OVER(
        PARTITION BY department
        ORDER BY hire_date
    ) AS running_dept_salary_total
FROM employees;
```

### Frame Specification

The frame defines which rows relative to the current row are included in the calculation.

**Syntax:** `{ROWS | RANGE | GROUPS} BETWEEN <start> AND <end>`

Frame boundaries:
- `UNBOUNDED PRECEDING` — first row of the partition
- `n PRECEDING` — n rows/values before current
- `CURRENT ROW` — the current row
- `n FOLLOWING` — n rows/values after current
- `UNBOUNDED FOLLOWING` — last row of the partition

```sql
-- Default frame when ORDER BY is specified:
-- RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW

-- Explicit 7-day moving average
SELECT
    date,
    revenue,
    AVG(revenue) OVER(
        ORDER BY date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS moving_avg_7d
FROM daily_revenue;

-- Centered moving average (smoothing)
SELECT
    date,
    revenue,
    AVG(revenue) OVER(
        ORDER BY date
        ROWS BETWEEN 3 PRECEDING AND 3 FOLLOWING
    ) AS centered_avg_7d
FROM daily_revenue;

-- RANGE vs ROWS: RANGE considers logical value proximity
-- This includes all rows within 7 days of the current row's date
SELECT
    date,
    revenue,
    SUM(revenue) OVER(
        ORDER BY date
        RANGE BETWEEN INTERVAL '7 days' PRECEDING AND CURRENT ROW
    ) AS rolling_7d_revenue
FROM daily_revenue;

-- GROUPS: operates on groups of peer rows (same ORDER BY value)
SELECT
    date,
    category,
    revenue,
    SUM(revenue) OVER(
        ORDER BY date
        GROUPS BETWEEN 1 PRECEDING AND 1 FOLLOWING
    ) AS neighboring_groups_sum
FROM daily_revenue;
```

### Ranking Functions

```sql
SELECT
    department,
    employee_id,
    salary,
    -- Unique sequential numbers, no gaps, arbitrary tiebreak
    ROW_NUMBER() OVER(PARTITION BY department ORDER BY salary DESC) AS row_num,
    -- Same rank for ties, gaps after ties (1,2,2,4)
    RANK() OVER(PARTITION BY department ORDER BY salary DESC) AS rank,
    -- Same rank for ties, no gaps (1,2,2,3)
    DENSE_RANK() OVER(PARTITION BY department ORDER BY salary DESC) AS dense_rank,
    -- Divide into N roughly equal buckets
    NTILE(4) OVER(PARTITION BY department ORDER BY salary DESC) AS quartile
FROM employees;
```

**Practical use — top-N per group:**

```sql
-- Top 3 earners per department
WITH ranked AS (
    SELECT
        department,
        employee_id,
        salary,
        ROW_NUMBER() OVER(PARTITION BY department ORDER BY salary DESC) AS rn
    FROM employees
)
SELECT * FROM ranked WHERE rn <= 3;
```

### Navigation Functions

```sql
SELECT
    date,
    revenue,
    -- Previous row's value
    LAG(revenue, 1) OVER(ORDER BY date) AS prev_day_revenue,
    -- Next row's value
    LEAD(revenue, 1) OVER(ORDER BY date) AS next_day_revenue,
    -- Day-over-day change
    revenue - LAG(revenue, 1) OVER(ORDER BY date) AS dod_change,
    -- Percentage change
    (revenue - LAG(revenue, 1) OVER(ORDER BY date))::numeric
        / NULLIF(LAG(revenue, 1) OVER(ORDER BY date), 0) * 100 AS dod_pct_change,
    -- First value in the partition
    FIRST_VALUE(revenue) OVER(ORDER BY date) AS first_day_revenue,
    -- Last value (need explicit frame to see the whole partition)
    LAST_VALUE(revenue) OVER(
        ORDER BY date
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS last_day_revenue,
    -- Nth value
    NTH_VALUE(revenue, 3) OVER(ORDER BY date) AS third_day_revenue
FROM daily_revenue;
```

### Combining Multiple Windows

Use the `WINDOW` clause (PostgreSQL, DuckDB) to avoid repeating window definitions:

```sql
SELECT
    date,
    product_category,
    revenue,
    SUM(revenue) OVER w AS running_total,
    AVG(revenue) OVER w AS running_avg,
    ROW_NUMBER() OVER w AS day_number
FROM daily_revenue
WINDOW w AS (PARTITION BY product_category ORDER BY date);
```

---

## 3. Common Table Expressions (CTEs)

### Non-Recursive CTEs for Readability

CTEs structure complex queries into named, logical steps:

```sql
-- Revenue analysis pipeline
WITH daily_metrics AS (
    SELECT
        date_trunc('day', created_at) AS day,
        COUNT(*) AS orders,
        SUM(total) AS revenue,
        COUNT(DISTINCT customer_id) AS unique_customers
    FROM orders
    WHERE created_at >= '2024-01-01'
    GROUP BY 1
),
weekly_aggregates AS (
    SELECT
        date_trunc('week', day) AS week,
        SUM(orders) AS weekly_orders,
        SUM(revenue) AS weekly_revenue,
        AVG(unique_customers) AS avg_daily_customers
    FROM daily_metrics
    GROUP BY 1
),
with_growth AS (
    SELECT
        *,
        LAG(weekly_revenue) OVER(ORDER BY week) AS prev_week_revenue,
        (weekly_revenue - LAG(weekly_revenue) OVER(ORDER BY week))::numeric
            / NULLIF(LAG(weekly_revenue) OVER(ORDER BY week), 0) * 100 AS wow_growth_pct
    FROM weekly_aggregates
)
SELECT * FROM with_growth ORDER BY week;
```

### Recursive CTEs

Recursive CTEs enable hierarchical traversal and series generation:

```sql
-- Organizational hierarchy traversal
WITH RECURSIVE org_tree AS (
    -- Base case: top-level managers
    SELECT
        id,
        name,
        manager_id,
        1 AS depth,
        ARRAY[name] AS path
    FROM employees
    WHERE manager_id IS NULL

    UNION ALL

    -- Recursive case: join children to existing tree
    SELECT
        e.id,
        e.name,
        e.manager_id,
        t.depth + 1,
        t.path || e.name
    FROM employees e
    JOIN org_tree t ON e.manager_id = t.id
    WHERE t.depth < 10  -- safety limit to prevent infinite recursion
)
SELECT
    id,
    name,
    depth,
    array_to_string(path, ' -> ') AS reporting_chain
FROM org_tree
ORDER BY path;
```

**Series generation with recursive CTE:**

```sql
-- Generate a date series (useful in engines without generate_series)
WITH RECURSIVE date_range AS (
    SELECT DATE '2024-01-01' AS dt
    UNION ALL
    SELECT dt + INTERVAL '1 day'
    FROM date_range
    WHERE dt < DATE '2024-12-31'
)
SELECT dt FROM date_range;
```

**Graph traversal — shortest path:**

```sql
-- Find all reachable nodes from a starting node
WITH RECURSIVE reachable AS (
    SELECT
        target_node AS node,
        1 AS hops,
        ARRAY[source_node, target_node] AS path
    FROM edges
    WHERE source_node = 'A'

    UNION

    SELECT
        e.target_node,
        r.hops + 1,
        r.path || e.target_node
    FROM reachable r
    JOIN edges e ON e.source_node = r.node
    WHERE e.target_node <> ALL(r.path)  -- cycle prevention
      AND r.hops < 20
)
SELECT DISTINCT ON (node) node, hops, path
FROM reachable
ORDER BY node, hops;
```

### Materialized vs Inline CTEs

PostgreSQL 12+ treats CTEs as optimization fences only when explicitly requested:

```sql
-- PostgreSQL: allow optimizer to inline/flatten this CTE
WITH recent_orders AS (
    SELECT * FROM orders WHERE created_at >= CURRENT_DATE - 30
)
SELECT * FROM recent_orders WHERE total > 100;
-- Optimizer can push the total > 100 predicate down

-- Force materialization (useful when CTE is referenced multiple times)
WITH recent_orders AS MATERIALIZED (
    SELECT * FROM orders WHERE created_at >= CURRENT_DATE - 30
)
SELECT COUNT(*) FROM recent_orders
UNION ALL
SELECT SUM(total) FROM recent_orders;
```

DuckDB always optimizes CTEs — they are never optimization barriers.

### Performance Implications

- **Single-reference CTEs** — generally safe to inline; optimizer handles it
- **Multi-reference CTEs** — materialization can prevent re-computation
- **Recursive CTEs** — always materialized; optimize the recursion depth and use proper termination conditions
- **CTE chains** — each step adds clarity but watch for unnecessary intermediate materializations in engines that default to materialization (pre-PG12)

---

## 4. Advanced Aggregation

### GROUPING SETS, CUBE, and ROLLUP

These produce multiple levels of aggregation in a single pass:

```sql
-- GROUPING SETS: explicit combinations
SELECT
    COALESCE(region, '(All Regions)') AS region,
    COALESCE(product_category, '(All Categories)') AS category,
    SUM(revenue) AS total_revenue,
    COUNT(*) AS order_count,
    GROUPING(region, product_category) AS grouping_level
FROM sales
GROUP BY GROUPING SETS (
    (region, product_category),  -- detail
    (region),                     -- by region
    (product_category),           -- by category
    ()                            -- grand total
)
ORDER BY GROUPING(region, product_category), region, product_category;
```

```sql
-- ROLLUP: hierarchical aggregation (totals at each level)
-- Produces: (year, quarter, month), (year, quarter), (year), ()
SELECT
    EXTRACT(year FROM order_date) AS year,
    EXTRACT(quarter FROM order_date) AS quarter,
    EXTRACT(month FROM order_date) AS month,
    SUM(revenue) AS revenue,
    COUNT(DISTINCT customer_id) AS unique_customers
FROM orders
GROUP BY ROLLUP(
    EXTRACT(year FROM order_date),
    EXTRACT(quarter FROM order_date),
    EXTRACT(month FROM order_date)
);
```

```sql
-- CUBE: all possible combinations (2^n groupings)
-- For 3 dimensions: 8 grouping combinations
SELECT
    region,
    product_category,
    sales_channel,
    SUM(revenue) AS revenue,
    AVG(margin) AS avg_margin
FROM sales
GROUP BY CUBE(region, product_category, sales_channel);
```

### FILTER Clause

PostgreSQL and DuckDB support `FILTER` for conditional aggregation — cleaner than CASE:

```sql
SELECT
    date_trunc('month', created_at) AS month,
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_orders,
    COUNT(*) FILTER (WHERE status = 'refunded') AS refunded_orders,
    SUM(total) FILTER (WHERE status = 'completed') AS completed_revenue,
    AVG(total) FILTER (WHERE total > 100) AS avg_high_value_order
FROM orders
GROUP BY 1
ORDER BY 1;
```

### Conditional Aggregation with CASE

For engines without FILTER, or for more complex logic:

```sql
SELECT
    product_id,
    COUNT(CASE WHEN rating >= 4 THEN 1 END) AS positive_reviews,
    COUNT(CASE WHEN rating <= 2 THEN 1 END) AS negative_reviews,
    COUNT(CASE WHEN rating = 3 THEN 1 END) AS neutral_reviews,
    ROUND(
        COUNT(CASE WHEN rating >= 4 THEN 1 END)::numeric / NULLIF(COUNT(*), 0) * 100,
        1
    ) AS positive_pct
FROM reviews
GROUP BY product_id;
```

### Percentile Functions

```sql
-- Continuous percentile (interpolates between values)
SELECT
    department,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salary) AS median_salary,
    PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY salary) AS p25_salary,
    PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY salary) AS p75_salary,
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY salary) AS p90_salary,
    PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY salary) AS p99_salary
FROM employees
GROUP BY department;

-- Discrete percentile (returns an actual value from the set)
SELECT
    PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY response_time_ms) AS median_response_ms
FROM api_requests
WHERE endpoint = '/api/search';
```

### Mode and Statistical Functions

```sql
-- Mode (most frequent value)
SELECT
    product_category,
    MODE() WITHIN GROUP (ORDER BY price_tier) AS most_common_tier
FROM products
GROUP BY product_category;

-- Variance and standard deviation
SELECT
    department,
    AVG(salary) AS mean,
    STDDEV_POP(salary) AS stddev,
    VARIANCE(salary) AS variance,
    -- Coefficient of variation (normalized spread)
    STDDEV_POP(salary) / NULLIF(AVG(salary), 0) AS cv
FROM employees
GROUP BY department;
```

### Approximate Aggregates

For extremely large datasets where exact counts are unnecessary:

```sql
-- DuckDB: approximate count distinct using HyperLogLog
SELECT approx_count_distinct(user_id) AS approx_unique_users
FROM page_views
WHERE event_date = CURRENT_DATE;

-- PostgreSQL: use the hll extension
CREATE EXTENSION IF NOT EXISTS hll;

-- Store HLL sketches for rollup
SELECT
    date_trunc('hour', event_time) AS hour,
    hll_add_agg(hll_hash_text(user_id)) AS user_hll
FROM events
GROUP BY 1;
```

---

## 5. Time Series Analysis in SQL

### Date/Time Foundations

```sql
-- date_trunc: truncate to specified precision
SELECT
    date_trunc('hour', event_time) AS hour,
    date_trunc('day', event_time) AS day,
    date_trunc('week', event_time) AS week_start,
    date_trunc('month', event_time) AS month_start,
    date_trunc('quarter', event_time) AS quarter_start
FROM events
LIMIT 1;

-- Extract components
SELECT
    EXTRACT(dow FROM event_time) AS day_of_week,  -- 0=Sunday
    EXTRACT(hour FROM event_time) AS hour,
    EXTRACT(epoch FROM event_time) AS unix_timestamp
FROM events;
```

### Filling Gaps with generate_series

Real time series data has gaps. Fill them:

```sql
-- Generate continuous date spine and LEFT JOIN actual data
WITH date_spine AS (
    SELECT generate_series(
        '2024-01-01'::date,
        '2024-12-31'::date,
        '1 day'::interval
    )::date AS date
),
daily_revenue AS (
    SELECT
        date_trunc('day', created_at)::date AS date,
        SUM(total) AS revenue,
        COUNT(*) AS orders
    FROM orders
    GROUP BY 1
)
SELECT
    ds.date,
    COALESCE(dr.revenue, 0) AS revenue,
    COALESCE(dr.orders, 0) AS orders
FROM date_spine ds
LEFT JOIN daily_revenue dr ON ds.date = dr.date
ORDER BY ds.date;
```

### Moving Averages

```sql
-- Simple moving average (SMA)
SELECT
    date,
    revenue,
    AVG(revenue) OVER(ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS sma_7,
    AVG(revenue) OVER(ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS sma_30
FROM daily_metrics;

-- Exponential moving average (approximation via recursive CTE)
WITH RECURSIVE ema AS (
    SELECT
        date,
        revenue,
        revenue::numeric AS ema_value,
        ROW_NUMBER() OVER(ORDER BY date) AS rn
    FROM daily_metrics
    WHERE date = (SELECT MIN(date) FROM daily_metrics)

    UNION ALL

    SELECT
        dm.date,
        dm.revenue,
        -- EMA formula: alpha * current + (1-alpha) * previous_ema
        -- alpha = 2/(N+1), for N=7: alpha ≈ 0.25
        0.25 * dm.revenue + 0.75 * e.ema_value,
        e.rn + 1
    FROM daily_metrics dm
    JOIN ema e ON dm.date = (
        SELECT MIN(date) FROM daily_metrics WHERE date > e.date
    )
    WHERE e.rn < 365
)
SELECT date, revenue, ROUND(ema_value, 2) AS ema_7
FROM ema
ORDER BY date;
```

### Year-over-Year and Month-over-Month Comparisons

```sql
-- YoY comparison
SELECT
    date_trunc('month', order_date) AS month,
    SUM(revenue) AS revenue,
    LAG(SUM(revenue), 12) OVER(ORDER BY date_trunc('month', order_date)) AS revenue_ly,
    ROUND(
        (SUM(revenue) - LAG(SUM(revenue), 12) OVER(ORDER BY date_trunc('month', order_date)))::numeric
        / NULLIF(LAG(SUM(revenue), 12) OVER(ORDER BY date_trunc('month', order_date)), 0) * 100,
        1
    ) AS yoy_growth_pct
FROM orders
GROUP BY 1
ORDER BY 1;

-- MoM comparison
WITH monthly AS (
    SELECT
        date_trunc('month', order_date) AS month,
        SUM(revenue) AS revenue
    FROM orders
    GROUP BY 1
)
SELECT
    month,
    revenue,
    LAG(revenue) OVER(ORDER BY month) AS prev_month,
    ROUND(
        (revenue - LAG(revenue) OVER(ORDER BY month))::numeric
        / NULLIF(LAG(revenue) OVER(ORDER BY month), 0) * 100, 1
    ) AS mom_growth_pct
FROM monthly;
```

### Cohort Analysis

```sql
-- User retention by signup cohort
WITH user_cohort AS (
    SELECT
        user_id,
        date_trunc('month', MIN(event_date)) AS cohort_month
    FROM user_events
    GROUP BY user_id
),
user_activity AS (
    SELECT
        ue.user_id,
        uc.cohort_month,
        date_trunc('month', ue.event_date) AS activity_month,
        -- Months since signup
        EXTRACT(YEAR FROM AGE(date_trunc('month', ue.event_date), uc.cohort_month)) * 12
        + EXTRACT(MONTH FROM AGE(date_trunc('month', ue.event_date), uc.cohort_month)) AS months_since_signup
    FROM user_events ue
    JOIN user_cohort uc USING (user_id)
)
SELECT
    cohort_month,
    months_since_signup,
    COUNT(DISTINCT user_id) AS active_users,
    FIRST_VALUE(COUNT(DISTINCT user_id)) OVER(
        PARTITION BY cohort_month ORDER BY months_since_signup
    ) AS cohort_size,
    ROUND(
        COUNT(DISTINCT user_id)::numeric
        / FIRST_VALUE(COUNT(DISTINCT user_id)) OVER(
            PARTITION BY cohort_month ORDER BY months_since_signup
        ) * 100, 1
    ) AS retention_pct
FROM user_activity
GROUP BY cohort_month, months_since_signup
ORDER BY cohort_month, months_since_signup;
```

### Funnel Analysis

```sql
-- Conversion funnel
WITH funnel_steps AS (
    SELECT
        session_id,
        MAX(CASE WHEN event = 'page_view' THEN 1 ELSE 0 END) AS step_1_view,
        MAX(CASE WHEN event = 'add_to_cart' THEN 1 ELSE 0 END) AS step_2_cart,
        MAX(CASE WHEN event = 'checkout_start' THEN 1 ELSE 0 END) AS step_3_checkout,
        MAX(CASE WHEN event = 'purchase' THEN 1 ELSE 0 END) AS step_4_purchase
    FROM events
    WHERE event_date >= CURRENT_DATE - 30
    GROUP BY session_id
)
SELECT
    'page_view' AS step,
    COUNT(*) FILTER (WHERE step_1_view = 1) AS users,
    100.0 AS pct_of_start
UNION ALL
SELECT
    'add_to_cart',
    COUNT(*) FILTER (WHERE step_2_cart = 1),
    ROUND(COUNT(*) FILTER (WHERE step_2_cart = 1)::numeric
        / NULLIF(COUNT(*) FILTER (WHERE step_1_view = 1), 0) * 100, 1)
FROM funnel_steps
UNION ALL
SELECT
    'checkout_start',
    COUNT(*) FILTER (WHERE step_3_checkout = 1),
    ROUND(COUNT(*) FILTER (WHERE step_3_checkout = 1)::numeric
        / NULLIF(COUNT(*) FILTER (WHERE step_1_view = 1), 0) * 100, 1)
FROM funnel_steps
UNION ALL
SELECT
    'purchase',
    COUNT(*) FILTER (WHERE step_4_purchase = 1),
    ROUND(COUNT(*) FILTER (WHERE step_4_purchase = 1)::numeric
        / NULLIF(COUNT(*) FILTER (WHERE step_1_view = 1), 0) * 100, 1)
FROM funnel_steps;
```

### Session Detection (Gaps-and-Islands)

Identify sessions from a stream of events with inactivity gaps:

```sql
-- Detect sessions: new session starts after 30 minutes of inactivity
WITH events_with_gap AS (
    SELECT
        user_id,
        event_time,
        event_type,
        EXTRACT(EPOCH FROM (
            event_time - LAG(event_time) OVER(PARTITION BY user_id ORDER BY event_time)
        )) AS seconds_since_last
    FROM user_events
),
session_starts AS (
    SELECT
        *,
        CASE
            WHEN seconds_since_last IS NULL THEN 1  -- first event
            WHEN seconds_since_last > 1800 THEN 1   -- 30 min gap
            ELSE 0
        END AS is_new_session
    FROM events_with_gap
),
sessionized AS (
    SELECT
        *,
        SUM(is_new_session) OVER(
            PARTITION BY user_id ORDER BY event_time
        ) AS session_id
    FROM session_starts
)
SELECT
    user_id,
    session_id,
    MIN(event_time) AS session_start,
    MAX(event_time) AS session_end,
    COUNT(*) AS events_in_session,
    EXTRACT(EPOCH FROM MAX(event_time) - MIN(event_time)) AS session_duration_sec
FROM sessionized
GROUP BY user_id, session_id;
```

### Event Sequence Analysis

```sql
-- Find users who performed action A then action B within 1 hour
WITH sequenced AS (
    SELECT
        user_id,
        event_type,
        event_time,
        LEAD(event_type) OVER(PARTITION BY user_id ORDER BY event_time) AS next_event,
        LEAD(event_time) OVER(PARTITION BY user_id ORDER BY event_time) AS next_event_time
    FROM user_events
    WHERE event_type IN ('signup', 'first_purchase')
)
SELECT
    user_id,
    event_time AS signup_time,
    next_event_time AS purchase_time,
    next_event_time - event_time AS time_to_convert
FROM sequenced
WHERE event_type = 'signup'
  AND next_event = 'first_purchase'
  AND next_event_time - event_time <= INTERVAL '1 hour';
```

---

## 6. Modern SQL Features

### LATERAL Joins

LATERAL allows a subquery to reference columns from preceding tables — essentially a correlated subquery in the FROM clause:

```sql
-- Top 3 orders per customer (more efficient than window + filter)
SELECT c.id, c.name, top_orders.*
FROM customers c
CROSS JOIN LATERAL (
    SELECT order_id, total, created_at
    FROM orders
    WHERE customer_id = c.id
    ORDER BY total DESC
    LIMIT 3
) AS top_orders;

-- Time-series: latest reading per sensor
SELECT s.sensor_id, s.location, latest.*
FROM sensors s
CROSS JOIN LATERAL (
    SELECT reading_value, reading_time
    FROM sensor_readings
    WHERE sensor_id = s.sensor_id
    ORDER BY reading_time DESC
    LIMIT 1
) AS latest;
```

### ARRAY and JSON Operations

```sql
-- PostgreSQL: ARRAY operations
SELECT
    user_id,
    ARRAY_AGG(DISTINCT tag ORDER BY tag) AS all_tags,
    ARRAY_LENGTH(ARRAY_AGG(DISTINCT tag), 1) AS tag_count
FROM user_tags
GROUP BY user_id;

-- JSONB querying
SELECT
    id,
    metadata->>'source' AS source,
    metadata->'metrics'->>'conversion_rate' AS conversion_rate,
    jsonb_array_length(metadata->'tags') AS num_tags
FROM campaigns
WHERE metadata @> '{"status": "active"}'
  AND (metadata->'metrics'->>'conversion_rate')::numeric > 0.05;

-- JSONB aggregation
SELECT
    jsonb_build_object(
        'total_users', COUNT(*),
        'avg_revenue', ROUND(AVG(lifetime_revenue)::numeric, 2),
        'segments', jsonb_agg(DISTINCT segment)
    ) AS summary
FROM users;
```

### UNNEST — Expanding Arrays

```sql
-- Expand array column into rows
SELECT
    order_id,
    unnest(product_ids) AS product_id
FROM orders;

-- DuckDB: unnest with position
SELECT
    order_id,
    unnest(product_ids) AS product_id,
    generate_subscripts(product_ids, 1) AS position
FROM orders;

-- Useful for tag/category explosion in analytics
WITH tag_expanded AS (
    SELECT
        article_id,
        unnest(tags) AS tag
    FROM articles
)
SELECT tag, COUNT(*) AS article_count
FROM tag_expanded
GROUP BY tag
ORDER BY article_count DESC;
```

### PIVOT and UNPIVOT

```sql
-- DuckDB native PIVOT
PIVOT sales
ON product_category
USING SUM(revenue)
GROUP BY region;

-- PostgreSQL: crosstab via tablefunc extension
CREATE EXTENSION IF NOT EXISTS tablefunc;

SELECT * FROM crosstab(
    'SELECT region, product_category, SUM(revenue)::numeric
     FROM sales
     GROUP BY region, product_category
     ORDER BY 1, 2',
    'SELECT DISTINCT product_category FROM sales ORDER BY 1'
) AS ct(region text, electronics numeric, clothing numeric, food numeric);

-- Manual pivot with conditional aggregation (works everywhere)
SELECT
    region,
    SUM(revenue) FILTER (WHERE product_category = 'electronics') AS electronics,
    SUM(revenue) FILTER (WHERE product_category = 'clothing') AS clothing,
    SUM(revenue) FILTER (WHERE product_category = 'food') AS food
FROM sales
GROUP BY region;

-- UNPIVOT (normalize wide to long)
-- DuckDB native UNPIVOT
UNPIVOT monthly_metrics
ON jan, feb, mar, apr, may, jun
INTO NAME month VALUE revenue;

-- PostgreSQL: unpivot via VALUES + LATERAL
SELECT m.product_id, v.month_name, v.revenue
FROM monthly_metrics m
CROSS JOIN LATERAL (
    VALUES
        ('jan', m.jan),
        ('feb', m.feb),
        ('mar', m.mar)
) AS v(month_name, revenue);
```

### QUALIFY Clause

DuckDB and some engines support QUALIFY for filtering window function results directly:

```sql
-- DuckDB: top 3 per category without a CTE
SELECT
    product_category,
    product_name,
    revenue,
    ROW_NUMBER() OVER(PARTITION BY product_category ORDER BY revenue DESC) AS rn
FROM products
QUALIFY rn <= 3;

-- Equivalent PostgreSQL (requires CTE or subquery)
SELECT * FROM (
    SELECT
        product_category,
        product_name,
        revenue,
        ROW_NUMBER() OVER(PARTITION BY product_category ORDER BY revenue DESC) AS rn
    FROM products
) sub
WHERE rn <= 3;
```

### MERGE / UPSERT

```sql
-- PostgreSQL: INSERT ... ON CONFLICT (upsert)
INSERT INTO daily_aggregates (date, metric_name, value)
VALUES ('2024-06-15', 'revenue', 50000)
ON CONFLICT (date, metric_name)
DO UPDATE SET
    value = EXCLUDED.value,
    updated_at = NOW();

-- Standard SQL MERGE (DuckDB, SQL Server, Oracle)
MERGE INTO target_table t
USING source_table s ON t.id = s.id
WHEN MATCHED AND s.updated_at > t.updated_at THEN
    UPDATE SET value = s.value, updated_at = s.updated_at
WHEN NOT MATCHED THEN
    INSERT (id, value, updated_at)
    VALUES (s.id, s.value, s.updated_at)
WHEN MATCHED AND s.is_deleted THEN
    DELETE;
```

### Table-Valued Functions

```sql
-- PostgreSQL: function returning a set of rows
CREATE OR REPLACE FUNCTION get_revenue_breakdown(
    start_date date,
    end_date date
)
RETURNS TABLE(
    month date,
    category text,
    revenue numeric,
    pct_of_total numeric
) AS $$
    WITH totals AS (
        SELECT date_trunc('month', order_date)::date AS m, SUM(amount) AS total
        FROM orders
        WHERE order_date BETWEEN start_date AND end_date
        GROUP BY 1
    )
    SELECT
        date_trunc('month', o.order_date)::date,
        p.category,
        SUM(o.amount),
        ROUND(SUM(o.amount) / t.total * 100, 2)
    FROM orders o
    JOIN products p USING (product_id)
    JOIN totals t ON date_trunc('month', o.order_date)::date = t.m
    WHERE o.order_date BETWEEN start_date AND end_date
    GROUP BY 1, 2, t.total;
$$ LANGUAGE SQL STABLE;

-- Usage
SELECT * FROM get_revenue_breakdown('2024-01-01', '2024-06-30');
```

---

## 7. Performance Optimization

### EXPLAIN ANALYZE Interpretation

```sql
EXPLAIN (ANALYZE, BUFFERS, TIMING, FORMAT TEXT)
SELECT c.name, SUM(o.total)
FROM customers c
JOIN orders o ON o.customer_id = c.id
WHERE o.created_at >= '2024-01-01'
GROUP BY c.name
ORDER BY SUM(o.total) DESC
LIMIT 20;
```

Key metrics to examine:

- **actual time** — startup time..total time in milliseconds (per loop iteration)
- **rows** — actual rows vs planned rows (large discrepancy = stale statistics)
- **loops** — number of times the node executed
- **Buffers: shared hit/read** — cache hit ratio (high read = cold cache or missing index)
- **Sort Method: external merge** — sort spilling to disk (increase `work_mem`)

Red flags in execution plans:
- Seq Scan on large table with low selectivity filter → missing index
- Nested Loop with large outer set → consider Hash Join
- planned rows: 1, actual rows: 100000 → statistics are stale, run ANALYZE
- Sort Method: external merge Disk → `work_mem` too small for this query

### Index Types and When to Use Them

**B-tree (default)** — equality and range queries:
```sql
-- Effective for: =, <, >, <=, >=, BETWEEN, IN, IS NULL
CREATE INDEX idx_orders_date ON orders (created_at);

-- Composite index: left-prefix queries benefit
CREATE INDEX idx_orders_customer_date ON orders (customer_id, created_at);
-- Benefits: WHERE customer_id = X
-- Benefits: WHERE customer_id = X AND created_at >= Y
-- Does NOT benefit: WHERE created_at >= Y (missing left prefix)
```

**Hash index** — equality only, smaller than B-tree:
```sql
CREATE INDEX idx_sessions_token ON sessions USING hash (session_token);
-- Only benefits: WHERE session_token = 'abc123'
```

**GIN (Generalized Inverted Index)** — contains queries on composite types:
```sql
-- Full-text search
CREATE INDEX idx_articles_fts ON articles USING gin (to_tsvector('english', body));

-- JSONB containment
CREATE INDEX idx_events_metadata ON events USING gin (metadata jsonb_path_ops);

-- Array contains
CREATE INDEX idx_posts_tags ON posts USING gin (tags);
```

**GiST (Generalized Search Tree)** — geometric, range, full-text proximity:
```sql
-- Range type queries (overlaps, contains)
CREATE INDEX idx_bookings_period ON bookings USING gist (
    tstzrange(check_in, check_out)
);

-- PostGIS geometry
CREATE INDEX idx_locations_geom ON locations USING gist (geom);
```

**BRIN (Block Range Index)** — physically ordered data, tiny index size:
```sql
-- Ideal for append-only tables where column correlates with physical order
-- 1000x smaller than B-tree for billion-row time-series tables
CREATE INDEX idx_events_time_brin ON events USING brin (event_time)
    WITH (pages_per_range = 32);
```

### Materialized Views

```sql
-- Pre-computed analytical summary
CREATE MATERIALIZED VIEW mv_daily_revenue AS
SELECT
    date_trunc('day', created_at)::date AS date,
    product_category,
    COUNT(*) AS orders,
    SUM(total) AS revenue,
    AVG(total) AS avg_order_value,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total) AS median_order_value
FROM orders
JOIN products USING (product_id)
GROUP BY 1, 2;

-- Create index on the materialized view
CREATE INDEX idx_mv_daily_date ON mv_daily_revenue (date);

-- Refresh (blocks reads during refresh)
REFRESH MATERIALIZED VIEW mv_daily_revenue;

-- Concurrent refresh (does not block reads, requires unique index)
CREATE UNIQUE INDEX idx_mv_daily_unique ON mv_daily_revenue (date, product_category);
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_revenue;
```

### Partitioning Strategies

```sql
-- Range partitioning by date (most common for time series)
CREATE TABLE events (
    id bigint GENERATED ALWAYS AS IDENTITY,
    event_time timestamptz NOT NULL,
    event_type text NOT NULL,
    user_id bigint,
    payload jsonb
) PARTITION BY RANGE (event_time);

-- Create monthly partitions
CREATE TABLE events_2024_01 PARTITION OF events
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
CREATE TABLE events_2024_02 PARTITION OF events
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- List partitioning (by category/region)
CREATE TABLE sales (
    id bigint,
    region text NOT NULL,
    amount numeric
) PARTITION BY LIST (region);

CREATE TABLE sales_na PARTITION OF sales FOR VALUES IN ('US', 'CA', 'MX');
CREATE TABLE sales_eu PARTITION OF sales FOR VALUES IN ('DE', 'FR', 'GB', 'IT');

-- Hash partitioning (even distribution for parallel processing)
CREATE TABLE sessions (
    session_id uuid NOT NULL,
    user_id bigint,
    data jsonb
) PARTITION BY HASH (session_id);

CREATE TABLE sessions_0 PARTITION OF sessions FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE sessions_1 PARTITION OF sessions FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE sessions_2 PARTITION OF sessions FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE sessions_3 PARTITION OF sessions FOR VALUES WITH (MODULUS 4, REMAINDER 3);
```

### Join Order Optimization

```sql
-- PostgreSQL: control join order when optimizer gets it wrong
SET join_collapse_limit = 1;  -- forces join order as written

-- Better: use explicit join hints in the query
-- Write the smallest/most selective table first in joins
SELECT /*+ Leading(small_table large_table) */ ...

-- Check that join selectivity estimates are accurate:
EXPLAIN SELECT ...
-- If "rows" estimate is wildly off, update statistics:
ANALYZE large_table;
```

### Subquery vs JOIN Performance

```sql
-- Anti-join patterns: find rows with NO match

-- EXISTS (usually best — can short-circuit)
SELECT c.*
FROM customers c
WHERE NOT EXISTS (
    SELECT 1 FROM orders o WHERE o.customer_id = c.id AND o.created_at >= '2024-01-01'
);

-- LEFT JOIN + NULL check (equivalent, sometimes optimizer prefers this)
SELECT c.*
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.id AND o.created_at >= '2024-01-01'
WHERE o.id IS NULL;

-- NOT IN (avoid — NULL semantics are dangerous and performance is often worse)
-- If subquery returns ANY NULL, the entire NOT IN returns no rows
SELECT c.*
FROM customers c
WHERE c.id NOT IN (SELECT customer_id FROM orders WHERE created_at >= '2024-01-01');
```

---

## 8. Analytics Engines

### PostgreSQL Analytical Capabilities

PostgreSQL is a strong analytical database for datasets up to ~500GB with proper tuning:

- Full window function support since version 8.4
- Parallel query execution (parallel seq scan, parallel hash join, parallel aggregation)
- Partitioning (declarative since PG 10)
- JIT compilation for complex expressions
- Extensions: `pg_stat_statements` for query analysis, `timescaledb` for time series, `citus` for distributed analytics

```sql
-- Tune for analytical workloads
SET max_parallel_workers_per_gather = 4;
SET parallel_tuple_cost = 0.001;
SET work_mem = '256MB';          -- per-sort memory
SET effective_cache_size = '24GB'; -- hint to planner about OS cache
SET random_page_cost = 1.1;      -- SSD: sequential ≈ random
```

### DuckDB — Embedded OLAP

DuckDB is an in-process columnar database designed for analytical queries. Key strengths:

- Zero-copy direct query of Parquet, CSV, JSON files
- Vectorized execution engine
- Automatic parallelism across cores
- No server — embeds into Python, R, Node.js, CLI

```sql
-- Query Parquet files directly (no load step)
SELECT
    date_trunc('month', order_date) AS month,
    product_category,
    SUM(revenue) AS revenue
FROM read_parquet('s3://data-lake/orders/year=2024/**/*.parquet')
GROUP BY 1, 2
ORDER BY 1, 2;

-- Query CSV with auto-detection
SELECT * FROM read_csv_auto('data/customers.csv')
WHERE signup_date >= '2024-01-01';

-- Query JSON
SELECT
    json_extract_string(data, '$.user.email') AS email,
    json_extract(data, '$.events') AS events
FROM read_json_auto('events/*.jsonl');

-- Combine multiple sources
SELECT
    c.name,
    SUM(o.total) AS lifetime_value
FROM read_parquet('orders.parquet') o
JOIN read_csv_auto('customers.csv') c ON o.customer_id = c.id
GROUP BY c.name
ORDER BY 2 DESC
LIMIT 20;

-- Export results
COPY (
    SELECT * FROM analytics_result
) TO 'output.parquet' (FORMAT PARQUET, COMPRESSION ZSTD);
```

### ClickHouse

Designed for real-time analytics on billions of rows:

- **MergeTree engine family** — LSM-tree-inspired, automatic background merging
- **Materialized views** — incrementally maintained on INSERT
- **Approximate functions** — `uniq`, `quantileTDigest`, `topK`
- **Vectorized execution** with SIMD

```sql
-- ClickHouse: create an analytics table
CREATE TABLE events (
    event_date Date,
    event_time DateTime,
    user_id UInt64,
    event_type LowCardinality(String),
    properties String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_type, user_id, event_time)
TTL event_date + INTERVAL 2 YEAR;

-- Materialized view for real-time aggregation
CREATE MATERIALIZED VIEW daily_active_users
ENGINE = SummingMergeTree()
ORDER BY (event_date)
AS SELECT
    event_date,
    uniqState(user_id) AS users_state
FROM events
GROUP BY event_date;

-- Query the materialized view
SELECT event_date, uniqMerge(users_state) AS dau
FROM daily_active_users
GROUP BY event_date
ORDER BY event_date;
```

### BigQuery

Google's serverless data warehouse:

- **Slot-based execution** — computing units allocated per query
- **Partitioning** — by ingestion time, DATE/TIMESTAMP column, or integer range
- **Clustering** — secondary sort within partitions (up to 4 columns)
- **Nested/repeated fields** — denormalized STRUCT and ARRAY types

```sql
-- BigQuery: partitioned and clustered table
CREATE TABLE `project.dataset.events`
PARTITION BY DATE(event_time)
CLUSTER BY user_id, event_type
AS SELECT * FROM source_events;

-- Query with partition filter (reduces cost)
SELECT
    event_type,
    COUNT(*) AS event_count
FROM `project.dataset.events`
WHERE DATE(event_time) BETWEEN '2024-01-01' AND '2024-01-31'
GROUP BY event_type;

-- Unnest repeated fields
SELECT
    user_id,
    item.product_id,
    item.quantity,
    item.price
FROM `project.dataset.orders`,
UNNEST(line_items) AS item;
```

### Snowflake

Multi-cluster, separated storage and compute:

- **Virtual warehouses** — independent compute clusters, scale up/out independently
- **Time travel** — query historical data up to 90 days back
- **Zero-copy cloning** — instant database/table clones for testing
- **Semi-structured data** — native VARIANT type for JSON/Avro/Parquet

```sql
-- Snowflake: time travel
SELECT * FROM orders AT(TIMESTAMP => '2024-06-01 12:00:00'::timestamp);

-- Query differences between two points in time
SELECT *
FROM orders BEFORE(STATEMENT => '<query-id>')
EXCEPT
SELECT *
FROM orders AT(STATEMENT => '<query-id>');

-- Semi-structured data
SELECT
    raw_data:user:email::string AS email,
    raw_data:events[0]:type::string AS first_event_type
FROM raw_events
WHERE raw_data:user:country::string = 'US';
```

### Trino/Presto — Federated Queries

Query across heterogeneous data sources with a single SQL interface:

```sql
-- Query across PostgreSQL, S3 Parquet, and Kafka simultaneously
SELECT
    pg.customers.name,
    s3.orders.total,
    kafka.events.event_type
FROM postgresql.public.customers AS pg_customers
JOIN hive.warehouse.orders AS s3_orders
    ON pg_customers.id = s3_orders.customer_id
JOIN kafka.events.user_events AS kafka_events
    ON pg_customers.id = kafka_events.user_id
WHERE s3_orders.order_date >= DATE '2024-01-01';
```

---

## 9. SQL Security

### SQL Injection Prevention

SQL injection remains in the OWASP Top 10. The attack surface exists wherever user input is concatenated into SQL strings.

**Parameterized queries (the primary defense):**

```python
# Python + psycopg2 — SAFE: parameterized
cursor.execute(
    "SELECT * FROM users WHERE email = %s AND status = %s",
    (user_email, 'active')
)

# UNSAFE: string formatting
cursor.execute(f"SELECT * FROM users WHERE email = '{user_email}'")
# If user_email = "'; DROP TABLE users; --" → catastrophic
```

```javascript
// Node.js + pg — SAFE: parameterized
const result = await pool.query(
  'SELECT * FROM users WHERE id = $1 AND org_id = $2',
  [userId, orgId]
);

// UNSAFE: template literal interpolation
const result = await pool.query(
  `SELECT * FROM users WHERE id = ${userId}`
);
```

**Prepared statements:**

```sql
-- PostgreSQL: server-side prepared statement
PREPARE get_user_orders(bigint, date) AS
    SELECT order_id, total, status
    FROM orders
    WHERE customer_id = $1 AND created_at >= $2;

EXECUTE get_user_orders(42, '2024-01-01');
```

**ORM safety considerations:**

ORMs generally parameterize by default, but raw query escape hatches are dangerous:

```python
# SQLAlchemy — SAFE: ORM methods
session.query(User).filter(User.email == user_input).all()

# SQLAlchemy — UNSAFE: raw text without binding
session.execute(text(f"SELECT * FROM users WHERE email = '{user_input}'"))

# SQLAlchemy — SAFE: raw text WITH binding
session.execute(
    text("SELECT * FROM users WHERE email = :email"),
    {"email": user_input}
)
```

**Dynamic identifiers (table/column names cannot be parameterized):**

```python
# Whitelist approach — the ONLY safe way for dynamic identifiers
ALLOWED_COLUMNS = {'name', 'email', 'created_at', 'status'}
ALLOWED_TABLES = {'users', 'orders', 'products'}

def build_query(table: str, column: str, value: str):
    if table not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table: {table}")
    if column not in ALLOWED_COLUMNS:
        raise ValueError(f"Invalid column: {column}")

    # Table/column names from whitelist are safe to interpolate
    # Value is still parameterized
    return f"SELECT * FROM {table} WHERE {column} = %s", (value,)
```

### Privilege Escalation via SQL

```sql
-- Principle of least privilege: application accounts should NEVER be superuser
CREATE ROLE app_reader WITH LOGIN PASSWORD '...' NOSUPERUSER NOCREATEDB;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_reader;

-- Separate roles for different access patterns
CREATE ROLE app_writer WITH LOGIN PASSWORD '...';
GRANT SELECT, INSERT, UPDATE ON orders TO app_writer;
-- No DELETE permission — soft delete via status column instead

-- Revoke dangerous permissions
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON pg_proc FROM PUBLIC;

-- Monitor for privilege escalation attempts
SELECT
    usename,
    query,
    query_start
FROM pg_stat_activity
WHERE query ILIKE '%ALTER ROLE%'
   OR query ILIKE '%GRANT%'
   OR query ILIKE '%CREATE EXTENSION%';
```

### Row-Level Security (RLS)

PostgreSQL RLS enforces data isolation at the database level — cannot be bypassed by application bugs:

```sql
-- Enable RLS on tenant-shared table
ALTER TABLE customer_data ENABLE ROW LEVEL SECURITY;

-- Policy: users can only see their own tenant's data
CREATE POLICY tenant_isolation ON customer_data
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id')::bigint);

-- Force RLS even for table owner
ALTER TABLE customer_data FORCE ROW LEVEL SECURITY;

-- Application sets the tenant context per connection
SET app.current_tenant_id = '42';
-- Now all queries on customer_data are automatically filtered

-- Verify isolation: this returns ONLY tenant 42's rows
SELECT * FROM customer_data;  -- RLS filter applied transparently
```

### Column-Level Encryption in Queries

```sql
-- PostgreSQL: pgcrypto for column-level encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encrypt sensitive data at rest
INSERT INTO users (email, ssn_encrypted)
VALUES (
    'user@example.com',
    pgp_sym_encrypt('123-45-6789', current_setting('app.encryption_key'))
);

-- Decrypt only when explicitly needed (and by authorized roles)
SELECT
    email,
    pgp_sym_decrypt(ssn_encrypted::bytea, current_setting('app.encryption_key')) AS ssn
FROM users
WHERE id = 42;

-- Never log the decrypted value — query logging must exclude sensitive columns
-- Configure pg_stat_statements to track queries without parameters:
-- pg_stat_statements.track_utility = off
```

### Audit Logging of Sensitive Queries

```sql
-- Create audit log table
CREATE TABLE query_audit_log (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    executed_at timestamptz DEFAULT NOW(),
    username text DEFAULT current_user,
    client_addr inet DEFAULT inet_client_addr(),
    query_text text,
    affected_tables text[],
    row_count bigint
);

-- PostgreSQL: use pgAudit extension for comprehensive audit
-- In postgresql.conf:
-- shared_preload_libraries = 'pgaudit'
-- pgaudit.log = 'write, ddl'
-- pgaudit.log_relation = on

-- Trigger-based audit for specific tables
CREATE OR REPLACE FUNCTION audit_sensitive_access()
RETURNS trigger AS $$
BEGIN
    INSERT INTO query_audit_log (query_text, affected_tables, row_count)
    VALUES (current_query(), ARRAY[TG_TABLE_NAME], 1);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_pii_access
AFTER SELECT ON users
FOR EACH STATEMENT
EXECUTE FUNCTION audit_sensitive_access();
```

### Dynamic SQL Risks

```sql
-- DANGEROUS: dynamic SQL in stored procedures
CREATE OR REPLACE FUNCTION search_users(search_field text, search_value text)
RETURNS SETOF users AS $$
BEGIN
    -- THIS IS VULNERABLE — never do this
    RETURN QUERY EXECUTE
        'SELECT * FROM users WHERE ' || search_field || ' = ''' || search_value || '''';
END;
$$ LANGUAGE plpgsql;

-- SAFE version: whitelist fields, parameterize values
CREATE OR REPLACE FUNCTION search_users_safe(search_field text, search_value text)
RETURNS SETOF users AS $$
BEGIN
    -- Whitelist allowed fields
    IF search_field NOT IN ('name', 'email', 'status') THEN
        RAISE EXCEPTION 'Invalid search field: %', search_field;
    END IF;

    -- Use format() with %I for identifiers and $1 for values
    RETURN QUERY EXECUTE
        format('SELECT * FROM users WHERE %I = $1', search_field)
        USING search_value;
END;
$$ LANGUAGE plpgsql;
```

---

## 10. Lab Exercises

### Lab 1: Complete Analytics Dashboard in Pure SQL

Build a cohort-based analytics dashboard using only SQL:

```sql
-- Setup: create sample data
CREATE TABLE lab_users (
    user_id bigint PRIMARY KEY,
    signup_date date NOT NULL,
    plan_type text NOT NULL,
    acquisition_channel text NOT NULL
);

CREATE TABLE lab_events (
    event_id bigint PRIMARY KEY,
    user_id bigint REFERENCES lab_users(user_id),
    event_date date NOT NULL,
    event_type text NOT NULL,
    revenue numeric DEFAULT 0
);

-- Insert sample data
INSERT INTO lab_users (user_id, signup_date, plan_type, acquisition_channel)
SELECT
    id,
    '2024-01-01'::date + (random() * 180)::int,
    (ARRAY['free', 'pro', 'enterprise'])[1 + (random() * 2)::int],
    (ARRAY['organic', 'paid', 'referral', 'social'])[1 + (random() * 3)::int]
FROM generate_series(1, 10000) AS id;

INSERT INTO lab_events (event_id, user_id, event_date, event_type, revenue)
SELECT
    row_number() OVER(),
    (random() * 9999 + 1)::bigint,
    '2024-01-01'::date + (random() * 365)::int,
    (ARRAY['page_view', 'feature_use', 'purchase', 'support_ticket'])[1 + (random() * 3)::int],
    CASE WHEN random() < 0.1 THEN (random() * 100)::numeric(10,2) ELSE 0 END
FROM generate_series(1, 500000);

-- EXERCISE 1: Monthly cohort retention matrix
-- Goal: For each signup month cohort, calculate what percentage
-- returned in months 0, 1, 2, ..., 6
WITH user_cohort AS (
    SELECT
        user_id,
        date_trunc('month', signup_date)::date AS cohort_month
    FROM lab_users
),
monthly_activity AS (
    SELECT DISTINCT
        e.user_id,
        uc.cohort_month,
        date_trunc('month', e.event_date)::date AS activity_month
    FROM lab_events e
    JOIN user_cohort uc USING (user_id)
),
retention AS (
    SELECT
        cohort_month,
        (EXTRACT(YEAR FROM activity_month) - EXTRACT(YEAR FROM cohort_month)) * 12
            + EXTRACT(MONTH FROM activity_month) - EXTRACT(MONTH FROM cohort_month) AS months_after,
        COUNT(DISTINCT user_id) AS active_users
    FROM monthly_activity
    GROUP BY 1, 2
),
cohort_sizes AS (
    SELECT cohort_month, COUNT(*) AS cohort_size
    FROM user_cohort
    GROUP BY 1
)
SELECT
    r.cohort_month,
    cs.cohort_size,
    r.months_after,
    r.active_users,
    ROUND(r.active_users::numeric / cs.cohort_size * 100, 1) AS retention_pct
FROM retention r
JOIN cohort_sizes cs USING (cohort_month)
WHERE r.months_after BETWEEN 0 AND 6
ORDER BY r.cohort_month, r.months_after;

-- EXERCISE 2: Conversion funnel by acquisition channel
-- Goal: page_view → feature_use → purchase, broken by channel
WITH user_first_events AS (
    SELECT
        u.user_id,
        u.acquisition_channel,
        MIN(e.event_date) FILTER (WHERE e.event_type = 'page_view') AS first_view,
        MIN(e.event_date) FILTER (WHERE e.event_type = 'feature_use') AS first_feature,
        MIN(e.event_date) FILTER (WHERE e.event_type = 'purchase') AS first_purchase
    FROM lab_users u
    LEFT JOIN lab_events e ON e.user_id = u.user_id
    GROUP BY u.user_id, u.acquisition_channel
)
SELECT
    acquisition_channel,
    COUNT(*) AS total_users,
    COUNT(first_view) AS viewed,
    COUNT(first_feature) FILTER (WHERE first_feature >= first_view) AS used_feature,
    COUNT(first_purchase) FILTER (WHERE first_purchase >= first_feature) AS purchased,
    ROUND(COUNT(first_view)::numeric / COUNT(*) * 100, 1) AS view_rate,
    ROUND(
        COUNT(first_feature) FILTER (WHERE first_feature >= first_view)::numeric
        / NULLIF(COUNT(first_view), 0) * 100, 1
    ) AS view_to_feature_pct,
    ROUND(
        COUNT(first_purchase) FILTER (WHERE first_purchase >= first_feature)::numeric
        / NULLIF(COUNT(first_feature) FILTER (WHERE first_feature >= first_view), 0) * 100, 1
    ) AS feature_to_purchase_pct
FROM user_first_events
GROUP BY acquisition_channel
ORDER BY purchased DESC;

-- EXERCISE 3: Revenue trends with forecasting baseline
-- Goal: calculate daily revenue, 7-day and 30-day moving averages,
-- and identify days that are >2 standard deviations from the 30-day mean
WITH daily_revenue AS (
    SELECT
        event_date AS date,
        SUM(revenue) AS revenue,
        COUNT(*) FILTER (WHERE revenue > 0) AS transactions
    FROM lab_events
    WHERE event_type = 'purchase'
    GROUP BY event_date
),
with_moving_stats AS (
    SELECT
        date,
        revenue,
        transactions,
        AVG(revenue) OVER(ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS ma_7d,
        AVG(revenue) OVER(ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS ma_30d,
        STDDEV_POP(revenue) OVER(ORDER BY date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS stddev_30d
    FROM daily_revenue
)
SELECT
    date,
    ROUND(revenue, 2) AS revenue,
    ROUND(ma_7d, 2) AS ma_7d,
    ROUND(ma_30d, 2) AS ma_30d,
    CASE
        WHEN revenue > ma_30d + 2 * stddev_30d THEN 'SPIKE'
        WHEN revenue < ma_30d - 2 * stddev_30d THEN 'DROP'
        ELSE 'NORMAL'
    END AS anomaly_flag
FROM with_moving_stats
WHERE stddev_30d > 0
ORDER BY date;
```

### Lab 2: Query Optimization — Before and After

```sql
-- SLOW QUERY: Find top customers with their most recent order
-- This runs a correlated subquery for EVERY customer
EXPLAIN ANALYZE
SELECT
    c.id,
    c.name,
    c.email,
    (SELECT MAX(o.created_at) FROM orders o WHERE o.customer_id = c.id) AS last_order,
    (SELECT SUM(o.total) FROM orders o WHERE o.customer_id = c.id) AS lifetime_value,
    (SELECT COUNT(*) FROM orders o WHERE o.customer_id = c.id) AS order_count
FROM customers c
WHERE EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.id)
ORDER BY lifetime_value DESC
LIMIT 100;

-- OPTIMIZED VERSION: single pass aggregation
EXPLAIN ANALYZE
WITH customer_stats AS (
    SELECT
        customer_id,
        MAX(created_at) AS last_order,
        SUM(total) AS lifetime_value,
        COUNT(*) AS order_count
    FROM orders
    GROUP BY customer_id
)
SELECT
    c.id,
    c.name,
    c.email,
    cs.last_order,
    cs.lifetime_value,
    cs.order_count
FROM customers c
JOIN customer_stats cs ON cs.customer_id = c.id
ORDER BY cs.lifetime_value DESC
LIMIT 100;

-- INDEX STRATEGY for this query:
CREATE INDEX idx_orders_customer_id ON orders (customer_id);
-- If filtering by date range is common:
CREATE INDEX idx_orders_customer_date ON orders (customer_id, created_at DESC);
-- Covering index to avoid heap fetches:
CREATE INDEX idx_orders_customer_covering ON orders (customer_id)
    INCLUDE (created_at, total);

-- EXERCISE: Compare execution plans before/after indexing
-- Document: planning time, execution time, buffers shared hit/read
```

### Lab 3: Row-Level Security for Multi-Tenant Analytics

```sql
-- Scenario: SaaS analytics platform where each tenant sees only their data

-- 1. Create the schema
CREATE TABLE tenants (
    tenant_id bigint PRIMARY KEY,
    name text NOT NULL,
    plan text NOT NULL CHECK (plan IN ('starter', 'growth', 'enterprise'))
);

CREATE TABLE tenant_metrics (
    id bigint GENERATED ALWAYS AS IDENTITY,
    tenant_id bigint NOT NULL REFERENCES tenants(tenant_id),
    metric_date date NOT NULL,
    metric_name text NOT NULL,
    metric_value numeric NOT NULL
);

-- 2. Enable RLS
ALTER TABLE tenant_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_metrics FORCE ROW LEVEL SECURITY;

-- 3. Create tenant isolation policy
CREATE POLICY tenant_read_own_data ON tenant_metrics
    FOR SELECT
    USING (tenant_id = current_setting('app.tenant_id')::bigint);

CREATE POLICY tenant_write_own_data ON tenant_metrics
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.tenant_id')::bigint);

-- 4. Create an admin policy that bypasses RLS for internal analytics
CREATE ROLE analytics_admin;
CREATE POLICY admin_full_access ON tenant_metrics
    FOR ALL
    TO analytics_admin
    USING (true);

-- 5. Application role with RLS enforced
CREATE ROLE app_service WITH LOGIN;
GRANT SELECT, INSERT ON tenant_metrics TO app_service;
GRANT SELECT ON tenants TO app_service;

-- 6. Verify isolation
SET ROLE app_service;
SET app.tenant_id = '1';

-- This only returns tenant 1's data
SELECT * FROM tenant_metrics;

-- This fails silently (no rows inserted, no error)
INSERT INTO tenant_metrics (tenant_id, metric_date, metric_name, metric_value)
VALUES (2, CURRENT_DATE, 'revenue', 5000);
-- The WITH CHECK policy prevents tenant_id != current_setting

-- 7. Cross-tenant analytics (admin only)
SET ROLE analytics_admin;
SELECT
    t.name AS tenant_name,
    t.plan,
    AVG(tm.metric_value) FILTER (WHERE tm.metric_name = 'revenue') AS avg_revenue,
    COUNT(DISTINCT tm.metric_date) AS active_days
FROM tenants t
JOIN tenant_metrics tm USING (tenant_id)
WHERE tm.metric_date >= CURRENT_DATE - 30
GROUP BY t.tenant_id, t.name, t.plan
ORDER BY avg_revenue DESC;

-- EXERCISE: Write a test that verifies:
-- a) Tenant A cannot read Tenant B's data
-- b) Tenant A cannot insert data with Tenant B's tenant_id
-- c) Admin can read all tenants
-- d) Queries with RLS still use indexes efficiently (check EXPLAIN)
```

### Lab 4: SQL-Based Anomaly Detection for Security Events

```sql
-- Scenario: Detect suspicious access patterns from authentication logs

CREATE TABLE auth_events (
    event_id bigint GENERATED ALWAYS AS IDENTITY,
    event_time timestamptz NOT NULL,
    user_id bigint NOT NULL,
    source_ip inet NOT NULL,
    event_type text NOT NULL,  -- 'login_success', 'login_failure', 'password_change', 'mfa_bypass'
    user_agent text,
    geo_country text,
    risk_score numeric DEFAULT 0
);

-- DETECTION 1: Brute force detection
-- Flag IPs with >10 failed logins in 5 minutes
WITH failure_windows AS (
    SELECT
        source_ip,
        event_time,
        COUNT(*) OVER(
            PARTITION BY source_ip
            ORDER BY event_time
            RANGE BETWEEN INTERVAL '5 minutes' PRECEDING AND CURRENT ROW
        ) AS failures_in_window
    FROM auth_events
    WHERE event_type = 'login_failure'
)
SELECT DISTINCT
    source_ip,
    MIN(event_time) AS window_start,
    MAX(event_time) AS window_end,
    MAX(failures_in_window) AS peak_failures
FROM failure_windows
WHERE failures_in_window > 10
GROUP BY source_ip;

-- DETECTION 2: Impossible travel
-- Flag logins from different countries within improbable timeframes
WITH login_pairs AS (
    SELECT
        user_id,
        event_time AS current_login,
        geo_country AS current_country,
        LAG(event_time) OVER(PARTITION BY user_id ORDER BY event_time) AS prev_login,
        LAG(geo_country) OVER(PARTITION BY user_id ORDER BY event_time) AS prev_country
    FROM auth_events
    WHERE event_type = 'login_success'
)
SELECT
    user_id,
    prev_login,
    prev_country,
    current_login,
    current_country,
    EXTRACT(EPOCH FROM current_login - prev_login) / 3600 AS hours_between
FROM login_pairs
WHERE prev_country IS NOT NULL
  AND prev_country <> current_country
  AND EXTRACT(EPOCH FROM current_login - prev_login) < 7200;  -- < 2 hours

-- DETECTION 3: Credential stuffing patterns
-- Multiple distinct users from same IP in short window
WITH ip_user_diversity AS (
    SELECT
        source_ip,
        date_trunc('hour', event_time) AS hour,
        COUNT(DISTINCT user_id) AS distinct_users,
        COUNT(*) AS total_attempts,
        COUNT(*) FILTER (WHERE event_type = 'login_failure') AS failures,
        COUNT(*) FILTER (WHERE event_type = 'login_success') AS successes
    FROM auth_events
    GROUP BY source_ip, date_trunc('hour', event_time)
)
SELECT
    source_ip,
    hour,
    distinct_users,
    total_attempts,
    failures,
    successes,
    ROUND(failures::numeric / NULLIF(total_attempts, 0) * 100, 1) AS failure_rate
FROM ip_user_diversity
WHERE distinct_users > 20  -- many different accounts
  AND failures::numeric / NULLIF(total_attempts, 0) > 0.8  -- high failure rate
ORDER BY distinct_users DESC;

-- DETECTION 4: Anomalous access time patterns (behavioral baseline)
WITH user_baseline AS (
    SELECT
        user_id,
        EXTRACT(hour FROM event_time) AS login_hour,
        COUNT(*) AS login_count
    FROM auth_events
    WHERE event_type = 'login_success'
      AND event_time >= CURRENT_TIMESTAMP - INTERVAL '90 days'
    GROUP BY user_id, EXTRACT(hour FROM event_time)
),
user_normal_hours AS (
    SELECT
        user_id,
        ARRAY_AGG(login_hour ORDER BY login_count DESC) AS preferred_hours,
        -- Top 3 hours represent "normal" behavior
        (ARRAY_AGG(login_hour ORDER BY login_count DESC))[1:3] AS top_3_hours
    FROM user_baseline
    GROUP BY user_id
),
recent_logins AS (
    SELECT
        user_id,
        event_time,
        EXTRACT(hour FROM event_time) AS login_hour,
        source_ip
    FROM auth_events
    WHERE event_type = 'login_success'
      AND event_time >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
)
SELECT
    rl.user_id,
    rl.event_time,
    rl.login_hour,
    rl.source_ip,
    unh.top_3_hours AS normal_hours,
    'OFF_HOURS_LOGIN' AS alert_type
FROM recent_logins rl
JOIN user_normal_hours unh USING (user_id)
WHERE rl.login_hour <> ALL(unh.top_3_hours);

-- DETECTION 5: Aggregate risk scoring
-- Combine signals into a composite risk score per user per day
WITH daily_signals AS (
    SELECT
        user_id,
        date_trunc('day', event_time)::date AS day,
        -- Signal 1: Failed login attempts
        COUNT(*) FILTER (WHERE event_type = 'login_failure') AS failed_logins,
        -- Signal 2: Distinct source IPs
        COUNT(DISTINCT source_ip) AS distinct_ips,
        -- Signal 3: Distinct countries
        COUNT(DISTINCT geo_country) AS distinct_countries,
        -- Signal 4: Password changes
        COUNT(*) FILTER (WHERE event_type = 'password_change') AS password_changes,
        -- Signal 5: MFA bypasses
        COUNT(*) FILTER (WHERE event_type = 'mfa_bypass') AS mfa_bypasses
    FROM auth_events
    GROUP BY user_id, date_trunc('day', event_time)::date
)
SELECT
    user_id,
    day,
    -- Weighted risk score
    (LEAST(failed_logins, 20) * 2        -- cap at 40 points
     + LEAST(distinct_ips, 5) * 5         -- cap at 25 points
     + distinct_countries * 15            -- 15 points per country
     + password_changes * 10             -- 10 points each
     + mfa_bypasses * 30                 -- 30 points each — high severity
    ) AS risk_score,
    failed_logins,
    distinct_ips,
    distinct_countries,
    password_changes,
    mfa_bypasses
FROM daily_signals
WHERE (
    failed_logins > 5
    OR distinct_ips > 3
    OR distinct_countries > 1
    OR mfa_bypasses > 0
)
ORDER BY risk_score DESC;

-- EXERCISE:
-- a) Implement a materialized view that refreshes every 5 minutes with the latest risk scores
-- b) Add an alert threshold system: risk_score > 50 → medium, > 80 → high, > 120 → critical
-- c) Track the false positive rate by marking resolved alerts and calculating precision
-- d) Build a query that identifies "slow and low" attacks: attackers who stay below
--    individual thresholds but accumulate risk over 7 days
```

---

## References and Further Reading

- PostgreSQL documentation: https://www.postgresql.org/docs/current/
- DuckDB documentation: https://duckdb.org/docs/
- "SQL Performance Explained" — Markus Winand (use-the-index-luke.com)
- "T-SQL Window Functions" — Itzik Ben-Gan
- OWASP SQL Injection Prevention Cheat Sheet
- ClickHouse documentation: https://clickhouse.com/docs
- Modern SQL features tracking: https://modern-sql.com/
