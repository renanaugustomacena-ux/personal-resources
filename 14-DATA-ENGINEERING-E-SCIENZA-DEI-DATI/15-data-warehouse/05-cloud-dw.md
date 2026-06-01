# Cloud Data Warehouses: Snowflake, BigQuery, Redshift, Databricks

Modern cloud data warehouses have fundamentally changed data engineering by separating
compute from storage, eliminating infrastructure administration, and making petabyte-scale
analytics accessible to organisations of any size. This document covers the architecture,
features, SQL patterns, and cost optimisation strategies for the four major platforms.

---

## Table of Contents

1. Architecture Principles
2. Google BigQuery
3. Snowflake
4. Amazon Redshift
5. Databricks (Lakehouse)
6. Comparison Matrix
7. Cost Optimisation
8. Data Sharing and Governance
9. Migration Strategies
10. Troubleshooting
11. Frequently Asked Questions
12. Exercises

---

## 1. Architecture Principles

All modern cloud DWs share three architectural principles:

### 1.1 Separation of Compute and Storage

```
Traditional DW (MPP appliance):
  ┌────────────────────────┐
  │ Compute + Storage      │     Storage and compute are tightly coupled.
  │ (same nodes)           │     Scaling one requires scaling both.
  │ ┌──────┐ ┌──────┐     │     Idle compute still costs money.
  │ │Node 1│ │Node 2│ ... │
  │ └──────┘ └──────┘     │
  └────────────────────────┘

Cloud DW:
  ┌──────────────────┐         ┌──────────────────────────────┐
  │ Compute Layer    │ ◄─────► │ Storage Layer                │
  │ (scale up/down   │         │ (S3, GCS, Azure Blob)        │
  │  independently)  │         │ Pay only for data stored     │
  │ Pay per second   │         │ Practically unlimited        │
  │ or per byte      │         │                              │
  └──────────────────┘         └──────────────────────────────┘
```

### 1.2 Columnar Storage with Compression

All cloud DWs store data in columnar format internally (BigQuery's Capacitor, Snowflake's
micro-partitions, Redshift's 1 MB blocks). This enables projection pushdown, predicate
pushdown via zone maps, and aggressive compression.

### 1.3 Massively Parallel Processing (MPP)

Queries are distributed across many compute nodes that process different partitions of data
simultaneously, then merge results. The query planner decides how to distribute the work
based on table statistics and data distribution.

---

## 2. Google BigQuery

BigQuery is Google Cloud's serverless data warehouse. It has no clusters, nodes, or
capacity to manage. The pricing model is either per-byte-scanned (on-demand) or per-slot
(flat-rate capacity reservations). Internally, BigQuery is built on Dremel (query engine),
Colossus (distributed file system), and Jupiter (network).

### 2.1 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    BigQuery                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────┐ │
│  │ Dremel      │   │ Colossus     │   │ Jupiter      │ │
│  │ Query Engine│   │ Storage      │   │ Network      │ │
│  │ (serverless)│◄─►│ (columnar,   │◄─►│ (petabit/s)  │ │
│  │             │   │  Capacitor)  │   │              │ │
│  └─────────────┘   └──────────────┘   └──────────────┘ │
│                                                         │
│  Metadata layer: slot management, caching,              │
│  access control, query scheduling                       │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Partitioning and Clustering

```sql
-- Partitioning: physically divides the table by a column (typically DATE/TIMESTAMP)
-- Clustering: sorts data within each partition by up to 4 columns

CREATE OR REPLACE TABLE `myproject.analytics.fact_sales`
PARTITION BY DATE(created_at)           -- partition by date
CLUSTER BY customer_id, product_id      -- sort within partitions
OPTIONS (
  partition_expiration_days = 365,       -- auto-delete old partitions (cost saving)
  require_partition_filter = TRUE        -- error if query does not filter on partition
)
AS SELECT * FROM `myproject.staging.raw_sales`;

-- Integer range partitioning (for non-date columns)
CREATE TABLE `myproject.analytics.events`
PARTITION BY RANGE_BUCKET(event_type_id, GENERATE_ARRAY(0, 100, 10))
CLUSTER BY user_id
AS SELECT * FROM `myproject.staging.raw_events`;

-- Ingestion-time partitioning (partition by load time, not data column)
CREATE TABLE `myproject.analytics.logs`
PARTITION BY _PARTITIONDATE    -- auto-assigned by BigQuery at ingestion time
CLUSTER BY severity, service_name
OPTIONS (require_partition_filter = TRUE);
```

### 2.3 Query Cost Estimation

```sql
-- BigQuery charges per byte scanned (on-demand: ~$6.25/TB in US multi-region)
-- Always check estimated bytes before running expensive queries

-- Method 1: dry run (API or bq CLI)
-- bq query --dry_run --use_legacy_sql=false 'SELECT ...'

-- Method 2: INFORMATION_SCHEMA after execution
SELECT
  job_id,
  ROUND(total_bytes_processed / POW(1024, 3), 3) AS gb_scanned,
  ROUND(total_bytes_billed / POW(1024, 3), 3)    AS gb_billed,
  total_slot_ms / 1000                             AS slot_seconds,
  TIMESTAMP_DIFF(end_time, start_time, SECOND)     AS duration_s,
  cache_hit,
  query
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE start_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
  AND job_type = 'QUERY'
ORDER BY total_bytes_processed DESC
LIMIT 20;

-- Cost estimation: gb_billed * $6.25 / 1000 (on-demand pricing)
```

### 2.4 BigQuery Semi-Structured Data

```sql
-- BigQuery natively supports ARRAY, STRUCT, and JSON types

-- Nested STRUCT
SELECT
  customer_id,
  address.city,
  address.country
FROM `analytics.customers`
WHERE address.country = 'US';

-- ARRAY operations
SELECT
  customer_id,
  ARRAY_AGG(
    STRUCT(product_id, quantity, unit_price)
    ORDER BY unit_price DESC
    LIMIT 5
  ) AS top_products
FROM `analytics.fact_sales`
WHERE DATE(created_at) = '2024-01-15'
GROUP BY customer_id;

-- UNNEST: flatten arrays into rows
SELECT
  order_id,
  item.product_id,
  item.quantity,
  item.unit_price
FROM `analytics.orders`,
  UNNEST(line_items) AS item
WHERE item.quantity > 5;

-- JSON column (BigQuery JSON type)
SELECT
  event_id,
  JSON_VALUE(payload, '$.action') AS action,
  CAST(JSON_VALUE(payload, '$.duration_ms') AS INT64) AS duration_ms
FROM `analytics.events`
WHERE JSON_VALUE(payload, '$.action') = 'purchase';
```

### 2.5 BigQuery ML

```sql
-- Train a logistic regression model using SQL
CREATE OR REPLACE MODEL `analytics.churn_model`
OPTIONS (
  model_type = 'LOGISTIC_REG',
  input_label_cols = ['churned'],
  auto_class_weights = TRUE,
  max_iterations = 20,
  l2_reg = 0.01
) AS
SELECT
  customer_id,
  COUNT(*)                                                    AS order_count,
  SUM(net_revenue)                                            AS total_revenue,
  DATE_DIFF(CURRENT_DATE(), MAX(DATE(created_at)), DAY)       AS days_since_last,
  COUNTIF(DATE(created_at) > DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY))
                                                              AS orders_last_90d,
  churned
FROM `analytics.customer_features`
GROUP BY customer_id, churned;

-- Evaluate model
SELECT * FROM ML.EVALUATE(MODEL `analytics.churn_model`);

-- Predict on new data
SELECT
  customer_id,
  predicted_churned,
  predicted_churned_probs[OFFSET(1)].prob AS churn_probability
FROM ML.PREDICT(
  MODEL `analytics.churn_model`,
  (SELECT * FROM `analytics.customer_features` WHERE churned IS NULL)
)
ORDER BY churn_probability DESC
LIMIT 100;
```

### 2.6 BigQuery BI Engine

BI Engine is an in-memory acceleration layer for BigQuery. It caches frequently accessed
data in memory, providing sub-second response times for BI dashboards.

```sql
-- Create a BI Engine reservation (via console or API)
-- Capacity is measured in GB of RAM reserved
-- BI Engine automatically accelerates queries on tables that fit in the reservation

-- No SQL changes needed — queries against the same tables automatically
-- use BI Engine if the reservation is active and the data fits.

-- Check BI Engine usage
SELECT
  project_id,
  bi_engine_statistics.bi_engine_mode,
  bi_engine_statistics.acceleration_mode,
  total_bytes_processed
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE bi_engine_statistics IS NOT NULL
  AND start_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR);
```

### 2.7 Python Integration

```python
from google.cloud import bigquery
import pandas as pd

client = bigquery.Client(project='myproject')

# Parameterised query (prevents SQL injection)
query = """
    SELECT
        DATE_TRUNC(created_at, MONTH) AS month,
        category,
        SUM(net_revenue) AS revenue,
        COUNT(DISTINCT customer_id) AS unique_customers
    FROM `analytics.fact_sales`
    WHERE DATE(created_at) BETWEEN @start_date AND @end_date
      AND category IN UNNEST(@categories)
    GROUP BY 1, 2
    ORDER BY 1, revenue DESC
"""

job_config = bigquery.QueryJobConfig(
    query_parameters=[
        bigquery.ScalarQueryParameter("start_date", "DATE", "2024-01-01"),
        bigquery.ScalarQueryParameter("end_date", "DATE", "2024-12-31"),
        bigquery.ArrayQueryParameter("categories", "STRING",
                                     ["Electronics", "Clothing"]),
    ]
)

df = client.query(query, job_config=job_config).to_dataframe()

# Load data to BigQuery from Pandas
table_ref = bigquery.TableReference.from_string('myproject.staging.orders_raw')
load_config = bigquery.LoadJobConfig(
    schema=[
        bigquery.SchemaField("order_id", "INTEGER"),
        bigquery.SchemaField("customer_id", "STRING"),
        bigquery.SchemaField("amount", "NUMERIC"),
        bigquery.SchemaField("created_at", "TIMESTAMP"),
    ],
    write_disposition="WRITE_APPEND",
    time_partitioning=bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="created_at",
    ),
)

job = client.load_table_from_dataframe(df, table_ref, job_config=load_config)
job.result()  # wait for completion
print(f"Loaded {job.output_rows} rows")
```

---

## 3. Snowflake

Snowflake is a cloud-agnostic data warehouse (runs on AWS, GCP, and Azure). Its
architecture separates storage (object storage), compute (virtual warehouses), and cloud
services (query routing, metadata, authentication, optimisation).

### 3.1 Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Snowflake                             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              Cloud Services Layer                       │ │
│  │  Query compilation, optimisation, metadata, auth,       │ │
│  │  transaction management, result caching                 │ │
│  └─────────────────────────────────────────────────────────┘ │
│                            │                                 │
│  ┌─────────────────────────┼──────────────────────────────┐  │
│  │         Compute Layer (Virtual Warehouses)             │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐               │  │
│  │  │ VW: ETL │  │ VW: BI  │  │ VW: DS  │  ...          │  │
│  │  │ (L)     │  │ (M)     │  │ (XL)    │               │  │
│  │  └─────────┘  └─────────┘  └─────────┘               │  │
│  │  Each VW scales independently, suspends when idle     │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                 │
│  ┌─────────────────────────┼──────────────────────────────┐  │
│  │         Storage Layer (micro-partitions)               │  │
│  │  S3 / GCS / Azure Blob                                │  │
│  │  Columnar, compressed, immutable files                │  │
│  │  Metadata: min/max per column per micro-partition      │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Virtual Warehouses

```sql
-- Create a virtual warehouse
CREATE WAREHOUSE analytics_wh
  WAREHOUSE_SIZE = 'X-SMALL'     -- XS, S, M, L, XL, 2XL, 3XL, 4XL, 5XL, 6XL
  AUTO_SUSPEND = 300              -- suspend after 5 minutes of inactivity
  AUTO_RESUME = TRUE              -- resume automatically when a query arrives
  INITIALLY_SUSPENDED = TRUE
  COMMENT = 'Warehouse for BI and analytics queries';

-- Multi-cluster warehouse for high concurrency
CREATE WAREHOUSE reporting_wh
  WAREHOUSE_SIZE = 'MEDIUM'
  MIN_CLUSTER_COUNT = 1
  MAX_CLUSTER_COUNT = 5           -- auto-scale up to 5 clusters
  SCALING_POLICY = 'ECONOMY'     -- ECONOMY: wait before scaling; STANDARD: scale quickly
  AUTO_SUSPEND = 120;

-- Resize warehouse for a heavy workload
ALTER WAREHOUSE analytics_wh SET WAREHOUSE_SIZE = 'LARGE';
-- Run the heavy query...
ALTER WAREHOUSE analytics_wh SET WAREHOUSE_SIZE = 'X-SMALL';

-- Query routing: use different warehouses for different workloads
USE WAREHOUSE etl_wh;     -- for ETL jobs
USE WAREHOUSE bi_wh;      -- for BI queries
USE WAREHOUSE ds_wh;      -- for data science (Snowpark)
```

### 3.3 Micro-Partitions and Clustering

```sql
-- Snowflake automatically partitions data into micro-partitions (50-500 MB compressed).
-- Clustering reorders micro-partitions by specified columns for better pruning.

-- Define cluster keys on a table
ALTER TABLE fact_sales CLUSTER BY (date_key, customer_key);

-- Check clustering quality
SELECT SYSTEM$CLUSTERING_INFORMATION('fact_sales');
-- Returns: average_overlaps, average_depth, clustering_ratio
-- Lower overlap + lower depth = better clustering

-- Check pruning efficiency for a specific query
SELECT
  query_id,
  query_text,
  partitions_scanned,
  partitions_total,
  ROUND(partitions_scanned / NULLIF(partitions_total, 0) * 100, 2) AS pct_scanned
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY(
  date_range_start => DATEADD('hours', -24, CURRENT_TIMESTAMP())
))
WHERE execution_status = 'SUCCESS'
ORDER BY total_elapsed_time DESC
LIMIT 20;
```

### 3.4 Time Travel and Cloning

```sql
-- Time Travel: access data as it was at a previous point in time (1-90 days)

-- Read data as it was 1 hour ago
SELECT * FROM fact_sales AT (OFFSET => -3600);

-- Read data as it was at a specific timestamp
SELECT * FROM fact_sales AT (TIMESTAMP => '2024-01-15 10:30:00'::TIMESTAMP);

-- Read data before a specific query was executed
SELECT * FROM fact_sales BEFORE (STATEMENT => '01a3f6e8-0000-0001-0000-000000000123');

-- Restore a dropped table
DROP TABLE fact_sales;
UNDROP TABLE fact_sales;

-- Zero-copy clone: instant, no data physically copied
-- Clones share underlying micro-partitions until one side modifies data
CREATE DATABASE dev_db CLONE prod_db;          -- clone entire database (instant)
CREATE TABLE fact_sales_backup CLONE fact_sales;    -- clone single table
CREATE TABLE fact_sales_snapshot CLONE fact_sales
  AT (TIMESTAMP => '2024-01-15 00:00:00'::TIMESTAMP);  -- clone from time travel

-- Cloning is free (no additional storage until data diverges)
```

### 3.5 Snowpipe and Continuous Loading

```sql
-- Stage: external location for data files
CREATE STAGE my_s3_stage
  URL = 's3://my-bucket/incoming/'
  STORAGE_INTEGRATION = my_s3_integration;   -- use storage integration, not raw keys

-- Snowpipe: event-driven continuous loading
CREATE PIPE orders_pipe AUTO_INGEST = TRUE AS
  COPY INTO raw.orders
  FROM @my_s3_stage/orders/
  FILE_FORMAT = (TYPE = 'JSON', STRIP_OUTER_ARRAY = TRUE);

-- Snowpipe monitors the S3 bucket via SQS notifications and loads new files
-- within minutes of arrival. Cost is per-file (not per-warehouse-hour).

-- Check Snowpipe status
SELECT SYSTEM$PIPE_STATUS('orders_pipe');

-- View Snowpipe load history
SELECT *
FROM TABLE(INFORMATION_SCHEMA.COPY_HISTORY(
  table_name => 'raw.orders',
  start_time => DATEADD(hours, -24, CURRENT_TIMESTAMP())
))
ORDER BY last_load_time DESC;
```

### 3.6 Streams and Tasks (CDC Pipeline)

```sql
-- Stream: captures change data (inserts, updates, deletes) on a table
CREATE STREAM orders_stream ON TABLE stg.orders_raw;

-- Task: scheduled job that consumes the stream
CREATE TASK process_orders_task
  WAREHOUSE = etl_wh
  SCHEDULE = '10 MINUTE'
WHEN
  SYSTEM$STREAM_HAS_DATA('orders_stream')   -- only run if new data exists
AS
  MERGE INTO mart.orders AS target
  USING (
    SELECT *, METADATA$ACTION, METADATA$ISUPDATE, METADATA$ROW_ID
    FROM orders_stream
  ) AS source
  ON target.order_id = source.order_id
  WHEN MATCHED AND source.METADATA$ACTION = 'INSERT' AND source.METADATA$ISUPDATE
    THEN UPDATE SET
      target.status = source.status,
      target.updated_at = source.updated_at
  WHEN NOT MATCHED AND source.METADATA$ACTION = 'INSERT'
    THEN INSERT (order_id, customer_id, amount, status, created_at)
    VALUES (source.order_id, source.customer_id, source.amount,
            source.status, source.created_at);

-- Resume the task (tasks are created in suspended state)
ALTER TASK process_orders_task RESUME;

-- Task DAG: chain tasks for multi-step pipelines
CREATE TASK step2_aggregate
  WAREHOUSE = etl_wh
  AFTER process_orders_task     -- runs after process_orders_task completes
AS
  INSERT INTO mart.daily_summary
  SELECT date_key, SUM(amount) AS total FROM mart.orders GROUP BY date_key;

ALTER TASK step2_aggregate RESUME;
```

### 3.7 Data Sharing

```sql
-- Snowflake Data Sharing: share data with other Snowflake accounts
-- without copying data — the consumer reads from the producer's storage.

-- Producer side: create a share
CREATE SHARE analytics_share;
GRANT USAGE ON DATABASE analytics_db TO SHARE analytics_share;
GRANT USAGE ON SCHEMA analytics_db.mart TO SHARE analytics_share;
GRANT SELECT ON TABLE analytics_db.mart.fact_sales TO SHARE analytics_share;

-- Add consumer account
ALTER SHARE analytics_share ADD ACCOUNTS = 'consumer_org.consumer_account';

-- Consumer side: create a database from the share
CREATE DATABASE shared_analytics FROM SHARE producer_org.producer_account.analytics_share;
SELECT * FROM shared_analytics.mart.fact_sales WHERE date_key = 20240115;
-- No data copied — reads directly from producer's storage
-- Consumer sees data updates in near-real-time
```

### 3.8 Dynamic Tables

```sql
-- Dynamic tables: declarative pipeline nodes with automatic refresh
-- (replaces manual streams + tasks for many ETL patterns)

CREATE DYNAMIC TABLE mart.customer_summary
  TARGET_LAG = '1 hour'            -- max acceptable lag from source
  WAREHOUSE = etl_wh
AS
SELECT
  customer_key,
  COUNT(*)               AS total_orders,
  SUM(net_revenue)       AS lifetime_value,
  MAX(date_key)          AS last_order_date,
  AVG(net_revenue)       AS avg_order_value
FROM mart.fact_sales
GROUP BY customer_key;

-- Snowflake automatically refreshes this table to maintain the target lag.
-- No manual scheduling needed.
```

---

## 4. Amazon Redshift

Redshift is AWS's data warehouse. It offers both provisioned clusters (fixed-capacity MPP
nodes) and Redshift Serverless (auto-scaling, pay-per-use). Its architecture is MPP with
a leader node that compiles and distributes queries to compute nodes.

### 4.1 Architecture

```
┌──────────────────────────────────────────────────────┐
│                    Redshift                          │
├──────────────────────────────────────────────────────┤
│  ┌────────────────┐                                  │
│  │  Leader Node   │  Query compilation, distribution,│
│  │                │  result aggregation              │
│  └───────┬────────┘                                  │
│          │                                           │
│  ┌───────┼───────┐                                   │
│  │       │       │                                   │
│  ▼       ▼       ▼                                   │
│ ┌────┐ ┌────┐ ┌────┐                                │
│ │ CN1│ │ CN2│ │ CN3│  Compute nodes (slices)         │
│ │    │ │    │ │    │  Each node has local SSD cache   │
│ └────┘ └────┘ └────┘  + access to S3 (managed storage)│
│                                                      │
│  Managed storage (RA3 nodes):                        │
│  Data stored in S3, cached on local SSD              │
│  Scales compute and storage independently            │
└──────────────────────────────────────────────────────┘
```

### 4.2 Node Types

```
┌──────────────┬──────────────┬──────────────┬──────────────────────┐
│ Node type    │ Storage      │ Compute      │ Use case             │
├──────────────┼──────────────┼──────────────┼──────────────────────┤
│ RA3.xlplus   │ Managed (S3) │ 4 vCPU       │ Small-medium         │
│ RA3.4xlarge  │ Managed (S3) │ 12 vCPU      │ Medium-large         │
│ RA3.16xlarge │ Managed (S3) │ 48 vCPU      │ Large, high perf     │
│ DC2.large    │ Local SSD    │ 2 vCPU       │ < 1 TB, fast local   │
│ DC2.8xlarge  │ Local SSD    │ 32 vCPU      │ < 10 TB, fast local  │
│ Serverless   │ Managed      │ Auto-scale   │ Variable workloads   │
└──────────────┴──────────────┴──────────────┴──────────────────────┘

Recommendation: use RA3 for new provisioned clusters (separates compute/storage).
Use Serverless for variable or unpredictable workloads.
```

### 4.3 Distribution Styles and Sort Keys

```sql
-- DISTRIBUTION STYLE: controls how rows are distributed across compute nodes
-- Critical for JOIN performance — co-located data avoids network shuffles.

-- DISTKEY: distribute by a column (rows with the same value go to the same node)
-- Use when a column is frequently used in JOINs
CREATE TABLE fact_sales (
  date_key      INT,
  customer_key  INT,
  product_key   INT,
  net_revenue   NUMERIC(12,2)
)
DISTKEY(customer_key)          -- rows with same customer_key are co-located
SORTKEY(date_key);             -- physically ordered by date for zone-map pruning

-- DISTSTYLE ALL: replicate the entire table on every node
-- Use for small dimension tables that are JOINed with many fact tables
CREATE TABLE dim_product (
  product_key   INT,
  product_name  VARCHAR(200),
  category      VARCHAR(100)
)
DISTSTYLE ALL                  -- every node has a complete copy
SORTKEY(product_key);

-- DISTSTYLE EVEN: round-robin distribution (default)
-- Use when no column is a good distribution key
CREATE TABLE staging_events (
  event_id      BIGINT,
  event_data    VARCHAR(MAX)
)
DISTSTYLE EVEN;

-- DISTSTYLE AUTO: let Redshift choose (recommended for most tables)
CREATE TABLE fact_clicks (
  date_key      INT,
  user_key      INT,
  page_url      VARCHAR(500)
)
DISTSTYLE AUTO;

-- Compound sort key (default): effective for queries that filter from left to right
CREATE TABLE fact_sales (...)
  COMPOUND SORTKEY(date_key, customer_key, product_key);
-- Effective for: WHERE date_key = ... AND customer_key = ...
-- Not effective for: WHERE product_key = ... (skips first sort column)

-- Interleaved sort key: effective for queries filtering on any column in the key
CREATE TABLE fact_sales (...)
  INTERLEAVED SORTKEY(date_key, customer_key, product_key);
-- Effective for: WHERE product_key = ... (does not require date_key filter)
-- Trade-off: VACUUM is much slower for interleaved sort keys
```

### 4.4 Redshift Spectrum

```sql
-- Spectrum: query data directly in S3 without loading it into Redshift

-- Create external schema (linked to AWS Glue Data Catalog)
CREATE EXTERNAL SCHEMA s3_data
FROM DATA CATALOG
DATABASE 'my_glue_db'
IAM_ROLE 'arn:aws:iam::123456789012:role/redshift-spectrum-role'
REGION 'us-east-1';

-- Query S3 data as if it were a Redshift table
SELECT
  s.customer_id,
  SUM(s.amount) AS s3_revenue
FROM s3_data.raw_events s
WHERE s.event_date = '2024-01-15'
GROUP BY s.customer_id;

-- Join Redshift table with S3 data (hot data in Redshift, cold data in S3)
SELECT
  r.customer_name,
  SUM(r.net_revenue)    AS recent_revenue,    -- from Redshift (last 90 days)
  SUM(s.amount)         AS historical_revenue  -- from S3 (older data)
FROM fact_sales r
JOIN s3_data.archived_sales s ON s.customer_id = r.customer_id
WHERE r.date_key >= 20240101
GROUP BY r.customer_name;
```

### 4.5 Redshift AQUA

AQUA (Advanced Query Accelerator) is a hardware-accelerated cache layer between compute
nodes and managed storage. It pushes down predicate evaluation and aggregation to custom
FPGA-based hardware near the storage, reducing data movement.

```sql
-- AQUA is enabled automatically for RA3 nodes.
-- No SQL changes needed. Queries that benefit from AQUA:
-- - Full table scans with simple predicates (WHERE status = 'completed')
-- - Aggregations (SUM, COUNT, AVG) on large tables
-- - LIKE pattern matching

-- Check AQUA acceleration
SELECT
  query,
  elapsed,
  label
FROM stl_query
WHERE label LIKE '%aqua%'
ORDER BY starttime DESC
LIMIT 10;
```

### 4.6 Maintenance Operations

```sql
-- ANALYZE: update table statistics for the query planner
ANALYZE fact_sales;
ANALYZE PREDICATE COLUMNS fact_sales;  -- only analyse columns used in predicates

-- VACUUM: reclaim space after DELETEs and re-sort data
VACUUM SORT ONLY fact_sales;     -- re-sort only (no space reclaim)
VACUUM DELETE ONLY fact_sales;   -- reclaim space only (no re-sort)
VACUUM FULL fact_sales;          -- both re-sort and reclaim space
VACUUM REINDEX fact_sales;       -- rebuild interleaved sort key indexes

-- Automatic maintenance (enabled by default for RA3 / Serverless)
-- Redshift runs ANALYZE and VACUUM automatically in the background.
-- Check maintenance status:
SELECT *
FROM svv_table_info
WHERE "table" = 'fact_sales';
```

---

## 5. Databricks (Lakehouse)

Databricks is not a traditional data warehouse — it is a lakehouse platform that combines
data lake storage (Delta Lake on S3/ADLS/GCS) with a high-performance SQL engine
(Photon) and a unified governance layer (Unity Catalog).

### 5.1 Architecture

```
┌──────────────────────────────────────────────────────────┐
│                      Databricks                          │
├──────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────┐  │
│  │              Unity Catalog                         │  │
│  │  Governance, access control, lineage, data sharing │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ SQL Warehouse│  │ Spark Cluster│  │ ML Runtime   │   │
│  │ (Photon)     │  │ (notebooks)  │  │ (MLflow)     │   │
│  │ BI queries   │  │ ETL / ELT    │  │ Training     │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │              Delta Lake (storage)                  │  │
│  │  ACID transactions, time travel, Z-order           │  │
│  │  On S3 / ADLS / GCS (Parquet + transaction log)    │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 5.2 SQL Warehouses (Serverless)

```sql
-- Databricks SQL Warehouses are serverless compute endpoints for BI queries
-- Photon is the native C++ vectorised engine (much faster than Spark SQL)

-- Create tables in Unity Catalog
CREATE CATALOG analytics;
CREATE SCHEMA analytics.production;

CREATE TABLE analytics.production.fact_sales (
  date_key      INT,
  customer_key  INT,
  product_key   INT,
  net_revenue   DECIMAL(12, 2)
)
USING DELTA
PARTITIONED BY (date_key)
TBLPROPERTIES (
  'delta.autoOptimize.optimizeWrite' = 'true',
  'delta.autoOptimize.autoCompact' = 'true'
);

-- Liquid Clustering (replaces PARTITION BY + Z-ORDER in newer Delta Lake)
CREATE TABLE analytics.production.fact_events
USING DELTA
CLUSTER BY (event_date, user_id)     -- adaptive clustering, no fixed partitions
AS SELECT * FROM staging.raw_events;
```

### 5.3 Unity Catalog

```sql
-- Unity Catalog: centralised governance across Databricks workspaces

-- Grant access (3-level namespace: catalog.schema.table)
GRANT USAGE ON CATALOG analytics TO `data_analysts`;
GRANT USAGE ON SCHEMA analytics.production TO `data_analysts`;
GRANT SELECT ON TABLE analytics.production.fact_sales TO `data_analysts`;

-- Row-level security
CREATE FUNCTION analytics.production.region_filter(region STRING)
RETURN CASE
  WHEN IS_ACCOUNT_GROUP_MEMBER('EMEA_team') AND region = 'EMEA' THEN TRUE
  WHEN IS_ACCOUNT_GROUP_MEMBER('NA_team') AND region = 'NA' THEN TRUE
  WHEN IS_ACCOUNT_GROUP_MEMBER('admin') THEN TRUE
  ELSE FALSE
END;

ALTER TABLE analytics.production.fact_sales
SET ROW FILTER analytics.production.region_filter ON (region);

-- Column masking
CREATE FUNCTION analytics.production.mask_email(email STRING)
RETURN CASE
  WHEN IS_ACCOUNT_GROUP_MEMBER('admin') THEN email
  ELSE CONCAT(LEFT(email, 2), '***@', SPLIT(email, '@')[1])
END;

ALTER TABLE analytics.production.dim_customer
ALTER COLUMN email SET MASK analytics.production.mask_email;

-- Data lineage: tracked automatically
-- View in Unity Catalog UI or query via REST API
```

---

## 6. Comparison Matrix

```
┌──────────────────────┬──────────────┬───────────────┬──────────────┬──────────────┐
│ Dimension            │ BigQuery     │ Snowflake     │ Redshift     │ Databricks   │
├──────────────────────┼──────────────┼───────────────┼──────────────┼──────────────┤
│ Pricing model        │ Per-byte or  │ Per-compute-  │ Per-node-hour│ Per-DBU      │
│                      │ per-slot     │ second + store│ or serverless│ (credit hour)│
│ Serverless           │ Fully        │ Fully         │ Optional     │ SQL WH only  │
│ Cloud support        │ GCP only     │ AWS/GCP/Azure │ AWS only     │ AWS/GCP/Azure│
│ SQL dialect          │ Standard SQL │ ANSI SQL      │ PostgreSQL   │ Spark SQL    │
│ Semi-structured      │ ARRAY/STRUCT │ VARIANT       │ SUPER type   │ Delta STRUCT │
│ Time travel          │ 7 days       │ 1-90 days     │ Snapshots    │ Delta versions│
│ Zero-copy clone      │ Table copy   │ Yes (instant) │ No           │ Delta CLONE  │
│ Multi-cloud          │ No           │ Yes           │ No           │ Yes          │
│ Integrated ML        │ BigQuery ML  │ Snowpark ML   │ Redshift ML  │ MLflow       │
│ Data sharing         │ Analytics Hub│ Shares        │ Lake sharing │ Delta Sharing│
│ Concurrency          │ Excellent    │ Excellent     │ Cluster-bound│ Warehouse    │
│ Cost predictability  │ Hard (demand)│ Good (credits)│ Good (nodes) │ Moderate     │
│ Open format          │ Capacitor    │ Proprietary   │ Proprietary  │ Delta/Parquet│
│ Governance           │ IAM + BQ     │ RBAC + tags   │ IAM + RBAC   │ Unity Catalog│
│ Best for             │ GCP-native,  │ Multi-cloud,  │ AWS-native,  │ ML + ETL +   │
│                      │ ad-hoc       │ data sharing  │ cost control │ SQL unified  │
└──────────────────────┴──────────────┴───────────────┴──────────────┴──────────────┘
```

---

## 7. Cost Optimisation

### 7.1 Universal Strategies

```sql
-- 1. Partition all time-series tables and enforce partition filters
-- BigQuery:
ALTER TABLE `analytics.fact_sales`
SET OPTIONS (require_partition_filter = TRUE);

-- 2. Select only needed columns (biggest cost lever in BigQuery)
-- BAD:  SELECT * FROM fact_sales WHERE ...
-- GOOD: SELECT customer_key, SUM(net_revenue) FROM fact_sales WHERE ...

-- 3. Materialise frequently recomputed results
-- All platforms support materialized views or dynamic tables.

-- 4. Set auto-suspend / auto-pause for compute
-- Snowflake:
ALTER WAREHOUSE bi_wh SET AUTO_SUSPEND = 60;    -- suspend after 60s
-- Redshift Serverless: RPU auto-pause after idle period
-- BigQuery: serverless, no action needed
```

### 7.2 Snowflake Cost Monitoring

```sql
-- Credit usage by warehouse (last 30 days)
SELECT
  warehouse_name,
  SUM(credits_used_compute) AS compute_credits,
  SUM(credits_used_cloud_services) AS service_credits,
  COUNT(DISTINCT DATE(start_time)) AS active_days,
  SUM(credits_used_compute) / NULLIF(COUNT(DISTINCT DATE(start_time)), 0)
    AS credits_per_day
FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
WHERE start_time > DATEADD(days, -30, CURRENT_TIMESTAMP())
GROUP BY warehouse_name
ORDER BY compute_credits DESC;

-- Resource monitors: set spending limits per warehouse
CREATE RESOURCE MONITOR marketing_monitor
  CREDIT_QUOTA = 100               -- 100 credits per period
  FREQUENCY = MONTHLY
  START_TIMESTAMP = IMMEDIATELY
  TRIGGERS
    ON 75 PERCENT DO NOTIFY
    ON 90 PERCENT DO SUSPEND
    ON 100 PERCENT DO SUSPEND_IMMEDIATE;

ALTER WAREHOUSE marketing_wh SET RESOURCE_MONITOR = marketing_monitor;

-- Query cost attribution per user
SELECT
  user_name,
  warehouse_name,
  COUNT(*) AS query_count,
  ROUND(SUM(credits_used_cloud_services), 4) AS total_credits,
  ROUND(SUM(bytes_scanned) / POW(1024, 3), 2) AS gb_scanned
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE start_time > DATEADD(days, -30, CURRENT_TIMESTAMP())
GROUP BY user_name, warehouse_name
ORDER BY total_credits DESC;
```

### 7.3 BigQuery Cost Monitoring

```sql
-- Top expensive queries (last 7 days)
SELECT
  user_email,
  ROUND(SUM(total_bytes_billed) / POW(1024, 4), 4) AS tb_billed,
  ROUND(SUM(total_bytes_billed) / POW(1024, 4) * 6.25, 2) AS estimated_cost_usd,
  COUNT(*) AS query_count
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE start_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND job_type = 'QUERY'
GROUP BY user_email
ORDER BY tb_billed DESC;

-- BigQuery custom cost controls
-- Set maximum bytes billed per query (prevents runaway queries)
-- In the query job config:
-- job_config.maximum_bytes_billed = 10 * 1024 ** 3  # 10 GB max

-- Slot reservations (flat-rate): buy a fixed number of slots for predictable cost
-- Use INFORMATION_SCHEMA.RESERVATIONS to monitor slot utilisation
```

### 7.4 Redshift Cost Monitoring

```sql
-- Query cost by user (Redshift)
SELECT
  u.usename,
  COUNT(q.query) AS query_count,
  SUM(q.elapsed / 1000000) AS total_elapsed_s,
  SUM(q.aborted) AS aborted_count
FROM stl_query q
JOIN pg_user u ON q.userid = u.usesysid
WHERE q.starttime > DATEADD(day, -7, GETDATE())
GROUP BY u.usename
ORDER BY total_elapsed_s DESC;

-- Identify queries that should be optimised
SELECT
  query,
  ROUND(elapsed::FLOAT / 1000000, 2) AS elapsed_s,
  ROUND(bytes_scanned::FLOAT / POW(1024, 3), 3) AS gb_scanned,
  label
FROM stl_query
WHERE starttime > DATEADD(day, -1, GETDATE())
  AND elapsed > 60000000  -- queries longer than 60 seconds
ORDER BY elapsed DESC
LIMIT 20;
```

---

## 8. Data Sharing and Governance

### 8.1 Cross-Platform Data Sharing

| Platform    | Sharing mechanism       | Cross-cloud | Cross-platform       |
|-------------|-------------------------|-------------|----------------------|
| Snowflake   | Secure Data Sharing     | Yes (replicate) | Snowflake accounts only |
| BigQuery    | Analytics Hub           | No          | BigQuery subscribers |
| Redshift    | Data Sharing (RA3)      | No          | Redshift clusters    |
| Databricks  | Delta Sharing           | Yes         | Open protocol (any reader) |

Delta Sharing (Databricks) is the only open-protocol sharing mechanism. Any tool that can
read Parquet files can consume Delta Shares — no Databricks account required for the
consumer.

### 8.2 Row-Level Security

```sql
-- Snowflake: row access policy
CREATE ROW ACCESS POLICY region_policy AS (region VARCHAR)
RETURNS BOOLEAN ->
  CASE
    WHEN CURRENT_ROLE() = 'ADMIN' THEN TRUE
    WHEN CURRENT_ROLE() = 'EMEA_ANALYST' AND region = 'EMEA' THEN TRUE
    WHEN CURRENT_ROLE() = 'NA_ANALYST' AND region = 'NA' THEN TRUE
    ELSE FALSE
  END;

ALTER TABLE fact_sales ADD ROW ACCESS POLICY region_policy ON (region);

-- BigQuery: authorised views (simpler approach)
CREATE VIEW `analytics.fact_sales_emea` AS
SELECT * FROM `analytics.fact_sales`
WHERE region = 'EMEA';

GRANT `roles/bigquery.dataViewer` ON TABLE `analytics.fact_sales_emea`
TO 'user:emea_analyst@company.com';
```

### 8.3 Column-Level Security

```sql
-- Snowflake: dynamic data masking
CREATE MASKING POLICY email_mask AS (val STRING)
RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() IN ('ADMIN', 'DATA_ENGINEER') THEN val
    ELSE CONCAT(LEFT(val, 2), '***@', SPLIT_PART(val, '@', 2))
  END;

ALTER TABLE dim_customer MODIFY COLUMN email SET MASKING POLICY email_mask;

-- BigQuery: column-level security via policy tags
-- Create a policy tag taxonomy in Data Catalog, tag sensitive columns,
-- then grant/deny access to the tag.
```

---

## 9. Migration Strategies

### 9.1 Choosing a Target Platform

| Scenario                              | Recommended platform         |
|---------------------------------------|------------------------------|
| Already on AWS, predictable workload  | Redshift (provisioned)       |
| Already on GCP, ad-hoc heavy          | BigQuery (on-demand)         |
| Multi-cloud or cloud-agnostic needs   | Snowflake                    |
| Unified ML + ETL + SQL on open format | Databricks                   |
| Small team, variable workload         | BigQuery or Snowflake        |
| Enterprise with data sharing needs    | Snowflake                    |

### 9.2 Migration Steps

1. **Assessment**: inventory tables, queries, ETL pipelines, users, and permissions.
2. **Schema translation**: convert DDL to the target dialect (distribution keys, partition
   strategies, data types).
3. **Data migration**: bulk export to object storage (Parquet), then load to target.
4. **Query translation**: adapt SQL (function names, date handling, JSON syntax).
5. **Pipeline migration**: rebuild ETL/ELT in target (dbt models are largely portable).
6. **Validation**: row counts, checksums, query result comparison between old and new.
7. **Cutover**: dual-run period, then switch BI tools to the new DW.

```sql
-- Example: translate Redshift → Snowflake
-- Redshift:   GETDATE()         → Snowflake: CURRENT_TIMESTAMP()
-- Redshift:   DATEADD(day, ...)  → Snowflake: DATEADD('day', ...)
-- Redshift:   CONVERT(VARCHAR, x)→ Snowflake: TO_VARCHAR(x)
-- Redshift:   NVL(a, b)          → Snowflake: NVL(a, b)  (same)
-- Redshift:   DISTKEY / SORTKEY   → Snowflake: CLUSTER BY (different concept)
```

---

## 10. Troubleshooting

### BigQuery: High Cost Queries

```sql
-- Find queries scanning more than 1 TB
SELECT
  user_email,
  query,
  ROUND(total_bytes_processed / POW(1024, 4), 3) AS tb_scanned
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE total_bytes_processed > POW(1024, 4)   -- > 1 TB
  AND start_time > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
ORDER BY total_bytes_processed DESC;

-- Common causes:
-- 1. SELECT * on large tables
-- 2. Missing partition filter (require_partition_filter not set)
-- 3. Cross-join or cartesian product (accidental)
-- 4. Querying a view that scans the entire underlying table
```

### Snowflake: Warehouse Queue Wait

```sql
-- Queries waiting in queue (warehouse too small or too many concurrent queries)
SELECT
  query_id,
  query_text,
  warehouse_name,
  queued_overload_time / 1000 AS queue_wait_s,
  total_elapsed_time / 1000 AS total_elapsed_s
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY(
  date_range_start => DATEADD('hours', -4, CURRENT_TIMESTAMP())
))
WHERE queued_overload_time > 0
ORDER BY queued_overload_time DESC;

-- Solution: increase warehouse size, enable multi-cluster, or separate workloads
```

### Redshift: High Disk Usage / VACUUM Needed

```sql
-- Check tables needing VACUUM
SELECT
  "table" AS table_name,
  unsorted AS pct_unsorted,
  empty AS pct_empty_blocks,
  tbl_rows
FROM svv_table_info
WHERE "schema" = 'public'
  AND (unsorted > 5 OR empty > 5)
ORDER BY tbl_rows DESC;

-- Run VACUUM on affected tables
VACUUM FULL fact_sales;
ANALYZE fact_sales;
```

---

## 11. Frequently Asked Questions

**Q: Which cloud DW should I choose?**

If you are already invested in a single cloud provider and want simplicity, choose the
native DW (BigQuery for GCP, Redshift for AWS). If you need multi-cloud or plan to migrate
between clouds, choose Snowflake. If you need unified ML + ETL + SQL on open formats,
choose Databricks. For small teams with variable workloads, BigQuery (on-demand) or
Snowflake (auto-suspend XS warehouse) offer the lowest cost floor.

**Q: How do I control BigQuery costs on on-demand pricing?**

1. Set `maximum_bytes_billed` on query jobs. 2. Use `require_partition_filter` on all
time-series tables. 3. Avoid `SELECT *`. 4. Monitor with INFORMATION_SCHEMA.JOBS. 5.
Consider switching to flat-rate (slot reservations) if monthly spend exceeds predictable
threshold.

**Q: What is the cheapest option for a small team (< 1 TB, < 10 users)?**

BigQuery on-demand (you pay only for queries you run; storage is ~$0.02/GB/month).
Snowflake XS warehouse with aggressive auto-suspend (1 credit/hour when running). Both
have a generous free tier or trial credits.

**Q: Can I use dbt with all four platforms?**

Yes. dbt-core supports adapters for BigQuery, Snowflake, Redshift, and Databricks. The SQL
models are mostly portable (with adapter-specific macros for platform differences).

**Q: How does Snowflake's credit pricing compare to BigQuery's per-byte pricing?**

They are fundamentally different models. Snowflake charges for compute time (credits per
second, based on warehouse size). BigQuery charges for data scanned (per TB). A query that
scans little data is cheap on BigQuery but costs the same in Snowflake (compute time). A
long-running query on little data is cheap on BigQuery but expensive on Snowflake. The
right model depends on your query patterns.

**Q: What about ClickHouse and DuckDB?**

ClickHouse is a high-performance open-source columnar OLAP database, excellent for
real-time analytics on insert-heavy workloads. DuckDB is an in-process columnar analytical
database (the "SQLite of analytics"), excellent for single-machine workloads up to ~100 GB.
Neither is a cloud DW in the traditional sense, but both are increasingly used as
components in modern data stacks.

---

## 12. Exercises

### Exercise 1: Platform Selection

For each scenario, recommend a cloud DW platform and justify your choice:

1. A startup on GCP with 500 GB of data, 3 analysts, unpredictable query patterns.
2. A Fortune 500 on AWS with 50 TB, strict cost governance, and 200 concurrent BI users.
3. A company operating on both AWS and Azure, needing to share data with 10 external
   partners who use different cloud providers.
4. A data science team that needs to run SQL queries, train ML models, and orchestrate
   Spark ETL jobs on a single platform.

### Exercise 2: Snowflake Warehouse Sizing

You have these workload requirements:
- ETL pipeline: runs every hour, takes 15 minutes on a MEDIUM warehouse.
- BI dashboards: 50 users, 200 queries/hour, average 5 seconds each on SMALL.
- Ad-hoc data science: 2 users, intermittent queries, some running 10+ minutes on LARGE.

Design the warehouse configuration (sizes, auto-suspend, multi-cluster settings) and
estimate the daily credit cost. (1 credit = 1 hour of XS compute.)

### Exercise 3: BigQuery Cost Estimation

You have a 10 TB fact table partitioned by date (365 partitions, ~27 GB each) and clustered
by customer_id. Estimate the bytes scanned and cost for each query (on-demand pricing,
$6.25/TB):

1. `SELECT * FROM fact_sales WHERE date = '2024-06-15'`
2. `SELECT customer_id, SUM(revenue) FROM fact_sales WHERE date BETWEEN '2024-01-01' AND
   '2024-12-31' GROUP BY customer_id`
3. `SELECT COUNT(*) FROM fact_sales`

### Exercise 4: Redshift Distribution Strategy

Design the distribution style and sort keys for these tables:
- `fact_orders` (500M rows, frequently joined with `dim_customer` on `customer_key`)
- `dim_customer` (5M rows, used in many JOINs)
- `dim_product` (10K rows, used in many JOINs)
- `staging_events` (100M rows, loaded daily, no common join key)

### Exercise 5: Migration Planning

You are migrating from an on-premises PostgreSQL-based DW (20 TB, 150 tables, 50 dbt
models, 30 Airflow DAGs) to a cloud DW. Outline a migration plan including:
1. Platform selection criteria
2. Schema translation challenges
3. Data migration approach
4. Query compatibility issues
5. Risk mitigation (dual-run period, validation strategy)
