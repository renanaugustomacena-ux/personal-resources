# dbt Snapshots: Slowly Changing Dimensions Automatizzate

## Cos'è uno Snapshot dbt

Uno snapshot dbt cattura automaticamente lo stato di una tabella nel tempo, implementando la logica SCD Type 2 (Slowly Changing Dimensions) senza codice manuale. Ad ogni esecuzione di `dbt snapshot`, dbt:

1. Legge la tabella sorgente corrente
2. Confronta con l'ultima versione snapshot
3. Aggiunge nuovi record (inserimento)
4. Chiude i record modificati (`dbt_valid_to = timestamp`)
5. Apre nuovi record per le righe cambiate

```
Esecuzione 1 (2024-01-01):
customer_id | email           | tier   | dbt_valid_from      | dbt_valid_to
1           | mario@ex.it     | silver | 2024-01-01 08:00:00 | NULL

Esecuzione 2 (2024-01-15): Mario upgrada a gold
customer_id | email           | tier   | dbt_valid_from      | dbt_valid_to
1           | mario@ex.it     | silver | 2024-01-01 08:00:00 | 2024-01-15 08:00:00  ← chiuso
1           | mario@ex.it     | gold   | 2024-01-15 08:00:00 | NULL                  ← aperto
```

---

## Struttura Directory e Configurazione

```
dbt_project/
├── snapshots/
│   ├── snap_customers.sql
│   ├── snap_products.sql
│   └── snap_suppliers.sql
├── dbt_project.yml
└── ...
```

```yaml
# dbt_project.yml
snapshots:
  myproject:
    target_schema: snapshots    # Schema dove vengono materializati
    target_database: analytics  # Database (opzionale, default = profiles.yml)
    +tags: ['snapshots']
    +persist_docs:
      relation: true
      columns: true
```

---

## Strategie di Snapshot

### 1. Timestamp Strategy

Usa una colonna `updated_at` per rilevare i cambiamenti. Efficiente e affidabile quando la sorgente mantiene un timestamp di modifica.

```sql
-- snapshots/snap_customers.sql
{% snapshot snap_customers %}

{{
    config(
        target_schema='snapshots',
        unique_key='customer_id',
        strategy='timestamp',
        updated_at='updated_at',
        invalidate_hard_deletes=True
    )
}}

SELECT
    customer_id,
    email,
    first_name,
    last_name,
    phone,
    tier,
    country_code,
    updated_at,
    -- Aggiungi metadati sorgente utili
    _source_system,
    _extracted_at
FROM {{ source('ecommerce_replica', 'customers') }}
WHERE deleted_at IS NULL  -- Escludi soft-deleted dalla sorgente

{% endsnapshot %}
```

**Quando usare timestamp:**
- La tabella sorgente ha una colonna `updated_at` / `modified_at` affidabile
- La sorgente aggiorna sempre il timestamp quando cambia qualsiasi campo
- Prestazioni migliori su tabelle grandi (scansiona solo righe recenti via `WHERE updated_at > last_snapshot`)

### 2. Check Strategy

Confronta valori specifici di colonne per rilevare cambiamenti. Più robusto ma più costoso computazionalmente.

```sql
-- snapshots/snap_products.sql
{% snapshot snap_products %}

{{
    config(
        target_schema='snapshots',
        unique_key='product_id',
        strategy='check',
        check_cols=['price_cents', 'stock_quantity', 'status', 'category_id', 'supplier_id'],
        invalidate_hard_deletes=True
    )
}}

SELECT
    product_id,
    sku,
    name,
    description,
    price_cents,
    stock_quantity,
    status,
    category_id,
    supplier_id,
    created_at
FROM {{ source('ecommerce_replica', 'products') }}

{% endsnapshot %}
```

**`check_cols='all'`** — confronta tutte le colonne (più sicuro, più lento):

```sql
{{
    config(
        strategy='check',
        check_cols='all',
        unique_key='product_id'
    )
}}
```

**Quando usare check:**
- La sorgente non ha colonna `updated_at` attendibile
- Sistemi legacy che non aggiornano il timestamp su ogni modifica
- Tabelle di configurazione dove ogni campo è critico

---

## Colonne Aggiunte Automaticamente

Ogni tabella snapshot riceve 4 metadati automatici:

```sql
-- Query di esempio sulla tabella snapshot risultante
SELECT
    customer_id,
    email,
    tier,
    dbt_scd_id,          -- Hash univoco della riga (surrogate key della versione)
    dbt_updated_at,      -- Timestamp dell'ultimo aggiornamento del record
    dbt_valid_from,      -- Quando questa versione è diventata attiva
    dbt_valid_to         -- NULL = versione corrente, timestamp = versione storica
FROM snapshots.snap_customers
ORDER BY customer_id, dbt_valid_from;
```

```
customer_id | tier   | dbt_valid_from         | dbt_valid_to
1           | bronze | 2023-01-01 00:00:00 UTC | 2023-06-15 08:00:00 UTC
1           | silver | 2023-06-15 08:00:00 UTC | 2024-01-15 08:00:00 UTC
1           | gold   | 2024-01-15 08:00:00 UTC | NULL
```

---

## Hard Delete Handling

```sql
-- Con invalidate_hard_deletes=True:
-- Se un record scompare dalla sorgente, il suo snapshot viene chiuso

{{
    config(
        strategy='timestamp',
        updated_at='updated_at',
        unique_key='customer_id',
        invalidate_hard_deletes=True  -- Default: False
    )
}}
```

**Con `invalidate_hard_deletes=False` (default):**
- I record eliminati dalla sorgente rimangono aperti nello snapshot
- `dbt_valid_to` rimane NULL anche dopo la cancellazione
- Utile quando la sorgente usa soft-delete e lo snapshot serve come audit trail

**Con `invalidate_hard_deletes=True`:**
- Se un `unique_key` scompare dalla sorgente, `dbt_valid_to` viene impostato al timestamp corrente
- Il record chiuso indica che l'entità non esiste più

---

## Utilizzo degli Snapshot nei Modelli

Gli snapshot vengono referenziati con `{{ ref('snap_customers') }}`:

```sql
-- models/marts/dim_customer.sql
-- SCD Type 2 dimension derivata dallo snapshot

WITH snapshot AS (
    SELECT
        customer_id,
        email,
        first_name,
        last_name,
        tier,
        country_code,
        dbt_valid_from,
        dbt_valid_to,
        dbt_scd_id AS customer_version_key,
        dbt_valid_to IS NULL AS is_current
    FROM {{ ref('snap_customers') }}
),
current_only AS (
    SELECT * FROM snapshot WHERE is_current
),
with_surrogate AS (
    SELECT
        {{ dbt_utils.generate_surrogate_key(['customer_id', 'dbt_valid_from']) }} AS customer_key,
        customer_id,
        email,
        INITCAP(first_name) AS first_name,
        INITCAP(last_name) AS last_name,
        tier,
        country_code,
        dbt_valid_from AS valid_from,
        dbt_valid_to AS valid_to,
        is_current,
        customer_version_key
    FROM snapshot
)

SELECT * FROM with_surrogate
```

### Point-in-Time Query (Bitemporal)

```sql
-- Qual era il tier di ciascun cliente il 1° luglio 2023?
SELECT
    c.customer_id,
    c.email,
    c.tier AS tier_at_2023_07_01,
    o.total_amount_cents
FROM snapshots.snap_customers c
JOIN analytics.fct_orders o
    ON c.customer_id = o.customer_id
    AND o.created_at BETWEEN c.dbt_valid_from AND COALESCE(c.dbt_valid_to, '9999-12-31')
WHERE
    -- Point-in-time: versione del cliente in quel momento
    '2023-07-01' BETWEEN c.dbt_valid_from AND COALESCE(c.dbt_valid_to, '9999-12-31')
    AND DATE_TRUNC('month', o.created_at) = '2023-07-01'
```

---

## Snapshot Avanzati

### Snapshot con Trasformazioni

Non limitarti a passare colonne raw: puoi normalizzare durante lo snapshot.

```sql
-- snapshots/snap_customers_clean.sql
{% snapshot snap_customers_clean %}

{{
    config(
        target_schema='snapshots',
        unique_key='customer_id',
        strategy='timestamp',
        updated_at='updated_at'
    )
}}

SELECT
    customer_id,
    LOWER(TRIM(email)) AS email,              -- Normalizzazione
    INITCAP(first_name) AS first_name,
    INITCAP(last_name) AS last_name,
    REGEXP_REPLACE(phone, '[^0-9+]', '') AS phone,  -- Pulizia
    CASE
        WHEN tier IN ('GOLD', 'Gold', 'gold') THEN 'gold'
        WHEN tier IN ('SILVER', 'Silver', 'silver') THEN 'silver'
        ELSE 'bronze'
    END AS tier,
    updated_at
FROM {{ source('ecommerce_replica', 'customers') }}

{% endsnapshot %}
```

### Snapshot Multi-Source (Union)

```sql
-- snapshots/snap_products_global.sql
{% snapshot snap_products_global %}

{{
    config(
        target_schema='snapshots',
        unique_key='global_product_id',
        strategy='check',
        check_cols=['price_eur_cents', 'status', 'category']
    )
}}

WITH eu_products AS (
    SELECT
        'EU-' || product_id::text AS global_product_id,
        product_id AS source_product_id,
        'EU' AS region,
        name,
        price_eur_cents,
        status,
        category,
        updated_at
    FROM {{ source('eu_catalog', 'products') }}
),
us_products AS (
    SELECT
        'US-' || product_id::text AS global_product_id,
        product_id AS source_product_id,
        'US' AS region,
        name,
        ROUND(price_usd_cents * 0.92) AS price_eur_cents,  -- Conversione approssimativa
        status,
        category,
        updated_at
    FROM {{ source('us_catalog', 'products') }}
)

SELECT * FROM eu_products
UNION ALL
SELECT * FROM us_products

{% endsnapshot %}
```

### Snapshot con Pre/Post Hooks

```sql
-- snapshots/snap_orders.sql
{% snapshot snap_orders %}

{{
    config(
        target_schema='snapshots',
        unique_key='order_id',
        strategy='timestamp',
        updated_at='updated_at',
        pre_hook="SET search_path = snapshots, public",
        post_hook="ANALYZE snapshots.snap_orders"
    )
}}

SELECT
    order_id,
    customer_id,
    status,
    total_amount_cents,
    shipping_address_id,
    updated_at
FROM {{ source('ecommerce_replica', 'orders') }}

{% endsnapshot %}
```

---

## Testing degli Snapshot

```yaml
# snapshots/schema.yml
version: 2

snapshots:
  - name: snap_customers
    description: "Storico SCD2 della tabella customers"
    columns:
      - name: customer_id
        tests:
          - not_null

      - name: dbt_valid_from
        tests:
          - not_null

      - name: tier
        tests:
          - accepted_values:
              values: ['bronze', 'silver', 'gold', 'platinum']

    tests:
      # Non ci devono essere record con valid_from > valid_to
      - dbt_utils.expression_is_true:
          expression: "dbt_valid_to IS NULL OR dbt_valid_to > dbt_valid_from"
          name: snap_customers_valid_dates_consistent

      # SCD_ID deve essere unico globalmente
      - unique:
          column_name: dbt_scd_id
```

Test singolare per verificare correttezza SCD2:

```sql
-- tests/assert_snap_customers_scd2_correct.sql
-- Per ogni customer_id, i periodi di validità non devono sovrapporsi

WITH overlapping AS (
    SELECT
        a.customer_id,
        a.dbt_valid_from AS a_from,
        COALESCE(a.dbt_valid_to, '9999-12-31') AS a_to,
        b.dbt_valid_from AS b_from,
        COALESCE(b.dbt_valid_to, '9999-12-31') AS b_to
    FROM {{ ref('snap_customers') }} a
    JOIN {{ ref('snap_customers') }} b
        ON a.customer_id = b.customer_id
        AND a.dbt_scd_id <> b.dbt_scd_id
        AND a.dbt_valid_from < COALESCE(b.dbt_valid_to, '9999-12-31')
        AND COALESCE(a.dbt_valid_to, '9999-12-31') > b.dbt_valid_from
)

SELECT * FROM overlapping
```

---

## Performance e Ottimizzazione

### Snapshot su Tabelle Grandi

Per tabelle con milioni di righe, la strategy `timestamp` è molto più efficiente:

```sql
-- dbt internamente genera qualcosa del tipo:
-- SELECT * FROM source WHERE updated_at > (SELECT MAX(dbt_updated_at) FROM snapshot)
-- Poi confronta solo le righe recenti con lo snapshot esistente
```

Indici raccomandati sulla tabella snapshot:

```sql
-- Crea dopo il primo run dello snapshot
CREATE INDEX CONCURRENTLY idx_snap_customers_customer_id
    ON snapshots.snap_customers(customer_id);

CREATE INDEX CONCURRENTLY idx_snap_customers_valid_to
    ON snapshots.snap_customers(dbt_valid_to)
    WHERE dbt_valid_to IS NOT NULL;

-- Index per query point-in-time
CREATE INDEX CONCURRENTLY idx_snap_customers_valid_range
    ON snapshots.snap_customers(customer_id, dbt_valid_from, dbt_valid_to);
```

### Snapshot Paralleli

```bash
# Esegui snapshot in parallelo con --threads
dbt snapshot --threads 8

# Solo snapshot specifici
dbt snapshot --select snap_customers snap_products

# Snapshot + test sugli snapshot
dbt build --select snapshots.*+
```

### Gestione Schema Evolution

Quando aggiungi colonne alla sorgente:

```bash
# 1. Aggiungi colonna al SELECT dello snapshot
# 2. Esegui snapshot: dbt aggiunge la colonna alla tabella
dbt snapshot

# 3. Per le righe storiche, la nuova colonna sarà NULL
# Questo è comportamento corretto e atteso per SCD2
```

Se rimuovi colonne, dbt NON le rimuove automaticamente. Devi gestirlo manualmente:
```sql
-- Rimuovi colonna dallo snapshot (run manuale in DWH)
ALTER TABLE snapshots.snap_customers DROP COLUMN IF EXISTS obsolete_field;
-- Poi rimuovi dal SELECT dello snapshot file
```

---

## Workflow Completo con Snapshot

```bash
# 1. Primo run: crea lo snapshot con lo stato corrente
dbt snapshot

# 2. Il giorno dopo: cattura i cambiamenti
dbt snapshot

# 3. Testa integrità dello snapshot
dbt test --select snap_customers

# 4. Rebuild downstream (dim_customer usa lo snapshot)
dbt run --select dim_customer+

# 5. Run completo in produzione
dbt build  # esegue: seed → snapshot → run → test in ordine corretto

# Verifica quante versioni esistono per i top customer
SELECT
    customer_id,
    COUNT(*) AS n_versions,
    MIN(dbt_valid_from) AS first_seen,
    MAX(dbt_valid_from) AS last_change
FROM snapshots.snap_customers
GROUP BY 1
ORDER BY n_versions DESC
LIMIT 20;
```

---

## Differenze Snapshot vs Modelli Incrementali

| Aspetto | Snapshot | Modello Incrementale |
|---------|----------|---------------------|
| Scopo | Storico delle versioni (SCD2) | Append o upsert efficiente |
| Output | Righe multiple per entità | Una riga per entità (tipicamente) |
| Metadati | `dbt_valid_from/to`, `dbt_scd_id` | Nessuno automatico |
| Configurazione | `strategy`, `unique_key`, `updated_at` | `unique_key`, `incremental_strategy` |
| Comando | `dbt snapshot` | `dbt run` |
| Use case | Chi era il cliente il giorno X? | ETL incrementale di fatti |
| Directory | `snapshots/` | `models/` |
| Materializzazione | Sempre tabella | view/table/incremental/ephemeral |
