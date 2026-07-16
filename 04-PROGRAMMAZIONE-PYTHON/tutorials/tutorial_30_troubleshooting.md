# Tutorial 30 — Troubleshooting Python: Debugging, Logging, Diagnostica

> **Companion a:** `30-troubleshooting.md`
> **Scope:** pdb, logging strutturato, traceback, diagnostica errori comuni, py-spy
> **Prerequisiti:** `tutorial_01_fondamenti_linguaggio.md`, `tutorial_10_programmazione_asincrona.md`
> **Durata stimata:** 10-14 ore

---

## Mappa concettuale

```
Troubleshooting Python
│
├── Debugging
│   ├── pdb — debugger integrato
│   ├── breakpoint() — Python 3.7+
│   ├── ipdb / pdb++ — enhanced debugger
│   ├── VS Code debugger — GUI
│   └── debugpy — remote debugging
│
├── Logging strutturato
│   ├── logging stdlib — configurazione
│   ├── structlog — log strutturati (JSON)
│   ├── Livelli: DEBUG/INFO/WARNING/ERROR/CRITICAL
│   └── Correlation ID — tracciabilità
│
├── Analisi errori
│   ├── traceback — stack trace
│   ├── sys.exc_info() — eccezione corrente
│   ├── faulthandler — crash dump
│   └── cgitb — traceback dettagliato
│
├── Diagnostica performance
│   ├── py-spy — profiler non-intrusivo
│   ├── memory-profiler — uso RAM
│   └── objgraph — reference leak
│
└── Errori comuni
    ├── ImportError / ModuleNotFoundError
    ├── AttributeError — typo su attributi
    ├── RuntimeError — asyncio
    ├── RecursionError — stack overflow
    └── MemoryError — dataset troppo grande
```

---

# Parte A — Debugging

---

## A1. pdb e breakpoint()

```python
import pdb

def calcola_media(numeri: list[float]) -> float:
    totale = sum(numeri)
    # Breakpoint — attiva il debugger qui
    breakpoint()   # equivalente a pdb.set_trace() in Python 3.7+
    n = len(numeri)
    return totale / n   # ZeroDivisionError se lista vuota!

# Comandi pdb principali:
# h         — help
# n (next)  — esegui riga corrente, vai alla prossima
# s (step)  — entra nella funzione chiamata
# c (cont)  — continua fino al prossimo breakpoint
# q (quit)  — esci dal debugger
# p var     — stampa variabile
# pp var    — pretty print variabile
# l         — mostra codice corrente
# u / d     — su/giù nello stack
# w         — stampa stack trace
# b 42      — imposta breakpoint alla riga 42
# tbreak    — breakpoint temporaneo (si rimuove dopo il primo hit)

# pdb post-mortem — analizza dopo un crash
def debug_dopo_crash():
    try:
        calcola_media([])
    except Exception:
        pdb.post_mortem()   # entra nel debugger con il contesto del crash
```

> **Analogia:** Il debugger è come una pausa sul video di un'animazione: puoi fermare il programma in un punto preciso, guardare cosa c'è dentro ogni variabile, muoverti riga per riga, e capire esattamente perché qualcosa non funziona. Molto più potente di un `print()` — puoi esplorare interattivamente senza modificare il codice.

---

## A2. Debugging asyncio

```python
import asyncio
import logging

# Abilita debug mode per asyncio
# Mostra coroutine lente, task non awaited, etc.
asyncio.run(main(), debug=True)
# oppure:
# PYTHONASYNCIODEBUG=1 python mio_script.py

# Logging asyncio
logging.getLogger("asyncio").setLevel(logging.DEBUG)

async def diagnostica_task():
    """Mostra tutti i task in esecuzione."""
    tasks = asyncio.all_tasks()
    print(f"Task attivi: {len(tasks)}")
    for task in tasks:
        print(f"  {task.get_name()}: {task.get_coro().__name__}")

# Trovare coroutine dimenticate
import warnings
warnings.filterwarnings("error", category=RuntimeWarning)
# RuntimeWarning: coroutine 'x' was never awaited → adesso è un errore
```

---

# Parte B — Logging strutturato

---

## B1. Configurazione logging stdlib

```python
import logging
import logging.config
import sys
from pathlib import Path

# Configurazione YAML/dict
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d — %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "standard",
            "level": "DEBUG",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/app.log",
            "maxBytes": 10 * 1024 * 1024,   # 10 MB
            "backupCount": 5,
            "formatter": "json",
            "level": "INFO",
        },
    },
    "loggers": {
        "": {   # root logger
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
        "sqlalchemy.engine": {"level": "WARNING"},
        "uvicorn.access": {"level": "WARNING"},
    },
}

Path("logs").mkdir(exist_ok=True)
logging.config.dictConfig(LOGGING_CONFIG)

logger = logging.getLogger(__name__)
logger.info("Applicazione avviata")
logger.warning("Attenzione!", extra={"utente_id": 42, "endpoint": "/api/dati"})
```

---

## B2. structlog: logging strutturato professionale

```python
# pip install structlog
import structlog
import logging

def configura_structlog(livello: str = "INFO", formato: str = "json") -> None:
    """Configura structlog per produzione o sviluppo."""
    livello_num = getattr(logging, livello.upper())

    if formato == "json":
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.BoundLogger,
        cache_logger_on_first_use=True,
    )

configura_structlog(formato="console")
log = structlog.get_logger()

# Logging con contesto strutturato
log.info("Richiesta ricevuta", metodo="GET", path="/api/prodotti", utente_id=42)
log.warning("Stock basso", prodotto_id=7, stock_rimanente=2, soglia=5)

# Binding contesto per una richiesta
log_richiesta = log.bind(request_id="abc-123", utente_id=42)
log_richiesta.info("Elaborazione iniziata")
log_richiesta.info("Query eseguita", ms=12)
log_richiesta.info("Elaborazione completata", codice=200)

# Context vars — automaticamente iniettate in tutti i log
import structlog.contextvars

async def middleware_logging(request, call_next):
    import uuid
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=str(uuid.uuid4()),
        metodo=request.method,
        path=str(request.url.path),
    )
    return await call_next(request)
```

---

# Parte C — Analisi errori

---

## C1. Traceback e exception handling

```python
import traceback
import sys

def analizza_eccezione():
    try:
        operazione_complessa()
    except Exception as e:
        # Informazioni complete sull'eccezione
        tipo, valore, tb = sys.exc_info()

        print(f"Tipo: {tipo.__name__}")
        print(f"Messaggio: {valore}")
        print("Stack trace:")
        print(traceback.format_exc())

        # Lista di frame
        frames = traceback.extract_tb(tb)
        for frame in frames:
            print(f"  File: {frame.filename}, Riga: {frame.lineno}, Funzione: {frame.name}")
            print(f"  Codice: {frame.line}")

def operazione_complessa():
    raise ValueError("Questo è l'errore!")

def gestore_eccezioni_globale(tipo, valore, tb):
    """Hook per eccezioni non gestite."""
    import logging
    logger = logging.getLogger("unhandled")
    logger.critical(
        "Eccezione non gestita",
        exc_info=(tipo, valore, tb),
        extra={"tipo": tipo.__name__},
    )

sys.excepthook = gestore_eccezioni_globale

# faulthandler — dump su crash SIGSEGV
import faulthandler
faulthandler.enable()   # scrive su stderr su crash
# faulthandler.enable(file=open("crash.log", "w"))
```

---

# Parte D — Errori comuni e soluzioni

---

## D1. Guida rapida agli errori più frequenti

```python
# 1. ModuleNotFoundError
# ImportError: No module named 'httpx'
# Soluzione: uv add httpx

# 2. AttributeError su None
risultato = None
# risultato.upper()   # AttributeError: 'NoneType' has no attribute 'upper'
# Soluzione: usare Optional e controllare prima
if risultato is not None:
    risultato.upper()
# Oppure: risultato = funzione() or ""

# 3. RecursionError — stack overflow
import sys
sys.getrecursionlimit()   # 1000 di default
sys.setrecursionlimit(5000)   # aumenta se necessario (attenzione!)
# Meglio: convertire ricorsione in iterazione

# 4. MemoryError su dataset grandi
# Soluzione: usare generatori o leggere in chunk
import pandas as pd
for chunk in pd.read_csv("file_grande.csv", chunksize=10_000):
    processa(chunk)

# 5. asyncio "This event loop is already running"
# In Jupyter: usare nest_asyncio
# import nest_asyncio; nest_asyncio.apply()
# In script: usare asyncio.run() solo al livello più alto

# 6. UnicodeDecodeError su file
# Soluzione: specificare encoding o usare errors='replace'
with open("file.txt", encoding="utf-8", errors="replace") as f:
    contenuto = f.read()

# 7. PicklingError in multiprocessing
# Lambda e classi locali non possono essere serializzati
# Usare funzioni al livello di modulo

# 8. SSL: CERTIFICATE_VERIFY_FAILED
# Mai disabilitare verify in produzione!
# In sviluppo con certificato self-signed:
import httpx
client = httpx.Client(verify=False)   # SOLO sviluppo locale
```

---

# Parte E — Riepilogo

## Checklist debug sistematico

1. **Leggi il traceback** — ultimo frame = punto del crash
2. **Riproduci** il problema in isolamento
3. **Aggiungi logging** nei punti chiave
4. **Usa breakpoint()** per ispezionare lo stato
5. **Controlla i tipi** — `type(var)`, `isinstance(var, tipo)`
6. **Verifica i valori None** — causa #1 di AttributeError
7. **Cerca in StackOverflow** l'errore esatto
8. **Scrivi un test** che riproduce il bug prima di fixarlo

## Livelli di logging: quando usarli

| Livello | Quando |
|---|---|
| `DEBUG` | Dettagli di sviluppo, disabilitato in prod |
| `INFO` | Operazioni normali, flusso applicazione |
| `WARNING` | Situazione anomala ma recuperabile |
| `ERROR` | Errore che impedisce un'operazione specifica |
| `CRITICAL` | Errore che mette a rischio il sistema |

## Prossimi passi

- `tutorial_31_otel.md` — observability con OpenTelemetry
- `tutorial_33_profiling.md` — profiling avanzato con py-spy
