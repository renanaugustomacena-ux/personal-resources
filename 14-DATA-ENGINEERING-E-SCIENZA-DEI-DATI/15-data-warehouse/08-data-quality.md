# Data Quality nel Data Warehouse

La data quality (qualità del dato) è forse il problema più sottovalutato nei progetti di data engineering. Un DW con dati di scarsa qualità è peggio di non avere un DW: le decisioni aziendali vengono prese sulla base di dati sbagliati, spesso senza che nessuno se ne accorga. "Garbage in, garbage out" è il principio che definisce il legame tra qualità dell'input e affidabilità dell'output.

## Dimensioni della Data Quality

Le dimensioni classiche della data quality:

```
┌─────────────────────────────────────────────────────────────────────┐
│ Dimensioni della Data Quality                                        │
├──────────────────┬──────────────────────────────────────────────────┤
│ Completezza      │ Tutti i dati attesi sono presenti?               │
│                  │ Es: il 5% delle email è NULL nei dati del CRM?   │
├──────────────────┼──────────────────────────────────────────────────┤
│ Accuratezza      │ I dati riflettono la realtà?                     │
│                  │ Es: l'indirizzo corrisponde a un indirizzo reale?  │
├──────────────────┼──────────────────────────────────────────────────┤
│ Coerenza         │ I dati sono consistenti tra sistemi?             │
│                  │ Es: stessa valuta tra OLTP e DW?                 │
├──────────────────┼──────────────────────────────────────────────────┤
│ Tempestività     │ I dati sono abbastanza recenti per la decisione? │
│                  │ Es: dati di ieri usati per decisione di oggi?    │
├──────────────────┼──────────────────────────────────────────────────┤
│ Unicità          │ Nessun duplicato non intenzionale?               │
│                  │ Es: lo stesso ordine caricato due volte?         │
├──────────────────┼──────────────────────────────────────────────────┤
│ Validità         │ I dati rispettano le regole di business?         │
│                  │ Es: quantità negativa in un ordine?              │
└──────────────────┴──────────────────────────────────────────────────┘
```

## Controlli di Qualità con SQL

```sql
-- Suite completa di data quality checks per fact_sales

-- 1. Completezza: quante righe mancano di dimensioni critiche?
SELECT
  COUNT(*) AS total_rows,
  COUNT(date_key) AS has_date,
  COUNT(customer_key) AS has_customer,
  COUNT(product_key) AS has_product,
  COUNT(*) - COUNT(date_key) AS missing_date,
  COUNT(*) - COUNT(customer_key) AS missing_customer,
  COUNT(*) - COUNT(net_revenue) AS missing_revenue,
  ROUND((COUNT(*) - COUNT(customer_key)) * 100.0 / COUNT(*), 2) AS pct_missing_customer
FROM fact_sales
WHERE date_key BETWEEN 20240101 AND 20241231;

-- 2. Unicità: ci sono ordini duplicati?
WITH duplicate_check AS (
  SELECT
    order_id,
    COUNT(*) AS occurrences
  FROM fact_sales
  GROUP BY order_id
  HAVING COUNT(*) > 1
)
SELECT
  COUNT(*) AS duplicate_order_count,
  SUM(occurrences) AS total_duplicate_rows
FROM duplicate_check;

-- 3. Validità: misure fuori range
SELECT
  COUNT(*) AS total_rows,
  COUNT(CASE WHEN net_revenue < 0 THEN 1 END) AS negative_revenue_rows,
  COUNT(CASE WHEN quantity <= 0 THEN 1 END) AS invalid_quantity_rows,
  COUNT(CASE WHEN unit_price <= 0 THEN 1 END) AS invalid_price_rows,
  COUNT(CASE WHEN net_revenue > 1000000 THEN 1 END) AS suspiciously_high_revenue
FROM fact_sales;

-- 4. Coerenza referenziale: FK che non trovano match nelle dimension
SELECT
  f.customer_key,
  COUNT(*) AS orphaned_rows
FROM fact_sales f
LEFT JOIN dim_customer c ON c.customer_key = f.customer_key
WHERE c.customer_key IS NULL
GROUP BY f.customer_key
ORDER BY orphaned_rows DESC;

-- 5. Tempestività: i dati più recenti di ieri sono presenti?
SELECT
  MAX(CAST(date_key::TEXT AS DATE)) AS latest_date_in_dw,
  CURRENT_DATE - 1 AS expected_latest_date,
  CURRENT_DATE - 1 - MAX(CAST(date_key::TEXT AS DATE)) AS days_behind
FROM fact_sales;

-- 6. Confronto con sorgente (riconciliazione)
-- Confrontare il totale delle vendite tra OLTP e DW
-- (da eseguire contro due connessioni distinte)
WITH oltp_total AS (
  SELECT SUM(total_amount) AS revenue
  FROM /* oltp_db */ orders
  WHERE DATE(created_at) = '2024-01-15'
    AND status = 'completed'
),
dw_total AS (
  SELECT SUM(net_revenue) AS revenue
  FROM fact_sales
  WHERE date_key = 20240115
)
SELECT
  o.revenue AS oltp_revenue,
  d.revenue AS dw_revenue,
  o.revenue - d.revenue AS discrepancy,
  ROUND(ABS(o.revenue - d.revenue) / NULLIF(o.revenue, 0) * 100, 4) AS discrepancy_pct
FROM oltp_total o, dw_total d;
```

## Great Expectations: Framework di Data Quality

Great Expectations è il framework Python standard per la data quality. Permette di definire "expectations" (aspettative sui dati) che vengono verificate automaticamente.

```python
import great_expectations as gx
from great_expectations.core.batch import RuntimeBatchRequest
import pandas as pd

# Inizializzare il contesto
context = gx.get_context()

# Connettere la sorgente dati
datasource_config = {
    "name": "warehouse_datasource",
    "class_name": "Datasource",
    "execution_engine": {
        "class_name": "SqlAlchemyExecutionEngine",
        "connection_string": "postgresql://user:pass@dw-host/warehouse"
    },
    "data_connectors": {
        "default_runtime_data_connector_name": {
            "class_name": "RuntimeDataConnector",
            "batch_identifiers": ["default_identifier_name"]
        }
    }
}
context.add_datasource(**datasource_config)

# Definire le expectations per fact_sales
expectation_suite_name = "fact_sales_suite"
suite = context.create_expectation_suite(
    expectation_suite_name=expectation_suite_name,
    overwrite_existing=True
)

validator = context.get_validator(
    batch_request=RuntimeBatchRequest(
        datasource_name="warehouse_datasource",
        data_connector_name="default_runtime_data_connector_name",
        data_asset_name="fact_sales",
        runtime_parameters={"query": "SELECT * FROM fact_sales WHERE date_key = 20240115"},
        batch_identifiers={"default_identifier_name": "fact_sales_20240115"}
    ),
    expectation_suite_name=expectation_suite_name
)

# Definire le expectations
# Colonne obbligatorie
validator.expect_column_to_exist("date_key")
validator.expect_column_to_exist("customer_key")
validator.expect_column_to_exist("net_revenue")

# Not null
validator.expect_column_values_to_not_be_null("date_key")
validator.expect_column_values_to_not_be_null("customer_key")
validator.expect_column_values_to_not_be_null("net_revenue")

# Unicità
validator.expect_compound_columns_to_be_unique(
    column_list=["date_key", "customer_key", "product_key", "order_id"]
)

# Range valori
validator.expect_column_values_to_be_between(
    column="net_revenue",
    min_value=0,
    max_value=1_000_000
)

validator.expect_column_values_to_be_between(
    column="quantity",
    min_value=1,
    max_value=10_000
)

# Valori attesi
validator.expect_column_values_to_be_in_set(
    column="status",
    value_set=["pending", "processing", "completed", "cancelled", "returned"]
)

# Statistiche aggregate
validator.expect_table_row_count_to_be_between(
    min_value=1_000,
    max_value=10_000_000
)

validator.expect_column_mean_to_be_between(
    column="net_revenue",
    min_value=10,
    max_value=500
)

# Freshness: la data più recente non deve essere più vecchia di 2 giorni
import datetime
max_age = datetime.date.today() - datetime.timedelta(days=2)
validator.expect_column_max_to_be_between(
    column="date_key",
    min_value=int(max_age.strftime('%Y%m%d'))
)

# Salvare le expectations
validator.save_expectation_suite(discard_failed_expectations=False)

# Eseguire la validazione
checkpoint = context.add_or_update_checkpoint(
    name="fact_sales_checkpoint",
    validations=[
        {
            "batch_request": RuntimeBatchRequest(
                datasource_name="warehouse_datasource",
                data_connector_name="default_runtime_data_connector_name",
                data_asset_name="fact_sales",
                runtime_parameters={"query": "SELECT * FROM fact_sales WHERE date_key = 20240115"},
                batch_identifiers={"default_identifier_name": "fact_sales_20240115"}
            ),
            "expectation_suite_name": "fact_sales_suite"
        }
    ]
)

results = checkpoint.run()
print(f"Validazione {'PASSATA' if results.success else 'FALLITA'}")
```

## Data Quality nel Pipeline ETL

```python
# Integrare i controlli di qualità nell'ETL

from dataclasses import dataclass
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class QualityCheckResult:
    check_name: str
    passed: bool
    rows_failing: int
    total_rows: int
    error_message: Optional[str] = None

def run_quality_checks(df: pd.DataFrame) -> List[QualityCheckResult]:
    """Esegue tutti i controlli di qualità su un DataFrame."""
    results = []
    
    # Check 1: not null su colonne critiche
    for col in ['order_id', 'customer_id', 'amount']:
        null_count = df[col].isna().sum()
        results.append(QualityCheckResult(
            check_name=f"not_null_{col}",
            passed=null_count == 0,
            rows_failing=null_count,
            total_rows=len(df),
            error_message=f"{null_count} righe con {col} NULL" if null_count > 0 else None
        ))
    
    # Check 2: unicità
    dup_count = df.duplicated(subset=['order_id']).sum()
    results.append(QualityCheckResult(
        check_name="unique_order_id",
        passed=dup_count == 0,
        rows_failing=dup_count,
        total_rows=len(df)
    ))
    
    # Check 3: range di valori
    negative_amount = (df['amount'] < 0).sum()
    results.append(QualityCheckResult(
        check_name="positive_amount",
        passed=negative_amount == 0,
        rows_failing=negative_amount,
        total_rows=len(df)
    ))
    
    return results

def handle_quality_failures(
    df: pd.DataFrame,
    results: List[QualityCheckResult],
    threshold: float = 0.01  # fallisce il pipeline se >1% righe fallisce
) -> pd.DataFrame:
    """
    Gestisce le righe che falliscono i controlli di qualità.
    Strategia: quarantena (salva le righe problematiche separatamente).
    """
    critical_failures = [r for r in results if not r.passed and r.rows_failing > 0]
    
    if not critical_failures:
        return df
    
    for failure in critical_failures:
        failure_rate = failure.rows_failing / failure.total_rows
        logger.warning(
            f"Quality check '{failure.check_name}' fallito: "
            f"{failure.rows_failing}/{failure.total_rows} righe ({failure_rate:.2%})"
        )
        
        if failure_rate > threshold:
            raise ValueError(
                f"Quality check '{failure.check_name}' supera la soglia di fallimento: "
                f"{failure_rate:.2%} > {threshold:.2%}"
            )
    
    # Quarantena: salvare le righe problematiche
    bad_order_ids = df[df['amount'] < 0]['order_id'].tolist()
    quarantine_df = df[df['order_id'].isin(bad_order_ids)]
    clean_df = df[~df['order_id'].isin(bad_order_ids)]
    
    if len(quarantine_df) > 0:
        quarantine_df.to_sql(
            'quarantine_orders',
            engine,
            if_exists='append',
            index=False
        )
        logger.warning(f"Messe in quarantena {len(quarantine_df)} righe problematiche")
    
    return clean_df
```

## Monitoring della Data Quality nel Tempo

```sql
-- Tabella per tracciare le metriche di qualità nel tempo
CREATE TABLE dq_metrics (
  check_time      TIMESTAMPTZ DEFAULT NOW(),
  table_name      TEXT NOT NULL,
  check_name      TEXT NOT NULL,
  date_key        INT,                 -- per trend su data specifica
  total_rows      BIGINT,
  failing_rows    BIGINT,
  failing_pct     NUMERIC(5,2),
  passed          BOOLEAN GENERATED ALWAYS AS (failing_rows = 0) STORED
);

-- Alert automatico se la qualità degrada
SELECT
  table_name,
  check_name,
  MAX(CASE WHEN check_time = (SELECT MAX(check_time) FROM dq_metrics WHERE table_name = d.table_name) THEN failing_pct END) AS current_failing_pct,
  AVG(failing_pct) AS avg_failing_pct_30d,
  STDDEV(failing_pct) AS stddev_30d
FROM dq_metrics d
WHERE check_time > NOW() - INTERVAL '30 days'
GROUP BY table_name, check_name
HAVING MAX(CASE WHEN check_time > NOW() - INTERVAL '1 day' THEN failing_pct END) >
       AVG(failing_pct) + 2 * STDDEV(failing_pct);  -- z-score > 2: anomalia
```

