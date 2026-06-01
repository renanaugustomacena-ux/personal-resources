---
corso: "Automazioni e Flussi di Lavoro"
fase: "3 — Piattaforme"
modulo: 9
titolo: "n8n — Guida Completa al Self-Hosting e Workflow Avanzati"
versione: "n8n 1.x LTS, Postgres 16+, Redis 7+, Traefik 3.x"
livello: "competent → proficient"
prerequisiti:
  - "Moduli 01-04"
  - "Docker basics"
  - "Reverse proxy (Nginx/Traefik)"
  - "Postgres/Redis basics"
obiettivi:
  - "Deployare n8n self-hosted in produzione con HTTPS, Postgres e Redis"
  - "Configurare queue mode con worker scaling per carichi elevati"
  - "Implementare secret management tramite vault e variabili d'ambiente"
  - "Progettare strategie di backup e disaster recovery per workflow e credentials"
  - "Integrare osservabilita con OpenTelemetry e monitorare metriche n8n"
tag: [n8n, self-hosting, docker, workflow, iPaaS, open-source, automazione]
---

# n8n — Guida Completa al Self-Hosting e Workflow Avanzati

> **Modulo del corso:** Automazioni e Flussi di Lavoro
> **Posizione:** Fase 3 — Piattaforme · Modulo 09
> **Prerequisiti:** Moduli 01-04; Docker basics; reverse proxy concept (Nginx/Traefik); Postgres/Redis basics.
> **Obiettivi:** deploy n8n self-hosted in produzione: HTTPS, Postgres backend, Redis queue, secret management, backup, OTel, vault integration.
> **Tempo:** lettura 90 min · lab 360 min
> **Livello:** competent → proficient
> **Ultimo aggiornamento:** 2026-05-24
> **Versioni:** n8n 1.x (release LTS), Postgres 16+, Redis 7+, Traefik 3.x.

## Idee guida

1. **n8n = open-source iPaaS senza lock-in.** Workflow esportabili JSON, integrabile con Git per change management.
2. **Self-hosted in prod richiede Postgres + Redis.** SQLite default e per dev only.
3. **`.env` rotation = mandatory.** L'encryption key di n8n cifra tutti i credentials del DB; perdere significa rifare ogni connessione.
4. **DB-backup credentials warning.** Postgres backup contiene credentials cifrati con la stessa key di `.env`. Ruotare key richiede ri-cifratura.
5. **Vault integration > env vars per produzione.** HashiCorp Vault, AWS Secrets Manager: rotation automatica.

---

## Indice

- [Panoramica](#panoramica)
- [Architettura di n8n](#architettura-di-n8n)
- [Installazione con Docker](#installazione-con-docker)
- [Docker Compose per Produzione](#docker-compose-per-produzione)
- [Configurazione con systemd](#configurazione-con-systemd)
- [Database Backend: SQLite vs PostgreSQL](#database-backend-sqlite-vs-postgresql)
- [Reverse Proxy con Nginx](#reverse-proxy-con-nginx)
- [Reverse Proxy con Traefik](#reverse-proxy-con-traefik)
- [Variabili di Ambiente Essenziali](#variabili-di-ambiente-essenziali)
- [Configurazione Webhook](#configurazione-webhook)
- [Gestione delle Credenziali](#gestione-delle-credenziali)
- [Design Pattern per Workflow](#design-pattern-per-workflow)
- [Nodi di Error Handling](#nodi-di-error-handling)
- [Sub-Workflow e Modularità](#sub-workflow-e-modularità)
- [Community Nodes](#community-nodes)
- [Backup e Restore](#backup-e-restore)
- [Scaling: Queue Mode con Redis e Bull](#scaling-queue-mode-con-redis-e-bull)
- [Monitoring e Observability](#monitoring-e-observability)
- [Security Hardening](#security-hardening)
- [Procedure di Upgrade](#procedure-di-upgrade)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

n8n è una piattaforma di workflow automation open source, distribuita con licenza fair-code (Sustainable Use License), che consente di creare flussi di integrazione visuale tra servizi, API e sistemi interni. A differenza delle piattaforme SaaS come Zapier o Make, n8n può essere completamente self-hosted, garantendo il pieno controllo sui dati, sulle credenziali e sulla logica di automazione. Questa caratteristica lo rende particolarmente adatto per ambienti enterprise, organizzazioni con requisiti di compliance stringenti (GDPR, HIPAA) e team di sviluppo che necessitano di personalizzazioni profonde.

L'architettura di n8n è basata su Node.js e TypeScript, con un'interfaccia web costruita su Vue.js. Il sistema supporta oltre 400 nodi nativi che coprono le integrazioni più comuni — da database relazionali a servizi cloud, da sistemi CRM a piattaforme di messaggistica. La possibilità di scrivere codice JavaScript o Python direttamente nei nodi Function e Code rende n8n estremamente flessibile, eliminando le limitazioni tipiche delle piattaforme puramente no-code.

In questa guida approfondita analizzeremo ogni aspetto del self-hosting di n8n: dall'installazione iniziale con Docker alla configurazione di un ambiente di produzione robusto con PostgreSQL, reverse proxy, queue mode per la scalabilità orizzontale, e le pratiche di sicurezza necessarie per esporre l'istanza in modo sicuro. Ogni sezione include configurazioni reali, comandi verificati e considerazioni operative per ambienti di produzione.

---

## Architettura di n8n

Prima di procedere con l'installazione, è fondamentale comprendere i componenti architetturali di n8n per prendere decisioni informate sulla configurazione.

### Componenti Principali

n8n è composto da diversi moduli interni che cooperano per eseguire i workflow:

- **Editor UI**: l'interfaccia web Vue.js che permette la creazione visuale dei workflow. Viene servita dal processo principale di n8n e comunica con il backend tramite REST API e WebSocket per gli aggiornamenti in tempo reale.
- **Workflow Engine**: il motore di esecuzione che interpreta i nodi del workflow, gestisce il passaggio dei dati tra i nodi e coordina l'esecuzione sequenziale o parallela delle operazioni.
- **Trigger Manager**: gestisce i trigger attivi (webhook, polling, cron) e si occupa di avviare l'esecuzione dei workflow quando le condizioni di trigger sono soddisfatte.
- **Credential Manager**: modulo responsabile della cifratura, archiviazione e decifratura delle credenziali. Utilizza una encryption key unica per istanza.
- **Database Layer**: astrazione per la persistenza dei dati. Supporta SQLite (sviluppo/piccole installazioni) e PostgreSQL (produzione). MySQL è supportato ma deprecato.

### Flusso di Esecuzione

Quando un workflow viene attivato, il processo segue questa sequenza: il Trigger Manager rileva l'evento (webhook in arrivo, schedule cron, polling su una risorsa), crea un'esecuzione nel database, e passa il controllo al Workflow Engine. Il motore attraversa il grafo dei nodi dall'inizio alla fine, eseguendo ogni nodo in sequenza, passando l'output di ciascun nodo come input del successivo. In caso di branching (nodi IF, Switch, Router), il motore segue il percorso corrispondente alla condizione valutata. Gli errori vengono catturati dal sistema di error handling, che può attivare nodi Error Trigger o percorsi alternativi definiti dall'utente.

---

## Installazione con Docker

Docker è il metodo di installazione raccomandato per n8n. L'immagine ufficiale `n8nio/n8n` è disponibile su Docker Hub e viene aggiornata ad ogni release.

### Quick Start per Sviluppo

Per un'installazione rapida di sviluppo locale:

```bash
docker run -d \
  --name n8n \
  --restart unless-stopped \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n:latest
```

Questo comando avvia n8n con SQLite come database (default), espone la porta 5678 e persiste i dati in un volume Docker. L'interfaccia è accessibile su `http://localhost:5678`.

### Variabili di Ambiente Fondamentali

Anche nell'installazione più semplice, è consigliato impostare alcune variabili di ambiente:

```bash
docker run -d \
  --name n8n \
  --restart unless-stopped \
  -p 5678:5678 \
  -e N8N_ENCRYPTION_KEY="chiave-segreta-molto-lunga-e-casuale" \
  -e N8N_HOST="n8n.example.com" \
  -e N8N_PORT=5678 \
  -e N8N_PROTOCOL=https \
  -e WEBHOOK_URL="https://n8n.example.com/" \
  -e GENERIC_TIMEZONE="Europe/Rome" \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n:latest
```

La variabile `N8N_ENCRYPTION_KEY` è critica: viene utilizzata per cifrare le credenziali archiviate nel database. Se viene persa o cambiata, tutte le credenziali salvate diventano illeggibili. È fondamentale documentarla e archiviarla in modo sicuro (ad esempio in un password manager o in un sistema di secrets management come Vault).

### Considerazioni sui Volumi

Il volume `/home/node/.n8n` contiene:
- Il database SQLite (`database.sqlite`)
- Il file di configurazione
- Le credenziali cifrate (all'interno del database)
- I log delle esecuzioni

Per ambienti di produzione, è preferibile montare un path host esplicito anziché un volume Docker anonimo:

```bash
mkdir -p /opt/n8n/data
chown -R 1000:1000 /opt/n8n/data  # n8n gira come utente node (UID 1000)

docker run -d \
  --name n8n \
  --restart unless-stopped \
  -p 5678:5678 \
  -v /opt/n8n/data:/home/node/.n8n \
  n8nio/n8n:latest
```

L'impostazione corretta dei permessi (UID 1000) è essenziale perché il container n8n esegue il processo come utente `node`, non come root. Un errore comune è dimenticare il `chown`, causando errori di permesso all'avvio.

---

## Docker Compose per Produzione

Per un deployment di produzione, Docker Compose permette di orchestrare n8n insieme ai servizi dipendenti (database, reverse proxy) in modo dichiarativo e riproducibile.

### Configurazione Completa con PostgreSQL

```yaml
version: '3.8'

services:
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
    networks:
      - n8n-internal

  n8n:
    image: n8nio/n8n:latest
    container_name: n8n
    restart: unless-stopped
    depends_on:
      n8n-db:
        condition: service_healthy
    environment:
      # Database
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: n8n-db
      DB_POSTGRESDB_PORT: 5432
      DB_POSTGRESDB_DATABASE: n8n
      DB_POSTGRESDB_USER: n8n
      DB_POSTGRESDB_PASSWORD: "${N8N_DB_PASSWORD}"
      # Encryption
      N8N_ENCRYPTION_KEY: "${N8N_ENCRYPTION_KEY}"
      # Networking
      N8N_HOST: "${N8N_DOMAIN}"
      N8N_PORT: 5678
      N8N_PROTOCOL: https
      WEBHOOK_URL: "https://${N8N_DOMAIN}/"
      # Timezone
      GENERIC_TIMEZONE: Europe/Rome
      TZ: Europe/Rome
      # Executions
      EXECUTIONS_DATA_PRUNE: "true"
      EXECUTIONS_DATA_MAX_AGE: 168  # 7 giorni in ore
      EXECUTIONS_DATA_SAVE_ON_ERROR: all
      EXECUTIONS_DATA_SAVE_ON_SUCCESS: all
      EXECUTIONS_DATA_SAVE_ON_PROGRESS: "true"
      EXECUTIONS_DATA_SAVE_MANUAL_EXECUTIONS: "true"
    volumes:
      - n8n_data:/home/node/.n8n
      - n8n_files:/files
    ports:
      - "127.0.0.1:5678:5678"
    networks:
      - n8n-internal
      - web

volumes:
  n8n_db_data:
    driver: local
  n8n_data:
    driver: local
  n8n_files:
    driver: local

networks:
  n8n-internal:
    internal: true
  web:
    external: true
```

Il file `.env` associato:

```bash
N8N_DB_PASSWORD=una-password-molto-sicura-per-postgresql
N8N_ENCRYPTION_KEY=una-chiave-di-cifratura-lunga-almeno-32-caratteri
N8N_DOMAIN=n8n.example.com
```

### Punti Chiave della Configurazione

La rete `n8n-internal` è dichiarata come `internal: true`, il che significa che i container connessi a questa rete non hanno accesso diretto a Internet. Questo isola il database PostgreSQL dalla rete esterna. n8n è connesso sia alla rete interna (per raggiungere il database) sia alla rete `web` esterna (per ricevere traffico dal reverse proxy).

Il binding della porta su `127.0.0.1:5678:5678` assicura che n8n sia raggiungibile solo da localhost, non dall'esterno. Tutto il traffico esterno deve passare attraverso il reverse proxy.

La direttiva `depends_on` con `condition: service_healthy` garantisce che n8n non si avvii finché PostgreSQL non è pronto ad accettare connessioni, evitando errori di connessione al database durante i primi secondi di avvio.

---

## Configurazione con systemd

Per chi preferisce un'installazione nativa senza Docker, n8n può essere installato tramite npm e gestito come servizio systemd.

### Installazione

```bash
# Installare Node.js 18+ (LTS)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo bash -
sudo apt-get install -y nodejs

# Installare n8n globalmente
sudo npm install -g n8n

# Creare utente dedicato
sudo useradd -r -m -d /opt/n8n -s /bin/bash n8n

# Creare directory dati
sudo mkdir -p /opt/n8n/.n8n
sudo chown -R n8n:n8n /opt/n8n
```

### Unit File systemd

Creare il file `/etc/systemd/system/n8n.service`:

```ini
[Unit]
Description=n8n Workflow Automation
Documentation=https://docs.n8n.io
After=network.target postgresql.service
Wants=postgresql.service

[Service]
Type=simple
User=n8n
Group=n8n
WorkingDirectory=/opt/n8n

Environment="N8N_ENCRYPTION_KEY=chiave-segreta-molto-lunga"
Environment="DB_TYPE=postgresdb"
Environment="DB_POSTGRESDB_HOST=localhost"
Environment="DB_POSTGRESDB_PORT=5432"
Environment="DB_POSTGRESDB_DATABASE=n8n"
Environment="DB_POSTGRESDB_USER=n8n"
Environment="DB_POSTGRESDB_PASSWORD=password-db"
Environment="N8N_HOST=n8n.example.com"
Environment="N8N_PORT=5678"
Environment="N8N_PROTOCOL=https"
Environment="WEBHOOK_URL=https://n8n.example.com/"
Environment="GENERIC_TIMEZONE=Europe/Rome"
Environment="NODE_ENV=production"

ExecStart=/usr/bin/n8n start
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=n8n

# Hardening
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/n8n
PrivateTmp=yes
ProtectKernelTunables=yes
ProtectControlGroups=yes

[Install]
WantedBy=multi-user.target
```

### Abilitazione e Avvio

```bash
sudo systemctl daemon-reload
sudo systemctl enable n8n
sudo systemctl start n8n
sudo systemctl status n8n

# Visualizzare i log
sudo journalctl -u n8n -f
```

Le direttive di hardening nella sezione `[Service]` applicano il principio del minimo privilegio: `NoNewPrivileges` impedisce l'escalation dei privilegi, `ProtectSystem=strict` monta il filesystem in sola lettura (eccetto i percorsi esplicitamente consentiti), e `PrivateTmp` isola la directory temporanea del servizio.

---

## Database Backend: SQLite vs PostgreSQL

La scelta del database backend è una delle decisioni architetturali più importanti per un'istanza n8n di produzione.

### SQLite

SQLite è il default ed è adatto per:
- Sviluppo locale e testing
- Istanze personali con pochi workflow
- Meno di 10 workflow attivi con esecuzioni poco frequenti

Vantaggi: zero configurazione, nessuna dipendenza esterna, backup semplice (copia del file). Svantaggi: non supporta accesso concorrente efficiente (problema nel queue mode), nessuna possibilità di scaling orizzontale, performance degradate con database grandi (>500MB).

### PostgreSQL

PostgreSQL è raccomandato per qualsiasi ambiente di produzione:

```sql
-- Creazione database e utente
CREATE USER n8n WITH PASSWORD 'password-sicura';
CREATE DATABASE n8n OWNER n8n ENCODING 'UTF8' LC_COLLATE 'C' LC_CTYPE 'C' TEMPLATE template0;
GRANT ALL PRIVILEGES ON DATABASE n8n TO n8n;
```

Configurazione ottimale in `postgresql.conf` per un server con 4GB di RAM dedicati a PostgreSQL:

```ini
# Memory
shared_buffers = 1GB
effective_cache_size = 3GB
work_mem = 16MB
maintenance_work_mem = 256MB

# WAL
wal_buffers = 32MB
checkpoint_completion_target = 0.9
max_wal_size = 2GB
min_wal_size = 512MB

# Query Planning
random_page_cost = 1.1  # SSD
effective_io_concurrency = 200  # SSD

# Connections
max_connections = 100
```

### Migrazione da SQLite a PostgreSQL

n8n fornisce un comando di migrazione integrato:

```bash
# Esportare i dati da SQLite
n8n export:workflow --all --output=workflows_backup.json
n8n export:credentials --all --output=credentials_backup.json

# Cambiare la configurazione del database a PostgreSQL
# (aggiornare le variabili di ambiente)

# Importare i dati in PostgreSQL
n8n import:workflow --input=workflows_backup.json
n8n import:credentials --input=credentials_backup.json
```

È fondamentale che la `N8N_ENCRYPTION_KEY` sia identica tra le due installazioni, altrimenti le credenziali non potranno essere decifrate dopo l'importazione.

---

## Reverse Proxy con Nginx

Un reverse proxy è essenziale per esporre n8n in produzione: gestisce la terminazione TLS, i certificati SSL, e può aggiungere header di sicurezza.

### Configurazione Nginx Completa

```nginx
upstream n8n_backend {
    server 127.0.0.1:5678;
    keepalive 32;
}

server {
    listen 80;
    server_name n8n.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name n8n.example.com;

    # Certificati SSL (Let's Encrypt con certbot)
    ssl_certificate /etc/letsencrypt/live/n8n.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/n8n.example.com/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/n8n.example.com/chain.pem;

    # TLS Security
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers on;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Limits
    client_max_body_size 50m;

    location / {
        proxy_pass http://n8n_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 600s;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        chunked_transfer_encoding on;
    }
}
```

La direttiva `proxy_set_header Upgrade` e `Connection "upgrade"` è essenziale per il supporto WebSocket, che n8n utilizza per aggiornare l'interfaccia in tempo reale durante l'esecuzione dei workflow. Senza queste direttive, l'editor funziona ma non mostra gli aggiornamenti live.

---

## Reverse Proxy con Traefik

Traefik è un'alternativa a Nginx particolarmente adatta in ambienti containerizzati perché può scoprire automaticamente i servizi Docker tramite label.

### Configurazione Traefik con Docker Compose

```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v3.0
    container_name: traefik
    restart: unless-stopped
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--entrypoints.web.http.redirections.entrypoint.to=websecure"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik_letsencrypt:/letsencrypt
    networks:
      - web

  n8n:
    image: n8nio/n8n:latest
    container_name: n8n
    restart: unless-stopped
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.n8n.rule=Host(`n8n.example.com`)"
      - "traefik.http.routers.n8n.entrypoints=websecure"
      - "traefik.http.routers.n8n.tls.certresolver=letsencrypt"
      - "traefik.http.services.n8n.loadbalancer.server.port=5678"
    environment:
      N8N_HOST: n8n.example.com
      N8N_PROTOCOL: https
      WEBHOOK_URL: "https://n8n.example.com/"
      N8N_ENCRYPTION_KEY: "${N8N_ENCRYPTION_KEY}"
    volumes:
      - n8n_data:/home/node/.n8n
    networks:
      - web

volumes:
  traefik_letsencrypt:
  n8n_data:

networks:
  web:
    external: true
```

Traefik gestisce automaticamente il provisioning e il rinnovo dei certificati Let's Encrypt tramite la HTTP-01 challenge. Le label sul container n8n configurano il routing senza necessità di file di configurazione separati.

---

## Variabili di Ambiente Essenziali

n8n è configurato interamente tramite variabili di ambiente. Ecco le categorie più importanti con le relative variabili:

### Configurazione Base

| Variabile | Descrizione | Default |
|-----------|-------------|---------|
| `N8N_HOST` | Hostname dell'istanza | `localhost` |
| `N8N_PORT` | Porta di ascolto | `5678` |
| `N8N_PROTOCOL` | Protocollo (http/https) | `http` |
| `N8N_ENCRYPTION_KEY` | Chiave per cifratura credenziali | Generata automaticamente |
| `GENERIC_TIMEZONE` | Timezone per gli schedule | `America/New_York` |
| `N8N_USER_FOLDER` | Directory dati utente | `~/.n8n` |

### Esecuzioni

| Variabile | Descrizione | Default |
|-----------|-------------|---------|
| `EXECUTIONS_PROCESS` | Modalità esecuzione (`main` o `own`) | `own` |
| `EXECUTIONS_TIMEOUT` | Timeout esecuzioni in secondi | `-1` (nessun timeout) |
| `EXECUTIONS_TIMEOUT_MAX` | Timeout massimo impostabile dall'utente | `3600` |
| `EXECUTIONS_DATA_PRUNE` | Eliminare vecchie esecuzioni | `true` |
| `EXECUTIONS_DATA_MAX_AGE` | Età massima esecuzioni in ore | `336` (14 giorni) |

### Sicurezza

| Variabile | Descrizione | Default |
|-----------|-------------|---------|
| `N8N_BASIC_AUTH_ACTIVE` | Attivare autenticazione base (deprecato) | `false` |
| `N8N_USER_MANAGEMENT_DISABLED` | Disabilitare gestione utenti | `false` |
| `N8N_BLOCK_ENV_ACCESS_IN_NODE` | Bloccare accesso env nei nodi | `false` |
| `N8N_TEMPLATES_ENABLED` | Abilitare template dalla community | `true` |

---

## Configurazione Webhook

I webhook sono il meccanismo principale attraverso il quale n8n riceve eventi esterni in tempo reale. Una configurazione corretta è cruciale per il funzionamento dei workflow trigger-based.

### WEBHOOK_URL

La variabile `WEBHOOK_URL` definisce l'URL base utilizzato per generare gli endpoint webhook. Deve corrispondere esattamente all'URL pubblico attraverso il quale n8n è raggiungibile:

```bash
WEBHOOK_URL=https://n8n.example.com/
```

Se questa variabile non è configurata correttamente, i webhook generati dai nodi Webhook conterranno URL errati. Un errore frequente è dimenticare lo slash finale o utilizzare l'indirizzo IP interno anziché il dominio pubblico.

### Percorsi Webhook

n8n genera due endpoint per ogni nodo Webhook nel workflow:
- **Test URL**: `https://n8n.example.com/webhook-test/<webhook-id>` — attivo solo quando il workflow è aperto nell'editor e si clicca "Listen for Test Event"
- **Production URL**: `https://n8n.example.com/webhook/<webhook-id>` — attivo quando il workflow è attivato in produzione

### Webhook Path Personalizzati

È possibile definire path personalizzati nel nodo Webhook per ottenere URL più leggibili:

```
Path: /api/ordini/nuovo
→ https://n8n.example.com/webhook/api/ordini/nuovo
```

### Considerazioni di Sicurezza per i Webhook

I webhook sono endpoint pubblici. Per proteggerli si possono adottare diverse strategie:

1. **Header Authentication**: configurare il nodo Webhook per verificare un header specifico (es. `X-Webhook-Secret`)
2. **IP Whitelisting**: nel reverse proxy, limitare l'accesso agli endpoint webhook a determinati IP
3. **HMAC Validation**: verificare la firma HMAC del payload nel nodo Function successivo al Webhook

Esempio di validazione HMAC in un nodo Code:

```javascript
const crypto = require('crypto');
const secret = $env.WEBHOOK_SECRET;
const signature = $input.first().headers['x-hub-signature-256'];
const payload = JSON.stringify($input.first().body);
const expectedSignature = 'sha256=' + crypto
  .createHmac('sha256', secret)
  .update(payload)
  .digest('hex');

if (signature !== expectedSignature) {
  throw new Error('Invalid webhook signature');
}

return $input.all();
```

---

## Gestione delle Credenziali

n8n cifra tutte le credenziali a riposo utilizzando l'algoritmo AES-256-CBC con la chiave definita in `N8N_ENCRYPTION_KEY`. Le credenziali sono archiviate nel database e sono associate ai workflow che le utilizzano.

### Tipi di Credenziali

n8n supporta diversi meccanismi di autenticazione a seconda del servizio:
- **API Key**: una chiave statica inserita nell'header o nei parametri della richiesta
- **OAuth2**: flusso completo con authorization code grant, gestione automatica del refresh token
- **Basic Auth**: username e password
- **Custom**: credenziali personalizzate per nodi custom

### OAuth2 Callback URL

Per le integrazioni OAuth2, n8n necessita di un callback URL configurato sia nel servizio esterno sia accessibile pubblicamente:

```
https://n8n.example.com/rest/oauth2-credential/callback
```

Questo URL deve essere aggiunto come "Redirect URI" nelle impostazioni dell'applicazione OAuth2 del servizio esterno (Google, GitHub, Slack, ecc.).

### Condivisione Credenziali tra Utenti

Con il user management attivo, le credenziali sono private per default. È possibile condividerle con altri utenti dell'istanza tramite la funzione di sharing, specificando i permessi (lettura o lettura/scrittura).

### Backup delle Credenziali

Le credenziali possono essere esportate tramite CLI, ma il file risultante contiene dati cifrati che sono utilizzabili solo con la stessa `N8N_ENCRYPTION_KEY`:

```bash
n8n export:credentials --all --output=credentials_backup.json
```

---

## Design Pattern per Workflow

Dopo anni di utilizzo della community, sono emersi diversi pattern consolidati per la progettazione di workflow n8n efficaci e manutenibili.

### Pattern: Data Transformation Pipeline

Questo pattern è il più comune: una sequenza lineare di nodi che trasformano progressivamente i dati. Esempio tipico — sincronizzazione dati da un CRM a un database:

```
Webhook → Set (normalizza campi) → IF (filtra record validi)
  → Sì: Postgres (upsert) → Slack (notifica successo)
  → No: Slack (notifica errore con dettagli)
```

### Pattern: Fan-Out / Fan-In

Utile quando un singolo input deve essere elaborato da più servizi in parallelo, e i risultati devono essere aggregati:

```
Trigger → Split In Batches
  → Branch 1: API Servizio A
  → Branch 2: API Servizio B
  → Branch 3: API Servizio C
→ Merge → Aggregazione → Output
```

### Pattern: Retry con Backoff Esponenziale

Per chiamate API che possono fallire temporaneamente, si implementa un retry con backoff usando un loop:

```
HTTP Request → IF (successo?)
  → Sì: Prosegui
  → No: Wait (backoff calcolato) → Incrementa contatore → IF (tentativi < max?)
    → Sì: Torna a HTTP Request
    → No: Error (notifica fallimento permanente)
```

### Pattern: Idempotenza

Per webhook che possono ricevere lo stesso evento più volte, si implementa il controllo di idempotenza:

```
Webhook → Postgres (cerca event_id) → IF (già processato?)
  → Sì: Respond to Webhook (200 OK, skip)
  → No: Processa → Postgres (salva event_id) → Respond to Webhook (200 OK)
```

### Pattern: Workflow Orchestrator

Un workflow principale che coordina l'esecuzione di sub-workflow specializzati:

```
Schedule Trigger → Execute Workflow (ETL Clienti) → IF (successo?)
  → Sì: Execute Workflow (ETL Ordini) → Execute Workflow (Report)
  → No: Slack (notifica errore ETL Clienti)
```

---

## Nodi di Error Handling

n8n fornisce diversi meccanismi per gestire gli errori nei workflow, dalla gestione a livello di singolo nodo fino alla gestione globale.

### Error Trigger Workflow

Si può configurare un workflow dedicato che viene eseguito ogni volta che un qualsiasi workflow fallisce. Questo workflow si attiva con il nodo "Error Trigger" e riceve come input le informazioni sull'errore:

```json
{
  "execution": {
    "id": "12345",
    "url": "https://n8n.example.com/execution/12345",
    "error": {
      "message": "HTTP 429 Too Many Requests",
      "node": "HTTP Request"
    },
    "lastNodeExecuted": "HTTP Request",
    "mode": "trigger"
  },
  "workflow": {
    "id": "42",
    "name": "Sync CRM Data"
  }
}
```

### Gestione Errori per Nodo

Ogni nodo può essere configurato con un "Error Output" che, in caso di fallimento, devia l'esecuzione verso un percorso alternativo anziché interrompere il workflow. Questo si configura nelle impostazioni del nodo sotto "On Error" selezionando "Continue Using Error Output".

### Pattern di Retry

Il nodo "Retry On Fail" permette di configurare automaticamente i tentativi di ripetizione con parametri di backoff:

- **Max Tries**: numero massimo di tentativi (es. 3)
- **Wait Between Tries**: tempo di attesa tra un tentativo e il successivo (in millisecondi)
- **Backoff**: se abilitato, aumenta progressivamente il tempo di attesa

---

## Sub-Workflow e Modularità

I sub-workflow sono workflow invocati da altri workflow tramite il nodo "Execute Workflow". Questa funzionalità è fondamentale per la modularizzazione e il riutilizzo della logica.

### Vantaggi dei Sub-Workflow

- **Riutilizzabilità**: la stessa logica può essere invocata da più workflow principali
- **Testabilità**: ogni sub-workflow può essere testato indipendentemente
- **Manutenibilità**: le modifiche a una logica comune vengono applicate in un unico punto
- **Leggibilità**: i workflow principali rimangono compatti e comprensibili

### Passaggio di Parametri

I dati vengono passati ai sub-workflow tramite l'input del nodo Execute Workflow e restituiti tramite il nodo finale del sub-workflow. È possibile passare parametri strutturati come JSON.

### Limitazioni

I sub-workflow vengono eseguiti nello stesso processo dell'esecuzione chiamante (in modalità `main`) o in un processo separato (in modalità `own`). In queue mode, i sub-workflow possono essere distribuiti su worker diversi, il che aggiunge latenza ma migliora la scalabilità.

---

## Community Nodes

I community nodes sono pacchetti npm che estendono n8n con integrazioni non disponibili nativamente. Vengono installati direttamente dall'interfaccia di n8n o tramite riga di comando.

### Installazione

Dall'interfaccia: Settings → Community Nodes → Install → inserire il nome del pacchetto npm.

Da CLI:

```bash
# Con Docker, montare un volume per i nodi personalizzati
docker run -d \
  -v n8n_custom_nodes:/home/node/.n8n/nodes \
  n8nio/n8n:latest

# Oppure installare nel container
docker exec -it n8n npm install n8n-nodes-nome-pacchetto
```

### Sicurezza dei Community Nodes

I community nodes eseguono codice arbitrario nel processo di n8n. È fondamentale:
- Verificare il codice sorgente prima dell'installazione
- Controllare la reputazione dell'autore e le stelle su GitHub
- Monitorare gli aggiornamenti per patch di sicurezza
- In ambienti enterprise, valutare l'uso della variabile `N8N_COMMUNITY_PACKAGES_ALLOW_TOOL_USAGE` per limitare i nodi utilizzabili nei tool degli agenti AI

---

## Backup e Restore

Una strategia di backup solida è essenziale per qualsiasi installazione di produzione.

### Cosa Sottoporre a Backup

1. **Database**: contiene workflow, credenziali (cifrate), esecuzioni, utenti
2. **N8N_ENCRYPTION_KEY**: senza questa chiave, le credenziali nel backup sono inutili
3. **Custom Nodes**: eventuali nodi della community installati
4. **File locali**: file caricati o generati dai workflow nella directory `/files`

### Backup con CLI n8n

```bash
#!/bin/bash
# Script di backup n8n
BACKUP_DIR="/backup/n8n/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Esportare workflow
n8n export:workflow --all --output="$BACKUP_DIR/workflows.json"

# Esportare credenziali
n8n export:credentials --all --output="$BACKUP_DIR/credentials.json"

# Backup database PostgreSQL
pg_dump -U n8n -h localhost n8n | gzip > "$BACKUP_DIR/database.sql.gz"

# Backup encryption key (da archivio sicuro, non dal backup stesso)
echo "REMINDER: Verificare che N8N_ENCRYPTION_KEY sia archiviata in modo sicuro" >> "$BACKUP_DIR/NOTES.txt"

# Pulizia backup vecchi (mantenere ultimi 30 giorni)
find /backup/n8n -maxdepth 1 -mtime +30 -type d -exec rm -rf {} +

echo "Backup completato in $BACKUP_DIR"
```

### Restore

```bash
# Ripristinare il database
gunzip -c database.sql.gz | psql -U n8n -h localhost n8n

# Oppure importare tramite CLI (assicurarsi che N8N_ENCRYPTION_KEY sia corretta)
n8n import:workflow --input=workflows.json
n8n import:credentials --input=credentials.json
```

---

## Scaling: Queue Mode con Redis e Bull

Per installazioni ad alto volume, n8n supporta una modalità queue che distribuisce l'esecuzione dei workflow su più worker, utilizzando Redis come message broker tramite la libreria Bull.

### Architettura Queue Mode

In queue mode, l'istanza n8n si divide in due ruoli:
- **Main Instance**: gestisce l'interfaccia web, i trigger, e inserisce i job nella coda Redis
- **Worker Instances**: prelevano i job dalla coda e li eseguono

Questo permette di scalare orizzontalmente il numero di worker in base al carico.

### Configurazione Docker Compose con Queue Mode

```yaml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: n8n-redis
    restart: unless-stopped
    command: redis-server --requirepass "${REDIS_PASSWORD}" --maxmemory 256mb --maxmemory-policy noeviction
    volumes:
      - redis_data:/data
    networks:
      - n8n-internal
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  n8n-main:
    image: n8nio/n8n:latest
    container_name: n8n-main
    restart: unless-stopped
    environment:
      EXECUTIONS_MODE: queue
      QUEUE_BULL_REDIS_HOST: redis
      QUEUE_BULL_REDIS_PORT: 6379
      QUEUE_BULL_REDIS_PASSWORD: "${REDIS_PASSWORD}"
      QUEUE_HEALTH_CHECK_ACTIVE: "true"
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: n8n-db
      DB_POSTGRESDB_PORT: 5432
      DB_POSTGRESDB_DATABASE: n8n
      DB_POSTGRESDB_USER: n8n
      DB_POSTGRESDB_PASSWORD: "${N8N_DB_PASSWORD}"
      N8N_ENCRYPTION_KEY: "${N8N_ENCRYPTION_KEY}"
      N8N_HOST: n8n.example.com
      N8N_PROTOCOL: https
      WEBHOOK_URL: "https://n8n.example.com/"
    depends_on:
      redis:
        condition: service_healthy
    ports:
      - "127.0.0.1:5678:5678"
    networks:
      - n8n-internal
      - web

  n8n-worker:
    image: n8nio/n8n:latest
    container_name: n8n-worker-1
    restart: unless-stopped
    command: n8n worker
    environment:
      EXECUTIONS_MODE: queue
      QUEUE_BULL_REDIS_HOST: redis
      QUEUE_BULL_REDIS_PORT: 6379
      QUEUE_BULL_REDIS_PASSWORD: "${REDIS_PASSWORD}"
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: n8n-db
      DB_POSTGRESDB_PORT: 5432
      DB_POSTGRESDB_DATABASE: n8n
      DB_POSTGRESDB_USER: n8n
      DB_POSTGRESDB_PASSWORD: "${N8N_DB_PASSWORD}"
      N8N_ENCRYPTION_KEY: "${N8N_ENCRYPTION_KEY}"
      QUEUE_BULL_REDIS_TIMEOUT_THRESHOLD: 60000
      N8N_CONCURRENCY_PRODUCTION_LIMIT: 10
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - n8n-internal

volumes:
  redis_data:

networks:
  n8n-internal:
    internal: true
  web:
    external: true
```

### Scaling dei Worker

Per aggiungere più worker, si può utilizzare `docker compose up --scale n8n-worker=3` o definire servizi worker multipli nel compose file. Ogni worker preleva job dalla stessa coda Redis, distribuendo naturalmente il carico.

La variabile `N8N_CONCURRENCY_PRODUCTION_LIMIT` limita il numero di esecuzioni concorrenti per singolo worker. Un valore di 10 significa che ogni worker può eseguire fino a 10 workflow contemporaneamente.

---

## Monitoring e Observability

### Health Check Endpoint

n8n espone un endpoint di health check configurabile:

```bash
curl https://n8n.example.com/healthz
# Risposta: {"status":"ok"}
```

### Metriche Prometheus

n8n può esporre metriche in formato Prometheus:

```bash
N8N_METRICS=true
N8N_METRICS_PREFIX=n8n_
# Endpoint: https://n8n.example.com/metrics
```

Metriche disponibili includono:
- `n8n_workflow_executions_total` (con label per workflow e stato)
- `n8n_workflow_execution_duration_seconds`
- `n8n_api_requests_total`
- Metriche Node.js standard (heap, event loop, GC)

### Dashboard Grafana

Con le metriche Prometheus è possibile costruire dashboard Grafana che visualizzano il volume di esecuzioni, i tassi di errore, la latenza delle esecuzioni e l'utilizzo delle risorse del sistema.

### Log Strutturati

n8n supporta output log in formato JSON per integrazione con sistemi di log management:

```bash
N8N_LOG_LEVEL=info
N8N_LOG_OUTPUT=console
```

I livelli disponibili sono: `silent`, `error`, `warn`, `info`, `verbose`, `debug`.

---

## Security Hardening

### Autenticazione e Autorizzazione

n8n include un sistema di user management con ruoli:
- **Owner**: controllo completo dell'istanza, gestione utenti
- **Admin**: gestione workflow e credenziali
- **Member**: accesso ai workflow condivisi

### Bloccare l'Accesso alle Variabili di Ambiente

Per impedire che i nodi Code/Function accedano alle variabili di ambiente (che potrebbero contenere segreti):

```bash
N8N_BLOCK_ENV_ACCESS_IN_NODE=true
```

### Limitare i Nodi Disponibili

È possibile restringere i nodi utilizzabili per ridurre la superficie di attacco:

```bash
NODES_EXCLUDE='["n8n-nodes-base.executeCommand","n8n-nodes-base.ssh"]'
```

Questo blocca l'uso dei nodi Execute Command e SSH, che permetterebbero l'esecuzione di comandi arbitrari sul server.

### Network Segmentation

Come visto nella configurazione Docker Compose, isolare la rete del database e di Redis tramite reti Docker interne (`internal: true`) impedisce l'accesso diretto da Internet a questi servizi.

### Rate Limiting per i Webhook

Configurare il rate limiting nel reverse proxy per proteggere i webhook da abusi:

```nginx
limit_req_zone $binary_remote_addr zone=n8n_webhooks:10m rate=30r/m;

location /webhook/ {
    limit_req zone=n8n_webhooks burst=10 nodelay;
    limit_req_status 429;
    proxy_pass http://n8n_backend;
    # ... altre direttive proxy
}
```

### Audit Log

Abilitare il logging dettagliato delle operazioni per tracciare le azioni degli utenti:

```bash
N8N_LOG_LEVEL=verbose
```

In ambienti enterprise con requisiti di compliance, è consigliabile inviare i log a un sistema centralizzato (ELK, Loki, Datadog) con retention configurata secondo le policy aziendali.

---

## Procedure di Upgrade

### Upgrade con Docker

```bash
# 1. Verificare le release notes per breaking changes
# https://docs.n8n.io/reference/release-notes/

# 2. Backup prima dell'upgrade
docker exec n8n n8n export:workflow --all --output=/home/node/.n8n/backup_workflows.json
docker exec n8n n8n export:credentials --all --output=/home/node/.n8n/backup_credentials.json

# 3. Backup del database PostgreSQL
docker exec n8n-db pg_dump -U n8n n8n | gzip > backup_db_$(date +%Y%m%d).sql.gz

# 4. Pull della nuova immagine
docker pull n8nio/n8n:latest

# 5. Stop e ricreare il container
docker compose down
docker compose up -d

# 6. Verificare lo stato
docker compose logs -f n8n
curl https://n8n.example.com/healthz
```

### Upgrade con systemd

```bash
# 1. Backup (come sopra)
# 2. Stop del servizio
sudo systemctl stop n8n

# 3. Aggiornare n8n
sudo npm update -g n8n

# 4. Riavviare
sudo systemctl start n8n
sudo journalctl -u n8n -f
```

### Migrazioni Database

n8n esegue automaticamente le migrazioni del database all'avvio. Non è necessario eseguire comandi di migrazione manuali. Tuttavia, è fondamentale avere un backup del database prima di ogni upgrade, in quanto le migrazioni possono essere irreversibili.

### Rollback

In caso di problemi dopo l'upgrade:

```bash
# Con Docker: specificare la versione precedente
docker compose down
# Modificare l'immagine nel compose file: n8nio/n8n:1.XX.X
docker compose up -d

# Ripristinare il database dal backup se necessario
gunzip -c backup_db_YYYYMMDD.sql.gz | docker exec -i n8n-db psql -U n8n n8n
```

---

## Best Practices

### Architettura dei Workflow

1. **Un workflow, una responsabilità**: evitare workflow monolitici che gestiscono troppi processi. Suddividere in sub-workflow modulari con responsabilità ben definite.
2. **Nomenclatura consistente**: adottare una convenzione di naming chiara, ad esempio `[Dominio] Azione - Dettaglio` (es. `[CRM] Sync Contatti - HubSpot → PostgreSQL`).
3. **Documentazione inline**: utilizzare i nodi Sticky Note per documentare la logica complessa direttamente nel workflow.
4. **Tagging sistematico**: assegnare tag ai workflow per organizzarli per dominio, priorità o team responsabile.

### Gestione degli Errori

5. **Error workflow globale**: configurare sempre un workflow di error handling globale che notifica il team via Slack, email o altro canale.
6. **Retry automatico**: per le chiamate API esterne, configurare sempre il retry con backoff esponenziale.
7. **Validazione input**: inserire nodi IF o Switch all'inizio dei workflow per validare la struttura dei dati in ingresso prima dell'elaborazione.

### Sicurezza Operativa

8. **Encryption key documentata**: archiviare la `N8N_ENCRYPTION_KEY` in un password manager aziendale o in un sistema di secrets management.
9. **Aggiornamenti regolari**: pianificare upgrade mensili per incorporare patch di sicurezza.
10. **Principle of Least Privilege**: assegnare a n8n solo le credenziali con i permessi minimi necessari per ogni integrazione.

### Performance

11. **Pruning delle esecuzioni**: configurare `EXECUTIONS_DATA_PRUNE=true` con un retention period adeguato per evitare che il database cresca indefinitamente.
12. **Batch processing**: per grandi volumi di dati, utilizzare Split In Batches per elaborare i record in gruppi, evitando timeout e consumo eccessivo di memoria.
13. **Timeout appropriati**: configurare `EXECUTIONS_TIMEOUT` per evitare che workflow bloccati consumino risorse indefinitamente.

---

## Troubleshooting

### Problema: Webhook Non Raggiungibili dall'Esterno

**Sintomi**: i servizi esterni non riescono a chiamare i webhook di n8n. I test dall'editor funzionano ma le esecuzioni in produzione non si attivano.

**Causa**: `WEBHOOK_URL` non configurato correttamente, reverse proxy non configurato per passare gli header necessari, o il workflow non è attivato (i production webhook sono attivi solo quando il workflow è "Active").

**Soluzione**: verificare che `WEBHOOK_URL` corrisponda esattamente all'URL pubblico. Controllare che il workflow sia attivato (toggle verde). Verificare la configurazione del reverse proxy con `curl -v https://n8n.example.com/webhook/test-webhook-id`. Controllare i log di n8n per eventuali errori: `docker compose logs n8n | grep webhook`.

### Problema: Credenziali Corrotte Dopo Migrazione

**Sintomi**: dopo la migrazione o il restore da backup, le credenziali risultano invalide. I nodi che le utilizzano mostrano errori di autenticazione.

**Causa**: la `N8N_ENCRYPTION_KEY` utilizzata nell'istanza attuale è diversa da quella con cui le credenziali sono state cifrate.

**Soluzione**: ripristinare la `N8N_ENCRYPTION_KEY` originale. Se la chiave è stata persa definitivamente, le credenziali dovranno essere reinserite manualmente in ogni nodo.

### Problema: Esecuzioni Bloccate in Stato "Running"

**Sintomi**: le esecuzioni appaiono come "Running" indefinitamente nella lista delle esecuzioni, anche se il workflow sembra non stare più facendo nulla.

**Causa**: crash del processo worker (in queue mode) o timeout del processo di esecuzione senza cleanup corretto. Può verificarsi anche dopo un riavvio del container durante un'esecuzione attiva.

**Soluzione**: configurare `EXECUTIONS_TIMEOUT` per impostare un timeout massimo. In queue mode, verificare che i worker siano attivi con `docker compose ps`. Per le esecuzioni bloccate, è possibile cancellarle manualmente dal database:

```sql
UPDATE execution_entity SET status = 'crashed', finished = true, "stoppedAt" = NOW()
WHERE status = 'running' AND "startedAt" < NOW() - INTERVAL '2 hours';
```

### Problema: Elevato Consumo di Memoria

**Sintomi**: il container o il processo n8n consuma progressivamente più memoria, fino a essere terminato dall'OOM killer.

**Causa**: workflow che elaborano grandi volumi di dati senza batching, memory leak in community nodes, o mancato pruning delle esecuzioni che causa la crescita del database in memoria.

**Soluzione**: implementare Split In Batches per i workflow con grandi dataset. Configurare `EXECUTIONS_DATA_PRUNE=true`. Limitare la memoria del container Docker con `mem_limit: 2g`. Monitorare l'utilizzo della memoria con le metriche Prometheus. Verificare se il problema è legato a un community node specifico disabilitandoli uno alla volta.

### Problema: Errori di Connessione al Database PostgreSQL

**Sintomi**: n8n non si avvia o si blocca con errori "Connection refused" o "FATAL: password authentication failed" nei log.

**Causa**: PostgreSQL non ancora pronto all'avvio di n8n, credenziali database errate, o limite connessioni raggiunto.

**Soluzione**: verificare che la direttiva `depends_on` con `condition: service_healthy` sia configurata nel Docker Compose. Controllare le credenziali nel file `.env`. Verificare `max_connections` in PostgreSQL e il numero di connessioni attive: `SELECT count(*) FROM pg_stat_activity WHERE datname = 'n8n';`.

---

## Riferimenti

- **Documentazione ufficiale n8n**: https://docs.n8n.io/
- **Repository GitHub n8n**: https://github.com/n8n-io/n8n
- **n8n Community Forum**: https://community.n8n.io/
- **Docker Hub n8n**: https://hub.docker.com/r/n8nio/n8n
- **Release Notes**: https://docs.n8n.io/reference/release-notes/
- **n8n Self-Hosting Guide**: https://docs.n8n.io/hosting/
- **n8n Queue Mode Documentation**: https://docs.n8n.io/hosting/scaling/queue-mode/
- **PostgreSQL Official Documentation**: https://www.postgresql.org/docs/16/
- **Nginx Reverse Proxy Guide**: https://nginx.org/en/docs/http/ngx_http_proxy_module.html
- **Traefik Documentation**: https://doc.traefik.io/traefik/
- **Redis Configuration**: https://redis.io/docs/management/config/

---

## Approfondimenti — note del 2026-04-27

> **Approfondimento — `.env` rotation procedure.** Per ruotare `N8N_ENCRYPTION_KEY` senza perdere workflow: (1) export workflow + credentials con vecchia key (`n8n export:workflow --all` + `n8n export:credentials --all --decrypted`); (2) genera nuova key, aggiorna `.env`; (3) re-import (`n8n import:workflow` + `n8n import:credentials`); (4) restart n8n. Backup integrale del volume di n8n PRIMA dell'operazione.

> **Errore comune — backup Postgres senza encryption key.** Sintomo: restore di backup su nuovo server n8n; tutti i credentials si vedono ma non si decifrano. Causa: backup ha cifrato ma la nuova installazione ha key diversa. Soluzione: copia `.env` (o `N8N_ENCRYPTION_KEY`) insieme al backup DB. Conserva entrambi insieme in vault sicuro.

---

## Letture e Riferimenti

### Documentazione ufficiale

- n8n Hosting — Configuration options: https://docs.n8n.io/hosting/configuration/configuration-examples/ (consultato: 2026-05-24)
- n8n Environment Variables Reference: https://docs.n8n.io/hosting/configuration/environment-variables/ (consultato: 2026-05-24)
- n8n Security Best Practices: https://docs.n8n.io/hosting/configuration/security/ (consultato: 2026-05-24)
- n8n Credentials — Encryption and Storage: https://docs.n8n.io/credentials/ (consultato: 2026-05-24)
- n8n Workflow Execution Data — Pruning and Retention: https://docs.n8n.io/hosting/configuration/configuration-examples/execution-data/ (consultato: 2026-05-24)
- Traefik — Let's Encrypt ACME Configuration: https://doc.traefik.io/traefik/https/acme/ (consultato: 2026-05-24)
- PostgreSQL Backup and Recovery: https://www.postgresql.org/docs/16/backup.html (consultato: 2026-05-24)

### Libri

- **"The DevOps Handbook"** — Gene Kim, Jez Humble, Patrick Debois, John Willis (IT Revolution Press). Principi di automazione infrastrutturale applicabili al self-hosting di piattaforme come n8n.
- **"Infrastructure as Code"** — Kief Morris (O'Reilly, 2a ed.). Pattern per gestione dichiarativa di infrastruttura, rilevante per deploy Docker Compose e configurazione n8n.

---

## Esercizi

1. **Lab — deploy n8n produzione.** Docker Compose con n8n + Postgres + Redis + Traefik + Let's Encrypt; configura HTTPS, secret in vault, backup giornaliero.
2. **Lab — workflow Git versioned.** Esporta workflow in JSON, commit in Git, deploy via webhook al merge.
3. **Stretch — n8n queue mode + worker scaling.** Setup queue mode con N worker, test load 100 webhook/min, misura latenza.

## Auto-valutazione

1. n8n SQLite vs Postgres: quando uno o l'altro?
2. Queue mode: cos'e e quando attivarlo?
3. `N8N_ENCRYPTION_KEY` rotation: procedura.
4. Vault integration vs env vars.
5. Workflow backup vs full backup: differenza.

## Collegamenti incrociati

- Modulo 10 — `10-make-integromat-guida-operativa.md`: alternativa SaaS.
- Modulo 14 — `14-zapier-guida-operativa.md`: confronto.
- Modulo 15 — `15-webhook-security-hmac-verifica.md`: HMAC in n8n.

## Glossario locale

| Termine | Definizione |
|---|---|
| **n8n** | Open-source iPaaS basato su Node.js. |
| **Self-hosting** | Deploy on-prem o private cloud. |
| **n8n Queue mode** | Architettura main + worker per scaling. |
| **`N8N_ENCRYPTION_KEY`** | Chiave per cifrare credentials nel DB. |
| **Workflow JSON export** | Esportabilita di un workflow come JSON. |
| **Traefik** | Reverse proxy con auto-Let's Encrypt. |
