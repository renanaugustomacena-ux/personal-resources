# 28 — Temporal.io: Orchestrazione Workflow Durabile

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Tipo:** Documento ufficiale
> **Livello:** advanced
> **Prerequisiti:** Python 3.11+, concetti di microservizi, async/await
> **Versioni di riferimento:** Temporal Python SDK 1.x, Temporal Server 1.24+

---

## Introduzione

Temporal.io è una piattaforma di workflow orchestration che garantisce
**durable execution**: un workflow che inizia, verrà sempre completato —
anche se il server si riavvia, il processo crasha, o la rete cade.

A differenza di Celery, Airflow, o n8n, Temporal non "esegue" il workflow:
**registra la storia di ogni workflow su un event log persistente**,
permettendo al worker di riprendere dall'esatto punto in cui si era fermato.

---

## 1. Concetti Fondamentali

### 1.1 Terminologia

```
TEMPORAL CONCEPTS:
                                                                       
  Workflow     → funzione Python decorata con @workflow.defn           
                 Definisce la logica di orchestrazione (NO I/O diretto)
                                                                       
  Activity     → funzione Python decorata con @activity.defn           
                 Esegue I/O reale: chiamate API, DB, file system       
                                                                       
  Worker       → processo che esegue workflow e activity               
                 Si connette al Temporal Server via gRPC               
                                                                       
  Temporal Server → gestisce stato workflow, code, timer, retry       
                    Può essere self-hosted (Docker) o cloud (Temporal Cloud)
                                                                       
  Task Queue   → coda logica che connette Client → Worker             
                 Nomi: "ordini-queue", "email-queue", etc.            
                                                                       
  WorkflowId   → identità univoca di un'istanza workflow               
                 Idempotency key: se riavvii con stesso ID = stesso WF
                                                                       
  RunId        → identità di una specifica esecuzione del workflow     
                 Cambia ad ogni retry del workflow (non dell'activity) 
```

### 1.2 Event History (il cuore di Temporal)

```
Ogni workflow ha una Event History immutabile:

  Event #1: WorkflowExecutionStarted
  Event #2: ActivityTaskScheduled (activity: "verifica_pagamento")
  Event #3: ActivityTaskStarted
  Event #4: ActivityTaskCompleted (result: {"pagato": true})
  Event #5: ActivityTaskScheduled (activity: "aggiorna_inventario")
  ...

Se il worker crasha dopo Event #4 e prima di completare Event #5:
  → Al restart, Temporal replay la history
  → Il worker ri-esegue la funzione Python
  → Le Activity già completate NON vengono rieseguite (result dalla history)
  → L'esecuzione riprende dall'Activity non completata

CONSEGUENZA CRITICA:
  Il codice del Workflow (non delle Activity) deve essere DETERMINISTICO.
  No: datetime.now(), random.random(), asyncio.sleep() diretti
  Sì: workflow.now(), workflow.random(), await asyncio.sleep() Temporal-aware
```

---

## 2. Setup Ambiente

### 2.1 Temporal Server via Docker Compose

```yaml
# docker-compose-temporal.yml
version: "3.8"

services:
  postgresql:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: temporal
      POSTGRES_USER: temporal
      POSTGRES_DB: temporal
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U temporal"]
      interval: 10s
      timeout: 5s
      retries: 5

  temporal:
    image: temporalio/auto-setup:1.24
    depends_on:
      postgresql:
        condition: service_healthy
    environment:
      DB: postgresql
      DB_PORT: 5432
      POSTGRES_USER: temporal
      POSTGRES_PWD: temporal
      POSTGRES_SEEDS: postgresql
    ports:
      - "7233:7233"  # gRPC API
    healthcheck:
      test: ["CMD", "tctl", "--address", "temporal:7233", "workflow", "list"]
      interval: 10s
      retries: 5

  temporal-ui:
    image: temporalio/ui:2.26
    depends_on:
      - temporal
    environment:
      TEMPORAL_ADDRESS: temporal:7233
    ports:
      - "8080:8080"  # Web UI

  temporal-admin-tools:
    image: temporalio/admin-tools:1.24
    depends_on:
      - temporal
    stdin_open: true
    tty: true
    environment:
      TEMPORAL_ADDRESS: temporal:7233
```

```bash
# Installazione SDK Python
pip install temporalio

# Avvio server
docker compose -f docker-compose-temporal.yml up -d

# Verifica
docker exec temporal-admin-tools tctl namespace list
# Deve mostrare il namespace "default"

# Web UI
open http://localhost:8080
```

---

## 3. Primo Workflow Python

### 3.1 Activity e Workflow

```python
# temporal_demo/activities.py
import asyncio
import httpx
import structlog
from temporalio import activity

log = structlog.get_logger()

@activity.defn
async def verifica_pagamento(ordine_id: str) -> dict:
    """Activity: chiama gateway pagamenti. Può essere ritentata senza problemi."""
    log.info("verifica_pagamento_avviata", ordine_id=ordine_id)
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"https://api.gateway.it/payments/{ordine_id}")
        resp.raise_for_status()
        return resp.json()

@activity.defn
async def aggiorna_inventario(sku: str, quantita: int) -> bool:
    """Activity: decrementa stock. Idempotente grazie a ordine_id come chiave."""
    log.info("aggiorna_inventario", sku=sku, quantita=quantita)
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.patch(
            f"https://api.magazzino.it/stock/{sku}",
            json={"decremento": quantita, "idempotency_key": f"ord-{sku}"},
        )
        return resp.status_code == 200

@activity.defn
async def invia_email_conferma(email: str, ordine_id: str, num_conferma: str) -> None:
    """Activity: invia email. Log se l'email è già stata inviata (idempotenza)."""
    log.info("email_conferma_inviata", email=email, ordine_id=ordine_id)
    # Implementa invio effettivo via SMTP/SendGrid
```

```python
# temporal_demo/workflow.py
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

# Importa activities tramite proxy (non import diretto — evita esecuzione locale)
with workflow.unsafe.imports_passed_through():
    from temporal_demo.activities import (
        verifica_pagamento, aggiorna_inventario, invia_email_conferma
    )

@workflow.defn
class OrdineWorkflow:
    """
    Workflow durabile per elaborazione ordine.
    Sopravvive a crash del worker, timeout rete, riavvii del server.
    """

    @workflow.run
    async def run(self, payload: dict) -> dict:
        ordine_id: str = payload["ordine_id"]
        workflow.logger.info("ordine_avviato", ordine_id=ordine_id)

        # STEP 1: Verifica pagamento
        # RetryPolicy: 3 tentativi, backoff esponenziale, max 5 minuti tra tentativi
        retry_api = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3,
        )
        pagamento = await workflow.execute_activity(
            verifica_pagamento,
            ordine_id,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=retry_api,
        )
        if not pagamento.get("pagato"):
            return {"stato": "pagamento_fallito", "ordine_id": ordine_id}

        # STEP 2: Aggiorna inventario per ogni prodotto
        prodotti = payload.get("prodotti", [])
        for prodotto in prodotti:
            ok = await workflow.execute_activity(
                aggiorna_inventario,
                prodotto["sku"],
                prodotto["quantita"],
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=retry_api,
            )
            if not ok:
                workflow.logger.warning("stock_update_fallito", sku=prodotto["sku"])

        # STEP 3: Invia email conferma
        await workflow.execute_activity(
            invia_email_conferma,
            payload["cliente_email"],
            ordine_id,
            pagamento.get("numero_conferma", "N/A"),
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(maximum_attempts=5),
        )

        workflow.logger.info("ordine_completato", ordine_id=ordine_id)
        return {"stato": "completato", "ordine_id": ordine_id, "pagamento": pagamento}
```

### 3.2 Worker e Client

```python
# temporal_demo/worker.py
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from temporal_demo.activities import verifica_pagamento, aggiorna_inventario, invia_email_conferma
from temporal_demo.workflow import OrdineWorkflow

async def avvia_worker() -> None:
    client = await Client.connect("localhost:7233")
    worker = Worker(
        client,
        task_queue="ordini-queue",
        workflows=[OrdineWorkflow],
        activities=[verifica_pagamento, aggiorna_inventario, invia_email_conferma],
    )
    print("Worker avviato — in ascolto su 'ordini-queue'")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(avvia_worker())
```

```python
# temporal_demo/client_submit.py
import asyncio
from temporalio.client import Client
from temporal_demo.workflow import OrdineWorkflow

async def invia_ordine(payload: dict) -> dict:
    client = await Client.connect("localhost:7233")
    # WorkflowId = idempotency key: se inviato due volte con stesso ID → workflow deduplicato
    handle = await client.start_workflow(
        OrdineWorkflow.run,
        payload,
        id=f"ordine-{payload['ordine_id']}",
        task_queue="ordini-queue",
    )
    print(f"Workflow avviato: {handle.id} (run_id: {handle.first_execution_run_id})")
    risultato = await handle.result()
    return risultato

if __name__ == "__main__":
    payload = {
        "ordine_id": "ORD-2026-001",
        "cliente_email": "mario@test.it",
        "prodotti": [{"sku": "SKU-001", "quantita": 2}],
    }
    result = asyncio.run(invia_ordine(payload))
    print(f"Risultato: {result}")
```

---

## 4. Pattern Avanzati

### 4.1 Signal — Comunicazione Asincrona con Workflow Attivo

```python
@workflow.defn
class OrdineConApprovazioneWorkflow:
    """Workflow che attende approvazione esterna prima di procedere."""

    def __init__(self) -> None:
        self._approvato: bool | None = None
        self._motivo_rifiuto: str = ""

    @workflow.signal
    async def approva(self, approvatore: str) -> None:
        """Signal: inviato dall'esterno per approvare il workflow."""
        workflow.logger.info("workflow_approvato", approvatore=approvatore)
        self._approvato = True

    @workflow.signal
    async def rifiuta(self, approvatore: str, motivo: str) -> None:
        """Signal: inviato dall'esterno per rifiutare il workflow."""
        workflow.logger.info("workflow_rifiutato", approvatore=approvatore, motivo=motivo)
        self._approvato = False
        self._motivo_rifiuto = motivo

    @workflow.run
    async def run(self, ordine_id: str) -> dict:
        # Notifica approvatori (activity)
        await workflow.execute_activity(
            "invia_notifica_approvazione",
            ordine_id,
            start_to_close_timeout=timedelta(minutes=1),
        )
        # Attendi signal (con timeout 48 ore)
        await workflow.wait_condition(
            lambda: self._approvato is not None,
            timeout=timedelta(hours=48),
        )
        if self._approvato is None:
            return {"stato": "timeout_approvazione", "ordine_id": ordine_id}
        if not self._approvato:
            return {"stato": "rifiutato", "motivo": self._motivo_rifiuto}
        # Procedi con l'ordine...
        return {"stato": "approvato_ed_elaborato", "ordine_id": ordine_id}
```

```python
# Inviare un signal a un workflow attivo
async def approva_ordine(ordine_id: str, approvatore: str) -> None:
    client = await Client.connect("localhost:7233")
    handle = client.get_workflow_handle(f"ordine-{ordine_id}")
    await handle.signal(OrdineConApprovazioneWorkflow.approva, approvatore)
```

### 4.2 Query — Leggere Stato Senza Modificarlo

```python
@workflow.defn
class OrdineConStatusWorkflow:
    def __init__(self) -> None:
        self._step_corrente: str = "inizializzazione"
        self._progressi: list[str] = []

    @workflow.query
    def stato_corrente(self) -> dict:
        """Query: lettura dello stato senza effetti collaterali."""
        return {"step": self._step_corrente, "progressi": self._progressi}

    @workflow.run
    async def run(self, ordine_id: str) -> dict:
        self._step_corrente = "verifica_pagamento"
        self._progressi.append("Verifica pagamento avviata")
        # ... activity ...
        self._step_corrente = "aggiornamento_inventario"
        self._progressi.append("Stock aggiornato")
        return {"stato": "completato"}

# Leggere lo stato dall'esterno
async def leggi_stato(ordine_id: str) -> dict:
    client = await Client.connect("localhost:7233")
    handle = client.get_workflow_handle(f"ordine-{ordine_id}")
    return await handle.query(OrdineConStatusWorkflow.stato_corrente)
```

### 4.3 Child Workflow e Fan-Out

```python
@workflow.defn
class BatchOrdiniWorkflow:
    """Workflow genitore che spawna child workflow per ogni ordine."""

    @workflow.run
    async def run(self, ordini_ids: list[str]) -> dict:
        # Esegui tutti gli ordini in parallelo (fan-out)
        handles = []
        for ordine_id in ordini_ids:
            handle = await workflow.start_child_workflow(
                OrdineWorkflow.run,
                {"ordine_id": ordine_id},
                id=f"ordine-{ordine_id}",
                task_queue="ordini-queue",
            )
            handles.append(handle)

        # Attendi tutti i child workflow
        risultati = await asyncio.gather(*[h.result() for h in handles])
        completati = sum(1 for r in risultati if r.get("stato") == "completato")
        return {
            "totale": len(ordini_ids),
            "completati": completati,
            "falliti": len(ordini_ids) - completati,
        }
```

---

## 5. Temporal vs Alternative

| Feature | Temporal | Celery | Airflow | n8n |
|---------|---------|--------|---------|-----|
| Durable execution | ✅ Nativo | ❌ No | ❌ No | ❌ No |
| Replay/recovery | ✅ Automatico | ❌ Manuale | ❌ Parziale | ❌ No |
| Long-running (giorni/mesi) | ✅ Sì | ⚠ Difficile | ⚠ Limitato | ❌ No |
| Signal/Query | ✅ Sì | ❌ No | ❌ No | ❌ No |
| Visual monitoring | ✅ UI nativa | ⚠ Flower | ✅ Sì | ✅ Sì |
| Curva apprendimento | Alta | Media | Media | Bassa |
| Uso PMI | Casi avanzati | Batch task | Data pipeline | Automazione visual |

**Quando usare Temporal:**
- Processi business che durano ore, giorni, o mesi (approvazioni, onboarding)
- Workflow che devono garantire "exactly-once" completion anche in caso di crash
- Saga patterns per transazioni distribuite con compensazione
- Processi con wait su eventi esterni (firma contratto, conferma pagamento)

**Quando NON usare Temporal:**
- Task semplici, veloci, senza dipendenze tra step → usa Celery o script Python
- Workflow visivi per utenti non tecnici → usa n8n o Make
- Pipeline batch periodiche → usa Airflow o APScheduler

---

## 6. Monitoring e Osservabilità

```python
# Metrics Temporal integrate con Prometheus
# Nel docker-compose, aggiungere al servizio temporal:
# ports:
#   - "9090:9090"  # metrics endpoint

# Metriche chiave Temporal:
# temporal_request_latency        → latenza chiamate gRPC
# temporal_workflow_task_latency  → latenza elaborazione task workflow  
# temporal_activity_task_latency  → latenza elaborazione task activity
# temporal_workflow_active_count  → workflow attivi in questo momento
# temporal_workflow_failed_count  → workflow falliti (non retriabili)

# Dashboard Grafana: usa il template ufficiale Temporal
# https://grafana.com/grafana/dashboards/15500

# Log strutturato nel workflow:
@workflow.defn
class WorkflowConLog:
    @workflow.run
    async def run(self, payload: dict) -> None:
        workflow.logger.info("step_avviato",
                             workflow_id=workflow.info().workflow_id,
                             run_id=workflow.info().run_id,
                             payload_size=len(str(payload)))
```

---

## Riferimenti

- Temporal Python SDK: https://python.temporal.io/
- Temporal Server docs: https://docs.temporal.io/
- Temporal UI: https://github.com/temporalio/ui
- Temporal Samples Python: https://github.com/temporalio/samples-python
- Saga Pattern in Temporal: https://docs.temporal.io/encyclopedia/workflow-message-passing
