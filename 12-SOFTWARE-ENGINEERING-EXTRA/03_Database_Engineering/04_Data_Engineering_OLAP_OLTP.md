# Module 3.4: Data Engineering — OLTP vs OLAP, Warehouses, Lakes

> **Module 03.4** · **Last updated:** 2026-05-22

## Guiding ideas
1. **OLTP (transactional) vs OLAP (analytical): different storage layouts.**
2. **Snowflake/BigQuery cloud DW; Databricks lakehouse.**
3. **Apache Iceberg/Delta Lake: table format on object storage.**
4. **dbt: SQL-based transformation tool.**

---

## 1. OLTP vs OLAP: Workload Polarities

Two different physics. Same SQL syntax, different storage and execution.

### 1.1 OLTP (Online Transaction Processing)

```
Characteristics:
  Workload:     High concurrency (thousands of TPS)
  Queries:      Point reads/writes, short transactions
  Latency:      < 10ms p99
  Schema:       3NF normalized
  Storage:      Row-store (heap or clustered B+ tree)
  Concurrency:  Full ACID, MVCC
  Typical query: SELECT * FROM orders WHERE id = 4711
                 → 1 page read, microseconds

Engines: PostgreSQL, MySQL/InnoDB, Oracle, SQL Server, CockroachDB, Spanner
```

### 1.2 OLAP (Online Analytical Processing)

```
Characteristics:
  Workload:     Low concurrency (tens of concurrent queries)
  Queries:      Large scans, aggregations, joins across millions/billions of rows
  Latency:      Seconds to minutes acceptable
  Schema:       Denormalized (star/snowflake)
  Storage:      Column-store
  Concurrency:  ACID often relaxed; eventual consistency on ingest tolerated
  Typical query: SELECT region, SUM(revenue) FROM sales
                 WHERE year = 2025 GROUP BY region
                 → scans millions of rows, reads only 2 columns

Engines: Snowflake, BigQuery, Redshift, ClickHouse, Druid, DuckDB
```

### 1.3 Why Columns Win for Analytics

```
Row-store (200 columns, query touches 3):

  Page 1: [row1: col1..col200] [row2: col1..col200]
  Page 2: [row3: col1..col200] [row4: col1..col200]

  Read: 100% of bytes from disk
  Use:  1.5% of bytes (3/200 columns)
  Waste: 98.5%

Column-store:

  File col_1:   [row1, row2, row3, row4, ...]
  File col_15:  [row1, row2, row3, row4, ...]
  File col_99:  [row1, row2, row3, row4, ...]

  Read: only 3 column files
  Use:  100% of bytes read
  Waste: 0%
```

**Additional column-store advantages:**
- **Compression:** Same-type adjacent values compress 5-20x (RLE, dictionary, delta).
- **SIMD:** Tight loops over `int32[]` arrays enable CPU vectorization.
- **Late materialization:** Filter columns first, reconstruct full rows only for
  qualifying rows.
- **Predicate pushdown:** Push WHERE predicates into the storage layer; skip entire
  blocks via min/max statistics.

### 1.4 HTAP (Hybrid Transactional/Analytical Processing)

Some systems aim to serve both OLTP and OLAP:

| System | Approach |
|---|---|
| TiDB + TiFlash | Row-store (TiKV) for OLTP + columnar replica (TiFlash) for OLAP |
| SingleStore (MemSQL) | Row-store + columnar in same engine |
| AlloyDB (Google) | PostgreSQL-compatible, columnar engine for analytics |
| CockroachDB | Row-store with limited analytical capabilities |
| Oracle Database In-Memory | Dual-format: row on disk, column in memory |

**Trade-off:** True HTAP avoids maintaining separate OLTP and OLAP systems (no ETL),
but the workload isolation problem is hard — an analytical scan should not slow
down transactional queries.

---

## 2. Dimensional Modeling

### 2.1 Star Schema (Kimball Methodology)

```
                    ┌──────────────────┐
                    │   dim_date       │
                    │  date_key (PK)   │
                    │  full_date       │
                    │  year, quarter   │
                    │  month, day      │
                    │  day_of_week     │
                    │  is_holiday      │
                    └────────┬─────────┘
                             │
   ┌──────────────┐   ┌──────┴──────────────────┐   ┌──────────────┐
   │ dim_product  │   │     fact_sales           │   │ dim_store    │
   │ product_key  │───│ date_key (FK)            │───│ store_key    │
   │ sku          │   │ product_key (FK)         │   │ store_name   │
   │ product_name │   │ store_key (FK)           │   │ city         │
   │ category     │   │ customer_key (FK)        │   │ state        │
   │ brand        │   │ ──────────────────────── │   │ region       │
   │ department   │   │ quantity      (measure)  │   │ manager      │
   └──────────────┘   │ unit_price    (measure)  │   └──────────────┘
                      │ discount_pct  (measure)  │
                      │ revenue       (measure)  │   ┌──────────────┐
                      │ cost          (measure)  │   │ dim_customer │
                      │                          │───│ customer_key │
                      └──────────────────────────┘   │ name         │
                                                      │ segment      │
                                                      │ tier         │
                                                      └──────────────┘
```

**Fact table principles:**
- Contains numeric measures (additive, semi-additive, non-additive).
- Foreign keys to dimension tables.
- Append-mostly (new facts are inserted, rarely updated).
- Grain: one row per transaction/event.
- Typically the largest table (millions to billions of rows).

**Dimension table principles:**
- Descriptive attributes (text, categories, hierarchies).
- Denormalized (repeat data rather than normalize).
- Smaller than facts (thousands to millions of rows).
- Surrogate keys (auto-increment integers, not natural keys).

**Why star schema?**
- Joins are always 1-hop (fact → dimension). No chained joins.
- Query patterns are predictable — optimizer can plan efficiently.
- BI tools (Tableau, Power BI, Looker) are designed for star schemas.
- Compression is excellent on dimension FKs in fact tables (low cardinality integers).

### 2.2 Snowflake Schema

Dimensions normalized further:

```
fact_sales → dim_product → dim_category → dim_department

Instead of star's:
fact_sales → dim_product (category and department embedded)
```

**Trade-offs:**
- Saves storage (no repeated category/department text in dim_product).
- Costs additional joins for every query.
- Rarely worth it on cloud warehouses where storage is cheap and join cost is real.

### 2.3 Inmon CIF (Corporate Information Factory)

Top-down approach (contrast with Kimball's bottom-up):

```
┌───────────────────────────────────────────────────┐
│  Source Systems → ETL → Enterprise DW (3NF)        │
│                         │                          │
│                         ├── Data Mart: Sales (Star)│
│                         ├── Data Mart: HR (Star)   │
│                         └── Data Mart: Finance     │
└───────────────────────────────────────────────────┘
```

- Enterprise DW is normalized (3NF) — single source of truth.
- Departmental data marts are star schemas derived from the DW.
- More upfront modeling work, slower delivery, more consistent semantics.
- Better for large enterprises with many interdependent domains.

### 2.4 Data Vault

Hybrid approach designed for agile data warehousing:

```
Hub:      Business keys (customer_id, product_id)
Link:     Relationships between hubs (order links customer to product)
Satellite: Descriptive attributes with load timestamps

Advantages:
  - Auditable: full history preserved, every change tracked
  - Agile: add new sources without restructuring
  - Parallel loading: hubs, links, satellites load independently
  
Disadvantages:
  - Complex queries (many joins between hub/link/satellite)
  - End users typically access via data marts on top
```

---

## 3. Materialized Views

### 3.1 Concept

A materialized view is a pre-computed query result stored as a physical table:

```sql
-- PostgreSQL:
CREATE MATERIALIZED VIEW monthly_revenue AS
SELECT
    date_trunc('month', order_date) AS month,
    region,
    SUM(revenue) AS total_revenue,
    COUNT(*) AS order_count
FROM fact_sales
JOIN dim_store USING (store_key)
GROUP BY 1, 2;

-- Query the materialized view (instant):
SELECT * FROM monthly_revenue
WHERE month = '2026-04-01' AND region = 'EMEA';
-- Instead of scanning the full fact table every time

-- Refresh (recalculate):
REFRESH MATERIALIZED VIEW monthly_revenue;
REFRESH MATERIALIZED VIEW CONCURRENTLY monthly_revenue;
-- CONCURRENTLY allows reads during refresh (requires unique index)
```

### 3.2 Refresh Strategies

| Strategy | Mechanism | Latency | Cost |
|---|---|---|---|
| Full refresh | Drop + rebuild entire MV | High | Expensive but simple |
| Incremental refresh | Apply only changes since last refresh | Low | Complex, engine-dependent |
| On-commit refresh | Update MV on every transaction commit | Zero | Very expensive for writes |
| Scheduled refresh | Cron job (e.g., every hour) | Bounded staleness | Predictable load |

**Cloud warehouse materialized views:**

```sql
-- Snowflake (auto-refresh):
CREATE MATERIALIZED VIEW mv_daily_sales AS
SELECT date, region, SUM(revenue) AS total
FROM sales
GROUP BY date, region;
-- Snowflake automatically refreshes when base data changes
-- Serverless compute handles refresh (additional cost)

-- BigQuery:
CREATE MATERIALIZED VIEW project.dataset.mv_sales AS
SELECT date, region, SUM(revenue) AS total
FROM project.dataset.sales
GROUP BY date, region;
-- Auto-refreshed within minutes of base table changes
-- Queries automatically rewrite to use MV when possible
```

### 3.3 Automatic Query Rewriting

Advanced systems automatically rewrite queries to use materialized views:

```sql
-- User writes:
SELECT region, SUM(revenue)
FROM fact_sales
WHERE order_date BETWEEN '2026-04-01' AND '2026-04-30'
GROUP BY region;

-- Optimizer rewrites to:
SELECT region, total_revenue
FROM monthly_revenue
WHERE month = '2026-04-01';
-- Same result, scans precomputed MV instead of full fact table
```

Supported by: Oracle (query rewrite), BigQuery (automatic), Snowflake (automatic),
Redshift (automatic with `AUTO REFRESH`).

---

## 4. ETL vs ELT

### 4.1 Traditional ETL

```
┌──────────┐    ┌──────────────────┐    ┌──────────────┐
│  Sources  │───►│  ETL Server      │───►│  Data        │
│           │    │  (Informatica,   │    │  Warehouse   │
│  ERP      │    │   SSIS, Talend)  │    │              │
│  CRM      │    │                  │    │  (cleaned,   │
│  Files    │    │  Extract →       │    │   transformed │
│           │    │  Transform →     │    │   data)      │
│           │    │  Load            │    │              │
└──────────┘    └──────────────────┘    └──────────────┘

Problems:
  - Transform runs on ETL server (limited compute)
  - Raw data discarded after transform
  - Schema changes require full pipeline rebuild
  - Slow iteration: change transform → re-run entire pipeline
```

### 4.2 Modern ELT

```
┌──────────┐   ┌───────────┐   ┌──────────────────────────────┐
│  Sources  │──►│  Ingestion │──►│  Cloud Warehouse             │
│           │   │  (Fivetran,│   │                              │
│  SaaS APIs│   │   Airbyte, │   │  Raw Zone ──► Staging ──►   │
│  DBs      │   │   Stitch)  │   │                  dbt         │
│  Events   │   │            │   │              Transform       │
│           │   │  Extract + │   │                  │           │
│           │   │  Load      │   │              ┌───▼────┐     │
│           │   │  (raw)     │   │              │ Marts  │     │
│           │   └───────────┘   │              └────────┘     │
│           │                    └──────────────────────────────┘

Advantages:
  - Transform runs in the warehouse (massive compute, SQL-based)
  - Raw data preserved (re-run transforms on raw data)
  - Fast iteration: change dbt model → re-run SQL
  - Storage is cheap on cloud warehouses
```

### 4.3 Comparison

| Aspect | ETL | ELT |
|---|---|---|
| Transform location | External ETL server | Inside the warehouse |
| Raw data retention | Often discarded | Always preserved |
| Transform language | Proprietary (Informatica, SSIS) | SQL (dbt) |
| Iteration speed | Slow (full pipeline re-run) | Fast (re-run SQL on loaded data) |
| Compute scaling | Limited by ETL server | Cloud warehouse scales on demand |
| Cost model | ETL license + server | Warehouse compute |
| Modern tools | Legacy (being replaced) | Fivetran + dbt + Snowflake/BigQuery |

---

## 5. dbt (data build tool)

### 5.1 What dbt Does

dbt is a SQL-first transformation framework for the "T" in ELT:

```
┌────────────────────────────────────────────────────────┐
│                    dbt Project                          │
│                                                         │
│  models/                                                │
│  ├── staging/          ← Clean raw data (1:1 with source) │
│  │   ├── stg_orders.sql                                 │
│  │   └── stg_customers.sql                              │
│  ├── intermediate/     ← Business logic transformations │
│  │   └── int_orders_enriched.sql                        │
│  └── marts/            ← Final business entities        │
│      ├── fct_orders.sql                                 │
│      └── dim_customers.sql                              │
│                                                         │
│  tests/                ← Data quality assertions        │
│  │   └── assert_order_total_positive.sql                │
│  │                                                      │
│  seeds/                ← Static reference data (CSV)    │
│  │   └── country_codes.csv                              │
│  │                                                      │
│  macros/               ← Reusable SQL functions         │
│  │   └── generate_surrogate_key.sql                     │
│  │                                                      │
│  dbt_project.yml       ← Project configuration          │
│  profiles.yml          ← Connection configuration       │
└────────────────────────────────────────────────────────┘
```

### 5.2 dbt Models

Each model is a SQL SELECT statement. dbt handles CREATE TABLE / CREATE VIEW:

```sql
-- models/staging/stg_orders.sql
-- Staging model: clean raw data, rename columns, cast types

{{ config(materialized='view') }}

SELECT
    id AS order_id,
    customer_id,
    CAST(order_date AS DATE) AS order_date,
    CAST(total_amount AS DECIMAL(12, 2)) AS order_total,
    LOWER(status) AS order_status,
    _loaded_at AS loaded_at
FROM {{ source('raw', 'orders') }}
WHERE id IS NOT NULL
```

```sql
-- models/marts/fct_orders.sql
-- Fact model: join staging models, add business logic

{{ config(
    materialized='incremental',
    unique_key='order_id',
    on_schema_change='sync_all_columns'
) }}

SELECT
    o.order_id,
    o.customer_id,
    c.customer_segment,
    d.fiscal_quarter,
    o.order_total,
    o.order_total * COALESCE(t.tax_rate, 0) AS tax_amount,
    o.order_total * (1 + COALESCE(t.tax_rate, 0)) AS total_with_tax,
    o.order_status,
    o.order_date
FROM {{ ref('stg_orders') }} o
LEFT JOIN {{ ref('dim_customers') }} c ON o.customer_id = c.customer_id
LEFT JOIN {{ ref('dim_date') }} d ON o.order_date = d.calendar_date
LEFT JOIN {{ ref('stg_tax_rates') }} t ON c.state = t.state

{% if is_incremental() %}
WHERE o.loaded_at > (SELECT MAX(loaded_at) FROM {{ this }})
{% endif %}
```

### 5.3 Materialization Types

| Materialization | What dbt creates | Best for |
|---|---|---|
| `view` | CREATE VIEW | Staging models, lightweight transforms |
| `table` | CREATE TABLE (full rebuild each run) | Dimension tables, small fact tables |
| `incremental` | INSERT/MERGE only new/changed rows | Large fact tables, event data |
| `ephemeral` | CTE (inlined into downstream models) | Intermediate logic, no physical table |

### 5.4 dbt Tests

```sql
-- schema.yml (generic tests):
models:
  - name: fct_orders
    columns:
      - name: order_id
        tests:
          - unique
          - not_null
      - name: order_total
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 1000000
      - name: customer_id
        tests:
          - relationships:
              to: ref('dim_customers')
              field: customer_id

-- Custom test (singular):
-- tests/assert_no_orphan_orders.sql
SELECT order_id
FROM {{ ref('fct_orders') }}
WHERE customer_id NOT IN (
    SELECT customer_id FROM {{ ref('dim_customers') }}
)
-- Test passes if this query returns zero rows
```

### 5.5 dbt Macros

```sql
-- macros/generate_surrogate_key.sql
{% macro generate_surrogate_key(field_list) %}
    {{ dbt_utils.generate_surrogate_key(field_list) }}
{% endmacro %}

-- macros/cents_to_dollars.sql
{% macro cents_to_dollars(column_name) %}
    CAST({{ column_name }} AS DECIMAL(12, 2)) / 100
{% endmacro %}

-- Usage in a model:
SELECT
    {{ generate_surrogate_key(['order_id', 'line_item_id']) }} AS sk,
    {{ cents_to_dollars('amount_cents') }} AS amount_dollars
FROM {{ ref('stg_line_items') }}
```

### 5.6 dbt Commands

```bash
# Run all models:
dbt run

# Run specific model and its dependencies:
dbt run --select fct_orders+

# Run only changed models (state-based):
dbt run --select state:modified+

# Run tests:
dbt test

# Run tests for specific model:
dbt test --select fct_orders

# Generate and serve documentation:
dbt docs generate
dbt docs serve

# Seed reference data:
dbt seed

# Full build (seed + run + test + snapshot):
dbt build

# Compile SQL without executing:
dbt compile --select fct_orders
```

---

## 6. Cloud Warehouse Internals

### 6.1 Separation of Compute & Storage

```
Traditional DW (e.g., Teradata, Netezza):
  ┌──────────────────────────────────────────┐
  │  Node 1: CPU + RAM + Local Disk          │
  │  Node 2: CPU + RAM + Local Disk          │
  │  Node 3: CPU + RAM + Local Disk          │
  └──────────────────────────────────────────┘
  Coupled: add storage = add compute. Expensive idle capacity.

Cloud DW (e.g., Snowflake, BigQuery):
  ┌──────────────────┐    ┌──────────────────┐
  │  Compute Layer    │    │  Storage Layer    │
  │  (ephemeral VMs)  │    │  (S3 / GCS / ADLS)│
  │                   │    │                   │
  │  Scale up/down    │    │  Scale            │
  │  per query        │    │  independently    │
  │  Pay per second   │    │  Pay per GB       │
  └──────────────────┘    └──────────────────┘
  
  Benefits:
  - Independent scaling (1 PB storage, burst to 100 nodes for a query)
  - Near-zero cost when idle (suspend compute)
  - Multi-cluster concurrency (different teams, different warehouses)
  - Infinite storage growth without compute changes
```

### 6.2 Snowflake

```
┌────────────────────────────────────────────────────────────┐
│                    Snowflake Architecture                    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Cloud Services Layer                                │   │
│  │  Authentication, metadata, query optimization,       │   │
│  │  access control, transaction management              │   │
│  └──────────────────────────┬───────────────────────────┘   │
│                             │                                │
│  ┌──────────────┐  ┌───────┴──────┐  ┌──────────────┐      │
│  │ Virtual WH   │  │ Virtual WH   │  │ Virtual WH   │      │
│  │ (Analytics)  │  │ (ETL)        │  │ (Dev)        │      │
│  │ Size: XL     │  │ Size: L      │  │ Size: S      │      │
│  │ 16 nodes     │  │ 8 nodes      │  │ 1 node       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                             │                                │
│  ┌──────────────────────────▼───────────────────────────┐   │
│  │  Storage Layer (S3 / Azure Blob / GCS)               │   │
│  │  Micro-partitions: ~50-500 MB compressed, immutable  │   │
│  │  Columnar format, auto-clustered                     │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

**Micro-partitions:**
- Immutable columnar units (~50-500 MB compressed).
- Each micro-partition stores min/max values per column (zone maps).
- Query pruning: `WHERE date = '2026-05-22'` skips all micro-partitions where
  max(date) < '2026-05-22' or min(date) > '2026-05-22'.

**Clustering keys:**

```sql
-- Automatic clustering on frequently filtered columns:
ALTER TABLE events CLUSTER BY (event_date, event_type);

-- Snowflake automatically reorganizes micro-partitions to improve pruning
-- Monitor clustering quality:
SELECT SYSTEM$CLUSTERING_INFORMATION('events', '(event_date, event_type)');
```

**Time Travel:**

```sql
-- Query data as it was 1 hour ago:
SELECT * FROM orders AT (OFFSET => -3600);

-- Query data as of a specific timestamp:
SELECT * FROM orders AT (TIMESTAMP => '2026-05-22 10:00:00'::timestamp);

-- Undrop a table:
UNDROP TABLE accidentally_dropped_table;
```

### 6.3 BigQuery

```
┌────────────────────────────────────────────────────────────┐
│                     BigQuery Architecture                    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Query Engine: Dremel                                │   │
│  │  Tree of "slots" (units of compute)                  │   │
│  │  Root → Mixers → Leaf Workers                        │   │
│  │                                                      │   │
│  │  Leaf workers scan Capacitor files in parallel        │   │
│  │  Mixers aggregate partial results                     │   │
│  │  Root produces final result                          │   │
│  └──────────────────────────────┬───────────────────────┘   │
│                                 │                            │
│  ┌──────────────────────────────▼───────────────────────┐   │
│  │  Storage: Colossus (Google's distributed filesystem)  │   │
│  │  Format: Capacitor (columnar, compressed)             │   │
│  │  Encoding: Dremel encoding for nested data            │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

**Pricing models:**

| Model | Cost | Best for |
|---|---|---|
| On-demand | $6.25/TB scanned | Ad-hoc queries, low volume |
| Flat-rate (editions) | Fixed $/slot-hour | Predictable high-volume workloads |

**BigQuery optimizations:**

```sql
-- Partition by date (reduces scan cost):
CREATE TABLE dataset.events
PARTITION BY DATE(event_timestamp)
CLUSTER BY event_type, user_id
AS SELECT * FROM source_events;

-- Check bytes scanned before running:
SELECT * FROM dataset.events
WHERE DATE(event_timestamp) = '2026-05-22'
-- Dry run: only scans one partition instead of entire table

-- Federated queries (query external sources):
SELECT * FROM EXTERNAL_QUERY(
  'us.my-connection',
  'SELECT * FROM postgres_table WHERE id > 1000'
);
```

### 6.4 Redshift

```
Original Redshift:                   Redshift RA3 (modern):
┌─────────────────────┐             ┌─────────────────────┐
│ Node 1: CPU + SSD   │             │ RA3 Node: CPU + SSD │
│ Node 2: CPU + SSD   │             │  (cache only)       │
│ Node 3: CPU + SSD   │             │  ┌──────────────┐   │
│                     │             │  │ Managed       │   │
│ Data on local SSD   │             │  │ Storage (S3)  │   │
│ (coupled)           │             │  └──────────────┘   │
└─────────────────────┘             └─────────────────────┘
```

**Redshift-specific concepts:**

```sql
-- Distribution styles:
CREATE TABLE orders (
    order_id BIGINT,
    customer_id BIGINT,
    order_date DATE,
    total DECIMAL(12,2)
)
DISTSTYLE KEY       -- distribute rows by this column
DISTKEY (customer_id)  -- co-locate orders for same customer
SORTKEY (order_date);   -- sort within each node for range pruning

-- Distribution styles:
-- KEY:    hash-distribute by column → co-located joins
-- EVEN:   round-robin across nodes → balanced storage
-- ALL:    full copy on every node → small dim tables, no shuffle for joins
-- AUTO:   Redshift picks based on table size
```

### 6.5 ClickHouse

Open-source column-store designed for real-time analytics:

```sql
-- MergeTree engine (the workhorse):
CREATE TABLE events (
    event_date Date,
    event_type String,
    user_id UInt64,
    properties String,
    created_at DateTime
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (event_type, user_id, created_at)
TTL created_at + INTERVAL 90 DAY;

-- ReplacingMergeTree (deduplication):
CREATE TABLE user_profiles (
    user_id UInt64,
    name String,
    email String,
    updated_at DateTime
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY user_id;
-- Keeps only the row with the latest updated_at per ORDER BY key

-- Materialized views (continuous aggregation):
CREATE MATERIALIZED VIEW hourly_events
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMMDD(hour)
ORDER BY (event_type, hour)
AS SELECT
    event_type,
    toStartOfHour(created_at) AS hour,
    count() AS event_count,
    uniq(user_id) AS unique_users
FROM events
GROUP BY event_type, hour;
-- Automatically updated on each INSERT into events
```

---

## 7. Batch vs Stream Processing

### 7.1 Batch Processing

```
┌──────────┐     ┌─────────────────┐     ┌──────────┐
│  Source   │────►│  Batch Engine   │────►│  Sink    │
│  (files, │     │  (Spark, Hive,  │     │  (DW,    │
│   dumps) │     │   MapReduce)    │     │   Lake)  │
└──────────┘     └─────────────────┘     └──────────┘

Characteristics:
  - Process bounded datasets (known start and end)
  - High throughput (process entire dataset at once)
  - High latency (hours: schedule, wait, process)
  - Simple fault tolerance (retry entire job)
  - Idempotent: reprocess = same result
```

### 7.2 Stream Processing

```
┌──────────┐     ┌─────────────────┐     ┌──────────┐
│  Source   │────►│  Stream Engine  │────►│  Sink    │
│  (Kafka, │     │  (Flink, Spark  │     │  (DW,    │
│   events)│     │   Streaming,    │     │   Redis, │
│          │     │   Kafka Streams)│     │   alerts)│
└──────────┘     └─────────────────┘     └──────────┘

Characteristics:
  - Process unbounded datasets (continuous)
  - Low latency (milliseconds to seconds)
  - Lower throughput per event
  - Complex fault tolerance (checkpointing, exactly-once)
  - State management required for aggregations
```

### 7.3 Apache Flink (True Streaming)

```
┌────────────────────────────────────────────────────────────┐
│                    Flink Architecture                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  JobManager (coordinator)                            │   │
│  │  - Schedules tasks                                   │   │
│  │  - Manages checkpoints                               │   │
│  │  - Handles failover                                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ TaskMgr 1│  │ TaskMgr 2│  │ TaskMgr 3│                  │
│  │          │  │          │  │          │                    │
│  │ Source → │  │ Source → │  │ Source → │                    │
│  │ Map →   │  │ Map →   │  │ Map →   │                    │
│  │ Window →│  │ Window →│  │ Window →│                    │
│  │ Sink    │  │ Sink    │  │ Sink    │                    │
│  └──────────┘  └──────────┘  └──────────┘                  │
└────────────────────────────────────────────────────────────┘
```

```java
// Flink streaming example:
StreamExecutionEnvironment env =
    StreamExecutionEnvironment.getExecutionEnvironment();

DataStream<Event> events = env
    .addSource(new FlinkKafkaConsumer<>("events", new EventSchema(), props));

DataStream<Alert> alerts = events
    .keyBy(Event::getUserId)
    .window(TumblingEventTimeWindows.of(Time.minutes(5)))
    .process(new FraudDetectionFunction());

alerts.addSink(new FlinkKafkaProducer<>("alerts", new AlertSchema(), props));

env.execute("Fraud Detection");
```

**Event time vs. Processing time:**

```
Event time:     When the event actually occurred (embedded timestamp)
Processing time: When the system processes the event

Problem: events arrive out of order (network delay, buffering)

Solution: Watermarks
  Watermark(t) = "all events with timestamp <= t have arrived"
  Window closes when watermark passes window end time
  Late events → side output or dropped (configurable)
```

### 7.4 Spark Structured Streaming (Micro-Batch)

```python
# Spark Structured Streaming:
from pyspark.sql import SparkSession
from pyspark.sql.functions import window, col, count

spark = SparkSession.builder.appName("streaming").getOrCreate()

# Read from Kafka:
events = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "broker:9092") \
    .option("subscribe", "events") \
    .load()

# Process:
windowed = events \
    .withWatermark("event_time", "10 minutes") \
    .groupBy(
        window(col("event_time"), "5 minutes"),
        col("event_type")
    ) \
    .agg(count("*").alias("count"))

# Write to Delta Lake:
query = windowed.writeStream \
    .outputMode("append") \
    .format("delta") \
    .option("checkpointLocation", "/checkpoints/windowed") \
    .start("/delta/windowed_counts")

query.awaitTermination()
```

### 7.5 Exactly-Once Semantics

Achieving exactly-once processing requires coordination between source, processor,
and sink:

```
At-most-once:   Process event, then commit offset
                If crash after process but before commit → event lost
                Simple but lossy

At-least-once:  Commit offset, then process event
                If crash after commit but before process → event replayed
                Must handle duplicates

Exactly-once:   Atomic: process + commit offset + write output in one transaction
                Or: at-least-once + idempotent sink
                Complex but correct
```

| Engine | Exactly-Once Approach |
|---|---|
| Flink | Chandy-Lamport distributed snapshots + 2PC sinks |
| Kafka Streams | Kafka transactions (read-process-write atomically) |
| Spark Streaming | Idempotent writes + checkpointed offsets |

---

## 8. Lambda and Kappa Architecture

### 8.1 Lambda Architecture

```
┌────────────────────────────────────────────────────────┐
│                  Lambda Architecture                    │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Batch Layer                                      │  │
│  │  (Spark, Hadoop, nightly ETL)                    │  │
│  │  → "Master dataset" → Batch views                │  │
│  │  Complete, accurate, high latency (hours)        │  │
│  └──────────────────────────────────┬───────────────┘  │
│                                      │                  │
│  Raw Events ──┬───────────────────── │ ──► Merge Layer  │
│               │                      │      (serve)     │
│               │                      │      batch +     │
│  ┌────────────▼─────────────────────┐│      speed       │
│  │  Speed Layer                     ││      views       │
│  │  (Storm, Flink, real-time)       ││                  │
│  │  → Real-time views               ││                  │
│  │  Approximate, low latency (sec)  ││                  │
│  └──────────────────────────────────┘│                  │
└────────────────────────────────────────────────────────┘

Challenges:
  - Maintain TWO code paths (batch + speed) for same logic
  - Merge layer complexity
  - Debugging: which layer produced wrong result?
  - Operational burden of two separate systems
```

### 8.2 Kappa Architecture

```
┌────────────────────────────────────────────────────────┐
│                  Kappa Architecture                      │
│                                                         │
│  Raw Events ──► Kafka (immutable log) ──► Stream        │
│                                           Processor     │
│                                           (Flink)       │
│                                              │          │
│                                              ▼          │
│                                          Serving DB     │
│                                                         │
│  Reprocessing: replay Kafka log with updated logic      │
│  Same code path for real-time and historical            │
└────────────────────────────────────────────────────────┘

Advantages:
  - Single code path (stream only)
  - Simpler to maintain and debug
  - Reprocess by replaying the log

Challenges:
  - Kafka retention must cover reprocessing window
  - Stream reprocessing slower than batch for large datasets
  - Some complex analytics still easier in batch SQL
```

### 8.3 When to Choose

| Factor | Lambda | Kappa |
|---|---|---|
| Logic complexity | High (batch SQL easier for complex joins) | Lower |
| Latency requirement | Real-time + batch accuracy | Real-time sufficient |
| Team skill | Separate batch/stream teams | Unified stream team |
| Reprocessing | Re-run batch job | Replay Kafka log |
| Modern recommendation | Legacy, avoid for new systems | Preferred when feasible |

---

## 9. Data Lakehouse

### 9.1 Evolution

```
Generation 1: Data Warehouse (1990s-2010s)
  - Structured data only
  - Proprietary formats (Oracle, Teradata)
  - Expensive storage, coupled compute
  - Strong governance, ACID, SQL

Generation 2: Data Lake (2010s)
  - All data types (structured, semi-structured, unstructured)
  - Open formats on cheap object storage (HDFS/S3)
  - Schema-on-read
  - Weak governance: "data swamp" problem
  - No ACID, no time travel

Generation 3: Data Lakehouse (2020s)
  - Open formats on object storage
  - ACID transactions via table formats (Iceberg, Delta Lake, Hudi)
  - Schema enforcement + evolution
  - Time travel, versioning
  - Direct SQL query access (no ETL to separate DW needed)
```

### 9.2 Lakehouse Table Formats

#### Apache Iceberg

```
Iceberg Architecture:
  ┌──────────────────────────────────────────────────────┐
  │  Catalog (Hive Metastore, REST, Nessie)              │
  │  Points to current metadata file                     │
  └──────────────────────────┬───────────────────────────┘
                             │
  ┌──────────────────────────▼───────────────────────────┐
  │  Metadata File (JSON)                                │
  │  Schema, partition spec, sort order, snapshots[]     │
  └──────────────────────────┬───────────────────────────┘
                             │
  ┌──────────────────────────▼───────────────────────────┐
  │  Manifest List (Avro)                                │
  │  Points to manifest files for this snapshot          │
  └──────────────────────────┬───────────────────────────┘
                             │
  ┌──────────────────────────▼───────────────────────────┐
  │  Manifest File (Avro)                                │
  │  Lists data files + per-file statistics              │
  │  (min/max per column, row count, null count)         │
  └──────────────────────────┬───────────────────────────┘
                             │
  ┌──────────────────────────▼───────────────────────────┐
  │  Data Files (Parquet, ORC, Avro)                     │
  │  Actual row data, stored on S3/GCS/ADLS              │
  └──────────────────────────────────────────────────────┘
```

**Key Iceberg features:**

```sql
-- Hidden partitioning (no partition columns in data):
CREATE TABLE events (
    event_id BIGINT,
    event_time TIMESTAMP,
    event_type STRING,
    payload STRING
) USING iceberg
PARTITIONED BY (days(event_time), bucket(16, event_type));
-- Users query by event_time; Iceberg auto-prunes partitions

-- Partition evolution (change partitioning without rewriting data):
ALTER TABLE events ADD PARTITION FIELD months(event_time);
-- Old data uses daily partitioning, new data uses monthly
-- Queries transparently handle both

-- Schema evolution:
ALTER TABLE events ADD COLUMNS (source STRING, version INT);
ALTER TABLE events RENAME COLUMN payload TO event_payload;
-- Old data files keep old schema; reads apply schema evolution rules

-- Time travel:
SELECT * FROM events VERSION AS OF 5;  -- snapshot ID
SELECT * FROM events TIMESTAMP AS OF '2026-05-22 10:00:00';

-- Rollback:
CALL system.rollback_to_snapshot('db.events', 5);
```

#### Delta Lake

```
Delta Lake on disk:

table_path/
├── _delta_log/
│   ├── 00000000000000000000.json   ← transaction 0 (CREATE TABLE)
│   ├── 00000000000000000001.json   ← transaction 1 (INSERT)
│   ├── 00000000000000000002.json   ← transaction 2 (UPDATE)
│   ├── ...
│   └── 00000000000000000010.checkpoint.parquet  ← checkpoint
├── part-00000-xxxx.snappy.parquet  ← data file
├── part-00001-xxxx.snappy.parquet
└── ...
```

```python
# Delta Lake with PySpark:
from delta.tables import DeltaTable

# Write:
df.write.format("delta").mode("overwrite").save("/delta/events")

# Read with time travel:
df = spark.read.format("delta").option("versionAsOf", 5).load("/delta/events")

# MERGE (upsert):
deltaTable = DeltaTable.forPath(spark, "/delta/customers")

deltaTable.alias("target").merge(
    updates.alias("source"),
    "target.customer_id = source.customer_id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()

# Z-Order (optimize layout for common filters):
deltaTable.optimize().zOrderBy("event_date", "event_type").executeCompaction()
```

#### Apache Hudi

```
Hudi table types:

Copy-on-Write (CoW):
  - Each update rewrites the entire Parquet file
  - Read performance: excellent (pure Parquet reads)
  - Write performance: slower (rewrite entire file for one update)
  - Best for: read-heavy workloads with infrequent updates

Merge-on-Read (MoR):
  - Updates written to delta log files (Avro)
  - Reads merge base Parquet + delta log
  - Compaction periodically merges delta into Parquet
  - Read performance: slower (merge required)
  - Write performance: fast (append-only delta log)
  - Best for: write-heavy, CDC, near-real-time ingestion
```

### 9.3 Table Format Comparison

| Feature | Iceberg | Delta Lake | Hudi |
|---|---|---|---|
| Origin | Netflix | Databricks | Uber |
| Governance | Apache | Linux Foundation (open) | Apache |
| Hidden partitioning | Yes (killer feature) | No | No |
| Partition evolution | Yes | No | Limited |
| Schema evolution | Full (add, rename, reorder, drop) | Add, rename | Add, rename |
| Time travel | Yes (snapshot-based) | Yes (log-based) | Yes (timeline-based) |
| Upsert | MERGE INTO | MERGE INTO | Built-in (core feature) |
| Streaming ingest | Via Flink connector | Spark Streaming native | Deltastreamer |
| Engine support | Spark, Flink, Trino, Dremio, Snowflake | Spark, Databricks, Flink | Spark, Flink, Presto |
| Catalog | REST, Hive, Nessie, Polaris | Unity Catalog, Hive | Hive |

---

## 10. Medallion Architecture

### 10.1 Three-Layer Pattern

```
┌────────────────────────────────────────────────────────────┐
│                    Medallion Architecture                    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Bronze (Raw)                                        │    │
│  │  - Exact copy of source data                         │    │
│  │  - Append-only, immutable                            │    │
│  │  - Preserves source schema                           │    │
│  │  - Includes metadata: _ingested_at, _source, _batch  │    │
│  │  - Format: Delta / Iceberg / raw Parquet             │    │
│  └─────────────────────────┬───────────────────────────┘    │
│                            │  Clean, deduplicate, conform    │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Silver (Cleaned / Conformed)                        │    │
│  │  - Validated, deduplicated, type-cast                │    │
│  │  - Standardized naming conventions                   │    │
│  │  - Joined with reference data                        │    │
│  │  - NULL handling, data quality checks                │    │
│  │  - Conformed dimensions across sources               │    │
│  └─────────────────────────┬───────────────────────────┘    │
│                            │  Aggregate, model, serve        │
│                            ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Gold (Business-Level / Serving)                     │    │
│  │  - Star schema facts and dimensions                  │    │
│  │  - Aggregated metrics (daily/weekly/monthly)         │    │
│  │  - ML feature stores                                 │    │
│  │  - Dashboard-ready datasets                          │    │
│  │  - Business KPIs                                     │    │
│  └─────────────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────────────┘
```

### 10.2 dbt + Medallion Mapping

```
dbt project structure:
  models/
  ├── bronze/        → source() references, minimal transformation
  │   ├── brz_orders.sql
  │   └── brz_customers.sql
  ├── silver/        → ref('brz_*'), cleaning + conforming
  │   ├── slv_orders.sql
  │   └── slv_customers.sql
  └── gold/          → ref('slv_*'), business models
      ├── fct_daily_revenue.sql
      └── dim_customer_360.sql
```

---

## 11. Change Data Capture (CDC)

### 11.1 CDC Methods

```
┌──────────────────────────────────────────────────────────────┐
│  CDC Methods                                                  │
│                                                                │
│  1. Trigger-based                                              │
│     DB trigger writes to audit/shadow table                   │
│     + Simple                                                   │
│     - Intrusive (performance impact on source DB)             │
│     - Schema changes break triggers                           │
│                                                                │
│  2. Timestamp-based (polling)                                  │
│     Query: SELECT * FROM orders WHERE updated_at > :last_run  │
│     + No DB changes needed                                    │
│     - Misses deletes                                          │
│     - Requires reliable updated_at column                     │
│     - Polling interval = latency floor                        │
│                                                                │
│  3. Log-based (WAL / binlog)                                   │
│     Read database's transaction log directly                  │
│     + Minimal source DB impact                                │
│     + Captures all changes including deletes                  │
│     + Preserves order                                         │
│     - Requires log retention configuration                    │
│     - Log format is DB-specific                               │
└──────────────────────────────────────────────────────────────┘
```

### 11.2 Debezium

Open-source CDC platform built on Kafka Connect:

```
┌──────────┐     ┌───────────┐     ┌──────────┐     ┌──────────┐
│ PostgreSQL│────►│  Debezium │────►│  Kafka   │────►│  Sink    │
│ (WAL)    │     │  Connector│     │  Topic   │     │  (DW,    │
│          │     │           │     │          │     │   Lake,  │
│ MySQL    │     │  Reads    │     │ per-table│     │   Search)│
│ (binlog) │     │  WAL/     │     │  topic   │     │          │
│          │     │  binlog   │     │          │     │          │
│ MongoDB  │     │           │     │          │     │          │
│ (oplog)  │     │           │     │          │     │          │
└──────────┘     └───────────┘     └──────────┘     └──────────┘
```

**Debezium event structure:**

```json
{
  "schema": { ... },
  "payload": {
    "before": {
      "id": 1001,
      "name": "Alice",
      "email": "alice@old.com"
    },
    "after": {
      "id": 1001,
      "name": "Alice",
      "email": "alice@new.com"
    },
    "source": {
      "version": "2.5.0",
      "connector": "postgresql",
      "db": "mydb",
      "schema": "public",
      "table": "customers",
      "lsn": 123456789,
      "txId": 54321
    },
    "op": "u",
    "ts_ms": 1716393060000
  }
}
```

Operations: `c` (create), `u` (update), `d` (delete), `r` (read/snapshot)

---

## 12. Slowly Changing Dimensions (SCD)

### 12.1 SCD Types

| Type | Strategy | History | Example |
|---|---|---|---|
| 0 | Retain original | None | Birth date (never changes) |
| 1 | Overwrite | None | Typo correction |
| 2 | New row + valid_from/valid_to | Full | Customer address |
| 3 | Add previous_value column | 1-step | Limited history |
| 6 | Hybrid 1+2+3 | Full | Complex requirements |

### 12.2 Type 2 SCD Implementation

```sql
-- Dimension table with Type 2 SCD:
CREATE TABLE dim_customer (
    customer_sk    BIGINT PRIMARY KEY,  -- surrogate key
    customer_id    VARCHAR(50),          -- natural key (from source)
    name           VARCHAR(200),
    email          VARCHAR(200),
    city           VARCHAR(100),
    state          VARCHAR(50),
    segment        VARCHAR(50),
    valid_from     TIMESTAMP NOT NULL,
    valid_to       TIMESTAMP,            -- NULL = current version
    is_current     BOOLEAN DEFAULT TRUE,
    row_hash       CHAR(64)              -- SHA-256 of tracked columns
);

-- Fact table references surrogate key:
CREATE TABLE fact_orders (
    order_id       BIGINT,
    customer_sk    BIGINT REFERENCES dim_customer(customer_sk),
    -- NOT customer_id — we need the VERSION valid at order time
    product_sk     BIGINT,
    date_key       INT,
    quantity       INT,
    revenue        DECIMAL(12,2)
);
```

```sql
-- Type 2 SCD merge with dbt (dbt snapshot):
-- dbt_project.yml
snapshots:
  - name: snap_customer
    relation: source('raw', 'customers')
    strategy: check
    check_cols: ['name', 'email', 'city', 'state', 'segment']
    unique_key: customer_id
    updated_at: updated_at
```

```sql
-- Manual Type 2 merge (e.g., in Snowflake):
MERGE INTO dim_customer AS target
USING stg_customers AS source
ON target.customer_id = source.customer_id AND target.is_current = TRUE
WHEN MATCHED AND target.row_hash != source.row_hash THEN
    UPDATE SET
        valid_to = CURRENT_TIMESTAMP,
        is_current = FALSE
WHEN NOT MATCHED THEN
    INSERT (customer_sk, customer_id, name, email, city, state, segment,
            valid_from, valid_to, is_current, row_hash)
    VALUES (seq_customer.NEXTVAL, source.customer_id, source.name,
            source.email, source.city, source.state, source.segment,
            CURRENT_TIMESTAMP, NULL, TRUE, source.row_hash);

-- Insert new version for updated customers:
INSERT INTO dim_customer
SELECT seq_customer.NEXTVAL, customer_id, name, email, city, state, segment,
       CURRENT_TIMESTAMP, NULL, TRUE, row_hash
FROM stg_customers source
WHERE EXISTS (
    SELECT 1 FROM dim_customer target
    WHERE target.customer_id = source.customer_id
    AND target.is_current = FALSE
    AND target.valid_to = CURRENT_TIMESTAMP
);
```

---

## 13. Data Quality

### 13.1 Data Quality Dimensions

| Dimension | Definition | Measurement |
|---|---|---|
| Completeness | All expected records and fields present | % non-null, row count vs. expected |
| Accuracy | Values match reality | Comparison with source, validation rules |
| Consistency | Same data tells same story across systems | Cross-system reconciliation |
| Timeliness | Data arrives within SLA | Ingestion lag, freshness metric |
| Uniqueness | No unintended duplicates | Duplicate count, PK uniqueness |
| Validity | Values conform to defined rules/formats | Regex, range checks, enum validation |

### 13.2 Data Quality Tools

```
┌────────────────────────────────────────────────────────────┐
│  Tool                │ Type        │ Integration           │
├──────────────────────┼─────────────┼───────────────────────┤
│  Great Expectations  │ Python lib  │ Airflow, dbt, Spark   │
│  dbt tests           │ SQL-native  │ dbt project           │
│  Soda                │ YAML config │ Any SQL warehouse     │
│  Monte Carlo         │ SaaS        │ Snowflake, BigQuery   │
│  Elementary          │ dbt package │ dbt + Slack alerts     │
│  Datafold            │ SaaS + CLI  │ dbt Cloud, CI/CD      │
└────────────────────────────────────────────────────────────┘
```

### 13.3 Great Expectations Example

```python
import great_expectations as gx

context = gx.get_context()

# Define expectations:
suite = context.add_expectation_suite("orders_suite")

suite.add_expectation(
    gx.expectations.ExpectColumnValuesToNotBeNull(column="order_id")
)
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToBeUnique(column="order_id")
)
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToBeBetween(
        column="order_total",
        min_value=0,
        max_value=1000000
    )
)
suite.add_expectation(
    gx.expectations.ExpectColumnDistinctValuesToBeInSet(
        column="status",
        value_set=["pending", "completed", "cancelled", "refunded"]
    )
)

# Run validation:
results = context.run_checkpoint(
    checkpoint_name="orders_checkpoint",
    batch_request=batch_request
)

if not results.success:
    raise ValueError(f"Data quality check failed: {results}")
```

### 13.4 Data Observability

```
Data observability = monitoring + alerting + lineage for data pipelines

Key metrics:
  - Row count trends (sudden drops or spikes)
  - Schema changes (new columns, type changes)
  - Freshness (time since last update)
  - Distribution shifts (mean, std, percentiles)
  - Null rate changes
  - Referential integrity failures
  - Cross-table consistency

Architecture:
  Source DB → CDC → Kafka → Flink → Data Lake
       │                              │
       └── Data observability layer ──┘
           (Monte Carlo / Elementary / custom)
           └── Alerts → Slack / PagerDuty
```

---

## 14. Orchestration

### 14.1 Apache Airflow

The dominant orchestrator for data pipelines:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.dbt.cloud.operators.dbt import DbtCloudRunJobOperator
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator
from datetime import datetime, timedelta

default_args = {
    "owner": "data-team",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "daily_etl",
    default_args=default_args,
    schedule_interval="0 6 * * *",  # 6 AM daily
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["production"],
) as dag:

    extract = PythonOperator(
        task_id="extract_from_api",
        python_callable=extract_data,
    )

    load_raw = SnowflakeOperator(
        task_id="load_to_raw",
        sql="COPY INTO raw.events FROM @stage/events/",
        snowflake_conn_id="snowflake_prod",
    )

    transform = DbtCloudRunJobOperator(
        task_id="dbt_run",
        job_id=12345,
        check_interval=30,
        timeout=3600,
    )

    quality_check = PythonOperator(
        task_id="data_quality",
        python_callable=run_quality_checks,
    )

    extract >> load_raw >> transform >> quality_check
```

### 14.2 Dagster

Modern alternative to Airflow with software-engineering-first approach:

```python
import dagster as dg

@dg.asset(
    group_name="bronze",
    compute_kind="python",
)
def raw_orders(context) -> pd.DataFrame:
    """Extract orders from source API."""
    df = extract_orders_from_api()
    context.log.info(f"Extracted {len(df)} orders")
    return df

@dg.asset(
    group_name="silver",
    deps=[raw_orders],
    compute_kind="dbt",
)
def clean_orders(context, raw_orders: pd.DataFrame) -> pd.DataFrame:
    """Clean and validate orders."""
    df = raw_orders.dropna(subset=["order_id", "total"])
    df = df[df["total"] > 0]
    return df

@dg.asset(
    group_name="gold",
    deps=[clean_orders],
    compute_kind="snowflake",
)
def daily_revenue(context, clean_orders: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily revenue."""
    return clean_orders.groupby("order_date").agg(
        total_revenue=("total", "sum"),
        order_count=("order_id", "count"),
    ).reset_index()
```

---

## 15. Modern Data Stack

```
┌────────────────────────────────────────────────────────────────┐
│                    Modern Data Stack (2024+)                    │
│                                                                  │
│  Ingestion:     Fivetran / Airbyte / Meltano                    │
│  Storage:       Snowflake / BigQuery / Databricks / S3+Iceberg  │
│  Transform:     dbt (Core or Cloud)                              │
│  Orchestration: Airflow / Dagster / Prefect                      │
│  Quality:       Great Expectations / Elementary / Soda           │
│  Catalog:       DataHub / OpenMetadata / Atlan                   │
│  BI:            Looker / Tableau / Metabase / Preset             │
│  Reverse ETL:   Census / Hightouch                               │
│  Feature Store: Feast / Tecton                                   │
│  Observability: Monte Carlo / Datafold                           │
└────────────────────────────────────────────────────────────────┘
```

---

## References

- **The Data Warehouse Toolkit** — Kimball and Ross, 3rd edition.
- **Building the Data Warehouse** — Inmon, 4th edition.
- **Designing Data-Intensive Applications** — Kleppmann, 2017. Chapters 3, 10, 11, 12.
- **Apache Iceberg spec** — iceberg.apache.org/spec
- **Delta Lake protocol** — github.com/delta-io/delta/blob/master/PROTOCOL.md
- **dbt documentation** — docs.getdbt.com
- **Dremel paper** — Melnik et al., "Dremel: Interactive Analysis of Web-Scale
  Datasets," VLDB 2010.
- **The Lambda Architecture** — Nathan Marz, manning.com/books/big-data
- **Streaming Systems** — Akidau, Chernyak, Lax, 2018.
- **Fundamentals of Data Engineering** — Reis and Housley, 2022.
