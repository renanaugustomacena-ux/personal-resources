# dbt (Data Build Tool)

dbt trasforma le pipeline di trasformazione dati in software engineering vero e proprio: versioning, testing, documentazione e modularità applicati alle trasformazioni SQL. Invece di scrivere stored procedure o script SQL non versionati, con dbt ogni trasformazione è un file `.sql` con test, documentazione e dipendenze esplicite.

## Filosofia e Posizionamento

dbt implementa il pattern **ELT** (Extract-Load-Transform): i dati vengono prima caricati nel data warehouse nella forma grezza, poi trasformati direttamente nel DWH usando SQL nativo. dbt gestisce solo la T (Transform) — per la E (Extract) e la L (Load) si usano strumenti come Fivetran, Airbyte, o pipeline custom.

```
Sorgenti → [Airbyte/Fivetran] → Raw Tables → [dbt] → Staging/Mart Tables → BI Tools
```

### Vantaggi rispetto a SQL manuale

| Problema SQL Manuale | Soluzione dbt |
|---------------------|---------------|
| Query non versionata | Git-tracked .sql files |
| Nessuna documentazione | doc blocks, schema.yml |
| Dipendenze implicite | ref() esplicite, grafo automatico |
| Nessun test | built-in + custom tests |
| Deploy manuale | dbt run, CI/CD |
| Nessuna modularità | Macro, packages, sources |

---

## Installazione e Setup

```bash
# Installa dbt con adattatore per il tuo DWH
pip install dbt-core dbt-postgres          # PostgreSQL
pip install dbt-core dbt-snowflake         # Snowflake
pip install dbt-core dbt-bigquery          # BigQuery
pip install dbt-core dbt-redshift          # Redshift
pip install dbt-core dbt-duckdb            # DuckDB (locale, ottimo per dev)

# Verifica installazione
dbt --version

# Crea nuovo progetto
dbt init my_data_project
cd my_data_project
```

### profiles.yml

Il file `profiles.yml` (fuori dal progetto, in `~/.dbt/profiles.yml`) contiene le configurazioni di connessione:

```yaml
# ~/.dbt/profiles.yml
my_data_project:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      user: "{{ env_var('DBT_USER') }}"
      password: "{{ env_var('DBT_PASSWORD') }}"
      port: 5432
      dbname: analytics_dev
      schema: dbt_dev      # Schema dedicato per sviluppo
      threads: 4            # Parallelismo

    prod:
      type: postgres
      host: "{{ env_var('DWH_HOST') }}"
      user: "{{ env_var('DWH_USER') }}"
      password: "{{ env_var('DWH_PASSWORD') }}"
      port: 5432
      dbname: analytics
      schema: public
      threads: 8

# Snowflake
my_snowflake_project:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      password: "{{ env_var('SNOWFLAKE_PASSWORD') }}"
      role: TRANSFORMER
      database: DEV_DB
      warehouse: TRANSFORM_WH
      schema: DBT_DEV
      threads: 4
      client_session_keep_alive: False

    prod:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      authenticator: externalbrowser  # SSO in prod
      role: TRANSFORMER
      database: PROD_DB
      warehouse: TRANSFORM_WH
      schema: PUBLIC
      threads: 8
```

### dbt_project.yml

```yaml
# dbt_project.yml
name: my_data_project
version: "1.0.0"
config-version: 2

profile: my_data_project

# Directory structure
model-paths:     ["models"]
analysis-paths:  ["analyses"]
test-paths:      ["tests"]
seed-paths:      ["seeds"]
macro-paths:     ["macros"]
snapshot-paths:  ["snapshots"]

target-path:     "target"
clean-targets:   ["target", "dbt_packages"]

# Configurazioni di default per layer
models:
  my_data_project:
    staging:
      +materialized: view         # Staging sempre come view
      +schema: staging

    intermediate:
      +materialized: ephemeral    # Non materializzata: CTE inline

    marts:
      +materialized: table        # Mart materializzata come tabella
      +schema: marts

      finance:
        +materialized: table
        +tags: ["finance"]
        +grants:
          select: ["role_analyst", "role_finance"]

    # Override per modelli specifici
    metrics:
      +materialized: incremental
      +on_schema_change: sync_all_columns

seeds:
  my_data_project:
    +schema: seeds
    +column_types:
      id: bigint

vars:
  # Variabili globali accessibili nei modelli
  start_date: "2021-01-01"
  is_test_run: false
```

---

## Struttura del Progetto

```
my_data_project/
├── dbt_project.yml
├── packages.yml
├── models/
│   ├── staging/               # Layer 1: lettura raw, minimal cleaning
│   │   ├── sources.yml        # Definizione sorgenti
│   │   ├── stg_orders.sql
│   │   ├── stg_customers.sql
│   │   └── stg_products.sql
│   ├── intermediate/          # Layer 2: join, logica di business
│   │   ├── int_orders_enriched.sql
│   │   └── int_customer_segments.sql
│   └── marts/                 # Layer 3: modelli finali per BI
│       ├── finance/
│       │   ├── fct_orders.sql
│       │   └── dim_customer.sql
│       └── marketing/
│           └── fct_campaigns.sql
├── macros/
│   ├── generate_schema_name.sql
│   └── cents_to_dollars.sql
├── tests/                     # Test SQL personalizzati
│   └── assert_revenue_positive.sql
├── seeds/                     # File CSV statici
│   └── country_codes.csv
├── snapshots/                 # SCD Type 2
│   └── snap_customer_status.sql
└── analyses/                  # Query ad hoc (non deployate)
    └── monthly_cohort.sql
```

---

## Modelli SQL

### Staging Model

```sql
-- models/staging/stg_orders.sql
{{ config(
    materialized='view',
    tags=['staging', 'orders']
) }}

WITH source AS (
    -- ref() a una source definita in sources.yml
    SELECT * FROM {{ source('raw', 'orders') }}
),

renamed AS (
    SELECT
        id::BIGINT                              AS order_id,
        customer_id::BIGINT                     AS customer_id,
        TRIM(LOWER(customer_email))             AS customer_email,
        CAST(total_amount AS NUMERIC(12,2))     AS total_amount,
        UPPER(TRIM(currency))                   AS currency,
        UPPER(TRIM(country_code))               AS country_code,
        COALESCE(status, 'unknown')             AS status,
        created_at::TIMESTAMPTZ                 AS created_at,
        updated_at::TIMESTAMPTZ                 AS updated_at
    FROM source
    WHERE id IS NOT NULL
),

deduped AS (
    SELECT *,
        ROW_NUMBER() OVER (
            PARTITION BY order_id
            ORDER BY updated_at DESC
        ) AS _rn
    FROM renamed
)

SELECT * EXCEPT (_rn)
FROM deduped
WHERE _rn = 1
```

### Incremental Model

```sql
-- models/marts/finance/fct_orders.sql
{{ config(
    materialized='incremental',
    unique_key='order_id',
    on_schema_change='sync_all_columns',
    incremental_strategy='merge',
    cluster_by=['order_date'],   -- Snowflake/BigQuery
    tags=['mart', 'finance', 'daily']
) }}

WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
    {% if is_incremental() %}
    -- Solo righe nuove o modificate dall'ultima run
    WHERE updated_at > (SELECT MAX(updated_at) FROM {{ this }})
    {% endif %}
),

customers AS (
    SELECT * FROM {{ ref('dim_customer') }}
    WHERE is_current = TRUE
),

enriched AS (
    SELECT
        o.order_id,
        o.customer_id,
        c.customer_sk,
        o.total_amount                                          AS net_amount,
        ROUND(o.total_amount * {{ var('default_tax_rate', 0.22) }}, 2)
                                                                AS tax_amount,
        o.total_amount + ROUND(o.total_amount * {{ var('default_tax_rate', 0.22) }}, 2)
                                                                AS gross_amount,
        o.currency,
        o.country_code,
        o.status,
        DATE(o.created_at)                                      AS order_date,
        DATE_TRUNC('month', o.created_at)::DATE                 AS order_month,
        DATE_TRUNC('year', o.created_at)::DATE                  AS order_year,
        EXTRACT(DOW FROM o.created_at)                          AS day_of_week,
        o.created_at,
        o.updated_at,
        CURRENT_TIMESTAMP                                        AS _dbt_updated_at
    FROM orders o
    LEFT JOIN customers c USING (customer_id)
)

SELECT * FROM enriched
```

### Ephemeral Model

```sql
-- models/intermediate/int_orders_with_items.sql
-- Ephemeral: non crea tabella nel DWH, viene inline come CTE
{{ config(materialized='ephemeral') }}

WITH orders AS (
    SELECT * FROM {{ ref('stg_orders') }}
),

order_items AS (
    SELECT * FROM {{ ref('stg_order_items') }}
),

aggregated_items AS (
    SELECT
        order_id,
        COUNT(*)                    AS item_count,
        SUM(quantity)               AS total_quantity,
        SUM(unit_price * quantity)  AS items_subtotal,
        ARRAY_AGG(product_id)       AS product_ids
    FROM order_items
    GROUP BY order_id
)

SELECT
    o.*,
    ai.item_count,
    ai.total_quantity,
    ai.items_subtotal,
    ai.product_ids
FROM orders o
LEFT JOIN aggregated_items ai USING (order_id)
```

---

## Sources e Freshness

```yaml
# models/staging/sources.yml
version: 2

sources:
  - name: raw
    database: production
    schema: public
    description: "Dati raw caricati da Fivetran/Airbyte"
    
    # Freshness check: fallisce se i dati sono troppo vecchi
    freshness:
      warn_after:  {count: 12, period: hour}
      error_after: {count: 24, period: hour}
    
    tables:
      - name: orders
        loaded_at_field: updated_at    # Colonna di riferimento per freshness
        description: "Ordini dal sistema operativo"
        columns:
          - name: id
            description: "Order ID univoco"
            tests:
              - not_null
              - unique
          - name: status
            tests:
              - accepted_values:
                  values: ["pending", "confirmed", "shipped", "delivered", "cancelled"]
          - name: total_amount
            tests:
              - not_null
              - dbt_utils.expression_is_true:
                  expression: ">= 0"

      - name: customers
        loaded_at_field: updated_at
        columns:
          - name: id
            tests: [not_null, unique]
          - name: email
            tests:
              - not_null
              - unique
              - dbt_utils.expression_is_true:
                  expression: "LIKE '%@%.%'"
```

---

## Testing

### Test Built-in

```yaml
# models/marts/finance/schema.yml
version: 2

models:
  - name: fct_orders
    description: "Fact table ordini per analytics finanziario"
    columns:
      - name: order_id
        tests:
          - not_null
          - unique                           # Chiave primaria
      
      - name: customer_id
        tests:
          - not_null
          - relationships:                   # FK check
              to: ref('dim_customer')
              field: customer_id

      - name: net_amount
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"

      - name: status
        tests:
          - accepted_values:
              values: ["pending", "confirmed", "shipped", "delivered", "cancelled"]
              severity: warn   # Warning invece di errore

      - name: order_date
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= '2020-01-01'"
```

### Test SQL Custom

```sql
-- tests/assert_revenue_not_negative.sql
-- Questo test fallisce se trova righe (deve restituire 0 righe per passare)
SELECT
    order_id,
    net_amount,
    gross_amount
FROM {{ ref('fct_orders') }}
WHERE net_amount < 0
   OR gross_amount < 0
```

```sql
-- tests/assert_orders_have_customers.sql
-- Tutti gli ordini devono avere un customer nel DWH
SELECT
    o.order_id,
    o.customer_id
FROM {{ ref('fct_orders') }} o
LEFT JOIN {{ ref('dim_customer') }} c USING (customer_id)
WHERE c.customer_id IS NULL
  AND o.order_id IS NOT NULL
```

---

## Macro e Jinja

```sql
-- macros/cents_to_dollars.sql
{% macro cents_to_dollars(column_name) %}
    ROUND({{ column_name }} / 100.0, 2)
{% endmacro %}

-- Uso nel modello:
-- {{ cents_to_dollars('amount_cents') }} AS amount_dollars
```

```sql
-- macros/generate_date_key.sql
{% macro generate_date_key(column_name) %}
    CAST(TO_CHAR({{ column_name }}, 'YYYYMMDD') AS INTEGER)
{% endmacro %}
```

```sql
-- macros/create_audit_columns.sql
-- Macro che aggiunge colonne di audit standard
{% macro audit_columns() %}
    CURRENT_TIMESTAMP                 AS _dbt_created_at,
    '{{ invocation_id }}'             AS _dbt_run_id,
    '{{ this.identifier }}'           AS _dbt_model
{% endmacro %}
```

---

## Comandi dbt

```bash
# Compila i modelli (senza eseguire)
dbt compile

# Esegui tutti i modelli
dbt run

# Esegui con selezione
dbt run --select stg_orders                  # Singolo modello
dbt run --select staging.*                   # Tag o directory
dbt run --select orders+                     # orders e tutti i downstream
dbt run --select +fct_orders                 # fct_orders e tutti gli upstream
dbt run --select 1+fct_orders                # Solo 1 livello upstream

# Esegui test
dbt test
dbt test --select fct_orders

# Controlla freshness delle sorgenti
dbt source freshness

# Genera documentazione
dbt docs generate
dbt docs serve    # Apre browser su http://localhost:8080

# Crea snapshot
dbt snapshot

# Carica seed files
dbt seed

# Debug connessione
dbt debug

# Build (run + test in sequenza)
dbt build

# Dry run (--dry-run non esiste, ma puoi usare --empty)
dbt run --empty  # Crea strutture senza dati
```

---

## CI/CD con dbt

```yaml
# .github/workflows/dbt-ci.yml
name: dbt CI

on: [pull_request]

jobs:
  dbt_test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Install dbt
        run: pip install dbt-snowflake==1.7.0

      - name: dbt debug
        env:
          DBT_SNOWFLAKE_ACCOUNT: ${{ secrets.SNOWFLAKE_ACCOUNT }}
          DBT_SNOWFLAKE_USER: ${{ secrets.SNOWFLAKE_CI_USER }}
          DBT_SNOWFLAKE_PASSWORD: ${{ secrets.SNOWFLAKE_CI_PASSWORD }}
        run: dbt debug --target ci

      - name: dbt compile
        run: dbt compile --target ci

      - name: dbt build (PR only, using schema isolation)
        run: |
          # Ogni PR ottiene un schema separato: ci_pr_123
          export DBT_SCHEMA="ci_pr_${{ github.event.pull_request.number }}"
          dbt build --target ci --vars "{'is_test_run': true}"

      - name: Cleanup CI schema
        if: always()
        run: |
          dbt run-operation drop_schema \
            --args "{'schema_name': 'ci_pr_${{ github.event.pull_request.number }}'}"
```

---

## Best Practice

**Convezione di naming**: prefissi espliciti che indicano il layer (`stg_`, `int_`, `fct_`, `dim_`). Chiunque veda il nome sa dove si trova nel grafo di trasformazione.

**Un modello = una CTE finale** — la trasformazione deve essere comprensibile senza eseguire il codice. Usa CTE intermedie con nomi significativi invece di subquery annidate.

**Non bypassare mai ref() e source()** — scrivere `FROM public.orders` invece di `FROM {{ source('raw', 'orders') }}` rompe il grafo di dipendenze e il lineage automatico.

**Testa ogni colonna critica** — almeno `not_null` e `unique` sulle primary key. Test sui FK, valori accettati, ranges numerici. Un test dbt che fallisce in CI evita dati corrotti in produzione.

**Schema separato per dev** — ogni sviluppatore lavora in `dbt_<username>` per non interferire con gli altri. In CI, schema isolato per PR.
