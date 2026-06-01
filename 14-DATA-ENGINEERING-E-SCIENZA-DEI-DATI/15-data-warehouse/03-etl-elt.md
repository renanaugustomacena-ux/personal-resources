# ETL vs ELT nel Data Warehouse

ETL (Extract, Transform, Load) ed ELT (Extract, Load, Transform) sono i due paradigmi principali per spostare i dati dalle sorgenti al data warehouse. La differenza fondamentale è dove avvengono le trasformazioni: nel middleware (ETL) o nel data warehouse stesso (ELT). La scelta tra i due impatta profondamente l'architettura, le skill richieste, e i costi operativi.

## ETL: Extract, Transform, Load

Nel paradigma ETL tradizionale, un sistema intermedio (es. Informatica, Talend, SSIS, Apache Spark) estrae i dati dalla sorgente, li trasforma in memoria o su disco, e carica il risultato trasformato nel data warehouse.

```
Sorgente → [Extraction] → [Staging Temp] → [Transformation] → [Loading] → DW
                                                  │
                                           Tool ETL
                                           (Spark, SSIS,
                                            Talend, Glue)
```

```python
# Esempio ETL con Python + Pandas (piccola scala)
import pandas as pd
import psycopg2
from sqlalchemy import create_engine
from datetime import datetime, timedelta

def extract_orders_from_oltp(oltp_conn_str: str, since_date: datetime) -> pd.DataFrame:
    """Step 1: Estrarre ordini dalla sorgente OLTP."""
    query = """
        SELECT
            o.id AS order_id,
            o.customer_id,
            o.created_at,
            o.status,
            oi.product_id,
            oi.quantity,
            oi.unit_price,
            oi.discount
        FROM orders o
        JOIN order_items oi ON oi.order_id = o.id
        WHERE o.created_at >= %(since_date)s
        ORDER BY o.created_at
    """
    engine = create_engine(oltp_conn_str)
    return pd.read_sql(query, engine, params={'since_date': since_date})

def transform_orders(raw_df: pd.DataFrame, dim_product: pd.DataFrame, dim_customer: pd.DataFrame) -> pd.DataFrame:
    """Step 2: Trasformare i dati per il DW."""
    # Calcolare misure derivate
    raw_df['gross_revenue'] = raw_df['quantity'] * raw_df['unit_price']
    raw_df['discount_amount'] = raw_df['gross_revenue'] * raw_df['discount'].fillna(0)
    raw_df['net_revenue'] = raw_df['gross_revenue'] - raw_df['discount_amount']
    
    # Generare date_key (YYYYMMDD)
    raw_df['date_key'] = raw_df['created_at'].dt.strftime('%Y%m%d').astype(int)
    
    # Lookup per surrogate keys (join con dimension tables)
    # In produzione: le dimension tables sono già nel DW, qui si usa la cache locale
    raw_df = raw_df.merge(
        dim_customer[['customer_id', 'customer_key', 'is_current']].query('is_current == True'),
        on='customer_id',
        how='left'
    )
    raw_df = raw_df.merge(
        dim_product[['product_id', 'product_key']],
        on='product_id',
        how='left'
    )
    
    # Gestire i valori mancanti (nuovi clienti/prodotti non ancora nel DW)
    # In produzione: usare la "unknown dimension member" (key=-1)
    raw_df['customer_key'] = raw_df['customer_key'].fillna(-1).astype(int)
    raw_df['product_key'] = raw_df['product_key'].fillna(-1).astype(int)
    
    # Selezionare e rinominare per la fact table
    return raw_df[[
        'date_key', 'customer_key', 'product_key',
        'order_id', 'quantity', 'unit_price', 'discount_amount',
        'gross_revenue', 'net_revenue'
    ]]

def load_to_warehouse(df: pd.DataFrame, dw_conn_str: str):
    """Step 3: Caricare nel data warehouse."""
    engine = create_engine(dw_conn_str)
    
    df.to_sql(
        'fact_sales_staging',
        engine,
        if_exists='append',
        index=False,
        method='multi',    # batch insert
        chunksize=10000
    )
    
    # Merge dallo staging alla tabella finale (deduplicazione)
    with engine.connect() as conn:
        conn.execute("""
            INSERT INTO fact_sales
            SELECT * FROM fact_sales_staging
            ON CONFLICT (date_key, customer_key, product_key, order_id)
            DO NOTHING;
            
            TRUNCATE fact_sales_staging;
        """)

# Orchestrazione
def run_etl():
    OLTP_DSN = "postgresql://user:pass@oltp-host/production"
    DW_DSN = "postgresql://user:pass@dw-host/warehouse"
    
    since_date = datetime.now() - timedelta(days=1)
    
    print(f"ETL iniziato: {datetime.now()}")
    raw = extract_orders_from_oltp(OLTP_DSN, since_date)
    print(f"Estratte {len(raw)} righe")
    
    # Caricare le dimension per il lookup
    engine = create_engine(DW_DSN)
    dim_product = pd.read_sql("SELECT product_id, product_key FROM dim_product", engine)
    dim_customer = pd.read_sql("SELECT customer_id, customer_key, is_current FROM dim_customer", engine)
    
    transformed = transform_orders(raw, dim_product, dim_customer)
    print(f"Trasformate {len(transformed)} righe")
    
    load_to_warehouse(transformed, DW_DSN)
    print(f"ETL completato: {datetime.now()}")
```

## ELT: Extract, Load, Transform

Nel paradigma ELT, i dati vengono caricati nel data warehouse nella loro forma grezza e poi trasformati direttamente nel DW usando SQL o strumenti come dbt. Questo approccio è diventato dominante con l'avvento di DW cloud come BigQuery, Snowflake e Redshift che hanno potenza computazionale massiccia a costi relativamente bassi.

```sql
-- ELT con SQL direttamente nel DW (BigQuery/Snowflake/Redshift/PostgreSQL)

-- Step 1: Raw data caricata in tabelle staging (via Fivetran, Airbyte, COPY, etc.)
-- Esempio: raw_orders caricata as-is dalla sorgente
CREATE TABLE raw.orders (
  id VARCHAR,
  customer_id VARCHAR,
  created_at TIMESTAMP,
  status VARCHAR,
  raw_json JSONB,     -- spesso i tool moderni caricano tutto in JSON
  _loaded_at TIMESTAMP DEFAULT NOW()  -- metadato di caricamento
);

-- Step 2: Trasformazioni SQL nel DW

-- Modello staging: pulizia e casting dei tipi
CREATE OR REPLACE VIEW stg.orders AS
SELECT
  id::INT AS order_id,
  customer_id::INT,
  created_at AT TIME ZONE 'UTC' AS created_at_utc,
  LOWER(TRIM(status)) AS status,
  (raw_json->>'total_amount')::NUMERIC AS total_amount,
  _loaded_at
FROM raw.orders
WHERE id IS NOT NULL
  AND created_at IS NOT NULL;

-- Modello intermedio: calcolo business logic
CREATE MATERIALIZED VIEW int.order_metrics AS
SELECT
  o.order_id,
  o.customer_id,
  o.created_at_utc,
  o.status,
  SUM(oi.quantity * oi.unit_price) AS gross_revenue,
  SUM(oi.quantity * oi.unit_price * (1 - COALESCE(oi.discount_pct, 0))) AS net_revenue,
  COUNT(oi.id) AS line_item_count
FROM stg.orders o
JOIN stg.order_items oi ON oi.order_id = o.order_id
GROUP BY o.order_id, o.customer_id, o.created_at_utc, o.status;

-- Modello finale: fact table
CREATE TABLE mart.fact_sales AS
SELECT
  TO_CHAR(o.created_at_utc, 'YYYYMMDD')::INT AS date_key,
  dc.customer_key,
  dp.product_key,
  o.order_id::TEXT AS order_id,
  oi.quantity,
  oi.unit_price,
  oi.quantity * oi.unit_price - COALESCE(oi.discount_amount, 0) AS net_revenue
FROM stg.orders o
JOIN stg.order_items oi ON oi.order_id = o.order_id
JOIN dim_customer dc ON dc.customer_id = o.customer_id AND dc.is_current = TRUE
JOIN dim_product dp ON dp.product_id = oi.product_id;
```

## Confronto ETL vs ELT

| Dimensione | ETL | ELT |
|-----------|-----|-----|
| Dove avvengono le trasformazioni | Tool intermedio | Nel DW |
| Linguaggio trasformazioni | Python, Java, GUI | SQL |
| Scalabilità | Limitata dallo strumento ETL | Scalabilità del DW |
| Costo compute | Server ETL dedicato | DW (può essere costoso) |
| Latency | Medio-alta (3 step) | Bassa (solo 2 step) |
| Privacy/Compliance | I dati raw non entrano nel DW | Tutti i dati raw nel DW |
| Testing | Complesso | Semplice (SQL unit test) |
| Manutenibilità | Dipende dal tool | Alta (SQL leggibile) |
| Tool principali | Spark, Informatica, Talend, Glue | dbt, SQL, BigQuery, Snowflake |

La tendenza del mercato è chiaramente verso ELT: i DW cloud sono abbastanza potenti e i costi di storage sono abbastanza bassi da rendere conveniente caricare i dati raw e trasformarli nel DW. dbt (data build tool) ha standardizzato questo pattern.

## Incremental Loading

Il caricamento incrementale è fondamentale per l'efficienza: invece di ricaricare tutto ogni volta, si carica solo il delta.

```sql
-- Strategia 1: Full Refresh (semplice ma costosa)
-- Cancella tutto e ricarica da zero
-- Accettabile solo per tabelle piccole (<1M righe) o quando la sorgente non ha timestamp

TRUNCATE TABLE dim_product;
INSERT INTO dim_product SELECT * FROM raw.products;

-- Strategia 2: Insert-only con high-water mark (per dati immutabili)
-- Tracciamo l'ultimo record caricato per caricare solo i nuovi

CREATE TABLE etl_watermarks (
  table_name TEXT PRIMARY KEY,
  last_loaded_at TIMESTAMPTZ,
  last_loaded_id BIGINT
);

-- Caricare solo gli ordini nuovi dal timestamp dell'ultimo caricamento
DO $$
DECLARE
  v_last_loaded TIMESTAMPTZ;
  v_rows_loaded INT;
BEGIN
  SELECT last_loaded_at INTO v_last_loaded
  FROM etl_watermarks WHERE table_name = 'fact_orders';
  
  v_last_loaded := COALESCE(v_last_loaded, '2000-01-01'::TIMESTAMPTZ);
  
  INSERT INTO fact_orders
  SELECT ...
  FROM raw.orders
  WHERE created_at > v_last_loaded;
  
  GET DIAGNOSTICS v_rows_loaded = ROW_COUNT;
  
  -- Aggiornare il watermark
  INSERT INTO etl_watermarks (table_name, last_loaded_at)
  VALUES ('fact_orders', NOW())
  ON CONFLICT (table_name) DO UPDATE SET last_loaded_at = EXCLUDED.last_loaded_at;
  
  RAISE NOTICE 'Loaded % rows', v_rows_loaded;
END;
$$;

-- Strategia 3: Upsert per dati mutabili (la riga nella sorgente può cambiare)
-- INSERT ... ON CONFLICT DO UPDATE (PostgreSQL)
INSERT INTO dim_customer (customer_id, name, email, city, region, is_current, effective_from)
SELECT customer_id, name, email, city, region, TRUE, CURRENT_DATE
FROM raw.customers
ON CONFLICT (customer_id) DO UPDATE
SET
  name = EXCLUDED.name,
  email = EXCLUDED.email,
  city = EXCLUDED.city,
  region = EXCLUDED.region;
-- NOTA: questo è SCD1 (overwrite). Per SCD2 serve la procedura più complessa.
```

## Change Data Capture (CDC)

Il CDC cattura i cambiamenti nel database sorgente (INSERT/UPDATE/DELETE) e li invia al DW in tempo reale o near-real-time.

```python
# Debezium: CDC via logical replication PostgreSQL
# Configurazione connector (JSON per Kafka Connect)
debezium_config = {
    "name": "orders-cdc-connector",
    "config": {
        "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
        "database.hostname": "oltp-db.example.com",
        "database.port": "5432",
        "database.user": "debezium",
        "database.password": "debezium_password",
        "database.dbname": "production",
        "database.server.name": "prod_oltp",
        
        # Tabelle da catturare
        "table.include.list": "public.orders,public.order_items,public.customers",
        
        # Plugin per logical decoding
        "plugin.name": "pgoutput",
        
        # Slot di replica dedicato
        "slot.name": "debezium_warehouse_slot",
        
        # Trasformazioni di routing
        "transforms": "route",
        "transforms.route.type": "org.apache.kafka.connect.transforms.ReplaceField$Value",
        
        # Formato Avro per schema evolution
        "value.converter": "io.confluent.kafka.serializers.KafkaAvroSerializer",
        "value.converter.schema.registry.url": "http://schema-registry:8081"
    }
}

# Consumer Kafka → DW
from kafka import KafkaConsumer
import json
import psycopg2

def consume_cdc_events():
    consumer = KafkaConsumer(
        'prod_oltp.public.orders',
        bootstrap_servers=['kafka:9092'],
        group_id='warehouse-loader',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    dw_conn = psycopg2.connect("host=dw-db user=etl dbname=warehouse")
    
    for message in consumer:
        event = message.value
        
        op = event['payload']['op']    # 'c'=create, 'u'=update, 'd'=delete, 'r'=read/snapshot
        after = event['payload'].get('after', {})
        before = event['payload'].get('before', {})
        
        if op in ('c', 'u'):
            # Upsert nella staging table
            with dw_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO raw.orders_cdc (order_id, customer_id, status, updated_at, cdc_op)
                    VALUES (%(id)s, %(customer_id)s, %(status)s, NOW(), %(op)s)
                    ON CONFLICT (order_id) DO UPDATE
                    SET customer_id = EXCLUDED.customer_id,
                        status = EXCLUDED.status,
                        updated_at = EXCLUDED.updated_at,
                        cdc_op = EXCLUDED.cdc_op
                """, {**after, 'op': op})
        
        elif op == 'd':
            # Soft delete: non cancelliamo mai dal DW
            with dw_conn.cursor() as cur:
                cur.execute("""
                    UPDATE raw.orders_cdc
                    SET is_deleted = TRUE, deleted_at = NOW()
                    WHERE order_id = %(id)s
                """, before)
        
        dw_conn.commit()
```

