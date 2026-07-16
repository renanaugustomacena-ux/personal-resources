# Tutorial Linux 17 — Web Server: nginx, SSL/TLS, Virtual Host, Reverse Proxy

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** nginx produzione, TLS con certbot, virtual host, proxy pass, caching, rate limit
> **Prerequisiti:** `tutorial_linux_05_networking.md`, `tutorial_linux_11_sicurezza.md`
> **Durata stimata:** 14-18 ore

---

## Mappa concettuale

```
nginx Web Server
│
├── Struttura configurazione
│   ├── /etc/nginx/nginx.conf — master
│   ├── /etc/nginx/conf.d/ — snippet
│   └── /etc/nginx/sites-enabled/ — virtual hosts
│
├── Virtual host (server block)
│   ├── server_name
│   ├── root e index
│   └── location blocks
│
├── TLS/SSL
│   ├── certbot (Let's Encrypt)
│   ├── Certificati custom
│   └── HSTS, OCSP stapling
│
├── Reverse proxy
│   ├── proxy_pass
│   ├── upstream (load balancing)
│   └── Header management
│
├── Performance
│   ├── gzip compression
│   ├── Static file caching
│   ├── FastCGI cache
│   └── proxy_cache
│
└── Sicurezza
    ├── Rate limiting
    ├── IP whitelist/blacklist
    ├── fail2ban + nginx
    └── Security headers
```

---

# Parte A — Installazione e struttura

---

## A1. Installazione nginx

```bash
# Ubuntu/Debian — repo ufficiale nginx
curl -fsSL https://nginx.org/keys/nginx_signing.key \
    | gpg --dearmor | tee /usr/share/keyrings/nginx-archive-keyring.gpg > /dev/null

echo "deb [signed-by=/usr/share/keyrings/nginx-archive-keyring.gpg] \
    https://nginx.org/packages/ubuntu $(lsb_release -cs) nginx" \
    > /etc/apt/sources.list.d/nginx.list

apt update && apt install nginx

# RHEL/Fedora
dnf install nginx

# Gestione
systemctl enable --now nginx
nginx -t            # verifica configurazione
nginx -s reload     # ricarica senza fermare

# Struttura directory
ls /etc/nginx/
# nginx.conf          — configurazione master
# conf.d/             — snippet globali
# sites-available/    — virtual host disponibili (Debian style)
# sites-enabled/      — virtual host attivi (symlink)
# snippets/           — frammenti riusabili
```

---

## A2. nginx.conf principale

```nginx
# /etc/nginx/nginx.conf

user www-data;
worker_processes auto;           # auto = numero CPU
pid /run/nginx.pid;
error_log /var/log/nginx/error.log warn;

events {
    worker_connections 1024;     # connessioni per worker
    multi_accept on;
    use epoll;                   # Linux: usa epoll
}

http {
    # Tipi MIME
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging strutturato
    log_format json escape=json
        '{"time":"$time_iso8601",'
        '"ip":"$remote_addr",'
        '"method":"$request_method",'
        '"uri":"$uri",'
        '"status":$status,'
        '"bytes":$body_bytes_sent,'
        '"referer":"$http_referer",'
        '"ua":"$http_user_agent",'
        '"request_time":$request_time}';

    access_log /var/log/nginx/access.log json;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    server_tokens off;           # non rivelare versione nginx

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css application/json
               application/javascript text/xml
               application/xml image/svg+xml;
    gzip_min_length 1000;
    gzip_comp_level 6;

    # Buffer sizes
    client_max_body_size 50M;
    client_body_buffer_size 128k;
    proxy_buffer_size 4k;
    proxy_buffers 4 32k;

    # Include virtual host
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
```

---

# Parte B — Virtual Host e SSL

---

## B1. Virtual host HTTPS

```nginx
# /etc/nginx/sites-available/esempio.it

# Redirect HTTP → HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name esempio.it www.esempio.it;

    # Let's Encrypt challenge
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;

    server_name esempio.it www.esempio.it;

    # Certificati TLS
    ssl_certificate /etc/letsencrypt/live/esempio.it/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/esempio.it/privkey.pem;

    # Configurazione TLS moderna (Mozilla SSL Generator)
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers off;

    # HSTS (6 mesi, includiSubdomains, preload)
    add_header Strict-Transport-Security "max-age=15768000; includeSubDomains; preload" always;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /etc/letsencrypt/live/esempio.it/chain.pem;
    resolver 1.1.1.1 8.8.8.8 valid=300s;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;

    # Root e file statici
    root /var/www/esempio.it;
    index index.html index.php;

    # Logging
    access_log /var/log/nginx/esempio.it-access.log json;
    error_log /var/log/nginx/esempio.it-error.log warn;

    location / {
        try_files $uri $uri/ =404;
    }

    # Cache file statici
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Certbot per Let's Encrypt
apt install certbot python3-certbot-nginx

# Ottieni certificato
certbot --nginx -d esempio.it -d www.esempio.it

# Rinnovo automatico (certbot installa il timer)
systemctl list-timers | grep certbot
# Oppure manualmente:
certbot renew --dry-run   # test
certbot renew             # rinnova

# Verifica configurazione SSL
nginx -t
systemctl reload nginx
openssl s_client -connect esempio.it:443 -servername esempio.it < /dev/null
```

> **Analogia:** nginx è come un receptionist professionale di un palazzo di uffici. L'HTTP→HTTPS redirect è il cartello che dice "Uso le scale sicure (HTTPS)". Il virtual host è il pannello delle campane — in base al nome sul campanello, il receptionist sa a quale ufficio portare il visitatore. Il reverse proxy è quando il receptionist instrada il visitatore verso un collega specializzato nel backend.

---

# Parte C — Reverse Proxy e Load Balancing

---

## C1. Reverse proxy per applicazione

```nginx
# /etc/nginx/conf.d/upstream-app.conf

# Upstream: pool di server backend
upstream app_backend {
    # Round-robin (default)
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;

    # Opzioni per server
    # server backup.interno.it backup;    # usato solo se gli altri sono down
    # server 10.0.0.5 weight=3;          # 3x il traffico degli altri
    # server 10.0.0.6 max_fails=3 fail_timeout=30s;

    keepalive 32;    # mantieni 32 connessioni aperte
}

server {
    listen 443 ssl;
    server_name api.esempio.it;
    # ... ssl config ...

    location / {
        proxy_pass http://app_backend;

        # Headers per il backend
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout
        proxy_connect_timeout 10s;
        proxy_read_timeout 60s;
        proxy_send_timeout 60s;

        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Endpoint health check (non proxyato)
    location /nginx-health {
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
```

---

# Parte D — Rate Limiting e Sicurezza

---

## D1. Rate limiting

```nginx
# In nginx.conf, blocco http:
# Zona rate limiting: 10MB per zone = ~160k IP
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
limit_conn_zone $binary_remote_addr zone=conn:10m;

# In server block:
location /api/ {
    # Max 10 req/s con burst di 20 (20 extra senza ritardo)
    limit_req zone=api burst=20 nodelay;
    limit_conn conn 10;          # max 10 connessioni contemporanee

    proxy_pass http://app_backend;
}

location /api/auth/login {
    # Login: 1 req/s, strict
    limit_req zone=login burst=5;

    proxy_pass http://app_backend;
}

# Blocca IP specifici
location / {
    deny 1.2.3.4;           # blocca IP singolo
    deny 10.0.0.0/8;        # blocca subnet
    allow 192.168.1.0/24;   # permetti solo LAN
    allow all;
}
```

---

## D2. Caching

```nginx
# Cache per proxy
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=app_cache:10m
    max_size=1g inactive=60m use_temp_path=off;

server {
    location /api/public/ {
        proxy_cache app_cache;
        proxy_cache_valid 200 1m;   # cache 200 per 1 minuto
        proxy_cache_valid 404 1m;
        proxy_cache_use_stale error timeout updating;
        proxy_cache_lock on;

        add_header X-Cache-Status $upstream_cache_status;
        proxy_pass http://app_backend;
    }
}
```

---

# Parte E — Riepilogo

## Configurazione minima per produzione

```bash
# 1. Installa nginx
apt install nginx certbot python3-certbot-nginx

# 2. Configura virtual host
nano /etc/nginx/sites-available/miosito.it

# 3. Attiva
ln -s /etc/nginx/sites-available/miosito.it /etc/nginx/sites-enabled/
nginx -t && nginx -s reload

# 4. SSL
certbot --nginx -d miosito.it

# 5. Verifica
curl -I https://miosito.it
openssl s_client -connect miosito.it:443 < /dev/null
```

## Test SSL score

```bash
# Test online: ssllabs.com/ssltest
# Test locale:
testssl.sh miosito.it
# oppure
nmap --script ssl-enum-ciphers -p 443 miosito.it
```

## Prossimi passi

- `tutorial_linux_28_nginx.md` — nginx configurazione avanzata (WebSockets, HTTP/3)
- `tutorial_linux_18_database.md` — PostgreSQL amministrazione
