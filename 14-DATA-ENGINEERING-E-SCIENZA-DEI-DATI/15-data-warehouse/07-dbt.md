# dbt: Data Build Tool

dbt (data build tool) è diventato lo strumento standard per le trasformazioni SQL nel data warehouse moderno. Ha rivoluzionato il lavoro degli analytics engineer portando le best practice dello sviluppo software (version control, test, documentazione, modularity) nel mondo delle query SQL. Con dbt, le trasformazioni sono modelli SQL versionati in git, testabili automaticamente, e documentati con lineage graph.

## Concetti Fondamentali

dbt opera con tre tipi di oggetti:
- **Models**: query SELECT che diventano tabelle o view nel DW
- **Tests**: verifiche sui dati (unicità, not null, referential integrity, custom)
- **Sources**: definizioni delle tabelle sorgente (raw data)

```yaml
# dbt_project.yml: configurazione del progetto

name: 'my_analytics'
version: '1.0.0'
config-version: 2

profile: 'my_analytics'  # riferisce profiles.yml con le credenziali DW

model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

target-path: "target"
clean-targets: ["target", "dbt_packages"]

models:
  my_analytics:
    # Layer staging: view (veloci da creare, no storage)
    staging:
      +materialized: view
      +schema: staging
    
    # Layer intermediate: tabelle effimere o view
    intermediate:
      +materialized: table
      +schema: intermediate
    
    # Layer mart: tabelle materializzate, ottimizzate per BI
    mart:
      +materialized: table
      +schema: mart
      +post-hook: "ANALYZE {{ this }}"  # hook post-creazione
```

```yaml
# profiles.yml: configurazione connessione DW
# ~/.dbt/profiles.yml o nel progetto (non committare le credenziali!)

my_analytics:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: myaccount.eu-central-1
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      private_key_path: "{{ env_var('SNOWFLAKE_PRIVATE_KEY_PATH') }}"
      role: transformer
      database: analytics_dev
      warehouse: dbt_wh
      schema: "dbt_{{ env_var('DBT_USER', 'default') }}"  # schema isolato per dev
      threads: 4
    
    prod:
      type: snowflake
      account: myaccount.eu-central-1
      user: "{{ env_var('SNOWFLAKE_PROD_USER') }}"
      private_key_path: "{{ env_var('SNOWFLAKE_PROD_KEY_PATH') }}"
      role: transformer_prod
      database: analytics_prod
      warehouse: dbt_prod_wh
      schema: public
      threads: 8
```

## Modelli dbt

```sql
-- models/staging/stg_orders.sql
-- Questo modello legge dalla sorgente raw e fa trasformazioni di base

-- La configurazione può essere in-file o nel dbt_project.yml
{{ config(
    materialized='view',
    tags=['staging', 'orders']
) }}

WITH source AS (
    SELECT * FROM {{ source('raw', 'orders') }}  -- riferimento alla source definita
),

renamed AS (
    SELECT
        id::INT AS order_id,
        customer_id::INT,
        created_at AT TIME ZONE 'UTC' AS created_at_utc,
        LOWER(TRIM(status)) AS status,
        COALESCE(total_amount, 0) AS total_amount,
        _loaded_at AS loaded_at
    FROM source
    WHERE id IS NOT NULL
),

deduplicated AS (
    -- Deduplicare per id, mantenendo il record più recente
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY loaded_at DESC) AS rn
    FROM renamed
)

SELECT
    order_id,
    customer_id,
    created_at_utc,
    status,
    total_amount,
    loaded_at
FROM deduplicated
WHERE rn = 1
```

```sql
-- models/intermediate/int_orders_with_items.sql
-- Combina ordini e righe d'ordine

{{ config(materialized='table') }}

WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }}  -- ref() = dipendenza su altro modello
),

order_items AS (
    SELECT * FROM {{ ref('stg_order_items') }}
),

order_metrics AS (
    SELECT
        oi.order_id,
        COUNT(*) AS line_item_count,
        SUM(oi.quantity) AS total_quantity,
        SUM(oi.quantity * oi.unit_price) AS gross_revenue,
        SUM(oi.quantity * oi.unit_price * (1 - COALESCE(oi.discount_pct, 0))) AS net_revenue
    FROM order_items oi
    GROUP BY oi.order_id
)

SELECT
    o.order_id,
    o.customer_id,
    o.created_at_utc,
    o.status,
    m.line_item_count,
    m.total_quantity,
    m.gross_revenue,
    m.net_revenue
FROM orders o
LEFT JOIN order_metrics m ON m.order_id = o.order_id
```

```sql
-- models/mart/fact_sales.sql
-- Fact table finale per il data mart

{{ config(
    materialized='incremental',       -- aggiornamento incrementale
    unique_key='order_id',            -- chiave per deduplicazione in upsert
    cluster_by=['date_key', 'customer_key'],  -- ottimizzazione Snowflake/BigQuery
    on_schema_change='sync_all_columns'
) }}

WITH orders AS (
    SELECT * FROM {{ ref('int_orders_with_items') }}
),

dim_date AS (
    SELECT * FROM {{ ref('dim_date') }}
),

dim_customer AS (
    SELECT * FROM {{ ref('dim_customer') }}
    WHERE is_current = TRUE
)

SELECT
    TO_CHAR(o.created_at_utc, 'YYYYMMDD')::INT AS date_key,
    c.customer_key,
    o.order_id,
    o.status,
    o.line_item_count,
    o.gross_revenue,
    o.net_revenue,
    o.created_at_utc
FROM orders o
JOIN dim_customer c ON c.customer_id = o.customer_id

-- Incremental: caricare solo i nuovi ordini dall'ultimo run
{% if is_incremental() %}
WHERE o.created_at_utc > (SELECT MAX(created_at_utc) FROM {{ this }})
{% endif %}
```

## Testing in dbt

```yaml
# models/staging/schema.yml
# Definire sorgenti e test

version: 2

sources:
  - name: raw
    database: analytics_prod
    schema: raw
    tables:
      - name: orders
        description: "Ordini grezzi dall'OLTP"
        loaded_at_field: _loaded_at
        freshness:
          warn_after: {count: 12, period: hour}
          error_after: {count: 24, period: hour}
        columns:
          - name: id
            description: "ID ordine dalla sorgente"
            tests:
              - unique
              - not_null

models:
  - name: stg_orders
    description: "Ordini con casting e deduplicazione"
    columns:
      - name: order_id
        description: "ID univoco dell'ordine"
        tests:
          - unique
          - not_null
      
      - name: customer_id
        tests:
          - not_null
          - relationships:
              to: ref('stg_customers')
              field: customer_id  # referential integrity test
      
      - name: status
        tests:
          - accepted_values:
              values: ['pending', 'processing', 'completed', 'cancelled', 'returned']
      
      - name: total_amount
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"  # total_amount non può essere negativo
```

```sql
-- tests/assert_orders_not_future_dated.sql
-- Test personalizzato: nessun ordine con data futura

SELECT order_id, created_at_utc
FROM {{ ref('stg_orders') }}
WHERE created_at_utc > CURRENT_TIMESTAMP()
-- Il test fallisce se questa query restituisce righe
```

## Macro e Jinja

```sql
-- macros/generate_date_key.sql
-- Macro riusabile per generare date_key

{% macro generate_date_key(date_column) %}
    TO_CHAR({{ date_column }}, 'YYYYMMDD')::INT
{% endmacro %}

-- Uso nei modelli:
-- SELECT {{ generate_date_key('created_at_utc') }} AS date_key

-- macros/cents_to_dollars.sql
{% macro cents_to_dollars(column_name, precision=2) %}
    ROUND({{ column_name }} / 100.0, {{ precision }})
{% endmacro %}

-- macros/union_relations.sql
-- Macro per fare UNION su più tabelle con naming pattern
{% macro union_tables(tables) %}
    {% for table in tables %}
        SELECT '{{ table }}' AS source_table, *
        FROM {{ ref(table) }}
        {% if not loop.last %} UNION ALL {% endif %}
    {% endfor %}
{% endmacro %}
```

## Snapshots: SCD2 Automatico

```sql
-- snapshots/customer_snapshot.sql
-- dbt gestisce automaticamente la SCD2 per la tabella dim_customer

{% snapshot customer_snapshot %}
    {{
        config(
            target_schema='snapshots',
            unique_key='customer_id',
            strategy='timestamp',  -- 'timestamp' o 'check' (check_cols)
            updated_at='updated_at',
            invalidate_hard_deletes=True
        )
    }}

    SELECT
        customer_id,
        name,
        email,
        city,
        region,
        country,
        segment,
        updated_at
    FROM {{ source('raw', 'customers') }}

{% endsnapshot %}

-- dbt aggiunge automaticamente:
-- dbt_scd_id: hash dell'identità del record
-- dbt_updated_at: quando il record è stato aggiornato nel snapshot
-- dbt_valid_from: inizio del periodo di validità
-- dbt_valid_to: fine del periodo (NULL = record corrente)
```

## Comandi dbt Fondamentali

```bash
# Eseguire tutti i modelli
dbt run

# Eseguire solo un modello e le sue dipendenze
dbt run --select fact_sales+    # + include downstream
dbt run --select +fact_sales    # + include upstream (dipendenze)
dbt run --select +fact_sales+   # entrambi

# Eseguire solo i modelli modificati (confronta con stato precedente)
dbt run --select state:modified

# Eseguire i test
dbt test
dbt test --select stg_orders   # test solo per questo modello

# Generare e servire la documentazione
dbt docs generate
dbt docs serve                  # http://localhost:8080 con lineage graph

# Snapshot SCD2
dbt snapshot

# Compilare i modelli senza eseguirli (debug)
dbt compile

# Freshness check delle sorgenti
dbt source freshness

# Esecuzione in produzione tipica (CI/CD pipeline)
dbt deps           # installare pacchetti (dbt_utils, etc.)
dbt seed           # caricare CSV di dati statici
dbt run            # creare/aggiornare i modelli
dbt test           # eseguire i test
dbt docs generate  # generare documentazione
```

## Pacchetti dbt Utili

```yaml
# packages.yml: dipendenze del progetto

packages:
  - package: dbt-labs/dbt_utils
    version: [">=1.0.0", "<2.0.0"]
    # Funzioni utili: surrogate_key, date_spine, pivot, unpivot
  
  - package: dbt-labs/audit_helper
    version: [">=0.9.0"]
    # Confronta modelli: detect_schema_changes, compare_queries
  
  - package: calogica/dbt_expectations
    version: [">=0.8.0"]
    # Test avanzati: expect_column_values_to_be_between, etc.
  
  - package: dbt-labs/dbt_project_evaluator
    version: [">=0.8.0"]
    # Valuta la struttura del progetto dbt
```

```sql
-- Uso di dbt_utils.surrogate_key per generare surrogate keys
-- invece di SERIAL che dipende dall'ordine di caricamento

SELECT
    {{ dbt_utils.surrogate_key(['customer_id', 'effective_from']) }} AS customer_dim_key,
    customer_id,
    name,
    city,
    effective_from,
    effective_to
FROM customers_scd2

-- dbt_utils.date_spine: generare una serie di date
{{ dbt_utils.date_spine(
    datepart="day",
    start_date="cast('2020-01-01' as date)",
    end_date="cast('2030-12-31' as date)"
) }}
```

