# Operatori Airflow

Gli operatori sono le unità di lavoro atomiche in Airflow. Ogni task è un'istanza di un operatore. La ricca libreria di operatori built-in e di provider copre la maggior parte dei casi d'uso senza dover scrivere codice da zero.

## PythonOperator e TaskFlow

Il modo più comune per eseguire codice Python personalizzato:

```python
from airflow.operators.python import PythonOperator

# Stile classico
def process_data(run_date: str, batch_size: int, **context):
    """Il parametro **context è obbligatorio se usi template."""
    records = fetch_records(run_date, limit=batch_size)
    return len(records)

task = PythonOperator(
    task_id="process",
    python_callable=process_data,
    op_kwargs={
        "run_date":   "{{ ds }}",      # Template risolto a runtime
        "batch_size": 50_000
    }
)

# TaskFlow (Airflow 2.0+) — più pythonic
from airflow.decorators import task

@task(
    task_id="process_v2",
    retries=3,
    retry_delay=timedelta(minutes=5)
)
def process_data_v2(run_date: str) -> dict:
    records = fetch_records(run_date)
    return {"count": len(records), "run_date": run_date}
```

## BashOperator

```python
from airflow.operators.bash import BashOperator

# Esegue comandi shell
run_dbt = BashOperator(
    task_id="dbt_run",
    bash_command=(
        "cd /opt/dbt && "
        "dbt run --select marts+ --target {{ var.value.dbt_target }} "
        "--vars '{run_date: {{ ds }}}'"
    ),
    env={
        "DBT_PROFILES_DIR": "/opt/dbt/profiles",
        "SNOWFLAKE_ACCOUNT":  "{{ conn.snowflake_dwh.host }}",
    },
    output_encoding="utf-8",
    cwd="/opt/dbt"
)

# Script multi-riga
validate_data = BashOperator(
    task_id="validate",
    bash_command="""
        set -e
        echo "Validazione per {{ ds }}"
        
        COUNT=$(psql $DWH_URL -t -c "
            SELECT COUNT(*) FROM fact_orders
            WHERE DATE(created_at) = '{{ ds }}'
        ")
        
        if [ "$COUNT" -lt "100" ]; then
            echo "ERRORE: solo $COUNT righe caricate, minimo 100"
            exit 1
        fi
        
        echo "OK: $COUNT righe validate"
    """,
    env={"DWH_URL": "{{ conn.postgres_dwh.get_uri() }}"}
)
```

## Operatori Database

### PostgresOperator

```python
from airflow.providers.postgres.operators.postgres import PostgresOperator

# SQL inline
refresh_mv = PostgresOperator(
    task_id="refresh_materialized_view",
    postgres_conn_id="postgres_dwh",
    sql="""
        REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_revenue;
        ANALYZE mv_daily_revenue;
    """
)

# SQL da file
run_migration = PostgresOperator(
    task_id="run_migration",
    postgres_conn_id="postgres_dwh",
    sql="sql/migrations/add_customer_segment.sql",  # Path relativo a dags/
    parameters={"run_date": "{{ ds }}"}
)

# Con template nel SQL
upsert_data = PostgresOperator(
    task_id="upsert_daily_summary",
    postgres_conn_id="postgres_dwh",
    sql="""
        INSERT INTO daily_order_summary (run_date, order_count, revenue)
        SELECT '{{ ds }}'::DATE, COUNT(*), SUM(amount)
        FROM fact_orders
        WHERE DATE(created_at) = '{{ ds }}'
        ON CONFLICT (run_date) DO UPDATE SET
            order_count = EXCLUDED.order_count,
            revenue = EXCLUDED.revenue,
            updated_at = NOW();
    """
)
```

### BigQueryOperator

```python
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryInsertJobOperator,
    BigQueryCreateEmptyTableOperator,
    BigQueryDeleteTableOperator,
)

# Esegue una query e scrive il risultato
run_aggregation = BigQueryInsertJobOperator(
    task_id="compute_daily_revenue",
    gcp_conn_id="google_cloud_default",
    configuration={
        "query": {
            "query": """
                CREATE OR REPLACE TABLE `{{ var.value.bq_dataset }}.daily_revenue_{{ ds_nodash }}`
                AS
                SELECT
                    DATE(created_at) AS sale_date,
                    country_code,
                    SUM(amount) AS revenue,
                    COUNT(*) AS orders
                FROM `{{ var.value.bq_dataset }}.fact_orders`
                WHERE DATE(created_at) = '{{ ds }}'
                GROUP BY 1, 2
            """,
            "useLegacySql": False,
            "priority": "BATCH",
            "createDisposition": "CREATE_IF_NEEDED",
            "writeDisposition": "WRITE_TRUNCATE",
        }
    }
)
```

### SnowflakeOperator

```python
from airflow.providers.snowflake.operators.snowflake import SnowflakeOperator

run_snowflake_query = SnowflakeOperator(
    task_id="refresh_daily_agg",
    snowflake_conn_id="snowflake_dwh",
    sql="""
        MERGE INTO DAILY_ORDERS AS t
        USING (
            SELECT
                DATE(CREATED_AT) AS ORDER_DATE,
                COUNT(*) AS ORDER_COUNT,
                SUM(AMOUNT) AS REVENUE
            FROM ORDERS
            WHERE DATE(CREATED_AT) = '{{ ds }}'
            GROUP BY 1
        ) AS s ON t.ORDER_DATE = s.ORDER_DATE
        WHEN MATCHED THEN UPDATE SET
            t.ORDER_COUNT = s.ORDER_COUNT,
            t.REVENUE = s.REVENUE
        WHEN NOT MATCHED THEN INSERT VALUES (s.ORDER_DATE, s.ORDER_COUNT, s.REVENUE);
    """,
    warehouse="TRANSFORM_WH",
    database="DWH",
    schema="STAGING",
    role="TRANSFORMER"
)
```

---

## Sensori

I sensori aspettano che una condizione esterna sia soddisfatta prima di procedere.

### S3KeySensor

```python
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor

wait_for_file = S3KeySensor(
    task_id="wait_for_daily_export",
    aws_conn_id="aws_default",
    bucket_name="data-lake-prod",
    bucket_key="raw/orders/{{ ds }}/part-*.parquet",
    wildcard_match=True,
    timeout=3600,         # Timeout dopo 1 ora
    poke_interval=120,    # Controlla ogni 2 minuti
    mode="reschedule",    # Libera il worker slot tra i check
    soft_fail=False       # Fallisce il task se scade il timeout
)
```

### ExternalTaskSensor

```python
from airflow.sensors.external_task import ExternalTaskSensor

wait_for_upstream = ExternalTaskSensor(
    task_id="wait_for_crm_etl",
    external_dag_id="crm_daily_etl",
    external_task_id=None,                  # None = aspetta il DAG completo
    allowed_states=["success"],
    failed_states=["failed", "upstream_failed"],
    execution_delta=timedelta(hours=1),     # Il CRM ETL gira 1 ora prima
    mode="reschedule",
    poke_interval=300,
    timeout=7200
)
```

### HttpSensor

```python
from airflow.providers.http.sensors.http import HttpSensor

wait_for_api = HttpSensor(
    task_id="wait_for_api_ready",
    http_conn_id="external_api",
    endpoint="/health",
    response_check=lambda response: response.json().get("status") == "healthy",
    poke_interval=60,
    timeout=600,
    mode="reschedule"
)
```

### PythonSensor

```python
from airflow.sensors.python import PythonSensor

def check_data_quality(**context) -> bool:
    """Controlla che la pipeline upstream abbia caricato dati validi."""
    import psycopg2
    conn = psycopg2.connect(get_dwh_dsn())
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) > 100 AND MAX(created_at)::DATE = %s
            FROM fact_orders
        """, (context["ds"],))
        return cur.fetchone()[0]

wait_for_data = PythonSensor(
    task_id="wait_for_upstream_data",
    python_callable=check_data_quality,
    poke_interval=300,
    timeout=3600,
    mode="reschedule"
)
```

---

## Operatori Cloud

### S3 Operations

```python
from airflow.providers.amazon.aws.operators.s3 import (
    S3CopyObjectOperator,
    S3DeleteObjectsOperator,
    S3ListOperator,
)
from airflow.providers.amazon.aws.transfers.s3_to_redshift import S3ToRedshiftOperator

# Copia file in S3
archive_file = S3CopyObjectOperator(
    task_id="archive_processed_file",
    aws_conn_id="aws_default",
    source_bucket_name="data-lake-raw",
    source_bucket_key="pending/orders.csv",
    dest_bucket_name="data-lake-archive",
    dest_bucket_key="archive/{{ ds }}/orders.csv"
)

# Carica S3 → Redshift
load_to_redshift = S3ToRedshiftOperator(
    task_id="load_s3_to_redshift",
    schema="staging",
    table="stg_orders",
    s3_bucket="data-lake-processed",
    s3_key="orders/{{ ds }}/",
    aws_conn_id="aws_default",
    redshift_conn_id="redshift_dwh",
    copy_options=["FORMAT AS PARQUET", "ACCEPTINVCHARS"],
    method="REPLACE"
)
```

### GCS Operations

```python
from airflow.providers.google.cloud.operators.gcs import (
    GCSCreateBucketOperator,
    GCSDeleteObjectsOperator,
    GCSToGCSOperator,
)
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator

load_gcs_to_bq = GCSToBigQueryOperator(
    task_id="load_gcs_to_bq",
    bucket="data-lake-prod",
    source_objects=["processed/orders/{{ ds }}/*.parquet"],
    destination_project_dataset_table="my_project.staging.stg_orders",
    source_format="PARQUET",
    write_disposition="WRITE_TRUNCATE",
    create_disposition="CREATE_IF_NEEDED",
    autodetect=True,
    gcp_conn_id="google_cloud_default"
)
```

---

## Operatori Personalizzati

Quando nessun operatore esistente soddisfa il caso d'uso, si crea un operatore custom:

```python
from airflow.models.baseoperator import BaseOperator
from airflow.utils.decorators import apply_defaults
from typing import Any, Optional
import logging

class DataQualityOperator(BaseOperator):
    """
    Operatore custom per validazione qualità dati.
    Esegue un insieme di check SQL e fallisce se qualcuno fallisce.
    """

    template_fields = ("sql_checks", "run_date")  # Template Jinja applicati qui

    def __init__(
        self,
        conn_id: str,
        table: str,
        sql_checks: list,  # Lista di dict {"name": ..., "sql": ..., "expected": ...}
        run_date: str = "{{ ds }}",
        fail_on_warning: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.conn_id = conn_id
        self.table = table
        self.sql_checks = sql_checks
        self.run_date = run_date
        self.fail_on_warning = fail_on_warning

    def execute(self, context: Any) -> dict:
        from airflow.hooks.base import BaseHook
        import psycopg2

        conn_meta = BaseHook.get_connection(self.conn_id)
        pg_conn = psycopg2.connect(
            host=conn_meta.host, port=conn_meta.port,
            dbname=conn_meta.schema, user=conn_meta.login,
            password=conn_meta.password
        )

        results = []
        failures = []

        with pg_conn.cursor() as cur:
            for check in self.sql_checks:
                name = check["name"]
                sql = check["sql"].format(
                    table=self.table, run_date=self.run_date
                )
                expected = check.get("expected", True)

                cur.execute(sql)
                result = cur.fetchone()[0]
                passed = (result == expected) if expected is not True else bool(result)

                results.append({
                    "check": name,
                    "result": result,
                    "expected": expected,
                    "passed": passed
                })

                if not passed:
                    failures.append(name)
                    self.log.error(f"Check FALLITO '{name}': got {result}, expected {expected}")
                else:
                    self.log.info(f"Check OK '{name}': {result}")

        pg_conn.close()

        if failures:
            raise ValueError(
                f"Data quality checks falliti su {self.table}: {failures}"
            )

        return results


# Uso nell'operatore
validate = DataQualityOperator(
    task_id="validate_orders",
    conn_id="postgres_dwh",
    table="fact_orders",
    sql_checks=[
        {
            "name": "no_null_order_id",
            "sql": "SELECT COUNT(*) = 0 FROM {table} WHERE order_id IS NULL AND DATE(created_at) = '{run_date}'",
            "expected": True
        },
        {
            "name": "positive_amounts",
            "sql": "SELECT COUNT(*) FROM {table} WHERE amount < 0 AND DATE(created_at) = '{run_date}'",
            "expected": 0
        },
        {
            "name": "minimum_rows",
            "sql": "SELECT COUNT(*) >= 100 FROM {table} WHERE DATE(created_at) = '{run_date}'",
            "expected": True
        },
    ]
)
```

---

## Hook Personalizzati

I Hook incapsulano la logica di connessione e sono riutilizzabili da più operatori:

```python
from airflow.hooks.base import BaseHook
import requests
from typing import Optional, List, Dict

class SalesforceHook(BaseHook):
    """Hook per accedere all'API Salesforce."""

    conn_name_attr = "salesforce_conn_id"
    default_conn_name = "salesforce_default"

    def __init__(self, salesforce_conn_id: str = default_conn_name):
        super().__init__()
        self.salesforce_conn_id = salesforce_conn_id
        self._session_id: Optional[str] = None
        self._instance_url: Optional[str] = None

    def get_conn(self):
        conn = self.get_connection(self.salesforce_conn_id)
        if not self._session_id:
            self._authenticate(conn)
        return conn

    def _authenticate(self, conn):
        resp = requests.post(
            f"https://login.salesforce.com/services/oauth2/token",
            data={
                "grant_type":    "password",
                "client_id":     conn.extra_dejson.get("client_id"),
                "client_secret": conn.extra_dejson.get("client_secret"),
                "username":      conn.login,
                "password":      conn.password + conn.extra_dejson.get("security_token", ""),
            }
        )
        resp.raise_for_status()
        data = resp.json()
        self._session_id = data["access_token"]
        self._instance_url = data["instance_url"]

    def query(self, soql: str) -> List[Dict]:
        """Esegue una query SOQL e ritorna tutti i record."""
        self.get_conn()
        headers = {
            "Authorization": f"Bearer {self._session_id}",
            "Content-Type": "application/json"
        }
        url = f"{self._instance_url}/services/data/v59.0/query"
        params = {"q": soql}
        records = []

        while url:
            resp = requests.get(url, headers=headers, params=params)
            resp.raise_for_status()
            data = resp.json()
            records.extend(data.get("records", []))
            next_url = data.get("nextRecordsUrl")
            url = f"{self._instance_url}{next_url}" if next_url else None
            params = {}

        return records
```

---

## Tabella Comparativa degli Operatori

| Operatore | Provider | Use Case |
|-----------|----------|----------|
| PythonOperator | core | Logica Python custom |
| BashOperator | core | Shell scripts, dbt, spark-submit |
| PostgresOperator | postgres | SQL su PostgreSQL |
| BigQueryInsertJobOperator | google | Query/load su BigQuery |
| SnowflakeOperator | snowflake | SQL su Snowflake |
| S3KeySensor | amazon | Attesa file su S3 |
| ExternalTaskSensor | core | Dipendenza cross-DAG |
| GCSToBigQueryOperator | google | GCS → BigQuery |
| S3ToRedshiftOperator | amazon | S3 → Redshift COPY |
| HttpOperator | http | Chiamate API REST |
| SparkSubmitOperator | apache.spark | Submit job Spark |
| KubernetesPodOperator | cncf.kubernetes | Run pod K8s arbitrario |
| DockerOperator | docker | Container Docker |
| EmailOperator | core | Invio email |
