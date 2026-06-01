# Capstone — Python Professionale

> **Tempo stimato:** 30-50 ore in 4-6 settimane
> **Livello:** competent → proficient
> **Prerequisiti:** completamento di tutti i moduli del corso (Fasi 1-5)
> **Aggiornamento:** 2026-05-23

---

## Scenario

Sei il backend developer principale di una startup SaaS che gestisce inventory per piccoli negozi. Il tuo compito è progettare e implementare un servizio FastAPI production-grade con autenticazione, database async, observability completa, pipeline CI/CD e deploy containerizzato.

---

## Deliverable

### D1 — Progetto e Struttura (4-6 ore)

1. **Inizializzazione progetto con uv**:
   - `uv init` con `pyproject.toml` PEP 621
   - Dependency groups: `[project.dependencies]`, `[project.optional-dependencies.dev]`
   - `uv lock` per lockfile deterministico
   - Struttura src-layout: `src/inventario/`, `tests/`, `migrations/`

2. **Tooling configurato**:
   - `ruff` per linting e formatting (in `pyproject.toml`)
   - `mypy` strict mode con `pyproject.toml` config
   - `pre-commit` hooks per ruff + mypy
   - `.python-version` pinned a 3.12+

### D2 — API FastAPI + Pydantic v2 (8-10 ore)

1. **Modelli Pydantic v2** per:
   - `Product` (id, name, sku, price, quantity, category, created_at)
   - `Order` (id, items, total, status, customer_id)
   - `User` (id, email, role, hashed_password)
   - Discriminated union per tipi prodotto (fisico/digitale)
   - Custom validators (SKU format, price positive, quantity non-negative)
   - Settings model con `BaseSettings` (database URL, JWT secret, OTel endpoint)

2. **Endpoint REST**:
   - CRUD prodotti con paginazione cursor-based
   - CRUD ordini con stato (draft → confirmed → shipped → delivered)
   - Autenticazione JWT httpOnly (login, refresh, logout)
   - Dependency injection per database session, current user, permissions
   - Rate limiting middleware
   - CORS configurato restrittivamente

3. **FastAPI lifespan**:
   - Database pool startup/shutdown
   - OTel provider initialization
   - Background task scheduler

### D3 — Database SQLAlchemy 2.0 + Alembic (6-8 ore)

1. **Modelli ORM** con SQLAlchemy 2.0:
   - `Mapped[int]`, `mapped_column()`, relationship con back_populates
   - AsyncSession con `async_sessionmaker`
   - Repository pattern per ogni entità
   - Indici ottimizzati (composite, partial)

2. **Alembic migrations**:
   - Auto-generation da modelli
   - Migration per schema iniziale
   - Migration per aggiunta campo
   - Downgrade testato
   - `env.py` configurato per async

3. **Query patterns**:
   - Eager loading con `selectinload` per evitare N+1
   - Paginazione cursor-based (non offset)
   - Transaction management con context manager

### D4 — Observability OTel + Structured Logging (6-8 ore)

1. **OpenTelemetry**:
   - TracerProvider con OTLP exporter (gRPC)
   - Auto-instrumentation: FastAPI, SQLAlchemy, httpx
   - Custom spans per business logic (order processing)
   - Span attributes con semantic conventions
   - MeterProvider: request latency histogram, active orders gauge, order value counter

2. **Structured Logging**:
   - `structlog` configurato con JSON output
   - Correlation ID via `contextvars` (propagato a ogni log entry)
   - Request ID middleware (X-Request-ID)
   - Log level per environment (DEBUG dev, INFO prod)
   - Trace-log correlation (trace_id nei log)

3. **Stack di monitoring** (docker-compose):
   - Jaeger o Tempo per traces
   - Prometheus per metrics
   - Grafana con dashboard preconfigurata

### D5 — Testing ≥ 80% Coverage (4-6 ore)

1. **Test suite**:
   - Unit test per modelli Pydantic (validation, serialization)
   - Unit test per repository (con database test PostgreSQL)
   - Integration test per endpoint (httpx AsyncClient + testcontainers)
   - Fixture conftest.py con database setup/teardown
   - `hypothesis` per property-based testing su modelli

2. **Coverage e qualità**:
   - Coverage ≥ 80% con `pytest-cov`
   - Branch coverage abilitato
   - `pytest.ini` / `pyproject.toml` config

### D6 — Docker + CI/CD (4-6 ore)

1. **Dockerfile multi-stage**:
   - Stage builder: `uv sync --frozen`
   - Stage runtime: `gcr.io/distroless/python3-debian12` o slim
   - Non-root user
   - Health check endpoint (`/health`)
   - `.dockerignore` completo

2. **docker-compose.yml**:
   - App service
   - PostgreSQL con volume
   - Jaeger + Prometheus + Grafana (monitoring stack)
   - Network isolation

3. **CI pipeline (GitHub Actions)**:
   - `uv sync` per dependency install
   - `ruff check` + `ruff format --check`
   - `mypy --strict`
   - `pytest --cov --cov-fail-under=80`
   - `pip-audit` per vulnerability scan
   - Build e push Docker image
   - OIDC per PyPI (opzionale) o container registry

### D7 — Documentazione e Demo (2-4 ore)

1. **README.md** con:
   - Setup locale (uv sync, database, .env)
   - API documentation (link a /docs)
   - Architecture decision records (ADR) per scelte chiave

2. **Demo live** (15 minuti):
   - CRUD via Swagger UI (/docs)
   - Trace in Jaeger per una request completa
   - Log strutturato con correlation ID
   - Dashboard Grafana con metriche
   - CI pipeline green

---

## Rubric di Valutazione

| Area | Peso | Pass (70%) | Distinction (90%) |
|------|------|------------|-------------------|
| **API + Pydantic** | 25% | CRUD funzionante, Pydantic base | Discriminated unions, custom validators, cursor pagination, rate limiting |
| **Database** | 15% | SQLAlchemy 2.0, migrations base | Async session, repository pattern, eager loading, cursor pagination |
| **Observability** | 15% | Logging base, qualche trace | OTel completo (traces + metrics), structlog + correlation ID, dashboard |
| **Testing** | 15% | 60%+ coverage, test base | 80%+, hypothesis, testcontainers, integration test |
| **Docker + CI** | 15% | Dockerfile funzionante | Multi-stage distroless, compose con monitoring, CI completa |
| **Security** | 15% | JWT base | httpOnly, pip-audit, rate limiting, CORS restrittivo, non-root container |

**Totale: 100%. Pass ≥ 70%, Distinction ≥ 90%.**

---

## Vincoli

- **Linguaggio**: Python 3.12+
- **Package manager**: `uv` (non pip/pipenv/poetry)
- **Linter/Formatter**: `ruff` (non black/flake8/isort)
- **Type checker**: `mypy` strict mode
- **Database**: PostgreSQL 16+ (via Docker)
- **Framework**: FastAPI 0.110+
- **ORM**: SQLAlchemy 2.0 (async)
- **Validation**: Pydantic v2
- **Testing**: pytest 8+
- **Monitoring**: OpenTelemetry SDK
- **Container**: Docker con multi-stage build

---

## Suggerimenti

1. **Parti dalla struttura** — `uv init`, `pyproject.toml`, directory layout. Errori qui cascadano.
2. **Database first** — modelli ORM e migrations prima degli endpoint. L'API dipende dal DB.
3. **Test while you build** — non lasciare i test alla fine. TDD per i modelli Pydantic.
4. **Observability early** — configura OTel prima di avere molti endpoint. Più facile debuggare.
5. **Security by default** — JWT httpOnly, CORS restrittivo, rate limiting dall'inizio.

---

## Cross-link al percorso

| Deliverable | Moduli chiave |
|-------------|---------------|
| D1 Struttura | 24 (venv), 32 (packaging), 22 (clean code) |
| D2 API | 13 (REST API), 29 (Pydantic), 11 (web framework) |
| D3 Database | 12 (database), 10 (async) |
| D4 Observability | 31 (OTel), 07 (logging) |
| D5 Testing | 08 (testing), 09 (type hints) |
| D6 Docker/CI | 26 (Docker), 27 (CI/CD), 18 (sicurezza) |
| D7 Demo | 30 (troubleshooting), 25 (performance) |
