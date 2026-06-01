# Docker: Guida Operativa Approfondita — Guida Approfondita

> **Modulo 26** · **Versione:** Docker 27+ · **Aggiornamento:** 2026-05-22

## Idee guida
1. **Rootless docker: `docker context use rootless`.**
2. **BuildKit + cache `--mount=type=cache`.**
3. **Multi-arch buildx: amd64 + arm64.**
4. **Compose V2 (CLI plugin) > V1 (legacy).**


## Indice

- [Panoramica](#panoramica)
- [Architettura Docker](#architettura-docker)
- [Ciclo di Vita di un Container](#ciclo-di-vita-di-un-container)
- [Dockerfile: Multi-Stage Build e Ottimizzazione Layer](#dockerfile-multi-stage-build-e-ottimizzazione-layer)
- [.dockerignore: Ottimizzazione Build Context](#dockerignore-ottimizzazione-build-context)
- [BuildKit Avanzato](#buildkit-avanzato)
- [Docker Compose v2](#docker-compose-v2)
- [Docker Networking](#docker-networking)
- [Docker Volumes e Storage](#docker-volumes-e-storage)
- [Security](#security)
- [Logging e Log Driver](#logging-e-log-driver)
- [Resource Limits e Cgroups](#resource-limits-e-cgroups)
- [Buildx: Multi-Platform e Cache](#buildx-multi-platform-e-cache)
- [Registry e Image Management](#registry-e-image-management)
- [Troubleshooting Avanzato](#troubleshooting-avanzato)
- [Overlay2 Storage Driver: Internals e Tuning](#overlay2-storage-driver-internals-e-tuning)
- [Docker in Produzione: Pattern Operativi](#docker-in-produzione-pattern-operativi)
- [Ottimizzazione Immagini: Distroless, Slim e Scratch](#ottimizzazione-immagini-distroless-slim-e-scratch)
- [Docker Content Trust e Firma delle Immagini](#docker-content-trust-e-firma-delle-immagini)
- [Docker Bench for Security e CIS Benchmark](#docker-bench-for-security-e-cis-benchmark)
- [Gestione dei Secrets in Produzione](#gestione-dei-secrets-in-produzione)
- [Docker Swarm vs Alternative di Orchestrazione](#docker-swarm-vs-alternative-di-orchestrazione)
- [Standard OCI (Open Container Initiative)](#standard-oci-open-container-initiative)
- [Esercizi Pratici](#esercizi-pratici)
- [Domande e Risposte (Q&A)](#domande-e-risposte-qa)
- [Best Practices](#best-practices)
- [Riferimenti](#riferimenti)

---

## Panoramica

Docker è la piattaforma di containerizzazione più diffusa che permette di impacchettare applicazioni con tutte le loro dipendenze in unità isolate e portabili chiamate container. A differenza della virtualizzazione tradizionale, i container condividono il kernel del sistema host e utilizzano namespace e cgroup del kernel Linux per l'isolamento, risultando in un overhead minimo rispetto all'esecuzione nativa.

Questo documento si concentra sugli aspetti avanzati di Docker che ogni Linux poweruser deve padroneggiare: la costruzione di immagini ottimizzate tramite multi-stage build, l'orchestrazione di stack applicativi complessi con Docker Compose v2, il networking avanzato (bridge, host, overlay, macvlan), la sicurezza dei container (rootless mode, seccomp, AppArmor, user namespaces) e il troubleshooting sistematico.

La padronanza di Docker non si limita al `docker run`: richiede una comprensione profonda di come i layer funzionano, come il networking è implementato a livello kernel (veth pairs, bridge, iptables), come il filesystem overlay funziona, e quali sono i confini reali dell'isolamento che i container offrono. Solo con questa comprensione si possono costruire ambienti containerizzati sicuri, performanti e manutenibili.

### Differenza tra Container e VM

```
VM Tradizionale:                          Container:
┌──────────┐  ┌──────────┐               ┌──────┐ ┌──────┐ ┌──────┐
│  App A   │  │  App B   │               │App A │ │App B │ │App C │
├──────────┤  ├──────────┤               ├──────┤ ├──────┤ ├──────┤
│  Bins/   │  │  Bins/   │               │Bins/ │ │Bins/ │ │Bins/ │
│  Libs    │  │  Libs    │               │Libs  │ │Libs  │ │Libs  │
├──────────┤  ├──────────┤               └──┬───┘ └──┬───┘ └──┬───┘
│  Guest   │  │  Guest   │                  │        │        │
│  OS      │  │  OS      │               ┌──▼────────▼────────▼───┐
├──────────┤  ├──────────┤               │   Container Runtime    │
│  Virtual │  │  Virtual │               │   (containerd + runc)  │
│  HW      │  │  HW      │               ├────────────────────────┤
└────┬─────┘  └────┬─────┘               │   Host OS Kernel       │
     │             │                      ├────────────────────────┤
┌────▼─────────────▼─────┐               │   Hardware             │
│     Hypervisor         │               └────────────────────────┘
├────────────────────────┤
│     Host OS            │               Overhead: ~1-5% CPU
├────────────────────────┤               Startup: millisecondi
│     Hardware           │               Dimensione: MB
└────────────────────────┘
Overhead: 10-20% CPU
Startup: secondi/minuti
Dimensione: GB
```

---

## Architettura Docker

### Stack Completo: dal CLI al Kernel

```
┌────────────────────────────────────────────────────────────┐
│                    Docker Client (CLI)                      │
│         docker build, run, compose, buildx                 │
└───────────────────────┬────────────────────────────────────┘
                        │ REST API (Unix socket /var/run/docker.sock
                        │          oppure TCP :2376 con TLS)
┌───────────────────────▼────────────────────────────────────┐
│                    Docker Daemon (dockerd)                  │
│   Responsabilità:                                          │
│   - Gestione immagini (pull, build, tag, push)             │
│   - Gestione container (create, start, stop, rm)           │
│   - Gestione reti (bridge, overlay, macvlan)               │
│   - Gestione volumi (create, mount, backup)                │
│   - Build cache e BuildKit integration                     │
│   - Logging, eventi, metriche                              │
│                                                             │
│   ┌──────────┐ ┌──────────┐ ┌────────────────┐            │
│   │ Images   │ │Containers│ │   Networks      │            │
│   └──────────┘ └──────────┘ └────────────────┘            │
│   ┌──────────┐ ┌──────────┐ ┌────────────────┐            │
│   │ Volumes  │ │ Plugins  │ │   Build Cache   │            │
│   └──────────┘ └──────────┘ └────────────────┘            │
└───────────────────────┬────────────────────────────────────┘
                        │ gRPC API
┌───────────────────────▼────────────────────────────────────┐
│                    containerd                               │
│   Responsabilità:                                          │
│   - Lifecycle dei container (create → start → stop → rm)   │
│   - Pull/push immagini dal registry                        │
│   - Gestione snapshot (layer filesystem)                   │
│   - Gestione dei task (processi nel container)             │
│   - Content store e metadata store                         │
│                                                             │
│   Per ogni container crea un "shim":                       │
│   ┌──────────────────────────────────────────────┐        │
│   │ containerd-shim-runc-v2                       │        │
│   │ - Processo intermedio tra containerd e runc    │        │
│   │ - Resta in vita dopo che runc esce             │        │
│   │ - Gestisce stdin/stdout/stderr del container   │        │
│   │ - Riporta exit code a containerd               │        │
│   │ - Permette a containerd di restartare senza    │        │
│   │   uccidere i container in esecuzione           │        │
│   └──────────────────┬───────────────────────────┘        │
└──────────────────────┼─────────────────────────────────────┘
                       │ exec(2)
┌──────────────────────▼─────────────────────────────────────┐
│                    runc (OCI Runtime)                       │
│   Responsabilità:                                          │
│   - Creazione effettiva del container nel kernel:          │
│     · Namespace: pid, net, mnt, uts, ipc, user, cgroup     │
│     · Cgroups: limiti CPU, memoria, I/O, PID               │
│     · pivot_root: cambia root filesystem                    │
│     · Seccomp: filtro syscall                               │
│     · Capabilities: drop/add Linux capabilities            │
│     · Appareled/SELinux: profili MAC                        │
│   - runc ESCE dopo aver creato il container                │
│   - Il PID 1 del container è il processo applicativo       │
└────────────────────────────────────────────────────────────┘
```

### Flusso di `docker run` Dettagliato

```bash
# Quando esegui:
docker run -d --name web -p 8080:80 nginx:alpine

# Succede questo (in ordine):
# 1. Docker CLI invia POST /containers/create all'API del daemon
# 2. dockerd verifica se l'immagine nginx:alpine è locale
#    → se no, docker pull nginx:alpine (via containerd)
# 3. dockerd crea la configurazione del container (OCI spec)
# 4. dockerd chiama containerd via gRPC: CreateContainer()
# 5. containerd crea un nuovo snapshot dal layer finale dell'immagine
# 6. containerd avvia containerd-shim-runc-v2
# 7. lo shim esegue runc con la OCI spec
# 8. runc:
#    a. Crea i namespace (clone/unshare)
#    b. Configura cgroups
#    c. Monta il filesystem (overlay + volumi)
#    d. Imposta la rete (veth pair nel network namespace)
#    e. Applica seccomp profile
#    f. Drop capabilities non necessarie
#    g. pivot_root nel filesystem del container
#    h. exec() del processo PID 1 (nginx)
# 9. runc esce — lo shim resta a gestire il container
# 10. dockerd configura le regole iptables per il port mapping 8080:80
```

### Namespace e Cgroup — Dettaglio

I container Linux si basano su due meccanismi del kernel:

**Namespaces** — isolamento della visibilità:

| Namespace | Flag clone | Isola | Verifica |
|-----------|-----------|-------|----------|
| `pid` | `CLONE_NEWPID` | Albero dei processi | `ls /proc` nel container mostra solo i suoi processi |
| `net` | `CLONE_NEWNET` | Stack di rete | `ip addr` mostra interfacce diverse dall'host |
| `mnt` | `CLONE_NEWNS` | Mount point | `/proc/mounts` mostra solo i mount del container |
| `uts` | `CLONE_NEWUTS` | Hostname e domainname | `hostname` restituisce il nome del container |
| `ipc` | `CLONE_NEWIPC` | Shared memory, semafori | SysV IPC isolata tra container |
| `user` | `CLONE_NEWUSER` | UID/GID mapping | root nel container ≠ root sull'host |
| `cgroup` | `CLONE_NEWCGROUP` | Vista cgroup | `/proc/1/cgroup` mostra solo i cgroup del container |

```bash
# Ispeziona i namespace di un container dall'host
PID=$(docker inspect -f '{{.State.Pid}}' web)
ls -la /proc/$PID/ns/
# lrwxrwxrwx 1 root root 0 ... cgroup -> cgroup:[4026532577]
# lrwxrwxrwx 1 root root 0 ... ipc -> ipc:[4026532575]
# lrwxrwxrwx 1 root root 0 ... mnt -> mnt:[4026532573]
# lrwxrwxrwx 1 root root 0 ... net -> net:[4026532578]
# lrwxrwxrwx 1 root root 0 ... pid -> pid:[4026532576]
# lrwxrwxrwx 1 root root 0 ... user -> user:[4026531837]
# lrwxrwxrwx 1 root root 0 ... uts -> uts:[4026532574]
```

**Cgroups** — limitazione delle risorse:

```bash
# cgroup v2 (default su kernel 5.x+, usato da Docker)
# Struttura in /sys/fs/cgroup/system.slice/docker-<container_id>.scope/

# CPU
cat /sys/fs/cgroup/system.slice/docker-<id>.scope/cpu.max
# 200000 100000  → 200% CPU (2 cores)

# Memoria
cat /sys/fs/cgroup/system.slice/docker-<id>.scope/memory.max
# 536870912  → 512 MB

# I/O
cat /sys/fs/cgroup/system.slice/docker-<id>.scope/io.max
# 8:0 rbps=1048576 wbps=1048576  → 1MB/s read/write
```

### Overlay Filesystem

Docker usa OverlayFS per costruire il filesystem del container come stack di layer read-only con un thin writable layer in cima:

```
┌────────────────────────────────┐
│     Container Layer            │ ← R/W (thin, modifiche live)
│     (upperdir)                 │
├────────────────────────────────┤
│     Image Layer 4              │ ← R/O (COPY . .)
├────────────────────────────────┤
│     Image Layer 3              │ ← R/O (RUN npm ci)
├────────────────────────────────┤
│     Image Layer 2              │ ← R/O (COPY package.json .)
├────────────────────────────────┤
│     Image Layer 1              │ ← R/O (FROM node:20-alpine)
└────────────────────────────────┘

# Meccanismo Copy-on-Write (CoW):
# Quando il container modifica un file del layer read-only,
# il file viene COPIATO nel writable layer e modificato lì.
# Il file originale nel layer R/O resta immutato.
# Questo è efficiente perché la maggior parte dei file non viene modificata.
```

```bash
# Ispeziona i layer di un'immagine
docker inspect nginx:alpine --format='{{json .RootFS.Layers}}' | jq .
# [
#   "sha256:abc123...",  ← base layer (alpine)
#   "sha256:def456...",  ← nginx packages
#   "sha256:ghi789..."   ← nginx config
# ]

# Vedi il mount overlay di un container in esecuzione
docker inspect web --format='{{json .GraphDriver.Data}}' | jq .
# {
#   "LowerDir": "/var/lib/docker/overlay2/.../diff:...",
#   "MergedDir": "/var/lib/docker/overlay2/.../merged",
#   "UpperDir": "/var/lib/docker/overlay2/.../diff",
#   "WorkDir": "/var/lib/docker/overlay2/.../work"
# }
```

---

## Ciclo di Vita di un Container

```
                          docker create
            ┌──────────────────────────────────────┐
            │                                       │
            ▼                                       │
    ┌──────────────┐     docker start       ┌──────┴───────┐
    │   Created    │──────────────────────→ │   Running     │
    └──────────────┘                        └──────┬───────┘
                                                   │
                               ┌───────────────────┼──────────────┐
                               │                   │              │
                          docker stop          docker pause    docker kill
                          (SIGTERM,            (SIGSTOP)       (SIGKILL)
                           timeout,                             │
                           SIGKILL)                             │
                               │                   │            │
                               ▼                   ▼            │
                        ┌──────────────┐  ┌──────────────┐     │
                        │   Exited     │  │   Paused     │     │
                        └──────┬───────┘  └──────┬───────┘     │
                               │                 │              │
                          docker start     docker unpause       │
                               │                 │              │
                               ▼                 ▼              │
                        ┌──────────────┐  ┌──────────────┐     │
                        │   Running    │  │   Running    │     │
                        └──────────────┘  └──────────────┘     │
                                                               │
                               ┌───────────────────────────────┘
                               ▼
                        ┌──────────────┐
                        │   Exited     │
                        │   (137)      │  ← 128 + 9 (SIGKILL)
                        └──────┬───────┘
                               │
                          docker rm
                               │
                               ▼
                        ┌──────────────┐
                        │   Removed    │
                        └──────────────┘
```

### Exit Code di Riferimento

| Exit Code | Significato | Causa Tipica |
|-----------|-------------|--------------|
| 0 | Successo | Il processo è terminato normalmente |
| 1 | Errore generico | Errore applicativo, eccezione non gestita |
| 2 | Uso errato della shell | Comando non trovato in bash |
| 126 | Non eseguibile | Permessi insufficienti sull'entrypoint |
| 127 | Comando non trovato | Entrypoint/CMD non esiste nel PATH |
| 137 | SIGKILL (128+9) | OOM killed o `docker kill` |
| 139 | SIGSEGV (128+11) | Segmentation fault |
| 143 | SIGTERM (128+15) | `docker stop` (graceful) |

```bash
# Verifica exit code
docker inspect web --format='{{.State.ExitCode}}'

# Verifica se è stato OOM killed
docker inspect web --format='{{.State.OOMKilled}}'

# Vedi motivo completo
docker inspect web --format='{{json .State}}' | jq .
```

---

## Dockerfile: Multi-Stage Build e Ottimizzazione Layer

### Comprensione dei Layer

Ogni istruzione in un Dockerfile crea un layer read-only. I layer sono cachati e condivisi tra immagini. L'ordine delle istruzioni è critico per l'efficienza della cache.

```dockerfile
# INEFFICIENTE: ogni cambio al codice invalida la cache dei pacchetti
FROM node:20-alpine
COPY . /app
WORKDIR /app
RUN npm install
CMD ["node", "server.js"]

# EFFICIENTE: i pacchetti cambiano raramente, il codice spesso
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --production
COPY . .
CMD ["node", "server.js"]
```

**Regole per la cache dei layer:**

1. Se un layer cambia, tutti i layer successivi vengono invalidati
2. `COPY` e `ADD` confrontano i checksum dei file — un file modificato invalida il layer
3. `RUN` invalida il layer ogni volta che il comando cambia (anche whitespace)
4. I layer identici tra immagini diverse sono condivisi sullo storage (content-addressable)

```bash
# Analizza l'impatto di ogni layer sulla dimensione
docker history myapp:latest --format "table {{.CreatedBy}}\t{{.Size}}"

# Output esempio:
# CREATED BY                                      SIZE
# CMD ["node" "server.js"]                         0B
# COPY . .                                         2.1MB
# RUN npm ci --production                          45MB
# COPY package.json package-lock.json ./           1.2KB
# WORKDIR /app                                     0B
# FROM node:20-alpine                              180MB
```

### Multi-Stage Build

Il multi-stage build permette di usare immagini diverse per la compilazione e per il runtime, producendo immagini finali molto più piccole:

```dockerfile
# ── Stage 1: Build ──────────────────────────────────
FROM golang:1.22-alpine AS builder

WORKDIR /src

# Dipendenze (cache-friendly)
COPY go.mod go.sum ./
RUN go mod download

# Compilazione
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -ldflags="-w -s" -o /app/server ./cmd/server

# ── Stage 2: Runtime ────────────────────────────────
FROM alpine:3.19

# Security: non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Solo il binario, non il toolchain Go
COPY --from=builder /app/server /usr/local/bin/server

# Health check
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -q --spider http://localhost:8080/health || exit 1

USER appuser
EXPOSE 8080
ENTRYPOINT ["server"]
```

Risultato: immagine da ~15 MB invece di ~800 MB (con toolchain Go incluso).

### Multi-Stage per Applicazioni Frontend

```dockerfile
# ── Stage 1: Build Node.js ──────────────────────────
FROM node:20-alpine AS frontend-build

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ── Stage 2: Build API (Python) ─────────────────────
FROM python:3.12-slim AS api-build

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt
COPY api/ .

# ── Stage 3: Runtime ────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Dipendenze Python
COPY --from=api-build /install /usr/local
COPY --from=api-build /app /app

# Frontend statico
COPY --from=frontend-build /app/dist /app/static

RUN useradd -r -s /bin/false appuser
USER appuser

EXPOSE 8000
CMD ["gunicorn", "main:app", "-b", "0.0.0.0:8000"]
```

### Multi-Stage con Test Integrati

```dockerfile
# ── Stage 1: Dependencies ──────────────────────────
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ── Stage 2: Test ──────────────────────────────────
FROM deps AS test
COPY . .
RUN npm run lint
RUN npm run test -- --coverage
# Se i test falliscono, il build si ferma qui

# ── Stage 3: Build ─────────────────────────────────
FROM deps AS build
COPY . .
RUN npm run build

# ── Stage 4: Production ───────────────────────────
FROM node:20-alpine AS production
WORKDIR /app

RUN addgroup -S app && adduser -S app -G app

COPY --from=build /app/dist ./dist
COPY --from=deps /app/node_modules ./node_modules
COPY package.json .

USER app
EXPOSE 3000
CMD ["node", "dist/server.js"]
```

### Ottimizzazione delle Dimensioni

```dockerfile
# Usa immagini base minimali
FROM debian:bookworm-slim   # invece di debian:bookworm (~80MB vs ~140MB)
FROM alpine:3.19            # ancora più piccola (~5MB)
FROM gcr.io/distroless/base # solo il runtime, zero shell (~2MB)
FROM scratch                # letteralmente vuota, per binari statici

# Combina RUN per ridurre i layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Distroless: per applicazioni che non necessitano di shell
FROM gcr.io/distroless/base-debian12
COPY --from=builder /app/server /
ENTRYPOINT ["/server"]
# NESSUNA shell, nessun package manager, nessun tool di debug
# Superficie di attacco minimale
# Non puoi fare docker exec ... sh — è una feature di sicurezza
```

### Confronto Dimensione Immagini Base

| Immagine | Dimensione | Shell | Package Manager | Uso |
|----------|-----------|-------|-----------------|-----|
| `scratch` | 0 B | No | No | Binari Go/Rust statici |
| `gcr.io/distroless/base` | ~2 MB | No | No | Binari con libc |
| `alpine:3.19` | ~5 MB | sh | apk | General purpose minimale |
| `debian:bookworm-slim` | ~80 MB | bash | apt | Compatibilità glibc |
| `ubuntu:24.04` | ~78 MB | bash | apt | Quando serve Ubuntu |
| `python:3.12-slim` | ~150 MB | bash | apt+pip | Python apps |
| `node:20-alpine` | ~180 MB | sh | apk+npm | Node.js apps |

---

## .dockerignore: Ottimizzazione Build Context

Il file `.dockerignore` è critico per performance e sicurezza. Senza di esso, l'intero contenuto della directory viene inviato al daemon come build context, inclusi `.git`, `node_modules`, file di configurazione locale, e potenzialmente segreti.

```bash
# .dockerignore — esempio completo per progetto full-stack

# Version control
.git
.gitignore
.svn

# Dipendenze (vengono installate nel container)
node_modules
vendor
__pycache__
*.pyc
.venv
venv

# Build output locali (vengono generati nel container)
dist
build
*.egg-info

# Docker files (non servono dentro l'immagine)
Dockerfile*
docker-compose*.yml
.dockerignore

# IDE e editor
.vscode
.idea
*.swp
*.swo
*~

# Documentazione e metadata
*.md
LICENSE
CHANGELOG

# Test e CI
.github
.gitlab-ci.yml
.travis.yml
coverage
.nyc_output
.pytest_cache
htmlcov

# Segreti e configurazione locale (MAI nell'immagine!)
.env
.env.*
*.pem
*.key
*.crt
secrets/
credentials/

# OS files
.DS_Store
Thumbs.db

# Log
*.log
logs/
```

```bash
# Verifica dimensione build context PRIMA del build
du -sh --exclude=.git .
# 2.3G  .  ← senza .dockerignore, invieresti 2.3 GB al daemon

# Con .dockerignore ben configurato:
# Sending build context to Docker daemon  4.521MB  ← 4.5 MB
```

---

## BuildKit Avanzato

### Attivazione e Configurazione BuildKit

```bash
# BuildKit è il default in Docker 23+, ma può essere abilitato esplicitamente
export DOCKER_BUILDKIT=1

# Oppure nel daemon config
# /etc/docker/daemon.json
# { "features": { "buildkit": true } }

# Configurazione BuildKit avanzata
# /etc/buildkit/buildkitd.toml (per buildx standalone)
[worker.oci]
  gc = true
  gckeepBytes = 10737418240  # 10GB cache

[[worker.oci.gcpolicy]]
  keepBytes = 5368709120     # 5GB min
  keepDuration = 604800      # 7 giorni
  filters = ["type==regular"]
```

### Cache Mount

```dockerfile
# syntax=docker/dockerfile:1

FROM python:3.12-slim

# Cache mount: i pacchetti pip vengono cachati tra build
# Il contenuto di /root/.cache/pip persiste tra build
# ma NON viene incluso nel layer finale
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Cache mount per apt (evita re-download dei pacchetti)
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y --no-install-recommends curl
```

### Secret Mount

```dockerfile
# Secret mount: esponi segreti solo durante il build
# Il segreto NON viene salvato in nessun layer dell'immagine

# Esempio: clonare repo privato
RUN --mount=type=secret,id=github_token \
    GITHUB_TOKEN=$(cat /run/secrets/github_token) \
    pip install git+https://${GITHUB_TOKEN}@github.com/org/private-repo.git

# Esempio: accesso a registry npm privato
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm ci
```

```bash
# Build con segreti (il file è accessibile solo durante il build)
docker build --secret id=github_token,src=./token.txt -t myapp .

# Il segreto NON appare in:
# - docker history myapp
# - docker inspect myapp
# - Nessun layer dell'immagine
```

### SSH Mount

```dockerfile
# SSH mount: usa le chiavi SSH dell'host durante il build
RUN --mount=type=ssh \
    git clone git@github.com:org/private-repo.git /app/vendor
```

```bash
# Build con SSH agent forwarding
eval $(ssh-agent)
ssh-add ~/.ssh/id_ed25519
docker build --ssh default -t myapp .
```

### Heredoc nel Dockerfile (BuildKit)

```dockerfile
# syntax=docker/dockerfile:1

FROM debian:bookworm-slim

# Heredoc per script multilinea leggibili
RUN <<EOF
    apt-get update
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates
    rm -rf /var/lib/apt/lists/*
EOF

# Heredoc per creare file di configurazione
COPY <<EOF /etc/nginx/conf.d/default.conf
server {
    listen 80;
    server_name _;
    location / {
        proxy_pass http://app:3000;
    }
}
EOF
```

### Parallelismo DAG in BuildKit

A differenza del build sequenziale classico, BuildKit costruisce un grafo aciclico diretto (DAG) delle operazioni di build e le esegue in parallelo quando possibile. Questo significa che stage indipendenti in un multi-stage build vengono eseguiti contemporaneamente.

```dockerfile
# syntax=docker/dockerfile:1

# Questi tre stage vengono eseguiti IN PARALLELO da BuildKit
# perché non hanno dipendenze tra loro
FROM golang:1.22-alpine AS api-builder
WORKDIR /src
COPY api/ .
RUN go build -o /api ./cmd/api

FROM node:20-alpine AS frontend-builder
WORKDIR /src
COPY frontend/ .
RUN npm ci && npm run build

FROM python:3.12-slim AS ml-builder
WORKDIR /src
COPY ml/ .
RUN pip install --no-cache-dir -r requirements.txt

# Questo stage dipende da tutti e tre — eseguito dopo
FROM alpine:3.19 AS final
COPY --from=api-builder /api /usr/local/bin/
COPY --from=frontend-builder /src/dist /var/www/
COPY --from=ml-builder /src /opt/ml/
```

```bash
# Visualizza il progresso parallelo durante il build
docker build --progress=plain -t myapp .

# Output mostra stage paralleli:
# => [api-builder 1/3] ...
# => [frontend-builder 1/3] ...
# => [ml-builder 1/3] ...
# Tutti iniziano simultaneamente invece che in sequenza
```

### Bind Mount nel Build

Il bind mount permette di montare file o directory dall'host durante il build senza copiarli nel layer. Utile per file di grandi dimensioni necessari solo temporaneamente.

```dockerfile
# syntax=docker/dockerfile:1

# Bind mount di un file dal build context (read-only di default)
RUN --mount=type=bind,source=large-dataset.csv,target=/tmp/data.csv \
    python process_data.py /tmp/data.csv

# Bind mount da un altro stage (utile per condividere artefatti)
FROM deps AS build
RUN --mount=type=bind,from=shared-config,source=/config,target=/app/config \
    npm run build

# Bind mount con permesso di scrittura (raro, solo quando necessario)
RUN --mount=type=bind,source=.,target=/src,rw \
    cd /src && make generate
```

### Cache Mount per Ecosistema

Ogni ecosistema ha la propria directory di cache. Usare cache mount specifici riduce drasticamente i tempi di build.

```dockerfile
# syntax=docker/dockerfile:1

# ── Go ─────────────────────────────────────────────
FROM golang:1.22-alpine AS go-build
WORKDIR /src
COPY go.mod go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go mod download
COPY . .
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 go build -o /app ./cmd/server

# ── Rust ───────────────────────────────────────────
FROM rust:1.78-slim AS rust-build
WORKDIR /src
COPY Cargo.toml Cargo.lock ./
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=cache,target=/src/target \
    mkdir src && echo "fn main() {}" > src/main.rs && \
    cargo build --release
COPY src/ src/
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    --mount=type=cache,target=/src/target \
    cargo build --release && \
    cp target/release/myapp /usr/local/bin/

# ── Java (Maven) ──────────────────────────────────
FROM maven:3.9-eclipse-temurin-21 AS java-build
WORKDIR /src
COPY pom.xml ./
RUN --mount=type=cache,target=/root/.m2/repository \
    mvn dependency:go-offline -B
COPY src/ src/
RUN --mount=type=cache,target=/root/.m2/repository \
    mvn package -DskipTests -B

# ── Java (Gradle) ─────────────────────────────────
FROM gradle:8.7-jdk21 AS gradle-build
WORKDIR /src
COPY build.gradle settings.gradle ./
RUN --mount=type=cache,target=/home/gradle/.gradle/caches \
    gradle dependencies --no-daemon
COPY src/ src/
RUN --mount=type=cache,target=/home/gradle/.gradle/caches \
    gradle build --no-daemon -x test

# ── Ruby ───────────────────────────────────────────
FROM ruby:3.3-slim AS ruby-build
WORKDIR /src
COPY Gemfile Gemfile.lock ./
RUN --mount=type=cache,target=/usr/local/bundle/cache \
    bundle install --jobs=4

# ── PHP (Composer) ─────────────────────────────────
FROM composer:2 AS php-deps
WORKDIR /src
COPY composer.json composer.lock ./
RUN --mount=type=cache,target=/tmp/cache \
    composer install --no-dev --no-scripts --prefer-dist
```

### Multi-Platform Build con Variabili di Piattaforma

BuildKit espone variabili automatiche per gestire build condizionali per piattaforma diversa.

```dockerfile
# syntax=docker/dockerfile:1

FROM --platform=$BUILDPLATFORM golang:1.22-alpine AS builder

# BUILDPLATFORM = piattaforma dove gira il build (es: linux/amd64)
# TARGETPLATFORM = piattaforma target (es: linux/arm64)
# TARGETOS, TARGETARCH, TARGETVARIANT = componenti del target

ARG TARGETOS TARGETARCH

WORKDIR /src
COPY . .
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    GOOS=${TARGETOS} GOARCH=${TARGETARCH} \
    go build -ldflags="-w -s" -o /app ./cmd/server

FROM alpine:3.19
COPY --from=builder /app /usr/local/bin/app
ENTRYPOINT ["app"]
```

```bash
# Build per 3 architetture simultaneamente
docker buildx build \
    --platform linux/amd64,linux/arm64,linux/arm/v7 \
    -t registry.example.com/myapp:1.0.0 \
    --push .
```

---

## Docker Compose v2

Docker Compose v2 è integrato come plugin di Docker (`docker compose` anziché `docker-compose`). Usa lo stesso formato YAML ma con performance migliori e feature aggiuntive.

### Struttura Completa

```yaml
# docker-compose.yml — Stack applicativo completo

# Nome del progetto (opzionale in Compose v2)
name: myapp

services:
  # ── Web Application ────────────────────────────
  app:
    build:
      context: .
      dockerfile: Dockerfile
      target: production        # multi-stage target
      args:
        NODE_ENV: production
      cache_from:
        - myregistry/myapp:cache
    image: myregistry/myapp:${VERSION:-latest}
    container_name: myapp-web
    restart: unless-stopped
    ports:
      - "8080:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://app:${DB_PASSWORD}@db:5432/myapp
      - REDIS_URL=redis://cache:6379/0
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
      cache:
        condition: service_started
    networks:
      - frontend
      - backend
    volumes:
      - uploads:/app/uploads
      - ./config:/app/config:ro
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  # ── Database ───────────────────────────────────
  db:
    image: postgres:16-alpine
    container_name: myapp-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: app
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --lc-collate=C"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./sql/init:/docker-entrypoint-initdb.d:ro
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d myapp"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 1G
    shm_size: 256m  # per PostgreSQL shared memory

  # ── Cache ──────────────────────────────────────
  cache:
    image: redis:7-alpine
    container_name: myapp-cache
    restart: unless-stopped
    command: >
      redis-server
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - backend
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  # ── Reverse Proxy ──────────────────────────────
  nginx:
    image: nginx:alpine
    container_name: myapp-proxy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - uploads:/var/www/uploads:ro
    depends_on:
      app:
        condition: service_healthy
    networks:
      - frontend

# ── Volumes ──────────────────────────────────────
volumes:
  pgdata:
    driver: local
  redis_data:
    driver: local
  uploads:
    driver: local

# ── Networks ─────────────────────────────────────
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # nessun accesso esterno
```

### Comandi Compose v2

```bash
# Avvia lo stack
docker compose up -d

# Avvia con rebuild
docker compose up -d --build

# Ferma lo stack (container rimossi, volumi preservati)
docker compose down

# Ferma e rimuovi volumi (ATTENZIONE: dati persi)
docker compose down -v

# Scala un servizio
docker compose up -d --scale app=3

# Log in tempo reale
docker compose logs -f app
docker compose logs --tail 100 db

# Esegui comando in un servizio attivo
docker compose exec app sh
docker compose exec db psql -U app -d myapp

# Esegui comando in un container effimero (one-shot)
docker compose run --rm app npm run migrate

# Stato dei servizi
docker compose ps
docker compose top

# Restart singolo servizio
docker compose restart app

# Pull immagini aggiornate e ricrea
docker compose pull
docker compose up -d  # ricrea container con nuove immagini

# Configurazione risolta (debug)
docker compose config

# Rimuovi immagini orfane
docker compose down --rmi local
```

### Profili

I profili permettono di definire servizi opzionali che si attivano solo su richiesta:

```yaml
services:
  app:
    image: myapp:latest
    # (nessun profilo → sempre attivo)

  # Servizi di debug — attivi solo con --profile debug
  mailhog:
    image: mailhog/mailhog
    profiles: ["debug"]
    ports:
      - "8025:8025"
      - "1025:1025"

  adminer:
    image: adminer
    profiles: ["debug"]
    ports:
      - "8081:8080"
    depends_on:
      - db

  # Servizi di monitoring — attivi con --profile monitoring
  prometheus:
    image: prom/prometheus
    profiles: ["monitoring"]
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    profiles: ["monitoring"]
    ports:
      - "3000:3000"
```

```bash
# Solo stack base
docker compose up -d

# Stack base + debug tools
docker compose --profile debug up -d

# Stack base + monitoring
docker compose --profile monitoring up -d

# Tutto
docker compose --profile debug --profile monitoring up -d
```

### Override e Extends

```yaml
# docker-compose.yml — configurazione base
services:
  app:
    image: myapp:latest
    environment:
      - NODE_ENV=production

# docker-compose.override.yml — caricato automaticamente in dev
services:
  app:
    build:
      context: .
      target: development
    volumes:
      - .:/app              # hot reload
      - /app/node_modules   # esclude node_modules dal mount
    environment:
      - NODE_ENV=development
      - DEBUG=app:*
    ports:
      - "9229:9229"         # Node.js debugger

# docker-compose.prod.yml — per produzione
services:
  app:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 512M
```

```yaml
# extends — ereditarietà tra servizi
# docker-compose.yml

services:
  # Servizio base con configurazione comune
  base-service:
    build:
      context: .
    environment:
      - LOG_LEVEL=info
      - METRICS_ENABLED=true
    logging:
      driver: json-file
      options:
        max-size: "10m"
    restart: unless-stopped

  # Servizi che ereditano la configurazione base
  api:
    extends:
      service: base-service
    command: ["node", "api.js"]
    ports:
      - "3000:3000"

  worker:
    extends:
      service: base-service
    command: ["node", "worker.js"]
    environment:
      - WORKER_CONCURRENCY=4

  scheduler:
    extends:
      service: base-service
    command: ["node", "scheduler.js"]
```

```bash
# Dev (carica automaticamente override)
docker compose up

# Produzione (ignora override)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### depends_on Avanzato

```yaml
services:
  app:
    depends_on:
      db:
        condition: service_healthy     # attendi healthcheck OK
        restart: true                  # riavvia app se db si riavvia
      cache:
        condition: service_started     # attendi solo lo start
      migrations:
        condition: service_completed_successfully  # attendi exit 0
    # L'app parte SOLO quando:
    # 1. db ha passato l'healthcheck
    # 2. cache è stato avviato
    # 3. migrations ha completato con successo (exit 0)

  migrations:
    image: myapp:latest
    command: ["npm", "run", "migrate"]
    depends_on:
      db:
        condition: service_healthy
    # Servizio one-shot: esegue le migrazioni e esce
```

### Watch Mode (Compose v2.22+)

Watch mode monitora i file locali e sincronizza automaticamente le modifiche nei container in esecuzione, eliminando la necessità di rebuild manuali durante lo sviluppo.

```yaml
# docker-compose.yml con watch mode
services:
  frontend:
    build:
      context: ./frontend
    ports:
      - "3000:3000"
    develop:
      watch:
        # sync: copia file modificati nel container (ideale per linguaggi interpretati)
        - action: sync
          path: ./frontend/src
          target: /app/src
          ignore:
            - "node_modules/"
            - "*.test.ts"

        # rebuild: ricostruisce l'immagine e ricrea il container
        # (ideale per linguaggi compilati o modifiche alle dipendenze)
        - action: rebuild
          path: ./frontend/package.json

        # sync+restart: sincronizza i file e riavvia il container
        # (ideale per modifiche alla configurazione)
        - action: sync+restart
          path: ./frontend/nginx.conf
          target: /etc/nginx/nginx.conf

  api:
    build:
      context: ./api
    develop:
      watch:
        - action: sync
          path: ./api/src
          target: /app/src
        - action: rebuild
          path: ./api/requirements.txt
```

```bash
# Avvia watch mode
docker compose watch

# Watch con build iniziale
docker compose watch --build

# Watch combinato con up (detached)
docker compose up -d && docker compose watch

# initial_sync (Compose v2.28+): sincronizza tutti i file all'avvio
# Prima di monitorare le modifiche, copia tutto nel container
# Previene il bug "il container esegue codice vecchio"
```

**Strategia per linguaggio:**

| Linguaggio | Azione Consigliata | Motivo |
|------------|-------------------|--------|
| Python, Ruby, PHP | `sync` | Interpretati, hot-reload nativo |
| JavaScript/TypeScript | `sync` | HMR con Vite/webpack |
| Go, Rust, Java | `rebuild` | Necessitano ricompilazione |
| Config (nginx, .env) | `sync+restart` | Il processo deve rileggere la config |

### Docker Bake (Compose Build Avanzato)

Docker Bake è il sistema di build avanzato che sostituisce il build interno di Compose. Offre orchestrazione multi-target, variabili, ereditarietà e build paralleli.

```hcl
# docker-bake.hcl — configurazione HCL per build orchestrato

variable "REGISTRY" {
  default = "ghcr.io/myorg"
}

variable "VERSION" {
  default = "latest"
}

# Gruppo: build multipli con un comando
group "default" {
  targets = ["api", "frontend", "worker"]
}

group "ci" {
  targets = ["api", "frontend", "worker"]
}

# Target base con configurazione comune
target "_common" {
  args = {
    BUILDKIT_INLINE_CACHE = "1"
  }
  labels = {
    "org.opencontainers.image.source" = "https://github.com/myorg/myapp"
    "org.opencontainers.image.version" = "${VERSION}"
  }
}

# Target specifici che ereditano dal base
target "api" {
  inherits = ["_common"]
  context = "./api"
  dockerfile = "Dockerfile"
  tags = ["${REGISTRY}/api:${VERSION}", "${REGISTRY}/api:latest"]
  platforms = ["linux/amd64", "linux/arm64"]
  cache-from = ["type=registry,ref=${REGISTRY}/api:cache"]
  cache-to = ["type=registry,ref=${REGISTRY}/api:cache,mode=max"]
}

target "frontend" {
  inherits = ["_common"]
  context = "./frontend"
  tags = ["${REGISTRY}/frontend:${VERSION}"]
  platforms = ["linux/amd64", "linux/arm64"]
}

target "worker" {
  inherits = ["_common"]
  context = "./worker"
  tags = ["${REGISTRY}/worker:${VERSION}"]
}
```

```bash
# Build tutti i target del gruppo default (in parallelo)
docker buildx bake

# Build un target specifico
docker buildx bake api

# Build con override della variabile
VERSION=1.2.3 docker buildx bake

# Build con push al registry
docker buildx bake --push

# Dry-run: mostra la configurazione risolta senza eseguire
docker buildx bake --print
```

### Direttiva include (Compose v2.20+)

La direttiva `include` permette di comporre file Compose da frammenti riutilizzabili, organizzando stack complessi in moduli.

```yaml
# docker-compose.yml — file principale
include:
  - path: ./compose/database.yml
  - path: ./compose/monitoring.yml
    env_file: .env.monitoring
  - path: ./compose/cache.yml

services:
  app:
    build: .
    depends_on:
      db:
        condition: service_healthy
    networks:
      - backend
```

```yaml
# compose/database.yml — modulo database
services:
  db:
    image: postgres:16-alpine
    volumes:
      - pgdata:/var/lib/postgresql/data
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app"]
      interval: 10s

volumes:
  pgdata:

networks:
  backend:
```

### Compose Dry-Run e Debug

```bash
# dry-run: simula l'operazione senza eseguirla (Compose v2.22+)
docker compose up --dry-run
docker compose down --dry-run
docker compose rm --dry-run

# Mostra la configurazione risolta (dopo merge di tutti i file)
docker compose config

# Mostra solo i servizi
docker compose config --services

# Mostra solo i volumi
docker compose config --volumes

# Valida la sintassi del file Compose
docker compose config --quiet
# Exit code 0 = valido, non-zero = errore di sintassi

# Mostra le immagini usate
docker compose images

# Mostra gli eventi in tempo reale
docker compose events
```

---

## Docker Networking

### Driver di Rete

| Driver | Isolamento | Uso | Performance | Multi-Host |
|--------|-----------|-----|-------------|------------|
| **bridge** | Container-level | Default, singolo host | Buona (NAT overhead) | No |
| **host** | Nessuno | Performance massima | Nativa | No |
| **overlay** | Cross-host | Docker Swarm, multi-host | Overhead VXLAN | Sì |
| **macvlan** | Layer 2 | Container con IP sulla rete fisica | Nativa | Sì (L2) |
| **ipvlan** | Layer 2/3 | Simile a macvlan, senza MAC multipli | Nativa | Sì |
| **none** | Completo | Container senza rete | N/A | N/A |

### Bridge Network (Custom)

```bash
# Crea rete bridge custom con opzioni avanzate
docker network create --driver bridge \
    --subnet 172.20.0.0/16 \
    --gateway 172.20.0.1 \
    --ip-range 172.20.240.0/20 \
    --opt "com.docker.network.bridge.name=br-mynet" \
    --opt "com.docker.network.bridge.enable_icc=true" \
    --opt "com.docker.network.bridge.enable_ip_masquerade=true" \
    --opt "com.docker.network.driver.mtu=1500" \
    mynet

# Connetti container alla rete
docker run -d --name web --network mynet nginx
docker run -d --name api --network mynet myapi

# I container nella stessa rete bridge custom possono comunicare per nome
# docker exec web ping api  → funziona (DNS integrato)

# Ispeziona la rete
docker network inspect mynet

# Connetti un container in esecuzione a una rete aggiuntiva
docker network connect backend api
docker network disconnect frontend api
```

**Come funziona il bridge internamente:**

```
Host:
┌──────────────────────────────────────────────────────────┐
│                                                           │
│  ┌─────────────┐     ┌─────────────┐                    │
│  │ Container A │     │ Container B │                    │
│  │ eth0        │     │ eth0        │                    │
│  │ 172.20.0.2  │     │ 172.20.0.3  │                    │
│  └──────┬──────┘     └──────┬──────┘                    │
│         │ (veth pair)       │ (veth pair)               │
│         │                   │                            │
│  ┌──────▼───────────────────▼──────┐                    │
│  │     br-mynet (Linux bridge)     │                    │
│  │     172.20.0.1                  │                    │
│  └─────────────┬───────────────────┘                    │
│                │                                         │
│          iptables NAT                                    │
│                │                                         │
│  ┌─────────────▼───────────────────┐                    │
│  │     eth0 (host interface)       │                    │
│  │     192.168.1.100               │                    │
│  └─────────────────────────────────┘                    │
└──────────────────────────────────────────────────────────┘

# Ogni container ha una veth pair:
# - un'estremità nel network namespace del container (eth0)
# - l'altra estremità attaccata al bridge sull'host
# Il bridge funziona come uno switch L2 virtuale
```

### Default Bridge vs Custom Bridge

| Caratteristica | Default `bridge` | Custom bridge |
|---------------|------------------|---------------|
| DNS automatico | No (solo `--link`, deprecato) | Sì (per nome container) |
| Isolamento | Tutti i container sulla stessa rete | Solo container della stessa rete |
| Connessione al volo | No | Sì (`docker network connect`) |
| Variabili d'ambiente | Condivise via `--link` | No (usa DNS) |
| Configurabilità | Limitata | Subnet, gateway, opzioni |

### Host Network

```bash
# Il container usa lo stack di rete dell'host
docker run -d --network host nginx

# Nessun port mapping necessario/possibile
# Il container ascolta direttamente sulle porte dell'host
# Performance: zero overhead di NAT

# Uso tipico:
# - Applicazioni con molte porte (es: servizi discovery)
# - Monitoring che deve vedere tutto il traffico di rete
# - Performance networking critica
# - Container che fa packet capture

# ATTENZIONE: nessun isolamento di rete!
# Il container vede tutte le interfacce dell'host
```

### Macvlan

```bash
# Crea rete macvlan — il container ottiene un IP sulla rete fisica
docker network create -d macvlan \
    --subnet=192.168.1.0/24 \
    --gateway=192.168.1.1 \
    -o parent=eth0 \
    macnet

# Container con IP specifico sulla LAN
docker run -d --name server \
    --network macnet \
    --ip 192.168.1.100 \
    nginx

# Il container è raggiungibile direttamente dalla LAN come fosse un host fisico

# NOTA: l'host NON può comunicare con il container macvlan
# Per comunicazione host↔container macvlan:
ip link add macvlan-host link eth0 type macvlan mode bridge
ip addr add 192.168.1.200/32 dev macvlan-host
ip link set macvlan-host up
ip route add 192.168.1.100/32 dev macvlan-host

# Modalità macvlan:
# bridge  — i container possono comunicare tra loro (default)
# private — i container NON possono comunicare tra loro
# vepa    — traffico inter-container passa per lo switch fisico
# passthru — assegna l'interfaccia fisica a un singolo container
```

### IPvlan

```bash
# Simile a macvlan ma tutti i container condividono il MAC dell'host
# Utile quando lo switch limita il numero di MAC per porta

# Layer 2 mode (come macvlan ma con un solo MAC)
docker network create -d ipvlan \
    --subnet=192.168.1.0/24 \
    --gateway=192.168.1.1 \
    -o parent=eth0 \
    -o ipvlan_mode=l2 \
    ipvlan-l2

# Layer 3 mode (routing, nessun broadcast)
docker network create -d ipvlan \
    --subnet=10.10.10.0/24 \
    -o parent=eth0 \
    -o ipvlan_mode=l3 \
    ipvlan-l3
```

### Overlay (Multi-Host)

```bash
# Richiede Docker Swarm o un key-value store esterno
docker swarm init

# Crea rete overlay
docker network create -d overlay --attachable myoverlay

# --attachable permette ai container standalone di unirsi alla rete overlay
# Senza --attachable, solo i servizi Swarm possono usarla

# I container su diversi nodi possono comunicare
docker service create --name web --network myoverlay nginx

# La rete overlay usa VXLAN per incapsulare il traffico L2 su L3
# Header overhead: 50 byte per pacchetto
# MTU consigliato: 1450 (1500 - 50 byte VXLAN)
```

### DNS Interno e Service Discovery

```bash
# Docker fornisce un DNS resolver interno (127.0.0.11) per le reti bridge custom
# Il nome del container è risolvibile come hostname

# Alias DNS — il container è raggiungibile con più nomi
docker run -d --name db --network mynet --network-alias database postgres
# Sia "db" che "database" risolvono allo stesso container

# Round-robin DNS per scaling
docker run -d --name app1 --network mynet --network-alias app myimage
docker run -d --name app2 --network mynet --network-alias app myimage
docker run -d --name app3 --network mynet --network-alias app myimage
# "app" risolve alternando tra app1, app2 e app3

# Verifica DNS
docker exec web nslookup database
# Server:    127.0.0.11
# Address:   127.0.0.11#53
# Non-authoritative answer:
# Name: database
# Address: 172.20.0.5

# Verifica risoluzione round-robin
for i in $(seq 10); do
    docker exec web nslookup app 2>/dev/null | grep Address | tail -1
done
# Address: 172.20.0.10
# Address: 172.20.0.11
# Address: 172.20.0.12
# Address: 172.20.0.10  ← round-robin
```

---

## Docker Volumes e Storage

### Tipi di Mount

```
┌──────────────────────────────────────────────────────┐
│                      Container                        │
│                                                       │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Named    │  │ Bind Mount   │  │ tmpfs Mount   │  │
│  │ Volume   │  │              │  │               │  │
│  │ /data    │  │ /app/config  │  │ /tmp          │  │
│  └────┬─────┘  └──────┬───────┘  └───────┬───────┘  │
└───────┼───────────────┼──────────────────┼───────────┘
        │               │                  │
        ▼               ▼                  ▼
   Docker area     Host filesystem      RAM (volatile)
   /var/lib/docker  /host/path          Non scritto
   /volumes/...                         su disco
```

```bash
# Named Volume — gestito da Docker (raccomandato per dati persistenti)
docker run -v pgdata:/var/lib/postgresql/data postgres

# Bind mount — file/directory dell'host montati nel container
docker run -v /host/path:/container/path:ro nginx
# Opzioni mount:
# :ro     → read-only
# :rw     → read-write (default)
# :z      → SELinux shared label
# :Z      → SELinux private label
# :cached → performance su macOS (write-behind)
# :delegated → performance su macOS (read-ahead)

# tmpfs mount — in memoria, non persistente, non scritto su disco
docker run --tmpfs /tmp:rw,size=100m,noexec myapp
# Uso: dati temporanei sensibili che non devono toccare il disco

# Sintassi --mount (più esplicita e raccomandata)
docker run --mount type=volume,source=pgdata,target=/var/lib/postgresql/data postgres
docker run --mount type=bind,source=/host/config,target=/app/config,readonly nginx
docker run --mount type=tmpfs,target=/tmp,tmpfs-size=104857600,tmpfs-mode=1777 myapp
```

### Gestione Volumi

```bash
# Crea volume con driver locale e opzioni
docker volume create --driver local \
    --opt type=none \
    --opt device=/mnt/storage/data \
    --opt o=bind \
    mydata

# Volume con NFS
docker volume create --driver local \
    --opt type=nfs \
    --opt o=addr=10.0.0.5,rw,nfsvers=4 \
    --opt device=:/exports/data \
    nfs_data

# Lista volumi
docker volume ls
docker volume ls --filter dangling=true  # volumi non associati

# Ispeziona
docker volume inspect mydata
# {
#     "CreatedAt": "2024-04-01T10:00:00Z",
#     "Driver": "local",
#     "Labels": {},
#     "Mountpoint": "/var/lib/docker/volumes/mydata/_data",
#     "Name": "mydata",
#     "Options": null,
#     "Scope": "local"
# }

# Rimuovi volumi orfani
docker volume prune
docker volume prune --filter "label!=keep"  # mantieni volumi con label "keep"

# Backup di un volume
docker run --rm \
    -v pgdata:/source:ro \
    -v $(pwd):/backup \
    alpine tar czf /backup/pgdata-$(date +%Y%m%d).tar.gz -C /source .

# Restore di un volume
docker volume create pgdata_restored
docker run --rm \
    -v pgdata_restored:/target \
    -v $(pwd):/backup \
    alpine tar xzf /backup/pgdata-20240401.tar.gz -C /target

# Copia tra volumi
docker run --rm \
    -v source_vol:/from:ro \
    -v dest_vol:/to \
    alpine sh -c "cp -a /from/. /to/"
```

### Volume in Docker Compose

```yaml
volumes:
  # Volume semplice
  pgdata:

  # Volume con opzioni
  app_data:
    driver: local
    driver_opts:
      type: none
      device: /mnt/ssd/app_data
      o: bind

  # Volume con label
  logs:
    labels:
      com.example.project: "myapp"
      com.example.environment: "production"

  # Volume esterno (creato fuori da Compose, deve già esistere)
  shared_data:
    external: true
    name: my-shared-volume
```

---

## Security

### Principio del Minimo Privilegio

```dockerfile
# Nel Dockerfile: crea e usa un utente non-root
RUN groupadd -r appgroup && useradd -r -g appgroup -s /bin/false appuser
USER appuser

# Filesystem read-only dove possibile
# docker run --read-only --tmpfs /tmp myapp
```

### Rootless Docker

```bash
# Installa Docker rootless (il daemon gira come utente non-root)
dockerd-rootless-setuptool.sh install

# Verifica
docker context ls
docker info | grep -i root
# Security Options: rootless

# Il daemon usa user namespaces automaticamente
# root nel container → UID mappato a utente non privilegiato sull'host

# Configurazione
# ~/.config/docker/daemon.json (non /etc/docker/)

# Limitazioni rootless:
# - Non può bindare porte < 1024 senza configurazione
#   Soluzione: sysctl net.ipv4.ip_unprivileged_port_start=80
# - Alcune funzionalità di rete limitate (no macvlan, ipvlan)
# - cgroup v2 necessario per resource limits
# - Overlay network non disponibile senza Swarm
# - Filesystem: usa fuse-overlayfs invece di overlay2

# Abilita porte privilegiate per rootless
sudo sysctl -w net.ipv4.ip_unprivileged_port_start=80
# Persistente: echo "net.ipv4.ip_unprivileged_port_start=80" >> /etc/sysctl.conf
```

### User Namespaces (Docker Rootful)

```bash
# Abilita user namespaces nel daemon Docker rootful
# /etc/docker/daemon.json
{
    "userns-remap": "default"
}

# Docker crea automaticamente l'utente "dockremap"
# e configura /etc/subuid e /etc/subgid:
# dockremap:100000:65536

# Risultato: root (UID 0) nel container → UID 100000 sull'host
# Se il container evade, l'attaccante ha UID 100000, non root

# Verifica il mapping
cat /etc/subuid
# dockremap:100000:65536

# Con user namespace, il container:
# - Non può scrivere su file di root dell'host
# - Non può accedere a device privilegiati
# - Non può montare filesystem
# Anche se "root" nel container

# Verifica che sia attivo
docker info | grep "User Namespace"
# userns

# NOTA: user namespaces e --privileged sono mutualmente esclusivi
```

### Seccomp Profile

```json
{
    "defaultAction": "SCMP_ACT_ERRNO",
    "architectures": ["SCMP_ARCH_X86_64", "SCMP_ARCH_X86", "SCMP_ARCH_AARCH64"],
    "syscalls": [
        {
            "names": [
                "accept4", "access", "arch_prctl", "bind", "brk",
                "clock_gettime", "clock_getres", "close", "connect",
                "epoll_create1", "epoll_ctl", "epoll_wait", "exit_group",
                "fcntl", "fstat", "futex", "getpid", "getuid", "getgid",
                "getsockname", "getsockopt", "ioctl", "listen", "lseek",
                "mmap", "mprotect", "munmap", "nanosleep", "open", "openat",
                "poll", "read", "recvfrom", "rt_sigaction", "rt_sigprocmask",
                "sendto", "set_robust_list", "setsockopt", "socket",
                "stat", "write", "writev", "pread64", "pwrite64",
                "getrandom", "getdents64", "newfstatat"
            ],
            "action": "SCMP_ACT_ALLOW"
        }
    ]
}
```

```bash
# Usa seccomp profile custom
docker run --security-opt seccomp=./seccomp-profile.json myapp

# Disabilita seccomp (NON raccomandato, solo per debug)
docker run --security-opt seccomp=unconfined myapp

# Il profilo default di Docker blocca ~44 syscall su ~300+
# Tra quelle bloccate: mount, reboot, swapon, ptrace, init_module

# Verifica il profilo attivo
docker inspect --format='{{.HostConfig.SecurityOpt}}' container_id

# Genera profilo da un container in esecuzione (con strace)
docker run --cap-add SYS_PTRACE --security-opt seccomp=unconfined myapp
# poi usa strace per catturare le syscall usate
```

### Capabilities

```bash
# Docker rimuove di default molte capabilities, ma ne mantiene alcune
# Lista capabilities di default del container Docker:
# CHOWN, DAC_OVERRIDE, FSETID, FOWNER, MKNOD, NET_RAW, SETGID,
# SETUID, SETFCAP, SETPCAP, NET_BIND_SERVICE, SYS_CHROOT, KILL,
# AUDIT_WRITE

# Rimuovi TUTTE le capabilities e aggiungi solo quelle necessarie
docker run --cap-drop ALL --cap-add NET_BIND_SERVICE myapp

# Lista capabilities di un container in esecuzione
docker exec container_id cat /proc/1/status | grep Cap
# CapEff: 00000000a80425fb

# Decodifica
capsh --decode=00000000a80425fb

# Capabilities comuni e quando servono:
# NET_BIND_SERVICE  — bind a porte < 1024
# SYS_TIME          — modifica clock di sistema (NTP)
# NET_RAW           — raw socket (ping, tcpdump)
# CHOWN             — cambia ownership file
# DAC_OVERRIDE      — bypassa permessi file
# SYS_PTRACE        — strace, gdb nel container
# NET_ADMIN         — configurazione rete (iptables, routing)
# SYS_ADMIN         — operazioni varie privilegiate (mount, ecc)

# BEST PRACTICE: inizia con --cap-drop ALL e aggiungi solo quelle necessarie
docker run \
    --cap-drop ALL \
    --cap-add NET_BIND_SERVICE \
    --cap-add CHOWN \
    --cap-add SETUID \
    --cap-add SETGID \
    nginx
```

### no-new-privileges

```bash
# Impedisce ai processi nel container di acquisire nuovi privilegi
# (via setuid binaries, file capabilities, ecc)
docker run --security-opt no-new-privileges myapp

# In Docker Compose:
# services:
#   app:
#     security_opt:
#       - no-new-privileges:true

# Esempio: senza no-new-privileges, un binario setuid nel container
# potrebbe elevare i privilegi del processo. Con il flag, setuid viene ignorato.

# Combinazione raccomandata per produzione:
docker run \
    --read-only \
    --tmpfs /tmp:rw,noexec,nosuid,size=100m \
    --cap-drop ALL \
    --cap-add NET_BIND_SERVICE \
    --security-opt no-new-privileges \
    --security-opt seccomp=./custom-seccomp.json \
    --user 1000:1000 \
    myapp
```

### Read-Only Root Filesystem

```bash
# Il filesystem del container è read-only
# Solo tmpfs e volumi sono scrivibili
docker run \
    --read-only \
    --tmpfs /tmp:rw,noexec,nosuid \
    --tmpfs /run:rw,noexec,nosuid \
    -v app_data:/app/data \
    myapp

# Identifica cosa ha bisogno di scrivere il container
docker diff container_name
# C /tmp          ← modified
# A /tmp/sess_abc ← added
# A /var/log/app  ← added

# Usa questa informazione per configurare tmpfs/volumi
```

### AppArmor e SELinux per Container

```bash
# AppArmor (Ubuntu/Debian)
# Docker applica il profilo docker-default automaticamente

# Profilo custom
docker run --security-opt apparmor=docker-myapp myapp

# Disabilita AppArmor (NON raccomandato)
docker run --security-opt apparmor=unconfined myapp

# SELinux (RHEL/Fedora)
# Docker usa il tipo svirt_lxc_net_t per i container

# Con Podman e bind mount:
podman run -v /data:/data:Z myimage  # :Z = private SELinux label
podman run -v /data:/data:z myimage  # :z = shared SELinux label

# Con Docker e bind mount su RHEL:
chcon -Rt svirt_sandbox_file_t /data
docker run -v /data:/data myapp
```

### Scanning Vulnerabilità

```bash
# Docker Scout (integrato in Docker Desktop e CLI)
docker scout cves myimage:latest
docker scout recommendations myimage:latest

# Trivy (open source, molto completo)
trivy image myimage:latest
trivy image --exit-code 1 --severity CRITICAL,HIGH myimage:latest

# Grype (Anchore)
grype myimage:latest

# Nel CI/CD pipeline — blocca build con vulnerabilità critiche
docker build -t myapp:test .
trivy image --exit-code 1 --severity CRITICAL myapp:test
# Se exit code ≠ 0, il pipeline fallisce

# Scan del Dockerfile per best practice
hadolint Dockerfile
# Output:
# DL3006 Always tag the version of an image explicitly
# DL3008 Pin versions in apt get install
# DL3018 Pin versions in apk add
# DL3025 Use arguments JSON notation for CMD and ENTRYPOINT
```

### Rootless Docker Approfondito

Docker rootless esegue l'intero stack (daemon, containerd, runc) come utente non privilegiato. Questo riduce drasticamente l'impatto di un'eventuale vulnerabilità nel daemon stesso.

```bash
# Prerequisiti per rootless Docker
# - uidmap (newuidmap, newgidmap)
# - dbus-user-session
# - slirp4netns OPPURE rootlesskit con pasta

# Installazione
curl -fsSL https://get.docker.com/rootless | sh

# Configura le variabili d'ambiente (aggiungile a ~/.bashrc)
export PATH=$HOME/bin:$PATH
export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock

# Avvia il daemon rootless
systemctl --user start docker
systemctl --user enable docker

# Abilita il lingering per avvio automatico senza login
sudo loginctl enable-linger $(whoami)
```

**Networking in rootless Docker:**

```bash
# slirp4netns (default) — networking in userspace
# Ogni container ottiene un'interfaccia TAP nello user namespace
# Performance limitata (~1-3 Gbps) per l'overhead dello userspace
docker info | grep -i network
# Network: slirp4netns

# pasta (Performance Alternative per Slirp4netns)
# Più veloce di slirp4netns, usa un socket pair
# Configurazione in ~/.config/docker/daemon.json:
# { "network-control-plane-mtu": 1500 }

# Confronto performance networking rootless:
# slirp4netns:  ~1-3 Gbps (overhead userspace elevato)
# pasta:        ~5-8 Gbps (socket pair, meno overhead)
# rootful:      ~10+ Gbps (veth bridge kernel-level)

# Per porte < 1024 in rootless mode:
sudo sysctl -w net.ipv4.ip_unprivileged_port_start=0
# Oppure usa un reverse proxy (nginx/caddy) rootful davanti
```

**Storage in rootless Docker:**

```bash
# Rootless usa fuse-overlayfs invece di overlay2 nativo del kernel
# perché overlay2 richiede privilegi per operazioni mount
docker info | grep -i storage
# Storage Driver: fuse-overlayfs

# fuse-overlayfs ha un overhead I/O di circa 10-20% rispetto a overlay2
# Per workload I/O intensivi, considera:
# 1. Usare volumi (i volumi bypassano fuse-overlayfs)
# 2. Passare a rootful con user namespaces (userns-remap)

# Directory dati rootless (non /var/lib/docker):
# ~/.local/share/docker/

# cgroup v2 è necessario per resource limits in rootless
# Verifica:
stat -fc %T /sys/fs/cgroup/
# cgroup2fs ← OK
# tmpfs ← cgroup v1, resource limits non funzioneranno

# Delega cgroup v2 all'utente
sudo mkdir -p /etc/systemd/system/user@.service.d
cat <<EOF | sudo tee /etc/systemd/system/user@.service.d/delegate.conf
[Service]
Delegate=cpu cpuset io memory pids
EOF
sudo systemctl daemon-reload
```

### Scanning Vulnerabilità Approfondito

#### Trivy — Scanner Open Source Completo

Trivy è lo scanner più adottato per immagini container, filesystem, repository Git, e configurazioni IaC. Non richiede un daemon e produce output in formati multipli.

```bash
# Installazione Trivy
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# Scan base di un'immagine
trivy image myapp:latest

# Scan con filtro severità e exit code per CI
trivy image --exit-code 1 --severity CRITICAL,HIGH myapp:latest

# Scan con output JSON (per integrazione con tool)
trivy image --format json --output results.json myapp:latest

# Scan con template personalizzato
trivy image --format template \
    --template "@contrib/html.tpl" \
    --output report.html myapp:latest

# Generazione SBOM (Software Bill of Materials)
trivy image --format spdx-json --output sbom.json myapp:latest
trivy image --format cyclonedx --output sbom-cdx.json myapp:latest

# Scan del filesystem locale (prima del build)
trivy fs --security-checks vuln,secret,config .

# Scan di un Dockerfile per misconfiguration
trivy config Dockerfile

# Ignora vulnerabilità specifiche (con file .trivyignore)
# .trivyignore:
# CVE-2023-12345
# CVE-2024-67890

# Scan offline (per ambienti air-gapped)
trivy image --download-db-only
trivy image --skip-db-update --offline-scan myapp:latest

# Scan con database aggiornato e cache
trivy image --cache-dir /tmp/trivy-cache myapp:latest
```

#### Grype — Scanner Anchore

```bash
# Installazione Grype
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin

# Scan base
grype myapp:latest

# Scan con filtro e output
grype myapp:latest --fail-on critical
grype myapp:latest -o json > grype-results.json
grype myapp:latest -o table

# Scan da SBOM (generata da Syft o Trivy)
syft myapp:latest -o spdx-json > sbom.json
grype sbom:sbom.json

# Grype usa i database di vulnerabilità di:
# - NVD (National Vulnerability Database)
# - GitHub Security Advisories
# - Alpine SecDB, Debian Security Tracker
# - Red Hat OVAL, Ubuntu CVE Tracker, ecc.

# Pattern CI/CD: doppio scanner per copertura massima
trivy image --exit-code 1 --severity CRITICAL myapp:latest && \
grype myapp:latest --fail-on critical
# Se uno dei due fallisce, il pipeline si blocca
```

#### Snyk Container

```bash
# Autenticazione
snyk auth

# Scan con Snyk
snyk container test myapp:latest
snyk container test myapp:latest --severity-threshold=high

# Monitoraggio continuo (registra l'immagine per notifiche)
snyk container monitor myapp:latest

# Snyk analizza anche le dipendenze applicative dentro il container
# Non si limita ai pacchetti OS come Trivy/Grype base
```

#### Pipeline CI Integrato per Scanning

```yaml
# Esempio GitHub Actions con doppio scanner
# .github/workflows/security-scan.yml
# jobs:
#   scan:
#     runs-on: ubuntu-latest
#     steps:
#       - uses: actions/checkout@v4
#
#       - name: Build immagine
#         run: docker build -t myapp:test .
#
#       - name: Hadolint (Dockerfile lint)
#         uses: hadolint/hadolint-action@v3
#         with:
#           dockerfile: Dockerfile
#
#       - name: Trivy (commit-gate scan)
#         uses: aquasecurity/trivy-action@master
#         with:
#           image-ref: myapp:test
#           exit-code: 1
#           severity: CRITICAL,HIGH
#           format: sarif
#           output: trivy-results.sarif
#
#       - name: Grype (secondary scan)
#         uses: anchore/scan-action@v3
#         with:
#           image: myapp:test
#           fail-build: true
#           severity-cutoff: critical
#
#       - name: Upload SARIF
#         uses: github/codeql-action/upload-sarif@v3
#         with:
#           sarif_file: trivy-results.sarif
```

---

## Logging e Log Driver

Docker supporta diversi driver per la gestione dei log dei container. La scelta del driver dipende dall'infrastruttura di logging.

### Driver Disponibili

| Driver | Destinazione | Rotazione | Performance | Uso |
|--------|-------------|-----------|-------------|-----|
| `json-file` | File JSON su disco | Sì (configurabile) | Buona | Default, sviluppo |
| `local` | File binario ottimizzato | Sì (automatica) | Migliore | Produzione locale |
| `syslog` | Syslog daemon | Dipende da syslog | Buona | Integrazione syslog |
| `journald` | Systemd journal | Sì (systemd) | Buona | Sistemi con systemd |
| `fluentd` | Fluentd/Fluent Bit | N/A | Buona | Stack EFK |
| `gelf` | Graylog (GELF) | N/A | Buona | Stack Graylog |
| `awslogs` | CloudWatch | N/A | Dipende da rete | AWS |
| `gcplogs` | Cloud Logging | N/A | Dipende da rete | GCP |
| `splunk` | Splunk HEC | N/A | Dipende da rete | Splunk |
| `none` | Nessuno | N/A | Massima | Container che non loggano |

### Configurazione json-file (Default)

```bash
# Configurazione globale nel daemon
# /etc/docker/daemon.json
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "5",
        "compress": "true",
        "labels": "production,environment",
        "env": "APP_VERSION,HOSTNAME"
    }
}

# Override per singolo container
docker run -d \
    --log-driver json-file \
    --log-opt max-size=50m \
    --log-opt max-file=10 \
    --log-opt compress=true \
    myapp

# In Docker Compose
# services:
#   app:
#     logging:
#       driver: json-file
#       options:
#         max-size: "10m"
#         max-file: "5"
#         compress: "true"

# I log json-file sono in:
# /var/lib/docker/containers/<container-id>/<container-id>-json.log
```

### Driver local (Ottimizzato)

```bash
# Il driver "local" usa un formato binario compresso
# Più efficiente di json-file, con rotazione automatica

{
    "log-driver": "local",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3",
        "compress": "true"
    }
}

# NOTA: docker logs funziona con local, json-file e journald
# Con syslog, fluentd, gelf, awslogs → docker logs NON funziona
```

### Driver syslog

```bash
docker run -d \
    --log-driver syslog \
    --log-opt syslog-address=udp://logserver:514 \
    --log-opt syslog-facility=local0 \
    --log-opt tag="myapp/{{.Name}}" \
    --log-opt syslog-format=rfc5424 \
    myapp
```

### Driver fluentd

```bash
docker run -d \
    --log-driver fluentd \
    --log-opt fluentd-address=localhost:24224 \
    --log-opt tag="docker.{{.Name}}" \
    --log-opt fluentd-async=true \
    --log-opt fluentd-buffer-limit=1048576 \
    myapp
```

### Driver journald

```bash
docker run -d \
    --log-driver journald \
    --log-opt tag="myapp" \
    myapp

# Leggi i log via journalctl
journalctl CONTAINER_NAME=myapp-web --since "1 hour ago"
journalctl -u docker --since "10 min ago"
```

### Best Practice: Dual Logging

```bash
# Problema: con driver remoti (fluentd, syslog), docker logs non funziona
# Soluzione: usa json-file/local + un log shipper sidecar

# docker-compose.yml
# services:
#   app:
#     logging:
#       driver: json-file
#       options:
#         max-size: "10m"
#
#   log-shipper:
#     image: fluent/fluent-bit
#     volumes:
#       - /var/lib/docker/containers:/var/lib/docker/containers:ro
```

---

## Resource Limits e Cgroups

### Limiti CPU

```bash
# Limita a 1.5 CPU
docker run --cpus=1.5 myapp

# Equivalente con cgroup period/quota
docker run --cpu-period=100000 --cpu-quota=150000 myapp
# 150000/100000 = 1.5 CPU

# CPU shares (peso relativo, non limite assoluto)
docker run --cpu-shares=512 myapp   # default: 1024
# Se due container con shares 1024 e 512 competono per CPU,
# il primo riceve 2/3 del tempo CPU, il secondo 1/3

# Binding a CPU core specifici
docker run --cpuset-cpus="0,1" myapp      # solo core 0 e 1
docker run --cpuset-cpus="0-3" myapp      # core 0, 1, 2, 3

# In Docker Compose
# services:
#   app:
#     deploy:
#       resources:
#         limits:
#           cpus: '2.0'
#         reservations:
#           cpus: '0.5'
#     cpuset: "0,1"
```

### Limiti Memoria

```bash
# Limite hard di memoria (container viene OOM killed se supera)
docker run --memory=512m myapp

# Memoria + swap
docker run --memory=512m --memory-swap=1g myapp
# L'app può usare 512m di RAM + 512m di swap (1g totale)

# Disabilita swap per il container
docker run --memory=512m --memory-swap=512m myapp

# Memory reservation (soft limit, per scheduling)
docker run --memory=512m --memory-reservation=256m myapp

# OOM score adjustment (priorità di kill in caso di OOM)
docker run --oom-score-adj=-500 myapp  # meno probabile di essere killed
docker run --oom-kill-disable myapp    # PERICOLOSO: non verrà mai OOM killed

# Kernel memory limit
docker run --kernel-memory=50m myapp

# Verifica limiti attivi
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.CPUPerc}}"
# NAME          MEM USAGE / LIMIT     MEM %   CPU %
# myapp-web     245.2MiB / 512MiB     47.89%  2.34%
# myapp-db      890.3MiB / 1GiB       86.94%  5.12%
```

### Limiti I/O

```bash
# Limite bandwidth lettura/scrittura per device
docker run \
    --device-read-bps /dev/sda:10mb \
    --device-write-bps /dev/sda:10mb \
    myapp

# Limite IOPS
docker run \
    --device-read-iops /dev/sda:1000 \
    --device-write-iops /dev/sda:500 \
    myapp

# Peso I/O relativo (10-1000, default 500)
docker run --blkio-weight 300 myapp
```

### Limite PID

```bash
# Limita il numero di processi nel container (previene fork bomb)
docker run --pids-limit=100 myapp

# Configurazione globale
# /etc/docker/daemon.json
# { "default-pids-limit": 200 }
```

---

## Buildx: Multi-Platform e Cache

### Buildx Setup

```bash
# Crea un builder buildx
docker buildx create --name multiarch --driver docker-container --use

# Verifica le piattaforme supportate (con QEMU)
docker buildx inspect --bootstrap
# Platforms: linux/amd64, linux/arm64, linux/arm/v7, linux/arm/v6,
#            linux/386, linux/ppc64le, linux/s390x

# Installa QEMU per emulazione cross-platform
docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
```

### Build Multi-Platform

```bash
# Build per amd64 e arm64 e push al registry
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t registry.example.com/myapp:1.0.0 \
    --push .

# Build solo per una piattaforma e carica localmente
docker buildx build \
    --platform linux/arm64 \
    -t myapp:arm64 \
    --load .  # --load funziona solo con una singola piattaforma

# Build con output specifico
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t myapp:latest \
    --output type=registry,ref=registry.example.com/myapp:latest .
```

### Cache Export/Import

```bash
# Esporta cache del build in un registry (inline, per layer)
docker buildx build \
    --cache-to type=inline \
    --push \
    -t registry.example.com/myapp:latest .

# Importa cache dal registry
docker buildx build \
    --cache-from type=registry,ref=registry.example.com/myapp:latest \
    -t myapp:latest .

# Cache su filesystem locale (per CI)
docker buildx build \
    --cache-to type=local,dest=/tmp/buildx-cache,mode=max \
    -t myapp:latest .

docker buildx build \
    --cache-from type=local,src=/tmp/buildx-cache \
    -t myapp:latest .

# Cache in un registry separato (cache manifest)
docker buildx build \
    --cache-to type=registry,ref=registry.example.com/myapp:cache \
    --cache-from type=registry,ref=registry.example.com/myapp:cache \
    -t registry.example.com/myapp:latest \
    --push .

# Cache S3 (per CI distribuito)
docker buildx build \
    --cache-to type=s3,region=eu-west-1,bucket=my-buildcache,name=myapp \
    --cache-from type=s3,region=eu-west-1,bucket=my-buildcache,name=myapp \
    -t myapp:latest .
```

### Buildx in CI/CD

```yaml
# GitHub Actions example
# .github/workflows/build.yml

# jobs:
#   build:
#     steps:
#       - uses: docker/setup-buildx-action@v3
#       - uses: docker/login-action@v3
#         with:
#           registry: ghcr.io
#           username: ${{ github.actor }}
#           password: ${{ secrets.GITHUB_TOKEN }}
#       - uses: docker/build-push-action@v5
#         with:
#           push: true
#           platforms: linux/amd64,linux/arm64
#           tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
#           cache-from: type=gha
#           cache-to: type=gha,mode=max
```

---

## Registry e Image Management

### Docker Hub, GHCR, ECR

```bash
# Tag e push a Docker Hub
docker tag myapp:latest username/myapp:1.0.0
docker push username/myapp:1.0.0

# GitHub Container Registry
docker login ghcr.io -u USERNAME
docker tag myapp:latest ghcr.io/username/myapp:1.0.0
docker push ghcr.io/username/myapp:1.0.0

# AWS ECR
aws ecr get-login-password --region eu-west-1 | \
    docker login --username AWS --password-stdin 123456789.dkr.ecr.eu-west-1.amazonaws.com
docker tag myapp:latest 123456789.dkr.ecr.eu-west-1.amazonaws.com/myapp:1.0.0
docker push 123456789.dkr.ecr.eu-west-1.amazonaws.com/myapp:1.0.0
```

### Registry Self-Hosted: Distribution (ex Docker Registry)

```bash
# Registry locale per test
docker run -d -p 5000:5000 --name registry registry:2

# Push a registry locale
docker tag myapp:latest localhost:5000/myapp:1.0.0
docker push localhost:5000/myapp:1.0.0

# Registry con autenticazione e TLS
mkdir -p /opt/registry/{auth,certs,data}

# Genera htpasswd
docker run --rm --entrypoint htpasswd httpd:2 -Bbn admin password123 \
    > /opt/registry/auth/htpasswd

# docker-compose per registry production-ready
# services:
#   registry:
#     image: registry:2
#     ports:
#       - "5000:5000"
#     environment:
#       REGISTRY_AUTH: htpasswd
#       REGISTRY_AUTH_HTPASSWD_REALM: "Registry Realm"
#       REGISTRY_AUTH_HTPASSWD_PATH: /auth/htpasswd
#       REGISTRY_HTTP_TLS_CERTIFICATE: /certs/domain.crt
#       REGISTRY_HTTP_TLS_KEY: /certs/domain.key
#       REGISTRY_STORAGE_DELETE_ENABLED: "true"
#     volumes:
#       - /opt/registry/auth:/auth
#       - /opt/registry/certs:/certs
#       - /opt/registry/data:/var/lib/registry
```

### Harbor (Enterprise Registry)

Harbor è un registry enterprise open source con scanning, firme, replicazione e RBAC:

```bash
# Installazione Harbor (richiede docker-compose)
wget https://github.com/goharbor/harbor/releases/download/v2.10.0/harbor-offline-installer-v2.10.0.tgz
tar xzf harbor-offline-installer-v2.10.0.tgz
cd harbor

# Configura harbor.yml
# hostname: harbor.example.com
# https:
#   certificate: /etc/ssl/certs/harbor.crt
#   private_key: /etc/ssl/private/harbor.key
# harbor_admin_password: secure_password
# database:
#   password: db_password

# Installa
./install.sh --with-trivy  # con vulnerability scanning

# Usa Harbor
docker login harbor.example.com
docker tag myapp:latest harbor.example.com/myproject/myapp:1.0.0
docker push harbor.example.com/myproject/myapp:1.0.0

# Caratteristiche Harbor:
# - Vulnerability scanning (integrato Trivy)
# - Content trust (Notary)
# - Replicazione tra registry
# - RBAC per progetti
# - Garbage collection
# - Audit log
# - OIDC authentication
# - Quota management per progetto
```

### Gestione Immagini

```bash
# Pulizia immagini
docker image prune -a              # rimuovi immagini non usate da container
docker image prune --filter "until=168h"  # immagini più vecchie di 7 giorni
docker system prune -a --volumes   # pulizia totale (ATTENZIONE!)

# Analizza dimensione layer
docker history myapp:latest --no-trunc
docker image inspect myapp:latest --format='{{.Size}}'

# Salva e carica (per ambienti air-gapped)
docker save myapp:latest | gzip > myapp-latest.tar.gz
docker load < myapp-latest.tar.gz

# Salva più immagini
docker save myapp:latest postgres:16 redis:7 | gzip > stack.tar.gz

# Copia tra registry
# regctl (strumento per copiare senza pull/push locale)
regctl image copy source-registry/myapp:1.0 dest-registry/myapp:1.0

# Crane (Google)
crane copy source-registry/myapp:1.0 dest-registry/myapp:1.0

# Skopeo (Red Hat)
skopeo copy docker://source/myapp:1.0 docker://dest/myapp:1.0
```

---

## Troubleshooting Avanzato

### Debugging Container

```bash
# Log con timestamp e filtro temporale
docker logs -t --since 10m container_name
docker logs -t --since "2024-04-01T10:00:00" --until "2024-04-01T11:00:00" container_name

# Entra in un container in esecuzione
docker exec -it container_name /bin/sh
docker exec -it -u root container_name /bin/bash  # come root

# Se il container non parte, esegui shell interattiva con l'immagine
docker run -it --entrypoint /bin/sh myimage

# Debug con immagine diversa (quando il container non ha shell)
# Usa un container di debug che condivide i namespace
docker run -it --rm \
    --pid container:target_container \
    --net container:target_container \
    nicolaka/netshoot bash

# Ispeziona stato completo
docker inspect container_name
docker inspect container_name --format='{{json .State}}' | jq .
docker inspect container_name --format='{{json .NetworkSettings.Networks}}' | jq .

# Risorse utilizzate in tempo reale
docker stats container_name
docker stats --no-stream --format \
    "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}\t{{.PIDs}}"

# Processi nel container (visti dall'host)
docker top container_name

# Differenze dal filesystem dell'immagine
docker diff container_name
# C /tmp        ← changed
# A /tmp/data   ← added
# D /etc/motd   ← deleted

# Copia file da/verso container
docker cp container_name:/app/log.txt ./log.txt
docker cp ./config.yml container_name:/app/config.yml

# Esporta filesystem del container come tar
docker export container_name > container-fs.tar
```

### Networking Debug

```bash
# Verifica rete del container
docker exec container_name ip addr
docker exec container_name cat /etc/resolv.conf
docker exec container_name cat /etc/hosts

# Test DNS
docker exec container_name nslookup other-container

# Test connettività
docker exec container_name wget -qO- http://other-container:8080/health

# Debug con container di rete (netshoot = swiss army knife per networking)
docker run --rm -it --network container:target_container \
    nicolaka/netshoot
# Dentro netshoot:
# tcpdump -i eth0 port 80
# ss -tlnp
# curl -v http://localhost:8080
# dig +short other-service

# Ispeziona regole iptables create da Docker
sudo iptables -t nat -L -n -v | grep -i docker
sudo iptables -L DOCKER -n -v
sudo iptables -t nat -L DOCKER -n -v

# Ispeziona bridge
brctl show
# bridge name     bridge id               STP enabled     interfaces
# br-abc123       8000.024211111111       no              veth1234567
#                                                         veth8901234

# Cattura pacchetti su veth pair dall'host
PID=$(docker inspect -f '{{.State.Pid}}' container_name)
VETH=$(ip link | grep -A1 "if$(nsenter -t $PID -n cat /sys/class/net/eth0/iflink)" | head -1 | awk '{print $2}' | tr -d ':@')
tcpdump -i $VETH -n port 80
```

### Performance Debug

```bash
# Statistiche dettagliate con formattazione
docker stats --no-stream --format \
    "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}\t{{.PIDs}}"

# Output:
# NAME          CPU %   MEM USAGE / LIMIT     NET I/O           BLOCK I/O         PIDS
# myapp-web     2.34%   245.2MiB / 512MiB     1.23GB / 567MB    12.3MB / 4.56MB   42
# myapp-db      5.12%   890.3MiB / 1GiB       234MB / 1.23GB    567MB / 2.34GB    15

# cgroup v2 info diretta
CONTAINER_ID=$(docker inspect -f '{{.Id}}' container_name)
cat /sys/fs/cgroup/system.slice/docker-${CONTAINER_ID}.scope/memory.current
cat /sys/fs/cgroup/system.slice/docker-${CONTAINER_ID}.scope/cpu.stat

# Strace nel container (richiede SYS_PTRACE capability)
docker run --cap-add SYS_PTRACE myapp
docker exec container_name strace -p 1 -f -e trace=network -c
# Output: tabella delle syscall con conteggi e tempi

# nsenter per debug dal host (entra nei namespace del container)
PID=$(docker inspect -f '{{.State.Pid}}' container_name)
nsenter -t $PID -n ss -tlnp        # rete del container visto dall'host
nsenter -t $PID -n ip addr          # interfacce di rete
nsenter -t $PID -m ls /app          # filesystem del container
nsenter -t $PID -p ps aux           # processi del container

# Profiling CPU con perf dall'host
PID=$(docker inspect -f '{{.State.Pid}}' container_name)
perf top -p $PID
perf record -p $PID -g -- sleep 30
perf report
```

### Troubleshooting Comune

#### Container si riavvia continuamente (CrashLoopBackOff)

**Sintomi**: `docker ps` mostra il container che si riavvia ripetutamente.

**Causa**: L'applicazione crasha all'avvio — dipendenza mancante, errore di configurazione, porta già in uso, o risorse insufficienti.

**Soluzione**:
```bash
# Controlla i log
docker logs --tail 50 container_name

# Esegui il container in modo interattivo per debug
docker run -it --entrypoint /bin/sh myimage

# Verifica l'exit code
docker inspect container_name --format='{{.State.ExitCode}}'
# 137 = OOM killed, 1 = errore applicativo, 126 = permission denied

# Se OOM killed:
docker inspect container_name --format='{{.State.OOMKilled}}'
# true → aumenta il memory limit
```

#### Container non riesce a connettersi ad altri container

**Sintomi**: "connection refused" o "name resolution failed".

**Causa**: Container su reti diverse, DNS non configurato, o servizio di destinazione non pronto.

**Soluzione**:
```bash
# Verifica che siano sulla stessa rete
docker inspect container1 --format='{{json .NetworkSettings.Networks}}' | jq 'keys'
docker inspect container2 --format='{{json .NetworkSettings.Networks}}' | jq 'keys'

# Test DNS
docker exec container1 nslookup container2

# Usa depends_on con condition: service_healthy in Compose
```

#### Spazio disco esaurito da Docker

**Sintomi**: `No space left on device` durante build o pull.

**Causa**: Accumulo di immagini, container fermati, volumi e build cache.

**Soluzione**:
```bash
# Analisi utilizzo dettagliata
docker system df
docker system df -v

# Output:
# TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
# Images          47        12        8.315GB   5.231GB (62%)
# Containers      15        5         1.234GB   987.6MB (80%)
# Local Volumes   23        10        4.567GB   2.345GB (51%)
# Build Cache     150       0         3.456GB   3.456GB (100%)

# Pulizia selettiva
docker container prune         # container fermati
docker image prune -a          # immagini non usate
docker volume prune            # volumi orfani
docker builder prune           # build cache
docker builder prune --all     # TUTTA la build cache

# Pulizia aggressiva (ATTENZIONE: rimuove tutto il non-usato)
docker system prune -a --volumes

# Configura garbage collection automatica
# /etc/docker/daemon.json
# {
#   "builder": {
#     "gc": {
#       "enabled": true,
#       "defaultKeepStorage": "20GB",
#       "policy": [
#         { "keepBytes": 10737418240, "filter": ["unused-for=168h"] },
#         { "keepBytes": 21474836480 }
#       ]
#     }
#   }
# }
```

#### Build lento: cache non funziona

**Sintomi**: Il build ricostruisce layer che non sono cambiati.

**Causa**: Ordine istruzioni errato nel Dockerfile, build context troppo grande, o cache invalidata.

**Soluzione**:
```bash
# Verifica dimensione build context
docker build --no-cache --progress=plain . 2>&1 | head -5
# => [internal] load build context
# => => transferring context: 234.5MB  ← troppo grande!

# Crea .dockerignore (vedi sezione dedicata)

# Ordine corretto delle istruzioni:
# 1. FROM
# 2. Istruzioni che cambiano raramente (apt install, ecc)
# 3. COPY dependency files (package.json, go.mod, requirements.txt)
# 4. RUN install dependencies
# 5. COPY source code (cambia spesso → ultimo)
# 6. RUN build
# 7. CMD/ENTRYPOINT
```

---

## Overlay2 Storage Driver: Internals e Tuning

Overlay2 è lo storage driver predefinito di Docker su tutti i sistemi Linux moderni. Comprenderne i meccanismi interni è fondamentale per ottimizzare le performance e diagnosticare problemi di I/O.

### Architettura OverlayFS nel Kernel

OverlayFS opera sovrappponendo più directory (layer) per presentare una vista unificata al processo nel container. Il kernel gestisce quattro directory per ogni mount overlay:

```
┌──────────────────────────────────────────────────────────┐
│                    merged (vista unificata)                │
│   Il container vede questo come il suo root filesystem    │
├──────────────────────────────────────────────────────────┤
│                    upperdir (layer scrivibile)             │
│   Tutte le modifiche runtime vengono scritte qui          │
│   Corrisponde al thin R/W layer del container             │
├──────────────────────────────────────────────────────────┤
│                    workdir (directory di lavoro)            │
│   Usata dal kernel per operazioni atomiche copy-up        │
│   NON contiene dati visibili — solo stato temporaneo      │
├──────────────────────────────────────────────────────────┤
│                    lowerdir (layer read-only)              │
│   Può essere una catena di directory separate da ":"       │
│   lowerdir=layer5:layer4:layer3:layer2:layer1             │
│   Corrispondono ai layer dell'immagine Docker             │
└──────────────────────────────────────────────────────────┘
```

### Meccanismo Copy-on-Write Dettagliato

```bash
# Quando un processo nel container legge un file:
# 1. Il kernel cerca nel upperdir (layer R/W)
# 2. Se non trovato, cerca nella catena lowerdir (dall'alto verso il basso)
# 3. Il primo match viene servito — i layer superiori mascherano quelli inferiori
# 4. I risultati vengono cachati per accelerare le ricerche successive

# Quando un processo nel container scrive un file esistente:
# 1. Il kernel esegue un'operazione "copy_up"
# 2. Il file viene COPIATO dal lowerdir al upperdir
# 3. La modifica viene applicata alla copia nel upperdir
# 4. Le letture successive trovano il file nel upperdir (mascherando l'originale)
# NOTA: la prima scrittura a un file grande ha un costo elevato (copia completa)

# Quando un file viene eliminato:
# 1. Il kernel crea un "whiteout file" nel upperdir
# 2. Il whiteout nasconde il file nel lowerdir senza eliminarlo
# 3. Il file originale resta nel layer dell'immagine (immutabile)

# Ispeziona i mount overlay attivi
mount | grep overlay
# overlay on /var/lib/docker/overlay2/.../merged type overlay
#   (rw,relatime,lowerdir=...,upperdir=...,workdir=...)

# Visualizza la dimensione del upperdir (modifiche del container)
du -sh /var/lib/docker/overlay2/<container-layer-id>/diff/
```

### Opzioni del Filesystem di Backing

La scelta e la configurazione del filesystem sottostante influiscono significativamente sulle performance di overlay2.

```bash
# ── ext4 ──────────────────────────────────────────
# Supporto nativo, stabile, ben testato
# Limiti: max 64TB filesystem, max ~4 miliardi di file
mkfs.ext4 -m 0 -T largefile4 /dev/sdb1
mount -o defaults,noatime,nodiratime /dev/sdb1 /var/lib/docker

# ── xfs ───────────────────────────────────────────
# Performance migliori per I/O parallelo e grandi volumi
# IMPORTANTE: d_type DEVE essere abilitato (ftype=1)
mkfs.xfs -n ftype=1 /dev/sdb1
mount -o defaults,noatime,nodiratime,logbufs=8,logbsize=256k /dev/sdb1 /var/lib/docker

# Verifica che ftype sia abilitato su xfs esistente
xfs_info /var/lib/docker | grep ftype
# ftype=1  ← OK
# ftype=0  ← PROBLEMA: overlay2 non funzionerà correttamente

# ── Confronto performance ─────────────────────────
# Operazione         │ ext4          │ xfs
# ────────────────────┼───────────────┼──────────────
# Lettura sequenziale │ ~2.3 GB/s    │ ~2.5 GB/s
# Scrittura random    │ ~180 MB/s    │ ~210 MB/s
# Creazione file      │ ~8000 file/s │ ~12000 file/s
# copy_up (overlay2)  │ ~300 MB/s    │ ~350 MB/s
# I/O parallelo       │ buono        │ eccellente
```

### Tuning Avanzato di Overlay2

```bash
# Opzioni overlay2 nel daemon Docker
# /etc/docker/daemon.json
{
    "storage-driver": "overlay2",
    "storage-opts": [
        "overlay2.size=20G"
    ]
}
# overlay2.size limita lo spazio scrivibile per container
# Richiede backing filesystem xfs con pquota

# Per xfs con project quota (necessario per overlay2.size):
mkfs.xfs -n ftype=1 /dev/sdb1
mount -o defaults,pquota /dev/sdb1 /var/lib/docker

# metacopy=on (kernel 4.19+): ottimizza copy_up
# Invece di copiare l'intero file, copia solo i metadati
# Il contenuto viene condiviso (copy-on-write a livello di dati)
# Attivazione:
mount -o remount,metacopy=on /var/lib/docker

# redirect_dir=on (kernel 4.10+): ottimizza rename di directory
# Senza redirect_dir, rinominare una directory in upperdir è O(n)
# Con redirect_dir, è O(1) usando un attributo xattr di redirect
# Attivazione:
mount -o remount,redirect_dir=on /var/lib/docker

# Verifica opzioni attive
cat /sys/module/overlay/parameters/metacopy
cat /sys/module/overlay/parameters/redirect_dir

# Monitoraggio spazio overlay2
docker system df -v
du -sh /var/lib/docker/overlay2/
# Identifica i layer più grandi
du -sh /var/lib/docker/overlay2/*/diff | sort -rh | head -20
```

### Pattern per Workload I/O Intensivi

```bash
# Regola fondamentale: MAI usare il writable layer per dati persistenti
# Il copy-on-write aggiunge overhead a ogni prima scrittura

# Pattern corretto per database:
docker run -v pgdata:/var/lib/postgresql/data postgres
# Il volume bypassa completamente overlay2

# Pattern corretto per log ad alto volume:
docker run --tmpfs /var/log/app:rw,size=500m myapp
# tmpfs è in RAM, zero overhead I/O su disco

# Pattern corretto per file temporanei:
docker run --tmpfs /tmp:rw,noexec,nosuid,size=200m myapp
# Evita copy_up per file temporanei
```

---

## Docker in Produzione: Pattern Operativi

### Problema del PID 1 e Gestione Segnali

In un container Docker, il processo specificato in `ENTRYPOINT`/`CMD` diventa PID 1. Nel kernel Linux, PID 1 ha un comportamento speciale: non riceve segnali che non ha esplicitamente gestito. Questo causa problemi con `docker stop` (SIGTERM).

```dockerfile
# PROBLEMA: la shell è PID 1, il segnale non raggiunge l'app
CMD node server.js
# Internamente: /bin/sh -c "node server.js"
# PID 1 = /bin/sh (non gestisce SIGTERM correttamente)
# PID 2 = node server.js (non riceve mai SIGTERM)
# docker stop → SIGTERM a PID 1 (sh) → sh non lo propaga → timeout → SIGKILL

# SOLUZIONE 1: form exec (JSON array)
CMD ["node", "server.js"]
# PID 1 = node server.js (riceve SIGTERM direttamente)

# SOLUZIONE 2: tini come init process
FROM node:20-alpine
RUN apk add --no-cache tini
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["node", "server.js"]
# PID 1 = tini (gestisce segnali correttamente e li propaga ai figli)
# PID 2 = node server.js (riceve SIGTERM da tini)

# SOLUZIONE 3: --init flag di Docker (usa tini integrato)
# docker run --init myapp
```

```bash
# STOPSIGNAL: cambia il segnale di stop (default SIGTERM)
# Alcune applicazioni preferiscono segnali diversi

# Dockerfile
# STOPSIGNAL SIGQUIT   # per nginx (graceful shutdown)
# STOPSIGNAL SIGINT    # per PostgreSQL

# Configura il timeout di grazia per docker stop
docker stop --time=30 container_name
# Aspetta 30 secondi di SIGTERM prima di inviare SIGKILL

# In Docker Compose
# services:
#   app:
#     stop_grace_period: 30s
#     stop_signal: SIGTERM
```

### Health Check Pattern Avanzati

```dockerfile
# Health check base — endpoint HTTP
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD wget -q --spider http://localhost:8080/health || exit 1

# Health check per applicazioni con startup lento
# start-period: ignora i fallimenti durante questo periodo
# start-interval (Docker 25+): intervallo ridotto durante lo startup
HEALTHCHECK --interval=30s --timeout=5s \
    --start-period=120s --start-interval=5s --retries=3 \
    CMD curl -fs http://localhost:8080/readyz || exit 1

# Health check per gRPC
HEALTHCHECK --interval=15s --timeout=3s --retries=5 \
    CMD grpc_health_probe -addr=:50051 || exit 1

# Health check per database PostgreSQL
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
    CMD pg_isready -U $POSTGRES_USER -d $POSTGRES_DB || exit 1

# Health check per Redis
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
    CMD redis-cli ping | grep PONG || exit 1

# Health check multi-condizione (script custom)
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD /app/healthcheck.sh || exit 1
```

```bash
# healthcheck.sh — script di health check completo
#!/bin/sh
set -e

# Controlla che l'applicazione risponda
curl -fs http://localhost:8080/health > /dev/null || exit 1

# Controlla connessione al database
pg_isready -h db -U app -d myapp -q || exit 1

# Controlla spazio disco disponibile
AVAIL=$(df /app/data | tail -1 | awk '{print $5}' | tr -d '%')
[ "$AVAIL" -lt 90 ] || exit 1

# Tutti i check passati
exit 0
```

### Restart Policy

```bash
# Policy disponibili:
# no           — non riavviare mai (default)
# on-failure   — riavvia solo su exit code != 0
# always       — riavvia sempre (anche dopo docker stop → riavvia al boot)
# unless-stopped — come always, ma non riavvia dopo docker stop

docker run -d --restart=unless-stopped myapp
docker run -d --restart=on-failure:5 myapp  # max 5 tentativi

# In Docker Compose
# services:
#   app:
#     restart: unless-stopped
#   worker:
#     restart: on-failure
#     deploy:
#       restart_policy:
#         condition: on-failure
#         delay: 5s
#         max_attempts: 10
#         window: 120s

# Verifica la policy attiva
docker inspect --format='{{.HostConfig.RestartPolicy.Name}}' container_name

# Contatore dei restart
docker inspect --format='{{.RestartCount}}' container_name
docker inspect --format='{{.State.StartedAt}}' container_name
```

### Blue-Green Deployment con Compose

```bash
# Pattern per zero-downtime deployment con Docker Compose

# 1. Deploy della nuova versione con nome diverso
VERSION=2.0.0 docker compose -p myapp-green up -d

# 2. Verifica che sia healthy
docker compose -p myapp-green ps
# Controlla che tutti i servizi siano healthy

# 3. Aggiorna il reverse proxy per puntare al nuovo stack
# (modifica la configurazione di nginx/traefik/caddy)

# 4. Rimuovi il vecchio stack
docker compose -p myapp-blue down

# Pattern alternativo: rolling update singolo servizio
docker compose up -d --no-deps --scale app=2 app
# Scala temporaneamente a 2 istanze, poi:
docker compose up -d --no-deps --scale app=1 app
```

### Logging Strutturato in Produzione

```bash
# Le applicazioni in container dovrebbero loggare in JSON su stdout/stderr
# Docker cattura stdout/stderr e li scrive secondo il log driver configurato

# Esempio output strutturato (app Node.js con pino):
# {"level":"info","time":1714500000,"msg":"Server started","port":8080}
# {"level":"error","time":1714500005,"msg":"DB connection failed","err":"timeout"}

# Filtra log JSON con jq direttamente
docker logs container_name 2>&1 | jq 'select(.level == "error")'

# Log label per identificazione in stack centralizzati
docker run -d \
    --log-opt labels=service,environment \
    --label service=api \
    --label environment=production \
    myapp
```

---

## Ottimizzazione Immagini: Distroless, Slim e Scratch

La scelta dell'immagine base ha un impatto diretto su dimensione, sicurezza e superficie d'attacco.

### Gerarchia delle Immagini Base

```
Più grande / più strumenti / più vulnerabilità
    ▲
    │  ubuntu:24.04          (~78 MB)  — bash, apt, coreutils, systemd-libs
    │  debian:bookworm-slim  (~80 MB)  — bash, apt, coreutils
    │  python:3.12-slim      (~150 MB) — Python + pip + bash
    │  node:20-alpine        (~180 MB) — Node.js + npm + sh
    │  alpine:3.19           (~5 MB)   — sh, apk, musl libc
    │  distroless/base       (~2 MB)   — glibc, ca-certs, tzdata
    │  distroless/static     (~1 MB)   — solo ca-certs, tzdata
    │  scratch               (0 B)     — letteralmente nulla
    ▼
Più piccola / zero strumenti / zero vulnerabilità note
```

### Immagini Distroless di Google

Le immagini distroless contengono solo l'applicazione e le sue dipendenze runtime. Non includono shell, package manager, o utility di sistema.

```dockerfile
# ── Distroless per Go (binario statico) ──────────
FROM golang:1.22-alpine AS builder
WORKDIR /src
COPY . .
RUN CGO_ENABLED=0 go build -ldflags="-w -s" -o /app ./cmd/server

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /app /app
USER nonroot:nonroot
ENTRYPOINT ["/app"]
# Immagine finale: ~3 MB (binario Go + ca-certs)
# Zero CVE note nell'immagine base

# ── Distroless per Java ──────────────────────────
FROM eclipse-temurin:21-jdk-alpine AS builder
WORKDIR /src
COPY . .
RUN ./gradlew bootJar

FROM gcr.io/distroless/java21-debian12:nonroot
COPY --from=builder /src/build/libs/app.jar /app.jar
USER nonroot:nonroot
ENTRYPOINT ["java", "-jar", "/app.jar"]

# ── Distroless per Python ────────────────────────
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/install -r requirements.txt
COPY . .

FROM gcr.io/distroless/python3-debian12:nonroot
COPY --from=builder /install /usr/local/lib/python3.12/site-packages
COPY --from=builder /app /app
WORKDIR /app
USER nonroot:nonroot
ENTRYPOINT ["python3", "main.py"]
```

### Immagine Scratch per Binari Statici

```dockerfile
# scratch è l'immagine vuota — zero byte, zero file
# Adatta SOLO per binari completamente statici (Go, Rust con musl)

FROM rust:1.78-alpine AS builder
RUN apk add --no-cache musl-dev
WORKDIR /src
COPY . .
RUN RUSTFLAGS='-C target-feature=+crt-static' \
    cargo build --release --target x86_64-unknown-linux-musl

FROM scratch
# Copia i certificati CA per HTTPS
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
# Copia il file passwd per utente non-root
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /src/target/x86_64-unknown-linux-musl/release/myapp /myapp
USER nobody
ENTRYPOINT ["/myapp"]
# Immagine finale: ~5 MB (solo il binario Rust statico + ca-certs)
```

### Confronto Vulnerabilità per Immagine Base

```bash
# Scan comparativo con Trivy
trivy image --severity CRITICAL,HIGH node:20          # ~30+ vulnerabilità
trivy image --severity CRITICAL,HIGH node:20-slim     # ~5-10 vulnerabilità
trivy image --severity CRITICAL,HIGH node:20-alpine   # ~1-3 vulnerabilità
trivy image --severity CRITICAL,HIGH gcr.io/distroless/nodejs20-debian12  # ~0 vulnerabilità

# La correlazione è chiara:
# più pacchetti installati = più superficie di attacco = più CVE
```

---

## Docker Content Trust e Firma delle Immagini

La firma crittografica delle immagini garantisce l'integrità e l'autenticità delle immagini container nella supply chain del software.

### Docker Content Trust (DCT) — Deprecato

Docker Content Trust utilizza Notary v1 per firmare e verificare le immagini. Docker ha annunciato il ritiro di DCT a partire da settembre 2025, con rimozione completa prevista per marzo 2028.

```bash
# Abilitazione DCT (ancora funzionante ma deprecato)
export DOCKER_CONTENT_TRUST=1

# Con DCT abilitato, docker pull/push verifica/appone firme
docker pull myregistry/myapp:1.0.0
# Se l'immagine non è firmata, il pull fallisce

# Firma durante il push
docker push myregistry/myapp:1.0.0
# Richiede una chiave di firma (delegation key)

# NOTA: Docker raccomanda la migrazione a Sigstore o Notation
```

### Sigstore / Cosign — Standard Moderno

Cosign (parte del progetto Sigstore) è lo standard emergente per la firma keyless di artefatti OCI. Usa certificati effimeri legati all'identità OIDC del firmatario.

```bash
# Installazione cosign
curl -sSfL https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64 \
    -o /usr/local/bin/cosign && chmod +x /usr/local/bin/cosign

# Firma keyless (usa OIDC — apre browser per autenticazione)
cosign sign ghcr.io/myorg/myapp:1.0.0

# Firma con chiave locale
cosign generate-key-pair
cosign sign --key cosign.key ghcr.io/myorg/myapp:1.0.0

# Verifica firma
cosign verify --key cosign.pub ghcr.io/myorg/myapp:1.0.0

# Verifica keyless (verifica il certificato OIDC)
cosign verify \
    --certificate-identity=user@example.com \
    --certificate-oidc-issuer=https://accounts.google.com \
    ghcr.io/myorg/myapp:1.0.0

# Allega attestazione SBOM all'immagine
cosign attest --predicate sbom.json --type spdxjson \
    ghcr.io/myorg/myapp:1.0.0

# La firma viene salvata come artefatto OCI nello stesso registry
# Non modifica l'immagine originale — è un artefatto collegato
```

### Notation (Notary v2)

Notation è l'implementazione del Notary Project v2, progettata per la firma di artefatti OCI con supporto per catene di approvazione multiple.

```bash
# Installazione notation
curl -sSfL https://github.com/notaryproject/notation/releases/latest/download/notation_linux_amd64.tar.gz | \
    tar xz -C /usr/local/bin notation

# Genera chiave di firma
notation cert generate-test --default "myorg.io"

# Firma un'immagine
notation sign ghcr.io/myorg/myapp:1.0.0

# Verifica firma
notation verify ghcr.io/myorg/myapp:1.0.0

# Vantaggi di Notation rispetto a DCT:
# - Supporto per firme multiple (catene di approvazione)
# - Aderenza agli standard OCI (portabilità tra registry)
# - Integrazione con Azure ACR, AWS ECR, GCP Artifact Registry
# - Plugin architecture per HSM e KMS
```

---

## Docker Bench for Security e CIS Benchmark

Docker Bench for Security è uno script open source che verifica l'installazione Docker contro le raccomandazioni del CIS (Center for Internet Security) Docker Benchmark v1.6.0.

### Esecuzione dell'Audit

```bash
# Metodo 1: esecuzione come container (raccomandato)
docker run --rm --net host --pid host --userns host --cap-add audit_control \
    -e DOCKER_CONTENT_TRUST=$DOCKER_CONTENT_TRUST \
    -v /var/lib:/var/lib:ro \
    -v /var/run/docker.sock:/var/run/docker.sock:ro \
    -v /usr/lib/systemd:/usr/lib/systemd:ro \
    -v /etc:/etc:ro \
    --label docker_bench_security \
    docker/docker-bench-security

# Metodo 2: esecuzione diretta dallo script
git clone https://github.com/docker/docker-bench-security.git
cd docker-bench-security
sudo sh docker-bench-security.sh

# Output con formato JSON (per integrazione con SIEM)
sudo sh docker-bench-security.sh -l /tmp/bench.log -j

# Esegui solo categorie specifiche
sudo sh docker-bench-security.sh -c container_images
sudo sh docker-bench-security.sh -c docker_daemon_configuration
```

### Categorie CIS Benchmark

L'audit copre 7 categorie con oltre 100 controlli individuali:

```
Categoria                          │ Controlli │ Esempi
───────────────────────────────────┼───────────┼──────────────────────────────────
1. Host Configuration              │ ~20       │ Audit logging, filesystem separato
                                   │           │ per /var/lib/docker, kernel hardening
2. Docker Daemon Configuration     │ ~15       │ TLS su socket TCP, user namespaces,
                                   │           │ live restore, logging driver
3. Docker Daemon Config Files      │ ~15       │ Permessi su docker.sock, daemon.json,
                                   │           │ certificati TLS, directory chiavi
4. Container Images & Dockerfiles  │ ~10       │ Utente non-root, HEALTHCHECK,
                                   │           │ COPY vs ADD, istruzioni sicure
5. Container Runtime               │ ~30       │ AppArmor, SELinux, capabilities,
                                   │           │ read-only fs, PID limit, no-new-priv
6. Docker Security Operations      │ ~5        │ Vulnerability scanning, secret mgmt,
                                   │           │ content trust, immagini aggiornate
7. Docker Swarm Configuration      │ ~10       │ Swarm mode, autolock, rotazione
                                   │           │ certificati, rete overlay cifrata
```

### Interpretazione dell'Output

```
[PASS] 1.1  - Ensure a separate partition for containers has been created
[WARN] 1.2  - Ensure only trusted users are allowed to control Docker daemon
[INFO] 2.1  - Run the Docker daemon as a non-root user, if possible
[PASS] 2.2  - Ensure network traffic is restricted between containers on the default bridge
[WARN] 4.1  - Ensure that a user for the container has been created
[PASS] 5.1  - Ensure that, if applicable, an AppArmor Profile is enabled

# [PASS]  = il sistema è conforme alla raccomandazione
# [WARN]  = non conforme, azione di remediation consigliata
# [INFO]  = informazione, valutazione manuale necessaria
# [NOTE]  = controllo non applicabile o skippato
```

### Remediation dei Problemi Comuni

```bash
# WARN 2.1: Restrict network traffic between containers
# Remediation: disabilita inter-container communication di default
# /etc/docker/daemon.json
# { "icc": false }

# WARN 2.8: Enable user namespace support
# Remediation:
# /etc/docker/daemon.json
# { "userns-remap": "default" }

# WARN 4.1: Ensure a user for the container has been created
# Remediation nel Dockerfile:
# RUN useradd -r -s /bin/false appuser
# USER appuser

# WARN 5.12: Ensure mount propagation mode is not shared
# Remediation:
# Non usare --mount propagation=shared a meno che strettamente necessario

# WARN 5.25: Ensure the container is restricted from acquiring additional privileges
# Remediation:
# docker run --security-opt no-new-privileges myapp

# Esegui il benchmark periodicamente (suggerito: settimanale in produzione)
# Integra in CI/CD per nuove configurazioni di deployment
```

---

## Gestione dei Secrets in Produzione

I segreti (password, chiavi API, certificati TLS, token) non devono mai essere inseriti in immagini Docker, variabili d'ambiente visibili, o repository di codice.

### Docker Swarm Secrets

Docker Swarm include un sistema di secrets management nativo. I segreti sono criptati nel Raft log del cluster e iniettati nei container come file in `/run/secrets/`.

```bash
# Crea un segreto dal contenuto di un file
echo "SuperSecretPassword123!" | docker secret create db_password -

# Crea un segreto da file
docker secret create tls_cert ./server.crt
docker secret create tls_key ./server.key

# Lista segreti (il contenuto non è mai visibile)
docker secret ls
# ID                          NAME          CREATED
# abc123def456                db_password   2 hours ago

# Ispeziona metadati (mai il contenuto)
docker secret inspect db_password

# Usa un segreto in un servizio Swarm
docker service create \
    --name api \
    --secret db_password \
    --secret tls_cert \
    --secret tls_key \
    myapp:latest
# Il segreto è disponibile nel container come file:
# /run/secrets/db_password
# /run/secrets/tls_cert
# /run/secrets/tls_key

# Nell'applicazione, leggi il segreto dal file:
# password = open("/run/secrets/db_password").read().strip()
```

### Secrets in Docker Compose

```yaml
# docker-compose.yml con secrets
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password

  app:
    image: myapp:latest
    secrets:
      - db_password
      - source: api_key
        target: /app/config/api_key
        uid: '1000'
        gid: '1000'
        mode: 0400   # solo lettura per il proprietario

secrets:
  db_password:
    file: ./secrets/db_password.txt    # da file locale

  api_key:
    environment: "API_KEY"             # da variabile d'ambiente (Compose v2.23+)
```

### Integrazione con Secret Manager Esterni

```bash
# ── HashiCorp Vault ───────────────────────────────
# Pattern: init container che recupera segreti da Vault
# e li scrive in un volume condiviso

# docker-compose.yml
# services:
#   vault-agent:
#     image: hashicorp/vault
#     command: agent -config=/vault/config.hcl
#     volumes:
#       - secrets-vol:/vault/secrets
#
#   app:
#     image: myapp:latest
#     volumes:
#       - secrets-vol:/run/secrets:ro
#     depends_on:
#       vault-agent:
#         condition: service_started
#
# volumes:
#   secrets-vol:

# ── AWS Secrets Manager ──────────────────────────
# Pattern: l'applicazione recupera i segreti all'avvio
# usando l'SDK AWS e le credenziali IAM role

# entrypoint.sh
#!/bin/sh
# Recupera il segreto da AWS Secrets Manager
export DB_PASSWORD=$(aws secretsmanager get-secret-value \
    --secret-id prod/db/password \
    --query SecretString --output text)
exec "$@"

# Dockerfile
# ENTRYPOINT ["/entrypoint.sh"]
# CMD ["node", "server.js"]

# ── Rotazione dei Segreti ────────────────────────
# Pattern per rotazione zero-downtime:
# 1. Crea il nuovo segreto nel secret manager
# 2. Aggiorna la configurazione del servizio
# 3. Rolling update dei container (leggono il nuovo segreto)
# 4. Revoca il vecchio segreto dopo conferma

docker service update \
    --secret-rm old_db_password \
    --secret-add new_db_password \
    api
```

### Anti-Pattern da Evitare

```bash
# MAI: segreti nelle variabili d'ambiente (visibili con docker inspect)
docker run -e DB_PASSWORD=secret123 myapp
docker inspect container_name | grep DB_PASSWORD
# "DB_PASSWORD=secret123"  ← visibile a chiunque acceda al daemon

# MAI: segreti nel Dockerfile (salvati nei layer per sempre)
ENV API_KEY=sk-1234567890
# docker history mostra il segreto anche se rimosso in un layer successivo

# MAI: segreti nel build argument senza secret mount
docker build --build-arg API_KEY=secret .
# L'ARG appare in docker history

# CORRETTO: usa BuildKit secret mount durante il build
docker build --secret id=api_key,src=./api_key.txt .
# E nel Dockerfile:
# RUN --mount=type=secret,id=api_key \
#     API_KEY=$(cat /run/secrets/api_key) npm run build
```

---

## Docker Swarm vs Alternative di Orchestrazione

### Confronto Docker Swarm vs Kubernetes

| Caratteristica | Docker Swarm | Kubernetes |
|---------------|-------------|------------|
| **Setup** | `docker swarm init` (1 comando) | 3+ nodi control plane, etcd, addons |
| **Curva di apprendimento** | Bassa (estensione naturale di Docker) | Alta (concetti e API propri) |
| **Scaling** | Fino a ~1000 nodi | Fino a ~5000 nodi |
| **Networking** | Overlay integrato, semplice | CNI plugin, Network Policies, service mesh |
| **Secrets** | Nativi, criptati nel Raft log | Secrets (base64), encryption at rest opzionale |
| **Rolling update** | Integrato | Integrato con più opzioni |
| **Autoscaling** | No (solo scale manuale) | HPA, VPA, Cluster Autoscaler |
| **Ecosistema** | Limitato | Enorme (Helm, Operators, CRDs) |
| **Multi-tenancy** | Limitata | Namespace, RBAC, Network Policies |
| **Monitoraggio** | Docker stats, soluzioni esterne | Prometheus, metriche API native |
| **Manutenzione** | Minima | Significativa (upgrade, etcd backup) |

### Quando Swarm è Ancora Appropriato

```bash
# Swarm è una scelta valida quando:
# - Team piccolo (1-5 persone)
# - Infrastruttura semplice (<100 container)
# - Budget limitato per la gestione dell'orchestratore
# - Stack già basato su Docker Compose (transizione naturale)
# - Nessuna necessità di autoscaling o multi-tenancy avanzata

# Swarm mode: inizializzazione
docker swarm init --advertise-addr 192.168.1.10

# Aggiungi worker
docker swarm join-token worker
# Output: docker swarm join --token SWMTKN-xxx 192.168.1.10:2377

# Deploy di uno stack (usa lo stesso docker-compose.yml!)
docker stack deploy -c docker-compose.yml myapp

# Scala un servizio
docker service scale myapp_api=5

# Rolling update
docker service update --image myapp:2.0.0 myapp_api

# Drain di un nodo per manutenzione
docker node update --availability drain node-02

# Autolock (cripta le chiavi TLS del cluster a riposo)
docker swarm update --autolock=true
```

### Alternative Leggere: Nomad

HashiCorp Nomad è un orchestratore più semplice di Kubernetes che supporta container Docker, binari nativi, Java, e altri workload.

```bash
# Confronto rapido
# Nomad:    singolo binario, multi-workload, semplice
# Kubernetes: ecosistema complesso, container-first, standard de facto
# Swarm:    integrato in Docker, transizione da Compose, feature limitate

# Nomad supporta Docker nativamente:
# job "api" {
#   group "web" {
#     task "server" {
#       driver = "docker"
#       config {
#         image = "myapp:latest"
#         ports = ["http"]
#       }
#     }
#   }
# }
```

---

## Standard OCI (Open Container Initiative)

L'OCI (Open Container Initiative) definisce gli standard aperti per il formato delle immagini container, il runtime dei container, e la distribuzione delle immagini. Docker è conforme a tutti gli standard OCI.

### OCI Image Specification

Definisce il formato con cui le immagini container vengono costruite, distribuite e archiviate.

```bash
# Un'immagine OCI è composta da:
# 1. Image Manifest — descrive i layer e la configurazione
# 2. Image Index (opzionale) — manifest multi-piattaforma
# 3. Layer — filesystem delta compressi (tar+gzip o tar+zstd)
# 4. Image Configuration — metadati (env, cmd, user, ecc.)

# Ispeziona il manifest OCI di un'immagine
docker manifest inspect nginx:alpine
# {
#   "schemaVersion": 2,
#   "mediaType": "application/vnd.oci.image.manifest.v1+json",
#   "config": { "mediaType": "application/vnd.oci.image.config.v1+json", ... },
#   "layers": [
#     { "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip", ... },
#     ...
#   ]
# }

# Image Index per immagini multi-piattaforma
docker manifest inspect --verbose nginx:alpine
# Mostra i manifest per ogni piattaforma:
# linux/amd64, linux/arm64, linux/arm/v7, ecc.

# Ogni piattaforma ha il proprio set di layer
# docker pull seleziona automaticamente la piattaforma corretta
```

### OCI Runtime Specification

Definisce come un container viene configurato, eseguito e gestito a livello di runtime. Docker usa `runc` come implementazione di riferimento.

```bash
# Genera l'OCI runtime bundle di un container
mkdir -p bundle/rootfs
docker export $(docker create alpine) | tar -C bundle/rootfs -xf -

# Genera la spec OCI (config.json)
cd bundle
runc spec

# config.json contiene:
# - root: path al rootfs e se è read-only
# - process: comando, argomenti, env, cwd, user
# - mounts: bind mount, tmpfs, proc, sysfs
# - linux: namespaces, cgroups, seccomp, capabilities
# - hooks: prestart, poststart, poststop

# Esegui il container con runc direttamente (senza Docker)
runc create mycontainer
runc start mycontainer
runc list
runc delete mycontainer

# Alternative a runc conformi all'OCI Runtime Spec:
# crun     — implementazione in C, più veloce di runc
# youki    — implementazione in Rust
# gVisor   — sandbox con kernel userspace (runsc)
# Kata     — micro-VM per isolamento hardware
```

### OCI Distribution Specification

Definisce l'API HTTP per il push e pull di immagini OCI dai registry. Tutti i registry moderni (Docker Hub, GHCR, ECR, ACR, Harbor) implementano questa specifica.

```bash
# L'API Distribution è un'API REST HTTP standard:
# GET  /v2/                          — verifica supporto API v2
# GET  /v2/<name>/manifests/<ref>    — scarica manifest
# GET  /v2/<name>/blobs/<digest>     — scarica un layer (blob)
# PUT  /v2/<name>/manifests/<ref>    — carica manifest
# POST /v2/<name>/blobs/uploads/     — inizia upload di un layer
# PATCH /v2/<name>/blobs/uploads/<id> — carica chunk del layer
# PUT  /v2/<name>/blobs/uploads/<id>  — completa upload del layer

# Esempio: recupera il manifest di un'immagine direttamente via HTTP
curl -s -H "Accept: application/vnd.oci.image.manifest.v1+json" \
    https://registry-1.docker.io/v2/library/alpine/manifests/3.19

# OCI Artifacts: il format OCI non è limitato a immagini container
# Può distribuire qualsiasi artefatto: SBOM, firme, helm chart, WASM
# cosign salva le firme come artefatti OCI nello stesso registry
# oras (OCI Registry As Storage) è il tool generico per push/pull artefatti
```

### OCI e il Futuro dei Container

```bash
# La conformità OCI garantisce:
# 1. Portabilità: immagini costruite con Docker funzionano con Podman, containerd, CRI-O
# 2. Interoperabilità: registry diversi parlano lo stesso protocollo
# 3. Indipendenza dal vendor: non sei locked-in a Docker
# 4. Ecosistema aperto: tool di terze parti (Trivy, cosign, crane) funzionano ovunque

# Verifica la conformità OCI di un'immagine
crane validate ghcr.io/myorg/myapp:latest
skopeo inspect --raw docker://ghcr.io/myorg/myapp:latest | jq .mediaType
# "application/vnd.oci.image.manifest.v1+json" ← OCI compliant

# Conversione Docker manifest → OCI manifest
# I tool moderni (buildx, buildah, podman) producono manifest OCI nativamente
```

---

## Esercizi Pratici

### Esercizio 1: Multi-Stage Build Ottimizzato

Dato un progetto Go con la struttura:
```
myapp/
├── cmd/server/main.go
├── go.mod
├── go.sum
└── internal/
    └── handler.go
```

Crea un Dockerfile multi-stage che:
1. Compila l'applicazione
2. Usa `scratch` come base finale
3. Include health check
4. Non esegue come root (hint: copia `/etc/passwd` dal builder)
5. L'immagine finale deve essere < 20 MB

### Esercizio 2: Stack Docker Compose con Health Dependency

Crea un `docker-compose.yml` con:
- PostgreSQL con healthcheck `pg_isready`
- Redis con healthcheck `redis-cli ping`
- Servizio migrations che esegue e esce (`service_completed_successfully`)
- App che parte solo dopo che DB è healthy e migrations hanno completato
- Nginx come reverse proxy che parte dopo l'app
- Rete interna per backend, rete bridge per frontend
- Resource limits su tutti i servizi

### Esercizio 3: Security Hardening

Prendi un container esistente e applica tutte le misure di sicurezza:
```bash
# Parti da:
docker run -d --name insecure myapp

# Trasformalo in:
docker run -d --name secure \
    --read-only \
    --tmpfs /tmp:... \
    --cap-drop ALL \
    --cap-add ... \
    --security-opt no-new-privileges \
    --security-opt seccomp=... \
    --memory ... \
    --pids-limit ... \
    --user ... \
    myapp
```

### Esercizio 4: Troubleshooting di Rete

Un container `web` non riesce a raggiungere un container `api`:
```bash
docker exec web curl http://api:3000/health
# curl: (6) Could not resolve host: api
```

Diagnostica e risolvi il problema usando:
1. `docker network inspect`
2. `docker exec ... nslookup`
3. `docker network connect`

---

## Domande e Risposte (Q&A)

**D: Qual è la differenza tra `CMD` e `ENTRYPOINT`?**

`ENTRYPOINT` definisce il comando base del container (non sovrascrivibile senza `--entrypoint`). `CMD` fornisce argomenti di default a `ENTRYPOINT`, oppure un comando completo se `ENTRYPOINT` non è definito. Best practice: usa `ENTRYPOINT` per il binario e `CMD` per gli argomenti di default.

```dockerfile
ENTRYPOINT ["python", "app.py"]
CMD ["--port", "8080"]
# docker run myapp                     → python app.py --port 8080
# docker run myapp --port 9090         → python app.py --port 9090
# docker run --entrypoint sh myapp     → sh
```

**D: Quando usare `COPY` vs `ADD`?**

Usa sempre `COPY` a meno che non serva specificamente una feature di `ADD`. `ADD` ha due feature in più: decompressione automatica di tar e supporto URL. Ma il supporto URL è deprecato e la decompressione automatica è spesso indesiderata. `COPY` è esplicito e prevedibile.

**D: Come gestire i segreti in Docker?**

Mai nel Dockerfile (layer), mai nelle variabili d'ambiente (visibili con `docker inspect`). Opzioni sicure:
1. Docker secrets (Swarm mode): `docker secret create`
2. BuildKit `--mount=type=secret` durante il build
3. File montati a runtime: `-v /host/secrets:/run/secrets:ro`
4. Tool di secrets management (Vault, AWS Secrets Manager)

**D: `docker stop` vs `docker kill`?**

`docker stop` invia SIGTERM, aspetta il timeout di grazia (default 10s), poi SIGKILL. `docker kill` invia SIGKILL immediatamente. Usa `docker stop` per shutdown pulito — l'applicazione ha tempo per chiudere connessioni e salvare stato.

**D: Come ridurre il tempo di build?**

1. Ottimizza `.dockerignore` (riduce build context)
2. Ordina istruzioni per cache (dipendenze prima, codice dopo)
3. Usa `--mount=type=cache` per cache di pacchetti
4. Usa BuildKit (parallellizza build)
5. Usa `--cache-from` per riutilizzare cache da registry
6. Multi-stage build (stage paralleli)

**D: Perché i log riempiono il disco?**

Il driver `json-file` di default non ha rotazione. Configura `max-size` e `max-file` nel daemon config o per container. Senza limiti, un container che logga molto riempirà il disco.

---

## Best Practices

1. **Una responsabilità per container**: Ogni container dovrebbe eseguire un singolo processo (web server, database, cache). Non creare container "monolitici" con più servizi.

2. **Immagini minimali**: Usa `alpine`, `slim`, o `distroless` come base. Meno software installato significa meno superficie di attacco e immagini più veloci da trasferire.

3. **Multi-stage build sempre**: Separa l'ambiente di build dall'ambiente di runtime. Il toolchain di compilazione non deve finire nell'immagine di produzione.

4. **Non eseguire come root**: Crea e usa un utente non-root nel Dockerfile. Usa `--cap-drop ALL` e aggiungi solo le capability necessarie. Abilita `no-new-privileges`.

5. **Usa .dockerignore**: Escludi `.git`, `node_modules`, file temporanei, e segreti dal build context. Un build context grande rallenta il build e rischia di includere dati sensibili.

6. **Tagga con versione semantica**: Non usare solo `latest`. Usa tag specifici (`1.2.3`) per riproducibilità. Il tag `latest` in produzione è un anti-pattern perché non è deterministico.

7. **Healthcheck sempre**: Definisci healthcheck nel Dockerfile e in Docker Compose. Senza healthcheck, Docker non sa se l'applicazione è veramente funzionante.

8. **Segreti fuori dalle immagini**: Non inserire password, chiavi API o certificati nelle immagini. Usa environment variables (con cautela), Docker secrets, o mount di file a runtime.

9. **Limita le risorse**: Imposta limiti di CPU e memoria con `deploy.resources.limits`. Un container senza limiti può consumare tutte le risorse dell'host e impattare gli altri container.

10. **Monitora i log**: Configura il logging driver con rotazione (`json-file` con `max-size` e `max-file`). Senza rotazione, i log possono riempire il disco.

11. **Scan le immagini**: Integra vulnerability scanning (Trivy, Scout, Grype) nel CI/CD. Non deployare immagini con vulnerabilità CRITICAL.

12. **Pin le versioni base**: Usa tag specifici (`python:3.12.3-slim`, non `python:3`). Rebuild periodicamente per includere security patch dell'immagine base.

13. **Configura user namespaces**: Abilita `userns-remap` nel daemon o usa rootless Docker per limitare l'impatto di un'eventuale container escape.

14. **Log in formato strutturato**: Configura le applicazioni per loggare in JSON. Facilita l'integrazione con stack di logging (ELK, Loki).

15. **Backup dei volumi**: I named volume non sono persistenti per definizione — il `docker volume prune` li rimuove. Implementa backup regolari dei volumi che contengono dati.

---

## Riferimenti

- **Docker Documentation**: https://docs.docker.com/
- **Dockerfile Reference**: https://docs.docker.com/engine/reference/builder/
- **Docker Compose Specification**: https://docs.docker.com/compose/compose-file/
- **Docker Compose Watch**: https://docs.docker.com/compose/how-tos/file-watch/
- **Docker Bake**: https://docs.docker.com/build/bake/
- **Docker Security**: https://docs.docker.com/engine/security/
- **BuildKit Documentation**: https://docs.docker.com/build/buildkit/
- **Dockerfile Best Practices**: https://docs.docker.com/develop/develop-images/dockerfile_best-practices/
- **OverlayFS Kernel Docs**: https://docs.kernel.org/filesystems/overlayfs.html
- **OCI Image Spec**: https://github.com/opencontainers/image-spec
- **OCI Runtime Spec**: https://github.com/opencontainers/runtime-spec
- **OCI Distribution Spec**: https://github.com/opencontainers/distribution-spec
- **Container Security (Liz Rice)**: https://www.oreilly.com/library/view/container-security/9781492056690/
- **Distroless Images**: https://github.com/GoogleContainerTools/distroless
- **Harbor Registry**: https://goharbor.io/
- **Trivy Scanner**: https://aquasecurity.github.io/trivy/
- **Grype Scanner**: https://github.com/anchore/grype
- **Hadolint (Dockerfile linter)**: https://github.com/hadolint/hadolint
- **Sigstore / Cosign**: https://docs.sigstore.dev/
- **Notation (Notary v2)**: https://notaryproject.dev/
- **Docker Bench for Security**: https://github.com/docker/docker-bench-security
- **CIS Docker Benchmark**: https://www.cisecurity.org/benchmark/docker
- `man docker`, `man docker-compose`, `man dockerd`
