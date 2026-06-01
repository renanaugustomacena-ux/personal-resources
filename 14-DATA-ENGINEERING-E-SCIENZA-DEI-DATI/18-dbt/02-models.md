# Modelli dbt

I modelli sono il nucleo di dbt: file SQL che definiscono trasformazioni. Ogni modello produce una relazione (view o table) nel data warehouse. La loro forza sta nella componibilità: ogni modello può riferirsi ad altri con `ref()`, costruendo un grafo di dipendenze automatico.

## Materializzazioni

La materializzazione determina come dbt crea la relazione nel DWH.

### View

Non crea una tabella fisica — ogni query esegue il SQL sottostante in tempo reale. Costo zero di storage, ma ogni query ricalcola.

```sql
{{ config(materialized='view') }}

SELECT * FROM {{ ref('stg_orders') }}
WHERE status = 'completed'
```

Appropriata per: staging models, modelli consultati raramente, trasformazioni semplici.

### Table

Crea una tabella fisica nel DWH. Ogni `dbt run` ricrea la tabella da zero (`DROP + CREATE`).

```sql
{{ config(
    materialized='table',
    post_hook=[
        "ANALYZE {{ this }}",
        "GRANT SELECT ON {{ this }} TO role_analyst"
    ]
) }}

SELECT
    customer_id,
    COUNT(order_id)  AS order_count,
    SUM(net_amount)  AS lifetime_value,
    MIN(order_date)  AS first_order_date,
    MAX(order_date)  AS last_order_date
FROM {{ ref('fct_orders') }}
GROUP BY customer_id
```

Appropriata per: mart models, aggregazioni costose, dati consultati frequentemente.

### Incremental

Aggiunge solo le righe nuove o modificate senza ricreare tutta la tabella. Fondamentale per fact table con milioni di righe.

```sql
{{ config(
    materialized='incremental',
    unique_key='order_id',
    incremental_strategy='merge',     -- merge, delete+insert, append
    on_schema_change='sync_all_columns'
) }}

SELECT
    order_id,
    customer_id,
    net_amount,
    status,
    order_date,
    updated_at
FROM {{ ref('stg_orders') }}

{% if is_incremental() %}
-- Filtra solo righe nuove/modificate
WHERE updated_at > (
    SELECT COALESCE(MAX(updated_at), '1970-01-01'::TIMESTAMPTZ)
    FROM {{ this }}
)
{% endif %}
```

**Strategie incrementali**:

| Strategia | Comportamento | Quando usare |
|-----------|--------------|--------------|
| `append` | Solo INSERT | Dati immutabili (events, logs) |
| `merge` | INSERT + UPDATE | Dati che possono cambiare (orders) |
| `delete+insert` | DELETE per unique_key, poi INSERT | Quando MERGE non è supportato |
| `insert_overwrite` | Sovrascrive partizioni (BigQuery/Spark) | Tabelle partizionate |

### Ephemeral

Non crea nessun oggetto nel DWH — viene inlineata come CTE in tutti i modelli che la referenziano.

```sql
{{ config(materialized='ephemeral') }}

-- Questo SQL diventa una CTE inline nel modello downstream
SELECT
    order_id,
    SUM(quantity * unit_price) AS items_total,
    COUNT(*) AS item_count
FROM {{ ref('stg_order_items') }}
GROUP BY order_id
```

Appropriata per: logica riutilizzabile ma non direttamente consultabile, evita materializzazioni intermedie inutili.

---

## Architettura a Layer

### Layer Staging (stg_)

Accede direttamente alle sorgenti via `source()`. Minima trasformazione: cast dei tipi, rename, dedup, filtraggio null ovvi. Nessuna logica di business.

```sql
-- models/staging/stg_customers.sql
{{ config(materialized='view') }}

WITH source AS (
    SELECT * FROM {{ source('raw', 'customers') }}
),

cleaned AS (
    SELECT
        id::BIGINT                          AS customer_id,
        TRIM(LOWER(email))                  AS email,
        TRIM(first_name)                    AS first_name,
        TRIM(last_name)                     AS last_name,
        phone,
        UPPER(TRIM(country_code))           AS country_code,
        DATE(birth_date)                    AS birth_date,
        created_at::TIMESTAMPTZ             AS created_at,
        updated_at::TIMESTAMPTZ             AS updated_at,
        is_active::BOOLEAN                  AS is_active
    FROM source
    WHERE id IS NOT NULL
      AND email IS NOT NULL
),

deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id
            ORDER BY updated_at DESC NULLS LAST
        ) AS _rn
    FROM cleaned
)

SELECT
    customer_id, email, first_name, last_name,
    phone, country_code, birth_date,
    created_at, updated_at, is_active
FROM deduped
WHERE _rn = 1
```

### Layer Intermediate (int_)

Combina modelli staging, applica logica di business, esegue join. Non accede mai direttamente a `source()`.

```sql
-- models/intermediate/int_orders_enriched.sql
{{ config(materialized='ephemeral') }}

WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),

customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),

products AS (
    SELECT * FROM {{ ref('stg_products') }}
),

order_items AS (
    SELECT * FROM {{ ref('stg_order_items') }}
),

item_aggregates AS (
    SELECT
        order_id,
        COUNT(*)                        AS item_count,
        SUM(quantity)                   AS total_quantity,
        SUM(unit_price * quantity)      AS items_subtotal,
        MAX(unit_price)                 AS max_item_price,
        MIN(unit_price)                 AS min_item_price
    FROM order_items
    GROUP BY order_id
),

enriched AS (
    SELECT
        -- Order fields
        o.order_id,
        o.customer_id,
        o.total_amount          AS net_amount,
        o.currency,
        o.country_code,
        o.status,
        o.created_at,
        o.updated_at,
        
        -- Customer enrichment
        c.email                 AS customer_email,
        c.first_name,
        c.last_name,
        c.country_code          AS customer_country,
        c.is_active             AS customer_is_active,
        
        -- Item aggregates
        ia.item_count,
        ia.total_quantity,
        ia.items_subtotal,
        
        -- Derived fields
        DATE(o.created_at)                              AS order_date,
        DATE_TRUNC('month', o.created_at)::DATE         AS order_month,
        CASE
            WHEN o.total_amount >= 1000 THEN 'high_value'
            WHEN o.total_amount >= 100  THEN 'medium_value'
            ELSE 'low_value'
        END                                             AS order_tier
    FROM orders o
    LEFT JOIN customers c      USING (customer_id)
    LEFT JOIN item_aggregates ia USING (order_id)
)

SELECT * FROM enriched
```

### Layer Mart (fct_, dim_)

Modelli finali per il consumo da BI e analytics. Usano solo `ref()` verso layer staging o intermediate.

```sql
-- models/marts/finance/dim_customer.sql
{{ config(
    materialized='table',
    tags=['mart', 'finance', 'dimension']
) }}

WITH customers AS (
    SELECT * FROM {{ ref('stg_customers') }}
),

order_metrics AS (
    SELECT
        customer_id,
        COUNT(order_id)                                 AS total_orders,
        SUM(net_amount)                                 AS lifetime_value,
        AVG(net_amount)                                 AS avg_order_value,
        MIN(order_date)                                 AS first_order_date,
        MAX(order_date)                                 AS last_order_date,
        MAX(order_date) < CURRENT_DATE - INTERVAL '90 days'
                                                        AS is_churned
    FROM {{ ref('fct_orders') }}
    WHERE status IN ('confirmed', 'shipped', 'delivered')
    GROUP BY customer_id
),

segmented AS (
    SELECT
        c.*,
        COALESCE(om.total_orders, 0)        AS total_orders,
        COALESCE(om.lifetime_value, 0)      AS lifetime_value,
        COALESCE(om.avg_order_value, 0)     AS avg_order_value,
        om.first_order_date,
        om.last_order_date,
        COALESCE(om.is_churned, FALSE)      AS is_churned,
        CASE
            WHEN om.lifetime_value >= 10000             THEN 'vip'
            WHEN om.lifetime_value >= 1000              THEN 'loyal'
            WHEN om.total_orders >= 3                   THEN 'returning'
            WHEN om.total_orders = 1                    THEN 'new'
            ELSE 'prospect'
        END                                             AS customer_segment
    FROM customers c
    LEFT JOIN order_metrics om USING (customer_id)
)

SELECT
    {{ dbt_utils.generate_surrogate_key(['customer_id']) }} AS customer_sk,
    customer_id,
    email,
    first_name,
    last_name,
    CONCAT(first_name, ' ', last_name)  AS full_name,
    country_code,
    birth_date,
    total_orders,
    lifetime_value,
    avg_order_value,
    first_order_date,
    last_order_date,
    is_churned,
    customer_segment,
    is_active,
    created_at,
    updated_at
FROM segmented
```

---

## Schema YML e Documentazione

```yaml
# models/marts/finance/schema.yml
version: 2

models:
  - name: fct_orders
    description: |
      Fact table degli ordini. Granularità: un record per ordine.
      Aggiornata ogni ora con strategia incrementale.
      
      **Attenzione**: gli ordini in stato 'pending' sono inclusi ma
      non contabilizzati nelle metriche finanziarie.
    
    meta:
      owner: "@team-data-engineering"
      sla: "completata entro le 05:00 UTC"
      pii_contains: false
    
    columns:
      - name: order_id
        description: "Identificatore univoco dell'ordine"
        tests: [not_null, unique]
      
      - name: customer_id
        description: "FK verso dim_customer"
        tests:
          - not_null
          - relationships:
              to: ref('dim_customer')
              field: customer_id
      
      - name: net_amount
        description: "Importo netto dell'ordine in EUR"
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"
      
      - name: status
        description: |
          Stato dell'ordine. Valori possibili:
          - pending: in attesa di conferma
          - confirmed: confermato
          - shipped: spedito
          - delivered: consegnato
          - cancelled: cancellato
        tests:
          - accepted_values:
              values: [pending, confirmed, shipped, delivered, cancelled]
      
      - name: order_date
        description: "Data dell'ordine (UTC)"
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= '2020-01-01'"

  - name: dim_customer
    description: "Dimensione cliente con metriche aggregate"
    columns:
      - name: customer_sk
        description: "Surrogate key generata da dbt_utils"
        tests: [not_null, unique]
      - name: customer_segment
        tests:
          - accepted_values:
              values: [vip, loyal, returning, new, prospect]
```

---

## Modelli con Variabili

```sql
-- models/marts/finance/fct_orders_ytd.sql
-- Usa la variabile start_date definita in dbt_project.yml
{{ config(materialized='table') }}

SELECT *
FROM {{ ref('fct_orders') }}
WHERE order_date >= '{{ var("start_date") }}'

{% if var("is_test_run", false) %}
LIMIT 1000  -- In test mode, limita i dati
{% endif %}
```

```bash
# Override delle variabili da CLI
dbt run --vars '{"start_date": "2024-01-01", "is_test_run": true}'
```

---

## Modelli con Macro Condizionali

```sql
-- models/staging/stg_events.sql
-- Gestisce differenze tra adapter (PostgreSQL vs Snowflake vs BigQuery)
{{ config(materialized='view') }}

SELECT
    id                                          AS event_id,
    user_id,
    event_type,
    
    {% if target.type == 'snowflake' %}
    PARSE_JSON(properties)::OBJECT              AS properties,
    {% elif target.type == 'bigquery' %}
    JSON_EXTRACT_SCALAR(properties, '$')        AS properties,
    {% else %}
    properties::JSONB                           AS properties,
    {% endif %}
    
    event_timestamp::TIMESTAMPTZ                AS event_at
FROM {{ source('raw', 'events') }}
WHERE id IS NOT NULL
```

---

## Anti-Pattern da Evitare

```sql
-- ❌ Accesso diretto a tabelle raw senza source()
SELECT * FROM public.orders   -- Rompe il lineage!

-- ✅ Usa sempre source() o ref()
SELECT * FROM {{ source('raw', 'orders') }}
SELECT * FROM {{ ref('stg_orders') }}

-- ❌ Logica di business nel layer staging
{{ config(materialized='view') }}
SELECT
    id,
    -- SBAGLIATO: staging non dovrebbe calcolare lifetime_value
    SUM(amount) OVER (PARTITION BY customer_id) AS lifetime_value
FROM {{ source('raw', 'orders') }}

-- ✅ Logica nel layer appropriato
-- staging: solo cast e rename
-- intermediate: join e calcoli
-- mart: metriche aggregate per BI

-- ❌ Subquery annidate illeggibili
SELECT *
FROM (SELECT * FROM (SELECT * FROM orders WHERE ...) WHERE ...) WHERE ...

-- ✅ CTE named con intenzione chiara
WITH filtered_orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
    WHERE status != 'cancelled'
),
enriched AS (
    SELECT o.*, c.email FROM filtered_orders o LEFT JOIN ... c
)
SELECT * FROM enriched
```
