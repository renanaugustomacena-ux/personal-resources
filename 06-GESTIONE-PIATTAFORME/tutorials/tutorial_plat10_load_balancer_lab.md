# Tutorial: Load Balancer e Reverse Proxy — HAProxy, Nginx, Traefik — Lab Pratico

> **Documento di riferimento:** `10-load-balancer-reverse-proxy.md`
> **Dominio:** Gestione Piattaforme — Networking e Bilanciamento
> **Ambito:** L4 vs L7 load balancing, HAProxy 3.x (bilanciamento TCP e HTTP, health check, statistiche), Nginx 1.27 come reverse proxy e load balancer, Traefik 3.x su Docker (service discovery automatico), TLS termination con certificati auto-firmati, rate limiting, algoritmi di bilanciamento (round-robin, least-connections, IP-hash), pattern architetturali multi-tier
> **Durata lab:** 5-6 ore
> **Livello:** Intermedio — richiede conoscenza base di HTTP e reti
> **Prerequisiti:** Docker Engine 29.x con Docker Compose, openssl (per certificati TLS)
> **Ambiente:** Docker Compose con 3 app di backend (Flask) + HAProxy + Nginx + Traefik come frontend alternativi

---

## Lab Environment Setup

```bash
# === VERIFICA PREREQUISITI LOAD BALANCER LAB ===
echo "=== CHECK PREREQUISITI ==="

docker --version && echo "[OK] Docker disponibile" || echo "[FAIL] Docker richiesto"
docker compose version && echo "[OK] Docker Compose disponibile" || echo "[FAIL] Compose richiesto"
openssl version && echo "[OK] openssl disponibile" || echo "[INFO] openssl per TLS (opzionale)"

# Porte necessarie libere
for port in 80 443 8080 8443 8404; do
  ss -tlnp 2>/dev/null | grep -q ":${port} " && \
    echo "[WARN] Porta ${port} occupata" || echo "[OK] Porta ${port} libera"
done

echo ""
echo "=== SETUP DIRECTORY LAB ==="
mkdir -p ~/lb-lab/{backends,haproxy,nginx,traefik,certs}
cd ~/lb-lab

echo "[OK] Directory lab: ~/lb-lab"
```

### Architettura del Lab

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      LOAD BALANCER LAB                                    │
│                                                                          │
│  CLIENT                                                                  │
│    │                                                                     │
│    ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  LOAD BALANCER (una delle tre opzioni):                        │     │
│  │                                                                 │     │
│  │  HAProxy :80/:8404(stats)   ← configurazione statica, potente │     │
│  │  Nginx   :80/:443           ← versatile, cache, SSL            │     │
│  │  Traefik :80/:443/:8080(UI) ← auto-discovery Docker           │     │
│  └─────────────────┬───────────────────────────────────────────────┘     │
│                    │  Round-robin / Least-conn / IP-hash                  │
│          ┌─────────┼─────────┐                                           │
│          ▼         ▼         ▼                                           │
│  ┌─────────────┐ ┌───────┐ ┌───────┐                                    │
│  │ backend-1   │ │ back2 │ │ back3 │  Flask app Python :5000            │
│  │ :5001       │ │ :5002 │ │ :5003 │  (simulano 3 istanze app)         │
│  └─────────────┘ └───────┘ └───────┘                                    │
└──────────────────────────────────────────────────────────────────────────┘
```

### App Backend di Demo

```bash
cd ~/lb-lab/backends

# App Flask che identifica su quale istanza siamo (per vedere il bilanciamento)
cat > app.py << 'PYTHON'
"""App backend di demo per il lab load balancer."""
import os, time, random
from flask import Flask, jsonify, request

app = Flask(__name__)

BACKEND_ID = os.environ.get("BACKEND_ID", "unknown")
BACKEND_REGION = os.environ.get("BACKEND_REGION", "eu-west-1")

@app.route('/health')
def health():
    return jsonify({"status": "ok", "backend": BACKEND_ID})

@app.route('/')
@app.route('/api/data')
def data():
    # Simulare latenza variabile (realistica)
    time.sleep(random.uniform(0.01, 0.05))
    return jsonify({
        "backend": BACKEND_ID,
        "region": BACKEND_REGION,
        "request_id": request.headers.get("X-Request-Id", "none"),
        "client_ip": request.headers.get("X-Forwarded-For", request.remote_addr),
        "timestamp": time.time()
    })

@app.route('/api/slow')
def slow():
    """Endpoint lento per testare timeout e circuit breaker."""
    time.sleep(float(request.args.get('delay', 3)))
    return jsonify({"backend": BACKEND_ID, "type": "slow"})

@app.route('/api/error')
def error():
    """Endpoint che restituisce errori (per testare health check)."""
    return jsonify({"error": "Simulated error", "backend": BACKEND_ID}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
PYTHON

cat > Dockerfile << 'EOF'
FROM python:3.12-slim
RUN useradd -m -u 1000 appuser
WORKDIR /app
RUN pip install --no-cache-dir flask==3.1.0
COPY app.py .
USER 1000
EXPOSE 5000
CMD ["python", "app.py"]
EOF

# Build backend image
docker build -t backend-app:latest .
echo "[OK] Immagine backend costruita"
```

---

## PART A: FONDAMENTI — L4 vs L7 Load Balancing

> Un load balancer è come un addetto allo smistamento posta in un grande ufficio.
> La differenza tra L4 e L7 è come due diversi livelli di lettura della busta:
> il bilanciatore L4 vede solo il mittente e il destinatario (indirizzo IP e porta)
> e smista la busta senza aprirla. Il bilanciatore L7 apre la busta, legge il
> contenuto, e può decidere dove mandarla in base al contenuto — per esempio,
> tutte le lettere con "fatture" vanno all'ufficio contabilità, tutte quelle con
> "reclami" vanno all'ufficio clienti.

---

### Concetto A1: Differenze L4 e L7

```
LOAD BALANCING L4 (Transport Layer — TCP/UDP):

  VEDE: indirizzo IP sorgente/destinazione, porta TCP/UDP
  NON VEDE: URL, header HTTP, cookie, body della richiesta
  
  ALGORITMI:
    Round-Robin:     1→server1, 2→server2, 3→server3, 4→server1...
    Least-Connections: nuove richieste → server con meno connessioni attive
    IP-Hash:         hash(IP_client) → stesso server sempre (sticky session)
    Random:          scelta casuale
  
  QUANDO USARE:
    - Database (MySQL, PostgreSQL, Redis) — protocollo binario, no HTTP
    - SMTP, FTP, SSH — protocolli non HTTP
    - Gaming UDP — bassa latenza, no HTTP
    - Alta frequenza: milioni di connessioni/sec
  
  ESEMPI: AWS NLB, HAProxy (mode tcp), nginx stream{}

LOAD BALANCING L7 (Application Layer — HTTP/HTTPS):

  VEDE: URL, header HTTP, cookie, TLS SNI, body (se analizzato)
  
  FUNZIONALITÀ AGGIUNTIVE:
    Path-based routing:    /api/* → backend-api, /web/* → backend-web
    Header-based routing:  X-User-Type: premium → backend-premium
    SSL termination:       decifrare HTTPS, parlare HTTP con i backend
    Compression:           gzip/brotli, riduce bandwidth
    Caching:               evita richieste duplicate al backend
    Rate limiting:         max N req/s per IP o API key
    WAF:                   blocca SQL injection, XSS
    Sticky session:        cookie → stesso backend (evitare se possibile!)
  
  QUANDO USARE:
    - Web application (HTTP/HTTPS)
    - Microservizi con routing URL diverso
    - Quando serve SSL termination, caching, rate limiting
  
  ESEMPI: AWS ALB, Nginx upstream{}, Traefik, HAProxy (mode http)

ARCHITETTURA TIPICA MULTI-TIER:

  Internet
     ↓
  AWS NLB/GCP Network LB (L4) — gestisce IP fisso, alta disponibilità
     ↓
  AWS ALB / Nginx (L7) — routing HTTP, SSL, rate limiting
     ↓
  Pod K8s / VM applicative — il codice vero
     ↓
  AWS RDS / Redis — database (L4 LB interno)
```

---

## PART B: HAPROXY — BILANCIAMENTO PROFESSIONALE

### Esercizio B1: HAProxy con Health Check e Statistiche

```bash
cd ~/lb-lab

# Avviare 3 backend
cat > compose-backends.yaml << 'EOF'
name: "lb-backends"
networks:
  lb-net:
    driver: bridge
services:
  backend-1:
    image: backend-app:latest
    container_name: backend-1
    environment:
      BACKEND_ID: "backend-1"
      BACKEND_REGION: "eu-west-1a"
    networks: [lb-net]
  backend-2:
    image: backend-app:latest
    container_name: backend-2
    environment:
      BACKEND_ID: "backend-2"
      BACKEND_REGION: "eu-west-1b"
    networks: [lb-net]
  backend-3:
    image: backend-app:latest
    container_name: backend-3
    environment:
      BACKEND_ID: "backend-3"
      BACKEND_REGION: "eu-west-1c"
    networks: [lb-net]
EOF
docker compose -f compose-backends.yaml up -d
echo "[OK] 3 backend avviati"

# ── Configurazione HAProxy ─────────────────────────────────────────────
cat > haproxy/haproxy.cfg << 'EOF'
# HAProxy 3.x — Configurazione completa per lab
# Documentazione: https://www.haproxy.org/download/3.0/doc/configuration.txt

global
    maxconn 50000               # max connessioni totali
    log stdout format raw local0 info
    user haproxy
    group haproxy
    daemon
    
    # Stats socket per monitoraggio runtime
    stats socket /run/haproxy.sock mode 660 level admin expose-fd listeners
    stats timeout 30s
    
    # Tuning performance
    nbthread 4                  # thread (uno per CPU core)
    cpu-map auto:1/1-4 0-3

defaults
    mode http                   # default: bilanciamento L7 HTTP
    log global
    option httplog              # log completo HTTP (metodo, URL, status, latenza)
    option dontlognull          # non loggare health check
    option forwardfor           # aggiunge X-Forwarded-For con IP client
    option redispatch           # se backend down, risparmi la richiesta su altro
    
    timeout connect  5s         # timeout connessione verso backend
    timeout client   30s        # timeout cliente inattivo
    timeout server   30s        # timeout risposta backend
    timeout http-request 10s    # tempo massimo per ricevere header HTTP
    
    retries 3                   # retry su backend non disponibile

# ── Frontend: punto di ingresso ──────────────────────────────────────
frontend web_frontend
    bind *:80
    
    # Rate limiting: max 100 richieste/secondo per IP
    # stick-table type ip size 100k expire 30s store conn_rate(1s),http_req_rate(1s)
    # http-request track-sc0 src
    # http-request deny deny_status 429 if { sc_http_req_rate(0) gt 100 }
    
    # Header sicurezza
    http-response set-header X-Frame-Options DENY
    http-response set-header X-Content-Type-Options nosniff
    http-response del-header Server              # nasconde versione HAProxy
    
    # Routing URL-based
    acl is_api path_beg /api
    acl is_health path /health
    
    use_backend api_servers if is_api
    use_backend health_backend if is_health
    default_backend web_servers

# ── Backend principale: round-robin con health check ─────────────────
backend web_servers
    balance roundrobin          # algoritmo: round-robin
    
    # Health check HTTP applicativo (verifica /health risponde 200)
    option httpchk GET /health
    http-check expect status 200
    
    # Sticky session (EVITARE se possibile — rompe la scalabilità orizzontale!)
    # cookie SERVERID insert indirect nocache
    
    # I tre server con weight (server con peso maggiore riceve più traffico)
    server backend-1 backend-1:5000 check inter 5s fall 2 rise 3
    server backend-2 backend-2:5000 check inter 5s fall 2 rise 3 weight 2
    server backend-3 backend-3:5000 check inter 5s fall 2 rise 3
    # fall 2: segnala DOWN dopo 2 health check falliti consecutivi
    # rise 3: torna UP dopo 3 health check riusciti consecutivi
    # inter 5s: health check ogni 5 secondi

# ── Backend API: least-connections ───────────────────────────────────
backend api_servers
    balance leastconn           # algoritmo: least-connections (per richieste lunghe)
    
    option httpchk GET /health
    http-check expect status 200
    
    # Timeout più lungo per API (potrebbero elaborare dati)
    timeout server 60s
    
    server backend-1 backend-1:5000 check inter 5s
    server backend-2 backend-2:5000 check inter 5s
    server backend-3 backend-3:5000 check inter 5s

# ── Backend health interno ────────────────────────────────────────────
backend health_backend
    server backend-1 backend-1:5000

# ── Statistiche HAProxy ───────────────────────────────────────────────
listen stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 5s
    stats realm "HAProxy Stats"
    stats auth admin:haproxy-lab-2026    # utente:password per la UI
    stats show-legends
    stats show-node
EOF

# Avviare HAProxy
cat >> compose-backends.yaml << 'EOF2'

  haproxy:
    image: haproxy:3.0-alpine
    container_name: haproxy
    ports:
      - "80:80"
      - "8404:8404"
    volumes:
      - ./haproxy/haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro
    networks: [lb-net]
    restart: unless-stopped
    depends_on: [backend-1, backend-2, backend-3]
EOF2

docker compose -f compose-backends.yaml up -d haproxy
sleep 5
echo "[OK] HAProxy avviato"

# Test bilanciamento
echo "Test round-robin (6 richieste):"
for i in $(seq 1 6); do
  BACKEND=$(curl -s "http://localhost/api/data" | python3 -c "import json,sys; print(json.load(sys.stdin).get('backend','?'))")
  echo "  Richiesta $i → $BACKEND"
done

# Statistiche HAProxy: http://localhost:8404/stats
echo "[INFO] Statistiche HAProxy: http://localhost:8404/stats (admin:haproxy-lab-2026)"
```

---

## PART C: NGINX — REVERSE PROXY E SSL TERMINATION

### Esercizio C1: Nginx con Load Balancing e HTTPS

```bash
cd ~/lb-lab

# Generare certificato TLS auto-firmato per il lab
mkdir -p certs
openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
  -keyout certs/lab.key \
  -out certs/lab.crt \
  -subj "/C=IT/ST=Lazio/L=Roma/O=Lab/CN=lab.local" \
  -addext "subjectAltName=DNS:lab.local,DNS:localhost,IP:127.0.0.1" \
  2>/dev/null

echo "[OK] Certificato TLS generato: certs/lab.crt, certs/lab.key"

# Configurazione Nginx
cat > nginx/nginx.conf << 'EOF'
# Nginx 1.27 — Reverse Proxy e Load Balancer

worker_processes auto;          # un processo per CPU core
worker_rlimit_nofile 65535;

events {
    worker_connections 4096;    # connessioni simultanee per worker
    use epoll;                  # event polling ottimale per Linux
    multi_accept on;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    # Logging strutturato (JSON per Loki/ELK)
    log_format json_combined escape=json
        '{"time":"$time_iso8601",'
        '"remote_addr":"$remote_addr",'
        '"method":"$request_method",'
        '"uri":"$request_uri",'
        '"status":$status,'
        '"body_bytes":$body_bytes_sent,'
        '"request_time":$request_time,'
        '"upstream_addr":"$upstream_addr",'
        '"upstream_response_time":"$upstream_response_time"}';
    
    access_log /var/log/nginx/access.log json_combined;
    error_log  /var/log/nginx/error.log warn;
    
    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 100;
    
    # Compressione gzip
    gzip on;
    gzip_types text/plain application/json application/javascript text/css;
    gzip_min_length 1024;
    
    # Nascondere versione Nginx
    server_tokens off;
    
    # ── Upstream: i server backend ───────────────────────────────────
    upstream backend_pool {
        # Algoritmo default: round-robin
        # Opzioni: least_conn; ip_hash;
        least_conn;
        
        server backend-1:5000 weight=1 max_fails=3 fail_timeout=30s;
        server backend-2:5000 weight=2 max_fails=3 fail_timeout=30s;
        server backend-3:5000 weight=1 max_fails=3 fail_timeout=30s;
        
        # Keepalive: riutilizza connessioni verso i backend
        keepalive 32;
    }
    
    # ── Rate limiting ─────────────────────────────────────────────────
    # Zona condivisa per rate limiting per IP
    limit_req_zone $binary_remote_addr zone=api_rate:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=web_rate:10m rate=30r/s;
    
    # ── Server HTTP: redirect a HTTPS ────────────────────────────────
    server {
        listen 80 default_server;
        server_name _;
        
        # Redirect permanente a HTTPS
        return 301 https://$host$request_uri;
    }
    
    # ── Server HTTPS ─────────────────────────────────────────────────
    server {
        listen 443 ssl http2 default_server;
        server_name lab.local localhost;
        
        # TLS Configuration
        ssl_certificate     /etc/nginx/certs/lab.crt;
        ssl_certificate_key /etc/nginx/certs/lab.key;
        ssl_protocols       TLSv1.2 TLSv1.3;
        ssl_ciphers         ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        ssl_session_cache   shared:SSL:10m;
        ssl_session_timeout 1d;
        ssl_session_tickets off;
        
        # HSTS: istruisce il browser a usare sempre HTTPS
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
        
        # Header sicurezza
        add_header X-Frame-Options DENY always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Content-Security-Policy "default-src 'self'" always;
        
        # ── Location API (con rate limiting) ─────────────────────────
        location /api/ {
            # Rate limiting: 10 req/s, burst di 20 con ritardo
            limit_req zone=api_rate burst=20 delay=10;
            
            proxy_pass http://backend_pool;
            
            # Header passati al backend
            proxy_set_header Host              $host;
            proxy_set_header X-Real-IP         $remote_addr;
            proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Request-Id      $request_id;  # ID univoco per correlazione log
            
            # Timeout
            proxy_connect_timeout 5s;
            proxy_send_timeout    30s;
            proxy_read_timeout    30s;
            
            # HTTP/1.1 per keepalive verso backend
            proxy_http_version 1.1;
            proxy_set_header Connection "";
        }
        
        # ── Location root ─────────────────────────────────────────────
        location / {
            limit_req zone=web_rate burst=50;
            
            proxy_pass http://backend_pool;
            
            proxy_set_header Host              $host;
            proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
        }
        
        # ── Health check interno ──────────────────────────────────────
        location = /nginx-health {
            access_log off;
            return 200 '{"status":"ok","service":"nginx-lb"}';
            add_header Content-Type application/json;
        }
    }
}
EOF

# Aggiungere Nginx al compose
cat >> compose-backends.yaml << 'NGINX'

  nginx:
    image: nginx:1.27-alpine
    container_name: nginx-lb
    ports:
      - "8080:80"
      - "8443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    networks: [lb-net]
    depends_on: [backend-1, backend-2, backend-3]
NGINX

docker compose -f compose-backends.yaml up -d nginx
sleep 5

# Test HTTP → HTTPS redirect
echo "Test redirect HTTP→HTTPS:"
curl -s -I http://localhost:8080/api/data | grep Location

# Test HTTPS (ignorando self-signed cert in lab)
echo "Test HTTPS:"
curl -sk "https://localhost:8443/api/data" | python3 -m json.tool

# Test rate limiting
echo "Test rate limiting (11 richieste veloci):"
for i in $(seq 1 11); do
  STATUS=$(curl -sk -o /dev/null -w "%{http_code}" "https://localhost:8443/api/data")
  echo -n "$STATUS "
done
echo ""
```

---

## PART D: TRAEFIK — SERVICE DISCOVERY AUTOMATICO

> **Analogia.** HAProxy e Nginx richiedono di configurare manualmente ogni server
> backend nel file di configurazione. Traefik è più moderno: si collega direttamente
> a Docker (o Kubernetes) e si aggiorna automaticamente quando i container
> partono o si fermano. È come avere un receptionist che sa sempre quante
> stanze sono disponibili in hotel senza che tu debba dirglielo — lo scopre
> da solo guardando il sistema di prenotazioni.

---

### Esercizio D1: Traefik con Routing Automatico

```bash
cd ~/lb-lab

mkdir -p traefik

# Configurazione statica Traefik (avvio)
cat > traefik/traefik.yml << 'EOF'
# Traefik 3.x — configurazione statica

api:
  dashboard: true         # UI web su :8080
  insecure: true          # Solo per lab! In produzione: autenticazione

log:
  level: INFO
  format: json

accessLog:
  format: json
  fields:
    headers:
      defaultMode: keep
      names:
        Authorization: redact    # Non loggare header Authorization

# Provider Docker: Traefik si connette al socket Docker
providers:
  docker:
    exposedByDefault: false      # Solo container con label traefik.enable=true
    network: lb-net

# Entrypoints (porte di ascolto)
entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
  
  websecure:
    address: ":443"

# Certificati TLS
tls:
  certificates:
    - certFile: /certs/lab.crt
      keyFile: /certs/lab.key
EOF

# Aggiungere Traefik al compose con label sui backend
cat > compose-traefik.yaml << 'EOF'
name: "lb-traefik"

networks:
  lb-net:
    external: true
    name: lb-backends_lb-net

services:
  traefik:
    image: traefik:v3.2
    container_name: traefik
    command:
      - "--configFile=/etc/traefik/traefik.yml"
    ports:
      - "8880:80"
      - "8843:443"
      - "8880:8080"   # Dashboard (dev only)
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro   # Docker discovery
      - ./traefik/traefik.yml:/etc/traefik/traefik.yml:ro
      - ./certs:/certs:ro
    networks: [lb-net]

  # Backend con label Traefik per configurazione automatica
  backend-traefik-1:
    image: backend-app:latest
    container_name: backend-traefik-1
    environment:
      BACKEND_ID: "traefik-backend-1"
    networks: [lb-net]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.app.rule=Host(`localhost`)"
      - "traefik.http.routers.app.entrypoints=websecure"
      - "traefik.http.routers.app.tls=true"
      - "traefik.http.services.app.loadbalancer.server.port=5000"
      - "traefik.http.services.app.loadbalancer.healthcheck.path=/health"
      - "traefik.http.services.app.loadbalancer.healthcheck.interval=5s"
      # Rate limiting middleware
      - "traefik.http.middlewares.rate-limit.ratelimit.average=10"
      - "traefik.http.middlewares.rate-limit.ratelimit.burst=20"
      - "traefik.http.routers.app.middlewares=rate-limit"

  backend-traefik-2:
    image: backend-app:latest
    container_name: backend-traefik-2
    environment:
      BACKEND_ID: "traefik-backend-2"
    networks: [lb-net]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.app.rule=Host(`localhost`)"
      - "traefik.http.services.app.loadbalancer.server.port=5000"

  backend-traefik-3:
    image: backend-app:latest
    container_name: backend-traefik-3
    environment:
      BACKEND_ID: "traefik-backend-3"
    networks: [lb-net]
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.app.rule=Host(`localhost`)"
      - "traefik.http.services.app.loadbalancer.server.port=5000"
EOF

docker compose -f compose-traefik.yaml up -d
sleep 8

echo "[INFO] Traefik Dashboard: http://localhost:8880/dashboard/ (nota la /)
echo "[INFO] Test HTTPS: curl -sk https://localhost:8843/"

# Test bilanciamento automatico Traefik
for i in $(seq 1 6); do
  BACKEND=$(curl -sk "https://localhost:8843/api/data" | \
    python3 -c "import json,sys; print(json.load(sys.stdin).get('backend','?'))")
  echo "  Richiesta $i → $BACKEND"
done
```

---

## PART E: ALGORITMI DI BILANCIAMENTO A CONFRONTO

### Esercizio E1: Verificare gli Algoritmi

```bash
cd ~/lb-lab

# Creare script di confronto algoritmi
cat > scripts/test-algorithms.sh << 'SCRIPT'
#!/bin/bash
# Confronto algoritmi di bilanciamento

echo "=== TEST ALGORITMI DI BILANCIAMENTO ==="

# Test Round-Robin (HAProxy default)
echo ""
echo "ROUND-ROBIN (distribuzione uniforme):"
echo "Inviando 9 richieste su HAProxy..."
declare -A round_robin_count
for i in $(seq 1 9); do
  BACKEND=$(curl -s "http://localhost/api/data" | \
    python3 -c "import json,sys; print(json.load(sys.stdin).get('backend','?'))")
  round_robin_count[$BACKEND]=$((${round_robin_count[$BACKEND]:-0} + 1))
done
for backend in "${!round_robin_count[@]}"; do
  echo "  $backend: ${round_robin_count[$backend]} richieste"
done
echo "Atteso: distribuzione uniforme ~3:3:3 (o proporzionale ai weight)"

# Test Least-Connections (simulazione: richieste lunghe e corte miste)
echo ""
echo "LEAST-CONNECTIONS (Nginx):"
echo "Inviando richieste miste (alcune lente) su Nginx..."
# Prima un slow request in background
curl -sk "https://localhost:8443/api/slow?delay=2" &
sleep 0.1
# Poi richieste normali — dovrebbero andare agli altri backend
for i in $(seq 1 4); do
  BACKEND=$(curl -sk "https://localhost:8443/api/data" | \
    python3 -c "import json,sys; print(json.load(sys.stdin).get('backend','?'))")
  echo "  Richiesta $i → $BACKEND (backend con meno connessioni)"
done
wait  # attendi il slow request

# Test IP-Hash (sticky session)
echo ""
echo "IP-HASH (stesso client → stesso backend):"
cat << 'INFO'
Per testare ip_hash: configurare upstream { ip_hash; ... } in nginx.conf
La stessa IP → sempre stesso backend (utile per sessioni senza Redis)
SCONSIGLIATO: rompe lo scaling orizzontale. Usare sessioni esterne (Redis).
INFO

SCRIPT

bash scripts/test-algorithms.sh
```

---

## PART F: MONITORING E HEALTH CHECK

### Esercizio F1: Health Check Avanzati

```bash
# Simulare un backend che va down e vedere il failover

echo "=== TEST FAILOVER AUTOMATICO ==="

# Mostrare stato prima
echo "Stato backend PRIMA del failover:"
for i in $(seq 1 3); do
  BACKEND=$(curl -s "http://localhost/api/data" | \
    python3 -c "import json,sys; print(json.load(sys.stdin).get('backend','?'))")
  echo "  $BACKEND"
done

# Fermare backend-3
docker stop backend-3
echo ""
echo "[SIM] backend-3 fermato (simula crash)"
sleep 8  # attendi che HAProxy rilevi il down (2 health check falliti × 5s = 10s)

echo "Stato backend DOPO failover (solo backend-1 e backend-2):"
for i in $(seq 1 6); do
  BACKEND=$(curl -s "http://localhost/api/data" | \
    python3 -c "import json,sys; print(json.load(sys.stdin).get('backend','?'))")
  echo "  $BACKEND"
done
echo "→ backend-3 non appare più (HAProxy lo ha rimosso automaticamente)"

# Riavviare backend-3
docker start backend-3
echo ""
echo "[SIM] backend-3 riavviato — attendo che torni healthy..."
sleep 20  # 3 health check riusciti × 5s = 15s

echo "Stato dopo recovery:"
for i in $(seq 1 6); do
  BACKEND=$(curl -s "http://localhost/api/data" | \
    python3 -c "import json,sys; print(json.load(sys.stdin).get('backend','?'))")
  echo "  $BACKEND"
done
echo "→ backend-3 torna nel pool (HAProxy lo reintegra automaticamente)"

# Statistiche HAProxy via socket (runtime API)
echo ""
echo "Statistiche HAProxy (via stats socket):"
echo "show stat" | docker exec -i haproxy socat - /run/haproxy.sock 2>/dev/null | \
  cut -d',' -f1,2,5,6,7,8,18,19 | \
  grep -v "^#" | column -s',' -t | head -10 || \
  echo "[INFO] Statistiche grafiche: http://localhost:8404/stats"
```

---

## Conclusioni e Prossimi Passi

```
LOAD BALANCER E REVERSE PROXY — RIEPILOGO:

L4 VS L7:
  ✓ L4 (TCP): veloce, trasparente, database, gaming, SMTP
  ✓ L7 (HTTP): routing URL, SSL termination, caching, rate limiting
  ✓ Architettura tipica: L4 cloud (NLB/Network LB) → L7 (Nginx/HAProxy) → backend

HAPROXY:
  ✓ backend: group server with health check (fall/rise/inter)
  ✓ frontend: ACL per routing URL-based
  ✓ balance: roundrobin, leastconn, source (IP hash)
  ✓ stats: UI ricca a :8404/stats
  ✓ Runtime API via socket: show stat, enable/disable server

NGINX (reverse proxy):
  ✓ upstream: pool di server con weight e max_fails
  ✓ proxy_pass: delega a upstream pool
  ✓ limit_req_zone: rate limiting per IP
  ✓ ssl_protocols TLSv1.2 TLSv1.3: configurazione TLS moderna
  ✓ gzip: compressione risposta

TRAEFIK:
  ✓ Configurazione via label Docker (zero config manuale)
  ✓ Service discovery automatico: nuovo container → routing automatico
  ✓ Dashboard UI: topologia e stato
  ✓ Let's Encrypt integrato: certificati automatici in produzione

ALGORITMI DI BILANCIAMENTO:
  ✓ Round-Robin: distribuzione uniforme, ideale per request di durata simile
  ✓ Least-Connections: manda al server con meno connessioni attive
                       (ideale per richieste di durata variabile)
  ✓ IP-Hash: stesso client → stesso server (sticky session senza cookie)
             SCONSIGLIATO: usare Redis per sessioni esterne
  ✓ Random: shuffle casuale (non usare senza motivo specifico)

HEALTH CHECK:
  ✓ TCP check: verifica solo che la porta sia aperta (troppo superficiale)
  ✓ HTTP check GET /health: verifica risposta applicativa (raccomandato)
  ✓ fall 2 rise 3: parametri ragionevoli per failover rapido e recovery conservativo
  ✓ L'app deve avere /health che verifica tutte le sue dipendenze (DB, cache)

SICUREZZA:
  ✓ TLS 1.2+: mai TLS 1.0/1.1 (deprecati)
  ✓ server_tokens off: non esporre versione nginx
  ✓ Header sicurezza: X-Frame-Options, X-Content-Type-Options, CSP
  ✓ Rate limiting: protezione DoS e brute force
  ✓ HSTS: istruisce browser a non usare mai HTTP
```

**Prossimi tutorial:**
- `tutorial_plat11_database_management_lab.md` — PostgreSQL HA, PgBouncer, backup
- `tutorial_plat16_api_gateway_lab.md` — Kong Gateway, autenticazione JWT

```bash
# Pulizia lab
docker compose -f compose-backends.yaml down -v
docker compose -f compose-traefik.yaml down -v
docker rmi backend-app:latest 2>/dev/null
rm -rf ~/lb-lab

echo "[OK] Lab Load Balancer completato"
```

---

> **Nota versioni:** Tutorial validato con HAProxy 3.0.x, Nginx 1.27.x (luglio 2025), Traefik 3.2.x.
> HAProxy 3.0 (giugno 2024): nuovo default socket di management, rimozione opzioni deprecate SSL.
> Nginx: stable branch 1.26.x, mainline 1.27.x — entrambe supportate in produzione.
> Traefik 3.x (2024): rimozione CRD v1alpha1, migrazione a v1, HTTP/3 stabile.
> Per certificati produzione: usare cert-manager (K8s) o Let's Encrypt con Traefik/Nginx ACME.
