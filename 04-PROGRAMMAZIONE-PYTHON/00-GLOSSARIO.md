# Glossario — Python Professionale

> **Aggiornamento:** 2026-05-23
> **Nota:** Termini introdotti nei moduli del corso. Per definizioni estese, consultare il modulo indicato.

---

## A

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **ABC** | Abstract Base Class — classe con metodi astratti (`abc.ABC`, `@abstractmethod`). | 02 |
| **Alembic** | Tool per database migration con SQLAlchemy (auto-generate, upgrade, downgrade). | 12 |
| **ASGI** | Asynchronous Server Gateway Interface — interfaccia async per web app Python. | 11, 13 |
| **`asyncio`** | Modulo stdlib per programmazione asincrona (event loop, coroutine, task). | 10 |
| **`asyncio.Runner`** | Context manager 3.11+ per eseguire coroutine da codice sincrono. | 10 |
| **`asyncio.TaskGroup`** | Structured concurrency 3.11+: gruppo di task con cancellazione automatica su errore. | 10 |
| **`asyncio.timeout()`** | Context manager 3.11+ per timeout su operazioni async. | 10 |

## B–C

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **`bandit`** | Static Application Security Testing (SAST) per Python. | 18 |
| **`BaseModel`** | Classe base Pydantic per modelli con validazione automatica. | 29 |
| **`BaseSettings`** | Pydantic class per caricare configurazione da env vars / .env / secrets. | 29 |
| **`bisect`** | Modulo stdlib per ricerca binaria e inserimento ordinato. | 03 |
| **`breakpoint()`** | Built-in 3.7+ che invoca il debugger (default: pdb). | 30 |
| **`click`** | Framework CLI con decoratori per comandi, opzioni, argomenti. | 19 |
| **`closure`** | Funzione interna che cattura variabili dallo scope esterno. | 04 |
| **`collections`** | Modulo stdlib: `deque`, `defaultdict`, `Counter`, `OrderedDict`, `namedtuple`. | 03 |
| **`contextlib`** | Modulo stdlib per creare context manager (`@contextmanager`, `suppress`, `ExitStack`). | 04 |
| **`contextvars`** | Modulo stdlib per propagazione contesto async-safe (correlation ID, trace context). | 07, 31 |
| **`cProfile`** | Profiler deterministico stdlib (C-based, low overhead). | 25, 33 |
| **`CycloneDX-py`** | Generatore SBOM (Software Bill of Materials) in formato CycloneDX per Python. | 18 |

## D

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **`dataclass`** | Decoratore stdlib che genera `__init__`, `__repr__`, `__eq__` automaticamente. | 02 |
| **`deque`** | Double-ended queue da `collections` — O(1) append/pop da entrambi i lati. | 03 |
| **`defaultdict`** | Dict con factory function per valori mancanti (no `KeyError`). | 03 |
| **decorator** | Funzione che wrappa un'altra funzione per aggiungere comportamento. | 04 |
| **dependency injection** | Pattern in cui le dipendenze sono passate come parametri (FastAPI `Depends()`). | 13 |
| **descriptor** | Oggetto che implementa `__get__`/`__set__`/`__delete__` per controllare accesso attributi. | 02 |
| **discriminated union** | Pydantic pattern con campo discriminatore per selezionare il modello corretto. | 29 |
| **`distroless`** | Immagine Docker minimale (Google) senza shell/package manager. | 26 |
| **dunder** | "Double underscore" — metodi speciali Python (`__init__`, `__repr__`, `__eq__`). | 02 |

## E–F

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **`ExceptionGroup`** | 3.11+ container per eccezioni multiple concorrenti (`except*` per cattura selettiva). | 07 |
| **f-string** | Formatted string literal (`f"..."`) — embedding espressioni direttamente nella stringa. | 01 |
| **`fabric`** | Libreria per esecuzione comandi remoti via SSH. | 16 |
| **FastAPI** | Web framework async moderno: auto-docs OpenAPI, dependency injection, Pydantic integration. | 11, 13 |
| **`Field()`** | Pydantic function per definire constraint su campi modello (default, alias, ge, le, pattern). | 29 |
| **fixture** | pytest: funzione che prepara stato per i test (`@pytest.fixture`, scope, autouse). | 08 |
| **`functools.wraps`** | Decoratore che preserva metadata della funzione wrappata (name, docstring). | 04 |

## G–H

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **GC** | Garbage Collector — gestione automatica memoria (reference counting + cycle detector). | 33 |
| **generator** | Funzione con `yield` che produce valori lazy (iterator protocol). | 04 |
| **GIL** | Global Interpreter Lock — mutex che impedisce esecuzione parallela di bytecode Python. | 10, 25 |
| **`heapq`** | Modulo stdlib per priority queue (min-heap). | 03 |
| **`httpx`** | HTTP client moderno con supporto async, HTTP/2, e streaming. | 17 |
| **`hypothesis`** | Property-based testing: genera input casualmente secondo strategia. | 08 |

## I–L

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **`Mapped[T]`** | SQLAlchemy 2.0 type annotation per colonne ORM. | 12 |
| **`mapped_column()`** | SQLAlchemy 2.0 function per definire colonne con tipo inferito da annotation. | 12 |
| **`manylinux`** | Standard per wheel binarie portable su distribuzioni Linux. | 32 |
| **`mmap`** | Memory-mapped file — accesso file come buffer in memoria. | 05 |
| **MRO** | Method Resolution Order — ordine di ricerca metodi in ereditarietà multipla (C3 linearization). | 02 |
| **`mypy`** | Static type checker per Python (strict mode per massima copertura). | 09 |

## N–O

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **`numba`** | JIT compiler per funzioni numeriche Python (LLVM backend). | 25 |
| **`objgraph`** | Tool per visualizzare reference graph di oggetti Python (debug memory leaks). | 33 |
| **OTLP** | OpenTelemetry Protocol — protocollo standard per trasmissione telemetry data. | 31 |
| **OTel** | OpenTelemetry — framework vendor-neutral per traces, metrics, logs. | 31 |

## P

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **`pandas`** | Libreria per data manipulation e analysis (DataFrame, Series). | 14 |
| **`parametrize`** | pytest decorator per eseguire test con input multipli. | 08 |
| **`Pathlib`** | Modulo stdlib per manipolazione path filesystem (object-oriented). | 05 |
| **PEP** | Python Enhancement Proposal — documento di design per features e standard Python. | 01 |
| **`pip-audit`** | Scanner CVE per dipendenze Python installate. | 18 |
| **`Polars`** | DataFrame library Rust-core: performance superiori a pandas, API lazy. | 14 |
| **`pre-commit`** | Framework per git hooks automatici (ruff, mypy, tests). | 27 |
| **`Protocol`** | typing: structural subtyping (duck typing statico). | 09 |
| **Pydantic v2** | Data validation library con core Rust (pydantic-core) per performance. | 29 |
| **`pyproject.toml`** | File di configurazione standard per progetti Python (PEP 621). | 32 |
| **`pyright`** | Type checker Microsoft (più veloce di mypy, integrato in VS Code). | 09 |
| **`py-spy`** | Sampling profiler per Python (low overhead, attach a processo running). | 25, 33 |
| **`pytest`** | Framework di testing standard (fixtures, parametrize, plugin ecosystem). | 08 |

## R–S

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **`rich`** | Libreria per output terminale formattato (tabelle, progress bar, syntax highlight). | 19 |
| **`ruff`** | Linter+formatter Rust-based (sostituisce flake8+isort+black). | 09, 27 |
| **SBOM** | Software Bill of Materials — inventario completo delle dipendenze software. | 18 |
| **`scikit-learn`** | Libreria ML classica (classification, regression, clustering, pipeline). | 28 |
| **`secrets`** | Modulo stdlib per generazione token crittograficamente sicuri. | 18 |
| **`selectinload`** | SQLAlchemy loading strategy che evita N+1 con query separate per relationship. | 12 |
| **`slots`** | `__slots__` — ottimizzazione memoria per classi (no `__dict__`). | 02 |
| **`structlog`** | Libreria per structured logging (JSON output, processors, binding). | 07 |
| **SQLAlchemy 2.0** | ORM Python con nuovo stile declarativo (`Mapped`, `mapped_column`, async). | 12 |

## T

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **`TaskGroup`** | Alias per `asyncio.TaskGroup` — structured concurrency. | 10 |
| **`testcontainers`** | Libreria per container Docker effimeri nei test (PostgreSQL, Redis, etc.). | 08 |
| **`timeit`** | Modulo stdlib per micro-benchmarking di codice. | 25 |
| **`tracemalloc`** | Modulo stdlib per tracciare allocazioni memoria (snapshot, diff, traceback). | 33 |
| **Trusted Publishers** | PyPI OIDC mechanism per publish senza password (GitHub Actions → PyPI). | 32 |
| **`TypeVar`** | typing: variabile di tipo per generics (`T = TypeVar('T')`). | 09 |
| **`typer`** | Framework CLI moderno basato su type hints (builds on click). | 19 |

## U–Z

| Termine | Definizione | Modulo |
|---------|-------------|--------|
| **`uv`** | Package manager Rust-based (sostituisce pip+venv+pip-tools). | 24, 32 |
| **`uvloop`** | Event loop ad alte prestazioni (Cython wrapper di libuv). | 10, 11 |
| **`venv`** | Modulo stdlib per creazione virtual environment isolati. | 24 |
| **`wheel`** | Formato di distribuzione binaria Python (.whl). | 23, 32 |
| **WSGI** | Web Server Gateway Interface — interfaccia sincrona per web app Python. | 11 |
| **`yield`** | Keyword che rende una funzione un generator (lazy evaluation). | 04 |

---

> **Conteggio termini:** ~100
> **Ultimo aggiornamento:** 2026-05-23
