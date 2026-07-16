# Tutorial Linux 28 — nginx Configurazione Avanzata: HTTP/3, WebSockets, Caching

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** nginx avanzato, HTTP/3 QUIC, WebSocket, proxy cache, Lua, WAF ModSecurity
> **Prerequisiti:** `tutorial_linux_17_web_server.md`
> **Durata stimata:** 14-18 ore

---

## Mappa concettuale

```
nginx Avanzato
│
├── Protocolli moderni
│   ├── HTTP/2 (TLS)
│   ├── HTTP/3 / QUIC (UDP)
│   └── WebSocket upgrade
│
├── Caching avanzato
│   ├── proxy_cache — cache backend response
│   ├── FastCGI cache — cache PHP
│   ├── Micro-caching (1s)
│   └── Cache bypass + purge
│
├── Load balancing avanzato
│   ├── least_conn
│   ├── ip_hash (sticky session)
│   ├── hash $request_uri
│   └── Upstream health check (nginx-plus o ngx_upstream_check)
│
├── Lua scripting (OpenResty)
│   ├── ngx.var, ngx.req
│   ├── Autenticazione custom
│   └── Rate limiting avanzato
│
└── Sicurezza
    ├── ModSecurity WAF
    ├── Geo blocking
    └── Bot detection
```

---

# Parte A — HTTP/3 e WebSocket

---

## A1. HTTP/3 con QUIC

```nginx
# nginx 1.25+ supporta HTTP/3 nativo

server {
    # HTTP/1.1 + HTTP/2 su TCP
    listen 443 ssl;
    http2 on;

    # HTTP/3 su UDP
    listen 443 quic reuseport;

    server_name esempio.it;

    ssl_certificate /etc/letsencrypt/live/esempio.it/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/esempio.it/privkey.pem;

    # Abilita HTTP/3 — annuncia al client via header
    add_header Alt-Svc 'h3=":443"; ma=86400';

    # QUIC specifico
    quic_retry on;
    quic_gso on;        # Generic Segmentation Offload (kernel 4.18+)

    location / {
        proxy_pass http://backend;
        # Forza HTTP/1.1 verso backend (standard)
        proxy_http_version 1.1;
    }
}
```

---

## A2. WebSocket proxy

```nginx
# WebSocket richiede upgrade della connessione HTTP → WebSocket

upstream ws_backend {
    server 127.0.0.1:3000;
    server 127.0.0.1:3001;
    keepalive 64;
}

server {
    listen 443 ssl;
    server_name ws.esempio.it;
    # ssl config ...

    # Map per gestire upgrade WebSocket
    map $http_upgrade $connection_upgrade {
        default upgrade;
        ''      close;
    }

    location /ws/ {
        proxy_pass http://ws_backend;
        
        # WebSocket upgrade headers
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        
        # Headers standard
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout lunghi per WebSocket (connessione persistente)
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
        proxy_connect_timeout 10s;
        
        # No buffering per WebSocket
        proxy_buffering off;
    }

    location / {
        # HTTP normale verso stesso backend
        proxy_pass http://ws_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";  # keep-alive per pool
    }
}
```

---

# Parte B — Caching avanzato

---

## B1. Proxy cache con micro-caching

```nginx
# In nginx.conf (blocco http)
# Cache per API con micro-caching (cache 1 secondo)
proxy_cache_path /var/cache/nginx/api
    levels=1:2
    keys_zone=api_cache:10m
    max_size=1g
    inactive=10s
    use_temp_path=off;

# Cache per contenuto statico (cache lunga)
proxy_cache_path /var/cache/nginx/static
    levels=1:2
    keys_zone=static_cache:50m
    max_size=10g
    inactive=60d
    use_temp_path=off;

server {
    # ...

    # API: micro-cache (1 secondo)
    # Assorbe burst, protegge backend da thundering herd
    location /api/ {
        proxy_cache api_cache;
        proxy_cache_valid 200 1s;
        proxy_cache_valid 404 10s;
        
        # Chiave cache
        proxy_cache_key "$scheme$request_method$host$request_uri";
        
        # Non mettere in cache se autenticato
        proxy_cache_bypass $http_authorization;
        proxy_no_cache $http_authorization;
        
        # Usa cache stale durante aggiornamento (no downtime)
        proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
        proxy_cache_lock on;
        proxy_cache_lock_timeout 5s;
        
        # Header per debug
        add_header X-Cache-Status $upstream_cache_status;
        
        proxy_pass http://api_backend;
    }

    # Contenuto statico: cache lunga
    location /static/ {
        proxy_cache static_cache;
        proxy_cache_valid 200 7d;
        
        # Ignora header no-cache dal backend
        proxy_ignore_headers Cache-Control Expires;
        
        # Ignora header Set-Cookie
        proxy_hide_header Set-Cookie;
        proxy_ignore_headers Set-Cookie;
        
        add_header X-Cache-Status $upstream_cache_status;
        add_header Cache-Control "public, max-age=604800, immutable";
        
        proxy_pass http://static_backend;
    }
}
```

---

## B2. Cache purge

```bash
# nginx non ha purge nativo (disponibile in nginx-plus o via modulo)
# Metodo 1: ngx_cache_purge module (compilato da sorgente)

location ~ /purge(/.*) {
    # Solo da IP admin
    allow 127.0.0.1;
    allow 10.0.0.0/8;
    deny all;
    
    proxy_cache_purge api_cache "$scheme$request_method$host$1";
}

# Metodo 2: PURGE method custom
map $request_method $purge_method {
    PURGE 1;
    default 0;
}

server {
    location /api/ {
        proxy_cache api_cache;
        proxy_cache_purge $purge_method;
        # ...
    }
}

# Richiesta purge
curl -X PURGE http://server/api/endpoint
```

---

# Parte C — Load balancing avanzato

---

## C1. Algoritmi e health check

```nginx
upstream api_backend {
    # Algoritmi disponibili:
    # (nessuno) = round-robin (default)
    # least_conn = backend con meno connessioni attive
    # ip_hash = sticky session per IP
    # hash $var = sticky per variabile custom
    # random = casuale

    least_conn;     # migliore per request di durata variabile

    server 10.0.0.10:8000 weight=3;     # 3x traffico
    server 10.0.0.11:8000;
    server 10.0.0.12:8000 backup;       # solo se gli altri down

    # max_fails e fail_timeout (passive health check)
    server 10.0.0.13:8000 max_fails=3 fail_timeout=30s;

    # Keepalive verso backend
    keepalive 32;
}

# Sticky session con hash
upstream sessions {
    hash $remote_addr consistent;    # consistent = meno rimescolamento se backend cambia
    server 10.0.0.10:8000;
    server 10.0.0.11:8000;
}

# Con cookie (richiede ngx_http_upstream_hash_module)
upstream by_cookie {
    hash $cookie_session_id;
    server 10.0.0.10:8000;
    server 10.0.0.11:8000;
}
```

---

# Parte D — Sicurezza avanzata

---

## D1. Rate limiting granulare

```nginx
# http block
# Rate limit per IP
limit_req_zone $binary_remote_addr zone=global:10m rate=100r/s;

# Rate limit per IP + URI
limit_req_zone "$binary_remote_addr$request_uri" zone=per_path:10m rate=10r/s;

# Rate limit per JWT user (se usi JWT)
map $http_authorization $user_id {
    default "anon";
    "~^Bearer\s+(.+)" $1;
}
limit_req_zone $user_id zone=per_user:10m rate=60r/m;

server {
    # Rate limit globale
    limit_req zone=global burst=200 nodelay;

    location /api/public/ {
        limit_req zone=per_path burst=20;
        proxy_pass http://backend;
    }

    location /api/v1/ {
        # Rate limit per utente autenticato
        limit_req zone=per_user burst=10;
        proxy_pass http://backend;
    }

    location /api/auth/login {
        # Login: molto più stretto
        limit_req zone=global burst=5;
        limit_req_status 429;
        proxy_pass http://backend;
    }
}
```

---

## D2. Geo blocking

```nginx
# http block
geoip2 /etc/nginx/GeoLite2-Country.mmdb {
    auto_reload 60m;
    $geoip2_country_code country iso_code;
}

# Blocca paesi specifici
map $geoip2_country_code $allow_country {
    default yes;
    CN no;   # China
    RU no;   # Russia
    KP no;   # North Korea
}

server {
    if ($allow_country = no) {
        return 403 "Accesso non disponibile nella tua regione.";
    }
}

# Installazione database GeoIP
apt install geoipupdate
cat > /etc/GeoIP.conf << 'EOF'
AccountID 123456
LicenseKey CHIAVE_MAXMIND
EditionIDs GeoLite2-Country GeoLite2-City
EOF
geoipupdate
```

---

# Parte E — Riepilogo

## Headers sicurezza moderni

```nginx
server {
    # Sicurezza HTTP
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
    
    # CSP (personalizza per la tua app)
    add_header Content-Security-Policy 
        "default-src 'self'; 
         script-src 'self' 'nonce-$request_id';
         style-src 'self';
         img-src 'self' data: https:;
         font-src 'self';
         connect-src 'self' https://api.esempio.it;
         frame-ancestors 'none';" always;

    # Rimuovi header che rivelano info server
    server_tokens off;
    more_clear_headers Server;
    more_clear_headers X-Powered-By;
}
```

## Prossimi passi

- `tutorial_linux_29_postgresql.md` — PostgreSQL avanzato
- `tutorial_linux_17_web_server.md` — nginx fondamentali
