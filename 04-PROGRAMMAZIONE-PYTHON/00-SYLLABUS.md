# Syllabus — Python Professionale (dal linguaggio alla produzione)

> **Lingua:** italiano · **Aggiornamento:** 2026-05-23
> **Versioni:** Python 3.12+ (compatibilità 3.11+); uv 0.4+; ruff 0.5+; Pydantic 2.x; FastAPI 0.110+; SQLAlchemy 2.0; pytest 8.x; OpenTelemetry SDK 1.x.
> **Moduli:** 33 + 2 case study + scaffolding
> **Tempo stimato:** 16-20 settimane (studio part-time) + 4-6 settimane capstone

---

## Identità

**"Python professionale"** — Python idiomatico moderno + production-grade tooling. Dal linguaggio core alle applicazioni enterprise: type system, async, web framework, database, testing, packaging, observability, security, deploy.

**Target:** competent → proficient. Capace di progettare e deployare un servizio FastAPI con OTel tracing, structured logging, Pydantic v2 validation, SQLAlchemy 2.0 async, uv packaging, CI con pip-audit, Docker distroless, deploy K8s.

## Prerequisiti

Programmazione di base (variabili, cicli, funzioni); Linux/CLI fluente (corso 02); Git base (corso 07).

## Obiettivi di Apprendimento

Al completamento del corso, lo studente sarà in grado di:

1. Scrivere Python idiomatico secondo PEP 8/257/20 con type hints completi (PEP 484/604/612).
2. Utilizzare `uv` per dependency management e `ruff` per linting/formatting.
3. Implementare data validation con Pydantic v2 (Rust core) e pattern avanzati (discriminated unions, custom validators).
4. Progettare database layer con SQLAlchemy 2.0 (`Mapped`, `mapped_column`, async session) e Alembic migrations.
5. Sviluppare API RESTful con FastAPI: lifespan, dependency injection, ASGI, uvloop.
6. Programmare asincrono con `asyncio.Runner`, `TaskGroup`, `timeout()`, comprendendo le implicazioni di PEP 703 (free-threading).
7. Implementare structured logging con `structlog` e correlation ID via `contextvars`.
8. Strumentare applicazioni con OpenTelemetry: traces, metrics, log correlation, OTLP export.
9. Gestire supply-chain security: `pip-audit`, SBOM con CycloneDX-py, PyPI Trusted Publishers.
10. Profilare applicazioni con `py-spy`, `tracemalloc`, e ottimizzare GC tuning.
11. Pacchettizzare e distribuire con `uv build`, manylinux wheels, PEP 660, Trusted Publishers.
12. Dockerizzare con multi-stage build, distroless, e configurare CI/CD Python-idiomatic.

## Struttura del Corso

### Fase 1 — Linguaggio Core (settimane 1-4)

| # | Modulo | Argomenti chiave |
|---|--------|-----------------|
| 01 | [Fondamenti linguaggio](01-fondamenti-linguaggio.md) | Tipi, strutture dati, control flow, funzioni, scope, PEP 8 |
| 02 | [OOP](02-oop.md) | Classi, ereditarietà, MRO, dunder, ABC, dataclass, slots |
| 03 | [Strutture dati avanzate](03-strutture-dati-avanzate.md) | Collections, deque, defaultdict, Counter, heapq, bisect |
| 04 | [Decoratori, generatori, CM](04-decoratori-generatori-context-manager.md) | Closure, decorator con parametri, yield, contextlib |
| 09 | [Type hints e mypy](09-type-hints-e-mypy.md) | PEP 484/604/612, TypeVar, Protocol, mypy strict, pyright |
| 21 | [Design patterns](21-design-patterns.md) | Strategy, Observer, Factory, Singleton, Repository, CQRS |
| 22 | [Clean code](22-clean-code.md) | SOLID, naming, refactoring, code smell, complexity |

### Fase 2 — I/O, Dati e Validazione (settimane 5-7)

| # | Modulo | Argomenti chiave |
|---|--------|-----------------|
| 05 | [Gestione file I/O](05-gestione-file-io.md) | Pathlib, encoding, CSV, JSON, YAML, binary, mmap |
| 06 | [Regex e text processing](06-regex-e-text-processing.md) | re, lookahead/behind, named groups, performance |
| 07 | [Error handling e logging](07-error-handling-e-logging.md) | Exception hierarchy, ExceptionGroup, structlog, contextvars |
| 12 | [Database](12-database.md) | SQLAlchemy 2.0, Mapped/mapped_column, async, Alembic |
| 13 | [REST API](13-rest-api.md) | FastAPI, Pydantic v2 models, OpenAPI, dependency injection |
| 14 | [Data processing](14-data-processing.md) | pandas, Polars, Apache Arrow, ETL patterns |
| 29 | [Pydantic e validazione](29-pydantic-e-validazione.md) | v2 Rust core, BaseModel, Field, validators, settings |

### Fase 3 — Network, Web e Sicurezza (settimane 8-10)

| # | Modulo | Argomenti chiave |
|---|--------|-----------------|
| 11 | [Web framework](11-web-framework.md) | Flask 3.x, FastAPI lifespan, ASGI, Jinja2, middleware |
| 15 | [Web scraping](15-web-scraping.md) | BeautifulSoup, Scrapy, Playwright, rate limiting, ethics |
| 17 | [Network programming](17-network-programming.md) | Socket, asyncio streams, HTTP/2, gRPC, mTLS |
| 18 | [Sicurezza](18-sicurezza.md) | OWASP, secrets, cryptography lib, SBOM, supply-chain |

### Fase 4 — Specializzazioni (settimane 11-13)

| # | Modulo | Argomenti chiave |
|---|--------|-----------------|
| 10 | [Programmazione asincrona](10-programmazione-asincrona.md) | asyncio.Runner, TaskGroup, timeout, uvloop, PEP 703 |
| 16 | [Automazione](16-automazione.md) | subprocess, fabric, ansible-runner, task scheduling |
| 19 | [CLI tools](19-cli-tools.md) | argparse, typer, rich, click, auto-completion |
| 20 | [GUI](20-gui.md) | PySide6/Qt6, Tkinter, layout, signals/slots, packaging |
| 28 | [Machine learning intro](28-machine-learning-intro.md) | scikit-learn, pipeline, cross-validation, feature eng |

### Fase 5 — Production e Operations (settimane 14-18)

| # | Modulo | Argomenti chiave |
|---|--------|-----------------|
| 08 | [Testing](08-testing.md) | pytest, fixtures, parametrize, mocking, coverage, hypothesis |
| 23 | [Packaging base](23-packaging-distribuzione.md) | setup.py legacy, wheel, sdist, PyPI upload |
| 24 | [Virtual environments](24-virtual-environments.md) | venv, uv, pip-tools, lockfile, isolation |
| 25 | [Performance](25-performance.md) | cProfile, py-spy, timeit, Cython, numba, C extension |
| 26 | [Docker per Python](26-docker-per-python.md) | Multi-stage, distroless, uv in Docker, health check |
| 27 | [CI/CD per Python](27-ci-cd-per-python.md) | GHA, uv lock, ruff, mypy, pytest, coverage, OIDC |
| 30 | [Troubleshooting](30-troubleshooting-e-guide-pratiche.md) | Debug, pdb, breakpoint(), common pitfalls, recipes |
| 31 | [Osservabilità OTel](31-osservabilita-otel-prometheus.md) | OTel SDK, traces, metrics, OTLP, Prometheus, Grafana |
| 32 | [Packaging avanzato](32-packaging-distribuzione.md) | uv build, manylinux, PEP 660, Trusted Publishers |
| 33 | [Profiling memoria GC](33-profiling-memoria-gc.md) | tracemalloc, objgraph, GC tuning, memory leaks |

### Fase 6 — Capstone (settimane 19-24)

Vedi [00-CAPSTONE.md](00-CAPSTONE.md) per il brief completo.

---

## Materiale Supplementare

| Risorsa | Scopo |
|---------|-------|
| [00-INDEX.md](00-INDEX.md) | Indice completo con sinossi |
| [00-GLOSSARIO.md](00-GLOSSARIO.md) | Glossario termini del corso |
| [00-BIBLIOGRAFIA.md](00-BIBLIOGRAFIA.md) | Fonti primarie consolidate |
| [00-CAPSTONE.md](00-CAPSTONE.md) | Progetto finale: brief, deliverable, rubric |
| [00-guida-allo-studio.md](00-guida-allo-studio.md) | Guida allo studio originale (legacy) |
| [99-CASE-STUDY/](99-CASE-STUDY/) | Case study: Log4Shell, colors.js supply-chain |
| [99-ESERCIZI/](99-ESERCIZI/) | Esercizi aggiuntivi per modulo |

---

## Valutazione

| Componente | Peso |
|------------|------|
| Capstone: FastAPI Service + Pydantic v2 | 25% |
| Capstone: SQLAlchemy 2.0 + Alembic | 15% |
| Capstone: OTel + Structured Logging | 15% |
| Capstone: Testing ≥ 80% coverage | 15% |
| Capstone: Packaging uv + Docker | 15% |
| Capstone: CI/CD + Security | 15% |

**Pass ≥ 70%, Distinction ≥ 90%.** Vedi [00-CAPSTONE.md](00-CAPSTONE.md) per la rubric dettagliata.
