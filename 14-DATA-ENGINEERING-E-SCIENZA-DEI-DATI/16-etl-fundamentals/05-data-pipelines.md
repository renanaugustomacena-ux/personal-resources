# Pipeline Dati (Data Pipelines)

Una pipeline dati è un sistema di orchestrazione che connette sorgenti, trasformazioni e destinazioni in un flusso automatizzato, monitorabile e riproducibile. Progettare pipeline robuste richiede di affrontare simultaneamente problemi di affidabilità, scalabilità, osservabilità e manutenibilità.

## Anatomia di una Pipeline

```
┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────┐
│  Source  │ →  │   Extract    │ →  │  Transform   │ →  │   Load   │
│ (DB/API/ │    │ (watermark,  │    │ (clean, enr- │    │ (upsert, │
│  Files)  │    │  CDC, batch) │    │  ich, derive)│    │  COPY)   │
└──────────┘    └──────────────┘    └──────────────┘    └──────────┘
                      │                    │                   │
                      └────────────────────┴───────────────────┘
                                           │
                               ┌───────────────────────┐
                               │   Orchestrator (DAG)  │
                               │   Monitoring + Alerts │
                               │   Error Handling/DLQ  │
                               └───────────────────────┘
```

### Componenti Fondamentali

**Source Connectors** — astraggono il protocollo di accesso alla sorgente (JDBC, REST, Kafka, S3).

**Task Units** — unità atomiche di lavoro con input/output ben definiti, testabili indipendentemente.

**DAG (Directed Acyclic Graph)** — definisce le dipendenze tra task: chi viene prima, chi può girare in parallelo, chi aspetta.

**State Store** — traccia watermarks, checkpoint, run history. Permette il resume dopo failure.

**Dead Letter Queue (DLQ)** — riceve record che non possono essere processati; permette riprocessamento manuale.

**Alerting** — notifica fallimenti, SLA violations, anomalie nei dati.

---

## Pipeline Sincrona vs Asincrona

### Pipeline Sincrona (Batch)

Il processo blocca fino al completamento: extract → transform → load in sequenza. Semplice da ragionare, ideale per ETL notturni.

```python
import logging
from datetime import datetime, date
from typing import Optional

logger = logging.getLogger(__name__)

class BatchPipeline:
    """Pipeline batch sincrona con step sequenziali."""

    def __init__(
        self,
        extractor,
        transformer,
        loader,
        pipeline_name: str
    ):
        self.extractor = extractor
        self.transformer = transformer
        self.loader = loader
        self.name = pipeline_name

    def run(
        self,
        run_date: Optional[date] = None,
        dry_run: bool = False
    ) -> dict:
        run_date = run_date or date.today()
        run_id = f"{self.name}_{run_date.isoformat()}_{datetime.utcnow().strftime('%H%M%S')}"
        
        logger.info(f"Pipeline '{self.name}' avviata — run_id: {run_id}")
        stats = {
            "run_id": run_id,
            "pipeline": self.name,
            "run_date": run_date.isoformat(),
            "started_at": datetime.utcnow().isoformat(),
            "rows_extracted": 0,
            "rows_loaded": 0,
            "status": "running"
        }

        try:
            # Fase 1: Extract
            all_records = []
            for batch in self.extractor.extract(run_date=run_date):
                all_records.extend(batch)
            stats["rows_extracted"] = len(all_records)
            logger.info(f"Estratte {len(all_records)} righe")

            # Fase 2: Transform
            valid_records, errors = self.transformer.transform(all_records)
            stats["rows_rejected"] = len(errors)
            logger.info(f"Trasformate: {len(valid_records)} valide, {len(errors)} scartate")

            # Fase 3: Load
            if not dry_run:
                load_result = self.loader.load(valid_records, run_id=run_id)
                stats["rows_loaded"] = load_result.get("rows_inserted", 0)
            else:
                logger.info(f"DRY RUN: saltato il caricamento di {len(valid_records)} righe")

            stats["status"] = "success"
            stats["finished_at"] = datetime.utcnow().isoformat()

        except Exception as e:
            stats["status"] = "failed"
            stats["error"] = str(e)
            stats["finished_at"] = datetime.utcnow().isoformat()
            logger.error(f"Pipeline '{self.name}' fallita: {e}", exc_info=True)
            raise

        finally:
            self._persist_run_stats(stats)

        return stats

    def _persist_run_stats(self, stats: dict):
        """Salva statistiche del run (log, DB, etc.)."""
        logger.info(f"Run stats: {stats}")
```

### Pipeline Asincrona con Producer/Consumer

```python
import asyncio
import aiohttp
from typing import AsyncIterator, List, Dict, Any

class AsyncPipeline:
    """Pipeline asincrona per alta throughput."""

    def __init__(self, queue_size: int = 1000):
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=queue_size)

    async def producer(
        self,
        urls: List[str],
        session: aiohttp.ClientSession
    ):
        """Produce record dalla sorgente."""
        for url in urls:
            async with session.get(url) as resp:
                data = await resp.json()
                for item in data.get("items", []):
                    await self.queue.put(item)
        
        # Segnala fine produzione
        await self.queue.put(None)

    async def consumer(self, batch_size: int = 100):
        """Consuma e trasforma record dalla queue."""
        batch = []
        while True:
            item = await self.queue.get()
            
            if item is None:  # Segnale di stop
                if batch:
                    yield batch
                break

            batch.append(item)
            if len(batch) >= batch_size:
                yield batch
                batch = []

    async def run(self, urls: List[str], loader):
        async with aiohttp.ClientSession() as session:
            producer_task = asyncio.create_task(
                self.producer(urls, session)
            )
            
            async for batch in self.consumer():
                await loader.load_async(batch)
            
            await producer_task
```

---

## Fan-Out e Fan-In

### Fan-Out: Distribuzione del Lavoro

```python
import concurrent.futures
from typing import List, Callable, Any

def fan_out_extract(
    sources: List[dict],
    extract_fn: Callable,
    max_workers: int = 4
) -> List[Any]:
    """Estrae da più sorgenti in parallelo."""
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(extract_fn, source): source
            for source in sources
        }
        
        for future in concurrent.futures.as_completed(futures):
            source = futures[future]
            try:
                data = future.result()
                results.append(data)
            except Exception as e:
                logger.error(f"Estrazione fallita per {source}: {e}")
                # Continua con le altre sorgenti
    
    return results


# Esempio: estrai da 4 shard di database in parallelo
shards = [
    {"host": "db-shard-1", "shard_id": 1},
    {"host": "db-shard-2", "shard_id": 2},
    {"host": "db-shard-3", "shard_id": 3},
    {"host": "db-shard-4", "shard_id": 4},
]

def extract_from_shard(shard_config: dict) -> list:
    extractor = PostgreSQLExtractor(shard_config["host"])
    records = []
    for batch in extractor.extract_table("orders"):
        records.extend(batch)
    return records

all_data = fan_out_extract(shards, extract_from_shard, max_workers=4)
merged = [record for shard_data in all_data for record in shard_data]
```

### Fan-In: Consolidamento

```python
from itertools import chain
from typing import List, Iterator, Dict, Any

def fan_in_merge(
    source_iterators: List[Iterator],
    dedup_key: str = None
) -> List[Dict[str, Any]]:
    """Consolida dati da più sorgenti con opzionale deduplicazione."""
    merged = list(chain.from_iterable(source_iterators))
    
    if dedup_key:
        seen = {}
        for record in merged:
            key = record.get(dedup_key)
            if key not in seen:
                seen[key] = record
        return list(seen.values())
    
    return merged
```

---

## Checkpoint e Resume

Per pipeline che elaborano terabyte di dati, la capacità di riprendere dall'ultimo checkpoint dopo un fallimento è fondamentale:

```python
import json
import os
from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime

@dataclass
class PipelineCheckpoint:
    pipeline_name: str
    run_date: str
    last_processed_key: Optional[str]  # Es: ultimo customer_id processato
    records_processed: int
    checkpoint_at: str
    status: str  # "running", "completed", "failed"

    def save(self, checkpoint_dir: str):
        path = os.path.join(checkpoint_dir, f"{self.pipeline_name}.json")
        with open(path, "w") as f:
            json.dump(asdict(self), f)

    @classmethod
    def load(cls, checkpoint_dir: str, pipeline_name: str) -> Optional["PipelineCheckpoint"]:
        path = os.path.join(checkpoint_dir, f"{pipeline_name}.json")
        if not os.path.exists(path):
            return None
        with open(path) as f:
            return cls(**json.load(f))


class CheckpointedPipeline:
    """Pipeline con checkpoint per resume dopo failure."""

    def __init__(self, pipeline_name: str, checkpoint_dir: str = "/tmp/checkpoints"):
        self.name = pipeline_name
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(checkpoint_dir, exist_ok=True)

    def run_with_checkpoints(
        self,
        record_iter,
        process_fn,
        key_fn,
        batch_size: int = 1000,
        resume: bool = True
    ):
        checkpoint = PipelineCheckpoint.load(self.checkpoint_dir, self.name)

        if resume and checkpoint and checkpoint.status == "running":
            last_key = checkpoint.last_processed_key
            records_processed = checkpoint.records_processed
            logger.info(f"Riprendo da checkpoint: last_key={last_key}, processed={records_processed}")
        else:
            last_key = None
            records_processed = 0

        batch = []
        skipped = 0

        for record in record_iter:
            key = key_fn(record)

            # Salta record già processati (se resume)
            if last_key and key <= last_key:
                skipped += 1
                continue

            batch.append(record)

            if len(batch) >= batch_size:
                process_fn(batch)
                records_processed += len(batch)
                last_key = key_fn(batch[-1])

                # Aggiorna checkpoint
                cp = PipelineCheckpoint(
                    pipeline_name=self.name,
                    run_date=datetime.utcnow().date().isoformat(),
                    last_processed_key=str(last_key),
                    records_processed=records_processed,
                    checkpoint_at=datetime.utcnow().isoformat(),
                    status="running"
                )
                cp.save(self.checkpoint_dir)
                batch = []

        # Flush ultimo batch
        if batch:
            process_fn(batch)
            records_processed += len(batch)

        # Marca come completato
        cp = PipelineCheckpoint(
            pipeline_name=self.name,
            run_date=datetime.utcnow().date().isoformat(),
            last_processed_key=str(key_fn(batch[-1])) if batch else str(last_key),
            records_processed=records_processed,
            checkpoint_at=datetime.utcnow().isoformat(),
            status="completed"
        )
        cp.save(self.checkpoint_dir)
        logger.info(f"Pipeline completata: {records_processed} record (skippati: {skipped})")
```

---

## Backfill

Il backfill è il riprocessamento di periodi storici, necessario quando si modifica la logica di trasformazione o si corregge un bug:

```python
from datetime import date, timedelta
from typing import List, Optional
import concurrent.futures

def run_backfill(
    pipeline_factory,
    start_date: date,
    end_date: date,
    parallelism: int = 1,
    dry_run: bool = False
) -> List[dict]:
    """
    Esegue backfill da start_date a end_date (inclusi).
    parallelism > 1 per date in parallelo (attenzione ai lock).
    """
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)

    logger.info(f"Backfill: {len(dates)} date da {start_date} a {end_date}")
    results = []

    if parallelism == 1:
        for run_date in dates:
            pipeline = pipeline_factory(run_date)
            result = pipeline.run(run_date=run_date, dry_run=dry_run)
            results.append(result)
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=parallelism) as executor:
            futures = {
                executor.submit(
                    lambda d: pipeline_factory(d).run(run_date=d, dry_run=dry_run),
                    d
                ): d
                for d in dates
            }
            for future in concurrent.futures.as_completed(futures):
                run_date = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"Backfill {run_date}: success")
                except Exception as e:
                    logger.error(f"Backfill {run_date}: FAILED — {e}")
                    results.append({"date": str(run_date), "status": "failed", "error": str(e)})

    success = sum(1 for r in results if r.get("status") == "success")
    failed = len(results) - success
    logger.info(f"Backfill completato: {success} successi, {failed} fallimenti")
    return results
```

---

## Dependency Injection nella Pipeline

Rendere i componenti della pipeline configurabili via dependency injection permette facile testing e swap di componenti:

```python
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

@runtime_checkable
class Extractor(Protocol):
    def extract(self, **kwargs): ...

@runtime_checkable
class Transformer(Protocol):
    def transform(self, records: list) -> tuple: ...

@runtime_checkable
class Loader(Protocol):
    def load(self, records: list, **kwargs) -> dict: ...


@dataclass
class PipelineConfig:
    extractor: Extractor
    transformer: Transformer
    loader: Loader
    pipeline_name: str
    batch_size: int = 10_000
    checkpoint_dir: str = "/tmp/checkpoints"


def build_orders_pipeline(env: str = "production") -> PipelineConfig:
    """Factory function: costruisce la pipeline orders per l'ambiente dato."""
    if env == "production":
        extractor = PostgreSQLExtractor(dsn="postgresql://prod-db/orders")
        loader_conn = psycopg2.connect("postgresql://dw-prod/datawarehouse")
    else:
        extractor = PostgreSQLExtractor(dsn="postgresql://dev-db/orders")
        loader_conn = psycopg2.connect("postgresql://dw-dev/datawarehouse")

    return PipelineConfig(
        extractor=extractor,
        transformer=OrderTransformer(),
        loader=PostgreSQLLoader(loader_conn, table="fact_orders"),
        pipeline_name="orders_etl"
    )
```

---

## Pipeline Testing

```python
import pytest
from unittest.mock import MagicMock, patch

class TestBatchPipeline:
    def test_full_pipeline_success(self):
        # Mock extractor
        extractor = MagicMock()
        extractor.extract.return_value = iter([
            [{"id": 1, "amount": "100.50", "email": "ALICE@TEST.COM"}],
            [{"id": 2, "amount": "200.00", "email": "bob@test.com"}],
        ])

        # Mock transformer
        transformer = MagicMock()
        transformer.transform.return_value = (
            [{"id": 1, "amount": 100.50, "email": "alice@test.com"},
             {"id": 2, "amount": 200.00, "email": "bob@test.com"}],
            []  # no errors
        )

        # Mock loader
        loader = MagicMock()
        loader.load.return_value = {"rows_inserted": 2}

        pipeline = BatchPipeline(extractor, transformer, loader, "test_pipeline")
        result = pipeline.run()

        assert result["status"] == "success"
        assert result["rows_extracted"] == 2
        assert result["rows_loaded"] == 2
        loader.load.assert_called_once()

    def test_pipeline_continues_after_transformer_errors(self):
        extractor = MagicMock()
        extractor.extract.return_value = iter([
            [{"id": 1, "email": "valid@test.com"},
             {"id": 2, "email": "INVALID"},
             {"id": 3, "email": "also@valid.com"}]
        ])

        transformer = MagicMock()
        transformer.transform.return_value = (
            [{"id": 1, "email": "valid@test.com"},
             {"id": 3, "email": "also@valid.com"}],
            [{"record": {"id": 2}, "error": "invalid email"}]  # DLQ
        )

        loader = MagicMock()
        loader.load.return_value = {"rows_inserted": 2}

        pipeline = BatchPipeline(extractor, transformer, loader, "test")
        result = pipeline.run()

        assert result["rows_extracted"] == 3
        assert result["rows_rejected"] == 1
        assert result["rows_loaded"] == 2
```

---

## SLA e Alerting

```python
from datetime import datetime, timedelta
from typing import Optional, Callable
import smtplib
from email.message import EmailMessage

class SLAMonitor:
    """Monitora SLA di pipeline e invia alert in caso di violazione."""

    def __init__(self, smtp_config: dict, alert_recipients: list):
        self.smtp_config = smtp_config
        self.recipients = alert_recipients

    def check_freshness_sla(
        self,
        table: str,
        max_age_hours: int,
        get_last_update_fn: Callable
    ) -> dict:
        """Verifica che la tabella sia stata aggiornata entro max_age_hours."""
        last_update = get_last_update_fn(table)
        age = datetime.utcnow() - last_update
        sla_hours = timedelta(hours=max_age_hours)

        if age > sla_hours:
            self._send_alert(
                subject=f"SLA VIOLATION: {table} non aggiornata",
                body=f"Tabella {table} aggiornata {age} fa (SLA: {max_age_hours}h)"
            )
            return {"status": "violated", "table": table, "age_hours": age.total_seconds() / 3600}

        return {"status": "ok", "table": table, "age_hours": age.total_seconds() / 3600}

    def _send_alert(self, subject: str, body: str):
        msg = EmailMessage()
        msg["Subject"] = f"[DATA PIPELINE ALERT] {subject}"
        msg["From"] = self.smtp_config["from"]
        msg["To"] = ", ".join(self.recipients)
        msg.set_content(body)

        with smtplib.SMTP(self.smtp_config["host"], self.smtp_config["port"]) as smtp:
            smtp.send_message(msg)
```

---

## Best Practice

**Ogni pipeline deve avere un run_id unico** — UUID o `{pipeline}_{date}_{timestamp}`. Fondamentale per debugging e riprocessamento selettivo.

**Separa configurazione dal codice** — connessioni, tabelle target, parametri di scheduling vanno in file di configurazione o variabili d'ambiente, non hardcodati.

**Progetta per il fallimento** — assume che ogni step possa fallire. Ogni step deve essere ripetibile senza side effects extra.

**Testa la pipeline con dati reali** non solo mock — i dati sorgente reali hanno edge case (encoding, null, valori fuori range) che i mock non catturano.

**Dimensiona il batch sulla base della memoria disponibile** — monitorare RSS del processo durante i test di carico; un batch da 500k righe di record complessi può consumare GB.

**Mantieni un catalogo delle pipeline** — chi la possiede, cosa consuma, cosa produce, SLA, frequenza. Senza questa documentazione, ogni pipeline diventa una blackbox.
