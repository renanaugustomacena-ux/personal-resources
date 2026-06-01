# Monitoring e Alerting in Airflow

Un sistema di orchestrazione senza monitoring è una blackbox. Airflow espone metriche, log e hook per costruire un'osservabilità completa sullo stato delle pipeline.

## Monitoring via UI

L'interfaccia web di Airflow offre diverse viste per il monitoring:

- **DAGs view**: stato di tutti i DAG, ultimo run, prossima esecuzione
- **Grid view**: storico dei run con task state colorati per data
- **Graph view**: topologia del DAG con stati attuali
- **Gantt view**: timeline di esecuzione dei task
- **Task logs**: output completo di ogni task
- **Audit log**: chi ha fatto cosa nell'interfaccia

## Metriche con StatsD e Prometheus

```python
# airflow.cfg
[metrics]
statsd_on = True
statsd_host = statsd.monitoring.svc
statsd_port = 8125
statsd_prefix = airflow

# Metriche chiave emesse:
# airflow.dag.loading-duration.<dag_id>
# airflow.dagrun.duration.success.<dag_id>
# airflow.dagrun.duration.failed.<dag_id>
# airflow.scheduler.heartbeat
# airflow.ti.start.<dag_id>.<task_id>
# airflow.ti.finish.<dag_id>.<task_id>.success
# airflow.ti.finish.<dag_id>.<task_id>.failed
# airflow.pool.open_slots.<pool_name>
# airflow.pool.queued_tasks.<pool_name>
# airflow.pool.running_tasks.<pool_name>
```

```yaml
# prometheus-statsd-exporter.yml per Prometheus
mappings:
  - match: "airflow.dagrun.duration.success.*"
    name: "airflow_dagrun_duration_seconds"
    labels:
      dag_id: "$1"
      status: "success"
    observer_type: summary

  - match: "airflow.ti.finish.*.*.success"
    name: "airflow_task_instance_duration_seconds"
    labels:
      dag_id: "$1"
      task_id: "$2"
      status: "success"
```

## Query di Monitoring sul Metadata DB

```sql
-- Panoramica ultimi 7 giorni per DAG
SELECT
    dag_id,
    state,
    COUNT(*) AS runs,
    ROUND(AVG(EXTRACT(EPOCH FROM (end_date - start_date))), 0) AS avg_duration_sec,
    ROUND(MAX(EXTRACT(EPOCH FROM (end_date - start_date))), 0) AS max_duration_sec,
    MAX(start_date) AS last_run
FROM dag_run
WHERE start_date > NOW() - INTERVAL '7 days'
GROUP BY dag_id, state
ORDER BY dag_id, state;

-- Task falliti e loro messaggi di errore
SELECT
    dr.dag_id,
    ti.task_id,
    ti.execution_date,
    ti.try_number,
    ti.state,
    ti.start_date,
    ti.end_date
FROM task_instance ti
JOIN dag_run dr ON dr.run_id = ti.run_id
WHERE ti.state = 'failed'
  AND ti.start_date > NOW() - INTERVAL '24 hours'
ORDER BY ti.start_date DESC;

-- SLA violations: pipeline non complete entro tempo atteso
SELECT
    dag_id,
    execution_date,
    task_id,
    email_sent,
    timestamp AS sla_miss_timestamp,
    description
FROM sla_miss
WHERE timestamp > NOW() - INTERVAL '7 days'
ORDER BY timestamp DESC;

-- Trend durata pipeline (regressione di performance)
SELECT
    DATE(start_date) AS run_date,
    dag_id,
    AVG(EXTRACT(EPOCH FROM (end_date - start_date))) AS avg_sec,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (end_date - start_date))) AS p95_sec
FROM dag_run
WHERE state = 'success'
  AND start_date > NOW() - INTERVAL '30 days'
GROUP BY 1, 2
ORDER BY 1, 2;

-- Task con più retry (segnale di instabilità)
SELECT
    dag_id,
    task_id,
    AVG(try_number) AS avg_tries,
    MAX(try_number) AS max_tries,
    COUNT(*) AS total_runs
FROM task_instance
WHERE start_date > NOW() - INTERVAL '7 days'
  AND state IN ('success', 'failed')
GROUP BY dag_id, task_id
HAVING AVG(try_number) > 1.5
ORDER BY avg_tries DESC;
```

## Alerting via Callback

```python
from airflow.models import TaskInstance, DagRun
from datetime import datetime
import requests

def build_failure_message(context: dict) -> str:
    """Costruisce messaggio di errore formattato."""
    dag = context["dag"]
    ti: TaskInstance = context["task_instance"]
    exception = context.get("exception")
    log_url = ti.log_url

    return (
        f"*DAG:* `{dag.dag_id}`\n"
        f"*Task:* `{ti.task_id}`\n"
        f"*Run date:* `{context['ds']}`\n"
        f"*Try #:* {ti.try_number}\n"
        f"*Error:* `{str(exception)[:500] if exception else 'Unknown'}`\n"
        f"*Log:* {log_url}"
    )


def slack_failure_callback(context: dict):
    """Invia notifica Slack quando un task fallisce."""
    from airflow.models import Variable
    webhook = Variable.get("slack_webhook_data_alerts", default_var=None)
    if not webhook:
        return

    requests.post(webhook, json={
        "attachments": [{
            "color": "#FF0000",
            "title": f":red_circle: Task Failure: {context['dag'].dag_id}",
            "text": build_failure_message(context),
            "footer": "Airflow",
            "ts": int(datetime.utcnow().timestamp())
        }]
    }, timeout=10)


def slack_success_callback(context: dict):
    """Notifica completion per pipeline critiche."""
    from airflow.models import Variable
    webhook = Variable.get("slack_webhook_data_alerts", default_var=None)
    if not webhook:
        return

    ti: TaskInstance = context["task_instance"]
    if ti.task_id != "end":  # Solo sull'ultimo task
        return

    dag = context["dag"]
    duration = context["task_instance"].duration

    requests.post(webhook, json={
        "text": (f":white_check_mark: *{dag.dag_id}* completato in "
                 f"{duration:.0f}s per il {context['ds']}")
    }, timeout=10)


def pagerduty_callback(context: dict):
    """Trigger PagerDuty per pipeline critiche fallite."""
    import requests
    from airflow.models import Variable

    routing_key = Variable.get("pagerduty_routing_key")
    ti: TaskInstance = context["task_instance"]

    requests.post("https://events.pagerduty.com/v2/enqueue", json={
        "routing_key": routing_key,
        "event_action": "trigger",
        "payload": {
            "summary": f"Airflow FAILURE: {context['dag'].dag_id}/{ti.task_id}",
            "severity": "critical",
            "source": "airflow",
            "custom_details": {
                "dag_id": context["dag"].dag_id,
                "task_id": ti.task_id,
                "run_date": context["ds"],
                "error": str(context.get("exception", ""))[:500]
            }
        }
    }, timeout=10)


# Applica callback al DAG
with DAG(
    "critical_orders_etl",
    default_args={
        "on_failure_callback": slack_failure_callback,
        "on_success_callback": slack_success_callback,
    },
    on_failure_callback=pagerduty_callback,  # Callback a livello DAG
    ...
) as dag:
    pass
```

## SLA Monitoring

```python
from airflow import DAG
from datetime import timedelta

def sla_miss_callback(dag, task_list, blocking_task_list, slas, blocking_tis):
    """Chiamata quando un task non completa entro il suo SLA."""
    from airflow.models import Variable
    import requests

    missing = [str(sla) for sla in slas]
    blocking = [str(ti) for ti in blocking_tis]

    webhook = Variable.get("slack_webhook_data_alerts")
    requests.post(webhook, json={
        "text": (
            f":warning: *SLA MISS* su `{dag.dag_id}`\n"
            f"Task in ritardo: {missing}\n"
            f"Task bloccanti: {blocking}"
        )
    }, timeout=10)


with DAG(
    "time_sensitive_etl",
    sla_miss_callback=sla_miss_callback,
    default_args={
        "sla": timedelta(hours=2),  # Ogni task deve completare entro 2h
    },
    ...
) as dag:

    # SLA specifico per task critico
    load_task = PythonOperator(
        task_id="load_to_dwh",
        python_callable=load_fn,
        sla=timedelta(hours=1)  # Override: questo task ha 1h di SLA
    )
```

## Grafana Dashboard

```json
// Pannelli Grafana per Airflow (query su StatsD/Prometheus)
{
  "panels": [
    {
      "title": "DAG Run Success Rate (7d)",
      "type": "stat",
      "targets": [{
        "expr": "sum(rate(airflow_dagrun_duration_success_total[7d])) / sum(rate(airflow_dagrun_duration_total[7d]))"
      }]
    },
    {
      "title": "Task Failures (24h)",
      "type": "timeseries",
      "targets": [{
        "expr": "increase(airflow_ti_finish_total{status='failed'}[1h])"
      }]
    },
    {
      "title": "Scheduler Heartbeat",
      "type": "stat",
      "targets": [{
        "expr": "time() - airflow_scheduler_heartbeat_last_timestamp",
        "legendFormat": "Seconds since last heartbeat"
      }]
    },
    {
      "title": "Pool Utilization",
      "type": "bargauge",
      "targets": [{
        "expr": "airflow_pool_running_tasks / (airflow_pool_running_tasks + airflow_pool_open_slots)"
      }]
    }
  ]
}
```

## Log Management

```python
# airflow.cfg per logging centralizzato su S3/GCS
[logging]
remote_logging = True
remote_base_log_folder = s3://airflow-logs-prod/
remote_log_conn_id = aws_default
logging_level = INFO
encrypt_s3_logs = True

# Per GCS:
# remote_base_log_folder = gs://airflow-logs-prod/
# remote_log_conn_id = google_cloud_default
```

```python
# Accesso ai log via API REST
import requests

def get_task_logs(dag_id: str, dag_run_id: str, task_id: str, try_number: int = 1) -> str:
    """Recupera log di un task via API."""
    resp = requests.get(
        f"{AIRFLOW_URL}/api/v1/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs/{try_number}",
        auth=AUTH,
        headers={"Accept": "text/plain"}
    )
    resp.raise_for_status()
    return resp.text
```

## Operational Health Check

```python
import requests
from typing import Dict

def airflow_health_check(airflow_url: str, auth: tuple) -> Dict:
    """Verifica la salute dell'istanza Airflow."""
    resp = requests.get(f"{airflow_url}/api/v1/health", auth=auth, timeout=10)
    resp.raise_for_status()
    health = resp.json()

    issues = []

    # Scheduler deve essere healthy
    scheduler_status = health.get("scheduler", {}).get("status")
    if scheduler_status != "healthy":
        issues.append(f"Scheduler non healthy: {scheduler_status}")

    # Metadb deve essere connesso
    metadb_status = health.get("metadatabase", {}).get("status")
    if metadb_status != "healthy":
        issues.append(f"MetaDB non healthy: {metadb_status}")

    return {
        "healthy": len(issues) == 0,
        "scheduler": scheduler_status,
        "metadb": metadb_status,
        "issues": issues
    }
```

---

## Best Practice

**Configura sempre SLA** per le pipeline critiche — il SLA miss callback è il primo segnale di degrado delle performance prima del failure.

**Monitora il heartbeat dello scheduler** — uno scheduler silenzioso (che non batte il heartbeat) è più pericoloso di un task fallito: le pipeline semplicemente smettono di girare senza alcun allarme visibile.

**Centralizza i log su S3/GCS** — i log locali vengono persi al restart del container. Per debugging post-mortem, i log remoti sono essenziali.

**Tieni i Grafana dashboard aggiornati** — un dashboard obsoleto crea false sicurezze. Allinealo alle pipeline critiche attuali.

**Usa differenti severity per gli alert** — non tutto deve andare a PagerDuty. Task failures normalissimi → Slack. SLA miss → Slack + email. DAG failure su pipeline business-critical → PagerDuty.
