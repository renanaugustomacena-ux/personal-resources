# Apache Airflow

Apache Airflow è la piattaforma di orchestrazione di workflow più diffusa nell'ecosistema data engineering. Permette di definire pipeline come codice Python (DAGs), schedularle, monitorarle e gestirne le dipendenze con un'interfaccia web completa.

## Architettura di Airflow

```
┌──────────────────────────────────────────────────────────────┐
│                    AIRFLOW CLUSTER                           │
│                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────┐  │
│  │  Webserver   │   │  Scheduler   │   │    Workers     │  │
│  │  (Flask UI)  │   │  (heartbeat) │   │ (Celery/K8s)   │  │
│  └──────────────┘   └──────────────┘   └────────────────┘  │
│          │                  │                   │            │
│          └──────────────────┴───────────────────┘           │
│                             │                                │
│                    ┌────────────────┐                        │
│                    │   Metadata DB  │                        │
│                    │  (PostgreSQL)  │                        │
│                    └────────────────┘                        │
│                             │                                │
│                    ┌────────────────┐                        │
│                    │  Message Queue │                        │
│                    │    (Redis)     │                        │
│                    └────────────────┘                        │
└──────────────────────────────────────────────────────────────┘
```

### Componenti

**Webserver** — interfaccia Flask/Gunicorn che espone la UI, l'API REST e i log.

**Scheduler** — processo che scansiona i DAG ogni `scheduler_heartbeat_sec` secondi, crea DagRun per le schedule scadute e submette TaskInstance alla coda.

**Worker** — processo che esegue i task. Con executor `CeleryExecutor` è un processo Celery separato; con `KubernetesExecutor` è un Pod K8s; con `LocalExecutor` gira nello stesso processo dello Scheduler.

**Metadata Database** — PostgreSQL (consigliato) o MySQL che memorizza DAG, task, run, log. È il cuore dello stato di Airflow.

**Message Queue** — Redis o RabbitMQ per la comunicazione Scheduler→Worker con CeleryExecutor.

---

## Installazione

### Con Docker Compose (sviluppo locale)

```yaml
# docker-compose.yml
version: '3.8'
x-airflow-common:
  &airflow-common
  image: apache/airflow:2.8.1
  environment:
    AIRFLOW__CORE__EXECUTOR: CeleryExecutor
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__RESULT_BACKEND: db+postgresql://airflow:airflow@postgres/airflow
    AIRFLOW__CELERY__BROKER_URL: redis://:@redis:6379/0
    AIRFLOW__CORE__FERNET_KEY: ''  # Genera con: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: 'true'
    AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
    AIRFLOW__API__AUTH_BACKENDS: 'airflow.api.auth.backend.basic_auth'
  volumes:
    - ./dags:/opt/airflow/dags
    - ./logs:/opt/airflow/logs
    - ./plugins:/opt/airflow/plugins
  depends_on:
    &airflow-common-depends-on
    redis:
      condition: service_healthy
    postgres:
      condition: service_healthy

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 10s
      retries: 5

  redis:
    image: redis:7.2-bookworm
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s

  airflow-webserver:
    <<: *airflow-common
    command: webserver
    ports:
      - "8080:8080"

  airflow-scheduler:
    <<: *airflow-common
    command: scheduler

  airflow-worker:
    <<: *airflow-common
    command: celery worker

  airflow-init:
    <<: *airflow-common
    command: >
      bash -c "
        airflow db init &&
        airflow users create --username admin --password admin
          --firstname Admin --lastname User --role Admin --email admin@example.com
      "
```

```bash
# Avvio
docker compose up -d

# Verifica
docker compose ps
curl http://localhost:8080/health
```

### Installazione Production su Kubernetes

```bash
# Con Helm Chart ufficiale
helm repo add apache-airflow https://airflow.apache.org
helm repo update

# values.yaml minimo per produzione
cat > airflow-values.yaml << 'EOF'
executor: KubernetesExecutor

config:
  core:
    dags_are_paused_at_creation: "True"
    load_examples: "False"
  scheduler:
    min_file_process_interval: "30"
  webserver:
    expose_config: "False"

dags:
  gitSync:
    enabled: true
    repo: git@github.com:company/airflow-dags.git
    branch: main
    rev: HEAD
    depth: 1
    period: 60s
    subPath: "dags"
    sshKeySecret: airflow-ssh-secret

postgresql:
  enabled: true
  auth:
    password: "$AIRFLOW_DB_PASSWORD"

redis:
  enabled: true
EOF

helm install airflow apache-airflow/airflow \
  --namespace airflow \
  --create-namespace \
  -f airflow-values.yaml
```

---

## Concetti Fondamentali

### DAG (Directed Acyclic Graph)

Un DAG è la definizione della pipeline: nodi = task, archi = dipendenze. Il grafo deve essere aciclico (nessun ciclo).

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# I default_args si applicano a tutti i task del DAG
default_args = {
    "owner":              "data_engineering",
    "depends_on_past":    False,  # Non aspetta run precedente
    "retries":            3,
    "retry_delay":        timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay":    timedelta(minutes=30),
    "email_on_failure":   True,
    "email_on_retry":     False,
    "email":              ["data-team@company.com"],
    "sla":                timedelta(hours=2),  # Alert se non finisce in 2h
}

with DAG(
    dag_id="orders_daily_etl",
    default_args=default_args,
    description="ETL giornaliero ordini → DWH",
    schedule_interval="@daily",        # Oppure "0 2 * * *"
    start_date=datetime(2024, 1, 1),
    catchup=False,                     # Non backfilla run storici persi
    max_active_runs=1,                 # 1 solo run attivo per volta
    max_active_tasks=5,                # Max 5 task paralleli in questo DAG
    tags=["orders", "etl", "daily"],
    doc_md="""
    ## Orders Daily ETL
    Estrae ordini dal database operativo e carica nel DWH.
    **Schedule**: ogni giorno alle 02:00 UTC
    **Owner**: data-team@company.com
    **SLA**: completa entro 04:00 UTC
    """
) as dag:
    pass  # I task vengono aggiunti qui
```

### Task e Operatori

```python
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator

# PythonOperator: esegue una funzione Python
extract_task = PythonOperator(
    task_id="extract_orders",
    python_callable=extract_orders_from_source,
    op_kwargs={
        "run_date": "{{ ds }}",        # Template date
        "batch_size": 50_000
    },
    execution_timeout=timedelta(hours=1)
)

# BashOperator: esegue un comando shell
dbt_transform = BashOperator(
    task_id="dbt_run_orders",
    bash_command="cd /opt/dbt && dbt run --select orders+ --target prod",
    env={"DBT_PROFILES_DIR": "/opt/dbt"}
)

# PostgresOperator: esegue SQL direttamente
refresh_materialized = PostgresOperator(
    task_id="refresh_mv_daily_orders",
    postgres_conn_id="postgres_dwh",
    sql="REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_orders;"
)

# EmptyOperator: nodo dummy per coordinare dipendenze
start = EmptyOperator(task_id="start")
end = EmptyOperator(task_id="end")

# Definisci dipendenze
start >> extract_task >> dbt_transform >> refresh_materialized >> end
```

---

## Connections e Variables

```python
# Connessioni: gestite via UI o CLI (mai hardcodate nel codice)
# Admin → Connections → Add

# Accesso nel codice:
from airflow.hooks.base import BaseHook
conn = BaseHook.get_connection("postgres_dwh")
dsn = f"postgresql://{conn.login}:{conn.password}@{conn.host}:{conn.port}/{conn.schema}"

# Variables: parametri globali configurabili senza deploy
from airflow.models import Variable

batch_size = int(Variable.get("orders_batch_size", default_var="50000"))
slack_webhook = Variable.get("slack_webhook_url", deserialize_json=False)

# Variable con JSON
config = Variable.get("pipeline_config", deserialize_json=True)
# config = {"max_retries": 3, "timeout_hours": 2, "target_schema": "dwh"}
```

---

## XCom

XCom (Cross-Communication) permette ai task di condividere piccoli metadati:

```python
def extract_and_report(**context):
    """Estrae dati e pubblica metriche per il task successivo."""
    run_date = context["ds"]
    records = extract_orders(run_date)

    # Push: pubblica valore
    context["ti"].xcom_push(key="record_count", value=len(records))
    context["ti"].xcom_push(key="watermark", value=str(get_watermark()))

    return len(records)  # Il return è automaticamente pushato come 'return_value'


def load_and_verify(**context):
    """Legge metriche dal task precedente."""
    ti = context["ti"]

    # Pull: legge valore dal task precedente
    record_count = ti.xcom_pull(
        task_ids="extract_orders",
        key="record_count"
    )

    if record_count == 0:
        raise ValueError("Nessun record estratto — problema con la sorgente?")

    print(f"Carico {record_count} record")
    load_records()
```

---

## Template Variables

Airflow fornisce variabili Jinja utilizzabili nei parametri dei task:

```python
# Variabili di template disponibili:
templates_dict = {
    "{{ ds }}":              "2024-01-15",          # Run date ISO
    "{{ ds_nodash }}":       "20240115",             # Run date senza -
    "{{ ts }}":              "2024-01-15T02:00:00+00:00",  # Timestamp completo
    "{{ ts_nodash }}":       "20240115T020000+0000",
    "{{ dag.dag_id }}":      "orders_daily_etl",
    "{{ run_id }}":          "scheduled__2024-01-15...",
    "{{ dag_run.conf }}":    "{}",                   # Parametri del triggered run
    "{{ prev_ds }}":         "2024-01-14",           # Data precedente
    "{{ next_ds }}":         "2024-01-16",           # Data successiva
    "{{ macros.ds_add(ds, 1) }}": "2024-01-16",     # Macro aritmetica sulle date
}
```

---

## Trigger Rules

Il trigger rule controlla quando un task viene schedulato rispetto ai suoi upstream:

```python
from airflow.utils.trigger_rule import TriggerRule

# all_success (default): parte solo se tutti gli upstream hanno successo
# all_failed: parte solo se tutti gli upstream falliscono
# all_done: parte quando tutti gli upstream finiscono (successo o fail)
# one_failed: parte se almeno uno degli upstream fallisce
# one_success: parte se almeno uno degli upstream ha successo
# none_failed: parte se nessuno degli upstream fallisce (ma alcuni potrebbero essere skipped)
# none_failed_min_one_success: utile per branch convergence

notify_on_failure = PythonOperator(
    task_id="notify_failure",
    python_callable=send_failure_notification,
    trigger_rule=TriggerRule.ONE_FAILED  # Gira se almeno un upstream fallisce
)

join_after_branch = EmptyOperator(
    task_id="join",
    trigger_rule=TriggerRule.NONE_FAILED_MIN_ONE_SUCCESS
    # Converge branch senza richiedere che tutti abbiano successo
)
```

---

## Airflow con TaskFlow API (Airflow 2.0+)

TaskFlow semplifica la scrittura di DAG Python-nativi con decoratori:

```python
from airflow.decorators import dag, task
from datetime import datetime

@dag(
    dag_id="orders_etl_taskflow",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["orders", "taskflow"]
)
def orders_etl():
    """Pipeline ordini con TaskFlow API."""

    @task(retries=3)
    def extract(run_date: str) -> dict:
        records = fetch_orders(run_date)
        return {"count": len(records), "data": records}

    @task
    def transform(extracted: dict) -> dict:
        records = extracted["data"]
        cleaned = [transform_record(r) for r in records]
        valid = [r for r in cleaned if r is not None]
        return {"count": len(valid), "data": valid}

    @task
    def load(transformed: dict) -> int:
        records = transformed["data"]
        rows = bulk_load_to_dwh(records)
        return rows

    @task
    def validate(rows_loaded: int, original_count: int) -> None:
        if rows_loaded < original_count * 0.95:
            raise ValueError(
                f"Caricamento incompleto: {rows_loaded}/{original_count}"
            )
        print(f"Validazione OK: {rows_loaded} righe caricate")

    # Costruisci pipeline con Python ordinario
    extracted = extract("{{ ds }}")
    transformed = transform(extracted)
    rows = load(transformed)
    validate(rows, extracted["count"])


# Istanzia il DAG
orders_etl_dag = orders_etl()
```

---

## Pool e Priority Weight

I pool limitano la concorrenza per proteggere risorse condivise:

```bash
# Crea pool via CLI (o UI: Admin → Pools)
airflow pools set db_connections 10 "Max connessioni al database"
airflow pools set api_calls 5 "Max chiamate API parallele"
```

```python
# Assegna task a pool
extract_task = PythonOperator(
    task_id="extract_orders",
    python_callable=extract_orders,
    pool="db_connections",     # Max 10 task di questo pool in parallelo
    pool_slots=2,              # Questo task usa 2 slot del pool
    priority_weight=10         # Priorità alta (default 1)
)
```

---

## Gestione degli Errori e Alerting

```python
from airflow.utils.email import send_email
from airflow.hooks.base import BaseHook

def on_failure_callback(context):
    """Callback eseguita quando un task fallisce."""
    dag_id = context["dag"].dag_id
    task_id = context["task_instance"].task_id
    run_id = context["run_id"]
    exception = context.get("exception")

    # Slack notification
    slack_webhook = Variable.get("slack_webhook_data_alerts")
    import requests
    requests.post(slack_webhook, json={
        "text": (f":red_circle: *AIRFLOW FAILURE*\n"
                 f"DAG: `{dag_id}`\n"
                 f"Task: `{task_id}`\n"
                 f"Run: `{run_id}`\n"
                 f"Error: `{str(exception)[:200]}`")
    })


def on_sla_miss_callback(dag, task_list, blocking_task_list, slas, blocking_tis):
    """Callback per SLA miss."""
    print(f"SLA MISS: {dag.dag_id} — task: {task_list}")
    # Notifica team


with DAG(
    dag_id="critical_pipeline",
    on_failure_callback=on_failure_callback,
    sla_miss_callback=on_sla_miss_callback,
    ...
) as dag:
    pass
```

---

## Architettura Production-Grade

Per deployment enterprise, considerare:

| Componente | Sviluppo | Produzione |
|-----------|----------|-----------|
| Executor | LocalExecutor | CeleryExecutor o KubernetesExecutor |
| Metadb | SQLite | PostgreSQL HA |
| Code sync | Volume mount | Git Sync con deploy automatico |
| Secrets | Variables | HashiCorp Vault o AWS Secrets Manager |
| Scaling | Singola macchina | Cluster Kubernetes |
| HA Scheduler | No | Sì (Airflow 2.0+ supporta scheduler multipli) |

---

## Best Practice

**Un DAG = una responsabilità** — non creare mega-DAG con 50 task. Meglio 10 DAG da 5 task ciascuno, con cross-DAG dependencies tramite ExternalTaskSensor.

**Niente logica di business nel DAG** — il DAG definisce solo struttura e scheduling. La logica Python importata da moduli separati è testabile indipendentemente.

**Usa `catchup=False`** a meno di necessità esplicita di backfill automatico — il backfill spontaneo può sovraccaricare sorgenti e destinazioni.

**Versiona il DB dei DAG** — usare git per i file DAG e tag per i deploy permette rollback istantanei se un DAG rotto viene deployato.

**Testa i DAG prima del deploy** con `airflow dags test <dag_id> <date>` — esegue un DagRun completo in locale senza modificare il metadb.
