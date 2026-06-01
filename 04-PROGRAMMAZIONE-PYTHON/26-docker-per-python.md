---
corso: Programmazione Python
fase: 6 — DevOps e Distribuzione
modulo: "26"
versione: Python 3.12+
livello: intermedio-avanzato
prerequisiti:
  - completamento modulo 24 (virtual-environments)
  - familiarità con la riga di comando e il filesystem
  - conoscenza base di Docker (concetti container, image, Dockerfile)
obiettivi:
  - costruire immagini Docker ottimizzate per applicazioni Python con multi-stage build
  - configurare docker-compose per ambienti di sviluppo e produzione
  - implementare pattern Docker per web app (FastAPI, Django), worker (Celery), script
  - applicare best practice di sicurezza (non-root, distroless, secret management)
  - gestire il debug di applicazioni Python containerizzate
  - integrare il build Docker nella pipeline CI/CD
tag:
  - docker
  - container
  - dockerfile
  - multi-stage
  - docker-compose
  - sicurezza
---

# Docker per Python — Guida Completa

> **Modulo 26** · **Aggiornamento:** 2026-05-24

> **Modulo del corso:** Programmazione Python
> **Prerequisiti:** [24-virtual-environments.md](24-virtual-environments.md), [23-packaging-distribuzione.md](23-packaging-distribuzione.md)
> **Obiettivi di apprendimento:**
> 1. Costruire immagini Docker ottimizzate per applicazioni Python con multi-stage build
> 2. Configurare docker-compose per ambienti di sviluppo e produzione
> 3. Implementare pattern Docker per web app, worker e script
> 4. Applicare best practice di sicurezza (non-root, distroless, secret management)
> 5. Gestire il debug di applicazioni Python containerizzate
> 6. Integrare il build Docker nella pipeline CI/CD
> **Tempo stimato:** lettura 50 min · lab 120 min
> **Livello:** intermedio-avanzato
> **Ultimo aggiornamento:** 2026-05-24

## Idee guida
1. **Multi-stage build per slim final image.**
2. **`python:3.12-slim` > `python:3.12` (full).** Distroless final piu pulito.
3. **Non-root user; PEP 668 considerations.**
4. **uv install in docker: `--frozen --no-dev`.**


## Indice

1. [Panoramica](#panoramica)
2. [Fondamenti Docker per Python](#fondamenti-docker-per-python)
   - [Dockerfile](#dockerfile)
   - [Multi-stage Build](#multi-stage-build)
   - [Gestione Dipendenze](#gestione-dipendenze)
3. [docker-compose per Sviluppo](#docker-compose-per-sviluppo)
   - [Setup Completo](#setup-completo)
   - [Development vs Production](#development-vs-production)
4. [Pattern Comuni](#pattern-comuni)
   - [Web Application (FastAPI)](#web-application-fastapi)
   - [Celery Worker](#celery-worker)
   - [Script di Automazione](#script-di-automazione)
   - [Jupyter Notebook](#jupyter-notebook)
5. [Testing in Docker](#testing-in-docker)
6. [Sicurezza](#sicurezza)
7. [Debugging](#debugging)
8. [Registry e CI/CD](#registry-e-cicd)
9. [Best Practices](#best-practices)
10. [Multi-stage Build Avanzato](#multi-stage-build-avanzato)
11. [uv Avanzato in Docker](#uv-avanzato-in-docker)
12. [pip-compile e pip-sync nei Container](#pip-compile-e-pip-sync-nei-container)
13. [Immagini Distroless per Python](#immagini-distroless-per-python)
14. [Health Check Avanzati](#health-check-avanzati)
15. [Docker Compose Avanzato per Sviluppo Python](#docker-compose-avanzato-per-sviluppo-python)
16. [Debugging Avanzato in Container](#debugging-avanzato-in-container)
17. [.dockerignore Specifico per Python](#dockerignore-specifico-per-python)
18. [Security Scanning delle Dipendenze Python](#security-scanning-delle-dipendenze-python)
19. [Signal Handling — SIGTERM e SIGINT](#signal-handling--sigterm-e-sigint)
20. [Gunicorn e Uvicorn in Docker](#gunicorn-e-uvicorn-in-docker)
21. [CI/CD con Docker per Python](#cicd-con-docker-per-python)
22. [Strategie di Layer Caching per pip e uv](#strategie-di-layer-caching-per-pip-e-uv)
23. [Logging in Container](#logging-in-container)
24. [Testing Avanzato — pytest e Testcontainers](#testing-avanzato--pytest-e-testcontainers)

---

## Panoramica

Docker ha rivoluzionato il modo in cui gli sviluppatori Python costruiscono, distribuiscono e gestiscono le applicazioni. Prima di Docker, la classica frase "funziona sulla mia macchina" era il problema quotidiano di ogni team di sviluppo. Versioni diverse di Python, dipendenze di sistema mancanti, configurazioni divergenti tra ambienti: tutto questo generava bug difficili da riprodurre e deploy rischiosi.

**Perche Docker per Python?**

Python presenta sfide specifiche nella gestione degli ambienti. I virtual environment risolvono l'isolamento delle dipendenze Python, ma non gestiscono le dipendenze di sistema (librerie C, binari di compilazione, configurazioni OS). Docker risolve questo problema incapsulando l'intera applicazione — codice, runtime Python, dipendenze di sistema e configurazione — in un container riproducibile.

**Vantaggi principali:**

- **Riproducibilita garantita**: ogni membro del team, ogni server di staging e ogni nodo di produzione eseguono esattamente lo stesso ambiente. Non esistono discrepanze tra "la mia versione di libpq" e "la tua versione di libpq".
- **Isolamento completo**: ogni applicazione vive nel proprio container con le proprie dipendenze, senza conflitti con altri progetti sulla stessa macchina.
- **Semplificazione del deploy**: il passaggio da sviluppo a produzione diventa prevedibile. L'immagine testata in CI e la stessa che viene eseguita in produzione.
- **Scalabilita orizzontale**: con orchestratori come Kubernetes o Docker Swarm, scalare un'applicazione Python significa semplicemente aggiungere piu repliche dello stesso container.
- **Onboarding veloce**: un nuovo sviluppatore puo avviare l'intero stack applicativo con un singolo comando `docker compose up`, senza dover installare manualmente Python, PostgreSQL, Redis e altre dipendenze.
- **Integrazione con CI/CD**: le pipeline di continuous integration possono costruire, testare e pubblicare immagini Docker in modo automatizzato e consistente.

---

## Fondamenti Docker per Python

### Dockerfile

Il Dockerfile e il file di istruzioni che definisce come costruire un'immagine Docker. Per le applicazioni Python, la scelta dell'immagine base e fondamentale perche influenza direttamente dimensioni, sicurezza e compatibilita dell'immagine finale.

**Immagini base Python:**

Python fornisce diverse varianti ufficiali, ciascuna con caratteristiche specifiche:

| Immagine | Dimensione | Descrizione | Uso consigliato |
|---|---|---|---|
| `python:3.12` | ~1.0 GB | Basata su Debian, include strumenti di compilazione completi | Sviluppo, applicazioni con dipendenze C complesse |
| `python:3.12-slim` | ~150 MB | Debian minimale, senza compilatori | Produzione, la maggior parte delle applicazioni |
| `python:3.12-alpine` | ~55 MB | Basata su Alpine Linux, usa musl libc | Immagini ultra-leggere, attenzione alla compatibilita |
| `python:3.12-bookworm` | ~1.0 GB | Basata su Debian Bookworm esplicitamente | Quando serve una versione Debian specifica |

> **Nota importante su Alpine**: sebbene Alpine produca immagini molto piccole, usa `musl` invece di `glibc`. Questo puo causare problemi con pacchetti Python che hanno estensioni C (numpy, pandas, cryptography). La compilazione su Alpine e spesso piu lenta e le wheel precompilate non funzionano. Per la maggior parte dei progetti, `python:3.12-slim` rappresenta il miglior compromesso.

**Dockerfile base per un'applicazione Python:**

```dockerfile
# Immagine base
FROM python:3.12-slim

# Metadati dell'immagine
LABEL maintainer="team@example.com"
LABEL version="1.0"
LABEL description="Applicazione web Python"

# Variabili d'ambiente per Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Directory di lavoro all'interno del container
WORKDIR /app

# Installazione dipendenze di sistema (se necessarie)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copia e installazione dipendenze Python (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia del codice sorgente
COPY . .

# Creazione utente non-root
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser && \
    chown -R appuser:appuser /app

# Passaggio all'utente non-root
USER appuser

# Esposizione della porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando di avvio
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Spiegazione delle istruzioni principali:**

- `WORKDIR /app`: imposta la directory di lavoro. Tutte le istruzioni successive (`COPY`, `RUN`, `CMD`) operano da questa directory. Se non esiste, viene creata automaticamente.
- `COPY`: copia file dal contesto di build al filesystem del container. L'ordine delle istruzioni `COPY` e cruciale per sfruttare la cache dei layer.
- `RUN`: esegue comandi durante la costruzione dell'immagine. Ogni `RUN` crea un nuovo layer; conviene concatenare comandi correlati con `&&` per ridurre il numero di layer.
- `CMD`: definisce il comando di default eseguito all'avvio del container. Accetta la forma exec `["cmd", "arg1"]` (preferita) oppure la forma shell `cmd arg1`.
- `ENTRYPOINT`: simile a `CMD`, ma definisce il comando fisso del container. `CMD` diventa l'argomento di default per `ENTRYPOINT`. Utile per container che funzionano come eseguibili.

```dockerfile
# Esempio di ENTRYPOINT + CMD
ENTRYPOINT ["python", "manage.py"]
CMD ["runserver", "0.0.0.0:8000"]

# docker run myapp                    -> python manage.py runserver 0.0.0.0:8000
# docker run myapp migrate            -> python manage.py migrate
# docker run myapp createsuperuser    -> python manage.py createsuperuser
```

**Il file .dockerignore:**

Il file `.dockerignore` esclude file e directory dal contesto di build, riducendo i tempi di build e prevenendo l'inclusione accidentale di file sensibili nell'immagine.

```dockerignore
# Ambienti virtuali Python
.venv/
venv/
env/

# Cache Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/

# File di configurazione locale
.env
.env.local
*.env

# Controllo versione
.git/
.gitignore

# Docker
Dockerfile
docker-compose*.yml
.dockerignore

# IDE e editor
.vscode/
.idea/
*.swp
*.swo

# Test e documentazione
tests/
docs/
*.md
htmlcov/
.coverage
.pytest_cache/

# OS
.DS_Store
Thumbs.db
```

---

### Multi-stage Build

I multi-stage build sono una tecnica fondamentale per creare immagini Docker leggere e sicure. L'idea e semplice: si usano piu fasi di build in un singolo Dockerfile, copiando solo gli artefatti necessari dalla fase di compilazione alla fase finale.

Questo approccio e particolarmente utile in Python quando si hanno dipendenze che richiedono compilazione (estensioni C, pacchetti con binari nativi).

```dockerfile
# ============================================
# STAGE 1: Builder — compila le dipendenze
# ============================================
FROM python:3.12-slim AS builder

# Installa strumenti di compilazione
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Crea le wheel delle dipendenze
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# ============================================
# STAGE 2: Runtime — immagine finale minimale
# ============================================
FROM python:3.12-slim AS runtime

# Solo le librerie runtime necessarie (no compilatori)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia le wheel pre-compilate e installa
COPY --from=builder /build/wheels /tmp/wheels
RUN pip install --no-cache-dir /tmp/wheels/* && \
    rm -rf /tmp/wheels

# Copia il codice sorgente
COPY . .

# Utente non-root
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Vantaggi del multi-stage build:**

- L'immagine finale non contiene compilatori, header di sviluppo o strumenti di build.
- Riduzione significativa delle dimensioni: un'immagine che con un singolo stage pesa 800 MB puo scendere a 200 MB.
- Superficie d'attacco ridotta: meno software installato significa meno vulnerabilita potenziali.

---

### Gestione Dipendenze

La gestione delle dipendenze in Docker richiede attenzione per sfruttare al meglio il meccanismo di caching dei layer.

**Principio fondamentale — copia requirements.txt per primo:**

Docker costruisce le immagini layer per layer. Se un file non cambia, Docker riusa il layer dalla cache. Copiando `requirements.txt` separatamente dal resto del codice, le dipendenze vengono reinstallate solo quando il file delle dipendenze cambia effettivamente, non a ogni modifica del codice sorgente.

```dockerfile
# CORRETTO: sfrutta la cache dei layer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# SBAGLIATO: reinstalla tutto a ogni modifica del codice
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
```

**pip install con --no-cache-dir:**

Il flag `--no-cache-dir` impedisce a pip di salvare i pacchetti scaricati nella cache locale. In un container questa cache e inutile e occupa solo spazio nell'immagine.

**Poetry in Docker:**

Poetry e un gestore di dipendenze moderno per Python. Ecco come integrarlo in un Dockerfile:

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.8.3 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

# Installazione di Poetry
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

WORKDIR /app

# Copia solo i file di lock per sfruttare la cache
COPY pyproject.toml poetry.lock ./

# Installazione dipendenze senza il pacchetto stesso
RUN poetry install --no-root --only=main

# Copia il codice e installa il pacchetto
COPY . .
RUN poetry install --only=main

USER 1000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**uv in Docker (l'approccio piu veloce):**

`uv` e un package manager scritto in Rust che e ordini di grandezza piu veloce di pip e Poetry. La sua integrazione con Docker e eccellente:

```dockerfile
FROM python:3.12-slim

# Copia uv dall'immagine ufficiale
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Installa dipendenze (uv e estremamente veloce)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copia codice e installa il progetto
COPY . .
RUN uv sync --frozen --no-dev

USER 1000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

La differenza di velocita e notevole: dove pip impiega 45 secondi per installare le dipendenze, uv completa la stessa operazione in 2-3 secondi. In un workflow CI/CD con build frequenti, questo risparmio e significativo.

---

## docker-compose per Sviluppo

### Setup Completo

Docker Compose permette di definire e gestire applicazioni multi-container. Per un progetto Python tipico, lo stack comprende l'applicazione web, un database, un sistema di cache e worker per task asincroni.

```yaml
# docker-compose.yml
services:
  # ============================================
  # Applicazione Web (FastAPI)
  # ============================================
  web:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/appdb
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY:-development-secret-key}
      - ENVIRONMENT=development
    volumes:
      - ./app:/app/app          # Hot reload del codice
      - ./alembic:/app/alembic  # Migrazioni database
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - app-network

  # ============================================
  # PostgreSQL
  # ============================================
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - app-network

  # ============================================
  # Redis
  # ============================================
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    networks:
      - app-network

  # ============================================
  # Celery Worker
  # ============================================
  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile
    command: celery -A app.celery_app worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/appdb
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./app:/app/app
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - app-network

  # ============================================
  # Celery Beat (scheduler)
  # ============================================
  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile
    command: celery -A app.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/appdb
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - celery-worker
    restart: unless-stopped
    networks:
      - app-network

volumes:
  postgres_data:
  redis_data:

networks:
  app-network:
    driver: bridge
```

**Punti chiave della configurazione:**

- I **volume mount** (`./app:/app/app`) permettono di modificare il codice localmente e vedere le modifiche riflesse immediatamente nel container, senza dover ricostruire l'immagine.
- Le **variabili d'ambiente** configurano i servizi. Si usa la sintassi `${VAR:-default}` per fornire valori di default.
- Gli **health check** verificano che un servizio sia effettivamente pronto, non solo avviato. `depends_on` con `condition: service_healthy` garantisce l'ordine corretto di avvio.
- I **named volumes** (`postgres_data`, `redis_data`) persistono i dati tra riavvii dei container.

---

### Development vs Production

E fondamentale mantenere configurazioni separate per sviluppo e produzione. Docker Compose supporta file di override che permettono di stratificare le configurazioni.

**docker-compose.yml (configurazione base, condivisa):**

```yaml
# docker-compose.yml — configurazione base
services:
  web:
    build:
      context: .
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/appdb
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - app-network

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network

volumes:
  postgres_data:
  redis_data:

networks:
  app-network:
    driver: bridge
```

**docker-compose.override.yml (sviluppo — caricato automaticamente):**

```yaml
# docker-compose.override.yml — override per sviluppo
services:
  web:
    ports:
      - "8000:8000"
      - "5678:5678"        # Porta per debugpy
    volumes:
      - ./app:/app/app     # Hot reload del codice
      - ./tests:/app/tests
    environment:
      - ENVIRONMENT=development
      - DEBUG=true
      - LOG_LEVEL=debug
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  db:
    ports:
      - "5432:5432"        # Accesso diretto al DB per sviluppo
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    ports:
      - "6379:6379"        # Accesso diretto a Redis per sviluppo
    volumes:
      - redis_data:/data
```

**docker-compose.prod.yml (produzione):**

```yaml
# docker-compose.prod.yml — override per produzione
services:
  web:
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
      - LOG_LEVEL=warning
    command: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 1G
        reservations:
          cpus: "0.5"
          memory: 256M
    restart: always
    # Nessun volume mount — il codice e integrato nell'immagine

  db:
    volumes:
      - postgres_data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
    restart: always
    # Nessuna porta esposta all'esterno

  redis:
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          cpus: "0.5"
          memory: 256M
    restart: always
```

**Comandi per i diversi ambienti:**

```bash
# Sviluppo (usa docker-compose.yml + docker-compose.override.yml automaticamente)
docker compose up

# Produzione (usa docker-compose.yml + docker-compose.prod.yml)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Build per produzione
docker compose -f docker-compose.yml -f docker-compose.prod.yml build
```

---

## Pattern Comuni

### Web Application (FastAPI)

FastAPI e il framework web Python piu popolare per la creazione di API moderne. Ecco un setup Docker completo e pronto per la produzione:

```dockerfile
# Dockerfile per FastAPI
FROM python:3.12-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libpq-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# ---

FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /build/wheels /tmp/wheels
RUN pip install --no-cache-dir /tmp/wheels/* && rm -rf /tmp/wheels

COPY . .

RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Produzione: Gunicorn con worker Uvicorn
CMD ["gunicorn", "app.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

**Endpoint health nel codice Python:**

```python
# app/main.py
from fastapi import FastAPI
from datetime import datetime

app = FastAPI(title="La Mia Applicazione")

@app.get("/health")
async def health_check():
    """Endpoint di health check per Docker e load balancer."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
```

**Gunicorn vs Uvicorn:**

In sviluppo si usa Uvicorn direttamente con `--reload` per il ricaricamento automatico. In produzione si usa Gunicorn come process manager con Uvicorn come worker class. Gunicorn gestisce il ciclo di vita dei worker, il restart automatico in caso di crash e la distribuzione del carico tra piu processi.

Il numero di worker consigliato e `(2 * CPU_CORES) + 1`. Per un container con 2 CPU: 5 worker.

**Configurazione avanzata di Gunicorn:**

Per applicazioni di produzione, e consigliabile creare un file di configurazione Gunicorn separato anziche passare tutti i parametri dalla riga di comando:

```python
# gunicorn.conf.py
import multiprocessing
import os

# Bind
bind = "0.0.0.0:8000"

# Worker
workers = int(os.getenv("WEB_CONCURRENCY", multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_tmp_dir = "/dev/shm"  # RAM disk per evitare I/O su disco

# Timeout
timeout = 120
keepalive = 5
graceful_timeout = 30

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")

# Lifecycle hooks
def on_starting(server):
    """Eseguito quando Gunicorn viene avviato."""
    pass

def post_fork(server, worker):
    """Eseguito dopo il fork di ogni worker."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")
```

Questo file viene poi referenziato nel Dockerfile:

```dockerfile
CMD ["gunicorn", "app.main:app", "-c", "gunicorn.conf.py"]
```

---

### Celery Worker

Celery gestisce l'esecuzione di task asincroni. In un'architettura Docker, ogni componente Celery e un servizio separato:

```yaml
# Estratto da docker-compose.yml per i servizi Celery
services:
  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile
    command: >
      celery -A app.celery_app worker
      --loglevel=info
      --concurrency=4
      --max-tasks-per-child=1000
      --without-heartbeat
      --without-gossip
      --without-mingle
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      redis:
        condition: service_healthy
    deploy:
      replicas: 2    # Due worker per maggiore throughput
    restart: unless-stopped

  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile
    command: >
      celery -A app.celery_app beat
      --loglevel=info
      --schedule=/tmp/celerybeat-schedule
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - celery-worker
    restart: unless-stopped

  flower:
    build:
      context: .
      dockerfile: Dockerfile
    command: celery -A app.celery_app flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - celery-worker
```

I flag `--without-heartbeat`, `--without-gossip` e `--without-mingle` sono ottimizzazioni per ambienti containerizzati dove la scoperta dei nodi non e necessaria. `--max-tasks-per-child` previene memory leak riavviando i worker dopo un certo numero di task.

Flower e l'interfaccia web di monitoraggio per Celery: mostra lo stato dei worker, i task in coda, i tassi di successo/errore e i grafici storici.

---

### Script di Automazione

Docker e utile anche per eseguire script Python isolati, come job di elaborazione dati o task di manutenzione.

**Esecuzione one-shot:**

```bash
# Eseguire uno script una tantum
docker run --rm \
    -v $(pwd)/data:/app/data \
    -e DB_URL=postgresql://user:pass@host:5432/db \
    myapp python scripts/migrate_data.py

# Eseguire un comando Python interattivo
docker run --rm -it myapp python

# Eseguire le migrazioni del database
docker compose run --rm web alembic upgrade head
```

**Cron job con Docker:**

```yaml
# docker-compose.yml — servizio cron
services:
  cron:
    build:
      context: .
      dockerfile: Dockerfile.cron
    volumes:
      - ./scripts:/app/scripts
      - ./logs:/app/logs
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/appdb
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
```

```dockerfile
# Dockerfile.cron
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Installazione cron
RUN apt-get update && \
    apt-get install -y --no-install-recommends cron && \
    rm -rf /var/lib/apt/lists/*

# Configurazione crontab
COPY crontab /etc/cron.d/app-cron
RUN chmod 0644 /etc/cron.d/app-cron && \
    crontab /etc/cron.d/app-cron

CMD ["cron", "-f"]
```

```crontab
# crontab — eseguito ogni giorno alle 02:00
0 2 * * * cd /app && python scripts/daily_report.py >> /app/logs/cron.log 2>&1
# Ogni 15 minuti: sincronizzazione dati
*/15 * * * * cd /app && python scripts/sync_data.py >> /app/logs/sync.log 2>&1
```

**Considerazioni sugli script one-shot:**

L'opzione `--rm` e fondamentale per i container one-shot: rimuove automaticamente il container dopo l'esecuzione, evitando l'accumulo di container fermi che consumano spazio su disco. Senza `--rm`, ogni esecuzione lascia un container arrestato che deve essere rimosso manualmente con `docker rm`.

**Pipeline di elaborazione dati:**

```yaml
# docker-compose.pipeline.yml
services:
  extract:
    build: .
    command: python pipeline/extract.py
    volumes:
      - pipeline_data:/data

  transform:
    build: .
    command: python pipeline/transform.py
    volumes:
      - pipeline_data:/data
    depends_on:
      extract:
        condition: service_completed_successfully

  load:
    build: .
    command: python pipeline/load.py
    volumes:
      - pipeline_data:/data
    depends_on:
      transform:
        condition: service_completed_successfully

volumes:
  pipeline_data:
```

---

### Jupyter Notebook

Jupyter Notebook in Docker garantisce ambienti di analisi riproducibili e condivisibili tra i membri del team.

```dockerfile
# Dockerfile.jupyter
FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /notebooks

COPY requirements-jupyter.txt .
RUN pip install --no-cache-dir -r requirements-jupyter.txt

# Installazione estensioni JupyterLab
RUN pip install --no-cache-dir \
    jupyterlab-git \
    jupyterlab-lsp \
    python-lsp-server[all]

# Utente non-root
RUN groupadd --gid 1000 jupyter && \
    useradd --uid 1000 --gid jupyter --shell /bin/bash --create-home jupyter && \
    chown -R jupyter:jupyter /notebooks
USER jupyter

EXPOSE 8888

CMD ["jupyter", "lab", \
     "--ip=0.0.0.0", \
     "--port=8888", \
     "--no-browser", \
     "--NotebookApp.token=''", \
     "--NotebookApp.password=''"]
```

```yaml
# docker-compose.jupyter.yml
services:
  jupyter:
    build:
      context: .
      dockerfile: Dockerfile.jupyter
    ports:
      - "8888:8888"
    volumes:
      - ./notebooks:/notebooks       # Notebook persistenti
      - ./data:/notebooks/data        # Dati condivisi
    environment:
      - JUPYTER_ENABLE_LAB=yes
```

---

## Testing in Docker

Docker garantisce che i test vengano eseguiti in un ambiente identico a quello di produzione, eliminando i problemi di "funziona sulla mia macchina ma non in CI". Questo e particolarmente importante per i test di integrazione, dove le dipendenze esterne (database, cache, code di messaggi) devono essere configurate in modo preciso e riproducibile.

**Esecuzione di pytest nel container:**

```bash
# Esegui tutti i test
docker compose run --rm web pytest tests/ -v

# Esegui test con coverage
docker compose run --rm web pytest tests/ --cov=app --cov-report=html

# Esegui solo i test unitari
docker compose run --rm web pytest tests/unit/ -v -x

# Esegui test specifici
docker compose run --rm web pytest tests/test_users.py::test_create_user -v
```

**Docker Compose per test di integrazione:**

```yaml
# docker-compose.test.yml
services:
  test:
    build:
      context: .
      dockerfile: Dockerfile
      target: builder    # Usa lo stage builder che include i tool di test
    command: pytest tests/ -v --tb=short --junitxml=reports/junit.xml
    environment:
      - DATABASE_URL=postgresql://postgres:password@test-db:5432/testdb
      - REDIS_URL=redis://test-redis:6379/0
      - ENVIRONMENT=testing
    volumes:
      - ./reports:/app/reports
    depends_on:
      test-db:
        condition: service_healthy
      test-redis:
        condition: service_healthy

  test-db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: testdb
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5
    # Nessun volume: il database e effimero per i test
    tmpfs:
      - /var/lib/postgresql/data    # RAM disk per velocita

  test-redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
```

```bash
# Esegui la suite di test completa
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from test

# Pulizia dopo i test
docker compose -f docker-compose.test.yml down -v
```

**Setup e teardown del database di test con fixture pytest:**

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base

@pytest.fixture(scope="session")
def db_engine():
    """Crea il database di test una volta per sessione."""
    engine = create_engine(os.environ["DATABASE_URL"])
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Ogni test ha la propria transazione, rollback alla fine."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()
```

**Integrazione in una pipeline CI (esempio GitHub Actions):**

```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and run tests
        run: |
          docker compose -f docker-compose.test.yml up \
            --build \
            --abort-on-container-exit \
            --exit-code-from test

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: reports/junit.xml

      - name: Cleanup
        if: always()
        run: docker compose -f docker-compose.test.yml down -v
```

---

## Sicurezza

La sicurezza dei container Docker e un aspetto critico, soprattutto per applicazioni che gestiscono dati sensibili. Ecco le pratiche fondamentali.

**Utente non-root (sempre!):**

Per default, i container Docker vengono eseguiti come root. Questo e un rischio di sicurezza significativo: se un attaccante riesce a evadere dal container, avra privilegi root sull'host.

```dockerfile
# Crea e usa sempre un utente non-root
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Imposta i permessi PRIMA di cambiare utente
RUN chown -R appuser:appuser /app

USER appuser
```

**Immagini base minimali:**

Meno software e installato nell'immagine, meno vulnerabilita potenziali esistono. Usa `python:3.12-slim` invece dell'immagine completa. Evita di installare tool non necessari (curl, wget, vim) nell'immagine di produzione, a meno che non servano per gli health check.

**Mai segreti nelle immagini:**

```dockerfile
# SBAGLIATO: il segreto rimane nella storia dei layer
ENV API_KEY=my-super-secret-key
COPY .env /app/.env

# CORRETTO: usa Docker build secrets (BuildKit)
RUN --mount=type=secret,id=pip_conf,target=/etc/pip.conf \
    pip install --no-cache-dir -r requirements.txt

# CORRETTO: passa segreti a runtime tramite variabili d'ambiente
# docker run -e API_KEY=my-super-secret-key myapp
```

```bash
# Build con secrets (BuildKit)
DOCKER_BUILDKIT=1 docker build \
    --secret id=pip_conf,src=./pip.conf \
    -t myapp .
```

**Scansione delle immagini:**

Strumenti come Trivy e Snyk analizzano le immagini Docker alla ricerca di vulnerabilita note nelle dipendenze di sistema e nei pacchetti Python.

```bash
# Scansione con Trivy
trivy image myapp:latest

# Scansione con livello di severita
trivy image --severity HIGH,CRITICAL myapp:latest

# Scansione in pipeline CI (esce con errore se ci sono vulnerabilita critiche)
trivy image --exit-code 1 --severity CRITICAL myapp:latest

# Scansione con Snyk
snyk container test myapp:latest
```

**Limitare le capability del container:**

Docker assegna un set di capability Linux al container per default. In produzione, e consigliabile rimuovere tutte le capability non necessarie:

```yaml
services:
  web:
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE    # Solo se serve bind su porte < 1024
    security_opt:
      - no-new-privileges:true
```

La direttiva `no-new-privileges` impedisce ai processi nel container di acquisire nuovi privilegi tramite setuid o setgid, chiudendo un potenziale vettore di attacco.

**Pinning dei digest delle immagini base:**

I tag delle immagini (`python:3.12-slim`) possono cambiare nel tempo. Per build completamente riproducibili, si puo fare il pin del digest SHA256:

```dockerfile
# Tag: puo cambiare senza preavviso
FROM python:3.12-slim

# Digest: immutabile, punta sempre alla stessa immagine
FROM python:3.12-slim@sha256:a1b2c3d4e5f6...

# Trova il digest corrente
# docker inspect --format='{{index .RepoDigests 0}}' python:3.12-slim
```

**Filesystem read-only:**

In produzione, il filesystem del container dovrebbe essere in sola lettura. Le applicazioni Python che devono scrivere file temporanei possono usare `tmpfs`:

```yaml
# docker-compose.prod.yml
services:
  web:
    image: myapp:latest
    read_only: true
    tmpfs:
      - /tmp
      - /app/.cache
    volumes:
      - app_uploads:/app/uploads    # Solo le directory necessarie sono scrivibili
```

---

## Debugging

Il debugging in ambienti containerizzati richiede tecniche specifiche. Docker fornisce diversi strumenti per ispezionare e diagnosticare problemi.

**Accesso shell con docker exec:**

```bash
# Apri una shell bash nel container in esecuzione
docker exec -it nome_container bash

# Esegui un comando specifico
docker exec nome_container python -c "import app; print(app.__version__)"

# Esegui come root (utile per debugging, non per produzione)
docker exec -u root -it nome_container bash

# Ispeziona le variabili d'ambiente
docker exec nome_container env | sort

# Verifica i pacchetti installati
docker exec nome_container pip list
```

**Docker logs:**

```bash
# Visualizza i log del container
docker logs nome_container

# Segui i log in tempo reale (come tail -f)
docker logs -f nome_container

# Ultimi 100 righe di log
docker logs --tail 100 nome_container

# Log con timestamp
docker logs -t nome_container

# Log da un certo momento
docker logs --since 2024-01-15T10:00:00 nome_container

# Log di tutti i servizi con Docker Compose
docker compose logs -f

# Log di un servizio specifico
docker compose logs -f web
```

**VS Code Remote Containers / Dev Containers:**

VS Code puo connettersi direttamente a un container Docker per fornire un'esperienza di sviluppo completa con IntelliSense, debugging integrato e terminale.

```json
// .devcontainer/devcontainer.json
{
    "name": "Python Dev Container",
    "dockerComposeFile": "../docker-compose.yml",
    "service": "web",
    "workspaceFolder": "/app",
    "customizations": {
        "vscode": {
            "extensions": [
                "ms-python.python",
                "ms-python.vscode-pylance",
                "charliermarsh.ruff"
            ],
            "settings": {
                "python.defaultInterpreterPath": "/usr/local/bin/python",
                "python.testing.pytestEnabled": true
            }
        }
    },
    "forwardPorts": [8000, 5432, 6379],
    "postCreateCommand": "pip install -e '.[dev]'"
}
```

**Remote debugging con debugpy:**

`debugpy` permette di fare debugging remoto di applicazioni Python in esecuzione nei container Docker.

```python
# app/main.py — avvia debugpy in modalita sviluppo
import os

if os.getenv("DEBUG") == "true":
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    print("Debugger in ascolto sulla porta 5678...")
    # Decommenta per attendere la connessione del debugger prima di avviare
    # debugpy.wait_for_client()
```

```yaml
# docker-compose.override.yml
services:
  web:
    ports:
      - "8000:8000"
      - "5678:5678"    # Porta debugpy
    environment:
      - DEBUG=true
```

```json
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Attach Docker",
            "type": "debugpy",
            "request": "attach",
            "connect": {
                "host": "localhost",
                "port": 5678
            },
            "pathMappings": [
                {
                    "localRoot": "${workspaceFolder}/app",
                    "remoteRoot": "/app/app"
                }
            ]
        }
    ]
}
```

**pdb in Docker:**

Per usare pdb (il debugger interattivo di Python) in un container, il container deve essere avviato con i flag `-it` per allocare un terminale interattivo:

```bash
# Avvia il container con terminale interattivo
docker compose run --rm -it web python -m pdb app/script.py

# Per inserire un breakpoint nel codice
# breakpoint()  # oppure import pdb; pdb.set_trace()

# Se il container e gia in esecuzione con docker compose up,
# usa stdin_open e tty nel compose file:
```

```yaml
services:
  web:
    stdin_open: true    # docker run -i
    tty: true           # docker run -t
```

---

## Registry e CI/CD

La pubblicazione e la distribuzione delle immagini Docker sono parte integrante del workflow CI/CD moderno.

**Build e push verso diversi registry:**

```bash
# Docker Hub
docker build -t username/myapp:latest .
docker push username/myapp:latest

# GitHub Container Registry (GHCR)
docker build -t ghcr.io/username/myapp:latest .
echo $GITHUB_TOKEN | docker login ghcr.io -u username --password-stdin
docker push ghcr.io/username/myapp:latest

# Amazon ECR
aws ecr get-login-password --region eu-west-1 | \
    docker login --username AWS --password-stdin 123456789.dkr.ecr.eu-west-1.amazonaws.com
docker build -t 123456789.dkr.ecr.eu-west-1.amazonaws.com/myapp:latest .
docker push 123456789.dkr.ecr.eu-west-1.amazonaws.com/myapp:latest
```

**GitHub Actions per build Docker:**

```yaml
# .github/workflows/docker.yml
name: Build and Push Docker Image
on:
  push:
    branches: [main]
    tags: ["v*"]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GHCR
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix=

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Scan image with Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:sha-${{ github.sha }}
          format: "sarif"
          output: "trivy-results.sarif"
```

**Strategie di tagging:**

| Strategia | Esempio | Uso |
|---|---|---|
| Git SHA | `myapp:a1b2c3d` | Tracciabilita esatta del codice |
| Semantic Versioning | `myapp:1.2.3` | Release ufficiali |
| Branch name | `myapp:main`, `myapp:develop` | Ambienti di staging |
| Latest | `myapp:latest` | Ultima build del branch principale |
| Data | `myapp:2024-01-15` | Build giornaliere |

Il consiglio e usare una combinazione: ogni immagine riceve sia il tag semver che il git SHA. Il tag `latest` dovrebbe puntare sempre all'ultima release stabile. In ambienti con piu team, e utile aggiungere anche il nome dell'ambiente (staging, production) per chiarezza.

**Build multi-architettura:**

Con Docker Buildx e possibile creare immagini che funzionano su architetture diverse (amd64, arm64). Questo e essenziale se il team di sviluppo include membri con Mac Apple Silicon (arm64) mentre la produzione gira su server x86_64:

```bash
# Crea un builder multi-piattaforma
docker buildx create --name multiarch --use

# Build e push per entrambe le architetture
docker buildx build --platform linux/amd64,linux/arm64 \
    -t ghcr.io/user/myapp:latest \
    --push .
```

Nelle GitHub Actions, basta aggiungere il parametro `platforms` alla build-push-action:

```yaml
- name: Build and push (multi-arch)
  uses: docker/build-push-action@v5
  with:
    context: .
    platforms: linux/amd64,linux/arm64
    push: true
    tags: ${{ steps.meta.outputs.tags }}
```

**Caching dei layer in CI:**

Il caching e fondamentale per ridurre i tempi di build in CI. Senza cache, ogni build scarica e installa tutte le dipendenze da zero.

```yaml
# GitHub Actions — cache con GitHub Actions cache backend
- name: Build and push
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: ${{ steps.meta.outputs.tags }}
    cache-from: type=gha                # Leggi cache da GitHub Actions
    cache-to: type=gha,mode=max         # Scrivi cache su GitHub Actions

# Alternativa: cache con registry
- name: Build and push
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: myapp:latest
    cache-from: type=registry,ref=ghcr.io/user/myapp:buildcache
    cache-to: type=registry,ref=ghcr.io/user/myapp:buildcache,mode=max
```

---

## Best Practices

Ecco le 10 best practice fondamentali per l'uso di Docker con Python, distillate dall'esperienza reale su progetti in produzione.

**1. Usa sempre immagini base slim**

Preferisci `python:3.12-slim` all'immagine completa. L'immagine slim e circa 6 volte piu piccola e contiene tutto il necessario per la maggior parte delle applicazioni. Usa l'immagine completa solo se hai bisogno di compilare estensioni C durante il build (ma in quel caso, usa multi-stage build).

**2. Un processo per container**

Ogni container dovrebbe eseguire un singolo processo. Non avviare l'applicazione web, il worker Celery e il beat scheduler nello stesso container. Servizi separati permettono scaling indipendente, logging pulito e restart isolato. Se un worker crasha, non trascina con se il server web.

**3. Sfrutta la cache dei layer in modo strategico**

Ordina le istruzioni nel Dockerfile dalla meno frequentemente modificata alla piu frequentemente modificata. Le dipendenze di sistema cambiano raramente, le dipendenze Python cambiano occasionalmente, il codice sorgente cambia costantemente. Questo ordine massimizza l'utilizzo della cache.

```dockerfile
# Ordine ottimale
RUN apt-get update && apt-get install -y libpq-dev    # Cambia raramente
COPY requirements.txt .                                 # Cambia occasionalmente
RUN pip install -r requirements.txt
COPY . .                                                # Cambia spesso
```

**4. Non eseguire mai container come root in produzione**

Crea sempre un utente dedicato non-root. E la singola misura di sicurezza piu importante. Se un attaccante sfrutta una vulnerabilita nella tua applicazione, l'utente non-root limita il danno che puo fare.

**5. Usa .dockerignore sempre**

Senza `.dockerignore`, Docker invia l'intero contesto di build al daemon, inclusi `.git/`, `node_modules/`, ambienti virtuali e potenzialmente file con segreti. Un buon `.dockerignore` riduce i tempi di build e previene leak di informazioni sensibili.

**6. Imposta PYTHONDONTWRITEBYTECODE e PYTHONUNBUFFERED**

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
```

`PYTHONDONTWRITEBYTECODE=1` evita la creazione di file `.pyc` inutili nel container. `PYTHONUNBUFFERED=1` garantisce che l'output di Python (stdout/stderr) venga inviato direttamente ai log Docker senza buffering, fondamentale per il debugging in tempo reale.

**7. Usa multi-stage build per le immagini di produzione**

I multi-stage build separano l'ambiente di compilazione da quello di esecuzione. L'immagine finale non contiene compilatori, header di sviluppo, file temporanei di build o strumenti non necessari a runtime. Questo riduce le dimensioni e la superficie d'attacco.

**8. Implementa health check appropriati**

Gli health check permettono a Docker (e agli orchestratori) di sapere se la tua applicazione e realmente funzionante, non solo se il processo e in esecuzione. Un processo puo essere vivo ma bloccato (deadlock, pool di connessioni esaurito). L'health check deve verificare la funzionalita reale.

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

**9. Gestisci i segreti correttamente**

Non inserire mai segreti (chiavi API, password, token) nel Dockerfile o nell'immagine. Usa variabili d'ambiente a runtime, Docker secrets, o strumenti di gestione dei segreti come HashiCorp Vault. Ricorda che anche `docker history` puo rivelare valori passati con `ARG` o `ENV` durante il build.

**10. Tagga le immagini in modo significativo e non usare solo latest**

Il tag `latest` e comodo in sviluppo ma pericoloso in produzione perche non permette di sapere quale versione esatta e in esecuzione. Usa sempre tag specifici: il git SHA per la tracciabilita, semver per le release. Mantieni `latest` come alias dell'ultima release stabile, ma non dipendere da esso per i deploy.

```bash
# Tagging corretto in CI
docker build -t myapp:$(git rev-parse --short HEAD) \
             -t myapp:1.2.3 \
             -t myapp:latest .
```

---

## Multi-stage Build Avanzato

La sezione precedente ha introdotto il concetto di multi-stage build con due stage (builder e runtime). In scenari reali, i pattern si fanno piu sofisticati. Questa sezione approfondisce le strategie avanzate per costruire immagini Python minimali e sicure.

### Pattern a Tre Stage: Base, Builder, Runtime

Il pattern a tre stage separa le responsabilita in modo ancora piu granulare. Lo stage `base` definisce la configurazione comune (variabili d'ambiente, utente), lo stage `builder` compila le dipendenze, e lo stage `runtime` contiene solo l'applicazione finale.

```dockerfile
# ============================================
# STAGE 1: Base — configurazione condivisa
# ============================================
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Utente non-root definito una volta sola
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

WORKDIR /app

# ============================================
# STAGE 2: Builder — compila le dipendenze
# ============================================
FROM base AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libffi-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Crea un virtualenv isolato per le dipendenze
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================
# STAGE 3: Runtime — immagine finale minimale
# ============================================
FROM base AS runtime

# Solo le librerie runtime (no compilatori, no header)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
        tini \
    && rm -rf /var/lib/apt/lists/*

# Copia il virtualenv completo dallo stage builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY --chown=appuser:appuser . .
USER appuser

ENTRYPOINT ["tini", "--"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Virtualenv Copy vs Wheels: Due Approcci

Esistono due approcci principali per trasferire le dipendenze dallo stage builder a quello runtime.

**Approccio 1 — Copia del virtualenv** (mostrato sopra):

Si crea un virtualenv nello stage builder e lo si copia integralmente nello stage runtime. Vantaggi: semplice, tutto il virtualenv viene copiato con un solo `COPY`. Svantaggio: il virtualenv potrebbe contenere file non strettamente necessari (script di entry point, metadati pip).

**Approccio 2 — Wheel pre-compilate:**

Si creano le wheel nello stage builder e si installano nello stage runtime. Vantaggi: le wheel sono artefatti compilati portatili, l'installazione e velocissima. Svantaggio: piu verboso nel Dockerfile.

```dockerfile
# Builder: crea le wheel
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# Runtime: installa dalle wheel
FROM python:3.12-slim AS runtime
COPY --from=builder /build/wheels /tmp/wheels
RUN pip install --no-cache-dir --no-deps /tmp/wheels/* && \
    rm -rf /tmp/wheels
```

Il flag `--no-deps` durante l'installazione delle wheel e importante: impedisce a pip di risolvere nuovamente le dipendenze, poiche tutte le wheel necessarie sono gia presenti nella directory.

### Stage Condizionali con Target

Docker Buildx permette di selezionare uno stage specifico come target di build. Questo e utile per avere un singolo Dockerfile che supporta sia sviluppo che produzione:

```dockerfile
FROM python:3.12-slim AS base
# ... configurazione comune ...

FROM base AS development
RUN pip install --no-cache-dir debugpy pytest ruff mypy
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS production
COPY --from=builder /opt/venv /opt/venv
COPY . .
USER appuser
CMD ["gunicorn", "app.main:app", "-c", "gunicorn.conf.py"]
```

```bash
# Build per sviluppo
docker build --target development -t myapp:dev .

# Build per produzione
docker build --target production -t myapp:prod .
```

### Pattern per Applicazioni con Estensioni C Pesanti

Applicazioni che dipendono da librerie come numpy, pandas, scipy, o cryptography richiedono compilatori e header di sistema per il build ma non per il runtime. Il multi-stage e essenziale:

```dockerfile
FROM python:3.12 AS builder
# L'immagine full contiene gia build-essential, gcc, ecc.

WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

FROM python:3.12-slim AS runtime
# L'immagine slim non ha compilatori ma ha glibc
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libopenblas0 \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/wheels /tmp/wheels
RUN pip install --no-cache-dir /tmp/wheels/* && rm -rf /tmp/wheels
COPY . .
```

Qui si usa `python:3.12` (immagine completa) per lo stage builder perche include tutti gli strumenti di compilazione, e `python:3.12-slim` per il runtime. Le librerie `libopenblas0` e `libgomp1` sono dipendenze runtime di numpy/scipy; servono a runtime ma non a compile-time.

---

## uv Avanzato in Docker

`uv` ha rivoluzionato la gestione delle dipendenze Python in Docker. Questa sezione approfondisce i pattern avanzati che vanno oltre l'uso base mostrato nella sezione precedente.

### Installazione Ottimale di uv

Il modo consigliato per ottenere il binario `uv` nel Dockerfile e copiarlo dall'immagine ufficiale di Astral. Questo evita di scaricare e installare uv via pip o curl, e garantisce una versione specifica e riproducibile:

```dockerfile
# Pin della versione per riproducibilita
COPY --from=ghcr.io/astral-sh/uv:0.7.9 /uv /uvx /usr/local/bin/
```

Pinnare la versione esatta di uv (non usare `latest`) e fondamentale per build riproducibili. Se la versione di uv cambia tra una build e l'altra, la risoluzione delle dipendenze potrebbe produrre risultati diversi.

### Variabili d'Ambiente per uv in Docker

```dockerfile
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_CACHE_DIR=/tmp/uv-cache \
    UV_NO_PROGRESS=1
```

- `UV_COMPILE_BYTECODE=1`: compila i file `.pyc` durante l'installazione. Questo accelera il tempo di avvio dell'applicazione a scapito di un build leggermente piu lungo, tradeoff favorevole in produzione.
- `UV_LINK_MODE=copy`: forza la copia dei file anziche i link simbolici, necessario per la compatibilita con i layer Docker.
- `UV_PYTHON_DOWNLOADS=never`: impedisce a uv di scaricare una propria versione di Python, usando quella dell'immagine base.
- `UV_NO_PROGRESS=1`: disabilita le barre di progresso, inutili nei log di build CI/CD.

### Pattern Two-Step Sync per Layer Caching

Il pattern piu efficace con uv e il two-step sync, che separa l'installazione delle dipendenze dall'installazione del progetto stesso:

```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.7.9 /uv /uvx /usr/local/bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Step 1: installa solo le dipendenze (senza il progetto)
# Questo layer viene cachato se pyproject.toml e uv.lock non cambiano
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Step 2: copia il codice e installa il progetto
COPY . .
RUN uv sync --frozen --no-dev

USER 1000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Il flag `--frozen` e cruciale: impedisce a uv di aggiornare il file di lock durante il build. Se il lock file non e in sync con `pyproject.toml`, il build fallisce, garantendo riproducibilita.

### uv con Multi-stage e Distroless

Il pattern piu avanzato combina uv, multi-stage e immagini distroless per ottenere immagini sotto gli 80 MB:

```dockerfile
# Stage 1: installa dipendenze con uv
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.7.9 /uv /uvx /usr/local/bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

# Stage 2: runtime distroless
FROM gcr.io/distroless/python3-debian12 AS runtime

COPY --from=builder /app /app
WORKDIR /app

# Distroless non ha shell, solo exec form
ENTRYPOINT ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Cache Mount con BuildKit

BuildKit supporta cache mount persistenti tra build successive. Questo e particolarmente efficace con uv:

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.7.9 /uv /uvx /usr/local/bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./

# La cache di uv viene persistita tra build
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev
```

Il `--mount=type=cache` crea un volume effimero che persiste tra build ma non viene incluso nell'immagine finale. Questo riduce drasticamente i tempi di rebuild quando le dipendenze non cambiano.

---

## pip-compile e pip-sync nei Container

Prima dell'avvento di uv, il toolchain `pip-tools` (composto da `pip-compile` e `pip-sync`) era lo standard de facto per build riproducibili in Docker. Molti progetti esistenti ancora lo utilizzano, e comprenderne il funzionamento resta importante.

### Il Workflow pip-tools

`pip-compile` prende un file di input (`requirements.in`) con le dipendenze top-level e produce un file di output (`requirements.txt`) completamente risolto e pinnato. `pip-sync` installa esattamente le dipendenze elencate nel file compilato, rimuovendo qualsiasi pacchetto estraneo.

```bash
# requirements.in — dipendenze top-level
fastapi>=0.110
uvicorn[standard]
sqlalchemy>=2.0
psycopg[binary]
pydantic-settings
```

```bash
# Genera requirements.txt con tutte le versioni pinnate
pip-compile requirements.in --generate-hashes --output-file=requirements.txt

# Il risultato sara qualcosa come:
# fastapi==0.115.6 \
#     --hash=sha256:abc123...
# uvicorn[standard]==0.34.0 \
#     --hash=sha256:def456...
# ... tutte le sotto-dipendenze pinnate con hash
```

### Dockerfile con pip-sync

```dockerfile
FROM python:3.12-slim AS builder

RUN pip install --no-cache-dir pip-tools

WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

FROM python:3.12-slim AS runtime

RUN pip install --no-cache-dir pip-tools

WORKDIR /app
COPY --from=builder /build/wheels /tmp/wheels
COPY requirements.txt .

# pip-sync installa ESATTAMENTE le dipendenze elencate
RUN pip-sync requirements.txt --pip-args="--no-cache-dir --find-links /tmp/wheels" && \
    rm -rf /tmp/wheels && \
    pip uninstall -y pip-tools  # Rimuovi pip-tools dall'immagine finale

COPY . .
USER 1000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Hash Verification per la Supply Chain

Il flag `--generate-hashes` di pip-compile aggiunge gli hash SHA256 di ogni pacchetto al file di output. Durante l'installazione, pip verifica che gli hash corrispondano, proteggendo contro pacchetti manomessi o attacchi alla supply chain.

```bash
# requirements.txt generato con --generate-hashes
fastapi==0.115.6 \
    --hash=sha256:27399... \
    --hash=sha256:8b5e6...
```

Se un pacchetto viene sostituito con una versione malevola sul registry PyPI, l'hash non corrispondera e l'installazione fallira. Questo e un livello di sicurezza fondamentale per applicazioni in produzione.

### Separazione Dipendenze Dev e Produzione

```bash
# requirements-dev.in
-c requirements.txt   # Usa gli stessi pin del file di produzione
pytest
ruff
mypy
debugpy

# Compila separatamente
pip-compile requirements-dev.in -o requirements-dev.txt
```

Il flag `-c requirements.txt` (constraint) garantisce che le dipendenze di sviluppo usino le stesse versioni delle dipendenze condivise con la produzione, evitando conflitti.

### Migrazione da pip-tools a uv

Per i progetti che vogliono migrare, uv e compatibile con i file `requirements.txt` esistenti:

```bash
# uv puo leggere requirements.txt generati da pip-compile
uv pip install -r requirements.txt

# Oppure: genera un uv.lock dal pyproject.toml esistente
uv lock
```

La migrazione e graduale: si puo iniziare usando `uv pip install` come drop-in replacement di pip, poi passare a `uv sync` con il lock file nativo quando si e pronti.

---

## Immagini Distroless per Python

Le immagini distroless rappresentano l'approccio piu radicale alla minimizzazione delle immagini container. Create originariamente da Google, contengono solo l'applicazione e le sue dipendenze runtime — niente shell, niente package manager, niente strumenti di debug.

### Perche Distroless

| Aspetto | `python:3.12-slim` | `gcr.io/distroless/python3` | Chainguard `python` |
|---|---|---|---|
| Dimensione | ~150 MB | ~50 MB | ~40 MB |
| Shell | Si (`/bin/sh`, `/bin/bash`) | No | No (versione `:latest`) |
| Package manager | Si (`apt-get`) | No | No |
| Utente root | Si (default) | No (nonroot default) | No (nonroot default) |
| CVE note tipiche | 20-50 | 0-5 | 0-3 |

L'assenza di shell e un vantaggio di sicurezza enorme: anche se un attaccante riesce a ottenere l'esecuzione di codice arbitrario nel container, non puo aprire una shell interattiva, scaricare strumenti aggiuntivi o esplorare il filesystem.

### Google Distroless per Python

Google fornisce immagini distroless specifiche per Python basate su Debian:

```dockerfile
# Multi-stage: builder + distroless runtime
FROM python:3.12-slim AS builder

WORKDIR /app

# Installa dipendenze in un virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Runtime distroless
FROM gcr.io/distroless/python3-debian12

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /app

# DEVE essere exec form — non c'e shell per la forma shell
ENTRYPOINT ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Chainguard Python Images

Chainguard offre un'alternativa a Google Distroless con aggiornamenti piu frequenti e SBOM (Software Bill of Materials) integrati:

```dockerfile
FROM python:3.12-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# Chainguard Python come runtime
FROM cgr.dev/chainguard/python:latest AS runtime

WORKDIR /app
COPY --from=builder /build/wheels /tmp/wheels
RUN pip install --no-cache-dir --no-deps /tmp/wheels/* && \
    rm -rf /tmp/wheels

COPY . .

ENTRYPOINT ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Distroless con Debug Tag

Per scenari dove serve ispezionare il container in produzione, le immagini distroless offrono un tag `:debug` che include una shell BusyBox minimale:

```bash
# Usa il tag debug SOLO per troubleshooting, mai in produzione permanente
FROM gcr.io/distroless/python3-debian12:debug

# In produzione: usa il tag standard senza shell
FROM gcr.io/distroless/python3-debian12
```

```bash
# Accedi alla shell nel container distroless:debug
docker exec -it container_name /busybox/sh
```

### Scelta tra Google Distroless e Chainguard

| Criterio | Google Distroless | Chainguard |
|---|---|---|
| Frequenza aggiornamenti | Settimanale | Giornaliera |
| SBOM integrato | No | Si (nativo) |
| Firma immagini (Sigstore) | Si | Si |
| Supporto Python versions | 3.11, 3.12 | 3.11, 3.12, 3.13 |
| Immagine `:debug` con shell | Si (BusyBox) | Si (tag `:latest-dev`) |
| Licensing | Apache 2.0 | Gratuito per uso non commerciale |
| Base OS | Debian 12 | Wolfi (alpine-like, glibc) |

Chainguard usa Wolfi, una distribuzione progettata specificamente per i container, che combina le dimensioni ridotte di Alpine con la compatibilita glibc di Debian. Questo risolve il problema storico di Alpine con i pacchetti Python che richiedono glibc.

### Limitazioni delle Immagini Distroless

- **Debugging difficile**: senza shell, `docker exec -it container bash` non funziona. Si devono usare strumenti esterni come `kubectl debug` (Kubernetes) o il tag `:debug`.
- **Dipendenze di sistema**: se l'applicazione Python richiede librerie C a runtime (es. `libpq` per psycopg, `libssl` per cryptography), queste devono essere copiate manualmente dallo stage builder.
- **Non adatte allo sviluppo**: usare distroless solo per il deploy di produzione, mai per ambienti di sviluppo.
- **Aggiornamenti di sicurezza**: senza un package manager, le vulnerabilita nelle librerie di sistema richiedono un rebuild completo dell'immagine. Automatizzare i rebuild periodici con Renovate o Dependabot e essenziale.

```dockerfile
# Copia librerie di sistema necessarie da Debian
FROM python:3.12-slim AS builder

# Identifica le librerie necessarie
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# ...installa dipendenze Python...

FROM gcr.io/distroless/python3-debian12

# Copia libpq e le sue dipendenze
COPY --from=builder /usr/lib/x86_64-linux-gnu/libpq.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libldap*.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/liblber*.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libsasl2.so* /usr/lib/x86_64-linux-gnu/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libgssapi*.so* /usr/lib/x86_64-linux-gnu/
```

---

## Health Check Avanzati

La sezione precedente ha mostrato un health check base con `curl`. In scenari reali, gli health check devono essere piu sofisticati per distinguere tra un'applicazione viva ma degradata e un'applicazione completamente sana.

### Liveness vs Readiness vs Startup

In Kubernetes (e per buona pratica anche in Docker Compose), esistono tre tipi di probe:

- **Liveness**: l'applicazione e viva? Se no, il container viene riavviato. Deve essere leggero e veloce.
- **Readiness**: l'applicazione e pronta a ricevere traffico? Se no, il container viene rimosso dal load balancer ma non riavviato.
- **Startup**: usata durante l'avvio iniziale per applicazioni lente a partire. Impedisce che la liveness probe uccida un container che sta ancora caricando.

### Health Check Python Completo

```python
# app/health.py
import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Response, status
from sqlalchemy import text
from redis.asyncio import Redis

router = APIRouter(tags=["health"])

@router.get("/health/live")
async def liveness():
    """Liveness probe: il processo Python e vivo e risponde."""
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}

@router.get("/health/ready")
async def readiness(response: Response):
    """Readiness probe: verifica le dipendenze critiche."""
    checks = {}
    all_healthy = True

    # Verifica database
    try:
        async with get_db_session() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {type(e).__name__}"
        all_healthy = False

    # Verifica Redis
    try:
        redis = Redis.from_url(settings.REDIS_URL)
        await redis.ping()
        await redis.aclose()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {type(e).__name__}"
        all_healthy = False

    if not all_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if all_healthy else "degraded",
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@router.get("/health/startup")
async def startup_check():
    """Startup probe: verifica che l'applicazione sia completamente inizializzata."""
    return {"status": "started", "version": "1.0.0"}
```

### Health Check nel Dockerfile senza curl

Un problema comune con gli health check e la dipendenza da `curl`, che aggiunge software non necessario all'immagine. Si puo usare Python stesso per gli health check:

```dockerfile
# Health check senza curl, usando Python
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/live')" || exit 1
```

Oppure, per un check piu robusto, creare uno script dedicato:

```python
#!/usr/bin/env python3
# healthcheck.py
import sys
import urllib.request
import json

try:
    with urllib.request.urlopen("http://localhost:8000/health/ready", timeout=5) as resp:
        data = json.loads(resp.read())
        if data.get("status") != "ready":
            sys.exit(1)
except Exception:
    sys.exit(1)
```

```dockerfile
COPY healthcheck.py .
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD ["python", "healthcheck.py"]
```

### Health Check in Docker Compose

```yaml
services:
  web:
    build: .
    healthcheck:
      test: ["CMD", "python", "healthcheck.py"]
      interval: 30s
      timeout: 10s
      start_period: 15s
      retries: 3

  celery-worker:
    build: .
    command: celery -A app.celery_app worker --loglevel=info
    healthcheck:
      # Celery: verifica che il worker sia vivo
      test: ["CMD-SHELL", "celery -A app.celery_app inspect ping --timeout 10"]
      interval: 30s
      timeout: 15s
      retries: 3
```

### Parametri Health Check — Guida alla Scelta

| Parametro | Default | Consiglio |
|---|---|---|
| `interval` | 30s | 10-30s per servizi critici, 60s per servizi secondari |
| `timeout` | 30s | 5-10s, non piu del 50% dell'intervallo |
| `start_period` | 0s | Tempo di avvio dell'app + margine (15-60s per Python) |
| `retries` | 3 | 2-5, numero di fallimenti prima di dichiarare unhealthy |

Il `start_period` e particolarmente importante per le applicazioni Python: il caricamento di moduli pesanti (Django con molte app, applicazioni ML con modelli) puo richiedere 10-30 secondi. Senza un `start_period` adeguato, il container potrebbe essere dichiarato unhealthy prima ancora di aver completato l'avvio.

---

## Docker Compose Avanzato per Sviluppo Python

Questa sezione approfondisce pattern Docker Compose specifici per il workflow di sviluppo Python, oltre le configurazioni base mostrate in precedenza.

### Watch Mode con Docker Compose

Docker Compose 2.22+ supporta la direttiva `watch` che sincronizza automaticamente i file dal filesystem locale al container, senza dover configurare volume mount manuali:

```yaml
services:
  web:
    build: .
    develop:
      watch:
        # Sincronizza modifiche al codice (hot reload)
        - action: sync
          path: ./app
          target: /app/app

        # Rebuild se cambiano le dipendenze
        - action: rebuild
          path: pyproject.toml

        # Rebuild se cambia il lock file
        - action: rebuild
          path: uv.lock
```

```bash
# Avvia con watch mode
docker compose watch
```

Il vantaggio rispetto ai volume mount e che `watch` gestisce automaticamente la logica di sync vs rebuild: i file di codice vengono sincronizzati (senza rebuild), mentre le modifiche ai file di dipendenze triggerano un rebuild completo dell'immagine.

### Profili per Servizi Opzionali

Non tutti i servizi sono necessari per ogni task di sviluppo. I profili Docker Compose permettono di raggruppare i servizi:

```yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
    # Nessun profilo: sempre avviato

  db:
    image: postgres:16-alpine
    # Nessun profilo: sempre avviato

  redis:
    image: redis:7-alpine
    # Nessun profilo: sempre avviato

  celery-worker:
    build: .
    command: celery -A app.celery_app worker
    profiles: [worker]

  celery-beat:
    build: .
    command: celery -A app.celery_app beat
    profiles: [worker]

  flower:
    build: .
    command: celery -A app.celery_app flower
    ports:
      - "5555:5555"
    profiles: [monitoring]

  mailpit:
    image: axllent/mailpit:latest
    ports:
      - "1025:1025"
      - "8025:8025"
    profiles: [email]

  pgadmin:
    image: dpage/pgadmin4:latest
    ports:
      - "5050:80"
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@example.com
      PGADMIN_DEFAULT_PASSWORD: admin
    profiles: [monitoring]
```

```bash
# Solo web + db + redis
docker compose up

# Con worker Celery
docker compose --profile worker up

# Con tutto il monitoring
docker compose --profile worker --profile monitoring up

# Con servizio email fake
docker compose --profile email up
```

### Init Container Pattern

Per eseguire operazioni di inizializzazione (migrazioni database, seed dei dati) prima dell'avvio dell'applicazione:

```yaml
services:
  migrate:
    build: .
    command: alembic upgrade head
    depends_on:
      db:
        condition: service_healthy
    restart: "no"  # Esegui una volta e fermati

  seed:
    build: .
    command: python scripts/seed_data.py
    depends_on:
      migrate:
        condition: service_completed_successfully
    restart: "no"

  web:
    build: .
    depends_on:
      seed:
        condition: service_completed_successfully
```

### Env Files e Sostituzione Variabili

```yaml
services:
  web:
    build: .
    env_file:
      - .env                    # Variabili di base
      - .env.local              # Override locali (non committato)
    environment:
      # Override espliciti che hanno precedenza su env_file
      - LOG_LEVEL=${LOG_LEVEL:-debug}
      - DATABASE_URL=postgresql://${DB_USER:-postgres}:${DB_PASS:-password}@db:5432/${DB_NAME:-appdb}
```

```bash
# .env
DB_USER=postgres
DB_PASS=password
DB_NAME=appdb
SECRET_KEY=dev-only-secret-change-in-production

# .env.local (gitignored)
DB_PASS=my-local-password
SECRET_KEY=override-local-secret
```

La precedenza e: variabili d'ambiente della shell > `environment` nel compose > `.env.local` > `.env`.

---

## Debugging Avanzato in Container

La sezione precedente ha introdotto debugpy e pdb. Qui approfondiamo scenari piu complessi di debugging remoto e tecniche avanzate.

### debugpy con Attach Condizionale

Invece di avviare debugpy incondizionatamente, un pattern piu robusto usa un flag per abilitarlo solo quando necessario:

```python
# app/debug.py
import os
import logging

logger = logging.getLogger(__name__)

def setup_debugger():
    """Configura debugpy solo se richiesto esplicitamente."""
    if os.getenv("DEBUGPY_ENABLE", "").lower() != "true":
        return

    try:
        import debugpy
        port = int(os.getenv("DEBUGPY_PORT", "5678"))
        debugpy.listen(("0.0.0.0", port))
        logger.info(f"debugpy in ascolto sulla porta {port}")

        if os.getenv("DEBUGPY_WAIT_FOR_CLIENT", "").lower() == "true":
            logger.info("In attesa del client debugger...")
            debugpy.wait_for_client()
            logger.info("Client debugger connesso")
    except ImportError:
        logger.warning("debugpy non installato, debugging remoto disabilitato")
```

```python
# app/main.py
from app.debug import setup_debugger

setup_debugger()

from fastapi import FastAPI
app = FastAPI()
```

### Configurazione PyCharm per Remote Debug

PyCharm Professional supporta il debugging remoto di applicazioni Python in container Docker. La configurazione richiede un interprete Python remoto:

```yaml
# docker-compose.override.yml per PyCharm
services:
  web:
    ports:
      - "8000:8000"
      - "5678:5678"
    environment:
      - DEBUGPY_ENABLE=true
      - DEBUGPY_PORT=5678
    # Per PyCharm: usa pydevd-pycharm invece di debugpy
    # pip install pydevd-pycharm~=242.23726.102
```

In PyCharm: Run > Edit Configurations > + > Python Debug Server. Impostare l'host su `localhost` e la porta su `5678`. Configurare i path mappings: `/app` nel container corrisponde alla directory del progetto locale.

### Profiling in Container con py-spy

`py-spy` permette di fare profiling di applicazioni Python in esecuzione senza modificare il codice o riavviare il processo:

```bash
# Installa py-spy nel container (o meglio, montalo come volume)
docker exec -u root container_name pip install py-spy

# Profiling top-like in tempo reale
docker exec -u root container_name py-spy top --pid 1

# Genera un flame graph SVG
docker exec -u root container_name py-spy record \
    --pid 1 \
    --output /tmp/profile.svg \
    --duration 30

# Copia il flame graph sull'host
docker cp container_name:/tmp/profile.svg ./profile.svg
```

Attenzione: py-spy richiede la capability `SYS_PTRACE`. In Docker Compose:

```yaml
services:
  web:
    cap_add:
      - SYS_PTRACE  # Necessario per py-spy, SOLO in sviluppo
```

### Breakpoint Condizionali con debugpy

debugpy supporta breakpoint condizionali che si attivano solo quando specifiche condizioni sono vere. Questo e utile per debuggare problemi che si verificano solo con determinati dati:

```python
import debugpy

# Breakpoint che si attiva solo per un utente specifico
if user_id == "problematic-user-123":
    debugpy.breakpoint()

# Oppure, breakpoint con log point (stampa senza fermarsi)
# Configurabile nell'IDE: Log Message = "request_id={request_id}, status={status}"
```

### Dump dello Stack di Tutti i Thread

Per debuggare deadlock o blocchi in applicazioni multi-thread containerizzate:

```bash
# Invia SIGUSR1 al processo Python per stampare lo stack trace
docker exec container_name kill -USR1 1

# Oppure con faulthandler abilitato nel codice:
```

```python
# app/main.py — abilita faulthandler per dump dello stack su SIGUSR1
import faulthandler
import signal

faulthandler.register(signal.SIGUSR1)
```

---

## .dockerignore Specifico per Python

Un `.dockerignore` ben configurato e fondamentale per la sicurezza, la velocita di build e la dimensione del contesto. Ecco un file completo con la spiegazione del rationale per ogni pattern.

### .dockerignore Completo e Annotato

```dockerignore
# ==============================================
# AMBIENTI VIRTUALI PYTHON
# Rationale: possono pesare centinaia di MB e contengono binari
# specifici per l'architettura dell'host, incompatibili col container
# ==============================================
.venv/
venv/
env/
.conda/
*.egg-info/

# ==============================================
# CACHE PYTHON
# Rationale: i .pyc compilati sull'host non sono validi nel container
# (versione Python diversa, path diversi). Occupano spazio inutilmente.
# ==============================================
__pycache__/
*.py[cod]
*.pyo
.mypy_cache/
.ruff_cache/
.pytest_cache/
.hypothesis/

# ==============================================
# BUILD ARTIFACTS
# Rationale: artefatti di build precedenti non servono nel container,
# il Dockerfile genera i propri artefatti.
# ==============================================
build/
dist/
*.egg
*.whl
sdist/

# ==============================================
# FILE DI CONFIGURAZIONE LOCALE E SEGRETI
# Rationale: CRITICO — i file .env contengono segreti che non devono
# MAI essere inclusi nell'immagine Docker. Anche se non copiati
# esplicitamente, fanno parte del contesto di build.
# ==============================================
.env
.env.*
*.env
!.env.example
secrets/
credentials/
*.pem
*.key

# ==============================================
# GIT E CONTROLLO VERSIONE
# Rationale: la directory .git puo pesare piu del codice stesso.
# Non serve nel container e contiene la storia completa del repository.
# ==============================================
.git/
.gitignore
.gitattributes
.gitmodules

# ==============================================
# DOCKER (META)
# Rationale: i file Docker stessi non servono dentro il container.
# Includerli potrebbe esporre la struttura dell'infrastruttura.
# ==============================================
Dockerfile*
docker-compose*.yml
.dockerignore

# ==============================================
# IDE E EDITOR
# Rationale: configurazioni dell'editor specifiche per lo sviluppatore,
# non hanno senso nel container.
# ==============================================
.vscode/
.idea/
*.swp
*.swo
*~
.project
.settings/

# ==============================================
# TEST E DOCUMENTAZIONE
# Rationale: nella maggior parte dei deploy di produzione, i test
# e la documentazione non servono. Se servono (es. per eseguire
# test in CI), commentare queste righe.
# ==============================================
tests/
test/
docs/
*.md
!README.md
htmlcov/
.coverage
.coverage.*
coverage.xml
junit.xml

# ==============================================
# DATI E LOG
# Rationale: dati locali e log non devono essere inclusi nell'immagine.
# I log del container vengono gestiti da Docker.
# ==============================================
data/
*.log
logs/
*.sqlite3
*.db

# ==============================================
# OS FILES
# Rationale: file di sistema operativo specifici per l'host.
# ==============================================
.DS_Store
Thumbs.db
desktop.ini

# ==============================================
# NOTEBOOK JUPYTER
# Rationale: i notebook contengono output eseguiti che possono
# includere dati sensibili nei metadata o negli output delle celle.
# ==============================================
*.ipynb
.ipynb_checkpoints/

# ==============================================
# TOOL DI INFRASTRUTTURA
# Rationale: configurazioni Terraform, Ansible, ecc. non servono
# nel container dell'applicazione.
# ==============================================
terraform/
ansible/
*.tf
*.tfstate*
.terraform/
```

### Verifica del Contesto di Build

Per verificare cosa viene incluso nel contesto di build:

```bash
# Mostra cosa Docker riceve come contesto (simula il .dockerignore)
# Usa un Dockerfile dummy per misurare
cat > /tmp/Dockerfile.ctx << 'EOF'
FROM busybox
COPY . /ctx
RUN du -sh /ctx && find /ctx -type f | wc -l
EOF

docker build -f /tmp/Dockerfile.ctx --no-cache -t ctx-check . 2>&1 | tail -5
```

Un contesto di build troppo grande (> 100 MB per un progetto tipico) indica che il `.dockerignore` necessita di miglioramenti.

### Errori Comuni nel .dockerignore

**Escludere troppo:**

```dockerignore
# ERRORE: esclude anche i migration files necessari all'app
migrations/
alembic/

# ERRORE: esclude il file di configurazione necessario a runtime
config/
*.toml
```

**Non escludere abbastanza:**

```dockerignore
# MANCANTE: i notebook Jupyter possono contenere output
# con dati sensibili (token, risultati di query, PII)
# *.ipynb    <-- decommenta se non serve

# MANCANTE: la directory node_modules per progetti misti Python+JS
# node_modules/
```

**Pattern con negazione:**

```dockerignore
# Escludi tutti i file .env
*.env
# Ma includi il file di esempio (.env.example)
!.env.example
```

L'ordine conta: le negazioni (`!`) devono venire dopo le esclusioni. Docker processa il `.dockerignore` dall'alto verso il basso, e l'ultima regola che matcha un file vince.

---

## Security Scanning delle Dipendenze Python

Oltre alla scansione dell'immagine Docker con Trivy (trattata nella sezione Sicurezza), e fondamentale scansionare le dipendenze Python stesse alla ricerca di vulnerabilita note.

### pip-audit — Lo Scanner del PyPA

`pip-audit` e sviluppato dalla Python Packaging Authority e consulta il database OSV (Open Source Vulnerabilities):

```bash
# Scansione delle dipendenze installate nel container
docker exec container_name pip-audit

# Scansione di un file requirements.txt specifico
docker run --rm -v $(pwd):/app python:3.12-slim \
    sh -c "pip install pip-audit && pip-audit -r /app/requirements.txt"

# Output in formato JSON per integrazione CI
docker exec container_name pip-audit --format json --output /tmp/audit.json

# Fix automatico: genera un requirements.txt aggiornato
docker exec container_name pip-audit --fix --dry-run -r requirements.txt
```

### Safety — Scansione con Database Proprietario

`safety` di Safety Cybersecurity (ex PyUp) usa un database proprietario che include vulnerabilita non ancora presenti nel database pubblico:

```bash
# Scansione base
docker exec container_name safety check

# Scansione di un file requirements
safety check -r requirements.txt

# Output JSON per CI
safety check --json --output report.json

# Con chiave API per il database completo (gratuito per open source)
safety check --key $SAFETY_API_KEY
```

### Grype — Scanner Multi-Ecosistema

Grype di Anchore analizza sia le dipendenze di sistema che quelle Python nell'immagine Docker:

```bash
# Scansione dell'intera immagine (OS + Python deps)
grype myapp:latest

# Solo dipendenze Python
grype myapp:latest --only-fixed

# Output in formato SARIF per integrazione GitHub
grype myapp:latest -o sarif > grype-results.sarif

# Con soglia di severita
grype myapp:latest --fail-on critical
```

### Integrazione nella Pipeline CI/CD

```yaml
# .github/workflows/security.yml
name: Security Scan
on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: "0 6 * * 1"  # Ogni lunedi alle 06:00 UTC

jobs:
  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pip-audit safety

      - name: pip-audit scan
        run: pip-audit --format json --output pip-audit-report.json
        continue-on-error: true

      - name: Safety scan
        run: safety check --json --output safety-report.json
        continue-on-error: true

      - name: Grype image scan
        uses: anchore/scan-action@v6
        with:
          image: myapp:latest
          fail-build: true
          severity-cutoff: high
          output-format: sarif

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: security-reports
          path: |
            pip-audit-report.json
            safety-report.json
```

### Scansione Continua con Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pypa/pip-audit
    rev: v2.7.3
    hooks:
      - id: pip-audit
        args: ["--require-hashes", "--disable-pip"]
```

### Politica di Risposta alle Vulnerabilita

| Severita CVSS | Tempo di Risposta | Azione |
|---|---|---|
| Critica (9.0-10.0) | 24 ore | Patch immediata, rebuild immagine, deploy |
| Alta (7.0-8.9) | 1 settimana | Pianifica patch nel prossimo sprint |
| Media (4.0-6.9) | 1 mese | Includi nel prossimo ciclo di aggiornamento |
| Bassa (0.1-3.9) | Prossimo trimestre | Monitora, aggiorna quando conveniente |

### Docker Scout — Scanning Integrato

Docker Scout e lo scanner di vulnerabilita integrato nella CLI Docker. Non richiede installazione di tool esterni:

```bash
# Scansione rapida dell'immagine
docker scout cves myapp:latest

# Solo vulnerabilita critiche e alte
docker scout cves --only-severity critical,high myapp:latest

# Confronta due versioni dell'immagine
docker scout compare myapp:latest myapp:previous

# Raccomandazioni per aggiornamenti base image
docker scout recommendations myapp:latest
```

### Dockerfile Multi-Stage per Scansione in CI

Un pattern utile e includere la scansione delle dipendenze come stage nel Dockerfile stesso. Se la scansione fallisce, il build si interrompe:

```dockerfile
# Stage: dependency audit
FROM python:3.12-slim AS audit

WORKDIR /audit
COPY requirements.txt .
RUN pip install --no-cache-dir pip-audit && \
    pip install --no-cache-dir -r requirements.txt && \
    pip-audit --strict --desc

# Se pip-audit trova vulnerabilita, il build fallisce qui
# Lo stage successivo non viene eseguito

FROM python:3.12-slim AS runtime
# ... resto del Dockerfile ...
```

### SBOM — Software Bill of Materials

Docker Buildx puo generare automaticamente un SBOM dell'immagine, utile per la conformita e l'audit trail:

```bash
# Genera SBOM durante il build
docker buildx build --sbom=true -t myapp:latest .

# Ispeziona l'SBOM dell'immagine
docker buildx imagetools inspect myapp:latest --format "{{json .SBOM}}"
```

In ambienti regolamentati (finanza, sanita, pubblica amministrazione), l'SBOM e spesso un requisito obbligatorio per i deploy in produzione. Documenta esattamente quali librerie e versioni sono incluse nell'immagine, facilitando la risposta a nuove vulnerabilita.

---

## Signal Handling — SIGTERM e SIGINT

La gestione dei segnali e un aspetto critico per le applicazioni Python containerizzate. Quando Docker ferma un container (con `docker stop` o durante un rolling update in Kubernetes), invia un segnale SIGTERM al processo con PID 1. Se il processo non termina entro il grace period (10 secondi per default), Docker invia SIGKILL, che uccide il processo immediatamente senza possibilita di cleanup.

### Il Problema del PID 1

Il processo con PID 1 in un container Linux ha un comportamento speciale: non riceve segnali con handler di default. Questo significa che se il processo Python e PID 1, SIGTERM viene ignorato a meno che non sia esplicitamente gestito.

**Il problema della forma shell:**

```dockerfile
# SBAGLIATO: forma shell — avvia /bin/sh -c "python app.py"
# /bin/sh e PID 1, Python e un sotto-processo che NON riceve SIGTERM
CMD python app.py

# CORRETTO: forma exec — Python e PID 1 e riceve SIGTERM direttamente
CMD ["python", "app.py"]
```

Nella forma shell, `/bin/sh` riceve SIGTERM ma non lo inoltra ai processi figli. Python non sa che deve terminare e Docker e costretto a inviare SIGKILL dopo il timeout.

### Tini come Init Process

`tini` e un init process minimale progettato per i container. Risolve il problema del PID 1 gestendo correttamente l'inoltro dei segnali e la raccolta dei processi zombie:

```dockerfile
# Installa tini
RUN apt-get update && \
    apt-get install -y --no-install-recommends tini && \
    rm -rf /var/lib/apt/lists/*

# tini e PID 1, inoltra SIGTERM a Python
ENTRYPOINT ["tini", "--"]
CMD ["python", "app.py"]
```

Docker fornisce anche il flag `--init` che aggiunge automaticamente tini:

```bash
# Equivalente all'uso di tini nel Dockerfile
docker run --init myapp
```

### Signal Handler in Python

Per applicazioni che devono eseguire operazioni di cleanup prima della terminazione (chiudere connessioni al database, completare task in corso, salvare stato):

```python
# app/signals.py
import signal
import sys
import logging
import asyncio

logger = logging.getLogger(__name__)

_shutdown_event = asyncio.Event()

def handle_sigterm(signum, frame):
    """Handler per SIGTERM: avvia graceful shutdown."""
    sig_name = signal.Signals(signum).name
    logger.info(f"Ricevuto {sig_name}, avvio graceful shutdown...")
    _shutdown_event.set()

def setup_signal_handlers():
    """Registra gli handler per SIGTERM e SIGINT."""
    signal.signal(signal.SIGTERM, handle_sigterm)
    signal.signal(signal.SIGINT, handle_sigterm)
    logger.info("Signal handlers registrati per SIGTERM e SIGINT")

async def wait_for_shutdown():
    """Attende il segnale di shutdown."""
    await _shutdown_event.wait()
```

```python
# app/main.py — uso dei signal handlers
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.signals import setup_signal_handlers

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_signal_handlers()
    yield
    # Shutdown — cleanup qui
    await close_db_pool()
    await close_redis_connection()

app = FastAPI(lifespan=lifespan)
```

### STOPSIGNAL nel Dockerfile

Per default, Docker invia SIGTERM. Alcune applicazioni richiedono un segnale diverso:

```dockerfile
# Cambia il segnale di stop (default: SIGTERM)
STOPSIGNAL SIGINT

# Utile per applicazioni che gestiscono SIGINT ma non SIGTERM
# (raro ma possibile con codice legacy)
```

### Grace Period e stop_grace_period

```yaml
# docker-compose.yml
services:
  web:
    build: .
    stop_grace_period: 30s  # Default: 10s
    # Gunicorn ha bisogno di tempo per terminare le richieste in corso
```

```bash
# Override da riga di comando
docker stop --time 30 container_name
```

Per applicazioni web, 30 secondi e un buon valore: permette di completare le richieste HTTP in corso e chiudere le connessioni al database in modo ordinato. Per worker Celery con task lunghi, potrebbe servire un grace period piu lungo (60-120 secondi).

### Graceful Shutdown con Gunicorn

Gunicorn gestisce SIGTERM nativamente: quando riceve il segnale, smette di accettare nuove connessioni, attende che i worker completino le richieste in corso, e poi termina. Il parametro `--graceful-timeout` controlla quanto tempo attendere:

```dockerfile
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--graceful-timeout", "30", \
     "--timeout", "120", \
     "--bind", "0.0.0.0:8000"]
```

---

## Gunicorn e Uvicorn in Docker

La configurazione del server ASGI/WSGI in Docker richiede considerazioni specifiche legate al modello di esecuzione dei container.

### Gunicorn come Process Manager

In produzione, Gunicorn funge da process manager che gestisce multipli worker Uvicorn. Ogni worker e un processo separato che gestisce le richieste. Se un worker crasha (out of memory, eccezione non gestita), Gunicorn lo riavvia automaticamente.

```python
# gunicorn.conf.py — configurazione per container Docker
import multiprocessing
import os

# Bind alla porta esposta dal container
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

# Worker — in container, il numero di CPU e limitato da cgroup
# Non usare multiprocessing.cpu_count() in container con CPU limit
workers = int(os.getenv("WEB_CONCURRENCY", "4"))
worker_class = "uvicorn.workers.UvicornWorker"

# Usa /dev/shm per i file temporanei dei worker
# Evita I/O su disco per la comunicazione inter-worker
worker_tmp_dir = "/dev/shm"

# Timeout
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
graceful_timeout = 30
keepalive = 5

# Preload: carica l'applicazione nel master prima del fork
# Vantaggi: riduce l'uso di memoria (copy-on-write), avvio piu veloce
# Svantaggi: le modifiche richiedono restart completo
preload_app = os.getenv("GUNICORN_PRELOAD", "true").lower() == "true"

# Logging
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Max requests: riavvia il worker dopo N richieste per prevenire memory leak
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "50"))

# Limita il numero di connessioni pendenti
backlog = 2048
```

### CPU Count nei Container

Un problema insidioso e che `multiprocessing.cpu_count()` in un container restituisce il numero di CPU dell'host, non quelle allocate al container tramite cgroup. Se l'host ha 64 CPU ma il container ha un limit di 2, `cpu_count()` restituisce 64, causando la creazione di troppi worker.

```python
# Modo corretto per determinare le CPU disponibili in un container
import os

def get_container_cpu_count() -> int:
    """Restituisce il numero di CPU disponibili, rispettando i cgroup limits."""
    # cgroup v2 (moderno)
    try:
        with open("/sys/fs/cgroup/cpu.max") as f:
            quota, period = f.read().strip().split()
            if quota != "max":
                return max(1, int(quota) // int(period))
    except (FileNotFoundError, ValueError):
        pass

    # cgroup v1 (legacy)
    try:
        with open("/sys/fs/cgroup/cpu/cpu.cfs_quota_us") as f:
            quota = int(f.read().strip())
        with open("/sys/fs/cgroup/cpu/cpu.cfs_period_us") as f:
            period = int(f.read().strip())
        if quota > 0:
            return max(1, quota // period)
    except (FileNotFoundError, ValueError):
        pass

    # Fallback
    return os.cpu_count() or 1
```

In alternativa, impostare `WEB_CONCURRENCY` esplicitamente nel Dockerfile o nel Compose file:

```yaml
services:
  web:
    environment:
      - WEB_CONCURRENCY=4  # Esplicito, non derivato da cpu_count()
    deploy:
      resources:
        limits:
          cpus: "2.0"
```

### Uvicorn Standalone vs Gunicorn + Uvicorn

| Scenario | Server Consigliato |
|---|---|
| Sviluppo locale | Uvicorn con `--reload` |
| Produzione con 1 worker | Uvicorn standalone |
| Produzione con N worker | Gunicorn + UvicornWorker |
| Kubernetes con autoscaling | Uvicorn standalone (1 worker per pod) |

In Kubernetes, ogni pod ha tipicamente un singolo processo. Lo scaling avviene aggiungendo pod, non worker. In questo caso, Uvicorn standalone e preferibile perche ha meno overhead e piu semplice da monitorare.

```dockerfile
# Produzione Kubernetes: Uvicorn standalone
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--log-level", "info", \
     "--no-access-log"]

# Produzione Docker Compose: Gunicorn + Uvicorn
CMD ["gunicorn", "app.main:app", "-c", "gunicorn.conf.py"]
```

### Uvicorn con uvloop e httptools

`uvloop` e `httptools` sono implementazioni ad alte prestazioni del loop asyncio e del parser HTTP rispettivamente. Entrambi sono scritti in C/Cython e offrono performance significativamente migliori:

```dockerfile
# requirements.txt — includi uvloop e httptools
uvicorn[standard]  # Include uvloop, httptools, websockets
# oppure esplicitamente:
uvicorn
uvloop
httptools
```

`uvicorn[standard]` installa automaticamente uvloop e httptools. Uvicorn li usa automaticamente se disponibili.

### Configurazione Memory Limit e OOM Killer

In un container Docker con limiti di memoria, il kernel Linux invoca l'OOM Killer quando il processo supera il limite. Per applicazioni Python, e fondamentale configurare i worker di Gunicorn in modo che il consumo di memoria totale resti sotto il limite:

```python
# gunicorn.conf.py — calcolo worker basato sulla memoria disponibile
import os

# Leggi il memory limit del container (cgroup v2)
def get_memory_limit_mb() -> int:
    try:
        with open("/sys/fs/cgroup/memory.max") as f:
            limit = f.read().strip()
            if limit == "max":
                return 2048  # No limit, usa un default ragionevole
            return int(limit) // (1024 * 1024)
    except FileNotFoundError:
        # cgroup v1 fallback
        try:
            with open("/sys/fs/cgroup/memory/memory.limit_in_bytes") as f:
                return int(f.read().strip()) // (1024 * 1024)
        except FileNotFoundError:
            return 2048

memory_mb = get_memory_limit_mb()
# Riserva 256MB per overhead Python/OS, dividi il resto per ~150MB per worker
workers = max(1, min(8, (memory_mb - 256) // 150))
```

Ogni worker Uvicorn con un'applicazione FastAPI tipica consuma 100-200 MB di RAM. Con un limite di 1 GB, 4 worker sono il massimo consigliato. Superare questo limite causa un OOM kill silenzioso: il container viene terminato senza traceback Python.

### Health Check per Gunicorn

Gunicorn non ha un endpoint di health check integrato. L'health check deve essere implementato a livello applicativo:

```python
# app/health.py — health check che verifica anche i worker Gunicorn
import os
import psutil

@router.get("/health/workers")
async def worker_health():
    """Verifica lo stato dei worker Gunicorn."""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()

    return {
        "pid": os.getpid(),
        "memory_rss_mb": round(memory_info.rss / (1024 * 1024), 2),
        "memory_vms_mb": round(memory_info.vms / (1024 * 1024), 2),
        "cpu_percent": process.cpu_percent(interval=0.1),
        "threads": process.num_threads(),
        "open_files": len(process.open_files()),
    }
```

### Django in Docker — wsgi vs asgi

Per applicazioni Django, la scelta tra WSGI (Gunicorn) e ASGI (Gunicorn + UvicornWorker o Daphne) dipende dall'uso di funzionalita asincrone:

```dockerfile
# Django WSGI (sincrono tradizionale)
CMD ["gunicorn", "myproject.wsgi:application", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000"]

# Django ASGI (asincrono, per WebSocket, async views)
CMD ["gunicorn", "myproject.asgi:application", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000"]

# Django con Daphne (alternativa ASGI ufficiale Django)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "myproject.asgi:application"]
```

Per il collect dei file statici in Docker:

```dockerfile
# Colleziona i file statici durante il build, non a runtime
RUN python manage.py collectstatic --noinput
```

---

## CI/CD con Docker per Python

Questa sezione approfondisce l'integrazione di Docker nelle pipeline CI/CD per progetti Python, andando oltre l'esempio base di GitHub Actions mostrato nella sezione Registry e CI/CD.

### Pipeline Completa — Build, Test, Scan, Deploy

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline
on:
  push:
    branches: [main, develop]
    tags: ["v*"]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ============================================
  # Job 1: Lint e Type Check (senza Docker)
  # ============================================
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - uses: astral-sh/setup-uv@v5
      - run: uv sync --frozen --dev
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run mypy app/

  # ============================================
  # Job 2: Test in Docker
  # ============================================
  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4

      - name: Build test image
        run: docker build --target test -t myapp:test .

      - name: Run tests with services
        run: |
          docker compose -f docker-compose.test.yml up \
            --build \
            --abort-on-container-exit \
            --exit-code-from test

      - name: Extract coverage
        if: always()
        run: |
          docker compose -f docker-compose.test.yml \
            cp test:/app/reports/. ./reports/

      - name: Upload coverage
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-reports
          path: reports/

      - name: Cleanup
        if: always()
        run: docker compose -f docker-compose.test.yml down -v

  # ============================================
  # Job 3: Build e Push Immagine
  # ============================================
  build:
    runs-on: ubuntu-latest
    needs: test
    permissions:
      contents: read
      packages: write
      id-token: write  # Per OIDC signing

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GHCR
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix=

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          platforms: linux/amd64,linux/arm64
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          provenance: true
          sbom: true

  # ============================================
  # Job 4: Security Scan
  # ============================================
  security:
    runs-on: ubuntu-latest
    needs: build
    if: github.event_name != 'pull_request'
    steps:
      - uses: actions/checkout@v4

      - name: Trivy vulnerability scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:sha-${{ github.sha }}
          format: "sarif"
          output: "trivy-results.sarif"
          severity: "CRITICAL,HIGH"

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: "trivy-results.sarif"
```

### Matrix Build per Versioni Python Multiple

```yaml
jobs:
  test:
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
      fail-fast: false

    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build and test for Python ${{ matrix.python-version }}
        run: |
          docker build \
            --build-arg PYTHON_VERSION=${{ matrix.python-version }} \
            --target test \
            -t myapp:test-py${{ matrix.python-version }} .
          docker run --rm myapp:test-py${{ matrix.python-version }}
```

```dockerfile
# Dockerfile con ARG per la versione Python
ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim AS base
# ... resto del Dockerfile
```

### OIDC Authentication per Registry

GitHub Actions supporta l'autenticazione OIDC verso i principali cloud provider, eliminando la necessita di gestire credenziali long-lived:

```yaml
# Autenticazione OIDC verso AWS ECR
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789:role/github-actions
    aws-region: eu-west-1

- name: Login to Amazon ECR
  uses: aws-actions/amazon-ecr-login@v2
```

### Caching Avanzato in CI

```yaml
# Cache multipla: cache GHA per i layer Docker + cache uv separata
- name: Build with multiple cache sources
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: ${{ steps.meta.outputs.tags }}
    cache-from: |
      type=gha
      type=registry,ref=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:buildcache
    cache-to: type=gha,mode=max
```

---

## Strategie di Layer Caching per pip e uv

La cache dei layer Docker e il fattore singolo piu importante per la velocita dei build. Questa sezione approfondisce le strategie specifiche per le dipendenze Python.

### Anatomia della Cache dei Layer Docker

Ogni istruzione nel Dockerfile crea un layer. Docker invalida la cache di un layer e di tutti i layer successivi se:
- L'istruzione stessa cambia (testo diverso nel Dockerfile)
- Un file copiato con `COPY` o `ADD` cambia (checksum diverso)
- Un layer precedente e stato invalidato (invalidazione a cascata)

```dockerfile
# Layer 1: immagine base (cambia quasi mai)
FROM python:3.12-slim

# Layer 2: dipendenze di sistema (cambia raramente)
RUN apt-get update && apt-get install -y --no-install-recommends libpq5

# Layer 3: file di dipendenze (cambia occasionalmente)
COPY requirements.txt .

# Layer 4: installazione dipendenze (invalidato se Layer 3 cambia)
RUN pip install --no-cache-dir -r requirements.txt

# Layer 5: codice sorgente (cambia a ogni commit)
COPY . .
```

Se solo il codice sorgente cambia, i Layer 1-4 vengono riusati dalla cache. L'installazione delle dipendenze (la parte piu lenta) viene saltata completamente.

### BuildKit Cache Mount per pip

BuildKit permette di montare cache persistenti che sopravvivono tra build diverse:

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .

# La cache di pip viene persistita in /root/.cache/pip
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

COPY . .
```

Senza cache mount, `--no-cache-dir` e necessario per evitare che la cache di pip venga inclusa nel layer. Con cache mount, la cache viene usata ma non fa parte dell'immagine finale. E il meglio di entrambi i mondi.

### BuildKit Cache Mount per uv

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.7.9 /uv /usr/local/bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./

# Cache mount per uv: riduce rebuild da 45s a 2-3s
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev
```

### Cache da Registry

In ambienti CI dove la cache locale non persiste tra job (ogni run ha un runner pulito), la cache puo essere salvata in un registry remoto:

```bash
# Build con cache da registry
docker buildx build \
    --cache-from type=registry,ref=ghcr.io/user/myapp:buildcache \
    --cache-to type=registry,ref=ghcr.io/user/myapp:buildcache,mode=max \
    -t myapp:latest .
```

`mode=max` salva tutti i layer intermedi nella cache remota (non solo quelli dell'immagine finale), massimizzando il riuso della cache per build multi-stage.

### Pattern Kaniko per CI senza Docker Daemon

In ambienti CI che non hanno accesso al daemon Docker (alcuni cluster Kubernetes, runner senza Docker-in-Docker), Kaniko permette di costruire immagini container senza privilegi root:

```yaml
# GitLab CI con Kaniko
build:
  stage: build
  image:
    name: gcr.io/kaniko-project/executor:v1.23.0
    entrypoint: [""]
  script:
    - /kaniko/executor
      --context "${CI_PROJECT_DIR}"
      --dockerfile "${CI_PROJECT_DIR}/Dockerfile"
      --destination "${CI_REGISTRY_IMAGE}:${CI_COMMIT_SHA}"
      --cache=true
      --cache-repo="${CI_REGISTRY_IMAGE}/cache"
```

### Confronto Tempi di Build

| Scenario | Prima Build | Rebuild (solo codice) | Rebuild (+ nuova dipendenza) |
|---|---|---|---|
| pip senza cache | 120s | 120s | 120s |
| pip con layer cache | 120s | 5s | 120s |
| pip con cache mount | 120s | 5s | 15s |
| uv con layer cache | 15s | 3s | 15s |
| uv con cache mount | 15s | 3s | 5s |

I numeri sono indicativi per un progetto con ~50 dipendenze. Il vantaggio di uv e particolarmente evidente nelle prime build e nei rebuild con nuove dipendenze.

---

## Logging in Container

Il logging in ambiente containerizzato segue regole diverse rispetto alle applicazioni tradizionali. I container sono effimeri: quando un container viene distrutto, i file al suo interno scompaiono. Per questo, il logging basato su file non ha senso nei container.

### Principio Fondamentale: Scrivi su stdout/stderr

Docker cattura automaticamente tutto cio che un processo scrive su stdout e stderr, e lo rende disponibile tramite `docker logs`. Questo e il meccanismo standard per il logging nei container:

```python
# app/logging_config.py
import logging
import sys
import json
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    """Formatter che produce log in formato JSON strutturato."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        # Campi extra (es. request_id, user_id)
        for key in ("request_id", "user_id", "trace_id", "span_id"):
            value = getattr(record, key, None)
            if value is not None:
                log_entry[key] = value

        return json.dumps(log_entry, ensure_ascii=False)

def setup_logging(level: str = "INFO"):
    """Configura il logging per ambiente containerizzato."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.handlers = [handler]

    # Riduci il rumore dei logger di terze parti
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
```

### Perche JSON Strutturato

I log in formato JSON consentono:
- **Parsing automatico** da parte di sistemi di log aggregation (ELK, Loki, Datadog, CloudWatch)
- **Ricerca e filtro** per campo: `level:ERROR AND module:auth`
- **Correlazione** tramite `request_id` e `trace_id` tra servizi
- **Alerting** basato su pattern strutturati

Il formato testuale tradizionale (`2024-01-15 10:30:00 ERROR app.auth: Failed login for user admin`) e leggibile per un umano ma difficile da parsare in modo affidabile.

### Docker Logging Driver

Docker supporta diversi driver di logging. Il driver predefinito (`json-file`) scrive i log su disco come JSON:

```bash
# Configura il driver di logging per container
docker run --log-driver=json-file \
    --log-opt max-size=50m \
    --log-opt max-file=3 \
    myapp:latest
```

```yaml
# docker-compose.yml — logging globale
services:
  web:
    build: .
    logging:
      driver: json-file
      options:
        max-size: "50m"
        max-file: "3"
        tag: "{{.Name}}/{{.ID}}"
```

| Driver | Uso | Note |
|---|---|---|
| `json-file` | Default, log su disco | Configurare sempre max-size |
| `local` | Piu efficiente di json-file | Compressione automatica |
| `fluentd` | Forward a Fluentd/Fluentbit | Per stack EFK |
| `syslog` | Forward a syslog | Per infrastrutture legacy |
| `awslogs` | Forward a CloudWatch | Per AWS |
| `gcplogs` | Forward a Cloud Logging | Per GCP |

### Log Rotation

Senza log rotation, i log possono riempire il disco dell'host. Configurare sempre `max-size` e `max-file`:

```json
// /etc/docker/daemon.json — configurazione globale
{
  "log-driver": "local",
  "log-opts": {
    "max-size": "100m",
    "max-file": "5"
  }
}
```

### Correlazione Log tra Servizi

In un'architettura a microservizi, un singolo request dell'utente attraversa multipli container. Per correlare i log, ogni richiesta deve avere un `request_id` unico che viene propagato tra i servizi:

```python
# app/middleware.py
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import contextvars

request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request_id_var.set(request_id)

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

### Non Usare print() per i Log

`print()` scrive su stdout senza livello, timestamp o contesto. In produzione, usare sempre il modulo `logging` di Python che supporta livelli, formattazione e filtraggio. `PYTHONUNBUFFERED=1` nel Dockerfile garantisce che i log di Python arrivino immediatamente a Docker senza buffering.

### Integrazione con Stack di Osservabilita

I log strutturati JSON si integrano naturalmente con gli stack di osservabilita moderni:

**Promtail + Loki + Grafana:**

```yaml
# docker-compose.monitoring.yml
services:
  promtail:
    image: grafana/promtail:3.0.0
    volumes:
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - ./promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml

  loki:
    image: grafana/loki:3.0.0
    ports:
      - "3100:3100"

  grafana:
    image: grafana/grafana:11.0.0
    ports:
      - "3000:3000"
    environment:
      GF_AUTH_ANONYMOUS_ENABLED: "true"
```

**Fluentbit per il forwarding:**

```yaml
services:
  web:
    build: .
    logging:
      driver: fluentd
      options:
        fluentd-address: "localhost:24224"
        tag: "app.web"

  fluent-bit:
    image: fluent/fluent-bit:3.0
    ports:
      - "24224:24224"
    volumes:
      - ./fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf
```

La scelta tra stack dipende dall'infrastruttura esistente. Loki e preferibile per chi usa gia Grafana; ELK (Elasticsearch, Logstash, Kibana) offre capacita di ricerca full-text piu avanzate ma richiede piu risorse.

### Livelli di Log per Ambiente

```yaml
# docker-compose.override.yml (sviluppo)
services:
  web:
    environment:
      - LOG_LEVEL=debug      # Verbose per sviluppo
      - SQL_ECHO=true        # Log di tutte le query SQL

# docker-compose.prod.yml (produzione)
services:
  web:
    environment:
      - LOG_LEVEL=warning    # Solo warning e errori
      - SQL_ECHO=false       # Nessun log SQL
```

In produzione, i log a livello DEBUG e INFO generano un volume enorme che appesantisce lo storage e rallenta le query. Usare `WARNING` come livello base in produzione e abbassare a `INFO` o `DEBUG` solo temporaneamente durante il troubleshooting.

---

## Testing Avanzato — pytest e Testcontainers

La sezione precedente ha trattato l'esecuzione di pytest in Docker Compose. Questa sezione approfondisce l'uso di `testcontainers-python` per test di integrazione piu sofisticati e il pattern di test in container isolati.

### Testcontainers per Python

`testcontainers-python` e una libreria che gestisce automaticamente il ciclo di vita dei container Docker necessari per i test di integrazione. Invece di configurare un `docker-compose.test.yml` separato, i container vengono creati e distrutti programmaticamente all'interno dei test.

```bash
# Installazione
pip install testcontainers[postgres,redis]
# oppure con uv
uv add --dev "testcontainers[postgres,redis]"
```

### Fixture pytest con Testcontainers

```python
# tests/conftest.py
import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base

@pytest.fixture(scope="session")
def postgres_container():
    """Avvia un container PostgreSQL per l'intera sessione di test."""
    with PostgresContainer(
        image="postgres:16-alpine",
        username="test",
        password="test",
        dbname="testdb",
    ) as postgres:
        yield postgres

@pytest.fixture(scope="session")
def redis_container():
    """Avvia un container Redis per l'intera sessione di test."""
    with RedisContainer(image="redis:7-alpine") as redis:
        yield redis

@pytest.fixture(scope="session")
def db_engine(postgres_container):
    """Crea il motore SQLAlchemy connesso al PostgreSQL containerizzato."""
    engine = create_engine(postgres_container.get_connection_url())
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(db_engine):
    """Ogni test ha la propria transazione con rollback automatico."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="session")
def redis_url(redis_container):
    """Restituisce l'URL di connessione Redis."""
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    return f"redis://{host}:{port}/0"
```

### Test di Integrazione con Testcontainers

```python
# tests/integration/test_user_repository.py
import pytest
from app.repositories.user import UserRepository
from app.models.user import User

class TestUserRepository:
    """Test di integrazione per UserRepository con database reale."""

    def test_create_user(self, db_session):
        repo = UserRepository(db_session)
        user = repo.create(
            email="test@example.com",
            name="Test User",
        )
        assert user.id is not None
        assert user.email == "test@example.com"

    def test_find_by_email(self, db_session):
        repo = UserRepository(db_session)
        repo.create(email="find@example.com", name="Find Me")

        found = repo.find_by_email("find@example.com")
        assert found is not None
        assert found.name == "Find Me"

    def test_find_by_email_not_found(self, db_session):
        repo = UserRepository(db_session)
        found = repo.find_by_email("nonexistent@example.com")
        assert found is None
```

### Testcontainers con Container Personalizzati

Per servizi non coperti dai moduli standard di testcontainers:

```python
# tests/conftest.py
from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs

@pytest.fixture(scope="session")
def minio_container():
    """Avvia un container MinIO per i test di storage S3-compatibile."""
    with DockerContainer("minio/minio:latest") \
        .with_command("server /data") \
        .with_env("MINIO_ROOT_USER", "minioadmin") \
        .with_env("MINIO_ROOT_PASSWORD", "minioadmin") \
        .with_exposed_ports(9000) as minio:

        wait_for_logs(minio, "API:")
        yield minio
```

### Test Paralleli in Docker

pytest-xdist permette l'esecuzione parallela dei test. In combinazione con Docker, ogni worker puo avere il proprio database isolato:

```python
# tests/conftest.py
import os

@pytest.fixture(scope="session")
def postgres_container(worker_id):
    """Ogni worker pytest-xdist ha il proprio database."""
    # worker_id e "gw0", "gw1", "gw2", etc. (o "master" senza xdist)
    db_name = f"testdb_{worker_id}" if worker_id != "master" else "testdb"

    with PostgresContainer(
        image="postgres:16-alpine",
        dbname=db_name,
    ) as postgres:
        yield postgres
```

```bash
# Esecuzione parallela dei test
docker compose run --rm web pytest tests/ -n auto --dist loadscope
```

### Dockerfile Multi-target per Test

Un Dockerfile con target separati per produzione e test:

```dockerfile
FROM python:3.12-slim AS base
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.7.9 /uv /usr/local/bin/
COPY pyproject.toml uv.lock ./

# Stage: dipendenze di produzione
FROM base AS production-deps
RUN uv sync --frozen --no-dev --no-install-project

# Stage: dipendenze di test (include dev deps)
FROM base AS test-deps
RUN uv sync --frozen --no-install-project

# Stage: produzione
FROM python:3.12-slim AS production
COPY --from=production-deps /app/.venv /app/.venv
COPY . /app
ENV PATH="/app/.venv/bin:$PATH"
USER 1000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Stage: test
FROM python:3.12-slim AS test
COPY --from=test-deps /app/.venv /app/.venv
COPY . /app
ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app
CMD ["pytest", "tests/", "-v", "--tb=short", "--cov=app", "--cov-report=xml"]
```

```bash
# Build e run dei test
docker build --target test -t myapp:test .
docker run --rm myapp:test

# Build per produzione
docker build --target production -t myapp:prod .
```

### Coverage Report in CI da Container Docker

```yaml
# .github/workflows/test.yml
- name: Run tests and extract coverage
  run: |
    docker build --target test -t myapp:test .
    docker create --name test-runner myapp:test
    docker start -a test-runner || true
    docker cp test-runner:/app/coverage.xml ./coverage.xml
    docker rm test-runner

- name: Upload coverage
  uses: codecov/codecov-action@v4
  with:
    files: ./coverage.xml
    fail_ci_if_error: true
```

---

> **Nota conclusiva**: Docker non e solo uno strumento di deployment — e una filosofia di sviluppo che enfatizza la riproducibilita, l'isolamento e l'automazione. Per i progetti Python, Docker elimina le ambiguita dell'ambiente, standardizza il workflow del team e rende il percorso dal codice alla produzione prevedibile e affidabile. Inizia con un Dockerfile semplice, aggiungi docker-compose per lo sviluppo locale e costruisci gradualmente verso una pipeline CI/CD completa.

---

## Esercizi

1. **Dockerfile multi-stage per FastAPI** — Scrivi un Dockerfile multi-stage che: (a) utilizzi `python:3.12-slim` come base, (b) installi le dipendenze in uno stage di build separato, (c) copi solo i file necessari nello stage finale, (d) crei un utente non-root, (e) configuri un `HEALTHCHECK` che interroghi l'endpoint `/health`. Misura la dimensione dell'immagine finale rispetto a un Dockerfile single-stage equivalente.

2. **Docker Compose per stack completo** — Crea un `docker-compose.yml` che orchestra: un servizio web Python (FastAPI o Flask), PostgreSQL, Redis e un worker Celery. Configura: volumi per la persistenza dei dati, rete dedicata, variabili d'ambiente tramite `.env`, healthcheck per ogni servizio, e dipendenze corrette con `depends_on` e `condition: service_healthy`.

3. **Ottimizzazione cache dei layer** — Parti da un Dockerfile non ottimizzato (che copia tutto il codice prima di installare le dipendenze) e riordinalo per massimizzare la cache dei layer. Misura i tempi di rebuild con e senza modifica al codice sorgente, documentando il miglioramento ottenuto.

4. **Security hardening** — Prendi un Dockerfile esistente e applica tutte le best practice di sicurezza: utente non-root, `.dockerignore` completo, nessun segreto nell'immagine, image scanning con Trivy o Grype, pinning delle versioni base. Esegui `docker scout` o `trivy image` sull'immagine prima e dopo le modifiche e confronta i risultati.

5. **Pipeline CI/CD con build Docker** — Configura una GitHub Action che: (a) esegua i test Python in un container, (b) costruisca l'immagine Docker con caching GHA, (c) esegua uno scan di sicurezza sull'immagine, (d) pubblichi l'immagine su GHCR con tag basati su semantic versioning e git SHA, (e) supporti build multi-architettura (amd64 + arm64).

---

## Letture e Riferimenti

### Fonti primarie

- Docker Documentation — *Dockerfile reference* — https://docs.docker.com/reference/dockerfile/ (consultato: 2026-05-24)
- Docker Documentation — *Docker Compose* — https://docs.docker.com/compose/ (consultato: 2026-05-24)
- Docker Documentation — *Multi-stage builds* — https://docs.docker.com/build/building/multi-stage/ (consultato: 2026-05-24)
- Docker Documentation — *Build cache* — https://docs.docker.com/build/cache/ (consultato: 2026-05-24)
- Docker Documentation — *Security best practices* — https://docs.docker.com/build/building/best-practices/ (consultato: 2026-05-24)
- Docker Documentation — *Docker Scout* — https://docs.docker.com/scout/ (consultato: 2026-05-24)
- Python Docker Official Images — https://hub.docker.com/_/python (consultato: 2026-05-24)
- Aqua Security — *Trivy* — https://aquasecurity.github.io/trivy/ (consultato: 2026-05-24)
- Hadolint — *Dockerfile linter* — https://github.com/hadolint/hadolint (consultato: 2026-05-24)

### Libri consigliati

- *Docker Deep Dive* — Nigel Poulton — Independently Published, 2024
- *Docker in Action* — Jeff Nickoloff, Stephen Kuenzli — Manning, 2019

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [27 — CI/CD per Python](27-ci-cd-per-python.md) | Pipeline CI/CD che costruiscono e pubblicano immagini Docker |
| [25 — Performance](25-performance.md) | Profiling e ottimizzazione di applicazioni Python containerizzate |
| [05 — Gestione File e I/O](05-gestione-file-io.md) | Volumi Docker e persistenza dei dati applicativi |
| [10 — Virtual Environments](10-virtual-environments.md) | Ambienti virtuali vs isolamento container |
| [09 — Pip e Gestione Pacchetti](09-pip-gestione-pacchetti.md) | Installazione dipendenze nel Dockerfile |
| [23 — Testing](23-testing.md) | Esecuzione test in container Docker |

---

## Glossario

| Termine | Definizione |
|---|---|
| **Container** | Istanza in esecuzione di un'immagine Docker, isolata dal sistema host tramite namespace e cgroup del kernel Linux |
| **Immagine** | Template immutabile e stratificato che contiene il filesystem, le dipendenze e la configurazione necessari per creare un container |
| **Dockerfile** | File di testo con le istruzioni per costruire un'immagine Docker, processato sequenzialmente dal Docker engine |
| **Layer** | Singolo strato del filesystem dell'immagine, generato da ciascuna istruzione del Dockerfile; i layer sono cached e condivisi tra immagini |
| **Multi-stage build** | Tecnica che utilizza piu stage `FROM` in un Dockerfile per separare build e runtime, riducendo la dimensione dell'immagine finale |
| **Docker Compose** | Strumento per definire e gestire applicazioni multi-container tramite un file YAML dichiarativo |
| **Volume** | Meccanismo di persistenza dei dati che sopravvive al ciclo di vita del container |
| **Bind mount** | Collegamento diretto tra una directory dell'host e un percorso nel container |
| **Registry** | Servizio di archiviazione e distribuzione di immagini Docker (Docker Hub, GHCR, ECR) |
| **Healthcheck** | Comando periodico eseguito all'interno del container per verificare che l'applicazione sia funzionante |
| **GHCR** | GitHub Container Registry — registry di immagini container integrato in GitHub |
| **Buildx** | Plugin Docker CLI per build avanzati con supporto multi-piattaforma e caching remoto |
| **Trivy** | Scanner open-source per vulnerabilita in immagini container, filesystem e repository |
| **`.dockerignore`** | File che specifica i pattern da escludere dal contesto di build Docker |
| **Distroless** | Immagini container minimali di Google che contengono solo l'applicazione e le sue dipendenze runtime, senza shell o package manager |
