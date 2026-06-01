# Gestione degli Errori nelle Pipeline ETL

La gestione degli errori in una pipeline ETL è diversa da quella in un'applicazione web: gli errori non si verificano in real-time davanti all'utente, ma durante elaborazioni batch notturne su milioni di record. Un errore mal gestito può corrompere silenziosamente il data warehouse o bloccare l'intera catena downstream.

## Tassonomia degli Errori

### Errori Transitori

Temporanei per natura: connessioni di rete perse, timeout del database, rate limiting API, lock contention. Risolvibili con retry.

```python
import time
import random
from functools import wraps
from typing import Callable, Type, Tuple

def retry(
    exceptions: Tuple[Type[Exception], ...],
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True
):
    """Decorator per retry con backoff esponenziale e jitter."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        raise  # Esaurite i tentativi

                    delay = min(
                        base_delay * (exponential_base ** (attempt - 1)),
                        max_delay
                    )
                    if jitter:
                        delay *= (0.5 + random.random() * 0.5)

                    print(f"Tentativo {attempt}/{max_attempts} fallito: {e}. "
                          f"Retry tra {delay:.1f}s")
                    time.sleep(delay)
        return wrapper
    return decorator


# Uso:
import psycopg2
import requests

@retry(
    exceptions=(psycopg2.OperationalError, psycopg2.InterfaceError),
    max_attempts=5,
    base_delay=2.0
)
def connect_to_database(dsn: str):
    return psycopg2.connect(dsn)


@retry(
    exceptions=(requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.HTTPError),
    max_attempts=3,
    base_delay=1.0
)
def fetch_from_api(url: str, **kwargs):
    resp = requests.get(url, timeout=30, **kwargs)
    if resp.status_code == 429:
        retry_after = int(resp.headers.get("Retry-After", 60))
        time.sleep(retry_after)
        raise requests.exceptions.HTTPError("Rate limited")
    resp.raise_for_status()
    return resp.json()
```

### Errori di Dati

Record che non passano la validazione: valori fuori range, tipi sbagliati, violazioni di foreign key, email malformate. Non risolvibili con retry — richiedono correzione dei dati o regole di gestione.

### Errori di Sistema

Mancanza di spazio su disco, OOM, crash del processo, interruzioni di rete prolungate. Richiedono intervento operativo.

### Errori di Logica

Bug nel codice di trasformazione che producono risultati sbagliati senza lanciare eccezioni. I più pericolosi perché difficili da rilevare.

---

## Dead Letter Queue (DLQ)

Il pattern DLQ isola i record problematici invece di bloccare l'intera pipeline:

```python
import json
import os
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class FailedRecord:
    record: Dict[str, Any]
    error_type: str
    error_message: str
    pipeline_name: str
    stage: str                       # "extract", "transform", "load"
    run_id: str
    attempt_count: int = 1
    first_failed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_failed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    resolved: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


class DeadLetterQueue:
    """
    Gestisce record falliti con persistenza su PostgreSQL.
    Supporta reprocessing selettivo e analisi degli errori.
    """

    def __init__(self, conn):
        self.conn = conn
        self._ensure_table()

    def _ensure_table(self):
        """Crea la tabella DLQ se non esiste."""
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS etl_dead_letter_queue (
                    id              BIGSERIAL PRIMARY KEY,
                    pipeline_name   TEXT NOT NULL,
                    run_id          TEXT NOT NULL,
                    stage           TEXT NOT NULL,
                    error_type      TEXT NOT NULL,
                    error_message   TEXT NOT NULL,
                    record_data     JSONB NOT NULL,
                    attempt_count   INT DEFAULT 1,
                    first_failed_at TIMESTAMPTZ DEFAULT NOW(),
                    last_failed_at  TIMESTAMPTZ DEFAULT NOW(),
                    resolved        BOOLEAN DEFAULT FALSE,
                    resolved_at     TIMESTAMPTZ,
                    resolution_note TEXT
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_dlq_pipeline
                ON etl_dead_letter_queue (pipeline_name, resolved, last_failed_at)
            """)
        self.conn.commit()

    def enqueue(self, failed: FailedRecord):
        """Inserisce un record fallito nella DLQ."""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO etl_dead_letter_queue
                    (pipeline_name, run_id, stage, error_type,
                     error_message, record_data, attempt_count)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                failed.pipeline_name,
                failed.run_id,
                failed.stage,
                failed.error_type,
                failed.error_message,
                json.dumps(failed.record),
                failed.attempt_count
            ))
        self.conn.commit()

    def enqueue_batch(self, failures: List[FailedRecord]):
        """Inserisce multipli record falliti in batch."""
        if not failures:
            return
        from psycopg2.extras import execute_values
        values = [
            (f.pipeline_name, f.run_id, f.stage, f.error_type,
             f.error_message, json.dumps(f.record), f.attempt_count)
            for f in failures
        ]
        with self.conn.cursor() as cur:
            execute_values(
                cur,
                """INSERT INTO etl_dead_letter_queue
                   (pipeline_name, run_id, stage, error_type,
                    error_message, record_data, attempt_count)
                   VALUES %s""",
                values
            )
        self.conn.commit()
        logger.warning(f"DLQ: {len(failures)} record in coda")

    def get_pending(
        self,
        pipeline_name: str,
        stage: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """Recupera record non risolti per reprocessing."""
        with self.conn.cursor() as cur:
            if stage:
                cur.execute("""
                    SELECT id, record_data, error_type, attempt_count
                    FROM etl_dead_letter_queue
                    WHERE pipeline_name = %s
                      AND stage = %s
                      AND resolved = FALSE
                    ORDER BY first_failed_at
                    LIMIT %s
                """, (pipeline_name, stage, limit))
            else:
                cur.execute("""
                    SELECT id, record_data, error_type, attempt_count
                    FROM etl_dead_letter_queue
                    WHERE pipeline_name = %s
                      AND resolved = FALSE
                    ORDER BY first_failed_at
                    LIMIT %s
                """, (pipeline_name, limit))
            return [
                {"dlq_id": row[0], "record": row[1],
                 "error_type": row[2], "attempt_count": row[3]}
                for row in cur.fetchall()
            ]

    def mark_resolved(self, dlq_ids: List[int], note: str = ""):
        """Marca record come risolti dopo reprocessing."""
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE etl_dead_letter_queue
                SET resolved = TRUE,
                    resolved_at = NOW(),
                    resolution_note = %s
                WHERE id = ANY(%s)
            """, (note, dlq_ids))
        self.conn.commit()

    def get_error_summary(self, pipeline_name: str) -> List[Dict]:
        """Aggregazione degli errori per tipo."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT error_type,
                       COUNT(*) as count,
                       MAX(last_failed_at) as latest_error,
                       MIN(first_failed_at) as first_error
                FROM etl_dead_letter_queue
                WHERE pipeline_name = %s AND resolved = FALSE
                GROUP BY error_type
                ORDER BY count DESC
            """, (pipeline_name,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
```

---

## Error Classification e Routing

```python
from enum import Enum

class ErrorSeverity(Enum):
    TRANSIENT = "transient"     # Retry
    DATA_QUALITY = "data_quality"  # DLQ
    FATAL = "fatal"             # Abort pipeline
    WARNING = "warning"         # Log e continua


def classify_error(error: Exception) -> ErrorSeverity:
    """Classifica un'eccezione per determinare l'azione appropriata."""
    import psycopg2
    import requests

    # Errori transitori → retry
    transient_types = (
        psycopg2.OperationalError,
        psycopg2.InterfaceError,
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        ConnectionResetError,
        TimeoutError,
    )
    if isinstance(error, transient_types):
        return ErrorSeverity.TRANSIENT

    # Errori di dati → DLQ
    if isinstance(error, (ValueError, TypeError, KeyError, AttributeError)):
        return ErrorSeverity.DATA_QUALITY

    # Violazioni constraint PostgreSQL
    if isinstance(error, psycopg2.errors.ForeignKeyViolation):
        return ErrorSeverity.DATA_QUALITY
    if isinstance(error, psycopg2.errors.UniqueViolation):
        return ErrorSeverity.DATA_QUALITY
    if isinstance(error, psycopg2.errors.NotNullViolation):
        return ErrorSeverity.DATA_QUALITY

    # Errori fatali → abort
    if isinstance(error, (psycopg2.errors.DiskFull, MemoryError, SystemError)):
        return ErrorSeverity.FATAL

    # Default: considera fatale
    return ErrorSeverity.FATAL


class ErrorAwarePipeline:
    """Pipeline con routing intelligente degli errori."""

    def __init__(self, transformer, loader, dlq: DeadLetterQueue,
                 pipeline_name: str, run_id: str,
                 max_error_rate: float = 0.05):
        self.transformer = transformer
        self.loader = loader
        self.dlq = dlq
        self.pipeline_name = pipeline_name
        self.run_id = run_id
        self.max_error_rate = max_error_rate
        self._total = 0
        self._errors = 0

    def _check_error_rate(self):
        """Abort se tasso di errore supera la soglia."""
        if self._total > 100:  # Solo dopo aver visto abbastanza dati
            error_rate = self._errors / self._total
            if error_rate > self.max_error_rate:
                raise RuntimeError(
                    f"Tasso di errore troppo alto: {error_rate:.1%} > {self.max_error_rate:.1%}. "
                    f"Controllare la qualità dei dati sorgente."
                )

    def process_batch(self, records: list):
        self._total += len(records)
        valid_records = []
        dlq_entries = []

        for record in records:
            try:
                transformed = self.transformer.transform_single(record)
                valid_records.append(transformed)
            except Exception as e:
                severity = classify_error(e)
                if severity == ErrorSeverity.FATAL:
                    raise
                elif severity == ErrorSeverity.TRANSIENT:
                    # Retry logic per singolo record
                    try:
                        transformed = retry_once(
                            lambda: self.transformer.transform_single(record)
                        )
                        valid_records.append(transformed)
                    except Exception as e2:
                        self._errors += 1
                        dlq_entries.append(FailedRecord(
                            record=record, error_type=type(e2).__name__,
                            error_message=str(e2), pipeline_name=self.pipeline_name,
                            stage="transform", run_id=self.run_id
                        ))
                elif severity == ErrorSeverity.DATA_QUALITY:
                    self._errors += 1
                    dlq_entries.append(FailedRecord(
                        record=record, error_type=type(e).__name__,
                        error_message=str(e), pipeline_name=self.pipeline_name,
                        stage="transform", run_id=self.run_id
                    ))

        if dlq_entries:
            self.dlq.enqueue_batch(dlq_entries)

        if valid_records:
            try:
                self.loader.load(valid_records)
            except Exception as e:
                severity = classify_error(e)
                if severity == ErrorSeverity.TRANSIENT:
                    time.sleep(5)
                    self.loader.load(valid_records)  # Retry
                else:
                    raise

        self._check_error_rate()
        return {"processed": len(valid_records), "failed": len(dlq_entries)}
```

---

## Circuit Breaker

Il circuit breaker previene che errori ripetuti su una sorgente continuino a consumare risorse:

```python
from enum import Enum
from datetime import datetime, timedelta
import threading

class CircuitState(Enum):
    CLOSED = "closed"       # Normale operazione
    OPEN = "open"           # Blocca richieste
    HALF_OPEN = "half_open" # Test di recovery


class CircuitBreaker:
    """
    Circuit breaker per proteggere chiamate a sorgenti instabili.
    
    Transitions:
    CLOSED → OPEN: dopo failure_threshold errori consecutivi
    OPEN → HALF_OPEN: dopo recovery_timeout secondi
    HALF_OPEN → CLOSED: dopo success in stato half_open
    HALF_OPEN → OPEN: dopo failure in stato half_open
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._lock = threading.Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self._state == CircuitState.OPEN:
                # Controlla se è scaduto il recovery timeout
                if (datetime.utcnow() - self._last_failure_time >
                        timedelta(seconds=self.recovery_timeout)):
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
            return self._state

    def call(self, func, *args, **kwargs):
        state = self.state

        if state == CircuitState.OPEN:
            raise RuntimeError(
                f"Circuit breaker OPEN — sorgente non disponibile. "
                f"Riprovo tra {self.recovery_timeout}s."
            )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        with self._lock:
            self._failure_count = 0
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    logger.info("Circuit breaker: HALF_OPEN → CLOSED")

    def _on_failure(self):
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.utcnow()
            if (self._state in (CircuitState.CLOSED, CircuitState.HALF_OPEN) and
                    self._failure_count >= self.failure_threshold):
                self._state = CircuitState.OPEN
                logger.error(
                    f"Circuit breaker: → OPEN dopo {self._failure_count} errori"
                )
```

---

## Idempotenza e Recovery

```python
def safe_load_with_recovery(
    conn,
    table: str,
    records: list,
    run_id: str
) -> dict:
    """
    Load con recovery automatica:
    1. Controlla se il run_id è già stato processato
    2. Se sì, skip (idempotente)
    3. Se no, carica e registra il run
    """
    with conn.cursor() as cur:
        # Controlla run precedente
        cur.execute("""
            SELECT status, rows_loaded
            FROM etl_run_log
            WHERE run_id = %s AND table_name = %s
        """, (run_id, table))
        existing_run = cur.fetchone()

    if existing_run:
        status, rows = existing_run
        if status == "success":
            logger.info(f"Run {run_id} già completato per {table}: skip")
            return {"skipped": True, "rows_loaded": rows}
        elif status == "running":
            logger.warning(f"Run {run_id} in corso da altro processo: skip")
            return {"skipped": True, "concurrent": True}
        # Se "failed", riprova

    # Registra inizio run
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO etl_run_log (run_id, table_name, status, started_at)
            VALUES (%s, %s, 'running', NOW())
            ON CONFLICT (run_id, table_name) DO UPDATE SET
                status = 'running', started_at = NOW()
        """, (run_id, table))
    conn.commit()

    try:
        # Esegui il caricamento
        rows = bulk_copy_from(conn, table, records)

        # Aggiorna run log come successo
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE etl_run_log
                SET status = 'success', rows_loaded = %s, finished_at = NOW()
                WHERE run_id = %s AND table_name = %s
            """, (rows, run_id, table))
        conn.commit()

        return {"skipped": False, "rows_loaded": rows}

    except Exception as e:
        # Aggiorna run log come fallito
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE etl_run_log
                SET status = 'failed', error_message = %s, finished_at = NOW()
                WHERE run_id = %s AND table_name = %s
            """, (str(e)[:1000], run_id, table))
        conn.commit()
        raise
```

---

## Alerting e Notifiche

```python
from abc import ABC, abstractmethod
from typing import List

class AlertChannel(ABC):
    @abstractmethod
    def send(self, title: str, message: str, severity: str): ...


class SlackAlerter(AlertChannel):
    def __init__(self, webhook_url: str, channel: str):
        self.webhook_url = webhook_url
        self.channel = channel

    def send(self, title: str, message: str, severity: str = "warning"):
        import requests
        color_map = {"critical": "#FF0000", "warning": "#FFA500", "info": "#36A64F"}
        payload = {
            "channel": self.channel,
            "attachments": [{
                "color": color_map.get(severity, "#808080"),
                "title": title,
                "text": message,
                "footer": "ETL Pipeline Monitor",
                "ts": int(datetime.utcnow().timestamp())
            }]
        }
        requests.post(self.webhook_url, json=payload, timeout=10)


class PipelineErrorHandler:
    """Centralizza la gestione errori e notifiche per una pipeline."""

    def __init__(self, alerters: List[AlertChannel], dlq: DeadLetterQueue,
                 pipeline_name: str):
        self.alerters = alerters
        self.dlq = dlq
        self.pipeline_name = pipeline_name

    def handle_fatal(self, error: Exception, context: dict):
        """Gestisce errori fatali: notifica + abort."""
        msg = (f"Pipeline **{self.pipeline_name}** FALLITA\n"
               f"Errore: {type(error).__name__}: {str(error)[:500]}\n"
               f"Contesto: {context}")
        for alerter in self.alerters:
            try:
                alerter.send(
                    title=f"FATAL: {self.pipeline_name}",
                    message=msg,
                    severity="critical"
                )
            except Exception:
                logger.error("Alert delivery failed", exc_info=True)
        raise error

    def handle_high_dlq_rate(self, rate: float, run_id: str):
        """Avvisa se il tasso DLQ supera la soglia."""
        if rate > 0.05:
            summary = self.dlq.get_error_summary(self.pipeline_name)
            msg = (f"Alto tasso di errori DLQ: {rate:.1%}\n"
                   f"Run: {run_id}\n"
                   f"Top errori: {summary[:3]}")
            for alerter in self.alerters:
                alerter.send(
                    title=f"DLQ WARNING: {self.pipeline_name}",
                    message=msg,
                    severity="warning"
                )
```

---

## Schema di Tabella per il Run Log

```sql
CREATE TABLE etl_run_log (
    id              BIGSERIAL PRIMARY KEY,
    run_id          TEXT NOT NULL,
    table_name      TEXT NOT NULL,
    pipeline_name   TEXT,
    status          TEXT NOT NULL CHECK (status IN ('running', 'success', 'failed', 'skipped')),
    rows_extracted  INT DEFAULT 0,
    rows_loaded     INT DEFAULT 0,
    rows_rejected   INT DEFAULT 0,
    error_message   TEXT,
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    finished_at     TIMESTAMPTZ,
    duration_sec    NUMERIC GENERATED ALWAYS AS (
                        EXTRACT(EPOCH FROM (finished_at - started_at))
                    ) STORED,
    UNIQUE (run_id, table_name)
);

-- Query di monitoraggio
SELECT
    pipeline_name,
    status,
    COUNT(*) AS runs,
    AVG(duration_sec) FILTER (WHERE status = 'success') AS avg_duration_sec,
    SUM(rows_loaded) FILTER (WHERE status = 'success') AS total_rows_loaded
FROM etl_run_log
WHERE started_at > NOW() - INTERVAL '7 days'
GROUP BY pipeline_name, status
ORDER BY pipeline_name, status;
```

---

## Checklist per la Gestione Errori

- [ ] Ogni errore transitorio ha la logica di retry con backoff esponenziale
- [ ] Record non processabili finiscono in DLQ, non bloccano la pipeline
- [ ] Il tasso di errore viene monitorato e genera alert sopra soglia
- [ ] I circuit breaker proteggono le sorgenti instabili
- [ ] Ogni run ha un ID univoco e viene loggato in una tabella di audit
- [ ] Le pipeline sono idempotenti — possono essere ri-eseguite senza duplicati
- [ ] Gli errori fatali generano alert immediati ai responsabili
- [ ] Il DLQ ha un processo di review e reprocessing periodico
