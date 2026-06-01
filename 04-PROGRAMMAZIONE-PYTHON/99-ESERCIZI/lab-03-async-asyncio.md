# Lab 03 — Async Client con TaskGroup, Timeout e Retry

> **Moduli di riferimento:** [10-programmazione-asincrona.md](../10-programmazione-asincrona.md), [17-network-programming.md](../17-network-programming.md), [07-error-handling-e-logging.md](../07-error-handling-e-logging.md)
> **Tempo stimato:** 4-5 ore
> **Livello:** proficient
> **Prerequisiti:** completamento moduli 01, 07, 10, 17; Python 3.12+ installato; `uv` o `pip` disponibile
> **Ultimo aggiornamento:** 2026-05-23

---

## Scenario

Lavori nel team backend di un'azienda fintech che aggrega dati di mercato da 6 API
esterne (cambi valuta, quotazioni crypto, indici azionari). Il sistema attuale esegue
le chiamate in sequenza, impiegando 12-18 secondi per ciclo di aggiornamento. Il
product owner vuole scendere sotto i 3 secondi mantenendo resilienza: ogni API ha SLA
diversi, timeout variabili e limiti di rate. Il tuo compito e costruire un client
asincrono strutturato che gestisca concorrenza, timeout, retry e backpressure.

---

## Obiettivi

Al termine del lab saprai:

1. Usare `asyncio.Runner` come entry point avanzato al posto di `asyncio.run`
2. Gestire concorrenza strutturata con `TaskGroup`
3. Applicare timeout granulari con `asyncio.timeout()`
4. Catturare errori multipli con `ExceptionGroup` e `except*`
5. Limitare la concorrenza con `asyncio.Semaphore`
6. Implementare il pattern producer-consumer con `asyncio.Queue`
7. Costruire retry con exponential backoff
8. Correlare le richieste con `contextvars`
9. Integrare `uvloop` per incrementare il throughput
10. Gestire lo shutdown gracefully con signal handling
11. Confrontare le performance: sequenziale vs concorrente vs parallelo

---

## Ambiente

```text
project/
├── pyproject.toml
├── src/
│   └── market_fetcher/
│       ├── __init__.py
│       ├── main.py
│       ├── client.py
│       ├── retry.py
│       ├── queue_pipeline.py
│       └── shutdown.py
└── tests/
    └── test_retry.py
```

Dipendenze:

```bash
uv init market-fetcher && cd market-fetcher
uv add httpx uvloop
uv add --dev pytest pytest-asyncio
```

> **Nota:** `uvloop` funziona solo su Linux e macOS. Su Windows, il lab funziona
> comunque ma salta l'integrazione uvloop (Parte 8).

---

## Parte 1 — Entry Point con asyncio.Runner (20 min)

### 1.1 Runner vs asyncio.run

`asyncio.Runner` (3.11+) consente di riutilizzare lo stesso event loop per piu
coroutine, configurare il loop factory e gestire il ciclo di vita manualmente.

Creare `src/market_fetcher/main.py`:

```python
import asyncio
import sys


async def healthcheck() -> dict:
    """Verifica che l'event loop sia funzionante."""
    loop = asyncio.get_running_loop()
    return {
        "loop_class": type(loop).__name__,
        "running": loop.is_running(),
        "pid": __import__("os").getpid(),
    }


async def main() -> None:
    info = await healthcheck()
    print(f"Event loop: {info['loop_class']} (pid={info['pid']})")


if __name__ == "__main__":
    with asyncio.Runner() as runner:
        runner.run(main())
```

Eseguire:

```bash
python -m market_fetcher.main
```

### 1.2 Configurare il loop factory

```python
def _create_loop() -> asyncio.AbstractEventLoop:
    """Factory che tenta uvloop, fallback al default."""
    try:
        import uvloop
        return uvloop.new_event_loop()
    except ImportError:
        return asyncio.new_event_loop()


if __name__ == "__main__":
    with asyncio.Runner(loop_factory=_create_loop) as runner:
        runner.run(main())
```

---

## Parte 2 — TaskGroup e Concorrenza Strutturata (40 min)

### 2.1 Simulare le API esterne

Per il lab, usiamo un server fittizio. Creare `src/market_fetcher/client.py`:

```python
from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class MarketQuote:
    source: str
    symbol: str
    price: float
    latency_ms: float
    timestamp: float = field(default_factory=time.time)


# Simula API con latenze realistiche
API_ENDPOINTS: dict[str, float] = {
    "forex-ecb": 0.8,       # 800ms tipico
    "forex-fixer": 1.2,     # 1.2s tipico
    "crypto-binance": 0.3,  # 300ms tipico
    "crypto-coinbase": 0.5, # 500ms tipico
    "index-yahoo": 1.5,     # 1.5s tipico
    "index-alphavantage": 2.0,  # 2s tipico, spesso lento
}


async def fetch_quote(source: str, base_latency: float) -> MarketQuote:
    """Simula una chiamata API con latenza variabile."""
    jitter = random.uniform(0.5, 1.5)
    actual_latency = base_latency * jitter

    # 15% di probabilita di errore transitorio
    if random.random() < 0.15:
        await asyncio.sleep(actual_latency * 0.3)
        raise ConnectionError(f"{source}: connection reset")

    await asyncio.sleep(actual_latency)
    return MarketQuote(
        source=source,
        symbol="EUR/USD",
        price=round(1.08 + random.uniform(-0.005, 0.005), 5),
        latency_ms=round(actual_latency * 1000, 1),
    )
```

### 2.2 Fetch sequenziale (baseline)

```python
async def fetch_sequential() -> list[MarketQuote]:
    """Fetch sequenziale — baseline per confronto."""
    results: list[MarketQuote] = []
    for source, latency in API_ENDPOINTS.items():
        try:
            quote = await fetch_quote(source, latency)
            results.append(quote)
        except ConnectionError as exc:
            print(f"  SKIP {source}: {exc}")
    return results
```

### 2.3 Fetch concorrente con TaskGroup

```python
async def fetch_concurrent() -> list[MarketQuote]:
    """Fetch concorrente con TaskGroup — structured concurrency."""
    results: list[MarketQuote] = []
    errors: list[Exception] = []

    async with asyncio.TaskGroup() as tg:
        tasks: dict[str, asyncio.Task[MarketQuote]] = {}
        for source, latency in API_ENDPOINTS.items():
            task = tg.create_task(
                fetch_quote(source, latency),
                name=f"fetch-{source}",
            )
            tasks[source] = task

    # Se arriviamo qui, tutti i task sono completati o e stato
    # sollevato un ExceptionGroup. Lo gestiamo nella Parte 4.
    for source, task in tasks.items():
        if not task.cancelled() and task.exception() is None:
            results.append(task.result())

    return results
```

**Problema:** `TaskGroup` propaga le eccezioni come `ExceptionGroup`. Se anche
un solo task fallisce, l'intero gruppo viene cancellato. Lo risolviamo nella
Parte 4 con `except*`.

---

## Parte 3 — Timeout per Task (30 min)

### 3.1 asyncio.timeout() per singola richiesta

```python
async def fetch_with_timeout(
    source: str,
    base_latency: float,
    timeout_seconds: float = 3.0,
) -> MarketQuote | None:
    """Fetch con timeout individuale."""
    try:
        async with asyncio.timeout(timeout_seconds):
            return await fetch_quote(source, base_latency)
    except TimeoutError:
        print(f"  TIMEOUT {source} dopo {timeout_seconds}s")
        return None
    except ConnectionError as exc:
        print(f"  ERROR {source}: {exc}")
        return None
```

### 3.2 TaskGroup con timeout individuali

```python
async def fetch_concurrent_with_timeouts() -> list[MarketQuote]:
    """Ogni task ha il proprio timeout; i fallimenti non cancellano il gruppo."""
    results: list[MarketQuote] = []

    async def _safe_fetch(source: str, latency: float) -> None:
        quote = await fetch_with_timeout(source, latency, timeout_seconds=2.5)
        if quote is not None:
            results.append(quote)

    async with asyncio.TaskGroup() as tg:
        for source, latency in API_ENDPOINTS.items():
            tg.create_task(_safe_fetch(source, latency), name=f"fetch-{source}")

    return results
```

**Osservazione:** avvolgendo ogni task in `_safe_fetch`, le eccezioni vengono
gestite internamente e il `TaskGroup` non vede errori non catturati.

---

## Parte 4 — ExceptionGroup e except* (30 min)

### 4.1 Lasciare propagare le eccezioni

Quando serve sapere *quali* task sono falliti e *perche*, usiamo `except*`:

```python
async def fetch_with_exception_groups() -> list[MarketQuote]:
    """Dimostra except* per gestione selettiva degli errori."""
    results: list[MarketQuote] = []

    try:
        async with asyncio.TaskGroup() as tg:
            tasks = {
                source: tg.create_task(fetch_quote(source, latency))
                for source, latency in API_ENDPOINTS.items()
            }
    except* ConnectionError as eg:
        # eg e un ExceptionGroup contenente solo ConnectionError
        print(f"  {len(eg.exceptions)} connection errors:")
        for exc in eg.exceptions:
            print(f"    - {exc}")
    except* TimeoutError as eg:
        print(f"  {len(eg.exceptions)} timeouts")
    else:
        # Nessun errore: tutti i task completati
        pass

    for source, task in tasks.items():
        if not task.cancelled() and task.exception() is None:
            results.append(task.result())

    return results
```

### 4.2 ExceptionGroup nidificati

```python
def analyze_exception_group(eg: ExceptionGroup, depth: int = 0) -> None:
    """Analisi ricorsiva di ExceptionGroup nidificati."""
    indent = "  " * depth
    print(f"{indent}ExceptionGroup: {eg.message} ({len(eg.exceptions)} sub)")
    for exc in eg.exceptions:
        if isinstance(exc, ExceptionGroup):
            analyze_exception_group(exc, depth + 1)
        else:
            print(f"{indent}  {type(exc).__name__}: {exc}")
```

---

## Parte 5 — HTTP Client Asincrono con httpx (40 min)

### 5.1 Sostituire il mock con httpx

Ora colleghiamo il client a endpoint reali. Usiamo `httpx` (asincrono nativo,
API vicina a `requests`).

```python
import httpx

# Endpoint pubblici che non richiedono autenticazione
REAL_ENDPOINTS: dict[str, str] = {
    "httpbin-get": "https://httpbin.org/get",
    "httpbin-delay-1": "https://httpbin.org/delay/1",
    "httpbin-delay-3": "https://httpbin.org/delay/3",
    "jsonplaceholder-1": "https://jsonplaceholder.typicode.com/posts/1",
    "jsonplaceholder-2": "https://jsonplaceholder.typicode.com/posts/2",
    "httpbin-status-500": "https://httpbin.org/status/500",
}


async def fetch_real_endpoint(
    client: httpx.AsyncClient,
    name: str,
    url: str,
) -> dict:
    """Fetch da un endpoint reale con timing."""
    t0 = time.monotonic()
    response = await client.get(url)
    elapsed_ms = (time.monotonic() - t0) * 1000

    response.raise_for_status()
    return {
        "name": name,
        "status": response.status_code,
        "latency_ms": round(elapsed_ms, 1),
        "size_bytes": len(response.content),
    }
```

### 5.2 Fetch concorrente con httpx e TaskGroup

```python
async def fetch_all_real() -> list[dict]:
    """Fetch concorrente da endpoint reali."""
    results: list[dict] = []

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0),
        limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        follow_redirects=True,
    ) as client:
        async def _safe_fetch(name: str, url: str) -> None:
            try:
                async with asyncio.timeout(5.0):
                    result = await fetch_real_endpoint(client, name, url)
                    results.append(result)
            except (httpx.HTTPStatusError, TimeoutError, httpx.ConnectError) as exc:
                print(f"  FAILED {name}: {type(exc).__name__}: {exc}")

        async with asyncio.TaskGroup() as tg:
            for name, url in REAL_ENDPOINTS.items():
                tg.create_task(_safe_fetch(name, url))

    return results
```

---

## Parte 6 — Semaphore per Rate Limiting (30 min)

### 6.1 Limitare la concorrenza

Molte API impongono rate limit. Un `Semaphore` limita il numero di richieste
simultanee senza cambiare la logica di fetch.

```python
async def fetch_rate_limited(
    max_concurrent: int = 3,
) -> list[MarketQuote]:
    """Fetch con al massimo max_concurrent richieste simultanee."""
    semaphore = asyncio.Semaphore(max_concurrent)
    results: list[MarketQuote] = []

    async def _limited_fetch(source: str, latency: float) -> None:
        async with semaphore:
            print(f"  START {source} (semaphore count: {semaphore._value})")
            quote = await fetch_with_timeout(source, latency)
            if quote is not None:
                results.append(quote)

    async with asyncio.TaskGroup() as tg:
        for source, latency in API_ENDPOINTS.items():
            tg.create_task(_limited_fetch(source, latency))

    return results
```

### 6.2 Sliding window rate limiter

Per rate limit piu sofisticati (es. "max 10 richieste per secondo"):

```python
class SlidingWindowLimiter:
    """Rate limiter a finestra scorrevole."""

    __slots__ = ("_max_requests", "_window_seconds", "_timestamps", "_lock")

    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._timestamps: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        while True:
            async with self._lock:
                now = time.monotonic()
                # Rimuovi timestamp fuori dalla finestra
                self._timestamps = [
                    ts for ts in self._timestamps
                    if now - ts < self._window_seconds
                ]
                if len(self._timestamps) < self._max_requests:
                    self._timestamps.append(now)
                    return
            # Finestra piena: attendi
            await asyncio.sleep(0.05)
```

---

## Parte 7 — Producer-Consumer con asyncio.Queue (40 min)

### 7.1 Pattern base

```python
import asyncio
from collections.abc import Sequence


async def producer(
    queue: asyncio.Queue[MarketQuote | None],
    sources: Sequence[tuple[str, float]],
    semaphore: asyncio.Semaphore,
) -> None:
    """Produce quote e le inserisce nella coda."""
    async with asyncio.TaskGroup() as tg:
        async def _produce_one(source: str, latency: float) -> None:
            async with semaphore:
                try:
                    quote = await fetch_quote(source, latency)
                    await queue.put(quote)
                except ConnectionError:
                    pass  # skip, non inserire nella coda

        for source, latency in sources:
            tg.create_task(_produce_one(source, latency))

    # Segnale di terminazione
    await queue.put(None)


async def consumer(
    queue: asyncio.Queue[MarketQuote | None],
    results: list[MarketQuote],
) -> None:
    """Consuma quote dalla coda e le processa."""
    while True:
        item = await queue.get()
        if item is None:
            queue.task_done()
            break
        # Simulazione di processing (validazione, persistenza, etc.)
        print(f"  CONSUMED {item.source}: {item.symbol} @ {item.price}")
        results.append(item)
        queue.task_done()


async def run_pipeline() -> list[MarketQuote]:
    """Esegue la pipeline producer-consumer."""
    queue: asyncio.Queue[MarketQuote | None] = asyncio.Queue(maxsize=10)
    semaphore = asyncio.Semaphore(3)
    results: list[MarketQuote] = []

    sources = list(API_ENDPOINTS.items())

    async with asyncio.TaskGroup() as tg:
        tg.create_task(producer(queue, sources, semaphore))
        tg.create_task(consumer(queue, results))

    return results
```

### 7.2 Multi-consumer

```python
async def run_multi_consumer_pipeline(
    n_consumers: int = 3,
) -> list[MarketQuote]:
    """Pipeline con N consumer in parallelo."""
    queue: asyncio.Queue[MarketQuote | None] = asyncio.Queue(maxsize=20)
    semaphore = asyncio.Semaphore(4)
    results: list[MarketQuote] = []

    sources = list(API_ENDPOINTS.items())

    async with asyncio.TaskGroup() as tg:
        tg.create_task(producer(queue, sources, semaphore))
        for i in range(n_consumers):
            tg.create_task(consumer(queue, results))

    # Nota: il producer deve inviare n_consumers sentinelle None
    return results
```

> **Attenzione:** con N consumer, il producer deve inserire N sentinelle `None`
> nella coda per terminare tutti i consumer. Modificare `producer()` di
> conseguenza.

---

## Parte 8 — Retry con Exponential Backoff (30 min)

### 8.1 Implementazione

Creare `src/market_fetcher/retry.py`:

```python
from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")
logger = logging.getLogger(__name__)

# Eccezioni per cui vale la pena ritentare
RETRYABLE: tuple[type[Exception], ...] = (
    ConnectionError,
    TimeoutError,
    OSError,
)


async def retry_with_backoff(
    func: Callable[..., Awaitable[T]],
    *args: object,
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
    retryable: tuple[type[Exception], ...] = RETRYABLE,
    **kwargs: object,
) -> T:
    """Esegue func con retry e exponential backoff + jitter."""
    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except retryable as exc:
            last_exc = exc
            if attempt == max_retries:
                break

            # Exponential backoff con full jitter (AWS style)
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            jitter = random.uniform(0, delay)
            logger.warning(
                "Attempt %d/%d failed: %s. Retrying in %.2fs",
                attempt,
                max_retries,
                exc,
                jitter,
            )
            await asyncio.sleep(jitter)

    raise last_exc  # type: ignore[misc]
```

### 8.2 Integrazione con il client

```python
async def fetch_with_retry(source: str, latency: float) -> MarketQuote | None:
    """Fetch con retry automatico."""
    try:
        return await retry_with_backoff(
            fetch_quote,
            source,
            latency,
            max_retries=3,
            base_delay=0.3,
        )
    except ConnectionError:
        print(f"  EXHAUSTED {source}: tutti i retry falliti")
        return None
```

### 8.3 Test unitario

Creare `tests/test_retry.py`:

```python
import asyncio
import pytest
from market_fetcher.retry import retry_with_backoff


@pytest.mark.asyncio
async def test_retry_succeeds_after_failures():
    call_count = 0

    async def flaky() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("simulated failure")
        return "ok"

    result = await retry_with_backoff(flaky, max_retries=3, base_delay=0.01)
    assert result == "ok"
    assert call_count == 3


@pytest.mark.asyncio
async def test_retry_raises_after_exhaustion():
    async def always_fails() -> str:
        raise ConnectionError("permanent failure")

    with pytest.raises(ConnectionError, match="permanent"):
        await retry_with_backoff(
            always_fails, max_retries=2, base_delay=0.01
        )
```

---

## Parte 9 — contextvars per Correlazione Richieste (20 min)

### 9.1 Correlation ID per request tracing

```python
import contextvars
import uuid

correlation_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "correlation_id", default="no-correlation"
)


async def fetch_with_correlation(source: str, latency: float) -> MarketQuote:
    """Ogni task ha il proprio correlation ID."""
    cid = str(uuid.uuid4())[:8]
    correlation_id.set(cid)

    logger.info("[%s] Starting fetch for %s", correlation_id.get(), source)
    quote = await fetch_quote(source, latency)
    logger.info(
        "[%s] Completed %s in %.1fms",
        correlation_id.get(),
        source,
        quote.latency_ms,
    )
    return quote
```

### 9.2 TaskGroup con correlation ID

```python
async def fetch_all_correlated() -> list[MarketQuote]:
    """Ogni task in TaskGroup mantiene il proprio contesto."""
    results: list[MarketQuote] = []

    async def _tracked_fetch(source: str, latency: float) -> None:
        try:
            quote = await fetch_with_correlation(source, latency)
            results.append(quote)
        except ConnectionError:
            logger.warning(
                "[%s] Failed %s", correlation_id.get(), source
            )

    async with asyncio.TaskGroup() as tg:
        for source, latency in API_ENDPOINTS.items():
            # copy_context() assicura che ogni task abbia il proprio contesto
            ctx = contextvars.copy_context()
            tg.create_task(ctx.run(_tracked_fetch, source, latency))

    return results
```

> **Nota:** `asyncio.Task` copia automaticamente il contesto corrente alla
> creazione. L'uso esplicito di `copy_context()` e necessario solo quando si
> vuole isolare ulteriormente il contesto (es. pre-impostare variabili).

---

## Parte 10 — uvloop per Performance (15 min)

### 10.1 Integrazione

> Disponibile solo su Linux e macOS. Su Windows, saltare questa parte.

```python
def create_uvloop() -> asyncio.AbstractEventLoop:
    """Crea un event loop uvloop (2-4x throughput su I/O pesante)."""
    import uvloop
    return uvloop.new_event_loop()


# In main.py, usare con Runner:
if __name__ == "__main__":
    try:
        import uvloop
        factory = create_uvloop
    except ImportError:
        factory = asyncio.new_event_loop

    with asyncio.Runner(loop_factory=factory) as runner:
        runner.run(main())
```

### 10.2 Benchmark loop default vs uvloop

```python
async def benchmark_loop(label: str, iterations: int = 100) -> float:
    """Misura il throughput dell'event loop."""
    t0 = time.monotonic()

    async def _noop() -> None:
        await asyncio.sleep(0)

    async with asyncio.TaskGroup() as tg:
        for _ in range(iterations):
            tg.create_task(_noop())

    elapsed = time.monotonic() - t0
    print(f"  {label}: {iterations} tasks in {elapsed*1000:.1f}ms")
    return elapsed
```

---

## Parte 11 — Graceful Shutdown con Signal Handling (30 min)

### 11.1 Catturare SIGINT e SIGTERM

Creare `src/market_fetcher/shutdown.py`:

```python
from __future__ import annotations

import asyncio
import signal
import logging

logger = logging.getLogger(__name__)


class GracefulShutdown:
    """Gestisce lo shutdown ordinato di task asincroni."""

    __slots__ = ("_shutdown_event", "_tasks")

    def __init__(self) -> None:
        self._shutdown_event = asyncio.Event()
        self._tasks: set[asyncio.Task[object]] = set()

    @property
    def is_shutting_down(self) -> bool:
        return self._shutdown_event.is_set()

    def register_task(self, task: asyncio.Task[object]) -> None:
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    def install_signal_handlers(self) -> None:
        """Installa handler per SIGINT e SIGTERM."""
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._handle_signal, sig)

    def _handle_signal(self, sig: signal.Signals) -> None:
        logger.info("Received %s, initiating graceful shutdown...", sig.name)
        self._shutdown_event.set()

    async def wait_for_shutdown(self) -> None:
        """Attende il segnale di shutdown."""
        await self._shutdown_event.wait()

    async def cancel_all(self, timeout: float = 5.0) -> None:
        """Cancella tutti i task registrati con un timeout."""
        if not self._tasks:
            return

        logger.info("Cancelling %d tasks...", len(self._tasks))
        for task in self._tasks:
            task.cancel()

        done, pending = await asyncio.wait(
            self._tasks, timeout=timeout
        )

        if pending:
            logger.warning(
                "%d tasks did not complete within %.1fs",
                len(pending),
                timeout,
            )
```

### 11.2 Integrazione nel main loop

```python
async def main_with_shutdown() -> None:
    """Main loop con graceful shutdown."""
    shutdown = GracefulShutdown()
    shutdown.install_signal_handlers()

    # Worker che gira fino allo shutdown
    async def polling_worker() -> None:
        cycle = 0
        while not shutdown.is_shutting_down:
            cycle += 1
            print(f"\n=== Cycle {cycle} ===")
            results = await fetch_rate_limited(max_concurrent=3)
            print(f"  Fetched {len(results)} quotes")
            # Attendi 5s o lo shutdown, qualunque venga prima
            try:
                async with asyncio.timeout(5.0):
                    await shutdown.wait_for_shutdown()
                    break
            except TimeoutError:
                continue  # timeout scaduto, nuovo ciclo

    task = asyncio.create_task(polling_worker())
    shutdown.register_task(task)

    await shutdown.wait_for_shutdown()
    await shutdown.cancel_all(timeout=3.0)
    print("Shutdown complete.")
```

---

## Parte 12 — Confronto Performance (30 min)

### 12.1 Benchmark comparativo

```python
import time


async def benchmark() -> None:
    """Confronta le tre strategie di fetch."""
    print("=" * 60)
    print("BENCHMARK: Sequenziale vs Concorrente vs Rate-Limited")
    print("=" * 60)

    # 1. Sequenziale
    t0 = time.monotonic()
    seq_results = await fetch_sequential()
    t_seq = time.monotonic() - t0
    print(f"\nSequenziale: {len(seq_results)} quote in {t_seq:.2f}s")

    # 2. Concorrente (tutte in parallelo)
    t0 = time.monotonic()
    conc_results = await fetch_concurrent_with_timeouts()
    t_conc = time.monotonic() - t0
    print(f"Concorrente: {len(conc_results)} quote in {t_conc:.2f}s")

    # 3. Rate-limited (max 3 simultanee)
    t0 = time.monotonic()
    rl_results = await fetch_rate_limited(max_concurrent=3)
    t_rl = time.monotonic() - t0
    print(f"Rate-limited: {len(rl_results)} quote in {t_rl:.2f}s")

    # Speedup
    print(f"\nSpeedup concorrente: {t_seq/t_conc:.1f}x")
    print(f"Speedup rate-limited: {t_seq/t_rl:.1f}x")
    print("=" * 60)
```

### 12.2 Output atteso

```text
============================================================
BENCHMARK: Sequenziale vs Concorrente vs Rate-Limited
============================================================

Sequenziale: 5 quote in 5.83s
Concorrente: 6 quote in 2.01s
Rate-limited: 5 quote in 3.24s

Speedup concorrente: 2.9x
Speedup rate-limited: 1.8x
============================================================
```

I risultati variano per la latenza simulata e gli errori casuali. Lo speedup
concorrente dovrebbe essere 2-4x; il rate-limited e un compromesso tra velocita
e rispetto dei limiti dell'API.

---

## Checklist finale

- [ ] `asyncio.Runner` usato come entry point con loop factory configurabile
- [ ] `TaskGroup` per structured concurrency con task nominati
- [ ] `asyncio.timeout()` applicato per-task con gestione graceful
- [ ] `ExceptionGroup` gestito con `except*` per errori selettivi
- [ ] `httpx.AsyncClient` configurato con timeout e connection limits
- [ ] `Semaphore` per limitare la concorrenza (es. max 3 simultanee)
- [ ] `asyncio.Queue` per pipeline producer-consumer funzionante
- [ ] Retry con exponential backoff + full jitter implementato e testato
- [ ] `contextvars` per correlation ID in ogni task
- [ ] `uvloop` integrato con fallback su Linux/macOS
- [ ] Signal handling per SIGINT/SIGTERM con cancellazione ordinata dei task
- [ ] Benchmark eseguito con confronto sequenziale/concorrente/rate-limited

---

## Valutazione

| Criterio | Peso | Insufficiente | Sufficiente | Buono | Eccellente |
|----------|------|---------------|-------------|-------|------------|
| Concorrenza strutturata (TaskGroup + timeout) | 25% | Non usa TaskGroup | TaskGroup senza timeout | TaskGroup con timeout ma senza error handling | TaskGroup + timeout + except* completo |
| Resilienza (retry + error handling) | 20% | Nessun retry | Retry fisso senza backoff | Exponential backoff | Backoff + jitter + test unitari |
| Rate limiting (Semaphore + sliding window) | 15% | Nessun limite | Semaphore base | Semaphore + maxsize Queue | Sliding window rate limiter |
| Pipeline (Queue producer-consumer) | 15% | Non implementata | Single consumer | Multi-consumer | Multi-consumer + backpressure (maxsize) |
| Shutdown e signal handling | 10% | Nessuno | Cattura SIGINT | Cattura + cancel task | Cancel + timeout + logging |
| Osservabilita (correlation, logging) | 10% | Nessun log | Print-based | logging module | contextvars + structured logging |
| Performance (uvloop + benchmark) | 5% | Nessun benchmark | Benchmark manuale | Confronto automatizzato | uvloop + confronto 3 strategie |

---

## Riferimenti

- [10-programmazione-asincrona.md](../10-programmazione-asincrona.md) — teoria asyncio, event loop, pattern
- [17-network-programming.md](../17-network-programming.md) — networking, protocolli, socket
- [07-error-handling-e-logging.md](../07-error-handling-e-logging.md) — gestione errori, logging strutturato
- PEP 654 — Exception Groups and except* — https://peps.python.org/pep-0654/
- asyncio.TaskGroup — https://docs.python.org/3/library/asyncio-task.html#asyncio.TaskGroup
- httpx — https://www.python-httpx.org/async/
- uvloop — https://github.com/MagicStack/uvloop
