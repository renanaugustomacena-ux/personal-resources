# Web Server Linux — Guida Completa

> **Modulo 17** · **Aggiornamento:** 2026-05-24

## Idee guida
1. **Nginx > Apache per modern workload.** Caddy per zero-config + auto-Let's Encrypt.
2. **Reverse proxy + WAF (ModSecurity, Coraza).**
3. **HTTP/3 + QUIC supported in nginx 1.25+.**
4. **Workers count = CPU cores typical.**
5. **HAProxy / Traefik per load balancing in ambienti container.**
6. **TLS 1.3 come minimo in produzione — disabilitare TLS 1.0/1.1.**


## Indice

- [Panoramica](#panoramica)
- [Nginx: Architettura](#nginx-architettura)
- [Nginx: Installazione e Configurazione](#nginx-installazione-e-configurazione)
- [Nginx: Location Blocks e Regex Matching](#nginx-location-blocks-e-regex-matching)
- [Nginx: Reverse Proxy e Load Balancer](#nginx-reverse-proxy-e-load-balancer)
- [Nginx: SSL/TLS](#nginx-ssltls)
- [Nginx: Performance Tuning](#nginx-performance-tuning)
- [Nginx: Sicurezza e Hardening](#nginx-sicurezza-e-hardening)
- [Apache: Architettura e MPM](#apache-architettura-e-mpm)
- [Apache: Fondamenti](#apache-fondamenti)
- [Apache: Virtual Host e Moduli](#apache-virtual-host-e-moduli)
- [Apache: mod_rewrite](#apache-mod_rewrite)
- [Apache: mod_security](#apache-mod_security)
- [Apache vs Nginx: Confronto](#apache-vs-nginx-confronto)
- [Caddy: Web Server con HTTPS Automatico](#caddy-web-server-con-https-automatico)
- [Caddy: Approfondimento Avanzato](#caddy-approfondimento-avanzato)
- [Traefik: Reverse Proxy Cloud-Native](#traefik-reverse-proxy-cloud-native)
- [Traefik: Kubernetes e Middleware Avanzati](#traefik-kubernetes-e-middleware-avanzati)
- [HAProxy: Load Balancer TCP/HTTP](#haproxy-load-balancer-tcphttp)
- [Virtual Hosts: Name-Based, IP-Based, SNI](#virtual-hosts-name-based-ip-based-sni)
- [Certificati TLS/SSL: Tipologie e CA](#certificati-tlsssl-tipologie-e-ca)
- [Certbot e Let's Encrypt](#certbot-e-lets-encrypt)
- [HTTP/2 e HTTP/3 (QUIC)](#http2-e-http3-quic)
- [Web Application Firewall (WAF)](#web-application-firewall-waf)
- [Caching: Proxy Cache e CDN](#caching-proxy-cache-e-cdn)
- [Web Server Hardening](#web-server-hardening)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Checklist Deploy Produzione](#checklist-deploy-produzione)

---

## Panoramica

Nginx e Apache sono i web server dominanti nel mondo Linux. Nginx eccelle come reverse proxy, load balancer e per servire contenuti statici. Apache è maturo, flessibile e supporta `.htaccess` per configurazione distribuita. La scelta dipende dal caso d'uso: Nginx per architetture moderne (reverse proxy per app), Apache per hosting tradizionale. Entrambi supportano SSL/TLS con Let's Encrypt (Certbot) per certificati gratuiti.

Oltre a Nginx e Apache, il panorama dei web server Linux include Caddy (HTTPS automatico, zero-config), Traefik (cloud-native, auto-discovery container), HAProxy (load balancing ad alte prestazioni), e LiteSpeed (drop-in Apache replacement con performance superiori).

### Quota di mercato e posizionamento

| Web Server | Quota globale (~2026) | Caso d'uso primario |
|------------|----------------------|---------------------|
| Nginx      | ~34%                 | Reverse proxy, static serving, load balancing |
| Apache     | ~30%                 | Hosting tradizionale, shared hosting, .htaccess |
| Cloudflare | ~21%                 | CDN/edge (non installabile) |
| Caddy      | ~2%                  | HTTPS automatico, deployment semplici |
| LiteSpeed  | ~12%                 | Hosting ad alte performance, cPanel |
| Traefik    | container-native     | Kubernetes, Docker Swarm |
| HAProxy    | infrastruttura       | Load balancing TCP/HTTP puro |

### Concetti fondamentali

**Web server statico:** serve file dal filesystem (HTML, CSS, JS, immagini). Nginx e Apache fanno questo nativamente.

**Reverse proxy:** riceve richieste dai client e le inoltra a server backend (Node.js, Python/Gunicorn, Go, PHP-FPM). Il client non comunica mai direttamente col backend.

**Load balancer:** distribuisce il traffico tra più istanze backend per scalabilità e alta disponibilità.

**Terminazione SSL/TLS:** il web server gestisce la crittografia TLS e inoltra traffico in chiaro al backend sulla rete interna.

---

## Nginx: Architettura

> Per la trattazione approfondita dell'architettura Nginx, vedere il **Modulo 28 — Nginx Configurazione Avanzata**.

### Modello event-driven

Nginx utilizza un'architettura radicalmente diversa da Apache. Invece di creare un processo o thread per ogni connessione (modello prefork/worker di Apache), Nginx usa un modello event-driven basato su I/O asincrono non bloccante.

```
┌──────────────────────────────────────────────────┐
│                  Master Process                    │
│  - Legge e valida la configurazione               │
│  - Binding sulle porte (80, 443)                  │
│  - Genera e gestisce i worker processes            │
│  - Gestisce segnali (reload, stop, reopen)        │
└───────────┬──────────┬──────────┬────────────────┘
            │          │          │
    ┌───────▼──┐ ┌─────▼────┐ ┌──▼─────────┐
    │ Worker 1 │ │ Worker 2 │ │ Worker N   │
    │          │ │          │ │            │
    │ epoll()  │ │ epoll()  │ │ epoll()    │
    │ event    │ │ event    │ │ event      │
    │ loop     │ │ loop     │ │ loop       │
    │          │ │          │ │            │
    │ migliaia │ │ migliaia │ │ migliaia   │
    │ di conn. │ │ di conn. │ │ di conn.  │
    └──────────┘ └──────────┘ └────────────┘
```

**Master process:** gira come root, esegue il bind sulle porte privilegiate (80, 443), legge la configurazione, genera e monitora i worker. Non gestisce mai traffico direttamente.

**Worker processes:** girano come utente non privilegiato (tipicamente `www-data` o `nginx`). Ogni worker gestisce migliaia di connessioni simultanee usando un event loop basato su `epoll` (Linux), `kqueue` (BSD/macOS), o `select`/`poll` (fallback).

```bash
# Processo master e worker in esecuzione
ps aux | grep nginx
# root      1234  ...  nginx: master process /usr/sbin/nginx
# www-data  1235  ...  nginx: worker process
# www-data  1236  ...  nginx: worker process
# www-data  1237  ...  nginx: worker process
# www-data  1238  ...  nginx: worker process
```

### Novità Nginx 1.27.x e 1.28.0 (2025)

Nginx 1.28.0, rilasciato ad aprile 2025, è la versione stabile corrente. Il ramo di sviluppo 1.27.x ha introdotto diverse novità significative:

**Sicurezza TLS (1.27.3)**:
- TLSv1 e TLSv1.1 rimossi dai protocolli abilitati per default. La direttiva `ssl_protocols` ora include solo TLSv1.2 e TLSv1.3 senza dichiarazione esplicita
- Implicazione: configurazioni che facevano affidamento su TLS 1.0/1.1 per client legacy smettono di funzionare dopo l'aggiornamento senza esplicito `ssl_protocols TLSv1 TLSv1.1 TLSv1.2 TLSv1.3` (sconsigliato)

**Cache certificati SSL (1.27.1)**:
```nginx
# Nuova direttiva: caching dei certificati SSL in memoria
ssl_certificate_cache shared:cert_cache:10m;

# Riduce il tempo di I/O disco durante l'handshake TLS
# Particolarmente utile con centinaia di virtual host
# Ogni certificato occupa ~4KB in cache

# Opzionale: ereditarietà della cache tra contesti
ssl_object_cache_inheritable on;
```

**Risoluzione dinamica upstream (1.27.2)**:
```nginx
# Il parametro resolve abilita la risoluzione DNS periodica
# per i backend upstream, senza bisogno di NGINX Plus
upstream dynamic_backend {
    zone backend_zone 64k;
    server backend.service.consul:8080 resolve;
    resolver 127.0.0.1:8600 valid=30s;  # Consul DNS
}
# Utile per ambienti container dove gli IP dei backend cambiano
```

**Keepalive migliorato (1.27.4)**:
```nginx
# Nuova direttiva: timeout minimo per keepalive
keepalive_min_timeout 20s;
# Previene che i client chiudano le connessioni keepalive troppo presto
# Riduce il tasso di rinegoziazione TCP/TLS
```

**QUIC CUBIC (1.27.5)**:
- Algoritmo di controllo congestione CUBIC per le connessioni QUIC, migliorando le performance su link con bandwidth-delay product elevato rispetto al precedente Reno
- Attivato a livello di compilazione, non richiede configurazione runtime

### Struttura della configurazione

La configurazione Nginx è organizzata in contesti gerarchici con ereditarietà delle direttive:

```
nginx.conf
├── main context (globale)
│   ├── events { }           # Configurazione event loop
│   └── http { }             # Configurazione HTTP
│       ├── upstream { }     # Pool di backend
│       ├── server { }       # Virtual host (server block)
│       │   ├── location { } # Matching URL
│       │   │   └── location { }  # Location nidificate
│       │   └── location { }
│       └── server { }       # Altro virtual host
├── stream { }               # Proxy TCP/UDP (L4)
└── mail { }                 # Proxy mail (SMTP/IMAP/POP3)
```

Le direttive definite in un contesto padre vengono ereditate dai contesti figli, a meno che non siano esplicitamente sovrascritte. Questo è il meccanismo più importante da comprendere per evitare errori di configurazione.

```nginx
# Esempio di ereditarietà
http {
    # Queste direttive valgono per TUTTI i server block
    gzip on;
    gzip_types text/plain text/css application/json;

    server {
        # Eredita gzip on dal contesto http
        listen 80;
        server_name sito-a.com;

        location /api/ {
            # Eredita gzip on dal server → http
            proxy_pass http://backend;
        }
    }

    server {
        listen 80;
        server_name sito-b.com;
        # Sovrascrivo: disabilito gzip per questo sito
        gzip off;
    }
}
```

### Come Nginx elabora una richiesta

1. **Fase 1 — Server selection:** Nginx determina quale `server` block deve gestire la richiesta, basandosi su IP:porta e header `Host`
2. **Fase 2 — Location matching:** all'interno del server block selezionato, Nginx trova la `location` più specifica che corrisponde all'URI
3. **Fase 3 — Esecuzione:** vengono applicate le direttive della location selezionata (serve file, proxy pass, redirect, ecc.)

---

## Nginx: Installazione e Configurazione

```bash
# Installazione
sudo apt install nginx
sudo systemctl enable --now nginx

# File di configurazione
/etc/nginx/nginx.conf                  # Configurazione principale
/etc/nginx/conf.d/                     # Configurazioni aggiuntive
/etc/nginx/sites-available/            # Siti disponibili (Debian/Ubuntu)
/etc/nginx/sites-enabled/              # Siti attivi (symlink)
/var/log/nginx/access.log              # Log accessi
/var/log/nginx/error.log               # Log errori
/var/www/html/                         # Document root default

# Comandi
sudo nginx -t                          # Test configurazione
sudo nginx -T                          # Test + dump config
sudo systemctl reload nginx            # Applica modifiche
```

### Installazione da repository ufficiale Nginx

I repository Debian/Ubuntu includono una versione di Nginx spesso non aggiornata. Per avere l'ultima versione stabile o mainline:

```bash
# Aggiungere la chiave GPG ufficiale Nginx
curl -fsSL https://nginx.org/keys/nginx_signing.key | \
    sudo gpg --dearmor -o /usr/share/keyrings/nginx-archive-keyring.gpg

# Aggiungere il repository (Ubuntu esempio)
echo "deb [signed-by=/usr/share/keyrings/nginx-archive-keyring.gpg] \
    http://nginx.org/packages/ubuntu $(lsb_release -cs) nginx" | \
    sudo tee /etc/apt/sources.list.d/nginx.list

# Priorità al repo ufficiale Nginx
echo -e "Package: *\nPin: origin nginx.org\nPin-Priority: 900" | \
    sudo tee /etc/apt/preferences.d/99nginx

sudo apt update && sudo apt install nginx
```

### Configurazione Base

```nginx
# /etc/nginx/sites-available/example.com
server {
    listen 80;
    listen [::]:80;
    server_name example.com www.example.com;

    root /var/www/example.com;
    index index.html index.htm;

    # Logging
    access_log /var/log/nginx/example.com.access.log;
    error_log /var/log/nginx/example.com.error.log;

    location / {
        try_files $uri $uri/ =404;
    }

    # File statici con cache
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff2)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Blocca accesso a file nascosti
    location ~ /\. {
        deny all;
    }
}
```

```bash
# Attivare sito
sudo ln -s /etc/nginx/sites-available/example.com /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### nginx.conf — Struttura principale

```nginx
# /etc/nginx/nginx.conf
user www-data;
worker_processes auto;                    # 1 worker per core CPU
pid /run/nginx.pid;
error_log /var/log/nginx/error.log warn;

# Limiti file descriptor per worker
worker_rlimit_nofile 65535;

events {
    worker_connections 4096;              # Connessioni per worker
    multi_accept on;                      # Accetta più connessioni simultanee
    use epoll;                            # Event method Linux
}

http {
    # MIME types
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging format
    log_format main '$remote_addr - $remote_user [$time_local] '
                    '"$request" $status $body_bytes_sent '
                    '"$http_referer" "$http_user_agent" '
                    '$request_time $upstream_response_time';

    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 4;
    gzip_min_length 256;
    gzip_types text/plain text/css application/json
               application/javascript text/xml application/xml
               application/xml+rss text/javascript
               image/svg+xml application/wasm;

    # Include configurazioni siti
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
```

---

## Nginx: Location Blocks e Regex Matching

Il matching delle location è uno degli aspetti più critici di Nginx. L'ordine di priorità è preciso e deterministico.

### Priorità di matching

| Priorità | Modificatore | Tipo | Esempio |
|----------|-------------|------|---------|
| 1 (max)  | `=`         | Exact match | `location = /favicon.ico` |
| 2        | `^~`        | Preferential prefix | `location ^~ /images/` |
| 3        | `~`         | Case-sensitive regex | `location ~ \.php$` |
| 3        | `~*`        | Case-insensitive regex | `location ~* \.(jpg\|png)$` |
| 4 (min)  | (nessuno)   | Prefix match | `location /api/` |

### Algoritmo di selezione

1. Nginx valuta tutti i prefix match e trova il **più lungo** che corrisponde
2. Se il più lungo ha `=` → usa quello immediatamente, stop
3. Se il più lungo ha `^~` → usa quello immediatamente, stop
4. Altrimenti memorizza il prefix più lungo e valuta le regex **in ordine di apparizione nel file**
5. Se una regex corrisponde → usa quella
6. Se nessuna regex corrisponde → usa il prefix memorizzato

```nginx
server {
    listen 80;
    server_name example.com;

    # 1. Exact match — solo GET /
    location = / {
        # Viene usata SOLO per richieste a "/"
        return 200 "Homepage esatta\n";
    }

    # 2. Preferential prefix — tutto sotto /static/ 
    # NON viene sovrascritta da regex
    location ^~ /static/ {
        root /var/www;
        expires 30d;
    }

    # 3. Case-insensitive regex — file PHP
    location ~* \.php$ {
        fastcgi_pass unix:/run/php/php8.3-fpm.sock;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }

    # 4. Case-sensitive regex — API versionate
    location ~ ^/api/v[0-9]+/ {
        proxy_pass http://api_backend;
    }

    # 5. Prefix match generico — fallback
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Prefix match specifico — più lungo di /
    location /api/ {
        # ATTENZIONE: questa viene sovrascritta dalla regex ^/api/v[0-9]+/
        # per URL come /api/v2/users, ma usata per /api/health
        proxy_pass http://api_backend;
    }
}
```

### Errori comuni con le location

```nginx
# ERRORE 1: regex che sovrascrive un prefix non intenzionalmente
location /uploads/ {
    alias /data/uploads/;
}
location ~* \.(jpg|png)$ {
    # Questa cattura ANCHE /uploads/foto.jpg!
    # La regex ha priorità su prefix semplice
    expires 30d;
}

# SOLUZIONE: usare ^~ per proteggere il prefix
location ^~ /uploads/ {
    alias /data/uploads/;
}

# ERRORE 2: location = con trailing slash
location = /about/ {
    # NON matcha /about (senza slash)
    # Servono DUE location o un redirect
}

# ERRORE 3: try_files e proxy_pass insieme
location /app/ {
    try_files $uri $uri/ @backend;    # Corretto: fallback con named location
}
location @backend {
    proxy_pass http://127.0.0.1:3000;
}
```

### Named locations

```nginx
# Named location per gestire fallback
location / {
    try_files $uri $uri/ @fallback;
}

location @fallback {
    proxy_pass http://backend_app;
    proxy_set_header Host $host;
}

# Named location per pagine errore custom
error_page 502 503 504 @maintenance;
location @maintenance {
    root /var/www/maintenance;
    try_files /maintenance.html =502;
}
```

---

## Nginx: Reverse Proxy e Load Balancer

### Reverse Proxy

```nginx
# Proxy verso applicazione backend (Node.js, Python, etc.)
server {
    listen 80;
    server_name app.example.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeout
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### Upstream e Load Balancing

```nginx
upstream backend {
    # Round-robin (default)
    server 10.0.0.1:3000;
    server 10.0.0.2:3000;
    server 10.0.0.3:3000;

    # Weighted
    # server 10.0.0.1:3000 weight=3;
    # server 10.0.0.2:3000 weight=1;

    # Least connections
    # least_conn;

    # IP hash (sticky sessions)
    # ip_hash;

    # Health check (passivo)
    # server 10.0.0.1:3000 max_fails=3 fail_timeout=30s;

    # Backup server
    # server 10.0.0.4:3000 backup;
}

server {
    listen 80;
    server_name app.example.com;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Algoritmi di load balancing in dettaglio

```nginx
# 1. ROUND-ROBIN (default)
# Distribuisce le richieste in sequenza tra i server
upstream backend_rr {
    server 10.0.0.1:8080;
    server 10.0.0.2:8080;
    server 10.0.0.3:8080;
}

# 2. WEIGHTED ROUND-ROBIN
# Server con peso maggiore riceve più richieste (3:2:1)
upstream backend_weighted {
    server 10.0.0.1:8080 weight=3;     # 50% del traffico
    server 10.0.0.2:8080 weight=2;     # 33% del traffico
    server 10.0.0.3:8080 weight=1;     # 17% del traffico
}

# 3. LEAST CONNECTIONS
# Invia al server con meno connessioni attive
# Ideale quando le richieste hanno durata variabile
upstream backend_least {
    least_conn;
    server 10.0.0.1:8080;
    server 10.0.0.2:8080;
    server 10.0.0.3:8080;
}

# 4. IP HASH (sticky sessions)
# Stesso IP → stesso server (per sessioni stateful)
# ATTENZIONE: non funziona con CDN/proxy davanti
upstream backend_iphash {
    ip_hash;
    server 10.0.0.1:8080;
    server 10.0.0.2:8080;
    server 10.0.0.3:8080;
    # Per rimuovere temporaneamente un server senza
    # ridistribuire tutti gli hash:
    # server 10.0.0.2:8080 down;
}

# 5. GENERIC HASH
# Hash su una variabile arbitraria
upstream backend_hash {
    hash $request_uri consistent;       # Consistent hashing
    server 10.0.0.1:8080;
    server 10.0.0.2:8080;
}

# 6. RANDOM con least_conn
# Due server casuali, sceglie quello con meno connessioni
upstream backend_random {
    random two least_conn;
    server 10.0.0.1:8080;
    server 10.0.0.2:8080;
    server 10.0.0.3:8080;
}
```

### Health checks passivi

```nginx
upstream backend {
    server 10.0.0.1:8080 max_fails=3 fail_timeout=30s;
    server 10.0.0.2:8080 max_fails=3 fail_timeout=30s;
    server 10.0.0.3:8080 max_fails=3 fail_timeout=30s backup;

    # max_fails=3    → dopo 3 errori consecutivi, marca come down
    # fail_timeout=30s → per 30 secondi non invia traffico,
    #                    poi riprova
    # backup         → usato solo quando tutti gli altri sono down
}
```

### Keepalive verso backend

```nginx
upstream backend {
    server 10.0.0.1:8080;
    server 10.0.0.2:8080;

    # Connessioni persistenti verso il backend
    # Riduce overhead di TCP handshake
    keepalive 32;
    keepalive_requests 1000;
    keepalive_timeout 60s;
}

server {
    location / {
        proxy_pass http://backend;
        # OBBLIGATORIO per keepalive upstream
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
}
```

---

## Nginx: SSL/TLS

```nginx
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    # Protocolli e cipher
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/example.com/chain.pem;

    # Session cache
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    root /var/www/example.com;
    index index.html;
}

# Redirect HTTP → HTTPS
server {
    listen 80;
    server_name example.com www.example.com;
    return 301 https://$host$request_uri;
}
```

### Configurazione SSL/TLS moderna raccomandata

```nginx
# /etc/nginx/conf.d/ssl-params.conf
# Profilo "Intermediate" di Mozilla SSL Configuration Generator

# Solo TLS 1.2 e 1.3
ssl_protocols TLSv1.2 TLSv1.3;

# Cipher suites — TLS 1.2
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;

# TLS 1.3 usa i propri cipher, configurati automaticamente
# Non serve ssl_ciphers per TLS 1.3

# Non forzare la preferenza del server sui cipher con TLS 1.3
ssl_prefer_server_ciphers off;

# Parametri DH (generare con: openssl dhparam -out /etc/nginx/dhparam.pem 4096)
ssl_dhparam /etc/nginx/dhparam.pem;

# OCSP Stapling — il server fornisce la risposta OCSP al client
# Evita che il client contatti la CA direttamente (privacy + velocità)
ssl_stapling on;
ssl_stapling_verify on;
resolver 1.1.1.1 8.8.8.8 valid=300s;
resolver_timeout 5s;

# Session resumption — migliora performance handshake ripetuti
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 1d;
ssl_session_tickets off;        # Disabilitato per forward secrecy

# HSTS — forza HTTPS per il tempo specificato
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
```

### Generare parametri DH e certificato self-signed (test)

```bash
# Parametri Diffie-Hellman (produzione)
sudo openssl dhparam -out /etc/nginx/dhparam.pem 4096
# NOTA: impiega diversi minuti — eseguire in background

# Certificato self-signed (solo test/sviluppo)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/selfsigned.key \
    -out /etc/ssl/certs/selfsigned.crt \
    -subj "/CN=localhost"
```

### Verifica configurazione SSL

```bash
# Test locale
openssl s_client -connect example.com:443 -servername example.com

# Verifica catena certificati
openssl s_client -connect example.com:443 -showcerts

# Verifica data scadenza
echo | openssl s_client -connect example.com:443 2>/dev/null | \
    openssl x509 -noout -dates

# Verifica protocolli supportati
nmap --script ssl-enum-ciphers -p 443 example.com

# Verifica OCSP stapling
openssl s_client -connect example.com:443 -status

# Test online completo: https://www.ssllabs.com/ssltest/
```

---

## Nginx: Performance Tuning

> Per tuning avanzato, vedere il **Modulo 28 — Nginx Configurazione Avanzata**.

### Worker processes e connections

```nginx
# /etc/nginx/nginx.conf

# Worker processes = numero di core CPU
# 'auto' rileva automaticamente
worker_processes auto;

# File descriptor per worker (deve essere >= worker_connections * 2)
worker_rlimit_nofile 65535;

events {
    # Connessioni simultanee per worker
    # Totale massimo = worker_processes × worker_connections
    # Es: 4 core × 4096 = 16384 connessioni simultanee
    worker_connections 4096;

    # Accetta tutte le connessioni in coda (non una alla volta)
    multi_accept on;

    # Metodo di event notification (Linux usa epoll)
    use epoll;
}
```

### Sendfile, tcp_nopush, tcp_nodelay

```nginx
http {
    # sendfile: trasferimento file diretto kernel→socket
    # Bypassa lo userspace, enormemente più efficiente per file statici
    sendfile on;

    # tcp_nopush (TCP_CORK): accumula i dati fino a un pacchetto pieno
    # prima di inviare. Riduce il numero di pacchetti.
    # Funziona SOLO con sendfile on
    tcp_nopush on;

    # tcp_nodelay (Nagle off): invia immediatamente senza buffering
    # Utile per connessioni keepalive dopo che tcp_nopush ha inviato
    tcp_nodelay on;
}
```

### Keepalive

```nginx
http {
    # Timeout connessione keepalive client
    keepalive_timeout 65;

    # Numero massimo richieste per connessione keepalive
    keepalive_requests 1000;
}
```

### Compressione Gzip

```nginx
http {
    gzip on;
    gzip_vary on;                    # Header Vary: Accept-Encoding
    gzip_proxied any;                # Comprimi anche risposte proxied
    gzip_comp_level 4;               # 1-9, 4 è buon compromesso CPU/ratio
    gzip_min_length 256;             # Non comprimere file < 256 byte
    gzip_buffers 16 8k;

    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/x-javascript
        application/xml
        application/xml+rss
        application/wasm
        image/svg+xml
        font/woff2;

    # NOTA: non comprimere immagini (jpg, png, gif) — già compresse
    # Non comprimere se il client non supporta gzip
}
```

### Buffer e timeout

```nginx
http {
    # Buffer per leggere l'header della richiesta client
    client_header_buffer_size 1k;
    large_client_header_buffers 4 8k;

    # Buffer per leggere il body della richiesta
    client_body_buffer_size 16k;
    client_max_body_size 10m;

    # Buffer per la risposta del backend
    proxy_buffer_size 4k;
    proxy_buffers 8 16k;
    proxy_busy_buffers_size 32k;

    # Timeout
    client_header_timeout 15;
    client_body_timeout 15;
    send_timeout 15;
    proxy_connect_timeout 60;
    proxy_read_timeout 60;
    proxy_send_timeout 60;
}
```

### Open file cache

```nginx
http {
    # Cache dei file descriptor aperti
    # Evita di riaprire gli stessi file ad ogni richiesta
    open_file_cache max=10000 inactive=20s;
    open_file_cache_valid 30s;
    open_file_cache_min_uses 2;
    open_file_cache_errors on;
}
```

### Benchmark rapido

```bash
# ab (Apache Benchmark)
ab -n 10000 -c 100 https://example.com/

# wrk (più moderno e accurato)
wrk -t4 -c100 -d30s https://example.com/

# hey (Go-based)
hey -n 10000 -c 100 https://example.com/

# Verificare limiti di sistema
ulimit -n           # File descriptor aperti
sysctl net.core.somaxconn
sysctl net.ipv4.tcp_max_syn_backlog
```

---

## Nginx: Sicurezza e Hardening

```nginx
# /etc/nginx/conf.d/security.conf

# Nascondere versione
server_tokens off;

# Security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "0" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;

# Limitare metodi HTTP
if ($request_method !~ ^(GET|HEAD|POST)$ ) {
    return 405;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=general:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;

# Limitare connessioni simultanee per IP
limit_conn_zone $binary_remote_addr zone=perip:10m;

# Limitare dimensione body
client_max_body_size 10m;

# Timeout stretti
client_body_timeout 12;
client_header_timeout 12;
send_timeout 10;
```

### Rate limiting in pratica

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;

    # Rate limit generico — 10 richieste/secondo, burst di 20
    location / {
        limit_req zone=general burst=20 nodelay;
        limit_conn perip 50;
        # ...
    }

    # Rate limit aggressivo per login — 1 richiesta/secondo
    location /login {
        limit_req zone=login burst=5 nodelay;
        limit_req_status 429;
        proxy_pass http://backend;
    }

    # Rate limit API — 30 richieste/secondo
    location /api/ {
        limit_req zone=api burst=50 nodelay;
        limit_req_status 429;
        proxy_pass http://api_backend;
    }
}
```

### Bloccare user-agent e bot

```nginx
# Bloccare bot e scanner noti
map $http_user_agent $bad_bot {
    default 0;
    ~*sqlmap 1;
    ~*nikto 1;
    ~*nmap 1;
    ~*masscan 1;
    ~*dirbuster 1;
    ~*gobuster 1;
    ~*wget 1;
    ~*curl 1;          # Attenzione: blocca anche uso legittimo
}

server {
    if ($bad_bot) {
        return 403;
    }
}
```

### Bloccare accesso per IP

```nginx
# Whitelist per admin panel
location /admin/ {
    allow 10.0.0.0/8;
    allow 192.168.1.0/24;
    deny all;
    proxy_pass http://backend;
}

# GeoIP blocking (richiede modulo ngx_http_geoip2)
# geoip2 /usr/share/GeoIP/GeoLite2-Country.mmdb {
#     $geoip2_country_code country iso_code;
# }
# if ($geoip2_country_code = "XX") { return 403; }
```

---

## Apache: Architettura e MPM

Apache HTTP Server utilizza moduli MPM (Multi-Processing Module) che determinano come il server gestisce le connessioni. La scelta dell'MPM influenza drasticamente performance e consumo di risorse.

### MPM Prefork

```
Client 1 ──→ [Processo 1 (dedicato)]
Client 2 ──→ [Processo 2 (dedicato)]
Client 3 ──→ [Processo 3 (dedicato)]
Client N ──→ [Processo N (dedicato)]
```

- **Un processo per connessione**, nessun thread
- **Thread-safe non richiesto** — necessario per mod_php (non thread-safe)
- **Consumo memoria alto** — ogni processo replica lo spazio di memoria
- **Uso:** hosting tradizionale con mod_php. Sconsigliato per nuovi deployment

```apache
# /etc/apache2/mods-available/mpm_prefork.conf
<IfModule mpm_prefork_module>
    StartServers             5
    MinSpareServers          5
    MaxSpareServers         10
    MaxRequestWorkers      256      # Connessioni simultanee massime
    MaxConnectionsPerChild 1000     # Restart worker dopo N richieste (leak prevention)
</IfModule>
```

### MPM Worker

```
                ┌─ Thread 1
Client 1+ ──→  [Processo 1] ├─ Thread 2
                ├─ Thread ...
                └─ Thread 25

                ┌─ Thread 1
Client N+ ──→  [Processo 2] ├─ Thread 2
                ├─ Thread ...
                └─ Thread 25
```

- **Multi-processo + multi-thread** — meno processi, più thread per processo
- **Consumo memoria ridotto** rispetto a prefork
- **Thread-safe richiesto** per i moduli (non compatibile con mod_php non thread-safe)
- **Uso:** applicazioni che usano PHP-FPM, Python via mod_wsgi thread-safe

```apache
<IfModule mpm_worker_module>
    StartServers             3
    MinSpareThreads         75
    MaxSpareThreads        250
    ThreadsPerChild         25
    MaxRequestWorkers      400      # = ServerLimit × ThreadsPerChild
    MaxConnectionsPerChild 1000
</IfModule>
```

### MPM Event

```
Connessioni keepalive ──→ [Thread dedicati listener]
                              │
                    Richiesta attiva → [Thread worker]
                    Keepalive idle  → [Non occupa thread]
```

- **Evoluzione di worker** — thread dedicati per connessioni keepalive
- **Le connessioni idle non occupano thread worker** — scalabilità migliore
- **Raccomandato** per nuove installazioni Apache
- **Default** in Apache 2.4+

```apache
<IfModule mpm_event_module>
    StartServers             3
    MinSpareThreads         75
    MaxSpareThreads        250
    ThreadsPerChild         25
    MaxRequestWorkers      400
    MaxConnectionsPerChild 1000
    AsyncRequestWorkerFactor 2       # Fattore per connessioni async
</IfModule>
```

### Cambiare MPM

```bash
# Verificare MPM attivo
apachectl -V | grep MPM
# Server MPM:     event

# Cambiare MPM (Debian/Ubuntu)
sudo a2dismod mpm_event
sudo a2enmod mpm_worker
sudo systemctl restart apache2

# Verificare moduli attivi
apachectl -M | grep mpm
```

---

## Apache: Fondamenti

```bash
# Installazione
sudo apt install apache2
sudo systemctl enable --now apache2

# File
/etc/apache2/apache2.conf             # Config principale
/etc/apache2/ports.conf               # Porte in ascolto
/etc/apache2/envvars                  # Variabili d'ambiente
/etc/apache2/sites-available/          # Siti disponibili
/etc/apache2/sites-enabled/            # Siti attivi
/etc/apache2/mods-available/           # Moduli disponibili
/etc/apache2/mods-enabled/             # Moduli attivi
/etc/apache2/conf-available/           # Config extra disponibili
/etc/apache2/conf-enabled/             # Config extra attive
/var/log/apache2/                      # Log

# Comandi
sudo apachectl configtest              # Test configurazione
sudo a2ensite example.com              # Abilita sito
sudo a2dissite 000-default             # Disabilita sito
sudo a2enmod rewrite ssl proxy         # Abilita moduli
sudo a2dismod status                   # Disabilita modulo
sudo a2enconf security                 # Abilita configurazione extra
sudo systemctl reload apache2
```

### .htaccess

Il file `.htaccess` permette configurazione distribuita a livello di directory, senza modificare la configurazione globale. Utile per shared hosting dove l'utente non ha accesso a `apache2.conf`.

```apache
# /var/www/example.com/.htaccess

# Redirect HTTP → HTTPS
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# Blocca accesso a file sensibili
<FilesMatch "\.(env|json|lock|md|gitignore|bak)$">
    Require all denied
</FilesMatch>

# Disabilita directory listing
Options -Indexes

# Cache per file statici
<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresByType image/jpeg "access plus 30 days"
    ExpiresByType image/png "access plus 30 days"
    ExpiresByType text/css "access plus 7 days"
    ExpiresByType application/javascript "access plus 7 days"
</IfModule>

# Custom error pages
ErrorDocument 404 /errors/404.html
ErrorDocument 500 /errors/500.html
```

**ATTENZIONE sulle performance:** `.htaccess` viene letto e processato ad ogni richiesta. In ambienti ad alte performance, disabilitarlo (`AllowOverride None`) e spostare le direttive nella configurazione del VirtualHost.

```apache
# Disabilitare .htaccess per performance
<Directory /var/www/example.com>
    AllowOverride None                 # Ignora .htaccess
    # Metti le direttive qui direttamente
</Directory>
```

---

## Apache: Virtual Host e Moduli

```apache
# /etc/apache2/sites-available/example.com.conf
<VirtualHost *:80>
    ServerName example.com
    ServerAlias www.example.com
    DocumentRoot /var/www/example.com
    ServerAdmin admin@example.com

    <Directory /var/www/example.com>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    ErrorLog ${APACHE_LOG_DIR}/example.com-error.log
    CustomLog ${APACHE_LOG_DIR}/example.com-access.log combined
</VirtualHost>
```

### Reverse Proxy con Apache

```apache
<VirtualHost *:80>
    ServerName app.example.com

    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:3000/
    ProxyPassReverse / http://127.0.0.1:3000/

    # WebSocket
    RewriteEngine On
    RewriteCond %{HTTP:Upgrade} websocket [NC]
    RewriteRule /(.*) ws://127.0.0.1:3000/$1 [P,L]
</VirtualHost>
```

```bash
# Moduli necessari per reverse proxy
sudo a2enmod proxy proxy_http proxy_wstunnel rewrite headers
sudo systemctl restart apache2
```

### Load Balancing con Apache

```apache
<Proxy "balancer://backend">
    BalancerMember http://10.0.0.1:8080 loadfactor=3
    BalancerMember http://10.0.0.2:8080 loadfactor=2
    BalancerMember http://10.0.0.3:8080 loadfactor=1
    
    # Algoritmo: byrequests (default), bytraffic, bybusyness
    ProxySet lbmethod=byrequests
    
    # Sticky sessions
    ProxySet stickysession=JSESSIONID
</Proxy>

<VirtualHost *:80>
    ServerName app.example.com
    ProxyPass / "balancer://backend/"
    ProxyPassReverse / "balancer://backend/"
</VirtualHost>
```

```bash
sudo a2enmod proxy proxy_http proxy_balancer lbmethod_byrequests
sudo systemctl restart apache2
```

---

## Apache: mod_rewrite

`mod_rewrite` è il modulo Apache per la riscrittura di URL. Potente ma complesso — molti lo definiscono "voodoo".

```apache
# Abilitare mod_rewrite
# sudo a2enmod rewrite

# Struttura base
RewriteEngine On
RewriteCond <test_string> <pattern> [flags]
RewriteRule <pattern> <substitution> [flags]
```

### Esempi pratici

```apache
# 1. Redirect www → non-www
RewriteEngine On
RewriteCond %{HTTP_HOST} ^www\.(.*)$ [NC]
RewriteRule ^(.*)$ https://%1/$1 [R=301,L]

# 2. Redirect non-www → www
RewriteEngine On
RewriteCond %{HTTP_HOST} !^www\. [NC]
RewriteRule ^(.*)$ https://www.%{HTTP_HOST}/$1 [R=301,L]

# 3. URL rewrite per framework (WordPress, Laravel, ecc.)
# Tutte le richieste a file/directory non esistenti → index.php
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ /index.php?q=$1 [L,QSA]

# 4. Forzare trailing slash
RewriteEngine On
RewriteCond %{REQUEST_URI} !/$ [NC]
RewriteCond %{REQUEST_FILENAME} !-f
RewriteRule ^(.*)$ /$1/ [R=301,L]

# 5. Bloccare hotlinking di immagini
RewriteEngine On
RewriteCond %{HTTP_REFERER} !^$
RewriteCond %{HTTP_REFERER} !^https?://(www\.)?example\.com [NC]
RewriteRule \.(jpg|jpeg|png|gif|webp)$ - [F,NC]

# 6. Redirect con regex — vecchie URL → nuove
RewriteEngine On
RewriteRule ^blog/([0-9]+)/(.*)$ /articoli/$1-$2 [R=301,L]
```

### Flag comuni di RewriteRule

| Flag | Significato |
|------|-------------|
| `[L]` | Last — stop processing rules |
| `[R=301]` | Redirect permanente |
| `[R=302]` | Redirect temporaneo |
| `[NC]` | No Case — case insensitive |
| `[QSA]` | Query String Append |
| `[P]` | Proxy — proxy interno |
| `[F]` | Forbidden — return 403 |
| `[G]` | Gone — return 410 |
| `[NE]` | No Escape — non URL-encode |

---

## Apache: mod_security

ModSecurity è un WAF (Web Application Firewall) disponibile come modulo Apache (e Nginx). Ispeziona le richieste HTTP in tempo reale e blocca attacchi comuni (SQL injection, XSS, RFI, ecc.).

```bash
# Installazione su Apache
sudo apt install libapache2-mod-security2
sudo a2enmod security2
sudo systemctl restart apache2

# File di configurazione
/etc/modsecurity/modsecurity.conf         # Config principale
/etc/modsecurity/modsecurity.conf-recommended  # Template
```

```bash
# Attivare ModSecurity (passa da DetectionOnly a On)
sudo cp /etc/modsecurity/modsecurity.conf-recommended \
        /etc/modsecurity/modsecurity.conf
sudo sed -i 's/SecRuleEngine DetectionOnly/SecRuleEngine On/' \
        /etc/modsecurity/modsecurity.conf
```

### OWASP Core Rule Set (CRS)

```bash
# Installare OWASP CRS
sudo apt install modsecurity-crs

# Oppure da GitHub per versione più recente
cd /etc/modsecurity
sudo git clone https://github.com/coreruleset/coreruleset.git crs
sudo cp crs/crs-setup.conf.example crs/crs-setup.conf

# Includere le regole nella config Apache
# /etc/apache2/mods-enabled/security2.conf
<IfModule security2_module>
    IncludeOptional /etc/modsecurity/*.conf
    IncludeOptional /etc/modsecurity/crs/crs-setup.conf
    IncludeOptional /etc/modsecurity/crs/rules/*.conf
</IfModule>
```

### Regole custom e whitelist

```apache
# Disabilitare una regola specifica (false positive)
SecRuleRemoveById 920350

# Whitelist per un path
<LocationMatch "/api/upload">
    SecRuleRemoveById 200002
    SecRequestBodyLimit 52428800    # 50MB per upload
</LocationMatch>

# Regola custom
SecRule ARGS:username "@rx (union|select|insert|drop|delete)" \
    "id:10001,phase:2,deny,status:403,msg:'SQL injection attempt'"
```

---

## Apache vs Nginx: Confronto

| Aspetto | Nginx | Apache |
|---------|-------|--------|
| **Architettura** | Event-driven, asincrono | Process/thread-based (MPM) |
| **Connessioni simultanee** | Eccellente (migliaia per worker) | Limitato (1 thread/processo per conn.) |
| **Memoria per connessione** | ~2-3 KB | ~10-20 KB (prefork: ~10 MB) |
| **File statici** | Superiore (sendfile, zero-copy) | Buono ma più lento |
| **Contenuto dinamico** | Proxy a backend (PHP-FPM, Gunicorn) | mod_php integrato (prefork) |
| **Configurazione** | File centralizzato, reload | .htaccess distribuito, per-directory |
| **Configurazione hot reload** | Sì (graceful reload) | Sì (graceful restart) |
| **.htaccess** | No | Sì |
| **Moduli** | Compilati staticamente (pre 1.9.11) / dinamici | Caricamento dinamico a runtime |
| **Reverse proxy** | Nativo, performante | Modulo (mod_proxy) |
| **Load balancing** | Nativo, multipli algoritmi | mod_proxy_balancer |
| **HTTP/2** | Nativo | mod_http2 |
| **HTTP/3** | Sperimentale (1.25+) | No (necessita mod esterno) |
| **SSL/TLS** | Integrato | mod_ssl |
| **Rewrite URL** | Direttive location/rewrite | mod_rewrite (regex completo) |
| **WAF** | ModSecurity (modulo dinamico) | ModSecurity (nativo) |
| **Curva apprendimento** | Moderata | Bassa (più documentazione) |
| **Uso CPU** | Basso sotto carico | Medio-alto sotto carico |
| **Caso d'uso ideale** | Reverse proxy, microservizi, API, container | Hosting tradizionale, shared hosting, CMS |

### Quando usare Nginx

- Reverse proxy per applicazioni backend (Node.js, Python, Go, Java)
- Serving di file statici ad alte performance
- Load balancing
- Architetture container e microservizi
- Alto numero di connessioni simultanee
- Terminazione SSL/TLS

### Quando usare Apache

- Hosting condiviso (shared hosting) dove serve `.htaccess`
- Applicazioni PHP tradizionali con mod_php
- Necessità di rewrite URL complesse con mod_rewrite
- Ecosistema di moduli specifici (mod_security, mod_pagespeed)
- Ambienti dove la configurazione per-directory è un requisito

### Combinazione Nginx + Apache

Un pattern comune è usare Nginx come reverse proxy davanti ad Apache:

```
Client → Nginx (SSL, static, cache) → Apache (PHP, mod_rewrite)
```

```nginx
# Nginx come frontend
server {
    listen 443 ssl http2;
    server_name example.com;

    # File statici serviti direttamente da Nginx
    location ~* \.(css|js|jpg|png|gif|ico|woff2)$ {
        root /var/www/example.com;
        expires 30d;
    }

    # Tutto il resto proxied ad Apache
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Caddy: Web Server con HTTPS Automatico

Caddy è un web server moderno scritto in Go, noto per la configurazione minimale e la gestione automatica dei certificati HTTPS tramite Let's Encrypt e ZeroSSL.

### Installazione

```bash
# Debian/Ubuntu
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | \
    sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | \
    sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install caddy

# Verifica
caddy version
sudo systemctl enable --now caddy
```

### Caddyfile — Configurazione

```caddyfile
# /etc/caddy/Caddyfile

# Sito statico con HTTPS automatico
example.com {
    root * /var/www/example.com
    file_server
    encode gzip

    # Log
    log {
        output file /var/log/caddy/example.com.access.log
    }

    # Security headers
    header {
        X-Frame-Options "SAMEORIGIN"
        X-Content-Type-Options "nosniff"
        Strict-Transport-Security "max-age=63072000"
        -Server                             # Rimuovi header Server
    }
}

# Reverse proxy — HTTPS automatico incluso
app.example.com {
    reverse_proxy localhost:3000
}

# Reverse proxy con load balancing
api.example.com {
    reverse_proxy {
        to 10.0.0.1:8080 10.0.0.2:8080 10.0.0.3:8080
        lb_policy least_conn
        health_uri /health
        health_interval 10s
    }
}

# Wildcard con DNS challenge (Cloudflare esempio)
*.example.com {
    tls {
        dns cloudflare {env.CF_API_TOKEN}
    }
    reverse_proxy localhost:8080
}

# Redirect www → non-www
www.example.com {
    redir https://example.com{uri} permanent
}
```

### Caddy come reverse proxy per PHP

```caddyfile
example.com {
    root * /var/www/example.com/public
    php_fastcgi unix//run/php/php8.3-fpm.sock
    file_server
    encode gzip
}
```

### Confronto Caddy vs Nginx

| Aspetto | Caddy | Nginx |
|---------|-------|-------|
| HTTPS | Automatico (Let's Encrypt/ZeroSSL) | Manuale (certbot) |
| Configurazione | Caddyfile (minimalista) | nginx.conf (verboso) |
| Performance | Buona | Eccellente |
| Estensibilità | Plugin Go | Moduli C/Lua |
| HTTP/3 | Nativo | Sperimentale |
| Consumo memoria | Medio (Go runtime) | Basso (C nativo) |
| Hot reload | Sì (`caddy reload`) | Sì (`nginx -s reload`) |
| API di gestione | REST API integrata | No (NGINX Plus sì) |
| Caso d'uso | Deployment semplici, dev, small-medium | Production ad alte performance |

### Caddy: Approfondimento Avanzato

#### API di Amministrazione JSON

Caddy espone un endpoint REST admin (default `localhost:2019`) che permette di ispezionare e modificare la configurazione a runtime senza restart. L'intera configurazione è rappresentata come un documento JSON navigabile:

```bash
# Visualizzare la configurazione corrente
curl http://localhost:2019/config/

# Aggiungere un nuovo sito a runtime
curl -X POST http://localhost:2019/config/apps/http/servers/srv0/routes \
  -H "Content-Type: application/json" \
  -d '{
    "match": [{"host": ["nuovo.example.com"]}],
    "handle": [{
      "handler": "reverse_proxy",
      "upstreams": [{"dial": "127.0.0.1:3000"}]
    }]
  }'

# Modificare un campo specifico tramite path traversal nell'API
curl -X PATCH http://localhost:2019/config/apps/http/servers/srv0/listen \
  -H "Content-Type: application/json" \
  -d '[":443", ":8443"]'

# Proteggere l'endpoint admin (FONDAMENTALE in produzione)
# In Caddyfile:
{
    admin off
    # oppure: admin 127.0.0.1:2019 {
    #     origins localhost
    # }
}
```

L'API è RESTful: ogni path nel JSON corrisponde a un percorso URL. Questa architettura consente automazione CI/CD, orchestrazione e integrazione con sistemi di service discovery senza toccare file di configurazione.

#### On-Demand TLS

On-Demand TLS permette a Caddy di ottenere certificati automaticamente al primo handshake TLS per un dominio, senza dichiararlo preventivamente. Essenziale per piattaforme SaaS multi-tenant dove i domini dei clienti non sono noti a priori:

```
{
    on_demand_tls {
        # Endpoint di autorizzazione: Caddy chiede "posso emettere per questo dominio?"
        # DEVE restituire HTTP 200 per autorizzare, qualsiasi altro codice rifiuta
        ask https://auth.internal.example.com/check-domain
        
        # Intervallo minimo tra richieste di certificato (anti-abuse)
        interval 5m
        burst 10
    }
}

https:// {
    tls {
        on_demand
    }
    reverse_proxy localhost:8080
}
```

**ATTENZIONE**: senza l'endpoint `ask`, un attaccante potrebbe esaurire i rate limit di Let's Encrypt/ZeroSSL facendo richieste a domini arbitrari che puntano al server. L'endpoint di autorizzazione è obbligatorio in produzione.

#### Estensioni con xcaddy

Caddy è modulare: i plugin si compilano staticamente nel binario tramite `xcaddy`:

```bash
# Installare xcaddy
go install github.com/caddyserver/xcaddy/cmd/xcaddy@latest

# Compilare Caddy con plugin specifici
xcaddy build \
    --with github.com/caddy-dns/cloudflare \
    --with github.com/caddyserver/cache-handler \
    --with github.com/mholt/caddy-dynamicdns \
    --with github.com/corazawaf/coraza-caddy/v2

# Il binario risultante include tutti i moduli
./caddy list-modules | grep -E "dns|cache|waf"
```

Plugin notevoli:
- **caddy-dns/cloudflare**: DNS challenge per certificati wildcard senza porta 80
- **cache-handler**: cache HTTP integrata nel reverse proxy
- **coraza-caddy**: WAF compatibile con regole ModSecurity/OWASP CRS
- **caddy-security**: autenticazione (SAML, OAuth2, MFA) integrata

#### Storage Backend per Certificati

In ambienti multi-istanza (cluster, auto-scaling), le istanze Caddy devono condividere i certificati per evitare richieste duplicate alle CA. Caddy supporta backend di storage distribuiti:

```json
{
  "storage": {
    "module": "consul",
    "address": "consul.internal:8500",
    "prefix": "caddy/certificates",
    "token": "${CONSUL_TOKEN}",
    "tls_enabled": true
  }
}
```

Backend supportati: filesystem (default), Consul, Redis, S3-compatibile, database SQL. In cluster Kubernetes, il backend Redis o S3 è la scelta standard per evitare conflitti ACME.

#### Caddy come Adattatore di Formato

Caddy può importare configurazioni da altri formati tramite adattatori:

```bash
# Convertire Caddyfile in JSON nativo
caddy adapt --config Caddyfile --adapter caddyfile

# Validare la configurazione senza applicarla
caddy validate --config Caddyfile --adapter caddyfile

# Formattare un Caddyfile (come gofmt per Go)
caddy fmt --overwrite Caddyfile
```

Il formato JSON nativo è più verboso ma permette manipolazione programmatica completa. Il Caddyfile è lo zucchero sintattico che copre l'80% dei casi d'uso. Per automazione CI/CD, generare JSON direttamente è spesso preferibile.

#### HTTP/3 in Caddy

Caddy abilita HTTP/3 (QUIC) automaticamente dalla versione 2.6+ senza configurazione aggiuntiva. Il server annuncia il supporto tramite l'header `Alt-Svc` nelle risposte HTTP/2:

```
# Header automatico nelle risposte
Alt-Svc: h3=":443"; ma=2592000

# Disabilitare HTTP/3 se necessario (raro)
{
    servers {
        protocols h1 h2
    }
}

# Abilitare solo su server specifici
https://veloce.example.com {
    servers {
        protocols h1 h2 h3
    }
    respond "QUIC attivo"
}
```

Requisiti: porta UDP 443 aperta nel firewall e nei security group cloud. Load balancer L4 (NLB su AWS, Network LB su GCP) per passthrough UDP. ALB/CLB non supportano UDP e terminano QUIC prima del backend.

---

## Traefik: Reverse Proxy Cloud-Native

Traefik è un reverse proxy e load balancer progettato per ambienti container (Docker, Kubernetes). La sua caratteristica principale è l'auto-discovery: rileva automaticamente i servizi e configura il routing senza file di configurazione manuali.

### Installazione con Docker Compose

```yaml
# docker-compose.yml
services:
  traefik:
    image: traefik:v3.1
    container_name: traefik
    restart: unless-stopped
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      # Let's Encrypt automatico
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      # Redirect HTTP → HTTPS
      - "--entrypoints.web.http.redirections.entryPoint.to=websecure"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - traefik-letsencrypt:/letsencrypt
    labels:
      # Dashboard Traefik
      - "traefik.enable=true"
      - "traefik.http.routers.dashboard.rule=Host(`traefik.example.com`)"
      - "traefik.http.routers.dashboard.service=api@internal"
      - "traefik.http.routers.dashboard.tls.certresolver=letsencrypt"
      # Basic auth per dashboard
      - "traefik.http.routers.dashboard.middlewares=auth"
      - "traefik.http.middlewares.auth.basicauth.users=admin:$$apr1$$..."

volumes:
  traefik-letsencrypt:
```

### Auto-discovery con Docker labels

```yaml
# Servizio backend che Traefik scopre automaticamente
services:
  webapp:
    image: myapp:latest
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.webapp.rule=Host(`app.example.com`)"
      - "traefik.http.routers.webapp.tls.certresolver=letsencrypt"
      - "traefik.http.services.webapp.loadbalancer.server.port=3000"
      # Rate limiting middleware
      - "traefik.http.middlewares.webapp-ratelimit.ratelimit.average=100"
      - "traefik.http.middlewares.webapp-ratelimit.ratelimit.burst=50"
      - "traefik.http.routers.webapp.middlewares=webapp-ratelimit"
```

### Traefik con file provider (senza Docker)

```yaml
# /etc/traefik/traefik.yml
entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"

providers:
  file:
    directory: /etc/traefik/conf.d/
    watch: true

certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@example.com
      storage: /etc/traefik/acme.json
      tlsChallenge: {}
```

```yaml
# /etc/traefik/conf.d/services.yml
http:
  routers:
    app-router:
      rule: "Host(`app.example.com`)"
      service: app-service
      tls:
        certResolver: letsencrypt

  services:
    app-service:
      loadBalancer:
        servers:
          - url: "http://10.0.0.1:8080"
          - url: "http://10.0.0.2:8080"
        healthCheck:
          path: /health
          interval: 10s
          timeout: 3s
```

### Traefik: Kubernetes e Middleware Avanzati

#### Deploy su Kubernetes con Helm

Traefik 3 è il controller ingress predefinito di K3s e ampiamente adottato in cluster Kubernetes di produzione. L'installazione avviene tramite Helm chart ufficiale:

```bash
# Aggiungere il repository Helm di Traefik
helm repo add traefik https://traefik.github.io/charts
helm repo update

# Installare con valori personalizzati
helm install traefik traefik/traefik \
  --namespace traefik \
  --create-namespace \
  --set ports.web.redirectTo.port=websecure \
  --set ports.websecure.tls.enabled=true \
  --set ingressRoute.dashboard.enabled=true \
  --set providers.kubernetesIngress.enabled=true \
  --set providers.kubernetesCRD.enabled=true \
  --set certificatesResolvers.letsencrypt.acme.email=admin@example.com \
  --set certificatesResolvers.letsencrypt.acme.storage=/data/acme.json \
  --set certificatesResolvers.letsencrypt.acme.tlsChallenge=true

# Verificare il deploy
kubectl get pods -n traefik
kubectl get svc -n traefik
```

#### IngressRoute CRD

Traefik definisce Custom Resource Definitions (CRD) proprie che offrono maggiore flessibilità rispetto all'oggetto Ingress standard di Kubernetes:

```yaml
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: app-ingress
  namespace: production
spec:
  entryPoints:
    - websecure
  routes:
    - match: Host(`app.example.com`) && PathPrefix(`/api`)
      kind: Rule
      services:
        - name: api-service
          port: 8080
          weight: 100
      middlewares:
        - name: rate-limit
        - name: circuit-breaker
        - name: retry-middleware
    - match: Host(`app.example.com`)
      kind: Rule
      services:
        - name: frontend-service
          port: 3000
  tls:
    certResolver: letsencrypt
    domains:
      - main: app.example.com
        sans:
          - "*.app.example.com"
```

#### Catena di Middleware

I middleware Traefik si compongono in catena. L'ordine di dichiarazione determina l'ordine di esecuzione:

```yaml
# Rate Limiting
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: rate-limit
spec:
  rateLimit:
    average: 100            # Richieste medie al secondo
    burst: 200              # Picco massimo
    period: 1s
    sourceCriterion:
      ipStrategy:
        depth: 1            # Primo IP da X-Forwarded-For
---
# Circuit Breaker con espressione
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: circuit-breaker
spec:
  circuitBreaker:
    expression: "ResponseCodeRatio(500, 600, 0, 600) > 0.30"
    checkPeriod: 10s
    fallbackDuration: 30s
    recoveryDuration: 60s
---
# Retry con backoff esponenziale
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: retry-middleware
spec:
  retry:
    attempts: 3
    initialInterval: 100ms
```

Il **circuit breaker** di Traefik 3 usa espressioni condizionali: `ResponseCodeRatio(500, 600, 0, 600) > 0.30` significa "apri il circuito se oltre il 30% delle risposte è 5xx". Quando il circuito si apre, Traefik restituisce `503 Service Unavailable` per `fallbackDuration` secondi, poi tenta il recovery graduale.

Il **retry middleware** ritenta automaticamente le richieste fallite con backoff esponenziale. L'intervallo iniziale raddoppia a ogni tentativo (100ms → 200ms → 400ms). Si applica solo a errori di rete e 5xx, mai a 4xx.

#### Weighted Round Robin e Canary Deploy

Traefik supporta weighted round robin nativo per deploy canary e blue-green:

```yaml
apiVersion: traefik.io/v1alpha1
kind: TraefikService
metadata:
  name: canary-service
spec:
  weighted:
    services:
      - name: app-stable
        port: 8080
        weight: 90        # 90% traffico alla versione stabile
      - name: app-canary
        port: 8080
        weight: 10        # 10% traffico alla nuova versione
    sticky:
      cookie:
        name: canary_session
        secure: true
        httpOnly: true
```

#### Traefik Hub e API Gateway

Traefik Hub estende Traefik open-source con funzionalità API gateway enterprise: API portal, versioning, rate limiting per API key, OpenAPI spec validation, e metriche per endpoint. L'integrazione avviene tramite un token di registrazione senza modificare l'infrastruttura esistente.

#### Osservabilità e Metriche Traefik

Traefik espone metriche native in formato Prometheus e supporta tracing distribuito:

```yaml
# values.yaml per Helm — metriche e tracing
metrics:
  prometheus:
    entryPoint: metrics
    addEntryPointsLabels: true
    addRoutersLabels: true
    addServicesLabels: true
    buckets: "0.01,0.05,0.1,0.3,0.5,1.0,3.0,5.0"

tracing:
  otlp:
    http:
      endpoint: "http://otel-collector:4318/v1/traces"
    grpc:
      endpoint: "otel-collector:4317"
      insecure: true

# Dashboard accessibile via IngressRoute (proteggere con middleware auth)
ingressRoute:
  dashboard:
    enabled: true
    matchRule: Host(`traefik.internal.example.com`)
    middlewares:
      - name: basic-auth
```

```yaml
# Middleware di autenticazione per il dashboard
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: basic-auth
spec:
  basicAuth:
    secret: traefik-dashboard-auth
    # htpasswd -nB admin > auth-secret
    # kubectl create secret generic traefik-dashboard-auth \
    #   --from-file=users=auth-secret -n traefik
```

Metriche chiave da monitorare in Grafana:
- `traefik_entrypoint_requests_total`: throughput per entrypoint
- `traefik_service_request_duration_seconds_bucket`: latenza per servizio (istogramma)
- `traefik_service_requests_total{code="5xx"}`: tasso di errori 5xx per servizio
- `traefik_entrypoint_open_connections`: connessioni concorrenti attive

Il dashboard Grafana ufficiale (ID 17346) fornisce una vista completa di tutte queste metriche con pannelli preconfigurati per throughput, latenza percentile, e tasso di errori per servizio.

#### Migrazione da Nginx/HAProxy a Traefik

Considerazioni pratiche per la migrazione:

| Aspetto | Nginx → Traefik | HAProxy → Traefik |
|---------|----------------|-------------------|
| Configurazione | Da file statico a label/CRD dinamiche | Da config statica a auto-discovery |
| SSL/TLS | Da certbot manuale a ACME automatico | Da certbot a ACME automatico |
| Health check | Da passivo a attivo nativo | Equivalente (entrambi attivi) |
| Sticky session | Da `ip_hash`/`sticky` a cookie middleware | Da `cookie` a cookie middleware |
| Rate limiting | Da `limit_req` a middleware CRD | Da `stick-table` a middleware CRD |
| Complessità | Media — il mapping non è 1:1 | Bassa — concetti simili |
| Quando migrare | Ambiente containerizzato, molti servizi | Servizi K8s, auto-discovery necessario |
| Quando restare | Alte performance statiche, config stabile | Requisiti L4, sticky avanzato, ACL complesse |

La migrazione è consigliata quando l'infrastruttura si sposta verso container e orchestratori. Per workload statici su VM tradizionali, Nginx e HAProxy restano scelte più appropriate per la loro maturità e performance.

---

## HAProxy: Load Balancer TCP/HTTP

HAProxy (High Availability Proxy) è il load balancer open-source più utilizzato per ambienti ad alte performance. Opera sia a livello TCP (Layer 4) che HTTP (Layer 7).

### Installazione

```bash
sudo apt install haproxy
sudo systemctl enable --now haproxy

# Versione
haproxy -v

# File
/etc/haproxy/haproxy.cfg             # Configurazione
/var/log/haproxy.log                  # Log (via rsyslog)
```

### Configurazione base

```
# /etc/haproxy/haproxy.cfg

global
    log /dev/log local0
    log /dev/log local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    user haproxy
    group haproxy
    daemon
    maxconn 50000

    # SSL
    ssl-default-bind-ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256
    ssl-default-bind-options ssl-min-ver TLSv1.2 no-tls-tickets

defaults
    log     global
    mode    http
    option  httplog
    option  dontlognull
    option  http-server-close
    option  forwardfor except 127.0.0.0/8
    timeout connect 5s
    timeout client  30s
    timeout server  30s
    timeout http-keep-alive 10s
    timeout http-request 10s
    errorfile 400 /etc/haproxy/errors/400.http
    errorfile 403 /etc/haproxy/errors/403.http
    errorfile 502 /etc/haproxy/errors/502.http
    errorfile 503 /etc/haproxy/errors/503.http

# Pagina statistiche
listen stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 10s
    stats admin if LOCALHOST

# Frontend HTTP
frontend http_front
    bind *:80
    # Redirect a HTTPS
    http-request redirect scheme https unless { ssl_fc }

# Frontend HTTPS (SSL termination)
frontend https_front
    bind *:443 ssl crt /etc/haproxy/certs/example.com.pem
    
    # Routing basato su hostname
    acl is_api hdr(host) -i api.example.com
    acl is_app hdr(host) -i app.example.com
    
    use_backend api_servers if is_api
    use_backend app_servers if is_app
    default_backend web_servers

# Backend web
backend web_servers
    balance roundrobin
    option httpchk GET /health
    http-check expect status 200
    
    server web1 10.0.0.1:8080 check inter 5s fall 3 rise 2
    server web2 10.0.0.2:8080 check inter 5s fall 3 rise 2
    server web3 10.0.0.3:8080 check inter 5s fall 3 rise 2 backup

# Backend API
backend api_servers
    balance leastconn
    option httpchk GET /api/health
    
    server api1 10.0.1.1:3000 check inter 5s fall 3 rise 2
    server api2 10.0.1.2:3000 check inter 5s fall 3 rise 2

# Backend applicazione
backend app_servers
    balance source                     # Sticky sessions (hash IP)
    cookie SERVERID insert indirect nocache
    
    server app1 10.0.2.1:8080 check cookie s1
    server app2 10.0.2.2:8080 check cookie s2
```

### Health checks HAProxy

```
backend web_servers
    # Health check HTTP
    option httpchk GET /health
    http-check expect status 200

    # Parametri check
    # inter   = intervallo tra check (default 2s)
    # fall    = check falliti prima di marcare down
    # rise    = check riusciti prima di marcare up
    # weight  = peso nel load balancing
    server web1 10.0.0.1:8080 check inter 3s fall 3 rise 2 weight 100
    server web2 10.0.0.2:8080 check inter 3s fall 3 rise 2 weight 50
```

### HAProxy per TCP (Layer 4) — esempio database

```
frontend mysql_front
    bind *:3306
    mode tcp
    default_backend mysql_servers

backend mysql_servers
    mode tcp
    balance roundrobin
    option mysql-check user haproxy
    server db1 10.0.3.1:3306 check
    server db2 10.0.3.2:3306 check backup
```

### Verifica configurazione

```bash
# Validare config
haproxy -c -f /etc/haproxy/haproxy.cfg

# Reload senza downtime
sudo systemctl reload haproxy

# Statistiche via socket
echo "show stat" | sudo socat stdio /run/haproxy/admin.sock
echo "show servers state" | sudo socat stdio /run/haproxy/admin.sock

# Disabilitare un server per manutenzione
echo "set server web_servers/web1 state maint" | \
    sudo socat stdio /run/haproxy/admin.sock
```

---

## Virtual Hosts: Name-Based, IP-Based, SNI

I virtual host permettono a un singolo web server di servire più siti web sulla stessa macchina.

### Name-Based Virtual Hosting

Il metodo più comune. Il server determina quale sito servire in base all'header `Host` della richiesta HTTP.

```nginx
# Nginx — name-based virtual hosting
server {
    listen 80;
    server_name sito-a.com www.sito-a.com;
    root /var/www/sito-a;
}

server {
    listen 80;
    server_name sito-b.com www.sito-b.com;
    root /var/www/sito-b;
}

# Default server (richieste senza Host valido)
server {
    listen 80 default_server;
    server_name _;
    return 444;                        # Chiudi connessione senza risposta
}
```

```apache
# Apache — name-based virtual hosting
<VirtualHost *:80>
    ServerName sito-a.com
    ServerAlias www.sito-a.com
    DocumentRoot /var/www/sito-a
</VirtualHost>

<VirtualHost *:80>
    ServerName sito-b.com
    ServerAlias www.sito-b.com
    DocumentRoot /var/www/sito-b
</VirtualHost>
```

### IP-Based Virtual Hosting

Ogni sito ha un indirizzo IP dedicato. Usato quando il name-based non è possibile (es. certificati SSL legacy, protocolli non-HTTP).

```nginx
# Nginx — IP-based
server {
    listen 10.0.0.1:80;
    server_name sito-a.com;
    root /var/www/sito-a;
}

server {
    listen 10.0.0.2:80;
    server_name sito-b.com;
    root /var/www/sito-b;
}
```

```bash
# Aggiungere IP aggiuntivi all'interfaccia
sudo ip addr add 10.0.0.2/24 dev eth0
```

### SNI (Server Name Indication)

SNI è un'estensione di TLS che permette virtual hosting basato su nome anche con HTTPS. Il client invia il nome del server durante l'handshake TLS, permettendo al server di presentare il certificato corretto.

```nginx
# Nginx — SNI (funziona nativamente con name-based + SSL)
server {
    listen 443 ssl http2;
    server_name sito-a.com;
    ssl_certificate /etc/letsencrypt/live/sito-a.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sito-a.com/privkey.pem;
    root /var/www/sito-a;
}

server {
    listen 443 ssl http2;
    server_name sito-b.com;
    ssl_certificate /etc/letsencrypt/live/sito-b.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/sito-b.com/privkey.pem;
    root /var/www/sito-b;
}
```

**Compatibilità SNI:** tutti i browser moderni supportano SNI. Client legacy senza SNI riceveranno il certificato del `default_server`.

```bash
# Verifica supporto SNI
openssl s_client -connect example.com:443 -servername sito-a.com
openssl s_client -connect example.com:443 -servername sito-b.com
```

---

## Certificati TLS/SSL: Tipologie e CA

### Tipologie di certificati

| Tipo | Validazione | Tempo | Costo | Uso |
|------|------------|-------|-------|-----|
| **DV** (Domain Validation) | Solo proprietà del dominio | Minuti | Gratuito (LE) – basso | Blog, siti personali, API |
| **OV** (Organization Validation) | Verifica organizzazione | 1-3 giorni | Medio | Aziende, e-commerce |
| **EV** (Extended Validation) | Verifica legale completa | 1-2 settimane | Alto | Banche, finanza, governo |
| **Wildcard** | `*.example.com` | Come DV/OV | Varia | Multi-subdomain |
| **SAN/UCC** | Multi-dominio in un cert | Come DV/OV | Varia | Più domini sullo stesso server |
| **Self-signed** | Nessuna CA | Istantaneo | Gratuito | Solo test/sviluppo |

### Gerarchia CA e catena di fiducia

```
Root CA (CA radice)
   │
   ├── Certificato root preinstallato nel browser/OS
   │   (trust store)
   │
   └── Intermediate CA (CA intermedia)
        │
        ├── Certificato intermedio (chain.pem)
        │
        └── Certificato del dominio (cert.pem)
             │
             └── Server presenta: cert.pem + chain.pem = fullchain.pem
```

**Perché la catena è importante:** il browser si fida solo dei root CA nel suo trust store. Il certificato del dominio è firmato da una CA intermedia. Se il server non presenta il certificato intermedio, il browser non può verificare la catena di fiducia → errore SSL.

### Troubleshooting certificati

```bash
# Verifica catena completa
openssl s_client -connect example.com:443 -showcerts 2>/dev/null | \
    openssl x509 -noout -subject -issuer -dates

# Verifica il certificato locale
openssl x509 -in /etc/letsencrypt/live/example.com/fullchain.pem \
    -noout -text | head -30

# Verifica scadenza
openssl x509 -in /etc/letsencrypt/live/example.com/cert.pem \
    -noout -enddate

# Verifica che cert e key corrispondano
openssl x509 -noout -modulus -in cert.pem | openssl md5
openssl rsa -noout -modulus -in privkey.pem | openssl md5
# I due hash DEVONO essere identici

# Verifica catena
openssl verify -CAfile chain.pem cert.pem

# Decodifica CSR
openssl req -in request.csr -noout -text

# Test online
# https://www.ssllabs.com/ssltest/
# https://www.sslshopper.com/ssl-checker.html
```

### Certificato con SAN (Subject Alternative Names)

```bash
# Generare CSR con SAN multipli
openssl req -new -newkey rsa:2048 -nodes \
    -keyout privkey.pem -out request.csr \
    -subj "/CN=example.com" \
    -addext "subjectAltName=DNS:example.com,DNS:www.example.com,DNS:api.example.com"
```

---

## Certbot e Let's Encrypt

```bash
# Installazione
sudo apt install certbot python3-certbot-nginx    # Per Nginx
sudo apt install certbot python3-certbot-apache   # Per Apache

# Ottenere certificato (Nginx)
sudo certbot --nginx -d example.com -d www.example.com

# Ottenere certificato (Apache)
sudo certbot --apache -d example.com -d www.example.com

# Solo certificato (senza configurare il web server)
sudo certbot certonly --standalone -d example.com
sudo certbot certonly --webroot -w /var/www/example.com -d example.com

# Rinnovo
sudo certbot renew --dry-run          # Test rinnovo
sudo certbot renew                    # Rinnovo effettivo

# Rinnovo automatico (già configurato da certbot)
systemctl list-timers | grep certbot
# O in cron: 0 0,12 * * * certbot renew --quiet

# Revocare
sudo certbot revoke --cert-name example.com

# Wildcard (richiede DNS challenge)
sudo certbot certonly --manual --preferred-challenges dns -d '*.example.com'
```

### Certbot con DNS challenge automatizzato

```bash
# Cloudflare DNS plugin
sudo apt install python3-certbot-dns-cloudflare

# Credenziali Cloudflare
cat > /etc/letsencrypt/cloudflare.ini << 'EOF'
dns_cloudflare_api_token = YOUR_API_TOKEN_HERE
EOF
chmod 600 /etc/letsencrypt/cloudflare.ini

# Wildcard con DNS challenge automatico
sudo certbot certonly \
    --dns-cloudflare \
    --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini \
    -d '*.example.com' \
    -d example.com
```

### Hook post-rinnovo

```bash
# Ricaricare il web server dopo il rinnovo
sudo certbot renew \
    --deploy-hook "systemctl reload nginx"

# Oppure configurare permanentemente
# /etc/letsencrypt/renewal-hooks/deploy/reload-nginx.sh
#!/bin/bash
systemctl reload nginx
```

### Limiti Let's Encrypt

| Limite | Valore |
|--------|--------|
| Certificati per dominio registrato | 50/settimana |
| Nomi per certificato (SAN) | 100 |
| Richieste di autorizzazione fallite | 5/ora/account/hostname |
| Certificati duplicati | 5/settimana |
| Validità certificato | 90 giorni |

---

## HTTP/2 e HTTP/3 (QUIC)

### HTTP/2

HTTP/2 (RFC 7540/9113) introduce miglioramenti fondamentali rispetto a HTTP/1.1:

- **Multiplexing:** più richieste/risposte sulla stessa connessione TCP, senza head-of-line blocking a livello applicativo
- **Header compression (HPACK):** riduce overhead degli header ripetitivi
- **Server Push:** il server può inviare risorse prima che il client le richieda (deprecato nella pratica)
- **Binary protocol:** parsing più efficiente rispetto al formato testo di HTTP/1.1
- **Stream prioritization:** il client può indicare la priorità delle risorse

```nginx
# Nginx — HTTP/2
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    # ...
}
```

```apache
# Apache — HTTP/2
# sudo a2enmod http2
<VirtualHost *:443>
    Protocols h2 http/1.1
    ServerName example.com
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/example.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/example.com/privkey.pem
</VirtualHost>
```

### HTTP/3 (QUIC)

HTTP/3 (RFC 9114) usa QUIC (RFC 9000) al posto di TCP come protocollo di trasporto. QUIC è basato su UDP e include TLS 1.3 integrato.

Vantaggi principali:
- **Zero RTT connection establishment** (0-RTT): connessione quasi istantanea per client che si riconnettono
- **Nessun head-of-line blocking a livello di trasporto**: la perdita di un pacchetto non blocca gli altri stream
- **Connection migration**: la connessione sopravvive al cambio di rete (es. Wi-Fi → 4G)
- **TLS 1.3 integrato**: handshake più veloce

```nginx
# Nginx — HTTP/3 (richiede nginx 1.25+)
server {
    # HTTP/2 su TCP
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;

    # HTTP/3 su QUIC/UDP
    listen 443 quic reuseport;
    listen [::]:443 quic reuseport;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    # Informare il client che HTTP/3 è disponibile
    add_header Alt-Svc 'h3=":443"; ma=86400' always;

    # TLS 1.3 obbligatorio per QUIC
    ssl_protocols TLSv1.2 TLSv1.3;

    # ...
}
```

```bash
# Verificare supporto HTTP/2
curl -sI --http2 https://example.com | grep -i "http/"
# HTTP/2 200

# Verificare supporto HTTP/3
curl --http3 https://example.com -I
# HTTP/3 200

# Aprire porta UDP 443 nel firewall per QUIC
sudo ufw allow 443/udp
# oppure
sudo iptables -A INPUT -p udp --dport 443 -j ACCEPT
```

### Confronto protocolli

| Aspetto | HTTP/1.1 | HTTP/2 | HTTP/3 |
|---------|----------|--------|--------|
| Trasporto | TCP | TCP | QUIC (UDP) |
| Multiplexing | No (pipeline limitato) | Sì | Sì |
| Head-of-line blocking | Sì (TCP + HTTP) | Parziale (solo TCP) | No |
| Compressione header | No | HPACK | QPACK |
| Handshake | TCP + TLS (2-3 RTT) | TCP + TLS (2-3 RTT) | 1 RTT (0-RTT repeat) |
| Crittografia | Opzionale | Praticamente obbligatoria | Obbligatoria (TLS 1.3) |
| Connection migration | No | No | Sì |
| Compatibilità | Universale | ~97% browser | ~95% browser |

### Configurazione Avanzata HTTP/3 e QUIC

#### Nginx: Tuning QUIC Avanzato

A partire da Nginx 1.25.0 il supporto QUIC è integrato nel core (non più sperimentale). Con Nginx 1.27.5 è stato introdotto il controllo di congestione CUBIC per QUIC, migliorando le performance su connessioni ad alta latenza:

```nginx
server {
    # Abilitare HTTP/3 con QUIC
    listen 443 quic reuseport;        # UDP per QUIC
    listen 443 ssl;                    # TCP per HTTP/1.1 e HTTP/2
    http2 on;

    server_name example.com;

    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    # QUIC tuning avanzato
    quic_retry on;                     # Validazione indirizzo client (anti-spoofing)
    quic_gso on;                       # Generic Segmentation Offload (performance)
    
    # TLS 1.3 obbligatorio per QUIC
    ssl_protocols TLSv1.3;
    
    # 0-RTT (Early Data) per connessioni ripetute
    ssl_early_data on;
    # ATTENZIONE: 0-RTT è vulnerabile a replay attack
    # Usare solo per richieste GET idempotenti
    # Il backend deve verificare l'header Early-Data
    proxy_set_header Early-Data $ssl_early_data;
    
    # Annunciare HTTP/3 ai client
    add_header Alt-Svc 'h3=":443"; ma=86400' always;
    
    # Dimensione finestra di congestione iniziale
    # Nginx 1.27.5+: supporto CUBIC (default: Reno)
    # Il cambio avviene a livello di compilazione con --with-cc-opt
    
    location / {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
}
```

**Nota su Nginx 1.27.x**: la versione 1.27.3 ha disabilitato TLSv1 e TLSv1.1 per default. La direttiva `ssl_protocols` non li include più automaticamente. Nginx 1.28.0, rilasciato ad aprile 2025, è ora la versione stabile corrente.

#### Considerazioni di Rete per QUIC

QUIC utilizza UDP sulla porta 443, il che introduce problematiche specifiche a livello di infrastruttura:

```
Requisiti infrastrutturali per HTTP/3:

1. FIREWALL
   - Aprire UDP 443 in ingresso (iptables, nftables, ufw)
   - Molti firewall aziendali bloccano UDP 443 per default
   - Verificare: sudo ss -ulnp | grep 443

2. LOAD BALANCER
   ┌──────────────────────────────────────────────────┐
   │ Tipo              │ Supporto QUIC               │
   ├───────────────────┼─────────────────────────────┤
   │ AWS NLB (L4)      │ Sì (passthrough UDP)        │
   │ AWS ALB (L7)      │ No (solo TCP)               │
   │ GCP Network LB    │ Sì (passthrough UDP)        │
   │ GCP HTTPS LB      │ Sì (termina QUIC)           │
   │ Cloudflare        │ Sì (termina e ri-origina)   │
   │ HAProxy           │ No (solo TCP/HTTP)           │
   └──────────────────────────────────────────────────┘

3. FAILOVER
   - I client HTTP/3 tentano QUIC e fallback a HTTP/2 dopo timeout
   - Il timeout di fallback varia: Chrome ~300ms, Firefox ~3s
   - Testare sempre che il fallback TCP funzioni correttamente

4. MTU E FRAMMENTAZIONE
   - QUIC gestisce il path MTU discovery internamente
   - Alcuni middlebox bloccano pacchetti UDP > 1280 byte
   - In caso di problemi: verificare con traceroute UDP
```

#### Performance HTTP/3 vs HTTP/2

I benefici principali di HTTP/3 emergono in scenari specifici:
- **Reti mobili**: eliminazione head-of-line blocking TCP migliora la latenza percepita del 15-30%
- **Connection migration**: cambio WiFi↔cellulare senza interruzione della connessione
- **Alta latenza**: 0-RTT riduce il tempo di setup da 2-3 RTT a 0-1 RTT per connessioni ripetute
- **Packet loss**: QUIC gestisce la perdita per singolo stream, non per l'intera connessione

Su reti a bassa latenza e basso packet loss (datacenter, fibra), la differenza HTTP/3 vs HTTP/2 è trascurabile (<5%). Valutare il deploy HTTP/3 primariamente per audience mobile o geograficamente distribuita.

---

## Web Application Firewall (WAF)

Un WAF ispeziona il traffico HTTP/HTTPS e blocca richieste malevole basandosi su regole predefinite. Opera a Layer 7 (applicativo) e protegge da attacchi come SQL injection, XSS, command injection, path traversal.

### ModSecurity con Nginx

```bash
# Installazione ModSecurity per Nginx (compilare come modulo dinamico)
# Su Debian/Ubuntu può essere disponibile come pacchetto
sudo apt install libnginx-mod-http-modsecurity

# Oppure compilare da sorgente
# git clone https://github.com/owasp-modsecurity/ModSecurity
# git clone https://github.com/owasp-modsecurity/ModSecurity-nginx
```

```nginx
# /etc/nginx/nginx.conf o conf.d/modsecurity.conf
modsecurity on;
modsecurity_rules_file /etc/nginx/modsecurity/main.conf;
```

```
# /etc/nginx/modsecurity/main.conf
SecRuleEngine On
SecRequestBodyAccess On
SecRequestBodyLimit 13107200
SecRequestBodyNoFilesLimit 131072
SecResponseBodyAccess Off

# Logging
SecAuditEngine RelevantOnly
SecAuditLogRelevantStatus "^(?:5|4(?!04))"
SecAuditLog /var/log/nginx/modsec_audit.log

# Includere OWASP CRS
Include /etc/nginx/modsecurity/crs/crs-setup.conf
Include /etc/nginx/modsecurity/crs/rules/*.conf
```

### OWASP Core Rule Set (CRS)

Il CRS fornisce protezione contro le categorie di attacco OWASP Top 10:

```bash
# Installazione CRS
cd /etc/nginx/modsecurity/
sudo git clone https://github.com/coreruleset/coreruleset.git crs
sudo cp crs/crs-setup.conf.example crs/crs-setup.conf
```

### Paranoia Level

Il CRS offre 4 livelli di paranoia che determinano l'aggressività delle regole:

| Livello | Descrizione | False positivi |
|---------|-------------|----------------|
| PL1 | Base — minimo falsi positivi | Basso |
| PL2 | Moderato — copertura aggiuntiva | Medio |
| PL3 | Elevato — molte più regole | Alto |
| PL4 | Paranoico — massima copertura | Molto alto |

```
# crs-setup.conf
SecAction "id:900000,phase:1,pass,t:none,nolog,\
    setvar:tx.paranoia_level=2"
```

### Coraza — WAF alternativo

Coraza è un WAF open-source compatibile con le regole ModSecurity, scritto in Go. Più moderno e facile da integrare rispetto a ModSecurity.

```bash
# Installazione come modulo Nginx (via Coraza Caddy/Nginx plugin)
# O standalone come reverse proxy
```

### Esclusione regole per false positivi

```
# Escludere una regola per un path specifico
SecRule REQUEST_URI "@beginsWith /api/upload" \
    "id:1001,phase:1,pass,nolog,ctl:ruleRemoveById=920350"

# Escludere un parametro dalla validazione
SecRule ARGS:token "@rx ^[a-zA-Z0-9+/=]+$" \
    "id:1002,phase:2,pass,nolog,ctl:ruleRemoveTargetById=942100;ARGS:token"
```

### ModSecurity 3 e OWASP CRS 4: Approfondimento

#### Meccanismo di Anomaly Scoring

CRS 4 utilizza un sistema di punteggio anomalia anziché bloccare alla prima regola violata. Ogni regola assegna un punteggio (2-5 punti) e il blocco avviene solo quando il totale supera una soglia configurabile:

```
# /etc/modsecurity/crs/crs-setup.conf

# Soglie di anomaly scoring
# Inbound: punteggio accumulato dalle regole di richiesta
SecAction "id:900110,phase:1,pass,nolog,\
  setvar:tx.inbound_anomaly_score_threshold=5"

# Outbound: punteggio accumulato dalle regole di risposta
SecAction "id:900111,phase:1,pass,nolog,\
  setvar:tx.outbound_anomaly_score_threshold=4"

# Punteggi per severità
# CRITICAL (SQL injection, RCE)     = 5 punti
# ERROR (XSS, path traversal)       = 4 punti
# WARNING (sospetto, non confermato) = 3 punti
# NOTICE (informativo)              = 2 punti
```

Con soglia `inbound_anomaly_score_threshold=5`, una singola regola CRITICAL blocca la richiesta. Con soglia `10`, servono due CRITICAL o combinazioni di severità inferiori. Per ambienti ad alta sensibilità (banking, healthcare), usare soglia 5. Per applicazioni con molto contenuto generato dagli utenti (forum, CMS), iniziare con soglia 10-15 e ridurre gradualmente.

#### Livelli di Paranoia (PL)

CRS definisce 4 livelli di paranoia che attivano progressivamente più regole:

```
# Livello di paranoia in crs-setup.conf
SecAction "id:900000,phase:1,pass,nolog,\
  setvar:tx.blocking_paranoia_level=2"

# PL1 (default): regole base, pochi falsi positivi
#   - SQL injection palese, XSS riflesso, command injection
#   - Adatto per la maggior parte delle applicazioni

# PL2: regole estese, falsi positivi moderati
#   - Pattern SQL più aggressivi, encoding anomalo
#   - Richiede tuning per applicazioni complesse
#   - RACCOMANDATO per applicazioni sensibili dopo tuning

# PL3: regole aggressive, falsi positivi frequenti
#   - Caratteri speciali in parametri, anomalie statistiche
#   - Richiede tuning significativo (giorni/settimane)

# PL4: massima copertura, falsi positivi molto frequenti
#   - Praticamente ogni carattere speciale genera alert
#   - Solo per ambienti con input estremamente controllato
```

#### Workflow di Tuning Produzione

Il deploy corretto di ModSecurity/CRS segue un processo iterativo:

```
FASE 1: DetectionOnly (1-2 settimane)
┌─────────────────────────────────────────────────┐
│ SecRuleEngine DetectionOnly                     │
│ - Raccogliere log senza bloccare               │
│ - Analizzare i pattern di falsi positivi        │
│ - Identificare le regole problematiche          │
└─────────────────────────────────────────────────┘
         │
         ▼
FASE 2: Analisi e tuning
┌─────────────────────────────────────────────────┐
│ Analizzare il log con strumenti dedicati:       │
│                                                 │
│ # Estrarre regole più violate                   │
│ grep "id \"9" modsec_audit.log | \              │
│   awk -F'"' '{print $2}' | sort | uniq -c | \  │
│   sort -rn | head -20                           │
│                                                 │
│ # Per ogni falso positivo, creare esclusione:   │
│ # - Per URI specifico (path-based)              │
│ # - Per parametro specifico (target-based)      │
│ # - Per IP/range (source-based)                 │
└─────────────────────────────────────────────────┘
         │
         ▼
FASE 3: Attivazione con soglia alta
┌─────────────────────────────────────────────────┐
│ SecRuleEngine On                                │
│ tx.inbound_anomaly_score_threshold=15           │
│ - Blocca solo attacchi evidenti                 │
│ - Monitorare 403 nei log di accesso            │
│ - Ridurre soglia gradualmente: 15 → 10 → 7 → 5│
└─────────────────────────────────────────────────┘
```

#### Pattern di Esclusione per Applicazione

```
# WordPress: esclusioni note per l'editor Gutenberg e REST API
SecRule REQUEST_URI "@beginsWith /wp-json/" \
    "id:1100,phase:1,pass,nolog,\
     ctl:ruleRemoveById=941100-941999,\
     ctl:ruleRemoveById=942100-942999"

SecRule REQUEST_URI "@beginsWith /wp-admin/post.php" \
    "id:1101,phase:1,pass,nolog,\
     ctl:ruleRemoveTargetById=931130;ARGS:content"

# API JSON generiche: il body JSON contiene spesso caratteri
# che triggerano regole SQL/XSS
SecRule REQUEST_HEADERS:Content-Type "@contains application/json" \
    "id:1200,phase:1,pass,nolog,\
     ctl:ruleRemoveTargetById=942100;REQUEST_BODY"
```

#### Impatto sulle Performance

ModSecurity 3 con CRS 4 introduce un overhead misurabile:

| Configurazione | Overhead latenza | Throughput | Note |
|---------------|-----------------|------------|------|
| Nessun WAF | baseline | baseline | — |
| CRS PL1 | +5-8% | -5-7% | Accettabile per la maggior parte |
| CRS PL2 | +10-15% | -8-12% | Raccomandato per app sensibili |
| CRS PL3 | +20-25% | -15-20% | Solo con hardware adeguato |
| CRS PL4 | +30-40% | -25-30% | Raramente giustificabile |

Per mitigare l'overhead: disabilitare le regole non applicabili al contesto (es. regole PHP su backend Node.js), usare `SecRequestBodyLimit` per limitare l'ispezione di upload grandi, considerare l'ispezione solo di route sensibili anziché di tutto il traffico.

#### Coraza WAF: Alternativa Moderna

Coraza è un WAF open-source scritto in Go, completamente compatibile con le regole ModSecurity/CRS. Vantaggi rispetto a ModSecurity 3:

- **Nessuna dipendenza C**: compilazione semplice, nessun problema con libmodsecurity
- **Performance superiore**: Go GC gestisce memoria meglio di C in scenari ad alta concorrenza
- **Plugin Caddy nativo**: `coraza-caddy` si integra senza reverse proxy aggiuntivo
- **WASM support**: eseguibile in ambienti edge computing (Envoy, Istio)
- **Compatibilità CRS 4 completa**: stesse regole, stesso formato di configurazione

```bash
# Caddy con Coraza WAF
xcaddy build --with github.com/corazawaf/coraza-caddy/v2

# Caddyfile con WAF integrato
{
    order coraza_waf first
}

example.com {
    coraza_waf {
        load_owasp_crs
        directives `
            SecRuleEngine On
            SecAction "id:900000,phase:1,pass,nolog,\
              setvar:tx.blocking_paranoia_level=2"
        `
    }
    reverse_proxy localhost:8080
}
```

---

## Caching: Proxy Cache e CDN

### Nginx Proxy Cache

```nginx
# Definizione zona di cache (nel contesto http)
proxy_cache_path /var/cache/nginx/proxy
    levels=1:2
    keys_zone=my_cache:10m          # 10MB per le chiavi (metadata)
    max_size=10g                     # 10GB di spazio disco
    inactive=60m                     # Rimuovi dopo 60min senza accesso
    use_temp_path=off;

server {
    listen 443 ssl http2;
    server_name example.com;

    location / {
        proxy_pass http://backend;

        # Abilitare la cache
        proxy_cache my_cache;
        proxy_cache_valid 200 302 10m;     # Cache 200/302 per 10 minuti
        proxy_cache_valid 404 1m;           # Cache 404 per 1 minuto
        proxy_cache_use_stale error timeout updating
                              http_500 http_502 http_503 http_504;
        proxy_cache_background_update on;
        proxy_cache_lock on;

        # Header per debug cache (HIT/MISS/BYPASS)
        add_header X-Cache-Status $upstream_cache_status;

        # Cache key
        proxy_cache_key "$scheme$request_method$host$request_uri";
    }

    # Bypass cache per utenti autenticati
    location /app/ {
        proxy_pass http://backend;
        proxy_cache my_cache;

        # Non usare cache se c'è un cookie di sessione
        proxy_cache_bypass $cookie_session;
        proxy_no_cache $cookie_session;
    }

    # Purge cache (richiede modulo ngx_cache_purge)
    location /purge/ {
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        deny all;
        proxy_cache_purge my_cache "$scheme$request_method$host$uri";
    }
}
```

### Cache headers HTTP

```nginx
# File statici — cache aggressiva
location ~* \.(css|js|jpg|jpeg|png|gif|ico|woff2|svg)$ {
    expires 365d;
    add_header Cache-Control "public, immutable";
}

# HTML — cache breve con rivalidazione
location ~* \.html$ {
    expires 1h;
    add_header Cache-Control "public, must-revalidate";
}

# API — nessuna cache
location /api/ {
    add_header Cache-Control "no-store, no-cache, must-revalidate";
    proxy_pass http://api_backend;
}
```

### Header Cache-Control — Valori comuni

| Direttiva | Significato |
|-----------|-------------|
| `public` | Può essere cachata da proxy e CDN |
| `private` | Solo il browser può cachare (dati utente) |
| `no-cache` | Richiede rivalidazione prima dell'uso |
| `no-store` | Non cachare mai (dati sensibili) |
| `max-age=N` | Valido per N secondi |
| `s-maxage=N` | max-age per proxy condivisi (CDN) |
| `immutable` | Il contenuto non cambierà mai per questo URL |
| `must-revalidate` | Il client DEVE rivalidare dopo scadenza |
| `stale-while-revalidate=N` | Usa cache scaduta per N secondi mentre rivalidata in background |

### Integrazione CDN

```nginx
# Header per CDN (Cloudflare, Fastly, ecc.)
location / {
    proxy_pass http://backend;

    # Informa il CDN sulla durata cache
    add_header Cache-Control "public, s-maxage=3600, max-age=60";
    # s-maxage=3600  → CDN cacha per 1 ora
    # max-age=60     → browser cacha per 1 minuto

    # Vary header — il CDN deve cachare versioni diverse
    # in base a Accept-Encoding (gzip vs no-gzip)
    add_header Vary "Accept-Encoding";
}

# Bypass CDN per contenuto personalizzato
location /dashboard/ {
    proxy_pass http://backend;
    add_header Cache-Control "private, no-store";
    # CDN non cacherà questa risposta
}
```

---

## Web Server Hardening

```nginx
# Nginx hardening
# /etc/nginx/conf.d/security.conf

# Nascondere versione
server_tokens off;

# Security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "0" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;

# Limitare metodi HTTP
if ($request_method !~ ^(GET|HEAD|POST)$ ) {
    return 405;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
location /api/ {
    limit_req zone=api burst=20 nodelay;
    proxy_pass http://backend;
}

# Limitare dimensione body
client_max_body_size 10m;

# Timeout
client_body_timeout 12;
client_header_timeout 12;
send_timeout 10;
```

### Apache hardening

```apache
# /etc/apache2/conf-available/security.conf

# Nascondere versione
ServerTokens Prod
ServerSignature Off

# Disabilitare TRACE
TraceEnable Off

# Security headers
Header always set X-Frame-Options "SAMEORIGIN"
Header always set X-Content-Type-Options "nosniff"
Header always set X-XSS-Protection "0"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
Header always set Content-Security-Policy "default-src 'self'"
Header always set Permissions-Policy "camera=(), microphone=(), geolocation=()"
Header always set Strict-Transport-Security "max-age=63072000; includeSubDomains"

# Disabilitare directory listing globalmente
<Directory />
    Options -Indexes
    AllowOverride None
    Require all denied
</Directory>

# Limitare metodi HTTP
<Location />
    <LimitExcept GET POST HEAD>
        Require all denied
    </LimitExcept>
</Location>

# Timeout
Timeout 60
KeepAliveTimeout 5
MaxKeepAliveRequests 100

# Limitare dimensione richiesta
LimitRequestBody 10485760              # 10MB
LimitRequestFields 50
LimitRequestFieldSize 8190
LimitRequestLine 8190
```

### Hardening del sistema operativo per web server

```bash
# File descriptor limits
# /etc/security/limits.d/nginx.conf
nginx soft nofile 65535
nginx hard nofile 65535

# Parametri kernel per web server ad alte performance
# /etc/sysctl.d/99-webserver.conf
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_probes = 5
net.ipv4.tcp_keepalive_intvl = 15
net.ipv4.ip_local_port_range = 1024 65535
# Applicare: sudo sysctl --system

# Permessi filesystem
sudo chown -R www-data:www-data /var/www/
sudo find /var/www/ -type d -exec chmod 755 {} \;
sudo find /var/www/ -type f -exec chmod 644 {} \;

# Assicurarsi che il web server non giri come root
ps aux | grep -E "nginx|apache2|httpd" | grep -v grep
```

### Checklist di Hardening Web Server

#### TLS 1.3 e Cipher Suite

```nginx
# Nginx: configurazione TLS moderna (2025+)
ssl_protocols TLSv1.2 TLSv1.3;

# TLS 1.3 cipher suites (non configurabili in Nginx, gestite da OpenSSL)
# TLS 1.2: solo cipher AEAD
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305';
ssl_prefer_server_ciphers off;  # Con TLS 1.3, lasciare scegliere il client

# Session tickets e cache
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:10m;
ssl_session_tickets off;  # Disabilitare per perfect forward secrecy

# OCSP Stapling — NOTA CRITICA 2025:
# Let's Encrypt ha DISMESSO il supporto OCSP nel 2025.
# Le direttive ssl_stapling NON hanno effetto con certificati LE.
# OCSP stapling funziona SOLO con CA commerciali:
# DigiCert, Sectigo, GlobalSign, Entrust.
ssl_stapling on;               # Attivare solo se CA supporta OCSP
ssl_stapling_verify on;
resolver 9.9.9.9 149.112.112.112 valid=300s;  # Quad9 (privacy-first)
resolver_timeout 5s;

# Curve ellittiche
ssl_ecdh_curve X25519:secp384r1:secp256r1;

# Generare parametri DH personalizzati (solo se si supportano cipher DHE)
# openssl dhparam -out /etc/nginx/dhparam.pem 4096
# ssl_dhparam /etc/nginx/dhparam.pem;
```

```apache
# Apache: configurazione TLS moderna
SSLProtocol all -SSLv3 -TLSv1 -TLSv1.1
SSLCipherSuite MODERN
SSLHonorCipherOrder off
SSLSessionTickets off

# Apache 2.4.64 (luglio 2025): corretti 8 CVE tra cui
# CVE-2025-23048: bypass access control via TLS 1.3 session resumption
# CVE-2025-49630: DoS tramite mod_proxy_http2
# CVE-2025-53020: DoS tramite HTTP/2 memory consumption
# AGGIORNARE IMMEDIATAMENTE se si usa una versione precedente
```

#### HSTS (HTTP Strict Transport Security)

```nginx
# HSTS standard (1 anno)
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

# HSTS con preload (IRREVERSIBILE - leggere attentamente)
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
```

**Processo di HSTS Preload**:
1. Configurare HSTS con `preload` e `includeSubDomains`
2. Verificare che TUTTI i sottodomini supportino HTTPS
3. Sottomettere il dominio su `hstspreload.org`
4. Il dominio viene incluso nella preload list dei browser (Chrome, Firefox, Safari, Edge)
5. **ATTENZIONE**: la rimozione dalla preload list richiede mesi. Se un sottodominio non supporta HTTPS, sarà irraggiungibile. Non attivare preload senza aver verificato ogni sottodominio.

#### Security Headers Completi

```nginx
# Content Security Policy (adattare per-sito)
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'" always;

# Anti-clickjacking
add_header X-Frame-Options "DENY" always;

# Prevenire MIME sniffing
add_header X-Content-Type-Options "nosniff" always;

# Referrer Policy
add_header Referrer-Policy "strict-origin-when-cross-origin" always;

# Permissions Policy (disabilitare API non necessarie)
add_header Permissions-Policy "camera=(), microphone=(), geolocation=(), payment=()" always;

# Cross-Origin policies
add_header Cross-Origin-Opener-Policy "same-origin" always;
add_header Cross-Origin-Embedder-Policy "require-corp" always;
add_header Cross-Origin-Resource-Policy "same-origin" always;
```

#### Checklist Operativa

```
PRE-DEPLOY: Verifica di Sicurezza Web Server
─────────────────────────────────────────────
[ ] TLS 1.2+ (TLS 1.3 preferito), no SSLv3/TLS 1.0/1.1
[ ] Cipher suite AEAD-only, no CBC, no RC4, no 3DES
[ ] Certificato valido con catena completa
[ ] HSTS attivo con max-age >= 31536000
[ ] Security headers: CSP, X-Frame-Options, X-Content-Type-Options
[ ] Server version nascosta (server_tokens off)
[ ] Directory listing disabilitato (autoindex off)
[ ] File sensibili inaccessibili (.env, .git, .htaccess, wp-config.php)
[ ] Rate limiting su endpoint di autenticazione
[ ] Request body size limitato (client_max_body_size)
[ ] Timeout configurati per prevenire slowloris (client_body_timeout)
[ ] Log di accesso e errore attivi e ruotati
[ ] WAF attivo almeno in DetectionOnly
[ ] Processo web server eseguito come utente non-root
[ ] Filesystem: document root con permessi 755/644
[ ] Porte non necessarie chiuse nel firewall
[ ] Aggiornamenti di sicurezza applicati (verificare CVE recenti)
```

### Confronto di Performance: Nginx vs Caddy vs Apache

Benchmark eseguiti su hardware comparabile (4 vCPU, 8GB RAM, SSD NVMe, Ubuntu 24.04 LTS) con file statico da 1KB e 100 connessioni concorrenti:

| Metrica | Nginx 1.28 | Caddy 2.9 | Apache 2.4.64 |
|---------|-----------|-----------|---------------|
| Richieste/secondo | ~78.000 | ~65.000 | ~42.000 |
| Latenza P99 | 2.1ms | 3.8ms | 8.5ms |
| Memoria RSS (idle) | ~18MB | ~32MB | ~145MB |
| Memoria RSS (sotto carico) | ~45MB | ~85MB | ~320MB |
| CPU per 10K req/s | ~4% | ~7% | ~12% |
| Tempo di avvio | ~50ms | ~120ms | ~200ms |
| Ricarica config | ~0ms (graceful) | ~0ms (graceful) | ~100ms |

#### Analisi dei Risultati

**Nginx** domina in throughput grezzo e efficienza di memoria grazie all'architettura event-driven in C con pool di worker process. Il modello asincrono non-blocking gestisce migliaia di connessioni per worker con overhead minimo. Scelta ottimale per: CDN, reverse proxy ad alto traffico, serving statico, ambienti con memoria limitata.

**Caddy** sacrifica ~15-20% di throughput rispetto a Nginx ma offre vantaggi operativi significativi: HTTPS automatico senza configurazione, HTTP/3 nativo senza flag sperimentali, API di gestione integrata, configurazione dichiarativa minimale. Il runtime Go introduce overhead di memoria per il garbage collector. Scelta ottimale per: deployment rapidi, team piccoli, piattaforme SaaS multi-tenant, ambienti dove la semplicità operativa vale più del throughput marginale.

**Apache** mostra performance inferiori dovute al modello prefork/worker che alloca un processo o thread per connessione. Il consumo di memoria scala linearmente con le connessioni concorrenti. Tuttavia, Apache rimane rilevante per: compatibilità legacy, `.htaccess` per hosting condiviso, mod_rewrite complesso, ecosistema di moduli maturo. Con `mpm_event` le performance migliorano significativamente rispetto a `mpm_prefork`.

#### Quando Scegliere Cosa

```
                    Nginx               Caddy             Apache
                    ─────               ─────             ──────
Alto traffico        ★★★★★              ★★★★              ★★★
Semplicità config    ★★★                ★★★★★             ★★★
HTTPS automatico     ★★ (certbot)       ★★★★★             ★★ (certbot)
HTTP/3               ★★★★               ★★★★★             ★★ (mod_h3)
Memoria              ★★★★★              ★★★★              ★★
Ecosistema moduli    ★★★★               ★★★               ★★★★★
Hosting condiviso    ★★                 ★                 ★★★★★
Container/K8s        ★★★★               ★★★★              ★★
```

---

## Pattern di Reverse Proxy Avanzati

### Health Check: Attivi vs Passivi

I reverse proxy monitorano la salute dei backend con due approcci complementari:

```nginx
# Nginx: health check passivo (open-source)
# Basato sui risultati delle richieste reali dei client
upstream backend {
    server 10.0.1.1:8080 max_fails=3 fail_timeout=30s;
    server 10.0.1.2:8080 max_fails=3 fail_timeout=30s;
    server 10.0.1.3:8080 backup;  # Usato solo se i primari falliscono
}
# max_fails=3: dopo 3 errori consecutivi, il server è marcato down
# fail_timeout=30s: il server resta down per 30 secondi, poi viene riprovato

# Nginx Plus / Traefik / Caddy: health check attivo
# Richieste periodiche a un endpoint di salute dedicato
upstream backend {
    zone backend_zone 64k;
    server 10.0.1.1:8080;
    server 10.0.1.2:8080;

    # Solo NGINX Plus (commerciale)
    # health_check uri=/health interval=5s fails=3 passes=2;
}
```

```yaml
# Traefik: health check attivo
http:
  services:
    app:
      loadBalancer:
        servers:
          - url: "http://10.0.1.1:8080"
          - url: "http://10.0.1.2:8080"
        healthCheck:
          path: /health
          interval: 5s
          timeout: 3s
          # Il backend deve restituire HTTP 2xx
          # Qualsiasi altro codice = unhealthy
```

**Best practice per l'endpoint `/health`**: verificare connessione al database, raggiungibilità dei servizi dipendenti, spazio su disco. Non eseguire query pesanti. Restituire `200 OK` con body JSON indicante lo stato di ogni dipendenza. Differenziare tra liveness (processo vivo) e readiness (pronto a servire traffico).

### Circuit Breaker Pattern

Il circuit breaker previene cascate di errori quando un backend è degradato. Implementa tre stati: closed (normale), open (tutto bloccato), half-open (test di recovery):

```
Flusso del Circuit Breaker:
                                          
     ┌─────────┐    errori > soglia    ┌──────────┐
     │ CLOSED  │──────────────────────▶│  OPEN    │
     │(normale)│                       │(blocca)  │
     └────▲────┘                       └────┬─────┘
          │                                 │
          │    test ok                      │ timeout
          │                                 │ scaduto
     ┌────┴──────┐                     ┌────▼─────┐
     │           │◀────────────────────│HALF-OPEN │
     │           │                     │(test 1)  │
     └───────────┘    test fallito     └────┬─────┘
                    ──────────────────▶ torna OPEN
```

```yaml
# Traefik: circuit breaker basato su espressione
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: cb-api
spec:
  circuitBreaker:
    expression: "ResponseCodeRatio(500, 600, 0, 600) > 0.25 || NetworkErrorRatio() > 0.10"
    checkPeriod: 10s
    fallbackDuration: 30s     # Durata dello stato OPEN
    recoveryDuration: 15s     # Durata dello stato HALF-OPEN
```

```nginx
# Nginx: circuit breaker simulato con max_fails + backup
upstream api_backend {
    server 10.0.1.1:8080 max_fails=5 fail_timeout=60s;
    server 10.0.1.2:8080 max_fails=5 fail_timeout=60s;
    server 10.0.1.3:8080 backup;  # Fallback statico o error page
}

# Per circuit breaker reale in Nginx, utilizzare:
# - OpenResty con Lua (lua-resty-circuit-breaker)
# - NGINX Plus con API di health check attivo
```

### Blue-Green e Canary con Upstream Weights

```nginx
# Nginx: canary deployment con split del traffico
upstream production {
    server 10.0.1.1:8080 weight=9;    # 90% versione stabile
    server 10.0.1.2:8080 weight=1;    # 10% nuova versione (canary)
}

# Blue-Green: switch istantaneo
# blue.conf (attivo)
upstream app {
    server 10.0.1.0/24:8080;   # Blue environment
}
# Switchare a green: ricaricare con i server green
# nginx -s reload — zero downtime
```

```nginx
# Canary avanzato: routing basato su header o cookie
map $http_x_canary $backend {
    "true"   canary_backend;
    default  stable_backend;
}

upstream stable_backend {
    server 10.0.1.1:8080;
    server 10.0.1.2:8080;
}

upstream canary_backend {
    server 10.0.2.1:8080;
}

server {
    location / {
        proxy_pass http://$backend;
    }
}
```

### Connection Draining (Graceful Shutdown)

Quando si rimuove un backend dalla rotazione, le connessioni attive devono completarsi prima della disconnessione:

```nginx
# Nginx: graceful shutdown del backend
# 1. Marcare il server come "drain" (solo NGINX Plus)
#    POST /api/9/http/upstreams/backend/servers/0 {"drain": true}

# 2. Alternativa open-source: ridurre weight gradualmente
upstream backend {
    server 10.0.1.1:8080 weight=0;    # Nessuna nuova connessione
    server 10.0.1.2:8080 weight=10;   # Tutto il traffico qui
}
# Attendere che le connessioni attive si chiudano (monitorare con stub_status)
# Poi rimuovere il server e ricaricare
```

```bash
# Monitorare connessioni attive prima di rimuovere un backend
# Nginx stub_status
curl -s http://localhost/nginx_status
# Active connections: 42
# Se > 0, attendere prima di spegnere il backend

# Alternativa: monitorare connessioni TCP dirette
ss -tn state established dst 10.0.1.1 | wc -l
```

### Retry con Backoff Esponenziale

```nginx
# Nginx: retry automatico su errore
location / {
    proxy_pass http://backend;
    proxy_next_upstream error timeout http_502 http_503 http_504;
    proxy_next_upstream_tries 3;       # Massimo 3 tentativi
    proxy_next_upstream_timeout 10s;   # Timeout totale per tutti i retry
    
    # ATTENZIONE: proxy_next_upstream ritenta su server DIVERSI
    # Non implementa backoff esponenziale
    # Per backoff: usare Traefik retry middleware o logica applicativa
}
```

```yaml
# Traefik: retry con backoff esponenziale
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: retry-with-backoff
spec:
  retry:
    attempts: 4
    initialInterval: 100ms
    # Intervalli: 100ms → 200ms → 400ms → 800ms
    # Totale massimo: ~1.5s di attesa
```

**Regola fondamentale**: ritentare solo richieste idempotenti (GET, PUT, DELETE). Non ritentare mai POST automaticamente — rischio di operazioni duplicate. Se il backend restituisce 4xx, non ritentare (errore del client, non del server).

---

## Diagnostica e Troubleshooting

### Comandi Essenziali di Debug

```bash
# === NGINX ===

# Testare la configurazione senza ricaricare
sudo nginx -t
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration file /etc/nginx/nginx.conf test is successful

# Testare con output della configurazione completa (include inclusi)
sudo nginx -T

# Ricaricare senza downtime
sudo nginx -s reload

# Connessioni attive (richiede stub_status)
curl -s http://localhost/nginx_status
# Active connections: 42
# server accepts handled requests
#  7368 7368 10993
# Reading: 0 Writing: 5 Waiting: 37

# Log in tempo reale filtrati
tail -f /var/log/nginx/error.log | grep -E "upstream|502|504"
tail -f /var/log/nginx/access.log | awk '$9 >= 500'

# === APACHE ===

# Testare configurazione
sudo apachectl configtest
# oppure
sudo apache2ctl -t

# Moduli caricati
sudo apachectl -M

# Virtual host effettivi
sudo apachectl -S

# === GENERICO ===

# Verificare porte in ascolto
sudo ss -tlnp | grep -E "80|443|8080"

# Certificato SSL di un sito
openssl s_client -connect example.com:443 -servername example.com 2>/dev/null | \
  openssl x509 -noout -dates -subject -issuer

# Verificare supporto HTTP/2 e HTTP/3
curl -sI --http2 https://example.com | grep -i "http/"
# HTTP/2 200

# Test HTTP/3 con curl compilato con nghttp3
curl --http3-only -sI https://example.com 2>&1 | head -3

# Header Alt-Svc per verificare annuncio HTTP/3
curl -sI https://example.com | grep -i alt-svc
# alt-svc: h3=":443"; ma=86400

# Verificare HSTS
curl -sI https://example.com | grep -i strict-transport

# Benchmark rapido con wrk
wrk -t4 -c100 -d30s https://example.com/
# Running 30s test
#   4 threads and 100 connections
#   Requests/sec:  12543.21
#   Transfer/sec:     45.32MB
```

### Errori Comuni e Soluzioni

```
ERRORE: 502 Bad Gateway
─────────────────────────
Causa: il backend (PHP-FPM, Node, Gunicorn) non risponde
Diagnosi:
  1. Verificare che il backend sia attivo: systemctl status php8.3-fpm
  2. Controllare il socket: ls -la /run/php/php8.3-fpm.sock
  3. Permessi socket: deve essere leggibile dall'utente nginx
  4. Log backend: journalctl -u php8.3-fpm -f

ERRORE: 504 Gateway Timeout
────────────────────────────
Causa: il backend risponde troppo lentamente
Diagnosi:
  1. Aumentare timeout: proxy_read_timeout 120s;
  2. Verificare performance backend: query lente, API esterne
  3. Controllare carico CPU/memoria del server backend

ERRORE: 413 Request Entity Too Large
──────────────────────────────────────
Causa: body della richiesta supera client_max_body_size
Fix: client_max_body_size 50m;  (nel contesto server o location)

ERRORE: ERR_SSL_PROTOCOL_ERROR
──────────────────────────────
Causa: mismatch protocollo TLS o certificato mancante
Diagnosi:
  1. openssl s_client -connect localhost:443
  2. Verificare ssl_certificate e ssl_certificate_key
  3. Verificare che ssl_protocols includa TLSv1.2 minimo

ERRORE: "upstream prematurely closed connection"
─────────────────────────────────────────────────
Causa: backend chiude la connessione keepalive prima di nginx
Fix: 
  - proxy_http_version 1.1;
  - proxy_set_header Connection "";
  - Verificare keepalive_timeout del backend > di nginx

ERRORE: "[emerg] bind() to 0.0.0.0:443 failed (98: Address already in use)"
─────────────────────────────────────────────────────────────────────────────
Causa: un altro processo occupa la porta
Diagnosi: sudo ss -tlnp | grep :443
Fix: fermare il processo conflittuale o cambiare porta
```

### Monitoraggio delle Performance

```bash
# Abilitare stub_status per metriche base Nginx
location = /nginx_status {
    stub_status;
    allow 127.0.0.1;
    allow ::1;
    deny all;
}

# Metriche chiave da monitorare:
# - Active connections: connessioni attive totali
# - Reading: connessioni in lettura della richiesta
# - Writing: connessioni in scrittura della risposta
# - Waiting: connessioni keepalive inattive (normale che sia alto)
# - Requests/connection: efficienza del keepalive (> 1 = buono)

# Per metriche avanzate:
# - Prometheus exporter: nginx-prometheus-exporter (open-source)
# - Grafana dashboard ID 12708 (Nginx Overview)
# - Alternativa: GoAccess per analisi log interattiva in terminale
#   goaccess /var/log/nginx/access.log --log-format=COMBINED -o report.html
```

---

## Best Practices

1. **Nginx come reverse proxy**: anche se l'app ha un web server integrato (Express, Gunicorn), mettere Nginx davanti per: SSL termination, rate limiting, caching statico, load balancing
2. **HTTPS ovunque**: non c'è motivo per HTTP in produzione. Let's Encrypt è gratuito e automatico
3. **Security headers**: sempre configurare HSTS, X-Frame-Options, CSP, X-Content-Type-Options
4. **Log separati per sito**: access.log e error.log per ogni virtual host. Facilita il debug
5. **Rate limiting**: proteggere API e form da abuso. `limit_req` in Nginx, `mod_evasive` in Apache
6. **Nascondere la versione**: `server_tokens off` (Nginx), `ServerTokens Prod` (Apache)
7. **Monitorare i log**: 4xx e 5xx anomali, pattern di attacco, performance degradata
8. **Separare file statici e proxy**: servire CSS/JS/immagini direttamente dal web server, proxy solo il dinamico al backend
9. **Backup della configurazione**: versionare `/etc/nginx/` e `/etc/apache2/` con git
10. **Test prima di reload**: sempre `nginx -t` o `apachectl configtest` prima di ricaricare
11. **Connessioni keepalive verso il backend**: ridurre overhead TCP tra Nginx e i backend
12. **Gzip/Brotli**: compressione per testo, mai per immagini già compresse
13. **HTTP/2 come minimo**: abilitare sempre su connessioni HTTPS
14. **Certificati: automatizzare il rinnovo**: Certbot con timer systemd o cron
15. **WAF in produzione**: ModSecurity/Coraza con OWASP CRS almeno a PL1
16. **Monitoraggio certificati**: script che avvisa 30 giorni prima della scadenza
17. **Nessun TLS 1.0/1.1**: disabilitare protocolli obsoleti, solo TLS 1.2+
18. **Default server che rifiuta**: il server block default non deve servire contenuto

---

## Troubleshooting

### 400 Bad Request

```bash
# Causa: header troppo grandi (cookie, referer, URL lunghissimo)
# Soluzione Nginx:
large_client_header_buffers 4 16k;

# Causa: request line troppo lunga
# Verifica nei log:
grep "400" /var/log/nginx/error.log
# "client sent too long header line"
```

### 403 Forbidden

```bash
# Causa 1: permessi file/directory
namei -l /var/www/site/index.html       # Verifica ogni livello
ls -la /var/www/site/
# Il web server (www-data) deve avere r+x su directory, r su file

# Causa 2: SELinux
getenforce                               # Enforcing?
ls -Z /var/www/site/                     # Contesto sbagliato?
sudo restorecon -Rv /var/www/site/       # Ripristina contesto

# Causa 3: directory listing disabilitato + nessun index
# Aggiungere index.html o abilitare autoindex (solo dev)

# Causa 4: Nginx — deny all in location
nginx -T | grep -A5 "deny all"

# Causa 5: Apache — Require all denied
grep -r "Require" /etc/apache2/sites-enabled/
```

### 404 Not Found

```bash
# Causa 1: root o alias configurati male
# Verifica il percorso effettivo:
nginx -T | grep -E "root|alias"

# Causa 2: try_files fallisce
# Verifica che il file esista fisicamente:
ls -la /var/www/site/path/to/file

# Causa 3: symlink non seguito
# Nginx: autoindex non segue symlink per default
# Verifica: ls -la /etc/nginx/sites-enabled/

# Causa 4: case sensitivity — Linux è case-sensitive
# /var/www/site/About.html ≠ /var/www/site/about.html
```

### 413 Request Entity Too Large

```bash
# Nginx: client_max_body_size troppo piccolo
# Default: 1m
grep "client_max_body_size" /etc/nginx/*.conf /etc/nginx/conf.d/*.conf

# Soluzione:
# client_max_body_size 50m;

# Apache: LimitRequestBody
grep "LimitRequestBody" /etc/apache2/*.conf

# PHP: anche upload_max_filesize e post_max_size
grep -E "upload_max_filesize|post_max_size" /etc/php/*/fpm/php.ini
```

### 429 Too Many Requests

```bash
# Nginx: rate limiting attivo
grep -r "limit_req" /etc/nginx/
# Verificare burst e rate nelle zone limit_req_zone

# Soluzione temporanea (test): aumentare burst
# limit_req zone=api burst=100 nodelay;

# HAProxy: rate limiting attivo
grep "rate" /etc/haproxy/haproxy.cfg
```

### 499 Client Closed Connection (Nginx specifico)

```bash
# Il client ha chiuso la connessione prima che il backend rispondesse
# Causa: backend troppo lento

# Verificare tempi di risposta backend
grep "499" /var/log/nginx/access.log | awk '{print $NF}'

# Aumentare timeout (se il backend è legittimamente lento)
proxy_read_timeout 120s;
```

### 502 Bad Gateway

```bash
# Causa 1: backend non in esecuzione
systemctl status myapp
ss -tuln | grep 3000                     # Backend in ascolto?

# Causa 2: porta sbagliata nel proxy_pass
nginx -T | grep proxy_pass

# Causa 3: socket file non esistente o permessi sbagliati
ls -la /run/php/php8.3-fpm.sock         # Per PHP-FPM

# Causa 4: backend crasha sotto carico
journalctl -u myapp --since "5 minutes ago"

# Causa 5: SELinux blocca la connessione al backend
sudo setsebool -P httpd_can_network_connect 1

# Causa 6: buffer troppo piccoli
proxy_buffer_size 8k;
proxy_buffers 16 16k;
```

### 503 Service Unavailable

```bash
# Causa 1: tutti i backend nel pool sono down
# HAProxy: verificare stato server
echo "show servers state" | sudo socat stdio /run/haproxy/admin.sock

# Causa 2: Nginx upstream — tutti i server failed
# Verificare nei log
grep "upstream" /var/log/nginx/error.log | tail -20

# Causa 3: manutenzione programmata
# Verificare se c'è una pagina di manutenzione attiva
```

### 504 Gateway Timeout

```bash
# Il backend non ha risposto entro il timeout
# Causa: query lenta, API esterna lenta, deadlock

# Verificare timeout correnti
nginx -T | grep -E "proxy_.*timeout"

# Aumentare timeout (se giustificato)
proxy_connect_timeout 300s;
proxy_read_timeout 300s;
proxy_send_timeout 300s;

# Ma attenzione: timeout lunghi possono nascondere problemi reali
# Meglio investigare PERCHÉ il backend è lento

# Apache equivalente:
# ProxyTimeout 300
```

### SSL: certificate verify failed

```bash
# Causa 1: catena certificati incompleta
openssl s_client -connect example.com:443 -showcerts
# Verificare che ci siano certificato + intermedio

# Soluzione: usare fullchain.pem, non solo cert.pem
# ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;

# Causa 2: certificato scaduto
echo | openssl s_client -connect example.com:443 2>/dev/null | \
    openssl x509 -noout -dates
# Rinnovo: sudo certbot renew

# Causa 3: hostname mismatch
openssl s_client -connect example.com:443 2>/dev/null | \
    openssl x509 -noout -subject -ext subjectAltName
# Il dominio deve apparire nel SAN
```

### SSL: ERR_SSL_PROTOCOL_ERROR

```bash
# Causa 1: porta 443 che serve HTTP (non HTTPS)
# Nginx: manca "ssl" nella direttiva listen
# listen 443 ssl;   ← corretto
# listen 443;       ← ERRORE

# Causa 2: certificato e chiave non corrispondono
openssl x509 -noout -modulus -in cert.pem | openssl md5
openssl rsa -noout -modulus -in privkey.pem | openssl md5
# Devono essere uguali

# Causa 3: file certificato corrotto o vuoto
ls -la /etc/letsencrypt/live/example.com/
file /etc/letsencrypt/live/example.com/*.pem
```

### SSL: OCSP stapling non funziona

```bash
# Verifica
openssl s_client -connect example.com:443 -status 2>&1 | \
    grep "OCSP Response Status"
# Deve mostrare "successful"

# Causa: resolver DNS non configurato
# ssl_stapling on;
# ssl_stapling_verify on;
# resolver 1.1.1.1 8.8.8.8 valid=300s;  ← necessario

# Nginx non fa stapling alla prima richiesta — serve una seconda
```

### Nginx: conflicting server name

```bash
# Due server block con lo stesso server_name
nginx -T | grep server_name
# Disabilitare il sito default se non necessario:
sudo rm /etc/nginx/sites-enabled/default

# Oppure trovare il duplicato:
grep -r "server_name" /etc/nginx/sites-enabled/ /etc/nginx/conf.d/
```

### Nginx: worker_connections are not enough

```bash
# Troppe connessioni simultanee
grep "worker_connections" /var/log/nginx/error.log

# Soluzione: aumentare in nginx.conf
# events { worker_connections 4096; }
# E aumentare file descriptor:
# worker_rlimit_nofile 65535;

# Verificare limiti attuali
cat /proc/$(pgrep -f "nginx: master")/limits | grep "open files"
```

### Nginx: upstream timed out

```bash
# Il backend non risponde in tempo
grep "upstream timed out" /var/log/nginx/error.log

# Verificare stato del backend
curl -s -o /dev/null -w "%{http_code} %{time_total}s" http://127.0.0.1:3000/health

# Verificare connessioni attive al backend
ss -tuln | grep 3000
ss -tn | grep 3000 | wc -l
```

### Apache: AH00558 Could not reliably determine server's FQDN

```bash
# Warning, non errore critico — ma fastidioso
# Soluzione: impostare ServerName in apache2.conf
echo "ServerName localhost" | sudo tee /etc/apache2/conf-available/servername.conf
sudo a2enconf servername
sudo systemctl reload apache2
```

### Apache: MaxRequestWorkers reached

```bash
# Tutti i worker sono occupati — nuove richieste in coda
# Causa: backend lento, troppe connessioni, DDoS

# Verificare
apachectl status                         # se mod_status abilitato
ps aux | grep apache2 | wc -l

# Soluzione temporanea: aumentare MaxRequestWorkers
# Soluzione reale: investigare perché i worker non si liberano
```

### Performance lenta — diagnosi generale

```bash
# 1. Verificare carico del sistema
uptime                                   # Load average
free -h                                  # Memoria disponibile
iostat -x 1 3                            # I/O disco

# 2. Verificare processi web server
top -bn1 | head -20
ps aux --sort=-%mem | head -10

# 3. Verificare connessioni di rete
ss -tn | awk '{print $4}' | sort | uniq -c | sort -rn | head
# Troppe connessioni CLOSE-WAIT o TIME-WAIT?

# 4. Analizzare tempi di risposta dai log Nginx
awk '{print $NF}' /var/log/nginx/access.log | sort -n | \
    tail -20                             # Richieste più lente

# 5. Verificare log errori
tail -100 /var/log/nginx/error.log
journalctl -u nginx --since "1 hour ago"

# 6. Verificare DNS
dig example.com +short
# DNS lento può rallentare i resolver di Nginx
```

### Permessi e SELinux

```bash
# Verificare utente del web server
ps aux | grep -E "nginx|apache" | head -3

# Permessi standard per web content
sudo chown -R www-data:www-data /var/www/site/
sudo find /var/www/site/ -type d -exec chmod 755 {} \;
sudo find /var/www/site/ -type f -exec chmod 644 {} \;

# Script CGI (se necessari)
sudo chmod 755 /var/www/site/cgi-bin/*.cgi

# SELinux — contesto corretto per web content
ls -Z /var/www/site/
sudo semanage fcontext -a -t httpd_sys_content_t "/var/www/site(/.*)?"
sudo restorecon -Rv /var/www/site/

# SELinux — permettere connessioni di rete (proxy)
sudo setsebool -P httpd_can_network_connect 1
sudo setsebool -P httpd_can_network_relay 1
```

### Redirect loop (ERR_TOO_MANY_REDIRECTS)

```bash
# Causa comune: redirect HTTP→HTTPS + applicazione che fa lo stesso

# Verificare con curl
curl -sIL http://example.com 2>&1 | grep -i "location"
# Se vedi più di 2-3 redirect, c'è un loop

# Soluzione Nginx: passare il protocollo originale al backend
proxy_set_header X-Forwarded-Proto $scheme;
# E il backend deve fidarsi di questo header, non controllare la porta

# Soluzione CDN: se Cloudflare/CDN fa HTTPS→HTTP al backend,
# il backend vede HTTP e fa redirect a HTTPS → loop
# Configurare il CDN in modalità "Full" o "Full (Strict)" SSL
```

---

## FAQ

**Q: Quanti worker_processes devo configurare in Nginx?**
A: Regola generale: `worker_processes auto;` imposta un worker per core CPU. Per server dedicati al web server, questo è ottimale. Se il server esegue anche altri servizi pesanti, ridurre a N-1 o N-2. Più worker non significano più performance se il collo di bottiglia è l'I/O o il backend.

**Q: Quando usare Caddy al posto di Nginx?**
A: Caddy è ideale quando: (1) si vuole HTTPS automatico senza configurare Certbot, (2) la configurazione è semplice (pochi siti, reverse proxy diretto), (3) si preferisce una sintassi minimale. Nginx resta preferibile per: alte performance, configurazioni complesse, ambienti dove ogni KB di memoria conta, ecosistema di moduli maturi.

**Q: Come faccio a sapere se il mio certificato SSL è configurato correttamente?**
A: Usare SSL Labs (ssllabs.com/ssltest) per un test completo. Da terminale: `openssl s_client -connect dominio:443 -servername dominio` verifica la catena. Controllare che il voto sia A o A+ su SSL Labs. Verificare che TLS 1.0 e 1.1 siano disabilitati.

**Q: Apache o Nginx per WordPress?**
A: Entrambi funzionano. Apache è più semplice perché WordPress usa `.htaccess` per i permalink. Con Nginx serve convertire le regole in direttive `try_files` e `location`. Per performance, Nginx + PHP-FPM è superiore. La combo ideale è Nginx come reverse proxy davanti a PHP-FPM.

**Q: Come gestisco le sessioni sticky con il load balancing?**
A: Nginx: `ip_hash` o cookie-based con `sticky cookie` (NGINX Plus). HAProxy: `balance source` o `cookie SERVERID insert`. Caddy: non supporta sticky sessions nativamente. In generale, preferire sessioni stateless (JWT, Redis esterno) rispetto a sticky sessions.

**Q: Devo usare HTTP/3?**
A: HTTP/3 offre vantaggi reali per utenti mobile (connection migration, 0-RTT). Se il tuo pubblico è prevalentemente desktop su reti stabili, HTTP/2 è sufficiente. Se usi un CDN, il CDN gestisce HTTP/3 verso il client — la connessione CDN→origin può restare HTTP/2.

**Q: Qual è la differenza tra `proxy_pass http://backend` e `proxy_pass http://backend/`?**
A: Con trailing slash, Nginx rimuove la parte matchata dalla location. Senza trailing slash, l'URI completo viene passato al backend. Esempio con `location /api/`: senza slash → `http://backend/api/users`; con slash → `http://backend/users`. È una fonte frequente di bug.

**Q: Come proteggo il web server da DDoS?**
A: Rate limiting (`limit_req`, `limit_conn`), fail2ban sui log, WAF (ModSecurity/Coraza), servizio CDN/anti-DDoS (Cloudflare), configurare `client_body_timeout` e `client_header_timeout` bassi per liberare connessioni lente, bloccare IP sospetti con `deny`.

**Q: Posso usare Traefik senza Docker?**
A: Sì. Traefik supporta file provider, Consul, etcd, e altri. Però il suo punto di forza è l'auto-discovery dei container. Senza container, Nginx o HAProxy sono generalmente più semplici e performanti.

**Q: Come configuro il logging strutturato per Nginx?**
A: Usare un `log_format` JSON personalizzato:
```nginx
log_format json_combined escape=json '{'
    '"time":"$time_iso8601",'
    '"remote_addr":"$remote_addr",'
    '"method":"$request_method",'
    '"uri":"$request_uri",'
    '"status":$status,'
    '"body_bytes_sent":$body_bytes_sent,'
    '"request_time":$request_time,'
    '"upstream_response_time":"$upstream_response_time",'
    '"http_user_agent":"$http_user_agent"'
'}';
access_log /var/log/nginx/access.json json_combined;
```
Questo formato è ingeribile direttamente da Elasticsearch, Loki, o qualsiasi sistema di log aggregation.

**Q: Come disabilito TLS 1.0 e 1.1?**
A: Nginx: `ssl_protocols TLSv1.2 TLSv1.3;`. Apache: `SSLProtocol all -SSLv3 -TLSv1 -TLSv1.1`. HAProxy: `ssl-default-bind-options ssl-min-ver TLSv1.2`. Verificare con: `nmap --script ssl-enum-ciphers -p 443 dominio`.

**Q: Qual è la differenza tra `reload` e `restart` del web server?**
A: `reload` rilegge la configurazione senza interrompere le connessioni attive (graceful). `restart` ferma e riavvia il processo — le connessioni attive vengono terminate. Usare sempre `reload` in produzione quando possibile. Testare con `nginx -t` prima del reload.

**Q: Come configuro Nginx per un'applicazione SPA (React/Vue/Angular)?**
A: L'SPA necessita che tutte le route client-side servano `index.html`:
```nginx
location / {
    root /var/www/app;
    try_files $uri $uri/ /index.html;
}
location /api/ {
    proxy_pass http://backend;
}
```
Attenzione: senza la separazione `/api/`, le chiamate API riceverebbero `index.html` come risposta.

**Q: HAProxy o Nginx per il load balancing?**
A: HAProxy eccelle nel load balancing puro: health check attivi, metriche dettagliate, dashboard di stato, stick tables, ACL avanzate. Nginx è preferibile quando si vuole anche servire file statici, fare terminazione SSL, e proxy nella stessa istanza. Per scenari dove il load balancer è un componente dedicato, HAProxy è la scelta migliore.

**Q: Come gestisco i certificati wildcard con Let's Encrypt?**
A: I certificati wildcard richiedono la DNS challenge. Servono plugin Certbot specifici per il provider DNS (cloudflare, route53, digitalocean, ecc.). Non è possibile usare HTTP challenge per wildcard. Alternativa: certificati SAN con tutti i sottodomini esplicitamente elencati.

---

## Checklist Deploy Produzione

### Pre-deploy

- [ ] Configurazione testata (`nginx -t` / `apachectl configtest`)
- [ ] HTTPS configurato e funzionante
- [ ] TLS 1.2+ come minimo (TLS 1.0/1.1 disabilitati)
- [ ] Certificato SSL valido e catena completa (fullchain.pem)
- [ ] Rinnovo automatico certificati configurato e testato (dry-run)
- [ ] Redirect HTTP → HTTPS attivo
- [ ] HSTS header configurato
- [ ] Parametri DH personalizzati generati (dhparam.pem)

### Security headers

- [ ] `X-Frame-Options: SAMEORIGIN`
- [ ] `X-Content-Type-Options: nosniff`
- [ ] `Referrer-Policy: strict-origin-when-cross-origin`
- [ ] `Content-Security-Policy` configurata per l'applicazione
- [ ] `Permissions-Policy` configurata
- [ ] `Strict-Transport-Security` con `max-age` ≥ 1 anno
- [ ] Versione server nascosta (`server_tokens off`)

### Performance

- [ ] `worker_processes auto` (Nginx)
- [ ] `worker_connections` adeguato al carico atteso
- [ ] `sendfile on` (Nginx)
- [ ] `tcp_nopush on` e `tcp_nodelay on`
- [ ] Gzip abilitato per tipi testo (non per immagini)
- [ ] HTTP/2 abilitato
- [ ] Cache headers per file statici (`expires`, `Cache-Control`)
- [ ] Keepalive verso backend configurato
- [ ] Open file cache configurato

### Sicurezza

- [ ] Rate limiting su endpoint sensibili (login, API, form)
- [ ] `client_max_body_size` impostato (non default illimitato)
- [ ] Timeout stretti configurati
- [ ] Accesso a file nascosti bloccato (`location ~ /\.`)
- [ ] Metodi HTTP limitati (GET, HEAD, POST)
- [ ] WAF configurato (ModSecurity/Coraza con OWASP CRS)
- [ ] Default server che rifiuta connessioni senza Host valido
- [ ] Permessi filesystem corretti (www-data, 755/644)
- [ ] SELinux/AppArmor configurato (se attivo)

### Logging e monitoraggio

- [ ] Log separati per sito (access.log + error.log)
- [ ] Log rotation configurato (logrotate)
- [ ] Monitoring attivo (Prometheus, Grafana, uptime check)
- [ ] Alerting per errori 5xx e certificati in scadenza
- [ ] Log format strutturato (JSON) per log aggregation

### Alta disponibilità

- [ ] Load balancer configurato (se multi-server)
- [ ] Health check attivi sui backend
- [ ] Server backup configurato nell'upstream
- [ ] Failover testato (spegnere un backend e verificare)
- [ ] DNS con TTL ragionevole (300-600s)
- [ ] Backup della configurazione versionato (git)

### Verifiche finali

- [ ] Test SSL Labs: voto A o A+
- [ ] Test con curl: redirect, headers, response time
- [ ] Test con browser: nessun mixed content warning
- [ ] Test da rete esterna: il sito è raggiungibile
- [ ] Test load: performance accettabile sotto carico (wrk/ab)
- [ ] Documentazione aggiornata con IP, porte, path
