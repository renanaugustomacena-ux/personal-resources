# Tutorial Linux 26 — Docker Guida Operativa

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** Docker produzione, multi-stage, compose avanzato, registry, swarm basics
> **Prerequisiti:** `tutorial_linux_14_containerizzazione.md`
> **Durata stimata:** 14-18 ore

---

## Mappa concettuale

```
Docker Operativo
│
├── Immagini
│   ├── Dockerfile ottimizzato
│   ├── BuildKit + cache mounts
│   ├── Multi-platform (buildx)
│   └── Private registry (Harbor, ECR)
│
├── Container
│   ├── Risorse e limiti
│   ├── Health checks
│   ├── Restart policy
│   └── Logging driver
│
├── Docker Compose produzione
│   ├── Profiles
│   ├── Secrets
│   └── configs
│
├── Networking
│   ├── Custom bridge
│   ├── Host networking
│   └── Macvlan
│
└── Docker Swarm
    ├── Init + join
    ├── Service update --rollback
    └── Secrets management
```

---

# Parte A — Dockerfile avanzato

---

## A1. BuildKit e cache ottimizzata

```dockerfile
# syntax=docker/dockerfile:1.7
# Abilita BuildKit features

FROM python:3.12-slim AS base

# Variabili build
ARG APP_VERSION=dev
ARG BUILD_DATE
ARG GIT_COMMIT

# Labels OCI
LABEL org.opencontainers.image.title="Mia App"
LABEL org.opencontainers.image.version="${APP_VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${GIT_COMMIT}"

# Layer base: raramente cambia → in alto per cache
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Stage builder: installa dipendenze Python
FROM base AS builder

# Cache pip downloads tra build (veloce!)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install uv

WORKDIR /build
COPY pyproject.toml uv.lock ./

# Cache delle dipendenze uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --frozen

# Stage finale: solo il necessario
FROM base AS runtime

# Non usare root
RUN groupadd --gid 1001 app && \
    useradd --uid 1001 --gid app --no-create-home --shell /sbin/nologin app

WORKDIR /app

# Copia venv dal builder
COPY --from=builder --chown=app:app /build/.venv /app/.venv

# Copia solo i file applicazione (cambia spesso → in fondo)
COPY --chown=app:app src/ ./src/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD /app/.venv/bin/python -c \
    "import httpx; httpx.get('http://localhost:8000/health', timeout=5).raise_for_status()"

EXPOSE 8000
USER app

ENTRYPOINT ["/app/.venv/bin/uvicorn"]
CMD ["src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build con BuildKit (default da Docker 23+)
docker buildx build \
    --build-arg APP_VERSION=1.2.3 \
    --build-arg BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ) \
    --build-arg GIT_COMMIT=$(git rev-parse --short HEAD) \
    --tag mia-app:1.2.3 \
    --tag mia-app:latest \
    .

# Build multi-platform
docker buildx create --use --name builder
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --tag ghcr.io/org/mia-app:1.2.3 \
    --push \
    .
```

---

# Parte B — Docker Compose produzione

---

## B1. Compose con secrets e profiles

```yaml
# docker-compose.yml
name: mia-app

services:
  app:
    build:
      context: .
      target: runtime
      args:
        APP_VERSION: "${APP_VERSION:-dev}"
    image: "mia-app:${APP_VERSION:-dev}"
    restart: unless-stopped
    
    # Secrets (da Docker Swarm o file)
    secrets:
      - db_password
      - jwt_secret
    
    # Config files (read-only, montati automaticamente)
    configs:
      - source: nginx_config
        target: /etc/nginx/conf.d/app.conf
    
    # Environment (non segreti)
    environment:
      APP_ENV: production
      DB_HOST: db
      DB_PORT: 5432
      DB_NAME: appdb
      DB_USER: appuser
      # Password da secret file (Swarm) o env (Compose)
      DB_PASSWORD_FILE: /run/secrets/db_password
    
    # Dipendenze
    depends_on:
      db:
        condition: service_healthy
    
    # Risorse
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 512M
        reservations:
          memory: 128M
      # Politica restart per Swarm
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    
    # Networking
    networks:
      - frontend
      - backend
    ports:
      - "8000:8000"
    
    # Sicurezza
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp

  db:
    image: postgres:16-alpine
    restart: unless-stopped
    secrets:
      - db_password
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser -d appdb"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend

  # Profilo: solo in sviluppo
  pgadmin:
    image: dpage/pgadmin4
    profiles: [dev]
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@test.it
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
    networks:
      - backend

networks:
  frontend:
  backend:
    internal: true

volumes:
  postgres-data:

secrets:
  db_password:
    file: ./secrets/db_password.txt   # in sviluppo
    # In Swarm: external: true

configs:
  nginx_config:
    file: ./config/nginx.conf
```

```bash
# Avvia solo servizi base
docker compose up -d

# Avvia con profilo sviluppo (include pgadmin)
docker compose --profile dev up -d

# Aggiorna solo l'app
docker compose up -d --no-deps app

# Deploy con zero-downtime (Swarm)
docker service update --image mia-app:1.3.0 mia-app_app

# Rollback automatico
docker service update --rollback mia-app_app
```

---

# Parte C — Registry privato

---

## C1. Harbor o registry semplice

```bash
# Registry semplice (sviluppo/test)
docker run -d \
    --name registry \
    --restart=unless-stopped \
    -v registry-data:/var/lib/registry \
    -p 5000:5000 \
    registry:2

# Testa push
docker tag mia-app:latest localhost:5000/mia-app:latest
docker push localhost:5000/mia-app:latest
docker pull localhost:5000/mia-app:latest

# Con autenticazione (via nginx htpasswd)
apt install apache2-utils
htpasswd -Bc /etc/registry/auth/htpasswd mario

cat > /etc/nginx/sites-enabled/registry << 'EOF'
server {
    listen 443 ssl;
    server_name registry.esempio.it;
    # ssl certs...

    location / {
        auth_basic "Docker Registry";
        auth_basic_user_file /etc/registry/auth/htpasswd;
        
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_read_timeout 900;
        client_max_body_size 4G;
    }
}
EOF

# Login al registry privato
docker login registry.esempio.it
```

---

# Parte D — Manutenzione Docker

---

## D1. Pulizia e diagnostica

```bash
# Pulizia generale
docker system prune          # rimuovi container/immagini/network non usati
docker system prune -a       # include immagini non usate di recente
docker system prune --volumes # include anche volumes (PERICOLOSO!)

# Pulizia specifica
docker image prune           # solo immagini dangling
docker container prune       # solo container fermi
docker volume prune          # solo volumi non usati
docker network prune         # solo reti non usate

# Uso disco
docker system df             # overview uso disco
docker system df -v          # dettagliato

# Debug container
docker exec -it container-name bash      # shell interattiva
docker exec container-name cat /etc/env  # comando singolo

docker logs container-name --tail 100 -f  # ultimi 100 log + follow
docker logs --since 1h container-name     # ultimo ora

docker inspect container-name            # configurazione completa JSON
docker inspect container-name | jq '.[0].NetworkSettings.Networks'

# Stats in tempo reale
docker stats                  # tutti i container
docker stats container-name   # specifico

# Copia file da/per container
docker cp container:/etc/nginx/nginx.conf ./nginx.conf
docker cp ./config.yml container:/etc/app/config.yml

# Top processi dentro container
docker top container-name

# Diff dal filesystem di partenza
docker diff container-name
# A = Added, C = Changed, D = Deleted
```

---

# Parte E — Riepilogo

## Best practice produzione

```bash
# 1. Sempre PIN versione immagini
image: postgres:16.2   # non :latest!

# 2. Non usare root
USER 1001

# 3. Read-only filesystem dove possibile
security_opt:
  - no-new-privileges:true
read_only: true

# 4. Limiti risorse sempre presenti
deploy:
  resources:
    limits:
      memory: 512M

# 5. Health check obbligatorio
HEALTHCHECK --interval=30s CMD ...

# 6. Segreti via secrets, non env
secrets:
  - db_password

# 7. Scan vulnerabilità prima del deploy
docker scout cves mia-app:latest
trivy image mia-app:latest
```

## Comandi operativi quotidiani

| Operazione | Comando |
|---|---|
| Vedi log | `docker logs -f --tail 100 nome` |
| Shell dentro container | `docker exec -it nome bash` |
| Stats risorse | `docker stats` |
| Riavvia servizio | `docker compose restart app` |
| Aggiorna immagine | `docker compose pull && docker compose up -d` |
| Spazio disco | `docker system df` |
| Pulisci tutto | `docker system prune -a` |

## Prossimi passi

- `tutorial_linux_27_selinux_apparmor.md` — sicurezza container avanzata
- `tutorial_linux_14_containerizzazione.md` — namespace e cgroups
