# Business Intelligence — Platforms, Architecture, and Security

## Table of Contents

1. [BI Architecture](#1-bi-architecture)
2. [Self-Service BI Platforms](#2-self-service-bi-platforms)
3. [Enterprise BI](#3-enterprise-bi)
4. [Semantic Layer](#4-semantic-layer)
5. [Data Modeling for BI](#5-data-modeling-for-bi)
6. [Performance Optimization](#6-performance-optimization)
7. [Security and Access Control](#7-security-and-access-control)
8. [Embedded Analytics](#8-embedded-analytics)
9. [BI Security Risks](#9-bi-security-risks)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. BI Architecture

### The BI Data Flow

The canonical BI architecture follows a layered pipeline:

```
Source Systems → Extract/Load → Data Warehouse → Semantic Layer → BI Tool → End User
     ↓                              ↓                  ↓              ↓
 OLTP DBs            Staging     Star/Snowflake    Metrics API    Dashboards
 SaaS APIs           Raw Zone    OLAP Cubes        LookML         Reports
 Event Streams       Clean Zone  Materialized      dbt metrics    Ad-hoc
 Files/Logs                      Views                            Alerts
```

The critical separation: **operational systems** (OLTP) never serve analytical queries directly. The warehouse exists to isolate analytical workloads from transactional systems, transform data into analysis-friendly structures, and provide a historical record optimized for aggregation.

### OLAP Concepts

**Online Analytical Processing (OLAP)** structures data around:

- **Dimensions** — categorical attributes by which you slice data (time, geography, product, customer segment). Dimensions answer "by what?" questions.
- **Measures** — quantitative values that are aggregated (revenue, count of orders, average session duration). Measures answer "how much?" questions.
- **Facts** — events or transactions recorded at a grain (one row per order line item, one row per page view). Facts sit at the intersection of dimensions.
- **Grain** — the level of detail in a fact table. "One row represents one ___." Getting grain wrong ruins everything downstream.

**OLAP operations:**
- **Roll-up** — aggregate from day to month to quarter
- **Drill-down** — disaggregate from region to city to store
- **Slice** — fix one dimension (show only Q4 2025)
- **Dice** — fix multiple dimensions (Q4 2025, EMEA, enterprise segment)
- **Pivot** — rotate axes (swap rows and columns)

### Star Schema vs Snowflake Schema

**Star schema:**
```sql
-- Central fact table surrounded by denormalized dimension tables
CREATE TABLE fact_sales (
    sale_id         BIGINT PRIMARY KEY,
    date_key        INT REFERENCES dim_date(date_key),
    product_key     INT REFERENCES dim_product(product_key),
    customer_key    INT REFERENCES dim_customer(customer_key),
    store_key       INT REFERENCES dim_store(store_key),
    quantity        INT NOT NULL,
    unit_price      DECIMAL(10,2) NOT NULL,
    discount_amount DECIMAL(10,2) DEFAULT 0,
    net_revenue     DECIMAL(12,2) NOT NULL
);

CREATE TABLE dim_product (
    product_key     INT PRIMARY KEY,
    product_id      VARCHAR(20) NOT NULL,   -- natural key
    product_name    VARCHAR(200) NOT NULL,
    category        VARCHAR(100),
    subcategory     VARCHAR(100),
    brand           VARCHAR(100),
    supplier_name   VARCHAR(200),           -- denormalized
    supplier_country VARCHAR(60)            -- denormalized
);
```

Star schemas denormalize dimensions for query simplicity. One JOIN between fact and dimension. BI tools love this — fewer joins means faster queries and simpler data models in the tool.

**Snowflake schema:**
```sql
-- Dimension tables normalized into sub-dimensions
CREATE TABLE dim_product (
    product_key     INT PRIMARY KEY,
    product_id      VARCHAR(20) NOT NULL,
    product_name    VARCHAR(200) NOT NULL,
    subcategory_key INT REFERENCES dim_subcategory(subcategory_key),
    brand_key       INT REFERENCES dim_brand(brand_key)
);

CREATE TABLE dim_subcategory (
    subcategory_key INT PRIMARY KEY,
    subcategory_name VARCHAR(100),
    category_key    INT REFERENCES dim_category(category_key)
);
```

Snowflake schemas reduce storage redundancy but increase JOIN complexity. Use when dimension tables are genuinely large and update-heavy, otherwise prefer star schemas for BI workloads.

### Slowly Changing Dimensions (SCD)

Dimensions change over time. How you handle that change defines your SCD type:

| Type | Strategy | Use Case |
|------|----------|----------|
| Type 0 | Never update | Reference data (country codes) |
| Type 1 | Overwrite old value | Corrections, non-historical attributes |
| Type 2 | Add new row with versioning | Full history required |
| Type 3 | Add column for previous value | Limited history (current + previous only) |
| Type 4 | Separate history table | High-change dimensions |
| Type 6 | Hybrid (1+2+3) | Current + historical + previous |

**SCD Type 2 implementation:**
```sql
CREATE TABLE dim_customer (
    customer_key    INT PRIMARY KEY,          -- surrogate key
    customer_id     VARCHAR(20) NOT NULL,     -- natural/business key
    customer_name   VARCHAR(200),
    segment         VARCHAR(50),
    region          VARCHAR(100),
    effective_date  DATE NOT NULL,
    expiry_date     DATE DEFAULT '9999-12-31',
    is_current      BOOLEAN DEFAULT TRUE
);

-- When customer changes segment:
UPDATE dim_customer 
SET expiry_date = CURRENT_DATE - INTERVAL '1 day', is_current = FALSE
WHERE customer_id = 'CUST-001' AND is_current = TRUE;

INSERT INTO dim_customer (customer_key, customer_id, customer_name, segment, region, effective_date)
VALUES (nextval('customer_seq'), 'CUST-001', 'Acme Corp', 'Enterprise', 'EMEA', CURRENT_DATE);
```

### Push vs Pull BI

**Pull BI (traditional):** Users go to the BI tool, open dashboards, write queries. The BI tool pulls data on demand from the warehouse.

**Push BI (modern):** Insights delivered proactively. Alerts, scheduled report delivery, anomaly detection, embedded KPIs in operational tools (Slack, email, CRM). Data reaches users where they work.

```yaml
# Example: Push BI alert configuration (Metabase-style)
alert:
  name: "Revenue Drop Alert"
  question_id: 142
  condition:
    type: "falls_below"
    threshold: 50000
  channels:
    - type: slack
      channel: "#revenue-alerts"
    - type: email
      recipients: ["finance-team@company.com"]
  schedule:
    frequency: hourly
    timezone: "UTC"
```

Modern architectures combine both: dashboards for exploration (pull), alerts and embedded metrics for action (push).

### Semantic Layers in the Architecture

The semantic layer sits between the warehouse and BI tools, providing:

- **Metric definitions** — single source of truth for "what is revenue?" across all tools
- **Access control** — who can query what
- **Performance** — pre-aggregation, caching
- **Abstraction** — shield users from raw table complexity

```
Data Warehouse → Semantic Layer (Cube / dbt metrics / LookML) → Multiple BI Tools
                      ↕                                              ↕
              Metric definitions                              Consistent numbers
              Access policies                                 regardless of tool
              Pre-aggregations
```

Without a semantic layer, each BI tool defines its own metrics, leading to "whose numbers are right?" debates.

---

## 2. Self-Service BI Platforms

### Metabase

Open-source BI designed for simplicity. Non-technical users can explore data through a point-and-click interface without writing SQL.

**Architecture:**
```
Browser → Metabase App (Java/Clojure) → Database Driver → Warehouse
              ↓
         H2/Postgres (metadata DB)
```

**Docker deployment:**
```yaml
# docker-compose.yml
version: '3.8'
services:
  metabase:
    image: metabase/metabase:v0.49.6
    container_name: metabase
    ports:
      - "3000:3000"
    environment:
      MB_DB_TYPE: postgres
      MB_DB_DBNAME: metabase_app
      MB_DB_PORT: 5432
      MB_DB_USER: metabase
      MB_DB_PASS: "${METABASE_DB_PASSWORD}"
      MB_DB_HOST: postgres
      MB_ENCRYPTION_SECRET_KEY: "${MB_ENCRYPTION_KEY}"
      MB_SITE_URL: "https://bi.company.com"
      MB_EMBEDDING_SECRET_KEY: "${MB_EMBEDDING_KEY}"
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 5

  postgres:
    image: postgres:16-alpine
    container_name: metabase_db
    environment:
      POSTGRES_DB: metabase_app
      POSTGRES_USER: metabase
      POSTGRES_PASSWORD: "${METABASE_DB_PASSWORD}"
    volumes:
      - metabase_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U metabase"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  metabase_data:
```

**Key concepts:**

- **Questions** — saved queries (SQL or GUI-built). Each question produces a visualization.
- **Models** — curated datasets that act as virtual tables. Models abstract complexity from end users. Define in the GUI or via SQL.
- **Collections** — organizational folders with permission inheritance.
- **Sandboxing** — row-level security via user attributes mapped to filter conditions (Pro/Enterprise).

**Metabase Models:**
```sql
-- Model definition: cleaned, joined, business-ready
SELECT
    o.id AS order_id,
    o.created_at AS order_date,
    c.name AS customer_name,
    c.segment,
    p.category AS product_category,
    oi.quantity,
    oi.unit_price * oi.quantity AS line_total,
    CASE 
        WHEN o.status = 'completed' THEN 'Completed'
        WHEN o.status = 'refunded' THEN 'Refunded'
        ELSE 'In Progress'
    END AS order_status
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
WHERE o.created_at >= '2024-01-01'
```

**Embedding (Pro/Enterprise):**
```javascript
// Signed embedding — server-side token generation
const jwt = require('jsonwebtoken');

function generateEmbedUrl(questionId, params, userPermissions) {
    const payload = {
        resource: { question: questionId },
        params: params,                    // locked parameter values
        exp: Math.floor(Date.now() / 1000) + (10 * 60) // 10 min expiry
    };
    
    const token = jwt.sign(payload, process.env.MB_EMBEDDING_KEY);
    return `${process.env.METABASE_URL}/embed/question/${token}`;
}

// Usage: embed with locked filters
const url = generateEmbedUrl(42, { customer_id: req.user.customerId }, {});
```

### Apache Superset

Open-source enterprise-grade BI. SQL-first, supports 40+ databases, rich visualization library. Backed by the Apache Software Foundation.

**Deployment with Helm:**
```yaml
# values.yaml for Kubernetes deployment
supersetNode:
  replicaCount: 3
  resources:
    requests:
      cpu: "2"
      memory: "4Gi"
    limits:
      cpu: "4"
      memory: "8Gi"

supersetWorker:
  replicaCount: 2

postgresql:
  enabled: true
  auth:
    password: "${SUPERSET_DB_PASSWORD}"

redis:
  enabled: true
  auth:
    password: "${REDIS_PASSWORD}"

configOverrides:
  secret: |
    SECRET_KEY = '${SUPERSET_SECRET_KEY}'
    
  enable_feature_flags: |
    FEATURE_FLAGS = {
        "DASHBOARD_RBAC": True,
        "EMBEDDED_SUPERSET": True,
        "ALERT_REPORTS": True,
        "DASHBOARD_CROSS_FILTERS": True,
        "ENABLE_TEMPLATE_PROCESSING": True,
    }
    
  security: |
    from flask_appbuilder.security.manager import AUTH_OAUTH
    AUTH_TYPE = AUTH_OAUTH
    OAUTH_PROVIDERS = [
        {
            'name': 'keycloak',
            'token_key': 'access_token',
            'icon': 'fa-key',
            'remote_app': {
                'client_id': '${KEYCLOAK_CLIENT_ID}',
                'client_secret': '${KEYCLOAK_CLIENT_SECRET}',
                'api_base_url': 'https://auth.company.com/realms/bi/protocol/openid-connect/',
                'access_token_url': 'https://auth.company.com/realms/bi/protocol/openid-connect/token',
                'authorize_url': 'https://auth.company.com/realms/bi/protocol/openid-connect/auth',
                'server_metadata_url': 'https://auth.company.com/realms/bi/.well-known/openid-configuration',
                'client_kwargs': {'scope': 'openid email profile'},
            }
        }
    ]
```

**Superset RBAC:**
```python
# superset_config.py — Role-based access control
from superset.security import SupersetSecurityManager

class CustomSecurityManager(SupersetSecurityManager):
    def get_schema_perm(self, database, schema):
        """Control schema-level access."""
        return f"[{database}].[{schema}]"

# Role definitions via CLI
# superset fab create-role -n "Sales_Analyst"
# superset fab add-role-permissions -r "Sales_Analyst" \
#   --permissions "datasource_access" "database_access" \
#   --resources "[warehouse].[sales_schema]" "[warehouse].(id:1)"
```

**SQL Lab features:**
- Query autocomplete with schema awareness
- Query history and saved queries
- Result set visualization inline
- Jinja templating in queries:

```sql
-- Jinja-templated query in Superset SQL Lab
SELECT 
    date_trunc('{{ time_grain }}', order_date) AS period,
    {{ metrics | join(', ') }},
    {{ dimensions | join(', ') }}
FROM {{ table }}
WHERE order_date BETWEEN '{{ from_dttm }}' AND '{{ to_dttm }}'
{% if filter_values('region') %}
    AND region IN ({{ filter_values('region') | where_in }})
{% endif %}
GROUP BY 1, {{ range(3, dimensions|length + 3) | join(', ') }}
```

### Lightdash

dbt-native BI. Reads your dbt project directly — metrics, descriptions, and relationships defined in dbt YAML become the BI layer.

```yaml
# dbt model YAML that Lightdash reads
version: 2
models:
  - name: orders
    description: "Order fact table — one row per order"
    meta:
      lightdash:
        joins:
          - join: customers
            sql_on: ${orders.customer_id} = ${customers.customer_id}
    columns:
      - name: order_id
        description: "Primary key"
        meta:
          dimension:
            type: string
            hidden: true
      - name: order_date
        description: "Date the order was placed"
        meta:
          dimension:
            type: date
            time_intervals: ['DAY', 'WEEK', 'MONTH', 'QUARTER', 'YEAR']
      - name: revenue
        description: "Net revenue after discounts and refunds"
        meta:
          metrics:
            total_revenue:
              type: sum
              label: "Total Revenue"
              format: "usd"
            average_order_value:
              type: average
              label: "Average Order Value"
              format: "usd"
      - name: status
        description: "Order status"
        meta:
          dimension:
            type: string
```

### Redash

Query-based BI. Write SQL, visualize results, assemble dashboards. Minimal abstraction layer — suited for teams comfortable with SQL.

```python
# Redash API — programmatic dashboard management
import requests

REDASH_URL = "https://redash.company.com"
API_KEY = os.environ["REDASH_API_KEY"]

headers = {"Authorization": f"Key {API_KEY}"}

# Create a query
query_payload = {
    "name": "Daily Revenue by Region",
    "query": """
        SELECT 
            date_trunc('day', order_date) AS day,
            region,
            SUM(revenue) AS daily_revenue
        FROM analytics.orders
        WHERE order_date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY 1, 2
        ORDER BY 1 DESC
    """,
    "data_source_id": 1,
    "schedule": {"interval": 3600, "until": None}  # refresh hourly
}

response = requests.post(
    f"{REDASH_URL}/api/queries",
    json=query_payload,
    headers=headers
)
```

### Platform Comparison

| Feature | Metabase | Superset | Lightdash | Redash |
|---------|----------|----------|-----------|--------|
| SQL required | No (optional) | Mostly yes | No (dbt-native) | Yes |
| Semantic layer | Models (basic) | Datasets | dbt metrics | None |
| Embedding | Pro/Enterprise | Yes (config) | Limited | None |
| RBAC | Pro/Enterprise | Built-in | Built-in | Basic |
| Scale | Small-medium | Large | Medium | Small-medium |
| Data governance | Limited | Moderate | dbt-based | Minimal |
| License | AGPL (OSS) / Commercial | Apache 2.0 | MIT / Commercial | BSD |
| Best for | Non-technical users | SQL-heavy teams | dbt shops | Quick SQL viz |

---

## 3. Enterprise BI

### Tableau

The dominant visual analytics platform. Strength: exploration speed, visual grammar based on Leland Wilkinson's "Grammar of Graphics."

**LOD (Level of Detail) Expressions:**
```
// FIXED — compute at specified granularity regardless of viz level
{ FIXED [Customer ID] : SUM([Revenue]) }

// INCLUDE — add a dimension to the computation
{ INCLUDE [Order ID] : AVG([Discount]) }

// EXCLUDE — remove a dimension from the computation  
{ EXCLUDE [Region] : SUM([Revenue]) }

// Example: Customer's first purchase date (regardless of what's in the viz)
{ FIXED [Customer ID] : MIN([Order Date]) }

// Example: Percent of total revenue per category
SUM([Revenue]) / { FIXED : SUM([Revenue]) }

// Example: Running distinct count at a different grain
{ FIXED [Date] : COUNTD([Customer ID]) }
```

**Tableau Data Modeling (multi-table):**
- **Relationships** (preferred) — logical layer connections. Tableau generates optimized JOINs at query time based on what fields are used. No fanout/duplication issues.
- **Joins** — physical layer. Explicit LEFT/INNER/FULL joins. Risk of row duplication with many-to-many.
- **Blends** — cross-data-source linkage. Left join semantics with the primary data source.

**Tableau Server architecture:**
```
Client → Load Balancer → Gateway
                           ↓
         ┌─────────────────┼─────────────────┐
         ↓                 ↓                 ↓
   VizQL Server      Data Server      Backgrounder
   (renders viz)    (manages cache)   (extract refresh,
                                       subscriptions)
         ↓                 ↓
    Cache Server      File Store
    (Redis/ext)       (extracts)
         ↓
   Repository (PostgreSQL — internal metadata)
```

### Power BI

Microsoft's BI stack. Deep integration with Azure, Office 365, and the Microsoft ecosystem. DAX (Data Analysis Expressions) is the formula language.

**DAX patterns:**
```dax
// Time intelligence — Year-over-Year growth
Revenue YoY% = 
VAR CurrentRevenue = [Total Revenue]
VAR PriorYearRevenue = CALCULATE([Total Revenue], SAMEPERIODLASTYEAR('Date'[Date]))
RETURN
    DIVIDE(CurrentRevenue - PriorYearRevenue, PriorYearRevenue)

// Running total
Running Total = 
CALCULATE(
    [Total Revenue],
    FILTER(
        ALL('Date'[Date]),
        'Date'[Date] <= MAX('Date'[Date])
    )
)

// Dynamic ranking
Product Rank = 
RANKX(
    ALL('Product'[Product Name]),
    [Total Revenue],
    ,
    DESC,
    Dense
)

// Row-Level Security DAX filter
[Region] = LOOKUPVALUE(
    'UserRegionMapping'[Region],
    'UserRegionMapping'[UserEmail],
    USERPRINCIPALNAME()
)
```

**Power BI Composite Models:**
```
DirectQuery tables (real-time) ──┐
                                 ├─→ Single semantic model
Import tables (cached)      ────┘

// Use cases:
// - Large fact tables via DirectQuery (avoid import size limits)
// - Small dimension tables imported for performance
// - Aggregation tables imported, detail tables via DirectQuery
```

**Row-Level Security (Power BI):**
```dax
-- Role: "Regional Manager"
-- DAX filter on the Sales table:
[Region] = LOOKUPVALUE(
    SecurityTable[Region],
    SecurityTable[Email],
    USERPRINCIPALNAME()
)

-- Role: "Department Head" — multiple allowed values
CONTAINS(
    FILTER(
        SecurityMapping,
        SecurityMapping[UserEmail] = USERPRINCIPALNAME()
    ),
    SecurityMapping[Department],
    Sales[Department]
)
```

### Looker (Google Cloud)

LookML-centric BI. The semantic layer IS the product — all metrics, dimensions, and relationships defined in code (version-controlled).

**LookML example:**
```lookml
# orders.view.lkml
view: orders {
  sql_table_name: analytics.fact_orders ;;

  dimension: order_id {
    primary_key: yes
    type: number
    sql: ${TABLE}.order_id ;;
  }

  dimension_group: created {
    type: time
    timeframes: [raw, date, week, month, quarter, year]
    sql: ${TABLE}.created_at ;;
  }

  dimension: status {
    type: string
    sql: ${TABLE}.status ;;
  }

  dimension: is_completed {
    type: yesno
    sql: ${status} = 'completed' ;;
  }

  measure: total_revenue {
    type: sum
    sql: ${TABLE}.revenue ;;
    value_format_name: usd
    drill_fields: [order_id, created_date, customer.name, total_revenue]
  }

  measure: average_order_value {
    type: average
    sql: ${TABLE}.revenue ;;
    value_format_name: usd
    filters: [is_completed: "yes"]
  }

  measure: order_count {
    type: count_distinct
    sql: ${order_id} ;;
  }

  measure: revenue_per_customer {
    type: number
    sql: ${total_revenue} / NULLIF(${customer.customer_count}, 0) ;;
    value_format_name: usd
  }
}

# model file — defines explores (queryable datasets)
explore: orders {
  join: customers {
    type: left_outer
    relationship: many_to_one
    sql_on: ${orders.customer_id} = ${customers.customer_id} ;;
  }
  
  join: products {
    type: left_outer
    relationship: many_to_one
    sql_on: ${orders.product_id} = ${products.product_id} ;;
  }

  # Access control
  access_filter: {
    field: customers.region
    user_attribute: allowed_regions
  }
}
```

**Persistent Derived Tables (PDTs):**
```lookml
view: customer_lifetime_value {
  derived_table: {
    sql:
      SELECT
        customer_id,
        COUNT(DISTINCT order_id) AS order_count,
        SUM(revenue) AS lifetime_revenue,
        MIN(created_at) AS first_order_date,
        MAX(created_at) AS last_order_date,
        DATEDIFF('day', MIN(created_at), MAX(created_at)) AS customer_tenure_days
      FROM analytics.fact_orders
      WHERE status = 'completed'
      GROUP BY 1
    ;;
    datagroup_trigger: daily_etl    # rebuild when ETL completes
    indexes: ["customer_id"]
  }

  dimension: customer_id { primary_key: yes }
  dimension: order_count { type: number }
  measure: avg_lifetime_value {
    type: average
    sql: ${TABLE}.lifetime_revenue ;;
  }
}
```

### Qlik

Associative engine — instead of pre-defined JOINs, Qlik loads all tables and dynamically resolves associations at query time. Users click any value in any field and instantly see related data across all tables highlight.

**Strengths:** Exploratory analysis where users don't know what they're looking for. The associative model reveals unexpected connections.
**Weakness:** Data governance — without a semantic layer, metric definitions can proliferate.

### Total Cost of Ownership Comparison

| Factor | Tableau | Power BI | Looker | Qlik |
|--------|---------|----------|--------|------|
| Per-user/month (Creator) | ~$70 | ~$10 (Pro) / $20 (Premium) | Contact sales | ~$30 |
| Per-user/month (Viewer) | ~$15 | Free (Pro sharing) / $10 | Contact sales | ~$15 |
| Server infrastructure | Self-hosted or Cloud | Cloud (included) | Cloud (GCP) | Cloud or on-prem |
| Data prep included | Tableau Prep | Dataflows | dbt (separate) | Qlik Data Integration |
| Governance tooling | Moderate | Power BI Premium | Strong (LookML) | Moderate |
| Hidden costs | Extract storage, Prep licenses | Premium capacity for large orgs | BigQuery compute | RAM-based pricing |
| Lock-in risk | Moderate (proprietary viz) | Low (M365 ecosystem) | High (LookML) | Moderate |

---

## 4. Semantic Layer

### What Is a Semantic Layer and Why

A semantic layer is an abstraction that maps physical database schemas to business concepts. It provides:

1. **Single source of truth** — "Revenue" means one thing, defined once, used everywhere
2. **Decoupling** — BI tools don't need to know table structures
3. **Governance** — centralized access control and metric definitions
4. **Performance** — pre-aggregation and caching between warehouse and consumers
5. **Consistency** — regardless of which tool queries the data, results are identical

Without a semantic layer, organizations end up with "metric sprawl" — 14 different definitions of "active user" across 6 dashboards in 3 tools.

### dbt Metrics / MetricFlow

MetricFlow (acquired by dbt Labs) defines metrics as code alongside your dbt models:

```yaml
# models/metrics/revenue_metrics.yml
semantic_models:
  - name: orders
    defaults:
      agg_time_dimension: order_date
    model: ref('fact_orders')
    entities:
      - name: order_id
        type: primary
      - name: customer_id
        type: foreign
    dimensions:
      - name: order_date
        type: time
        type_params:
          time_granularity: day
      - name: region
        type: categorical
      - name: channel
        type: categorical
    measures:
      - name: revenue
        agg: sum
        expr: net_revenue
      - name: order_count
        agg: count
        expr: order_id
      - name: customers
        agg: count_distinct
        expr: customer_id

metrics:
  - name: revenue
    type: simple
    label: "Total Revenue"
    description: "Sum of net revenue from completed orders"
    type_params:
      measure: revenue
    filter: |
      {{ Dimension('orders__status') }} = 'completed'

  - name: revenue_per_customer
    type: derived
    label: "Revenue per Customer"
    type_params:
      expr: revenue / customers
      metrics:
        - name: revenue
        - name: customers

  - name: revenue_growth
    type: derived
    label: "Revenue Growth %"
    type_params:
      expr: (current_revenue - prior_revenue) / prior_revenue
      metrics:
        - name: current_revenue
          offset_window: 0
          filter: |
            {{ TimeDimension('orders__order_date', 'month') }} = ...
        - name: prior_revenue
          offset_window: 1
```

**Querying MetricFlow:**
```bash
# CLI
mf query --metrics revenue,order_count \
         --group-by metric_time__month,region \
         --where "region = 'EMEA'" \
         --order metric_time__month

# API (dbt Cloud Semantic Layer API)
# POST /api/v1/semantic-layer/query
{
  "metrics": ["revenue", "revenue_per_customer"],
  "group_by": ["metric_time__week", "channel"],
  "where": [
    {"dimension": "region", "operator": "=", "value": "APAC"}
  ],
  "limit": 100
}
```

### Cube.js

Headless BI / semantic layer as an API. Cube defines a data model and exposes it via REST, GraphQL, or SQL APIs that any BI tool or application can consume.

**Cube data model:**
```javascript
// schema/Orders.js
cube('Orders', {
  sql: `SELECT * FROM analytics.fact_orders`,
  
  preAggregations: {
    // Pre-computed rollup for fast queries
    revenueByDay: {
      measures: [CUBE.totalRevenue, CUBE.orderCount],
      dimensions: [CUBE.region, CUBE.channel],
      timeDimension: CUBE.createdAt,
      granularity: 'day',
      partitionGranularity: 'month',
      refreshKey: {
        every: '1 hour',
        sql: `SELECT MAX(updated_at) FROM analytics.fact_orders`
      },
      indexes: {
        regionIndex: { columns: [CUBE.region] }
      }
    }
  },

  joins: {
    Customers: {
      relationship: 'belongsTo',
      sql: `${CUBE}.customer_id = ${Customers}.customer_id`
    }
  },

  measures: {
    totalRevenue: {
      type: 'sum',
      sql: 'net_revenue',
      format: 'currency'
    },
    orderCount: {
      type: 'count'
    },
    averageOrderValue: {
      type: 'number',
      sql: `${totalRevenue} / NULLIF(${orderCount}, 0)`,
      format: 'currency'
    }
  },

  dimensions: {
    id: {
      sql: 'order_id',
      type: 'number',
      primaryKey: true
    },
    status: {
      sql: 'status',
      type: 'string'
    },
    region: {
      sql: 'region',
      type: 'string'
    },
    channel: {
      sql: 'channel',
      type: 'string'
    },
    createdAt: {
      sql: 'created_at',
      type: 'time'
    }
  },

  segments: {
    completedOrders: {
      sql: `${CUBE}.status = 'completed'`
    }
  }
});
```

**Cube security context:**
```javascript
// cube.js configuration — multi-tenant security
module.exports = {
  contextToAppId: ({ securityContext }) => 
    `CUBE_APP_${securityContext.tenantId}`,
  
  scheduledRefreshContexts: async () => {
    const tenants = await fetchActiveTenants();
    return tenants.map(t => ({ securityContext: { tenantId: t.id } }));
  },

  queryRewrite: (query, { securityContext }) => {
    // Enforce tenant isolation at query level
    if (!securityContext.tenantId) {
      throw new Error('Tenant context required');
    }
    
    query.filters.push({
      member: 'Orders.tenantId',
      operator: 'equals',
      values: [securityContext.tenantId]
    });

    // Role-based metric access
    if (!securityContext.roles.includes('finance')) {
      const restricted = ['Orders.costOfGoods', 'Orders.margin'];
      query.measures = query.measures.filter(m => !restricted.includes(m));
    }
    
    return query;
  }
};
```

### Headless BI Pattern

Headless BI decouples the semantic/metric layer from the visualization layer:

```
                    ┌─→ Custom React dashboards
Semantic Layer API ─┼─→ Metabase / Superset (SQL interface to semantic layer)
                    ├─→ Jupyter notebooks
                    ├─→ Slack bots
                    └─→ Embedded analytics in SaaS product
```

**Benefits:**
- Metrics stay consistent across all surfaces
- Frontend teams choose their own visualization approach
- Mobile, CLI, chatbot — all consume the same metric definitions
- The semantic layer becomes infrastructure, not a BI tool feature

**Cube as headless BI API:**
```bash
# REST API query
curl -X POST https://cube.company.com/cubejs-api/v1/load \
  -H "Authorization: Bearer ${CUBE_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "measures": ["Orders.totalRevenue"],
    "dimensions": ["Orders.region"],
    "timeDimensions": [{
      "dimension": "Orders.createdAt",
      "granularity": "month",
      "dateRange": "last 6 months"
    }],
    "filters": [{
      "member": "Orders.status",
      "operator": "equals",
      "values": ["completed"]
    }]
  }'
```

### Semantic Layer Security

Access control in the semantic layer enforces who sees which metrics:

```yaml
# Cube — role-based dimension/measure visibility
cube('Revenue', {
  # ...
  measures: {
    grossRevenue: {
      type: 'sum',
      sql: 'gross_revenue',
      # Only finance and executives can see this
      public: false,  # hidden from API discovery
    },
    netRevenue: {
      type: 'sum',
      sql: 'net_revenue',
    }
  }
});

# queryRewrite enforces at runtime:
# - Tenant isolation (multi-tenant SaaS)
# - Role-based measure filtering
# - Row-level filtering via dimension constraints
```

---

## 5. Data Modeling for BI

### Kimball Methodology

Ralph Kimball's dimensional modeling approach remains the gold standard for BI-optimized data warehouses. Core principles:

1. **Business process first** — model around business processes (sales, inventory, claims), not departments
2. **Declare the grain** — the most atomic level of data in each fact table
3. **Identify dimensions** — the "by" in every analytical question
4. **Identify facts** — the measurable, numeric, additive values
5. **Bus architecture** — shared/conformed dimensions across fact tables enable cross-process analysis

### Fact Table Types

**Transaction fact tables:**
```sql
-- One row per transaction event at the most atomic grain
CREATE TABLE fact_order_lines (
    order_line_id   BIGINT PRIMARY KEY,
    order_id        BIGINT NOT NULL,
    date_key        INT REFERENCES dim_date(date_key),
    product_key     INT REFERENCES dim_product(product_key),
    customer_key    INT REFERENCES dim_customer(customer_key),
    promotion_key   INT REFERENCES dim_promotion(promotion_key),
    -- Facts (measures)
    quantity        INT NOT NULL,
    unit_price      DECIMAL(10,2) NOT NULL,
    discount_pct    DECIMAL(5,2) DEFAULT 0,
    net_amount      DECIMAL(12,2) NOT NULL,
    cost_amount     DECIMAL(12,2) NOT NULL,
    -- Degenerate dimension (no separate dim table needed)
    invoice_number  VARCHAR(30)
);
```

**Periodic snapshot fact tables:**
```sql
-- One row per entity per time period — captures state at regular intervals
CREATE TABLE fact_inventory_daily (
    date_key            INT REFERENCES dim_date(date_key),
    product_key         INT REFERENCES dim_product(product_key),
    warehouse_key       INT REFERENCES dim_warehouse(warehouse_key),
    -- Semi-additive facts (can SUM across products/warehouses, NOT across time)
    quantity_on_hand    INT NOT NULL,
    quantity_on_order   INT NOT NULL,
    reorder_point       INT NOT NULL,
    days_of_supply      DECIMAL(6,1),
    -- Fully additive
    units_received      INT DEFAULT 0,
    units_shipped       INT DEFAULT 0,
    PRIMARY KEY (date_key, product_key, warehouse_key)
);
```

**Accumulating snapshot fact tables:**
```sql
-- One row per entity lifecycle — tracks milestones
CREATE TABLE fact_order_fulfillment (
    order_id            BIGINT PRIMARY KEY,
    -- Milestone date keys
    order_date_key      INT REFERENCES dim_date(date_key),
    payment_date_key    INT REFERENCES dim_date(date_key),
    ship_date_key       INT REFERENCES dim_date(date_key),
    delivery_date_key   INT REFERENCES dim_date(date_key),
    return_date_key     INT REFERENCES dim_date(date_key),
    -- Lag measures (days between milestones)
    order_to_payment_days   INT,
    payment_to_ship_days    INT,
    ship_to_delivery_days   INT,
    -- Facts
    order_amount        DECIMAL(12,2),
    shipping_cost       DECIMAL(8,2),
    current_status      VARCHAR(20)
);
-- Updated as each milestone is reached (unlike transaction facts which are insert-only)
```

### Dimension Table Patterns

**Junk dimensions — collect low-cardinality flags:**
```sql
-- Instead of 8 boolean dimension tables or degenerate dimensions
CREATE TABLE dim_order_flags (
    flag_key        INT PRIMARY KEY,
    is_rush_order   BOOLEAN,
    is_gift_wrapped BOOLEAN,
    is_first_order  BOOLEAN,
    payment_method  VARCHAR(20),  -- 'credit_card', 'paypal', 'wire'
    shipping_tier   VARCHAR(20),  -- 'standard', 'express', 'overnight'
    order_source    VARCHAR(20)   -- 'web', 'mobile', 'phone', 'pos'
);
-- Pre-populate all valid combinations. Fact table references flag_key.
```

**Degenerate dimensions — dimension with no attributes beyond the key:**
```sql
-- Invoice number, order number, transaction ID
-- Live directly in the fact table (no separate dim table)
-- The dimension IS the key value itself
```

**Conformed dimensions — shared across fact tables (bus architecture):**
```sql
-- dim_date is the canonical conformed dimension
CREATE TABLE dim_date (
    date_key            INT PRIMARY KEY,        -- YYYYMMDD format
    full_date           DATE NOT NULL UNIQUE,
    day_of_week         SMALLINT,               -- 1=Monday
    day_name            VARCHAR(10),
    day_of_month        SMALLINT,
    day_of_year         SMALLINT,
    week_of_year        SMALLINT,
    iso_week            SMALLINT,
    month_number        SMALLINT,
    month_name          VARCHAR(10),
    quarter             SMALLINT,
    year                SMALLINT,
    fiscal_quarter      SMALLINT,
    fiscal_year         SMALLINT,
    is_weekend          BOOLEAN,
    is_holiday          BOOLEAN,
    holiday_name        VARCHAR(50)
);

-- dim_customer used by: fact_orders, fact_support_tickets, fact_web_sessions
-- Same customer_key everywhere → cross-process analysis possible
```

### Bus Architecture Matrix

```
                    dim_date  dim_customer  dim_product  dim_store  dim_employee
fact_orders           ✓          ✓             ✓           ✓
fact_inventory        ✓                        ✓           ✓
fact_returns          ✓          ✓             ✓           ✓
fact_web_sessions     ✓          ✓
fact_support_tickets  ✓          ✓                                     ✓
```

Each `✓` represents a conformed dimension shared across business processes. This matrix guides incremental warehouse development — build one fact table at a time, reusing conformed dimensions.

---

## 6. Performance Optimization

### Materialized Views

```sql
-- PostgreSQL materialized view for dashboard queries
CREATE MATERIALIZED VIEW mv_daily_revenue AS
SELECT
    d.full_date,
    d.month_name,
    d.quarter,
    d.fiscal_year,
    p.category AS product_category,
    c.segment AS customer_segment,
    s.region,
    COUNT(DISTINCT f.order_id) AS order_count,
    SUM(f.net_revenue) AS total_revenue,
    AVG(f.net_revenue) AS avg_order_value,
    COUNT(DISTINCT f.customer_key) AS unique_customers
FROM fact_sales f
JOIN dim_date d ON f.date_key = d.date_key
JOIN dim_product p ON f.product_key = p.product_key
JOIN dim_customer c ON f.customer_key = c.customer_key
JOIN dim_store s ON f.store_key = s.store_key
GROUP BY 1, 2, 3, 4, 5, 6, 7
WITH DATA;

-- Concurrent refresh (no lock on reads during refresh)
CREATE UNIQUE INDEX idx_mv_daily_revenue 
ON mv_daily_revenue (full_date, product_category, customer_segment, region);

REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_revenue;

-- Schedule refresh
-- (via pg_cron or external scheduler)
SELECT cron.schedule(
    'refresh_daily_revenue',
    '0 */2 * * *',  -- every 2 hours
    'REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_revenue'
);
```

### Pre-Aggregation Strategies

**Cube pre-aggregations:**
```javascript
cube('Orders', {
  // ...
  preAggregations: {
    // Rollup — materialized summary table
    revenueByRegionDaily: {
      measures: [CUBE.totalRevenue, CUBE.orderCount, CUBE.uniqueCustomers],
      dimensions: [CUBE.region, CUBE.channel, CUBE.productCategory],
      timeDimension: CUBE.createdAt,
      granularity: 'day',
      partitionGranularity: 'month',
      buildRangeStart: { sql: `SELECT DATE_SUB(NOW(), INTERVAL 2 YEAR)` },
      buildRangeEnd: { sql: `SELECT NOW()` },
      refreshKey: {
        every: '30 minutes',
        incremental: true,
        updateWindow: '7 days'  // only refresh last 7 days
      },
      indexes: {
        main: { columns: [CUBE.region, CUBE.createdAt] }
      }
    },
    
    // Original SQL — for complex queries that don't fit rollups
    complexMetrics: {
      type: 'originalSql',
      timeDimension: CUBE.createdAt,
      partitionGranularity: 'day',
      refreshKey: { every: '1 hour' }
    }
  }
});
```

**Tableau extracts:**
- `.hyper` format — columnar, compressed, indexed
- Scheduled refresh from live connection
- Aggregation at extract time: `Aggregate data for visible dimensions`
- Extract filters reduce dataset size

**Power BI aggregation tables:**
```dax
// Aggregation table pattern in Power BI
// 1. Import a summarized agg table (fast, in-memory)
// 2. Detail table stays in DirectQuery (real-time, large)
// 3. Power BI automatically routes queries to appropriate table

// Agg table covers: Sum of Revenue by Date, Product Category, Region
// Detail table: individual transactions
// User drills down → automatic fallback to DirectQuery detail
```

### Query Caching

```python
# Superset caching configuration
CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 60 * 60 * 24,  # 24 hours
    'CACHE_KEY_PREFIX': 'superset_results_',
    'CACHE_REDIS_URL': 'redis://redis:6379/0',
}

# Per-dataset cache timeout
DATA_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 60 * 60,  # 1 hour default
    'CACHE_KEY_PREFIX': 'superset_data_',
    'CACHE_REDIS_URL': 'redis://redis:6379/1',
}

# Dashboard-level cache
FILTER_STATE_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache', 
    'CACHE_DEFAULT_TIMEOUT': 60 * 60 * 8,
    'CACHE_KEY_PREFIX': 'superset_filter_',
    'CACHE_REDIS_URL': 'redis://redis:6379/2',
}
```

### Partition Pruning

```sql
-- BigQuery partitioned table — BI queries only scan relevant partitions
CREATE TABLE analytics.fact_events
PARTITION BY DATE(event_timestamp)
CLUSTER BY user_id, event_type
AS SELECT * FROM raw.events;

-- Query with partition filter → scans only matching partitions
SELECT event_type, COUNT(*) 
FROM analytics.fact_events
WHERE event_timestamp BETWEEN '2025-01-01' AND '2025-01-31'
GROUP BY 1;
-- Without the date filter → full table scan (expensive!)

-- Snowflake automatic clustering
ALTER TABLE analytics.fact_orders
CLUSTER BY (order_date, region);
-- Snowflake re-clusters data in the background for optimal pruning
```

### Incremental Refresh

```sql
-- dbt incremental model — only process new/changed rows
{{
  config(
    materialized='incremental',
    unique_key='event_id',
    incremental_strategy='merge',
    partition_by={
      "field": "event_date",
      "data_type": "date",
      "granularity": "day"
    }
  )
}}

SELECT
    event_id,
    event_date,
    user_id,
    event_type,
    properties,
    _loaded_at
FROM {{ source('raw', 'events') }}

{% if is_incremental() %}
WHERE _loaded_at > (SELECT MAX(_loaded_at) FROM {{ this }})
{% endif %}
```

### Columnar Storage Benefits for BI

BI queries are typically:
- Read-heavy (no updates during analysis)
- Aggregation-focused (`SUM`, `COUNT`, `AVG` over millions of rows)
- Column-selective (use 5-10 columns out of 50+)

Columnar storage (Parquet, ORC, BigQuery, Redshift, Snowflake, ClickHouse) excels because:

| Advantage | Why It Matters for BI |
|-----------|----------------------|
| Only reads needed columns | Dashboard query touching 5/50 cols reads 10% of data |
| Better compression | Same-type values compress 5-10x better together |
| Vectorized execution | CPU processes columns as arrays, not row-by-row |
| Min/max statistics | Skip entire blocks that can't match filters |
| Late materialization | Don't construct full rows until after filtering |

---

## 7. Security and Access Control

### Row-Level Security (RLS) Implementation

**PostgreSQL RLS (native):**
```sql
-- Enable RLS on the table
ALTER TABLE analytics.fact_sales ENABLE ROW LEVEL SECURITY;

-- Policy: users see only their region's data
CREATE POLICY region_isolation ON analytics.fact_sales
    FOR SELECT
    USING (
        region = current_setting('app.user_region')
        OR current_setting('app.user_role') = 'admin'
    );

-- Force RLS even for table owners
ALTER TABLE analytics.fact_sales FORCE ROW LEVEL SECURITY;

-- Set context per session (application sets this before queries)
SET app.user_region = 'EMEA';
SET app.user_role = 'analyst';
```

**Metabase sandboxing (Enterprise):**
```json
// Metabase sandbox configuration via API
{
  "id": 1,
  "group_id": 5,
  "table_id": 12,
  "card_id": null,
  "attribute_remappings": {
    "region": ["dimension", ["field", 45, null]]
  }
}
// Group 5 (EMEA Analysts) only sees rows where region matches
// their "region" user attribute
```

**Superset RLS:**
```python
# superset_config.py or via Admin → Security → Row Level Security
# Pattern: regex on table name → SQL clause → mapped to roles

# Via API:
{
    "name": "tenant_isolation",
    "description": "Multi-tenant row isolation",
    "filter_type": "Regular",
    "tables": [{"id": 5}, {"id": 12}, {"id": 18}],
    "roles": [{"id": 3}],  # "Tenant User" role
    "group_key": "tenant_id",
    "clause": "tenant_id = '{{current_user_id()}}'"
}
```

**Cube RLS via queryRewrite:**
```javascript
queryRewrite: (query, { securityContext }) => {
    const { tenantId, department, role } = securityContext;
    
    // Mandatory tenant isolation
    if (tenantId) {
        query.filters.push({
            member: 'Base.tenantId',
            operator: 'equals',
            values: [tenantId]
        });
    }
    
    // Department-level filtering for non-admins
    if (role !== 'admin' && department) {
        query.filters.push({
            member: 'Base.department',
            operator: 'equals',
            values: [department]
        });
    }
    
    return query;
}
```

### Column-Level Security

```sql
-- PostgreSQL: grant/revoke column access
REVOKE ALL ON analytics.dim_customer FROM analyst_role;
GRANT SELECT (customer_id, segment, region, signup_date) 
    ON analytics.dim_customer TO analyst_role;
-- analyst_role cannot see: email, phone, address, ssn

-- View-based column masking
CREATE VIEW analytics.customer_safe AS
SELECT 
    customer_id,
    segment,
    region,
    signup_date,
    '***' || RIGHT(email, 4) AS email_masked,
    CASE WHEN current_setting('app.user_role') = 'admin'
         THEN phone
         ELSE 'XXX-XXX-' || RIGHT(phone, 4)
    END AS phone
FROM analytics.dim_customer;
```

**Power BI Object-Level Security (OLS):**
```json
// model.bim — restrict table/column visibility per role
{
  "roles": [
    {
      "name": "SalesTeam",
      "tablePermissions": [
        {
          "name": "FactSales",
          "metadataPermission": "read"
        },
        {
          "name": "FactCosts",
          "metadataPermission": "none"  // hidden from this role
        }
      ],
      "columnPermissions": [
        {
          "tableName": "DimCustomer",
          "columnName": "Email",
          "metadataPermission": "none"
        }
      ]
    }
  ]
}
```

### Data Masking in Reports

```sql
-- Dynamic masking based on user context
CREATE FUNCTION mask_pii(value TEXT, user_role TEXT) 
RETURNS TEXT AS $$
BEGIN
    IF user_role IN ('admin', 'compliance') THEN
        RETURN value;
    ELSIF user_role = 'support' THEN
        -- Partial mask: show first/last characters
        RETURN LEFT(value, 2) || REPEAT('*', LENGTH(value) - 4) || RIGHT(value, 2);
    ELSE
        RETURN REPEAT('*', LENGTH(value));
    END IF;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Snowflake dynamic masking policy
CREATE MASKING POLICY email_mask AS (val STRING) RETURNS STRING ->
    CASE 
        WHEN CURRENT_ROLE() IN ('ADMIN', 'COMPLIANCE') THEN val
        WHEN CURRENT_ROLE() = 'ANALYST' THEN REGEXP_REPLACE(val, '.+@', '***@')
        ELSE '****@****.***'
    END;

ALTER TABLE dim_customer MODIFY COLUMN email 
    SET MASKING POLICY email_mask;
```

### SSO / SAML / OIDC Integration

```yaml
# Metabase SAML configuration (Enterprise)
# Environment variables:
MB_SAML_ENABLED: "true"
MB_SAML_IDENTITY_PROVIDER_URI: "https://idp.company.com/saml/metadata"
MB_SAML_IDENTITY_PROVIDER_ISSUER: "https://idp.company.com"
MB_SAML_IDENTITY_PROVIDER_CERTIFICATE: "/certs/idp-signing.pem"
MB_SAML_APPLICATION_NAME: "Metabase BI"
MB_SAML_KEYSTORE_PATH: "/certs/metabase-keystore.jks"
MB_SAML_KEYSTORE_PASSWORD: "${SAML_KEYSTORE_PASSWORD}"
MB_SAML_KEYSTORE_ALIAS: "metabase"
MB_SAML_ATTRIBUTE_EMAIL: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress"
MB_SAML_ATTRIBUTE_FIRSTNAME: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname"
MB_SAML_ATTRIBUTE_LASTNAME: "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname"
MB_SAML_GROUP_SYNC: "true"
MB_SAML_ATTRIBUTE_GROUP: "memberOf"
MB_SAML_GROUP_MAPPINGS: '{"cn=bi-admins,ou=groups,dc=company,dc=com": [1], "cn=analysts,ou=groups,dc=company,dc=com": [4]}'
```

```python
# Superset OIDC configuration
from flask_appbuilder.security.manager import AUTH_OAUTH

AUTH_TYPE = AUTH_OAUTH
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = "Viewer"  # default role for new users

OAUTH_PROVIDERS = [{
    'name': 'azure',
    'token_key': 'access_token',
    'icon': 'fa-windows',
    'remote_app': {
        'client_id': os.environ['AZURE_CLIENT_ID'],
        'client_secret': os.environ['AZURE_CLIENT_SECRET'],
        'api_base_url': 'https://graph.microsoft.com/v1.0/',
        'access_token_url': f'https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token',
        'authorize_url': f'https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize',
        'client_kwargs': {
            'scope': 'openid email profile User.Read',
        },
        'server_metadata_url': f'https://login.microsoftonline.com/{TENANT_ID}/v2.0/.well-known/openid-configuration',
    }
}]

# Map Azure AD groups to Superset roles
AUTH_ROLES_MAPPING = {
    "bi-admins": ["Admin"],
    "bi-analysts": ["Alpha", "sql_lab"],
    "bi-viewers": ["Gamma"],
}
AUTH_ROLES_SYNC_AT_LOGIN = True
```

### Audit Logging

```sql
-- PostgreSQL audit trigger for BI access tracking
CREATE TABLE audit.bi_query_log (
    log_id          BIGSERIAL PRIMARY KEY,
    query_timestamp TIMESTAMPTZ DEFAULT NOW(),
    username        TEXT NOT NULL,
    source_ip       INET,
    bi_tool         TEXT,           -- 'metabase', 'superset', 'direct'
    query_text      TEXT,
    tables_accessed TEXT[],
    rows_returned   BIGINT,
    execution_ms    INT,
    was_cached      BOOLEAN DEFAULT FALSE
);

-- pgAudit extension for comprehensive logging
ALTER SYSTEM SET pgaudit.log = 'read';
ALTER SYSTEM SET pgaudit.log_catalog = off;
ALTER SYSTEM SET pgaudit.log_relation = on;

-- Superset audit via event logger
class CustomEventLogger(AbstractEventLogger):
    def log(self, user_id, action, dashboard_id, slice_id, json_payload, **kwargs):
        AuditLog.objects.create(
            user_id=user_id,
            action=action,
            resource_type='dashboard' if dashboard_id else 'chart',
            resource_id=dashboard_id or slice_id,
            metadata=json_payload,
            ip_address=request.remote_addr,
            timestamp=datetime.utcnow()
        )

EVENT_LOGGER = CustomEventLogger()
```

### Multi-Tenancy

```javascript
// Cube multi-tenant architecture
module.exports = {
  // Each tenant gets isolated pre-aggregations
  contextToAppId: ({ securityContext }) => 
    `CUBEJS_APP_${securityContext.tenantId}`,
  
  // Tenant-specific database connections
  driverFactory: ({ securityContext }) => {
    const tenant = securityContext.tenantId;
    return {
      type: 'postgres',
      host: process.env[`DB_HOST_${tenant}`] || process.env.DB_HOST,
      database: `analytics_${tenant}`,
      user: process.env.DB_USER,
      password: process.env.DB_PASSWORD,
    };
  },

  // Schema compilation per tenant
  repositoryFactory: ({ securityContext }) => ({
    dataSchemaFiles: () => [
      // Shared schemas
      ...loadSharedSchemas(),
      // Tenant-specific overrides
      ...loadTenantSchemas(securityContext.tenantId)
    ]
  })
};
```

---

## 8. Embedded Analytics

### Metabase Embedding

**Interactive embedding (Pro/Enterprise):**
```javascript
// Server-side: generate embed URL with SSO
const metabaseApi = require('./metabase-client');

async function getEmbedUrl(user, dashboardId) {
    // Authenticate as the user via SSO
    const session = await metabaseApi.authenticateUser({
        email: user.email,
        first_name: user.firstName,
        last_name: user.lastName,
        groups: user.biGroups,        // maps to Metabase groups
        attributes: {
            tenant_id: user.tenantId,  // for sandboxing
            region: user.region
        }
    });
    
    return {
        iframeUrl: `${METABASE_URL}/embed/dashboard/${dashboardId}`,
        token: session.token
    };
}

// Client-side: render embedded dashboard
// <iframe 
//   src="${iframeUrl}#token=${token}&bordered=false&titled=false"
//   width="100%" 
//   height="800"
//   frameborder="0"
// />
```

**Static embedding (signed JWT, all editions):**
```javascript
const jwt = require('jsonwebtoken');

function createStaticEmbed(resourceType, resourceId, params = {}) {
    const payload = {
        resource: { [resourceType]: resourceId },
        params: params,  // locked parameters (user can't change)
        exp: Math.floor(Date.now() / 1000) + (60 * 10)  // 10 min
    };
    
    const token = jwt.sign(payload, process.env.METABASE_EMBEDDING_SECRET);
    return `${process.env.METABASE_URL}/embed/${resourceType}/${token}#bordered=false&titled=true`;
}

// Multi-tenant: lock tenant_id parameter
const embedUrl = createStaticEmbed('dashboard', 7, {
    tenant_id: currentUser.tenantId  // user cannot override
});
```

### Superset Embedded

```python
# Superset embedded dashboard configuration
# superset_config.py

FEATURE_FLAGS = {
    "EMBEDDED_SUPERSET": True,
    "EMBEDDABLE_CHARTS": True,
}

# Guest token endpoint for embedded access
GUEST_ROLE_NAME = "EmbeddedViewer"
GUEST_TOKEN_JWT_SECRET = os.environ["SUPERSET_GUEST_SECRET"]
GUEST_TOKEN_JWT_EXP = 300  # 5 minutes
GUEST_TOKEN_HEADER_NAME = "X-GuestToken"

# Row-level security for embedded users
EMBEDDED_RLS_RULES = [
    {
        "dataset": "orders",
        "clause": "tenant_id = '{{ current_guest_user.tenant_id }}'",
    }
]
```

```javascript
// Client-side: Superset embedded SDK
import { embedDashboard } from '@superset-ui/embedded-sdk';

async function renderDashboard(containerId, dashboardId, user) {
    // Fetch guest token from your backend
    const response = await fetch('/api/bi/guest-token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            dashboard_id: dashboardId,
            user_context: {
                tenant_id: user.tenantId,
                role: user.role
            }
        })
    });
    const { guestToken } = await response.json();

    embedDashboard({
        id: dashboardId,
        supersetDomain: 'https://superset.company.com',
        mountPoint: document.getElementById(containerId),
        fetchGuestToken: () => guestToken,
        dashboardUiConfig: {
            hideTitle: true,
            hideChartControls: false,
            filters: {
                visible: true,
                expanded: false
            }
        }
    });
}
```

### Tableau Embedded Analytics

```javascript
// Tableau Embedding API v3 (current)
import { TableauViz } from '@tableau/embedding-api';

const viz = new TableauViz();
viz.src = 'https://tableau.company.com/views/SalesDashboard/Overview';
viz.token = await getTableauJWT(currentUser);  // Connected App JWT
viz.toolbar = 'hidden';
viz.hideTabs = true;

// Apply filters based on user context
viz.addEventListener('firstinteractive', () => {
    const sheet = viz.workbook.activeSheet;
    sheet.applyFilterAsync('Region', [currentUser.region], 'replace');
    sheet.applyFilterAsync('Tenant', [currentUser.tenantId], 'replace');
});

document.getElementById('tableau-container').appendChild(viz);

// Server-side: Generate Connected App JWT
function generateTableauJWT(user) {
    const payload = {
        iss: process.env.TABLEAU_CONNECTED_APP_CLIENT_ID,
        sub: user.email,
        aud: 'tableau',
        exp: Math.floor(Date.now() / 1000) + 600,
        jti: crypto.randomUUID(),
        scp: ['tableau:views:embed', 'tableau:metrics:embed']
    };
    
    return jwt.sign(payload, process.env.TABLEAU_CONNECTED_APP_SECRET, {
        algorithm: 'HS256',
        header: {
            kid: process.env.TABLEAU_CONNECTED_APP_SECRET_ID,
            iss: process.env.TABLEAU_CONNECTED_APP_CLIENT_ID
        }
    });
}
```

### Security Considerations for Embedded Analytics

| Risk | Mitigation |
|------|-----------|
| Token theft | Short expiry (5-10 min), audience validation, IP binding |
| Parameter tampering | Server-side locked params, never trust client-side filters alone |
| Data leakage via browser tools | RLS enforced at database/semantic layer, not just UI filters |
| Session fixation | Rotate tokens, bind to session ID |
| Clickjacking | X-Frame-Options: ALLOW-FROM, CSP frame-ancestors |
| Cross-tenant access | Mandatory tenant isolation in RLS, validated server-side |

```javascript
// Secure token generation pattern
function generateSecureEmbedToken(user, resource) {
    // Validate user has access to this resource
    if (!canAccess(user, resource)) {
        throw new AuthorizationError('User lacks permission');
    }

    const token = jwt.sign({
        sub: user.id,
        tenant: user.tenantId,
        resource: resource,
        permissions: user.biPermissions,
        // Security fields
        iss: 'bi-service',
        aud: 'embedded-bi',
        iat: Math.floor(Date.now() / 1000),
        exp: Math.floor(Date.now() / 1000) + 300,  // 5 min max
        jti: crypto.randomUUID(),  // prevent replay
        // Bind to session
        sid: user.sessionId
    }, process.env.EMBED_SIGNING_KEY, { algorithm: 'ES256' });
    
    return token;
}
```

### White-Labeling and Custom Themes

```css
/* Metabase white-labeling (Enterprise) */
/* Applied via Admin → Appearance */
:root {
    --mb-color-brand: #1a365d;
    --mb-color-brand-light: #2d5a9e;
    --mb-font-family: 'Inter', sans-serif;
}

/* Superset custom theme via environment */
/* SUPERSET_THEME_OVERRIDES in superset_config.py */
THEME_OVERRIDES = {
    "colors": {
        "primary": {"base": "#1a365d"},
        "secondary": {"base": "#4a90d9"},
        "error": {"base": "#dc2626"},
        "warning": {"base": "#f59e0b"},
        "success": {"base": "#10b981"},
    },
    "typography": {
        "families": {
            "sansSerif": "'Inter', 'Helvetica Neue', sans-serif",
            "monospace": "'JetBrains Mono', monospace",
        }
    }
}
```

---

## 9. BI Security Risks

### SQL Injection Through BI Tools

BI tools that allow user-authored SQL (Superset SQL Lab, Redash, Metabase native queries) are injection surfaces:

```sql
-- Vulnerable: Superset Jinja template with unvalidated input
SELECT * FROM orders WHERE region = '{{ filter_values("region")[0] }}'
-- Attacker sets filter to: ' OR 1=1; DROP TABLE orders; --

-- Mitigated: parameterized approach
SELECT * FROM orders WHERE region = %(region)s
-- or in Superset Jinja:
SELECT * FROM orders WHERE region = {{ filter_values("region")[0] | sqlsafe }}
```

**Attack vectors:**
- Custom SQL in calculated fields
- User-defined parameters passed to raw queries
- Template injection in Jinja-enabled dashboards
- URL parameter injection in embedded dashboards

**Mitigations:**
```python
# Superset: disable dangerous Jinja functions
JINJA_CONTEXT_ADDONS = {}  # don't add unsafe functions
CUSTOM_TEMPLATE_PROCESSORS = {}

# Restrict SQL Lab permissions
# Only give sql_lab role to trusted users
# Use READ-ONLY database connections for BI
# Create dedicated BI service accounts with SELECT-only grants

# PostgreSQL: BI service account
CREATE ROLE bi_reader LOGIN PASSWORD '${BI_DB_PASSWORD}';
GRANT CONNECT ON DATABASE analytics TO bi_reader;
GRANT USAGE ON SCHEMA public, analytics TO bi_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO bi_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT SELECT ON TABLES TO bi_reader;
-- NEVER grant INSERT, UPDATE, DELETE, CREATE, DROP to BI accounts
```

### Data Leakage via Exports

```python
# Superset: control export capabilities
FEATURE_FLAGS = {
    "ALLOW_DASHBOARD_DOMAIN_SHARDING": True,
    # Disable CSV download for sensitive dashboards
    "DASHBOARD_DOWNLOAD_CSV": False,
}

# Per-role export control
# Disable "Download as CSV/Excel" for viewer roles
# Audit all export events
class ExportAuditHook:
    def on_export(self, user, resource_type, resource_id, export_format):
        audit_log.info(
            f"EXPORT: user={user.username} resource={resource_type}:{resource_id} "
            f"format={export_format} ip={request.remote_addr} "
            f"timestamp={datetime.utcnow().isoformat()}"
        )
        # Alert on bulk exports
        if self.is_bulk_export(user, timeframe_minutes=60):
            security_alert.send(
                f"Bulk export detected: {user.username} exported "
                f"{self.recent_export_count(user)} resources in 60 min"
            )
```

**Screenshot/screen recording risks:**
- Watermarking dashboards with user email (visible in screenshots)
- Session recording detection (enterprise DLP)
- Limiting data density per view (force drill-down for detail)

### Privilege Escalation in BI Platforms

Common escalation paths:

1. **Metabase:** Collection permission inheritance bypass — moving a dashboard to a less-restricted collection
2. **Superset:** Role stacking — user inherits multiple roles, gaining unintended access unions
3. **Tableau:** Project permissions vs workbook permissions mismatch
4. **Power BI:** Workspace member can publish RLS-bypassing datasets

```python
# Audit script: detect privilege escalation risks in Superset
import requests

def audit_role_stacking(superset_url, admin_token):
    """Detect users with excessive combined permissions."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    users = requests.get(f"{superset_url}/api/v1/security/users", headers=headers).json()
    
    escalation_risks = []
    for user in users['result']:
        user_roles = [r['name'] for r in user['roles']]
        
        # Flag: user has both viewer AND sql_lab (can bypass dashboard filters)
        if 'Gamma' in user_roles and 'sql_lab' in user_roles:
            escalation_risks.append({
                'user': user['username'],
                'risk': 'SQL Lab access bypasses dashboard-level RLS',
                'severity': 'HIGH'
            })
        
        # Flag: user has Admin role plus other roles (unnecessary)
        if 'Admin' in user_roles and len(user_roles) > 1:
            escalation_risks.append({
                'user': user['username'],
                'risk': 'Admin with additional roles — review necessity',
                'severity': 'MEDIUM'
            })
    
    return escalation_risks
```

### API Key Exposure

```bash
# Common exposure vectors:
# 1. Hardcoded in frontend JavaScript
# 2. Committed to git in config files
# 3. Logged in error messages
# 4. Shared in Slack/email

# Detection: scan for exposed BI API keys
grep -r "METABASE_SECRET\|MB_EMBEDDING\|SUPERSET_SECRET\|TABLEAU_TOKEN" \
    --include="*.js" --include="*.ts" --include="*.py" --include="*.env" \
    --include="*.yaml" --include="*.yml" .

# Mitigation: rotate and use secret management
# Vault integration example
vault kv put secret/bi \
    metabase_embedding_key="$(openssl rand -hex 32)" \
    superset_secret_key="$(openssl rand -hex 32)" \
    cube_api_secret="$(openssl rand -hex 32)"
```

### BI Tool CVEs and Hardening

```yaml
# Hardening checklist for Metabase deployment
security_hardening:
  network:
    - bind_to: "127.0.0.1"  # behind reverse proxy only
    - tls: required
    - cors_origins: ["https://app.company.com"]
    
  authentication:
    - disable_local_auth_if_sso: true
    - enforce_mfa: true
    - session_timeout: 3600  # 1 hour
    - max_sessions_per_user: 3
    
  authorization:
    - default_new_user_group: "viewers"  # minimal permissions
    - disable_public_sharing: true
    - disable_embedding_unless_needed: true
    
  data_access:
    - use_read_only_db_connections: true
    - set_query_timeout: 300  # 5 min max query
    - limit_result_rows: 10000
    - disable_native_query_for_non_admins: true
    
  monitoring:
    - enable_audit_log: true
    - alert_on_failed_logins: 5  # per 15 min
    - alert_on_bulk_exports: true
    - monitor_for_cve_updates: true

  updates:
    # Subscribe to security advisories
    - metabase: "https://github.com/metabase/metabase/security/advisories"
    - superset: "https://github.com/apache/superset/security"
```

### Attack Vectors Specific to BI Deployments

| Vector | Description | Severity |
|--------|-------------|----------|
| Semantic layer bypass | Direct DB access bypasses metric-level security | Critical |
| Filter parameter injection | Manipulating URL/API params to see other tenants' data | Critical |
| Cache poisoning | Polluting query cache with manipulated results | High |
| Extract/snapshot theft | Stealing materialized data files from disk/S3 | High |
| Metadata enumeration | Listing all tables/columns to discover sensitive data | Medium |
| Dashboard link sharing | Shared links exposing data beyond intended audience | Medium |
| Scheduled report interception | Email-delivered reports sent to wrong recipients | Medium |
| Cross-tenant aggregation | Aggregate queries leaking other tenants' data in totals | Critical |

---

## 10. Lab Exercises

### Lab 1: Deploy Metabase with PostgreSQL and Implement RLS

**Objective:** Deploy a production-ready Metabase instance with row-level security enforced at the database level.

```yaml
# docker-compose.yml — Lab 1
version: '3.8'
services:
  # Application database (the data to analyze)
  analytics_db:
    image: postgres:16-alpine
    container_name: lab_analytics_db
    environment:
      POSTGRES_DB: analytics
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: "lab_analytics_pass_change_me"
    volumes:
      - ./init-scripts:/docker-entrypoint-initdb.d
      - analytics_data:/var/lib/postgresql/data
    ports:
      - "5433:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admin -d analytics"]
      interval: 5s
      timeout: 3s
      retries: 5

  # Metabase application database
  metabase_db:
    image: postgres:16-alpine
    container_name: lab_metabase_db
    environment:
      POSTGRES_DB: metabase
      POSTGRES_USER: metabase
      POSTGRES_PASSWORD: "lab_metabase_pass_change_me"
    volumes:
      - metabase_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U metabase -d metabase"]
      interval: 5s
      timeout: 3s
      retries: 5

  metabase:
    image: metabase/metabase:v0.49.6
    container_name: lab_metabase
    ports:
      - "3000:3000"
    environment:
      MB_DB_TYPE: postgres
      MB_DB_DBNAME: metabase
      MB_DB_PORT: 5432
      MB_DB_USER: metabase
      MB_DB_PASS: "lab_metabase_pass_change_me"
      MB_DB_HOST: metabase_db
      MB_ENCRYPTION_SECRET_KEY: "lab_encryption_key_32chars_min!!"
    depends_on:
      metabase_db:
        condition: service_healthy
      analytics_db:
        condition: service_healthy

volumes:
  analytics_data:
  metabase_data:
```

```sql
-- init-scripts/01-schema.sql
-- Create the analytical schema with RLS

-- Star schema
CREATE SCHEMA analytics;

CREATE TABLE analytics.dim_region (
    region_id   SERIAL PRIMARY KEY,
    region_name VARCHAR(50) UNIQUE NOT NULL
);

INSERT INTO analytics.dim_region (region_name) VALUES 
('EMEA'), ('APAC'), ('AMER'), ('LATAM');

CREATE TABLE analytics.dim_product (
    product_id   SERIAL PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category     VARCHAR(50) NOT NULL,
    unit_cost    DECIMAL(10,2) NOT NULL
);

CREATE TABLE analytics.fact_sales (
    sale_id     BIGSERIAL PRIMARY KEY,
    sale_date   DATE NOT NULL,
    region_id   INT REFERENCES analytics.dim_region(region_id),
    product_id  INT REFERENCES analytics.dim_product(product_id),
    quantity    INT NOT NULL,
    revenue     DECIMAL(12,2) NOT NULL,
    tenant_id   VARCHAR(20) NOT NULL
);

-- Create BI read-only role
CREATE ROLE bi_reader LOGIN PASSWORD 'bi_reader_pass_change_me';
GRANT CONNECT ON DATABASE analytics TO bi_reader;
GRANT USAGE ON SCHEMA analytics TO bi_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO bi_reader;

-- Enable RLS
ALTER TABLE analytics.fact_sales ENABLE ROW LEVEL SECURITY;
ALTER TABLE analytics.fact_sales FORCE ROW LEVEL SECURITY;

-- RLS policy: filter by tenant_id set in session variable
CREATE POLICY tenant_isolation ON analytics.fact_sales
    FOR SELECT
    USING (
        tenant_id = current_setting('app.tenant_id', true)
        OR current_setting('app.is_admin', true) = 'true'
    );

-- Create per-region policies
CREATE POLICY region_access ON analytics.fact_sales
    FOR SELECT
    USING (
        region_id IN (
            SELECT region_id FROM analytics.dim_region 
            WHERE region_name = ANY(
                string_to_array(current_setting('app.allowed_regions', true), ',')
            )
        )
        OR current_setting('app.is_admin', true) = 'true'
    );
```

```sql
-- init-scripts/02-seed-data.sql
-- Generate test data

INSERT INTO analytics.dim_product (product_name, category, unit_cost) VALUES
('Widget Pro', 'Hardware', 45.00),
('Widget Lite', 'Hardware', 22.50),
('DataSync SaaS', 'Software', 0),
('Support Plan', 'Services', 0),
('Integration Kit', 'Hardware', 120.00);

-- Generate 10K sales records across tenants and regions
INSERT INTO analytics.fact_sales (sale_date, region_id, product_id, quantity, revenue, tenant_id)
SELECT 
    CURRENT_DATE - (random() * 365)::INT,
    (random() * 3 + 1)::INT,
    (random() * 4 + 1)::INT,
    (random() * 50 + 1)::INT,
    (random() * 5000 + 100)::DECIMAL(12,2),
    CASE (random() * 2)::INT 
        WHEN 0 THEN 'tenant_alpha'
        WHEN 1 THEN 'tenant_beta'
        ELSE 'tenant_gamma'
    END
FROM generate_series(1, 10000);
```

**Verification steps:**
1. Connect Metabase to `analytics_db` using `bi_reader` credentials
2. Create a question showing total revenue by region
3. Verify that without session variables, RLS blocks all rows (since `current_setting` returns NULL)
4. Configure Metabase to set session variables via "Additional JDBC connection string options" or use sandboxing

### Lab 2: Security Metrics Dashboard in Superset

**Objective:** Build a dashboard tracking security events (failed logins, permission changes, data exports) using Superset.

```python
# deploy-superset.py — Automated Superset setup for the lab
import subprocess
import os

SUPERSET_CONFIG = """
import os
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'lab-secret-key-change-in-prod')
SQLALCHEMY_DATABASE_URI = 'postgresql://superset:superset_pass@postgres:5432/superset'

FEATURE_FLAGS = {
    "DASHBOARD_RBAC": True,
    "ALERT_REPORTS": True,
    "EMBEDDED_SUPERSET": True,
}

# Security settings
WTF_CSRF_ENABLED = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
TALISMAN_ENABLED = True
"""

# SQL for security events schema
SECURITY_SCHEMA = """
CREATE SCHEMA IF NOT EXISTS security_metrics;

CREATE TABLE security_metrics.auth_events (
    event_id        BIGSERIAL PRIMARY KEY,
    event_timestamp TIMESTAMPTZ DEFAULT NOW(),
    event_type      VARCHAR(50) NOT NULL,  -- login_success, login_failure, mfa_challenge, lockout
    username        VARCHAR(100),
    source_ip       INET,
    user_agent      TEXT,
    geo_country     VARCHAR(3),
    geo_city        VARCHAR(100),
    risk_score      DECIMAL(3,2),  -- 0.00 to 1.00
    session_id      VARCHAR(64)
);

CREATE TABLE security_metrics.access_events (
    event_id        BIGSERIAL PRIMARY KEY,
    event_timestamp TIMESTAMPTZ DEFAULT NOW(),
    actor           VARCHAR(100) NOT NULL,
    action          VARCHAR(50) NOT NULL,  -- view, export, share, modify_permission
    resource_type   VARCHAR(50),           -- dashboard, dataset, query, user
    resource_id     VARCHAR(100),
    resource_name   TEXT,
    details         JSONB,
    was_allowed     BOOLEAN DEFAULT TRUE
);

CREATE TABLE security_metrics.vulnerability_scan (
    scan_id         SERIAL PRIMARY KEY,
    scan_timestamp  TIMESTAMPTZ DEFAULT NOW(),
    scanner         VARCHAR(50),
    target          VARCHAR(200),
    finding_type    VARCHAR(100),
    severity        VARCHAR(20),  -- critical, high, medium, low, info
    cvss_score      DECIMAL(3,1),
    cwe_id          VARCHAR(20),
    description     TEXT,
    remediation     TEXT,
    is_resolved     BOOLEAN DEFAULT FALSE,
    resolved_at     TIMESTAMPTZ
);

-- Indexes for dashboard query performance
CREATE INDEX idx_auth_events_ts ON security_metrics.auth_events(event_timestamp DESC);
CREATE INDEX idx_auth_events_type ON security_metrics.auth_events(event_type);
CREATE INDEX idx_access_events_ts ON security_metrics.access_events(event_timestamp DESC);
CREATE INDEX idx_vuln_severity ON security_metrics.vulnerability_scan(severity, is_resolved);
"""
```

**Dashboard queries:**
```sql
-- Failed login rate (last 24h, by hour)
SELECT 
    date_trunc('hour', event_timestamp) AS hour,
    COUNT(*) FILTER (WHERE event_type = 'login_failure') AS failed,
    COUNT(*) FILTER (WHERE event_type = 'login_success') AS success,
    ROUND(
        COUNT(*) FILTER (WHERE event_type = 'login_failure')::DECIMAL / 
        NULLIF(COUNT(*), 0) * 100, 2
    ) AS failure_rate_pct
FROM security_metrics.auth_events
WHERE event_timestamp > NOW() - INTERVAL '24 hours'
GROUP BY 1
ORDER BY 1;

-- Top data export events (potential exfiltration)
SELECT 
    actor,
    COUNT(*) AS export_count,
    COUNT(DISTINCT resource_id) AS unique_resources,
    array_agg(DISTINCT resource_name ORDER BY resource_name) AS exported_resources
FROM security_metrics.access_events
WHERE action = 'export'
  AND event_timestamp > NOW() - INTERVAL '7 days'
GROUP BY actor
HAVING COUNT(*) > 10
ORDER BY export_count DESC;

-- Open vulnerabilities by severity
SELECT 
    severity,
    COUNT(*) AS open_count,
    AVG(EXTRACT(EPOCH FROM (NOW() - scan_timestamp)) / 86400)::INT AS avg_age_days,
    MAX(cvss_score) AS max_cvss
FROM security_metrics.vulnerability_scan
WHERE is_resolved = FALSE
GROUP BY severity
ORDER BY 
    CASE severity 
        WHEN 'critical' THEN 1 
        WHEN 'high' THEN 2 
        WHEN 'medium' THEN 3 
        WHEN 'low' THEN 4 
        ELSE 5 
    END;

-- Suspicious access patterns (off-hours, unusual geo)
SELECT 
    username,
    source_ip,
    geo_country,
    event_timestamp,
    risk_score
FROM security_metrics.auth_events
WHERE (
    EXTRACT(HOUR FROM event_timestamp AT TIME ZONE 'UTC') NOT BETWEEN 6 AND 22
    OR risk_score > 0.7
    OR geo_country NOT IN (SELECT allowed_country FROM security_metrics.allowed_countries)
)
AND event_timestamp > NOW() - INTERVAL '48 hours'
ORDER BY risk_score DESC;
```

### Lab 3: Dimensional Model and Cube Semantic Layer

**Objective:** Design a dimensional model for an e-commerce platform and expose it via Cube.

```yaml
# cube/docker-compose.yml
version: '3.8'
services:
  cube:
    image: cubejs/cube:v0.35
    container_name: lab_cube
    ports:
      - "4000:4000"    # API
      - "15432:15432"  # SQL API (Postgres protocol)
    environment:
      CUBEJS_DB_TYPE: postgres
      CUBEJS_DB_HOST: analytics_db
      CUBEJS_DB_PORT: 5432
      CUBEJS_DB_NAME: analytics
      CUBEJS_DB_USER: bi_reader
      CUBEJS_DB_PASS: "bi_reader_pass_change_me"
      CUBEJS_API_SECRET: "${CUBE_API_SECRET}"
      CUBEJS_DEV_MODE: "false"
      CUBEJS_CACHE_AND_QUEUE_DRIVER: redis
      CUBEJS_REDIS_URL: "redis://redis:6379"
      CUBEJS_PRE_AGGREGATIONS_SCHEMA: "cube_preaggs"
    volumes:
      - ./schema:/cube/conf/schema
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    container_name: lab_redis
```

```javascript
// schema/Orders.js — Cube schema for e-commerce dimensional model
cube('Orders', {
  sql: `
    SELECT 
      f.sale_id,
      f.sale_date,
      f.quantity,
      f.revenue,
      f.tenant_id,
      r.region_name AS region,
      p.product_name,
      p.category,
      p.unit_cost,
      f.revenue - (p.unit_cost * f.quantity) AS margin
    FROM analytics.fact_sales f
    JOIN analytics.dim_region r ON f.region_id = r.region_id
    JOIN analytics.dim_product p ON f.product_id = p.product_id
  `,

  preAggregations: {
    dailyRevenue: {
      measures: [CUBE.totalRevenue, CUBE.totalMargin, CUBE.orderCount, CUBE.avgOrderValue],
      dimensions: [CUBE.region, CUBE.category],
      timeDimension: CUBE.saleDate,
      granularity: 'day',
      partitionGranularity: 'month',
      refreshKey: {
        every: '1 hour',
        incremental: true,
        updateWindow: '3 days'
      }
    },
    monthlyByProduct: {
      measures: [CUBE.totalRevenue, CUBE.totalQuantity],
      dimensions: [CUBE.productName, CUBE.region],
      timeDimension: CUBE.saleDate,
      granularity: 'month',
      refreshKey: { every: '6 hours' }
    }
  },

  measures: {
    orderCount: {
      type: 'count',
      sql: 'sale_id'
    },
    totalRevenue: {
      type: 'sum',
      sql: 'revenue',
      format: 'currency'
    },
    totalMargin: {
      type: 'sum',
      sql: 'margin',
      format: 'currency'
    },
    totalQuantity: {
      type: 'sum',
      sql: 'quantity'
    },
    avgOrderValue: {
      type: 'avg',
      sql: 'revenue',
      format: 'currency'
    },
    marginPercent: {
      type: 'number',
      sql: `${CUBE.totalMargin} / NULLIF(${CUBE.totalRevenue}, 0) * 100`,
      format: 'percent'
    }
  },

  dimensions: {
    id: {
      sql: 'sale_id',
      type: 'number',
      primaryKey: true
    },
    saleDate: {
      sql: 'sale_date',
      type: 'time'
    },
    region: {
      sql: 'region',
      type: 'string'
    },
    productName: {
      sql: 'product_name',
      type: 'string'
    },
    category: {
      sql: 'category',
      type: 'string'
    },
    tenantId: {
      sql: 'tenant_id',
      type: 'string',
      public: false  // hidden from API discovery, used for security
    }
  },

  segments: {
    highValue: {
      sql: `${CUBE}.revenue > 1000`
    }
  }
});
```

```javascript
// schema/cube.js — Security configuration
module.exports = {
  queryRewrite: (query, { securityContext }) => {
    if (!securityContext || !securityContext.tenantId) {
      throw new Error('Authentication required: tenantId missing');
    }

    // Enforce tenant isolation
    query.filters.push({
      member: 'Orders.tenantId',
      operator: 'equals',
      values: [securityContext.tenantId]
    });

    // Role-based measure restriction
    if (!securityContext.roles?.includes('finance')) {
      const financeMeasures = ['Orders.totalMargin', 'Orders.marginPercent'];
      query.measures = (query.measures || []).filter(
        m => !financeMeasures.includes(m)
      );
    }

    return query;
  },

  contextToAppId: ({ securityContext }) =>
    `CUBE_${securityContext.tenantId}`,

  scheduledRefreshContexts: async () => {
    // Pre-aggregate for each tenant
    return [
      { securityContext: { tenantId: 'tenant_alpha', roles: ['admin'] } },
      { securityContext: { tenantId: 'tenant_beta', roles: ['admin'] } },
      { securityContext: { tenantId: 'tenant_gamma', roles: ['admin'] } },
    ];
  }
};
```

**Verification:**
```bash
# Test the Cube API with tenant isolation
curl -X POST http://localhost:4000/cubejs-api/v1/load \
  -H "Authorization: Bearer eyJ0ZW5hbnRJZCI6InRlbmFudF9hbHBoYSIsInJvbGVzIjpbImFuYWx5c3QiXX0=" \
  -H "Content-Type: application/json" \
  -d '{
    "measures": ["Orders.totalRevenue", "Orders.orderCount"],
    "dimensions": ["Orders.region"],
    "timeDimensions": [{
      "dimension": "Orders.saleDate",
      "granularity": "month",
      "dateRange": "last 6 months"
    }]
  }'

# Verify margin measures are filtered for non-finance roles
curl -X POST http://localhost:4000/cubejs-api/v1/load \
  -H "Authorization: Bearer eyJ0ZW5hbnRJZCI6InRlbmFudF9hbHBoYSIsInJvbGVzIjpbImFuYWx5c3QiXX0=" \
  -H "Content-Type: application/json" \
  -d '{
    "measures": ["Orders.totalMargin"],
    "dimensions": ["Orders.region"]
  }'
# Expected: totalMargin filtered out (empty measures)
```

### Lab 4: Security Assessment of a BI Deployment (Pentest Perspective)

**Objective:** Perform a security assessment of a BI deployment, identifying common vulnerabilities and misconfigurations.

```bash
#!/bin/bash
# bi-security-assessment.sh — Automated BI security checks
# Run from an authorized penetration testing engagement ONLY

set -euo pipefail

BI_URL="${1:?Usage: $0 <bi-tool-url>}"
REPORT_DIR="./bi-assessment-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$REPORT_DIR"

echo "[*] BI Security Assessment — $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "[*] Target: $BI_URL"
echo "[*] Report directory: $REPORT_DIR"

# 1. Information disclosure
echo "[+] Checking information disclosure..."
curl -sk "$BI_URL/api/health" -o "$REPORT_DIR/health.json" 2>/dev/null
curl -sk "$BI_URL/api/session/properties" -o "$REPORT_DIR/session-props.json" 2>/dev/null
curl -sk "$BI_URL/api/util/diagnostic_info/connection_pool_info" -o "$REPORT_DIR/pool-info.json" 2>/dev/null

# 2. Authentication tests
echo "[+] Testing authentication..."
# Default credentials
for cred in "admin@metabase.local:metabase" "admin:admin" "superset:superset"; do
    user="${cred%%:*}"
    pass="${cred##*:}"
    response=$(curl -sk -X POST "$BI_URL/api/session" \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"$user\",\"password\":\"$pass\"}" \
        -w "%{http_code}" -o /dev/null 2>/dev/null)
    if [ "$response" = "200" ]; then
        echo "  [CRITICAL] Default credentials work: $user:$pass"
    fi
done

# 3. API enumeration (unauthenticated)
echo "[+] Checking unauthenticated API access..."
endpoints=(
    "/api/database"
    "/api/card"
    "/api/dashboard"
    "/api/collection"
    "/api/user"
    "/api/table"
    "/api/dataset"
)
for endpoint in "${endpoints[@]}"; do
    status=$(curl -sk -o /dev/null -w "%{http_code}" "$BI_URL$endpoint")
    if [ "$status" = "200" ]; then
        echo "  [HIGH] Unauthenticated access to: $endpoint"
    fi
done

# 4. Header security
echo "[+] Checking security headers..."
headers=$(curl -skI "$BI_URL")
echo "$headers" > "$REPORT_DIR/headers.txt"

check_header() {
    local header="$1"
    if ! echo "$headers" | grep -qi "$header"; then
        echo "  [MEDIUM] Missing header: $header"
    fi
}
check_header "Strict-Transport-Security"
check_header "X-Content-Type-Options"
check_header "X-Frame-Options"
check_header "Content-Security-Policy"
check_header "Referrer-Policy"

# 5. Public sharing check
echo "[+] Checking for public shares..."
# Metabase public links
curl -sk "$BI_URL/api/public/dashboard" -o "$REPORT_DIR/public-dashboards.json" 2>/dev/null
curl -sk "$BI_URL/api/public/card" -o "$REPORT_DIR/public-cards.json" 2>/dev/null

# 6. Version disclosure
echo "[+] Checking version disclosure..."
version=$(curl -sk "$BI_URL/api/health" | grep -o '"version":"[^"]*"' || echo "unknown")
echo "  [INFO] Detected version: $version"

echo "[*] Assessment complete. Review $REPORT_DIR/"
```

```python
# bi_rls_tester.py — Verify RLS enforcement
"""
Test that Row-Level Security actually works by attempting
cross-tenant data access through various vectors.
"""
import requests
import json
from typing import Optional

class BISecurityTester:
    def __init__(self, base_url: str, admin_token: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers['Authorization'] = f'Bearer {admin_token}'
        self.findings = []

    def test_rls_bypass_via_native_query(self, db_id: int, tenant_id: str):
        """Attempt to access other tenants' data via native SQL."""
        payload = {
            "database": db_id,
            "type": "native",
            "native": {
                "query": f"SELECT * FROM analytics.fact_sales WHERE tenant_id != '{tenant_id}' LIMIT 5"
            }
        }
        response = self.session.post(
            f"{self.base_url}/api/dataset",
            json=payload
        )
        result = response.json()
        
        if result.get('data', {}).get('rows', []):
            self.findings.append({
                'severity': 'CRITICAL',
                'title': 'RLS bypass via native query',
                'description': 'Native SQL query returned data from other tenants',
                'evidence': f"Returned {len(result['data']['rows'])} rows from other tenants",
                'cwe': 'CWE-863',
                'remediation': 'Enforce RLS at database level (PostgreSQL policies) '
                              'and restrict native query access to trusted roles only'
            })
        else:
            print("[PASS] RLS enforced — native query cannot access other tenants")

    def test_parameter_tampering(self, dashboard_id: int, param_name: str, 
                                  legit_value: str, tampered_value: str):
        """Test if dashboard parameters can be tampered to bypass filters."""
        # Legitimate request
        legit_response = self.session.get(
            f"{self.base_url}/api/dashboard/{dashboard_id}",
            params={param_name: legit_value}
        )
        
        # Tampered request
        tampered_response = self.session.get(
            f"{self.base_url}/api/dashboard/{dashboard_id}",
            params={param_name: tampered_value}
        )
        
        if tampered_response.status_code == 200:
            # Check if tampered data is actually returned
            self.findings.append({
                'severity': 'HIGH',
                'title': 'Dashboard parameter tampering',
                'description': f'Parameter {param_name} can be overridden by client',
                'evidence': f'Tampered value "{tampered_value}" accepted',
                'cwe': 'CWE-639',
                'remediation': 'Lock parameters server-side in embedded contexts; '
                              'validate parameter values against user permissions'
            })

    def test_export_controls(self, card_id: int):
        """Test if data export bypasses access controls."""
        # Try CSV export
        csv_response = self.session.post(
            f"{self.base_url}/api/card/{card_id}/query/csv",
            json={}
        )
        
        if csv_response.status_code == 200 and len(csv_response.content) > 100:
            # Check row count vs what the user should see
            row_count = csv_response.content.decode().count('\n') - 1
            self.findings.append({
                'severity': 'MEDIUM',
                'title': 'Unrestricted data export',
                'description': f'CSV export returned {row_count} rows — verify RLS applied',
                'evidence': f'{row_count} rows exported from card {card_id}',
                'cwe': 'CWE-200',
                'remediation': 'Verify RLS applies to export queries; '
                              'add export audit logging; restrict export by role'
            })

    def generate_report(self) -> str:
        """Generate findings report."""
        report = {
            'assessment_date': '2025-01-15T14:30:00Z',
            'target': self.base_url,
            'total_findings': len(self.findings),
            'by_severity': {
                'critical': len([f for f in self.findings if f['severity'] == 'CRITICAL']),
                'high': len([f for f in self.findings if f['severity'] == 'HIGH']),
                'medium': len([f for f in self.findings if f['severity'] == 'MEDIUM']),
                'low': len([f for f in self.findings if f['severity'] == 'LOW']),
            },
            'findings': self.findings
        }
        return json.dumps(report, indent=2)


# Usage
if __name__ == '__main__':
    tester = BISecurityTester(
        base_url='http://localhost:3000',
        admin_token='your-session-token'
    )
    
    # Test RLS
    tester.test_rls_bypass_via_native_query(db_id=1, tenant_id='tenant_alpha')
    
    # Test parameter tampering  
    tester.test_parameter_tampering(
        dashboard_id=1,
        param_name='tenant_id',
        legit_value='tenant_alpha',
        tampered_value='tenant_beta'
    )
    
    # Test export controls
    tester.test_export_controls(card_id=42)
    
    # Report
    print(tester.generate_report())
```

**Assessment checklist (pentest deliverable):**

```markdown
## BI Security Assessment Checklist

### Authentication & Authorization
- [ ] Default credentials changed
- [ ] SSO/MFA enforced
- [ ] Session timeout configured (< 8 hours)
- [ ] API tokens have expiry and rotation policy
- [ ] Service accounts use minimal permissions
- [ ] RLS verified at database level (not just BI tool level)

### Network & Infrastructure
- [ ] BI tool not exposed to public internet (or properly firewalled)
- [ ] TLS 1.2+ enforced
- [ ] Security headers present (HSTS, CSP, X-Frame-Options)
- [ ] Database connection encrypted (SSL required)
- [ ] Internal APIs not accessible from BI tool network

### Data Access
- [ ] Read-only database connections for BI
- [ ] Native SQL restricted to trusted roles
- [ ] Query timeout enforced (prevent resource exhaustion)
- [ ] Result row limits configured
- [ ] Export/download audit logged
- [ ] Sensitive columns masked or excluded

### Multi-Tenancy
- [ ] Tenant isolation verified at every layer
- [ ] Cross-tenant queries impossible
- [ ] Shared caches don't leak between tenants
- [ ] Pre-aggregations tenant-aware

### Operational Security
- [ ] BI tool version current (no known CVEs)
- [ ] Audit logging enabled and monitored
- [ ] Backup encryption at rest
- [ ] Secrets in vault (not env vars in container definition)
- [ ] Incident response plan for BI data breach
```

---

## Summary

Business Intelligence architecture spans from data modeling fundamentals (Kimball, star schemas, SCDs) through platform selection (self-service vs enterprise), semantic layers (Cube, dbt metrics, LookML) for metric consistency, and deep security considerations at every layer.

Key takeaways:

- **Model first, tool second.** A well-designed dimensional model serves any BI tool. A poorly designed model makes every tool struggle.
- **Semantic layers prevent metric chaos.** Define once, query everywhere. Without one, organizations inevitably argue about whose numbers are correct.
- **Security is multi-layered.** Database-level RLS + semantic layer filtering + BI tool permissions + network controls. Never rely on a single layer.
- **Performance requires proactive design.** Pre-aggregations, materialized views, columnar storage, and incremental refresh — build these in from the start, not after dashboards are slow.
- **Embedded analytics multiply the attack surface.** Every embedded dashboard is an additional authentication boundary, token management challenge, and data leakage risk.
- **Assess BI deployments like any other web application** — default credentials, injection vectors, information disclosure, and broken access control all apply.
