# Tutorial Lab — n8n Self-Hosted in Produzione

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `09-n8n-guida-completa-self-hosted.md`
> **Livello:** competent → proficient
> **Tempo stimato:** 6-8 ore (lab completo)
> **Prerequisiti:** Docker + Docker Compose, concetto di reverse proxy, Postgres/Redis basics
> **Versioni di riferimento:** n8n 1.x LTS · PostgreSQL 16 · Redis 7 · Traefik 3.x

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Deployare n8n self-hosted in produzione con PostgreSQL + Redis (queue mode)
2. Configurare Traefik come reverse proxy con HTTPS automatico (Let's Encrypt)
3. Gestire l'encryption key e i segreti in modo sicuro (`.env`, nessun secret hard-coded)
4. Progettare workflow con error handling, sub-workflow e retry
5. Implementare backup automatizzato di database e credenziali
6. Integrare OpenTelemetry per osservabilità in produzione
7. Eseguire upgrade zero-downtime

---

## Lab Environment Setup

### Requisiti Hardware Minimi

```
CPU:     2 core (4 raccomandati per queue mode)
RAM:     4 GB (8 GB per carichi elevati)
Disco:   20 GB SSD (database + log esecuzioni)
OS:      Ubuntu 22.04 LTS / Debian 12 / qualsiasi Linux con Docker 24+
```

### Verifica Prerequisiti

```bash
#!/bin/bash
# Script: check-prereqs-n8n.sh
set -euo pipefail

echo "=== Verifica prerequisiti n8n Lab ==="

check_command() {
    if command -v "$1" &>/dev/null; then
        echo "  [OK] $1 trovato: $($1 --version 2>&1 | head -1)"
    else
        echo "  [MANCANTE] $1 non trovato — installazione richiesta"
        return 1
    fi
}

check_version() {
    local cmd="$1"
    local min_major="$2"
    local version
    version=$($cmd --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
    local major=${version%%.*}
    if [ "$major" -ge "$min_major" ]; then
        echo "  [OK] $cmd versione $version (>= $min_major richiesta)"
    else
        echo "  [AVVISO] $cmd versione $version — >= $min_major raccomandato"
    fi
}

echo ""
echo "--- Strumenti richiesti ---"
check_command docker
check_command docker-compose || check_command "docker compose"
check_command curl
check_command openssl

echo ""
echo "--- Versioni ---"
check_version docker 24
check_version docker-compose 2

echo ""
echo "--- Porte disponibili ---"
for port in 80 443 5678; do
    if ss -tlnp | grep -q ":$port "; then
        echo "  [OCCUPATA] Porta $port in uso — liberare prima del lab"
    else
        echo "  [OK] Porta $port disponibile"
    fi
done

echo ""
echo "--- Spazio disco ---"
available=$(df -BG /opt 2>/dev/null | tail -1 | awk '{print $4}' | tr -d 'G')
if [ "${available:-0}" -ge 10 ]; then
    echo "  [OK] ${available}G disponibili su /opt"
else
    echo "  [AVVISO] Solo ${available}G disponibili — raccomandati 20G"
fi

echo ""
echo "=== Verifica completata ==="
```

```bash
chmod +x check-prereqs-n8n.sh
./check-prereqs-n8n.sh
```

---

## Analogia Introduttiva

> **n8n è come un centralinista umano iperqualificato**:
> riceve chiamate da qualsiasi sistema (trigger), capisce cosa vuole (workflow),
> chiama altri servizi per conto tuo (nodi), e tiene nota di tutto in un registro (database).
>
> Il **queue mode con Redis** è come avere più centralinisti in parallelo:
> i lavori arrivano nella coda Redis, e ogni worker prende il prossimo disponibile.
> Se un centralinista cade, il lavoro non si perde — lo prende un altro.
>
> **PostgreSQL** è il registro permanente (esecuzioni, credenziali cifrate, workflow).
> **SQLite** è il quadernetto sul desktop: va benissimo per casa, disastroso per l'ufficio.

---

## Architettura Target

```
ARCHITETTURA n8n PRODUZIONE:

Internet ──HTTPS──▶  Traefik (reverse proxy)
                          │
              ┌───────────┴──────────────┐
              │                          │
         n8n Main                   n8n Workers (queue mode)
         (UI + API)               (esecuzioni background)
              │                          │
              └─────────┬────────────────┘
                        │
              ┌─────────┼──────────────┐
              │         │              │
         PostgreSQL   Redis       MinIO (opz.)
         (workflow,   (queue,    (file storage)
          esecuzioni)  cache)

FLUSSO ESECUZIONE (queue mode):
  1. Trigger attivo → n8n Main mette job in coda Redis
  2. Worker libero → preleva job da Redis (Bull queue)
  3. Worker esegue il workflow nodo per nodo
  4. Risultato → scritto in PostgreSQL
  5. UI → legge i risultati in tempo reale via WebSocket

NETWORK ISOLATION:
  n8n-internal (internal: true) = DB + Redis non raggiungibili da Internet
  web = solo Traefik e n8n Main esposti
```

---

## PART A — Deploy Base con PostgreSQL

### A1 — Struttura Progetto

```bash
mkdir -p /opt/n8n/{data,files,backups}
chmod 700 /opt/n8n/backups

# n8n gira come utente node (UID 1000)
sudo chown -R 1000:1000 /opt/n8n/data
sudo chown -R 1000:1000 /opt/n8n/files

cd /opt/n8n
```

### A2 — Generazione Segreti

```bash
# Genera encryption key casuale (OBBLIGATORIA — se persa tutte le credenziali sono perse)
N8N_ENCRYPTION_KEY=$(openssl rand -hex 32)
echo "N8N_ENCRYPTION_KEY=$N8N_ENCRYPTION_KEY"

# Genera password PostgreSQL
N8N_DB_PASSWORD=$(openssl rand -base64 24 | tr -d '+/=' | head -c 32)
echo "N8N_DB_PASSWORD=$N8N_DB_PASSWORD"

# Scrive il file .env (mai committare in git)
cat > /opt/n8n/.env << EOF
# n8n Configuration — NON COMMITTARE IN GIT
# Generato il: $(date -Iseconds)

# Dominio
N8N_DOMAIN=n8n.example.com

# Database PostgreSQL
N8N_DB_PASSWORD=${N8N_DB_PASSWORD}

# Cifratura credenziali (CRITICO: backup questo valore in un password manager)
N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}

# Email admin per notifiche Traefik Let's Encrypt
TRAEFIK_ACME_EMAIL=admin@example.com
EOF

chmod 600 /opt/n8n/.env
echo "File .env creato. SALVA N8N_ENCRYPTION_KEY in un password manager ORA."
```

> **ATTENZIONE:** L'`N8N_ENCRYPTION_KEY` cifra TUTTE le credenziali salvate in n8n (API key, password, token OAuth). Se la perdi, devi ricreare manualmente ogni credenziale. Archiviarla in un vault (1Password, Bitwarden, HashiCorp Vault) è **obbligatorio**.

### A3 — Docker Compose Produzione

```yaml
# /opt/n8n/docker-compose.yml
version: "3.8"

services:
  # ── Database ──────────────────────────────────────────────────────
  n8n-db:
    image: postgres:16-alpine
    container_name: n8n-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: n8n
      POSTGRES_PASSWORD: "${N8N_DB_PASSWORD}"
      POSTGRES_DB: n8n
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=C"
    volumes:
      - n8n_db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U n8n -d n8n"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    networks:
      - n8n-internal

  # ── Cache / Queue ─────────────────────────────────────────────────
  n8n-redis:
    image: redis:7-alpine
    container_name: n8n-redis
    restart: unless-stopped
    command: >
      redis-server
      --requirepass "${N8N_ENCRYPTION_KEY:0:32}"
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --save 60 1
      --loglevel warning
    volumes:
      - n8n_redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--no-auth-warning", "-a", "${N8N_ENCRYPTION_KEY:0:32}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - n8n-internal

  # ── n8n Main (UI + API + Webhook receiver) ────────────────────────
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n
    restart: unless-stopped
    depends_on:
      n8n-db:
        condition: service_healthy
      n8n-redis:
        condition: service_healthy
    environment:
      # Database
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: n8n-db
      DB_POSTGRESDB_PORT: 5432
      DB_POSTGRESDB_DATABASE: n8n
      DB_POSTGRESDB_USER: n8n
      DB_POSTGRESDB_PASSWORD: "${N8N_DB_PASSWORD}"
      DB_POSTGRESDB_SSL_REJECT_UNAUTHORIZED: "false"

      # Queue mode (Redis)
      EXECUTIONS_MODE: queue
      QUEUE_BULL_REDIS_HOST: n8n-redis
      QUEUE_BULL_REDIS_PORT: 6379
      QUEUE_BULL_REDIS_PASSWORD: "${N8N_ENCRYPTION_KEY:0:32}"
      QUEUE_HEALTH_CHECK_ACTIVE: "true"

      # Cifratura credenziali
      N8N_ENCRYPTION_KEY: "${N8N_ENCRYPTION_KEY}"

      # Networking
      N8N_HOST: "${N8N_DOMAIN}"
      N8N_PORT: 5678
      N8N_PROTOCOL: https
      WEBHOOK_URL: "https://${N8N_DOMAIN}/"

      # Timezone
      GENERIC_TIMEZONE: Europe/Rome
      TZ: Europe/Rome

      # Gestione esecuzioni
      EXECUTIONS_DATA_PRUNE: "true"
      EXECUTIONS_DATA_MAX_AGE: 168          # 7 giorni in ore
      EXECUTIONS_DATA_SAVE_ON_ERROR: all
      EXECUTIONS_DATA_SAVE_ON_SUCCESS: all
      EXECUTIONS_DATA_SAVE_ON_PROGRESS: "true"
      EXECUTIONS_DATA_SAVE_MANUAL_EXECUTIONS: "true"

      # Log
      N8N_LOG_LEVEL: info
      N8N_LOG_OUTPUT: console

    volumes:
      - n8n_data:/home/node/.n8n
      - n8n_files:/files
    ports:
      - "127.0.0.1:5678:5678"
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.n8n.rule=Host(`${N8N_DOMAIN}`)"
      - "traefik.http.routers.n8n.entrypoints=websecure"
      - "traefik.http.routers.n8n.tls.certresolver=letsencrypt"
      - "traefik.http.services.n8n.loadbalancer.server.port=5678"
    networks:
      - n8n-internal
      - web

  # ── n8n Worker (esecuzioni in coda) ──────────────────────────────
  n8n-worker:
    image: n8nio/n8n:latest
    container_name: n8n-worker
    restart: unless-stopped
    command: worker
    depends_on:
      n8n-db:
        condition: service_healthy
      n8n-redis:
        condition: service_healthy
    environment:
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: n8n-db
      DB_POSTGRESDB_PORT: 5432
      DB_POSTGRESDB_DATABASE: n8n
      DB_POSTGRESDB_USER: n8n
      DB_POSTGRESDB_PASSWORD: "${N8N_DB_PASSWORD}"
      N8N_ENCRYPTION_KEY: "${N8N_ENCRYPTION_KEY}"
      EXECUTIONS_MODE: queue
      QUEUE_BULL_REDIS_HOST: n8n-redis
      QUEUE_BULL_REDIS_PORT: 6379
      QUEUE_BULL_REDIS_PASSWORD: "${N8N_ENCRYPTION_KEY:0:32}"
      GENERIC_TIMEZONE: Europe/Rome
      TZ: Europe/Rome
      N8N_LOG_LEVEL: info
      N8N_LOG_OUTPUT: console
    volumes:
      - n8n_data:/home/node/.n8n
      - n8n_files:/files
    networks:
      - n8n-internal

  # ── Reverse Proxy Traefik ─────────────────────────────────────────
  traefik:
    image: traefik:v3.0
    container_name: traefik
    restart: unless-stopped
    command:
      - "--api.insecure=false"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.web.http.redirections.entrypoint.to=websecure"
      - "--entrypoints.web.http.redirections.entrypoint.scheme=https"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.email=${TRAEFIK_ACME_EMAIL}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      - "--log.level=WARN"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik_letsencrypt:/letsencrypt
    networks:
      - web

volumes:
  n8n_db_data:
  n8n_data:
  n8n_files:
  n8n_redis_data:
  traefik_letsencrypt:

networks:
  n8n-internal:
    internal: true      # isolata da Internet
  web:
    external: false
```

### A4 — Avvio e Verifica

```bash
cd /opt/n8n

# Avvio in background
docker compose up -d

# Attesa health check (~30 secondi)
echo "Attesa avvio servizi..."
sleep 15

# Verifica stato servizi
docker compose ps

# Output atteso:
# NAME         STATUS          PORTS
# n8n          Up 30 seconds   127.0.0.1:5678->5678/tcp
# n8n-db       Up 30 seconds   5432/tcp
# n8n-redis    Up 30 seconds   6379/tcp
# n8n-worker   Up 30 seconds
# traefik      Up 30 seconds   0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp

# Controlla i log n8n per errori
docker compose logs n8n --tail=50

# Verifica connessione DB (cerca "Database connection successful" nei log)
docker compose logs n8n 2>&1 | grep -i "database\|connection\|error" | tail -20

# Verifica queue mode attivo
docker compose logs n8n-worker 2>&1 | grep -i "queue\|worker\|redis" | tail -10
```

**Output atteso nei log n8n:**
```
n8n  | Successfully connected to n8n database.
n8n  | n8n is ready on port 5678
n8n  | Tunnel is enabled and Externally Available (via Traefik)
n8n-worker | Starting n8n with queue mode
n8n-worker | Worker connected to Redis queue
```

### A5 — Setup Iniziale via UI

Per ambienti lab senza DNS configurato, usa un tunnel locale:

```bash
# Per lab locale senza DNS — usa port forward
# Apri browser su http://localhost:5678
# (oppure su https://n8n.example.com se hai DNS configurato)

# Prima apertura: crea account owner
# - Email: admin@lab.local
# - Password: scegli una password sicura

# Verifica che il setup sia completo:
curl -s http://localhost:5678/healthz
# Output atteso: {"status":"ok"}
```

---

## PART B — Workflow Design Pattern

### B1 — Workflow con Error Handling

Il pattern fondamentale per workflow production-ready:

```
ARCHITETTURA WORKFLOW CON ERROR HANDLING:

  [Trigger]
      │
      ▼
  [Set Variables]  ← normalizzazione input
      │
      ▼
  [HTTP Request]   ← operazione principale
      │         \
  (SUCCESS)    (ERROR)
      │              \
      ▼               ▼
  [Process]       [Error Trigger] → [Slack Alert] → [Sentry Log]
      │
      ▼
  [Respond]
```

**Workflow JSON — Import diretto in n8n:**

```json
{
  "name": "Pattern Error Handling Base",
  "nodes": [
    {
      "id": "trigger-1",
      "name": "Webhook Trigger",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "httpMethod": "POST",
        "path": "process-order",
        "responseMode": "responseNode"
      },
      "position": [240, 300]
    },
    {
      "id": "set-1",
      "name": "Normalizza Input",
      "type": "n8n-nodes-base.set",
      "parameters": {
        "values": {
          "string": [
            {
              "name": "orderId",
              "value": "={{ $json.body.order_id }}"
            },
            {
              "name": "correlationId",
              "value": "={{ $json.body.correlation_id || $execution.id }}"
            }
          ]
        }
      },
      "position": [440, 300]
    },
    {
      "id": "http-1",
      "name": "Chiama API Ordini",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "method": "GET",
        "url": "=https://api.example.com/orders/{{ $json.orderId }}",
        "headers": {
          "values": [
            {"name": "X-Correlation-ID", "value": "={{ $json.correlationId }}"}
          ]
        },
        "options": {
          "timeout": 30000,
          "retry": {
            "enabled": true,
            "maxTries": 3,
            "waitBetweenTries": 1000
          }
        },
        "onError": "continueErrorOutput"
      },
      "position": [640, 300]
    }
  ]
}
```

### B2 — Sub-Workflow e Modularità

> **I sub-workflow sono come funzioni riutilizzabili**: invece di riscrivere la logica di autenticazione in ogni workflow, la metti in un workflow figlio e lo chiami con il nodo Execute Workflow.

**Struttura consigliata:**

```
ORGANIZZAZIONE WORKFLOW:

/Library (sub-workflow riutilizzabili)
  ├── auth/get-token       ← ottieni token OAuth
  ├── notify/slack-alert   ← invia alert Slack
  ├── notify/email-report  ← invia report email
  └── utils/log-to-db      ← log audit su PostgreSQL

/Workflows (workflow principali)
  ├── orders/process-new
  ├── orders/check-status
  ├── invoices/generate
  └── reports/daily-summary
```

**Nodo Execute Workflow (chiamata sub-workflow):**

```
Configurazione nodo "Execute Workflow":
  - Workflow: [seleziona dal dropdown]
  - Wait for sub-workflow: ON (per risultati sincroni)
  - Input Data: {{ $json }}  ← passa tutti i dati
```

### B3 — Workflow con Retry Intelligente

```javascript
// Nodo Code: retry con exponential backoff
// Inserire prima di chiamate API critiche

const MAX_RETRIES = 3;
const BASE_DELAY_MS = 1000;

async function callWithRetry(url, options, attempt = 0) {
  try {
    const response = await $helpers.httpRequest({
      method: 'GET',
      url: url,
      ...options
    });
    return response;
  } catch (error) {
    if (attempt >= MAX_RETRIES) {
      // Dopo tutti i retry, lancia per attivare Error Trigger
      throw new Error(`Fallito dopo ${MAX_RETRIES} tentativi: ${error.message}`);
    }
    
    // Verifica se l'errore è retriable
    const statusCode = error.response?.status;
    const isRetriable = !statusCode || statusCode === 429 || statusCode >= 500;
    
    if (!isRetriable) {
      throw error; // 4xx client errors: non riprovare
    }
    
    // Backoff esponenziale con jitter
    const delay = BASE_DELAY_MS * Math.pow(2, attempt) + Math.random() * 500;
    console.log(`Tentativo ${attempt + 1}/${MAX_RETRIES} fallito. Retry in ${delay}ms...`);
    
    await new Promise(resolve => setTimeout(resolve, delay));
    return callWithRetry(url, options, attempt + 1);
  }
}

const result = await callWithRetry(
  'https://api.example.com/resource',
  { headers: { 'Authorization': 'Bearer ' + $env.API_TOKEN } }
);

return [{ json: result }];
```

### B4 — Design Pattern per PMI Italiane

```
CASI D'USO TIPICI PMI:

1. CICLO ORDINE-FATTURA:
   Webhook e-commerce (WooCommerce/Shopify)
   → Verifica disponibilità magazzino (ERP)
   → Crea ordine in gestionale (API SAP B1 / TeamSystem)
   → Genera fattura XML SDI (B2B)
   → Invia al cliente (email + portale)
   → Update CRM (Salesforce / HubSpot)

2. ONBOARDING DIPENDENTE:
   Trigger: nuovo record in HR system
   → Crea account Google Workspace
   → Crea account Slack + invita ai canali
   → Crea account GitHub + assegna team
   → Crea ticket Jira per computer setup
   → Notify manager su Teams
   → Schedule call con HR (Google Calendar)

3. MONITORING FATTURATO:
   Schedule: ogni lunedì 08:00
   → Query DB vendite settimana
   → Calcola KPI (fatturato, margine, ordini pendenti)
   → Genera PDF report con grafici
   → Invia a direzione via email
   → Post su canale Slack #management
```

---

## PART C — Backup, Security, Upgrade

### C1 — Backup Automatizzato

```bash
#!/bin/bash
# Script: /opt/n8n/backup.sh
# Uso: sudo crontab -e → 0 3 * * * /opt/n8n/backup.sh
set -euo pipefail

BACKUP_DIR="/opt/n8n/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="n8n_backup_${DATE}"
RETENTION_DAYS=30

# Carica variabili d'ambiente
source /opt/n8n/.env

log() { echo "[$(date -Iseconds)] $*"; }

log "Inizio backup n8n..."

# 1. Backup database PostgreSQL
log "Backup PostgreSQL..."
docker exec n8n-db pg_dump \
    -U n8n \
    -d n8n \
    --no-password \
    --format=custom \
    --compress=9 \
    > "${BACKUP_DIR}/${BACKUP_NAME}_db.dump"

# 2. Backup dati n8n (workflow, credenziali cifrate, encryption key)
log "Backup dati n8n..."
tar -czf "${BACKUP_DIR}/${BACKUP_NAME}_data.tar.gz" \
    -C /opt/n8n \
    data/ \
    .env \  # Include .env con encryption key!
    2>/dev/null || true

# 3. Export workflow via API (backup addizionale in formato JSON leggibile)
log "Export workflow via API..."
N8N_API_URL="http://localhost:5678/api/v1"

# Richiede token API (da creare in Settings → API → Create API Key)
if [ -f /opt/n8n/.n8n-api-key ]; then
    API_KEY=$(cat /opt/n8n/.n8n-api-key)
    curl -s -H "X-N8N-API-KEY: ${API_KEY}" \
        "${N8N_API_URL}/workflows?active=true" \
        > "${BACKUP_DIR}/${BACKUP_NAME}_workflows.json" || true
fi

# 4. Pulizia backup vecchi
log "Pulizia backup >$RETENTION_DAYS giorni..."
find "${BACKUP_DIR}" -name "n8n_backup_*" -mtime "+${RETENTION_DAYS}" -delete

# 5. Verifica dimensioni
TOTAL_SIZE=$(du -sh "${BACKUP_DIR}" | cut -f1)
log "Backup completato. Spazio totale backup: ${TOTAL_SIZE}"

# 6. Alert se backup troppo piccolo (potenziale problema)
DB_SIZE=$(stat -c%s "${BACKUP_DIR}/${BACKUP_NAME}_db.dump")
if [ "$DB_SIZE" -lt 10240 ]; then  # meno di 10KB è sospetto
    echo "AVVISO: Backup DB è solo ${DB_SIZE} bytes — verificare!" >&2
    exit 1
fi

log "=== Backup OK: ${BACKUP_NAME} ==="
```

```bash
# Setup cron per backup notturno
chmod +x /opt/n8n/backup.sh

# Test manuale
/opt/n8n/backup.sh

# Cron: ogni giorno alle 03:00
echo "0 3 * * * root /opt/n8n/backup.sh >> /var/log/n8n-backup.log 2>&1" | \
    sudo tee /etc/cron.d/n8n-backup

# Verifica backup presenti
ls -lh /opt/n8n/backups/
```

### C2 — Restore da Backup

```bash
#!/bin/bash
# Script: /opt/n8n/restore.sh <backup_name>
# Uso: ./restore.sh n8n_backup_20260716_030000
set -euo pipefail

BACKUP_NAME="${1:?Specificare il nome del backup}"
BACKUP_DIR="/opt/n8n/backups"

echo "=== RESTORE n8n da: ${BACKUP_NAME} ==="
echo "ATTENZIONE: Questo sovrascriverà il database corrente!"
read -p "Continuare? (digita 'SI' per confermare): " confirm
[ "$confirm" = "SI" ] || { echo "Annullato."; exit 0; }

# Stop n8n (non il DB)
docker compose stop n8n n8n-worker

# Restore database
echo "Restore PostgreSQL..."
docker exec -i n8n-db psql -U n8n -c "DROP DATABASE IF EXISTS n8n_restore;"
docker exec -i n8n-db psql -U n8n -c "CREATE DATABASE n8n_restore;"
docker exec -i n8n-db pg_restore \
    -U n8n \
    -d n8n_restore \
    --no-password \
    < "${BACKUP_DIR}/${BACKUP_NAME}_db.dump"

# Switch database (rename)
docker exec -i n8n-db psql -U n8n -c "
    SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'n8n';
    DROP DATABASE n8n;
    ALTER DATABASE n8n_restore RENAME TO n8n;
"

# Riavvio
docker compose start n8n n8n-worker
echo "=== Restore completato ==="
```

### C3 — Security Hardening

```bash
# 1. Abilitare autenticazione di base (oltre all'account utente)
# Aggiungere a .env:
cat >> /opt/n8n/.env << 'EOF'

# Security hardening
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=n8nadmin
N8N_BASIC_AUTH_PASSWORD=CAMBIA_QUESTA_PASSWORD_SICURA

# Disabilita telemetria
N8N_DIAGNOSTICS_ENABLED=false
N8N_VERSION_NOTIFICATIONS_ENABLED=false

# Limita dimensione payload
N8N_PAYLOAD_SIZE_MAX=64

# Abilitare cookie secure
N8N_SECURE_COOKIE=true
EOF

# 2. Limitare accesso alla rete
# Il container n8n già usa 127.0.0.1:5678 — solo Traefik può raggiungerlo

# 3. Verificare variabili d'ambiente NON esposte
docker inspect n8n | python3 -c "
import json, sys
container = json.load(sys.stdin)[0]
env = container['Config']['Env']
# Verifica che nessuna chiave/password sia in chiaro (solo variabili da .env)
for e in env:
    if 'PASSWORD' in e or 'KEY' in e or 'SECRET' in e:
        name, _, value = e.partition('=')
        if len(value) < 8:
            print(f'AVVISO: {name} potrebbe essere vuota o debole')
        else:
            print(f'OK: {name} presente (lunghezza: {len(value)})')
"
```

### C4 — Procedure di Upgrade

```bash
#!/bin/bash
# Script: /opt/n8n/upgrade.sh
# Seguire la migration guide di n8n per upgrade major (v0→v1)
set -euo pipefail

echo "=== Upgrade n8n ==="

# 1. Backup pre-upgrade (OBBLIGATORIO)
/opt/n8n/backup.sh || { echo "Backup fallito — upgrade annullato"; exit 1; }

# 2. Verifica versione corrente
CURRENT_VERSION=$(docker inspect n8n --format='{{.Config.Image}}' | cut -d: -f2)
echo "Versione attuale: ${CURRENT_VERSION}"

# 3. Pull nuova immagine
docker compose pull n8n n8n-worker

# 4. Verifica nuova versione disponibile
NEW_VERSION=$(docker inspect n8nio/n8n:latest --format='{{index .RepoDigests 0}}' 2>/dev/null || echo "latest")
echo "Nuova versione: ${NEW_VERSION}"

# 5. Riavvio con nuova immagine
echo "Riavvio con nuova immagine..."
docker compose up -d --no-deps n8n n8n-worker

# 6. Health check post-upgrade
sleep 15
if curl -sf http://localhost:5678/healthz | grep -q '"status":"ok"'; then
    echo "=== Upgrade completato con successo ==="
else
    echo "ERRORE: Health check fallito dopo upgrade!"
    echo "Rollback in corso..."
    docker compose down
    # Restore dal backup
    /opt/n8n/restore.sh "$(ls /opt/n8n/backups/n8n_backup_*.dump | sort | tail -1 | sed 's/_db.dump//' | xargs basename)"
    exit 1
fi
```

---

## PART D — Osservabilità con OpenTelemetry

### D1 — Setup OTel Collector

```yaml
# /opt/n8n/otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 5s
    send_batch_size: 512
  resource:
    attributes:
      - action: insert
        key: service.namespace
        value: n8n-production

exporters:
  prometheus:
    endpoint: "0.0.0.0:8889"
  debug:
    verbosity: basic
  # Per Grafana Cloud o Tempo:
  # otlp/tempo:
  #   endpoint: https://tempo.grafana.net:443
  #   headers:
  #     authorization: Basic <base64(username:password)>

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [debug]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
```

**Aggiungere OTel Collector al docker-compose.yml:**

```yaml
  # Aggiungere al docker-compose.yml esistente
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    container_name: otel-collector
    restart: unless-stopped
    command: ["--config=/etc/otel/config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel/config.yaml:ro
    ports:
      - "4317:4317"    # OTLP gRPC
      - "4318:4318"    # OTLP HTTP
      - "8889:8889"    # Prometheus metrics
    networks:
      - n8n-internal
```

**Abilitare OTel in n8n — aggiungere alle variabili d'ambiente di n8n:**

```yaml
      # OpenTelemetry
      N8N_METRICS: "true"
      N8N_METRICS_INCLUDE_WORKFLOW_ID_LABEL: "true"
      N8N_METRICS_INCLUDE_NODE_TYPE_LABEL: "true"
      N8N_METRICS_INCLUDE_CREDENTIAL_TYPE_LABEL: "true"
      OTEL_EXPORTER_OTLP_ENDPOINT: "http://otel-collector:4318"
      OTEL_SERVICE_NAME: "n8n"
```

### D2 — Metriche n8n Rilevanti

```python
#!/usr/bin/env python3
"""
Script: monitor-n8n.py
Monitora le metriche n8n via API e genera alert
"""
import httpx
import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class N8nMetrics:
    total_executions: int
    success_rate: float
    avg_execution_time_ms: float
    active_workflows: int
    failed_executions_24h: int


def fetch_n8n_metrics(base_url: str, api_key: str) -> N8nMetrics:
    headers = {"X-N8N-API-KEY": api_key}

    with httpx.Client(base_url=base_url, headers=headers, timeout=10) as client:
        # Esecuzioni ultime 24h
        executions_resp = client.get(
            "/api/v1/executions",
            params={"limit": 100, "includeData": "false"}
        )
        executions_resp.raise_for_status()
        executions = executions_resp.json().get("data", [])

        # Workflow attivi
        workflows_resp = client.get("/api/v1/workflows", params={"active": "true"})
        workflows_resp.raise_for_status()
        active_count = workflows_resp.json().get("count", 0)

    total = len(executions)
    if total == 0:
        return N8nMetrics(0, 100.0, 0.0, active_count, 0)

    successful = sum(1 for e in executions if e.get("finished") and not e.get("stoppedAt"))
    failed = sum(1 for e in executions if e.get("status") == "error")

    durations = [
        (e.get("stoppedAt", 0) - e.get("startedAt", 0))
        for e in executions
        if e.get("stoppedAt") and e.get("startedAt")
    ]
    avg_duration = sum(durations) / len(durations) if durations else 0

    return N8nMetrics(
        total_executions=total,
        success_rate=(successful / total) * 100,
        avg_execution_time_ms=avg_duration,
        active_workflows=active_count,
        failed_executions_24h=failed,
    )


def check_alerts(metrics: N8nMetrics) -> list[str]:
    alerts = []
    if metrics.success_rate < 95:
        alerts.append(f"[CRITICO] Success rate {metrics.success_rate:.1f}% < 95%")
    if metrics.failed_executions_24h > 10:
        alerts.append(f"[AVVISO] {metrics.failed_executions_24h} esecuzioni fallite nelle 24h")
    if metrics.avg_execution_time_ms > 30000:
        alerts.append(f"[AVVISO] Tempo medio {metrics.avg_execution_time_ms:.0f}ms > 30s")
    return alerts


if __name__ == "__main__":
    import os
    metrics = fetch_n8n_metrics(
        base_url=os.environ.get("N8N_URL", "http://localhost:5678"),
        api_key=os.environ.get("N8N_API_KEY", "")
    )
    print(f"Workflow attivi:       {metrics.active_workflows}")
    print(f"Esecuzioni monitorate: {metrics.total_executions}")
    print(f"Success rate:          {metrics.success_rate:.1f}%")
    print(f"Tempo medio:           {metrics.avg_execution_time_ms:.0f}ms")
    print(f"Fallite 24h:           {metrics.failed_executions_24h}")

    alerts = check_alerts(metrics)
    if alerts:
        print("\n=== ALERT ===")
        for alert in alerts:
            print(alert)
```

### D3 — Dashboard PrometheusRule

```yaml
# prometheus-rules-n8n.yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: n8n-alerts
  namespace: monitoring
spec:
  groups:
    - name: n8n.rules
      interval: 60s
      rules:
        - alert: N8nHighFailureRate
          expr: |
            (
              rate(n8n_workflow_failed_total[5m]) /
              (rate(n8n_workflow_succeeded_total[5m]) + rate(n8n_workflow_failed_total[5m]))
            ) > 0.05
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "n8n failure rate > 5%"
            description: "Il tasso di fallimento dei workflow è {{ $value | humanizePercentage }}"

        - alert: N8nWorkerDown
          expr: absent(n8n_queue_workers_active) or n8n_queue_workers_active == 0
          for: 2m
          labels:
            severity: critical
          annotations:
            summary: "Nessun worker n8n attivo"
            description: "La coda Redis non ha worker — le esecuzioni si bloccano"

        - alert: N8nQueueBacklog
          expr: n8n_queue_waiting_jobs > 100
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Backlog coda n8n elevato"
            description: "{{ $value }} job in attesa — considerare scaling dei worker"
```

---

## PART E — Esercizi Pratici

### Esercizio 1 — Webhook → Slack (15 min)

Crea un workflow che:
1. Riceve un webhook POST con payload `{"message": "...", "priority": "high|normal"}`
2. Se `priority == "high"`: invia su #alerts Slack con emoji 🚨
3. Se `priority == "normal"`: invia su #general Slack
4. Risponde al webhook con `{"received": true, "channel": "..."}`

**Verifica:**
```bash
# Test con curl dopo aver attivato il workflow
curl -X POST http://localhost:5678/webhook/test-slack \
    -H "Content-Type: application/json" \
    -d '{"message": "Test alert", "priority": "high"}'

# Output atteso:
# {"received": true, "channel": "#alerts"}
```

### Esercizio 2 — Cron + Report Excel (30 min)

Workflow schedulato ogni lunedì alle 09:00 che:
1. Legge dati da un Google Sheet (simulare con un CSV statico per il lab)
2. Calcola: totale vendite, media per riga, top 3 prodotti
3. Genera email HTML con tabella riassuntiva
4. Salva log dell'esecuzione in un nodo Write Binary File

```javascript
// Nodo Code: calcola statistiche
const rows = $input.all().map(item => item.json);

const totalSales = rows.reduce((sum, r) => sum + (parseFloat(r.amount) || 0), 0);
const avg = totalSales / rows.length;

const byProduct = {};
for (const row of rows) {
    byProduct[row.product] = (byProduct[row.product] || 0) + parseFloat(row.amount || 0);
}

const top3 = Object.entries(byProduct)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([product, total]) => ({ product, total: total.toFixed(2) }));

return [{
    json: {
        totalSales: totalSales.toFixed(2),
        avgPerRow: avg.toFixed(2),
        rowCount: rows.length,
        top3Products: top3,
        generatedAt: new Date().toISOString()
    }
}];
```

### Esercizio 3 — Queue Mode Stress Test (20 min)

Verifica che il queue mode distribuisca il lavoro tra i worker:

```bash
# Crea un workflow "lento" (usa nodo Wait 5s) e attivalo
# Poi invia 10 richieste in parallelo

for i in $(seq 1 10); do
    curl -s -X POST http://localhost:5678/webhook/stress-test \
        -H "Content-Type: application/json" \
        -d "{\"request_id\": $i}" &
done
wait

# Controlla i log dei worker
docker compose logs n8n-worker --tail=50 | grep "execution\|job\|queue"

# Verifica le esecuzioni completate
curl -s -H "X-N8N-API-KEY: $N8N_API_KEY" \
    http://localhost:5678/api/v1/executions?limit=15 | \
    python3 -c "
import json, sys
data = json.load(sys.stdin)
execs = data.get('data', [])
statuses = [e.get('status', 'unknown') for e in execs]
from collections import Counter
print('Distribuzione stati:', Counter(statuses))
"
```

### Esercizio 4 — Backup e Restore (30 min)

1. Crea un workflow di test e salvalo
2. Esegui il backup manuale: `/opt/n8n/backup.sh`
3. Elimina il workflow dalla UI
4. Esegui il restore dal backup
5. Verifica che il workflow sia tornato

```bash
# Backup
/opt/n8n/backup.sh

# Lista backup
ls -lh /opt/n8n/backups/

# Identifica il backup più recente
LATEST=$(ls /opt/n8n/backups/n8n_backup_*_db.dump | sort | tail -1)
BACKUP_NAME=$(basename "$LATEST" _db.dump)
echo "Backup più recente: $BACKUP_NAME"

# Dopo aver eliminato il workflow dalla UI:
/opt/n8n/restore.sh "$BACKUP_NAME"
```

---

## Checklist Produzione

Prima di andare live, verificare ogni punto:

```
PREREQUISITI TECNICI:
[ ] N8N_ENCRYPTION_KEY archiviata in password manager (non solo in .env)
[ ] PostgreSQL con volume separato e backup automatico
[ ] Redis con password abilitata
[ ] Traefik con HTTPS e redirect HTTP→HTTPS
[ ] n8n esposto solo su 127.0.0.1 (Traefik come unico ingress)
[ ] Backup testato con restore effettivo (non basta il file)

SICUREZZA:
[ ] Nessun secret hard-coded nei workflow (usare variabili n8n)
[ ] Account admin con password robusta (>= 16 caratteri)
[ ] Disabilitata telemetria se dati sensibili
[ ] Log retention configurata (EXECUTIONS_DATA_MAX_AGE)
[ ] Firewall: solo porte 80/443 aperte su Internet

OSSERVABILITÀ:
[ ] Health check attivo (/healthz)
[ ] Alert su failure rate > 5%
[ ] Alert su worker down
[ ] Log centralizzati (n8n logs → Loki o CloudWatch)
[ ] Backup completato notificato (via email o Slack)

OPERATIVITÀ:
[ ] Runbook di upgrade documentato
[ ] Runbook di disaster recovery documentato con RTO/RPO
[ ] Cron backup attivo e verificato
[ ] Procedura rollback testata
```

---

## Troubleshooting Comune

```
PROBLEMA: n8n non si avvia (errore DB connection)
CAUSA:    PostgreSQL non ancora pronto
SOLUZIONE: docker compose logs n8n-db → verificare healthcheck
           Attendere 30-60 secondi dopo il primo avvio

PROBLEMA: Credenziali n8n non funzionano dopo restore
CAUSA:    N8N_ENCRYPTION_KEY nel .env non corrisponde al backup
SOLUZIONE: Usare l'encryption key del backup originale
           Aggiornare .env e riavviare

PROBLEMA: Worker non prende i job (queue mode)
CAUSA:    Redis non raggiungibile dal worker, o password errata
SOLUZIONE: docker exec n8n-worker redis-cli -h n8n-redis -a $KEY ping
           Verificare QUEUE_BULL_REDIS_PASSWORD uguale su main e worker

PROBLEMA: Webhook non ricevuti
CAUSA:    WEBHOOK_URL non corrisponde all'URL effettivo di n8n
SOLUZIONE: Impostare WEBHOOK_URL=https://<dominio-effettivo>/
           Verificare che Traefik stia instradando correttamente

PROBLEMA: Esecuzioni bloccate in "running"
CAUSA:    Worker crashato durante un'esecuzione
SOLUZIONE: docker compose restart n8n-worker
           Le esecuzioni orfane si azzerano dopo il riavvio
```

---

## Riferimenti

- n8n Self-Hosting Docs: https://docs.n8n.io/hosting/
- n8n Queue Mode: https://docs.n8n.io/hosting/scaling/queue-mode/
- Traefik + Let's Encrypt: https://doc.traefik.io/traefik/user-guides/docker-compose/acme-http/
- PostgreSQL 16 Docker: https://hub.docker.com/_/postgres
- Redis 7 Docker: https://hub.docker.com/_/redis
- OpenTelemetry n8n: https://docs.n8n.io/hosting/configuration/environment-variables/monitoring/
- n8n Community Forum: https://community.n8n.io
- Modulo sorgente: `09-n8n-guida-completa-self-hosted.md`
