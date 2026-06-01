# Orchestrazione delle Pipeline ETL

L'orchestrazione è il sistema che pianifica, esegue, monitora e gestisce le dipendenze tra le pipeline dati. Senza un orchestratore, le pipeline diventano una collezione di cron job indipendenti impossibili da mantenere su larga scala.

## Cosa Fa un Orchestratore

- **Scheduling**: esegue pipeline a orari definiti o su trigger
- **Dependency management**: garantisce che la pipeline B parta solo dopo che la A è completata con successo
- **Retry automatico**: riprova i task falliti secondo una policy
- **Backfill**: riprocessa periodi storici
- **Parallelismo**: esegue task indipendenti in parallelo
- **Monitoring**: espone dashboard, log, alert
- **Lineage**: traccia quali dati ha prodotto quale run

---

## Apache Airflow

Airflow è lo standard de facto per l'orchestrazione di pipeline batch. Un DAG (Directed Acyclic Graph) definisce i task e le loro dipendenze.

### Struttura di un DAG

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.dates import days_ago
from datetime import datetime, timedelta

default_args = {
    "owner": "data_engineering",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=60),
    "email_on_failure": True,
    "email": ["data-team@company.com"],
    "depends_on_past": False,  # True: aspetta run precedente per stessa data
}

with DAG(
    dag_id="orders_etl",
    default_args=default_args,
    description="ETL giornaliero degli ordini",
    schedule_interval="0 2 * * *",  # 02:00 UTC ogni giorno
    start_date=days_ago(1),
    catchup=False,           # Non backfilla run mancati
    max_active_runs=1,       # Solo 1 run attivo per volta
    tags=["orders", "etl", "daily"],
) as dag:

    start = EmptyOperator(task_id="start")
    end = EmptyOperator(task_id="end")

    extract_orders = PythonOperator(
        task_id="extract_orders",
        python_callable=extract_orders_fn,
        op_kwargs={"run_date": "{{ ds }}"}  # Template date
    )

    extract_customers = PythonOperator(
        task_id="extract_customers",
        python_callable=extract_customers_fn,
        op_kwargs={"run_date": "{{ ds }}"}
    )

    transform_orders = PythonOperator(
        task_id="transform_orders",
        python_callable=transform_orders_fn
    )

    load_fact_orders = PythonOperator(
        task_id="load_fact_orders",
        python_callable=load_fact_orders_fn,
        op_kwargs={"run_id": "{{ run_id }}"}
    )

    validate_results = PythonOperator(
        task_id="validate_results",
        python_callable=validate_fn
    )

    # Definisci il grafo di dipendenze
    start >> [extract_orders, extract_customers] >> transform_orders
    transform_orders >> load_fact_orders >> validate_results >> end
```

### XCom per Passaggio di Metadati

```python
from airflow.models import TaskInstance

def extract_with_xcom(run_date: str, **context):
    """Estrae dati e passa metadati al task successivo via XCom."""
    ti: TaskInstance = context["ti"]
    
    # Esegui estrazione
    records_count = extract_orders(run_date)
    watermark = get_last_watermark("orders")

    # Pubblica metadati
    ti.xcom_push(key="records_count", value=records_count)
    ti.xcom_push(key="watermark", value=str(watermark))
    ti.xcom_push(key="run_date", value=run_date)
    
    return {"records_count": records_count, "status": "ok"}


def transform_with_xcom(**context):
    """Legge metadati dal task precedente."""
    ti: TaskInstance = context["ti"]
    
    records_count = ti.xcom_pull(task_ids="extract_orders", key="records_count")
    run_date = ti.xcom_pull(task_ids="extract_orders", key="run_date")
    
    if not records_count:
        print("Nessun record da trasformare — skip")
        return

    # Trasforma
    transform_orders(run_date, records_count)
```

### ShortCircuitOperator per Skip Condizionale

```python
from airflow.operators.python import ShortCircuitOperator

def check_data_availability(**context):
    """Ritorna False per skippare il downstream se non ci sono dati."""
    run_date = context["ds"]
    source_count = count_source_records(run_date)
    
    if source_count == 0:
        print(f"Nessun dato per {run_date} — skipping pipeline")
        return False
    
    print(f"Trovati {source_count} record per {run_date}")
    return True


check_data = ShortCircuitOperator(
    task_id="check_data_availability",
    python_callable=check_data_availability
)

check_data >> extract_orders  # Skip tutto il downstream se nessun dato
```

### BranchPythonOperator per Branching Condizionale

```python
from airflow.operators.python import BranchPythonOperator

def choose_load_strategy(**context):
    """Sceglie tra full load e incremental load."""
    run_date = context["ds"]
    is_first_run = not has_previous_successful_run("orders_etl")
    
    if is_first_run:
        return "full_load"
    else:
        return "incremental_load"


branch = BranchPythonOperator(
    task_id="choose_strategy",
    python_callable=choose_load_strategy
)

full_load = PythonOperator(task_id="full_load", python_callable=run_full_load)
incr_load = PythonOperator(task_id="incremental_load", python_callable=run_incremental)
join = EmptyOperator(task_id="join", trigger_rule="none_failed_min_one_success")

branch >> [full_load, incr_load] >> join
```

### Sensor per Attesa di Condizioni Esterne

```python
from airflow.sensors.python import PythonSensor
from airflow.sensors.filesystem import FileSensor
from airflow.providers.postgres.sensors.sql import SqlSensor

# Aspetta che un file S3 sia disponibile
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor

wait_for_source_file = S3KeySensor(
    task_id="wait_for_source_file",
    bucket_name="data-lake",
    bucket_key="raw/orders/{{ ds }}/part-*.parquet",
    wildcard_match=True,
    timeout=3600,     # Timeout dopo 1 ora
    poke_interval=60, # Controlla ogni minuto
    mode="reschedule" # Libera il worker slot tra i check
)

# Aspetta che una query SQL restituisca True
wait_for_upstream = SqlSensor(
    task_id="wait_for_upstream_pipeline",
    conn_id="postgres_dwh",
    sql="""
        SELECT COUNT(*) > 0
        FROM etl_run_log
        WHERE table_name = 'stg_orders'
          AND status = 'success'
          AND DATE(started_at) = '{{ ds }}'
    """,
    poke_interval=300,
    timeout=7200
)

# Sensor personalizzato
def check_api_available():
    import requests
    try:
        resp = requests.get("https://api.example.com/health", timeout=5)
        return resp.status_code == 200
    except Exception:
        return False

wait_for_api = PythonSensor(
    task_id="wait_for_api",
    python_callable=check_api_available,
    poke_interval=60,
    timeout=1800,
    mode="reschedule"
)
```

---

## Prefect

Prefect è un orchestratore moderno con API più pythonica rispetto ad Airflow:

```python
from prefect import flow, task
from prefect.tasks import task_input_hash
from datetime import timedelta
from typing import List

@task(
    retries=3,
    retry_delay_seconds=30,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1)
)
def extract_orders(run_date: str) -> List[dict]:
    """Task di estrazione con cache e retry."""
    extractor = PostgreSQLExtractor(dsn="postgresql://prod/db")
    records = []
    for batch in extractor.extract_table("orders", where_clause="DATE(created_at) = %s",
                                          params=(run_date,)):
        records.extend(batch)
    return records


@task(retries=2)
def transform_records(records: List[dict]) -> dict:
    """Task di trasformazione."""
    pipeline = build_transformation_pipeline()
    valid, errors = pipeline.execute(records)
    return {"valid": valid, "error_count": len(errors)}


@task
def load_to_warehouse(valid_records: List[dict], run_date: str) -> int:
    """Task di loading."""
    conn = psycopg2.connect("postgresql://dwh/warehouse")
    result = upsert(conn, "fact_orders", valid_records, ["order_id"])
    return len(valid_records)


@flow(
    name="orders-etl",
    description="ETL giornaliero degli ordini",
    retries=0  # Retry a livello di task, non di flow
)
def orders_etl_flow(run_date: str = None):
    """Flow principale per l'ETL degli ordini."""
    from datetime import date
    run_date = run_date or date.today().isoformat()

    # Estrazione parallela
    orders_future = extract_orders.submit(run_date)
    # Altri task paralleli...

    # Aspetta e trasforma
    orders = orders_future.result()
    result = transform_records(orders)

    # Load
    rows = load_to_warehouse(result["valid"], run_date)
    return {"run_date": run_date, "rows_loaded": rows}


# Scheduling con Prefect Deployments
if __name__ == "__main__":
    from prefect.deployments import Deployment
    from prefect.server.schemas.schedules import CronSchedule

    deployment = Deployment.build_from_flow(
        flow=orders_etl_flow,
        name="daily-orders-etl",
        schedule=CronSchedule(cron="0 2 * * *", timezone="UTC"),
        work_queue_name="data-engineering"
    )
    deployment.apply()
```

---

## Dagster

Dagster introduce il concetto di "asset-based orchestration" — invece di schedulare job, definisce gli asset dati che vuole mantenere aggiornati:

```python
from dagster import (
    asset, AssetIn, Output, MetadataValue,
    define_asset_job, ScheduleDefinition, Definitions
)
import pandas as pd

@asset(
    description="Ordini grezzi estratti dal DB operativo",
    compute_kind="python",
    group_name="raw"
)
def raw_orders(context) -> pd.DataFrame:
    """Asset: ordini raw dal database operativo."""
    run_date = context.partition_key  # Se partizionato per data
    extractor = PostgreSQLExtractor(dsn="postgresql://prod/db")
    records = []
    for batch in extractor.extract_table("orders"):
        records.extend(batch)
    
    df = pd.DataFrame(records)
    context.add_output_metadata({
        "rows": MetadataValue.int(len(df)),
        "columns": MetadataValue.text(str(list(df.columns)))
    })
    return df


@asset(
    ins={"raw_orders": AssetIn()},
    description="Ordini puliti e normalizzati",
    group_name="staging"
)
def stg_orders(raw_orders: pd.DataFrame) -> pd.DataFrame:
    """Asset: ordini staging con trasformazioni applicate."""
    df = raw_orders.copy()
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["customer_email"] = df["customer_email"].str.strip().str.lower()
    df = df.dropna(subset=["order_id", "customer_id", "amount"])
    return df


@asset(
    ins={"stg_orders": AssetIn()},
    description="Fatto ordini nel data warehouse",
    group_name="warehouse"
)
def fact_orders(context, stg_orders: pd.DataFrame) -> Output:
    """Asset: fact table ordini nel DWH."""
    conn = psycopg2.connect("postgresql://dwh/warehouse")
    rows = upsert_dataframe(conn, "fact_orders", stg_orders, ["order_id"])
    return Output(
        value=rows,
        metadata={"rows_upserted": MetadataValue.int(rows)}
    )


# Definizione job e schedule
orders_job = define_asset_job(
    name="orders_refresh",
    selection=["raw_orders", "stg_orders", "fact_orders"]
)

daily_orders_schedule = ScheduleDefinition(
    job=orders_job,
    cron_schedule="0 2 * * *",
    execution_timezone="UTC"
)

defs = Definitions(
    assets=[raw_orders, stg_orders, fact_orders],
    jobs=[orders_job],
    schedules=[daily_orders_schedule]
)
```

---

## Orchestrazione con Python Puro

Per pipeline semplici senza bisogno di un orchestratore completo, una classe di scheduling minimale è sufficiente:

```python
import schedule
import time
import threading
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SimpleOrchestrator:
    """Orchestratore minimalista per pipeline piccole."""

    def __init__(self):
        self._jobs = []
        self._running = False
        self._thread = None

    def add_daily(self, func, at_time: str, **kwargs):
        """Aggiunge un job giornaliero (es: at_time='02:00')."""
        def job():
            try:
                logger.info(f"Avvio {func.__name__} alle {datetime.utcnow().isoformat()}")
                result = func(**kwargs)
                logger.info(f"Completato {func.__name__}: {result}")
            except Exception as e:
                logger.error(f"Fallito {func.__name__}: {e}", exc_info=True)

        schedule.every().day.at(at_time).do(job)
        self._jobs.append(func.__name__)
        return self

    def add_hourly(self, func, **kwargs):
        def job():
            try:
                func(**kwargs)
            except Exception as e:
                logger.error(f"Fallito {func.__name__}: {e}", exc_info=True)
        schedule.every().hour.do(job)
        return self

    def start(self, background: bool = True):
        self._running = True
        if background:
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
        else:
            self._run_loop()

    def stop(self):
        self._running = False

    def _run_loop(self):
        while self._running:
            schedule.run_pending()
            time.sleep(30)


# Uso
orchestrator = SimpleOrchestrator()
orchestrator.add_daily(run_orders_pipeline, at_time="02:00")
orchestrator.add_daily(run_customers_pipeline, at_time="02:30")
orchestrator.add_hourly(run_realtime_events_pipeline)
orchestrator.start(background=True)
```

---

## Pattern di Dipendenza tra Pipeline

### Trigger Basato su File

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os

class NewFileHandler(FileSystemEventHandler):
    """Triggera pipeline quando appare un nuovo file nella cartella."""

    def __init__(self, pipeline_fn, file_pattern: str = "*.parquet"):
        import fnmatch
        self.pipeline_fn = pipeline_fn
        self.file_pattern = file_pattern

    def on_created(self, event):
        if not event.is_directory:
            filename = os.path.basename(event.src_path)
            import fnmatch
            if fnmatch.fnmatch(filename, self.file_pattern):
                logger.info(f"Nuovo file rilevato: {event.src_path}")
                try:
                    self.pipeline_fn(filepath=event.src_path)
                except Exception as e:
                    logger.error(f"Pipeline fallita per {event.src_path}: {e}")


def start_file_watcher(watch_dir: str, pipeline_fn):
    handler = NewFileHandler(pipeline_fn)
    observer = Observer()
    observer.schedule(handler, watch_dir, recursive=False)
    observer.start()
    return observer
```

### Trigger Basato su Completion Table

```python
def wait_for_upstream(
    conn,
    upstream_pipeline: str,
    run_date: str,
    timeout_sec: int = 3600,
    poll_interval_sec: int = 60
) -> bool:
    """Aspetta che la pipeline upstream completi prima di procedere."""
    import time
    deadline = time.monotonic() + timeout_sec

    while time.monotonic() < deadline:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT status FROM etl_run_log
                WHERE pipeline_name = %s
                  AND DATE(started_at) = %s
                ORDER BY started_at DESC
                LIMIT 1
            """, (upstream_pipeline, run_date))
            row = cur.fetchone()

        if row:
            status = row[0]
            if status == "success":
                return True
            elif status == "failed":
                raise RuntimeError(f"Upstream '{upstream_pipeline}' fallita per {run_date}")

        remaining = deadline - time.monotonic()
        logger.info(f"Aspetto '{upstream_pipeline}' per {run_date}... ({remaining:.0f}s rimanenti)")
        time.sleep(poll_interval_sec)

    raise TimeoutError(f"Timeout attesa '{upstream_pipeline}' per {run_date}")
```

---

## Confronto Orchestratori

| Feature | Airflow | Prefect | Dagster |
|---------|---------|---------|---------|
| Paradigma | Task-based DAG | Flow + Task | Asset-based |
| Setup | Pesante (metadb+scheduler+worker) | Leggero (cloud o self-hosted) | Medio |
| UI | Matura, ricca | Moderna | Asset-centric |
| Scheduling | Cron nativo | Deployment | Schedule |
| Testing | Difficile | Facile (test diretti) | Buono |
| Lineage | Plugin | Limitato | Nativo (asset graph) |
| Dynamic tasks | Limitato (2.x+) | Nativo | Nativo |
| Community | Molto grande | Media | Crescente |
| Use case | Enterprise, batch | Pipelines moderne | Data platform |

---

## Best Practice

**Dimensiona i DAG/Flow per singola responsabilità** — un DAG per tipo di entità (ordini, clienti, prodotti), non un mega-DAG per tutto.

**Usa `catchup=False` in Airflow** a meno che non sia necessario il backfill automatico — il backfill automatico può sovraccaricare il sistema e le sorgenti.

**Non mettere logica di business nei DAG** — il DAG/Flow è solo la definizione del grafo e dei parametri. La logica sta nei moduli Python importati.

**Versiona i DAG** con git tag o branch per permettere rollback della logica di orchestrazione.

**Monitora la durata media dei task** — un task che impiega 3x più del solito è il primo segnale di problema ai dati o alle risorse.

**Testa i DAG localmente** prima del deploy — Airflow ha `dag.test()`, Prefect permette l'esecuzione diretta delle funzioni, Dagster ha `materialize`.
