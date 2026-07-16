# Tutorial Linux 14 — Containerizzazione: cgroups, namespaces, Docker, Podman

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** primitive kernel, Docker avanzato, Podman rootless, networking container
> **Prerequisiti:** `tutorial_linux_07_kernel.md`, `tutorial_linux_11_sicurezza.md`
> **Durata stimata:** 14-18 ore

---

## Mappa concettuale

```
Containerizzazione Linux
│
├── Primitive kernel
│   ├── Namespaces — isolamento risorse
│   │   ├── pid, net, mnt, uts, ipc, user
│   │   └── cgroup
│   └── cgroups v2 — limiti risorse
│       ├── CPU, Memory, I/O
│       └── /sys/fs/cgroup/
│
├── Docker
│   ├── Dockerfile multi-stage
│   ├── Docker Compose avanzato
│   ├── Networking (bridge, host, overlay)
│   └── Storage (volumes, bind, tmpfs)
│
├── Podman — rootless
│   ├── Compatibile Docker CLI
│   ├── No daemon
│   └── Systemd integration
│
└── Container security
    ├── Non-root user
    ├── Read-only filesystem
    ├── Seccomp profiles
    └── Capabilities
```

---

# Parte A — Primitive kernel

---

## A1. Namespaces

```bash
# Namespaces: isolano cosa un processo può vedere
# PID namespace:  processi vedono solo il loro namespace
# Net namespace:  interfacce di rete separate
# Mnt namespace:  filesystem mount points separati
# UTS namespace:  hostname/domainname separati
# IPC namespace:  code IPC e shared memory separate
# User namespace: UID/GID remappati (rootless containers)
# Cgroup namespace: cgroup hierarchy isolata

# Crea processo con nuovo namespace
unshare --pid --fork --mount-proc bash
# Ora hai un PID namespace separato
ps aux   # vedi solo il tuo bash e ps

# Ispeziona namespace di un processo
ls -la /proc/self/ns/
ls -la /proc/1234/ns/

# Entra nel namespace di un container
docker inspect --format '{{.State.Pid}}' container-name
nsenter -t 12345 --net ip addr    # vedi rete del container

# Crea network namespace manuale
ip netns add test-ns
ip netns exec test-ns ip link show   # lista interfacce in questo namespace
ip netns exec test-ns bash           # shell nel namespace
ip netns del test-ns
```

---

## A2. cgroups v2

```bash
# Controlla versione cgroup
mount | grep cgroup
# cgroup2 on /sys/fs/cgroup type cgroup2

# Gerarchia cgroup
ls /sys/fs/cgroup/
# cpu.max  memory.max  io.max  pids.max  ...

# Esempio: limita memoria a 512MB per un processo
# 1. Crea cgroup
mkdir /sys/fs/cgroup/test-app

# 2. Imposta limiti
echo "512M" > /sys/fs/cgroup/test-app/memory.max
echo "256M" > /sys/fs/cgroup/test-app/memory.high    # soft limit (throttle)
echo "200000 1000000" > /sys/fs/cgroup/test-app/cpu.max   # 20% CPU

# 3. Aggiungi processo al cgroup
echo $$ > /sys/fs/cgroup/test-app/cgroup.procs

# 4. Verifica
cat /proc/$$/cgroup

# systemd slice — modo raccomandato per produzione
systemd-run --scope --unit=test-app.scope \
    --property=MemoryMax=512M \
    --property=CPUQuota=20% \
    python3 mia_app.py

# Limiti RAM per servizio systemd
# In mia-app.service:
# [Service]
# MemoryMax=512M
# MemoryHigh=400M
# CPUQuota=200%   # 2 CPU cores
```

> **Analogia:** I namespace sono come gli appartamenti di un condominio — ogni famiglia (container) vede solo il proprio appartamento, non quelli degli altri. I cgroups sono invece il contatore della luce e dell'acqua: limitano quante risorse condominiali può consumare ogni famiglia. Il container runtime (Docker, Podman) è l'amministratore del condominio che combina le due tecnologie.

---

# Parte B — Docker avanzato

---

## B1. Dockerfile best practice

```dockerfile
# Multi-stage build — immagine finale minimale
FROM python:3.12-slim AS builder

# Non installare pacchetti di sistema inutili
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Installa dipendenze separatamente per cache layer
WORKDIR /build
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --no-dev --frozen

# Stage runtime: partenza da immagine più piccola
FROM python:3.12-slim AS runtime

# Non usare root
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --no-create-home --shell /usr/sbin/nologin appuser

WORKDIR /app

# Copia solo il necessario
COPY --from=builder /build/.venv /app/.venv
COPY --chown=appuser:appgroup src/ ./src/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

# Non esporre porte privilegiate (usa >1024)
EXPOSE 8000

USER appuser

# CMD vs ENTRYPOINT
# ENTRYPOINT = il processo principale (non sovrascrivibile facilmente)
# CMD = argomenti default (sovrascrivibili con docker run ... <args>)
ENTRYPOINT ["/app/.venv/bin/python", "-m", "uvicorn"]
CMD ["src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build e tag
docker build -t mia-app:1.0.0 .
docker build -t mia-app:latest -t mia-app:1.0.0 .

# Build con buildkit (più veloce, cache avanzata)
DOCKER_BUILDKIT=1 docker build .

# Ispeziona layers
docker history mia-app:latest
docker image inspect mia-app:latest

# Scan vulnerabilità
docker scout cves mia-app:latest    # docker scout (built-in)
# oppure:
trivy image mia-app:latest          # trivy (open source)
```

---

## B2. Docker networking avanzato

```bash
# Tipi di network
# bridge (default): container isolati tra loro, NAT verso host
# host: condivide stack rete dell'host (no isolamento, max performance)
# none: nessuna rete
# overlay: multi-host (Swarm)
# macvlan: container con IP proprio sulla rete LAN

# Crea network custom
docker network create \
    --driver bridge \
    --subnet 172.20.0.0/16 \
    --ip-range 172.20.100.0/24 \
    --gateway 172.20.0.1 \
    app-network

# Container in network custom possono comunicare per nome
docker run -d --name db --network app-network postgres:16
docker run -d --name app --network app-network -e DB_HOST=db mia-app

# Collega container a più reti
docker network connect frontend-network app
docker network disconnect backend-network app

# DNS interno Docker
# I container si trovano per nome nell'ambito della stessa rete custom
docker exec app ping db    # funziona se stessa network

# Host networking (performance massima, no isolamento)
docker run --network host nginx
```

---

## B3. Docker Compose avanzato

```yaml
# docker-compose.yml
name: produzione

services:
  app:
    build:
      context: .
      target: runtime     # multi-stage target
    image: mia-app:latest
    restart: unless-stopped
    
    # Risorse
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 128M
    
    # Ambiente
    environment:
      APP_ENV: production
      DB_URL: postgresql+asyncpg://app:${DB_PASSWORD}@db/appdb
    env_file:
      - .env.production
    
    # Dipendenze con health check
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    
    # Networking
    networks:
      - frontend
      - backend
    ports:
      - "8000:8000"
    
    # Volumes
    volumes:
      - app-uploads:/app/uploads
      - /var/log/mia-app:/app/logs
    
    # Sicurezza
    user: "1001:1001"
    read_only: true
    tmpfs:
      - /tmp:size=100M
    security_opt:
      - no-new-privileges:true

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: appdb
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d appdb"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 256mb
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
    networks:
      - backend

networks:
  frontend:
  backend:
    internal: true    # nessun accesso internet per questa rete

volumes:
  postgres-data:
  redis-data:
  app-uploads:
```

---

# Parte C — Podman (rootless)

---

## C1. Podman: container senza root

```bash
# Installazione
apt install podman

# Compatibile Docker CLI
alias docker=podman

# Differenze chiave:
# - No daemon (ogni container è figlio diretto della shell)
# - Rootless by default
# - Usa newuidmap/newgidmap per UID mapping

# UID mapping per rootless
cat /etc/subuid
# mario:100000:65536
# mario può usare UID 100000-165535 all'interno dei container

cat /etc/subgid
# mario:100000:65536

# Run come utente normale
podman run -d --name mia-app -p 8000:8000 mia-app:latest
podman ps
podman logs mia-app

# Systemd integration (unit per container)
podman generate systemd --name mia-app --files --new
# Genera: container-mia-app.service
mv container-mia-app.service ~/.config/systemd/user/
systemctl --user enable --now container-mia-app

# Podman Compose (compatibile docker-compose)
pip3 install podman-compose
podman-compose up -d

# Quadlet — systemd unit nativa (podman 4.4+)
cat > ~/.config/containers/systemd/mia-app.container << 'EOF'
[Unit]
Description=Mia App Container
After=network-online.target

[Container]
Image=docker.io/mia-org/mia-app:latest
PublishPort=8000:8000
Environment=APP_ENV=production
Volume=/var/data/mia-app:/app/data:Z
User=appuser

[Service]
Restart=always

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user start mia-app
```

---

# Parte E — Riepilogo

## Docker vs Podman

| Aspetto | Docker | Podman |
|---|---|---|
| Daemon | Sì (dockerd) | No |
| Root richiesto | Sì (di default) | No (rootless default) |
| Compatibilità | Riferimento | Drop-in replacement |
| Systemd | Manual | Nativa (Quadlet) |
| OCI compliant | Sì | Sì |

## Sicurezza container checklist

```bash
# 1. Mai root nel container
USER 1001

# 2. Filesystem read-only
docker run --read-only --tmpfs /tmp mia-app

# 3. No new privileges
docker run --security-opt=no-new-privileges mia-app

# 4. Limita capabilities
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE mia-app

# 5. Scan immagini per vulnerabilità
trivy image mia-app:latest

# 6. Non usare :latest in produzione
docker run mia-app:1.2.3   # pin alla versione
```

## Prossimi passi

- `tutorial_linux_15_virtualizzazione.md` — KVM/QEMU, libvirt
- `tutorial_linux_26_docker.md` — Docker guida operativa completa
