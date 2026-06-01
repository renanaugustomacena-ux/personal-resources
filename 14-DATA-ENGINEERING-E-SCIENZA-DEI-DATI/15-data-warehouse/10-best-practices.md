# Data Warehouse Best Practices

This document distils lessons from decades of data warehouse implementations — both
successes and failures. Every principle here is the answer to a mistake that cost someone
money, credibility, or months of re-engineering. The practices span modelling, operations,
data quality, testing, cost governance, access control, and documentation.

---

## Table of Contents

1. Medallion Architecture (Bronze / Silver / Gold)
2. Data Quality Gates
3. SLA Management
4. Schema Evolution
5. Documentation and Metadata
6. Testing Data Pipelines
7. Cost Governance
8. Access Control and Security
9. Design Best Practices
10. Operational Best Practices
11. Anti-Patterns
12. Production Checklist
13. Troubleshooting
14. Frequently Asked Questions
15. Exercises

---

## 1. Medallion Architecture (Bronze / Silver / Gold)

The medallion architecture is the standard layering pattern for modern data warehouses and
lakehouses. Data flows through three quality tiers, each with a clear purpose and contract.

### 1.1 Bronze Layer (Raw)

```
Purpose:  Immutable landing zone for source data. Append-only. No transformations.
Contract: Data is an exact copy of the source at the time of extraction.
Format:   JSON, CSV, Parquet, Avro — whatever the source emits.
Retention: Long (years) — this is the audit trail.
```

```sql
-- Bronze table: raw orders from the OLTP source
CREATE TABLE bronze.orders_raw (
  _loaded_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- load metadata
  _source_file  VARCHAR(500),                          -- provenance
  _source_system VARCHAR(50) DEFAULT 'oltp_postgres',
  payload       VARIANT  -- Snowflake: store raw JSON
);

-- Or structured bronze (columnar, but no transformations)
CREATE TABLE bronze.orders_raw (
  _loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  order_id        VARCHAR(50),      -- as-is from source (might be string)
  customer_id     VARCHAR(50),
  order_date      VARCHAR(50),      -- as-is (might be '2024-01-15' or '01/15/2024')
  total_amount    VARCHAR(50),      -- as-is (might have currency symbols)
  status          VARCHAR(50),
  raw_json        VARCHAR(MAX)      -- optional: full JSON payload for debugging
);

-- Bronze loading pattern: append-only, idempotent
INSERT INTO bronze.orders_raw (_source_file, payload)
SELECT
  metadata$filename,
  PARSE_JSON($1)
FROM @my_s3_stage/orders/2024-01-15/;
```

**Bronze rules:**
- Never transform data. If the source sends `"total": "$49.99"`, store `"$49.99"`.
- Always add load metadata (`_loaded_at`, `_source_file`, `_source_system`).
- Never delete rows (append-only). If data is corrected at the source, append the
  correction — do not overwrite.
- Partition by load date or source date for efficient pruning.

### 1.2 Silver Layer (Cleaned / Conformed)

```
Purpose:  Cleaned, typed, deduplicated, and conformed data. Business keys resolved.
Contract: Data conforms to declared schemas with correct types. Nulls are handled.
          Duplicates are removed. Cross-source entities are unified.
Format:   Typed tables or views (dbt models).
Retention: Medium (months to years).
```

```sql
-- Silver model: cleaned orders (typically a dbt model)
-- File: models/silver/stg_orders.sql
CREATE TABLE silver.stg_orders AS
SELECT
  CAST(order_id AS INT)                             AS order_id,
  CAST(customer_id AS INT)                          AS customer_id,
  TO_DATE(order_date, 'YYYY-MM-DD')                 AS order_date,
  TO_NUMBER(REPLACE(REPLACE(total_amount, '$', ''), ',', ''), 10, 2)
                                                    AS total_amount,
  UPPER(TRIM(status))                               AS status,
  -- Deduplication: keep the latest loaded version of each order
  ROW_NUMBER() OVER (
    PARTITION BY order_id ORDER BY _loaded_at DESC
  )                                                 AS _row_num,
  _loaded_at,
  _source_system
FROM bronze.orders_raw
QUALIFY _row_num = 1;   -- deduplicate

-- Silver layer handles:
-- 1. Type casting (string → int, date, decimal)
-- 2. Null handling (COALESCE, default values)
-- 3. Deduplication (ROW_NUMBER with business key)
-- 4. Standardisation (UPPER, TRIM, date formats)
-- 5. Cross-source unification (matching customer IDs across systems)
```

### 1.3 Gold Layer (Business-Ready)

```
Purpose:  Analytical models optimised for consumption. Star schemas, aggregates,
          wide denormalised tables for specific BI tools or ML features.
Contract: Data is accurate, documented, tested, and ready for business users.
Format:   Fact and dimension tables. Materialised views. Aggregation tables.
Retention: As long as business needs require.
```

```sql
-- Gold model: fact_sales star schema (dbt model)
-- File: models/gold/fact_sales.sql
CREATE TABLE gold.fact_sales AS
SELECT
  dd.date_key,
  dc.customer_key,
  dp.product_key,
  dch.channel_key,
  o.order_id,
  oli.line_number,
  oli.quantity,
  oli.unit_price,
  oli.discount_amount,
  oli.quantity * oli.unit_price - oli.discount_amount AS net_revenue,
  oli.quantity * dp.unit_cost                          AS cost_amount
FROM silver.stg_order_line_items oli
  JOIN silver.stg_orders     o   ON oli.order_id    = o.order_id
  JOIN gold.dim_date         dd  ON o.order_date    = dd.full_date
  JOIN gold.dim_customer     dc  ON o.customer_id   = dc.customer_id AND dc.is_current
  JOIN gold.dim_product      dp  ON oli.product_id  = dp.product_id
  JOIN gold.dim_channel      dch ON o.channel        = dch.channel_name;

-- Gold layer also includes pre-aggregated tables for dashboards
CREATE TABLE gold.agg_daily_revenue AS
SELECT
  date_key,
  product_key,
  channel_key,
  SUM(net_revenue) AS daily_revenue,
  SUM(quantity)    AS daily_units,
  COUNT(*)         AS transaction_count
FROM gold.fact_sales
GROUP BY date_key, product_key, channel_key;
```

### 1.4 Layer Dependency Rules

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    Bronze    │────►│    Silver    │────►│     Gold     │
│   (raw)      │     │  (cleaned)   │     │ (business)   │
└──────────────┘     └──────────────┘     └──────────────┘

Rules:
1. Gold depends on Silver only (never reads Bronze directly)
2. Silver depends on Bronze only
3. Bronze depends on external sources only
4. No lateral dependencies (Gold table A should not depend on Gold table B)
5. No reverse dependencies (Bronze never reads Silver)
```

---

## 2. Data Quality Gates

Data quality is not optional — it is a pipeline stage. Quality gates are automated checks
that run after each transformation step and block downstream processing if quality falls
below thresholds.

### 2.1 Quality Dimensions

| Dimension       | Definition                                     | Example check                        |
|-----------------|------------------------------------------------|--------------------------------------|
| Completeness    | No unexpected NULLs                            | `NOT NULL` on required fields        |
| Uniqueness      | No duplicate records                           | `UNIQUE` on business keys            |
| Timeliness      | Data arrives within expected window            | Freshness check (max date vs today)  |
| Validity        | Values fall within expected ranges/formats     | Amount > 0, status IN valid set      |
| Consistency     | Cross-table relationships hold                 | FK integrity, row count ratios       |
| Accuracy        | Data matches real-world truth                  | Reconciliation against source system |

### 2.2 dbt Tests

```yaml
# models/gold/schema.yml
version: 2

models:
  - name: fact_sales
    description: "Transaction-grain fact table for sales"
    columns:
      - name: date_key
        tests:
          - not_null
          - relationships:
              to: ref('dim_date')
              field: date_key
      - name: customer_key
        tests:
          - not_null
          - relationships:
              to: ref('dim_customer')
              field: customer_key
      - name: net_revenue
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 500000
              # Flag any single transaction over $500K as suspicious
      - name: order_id
        tests:
          - not_null
          - unique
    tests:
      - dbt_utils.recency:
          datepart: day
          field: _loaded_at
          interval: 1
          # Data must not be older than 1 day

  - name: dim_customer
    columns:
      - name: customer_key
        tests: [not_null, unique]
      - name: customer_id
        tests: [not_null]
      - name: email
        tests:
          - dbt_expectations.expect_column_values_to_match_regex:
              regex: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
              # Validate email format
```

### 2.3 Row Count Reconciliation

```sql
-- Automated reconciliation: compare source count vs warehouse count daily
-- Run this as a post-load quality gate

WITH source_counts AS (
  SELECT
    'orders' AS table_name,
    COUNT(*) AS source_count
  FROM bronze.orders_raw
  WHERE _loaded_at::DATE = CURRENT_DATE
),
warehouse_counts AS (
  SELECT
    'orders' AS table_name,
    COUNT(*) AS warehouse_count
  FROM gold.fact_sales
  WHERE date_key = TO_CHAR(CURRENT_DATE, 'YYYYMMDD')::INT
)
SELECT
  s.table_name,
  s.source_count,
  w.warehouse_count,
  ABS(s.source_count - w.warehouse_count) AS difference,
  ROUND(ABS(s.source_count - w.warehouse_count) * 100.0
    / NULLIF(s.source_count, 0), 2) AS diff_pct,
  CASE
    WHEN ABS(s.source_count - w.warehouse_count) * 100.0
         / NULLIF(s.source_count, 0) > 5 THEN 'CRITICAL'
    WHEN ABS(s.source_count - w.warehouse_count) * 100.0
         / NULLIF(s.source_count, 0) > 1 THEN 'WARNING'
    ELSE 'OK'
  END AS status
FROM source_counts s
  JOIN warehouse_counts w ON s.table_name = w.table_name;

-- If diff_pct > 5%: block downstream models and alert the data team.
-- If diff_pct > 1%: warn but allow processing to continue.
```

### 2.4 Anomaly Detection

```sql
-- Volume anomaly detection: flag days with unusually high or low row counts
WITH daily_volumes AS (
  SELECT
    date_key,
    COUNT(*) AS row_count
  FROM gold.fact_sales
  GROUP BY date_key
),
stats AS (
  SELECT
    AVG(row_count) AS avg_volume,
    STDDEV(row_count) AS stddev_volume
  FROM daily_volumes
  WHERE date_key >= TO_CHAR(CURRENT_DATE - INTERVAL '90 days', 'YYYYMMDD')::INT
)
SELECT
  dv.date_key,
  dv.row_count,
  ROUND(s.avg_volume) AS avg_volume,
  ROUND((dv.row_count - s.avg_volume) / NULLIF(s.stddev_volume, 0), 2) AS z_score,
  CASE
    WHEN ABS((dv.row_count - s.avg_volume) / NULLIF(s.stddev_volume, 0)) > 3
      THEN 'ANOMALY'
    WHEN ABS((dv.row_count - s.avg_volume) / NULLIF(s.stddev_volume, 0)) > 2
      THEN 'WARNING'
    ELSE 'NORMAL'
  END AS status
FROM daily_volumes dv
  CROSS JOIN stats s
ORDER BY dv.date_key DESC
LIMIT 30;
```

### 2.5 Great Expectations Integration

```python
import great_expectations as gx

context = gx.get_context()

# Define expectations for the fact_sales table
suite = context.add_expectation_suite("fact_sales_suite")

# Completeness
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToNotBeNull(column="date_key")
)
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToNotBeNull(column="customer_key")
)

# Validity
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToBeBetween(
        column="net_revenue", min_value=0, max_value=500000
    )
)

# Uniqueness
suite.add_expectation(
    gx.expectations.ExpectCompoundColumnsToBeUnique(
        column_list=["date_key", "customer_key", "product_key", "order_id", "line_number"]
    )
)

# Timeliness
suite.add_expectation(
    gx.expectations.ExpectColumnMaxToBeBetween(
        column="date_key",
        min_value=int((datetime.now() - timedelta(days=1)).strftime('%Y%m%d')),
        max_value=int(datetime.now().strftime('%Y%m%d'))
    )
)

# Run validation
checkpoint = context.add_or_update_checkpoint(
    name="fact_sales_checkpoint",
    validations=[{"batch_request": batch_request, "expectation_suite_name": "fact_sales_suite"}]
)
result = checkpoint.run()

# Block pipeline if validation fails
if not result.success:
    raise RuntimeError("Data quality check failed. Pipeline halted.")
```

---

## 3. SLA Management

### 3.1 Defining SLAs

Every data product (table, dashboard, API endpoint) should have an explicit SLA covering:

| SLA dimension    | Definition                                     | Example                       |
|------------------|-------------------------------------------------|-------------------------------|
| Freshness        | Maximum acceptable data latency                | "Data no older than 1 hour"   |
| Availability     | Uptime of the data product                     | "99.9% availability"          |
| Completeness     | Minimum acceptable data coverage               | "> 99% of source records"     |
| Accuracy         | Maximum acceptable error rate                  | "< 0.1% reconciliation error" |
| Response time    | Maximum query latency for BI dashboards        | "P95 < 5 seconds"             |

### 3.2 Freshness Monitoring

```sql
-- Freshness dashboard: how current is each table?
CREATE VIEW monitoring.data_freshness AS
SELECT
  'fact_sales'          AS table_name,
  MAX(date_key)         AS latest_date_key,
  DATEDIFF('day',
    TO_DATE(MAX(date_key)::VARCHAR, 'YYYYMMDD'),
    CURRENT_DATE)       AS days_behind,
  CASE
    WHEN DATEDIFF('day',
      TO_DATE(MAX(date_key)::VARCHAR, 'YYYYMMDD'),
      CURRENT_DATE) = 0 THEN 'GREEN'
    WHEN DATEDIFF('day',
      TO_DATE(MAX(date_key)::VARCHAR, 'YYYYMMDD'),
      CURRENT_DATE) <= 1 THEN 'YELLOW'
    ELSE 'RED'
  END AS freshness_status
FROM gold.fact_sales

UNION ALL

SELECT
  'dim_customer'        AS table_name,
  MAX(effective_from)   AS latest_update,
  DATEDIFF('day', MAX(effective_from), CURRENT_DATE) AS days_behind,
  CASE
    WHEN DATEDIFF('day', MAX(effective_from), CURRENT_DATE) <= 1 THEN 'GREEN'
    ELSE 'YELLOW'
  END AS freshness_status
FROM gold.dim_customer;

-- Alert on SLA breach
-- This query should be scheduled (Airflow, dbt Cloud, Snowflake Tasks)
-- and wired to a notification system (Slack, PagerDuty, email).
SELECT *
FROM monitoring.data_freshness
WHERE freshness_status = 'RED';
```

### 3.3 SLA Tracking Table

```sql
-- Track SLA compliance over time for reporting to stakeholders
CREATE TABLE monitoring.sla_history (
  check_timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  table_name        VARCHAR(100),
  sla_dimension     VARCHAR(50),      -- 'freshness', 'completeness', 'accuracy'
  expected_value    VARCHAR(100),
  actual_value      VARCHAR(100),
  status            VARCHAR(10),      -- 'PASS', 'WARN', 'FAIL'
  details           VARCHAR(500)
);

-- Insert SLA check results daily
INSERT INTO monitoring.sla_history (table_name, sla_dimension, expected_value,
  actual_value, status, details)
SELECT
  'fact_sales',
  'freshness',
  '0 days behind',
  days_behind || ' days behind',
  freshness_status,
  'Latest date_key: ' || latest_date_key
FROM monitoring.data_freshness
WHERE table_name = 'fact_sales';
```

---

## 4. Schema Evolution

### 4.1 Additive Changes (Safe)

Adding new columns or new tables is always safe. Existing queries and downstream consumers
are unaffected.

```sql
-- Add a new column to a dimension (safe — existing queries unaffected)
ALTER TABLE gold.dim_customer ADD COLUMN loyalty_tier VARCHAR(20);

-- Add a new column to a fact table (safe — existing queries unaffected)
ALTER TABLE gold.fact_sales ADD COLUMN is_gift_purchase BOOLEAN DEFAULT FALSE;

-- dbt: use the --full-refresh flag to rebuild models that incorporate the new column
-- dbt run --select fact_sales --full-refresh
```

### 4.2 Breaking Changes (Dangerous)

Renaming columns, changing data types, or dropping columns can break downstream consumers.

```sql
-- BAD: rename a column (breaks all queries referencing the old name)
ALTER TABLE gold.dim_customer RENAME COLUMN city TO customer_city;

-- BETTER: add new column, populate, deprecate old, then drop after migration window
ALTER TABLE gold.dim_customer ADD COLUMN customer_city VARCHAR(100);
UPDATE gold.dim_customer SET customer_city = city;

-- Communicate to downstream consumers:
-- "Column 'city' is deprecated. Use 'customer_city'. Old column will be removed on 2024-03-01."

-- After migration window:
ALTER TABLE gold.dim_customer DROP COLUMN city;
```

### 4.3 Schema Evolution with dbt

```yaml
# dbt_project.yml: control how schema changes are applied
models:
  my_project:
    gold:
      +materialized: table
      +on_schema_change: 'append_new_columns'
      # Options:
      # 'ignore'             — do not modify the target table schema
      # 'append_new_columns' — add new columns, do not remove old ones (safest)
      # 'sync_all_columns'   — add new, remove dropped (dangerous)
      # 'fail'               — error if schema differs (strictest)
```

### 4.4 Schema Registry Pattern

For teams with many producers and consumers, maintain a schema registry that versions and
validates schemas before they reach the warehouse.

```python
# Schema registry pattern (simplified)
# Store expected schemas in version control and validate on load.

EXPECTED_SCHEMA = {
    "order_id":     {"type": "INTEGER", "nullable": False},
    "customer_id":  {"type": "VARCHAR", "nullable": False},
    "total_amount": {"type": "NUMERIC", "nullable": False, "min": 0},
    "order_date":   {"type": "DATE",    "nullable": False},
    "status":       {"type": "VARCHAR", "nullable": False,
                     "allowed": ["completed", "pending", "cancelled", "returned"]},
}

def validate_schema(df, expected):
    """Validate a DataFrame against the expected schema before loading."""
    errors = []
    for col, rules in expected.items():
        if col not in df.columns:
            errors.append(f"Missing column: {col}")
            continue
        if not rules["nullable"] and df[col].isnull().any():
            errors.append(f"NULL values in non-nullable column: {col}")
        if "min" in rules and (df[col] < rules["min"]).any():
            errors.append(f"Values below minimum in {col}")
        if "allowed" in rules:
            invalid = set(df[col].dropna().unique()) - set(rules["allowed"])
            if invalid:
                errors.append(f"Invalid values in {col}: {invalid}")
    if errors:
        raise ValueError(f"Schema validation failed:\n" + "\n".join(errors))
```

---

## 5. Documentation and Metadata

### 5.1 What to Document

| Artefact                 | Content                                                   |
|--------------------------|-----------------------------------------------------------|
| Table description        | Business purpose, grain, update frequency, owner          |
| Column descriptions      | Business meaning, units, allowed values, source mapping   |
| Data lineage             | Source system → bronze → silver → gold transformation chain|
| Business glossary        | Canonical definitions ("revenue" = net of discounts + tax)|
| SLA documentation        | Freshness, completeness, availability targets              |
| Change log               | Schema changes, business logic changes, with dates        |

### 5.2 dbt Documentation

```yaml
# models/gold/schema.yml
version: 2

models:
  - name: fact_sales
    description: |
      Transaction-grain fact table for sales. One row per order line item.
      Grain: order_id × line_number.
      Updated: hourly via incremental load.
      Owner: data-engineering@company.com
      SLA: data no older than 2 hours.
    columns:
      - name: date_key
        description: "Surrogate key referencing dim_date. Format: YYYYMMDD."
      - name: customer_key
        description: |
          Surrogate key referencing dim_customer. SCD2: references the customer
          version that was active at the time of the sale.
      - name: net_revenue
        description: |
          Revenue net of discounts. Calculated as: quantity × unit_price - discount_amount.
          Currency: USD. Additive measure — safe to SUM across all dimensions.
      - name: order_id
        description: "Degenerate dimension. Original order ID from the OLTP system."
```

### 5.3 Data Lineage

```
Source: PostgreSQL (orders table)
  │
  ▼
Bronze: bronze.orders_raw (append-only, raw JSON)
  │
  ▼
Silver: silver.stg_orders (typed, deduplicated, validated)
  │
  ├──► Gold: gold.dim_customer (SCD2, conformed)
  ├──► Gold: gold.dim_product (SCD1, conformed)
  └──► Gold: gold.fact_sales (star schema, incremental)
         │
         ├──► Gold: gold.agg_daily_revenue (daily aggregate)
         └──► Dashboard: "Executive Sales Dashboard" (Looker)
```

dbt generates lineage graphs automatically. Snowflake and Databricks (Unity Catalog) also
track lineage natively.

---

## 6. Testing Data Pipelines

### 6.1 Test Pyramid for Data

```
                    ┌────────────────┐
                    │  Reconciliation │   ← Compare DW totals against source
                    │  (end-to-end)  │      Run daily, alert on >1% drift
                    ├────────────────┤
                    │  Integration    │   ← Test cross-table relationships
                    │  tests          │      FK integrity, dimension lookups
                    ├────────────────┤
                    │  Unit tests     │   ← Test individual transformations
                    │  (dbt tests)    │      NOT NULL, unique, range, regex
                    └────────────────┘
```

### 6.2 dbt Unit Tests

```yaml
# dbt test: ensure no orphan fact rows
# (every customer_key in fact_sales exists in dim_customer)

tests:
  - name: fact_sales_customer_fk
    model: fact_sales
    tests:
      - relationships:
          to: ref('dim_customer')
          field: customer_key

  # Custom test: revenue should never be negative
  - name: fact_sales_positive_revenue
    model: fact_sales
    tests:
      - dbt_utils.expression_is_true:
          expression: "net_revenue >= 0"

  # Custom test: no future dates
  - name: fact_sales_no_future_dates
    model: fact_sales
    tests:
      - dbt_utils.expression_is_true:
          expression: "date_key <= CAST(TO_CHAR(CURRENT_DATE, 'YYYYMMDD') AS INT)"
```

### 6.3 dbt Singular Tests

```sql
-- tests/assert_revenue_reconciliation.sql
-- This custom test compares total revenue in the DW against the source system.
-- If the difference exceeds 1%, the test fails.

WITH source_total AS (
  SELECT SUM(total_amount) AS source_revenue
  FROM {{ source('oltp', 'orders') }}
  WHERE order_date = CURRENT_DATE - INTERVAL '1 day'
),
dw_total AS (
  SELECT SUM(net_revenue) AS dw_revenue
  FROM {{ ref('fact_sales') }}
  WHERE date_key = CAST(TO_CHAR(CURRENT_DATE - INTERVAL '1 day', 'YYYYMMDD') AS INT)
)
SELECT
  s.source_revenue,
  d.dw_revenue,
  ABS(s.source_revenue - d.dw_revenue) / NULLIF(s.source_revenue, 0) AS diff_pct
FROM source_total s
  CROSS JOIN dw_total d
WHERE ABS(s.source_revenue - d.dw_revenue) / NULLIF(s.source_revenue, 0) > 0.01;
-- Returns rows only if the difference exceeds 1% (test failure)
```

### 6.4 Pipeline Testing Strategy

| Test type              | When it runs         | What it checks                        | Blocks pipeline? |
|------------------------|----------------------|---------------------------------------|-------------------|
| Schema validation      | Before loading       | Column names, types, nullability       | Yes              |
| Row count check        | After Bronze load    | Source count matches Bronze count      | Yes (>5% diff)   |
| dbt tests (unit)       | After Silver/Gold    | NOT NULL, unique, range, FK            | Yes              |
| Reconciliation         | After Gold load      | DW totals match source totals          | Yes (>1% diff)   |
| Freshness check        | Scheduled (hourly)   | Data is not stale beyond SLA           | Alert only        |
| Anomaly detection      | Scheduled (daily)    | Volume, distribution anomalies         | Alert only        |

---

## 7. Cost Governance

### 7.1 Cost Attribution

```sql
-- Tag every query with its team, pipeline, and purpose
-- Snowflake:
ALTER SESSION SET QUERY_TAG = 'team=marketing;pipeline=campaign_report;env=prod';

-- BigQuery: use labels on jobs
-- Python SDK:
-- job_config.labels = {"team": "marketing", "pipeline": "campaign_report"}

-- Aggregate cost by team (Snowflake)
SELECT
  SPLIT_PART(query_tag, ';', 1) AS team_tag,
  SUM(credits_used_cloud_services) AS total_credits,
  COUNT(*) AS query_count
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE query_tag IS NOT NULL
  AND start_time > DATEADD(days, -30, CURRENT_TIMESTAMP())
GROUP BY team_tag
ORDER BY total_credits DESC;
```

### 7.2 Budget Alerts and Guardrails

```sql
-- Snowflake: resource monitors
CREATE RESOURCE MONITOR company_monthly
  CREDIT_QUOTA = 5000          -- 5000 credits/month budget
  FREQUENCY = MONTHLY
  START_TIMESTAMP = IMMEDIATELY
  TRIGGERS
    ON 50 PERCENT DO NOTIFY     -- alert at 50%
    ON 75 PERCENT DO NOTIFY     -- alert at 75%
    ON 90 PERCENT DO SUSPEND    -- suspend non-critical warehouses at 90%
    ON 100 PERCENT DO SUSPEND_IMMEDIATE;  -- hard stop at 100%

-- BigQuery: custom quota per project
-- Set in the GCP console: project-level maximum bytes billed per day

-- Redshift: WLM (Workload Management) to limit query resources
-- Configure max concurrency, query timeout, and memory allocation per queue.
```

### 7.3 Cost Optimisation Checklist

| Strategy                            | Savings estimate | Effort    |
|-------------------------------------|------------------|-----------|
| Select only needed columns          | 30-80% (BigQuery)| Low       |
| Partition time-series tables        | 50-99%           | Low       |
| Auto-suspend idle warehouses        | 20-50%           | Low       |
| Materialise repeated queries        | 40-80%           | Medium    |
| Right-size warehouses               | 20-40%           | Medium    |
| Archive cold data to cheaper storage| 30-60%           | Medium    |
| Optimise table clustering           | 10-30%           | Medium    |
| Migrate from on-demand to flat-rate | Variable         | Low       |
| Eliminate unused tables and models  | 10-20%           | Low       |
| Review and cancel long-running jobs | 5-15%            | Low       |

### 7.4 Storage Cost Management

```sql
-- Identify large tables that may benefit from archival or compression
SELECT
  TABLE_CATALOG,
  TABLE_SCHEMA,
  TABLE_NAME,
  ROW_COUNT,
  ROUND(BYTES / POW(1024, 3), 2) AS size_gb,
  LAST_ALTERED
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA NOT IN ('INFORMATION_SCHEMA', 'ACCOUNT_USAGE')
ORDER BY BYTES DESC
LIMIT 20;

-- Identify tables not queried in the last 90 days (candidates for archival)
SELECT
  t.TABLE_SCHEMA,
  t.TABLE_NAME,
  t.ROW_COUNT,
  ROUND(t.BYTES / POW(1024, 3), 2) AS size_gb,
  MAX(ah.last_accessed) AS last_queried
FROM INFORMATION_SCHEMA.TABLES t
  LEFT JOIN SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY ah
    ON ah.base_objects_accessed[0]:objectName = t.TABLE_NAME
WHERE t.TABLE_SCHEMA = 'GOLD'
GROUP BY 1, 2, 3, 4
HAVING MAX(ah.last_accessed) < DATEADD(days, -90, CURRENT_TIMESTAMP())
   OR MAX(ah.last_accessed) IS NULL
ORDER BY size_gb DESC;
```

---

## 8. Access Control and Security

### 8.1 Role-Based Access Control (RBAC)

```sql
-- Snowflake: role hierarchy
CREATE ROLE data_reader;
CREATE ROLE data_analyst;
CREATE ROLE data_engineer;
CREATE ROLE data_admin;

-- Hierarchy: data_admin > data_engineer > data_analyst > data_reader
GRANT ROLE data_reader  TO ROLE data_analyst;
GRANT ROLE data_analyst TO ROLE data_engineer;
GRANT ROLE data_engineer TO ROLE data_admin;

-- Permissions
GRANT USAGE ON DATABASE analytics TO ROLE data_reader;
GRANT USAGE ON SCHEMA analytics.gold TO ROLE data_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics.gold TO ROLE data_reader;

GRANT USAGE ON SCHEMA analytics.silver TO ROLE data_analyst;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics.silver TO ROLE data_analyst;

GRANT ALL ON SCHEMA analytics.silver TO ROLE data_engineer;
GRANT ALL ON SCHEMA analytics.gold TO ROLE data_engineer;

-- Assign roles to users
GRANT ROLE data_analyst TO USER analyst_alice;
GRANT ROLE data_engineer TO USER engineer_bob;
```

### 8.2 PII Protection

```sql
-- Identify PII columns and apply masking policies
-- PII columns: email, phone, address, SSN, credit card

-- Snowflake: tag PII columns
ALTER TABLE gold.dim_customer MODIFY COLUMN email
  SET TAG pii_classification = 'email';
ALTER TABLE gold.dim_customer MODIFY COLUMN phone
  SET TAG pii_classification = 'phone';

-- Apply masking policy
CREATE MASKING POLICY mask_pii_email AS (val STRING)
RETURNS STRING ->
  CASE
    WHEN CURRENT_ROLE() IN ('DATA_ADMIN', 'DATA_ENGINEER') THEN val
    ELSE REGEXP_REPLACE(val, '(^.{2})(.*)(@.*)', '\\1***\\3')
  END;

ALTER TABLE gold.dim_customer MODIFY COLUMN email
  SET MASKING POLICY mask_pii_email;

-- BigQuery: column-level security via Data Catalog policy tags
-- Tag columns as 'PII', then restrict access to the tag.
-- Only users with the 'Fine-Grained Reader' role on the tag can see unmasked values.
```

### 8.3 Audit Logging

```sql
-- Snowflake: query history for audit
SELECT
  user_name,
  role_name,
  query_text,
  start_time,
  end_time,
  execution_status,
  rows_produced,
  bytes_scanned
FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE start_time > DATEADD(days, -7, CURRENT_TIMESTAMP())
  AND query_text ILIKE '%dim_customer%'    -- who accessed customer data?
ORDER BY start_time DESC;

-- BigQuery: audit log via Cloud Logging
-- Filter: resource.type="bigquery_resource" AND
--         protoPayload.methodName="jobservice.jobcompleted"
```

---

## 9. Design Best Practices

### 9.1 Declare Granularity Before Building

Every fact table must have a declared, immutable grain. Adding measures incompatible with
the grain is impossible to fix without rebuilding.

```sql
-- GOOD: explicitly documented grain
-- fact_sales: one row per order line item (order_id × line_number)
-- fact_daily_inventory: one row per product per warehouse per day
-- fact_order_fulfilment: one row per order lifecycle
```

### 9.2 Follow Dimensional Modelling

Star schema over normalised schema. Denormalise dimensions. Use surrogate keys. Implement
SCD2 for historically significant attributes.

### 9.3 Keep Business Logic in SQL Models (dbt)

Business logic (e.g., "an order is completed when status = 'completed' AND payment_status =
'paid'") belongs in version-controlled SQL models, not in Python ETL scripts, Airflow DAGs,
or stored procedures.

```sql
-- dbt model: models/gold/fact_completed_orders.sql
SELECT
  *,
  status = 'completed' AND payment_status = 'paid' AS is_truly_completed
FROM {{ ref('stg_orders') }}
```

### 9.4 Never Use Real Dates as Foreign Keys

```sql
-- BAD: date column as FK in fact table
CREATE TABLE fact_sales (sale_date DATE, ...);
-- Cannot join with dim_date (no shared key), no fiscal calendar attributes.

-- GOOD: integer surrogate key
CREATE TABLE fact_sales (date_key INT, ...);
-- date_key = YYYYMMDD → joins with dim_date which has all calendar attributes.
```

### 9.5 Always Have an Unknown Dimension Member

```sql
-- Every dimension table should have a row with key = -1 for 'Unknown'
INSERT INTO gold.dim_customer (customer_key, customer_id, first_name, last_name,
  is_current, effective_from)
VALUES (-1, 'UNKNOWN', 'Unknown', 'Customer', TRUE, '1900-01-01');

-- ETL: map unresolvable FKs to -1 instead of dropping the fact row.
```

---

## 10. Operational Best Practices

### 10.1 Incremental Loading by Default

```sql
-- Pattern: high-water mark incremental load
-- Load only new or changed records since the last successful run.

CREATE OR REPLACE PROCEDURE load_fact_sales_incremental()
LANGUAGE SQL
AS
$$
  DECLARE
    v_watermark TIMESTAMP;
  BEGIN
    SELECT COALESCE(MAX(_loaded_at), '2000-01-01'::TIMESTAMP)
    INTO :v_watermark
    FROM gold.fact_sales;

    INSERT INTO gold.fact_sales
    SELECT *
    FROM silver.stg_orders
    WHERE _loaded_at > :v_watermark;

    RETURN 'Loaded records after ' || :v_watermark;
  END;
$$;

-- Full refresh only when:
-- 1. Business logic change requires recalculation of all historical data
-- 2. Bug fix that affected historical records
-- 3. Initial load (table does not exist yet)
```

### 10.2 Idempotent Loads

Every load operation should produce the same result whether run once or multiple times. Use
MERGE (upsert) or DELETE + INSERT patterns.

```sql
-- Idempotent load using MERGE
MERGE INTO gold.fact_sales AS target
USING silver.stg_orders_today AS source
ON target.order_id = source.order_id AND target.line_number = source.line_number
WHEN MATCHED THEN
  UPDATE SET
    target.net_revenue = source.net_revenue,
    target.status = source.status
WHEN NOT MATCHED THEN
  INSERT (date_key, customer_key, product_key, order_id, line_number, net_revenue)
  VALUES (source.date_key, source.customer_key, source.product_key,
          source.order_id, source.line_number, source.net_revenue);

-- Running this MERGE twice with the same source data produces the same result.
```

### 10.3 Separate ETL and Query Compute

Use different compute resources for ETL and BI to prevent interference.

```sql
-- Snowflake: separate warehouses
CREATE WAREHOUSE etl_wh  WAREHOUSE_SIZE='LARGE' AUTO_SUSPEND=300;
CREATE WAREHOUSE bi_wh   WAREHOUSE_SIZE='SMALL' AUTO_SUSPEND=60;

-- ETL jobs use etl_wh; BI queries use bi_wh.
-- A heavy ETL load does not slow down dashboard queries.
```

### 10.4 Implement Retry and Alerting

```python
# Airflow task with retry and alert (conceptual pattern)
from airflow.decorators import task
from airflow.operators.email import EmailOperator

@task(retries=3, retry_delay=timedelta(minutes=5))
def load_fact_sales():
    """Incremental load with retry."""
    # ... load logic ...

alert = EmailOperator(
    task_id='alert_on_failure',
    to='data-team@company.com',
    subject='ALERT: fact_sales load failed',
    trigger_rule='one_failed'
)

load_fact_sales() >> alert
```

---

## 11. Anti-Patterns

### Anti-Pattern 1: Business Logic in the ETL Pipeline

```python
# BAD: Python script that encodes business rules
if row['status'] == 'completed' and row['payment'] == 'received':
    row['is_completed'] = True
# This logic is invisible to SQL users, not testable with dbt, not version-controlled.

# GOOD: business logic in a dbt model (SQL, version-controlled, testable)
# SELECT ..., status = 'completed' AND payment_status = 'paid' AS is_completed
```

### Anti-Pattern 2: Monolithic ETL

One giant DAG that loads everything in sequence. If one table fails, everything stops.

**Fix**: modular pipelines with independent DAGs per business process. Use dbt's DAG to
manage dependencies within the transformation layer.

### Anti-Pattern 3: No Unknown Dimension Member

Results in silently dropped fact rows when INNER JOIN fails to find a match.

### Anti-Pattern 4: Mixed Granularity in a Fact Table

Transaction-level and daily-aggregate rows in the same table make every measure ambiguous.

### Anti-Pattern 5: No Testing

"It looks right in the dashboard" is not a test. Implement automated quality gates at
every layer.

### Anti-Pattern 6: Over-Engineering

Building a Data Vault with Hub/Link/Satellite for a 3-table warehouse is over-engineering.
Match the complexity of your architecture to the complexity of your data landscape.

### Anti-Pattern 7: Copy-Paste Dimensions

Two teams independently build `dim_customer` with different definitions. Cross-process
queries produce nonsensical results.

**Fix**: conformed dimensions, shared dbt models, automated conformance tests.

---

## 12. Production Checklist

### Modelling

- [ ] Granularity declared and documented for every fact table
- [ ] Star schema (not over-normalised snowflake or 3NF)
- [ ] SCD2 for all historically significant dimension attributes
- [ ] Unknown member (-1) for every dimension
- [ ] Business logic in dbt models, not in ETL scripts
- [ ] Conformed dimensions shared across business processes
- [ ] Surrogate keys (integer) on all dimensions and fact FKs

### Performance

- [ ] Fact tables partitioned by date
- [ ] Clustering / sort keys on frequently filtered columns
- [ ] Materialised views for frequently computed aggregations
- [ ] Statistics up to date (ANALYZE or automatic)
- [ ] Query slow log monitored with alerts
- [ ] No `SELECT *` in production queries

### Quality

- [ ] dbt tests on all fact and dimension tables (NOT NULL, unique, FK, range)
- [ ] Daily reconciliation against source system
- [ ] Volume anomaly detection (z-score alerts)
- [ ] Freshness monitoring with SLA alerts
- [ ] Schema validation on incoming data

### Governance

- [ ] Owner documented for every table (schema.yml or catalog)
- [ ] Data lineage tracked (dbt docs or catalog tool)
- [ ] PII columns identified, tagged, and masked
- [ ] Retention policy defined and enforced (partition expiration)
- [ ] Access reviewed quarterly (least privilege, RBAC)
- [ ] Audit logging enabled for sensitive tables

### Cost

- [ ] Cost attribution by team / pipeline (query tags)
- [ ] Resource monitors / budget alerts configured
- [ ] Auto-suspend on all compute resources
- [ ] Unused tables identified and archived
- [ ] Storage tiering for cold data (cheaper storage class)

### Documentation

- [ ] Table and column descriptions in dbt schema.yml
- [ ] Business glossary for key terms (revenue, customer, churn)
- [ ] SLA documented per data product
- [ ] Change log maintained for schema and logic changes
- [ ] Runbook for incident response (load failures, data quality issues)

---

## 13. Troubleshooting

### Problem: Dashboard shows stale data

**Diagnosis**: check freshness monitoring view. Identify which layer is behind.

```sql
-- Check which layer is stale
SELECT 'bronze' AS layer, MAX(_loaded_at) AS latest FROM bronze.orders_raw
UNION ALL
SELECT 'silver', MAX(_loaded_at) FROM silver.stg_orders
UNION ALL
SELECT 'gold', MAX(_loaded_at) FROM gold.fact_sales;

-- If bronze is fresh but silver is stale → silver transformation is failing
-- If bronze is stale → source extraction is failing
```

### Problem: Revenue in DW does not match finance system

**Diagnosis**: reconcile at each layer to find where the discrepancy is introduced.

```sql
-- Reconciliation waterfall
SELECT
  'source'  AS layer, SUM(total_amount) AS revenue FROM source_system.orders WHERE date = '2024-01-15'
UNION ALL
SELECT 'bronze', SUM(CAST(total_amount AS NUMERIC)) FROM bronze.orders_raw WHERE order_date = '2024-01-15'
UNION ALL
SELECT 'silver', SUM(total_amount) FROM silver.stg_orders WHERE order_date = '2024-01-15'
UNION ALL
SELECT 'gold',   SUM(net_revenue) FROM gold.fact_sales WHERE date_key = 20240115;

-- The layer where revenue first diverges is where the bug lives.
```

### Problem: ETL job takes too long

**Diagnosis**: identify the bottleneck.

```sql
-- dbt: check model run times
SELECT model_name, execution_time_seconds
FROM dbt_artifacts.model_executions
WHERE run_started_at > DATEADD(days, -7, CURRENT_TIMESTAMP())
ORDER BY execution_time_seconds DESC
LIMIT 10;

-- Common fixes:
-- 1. Switch from full refresh to incremental
-- 2. Reduce the number of joins (pre-aggregate, materialise)
-- 3. Increase warehouse size for the ETL job
-- 4. Parallel model execution (dbt threads)
```

---

## 14. Frequently Asked Questions

**Q: Should I use dbt for my data warehouse?**

For any team with more than one person building transformations, yes. dbt provides version
control, testing, documentation, dependency management, and CI/CD for SQL models. The
overhead of adopting dbt is far less than the cost of debugging unversioned stored
procedures.

**Q: How many layers should my medallion architecture have?**

Three (bronze, silver, gold) is the standard. Some teams add a fourth "platinum" or
"semantic" layer for published data products with stricter governance. Avoid adding layers
without clear purpose — each layer adds maintenance cost.

**Q: How do I handle data corrections from the source system?**

Two approaches:
1. **Soft correction**: the source sends a corrected record. Your incremental load picks
   it up and the MERGE updates the existing row. Simple, but does not preserve the
   original incorrect value.
2. **Hard correction**: load the correction as a new version (SCD2 for dimensions, insert
   with corrected flag for facts). Preserves audit history.

**Q: How often should I run ANALYZE / refresh statistics?**

After every significant data load (ETL batch). In cloud DWs (BigQuery, Snowflake), this is
automatic. In PostgreSQL/Redshift, schedule ANALYZE after each batch load.

**Q: What is the right balance between materialisation and on-the-fly computation?**

Materialise when: the query is run frequently (>10x/day), the computation is expensive
(scans >1 TB), and the result changes infrequently. Compute on-the-fly when: the query is
ad-hoc, the result changes frequently, or storage cost exceeds compute cost.

**Q: How do I handle time zones in a global DW?**

Store all timestamps in UTC. Add timezone-specific columns in `dim_date` or a separate
`dim_time` table for local-time analysis. Never store timestamps in local time without
specifying the timezone.

---

## 15. Exercises

### Exercise 1: Medallion Architecture Design

Design the bronze, silver, and gold layers for an e-commerce company that has:
- Orders from a PostgreSQL OLTP database
- Product catalogue from a REST API
- Customer reviews from a MongoDB collection
- Web analytics events from Google Analytics (BigQuery export)

For each layer, specify: table names, key transformations, data quality checks, and refresh
strategy.

### Exercise 2: Data Quality Gate Implementation

Write dbt tests (YAML) for a `fact_orders` table with these quality requirements:
1. `order_id` is unique and not null.
2. `net_revenue` is between $0 and $100,000.
3. `date_key` references `dim_date`.
4. Data is no older than 1 day.
5. `customer_key` is not the unknown member (-1) for more than 5% of rows.

### Exercise 3: Cost Governance Plan

You are the data platform lead for a company spending $15,000/month on Snowflake. The CFO
wants a 30% cost reduction. Design a cost governance plan that includes:
1. Cost attribution (query tagging strategy)
2. Budget alerts and guardrails
3. Warehouse sizing review
4. Unused table cleanup
5. Data retention policy

### Exercise 4: Access Control Matrix

Design an RBAC model for a data warehouse with these roles:
- Data Engineer (full access to all layers)
- Data Analyst (read access to silver and gold, no PII)
- BI Developer (read access to gold only)
- Executive (read access to specific gold aggregates only)
- External Partner (read access to a shared dataset, masked PII)

Write the SQL GRANT statements for Snowflake.

### Exercise 5: Incident Response

The finance team reports that yesterday's revenue in the executive dashboard is 20% lower
than expected. Write a step-by-step investigation plan that:
1. Identifies which layer the discrepancy originates from.
2. Checks for common root causes (late data, failed loads, schema changes).
3. Provides a remediation procedure.
4. Documents the incident for the post-mortem.
