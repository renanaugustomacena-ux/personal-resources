# Best Practice Apache Airflow

Le pipeline Airflow mal progettate generano DAG fragili, scheduler lenti, debugging impossibile e deployment dolorosi. Questo capitolo raccoglie le pratiche che separano un deployment enterprise-grade da uno hobbyist.

## Struttura del Progetto

### Layout Raccomandato

```
airflow-project/
├── dags/
│   ├── __init__.py
│   ├── orders/
│   │   ├── orders_daily_etl.py
│   │   └── orders_hourly_sync.py
│   ├── customers/
│   │   └── customers_etl.py
│   └── shared/
│       └── base_dag.py          # Factory con default_args comuni
├── plugins/
│   ├── operators/
│   │   ├── data_quality.py
│   │   └── notifications.py
│   ├── hooks/
│   │   └── salesforce.py
│   └── plugin_registry.py
├── tests/
│   ├── dags/
│   │   └── test_orders_dag.py
│   ├── operators/
│   │   └── test_data_quality.py
│   └── conftest.py
├── scripts/
│   └── create_connections.sh
├── requirements.txt             # Versioni pinned
├── docker-compose.yml
└── .env.example
```

### Default Args Centralizzati

```python
# dags/shared/base_dag.py
from datetime import timedelta

DEFAULT_ARGS = {
    "owner":                    "data_engineering",
    "retries":                  3,
    "retry_delay":              timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay":          timedelta(minutes=30),
    "email_on_failure":         True,
    "email_on_retry":           False,
    "email":                    ["data-team@company.com"],
    "depends_on_past":          False,
    "on_failure_callback":      slack_failure_callback,
}

DAILY_DAG_DEFAULTS = {
    **DEFAULT_ARGS,
    "sla": timedelta(hours=3),
}
```

---

## Regole di Progettazione del DAG

### 1. Nessun Codice di Business nel File DAG

```python
# ❌ SBAGLIATO: logica di business hardcodata nel DAG
def extract_task(**context):
    conn = psycopg2.connect("postgresql://user:pass@host/db")  # Credenziale hardcodata!
    df = pd.read_sql("SELECT * FROM orders WHERE date = %s", conn, params=(context["ds"],))
    df["amount"] = df["amount"].apply(lambda x: float(x.replace("$", "").replace(",", "")))
    df.to_parquet(f"/tmp/orders_{context['ds']}.parquet")

# ✅ CORRETTO: DAG delega a moduli testabili
from pipelines.orders.extractor import OrdersExtractor
from pipelines.orders.transformer import OrdersTransformer

def extract_task(**context):
    extractor = OrdersExtractor.from_airflow_conn("postgres_orders")
    extractor.run(run_date=context["ds"], output_path=f"/tmp/orders_{context['ds']}.parquet")
```

### 2. Niente I/O al Top-Level del DAG

```python
# ❌ SBAGLIATO: accesso DB al momento del parse (ogni 30s!)
import psycopg2
conn = psycopg2.connect(...)          # Connessione a ogni parse del DAG!
tables = [row[0] for row in conn.execute("SELECT table_name FROM ...")]

with DAG(...) as dag:
    for table in tables:
        task = PythonOperator(task_id=f"load_{table}", ...)

# ✅ CORRETTO: I/O solo dentro i callable dei task
def get_tables_to_process(**context):
    conn = psycopg2.connect(get_dsn_from_airflow_conn("postgres_source"))
    with conn.cursor() as cur:
        cur.execute("SELECT table_name FROM tables_to_process WHERE active = TRUE")
        return [row[0] for row in cur.fetchall()]
```

### 3. DAG Piccoli e Focalizzati

```python
# ❌ SBAGLIATO: mega-DAG con 50 task
with DAG("everything_etl", ...):
    # 50 task: ordini, clienti, prodotti, categorie, pagamenti...

# ✅ CORRETTO: DAG separati per entità, con dipendenze esplicite
with DAG("orders_etl", ...): pass    # 5 task
with DAG("customers_etl", ...): pass # 5 task  
with DAG("revenue_report", ...): pass # 8 task, dipende dagli altri due via ExternalTaskSensor
```

### 4. Idempotenza

```python
def load_task(**context):
    run_id = context["run_id"]
    run_date = context["ds"]

    # ❌ Append naive: ogni retry duplica i dati
    # cur.execute("INSERT INTO orders SELECT ...")

    # ✅ Idempotente: cancella e riinserisci per stesso run_id
    cur.execute("DELETE FROM orders WHERE _run_id = %s", (run_id,))
    bulk_insert(orders, run_id=run_id)
    conn.commit()
```

---

## Gestione delle Dipendenze

### Versioni Pinned in requirements.txt

```txt
# requirements.txt
apache-airflow==2.8.1
apache-airflow-providers-postgres==5.10.0
apache-airflow-providers-amazon==8.14.0
apache-airflow-providers-google==10.14.0
apache-airflow-providers-snowflake==5.3.1
apache-airflow-providers-http==4.7.0
psycopg2-binary==2.9.9
pandas==2.1.4
pyarrow==14.0.2
```

Fissare le versioni previene regressioni silenti dopo upgrade automatici di pip.

### Constraints File

```bash
# Usa il constraints file di Airflow per evitare conflitti di dipendenze
pip install "apache-airflow==2.8.1" \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.8.1/constraints-3.11.txt"
```

---

## Performance

### Ottimizzazione del Parser

```ini
# airflow.cfg
[scheduler]
min_file_process_interval = 60     # Parsare meno frequentemente
max_callbacks_per_loop = 20         # Limita callback per ciclo
parsing_processes = 2               # Meno processi su macchine piccole

[core]
dag_file_processor_timeout = 60    # Timeout per file troppo pesanti
dagbag_import_timeout = 30.0       # Timeout per import singolo file
```

```python
# Evita import pesanti al top-level — usa lazy import
# ❌ LENTO: importato a ogni parse del DAG file
import tensorflow as tf
import torch

# ✅ VELOCE: importato solo quando il task gira
def ml_inference(**context):
    import tensorflow as tf   # Import lazy, solo a runtime del task
    model = tf.keras.models.load_model(...)
```

### Configurazione Worker

```ini
[celery]
# Numero di processi worker per macchina
worker_concurrency = 4

# Prefetch: quanti task prefetchare per worker
worker_prefetch_multiplier = 1  # 1 = no prefetch, evita task che aspettano

[core]
parallelism = 32          # Max task in esecuzione globale
dag_concurrency = 16      # Max task per DAG
max_active_tasks_per_dag = 16
```

---

## Sicurezza

### RBAC (Role-Based Access Control)

```python
# airflow.cfg
[webserver]
rbac = True
auth_backend = airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager

# Ruoli disponibili:
# - Admin: accesso completo
# - Op: can manage DAGs, connections, variables, pools
# - User: can trigger DAGs, view logs
# - Viewer: read-only
# - Public: no access

# Crea utente con ruolo limitato via CLI
airflow users create \
    --username analyst_user \
    --firstname Analyst \
    --lastname User \
    --role Viewer \
    --email analyst@company.com \
    --password "$(openssl rand -base64 16)"
```

### Accesso Minimale alle Connection

```python
# Non condividere conn_id tra DAG con diversi owner
# Un DAG che processa dati finanziari non deve usare
# la stessa connection di un DAG che processa analytics

# Crea conn separate per scope diversi:
# postgres_orders_readonly  → solo SELECT su tabella orders
# postgres_dwh_etl          → SELECT/INSERT/UPDATE sul DWH
# postgres_admin            → riservato solo a migration DAG
```

---

## Testing

### Unit Test Completo

```python
# tests/dags/test_orders_dag.py
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from airflow.models import DagBag


@pytest.fixture(scope="session")
def dagbag():
    return DagBag(dag_folder="dags/", include_examples=False)


class TestOrdersDag:
    def test_dag_exists(self, dagbag):
        assert "orders_daily_etl" in dagbag.dags

    def test_no_import_errors(self, dagbag):
        assert dagbag.import_errors == {}

    def test_task_count(self, dagbag):
        dag = dagbag.dags["orders_daily_etl"]
        assert len(dag.tasks) == 8  # Numero atteso di task

    def test_dag_schedule(self, dagbag):
        dag = dagbag.dags["orders_daily_etl"]
        assert str(dag.schedule_interval) == "0 2 * * *"

    def test_dependencies(self, dagbag):
        dag = dagbag.dags["orders_daily_etl"]
        extract = dag.get_task("extract")
        transform = dag.get_task("transform")
        load = dag.get_task("load")
        
        # transform deve dipendere da extract
        assert extract in transform.upstream_list
        # load deve dipendere da transform
        assert transform in load.upstream_list

    def test_default_args(self, dagbag):
        dag = dagbag.dags["orders_daily_etl"]
        assert dag.default_args["retries"] == 3
        assert dag.catchup == False

    @patch("pipelines.orders.extractor.OrdersExtractor.run")
    def test_extract_task_calls_extractor(self, mock_run, dagbag):
        """Test che il task di estrazione chiami il modulo corretto."""
        from airflow.models import TaskInstance
        dag = dagbag.dags["orders_daily_etl"]
        
        ti = TaskInstance(
            task=dag.get_task("extract"),
            run_id="test",
            execution_date=datetime(2024, 1, 15)
        )
        context = {"ds": "2024-01-15", "run_id": "test", "ti": MagicMock()}
        ti.run(ignore_ti_state=True)
        
        mock_run.assert_called_once()
```

### Test di Integrazione Locale

```bash
# Test completo del DAG in locale (senza modificare il metaDB)
airflow dags test orders_daily_etl 2024-01-15

# Test di un singolo task
airflow tasks test orders_daily_etl extract 2024-01-15

# Verifica stato dopo test
airflow tasks state orders_daily_etl extract 2024-01-15
```

---

## CI/CD Pipeline

```yaml
# .github/workflows/airflow-ci.yml
name: Airflow CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: airflow
          POSTGRES_DB: airflow
        ports: ["5432:5432"]

    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Init Airflow DB
        env:
          AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql://airflow:airflow@localhost/airflow
          AIRFLOW__CORE__FERNET_KEY: dGhpcyBpcyBhIHRlc3Qga2V5IGZvciBjaQ==
        run: airflow db init

      - name: Run DAG tests
        env:
          AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql://airflow:airflow@localhost/airflow
          AIRFLOW__CORE__FERNET_KEY: dGhpcyBpcyBhIHRlc3Qga2V5IGZvciBjaQ==
        run: |
          pytest tests/ -v --cov=dags --cov=plugins --cov-report=xml

      - name: Validate DAG syntax
        run: python -c "from airflow.models import DagBag; db = DagBag('dags/', include_examples=False); assert len(db.import_errors) == 0, db.import_errors"

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Sync DAGs to S3
        run: |
          aws s3 sync dags/ s3://airflow-dags-prod/ --delete
          aws s3 sync plugins/ s3://airflow-plugins-prod/ --delete
```

---

## Checklist Production Deployment

- [ ] Fernet key generata e conservata in modo sicuro (non in git)
- [ ] RBAC abilitato con ruoli appropriati per ogni utente
- [ ] Metadata DB su PostgreSQL (non SQLite)
- [ ] Redis per broker Celery (non DB)
- [ ] Worker su nodi separati dallo Scheduler
- [ ] `catchup=False` su tutti i DAG tranne quelli che ne hanno esplicita necessità
- [ ] SLA configurato su pipeline critiche
- [ ] Callback di failure su Slack/PagerDuty
- [ ] Log remoti su S3/GCS
- [ ] Connection create via Vault/Secrets Manager (non hardcodate nel metadata DB in plain text)
- [ ] DAG testati con `airflow dags test` prima del merge
- [ ] Nessun segreto in git (config, passwords, api keys)
- [ ] `max_active_runs=1` su pipeline che hanno side effects sequenziali
- [ ] Pool configurati per sorgenti con limiti di connessione
- [ ] Monitoring con StatsD/Prometheus + Grafana dashboard
