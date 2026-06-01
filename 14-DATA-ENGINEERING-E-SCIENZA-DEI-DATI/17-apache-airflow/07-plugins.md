# Plugin Airflow

I plugin permettono di estendere Airflow con operatori custom, hook, sensor, macro, viste web e altro senza modificare il core. Ogni file in `$AIRFLOW_HOME/plugins/` (o nella directory configurata) viene caricato automaticamente.

## Struttura di un Plugin

```
plugins/
├── __init__.py
├── custom_operators/
│   ├── __init__.py
│   ├── data_quality.py
│   └── notification.py
├── custom_hooks/
│   ├── __init__.py
│   └── salesforce.py
├── custom_sensors/
│   ├── __init__.py
│   └── data_availability.py
└── my_plugin.py          # File di registrazione
```

## Registrazione del Plugin

```python
# plugins/my_plugin.py
from airflow.plugins_manager import AirflowPlugin
from custom_operators.data_quality import DataQualityOperator
from custom_operators.notification import SlackNotificationOperator
from custom_hooks.salesforce import SalesforceHook
from custom_sensors.data_availability import DataAvailabilitySensor

class DataEngineeringPlugin(AirflowPlugin):
    name = "data_engineering_plugin"
    
    # Registra componenti
    operators = [DataQualityOperator, SlackNotificationOperator]
    hooks = [SalesforceHook]
    sensors = [DataAvailabilitySensor]
    macros = []        # Funzioni Jinja custom
    flask_blueprints = []  # Viste web aggiuntive
    appbuilder_views = []
    appbuilder_menu_items = []
```

## Operatore Custom Avanzato

```python
# plugins/custom_operators/data_quality.py
from airflow.models.baseoperator import BaseOperator
from airflow.hooks.base import BaseHook
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DataQualityOperator(BaseOperator):
    """
    Esegue una suite di check di qualità dati.
    
    Ogni check è un dict:
      name:     identificatore
      sql:      query SQL che deve restituire True/1 per passare
      severity: 'critical' (blocca), 'warning' (logga ma continua)
    """
    
    template_fields = ("run_date", "sql_checks")
    ui_color = "#4a90d9"  # Colore nella UI Airflow

    def __init__(
        self,
        conn_id: str,
        table: str,
        sql_checks: List[Dict[str, Any]],
        run_date: str = "{{ ds }}",
        max_failure_rate: float = 0.0,   # 0 = nessun fallimento tollerato
        **kwargs
    ):
        super().__init__(**kwargs)
        self.conn_id = conn_id
        self.table = table
        self.sql_checks = sql_checks
        self.run_date = run_date
        self.max_failure_rate = max_failure_rate

    def execute(self, context: Any) -> Dict[str, Any]:
        conn_meta = BaseHook.get_connection(self.conn_id)
        import psycopg2

        pg_conn = psycopg2.connect(
            host=conn_meta.host, port=conn_meta.port,
            dbname=conn_meta.schema,
            user=conn_meta.login, password=conn_meta.password
        )

        results = []
        critical_failures = []
        warnings = []

        with pg_conn.cursor() as cur:
            for check in self.sql_checks:
                name = check["name"]
                sql = check["sql"].format(
                    table=self.table, run_date=self.run_date
                )
                severity = check.get("severity", "critical")
                expected = check.get("expected", True)

                try:
                    cur.execute(sql)
                    actual = cur.fetchone()[0]
                    passed = bool(actual) if expected is True else (actual == expected)
                except Exception as e:
                    passed = False
                    actual = f"ERROR: {e}"

                result = {
                    "check": name,
                    "sql": sql,
                    "actual": actual,
                    "expected": expected,
                    "passed": passed,
                    "severity": severity
                }
                results.append(result)

                if not passed:
                    if severity == "critical":
                        critical_failures.append(name)
                        logger.error(f"CHECK FALLITO [{severity}] '{name}': actual={actual}")
                    else:
                        warnings.append(name)
                        logger.warning(f"CHECK FALLITO [{severity}] '{name}': actual={actual}")
                else:
                    logger.info(f"CHECK OK '{name}': {actual}")

        pg_conn.close()

        failure_rate = len(critical_failures) / len(results) if results else 0

        if critical_failures and failure_rate > self.max_failure_rate:
            raise ValueError(
                f"Data quality FALLITA su {self.table}: "
                f"{len(critical_failures)} check critici falliti: {critical_failures}"
            )

        context["ti"].xcom_push("dq_results", results)
        return {
            "total_checks": len(results),
            "passed": len(results) - len(critical_failures) - len(warnings),
            "critical_failures": critical_failures,
            "warnings": warnings,
        }
```

## Hook Custom

```python
# plugins/custom_hooks/salesforce.py
from airflow.hooks.base import BaseHook
import requests
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class SalesforceHook(BaseHook):
    """Hook per Salesforce API con OAuth2 e paginazione automatica."""

    conn_name_attr = "salesforce_conn_id"
    default_conn_name = "salesforce_default"
    conn_type = "http"
    hook_name = "Salesforce"

    def __init__(self, salesforce_conn_id: str = default_conn_name):
        super().__init__()
        self.salesforce_conn_id = salesforce_conn_id
        self._access_token: Optional[str] = None
        self._instance_url: Optional[str] = None
        self._session = requests.Session()

    def _authenticate(self):
        conn = self.get_connection(self.salesforce_conn_id)
        extra = conn.extra_dejson

        resp = self._session.post(
            f"https://{extra.get('login_domain', 'login.salesforce.com')}/services/oauth2/token",
            data={
                "grant_type":    "password",
                "client_id":     extra["client_id"],
                "client_secret": extra["client_secret"],
                "username":      conn.login,
                "password":      conn.password + extra.get("security_token", ""),
            }
        )
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data["access_token"]
        self._instance_url = data["instance_url"]
        self._session.headers.update({
            "Authorization": f"Bearer {self._access_token}"
        })
        logger.info(f"Autenticato su {self._instance_url}")

    def get_conn(self):
        if not self._access_token:
            self._authenticate()
        return self._session

    def query(self, soql: str) -> List[Dict]:
        """Esegue SOQL con paginazione automatica."""
        session = self.get_conn()
        url = f"{self._instance_url}/services/data/v59.0/query"
        all_records = []

        while url:
            resp = session.get(url, params={"q": soql} if "query" in url else {})
            if resp.status_code == 401:
                # Token scaduto — riautentica
                self._access_token = None
                self._authenticate()
                session = self.get_conn()
                resp = session.get(url, params={"q": soql} if "query" in url else {})
            resp.raise_for_status()
            data = resp.json()
            all_records.extend(data.get("records", []))
            next_url = data.get("nextRecordsUrl")
            url = f"{self._instance_url}{next_url}" if next_url else None
            soql = None  # Dopo la prima pagina, usa nextRecordsUrl direttamente

        # Rimuovi attributi Salesforce internali
        for record in all_records:
            record.pop("attributes", None)

        return all_records

    def bulk_create(self, sobject: str, records: List[Dict]) -> List[Dict]:
        """Inserisce record in bulk via Salesforce Bulk API 2.0."""
        session = self.get_conn()
        import csv, io

        # Crea job
        job_resp = session.post(
            f"{self._instance_url}/services/data/v59.0/jobs/ingest",
            json={"object": sobject, "operation": "insert", "contentType": "CSV"}
        )
        job_resp.raise_for_status()
        job_id = job_resp.json()["id"]

        # Carica dati
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
        session.put(
            f"{self._instance_url}/services/data/v59.0/jobs/ingest/{job_id}/batches",
            data=buf.getvalue(),
            headers={"Content-Type": "text/csv"}
        )

        # Chiudi job
        session.patch(
            f"{self._instance_url}/services/data/v59.0/jobs/ingest/{job_id}",
            json={"state": "UploadComplete"}
        )

        return {"job_id": job_id, "records_uploaded": len(records)}
```

## Sensor Custom

```python
# plugins/custom_sensors/data_availability.py
from airflow.sensors.base import BaseSensorOperator
from airflow.hooks.base import BaseHook
from typing import Any
import logging

logger = logging.getLogger(__name__)


class DataAvailabilitySensor(BaseSensorOperator):
    """
    Aspetta che la tabella upstream abbia dati per la data di run.
    Controlla via SQL sul database di destinazione.
    """

    template_fields = ("sql", "run_date")

    def __init__(
        self,
        conn_id: str,
        table: str,
        run_date: str = "{{ ds }}",
        min_rows: int = 1,
        date_column: str = "created_at",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.conn_id = conn_id
        self.table = table
        self.run_date = run_date
        self.min_rows = min_rows
        self.date_column = date_column

    def poke(self, context: Any) -> bool:
        """Controlla se ci sono abbastanza dati. Ritorna True per uscire dal loop."""
        conn_meta = BaseHook.get_connection(self.conn_id)
        import psycopg2

        conn = psycopg2.connect(
            host=conn_meta.host, port=conn_meta.port,
            dbname=conn_meta.schema,
            user=conn_meta.login, password=conn_meta.password
        )

        with conn.cursor() as cur:
            cur.execute(
                f"SELECT COUNT(*) FROM {self.table} WHERE DATE({self.date_column}) = %s",
                (self.run_date,)
            )
            count = cur.fetchone()[0]

        conn.close()

        logger.info(
            f"Sensor {self.table}: {count} righe per {self.run_date} "
            f"(minimo: {self.min_rows})"
        )
        return count >= self.min_rows
```

## Macro Custom

Le macro personalizzate estendono il sistema di template Jinja con funzioni Python:

```python
# plugins/custom_macros.py
from datetime import datetime, date
from typing import Optional

def fiscal_year(dt_str: str) -> int:
    """Restituisce l'anno fiscale (FY inizia ad aprile) per una data."""
    dt = datetime.strptime(dt_str, "%Y-%m-%d").date()
    return dt.year if dt.month >= 4 else dt.year - 1


def fiscal_quarter(dt_str: str) -> str:
    """Restituisce FQ nel formato 'FY2024-Q1'."""
    dt = datetime.strptime(dt_str, "%Y-%m-%d").date()
    fy = fiscal_year(dt_str)
    months_in_fy = (dt.month - 4) % 12 + 1
    quarter = (months_in_fy - 1) // 3 + 1
    return f"FY{fy}-Q{quarter}"


def previous_business_day(dt_str: str) -> str:
    """Restituisce il giorno lavorativo precedente."""
    import pandas as pd
    dt = pd.Timestamp(dt_str)
    prev = dt - pd.offsets.BDay(1)
    return prev.strftime("%Y-%m-%d")


# Registra nel plugin
from airflow.plugins_manager import AirflowPlugin

class MacrosPlugin(AirflowPlugin):
    name = "custom_macros_plugin"
    macros = [fiscal_year, fiscal_quarter, previous_business_day]
```

```python
# Uso nei template
task = PythonOperator(
    task_id="process",
    python_callable=process_fn,
    op_kwargs={
        "fiscal_year":    "{{ macros.fiscal_year(ds) }}",
        "fiscal_quarter": "{{ macros.fiscal_quarter(ds) }}",
        "prev_bday":      "{{ macros.previous_business_day(ds) }}"
    }
)
```

## Vista Web Custom

```python
# plugins/views/pipeline_dashboard.py
from flask import Blueprint, render_template_string
from flask_appbuilder import BaseView, expose, has_access
from airflow.www.app import csrf

blueprint = Blueprint(
    "pipeline_dashboard",
    __name__,
    template_folder="templates",
    url_prefix="/custom"
)


class PipelineDashboardView(BaseView):
    """Vista custom per dashboard pipeline."""
    default_view = "dashboard"

    @expose("/dashboard")
    @has_access
    def dashboard(self):
        from airflow.models import DagRun
        from sqlalchemy import func
        from airflow.utils.session import create_session

        with create_session() as session:
            runs = session.query(
                DagRun.dag_id,
                DagRun.state,
                func.count().label("count")
            ).filter(
                DagRun.start_date > func.now() - func.cast("7 days", type_=None)
            ).group_by(DagRun.dag_id, DagRun.state).all()

        return self.render_template(
            "dashboard.html",
            runs=runs
        )


# Registrazione
from airflow.plugins_manager import AirflowPlugin

class DashboardPlugin(AirflowPlugin):
    name = "pipeline_dashboard_plugin"
    flask_blueprints = [blueprint]
    appbuilder_views = [{"view": PipelineDashboardView()}]
    appbuilder_menu_items = [{
        "name": "Pipeline Dashboard",
        "category": "Custom",
        "view": PipelineDashboardView()
    }]
```

## Installazione Plugin via Package Python

Per plugin condivisi tra team, distribuirli come package Python è più scalabile:

```python
# setup.py del package plugin
from setuptools import setup, find_packages

setup(
    name="acme-airflow-plugins",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "apache-airflow>=2.6.0",
        "requests>=2.28.0",
    ],
    entry_points={
        "airflow.plugins": [
            "acme_plugins = acme_airflow_plugins:AcmePlugin"
        ]
    }
)
```

```bash
# Installazione nel container Airflow
pip install acme-airflow-plugins==1.0.0
# o da git
pip install git+https://github.com/acme/airflow-plugins.git@v1.0.0
```

---

## Best Practice

**Testa i plugin indipendentemente da Airflow** — operatori e hook sono classi Python normali, testabili con pytest senza avviare un'istanza Airflow.

**Versiona i plugin** — un plugin rotto deployato silenziosamente rompe tutti i DAG che lo usano. Usa semantic versioning e changelog.

**Non mettere logica di business nei plugin** — i plugin devono essere generici e riutilizzabili. La logica specifica va nei DAG o nei moduli importati.

**Monitora il tempo di caricamento dei plugin** — un plugin con import pesanti (es. TensorFlow) rallenta il boot dello scheduler. Usa lazy import dove possibile.
