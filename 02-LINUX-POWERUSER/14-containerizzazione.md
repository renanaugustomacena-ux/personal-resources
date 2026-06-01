# Containerizzazione Linux — Guida Completa

> **Modulo 14** · **Aggiornamento:** 2026-05-22

## Idee guida
1. **Rootless containers default per security.** Docker rootless + Podman.
2. **Registry auth flow: Docker login → token-based.**
3. **CVE tracking template per image: trivy + grype.**
4. **Distroless > Alpine > Ubuntu per attack surface.**


## Indice

- [Fondamenti dei Container](#fondamenti-dei-container)
  - [Namespaces del Kernel](#namespaces-del-kernel)
  - [Control Groups (cgroups)](#control-groups-cgroups)
  - [Union Filesystem](#union-filesystem)
  - [Container vs VM — Differenze architetturali](#container-vs-vm--differenze-architetturali)
- [Docker: Fondamenti](#docker-fondamenti)
  - [Architettura Docker](#architettura-docker)
  - [Installazione e configurazione](#installazione-e-configurazione)
  - [Lifecycle dei container](#lifecycle-dei-container)
  - [Interazione con i container](#interazione-con-i-container)
  - [Pulizia e manutenzione](#pulizia-e-manutenzione)
- [Immagini e Dockerfile](#immagini-e-dockerfile)
  - [Gestione immagini](#gestione-immagini)
  - [Dockerfile — Istruzioni fondamentali](#dockerfile--istruzioni-fondamentali)
  - [Multi-stage build](#multi-stage-build)
  - [Layer caching — Ottimizzazione build](#layer-caching--ottimizzazione-build)
  - [.dockerignore](#dockerignore)
  - [Security scanning delle immagini](#security-scanning-delle-immagini)
  - [Build multi-piattaforma](#build-multi-piattaforma)
- [Docker Networking](#docker-networking)
  - [Driver di rete: bridge](#driver-di-rete-bridge)
  - [Driver di rete: host](#driver-di-rete-host)
  - [Driver di rete: overlay](#driver-di-rete-overlay)
  - [Driver di rete: macvlan](#driver-di-rete-macvlan)
  - [DNS resolution interna](#dns-resolution-interna)
  - [Port mapping — Meccanismo interno](#port-mapping--meccanismo-interno)
  - [Comandi di rete](#comandi-di-rete)
- [Docker Volumi e Storage](#docker-volumi-e-storage)
  - [Volume Docker (named volumes)](#volume-docker-named-volumes)
  - [Bind mounts](#bind-mounts)
  - [tmpfs mounts](#tmpfs-mounts)
  - [Storage drivers](#storage-drivers)
  - [Backup e restore dei volumi](#backup-e-restore-dei-volumi)
- [Docker Compose v2](#docker-compose-v2)
  - [Struttura del file Compose](#struttura-del-file-compose)
  - [Services, Networks, Volumes](#services-networks-volumes)
  - [depends_on e healthcheck](#depends_on-e-healthcheck)
  - [Profiles](#profiles)
  - [Extensions (x-)](#extensions-x-)
  - [Comandi Compose](#comandi-compose)
- [Docker Sicurezza](#docker-sicurezza)
  - [Container rootless](#container-rootless)
  - [Read-only filesystem](#read-only-filesystem)
  - [Capabilities dropping](#capabilities-dropping)
  - [Profili seccomp](#profili-seccomp)
  - [User namespaces](#user-namespaces)
  - [Secrets management](#secrets-management)
  - [Limitazione risorse](#limitazione-risorse)
- [Podman — Alternativa Rootless](#podman--alternativa-rootless)
  - [Architettura senza daemon](#architettura-senza-daemon)
  - [Concetto di Pod](#concetto-di-pod)
  - [Compatibilità con Docker](#compatibilità-con-docker)
  - [Integrazione systemd](#integrazione-systemd)
  - [Podman Compose e pod play kube](#podman-compose-e-pod-play-kube)
- [Gestione Immagini e Registry](#gestione-immagini-e-registry)
  - [Registry: Docker Hub, Harbor, Quay](#registry-docker-hub-harbor-quay)
  - [Image signing: cosign e Notary](#image-signing-cosign-e-notary)
  - [Vulnerability scanning: Trivy e Grype](#vulnerability-scanning-trivy-e-grype)
- [LXC/LXD — Container di Sistema](#lxclxd--container-di-sistema)
- [Buildah e Skopeo](#buildah-e-skopeo)
  - [Buildah — Build OCI senza daemon](#buildah--build-oci-senza-daemon)
  - [Skopeo — Gestione immagini tra registry](#skopeo--gestione-immagini-tra-registry)
- [Orchestrazione Container](#orchestrazione-container)
  - [Docker Swarm — Fondamenti](#docker-swarm--fondamenti)
  - [Kubernetes — Introduzione](#kubernetes--introduzione)
- [Monitoraggio Container](#monitoraggio-container)
  - [docker stats](#docker-stats)
  - [cAdvisor](#cadvisor)
  - [Metriche Prometheus](#metriche-prometheus)
- [Debugging Container](#debugging-container)
  - [docker exec e docker cp](#docker-exec-e-docker-cp)
  - [nsenter — Entrare nei namespace](#nsenter--entrare-nei-namespace)
  - [strace in container](#strace-in-container)
  - [Core dumps](#core-dumps)
- [systemd e Container](#systemd-e-container)
  - [Container come servizi systemd](#container-come-servizi-systemd)
  - [Quadlet — Integrazione nativa](#quadlet--integrazione-nativa)
- [Best Practices — Checklist Produzione](#best-practices--checklist-produzione)
- [Troubleshooting — Problemi Comuni](#troubleshooting--problemi-comuni)
- [Migrazione Docker → Podman](#migrazione-docker--podman)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)

---

## Fondamenti dei Container

I container sono la tecnologia di deployment dominante nel software moderno. A differenza delle VM, i container condividono il kernel dell'host, sono leggeri (MB, non GB), si avviano in secondi e permettono una densità molto superiore. La comprensione dei meccanismi kernel sottostanti è essenziale per debugging avanzato e per hardening.

Un container è, in ultima analisi, un processo (o gruppo di processi) isolato tramite tre primitive del kernel Linux:

1. **Namespaces** — isolamento della visibilità delle risorse
2. **Control Groups (cgroups)** — limitazione e accounting delle risorse
3. **Union Filesystem** — layered filesystem per immagini efficienti

### Namespaces del Kernel

I namespace sono il meccanismo con cui il kernel isola la visibilità delle risorse. Ogni container ha i propri namespace, e non può vedere le risorse appartenenti ad altri namespace. Linux supporta 8 tipi di namespace rilevanti per la containerizzazione:

#### PID Namespace

Isola l'albero dei processi. Il processo init del container ha PID 1 all'interno del namespace, ma un PID diverso (es. 48372) dal punto di vista dell'host.

```bash
# Creare un nuovo PID namespace manualmente
sudo unshare --pid --fork --mount-proc bash
# Dentro il nuovo namespace:
ps aux
# Vedrai solo bash (PID 1) e ps (PID 2)
# L'host continua a vedere tutti i processi

# Verificare il PID namespace di un container Docker
docker inspect --format '{{.State.Pid}}' web
# Es. output: 48372

# Dall'host, esaminare i namespace del processo
ls -la /proc/48372/ns/
# lrwxrwxrwx pid -> pid:[4026532684]

# Confrontare con il PID namespace dell'host
ls -la /proc/1/ns/pid
# lrwxrwxrwx pid -> pid:[4026531836]
# Numeri diversi → namespace diversi
```

#### Network Namespace (net)

Ogni container ha il proprio stack di rete: interfacce, tabella di routing, regole iptables, socket. Docker crea una coppia veth (virtual ethernet) per connettere il network namespace del container al bridge sull'host.

```bash
# Creare un network namespace manualmente
sudo ip netns add test_ns
sudo ip netns list

# Creare una coppia veth e connetterla
sudo ip link add veth0 type veth peer name veth1
sudo ip link set veth1 netns test_ns

# Configurare IP nel namespace
sudo ip netns exec test_ns ip addr add 10.0.0.2/24 dev veth1
sudo ip netns exec test_ns ip link set veth1 up
sudo ip netns exec test_ns ip link set lo up

# Eseguire comandi nel namespace di rete
sudo ip netns exec test_ns ping 10.0.0.2
sudo ip netns exec test_ns ss -tuln

# Pulire
sudo ip netns delete test_ns
```

#### Mount Namespace (mnt)

Isola la vista del filesystem. Il container vede solo il proprio root filesystem (dall'immagine) più eventuali mount espliciti (volumi, bind mount). Le modifiche ai mount point nel container non influenzano l'host.

```bash
# Creare un mount namespace
sudo unshare --mount bash
# Dentro: mount e umount non influenzano l'host

# Verificare i mount di un container
docker inspect --format '{{json .Mounts}}' web | jq .

# Esaminare i mount dal punto di vista dell'host
cat /proc/$(docker inspect --format '{{.State.Pid}}' web)/mounts
```

#### UTS Namespace

Isola hostname e domain name. Ogni container può avere il proprio hostname senza influenzare l'host.

```bash
# Il container ha il proprio hostname
docker run --rm --hostname mycontainer alpine hostname
# Output: mycontainer

# Creare un UTS namespace manualmente
sudo unshare --uts bash
hostname container-test  # Non cambia l'hostname dell'host
```

#### IPC Namespace

Isola le risorse IPC System V (shared memory, semafori, code di messaggi) e POSIX message queues. Impedisce a container diversi di interferire tramite IPC.

```bash
# Verificare l'isolamento IPC
docker run --rm alpine ipcs  # Nessuna risorsa IPC visibile

# Condividere IPC namespace tra container (raro, per legacy)
docker run -d --name ipc_provider --ipc=shareable alpine sleep 3600
docker run --rm --ipc=container:ipc_provider alpine ipcs
```

#### User Namespace

Mappa UID/GID del container a UID/GID diversi sull'host. Root (UID 0) nel container corrisponde a un utente non privilegiato sull'host. Fondamentale per i container rootless.

```bash
# Verificare il mapping utente (rootless Podman)
podman run --rm alpine cat /proc/self/uid_map
#          0       1000          1
#          1     100000      65536
# Traduzione: UID 0 nel container = UID 1000 sull'host
#             UID 1-65536 nel container = UID 100000-165536 sull'host

# Configurare user namespace remapping per Docker
# /etc/docker/daemon.json:
# {
#   "userns-remap": "default"
# }
# Docker creerà un utente "dockremap" e userà subordinate UID/GID
# da /etc/subuid e /etc/subgid
```

#### Cgroup Namespace

Isola la vista della gerarchia cgroup. Il container vede solo la propria porzione dell'albero cgroup, non quella dell'host o di altri container.

```bash
# Dal container, il cgroup root appare come /
docker run --rm alpine cat /proc/1/cgroup
# 0::/

# Dall'host, il container è in un sotto-cgroup specifico
cat /proc/$(docker inspect --format '{{.State.Pid}}' web)/cgroup
# 0::/system.slice/docker-<container_id>.scope
```

#### Time Namespace (Linux 5.6+)

Isola i clock `CLOCK_MONOTONIC` e `CLOCK_BOOTTIME`. Poco usato nei container, ma utile per testare software time-sensitive.

### Control Groups (cgroups)

I cgroups sono il meccanismo kernel per limitare, contabilizzare e isolare l'uso delle risorse (CPU, memoria, I/O disco, rete) da parte di gruppi di processi. Esistono due versioni:

- **cgroups v1**: gerarchia multipla, un albero per ogni controller (cpu, memory, blkio, etc.)
- **cgroups v2**: gerarchia unificata (un singolo albero), modello più pulito. Default in kernel moderni

```bash
# Verificare quale versione è in uso
stat -fc %T /sys/fs/cgroup/
# "cgroup2fs" → cgroups v2
# "tmpfs"     → cgroups v1

# Per cgroups v2, esaminare i controller disponibili
cat /sys/fs/cgroup/cgroup.controllers
# cpu io memory pids

# Esaminare i limiti di un container Docker (cgroups v2)
CONTAINER_PID=$(docker inspect --format '{{.State.Pid}}' web)
CGROUP_PATH=$(cat /proc/$CONTAINER_PID/cgroup | cut -d: -f3)

# Limiti memoria
cat /sys/fs/cgroup${CGROUP_PATH}/memory.max
cat /sys/fs/cgroup${CGROUP_PATH}/memory.current

# Limiti CPU
cat /sys/fs/cgroup${CGROUP_PATH}/cpu.max
# "100000 100000" → 100% di 1 CPU (quota/period in microsec)
# "50000 100000"  → 50% di 1 CPU

# Statistiche I/O
cat /sys/fs/cgroup${CGROUP_PATH}/io.stat
```

#### Limiti risorse con Docker e cgroups

```bash
# Limite memoria: 512MB hard limit, 256MB soft limit
docker run -d --memory=512m --memory-reservation=256m myapp

# Limite CPU: 1.5 core
docker run -d --cpus=1.5 myapp

# CPU shares (peso relativo, default 1024)
docker run -d --cpu-shares=512 myapp   # Peso dimezzato rispetto al default

# CPU pinning: usare solo core 0 e 1
docker run -d --cpuset-cpus="0,1" myapp

# Limite PID: massimo 100 processi
docker run -d --pids-limit=100 myapp

# Limite I/O: max 10MB/s in lettura dal device
docker run -d --device-read-bps /dev/sda:10mb myapp

# Limite I/O: max 1000 IOPS in scrittura
docker run -d --device-write-iops /dev/sda:1000 myapp

# OOM (Out Of Memory) — disabilitare il kill (sconsigliato)
docker run -d --oom-kill-disable myapp   # Il container congelarà invece di venire ucciso

# OOM score adjustment (-1000 a 1000, valori più alti = più probabile il kill)
docker run -d --oom-score-adj=-500 myapp
```

### Union Filesystem

Il filesystem union è il meccanismo che permette a Docker di costruire immagini a layer. Ogni istruzione del Dockerfile crea un nuovo layer read-only. Quando si avvia un container, Docker aggiunge un layer read-write (container layer) sopra i layer dell'immagine.

```
┌─────────────────────────┐
│   Container Layer (RW)  │  ← modifiche runtime
├─────────────────────────┤
│   Layer: CMD/EXPOSE     │  ← Dockerfile
├─────────────────────────┤
│   Layer: COPY app       │  ← Dockerfile
├─────────────────────────┤
│   Layer: RUN apt-get    │  ← Dockerfile
├─────────────────────────┤
│   Layer: base image     │  ← FROM ubuntu:22.04
└─────────────────────────┘
```

Il meccanismo **Copy-on-Write (CoW)** fa sì che un file venga copiato dal layer inferiore al container layer solo quando viene modificato. Letture avvengono direttamente dal layer inferiore.

```bash
# Esaminare i layer di un'immagine
docker history nginx:1.25
docker inspect nginx:1.25 | jq '.[0].RootFS.Layers'

# Confrontare layer tra due immagini (per capire cosa condividono)
docker inspect img1 | jq '.[0].RootFS.Layers' > /tmp/img1_layers
docker inspect img2 | jq '.[0].RootFS.Layers' > /tmp/img2_layers
diff /tmp/img1_layers /tmp/img2_layers

# Verificare lo storage driver in uso
docker info | grep "Storage Driver"
# Tipicamente: overlay2

# Dimensione dei layer di un container
docker inspect --format '{{.GraphDriver.Data}}' container_name
```

### Container vs VM — Differenze architetturali

```
         VM                          Container
┌─────────────────┐          ┌─────────────────┐
│   App A │ App B │          │  App A │  App B  │
├─────────┼───────┤          ├────────┼─────────┤
│  Bins   │ Bins  │          │  Bins  │  Bins   │
├─────────┼───────┤          ├────────┴─────────┤
│ Guest OS│GuestOS│          │  Container Engine │
├─────────┴───────┤          ├──────────────────┤
│   Hypervisor    │          │    Host OS        │
├─────────────────┤          ├──────────────────┤
│   Host OS       │          │    Hardware       │
├─────────────────┤          └──────────────────┘
│   Hardware      │
└─────────────────┘

VM: isolamento forte (kernel separato), overhead maggiore (~GB, minuti per boot)
Container: isolamento via namespace/cgroups (kernel condiviso), leggero (~MB, secondi per boot)
```

| Aspetto | VM | Container |
|---------|-----|-----------|
| Isolamento | Kernel separato | Namespace/cgroup |
| Dimensione | GB | MB |
| Boot | Minuti | Secondi |
| Overhead | Alto (hypervisor) | Minimo |
| Densità | Decine per host | Centinaia/migliaia per host |
| Portabilità | Formato immagine VM | Immagine OCI standard |
| Sicurezza | Forte (kernel separato) | Buona (kernel condiviso) |

---

## Docker: Fondamenti

### Architettura Docker

Docker usa un modello client-server:

```
┌──────────┐     REST API      ┌──────────────┐
│  docker   │ ───────────────► │  dockerd      │
│  (CLI)    │   (Unix socket)  │  (daemon)     │
└──────────┘                   └──────┬───────┘
                                      │
                              ┌───────▼───────┐
                              │  containerd    │
                              │  (runtime)     │
                              └───────┬───────┘
                                      │
                              ┌───────▼───────┐
                              │  runc          │
                              │  (OCI runtime) │
                              └───────────────┘
```

- **docker CLI**: interfaccia utente, invia comandi via Unix socket (`/var/run/docker.sock`)
- **dockerd**: daemon principale, gestisce immagini, reti, volumi
- **containerd**: runtime di alto livello, gestisce lifecycle dei container
- **runc**: runtime OCI di basso livello, crea effettivamente i container (namespace, cgroups, etc.)

### Installazione e configurazione

```bash
# Installazione (Ubuntu/Debian)
sudo apt update
sudo apt install docker.io
sudo systemctl enable --now docker
sudo usermod -aG docker $USER       # Permetti uso senza sudo (re-login necessario)

# Installazione da repository ufficiale Docker (versione più aggiornata)
sudo apt install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Configurazione daemon — /etc/docker/daemon.json
{
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "dns": ["8.8.8.8", "1.1.1.1"],
  "default-address-pools": [
    {"base": "172.20.0.0/16", "size": 24}
  ],
  "live-restore": true,
  "userland-proxy": false,
  "default-ulimits": {
    "nofile": { "Name": "nofile", "Hard": 65536, "Soft": 65536 }
  }
}

# Applicare le modifiche
sudo systemctl restart docker

# Verificare l'installazione
docker version
docker info
docker run hello-world
```

### Lifecycle dei container

```bash
# CONTAINER LIFECYCLE
docker run nginx                     # Scarica + crea + avvia
docker run -d nginx                  # Detached (background)
docker run -d --name web -p 8080:80 nginx  # Nome + port mapping
docker run -it ubuntu bash           # Interattivo con terminale

docker create --name web nginx       # Crea senza avviare
docker start web                     # Avvia container creato

docker ps                            # Container in esecuzione
docker ps -a                         # Tutti (inclusi fermi)
docker ps -q                         # Solo ID
docker ps --filter status=exited     # Filtro per stato
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

docker stop web                      # Ferma (SIGTERM + timeout + SIGKILL)
docker stop -t 30 web                # Timeout 30s prima di SIGKILL
docker kill web                      # SIGKILL immediato
docker start web                     # Riavvia
docker restart web                   # Stop + start
docker pause web                     # Congela (SIGSTOP via cgroup freezer)
docker unpause web                   # Scongela
docker rm web                        # Rimuovi (deve essere fermo)
docker rm -f web                     # Forza rimozione

# Avvio con policy di restart
docker run -d --restart=always nginx         # Riavvia sempre (anche dopo reboot)
docker run -d --restart=unless-stopped nginx # Come always, ma non se fermato manualmente
docker run -d --restart=on-failure:5 nginx   # Riavvia su fallimento, max 5 tentativi

# Rinominare un container
docker rename old_name new_name

# Aggiornare configurazione a caldo
docker update --memory=1g --cpus=2 web
```

### Interazione con i container

```bash
# INTERAZIONE
docker exec -it web bash             # Shell nel container
docker exec -it web sh               # Shell per Alpine (no bash)
docker exec web cat /etc/nginx/nginx.conf  # Comando singolo
docker exec -u root web whoami       # Eseguire come utente specifico
docker exec -e MY_VAR=value web env  # Con variabili d'ambiente

docker logs web                      # Log
docker logs -f web                   # Follow logs
docker logs --tail 100 web           # Ultime 100 righe
docker logs --since 1h web           # Ultimo ora
docker logs --until 2026-05-22T10:00:00 web  # Fino a data/ora specifica

docker inspect web                   # Dettagli JSON completi
docker inspect --format '{{.NetworkSettings.IPAddress}}' web
docker inspect --format '{{.State.Status}}' web
docker inspect --format '{{json .Config.Env}}' web | jq .

docker stats                         # Risorse in tempo reale (tutti)
docker stats web                     # Risorse di un container specifico
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

docker top web                       # Processi nel container
docker diff web                      # File modificati rispetto all'immagine

# Copiare file da/verso container
docker cp web:/etc/nginx/nginx.conf ./nginx.conf
docker cp ./index.html web:/usr/share/nginx/html/

# Esportare container come tarball
docker export web > web_filesystem.tar

# Creare immagine da container modificato (non raccomandato per produzione)
docker commit web myapp:snapshot
```

### Pulizia e manutenzione

```bash
# PULIZIA
docker system prune                  # Rimuovi container/immagini/network non usati
docker system prune -a               # + immagini senza container
docker system prune -a --volumes     # + volumi
docker system prune --filter "until=24h"  # Solo risorse più vecchie di 24h
docker system df                     # Uso spazio
docker system df -v                  # Dettagliato per risorsa

# Pulizia selettiva
docker container prune               # Solo container fermi
docker image prune                   # Solo immagini dangling
docker image prune -a                # Tutte le immagini non in uso
docker volume prune                  # Solo volumi orfani
docker network prune                 # Solo reti non in uso

# Script di manutenzione automatica (crontab)
# 0 3 * * * docker system prune -af --filter "until=168h" 2>&1 | logger -t docker-prune
```

---

## Immagini e Dockerfile

### Gestione immagini

```bash
# GESTIONE IMMAGINI
docker images                        # Lista immagini locali
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
docker pull nginx:1.25               # Scarica versione specifica
docker pull nginx:latest             # Ultima versione
docker pull --platform linux/arm64 nginx  # Piattaforma specifica
docker rmi nginx:1.25                # Rimuovi immagine
docker image prune                   # Rimuovi immagini dangling
docker tag myapp:latest myapp:v1.0   # Tag
docker history nginx                 # Layer dell'immagine
docker image inspect nginx --format '{{.Size}}'

# Salvare/caricare immagini (air-gapped environments)
docker save nginx:1.25 -o nginx-1.25.tar
docker load -i nginx-1.25.tar

# Salvare multiple immagini
docker save nginx:1.25 redis:7 postgres:16 -o stack.tar
```

### Dockerfile — Istruzioni fondamentali

Ogni istruzione del Dockerfile crea un nuovo layer nell'immagine. L'ordine delle istruzioni impatta la cache e la dimensione finale.

| Istruzione | Funzione |
|-----------|----------|
| `FROM` | Immagine base |
| `RUN` | Esegue comando (crea layer) |
| `COPY` | Copia file dal build context |
| `ADD` | Come COPY ma con auto-extraction e URL (preferire COPY) |
| `WORKDIR` | Directory di lavoro |
| `ENV` | Variabile d'ambiente (persistente nell'immagine) |
| `ARG` | Variabile solo per il build (non presente nel container) |
| `EXPOSE` | Documenta la porta (non fa binding) |
| `USER` | Utente per RUN/CMD/ENTRYPOINT successivi |
| `VOLUME` | Definisce mount point (crea volume anonimo) |
| `HEALTHCHECK` | Controllo stato del servizio |
| `ENTRYPOINT` | Comando base (non sovrascrivibile senza --entrypoint) |
| `CMD` | Argomenti default per ENTRYPOINT (sovrascrivibili) |
| `LABEL` | Metadati dell'immagine |
| `STOPSIGNAL` | Segnale per docker stop (default SIGTERM) |
| `SHELL` | Shell per le istruzioni RUN |

```dockerfile
# Differenza ENTRYPOINT vs CMD
# ENTRYPOINT = il binario che viene sempre eseguito
# CMD = argomenti default che possono essere sovrascritti

# Esempio: ENTRYPOINT + CMD
ENTRYPOINT ["python", "app.py"]
CMD ["--port", "8000"]
# docker run myapp               → python app.py --port 8000
# docker run myapp --port 9000   → python app.py --port 9000

# Esempio: solo CMD (più flessibile)
CMD ["python", "app.py", "--port", "8000"]
# docker run myapp               → python app.py --port 8000
# docker run myapp bash          → bash (sostituisce tutto)
```

### Multi-stage build

Il multi-stage build è fondamentale per produrre immagini minimali. Lo stage di build contiene compilatori, dependency di sviluppo, strumenti di test. Lo stage finale contiene solo il runtime e l'artefatto compilato.

```dockerfile
# ============================================================
# Esempio: Applicazione Go (da ~1GB a ~10MB)
# ============================================================
FROM golang:1.22-alpine AS builder

WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /app/server ./cmd/server

# Stage di test (opzionale, per CI)
FROM builder AS tester
RUN go test -v ./...

# Stage finale: distroless (nessun shell, nessun package manager)
FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /app/server /server
EXPOSE 8080
USER nonroot:nonroot
ENTRYPOINT ["/server"]

# ============================================================
# Esempio: Applicazione Node.js
# ============================================================
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:20-alpine
WORKDIR /app

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

COPY --from=builder /app/node_modules ./node_modules
COPY . .

ENV NODE_ENV=production
ENV PORT=3000

EXPOSE 3000

USER appuser

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -qO- http://localhost:3000/health || exit 1

CMD ["node", "server.js"]

# ============================================================
# Esempio: Applicazione Python
# ============================================================
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

FROM base AS deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY . .

RUN useradd -r -s /bin/false appuser
USER appuser

EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]

# ============================================================
# Esempio: Applicazione Rust
# ============================================================
FROM rust:1.78-slim AS builder

WORKDIR /app
COPY Cargo.toml Cargo.lock ./
# Cache delle dipendenze: trucco con progetto vuoto
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release
RUN rm -rf src

COPY src ./src
RUN touch src/main.rs  # Forza ricompilazione
RUN cargo build --release

FROM gcr.io/distroless/cc-debian12:nonroot
COPY --from=builder /app/target/release/myapp /myapp
USER nonroot:nonroot
ENTRYPOINT ["/myapp"]

# ============================================================
# Esempio: Frontend React + nginx
# ============================================================
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.25-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### Layer caching — Ottimizzazione build

La cache dei layer è il fattore principale di performance nel build. Docker riusa un layer dalla cache se l'istruzione e tutti i layer precedenti sono identici.

```dockerfile
# ✗ SBAGLIATO: COPY . . invalida la cache ad ogni modifica di qualsiasi file
FROM node:20-alpine
WORKDIR /app
COPY . .
RUN npm ci
CMD ["node", "server.js"]

# ✓ CORRETTO: separare dipendenze da codice applicativo
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./    # Cambia raramente
RUN npm ci                                 # Cachato finché package.json non cambia
COPY . .                                   # Solo il codice, invalidazione frequente OK
CMD ["node", "server.js"]
```

Regole per ottimizzare la cache:

1. **Ordine per frequenza di cambiamento**: istruzioni che cambiano raramente prima, quelle che cambiano spesso dopo
2. **Separare dipendenze dal codice**: copiare prima i file di lock, poi installare, poi copiare il codice
3. **Combinare RUN per ridurre layer**: più comandi `apt-get` in un unico `RUN`
4. **Pulire nella stessa istruzione RUN**: `apt-get install && rm -rf /var/lib/apt/lists/*`

```dockerfile
# ✗ SBAGLIATO: ogni RUN crea un layer, la pulizia nel secondo non recupera spazio
RUN apt-get update && apt-get install -y curl wget
RUN rm -rf /var/lib/apt/lists/*

# ✓ CORRETTO: installazione e pulizia nello stesso layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl wget && \
    rm -rf /var/lib/apt/lists/*
```

```bash
# Build con cache avanzata (BuildKit, abilitato di default in Docker 23+)
DOCKER_BUILDKIT=1 docker build -t myapp .

# Cache mount per package manager (evita re-download)
# Nel Dockerfile:
# RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.txt
# RUN --mount=type=cache,target=/var/cache/apt apt-get install -y curl

# Esaminare l'uso della cache durante il build
docker build -t myapp . 2>&1 | grep -i cache
```

### .dockerignore

Il file `.dockerignore` riduce il build context (dati inviati al daemon Docker) e previene l'inclusione accidentale di file sensibili o inutili nell'immagine.

```
# VCS
.git
.gitignore
.svn

# Dipendenze (verranno installate nel Dockerfile)
node_modules
vendor
__pycache__
*.pyc
.venv
venv

# Build output
dist
build
target
*.o
*.a

# IDE
.idea
.vscode
*.swp
*.swo

# Test e docs
*.test.js
*.spec.js
coverage
.nyc_output
docs
README.md
CHANGELOG.md

# Environment e secrets
.env
.env.*
*.pem
*.key
*.crt
secrets/

# Docker
Dockerfile*
docker-compose*
.dockerignore

# Log
*.log
logs/

# OS
.DS_Store
Thumbs.db
```

### Security scanning delle immagini

```bash
# Trivy — scanner open source (consigliato)
# Installazione
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sudo sh -s -- -b /usr/local/bin

# Scansione immagine
trivy image myapp:v1.0
trivy image --severity HIGH,CRITICAL myapp:v1.0
trivy image --severity CRITICAL --exit-code 1 myapp:v1.0  # Fallisci se critico

# Scansione Dockerfile
trivy config Dockerfile

# Scansione filesystem locale
trivy fs .

# Report in formato JSON (per CI/CD)
trivy image --format json --output report.json myapp:v1.0

# Grype — scanner di Anchore
# Installazione
curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sudo sh -s -- -b /usr/local/bin

# Scansione
grype myapp:v1.0
grype myapp:v1.0 --only-fixed              # Solo vulnerabilità con fix disponibile
grype myapp:v1.0 --fail-on critical        # Exit code 1 se critico
grype myapp:v1.0 -o json > grype-report.json

# Docker Scout (integrato in Docker Desktop)
docker scout cves myapp:v1.0
docker scout recommendations myapp:v1.0

# Esempio di integrazione CI (GitHub Actions snippet)
# - name: Scan image
#   run: |
#     trivy image --exit-code 1 --severity CRITICAL ${{ env.IMAGE }}
```

### Build multi-piattaforma

```bash
# Creare builder multi-piattaforma
docker buildx create --name multiarch --driver docker-container --use

# Build per multiple architetture e push
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  -t myregistry.com/myapp:v1.0 \
  --push .

# Build solo per un'architettura diversa (senza push)
docker buildx build --platform linux/arm64 -t myapp:arm64 --load .

# Verificare le piattaforme supportate
docker buildx ls

# Ispezionare manifest multi-arch
docker manifest inspect nginx:1.25
```

---

## Docker Networking

Docker crea un ecosistema di rete completo per i container. Comprendere i driver di rete è fondamentale per architetture multi-container e per il debugging.

### Driver di rete: bridge

Il driver **bridge** è il default. Docker crea un bridge virtuale (`docker0`) sull'host. Ogni container riceve una coppia veth: un'estremità nel network namespace del container, l'altra connessa al bridge.

```bash
# La rete bridge default
docker network inspect bridge

# Traffico tra container sulla rete bridge default:
# I container comunicano tramite IP, ma NON per nome (no DNS su rete default)

# Rete bridge custom (consigliata): DNS automatico
docker network create --driver bridge \
  --subnet 172.20.0.0/16 \
  --gateway 172.20.0.1 \
  --ip-range 172.20.1.0/24 \
  --opt com.docker.network.bridge.name=br-custom \
  mynet

docker run -d --name web --network mynet nginx
docker run -d --name app --network mynet myapp

# Da "app": curl http://web:80  ← risoluzione DNS per nome container
```

```
Architettura bridge:

  Host
  ┌────────────────────────────────────────────┐
  │                                            │
  │   ┌──────────┐  veth    ┌───────────┐     │
  │   │Container │──────────│           │     │
  │   │  web     │          │  docker0  │     │
  │   └──────────┘  veth    │  (bridge) │─── eth0 ──► Internet
  │   ┌──────────┐──────────│           │     │
  │   │Container │          └───────────┘     │
  │   │  app     │                            │
  │   └──────────┘                            │
  │                                            │
  └────────────────────────────────────────────┘
```

### Driver di rete: host

Il container condivide lo stack di rete dell'host. Nessun isolamento di rete, nessun overhead NAT. Il container usa direttamente le porte dell'host.

```bash
# Rete host — massime prestazioni, zero isolamento
docker run -d --network host nginx
# nginx ascolta direttamente sulla porta 80 dell'host
# Nessun port mapping necessario (-p non ha effetto)

# Utile per:
# - Applicazioni che necessitano di performance di rete native
# - Servizi di monitoraggio che devono vedere tutto il traffico host
# - Ridurre l'overhead NAT per applicazioni ad alto throughput

# NON usare quando:
# - Servono più container sulla stessa porta
# - L'isolamento di rete è un requisito
```

### Driver di rete: overlay

Il driver **overlay** crea una rete Layer 2 virtuale sopra la rete fisica, permettendo a container su host diversi di comunicare come se fossero sulla stessa LAN. Richiede Docker Swarm o un key-value store esterno.

```bash
# Creare una rete overlay (richiede Swarm mode)
docker network create --driver overlay --attachable my-overlay

# --attachable permette a container standalone di connettersi
# (non solo servizi Swarm)

# Overlay usa VXLAN per incapsulare il traffico Layer 2 in UDP
# Porta default: UDP 4789

# Opzioni avanzate
docker network create --driver overlay \
  --subnet 10.10.0.0/24 \
  --opt encrypted \
  my-secure-overlay
# --opt encrypted: crittografa il traffico VXLAN con IPSec (overhead ~10%)
```

### Driver di rete: macvlan

Il driver **macvlan** assegna un indirizzo MAC reale ad ogni container, facendoli apparire come device fisici sulla rete. I container ricevono IP dalla stessa subnet dell'host o da una VLAN dedicata.

```bash
# macvlan: i container appaiono come host fisici sulla rete
docker network create -d macvlan \
  --subnet=192.168.1.0/24 \
  --gateway=192.168.1.1 \
  -o parent=eth0 \
  my-macvlan

docker run -d --network my-macvlan --ip 192.168.1.100 --name srv1 nginx

# macvlan con VLAN tagging (trunk)
docker network create -d macvlan \
  --subnet=10.0.10.0/24 \
  --gateway=10.0.10.1 \
  -o parent=eth0.10 \
  vlan10

# Limitazione: il container macvlan NON può comunicare con l'host
# (il traffico dall'IP macvlan all'IP host viene scartato dal kernel)
# Workaround: creare un'interfaccia macvlan anche sull'host
```

### DNS resolution interna

Docker fornisce un server DNS embedded (127.0.0.11) per le reti custom (non per la rete bridge default). Ogni container su una rete custom può raggiungere gli altri per nome.

```bash
# Verifica DNS nel container
docker run --rm --network mynet alpine nslookup web
# Server: 127.0.0.11
# Address: 127.0.0.11:53
# Name: web
# Address: 172.20.1.2

# Network alias — un container raggiungibile con nomi multipli
docker run -d --network mynet --network-alias db --network-alias database postgres:16
# Raggiungibile sia come "db" che come "database"

# DNS round-robin per load balancing (limitato)
docker run -d --name web1 --network mynet --network-alias webservers nginx
docker run -d --name web2 --network mynet --network-alias webservers nginx
# "webservers" risolve alternativamente a web1 o web2

# Custom DNS per il container
docker run -d --dns 8.8.8.8 --dns-search example.com nginx
```

### Port mapping — Meccanismo interno

Quando si usa `-p host_port:container_port`, Docker configura regole iptables (o nftables) per fare DNAT (Destination NAT) dal port dell'host al port del container.

```bash
# Esaminare le regole iptables create da Docker
sudo iptables -t nat -L -n -v | grep -A5 DOCKER

# Per il mapping -p 8080:80:
# Chain DOCKER (2 references)
# target   prot  opt  source   destination
# DNAT     tcp   --   0.0.0.0/0  0.0.0.0/0  tcp dpt:8080 to:172.17.0.2:80

# Port mapping completo
docker run -d -p 8080:80 nginx               # host:container su tutte le interfacce
docker run -d -p 127.0.0.1:8080:80 nginx     # Solo localhost
docker run -d -p 8080:80/udp nginx            # UDP
docker run -d -p 8080:80/tcp -p 8080:80/udp nginx  # TCP e UDP
docker run -d -P nginx                        # Porte random per tutti gli EXPOSE
docker run -d -p 8080-8090:80 nginx           # Range di porte host

# Verificare il mapping
docker port web
# 80/tcp -> 0.0.0.0:8080

# Nota sicurezza: -p 8080:80 espone su 0.0.0.0 (tutte le interfacce)
# In produzione, bind esplicito: -p 127.0.0.1:8080:80
# Docker bypassa firewall come ufw/firewalld perché opera su iptables direttamente
```

### Comandi di rete

```bash
# Gestione reti
docker network ls                    # Lista reti
docker network inspect mynet         # Dettagli (subnet, gateway, container connessi)
docker network create mynet          # Crea rete bridge
docker network rm mynet              # Rimuovi
docker network prune                 # Rimuovi reti non usate

# Connettere/disconnettere container
docker network connect mynet existing_container
docker network connect --ip 172.20.1.50 mynet container  # IP specifico
docker network disconnect mynet existing_container

# Container su multiple reti
docker run -d --name proxy --network frontend nginx
docker network connect backend proxy
# Il container "proxy" è ora su sia "frontend" che "backend"

# Debugging rete
docker run --rm --network mynet nicolaka/netshoot \
  curl -v http://web:80
# netshoot contiene: tcpdump, nslookup, dig, curl, iperf, etc.
```

---

## Docker Volumi e Storage

### Volume Docker (named volumes)

I volumi Docker sono il metodo raccomandato per persistere dati. Sono gestiti da Docker in `/var/lib/docker/volumes/` e offrono backup, migrazione, e condivisione semplificata.

```bash
# Creazione e gestione
docker volume create mydata
docker volume create --label project=myapp mydata
docker volume ls
docker volume ls --filter label=project=myapp
docker volume inspect mydata
# {
#   "CreatedAt": "2026-05-22T10:00:00Z",
#   "Driver": "local",
#   "Labels": {"project": "myapp"},
#   "Mountpoint": "/var/lib/docker/volumes/mydata/_data",
#   "Name": "mydata",
#   "Options": null,
#   "Scope": "local"
# }
docker volume rm mydata
docker volume prune                  # Rimuovi non usati

# Utilizzo
docker run -d -v mydata:/var/lib/mysql mysql:8
docker run -d --mount source=mydata,target=/var/lib/mysql mysql:8

# Volume condiviso tra container (es. asset statici)
docker run -d --name generator -v shared:/output myapp
docker run -d --name webserver -v shared:/usr/share/nginx/html:ro nginx

# Volume con driver NFS (condiviso tra host)
docker volume create \
  --driver local \
  --opt type=nfs \
  --opt o=addr=192.168.1.10,rw \
  --opt device=:/exports/data \
  nfs-data
```

### Bind mounts

I bind mount montano una directory o file dell'host direttamente nel container. Utili per sviluppo (hot reload), ma meno portabili dei volumi.

```bash
# Bind mount di directory
docker run -d -v /host/path:/container/path nginx
docker run -d -v $(pwd)/html:/usr/share/nginx/html:ro nginx  # Read-only

# Sintassi --mount (più esplicita, raccomandata)
docker run -d \
  --mount type=bind,source=/host/path,target=/container/path,readonly \
  nginx

# Bind mount di file singolo (es. configurazione)
docker run -d -v /host/nginx.conf:/etc/nginx/nginx.conf:ro nginx

# Attenzione: se il path host non esiste:
# -v → Docker crea una directory vuota
# --mount → errore (comportamento più sicuro)

# Propagazione dei mount
docker run -d --mount type=bind,source=/data,target=/data,bind-propagation=shared nginx
# shared: mount/unmount propagano in entrambe le direzioni
# slave: propagano solo host → container
# private: nessuna propagazione (default)
```

### tmpfs mounts

I tmpfs mount esistono solo in memoria (RAM). I dati vengono persi quando il container si ferma. Utili per dati temporanei sensibili o per performance.

```bash
# tmpfs con limiti
docker run -d --tmpfs /tmp:size=100m,mode=1777 nginx

# Sintassi --mount
docker run -d \
  --mount type=tmpfs,destination=/tmp,tmpfs-size=100m,tmpfs-mode=1777 \
  nginx

# Caso d'uso: sessioni, cache temporanea, file PID
docker run -d \
  --read-only \
  --tmpfs /tmp:size=50m \
  --tmpfs /run:size=10m \
  myapp
# Container read-only con directory temporanee in RAM
```

### Storage drivers

Lo storage driver determina come Docker salva i layer delle immagini e il layer read-write dei container sul filesystem.

| Driver | Filesystem host | Note |
|--------|----------------|------|
| **overlay2** | ext4, xfs | Default e raccomandato. Stabile, performante |
| **btrfs** | btrfs | Usa snapshot nativi btrfs. Buono per molte immagini |
| **zfs** | zfs | Usa clone ZFS. Eccellente per I/O intensivo |
| **devicemapper** | Direct-lvm | Legacy, deprecato. Evitare |
| **fuse-overlayfs** | qualsiasi | Per container rootless su kernel senza overlay unprivileged |

```bash
# Verificare lo storage driver in uso
docker info | grep "Storage Driver"
# Storage Driver: overlay2

# overlay2 — Come funziona:
# Usa OverlayFS del kernel per unire layer in una vista unificata.
# lowerdir: layer read-only dell'immagine (impilati)
# upperdir: layer read-write del container
# merged: vista unificata visibile al container
# workdir: directory di lavoro per operazioni atomiche

# Esaminare i path overlay di un container
docker inspect web --format '{{json .GraphDriver.Data}}' | jq .
# {
#   "LowerDir": "/var/lib/docker/overlay2/abc.../diff:...",
#   "MergedDir": "/var/lib/docker/overlay2/xyz.../merged",
#   "UpperDir": "/var/lib/docker/overlay2/xyz.../diff",
#   "WorkDir": "/var/lib/docker/overlay2/xyz.../work"
# }

# Cambiare storage driver (richiede riavvio, perde tutte le immagini/container)
# /etc/docker/daemon.json:
# {
#   "storage-driver": "btrfs"
# }

# btrfs — Usare quando il filesystem host è btrfs:
# Ogni layer è un subvolume btrfs
# Copy-on-Write nativo del filesystem
# Snapshot efficienti per i container
# btrfs send/receive per migrazione

# zfs — Usare quando il filesystem host è zfs:
# Ogni layer è un clone ZFS
# Deduplicazione, compressione, checksum nativi
# Eccellente per carichi I/O intensivi
# zfs send/receive per migrazione
```

### Backup e restore dei volumi

```bash
# Backup di un volume in un archivio tar
docker run --rm \
  -v mydata:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/mydata-$(date +%Y%m%d).tar.gz -C /data .

# Restore di un volume da archivio
docker volume create mydata_restored
docker run --rm \
  -v mydata_restored:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/mydata-20260522.tar.gz -C /data

# Copiare un volume tra host (via ssh)
docker run --rm -v mydata:/data alpine tar czf - -C /data . | \
  ssh user@remote "docker run --rm -i -v mydata:/data alpine tar xzf - -C /data"

# Backup automatizzato con script
# #!/bin/bash
# VOLUMES=$(docker volume ls -q)
# BACKUP_DIR="/backup/docker-volumes/$(date +%Y%m%d)"
# mkdir -p "$BACKUP_DIR"
# for vol in $VOLUMES; do
#   docker run --rm -v "$vol":/data -v "$BACKUP_DIR":/backup \
#     alpine tar czf "/backup/${vol}.tar.gz" -C /data .
# done
```

---

## Docker Compose v2

Docker Compose v2 è un plugin CLI di Docker (`docker compose`, senza trattino). Gestisce applicazioni multi-container con un file YAML dichiarativo.

> **Nota:** La chiave `version` nel file Compose è deprecata dalla specifica Compose v2. Docker la ignora e inferisce la versione dal contenuto. Negli esempi esistenti può essere presente per retrocompatibilità, ma non è più necessaria.

### Struttura del file Compose

```yaml
# compose.yml (nome raccomandato) o docker-compose.yml
# La chiave "version" è deprecata in Compose v2 e può essere omessa

services:
  web:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - API_URL=http://api:8000
    depends_on:
      - api
    networks:
      - frontend

  api:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
      args:
        - BUILD_ENV=production
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
      - REDIS_URL=redis://cache:6379
    depends_on:
      db:
        condition: service_healthy
      cache:
        condition: service_started
    networks:
      - frontend
      - backend
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 512M
        reservations:
          cpus: "0.5"
          memory: 128M

  db:
    image: postgres:16-alpine
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: mydb
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d mydb"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    networks:
      - backend

  cache:
    image: redis:7-alpine
    command: redis-server --save 60 1 --loglevel warning
    volumes:
      - redisdata:/data
    networks:
      - backend

volumes:
  pgdata:
    driver: local
  redisdata:
    driver: local

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true    # Nessun accesso esterno (solo tra container)
```

### Services, Networks, Volumes

```yaml
# ============================================================
# Sezione services — opzioni avanzate
# ============================================================
services:
  app:
    image: myapp:v1.0
    # oppure
    build:
      context: .
      dockerfile: Dockerfile
      target: production       # Stage specifico del multi-stage
      cache_from:
        - myapp:cache
      labels:
        com.example.version: "1.0"

    # Variabili d'ambiente (tre modi)
    environment:
      - DEBUG=false
      - LOG_LEVEL=info
    # oppure da file
    env_file:
      - .env
      - .env.production

    # Porte
    ports:
      - "8080:80"             # host:container
      - "127.0.0.1:9090:9090" # Solo localhost
    expose:
      - "3000"                # Solo tra container (non sull'host)

    # Volumi
    volumes:
      - app-data:/data                    # Named volume
      - ./config:/app/config:ro           # Bind mount read-only
      - type: tmpfs
        target: /tmp
        tmpfs:
          size: 100m

    # Limiti risorse
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: "1.0"
          memory: 256M
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3

    # Logging
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

    # Extra hosts (aggiunge entry in /etc/hosts)
    extra_hosts:
      - "host.docker.internal:host-gateway"

    # Capabilities
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE

    # Sicurezza
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /run

# ============================================================
# Sezione networks — opzioni avanzate
# ============================================================
networks:
  frontend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/24
          gateway: 172.20.0.1

  backend:
    driver: bridge
    internal: true            # Nessun accesso a internet

  external-net:
    external: true            # Rete creata esternamente (docker network create)
    name: shared-network

# ============================================================
# Sezione volumes — opzioni avanzate
# ============================================================
volumes:
  app-data:
    driver: local

  nfs-share:
    driver: local
    driver_opts:
      type: nfs
      o: "addr=192.168.1.10,nolock,soft,rw"
      device: ":/exports/data"

  existing-volume:
    external: true
    name: pre-existing-volume
```

### depends_on e healthcheck

```yaml
services:
  api:
    build: .
    depends_on:
      db:
        condition: service_healthy      # Aspetta che db passi healthcheck
        restart: true                   # Riavvia se db si riavvia
      cache:
        condition: service_started      # Aspetta solo che sia avviato
      migrations:
        condition: service_completed_successfully  # Aspetta completamento

  db:
    image: postgres:16-alpine
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d mydb"]
      interval: 10s          # Ogni 10 secondi
      timeout: 5s            # Timeout per singolo check
      retries: 5             # Tentativi prima di dichiarare unhealthy
      start_period: 30s      # Grazia iniziale (check falliti non contano)
      start_interval: 2s     # Intervallo durante start_period

  cache:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 3

  migrations:
    build: ./migrations
    command: ["python", "migrate.py"]
    depends_on:
      db:
        condition: service_healthy
    # Container one-shot: si avvia, esegue, esce
```

### Profiles

I profili permettono di avviare sottoinsiemi di servizi. Utili per separare ambienti di sviluppo, test, debug.

```yaml
services:
  app:
    build: .
    ports:
      - "8080:8080"
    # Nessun profilo: sempre avviato

  db:
    image: postgres:16-alpine
    # Nessun profilo: sempre avviato

  debug-tools:
    image: nicolaka/netshoot
    profiles:
      - debug
    network_mode: "service:app"
    # Avviato solo con: docker compose --profile debug up

  test-runner:
    build:
      context: .
      target: test
    profiles:
      - test
    depends_on:
      - db
    command: ["pytest", "-v"]
    # Avviato solo con: docker compose --profile test up

  monitoring:
    image: prom/prometheus
    profiles:
      - monitoring
      - production
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    profiles:
      - monitoring
      - production
    ports:
      - "3000:3000"
```

```bash
# Avviare servizi senza profilo (app + db)
docker compose up -d

# Avviare con profilo debug
docker compose --profile debug up -d

# Avviare con multipli profili
docker compose --profile monitoring --profile debug up -d

# Il profilo "production" include monitoring + grafana
docker compose --profile production up -d
```

### Extensions (x-)

Le chiavi che iniziano con `x-` sono estensioni custom ignorate da Compose. Utili per riutilizzare blocchi di configurazione con YAML anchors.

```yaml
# Blocchi riutilizzabili con anchors YAML
x-common-env: &common-env
  LOG_LEVEL: info
  TZ: Europe/Rome
  NODE_ENV: production

x-common-deploy: &common-deploy
  deploy:
    resources:
      limits:
        cpus: "1.0"
        memory: 256M
    restart_policy:
      condition: on-failure
      max_attempts: 3

x-common-logging: &common-logging
  logging:
    driver: json-file
    options:
      max-size: "10m"
      max-file: "3"

services:
  api:
    build: ./api
    environment:
      <<: *common-env
      PORT: "8000"
    <<: [*common-deploy, *common-logging]

  worker:
    build: ./worker
    environment:
      <<: *common-env
      QUEUE: default
    <<: [*common-deploy, *common-logging]

  scheduler:
    build: ./scheduler
    environment:
      <<: *common-env
    <<: [*common-deploy, *common-logging]
```

### Comandi Compose

```bash
# Lifecycle
docker compose up -d                 # Avvia tutto in background
docker compose up -d --build         # Rebuild prima di avviare
docker compose up -d --force-recreate  # Forza ricreazione container
docker compose down                  # Ferma e rimuovi container + reti
docker compose down -v               # + rimuovi volumi
docker compose down --rmi all        # + rimuovi immagini
docker compose stop                  # Ferma senza rimuovere
docker compose start                 # Avvia container esistenti

# Status
docker compose ps                    # Stato servizi
docker compose ps -a                 # Inclusi fermi
docker compose top                   # Processi per servizio

# Log
docker compose logs                  # Log tutti
docker compose logs -f api           # Follow log di un servizio
docker compose logs --tail 50 api db # Ultimi 50 di api e db
docker compose logs --since 1h       # Ultima ora

# Interazione
docker compose exec api bash         # Shell in un servizio
docker compose run --rm api pytest   # Esegui comando one-shot

# Gestione
docker compose build                 # Rebuild immagini
docker compose build --no-cache api  # Rebuild senza cache
docker compose pull                  # Aggiorna immagini
docker compose push                  # Push immagini al registry
docker compose restart api           # Restart singolo servizio
docker compose up -d --scale api=3   # 3 istanze di api

# Configurazione
docker compose config                # Validare e visualizzare config compilata
docker compose config --services     # Lista servizi

# Compose con file multipli (override)
docker compose -f compose.yml -f compose.prod.yml up -d
# Il secondo file sovrascrive/estende il primo
```

---

## Docker Sicurezza

La sicurezza dei container si basa su più livelli di difesa. Nessuna singola misura è sufficiente; la combinazione di più tecniche riduce significativamente la superficie d'attacco.

### Container rootless

Eseguire il daemon Docker senza privilegi root elimina un'intera classe di vulnerabilità di container escape.

```bash
# Docker rootless — installazione
# Prerequisiti: uidmap, newuidmap, newgidmap
sudo apt install uidmap dbus-user-session

# Installare dockerd-rootless
dockerd-rootless-setuptool.sh install

# Il daemon gira come utente normale
# Socket: $XDG_RUNTIME_DIR/docker.sock
# Data: ~/.local/share/docker

# Configurare l'uso rootless
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/docker.sock

# Verificare
docker info | grep "Root"
# rootless: true

# Limitazioni rootless:
# - Non può fare bind su porte < 1024 (senza sysctl)
# - Prestazioni di rete leggermente inferiori (slirp4netns o pasta)
# - Alcuni storage driver non disponibili
# - No --privileged, no --net=host

# Permettere porte privilegiate per rootless
sudo sysctl net.ipv4.ip_unprivileged_port_start=80
```

### Read-only filesystem

```bash
# Container completamente read-only
docker run -d --read-only nginx
# Il container non può scrivere su nessun path

# Read-only con eccezioni necessarie
docker run -d \
  --read-only \
  --tmpfs /tmp:size=50m \
  --tmpfs /run:size=10m \
  --tmpfs /var/cache/nginx:size=20m \
  -v nginx-logs:/var/log/nginx \
  nginx

# In Docker Compose
services:
  app:
    image: myapp
    read_only: true
    tmpfs:
      - /tmp:size=50m
    volumes:
      - app-data:/data
```

### Capabilities dropping

Le Linux capabilities suddividono i privilegi di root in unità granulari. Ogni container Docker parte con un set ridotto di capability, ma è best practice droppare tutto e aggiungere solo quelle necessarie.

```bash
# Capability di default concesse da Docker:
# AUDIT_WRITE, CHOWN, DAC_OVERRIDE, FOWNER, FSETID,
# KILL, MKNOD, NET_BIND_SERVICE, NET_RAW, SETFCAP,
# SETGID, SETPCAP, SETUID, SYS_CHROOT

# Droppare tutto, aggiungere solo il necessario
docker run -d \
  --cap-drop=ALL \
  --cap-add=NET_BIND_SERVICE \
  nginx
# nginx ha bisogno solo di NET_BIND_SERVICE per port 80

# Verificare le capability di un container
docker inspect --format '{{.HostConfig.CapAdd}}' web
docker inspect --format '{{.HostConfig.CapDrop}}' web

# Capability comuni e il loro uso:
# NET_BIND_SERVICE — bind su porte < 1024
# CHOWN           — cambiare owner dei file
# SETUID/SETGID   — cambiare UID/GID
# SYS_PTRACE      — debugging (strace, gdb)
# NET_ADMIN        — configurazione rete (iptables, routing)
# SYS_ADMIN        — mount, namespace ops (pericolosa, quasi equivalente a root)
# DAC_OVERRIDE     — bypassare permessi file

# MAI in produzione:
# --privileged     → concede TUTTE le capability + accesso /dev
# SYS_ADMIN        → troppo ampia, preferire alternative specifiche
```

### Profili seccomp

Seccomp (Secure Computing Mode) filtra le system call che un processo può eseguire. Docker applica un profilo seccomp di default che blocca ~44 syscall pericolose.

```bash
# Verificare che seccomp è attivo
docker info | grep -i seccomp

# Eseguire con il profilo di default (già applicato automaticamente)
docker run -d --security-opt seccomp=unconfined nginx  # DISABILITA seccomp (MAI in prod)

# Profilo seccomp custom
# Creare un file JSON con le syscall permesse
# Esempio minimale:
cat > custom-seccomp.json << 'SECCOMP_EOF'
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": ["read", "write", "open", "close", "stat", "fstat",
                "mmap", "mprotect", "munmap", "brk", "rt_sigaction",
                "rt_sigprocmask", "ioctl", "access", "pipe", "select",
                "sched_yield", "mremap", "msync", "clone", "fork",
                "execve", "exit", "wait4", "kill", "uname", "fcntl",
                "flock", "fsync", "fdatasync", "getpid", "getppid",
                "socket", "connect", "accept", "sendto", "recvfrom",
                "bind", "listen", "epoll_create", "epoll_ctl", "epoll_wait",
                "futex", "set_robust_list", "nanosleep", "clock_gettime",
                "openat", "newfstatat", "getrandom", "prlimit64"],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
SECCOMP_EOF

docker run -d --security-opt seccomp=custom-seccomp.json myapp

# Generare un profilo seccomp da un container in esecuzione (tool: oci-seccomp-bpf-hook)
# Utile per creare profili minimali basati sull'uso effettivo
```

### User namespaces

I user namespace mappano UID/GID del container a UID/GID diversi sull'host. Root nel container è un utente non privilegiato sull'host.

```bash
# Abilitare user namespace remapping per Docker
# 1. Creare l'utente di remapping
sudo groupadd dockremap
sudo useradd -g dockremap dockremap

# 2. Configurare subordinate UID/GID
echo "dockremap:100000:65536" | sudo tee -a /etc/subuid
echo "dockremap:100000:65536" | sudo tee -a /etc/subgid

# 3. Abilitare in daemon.json
# /etc/docker/daemon.json:
# {
#   "userns-remap": "dockremap"
# }

# 4. Riavviare Docker
sudo systemctl restart docker

# Verifica: root nel container ha un UID alto sull'host
docker run -d --name test nginx
ps aux | grep nginx
# 100000  ... nginx: master process  ← UID 100000, non 0

# Nota: non tutti i container funzionano con user namespace remapping
# Alcuni richiedono accesso a device o a UID specifici
```

### Secrets management

```bash
# Docker Secrets (per Swarm mode)
echo "my_super_secret_password" | docker secret create db_password -
docker service create --secret db_password --name api myapp
# Il secret è disponibile in /run/secrets/db_password nel container

# Docker Compose secrets (anche senza Swarm)
# compose.yml:
# services:
#   api:
#     image: myapp
#     secrets:
#       - db_password
#       - api_key
#     environment:
#       DB_PASSWORD_FILE: /run/secrets/db_password
#
# secrets:
#   db_password:
#     file: ./secrets/db_password.txt
#   api_key:
#     environment: "API_KEY"     # Da variabile d'ambiente dell'host

# Regole fondamentali:
# 1. MAI password in variabili d'ambiente (visibili con docker inspect)
# 2. MAI secrets nel Dockerfile o nell'immagine
# 3. Usare file secrets montati come volume o Docker secrets
# 4. Rotare i secrets periodicamente
# 5. Usare vault esterni (HashiCorp Vault, AWS Secrets Manager) in produzione
```

### Limitazione risorse

```bash
# Memoria
docker run -d --memory=512m --memory-swap=1g myapp
# --memory: hard limit RAM
# --memory-swap: RAM + swap (1g = 512m RAM + 512m swap)
# --memory-swap=-1: swap illimitato
# --memory-reservation: soft limit (best effort)

# CPU
docker run -d --cpus=1.5 myapp              # 1.5 core equivalenti
docker run -d --cpu-shares=512 myapp         # Peso relativo
docker run -d --cpuset-cpus="0,2" myapp      # Core specifici

# PID limit (previene fork bomb)
docker run -d --pids-limit=100 myapp

# Ulimits
docker run -d --ulimit nofile=65536:65536 --ulimit nproc=4096:4096 myapp

# Combinazione completa per produzione
docker run -d \
  --name api \
  --memory=512m \
  --memory-swap=512m \
  --cpus=1.0 \
  --pids-limit=200 \
  --ulimit nofile=65536:65536 \
  --read-only \
  --tmpfs /tmp:size=50m \
  --cap-drop=ALL \
  --cap-add=NET_BIND_SERVICE \
  --security-opt=no-new-privileges \
  --security-opt seccomp=default \
  --user 1000:1000 \
  -p 127.0.0.1:8080:8080 \
  myapp:v1.0
```

---

## Podman — Alternativa Rootless

Podman è un container engine OCI-compatibile con Docker ma con differenze architetturali fondamentali. Non richiede un daemon root, usa fork/exec per ogni container, ed è integrato nativamente con systemd.

### Architettura senza daemon

```
Docker:                           Podman:
┌──────────┐                     ┌──────────┐
│  docker   │                     │  podman   │
│  (CLI)    │                     │  (CLI)    │
└─────┬────┘                     └─────┬────┘
      │ socket                         │ fork/exec
┌─────▼────┐                     ┌─────▼────┐
│  dockerd  │  ← daemon root     │  conmon   │  ← monitor per container
│  (daemon) │                     └─────┬────┘
└─────┬────┘                           │
┌─────▼────┐                     ┌─────▼────┐
│containerd │                     │   runc    │
└─────┬────┘                     │  /crun    │
┌─────▼────┐                     └──────────┘
│   runc    │
└──────────┘

# Vantaggi architettura Podman:
# - Nessun single point of failure (no daemon)
# - Rootless di default
# - Integrazione systemd nativa
# - Container sopravvivono al crash del tool di gestione
```

```bash
# Installazione
sudo apt install podman

# Comandi identici a Docker
podman run -d --name web -p 8080:80 nginx
podman ps
podman logs web
podman stop web
podman rm web

# Rootless (come utente normale, senza sudo)
podman run -d -p 8080:80 nginx      # Funziona senza root

# Configurazione storage rootless
# ~/.config/containers/storage.conf
# [storage]
# driver = "overlay"
# [storage.options.overlay]
# mount_program = "/usr/bin/fuse-overlayfs"

# Configurazione registries
# ~/.config/containers/registries.conf
# unqualified-search-registries = ["docker.io", "quay.io"]
```

### Concetto di Pod

Il Pod è un concetto di Podman che raggruppa container che condividono namespace (network, IPC, PID). Analogo ai Pod di Kubernetes.

```bash
# Creare un pod
podman pod create --name myapp-pod -p 8080:80

# Aggiungere container al pod
podman run -d --pod myapp-pod --name web nginx
podman run -d --pod myapp-pod --name sidecar mylogger

# I container nel pod condividono:
# - Network namespace (stessa IP, stesse porte)
# - IPC namespace (shared memory)
# - PID namespace (opzionale)

# Gestione pod
podman pod list
podman pod inspect myapp-pod
podman pod stop myapp-pod
podman pod start myapp-pod
podman pod rm myapp-pod

# Creare pod da YAML Kubernetes
podman play kube pod-definition.yaml

# Generare YAML Kubernetes da un pod existente
podman generate kube myapp-pod > pod.yaml

# Questo flusso permette: sviluppo locale con Podman → deploy su Kubernetes
```

### Compatibilità con Docker

```bash
# Alias per compatibilità Docker
alias docker=podman

# Socket API compatibile (per tool che richiedono il Docker socket)
systemctl --user enable --now podman.socket
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/podman/podman.sock

# Docker Compose con Podman
# Il socket Podman è compatibile con Docker Compose
docker compose up -d  # Funziona se DOCKER_HOST punta al socket Podman

# Differenze chiave da ricordare:
# 1. Nessun daemon: podman non ha "docker restart" globale
# 2. Network: Podman usa CNI o netavark (non la rete bridge Docker)
# 3. Build: Podman usa Buildah internamente
# 4. Volumi: path diversi (/var/lib/containers vs /var/lib/docker)
# 5. Rootless: port < 1024 richiedono sysctl o slirp4netns config

# Verificare differenze
podman info
podman system info
```

### Integrazione systemd

```bash
# Generare unit systemd da container (metodo legacy)
podman generate systemd --name web --new --files
# Crea: container-web.service

# Installare come servizio utente
mkdir -p ~/.config/systemd/user
cp container-web.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now container-web.service

# Come servizio di sistema (root)
sudo cp container-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now container-web.service

# Abilitare linger (servizi utente sopravvivono al logout)
loginctl enable-linger $USER
```

### Podman Compose e pod play kube

```bash
# Podman Compose (richiede installazione separata)
pip install podman-compose
podman-compose up -d
podman-compose down

# Pod play kube — eseguire manifesti Kubernetes con Podman
podman play kube deployment.yaml
podman play kube deployment.yaml --replace    # Aggiornare
podman play kube deployment.yaml --down       # Rimuovere

# Esempio di Kubernetes YAML minimale per Podman
cat > my-pod.yaml << 'K8S_EOF'
apiVersion: v1
kind: Pod
metadata:
  name: myapp
spec:
  containers:
    - name: web
      image: nginx:1.25-alpine
      ports:
        - containerPort: 80
          hostPort: 8080
      volumeMounts:
        - name: html
          mountPath: /usr/share/nginx/html
  volumes:
    - name: html
      hostPath:
        path: /srv/www
        type: Directory
K8S_EOF

podman play kube my-pod.yaml
```

---

## Gestione Immagini e Registry

### Registry: Docker Hub, Harbor, Quay

Un registry è un servizio che archivia e distribuisce immagini OCI/Docker. La scelta del registry impatta sicurezza, prestazioni, e costi.

```bash
# Docker Hub (registry pubblico default)
docker login                          # Login (richiede account)
docker push myuser/myapp:v1.0        # Push
docker pull myuser/myapp:v1.0        # Pull
docker search nginx                   # Ricerca su Docker Hub

# Rate limiting Docker Hub (2026):
# Anonimo: 100 pull/6h per IP
# Autenticato free: 200 pull/6h
# Pro/Team: illimitati

# Registry locale (per sviluppo/test)
docker run -d -p 5000:5000 --name registry registry:2
docker tag myapp:v1.0 localhost:5000/myapp:v1.0
docker push localhost:5000/myapp:v1.0

# Harbor — registry enterprise open source
# Funzionalità: scan vulnerabilità, RBAC, replica tra registry,
#               firma immagini, garbage collection, audit log
# Deploy via Docker Compose o Helm (Kubernetes)
# https://goharbor.io

# Configurare Docker per registry privato (HTTP, non HTTPS)
# /etc/docker/daemon.json:
# {
#   "insecure-registries": ["myregistry.internal:5000"]
# }

# Quay.io (Red Hat)
# Funzionalità: scan Clair integrato, build automatici, mirroring
# Usato come default registry per immagini Red Hat/Fedora/CentOS

# Amazon ECR
aws ecr get-login-password --region eu-west-1 | \
  docker login --username AWS --password-stdin 123456.dkr.ecr.eu-west-1.amazonaws.com

# Google Container Registry / Artifact Registry
gcloud auth configure-docker europe-west1-docker.pkg.dev

# GitHub Container Registry (ghcr.io)
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin
docker push ghcr.io/username/myapp:v1.0
```

### Image signing: cosign e Notary

La firma delle immagini garantisce l'integrità e la provenienza. Verifica che l'immagine non sia stata modificata dopo il build e che provenga da una fonte attendibile.

```bash
# cosign (Sigstore) — firma keyless e con chiave
# Installazione
# Verificare latest release su GitHub sigstore/cosign
# https://github.com/sigstore/cosign/releases

# Generare una coppia di chiavi
cosign generate-key-pair
# Crea: cosign.key (privata) e cosign.pub (pubblica)

# Firmare un'immagine
cosign sign --key cosign.key myregistry.com/myapp:v1.0

# Verificare la firma
cosign verify --key cosign.pub myregistry.com/myapp:v1.0

# Firma keyless (tramite OIDC, es. GitHub Actions)
# cosign sign myregistry.com/myapp:v1.0
# Autentica via browser e firma con certificato temporaneo da Fulcio

# Verificare firma keyless
cosign verify \
  --certificate-identity user@example.com \
  --certificate-oidc-issuer https://accounts.google.com \
  myregistry.com/myapp:v1.0

# Attaccare SBOM (Software Bill of Materials) all'immagine
cosign attach sbom --sbom sbom.spdx.json myregistry.com/myapp:v1.0

# Notary v2 / notation (CNCF)
# Standard alternativo di firma, supportato da ACR, ECR, Harbor
# notation sign myregistry.com/myapp:v1.0
# notation verify myregistry.com/myapp:v1.0
```

### Vulnerability scanning: Trivy e Grype

```bash
# ============================================================
# Trivy — scanner completo (immagini, filesystem, config, SBOM)
# ============================================================
# Scansione immagine con severità minima
trivy image --severity HIGH,CRITICAL myapp:v1.0

# Scansione con uscita non-zero per CI/CD
trivy image --exit-code 1 --severity CRITICAL myapp:v1.0

# Ignorare vulnerabilità specifiche
# .trivyignore:
# CVE-2024-12345
# CVE-2024-67890
trivy image --ignorefile .trivyignore myapp:v1.0

# Scansione IaC (Dockerfile, Kubernetes YAML, Terraform)
trivy config .
trivy config --severity HIGH,CRITICAL Dockerfile

# Generare SBOM
trivy image --format spdx-json --output sbom.json myapp:v1.0

# Scansione in modalità server (per ambienti CI condivisi)
trivy server --listen 0.0.0.0:8080
trivy image --server http://trivy-server:8080 myapp:v1.0

# ============================================================
# Grype — scanner di vulnerabilità Anchore
# ============================================================
grype myapp:v1.0
grype myapp:v1.0 --only-fixed              # Solo con fix disponibile
grype myapp:v1.0 --fail-on critical        # Exit code 1 se critico
grype myapp:v1.0 -o json > grype-report.json
grype myapp:v1.0 -o table                  # Output tabellare

# Scansione da SBOM
syft myapp:v1.0 -o spdx-json > sbom.json   # Generare SBOM con syft
grype sbom:sbom.json                         # Scansione da SBOM

# ============================================================
# Pipeline CI consigliata
# ============================================================
# 1. Build immagine
# 2. trivy image --exit-code 1 --severity CRITICAL (blocca se critico)
# 3. cosign sign (firma immagine)
# 4. Push al registry
# 5. cosign verify nel deployment (verifica firma)
```

---

## LXC/LXD — Container di Sistema

LXC/LXD sono container "di sistema" — eseguono un init completo, più simili a VM leggere.

```bash
# Installazione LXD
sudo snap install lxd
sudo lxd init                        # Configurazione iniziale

# Gestione container
lxc launch ubuntu:22.04 myserver    # Crea e avvia
lxc list                             # Lista
lxc exec myserver bash               # Shell
lxc stop myserver
lxc delete myserver
lxc info myserver                    # Dettagli

# Snapshot
lxc snapshot myserver snap1
lxc restore myserver snap1

# Profili (template di risorse)
lxc profile create webserver
lxc profile set webserver limits.memory 2GB
lxc profile set webserver limits.cpu 2
```

---

## Buildah e Skopeo

### Buildah — Build OCI senza daemon

Buildah costruisce immagini OCI senza richiedere un daemon. Ogni operazione è una transazione indipendente. Supporta sia Dockerfile che comandi shell nativi.

```bash
# Build da Dockerfile (come docker build)
buildah bud -t myapp:v1.0 .
buildah bud -t myapp:v1.0 -f Dockerfile.prod .
buildah bud --layers -t myapp:v1.0 .   # Cache per layer

# Build interattivo (senza Dockerfile)
container=$(buildah from alpine:3.19)
buildah run $container apk add --no-cache nginx
buildah copy $container nginx.conf /etc/nginx/nginx.conf
buildah config --port 80 $container
buildah config --entrypoint '["nginx", "-g", "daemon off;"]' $container
buildah config --author "Renan" --label version=1.0 $container
buildah commit $container myapp:v1.0

# Vantaggi del build interattivo:
# - Ogni comando è una transazione
# - Nessun layer intermedio non necessario
# - Più controllo sul processo
# - Scriptabile in bash

# Mount del filesystem durante il build (per operazioni complesse)
mnt=$(buildah mount $container)
echo "custom content" > $mnt/var/www/html/index.html
buildah umount $container

# Push al registry
buildah push myapp:v1.0 docker://myregistry.com/myapp:v1.0
buildah push myapp:v1.0 oci:/tmp/myapp-oci:v1.0
buildah push myapp:v1.0 docker-archive:/tmp/myapp.tar

# Buildah rootless
buildah --storage-driver overlay bud -t myapp:v1.0 .

# Pulizia
buildah containers           # Lista container di build
buildah rm --all             # Rimuovi tutti i container di build
buildah images               # Lista immagini
buildah rmi myapp:v1.0       # Rimuovi immagine
```

### Skopeo — Gestione immagini tra registry

Skopeo copia, ispeziona e gestisce immagini tra registry senza scaricarle localmente. Non richiede un daemon.

```bash
# Ispezionare immagini remote (senza scaricare)
skopeo inspect docker://docker.io/nginx:latest
skopeo inspect docker://docker.io/nginx:latest | jq '.Digest'
skopeo inspect --raw docker://docker.io/nginx:latest | jq .  # Manifest OCI

# Copiare tra registry (senza pull/push locale)
skopeo copy \
  docker://myregistry.com/myapp:v1.0 \
  docker://newregistry.com/myapp:v1.0

# Copiare da registry a file locale (air-gapped)
skopeo copy docker://nginx:latest docker-archive:/tmp/nginx.tar
skopeo copy docker://nginx:latest oci:/tmp/nginx-oci:latest
skopeo copy docker://nginx:latest dir:/tmp/nginx-dir

# Copiare da file locale a registry
skopeo copy docker-archive:/tmp/nginx.tar docker://myregistry.com/nginx:latest

# Sincronizzare tag tra registry
skopeo sync --src docker --dest docker \
  myregistry.com/myapp \
  newregistry.com/myapp

# Eliminare immagine da registry (se supportato)
skopeo delete docker://myregistry.com/myapp:old

# Autenticazione
skopeo login myregistry.com
skopeo logout myregistry.com

# Lista tag disponibili
skopeo list-tags docker://docker.io/nginx
```

---

## Build Multi-Architettura

### Immagini Multi-Arch con Docker Buildx

```bash
# Le immagini multi-architettura permettono di pubblicare un singolo tag
# che funziona su architetture diverse (amd64, arm64, armv7, s390x, ppc64le).
# Questo e` essenziale per ambienti eterogenei: server x86, Raspberry Pi,
# cloud ARM (AWS Graviton, Azure Cobalt, GCP Axion).

# Verificare che buildx sia disponibile (incluso in Docker Desktop,
# installabile separatamente su Linux)
docker buildx version

# Creare un builder multi-platform con QEMU emulation
docker buildx create --name multiarch --driver docker-container \
    --platform linux/amd64,linux/arm64,linux/arm/v7 --use
docker buildx inspect multiarch --bootstrap

# Installare QEMU user-mode (necessario per cross-compilation)
# Su Ubuntu/Debian:
apt install -y qemu-user-static
# Oppure il metodo container (auto-registra binfmt_misc):
docker run --privileged --rm tonistiigi/binfmt --install all

# Verificare le architetture supportate
ls /proc/sys/fs/binfmt_misc/
# Dovrebbe mostrare: qemu-aarch64, qemu-arm, ecc.

# Build multi-arch e push diretto al registry
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --tag myregistry.com/myapp:1.0 \
    --push \
    .

# Verificare il manifest list risultante
docker buildx imagetools inspect myregistry.com/myapp:1.0
# Output mostra i digest per ogni architettura:
# Name:      myregistry.com/myapp:1.0
# MediaType: application/vnd.oci.image.index.v1+json
# Manifests:
#   Name: myregistry.com/myapp:1.0@sha256:aaa...
#   Platform: linux/amd64
#   Name: myregistry.com/myapp:1.0@sha256:bbb...
#   Platform: linux/arm64
```

### Build Multi-Arch con Buildah

```bash
# Buildah supporta build multi-arch tramite manifest list nativi.
# Non richiede un daemon Docker.

# Creare un manifest list vuoto
buildah manifest create myapp:1.0

# Build per amd64
buildah build --arch amd64 --os linux \
    --tag myregistry.com/myapp:1.0-amd64 .
buildah manifest add myapp:1.0 myregistry.com/myapp:1.0-amd64

# Build per arm64 (richiede qemu-user-static)
buildah build --arch arm64 --os linux \
    --tag myregistry.com/myapp:1.0-arm64 .
buildah manifest add myapp:1.0 myregistry.com/myapp:1.0-arm64

# Push del manifest list al registry
buildah manifest push --all myapp:1.0 \
    docker://myregistry.com/myapp:1.0

# Ispezionare il risultato con Skopeo
skopeo inspect --raw docker://myregistry.com/myapp:1.0 | python3 -m json.tool
```

### Best Practice per Dockerfile Multi-Arch

```dockerfile
# Usare immagini base multi-arch ufficiali
FROM --platform=$TARGETPLATFORM golang:1.23-alpine AS builder

# TARGETPLATFORM, TARGETOS, TARGETARCH sono variabili
# iniettate automaticamente da buildx/buildah
ARG TARGETPLATFORM
ARG TARGETOS
ARG TARGETARCH

# Cross-compile per l'architettura target
RUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} \
    go build -ldflags="-s -w" -o /app ./cmd/server

# Stage finale: immagine minimale
FROM --platform=$TARGETPLATFORM alpine:3.20
RUN apk add --no-cache ca-certificates tzdata
COPY --from=builder /app /usr/local/bin/app
EXPOSE 8080
USER 65534:65534
ENTRYPOINT ["/usr/local/bin/app"]

# Note:
# - Le immagini base (golang, alpine, ubuntu, ecc.) sono gia` multi-arch
# - Se si installa software nativo (C libraries), assicurarsi che
#   i pacchetti siano disponibili per tutte le architetture target
# - Per dipendenze binarie platform-specific, usare condizionali
#   basate su TARGETARCH
```

---

## Networking Avanzato dei Container

### Modelli di Rete

```
Docker e Podman supportano diversi driver di rete, ognuno con trade-off
specifici in termini di isolamento, performance e complessita`.

Tipo            │ Isolamento │ Performance │ Caso d'Uso
────────────────┼────────────┼─────────────┼──────────────────────────
bridge (default)│ Medio      │ Buona       │ Sviluppo, singolo host
host            │ Nessuno    │ Massima     │ Performance-critical apps
macvlan         │ Alto       │ Ottima      │ Container con IP sulla LAN
ipvlan (L2/L3)  │ Alto       │ Ottima      │ Ambienti con restrizioni MAC
overlay         │ Alto       │ Media       │ Swarm/multi-host
none            │ Massimo    │ N/A         │ Container batch/offline

Architettura bridge con veth pairs:

  Host namespace                Container namespace
  ┌─────────────┐              ┌─────────────────┐
  │ eth0        │              │ eth0 (172.17.0.2)│
  │ 192.168.1.10│              │       │          │
  │      │      │              │       │          │
  │ docker0     │              └───────┼──────────┘
  │ (bridge)    │                      │
  │ 172.17.0.1  │──── veth pair ───────┘
  │      │      │
  │ iptables    │
  │ NAT/FORWARD │
  └─────────────┘
```

### Macvlan — Container con IP sulla LAN

```bash
# Macvlan assegna un indirizzo MAC e IP unico ad ogni container,
# rendendolo visibile sulla rete fisica come un host reale.

# Creare rete macvlan (Docker)
docker network create -d macvlan \
    --subnet=192.168.1.0/24 \
    --gateway=192.168.1.1 \
    -o parent=eth0 \
    lan_network

# Avviare container con IP fisso sulla LAN
docker run -d --name web-lan \
    --network lan_network \
    --ip 192.168.1.50 \
    nginx:alpine

# Il container e` ora raggiungibile da qualsiasi host sulla LAN
# come se fosse una macchina fisica con IP 192.168.1.50

# ATTENZIONE: l'host NON puo` comunicare direttamente con i container
# macvlan sulla stessa interfaccia (limitazione del kernel).
# Workaround: creare una sub-interfaccia macvlan sull'host
ip link add macvlan-host link eth0 type macvlan mode bridge
ip addr add 192.168.1.200/32 dev macvlan-host
ip link set macvlan-host up
ip route add 192.168.1.50/32 dev macvlan-host

# Podman: stessa sintassi con podman network create
podman network create -d macvlan \
    --subnet=192.168.1.0/24 \
    --gateway=192.168.1.1 \
    -o parent=eth0 \
    lan_network
```

### DNS e Service Discovery

```bash
# Docker embedded DNS server (127.0.0.11) risolve automaticamente
# i nomi dei container sulla stessa user-defined network.

# Creare network e container
docker network create app-net
docker run -d --name postgres --network app-net postgres:16-alpine
docker run -d --name api --network app-net myapp:latest

# Dal container 'api', 'postgres' si risolve automaticamente
docker exec api getent hosts postgres
# 172.20.0.2  postgres

# Con Docker Compose, il DNS risolve i nomi dei servizi:
# services:
#   api:
#     environment:
#       DATABASE_URL: postgresql://user:pass@postgres:5432/mydb
#   postgres:
#     image: postgres:16-alpine
# 'postgres' nel connection string si risolve automaticamente

# Podman pods: i container nello stesso pod condividono localhost
podman pod create --name myapp -p 8080:8080 -p 5432:5432
podman run -d --pod myapp --name db postgres:16-alpine
podman run -d --pod myapp --name api myapp:latest
# 'api' raggiunge postgres su localhost:5432 (stesso network namespace)

# Debugging DNS
docker exec api nslookup postgres
docker exec api dig postgres
# Se DNS non funziona, verificare:
# 1. Entrambi i container sulla stessa network
# 2. Network e` user-defined (non default bridge!)
# 3. Container non in stato unhealthy
```

---

## Orchestrazione Container

### Docker Swarm — Fondamenti

Docker Swarm è l'orchestratore nativo di Docker. Più semplice di Kubernetes, adatto per cluster di piccola/media dimensione.

```bash
# Inizializzare Swarm (sul nodo manager)
docker swarm init --advertise-addr 192.168.1.10

# Aggiungere worker (il comando è fornito dall'init)
docker swarm join --token SWMTKN-xxx 192.168.1.10:2377

# Aggiungere manager aggiuntivi
docker swarm join-token manager  # Mostra il comando con token manager

# Gestione nodi
docker node ls                   # Lista nodi del cluster
docker node inspect node-name
docker node promote node-name    # Worker → manager
docker node demote node-name     # Manager → worker
docker node update --availability drain node-name  # Evacuare nodo

# Servizi (equivalente di docker run per Swarm)
docker service create --name web --replicas 3 -p 8080:80 nginx
docker service ls
docker service ps web            # Dove girano le repliche
docker service logs web
docker service scale web=5       # Scalare
docker service update --image nginx:1.26 web  # Rolling update
docker service rm web

# Stack (equivalente di Compose per Swarm)
docker stack deploy -c compose.yml mystack
docker stack ls
docker stack services mystack
docker stack rm mystack

# Rete overlay (automatica in Swarm)
docker network create --driver overlay --attachable my-overlay

# Swarm routing mesh: qualsiasi nodo può ricevere traffico su -p
# e lo instrada al container corretto, anche se non è su quel nodo
```

### Kubernetes — Introduzione

Kubernetes (K8s) è l'orchestratore container standard per produzione su larga scala. Trattato in dettaglio nella cartella `06-KUBERNETES`. Qui una panoramica dei concetti fondamentali.

```
Architettura Kubernetes:

┌─────────────────────────────────────────────────────────┐
│                    Control Plane                         │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌────────┐│
│  │kube-api  │  │ scheduler │  │controller │  │  etcd  ││
│  │server    │  │           │  │manager    │  │        ││
│  └──────────┘  └───────────┘  └──────────┘  └────────┘│
└──────────────────────┬──────────────────────────────────┘
                       │
     ┌─────────────────┼─────────────────┐
     │                 │                 │
┌────▼────┐      ┌────▼────┐      ┌────▼────┐
│ Worker  │      │ Worker  │      │ Worker  │
│  Node   │      │  Node   │      │  Node   │
│┌───────┐│      │┌───────┐│      │┌───────┐│
││kubelet ││      ││kubelet ││      ││kubelet ││
│├───────┤│      │├───────┤│      │├───────┤│
││kube-  ││      ││kube-  ││      ││kube-  ││
││proxy  ││      ││proxy  ││      ││proxy  ││
│├───────┤│      │├───────┤│      │├───────┤│
││ Pods  ││      ││ Pods  ││      ││ Pods  ││
│└───────┘│      │└───────┘│      │└───────┘│
└─────────┘      └─────────┘      └─────────┘
```

Concetti chiave:

| Risorsa | Funzione |
|---------|----------|
| **Pod** | Unità minima di deploy, uno o più container che condividono rete e storage |
| **Deployment** | Gestisce repliche di Pod, rolling update, rollback |
| **Service** | Astrazione di rete stabile (DNS, IP) per un set di Pod |
| **Ingress** | Reverse proxy Layer 7 per esporre servizi HTTP/S |
| **ConfigMap** | Configurazione esternalizzata |
| **Secret** | Dati sensibili (base64, non cifrati di default) |
| **PersistentVolume** | Storage persistente |
| **Namespace** | Isolamento logico delle risorse |

```bash
# Comandi kubectl essenziali
kubectl get pods
kubectl get services
kubectl get deployments
kubectl describe pod pod-name
kubectl logs pod-name
kubectl exec -it pod-name -- bash
kubectl apply -f deployment.yaml
kubectl delete -f deployment.yaml

# Per approfondimento completo → cartella 06-KUBERNETES
```

---

## Monitoraggio Container

### docker stats

```bash
# Statistiche real-time di tutti i container
docker stats

# Container specifico
docker stats web api db

# Output formattato (per script)
docker stats --no-stream --format \
  "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}\t{{.PIDs}}"

# Metriche disponibili:
# CPU%     — percentuale CPU usata
# MEM USAGE/LIMIT — RAM usata / limite
# MEM%     — percentuale RAM usata
# NET I/O  — traffico rete in/out
# BLOCK I/O — I/O disco letto/scritto
# PIDS     — numero di processi

# Esportare metriche periodicamente (per analisi)
while true; do
  docker stats --no-stream --format \
    '{{.Name}},{{.CPUPerc}},{{.MemPerc}},{{.NetIO}}' >> /tmp/docker-metrics.csv
  sleep 60
done
```

### cAdvisor

cAdvisor (Container Advisor) è un tool Google per monitoraggio dettagliato dei container. Fornisce statistiche in tempo reale, grafici, e endpoint Prometheus.

```bash
# Avviare cAdvisor come container
docker run -d \
  --name cadvisor \
  --volume=/:/rootfs:ro \
  --volume=/var/run:/var/run:ro \
  --volume=/sys:/sys:ro \
  --volume=/var/lib/docker/:/var/lib/docker:ro \
  --volume=/dev/disk/:/dev/disk:ro \
  --publish=8080:8080 \
  --privileged \
  --device=/dev/kmsg \
  gcr.io/cadvisor/cadvisor:latest

# Dashboard web: http://localhost:8080
# Metriche Prometheus: http://localhost:8080/metrics
# API JSON: http://localhost:8080/api/v2.1/machine

# Metriche cAdvisor esportate:
# container_cpu_usage_seconds_total
# container_memory_usage_bytes
# container_memory_working_set_bytes
# container_network_receive_bytes_total
# container_network_transmit_bytes_total
# container_fs_usage_bytes
# container_fs_reads_total
# container_fs_writes_total
```

### Metriche Prometheus

```bash
# Abilitare le metriche Prometheus di Docker daemon
# /etc/docker/daemon.json:
# {
#   "metrics-addr": "0.0.0.0:9323",
#   "experimental": true
# }

# Endpoint: http://localhost:9323/metrics
# Metriche: engine_daemon_container_states_containers (running, paused, stopped)
#           builder_builds_triggered_total
#           engine_daemon_health_checks_total

# Stack di monitoraggio completo con Compose
# compose-monitoring.yml:
# services:
#   prometheus:
#     image: prom/prometheus
#     volumes:
#       - ./prometheus.yml:/etc/prometheus/prometheus.yml
#       - prom-data:/prometheus
#     ports:
#       - "9090:9090"
#
#   grafana:
#     image: grafana/grafana
#     volumes:
#       - grafana-data:/var/lib/grafana
#     ports:
#       - "3000:3000"
#     environment:
#       - GF_SECURITY_ADMIN_PASSWORD=admin
#
#   cadvisor:
#     image: gcr.io/cadvisor/cadvisor
#     volumes:
#       - /:/rootfs:ro
#       - /var/run:/var/run:ro
#       - /sys:/sys:ro
#       - /var/lib/docker/:/var/lib/docker:ro
#     ports:
#       - "8080:8080"
#
#   node-exporter:
#     image: prom/node-exporter
#     ports:
#       - "9100:9100"
#
# volumes:
#   prom-data:
#   grafana-data:

# Prometheus config — prometheus.yml:
# global:
#   scrape_interval: 15s
# scrape_configs:
#   - job_name: 'docker'
#     static_configs:
#       - targets: ['host.docker.internal:9323']
#   - job_name: 'cadvisor'
#     static_configs:
#       - targets: ['cadvisor:8080']
#   - job_name: 'node'
#     static_configs:
#       - targets: ['node-exporter:9100']
```

---

## Debugging Container

### docker exec e docker cp

```bash
# Shell nel container (metodo più comune)
docker exec -it web bash
docker exec -it web sh         # Per immagini Alpine/distroless con sh

# Eseguire come root anche se il container gira come non-root
docker exec -u 0 web bash

# Comandi diagnostici dentro il container
docker exec web cat /etc/resolv.conf    # Configurazione DNS
docker exec web cat /etc/hosts          # Hosts file
docker exec web env                     # Variabili d'ambiente
docker exec web df -h                   # Spazio disco
docker exec web free -h                 # Memoria (se disponibile)
docker exec web ss -tuln                # Porte in ascolto
docker exec web ip addr                 # Interfacce di rete

# Copiare file per analisi
docker cp web:/var/log/nginx/error.log ./error.log
docker cp web:/etc/nginx/nginx.conf ./nginx-debug.conf

# Debug container con immagine minimal (no shell)
# Usare un container debug nello stesso network namespace
docker run -it --rm \
  --pid=container:web \
  --network=container:web \
  nicolaka/netshoot bash
# Ora hai accesso a tutti i tool di debugging con la stessa rete del container

# Container di debug con immagine distroless (nessun shell)
# Docker 28+: debug mode
docker debug web
# Aggiunge temporaneamente un layer con shell e tool di debug
```

### nsenter — Entrare nei namespace

`nsenter` permette di eseguire comandi nei namespace di un processo esistente. Utile quando il container non ha shell o tool diagnostici.

```bash
# Ottenere il PID del container
CONTAINER_PID=$(docker inspect --format '{{.State.Pid}}' web)

# Entrare in tutti i namespace del container
sudo nsenter -t $CONTAINER_PID -m -u -i -n -p -- bash

# Entrare solo nel network namespace
sudo nsenter -t $CONTAINER_PID -n -- ss -tuln
sudo nsenter -t $CONTAINER_PID -n -- ip addr
sudo nsenter -t $CONTAINER_PID -n -- tcpdump -i eth0 -c 20

# Entrare solo nel mount namespace
sudo nsenter -t $CONTAINER_PID -m -- ls -la /app/

# Entrare solo nel PID namespace
sudo nsenter -t $CONTAINER_PID -p -- ps aux

# Opzioni nsenter:
# -t PID  → target process
# -m      → mount namespace
# -u      → UTS namespace (hostname)
# -i      → IPC namespace
# -n      → network namespace
# -p      → PID namespace
# -C      → cgroup namespace
# -U      → user namespace
```

### strace in container

```bash
# strace richiede SYS_PTRACE capability (droppata di default)
docker run -d --cap-add=SYS_PTRACE --name debug-web nginx

# strace dal container (se strace è installato)
docker exec debug-web strace -p 1 -f -e trace=network

# strace dall'host via nsenter (il container non ha bisogno di strace)
CONTAINER_PID=$(docker inspect --format '{{.State.Pid}}' debug-web)
sudo nsenter -t $CONTAINER_PID -p -m -- strace -p 1 -f -e trace=open,read,write

# Alternativa: usare un container sidecar con strace
docker run -it --rm \
  --pid=container:web \
  --cap-add=SYS_PTRACE \
  alpine sh -c "apk add strace && strace -p 1 -f"

# Filtri strace utili:
# -e trace=network       → chiamate di rete (socket, connect, bind)
# -e trace=file          → operazioni su file (open, read, write, stat)
# -e trace=process       → fork, exec, exit
# -e trace=signal        → gestione segnali
# -e trace=memory        → mmap, mprotect, brk
# -c                     → statistiche aggregate (conteggio syscall)
```

### Core dumps

```bash
# Abilitare core dump nel container
docker run -d \
  --ulimit core=-1 \
  -v /tmp/cores:/cores \
  -e GOTRACEBACK=crash \
  myapp

# Configurare il pattern di core dump sull'host
echo "/cores/core.%e.%p.%t" | sudo tee /proc/sys/kernel/core_pattern

# Analizzare un core dump
# gdb /path/to/binary /cores/core.myapp.12345.1716393600
# (gdb) bt        → backtrace
# (gdb) info threads
# (gdb) thread apply all bt

# Per applicazioni Go
# GOTRACEBACK=crash fa sì che Go scriva un core dump su crash
# Analizzare con dlv (Delve):
# dlv core /path/to/binary /cores/core.myapp.12345

# Per applicazioni Python (segfault in estensioni C)
# pip install faulthandler
# python -X faulthandler app.py
```

### Container Healthcheck Avanzati

```bash
# Un healthcheck ben progettato e` essenziale per orchestratori
# (Swarm, Kubernetes) e per restart automatici. Non basta verificare
# che il processo sia in esecuzione: bisogna verificare che il servizio
# sia effettivamente funzionante e in grado di servire richieste.

# Healthcheck in Dockerfile
# HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=10s \
#   CMD curl -f http://localhost:8080/health || exit 1

# Healthcheck piu` robusto: verifica anche connessione al database
# HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=30s \
#   CMD ["/app/healthcheck"]

# Esempio script healthcheck dedicato (healthcheck.sh):
#!/bin/bash
set -euo pipefail

# Verifica HTTP endpoint
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health)
if [ "$HTTP_STATUS" != "200" ]; then
    echo "HTTP check failed: status $HTTP_STATUS"
    exit 1
fi

# Verifica connessione database (se applicabile)
if ! pg_isready -h localhost -p 5432 -q 2>/dev/null; then
    echo "Database connection failed"
    exit 1
fi

# Verifica spazio disco nel container
DISK_PCT=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$DISK_PCT" -gt 90 ]; then
    echo "Disk usage critical: ${DISK_PCT}%"
    exit 1
fi

echo "Healthy"
exit 0

# Healthcheck da CLI (override runtime)
docker run -d \
    --health-cmd "curl -f http://localhost:8080/health || exit 1" \
    --health-interval 30s \
    --health-timeout 5s \
    --health-retries 3 \
    --health-start-period 15s \
    --name api myapp:latest

# Monitorare stato health
docker inspect --format '{{json .State.Health}}' api | python3 -m json.tool
# {
#     "Status": "healthy",
#     "FailingStreak": 0,
#     "Log": [...]
# }

# Filtrare container unhealthy
docker ps --filter health=unhealthy --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"

# Con Podman: stessa sintassi. Podman supporta anche healthcheck
# in pod definition via Kubernetes YAML
podman pod create --name myapp
podman run -d --pod myapp \
    --health-cmd "curl -sf http://localhost:8080/health" \
    --health-interval 30s \
    --name api myapp:latest
podman healthcheck run api
```

### Resource Limits e OOM Management

```bash
# Impostare limiti CPU e memoria e` critico per evitare che un container
# rogue consumi tutte le risorse dell'host.

# Limiti memoria
docker run -d \
    --memory=512m \
    --memory-swap=1g \
    --memory-reservation=256m \
    --name app myapp:latest

# --memory: hard limit (OOM kill se superato)
# --memory-swap: limite swap+ram combinato (1g = 512m RAM + 512m swap)
# --memory-reservation: soft limit (il kernel cerca di rispettarlo)

# Limiti CPU
docker run -d \
    --cpus=2.0 \
    --cpu-shares=512 \
    --cpuset-cpus="0,1" \
    --name app myapp:latest

# --cpus: numero di CPU equivalenti (2.0 = max 200% CPU time)
# --cpu-shares: peso relativo (default 1024, 512 = meta` priorita`)
# --cpuset-cpus: pin a CPU specifiche (utile per NUMA)

# Verificare limiti effettivi dentro il container
docker exec app cat /sys/fs/cgroup/memory.max        # cgroup v2
docker exec app cat /sys/fs/cgroup/cpu.max           # cgroup v2
# Output cpu.max: "200000 100000" → 2.0 CPU (200ms ogni 100ms periodo)

# Gestione OOM (Out of Memory)
# Quando un container supera --memory, il kernel lo OOM-killa
# Controllare se un container e` stato OOM-killed:
docker inspect --format '{{.State.OOMKilled}}' app
# true → il container e` stato terminato per esaurimento memoria

# Disabilitare OOM killer (PERICOLOSO, usare solo in casi specifici)
# docker run -d --oom-kill-disable --memory=512m myapp
# ATTENZIONE: senza OOM killer, il container puo` far swappare l'intero host

# Podman: stessa sintassi, inoltre supporta --memory-swappiness
podman run -d --memory=512m --memory-swappiness=10 --name app myapp:latest
```

---

## systemd e Container

### Container come servizi systemd

Eseguire container come servizi systemd permette gestione automatica (avvio al boot, restart, dipendenze, log via journal).

```bash
# ============================================================
# Docker: container come servizio systemd
# ============================================================
cat > /etc/systemd/system/docker-web.service << 'UNIT_EOF'
[Unit]
Description=Nginx Web Container
After=docker.service
Requires=docker.service

[Service]
Type=simple
Restart=always
RestartSec=10

# Pulizia: rimuovi container precedente (se esiste)
ExecStartPre=-/usr/bin/docker rm -f web

# Avvia container
ExecStart=/usr/bin/docker run --rm --name web \
  -p 8080:80 \
  --memory=256m \
  --cpus=0.5 \
  --read-only \
  --tmpfs /var/cache/nginx:size=10m \
  --tmpfs /run:size=5m \
  --cap-drop=ALL \
  --cap-add=NET_BIND_SERVICE \
  nginx:1.25-alpine

# Stop
ExecStop=/usr/bin/docker stop -t 30 web

[Install]
WantedBy=multi-user.target
UNIT_EOF

sudo systemctl daemon-reload
sudo systemctl enable --now docker-web.service
sudo systemctl status docker-web.service
journalctl -u docker-web.service -f   # Log

# ============================================================
# Podman: container come servizio systemd (utente)
# ============================================================
# Generare automaticamente
podman generate systemd --name web --new --files
mv container-web.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now container-web.service
loginctl enable-linger $USER   # Sopravvive al logout
```

### Quadlet — Integrazione nativa

Quadlet è l'evoluzione di `podman generate systemd`. Definisce container direttamente come unità systemd con file `.container`, `.volume`, `.network`, `.kube`.

```bash
# ============================================================
# File Quadlet — /etc/containers/systemd/ (root)
# oppure ~/.config/containers/systemd/ (utente)
# ============================================================

# web.container
cat > ~/.config/containers/systemd/web.container << 'QUADLET_EOF'
[Unit]
Description=Nginx Web Server
After=local-fs.target

[Container]
Image=docker.io/nginx:1.25-alpine
ContainerName=web
PublishPort=8080:80
Volume=web-html.volume:/usr/share/nginx/html:ro
Network=app.network
ReadOnly=true
# Tmpfs per directory scrivibili
Tmpfs=/var/cache/nginx:size=10m
Tmpfs=/run:size=5m
# Sicurezza
DropCapability=ALL
AddCapability=CAP_NET_BIND_SERVICE
NoNewPrivileges=true
# Risorse
Memory=256M
# Healthcheck
HealthCmd=curl -sf http://localhost:80/ || exit 1
HealthInterval=30s
HealthTimeout=5s
HealthRetries=3

[Service]
Restart=always
RestartSec=10
TimeoutStartSec=60

[Install]
WantedBy=default.target
QUADLET_EOF

# web-html.volume
cat > ~/.config/containers/systemd/web-html.volume << 'VOL_EOF'
[Volume]
# Volume gestito da Podman
VOL_EOF

# app.network
cat > ~/.config/containers/systemd/app.network << 'NET_EOF'
[Network]
Subnet=172.20.0.0/24
Gateway=172.20.0.1
NET_EOF

# Ricaricare e avviare
systemctl --user daemon-reload
systemctl --user start web.service     # .container diventa .service
systemctl --user status web.service

# Quadlet supporta anche file .kube per manifesti Kubernetes
# myapp.kube:
# [Kube]
# Yaml=/path/to/pod.yaml
# PublishPort=8080:80
```

---

## Best Practices — Checklist Produzione

### Immagini

- [ ] Usare immagini base minimali: distroless > Alpine > slim > full
- [ ] Tag specifico, mai `:latest` in produzione (es. `nginx:1.25.3-alpine`)
- [ ] Multi-stage build per separare build da runtime
- [ ] Un processo per container
- [ ] Layer ordering ottimizzato per cache (dipendenze prima, codice dopo)
- [ ] `.dockerignore` completo (`.git`, `node_modules`, `.env`, test)
- [ ] Nessun segreto nell'immagine (no `COPY .env`, no `ARG PASSWORD`)
- [ ] LABEL con metadati (versione, maintainer, VCS ref)
- [ ] HEALTHCHECK definito nel Dockerfile
- [ ] Scan vulnerabilità integrato nella CI (trivy/grype, blocco su CRITICAL)
- [ ] Immagini firmate (cosign)

### Runtime e sicurezza

- [ ] Container gira come utente non-root (`USER` nel Dockerfile)
- [ ] `--cap-drop=ALL` + aggiungere solo le capability necessarie
- [ ] `--read-only` con tmpfs per directory temporanee
- [ ] `--security-opt=no-new-privileges`
- [ ] Limiti risorse: `--memory`, `--cpus`, `--pids-limit`
- [ ] Port binding solo su localhost in produzione (`-p 127.0.0.1:PORT:PORT`)
- [ ] Mai `--privileged` in produzione
- [ ] Mai montare Docker socket nel container (a meno di estrema necessità)
- [ ] Secrets gestiti tramite file mount o secret manager, mai variabili d'ambiente
- [ ] Network segmentation (reti interne per backend, esposte per frontend)

### Operazioni

- [ ] Restart policy configurata (`--restart=unless-stopped`)
- [ ] Log rotation configurata (`--log-opt max-size=10m --log-opt max-file=3`)
- [ ] Monitoraggio attivo (cAdvisor / Prometheus / docker stats)
- [ ] Backup automatici dei volumi
- [ ] Pulizia periodica (`docker system prune`)
- [ ] Aggiornamento regolare delle immagini base (patch di sicurezza)
- [ ] CI/CD pipeline con build → test → scan → sign → push → deploy
- [ ] Rollback plan documentato

### Compose / Orchestrazione

- [ ] `depends_on` con `condition: service_healthy` per dipendenze
- [ ] Healthcheck definito per ogni servizio
- [ ] Reti separate per frontend e backend
- [ ] Volumi named per dati persistenti (no bind mount in produzione)
- [ ] `deploy.resources.limits` per ogni servizio
- [ ] Profili per separare dev/test/prod

---

## Troubleshooting — Problemi Comuni

### 1. Container esce immediatamente (exit 0 o 1)

```bash
docker logs container_name
# Cause comuni: CMD che fallisce, file mancante, variabile d'ambiente non impostata
# Test: docker run -it image bash   (o sh per Alpine)
# Verificare exit code: docker inspect --format '{{.State.ExitCode}}' container
# Exit 0: comando completato (container one-shot). Normale per CMD come echo/ls
# Exit 1: errore generico. Leggere i log
# Exit 137: OOM kill (SIGKILL). Aumentare --memory
# Exit 139: Segfault (SIGSEGV). Bug nel codice
# Exit 143: SIGTERM ricevuto (docker stop normale)
```

### 2. Porta già in uso

```bash
ss -tuln | grep PORT
# Trovare il processo: sudo lsof -i :8080
# Cambiare mapping: -p 8081:80
# O fermare il servizio conflittuale: sudo systemctl stop nginx
```

### 3. Spazio disco esaurito da Docker

```bash
docker system df                    # Vedere l'uso
docker system df -v                 # Dettagliato
docker system prune -a              # Pulizia aggressiva
docker volume prune                 # Volumi orfani
# Configurare log rotation:
# /etc/docker/daemon.json: {"log-opts": {"max-size": "10m", "max-file": "3"}}
# Spostare data directory Docker:
# /etc/docker/daemon.json: {"data-root": "/mnt/docker-data"}
```

### 4. Container non raggiunge internet

```bash
# Verificare DNS
docker run --rm alpine nslookup google.com
# Se fallisce: problema DNS Docker
# Fix: /etc/docker/daemon.json con {"dns": ["8.8.8.8", "1.1.1.1"]}
# Poi: sudo systemctl restart docker

# Verificare routing
docker run --rm alpine traceroute -m 5 8.8.8.8
# Verificare iptables
sudo iptables -t nat -L DOCKER -n -v
# Verificare IP forwarding
cat /proc/sys/net/ipv4/ip_forward   # Deve essere 1
# Fix: sudo sysctl net.ipv4.ip_forward=1
```

### 5. Permessi negati su volume montato

```bash
# L'utente nel container (es. UID 1000) non ha permessi sulla directory host
# Verificare: docker exec web id    → uid=1000(appuser)
# Fix 1: chown sull'host
sudo chown -R 1000:1000 /host/path
# Fix 2: usare un volume Docker gestito (non bind mount)
docker volume create mydata
# Fix 3: usare --user per matchare l'utente host
docker run --user $(id -u):$(id -g) -v $(pwd):/app myimage
# Fix 4: aggiungere :z o :Z per SELinux
docker run -v /data:/data:z myimage
```

### 6. Container non raggiunge altro container

```bash
# Sulla rete bridge default i container non si vedono per nome (no DNS)
# Soluzione: creare una rete custom
docker network create mynet
docker run -d --name web --network mynet nginx
docker run -d --name app --network mynet myapp
# Ora app può raggiungere web: curl http://web:80

# Container su reti diverse non comunicano
docker network connect shared-net container_isolato
```

### 7. Immagine non scaricabile (pull fail)

```bash
# Errore: "Error response from daemon: manifest unknown"
# → Tag non esiste. Verificare i tag disponibili:
skopeo list-tags docker://docker.io/library/nginx
# oppure visitare Docker Hub

# Errore: "toomanyrequests: Too Many Requests"
# → Rate limit Docker Hub raggiunto
# Fix: docker login (account autenticato ha limiti più alti)
# Fix: usare mirror/proxy cache
# /etc/docker/daemon.json: {"registry-mirrors": ["https://mirror.gcr.io"]}

# Errore: "x509: certificate signed by unknown authority"
# → Registry con certificato self-signed
# Fix: /etc/docker/daemon.json: {"insecure-registries": ["myregistry:5000"]}
# Meglio: aggiungere il CA cert a /etc/docker/certs.d/myregistry:5000/ca.crt
```

### 8. OOM Kill — Container ucciso per eccesso di memoria

```bash
# Verificare se il container è stato OOM-killed
docker inspect --format '{{.State.OOMKilled}}' container
# true → il kernel ha ucciso il container

# Verificare nei log del kernel
dmesg | grep -i oom
journalctl -k | grep -i "out of memory"

# Soluzioni:
# 1. Aumentare il limite di memoria
docker update --memory=1g container
# 2. Indagare il memory leak nell'applicazione
docker stats container  # Monitorare la crescita
# 3. Usare memory-reservation (soft limit) + memory (hard limit)
docker run -d --memory=1g --memory-reservation=512m myapp
```

### 9. Container lento / high CPU

```bash
# Identificare il container problematico
docker stats --no-stream

# Ispezionare i processi
docker top container
docker exec container top -b -n 1

# Verificare throttling CPU
cat /sys/fs/cgroup/$(docker inspect --format '{{.State.Pid}}' container)/cpu.stat
# nr_throttled: numero di volte che il container è stato rallentato
# throttled_time: tempo totale di throttling in ns

# Profiling (se l'applicazione lo supporta)
docker exec container kill -SIGUSR1 1   # Trigger profile dump (Node.js, Go, etc.)
```

### 10. Build lento / cache non funziona

```bash
# Verificare che BuildKit sia abilitato
DOCKER_BUILDKIT=1 docker build .

# Verificare l'ordine dei layer nel Dockerfile
# COPY dei file che cambiano spesso DEVE essere DOPO le istruzioni stabili

# Cache mount per package manager
# RUN --mount=type=cache,target=/var/cache/apt apt-get install -y curl

# Utilizzare --cache-from per CI (dove non c'è cache locale)
docker build --cache-from myregistry.com/myapp:cache -t myapp .

# Cache esterna con buildx
docker buildx build \
  --cache-to type=registry,ref=myregistry.com/myapp:cache \
  --cache-from type=registry,ref=myregistry.com/myapp:cache \
  -t myapp .
```

### 11. Volume dati corrotti / inconsistenti

```bash
# Verificare integrità del volume
docker run --rm -v mydata:/data alpine ls -la /data
docker run --rm -v mydata:/data alpine df -h /data

# Backup prima di qualsiasi intervento
docker run --rm -v mydata:/data -v $(pwd):/backup alpine \
  tar czf /backup/emergency-backup.tar.gz -C /data .

# Per database: usare i tool nativi per check/repair
docker exec db pg_isready -U user         # PostgreSQL health
docker exec db mysqlcheck --all-databases  # MySQL check
```

### 12. Conflitto di rete / subnet overlap

```bash
# Docker default usa 172.17.0.0/16 per bridge
# Se conflitto con rete aziendale:
# /etc/docker/daemon.json:
# {
#   "bip": "10.200.0.1/24",
#   "default-address-pools": [
#     {"base": "10.201.0.0/16", "size": 24}
#   ]
# }
```

### 13. Container non riceve SIGTERM (graceful shutdown fallisce)

```bash
# Il problema: il container non si ferma con "docker stop"
# Docker aspetta il timeout (10s) poi invia SIGKILL

# Causa 1: shell form di CMD (PID 1 = /bin/sh, non l'app)
# ✗ CMD node server.js         → /bin/sh -c "node server.js" (PID 1 = sh)
# ✓ CMD ["node", "server.js"] → node server.js (PID 1 = node)

# Causa 2: l'applicazione non gestisce SIGTERM
# Soluzione: aggiungere handler nell'app
# Node.js: process.on('SIGTERM', () => { server.close(); });
# Python: signal.signal(signal.SIGTERM, handler)

# Causa 3: init system necessario
# Usare --init per aggiungere tini come PID 1
docker run -d --init myapp
# Tini inoltra i segnali correttamente ai processi figli
```

### 14. Layer troppo grandi

```bash
# Trovare layer grandi
docker history myapp:v1.0 --no-trunc

# Cause comuni:
# - apt-get senza --no-install-recommends
# - Mancata pulizia di cache/temp nella stessa RUN
# - COPY di file non necessari (manca .dockerignore)
# - Layer di build inclusi nell'immagine finale (usare multi-stage)

# Analisi con dive (tool di analisi layer)
# https://github.com/wagoodman/dive
dive myapp:v1.0
# Mostra: layer per layer, file aggiunti/rimossi, spreco di spazio
```

### 15. Docker socket esposto — rischio sicurezza

```bash
# Mai montare il Docker socket in un container in produzione
# -v /var/run/docker.sock:/var/run/docker.sock
# Chi ha accesso al socket ha accesso ROOT all'host

# Se assolutamente necessario (CI/CD runner, monitoring):
# 1. Usare un proxy read-only come tecnwebsolutions/docker-socket-proxy
docker run -d \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e CONTAINERS=1 -e INFO=1 -e IMAGES=1 \
  -p 2375:2375 \
  tecnwebsolutions/docker-socket-proxy
# 2. Settare DOCKER_HOST=tcp://proxy:2375 nei container che necessitano accesso
```

### 16. Errore "no space left on device" durante il build

```bash
# Lo spazio su /var/lib/docker è esaurito
df -h /var/lib/docker

# Pulizia aggressiva
docker builder prune -a    # Cache di build
docker system prune -a     # Tutto il non usato

# Se il disco è pieno anche dopo la pulizia, spostare la data directory
# /etc/docker/daemon.json: {"data-root": "/mnt/larger-disk/docker"}
# sudo systemctl restart docker
```

### 17. Container ha IP vecchio dopo restart della rete

```bash
# Docker non garantisce lo stesso IP dopo restart
# Soluzione: usare sempre i nomi DNS (reti custom) per comunicare
# Se serve IP fisso:
docker network create --subnet 172.20.0.0/24 mynet
docker run -d --network mynet --ip 172.20.0.10 --name web nginx
```

### 18. docker compose up ignora le modifiche al Dockerfile

```bash
# Compose non ricostruisce automaticamente
docker compose up -d --build           # Forza rebuild
docker compose build --no-cache api    # Rebuild senza cache di un servizio
```

### 19. Errore "ERRO[0000] error waiting for container" / container in stato "removal in progress"

```bash
# Container bloccato in fase di rimozione
# Causa: mount busy o processo zombie
docker rm -f container_name

# Se persiste:
sudo systemctl restart docker
# Ultima risorsa: rimuovere manualmente da /var/lib/docker/containers/
```

### 20. Time zone errato nel container

```bash
# I container usano UTC di default
# Fix 1: variabile d'ambiente (se l'immagine la supporta)
docker run -e TZ=Europe/Rome myapp

# Fix 2: montare il timezone dell'host
docker run -v /etc/localtime:/etc/localtime:ro -v /etc/timezone:/etc/timezone:ro myapp

# Fix 3: nel Dockerfile
ENV TZ=Europe/Rome
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
```

### 21. Health check fallisce ma l'app funziona

```bash
# Verificare il comando healthcheck
docker inspect --format '{{json .State.Health}}' container | jq .

# Cause comuni:
# - Il tool di healthcheck (curl/wget) non è installato nell'immagine
# - Il servizio non è ancora pronto (start_period troppo breve)
# - Il timeout è troppo stretto

# Fix: usare start_period adeguato
# healthcheck:
#   test: ["CMD", "curl", "-sf", "http://localhost:8080/health"]
#   interval: 30s
#   timeout: 10s
#   retries: 3
#   start_period: 60s    # Grazia iniziale di 60 secondi
```

### 22. Errore "Cannot connect to the Docker daemon"

```bash
# Verificare che Docker sia in esecuzione
sudo systemctl status docker

# Verificare i permessi del socket
ls -la /var/run/docker.sock
# srw-rw---- 1 root docker ...

# L'utente deve essere nel gruppo "docker"
groups $USER | grep docker
# Se manca: sudo usermod -aG docker $USER && newgrp docker

# Per Docker rootless:
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/docker.sock
```

---

## Migrazione Docker → Podman

### Prerequisiti

```bash
# Installare Podman e tool correlati
sudo apt install podman podman-compose buildah skopeo

# Verificare la versione
podman --version

# Configurare registries
mkdir -p ~/.config/containers
cat > ~/.config/containers/registries.conf << 'REG_EOF'
unqualified-search-registries = ["docker.io", "quay.io", "ghcr.io"]

[[registry]]
location = "docker.io"
REG_EOF
```

### Mappatura comandi

La maggior parte dei comandi è identica. Differenze chiave:

| Docker | Podman | Note |
|--------|--------|------|
| `docker run` | `podman run` | Identico |
| `docker build` | `podman build` | Usa Buildah internamente |
| `docker compose` | `podman compose` / `podman-compose` | Compatibile via socket |
| `docker system prune` | `podman system prune` | Identico |
| `docker login` | `podman login` | Identico |
| `docker push/pull` | `podman push/pull` | Identico |
| N/A | `podman pod create` | Concetto esclusivo Podman |
| N/A | `podman generate kube` | Genera YAML K8s |
| N/A | `podman play kube` | Esegue YAML K8s |

### Migrazione delle immagini

```bash
# Esportare da Docker
docker save myapp:v1.0 -o myapp-v1.tar

# Importare in Podman
podman load -i myapp-v1.tar

# Oppure usare Skopeo per trasferimento diretto
skopeo copy \
  docker-daemon:myapp:v1.0 \
  containers-storage:myapp:v1.0
```

### Migrazione dei volumi

```bash
# I volumi Docker sono in /var/lib/docker/volumes/
# I volumi Podman (rootless) sono in ~/.local/share/containers/storage/volumes/

# Creare volume Podman
podman volume create mydata

# Copiare i dati
sudo tar czf /tmp/vol-backup.tar.gz -C /var/lib/docker/volumes/mydata/_data .
podman run --rm -v mydata:/data -v /tmp:/backup alpine \
  tar xzf /backup/vol-backup.tar.gz -C /data
```

### Migrazione Docker Compose → Podman

```bash
# Opzione 1: docker-compose.yml con socket Podman
systemctl --user enable --now podman.socket
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/podman/podman.sock
docker compose up -d   # Funziona con il socket Podman

# Opzione 2: podman-compose (alternativa Python)
pip install podman-compose
podman-compose up -d

# Opzione 3: Convertire in pod Kubernetes e usare podman play kube
# (per stack più complessi, migliore portabilità)
# Riscrivere compose.yml come pod.yaml Kubernetes
podman play kube pod.yaml
```

### Migrazione systemd

```bash
# Da Docker: rimuovere il servizio Docker-based
sudo systemctl stop docker-web.service
sudo systemctl disable docker-web.service

# A Podman: usare Quadlet (metodo moderno)
cat > ~/.config/containers/systemd/web.container << 'QUADLET_EOF'
[Container]
Image=docker.io/nginx:1.25-alpine
ContainerName=web
PublishPort=8080:80
ReadOnly=true
Tmpfs=/var/cache/nginx:size=10m
Tmpfs=/run:size=5m

[Service]
Restart=always

[Install]
WantedBy=default.target
QUADLET_EOF

systemctl --user daemon-reload
systemctl --user enable --now web.service
loginctl enable-linger $USER
```

### Checklist migrazione

- [ ] Installare Podman, Buildah, Skopeo
- [ ] Configurare registries (`~/.config/containers/registries.conf`)
- [ ] Configurare storage (`~/.config/containers/storage.conf`)
- [ ] Migrare immagini (docker save → podman load oppure skopeo)
- [ ] Migrare volumi (tar backup → restore in volumi Podman)
- [ ] Testare tutti i container individualmente
- [ ] Migrare Compose (socket compatibile oppure podman-compose)
- [ ] Migrare servizi systemd a Quadlet
- [ ] Verificare che le porte funzionino (rootless: porte < 1024 richiedono sysctl)
- [ ] Rimuovere Docker: `sudo apt remove docker.io docker-ce`
- [ ] Alias opzionale: `alias docker=podman` in `.bashrc`

---

## FAQ — Domande Frequenti

**1. Docker o Podman per lo sviluppo?**

Per la maggior parte degli sviluppatori, Docker rimane la scelta più immediata per l'ecosistema maturo e la compatibilità universale. Podman è preferibile se la sicurezza rootless è un requisito aziendale, se si lavora su sistemi Red Hat/Fedora, o se si vuole un percorso diretto verso Kubernetes (via `podman play kube`). I comandi sono quasi identici; la transizione è a basso attrito.

**2. Alpine o Distroless come base image?**

Alpine (~5MB) offre un buon compromesso: minimale ma con shell e package manager, utile per debugging. Distroless (Google) è ancora più minimale (no shell, no package manager), ideale per produzione hardened dove non si deve mai entrare nel container. Per sviluppo: Alpine. Per produzione con massima sicurezza: distroless. Per il compromesso migliore: slim (Debian minimal).

**3. Qual è il limite pratico di container per host?**

Dipende da risorse e workload. Un host con 32GB RAM e 8 core può gestire centinaia di container leggeri (Alpine + app Go/Rust), o decine di container pesanti (JVM, database). Il collo di bottiglia è tipicamente la RAM, poi I/O disco, poi CPU. Monitorare con `docker stats` e impostare limiti per evitare un singolo container che monopolizzi le risorse.

**4. Come gestire i log dei container in produzione?**

Non usare `json-file` senza rotation (riempie il disco). Configurare in `/etc/docker/daemon.json`: `"log-opts": {"max-size": "10m", "max-file": "3"}`. Per stack più grandi, usare un driver di log centralizzato: `fluentd`, `syslog`, o `gelf`. Aggregare in un sistema come ELK/EFK stack, Loki+Grafana, o un servizio cloud.

**5. `docker run --privileged` è mai accettabile?**

Quasi mai. `--privileged` dà accesso a tutti i device, a tutte le capability, e disabilita i profili di sicurezza. Un container privilegiato può fare container escape banalmente. Eccezioni strettamente limitate: Docker-in-Docker (DinD) per CI/CD, tool di sistema come cAdvisor. Anche in questi casi, valutare alternative (Podman in Podman non richiede privileged, Kaniko per build senza DinD).

**6. Come funziona il networking tra container su host diversi?**

Con Docker Swarm: rete overlay (VXLAN) automatica. Con Kubernetes: CNI plugin (Calico, Cilium, Flannel) gestiscono la rete tra nodi. Senza orchestratore: WireGuard VPN tra host, o macvlan con routing configurato manualmente. L'overlay è la soluzione standard per la maggior parte dei casi.

**7. Come forzare il rebuild senza cache?**

`docker build --no-cache -t myapp .` ricostruisce tutti i layer da zero. Per un singolo layer: modificare l'istruzione (anche un commento) invalida la cache da quel punto in poi. Per Compose: `docker compose build --no-cache service_name`.

**8. Container o VM per isolamento in ambienti multi-tenant?**

Per isolamento forte tra tenant non fidati: VM. Il kernel condiviso dei container è una superficie d'attacco; vulnerabilità kernel = container escape. Per microservizi dello stesso team/organizzazione: container. Per il meglio dei due mondi: Kata Containers o gVisor (container con kernel leggero isolato).

**9. Come aggiornare un container in produzione con zero downtime?**

Con un singolo host: avviare il nuovo container, verificare l'health, aggiornare il reverse proxy (nginx/traefik), fermare il vecchio. Con Docker Swarm: `docker service update --image myapp:v2.0 myservice` fa rolling update automatico. Con Kubernetes: `kubectl set image deployment/myapp myapp=myapp:v2.0` con rolling update strategy.

**10. Perché non devo usare `:latest` in produzione?**

`:latest` è un tag mutabile. Può puntare a versioni diverse nel tempo. Due `docker pull nginx:latest` a distanza di settimane possono dare immagini diverse. Questo rompe la riproducibilità. Usare tag immutabili (es. `nginx:1.25.3-alpine`) o, meglio, pin al digest SHA256: `nginx@sha256:abc123...`.

**11. Come ridurre la dimensione di un'immagine Docker?**

1. Multi-stage build (compilare in uno stage, copiare solo l'artefatto nel finale)
2. Immagine base minimale (distroless, Alpine, slim)
3. Combinare RUN e pulire nella stessa istruzione
4. `.dockerignore` completo
5. `--no-install-recommends` per apt-get
6. `--no-cache-dir` per pip
7. Rimuovere tool di build non necessari nel runtime

**12. Come debuggare un container che non ha shell (distroless)?**

Docker 28+: `docker debug container_name` aggiunge temporaneamente un layer con shell e tool. In alternativa, usare `nsenter` dall'host per entrare nei namespace. Oppure usare un container sidecar nella stessa rete/PID namespace con tool installati. Ultima risorsa: `docker cp` per estrarre file e analizzarli sull'host.

**13. Come condividere dati tra container?**

1. **Volume named**: `docker volume create shared && docker run -v shared:/data ...` per entrambi
2. **Bind mount**: stessa directory host montata in più container
3. **Network**: comunicazione via API/socket tra container
4. **tmpfs condiviso**: per dati temporanei (richiede `--ipc=shareable`)
5. In Compose: definire un volume nella sezione `volumes:` e montarlo in più servizi

**14. Docker Desktop è necessario su Linux?**

No. Su Linux, Docker Engine (CLI + daemon) è tutto ciò che serve. Docker Desktop è un wrapper con VM e GUI, utile su macOS/Windows dove non c'è un kernel Linux nativo. Su Linux aggiunge overhead senza beneficio reale. Installare `docker-ce` direttamente.

**15. Come eseguire container con GPU (CUDA)?**

```bash
# Installare NVIDIA Container Toolkit
# https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html
sudo apt install nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Usare GPU nel container
docker run --gpus all nvidia/cuda:12.3.2-base-ubuntu22.04 nvidia-smi
docker run --gpus '"device=0,1"' myapp    # GPU specifiche
docker run --gpus all -e NVIDIA_VISIBLE_DEVICES=0 myapp
```

**16. Qual è la differenza tra COPY e ADD nel Dockerfile?**

`COPY` copia file dal build context al filesystem dell'immagine. `ADD` fa lo stesso ma con due funzionalità extra: (1) auto-extraction di archivi tar locali, (2) download da URL. Preferire sempre `COPY` per chiarezza e prevedibilità. Usare `ADD` solo quando serve l'auto-extraction di un archivio locale. Per download da URL, usare `RUN curl` o `RUN wget` (permette verifica checksum e pulizia nello stesso layer).

**17. Come migrare dati tra volumi Docker su host diversi?**

```bash
# Metodo 1: tar + ssh
docker run --rm -v mydata:/data alpine tar czf - -C /data . | \
  ssh user@remote "docker run --rm -i -v mydata:/data alpine tar xzf - -C /data"

# Metodo 2: rsync (più efficiente per sync incrementali)
# Montare il volume, rsync verso l'host remoto

# Metodo 3: NFS volume condiviso tra host
docker volume create --driver local \
  --opt type=nfs \
  --opt o=addr=192.168.1.10,rw \
  --opt device=:/exports/data \
  nfs-data
```
