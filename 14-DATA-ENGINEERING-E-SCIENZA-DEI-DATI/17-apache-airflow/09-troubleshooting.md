# Troubleshooting Apache Airflow

La diagnosi di problemi in Airflow richiede di navigare attraverso layer diversi: scheduler, worker, metadb, DAG file, connessioni esterne. Questo capitolo fornisce un approccio sistematico ai problemi più comuni.

## Metodologia Diagnostica

```
1. Controlla lo stato del cluster
   └── airflow scheduler status + webserver health
       └── Scheduler heartbeat recente? Worker attivi?

2. Identifica il DAG/task problematico
   └── UI Grid view + task logs
       └── Qual è lo stato? Qual è il messaggio di errore?

3. Riproduci localmente
   └── airflow tasks test <dag_id> <task_id> <date>
       └── Stesso errore? → bug nel codice
       └── Nessun errore? → problema ambiente produzione

4. Analizza il metadb
   └── Query su dag_run, task_instance, log
       └── Pattern di errore? Timing anomalo?

5. Applica fix e verifica
   └── Fix → test locale → deploy → re-run del task
```

---

## Problemi Comuni e Soluzioni

### Scheduler Non Invia Task

**Sintomi**: Task rimangono in `queued` per ore. Scheduler attivo ma worker non li prendono.

```bash
# Verifica stato worker Celery
celery -A airflow.executors.celery_executor.app inspect active
celery -A airflow.executors.celery_executor.app inspect ping

# Verifica code Redis/RabbitMQ
redis-cli LLEN airflow

# Riavvia worker se bloccati
celery -A airflow.executors.celery_executor.app purge  # Svuota queue
# Poi riavvia i worker

# Verifica che la Celery app sia la stessa su scheduler e worker
# (stessa AIRFLOW__CELERY__BROKER_URL, stessa FERNET_KEY)
```

```sql
-- Task in queued da troppo tempo
SELECT
    dag_id,
    task_id,
    state,
    queued_dttm,
    EXTRACT(EPOCH FROM (NOW() - queued_dttm)) / 60 AS queued_minutes
FROM task_instance
WHERE state = 'queued'
  AND queued_dttm < NOW() - INTERVAL '30 minutes'
ORDER BY queued_dttm;
```

### Scheduler Lento / High CPU

**Sintomi**: Scheduler usa 100% CPU. Nuovi DagRun vengono creati in ritardo.

```bash
# Profila il scheduler
python -m cProfile -o scheduler.prof \
    -m airflow scheduler -n 5  # Dopo 5 DagRun, esci

# Analizza il profilo
python -c "
import pstats
stats = pstats.Stats('scheduler.prof')
stats.sort_stats('cumulative')
stats.print_stats(20)
"
```

```ini
# airflow.cfg — ottimizzazioni scheduler
[scheduler]
min_file_process_interval = 120     # Aumenta: riduce parsing frequente
parsing_processes = 2               # Riduci su macchine con poca CPU
max_tis_per_query = 256             # Riduci se il DB è lento

[core]
# Se hai molti DAG file inutilizzati, nascondili
dag_ignore_file_syntax_errors = False
```

```python
# Identifica DAG lenti da parsare
# Usa airflow dags report per vedere i tempi di parsing
# airflow dags report
```

### Import Error nel DAG

**Sintomi**: DAG non appare nella UI. `DagBag.import_errors` non è vuoto.

```bash
# Visualizza errori di import
airflow dags list-import-errors

# Debug specifico
python -c "
from airflow.models import DagBag
db = DagBag('dags/', include_examples=False)
for dag_id, err in db.import_errors.items():
    print(f'{dag_id}: {err}')
"

# Test import diretto del file
python dags/my_dag.py
```

Cause comuni:
- Import di modulo non installato nel virtualenv dei worker
- Errore di sintassi Python
- Dipendenza circolare tra moduli
- Variabile d'ambiente mancante letta al top-level

### Task Bloccato in `running`

**Sintomi**: Task in stato `running` da ore. Il processo worker è morto o il container è stato killato.

```bash
# Identifica task zombie
airflow tasks list --output table --dag-id my_dag

# Reset manuale di task bloccati
airflow tasks clear --dag-id orders_daily_etl \
    --task-id extract \
    --start-date 2024-01-15 \
    --end-date 2024-01-15 \
    --only-failed  # Oppure --only-running per forzare restart
```

```sql
-- Reset diretto nel metadb (solo in emergenza)
UPDATE task_instance
SET state = 'failed',
    end_date = NOW()
WHERE state = 'running'
  AND start_date < NOW() - INTERVAL '3 hours'
  AND dag_id = 'orders_daily_etl';
```

### Errore di Connessione al Database

**Sintomi**: `OperationalError: could not connect to server` nei log del task.

```bash
# Testa connessione dal container worker
airflow connections test postgres_dwh

# Verifica che il conn_id esista
airflow connections list | grep postgres_dwh

# Verifica connettività di rete
docker exec airflow_worker_1 pg_isready -h dwh.internal -p 5432

# Verifica credenziali direttamente
docker exec airflow_worker_1 psql \
    "postgresql://etl_user:@dwh.internal:5432/datawarehouse" \
    -c "SELECT 1"
```

### XCom Errori

**Sintomi**: `xcom_pull` restituisce `None` quando il task precedente ha sicuramente pubblicato.

```python
# Causa comune: task_ids sbagliato nella pull
# ❌ task_id errato (usa task_id, non python_callable.__name__)
value = ti.xcom_pull(task_ids="extract_orders_function", key="count")

# ✅ usa il task_id definito nel DAG
value = ti.xcom_pull(task_ids="extract_orders", key="count")

# Verifica XCom nel metadb
```

```sql
SELECT
    dag_id,
    task_id,
    run_id,
    key,
    LEFT(value::text, 200) AS value_preview
FROM xcom
WHERE dag_id = 'orders_daily_etl'
  AND run_id LIKE '%2024-01-15%'
ORDER BY timestamp DESC;
```

### Out of Memory

**Sintomi**: Worker killato con `Killed` nei log. OOM killer del kernel.

```python
# ❌ Caricamento dell'intera tabella in memoria
def extract(**context):
    conn = psycopg2.connect(...)
    df = pd.read_sql("SELECT * FROM large_table", conn)  # OOM con 100M righe!
    context["ti"].xcom_push("data", df.to_dict())  # XCom non supporta GB di dati!

# ✅ Processing a chunkin con file intermedio
def extract(**context):
    run_id = context["run_id"]
    output_path = f"/shared/tmp/extract_{run_id}.parquet"
    
    conn = psycopg2.connect(...)
    cur = conn.cursor(name="large_cursor")  # Server-side cursor
    cur.execute("SELECT * FROM large_table WHERE ...")
    
    import pyarrow as pa, pyarrow.parquet as pq
    writer = None
    while True:
        rows = cur.fetchmany(50_000)
        if not rows:
            break
        table = pa.Table.from_pylist([dict(zip([d[0] for d in cur.description], r)) for r in rows])
        if writer is None:
            writer = pq.ParquetWriter(output_path, table.schema)
        writer.write_table(table)
    
    if writer:
        writer.close()
    
    context["ti"].xcom_push("output_path", output_path)  # Solo il path, non i dati
```

---

## Script di Diagnostica Completo

```bash
#!/bin/bash
# airflow-diagnostics.sh

echo "=== AIRFLOW CLUSTER HEALTH ==="
curl -s http://localhost:8080/api/v1/health | python3 -m json.tool

echo ""
echo "=== SCHEDULER STATUS ==="
airflow scheduler --health-check 2>&1 | tail -5

echo ""
echo "=== IMPORT ERRORS ==="
airflow dags list-import-errors 2>&1

echo ""
echo "=== FAILED TASKS (last 24h) ==="
airflow db shell << 'SQL'
SELECT dag_id, task_id, state, start_date, try_number
FROM task_instance
WHERE state = 'failed' AND start_date > NOW() - INTERVAL '24 hours'
ORDER BY start_date DESC
LIMIT 20;
SQL

echo ""
echo "=== ZOMBIE TASKS (running > 2h) ==="
airflow db shell << 'SQL'
SELECT dag_id, task_id, state, start_date,
       EXTRACT(EPOCH FROM (NOW() - start_date))/3600 AS hours_running
FROM task_instance
WHERE state = 'running' AND start_date < NOW() - INTERVAL '2 hours';
SQL

echo ""
echo "=== POOL UTILIZATION ==="
airflow pools list

echo ""
echo "=== CELERY WORKER STATUS ==="
celery -A airflow.executors.celery_executor.app inspect active_queues 2>&1 | head -30
```

---

## Recovery Procedure

### Re-run di un DAG Fallito

```bash
# Opzione 1: Clear e re-run dal task fallito
airflow tasks clear \
    --dag-id orders_daily_etl \
    --start-date 2024-01-15 \
    --end-date 2024-01-15 \
    --downstream \       # Cancella anche i task downstream
    --only-failed        # Solo i task falliti

# Opzione 2: Mark come success e skip (emergenza)
airflow tasks mark-success \
    --dag-id orders_daily_etl \
    --task-id extract \
    --execution-date 2024-01-15 \
    --downstream

# Opzione 3: Trigger nuovo run
airflow dags trigger orders_daily_etl \
    --conf '{"run_date": "2024-01-15", "force": true}' \
    --run-id "manual_recovery_20240115"
```

### Pulizia del Metadb

```sql
-- Rimuovi run e task vecchi (> 90 giorni) per ridurre dimensione DB
DELETE FROM xcom WHERE timestamp < NOW() - INTERVAL '90 days';
DELETE FROM task_instance WHERE start_date < NOW() - INTERVAL '90 days';
DELETE FROM dag_run WHERE start_date < NOW() - INTERVAL '90 days';
-- In Airflow 2.x usa il comando built-in:
-- airflow db clean --clean-before-timestamp "2023-10-01T00:00:00" --tables all
```

---

## Tabella di Risoluzione Rapida

| Sintomo | Causa Probabile | Azione |
|---------|----------------|--------|
| Task in `queued` per ore | Worker disconnessi da broker | Riavvia worker, verifica Redis/RabbitMQ |
| Scheduler non crea DagRun | Import error nel DAG file | `airflow dags list-import-errors` |
| Task in `running` zombie | Worker killato, nessun cleanup | `airflow tasks clear --only-running` |
| Import error | Modulo mancante nel venv dei worker | `pip install` sul container worker |
| `None` da xcom_pull | `task_ids` errato o task non pushato | Verifica task_id nella pull + metadb xcom |
| OOM worker | Dataset caricato in memoria | Server-side cursor + file intermedi |
| Scheduler ad alta CPU | DAG file troppo pesanti o frequenti | Aumenta `min_file_process_interval` |
| Connection refused | Credenziali errate o DB non raggiungibile | `airflow connections test <conn_id>` |
