# Scheduling in Airflow

Lo scheduling è il meccanismo che determina quando un DAG viene eseguito. Airflow offre scheduling cron, intervalli fissi, trigger manuali, dataset-driven scheduling e scheduling programmato.

## Schedule Interval

```python
from airflow import DAG
from datetime import datetime, timedelta

# Cron expression
with DAG("daily_etl", schedule_interval="0 2 * * *", ...):   # 02:00 UTC ogni giorno
    pass

with DAG("hourly", schedule_interval="@hourly", ...):         # Ogni ora
    pass

with DAG("weekly", schedule_interval="@weekly", ...):         # Ogni domenica a mezzanotte
    pass

# Airflow presets
presets = {
    "@once":    "Esegui una sola volta",
    "@hourly":  "0 * * * *",
    "@daily":   "0 0 * * *",
    "@weekly":  "0 0 * * 0",
    "@monthly": "0 0 1 * *",
    "@yearly":  "0 0 1 1 *",
}

# Timedelta (intervallo fisso da ultimo run)
with DAG("every_6h", schedule_interval=timedelta(hours=6), ...):
    pass

# Solo trigger manuale
with DAG("manual_only", schedule_interval=None, ...):
    pass
```

## Data Logic di Airflow

Airflow ha una semantica di scheduling peculiare: il `execution_date` di un DAG run rappresenta l'inizio del periodo che il run sta elaborando, non l'orario di esecuzione effettivo.

```
Schedule: daily @midnight
                                                  
2024-01-01 00:00 ──── 2024-01-02 00:00 ──── 2024-01-03 00:00
      │                      │                      │
      │   execution_date      │   execution_date      │
      │   = 2024-01-01        │   = 2024-01-02        │
      │   (periodo 1)         │   (periodo 2)         │
      │                      │                      │
      └── run_01 starts ──────┘── run_02 starts ─────┘
          at 00:00 on 01/02       at 00:00 on 01/03
```

Il run con `execution_date=2024-01-01` parte a `2024-01-02 00:00` — questo è il "data interval end" che triggera il run. Questo spiega perché `{{ ds }}` nel template è la data del periodo, non l'orario di effettiva esecuzione.

```python
# Template variables per capire la data logic
def process(**context):
    ds = context["ds"]                  # "2024-01-01" — data del periodo
    ts = context["ts"]                  # "2024-01-02T00:00:00+00:00" — run effettivo
    data_interval_start = context["data_interval_start"]  # datetime(2024,1,1)
    data_interval_end   = context["data_interval_end"]    # datetime(2024,1,2)

    # Per un ETL giornaliero, filtra sulla data del periodo:
    query = f"SELECT * FROM orders WHERE DATE(created_at) = '{ds}'"
```

## Catchup e Backfill

**Catchup** — se `catchup=True` (default storico), Airflow esegue tutti i run mancati dall'`start_date`. Per la maggior parte delle pipeline è indesiderato:

```python
# ATTENZIONE: se catchup=True e start_date è 1 anno fa, Airflow lancia
# 365 DagRun in parallelo (fino a max_active_runs)
with DAG(
    "orders_etl",
    start_date=datetime(2024, 1, 1),
    catchup=False,     # NON backfillare run storici automaticamente
    max_active_runs=1, # Solo 1 run attivo per volta
):
    pass
```

**Backfill manuale** — per riprocessare periodi specifici in modo controllato:

```bash
# Backfill per un range di date
airflow dags backfill \
    --start-date 2024-01-01 \
    --end-date 2024-01-31 \
    --reset-dagruns \    # Resetta run esistenti prima di riprocessare
    orders_etl

# Backfill con parallelismo
airflow dags backfill \
    --start-date 2024-01-01 \
    --end-date 2024-01-31 \
    --max-jobs 4 \
    orders_etl
```

## Trigger Manuale via API REST

```python
import requests

AIRFLOW_URL = "http://airflow-webserver:8080"
AUTH = ("admin", "admin")

def trigger_dag(
    dag_id: str,
    conf: dict = None,
    run_id: str = None,
    logical_date: str = None
) -> dict:
    """Triggera manualmente un DAG via API REST."""
    payload = {
        "conf": conf or {},
        "dag_run_id": run_id,
        "logical_date": logical_date,
    }
    # Rimuovi None values
    payload = {k: v for k, v in payload.items() if v is not None}

    resp = requests.post(
        f"{AIRFLOW_URL}/api/v1/dags/{dag_id}/dagRuns",
        json=payload,
        auth=AUTH
    )
    resp.raise_for_status()
    return resp.json()


# Trigger con parametri
result = trigger_dag(
    dag_id="orders_etl",
    conf={"run_date": "2024-01-15", "force_full": True},
    run_id="manual_backfill_20240115"
)
print(f"DagRun creato: {result['dag_run_id']}")
```

## Dataset-Driven Scheduling

```python
from airflow import Dataset
from airflow.decorators import dag, task
from datetime import datetime

# Definisci dataset come URI
ORDERS_DATASET  = Dataset("s3://data-lake/processed/orders/")
CUSTOMERS_DATASET = Dataset("postgres://dwh/dim_customer")

# Producer: dichiara cosa produce
@dag(schedule_interval="@daily", start_date=datetime(2024, 1, 1), catchup=False)
def orders_producer():
    @task(outlets=[ORDERS_DATASET])
    def extract_and_load():
        extract_orders()
        return "done"
    extract_and_load()

# Consumer: viene triggerato quando i dataset sono pronti
@dag(
    schedule=[ORDERS_DATASET, CUSTOMERS_DATASET],  # Aspetta entrambi
    start_date=datetime(2024, 1, 1),
    catchup=False
)
def revenue_report():
    @task
    def build_report():
        generate_revenue_report()
    build_report()

orders_dag = orders_producer()
report_dag = revenue_report()
```

## Timetable Custom

Per schedule non esprimibili con cron (es. giorni lavorativi italiani, festività, orari di mercato):

```python
from airflow.timetables.base import DagRunInfo, DataInterval, TimeRestriction, Timetable
from pendulum import DateTime, instance, timezone
from typing import Optional
import pendulum

class BusinessDaysTimetable(Timetable):
    """Esegue solo nei giorni lavorativi (lun-ven, no festività italiane)."""

    ITALIAN_HOLIDAYS_2024 = {
        (1, 1), (1, 6), (4, 25), (5, 1), (6, 2),
        (8, 15), (11, 1), (12, 8), (12, 25), (12, 26)
    }

    def _is_business_day(self, dt: DateTime) -> bool:
        if dt.weekday() >= 5:  # Sabato=5, Domenica=6
            return False
        if (dt.month, dt.day) in self.ITALIAN_HOLIDAYS_2024:
            return False
        return True

    def _next_business_day(self, dt: DateTime) -> DateTime:
        next_day = dt.add(days=1)
        while not self._is_business_day(next_day):
            next_day = next_day.add(days=1)
        return next_day

    def next_dagrun_info(
        self,
        last_automated_data_interval: Optional[DataInterval],
        restriction: TimeRestriction
    ) -> Optional[DagRunInfo]:
        if last_automated_data_interval is None:
            # Prima esecuzione
            tz = timezone("Europe/Rome")
            start = pendulum.now(tz).start_of("day").at(8, 0, 0)
            if not self._is_business_day(start):
                start = self._next_business_day(start).at(8, 0, 0)
        else:
            start = self._next_business_day(
                last_automated_data_interval.end
            ).at(8, 0, 0)

        if restriction.latest is not None and start > restriction.latest:
            return None

        end = start.add(days=1)
        return DagRunInfo.interval(start=start, end=end)

    def serialize(self) -> dict:
        return {}

    @classmethod
    def deserialize(cls, data: dict) -> "BusinessDaysTimetable":
        return cls()


# Registra la timetable custom nel plugin
from airflow.plugins_manager import AirflowPlugin

class BusinessDaysPlugin(AirflowPlugin):
    name = "business_days_plugin"
    timetables = [BusinessDaysTimetable]


# Uso nel DAG
with DAG(
    "financial_report",
    timetable=BusinessDaysTimetable(),
    start_date=datetime(2024, 1, 1),
    ...
) as dag:
    pass
```

## Depends on Past

```python
with DAG(
    "sequential_etl",
    default_args={
        "depends_on_past": True,  # Il task non parte se il run precedente è fallito
    },
    ...
) as dag:
    # Con depends_on_past=True:
    # Il task extract del 15/01 non parte se extract del 14/01 è failed
    # Utile per pipeline cumulative dove l'ordine è critico
    extract = PythonOperator(...)
```

## Monitoring dello Scheduler

```bash
# Verifica health dello scheduler
airflow scheduler --health-check

# Vedi prossimi run pianificati
airflow dags next-execution orders_etl

# Lista DagRun attivi
airflow dags list-runs --dag-id orders_etl --state running

# Conteggio task per stato
airflow tasks states-for-dag-run orders_etl scheduled__2024-01-15T02:00:00+00:00
```

```sql
-- Query diretta sul metadata DB per analisi scheduling
SELECT
    dag_id,
    state,
    execution_date,
    start_date,
    end_date,
    EXTRACT(EPOCH FROM (end_date - start_date)) AS duration_sec
FROM dag_run
WHERE dag_id = 'orders_etl'
  AND execution_date > NOW() - INTERVAL '7 days'
ORDER BY execution_date DESC;

-- Task falliti nelle ultime 24h
SELECT
    dag_id,
    task_id,
    state,
    start_date,
    end_date,
    try_number
FROM task_instance
WHERE state = 'failed'
  AND start_date > NOW() - INTERVAL '24 hours'
ORDER BY start_date DESC;
```

## Configurazione Scheduler per Produzione

```python
# airflow.cfg (sezione [scheduler])
[scheduler]
# Frequenza di scansione file DAG
min_file_process_interval = 30

# Numero di processi per parsare i DAG in parallelo
parsing_processes = 4

# Heartbeat interval
scheduler_heartbeat_sec = 5

# Numero max di DAG run da creare per ciclo
max_tis_per_query = 512

# Se True, usa solo DAGRun date logica precisa
use_job_schedule = True

# HA: se True, più scheduler possono girare contemporaneamente (Airflow 2.0+)
standalone_dag_processor = False
```
