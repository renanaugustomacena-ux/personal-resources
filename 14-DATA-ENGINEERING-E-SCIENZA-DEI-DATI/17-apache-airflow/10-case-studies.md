# Case Study Apache Airflow

Scenari reali di implementazione di pipeline Airflow in ambienti di produzione. Ogni caso presenta il problema, la soluzione architetturale e le lezioni apprese.

---

## Case Study 1: Pipeline Dati E-Commerce Multi-Sorgente

### Contesto

Una piattaforma e-commerce ha dati distribuiti in 6 sorgenti diverse: database ordini (PostgreSQL), CRM (Salesforce), pagamenti (Stripe), analytics eventi (BigQuery), magazzino (MySQL), ERP (Oracle). Ogni sorgente deve alimentare un Snowflake DWH con frequenze diverse.

### Soluzione con DAG Factory + ExternalTaskSensor

```python
# dags/factory.py
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
from datetime import datetime, timedelta
from pipelines.loaders import GenericLoader
from plugins.operators.data_quality import DataQualityOperator

SOURCE_CONFIGS = [
    {
        "name": "orders_postgres",
        "conn_id": "postgres_orders",
        "table": "orders",
        "schedule": "0 * * * *",      # Ogni ora
        "target_table": "STG_ORDERS",
        "key_column": "order_id",
        "timestamp_col": "updated_at",
        "quality_checks": [
            {"name": "no_null_ids", "sql": "SELECT COUNT(*) = 0 FROM {table} WHERE order_id IS NULL"},
            {"name": "positive_amounts", "sql": "SELECT COUNT(*) = 0 FROM {table} WHERE amount < 0"},
        ]
    },
    {
        "name": "crm_salesforce",
        "conn_id": "salesforce_prod",
        "table": "Contact",
        "schedule": "0 4 * * *",     # Ogni giorno alle 04:00
        "target_table": "STG_CRM_CONTACTS",
        "key_column": "Id",
        "timestamp_col": "LastModifiedDate",
        "quality_checks": [
            {"name": "email_not_null", "sql": "SELECT COUNT(*) = 0 FROM {table} WHERE email IS NULL"},
        ]
    },
    {
        "name": "payments_stripe",
        "conn_id": "stripe_api",
        "table": "charges",
        "schedule": "*/30 * * * *",  # Ogni 30 minuti
        "target_table": "STG_PAYMENTS",
        "key_column": "id",
        "timestamp_col": "created",
        "quality_checks": []
    },
]


def create_source_dag(config: dict) -> DAG:
    """Factory che genera un DAG per ogni sorgente."""
    
    with DAG(
        dag_id=f"ingest_{config['name']}",
        schedule_interval=config["schedule"],
        start_date=datetime(2024, 1, 1),
        catchup=False,
        max_active_runs=1,
        default_args={
            "retries": 3,
            "retry_delay": timedelta(minutes=5),
            "on_failure_callback": slack_failure_callback,
        },
        tags=["ingestion", config["name"]]
    ) as dag:

        extract = PythonOperator(
            task_id="extract",
            python_callable=generic_extract,
            op_kwargs=config
        )

        load = PythonOperator(
            task_id="load",
            python_callable=GenericLoader(config["conn_id"]).load,
            op_kwargs={
                "target_table": config["target_table"],
                "key_column": config["key_column"],
                "run_id": "{{ run_id }}"
            }
        )

        if config.get("quality_checks"):
            validate = DataQualityOperator(
                task_id="validate",
                conn_id="snowflake_dwh",
                table=config["target_table"],
                sql_checks=config["quality_checks"]
            )
            extract >> load >> validate
        else:
            extract >> load

    return dag


# Genera e registra tutti i DAG
for source_config in SOURCE_CONFIGS:
    dag = create_source_dag(source_config)
    globals()[dag.dag_id] = dag


# DAG di aggregazione che dipende da tutti i source DAG
with DAG(
    dag_id="build_data_marts",
    schedule_interval="0 6 * * *",  # 06:00 quando tutti i source DAG orari sono finiti
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["marts", "downstream"]
) as marts_dag:

    # Aspetta ogni source DAG giornaliero
    wait_for_orders = ExternalTaskSensor(
        task_id="wait_orders",
        external_dag_id="ingest_orders_postgres",
        execution_delta=timedelta(hours=1),
        mode="reschedule", timeout=7200
    )

    wait_for_crm = ExternalTaskSensor(
        task_id="wait_crm",
        external_dag_id="ingest_crm_salesforce",
        execution_delta=timedelta(hours=2),
        mode="reschedule", timeout=7200
    )

    build_revenue = PythonOperator(
        task_id="build_revenue_mart",
        python_callable=build_revenue_mart,
        op_kwargs={"run_date": "{{ ds }}"}
    )

    build_customer = PythonOperator(
        task_id="build_customer_mart",
        python_callable=build_customer_mart
    )

    [wait_for_orders, wait_for_crm] >> [build_revenue, build_customer]
```

### Risultati

- 6 DAG generati automaticamente dalla factory: aggiungere una nuova sorgente richiede aggiungere un dict nella lista
- Il DAG di aggregazione garantisce che tutti i dati siano freschi prima di costruire i mart
- Tasso di errore sceso dal 15% (pipeline manuale) al 2% dopo l'introduzione dei quality checks automatici

---

## Case Study 2: Backfill di 3 Anni di Dati Storici

### Contesto

Un cambio di logica di calcolo delle commissioni richiede il ricalcolo di tutti gli ordini degli ultimi 3 anni (36 milioni di record). La pipeline deve completare entro 8 ore per rispettare la finestra di manutenzione.

### Soluzione con Parallelismo Controllato

```python
from airflow.decorators import dag, task
from airflow.models.param import Param
from datetime import datetime, date, timedelta
import concurrent.futures

@dag(
    dag_id="historical_backfill",
    schedule_interval=None,  # Solo trigger manuale
    start_date=datetime(2024, 1, 1),
    catchup=False,
    params={
        "start_date":   Param("2021-01-01", type="string"),
        "end_date":     Param("2023-12-31", type="string"),
        "batch_months": Param(3, type="integer"),    # Processa N mesi alla volta
        "parallelism":  Param(4, type="integer"),    # Worker paralleli
    }
)
def historical_backfill():

    @task
    def plan_batches(start_date: str, end_date: str, batch_months: int) -> list:
        """Pianifica i batch da processare."""
        from dateutil.relativedelta import relativedelta
        
        batches = []
        current = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        
        while current <= end:
            batch_end = min(
                current + relativedelta(months=batch_months) - timedelta(days=1),
                end
            )
            batches.append({
                "batch_id": f"{current.isoformat()}_{batch_end.isoformat()}",
                "start": current.isoformat(),
                "end": batch_end.isoformat()
            })
            current = batch_end + timedelta(days=1)
        
        print(f"Pianificati {len(batches)} batch")
        return batches

    @task
    def process_batch(batch: dict) -> dict:
        """Processa un singolo batch mensile."""
        start = batch["start"]
        end = batch["end"]
        batch_id = batch["batch_id"]
        
        print(f"Processo batch {batch_id}: {start} → {end}")
        
        conn = get_source_conn()
        dwh = get_dwh_conn()
        
        # Estrai
        records = extract_orders_for_range(conn, start, end)
        print(f"Estratti {len(records)} ordini")
        
        # Ricaola commissioni con nuova logica
        enriched = [recalculate_commission(r) for r in records]
        
        # Carica con upsert idempotente
        rows = upsert_orders(dwh, enriched, key=["order_id"])
        
        return {"batch_id": batch_id, "records": len(records), "rows_updated": rows}

    @task
    def summarize_results(results: list) -> None:
        """Aggrega risultati e verifica completezza."""
        total_records = sum(r["records"] for r in results)
        total_updated = sum(r["rows_updated"] for r in results)
        failed = [r for r in results if r.get("status") == "failed"]
        
        print(f"Backfill completato:")
        print(f"  Record processati: {total_records:,}")
        print(f"  Righe aggiornate:  {total_updated:,}")
        print(f"  Batch falliti:     {len(failed)}")
        
        if failed:
            raise ValueError(f"Batch falliti: {[r['batch_id'] for r in failed]}")

    batches = plan_batches(
        start_date="{{ params.start_date }}",
        end_date="{{ params.end_date }}",
        batch_months="{{ params.batch_months }}"
    )
    results = process_batch.expand(batch=batches)  # Dynamic mapping!
    summarize_results(results)


dag = historical_backfill()
```

### Risultati

- 12 batch da 3 mesi ciascuno, 4 in parallelo → 3 round di esecuzione
- Completato in 4.5 ore (vs 8h budget)
- Zero rollback necessari grazie all'upsert idempotente

---

## Case Study 3: Pipeline CDC Real-Time con Debezium + Airflow

### Contesto

Il team vuole un sistema che replichi ogni modifica al database ordini in un data lake S3 entro 5 minuti. Debezium cattura i cambiamenti; Airflow orchestra il micro-batching.

```python
# dags/cdc_micro_batch.py
from airflow.decorators import dag, task
from datetime import datetime, timedelta
from confluent_kafka import Consumer

@dag(
    dag_id="cdc_orders_micro_batch",
    schedule_interval=timedelta(minutes=5),  # Ogni 5 minuti
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,       # Serializza i run
    tags=["cdc", "realtime"]
)
def cdc_micro_batch():

    @task(retries=3, retry_delay=timedelta(seconds=30))
    def consume_kafka_events(max_messages: int = 10_000) -> dict:
        """Consuma eventi CDC da Kafka per i prossimi 5 minuti."""
        from airflow.models import Variable
        
        consumer = Consumer({
            "bootstrap.servers": Variable.get("kafka_bootstrap_servers"),
            "group.id": "airflow_cdc_orders",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        })
        consumer.subscribe(["prod.public.orders"])

        events = []
        deadline = datetime.utcnow() + timedelta(minutes=4, seconds=30)

        while datetime.utcnow() < deadline and len(events) < max_messages:
            msg = consumer.poll(timeout=1.0)
            if msg and not msg.error():
                import json
                events.append(json.loads(msg.value()))

        consumer.commit(asynchronous=False)
        consumer.close()
        return {"count": len(events), "events": events}

    @task
    def write_to_s3(consumed: dict) -> str:
        """Scrive gli eventi in S3 come Parquet."""
        import boto3, pyarrow as pa, pyarrow.parquet as pq, io
        from datetime import datetime

        events = consumed["events"]
        if not events:
            return "no_events"

        table = pa.Table.from_pylist(events)
        buf = io.BytesIO()
        pq.write_table(table, buf, compression="snappy")
        buf.seek(0)

        now = datetime.utcnow()
        key = f"raw/cdc/orders/{now.year}/{now.month:02d}/{now.day:02d}/{now.strftime('%H%M%S')}.parquet"

        s3 = boto3.client("s3")
        s3.put_object(Bucket="data-lake-prod", Key=key, Body=buf.getvalue())
        return f"s3://data-lake-prod/{key}"

    @task(trigger_rule="none_failed")
    def trigger_downstream_refresh(s3_path: str) -> None:
        """Triggera refresh del layer staging se ci sono nuovi eventi."""
        if s3_path == "no_events":
            print("Nessun evento, skip refresh")
            return
        
        # Trigger DAG downstream via API REST
        import requests
        requests.post(
            "http://airflow-webserver:8080/api/v1/dags/stg_orders_refresh/dagRuns",
            json={"conf": {"source_path": s3_path}},
            auth=("admin", get_admin_password())
        )

    events = consume_kafka_events()
    path = write_to_s3(events)
    trigger_downstream_refresh(path)


dag = cdc_micro_batch()
```

### Lezioni Apprese

**`max_active_runs=1` è essenziale** — senza questa impostazione, se un run da 5 minuti impiega 6 minuti, il successivo parte mentre il primo è ancora in esecuzione e i due Consumer Kafka interferiscono.

**Kafka consumer group isolation** — usa un group_id dedicato per Airflow separato dai consumer applicativi. Un commit errato non deve impattare gli altri consumer.

**Il timeout di 4:30 sui 5 minuti** lascia 30 secondi per il commit e la chiusura del consumer. Se il poll impiegasse tutti i 5 minuti, i successivi step fallirebbero per timeout.

---

## Lezioni Apprese Generali

**La DAG factory è potente ma richiede disciplina** — aggiungere una sorgente diventa banale, ma un bug nella factory rompe tutti i DAG generati simultaneamente. Test unitari sulla factory sono obbligatori.

**ExternalTaskSensor mal configurato è fonte di deadlock** — `execution_delta` deve essere calcolato con cura. Se il producer gira alle 02:00 e il consumer si aspetta dati delle ore 00:00 del giorno prima, `execution_delta=timedelta(hours=2)` è corretto. Sbagliare questo parametro manda il sensor in loop infinito.

**Il backfill con dynamic mapping è molto più elegante** rispetto al for loop che genera task staticamente. Ma richiede Airflow 2.3+ e la funzione `expand()` che crea task a runtime.

**Non usare Airflow per micro-batching < 1 minuto** — l'overhead del scheduling (creazione DagRun, query al metadb, routing al worker) è di circa 10-30 secondi. Sotto il minuto, considera Kafka Streams, Flink, o un consumer loop Python che gira continuativamente.
