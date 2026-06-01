# Data Warehouse: Fundamentals and Architecture

A data warehouse is a data management system purpose-built for analytical querying and
reporting, architecturally separated from the operational databases (OLTP) that serve
day-to-day transactions. The term was coined by Bill Inmon in the late 1980s. He defined a
data warehouse as "a subject-oriented, integrated, time-variant, non-volatile collection
of data in support of management's decision-making process." In the early 1990s, Ralph
Kimball proposed a complementary methodology centred on dimensional modelling. Both schools
of thought remain in active use and have deeply shaped modern data engineering.

The core problem a data warehouse solves is workload isolation. OLTP systems are optimised
for the latency of individual transactions — single-row INSERTs, UPDATEs, and point lookups.
Running an analytical query that scans millions of rows on a production OLTP database
degrades write performance, raises lock contention, and can bring the operational system to
its knees. The data warehouse moves the analytical workload to a separate system with a
schema, storage layout, and query engine designed specifically for scans and aggregations.

---

## Table of Contents

1. OLTP vs OLAP
2. Inmon vs Kimball Methodology
3. Dimensional Modelling
4. Star Schema
5. Snowflake Schema
6. Galaxy Schema (Fact Constellation)
7. Fact Tables — Types
8. Dimension Tables and Slowly Changing Dimensions (SCD Type 1-6)
9. Conformed Dimensions and the Enterprise Bus Matrix
10. Surrogate Keys vs Natural Keys
11. Degenerate Dimensions
12. Junk Dimensions and Mini-Dimensions
13. Modern Data Warehouse Architecture
14. ETL vs ELT
15. Common Anti-Patterns
16. Troubleshooting
17. Frequently Asked Questions
18. Exercises

---

## 1. OLTP vs OLAP: The Fundamental Contrast

```
┌───────────────────────────────────────────────────────────────────────────┐
│                         OLTP  vs  OLAP                                  │
├───────────────────┬──────────────────────┬────────────────────────────────┤
│ Characteristic    │ OLTP                 │ OLAP / Data Warehouse         │
├───────────────────┼──────────────────────┼────────────────────────────────┤
│ Purpose           │ Daily operations     │ Analysis & decision support   │
│ Data scope        │ Current state        │ Historical (years)            │
│ Typical query     │ Point lookup, update │ Full / partial table scan     │
│ Tables per query  │ 1–10                 │ Dozens to hundreds            │
│ Data volume       │ GB                   │ TB–PB                         │
│ Updates           │ Frequent (ms)        │ Batch / micro-batch           │
│ Users             │ Thousands (apps)     │ Tens–hundreds (analysts, BI)  │
│ Schema            │ Normalised (3NF)     │ Denormalised (star/snowflake) │
│ Optimised for     │ Write throughput     │ Read/scan throughput          │
│ Examples          │ PostgreSQL, MySQL    │ BigQuery, Snowflake, Redshift │
└───────────────────┴──────────────────────┴────────────────────────────────┘
```

**Key insight**: the same data lives in both systems, but in different shapes. The OLTP
schema is normalised to avoid update anomalies. The DW schema is denormalised to minimise
the number of joins an analytical query must perform.

---

## 2. Inmon vs Kimball Methodology

The two foundational approaches to building a data warehouse differ in scope, modelling
philosophy, and build sequence.

### 2.1 Inmon — Top-Down ("Corporate Information Factory")

Bill Inmon advocates building a single, enterprise-wide data warehouse in third normal form
(3NF). Subject-area data marts are then derived from this central repository.

```
Sources → ETL → Enterprise DW (3NF) → Data Marts (star schema) → BI
```

**Characteristics:**
- The enterprise DW is the single source of truth.
- Data is modelled in 3NF — normalised, entity-relationship-driven.
- Data marts are created per department (finance, marketing, ops) as star schemas derived
  from the 3NF warehouse.
- The approach requires heavy up-front modelling effort before any business user sees data.

**Advantages:**
- One integrated model; data consistency is architecturally enforced.
- Handles complex inter-subject-area queries well (e.g., "which marketing campaigns drove
  which product returns?").
- Schema changes in the central model propagate cleanly to all downstream marts.

**Disadvantages:**
- Long time-to-first-value (months to years before the first mart is queryable).
- Requires dedicated data modelling expertise up-front.
- Initial cost and organisational buy-in are high.

### 2.2 Kimball — Bottom-Up ("Dimensional Data Warehouse")

Ralph Kimball advocates building conformed dimensional models (star schemas) iteratively,
one business process at a time. The data warehouse is the union of all conformed star
schemas.

```
Sources → ETL → Star Schema Data Marts → Conformed DW (virtual/physical union)
```

**Characteristics:**
- Each business process (orders, shipments, returns) gets its own star schema.
- Dimensions are conformed across business processes (same `dim_customer` in orders and
  returns) so that queries can drill across.
- The "data warehouse" is the collection of all conformed star schemas, not a separate 3NF
  database.

**Advantages:**
- Fast time-to-first-value: deliver one star schema in weeks.
- Intuitive for business users — dimensions map directly to how they think about data.
- Incremental investment; each new star schema adds value without re-engineering the whole
  warehouse.

**Disadvantages:**
- Requires discipline in conforming dimensions; without it, the warehouse degrades into
  siloed data marts.
- Cross-process queries (spanning multiple fact tables) can be harder to model and optimise.

### 2.3 Comparison Matrix

```
┌──────────────────────┬─────────────────────┬─────────────────────────┐
│ Dimension            │ Inmon               │ Kimball                 │
├──────────────────────┼─────────────────────┼─────────────────────────┤
│ Schema model         │ 3NF (normalised)    │ Star schema             │
│ Build order          │ Top-down            │ Bottom-up               │
│ Central artefact     │ Enterprise DW       │ Conformed dimensions    │
│ Time to first value  │ Long (months)       │ Short (weeks)           │
│ Modelling skill req. │ Very high           │ High                    │
│ Maintenance cost     │ Front-loaded        │ Ongoing (conformance)   │
│ Best fit             │ Large enterprises   │ Mid-size, iterative     │
│ Modern alignment     │ Data vault hybrid   │ dbt, Kimball revival    │
└──────────────────────┴─────────────────────┴─────────────────────────┘
```

### 2.4 Modern Convergence

In practice, most modern data stacks blend both schools:

- **ELT + dbt** follows Kimball's iterative star-schema philosophy but uses an Inmon-like
  staging layer (raw → staging → mart).
- **Data Vault** (Dan Linstedt) is a third methodology that models the raw warehouse as
  Hubs, Links, and Satellites — closer to Inmon's normalised approach but designed for
  agile, incremental loading. Mart layers are then built as star schemas (Kimball).

---

## 3. Dimensional Modelling

Dimensional modelling organises data around two types of tables:

- **Fact tables** — contain the quantitative measures (metrics) of a business process.
  Each row represents an event or measurement at a declared grain.
- **Dimension tables** — contain the descriptive context of the measures (who, what, when,
  where, how). Each row represents an entity or attribute.

### 3.1 The Four-Step Design Process (Kimball)

1. **Select the business process** — e.g., "retail sales" or "order fulfilment."
2. **Declare the grain** — the level of detail each fact row represents. This is the single
   most important decision. Example grains: one row per order line item, one row per daily
   product inventory snapshot, one row per click event.
3. **Identify the dimensions** — what contextual attributes describe each fact row? Date,
   customer, product, store, promotion, channel.
4. **Identify the facts (measures)** — what numeric values are recorded? Quantity, unit
   price, discount amount, revenue, cost.

### 3.2 Measure Additivity

Measures fall into three categories based on how they behave under aggregation across
dimensions:

| Type             | Definition                                           | Example                         |
|------------------|------------------------------------------------------|---------------------------------|
| **Additive**     | Can be summed across ALL dimensions                  | Revenue, quantity, cost         |
| **Semi-additive** | Can be summed across SOME dimensions (not time)     | Account balance, inventory level|
| **Non-additive** | Cannot be meaningfully summed across any dimension   | Unit price, ratio, percentage   |

```sql
-- Additive measure: summing revenue across time makes sense
SELECT SUM(net_revenue) FROM fact_sales WHERE year = 2024;

-- Semi-additive measure: summing account_balance across time does NOT make sense
-- (you would double-count). Instead, use MAX, MIN, or AVG for the time dimension.
SELECT
  customer_key,
  AVG(account_balance) AS avg_balance  -- NOT SUM
FROM fact_account_snapshot
GROUP BY customer_key;

-- Non-additive measure: unit_price cannot be summed at all.
-- Use weighted average or bring it down from a dimension.
SELECT
  product_key,
  SUM(quantity * unit_price) / SUM(quantity) AS weighted_avg_price
FROM fact_sales
GROUP BY product_key;
```

---

## 4. Star Schema

The star schema is the most widely used DW schema. The fact table sits at the centre, with
foreign keys pointing outward to denormalised dimension tables — forming a star shape.

### 4.1 Complete Star Schema Example

```sql
-- ==========================================================================
-- Dimension: Date (present in virtually every data warehouse)
-- ==========================================================================
CREATE TABLE dim_date (
  date_key        INT PRIMARY KEY,        -- surrogate key: YYYYMMDD
  full_date       DATE NOT NULL,
  day_of_week     SMALLINT,               -- 1 = Monday, 7 = Sunday (ISO)
  day_name        VARCHAR(10),            -- 'Monday', 'Tuesday', ...
  day_of_month    SMALLINT,
  day_of_year     SMALLINT,
  week_of_year    SMALLINT,               -- ISO week number
  month_number    SMALLINT,
  month_name      VARCHAR(10),            -- 'January', 'February', ...
  quarter         SMALLINT,
  year            SMALLINT,
  is_weekend      BOOLEAN,
  is_holiday      BOOLEAN,
  holiday_name    VARCHAR(100),
  fiscal_year     SMALLINT,               -- may differ from calendar year
  fiscal_quarter  SMALLINT,
  is_last_day_of_month BOOLEAN
);

-- Populate dim_date once, typically 10–20 years ahead
INSERT INTO dim_date
SELECT
  TO_CHAR(d, 'YYYYMMDD')::INT                  AS date_key,
  d::DATE                                       AS full_date,
  EXTRACT(ISODOW FROM d)                        AS day_of_week,
  TO_CHAR(d, 'Day')                             AS day_name,
  EXTRACT(DAY FROM d)                           AS day_of_month,
  EXTRACT(DOY FROM d)                           AS day_of_year,
  EXTRACT(WEEK FROM d)                          AS week_of_year,
  EXTRACT(MONTH FROM d)                         AS month_number,
  TO_CHAR(d, 'Month')                           AS month_name,
  EXTRACT(QUARTER FROM d)                       AS quarter,
  EXTRACT(YEAR FROM d)                          AS year,
  EXTRACT(ISODOW FROM d) IN (6, 7)             AS is_weekend,
  FALSE                                         AS is_holiday,
  NULL                                          AS holiday_name,
  CASE WHEN EXTRACT(MONTH FROM d) >= 4
       THEN EXTRACT(YEAR FROM d)
       ELSE EXTRACT(YEAR FROM d) - 1
  END                                           AS fiscal_year,
  CASE WHEN EXTRACT(MONTH FROM d) >= 4
       THEN (EXTRACT(MONTH FROM d) - 4) / 3 + 1
       ELSE (EXTRACT(MONTH FROM d) + 8) / 3 + 1
  END                                           AS fiscal_quarter,
  d::DATE = (DATE_TRUNC('month', d) + INTERVAL '1 month - 1 day')::DATE
                                                AS is_last_day_of_month
FROM GENERATE_SERIES('2015-01-01', '2035-12-31', '1 day'::INTERVAL) d;


-- ==========================================================================
-- Dimension: Customer (with SCD2 tracking columns)
-- ==========================================================================
CREATE TABLE dim_customer (
  customer_key        INT PRIMARY KEY,      -- surrogate key
  customer_id         VARCHAR(20) NOT NULL,  -- natural / business key from OLTP
  first_name          VARCHAR(100),
  last_name           VARCHAR(100),
  email               VARCHAR(200),
  phone               VARCHAR(30),
  street_address      VARCHAR(300),
  city                VARCHAR(100),
  state_province      VARCHAR(100),
  postal_code         VARCHAR(20),
  country             VARCHAR(50),
  segment             VARCHAR(50),          -- B2B / B2C, SMB / Enterprise
  acquisition_channel VARCHAR(50),          -- Web, Referral, Paid Search ...
  registration_date   DATE,
  -- SCD2 tracking columns
  is_current          BOOLEAN DEFAULT TRUE,
  effective_from      DATE NOT NULL,
  effective_to        DATE                  -- NULL means currently active
);


-- ==========================================================================
-- Dimension: Product
-- ==========================================================================
CREATE TABLE dim_product (
  product_key     INT PRIMARY KEY,
  product_id      VARCHAR(20) NOT NULL,
  product_name    VARCHAR(200),
  category        VARCHAR(100),
  subcategory     VARCHAR(100),
  brand           VARCHAR(100),
  unit_cost       NUMERIC(10,2),
  unit_list_price NUMERIC(10,2),
  sku             VARCHAR(50),
  weight_kg       NUMERIC(8,3),
  is_active       BOOLEAN DEFAULT TRUE
);


-- ==========================================================================
-- Dimension: Channel
-- ==========================================================================
CREATE TABLE dim_channel (
  channel_key   INT PRIMARY KEY,
  channel_name  VARCHAR(50),          -- 'Web', 'Mobile App', 'In-Store', 'Call Centre'
  channel_type  VARCHAR(20),          -- 'Online', 'Offline'
  region        VARCHAR(50)
);


-- ==========================================================================
-- Fact Table: Sales (at the centre of the star)
-- ==========================================================================
CREATE TABLE fact_sales (
  -- Foreign keys to dimension tables
  date_key        INT NOT NULL REFERENCES dim_date(date_key),
  customer_key    INT NOT NULL REFERENCES dim_customer(customer_key),
  product_key     INT NOT NULL REFERENCES dim_product(product_key),
  channel_key     INT NOT NULL REFERENCES dim_channel(channel_key),

  -- Degenerate dimension (no separate dimension table, but useful for drill-down)
  order_id        VARCHAR(20),
  line_number     SMALLINT,

  -- Additive measures
  quantity        INT NOT NULL,
  unit_price      NUMERIC(10,2) NOT NULL,
  discount_amount NUMERIC(10,2) DEFAULT 0,
  gross_revenue   NUMERIC(12,2) GENERATED ALWAYS AS (quantity * unit_price) STORED,
  net_revenue     NUMERIC(12,2) GENERATED ALWAYS AS
                    (quantity * unit_price - discount_amount) STORED,
  cost_amount     NUMERIC(12,2),

  -- Composite primary key: one row per order line item
  PRIMARY KEY (date_key, customer_key, product_key, channel_key, order_id, line_number)
);

-- Indexes for the most common analytical access patterns
CREATE INDEX idx_fact_sales_date     ON fact_sales(date_key);
CREATE INDEX idx_fact_sales_customer ON fact_sales(customer_key);
CREATE INDEX idx_fact_sales_product  ON fact_sales(product_key);
```

### 4.2 Querying the Star Schema

```sql
-- Revenue by product category and quarter
SELECT
  d.year,
  d.quarter,
  p.category,
  SUM(f.net_revenue)                     AS total_revenue,
  COUNT(DISTINCT f.customer_key)         AS unique_customers,
  SUM(f.quantity)                         AS units_sold,
  SUM(f.net_revenue) / NULLIF(SUM(f.quantity), 0) AS revenue_per_unit
FROM fact_sales f
  JOIN dim_date    d ON f.date_key    = d.date_key
  JOIN dim_product p ON f.product_key = p.product_key
WHERE d.year = 2024
GROUP BY d.year, d.quarter, p.category
ORDER BY d.year, d.quarter, total_revenue DESC;


-- Top 10 customers by revenue for the Web channel in 2024
SELECT
  c.first_name || ' ' || c.last_name  AS customer,
  c.segment,
  SUM(f.net_revenue)                   AS revenue,
  COUNT(DISTINCT f.date_key)           AS active_days
FROM fact_sales f
  JOIN dim_customer c  ON f.customer_key = c.customer_key
  JOIN dim_channel  ch ON f.channel_key  = ch.channel_key
  JOIN dim_date     d  ON f.date_key     = d.date_key
WHERE ch.channel_name = 'Web'
  AND d.year = 2024
  AND c.is_current = TRUE
GROUP BY customer, c.segment
ORDER BY revenue DESC
LIMIT 10;


-- Year-over-year monthly revenue comparison
SELECT
  d.month_number,
  d.month_name,
  SUM(CASE WHEN d.year = 2024 THEN f.net_revenue END) AS revenue_2024,
  SUM(CASE WHEN d.year = 2023 THEN f.net_revenue END) AS revenue_2023,
  ROUND(
    (SUM(CASE WHEN d.year = 2024 THEN f.net_revenue END)
     - SUM(CASE WHEN d.year = 2023 THEN f.net_revenue END))
    / NULLIF(SUM(CASE WHEN d.year = 2023 THEN f.net_revenue END), 0) * 100
  , 2) AS yoy_growth_pct
FROM fact_sales f
  JOIN dim_date d ON f.date_key = d.date_key
WHERE d.year IN (2023, 2024)
GROUP BY d.month_number, d.month_name
ORDER BY d.month_number;
```

### 4.3 Star Schema Advantages

| Advantage                | Explanation                                                          |
|--------------------------|----------------------------------------------------------------------|
| Query simplicity         | Analysts write predictable JOIN patterns: fact → dimension           |
| Performance              | Fewer JOINs than normalised schemas; columnar engines exploit this   |
| BI tool compatibility    | Every BI tool (Looker, Tableau, Power BI) natively understands stars |
| Aggregation friendliness | Additive measures + dimensional slicing = natural GROUP BY patterns  |
| Parallelism              | Dimension tables fit in memory; fact scans parallelise per partition |

---

## 5. Snowflake Schema

The snowflake schema normalises one or more dimension tables into sub-tables, forming a
shape that looks like a snowflake rather than a star.

```sql
-- ========================================
-- Snowflake: product dimension normalised
-- ========================================
CREATE TABLE dim_department (
  department_key   INT PRIMARY KEY,
  department_name  VARCHAR(100)
);

CREATE TABLE dim_category (
  category_key     INT PRIMARY KEY,
  category_name    VARCHAR(100),
  department_key   INT REFERENCES dim_department(department_key)
);

CREATE TABLE dim_subcategory (
  subcategory_key  INT PRIMARY KEY,
  subcategory_name VARCHAR(100),
  category_key     INT REFERENCES dim_category(category_key)
);

CREATE TABLE dim_product_snowflake (
  product_key      INT PRIMARY KEY,
  product_name     VARCHAR(200),
  subcategory_key  INT REFERENCES dim_subcategory(subcategory_key),
  brand            VARCHAR(100),
  unit_cost        NUMERIC(10,2)
);

-- Query now requires 3 JOINs to reach department from the fact table:
-- fact_sales → dim_product_snowflake → dim_subcategory → dim_category → dim_department

SELECT
  dept.department_name,
  SUM(f.net_revenue) AS revenue
FROM fact_sales f
  JOIN dim_product_snowflake p   ON f.product_key    = p.product_key
  JOIN dim_subcategory       sc  ON p.subcategory_key = sc.subcategory_key
  JOIN dim_category          cat ON sc.category_key   = cat.category_key
  JOIN dim_department        dept ON cat.department_key = dept.department_key
GROUP BY dept.department_name
ORDER BY revenue DESC;
```

### 5.1 Star vs Snowflake Trade-offs

```
┌────────────────────────┬─────────────────────┬──────────────────────────┐
│ Criterion              │ Star Schema         │ Snowflake Schema         │
├────────────────────────┼─────────────────────┼──────────────────────────┤
│ Query complexity       │ Simpler (fewer JOINs)│ More JOINs               │
│ Storage redundancy     │ Higher              │ Lower                    │
│ Dimension updates      │ Update one table    │ Update sub-table only    │
│ BI tool support        │ Excellent           │ Good (but more setup)    │
│ Query performance      │ Faster (fewer JOINs)│ Slower for dimension hops│
│ When to use            │ Default choice      │ Very large dimensions or │
│                        │                     │ strict governance needs  │
└────────────────────────┴─────────────────────┴──────────────────────────┘
```

**Practical guidance**: prefer star schema as the default. Use snowflake only when a
dimension is extremely large (millions of rows) and normalisation materially reduces
storage and maintenance burden.

---

## 6. Galaxy Schema (Fact Constellation)

When multiple business processes share conformed dimensions, the result is a galaxy schema
(also called a fact constellation). Several fact tables reference the same dimension tables.

```sql
-- Two fact tables sharing conformed dimensions
CREATE TABLE fact_sales (
  date_key      INT REFERENCES dim_date(date_key),
  customer_key  INT REFERENCES dim_customer(customer_key),
  product_key   INT REFERENCES dim_product(product_key),
  ...
);

CREATE TABLE fact_returns (
  date_key       INT REFERENCES dim_date(date_key),
  customer_key   INT REFERENCES dim_customer(customer_key),
  product_key    INT REFERENCES dim_product(product_key),
  return_reason_key INT REFERENCES dim_return_reason(return_reason_key),
  quantity_returned INT,
  refund_amount     NUMERIC(12,2)
);

-- Cross-process analysis: return rate by product category
SELECT
  p.category,
  SUM(s.quantity)             AS units_sold,
  SUM(r.quantity_returned)    AS units_returned,
  ROUND(SUM(r.quantity_returned) * 100.0 / NULLIF(SUM(s.quantity), 0), 2) AS return_rate_pct
FROM fact_sales   s
  JOIN dim_product p ON s.product_key = p.product_key
  LEFT JOIN fact_returns r ON r.product_key = s.product_key
                          AND r.date_key    = s.date_key
GROUP BY p.category
ORDER BY return_rate_pct DESC;
```

This design pattern is central to Kimball's concept of the enterprise data warehouse bus.

---

## 7. Fact Tables — Types

Kimball identifies three fundamental types of fact tables, each serving different analytical
needs.

### 7.1 Transaction Fact Table

Stores one row per discrete event. The grain is the individual transaction (or line item).

```sql
-- One row per order line item
CREATE TABLE fact_order_line (
  date_key        INT NOT NULL,
  customer_key    INT NOT NULL,
  product_key     INT NOT NULL,
  channel_key     INT NOT NULL,
  order_id        VARCHAR(20),      -- degenerate dimension
  line_number     SMALLINT,
  quantity        INT,
  unit_price      NUMERIC(10,2),
  discount_pct    NUMERIC(5,2),
  net_revenue     NUMERIC(12,2),
  cost            NUMERIC(12,2)
);

-- Characteristics:
--   + Most detailed grain — supports drill-down to individual events
--   + Grows indefinitely (one row per event)
--   + Typically the largest table in the warehouse
--   - Not efficient for "current state" questions
```

**When to use**: any process where each event is independently meaningful — sales, clicks,
log entries, shipments, payments.

### 7.2 Periodic Snapshot Fact Table

Stores one row per entity per time period. The grain is the combination of a time period
and an entity.

```sql
-- One row per product per month
CREATE TABLE fact_monthly_inventory (
  month_key         INT NOT NULL,      -- YYYYMM
  product_key       INT NOT NULL,
  warehouse_key     INT NOT NULL,
  quantity_on_hand  INT,               -- semi-additive (do NOT sum across time)
  quantity_received INT,               -- additive
  quantity_shipped  INT,               -- additive
  days_of_supply    NUMERIC(6,1),      -- non-additive
  PRIMARY KEY (month_key, product_key, warehouse_key)
);

-- One row per customer per week: account activity
CREATE TABLE fact_weekly_account_snapshot (
  week_key          INT NOT NULL,      -- YYYYWW
  customer_key      INT NOT NULL,
  account_balance   NUMERIC(14,2),     -- semi-additive
  deposits          NUMERIC(14,2),     -- additive
  withdrawals       NUMERIC(14,2),     -- additive
  transaction_count INT,               -- additive
  PRIMARY KEY (week_key, customer_key)
);

-- Semi-additive query: average balance per customer segment
SELECT
  c.segment,
  AVG(f.account_balance) AS avg_balance,
  SUM(f.deposits)        AS total_deposits
FROM fact_weekly_account_snapshot f
  JOIN dim_customer c ON f.customer_key = c.customer_key
WHERE f.week_key BETWEEN 202401 AND 202452
GROUP BY c.segment;
```

**When to use**: processes where you need to measure the state at regular intervals —
inventory levels, account balances, pipeline snapshots, workforce headcount.

### 7.3 Accumulating Snapshot Fact Table

Stores one row per entity lifecycle instance. The row is updated as the entity progresses
through defined milestones.

```sql
-- One row per order, updated as it moves through the fulfilment pipeline
CREATE TABLE fact_order_fulfilment (
  order_key              INT PRIMARY KEY,
  customer_key           INT,
  product_key            INT,

  -- Milestone date keys (each references dim_date)
  order_date_key         INT,
  payment_date_key       INT,      -- NULL until payment received
  pick_date_key          INT,      -- NULL until warehouse picks the order
  ship_date_key          INT,      -- NULL until shipped
  delivery_date_key      INT,      -- NULL until delivered

  -- Lag measures (computed: days between milestones)
  days_to_payment        INT,
  days_to_pick           INT,
  days_to_ship           INT,
  days_to_deliver        INT,
  total_days             INT,

  -- Status
  current_status         VARCHAR(30),

  -- Measures
  order_amount           NUMERIC(12,2)
);

-- Populate milestone dates via UPDATE as events occur
UPDATE fact_order_fulfilment
SET
  ship_date_key   = 20240120,
  days_to_ship    = 20240120 - pick_date_key,
  current_status  = 'shipped'
WHERE order_key = 42;

-- Analysis: average days-to-deliver by product category
SELECT
  p.category,
  AVG(f.total_days)       AS avg_fulfilment_days,
  AVG(f.days_to_ship)     AS avg_days_to_ship,
  AVG(f.days_to_deliver)  AS avg_days_to_deliver,
  COUNT(*)                AS order_count
FROM fact_order_fulfilment f
  JOIN dim_product p ON f.product_key = p.product_key
WHERE f.delivery_date_key IS NOT NULL  -- completed orders only
GROUP BY p.category
ORDER BY avg_fulfilment_days DESC;
```

**When to use**: processes with a defined lifecycle — order fulfilment, claims processing,
loan applications, patient journeys, support ticket resolution.

### 7.4 Comparison of Fact Table Types

```
┌──────────────────────┬──────────────────┬────────────────────┬─────────────────────────┐
│                      │ Transaction      │ Periodic Snapshot  │ Accumulating Snapshot   │
├──────────────────────┼──────────────────┼────────────────────┼─────────────────────────┤
│ Grain                │ One event        │ Period + entity    │ Entity lifecycle        │
│ Row behaviour        │ Insert-only      │ Insert (per period)│ Insert, then update     │
│ Date keys            │ Single date      │ Single period date │ Multiple milestone dates│
│ Typical size         │ Very large       │ Moderate           │ Small–moderate          │
│ Measures             │ Additive         │ Semi-additive mix  │ Additive + lag measures │
│ Primary use          │ Detail analysis  │ State tracking     │ Process efficiency      │
└──────────────────────┴──────────────────┴────────────────────┴─────────────────────────┘
```

---

## 8. Dimension Tables and Slowly Changing Dimensions (SCD)

Dimensions change over time. How you handle those changes determines whether your
historical analyses remain accurate.

### 8.1 SCD Type 0 — Retain Original

The dimension attribute is set once and never changes, regardless of what happens in the
source system.

```sql
-- Type 0: customer's original acquisition channel is never overwritten
-- Rationale: we always want to attribute the customer to how they first arrived.

-- The column acquisition_channel is populated on first load and never updated.
```

**Use case**: original registration date, first-purchase channel, account creation date.

### 8.2 SCD Type 1 — Overwrite

The current value replaces the old value. No history is preserved.

```sql
-- Type 1: customer changes city — just overwrite
UPDATE dim_customer
SET city = 'London',
    state_province = 'England'
WHERE customer_id = 'C001' AND is_current = TRUE;

-- Advantages: simple, no bloat.
-- Disadvantage: historical queries report the CURRENT city, not the city at the time
-- of the transaction. A sale that occurred when the customer lived in Manchester now
-- appears as a London sale.
```

**Use case**: corrections (typo in name), attributes where history is irrelevant (e.g.,
internal customer segment that is always queried at current value).

### 8.3 SCD Type 2 — Add New Row (Full History)

A new row is inserted for each change. The previous row is marked as inactive with an end
date. This is the most common SCD strategy in production data warehouses.

```sql
-- Type 2: customer moves from Manchester to London

-- Step 1: close the current row
UPDATE dim_customer
SET is_current    = FALSE,
    effective_to  = CURRENT_DATE - INTERVAL '1 day'
WHERE customer_id = 'C001' AND is_current = TRUE;

-- Step 2: insert a new row with a new surrogate key
INSERT INTO dim_customer (
  customer_key, customer_id, first_name, last_name, email, city, state_province,
  country, segment, acquisition_channel, registration_date,
  is_current, effective_from, effective_to
)
VALUES (
  NEXTVAL('dim_customer_seq'),
  'C001', 'James', 'Smith', 'james.smith@example.com',
  'London', 'England', 'UK', 'B2C', 'Web', '2021-03-15',
  TRUE, CURRENT_DATE, NULL
);

-- The fact_sales rows that were loaded while the customer lived in Manchester still
-- reference the OLD customer_key (Manchester row). New fact rows reference the NEW
-- customer_key (London row). Historical analysis is accurate.

-- SCD2 point-in-time query: what did the customer look like on 2023-06-15?
SELECT *
FROM dim_customer
WHERE customer_id = 'C001'
  AND '2023-06-15' BETWEEN effective_from AND COALESCE(effective_to, '9999-12-31');
```

**Design considerations:**
- The surrogate key (`customer_key`) is unique per version. The natural key
  (`customer_id`) identifies the real-world entity across versions.
- Always include `is_current`, `effective_from`, and `effective_to` for clean querying.
- Use `COALESCE(effective_to, '9999-12-31')` or keep `NULL` — both conventions work, but
  pick one and be consistent.

### 8.4 SCD Type 3 — Add New Column

Tracks a limited history (typically only the previous value) by adding columns.

```sql
-- Type 3: track the customer's current and previous city
ALTER TABLE dim_customer ADD COLUMN previous_city VARCHAR(100);
ALTER TABLE dim_customer ADD COLUMN city_changed_on DATE;

UPDATE dim_customer
SET previous_city    = city,
    city             = 'London',
    city_changed_on  = CURRENT_DATE
WHERE customer_id = 'C001';

-- Advantages: simple, no row explosion.
-- Disadvantage: only the immediately previous value is available; anything older is lost.
```

**Use case**: when the business only needs to compare "current vs previous" — e.g.,
current and previous sales territory for territory-realignment analysis.

### 8.5 SCD Type 4 — Mini-Dimension (History Table)

Rapidly changing attributes are separated into a "mini-dimension" to avoid bloating the
main dimension with SCD2 rows.

```sql
-- Type 4: customer demographics that change frequently (age band, income band, score)
CREATE TABLE dim_customer_demographics (
  demographics_key  INT PRIMARY KEY,
  age_band          VARCHAR(20),    -- '18-25', '26-35', ...
  income_band       VARCHAR(20),    -- 'Low', 'Medium', 'High'
  credit_score_band VARCHAR(20)     -- 'Poor', 'Fair', 'Good', 'Excellent'
);

-- The fact table carries BOTH the main customer key AND the demographics key
CREATE TABLE fact_sales_with_mini (
  date_key           INT,
  customer_key       INT REFERENCES dim_customer(customer_key),
  demographics_key   INT REFERENCES dim_customer_demographics(demographics_key),
  product_key        INT,
  net_revenue        NUMERIC(12,2)
);

-- At load time, the ETL looks up the customer's current demographic profile,
-- finds or creates the matching demographics_key, and writes it to the fact row.

-- Query: revenue by income band (without bloating dim_customer)
SELECT
  demo.income_band,
  SUM(f.net_revenue) AS revenue
FROM fact_sales_with_mini f
  JOIN dim_customer_demographics demo ON f.demographics_key = demo.demographics_key
GROUP BY demo.income_band;
```

**Use case**: attributes that change too frequently for SCD2 to be practical — customer
scoring, risk tier, age band (recalculated periodically).

### 8.6 SCD Type 5 — Type 4 + Type 1 Outrigger

Combines Type 4 (mini-dimension in the fact table) with a Type 1 outrigger on the base
dimension, giving you both "as-was" (via the fact table's demographics key) and "as-is"
(via the current outrigger on dim_customer).

```sql
-- dim_customer has a current_demographics_key (Type 1 overwrite)
ALTER TABLE dim_customer ADD COLUMN current_demographics_key INT
  REFERENCES dim_customer_demographics(demographics_key);

-- The fact table still carries its own demographics_key (as-was, from load time).
-- For "current" analysis, join fact → dim_customer → dim_customer_demographics.
-- For "as-was" analysis, join fact → dim_customer_demographics directly.
```

### 8.7 SCD Type 6 — Hybrid (Type 1 + Type 2 + Type 3)

Also called "Type 2 with Type 1 overlay." Every SCD2 row carries the current value of the
changing attribute alongside the historical value, plus effective dates.

```sql
-- Type 6: each SCD2 row has both historical and current city
CREATE TABLE dim_customer_type6 (
  customer_key       INT PRIMARY KEY,
  customer_id        VARCHAR(20),
  first_name         VARCHAR(100),
  last_name          VARCHAR(100),
  historical_city    VARCHAR(100),    -- city at the time this row was active (Type 2)
  current_city       VARCHAR(100),    -- always reflects the latest city (Type 1 overlay)
  is_current         BOOLEAN,
  effective_from     DATE,
  effective_to       DATE
);

-- When the customer moves from Manchester to London:
-- Step 1: insert new row (SCD2)
-- Step 2: update ALL rows for this customer_id, setting current_city = 'London' (Type 1)
UPDATE dim_customer_type6
SET current_city = 'London'
WHERE customer_id = 'C001';

-- Now:
--   Row 1: historical_city='Manchester', current_city='London', is_current=FALSE
--   Row 2: historical_city='London',     current_city='London', is_current=TRUE

-- Analysts can choose which to use:
-- GROUP BY historical_city  →  revenue attributed to where the customer was at sale time
-- GROUP BY current_city     →  revenue attributed to where the customer is now
```

**Use case**: when both historical and current views are frequently needed and you want to
avoid complex self-joins.

### 8.8 SCD Summary Matrix

```
┌───────┬──────────────────────────────┬──────────────┬───────────────┐
│ Type  │ Strategy                     │ History kept │ Row growth    │
├───────┼──────────────────────────────┼──────────────┼───────────────┤
│ 0     │ Retain original              │ Original only│ None          │
│ 1     │ Overwrite                    │ None         │ None          │
│ 2     │ New row per change           │ Full         │ Unbounded     │
│ 3     │ Add column for previous value│ Previous only│ None          │
│ 4     │ Mini-dimension               │ In fact table│ Mini-dim rows │
│ 5     │ Type 4 + Type 1 outrigger    │ In fact + dim│ Mini-dim rows │
│ 6     │ Type 2 + Type 1 overlay      │ Full + current│ SCD2 growth  │
└───────┴──────────────────────────────┴──────────────┴───────────────┘
```

---

## 9. Conformed Dimensions and the Enterprise Bus Matrix

### 9.1 Conformed Dimensions

A conformed dimension is a dimension table that is shared identically across multiple fact
tables (business processes). Conformance means:

- Same surrogate keys.
- Same attributes and attribute names.
- Same grain or a strict subset/superset with clean rollup.

```sql
-- dim_customer is used by fact_sales, fact_returns, and fact_support_tickets
-- It is the SAME table, not three copies with different definitions.

-- If marketing defines "segment" differently from finance, you do NOT have a conformed
-- dimension. You have a data integration bug.

-- Cross-process query enabled by conformed dimensions:
SELECT
  c.segment,
  SUM(s.net_revenue)           AS total_sales,
  SUM(r.refund_amount)         AS total_refunds,
  COUNT(DISTINCT t.ticket_id)  AS support_tickets
FROM dim_customer c
  LEFT JOIN fact_sales           s ON c.customer_key = s.customer_key
  LEFT JOIN fact_returns          r ON c.customer_key = r.customer_key
  LEFT JOIN fact_support_tickets  t ON c.customer_key = t.customer_key
WHERE c.is_current = TRUE
GROUP BY c.segment;
```

Without conformed dimensions, this query is impossible (or produces wrong results because
"customer" means different things in different fact tables).

### 9.2 The Enterprise Bus Matrix

The bus matrix is Kimball's planning tool for the data warehouse. It maps business
processes (rows) to dimensions (columns), showing which dimensions participate in which
processes.

```
                        dim_   dim_      dim_     dim_    dim_     dim_
                        date   customer  product  store   channel  promotion
                       ──────  ────────  ───────  ─────  ───────  ─────────
Sales                    ✓       ✓         ✓       ✓       ✓        ✓
Returns                  ✓       ✓         ✓       ✓       ✓
Inventory snapshots      ✓                 ✓       ✓
Website clickstream      ✓       ✓                         ✓
Customer support tickets ✓       ✓         ✓
Marketing campaigns      ✓       ✓                                  ✓
```

**How to use the bus matrix:**

1. List all business processes the organisation wants to analyse.
2. For each process, identify the dimensions that provide context.
3. Shared dimensions (columns with multiple checkmarks) are candidates for conformance.
4. Prioritise building the processes that share the most dimensions — they provide the
   highest cross-process analytical value.
5. Implement one row (one star schema) at a time, conforming dimensions as you go.

The bus matrix is both a planning document and a communication tool. Business stakeholders
can read it and validate: "Yes, marketing campaigns involve date, customer, and promotion.
No, they do not involve inventory."

### 9.3 Conformed Dimensions — Common Pitfalls

| Pitfall                          | Consequence                                              |
|----------------------------------|----------------------------------------------------------|
| Same name, different definition  | Cross-process queries produce wrong numbers               |
| Subset dimension not aligned     | Drill-across breaks — rows don't join                    |
| Stale copies (ETL lag)           | Process A has today's customer; Process B has yesterday's |
| Different surrogate key sequences| JOINs across facts fail silently                         |

**Mitigation**: build conformed dimensions as shared dbt models (or equivalent), loaded
from a single source, with automated consistency tests.

---

## 10. Surrogate Keys vs Natural Keys

### 10.1 Why Surrogate Keys

A surrogate key is a system-generated integer with no business meaning. It replaces the
natural (business) key as the primary key in dimension tables and as the foreign key in
fact tables.

```sql
-- Natural key approach (problematic):
CREATE TABLE fact_sales (
  sale_date    DATE,
  customer_id  VARCHAR(20),  -- natural key from the OLTP system
  product_sku  VARCHAR(50),
  net_revenue  NUMERIC(12,2)
);

-- Problems:
-- 1. If the source changes customer_id format (C001 → CUST-001), all fact rows break.
-- 2. SCD2 is impossible: which "C001" does this fact row refer to?
-- 3. VARCHAR keys are larger and slower to join than INT keys.
-- 4. Multiple source systems may reuse the same natural key (customer 1 in System A ≠
--    customer 1 in System B).

-- Surrogate key approach (recommended):
CREATE TABLE fact_sales (
  date_key      INT,        -- integer surrogate key → dim_date
  customer_key  INT,        -- integer surrogate key → dim_customer
  product_key   INT,        -- integer surrogate key → dim_product
  net_revenue   NUMERIC(12,2)
);

-- Advantages:
-- 1. Immune to source key format changes.
-- 2. Supports SCD2 (multiple rows per natural key, each with a unique surrogate key).
-- 3. Smaller (4 bytes INT vs 20+ bytes VARCHAR) → faster joins.
-- 4. Integrates multiple source systems under one key space.
```

### 10.2 The Unknown Member

Every dimension should have a special row for "unknown" with a fixed surrogate key (e.g.,
-1). When a fact row's foreign key cannot be resolved to a dimension member, it maps to
the unknown member instead of being dropped (INNER JOIN) or left as NULL.

```sql
INSERT INTO dim_customer (customer_key, customer_id, first_name, last_name,
  is_current, effective_from)
VALUES (-1, 'UNKNOWN', 'Unknown', 'Customer', TRUE, '1900-01-01');

-- In the ETL: map unresolvable customer IDs to the unknown member
INSERT INTO fact_sales (date_key, customer_key, product_key, net_revenue)
SELECT
  d.date_key,
  COALESCE(c.customer_key, -1) AS customer_key,  -- -1 if no match
  COALESCE(p.product_key, -1)  AS product_key,
  raw.net_revenue
FROM staging.raw_sales raw
  LEFT JOIN dim_date     d ON d.full_date     = raw.sale_date
  LEFT JOIN dim_customer c ON c.customer_id   = raw.customer_id AND c.is_current = TRUE
  LEFT JOIN dim_product  p ON p.product_id    = raw.product_id;
```

---

## 11. Degenerate Dimensions

A degenerate dimension is a dimension key that lives in the fact table without a
corresponding dimension table. It is typically a transaction identifier (order number,
invoice number, shipment tracking number).

```sql
-- order_id is a degenerate dimension: it exists in the fact table,
-- but there is no dim_order table because the only interesting attribute
-- IS the order_id itself.
CREATE TABLE fact_sales (
  date_key      INT,
  customer_key  INT,
  product_key   INT,
  order_id      VARCHAR(20),   -- degenerate dimension
  line_number   SMALLINT,      -- degenerate dimension
  net_revenue   NUMERIC(12,2)
);

-- Use degenerate dimensions to drill down to individual transactions
-- or to group line items belonging to the same order.
SELECT
  order_id,
  COUNT(*) AS line_count,
  SUM(net_revenue) AS order_total
FROM fact_sales
GROUP BY order_id
ORDER BY order_total DESC
LIMIT 10;
```

---

## 12. Junk Dimensions and Mini-Dimensions

### 12.1 Junk Dimensions

When multiple low-cardinality flags and indicators exist (is_rush, is_gift, payment_type,
order_source), putting each in the fact table wastes space and widens the row. A junk
dimension collects them into a single small dimension.

```sql
CREATE TABLE dim_order_flags (
  order_flags_key  INT PRIMARY KEY,
  is_rush          BOOLEAN,
  is_gift_wrap     BOOLEAN,
  payment_type     VARCHAR(20),    -- 'Credit Card', 'PayPal', 'Wire Transfer'
  order_source     VARCHAR(20)     -- 'Web', 'Mobile', 'Phone'
);

-- Pre-populate all possible combinations (or build dynamically during ETL)
-- For 2 booleans × 3 payment types × 3 order sources = 36 rows

-- Fact table references the junk dimension with a single FK
CREATE TABLE fact_sales (
  date_key          INT,
  customer_key      INT,
  product_key       INT,
  order_flags_key   INT REFERENCES dim_order_flags(order_flags_key),
  net_revenue       NUMERIC(12,2)
);
```

### 12.2 Mini-Dimensions

Mini-dimensions are used for Type 4 SCD (covered in Section 8.5). They extract
rapidly-changing or high-cardinality attributes from a large dimension into a separate
small dimension table, referenced directly from the fact table.

---

## 13. Modern Data Warehouse Architecture

The modern cloud-native data warehouse has evolved the classical model:

```
Data Sources              Ingestion / ELT
    │                          │
    ▼                          ▼
[OLTP Databases]  ────────► [Object Storage / Staging]
[APIs / Events]                    │
[Files (CSV/JSON/Parquet)]         ▼
[SaaS tools (Salesforce,     [Cloud Data Warehouse]
 Stripe, HubSpot)]           (BigQuery / Snowflake / Redshift)
                                   │
                     ┌─────────────┼──────────────┐
                     ▼             ▼              ▼
               [Raw / Bronze]  [Staging / Silver]  [Presentation / Gold]
               (schema-on-     (cleaned, typed,    (star schemas,
                read, as-is)    deduplicated)       aggregates, BI)
```

The three zones of the modern DW:

1. **Raw / Bronze** — data loaded as-is from the source. No transformations. Immutable
   landing zone. Stored in Parquet, JSON, or the DW's native format.
2. **Staging / Silver** — data is cleaned, typed, deduplicated, and conformed. Business
   keys are resolved to surrogate keys. dbt models typically live here.
3. **Presentation / Gold** — tables optimised for BI consumption: star schemas, aggregated
   summaries, wide denormalised tables. Business users and BI tools connect here.

This three-layer pattern is called the **medallion architecture** and is adopted by
Databricks, dbt, and virtually every modern data engineering framework.

### 13.1 Data Vault

Data Vault (Dan Linstedt, 2000) is an alternative modelling approach for the raw vault
layer. It uses three entity types:

- **Hub** — a unique list of business keys (customer hub, product hub).
- **Link** — relationships between hubs (customer-order link, order-product link).
- **Satellite** — descriptive attributes and their history, attached to hubs or links.

Data Vault fits naturally as the Silver layer in a medallion architecture, with star
schemas built on top as the Gold layer.

---

## 14. ETL vs ELT

| Aspect             | ETL (Extract-Transform-Load)          | ELT (Extract-Load-Transform)         |
|--------------------|---------------------------------------|--------------------------------------|
| Transform location | External engine (Informatica, SSIS)   | Inside the DW (dbt, SQL)             |
| Data landing       | Data arrives pre-transformed          | Raw data lands first, then transformed|
| Scalability        | Limited by ETL server                 | Leverages DW compute (massive scale) |
| Flexibility        | Schema changes require ETL rebuild    | Schema-on-read; transform later      |
| Debugging          | Complex (logic spread across tools)   | Transparent (SQL, version-controlled)|
| Modern alignment   | Legacy, still common in enterprises   | Default for cloud DW (dbt + BigQuery)|

**Practical guidance**: for greenfield projects on cloud DW, use ELT. Load raw data to the
Bronze layer, then transform in SQL (dbt) through Silver to Gold.

---

## 15. Common Anti-Patterns

### Anti-Pattern 1: Normalised Schema in the DW

Bringing 3NF OLTP normalisation into the analytical layer forces deep join chains that
destroy query performance on billion-row fact tables.

```sql
-- BAD: 4 joins to reach product category
-- orders → order_items → products → categories → departments

-- GOOD: star schema, 1 join
-- fact_sales → dim_product (category is a denormalised attribute)
```

### Anti-Pattern 2: Mixed Granularity in a Fact Table

Putting daily aggregates and individual transactions in the same table makes every measure
ambiguous.

```sql
-- BAD: what does one row represent?
INSERT INTO fact_sales (date_key, customer_key, product_key, net_revenue, daily_total)
VALUES (20240115, 42, 100, 49.99, 15000.00);

-- GOOD: separate tables with declared grain
-- fact_sales: one row per line item
-- fact_daily_revenue: one row per day per product per channel
```

### Anti-Pattern 3: No Surrogate Keys

Using natural keys from the source system directly in fact tables creates fragile joins
and makes SCD2 impossible.

### Anti-Pattern 4: Ignoring the Unknown Member

When a fact row's FK has no matching dimension member, an INNER JOIN silently drops the
row. Revenue disappears. The unknown member (-1) catches these rows and makes the data
loss visible.

### Anti-Pattern 5: Business Logic in the ETL Pipeline

Business rules buried in Python scripts, Airflow DAGs, or stored procedures are hard to
version, test, and review. Move business logic into SQL models (dbt) where it can be
version-controlled, tested, and documented alongside the schema.

---

## 16. Troubleshooting

### Problem: Fact table row counts don't match the source system

**Causes:**
- INNER JOIN drops rows when dimension members are missing (unknown member not implemented).
- Duplicate source records inflate the count.
- Timezone misalignment shifts records across date boundaries.

**Diagnosis:**
```sql
-- Count rows in source vs fact table for a specific date
SELECT COUNT(*) FROM staging.raw_orders WHERE sale_date = '2024-01-15';
SELECT COUNT(*) FROM fact_sales WHERE date_key = 20240115;

-- Find fact rows mapping to the unknown member (possible missing dimension records)
SELECT COUNT(*) FROM fact_sales WHERE customer_key = -1;
```

### Problem: SCD2 dimension growing too fast

**Causes:**
- Tracking volatile attributes (login timestamp, session count) with SCD2.
- Source system sends unchanged records that trigger false updates.

**Solutions:**
- Move volatile attributes to a mini-dimension (SCD Type 4).
- Add a change-detection hash in the ETL to avoid inserting rows when nothing changed.

```sql
-- Change-detection hash: only insert SCD2 row if the hash changes
SELECT
  customer_id,
  MD5(CONCAT(city, '|', state_province, '|', segment)) AS change_hash
FROM staging.customers;
```

### Problem: Query performance degrades over time

**Causes:**
- Stale statistics (ANALYZE not running).
- Partition pruning not engaged (missing partition filter).
- Materialized views not refreshed.

**Diagnosis:**
```sql
-- Check if partition pruning is working (Snowflake example)
SELECT
  query_id,
  partitions_scanned,
  partitions_total,
  ROUND(partitions_scanned * 100.0 / partitions_total, 2) AS pct_scanned
FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY())
ORDER BY total_elapsed_time DESC
LIMIT 20;
```

---

## 17. Frequently Asked Questions

**Q: When should I use a star schema vs a snowflake schema?**

Star schema should be the default. Use snowflake only when a dimension table is very large
(millions of rows) and normalising it materially reduces storage and maintenance cost.
Modern columnar engines make the star schema's denormalisation essentially free for
read-heavy workloads.

**Q: How many dimensions is too many for a single fact table?**

There is no hard limit, but 10-15 dimensions is typical. More than 20 dimensions usually
signals that the grain is too coarse or that some dimensions should be consolidated (junk
dimension) or moved to a mini-dimension.

**Q: Should I use SCD2 for every dimension?**

No. SCD2 is appropriate when historical accuracy matters for analysis (e.g., a customer's
sales territory at the time of the sale). For attributes where only the current value
matters (e.g., a typo correction in a product name), SCD1 (overwrite) is simpler and
sufficient.

**Q: How do I handle late-arriving facts?**

Late-arriving facts arrive after the dimension has already changed. The ETL must look up
the dimension member that was active at the time of the event (point-in-time lookup).

```sql
-- Look up the customer_key that was active on the date of the late-arriving sale
SELECT customer_key
FROM dim_customer
WHERE customer_id = 'C001'
  AND '2024-01-10' BETWEEN effective_from AND COALESCE(effective_to, '9999-12-31');
```

**Q: How do I handle late-arriving dimensions?**

Late-arriving dimensions occur when a fact row arrives before the dimension member exists.
Insert the fact row with the unknown member (-1) and back-fill when the dimension arrives.

```sql
-- Back-fill: update fact rows that were loaded with the unknown member
UPDATE fact_sales
SET customer_key = (
  SELECT customer_key FROM dim_customer
  WHERE customer_id = 'C001' AND is_current = TRUE
)
WHERE customer_key = -1
  AND order_id IN (SELECT order_id FROM staging.late_dim_backfill WHERE customer_id = 'C001');
```

**Q: What is the difference between a data warehouse and a data lake?**

A data warehouse stores structured, modelled data optimised for BI queries (star schemas,
columnar storage). A data lake stores raw, unstructured, or semi-structured data at any
scale (Parquet files on S3, raw JSON logs). The modern "lakehouse" combines both: raw data
in the lake, with a table format (Delta Lake, Iceberg) that adds schema enforcement and
ACID semantics, and a query engine that can serve both exploratory and BI workloads.

**Q: What is the role of dbt in a modern data warehouse?**

dbt (data build tool) manages the transformation layer of an ELT pipeline. It compiles
SQL models (SELECT statements) into tables or views in the data warehouse, handles
dependencies (DAG), runs tests, and generates documentation. In medallion architecture
terms, dbt models typically implement the Silver and Gold layers.

---

## 18. Exercises

### Exercise 1: Star Schema Design

Design a star schema for a ride-sharing company (e.g., Uber/Lyft). Identify:
- The business process (trips).
- The grain (one row per trip).
- At least four dimensions (date, rider, driver, location).
- At least five additive measures (fare, tip, distance, duration, surge multiplier).

Write the CREATE TABLE statements for all tables.

### Exercise 2: SCD2 Implementation

Given this scenario:
- Customer C042 registered on 2023-01-10 in Berlin, segment "B2C".
- On 2024-03-15, the customer moved to Munich.
- On 2025-01-20, the customer's segment changed to "B2B".

Write the SQL statements to implement SCD2 for both changes. Show the final state of
`dim_customer` for customer C042 (all three rows with correct effective dates).

### Exercise 3: Bus Matrix

Create an enterprise bus matrix for an e-commerce company with these business processes:
- Online orders
- In-store orders
- Returns
- Customer support tickets
- Marketing email campaigns
- Inventory snapshots

Identify at least 8 dimensions and mark which processes use which dimensions.

### Exercise 4: Fact Table Type Selection

For each of the following scenarios, identify the correct fact table type (transaction,
periodic snapshot, or accumulating snapshot) and justify your choice:

1. A bank records every deposit and withdrawal.
2. A bank needs to know the daily balance of every account.
3. A hospital tracks patient admissions through intake → diagnosis → treatment → discharge.
4. An e-commerce company records every click on its website.
5. A telecommunications company measures daily active subscribers per plan.

### Exercise 5: Anti-Pattern Detection

Review the following schema and identify at least three anti-patterns:

```sql
CREATE TABLE sales (
  sale_date       DATE,
  customer_email  VARCHAR(200),
  product_name    VARCHAR(200),
  category_name   VARCHAR(100),
  quantity         INT,
  price            NUMERIC(10,2),
  total            NUMERIC(12,2),
  daily_total      NUMERIC(14,2),
  customer_city    VARCHAR(100)
);
```

Propose a corrected star schema design.

### Exercise 6: Conformed Dimension Validation

Two teams have independently built these customer dimensions:

**Team A (Orders):**
```sql
CREATE TABLE dim_customer_orders (
  cust_key INT, cust_id VARCHAR(20), name TEXT, segment VARCHAR(20), city TEXT
);
```

**Team B (Support):**
```sql
CREATE TABLE dim_customer_support (
  customer_sk INT, customer_number VARCHAR(20), full_name TEXT,
  tier VARCHAR(20), location TEXT
);
```

Identify the conformance violations and propose a single conformed `dim_customer`.
