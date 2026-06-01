# Scenario 03 — Deadlock in asyncio TaskGroup di Produzione

> **Modulo di riferimento:** [10-programmazione-asincrona.md](../10-programmazione-asincrona.md), [07-error-handling-e-logging.md](../07-error-handling-e-logging.md), [30-troubleshooting-e-guide-pratiche.md](../30-troubleshooting-e-guide-pratiche.md)
> **Tempo stimato:** 2-3 ore
> **Livello:** avanzato
> **Prerequisiti:** completamento moduli 07, 10, 30; familiarita con asyncio e structured concurrency
> **Ultimo aggiornamento:** 2026-05-23

---

## Contesto

Un servizio di data processing pipeline processa eventi da Kafka in tempo reale.
L'architettura usa `asyncio.TaskGroup` (Python 3.12) per orchestrare tre stage
di processing che comunicano tramite `asyncio.Event` per la sincronizzazione.

Architettura:

```
Kafka -> [Ingestion Task] -> [Enrichment Task] -> [Output Task] -> PostgreSQL
              |                     |                    |
              +--- Event A ---------+                    |
                                    +--- Event B --------+
                                    |                    |
                                    +<--- Event C -------+
                                          (feedback)
```

Il servizio gira da 2 settimane senza problemi. Dopo un deploy che ha aggiunto
un feedback loop (Event C: Output notifica Enrichment quando il batch e completo),
il servizio si blocca dopo 10-30 minuti di attivita.

---

## Sintomi osservati

1. Il servizio smette di processare eventi — Kafka consumer lag cresce
2. Nessun errore nei log, nessun crash, nessun OOM
3. CPU a 0%, memoria stabile, connessioni DB idle
4. L'health check HTTP risponde (FastAPI su un thread separato)
5. `SIGTERM` non provoca shutdown pulito — il processo resta appeso
6. Il restart risolve temporaneamente, ma il blocco si ripresenta

---

## Dati iniziali

### Log del servizio (ultimi messaggi prima del blocco)

```
2026-05-22 14:23:01.442 INFO  [ingestion] Batch 847 received (250 events)
2026-05-22 14:23:01.443 INFO  [ingestion] Setting event_a for enrichment
2026-05-22 14:23:01.444 INFO  [enrichment] event_a received, processing batch 847
2026-05-22 14:23:01.891 INFO  [enrichment] Batch 847 enriched, setting event_b for output
2026-05-22 14:23:01.892 INFO  [output] event_b received, writing batch 847
2026-05-22 14:23:02.156 INFO  [output] Batch 847 written, setting event_c for enrichment
2026-05-22 14:23:02.157 INFO  [enrichment] event_c received (feedback), ready for next batch
2026-05-22 14:23:02.158 INFO  [ingestion] Batch 848 received (250 events)
2026-05-22 14:23:02.158 INFO  [ingestion] Setting event_a for enrichment
2026-05-22 14:23:02.159 INFO  [enrichment] event_a received, processing batch 848
2026-05-22 14:23:02.601 INFO  [enrichment] Batch 848 enriched, setting event_b for output
2026-05-22 14:23:02.601 INFO  [output] event_b received, writing batch 848
2026-05-22 14:23:02.602 INFO  [enrichment] Waiting for event_c (feedback)...
2026-05-22 14:23:02.602 INFO  [output] Waiting for enrichment to ack event_b...
--- NESSUN ALTRO LOG ---
```

### Metriche (Prometheus)

```
# Kafka consumer lag crescente
kafka_consumer_lag{group="pipeline"} 0      # 14:22:00
kafka_consumer_lag{group="pipeline"} 0      # 14:23:00
kafka_consumer_lag{group="pipeline"} 250    # 14:24:00
kafka_consumer_lag{group="pipeline"} 750    # 14:25:00
kafka_consumer_lag{group="pipeline"} 1500   # 14:26:00
kafka_consumer_lag{group="pipeline"} 3000   # 14:28:00

# Task asyncio attivi
asyncio_tasks_active 3                      # stabile, nessuno termina
```

---

## Codice sorgente del servizio (versione buggata)

### pipeline.py

```python
"""Data processing pipeline — versione con DEADLOCK."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PipelineEvents:
    """Eventi di sincronizzazione tra gli stage della pipeline."""
    event_a: asyncio.Event = field(default_factory=asyncio.Event)  # ingestion -> enrichment
    event_b: asyncio.Event = field(default_factory=asyncio.Event)  # enrichment -> output
    event_c: asyncio.Event = field(default_factory=asyncio.Event)  # output -> enrichment (feedback)


@dataclass
class Batch:
    id: int
    events: list[dict]
    enriched: bool = False
    written: bool = False


async def ingestion_task(events: PipelineEvents, queue: list[Batch]) -> None:
    """Stage 1: riceve batch da Kafka e segnala enrichment."""
    batch_id = 0
    while True:
        # Simula ricezione da Kafka
        await asyncio.sleep(0.5)
        batch_id += 1
        batch = Batch(id=batch_id, events=[{"data": f"event-{i}"} for i in range(250)])
        queue.append(batch)
        logger.info(f"[ingestion] Batch {batch_id} received ({len(batch.events)} events)")

        logger.info(f"[ingestion] Setting event_a for enrichment")
        events.event_a.set()


async def enrichment_task(events: PipelineEvents, queue: list[Batch]) -> None:
    """Stage 2: arricchisce i dati e segnala output."""
    while True:
        # Aspetta dati da ingestion
        await events.event_a.wait()
        events.event_a.clear()

        if not queue:
            continue

        batch = queue[-1]
        logger.info(f"[enrichment] event_a received, processing batch {batch.id}")

        # Simula enrichment (lookup DB, API call, etc.)
        await asyncio.sleep(0.4)
        batch.enriched = True

        logger.info(f"[enrichment] Batch {batch.id} enriched, setting event_b for output")
        events.event_b.set()

        # BUG: aspetta feedback da output PRIMA di essere pronto per il prossimo batch
        # Ma output sta aspettando che enrichment confermi la ricezione di event_b
        logger.info(f"[enrichment] Waiting for event_c (feedback)...")
        await events.event_c.wait()      # <-- DEADLOCK: aspetta output
        events.event_c.clear()
        logger.info(f"[enrichment] event_c received (feedback), ready for next batch")


async def output_task(events: PipelineEvents, queue: list[Batch]) -> None:
    """Stage 3: scrive i dati e invia feedback a enrichment."""
    while True:
        # Aspetta dati arricchiti
        await events.event_b.wait()
        events.event_b.clear()

        if not queue:
            continue

        batch = queue[-1]
        logger.info(f"[output] event_b received, writing batch {batch.id}")

        # Simula scrittura DB
        await asyncio.sleep(0.2)
        batch.written = True

        # BUG: nel path di race condition, output setta event_b_ack
        # e poi aspetta che enrichment processi il prossimo evento
        # prima di settare event_c, creando un ciclo di attesa

        # In condizioni normali funziona, ma quando il timing
        # fa si che enrichment sia gia in wait su event_c
        # PRIMA che output abbia finito di scrivere:
        logger.info(f"[output] Batch {batch.id} written, setting event_c for enrichment")
        events.event_c.set()

        # BUG CRITICO: output aspetta una conferma implicita da enrichment
        # che enrichment ha ricevuto event_c. Ma enrichment potrebbe
        # aver gia fatto clear() su event_c e essere tornato in wait
        # su event_a. Se ingestion ha gia settato event_a, enrichment
        # processa il batch successivo e arriva a wait(event_c)
        # PRIMA che output arrivi qui nel ciclo successivo.
        logger.info(f"[output] Waiting for enrichment to ack event_b...")
        await events.event_b.wait()     # <-- DEADLOCK: aspetta enrichment
        # ^^ Questo e il bug: output riusa event_b come "ack" da enrichment,
        # ma enrichment setta event_b solo DOPO aver ricevuto event_c.
        # Se il timing e sfavorevole:
        #   enrichment: wait(event_c)  -- bloccato
        #   output:     wait(event_b)  -- bloccato
        #   => DEADLOCK


async def run_pipeline() -> None:
    """Avvia la pipeline con TaskGroup."""
    events = PipelineEvents()
    queue: list[Batch] = []

    async with asyncio.TaskGroup() as tg:
        tg.create_task(ingestion_task(events, queue))
        tg.create_task(enrichment_task(events, queue))
        tg.create_task(output_task(events, queue))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-5s %(message)s")
    asyncio.run(run_pipeline())
```

---

## Domande guidate

### D1 — Identificazione del deadlock

Traccia manualmente l'ordine delle operazioni che porta al deadlock.
In quale sequenza precisa di `wait()` e `set()` si verifica il blocco?

<details>
<summary>Suggerimento</summary>

Segui il flusso dopo batch N:
1. enrichment: processa batch, setta `event_b`, poi `wait(event_c)`
2. output: riceve `event_b`, scrive, setta `event_c`, poi `wait(event_b)`
3. enrichment: riceve `event_c`, torna a `wait(event_a)`
4. ingestion: setta `event_a`
5. enrichment: processa batch N+1, setta `event_b`, poi `wait(event_c)`
6. output: riceve `event_b`, scrive, setta `event_c`, poi `wait(event_b)` <-- qui aspetta
7. Ma il timing puo fare si che output arrivi a step 6 e faccia `wait(event_b)`
   PRIMA che enrichment abbia processato batch N+2 e settato `event_b`.
   Questo non e il deadlock vero. Il deadlock e piu sottile...

Il vero deadlock:
- enrichment e in `wait(event_c)` (aspetta feedback)
- output e in `wait(event_b)` (aspetta prossimo batch arricchito)
- enrichment non puo settare `event_b` perche aspetta `event_c`
- output non puo settare `event_c` perche aspetta `event_b`
- Ciclo: enrichment -> event_c -> output -> event_b -> enrichment

</details>

### D2 — Perche funzionava prima?

Il servizio ha funzionato 2 settimane senza il feedback loop.
Cosa ha introdotto il ciclo di dipendenza?

<details>
<summary>Suggerimento</summary>

Senza `event_c`, il flusso era lineare:
- ingestion -> event_a -> enrichment -> event_b -> output
Nessun ciclo, nessuna possibilita di deadlock.
L'aggiunta di `event_c` (output -> enrichment) ha chiuso il ciclo
di dipendenze: A->B->C->A.

</details>

### D3 — Diagnosi con asyncio debug mode

Quali informazioni fornisce `PYTHONASYNCIODEBUG=1`? Come si usano
per identificare coroutine bloccate?

<details>
<summary>Suggerimento</summary>

Abilita: warning per coroutine che non yielddano per >100ms,
logging dettagliato dell'event loop, traceback dei task.
`asyncio.all_tasks()` elenca tutti i task con il loro stato.

</details>

### D4 — Soluzione architetturale

Come ridisegneresti la comunicazione tra gli stage per eliminare
la possibilita di deadlock? Quale primitiva asyncio e piu adatta?

<details>
<summary>Suggerimento</summary>

`asyncio.Queue` disaccoppia produttore e consumatore: il produttore
non deve aspettare che il consumatore legga. Il feedback puo essere
una seconda queue in direzione opposta, ma senza blocchi sincronizzati.

</details>

### D5 — ExceptionGroup

Se durante il deadlock un task lancia un'eccezione (es. timeout),
come si comporta `TaskGroup`? Come gestire `ExceptionGroup`?

<details>
<summary>Suggerimento</summary>

`TaskGroup` cancella tutti i task rimanenti e raccoglie le eccezioni
in un `ExceptionGroup` (PEP 654). Usare `except*` per gestire
eccezioni specifiche dal gruppo.

</details>

---

## Diagnosi passo-passo

### Passo 1 — Abilitare asyncio debug mode

```bash
# Variabile d'ambiente
export PYTHONASYNCIODEBUG=1

# Oppure programmaticamente
python -X dev pipeline.py
```

Output con debug mode:

```
2026-05-22 14:23:02.602 WARNING  Executing <Task pending name='Task-3'
    coro=<enrichment_task() running at pipeline.py:54>
    wait_for=<Future pending cb=[Event._set.<locals>._wake_up()]>
    created at pipeline.py:73>
    took 0.000 seconds

2026-05-22 14:23:02.602 WARNING  Executing <Task pending name='Task-4'
    coro=<output_task() running at pipeline.py:78>
    wait_for=<Future pending cb=[Event._set.<locals>._wake_up()]>
    created at pipeline.py:74>
    took 0.000 seconds
```

### Passo 2 — Introspection dei task bloccati

```python
"""Script di diagnostica: ispeziona task asyncio bloccati."""

import asyncio
import sys
import traceback


async def diagnose_tasks():
    """Stampa stato di tutti i task asyncio."""
    tasks = asyncio.all_tasks()
    print(f"\n{'='*60}")
    print(f"Task attivi: {len(tasks)}")
    print(f"{'='*60}\n")

    for task in sorted(tasks, key=lambda t: t.get_name()):
        print(f"Task: {task.get_name()}")
        print(f"  State:     {task._state}")
        print(f"  Cancelled: {task.cancelled()}")
        print(f"  Done:      {task.done()}")

        # Estrarre il frame della coroutine
        coro = task.get_coro()
        if coro is not None and hasattr(coro, "cr_frame") and coro.cr_frame is not None:
            frame = coro.cr_frame
            print(f"  File:      {frame.f_code.co_filename}:{frame.f_lineno}")
            print(f"  Function:  {frame.f_code.co_name}")
            print(f"  Locals:    {list(frame.f_locals.keys())}")
        print()


# Aggiungere come endpoint di diagnostica
from fastapi import FastAPI
app = FastAPI()

@app.get("/debug/tasks")
async def debug_tasks():
    tasks = asyncio.all_tasks()
    result = []
    for task in tasks:
        info = {
            "name": task.get_name(),
            "state": str(task._state),
            "cancelled": task.cancelled(),
            "done": task.done(),
        }
        coro = task.get_coro()
        if coro is not None and hasattr(coro, "cr_frame") and coro.cr_frame is not None:
            frame = coro.cr_frame
            info["file"] = f"{frame.f_code.co_filename}:{frame.f_lineno}"
            info["function"] = frame.f_code.co_name
        result.append(info)
    return {"tasks": result, "total": len(tasks)}
```

Output dell'endpoint `/debug/tasks` durante il deadlock:

```json
{
  "tasks": [
    {
      "name": "Task-2",
      "state": "PENDING",
      "cancelled": false,
      "done": false,
      "file": "pipeline.py:32",
      "function": "ingestion_task"
    },
    {
      "name": "Task-3",
      "state": "PENDING",
      "cancelled": false,
      "done": false,
      "file": "pipeline.py:54",
      "function": "enrichment_task"
    },
    {
      "name": "Task-4",
      "state": "PENDING",
      "cancelled": false,
      "done": false,
      "file": "pipeline.py:78",
      "function": "output_task"
    }
  ],
  "total": 3
}
```

Task-3 bloccato su riga 54 (`await events.event_c.wait()`).
Task-4 bloccato su riga 78 (`await events.event_b.wait()`).
Conferma deadlock circolare.

### Passo 3 — py-spy per coroutine bloccate

```bash
# Installare py-spy
pip install py-spy

# Catturare stack trace del processo bloccato
py-spy dump --pid $(pgrep -f pipeline.py) --subprocesses
```

Output:

```
Process 12847 (python pipeline.py)
Thread 12847 (MainThread)
  asyncio/events.py:88   _run
  asyncio/runners.py:194 run
  pipeline.py:77         run_pipeline (async)
  pipeline.py:54         enrichment_task (async)
    await events.event_c.wait()    # <-- BLOCCATO QUI
  asyncio/locks.py:213   wait (async)
    await self._event.wait()

Thread 12847 (MainThread) [another coroutine]
  pipeline.py:78         output_task (async)
    await events.event_b.wait()    # <-- BLOCCATO QUI
  asyncio/locks.py:213   wait (async)
    await self._event.wait()
```

### Passo 4 — Visualizzazione del grafo di dipendenze

```
                    enrichment_task
                   /              \
            wait(event_a)     wait(event_c)
                 |                  ^
                 v                  |
           ingestion_task      output_task
           set(event_a)       set(event_c)
                              wait(event_b)
                                    ^
                                    |
                            enrichment_task
                            set(event_b)
                            wait(event_c)  <-- CICLO!

Dipendenze circolari:
  enrichment --[aspetta event_c]--> output
  output     --[aspetta event_b]--> enrichment
```

---

## Soluzione completa

### pipeline_fixed.py

```python
"""Data processing pipeline — versione CORRETTA con asyncio.Queue."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Timeout globale per operazioni di queue
QUEUE_TIMEOUT = 30.0


@dataclass
class Batch:
    id: int
    events: list[dict]
    enriched: bool = False
    written: bool = False


async def ingestion_task(
    ingestion_to_enrichment: asyncio.Queue[Batch],
) -> None:
    """Stage 1: riceve batch e li mette nella queue per enrichment."""
    batch_id = 0
    while True:
        await asyncio.sleep(0.5)  # simula ricezione Kafka
        batch_id += 1
        batch = Batch(id=batch_id, events=[{"data": f"event-{i}"} for i in range(250)])
        logger.info(f"[ingestion] Batch {batch_id} received ({len(batch.events)} events)")

        # Queue.put non si blocca sul consumatore — nessun deadlock possibile
        await ingestion_to_enrichment.put(batch)
        logger.info(f"[ingestion] Batch {batch_id} queued for enrichment")


async def enrichment_task(
    ingestion_to_enrichment: asyncio.Queue[Batch],
    enrichment_to_output: asyncio.Queue[Batch],
    feedback_queue: asyncio.Queue[int],
) -> None:
    """Stage 2: arricchisce i dati e li passa a output."""
    while True:
        # Ricevi batch da ingestion (con timeout per evitare hang infiniti)
        try:
            batch = await asyncio.wait_for(
                ingestion_to_enrichment.get(),
                timeout=QUEUE_TIMEOUT,
            )
        except TimeoutError:
            logger.warning("[enrichment] Timeout waiting for batch from ingestion")
            continue

        logger.info(f"[enrichment] Processing batch {batch.id}")
        await asyncio.sleep(0.4)  # simula enrichment
        batch.enriched = True

        # Invia a output
        await enrichment_to_output.put(batch)
        logger.info(f"[enrichment] Batch {batch.id} enriched, queued for output")

        # Ricevi feedback (non bloccante rispetto ad output)
        # Il feedback arriva DOPO che output ha scritto,
        # ma enrichment puo gia processare il prossimo batch
        # perche non aspetta feedback prima di leggere dalla queue
        try:
            feedback_batch_id = await asyncio.wait_for(
                feedback_queue.get(),
                timeout=QUEUE_TIMEOUT,
            )
            logger.info(f"[enrichment] Feedback received for batch {feedback_batch_id}")
        except TimeoutError:
            logger.warning("[enrichment] Timeout waiting for feedback, continuing")


async def output_task(
    enrichment_to_output: asyncio.Queue[Batch],
    feedback_queue: asyncio.Queue[int],
) -> None:
    """Stage 3: scrive i dati e invia feedback."""
    while True:
        try:
            batch = await asyncio.wait_for(
                enrichment_to_output.get(),
                timeout=QUEUE_TIMEOUT,
            )
        except TimeoutError:
            logger.warning("[output] Timeout waiting for enriched batch")
            continue

        logger.info(f"[output] Writing batch {batch.id}")
        await asyncio.sleep(0.2)  # simula scrittura DB
        batch.written = True

        # Feedback ad enrichment — non bloccante
        await feedback_queue.put(batch.id)
        logger.info(f"[output] Batch {batch.id} written, feedback sent")


async def run_pipeline() -> None:
    """Avvia la pipeline con TaskGroup e timeout guard."""

    # Queue con maxsize per backpressure
    ingestion_to_enrichment: asyncio.Queue[Batch] = asyncio.Queue(maxsize=100)
    enrichment_to_output: asyncio.Queue[Batch] = asyncio.Queue(maxsize=100)
    feedback_queue: asyncio.Queue[int] = asyncio.Queue(maxsize=100)

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(
                ingestion_task(ingestion_to_enrichment),
                name="ingestion",
            )
            tg.create_task(
                enrichment_task(ingestion_to_enrichment, enrichment_to_output, feedback_queue),
                name="enrichment",
            )
            tg.create_task(
                output_task(enrichment_to_output, feedback_queue),
                name="output",
            )
    except* TimeoutError as eg:
        logger.error(f"Pipeline timeout: {len(eg.exceptions)} task(s) timed out")
        for exc in eg.exceptions:
            logger.error(f"  Timeout: {exc}")
    except* Exception as eg:
        logger.error(f"Pipeline error: {len(eg.exceptions)} exception(s)")
        for exc in eg.exceptions:
            logger.error(f"  Error: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s.%(msecs)03d %(levelname)-5s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    asyncio.run(run_pipeline())
```

### Differenze chiave

| Aspetto | Prima (deadlock) | Dopo (fix) |
|---------|------------------|------------|
| Sincronizzazione | `asyncio.Event` (bidirezionale) | `asyncio.Queue` (unidirezionale) |
| Dipendenze | Cicliche: A->B->C->A | Lineari: ingestion->enrichment->output |
| Feedback | `Event` bloccante nel ciclo | Queue separata, non bloccante |
| Backpressure | Nessuna | `Queue(maxsize=100)` |
| Timeout | Assenti | `asyncio.wait_for()` su ogni operazione |
| Error handling | Nessuno | `except*` per `ExceptionGroup` |

---

## Pattern di prevenzione deadlock

### 1. Timeout guard su ogni primitiva di sincronizzazione

```python
async def safe_event_wait(event: asyncio.Event, name: str, timeout: float = 30.0) -> bool:
    """Wrapper con timeout e logging per Event.wait()."""
    try:
        await asyncio.wait_for(event.wait(), timeout=timeout)
        return True
    except TimeoutError:
        logger.error(f"TIMEOUT waiting for event '{name}' after {timeout}s")
        # Potenziale deadlock rilevato
        await _dump_task_state()
        return False


async def _dump_task_state() -> None:
    """Dump diagnostico dello stato dei task."""
    for task in asyncio.all_tasks():
        coro = task.get_coro()
        frame_info = ""
        if coro and hasattr(coro, "cr_frame") and coro.cr_frame:
            f = coro.cr_frame
            frame_info = f" at {f.f_code.co_filename}:{f.f_lineno}"
        logger.warning(f"  Task {task.get_name()}: {task._state}{frame_info}")
```

### 2. Deadlock detection con watchdog

```python
async def deadlock_watchdog(
    interval: float = 60.0,
    max_idle: float = 120.0,
) -> None:
    """Watchdog che rileva stallo nella pipeline."""
    last_progress: float = asyncio.get_event_loop().time()
    last_batch_count: int = 0

    while True:
        await asyncio.sleep(interval)
        current_count = get_processed_batch_count()  # da implementare

        if current_count > last_batch_count:
            last_batch_count = current_count
            last_progress = asyncio.get_event_loop().time()
        else:
            idle_time = asyncio.get_event_loop().time() - last_progress
            if idle_time > max_idle:
                logger.critical(
                    f"DEADLOCK DETECTED: no progress for {idle_time:.0f}s"
                )
                await _dump_task_state()
                # Opzione: cancellare il TaskGroup e riavviare
                raise RuntimeError("Pipeline deadlock detected")
```

### 3. Grafo di dipendenze senza cicli

```python
"""Verifica statica che le dipendenze tra stage non abbiano cicli."""

from collections import defaultdict


def detect_cycles(dependencies: dict[str, list[str]]) -> list[list[str]]:
    """Trova cicli nel grafo di dipendenze usando DFS."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = defaultdict(int)
    cycles: list[list[str]] = []
    path: list[str] = []

    def dfs(node: str) -> None:
        color[node] = GRAY
        path.append(node)
        for neighbor in dependencies.get(node, []):
            if color[neighbor] == GRAY:
                # Trovato ciclo
                cycle_start = path.index(neighbor)
                cycles.append(path[cycle_start:] + [neighbor])
            elif color[neighbor] == WHITE:
                dfs(neighbor)
        path.pop()
        color[node] = BLACK

    for node in dependencies:
        if color[node] == WHITE:
            dfs(node)
    return cycles


# Versione buggata: ciclo rilevato
buggy_deps = {
    "ingestion": ["enrichment"],    # event_a
    "enrichment": ["output"],       # event_b
    "output": ["enrichment"],       # event_c  <-- crea ciclo!
}
cycles = detect_cycles(buggy_deps)
print(f"Cicli trovati: {cycles}")
# Cicli trovati: [['enrichment', 'output', 'enrichment']]

# Versione corretta: nessun ciclo (queue unidirezionali)
fixed_deps = {
    "ingestion": ["enrichment"],
    "enrichment": ["output"],
    "output": [],    # feedback via queue separata, non dipendenza bloccante
}
cycles = detect_cycles(fixed_deps)
print(f"Cicli trovati: {cycles}")
# Cicli trovati: []
```

---

## Gestione ExceptionGroup con TaskGroup

### Partial failure handling

```python
"""Gestione di errori parziali in TaskGroup con except*."""

import asyncio


class StageError(Exception):
    """Errore in uno stage della pipeline."""
    def __init__(self, stage: str, message: str):
        self.stage = stage
        super().__init__(f"[{stage}] {message}")


class IngestionError(StageError):
    def __init__(self, msg: str):
        super().__init__("ingestion", msg)


class EnrichmentError(StageError):
    def __init__(self, msg: str):
        super().__init__("enrichment", msg)


class OutputError(StageError):
    def __init__(self, msg: str):
        super().__init__("output", msg)


async def run_pipeline_with_error_handling() -> None:
    """Pipeline con gestione granulare degli errori per stage."""
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(ingestion_task(...), name="ingestion")
            tg.create_task(enrichment_task(...), name="enrichment")
            tg.create_task(output_task(...), name="output")

    except* IngestionError as eg:
        # Errore in ingestion: Kafka down?
        for exc in eg.exceptions:
            logger.error(f"Ingestion failed: {exc}")
        # Retry con backoff
        await asyncio.sleep(5)

    except* EnrichmentError as eg:
        # Errore in enrichment: API di arricchimento down?
        for exc in eg.exceptions:
            logger.error(f"Enrichment failed: {exc}")
        # Salvare batch non arricchiti per retry

    except* OutputError as eg:
        # Errore in output: DB down?
        for exc in eg.exceptions:
            logger.error(f"Output failed: {exc}")
        # Salvare batch in dead letter queue

    except* TimeoutError as eg:
        # Potenziale deadlock
        logger.critical(f"Timeout: {len(eg.exceptions)} task(s) stuck")
        for exc in eg.exceptions:
            logger.critical(f"  {exc}")

    except* Exception as eg:
        # Errori imprevisti
        logger.critical(f"Unexpected: {len(eg.exceptions)} exception(s)")
        for exc in eg.exceptions:
            logger.critical(f"  {type(exc).__name__}: {exc}", exc_info=exc)
```

### Test del comportamento

```python
"""Test: verifica che il deadlock non si verifichi con la soluzione."""

import asyncio
import pytest


@pytest.mark.asyncio
async def test_pipeline_no_deadlock():
    """La pipeline deve processare N batch senza bloccarsi."""
    ingestion_q: asyncio.Queue[Batch] = asyncio.Queue(maxsize=10)
    enrichment_q: asyncio.Queue[Batch] = asyncio.Queue(maxsize=10)
    feedback_q: asyncio.Queue[int] = asyncio.Queue(maxsize=10)

    processed_batches: list[int] = []
    target_batches = 50

    async def _ingestion():
        for i in range(target_batches):
            batch = Batch(id=i, events=[{"data": "test"}])
            await ingestion_q.put(batch)
            await asyncio.sleep(0.01)

    async def _enrichment():
        for _ in range(target_batches):
            batch = await asyncio.wait_for(ingestion_q.get(), timeout=5.0)
            batch.enriched = True
            await enrichment_q.put(batch)
            try:
                await asyncio.wait_for(feedback_q.get(), timeout=5.0)
            except TimeoutError:
                pass

    async def _output():
        for _ in range(target_batches):
            batch = await asyncio.wait_for(enrichment_q.get(), timeout=5.0)
            batch.written = True
            processed_batches.append(batch.id)
            await feedback_q.put(batch.id)

    # Timeout complessivo: se deadlock, il test fallisce in 10s
    async with asyncio.timeout(10.0):
        async with asyncio.TaskGroup() as tg:
            tg.create_task(_ingestion())
            tg.create_task(_enrichment())
            tg.create_task(_output())

    assert len(processed_batches) == target_batches
    assert all(b.written for b in [])  # simplificato per il test


@pytest.mark.asyncio
async def test_pipeline_timeout_on_deadlock():
    """Verifica che il timeout rilevi il deadlock nella versione buggata."""
    events = PipelineEvents()

    async def _deadlocking_enrichment():
        events.event_a.set()
        await events.event_c.wait()  # aspetta output

    async def _deadlocking_output():
        await events.event_b.wait()  # aspetta enrichment

    with pytest.raises(TimeoutError):
        async with asyncio.timeout(2.0):
            async with asyncio.TaskGroup() as tg:
                tg.create_task(_deadlocking_enrichment())
                tg.create_task(_deadlocking_output())
```

---

## Lezioni apprese

### 1. Event bidirezionali = deadlock risk

`asyncio.Event` e progettato per segnalazione unidirezionale.
Quando due task si aspettano reciprocamente tramite Event,
si crea una dipendenza circolare identica al classico deadlock
di mutex in programmazione concorrente.

Regola: se il grafo delle dipendenze `wait/set` tra task forma
un ciclo, c'e un deadlock latente.

### 2. asyncio.Queue disaccoppia produttore e consumatore

`Queue.put()` non richiede che il consumatore sia in stato specifico.
Il produttore deposita e continua. Il consumatore legge quando pronto.
Questo rompe le dipendenze circolari per design.

| Primitiva | Modello | Rischio deadlock |
|-----------|---------|------------------|
| `Event` | Segnalazione sincrona | Alto se bidirezionale |
| `Queue` | Produttore-consumatore | Basso (unidirezionale) |
| `Condition` | Monitor pattern | Medio (dipende dall'uso) |
| `Semaphore` | Rate limiting | Basso |
| `Lock` | Mutua esclusione | Alto se multipli lock |

### 3. Timeout su OGNI primitiva di sincronizzazione

Un `await event.wait()` senza timeout puo bloccare per sempre.
`asyncio.wait_for()` o `asyncio.timeout()` (3.11+) devono wrappare
qualsiasi operazione di attesa in produzione.

### 4. Deadlock detection proattivo

- Watchdog task che monitora il progresso della pipeline
- Metriche di throughput con alert su stallo
- Endpoint di diagnostica che dumpa lo stato dei task
- `py-spy` per inspection esterna senza modificare il codice

### 5. ExceptionGroup per failure parziali

Con `TaskGroup`, se un task fallisce, tutti vengono cancellati.
`except*` (PEP 654) permette di gestire eccezioni diverse da
task diversi in modo granulare, abilitando retry selettivi.

### 6. Validazione statica del grafo di dipendenze

Prima di deployare, verificare che il grafo di dipendenze tra
task non contenga cicli. Un semplice DFS sul grafo rivela
deadlock potenziali a tempo di design, non di produzione.

---

## Riferimenti

- [Modulo 10 — Programmazione asincrona](../10-programmazione-asincrona.md): TaskGroup, Event, Queue, structured concurrency
- [Modulo 07 — Error handling e logging](../07-error-handling-e-logging.md): ExceptionGroup, except*, structured logging
- [Modulo 30 — Troubleshooting](../30-troubleshooting-e-guide-pratiche.md): diagnosi, py-spy, debug mode
- PEP 654 — Exception Groups and except*
- Python docs: `asyncio.TaskGroup`, `asyncio.Queue`, `asyncio.Event`
- `py-spy` docs: sampling profiler per Python
