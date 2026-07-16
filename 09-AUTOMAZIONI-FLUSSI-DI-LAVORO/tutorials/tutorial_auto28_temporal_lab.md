# Tutorial Lab — Temporal.io: Workflow Durabili con Python SDK

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `28-temporal-workflow-orchestration.md`
> **Livello:** advanced
> **Tempo stimato:** 3.5 ore
> **Prerequisiti:** Python 3.11+, asyncio, Docker Compose, concetti microservizi
> **Versioni di riferimento:** Temporal Python SDK 1.x, Temporal Server 1.24+

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Avviare Temporal Server in locale con Docker Compose
2. Definire Activity e Workflow con il Python SDK
3. Avviare, monitorare e gestire workflow dalla Web UI
4. Implementare Signal, Query e Child Workflow
5. Configurare RetryPolicy personalizzata per le Activity
6. Costruire un Saga Pattern per transazioni distribuite con compensazione
7. Debuggare workflow tramite Temporal Web UI e trace

---

## Lab Environment Setup

```bash
# 1. Avvio Temporal Server (PostgreSQL backend)
# Salva come docker-compose-temporal.yml

# 2. Avvio
docker compose -f docker-compose-temporal.yml up -d

# 3. Verifica (dopo ~30 secondi)
docker compose -f docker-compose-temporal.yml ps
# tutti i servizi devono essere "Up"

# 4. Apri Web UI
# http://localhost:8080

# 5. Installa SDK Python
pip install temporalio structlog

# 6. Verifica connessione
python -c "
import asyncio
from temporalio.client import Client

async def test():
    client = await Client.connect('localhost:7233')
    print(f'Connesso a Temporal: {client.identity}')

asyncio.run(test())
"

# SCRIPT VERIFICA PREREQUISITI COMPLETO
python - <<'EOF'
import asyncio, sys

async def main():
    errori = []
    try:
        from temporalio.client import Client
        client = await Client.connect("localhost:7233", target_host="localhost:7233")
        print("✅ Temporal Server: OK")
    except Exception as e:
        errori.append(f"❌ Temporal Server non raggiungibile: {e}")
        print(f"   Controlla: docker compose -f docker-compose-temporal.yml up -d")
    
    try:
        import structlog
        print("✅ structlog: OK")
    except ImportError:
        errori.append("❌ structlog mancante: pip install structlog")
    
    if errori:
        for e in errori:
            print(e)
        sys.exit(1)
    print("\n✅ Tutti i prerequisiti soddisfatti")

asyncio.run(main())
EOF
```

---

## Analogia Introduttiva

> **Temporal è come un notaio per i tuoi workflow**:
> ogni step di un processo viene registrato e notarizzato nell'event log.
> Se l'esecutore (worker) viene colpito da un fulmine mentre firma i documenti,
> il notaio sa esattamente a che punto era arrivato e un nuovo esecutore
> può riprendere dall'ultimo documento firmato, non da capo.
>
> Questo è il concetto di **durable execution**:
> il workflow *deve* completarsi, indipendentemente da guasti tecnici.
>
> La differenza con Celery/n8n/cron:
> - Cron: se il server crasha durante il job, il job viene perso
> - Celery: retry possibile, ma devi gestirlo manualmente con ack
> - Temporal: il workflow riprende *automaticamente* dall'esatto punto di interruzione

---

## Architettura del Lab

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TEMPORAL LAB ARCHITECTURE                         │
│                                                                       │
│  ┌─────────────────┐    gRPC     ┌──────────────────────────────┐  │
│  │  Python Client  │ ──────────► │      Temporal Server          │  │
│  │  (start_wf.py) │             │   ┌──────────┐ ┌─────────┐   │  │
│  └─────────────────┘             │   │Workflow  │ │Activity │   │  │
│                                  │   │ Service  │ │ Service │   │  │
│  ┌─────────────────┐             │   └──────────┘ └─────────┘   │  │
│  │  Python Worker  │ ◄────────── │                              │  │
│  │  (worker.py)   │    pull      │   ┌──────────┐               │  │
│  │  - Workflow fn  │             │   │PostgreSQL│               │  │
│  │  - Activity fn  │             │   │(history) │               │  │
│  └─────────────────┘             │   └──────────┘               │  │
│                                  └──────────────────────────────┘  │
│                                           │                          │
│                                    ┌──────▼──────┐                  │
│                                    │ Temporal UI  │                  │
│                                    │ :8080        │                  │
│                                    └─────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## PART A — Primo Workflow Durabile

### A1 — Activity e Workflow di Base

```python
# temporal_lab/activities.py
import asyncio
import random
from datetime import datetime

import structlog
from temporalio import activity

log = structlog.get_logger()

@activity.defn
async def recupera_dati_cliente(cliente_id: str) -> dict:
    """
    Simula chiamata API esterna per recuperare dati cliente.
    Con ritardi e fallimenti casuali per testare il retry.
    """
    logger = activity.logger
    logger.info("recupero_dati_cliente", cliente_id=cliente_id)
    await asyncio.sleep(0.5)  # simula latenza di rete
    if random.random() < 0.2:  # 20% di fallimento per test retry
        raise RuntimeError(f"API temporaneamente non disponibile per {cliente_id}")
    return {
        "id": cliente_id,
        "nome": "Mario Rossi",
        "email": "mario@azienda.it",
        "piano": "pro",
        "credito": 1500.00,
    }

@activity.defn
async def processa_ordine(ordine_id: str, cliente: dict, prodotti: list) -> dict:
    """Processa l'ordine: verifica stock, calcola totale, etc."""
    logger = activity.logger
    logger.info("processamento_ordine", ordine_id=ordine_id)
    await asyncio.sleep(0.3)
    totale = sum(p.get("prezzo", 0) * p.get("quantita", 1) for p in prodotti)
    if totale > cliente.get("credito", 0):
        raise ValueError(f"Credito insufficiente: {totale} > {cliente['credito']}")
    return {
        "ordine_id": ordine_id,
        "stato": "processato",
        "totale": totale,
        "processato_at": datetime.utcnow().isoformat(),
    }

@activity.defn
async def invia_conferma_email(email: str, ordine: dict) -> bool:
    """Invia email di conferma ordine."""
    logger = activity.logger
    logger.info("email_conferma", email=email, ordine_id=ordine["ordine_id"])
    await asyncio.sleep(0.2)
    print(f"[EMAIL SIMULATA] → {email}: Ordine {ordine['ordine_id']} confermato, totale €{ordine['totale']}")
    return True

@activity.defn
async def annulla_ordine(ordine_id: str, motivo: str) -> None:
    """Activity di compensazione (usata nel Saga pattern)."""
    logger = activity.logger
    logger.info("annullo_ordine_compensazione", ordine_id=ordine_id, motivo=motivo)
    await asyncio.sleep(0.1)
    print(f"[SAGA COMPENSAZIONE] Ordine {ordine_id} annullato: {motivo}")
```

```python
# temporal_lab/workflow_ordine.py
from datetime import timedelta

import structlog
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from temporal_lab.activities import (
        recupera_dati_cliente, processa_ordine,
        invia_conferma_email, annulla_ordine,
    )

@workflow.defn
class OrdineWorkflow:
    """
    Workflow durabile per elaborazione ordine.
    Sopravvive a: crash worker, timeout rete, riavvii server.
    """

    @workflow.run
    async def run(self, payload: dict) -> dict:
        ordine_id: str = payload["ordine_id"]
        cliente_id: str = payload["cliente_id"]
        prodotti: list = payload.get("prodotti", [])

        workflow.logger.info("ordine_workflow_avviato", ordine_id=ordine_id)

        # Policy retry con backoff esponenziale
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=5,
            non_retryable_error_types=["ValueError"],  # errori logici: no retry
        )

        # Step 1: Recupera dati cliente (può fallire → retry automatico)
        try:
            cliente = await workflow.execute_activity(
                recupera_dati_cliente,
                cliente_id,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy,
            )
        except Exception as e:
            workflow.logger.error("cliente_non_recuperabile", errore=str(e))
            return {"stato": "fallito", "motivo": f"Cliente non trovato: {e}"}

        # Step 2: Processa ordine
        ordine_processato = None
        try:
            ordine_processato = await workflow.execute_activity(
                processa_ordine,
                ordine_id,
                cliente,
                prodotti,
                start_to_close_timeout=timedelta(seconds=20),
                retry_policy=retry_policy,
            )
        except ValueError as e:
            # Errore logico (credito insufficiente) → no retry
            workflow.logger.warning("ordine_rifiutato", motivo=str(e))
            return {"stato": "rifiutato", "motivo": str(e)}

        # Step 3: Invia email conferma
        await workflow.execute_activity(
            invia_conferma_email,
            cliente["email"],
            ordine_processato,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=RetryPolicy(maximum_attempts=5),
        )

        workflow.logger.info("ordine_completato", ordine_id=ordine_id,
                             totale=ordine_processato["totale"])
        return {
            "stato": "completato",
            "ordine_id": ordine_id,
            "totale": ordine_processato["totale"],
        }
```

### A2 — Worker e Client

```python
# temporal_lab/worker.py
import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from temporal_lab.activities import (
    recupera_dati_cliente, processa_ordine,
    invia_conferma_email, annulla_ordine,
)
from temporal_lab.workflow_ordine import OrdineWorkflow

TASK_QUEUE = "ordini-lab-queue"

async def avvia_worker() -> None:
    client = await Client.connect("localhost:7233")
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[OrdineWorkflow],
        activities=[
            recupera_dati_cliente, processa_ordine,
            invia_conferma_email, annulla_ordine,
        ],
    )
    print(f"Worker avviato — task queue: '{TASK_QUEUE}'")
    print("Apri http://localhost:8080 per monitorare i workflow")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(avvia_worker())
```

```python
# temporal_lab/invia_ordine.py
import asyncio
from temporalio.client import Client
from temporal_lab.workflow_ordine import OrdineWorkflow

TASK_QUEUE = "ordini-lab-queue"

async def invia_ordine(ordine_id: str, cliente_id: str, prodotti: list) -> dict:
    client = await Client.connect("localhost:7233")
    payload = {"ordine_id": ordine_id, "cliente_id": cliente_id, "prodotti": prodotti}
    # WorkflowId = chiave idempotency: inviare due volte lo stesso ID → stessa esecuzione
    handle = await client.start_workflow(
        OrdineWorkflow.run,
        payload,
        id=f"ordine-{ordine_id}",
        task_queue=TASK_QUEUE,
    )
    print(f"Workflow avviato: {handle.id}")
    print(f"Monitorare su: http://localhost:8080/namespaces/default/workflows/{handle.id}")
    risultato = await handle.result()
    return risultato

if __name__ == "__main__":
    prodotti_test = [
        {"nome": "Laptop Pro", "sku": "LAP-001", "quantita": 1, "prezzo": 1200.00},
        {"nome": "Mouse USB", "sku": "MOU-001", "quantita": 2, "prezzo": 25.00},
    ]
    risultato = asyncio.run(invia_ordine("ORD-2026-TEST-001", "CLT-001", prodotti_test))
    print(f"Risultato: {risultato}")
```

---

## PART B — Signal e Query

### B1 — Workflow con Approvazione via Signal

```python
# temporal_lab/workflow_approvazione.py
import asyncio
from datetime import timedelta
from typing import Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from temporal_lab.activities import invia_conferma_email, annulla_ordine

@workflow.defn
class OrdineConApprovazioneWorkflow:
    """
    Workflow con gate di approvazione esterna.
    Attende un Signal prima di procedere.
    """

    def __init__(self) -> None:
        self._approvato: Optional[bool] = None
        self._approvatore: str = ""
        self._motivo_rifiuto: str = ""
        self._step_corrente: str = "iniziato"

    @workflow.signal
    async def approva(self, approvatore: str) -> None:
        """Signal: inviato dall'esterno per approvare."""
        workflow.logger.info("signal_approvazione", approvatore=approvatore)
        self._approvato = True
        self._approvatore = approvatore

    @workflow.signal
    async def rifiuta(self, approvatore: str, motivo: str) -> None:
        """Signal: inviato dall'esterno per rifiutare."""
        workflow.logger.info("signal_rifiuto", approvatore=approvatore, motivo=motivo)
        self._approvato = False
        self._approvatore = approvatore
        self._motivo_rifiuto = motivo

    @workflow.query
    def stato(self) -> dict:
        """Query: legge lo stato corrente del workflow (senza modificarlo)."""
        return {
            "step": self._step_corrente,
            "approvato": self._approvato,
            "approvatore": self._approvatore,
        }

    @workflow.run
    async def run(self, payload: dict) -> dict:
        ordine_id: str = payload["ordine_id"]
        self._step_corrente = "in_attesa_approvazione"

        workflow.logger.info("in_attesa_approvazione", ordine_id=ordine_id)

        # Attendi signal con timeout 48 ore
        try:
            await workflow.wait_condition(
                lambda: self._approvato is not None,
                timeout=timedelta(hours=48),
            )
        except asyncio.TimeoutError:
            self._step_corrente = "timeout"
            return {"stato": "scaduto", "ordine_id": ordine_id}

        if not self._approvato:
            self._step_corrente = "rifiutato"
            await workflow.execute_activity(
                annulla_ordine, ordine_id, self._motivo_rifiuto,
                start_to_close_timeout=timedelta(seconds=10),
            )
            return {
                "stato": "rifiutato",
                "motivo": self._motivo_rifiuto,
                "approvatore": self._approvatore,
            }

        self._step_corrente = "approvato_in_elaborazione"
        await workflow.execute_activity(
            invia_conferma_email,
            payload.get("email", ""),
            {"ordine_id": ordine_id, "totale": payload.get("totale", 0)},
            start_to_close_timeout=timedelta(minutes=2),
        )
        self._step_corrente = "completato"
        return {
            "stato": "approvato",
            "approvatore": self._approvatore,
            "ordine_id": ordine_id,
        }
```

```python
# temporal_lab/gestisci_approvazione.py
"""CLI per inviare Signal a workflow attivi."""
import asyncio
import sys
from temporalio.client import Client
from temporal_lab.workflow_approvazione import OrdineConApprovazioneWorkflow

async def approva(ordine_id: str, approvatore: str) -> None:
    client = await Client.connect("localhost:7233")
    handle = client.get_workflow_handle(f"ordine-approv-{ordine_id}")
    await handle.signal(OrdineConApprovazioneWorkflow.approva, approvatore)
    stato = await handle.query(OrdineConApprovazioneWorkflow.stato)
    print(f"Signal inviato. Stato corrente: {stato}")

async def rifiuta(ordine_id: str, approvatore: str, motivo: str) -> None:
    client = await Client.connect("localhost:7233")
    handle = client.get_workflow_handle(f"ordine-approv-{ordine_id}")
    await handle.signal(OrdineConApprovazioneWorkflow.rifiuta, approvatore, motivo)
    print(f"Ordine {ordine_id} rifiutato da {approvatore}")

async def leggi_stato(ordine_id: str) -> dict:
    client = await Client.connect("localhost:7233")
    handle = client.get_workflow_handle(f"ordine-approv-{ordine_id}")
    return await handle.query(OrdineConApprovazioneWorkflow.stato)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python gestisci_approvazione.py <approva|rifiuta|stato> <ordine_id> [approvatore] [motivo]")
        sys.exit(1)
    azione, ordine_id = sys.argv[1], sys.argv[2]
    if azione == "approva":
        asyncio.run(approva(ordine_id, sys.argv[3] if len(sys.argv) > 3 else "admin"))
    elif azione == "rifiuta":
        asyncio.run(rifiuta(ordine_id, sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else "Rifiuto senza motivo"))
    elif azione == "stato":
        stato = asyncio.run(leggi_stato(ordine_id))
        print(f"Stato ordine {ordine_id}: {stato}")
```

---

## PART C — Saga Pattern

### C1 — Transazione Distribuita con Compensazione

```python
# temporal_lab/workflow_saga.py
"""
Saga Pattern: sequenza di step con compensazione in caso di fallimento.
Se lo step 3 fallisce, vengono eseguiti gli "undo" degli step 1 e 2.
"""
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from temporal_lab.activities import (
        recupera_dati_cliente, processa_ordine,
        invia_conferma_email, annulla_ordine,
    )

@workflow.defn
class OrdineWorkflowSaga:
    """
    Implementa il Saga Pattern per garantire consistenza distribuita.
    Ogni step forward ha un corrispondente step di compensazione.
    """

    @workflow.run
    async def run(self, payload: dict) -> dict:
        ordine_id = payload["ordine_id"]
        cliente_id = payload["cliente_id"]
        retry = RetryPolicy(
            maximum_attempts=3,
            non_retryable_error_types=["ValueError"],
        )
        compensazioni_da_eseguire: list[tuple] = []

        try:
            # STEP 1: Recupera cliente
            cliente = await workflow.execute_activity(
                recupera_dati_cliente, cliente_id,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry,
            )
            # Registra compensazione per step 1 (in questo caso nulla da annullare)

            # STEP 2: Processa ordine
            ordine = await workflow.execute_activity(
                processa_ordine, ordine_id, cliente, payload.get("prodotti", []),
                start_to_close_timeout=timedelta(seconds=20),
                retry_policy=retry,
            )
            # Registra compensazione per step 2
            compensazioni_da_eseguire.append(
                (annulla_ordine, ordine_id, "rollback saga")
            )

            # STEP 3: Invia email (può fallire — scatena compensazione)
            await workflow.execute_activity(
                invia_conferma_email, cliente["email"], ordine,
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry,
            )

            return {"stato": "completato", "ordine_id": ordine_id}

        except Exception as e:
            workflow.logger.error("saga_errore", step="forward", errore=str(e))
            # Esegui compensazioni in ordine inverso
            for attivita, *args in reversed(compensazioni_da_eseguire):
                try:
                    await workflow.execute_activity(
                        attivita, *args,
                        start_to_close_timeout=timedelta(seconds=30),
                        retry_policy=RetryPolicy(maximum_attempts=5),
                    )
                    workflow.logger.info("compensazione_eseguita",
                                         attivita=attivita.__name__)
                except Exception as comp_e:
                    workflow.logger.error("compensazione_fallita",
                                          attivita=attivita.__name__,
                                          errore=str(comp_e))
            return {"stato": "rollback_completato", "motivo": str(e)}
```

---

## Esercizi

### Esercizio 1 — Test Durabilità (20 min)

1. Avvia il worker: `python temporal_lab/worker.py`
2. Invia un ordine: `python temporal_lab/invia_ordine.py`
3. **Mentre il workflow è in esecuzione**: ferma il worker (Ctrl+C)
4. Osserva in Web UI: il workflow mostra stato "Running" ma è bloccato
5. Riavvia il worker: `python temporal_lab/worker.py`
6. Osserva: il workflow riprende automaticamente dall'ultimo step completato
7. Verifica il risultato finale

### Esercizio 2 — Approvazione Multi-Step (40 min)

1. Avvia un workflow `OrdineConApprovazioneWorkflow`
2. Leggi lo stato con `python gestisci_approvazione.py stato ORD-001`
3. Invia signal di approvazione: `python gestisci_approvazione.py approva ORD-001 mario@azienda.it`
4. Verifica nella Web UI: controlla l'event history del workflow
5. Implementa un reminder: aggiungi activity `invia_reminder_approvazione()` che viene chiamata dopo 24 ore se nessun signal è arrivato

### Esercizio 3 — Monitoring Dashboard (25 min)

Scrivi `monitor_workflows.py` che ogni 30 secondi:
1. Interroga Temporal API per workflow attivi: `client.list_workflows("WorkflowType='OrdineWorkflow' AND ExecutionStatus='Running'")`
2. Stampa: N running, N completed, N failed nelle ultime 24h
3. Se `failed > 5` negli ultimi 10 minuti: logga alert
4. Esporta le metriche in `logs/temporal_metrics.json`

---

## Riferimenti

- Temporal Python SDK: https://python.temporal.io/
- Temporal Concepts: https://docs.temporal.io/concepts
- Saga Pattern: https://docs.temporal.io/encyclopedia/workflow-message-passing
- Temporal Samples: https://github.com/temporalio/samples-python
- Temporal Community: https://community.temporal.io/
- Modulo sorgente: `28-temporal-workflow-orchestration.md`
