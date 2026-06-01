# Data Governance nel Data Warehouse

La data governance è il framework di politiche, processi, e responsabilità che assicura che i dati siano accurati, accessibili, sicuri, e usati in modo etico e conforme alle normative. È la disciplina che risponde alle domande: chi possiede i dati? Chi può accedervi? Come si sa se un dato è affidabile? Come si traccia la storia di un dato?

## Data Catalog

Il data catalog è l'inventario centralizzato di tutti gli asset dati: tabelle, viste, modelli dbt, dashboard, API. Permette agli utenti di trovare i dati di cui hanno bisogno senza dover chiedere a qualcuno.

```python
# Apache Atlas o DataHub: i catalog open-source più diffusi

# DataHub: esempio di integrazione via API
from datahub.emitter.mcp_builder import (
    DatabaseKeyAspect, SchemaMetadata, OwnershipClass
)
from datahub.emitter.rest_emitter import DatahubRestEmitter
from datahub.metadata.schema_classes import (
    DatasetSnapshotClass, MetadataChangeEventClass,
    SchemaMetadataClass, SchemaFieldClass
)

emitter = DatahubRestEmitter("http://datahub-gms:8080")

# Registrare una tabella nel catalog
dataset_urn = "urn:li:dataset:(urn:li:dataPlatform:postgres,analytics.fact_sales,PROD)"

mce = MetadataChangeEventClass(
    proposedSnapshot=DatasetSnapshotClass(
        urn=dataset_urn,
        aspects=[
            SchemaMetadataClass(
                schemaName="fact_sales",
                platform="urn:li:dataPlatform:postgres",
                version=0,
                hash="",
                platformSchema=None,
                fields=[
                    SchemaFieldClass(
                        fieldPath="date_key",
                        nativeDataType="INT",
                        type=None,
                        description="Data della vendita nel formato YYYYMMDD",
                        nullable=False
                    ),
                    SchemaFieldClass(
                        fieldPath="net_revenue",
                        nativeDataType="NUMERIC(12,2)",
                        type=None,
                        description="Revenue netto (lordo - sconti) in EUR",
                        nullable=False
                    )
                ]
            )
        ]
    )
)

emitter.emit_mce(mce)
```

```sql
-- Data Catalog inline nel database: documenting con COMMENT

-- Commentare tabelle
COMMENT ON TABLE fact_sales IS
'Fact table principale per l''analisi delle vendite.
Granularità: una riga per ogni linea d''ordine.
Owner: Analytics Team (analytics@example.com)
Aggiornamento: ogni giorno alle 06:00 UTC via dbt
SLA: dati disponibili entro le 08:00 UTC per il business';

-- Commentare colonne
COMMENT ON COLUMN fact_sales.date_key IS
'Data della vendita nel formato YYYYMMDD (es: 20240115 = 15 gennaio 2024).
FK verso dim_date. Non contiene mai NULL.';

COMMENT ON COLUMN fact_sales.customer_key IS
'Surrogate key del cliente. FK verso dim_customer.
Valore -1 indica il cliente "Unknown" (dati storici prima del 2020).
Usa is_current=TRUE di dim_customer per il profilo corrente.';

COMMENT ON COLUMN fact_sales.net_revenue IS
'Revenue netto in EUR dopo sconti applicati.
Formula: unit_price * quantity * (1 - discount_pct).
Sempre >= 0. Non include tasse.
Vedi gross_revenue per il valore ante-sconto.';

-- Recuperare la documentazione
SELECT
  c.column_name,
  c.data_type,
  c.is_nullable,
  pgd.description
FROM information_schema.columns c
LEFT JOIN pg_catalog.pg_statio_all_tables st ON c.table_schema = st.schemaname
  AND c.table_name = st.relname
LEFT JOIN pg_catalog.pg_description pgd ON pgd.objoid = st.relid
  AND pgd.objsubid = c.ordinal_position
WHERE c.table_name = 'fact_sales'
ORDER BY c.ordinal_position;
```

## Data Lineage

Il data lineage (lignaggio) traccia il percorso di un dato: da quale sorgente proviene, attraverso quali trasformazioni è passato, in quali output finisce.

```sql
-- Implementazione semplice del lineage nel database
-- In produzione: usare OpenLineage o strumenti dedicati (dbt docs, Atlas, DataHub)

CREATE TABLE data_lineage (
  id SERIAL PRIMARY KEY,
  object_type TEXT NOT NULL,   -- 'table', 'view', 'model', 'pipeline'
  object_name TEXT NOT NULL,
  object_schema TEXT NOT NULL,
  parent_object_name TEXT,
  parent_object_schema TEXT,
  transformation_type TEXT,   -- 'aggregation', 'join', 'filter', 'enrichment'
  transformation_description TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  owner TEXT
);

INSERT INTO data_lineage VALUES
  (DEFAULT, 'table', 'fact_sales', 'mart', 'orders', 'raw', 'join', 'Join con order_items e dim tables', NOW(), 'analytics-team'),
  (DEFAULT, 'table', 'fact_sales', 'mart', 'order_items', 'raw', 'join', 'Aggregazione per ordine', NOW(), 'analytics-team'),
  (DEFAULT, 'table', 'fact_sales', 'mart', 'dim_customer', 'mart', 'lookup', 'Lookup surrogate key', NOW(), 'analytics-team'),
  (DEFAULT, 'view', 'revenue_by_month', 'reporting', 'fact_sales', 'mart', 'aggregation', 'Revenue mensile per categoria', NOW(), 'analytics-team');

-- Query per trovare tutti gli antenati di fact_sales (upstream lineage)
WITH RECURSIVE upstream AS (
  SELECT object_name, object_schema, parent_object_name, parent_object_schema, 0 AS depth
  FROM data_lineage
  WHERE object_name = 'fact_sales' AND object_schema = 'mart'
  
  UNION ALL
  
  SELECT l.object_name, l.object_schema, l.parent_object_name, l.parent_object_schema, u.depth + 1
  FROM data_lineage l
  JOIN upstream u ON l.object_name = u.parent_object_name
    AND l.object_schema = u.parent_object_schema
  WHERE u.depth < 10
)
SELECT DISTINCT parent_object_schema, parent_object_name, depth
FROM upstream
ORDER BY depth, parent_object_schema;
```

```yaml
# dbt genera automaticamente il lineage graph
# Ogni ref() e source() nel codice dbt costruisce il grafo di dipendenze

# models/mart/fact_sales.sql
# Le dipendenze sono esplicite nel codice:
# ref('int_orders_with_items') → int_orders_with_items
# ref('dim_customer') → dim_customer
# ref('dim_product') → dim_product

# 'dbt docs generate' crea un sito web con il lineage graph interattivo
# 'dbt ls --select +fact_sales+' mostra tutte le dipendenze via CLI
```

## Data Ownership e Stewardship

```sql
-- Tabella di ownership degli asset dati
CREATE TABLE data_ownership (
  asset_schema      TEXT NOT NULL,
  asset_name        TEXT NOT NULL,
  asset_type        TEXT NOT NULL,     -- 'table', 'schema', 'database'
  business_owner    TEXT NOT NULL,     -- chi "possiede" il dato dal punto di vista business
  technical_owner   TEXT NOT NULL,     -- chi mantiene il dato tecnicamente
  data_steward      TEXT,              -- chi verifica la qualità del dato
  criticality       TEXT,              -- 'critical', 'high', 'medium', 'low'
  pii_contains      BOOLEAN DEFAULT FALSE,
  last_reviewed     DATE,
  PRIMARY KEY (asset_schema, asset_name)
);

INSERT INTO data_ownership VALUES
  ('mart', 'fact_sales', 'table', 'sales-team@example.com', 'analytics-team@example.com', 'data-steward@example.com', 'critical', false, '2025-01-01'),
  ('mart', 'dim_customer', 'table', 'crm-team@example.com', 'analytics-team@example.com', 'data-privacy@example.com', 'critical', true, '2025-01-01'),
  ('raw', 'orders', 'table', 'ecommerce-team@example.com', 'data-eng@example.com', NULL, 'high', false, '2025-01-01');

-- Asset non revisionati da più di 6 mesi
SELECT *
FROM data_ownership
WHERE last_reviewed < CURRENT_DATE - INTERVAL '6 months'
  OR last_reviewed IS NULL
ORDER BY criticality, last_reviewed NULLS FIRST;
```

## Access Control e Compliance

```sql
-- Matrice di accesso per il DW

-- Schema di governance per i permessi
CREATE TABLE access_policies (
  role_name         TEXT NOT NULL,
  schema_name       TEXT NOT NULL,
  table_name        TEXT,               -- NULL = tutti gli oggetti dello schema
  allowed_ops       TEXT[] NOT NULL,    -- {'SELECT', 'INSERT', 'UPDATE', 'DELETE'}
  row_filter        TEXT,               -- condizione SQL per RLS
  column_mask       JSONB,              -- {"ssn": "mask_ssn(ssn)", "email": "mask_email(email)"}
  purpose           TEXT,               -- perché questo ruolo ha questo accesso
  approved_by       TEXT,
  approved_at       TIMESTAMPTZ
);

-- Generare i comandi GRANT da questa tabella (Infrastructure as Code)
SELECT
  FORMAT(
    'GRANT %s ON %I.%I TO %I;',
    ARRAY_TO_STRING(allowed_ops, ', '),
    schema_name,
    table_name,
    role_name
  ) AS grant_statement
FROM access_policies
WHERE table_name IS NOT NULL;

-- Audit: chi ha accesso a cosa?
SELECT
  r.rolname AS user_or_role,
  t.table_schema,
  t.table_name,
  STRING_AGG(DISTINCT t.privilege_type, ', ' ORDER BY t.privilege_type) AS privileges
FROM information_schema.role_table_grants t
JOIN pg_roles r ON r.rolname = t.grantee
WHERE t.table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY r.rolname, t.table_schema, t.table_name;
```

## SLA e Alerting

```python
#!/usr/bin/env python3
"""
SLA monitor per il data warehouse.
Verifica che i dati siano disponibili entro l'orario SLA concordato.
"""
import psycopg2
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, date, timedelta
import pytz

SLA_DEFINITIONS = {
    'fact_sales': {
        'expected_by': '08:00',    # UTC
        'expected_days': 'weekdays',
        'min_rows': 1000,
        'max_date_lag_days': 1,    # i dati devono essere di ieri al più
        'owner': 'analytics-team@example.com'
    },
    'fact_orders': {
        'expected_by': '07:00',
        'expected_days': 'daily',
        'min_rows': 500,
        'max_date_lag_days': 1,
        'owner': 'data-eng@example.com'
    }
}

def check_table_freshness(conn, table_name: str, max_date_lag_days: int) -> dict:
    """Verifica che la tabella contenga i dati più recenti attesi."""
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT
                MAX(date_key) AS latest_date,
                COUNT(*) AS row_count
            FROM {table_name}
            WHERE date_key >= TO_CHAR(CURRENT_DATE - {max_date_lag_days + 1}, 'YYYYMMDD')::INT
        """)
        row = cur.fetchone()
        latest_date = date(
            int(str(row[0])[:4]),
            int(str(row[0])[4:6]),
            int(str(row[0])[6:8])
        ) if row[0] else None
        
        expected_date = date.today() - timedelta(days=max_date_lag_days)
        
        return {
            'table': table_name,
            'latest_date': latest_date,
            'expected_date': expected_date,
            'row_count': row[1],
            'is_fresh': latest_date >= expected_date if latest_date else False
        }

def run_sla_checks(conn_str: str) -> list:
    """Esegue tutti i check SLA e restituisce i fallimenti."""
    failures = []
    
    with psycopg2.connect(conn_str) as conn:
        for table_name, sla in SLA_DEFINITIONS.items():
            result = check_table_freshness(conn, table_name, sla['max_date_lag_days'])
            
            if not result['is_fresh']:
                failures.append({
                    'table': table_name,
                    'issue': 'data_stale',
                    'latest': result['latest_date'],
                    'expected': result['expected_date'],
                    'owner': sla['owner']
                })
            
            if result['row_count'] < sla['min_rows']:
                failures.append({
                    'table': table_name,
                    'issue': 'low_row_count',
                    'actual': result['row_count'],
                    'expected_min': sla['min_rows'],
                    'owner': sla['owner']
                })
    
    return failures
```

