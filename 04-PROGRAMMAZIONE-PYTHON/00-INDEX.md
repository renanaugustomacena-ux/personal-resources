# Indice — Python Professionale

> **Corso:** Python professionale — dal linguaggio alla produzione
> **Aggiornamento:** 2026-05-23
> **Moduli:** 33 + 2 case study + scaffolding
> **Percorso consigliato:** vedi [00-SYLLABUS.md](00-SYLLABUS.md)

---

## File di Scaffolding

| File | Scopo | Stato |
|------|-------|-------|
| [00-SYLLABUS.md](00-SYLLABUS.md) | Percorso formativo, fasi, prerequisiti, capstone | stable |
| [00-INDEX.md](00-INDEX.md) | Questo file — indice completo | stable |
| [00-GLOSSARIO.md](00-GLOSSARIO.md) | Glossario termini introdotti nel corso | stable |
| [00-BIBLIOGRAFIA.md](00-BIBLIOGRAFIA.md) | Fonti primarie consolidate | stable |
| [00-CAPSTONE.md](00-CAPSTONE.md) | Progetto finale: brief, deliverable, rubric | stable |
| [00-guida-allo-studio.md](00-guida-allo-studio.md) | Guida allo studio originale (legacy) | base |

---

## Moduli del Corso

### Fase 1 — Linguaggio Core

| # | Modulo | Sinossi | Stato |
|---|--------|---------|-------|
| 01 | [fondamenti-linguaggio.md](01-fondamenti-linguaggio.md) | Tipi, strutture dati base, control flow, funzioni, scope, PEP 8/20 | stable |
| 02 | [oop.md](02-oop.md) | Classi, ereditarietà, MRO, dunder methods, ABC, dataclass, slots | stable |
| 03 | [strutture-dati-avanzate.md](03-strutture-dati-avanzate.md) | Collections module, deque, defaultdict, Counter, heapq, bisect | stable |
| 04 | [decoratori-generatori-context-manager.md](04-decoratori-generatori-context-manager.md) | Closure, decorator parametrici, yield/send, contextlib | stable |
| 09 | [type-hints-e-mypy.md](09-type-hints-e-mypy.md) | PEP 484/604/612, TypeVar, Protocol, ParamSpec, mypy strict | stable |
| 21 | [design-patterns.md](21-design-patterns.md) | Strategy, Observer, Factory, Repository, CQRS, pattern Pythonic | stable |
| 22 | [clean-code.md](22-clean-code.md) | SOLID Python, naming, refactoring, code smell, complexity metrics | stable |

### Fase 2 — I/O, Dati e Validazione

| # | Modulo | Sinossi | Stato |
|---|--------|---------|-------|
| 05 | [gestione-file-io.md](05-gestione-file-io.md) | Pathlib, encoding UTF-8, CSV/JSON/YAML, binary I/O, mmap | stable |
| 06 | [regex-e-text-processing.md](06-regex-e-text-processing.md) | re module, lookahead/behind, named groups, performance tuning | stable |
| 07 | [error-handling-e-logging.md](07-error-handling-e-logging.md) | Exception hierarchy, ExceptionGroup (3.11), structlog, contextvars | stable |
| 12 | [database.md](12-database.md) | SQLAlchemy 2.0 (Mapped, mapped_column), async session, Alembic | stable |
| 13 | [rest-api.md](13-rest-api.md) | FastAPI, Pydantic v2 models, OpenAPI, dependency injection, auth | stable |
| 14 | [data-processing.md](14-data-processing.md) | pandas, Polars, Apache Arrow, ETL patterns, data pipeline | stable |
| 29 | [pydantic-e-validazione.md](29-pydantic-e-validazione.md) | Pydantic v2 Rust core, BaseModel, Field, validators, Settings | stable |

### Fase 3 — Network, Web e Sicurezza

| # | Modulo | Sinossi | Stato |
|---|--------|---------|-------|
| 11 | [web-framework.md](11-web-framework.md) | Flask 3.x, FastAPI lifespan, ASGI, Jinja2, middleware stack | stable |
| 15 | [web-scraping.md](15-web-scraping.md) | BeautifulSoup, Scrapy, Playwright, rate limiting, robots.txt | stable |
| 17 | [network-programming.md](17-network-programming.md) | Socket, asyncio streams, HTTP/2, gRPC, mTLS, DNS | stable |
| 18 | [sicurezza.md](18-sicurezza.md) | OWASP Python, secrets module, cryptography lib, SBOM, supply-chain | stable |

### Fase 4 — Specializzazioni

| # | Modulo | Sinossi | Stato |
|---|--------|---------|-------|
| 10 | [programmazione-asincrona.md](10-programmazione-asincrona.md) | asyncio.Runner, TaskGroup, timeout, uvloop, PEP 703 free-threading | stable |
| 16 | [automazione.md](16-automazione.md) | subprocess, fabric, ansible-runner, task scheduling, cron | stable |
| 19 | [cli-tools.md](19-cli-tools.md) | argparse, typer, rich, click, auto-completion, piping | stable |
| 20 | [gui.md](20-gui.md) | PySide6/Qt6, Tkinter, layout management, signals/slots | stable |
| 28 | [machine-learning-intro.md](28-machine-learning-intro.md) | scikit-learn, pipeline, cross-validation, feature engineering | stable |

### Fase 5 — Production e Operations

| # | Modulo | Sinossi | Stato |
|---|--------|---------|-------|
| 08 | [testing.md](08-testing.md) | pytest, fixtures, parametrize, mocking, coverage, hypothesis | stable |
| 23 | [packaging-distribuzione.md](23-packaging-distribuzione.md) | setup.py legacy, wheel, sdist, PyPI upload, packaging base | stable |
| 24 | [virtual-environments.md](24-virtual-environments.md) | venv, uv, pip-tools, lockfile, isolation patterns | stable |
| 25 | [performance.md](25-performance.md) | cProfile, py-spy, timeit, Cython, numba, C extension API | stable |
| 26 | [docker-per-python.md](26-docker-per-python.md) | Multi-stage, distroless, uv in Docker, health check, compose | stable |
| 27 | [ci-cd-per-python.md](27-ci-cd-per-python.md) | GHA, uv lock, ruff, mypy, pytest, coverage, OIDC publish | stable |
| 30 | [troubleshooting-e-guide-pratiche.md](30-troubleshooting-e-guide-pratiche.md) | Debug, pdb, breakpoint(), common pitfalls, recipes | stable |
| 31 | [osservabilita-otel-prometheus.md](31-osservabilita-otel-prometheus.md) | OTel SDK, traces, metrics, OTLP export, Prometheus, Grafana | stable |
| 32 | [packaging-distribuzione.md](32-packaging-distribuzione.md) | uv build, manylinux, PEP 660, Trusted Publishers, wheels | stable |
| 33 | [profiling-memoria-gc.md](33-profiling-memoria-gc.md) | tracemalloc, objgraph, GC tuning, memory leaks, optimization | stable |

---

## Materiale Supplementare

### Case Study

| File | Argomento |
|------|-----------|
| [99-CASE-STUDY/log4shell-python-equivalent.md](99-CASE-STUDY/log4shell-python-equivalent.md) | Log4Shell e parallelismo Python: injection via logging, mitigazione |
| [99-CASE-STUDY/colors.js-supply-chain.md](99-CASE-STUDY/colors.js-supply-chain.md) | Sabotaggio colors.js/faker.js e supply-chain Python (PyPI) |

### Esercizi Extra

| Directory | Contenuto |
|-----------|-----------|
| [99-ESERCIZI/](99-ESERCIZI/) | Lab e scenari pratici per modulo |
