# DAG in Apache Airflow

I DAG (Directed Acyclic Graph) sono il cuore di Airflow: ogni pipeline viene definita come un grafo Python in cui i nodi sono task e gli archi rappresentano le dipendenze di esecuzione.

## Struttura di un DAG Completo

```python
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator, ShortCircuitOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


# ── Helper functions (importate da moduli separati in produzione) ──

def check_source_available(**context) -> bool:
    """Ritorna False se la sorgente non ha dati → skip pipeline."""
    run_date = context["ds"]
    count = count_source_records_for_date(run_date)
    if count == 0:
        logger.info(f"Nessun dato per {run_date} — skip")
        return False
    context["ti"].xcom_push("source_count", count)
    return True


def choose_strategy(**context) -> str:
    """Branch: full o incremental."""
    if not has_prior_successful_run():
        return "full_extract"
    return "incremental_extract"


def full_extract(**context):
    records = extract_all_records()
    context["ti"].xcom_push("records", records)


def incremental_extract(**context):
    run_date = context["ds"]
    records = extract_records_for_date(run_date)
    context["ti"].xcom_push("records", records)


def transform_records(**context):
    ti = context["ti"]
    # Pull da qualsiasi branch abbia girato
    records = ti.xcom_pull(task_ids=["full_extract", "incremental_extract"])
    # xcom_pull con task_ids lista ritorna lista di valori — prendi il non-None
    records = next((r for r in records if r is not None), [])
    validated, errors = validate_and_transform(records)
    ti.xcom_push("valid_records", validated)
    ti.xcom_push("error_count", len(errors))
    return len(validated)


def load_to_dwh(**context):
    ti = context["ti"]
    records = ti.xcom_pull(task_ids="transform", key="valid_records")
    run_id = context["run_id"]
    rows = upsert_records(records, run_id=run_id)
    ti.xcom_push("rows_loaded", rows)
    return rows


def post_load_validation(**context):
    ti = context["ti"]
    rows_loaded = ti.xcom_pull(task_ids="load", key="rows_loaded")
    source_count = ti.xcom_pull(task_ids="check_source", key="source_count")

    if source_count and rows_loaded < source_count * 0.95:
        raise ValueError(
            f"Validazione fallita: {rows_loaded} caricati vs {source_count} attesi"
        )


def notify_completion(**context):
    rows = context["ti"].xcom_pull(task_ids="load", key="rows_loaded")
    send_slack_message(f"Pipeline completata: {rows} righe caricate.")


# ── Definizione DAG ──

with DAG(
    dag_id="orders_full_pipeline",
    default_args={
        "owner":                    "data_engineering",
        "retries":                  3,
        "retry_delay":              timedelta(minutes=5),
        "retry_exponential_backoff": True,
        "max_retry_delay":          timedelta(minutes=30),
        "email_on_failure":         True,
        "email":                    ["data-team@company.com"],
    },
    schedule_interval="0 2 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["orders", "daily"],
) as dag:

    # ── Nodi start/end ──
    start   = EmptyOperator(task_id="start")
    success = EmptyOperator(task_id="pipeline_success",
                            trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)
    notify  = PythonOperator(task_id="notify", python_callable=notify_completion)

    # ── Check disponibilità dati ──
    check_source = ShortCircuitOperator(
        task_id="check_source",
        python_callable=check_source_available,
        ignore_downstream_trigger_rules=False
    )

    # ── Branch: full vs incremental ──
    branch = BranchPythonOperator(
        task_id="choose_strategy",
        python_callable=choose_strategy
    )
    full_task  = PythonOperator(task_id="full_extract",  python_callable=full_extract)
    incr_task  = PythonOperator(task_id="incremental_extract", python_callable=incremental_extract)
    join_branch = EmptyOperator(task_id="join_branch",
                                trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS)

    # ── Transform e Load ──
    transform = PythonOperator(task_id="transform",  python_callable=transform_records)
    load      = PythonOperator(task_id="load",       python_callable=load_to_dwh)
    validate  = PythonOperator(task_id="post_validate", python_callable=post_load_validation)

    # ── Grafo ──
    start >> check_source >> branch
    branch >> [full_task, incr_task] >> join_branch
    join_branch >> transform >> load >> validate >> [success, notify]
```

---

## Dynamic Task Mapping (Airflow 2.3+)

Genera task dinamicamente in base ai dati di runtime:

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(schedule_interval="@daily", start_date=datetime(2024, 1, 1), catchup=False)
def dynamic_etl():

    @task
    def get_sources() -> list:
        """Restituisce lista di sorgenti da processare."""
        return [
            {"source": "orders_eu", "schema": "eu_orders"},
            {"source": "orders_us", "schema": "us_orders"},
            {"source": "orders_apac", "schema": "apac_orders"},
        ]

    @task
    def process_source(source_config: dict) -> dict:
        """Processa una singola sorgente — istanziato per ogni elemento."""
        source = source_config["source"]
        schema = source_config["schema"]
        records = extract_from_schema(schema)
        rows = load_to_dwh(records, target=f"fact_{source}")
        return {"source": source, "rows": rows}

    @task
    def aggregate_results(results: list) -> None:
        """Riceve la lista di tutti i risultati."""
        total = sum(r["rows"] for r in results)
        print(f"Totale righe caricate: {total}")
        for r in results:
            print(f"  {r['source']}: {r['rows']}")

    # expand() crea un task per ogni elemento della lista
    sources = get_sources()
    results = process_source.expand(source_config=sources)
    aggregate_results(results)


dag = dynamic_etl()
```

---

## DAG con Dipendenze Cross-DAG

```python
from airflow.sensors.external_task import ExternalTaskSensor

# DAG B aspetta che il DAG A abbia completato con successo
wait_for_upstream = ExternalTaskSensor(
    task_id="wait_for_orders_etl",
    external_dag_id="orders_daily_etl",
    external_task_id=None,      # None = aspetta il DAG completo
    allowed_states=["success"],
    failed_states=["failed", "skipped"],
    execution_delta=timedelta(0),   # Stessa data logica
    mode="reschedule",              # Libera worker tra i check
    poke_interval=300,              # Controlla ogni 5 minuti
    timeout=7200,                   # Timeout dopo 2 ore
)
```

---

## Parametrizzazione con DAG Runs

```python
from airflow.models.param import Param

with DAG(
    dag_id="parameterized_etl",
    params={
        "run_date": Param(
            default="",
            type="string",
            description="Data da processare (YYYY-MM-DD). Lascia vuoto per usare oggi.",
        ),
        "batch_size": Param(
            default=50_000,
            type="integer",
            minimum=1000,
            maximum=500_000,
            description="Numero di record per batch"
        ),
        "dry_run": Param(
            default=False,
            type="boolean",
            description="Se True, non scrive nel DWH"
        ),
    },
    schedule_interval=None,  # Solo trigger manuale
    ...
) as dag:

    run = PythonOperator(
        task_id="run_pipeline",
        python_callable=execute_pipeline,
        op_kwargs={
            "run_date": "{{ params.run_date or ds }}",
            "batch_size": "{{ params.batch_size }}",
            "dry_run": "{{ params.dry_run }}"
        }
    )
```

---

## SubDAG e TaskGroup

I TaskGroup organizzano visivamente i task nella UI senza creare complessità:

```python
from airflow.utils.task_group import TaskGroup

with DAG(...) as dag:
    with TaskGroup("extraction", tooltip="Task di estrazione") as extraction_group:
        extract_orders   = PythonOperator(task_id="orders",   ...)
        extract_customers = PythonOperator(task_id="customers", ...)
        extract_products  = PythonOperator(task_id="products",  ...)
        # All'interno del gruppo i task girano in parallelo per default

    with TaskGroup("transformation") as transform_group:
        transform_orders    = PythonOperator(task_id="orders",    ...)
        transform_customers = PythonOperator(task_id="customers", ...)

    with TaskGroup("loading") as load_group:
        load_dims = PythonOperator(task_id="dimensions", ...)
        load_facts = PythonOperator(task_id="facts", ...)
        load_dims >> load_facts

    extraction_group >> transform_group >> load_group
```

---

## Dataset-Driven Scheduling (Airflow 2.4+)

Airflow 2.4 introduce lo scheduling basato su dataset — un DAG parte quando un altro DAG produce un determinato dataset:

```python
from airflow import Dataset

# Dataset A: rappresenta la tabella ordini aggiornata
orders_dataset = Dataset("postgres://dwh/fact_orders")
customers_dataset = Dataset("postgres://dwh/dim_customer")

# DAG che produce il dataset
with DAG(
    dag_id="orders_etl",
    schedule_interval="@daily",
    ...
) as dag_producer:
    load_orders = PythonOperator(
        task_id="load",
        python_callable=load_fn,
        outlets=[orders_dataset]  # Dichiara cosa produce
    )

# DAG che dipende dal dataset — parte automaticamente quando orders_dataset è aggiornato
with DAG(
    dag_id="revenue_report",
    schedule=[orders_dataset, customers_dataset],  # Aspetta entrambi
    ...
) as dag_consumer:
    run_report = PythonOperator(task_id="run", python_callable=generate_report_fn)
```

---

## Testing dei DAG

```python
# test_orders_dag.py
import pytest
from airflow.models import DagBag

def test_dag_loads_without_errors():
    dagbag = DagBag(dag_folder="dags/", include_examples=False)
    assert "orders_daily_etl" in dagbag.dags
    assert len(dagbag.import_errors) == 0, f"Import errors: {dagbag.import_errors}"


def test_dag_structure():
    dagbag = DagBag(dag_folder="dags/", include_examples=False)
    dag = dagbag.dags["orders_daily_etl"]

    # Verifica task presenti
    task_ids = {task.task_id for task in dag.tasks}
    expected = {"start", "check_source", "extract", "transform", "load", "validate"}
    assert expected.issubset(task_ids)

    # Verifica topologia
    transform_task = dag.get_task("transform")
    assert "extract" in {t.task_id for t in transform_task.upstream_list}


def test_dag_has_no_cycles():
    dagbag = DagBag(dag_folder="dags/", include_examples=False)
    dag = dagbag.dags["orders_daily_etl"]
    # DAG invalido se ha cicli — Airflow lancia già errore, questo è un test esplicito
    assert dag.test_cycle() is False


@pytest.mark.integration
def test_dag_run_local():
    """Test E2E: esegue il DAG su un DB di test (lento, solo in CI)."""
    from airflow.models import DagRun
    from airflow.utils.state import DagRunState

    dagbag = DagBag(dag_folder="dags/", include_examples=False)
    dag = dagbag.dags["orders_daily_etl"]
    dag.test(run_conf={"dry_run": True})
```

---

## DAG Factories

Quando si hanno molte pipeline simili (es. 20 sorgenti diverse con lo stesso processo ETL), le DAG factory evitano la duplicazione:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

def create_source_etl_dag(
    source_name: str,
    source_schema: str,
    schedule: str,
    target_table: str,
) -> DAG:
    """Factory: crea un DAG ETL parametrizzato per una sorgente."""

    dag = DAG(
        dag_id=f"etl_{source_name}",
        schedule_interval=schedule,
        start_date=datetime(2024, 1, 1),
        catchup=False,
        default_args={
            "retries": 3,
            "retry_delay": timedelta(minutes=5),
        },
        tags=["auto_generated", source_name]
    )

    with dag:
        extract = PythonOperator(
            task_id="extract",
            python_callable=generic_extract,
            op_kwargs={"schema": source_schema}
        )
        transform = PythonOperator(
            task_id="transform",
            python_callable=generic_transform
        )
        load = PythonOperator(
            task_id="load",
            python_callable=generic_load,
            op_kwargs={"target_table": target_table}
        )
        extract >> transform >> load

    return dag


# Genera DAG per tutte le sorgenti configurate
SOURCES = [
    {"name": "crm",     "schema": "salesforce", "schedule": "0 3 * * *", "table": "dim_crm_contact"},
    {"name": "billing", "schema": "stripe",     "schedule": "0 4 * * *", "table": "fact_payments"},
    {"name": "support", "schema": "zendesk",    "schedule": "0 5 * * *", "table": "fact_tickets"},
]

for source in SOURCES:
    # Registra nel namespace globale — Airflow scopre i DAG via `globals()`
    globals()[f"dag_{source['name']}"] = create_source_etl_dag(
        source_name=source["name"],
        source_schema=source["schema"],
        schedule=source["schedule"],
        target_table=source["table"]
    )
```

---

## Anti-Pattern da Evitare

```python
# ❌ Top-level code che accede a DB o rete al momento del parse
# (il DAG viene parsato ogni 30s dallo scheduler — non fare I/O qui)
conn = psycopg2.connect(...)  # SBAGLIATO: connessione al parse time
tables = conn.execute("SELECT ...").fetchall()  # SBAGLIATO

# ✅ Accesso a risorse solo dentro i task
def my_task(**context):
    conn = psycopg2.connect(...)  # OK: solo a runtime
    ...

# ❌ Passare grandi quantità di dati via XCom
def extract(**context):
    records = fetch_10_million_records()
    context["ti"].xcom_push("data", records)  # XCom è per metadata, non dati!

# ✅ Usa file system o storage intermedio per dati grandi
def extract(**context):
    records = fetch_10_million_records()
    path = f"/tmp/extract_{context['run_id']}.parquet"
    save_to_parquet(records, path)
    context["ti"].xcom_push("data_path", path)  # Solo il percorso

# ❌ Variabili globali mutabili (non thread-safe)
global_state = {}
def task_a(**context):
    global_state["result"] = compute()  # Race condition!

# ✅ XCom o storage esterno per condivisione stato
```
