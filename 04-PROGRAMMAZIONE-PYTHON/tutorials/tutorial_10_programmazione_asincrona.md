# Tutorial 10 — Programmazione Asincrona in Python: Dal Principiante all'Esperto

> **Companion a:** `10-programmazione-asincrona.md`
> **Scope:** asyncio, async/await, TaskGroup, timeout, asyncio.Runner, uvloop, pattern asincroni
> **Prerequisiti:** `tutorial_01_fondamenti_linguaggio.md`, `tutorial_04_decoratori_generatori_context_manager.md`
> **Durata stimata:** 20-25 ore
> **Versione Python:** 3.12+

---

## Mappa concettuale

```
Concorrenza in Python
│
├── Thread (threading) — I/O-bound, GIL limita CPU
├── Processi (multiprocessing) — CPU-bound, overhead alto
└── Asyncio — I/O-bound, singolo thread, cooperativo  ← questo tutorial
    │
    ├── Event Loop — motore centrale
    │   ├── asyncio.run() — entry point
    │   ├── asyncio.Runner (3.11+) — controllo fine
    │   └── uvloop — implementazione C++ più veloce
    │
    ├── Coroutine (async def) — co-routine cooperative
    │   ├── await — sospende e cede controllo
    │   └── return — ritorna valore al chiamante
    │
    ├── Task — coroutine schedulata sull'event loop
    │   ├── asyncio.create_task() — lancia in background
    │   ├── asyncio.gather() — esegui N in parallelo
    │   ├── asyncio.TaskGroup (3.11+) — structured concurrency
    │   └── asyncio.wait_for() — timeout su singolo task
    │
    ├── Sincronizzazione
    │   ├── asyncio.Lock — mutex
    │   ├── asyncio.Semaphore — limitare concorrenza
    │   ├── asyncio.Event — flag attesa
    │   └── asyncio.Queue — producer/consumer
    │
    └── I/O asincrono
        ├── asyncio.open_connection() — TCP client
        ├── asyncio.start_server() — TCP server
        ├── aiofiles — file I/O asincrono
        └── httpx/aiohttp — HTTP client asincrono
```

---

# Parte A — Basi

---

## A1. Il problema della concorrenza I/O

> **Analogia:** Un cameriere tradizionale (sincrono) prende l'ordine al tavolo 1, va in cucina, aspetta che sia pronto, lo porta, poi va al tavolo 2. Un cameriere asincrono prende l'ordine al tavolo 1, lo passa in cucina, va subito al tavolo 2, poi al 3, e quando la cucina suona, torna a ritirare il piatto. Stesso numero di camerieri, tre volte più tavoli serviti.

```python
import time
import asyncio

# Sincrono — aspetta ogni operazione I/O
def scarica_sync(url: str) -> str:
    time.sleep(1)   # simula latenza di rete
    return f"Contenuto di {url}"

def main_sync():
    urls = ["https://a.com", "https://b.com", "https://c.com"]
    inizio = time.perf_counter()
    for url in urls:
        risultato = scarica_sync(url)
        print(risultato)
    print(f"Sync: {time.perf_counter() - inizio:.1f}s")   # ~3.0s

# Asincrono — interleave delle operazioni I/O
async def scarica_async(url: str) -> str:
    await asyncio.sleep(1)   # cede controllo durante l'attesa
    return f"Contenuto di {url}"

async def main_async():
    urls = ["https://a.com", "https://b.com", "https://c.com"]
    inizio = time.perf_counter()
    tasks = [scarica_async(url) for url in urls]
    risultati = await asyncio.gather(*tasks)
    for r in risultati:
        print(r)
    print(f"Async: {time.perf_counter() - inizio:.1f}s")  # ~1.0s

# asyncio.run() — entry point principale
asyncio.run(main_async())
```

---

## A2. Coroutine: `async def` e `await`

```python
import asyncio

# Una coroutine è una funzione che può essere sospesa
async def saluta(nome: str, ritardo: float) -> str:
    print(f"Inizio saluto a {nome}")
    await asyncio.sleep(ritardo)   # sospende qui senza bloccare
    messaggio = f"Ciao, {nome}!"
    print(f"Fine saluto a {nome}")
    return messaggio

# Chiamare una coroutine ritorna un oggetto coroutine — NON la esegue
coro = saluta("Anna", 0.5)
print(type(coro))   # <class 'coroutine'>

# Per eseguire serve await o asyncio.run()
async def principale():
    # await esegue la coroutine e aspetta il risultato
    risultato = await saluta("Anna", 0.5)
    print(risultato)

asyncio.run(principale())
```

**Regola fondamentale:** `await` può essere usato solo **dentro una funzione `async def`**. Non si può fare `await` nel codice sincrono normale.

---

## A3. Task: concorrenza reale

```python
import asyncio

async def operazione(nome: str, secondi: float) -> str:
    print(f"{nome}: start")
    await asyncio.sleep(secondi)
    print(f"{nome}: fine")
    return f"{nome} completata in {secondi}s"

async def con_gather():
    """gather — esegui N coroutine in parallelo, aspetta tutte."""
    inizio = asyncio.get_event_loop().time()

    risultati = await asyncio.gather(
        operazione("A", 1.0),
        operazione("B", 0.5),
        operazione("C", 0.8),
    )
    # Tutte e tre partono contemporaneamente
    # Tempo totale ≈ max(1.0, 0.5, 0.8) = 1.0s

    for r in risultati:
        print(r)

async def con_create_task():
    """create_task — lancia task e continua, raccogli dopo."""
    task_a = asyncio.create_task(operazione("A", 1.0), name="task-A")
    task_b = asyncio.create_task(operazione("B", 0.5), name="task-B")

    # Posso fare altro mentre i task girano...
    print("Task lanciati, faccio altro...")
    await asyncio.sleep(0.1)
    print("Aspetto i risultati...")

    ris_a = await task_a
    ris_b = await task_b
    print(ris_a, ris_b)

asyncio.run(con_gather())
asyncio.run(con_create_task())
```

---

## A4. TaskGroup (Python 3.11+) — Structured Concurrency

```python
import asyncio

async def scarica(url: str) -> str:
    await asyncio.sleep(0.5)
    return f"Dati da {url}"

async def con_taskgroup():
    """TaskGroup garantisce che tutti i task siano completati (o annullati)
    prima di uscire dal blocco with, anche in caso di eccezione."""

    risultati: list[str] = []

    async with asyncio.TaskGroup() as tg:
        tasks = [
            tg.create_task(scarica(f"https://api{i}.example.com"))
            for i in range(5)
        ]
    # Qui siamo sicuri che TUTTI i task sono terminati

    for t in tasks:
        risultati.append(t.result())

    return risultati

async def taskgroup_con_errore():
    """Se un task lancia eccezione, TaskGroup cancella gli altri
    e rilancia con ExceptionGroup."""
    async def fallisce():
        await asyncio.sleep(0.1)
        raise ValueError("qualcosa è andato storto")

    async def ok():
        await asyncio.sleep(0.5)
        return "ok"

    try:
        async with asyncio.TaskGroup() as tg:
            t1 = tg.create_task(ok())
            t2 = tg.create_task(fallisce())
    except* ValueError as eg:
        print(f"Errori: {eg.exceptions}")

asyncio.run(con_taskgroup())
asyncio.run(taskgroup_con_errore())
```

---

## A5. Timeout

```python
import asyncio

async def operazione_lenta() -> str:
    await asyncio.sleep(10)
    return "completata"

async def con_timeout():
    # asyncio.timeout — context manager (Python 3.11+)
    try:
        async with asyncio.timeout(2.0):
            risultato = await operazione_lenta()
    except asyncio.TimeoutError:
        print("Timeout!")

    # asyncio.wait_for — equivalente più vecchio
    try:
        risultato = await asyncio.wait_for(operazione_lenta(), timeout=2.0)
    except asyncio.TimeoutError:
        print("Timeout con wait_for!")

    # asyncio.timeout — con deadline assoluta
    deadline = asyncio.get_event_loop().time() + 5.0
    try:
        async with asyncio.timeout_at(deadline):
            risultato = await operazione_lenta()
    except asyncio.TimeoutError:
        print("Scaduta la deadline!")

asyncio.run(con_timeout())
```

---

# Parte B — Comprensione profonda

---

## B1. Event loop e asyncio.Runner

```python
import asyncio

# asyncio.run() — entry point semplice, crea e chiude l'event loop
asyncio.run(main())

# asyncio.Runner (Python 3.11+) — controllo più fine
# Utile per eseguire più coroutine nello stesso loop
with asyncio.Runner() as runner:
    risultato1 = runner.run(prima_coroutine())
    risultato2 = runner.run(seconda_coroutine())
    # Il loop è lo stesso per entrambe le chiamate

# Accedere all'event loop corrente (dentro async)
async def ispeziona_loop():
    loop = asyncio.get_event_loop()
    print(f"Loop: {loop}")
    print(f"Time: {loop.time():.3f}")
    print(f"Is running: {loop.is_running()}")
    print(f"Tasks: {asyncio.all_tasks()}")

# Schedulare da codice sincrono
async def task_da_schedulare():
    await asyncio.sleep(1)
    return "fatto"

# Se il loop è già in esecuzione (es. in Jupyter):
# asyncio.ensure_future(task_da_schedulare())
```

---

## B2. Sincronizzazione asincrona

```python
import asyncio
from collections import deque

# Lock — mutex per sezioni critiche
async def uso_lock():
    lock = asyncio.Lock()
    contatore = 0

    async def incrementa():
        nonlocal contatore
        async with lock:
            tmp = contatore
            await asyncio.sleep(0)   # simula operazione
            contatore = tmp + 1

    await asyncio.gather(*[incrementa() for _ in range(100)])
    print(contatore)   # 100 — nessuna race condition

# Semaphore — limitare concorrenza
async def uso_semaphore():
    """Massimo 3 richieste HTTP contemporanee."""
    sem = asyncio.Semaphore(3)

    async def richiesta(n: int) -> str:
        async with sem:   # al massimo 3 task attivi qui
            await asyncio.sleep(0.1)
            return f"risposta {n}"

    risultati = await asyncio.gather(*[richiesta(i) for i in range(20)])
    print(f"Completate {len(risultati)} richieste")

# Event — segnalazione tra task
async def uso_event():
    pronto = asyncio.Event()

    async def produttore():
        await asyncio.sleep(1)
        pronto.set()   # segnala che i dati sono pronti
        print("Produttore: dati pronti")

    async def consumatore():
        await pronto.wait()   # aspetta il segnale
        print("Consumatore: ricevuto segnale, processo")

    await asyncio.gather(produttore(), consumatore())

# Queue — producer/consumer pattern
async def uso_queue():
    coda: asyncio.Queue[str] = asyncio.Queue(maxsize=10)

    async def producer():
        for i in range(5):
            await asyncio.sleep(0.1)
            await coda.put(f"elemento-{i}")
            print(f"Prodotto: elemento-{i}")
        await coda.put(None)   # sentinella di fine

    async def consumer():
        while True:
            elemento = await coda.get()
            if elemento is None:
                break
            print(f"Consumato: {elemento}")
            coda.task_done()

    await asyncio.gather(producer(), consumer())
```

---

## B3. Pattern: context manager asincrono e async for

```python
import asyncio
from contextlib import asynccontextmanager

# Context manager asincrono
class ConnessioneAsincrona:
    def __init__(self, host: str):
        self.host = host
        self._connessione = None

    async def __aenter__(self) -> "ConnessioneAsincrona":
        print(f"Connessione a {self.host}...")
        await asyncio.sleep(0.1)   # handshake
        self._connessione = True
        return self

    async def __aexit__(self, *args) -> None:
        if self._connessione:
            await asyncio.sleep(0.05)   # graceful close
            self._connessione = None
            print(f"Disconnesso da {self.host}")

    async def invia(self, dati: str) -> str:
        await asyncio.sleep(0.1)
        return f"Echo: {dati}"


async def usa_connessione():
    async with ConnessioneAsincrona("localhost") as conn:
        risposta = await conn.invia("PING")
        print(risposta)

# asynccontextmanager — approccio più semplice
@asynccontextmanager
async def transazione_db(conn):
    try:
        await conn.begin()
        yield conn
        await conn.commit()
    except Exception:
        await conn.rollback()
        raise

# Async generator e async for
async def genera_numeri(n: int):
    for i in range(n):
        await asyncio.sleep(0.01)
        yield i

async def usa_async_for():
    async for numero in genera_numeri(5):
        print(f"Numero: {numero}")

    # Async comprehension
    risultati = [n async for n in genera_numeri(10)]
    print(risultati)
```

---

## B4. Eseguire codice sincrono in asyncio

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

def operazione_bloccante(n: int) -> int:
    """Funzione sincrona bloccante — es. libreria I/O legacy."""
    import time
    time.sleep(1)
    return n * 2

def calcolo_cpu_intensivo(n: int) -> int:
    """Operazione CPU-bound."""
    return sum(i ** 2 for i in range(n))

async def integra_sincrono():
    loop = asyncio.get_event_loop()

    # run_in_executor — esegui funzione sincrona in un thread pool
    # NON blocca l'event loop
    with ThreadPoolExecutor(max_workers=5) as executor:
        risultato = await loop.run_in_executor(
            executor, operazione_bloccante, 42
        )
        print(f"Thread executor: {risultato}")

    # Default executor (ThreadPoolExecutor)
    risultato2 = await loop.run_in_executor(None, operazione_bloccante, 10)
    print(f"Default executor: {risultato2}")

    # ProcessPoolExecutor per CPU-bound (bypassa il GIL)
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = [
            loop.run_in_executor(executor, calcolo_cpu_intensivo, 1_000_000)
            for _ in range(4)
        ]
        risultati = await asyncio.gather(*futures)
        print(f"Process executor: {risultati}")

asyncio.run(integra_sincrono())
```

---

## B5. Errori e cancellazione

```python
import asyncio

async def task_annullabile(nome: str) -> str:
    try:
        await asyncio.sleep(10)
        return f"{nome} completato"
    except asyncio.CancelledError:
        print(f"{nome}: annullamento richiesto, pulizia in corso...")
        # Pulizia risorse
        await asyncio.sleep(0.1)   # cleanup asincrono permesso
        raise   # OBBLIGATORIO: rilancia sempre CancelledError

async def gestione_cancellazione():
    task = asyncio.create_task(task_annullabile("operazione"))

    await asyncio.sleep(2)
    task.cancel()   # richiede l'annullamento

    try:
        await task
    except asyncio.CancelledError:
        print("Task annullato con successo")

# ExceptionGroup — gestire più eccezioni da TaskGroup
async def con_exception_group():
    async def può_fallire(n: int) -> int:
        if n % 2 == 0:
            raise ValueError(f"n={n} è pari")
        return n

    try:
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(può_fallire(i)) for i in range(6)]
    except* ValueError as eg:
        print(f"Catturate {len(eg.exceptions)} eccezioni ValueError:")
        for exc in eg.exceptions:
            print(f"  - {exc}")

asyncio.run(gestione_cancellazione())
asyncio.run(con_exception_group())
```

---

# Parte C — Esercizi pratici guidati

---

## C1. Rate limiter asincrono

```python
import asyncio
import time
from collections import deque

class RateLimiter:
    """Limita a N chiamate per secondo con sliding window."""

    def __init__(self, max_per_secondo: int) -> None:
        self.max_per_secondo = max_per_secondo
        self._chiamate: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquisisci(self) -> None:
        async with self._lock:
            ora = time.monotonic()
            # Rimuovi chiamate più vecchie di 1 secondo
            while self._chiamate and ora - self._chiamate[0] >= 1.0:
                self._chiamate.popleft()

            if len(self._chiamate) >= self.max_per_secondo:
                # Aspetta fino a quando una slot si libera
                attesa = 1.0 - (ora - self._chiamate[0])
                if attesa > 0:
                    await asyncio.sleep(attesa)

            self._chiamate.append(time.monotonic())

    async def __aenter__(self) -> "RateLimiter":
        await self.acquisisci()
        return self

    async def __aexit__(self, *args) -> None:
        pass


async def test_rate_limiter():
    limiter = RateLimiter(max_per_secondo=5)

    async def chiama_api(n: int) -> str:
        async with limiter:
            ts = time.monotonic()
            await asyncio.sleep(0.01)
            return f"Risposta {n} alle {ts:.2f}"

    inizio = time.monotonic()
    risultati = await asyncio.gather(*[chiama_api(i) for i in range(15)])
    durata = time.monotonic() - inizio
    print(f"15 chiamate completate in {durata:.1f}s (atteso ~3.0s per 5/s)")

asyncio.run(test_rate_limiter())
```

---

## C2. HTTP client con retry e timeout

```python
import asyncio
import random
from dataclasses import dataclass

@dataclass
class RispostaHTTP:
    status: int
    corpo: str
    latenza_ms: float

async def http_get(url: str, timeout: float = 5.0) -> RispostaHTTP:
    """Simula una chiamata HTTP con latenza variabile."""
    latenza = random.uniform(0.1, 2.0)
    async with asyncio.timeout(timeout):
        await asyncio.sleep(latenza)
        if random.random() < 0.3:   # 30% di fallimenti
            raise ConnectionError(f"Connessione fallita a {url}")
        return RispostaHTTP(200, f"OK da {url}", latenza * 1000)

async def get_con_retry(
    url: str,
    max_tentativi: int = 3,
    backoff_base: float = 0.5,
) -> RispostaHTTP:
    ultimo_errore: Exception | None = None

    for tentativo in range(max_tentativi):
        try:
            return await http_get(url)
        except (ConnectionError, asyncio.TimeoutError) as e:
            ultimo_errore = e
            if tentativo < max_tentativi - 1:
                attesa = backoff_base * (2 ** tentativo)
                print(f"Tentativo {tentativo+1} fallito ({e}), retry in {attesa:.1f}s")
                await asyncio.sleep(attesa)

    raise RuntimeError(f"Tutti {max_tentativi} tentativi falliti: {ultimo_errore}")

async def scrape_parallel(urls: list[str], max_concurrent: int = 5) -> list[RispostaHTTP | Exception]:
    """Scarica N URL in parallelo, max max_concurrent alla volta."""
    sem = asyncio.Semaphore(max_concurrent)
    risultati: list[RispostaHTTP | Exception] = []
    lock = asyncio.Lock()

    async def scarica_uno(url: str) -> None:
        async with sem:
            try:
                r = await get_con_retry(url)
                async with lock:
                    risultati.append(r)
            except Exception as e:
                async with lock:
                    risultati.append(e)

    await asyncio.gather(*[scarica_uno(url) for url in urls])
    return risultati

async def main():
    urls = [f"https://api.example.com/endpoint/{i}" for i in range(10)]
    risposte = await scrape_parallel(urls)
    ok = [r for r in risposte if isinstance(r, RispostaHTTP)]
    errori = [r for r in risposte if isinstance(r, Exception)]
    print(f"Successi: {len(ok)}, Errori: {len(errori)}")
    if ok:
        media_latenza = sum(r.latenza_ms for r in ok) / len(ok)
        print(f"Latenza media: {media_latenza:.0f}ms")

asyncio.run(main())
```

---

## C3. Pipeline asincrona producer-consumer

```python
import asyncio
import random
from dataclasses import dataclass, field

@dataclass
class Elemento:
    id: int
    dati: str

@dataclass
class ElementoProcessato:
    elemento: Elemento
    risultato: str

async def producer(coda: asyncio.Queue[Elemento | None], n: int) -> None:
    """Genera N elementi e li mette in coda."""
    for i in range(n):
        await asyncio.sleep(random.uniform(0.01, 0.05))
        elemento = Elemento(i, f"dati-{i}")
        await coda.put(elemento)
        print(f"Prodotto: {elemento.id}")
    await coda.put(None)   # sentinella di fine

async def processor(
    in_q: asyncio.Queue[Elemento | None],
    out_q: asyncio.Queue[ElementoProcessato | None],
    worker_id: int,
) -> None:
    """Preleva da in_q, processa, mette in out_q."""
    while True:
        elemento = await in_q.get()
        if elemento is None:
            # Propaga la sentinella agli altri worker e al consumatore
            await in_q.put(None)   # per gli altri worker
            await out_q.put(None)  # per il consumatore
            break
        await asyncio.sleep(random.uniform(0.02, 0.1))
        risultato = ElementoProcessato(elemento, f"elaborato-{elemento.id}-da-W{worker_id}")
        await out_q.put(risultato)
        in_q.task_done()

async def consumer(coda: asyncio.Queue[ElementoProcessato | None]) -> list[str]:
    """Raccoglie i risultati finali."""
    risultati: list[str] = []
    while True:
        ep = await coda.get()
        if ep is None:
            break
        risultati.append(ep.risultato)
        print(f"Consumato: {ep.risultato}")
    return risultati

async def pipeline():
    N_ELEMENTI = 20
    N_WORKER = 3

    in_queue: asyncio.Queue[Elemento | None] = asyncio.Queue(maxsize=10)
    out_queue: asyncio.Queue[ElementoProcessato | None] = asyncio.Queue()

    prod = asyncio.create_task(producer(in_queue, N_ELEMENTI))
    workers = [
        asyncio.create_task(processor(in_queue, out_queue, i))
        for i in range(N_WORKER)
    ]
    risultati = await consumer(out_queue)

    await prod
    await asyncio.gather(*workers)

    print(f"\nProcessati {len(risultati)} elementi con {N_WORKER} worker")

asyncio.run(pipeline())
```

---

# Parte D — Approfondimento per esperti

---

## D1. uvloop: event loop ad alte prestazioni

```python
# Installazione: pip install uvloop
import asyncio
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    print("uvloop attivo")
except ImportError:
    print("uvloop non disponibile, uso asyncio standard")

# uvloop è implementato in Cython/C++, 2-4x più veloce per I/O pesante
# Supporto: Linux e macOS (non Windows)

async def benchmark():
    """Confronto: 10.000 sleep(0) in loop."""
    for _ in range(10_000):
        await asyncio.sleep(0)

asyncio.run(benchmark())
```

---

## D2. Server TCP asincrono

```python
import asyncio

async def gestisci_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter
) -> None:
    addr = writer.get_extra_info("peername")
    print(f"Connessione da {addr}")

    try:
        while True:
            dati = await reader.read(1024)
            if not dati:
                break
            messaggio = dati.decode().strip()
            print(f"Ricevuto da {addr}: {messaggio}")

            risposta = f"Echo: {messaggio}\n"
            writer.write(risposta.encode())
            await writer.drain()   # flush del buffer

    except (ConnectionResetError, asyncio.IncompleteReadError):
        pass
    finally:
        writer.close()
        await writer.wait_closed()
        print(f"Disconnesso: {addr}")

async def avvia_server(host: str = "127.0.0.1", porta: int = 8888) -> None:
    server = await asyncio.start_server(gestisci_client, host, porta)
    addrs = ", ".join(str(s.getsockname()) for s in server.sockets)
    print(f"Server in ascolto su {addrs}")

    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(avvia_server())
```

---

## D3. Pattern avanzati: Supervisor

```python
import asyncio
import logging
from collections.abc import Callable, Awaitable

logger = logging.getLogger(__name__)

async def supervisor(
    nome: str,
    coro_factory: Callable[[], Awaitable],
    max_riavvii: int = 5,
    backoff: float = 1.0,
) -> None:
    """Supervisor che riavvia automaticamente una coroutine se crasha."""
    riavvii = 0
    while riavvii <= max_riavvii:
        try:
            await coro_factory()
            break   # completato con successo
        except asyncio.CancelledError:
            raise   # non riavviare se annullato
        except Exception as e:
            riavvii += 1
            if riavvii > max_riavvii:
                logger.error(f"[{nome}] Troppi riavvii ({max_riavvii}), abbandono")
                raise
            attesa = backoff * (2 ** (riavvii - 1))
            logger.warning(f"[{nome}] Crash ({e}), riavvio #{riavvii} tra {attesa:.1f}s")
            await asyncio.sleep(attesa)


# Worker con supervisor
async def main_supervisor():
    contatore = {"n": 0}

    async def worker_instabile():
        while True:
            contatore["n"] += 1
            if contatore["n"] % 3 == 0:
                raise RuntimeError("crash simulato!")
            await asyncio.sleep(0.5)
            print(f"Worker tick #{contatore['n']}")

    await supervisor("worker", lambda: worker_instabile(), max_riavvii=3)

asyncio.run(main_supervisor())
```

---

## D4. Integrazione con librerie sincrone: asyncio.to_thread

```python
import asyncio
import hashlib
import os

# asyncio.to_thread (Python 3.9+) — shortcut per run_in_executor con ThreadPoolExecutor
async def hash_file_asincrono(percorso: str) -> str:
    """Calcola SHA-256 di un file senza bloccare l'event loop."""
    def _hash_sync(path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    return await asyncio.to_thread(_hash_sync, percorso)

async def hash_multipli(percorsi: list[str]) -> dict[str, str]:
    tasks = {p: asyncio.to_thread(lambda path=p: hash_file_asincrono(path)) for p in percorsi}
    # Simpler:
    risultati = await asyncio.gather(*[hash_file_asincrono(p) for p in percorsi])
    return dict(zip(percorsi, risultati))
```

---

# Parte E — Riepilogo e prossimi passi

## Riepilogo

| Concetto | API | Quando usare |
|---|---|---|
| Coroutine semplice | `async def` + `await` | Qualsiasi operazione asincrona |
| Parallelismo N task | `asyncio.gather()` | Risultati di tutti N |
| Structured concurrency | `asyncio.TaskGroup` | Annullamento automatico se uno fallisce |
| Task background | `asyncio.create_task()` | Lancia senza aspettare subito |
| Timeout | `asyncio.timeout()` | Limite di tempo su qualsiasi await |
| Mutex | `asyncio.Lock()` | Sezione critica |
| Limite concorrenza | `asyncio.Semaphore(N)` | Max N operazioni contemporanee |
| Segnalazione | `asyncio.Event()` | Un task aspetta che un altro segnali |
| Coda | `asyncio.Queue()` | Producer-consumer |
| Codice sincrono | `asyncio.to_thread()` | Librerie legacy senza async |
| CPU-bound | `ProcessPoolExecutor` | Bypassa GIL |
| Performance | `uvloop` | 2-4x su Linux/macOS |

## Errori comuni

- **`RuntimeError: This event loop is already running`** — usare `asyncio.run()` solo nel codice di ingresso, non annidato
- **Dimenticare `await`** — chiamare una coroutine senza `await` ritorna l'oggetto, non lo esegue; Python 3.12 emette `RuntimeWarning`
- **Chiamare funzioni bloccanti dentro `async`** — usare `asyncio.to_thread()` o `run_in_executor()`
- **Non propagare `CancelledError`** — non catturare senza rilanciare
- **`asyncio.sleep(0)`** — cede il controllo all'event loop senza attendere; utile per non tenere troppo a lungo il loop

## Prossimi passi

- `tutorial_11_web_framework.md` — FastAPI è asincrono by default
- `tutorial_12_database.md` — SQLAlchemy async, asyncpg
- `tutorial_17_network_programming.md` — socket, HTTP/2, gRPC async
