# Strumenti ETL

L'ecosistema degli strumenti ETL è vasto e in continua evoluzione. Scegliere lo strumento giusto per il caso d'uso giusto è tanto importante quanto scrivere codice di qualità.

## Strumenti di Integrazione Dati

### Apache Spark

Spark è il framework de facto per l'elaborazione distribuita di dataset di grandi dimensioni. La sua API DataFrame unifica batch e streaming.

```python
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

# Inizializzazione Spark Session
spark = SparkSession.builder \
    .appName("ETL_Pipeline") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
    .config("spark.sql.shuffle.partitions", "200") \
    .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
    .getOrCreate()

# Schema esplicito (evita inferenza costosa per file grandi)
schema = StructType([
    StructField("order_id", StringType(), nullable=False),
    StructField("customer_id", StringType(), nullable=False),
    StructField("amount", DoubleType(), nullable=True),
    StructField("created_at", TimestampType(), nullable=True),
    StructField("status", StringType(), nullable=True),
])

# Lettura da S3 con predicate pushdown
df_raw = spark.read \
    .schema(schema) \
    .option("header", "true") \
    .parquet("s3a://data-lake/raw/orders/")

# ETL con Spark
df_clean = (
    df_raw
    .filter(F.col("order_id").isNotNull())
    .filter(F.col("amount").isNotNull() & (F.col("amount") > 0))
    .withColumn("amount", F.round(F.col("amount"), 2))
    .withColumn("year_month", F.date_format("created_at", "yyyy-MM"))
    .withColumn("is_high_value", F.col("amount") > 1000)
    .dropDuplicates(["order_id"])
)

# Window functions per calcoli cumulativi
from pyspark.sql.window import Window

window_spec = Window.partitionBy("customer_id").orderBy("created_at")
df_with_cumsum = df_clean.withColumn(
    "cumulative_spend",
    F.sum("amount").over(window_spec)
)

# Scrittura partizionata
df_clean.write \
    .mode("overwrite") \
    .partitionBy("year_month") \
    .parquet("s3a://data-lake/processed/orders/")

spark.stop()
```

### dbt (Data Build Tool)

dbt trasforma le trasformazioni SQL in un sistema versionabile con test, documentazione e lineage. Vedi modulo 18 per la guida completa; qui i pattern chiave:

```sql
-- models/staging/stg_orders.sql
{{ config(
    materialized='incremental',
    unique_key='order_id',
    on_schema_change='sync_all_columns'
) }}

WITH source AS (
    SELECT * FROM {{ source('raw', 'orders') }}
    {% if is_incremental() %}
    WHERE created_at > (SELECT MAX(created_at) FROM {{ this }})
    {% endif %}
),
cleaned AS (
    SELECT
        order_id,
        customer_id,
        TRIM(LOWER(customer_email)) AS customer_email,
        CAST(amount AS NUMERIC(10,2)) AS amount,
        created_at::TIMESTAMPTZ AS created_at,
        COALESCE(status, 'unknown') AS status
    FROM source
    WHERE order_id IS NOT NULL
      AND customer_id IS NOT NULL
)

SELECT * FROM cleaned
```

### Airbyte

Airbyte è una piattaforma open-source per la replica di dati (EL senza transform). Offre 300+ connettori preconfigurati.

```python
# Python SDK per Airbyte API (gestione programmatica)
import requests

AIRBYTE_URL = "http://localhost:8000/api/v1"

def create_postgres_source(name: str, host: str, port: int, database: str,
                            username: str, password: str) -> str:
    """Crea sorgente PostgreSQL via API Airbyte."""
    payload = {
        "name": name,
        "sourceDefinitionId": "decd338e-5647-4c0b-adf4-da0e75f5a750",
        "workspaceId": get_workspace_id(),
        "connectionConfiguration": {
            "host": host, "port": port,
            "database": database, "username": username,
            "password": password,  # In produzione: usa Secret Manager
            "ssl": True,
            "replication_method": {"method": "CDC"},
        }
    }
    resp = requests.post(f"{AIRBYTE_URL}/sources/create", json=payload)
    resp.raise_for_status()
    return resp.json()["sourceId"]


def trigger_sync(connection_id: str) -> str:
    """Triggera sincronizzazione manuale."""
    resp = requests.post(
        f"{AIRBYTE_URL}/connections/sync",
        json={"connectionId": connection_id}
    )
    resp.raise_for_status()
    return resp.json()["job"]["id"]
```

### Fivetran / Stitch

Soluzioni managed (SaaS) per la replica di dati. Nessun codice da scrivere per le sorgenti standard; configurazione via UI o Terraform.

```hcl
# Terraform per gestire Fivetran connettori
resource "fivetran_connector" "salesforce_prod" {
  group_id    = "your_group_id"
  service     = "salesforce"
  sync_frequency = 360  # minuti

  destination_schema {
    name = "salesforce"
  }

  config {
    username = var.salesforce_username
    password = var.salesforce_password
  }
}
```

---

## Strumenti di Qualità e Validazione

### Great Expectations

```python
import great_expectations as gx
from great_expectations.core.batch import RuntimeBatchRequest

context = gx.get_context()

# Aggiungi datasource
context.add_or_update_datasource(
    name="postgres_source",
    class_name="Datasource",
    execution_engine={"class_name": "SqlAlchemyExecutionEngine",
                      "connection_string": "postgresql://localhost/mydb"},
    data_connectors={
        "default": {
            "class_name": "RuntimeDataConnector",
            "batch_identifiers": ["run_date"]
        }
    }
)

# Crea expectation suite
suite = context.add_or_update_expectation_suite("orders_suite")

# Ottieni validator
batch_request = RuntimeBatchRequest(
    datasource_name="postgres_source",
    data_connector_name="default",
    data_asset_name="orders",
    runtime_parameters={"query": "SELECT * FROM orders LIMIT 10000"},
    batch_identifiers={"run_date": "2024-01-01"}
)
validator = context.get_validator(batch_request=batch_request,
                                   expectation_suite=suite)

# Definisci expectations
validator.expect_column_to_exist("order_id")
validator.expect_column_values_to_not_be_null("order_id")
validator.expect_column_values_to_be_unique("order_id")
validator.expect_column_values_to_not_be_null("customer_id")
validator.expect_column_values_to_be_between("amount", min_value=0, max_value=100000)
validator.expect_column_values_to_be_in_set("status",
    ["pending", "confirmed", "shipped", "delivered", "cancelled"])
validator.expect_column_value_lengths_to_be_between("order_id", min_value=10, max_value=50)

validator.save_expectation_suite()

# Esegui validazione
results = validator.validate()
print(f"Validazione: {'OK' if results.success else 'FALLITA'}")
```

### Soda Core

```python
from soda.scan import Scan

scan = Scan()
scan.set_data_source_name("postgres_dwh")
scan.add_configuration_yaml_str("""
    data_sources:
      postgres_dwh:
        type: postgres
        host: localhost
        database: dwh
        username: etl_user
        password: ${ETL_PASSWORD}
""")

scan.add_sodacl_yaml_str("""
    checks for orders:
      - row_count > 0
      - missing_count(order_id) = 0
      - duplicate_count(order_id) = 0
      - min(amount) >= 0
      - max(amount) < 1000000
      - invalid_percent(customer_email):
          valid format: email
          < 5%
      - freshness(created_at) < 2d
""")

scan.execute()
print(scan.get_logs_text())
if scan.has_check_failures():
    raise RuntimeError("Data quality checks failed")
```

---

## Strumenti di Formato e Serializzazione

### PyArrow per Parquet

```python
import pyarrow as pa
import pyarrow.parquet as pq
from typing import List, Dict, Any

def write_parquet_optimized(
    records: List[Dict[str, Any]],
    output_path: str,
    partition_cols: List[str] = None,
    compression: str = "snappy"
):
    """Scrive Parquet con encoding ottimizzato per query analitiche."""
    table = pa.Table.from_pylist(records)

    # Ottimizza encoding per colonne stringa con bassa cardinalità
    for col_name in table.schema.names:
        col = table.column(col_name)
        if col.type == pa.string() and len(table) > 0:
            unique_ratio = col.value_counts().to_pydict()["values"].count(
                max(col.value_counts().to_pydict()["values"])
            ) / len(table)
            # Usa dictionary encoding per colonne a bassa cardinalità
            if len(col.unique()) < len(table) * 0.1:
                idx = table.schema.get_field_index(col_name)
                table = table.set_column(
                    idx, col_name, col.dictionary_encode()
                )

    pq.write_to_dataset(
        table,
        root_path=output_path,
        partition_cols=partition_cols,
        compression=compression,
        write_statistics=True,
        use_dictionary=True,
        row_group_size=131072  # 128k righe per row group
    )


def read_parquet_with_pushdown(
    path: str,
    filters: List = None,
    columns: List[str] = None
) -> pa.Table:
    """Legge Parquet con predicate e projection pushdown."""
    # filters: [(col, op, val)] es. [("year", "=", "2024"), ("amount", ">", 100)]
    return pq.read_table(
        path,
        filters=filters,   # Predicate pushdown: salta row groups
        columns=columns    # Projection pushdown: legge solo colonne necessarie
    )
```

### DuckDB per Analisi Locale

DuckDB è un database OLAP in-process ideale per elaborazioni locali su file Parquet, CSV, JSON:

```python
import duckdb

# DuckDB può leggere direttamente Parquet, CSV, JSON da S3 o locale
conn = duckdb.connect()

# Analisi su file Parquet senza caricarli in memoria
result = conn.execute("""
    SELECT
        year_month,
        SUM(amount) AS total_revenue,
        COUNT(*) AS order_count,
        AVG(amount) AS avg_order_value
    FROM parquet_scan('s3://data-lake/processed/orders/**/*.parquet')
    WHERE created_at >= '2024-01-01'
    GROUP BY year_month
    ORDER BY year_month
""").df()

# Trasformazione ETL locale con DuckDB (ottimo per file fino a 100GB)
conn.execute("""
    CREATE TABLE stg_orders AS
    SELECT
        order_id,
        customer_id,
        LOWER(TRIM(customer_email)) AS customer_email,
        CAST(amount AS DECIMAL(10,2)) AS amount,
        CAST(created_at AS TIMESTAMP WITH TIME ZONE) AS created_at,
        COALESCE(status, 'unknown') AS status,
        CURRENT_TIMESTAMP AS _loaded_at
    FROM read_csv_auto('raw/orders/*.csv', header=true)
    WHERE order_id IS NOT NULL
      AND amount > 0
""")

# Export in Parquet
conn.execute("""
    COPY stg_orders TO 'processed/stg_orders.parquet'
    (FORMAT PARQUET, COMPRESSION SNAPPY)
""")
```

### Pandas e Polars

```python
import pandas as pd
import polars as pl

# Pandas: versatile, ecosystem ricco, slow su dataset grandi
df_pd = pd.read_csv("orders.csv", dtype={"order_id": str})
df_pd["amount"] = pd.to_numeric(df_pd["amount"], errors="coerce")
df_pd["year_month"] = pd.to_datetime(df_pd["created_at"]).dt.to_period("M")

# Polars: molto più veloce di Pandas, lazy evaluation, nessun GIL
df_pl = pl.read_csv("orders.csv")
result = (
    df_pl
    .with_columns([
        pl.col("amount").cast(pl.Float64),
        pl.col("created_at").str.to_datetime().alias("created_at"),
    ])
    .filter(pl.col("amount") > 0)
    .group_by("customer_id")
    .agg([
        pl.sum("amount").alias("total_spend"),
        pl.count("order_id").alias("order_count"),
        pl.max("created_at").alias("last_order_at")
    ])
)

# Polars Lazy API per dataset grandi (streaming)
lazy_result = (
    pl.scan_parquet("s3://data-lake/orders/**/*.parquet")
    .filter(pl.col("amount") > 0)
    .group_by("year_month")
    .agg(pl.sum("amount").alias("revenue"))
    .sort("year_month")
    .collect(streaming=True)  # Processa in streaming, non carica tutto in RAM
)
```

---

## Change Data Capture Tools

### Debezium

Debezium legge il WAL di PostgreSQL/binlog MySQL e pubblica eventi CDC su Kafka:

```json
{
  "name": "postgres-orders-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "postgres-primary",
    "database.port": "5432",
    "database.user": "debezium",
    "database.password": "${file:/opt/kafka/debezium.properties:database.password}",
    "database.dbname": "production",
    "database.server.name": "prod",
    "table.include.list": "public.orders,public.customers,public.products",
    "plugin.name": "pgoutput",
    "slot.name": "debezium_orders",
    "publication.name": "dbz_publication",
    "snapshot.mode": "initial",
    "heartbeat.interval.ms": "10000",
    "decimal.handling.mode": "double",
    "time.precision.mode": "isostring",
    "transforms": "unwrap",
    "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState",
    "transforms.unwrap.drop.tombstones": "false",
    "transforms.unwrap.delete.handling.mode": "rewrite"
  }
}
```

### AWS DMS (Database Migration Service)

Per migrazioni e replicazione verso servizi cloud AWS:

```python
import boto3

dms = boto3.client("dms", region_name="eu-west-1")

# Crea task di replicazione CDC
response = dms.create_replication_task(
    ReplicationTaskIdentifier="orders-cdc-to-s3",
    SourceEndpointArn="arn:aws:dms:...:endpoint:postgres-source",
    TargetEndpointArn="arn:aws:dms:...:endpoint:s3-target",
    ReplicationInstanceArn="arn:aws:dms:...:rep:instance",
    MigrationType="cdc",
    TableMappings=json.dumps({
        "rules": [
            {
                "rule-type": "selection",
                "rule-id": "1",
                "rule-name": "orders-rule",
                "object-locator": {
                    "schema-name": "public",
                    "table-name": "orders"
                },
                "rule-action": "include"
            }
        ]
    })
)
```

---

## Strumenti di Monitoraggio

### OpenLineage

Standard aperto per il lineage dei dati — compatibile con Airflow, Spark, dbt:

```python
from openlineage.client import OpenLineageClient
from openlineage.client.run import RunEvent, RunState, Run, Job
from openlineage.client.facet import SchemaDatasetFacet, SchemaField
from openlineage.client.dataset import Dataset, DatasetFacets
import uuid
from datetime import datetime

client = OpenLineageClient.from_environment()

run_id = str(uuid.uuid4())
job_name = "orders_etl"
namespace = "data_engineering"

# Evento START
client.emit(RunEvent(
    eventType=RunState.START,
    eventTime=datetime.utcnow().isoformat() + "Z",
    run=Run(runId=run_id),
    job=Job(namespace=namespace, name=job_name),
    inputs=[Dataset(
        namespace="postgres://prod",
        name="public.orders",
        facets=DatasetFacets(schema=SchemaDatasetFacet(fields=[
            SchemaField("order_id", "STRING"),
            SchemaField("amount", "DOUBLE"),
        ]))
    )],
    outputs=[]
))

# ... esegui pipeline ...

# Evento COMPLETE
client.emit(RunEvent(
    eventType=RunState.COMPLETE,
    eventTime=datetime.utcnow().isoformat() + "Z",
    run=Run(runId=run_id),
    job=Job(namespace=namespace, name=job_name),
    inputs=[],
    outputs=[Dataset(
        namespace="postgres://dwh",
        name="public.fact_orders",
    )]
))
```

---

## Confronto Strumenti ETL

| Strumento | Paradigma | Volume | Licensing | Forza |
|-----------|-----------|--------|-----------|-------|
| Python custom | Codice | Qualsiasi | Open | Flessibilità totale |
| Apache Spark | Distribuito | Molto grande | Open | Scale-out orizzontale |
| dbt | ELT / SQL | Data warehouse | Open/Cloud | Transform in SQL, testing |
| Airbyte | EL / Replica | Medio-grande | Open/Cloud | 300+ connettori |
| Fivetran | EL Managed | Qualsiasi | SaaS | Zero manutenzione |
| DuckDB | In-process OLAP | Fino a 100GB | Open | Velocità locale, nessun server |
| Polars | DataFrame | Fino a RAM | Open | 10x più veloce di Pandas |
| Debezium | CDC streaming | Qualsiasi | Open | CDC real-time |
| AWS Glue | ETL managed | Grandi | Cloud | Integrazione AWS |
| Dataflow | ETL managed | Grandi | Cloud | Integrazione GCP |

---

## Linee Guida Scelta

**Piccolo team, budget limitato**: Python custom + dbt + DuckDB/PostgreSQL + Airflow (self-hosted).

**Startup con dati medi**: Airbyte (EL) + dbt (T) + Snowflake/BigQuery (DWH).

**Enterprise con volumi terabyte**: Spark per elaborazione, Kafka + Debezium per CDC, dbt per transform, Airflow/Dagster per orchestrazione.

**Dataset < 10GB su singola macchina**: DuckDB o Polars sono più veloci e semplici di Spark senza bisogno di cluster.

**Priorità sulla velocità di delivery**: Fivetran + Snowflake + dbt elimina quasi completamente il codice di infrastruttura.
