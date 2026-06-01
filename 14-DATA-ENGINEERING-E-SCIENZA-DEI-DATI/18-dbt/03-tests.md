# dbt Testing: Qualità dei Dati come Codice

## Filosofia del Testing in dbt

dbt tratta i test come cittadini di prima classe del progetto. Ogni modello può avere asserzioni dichiarative che vengono eseguite con `dbt test`, restituendo un risultato binario pass/fail. Il principio fondamentale: i test dbt sono query SQL che restituiscono righe quando qualcosa va storto. Zero righe = test superato.

```
dbt test
├── Generic tests (schema.yml)   → parametrizzati, riusabili
├── Singular tests (tests/)      → SQL personalizzati one-shot
└── Risultato: tabella di audit in target schema
```

I test vengono eseguiti in CI/CD su ogni PR e in produzione dopo ogni run per garantire che i dati caricati rispettino i contratti definiti.

---

## Generic Tests (Schema.yml)

### I Quattro Test Built-in

dbt include quattro generic tests utilizzabili su qualsiasi colonna o combinazione di colonne:

```yaml
# models/staging/schema.yml
version: 2

models:
  - name: stg_orders
    description: "Ordini normalizzati dalla replica PostgreSQL"
    columns:
      - name: order_id
        description: "Chiave primaria surrogate"
        tests:
          - not_null
          - unique

      - name: customer_id
        description: "FK verso dim_customer"
        tests:
          - not_null
          - relationships:
              to: ref('dim_customer')
              field: customer_id

      - name: status
        description: "Stato lifecycle dell'ordine"
        tests:
          - not_null
          - accepted_values:
              values: ['pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded']

      - name: total_amount_cents
        description: "Importo in centesimi (evita float)"
        tests:
          - not_null

      - name: created_at
        tests:
          - not_null
```

**Comportamento di ogni test:**

| Test | Query generata internamente | Fail quando |
|------|-----------------------------|-------------|
| `not_null` | `SELECT * WHERE col IS NULL` | Esiste almeno un NULL |
| `unique` | `SELECT col, COUNT(*) GROUP BY col HAVING COUNT(*) > 1` | Duplicati presenti |
| `relationships` | `LEFT JOIN ... WHERE ref.pk IS NULL` | FK senza corrispondente PK |
| `accepted_values` | `SELECT * WHERE col NOT IN (...)` | Valore fuori dominio |

### Configurazione Avanzata dei Test

```yaml
# Severity: warn invece di error (non blocca il pipeline)
- name: status
  tests:
    - accepted_values:
        values: ['pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded']
        severity: warn
        # Logga warning ma non fallisce il run

# Threshold: tollera una percentuale di fallimenti
- name: email
  tests:
    - not_null:
        severity: warn
        warn_if: ">= 10"   # warning se >= 10 righe fallite
        error_if: ">= 100" # error se >= 100 righe fallite

# Where: applica il test solo su un sottoinsieme
- name: shipped_at
  tests:
    - not_null:
        where: "status = 'shipped'"

# Name: sovrascrive il nome auto-generato del test
- name: order_id
  tests:
    - unique:
        name: stg_orders_order_id_unique_v2
```

### Test a Livello di Modello (Multi-colonna)

```yaml
models:
  - name: fct_orders
    tests:
      # Combinazione unica (composite key)
      - unique:
          column_name: "concat(order_id, '-', line_item_id)"

      # Test a livello di modello con macro dbt_utils
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns:
            - order_id
            - line_item_id

      # Row count non zero
      - dbt_utils.expression_is_true:
          expression: "total_amount_cents >= 0"
          name: fct_orders_non_negative_amount
```

---

## Singular Tests (SQL Personalizzati)

I singular tests sono file SQL nella directory `tests/` che devono restituire zero righe per essere considerati superati.

### Struttura Base

```sql
-- tests/assert_orders_have_positive_amount.sql
-- Descrizione: ogni ordine completato deve avere importo > 0

SELECT
    order_id,
    total_amount_cents,
    status
FROM {{ ref('fct_orders') }}
WHERE
    status IN ('delivered', 'shipped')
    AND total_amount_cents <= 0
```

Se questa query restituisce righe, il test fallisce con un elenco degli order_id incriminati.

### Test su Aggregazioni

```sql
-- tests/assert_daily_revenue_consistent.sql
-- Revenue giornaliera non deve mai azzerarsi dopo essere esistita

WITH daily_revenue AS (
    SELECT
        DATE_TRUNC('day', created_at) AS day,
        SUM(total_amount_cents) AS revenue_cents
    FROM {{ ref('fct_orders') }}
    WHERE status = 'delivered'
    GROUP BY 1
),
lagged AS (
    SELECT
        day,
        revenue_cents,
        LAG(revenue_cents) OVER (ORDER BY day) AS prev_day_revenue
    FROM daily_revenue
)

SELECT day, revenue_cents, prev_day_revenue
FROM lagged
WHERE
    prev_day_revenue > 0
    AND revenue_cents = 0
    AND day < CURRENT_DATE  -- ignora il giorno corrente (incompleto)
```

### Test su Referential Integrity Complessa

```sql
-- tests/assert_line_items_match_order_total.sql
-- La somma dei line items deve corrispondere al totale dell'ordine (tolleranza 1 cent)

WITH order_totals AS (
    SELECT
        order_id,
        total_amount_cents
    FROM {{ ref('fct_orders') }}
),
line_item_sums AS (
    SELECT
        order_id,
        SUM(amount_cents) AS calculated_total
    FROM {{ ref('fct_order_line_items') }}
    GROUP BY 1
),
discrepancies AS (
    SELECT
        o.order_id,
        o.total_amount_cents AS stated_total,
        l.calculated_total,
        ABS(o.total_amount_cents - l.calculated_total) AS delta_cents
    FROM order_totals o
    JOIN line_item_sums l ON o.order_id = l.order_id
    WHERE ABS(o.total_amount_cents - l.calculated_total) > 1  -- tolleranza 1 cent arrotondamento
)

SELECT * FROM discrepancies
```

### Test con Variabili e Configurazione

```sql
-- tests/assert_recent_data_freshness.sql
-- Verifica che ci siano dati degli ultimi N minuti (configurabile)

{% set max_minutes_stale = var('max_freshness_minutes', 60) %}

SELECT
    MAX(created_at) AS last_record_at,
    CURRENT_TIMESTAMP AS now,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - MAX(created_at))) / 60 AS minutes_stale
FROM {{ ref('stg_orders') }}
HAVING MAX(created_at) < CURRENT_TIMESTAMP - INTERVAL '{{ max_minutes_stale }} minutes'
```

Esecuzione con override della variabile:
```bash
dbt test --select assert_recent_data_freshness --vars '{"max_freshness_minutes": 30}'
```

---

## Pacchetti di Test: dbt_utils e dbt_expectations

### Installazione

```yaml
# packages.yml
packages:
  - package: dbt-labs/dbt_utils
    version: 1.2.0
  - package: calogica/dbt_expectations
    version: 0.10.1
  - package: dbt-labs/dbt_project_evaluator
    version: 0.8.0

# Poi eseguire:
# dbt deps
```

### dbt_utils Tests

```yaml
models:
  - name: fct_orders
    tests:
      # Unicità su combinazione di colonne
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns:
            - order_id
            - line_item_id

      # Intervalli di date validi
      - dbt_utils.at_least_one:
          column_name: order_id

      # Espressione booleana
      - dbt_utils.expression_is_true:
          expression: "shipped_at IS NULL OR shipped_at >= created_at"
          name: shipped_after_created

      # Cardinalità minima
      - dbt_utils.cardinality_equality:
          field: customer_id
          to: ref('dim_customer')
          field: customer_id

    columns:
      - name: total_amount_cents
        tests:
          # Range numerico
          - dbt_utils.accepted_range:
              min_value: 0
              max_value: 10000000  # 100.000 EUR in centesimi
              inclusive: true

      - name: order_date
        tests:
          # Non nel futuro
          - dbt_utils.expression_is_true:
              expression: "<= CURRENT_DATE"
```

### dbt_expectations Tests (ispirato a Great Expectations)

```yaml
models:
  - name: stg_customers
    columns:
      - name: email
        tests:
          # Lunghezza stringa
          - dbt_expectations.expect_column_value_lengths_to_be_between:
              min_value: 5
              max_value: 254

          # Pattern regex
          - dbt_expectations.expect_column_values_to_match_regex:
              regex: "^[a-zA-Z0-9._%+\\-]+@[a-zA-Z0-9.\\-]+\\.[a-zA-Z]{2,}$"
              name: email_format_valid

      - name: total_amount_cents
        tests:
          # Distribuzione statistica
          - dbt_expectations.expect_column_mean_to_be_between:
              min_value: 1000   # media almeno 10 EUR
              max_value: 500000 # media massimo 5000 EUR

          - dbt_expectations.expect_column_quantile_values_to_be_between:
              quantile: 0.95
              min_value: 0
              max_value: 1000000

          # Non nullo con soglia percentuale
          - dbt_expectations.expect_column_values_to_not_be_null:
              mostly: 0.99  # 99% non nulli (tollera 1% dati storici mancanti)

  - name: fct_orders
    tests:
      # Row count non cala drasticamente rispetto a ieri
      - dbt_expectations.expect_table_row_count_to_be_between:
          min_value: 100
          max_value: 1000000

      # Schema fisso (no colonne aggiunte/rimosse senza PR)
      - dbt_expectations.expect_table_columns_to_match_ordered_list:
          column_list:
            - order_id
            - customer_id
            - created_at
            - status
            - total_amount_cents
          transform: upper  # case insensitive
```

---

## Custom Generic Tests (Macro)

Puoi creare generic tests riusabili definendo macro nella directory `macros/`.

### Test: Not Null se Condizione

```sql
-- macros/tests/test_not_null_where.sql
{% test not_null_where(model, column_name, where_clause) %}

SELECT {{ column_name }}
FROM {{ model }}
WHERE
    {{ where_clause }}
    AND {{ column_name }} IS NULL

{% endtest %}
```

Utilizzo in schema.yml:
```yaml
- name: shipped_at
  tests:
    - not_null_where:
        where_clause: "status = 'shipped'"
```

### Test: Valori Attesi con Tolleranza Percentuale

```sql
-- macros/tests/test_accepted_values_pct.sql
-- Fallisce solo se PIÙ DEL threshold% delle righe ha valori non attesi

{% test accepted_values_pct(model, column_name, values, threshold_pct=5) %}

WITH invalid_rows AS (
    SELECT {{ column_name }}
    FROM {{ model }}
    WHERE {{ column_name }} NOT IN (
        {% for v in values %}'{{ v }}'{% if not loop.last %},{% endif %}{% endfor %}
    )
),
total AS (
    SELECT COUNT(*) AS n FROM {{ model }}
),
invalid_pct AS (
    SELECT
        COUNT(*) AS invalid_count,
        t.n AS total_count,
        100.0 * COUNT(*) / NULLIF(t.n, 0) AS pct_invalid
    FROM invalid_rows, total t
    GROUP BY t.n
)

SELECT *
FROM invalid_pct
WHERE pct_invalid > {{ threshold_pct }}

{% endtest %}
```

Utilizzo:
```yaml
- name: payment_method
  tests:
    - accepted_values_pct:
        values: ['credit_card', 'paypal', 'bank_transfer', 'crypto']
        threshold_pct: 2  # Fallisce solo se >2% ha valori non attesi
```

### Test: Monotonia Temporale

```sql
-- macros/tests/test_timestamps_are_increasing.sql
-- Verifica che i timestamp non regrediscano entro ogni gruppo

{% test timestamps_are_increasing(model, column_name, partition_by, order_by=None) %}

{% set order_col = order_by if order_by else column_name %}

WITH ordered AS (
    SELECT
        {{ partition_by }},
        {{ column_name }},
        LAG({{ column_name }}) OVER (
            PARTITION BY {{ partition_by }}
            ORDER BY {{ order_col }}
        ) AS prev_val
    FROM {{ model }}
)

SELECT *
FROM ordered
WHERE prev_val IS NOT NULL
  AND {{ column_name }} < prev_val

{% endtest %}
```

---

## Configurazione e Selezione dei Test

### Eseguire Sottoinsieme di Test

```bash
# Test su un modello specifico
dbt test --select stg_orders

# Test su un modello e tutti i suoi discendenti
dbt test --select stg_orders+

# Solo test di tipo specifico (via tag)
dbt test --select tag:critical

# Escludi test lenti
dbt test --exclude tag:slow

# Test su modelli modificati (ottimo per CI)
dbt test --select state:modified+

# Test falliti nel run precedente (retry)
dbt test --select result:fail
```

### Tagging dei Test

```yaml
# schema.yml - tagging individuale
- name: order_id
  tests:
    - not_null:
        tags: ['critical', 'pk']
    - unique:
        tags: ['critical', 'pk']

- name: email
  tests:
    - dbt_expectations.expect_column_values_to_match_regex:
        regex: "..."
        tags: ['pii', 'slow']

# dbt_project.yml - tagging a livello di directory
models:
  myproject:
    staging:
      +tags: ['staging']
    marts:
      +tags: ['production', 'critical']

tests:
  myproject:
    +store_failures: true  # salva righe fallite per debug
```

### Store Failures: Debug Facilitato

```yaml
# dbt_project.yml
tests:
  myproject:
    +store_failures: true
    +store_failures_as: table  # oppure 'view' (default) o 'ephemeral'
    +schema: test_failures     # schema separato per non inquinare prod
```

Con `store_failures: true`, dbt crea tabelle tipo:
```
analytics_test_failures.not_null_stg_orders_order_id
analytics_test_failures.unique_fct_orders_order_id__line_item_id
```

Query di debug:
```sql
-- Ispeziona le righe fallite direttamente
SELECT * FROM analytics_test_failures.not_null_stg_orders_customer_id LIMIT 100;
```

---

## Source Freshness Tests

I test di freshness verificano che i dati sorgente siano aggiornati:

```yaml
# models/staging/sources.yml
version: 2

sources:
  - name: ecommerce_replica
    database: production
    schema: public
    freshness:
      warn_after: {count: 6, period: hour}   # warning dopo 6 ore
      error_after: {count: 24, period: hour}  # error dopo 24 ore
    loaded_at_field: _extracted_at            # colonna timestamp di estrazione

    tables:
      - name: orders
        description: "Tabella ordini principale"
        freshness:
          warn_after: {count: 1, period: hour}   # SLA più stretto per ordini
          error_after: {count: 4, period: hour}
        columns:
          - name: id
            tests:
              - not_null
              - unique

      - name: customers
        # Eredita freshness dal source parent
        loaded_at_field: updated_at  # Override campo timestamp

      - name: products
        freshness: null  # Disabilita freshness per tabelle statiche
```

Esecuzione:
```bash
dbt source freshness
# Oppure in combinazione con test
dbt build --select source:ecommerce_replica
```

Output esempio:
```
14:23:10  Found 1 source, 3 tables
14:23:11  [WARN] Source 'ecommerce_replica.customers' is 7 hours, 3 minutes old (WARNING after 6 hours)
14:23:11  [PASS] Source 'ecommerce_replica.orders' is 23 minutes old
```

---

## Integrazione CI/CD

### GitHub Actions con Matrix Testing

```yaml
# .github/workflows/dbt_ci.yml
name: dbt CI

on:
  pull_request:
    paths:
      - 'models/**'
      - 'tests/**'
      - 'macros/**'
      - 'packages.yml'

jobs:
  dbt_test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: analytics_ci
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dbt
        run: |
          pip install dbt-postgres==1.7.0
          dbt deps

      - name: Setup CI profile
        run: |
          mkdir -p ~/.dbt
          cat > ~/.dbt/profiles.yml << EOF
          myproject:
            target: ci
            outputs:
              ci:
                type: postgres
                host: localhost
                port: 5432
                user: postgres
                password: test
                dbname: analytics_ci
                schema: ci_{{ github.event.pull_request.number }}
                threads: 4
          EOF

      - name: dbt build (modelli modificati + dipendenti)
        run: |
          dbt build \
            --select state:modified+ \
            --defer \
            --state ./target/manifest.json \
            --target-path ./target_ci
        env:
          DBT_PROFILES_DIR: ~/.dbt

      - name: Upload artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: dbt-artifacts-${{ github.event.pull_request.number }}
          path: target_ci/

  dbt_docs:
    runs-on: ubuntu-latest
    needs: dbt_test
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
      - name: Generate docs
        run: |
          pip install dbt-postgres==1.7.0
          dbt deps
          dbt docs generate
      - name: Deploy docs preview
        run: echo "Deploy to staging docs site..."
```

### Slim CI con Manifest Caching

La tecnica "slim CI" con `--defer` e `--state` evita di ricostruire tutti i modelli in CI:

```bash
# In produzione: scarica il manifest dal ultimo run di successo
dbt run-operation upload_manifest  # custom macro che carica su S3

# In CI: scarica manifest di prod e usa --defer
aws s3 cp s3://my-bucket/dbt/manifest.json ./target/manifest.json

# Esegui solo modelli modificati, using prod results per i non modificati
dbt build \
  --select state:modified+ \
  --defer \
  --state ./target/manifest.json
```

---

## Best Practices per i Test dbt

### Strategia di Coverage

```
Priorità test per layer:

staging/  → not_null, unique su PK, accepted_values su enum critici
           → relationships per ogni FK verso sorgenti
           → freshness su tutti i source

intermediate/ → test minimi (è layer di trasformazione)
              → expression_is_true per logica di business complessa

marts/ → not_null + unique su tutte le PK
       → relationships verso dim_*
       → singular tests per invarianti di business
       → dbt_expectations per distribuzione/range
```

### Nomenclatura Coerente

```bash
# Test singolari: assert_ + cosa deve essere vero
tests/assert_orders_amount_positive.sql        ✓
tests/check_orders.sql                         ✗ (troppo vago)
tests/orders_amount.sql                        ✗ (non indica il tipo)

# Generic tests custom: test_ + predicato
macros/tests/test_not_null_where.sql          ✓
macros/tests/test_accepted_pct.sql            ✓
macros/tests/validate_column.sql              ✗ (non è formato macro test)
```

### Quando Usare ogni Tipo

| Situazione | Approccio consigliato |
|------------|----------------------|
| PK not null + unique | Generic test built-in |
| FK referential integrity | Generic `relationships` |
| Enum/status noti | Generic `accepted_values` |
| Invariante di business complessa | Singular test SQL |
| Distribuzione statistica | `dbt_expectations` |
| Unicità composita | `dbt_utils.unique_combination_of_columns` |
| Test parametrizzato riusabile | Custom generic test (macro) |
| Freshness dati sorgente | `source freshness` |

### Gestione Test Flaky

Test intermittenti sono peggiori della loro assenza — generano alert fatigue:

```yaml
# Soluzione 1: usa threshold invece di 100% strict
- name: payment_method
  tests:
    - accepted_values:
        values: ['credit_card', 'paypal', 'bank_transfer']
        severity: warn  # Non blocca pipeline

# Soluzione 2: applica where per escludere dati storici problematici
- name: email
  tests:
    - not_null:
        where: "created_at >= '2022-01-01'"  # Dati pre-2022 hanno email mancante by design

# Soluzione 3: usa warn_if / error_if con soglie
- name: phone
  tests:
    - not_null:
        warn_if: ">= 50"
        error_if: ">= 500"
```

---

## Esempio Completo: Schema.yml Produzione

```yaml
# models/marts/schema.yml
version: 2

models:
  - name: dim_customer
    description: >
      Dimensione cliente con attributi correnti (SCD Type 1 per gli attributi
      non storici, SCD Type 2 per tier e segmento). Grain: un record per
      customer attivo.
    meta:
      owner: data-team
      sla: daily
      pii_contains: true
    tests:
      - dbt_utils.unique_combination_of_columns:
          combination_of_columns: [customer_id, valid_from]
          name: dim_customer_pk_unique
          tags: ['critical']
    columns:
      - name: customer_key
        description: "Surrogate key (hash MD5 di customer_id + valid_from)"
        tests:
          - not_null:
              tags: ['critical']
          - unique:
              tags: ['critical']

      - name: customer_id
        description: "Business key dal sistema sorgente"
        tests:
          - not_null

      - name: email
        description: "Email normalizzata lowercase"
        meta:
          pii: true
        tests:
          - not_null:
              where: "valid_to IS NULL"  # Solo record correnti
          - dbt_expectations.expect_column_values_to_match_regex:
              regex: "^[^@]+@[^@]+\\.[^@]+$"
              severity: warn

      - name: customer_tier
        tests:
          - accepted_values:
              values: ['bronze', 'silver', 'gold', 'platinum']

      - name: valid_from
        tests:
          - not_null

      - name: valid_to
        description: "NULL = record corrente"
        # Nessun test not_null, i record correnti hanno valid_to = NULL

      - name: is_current
        tests:
          - not_null
          - accepted_values:
              values: [true, false]
              quote: false

  - name: fct_orders
    description: "Fatti ordini al grain di ordine (un record per ordine)"
    meta:
      owner: data-team
      sla: hourly
    tests:
      - dbt_expectations.expect_table_row_count_to_be_between:
          min_value: 1000
          name: fct_orders_not_empty
          tags: ['critical']
    columns:
      - name: order_id
        tests:
          - not_null:
              tags: ['critical']
          - unique:
              tags: ['critical']

      - name: customer_key
        tests:
          - not_null
          - relationships:
              to: ref('dim_customer')
              field: customer_key

      - name: total_amount_cents
        tests:
          - not_null
          - dbt_utils.accepted_range:
              min_value: 0
              max_value: 100000000
              name: fct_orders_amount_reasonable_range

      - name: status
        tests:
          - not_null
          - accepted_values:
              values: ['pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded']

      - name: created_at
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: "<= CURRENT_TIMESTAMP"
              name: fct_orders_created_not_future
```

---

## Comandi Test Utili

```bash
# Esegui tutti i test
dbt test

# Test su modello specifico con output verbose
dbt test --select fct_orders --log-level debug

# Test falliti precedentemente
dbt retry  # dbt 1.6+

# Source freshness
dbt source freshness

# Build completo (run + test in ordine corretto)
dbt build

# Build solo su cambiamenti (CI slim)
dbt build --select state:modified+

# Genera documentazione con test coverage
dbt docs generate && dbt docs serve

# Lista tutti i test senza eseguirli
dbt ls --resource-type test

# Lista test su modello specifico
dbt ls --resource-type test --select stg_orders
```

Output `dbt test`:
```
14:31:02  Running 24 tests
14:31:03  [PASS] not_null_stg_orders_order_id
14:31:03  [PASS] unique_stg_orders_order_id
14:31:04  [WARN] accepted_values_stg_orders_payment_method (3 rows)
14:31:05  [FAIL] relationships_fct_orders_customer_key__customer_key__ref_dim_customer_ (127 rows)
14:31:05
14:31:05  Completed with 1 error, 1 warning and 0 exceptions
14:31:05
14:31:05  Failure in test relationships_fct_orders_customer_key (models/marts/schema.yml)
14:31:05    Got 127 results, configured to fail if != 0
14:31:05    Inspect: SELECT * FROM analytics_test_failures.relationships_fct_orders_customer_key
```
