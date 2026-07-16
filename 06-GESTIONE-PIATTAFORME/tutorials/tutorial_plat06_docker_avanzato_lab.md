# Tutorial: Docker Avanzato — Build, Sicurezza e Supply Chain — Lab Pratico

> **Documento di riferimento:** `06-docker-avanzato.md`
> **Dominio:** Gestione Piattaforme — Container Build & Security
> **Ambito:** Architettura Docker 29.x, Dockerfile multi-stage ottimizzati, BuildKit 0.31+ mount cache, immagini distroless, build multi-architettura amd64/arm64 con buildx, container rootless, read-only filesystem, SBOM con syft, scan CVE con trivy, Docker Compose avanzato, integrazione CI/CD, container signing con cosign
> **Durata lab:** 5-6 ore
> **Livello:** Intermedio-Avanzato — richiede conoscenza base di Docker (build, run, compose)
> **Prerequisiti:** Docker Engine 29.x installato e funzionante, git installato, almeno 4GB RAM e 10GB spazio disco
> **Ambiente:** Macchina locale con Docker Engine 29.x (Linux/macOS/WSL2), Docker Buildx, Trivy, Syft

---

## Lab Environment Setup

```bash
# === VERIFICA PREREQUISITI DOCKER AVANZATO LAB ===
echo "=== CHECK PREREQUISITI ==="

# Docker Engine disponibile?
docker --version && echo "[OK] Docker disponibile" || echo "[FAIL] Installare Docker Engine 29.x"

# Versione raccomandata: 29.x (rilasciata novembre 2025)
# Il containerd image store è ora il DEFAULT in Docker 29.x
docker info --format '{{.Driver}}' && echo "[INFO] Storage driver attivo"

# BuildKit abilitato? (default da Docker 23.x in poi)
DOCKER_BUILDKIT=1 docker build --help | grep -q "buildx\|BuildKit" && \
  echo "[OK] BuildKit disponibile" || echo "[INFO] BuildKit non rilevato — abilitare manualmente"

# Buildx disponibile? (per multi-arch)
docker buildx version && echo "[OK] buildx disponibile" || echo "[WARN] buildx non trovato"

# Trivy disponibile? (scan CVE)
trivy --version 2>/dev/null && echo "[OK] Trivy disponibile" || \
  echo "[INFO] Trivy non installato — lo installiamo nel lab"

# Syft disponibile? (SBOM)
syft --version 2>/dev/null && echo "[OK] Syft disponibile" || \
  echo "[INFO] Syft non installato — lo installiamo nel lab"

# Cosign disponibile? (container signing)
cosign version 2>/dev/null && echo "[OK] Cosign disponibile" || \
  echo "[INFO] Cosign non installato — opzionale"

# Spazio disco disponibile
df -h . | awk 'NR==2{print "[INFO] Spazio disponibile:", $4}'

echo ""
echo "=== INSTALLAZIONE TOOL DI SICUREZZA ==="

# Installare Trivy (scanner CVE — versione corrente: 0.72.x, luglio 2026)
if ! command -v trivy &> /dev/null; then
  curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
  trivy --version && echo "[OK] Trivy installato"
fi

# Installare Syft (SBOM generator)
if ! command -v syft &> /dev/null; then
  curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin
  syft --version && echo "[OK] Syft installato"
fi

echo "=== AMBIENTE PRONTO ==="
```

### Architettura del Lab

```
┌─────────────────────────────────────────────────────────────────────┐
│                      BUILD PIPELINE LAB                             │
│                                                                     │
│  DOCKERFILE          BUILDKIT 0.31+         REGISTRY (LOCAL)       │
│  multi-stage    →   (mount cache,       →   localhost:5000          │
│  distroless          multi-arch,            (Harbor-lite)           │
│                       attestazioni)                                  │
│                            │                                        │
│                    ┌───────┴───────┐                                │
│              amd64/linux    arm64/linux                              │
│                    └───────┬───────┘                                │
│                     manifest list                                    │
│                                                                     │
│  SECURITY PIPELINE:                                                  │
│  immagine → trivy scan → syft SBOM → cosign sign → registry        │
│              │CVE scan    │inventario  │firma                       │
│              ↓            ↓            ↓                            │
│           report.json  sbom.cdx.json  firma.sig                    │
└─────────────────────────────────────────────────────────────────────┘
```

### Directory di lavoro del Lab

```bash
# Creare la directory di lavoro
mkdir -p ~/docker-lab/{app,multi-arch,security,compose}
cd ~/docker-lab

echo "[OK] Directory lab creata: ~/docker-lab"
ls -la
```

---

## PART A: FONDAMENTI — Docker dall'Interno

> Molti sviluppatori usano Docker da anni ma pensano ancora ad esso come "una VM leggera".
> Non è così. Un container Docker è fondamentalmente diverso da una VM: condivide il kernel
> del sistema operativo host, usa i namespace Linux per l'isolamento (PID, UTS, NET, IPC, MNT)
> e i cgroups per il controllo delle risorse. Comprendere questa differenza cambia radicalmente
> come si progettano i container: decide cosa è sicuro, cosa è performante, cosa è sostenibile
> a scala.

---

### Concetto A1: Architettura a Livelli — Docker 29.x

> **Analogia.** Pensa alla catena di distribuzione di un libro. L'autore scrive il manoscritto
> (Dockerfile). La casa editrice lo stampa (BuildKit che esegue il build). Il magazzino lo
> conserva (registry). La libreria lo vende (docker pull). E il cliente lo legge (docker run).
> Ogni fase della catena è separata, sostituibile, e — nelle versioni moderne — verificabile
> con una firma digitale per garantire autenticità.

```
STACK DOCKER 29.x:

  docker CLI  ←→  dockerd (daemon)
                       │
                  containerd (container runtime)
                       │
              ┌────────┴──────────┐
              │                   │
         BuildKit             runc/gVisor
         (build)              (container exec)
              │
         Snapshotter
         (overlay2/containerd image store)

NOVITÀ DOCKER 29.x:
  - containerd image store è il DEFAULT per nuove installazioni
  - Supporto sperimentale NFTables (alternativa moderna a iptables)
  - BuildKit vendorato a 0.31.0 — OCI media types di default
  - docker compose integrato nel CLI (Compose Specification v5.0)
  - Compose v5 delega i build a Docker Bake (BuildKit nativo)
```

```bash
# Esplorare la struttura interna di Docker
docker system info
# Vedere: Storage Driver, Kernel Version, Cgroup Driver, Security Options

# Storage driver (Docker 29.x default = containerd)
docker info --format '{{.Driver}}'
# OUTPUT: overlay2 (legacy) o containerd (nuovo default)

# Quanta memoria e CPU usa Docker sul sistema?
docker system df
# OUTPUT: immagini, container, volumi con dimensioni e spazio recuperabile

# Pulizia completa (attenzione: rimuove tutto)
# docker system prune -af --volumes
```

---

### Concetto A2: Layer e Cache — Come Docker Costruisce le Immagini

> **Analogia.** Pensa a come si dipinge una tela. Ogni pennellata aggiuntiva va sopra
> le precedenti — non si cancellano. I layer Docker funzionano esattamente così:
> ogni istruzione nel Dockerfile crea un layer immutabile che si accumula sugli altri.
> Se cambi l'ultima pennellata, ricalcoli solo quella. Se cambi la prima, ricalcoli tutto.
> Per questo l'ordine delle istruzioni nel Dockerfile è critico per le performance di build.

```
DOCKERFILE → LAYERS → IMMAGINE FINALE:

FROM python:3.12-slim    → Layer 1: base OS + Python (300MB) — RARAMENTE CAMBIA
COPY requirements.txt .  → Layer 2: file requirements (1KB)   — CAMBIA POCO
RUN pip install -r ...   → Layer 3: dipendenze Python (200MB) — CAMBIA POCO
COPY . /app              → Layer 4: codice applicativo (50KB)  — CAMBIA SPESSO
CMD ["python", "app.py"] → Layer 5: metadata (1B)              — CAMBIA A VOLTE

REGOLA ORO: metti quello che cambia di MENO in alto
            metti quello che cambia di PIÙ in basso

Senza ottimizzazione: ogni cambio al codice → rebuild di 550MB
Con ottimizzazione:   ogni cambio al codice → rebuild di 50KB
                      (solo il Layer 4 viene ricreato)
```

```bash
# Visualizzare i layer di un'immagine
docker history nginx:1.27-alpine
# Ogni riga = un layer con la sua dimensione

# Ispezionare i metadati di un'immagine
docker inspect nginx:1.27-alpine | python3 -m json.tool | head -80

# Esportare e analizzare i layer fisicamente
docker save nginx:1.27-alpine | tar -t | head -20
# Ogni cartella sha256:xxx/ è un layer
```

---

## PART B: DOCKERFILE MULTI-STAGE E BUILDKIT

### Esercizio B1: Dockerfile Single-Stage vs Multi-Stage

Prima approfondiamo il problema con un Dockerfile naif, poi lo ottimizziamo.

```bash
mkdir -p ~/docker-lab/app
cd ~/docker-lab/app

# Applicazione Python di esempio
cat > app.py << 'PYEOF'
from flask import Flask, jsonify
import sys, os

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({"status": "ok", "python": sys.version})

@app.route('/')
def index():
    return jsonify({"message": "Docker Lab App", "env": os.environ.get("APP_ENV", "dev")})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
PYEOF

cat > requirements.txt << 'EOF'
flask==3.1.0
gunicorn==23.0.0
EOF

# ======================================================
# VERSIONE 1: Dockerfile NAIVE — non fare così in prod
# ======================================================
cat > Dockerfile.naive << 'EOF'
FROM python:3.12                   # immagine base ENORME (900MB+)
WORKDIR /app
COPY . .                           # copia TUTTO (inclusi .git, test, doc)
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
# Risultato: ~1.2GB, nessuna ottimizzazione cache, root user, tutto writable
EOF

docker build -f Dockerfile.naive -t app-naive .
docker images app-naive
# OUTPUT: ~1.1GB — inaccettabile per produzione
```

```bash
# ======================================================
# VERSIONE 2: Dockerfile OTTIMIZZATO multi-stage
# ======================================================
cat > Dockerfile << 'EOF'
# ── STAGE 1: Builder ────────────────────────────────────────────────
# Installa le dipendenze in un ambiente completo
FROM python:3.12-slim AS builder

WORKDIR /build

# Installa build deps di sistema (solo per stage builder)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia prima requirements (invalida cache solo se requirements cambiano)
COPY requirements.txt .

# BuildKit mount cache: la cache pip persiste tra build successive
# --mount=type=cache: NON inclusa nell'immagine finale, solo velocizza build
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefix=/install --no-cache-dir -r requirements.txt

# ── STAGE 2: Runtime ────────────────────────────────────────────────
# Immagine finale: solo runtime, no build tools, no cache
FROM python:3.12-slim AS runtime

# Utente non-root per sicurezza
RUN groupadd -r appgroup && useradd -r -g appgroup -u 10001 appuser

WORKDIR /app

# Copia solo i pacchetti installati dallo stage builder
COPY --from=builder /install /usr/local

# Copia il codice applicativo
COPY --chown=appuser:appgroup app.py .

# Security hardening
USER appuser

# Container read-only root (con eccezione /tmp per gunicorn)
ENV APP_ENV=production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# Usa gunicorn (server di produzione) invece di Flask dev server
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]
EOF

# Build con BuildKit esplicito (già default in Docker 29.x)
DOCKER_BUILDKIT=1 docker build -t app-ottimizzata:latest .

# Confronto dimensioni
docker images | grep -E "app-naive|app-ottimizzata"
# OUTPUT: app-naive ~1.1GB    app-ottimizzata ~150MB

echo "[OK] Riduzione dimensioni: 1.1GB → 150MB (riduzione ~86%)"

# Verifica che gira come utente non-root
docker run --rm app-ottimizzata id
# OUTPUT: uid=10001(appuser) gid=10001(appgroup)
```

---

### Esercizio B2: BuildKit — Cache Mount Avanzata

```bash
# BuildKit offre tre tipi di mount in Dockerfile:
# --mount=type=cache   → persiste tra build, non nell'immagine finale
# --mount=type=secret  → passa secret senza includerli nell'immagine
# --mount=type=bind    → bind mount di un file dell'host durante il build

# Benchmark: build con e senza cache mount
time docker build --no-cache -t app-nocache . 2>&1 | tail -5
# OUTPUT: ~30-60 secondi (scarica e installa tutto)

time docker build -t app-cached . 2>&1 | tail -5
# OUTPUT: ~3-5 secondi (usa la cache mount pip)

# SECRET durante il build (esempio: token per npm/pip privato)
cat > Dockerfile.secret << 'EOF'
FROM python:3.12-slim
WORKDIR /app

# Il secret NON finisce nella history dell'immagine
RUN --mount=type=secret,id=pip_token \
    PIP_EXTRA_INDEX_URL="https://$(cat /run/secrets/pip_token)@pypi.private.company.com/simple/" \
    pip install mypackage-internal

COPY app.py .
CMD ["python", "app.py"]
EOF

# Passare il secret durante il build
echo "mytoken123" > /tmp/pip_token.txt
docker build \
  --secret id=pip_token,src=/tmp/pip_token.txt \
  -f Dockerfile.secret -t app-with-secret .
rm /tmp/pip_token.txt

# Verificare che il secret NON sia nell'immagine
docker history app-with-secret
# Il token NON appare nella history — solo "[secret mount]"
```

---

### Esercizio B3: Immagini Distroless — Massima Sicurezza

```bash
# Distroless: immagini senza shell, senza package manager, senza coreutils
# Superficie di attacco minima: solo runtime + applicazione

cat > Dockerfile.distroless << 'EOF'
# Stage 1: builder con strumenti completi
FROM python:3.12-slim AS builder
WORKDIR /install
RUN apt-get update && apt-get install -y gcc
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefix=/install -r requirements.txt

# Stage 2: distroless — NESSUNA SHELL
FROM gcr.io/distroless/python3-debian12:nonroot AS runtime
# Caratteristiche distroless:nonroot:
# - UID 65532 (nobody): nessun accesso root
# - No /bin/sh, no bash, no apt
# - Solo il runtime Python
# - Scansioni CVE molto più pulite

COPY --from=builder /install/lib/python3.12/site-packages \
    /usr/lib/python3/dist-packages/
COPY app.py /app/app.py

WORKDIR /app
EXPOSE 8080

ENTRYPOINT ["python", "app.py"]
EOF

docker build -f Dockerfile.distroless -t app-distroless .

# Confronto finale:
docker images | grep -E "app-"
# app-naive          ~1.1GB  — evitare
# app-ottimizzata    ~150MB  — buono per molti casi
# app-distroless     ~80MB   — ottimale per produzione

# Tentativo di shell (deve fallire in distroless)
docker run --rm app-distroless /bin/sh
# OUTPUT: OCI runtime exec failed: exec: "/bin/sh": stat /bin/sh: no such file or directory
# [OK] Questo è il comportamento CORRETTO — nessuna shell = meno attacco surface
```

---

## PART C: BUILD MULTI-ARCHITETTURA

### Esercizio C1: buildx per amd64 + arm64

> **Analogia.** Un libro pubblicato in due lingue: lo stesso contenuto, due edizioni
> per lettori diversi. Un'immagine multi-arch è la stessa cosa: un singolo nome
> (`myapp:latest`), ma Docker scarica automaticamente la versione giusta per
> l'architettura del sistema (Intel/AMD = amd64, Apple Silicon = arm64).

```bash
# Verificare i builder disponibili
docker buildx ls
# OUTPUT: default   docker   amd64/linux (solo architettura host)

# Creare un builder QEMU multi-arch
docker buildx create --name multiarch-builder \
  --driver docker-container \
  --use

# Avviare il builder
docker buildx inspect --bootstrap
# Ora supporta: linux/amd64, linux/arm64, linux/arm/v7, ...

# Build multi-architettura
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag localhost:5000/myapp:latest \
  --push \
  .
# Questo crea un "manifest list": unico tag → 2 immagini diverse

# Verificare il manifest list
docker buildx imagetools inspect localhost:5000/myapp:latest
# OUTPUT:
# MediaType: application/vnd.oci.image.index.v1+json
# Digests:
#   linux/amd64  sha256:aaa...  → binario per Intel/AMD
#   linux/arm64  sha256:bbb...  → binario per Apple Silicon/Raspberry Pi

# Quando si fa docker pull localhost:5000/myapp:latest:
# → su x86_64: scarica automaticamente l'immagine amd64
# → su Apple M1/M2/M3: scarica automaticamente l'immagine arm64
echo "[OK] Multi-arch build completato"
```

---

### Esercizio C2: Registry Locale per il Lab

```bash
# Avvio di un registry Docker locale per i test
docker run -d \
  --name local-registry \
  --restart always \
  -p 5000:5000 \
  -v registry-data:/var/lib/registry \
  registry:3

echo "[OK] Registry locale avviato su localhost:5000"

# Tag e push dell'immagine ottimizzata al registry locale
docker tag app-ottimizzata:latest localhost:5000/app-ottimizzata:v1.0
docker push localhost:5000/app-ottimizzata:v1.0

# Lista immagini nel registry locale
curl -s http://localhost:5000/v2/_catalog | python3 -m json.tool
# OUTPUT: {"repositories": ["app-ottimizzata"]}

curl -s http://localhost:5000/v2/app-ottimizzata/tags/list
# OUTPUT: {"name":"app-ottimizzata","tags":["v1.0"]}
```

---

## PART D: SICUREZZA CONTAINER — TRIVY, SBOM, SIGNING

### Esercizio D1: Scan CVE con Trivy 0.72

> **Analogia.** Prima di comprare un appartamento, fai fare una perizia strutturale
> che rivela problemi nascosti: umidità, cablaggio obsoleto, amianto. Trivy fa la
> stessa cosa per le immagini container: rivela vulnerabilità conosciute (CVE)
> nelle librerie e nel sistema operativo base — prima che vadano in produzione.

```bash
# Scan di un'immagine vulnerabile per vedere Trivy in azione
docker pull nginx:1.23
trivy image nginx:1.23 --format table
# OUTPUT: tabella di CVE con severità (CRITICAL, HIGH, MEDIUM, LOW)

# Scan dell'immagine ottimizzata (deve avere meno CVE)
trivy image app-ottimizzata:latest
# OUTPUT: meno vulnerabilità rispetto a nginx:1.23

# Scan dell'immagine distroless
trivy image app-distroless:latest
# OUTPUT: pochissime o zero CVE — superficie minima

# Export del report in JSON (per integrazione CI/CD)
trivy image \
  --format json \
  --output /tmp/trivy-report.json \
  app-ottimizzata:latest

# Analizzare il report
python3 -c "
import json
with open('/tmp/trivy-report.json') as f:
    report = json.load(f)
results = report.get('Results', [])
for r in results:
    vulns = r.get('Vulnerabilities', [])
    critical = [v for v in vulns if v.get('Severity') == 'CRITICAL']
    high = [v for v in vulns if v.get('Severity') == 'HIGH']
    print(f'{r[\"Target\"]}: {len(critical)} CRITICAL, {len(high)} HIGH')
"

# Fallire il CI/CD se ci sono CVE CRITICAL
trivy image \
  --exit-code 1 \
  --severity CRITICAL \
  app-ottimizzata:latest
# Exit code 0 = nessuna vulnerabilità critica
# Exit code 1 = trovate vulnerabilità critiche → blocca il deploy

echo "Versione Trivy:"
trivy --version | head -1
# [INFO] Versione corrente: v0.72.x (luglio 2026)
```

---

### Esercizio D2: SBOM con Syft — Software Bill of Materials

```bash
# SBOM = inventario di TUTTO ciò che è dentro un'immagine
# Come la lista ingredienti su una confezione, ma per il software

# Generare SBOM in formato CycloneDX (standard industriale)
syft app-ottimizzata:latest \
  --output cyclonedx-json=/tmp/sbom-app.cdx.json

# Generare SBOM in formato SPDX (standard Linux Foundation)
syft app-ottimizzata:latest \
  --output spdx-json=/tmp/sbom-app.spdx.json

# Visualizzare sommario SBOM
syft app-ottimizzata:latest --output table | head -30
# OUTPUT: lista di pacchetti, versioni, tipo (OS, python, ecc.)

# Analizzare il SBOM CycloneDX
python3 << 'PYEOF'
import json
with open('/tmp/sbom-app.cdx.json') as f:
    sbom = json.load(f)

components = sbom.get('components', [])
print(f"Totale componenti: {len(components)}")
print("\nPacchetti Python:")
for c in components:
    if c.get('type') == 'library' and c.get('purl', '').startswith('pkg:pypi'):
        print(f"  {c['name']}=={c.get('version', 'N/A')}")
PYEOF

# Scansionare il SBOM per CVE (più veloce che scannerizzare l'immagine)
# grype usa il SBOM già generato invece di analizzare di nuovo i layer
if command -v grype &> /dev/null; then
  grype sbom:/tmp/sbom-app.cdx.json
fi

echo "[OK] SBOM generato: $(wc -l < /tmp/sbom-app.cdx.json) righe JSON"
```

---

### Esercizio D3: Container Hardening — Read-Only Filesystem

```bash
# Container Hardening checklist in pratica
cat > /tmp/hardening-test.yaml << 'EOF'
# Docker run equivalente al manifest Kubernetes PSS Restricted
# Simuliamo con docker run le restrizioni che useremmo in K8s

docker run --rm \
  --read-only \
  --tmpfs /tmp:rw,size=64m \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  --security-opt no-new-privileges:true \
  --security-opt seccomp=/etc/docker/seccomp/default.json \
  --user 10001:10001 \
  --memory 128m \
  --cpus 0.5 \
  app-ottimizzata:latest
EOF

# Eseguiamo il container con hardening
docker run --rm \
  --read-only \
  --tmpfs /tmp:rw,size=64m,noexec \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  --user 10001:10001 \
  --memory 128m \
  --cpus 0.5 \
  -p 8080:8080 \
  -d \
  --name app-hardened \
  app-ottimizzata:latest

# Test che l'app funzioni
sleep 2
curl -s http://localhost:8080/health
# OUTPUT: {"python":"3.12.x...","status":"ok"}

# Test che non possa scrivere in posizioni protette
docker exec app-hardened touch /etc/hacked 2>&1
# OUTPUT: touch: /etc/hacked: Read-only file system
# [OK] Il filesystem è protetto

docker stop app-hardened

# SCHEMA HARDENING:
cat << 'SCHEMA'
CONTAINER SECURITY CHECKLIST:
  ✓ --read-only              → filesystem root non scrivibile
  ✓ --tmpfs /tmp             → solo /tmp scrivibile, temporaneo
  ✓ --cap-drop ALL           → rimuove tutte le Linux capabilities
  ✓ --no-new-privileges      → nessun escalation via setuid/setgid
  ✓ --user <non-root>        → non girare come root
  ✓ --memory + --cpus        → limiti di risorse (anti-DoS)
  ✓ seccomp profile          → limita le syscall consentite
SCHEMA
```

---

## PART E: DOCKER COMPOSE AVANZATO

### Esercizio E1: Stack Completo con Compose v5

```bash
mkdir -p ~/docker-lab/compose
cd ~/docker-lab/compose

# Compose v5 (Compose Specification 5.0, dicembre 2025)
# Nota: docker-compose (V1) è rimosso — si usa "docker compose" (V2)
cat > compose.yaml << 'EOF'
name: "lab-stack"

services:
  
  app:
    build:
      context: ../app
      dockerfile: Dockerfile
      target: runtime               # build solo lo stage runtime
      args:
        - APP_VERSION=${APP_VERSION:-1.0.0}
    image: localhost:5000/lab-app:${APP_VERSION:-1.0.0}
    environment:
      APP_ENV: production
      DB_HOST: postgres
      DB_PORT: "5432"
      DB_NAME: labdb
    env_file:
      - .env.local                  # file locale NON nel git
    secrets:
      - db_password                 # secret da Docker Swarm o file
    ports:
      - "8080:8080"
    depends_on:
      postgres:
        condition: service_healthy  # attende healthcheck prima di avviarsi
      redis:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: "0.5"
          memory: 256M
        reservations:
          cpus: "0.1"
          memory: 64M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s
    restart: unless-stopped
    networks:
      - frontend
      - backend
    read_only: true
    tmpfs:
      - /tmp:rw,size=64m
    security_opt:
      - no-new-privileges:true

  postgres:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: labdb
      POSTGRES_USER: labuser
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U labuser -d labdb"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7.4-alpine
    command: >
      redis-server
      --requirepass ${REDIS_PASSWORD:-changeme}
      --maxmemory 128mb
      --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    networks:
      - backend
    healthcheck:
      test: ["CMD", "redis-cli", "--no-auth-warning", "-a", "${REDIS_PASSWORD:-changeme}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:v3.1.0
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.retention.time=7d"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - frontend
      - backend
    restart: unless-stopped

secrets:
  db_password:
    file: ./secrets/db_password.txt     # file locale, non nel git

volumes:
  postgres-data:
    driver: local
  redis-data:
    driver: local
  prometheus-data:
    driver: local

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true    # backend NON ha accesso a internet

EOF

# Creare i file di supporto
mkdir -p secrets
echo "Sup3rS3cretP@ss!" > secrets/db_password.txt
chmod 600 secrets/db_password.txt

cat > .env.local << 'EOF'
APP_VERSION=1.0.0
REDIS_PASSWORD=redis-secret-2026
EOF

cat > init.sql << 'EOF'
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
EOF

cat > prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: "app"
    static_configs:
      - targets: ["app:8080"]
  - job_name: "postgres"
    static_configs:
      - targets: ["postgres-exporter:9187"]
EOF

# Avvio dello stack
docker compose up -d
docker compose ps
# OUTPUT: tutti i servizi in stato "running" con healthcheck OK

# Verificare i log
docker compose logs app --tail 20

# Test end-to-end
sleep 10
curl -s http://localhost:8080/health
# OUTPUT: {"status":"ok","python":"..."}

echo "[OK] Stack completo operativo"

# Scaling di un servizio
docker compose up -d --scale app=3
docker compose ps
# OUTPUT: 3 istanze di app-1, app-2, app-3

docker compose down -v   # pulizia
```

---

## PART F: INTEGRAZIONE CI/CD — BUILD AUTOMATIZZATA

### Esercizio F1: Script CI/CD Completo

```bash
# Script replicabile in qualsiasi CI/CD (GitHub Actions, GitLab CI, Jenkins)
cd ~/docker-lab

cat > build-pipeline.sh << 'PIPELINE'
#!/bin/bash
set -euo pipefail

# ─────────────────────────────────────────────────────────
# PIPELINE DI BUILD SICURA — Replicabile in CI/CD
# Implementa: build → test → scan → SBOM → push
# ─────────────────────────────────────────────────────────

APP_NAME="${APP_NAME:-lab-app}"
REGISTRY="${REGISTRY:-localhost:5000}"
VERSION="${VERSION:-1.0.0}"
COMMIT="${COMMIT:-$(git rev-parse --short HEAD 2>/dev/null || echo 'local')}"
FULL_TAG="${REGISTRY}/${APP_NAME}:${VERSION}"
COMMIT_TAG="${REGISTRY}/${APP_NAME}:${COMMIT}"

echo "=== FASE 1: BUILD ==="
docker buildx build \
  --platform linux/amd64 \
  --tag "${FULL_TAG}" \
  --tag "${COMMIT_TAG}" \
  --label "build.version=${VERSION}" \
  --label "build.commit=${COMMIT}" \
  --label "build.date=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --cache-from type=registry,ref="${REGISTRY}/${APP_NAME}:cache" \
  --cache-to type=registry,ref="${REGISTRY}/${APP_NAME}:cache",mode=max \
  app/
echo "[OK] Build completata: ${FULL_TAG}"

echo "=== FASE 2: TEST CONTAINER ==="
CONTAINER_ID=$(docker run -d --rm -p 18080:8080 "${FULL_TAG}")
sleep 3
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:18080/health)
docker stop "${CONTAINER_ID}" 2>/dev/null || true
if [ "${HTTP_STATUS}" == "200" ]; then
  echo "[OK] Health check passato (HTTP 200)"
else
  echo "[FAIL] Health check fallito (HTTP ${HTTP_STATUS})" && exit 1
fi

echo "=== FASE 3: SCAN CVE (Trivy) ==="
trivy image \
  --exit-code 1 \
  --severity CRITICAL \
  --format json \
  --output "/tmp/trivy-${COMMIT}.json" \
  "${FULL_TAG}"
CRITICAL_CVE=$(python3 -c "
import json,sys
r=json.load(open('/tmp/trivy-${COMMIT}.json'))
c=sum(len([v for v in x.get('Vulnerabilities',[]) if v.get('Severity')=='CRITICAL']) for x in r.get('Results',[]))
print(c)")
echo "[OK] Scan CVE: ${CRITICAL_CVE} vulnerabilità CRITICAL"
[ "${CRITICAL_CVE}" -gt 0 ] && echo "[FAIL] CVE critical trovate!" && exit 1

echo "=== FASE 4: SBOM (Syft) ==="
syft "${FULL_TAG}" \
  --output cyclonedx-json="/tmp/sbom-${COMMIT}.cdx.json"
COMPONENT_COUNT=$(python3 -c "
import json
s=json.load(open('/tmp/sbom-${COMMIT}.cdx.json'))
print(len(s.get('components',[])))")
echo "[OK] SBOM generato: ${COMPONENT_COUNT} componenti"

echo "=== FASE 5: PUSH AL REGISTRY ==="
docker push "${FULL_TAG}"
docker push "${COMMIT_TAG}"
echo "[OK] Immagini pushate al registry"

echo ""
echo "═══════════════════════════════════════════════════"
echo " BUILD PIPELINE COMPLETATA CON SUCCESSO"
echo " Immagine: ${FULL_TAG}"
echo " Commit:   ${COMMIT_TAG}"
echo " SBOM:     /tmp/sbom-${COMMIT}.cdx.json"
echo " CVE scan: /tmp/trivy-${COMMIT}.json"
echo "═══════════════════════════════════════════════════"
PIPELINE

chmod +x build-pipeline.sh

# Avviare il registry locale se non è già attivo
docker start local-registry 2>/dev/null || \
  docker run -d --name local-registry --restart always \
    -p 5000:5000 registry:3

# Eseguire la pipeline
APP_NAME=lab-app REGISTRY=localhost:5000 VERSION=1.0.0 ./build-pipeline.sh
echo "[OK] Pipeline CI/CD completata"
```

---

## PART G: TROUBLESHOOTING — PROBLEMI COMUNI

### Esercizio G1: Debug di un Container che Non si Avvia

```bash
# Caso 1: Permessi sbagliati
cat > ~/docker-lab/Dockerfile.buggy-perm << 'EOF'
FROM python:3.12-slim
WORKDIR /app
COPY --chown=root:root app.py .    # sbagliato: root possiede il file
USER 10001                          # ma l'utente non ha permessi di lettura
CMD ["python", "app.py"]
EOF

docker build -f ~/docker-lab/Dockerfile.buggy-perm -t app-buggy-perm ~/docker-lab/app/
docker run --rm app-buggy-perm
# ERROR: Permission denied

# DIAGNOSI:
docker run --rm --user root app-buggy-perm ls -la /app/
# Vedere: -rw-r--r-- root root app.py (leggibile da tutti)
# In realtà funziona, ma se avesse chmod 600...

# Caso 2: Container che crasha immediatamente
docker run --rm ubuntu:24.04 /bin/bash -c "exit 1"
docker ps -a | head -3
# Vedere: container Exited(1) — exit code 1 = errore applicativo

# DIAGNOSI sistematica:
echo "
DEBUGGING CONTAINER:
  1. docker logs <container_id>      → cosa ha scritto il processo?
  2. docker inspect <container_id>   → exit code, exit reason
  3. docker run --entrypoint sh <image>  → apri shell per debug manuale
  4. docker run --entrypoint sh <image> -c 'cat /etc/os-release'
  5. docker history <image>          → quali layer compongono l'immagine?

EXIT CODES COMUNI:
  0   = successo
  1   = errore generico applicativo
  126 = permesso negato (file non eseguibile)
  127 = file non trovato (CMD sbagliato)
  137 = SIGKILL (OOM o docker kill)
  143 = SIGTERM (docker stop)
"
```

---

### Esercizio G2: Ottimizzare la Cache di Build

```bash
# Problema: ogni cambio al codice ri-scarica le dipendenze
# Causa: COPY . . prima di pip install invalida la cache pip

# SBAGLIATO:
cat > /tmp/Dockerfile.bad-cache << 'EOF'
FROM python:3.12-slim
WORKDIR /app
COPY . .                    # invalida cache ogni volta che il codice cambia
RUN pip install -r requirements.txt  # quindi pip ri-scarica tutto
EOF

# CORRETTO:
cat > /tmp/Dockerfile.good-cache << 'EOF'
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .     # cambia RARAMENTE → cache stabile
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
COPY app.py .               # cambia SPESSO → solo questo layer viene invalidato
EOF

# Test: benchmark con e senza ottimizzazione
cd ~/docker-lab/app
echo "# commento cambiamento" >> app.py    # simula una modifica al codice

time docker build --no-cache -f /tmp/Dockerfile.bad-cache -t test-bad . 2>&1 | tail -3
time docker build -f /tmp/Dockerfile.good-cache -t test-good . 2>&1 | tail -3
# test-good: solo l'ultimo layer viene ricostruito → molto più veloce

git checkout app.py 2>/dev/null || sed -i '/# commento cambiamento/d' app.py
```

---

## Conclusioni e Prossimi Passi

Hai completato il lab Docker Avanzato. Ecco il riepilogo di ciò che hai appreso:

```
BUILD OTTIMIZZATA:
  ✓ Multi-stage Dockerfile: separare build da runtime
  ✓ BuildKit --mount=type=cache: cache pip/npm persistente tra build
  ✓ BuildKit --mount=type=secret: secret senza esporli nell'history
  ✓ Distroless: superficie di attacco minima
  ✓ Build multi-arch: un tag → amd64 e arm64 automatici

SICUREZZA:
  ✓ Trivy: scan CVE su immagini prima del deploy
  ✓ Syft: SBOM — inventario completo dei componenti
  ✓ Read-only filesystem + --cap-drop ALL + non-root user
  ✓ Secret management: file, Docker secrets, BuildKit mount

COMPOSE AVANZATO:
  ✓ Compose Specification v5 (docker compose, non docker-compose)
  ✓ depends_on con condition: service_healthy
  ✓ Networks interne (internal: true) per isolamento backend
  ✓ Scaling con docker compose up --scale

CI/CD INTEGRATION:
  ✓ Pipeline di build: build → test → scan → SBOM → push
  ✓ Exit code per bloccare CI se CVE critiche trovate
  ✓ Cache registry per build veloci in CI/CD
  ✓ Labels di build (versione, commit, data) per tracciabilità

COMANDI ESSENZIALI:
  docker buildx build --platform linux/amd64,linux/arm64
  docker buildx imagetools inspect <image>
  trivy image --severity CRITICAL --exit-code 1 <image>
  syft <image> --output cyclonedx-json=sbom.json
  docker compose up/down/logs/ps/exec
```

**Prossimi tutorial consigliati:**
- `tutorial_plat07_cicd_lab.md` — Pipeline CI/CD con GitHub Actions
- `tutorial_plat20_supply_chain_slsa_lab.md` — cosign, SLSA, supply chain completa

```bash
# Pulizia lab
docker stop local-registry 2>/dev/null
docker rm local-registry 2>/dev/null
docker volume rm registry-data 2>/dev/null
rm -rf ~/docker-lab

echo "[OK] Lab Docker Avanzato completato"
```

---

> **Nota versioni:** Tutorial validato con Docker Engine 29.x (novembre 2025), BuildKit 0.31.0
> (OCI media types default), Trivy 0.72.x (luglio 2026), Syft ultima versione.
> Compose Specification v5.0 "Mont Blanc" (dicembre 2025): il build delegato a Docker Bake
> — per build complessi, preferire `docker buildx bake` a `docker compose build`.
