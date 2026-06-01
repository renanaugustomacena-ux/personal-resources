# Best Practice ETL

Le pipeline ETL mal progettate sono tra le fonti più comuni di problemi in un data team: dati corrotti, run mancati non rilevati, latenze imprevedibili, impossibilità di debugging. Questo capitolo raccoglie i principi che separano una pipeline professionale da una pipeline fragile.

## Principi Fondamentali

### 1. Idempotenza

Una pipeline idempotente produce lo stesso risultato se eseguita una volta o cento volte con gli stessi dati di input. Questo è il principio più importante: rende sicuro il retry e il backfill.

```python
# NON idempotente
def load_bad(records, conn):
    cur = conn.cursor()
    for r in records:
        cur.execute("INSERT INTO orders VALUES (%s, %s)", (r["id"], r["amount"]))
    conn.commit()
# Problema: ogni esecuzione duplica i record

# Idempotente
def load_good(records, conn, run_id: str):
    from psycopg2.extras import execute_values
    # Prima pulisce i dati del run, poi reinserisce
    cur = conn.cursor()
    cur.execute("DELETE FROM orders WHERE _run_id = %s", (run_id,))
    execute_values(
        cur,
        "INSERT INTO orders (id, amount, _run_id) VALUES %s",
        [(r["id"], r["amount"], run_id) for r in records]
    )
    conn.commit()
# Risultato sempre identico per lo stesso run_id
```

### 2. Separazione delle Responsabilità

Ogni fase (extract, transform, load) deve essere indipendente, testabile e deployabile separatamente:

```
raw/           → Bronze: dati grezzi inalterati (append only)
staging/       → Silver: dati puliti e validati
warehouse/     → Gold: modelli dimensionali per analytics
```

Non processare i raw in-place. Non mixare logica di business con operazioni di I/O.

### 3. Dati Raw Immutabili

I dati grezzi non vengono mai modificati. Archiviali su storage a basso costo (S3, GCS) per sempre. Se la logica di trasformazione cambia, riprocessi dal raw — non perdi mai la possibilità di correggere errori.

```python
def archive_raw(records: list, source: str, run_id: str, s3_bucket: str):
    """Archivia sempre i raw prima di qualsiasi trasformazione."""
    import boto3, json, gzip
    from datetime import datetime

    today = datetime.utcnow().strftime("%Y/%m/%d")
    key = f"raw/{source}/{today}/{run_id}.jsonl.gz"

    content = "\n".join(json.dumps(r) for r in records).encode("utf-8")
    compressed = gzip.compress(content)

    boto3.client("s3").put_object(
        Bucket=s3_bucket,
        Key=key,
        Body=compressed,
        ContentEncoding="gzip",
        ContentType="application/x-ndjson",
        StorageClass="STANDARD_IA"  # Infrequent Access per ridurre costi
    )
    return f"s3://{s3_bucket}/{key}"
```

### 4. Fail Fast, Non Silenziosamente

Un errore ingoiato silenziosamente è più pericoloso di un crash visibile. Meglio fermare la pipeline che caricare dati corrotti nel data warehouse.

```python
# SBAGLIATO — errore silenzioso
def transform_bad(record):
    try:
        amount = float(record["amount"])
        return {**record, "amount": amount}
    except:
        return {**record, "amount": 0.0}  # Sostituisce con 0 silenziosamente!

# CORRETTO — errore esplicito, record in DLQ
def transform_good(record):
    try:
        amount = float(record["amount"])
        if amount < 0:
            raise ValueError(f"Importo negativo: {amount}")
        return {**record, "amount": round(amount, 2)}
    except (TypeError, ValueError) as e:
        raise DataQualityError(f"Campo 'amount' non valido: {e}") from e
```

---

## Design della Pipeline

### Schema a Tre Layer

```
┌─────────────────────────────────────────────────────────────────┐
│  BRONZE LAYER (Raw)                                             │
│  • Dati grezzi inalterati                                       │
│  • Formato: JSON/CSV/Parquet originale                          │
│  • Partizione per data di ingestione                            │
│  • Conservazione: indefinita                                    │
├─────────────────────────────────────────────────────────────────┤
│  SILVER LAYER (Staging)                                         │
│  • Dati puliti, validati, deduplicati                           │
│  • Schema unificato, tipi corretti                              │
│  • Partizione per data di business                              │
│  • Conservazione: 2 anni                                        │
├─────────────────────────────────────────────────────────────────┤
│  GOLD LAYER (Analytics / Data Mart)                             │
│  • Modelli dimensionali, aggregazioni, KPI                      │
│  • Ottimizzati per query analitiche                             │
│  • Partizione per colonne ad alta cardinalità di filtro         │
│  • Conservazione: permanente                                    │
└─────────────────────────────────────────────────────────────────┘
```

### Naming Convention

```python
# Consistenza nei nomi → leggibilità, mantenibilità

# Pipeline names: {source}_{entity}_{frequency}
pipeline_names = [
    "postgres_orders_daily",
    "salesforce_leads_hourly",
    "stripe_payments_realtime",
]

# Table names: {layer}_{source}_{entity}
table_names = [
    "raw_postgres_orders",        # Bronze
    "stg_orders",                 # Silver
    "dim_customer",               # Gold - dimension
    "fact_orders",                # Gold - fact
    "mart_revenue_by_channel",    # Gold - data mart
]

# Column names: snake_case, suffisso tipo dove utile
column_conventions = {
    "ids": "order_id, customer_sk, product_key",
    "timestamps": "created_at, updated_at, _loaded_at",
    "flags": "is_current, is_deleted, is_high_value",
    "amounts": "gross_amount, net_amount, tax_amount",
    "meta": "_run_id, _source, _loaded_at, _version",
}
```

### Gestione dei Segreti

```python
import os
from typing import Optional

class SecretManager:
    """Gestione sicura dei segreti per le pipeline."""

    @staticmethod
    def get_db_url(service: str) -> str:
        """Carica DSN da variabile d'ambiente o AWS Secrets Manager."""
        env_key = f"{service.upper()}_DATABASE_URL"
        url = os.environ.get(env_key)
        if url:
            return url

        # Fallback su AWS Secrets Manager
        import boto3
        import json
        client = boto3.client("secretsmanager")
        secret = client.get_secret_value(SecretId=f"etl/{service}/db")
        creds = json.loads(secret["SecretString"])
        return (f"postgresql://{creds['username']}:{creds['password']}"
                f"@{creds['host']}:{creds['port']}/{creds['dbname']}")

    @staticmethod
    def get_api_key(service: str) -> str:
        """Carica API key da variabile d'ambiente."""
        key = os.environ.get(f"{service.upper()}_API_KEY")
        if not key:
            raise ValueError(f"Missing env var: {service.upper()}_API_KEY")
        return key
```

---

## Performance

### Dimensionamento dei Batch

Il batch size ottimale dipende dalla dimensione media di un record, la RAM disponibile e le caratteristiche della destinazione.

```python
def calculate_optimal_batch_size(
    avg_record_bytes: int,
    available_memory_mb: int = 512,
    memory_multiplier: float = 3.0  # Overhead Python dict vs raw bytes
) -> int:
    """
    Calcola il batch size ottimale per non superare la memoria.
    
    memory_multiplier: un dict Python usa ~3x più memoria del raw bytes
    0.8: lascia 20% di headroom per overhead aggiuntivo
    """
    available_bytes = available_memory_mb * 1024 * 1024 * 0.8
    record_size = avg_record_bytes * memory_multiplier
    return max(100, int(available_bytes / record_size))


# Linee guida pratiche per PostgreSQL target:
BATCH_SIZES = {
    "small_records": 50_000,    # < 500 bytes/record
    "medium_records": 10_000,   # 500 - 5000 bytes/record
    "large_records": 1_000,     # > 5000 bytes/record (JSONB, arrays)
    "blob_records": 100,        # Record con BLOBs o testi lunghi
}
```

### Parallelismo Controllato

```python
import concurrent.futures
from typing import List, Callable, Any

def parallel_extract(
    configs: List[dict],
    extract_fn: Callable,
    max_workers: int = 4,
    timeout: float = 300.0
) -> List[Any]:
    """
    Estrazione parallela con limite di workers per non sovraccaricare le sorgenti.
    
    max_workers deve rispettare il connection pool della sorgente.
    Es: se il DB ha max_connections=100 e ci sono 5 processi ETL,
    non usare più di 15-20 workers per processo.
    """
    results = []
    errors = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(extract_fn, cfg): cfg for cfg in configs}
        for future in concurrent.futures.as_completed(futures, timeout=timeout):
            config = futures[future]
            try:
                results.append(future.result())
            except Exception as e:
                errors.append({"config": config, "error": str(e)})

    if errors:
        for err in errors:
            logger.error(f"Estrazione fallita: {err}")

    return results
```

### Connection Pooling

```python
from psycopg2 import pool

class DatabasePool:
    """Pool di connessioni PostgreSQL per pipeline multi-threaded."""

    _instance = None

    def __init__(self, dsn: str, min_conn: int = 2, max_conn: int = 10):
        self._pool = pool.ThreadedConnectionPool(
            minconn=min_conn,
            maxconn=max_conn,
            dsn=dsn,
            # Timeout connessione dopo 5s di inattività
            keepalives=1,
            keepalives_idle=30,
            keepalives_interval=10,
            keepalives_count=5
        )

    @classmethod
    def get_instance(cls, dsn: str) -> "DatabasePool":
        if cls._instance is None:
            cls._instance = cls(dsn)
        return cls._instance

    def getconn(self):
        return self._pool.getconn()

    def putconn(self, conn):
        self._pool.putconn(conn)

    def closeall(self):
        self._pool.closeall()
```

---

## Monitoring e Observability

### Metriche da Raccogliere

```python
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, Any

@dataclass
class PipelineRunMetrics:
    pipeline_name: str
    run_id: str
    run_date: str
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Volume
    rows_extracted: int = 0
    rows_transformed: int = 0
    rows_loaded: int = 0
    rows_rejected: int = 0
    bytes_processed: int = 0
    
    # Timing
    extract_duration_sec: float = 0.0
    transform_duration_sec: float = 0.0
    load_duration_sec: float = 0.0
    total_duration_sec: float = 0.0
    
    # Quality
    error_rate: float = 0.0
    dlq_count: int = 0
    
    # Status
    status: str = "running"
    error_message: str = None
    finished_at: str = None

    @property
    def rows_per_second(self) -> float:
        return self.rows_loaded / max(self.total_duration_sec, 0.001)

    def finish(self, status: str = "success", error: str = None):
        self.finished_at = datetime.utcnow().isoformat()
        self.status = status
        self.error_message = error
        self.error_rate = self.rows_rejected / max(self.rows_extracted, 1)

    def to_prometheus_labels(self) -> Dict[str, str]:
        return {
            "pipeline": self.pipeline_name,
            "status": self.status,
            "run_date": self.run_date
        }


def emit_metrics_to_prometheus(metrics: PipelineRunMetrics):
    """Emette metriche verso Prometheus Pushgateway."""
    from prometheus_client import (
        CollectorRegistry, Gauge, Counter, push_to_gateway
    )
    registry = CollectorRegistry()
    labels = ["pipeline", "status"]

    rows_loaded = Gauge("etl_rows_loaded", "Righe caricate", labels, registry=registry)
    duration = Gauge("etl_duration_seconds", "Durata in secondi", ["pipeline"], registry=registry)
    error_rate = Gauge("etl_error_rate", "Tasso di errori", ["pipeline"], registry=registry)

    rows_loaded.labels(
        pipeline=metrics.pipeline_name,
        status=metrics.status
    ).set(metrics.rows_loaded)
    duration.labels(pipeline=metrics.pipeline_name).set(metrics.total_duration_sec)
    error_rate.labels(pipeline=metrics.pipeline_name).set(metrics.error_rate)

    push_to_gateway(
        "http://pushgateway:9091",
        job=f"etl_{metrics.pipeline_name}",
        registry=registry
    )
```

### Dashboard SQL per il Monitoraggio

```sql
-- Run recenti con stato
SELECT
    pipeline_name,
    run_date,
    status,
    rows_loaded,
    error_rate,
    total_duration_sec,
    started_at,
    finished_at
FROM etl_run_log
WHERE started_at > NOW() - INTERVAL '7 days'
ORDER BY started_at DESC
LIMIT 100;

-- Pipeline che falliscono con frequenza
SELECT
    pipeline_name,
    COUNT(*) FILTER (WHERE status = 'failed') AS failures,
    COUNT(*) AS total_runs,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'failed') / COUNT(*), 1) AS failure_rate_pct
FROM etl_run_log
WHERE started_at > NOW() - INTERVAL '30 days'
GROUP BY pipeline_name
HAVING COUNT(*) FILTER (WHERE status = 'failed') > 0
ORDER BY failure_rate_pct DESC;

-- SLA check: pipeline che non girano da troppo tempo
SELECT
    expected.pipeline_name,
    expected.max_age_hours,
    EXTRACT(EPOCH FROM (NOW() - MAX(started_at))) / 3600 AS hours_since_last_run,
    CASE
        WHEN EXTRACT(EPOCH FROM (NOW() - MAX(started_at))) / 3600 > expected.max_age_hours
        THEN 'SLA_VIOLATED'
        ELSE 'ok'
    END AS sla_status
FROM (VALUES
    ('orders_etl', 25),
    ('customers_etl', 25),
    ('products_etl', 49)
) AS expected(pipeline_name, max_age_hours)
LEFT JOIN etl_run_log log ON log.pipeline_name = expected.pipeline_name
                          AND log.status = 'success'
GROUP BY expected.pipeline_name, expected.max_age_hours;
```

---

## Testing

### Test Unitari per Transform

```python
import pytest

def test_order_transformation():
    """Le trasformazioni sono funzioni pure — test semplici."""
    input_record = {
        "order_id": "ORD-001",
        "customer_email": "  ALICE@EXAMPLE.COM  ",
        "amount": "$1,234.56",
        "created_at": "2024-01-15",
        "status": None
    }

    result = transform_order(input_record)

    assert result["order_id"] == "ORD-001"
    assert result["customer_email"] == "alice@example.com"
    assert result["amount"] == 1234.56
    assert result["status"] == "unknown"
    assert result["created_at"] is not None


def test_pipeline_e2e_with_test_data(pg_test_conn, pg_target_conn):
    """Test E2E con database di test reale."""
    # Inserisci dati di test nella sorgente
    insert_test_orders(pg_test_conn, count=100)

    # Esegui la pipeline
    pipeline = OrderPipeline(
        source_conn=pg_test_conn,
        target_conn=pg_target_conn
    )
    result = pipeline.run(run_date="2024-01-15", dry_run=False)

    # Verifica risultati
    assert result["status"] == "success"
    assert result["rows_loaded"] == 100

    # Verifica dati nel target
    with pg_target_conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM fact_orders WHERE run_date = '2024-01-15'")
        count = cur.fetchone()[0]
    assert count == 100
```

---

## Checklist Production Readiness

### Prima del Deploy

- [ ] La pipeline è idempotente (testata con doppia esecuzione)
- [ ] I dati raw vengono archiviati prima di qualsiasi trasformazione
- [ ] Gli errori di dati vanno in DLQ, non crashano la pipeline
- [ ] La pipeline ha un run_id univoco e viene loggata
- [ ] Tutti i segreti sono in variabili d'ambiente o secret manager
- [ ] Il tasso di errore massimo accettabile è configurato e fa abort
- [ ] I test unitari coprono le trasformazioni principali (>80%)
- [ ] Esiste un test E2E su database di test
- [ ] La pipeline è testata su un campione reale di dati storici

### In Produzione

- [ ] Dashboard di monitoring con metriche chiave (volume, durata, error rate)
- [ ] Alert per fallimenti e SLA violations
- [ ] Processo di review e reprocessing del DLQ (almeno settimanale)
- [ ] Runbook per le procedure di recovery più comuni
- [ ] Documentazione: cosa consuma, cosa produce, SLA, owner

### Anti-Pattern da Evitare

```python
# ❌ Hard-coding delle credenziali
conn = psycopg2.connect("postgresql://user:password123@prod-db/mydb")

# ✅ Variabili d'ambiente
conn = psycopg2.connect(os.environ["DATABASE_URL"])

# ❌ SELECT * senza LIMIT su tabelle grandi
cur.execute("SELECT * FROM orders")
rows = cur.fetchall()  # OOM su tabelle da milioni di righe

# ✅ Server-side cursor con fetchmany
cur = conn.cursor(name="my_cursor")
cur.execute("SELECT * FROM orders")
while chunk := cur.fetchmany(10000):
    process(chunk)

# ❌ Trasformazione in-place dei dati raw
record["email"] = record["email"].lower()  # Muta l'originale

# ✅ Crea nuovo dict
clean_record = {**record, "email": record["email"].lower()}

# ❌ Ignorare gli errori di caricamento
try:
    load(records)
except Exception:
    pass  # Silenzioso!

# ✅ Classificare e gestire esplicitamente
try:
    load(records)
except IntegrityError as e:
    dlq.enqueue_batch(records, error=str(e))
except OperationalError as e:
    time.sleep(5)
    load(records)  # Retry una volta
```

---

## Evoluzione dello Schema

Gestire i cambiamenti dello schema sorgente è uno dei problemi più frequenti nelle pipeline di produzione:

```python
def schema_flexible_load(conn, table: str, records: list):
    """
    Carica record anche se lo schema è cambiato:
    - Nuove colonne nella sorgente: aggiunte automaticamente alla tabella
    - Colonne mancanti nella sorgente: caricate come NULL
    """
    if not records:
        return

    # Recupera schema corrente della tabella target
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = %s AND table_schema = 'public'
        """, (table,))
        existing_cols = {row[0] for row in cur.fetchall()}

    # Trova nuove colonne
    new_cols = set(records[0].keys()) - existing_cols
    if new_cols:
        with conn.cursor() as cur:
            for col in new_cols:
                # Inferisci tipo dalla prima riga non-null
                sample = next(
                    (r[col] for r in records if r.get(col) is not None), None
                )
                pg_type = "TEXT"  # Default sicuro
                if isinstance(sample, bool):
                    pg_type = "BOOLEAN"
                elif isinstance(sample, int):
                    pg_type = "BIGINT"
                elif isinstance(sample, float):
                    pg_type = "DOUBLE PRECISION"

                cur.execute(
                    f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {pg_type}"
                )
                logger.info(f"Aggiunta colonna {col} ({pg_type}) a {table}")
        conn.commit()

    # Ora carica normalmente
    upsert(conn, table, records, key_columns=["id"])
```
