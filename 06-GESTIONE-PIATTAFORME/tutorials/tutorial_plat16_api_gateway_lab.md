# Tutorial: API Gateway — Kong DB-less, Rate Limiting, JWT e Observability

> **Documento di riferimento:** `16-api-gateway.md`
> **Dominio:** Gestione Piattaforme — Architetture Avanzate
> **Ambito:** Kong Gateway 3.x DB-less mode, plugin rate-limiting e JWT, Traefik come API gateway, versioning API via header, distributed tracing integrazione, OWASP API Top 10
> **Durata lab:** 5-6 ore
> **Livello:** Avanzato — richiede Docker, Python 3.10+, curl/httpie
> **Prerequisiti:** Docker Engine 29.x, Python 3.10+ con Flask, curl disponibile
> **Ambiente:** Kong Gateway 3.x via Docker Compose (DB-less), backend Flask Python, Prometheus metrics

---

## Lab Environment Setup

```bash
# === VERIFICA PREREQUISITI API GATEWAY LAB ===
echo "=== PREREQUISITI ==="

docker --version && echo "[OK] Docker" || echo "[FAIL] Docker richiesto"
docker compose version && echo "[OK] Docker Compose" || echo "[FAIL] Compose richiesto"
python3 --version && echo "[OK] Python" || echo "[FAIL] Python richiesto"
curl --version | head -1 && echo "[OK] curl" || echo "[FAIL] curl richiesto"

pip3 install flask==3.1.0 pyjwt==2.10.1 2>/dev/null && echo "[OK] Flask + PyJWT" || \
  echo "[INFO] Installare: pip3 install flask pyjwt"

mkdir -p ~/gateway-lab/{kong,backend,jwt,scripts}
cd ~/gateway-lab

echo "[OK] Directory lab: ~/gateway-lab"
```

### Architettura API Gateway

```
                        CLIENT
                          │
                          ▼
                ┌─────────────────┐
                │   KONG GATEWAY  │  :8000 (HTTP) / :8443 (HTTPS)
                │                 │  :8001 Admin API
                │  Plugin Stack:  │
                │  ├── rate-limit │  ← blocca >10 req/min
                │  ├── jwt-auth   │  ← valida Bearer token
                │  └── prometheus │  ← espone metriche /metrics
                └────────┬────────┘
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
    /api/v1/users  /api/v1/orders  /api/v2/users
          │              │              │
    backend-users  backend-orders  backend-users-v2
    (Flask :5001)  (Flask :5002)   (Flask :5003)
```

---

## PART A: FONDAMENTI — Cos'è un API Gateway

> Un API Gateway è il "receptionist" di un edificio aziendale.
> Chiunque voglia parlare con un ufficio interno deve passare per lui.
> Il receptionist controlla il badge (autenticazione JWT),
> tiene traccia di quante volte qualcuno ha bussato oggi (rate limiting),
> e instrada le persone all'ufficio giusto (routing).
> Senza receptionist, ogni ufficio dovrebbe fare tutto da solo —
> e ogni ufficio avrebbe il suo sistema di badge incompatibile con gli altri.

---

### Concetto A1: Kong Gateway Architettura

```
KONG GATEWAY — DUE MODALITÀ:

1. DB MODE (PostgreSQL):
   - Configurazione persistente nel database
   - Admin API per modifiche runtime
   - Richiede PostgreSQL separato
   - Pro: configurazione dinamica senza restart
   - Contro: complessità operativa, stato nel DB

2. DB-LESS MODE (dichiarativo — NOSTRO LAB):
   - Configurazione in file YAML (kong.yaml)
   - Ricarica a caldo: PUT /config all'Admin API
   - Nessun DB necessario
   - Pro: GitOps-friendly, immutabile, semplice
   - Contro: nessuna modifica runtime senza push YAML
   - Usato in produzione con ArgoCD/Flux per GitOps

COMPONENTI:
  Services:  il backend che Kong chiama (upstream)
  Routes:    le regole di routing (path, header, method)
  Plugins:   funzionalità applicate a Service o Route
  Consumers: client identificati (per rate limit per-user)

OWASP API TOP 10 — COSA MITIGARE CON KONG:
  API1: Broken Object Level Authorization → JWT + claim validation
  API2: Broken Authentication → JWT plugin, rate limit on /login
  API4: Unrestricted Resource Consumption → rate-limit plugin
  API6: Unrestricted Access to Sensitive Business Flows → rate-limit
  API8: Security Misconfiguration → CORS plugin, HTTPS enforcement
  API10: Unsafe Consumption of APIs → request-validator plugin
```

---

## PART B: BACKEND FLASK PER IL LAB

### Esercizio B1: Backend Services

```bash
cd ~/gateway-lab

# Backend Users v1
cat > backend/users_v1.py << 'PYTHON'
"""Backend: Users API v1 — risponde a Kong sulle porte 5001."""
import os
from flask import Flask, jsonify, request

app = Flask(__name__)
VERSION = "v1"
SERVICE = "users"

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": SERVICE, "version": VERSION})

@app.route("/api/v1/users")
def list_users():
    return jsonify({
        "version": VERSION,
        "users": [
            {"id": 1, "name": "Alice Rossi", "email": "alice@example.com"},
            {"id": 2, "name": "Bob Verdi", "email": "bob@example.com"},
        ],
        "upstream": os.environ.get("HOSTNAME", "localhost")
    })

@app.route("/api/v1/users/<int:user_id>")
def get_user(user_id: int):
    users = {
        1: {"id": 1, "name": "Alice Rossi", "email": "alice@example.com", "pii": True},
        2: {"id": 2, "name": "Bob Verdi", "email": "bob@example.com", "pii": True},
    }
    if user_id not in users:
        return jsonify({"error": "not found"}), 404
    return jsonify(users[user_id])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
PYTHON

# Backend Orders
cat > backend/orders_v1.py << 'PYTHON'
"""Backend: Orders API — risponde su porta 5002."""
import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "orders"})

@app.route("/api/v1/orders")
def list_orders():
    return jsonify({
        "orders": [
            {"id": 101, "user_id": 1, "amount": 99.99, "status": "shipped"},
            {"id": 102, "user_id": 2, "amount": 249.00, "status": "pending"},
        ]
    })

@app.route("/api/v1/orders/<int:order_id>")
def get_order(order_id: int):
    if order_id not in (101, 102):
        return jsonify({"error": "not found"}), 404
    return jsonify({"id": order_id, "amount": 99.99, "status": "shipped"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
PYTHON

# Avviare i backend in background
python3 backend/users_v1.py &>/tmp/users.log &
python3 backend/orders_v1.py &>/tmp/orders.log &

sleep 2

# Verificare che i backend funzionino
curl -s http://localhost:5001/health && echo ""
curl -s http://localhost:5002/health && echo ""

echo "[OK] Backend Flask avviati"
```

---

### Esercizio B2: Kong Gateway DB-less

```bash
cd ~/gateway-lab

# Configurazione Kong DB-less (dichiarativa)
cat > kong/kong.yaml << 'EOF'
_format_version: "3.0"
_transform: true

services:
  # Service: Users API v1
  - name: users-service-v1
    url: http://host.docker.internal:5001
    connect_timeout: 5000
    read_timeout: 30000
    write_timeout: 30000
    retries: 3
    
    routes:
      - name: users-route-v1
        paths: ["/api/v1/users"]
        methods: ["GET", "POST"]
        strip_path: false
        
        plugins:
          # Plugin 1: rate limiting per route
          - name: rate-limiting
            config:
              minute: 10          # max 10 richieste per minuto per IP
              hour: 100           # max 100 per ora
              policy: local       # contatore locale (in-memory)
              hide_client_headers: false
          
          # Plugin 2: autenticazione JWT
          - name: jwt
            config:
              secret_is_base64: false
              claims_to_verify: ["exp"]   # verifica scadenza token
              key_claim_name: "iss"       # campo "iss" identifica il consumer
  
  # Service: Orders API
  - name: orders-service
    url: http://host.docker.internal:5002
    
    routes:
      - name: orders-route
        paths: ["/api/v1/orders"]
        methods: ["GET"]
        strip_path: false
        
        plugins:
          - name: rate-limiting
            config:
              minute: 20
              policy: local
          
          - name: jwt
            config:
              claims_to_verify: ["exp"]
              key_claim_name: "iss"
  
  # Service: Health Check (no auth)
  - name: health-service
    url: http://host.docker.internal:5001
    routes:
      - name: health-route
        paths: ["/health"]
        methods: ["GET"]

# Plugin globale: Prometheus metrics
plugins:
  - name: prometheus
    config:
      status_code_metrics: true
      latency_metrics: true
      upstream_health_metrics: true

# Consumers: client identificati per JWT
consumers:
  - username: app-frontend
    jwt_secrets:
      - key: "app-frontend"           # valore del campo "iss" nel JWT
        secret: "jwt-secret-frontend-lab-2026"
        algorithm: HS256
  
  - username: app-mobile
    jwt_secrets:
      - key: "app-mobile"
        secret: "jwt-secret-mobile-lab-2026"
        algorithm: HS256

EOF

# Docker Compose per Kong
cat > compose-kong.yaml << 'EOF'
name: "gateway-lab-kong"

services:
  kong:
    image: kong:3.8.0
    container_name: kong-gateway
    environment:
      KONG_DATABASE: "off"           # DB-less mode
      KONG_DECLARATIVE_CONFIG: /kong.yaml
      KONG_PROXY_ACCESS_LOG: /dev/stdout
      KONG_ADMIN_ACCESS_LOG: /dev/stdout
      KONG_PROXY_ERROR_LOG: /dev/stderr
      KONG_ADMIN_ERROR_LOG: /dev/stderr
      KONG_ADMIN_LISTEN: "0.0.0.0:8001"
      KONG_PROXY_LISTEN: "0.0.0.0:8000"
      KONG_LOG_LEVEL: info
    ports:
      - "8000:8000"   # Proxy HTTP
      - "8001:8001"   # Admin API
      - "8444:8444"   # Proxy HTTPS (opzionale)
    volumes:
      - ./kong/kong.yaml:/kong.yaml:ro
    extra_hosts:
      - "host.docker.internal:host-gateway"
    healthcheck:
      test: ["CMD", "kong", "health"]
      interval: 15s
      timeout: 10s
      retries: 5
EOF

docker compose -f compose-kong.yaml up -d

echo "Attendo Kong Gateway..."
until curl -s http://localhost:8001/ > /dev/null 2>&1; do sleep 3; done

echo "[OK] Kong Gateway 3.x avviato"
echo "[INFO] Admin API: http://localhost:8001"
echo "[INFO] Proxy: http://localhost:8000"

# Verificare la configurazione caricata
curl -s http://localhost:8001/services | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(f'Services configurati: {data[\"total\"]}')
for svc in data['data']:
    print(f'  - {svc[\"name\"]}: {svc[\"host\"]}:{svc[\"port\"]}')
"
```

---

## PART C: JWT AUTHENTICATION

### Esercizio C1: Generare e Usare JWT

```bash
cd ~/gateway-lab

# Script per generare JWT per il lab
cat > jwt/generate-token.py << 'PYTHON'
"""
Generatore JWT per il lab Kong Gateway.
In produzione: l'authorization server (Keycloak, Auth0) emette i token.
"""
import jwt
import time

# Configurazione (deve corrispondere al consumer in kong.yaml)
CONSUMERS = {
    "frontend": {
        "iss": "app-frontend",          # deve corrispondere a consumers[].jwt_secrets[].key
        "secret": "jwt-secret-frontend-lab-2026",
    },
    "mobile": {
        "iss": "app-mobile",
        "secret": "jwt-secret-mobile-lab-2026",
    }
}


def generate_token(consumer: str, extra_claims: dict | None = None, ttl_seconds: int = 3600) -> str:
    """Genera un JWT firmato con HMAC-SHA256."""
    if consumer not in CONSUMERS:
        raise ValueError(f"Consumer sconosciuto: {consumer}")
    
    conf = CONSUMERS[consumer]
    now = int(time.time())
    
    payload = {
        "iss": conf["iss"],           # issuer (usato da Kong per identificare il consumer)
        "sub": f"user-{consumer}",    # subject
        "iat": now,                   # issued at
        "exp": now + ttl_seconds,     # expiration
        "scope": "read:users read:orders",
    }
    
    if extra_claims:
        payload.update(extra_claims)
    
    token = jwt.encode(payload, conf["secret"], algorithm="HS256")
    return token


if __name__ == "__main__":
    print("=== TOKEN JWT PER LAB KONG GATEWAY ===\n")
    
    # Token valido (1 ora)
    frontend_token = generate_token("frontend", ttl_seconds=3600)
    print(f"Token FRONTEND (1h):\n{frontend_token}\n")
    
    mobile_token = generate_token("mobile", ttl_seconds=1800)
    print(f"Token MOBILE (30min):\n{mobile_token}\n")
    
    # Token scaduto (per testare il rifiuto)
    expired_token = generate_token("frontend", ttl_seconds=-1)
    print(f"Token SCADUTO:\n{expired_token}\n")
    
    # Decodificare e mostrare il payload (senza verifica firma — solo per debug)
    decoded = jwt.decode(frontend_token, options={"verify_signature": False})
    print(f"Payload decodificato: {decoded}")
PYTHON

python3 jwt/generate-token.py

echo ""
echo "=== COPIA IL TOKEN SOPRA PER I TEST SUCCESSIVI ==="
FRONTEND_TOKEN=$(python3 -c "
import jwt, time
payload = {'iss': 'app-frontend', 'sub': 'user-frontend', 'iat': int(time.time()), 'exp': int(time.time())+3600, 'scope': 'read:users'}
print(jwt.encode(payload, 'jwt-secret-frontend-lab-2026', algorithm='HS256'))
" 2>/dev/null)

echo ""
echo "=== TEST: SENZA TOKEN (deve fallire 401) ==="
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" \
  http://localhost:8000/api/v1/users

echo ""
echo "=== TEST: CON TOKEN VALIDO (deve passare 200) ==="
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -H "Authorization: Bearer ${FRONTEND_TOKEN}" \
  http://localhost:8000/api/v1/users

echo ""
echo "=== TEST: HEALTH ENDPOINT (no auth) ==="
curl -s -w "\nHTTP Status: %{http_code}\n" \
  http://localhost:8000/health
```

---

## PART D: RATE LIMITING E TEST DI CARICO

### Esercizio D1: Testare Rate Limiting

```bash
cd ~/gateway-lab

# Generare token per i test
FRONTEND_TOKEN=$(python3 -c "
import jwt, time
payload = {'iss': 'app-frontend', 'sub': 'user-1', 'iat': int(time.time()), 'exp': int(time.time())+3600}
print(jwt.encode(payload, 'jwt-secret-frontend-lab-2026', algorithm='HS256'))
" 2>/dev/null)

echo "=== TEST RATE LIMITING (10 req/min per /api/v1/users) ==="

# Inviare 12 richieste velocemente (la 11a e 12a devono essere bloccate)
SUCCESS=0
RATE_LIMITED=0
for i in $(seq 1 12); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer ${FRONTEND_TOKEN}" \
    http://localhost:8000/api/v1/users)
  
  if [ "$STATUS" = "200" ]; then
    SUCCESS=$((SUCCESS + 1))
    echo "  Richiesta $i: $STATUS [OK]"
  elif [ "$STATUS" = "429" ]; then
    RATE_LIMITED=$((RATE_LIMITED + 1))
    echo "  Richiesta $i: $STATUS [RATE LIMITED]"
  else
    echo "  Richiesta $i: $STATUS"
  fi
  
  sleep 0.1  # pausa minima
done

echo ""
echo "Risultato: ${SUCCESS} successi, ${RATE_LIMITED} bloccate da rate limit"
[ "$RATE_LIMITED" -gt 0 ] && echo "[OK] Rate limiting funziona!" || echo "[INFO] Potrebbe servire più velocità o meno delay"

echo ""
echo "=== HEADER RATE LIMIT NELLA RISPOSTA ==="
curl -sv -H "Authorization: Bearer ${FRONTEND_TOKEN}" \
  http://localhost:8000/api/v1/users 2>&1 | grep -i "ratelimit"
```

---

## PART E: AGGIORNAMENTO CONFIG DINAMICO

### Esercizio E1: Aggiornare Kong senza Restart

```bash
cd ~/gateway-lab

echo "=== AGGIORNAMENTO CONFIGURAZIONE KONG (DB-less) ==="

# In DB-less mode, aggiornare la config via PUT /config
# Questo simula il GitOps: commit su YAML → pipeline push config

# Aggiungere una route v2 con rate limit più alto
cat > kong/kong-v2.yaml << 'EOF'
_format_version: "3.0"
_transform: true

services:
  - name: users-service-v1
    url: http://host.docker.internal:5001
    routes:
      - name: users-route-v1
        paths: ["/api/v1/users"]
        methods: ["GET", "POST"]
        strip_path: false
        plugins:
          - name: rate-limiting
            config:
              minute: 10
              policy: local
          - name: jwt
            config:
              claims_to_verify: ["exp"]
              key_claim_name: "iss"
  
  - name: orders-service
    url: http://host.docker.internal:5002
    routes:
      - name: orders-route
        paths: ["/api/v1/orders"]
        strip_path: false
        plugins:
          - name: rate-limiting
            config:
              minute: 20
              policy: local
          - name: jwt
            config:
              claims_to_verify: ["exp"]
              key_claim_name: "iss"
  
  # NUOVO: Route v2 con header-based versioning
  - name: users-service-v2
    url: http://host.docker.internal:5001
    routes:
      - name: users-route-v2-header
        paths: ["/api/users"]   # stesso path del v2
        methods: ["GET"]
        strip_path: false
        headers:
          X-API-Version: ["2"]    # routing basato su header (best practice vs URL)
        plugins:
          - name: rate-limiting
            config:
              minute: 50    # v2 ha rate limit più alto
              policy: local
          - name: jwt
            config:
              claims_to_verify: ["exp"]
              key_claim_name: "iss"

  - name: health-service
    url: http://host.docker.internal:5001
    routes:
      - name: health-route
        paths: ["/health"]
        methods: ["GET"]

plugins:
  - name: prometheus
    config:
      status_code_metrics: true
      latency_metrics: true

consumers:
  - username: app-frontend
    jwt_secrets:
      - key: "app-frontend"
        secret: "jwt-secret-frontend-lab-2026"
        algorithm: HS256
  
  - username: app-mobile
    jwt_secrets:
      - key: "app-mobile"
        secret: "jwt-secret-mobile-lab-2026"
        algorithm: HS256
EOF

# Push nuova configurazione a Kong senza restart
curl -s -X POST \
  -H "Content-Type: application/json" \
  --data-urlencode "config@kong/kong-v2.yaml" \
  http://localhost:8001/config | python3 -c "
import json, sys
resp = json.load(sys.stdin)
print('Configurazione aggiornata:')
print(f'  Services: {len(resp.get(\"services\", []))}')
print(f'  Routes: {len(resp.get(\"routes\", []))}')
" 2>/dev/null || \
  echo "[INFO] Per aggiornare la config: PUT /config con YAML"

echo ""
echo "[OK] Configurazione Kong aggiornata"

echo ""
echo "=== TEST VERSIONING VIA HEADER ==="
FRONTEND_TOKEN=$(python3 -c "
import jwt, time
payload = {'iss': 'app-frontend', 'sub': 'user-1', 'iat': int(time.time()), 'exp': int(time.time())+3600}
print(jwt.encode(payload, 'jwt-secret-frontend-lab-2026', algorithm='HS256'))
" 2>/dev/null)

# Richiesta senza header versione → v1
curl -s -w " | HTTP: %{http_code}\n" \
  -H "Authorization: Bearer ${FRONTEND_TOKEN}" \
  http://localhost:8000/api/v1/users | head -c 100

# Richiesta con header X-API-Version: 2 → route v2
curl -s -w " | HTTP: %{http_code}\n" \
  -H "Authorization: Bearer ${FRONTEND_TOKEN}" \
  -H "X-API-Version: 2" \
  http://localhost:8000/api/users 2>/dev/null | head -c 100
```

---

## PART F: METRICHE PROMETHEUS

### Esercizio F1: Monitoring Kong

```bash
echo "=== METRICHE PROMETHEUS DI KONG ==="

# Kong espone metriche Prometheus su /metrics (plugin prometheus abilitato)
curl -s http://localhost:8000/metrics 2>/dev/null | head -30 || \
  curl -s http://localhost:8001/metrics 2>/dev/null | head -30

echo ""
echo "=== PromQL QUERIES UTILI PER KONG ==="

cat << 'PROMQL'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KONG GATEWAY — METRICHE PROMETHEUS KEY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REQUEST RATE per service:
  rate(kong_http_requests_total[5m])

REQUEST RATE per status code (errori 5xx):
  rate(kong_http_requests_total{code=~"5.."}[5m])

LATENCY p99 per upstream:
  histogram_quantile(0.99, rate(kong_request_latency_ms_bucket[5m]))

RATE LIMIT violations (429):
  rate(kong_http_requests_total{code="429"}[5m])

UPSTREAM HEALTH:
  kong_upstream_target_health

ERROR RATE globale:
  sum(rate(kong_http_requests_total{code=~"[45].."}[5m])) /
  sum(rate(kong_http_requests_total[5m]))

ALERT RACCOMANDATI:
  - alert: KongHighErrorRate
    expr: >
      sum(rate(kong_http_requests_total{code=~"5.."}[5m])) /
      sum(rate(kong_http_requests_total[5m])) > 0.05
    annotations:
      summary: "Kong error rate > 5% in 5 minuti"
  
  - alert: KongHighLatency
    expr: >
      histogram_quantile(0.99, rate(kong_request_latency_ms_bucket[5m])) > 1000
    annotations:
      summary: "Kong p99 latency > 1 secondo"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROMQL
```

---

## Conclusioni e Prossimi Passi

```
API GATEWAY — RIEPILOGO:

KONG DB-LESS:
  ✓ Configurazione YAML dichiarativa — GitOps friendly
  ✓ Aggiornamento senza restart: POST /config all'Admin API
  ✓ Plugins: rate-limiting, jwt, prometheus, CORS, request-validator
  ✓ Consumers: client identificati con propri segreti JWT e rate limit

JWT AUTH:
  ✓ Plugin jwt: valida firma + claims (exp obbligatorio)
  ✓ key_claim_name: "iss" — mappa il token al Consumer
  ✓ In produzione: auth server (Keycloak/Auth0) emette i token
  ✓ Kong valida solo la firma — non emette token

RATE LIMITING:
  ✓ Per route: diversi limiti per endpoint diversi
  ✓ Policies: local (in-memory), redis (distribuito per più nodi)
  ✓ Headers risposta: X-RateLimit-Remaining, X-RateLimit-Reset
  ✓ HTTP 429 Too Many Requests quando supera il limite

VERSIONING API:
  ✓ Header-based (X-API-Version): preferito (URL immutabile)
  ✓ URL-based (/api/v1/, /api/v2/): semplice ma accoppia URL a versione
  ✓ Accept-header (/api/users, Accept: application/vnd.api+json;v=2)
  ✓ Kong supporta routing su header — ideale per versioning

OWASP API TOP 10 — MITIGAZIONI:
  ✓ API1: BOLA → validazione claims JWT (sub, scope)
  ✓ API2: Auth broken → JWT plugin obbligatorio su tutte le route
  ✓ API4: Resource exhaustion → rate-limit plugin
  ✓ API6: Sensitive flows → rate-limit specifica per /login, /forgot-password
  ✓ API8: Misconfiguration → CORS plugin con origin allowlist

ALTERNATIVE KONG:
  Traefik 3.x: ottimo per K8s-native, discovery automatico via annotation
  Nginx: ultra-performante, meno funzionalità built-in
  Envoy Gateway: K8s Gateway API standard, futuro di K8s networking
  AWS API Gateway: serverless, integrazione Lambda, pay-per-use
  Azure APIM: enterprise, developer portal, policy XML
```

```bash
# Pulizia
docker compose -f compose-kong.yaml down -v
pkill -f "users_v1.py" 2>/dev/null
pkill -f "orders_v1.py" 2>/dev/null
rm -rf ~/gateway-lab
echo "[OK] Lab API Gateway completato"
```

---

> **Nota versioni:** Kong Gateway 3.8.x (Community Edition, licenza Apache 2.0).
> Kong Enterprise aggiunge: Developer Portal, Analytics, RBAC admin UI, FIPS 140-2.
> Alternativa open: Apache APISIX 3.x (CNCF graduated 2024), Envoy Gateway 1.1 (K8s Gateway API v1.1 stable).
> Kubernetes Gateway API v1.1: stabile da maggio 2024 — rimpiazza gradualmente Ingress API.
> Kong 3.8 (settembre 2024): expressions router GA, plugin ordering, WebAssembly plugins beta.
