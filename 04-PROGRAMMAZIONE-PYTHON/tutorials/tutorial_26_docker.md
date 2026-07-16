# Tutorial 26 — Docker per Python: Containerizzazione e Deploy

> **Companion a:** `26-docker.md`
> **Scope:** Dockerfile, multi-stage build, Docker Compose, best practice per Python
> **Prerequisiti:** `tutorial_24_virtual_environments.md`, `tutorial_11_web_framework.md`
> **Durata stimata:** 12-16 ore

---

## Mappa concettuale

```
Docker per Python
│
├── Dockerfile — costruzione immagine
│   ├── FROM — immagine base
│   ├── WORKDIR, COPY, RUN, CMD
│   ├── Multi-stage build — immagine minima
│   └── .dockerignore — escludere file
│
├── Best practice Python
│   ├── Utente non-root
│   ├── Layer caching — COPY uv.lock prima del codice
│   ├── virtualenv nel container
│   └── Health check
│
├── Docker Compose
│   ├── services — app, db, cache
│   ├── volumes — persistenza dati
│   ├── networks — isolamento
│   └── depends_on + healthcheck
│
└── Ambienti
    ├── Development — hot-reload, debug
    ├── Testing — database di test
    └── Production — immagine minima, no dev deps
```

---

# Parte A — Dockerfile per Python

---

## A1. Dockerfile base ottimizzato

```dockerfile
# Dockerfile
# ─── Stage 1: Builder ──────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Installa uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copia lockfile prima del codice sorgente
# → Docker invalida questo layer solo se il lockfile cambia
COPY pyproject.toml uv.lock ./

# Installa dipendenze in un venv dedicato (senza dev deps)
RUN uv sync --frozen --no-dev --no-install-project

# ─── Stage 2: Runtime ──────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# Utente non-root per sicurezza
RUN groupadd --system app && useradd --system --gid app app

# Copia solo il venv dal builder (non uv stesso, non cache)
COPY --from=builder /app/.venv /app/.venv

# Copia il codice sorgente
COPY --chown=app:app src/ ./src/

# Usa il Python del venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

USER app

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/salute').raise_for_status()"

EXPOSE 8000

CMD ["uvicorn", "mio_progetto.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```dockerfile
# Per sviluppo — con hot-reload
FROM python:3.12-slim AS development

WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen   # include dev deps

COPY . .
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

CMD ["uvicorn", "mio_progetto.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

---

## A2. .dockerignore

```dockerignore
# .dockerignore
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.venv/
env/
venv/
.env
.env.*
*.env

# Test e CI
.pytest_cache/
.mypy_cache/
.ruff_cache/
htmlcov/
.coverage
coverage.xml

# Git
.git/
.gitignore
.github/

# Documentazione
docs/
*.md
!README.md

# Docker
Dockerfile*
docker-compose*.yml
.dockerignore

# IDE
.idea/
.vscode/
*.sw[nop]
```

---

# Parte B — Docker Compose

---

## B1. Stack completo: FastAPI + PostgreSQL + Redis

```yaml
# docker-compose.yml
version: "3.9"

services:
  app:
    build:
      context: .
      target: runtime
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://app:secret@db:5432/appdb
      - REDIS_URL=redis://cache:6379/0
      - LOG_LEVEL=info
    depends_on:
      db:
        condition: service_healthy
      cache:
        condition: service_healthy
    networks:
      - backend
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: app
      POSTGRES_PASSWORD: secret
    volumes:
      - pg_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d appdb"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend

  cache:
    image: redis:7-alpine
    command: redis-server --save 60 1 --loglevel warning
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend

volumes:
  pg_data:
  redis_data:

networks:
  backend:
    driver: bridge
```

```yaml
# docker-compose.override.yml — SOLO sviluppo (sovrascrive compose.yml)
services:
  app:
    build:
      target: development   # usa lo stage development
    volumes:
      - ./src:/app/src:ro   # mount del codice per hot-reload
    environment:
      - LOG_LEVEL=debug
    ports:
      - "8000:8000"
      - "5678:5678"   # debugpy port
```

---

## B2. Comandi Docker essenziali

```bash
# Build
docker build -t mia-app:latest .
docker build --target development -t mia-app:dev .

# Build multi-platform (per deploy su ARM/AMD64)
docker buildx build --platform linux/amd64,linux/arm64 -t mia-app:latest .

# Run singolo container
docker run -d \
  --name mia-app \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://... \
  mia-app:latest

# Docker Compose
docker compose up -d               # avvia tutto in background
docker compose up --build          # rebuild prima di avviare
docker compose down                # ferma e rimuovi container
docker compose down -v             # ferma e rimuovi anche i volumi
docker compose logs -f app         # segui log in tempo reale
docker compose ps                  # stato servizi

# Migrazione DB nel container
docker compose run --rm app uv run alembic upgrade head

# Shell nel container
docker compose exec app bash
docker compose exec db psql -U app -d appdb

# Pulizia
docker system prune -af            # rimuovi tutto inutilizzato
docker volume prune                # rimuovi volumi inutilizzati
```

---

# Parte C — Best practice produzione

---

## C1. Segreti e configurazione

```python
# src/mio_progetto/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class ImpostazioniApp(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str
    database_pool_size: int = 10
    database_pool_overflow: int = 20

    # Cache
    redis_url: str = "redis://localhost:6379/0"

    # App
    secret_key: str
    debug: bool = False
    log_level: str = "info"
    cors_origins: list[str] = ["http://localhost:3000"]

settings = ImpostazioniApp()
```

```bash
# .env (SOLO sviluppo locale — mai in git!)
DATABASE_URL=postgresql+asyncpg://app:secret@localhost:5432/appdb
SECRET_KEY=dev-secret-key-non-per-produzione
DEBUG=true

# Produzione: usa Docker Secrets o un vault
# docker secret create db_password - < /dev/stdin
```

---

# Parte D — Riepilogo

## Dockerfile best practice Python

| Pratica | Perché |
|---|---|
| Multi-stage build | Immagine finale più piccola (100MB vs 800MB) |
| Copia lockfile prima del codice | Layer caching — rebuild veloce |
| Utente non-root | Sicurezza: limita blast radius |
| `PYTHONUNBUFFERED=1` | Log in tempo reale senza buffer |
| `PYTHONDONTWRITEBYTECODE=1` | Nessun file `.pyc` nell'immagine |
| `.dockerignore` completo | Build più veloce, nessun secret nel layer |
| Health check | Orchestrator (Kubernetes) sa quando è pronto |
| `--frozen` in CI | Build riproducibile dal lockfile |

## Prossimi passi

- `tutorial_27_ci_cd.md` — pipeline che usa queste immagini Docker
- `tutorial_31_otel.md` — osservabilità nei container
