---
Modulo del corso: 02 — Linux Power User
Capitolo: 28 — Nginx Configurazione Avanzata
Prerequisiti:
  - Conoscenza base di reti TCP/IP e HTTP (Moduli 18-19)
  - Amministrazione Linux (filesystem, servizi systemd, permessi — Moduli 5-10)
  - Fondamenti di crittografia e TLS (Modulo 15)
  - Esperienza con un editor di testo (vim/nano)
Obiettivi di apprendimento:
  - Comprendere l'architettura event-driven di Nginx e il modello master/worker
  - Padroneggiare la gerarchia dei contesti di configurazione e le regole di ereditarietà
  - Configurare reverse proxy, load balancing e health check per ambienti di produzione
  - Implementare hardening SSL/TLS con mTLS, OCSP stapling e cipher suite moderne
  - Attivare HTTP/2 e HTTP/3 (QUIC) con configurazione ottimale
  - Configurare rate limiting, caching e security headers secondo le best practice OWASP
  - Utilizzare Nginx come API gateway con auth_request e validazione JWT
  - Diagnosticare e risolvere i 20 problemi più comuni in produzione
  - Migrare configurazioni da Apache a Nginx
Tempo stimato: 12-16 ore (studio + esercizi)
Livello: Avanzato
Ultimo aggiornamento: 2026-05-23
Versioni di riferimento:
  - Nginx: 1.26.x (mainline), 1.24.x (stable)
  - OpenSSL: 3.2+
  - Let's Encrypt / Certbot: 3.x
---

# Nginx: Configurazione Avanzata — Guida Approfondita

> **Modulo 28** · **Aggiornamento:** 2026-05-23

## Idee guida
1. **`nginx -t` validate config before reload.**
2. **gzip + brotli compression.**
3. **HTTP/2 + HTTP/3 (QUIC) 1.25+.**
4. **Rate limit zones: `limit_req_zone`.**


## Indice

- [Panoramica](#panoramica)
- [Architettura Nginx](#architettura-nginx)
  - [Ciclo di Vita di una Richiesta](#ciclo-di-vita-di-una-richiesta)
  - [Event Loop e I/O Multiplexing](#event-loop-e-io-multiplexing)
- [Contesti di Configurazione e Ereditarietà](#contesti-di-configurazione-e-ereditarietà)
- [Server Blocks e Location Matching](#server-blocks-e-location-matching)
  - [Pattern try_files](#pattern-try_files)
  - [La Direttiva map](#la-direttiva-map)
- [Reverse Proxy](#reverse-proxy)
  - [Proxy Buffering Approfondito](#proxy-buffering-approfondito)
  - [Keepalive verso Upstream](#keepalive-verso-upstream)
- [Load Balancing](#load-balancing)
  - [Algoritmo random e Slow Start](#algoritmo-random-e-slow-start)
- [SSL/TLS Configurazione](#ssltls-configurazione)
  - [Catena di Certificati](#catena-di-certificati)
  - [mTLS — Autenticazione Client con Certificato](#mtls--autenticazione-client-con-certificato)
  - [Session Tickets vs Session Cache](#session-tickets-vs-session-cache)
- [Caching](#caching)
  - [Microcaching per Contenuti Dinamici](#microcaching-per-contenuti-dinamici)
  - [Cache Purging](#cache-purging)
- [Rate Limiting](#rate-limiting)
  - [Strategie Avanzate di Rate Limiting](#strategie-avanzate-di-rate-limiting)
- [Security Headers](#security-headers)
  - [Content Security Policy Approfondita](#content-security-policy-approfondita)
- [HTTP/2 e HTTP/3](#http2-e-http3)
  - [QUIC: Requisiti Infrastrutturali](#quic-requisiti-infrastrutturali)
- [Logging e Monitoring](#logging-e-monitoring)
  - [Log Rotation e Syslog](#log-rotation-e-syslog)
- [Performance Tuning](#performance-tuning)
- [Nginx come API Gateway](#nginx-come-api-gateway)
- [WebSocket Proxying Avanzato](#websocket-proxying-avanzato)
- [High Availability e Failover](#high-availability-e-failover)
- [Configurazione Completa di Produzione](#configurazione-completa-di-produzione)
- [Best Practices](#best-practices)
- [Debugging e Diagnostica](#debugging-e-diagnostica)
- [Troubleshooting](#troubleshooting)
- [Migrazione da Apache a Nginx](#migrazione-da-apache-a-nginx)
- [Esercizi](#esercizi)
- [Auto-valutazione](#auto-valutazione)
- [Letture Primarie Consigliate](#letture-primarie-consigliate)
- [Collegamenti Incrociati](#collegamenti-incrociati)
- [Glossario Locale](#glossario-locale)
- [Riferimenti](#riferimenti)

---

## Panoramica

Nginx (pronunciato "engine-x") è un web server, reverse proxy e load balancer ad alte performance, creato da Igor Sysoev nel 2004 per risolvere il problema C10K (gestire 10.000 connessioni simultanee). A differenza di Apache che usa un modello basato su processi/thread (un worker per connessione), Nginx utilizza un'architettura event-driven con I/O asincrono non bloccante, che permette a un singolo worker process di gestire migliaia di connessioni simultanee con un consumo di memoria minimo.

Oggi Nginx serve circa il 35% dei siti web globali ed è lo standard de facto per reverse proxy, terminazione SSL, load balancing e serving di contenuti statici. Questo documento copre la configurazione avanzata di Nginx dalla prospettiva di un system administrator Linux, con enfasi su scenari reali di produzione: reverse proxy per applicazioni backend, load balancing con health check, ottimizzazione SSL/TLS, caching, rate limiting e hardening della sicurezza.

La configurazione di Nginx è dichiarativa e gerarchica. Comprendere il meccanismo di ereditarietà delle direttive tra contesti (http → server → location) e l'algoritmo di matching delle location è fondamentale per evitare comportamenti inattesi che sono alla base della maggior parte dei problemi di configurazione.

---

## Architettura Nginx

```
┌──────────────────────────────────────────────────┐
│                  Master Process                    │
│  (lettura config, binding porte, gestione worker)  │
└───────────┬──────────┬──────────┬────────────────┘
            │          │          │
    ┌───────▼──┐ ┌─────▼────┐ ┌──▼─────────┐
    │ Worker 1 │ │ Worker 2 │ │ Worker N   │
    │          │ │          │ │            │
    │ Event    │ │ Event    │ │ Event      │
    │ Loop     │ │ Loop     │ │ Loop       │
    │          │ │          │ │            │
    │ epoll()  │ │ epoll()  │ │ epoll()    │
    │          │ │          │ │            │
    │ ~1000+   │ │ ~1000+   │ │ ~1000+    │
    │ connessioni│ connessioni│ connessioni │
    └──────────┘ └──────────┘ └────────────┘
```

### Configurazione Base del Worker

```nginx
# /etc/nginx/nginx.conf

# Utente del worker process
user www-data;

# Numero di worker — auto = un worker per CPU core
worker_processes auto;

# Binding dei worker ai CPU core (affinità)
worker_cpu_affinity auto;

# Limiti del processo
worker_rlimit_nofile 65535;

# PID file
pid /run/nginx.pid;

# Moduli
include /etc/nginx/modules-enabled/*.conf;

events {
    # Connessioni simultanee per worker
    worker_connections 4096;

    # Metodo di I/O multiplexing
    use epoll;  # Linux (default su Linux)

    # Accetta più connessioni alla volta
    multi_accept on;
}

http {
    # ── Impostazioni di base ─────────────────
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;  # Nascondi versione Nginx

    # ── MIME types ───────────────────────────
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # ── Logging ──────────────────────────────
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # ── Gzip ─────────────────────────────────
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 4;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript
               application/xml application/rss+xml
               image/svg+xml;

    # ── Include server blocks ────────────────
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
```

### Ciclo di Vita di una Richiesta

Ogni richiesta HTTP in Nginx attraversa una pipeline di fasi ben definite. Comprendere queste fasi è fondamentale per capire quando e dove le direttive vengono eseguite.

```
Connessione TCP in arrivo
         │
         ▼
┌─────────────────────────┐
│  1. POST_READ           │  Lettura degli header della richiesta
│     (realip)            │  Modulo realip risolve l'IP reale dal proxy
├─────────────────────────┤
│  2. SERVER_REWRITE      │  Riscritture nel contesto server (prima
│     (rewrite)           │  della selezione della location)
├─────────────────────────┤
│  3. FIND_CONFIG         │  Algoritmo di matching della location
│                         │  (descritto nella sezione successiva)
├─────────────────────────┤
│  4. REWRITE             │  Riscritture nel contesto location
│     (rewrite)           │
├─────────────────────────┤
│  5. POST_REWRITE        │  Redirect interno se URI è cambiato
│                         │  (torna a FIND_CONFIG)
├─────────────────────────┤
│  6. PREACCESS           │  limit_req, limit_conn
│     (rate limiting)     │
├─────────────────────────┤
│  7. ACCESS              │  auth_basic, auth_request, allow/deny
│     (autenticazione)    │
├─────────────────────────┤
│  8. POST_ACCESS         │  Combinazione dei risultati (satisfy)
│                         │
├─────────────────────────┤
│  9. PRECONTENT          │  try_files, mirror
│                         │
├─────────────────────────┤
│ 10. CONTENT             │  Generazione della risposta:
│     (proxy, fastcgi,    │  proxy_pass, fastcgi_pass, root,
│      static, etc.)      │  alias, return, etc.
├─────────────────────────┤
│ 11. LOG                 │  access_log, scrittura log
│                         │
└─────────────────────────┘
```

Ogni fase è servita da uno o più moduli. Ad esempio, `ngx_http_access_module` opera nella fase ACCESS, mentre `ngx_http_limit_req_module` opera nella fase PREACCESS. Questo spiega perché `limit_req` viene valutato *prima* di `auth_basic`: le fasi sono eseguite in ordine fisso, indipendentemente dalla posizione delle direttive nel file di configurazione.

### Event Loop e I/O Multiplexing

Nginx utilizza un modello di I/O **event-driven non bloccante** basato su meccanismi di notifica del kernel:

| Piattaforma | Meccanismo | Direttiva Nginx |
|-------------|-----------|-----------------|
| Linux 2.6+  | `epoll`   | `use epoll;`    |
| FreeBSD/macOS | `kqueue` | `use kqueue;`  |
| Solaris     | `eventport` | `use eventport;` |
| Fallback    | `select`/`poll` | `use select;` |

Il funzionamento dell'event loop in un worker process:

```
┌──────────────────────────────────────────────────┐
│                Worker Process                     │
│                                                  │
│  ┌────────────────────────────────────────────┐  │
│  │           Event Loop (epoll_wait)          │  │
│  │                                            │  │
│  │  1. Attendi eventi su tutti i file          │  │
│  │     descriptor registrati                   │  │
│  │                                            │  │
│  │  2. Evento di connessione in arrivo:       │  │
│  │     → accept() → crea oggetto connessione  │  │
│  │     → registra fd per lettura              │  │
│  │                                            │  │
│  │  3. Evento di lettura disponibile:         │  │
│  │     → read() header → parse HTTP           │  │
│  │     → determina handler (proxy/static)     │  │
│  │                                            │  │
│  │  4. Handler proxy: connetti al backend     │  │
│  │     → registra fd upstream per lettura     │  │
│  │     → NON BLOCCA: torna a epoll_wait      │  │
│  │                                            │  │
│  │  5. Risposta upstream disponibile:         │  │
│  │     → read() da upstream                   │  │
│  │     → write() al client                    │  │
│  │     → registra per prossimo evento         │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  Ogni iterazione può gestire centinaia di eventi │
│  senza mai bloccarsi su una singola connessione  │
└──────────────────────────────────────────────────┘
```

**Implicazioni pratiche:**

- Un singolo worker non si blocca mai su una connessione lenta: passa ad un'altra connessione pronta.
- Le operazioni bloccanti (accesso a disco, DNS lookup) vengono gestite da un thread pool interno (direttiva `aio threads;` da Nginx 1.7.11+).
- Il numero ideale di `worker_connections` dipende dal rapporto tra connessioni attive e inattive. Per un reverse proxy con molte connessioni keepalive: `worker_connections` × `worker_processes` ≥ connessioni simultanee attese × 2 (client + upstream).

```nginx
# Thread pool per operazioni di I/O su disco (Nginx 1.7.11+)
# Evita che letture lente da disco blocchino l'event loop
thread_pool default threads=32 max_queue=65536;

http {
    # Abilita AIO con thread pool per file statici
    aio threads=default;

    # Directio per file > 4MB (bypass del page cache)
    directio 4m;
    directio_alignment 512;
}
```

---

## Contesti di Configurazione e Ereditarietà

La configurazione di Nginx è organizzata in **contesti** annidati. Ogni direttiva è valida solo in determinati contesti, e i valori vengono ereditati dai contesti genitori a quelli figli.

### Gerarchia dei Contesti

```
main (nginx.conf — livello globale)
├── events { }              — configurazione del modello di eventi
├── http { }                — configurazione HTTP
│   ├── upstream { }        — pool di server backend
│   ├── map { }             — mappatura variabili
│   ├── server { }          — virtual host
│   │   ├── location { }    — matching URI
│   │   │   └── location { } — location annidata
│   │   └── if { }          — condizionale (da evitare)
│   └── types { }           — mapping MIME
├── mail { }                — proxy email (opzionale)
└── stream { }              — proxy TCP/UDP (Layer 4)
```

### Regole di Ereditarietà

Le direttive seguono regole di ereditarietà specifiche che variano per tipo:

**1. Direttive semplici (valore singolo)** — il figlio eredita dal genitore, ma può sovrascrivere:

```nginx
http {
    gzip on;                    # Ereditato da tutti i server/location

    server {
        # gzip è "on" qui (ereditato da http)

        location /api/ {
            gzip off;           # Sovrascrive solo per questa location
        }

        location /static/ {
            # gzip è ancora "on" qui (ereditato da server, che eredita da http)
        }
    }
}
```

**2. Direttive array (valori multipli)** — i figli NON ereditano se definiscono le proprie:

```nginx
http {
    # Header definiti a livello http
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    server {
        # ATTENZIONE: se aggiungi un header qui, gli header di http vengono PERSI
        add_header Strict-Transport-Security "max-age=63072000" always;
        # ↑ Solo HSTS. X-Frame-Options e X-Content-Type-Options NON sono ereditati.

        # Soluzione: ripeti tutti gli header necessari, oppure usa include
        include /etc/nginx/conf.d/security-headers.conf;
    }
}
```

> **Regola critica**: `add_header`, `proxy_set_header`, `proxy_hide_header` e altre direttive "array" vengono completamente sostituite quando ridefinite nel contesto figlio, non aggiunte. Questo è la fonte del 90% degli errori di configurazione Nginx legati agli header.

**3. Direttive di azione** — non ereditano, devono essere esplicite:

```nginx
server {
    location / {
        proxy_pass http://backend;   # Deve essere in ogni location che fa proxy
    }

    location /static/ {
        # proxy_pass NON è ereditato — questa location serve file statici
        root /var/www;
    }
}
```

### Contesto `main` — Direttive Globali Importanti

```nginx
# ── Contesto main (fuori da qualsiasi blocco) ────────────────

# Numero massimo di file aperti per worker
worker_rlimit_nofile 65535;

# Core dump (per debugging)
working_directory /var/crash/nginx;
worker_rlimit_core 500M;

# Priorità del processo (nice value)
worker_priority -5;

# Timer resolution — riduce le chiamate gettimeofday()
# Utile su server ad alto traffico
timer_resolution 100ms;

# Percorso per lock files
lock_file /var/lock/nginx.lock;

# Include moduli dinamici
load_module modules/ngx_http_brotli_filter_module.so;
load_module modules/ngx_http_brotli_static_module.so;
```

---

## Server Blocks e Location Matching

### Server Block Selection

Quando una richiesta arriva, Nginx seleziona il server block in questo ordine:

1. Match per `listen` IP:porta
2. Match per `server_name` (header Host)
3. Se nessun match: usa il `default_server`

```nginx
# Server block esplicito
server {
    listen 80;
    server_name example.com www.example.com;
    # ...
}

# Default server (catch-all) — restituisci 444 per richieste senza Host valido
server {
    listen 80 default_server;
    server_name _;
    return 444;  # Chiudi connessione senza risposta
}

# Virtual host con SSL
server {
    listen 443 ssl http2;
    server_name app.example.com;
    ssl_certificate /etc/ssl/certs/app.example.com.pem;
    ssl_certificate_key /etc/ssl/private/app.example.com.key;
    # ...
}
```

### Location Matching

L'algoritmo di matching delle location è uno degli aspetti più importanti e fraintesi di Nginx:

```nginx
# Ordine di priorità (dal più alto al più basso):

# 1. Match esatto (=)
location = /api/health {
    return 200 "OK";
}

# 2. Prefix match preferenziale (^~) — ferma la ricerca
location ^~ /static/ {
    root /var/www;
}

# 3. Regular expression match (~, ~*) — in ordine di definizione
location ~ \.php$ {                 # case-sensitive regex
    fastcgi_pass unix:/run/php-fpm.sock;
}

location ~* \.(jpg|jpeg|png|gif)$ { # case-insensitive regex
    expires 30d;
}

# 4. Prefix match (nessun modificatore) — il più lungo vince
location /api/ {
    proxy_pass http://backend;
}

location /api/v2/ {
    proxy_pass http://backend_v2;  # Vince per /api/v2/* (più lungo)
}

location / {
    root /var/www/html;            # Catch-all per tutto il resto
}
```

### Algoritmo di Matching Dettagliato

```
Richiesta: GET /api/v2/users

1. Controlla match esatti (=): nessuno → continua
2. Cerca tutti i prefix match:
   - / → match (lunghezza 1)
   - /api/ → match (lunghezza 5)
   - /api/v2/ → match (lunghezza 8) ← più lungo
3. Il prefix più lungo è /api/v2/ — è ^~? No → continua
4. Controlla regex nell'ordine di definizione:
   - ~ \.php$ → non matcha → continua
   - ~* \.(jpg|jpeg|png|gif)$ → non matcha → continua
5. Nessuna regex matcha → usa il prefix più lungo: /api/v2/
```

### Nested Location

```nginx
location /api/ {
    # Regole comuni per /api/
    proxy_set_header X-Real-IP $remote_addr;

    location /api/public/ {
        # Nessuna autenticazione
        proxy_pass http://backend;
    }

    location /api/admin/ {
        # Richiede autenticazione
        auth_basic "Admin Area";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://backend;
    }
}
```

### Pattern try_files

La direttiva `try_files` è uno strumento potente per controllare la risoluzione delle risorse. Viene eseguita nella fase PRECONTENT, prima del handler di contenuto.

```nginx
# Pattern 1: SPA (Single Page Application)
# Prova il file, poi la directory, poi fallback su index.html
location / {
    root /var/www/app/dist;
    try_files $uri $uri/ /index.html;
}

# Pattern 2: File statico con fallback al backend
# Prova il file statico, se non esiste inoltra al backend
location / {
    root /var/www/static;
    try_files $uri $uri/ @backend;
}

location @backend {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

# Pattern 3: Named location per errori
# Restituisci una pagina di errore personalizzata
location / {
    proxy_pass http://backend;
    proxy_intercept_errors on;
    error_page 502 503 504 = @maintenance;
}

location @maintenance {
    root /var/www/maintenance;
    try_files /maintenance.html =503;
}

# Pattern 4: Verifica esistenza con estensioni
# Utile per pretty URLs senza estensione
location / {
    root /var/www/docs;
    try_files $uri $uri.html $uri/index.html =404;
}

# Pattern 5: Multi-lingua con fallback
location / {
    root /var/www/site;
    try_files /$lang/$uri /$lang/$uri/ /en/$uri /en/$uri/ =404;
}
```

**Errore comune con try_files**: la direttiva `try_files` effettua un redirect interno per l'ultimo argomento se è un URI (non un codice di stato). Questo significa che `try_files $uri /index.html` invocherà nuovamente il matching delle location per `/index.html`, potenzialmente entrando in una location diversa.

### La Direttiva map

La direttiva `map` crea variabili il cui valore dipende da un'altra variabile. È il modo corretto di implementare logiche condizionali in Nginx, al posto della direttiva `if`.

```nginx
http {
    # Mappa per determinare se il client supporta WebP
    map $http_accept $webp_suffix {
        default   "";
        "~*webp"  ".webp";
    }

    # Mappa per rate limiting differenziato per tipo di richiesta
    map $request_method $limit_key {
        default         $binary_remote_addr;
        POST            $binary_remote_addr;
        GET             "";     # Non limitare le GET
    }

    # Mappa per redirect basati su hostname
    map $host $redirect_target {
        old.example.com     "https://new.example.com";
        legacy.example.com  "https://new.example.com";
        default             "";
    }

    # Mappa per selezionare il backend in base al cookie
    map $cookie_version $backend_pool {
        "v2"     http://backend_v2;
        default  http://backend_v1;
    }

    # Mappa per CORS — consentire solo origini specifiche
    map $http_origin $cors_origin {
        default                     "";
        "https://app.example.com"   $http_origin;
        "https://admin.example.com" $http_origin;
        ~^https://.*\.example\.com$ $http_origin;
    }

    server {
        # Uso della mappa CORS
        location /api/ {
            if ($cors_origin) {
                add_header Access-Control-Allow-Origin $cors_origin always;
                add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
                add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
            }
            proxy_pass http://backend;
        }

        # Uso della mappa redirect
        if ($redirect_target) {
            return 301 $redirect_target$request_uri;
        }
    }
}
```

---

## Reverse Proxy

### Configurazione Base

```nginx
server {
    listen 80;
    server_name app.example.com;

    location / {
        proxy_pass http://127.0.0.1:3000;

        # Header fondamentali per il reverse proxy
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;

        # Timeout
        proxy_connect_timeout 10s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;

        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
    }
}
```

### Proxy per WebSocket

```nginx
location /ws/ {
    proxy_pass http://127.0.0.1:3000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;

    # Timeout per connessioni WebSocket (più lungo)
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
}
```

### Proxy con Path Rewriting

```nginx
# /app/api/users → backend riceve /api/users (rimuove /app)
location /app/ {
    proxy_pass http://backend/;  # Il trailing slash è CRITICO
}

# /old-api/users → backend riceve /v2/users
location /old-api/ {
    rewrite ^/old-api/(.*) /v2/$1 break;
    proxy_pass http://backend;
}
```

### Attenzione al Trailing Slash

```nginx
# CON trailing slash in proxy_pass: il path della location viene sostituito
location /api/ {
    proxy_pass http://backend/v1/;
    # /api/users → http://backend/v1/users
}

# SENZA trailing slash: il path originale viene preservato
location /api/ {
    proxy_pass http://backend;
    # /api/users → http://backend/api/users
}
```

### Proxy Buffering Approfondito

Il buffering controlla come Nginx gestisce le risposte dal backend. Con il buffering attivo (default), Nginx legge l'intera risposta dal backend e la memorizza in buffer interni prima di inviarla al client. Questo libera il backend rapidamente, anche se il client è lento.

```nginx
location /api/ {
    proxy_pass http://backend;

    # ── Buffering attivo (default e raccomandato per la maggior parte dei casi) ──
    proxy_buffering on;

    # Buffer per la prima parte della risposta (header + inizio body)
    proxy_buffer_size 8k;

    # Buffer per il resto della risposta
    # numero × dimensione = memoria massima per connessione
    proxy_buffers 16 8k;

    # Dimensione massima che può essere inviata al client
    # mentre il resto della risposta è ancora in arrivo dal backend
    proxy_busy_buffers_size 16k;

    # Se la risposta supera i buffer in memoria, scrivi su disco
    proxy_max_temp_file_size 1024m;
    proxy_temp_file_write_size 16k;
    proxy_temp_path /var/cache/nginx/proxy_temp 1 2;
}

# ── Buffering disabilitato: per SSE (Server-Sent Events) ──
location /api/events {
    proxy_pass http://backend;
    proxy_buffering off;

    # Disabilita anche il buffering di chunked responses
    proxy_http_version 1.1;
    proxy_set_header Connection "";

    # Timeout lungo per streaming
    proxy_read_timeout 3600s;
}

# ── Controllo del buffering lato client (header X-Accel-Buffering) ──
# Il backend può inviare l'header "X-Accel-Buffering: no" per
# disabilitare il buffering per specifiche risposte.
# Questo è utile per SSE o streaming dove il backend decide.
location /api/stream {
    proxy_pass http://backend;
    # Il backend controlla il buffering tramite X-Accel-Buffering
    proxy_pass_header X-Accel-Buffering;
}
```

### Keepalive verso Upstream

Le connessioni keepalive verso i backend riducono drasticamente la latenza eliminando il costo di stabilire nuove connessioni TCP (e TLS se il backend è HTTPS). Senza keepalive, ogni richiesta proxy apre e chiude una connessione TCP.

```nginx
upstream backend {
    server 10.0.0.1:8000;
    server 10.0.0.2:8000;

    # Numero di connessioni keepalive inattive per worker
    # Non è un limite massimo, è il numero di connessioni da mantenere in cache
    keepalive 32;

    # Timeout per connessioni keepalive inattive
    keepalive_timeout 60s;

    # Numero massimo di richieste su una singola connessione keepalive
    # Dopo questo numero, la connessione viene chiusa e ricreata
    keepalive_requests 1000;
}

server {
    location / {
        proxy_pass http://backend;

        # OBBLIGATORIO per keepalive upstream:
        # HTTP/1.1 supporta keepalive (HTTP/1.0 no)
        proxy_http_version 1.1;

        # Rimuovi l'header Connection per evitare "Connection: close"
        proxy_set_header Connection "";

        # Il resto degli header proxy rimane invariato
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

**Dimensionamento del keepalive**: il valore di `keepalive` deve essere proporzionale al traffico medio per worker. Regola empirica: `keepalive ≈ (richieste_per_secondo / worker_processes) × latenza_media_backend_in_secondi × 2`. Per un server con 1000 req/s, 4 worker e 50ms di latenza backend: `(1000/4) × 0.05 × 2 = 25`, quindi `keepalive 32` è appropriato.

---

## Load Balancing

### Upstream e Algoritmi

```nginx
# Round Robin (default)
upstream backend {
    server 10.0.0.1:8080;
    server 10.0.0.2:8080;
    server 10.0.0.3:8080;
}

# Weighted Round Robin
upstream backend_weighted {
    server 10.0.0.1:8080 weight=5;  # riceve 5x più traffico
    server 10.0.0.2:8080 weight=3;
    server 10.0.0.3:8080 weight=1;
}

# Least Connections
upstream backend_leastconn {
    least_conn;
    server 10.0.0.1:8080;
    server 10.0.0.2:8080;
    server 10.0.0.3:8080;
}

# IP Hash (sticky session per IP)
upstream backend_iphash {
    ip_hash;
    server 10.0.0.1:8080;
    server 10.0.0.2:8080;
    server 10.0.0.3:8080;
}

# Hash generico (per header o variabile)
upstream backend_hash {
    hash $request_uri consistent;
    server 10.0.0.1:8080;
    server 10.0.0.2:8080;
}
```

### Health Check e Failover

```nginx
upstream backend {
    server 10.0.0.1:8080 max_fails=3 fail_timeout=30s;
    server 10.0.0.2:8080 max_fails=3 fail_timeout=30s;
    server 10.0.0.3:8080 backup;  # usato solo se tutti gli altri falliscono

    # Mantieni connessioni keepalive verso i backend
    keepalive 32;
}

server {
    location / {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";  # necessario per keepalive upstream

        # Retry su errori
        proxy_next_upstream error timeout http_502 http_503 http_504;
        proxy_next_upstream_timeout 10s;
        proxy_next_upstream_tries 3;
    }
}
```

### Active Health Check (Nginx Plus / alternativa con modulo)

```nginx
# Con Nginx Plus (commerciale)
upstream backend {
    zone backend 64k;
    server 10.0.0.1:8080;
    server 10.0.0.2:8080;

    health_check interval=5s fails=3 passes=2;
    health_check uri=/health match=healthy;
}

match healthy {
    status 200;
    body ~ "OK";
}

# Con Nginx open source, si usa il passive health check (max_fails)
# oppure un modulo esterno come nginx_upstream_check_module
```

### Algoritmo random e Slow Start

```nginx
# Random con two-choices (Nginx 1.15.1+)
# Seleziona 2 server casuali, poi sceglie quello con meno connessioni
# Distribuzione molto uniforme senza stato condiviso tra i worker
upstream backend_random {
    random two least_conn;
    server 10.0.0.1:8080;
    server 10.0.0.2:8080;
    server 10.0.0.3:8080;
}
```

**Confronto algoritmi di load balancing:**

| Algoritmo | Pro | Contro | Caso d'uso |
|-----------|-----|--------|------------|
| Round Robin | Semplice, nessun overhead | Ignora carico reale | Backend omogenei, richieste uniformi |
| Weighted RR | Bilancia per capacità hardware | Configurazione statica | Hardware eterogeneo |
| Least Connections | Si adatta al carico reale | Stato per worker (non globale) | Richieste con latenza variabile |
| IP Hash | Affinità sessione | Distribuzione non uniforme con pochi IP | Sessioni sticky senza cookie |
| Hash (consistent) | Distribuzione stabile, buona per cache | Ribilanciamento parziale su modifiche | Caching distribuito |
| Random Two | Scalabile, nessuno stato condiviso | Leggermente meno preciso di least_conn | Cluster molto grandi |

### Parametri Avanzati dei Server Upstream

```nginx
upstream backend {
    least_conn;

    # weight: peso relativo (default 1)
    # max_fails: tentativi falliti prima di considerare il server down
    # fail_timeout: finestra temporale per max_fails E durata della penalizzazione
    # max_conns: limite massimo di connessioni contemporanee (0 = illimitato)
    # down: segna il server come permanentemente offline
    # backup: usato solo quando tutti i server primari sono down
    # resolve: risolvi il nome DNS periodicamente (richiede resolver)

    server 10.0.0.1:8080 weight=5 max_fails=3 fail_timeout=30s max_conns=100;
    server 10.0.0.2:8080 weight=3 max_fails=3 fail_timeout=30s max_conns=100;
    server 10.0.0.3:8080 weight=1 max_fails=3 fail_timeout=30s;
    server 10.0.0.4:8080 backup;
    server 10.0.0.5:8080 down;    # Fuori rotazione per manutenzione

    # Slow start (solo Nginx Plus)
    # server 10.0.0.6:8080 slow_start=30s;
    # Il peso aumenta gradualmente da 0 al valore configurato in 30 secondi

    keepalive 32;
}
```

### Upstream con DNS Dinamico

Per ambienti container (Docker, Kubernetes) dove gli IP cambiano dinamicamente:

```nginx
http {
    # Resolver per risoluzioni DNS periodiche
    resolver 127.0.0.53 valid=30s ipv6=off;
    resolver_timeout 5s;

    upstream dynamic_backend {
        # La variabile forza Nginx a ri-risolvere il DNS ad ogni richiesta
        # (altrimenti il DNS viene risolto solo al caricamento della config)
        server backend.service.consul:8080 resolve;

        keepalive 16;
    }

    server {
        location / {
            # Alternativa senza upstream block:
            # Usare una variabile forza la ri-risoluzione DNS
            set $backend_host "backend.service.consul";
            proxy_pass http://$backend_host:8080;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
        }
    }
}
```

> **Nota**: quando `proxy_pass` contiene una variabile, Nginx non usa il resolver del sistema ma quello configurato con la direttiva `resolver`. Senza un resolver configurato, la risoluzione fallirà silenziosamente.

---

## SSL/TLS Configurazione

### Configurazione SSL Moderna

```nginx
# /etc/nginx/conf.d/ssl-params.conf — include in ogni server block SSL

ssl_protocols TLSv1.2 TLSv1.3;

# Cipher suite — TLS 1.3 negozia automaticamente, TLS 1.2 richiede configurazione
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
ssl_prefer_server_ciphers off;  # off con TLS 1.3

# Session caching
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:10m;
ssl_session_tickets off;  # Forward secrecy — non usare ticket per sessioni lunghe

# OCSP Stapling — il server include la risposta OCSP nella connessione TLS
ssl_stapling on;
ssl_stapling_verify on;
ssl_trusted_certificate /etc/ssl/certs/ca-chain.pem;
resolver 1.1.1.1 8.8.8.8 valid=300s;
resolver_timeout 5s;

# DH parameters (solo per TLS 1.2 con DHE)
ssl_dhparam /etc/ssl/dhparam.pem;
# Genera: openssl dhparam -out /etc/ssl/dhparam.pem 2048
```

### Server Block con SSL Completo

```nginx
# Redirect HTTP → HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name example.com www.example.com;
    return 301 https://example.com$request_uri;
}

# Redirect www → non-www (HTTPS)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name www.example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    include /etc/nginx/conf.d/ssl-params.conf;

    return 301 https://example.com$request_uri;
}

# Server principale
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    include /etc/nginx/conf.d/ssl-params.conf;

    # HSTS (dopo aver verificato che SSL funziona!)
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

    root /var/www/example.com;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

### Let's Encrypt con Certbot

```bash
# Installazione
apt install certbot python3-certbot-nginx

# Ottenimento certificato (modifica automaticamente nginx config)
certbot --nginx -d example.com -d www.example.com

# Solo ottenimento, senza modificare nginx
certbot certonly --webroot -w /var/www/html -d example.com

# Rinnovo automatico (certbot installa un timer systemd)
certbot renew --dry-run  # test

# Hook post-rinnovo per reload nginx
# /etc/letsencrypt/renewal-hooks/post/reload-nginx.sh
#!/bin/bash
systemctl reload nginx
```

### Catena di Certificati

Il certificato SSL presentato al client deve includere l'intera catena di fiducia, dal certificato del server fino alla CA intermedia. La CA root non va inclusa poiché il client la possiede già nel proprio trust store.

```
Ordine corretto nel file fullchain.pem:
┌────────────────────────────┐
│  Certificato del server    │  ← Il tuo certificato
├────────────────────────────┤
│  CA Intermedia 1           │  ← Firmata dalla Root CA
├────────────────────────────┤
│  CA Intermedia 2           │  ← (se presente)
└────────────────────────────┘
   ↑ NON includere la Root CA
```

```bash
# Verifica la catena di certificati
openssl verify -CAfile /etc/ssl/certs/ca-certificates.crt \
    -untrusted /etc/ssl/certs/intermediate.pem \
    /etc/ssl/certs/server.pem

# Visualizza i certificati nella catena
openssl crl2pkcs7 -nocrl -certfile fullchain.pem | \
    openssl pkcs7 -print_certs -noout

# Verifica che la chiave corrisponda al certificato
openssl x509 -noout -modulus -in server.pem | openssl md5
openssl rsa -noout -modulus -in server.key | openssl md5
# I due hash MD5 devono essere identici
```

```nginx
# Configurazione con catena esplicita
server {
    # fullchain.pem = server cert + intermediate(s)
    ssl_certificate     /etc/ssl/certs/fullchain.pem;
    ssl_certificate_key /etc/ssl/private/server.key;

    # Per OCSP stapling, serve il file con le CA intermedie
    ssl_trusted_certificate /etc/ssl/certs/chain.pem;
}
```

### Selezione delle Cipher Suite

La scelta delle cipher suite bilancia sicurezza e compatibilità. Con TLS 1.3 (RFC 8446), le cipher suite sono fisse e non necessitano di configurazione manuale. Per TLS 1.2 rimane necessaria una selezione esplicita.

```nginx
# ── Profilo MODERNO: solo TLS 1.3 ──
# Compatibilità: browser aggiornati dal 2019+
ssl_protocols TLSv1.3;
# TLS 1.3 usa automaticamente:
#   TLS_AES_256_GCM_SHA384
#   TLS_AES_128_GCM_SHA256
#   TLS_CHACHA20_POLY1305_SHA256

# ── Profilo INTERMEDIO (raccomandato): TLS 1.2 + 1.3 ──
# Compatibilità: tutti i browser moderni
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;

# Con TLS 1.3 presente, lasciare al client la scelta
# (i client moderni preferiscono ChaCha20 su mobile per efficienza)
ssl_prefer_server_ciphers off;

# Curve ellittiche da negoziare
ssl_ecdh_curves X25519:prime256v1:secp384r1;
```

Fonte: Mozilla SSL Configuration Generator (https://ssl-config.mozilla.org/), consultato il 2026-05-23.

### mTLS — Autenticazione Client con Certificato

L'autenticazione mTLS (Mutual TLS) richiede che anche il client presenti un certificato valido, non solo il server. È utilizzata per comunicazioni machine-to-machine, API interne e zero-trust architectures.

```nginx
server {
    listen 443 ssl;
    server_name api-internal.example.com;

    # Certificato del server (come sempre)
    ssl_certificate     /etc/ssl/certs/server.pem;
    ssl_certificate_key /etc/ssl/private/server.key;

    # ── mTLS: certificato client ──
    # CA che ha firmato i certificati client
    ssl_client_certificate /etc/ssl/certs/client-ca.pem;

    # Richiedi il certificato client
    # on         = obbligatorio, rifiuta se mancante
    # optional   = richiesto ma non obbligatorio (verifica in location)
    # optional_no_ca = accetta qualsiasi certificato (utile per debug)
    ssl_verify_client on;

    # Profondità massima della catena di verifica
    ssl_verify_depth 2;

    # CRL (Certificate Revocation List) per revocare certificati compromessi
    ssl_crl /etc/ssl/certs/client-revoked.crl;

    location / {
        # Variabili disponibili dopo la verifica del client
        # $ssl_client_s_dn       — Subject DN del certificato
        # $ssl_client_i_dn       — Issuer DN
        # $ssl_client_serial     — Numero seriale
        # $ssl_client_fingerprint — Fingerprint SHA1
        # $ssl_client_verify     — "SUCCESS", "FAILED:reason", "NONE"
        # $ssl_client_v_start    — Data inizio validità
        # $ssl_client_v_end      — Data fine validità

        # Inoltra le informazioni del certificato client al backend
        proxy_set_header X-Client-DN     $ssl_client_s_dn;
        proxy_set_header X-Client-Verify $ssl_client_verify;
        proxy_set_header X-Client-Serial $ssl_client_serial;

        proxy_pass http://internal_backend;
    }
}

# Con ssl_verify_client optional — verifica per location
server {
    listen 443 ssl;
    server_name mixed.example.com;

    ssl_client_certificate /etc/ssl/certs/client-ca.pem;
    ssl_verify_client optional;

    # Endpoint pubblico — non richiede certificato client
    location /public/ {
        proxy_pass http://backend;
    }

    # Endpoint protetto — richiede certificato valido
    location /internal/ {
        if ($ssl_client_verify != SUCCESS) {
            return 403;
        }
        proxy_pass http://internal_backend;
    }
}
```

```bash
# Generazione CA per certificati client
# 1. Crea la CA
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 \
    -days 3650 -nodes -keyout client-ca.key -out client-ca.pem \
    -subj "/CN=Internal Client CA/O=Example Corp"

# 2. Genera chiave e CSR per il client
openssl req -newkey ec -pkeyopt ec_paramgen_curve:prime256v1 \
    -nodes -keyout client.key -out client.csr \
    -subj "/CN=service-a/O=Example Corp"

# 3. Firma il certificato client con la CA
openssl x509 -req -in client.csr -CA client-ca.pem -CAkey client-ca.key \
    -CAcreateserial -out client.pem -days 365

# 4. Test della connessione mTLS
curl --cert client.pem --key client.key \
     --cacert server-ca.pem \
     https://api-internal.example.com/health
```

### Session Tickets vs Session Cache

La ripresa delle sessioni TLS evita una full handshake ad ogni connessione, riducendo la latenza. Esistono due meccanismi, con trade-off diversi:

| Aspetto | Session Cache | Session Tickets |
|---------|---------------|-----------------|
| Meccanismo | Server mantiene una cache delle sessioni | Server cifra lo stato e lo invia al client |
| Forward Secrecy | Sì (la sessione scade dalla cache) | Rischio se la chiave del ticket non viene ruotata |
| Memoria server | Richiede memoria condivisa | Nessuna memoria lato server |
| Multi-server | Difficile (cache non condivisa) | Facile (stessa chiave su tutti i server) |
| RFC | RFC 5246 §7.4.1.1 | RFC 5077, aggiornato in RFC 8446 §2.2 |

```nginx
# ── Opzione 1: Solo Session Cache (più sicuro per forward secrecy) ──
ssl_session_cache shared:SSL:50m;   # ~200.000 sessioni
ssl_session_timeout 1d;
ssl_session_tickets off;            # Disabilitato per forward secrecy

# ── Opzione 2: Session Tickets con rotazione delle chiavi ──
# Richiede la rotazione periodica dei file ticket key
ssl_session_tickets on;
ssl_session_ticket_key /etc/ssl/private/ticket-current.key;
ssl_session_ticket_key /etc/ssl/private/ticket-previous.key;

# Genera e ruota le chiavi:
# openssl rand 80 > /etc/ssl/private/ticket-current.key
# Ogni 12 ore: rinomina current → previous, genera nuovo current
# Il file deve essere esattamente 80 byte (48 per AES-256-CBC + 32 per HMAC-SHA256)
```

### HSTS Preloading — Procedura Completa

La direttiva HSTS (HTTP Strict Transport Security, RFC 6797) istruisce il browser a usare solo HTTPS per il dominio. Il preloading incorpora il dominio direttamente nei browser.

```nginx
# Passo 1: Attiva HSTS con max-age breve (per test)
add_header Strict-Transport-Security "max-age=300" always;

# Passo 2: Dopo aver verificato che tutto funziona, aumenta max-age
add_header Strict-Transport-Security "max-age=63072000" always;

# Passo 3: Aggiungi includeSubDomains (ATTENZIONE: TUTTI i sottodomini
# devono supportare HTTPS, altrimenti saranno inaccessibili)
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;

# Passo 4: Aggiungi preload e sottometti a hstspreload.org
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
```

> **Avvertenza**: la rimozione da HSTS preload list richiede mesi. Assicurarsi che TUTTI i sottodomini (inclusi quelli interni, staging, etc.) supportino HTTPS prima di aggiungere `includeSubDomains`. Riferimento: RFC 6797, consultato il 2026-05-23.

---

## Caching

### Proxy Cache

```nginx
http {
    # Definizione della cache
    proxy_cache_path /var/cache/nginx/proxy
        levels=1:2              # struttura directory (1 carattere, 2 caratteri)
        keys_zone=proxy_cache:10m  # nome e dimensione della zona chiavi in RAM
        max_size=10g            # dimensione massima su disco
        inactive=60m            # rimuovi dopo 60 min senza accessi
        use_temp_path=off;      # scrivi direttamente nella cache

    server {
        location / {
            proxy_pass http://backend;

            # Abilita caching
            proxy_cache proxy_cache;
            proxy_cache_valid 200 302 10m;   # cache 200/302 per 10 minuti
            proxy_cache_valid 404 1m;         # cache 404 per 1 minuto
            proxy_cache_use_stale error timeout updating http_502 http_503;
            proxy_cache_lock on;              # serializza richieste per la stessa chiave
            proxy_cache_lock_timeout 5s;
            proxy_cache_revalidate on;        # usa If-Modified-Since

            # Cache key
            proxy_cache_key $scheme$request_method$host$request_uri;

            # Header informativi
            add_header X-Cache-Status $upstream_cache_status;

            # Bypass cache per richieste autenticate
            proxy_cache_bypass $http_authorization;
            proxy_no_cache $http_authorization;
        }

        # Bypass cache per admin
        location /admin/ {
            proxy_pass http://backend;
            proxy_cache off;
        }
    }
}
```

### Static File Caching

```nginx
location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg|woff2|woff|ttf)$ {
    root /var/www/html;

    # Browser cache
    expires 30d;
    add_header Cache-Control "public, immutable";

    # Disabilita access log per file statici
    access_log off;

    # Open file cache per performance
    open_file_cache max=1000 inactive=20s;
    open_file_cache_valid 30s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;
}
```

### Microcaching per Contenuti Dinamici

Il microcaching memorizza risposte dinamiche per un periodo molto breve (1-5 secondi). Per un sito con 1000 req/s alla stessa pagina, il microcaching riduce le richieste al backend a 1 ogni 1-5 secondi, offrendo un rapporto cache-hit del 99.9%+ senza servire contenuti stantii.

```nginx
http {
    # Zona di microcache
    proxy_cache_path /var/cache/nginx/microcache
        levels=1:2
        keys_zone=microcache:10m
        max_size=1g
        inactive=10m
        use_temp_path=off;

    server {
        location / {
            proxy_pass http://backend;

            # Microcaching: 1 secondo
            proxy_cache microcache;
            proxy_cache_valid 200 1s;
            proxy_cache_valid 301 302 10s;
            proxy_cache_valid 404 5s;

            # Usa stale mentre si aggiorna (evita thundering herd)
            proxy_cache_use_stale updating error timeout;
            proxy_cache_background_update on;
            proxy_cache_lock on;

            # Non cachare richieste con cookie di sessione
            proxy_cache_bypass $cookie_sessionid;
            proxy_no_cache $cookie_sessionid;

            # Header diagnostico
            add_header X-Cache-Status $upstream_cache_status always;
        }
    }
}
```

**Valori di `$upstream_cache_status`:**

| Valore | Significato |
|--------|------------|
| `MISS` | Risposta non in cache, ottenuta dal backend |
| `HIT` | Risposta servita dalla cache |
| `EXPIRED` | Cache scaduta, nuova risposta ottenuta dal backend |
| `STALE` | Cache scaduta, servita perché il backend non è disponibile |
| `UPDATING` | Cache scaduta, servita mentre l'aggiornamento è in corso |
| `REVALIDATED` | Cache scaduta, rivalidata con If-Modified-Since (304) |
| `BYPASS` | Risposta dal backend per proxy_cache_bypass |

### Cache Purging

L'invalidazione della cache è necessaria quando il contenuto viene aggiornato e non si vuole attendere la scadenza naturale.

```nginx
# Metodo 1: Purge con modulo ngx_cache_purge (modulo di terze parti)
# Installazione: compilare Nginx con --add-module=ngx_cache_purge
location ~ /purge(/.*) {
    # Limita l'accesso al purge
    allow 127.0.0.1;
    allow 10.0.0.0/8;
    deny all;

    proxy_cache_purge proxy_cache $scheme$request_method$host$1;
}

# Uso: curl -X PURGE https://example.com/purge/page-to-invalidate

# Metodo 2: Purge manuale (senza moduli aggiuntivi)
# Cancella i file dalla directory della cache
# La chiave di cache determina il percorso del file
```

```bash
# Purge manuale della cache: script per invalidare una URL specifica
#!/bin/bash
CACHE_DIR="/var/cache/nginx/proxy"
URL_KEY="$1"

# Calcola l'hash MD5 della cache key
HASH=$(echo -n "${URL_KEY}" | md5sum | awk '{print $1}')

# Struttura levels=1:2 → ultimo carattere / ultimi 2 caratteri
LEVEL1="${HASH: -1}"
LEVEL2="${HASH: -3:2}"

FILE="${CACHE_DIR}/${LEVEL1}/${LEVEL2}/${HASH}"

if [ -f "$FILE" ]; then
    rm -f "$FILE"
    echo "Cache invalidata: $FILE"
else
    echo "File non trovato in cache: $FILE"
fi

# Uso: ./purge-cache.sh "GEThttps://example.com/page"
```

---

## Rate Limiting

### Configurazione Rate Limit

```nginx
http {
    # Definisci zone di rate limiting
    # $binary_remote_addr è più efficiente di $remote_addr (meno memoria)

    # 10 richieste al secondo per IP
    limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;

    # 1 richiesta al secondo per IP per login
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    # Rate limit per server_name (protezione per virtual host)
    limit_req_zone $server_name zone=per_server:10m rate=100r/s;

    # Status code per rate limit exceeded
    limit_req_status 429;

    server {
        # Rate limit generale con burst
        location / {
            limit_req zone=general burst=20 nodelay;
            # burst=20: accetta fino a 20 richieste sopra il rate
            # nodelay: non mette in coda, processa immediatamente

            proxy_pass http://backend;
        }

        # Rate limit stringente per login
        location /api/login {
            limit_req zone=login burst=5;
            # Senza nodelay: le richieste in eccesso vengono ritardate

            proxy_pass http://backend;
        }

        # Rate limit per connessioni simultanee
        limit_conn_zone $binary_remote_addr zone=addr:10m;

        location /download/ {
            limit_conn addr 5;          # max 5 connessioni simultanee per IP
            limit_rate 1m;              # 1 MB/s per connessione
            limit_rate_after 10m;       # rate limit dopo i primi 10 MB
        }
    }
}
```

### Strategie Avanzate di Rate Limiting

#### Rate Limiting per URI

```nginx
http {
    # Zona combinata IP + URI
    limit_req_zone $binary_remote_addr$request_uri zone=per_uri:20m rate=5r/s;

    # Zona per endpoint API specifici
    map $request_uri $api_zone_key {
        ~^/api/search    $binary_remote_addr;
        ~^/api/export    $binary_remote_addr;
        default          "";
    }
    limit_req_zone $api_zone_key zone=api_expensive:10m rate=2r/s;

    server {
        # Endpoint costosi con rate limit specifico
        location /api/search {
            limit_req zone=api_expensive burst=5 nodelay;
            proxy_pass http://backend;
        }

        location /api/export {
            limit_req zone=api_expensive burst=2;
            proxy_pass http://backend;
        }
    }
}
```

#### Whitelist e Rate Limiting Differenziato

```nginx
http {
    # Geo block per identificare IP affidabili
    geo $limit_whitelist {
        default         1;
        10.0.0.0/8      0;   # Rete interna — nessun limite
        192.168.0.0/16  0;   # Rete locale — nessun limite
        203.0.113.50    0;   # IP del monitoring — nessun limite
    }

    # Se whitelisted, la chiave è "" (vuota) → non viene limitato
    map $limit_whitelist $limit_key {
        0  "";
        1  $binary_remote_addr;
    }

    limit_req_zone $limit_key zone=api:10m rate=10r/s;

    server {
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://backend;
        }
    }
}
```

#### Combinare Rate Limiting e Connection Limiting

```nginx
http {
    # Rate limit: richieste per secondo
    limit_req_zone $binary_remote_addr zone=req_limit:10m rate=30r/s;

    # Connection limit: connessioni simultanee
    limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

    # Risposta personalizzata per rate limit
    limit_req_status 429;
    limit_conn_status 429;

    server {
        # Applicazione contemporanea di entrambi i limiti
        location /api/ {
            limit_req zone=req_limit burst=50 nodelay;
            limit_conn conn_limit 20;

            # Logging del rate limiting
            limit_req_log_level warn;
            limit_conn_log_level warn;

            # Header per comunicare i limiti al client
            add_header X-RateLimit-Limit "30" always;
            add_header Retry-After "1" always;

            proxy_pass http://backend;
        }
    }
}
```

> **burst e nodelay**: `burst=20 nodelay` accetta immediatamente fino a 20 richieste in eccesso, ma le scala dal token bucket. Senza `nodelay`, le richieste in eccesso vengono ritardate (messe in coda) per rispettare il rate dichiarato. Il delay offre un'esperienza più graduale; il nodelay offre risposte immediate ma con un taglio più brusco una volta esaurito il burst. Da Nginx 1.15.7 esiste anche `delay=N` per un approccio ibrido: le prime N richieste sopra il rate vengono servite immediatamente, le successive ritardate.

---

## Security Headers

```nginx
# /etc/nginx/conf.d/security-headers.conf
# Include in ogni server block

# HSTS — forza HTTPS per 2 anni
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

# Content Security Policy
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'nonce-$request_id'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'" always;

# Previeni MIME type sniffing
add_header X-Content-Type-Options "nosniff" always;

# Previeni clickjacking
add_header X-Frame-Options "DENY" always;

# XSS protection (legacy, CSP è superiore)
add_header X-XSS-Protection "1; mode=block" always;

# Referrer Policy
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Permissions Policy
add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()" always;

# DNS Prefetch
add_header X-DNS-Prefetch-Control "on" always;
```

### Content Security Policy Approfondita

La CSP (Content Security Policy) è la difesa primaria contro XSS (Cross-Site Scripting). Definisce da quali origini il browser può caricare risorse. Riferimento: OWASP CSP Cheat Sheet (https://cheatsheetseries.owasp.org/), consultato il 2026-05-23.

```nginx
# ── CSP Strict con nonce (raccomandato) ──
# Il nonce deve essere generato lato server per ogni risposta.
# In Nginx, $request_id è un valore pseudo-random per richiesta.

# Mappa per generare il nonce
map $request_id $csp_nonce {
    default $request_id;
}

server {
    # CSP di base per un'applicazione web
    add_header Content-Security-Policy "
        default-src 'self';
        script-src 'self' 'nonce-$csp_nonce' 'strict-dynamic';
        style-src 'self' 'unsafe-inline' https://fonts.googleapis.com;
        img-src 'self' data: https:;
        font-src 'self' https://fonts.gstatic.com;
        connect-src 'self' https://api.example.com wss://ws.example.com;
        media-src 'self';
        object-src 'none';
        frame-src 'none';
        frame-ancestors 'none';
        base-uri 'self';
        form-action 'self';
        upgrade-insecure-requests;
    " always;

    # Il nonce viene passato al backend per l'inserimento nei tag <script>
    proxy_set_header X-CSP-Nonce $csp_nonce;
}

# ── CSP Report-Only (per test prima della messa in produzione) ──
server {
    add_header Content-Security-Policy-Report-Only "
        default-src 'self';
        script-src 'self';
        report-uri /csp-report;
        report-to csp-endpoint;
    " always;

    # Endpoint per raccogliere le violazioni CSP
    location /csp-report {
        proxy_pass http://logging_backend;
        # Limite dimensione dei report
        client_max_body_size 10k;
        # Rate limit per evitare flood di report
        limit_req zone=general burst=5;
    }
}
```

**Direttive CSP chiave:**

| Direttiva | Cosa controlla |
|-----------|---------------|
| `default-src` | Fallback per tutte le direttive non specificate |
| `script-src` | Sorgenti JavaScript |
| `style-src` | Sorgenti CSS |
| `img-src` | Sorgenti immagini |
| `connect-src` | Destinazioni per XHR, fetch, WebSocket |
| `frame-src` | Sorgenti per `<iframe>` |
| `frame-ancestors` | Chi può incorporare questa pagina in iframe |
| `form-action` | Destinazioni per `<form action>` |
| `base-uri` | Limita i valori per `<base>` |
| `object-src` | Sorgenti per `<object>`, `<embed>`, `<applet>` |
| `upgrade-insecure-requests` | Converte automaticamente HTTP → HTTPS |

### Permissions-Policy Dettagliata

La Permissions-Policy (ex Feature-Policy) controlla quali API del browser possono essere usate dalla pagina e dai suoi iframe.

```nginx
# Permissions-Policy granulare
add_header Permissions-Policy "
    camera=(),
    microphone=(),
    geolocation=(),
    payment=(),
    usb=(),
    bluetooth=(),
    midi=(),
    magnetometer=(),
    gyroscope=(),
    accelerometer=(),
    autoplay=(self),
    fullscreen=(self),
    picture-in-picture=(self),
    display-capture=(),
    serial=(),
    xr-spatial-tracking=()
" always;
```

### Cross-Origin Headers Moderni

```nginx
# Cross-Origin Embedder Policy — isola la pagina da risorse cross-origin
add_header Cross-Origin-Embedder-Policy "require-corp" always;

# Cross-Origin Opener Policy — isola il browsing context
add_header Cross-Origin-Opener-Policy "same-origin" always;

# Cross-Origin Resource Policy — controlla chi può leggere le risorse
add_header Cross-Origin-Resource-Policy "same-origin" always;

# Nota: COEP + COOP abilitano SharedArrayBuffer e performance.measureUserAgentSpecificMemory()
# Necessari per alcune funzionalità web avanzate, ma possono rompere integrazioni di terze parti
```

### Configurazione CORS Avanzata

```nginx
# CORS (Cross-Origin Resource Sharing) e` essenziale per API
# consumate da frontend su domini diversi. La configurazione deve
# essere precisa: CORS troppo permissivo e` una vulnerabilita`,
# CORS troppo restrittivo rompe il frontend.

# Mappa per validare origini consentite (whitelist esplicita)
map $http_origin $cors_origin {
    default "";
    "https://app.example.com"    $http_origin;
    "https://staging.example.com" $http_origin;
    "https://admin.example.com"  $http_origin;
    # Pattern con regex (usare con cautela):
    # "~^https://.*\.example\.com$" $http_origin;
}

# Mappa per le credenziali (solo se origin e` valido)
map $cors_origin $cors_credentials {
    default "";
    "~.+" "true";
}

server {
    listen 443 ssl;
    server_name api.example.com;

    location /api/ {
        # Gestire preflight (OPTIONS) separatamente
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin $cors_origin always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, PATCH" always;
            add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-Request-ID" always;
            add_header Access-Control-Allow-Credentials $cors_credentials always;
            add_header Access-Control-Max-Age 86400 always;
            add_header Content-Type "text/plain; charset=utf-8";
            add_header Content-Length 0;
            return 204;
        }

        # Header CORS sulle risposte normali
        add_header Access-Control-Allow-Origin $cors_origin always;
        add_header Access-Control-Allow-Credentials $cors_credentials always;
        add_header Access-Control-Expose-Headers "X-Request-ID, X-RateLimit-Remaining" always;

        proxy_pass http://api_backend;
    }
}

# ANTI-PATTERN: Access-Control-Allow-Origin: *
# → Non usare MAI con credenziali
# → Consente a qualsiasi sito di fare richieste alla tua API
# → Accettabile SOLO per API pubbliche senza auth (CDN, risorse statiche)
```

### Request Filtering e Bot Protection

```nginx
# Bloccare user-agent malevoli conosciuti
map $http_user_agent $blocked_agent {
    default 0;
    "~*(?:Scrapy|Nutch|AhrefsBot|SemrushBot|MJ12bot)" 1;
    "~*(?:sqlmap|nikto|masscan|nmap)" 1;
    ""  1;   # User-agent vuoto = quasi sempre bot/scanner
}

# Bloccare metodi HTTP non necessari
map $request_method $bad_method {
    default 0;
    "TRACE"   1;
    "CONNECT" 1;
    "DELETE"  1;   # Rimuovere se l'API usa DELETE
}

server {
    # Applicare i filtri
    if ($blocked_agent) {
        return 403;
    }

    if ($bad_method) {
        return 405;
    }

    # Limitare dimensione del body (difesa contro DoS via upload)
    client_max_body_size 10m;

    # Limitare dimensione header (difesa contro header injection)
    large_client_header_buffers 4 8k;

    # Bloccare path traversal
    location ~ /\.\./ {
        deny all;
    }

    # Bloccare file nascosti (tranne .well-known per Let's Encrypt)
    location ~ /\.(?!well-known) {
        deny all;
    }

    # Bloccare estensioni pericolose
    location ~* \.(bak|config|sql|fla|psd|ini|log|sh|inc|swp|dist)$ {
        deny all;
    }
}
```

---

## HTTP/2 e HTTP/3

### HTTP/2

```nginx
server {
    # HTTP/2 richiede SSL
    listen 443 ssl http2;
    listen [::]:443 ssl http2;

    # HTTP/2 push (deprecato nella maggior parte dei browser)
    # location / {
    #     http2_push /css/style.css;
    #     http2_push /js/app.js;
    # }
}

# Tuning HTTP/2
http2_max_concurrent_streams 128;
http2_recv_timeout 30s;
```

### HTTP/3 (QUIC)

```nginx
# Richiede Nginx 1.25+ con supporto QUIC

server {
    listen 443 ssl;
    listen 443 quic reuseport;
    listen [::]:443 ssl;
    listen [::]:443 quic reuseport;

    http2 on;
    http3 on;

    # Alt-Svc header per comunicare disponibilità HTTP/3
    add_header Alt-Svc 'h3=":443"; ma=86400';

    ssl_certificate /etc/ssl/certs/example.com.pem;
    ssl_certificate_key /etc/ssl/private/example.com.key;

    # TLS 1.3 richiesto per QUIC
    ssl_protocols TLSv1.2 TLSv1.3;

    # Early data (0-RTT) per HTTP/3
    ssl_early_data on;
    proxy_set_header Early-Data $ssl_early_data;
}
```

### HTTP/2 — Dettagli e Configurazione Avanzata

HTTP/2 (RFC 7540, consultato il 2026-05-23) introduce multiplexing delle richieste su una singola connessione TCP, compressione degli header (HPACK) e prioritizzazione dei flussi.

```nginx
server {
    # Da Nginx 1.25.1, la direttiva http2 è separata da listen
    listen 443 ssl;
    http2 on;

    # ── Tuning HTTP/2 ──
    # Numero massimo di stream concorrenti per connessione
    http2_max_concurrent_streams 128;

    # Dimensione massima delle richieste HTTP/2
    http2_max_field_size 4k;
    http2_max_header_size 16k;

    # Dimensione del chunk per il body
    http2_chunk_size 8k;

    # Timeout per connessioni HTTP/2 inattive
    http2_idle_timeout 300s;
}
```

**Server Push HTTP/2 — Deprecato**: il server push HTTP/2 (`http2_push`) è stato rimosso da Nginx 1.25.1 e deprecato dai principali browser (Chrome 106+, Firefox). I browser moderni utilizzano `103 Early Hints` come alternativa più efficiente:

```nginx
server {
    listen 443 ssl;
    http2 on;

    location / {
        # 103 Early Hints — alternativa moderna a server push
        # Il server invia un header Link prima della risposta completa
        add_header Link "</css/style.css>; rel=preload; as=style" always;
        add_header Link "</js/app.js>; rel=preload; as=script" always;

        proxy_pass http://backend;
    }
}
```

### QUIC: Requisiti Infrastrutturali

HTTP/3 (RFC 9114, consultato il 2026-05-23) utilizza QUIC (RFC 9000) al posto di TCP, basato su UDP. Questo richiede configurazioni infrastrutturali specifiche.

**Requisiti:**
1. Nginx 1.25+ compilato con `--with-http_v3_module` (o il pacchetto `nginx-quic`)
2. Libreria TLS con supporto QUIC: BoringSSL (raccomandato) o quictls (fork OpenSSL)
3. Porte UDP 443 aperte sul firewall
4. Kernel Linux 5.7+ per ottimizzazione GSO (Generic Segmentation Offload)

```bash
# Verifica che Nginx sia compilato con supporto QUIC
nginx -V 2>&1 | grep -i quic

# Firewall: apri UDP 443 (iptables)
iptables -A INPUT -p udp --dport 443 -j ACCEPT
ip6tables -A INPUT -p udp --dport 443 -j ACCEPT

# Firewall: apri UDP 443 (nftables)
nft add rule inet filter input udp dport 443 accept

# Ottimizzazione kernel per QUIC
# Buffer UDP più grandi
sysctl -w net.core.rmem_max=2500000
sysctl -w net.core.wmem_max=2500000
```

```nginx
# Configurazione HTTP/3 completa con fallback
server {
    # HTTP/1.1 e HTTP/2 su TCP
    listen 443 ssl;
    listen [::]:443 ssl;

    # HTTP/3 su QUIC/UDP
    # reuseport: solo sul primo server block che ascolta sulla porta
    listen 443 quic reuseport;
    listen [::]:443 quic reuseport;

    http2 on;
    http3 on;

    # Comunica ai client che HTTP/3 è disponibile
    # ma=86400 → il client può ricordare per 24 ore
    add_header Alt-Svc 'h3=":443"; ma=86400' always;

    # TLS 1.3 obbligatorio per QUIC
    ssl_protocols TLSv1.3;

    # ── 0-RTT (Early Data) ──
    # Permette al client di inviare dati nella prima richiesta
    # senza attendere il completamento dell'handshake
    ssl_early_data on;

    # IMPORTANTE: 0-RTT è vulnerabile a replay attack
    # Inoltra al backend per decidere se accettare
    proxy_set_header Early-Data $ssl_early_data;

    # Il backend DEVE rifiutare richieste Early-Data per
    # operazioni non idempotenti (POST, PUT, DELETE)
    # Valore: "1" se la richiesta arriva via 0-RTT, "" altrimenti

    # QUIC connection migration
    quic_gso on;           # Generic Segmentation Offload (Linux 5.7+)
    quic_retry on;         # Richiedi token di validazione
                           # (protezione contro amplification attack)
}
```

**ALPN (Application-Layer Protocol Negotiation)**: durante la handshake TLS, client e server negoziano il protocollo applicativo da utilizzare. Nginx gestisce ALPN automaticamente, ma è possibile verificare la negoziazione:

```bash
# Verifica ALPN supportati dal server
openssl s_client -connect example.com:443 -alpn h2,http/1.1 2>/dev/null | \
    grep "ALPN"

# Test HTTP/3 con curl
curl --http3-only -I https://example.com
# oppure con fallback
curl --http3 -I https://example.com
```

---

## Logging e Monitoring

### Syslog Remoto e Log Aggregation

```nginx
# Nginx puo` inviare i log direttamente a un syslog server remoto,
# eliminando la necessita` di agent sul server Nginx stesso.

# Inviare access log a syslog UDP
access_log syslog:server=10.0.1.50:514,facility=local7,tag=nginx,severity=info
    json_combined;

# Inviare error log a syslog TCP (piu` affidabile)
error_log syslog:server=10.0.1.50:1514,facility=local7,tag=nginx_err warn;

# Logging multiplo: file locale + syslog remoto
# (utile per avere log locali per debug rapido e log remoti per SIEM)
access_log /var/log/nginx/access.json json_combined if=$loggable;
access_log syslog:server=10.0.1.50:514,tag=nginx json_combined if=$loggable;

# Per ambienti con Loki (Grafana stack), usare Promtail
# che legge i file di log JSON e li invia a Loki.
# Configurazione Promtail minimale:
# scrape_configs:
#   - job_name: nginx
#     static_configs:
#       - targets: [localhost]
#         labels:
#           job: nginx
#           host: web01
#           __path__: /var/log/nginx/access.json
#     pipeline_stages:
#       - json:
#           expressions:
#             status: status
#             method: request_method
#             uri: request_uri
#       - labels:
#           status:
#           method:
```

### Log Personalizzati

```nginx
http {
    # Formato JSON per integrazione con ELK/Loki
    log_format json_combined escape=json
        '{'
            '"time":"$time_iso8601",'
            '"remote_addr":"$remote_addr",'
            '"request_method":"$request_method",'
            '"request_uri":"$request_uri",'
            '"status":$status,'
            '"body_bytes_sent":$body_bytes_sent,'
            '"request_time":$request_time,'
            '"upstream_response_time":"$upstream_response_time",'
            '"upstream_addr":"$upstream_addr",'
            '"http_referer":"$http_referer",'
            '"http_user_agent":"$http_user_agent",'
            '"http_x_forwarded_for":"$http_x_forwarded_for",'
            '"cache_status":"$upstream_cache_status"'
        '}';

    # Logging condizionale (escludi health check)
    map $request_uri $loggable {
        ~*^/health 0;
        ~*^/metrics 0;
        default 1;
    }

    access_log /var/log/nginx/access.json json_combined if=$loggable;
}
```

### Stub Status per Monitoring

```nginx
server {
    listen 127.0.0.1:8080;

    location /nginx_status {
        stub_status;
        allow 127.0.0.1;
        deny all;
    }
}

# Output:
# Active connections: 291
# server accepts handled requests
#  16630948 16630948 31070465
# Reading: 6 Writing: 179 Waiting: 106
```

### Log Rotation e Syslog

#### Configurazione logrotate

```
# /etc/logrotate.d/nginx
/var/log/nginx/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        # Invia USR1 a Nginx per riaprire i file di log
        # SENZA interrompere le connessioni attive
        if [ -f /run/nginx.pid ]; then
            kill -USR1 $(cat /run/nginx.pid)
        fi
    endscript
}
```

> **Perché USR1 e non HUP**: il segnale `USR1` riapre solo i file di log, senza ricaricare la configurazione. `HUP` (usato da `systemctl reload`) ricarica l'intera configurazione e riapre i log. Per la sola rotazione dei log, `USR1` è più leggero e sicuro.

#### Invio Log a Syslog

```nginx
http {
    # Invio log a syslog remoto (RFC 5424)
    access_log syslog:server=10.0.0.100:514,facility=local7,tag=nginx,severity=info
               json_combined;

    error_log syslog:server=10.0.0.100:514,facility=local7,tag=nginx_error
              warn;

    # Invio a Unix socket (per rsyslog/journald locale)
    access_log syslog:server=unix:/var/run/syslog,nohostname json_combined;

    # Doppio output: file locale + syslog remoto
    access_log /var/log/nginx/access.log combined;
    access_log syslog:server=log-collector.internal:514,tag=nginx json_combined;
}
```

#### Log per Location

```nginx
server {
    # Log generale del server
    access_log /var/log/nginx/app-access.log json_combined;
    error_log /var/log/nginx/app-error.log warn;

    location /api/ {
        # Log dedicato per le API
        access_log /var/log/nginx/api-access.log json_combined;
        proxy_pass http://backend;
    }

    location /static/ {
        # Nessun log per file statici (riduce I/O)
        access_log off;
        root /var/www;
    }

    location /health {
        # Health check — nessun log
        access_log off;
        return 200 "OK";
    }
}
```

#### Log Format Avanzati

```nginx
http {
    # Formato con informazioni SSL/TLS
    log_format tls_info '$remote_addr - [$time_local] '
                        '"$request" $status '
                        'SSL: $ssl_protocol/$ssl_cipher '
                        'ALPN: $ssl_alpn_protocol '
                        'SNI: $ssl_server_name';

    # Formato con informazioni di latenza dettagliate
    log_format latency '$remote_addr [$time_local] '
                       '"$request" $status '
                       'req_time=$request_time '
                       'upstream_time=$upstream_response_time '
                       'upstream_connect=$upstream_connect_time '
                       'upstream_header=$upstream_header_time';

    # Formato per analisi degli errori upstream
    log_format upstream_debug '$remote_addr [$time_local] '
                              '"$request" $status '
                              'upstream=$upstream_addr '
                              'upstream_status=$upstream_status '
                              'upstream_time=$upstream_response_time '
                              'cache=$upstream_cache_status '
                              'tries=$upstream_connect_time';
}
```

---

## Performance Tuning

### Ottimizzazione del Kernel

Le performance di Nginx dipendono fortemente dai parametri del kernel Linux. Queste impostazioni si applicano a server ad alto traffico.

```bash
# /etc/sysctl.d/99-nginx-tuning.conf

# ── Connessioni TCP ──
# Dimensione della coda di backlog
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65535

# Riutilizzo rapido delle porte TIME_WAIT
net.ipv4.tcp_tw_reuse = 1

# Range di porte effimere (aumenta per molte connessioni in uscita)
net.ipv4.ip_local_port_range = 1024 65535

# Numero massimo di connessioni tracciate (conntrack)
net.netfilter.nf_conntrack_max = 1048576

# ── Buffer TCP ──
# min, default, max (in byte)
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 87380 16777216
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216

# ── TCP Keepalive ──
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_keepalive_probes = 5

# ── File descriptor ──
fs.file-max = 2097152

# Applica: sysctl -p /etc/sysctl.d/99-nginx-tuning.conf
```

```bash
# /etc/security/limits.d/nginx.conf
# Limiti per l'utente www-data
www-data soft nofile 65535
www-data hard nofile 65535
www-data soft nproc 65535
www-data hard nproc 65535
```

### sendfile, tcp_nopush, tcp_nodelay

Queste tre direttive controllano come Nginx trasferisce i dati al livello TCP. La loro interazione è spesso fraintesa.

```nginx
http {
    # sendfile: trasferisce file direttamente dal filesystem al socket
    # senza passare per lo spazio utente (zero-copy I/O).
    # Elimina una copia in memoria per ogni file servito.
    sendfile on;

    # tcp_nopush (corrisponde a TCP_CORK su Linux):
    # accumula i dati e invia pacchetti TCP completi.
    # Funziona SOLO con sendfile on.
    # Riduce il numero di pacchetti piccoli.
    tcp_nopush on;

    # tcp_nodelay (corrisponde a TCP_NODELAY, disabilita Nagle's algorithm):
    # invia i dati immediatamente senza attendere l'accumulo.
    # Attivato automaticamente per connessioni keepalive.
    # Riduce la latenza per risposte piccole.
    tcp_nodelay on;

    # Combinazione ottimale: tutte e tre abilitate.
    # Nginx usa tcp_nopush durante l'invio del corpo della risposta,
    # poi passa a tcp_nodelay per l'ultimo pacchetto.
}
```

### Compressione: Gzip vs Brotli

```nginx
# ── Gzip (incluso in Nginx) ──
gzip on;
gzip_vary on;
gzip_proxied any;
gzip_comp_level 4;              # 1-9, 4-6 è il migliore rapporto qualità/CPU
gzip_min_length 256;            # Non comprimere risposte < 256 byte
gzip_buffers 16 8k;
gzip_http_version 1.1;
gzip_types
    text/plain
    text/css
    text/xml
    text/javascript
    application/json
    application/javascript
    application/xml
    application/rss+xml
    application/atom+xml
    application/vnd.ms-fontobject
    font/opentype
    image/svg+xml
    image/x-icon;

# Non comprimere ciò che è già compresso
gzip_disable "msie6";

# ── Brotli (modulo esterno: ngx_brotli) ──
# Installazione: compilare con --add-dynamic-module=ngx_brotli
# oppure installare da repository (es. ppa:ondrej/nginx-mainline)
load_module modules/ngx_http_brotli_filter_module.so;
load_module modules/ngx_http_brotli_static_module.so;

brotli on;
brotli_comp_level 6;             # 0-11, 6 è un buon compromesso
brotli_min_length 256;
brotli_types
    text/plain
    text/css
    text/xml
    text/javascript
    application/json
    application/javascript
    application/xml
    application/rss+xml
    font/opentype
    image/svg+xml;

# Servire file pre-compressi con Brotli
# Crea file .br al deploy: brotli --best file.js -o file.js.br
brotli_static on;
gzip_static on;                  # Equivalente per gzip: file .gz
```

**Confronto compressione:**

| Formato | Riduzione tipica | CPU | Supporto browser |
|---------|-----------------|-----|-------------------|
| Gzip livello 4 | 60-70% | Basso | Universale |
| Gzip livello 9 | 65-75% | Alto | Universale |
| Brotli livello 6 | 70-80% | Medio | Tutti i browser moderni |
| Brotli livello 11 | 75-85% | Molto alto | Tutti i browser moderni |

> Brotli è superiore a Gzip per contenuti testuali, ma richiede HTTPS (i browser non accettano `Accept-Encoding: br` su HTTP). Pre-comprimere i file al momento del deploy (`brotli_static on`) elimina il costo CPU in runtime.

### Open File Cache

```nginx
http {
    # Cache dei file descriptor e metadati dei file
    # Evita chiamate stat() e open() ripetute per gli stessi file
    open_file_cache max=10000 inactive=60s;

    # Quanto spesso verificare che il file in cache sia ancora valido
    open_file_cache_valid 60s;

    # Numero minimo di accessi prima che un file entri in cache
    open_file_cache_min_uses 2;

    # Cachare anche gli errori (file non trovato)
    open_file_cache_errors on;
}
```

### Worker Tuning

```nginx
# Numero di worker = numero di CPU core
worker_processes auto;

# Affina il binding ai core per evitare context switching
worker_cpu_affinity auto;

# Connessioni per worker — deve coprire:
# connessioni client + connessioni upstream + file aperti
# Regola: worker_connections >= 2 × connessioni_client_per_worker
worker_connections 8192;

# Priorità del processo (nice value, -20 a 19)
# Valori negativi = priorità più alta
worker_priority -5;

# Accetta più connessioni alla volta quando viene notificato
multi_accept on;

# File descriptor massimi per worker
worker_rlimit_nofile 65535;
```

**Calcolo delle risorse:**
- Memoria per connessione ≈ 2-3 KB (senza proxy) / 8-16 KB (con proxy + buffering)
- `worker_processes × worker_connections` = connessioni simultanee massime
- 4 worker × 8192 connessioni = 32.768 connessioni simultanee
- Memoria stimata: 32.768 × 16 KB ≈ 512 MB (con proxy e buffering)

---

## Nginx come API Gateway

Nginx può fungere da API gateway leggero per autenticazione, autorizzazione e routing delle richieste API, senza la necessità di un API gateway dedicato.

### auth_request — Autenticazione tramite Subrequest

La direttiva `auth_request` invia una subrequest interna ad un servizio di autenticazione. Se il servizio risponde con 2xx, la richiesta procede; con 401/403, viene rifiutata.

```nginx
server {
    listen 443 ssl;
    server_name api.example.com;

    # Endpoint di autenticazione (servizio esterno)
    location = /auth/verify {
        internal;   # Accessibile solo come subrequest interna
        proxy_pass http://auth-service:8080/verify;

        # Non inviare il body della richiesta originale
        proxy_pass_request_body off;
        proxy_set_header Content-Length "";

        # Inoltra header necessari per la verifica
        proxy_set_header X-Original-URI $request_uri;
        proxy_set_header X-Original-Method $request_method;
        proxy_set_header Authorization $http_authorization;
        proxy_set_header X-Real-IP $remote_addr;

        # Timeout breve per il servizio di autenticazione
        proxy_connect_timeout 5s;
        proxy_read_timeout 5s;
    }

    # Endpoint protetto con auth_request
    location /api/ {
        # Verifica autenticazione prima di proseguire
        auth_request /auth/verify;

        # Cattura header dalla risposta del servizio di autenticazione
        auth_request_set $auth_user $upstream_http_x_auth_user;
        auth_request_set $auth_roles $upstream_http_x_auth_roles;
        auth_request_set $auth_tenant $upstream_http_x_auth_tenant;

        # Inoltra le informazioni di autenticazione al backend
        proxy_set_header X-Auth-User $auth_user;
        proxy_set_header X-Auth-Roles $auth_roles;
        proxy_set_header X-Auth-Tenant $auth_tenant;

        proxy_pass http://api_backend;
    }

    # Endpoint pubblico — nessuna autenticazione
    location /api/public/ {
        proxy_pass http://api_backend;
    }

    # Gestione errori di autenticazione
    error_page 401 = @auth_error_401;
    error_page 403 = @auth_error_403;

    location @auth_error_401 {
        default_type application/json;
        return 401 '{"error": "Autenticazione richiesta", "code": "AUTH_REQUIRED"}';
    }

    location @auth_error_403 {
        default_type application/json;
        return 403 '{"error": "Accesso negato", "code": "FORBIDDEN"}';
    }
}
```

### Validazione JWT con njs

Il modulo `njs` (Nginx JavaScript) permette di eseguire logica JavaScript dentro Nginx, ad esempio per validare token JWT senza un servizio esterno.

```nginx
# Carica il modulo njs
load_module modules/ngx_http_js_module.so;

http {
    # Importa lo script JavaScript
    js_path /etc/nginx/njs/;
    js_import auth from jwt_validator.js;

    server {
        # Validazione JWT tramite njs
        location /api/ {
            # Esegui la funzione di validazione
            js_content auth.validateJwt;

            # Se la validazione ha successo, njs invoca internamente
            # un proxy_pass al backend
        }
    }
}
```

```javascript
// /etc/nginx/njs/jwt_validator.js
// Nota: questo è un esempio semplificato.
// In produzione, usare una libreria JWT validata.

function validateJwt(r) {
    var token = r.headersIn['Authorization'];

    if (!token || !token.startsWith('Bearer ')) {
        r.return(401, JSON.stringify({error: 'Token mancante'}));
        return;
    }

    token = token.slice(7);
    var parts = token.split('.');

    if (parts.length !== 3) {
        r.return(401, JSON.stringify({error: 'Token non valido'}));
        return;
    }

    try {
        var payload = JSON.parse(
            Buffer.from(parts[1], 'base64url').toString()
        );

        // Verifica scadenza
        var now = Math.floor(Date.now() / 1000);
        if (payload.exp && payload.exp < now) {
            r.return(401, JSON.stringify({error: 'Token scaduto'}));
            return;
        }

        // Imposta header per il backend
        r.headersOut['X-Auth-User'] = payload.sub || '';
        r.headersOut['X-Auth-Roles'] = (payload.roles || []).join(',');

        // Prosegui verso il backend
        r.internalRedirect('/api_upstream' + r.uri);
    } catch (e) {
        r.return(401, JSON.stringify({error: 'Token malformato'}));
    }
}

export default { validateJwt };
```

### Routing API Basato su Versione

```nginx
# Routing per versione API con header
map $http_api_version $api_backend {
    "v1"    http://api_v1;
    "v2"    http://api_v2;
    default http://api_v2;   # Default all'ultima versione
}

# Routing per versione API con path
upstream api_v1 {
    server 10.0.1.10:8000;
    server 10.0.1.11:8000;
}

upstream api_v2 {
    server 10.0.2.10:8000;
    server 10.0.2.11:8000;
}

server {
    # Routing per path
    location /api/v1/ {
        proxy_pass http://api_v1/;
    }

    location /api/v2/ {
        proxy_pass http://api_v2/;
    }

    # Routing per header
    location /api/ {
        proxy_pass $api_backend;
    }
}
```

---

## WebSocket Proxying Avanzato

### Upgrade della Connessione

WebSocket richiede un upgrade del protocollo da HTTP/1.1 a WebSocket tramite gli header `Upgrade` e `Connection`. Nginx deve passare esplicitamente questi header al backend.

```nginx
# Mappa per gestire l'header Connection in base alla presenza di Upgrade
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

upstream websocket_backend {
    # Sticky session per WebSocket (i client devono tornare allo stesso server)
    ip_hash;
    server 10.0.0.1:3000;
    server 10.0.0.2:3000;
}

server {
    location /ws/ {
        proxy_pass http://websocket_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout per connessioni WebSocket
        # Deve essere abbastanza lungo per connessioni a lunga durata
        proxy_read_timeout 86400s;   # 24 ore
        proxy_send_timeout 86400s;

        # Disabilita il buffering per WebSocket
        proxy_buffering off;

        # Dimensione massima del messaggio
        # client_max_body_size non si applica a WebSocket frames
    }

    # Pattern misto: stessa location per HTTP e WebSocket
    location /app/ {
        proxy_pass http://app_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;

        # Se Upgrade è presente → WebSocket, altrimenti → HTTP normale
        # La mappa $connection_upgrade gestisce automaticamente questo caso
    }
}
```

### WebSocket con Heartbeat

```nginx
location /ws/ {
    proxy_pass http://websocket_backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;

    # Timeout lungo, ma il backend dovrebbe implementare ping/pong
    # Il ping WebSocket (opcode 0x9) passa attraverso Nginx trasparente
    proxy_read_timeout 300s;

    # Se il backend non invia ping, le connessioni inattive
    # verranno chiuse dopo proxy_read_timeout.
    # Soluzione: il backend deve inviare ping ogni < proxy_read_timeout
}
```

---

## High Availability e Failover

### Architettura ad Alta Disponibilità

```
                    ┌──────────┐
                    │   DNS    │
                    │ (Round   │
                    │  Robin)  │
                    └────┬─────┘
                         │
              ┌──────────┴──────────┐
              │                     │
        ┌─────▼─────┐        ┌─────▼─────┐
        │  Nginx 1  │        │  Nginx 2  │
        │  (MASTER) │◄──────►│ (BACKUP)  │
        │           │ VRRP/  │           │
        │  VIP:     │ keepa- │           │
        │ 10.0.0.50 │ lived  │           │
        └─────┬─────┘        └─────┬─────┘
              │                     │
      ┌───────┴───────┐    ┌───────┴───────┐
      │               │    │               │
  ┌───▼───┐  ┌───▼───┐  ┌───▼───┐  ┌───▼───┐
  │Back 1 │  │Back 2 │  │Back 3 │  │Back 4 │
  └───────┘  └───────┘  └───────┘  └───────┘
```

### Keepalived + Nginx (Active/Passive Failover)

```bash
# /etc/keepalived/keepalived.conf — MASTER
vrrp_script check_nginx {
    script "/usr/bin/pgrep nginx"
    interval 2
    weight 2
    fall 3
    rise 2
}

vrrp_instance VI_1 {
    state MASTER
    interface eth0
    virtual_router_id 51
    priority 101
    advert_int 1

    authentication {
        auth_type PASS
        auth_pass SecretPassword123
    }

    virtual_ipaddress {
        10.0.0.50/24
    }

    track_script {
        check_nginx
    }

    notify_master "/etc/keepalived/scripts/notify-master.sh"
    notify_backup "/etc/keepalived/scripts/notify-backup.sh"
}
```

### Upstream con Backup e Failover Avanzato

```nginx
upstream primary_backend {
    server 10.0.1.10:8000 max_fails=2 fail_timeout=10s;
    server 10.0.1.11:8000 max_fails=2 fail_timeout=10s;

    # Backup: usato solo se tutti i server primari falliscono
    server 10.0.2.10:8000 backup;

    # Timeout aggressivi per failover rapido
    keepalive 32;
}

server {
    location / {
        proxy_pass http://primary_backend;

        # Retry su errori — passa al prossimo server upstream
        proxy_next_upstream error timeout http_502 http_503 http_504;

        # Limite di tempo totale per i retry
        proxy_next_upstream_timeout 15s;

        # Numero massimo di tentativi
        proxy_next_upstream_tries 3;

        # Timeout brevi per rilevare problemi rapidamente
        proxy_connect_timeout 5s;
        proxy_read_timeout 15s;
    }
}
```

---

## Proxy per SSE, gRPC e HTTP/2 Backend

### Server-Sent Events (SSE) Proxy

```nginx
# SSE (Server-Sent Events) usa connessioni HTTP long-lived con
# Content-Type: text/event-stream. A differenza di WebSocket, SSE
# e` unidirezionale (server → client) e funziona su HTTP/1.1 standard.

# La sfida principale e` evitare che Nginx faccia buffering
# degli eventi, introducendo latenza nell'invio.

location /events {
    proxy_pass http://sse_backend;

    # CRITICO: disabilitare il buffering per SSE
    proxy_buffering off;

    # Disabilitare anche il chunked encoding verso il client
    # per garantire invio immediato di ogni evento
    proxy_cache off;

    # Timeout lungo: le connessioni SSE restano aperte a lungo
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;

    # Header standard per proxying
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

    # Forzare HTTP/1.1 (SSE non richiede upgrade come WebSocket)
    proxy_http_version 1.1;
    proxy_set_header Connection "";

    # Se si usa gzip a livello globale, disabilitarlo per SSE
    # (gli eventi sono piccoli e il buffering della compressione
    # aggiunge latenza inaccettabile)
    gzip off;
}

upstream sse_backend {
    server 10.0.1.10:8080;
    server 10.0.1.11:8080;
    # Non usare keepalive con SSE: le connessioni sono gia` long-lived
}
```

### gRPC Proxy

```nginx
# Nginx supporta il proxying gRPC nativo dalla versione 1.13.10+.
# gRPC utilizza HTTP/2 come trasporto, quindi richiede configurazione
# specifica per gestire i frame HTTP/2 correttamente.

# gRPC su TLS (consigliato per produzione)
upstream grpc_servers {
    server 10.0.1.10:50051;
    server 10.0.1.11:50051;
    # Bilanciamento round-robin di default.
    # Per gRPC, least_conn puo` funzionare meglio se le RPC
    # hanno durata variabile.
}

server {
    listen 443 ssl;
    http2 on;
    server_name grpc.example.com;

    ssl_certificate /etc/ssl/certs/grpc.example.com.pem;
    ssl_certificate_key /etc/ssl/private/grpc.example.com.key;

    location / {
        # grpc_pass al posto di proxy_pass per gRPC
        grpc_pass grpc://grpc_servers;

        # Timeout per chiamate unary e streaming
        grpc_read_timeout 300s;
        grpc_send_timeout 300s;

        # Per gRPC-Web (usato da browser):
        # grpc_pass grpcs://grpc_servers;  (se backend usa TLS)

        # Propagare metadata gRPC
        grpc_set_header X-Real-IP $remote_addr;
        grpc_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Health check endpoint gRPC (usa il protocollo standard gRPC Health)
    location = /grpc.health.v1.Health/Check {
        grpc_pass grpc://grpc_servers;
        # Timeout breve per health check
        grpc_read_timeout 5s;
    }
}

# gRPC senza TLS (solo per sviluppo/testing)
server {
    listen 8080;
    http2 on;

    location / {
        grpc_pass grpc://localhost:50051;
    }
}
```

### HTTP/2 Backend Proxying

```nginx
# Quando il backend supporta HTTP/2, Nginx puo` fare proxy
# usando HTTP/2 verso l'upstream per multiplexing e header compression.

upstream h2_backend {
    server 10.0.1.10:8443;
    server 10.0.1.11:8443;
    keepalive 64;  # HTTP/2 multiplexing riduce la necessita` di connessioni
}

server {
    listen 443 ssl;
    http2 on;
    server_name app.example.com;

    ssl_certificate /etc/ssl/certs/app.example.com.pem;
    ssl_certificate_key /etc/ssl/private/app.example.com.key;

    location / {
        proxy_pass https://h2_backend;

        # Abilitare HTTP/2 verso il backend (richiede Nginx 1.25.1+)
        proxy_http_version 1.1;   # Per HTTP/2 upstream: usare grpc_pass
        # NOTA: proxy_pass non supporta HTTP/2 nativo verso upstream
        # in Nginx OSS. Per HTTP/2 upstream, usare:
        # - Nginx Plus (con proxy_http_version 2)
        # - Envoy Proxy
        # - oppure grpc_pass per endpoint gRPC specifici

        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Active Health Checks (Nginx OSS Workaround)

```nginx
# Nginx OSS non supporta active health check come Nginx Plus.
# Workaround con un cron job + upstream reload:

# Script /etc/nginx/scripts/health-check.sh:
# #!/bin/bash
# set -euo pipefail
#
# UPSTREAM_CONF="/etc/nginx/conf.d/upstream-dynamic.conf"
# SERVERS="10.0.1.10 10.0.1.11 10.0.1.12"
# PORT=8080
# HEALTH_PATH="/health"
#
# echo "upstream app_backend {" > "$UPSTREAM_CONF.tmp"
# echo "    least_conn;" >> "$UPSTREAM_CONF.tmp"
#
# for srv in $SERVERS; do
#     HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
#         --max-time 3 "http://${srv}:${PORT}${HEALTH_PATH}" 2>/dev/null || echo "000")
#     if [ "$HTTP_CODE" = "200" ]; then
#         echo "    server ${srv}:${PORT};"  >> "$UPSTREAM_CONF.tmp"
#     else
#         echo "    # server ${srv}:${PORT} DOWN ($HTTP_CODE);" >> "$UPSTREAM_CONF.tmp"
#     fi
# done
#
# echo "    keepalive 32;" >> "$UPSTREAM_CONF.tmp"
# echo "}" >> "$UPSTREAM_CONF.tmp"
#
# # Verificare che almeno un server sia attivo
# if grep -q "server.*:${PORT};" "$UPSTREAM_CONF.tmp"; then
#     mv "$UPSTREAM_CONF.tmp" "$UPSTREAM_CONF"
#     nginx -t && nginx -s reload
# else
#     echo "CRITICAL: tutti i server DOWN, mantengo configurazione precedente"
#     rm -f "$UPSTREAM_CONF.tmp"
# fi

# Crontab: eseguire ogni 30 secondi
# (cron supporta solo minuti, quindi usare due entry)
# * * * * * /etc/nginx/scripts/health-check.sh >> /var/log/nginx/healthcheck.log 2>&1
# * * * * * sleep 30 && /etc/nginx/scripts/health-check.sh >> /var/log/nginx/healthcheck.log 2>&1

# Alternativa superiore: usare Lua con lua-resty-healthcheck
# (richiede OpenResty o Nginx compilato con lua-nginx-module)
```

---

## Configurazione Completa di Produzione

```nginx
# /etc/nginx/sites-available/production-app.conf

upstream app_backend {
    least_conn;
    server 10.0.1.10:8000 max_fails=3 fail_timeout=30s;
    server 10.0.1.11:8000 max_fails=3 fail_timeout=30s;
    server 10.0.1.12:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

# Rate limiting zones
limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;
limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/m;

# Redirect HTTP → HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name app.example.com;

    # Let's Encrypt ACME challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# Main HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name app.example.com;

    # SSL
    ssl_certificate /etc/letsencrypt/live/app.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.example.com/privkey.pem;
    include /etc/nginx/conf.d/ssl-params.conf;

    # Security headers
    include /etc/nginx/conf.d/security-headers.conf;

    # Limiti
    client_max_body_size 50m;
    client_body_timeout 60s;

    # File statici
    location /static/ {
        alias /var/www/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    location /media/ {
        alias /var/www/app/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # API con rate limiting
    location /api/ {
        limit_req zone=api burst=50 nodelay;

        proxy_pass http://app_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        proxy_connect_timeout 10s;
        proxy_read_timeout 30s;
        proxy_send_timeout 30s;

        proxy_next_upstream error timeout http_502 http_503;
        proxy_next_upstream_tries 2;
    }

    # Auth con rate limiting stringente
    location /api/auth/ {
        limit_req zone=auth burst=3;

        proxy_pass http://app_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://app_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 3600s;
    }

    # Frontend SPA
    location / {
        root /var/www/app/dist;
        try_files $uri $uri/ /index.html;

        location = /index.html {
            add_header Cache-Control "no-cache";
        }
    }

    # Deny accesso a file nascosti
    location ~ /\. {
        deny all;
        return 404;
    }
}
```

---

## Best Practices

1. **Testa sempre la configurazione prima del reload**: `nginx -t` valida la sintassi. `nginx -T` mostra la configurazione risolta. Mai `systemctl restart` senza test.

2. **Usa `server_tokens off`**: Non esporre la versione di Nginx nelle risposte HTTP. È informazione utile solo per un attaccante.

3. **Un server block per file**: Organizza la configurazione in file separati per ogni virtual host in `/etc/nginx/sites-available/` con symlink in `sites-enabled/`.

4. **Non usare `if` nelle location**: La direttiva `if` in Nginx non è un vero condizionale — ha comportamenti sorprendenti. Usa `map`, `try_files`, o location separate quando possibile.

5. **Imposta `client_max_body_size`**: Il default (1 MB) è troppo basso per la maggior parte delle applicazioni. Impostalo al minimo necessario per il tuo caso d'uso.

6. **Keepalive verso upstream**: Usa `keepalive` nella direttiva upstream e `proxy_http_version 1.1; proxy_set_header Connection "";` per riutilizzare le connessioni ai backend.

7. **Monitora upstream_response_time**: Questo è il tempo che il backend impiega a rispondere. Un aumento indica problemi nel backend, non in Nginx.

8. **Implementa rate limiting**: Ogni endpoint pubblico deve avere rate limiting. Gli endpoint di autenticazione devono avere limiti molto più stringenti.

9. **SSL/TLS aggiornato**: Disabilita TLS 1.0 e 1.1. Usa solo TLS 1.2+ con cipher suite moderne. Abilita HSTS solo dopo aver verificato che SSL funziona correttamente.

10. **Log in formato JSON**: I log JSON sono immensamente più facili da parsare e analizzare con strumenti come ELK, Loki, o script personalizzati.

---

## Debugging e Diagnostica

### Livelli di Log per il Debug

```nginx
# Livelli di log (dal meno al più verboso):
# emerg, alert, crit, error, warn, notice, info, debug

# Debug log — ATTENZIONE: genera enormi quantità di dati
# Usare SOLO per diagnostica temporanea
error_log /var/log/nginx/debug.log debug;

# Debug solo per specifici IP (riduce il volume)
events {
    debug_connection 192.168.1.100;
    debug_connection 10.0.0.0/24;
}

# Debug per singolo server block
server {
    error_log /var/log/nginx/app-debug.log debug;
    # ...
}
```

> **Nota**: il debug log richiede che Nginx sia compilato con `--with-debug`. Verificare: `nginx -V 2>&1 | grep -- '--with-debug'`. I pacchetti delle distribuzioni principali tipicamente includono il supporto debug.

### Comandi di Diagnostica

```bash
# ── Verifica configurazione ──
# Testa la sintassi della configurazione
nginx -t

# Mostra la configurazione risolta completa (tutti gli include espansi)
nginx -T

# Mostra la versione e le opzioni di compilazione
nginx -V

# ── Stato del processo ──
# Processi Nginx (master + worker)
ps aux | grep nginx

# File descriptor aperti per un worker
ls -la /proc/$(pgrep -f "worker process" | head -1)/fd | wc -l

# Connessioni attive per processo
ss -tnp | grep nginx | wc -l

# Connessioni per stato TCP
ss -tan | awk '{print $1}' | sort | uniq -c | sort -rn

# ── Analisi del traffico ──
# Richieste per secondo (dall'access log)
tail -f /var/log/nginx/access.log | pv -lr > /dev/null

# Top 10 IP per numero di richieste
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head

# Distribuzione degli status code
awk '{print $9}' /var/log/nginx/access.log | sort | uniq -c | sort -rn

# Richieste più lente (richiede il campo request_time nel log)
awk '$NF > 1.0 {print $NF, $7}' /var/log/nginx/access.log | sort -rn | head

# ── Analisi dei certificati SSL ──
# Verifica certificato in uso
echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null | \
    openssl x509 -noout -dates -subject -issuer

# Verifica OCSP stapling
openssl s_client -connect example.com:443 -status 2>/dev/null | \
    grep -A 10 "OCSP Response Status"

# ── Stub status ──
# Se stub_status è configurato
curl http://127.0.0.1:8080/nginx_status
# Active connections: 291
# server accepts handled requests
#  16630948 16630948 31070465
# Reading: 6 Writing: 179 Waiting: 106
#
# Reading = connessioni dove Nginx sta leggendo la richiesta
# Writing = connessioni dove Nginx sta scrivendo la risposta
# Waiting = connessioni keepalive inattive (è normale averne molte)
```

### Diagnosi Errori Comuni nei Log

| Messaggio nel log | Significato | Azione |
|-------------------|-------------|--------|
| `connect() failed (111: Connection refused)` | Backend non in ascolto | Verificare che il servizio backend sia attivo |
| `upstream timed out` | Backend troppo lento | Aumentare `proxy_read_timeout` o investigare il backend |
| `no live upstreams` | Tutti i backend marcati come down | Verificare health check, ridurre `fail_timeout` |
| `upstream sent too big header` | Header di risposta del backend troppo grandi | Aumentare `proxy_buffer_size` |
| `client intended to send too large body` | Request body > `client_max_body_size` | Aumentare `client_max_body_size` |
| `open() failed (13: Permission denied)` | Permessi file insufficienti | Verificare owner/permessi dei file |
| `SSL_do_handshake() failed` | Errore nella handshake TLS | Verificare certificati e cipher suite |
| `could not build optimal types_hash` | Hash table troppo piccola | Aumentare `types_hash_max_size` |
| `worker_connections are not enough` | Troppe connessioni simultanee | Aumentare `worker_connections` |
| `bind() failed (98: Address already in use)` | Porta già occupata | Trovare e terminare il processo che usa la porta |

---

## Troubleshooting

### Problema: 502 Bad Gateway

**Sintomi**: Nginx restituisce 502 per richieste proxied verso il backend.

**Causa**: Il backend non è raggiungibile, non è in ascolto, o ha crashato.

**Soluzione**:
```bash
# Verifica che il backend sia in ascolto
ss -tlnp | grep :8000

# Verifica connettività
curl -v http://127.0.0.1:8000/health

# Controlla i log di errore
tail -f /var/log/nginx/error.log
# "connect() failed (111: Connection refused)" → backend non in ascolto
# "upstream timed out" → backend troppo lento

# Verifica SELinux (se su RHEL)
setsebool -P httpd_can_network_connect 1
```

### Problema: 413 Request Entity Too Large

**Sintomi**: Upload di file fallisce con errore 413.

**Causa**: `client_max_body_size` è troppo basso (default: 1 MB).

**Soluzione**:
```nginx
# Nel contesto http, server, o location
client_max_body_size 50m;
```

### Problema: Redirect loop (ERR_TOO_MANY_REDIRECTS)

**Sintomi**: Il browser mostra errore di loop di redirect.

**Causa**: Configurazione di redirect HTTP→HTTPS che non gestisce correttamente il proxy header, o il backend genera anche un redirect.

**Soluzione**:
```nginx
# Se dietro un load balancer che termina SSL
server {
    listen 80;

    # Controlla l'header del load balancer, non il protocollo locale
    if ($http_x_forwarded_proto != 'https') {
        return 301 https://$host$request_uri;
    }

    location / {
        proxy_pass http://backend;
    }
}
```

### Problema: Performance scarse con file statici

**Sintomi**: Il serving di file statici è lento, CPU alta su Nginx.

**Causa**: `sendfile` disabilitato, compressione non attiva, o cache headers mancanti.

**Soluzione**:
```nginx
http {
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;

    gzip on;
    gzip_comp_level 4;
    gzip_types text/plain text/css application/javascript;

    open_file_cache max=2000 inactive=20s;
    open_file_cache_valid 30s;
}
```

### Problema: 504 Gateway Timeout

**Sintomi**: Nginx restituisce 504 per richieste che richiedono tempo.

**Causa**: Il backend non risponde entro il `proxy_read_timeout` (default 60s).

**Soluzione**:
```nginx
location /api/reports/ {
    proxy_pass http://backend;
    # Aumenta i timeout per endpoint lenti
    proxy_connect_timeout 10s;
    proxy_read_timeout 300s;    # 5 minuti per report complessi
    proxy_send_timeout 300s;
}
```

### Problema: upstream sent too big header

**Sintomi**: 502 con il messaggio "upstream sent too big header while reading response header from upstream" nel log degli errori.

**Causa**: Gli header di risposta del backend (tipicamente cookie o header custom) superano il `proxy_buffer_size` (default 4k/8k).

**Soluzione**:
```nginx
location / {
    proxy_pass http://backend;
    proxy_buffer_size 16k;         # Buffer per gli header
    proxy_buffers 4 32k;           # Buffer per il body
    proxy_busy_buffers_size 64k;
}
```

### Problema: Permission Denied (13) per file statici

**Sintomi**: Errore 403 o 500 con "open() failed (13: Permission denied)" nel log.

**Causa**: Il worker Nginx (utente `www-data` o `nginx`) non ha permessi di lettura sui file o sulle directory.

**Soluzione**:
```bash
# Verifica l'utente del worker
grep "^user" /etc/nginx/nginx.conf

# Imposta i permessi corretti
# Le directory necessitano di permesso di esecuzione (x)
find /var/www/html -type d -exec chmod 755 {} \;
find /var/www/html -type f -exec chmod 644 {} \;

# Verifica che l'intero percorso sia attraversabile
namei -l /var/www/html/index.html

# SELinux (RHEL/CentOS)
# Verifica se SELinux blocca l'accesso
ausearch -m avc -ts recent
# Imposta il contesto corretto
chcon -R -t httpd_sys_content_t /var/www/html/
# Oppure abilita il boolean specifico
setsebool -P httpd_can_network_connect 1
setsebool -P httpd_read_user_content 1
```

### Problema: SSL Handshake Failure

**Sintomi**: ERR_SSL_PROTOCOL_ERROR o "SSL_do_handshake() failed" nel log.

**Causa**: Certificato non valido, catena incompleta, cipher suite incompatibili, o protocollo TLS non supportato.

**Soluzione**:
```bash
# 1. Verifica il certificato
openssl s_client -connect example.com:443 -servername example.com

# 2. Verifica la catena
openssl verify -CAfile /etc/ssl/certs/ca-certificates.crt \
    /etc/letsencrypt/live/example.com/fullchain.pem

# 3. Verifica la corrispondenza chiave/certificato
diff <(openssl x509 -noout -modulus -in cert.pem) \
     <(openssl rsa -noout -modulus -in key.pem)

# 4. Testa i protocolli e le cipher
openssl s_client -connect example.com:443 -tls1_2
openssl s_client -connect example.com:443 -tls1_3
```

```nginx
# Configurazione SSL difensiva
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers HIGH:!aNULL:!MD5;
ssl_certificate /etc/ssl/certs/fullchain.pem;  # DEVE essere fullchain
ssl_certificate_key /etc/ssl/private/server.key;
```

### Problema: Connection Reset by Peer

**Sintomi**: Connessioni che si chiudono improvvisamente, "recv() failed (104: Connection reset by peer)" nel log.

**Causa**: Il backend chiude la connessione prima che Nginx abbia finito di leggere la risposta. Comune con connessioni keepalive mal configurate.

**Soluzione**:
```nginx
upstream backend {
    server 10.0.0.1:8000;
    keepalive 32;
    # Il keepalive_timeout di Nginx verso upstream deve essere
    # INFERIORE al timeout del backend, altrimenti Nginx tenta
    # di usare una connessione che il backend ha già chiuso
    keepalive_timeout 55s;  # Se il backend ha timeout=60s
}
```

### Problema: worker_connections are not enough

**Sintomi**: "worker_connections are not enough" nel log degli errori, connessioni rifiutate.

**Causa**: Il numero di connessioni simultanee supera `worker_connections × worker_processes`.

**Soluzione**:
```nginx
events {
    worker_connections 8192;   # Aumenta (default 512 o 1024)
}

# Aumenta anche il limite di file descriptor
worker_rlimit_nofile 65535;
```

```bash
# Verifica i limiti del sistema operativo
ulimit -n
cat /proc/sys/fs/file-max

# Aumenta se necessario
echo "www-data soft nofile 65535" >> /etc/security/limits.d/nginx.conf
echo "www-data hard nofile 65535" >> /etc/security/limits.d/nginx.conf
echo "fs.file-max = 2097152" >> /etc/sysctl.d/99-limits.conf
sysctl -p
```

### Problema: proxy_pass con Variabili non Funziona

**Sintomi**: Errore "no resolver defined to resolve" quando `proxy_pass` contiene una variabile.

**Causa**: Quando `proxy_pass` usa una variabile (es. `$backend`), Nginx non risolve il DNS al caricamento della config ma a runtime, e necessita di un resolver esplicito.

**Soluzione**:
```nginx
http {
    # Resolver obbligatorio quando proxy_pass usa variabili
    resolver 127.0.0.53 valid=30s ipv6=off;
    resolver_timeout 5s;

    server {
        set $backend "backend.service.consul";
        location / {
            proxy_pass http://$backend:8080;
        }
    }
}
```

### Problema: add_header Non Appare nella Risposta

**Sintomi**: Gli header aggiunti con `add_header` non compaiono nella risposta del browser.

**Causa**: `add_header` nel contesto figlio sovrascrive tutti gli header del contesto genitore. Inoltre, `add_header` senza `always` non viene aggiunto per risposte di errore.

**Soluzione**:
```nginx
server {
    # Gli header definiti qui vengono PERSI se una location ridefinisce add_header
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    location /api/ {
        # Questa location aggiunge un header → TUTTI gli header del server sono persi
        add_header X-Custom "value" always;

        # SOLUZIONE: ripetere tutti gli header necessari
        add_header X-Frame-Options "DENY" always;
        add_header X-Content-Type-Options "nosniff" always;

        # OPPURE: usare un file di include
        include /etc/nginx/conf.d/security-headers.conf;
        add_header X-Custom "value" always;

        proxy_pass http://backend;
    }
}
```

### Problema: if is Evil — Comportamenti Inattesi

**Sintomi**: Configurazioni con `if` che non funzionano come previsto, direttive ignorate, comportamenti imprevedibili.

**Causa**: La direttiva `if` in Nginx non è un vero condizionale imperativo — crea un nuovo contesto che può interagire in modo non intuitivo con altre direttive.

**Soluzione**: usare alternative a `if` quando possibile:
```nginx
# ── SBAGLIATO: if nel contesto location ──
location / {
    # PROBLEMA: set dentro if cambia il contesto
    if ($request_method = POST) {
        # Questo crea un contesto separato
        # Le direttive qui possono essere ignorate
        proxy_pass http://post_backend;
    }
    proxy_pass http://get_backend;
}

# ── CORRETTO: usare map + variabile ──
map $request_method $backend_by_method {
    POST    http://post_backend;
    default http://get_backend;
}

server {
    location / {
        proxy_pass $backend_by_method;
    }
}

# ── CORRETTO: usare location separate ──
server {
    location / {
        # Limita il metodo con limit_except
        limit_except GET HEAD {
            proxy_pass http://write_backend;
        }
        proxy_pass http://read_backend;
    }
}
```

> **Casi sicuri per `if`**: `return`, `rewrite`, e `set` sono sicuri dentro `if`. Fonte: https://www.nginx.com/resources/wiki/start/topics/depth/ifisevil/, consultato il 2026-05-23.

### Problema: CORS Non Funziona con Preflight

**Sintomi**: Le richieste OPTIONS (preflight) restituiscono errori CORS.

**Causa**: Le richieste OPTIONS non raggiungono il backend o mancano gli header CORS nella risposta.

**Soluzione**:
```nginx
location /api/ {
    # Gestisci preflight OPTIONS direttamente in Nginx
    if ($request_method = 'OPTIONS') {
        add_header Access-Control-Allow-Origin $cors_origin always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type, X-Requested-With" always;
        add_header Access-Control-Max-Age 86400 always;
        add_header Content-Length 0;
        return 204;
    }

    # Header CORS per richieste normali
    add_header Access-Control-Allow-Origin $cors_origin always;
    add_header Access-Control-Allow-Credentials "true" always;

    proxy_pass http://backend;
}
```

### Problema: Nginx Non Serve Brotli/Gzip

**Sintomi**: Le risposte non sono compresse nonostante la configurazione.

**Causa**: L'header `Accept-Encoding` del client non include il formato, il tipo MIME non è nella lista `gzip_types`, o il backend invia già l'header `Content-Encoding`.

**Soluzione**:
```bash
# 1. Verifica che il client invii Accept-Encoding
curl -H "Accept-Encoding: gzip, br" -I https://example.com/style.css

# 2. Verifica che il tipo MIME sia nella lista gzip_types
# 3. Verifica che la risposta non sia già compressa dal backend
curl -sI https://example.com/api/data | grep -i content-encoding

# 4. Per richieste proxy: gzip_proxied deve essere "any" o includere
# il tipo di cache control della risposta upstream
```

```nginx
gzip on;
gzip_proxied any;              # Comprimi anche risposte proxy
gzip_min_length 256;           # Non comprimere risposte troppo piccole
gzip_types text/plain text/css application/json application/javascript;
```

### Problema: Upstream Server Temporarily Disabled

**Sintomi**: Nginx smette di inviare richieste a un backend, "upstream server temporarily disabled while connecting" nel log.

**Causa**: Il backend ha superato `max_fails` nel periodo `fail_timeout` ed è stato temporaneamente rimosso dalla rotazione.

**Soluzione**:
```nginx
upstream backend {
    # Bilancia i valori per il tuo scenario:
    # max_fails=0 disabilita il passive health check (non raccomandato)
    # fail_timeout è sia la finestra di conteggio che il periodo di penalizzazione
    server 10.0.0.1:8000 max_fails=5 fail_timeout=10s;
    server 10.0.0.2:8000 max_fails=5 fail_timeout=10s;

    # Un backup garantisce che le richieste vengano servite
    # anche se tutti i server primari sono penalizzati
    server 10.0.0.3:8000 backup;
}
```

### Problema: WebSocket Disconnessioni Frequenti

**Sintomi**: Le connessioni WebSocket si chiudono dopo circa 60 secondi.

**Causa**: `proxy_read_timeout` default (60s) chiude le connessioni inattive.

**Soluzione**:
```nginx
location /ws/ {
    proxy_pass http://websocket_backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";

    # Timeout alto per WebSocket
    proxy_read_timeout 86400s;
    proxy_send_timeout 86400s;

    # Alternativa: il backend implementa ping/pong
    # e il proxy_read_timeout può restare più basso (es. 300s)
}
```

### Problema: try_files Non Funziona con proxy_pass

**Sintomi**: `try_files` in una location con `proxy_pass` non si comporta come previsto.

**Causa**: `try_files` e `proxy_pass` nella stessa location interferiscono. `try_files` controlla i file locali, ma `proxy_pass` deve inviare al backend.

**Soluzione**: usare una named location come fallback:
```nginx
location / {
    root /var/www/static;
    try_files $uri $uri/ @proxy;
}

location @proxy {
    proxy_pass http://backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### Problema: Locale/Encoding nei Filename

**Sintomi**: File con caratteri non-ASCII (UTF-8) nel nome restituiscono 404.

**Causa**: Nginx e il filesystem devono concordare sull'encoding.

**Soluzione**:
```nginx
# Abilita charset UTF-8 nelle risposte
charset utf-8;
charset_types text/plain text/css text/xml text/javascript
              application/json application/javascript;

# Verifica che il filesystem usi UTF-8
# locale -a | grep -i utf
```

---

## Migrazione da Apache a Nginx

### Equivalenze .htaccess → Nginx

Apache usa file `.htaccess` distribuiti per directory. Nginx non supporta questo modello: tutta la configurazione è centralizzata nel file di configurazione. Ecco le equivalenze più comuni.

#### Redirect e Rewrite

```apache
# Apache (.htaccess)
RewriteEngine On
RewriteRule ^old-page$ /new-page [R=301,L]
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}/$1 [R=301,L]
```

```nginx
# Nginx equivalente
server {
    listen 80;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    location = /old-page {
        return 301 /new-page;
    }
}
```

#### Directory Index e Directory Listing

```apache
# Apache
DirectoryIndex index.html index.php
Options +Indexes
```

```nginx
# Nginx
index index.html index.php;
autoindex on;        # Equivalente di Options +Indexes
autoindex_exact_size off;
autoindex_localtime on;
```

#### Negare l'Accesso

```apache
# Apache (.htaccess)
<Files ".ht*">
    Require all denied
</Files>

<Directory /var/www/private>
    Require ip 10.0.0.0/8
</Directory>
```

```nginx
# Nginx
location ~ /\.ht {
    deny all;
}

location /private/ {
    allow 10.0.0.0/8;
    deny all;
}
```

#### Autenticazione Basic

```apache
# Apache (.htaccess)
AuthType Basic
AuthName "Area Riservata"
AuthUserFile /etc/apache2/.htpasswd
Require valid-user
```

```nginx
# Nginx
location /admin/ {
    auth_basic "Area Riservata";
    auth_basic_user_file /etc/nginx/.htpasswd;
}

# Il file .htpasswd è compatibile tra Apache e Nginx
# Genera con: htpasswd -c /etc/nginx/.htpasswd username
```

#### Expires e Cache-Control

```apache
# Apache (mod_expires)
ExpiresActive On
ExpiresByType image/jpeg "access plus 30 days"
ExpiresByType text/css "access plus 7 days"
```

```nginx
# Nginx
location ~* \.(jpg|jpeg|png|gif|ico)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}

location ~* \.(css|js)$ {
    expires 7d;
    add_header Cache-Control "public";
}
```

#### PHP-FPM

```apache
# Apache (mod_php o php-fpm con ProxyPassMatch)
<FilesMatch \.php$>
    SetHandler "proxy:unix:/run/php/php-fpm.sock|fcgi://localhost/"
</FilesMatch>
```

```nginx
# Nginx
location ~ \.php$ {
    include fastcgi_params;
    fastcgi_pass unix:/run/php/php8.3-fpm.sock;
    fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    fastcgi_index index.php;

    # Sicurezza: impedisci l'esecuzione di PHP in directory di upload
    location ~* /uploads/.*\.php$ {
        deny all;
    }
}
```

#### Proxy e Load Balancing

```apache
# Apache (mod_proxy)
ProxyPass /api http://backend:8000/api
ProxyPassReverse /api http://backend:8000/api

<Proxy "balancer://mycluster">
    BalancerMember http://10.0.0.1:8000
    BalancerMember http://10.0.0.2:8000
    ProxySet lbmethod=byrequests
</Proxy>
```

```nginx
# Nginx
upstream mycluster {
    server 10.0.0.1:8000;
    server 10.0.0.2:8000;
}

location /api {
    proxy_pass http://mycluster;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

### Tabella di Riferimento Rapido

| Apache | Nginx |
|--------|-------|
| `.htaccess` | Configurazione centralizzata (`server {}`, `location {}`) |
| `RewriteRule` | `rewrite` oppure `return` |
| `RewriteCond` | `if`, `map`, o location separate |
| `ProxyPass` | `proxy_pass` |
| `<Directory>` | `location` |
| `<Files>` | `location ~` con regex |
| `AllowOverride` | Non applicabile (nessun .htaccess) |
| `mod_expires` | `expires`, `add_header Cache-Control` |
| `mod_deflate` | `gzip on;` |
| `mod_headers` | `add_header`, `proxy_set_header` |
| `mod_rewrite` | `rewrite`, `return`, `map` |
| `mod_ssl` | Direttive `ssl_*` |
| `mod_auth_basic` | `auth_basic` |
| `mod_proxy_balancer` | `upstream {}` |
| `ErrorDocument` | `error_page` |

> **Nota sulla migrazione**: Apache valuta `.htaccess` ad ogni richiesta, causando overhead I/O. Nginx carica la configurazione una volta in memoria al avvio/reload, il che è significativamente più performante. Questa differenza architettonica è la ragione principale per cui Nginx non supporta file di configurazione per-directory.

---

## Riferimenti

- **Nginx Documentation**: https://nginx.org/en/docs/
- **Nginx Pitfalls and Common Mistakes**: https://www.nginx.com/resources/wiki/start/topics/tutorials/config_pitfalls/
- **Mozilla SSL Configuration Generator**: https://ssl-config.mozilla.org/
- **Nginx Admin Guide**: https://docs.nginx.com/nginx/admin-guide/
- **H5BP Server Configs Nginx**: https://github.com/h5bp/server-configs-nginx
- **Certbot**: https://certbot.eff.org/
- `man nginx`

---

## Esercizi

### Esercizio 1: Reverse Proxy con Load Balancing e Health Check

**Obiettivo**: Configurare Nginx come reverse proxy per tre istanze di un'applicazione backend con load balancing e failover.

**Requisiti**:
1. Crea tre backend simulati con `python3 -m http.server` sulle porte 8001, 8002, 8003
2. Configura un upstream block con `least_conn` e `keepalive 16`
3. Imposta `max_fails=3` e `fail_timeout=15s` per ogni server
4. Configura `proxy_next_upstream` per retry automatici su 502/503/504
5. Aggiungi un server di backup sulla porta 8004
6. Verifica il failover fermando uno dei backend
7. Monitora gli upstream con il log format `upstream_debug`

**Verifica**:
```bash
# Testa il load balancing
for i in $(seq 1 30); do
    curl -s http://localhost/ | head -1
done

# Ferma un backend e verifica il failover
kill $(lsof -t -i:8002)
curl -v http://localhost/
```

### Esercizio 2: SSL/TLS Hardening con mTLS

**Obiettivo**: Configurare un server HTTPS con TLS 1.3, OCSP stapling e autenticazione mTLS per un endpoint API interno.

**Requisiti**:
1. Genera una CA interna con OpenSSL (EC P-256)
2. Genera un certificato server firmato dalla CA
3. Genera un certificato client firmato dalla stessa CA
4. Configura Nginx con:
   - Solo TLS 1.3 per l'endpoint mTLS
   - TLS 1.2+1.3 per l'endpoint pubblico
   - OCSP stapling (con `ssl_stapling_verify on`)
   - HSTS con `max-age=63072000; includeSubDomains`
5. L'endpoint `/api/internal/` richiede mTLS (`ssl_verify_client on`)
6. L'endpoint `/api/public/` non richiede certificato client
7. Testa con `curl --cert` e senza certificato client

**Verifica**:
```bash
# Test senza certificato client (deve fallire per /api/internal/)
curl -v --cacert ca.pem https://api-internal.example.com/api/internal/

# Test con certificato client (deve funzionare)
curl -v --cacert ca.pem --cert client.pem --key client.key \
    https://api-internal.example.com/api/internal/

# Verifica configurazione SSL
openssl s_client -connect api-internal.example.com:443 -tls1_3
```

### Esercizio 3: Rate Limiting e Caching Combinati

**Obiettivo**: Implementare rate limiting differenziato e proxy caching per un'API.

**Requisiti**:
1. Configura tre zone di rate limiting:
   - `general`: 30 req/s con burst=50 nodelay
   - `search`: 5 req/s con burst=10 (per `/api/search`)
   - `auth`: 3 req/min con burst=5 (per `/api/auth/login`)
2. Implementa whitelist per la rete interna (10.0.0.0/8)
3. Configura proxy cache per `/api/search` con:
   - TTL di 30 secondi
   - Cache key basata su URI + query string
   - Stale-while-revalidate
   - Header `X-Cache-Status` nella risposta
4. Escludi dal cache le richieste con header `Authorization`
5. Implementa microcaching (1s) per `/api/products`
6. Configura `limit_conn` a 10 connessioni simultanee per IP per `/api/export`
7. Restituisci risposte JSON per gli errori 429

**Verifica**:
```bash
# Test rate limiting
for i in $(seq 1 50); do
    curl -s -o /dev/null -w "%{http_code}\n" http://localhost/api/search?q=test
done

# Verifica caching
curl -I http://localhost/api/search?q=test | grep X-Cache-Status
```

### Esercizio 4: Nginx come API Gateway con auth_request

**Obiettivo**: Configurare Nginx come API gateway con autenticazione centralizzata tramite `auth_request`.

**Requisiti**:
1. Crea un semplice servizio di autenticazione (script Python/Node) che:
   - Verifica un header `Authorization: Bearer <token>`
   - Restituisce 200 se il token è valido, 401 se mancante, 403 se scaduto
   - Restituisce header `X-Auth-User` e `X-Auth-Roles` nella risposta
2. Configura Nginx con:
   - `auth_request` verso il servizio di autenticazione
   - `auth_request_set` per catturare user e roles dal servizio
   - Routing per versione API (`/api/v1/` e `/api/v2/`)
   - Rate limiting differenziato per ruolo (admin: illimitato, user: 30/s)
   - Error pages JSON per 401 e 403
3. L'endpoint `/api/public/health` non richiede autenticazione
4. Configura logging JSON con le informazioni di autenticazione

**Verifica**:
```bash
# Test senza token (401)
curl -v http://localhost/api/v1/users

# Test con token valido
curl -H "Authorization: Bearer valid-token" http://localhost/api/v1/users

# Verifica che gli header di autenticazione arrivino al backend
```

---

## Auto-valutazione

1. **Ereditarietà degli header**: Se definisci `add_header X-Custom "value"` in una `location {}` che è figlia di un `server {}` con `add_header X-Frame-Options "DENY"`, quali header saranno presenti nella risposta? Perché? Come risolvi il problema?

2. **Location matching**: Data la seguente configurazione, quale location gestirà la richiesta `GET /images/logo.png`? Quale gestirà `GET /images/avatars/user.jpg`?
   ```nginx
   location /images/ { root /var/www; }
   location ^~ /images/avatars/ { alias /var/www/user-uploads/; }
   location ~* \.(png|jpg)$ { expires 30d; root /var/www; }
   ```

3. **SSL/TLS**: Spiega la differenza tra `ssl_session_cache` e `ssl_session_tickets`. Quale dei due meccanismi è preferibile per forward secrecy e perché? In quale scenario useresti entrambi?

4. **Rate limiting**: Qual è la differenza tra `burst=20 nodelay` e `burst=20` senza `nodelay`? In quale scenario è preferibile usare `delay=10` (Nginx 1.15.7+)?

5. **Proxy buffering**: Quando è necessario disabilitare `proxy_buffering`? Quali sono le conseguenze sulle performance del backend? Come interagisce con Server-Sent Events (SSE)?

6. **Health check**: Spiega la differenza tra passive health check (open source) e active health check (Nginx Plus). Come si può simulare un active health check con Nginx open source?

7. **try_files e named location**: Perché `try_files $uri @backend` funziona ma `try_files $uri proxy_pass http://backend` non funziona? Qual è la semantica dell'ultimo argomento di `try_files`?

8. **HTTP/3 e QUIC**: Quali requisiti infrastrutturali (firewall, kernel, librerie TLS) sono necessari per abilitare HTTP/3 con Nginx? Perché TLS 1.3 è obbligatorio per QUIC? Quali sono i rischi di 0-RTT (Early Data)?

---

## Letture Primarie Consigliate

### RFC e Standard
- **RFC 7540** — HTTP/2 (Hypertext Transfer Protocol Version 2). Consultato il 2026-05-23. https://www.rfc-editor.org/rfc/rfc7540
- **RFC 9114** — HTTP/3 (Hypertext Transfer Protocol Version 3). Consultato il 2026-05-23. https://www.rfc-editor.org/rfc/rfc9114
- **RFC 9000** — QUIC: A UDP-Based Multiplexed and Secure Transport. Consultato il 2026-05-23. https://www.rfc-editor.org/rfc/rfc9000
- **RFC 8446** — TLS 1.3 (The Transport Layer Security Protocol Version 1.3). Consultato il 2026-05-23. https://www.rfc-editor.org/rfc/rfc8446
- **RFC 6797** — HSTS (HTTP Strict Transport Security). Consultato il 2026-05-23. https://www.rfc-editor.org/rfc/rfc6797
- **RFC 7525** — Recommendations for Secure Use of TLS and DTLS (BCP 195). Consultato il 2026-05-23. https://www.rfc-editor.org/rfc/rfc7525
- **RFC 5077** — TLS Session Resumption without Server-Side State. Consultato il 2026-05-23. https://www.rfc-editor.org/rfc/rfc5077

### Documentazione Ufficiale
- **Nginx Official Documentation** — https://nginx.org/en/docs/ — Consultato il 2026-05-23. La fonte primaria per tutte le direttive, variabili e moduli.
- **Nginx Admin Guide** — https://docs.nginx.com/nginx/admin-guide/ — Consultato il 2026-05-23. Guide pratiche per configurazione, deployment e troubleshooting.
- **Nginx Pitfalls and Common Mistakes** — https://www.nginx.com/resources/wiki/start/topics/tutorials/config_pitfalls/ — Consultato il 2026-05-23.
- **Nginx "If Is Evil"** — https://www.nginx.com/resources/wiki/start/topics/depth/ifisevil/ — Consultato il 2026-05-23.

### Sicurezza
- **OWASP Secure Headers Project** — https://owasp.org/www-project-secure-headers/ — Consultato il 2026-05-23. Linee guida per la configurazione degli header di sicurezza HTTP.
- **OWASP CSP Cheat Sheet** — https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html — Consultato il 2026-05-23.
- **Mozilla SSL Configuration Generator** — https://ssl-config.mozilla.org/ — Consultato il 2026-05-23. Generatore di configurazioni SSL/TLS per Nginx, Apache e altri server.
- **Mozilla Web Security Guidelines** — https://infosec.mozilla.org/guidelines/web_security — Consultato il 2026-05-23.

### Strumenti
- **SSL Labs Server Test** — https://www.ssllabs.com/ssltest/ — Verifica la configurazione SSL/TLS del server.
- **Security Headers** — https://securityheaders.com/ — Analizza gli header di sicurezza HTTP.
- **H5BP Server Configs Nginx** — https://github.com/h5bp/server-configs-nginx — Template di configurazione Nginx ottimizzati.

---

## Collegamenti Incrociati

| Modulo | Argomento | Relazione |
|--------|-----------|-----------|
| 15 — Sicurezza | Crittografia e TLS | Fondamenti di TLS, generazione certificati, PKI |
| 18 — Reti TCP/IP | Protocolli di rete | TCP, UDP, DNS, modello OSI — prerequisiti per capire il proxying |
| 19 — HTTP | Protocollo HTTP | Metodi, header, status code, cache — prerequisiti per configurare Nginx |
| 21 — Firewall | iptables/nftables | Regole firewall per porte TCP/UDP 80, 443 |
| 22 — DNS | Configurazione DNS | Record A, AAAA, CNAME per i virtual host Nginx |
| 26 — Systemd | Gestione servizi | `systemctl start/stop/reload nginx`, unit file, journald |
| 29 — Docker | Container | Nginx in container, docker-compose con backend |
| 30 — Monitoring | Osservabilità | Prometheus exporter per Nginx, Grafana dashboards, ELK per log |

---

## Glossario Locale

| Termine | Definizione |
|---------|------------|
| **ALPN** | Application-Layer Protocol Negotiation — estensione TLS per negoziare il protocollo applicativo (h2, http/1.1, h3) durante la handshake |
| **Cipher suite** | Combinazione di algoritmi crittografici per la negoziazione TLS: scambio chiavi + cifratura simmetrica + MAC + hash |
| **CSP** | Content Security Policy — header HTTP che limita le origini da cui il browser può caricare risorse, difesa primaria contro XSS |
| **Event loop** | Ciclo di elaborazione principale di un worker Nginx: attende eventi I/O (epoll/kqueue) e li processa senza mai bloccarsi |
| **Forward secrecy** | Proprietà crittografica che garantisce che la compromissione della chiave privata non comprometta le sessioni passate |
| **HPACK** | Algoritmo di compressione degli header HTTP/2 (RFC 7541) |
| **HSTS** | HTTP Strict Transport Security — header che obbliga il browser a usare solo HTTPS per il dominio (RFC 6797) |
| **Keepalive** | Riutilizzo di una connessione TCP esistente per richieste successive, evitando l'overhead di nuove connessioni |
| **Location** | Blocco di configurazione Nginx che definisce come gestire un URI o un pattern di URI |
| **mTLS** | Mutual TLS — autenticazione bidirezionale dove sia il server che il client presentano certificati |
| **Named location** | Location identificata da `@nome`, accessibile solo tramite redirect interni (`try_files`, `error_page`) |
| **OCSP stapling** | Il server include la risposta OCSP (validità del certificato) nella handshake TLS, evitando una query separata al client |
| **Proxy buffering** | Nginx memorizza l'intera risposta dal backend prima di inviarla al client, liberando il backend rapidamente |
| **QUIC** | Protocollo di trasporto basato su UDP che sostituisce TCP per HTTP/3, con handshake 0-RTT e connection migration (RFC 9000) |
| **Rate limiting** | Controllo del numero di richieste per unità di tempo, implementato con il modulo `ngx_http_limit_req_module` |
| **Reverse proxy** | Server che riceve richieste dai client e le inoltra ai backend, agendo come intermediario |
| **Server block** | Blocco `server {}` nella configurazione Nginx, equivalente al VirtualHost di Apache |
| **SNI** | Server Name Indication — estensione TLS che permette al client di specificare l'hostname durante la handshake, abilitando più certificati sulla stessa IP |
| **SSE** | Server-Sent Events — protocollo per streaming unidirezionale server→client su HTTP, richiede `proxy_buffering off` |
| **Sticky session** | Affinità che dirige le richieste di uno stesso client sempre allo stesso backend (via ip_hash, cookie, etc.) |
| **Upstream** | Blocco `upstream {}` che definisce un pool di server backend per il load balancing |
| **Worker** | Processo figlio di Nginx che gestisce le connessioni client tramite un event loop |
| **0-RTT** | Zero Round-Trip Time — invio di dati nella prima richiesta TLS senza attendere la handshake completa, vulnerabile a replay attack |
