---
corso: "Gestione Piattaforme e DevOps"
fase: "7 — Architetture Avanzate"
modulo: 16
titolo: "API Gateway"
versione: "Kong 3.x; AWS API Gateway v2; Apigee X; Tyk 5.x"
livello: "Avanzato"
prerequisiti: ["09-service-mesh", "10-load-balancer-reverse-proxy", "13-sicurezza-piattaforme"]
obiettivi:
  - "Confrontare architetture e deployment model di Kong, Apigee, AWS API Gateway e Tyk"
  - "Configurare rate limiting, autenticazione OAuth2/JWT e mutual TLS su un API gateway"
  - "Implementare versioning delle API tramite header e canary release"
  - "Integrare l'API gateway con tracing distribuito e metriche Prometheus"
  - "Progettare un GraphQL gateway con persisted queries e depth limiting"
tag: [api-gateway, kong, apigee, tyk, rate-limiting, oauth2, graphql, versioning]
---

# API Gateway — Documentazione Completa

> **Modulo 16** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> Al completamento di questo modulo sarai in grado di:
> 1. Confrontare architetture e deployment model di Kong, Apigee, AWS API Gateway e Tyk.
> 2. Configurare rate limiting, autenticazione OAuth2/JWT e mutual TLS su un API gateway.
> 3. Implementare versioning delle API tramite header e canary release.
> 4. Integrare l'API gateway con tracing distribuito e metriche Prometheus.
> 5. Progettare un GraphQL gateway con persisted queries e depth limiting.

## Idee guida

1. **Kong, Apigee, AWS API Gateway, Tyk: top players.**
2. **Rate limit + auth + observability in singolo layer.**
3. **GraphQL gateway diverso da REST gateway.** Persisted queries, depth limit.
4. **Versioning API: header > URL.** Cleaner.


## Indice

1. [Panoramica e Concetti Fondamentali](#1-panoramica-e-concetti-fondamentali)
2. [Kong Gateway](#2-kong-gateway)
3. [Kong — Plugin Ecosystem](#3-kong--plugin-ecosystem)
4. [Traefik come API Gateway](#4-traefik-come-api-gateway)
5. [AWS API Gateway](#5-aws-api-gateway)
6. [Azure API Management (APIM)](#6-azure-api-management-apim)
7. [GCP API Gateway e Apigee](#7-gcp-api-gateway-e-apigee)
8. [Authentication e Authorization](#8-authentication-e-authorization)
9. [Rate Limiting e Throttling](#9-rate-limiting-e-throttling)
10. [Request/Response Transformation](#10-requestresponse-transformation)
11. [Monitoring e Troubleshooting](#11-monitoring-e-troubleshooting)
12. [Best Practices](#12-best-practices)
13. [Apache APISIX](#13-apache-apisix)
14. [Tyk Gateway](#14-tyk-gateway)
15. [Envoy Gateway e Kubernetes Gateway API](#15-envoy-gateway-e-kubernetes-gateway-api)
16. [GraphQL Federation Gateway](#16-graphql-federation-gateway)
17. [AI Gateway e LLM Proxy](#17-ai-gateway-e-llm-proxy)
18. [Streaming: WebSocket e Server-Sent Events](#18-streaming-websocket-e-server-sent-events)
19. [Sicurezza Avanzata — OWASP API Top 10 e Zero Trust](#19-sicurezza-avanzata--owasp-api-top-10-e-zero-trust)
20. [OpenAPI-First e Specification-Driven Gateway](#20-openapi-first-e-specification-driven-gateway)

---

## 1. Panoramica e Concetti Fondamentali

### Definizione di API Gateway

Un API Gateway e un componente infrastrutturale che funge da singolo punto di ingresso per tutte le richieste
dei client verso i servizi backend. Opera come intermediario tra i consumer delle API e i microservizi interni,
centralizzando funzionalita trasversali (cross-cutting concerns) che altrimenti dovrebbero essere implementate
in ogni singolo servizio.

A differenza di un semplice reverse proxy, l'API Gateway implementa logica applicativa specifica per la
gestione delle API: autenticazione, autorizzazione, rate limiting, trasformazione dei payload, aggregazione
delle risposte, versionamento e analytics.

### Differenze con Reverse Proxy e Load Balancer

| Componente | Funzione Primaria | Livello OSI | Consapevolezza API |
|---|---|---|---|
| Load Balancer | Distribuzione del traffico | L4 (TCP/UDP) o L7 (HTTP) | Nessuna |
| Reverse Proxy | Intermediazione richieste, TLS termination, caching | L7 (HTTP) | Limitata |
| API Gateway | Gestione completa del ciclo di vita delle API | L7 (HTTP/gRPC/WebSocket) | Completa |

Un load balancer distribuisce il traffico tra istanze identiche dello stesso servizio. Un reverse proxy
instrada le richieste verso backend differenti in base al path o all'host. Un API Gateway aggiunge a
queste capacita la gestione di autenticazione, rate limiting, trasformazione dei payload, versionamento
e monitoring specifico per API.

### Pattern Architetturali

**Gateway Routing** — Il gateway instrada le richieste al servizio backend appropriato in base a path, header,
query parameter o altri attributi della richiesta. Ogni rotta mappa a un servizio specifico.

**Gateway Aggregation** — Il gateway compone una singola risposta aggregando dati da piu servizi backend.
Il client effettua una sola richiesta, il gateway esegue fanout verso N servizi e assembla la risposta.
Riduce la chattiness tra client e backend, particolarmente utile per client mobile con latenza elevata.

**Gateway Offloading** — Il gateway assume responsabilita che altrimenti ricadrebbero sui singoli servizi:
TLS termination, autenticazione, rate limiting, caching, compressione, CORS, logging. I servizi backend
si concentrano esclusivamente sulla business logic.

### Responsabilita dell'API Gateway

**Authentication e Authorization** — Validazione dei token (JWT, OAuth2), verifica delle API key, integrazione
con identity provider esterni (OIDC), enforcement delle policy di accesso basate su ruoli o scope.

**Rate Limiting e Throttling** — Controllo della frequenza delle richieste per proteggere i servizi backend
dal sovraccarico. Implementazione di quote (giornaliere, mensili) e limiti burst per consumer, rotta o
globalmente.

**Request/Response Transformation** — Modifica degli header, riscrittura degli URL, trasformazione del body
(JSON verso XML, field mapping), validazione dello schema della richiesta, filtering dei campi nella risposta.

**Caching** — Cache delle risposte a livello di gateway per ridurre il carico sui servizi backend. Supporto
per cache-control header, invalidazione granulare, cache per consumer o per rotta.

**Logging e Monitoring** — Registrazione centralizzata di tutte le richieste API, metriche di performance
(latenza, throughput, error rate), distributed tracing, audit logging per compliance.

**Circuit Breaking** — Protezione dei servizi backend dal cascading failure. Quando un servizio backend
supera una soglia di errori, il circuit breaker si apre e il gateway restituisce immediatamente un errore
senza inoltrare la richiesta, dando al servizio tempo per recuperare.

### API Gateway nel Contesto Microservizi

In un'architettura a microservizi, l'API Gateway risolve il problema della complessita di comunicazione
tra client e servizi. Senza un gateway, un client deve conoscere gli indirizzi di tutti i servizi, gestire
autenticazione con ciascuno, e aggregare risposte da servizi multipli.

Il pattern Backend-for-Frontend (BFF) estende il concetto di API Gateway creando gateway specializzati
per diversi tipi di client: un BFF per l'applicazione web, uno per l'app mobile, uno per i partner esterni.
Ogni BFF ottimizza le API per le esigenze specifiche del proprio client.

### North-South vs East-West Traffic

**North-South traffic** — Traffico che attraversa il perimetro del cluster, tipicamente dal client esterno
verso i servizi interni. L'API Gateway gestisce primariamente questo tipo di traffico, applicando
autenticazione, rate limiting e trasformazioni al confine della rete.

**East-West traffic** — Traffico tra servizi interni al cluster. Gestito tipicamente da un service mesh
(Istio, Linkerd, Consul Connect) piuttosto che dall'API Gateway. Il service mesh fornisce mTLS,
load balancing, circuit breaking e observability per la comunicazione intra-cluster.

La separazione tra API Gateway (north-south) e service mesh (east-west) segue il principio della
separazione delle responsabilita. Alcuni prodotti (come Kong Mesh o Traefik con Consul) offrono
soluzioni integrate che coprono entrambi i flussi.

---

## 2. Kong Gateway

### Architettura

Kong Gateway e un API Gateway open-source costruito su Nginx e OpenResty (LuaJIT). L'architettura si
compone di due piani distinti:

**Data Plane** — Il componente che processa il traffico API. Riceve le richieste dai client, applica i plugin
configurati (autenticazione, rate limiting, trasformazioni) e inoltra le richieste ai servizi backend.
Il data plane e stateless: riceve la configurazione dal control plane e la mantiene in memoria.

**Control Plane** — Gestisce la configurazione del gateway. Espone l'Admin API per CRUD di servizi, rotte,
consumer e plugin. Memorizza la configurazione nel database (PostgreSQL o Cassandra) e la distribuisce
ai nodi del data plane.

**Database Mode** — Kong utilizza PostgreSQL (consigliato) o Cassandra per la persistenza della configurazione.
Ogni nodo data plane si connette al database per leggere la configurazione. Supporta clustering multi-nodo.

**DB-less Mode** — Kong carica la configurazione da un file YAML dichiarativo (kong.yml) senza necessita
di database. Ideale per ambienti immutabili e GitOps. La configurazione viene fornita all'avvio e puo
essere aggiornata tramite l'Admin API (endpoint /config).

**Hybrid Mode** — Combina control plane centralizzato (con database) e data plane distribuiti (senza database).
I data plane ricevono la configurazione dal control plane tramite connessione WebSocket con mTLS.
Modalita raccomandata per deployment in produzione.

### Installazione con Docker

```bash
# Creazione della rete Docker per Kong
docker network create kong-net

# Avvio di PostgreSQL per Kong
docker run -d --name kong-database \
  --network kong-net \
  -e "POSTGRES_USER=kong" \
  -e "POSTGRES_DB=kong" \
  -e "POSTGRES_PASSWORD=kong_password_secure" \
  -p 5432:5432 \
  postgres:15-alpine

# Migrazione del database
docker run --rm --network kong-net \
  -e "KONG_DATABASE=postgres" \
  -e "KONG_PG_HOST=kong-database" \
  -e "KONG_PG_USER=kong" \
  -e "KONG_PG_PASSWORD=kong_password_secure" \
  kong:3.6 kong migrations bootstrap

# Avvio di Kong Gateway
docker run -d --name kong-gateway \
  --network kong-net \
  -e "KONG_DATABASE=postgres" \
  -e "KONG_PG_HOST=kong-database" \
  -e "KONG_PG_USER=kong" \
  -e "KONG_PG_PASSWORD=kong_password_secure" \
  -e "KONG_PROXY_ACCESS_LOG=/dev/stdout" \
  -e "KONG_ADMIN_ACCESS_LOG=/dev/stdout" \
  -e "KONG_PROXY_ERROR_LOG=/dev/stderr" \
  -e "KONG_ADMIN_ERROR_LOG=/dev/stderr" \
  -e "KONG_ADMIN_LISTEN=0.0.0.0:8001" \
  -e "KONG_ADMIN_GUI_URL=http://localhost:8002" \
  -p 8000:8000 \
  -p 8443:8443 \
  -p 8001:8001 \
  -p 8002:8002 \
  kong:3.6
```

### Installazione su Kubernetes con Helm

```bash
# Aggiunta del repository Helm di Kong
helm repo add kong https://charts.konghq.com
helm repo update

# Installazione con Helm e valori personalizzati
helm install kong kong/ingress -n kong --create-namespace \
  --set gateway.proxy.type=LoadBalancer \
  --set gateway.admin.enabled=true \
  --set gateway.admin.type=ClusterIP \
  --set gateway.env.database=postgres \
  --set gateway.postgresql.enabled=true \
  --set gateway.postgresql.auth.username=kong \
  --set gateway.postgresql.auth.database=kong

# Verifica dello stato del deployment
kubectl get pods -n kong
kubectl get svc -n kong
```

### Configurazione Dichiarativa (kong.yml)

```yaml
# kong.yml — Configurazione declarativa DB-less
_format_version: "3.0"
_transform: true

services:
  - name: user-service
    url: http://user-api.internal:8080
    connect_timeout: 5000
    write_timeout: 10000
    read_timeout: 10000
    retries: 3
    routes:
      - name: user-routes
        paths:
          - /api/v1/users
        methods:
          - GET
          - POST
          - PUT
          - DELETE
        strip_path: false
        preserve_host: true
    plugins:
      - name: rate-limiting
        config:
          minute: 100
          policy: local
      - name: key-auth
        config:
          key_names:
            - X-API-Key
            - apikey

  - name: order-service
    url: http://order-api.internal:8080
    routes:
      - name: order-routes
        paths:
          - /api/v1/orders
        methods:
          - GET
          - POST
        strip_path: false
    plugins:
      - name: jwt
        config:
          claims_to_verify:
            - exp
            - nbf

upstreams:
  - name: user-api-upstream
    algorithm: round-robin
    hash_on: none
    healthchecks:
      active:
        healthy:
          interval: 10
          successes: 3
        unhealthy:
          interval: 5
          http_failures: 3
          tcp_failures: 3
          timeouts: 3
        http_path: /health
        timeout: 5
      passive:
        healthy:
          successes: 5
        unhealthy:
          http_failures: 5
          tcp_failures: 3
          timeouts: 3
    targets:
      - target: user-api-1.internal:8080
        weight: 100
      - target: user-api-2.internal:8080
        weight: 100

consumers:
  - username: mobile-app
    keyauth_credentials:
      - key: mobile-app-api-key-2024
    plugins:
      - name: rate-limiting
        config:
          minute: 500
          policy: local

  - username: partner-service
    keyauth_credentials:
      - key: partner-service-api-key-2024
    plugins:
      - name: rate-limiting
        config:
          minute: 1000
          policy: local
```

### Oggetti Core

**Services** — Rappresentano un servizio backend upstream. Definiscono protocollo, host, porta e path del
servizio. Ogni service puo avere piu routes associate.

**Routes** — Definiscono le regole di matching per le richieste in ingresso (path, host, header, metodo).
Una richiesta che corrisponde a una route viene instradata al service associato.

**Upstreams e Targets** — Un upstream rappresenta un cluster di backend con load balancing. I targets
sono le singole istanze del servizio backend. Supporta health checking attivo e passivo.

**Consumers** — Rappresentano i fruitori delle API. Ogni consumer puo avere credenziali associate
(API key, JWT, OAuth2) e configurazioni di plugin specifiche (rate limit personalizzato).

**Plugins** — Moduli che aggiungono funzionalita al gateway. Possono essere applicati globalmente,
per service, per route o per consumer.

### Admin API

```bash
# Verifica stato del gateway
curl -s http://localhost:8001/status | jq .

# Creazione di un service
curl -X POST http://localhost:8001/services \
  -H "Content-Type: application/json" \
  -d '{
    "name": "payment-service",
    "url": "http://payment-api.internal:8080",
    "connect_timeout": 5000,
    "read_timeout": 15000,
    "retries": 2
  }'

# Creazione di una route per il service
curl -X POST http://localhost:8001/services/payment-service/routes \
  -H "Content-Type: application/json" \
  -d '{
    "name": "payment-routes",
    "paths": ["/api/v1/payments"],
    "methods": ["GET", "POST"],
    "strip_path": false,
    "preserve_host": true
  }'

# Elenco di tutti i services
curl -s http://localhost:8001/services | jq '.data[] | {name, host, port}'

# Elenco di tutte le routes
curl -s http://localhost:8001/routes | jq '.data[] | {name, paths, methods}'

# Aggiunta di un consumer
curl -X POST http://localhost:8001/consumers \
  -H "Content-Type: application/json" \
  -d '{"username": "frontend-app"}'

# Abilitazione di un plugin su un service
curl -X POST http://localhost:8001/services/payment-service/plugins \
  -H "Content-Type: application/json" \
  -d '{
    "name": "rate-limiting",
    "config": {
      "minute": 60,
      "policy": "redis",
      "redis_host": "redis.internal",
      "redis_port": 6379
    }
  }'
```

### Kong Ingress Controller per Kubernetes

Kong Ingress Controller (KIC) integra Kong con l'Ingress API nativa di Kubernetes, permettendo di
configurare il gateway attraverso risorse Kubernetes standard e CRD.

```yaml
# KongIngress per configurazione avanzata del service
apiVersion: configuration.konghq.com/v1
kind: KongIngress
metadata:
  name: payment-config
  namespace: production
proxy:
  connect_timeout: 5000
  read_timeout: 15000
  write_timeout: 15000
  retries: 3
route:
  strip_path: false
  preserve_host: true
upstream:
  algorithm: round-robin
  hash_on: none
  healthchecks:
    active:
      healthy:
        interval: 10
        successes: 3
      unhealthy:
        interval: 5
        http_failures: 3
      http_path: /health
      timeout: 5

---
# Ingress resource con Kong annotations
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: payment-ingress
  namespace: production
  annotations:
    konghq.com/override: payment-config
    konghq.com/plugins: rate-limiting-payment,jwt-auth
spec:
  ingressClassName: kong
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /api/v1/payments
            pathType: Prefix
            backend:
              service:
                name: payment-service
                port:
                  number: 8080

---
# KongPlugin per rate limiting
apiVersion: configuration.konghq.com/v1
kind: KongPlugin
metadata:
  name: rate-limiting-payment
  namespace: production
config:
  minute: 100
  policy: redis
  redis_host: redis.production.svc.cluster.local
  redis_port: 6379
plugin: rate-limiting
```

---

## 3. Kong — Plugin Ecosystem

### Plugin di Autenticazione

Kong offre diversi plugin per l'autenticazione, ciascuno adatto a scenari differenti.

**Key Authentication** — Autenticazione basata su API key. Semplice da implementare, adatto per
comunicazione machine-to-machine o integrazione con partner.

```bash
# Abilitazione key-auth su un service
curl -X POST http://localhost:8001/services/user-service/plugins \
  -H "Content-Type: application/json" \
  -d '{
    "name": "key-auth",
    "config": {
      "key_names": ["X-API-Key", "apikey"],
      "key_in_header": true,
      "key_in_query": true,
      "key_in_body": false,
      "hide_credentials": true
    }
  }'

# Creazione di una API key per un consumer
curl -X POST http://localhost:8001/consumers/mobile-app/key-auth \
  -H "Content-Type: application/json" \
  -d '{"key": "secure-api-key-mobile-2024"}'
```

**JWT Authentication** — Validazione di JSON Web Token. Il client invia un JWT firmato nell'header
Authorization. Kong verifica la firma, la scadenza e i claim configurati.

```bash
# Abilitazione JWT su un service
curl -X POST http://localhost:8001/services/order-service/plugins \
  -H "Content-Type: application/json" \
  -d '{
    "name": "jwt",
    "config": {
      "claims_to_verify": ["exp", "nbf"],
      "key_claim_name": "iss",
      "header_names": ["Authorization"],
      "maximum_expiration": 3600,
      "run_on_preflight": true
    }
  }'

# Creazione delle credenziali JWT per un consumer
curl -X POST http://localhost:8001/consumers/frontend-app/jwt \
  -H "Content-Type: application/json" \
  -d '{
    "algorithm": "RS256",
    "key": "frontend-app-issuer",
    "rsa_public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqh...\n-----END PUBLIC KEY-----"
  }'
```

**OAuth 2.0** — Kong puo agire come OAuth 2.0 provider, gestendo il flusso completo di autorizzazione.

```bash
# Abilitazione OAuth2 su un service
curl -X POST http://localhost:8001/services/user-service/plugins \
  -H "Content-Type: application/json" \
  -d '{
    "name": "oauth2",
    "config": {
      "scopes": ["read", "write", "admin"],
      "mandatory_scope": true,
      "enable_client_credentials": true,
      "enable_authorization_code": true,
      "token_expiration": 7200,
      "refresh_token_ttl": 1209600,
      "accept_http_if_already_terminated": true
    }
  }'
```

**OpenID Connect (OIDC)** — Disponibile in Kong Enterprise. Integrazione con identity provider
esterni come Keycloak, Auth0, Azure AD, Okta.

```yaml
# Configurazione OIDC in kong.yml (Enterprise)
plugins:
  - name: openid-connect
    service: user-service
    config:
      issuer: https://keycloak.example.com/realms/production
      client_id:
        - kong-gateway
      client_secret:
        - ${OIDC_CLIENT_SECRET}
      auth_methods:
        - bearer
        - session
      scopes:
        - openid
        - profile
        - email
      consumer_claim:
        - sub
      consumer_by:
        - username
      login_redirect_uri:
        - https://api.example.com/callback
      logout_redirect_uri:
        - https://api.example.com/logged-out
      ssl_verify: true
      cache_ttl: 300
```

### Rate Limiting

```yaml
# Configurazione rate limiting in kong.yml
plugins:
  # Rate limiting globale
  - name: rate-limiting
    config:
      second: 50
      minute: 1000
      hour: 30000
      policy: redis
      redis_host: redis.internal
      redis_port: 6379
      redis_timeout: 2000
      redis_database: 0
      fault_tolerant: true
      hide_client_headers: false
      error_code: 429
      error_message: "Limite di richieste superato. Riprovare dopo il periodo indicato."

  # Rate limiting avanzato per consumer (Enterprise)
  - name: rate-limiting-advanced
    service: premium-api
    config:
      limit:
        - 100
        - 10000
      window_size:
        - 60
        - 3600
      identifier: consumer
      strategy: sliding
      sync_rate: 10
      redis:
        host: redis.internal
        port: 6379
```

### Request/Response Transformation

```bash
# Aggiunta di header alla richiesta upstream
curl -X POST http://localhost:8001/services/user-service/plugins \
  -H "Content-Type: application/json" \
  -d '{
    "name": "request-transformer",
    "config": {
      "add": {
        "headers": [
          "X-Request-Source:api-gateway",
          "X-Gateway-Version:kong-3.6"
        ],
        "querystring": ["gateway=true"]
      },
      "remove": {
        "headers": ["X-Internal-Only"]
      },
      "rename": {
        "headers": ["X-Old-Header:X-New-Header"]
      },
      "replace": {
        "headers": ["X-Forwarded-Proto:https"]
      }
    }
  }'

# Trasformazione della risposta
curl -X POST http://localhost:8001/services/user-service/plugins \
  -H "Content-Type: application/json" \
  -d '{
    "name": "response-transformer",
    "config": {
      "add": {
        "headers": [
          "X-Served-By:kong-gateway",
          "Strict-Transport-Security:max-age=63072000; includeSubDomains; preload"
        ]
      },
      "remove": {
        "headers": ["Server", "X-Powered-By"]
      }
    }
  }'
```

### Logging

```yaml
# Configurazione logging in kong.yml
plugins:
  # File logging
  - name: file-log
    config:
      path: /var/log/kong/api-access.log
      reopen: true

  # HTTP logging verso servizio centralizzato
  - name: http-log
    config:
      http_endpoint: https://log-collector.internal:9200/kong-logs/_doc
      method: POST
      timeout: 10000
      keepalive: 60000
      flush_timeout: 2
      retry_count: 3
      headers:
        Content-Type: application/json
        Authorization: "Basic ${LOG_COLLECTOR_AUTH}"

  # TCP logging verso Logstash
  - name: tcp-log
    config:
      host: logstash.internal
      port: 5044
      timeout: 10000
      keepalive: 60000
      tls: true

  # Prometheus metrics
  - name: prometheus
    config:
      per_consumer: true
      status_code_metrics: true
      latency_metrics: true
      bandwidth_metrics: true
      upstream_health_metrics: true

  # StatsD metrics
  - name: statsd
    config:
      host: statsd.internal
      port: 8125
      metrics:
        - name: request_count
          stat_type: counter
          sample_rate: 1
        - name: latency
          stat_type: timer
        - name: request_size
          stat_type: histogram
        - name: status_count
          stat_type: counter
          sample_rate: 1
```

### Security Plugins

```yaml
# Plugin di sicurezza in kong.yml
plugins:
  # CORS
  - name: cors
    service: public-api
    config:
      origins:
        - https://app.example.com
        - https://admin.example.com
      methods:
        - GET
        - POST
        - PUT
        - PATCH
        - DELETE
        - OPTIONS
      headers:
        - Accept
        - Authorization
        - Content-Type
        - X-API-Key
      exposed_headers:
        - X-RateLimit-Limit
        - X-RateLimit-Remaining
        - X-RateLimit-Reset
      credentials: true
      max_age: 3600
      preflight_continue: false

  # IP Restriction
  - name: ip-restriction
    service: admin-api
    config:
      allow:
        - 10.0.0.0/8
        - 172.16.0.0/12
        - 192.168.0.0/16
      deny:
        - 0.0.0.0/0
      status: 403
      message: "Accesso non consentito da questo indirizzo IP"

  # Bot Detection
  - name: bot-detection
    service: public-api
    config:
      allow:
        - googlebot
        - bingbot
      deny:
        - scrapy
        - wget

  # ACME (Let's Encrypt)
  - name: acme
    config:
      account_email: admin@example.com
      api_uri: https://acme-v02.api.letsencrypt.org/directory
      domains:
        - api.example.com
        - gateway.example.com
      storage: redis
      storage_config:
        redis:
          host: redis.internal
          port: 6379
      tos_accepted: true
```

### Custom Plugins

Kong supporta custom plugin in Lua (nativo), Go, Python e JavaScript (via plugin server).

```lua
-- custom-auth-validator/handler.lua
local BasePlugin = require "kong.plugins.base_plugin"
local CustomAuthValidator = BasePlugin:extend()

CustomAuthValidator.PRIORITY = 1000
CustomAuthValidator.VERSION = "1.0.0"

function CustomAuthValidator:new()
  CustomAuthValidator.super.new(self, "custom-auth-validator")
end

function CustomAuthValidator:access(conf)
  CustomAuthValidator.super.access(self)

  local auth_header = kong.request.get_header("Authorization")
  if not auth_header then
    return kong.response.exit(401, {
      message = "Token di autenticazione mancante"
    })
  end

  local token = auth_header:match("Bearer%s+(.+)")
  if not token then
    return kong.response.exit(401, {
      message = "Formato token non valido. Utilizzare: Bearer <token>"
    })
  end

  -- Validazione custom del token
  local ok, err = validate_token(token, conf)
  if not ok then
    kong.log.warn("Token validation failed: ", err)
    return kong.response.exit(403, {
      message = "Token non valido o scaduto"
    })
  end

  -- Propagazione dell'identita verso il backend
  kong.service.request.set_header("X-Authenticated-User", ok.sub)
  kong.service.request.set_header("X-User-Roles", table.concat(ok.roles, ","))
end

return CustomAuthValidator
```

---

## 4. Traefik come API Gateway

### Traefik oltre il Reverse Proxy

Traefik, nato come reverse proxy e load balancer per ambienti cloud-native, puo funzionare come
API Gateway grazie al sistema di middleware chain. I middleware vengono applicati sequenzialmente
alle richieste prima che raggiungano il servizio backend, implementando le funzionalita tipiche
di un API Gateway.

La differenza tra Traefik Proxy (open-source), Traefik Enterprise e Traefik Hub definisce il
livello di funzionalita disponibili:

- **Traefik Proxy** — Reverse proxy, load balancing, middleware base, auto-discovery dei servizi.
- **Traefik Enterprise** — Aggiunge distributed tracing, OIDC authentication, rate limiting
  avanzato, WAF, high availability.
- **Traefik Hub** — API management platform: API portal, access control, API versioning,
  analytics, monetizzazione.

### Middleware Chain

La catena di middleware definisce l'ordine di elaborazione delle richieste. Ogni middleware puo
modificare la richiesta, bloccarla o arricchirla con informazioni aggiuntive.

```yaml
# traefik-dynamic.yml — Configurazione middleware per API Gateway
http:
  # Definizione dei middleware
  middlewares:
    # Rate Limiting
    api-rate-limit:
      rateLimit:
        average: 100
        burst: 50
        period: 1m
        sourceCriterion:
          ipStrategy:
            depth: 1
          requestHeaderName: X-API-Key

    # Autenticazione BasicAuth
    api-basic-auth:
      basicAuth:
        users:
          - "admin:$apr1$H6uskkkW$IgXLP6ewTrSuBkTrqE8wj/"
          - "reader:$apr1$d9hr9HBB$4HxwgUir3HP4EsggP/QNo0"
        removeHeader: true

    # Autenticazione JWT (tramite ForwardAuth)
    jwt-auth:
      forwardAuth:
        address: http://auth-service:4000/verify
        trustForwardHeader: true
        authResponseHeaders:
          - X-User-Id
          - X-User-Roles
          - X-User-Email
        authResponseHeadersRegex: "^X-Auth-"
        authRequestHeaders:
          - Authorization
          - X-API-Key

    # Security Headers
    security-headers:
      headers:
        browserXssFilter: true
        contentTypeNosniff: true
        frameDeny: true
        stsIncludeSubdomains: true
        stsPreload: true
        stsSeconds: 63072000
        customResponseHeaders:
          X-Robots-Tag: "noindex, nofollow"
          Referrer-Policy: "strict-origin-when-cross-origin"
          Permissions-Policy: "camera=(), microphone=(), geolocation=()"
        contentSecurityPolicy: >-
          default-src 'self';
          script-src 'self' 'nonce-{random}';
          style-src 'self' 'unsafe-inline';
          img-src 'self' data:;
          font-src 'self';
          object-src 'none';
          frame-ancestors 'none';
          base-uri 'self';
          upgrade-insecure-requests

    # Circuit Breaker
    api-circuit-breaker:
      circuitBreaker:
        expression: "LatencyAtQuantileMS(50.0) > 1000 || NetworkErrorRatio() > 0.10 || ResponseCodeRatio(500, 600, 0, 600) > 0.25"
        checkPeriod: 10s
        fallbackDuration: 30s
        recoveryDuration: 60s

    # Retry
    api-retry:
      retry:
        attempts: 3
        initialInterval: 100ms

    # IP Whitelist
    admin-ip-whitelist:
      ipAllowList:
        sourceRange:
          - "10.0.0.0/8"
          - "172.16.0.0/12"
          - "192.168.0.0/16"
        ipStrategy:
          depth: 1

    # Strip Prefix
    strip-api-prefix:
      stripPrefix:
        prefixes:
          - "/api/v1"
          - "/api/v2"

    # Request Size Limit
    request-size-limit:
      buffering:
        maxRequestBodyBytes: 10485760  # 10 MB
        memRequestBodyBytes: 2097152   # 2 MB

    # Compress Response
    gzip-compress:
      compress:
        excludedContentTypes:
          - "text/event-stream"
        minResponseBodyBytes: 1024

  # Definizione dei router con middleware chain
  routers:
    # API pubblica con rate limiting e JWT
    public-api:
      rule: "Host(`api.example.com`) && PathPrefix(`/api/v1/public`)"
      service: public-service
      middlewares:
        - api-rate-limit
        - jwt-auth
        - security-headers
        - gzip-compress
      entryPoints:
        - websecure
      tls:
        certResolver: letsencrypt

    # API admin con IP whitelist e autenticazione
    admin-api:
      rule: "Host(`api.example.com`) && PathPrefix(`/api/v1/admin`)"
      service: admin-service
      middlewares:
        - admin-ip-whitelist
        - jwt-auth
        - api-rate-limit
        - security-headers
        - api-circuit-breaker
      entryPoints:
        - websecure
      tls:
        certResolver: letsencrypt
      priority: 100

    # Versione API v2 con canary
    api-v2-canary:
      rule: "Host(`api.example.com`) && PathPrefix(`/api/v2`) && Headers(`X-Canary`, `true`)"
      service: api-v2-service
      middlewares:
        - jwt-auth
        - security-headers
      entryPoints:
        - websecure
      tls:
        certResolver: letsencrypt
      priority: 200

  # Definizione dei servizi
  services:
    public-service:
      loadBalancer:
        servers:
          - url: "http://public-api-1:8080"
          - url: "http://public-api-2:8080"
        healthCheck:
          path: /health
          interval: 10s
          timeout: 5s
          hostname: public-api
        sticky:
          cookie:
            name: server_id
            secure: true
            httpOnly: true

    admin-service:
      loadBalancer:
        servers:
          - url: "http://admin-api:8080"
        healthCheck:
          path: /health
          interval: 15s
          timeout: 5s

    # Canary deployment con weighted services
    api-v2-service:
      weighted:
        services:
          - name: api-v2-stable
            weight: 90
          - name: api-v2-canary
            weight: 10

    api-v2-stable:
      loadBalancer:
        servers:
          - url: "http://api-v2-stable:8080"

    api-v2-canary:
      loadBalancer:
        servers:
          - url: "http://api-v2-canary:8080"
```

### ForwardAuth per External Authentication

ForwardAuth delega l'autenticazione a un servizio esterno. Traefik invia una subrequest al
servizio di autenticazione prima di inoltrare la richiesta al backend.

```yaml
# docker-compose.yml con Traefik e servizio di autenticazione
services:
  traefik:
    image: traefik:v3.1
    command:
      - "--api.insecure=false"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--accesslog=true"
      - "--accesslog.format=json"
      - "--metrics.prometheus=true"
      - "--metrics.prometheus.entryPoint=metrics"
      - "--entrypoints.metrics.address=:9100"
    ports:
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./letsencrypt:/letsencrypt"
    networks:
      - gateway-net

  auth-service:
    image: auth-service:latest
    labels:
      - "traefik.enable=false"
    environment:
      - JWT_SECRET=${JWT_SECRET}
      - ISSUER=api.example.com
    networks:
      - gateway-net

  user-api:
    image: user-api:latest
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.user-api.rule=Host(`api.example.com`) && PathPrefix(`/api/v1/users`)"
      - "traefik.http.routers.user-api.entrypoints=websecure"
      - "traefik.http.routers.user-api.tls.certresolver=letsencrypt"
      - "traefik.http.routers.user-api.middlewares=jwt-auth@file,api-rate-limit@file,security-headers@file"
      - "traefik.http.services.user-api.loadbalancer.server.port=8080"
      - "traefik.http.services.user-api.loadbalancer.healthcheck.path=/health"
      - "traefik.http.services.user-api.loadbalancer.healthcheck.interval=10s"
    networks:
      - gateway-net

networks:
  gateway-net:
    driver: bridge
```

### API Versioning con Routing

```yaml
# Configurazione per gestire multiple versioni API
http:
  routers:
    # Routing basato su header Accept-Version
    api-v1-header:
      rule: "Host(`api.example.com`) && Headers(`Accept-Version`, `v1`)"
      service: api-v1-service
      middlewares:
        - jwt-auth
      priority: 300

    api-v2-header:
      rule: "Host(`api.example.com`) && Headers(`Accept-Version`, `v2`)"
      service: api-v2-service
      middlewares:
        - jwt-auth
      priority: 300

    # Routing basato su path prefix
    api-v1-path:
      rule: "Host(`api.example.com`) && PathPrefix(`/api/v1`)"
      service: api-v1-service
      middlewares:
        - jwt-auth
        - strip-v1-prefix
      priority: 200

    api-v2-path:
      rule: "Host(`api.example.com`) && PathPrefix(`/api/v2`)"
      service: api-v2-service
      middlewares:
        - jwt-auth
        - strip-v2-prefix
      priority: 200

    # Default alla versione piu recente
    api-default:
      rule: "Host(`api.example.com`) && PathPrefix(`/api`)"
      service: api-v2-service
      middlewares:
        - jwt-auth
      priority: 100

  middlewares:
    strip-v1-prefix:
      stripPrefix:
        prefixes:
          - "/api/v1"
    strip-v2-prefix:
      stripPrefix:
        prefixes:
          - "/api/v2"
```

---

## 5. AWS API Gateway

### Tipi di API Gateway

AWS offre tre tipi di API Gateway, ciascuno ottimizzato per scenari differenti:

**REST API** — Il tipo originale, con funzionalita complete: request/response mapping templates (VTL),
request validation, caching, WAF integration, usage plans, API keys, canary deployment, private
API via VPC endpoint. Costo maggiore, latenza piu alta.

**HTTP API** — Versione semplificata e ottimizzata per performance. Supporta Lambda proxy, HTTP proxy,
JWT authorizer, OIDC, CORS automatico. Costo circa 70% inferiore rispetto a REST API. Non supporta
caching, WAF diretto, o mapping templates. Ideale per la maggior parte dei casi d'uso.

**WebSocket API** — Per comunicazione bidirezionale in tempo reale. Supporta route selection expression
basata su messaggi JSON, integrazione con Lambda, DynamoDB, HTTP, SNS.

| Funzionalita | REST API | HTTP API | WebSocket API |
|---|---|---|---|
| Lambda Integration | Si | Si (proxy only) | Si |
| HTTP Proxy | Si | Si | No |
| Request Validation | Si | No | No |
| Response Caching | Si | No | No |
| WAF Integration | Si | No | No |
| Usage Plans / API Keys | Si | No | No |
| Custom Domain | Si | Si | Si |
| Authorizers | IAM, Cognito, Lambda | JWT, IAM | IAM, Lambda |
| Costo per milione | ~$3.50 | ~$1.00 | ~$1.00 + connection |

### Stages e Deployment

```bash
# Creazione di una REST API
aws apigateway create-rest-api \
  --name "ProductionAPI" \
  --description "API di produzione per servizi core" \
  --endpoint-configuration types=REGIONAL

# Ottenere l'ID della risorsa root
API_ID="abc123def"
ROOT_ID=$(aws apigateway get-resources --rest-api-id $API_ID \
  --query 'items[?path==`/`].id' --output text)

# Creazione di una risorsa
aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part "users"

# Creazione di un metodo
RESOURCE_ID="xyz789"
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method GET \
  --authorization-type COGNITO_USER_POOLS \
  --authorizer-id "auth001"

# Integrazione con Lambda
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $RESOURCE_ID \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri "arn:aws:apigateway:eu-west-1:lambda:path/2015-03-31/functions/arn:aws:lambda:eu-west-1:123456789:function:GetUsers/invocations"

# Deployment su uno stage
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name production \
  --stage-description "Stage di produzione" \
  --description "Deploy v1.2.0"

# Configurazione dello stage
aws apigateway update-stage \
  --rest-api-id $API_ID \
  --stage-name production \
  --patch-operations \
    op=replace,path=/throttling/rateLimit,value=1000 \
    op=replace,path=/throttling/burstLimit,value=2000 \
    op=replace,path=/*/*/logging/loglevel,value=INFO \
    op=replace,path=/*/*/metrics/enabled,value=true
```

### Authorization

**Lambda Authorizer** — Funzione Lambda che valida il token e restituisce una IAM policy.

```python
# lambda_authorizer.py
import json
import jwt
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

JWT_SECRET = os.environ['JWT_SECRET']
ISSUER = os.environ['JWT_ISSUER']

def handler(event, context):
    """Lambda authorizer per API Gateway REST API."""
    token = event.get('authorizationToken', '')

    if not token.startswith('Bearer '):
        logger.warning("Token mancante o formato non valido")
        raise Exception('Unauthorized')

    token = token[7:]  # Rimozione del prefisso "Bearer "

    try:
        decoded = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=['HS256'],
            issuer=ISSUER,
            options={
                'require': ['exp', 'sub', 'iss', 'scope'],
                'verify_exp': True,
                'verify_iss': True
            }
        )
    except jwt.ExpiredSignatureError:
        logger.info("Token scaduto")
        raise Exception('Unauthorized')
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token non valido: {e}")
        raise Exception('Unauthorized')

    # Generazione della IAM policy
    scopes = decoded.get('scope', '').split()
    method_arn = event['methodArn']
    arn_parts = method_arn.split(':')
    region = arn_parts[3]
    account_id = arn_parts[4]
    api_gateway_arn = arn_parts[5].split('/')
    api_id = api_gateway_arn[0]
    stage = api_gateway_arn[1]

    statements = []

    if 'read' in scopes:
        statements.append({
            'Action': 'execute-api:Invoke',
            'Effect': 'Allow',
            'Resource': f'arn:aws:execute-api:{region}:{account_id}:{api_id}/{stage}/GET/*'
        })

    if 'write' in scopes:
        statements.append({
            'Action': 'execute-api:Invoke',
            'Effect': 'Allow',
            'Resource': [
                f'arn:aws:execute-api:{region}:{account_id}:{api_id}/{stage}/POST/*',
                f'arn:aws:execute-api:{region}:{account_id}:{api_id}/{stage}/PUT/*',
                f'arn:aws:execute-api:{region}:{account_id}:{api_id}/{stage}/PATCH/*'
            ]
        })

    if 'admin' in scopes:
        statements.append({
            'Action': 'execute-api:Invoke',
            'Effect': 'Allow',
            'Resource': f'arn:aws:execute-api:{region}:{account_id}:{api_id}/{stage}/*'
        })

    return {
        'principalId': decoded['sub'],
        'policyDocument': {
            'Version': '2012-10-17',
            'Statement': statements
        },
        'context': {
            'userId': decoded['sub'],
            'email': decoded.get('email', ''),
            'roles': json.dumps(decoded.get('roles', []))
        }
    }
```

### Request/Response Mapping Templates (VTL)

```velocity
## Request Mapping Template — Trasformazione da query params a JSON body
#set($inputRoot = $input.path('$'))
{
  "userId": "$input.params('userId')",
  "filters": {
    "status": "$util.escapeJavaScript($input.params('status'))",
    "startDate": "$util.escapeJavaScript($input.params('startDate'))",
    "endDate": "$util.escapeJavaScript($input.params('endDate'))"
  },
  "pagination": {
    "page": $input.params('page'),
    "limit": $input.params('limit')
  },
  "requestContext": {
    "sourceIp": "$context.identity.sourceIp",
    "userAgent": "$context.identity.userAgent",
    "requestId": "$context.requestId",
    "stage": "$context.stage"
  }
}

## Response Mapping Template — Standardizzazione della risposta
#set($inputRoot = $input.path('$'))
#if($input.path('$.errorType') != "")
  #set($context.responseOverride.status = 500)
  {
    "errors": [{
      "code": "INTERNAL_ERROR",
      "message": "Errore interno del servizio",
      "requestId": "$context.requestId"
    }]
  }
#else
  {
    "data": $input.json('$.body'),
    "meta": {
      "total": $input.json('$.total'),
      "page": $input.json('$.page'),
      "requestId": "$context.requestId"
    }
  }
#end
```

### AWS CDK Example

```typescript
// lib/api-gateway-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as wafv2 from 'aws-cdk-lib/aws-wafv2';
import * as logs from 'aws-cdk-lib/aws-logs';
import { Construct } from 'constructs';

export class ApiGatewayStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Cognito User Pool per autenticazione
    const userPool = new cognito.UserPool(this, 'ApiUserPool', {
      userPoolName: 'production-api-users',
      selfSignUpEnabled: false,
      signInAliases: { email: true },
      passwordPolicy: {
        minLength: 12,
        requireUppercase: true,
        requireDigits: true,
        requireSymbols: true,
      },
      mfa: cognito.Mfa.REQUIRED,
      mfaSecondFactor: { sms: false, otp: true },
      accountRecovery: cognito.AccountRecovery.EMAIL_ONLY,
    });

    const userPoolClient = userPool.addClient('ApiClient', {
      oAuth: {
        flows: { authorizationCodeGrant: true, clientCredentials: true },
        scopes: [
          cognito.OAuthScope.custom('api/read'),
          cognito.OAuthScope.custom('api/write'),
        ],
      },
      accessTokenValidity: cdk.Duration.hours(1),
      refreshTokenValidity: cdk.Duration.days(30),
    });

    // Lambda functions
    const getUsersFunction = new lambda.Function(this, 'GetUsers', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'handlers.get_users',
      code: lambda.Code.fromAsset('lambda/users'),
      timeout: cdk.Duration.seconds(15),
      memorySize: 256,
      environment: {
        TABLE_NAME: 'users',
        REGION: this.region,
      },
    });

    // API Gateway REST API
    const api = new apigateway.RestApi(this, 'ProductionApi', {
      restApiName: 'Production API',
      description: 'API di produzione con autenticazione Cognito e WAF',
      deployOptions: {
        stageName: 'v1',
        throttlingRateLimit: 1000,
        throttlingBurstLimit: 2000,
        loggingLevel: apigateway.MethodLoggingLevel.INFO,
        dataTraceEnabled: false,
        metricsEnabled: true,
        accessLogDestination: new apigateway.LogGroupLogDestination(
          new logs.LogGroup(this, 'ApiAccessLogs', {
            retention: logs.RetentionDays.THIRTY_DAYS,
          })
        ),
        accessLogFormat: apigateway.AccessLogFormat.jsonWithStandardFields({
          caller: true,
          httpMethod: true,
          ip: true,
          protocol: true,
          requestTime: true,
          resourcePath: true,
          responseLength: true,
          status: true,
          user: true,
        }),
      },
      defaultCorsPreflightOptions: {
        allowOrigins: ['https://app.example.com'],
        allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allowHeaders: ['Content-Type', 'Authorization', 'X-Api-Key'],
        maxAge: cdk.Duration.hours(1),
      },
    });

    // Cognito Authorizer
    const authorizer = new apigateway.CognitoUserPoolsAuthorizer(this, 'CognitoAuthorizer', {
      cognitoUserPools: [userPool],
      authorizerName: 'CognitoAuthorizer',
      identitySource: 'method.request.header.Authorization',
    });

    // API Resources e Methods
    const usersResource = api.root.addResource('users');
    usersResource.addMethod('GET',
      new apigateway.LambdaIntegration(getUsersFunction, {
        proxy: true,
        integrationResponses: [{
          statusCode: '200',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': "'https://app.example.com'",
          },
        }],
      }),
      {
        authorizer,
        authorizationType: apigateway.AuthorizationType.COGNITO,
        authorizationScopes: ['api/read'],
        requestValidator: new apigateway.RequestValidator(this, 'GetUsersValidator', {
          restApi: api,
          validateRequestParameters: true,
        }),
        requestParameters: {
          'method.request.querystring.page': false,
          'method.request.querystring.limit': false,
        },
      }
    );

    // Usage Plan e API Key
    const usagePlan = api.addUsagePlan('StandardPlan', {
      name: 'Standard',
      description: 'Piano standard per partner',
      throttle: { rateLimit: 100, burstLimit: 200 },
      quota: { limit: 100000, period: apigateway.Period.MONTH },
    });

    const apiKey = api.addApiKey('PartnerApiKey', {
      apiKeyName: 'partner-key',
      description: 'API Key per partner',
    });

    usagePlan.addApiKey(apiKey);
    usagePlan.addApiStage({ stage: api.deploymentStage });

    // WAF Web ACL
    const webAcl = new wafv2.CfnWebACL(this, 'ApiWaf', {
      scope: 'REGIONAL',
      defaultAction: { allow: {} },
      rules: [
        {
          name: 'RateLimitRule',
          priority: 1,
          action: { block: {} },
          statement: {
            rateBasedStatement: {
              limit: 2000,
              aggregateKeyType: 'IP',
            },
          },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: 'RateLimitRule',
          },
        },
        {
          name: 'AWSManagedRulesCommonRuleSet',
          priority: 2,
          overrideAction: { none: {} },
          statement: {
            managedRuleGroupStatement: {
              vendorName: 'AWS',
              name: 'AWSManagedRulesCommonRuleSet',
            },
          },
          visibilityConfig: {
            sampledRequestsEnabled: true,
            cloudWatchMetricsEnabled: true,
            metricName: 'AWSManagedRulesCommonRuleSet',
          },
        },
      ],
      visibilityConfig: {
        sampledRequestsEnabled: true,
        cloudWatchMetricsEnabled: true,
        metricName: 'ApiWaf',
      },
    });

    // Associazione WAF con API Gateway
    new wafv2.CfnWebACLAssociation(this, 'ApiWafAssociation', {
      resourceArn: api.deploymentStage.stageArn,
      webAclArn: webAcl.attrArn,
    });

    // Output
    new cdk.CfnOutput(this, 'ApiUrl', {
      value: api.url,
      description: 'URL dell\'API Gateway',
    });
  }
}
```

### Terraform Example

```hcl
# api-gateway.tf
resource "aws_api_gateway_rest_api" "production" {
  name        = "production-api"
  description = "API di produzione"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  body = templatefile("${path.module}/openapi.json", {
    lambda_invoke_arn = aws_lambda_function.api_handler.invoke_arn
    authorizer_uri    = aws_lambda_function.authorizer.invoke_arn
    region            = var.region
    account_id        = data.aws_caller_identity.current.account_id
  })
}

resource "aws_api_gateway_deployment" "production" {
  rest_api_id = aws_api_gateway_rest_api.production.id

  triggers = {
    redeployment = sha1(jsonencode(aws_api_gateway_rest_api.production.body))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "v1" {
  deployment_id = aws_api_gateway_deployment.production.id
  rest_api_id   = aws_api_gateway_rest_api.production.id
  stage_name    = "v1"

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_access_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      caller         = "$context.identity.caller"
      user           = "$context.identity.user"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      latency        = "$context.responseLatency"
    })
  }

  xray_tracing_enabled = true
}

resource "aws_api_gateway_method_settings" "all" {
  rest_api_id = aws_api_gateway_rest_api.production.id
  stage_name  = aws_api_gateway_stage.v1.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled    = true
    logging_level      = "INFO"
    throttling_rate_limit  = 1000
    throttling_burst_limit = 2000
    caching_enabled    = true
    cache_ttl_in_seconds = 300
  }
}

resource "aws_api_gateway_domain_name" "api" {
  domain_name              = "api.example.com"
  regional_certificate_arn = aws_acm_certificate.api.arn

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

resource "aws_api_gateway_base_path_mapping" "api" {
  api_id      = aws_api_gateway_rest_api.production.id
  stage_name  = aws_api_gateway_stage.v1.stage_name
  domain_name = aws_api_gateway_domain_name.api.domain_name
  base_path   = "v1"
}
```

---

## 6. Azure API Management (APIM)

### Architettura

Azure API Management (APIM) e composto da tre componenti principali:

**Gateway** — Il componente che processa le richieste API. Accetta le chiamate, applica le policy
configurate, instrada verso i backend, e restituisce le risposte. In produzione puo essere
distribuito in piu regioni Azure per ridurre la latenza.

**Management Plane** — Il piano di gestione accessibile tramite Azure Portal, API REST, Azure CLI,
PowerShell, e SDK. Consente di definire API, prodotti, policy, utenti e sottoscrizioni.

**Developer Portal** — Un portale web generato automaticamente dove i consumer delle API possono
consultare la documentazione, provare le API interattivamente, gestire le proprie sottoscrizioni
e API key.

### Tiers

| Tier | SLA | Capacita | Cache | VNet | Multi-Region | Prezzo Approssimativo |
|---|---|---|---|---|---|---|
| Consumption | 99.95% | Autoscaling | No | No | No | Pay-per-call |
| Developer | No SLA | 1 unita | 10 MB | Si | No | ~$50/mese |
| Basic | 99.95% | 2 unita | 50 MB | No | No | ~$150/mese |
| Standard | 99.95% | 4 unita | 1 GB | No | No | ~$700/mese |
| Premium | 99.99% | 12+ unita | 5 GB | Si | Si | ~$2800/mese/unita |

### Policy System

Le policy in APIM sono istruzioni XML che modificano il comportamento del gateway. Sono organizzate
in quattro sezioni che corrispondono a fasi diverse della pipeline di elaborazione:

- **inbound** — Eseguite quando la richiesta arriva al gateway, prima dell'inoltro al backend.
- **backend** — Eseguite immediatamente prima dell'invio al backend.
- **outbound** — Eseguite quando la risposta torna dal backend, prima dell'invio al client.
- **on-error** — Eseguite in caso di errore in qualsiasi fase.

```xml
<!-- Policy completa per un'API di produzione -->
<policies>
    <inbound>
        <base />

        <!-- Validazione JWT -->
        <validate-jwt header-name="Authorization"
                      failed-validation-httpcode="401"
                      failed-validation-error-message="Token non valido o scaduto"
                      require-expiration-time="true"
                      require-scheme="Bearer">
            <openid-config url="https://login.microsoftonline.com/{tenant-id}/v2.0/.well-known/openid-configuration" />
            <audiences>
                <audience>api://production-api</audience>
            </audiences>
            <issuers>
                <issuer>https://sts.windows.net/{tenant-id}/</issuer>
            </issuers>
            <required-claims>
                <claim name="roles" match="any">
                    <value>API.Read</value>
                    <value>API.Write</value>
                </claim>
            </required-claims>
        </validate-jwt>

        <!-- Rate Limiting per subscription key -->
        <rate-limit-by-key calls="100"
                          renewal-period="60"
                          counter-key="@(context.Subscription.Id)"
                          increment-condition="@(context.Response.StatusCode >= 200 && context.Response.StatusCode < 400)"
                          remaining-calls-header-name="X-RateLimit-Remaining"
                          total-calls-header-name="X-RateLimit-Limit" />

        <!-- Quota per subscription -->
        <quota-by-key calls="50000"
                      bandwidth="104857600"
                      renewal-period="2592000"
                      counter-key="@(context.Subscription.Id)" />

        <!-- Validazione del corpo della richiesta -->
        <validate-content unspecified-content-type-action="prevent"
                          max-size="1048576"
                          size-exceeded-action="prevent"
                          errors-variable-name="validationErrors">
            <content type="application/json" validate-as="json"
                     action="prevent"
                     schema-id="user-schema" />
        </validate-content>

        <!-- Trasformazione degli header -->
        <set-header name="X-Request-Id" exists-action="skip">
            <value>@(Guid.NewGuid().ToString())</value>
        </set-header>
        <set-header name="X-Forwarded-For" exists-action="override">
            <value>@(context.Request.IpAddress)</value>
        </set-header>

        <!-- Rimozione di header sensibili -->
        <set-header name="X-Powered-By" exists-action="delete" />
        <set-header name="Server" exists-action="delete" />

        <!-- Cache della risposta -->
        <cache-lookup vary-by-developer="false"
                      vary-by-developer-groups="false"
                      downstream-caching-type="none">
            <vary-by-header>Accept</vary-by-header>
            <vary-by-query-parameter>page</vary-by-query-parameter>
            <vary-by-query-parameter>limit</vary-by-query-parameter>
        </cache-lookup>

        <!-- CORS -->
        <cors allow-credentials="true">
            <allowed-origins>
                <origin>https://app.example.com</origin>
                <origin>https://admin.example.com</origin>
            </allowed-origins>
            <allowed-methods preflight-result-max-age="3600">
                <method>GET</method>
                <method>POST</method>
                <method>PUT</method>
                <method>DELETE</method>
                <method>OPTIONS</method>
            </allowed-methods>
            <allowed-headers>
                <header>Content-Type</header>
                <header>Authorization</header>
                <header>Ocp-Apim-Subscription-Key</header>
            </allowed-headers>
            <expose-headers>
                <header>X-RateLimit-Limit</header>
                <header>X-RateLimit-Remaining</header>
                <header>X-RateLimit-Reset</header>
            </expose-headers>
        </cors>
    </inbound>

    <backend>
        <base />
        <!-- Circuit Breaker -->
        <forward-request timeout="15"
                         follow-redirects="false"
                         buffer-request-body="true" />
    </backend>

    <outbound>
        <base />

        <!-- Cache della risposta -->
        <cache-store duration="300" />

        <!-- Security headers -->
        <set-header name="Strict-Transport-Security" exists-action="override">
            <value>max-age=63072000; includeSubDomains; preload</value>
        </set-header>
        <set-header name="X-Content-Type-Options" exists-action="override">
            <value>nosniff</value>
        </set-header>
        <set-header name="X-Frame-Options" exists-action="override">
            <value>DENY</value>
        </set-header>
        <set-header name="Content-Security-Policy" exists-action="override">
            <value>default-src 'none'; frame-ancestors 'none'</value>
        </set-header>

        <!-- Trasformazione della risposta -->
        <set-body>@{
            var response = context.Response.Body.As<JObject>();
            var result = new JObject();
            result["data"] = response;
            result["meta"] = new JObject {
                ["requestId"] = context.RequestId.ToString(),
                ["timestamp"] = DateTime.UtcNow.ToString("o"),
                ["gateway"] = "azure-apim"
            };
            return result.ToString();
        }</set-body>

        <!-- Rimozione di campi sensibili dalla risposta -->
        <set-body>@{
            var body = context.Response.Body.As<JObject>();
            if (body["data"] is JObject data) {
                data.Remove("internalId");
                data.Remove("passwordHash");
                data.Remove("_metadata");
            }
            return body.ToString();
        }</set-body>
    </outbound>

    <on-error>
        <base />
        <!-- Logging dell'errore -->
        <set-header name="X-Error-Source" exists-action="override">
            <value>@(context.LastError.Source)</value>
        </set-header>

        <!-- Risposta di errore standardizzata -->
        <return-response>
            <set-status code="@((int)context.Response.StatusCode)"
                        reason="@(context.Response.StatusReason)" />
            <set-header name="Content-Type" exists-action="override">
                <value>application/json</value>
            </set-header>
            <set-body>@{
                return new JObject(
                    new JProperty("errors", new JArray(
                        new JObject(
                            new JProperty("code", context.LastError.Source),
                            new JProperty("message", context.LastError.Message),
                            new JProperty("requestId", context.RequestId.ToString())
                        )
                    ))
                ).ToString();
            }</set-body>
        </return-response>
    </on-error>
</policies>
```

### Gestione con Azure CLI

```bash
# Creazione di un'istanza APIM
az apim create \
  --name production-apim \
  --resource-group rg-production \
  --publisher-name "Example Corp" \
  --publisher-email admin@example.com \
  --sku-name Standard \
  --location westeurope

# Importazione di un'API da OpenAPI spec
az apim api import \
  --resource-group rg-production \
  --service-name production-apim \
  --api-id user-api \
  --path /users \
  --specification-format OpenApiJson \
  --specification-url https://raw.githubusercontent.com/example/specs/main/user-api.json \
  --display-name "User API" \
  --service-url https://user-backend.internal \
  --protocols https \
  --api-type http \
  --subscription-required true

# Creazione di un prodotto
az apim product create \
  --resource-group rg-production \
  --service-name production-apim \
  --product-id premium-tier \
  --display-name "Premium Tier" \
  --description "Accesso completo alle API con limiti elevati" \
  --subscription-required true \
  --approval-required true \
  --state published

# Associazione API al prodotto
az apim product api add \
  --resource-group rg-production \
  --service-name production-apim \
  --product-id premium-tier \
  --api-id user-api

# Creazione di una sottoscrizione
az apim subscription create \
  --resource-group rg-production \
  --service-name production-apim \
  --subscription-id partner-sub-001 \
  --display-name "Partner Corp Subscription" \
  --scope "/products/premium-tier" \
  --state active

# Configurazione di un Named Value (secret reference)
az apim nv create \
  --resource-group rg-production \
  --service-name production-apim \
  --named-value-id jwt-secret \
  --display-name "JWT Secret" \
  --value "" \
  --secret true \
  --tags "security" "jwt"

# Esportazione della configurazione API
az apim api export \
  --resource-group rg-production \
  --service-name production-apim \
  --api-id user-api \
  --export-format openapi-link

# Configurazione del developer portal
az apim portalsetting show \
  --resource-group rg-production \
  --service-name production-apim
```

### Products e Subscriptions

I Products in APIM raggruppano una o piu API e definiscono le condizioni di accesso (approvazione
richiesta, limiti di quota, termini di utilizzo). Ogni consumer ottiene l'accesso alle API tramite
una Subscription associata a un Product, che genera una coppia di chiavi (primaria e secondaria).

### Versioning e Revision

```bash
# Creazione di una nuova versione dell'API
az apim api create \
  --resource-group rg-production \
  --service-name production-apim \
  --api-id user-api-v2 \
  --display-name "User API v2" \
  --path /users \
  --api-version v2 \
  --api-version-set-id user-api-versions \
  --protocols https \
  --service-url https://user-backend-v2.internal

# Creazione di un version set
az apim api versionset create \
  --resource-group rg-production \
  --service-name production-apim \
  --version-set-id user-api-versions \
  --display-name "User API Versions" \
  --versioning-scheme Header \
  --version-header-name Api-Version

# Creazione di una revision (non-breaking change)
az apim api revision create \
  --resource-group rg-production \
  --service-name production-apim \
  --api-id user-api \
  --api-revision 2 \
  --api-revision-description "Aggiunta paginazione ai risultati GET"
```

### Self-Hosted Gateway

Il self-hosted gateway e un container Docker che replica la funzionalita del gateway APIM in
ambienti on-premise, edge, multi-cloud o Kubernetes. Sincronizza la configurazione con il
control plane in Azure.

```bash
# Deployment del self-hosted gateway su Kubernetes
az apim gateway create \
  --resource-group rg-production \
  --service-name production-apim \
  --gateway-id on-premise-gw \
  --description "Gateway on-premise per datacenter Milano"

# Ottenere il token di configurazione
az apim gateway token create \
  --resource-group rg-production \
  --service-name production-apim \
  --gateway-id on-premise-gw \
  --expiry "2026-12-31T23:59:59Z"
```

---

## 7. GCP API Gateway e Apigee

### Panoramica dei Servizi GCP

Google Cloud offre tre soluzioni per la gestione delle API, ciascuna con un livello di
complessita e funzionalita differente:

**Cloud Endpoints** — Soluzione leggera basata su ESP (Extensible Service Proxy) o ESPv2,
un proxy Envoy-based che si affianca al servizio. Supporta OpenAPI e gRPC, autenticazione
con API key, Firebase Auth, Auth0. Ideale per servizi su Cloud Run, GKE, Compute Engine.

**API Gateway** — Servizio managed completamente serverless. Accetta specifiche OpenAPI 2.0,
gestisce autenticazione (API key, Firebase, JWT), monitoring integrato. Costo basato
esclusivamente sulle chiamate. Non richiede gestione dell'infrastruttura.

**Apigee** — Piattaforma enterprise di API management. Include analytics avanzato,
monetizzazione, developer portal, traffic management, security avanzata, supporto
per ambienti ibridi (Apigee hybrid). Acquisito da Google, ora integrato in GCP.

| Funzionalita | Cloud Endpoints | API Gateway | Apigee |
|---|---|---|---|
| Modello di Deploy | Sidecar proxy | Serverless managed | Managed o hybrid |
| OpenAPI Support | Si (2.0 e 3.0) | Si (2.0) | Si (2.0 e 3.0) |
| gRPC Support | Si | No | Si |
| Analytics | Base (Cloud Monitoring) | Base | Avanzato |
| Monetizzazione | No | No | Si |
| Developer Portal | No | No | Si |
| Traffic Management | Limitato | Limitato | Avanzato |
| Costo | Basso | Pay-per-call | Enterprise |

### API Gateway — Deployment con OpenAPI Spec

```yaml
# openapi-spec.yaml per GCP API Gateway
swagger: "2.0"
info:
  title: "Production User API"
  description: "API per la gestione degli utenti"
  version: "1.0.0"

host: "api-gateway-abc123.apigateway.project-id.cloud.goog"
basePath: "/"

schemes:
  - "https"

produces:
  - "application/json"
consumes:
  - "application/json"

securityDefinitions:
  api_key:
    type: "apiKey"
    name: "x-api-key"
    in: "header"

  firebase_auth:
    authorizationUrl: ""
    flow: "implicit"
    type: "oauth2"
    x-google-issuer: "https://securetoken.google.com/project-id"
    x-google-jwks_uri: "https://www.googleapis.com/service_accounts/v1/metadata/x509/securetoken@system.gserviceaccount.com"
    x-google-audiences: "project-id"

  custom_jwt:
    authorizationUrl: ""
    flow: "implicit"
    type: "oauth2"
    x-google-issuer: "https://auth.example.com"
    x-google-jwks_uri: "https://auth.example.com/.well-known/jwks.json"
    x-google-audiences: "production-api"

paths:
  /users:
    get:
      summary: "Elenco utenti"
      operationId: "listUsers"
      security:
        - firebase_auth: []
        - api_key: []
      x-google-backend:
        address: "https://user-service-abc123.run.app"
        path_translation: APPEND_PATH_TO_ADDRESS
        deadline: 30.0
      x-google-quota:
        metricCosts:
          read-requests: 1
      parameters:
        - name: page
          in: query
          type: integer
          default: 1
        - name: limit
          in: query
          type: integer
          default: 20
          maximum: 100
      responses:
        "200":
          description: "Lista utenti"
          schema:
            type: object
            properties:
              data:
                type: array
                items:
                  $ref: "#/definitions/User"
              meta:
                $ref: "#/definitions/PaginationMeta"
        "401":
          description: "Non autenticato"
        "429":
          description: "Limite di richieste superato"

    post:
      summary: "Creazione utente"
      operationId: "createUser"
      security:
        - custom_jwt: []
      x-google-backend:
        address: "https://user-service-abc123.run.app"
        path_translation: APPEND_PATH_TO_ADDRESS
        deadline: 15.0
      x-google-quota:
        metricCosts:
          write-requests: 5
      parameters:
        - name: body
          in: body
          required: true
          schema:
            $ref: "#/definitions/CreateUserRequest"
      responses:
        "201":
          description: "Utente creato"
        "400":
          description: "Dati non validi"

definitions:
  User:
    type: object
    properties:
      id:
        type: string
      email:
        type: string
      name:
        type: string
      createdAt:
        type: string
        format: date-time

  PaginationMeta:
    type: object
    properties:
      total:
        type: integer
      page:
        type: integer
      limit:
        type: integer

  CreateUserRequest:
    type: object
    required:
      - email
      - name
    properties:
      email:
        type: string
        format: email
      name:
        type: string
        minLength: 2
        maxLength: 100

x-google-management:
  metrics:
    - name: read-requests
      displayName: "Read Requests"
      valueType: INT64
      metricKind: DELTA
    - name: write-requests
      displayName: "Write Requests"
      valueType: INT64
      metricKind: DELTA
  quota:
    limits:
      - name: read-requests-limit
        metric: read-requests
        unit: "1/min/{project}"
        values:
          STANDARD: 1000
      - name: write-requests-limit
        metric: write-requests
        unit: "1/min/{project}"
        values:
          STANDARD: 100
```

```bash
# Deployment dell'API Gateway su GCP

# Creazione dell'API config
gcloud api-gateway api-configs create user-api-config-v1 \
  --api=user-api \
  --openapi-spec=openapi-spec.yaml \
  --project=my-project-id \
  --backend-auth-service-account=api-gateway-sa@my-project-id.iam.gserviceaccount.com

# Creazione del gateway
gcloud api-gateway gateways create user-api-gateway \
  --api=user-api \
  --api-config=user-api-config-v1 \
  --location=europe-west1 \
  --project=my-project-id

# Verifica dello stato
gcloud api-gateway gateways describe user-api-gateway \
  --location=europe-west1 \
  --project=my-project-id

# Aggiornamento della configurazione (nuova versione)
gcloud api-gateway api-configs create user-api-config-v2 \
  --api=user-api \
  --openapi-spec=openapi-spec-v2.yaml \
  --project=my-project-id \
  --backend-auth-service-account=api-gateway-sa@my-project-id.iam.gserviceaccount.com

# Aggiornamento del gateway alla nuova config
gcloud api-gateway gateways update user-api-gateway \
  --api=user-api \
  --api-config=user-api-config-v2 \
  --location=europe-west1 \
  --project=my-project-id

# Creazione di una API key
gcloud services api-keys create \
  --display-name="Partner API Key" \
  --api-target=service=user-api-abc123.apigateway.my-project-id.cloud.goog

# Monitoring delle metriche
gcloud monitoring dashboards create \
  --config-from-file=api-gateway-dashboard.json
```

### Apigee — Configurazione Enterprise

Apigee utilizza un modello a proxy. Ogni API proxy definisce come le richieste vengono
elaborate attraverso una pipeline di policy.

```xml
<!-- Apigee API Proxy — ProxyEndpoint configuration -->
<ProxyEndpoint name="default">
    <PreFlow name="PreFlow">
        <Request>
            <!-- Verifica API key -->
            <Step>
                <Name>VerifyAPIKey</Name>
                <Condition>request.header.x-api-key != null</Condition>
            </Step>
            <!-- Spike Arrest per prevenire burst -->
            <Step>
                <Name>SpikeArrest-PerKey</Name>
            </Step>
            <!-- Quota per consumer -->
            <Step>
                <Name>Quota-PerDeveloper</Name>
            </Step>
            <!-- Validazione del payload -->
            <Step>
                <Name>JSON-Threat-Protection</Name>
                <Condition>request.verb = "POST" or request.verb = "PUT"</Condition>
            </Step>
        </Request>
        <Response>
            <!-- CORS headers -->
            <Step>
                <Name>AssignMessage-CORSHeaders</Name>
            </Step>
        </Response>
    </PreFlow>

    <Flows>
        <Flow name="GetUsers">
            <Condition>(proxy.pathsuffix MatchesPath "/users") and (request.verb = "GET")</Condition>
            <Request>
                <Step>
                    <Name>Cache-Lookup-Users</Name>
                </Step>
            </Request>
            <Response>
                <Step>
                    <Name>Cache-Populate-Users</Name>
                    <Condition>lookupcache.Cache-Lookup-Users.cachehit = false</Condition>
                </Step>
            </Response>
        </Flow>
    </Flows>

    <HTTPProxyConnection>
        <BasePath>/v1</BasePath>
        <VirtualHost>secure</VirtualHost>
    </HTTPProxyConnection>

    <RouteRule name="default">
        <TargetEndpoint>default</TargetEndpoint>
    </RouteRule>
</ProxyEndpoint>
```

### Apigee Analytics e Monetization

Apigee fornisce analytics dettagliati sulle API: volumi di traffico, tempi di risposta, error rate,
distribuzione geografica, analisi per developer, app e prodotto. Il modulo di monetizzazione
consente di definire piani tariffari (per chiamata, per volume, freemium con limiti), associarli
ai prodotti API, gestire la fatturazione e il revenue sharing con i partner.

---

## 8. Authentication e Authorization

### API Key Management

Le API key sono il metodo piu semplice di autenticazione, adatto per comunicazione machine-to-machine
o per identificare il consumer dell'API (non per autenticare un utente finale). Le API key devono
essere trattate come secret: trasmesse solo su HTTPS, mai incluse in URL (usare header), soggette
a rotazione periodica.

```bash
# Kong — Creazione e rotazione API key
# Creazione di un consumer con API key
curl -X POST http://localhost:8001/consumers \
  -H "Content-Type: application/json" \
  -d '{"username": "partner-app"}'

curl -X POST http://localhost:8001/consumers/partner-app/key-auth \
  -H "Content-Type: application/json" \
  -d '{"key": "new-api-key-2024-Q2"}'

# Rotazione: aggiunta della nuova key, poi rimozione della vecchia
# 1. Aggiunta della nuova key
curl -X POST http://localhost:8001/consumers/partner-app/key-auth \
  -H "Content-Type: application/json" \
  -d '{"key": "new-api-key-2024-Q3"}'

# 2. Verifica che il consumer usi la nuova key
curl -s http://localhost:8001/consumers/partner-app/key-auth | jq '.data[].key'

# 3. Rimozione della vecchia key dopo il periodo di transizione
curl -X DELETE http://localhost:8001/consumers/partner-app/key-auth/{old-key-id}
```

### OAuth 2.0 Flows

**Client Credentials** — Per comunicazione machine-to-machine. Il client si autentica direttamente
con client_id e client_secret per ottenere un access token. Non coinvolge un utente finale.

**Authorization Code** — Per applicazioni web server-side. L'utente viene reindirizzato all'identity
provider, autorizza l'applicazione, riceve un authorization code che viene scambiato server-side
per un access token.

**Authorization Code with PKCE** — Per applicazioni SPA e mobile. Aggiunge un code_verifier e
code_challenge per prevenire l'intercettazione dell'authorization code. Obbligatorio per client
pubblici (che non possono custodire un client secret).

```yaml
# Kong — Configurazione OAuth2
plugins:
  - name: oauth2
    service: protected-api
    config:
      scopes:
        - read
        - write
        - admin
      mandatory_scope: true
      enable_client_credentials: true
      enable_authorization_code: true
      enable_password_grant: false
      enable_implicit_grant: false
      token_expiration: 3600
      refresh_token_ttl: 1209600
      accept_http_if_already_terminated: true
      global_credentials: false
```

### JWT Validation

```yaml
# Traefik — ForwardAuth per JWT validation
http:
  middlewares:
    jwt-validator:
      forwardAuth:
        address: http://jwt-validator:4000/validate
        trustForwardHeader: true
        authResponseHeaders:
          - X-User-Id
          - X-User-Email
          - X-User-Roles
          - X-User-Scopes
        authRequestHeaders:
          - Authorization
```

```python
# jwt-validator/app.py — Servizio di validazione JWT per ForwardAuth
from flask import Flask, request, jsonify
import jwt
import os
import logging

app = Flask(__name__)
logger = logging.getLogger(__name__)

JWKS_URI = os.environ.get('JWKS_URI')
ISSUER = os.environ.get('JWT_ISSUER')
AUDIENCE = os.environ.get('JWT_AUDIENCE')
ALGORITHMS = ['RS256', 'ES256']

# In produzione, caricare le chiavi da JWKS endpoint con caching
PUBLIC_KEY = os.environ.get('JWT_PUBLIC_KEY', '').replace('\\n', '\n')

@app.route('/validate', methods=['GET'])
def validate():
    auth_header = request.headers.get('Authorization', '')

    if not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Token mancante'}), 401

    token = auth_header[7:]

    try:
        decoded = jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=ALGORITHMS,
            issuer=ISSUER,
            audience=AUDIENCE,
            options={
                'require': ['exp', 'sub', 'iss', 'aud'],
                'verify_exp': True,
                'verify_iss': True,
                'verify_aud': True
            }
        )
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token scaduto'}), 401
    except jwt.InvalidTokenError as e:
        logger.warning(f"Token non valido: {e}")
        return jsonify({'error': 'Token non valido'}), 401

    # Propagazione delle informazioni utente al backend tramite header
    response = app.make_response('')
    response.status_code = 200
    response.headers['X-User-Id'] = decoded.get('sub', '')
    response.headers['X-User-Email'] = decoded.get('email', '')
    response.headers['X-User-Roles'] = ','.join(decoded.get('roles', []))
    response.headers['X-User-Scopes'] = ' '.join(decoded.get('scope', '').split())

    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000)
```

### mTLS per Client Authentication

Mutual TLS (mTLS) autentica sia il server che il client tramite certificati X.509. Il client presenta
il proprio certificato durante il TLS handshake, e il gateway verifica che sia firmato da una CA
trusted. Usato per comunicazione tra servizi interni o per autenticazione forte di partner.

```yaml
# Kong — Configurazione mTLS
plugins:
  - name: mtls-auth
    service: internal-api
    config:
      ca_certificates:
        - 793a0a1b-3867-4e08-b2a1-example
      skip_consumer_lookup: false
      revocation_check_mode: SKIP
      http_proxy_host: null
      cert_cache_ttl: 60
```

### Multi-Tenant API Access Control

In un contesto multi-tenant, l'API Gateway deve garantire l'isolamento dei dati tra tenant diversi.
La strategia tipica prevede l'estrazione del tenant ID dal token JWT (claim personalizzato) e la sua
propagazione al backend tramite header, dove il servizio applica il filtraggio dei dati.

```xml
<!-- Azure APIM — Policy per multi-tenant isolation -->
<policies>
    <inbound>
        <base />
        <validate-jwt header-name="Authorization" require-scheme="Bearer">
            <openid-config url="https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration" />
        </validate-jwt>

        <!-- Estrazione del tenant ID dal token JWT -->
        <set-variable name="tenantId"
                      value="@(context.Request.Headers.GetValueOrDefault("Authorization","")
                        .AsJwt()?.Claims.GetValueOrDefault("tenant_id", ""))" />

        <!-- Verifica che il tenant ID sia presente -->
        <choose>
            <when condition="@(String.IsNullOrEmpty((string)context.Variables["tenantId"]))">
                <return-response>
                    <set-status code="403" reason="Forbidden" />
                    <set-body>{"errors":[{"code":"MISSING_TENANT","message":"Tenant ID mancante nel token"}]}</set-body>
                </return-response>
            </when>
        </choose>

        <!-- Propagazione del tenant ID al backend -->
        <set-header name="X-Tenant-Id" exists-action="override">
            <value>@((string)context.Variables["tenantId"])</value>
        </set-header>

        <!-- Rate limiting per tenant -->
        <rate-limit-by-key calls="500"
                          renewal-period="60"
                          counter-key="@((string)context.Variables["tenantId"])" />
    </inbound>
</policies>
```

---

## 9. Rate Limiting e Throttling

### Algoritmi

**Fixed Window** — Conta le richieste in finestre temporali fisse (es. ogni minuto da :00 a :59).
Semplice da implementare ma soggetto al problema del burst al confine della finestra: un client
puo inviare il doppio delle richieste consentite concentrandole attorno al cambio di finestra.

**Sliding Window** — Calcola il rate in una finestra mobile che scorre nel tempo. Risolve il
problema del boundary burst del fixed window. Implementazione piu complessa, richiede il
tracciamento del timestamp di ogni richiesta o un approccio ibrido weighted.

**Token Bucket** — Un bucket virtuale viene riempito con token a un rate costante (es. 10
token/secondo). Ogni richiesta consuma un token. Se il bucket e vuoto, la richiesta viene
rifiutata. Consente burst controllati: se il bucket ha accumulato token, il client puo inviare
un burst fino alla capacita del bucket.

**Leaky Bucket** — Le richieste entrano in una coda (bucket) e vengono processate a un rate
costante (leak rate). Se la coda e piena, le nuove richieste vengono rifiutate. Produce un
output perfettamente uniforme, ideale per backend che non tollerano burst.

### Response Headers

Gli header di rate limiting comunicano al client lo stato del suo budget di richieste:

```
X-RateLimit-Limit: 100          # Numero massimo di richieste nel periodo
X-RateLimit-Remaining: 42       # Richieste rimanenti nel periodo corrente
X-RateLimit-Reset: 1712847600   # Timestamp Unix del reset del contatore
Retry-After: 30                 # Secondi di attesa prima di riprovare (su 429)
```

### Rate Limiting Distribuito (Redis-Based)

In un deployment multi-nodo, il rate limiting deve essere coordinato centralmente. Redis e la
scelta piu comune per il contatore distribuito grazie alla sua bassa latenza e alle operazioni
atomiche (INCR, EXPIRE, Lua scripting).

```yaml
# Kong — Rate limiting con Redis
plugins:
  - name: rate-limiting
    config:
      second: 50
      minute: 1000
      hour: 30000
      day: 500000
      policy: redis
      redis_host: redis-cluster.internal
      redis_port: 6379
      redis_password: ${REDIS_PASSWORD}
      redis_ssl: true
      redis_ssl_verify: true
      redis_database: 0
      redis_timeout: 2000
      fault_tolerant: true
      hide_client_headers: false
      error_code: 429
      error_message: "Limite di richieste superato"
```

```lua
-- Script Redis Lua per sliding window rate limiting
-- KEYS[1] = chiave del rate limiter (es. "ratelimit:consumer:123:minute")
-- ARGV[1] = timestamp corrente in millisecondi
-- ARGV[2] = window size in millisecondi
-- ARGV[3] = limite massimo di richieste
-- ARGV[4] = TTL della chiave in secondi

local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local ttl = tonumber(ARGV[4])

-- Rimozione delle entry fuori dalla finestra
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)

-- Conteggio delle richieste nella finestra corrente
local count = redis.call('ZCARD', key)

if count < limit then
    -- Aggiunta della richiesta corrente
    redis.call('ZADD', key, now, now .. '-' .. math.random(1000000))
    redis.call('EXPIRE', key, ttl)
    return {0, limit - count - 1, ttl}  -- allowed, remaining, reset
else
    return {1, 0, ttl}  -- denied, remaining=0, reset
end
```

### Per-Consumer vs Per-Route vs Global

**Global** — Un singolo contatore per tutte le richieste al gateway. Protegge l'infrastruttura
complessiva dal sovraccarico. Tipicamente configurato con limiti elevati.

**Per-Route** — Contatore separato per ogni rotta/endpoint. Permette di proteggere servizi
specifici (es. endpoint di ricerca con limiti piu bassi rispetto a endpoint di lettura semplice).

**Per-Consumer** — Contatore separato per ogni consumer autenticato. Il metodo piu granulare,
consente di differenziare i limiti in base al piano di servizio (free, standard, premium).

```yaml
# Kong — Rate limiting combinato (globale + per-consumer)
plugins:
  # Limite globale
  - name: rate-limiting
    config:
      minute: 10000
      policy: redis
      redis_host: redis.internal

  # Limite per consumer "free-tier"
  - name: rate-limiting
    consumer: free-tier-consumer
    config:
      minute: 60
      hour: 1000
      policy: redis
      redis_host: redis.internal

  # Limite per consumer "premium-tier"
  - name: rate-limiting
    consumer: premium-consumer
    config:
      minute: 1000
      hour: 50000
      policy: redis
      redis_host: redis.internal
```

### Graceful Degradation

Quando il rate limit viene superato, il gateway puo implementare strategie di degradazione
graduale invece di un rifiuto immediato:

1. **Throttling progressivo** — Aumentare la latenza delle risposte man mano che il client si
   avvicina al limite, scoraggiando ulteriori richieste.
2. **Risposte semplificate** — Restituire versioni cached o semplificate delle risposte quando
   il backend e sotto stress.
3. **Priority queuing** — Dare priorita alle richieste di consumer premium e rallentare quelle
   di consumer free.
4. **Retry-After con backoff** — Comunicare al client un tempo di attesa crescente ad ogni
   violazione consecutiva.

---

## 10. Request/Response Transformation

### Header Manipulation

La manipolazione degli header e l'operazione di trasformazione piu comune. Include l'aggiunta
di header per il tracing, la rimozione di header interni, la riscrittura di header per
compatibilita con backend legacy.

```yaml
# Kong — Request/Response Transformer
plugins:
  - name: request-transformer
    service: legacy-backend
    config:
      add:
        headers:
          - "X-Request-Id:$(uuid)"
          - "X-Gateway-Timestamp:$(timestamp)"
          - "X-Forwarded-Proto:https"
        body:
          - "source:api-gateway"
      remove:
        headers:
          - "X-Debug-Mode"
          - "X-Internal-Token"
      rename:
        headers:
          - "Authorization:X-Legacy-Auth"
      replace:
        headers:
          - "Content-Type:application/json; charset=utf-8"
      append:
        headers:
          - "X-Via:kong-gateway"

  - name: response-transformer
    service: legacy-backend
    config:
      add:
        headers:
          - "X-Response-Time:$(latency)"
          - "Cache-Control:no-store, no-cache, must-revalidate"
      remove:
        headers:
          - "Server"
          - "X-Powered-By"
          - "X-AspNet-Version"
      replace:
        headers:
          - "Content-Type:application/json; charset=utf-8"
```

### URL Rewriting

```yaml
# Traefik — URL rewriting con middleware
http:
  middlewares:
    # Rimozione del prefisso versione
    strip-api-version:
      stripPrefix:
        prefixes:
          - "/api/v1"
          - "/api/v2"

    # Sostituzione del path
    rewrite-users-path:
      replacePathRegex:
        regex: "^/api/v1/users/(.*)/profile$"
        replacement: "/internal/user-profiles/$1"

    # Aggiunta di prefisso
    add-internal-prefix:
      addPrefix:
        prefix: "/internal"

    # Redirect
    api-redirect:
      redirectRegex:
        regex: "^/api/v0/(.*)"
        replacement: "/api/v2/$1"
        permanent: true
```

### Body Transformation

```xml
<!-- Azure APIM — Trasformazione JSON to XML -->
<policies>
    <inbound>
        <base />
        <!-- Il client invia JSON, il backend legacy richiede XML -->
        <set-header name="Content-Type" exists-action="override">
            <value>application/xml</value>
        </set-header>
        <set-body>@{
            var json = context.Request.Body.As<JObject>();
            var xml = new System.Xml.Linq.XElement("UserRequest",
                new System.Xml.Linq.XElement("FirstName", (string)json["firstName"]),
                new System.Xml.Linq.XElement("LastName", (string)json["lastName"]),
                new System.Xml.Linq.XElement("Email", (string)json["email"]),
                new System.Xml.Linq.XElement("RequestTimestamp",
                    DateTime.UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"))
            );
            return xml.ToString();
        }</set-body>
    </inbound>

    <outbound>
        <base />
        <!-- Il backend risponde in XML, il client riceve JSON -->
        <set-header name="Content-Type" exists-action="override">
            <value>application/json</value>
        </set-header>
        <set-body>@{
            var xml = System.Xml.Linq.XDocument.Parse(context.Response.Body.As<string>());
            var user = xml.Root;
            var json = new JObject(
                new JProperty("data", new JObject(
                    new JProperty("id", (string)user.Element("Id")),
                    new JProperty("firstName", (string)user.Element("FirstName")),
                    new JProperty("lastName", (string)user.Element("LastName")),
                    new JProperty("email", (string)user.Element("Email"))
                )),
                new JProperty("meta", new JObject(
                    new JProperty("requestId", context.RequestId.ToString())
                ))
            );
            return json.ToString();
        }</set-body>
    </outbound>
</policies>
```

### Request Validation (JSON Schema)

```yaml
# Kong — Request Validator plugin
plugins:
  - name: request-validator
    service: user-service
    config:
      content_type: application/json
      body_schema: |
        {
          "type": "object",
          "required": ["email", "name"],
          "properties": {
            "email": {
              "type": "string",
              "format": "email",
              "maxLength": 254
            },
            "name": {
              "type": "string",
              "minLength": 2,
              "maxLength": 100,
              "pattern": "^[a-zA-Z\\s'-]+$"
            },
            "phone": {
              "type": "string",
              "pattern": "^\\+?[1-9]\\d{6,14}$"
            },
            "role": {
              "type": "string",
              "enum": ["user", "editor", "admin"]
            }
          },
          "additionalProperties": false
        }
      verbose_response: true
      allowed_content_types:
        - application/json
```

### Request Aggregation (Backend Fanout)

L'API Gateway puo aggregare risposte da piu servizi backend in una singola risposta per il
client. Questo pattern riduce il numero di round-trip per client con latenza elevata (mobile).

```xml
<!-- Azure APIM — Request aggregation con send-request -->
<policies>
    <inbound>
        <base />
        <!-- Fanout verso servizi multipli in parallelo -->
        <send-request mode="new" response-variable-name="userResponse" timeout="10">
            <set-url>@("https://user-service.internal/users/" +
                context.Request.MatchedParameters["userId"])</set-url>
            <set-method>GET</set-method>
            <set-header name="Authorization" exists-action="override">
                <value>@(context.Request.Headers.GetValueOrDefault("Authorization",""))</value>
            </set-header>
        </send-request>

        <send-request mode="new" response-variable-name="ordersResponse" timeout="10">
            <set-url>@("https://order-service.internal/users/" +
                context.Request.MatchedParameters["userId"] + "/orders?limit=5")</set-url>
            <set-method>GET</set-method>
        </send-request>

        <send-request mode="new" response-variable-name="notificationsResponse" timeout="10">
            <set-url>@("https://notification-service.internal/users/" +
                context.Request.MatchedParameters["userId"] + "/notifications?unread=true")</set-url>
            <set-method>GET</set-method>
        </send-request>
    </inbound>

    <outbound>
        <!-- Aggregazione delle risposte -->
        <return-response>
            <set-status code="200" />
            <set-header name="Content-Type" exists-action="override">
                <value>application/json</value>
            </set-header>
            <set-body>@{
                var user = ((IResponse)context.Variables["userResponse"])
                    .Body.As<JObject>();
                var orders = ((IResponse)context.Variables["ordersResponse"])
                    .Body.As<JObject>();
                var notifications = ((IResponse)context.Variables["notificationsResponse"])
                    .Body.As<JObject>();

                return new JObject(
                    new JProperty("data", new JObject(
                        new JProperty("user", user),
                        new JProperty("recentOrders", orders["data"]),
                        new JProperty("unreadNotifications", notifications["data"])
                    )),
                    new JProperty("meta", new JObject(
                        new JProperty("requestId", context.RequestId.ToString()),
                        new JProperty("aggregatedFrom", new JArray("user-service", "order-service", "notification-service"))
                    ))
                ).ToString();
            }</set-body>
        </return-response>
    </outbound>
</policies>
```

### Protocol Translation (REST to gRPC)

```yaml
# Kong — gRPC Gateway plugin (REST to gRPC)
plugins:
  - name: grpc-gateway
    service: grpc-user-service
    config:
      proto: /usr/local/kong/protos/user_service.proto

# Configurazione del service gRPC
services:
  - name: grpc-user-service
    protocol: grpc
    host: grpc-user-service.internal
    port: 50051
    routes:
      - name: grpc-user-routes
        paths:
          - /api/v1/grpc/users
        protocols:
          - http
          - https
```

Il plugin grpc-gateway traduce automaticamente le richieste REST in chiamate gRPC basandosi
sulla definizione del file .proto e sulle annotazioni google.api.http. La risposta gRPC viene
serializzata in JSON per il client REST.

---

## 11. Monitoring e Troubleshooting

### Metriche Chiave

Le metriche fondamentali per il monitoring di un API Gateway seguono il framework RED
(Rate, Errors, Duration) e il framework USE (Utilization, Saturation, Errors):

**Request Rate** — Numero di richieste al secondo (RPS) per rotta, servizio e consumer.
Stabilisce la baseline di traffico e permette di rilevare anomalie (spike o cali improvvisi).

**Latency** — Tempo di elaborazione della richiesta. Distinguere tra:
- Gateway latency (tempo nel gateway stesso)
- Upstream latency (tempo di risposta del backend)
- Total latency (gateway + upstream + rete)
Monitorare i percentili (p50, p90, p95, p99) piuttosto che la media.

**Error Rate** — Percentuale di risposte con status code 4xx e 5xx per rotta e consumer.
Separare gli errori client (4xx) dagli errori server (5xx): un aumento dei 5xx indica
problemi nei backend, un aumento dei 4xx puo indicare abuso o misconfiguration.

```yaml
# Kong — Prometheus plugin per metriche
plugins:
  - name: prometheus
    config:
      per_consumer: true
      status_code_metrics: true
      latency_metrics: true
      bandwidth_metrics: true
      upstream_health_metrics: true

# prometheus.yml — Scrape configuration
scrape_configs:
  - job_name: 'kong'
    scrape_interval: 15s
    static_configs:
      - targets: ['kong-gateway:8001']
    metrics_path: /metrics
```

```yaml
# Grafana dashboard queries per Kong
# Request rate per route
# PromQL: rate(kong_http_requests_total{route=~".*"}[5m])

# Latency p99 per service
# PromQL: histogram_quantile(0.99, rate(kong_request_latency_ms_bucket{type="kong"}[5m]))

# Error rate per route
# PromQL: sum(rate(kong_http_requests_total{code=~"5.."}[5m])) by (route)
#          / sum(rate(kong_http_requests_total[5m])) by (route) * 100

# Upstream health
# PromQL: kong_upstream_target_health{state="healthy"}
```

### Distributed Tracing

L'API Gateway deve propagare i correlation ID e gli span di tracing per abilitare il
distributed tracing end-to-end attraverso i microservizi.

```yaml
# Kong — OpenTelemetry plugin
plugins:
  - name: opentelemetry
    config:
      endpoint: http://otel-collector.internal:4318/v1/traces
      resource_attributes:
        service.name: kong-gateway
        service.version: "3.6"
        deployment.environment: production
      header_type: w3c
      batch_span_count: 200
      batch_flush_delay: 3
```

### Access e Audit Logging

```yaml
# Kong — Configurazione logging strutturato
# Formato del log personalizzato via variabili d'ambiente
# KONG_LOG_LEVEL=info
# KONG_PROXY_ACCESS_LOG=/dev/stdout
# KONG_PROXY_ERROR_LOG=/dev/stderr

# HTTP log verso un servizio centralizzato con formato strutturato
plugins:
  - name: http-log
    config:
      http_endpoint: https://log-aggregator.internal/kong-logs
      method: POST
      timeout: 10000
      keepalive: 60000
      flush_timeout: 2
      retry_count: 3
      custom_fields_by_lua:
        request_body: "return kong.request.get_raw_body()"
        consumer_username: "return kong.client.get_consumer() and kong.client.get_consumer().username or 'anonymous'"
```

### Common Issues e Debugging

**504 Gateway Timeout** — Il backend non ha risposto entro il timeout configurato.
Cause: backend sovraccarico, query lente nel database, deadlock, rete congestionata.
Azione: verificare i log del backend, controllare la latenza upstream nelle metriche del gateway,
aumentare il timeout se giustificato dal caso d'uso, implementare circuit breaking.

```bash
# Diagnosi 504 — Verifica timeout configuration in Kong
curl -s http://localhost:8001/services/slow-service | jq '{
  connect_timeout,
  write_timeout,
  read_timeout,
  retries
}'

# Aggiornamento dei timeout
curl -X PATCH http://localhost:8001/services/slow-service \
  -H "Content-Type: application/json" \
  -d '{
    "connect_timeout": 10000,
    "read_timeout": 60000,
    "write_timeout": 30000,
    "retries": 2
  }'
```

**429 Too Many Requests** — Il client ha superato il rate limit configurato.
Azione: verificare le configurazioni di rate limiting, controllare se il consumer ha
un piano adeguato, analizzare i pattern di traffico per determinare se i limiti sono
troppo restrittivi.

```bash
# Verifica rate limit configuration per un consumer
curl -s http://localhost:8001/consumers/partner-app/plugins | \
  jq '.data[] | select(.name == "rate-limiting") | .config'

# Verifica le metriche di rate limiting
curl -s http://localhost:8001/status | jq '.server'
```

**502 Bad Gateway** — Il gateway non riesce a comunicare con il backend o il backend ha
restituito una risposta non valida.
Cause: backend down, DNS resolution failure, TLS handshake failure, risposta malformata.
Azione: verificare lo stato dei target upstream, controllare i health check, verificare
la connettivita di rete.

```bash
# Verifica stato degli upstream e dei target
curl -s http://localhost:8001/upstreams | jq '.data[] | {name, algorithm}'
curl -s http://localhost:8001/upstreams/user-api-upstream/health | jq .

# Verifica lo stato di salute dei target
curl -s http://localhost:8001/upstreams/user-api-upstream/targets/all | \
  jq '.data[] | {target, weight, health}'
```

**CORS Issues** — Errori di cross-origin quando il browser blocca le richieste.
Cause: header Access-Control-Allow-Origin mancante o errato, metodi o header non
consentiti, credenziali non gestite.

```bash
# Verifica configurazione CORS
curl -s http://localhost:8001/services/public-api/plugins | \
  jq '.data[] | select(.name == "cors") | .config'

# Test preflight request
curl -v -X OPTIONS https://api.example.com/api/v1/users \
  -H "Origin: https://app.example.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type, Authorization"
```

### API Analytics

L'analisi del traffico API fornisce insight su: pattern di utilizzo per consumer, endpoint
piu utilizzati, distribuzione temporale del traffico, tempo medio di risposta per endpoint,
top consumer per volume, API con error rate elevato.

```bash
# Query Prometheus per analytics
# Top 10 rotte per traffico
# topk(10, sum(rate(kong_http_requests_total[1h])) by (route))

# Consumer con piu errori
# topk(5, sum(rate(kong_http_requests_total{code=~"5.."}[1h])) by (consumer))

# Trend della latenza nell'ultima settimana
# avg_over_time(histogram_quantile(0.95, rate(kong_request_latency_ms_bucket[5m]))[7d:1h])
```

---

## 12. Best Practices

### API Versioning Strategy

La scelta della strategia di versionamento ha impatto significativo sulla manutenibilita e
sull'esperienza degli sviluppatori consumer.

**URL Path Versioning** — `/api/v1/users`, `/api/v2/users`. La strategia piu esplicita e
visibile. Semplice da implementare nel gateway tramite routing basato su path. Svantaggio:
cambiare versione richiede di modificare tutti gli URL nel client.

**Header Versioning** — `Accept-Version: v2` o `API-Version: 2`. Mantiene gli URL puliti.
Piu difficile da testare (non basta il browser). Richiede configurazione specifica nel gateway
per il routing basato su header.

**Query Parameter** — `/api/users?version=2`. Semplice da testare ma considerato meno elegante.
Rischio di conflitto con altri parametri. Non raccomandato per nuove API.

**Content Negotiation** — `Accept: application/vnd.example.v2+json`. Segue i principi REST
in modo rigoroso. Complessita maggiore nella configurazione del routing.

Raccomandazione: URL path versioning per la sua semplicita e visibilita, con supporto
simultaneo di massimo 2-3 versioni attive.

### Deprecation Policy

```yaml
# Traefik — Header di deprecation
http:
  middlewares:
    v1-deprecation-notice:
      headers:
        customResponseHeaders:
          Deprecation: "true"
          Sunset: "Sat, 01 Mar 2025 00:00:00 GMT"
          Link: '<https://api.example.com/api/v2/docs>; rel="successor-version"'
          X-API-Warn: "La versione v1 sara dismessa il 01/03/2025. Migrare alla v2."
```

Processo di deprecation:
1. Annunciare la deprecation con largo anticipo (minimo 6 mesi per API pubbliche).
2. Aggiungere header Deprecation e Sunset a tutte le risposte della versione deprecata.
3. Monitorare il traffico sulla versione deprecata per identificare i consumer ancora attivi.
4. Contattare direttamente i consumer attivi per assistenza nella migrazione.
5. Ridurre gradualmente i rate limit della versione deprecata.
6. Dismettere la versione solo quando il traffico e zero o trascurabile.

### Security Hardening

```yaml
# Checklist di sicurezza per API Gateway

# 1. TLS 1.2+ obbligatorio
# Kong
# KONG_SSL_PROTOCOLS="TLSv1.2 TLSv1.3"
# KONG_SSL_CIPHERS="ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384"

# 2. Admin API non esposta pubblicamente
# KONG_ADMIN_LISTEN="127.0.0.1:8001"

# 3. Rate limiting su tutti gli endpoint
# 4. Request size limiting
# 5. IP restriction sull'Admin API
# 6. Logging di tutti gli accessi
# 7. Health check endpoint separato (non esposto pubblicamente)
# 8. Aggiornamenti di sicurezza regolari
```

```yaml
# Kong — Security hardening plugins
plugins:
  # Limitazione dimensione richiesta
  - name: request-size-limiting
    config:
      allowed_payload_size: 10  # MB
      size_unit: megabytes
      require_content_length: true

  # Limitazione dimensione corpo richiesta
  - name: request-termination
    service: maintenance-service
    config:
      status_code: 503
      message: "Servizio temporaneamente non disponibile per manutenzione"

  # Bot detection
  - name: bot-detection
    config:
      allow:
        - googlebot
        - bingbot
      deny:
        - scrapy
        - python-requests
```

### Documentation (OpenAPI/Swagger)

Ogni API esposta tramite il gateway deve avere una specifica OpenAPI aggiornata. Il gateway
puo servire la documentazione direttamente o indirizzare al developer portal.

```yaml
# Kong — Servire la documentazione OpenAPI
services:
  - name: api-docs
    url: http://docs-server.internal:8080
    routes:
      - name: api-docs-route
        paths:
          - /api/docs
          - /api/openapi.json
        methods:
          - GET
        strip_path: false
    plugins:
      - name: cors
        config:
          origins:
            - "*"
          methods:
            - GET
            - OPTIONS
```

### Gateway Scalability

**Horizontal Scaling** — Aggiungere nodi data plane dietro un load balancer. I nodi sono
stateless (in hybrid mode), quindi lo scaling e lineare. Ogni nodo riceve la configurazione
dal control plane e processa il traffico indipendentemente.

**Connection Pooling** — Configurare il pool di connessioni verso i backend per evitare
l'esaurimento delle connessioni. Ogni nodo del gateway mantiene un pool separato.

**Caching** — Abilitare il caching a livello di gateway per ridurre il carico sui backend.
Usare cache distribuita (Redis) per consistenza tra i nodi.

### Multi-Region Deployment

```yaml
# Architettura multi-region con Kong
# Region EU (primaria)
# - Control Plane: kong-cp-eu.internal (PostgreSQL master)
# - Data Plane: kong-dp-eu-1, kong-dp-eu-2, kong-dp-eu-3
# - DNS: api-eu.example.com -> LB -> Data Plane EU

# Region US (secondaria)
# - Data Plane: kong-dp-us-1, kong-dp-us-2
# - DNS: api-us.example.com -> LB -> Data Plane US
# - Configurazione sincronizzata dal Control Plane EU via hybrid mode

# DNS GeoDNS
# api.example.com -> GeoDNS -> api-eu.example.com | api-us.example.com
```

### GitOps per API Gateway Configuration

La configurazione del gateway deve essere versionata in Git e applicata tramite pipeline CI/CD,
seguendo il principio GitOps: il repository Git e la single source of truth per la
configurazione dell'infrastruttura.

```yaml
# .github/workflows/kong-deploy.yml
name: Deploy Kong Configuration

on:
  push:
    branches: [main]
    paths:
      - 'gateway/kong/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Installa deck (Kong declarative CLI)
        run: |
          curl -sL https://github.com/Kong/deck/releases/download/v1.35.0/deck_1.35.0_linux_amd64.tar.gz \
            | tar xz -C /usr/local/bin deck

      - name: Validazione della configurazione
        run: |
          deck file validate gateway/kong/kong.yml

      - name: Diff rispetto alla configurazione attuale
        run: |
          deck gateway diff gateway/kong/kong.yml \
            --kong-addr https://kong-admin.internal:8001 \
            --headers "Kong-Admin-Token:${{ secrets.KONG_ADMIN_TOKEN }}"

  deploy:
    needs: validate
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Installa deck
        run: |
          curl -sL https://github.com/Kong/deck/releases/download/v1.35.0/deck_1.35.0_linux_amd64.tar.gz \
            | tar xz -C /usr/local/bin deck

      - name: Applicazione della configurazione
        run: |
          deck gateway sync gateway/kong/kong.yml \
            --kong-addr https://kong-admin.internal:8001 \
            --headers "Kong-Admin-Token:${{ secrets.KONG_ADMIN_TOKEN }}" \
            --parallelism 5

      - name: Verifica post-deployment
        run: |
          curl -sf https://api.example.com/health || exit 1
          echo "Health check superato"
```

### API Lifecycle Management

Il ciclo di vita di un'API attraversa le seguenti fasi:

1. **Design** — Definizione della specifica OpenAPI. Revisione con i consumer. Allineamento
   con gli standard aziendali (naming, error format, pagination).

2. **Develop** — Implementazione del servizio backend. Sviluppo dei test. Documentazione
   degli endpoint.

3. **Test** — Validazione funzionale, test di performance, security testing. Deployment
   su ambiente di staging con configurazione gateway identica alla produzione.

4. **Deploy** — Rilascio graduale (canary, blue-green). Configurazione del gateway (routing,
   autenticazione, rate limiting). Aggiornamento della documentazione nel developer portal.

5. **Manage** — Monitoring delle metriche (traffico, latenza, errori). Gestione delle API key
   e delle sottoscrizioni. Supporto ai consumer.

6. **Retire** — Annuncio di deprecation. Periodo di migrazione. Rimozione progressiva.
   Dismessa definitiva.

### Disaster Recovery

Strategie di disaster recovery per l'API Gateway:

**Backup della configurazione** — Esportazione regolare della configurazione del gateway
(deck dump per Kong, export per APIM). Versionamento in Git come single source of truth.

**Failover automatico** — Deployment multi-region con health checking e DNS failover.
Se la region primaria non risponde, il traffico viene reindirizzato alla region secondaria.

**Recovery procedure** — Documentare la procedura di recovery: ripristino del database,
rideployment dei nodi, riapplicazione della configurazione, verifica degli health check,
smoke test sulle API critiche.

```bash
# Kong — Backup e restore della configurazione
# Backup
deck gateway dump \
  --kong-addr https://kong-admin.internal:8001 \
  --headers "Kong-Admin-Token:${KONG_ADMIN_TOKEN}" \
  -o kong-backup-$(date +%Y%m%d).yml

# Restore
deck gateway sync kong-backup-20260411.yml \
  --kong-addr https://kong-admin.internal:8001 \
  --headers "Kong-Admin-Token:${KONG_ADMIN_TOKEN}"

# Verifica post-restore
curl -sf https://api.example.com/health && echo "Gateway operativo" || echo "ERRORE: gateway non risponde"
```

---

## 13. Apache APISIX

### 13.1 Architettura e Data Plane

Apache APISIX è un API gateway cloud-native ad alte prestazioni, incubato dalla Apache Software Foundation e rilasciato sotto licenza Apache 2.0. A differenza di Kong, che storicamente si appoggia a PostgreSQL (o Cassandra) per lo storage della configurazione, APISIX utilizza **etcd** come unico data store, sfruttando il protocollo Raft per la consistenza distribuita e il meccanismo di watch per la propagazione istantanea delle modifiche a tutti i nodi del data plane.

L'architettura si compone di due livelli principali:

```
┌─────────────────────────────────────────────────┐
│                  Control Plane                   │
│  ┌──────────────┐     ┌──────────────────────┐  │
│  │  Dashboard /  │     │       etcd            │  │
│  │  Admin API    │────▶│  (Raft consensus)     │  │
│  └──────────────┘     └──────────────────────┘  │
└────────────────────────────┬────────────────────┘
                             │ watch / push
┌────────────────────────────▼────────────────────┐
│                   Data Plane                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │  APISIX   │  │  APISIX   │  │  APISIX   │    │
│  │  Worker 1 │  │  Worker 2 │  │  Worker N │    │
│  └──────────┘  └──────────┘  └──────────┘      │
│          nginx + LuaJIT + plugin chain          │
└─────────────────────────────────────────────────┘
```

Il data plane è costruito su **NGINX** + **LuaJIT** (OpenResty), garantendo prestazioni a bassa latenza comparabili a un reverse proxy nativo. APISIX supporta protocolli multipli: HTTP/1.1, HTTP/2, HTTP/3 (QUIC), gRPC, TCP/UDP stream, MQTT e WebSocket.

### 13.2 Installazione e Configurazione Base

Installazione via Helm chart su Kubernetes:

```bash
# Aggiungere il repository Helm ufficiale
helm repo add apisix https://charts.apiseven.com
helm repo update

# Installare con etcd integrato
helm install apisix apisix/apisix \
  --namespace apisix --create-namespace \
  --set etcd.enabled=true \
  --set etcd.replicaCount=3 \
  --set dashboard.enabled=true \
  --set ingress-controller.enabled=true \
  --set ingress-controller.config.apisix.serviceNamespace=apisix
```

Configurazione di una Route con upstream tramite Admin API:

```bash
# Creare un upstream con health check attivo
curl -X PUT http://127.0.0.1:9180/apisix/admin/upstreams/1 \
  -H "X-API-KEY: ${APISIX_ADMIN_KEY}" \
  -d '{
    "type": "roundrobin",
    "nodes": {
      "backend-v1:8080": 3,
      "backend-v2:8080": 1
    },
    "checks": {
      "active": {
        "http_path": "/health",
        "healthy": { "interval": 5, "successes": 2 },
        "unhealthy": { "interval": 3, "http_failures": 3 }
      }
    }
  }'

# Creare una Route con plugin di rate-limiting e autenticazione
curl -X PUT http://127.0.0.1:9180/apisix/admin/routes/1 \
  -H "X-API-KEY: ${APISIX_ADMIN_KEY}" \
  -d '{
    "uri": "/api/v1/orders/*",
    "methods": ["GET", "POST"],
    "upstream_id": 1,
    "plugins": {
      "key-auth": {},
      "limit-count": {
        "count": 100,
        "time_window": 60,
        "rejected_code": 429,
        "key_type": "var",
        "key": "consumer_name",
        "policy": "redis",
        "redis_host": "redis.apisix.svc",
        "redis_port": 6379
      },
      "prometheus": { "prefer_name": true }
    }
  }'
```

### 13.3 Sistema di Plugin

APISIX offre oltre **90 plugin** ufficiali, organizzati per categoria:

| Categoria | Plugin principali | Descrizione |
|-----------|------------------|-------------|
| Autenticazione | `key-auth`, `jwt-auth`, `openid-connect`, `hmac-auth`, `ldap-auth` | Validazione credenziali e token |
| Sicurezza | `cors`, `ip-restriction`, `ua-restriction`, `csrf`, `consumer-restriction` | Protezione a livello di rete e applicazione |
| Traffic Control | `limit-count`, `limit-req`, `limit-conn`, `traffic-split` | Rate limiting e gestione del traffico |
| Osservabilità | `prometheus`, `opentelemetry`, `skywalking`, `datadog`, `zipkin` | Metriche, tracing, logging |
| Trasformazione | `response-rewrite`, `proxy-rewrite`, `grpc-transcode`, `body-transformer` | Modifica request/response |
| AI / LLM | `ai-proxy`, `ai-prompt-guard`, `ai-semantic-cache`, `ai-rate-limiting` | Proxy verso modelli LLM |

A differenza di Kong, che usa esclusivamente Lua per lo sviluppo di plugin personalizzati, APISIX supporta plugin **multilingua** tramite il meccanismo di Plugin Runner. I linguaggi supportati includono:

- **Lua** — plugin nativi, massime prestazioni, accesso diretto alle API di NGINX
- **Go** — tramite `apisix-go-plugin-runner`, comunicazione via Unix socket
- **Java** — tramite `apisix-java-plugin-runner`, ideale per team enterprise
- **Python** — tramite `apisix-python-plugin-runner`, per prototipazione rapida
- **Wasm** — supporto WebAssembly per plugin portabili e sandbox-safe

Esempio di plugin personalizzato in Go:

```go
// plugins/custom_header.go
package plugins

import (
    "net/http"
    pkgHTTP "github.com/apache/apisix-go-plugin-runner/pkg/http"
    "github.com/apache/apisix-go-plugin-runner/pkg/plugin"
)

func init() {
    plugin.RegisterPlugin(&CustomHeader{})
}

type CustomHeader struct {
    plugin.DefaultPlugin
}

func (p *CustomHeader) Name() string {
    return "custom-header"
}

func (p *CustomHeader) RequestFilter(conf interface{}, w http.ResponseWriter,
    r pkgHTTP.Request) {
    r.Header().Set("X-Gateway", "apisix")
    r.Header().Set("X-Request-Start", fmt.Sprintf("%d", time.Now().UnixMilli()))
}
```

### 13.4 Confronto APISIX vs Kong

| Caratteristica | Apache APISIX | Kong Gateway |
|----------------|---------------|--------------|
| Storage configurazione | etcd (Raft) | PostgreSQL / DB-less YAML |
| Propagazione config | Push istantaneo (watch) | Pull periodico (5s default) |
| Plugin multilingua | Lua, Go, Java, Python, Wasm | Lua (+ Go con PDK esterno) |
| Supporto protocolli | HTTP/1-2-3, gRPC, TCP/UDP, MQTT | HTTP/1-2, gRPC, TCP/UDP |
| Licenza | Apache 2.0 | Apache 2.0 (OSS) / Proprietary (EE) |
| Dashboard | APISIX Dashboard (OSS) | Kong Manager (solo EE) |
| AI Gateway nativo | Sì (plugin ai-proxy, ai-prompt-guard) | Sì (Kong AI Gateway da 3.8) |
| Kubernetes Ingress | APISIX Ingress Controller | Kong Ingress Controller (KIC) |
| Community (GitHub stars) | ~14K | ~39K |
| Maintainer | Apache Software Foundation | Kong Inc. |

### 13.5 Modalità Standalone (DB-less)

Per ambienti edge o IoT dove etcd non è disponibile, APISIX supporta la modalità **standalone** con configurazione da file YAML:

```yaml
# conf/apisix.yaml
routes:
  - uri: /api/sensors/*
    upstream:
      type: roundrobin
      nodes:
        "sensor-backend:3000": 1
    plugins:
      key-auth: {}
      limit-req:
        rate: 50
        burst: 10
        rejected_code: 429
        key_type: var
        key: remote_addr

consumers:
  - username: iot-device-001
    plugins:
      key-auth:
        key: "sk-device-001-a7b3c9d2e1f0"
#END
```

La direttiva `#END` è obbligatoria per segnalare la fine del file di configurazione in modalità standalone.

---

## 14. Tyk Gateway

### 14.1 Architettura e Filosofia OAS-Native

Tyk è un API gateway open-source scritto interamente in **Go**, progettato per prestazioni elevate senza dipendenze da runtime esterni come LuaJIT o OpenResty. La caratteristica distintiva di Tyk rispetto ai concorrenti è il suo approccio **OAS-native**: anziché estrarre e trasformare la specifica OpenAPI in un formato proprietario interno, Tyk conserva il documento OpenAPI originale come definizione primaria dell'API, aggiungendo le estensioni gateway in un namespace dedicato (`x-tyk-api-gateway`).

```
┌────────────────────────────────────────────────┐
│                 Tyk Stack                       │
│                                                 │
│  ┌─────────────┐  ┌─────────────┐              │
│  │ Tyk Dashboard│  │   Tyk Portal │              │
│  │  (Control)   │  │  (Developer) │              │
│  └──────┬──────┘  └──────┬──────┘              │
│         │                │                      │
│  ┌──────▼────────────────▼──────┐              │
│  │         Redis (config +       │              │
│  │         rate limit counters)   │              │
│  └──────────────┬───────────────┘              │
│                 │                               │
│  ┌──────────────▼───────────────┐              │
│  │      Tyk Gateway (Go)        │              │
│  │   ┌──────────────────────┐   │              │
│  │   │   Middleware Chain    │   │              │
│  │   │  Auth → Transform →  │   │              │
│  │   │  Rate Limit → Proxy  │   │              │
│  │   └──────────────────────┘   │              │
│  └──────────────────────────────┘              │
└────────────────────────────────────────────────┘
```

### 14.2 Definizione API con OpenAPI 3.0

Il vantaggio dell'approccio OAS-native è che il documento OpenAPI rimane valido e importabile in qualsiasi tool dell'ecosistema (Swagger UI, Postman, Stoplight), senza necessità di conversione:

```yaml
# api-definition.yaml — specifica OpenAPI 3.0 con estensioni Tyk
openapi: "3.0.3"
info:
  title: "Orders API"
  version: "2.1.0"
x-tyk-api-gateway:
  info:
    name: orders-api
    state:
      active: true
  server:
    listenPath:
      value: /api/orders/
      strip: true
  upstream:
    url: http://orders-service.internal:8080
    rateLimit:
      enabled: true
      rate: 500
      per: 60
  middleware:
    global:
      pluginConfig:
        driver: goplugin
        bundle:
          enabled: true
          path: "/opt/tyk-plugins/auth-enrichment.so"
    operations:
      createOrder:
        validateRequest:
          enabled: true
          errorResponseCode: 422
paths:
  /orders:
    get:
      operationId: listOrders
      summary: "Lista ordini con paginazione"
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            minimum: 1
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
      responses:
        "200":
          description: "Lista paginata di ordini"
    post:
      operationId: createOrder
      summary: "Crea un nuovo ordine"
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/OrderCreate"
      responses:
        "201":
          description: "Ordine creato"
        "422":
          description: "Validazione fallita"
```

### 14.3 Universal Data Graph (UDG) e GraphQL Federation

Tyk offre il **Universal Data Graph (UDG)**, un motore di federazione GraphQL integrato nativamente nel gateway. UDG permette di comporre API REST, GraphQL e gRPC in un unico supergraph GraphQL senza richiedere componenti esterni:

```json
{
  "name": "unified-graph",
  "type": "UDG",
  "graphql": {
    "enabled": true,
    "execution_mode": "supergraph",
    "supergraph": {
      "subgraphs": [
        {
          "api_id": "users-subgraph-id",
          "url": "http://users-service:4001/graphql",
          "sdl": "extend type Query { users: [User] } type User @key(fields: \"id\") { id: ID! name: String! email: String! }"
        },
        {
          "api_id": "orders-subgraph-id",
          "url": "http://orders-service:4002/graphql",
          "sdl": "extend type Query { orders: [Order] } type Order @key(fields: \"id\") { id: ID! userId: ID! total: Float! } extend type User @key(fields: \"id\") { id: ID! @external orders: [Order] }"
        }
      ],
      "merged_sdl": "",
      "global_headers": {
        "X-Internal-Auth": "{{ .token }}"
      }
    },
    "schema": "",
    "version": "v2"
  }
}
```

UDG supporta anche la conversione automatica di endpoint REST in datasource GraphQL, permettendo di esporre API legacy tramite un'interfaccia GraphQL unificata senza modificare i backend.

### 14.4 Plugin Go e Middleware Personalizzati

Tyk supporta plugin scritti in Go compilati come shared object (`.so`), oltre a plugin in JavaScript (Otto engine), Python, gRPC e bundle Lua:

```go
// plugins/auth_enrichment.go
package main

import (
    "encoding/json"
    "net/http"
    "github.com/TykTechnologies/tyk/ctx"
)

// AuthEnrichment aggiunge claim JWT al header per i backend
func AuthEnrichment(rw http.ResponseWriter, r *http.Request) {
    session := ctx.GetSession(r)
    if session == nil {
        rw.WriteHeader(http.StatusUnauthorized)
        json.NewEncoder(rw).Encode(map[string]string{
            "error": "sessione non trovata",
        })
        return
    }

    // Propagare i metadata della sessione ai backend
    r.Header.Set("X-User-ID", session.MetaData["user_id"].(string))
    r.Header.Set("X-Org-ID", session.MetaData["org_id"].(string))
    r.Header.Set("X-User-Role", session.MetaData["role"].(string))
}

func main() {}
```

Compilazione del plugin:

```bash
# Il plugin deve essere compilato con la stessa versione Go del gateway
CGO_ENABLED=1 go build -buildmode=plugin -o auth-enrichment.so plugins/auth_enrichment.go

# Caricare il plugin nel gateway
cp auth-enrichment.so /opt/tyk-gateway/middleware/
```

### 14.5 Confronto Tyk vs Kong vs APISIX

| Caratteristica | Tyk | Kong | APISIX |
|----------------|-----|------|--------|
| Linguaggio core | Go | Lua/OpenResty | Lua/OpenResty |
| OpenAPI nativo | Sì (preserva doc originale) | No (formato interno) | No (formato interno) |
| GraphQL Federation | UDG integrato | Plugin (EE) | Plugin community |
| Storage | Redis | PostgreSQL/DB-less | etcd |
| Plugin languages | Go, JS, Python, gRPC, Lua | Lua (Go PDK esterno) | Lua, Go, Java, Python, Wasm |
| Licenza OSS | MPL 2.0 | Apache 2.0 | Apache 2.0 |
| REST-to-GraphQL | Sì (UDG) | No | No |
| Validazione OAS nativa | Sì (per operationId) | Sì (plugin oas-validation EE) | Sì (plugin request-validation) |

---

## 15. Envoy Gateway e Kubernetes Gateway API

### 15.1 Kubernetes Gateway API: lo Standard

La **Kubernetes Gateway API** è la specifica ufficiale che succede al tradizionale Ingress resource, offrendo un modello più espressivo, role-oriented e estensibile per il routing del traffico in cluster Kubernetes. La versione **v1.2** (rilasciata nel 2025) ha portato a GA diverse risorse:

| Risorsa | Canale | Funzione |
|---------|--------|----------|
| `GatewayClass` | GA (v1) | Definisce l'implementazione del gateway (es. Envoy, Istio, Kong) |
| `Gateway` | GA (v1) | Istanza di un gateway con listener, porte, TLS |
| `HTTPRoute` | GA (v1) | Routing HTTP/HTTPS con path, header, method matching |
| `GRPCRoute` | GA (v1) | Routing nativo per traffico gRPC |
| `ReferenceGrant` | GA (v1) | Permessi cross-namespace per risorse |
| `TLSRoute` | Beta | Routing TLS passthrough basato su SNI |
| `TCPRoute` | Alpha | Routing TCP generico |
| `UDPRoute` | Alpha | Routing UDP generico |
| `BackendTLSPolicy` | GA (v1.2) | Configurazione TLS verso backend (mTLS) |

Il modello role-oriented separa le responsabilità:

```
┌───────────────────────────────────────────────┐
│  Infra Provider  →  GatewayClass               │
│  (Platform team)    "Quale implementazione?"    │
├───────────────────────────────────────────────┤
│  Cluster Operator →  Gateway                   │
│  (Network team)      "Quali porte e domini?"   │
├───────────────────────────────────────────────┤
│  App Developer   →  HTTPRoute / GRPCRoute      │
│  (Dev team)         "Come arriva il traffico?"  │
└───────────────────────────────────────────────┘
```

### 15.2 Envoy Gateway: Implementazione di Riferimento

Envoy Gateway è il progetto ufficiale della CNCF che implementa la Gateway API utilizzando **Envoy Proxy** come data plane. Envoy comunica con il control plane tramite il protocollo **xDS** (discovery service), che permette aggiornamenti di configurazione senza restart.

Installazione:

```bash
# Installare Envoy Gateway via Helm
helm install envoy-gateway oci://docker.io/envoyproxy/gateway-helm \
  --version v1.3.0 \
  --namespace envoy-gateway-system \
  --create-namespace

# Verificare lo stato
kubectl wait --timeout=5m -n envoy-gateway-system \
  deployment/envoy-gateway --for=condition=Available
```

### 15.3 Configurazione Pratica

Definire un GatewayClass e un Gateway:

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: envoy-gateway
spec:
  controllerName: gateway.envoyproxy.io/gatewayclass-controller
---
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: production-gateway
  namespace: gateway-infra
spec:
  gatewayClassName: envoy-gateway
  listeners:
    - name: https
      protocol: HTTPS
      port: 443
      tls:
        mode: Terminate
        certificateRefs:
          - name: wildcard-tls-cert
            namespace: cert-manager
      allowedRoutes:
        namespaces:
          from: Selector
          selector:
            matchLabels:
              gateway-access: "true"
    - name: grpc
      protocol: HTTPS
      port: 443
      hostname: "grpc.example.com"
      tls:
        mode: Terminate
        certificateRefs:
          - name: grpc-tls-cert
      allowedRoutes:
        kinds:
          - kind: GRPCRoute
```

HTTPRoute con canary deployment e header-based routing:

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: orders-route
  namespace: orders
spec:
  parentRefs:
    - name: production-gateway
      namespace: gateway-infra
  hostnames:
    - "api.example.com"
  rules:
    # Canary: header X-Canary=true → v2
    - matches:
        - path:
            type: PathPrefix
            value: /api/orders
          headers:
            - name: X-Canary
              value: "true"
      backendRefs:
        - name: orders-v2
          port: 8080
    # Default: traffico ponderato 90/10
    - matches:
        - path:
            type: PathPrefix
            value: /api/orders
      backendRefs:
        - name: orders-v1
          port: 8080
          weight: 90
        - name: orders-v2
          port: 8080
          weight: 10
---
apiVersion: gateway.networking.k8s.io/v1
kind: GRPCRoute
metadata:
  name: payment-grpc
  namespace: payments
spec:
  parentRefs:
    - name: production-gateway
      namespace: gateway-infra
      sectionName: grpc
  hostnames:
    - "grpc.example.com"
  rules:
    - matches:
        - method:
            service: payment.v1.PaymentService
            method: ProcessPayment
      backendRefs:
        - name: payment-grpc-svc
          port: 50051
```

### 15.4 SecurityPolicy e Rate Limiting con Envoy Gateway

Envoy Gateway fornisce CRD personalizzati per sicurezza e traffic management:

```yaml
apiVersion: gateway.envoyproxy.io/v1alpha1
kind: SecurityPolicy
metadata:
  name: jwt-auth-policy
  namespace: gateway-infra
spec:
  targetRefs:
    - group: gateway.networking.k8s.io
      kind: Gateway
      name: production-gateway
  jwt:
    providers:
      - name: keycloak
        issuer: "https://keycloak.example.com/realms/production"
        audiences:
          - "api-gateway"
        remoteJWKS:
          uri: "https://keycloak.example.com/realms/production/protocol/openid-connect/certs"
          cacheDuration: 300s
---
apiVersion: gateway.envoyproxy.io/v1alpha1
kind: BackendTrafficPolicy
metadata:
  name: rate-limit-policy
  namespace: orders
spec:
  targetRefs:
    - group: gateway.networking.k8s.io
      kind: HTTPRoute
      name: orders-route
  rateLimit:
    type: Global
    global:
      rules:
        - clientSelectors:
            - headers:
                - name: X-API-Key
                  type: Distinct
          limit:
            requests: 100
            unit: Minute
        - limit:
            requests: 20
            unit: Minute
  circuitBreaker:
    maxConnections: 1024
    maxPendingRequests: 128
    maxRequests: 512
  timeout:
    tcp:
      connectTimeout: 5s
    http:
      requestTimeout: 30s
      idleTimeout: 300s
```

### 15.5 Confronto Implementazioni Gateway API

| Implementazione | Data Plane | Canale GA | Caratteristica distintiva |
|-----------------|------------|-----------|--------------------------|
| Envoy Gateway | Envoy Proxy | v1.2+ | Implementazione di riferimento CNCF, xDS nativo |
| Istio | Envoy Proxy | v1.0+ | Service mesh integrata, mTLS automatico |
| Kong (KIC) | Kong/OpenResty | v1.0+ | Ecosystem plugin maturo, Admin API |
| APISIX Ingress | APISIX | v1.0+ | Plugin multilingua, etcd |
| Traefik | Traefik | v1.0+ | Auto-discovery, Let's Encrypt nativo |
| Cilium | eBPF/Envoy | v1.0+ | Networking L3-L7 basato su eBPF |
| NGINX Gateway Fabric | NGINX | v1.0+ | Performance NGINX, config dichiarativa |

---

## 16. GraphQL Federation Gateway

### 16.1 Supergraph e Composizione di Subgraph

La **GraphQL Federation** è un'architettura che permette di comporre un unico schema GraphQL (il **supergraph**) a partire da molteplici servizi indipendenti (i **subgraph**). Ogni team possiede e sviluppa il proprio subgraph, definendo i tipi e le query di propria competenza. Il gateway di federazione si occupa della composizione degli schemi e del routing delle query.

L'evoluzione della federazione GraphQL ha attraversato diverse fasi:

| Versione | Anno | Innovazioni principali |
|----------|------|----------------------|
| Federation v1 | 2019 | `@key`, `@external`, `@requires`, `@provides` |
| Federation v2 | 2022 | `@shareable`, `@inaccessible`, `@override`, `@link`, composizione migliorata |
| Federation v2.5+ | 2024 | `@cost`, `@listSize`, demand control, progressive override |

### 16.2 Apollo Router

**Apollo Router** è il gateway di federazione di riferimento, riscritto in **Rust** per prestazioni superiori rispetto al precedente Apollo Gateway (Node.js). Apollo Router supporta:

- **Query planning** ottimizzato — decomposizione intelligente delle query in fetch plan paralleli verso i subgraph
- **Persisted queries (PQ)** — whitelist di query pre-approvate che impediscono l'esecuzione di query arbitrarie in produzione
- **Demand control** — budget di costo per query basato su direttive `@cost` e `@listSize`
- **Subscription tramite callback** — supporto a subscription GraphQL senza WebSocket persistente tra client e router
- **Coprocessor** — middleware esterno via HTTP/gRPC per logica custom (auth, logging, trasformazione)

Configurazione del router:

```yaml
# router.yaml — Apollo Router configuration
supergraph:
  introspection: false  # Disabilitare in produzione
  listen: 0.0.0.0:4000

headers:
  all:
    request:
      - propagate:
          named: "Authorization"
      - propagate:
          named: "X-Request-ID"
      - insert:
          name: "X-Router-Version"
          value: "1.0"

persisted_queries:
  enabled: true
  log_unpersisted: true
  safelist:
    enabled: true
    require_id: true  # Blocca query non registrate

limits:
  max_depth: 8
  max_height: 50
  max_aliases: 5
  max_root_fields: 10
  warn_only: false
  parser_max_tokens: 15000
  parser_max_recursion: 500

demand_control:
  enabled: true
  mode: enforce  # measure | enforce
  strategy:
    static_estimated:
      list_size: 10
      max: 1000  # Budget massimo per query

telemetry:
  instrumentation:
    spans:
      mode: spec_compliant
  exporters:
    tracing:
      otlp:
        enabled: true
        endpoint: "http://otel-collector:4317"
        protocol: grpc
    metrics:
      prometheus:
        enabled: true
        listen: 0.0.0.0:9090
        path: /metrics

coprocessor:
  url: http://auth-coprocessor:8081
  router:
    request:
      headers: true
      body: false
      context: true
  subgraph:
    all:
      request:
        headers: true
```

### 16.3 Definizione di Subgraph con Federation v2

Esempio di due subgraph che collaborano tramite entity resolution:

```graphql
# === subgraph: users ===
extend schema @link(url: "https://specs.apollo.dev/federation/v2.5",
  import: ["@key", "@shareable"])

type Query {
  user(id: ID!): User
  users(limit: Int = 20, offset: Int = 0): [User!]!
}

type User @key(fields: "id") {
  id: ID!
  email: String!
  name: String!
  role: Role!
  createdAt: DateTime!
}

enum Role {
  ADMIN
  EDITOR
  VIEWER
}

# === subgraph: orders ===
extend schema @link(url: "https://specs.apollo.dev/federation/v2.5",
  import: ["@key", "@external", "@requires", "@shareable", "@cost", "@listSize"])

type Query {
  order(id: ID!): Order
  ordersByUser(userId: ID!, status: OrderStatus): [Order!]! @listSize(assumedSize: 10, sizedFields: ["orders"])
}

type Order @key(fields: "id") {
  id: ID!
  userId: ID!
  items: [OrderItem!]! @cost(weight: 5)
  total: Float!
  status: OrderStatus!
  createdAt: DateTime!
}

type OrderItem {
  productId: ID!
  name: String!
  quantity: Int!
  unitPrice: Float!
}

enum OrderStatus {
  PENDING
  CONFIRMED
  SHIPPED
  DELIVERED
  CANCELLED
}

# Estendere User dal subgraph users
type User @key(fields: "id") {
  id: ID! @external
  orders: [Order!]! @requires(fields: "id")
}
```

### 16.4 Composizione e Schema Registry

Il workflow di composizione utilizza il **Rover CLI**:

```bash
# Pubblicare i subgraph nel registry
rover subgraph publish my-supergraph@production \
  --schema ./users/schema.graphql \
  --name users \
  --routing-url http://users-service:4001/graphql

rover subgraph publish my-supergraph@production \
  --schema ./orders/schema.graphql \
  --name orders \
  --routing-url http://orders-service:4002/graphql

# Verificare la composizione locale (CI/CD check)
rover subgraph check my-supergraph@production \
  --schema ./orders/schema.graphql \
  --name orders

# Comporre il supergraph localmente per test
rover supergraph compose --config supergraph.yaml > supergraph.graphql
```

File di composizione locale:

```yaml
# supergraph.yaml
federation_version: =2.5.0
subgraphs:
  users:
    routing_url: http://users-service:4001/graphql
    schema:
      file: ./users/schema.graphql
  orders:
    routing_url: http://orders-service:4002/graphql
    schema:
      file: ./orders/schema.graphql
```

### 16.5 Sicurezza del GraphQL Gateway

| Minaccia | Mitigazione nel Router | Configurazione |
|----------|----------------------|----------------|
| Query profonde (depth attack) | `limits.max_depth` | 8-15 livelli max |
| Query ampie (breadth attack) | `limits.max_height` | 50-200 nodi max |
| Alias bombing | `limits.max_aliases` | 5-10 alias max |
| Query costose | Demand control `@cost` | Budget numerico per query |
| Introspection leak | `supergraph.introspection: false` | Disabilitare in prod |
| Query arbitrarie | Persisted queries con safelist | `require_id: true` |
| Batching abuse | `limits.max_root_fields` | 10-20 root fields |
| Schema reconnaissance | Schema visibility policy | Nascondere tipi interni |

---

## 17. AI Gateway e LLM Proxy

### 17.1 Perché un AI Gateway

L'adozione massiva di Large Language Model (LLM) in produzione ha creato nuove sfide che un API gateway tradizionale non è progettato per gestire:

- **Token-based billing** — i costi degli LLM sono calcolati per token, non per richiesta; il rate limiting tradizionale (request/minuto) è insufficiente
- **Latenza variabile** — le risposte degli LLM possono richiedere da 200ms a 60+ secondi per generazioni lunghe
- **Streaming** — la maggior parte delle risposte LLM utilizza Server-Sent Events (SSE) per lo streaming token-by-token
- **Prompt injection** — le richieste possono contenere istruzioni malevole che tentano di manipolare il modello
- **Multi-model routing** — le applicazioni necessitano di instradare verso modelli diversi in base al task (GPT-4o per ragionamento, Claude per codice, Gemini per visione)
- **Cost governance** — senza controllo centralizzato, i costi per API LLM possono crescere in modo esponenziale

### 17.2 Architettura di un AI Gateway

```
┌──────────────────────────────────────────────────────┐
│                    AI Gateway                         │
│                                                       │
│  ┌─────────┐  ┌──────────┐  ┌────────────────────┐  │
│  │ Prompt   │  │ Semantic  │  │  Token-Aware       │  │
│  │ Guard    │  │ Cache     │  │  Rate Limiter      │  │
│  │          │  │ (Vector   │  │  (TPM / RPM /      │  │
│  │ PII      │  │  Similarity│ │   cost-based)      │  │
│  │ Sanitize │  │  Search)  │  │                    │  │
│  └────┬─────┘  └─────┬────┘  └────────┬───────────┘  │
│       │              │               │                │
│  ┌────▼──────────────▼───────────────▼───────────┐   │
│  │            Model Router / Load Balancer         │   │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────────┐    │   │
│  │  │ OpenAI  │ │ Anthropic│ │ Azure OpenAI │    │   │
│  │  │ GPT-4o  │ │ Claude   │ │  GPT-4o      │    │   │
│  │  └─────────┘ └──────────┘ └──────────────┘    │   │
│  │  ┌─────────┐ ┌──────────┐ ┌──────────────┐    │   │
│  │  │ Google  │ │ Self-    │ │ Hugging Face │    │   │
│  │  │ Gemini  │ │ Hosted   │ │  Inference   │    │   │
│  │  └─────────┘ └──────────┘ └──────────────┘    │   │
│  └────────────────────────────────────────────────┘   │
│                                                       │
│  ┌────────────────────────────────────────────────┐   │
│  │        Analytics & Cost Tracking                │   │
│  │  Token usage │ Latency │ Cost/team │ Model perf │  │
│  └────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

### 17.3 Kong AI Gateway

Kong ha introdotto funzionalità AI gateway a partire dalla versione **3.8**, espandendole progressivamente:

| Versione | Funzionalità AI |
|----------|----------------|
| Kong 3.8 | Plugin `ai-proxy` base, supporto OpenAI/Anthropic/Azure/Cohere |
| Kong 3.9 | Semantic caching, AI rate limiting per token, LLM load balancing |
| Kong 3.10 | PII sanitization, RAG injection, Hugging Face support, streaming analytics |

Configurazione del plugin `ai-proxy` per multi-model routing:

```yaml
# Kong declarative config — AI Gateway
_format_version: "3.0"

services:
  - name: ai-llm-service
    url: http://localhost:8001  # placeholder, il plugin gestisce il routing

routes:
  - name: ai-chat-route
    service: ai-llm-service
    paths:
      - /ai/chat
    methods:
      - POST

plugins:
  - name: ai-proxy
    route: ai-chat-route
    config:
      route_type: llm/v1/chat
      model:
        provider: openai
        name: gpt-4o
        options:
          max_tokens: 4096
          temperature: 0.7
      auth:
        header_name: Authorization
        header_value: "Bearer ${OPENAI_API_KEY}"
      logging:
        log_statistics: true
        log_payloads: false  # Non loggare prompt/risposte per privacy

  - name: ai-rate-limiting-advanced
    route: ai-chat-route
    config:
      limit_by: consumer
      window_size: 60
      window_type: sliding
      strategy: redis
      tokens_count_strategy: total  # input + output tokens
      redis:
        host: redis.kong.svc
        port: 6379
      sync_rate: 1
      dictionary_name: kong_rate_limiting_counters
      limits:
        - tokens_per_minute: 100000
        - requests_per_minute: 60

  - name: ai-prompt-guard
    route: ai-chat-route
    config:
      allow_patterns:
        - ".*"
      deny_patterns:
        - "(?i)(ignore previous|ignore all|disregard|forget your)\\s+(instructions|rules|guidelines|system prompt)"
        - "(?i)you are now (DAN|evil|unrestricted|unfiltered)"
        - "(?i)(reveal|show|print|output)\\s+(your|the)\\s+(system|initial|original)\\s+prompt"
        - "(?i)\\b(sudo|jailbreak|bypass|override)\\b.*\\b(mode|filter|safety|restriction)\\b"
      max_request_body_size: 65536

  - name: ai-semantic-cache
    route: ai-chat-route
    config:
      embeddings:
        provider: openai
        name: text-embedding-3-small
        auth:
          header_name: Authorization
          header_value: "Bearer ${OPENAI_API_KEY}"
      vectordb:
        provider: redis
        config:
          host: redis-vector.kong.svc
          port: 6379
          dimensions: 1536
          distance_metric: cosine
      similarity_threshold: 0.92
      cache_ttl: 3600
```

### 17.4 APISIX AI Gateway

Apache APISIX offre un set di plugin AI introdotti a partire dalla versione 3.9:

```bash
# Configurare ai-proxy su APISIX per Claude
curl -X PUT http://127.0.0.1:9180/apisix/admin/routes/ai-chat \
  -H "X-API-KEY: ${APISIX_ADMIN_KEY}" \
  -d '{
    "uri": "/v1/ai/chat",
    "methods": ["POST"],
    "plugins": {
      "ai-proxy": {
        "provider": "anthropic",
        "auth": {
          "type": "header",
          "name": "x-api-key",
          "value": "'"${ANTHROPIC_API_KEY}"'"
        },
        "model": {
          "name": "claude-sonnet-4-20250514",
          "max_tokens": 8192
        },
        "passthrough": false
      },
      "ai-prompt-guard": {
        "match_mode": "any",
        "deny_patterns": [
          "(?i)ignore.*instructions",
          "(?i)system.*prompt.*reveal"
        ],
        "denied_response": {
          "status_code": 400,
          "body": "{\"error\": \"Richiesta bloccata dal prompt guard\"}"
        }
      },
      "ai-rate-limiting": {
        "limit_by": "consumer",
        "tokens_per_minute": 50000,
        "requests_per_minute": 30,
        "rejected_code": 429
      }
    },
    "upstream": {
      "type": "roundrobin",
      "nodes": { "api.anthropic.com:443": 1 },
      "scheme": "https"
    }
  }'
```

### 17.5 Semantic Cache: Funzionamento

Il semantic cache è una delle innovazioni più significative degli AI gateway. A differenza del cache tradizionale (basato su hash esatto della richiesta), il semantic cache utilizza **embedding vettoriali** per identificare prompt semanticamente simili:

```
Prompt A: "Quali sono i vantaggi di Kubernetes?"
Prompt B: "Elenca i benefici dell'uso di Kubernetes"
                    │
                    ▼
         ┌─────────────────┐
         │ Embedding Model  │
         │ (text-embedding  │
         │  -3-small)       │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Vector Database  │
         │ cosine_sim(A,B)  │
         │   = 0.96         │
         │   > threshold    │
         │     (0.92)       │
         └────────┬────────┘
                  │
                  ▼
         Cache HIT → risposta cached
         (risparmio token + latenza ~10ms vs ~2000ms)
```

Il risparmio medio è significativo:

| Metrica | Senza cache | Con semantic cache (hit rate 40%) |
|---------|-------------|----------------------------------|
| Costo token/giorno | $150 | $90 (-40%) |
| Latenza media | 1800ms | 720ms (-60%) |
| Throughput effettivo | 100 RPM | 165 RPM (+65%) |

### 17.6 Confronto AI Gateway Solutions

| Caratteristica | Kong AI GW | APISIX AI | Azure APIM GenAI | Portkey | LiteLLM |
|----------------|------------|-----------|-------------------|---------|---------|
| Tipo | Plugin su gateway | Plugin su gateway | Policy su APIM | SaaS dedicato | Proxy OSS |
| Provider supportati | 10+ | 6+ | Azure OpenAI + OpenAI | 200+ | 100+ |
| Semantic cache | Sì (Redis Vector) | Sì | Sì (Azure Cache) | Sì | Community |
| Prompt guard | Regex + ML | Regex | Azure Content Safety | Sì (guardrails) | No |
| Token rate limiting | Sì (TPM/RPM) | Sì | Sì (TPM nativo) | Sì | Sì |
| Cost tracking | Sì | Base | Sì (Azure Monitor) | Sì (dettagliato) | Sì |
| PII redaction | Sì (3.10+) | No | Sì (Presidio) | No | No |
| Load balancing LLM | Round-robin, weighted | Round-robin | Priority + fallback | Sì (avanzato) | Sì |
| Licenza | Apache 2.0 / EE | Apache 2.0 | Proprietary | Proprietary | MIT |

---

## 18. Streaming: WebSocket e Server-Sent Events

### 18.1 Protocolli di Streaming negli API Gateway

Le applicazioni moderne — in particolare quelle basate su AI/LLM, dashboard real-time, trading, IoT e collaborative editing — richiedono protocolli di comunicazione bidirezionale o push server-to-client. I due protocolli principali sono:

| Caratteristica | WebSocket | Server-Sent Events (SSE) |
|----------------|-----------|--------------------------|
| Direzione | Bidirezionale (full-duplex) | Unidirezionale (server → client) |
| Protocollo | ws:// / wss:// (upgrade da HTTP) | HTTP standard (text/event-stream) |
| Reconnection | Manuale (client-side) | Automatica (EventSource API) |
| Formato dati | Binario + testo | Solo testo (UTF-8) |
| Browser support | Tutti i moderni | Tutti i moderni |
| Proxy/CDN traversal | Problematico (richiede upgrade) | Trasparente (HTTP standard) |
| Caso d'uso tipico | Chat, gaming, collaborative editing | LLM streaming, notifiche, feed |

### 18.2 Configurazione WebSocket negli API Gateway

#### Kong — WebSocket Proxying

```yaml
# Kong declarative — WebSocket service
_format_version: "3.0"

services:
  - name: ws-chat-service
    url: http://chat-backend:8080
    protocol: ws  # oppure wss per TLS al backend

routes:
  - name: ws-chat-route
    service: ws-chat-service
    paths:
      - /ws/chat
    protocols:
      - https  # Il client si connette via HTTPS, l'upgrade avviene automaticamente

plugins:
  - name: ip-restriction
    route: ws-chat-route
    config:
      allow:
        - 10.0.0.0/8
        - 172.16.0.0/12

  - name: rate-limiting
    route: ws-chat-route
    config:
      second: 5  # Max 5 connection upgrade/secondo per IP
      policy: redis
      redis_host: redis.kong.svc
```

Kong supporta nativamente i WebSocket dalla versione 3.0, gestendo automaticamente l'upgrade del protocollo HTTP → WebSocket. Il plugin `websocket-size-limit` (Enterprise) permette di limitare la dimensione dei frame WebSocket per prevenire abusi.

#### Envoy Gateway — WebSocket

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: websocket-route
  namespace: realtime
spec:
  parentRefs:
    - name: production-gateway
      namespace: gateway-infra
  hostnames:
    - "ws.example.com"
  rules:
    - matches:
        - path:
            type: PathPrefix
            value: /ws
      backendRefs:
        - name: websocket-backend
          port: 8080
      timeouts:
        backendRequest: 3600s  # 1 ora per connessioni long-lived
---
# ClientTrafficPolicy per abilitare WebSocket upgrade
apiVersion: gateway.envoyproxy.io/v1alpha1
kind: ClientTrafficPolicy
metadata:
  name: websocket-policy
  namespace: gateway-infra
spec:
  targetRefs:
    - group: gateway.networking.k8s.io
      kind: Gateway
      name: production-gateway
  connection:
    bufferLimit: 32768
  http1:
    enableTrailers: true
  timeout:
    http:
      idleTimeout: 3600s
```

### 18.3 Server-Sent Events per AI/LLM Streaming

SSE è il protocollo predominante per lo streaming delle risposte LLM. Il formato è standardizzato:

```
data: {"id":"chatcmpl-abc","choices":[{"delta":{"content":"Ciao"}}]}

data: {"id":"chatcmpl-abc","choices":[{"delta":{"content":", come"}}]}

data: {"id":"chatcmpl-abc","choices":[{"delta":{"content":" posso"}}]}

data: {"id":"chatcmpl-abc","choices":[{"delta":{"content":" aiutarti?"}}]}

data: [DONE]
```

La configurazione critica per SSE negli API gateway è la **disabilitazione del response buffering**:

#### NGINX / Kong — SSE

```nginx
# nginx.conf snippet per SSE
location /ai/chat/stream {
    proxy_pass http://ai-backend;

    # CRITICO per SSE: disabilitare il buffering
    proxy_buffering off;
    proxy_cache off;

    # Chunked transfer encoding
    proxy_http_version 1.1;
    proxy_set_header Connection "";

    # Timeout lunghi per generazioni lente
    proxy_read_timeout 300s;
    proxy_send_timeout 300s;

    # Header SSE
    add_header Content-Type text/event-stream;
    add_header Cache-Control no-cache;
    add_header X-Accel-Buffering no;  # Disabilita buffering nel reverse proxy upstream
}
```

#### Traefik — SSE

```yaml
# Traefik dynamic config — SSE
http:
  routers:
    ai-stream:
      rule: "Host(`api.example.com`) && PathPrefix(`/ai/stream`)"
      service: ai-backend
      middlewares:
        - sse-headers

  middlewares:
    sse-headers:
      headers:
        customResponseHeaders:
          X-Accel-Buffering: "no"
          Cache-Control: "no-cache"

  services:
    ai-backend:
      loadBalancer:
        responseForwarding:
          flushInterval: "1ms"  # Flush immediato per SSE
        servers:
          - url: "http://ai-service:8080"
        healthCheck:
          path: /health
          interval: 10s
```

#### Azure APIM — SSE Policy

```xml
<!-- Azure APIM policy per SSE streaming -->
<policies>
  <inbound>
    <base />
    <set-backend-service base-url="https://my-openai.openai.azure.com" />
    <authentication-managed-identity resource="https://cognitiveservices.azure.com" />
  </inbound>
  <backend>
    <forward-request timeout="300"
                     follow-redirects="false"
                     buffer-request-body="false"
                     buffer-response="false"
                     fail-on-error-status-code="true" />
  </backend>
  <outbound>
    <base />
    <!-- Non bufferizzare la risposta per streaming SSE -->
    <set-header name="Cache-Control" exists-action="override">
      <value>no-cache</value>
    </set-header>
  </outbound>
</policies>
```

### 18.4 Checklist Streaming

| Verifica | WebSocket | SSE |
|----------|-----------|-----|
| Buffering disabilitato | ✓ `proxy_buffering off` | ✓ `proxy_buffering off` + `X-Accel-Buffering: no` |
| Timeout adeguato | ✓ idle timeout 1h+ | ✓ read timeout 5min+ |
| Chunked encoding | N/A (frame-based) | ✓ `Transfer-Encoding: chunked` |
| Health check | ✓ ping/pong frame | ✓ comment line (`:keepalive`) |
| Rate limiting | Per connessione/upgrade | Per richiesta iniziale |
| Autenticazione | Al momento dell'upgrade | Header Authorization o query param |
| CDN compatibilità | Richiede CDN WebSocket-aware | Compatibile (HTTP standard) |
| Load balancer | Sticky session consigliato | Stateless, qualsiasi algoritmo |

---

## 19. Sicurezza Avanzata — OWASP API Top 10 e Zero Trust

### 19.1 OWASP API Security Top 10 (2023)

L'**OWASP API Security Top 10** (edizione 2023, ancora il riferimento corrente nel 2025-2026) identifica le vulnerabilità più critiche nelle API. Per ciascun rischio, il gateway può implementare mitigazioni specifiche:

| # | Rischio OWASP | Descrizione | Mitigazione Gateway |
|---|--------------|-------------|---------------------|
| API1 | **Broken Object Level Authorization (BOLA)** | Accesso a risorse di altri utenti manipolando gli ID | OPA/rego policy per validare ownership; log audit per pattern detection |
| API2 | **Broken Authentication** | Falle nell'autenticazione (credential stuffing, token deboli) | JWT validation con JWKS rotation, mTLS, rate limiting su /auth |
| API3 | **Broken Object Property Level Authorization** | Esposizione di proprietà sensibili nella risposta | Response transformation per filtrare campi; schema validation |
| API4 | **Unrestricted Resource Consumption** | Assenza di limiti su risorse (CPU, bandwidth, query) | Rate limiting (token bucket), request size limit, pagination enforcement |
| API5 | **Broken Function Level Authorization** | Accesso a funzioni admin senza autorizzazione adeguata | RBAC enforcement nel gateway; path-based policy per /admin/* |
| API6 | **Unrestricted Access to Sensitive Business Flows** | Abuso automatizzato di flussi business (acquisti, registrazioni) | Bot detection, CAPTCHA integration, behavioral rate limiting |
| API7 | **Server-Side Request Forgery (SSRF)** | Il server effettua richieste verso URL controllati dall'attaccante | URL allowlisting nel gateway; blocco di IP privati nelle risposte redirect |
| API8 | **Security Misconfiguration** | Configurazione errata (CORS permissivi, error verbosi, default cred) | Default-deny CORS; custom error pages senza stack trace; security headers |
| API9 | **Improper Inventory Management** | API non documentate, versioni obsolete esposte, shadow API | API discovery automatica; deprecation policy; versioning enforcement |
| API10 | **Unsafe Consumption of APIs** | Il backend consuma API di terze parti senza validazione | Egress gateway con allowlist; response validation; timeout stringenti |

### 19.2 Implementazione OWASP nel Gateway — Esempi Pratici

#### BOLA Protection con OPA (Open Policy Agent)

```yaml
# Kong plugin OPA per BOLA check
plugins:
  - name: opa
    route: user-resources-route
    config:
      opa_host: "http://opa-sidecar:8181"
      opa_path: "/v1/data/api/authz/allow"
      include_body: false
      include_parsed_json_body: true
      include_uri_captures: true
      include_consumer: true
```

Policy Rego corrispondente:

```rego
# policy/api/authz.rego
package api.authz

import rego.v1

default allow := false

# L'utente può accedere solo alle proprie risorse
allow if {
    input.method == "GET"
    input.path = ["api", "v1", "users", user_id, _]
    input.consumer.custom_id == user_id
}

# Gli admin possono accedere a tutte le risorse
allow if {
    input.consumer.groups[_] == "admin"
}

# Negare accesso cross-tenant
deny_reason := "BOLA: accesso a risorsa di altro utente" if {
    input.path = ["api", "v1", "users", user_id, _]
    input.consumer.custom_id != user_id
    not input.consumer.groups[_] == "admin"
}
```

#### Unrestricted Resource Consumption — Difesa Multi-Livello

```yaml
# Kong — stack completo di protezione API4
plugins:
  # 1. Rate limiting per consumer
  - name: rate-limiting-advanced
    config:
      limit:
        - second: 10
        - minute: 200
        - hour: 5000
      window_type: sliding
      strategy: redis
      sync_rate: 1
      redis:
        host: redis.kong.svc

  # 2. Limite dimensione richiesta
  - name: request-size-limiting
    config:
      allowed_payload_size: 1  # 1 MB max
      size_unit: megabytes
      require_content_length: true

  # 3. Request termination per endpoint deprecati
  - name: request-termination
    route: deprecated-v1-route
    config:
      status_code: 410
      message: "API v1 deprecata. Migrare a v2."
      content_type: "application/json"

  # 4. Timeout stringenti
  - name: proxy-timeout
    config:
      connect_timeout: 5000    # 5s
      send_timeout: 30000      # 30s
      read_timeout: 30000      # 30s
```

### 19.3 Zero Trust Architecture al Layer Gateway

Il modello **Zero Trust** ("non fidarsi mai, verificare sempre") applicato agli API gateway richiede:

```
┌─────────────────────────────────────────────────────┐
│                  Zero Trust Gateway                  │
│                                                      │
│  1. IDENTITY VERIFICATION                            │
│     ├── mTLS (certificato client obbligatorio)       │
│     ├── JWT validation (firma, scadenza, audience)   │
│     ├── Token binding (DPoP — RFC 9449)              │
│     └── Device attestation                           │
│                                                      │
│  2. CONTINUOUS AUTHORIZATION                         │
│     ├── Per-request policy evaluation (OPA)          │
│     ├── Context-aware decisions (IP, geo, time)      │
│     ├── Step-up auth per operazioni sensibili        │
│     └── Session risk scoring                         │
│                                                      │
│  3. LEAST PRIVILEGE                                  │
│     ├── Scope-based access (OAuth2 scopes)           │
│     ├── Field-level authorization (GraphQL)          │
│     ├── Response filtering (rimuovere campi PII)     │
│     └── Temporal access (token short-lived, 5-15min) │
│                                                      │
│  4. ASSUME BREACH                                    │
│     ├── Encrypt in transit (TLS 1.3 minimo)          │
│     ├── Encrypt at rest (config, secrets)            │
│     ├── Audit log completo (chi, cosa, quando)       │
│     └── Anomaly detection (baseline + deviazione)    │
└─────────────────────────────────────────────────────┘
```

#### mTLS End-to-End con Kong

```yaml
# Kong — mTLS client verification
_format_version: "3.0"

certificates:
  - cert: |
      -----BEGIN CERTIFICATE-----
      ... (CA root per la validazione client) ...
      -----END CERTIFICATE-----
    key: |
      -----BEGIN PRIVATE KEY-----
      ... (chiave privata del gateway) ...
      -----END PRIVATE KEY-----

plugins:
  - name: mtls-auth
    config:
      ca_certificates:
        - ca-cert-uuid-from-kong-admin
      revocation_check_mode: SKIP  # oppure IGNORE_CA_ERROR per CRL/OCSP
      skip_consumer_lookup: false
      authenticated_group_by: CN  # Raggruppare consumer per Common Name
      cert_cache_ttl: 60
      http_proxy_host: null
      default_consumer: null
      allow_partial_chain: false

  # Policy OPA che valida anche il certificato client
  - name: opa
    config:
      opa_host: "http://opa:8181"
      opa_path: "/v1/data/zerotrust/allow"
      include_cert_info: true
```

### 19.4 Security Headers e Hardening

Configurazione completa degli header di sicurezza da applicare a tutte le risposte del gateway:

```yaml
# Kong — response-transformer per security headers
plugins:
  - name: response-transformer
    config:
      add:
        headers:
          - "Strict-Transport-Security: max-age=63072000; includeSubDomains; preload"
          - "X-Content-Type-Options: nosniff"
          - "X-Frame-Options: DENY"
          - "Referrer-Policy: strict-origin-when-cross-origin"
          - "Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()"
          - "Content-Security-Policy: default-src 'self'; frame-ancestors 'none'"
          - "X-Permitted-Cross-Domain-Policies: none"
      remove:
        headers:
          - "Server"           # Non rivelare il software del backend
          - "X-Powered-By"     # Non rivelare il framework
          - "X-AspNet-Version" # Non rivelare la versione .NET
```

### 19.5 Audit Logging per Compliance

```yaml
# Kong — configurazione logging per compliance (SOC 2, GDPR, PCI-DSS)
plugins:
  - name: tcp-log
    config:
      host: siem.internal
      port: 5514
      tls: true
      custom_fields_by_lua:
        audit_event: |
          return {
            timestamp = ngx.now(),
            gateway_id = kong.node.get_id(),
            consumer = kong.client.get_consumer(),
            route = kong.router.get_route(),
            service = kong.router.get_service(),
            client_ip = kong.client.get_forwarded_ip(),
            method = kong.request.get_method(),
            path = kong.request.get_path(),
            status = kong.response.get_status(),
            latency = kong.response.get_latency(),
            -- MAI loggare il body della richiesta (può contenere PII/secrets)
          }
```

---

## 20. OpenAPI-First e Specification-Driven Gateway

### 20.1 Design-First vs Code-First

L'approccio **specification-driven** (o **API-first**) inverte il flusso tradizionale di sviluppo: anziché scrivere prima il codice e poi generare la documentazione, si parte dalla specifica OpenAPI come "single source of truth":

```
┌─────────────────────────────────────────────────────┐
│              Design-First Workflow                   │
│                                                      │
│  1. DESIGN                                           │
│     └── Scrivere la specifica OpenAPI 3.x            │
│         (collaborazione tra team API, frontend, QA)  │
│                                                      │
│  2. VALIDATE                                         │
│     └── Linting con Spectral / Vacuum                │
│         (regole di stile, naming, security)           │
│                                                      │
│  3. MOCK                                             │
│     └── Prism / Microcks per mock server             │
│         (frontend può sviluppare in parallelo)       │
│                                                      │
│  4. IMPLEMENT                                        │
│     └── Code generation / manual implementation      │
│         (il gateway valida la conformità)             │
│                                                      │
│  5. TEST                                             │
│     └── Contract testing (Schemathesis, Dredd)       │
│         (verifica che l'implementazione rispetti      │
│          il contratto OpenAPI)                        │
│                                                      │
│  6. DEPLOY                                           │
│     └── Gateway importa la specifica                 │
│         (route, validazione, docs automatici)         │
│                                                      │
│  7. GOVERN                                           │
│     └── API Catalog + Versioning + Deprecation       │
└─────────────────────────────────────────────────────┘
```

### 20.2 OpenAPI 3.1 e 3.2 — Evoluzioni Chiave

La specifica OpenAPI ha subito importanti evoluzioni:

| Versione | Data | Novità principali |
|----------|------|-------------------|
| OpenAPI 3.0 | 2017 | Links, callbacks, cookie parameters, `oneOf`/`anyOf` |
| OpenAPI 3.1 | 2021 | Allineamento completo a JSON Schema 2020-12, webhooks, `pathItems` riutilizzabili |
| OpenAPI 3.2 | 2025 (Settembre) | Overlay support nativo, miglioramento `x-` extensions, type unions semplificate |

Le implicazioni per i gateway:

- **JSON Schema 2020-12** (da 3.1) — supporto completo per `if/then/else`, `$dynamicRef`, pattern properties, che permette validazioni più sofisticate direttamente nel gateway
- **Webhooks** — il gateway può validare anche le notifiche in uscita
- **Overlay** — permette di applicare trasformazioni alla specifica base senza modificarla (utile per environment-specific config)

### 20.3 Linting e Governance con Spectral

**Spectral** è lo standard de facto per il linting delle specifiche OpenAPI. Le regole personalizzate garantiscono la consistenza dell'API design:

```yaml
# .spectral.yaml — regole di governance API
extends:
  - spectral:oas

rules:
  # Sicurezza: tutti gli endpoint devono avere security scheme
  operation-security-defined:
    severity: error
    given: "$.paths[*][get,post,put,patch,delete]"
    then:
      - field: security
        function: truthy

  # Naming: path in kebab-case
  path-kebab-case:
    severity: warn
    given: "$.paths"
    then:
      function: pattern
      functionOptions:
        match: "^(/[a-z][a-z0-9-]*)+$"

  # Paginazione obbligatoria per liste
  pagination-required:
    severity: warn
    message: "Le operazioni che ritornano array dovrebbero supportare paginazione"
    given: "$.paths[*].get.responses.200.content.application/json.schema"
    then:
      - field: properties.page
        function: truthy

  # Versioning nel path
  api-version-in-path:
    severity: error
    given: "$.paths"
    then:
      function: pattern
      functionOptions:
        match: "^/v[0-9]+/"

  # Response envelope consistente
  response-envelope:
    severity: warn
    given: "$.paths[*][*].responses[200,201].content.application/json.schema"
    then:
      - field: properties.data
        function: truthy
      - field: properties.meta
        function: truthy

  # Niente schema inline — usare $ref
  no-inline-schema:
    severity: warn
    given: "$.paths[*][*].requestBody.content.application/json.schema"
    then:
      field: "$ref"
      function: truthy
```

Esecuzione nel CI/CD:

```bash
# Installare Spectral
npm install -g @stoplight/spectral-cli

# Linting della specifica
spectral lint openapi.yaml --ruleset .spectral.yaml --format stylish

# In CI — fail su errori
spectral lint openapi.yaml --ruleset .spectral.yaml --fail-severity error
```

### 20.4 Validazione Request/Response nel Gateway

I gateway moderni possono validare le richieste in ingresso e le risposte in uscita direttamente contro la specifica OpenAPI:

#### Kong — OAS Validation Plugin

```yaml
# Kong — validazione OpenAPI nativa
plugins:
  - name: oas-validation
    service: orders-service
    config:
      api_spec: |
        openapi: "3.1.0"
        info:
          title: "Orders API"
          version: "2.0.0"
        paths:
          /orders:
            post:
              requestBody:
                required: true
                content:
                  application/json:
                    schema:
                      type: object
                      required: [items, shipping_address]
                      properties:
                        items:
                          type: array
                          minItems: 1
                          items:
                            type: object
                            required: [product_id, quantity]
                            properties:
                              product_id:
                                type: string
                                format: uuid
                              quantity:
                                type: integer
                                minimum: 1
                                maximum: 100
                        shipping_address:
                          $ref: "#/components/schemas/Address"
              responses:
                "201":
                  content:
                    application/json:
                      schema:
                        $ref: "#/components/schemas/OrderResponse"
      validate_request_body: true
      validate_request_header_params: true
      validate_request_query_params: true
      validate_request_uri_params: true
      validate_response_body: false  # Abilitare in staging, disabilitare in prod per performance
      verbose_response: false  # Non esporre dettagli di validazione in prod
      header_parameter_check: true
      query_parameter_check: true
      allowed_content_types:
        - application/json
```

#### APISIX — Request Validation

```bash
# APISIX — validazione schema JSON nella route
curl -X PUT http://127.0.0.1:9180/apisix/admin/routes/orders-create \
  -H "X-API-KEY: ${APISIX_ADMIN_KEY}" \
  -d '{
    "uri": "/api/v1/orders",
    "methods": ["POST"],
    "plugins": {
      "request-validation": {
        "body_schema": {
          "type": "object",
          "required": ["items", "shipping_address"],
          "properties": {
            "items": {
              "type": "array",
              "minItems": 1,
              "items": {
                "type": "object",
                "required": ["product_id", "quantity"],
                "properties": {
                  "product_id": { "type": "string", "pattern": "^[0-9a-f]{8}-" },
                  "quantity": { "type": "integer", "minimum": 1, "maximum": 100 }
                }
              }
            }
          }
        },
        "rejected_code": 422,
        "rejected_msg": "Validazione richiesta fallita"
      }
    },
    "upstream_id": 1
  }'
```

### 20.5 Contract Testing con Schemathesis

Il **contract testing** verifica automaticamente che l'implementazione del backend rispetti il contratto OpenAPI. **Schemathesis** è uno strumento property-based testing specifico per API:

```bash
# Installare Schemathesis
pip install schemathesis

# Test automatici contro l'API in staging
schemathesis run \
  --url https://staging-api.example.com/openapi.json \
  --hypothesis-max-examples=200 \
  --checks all \
  --validate-schema true \
  --workers 4 \
  --report \
  --cassette-path=schemathesis-cassette.yaml

# Test specifico per un singolo endpoint
schemathesis run \
  --url https://staging-api.example.com/openapi.json \
  --endpoint "/api/v1/orders" \
  --method POST \
  --hypothesis-max-examples=500 \
  --checks all
```

Schemathesis genera automaticamente input basati sugli schema OpenAPI e verifica:

| Check | Descrizione |
|-------|-------------|
| `status_code_conformance` | I codici di stato ritornati sono dichiarati nella specifica |
| `content_type_conformance` | I Content-Type delle risposte corrispondono alla specifica |
| `response_schema_conformance` | Il body della risposta è conforme allo schema JSON |
| `negative_data_rejection` | Input invalidi vengono rifiutati (non 500) |
| `response_headers_conformance` | Gli header obbligatori sono presenti nelle risposte |

### 20.6 Workflow CI/CD Specification-Driven

```yaml
# .github/workflows/api-governance.yml
name: API Governance

on:
  pull_request:
    paths:
      - 'api/openapi.yaml'
      - 'api/schemas/**'

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Lint OpenAPI
        run: |
          npm install -g @stoplight/spectral-cli
          spectral lint api/openapi.yaml --fail-severity error

  breaking-changes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Detect breaking changes
        run: |
          npm install -g @openapitools/openapi-diff
          # Confronto tra la specifica nel branch base e la PR
          git show origin/main:api/openapi.yaml > /tmp/base-spec.yaml
          openapi-diff /tmp/base-spec.yaml api/openapi.yaml \
            --fail-on-incompatible \
            --markdown report.md

  contract-test:
    needs: lint
    runs-on: ubuntu-latest
    services:
      api:
        image: ghcr.io/myorg/orders-api:${{ github.sha }}
        ports:
          - 8080:8080
    steps:
      - uses: actions/checkout@v4
      - name: Contract test
        run: |
          pip install schemathesis
          schemathesis run \
            --url http://localhost:8080/openapi.json \
            --checks all \
            --hypothesis-max-examples=100

  gateway-sync:
    needs: [lint, breaking-changes, contract-test]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Sync to Kong
        run: |
          # Convertire OpenAPI in Kong declarative config
          deck file openapi2kong \
            --spec api/openapi.yaml \
            --output-file kong.yaml
          # Applicare la configurazione
          deck gateway sync kong.yaml \
            --kong-addr ${{ secrets.KONG_ADMIN_URL }} \
            --headers "Kong-Admin-Token:${{ secrets.KONG_ADMIN_TOKEN }}"
```

### 20.7 Confronto Tool OpenAPI-First

| Tool | Funzione | Linguaggio | Integrazione Gateway |
|------|----------|-----------|---------------------|
| Spectral | Linting e governance | Node.js | CI/CD pre-deploy |
| Vacuum | Linting veloce (Go) | Go | CI/CD pre-deploy |
| Prism | Mock server da spec | Node.js | Sviluppo parallelo frontend |
| Microcks | Mock + contract test | Java | Kubernetes-native |
| Schemathesis | Property-based contract test | Python | CI/CD post-deploy |
| Dredd | Contract testing HTTP | Node.js | CI/CD post-deploy |
| openapi-diff | Breaking change detection | Node.js | CI/CD PR check |
| deck openapi2kong | Conversione spec → Kong config | Go | Deploy pipeline |
| Optic | API changelog e diff | Node.js | CI/CD PR review |

---

## Esercizi

1. **Kong rate limiting lab** — Deploya Kong in Docker Compose con PostgreSQL. Configura un Service e una Route, poi abilita il plugin `rate-limiting` a 10 request/minuto. Verifica con `curl` che il 429 venga ritornato al superamento della soglia e ispeziona gli header `X-RateLimit-Remaining`.

2. **OAuth2 + JWT validation** — Configura il plugin `jwt` di Kong per validare token JWT emessi da un IdP (ad esempio Keycloak o Auth0). Crea un consumer, associa una chiave pubblica RS256, e verifica che le richieste senza token o con token scaduto vengano rifiutate con 401.

3. **API versioning con canary** — Implementa due versioni di un backend (v1, v2) dietro Kong. Usa il plugin `canary-release` (o Ingress annotation `canary-weight`) per inviare il 10% del traffico alla v2. Monitora le metriche con Prometheus e Grafana per confrontare latenza e error rate tra le due versioni.

4. **GraphQL gateway depth limiting** — Deploya Apollo Router o Hasura davanti a due subgraph GraphQL. Configura persisted queries, depth limit a 5, e query complexity budget. Verifica che query con nesting eccessivo vengano rifiutate e che query non registrate (se APQ enforced) restituiscano errore.

5. **Multi-gateway disaster recovery** — Deploya due istanze Kong in region diverse (simulabili con due namespace Kubernetes). Configura un health check attivo e un DNS failover (simulabile con coredns custom). Esegui un backup `deck dump` della region primaria, simula un failure, e ripristina la configurazione nella region secondaria.

---

## Letture e Riferimenti

### Documentazione ufficiale

- Kong Gateway documentation. https://docs.konghq.com/gateway/latest/
- AWS API Gateway Developer Guide. https://docs.aws.amazon.com/apigateway/latest/developerguide/
- Apigee X documentation. https://cloud.google.com/apigee/docs
- Tyk API Gateway documentation. https://tyk.io/docs/
- Apollo Router documentation. https://www.apollographql.com/docs/router/

### Libri

- Biehl, M. *API Architecture: The Big Picture for Building APIs*. API-University Press, 2024.
- Richardson, C. *Microservices Patterns*. Manning, 2018. Cap. 8 — API Gateway pattern.
- Lauret, A. *The Design of Web APIs*. Manning, 2019.

---

## Riferimenti Incrociati

| Modulo | Titolo | Relazione |
|---|---|---|
| [09-service-mesh](09-service-mesh.md) | Service Mesh | Il service mesh gestisce comunicazione est-ovest; l'API gateway gestisce nord-sud |
| [10-load-balancer-reverse-proxy](10-load-balancer-reverse-proxy.md) | Load Balancer e Reverse Proxy | L'API gateway estende il reverse proxy con auth, rate limiting e transformation |
| [13-sicurezza-piattaforme](13-sicurezza-piattaforme.md) | Sicurezza delle Piattaforme | WAF e DDoS mitigation integrabili come layer davanti all'API gateway |
| [15-secrets-management](15-secrets-management.md) | Secrets Management | API key, JWT signing key e mTLS cert gestiti tramite Vault o secret manager |
| [08-monitoring-observability](08-monitoring-observability.md) | Monitoring e Observability | Tracing distribuito e metriche dell'API gateway esposte a Prometheus/Grafana |
| [07-ci-cd](07-ci-cd.md) | CI/CD | Deployment declarativo della configurazione gateway via GitOps (deck sync) |

---

## Glossario

| Termine | Definizione |
|---|---|
| **API Gateway** | Punto di ingresso centralizzato che gestisce routing, autenticazione, rate limiting e transformation per le API. |
| **Rate limiting** | Meccanismo che limita il numero di richieste per unita' di tempo per proteggere i backend da sovraccarico. |
| **JWT (JSON Web Token)** | Token firmato crittograficamente usato per trasportare claims di autenticazione e autorizzazione. |
| **mTLS (Mutual TLS)** | Autenticazione bidirezionale in cui sia client che server presentano certificati X.509. |
| **OAuth2** | Framework di autorizzazione delegata che emette access token per accesso a risorse protette. |
| **GraphQL** | Linguaggio di query per API che permette al client di specificare i campi desiderati nella risposta. |
| **Persisted queries** | Query GraphQL pre-registrate nel gateway, identificate tramite hash, per ridurre dimensione request e attack surface. |
| **Depth limiting** | Controllo che limita la profondita' massima di nesting delle query GraphQL per prevenire abuse. |
| **Canary release** | Strategia di deployment che invia una piccola percentuale di traffico alla nuova versione per validazione. |
| **Consumer** | Entita' (utente, applicazione, servizio) registrata nel gateway con credenziali e policy associate. |
| **Plugin** | Modulo estensibile che aggiunge funzionalita' all'API gateway (auth, logging, transformation, caching). |
| **Upstream** | Servizio backend a cui l'API gateway inoltra le richieste dopo routing e policy enforcement. |
| **Route** | Regola che mappa una richiesta in ingresso (path, host, header) a un upstream specifico. |
| **deck** | Tool CLI per gestire la configurazione di Kong in modo declarativo (dump, diff, sync). |
| **API key** | Stringa segreta usata come credenziale semplice per identificare il chiamante di un'API. |
