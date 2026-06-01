---
corso: "Gestione Piattaforme e DevOps"
fase: "4 — Osservabilità e Networking"
modulo: 10
titolo: "Load Balancer e Reverse Proxy"
versione: "HAProxy 3.x / Nginx 1.27 / Traefik 3.x / Envoy 1.31"
livello: "Intermedio"
prerequisiti: ["05-kubernetes", "01-cloud-aws", "13-sicurezza-piattaforme"]
obiettivi:
  - "Distinguere load balancing L4 (TCP/UDP) e L7 (HTTP) e scegliere in base al caso d'uso"
  - "Configurare HAProxy, Nginx e Traefik come reverse proxy con health check applicativi"
  - "Implementare TLS termination, session persistence e rate limiting"
  - "Progettare architetture multi-tier con cloud load balancer (ALB, NLB, GCP LB)"
  - "Pianificare disaster recovery e scalabilità orizzontale per il layer di bilanciamento"
tag: [load-balancer, reverse-proxy, haproxy, nginx, traefik, tls-termination, health-check, l4-l7]
---

# Load Balancer e Reverse Proxy — Documentazione Completa

> **Modulo 10** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Distinguere load balancing L4 (TCP/UDP) e L7 (HTTP) e scegliere in base al caso d'uso
> 2. Configurare HAProxy, Nginx e Traefik come reverse proxy con health check applicativi
> 3. Implementare TLS termination, session persistence e rate limiting
> 4. Progettare architetture multi-tier con cloud load balancer (ALB, NLB, GCP LB)
> 5. Pianificare disaster recovery e scalabilità orizzontale per il layer di bilanciamento
>
> **Prerequisiti:** [Kubernetes](05-kubernetes.md) · [Cloud AWS](01-cloud-aws.md) · [Sicurezza Piattaforme](13-sicurezza-piattaforme.md)
> **Tempo stimato:** 6-8 ore · **Livello:** Intermedio

## Idee guida

1. **L4 (TCP) vs L7 (HTTP) load balancer: capacity differente.** L7 piu intelligente, costoso.
2. **HAProxy + Nginx + Traefik: triadi top.** AWS ALB/NLB, GCP LB native.
3. **Health check: must include applicative, not just TCP.**
4. **Sticky sessions evitate per scalabilita.** State esterno (Redis).


## Indice

1. [Panoramica e Concetti Fondamentali](#1-panoramica-e-concetti-fondamentali)
2. [HAProxy](#2-haproxy)
3. [Nginx come Load Balancer e Reverse Proxy](#3-nginx-come-load-balancer-e-reverse-proxy)
4. [Traefik](#4-traefik)
5. [Cloud Load Balancers — AWS](#5-cloud-load-balancers--aws)
6. [Cloud Load Balancers — Azure e GCP](#6-cloud-load-balancers--azure-e-gcp)
7. [SSL/TLS e Certificati](#7-ssltls-e-certificati)
8. [Pattern Architetturali](#8-pattern-architetturali)
9. [Performance e Tuning](#9-performance-e-tuning)
10. [Monitoring e Troubleshooting](#10-monitoring-e-troubleshooting)
11. [Best Practices](#11-best-practices)
12. [Envoy Proxy — Deep-Dive](#12-envoy-proxy--deep-dive)
13. [Confronto Avanzato degli Algoritmi di Bilanciamento](#13-confronto-avanzato-degli-algoritmi-di-bilanciamento)
14. [WebSocket, HTTP/2 e gRPC Load Balancing](#14-websocket-http2-e-grpc-load-balancing)
15. [Global Server Load Balancing (GSLB)](#15-global-server-load-balancing-gslb)
16. [Pattern di Alta Disponibilita Avanzati](#16-pattern-di-alta-disponibilita-avanzati)
17. [Monitoring Avanzato dei Load Balancer](#17-monitoring-avanzato-dei-load-balancer)

---

## 1. Panoramica e Concetti Fondamentali

### Differenza tra Load Balancer e Reverse Proxy

Un **reverse proxy** e un **load balancer** sono componenti distinti che spesso vengono sovrapposti perche la maggior parte delle implementazioni moderne svolge entrambe le funzioni. Un reverse proxy si posiziona davanti a uno o piu server backend e inoltra le richieste dei client, nascondendo l'infrastruttura reale. Il client non comunica mai direttamente con il backend. Un load balancer, invece, ha come scopo principale la distribuzione del traffico su piu istanze di un servizio per garantire scalabilita e disponibilita.

Un reverse proxy puo operare con un singolo backend e fornire comunque valore aggiunto tramite caching, compressione, SSL termination e protezione dell'infrastruttura. Un load balancer presuppone per definizione la presenza di piu backend e si concentra sulla distribuzione ottimale del carico.

### Layer 4 (TCP/UDP) vs Layer 7 (HTTP/HTTPS)

Il bilanciamento a **Layer 4** opera a livello di trasporto. Le decisioni di routing sono basate su indirizzo IP sorgente, IP destinazione, porta sorgente e porta destinazione. Il load balancer non ispeziona il contenuto del pacchetto: si limita a instradare le connessioni TCP o i datagrammi UDP verso i backend. Questo lo rende estremamente performante perche non deve effettuare parsing del protocollo applicativo, ma lo priva della capacita di prendere decisioni basate sul contenuto della richiesta.

Il bilanciamento a **Layer 7** opera a livello applicativo. Il load balancer comprende il protocollo HTTP/HTTPS e puo prendere decisioni basate su URL path, hostname (virtual hosting), header HTTP, cookie, metodo HTTP e persino il body della richiesta. Questo consente routing sofisticato (ad esempio, inviare tutte le richieste `/api/v2/*` a un cluster specifico) ma introduce una latenza aggiuntiva dovuta al parsing del protocollo.

| Caratteristica          | Layer 4               | Layer 7                     |
|-------------------------|-----------------------|-----------------------------|
| Protocolli              | TCP, UDP              | HTTP, HTTPS, gRPC, WebSocket |
| Decisioni di routing    | IP, porta             | URL, header, cookie, host   |
| Performance             | Molto alta            | Alta (overhead di parsing)  |
| SSL inspection          | No (passthrough)      | Si (termination/re-encrypt) |
| Session persistence     | IP hash               | Cookie-based                |
| Content-based routing   | No                    | Si                          |
| Caching                 | No                    | Si                          |

### Algoritmi di Bilanciamento

**Round-Robin**: le richieste vengono distribuite in sequenza circolare tra i backend. E l'algoritmo piu semplice, adatto quando i server hanno capacita omogenea e le richieste hanno costo computazionale uniforme. Non considera il carico effettivo dei server.

**Weighted Round-Robin**: variante del round-robin che assegna un peso a ciascun backend. Un server con peso 3 riceve tre volte il traffico di un server con peso 1. Utile quando i backend hanno capacita hardware differenti.

**Least Connections**: la richiesta viene inviata al backend con il minor numero di connessioni attive. Adatto quando le richieste hanno durata variabile. Nella variante weighted, il numero di connessioni viene diviso per il peso del server.

**IP Hash**: l'indirizzo IP del client viene usato come input per una funzione hash che determina il backend. Garantisce che lo stesso client venga sempre diretto allo stesso server (utile per session persistence senza cookie), ma puo causare distribuzione non uniforme se un numero limitato di IP genera la maggior parte del traffico.

**Consistent Hashing**: variante avanzata dell'IP hash che minimizza la redistribuzione delle connessioni quando un backend viene aggiunto o rimosso. Ogni backend viene mappato su un anello hash virtuale, e le richieste vengono assegnate al backend piu vicino sull'anello. Quando un nodo cade, solo le sue richieste vengono redistribuite, non tutte.

**Random**: selezione casuale del backend. Sorprendentemente efficace con un numero elevato di backend grazie alla legge dei grandi numeri. La variante **Random Two Choices** seleziona casualmente due backend e sceglie quello con meno connessioni.

### Health Checks

Gli **health check attivi** prevedono che il load balancer invii periodicamente probe ai backend per verificarne lo stato. Possono essere:
- **TCP check**: verifica che la porta sia aperta e accetti connessioni
- **HTTP check**: invia una richiesta GET/HEAD a un endpoint specifico (es. `/healthz`) e verifica il codice di risposta
- **Custom script**: esegue uno script arbitrario per verificare lo stato del servizio

Gli **health check passivi** monitorano il traffico di produzione reale. Se un backend restituisce un numero configurato di errori (5xx, timeout, connection refused) entro una finestra temporale, viene marcato come unhealthy. Non generano traffico aggiuntivo ma reagiscono piu lentamente alla degradazione.

La combinazione di entrambi i metodi e la prassi raccomandata: gli health check attivi individuano rapidamente i server completamente down, mentre quelli passivi catturano degradazioni parziali non rilevabili da una semplice probe.

### Session Persistence (Sticky Sessions)

La session persistence garantisce che le richieste successive di uno stesso client vengano instradate allo stesso backend. I metodi principali sono:

- **Cookie-based**: il load balancer inietta un cookie (es. `SERVERID=backend1`) nella risposta. Le richieste successive del client includono questo cookie, e il load balancer le dirige al backend corrispondente.
- **Source IP affinity**: tutte le richieste provenienti dallo stesso IP vengono inviate allo stesso backend. Problematico con NAT e proxy condivisi.
- **Application-controlled**: l'applicazione stessa gestisce la sessione in un datastore condiviso (Redis, database), eliminando la necessita di sticky sessions a livello di load balancer. Questo e l'approccio preferito nelle architetture moderne.

### SSL/TLS Termination, Passthrough e Re-encryption

**SSL Termination**: il load balancer decifra il traffico TLS e lo inoltra in chiaro ai backend. Il certificato risiede sul load balancer. Vantaggi: centralizzazione della gestione certificati, possibilita di ispezione del traffico a Layer 7, riduzione del carico computazionale sui backend. Svantaggio: il tratto load balancer-backend non e cifrato.

**SSL Passthrough**: il load balancer inoltra il traffico TLS cifrato direttamente al backend senza decifrarlo. Il certificato risiede sui backend. Il load balancer opera a Layer 4 e non puo ispezionare il contenuto. Vantaggi: sicurezza end-to-end. Svantaggio: impossibilita di routing basato su contenuto HTTP.

**SSL Re-encryption (SSL Bridging)**: il load balancer decifra il traffico TLS dal client, lo ispeziona e lo re-cifra prima di inviarlo al backend su una nuova connessione TLS. Massima flessibilita e sicurezza, ma doppio overhead crittografico.

### High Availability del Load Balancer

Il load balancer stesso rappresenta un single point of failure se non viene deployato in alta disponibilita. Le strategie principali sono:

- **Active-Passive con VRRP**: due load balancer condividono un Virtual IP (VIP). Il nodo attivo gestisce tutto il traffico. Se cade, il nodo passivo prende il VIP tramite il protocollo VRRP (es. Keepalived). Failover tipico in 1-3 secondi.
- **Active-Active**: entrambi i nodi gestiscono traffico contemporaneamente, bilanciati da DNS round-robin o da un livello superiore (ECMP). Massimizza l'utilizzo delle risorse ma e piu complesso da gestire.
- **Anycast**: lo stesso IP viene annunciato da piu punti di presenza (PoP) geograficamente distribuiti. Il routing BGP dirige il client al PoP piu vicino. Usato dai CDN e dai load balancer globali dei cloud provider.

---

## 2. HAProxy

### Architettura e Componenti

HAProxy (High Availability Proxy) e un load balancer e proxy server ad alte prestazioni, single-process e event-driven. Utilizza un modello di I/O non-bloccante basato su epoll (Linux) o kqueue (BSD), capace di gestire centinaia di migliaia di connessioni concorrenti con un consumo di memoria minimo.

L'architettura si compone di:
- **Frontend**: definisce come le connessioni in ingresso vengono accettate (bind address, porta, protocollo, SSL)
- **Backend**: definisce il pool di server verso cui le richieste vengono inoltrate, con algoritmo di bilanciamento e health check
- **Listen**: combina frontend e backend in una singola sezione
- **ACL (Access Control List)**: regole per il routing condizionale basato su attributi della richiesta
- **Stick Tables**: tabelle in memoria per tracking di sessioni, rate limiting e conteggi

### Installazione

```bash
# Debian/Ubuntu - versione dal repository ufficiale
sudo apt update && sudo apt install -y haproxy

# Compilazione da sorgente con supporto OpenSSL e Lua
wget https://www.haproxy.org/download/2.9/src/haproxy-2.9.7.tar.gz
tar xzf haproxy-2.9.7.tar.gz
cd haproxy-2.9.7
make -j$(nproc) TARGET=linux-glibc USE_OPENSSL=1 USE_LUA=1 USE_PCRE2=1 USE_SYSTEMD=1
sudo make install

# Verifica versione e build options
haproxy -vv

# Validazione configurazione
haproxy -c -f /etc/haproxy/haproxy.cfg

# Reload senza downtime (graceful reload)
sudo systemctl reload haproxy
```

### Configurazione Completa haproxy.cfg

```
#---------------------------------------------------------------------
# Global settings
#---------------------------------------------------------------------
global
    log         /dev/log local0 info
    log         /dev/log local1 notice
    chroot      /var/lib/haproxy
    pidfile     /var/run/haproxy.pid
    maxconn     50000
    user        haproxy
    group       haproxy
    daemon

    # SSL/TLS settings
    ssl-default-bind-ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384
    ssl-default-bind-ciphersuites TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256
    ssl-default-bind-options prefer-client-ciphers no-sslv3 no-tlsv10 no-tlsv11
    ssl-default-server-ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256
    ssl-default-server-options no-sslv3 no-tlsv10 no-tlsv11

    # Stats socket per runtime API
    stats socket /var/run/haproxy/admin.sock mode 660 level admin expose-fd listeners
    stats timeout 30s

    # Tuning
    tune.ssl.default-dh-param 2048
    tune.bufsize 32768
    tune.maxrewrite 1024

#---------------------------------------------------------------------
# Defaults
#---------------------------------------------------------------------
defaults
    log     global
    mode    http
    option  httplog
    option  dontlognull
    option  forwardfor except 127.0.0.0/8
    option  redispatch
    retries 3
    timeout connect     5s
    timeout client      30s
    timeout server      30s
    timeout http-request 10s
    timeout http-keep-alive 10s
    timeout queue       30s
    timeout check       5s
    errorfile 400 /etc/haproxy/errors/400.http
    errorfile 403 /etc/haproxy/errors/403.http
    errorfile 408 /etc/haproxy/errors/408.http
    errorfile 500 /etc/haproxy/errors/500.http
    errorfile 502 /etc/haproxy/errors/502.http
    errorfile 503 /etc/haproxy/errors/503.http
    errorfile 504 /etc/haproxy/errors/504.http

#---------------------------------------------------------------------
# Statistics Page
#---------------------------------------------------------------------
listen stats
    bind *:8404
    mode http
    stats enable
    stats uri /stats
    stats refresh 10s
    stats show-legends
    stats show-node
    stats auth admin:SecureP4ssw0rd!
    stats admin if TRUE

#---------------------------------------------------------------------
# Frontend HTTP - Redirect a HTTPS
#---------------------------------------------------------------------
frontend http-in
    bind *:80
    mode http

    # Redirect tutto il traffico HTTP a HTTPS
    http-request redirect scheme https unless { ssl_fc }

#---------------------------------------------------------------------
# Frontend HTTPS
#---------------------------------------------------------------------
frontend https-in
    bind *:443 ssl crt /etc/haproxy/certs/combined.pem alpn h2,http/1.1
    mode http

    # Security headers
    http-response set-header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
    http-response set-header X-Content-Type-Options nosniff
    http-response set-header X-Frame-Options DENY
    http-response set-header Referrer-Policy strict-origin-when-cross-origin

    # Logging del client IP reale
    option forwardfor

    # ACL per routing basato su hostname
    acl host_api      hdr(host) -i api.example.com
    acl host_web      hdr(host) -i www.example.com
    acl host_admin    hdr(host) -i admin.example.com

    # ACL per routing basato su path
    acl path_api_v1   path_beg /api/v1
    acl path_api_v2   path_beg /api/v2
    acl path_static   path_beg /static /assets /images
    acl path_ws       path_beg /ws

    # ACL per rate limiting
    acl too_many_requests sc_http_req_rate(0) gt 100

    # Stick table per rate limiting
    stick-table type ip size 100k expire 30s store http_req_rate(10s)
    http-request track-sc0 src
    http-request deny deny_status 429 if too_many_requests

    # Routing condizionale
    use_backend backend_api_v1    if host_api path_api_v1
    use_backend backend_api_v2    if host_api path_api_v2
    use_backend backend_static    if path_static
    use_backend backend_websocket if path_ws
    use_backend backend_admin     if host_admin
    default_backend backend_web

#---------------------------------------------------------------------
# Backend API v1
#---------------------------------------------------------------------
backend backend_api_v1
    mode http
    balance leastconn
    option httpchk GET /healthz HTTP/1.1\r\nHost:\ api.example.com
    http-check expect status 200

    # Retry su errore
    retry-on conn-failure empty-response response-timeout 503

    # Compressione
    compression algo gzip
    compression type text/html text/plain application/json

    server api-v1-1 10.0.1.10:8080 check inter 3s fall 3 rise 2 maxconn 500 weight 100
    server api-v1-2 10.0.1.11:8080 check inter 3s fall 3 rise 2 maxconn 500 weight 100
    server api-v1-3 10.0.1.12:8080 check inter 3s fall 3 rise 2 maxconn 500 weight 50

#---------------------------------------------------------------------
# Backend API v2
#---------------------------------------------------------------------
backend backend_api_v2
    mode http
    balance roundrobin
    option httpchk GET /health
    http-check expect status 200

    cookie SERVERID insert indirect nocache
    server api-v2-1 10.0.2.10:8080 check cookie s1
    server api-v2-2 10.0.2.11:8080 check cookie s2

#---------------------------------------------------------------------
# Backend Web
#---------------------------------------------------------------------
backend backend_web
    mode http
    balance roundrobin
    option httpchk HEAD / HTTP/1.1\r\nHost:\ www.example.com

    server web-1 10.0.3.10:8080 check inter 5s fall 3 rise 2
    server web-2 10.0.3.11:8080 check inter 5s fall 3 rise 2
    server web-3 10.0.3.12:8080 check inter 5s fall 3 rise 2 backup

#---------------------------------------------------------------------
# Backend Static Assets
#---------------------------------------------------------------------
backend backend_static
    mode http
    balance roundrobin
    timeout server 10s

    server static-1 10.0.4.10:80 check
    server static-2 10.0.4.11:80 check

#---------------------------------------------------------------------
# Backend WebSocket
#---------------------------------------------------------------------
backend backend_websocket
    mode http
    balance source
    option httpchk GET /ws/health
    timeout tunnel 3600s

    server ws-1 10.0.5.10:8080 check
    server ws-2 10.0.5.11:8080 check

#---------------------------------------------------------------------
# Backend Admin
#---------------------------------------------------------------------
backend backend_admin
    mode http
    balance roundrobin

    # Restrizione IP per admin
    acl allowed_networks src 10.0.0.0/8 192.168.0.0/16
    http-request deny unless allowed_networks

    server admin-1 10.0.6.10:8080 check
```

### HAProxy Runtime API

La runtime API consente di gestire HAProxy senza ricaricare la configurazione:

```bash
# Stato dei server
echo "show servers state" | socat stdio /var/run/haproxy/admin.sock

# Disabilitare un server (drain mode)
echo "set server backend_api_v1/api-v1-1 state drain" | socat stdio /var/run/haproxy/admin.sock

# Mettere un server in manutenzione
echo "set server backend_api_v1/api-v1-1 state maint" | socat stdio /var/run/haproxy/admin.sock

# Riabilitare un server
echo "set server backend_api_v1/api-v1-1 state ready" | socat stdio /var/run/haproxy/admin.sock

# Modificare il peso di un server a runtime
echo "set server backend_api_v1/api-v1-1 weight 50" | socat stdio /var/run/haproxy/admin.sock

# Statistiche in formato CSV
echo "show stat" | socat stdio /var/run/haproxy/admin.sock

# Informazioni sulle sessioni correnti
echo "show sess" | socat stdio /var/run/haproxy/admin.sock

# Mostrare la stick table
echo "show table backend_api_v1" | socat stdio /var/run/haproxy/admin.sock
```

### HAProxy con Docker

```yaml
# docker-compose.yml
version: "3.8"
services:
  haproxy:
    image: haproxy:2.9-alpine
    container_name: haproxy
    ports:
      - "80:80"
      - "443:443"
      - "8404:8404"
    volumes:
      - ./haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro
      - ./certs:/etc/haproxy/certs:ro
      - ./errors:/etc/haproxy/errors:ro
    restart: unless-stopped
    sysctls:
      - net.ipv4.ip_unprivileged_port_start=0
    networks:
      - proxy-network

networks:
  proxy-network:
    driver: bridge
```

### ACL Avanzate e Logica Multi-Criterio

Le ACL in HAProxy possono essere combinate con operatori logici per costruire regole di routing complesse. Ogni ACL e una condizione booleana valutata su attributi della richiesta, della connessione o delle stick table.

**Operatori logici tra ACL**:
- `if acl1 acl2` — AND implicito (entrambe devono essere vere)
- `if acl1 || acl2` — OR (almeno una deve essere vera)
- `if !acl1` — NOT (negazione)
- `if { condition }` — ACL inline anonima (senza dare un nome)

**ACL multi-criterio per routing sofisticato**:

```
frontend https-in
    bind *:443 ssl crt /etc/haproxy/certs/ strict-sni

    # ACL basate su SNI (prima del TLS handshake completo)
    acl is_api     ssl_fc_sni -i api.example.com
    acl is_admin   ssl_fc_sni -i admin.example.com

    # ACL basate su header e path
    acl is_mobile       hdr(User-Agent) -i -m sub Mobile Android iPhone
    acl is_api_v2       path_beg /api/v2
    acl is_graphql      path_beg /graphql
    acl is_internal_ip  src 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16
    acl is_post_method  method POST
    acl has_auth_header hdr(Authorization) -m found
    acl is_json         hdr(Content-Type) -i -m sub application/json

    # ACL con map file (lookup dinamico)
    acl is_blocked_country hdr_ip(X-Forwarded-For) -f /etc/haproxy/maps/blocked-countries.lst
    acl is_premium_user    hdr(X-User-Tier) -i premium enterprise

    # Routing condizionale combinato
    use_backend backend_mobile_api  if is_api is_mobile is_api_v2
    use_backend backend_graphql     if is_graphql is_post_method has_auth_header
    use_backend backend_admin       if is_admin is_internal_ip
    http-request deny deny_status 403 if is_admin !is_internal_ip
    use_backend backend_premium     if is_api is_premium_user
    default_backend backend_web
```

**Map file per routing dinamico**: i map file consentono di associare valori di input a valori di output senza scrivere centinaia di ACL. Sono caricati in memoria e aggiornabili a runtime tramite la Runtime API.

```
# /etc/haproxy/maps/domain-backend.map
api.example.com       backend_api
www.example.com       backend_web
admin.example.com     backend_admin
cdn.example.com       backend_static
ws.example.com        backend_websocket

# Uso nel frontend
frontend https-in
    bind *:443 ssl crt /etc/haproxy/certs/
    use_backend %[req.hdr(host),lower,map_dom(/etc/haproxy/maps/domain-backend.map,backend_default)]

# Aggiornamento a runtime senza reload
echo "add map /etc/haproxy/maps/domain-backend.map staging.example.com backend_staging" | \
  socat stdio /var/run/haproxy/admin.sock

echo "del map /etc/haproxy/maps/domain-backend.map staging.example.com" | \
  socat stdio /var/run/haproxy/admin.sock

echo "show map /etc/haproxy/maps/domain-backend.map" | \
  socat stdio /var/run/haproxy/admin.sock
```

### Stick Table Avanzate e Peer Replication

Le stick table vanno oltre il semplice rate limiting. Fungono da database in-memory ad alte prestazioni per tracking di sessioni, conteggi, rate e pattern di accesso. HAProxy supporta la replica delle stick table tra peer per garantire consistenza in scenari multi-nodo.

**Tipi di dati nelle stick table**:

| Contatore | Descrizione |
|-----------|-------------|
| `conn_cnt` | Numero totale di connessioni |
| `conn_cur` | Connessioni correnti |
| `conn_rate(period)` | Tasso connessioni nel periodo |
| `http_req_cnt` | Totale richieste HTTP |
| `http_req_rate(period)` | Tasso richieste HTTP nel periodo |
| `http_err_cnt` | Totale errori HTTP |
| `http_err_rate(period)` | Tasso errori HTTP nel periodo |
| `bytes_in_cnt` | Byte ricevuti totali |
| `bytes_out_cnt` | Byte inviati totali |
| `gpc0` | General purpose counter 0 |
| `gpc0_rate(period)` | Tasso del contatore gpc0 |

**Stick table con tracking multi-livello**:

```
frontend https-in
    bind *:443 ssl crt /etc/haproxy/certs/combined.pem

    # Stick table per rate limiting per IP (layer connection)
    stick-table type ip size 200k expire 2m store conn_cur,conn_rate(10s),http_req_rate(10s),http_err_rate(10s),bytes_out_cnt

    # Tracking dell'IP sorgente
    http-request track-sc0 src

    # Protezione multi-livello
    # 1. Tropppe connessioni simultanee dallo stesso IP
    acl abuse_conn_cur     sc0_conn_cur gt 100
    # 2. Tasso connessioni troppo alto
    acl abuse_conn_rate    sc0_conn_rate gt 50
    # 3. Tasso richieste HTTP troppo alto
    acl abuse_req_rate     sc0_http_req_rate gt 200
    # 4. Tasso errori troppo alto (possibile scanning)
    acl abuse_err_rate     sc0_http_err_rate gt 50
    # 5. Scaricamento massivo di dati
    acl abuse_bandwidth    sc0_bytes_out_cnt gt 104857600

    # Azioni graduali: prima tarpit, poi deny
    http-request tarpit if abuse_req_rate !abuse_conn_cur
    http-request deny deny_status 429 if abuse_conn_cur || abuse_conn_rate
    http-request deny deny_status 403 if abuse_err_rate
    tcp-request connection reject if abuse_bandwidth

    # Stick table separata per sessioni utente (tracking per cookie)
    stick-table type string len 64 size 100k expire 30m store http_req_cnt,http_req_rate(1m) peers mycluster
```

**Peer replication tra nodi HAProxy**: la replica delle stick table garantisce che i contatori di rate limiting e le informazioni di sessione siano condivise tra tutti i nodi di un cluster HAProxy. Se un client viene rate-limited su un nodo, la stessa limitazione si applica anche sugli altri nodi.

```
# Sezione peers nella configurazione HAProxy
peers mycluster
    peer haproxy-node-1 192.168.1.10:1024
    peer haproxy-node-2 192.168.1.11:1024
    peer haproxy-node-3 192.168.1.12:1024

# Riferimento nella stick table
backend backend_api
    stick-table type ip size 200k expire 2m store http_req_rate(10s) peers mycluster
    stick on src

# Comandi per verificare lo stato della replica
echo "show peers" | socat stdio /var/run/haproxy/admin.sock
echo "show table backend_api" | socat stdio /var/run/haproxy/admin.sock
```

### HAProxy Data Plane API

La Data Plane API e un'interfaccia REST che estende la Runtime API fornendo la capacita di gestire l'intera configurazione di HAProxy in modo programmatico. A differenza della Runtime API (socket UNIX, comandi testuali), la Data Plane API espone endpoint RESTful con schema OpenAPI, ideale per l'integrazione con sistemi di orchestrazione e CI/CD.

```bash
# Installazione dell'HAProxy Data Plane API
wget https://github.com/haproxytech/dataplaneapi/releases/download/v3.0.0/dataplaneapi_3.0.0_linux_amd64.tar.gz
tar xzf dataplaneapi_3.0.0_linux_amd64.tar.gz

# Configurazione in haproxy.cfg
# program api
#   command /usr/local/bin/dataplaneapi --host 0.0.0.0 --port 5555 \
#     --haproxy-bin /usr/sbin/haproxy \
#     --config-file /etc/haproxy/haproxy.cfg \
#     --reload-cmd "systemctl reload haproxy" \
#     --userlist controller

# Aggiungere un server al backend via API REST
curl -X POST "http://localhost:5555/v3/services/haproxy/configuration/servers?backend=backend_api&version=1" \
  -H "Content-Type: application/json" \
  -u admin:password \
  -d '{
    "name": "api-new-3",
    "address": "10.0.1.13",
    "port": 8080,
    "check": "enabled",
    "weight": 100
  }'

# Ottenere la configurazione corrente di un backend
curl -s "http://localhost:5555/v3/services/haproxy/configuration/backends/backend_api" \
  -u admin:password | python3 -m json.tool

# Modificare il peso di un server
curl -X PUT "http://localhost:5555/v3/services/haproxy/configuration/servers/api-v1-1?backend=backend_api&version=2" \
  -H "Content-Type: application/json" \
  -u admin:password \
  -d '{"name": "api-v1-1", "address": "10.0.1.10", "port": 8080, "weight": 50}'

# Creare una nuova ACL a runtime
curl -X POST "http://localhost:5555/v3/services/haproxy/configuration/acls?parent_type=frontend&parent_name=https-in&version=3" \
  -H "Content-Type: application/json" \
  -u admin:password \
  -d '{"acl_name": "is_maintenance", "criterion": "hdr(X-Maintenance)", "value": "-i true"}'

# Elencare le transazioni pendenti
curl -s "http://localhost:5555/v3/services/haproxy/transactions" -u admin:password
```

### Scripting Lua in HAProxy

HAProxy supporta nativamente l'esecuzione di script Lua per logiche di routing personalizzate, trasformazioni di richieste e integrazioni con servizi esterni. Gli script Lua possono essere invocati in diversi punti del ciclo di vita della richiesta.

```lua
-- /etc/haproxy/lua/custom-auth.lua
-- Verifica JWT semplificata con lookup su servizio esterno

core.register_action("check_jwt", { "http-req" }, function(txn)
    local auth_header = txn.http:req_get_headers()["authorization"]
    if auth_header == nil then
        txn:set_var("txn.auth_status", "missing")
        return
    end

    local token = string.match(auth_header[0], "Bearer%s+(.+)")
    if token == nil then
        txn:set_var("txn.auth_status", "invalid_format")
        return
    end

    -- Validazione tramite servizio esterno
    local http = core.httpclient()
    local res = http:post{
        url = "http://127.0.0.1:8081/validate",
        headers = {
            ["content-type"] = { "application/json" },
            ["x-token"]      = { token }
        },
        timeout = 2000
    }

    if res and res.status == 200 then
        txn:set_var("txn.auth_status", "valid")
    else
        txn:set_var("txn.auth_status", "rejected")
    end
end)

-- Registrare un fetcher personalizzato
core.register_fetches("geo_region", function(txn)
    local ip = txn.f:src()
    -- Lookup IP in tabella regioni (esempio semplificato)
    local regions = {
        ["10.0.1.0/24"] = "eu-west",
        ["10.0.2.0/24"] = "us-east",
    }
    for cidr, region in pairs(regions) do
        -- in produzione usare una libreria IP/CIDR
        return region
    end
    return "default"
end)
```

```
# haproxy.cfg - Riferimento allo script Lua
global
    lua-load /etc/haproxy/lua/custom-auth.lua

frontend https-in
    # Invocare l'action Lua
    http-request lua.check_jwt
    # Decisioni basate sul risultato
    http-request deny deny_status 401 if { var(txn.auth_status) -m str missing }
    http-request deny deny_status 401 if { var(txn.auth_status) -m str invalid_format }
    http-request deny deny_status 403 if { var(txn.auth_status) -m str rejected }
```

---

## 3. Nginx come Load Balancer e Reverse Proxy

### Nginx OSS vs Nginx Plus

**Nginx OSS** (Open Source) fornisce funzionalita complete di reverse proxy e load balancing. Supporta bilanciamento round-robin, least connections, IP hash e generic hash. Gli health check sono esclusivamente passivi: Nginx rileva i backend falliti solo quando una richiesta reale fallisce.

**Nginx Plus** (commerciale) aggiunge health check attivi, session persistence avanzata (sticky cookie, sticky route, sticky learn), dynamic reconfiguration via API, live activity monitoring dashboard, DNS service discovery, caching avanzato e supporto per JWT authentication nativo. Il costo si aggira intorno a 2500 USD/anno per istanza.

### Configurazione Completa come Load Balancer

```nginx
# /etc/nginx/nginx.conf

user nginx;
worker_processes auto;
worker_rlimit_nofile 65535;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 16384;
    multi_accept on;
    use epoll;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    # Logging format con metriche utili
    log_format main '$remote_addr - $remote_user [$time_local] '
                    '"$request" $status $body_bytes_sent '
                    '"$http_referer" "$http_user_agent" '
                    'rt=$request_time uct=$upstream_connect_time '
                    'uht=$upstream_header_time urt=$upstream_response_time '
                    'us=$upstream_status';

    access_log /var/log/nginx/access.log main buffer=32k flush=5s;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 1000;
    reset_timedout_connection on;

    # Buffer sizes
    client_body_buffer_size 16k;
    client_header_buffer_size 1k;
    client_max_body_size 50m;
    large_client_header_buffers 4 8k;

    # Compressione
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 4;
    gzip_min_length 256;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml
        application/xml+rss
        application/x-font-ttf
        font/opentype
        image/svg+xml;

    # Rate Limiting zones
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=30r/s;
    limit_req_zone $binary_remote_addr zone=login_limit:10m rate=5r/m;
    limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

    # ---------- Upstream Definitions ----------

    upstream api_backend {
        least_conn;
        keepalive 32;

        server 10.0.1.10:8080 weight=5 max_fails=3 fail_timeout=30s;
        server 10.0.1.11:8080 weight=5 max_fails=3 fail_timeout=30s;
        server 10.0.1.12:8080 weight=3 max_fails=3 fail_timeout=30s;
        server 10.0.1.13:8080 backup;
    }

    upstream web_backend {
        # Round-robin implicito (default)
        server 10.0.2.10:8080 max_fails=2 fail_timeout=15s;
        server 10.0.2.11:8080 max_fails=2 fail_timeout=15s;
        server 10.0.2.12:8080 max_fails=2 fail_timeout=15s;
    }

    upstream websocket_backend {
        ip_hash;
        server 10.0.3.10:8080;
        server 10.0.3.11:8080;
    }

    upstream grpc_backend {
        least_conn;
        server 10.0.4.10:50051;
        server 10.0.4.11:50051;
    }

    # ---------- Proxy Cache ----------

    proxy_cache_path /var/cache/nginx/static
                     levels=1:2
                     keys_zone=static_cache:10m
                     max_size=1g
                     inactive=60m
                     use_temp_path=off;

    proxy_cache_path /var/cache/nginx/api
                     levels=1:2
                     keys_zone=api_cache:5m
                     max_size=500m
                     inactive=10m
                     use_temp_path=off;

    # ---------- SSL Settings ----------

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;

    # ---------- HTTP -> HTTPS Redirect ----------

    server {
        listen 80 default_server;
        listen [::]:80 default_server;
        server_name _;

        # ACME challenge per Let's Encrypt
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

        location / {
            return 301 https://$host$request_uri;
        }
    }

    # ---------- API Server ----------

    server {
        listen 443 ssl http2;
        listen [::]:443 ssl http2;
        server_name api.example.com;

        ssl_certificate     /etc/nginx/certs/api.example.com/fullchain.pem;
        ssl_certificate_key /etc/nginx/certs/api.example.com/privkey.pem;

        # Security headers
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
        add_header X-Content-Type-Options nosniff always;
        add_header X-Frame-Options DENY always;
        add_header Referrer-Policy strict-origin-when-cross-origin always;

        # API v1
        location /api/v1/ {
            limit_req zone=api_limit burst=50 nodelay;
            limit_conn conn_limit 30;

            proxy_pass http://api_backend;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Request-ID $request_id;

            proxy_connect_timeout 5s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;

            proxy_next_upstream error timeout http_502 http_503 http_504;
            proxy_next_upstream_tries 2;
            proxy_next_upstream_timeout 10s;
        }

        # Rate-limited login endpoint
        location /api/v1/auth/login {
            limit_req zone=login_limit burst=3 nodelay;

            proxy_pass http://api_backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Cached GET responses
        location /api/v1/public/ {
            proxy_cache api_cache;
            proxy_cache_valid 200 5m;
            proxy_cache_valid 404 1m;
            proxy_cache_use_stale error timeout updating http_500 http_502 http_503;
            proxy_cache_lock on;
            add_header X-Cache-Status $upstream_cache_status;

            proxy_pass http://api_backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }

    # ---------- Web Application Server ----------

    server {
        listen 443 ssl http2;
        server_name www.example.com;

        ssl_certificate     /etc/nginx/certs/www.example.com/fullchain.pem;
        ssl_certificate_key /etc/nginx/certs/www.example.com/privkey.pem;

        # Static assets con caching aggressivo
        location /static/ {
            proxy_cache static_cache;
            proxy_cache_valid 200 7d;
            proxy_cache_use_stale error timeout updating;
            add_header X-Cache-Status $upstream_cache_status;
            expires 7d;
            add_header Cache-Control "public, immutable";

            proxy_pass http://web_backend;
        }

        # WebSocket proxying
        location /ws/ {
            proxy_pass http://websocket_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_read_timeout 3600s;
            proxy_send_timeout 3600s;
        }

        location / {
            proxy_pass http://web_backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }

    # ---------- gRPC Proxy ----------

    server {
        listen 443 ssl http2;
        server_name grpc.example.com;

        ssl_certificate     /etc/nginx/certs/grpc.example.com/fullchain.pem;
        ssl_certificate_key /etc/nginx/certs/grpc.example.com/privkey.pem;

        location / {
            grpc_pass grpc://grpc_backend;
            grpc_set_header X-Real-IP $remote_addr;

            # Error handling per gRPC
            error_page 502 = /error502grpc;
        }

        location = /error502grpc {
            internal;
            default_type application/grpc;
            add_header grpc-status 14;
            add_header grpc-message "Upstream unavailable";
            return 204;
        }
    }

    # ---------- Stub Status per Monitoring ----------

    server {
        listen 8080;
        server_name localhost;

        location /nginx_status {
            stub_status;
            allow 127.0.0.1;
            allow 10.0.0.0/8;
            deny all;
        }
    }
}
```

### Comandi Operativi Nginx

```bash
# Test della configurazione
sudo nginx -t

# Reload graceful
sudo nginx -s reload

# Visualizzare le connessioni attive
curl http://localhost:8080/nginx_status

# Analizzare i log degli upstream
tail -f /var/log/nginx/access.log | awk '{print $NF}'

# Verificare i certificati SSL
openssl s_client -connect api.example.com:443 -servername api.example.com </dev/null 2>/dev/null | openssl x509 -noout -dates
```

### Upstream Avanzato: Zone, Slow Start e Resolver Dinamico

Il blocco `upstream` di Nginx supporta configurazioni avanzate per scenari di produzione complessi.

**Zone directive**: abilita la memoria condivisa tra worker process. Senza `zone`, ogni worker mantiene il proprio contatore di connessioni e fallimenti, portando a distribuzione non uniforme e health check incoerenti.

```nginx
upstream api_backend {
    zone api_upstream 256k;   # Memoria condivisa tra tutti i worker
    least_conn;
    keepalive 64;

    # Slow start: aumenta gradualmente il peso di un server appena aggiunto
    # o appena tornato healthy (solo Nginx Plus)
    server 10.0.1.10:8080 weight=5 max_fails=3 fail_timeout=30s slow_start=30s;
    server 10.0.1.11:8080 weight=5 max_fails=3 fail_timeout=30s slow_start=30s;
    server 10.0.1.12:8080 weight=3 max_fails=3 fail_timeout=30s;
    server 10.0.1.13:8080 backup max_fails=2 fail_timeout=10s;
}
```

**Resolver dinamico**: in ambienti containerizzati (Docker, Kubernetes), gli IP dei backend cambiano frequentemente. Il resolver DNS permette a Nginx di ri-risolvere periodicamente gli hostname senza reload.

```nginx
http {
    # Resolver con TTL e IPv6 disabilitato
    resolver 169.254.169.253 valid=10s ipv6=off;
    resolver_timeout 3s;

    upstream dynamic_backend {
        zone dynamic 128k;
        # Usare variabile per forzare risoluzione DNS dinamica
        server service.internal.local:8080 resolve;
    }

    server {
        location /api/ {
            # Approccio alternativo con variabile (OSS-compatible)
            set $backend_host "api-service.default.svc.cluster.local";
            proxy_pass http://$backend_host:8080;
            proxy_http_version 1.1;
            proxy_set_header Connection "";
        }
    }
}
```

### Nginx Lua (OpenResty) per Logiche Personalizzate

OpenResty estende Nginx con LuaJIT, permettendo di scrivere logiche personalizzate ad alte prestazioni direttamente nel ciclo di vita della richiesta. Le fasi principali in cui Lua puo intervenire sono: `init_worker_by_lua`, `access_by_lua`, `content_by_lua`, `header_filter_by_lua`, `body_filter_by_lua` e `log_by_lua`.

**Rate limiting avanzato con Lua** — limiti differenziati per endpoint, utente e piano di abbonamento:

```nginx
# /etc/nginx/conf.d/lua-rate-limit.conf

lua_shared_dict rate_limit_store 50m;
lua_shared_dict api_keys_cache 10m;

server {
    listen 443 ssl http2;
    server_name api.example.com;

    # Rate limiting Lua-based con logica multi-tier
    access_by_lua_block {
        local limit_req = require "resty.limit.req"

        -- Determinare il tier dell'utente dall'header
        local api_key = ngx.req.get_headers()["X-API-Key"]
        local tier = "free"  -- default
        if api_key then
            local cache = ngx.shared.api_keys_cache
            tier = cache:get(api_key) or "free"
        end

        -- Limiti differenziati per tier
        local limits = {
            free       = { rate = 10,  burst = 20  },
            basic      = { rate = 100, burst = 200 },
            premium    = { rate = 500, burst = 1000 },
            enterprise = { rate = 5000, burst = 10000 }
        }

        local cfg = limits[tier] or limits["free"]
        local lim, err = limit_req.new("rate_limit_store", cfg.rate, cfg.burst)
        if not lim then
            ngx.log(ngx.ERR, "failed to instantiate limiter: ", err)
            return ngx.exit(500)
        end

        local key = ngx.var.binary_remote_addr
        local delay, err = lim:incoming(key, true)
        if not delay then
            if err == "rejected" then
                ngx.header["Retry-After"] = "60"
                ngx.header["X-RateLimit-Limit"] = cfg.rate
                return ngx.exit(429)
            end
            ngx.log(ngx.ERR, "rate limiter error: ", err)
            return ngx.exit(500)
        end

        -- Aggiungere header informativi
        ngx.header["X-RateLimit-Limit"] = cfg.rate
        ngx.header["X-RateLimit-Remaining"] = math.max(0, cfg.burst - delay * cfg.rate)

        if delay >= 0.001 then
            ngx.sleep(delay)
        end
    }

    location /api/ {
        proxy_pass http://api_backend;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
}
```

**Routing dinamico con Lua** — selezione del backend basata su logica applicativa:

```nginx
location /route {
    content_by_lua_block {
        local http = require "resty.http"
        local cjson = require "cjson"

        -- Leggere il body della richiesta
        ngx.req.read_body()
        local body = ngx.req.get_body_data()

        -- Decisione di routing basata sul contenuto
        if body then
            local data = cjson.decode(body)
            local region = data.region or "default"

            local backends = {
                ["eu"]      = "http://10.0.1.10:8080",
                ["us"]      = "http://10.0.2.10:8080",
                ["ap"]      = "http://10.0.3.10:8080",
                ["default"] = "http://10.0.1.10:8080"
            }

            local target = backends[region] or backends["default"]
            local httpc = http.new()
            local res, err = httpc:request_uri(target .. ngx.var.request_uri, {
                method  = ngx.req.get_method(),
                body    = body,
                headers = ngx.req.get_headers(),
            })

            if res then
                ngx.status = res.status
                ngx.say(res.body)
            else
                ngx.status = 502
                ngx.say("Backend error: " .. (err or "unknown"))
            end
        end
    }
}
```

### Caching Avanzato in Nginx

Nginx offre un sistema di caching proxy potente che puo ridurre drasticamente il carico sui backend per contenuti ripetitivi.

**Microcaching**: cache di durata brevissima (1-5 secondi) per endpoint ad alto traffico. Anche una cache di 1 secondo puo assorbire migliaia di richieste duplicate durante un picco.

```nginx
proxy_cache_path /var/cache/nginx/micro
                 levels=1:2
                 keys_zone=micro_cache:5m
                 max_size=500m
                 inactive=1m
                 use_temp_path=off;

server {
    location /api/v1/feed {
        proxy_cache micro_cache;
        proxy_cache_valid 200 1s;            # Cache di 1 secondo
        proxy_cache_valid 404 5s;
        proxy_cache_use_stale error timeout updating http_500 http_502 http_503;
        proxy_cache_lock on;                  # Serializza richieste concorrenti per la stessa chiave
        proxy_cache_lock_timeout 5s;
        proxy_cache_lock_age 5s;
        proxy_cache_background_update on;     # Aggiorna in background
        proxy_cache_revalidate on;            # Usa If-Modified-Since

        # Chiave di cache personalizzata (esclude parametri non rilevanti)
        proxy_cache_key "$scheme$host$uri$arg_page$arg_limit";

        # Bypass della cache per utenti autenticati
        proxy_cache_bypass $http_authorization;
        proxy_no_cache $http_authorization;

        # Header diagnostico
        add_header X-Cache-Status $upstream_cache_status always;

        proxy_pass http://api_backend;
    }
}
```

**Cache purge** (richiede il modulo `ngx_cache_purge` o approccio custom):

```nginx
# Con il modulo ngx_cache_purge
location ~ /purge(/.*) {
    allow 127.0.0.1;
    allow 10.0.0.0/8;
    deny all;
    proxy_cache_purge static_cache "$scheme$host$1";
}

# Approccio alternativo senza modulo — invalidazione via file
# Script esterno che elimina i file di cache corrispondenti
# find /var/cache/nginx/static -type f -name "$(echo -n "$KEY" | md5sum | cut -d' ' -f1)" -delete
```

**Cache condizionale per risposte API**:

```nginx
# Caching solo per GET con risposte piccole
map $request_method $skip_cache {
    default 1;
    GET     0;
    HEAD    0;
}

map $upstream_http_cache_control $skip_cache_control {
    default        0;
    "~*no-cache"   1;
    "~*no-store"   1;
    "~*private"    1;
}

server {
    location /api/v1/public/ {
        proxy_cache api_cache;
        proxy_cache_valid 200 5m;
        proxy_no_cache $skip_cache $skip_cache_control;
        proxy_cache_bypass $skip_cache $skip_cache_control;

        proxy_pass http://api_backend;
    }
}
```

---

## 4. Traefik

### Architettura

Traefik e un reverse proxy e load balancer moderno progettato per ambienti cloud-native e container. La sua architettura si basa su quattro componenti principali:

- **Providers**: fonti di configurazione dinamica. Traefik rileva automaticamente i servizi tramite Docker labels, Kubernetes Ingress/IngressRoute, file di configurazione, Consul, etcd e altri.
- **Routers**: definiscono le regole per associare le richieste in ingresso ai servizi. Le regole possono essere basate su host, path, header, metodo HTTP e query parameters.
- **Middlewares**: componenti che trasformano la richiesta prima che raggiunga il servizio (autenticazione, rate limiting, path stripping, retry, circuit breaker, headers).
- **Services**: definiscono come raggiungere i server backend, con algoritmo di bilanciamento, health check e sticky sessions.

Il flusso e: `Entrypoint -> Router (match rule) -> Middleware chain -> Service -> Backend Servers`.

### Configurazione Statica

```yaml
# /etc/traefik/traefik.yml - Configurazione statica

# Entrypoints
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
    http:
      tls:
        certResolver: letsencrypt
    http2:
      maxConcurrentStreams: 250
  metrics:
    address: ":8082"

# Providers
providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
    network: traefik-public
    watch: true
  file:
    directory: /etc/traefik/dynamic
    watch: true
  kubernetesIngress: {}
  kubernetesCRD: {}

# Let's Encrypt automatico
certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@example.com
      storage: /etc/traefik/acme/acme.json
      httpChallenge:
        entryPoint: web
  letsencrypt-dns:
    acme:
      email: admin@example.com
      storage: /etc/traefik/acme/acme-dns.json
      dnsChallenge:
        provider: cloudflare
        delayBeforeCheck: 10

# API e Dashboard
api:
  dashboard: true
  insecure: false

# Logging
log:
  level: INFO
  filePath: /var/log/traefik/traefik.log
  format: json

accessLog:
  filePath: /var/log/traefik/access.log
  format: json
  bufferingSize: 100
  filters:
    statusCodes:
      - "400-499"
      - "500-599"
    retryAttempts: true
    minDuration: "500ms"

# Metriche Prometheus
metrics:
  prometheus:
    entryPoint: metrics
    addEntryPointsLabels: true
    addRoutersLabels: true
    addServicesLabels: true
    buckets:
      - 0.01
      - 0.05
      - 0.1
      - 0.3
      - 0.5
      - 1.0
      - 3.0
      - 5.0

# Health check globale
ping:
  entryPoint: web

# Serializzazione del traffico in ingresso
serversTransport:
  maxIdleConnsPerHost: 200
  forwardingTimeouts:
    dialTimeout: 5s
    responseHeaderTimeout: 30s
    idleConnTimeout: 90s
```

### Configurazione Dinamica con File Provider

```yaml
# /etc/traefik/dynamic/services.yml

http:
  # ----- Routers -----
  routers:
    api-router:
      rule: "Host(`api.example.com`) && PathPrefix(`/api`)"
      service: api-service
      entryPoints:
        - websecure
      tls:
        certResolver: letsencrypt
      middlewares:
        - rate-limit
        - security-headers
        - api-stripprefix

    web-router:
      rule: "Host(`www.example.com`)"
      service: web-service
      entryPoints:
        - websecure
      tls:
        certResolver: letsencrypt
      middlewares:
        - security-headers
        - compress

    admin-router:
      rule: "Host(`admin.example.com`)"
      service: admin-service
      entryPoints:
        - websecure
      tls:
        certResolver: letsencrypt
      middlewares:
        - admin-auth
        - security-headers
        - admin-ipwhitelist

  # ----- Services -----
  services:
    api-service:
      loadBalancer:
        healthCheck:
          path: /healthz
          interval: 10s
          timeout: 3s
        servers:
          - url: "http://10.0.1.10:8080"
          - url: "http://10.0.1.11:8080"
          - url: "http://10.0.1.12:8080"
        passHostHeader: true
        sticky:
          cookie:
            name: api_affinity
            secure: true
            httpOnly: true

    web-service:
      loadBalancer:
        servers:
          - url: "http://10.0.2.10:8080"
          - url: "http://10.0.2.11:8080"
        healthCheck:
          path: /
          interval: 15s
          timeout: 5s

    admin-service:
      loadBalancer:
        servers:
          - url: "http://10.0.3.10:8080"

  # ----- Middlewares -----
  middlewares:
    rate-limit:
      rateLimit:
        average: 100
        burst: 200
        period: 1s
        sourceCriterion:
          ipStrategy:
            depth: 1

    security-headers:
      headers:
        stsSeconds: 63072000
        stsIncludeSubdomains: true
        stsPreload: true
        contentTypeNosniff: true
        frameDeny: true
        browserXssFilter: true
        referrerPolicy: strict-origin-when-cross-origin
        customResponseHeaders:
          X-Robots-Tag: "noindex,nofollow"
        contentSecurityPolicy: "default-src 'self'; script-src 'self' 'nonce-{random}'; style-src 'self' 'unsafe-inline'"

    compress:
      compress:
        excludedContentTypes:
          - text/event-stream

    api-stripprefix:
      stripPrefix:
        prefixes:
          - /api

    admin-auth:
      basicAuth:
        users:
          - "admin:$apr1$xyz$HashedPasswordHere"
        removeHeader: true

    admin-ipwhitelist:
      ipAllowList:
        sourceRange:
          - "10.0.0.0/8"
          - "192.168.0.0/16"

    retry-middleware:
      retry:
        attempts: 3
        initialInterval: 100ms

    circuit-breaker:
      circuitBreaker:
        expression: "LatencyAtQuantileMS(50.0) > 1000 || NetworkErrorRatio() > 0.30"
        checkPeriod: 10s
        fallbackDuration: 30s
        recoveryDuration: 60s
```

### Traefik con Docker Labels

```yaml
# docker-compose.yml completo con Traefik e servizi

version: "3.8"

services:
  traefik:
    image: traefik:v3.1
    container_name: traefik
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik.yml:/etc/traefik/traefik.yml:ro
      - ./dynamic:/etc/traefik/dynamic:ro
      - ./acme:/etc/traefik/acme
      - ./logs:/var/log/traefik
    labels:
      # Dashboard
      - "traefik.enable=true"
      - "traefik.http.routers.dashboard.rule=Host(`traefik.example.com`)"
      - "traefik.http.routers.dashboard.service=api@internal"
      - "traefik.http.routers.dashboard.entrypoints=websecure"
      - "traefik.http.routers.dashboard.tls.certresolver=letsencrypt"
      - "traefik.http.routers.dashboard.middlewares=dashboard-auth"
      - "traefik.http.middlewares.dashboard-auth.basicauth.users=admin:$$apr1$$xyz$$HashedPassword"
    restart: unless-stopped
    networks:
      - traefik-public

  api-app:
    image: myregistry/api-app:latest
    deploy:
      replicas: 3
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`api.example.com`)"
      - "traefik.http.routers.api.entrypoints=websecure"
      - "traefik.http.routers.api.tls.certresolver=letsencrypt"
      - "traefik.http.services.api.loadbalancer.server.port=8080"
      - "traefik.http.services.api.loadbalancer.healthcheck.path=/healthz"
      - "traefik.http.services.api.loadbalancer.healthcheck.interval=10s"
      - "traefik.http.routers.api.middlewares=rate-limit@file,security-headers@file"
    networks:
      - traefik-public

  web-app:
    image: myregistry/web-app:latest
    deploy:
      replicas: 2
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.web.rule=Host(`www.example.com`)"
      - "traefik.http.routers.web.entrypoints=websecure"
      - "traefik.http.routers.web.tls.certresolver=letsencrypt"
      - "traefik.http.services.web.loadbalancer.server.port=3000"
      - "traefik.http.routers.web.middlewares=security-headers@file,compress@file"
    networks:
      - traefik-public

networks:
  traefik-public:
    external: true
```

### Traefik Kubernetes IngressRoute (CRD)

```yaml
# IngressRoute per Traefik su Kubernetes
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: api-ingressroute
  namespace: production
spec:
  entryPoints:
    - websecure
  routes:
    - match: Host(`api.example.com`) && PathPrefix(`/api/v1`)
      kind: Rule
      services:
        - name: api-service
          port: 8080
          weight: 100
          strategy: RoundRobin
      middlewares:
        - name: rate-limit
          namespace: production
        - name: security-headers
          namespace: production
    - match: Host(`api.example.com`) && PathPrefix(`/api/v2`)
      kind: Rule
      services:
        - name: api-v2-service
          port: 8080
  tls:
    certResolver: letsencrypt
---
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: rate-limit
  namespace: production
spec:
  rateLimit:
    average: 50
    burst: 100
    period: 1s
```

### Traefik v3 — Novita e Funzionalita Avanzate

Traefik v3 introduce miglioramenti significativi in termini di routing, middleware e integrazione Kubernetes.

**Wildcard Host e HostSNI matcher**: Traefik v3 supporta matcher wildcard per hostname, semplificando la gestione di domini multi-tenant.

```yaml
# IngressRoute con wildcard host
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: wildcard-route
  namespace: production
spec:
  entryPoints:
    - websecure
  routes:
    - match: HostRegexp(`{subdomain:[a-z]+}.example.com`)
      kind: Rule
      services:
        - name: multi-tenant-service
          port: 8080
      middlewares:
        - name: tenant-headers
  tls:
    certResolver: letsencrypt
    domains:
      - main: example.com
        sans:
          - "*.example.com"
```

**Multi-layer routing con parent/child IngressRoute**: la struttura gerarchica consente di applicare middleware globali tramite un IngressRoute padre, mentre i figli definiscono il routing specifico. Questo evita la duplicazione di middleware su ogni singola rotta.

```yaml
# IngressRoute padre — applica middleware globali
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: global-middleware-route
  namespace: production
spec:
  entryPoints:
    - websecure
  routes:
    - match: Host(`api.example.com`)
      kind: Rule
      services:
        - name: noop@internal
          kind: TraefikService
      middlewares:
        - name: security-headers
        - name: rate-limit
        - name: compress
---
# IngressRoute figlio — routing specifico
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  name: api-v2-route
  namespace: production
spec:
  entryPoints:
    - websecure
  routes:
    - match: Host(`api.example.com`) && PathPrefix(`/api/v2`)
      kind: Rule
      services:
        - name: api-v2-service
          port: 8080
      middlewares:
        - name: api-v2-auth
  tls:
    certResolver: letsencrypt
```

**Service-level middleware**: Traefik v3 permette di applicare middleware a livello di servizio invece che di router. Questo e utile quando lo stesso servizio e raggiunto da piu router e si desidera applicare trasformazioni uniformi indipendentemente dalla rotta.

```yaml
# Middleware applicati al servizio tramite CRD
apiVersion: traefik.io/v1alpha1
kind: TraefikService
metadata:
  name: weighted-api
  namespace: production
spec:
  weighted:
    services:
      - name: api-v1
        port: 8080
        weight: 80
      - name: api-v2
        port: 8080
        weight: 20
    sticky:
      cookie:
        name: canary_session
        secure: true
        httpOnly: true
        sameSite: strict
```

**Middleware encodedCharacters**: nuovo middleware introdotto in Traefik v3.7 che gestisce la normalizzazione dei caratteri codificati nelle URL, prevenendo bypass delle regole di routing tramite encoding.

**Provider precedence**: Traefik v3 consente di configurare la priorita tra provider multipli. In ambienti ibridi (Docker + file + Kubernetes), e possibile definire quale provider prevale in caso di conflitto.

```yaml
# traefik.yml — Priorita dei provider
providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
  file:
    directory: /etc/traefik/dynamic
    watch: true
  kubernetesCRD:
    allowCrossNamespace: true
    allowExternalNameServices: true
    labelSelector: "environment=production"

# Priorita: CRD > file > Docker (implicita dall'ordine di risoluzione)
```

**Traefik con OpenTelemetry**: Traefik v3 supporta nativamente l'esportazione di tracce distribuite via OpenTelemetry, oltre a Jaeger e Zipkin.

```yaml
# traefik.yml — Tracing con OpenTelemetry
tracing:
  otlp:
    http:
      endpoint: "http://otel-collector:4318/v1/traces"
    grpc:
      endpoint: "otel-collector:4317"
      insecure: true
```

---

## 5. Cloud Load Balancers — AWS

### Application Load Balancer (ALB) — Layer 7

L'ALB opera a Layer 7 e supporta routing basato su contenuto HTTP/HTTPS. Caratteristiche principali:

- Routing basato su host, path, header HTTP, metodo HTTP e query string
- Supporto nativo per HTTP/2 e gRPC
- Autenticazione integrata con Cognito e OIDC
- Integrazione con AWS WAF per protezione a livello applicativo
- Supporto per WebSocket
- Target groups con istanze EC2, IP addresses, Lambda functions e container ECS/EKS
- Listener rules con priority per routing avanzato
- Slow start mode per nuovi target

### Network Load Balancer (NLB) — Layer 4

L'NLB opera a Layer 4 con prestazioni ultra-basse latenza (microsecondi). Caratteristiche principali:

- Gestione di milioni di richieste al secondo
- IP statici ed Elastic IP per indirizzo fisso
- Preservazione dell'IP sorgente del client
- Supporto per protocolli TCP, UDP e TLS
- Cross-zone load balancing configurabile
- Integrazione con AWS PrivateLink per servizi esposti privatamente

### Gateway Load Balancer (GWLB)

Progettato per instradare il traffico attraverso appliance di rete virtuali (firewall, IDS/IPS, deep packet inspection). Opera a Layer 3 (IP) e usa il protocollo GENEVE per l'incapsulamento. I target sono appliance di sicurezza di terze parti.

### Configurazione ALB con Terraform

```hcl
# Application Load Balancer completo con Terraform

resource "aws_lb" "main" {
  name               = "app-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = true
  enable_http2               = true
  idle_timeout               = 60
  drop_invalid_header_fields = true

  access_logs {
    bucket  = aws_s3_bucket.alb_logs.id
    prefix  = "alb-logs"
    enabled = true
  }

  tags = {
    Environment = "production"
  }
}

# Security Group per ALB
resource "aws_security_group" "alb_sg" {
  name_prefix = "alb-sg-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Listener HTTPS
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate.main.arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
}

# Listener HTTP -> redirect HTTPS
resource "aws_lb_listener" "http_redirect" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"
    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# Target Group per API
resource "aws_lb_target_group" "api" {
  name                 = "api-tg"
  port                 = 8080
  protocol             = "HTTP"
  vpc_id               = var.vpc_id
  target_type          = "ip"
  deregistration_delay = 30
  slow_start           = 60

  health_check {
    enabled             = true
    path                = "/healthz"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 15
    matcher             = "200"
  }

  stickiness {
    type            = "lb_cookie"
    cookie_duration = 3600
    enabled         = true
  }
}

# Target Group per Web
resource "aws_lb_target_group" "web" {
  name        = "web-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200-399"
  }
}

# Listener Rule - routing basato su path
resource "aws_lb_listener_rule" "api_routing" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}

# Listener Rule - routing basato su host header
resource "aws_lb_listener_rule" "api_host_routing" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 90

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }

  condition {
    host_header {
      values = ["api.example.com"]
    }
  }
}

# Weighted target group per canary deployment
resource "aws_lb_listener_rule" "canary" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 50

  action {
    type = "forward"

    forward {
      target_group {
        arn    = aws_lb_target_group.web.arn
        weight = 90
      }
      target_group {
        arn    = aws_lb_target_group.web_canary.arn
        weight = 10
      }

      stickiness {
        enabled  = true
        duration = 600
      }
    }
  }

  condition {
    path_pattern {
      values = ["/*"]
    }
  }
}

# WAF Association
resource "aws_wafv2_web_acl_association" "alb_waf" {
  resource_arn = aws_lb.main.arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn
}
```

### Comandi AWS CLI per Load Balancer

```bash
# Elencare tutti gli ALB
aws elbv2 describe-load-balancers --type application

# Dettagli di un ALB specifico
aws elbv2 describe-load-balancers --names app-alb

# Elencare i target group
aws elbv2 describe-target-groups --load-balancer-arn <alb-arn>

# Health status dei target
aws elbv2 describe-target-health --target-group-arn <tg-arn>

# Registrare un nuovo target
aws elbv2 register-targets --target-group-arn <tg-arn> \
  --targets Id=i-0123456789abcdef0,Port=8080

# Deregistrare un target (graceful con connection draining)
aws elbv2 deregister-targets --target-group-arn <tg-arn> \
  --targets Id=i-0123456789abcdef0

# Elencare le listener rules
aws elbv2 describe-rules --listener-arn <listener-arn>

# Accedere ai log dell'ALB su S3
aws s3 ls s3://my-alb-logs/alb-logs/AWSLogs/
```

---

## 6. Cloud Load Balancers — Azure e GCP

### Azure

**Azure Load Balancer (Layer 4)**: load balancer regionale a Layer 4 per traffico TCP/UDP. Supporta SKU Basic e Standard. Lo Standard offre alta disponibilita con zone di disponibilita, metriche diagnostiche e SLA 99.99%. Supporta inbound e outbound rules, health probes (TCP, HTTP, HTTPS) e HA ports per bilanciare tutto il traffico su tutte le porte contemporaneamente.

**Azure Application Gateway (Layer 7)**: reverse proxy e load balancer Layer 7 con WAF integrato (basato su OWASP Core Rule Set). Supporta SSL termination, cookie-based session affinity, URL-based routing, multi-site hosting, WebSocket, HTTP/2 e autoscaling. La versione v2 supporta zone redundancy e static VIP.

**Azure Front Door**: servizio globale Layer 7 che combina load balancing, CDN, WAF e accelerazione applicativa. Opera sulla rete globale Microsoft con PoP distribuiti a livello mondiale. Supporta routing basato su latenza, priority, weighted e session affinity. Integrazione nativa con Private Link per backend protetti.

**Azure Traffic Manager**: load balancer DNS-based che opera a livello DNS. Non gestisce il traffico direttamente ma restituisce l'endpoint ottimale nella risposta DNS. Metodi di routing: Performance (latenza minima), Priority (failover), Weighted, Geographic, MultiValue e Subnet.

```bash
# Azure CLI - Creare un Application Gateway
az network application-gateway create \
  --name myAppGateway \
  --resource-group myRG \
  --sku Standard_v2 \
  --capacity 2 \
  --vnet-name myVNet \
  --subnet appGatewaySubnet \
  --frontend-port 443 \
  --http-settings-port 8080 \
  --http-settings-protocol Http \
  --routing-rule-type Basic \
  --priority 100

# Aggiungere un backend pool
az network application-gateway address-pool create \
  --gateway-name myAppGateway \
  --resource-group myRG \
  --name apiBackendPool \
  --servers 10.0.1.10 10.0.1.11 10.0.1.12

# Configurare health probe
az network application-gateway probe create \
  --gateway-name myAppGateway \
  --resource-group myRG \
  --name apiHealthProbe \
  --protocol Http \
  --host-name-from-http-settings true \
  --path /healthz \
  --interval 15 \
  --threshold 3 \
  --timeout 10

# Azure Front Door
az afd profile create \
  --profile-name myFrontDoor \
  --resource-group myRG \
  --sku Premium_AzureFrontDoor

az afd endpoint create \
  --endpoint-name myEndpoint \
  --profile-name myFrontDoor \
  --resource-group myRG
```

### GCP

**GCP Cloud Load Balancing** offre una gamma di load balancer integrati nella rete globale di Google:

- **External HTTP(S) Load Balancer**: load balancer globale Layer 7. Il traffico viene distribuito tramite gli edge PoP di Google. Supporta URL maps per routing basato su host e path, managed SSL certificates, Cloud CDN integration, Cloud Armor (WAF/DDoS), traffic splitting per canary deployment.
- **External TCP/SSL Proxy Load Balancer**: load balancer globale Layer 4 per traffico TCP con opzione SSL offloading.
- **External Network Load Balancer**: load balancer regionale Layer 4, pass-through (non proxy). Preserva l'IP sorgente del client.
- **Internal HTTP(S) Load Balancer**: load balancer Layer 7 per traffico interno alla VPC. Basato su Envoy proxy.
- **Internal TCP/UDP Load Balancer**: load balancer Layer 4 regionale per traffico interno.

```bash
# GCP CLI - Creare un HTTP(S) Load Balancer

# 1. Creare health check
gcloud compute health-checks create http api-health-check \
  --port=8080 \
  --request-path=/healthz \
  --check-interval=10s \
  --timeout=5s \
  --healthy-threshold=2 \
  --unhealthy-threshold=3

# 2. Creare backend service
gcloud compute backend-services create api-backend-svc \
  --protocol=HTTP \
  --port-name=http \
  --health-checks=api-health-check \
  --global \
  --enable-cdn \
  --connection-draining-timeout=30s

# 3. Aggiungere instance group al backend
gcloud compute backend-services add-backend api-backend-svc \
  --instance-group=api-ig \
  --instance-group-zone=europe-west1-b \
  --global \
  --balancing-mode=UTILIZATION \
  --max-utilization=0.8

# 4. Creare URL map
gcloud compute url-maps create web-url-map \
  --default-service=web-backend-svc

# 5. Aggiungere path matcher
gcloud compute url-maps add-path-matcher web-url-map \
  --path-matcher-name=api-paths \
  --default-service=api-backend-svc \
  --path-rules="/api/*=api-backend-svc,/static/*=cdn-backend-svc"

# 6. Creare target HTTP(S) proxy
gcloud compute target-https-proxies create web-https-proxy \
  --url-map=web-url-map \
  --ssl-certificates=my-ssl-cert

# 7. Creare forwarding rule globale
gcloud compute forwarding-rules create web-forwarding-rule \
  --global \
  --target-https-proxy=web-https-proxy \
  --ports=443 \
  --ip-version=IPV4
```

### Confronto tra Cloud Provider

| Funzionalita              | AWS ALB/NLB         | Azure App GW/LB    | GCP HTTP(S) LB      |
|---------------------------|---------------------|---------------------|----------------------|
| Layer 7 globale           | CloudFront + ALB    | Front Door          | External HTTP(S) LB  |
| Layer 4                   | NLB                 | Azure LB            | Network LB           |
| WAF integrato             | WAF v2              | App GW WAF          | Cloud Armor           |
| CDN integrato             | CloudFront          | Front Door CDN      | Cloud CDN             |
| Managed SSL               | ACM                 | App GW + Key Vault  | Managed certificates  |
| gRPC                      | ALB                 | App GW v2           | HTTP(S) LB            |
| WebSocket                 | ALB/NLB             | App GW              | HTTP(S) LB            |
| Costo base (mese, approx) | ~20-30 USD          | ~20-180 USD         | ~20-25 USD            |
| Autoscaling               | Si                  | App GW v2 si        | Si (automatico)       |
| DNS-based                 | Route 53            | Traffic Manager     | Cloud DNS             |

---

## 7. SSL/TLS e Certificati

### Configurazione TLS Moderna

La configurazione TLS deve bilanciare sicurezza e compatibilita. Le linee guida attuali (Mozilla Server Side TLS) raccomandano:

**Configurazione "Modern"** (solo client recenti):
- TLS 1.3 esclusivamente
- Cipher suites: TLS_AES_128_GCM_SHA256, TLS_AES_256_GCM_SHA384, TLS_CHACHA20_POLY1305_SHA256
- Non richiede configurazione del server-side cipher order (TLS 1.3 non lo supporta)

**Configurazione "Intermediate"** (compatibilita ragionevole):
- TLS 1.2 e TLS 1.3
- Cipher suites TLS 1.2: ECDHE-ECDSA-AES128-GCM-SHA256, ECDHE-RSA-AES128-GCM-SHA256, ECDHE-ECDSA-AES256-GCM-SHA384, ECDHE-RSA-AES256-GCM-SHA384, ECDHE-ECDSA-CHACHA20-POLY1305, ECDHE-RSA-CHACHA20-POLY1305, DHE-RSA-AES128-GCM-SHA256, DHE-RSA-AES256-GCM-SHA384
- Curve ECDHE: X25519, prime256v1, secp384r1
- DH parameters: 2048 bit minimo (preferibilmente ffdhe2048)

### HSTS (HTTP Strict Transport Security)

HSTS informa il browser che il sito deve essere raggiunto esclusivamente tramite HTTPS. Il browser converte automaticamente tutti i futuri tentativi HTTP in HTTPS prima di inviare la richiesta.

```
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
```

- `max-age=63072000`: 2 anni. Il browser ricordera la policy per questa durata.
- `includeSubDomains`: applica HSTS a tutti i sottodomini.
- `preload`: richiesta di inclusione nella HSTS preload list dei browser, eliminando la vulnerabilita del primo accesso.

### OCSP Stapling

L'OCSP stapling elimina la necessita per il client di contattare la Certificate Authority per verificare la revoca del certificato. Il server ottiene la risposta OCSP dalla CA e la include (staple) nel TLS handshake.

```nginx
# Nginx OCSP Stapling
ssl_stapling on;
ssl_stapling_verify on;
ssl_trusted_certificate /etc/nginx/certs/chain.pem;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
```

### Let's Encrypt con Certbot

```bash
# Installazione certbot
sudo apt install -y certbot python3-certbot-nginx

# Ottenere certificato con plugin Nginx
sudo certbot --nginx -d example.com -d www.example.com \
  --non-interactive --agree-tos --email admin@example.com

# Ottenere certificato standalone (senza web server in ascolto)
sudo certbot certonly --standalone -d example.com \
  --non-interactive --agree-tos --email admin@example.com

# Ottenere certificato wildcard con DNS challenge
sudo certbot certonly --dns-cloudflare \
  --dns-cloudflare-credentials /etc/letsencrypt/cloudflare.ini \
  -d example.com -d "*.example.com" \
  --non-interactive --agree-tos --email admin@example.com

# Rinnovo automatico - test dry run
sudo certbot renew --dry-run

# Rinnovo con hook post-rinnovo
sudo certbot renew --deploy-hook "systemctl reload nginx"

# Verifica scadenza certificati
sudo certbot certificates

# Cron job per rinnovo automatico (gia configurato da certbot)
# 0 0,12 * * * root certbot renew --quiet --deploy-hook "systemctl reload nginx"
```

### Certificato per HAProxy (formato combinato)

HAProxy richiede certificato e chiave privata in un unico file:

```bash
# Combinare certificato e chiave per HAProxy
cat /etc/letsencrypt/live/example.com/fullchain.pem \
    /etc/letsencrypt/live/example.com/privkey.pem \
    > /etc/haproxy/certs/example.com.pem

# Hook di deploy per certbot con HAProxy
# /etc/letsencrypt/renewal-hooks/deploy/haproxy-deploy.sh
#!/bin/bash
DOMAIN=$RENEWED_LINEAGE
cat "${DOMAIN}/fullchain.pem" "${DOMAIN}/privkey.pem" \
    > /etc/haproxy/certs/$(basename ${DOMAIN}).pem
systemctl reload haproxy
```

### mTLS (Mutual TLS) per Backend

mTLS richiede che sia il client che il server presentino un certificato durante il TLS handshake. Utile per la comunicazione sicura tra load balancer e backend, o tra microservizi.

```nginx
# Nginx - mTLS verso il backend
upstream secure_backend {
    server 10.0.1.10:8443;
}

server {
    location /api/ {
        proxy_pass https://secure_backend;
        proxy_ssl_certificate     /etc/nginx/certs/client.pem;
        proxy_ssl_certificate_key /etc/nginx/certs/client-key.pem;
        proxy_ssl_trusted_certificate /etc/nginx/certs/backend-ca.pem;
        proxy_ssl_verify on;
        proxy_ssl_verify_depth 2;
        proxy_ssl_session_reuse on;
        proxy_ssl_protocols TLSv1.2 TLSv1.3;
    }
}
```

```
# HAProxy - mTLS verso il backend
backend secure_backend
    mode http
    server backend1 10.0.1.10:8443 ssl verify required \
        ca-file /etc/haproxy/certs/backend-ca.pem \
        crt /etc/haproxy/certs/client-combined.pem
```

### Verifica della Configurazione TLS

```bash
# Test completo della configurazione TLS
openssl s_client -connect example.com:443 -servername example.com \
  -tls1_3 </dev/null 2>/dev/null | openssl x509 -noout -text

# Verificare i protocolli supportati
nmap --script ssl-enum-ciphers -p 443 example.com

# Verifica HSTS
curl -sI https://example.com | grep -i strict-transport

# Verifica OCSP stapling
openssl s_client -connect example.com:443 -servername example.com \
  -status </dev/null 2>&1 | grep -A 3 "OCSP Response"

# Test con SSL Labs (da riga di comando via ssllabs-scan)
ssllabs-scan --grade example.com
```

---

## 8. Pattern Architetturali

### DMZ Design

La DMZ (Demilitarized Zone) e una zona di rete intermedia tra la rete esterna (Internet) e la rete interna. Il load balancer/reverse proxy si posiziona nella DMZ e funge da unico punto di ingresso. Il traffico attraversa due livelli di firewall:

1. **Firewall esterno**: consente solo traffico HTTP/HTTPS dalla rete pubblica verso il load balancer nella DMZ.
2. **Load balancer nella DMZ**: termina SSL, applica WAF rules, filtra richieste malevole.
3. **Firewall interno**: consente solo traffico dal load balancer verso i backend nella rete interna, su porte specifiche.
4. **Backend nella rete interna**: mai esposti direttamente a Internet.

Questo design implementa il principio di defense-in-depth: anche se il load balancer viene compromesso, l'attaccante deve superare il firewall interno per raggiungere i dati.

### Multi-Tier Load Balancing

In architetture complesse, il bilanciamento opera su piu livelli:

**Tier 1 — Edge/Global**: DNS-based o anycast load balancing distribuisce il traffico tra datacenter o regioni. Gestito da CDN (Cloudflare, Akamai) o servizi cloud (AWS Global Accelerator, Azure Front Door).

**Tier 2 — Datacenter ingress**: load balancer Layer 7 (HAProxy, Nginx, ALB) all'ingresso del datacenter. Esegue SSL termination, WAF, routing basato su contenuto.

**Tier 3 — Service mesh**: load balancing tra microservizi interni gestito da sidecar proxy (Envoy, Linkerd) con service discovery dinamica, circuit breaking e retry automatici.

### Blue-Green Deployment

Nel blue-green deployment, due ambienti identici (blue = produzione attuale, green = nuova versione) coesistono. Il load balancer funge da switch per reindirizzare il traffico:

```
# HAProxy - Switch blue-green tramite runtime API
# Attivare il green environment
echo "set server backend_web/green-1 state ready" | socat stdio /var/run/haproxy/admin.sock
echo "set server backend_web/green-2 state ready" | socat stdio /var/run/haproxy/admin.sock
echo "set server backend_web/blue-1 state drain"  | socat stdio /var/run/haproxy/admin.sock
echo "set server backend_web/blue-2 state drain"  | socat stdio /var/run/haproxy/admin.sock
```

```nginx
# Nginx - Blue-green con variabile
upstream blue {
    server 10.0.1.10:8080;
    server 10.0.1.11:8080;
}

upstream green {
    server 10.0.2.10:8080;
    server 10.0.2.11:8080;
}

# In /etc/nginx/conf.d/active-env.conf (aggiornato dallo script di deploy)
# set $active_env "green";

server {
    location / {
        proxy_pass http://$active_env;
    }
}
```

### Canary Release con Weighted Routing

Il canary release instrada una percentuale ridotta di traffico alla nuova versione per validarla gradualmente prima del rollout completo:

```nginx
# Nginx - Canary con split_clients
split_clients "${remote_addr}${uri}" $backend_variant {
    5%   canary_backend;
    *    stable_backend;
}

upstream stable_backend {
    server 10.0.1.10:8080;
    server 10.0.1.11:8080;
}

upstream canary_backend {
    server 10.0.2.10:8080;
}

server {
    location / {
        proxy_pass http://$backend_variant;
    }
}
```

```
# HAProxy - Canary con weighted servers
backend web_production
    balance roundrobin
    server stable-1 10.0.1.10:8080 weight 95 check
    server stable-2 10.0.1.11:8080 weight 95 check
    server canary-1 10.0.2.10:8080 weight 5  check
```

### Geographic Load Balancing

Il geographic load balancing indirizza gli utenti al datacenter geograficamente piu vicino per minimizzare la latenza. Implementazioni:

- **DNS-based**: il DNS resolver restituisce l'IP del datacenter piu vicino in base alla geolocalizzazione dell'IP del resolver (Route 53 Geolocation, Azure Traffic Manager Geographic, GCP Cloud DNS).
- **Anycast**: lo stesso IP e annunciato da piu datacenter via BGP. Il routing Internet dirige i pacchetti al PoP piu vicino (usato da Cloudflare, Fastly, Google).
- **Application-level**: il load balancer globale (Azure Front Door, GCP HTTP(S) LB) misura la latenza tra i PoP e i backend e instrada verso quello con latenza minore.

### Failover Multi-Datacenter

```
# HAProxy - Failover tra datacenter
backend web_multidatacenter
    balance roundrobin
    option httpchk GET /healthz

    # Datacenter primario (Europa)
    server eu-web-1 10.0.1.10:8080 check weight 100
    server eu-web-2 10.0.1.11:8080 check weight 100

    # Datacenter secondario (US) - usato solo se il primario e down
    server us-web-1 10.1.1.10:8080 check weight 100 backup
    server us-web-2 10.1.1.11:8080 check weight 100 backup

    # Fallback di emergenza
    server dr-web-1 10.2.1.10:8080 check backup
```

### API Gateway vs Reverse Proxy

Un **reverse proxy** (Nginx, HAProxy) gestisce routing, load balancing, SSL termination e caching. Opera prevalentemente a livello di rete e trasporto.

Un **API gateway** (Kong, AWS API Gateway, Apigee) aggiunge funzionalita a livello applicativo: autenticazione e autorizzazione (OAuth2, JWT, API key), rate limiting per utente/piano, request/response transformation, API versioning, developer portal, analytics e monetizzazione.

In molte architetture i due componenti coesistono: il reverse proxy gestisce il traffico generico e la DMZ, l'API gateway protegge e gestisce specificamente le API.

---

## 9. Performance e Tuning

### Connection Pooling e Keep-Alive

Il connection pooling tra load balancer e backend riduce drasticamente l'overhead del TCP handshake e del TLS negotiation per ogni richiesta:

```nginx
# Nginx - Keepalive verso il backend
upstream api_backend {
    server 10.0.1.10:8080;
    server 10.0.1.11:8080;
    keepalive 64;           # Pool di 64 connessioni idle per worker
    keepalive_requests 1000; # Max richieste per connessione
    keepalive_timeout 60s;   # Timeout per connessioni idle nel pool
}

server {
    location /api/ {
        proxy_pass http://api_backend;
        proxy_http_version 1.1;           # Necessario per keepalive
        proxy_set_header Connection "";    # Rimuove "close" dal client
    }
}
```

```
# HAProxy - Connection reuse
defaults
    option http-server-close        # Chiude la connessione server dopo la risposta
    # oppure
    option http-keep-alive          # Mantiene le connessioni aperte (preferito)

backend api
    http-reuse safe                 # Riutilizza connessioni se sicuro
    # http-reuse always             # Riutilizza sempre (attenzione a header sensibili)
```

### Buffer e Timeout Tuning

```nginx
# Nginx - Tuning dei buffer
proxy_buffering on;
proxy_buffer_size 4k;          # Buffer per la prima parte della risposta (header)
proxy_buffers 8 16k;           # 8 buffer da 16k per il body
proxy_busy_buffers_size 32k;   # Buffer usabili mentre il resto e in scrittura su disco
proxy_temp_file_write_size 64k;

# Timeout
proxy_connect_timeout 5s;     # Timeout per connessione al backend
proxy_send_timeout 30s;       # Timeout per invio dati al backend
proxy_read_timeout 60s;       # Timeout per ricevere risposta dal backend
send_timeout 30s;             # Timeout per invio dati al client
```

### TCP Tuning a Livello di Sistema Operativo

```bash
# /etc/sysctl.conf - Tuning kernel per load balancer

# Aumentare il backlog delle connessioni in coda
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 65535
net.ipv4.tcp_max_syn_backlog = 65535

# Disabilitare TCP slow start dopo idle
net.ipv4.tcp_slow_start_after_idle = 0

# Abilitare TCP Fast Open
net.ipv4.tcp_fastopen = 3

# Ridurre timeout per connessioni TIME_WAIT
net.ipv4.tcp_fin_timeout = 15

# Riciclare connessioni TIME_WAIT
net.ipv4.tcp_tw_reuse = 1

# Aumentare i range di porte effimere
net.ipv4.ip_local_port_range = 1024 65535

# Buffer TCP
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# Keepalive TCP
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_keepalive_probes = 5

# Abilitare TCP_NODELAY (disabilita Nagle's algorithm)
# Configurato a livello applicativo, non sysctl

# Applicare
sudo sysctl -p
```

### Compressione

```nginx
# Nginx - Compressione gzip e Brotli
gzip on;
gzip_vary on;
gzip_proxied any;
gzip_comp_level 4;           # 1-9, 4-6 e il compromesso migliore
gzip_min_length 256;         # Non comprimere risposte piccole
gzip_types
    text/plain text/css text/xml text/javascript
    application/json application/javascript application/xml
    application/xml+rss application/x-font-ttf
    font/opentype image/svg+xml;

# Brotli (richiede modulo ngx_brotli)
brotli on;
brotli_comp_level 4;
brotli_types text/plain text/css text/xml text/javascript
    application/json application/javascript application/xml;
```

### HTTP/2 e HTTP/3

HTTP/2 introduce multiplexing (piu richieste su una singola connessione TCP), header compression (HPACK) e server push. Per il load balancer, HTTP/2 e particolarmente vantaggioso tra client e load balancer, mentre la connessione verso il backend puo rimanere HTTP/1.1 con keepalive.

HTTP/3 (QUIC) utilizza UDP invece di TCP, eliminando il head-of-line blocking a livello di trasporto. QUIC integra TLS 1.3 nel protocollo, riducendo il round-trip del handshake iniziale a 0-RTT per connessioni ripetute.

```nginx
# Nginx - HTTP/2 e HTTP/3
server {
    listen 443 ssl;
    listen 443 quic reuseport;    # HTTP/3 su UDP
    http2 on;

    # Informare il client del supporto HTTP/3
    add_header Alt-Svc 'h3=":443"; ma=86400' always;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_early_data on;            # 0-RTT per TLS 1.3 (attenzione a replay attacks)
}
```

### Benchmarking

```bash
# wrk - Test HTTP avanzato con scripting Lua
wrk -t12 -c400 -d30s --latency https://api.example.com/api/v1/items

# ab (Apache Benchmark) - Test semplice
ab -n 10000 -c 100 -k https://api.example.com/api/v1/items

# vegeta - Load testing con report dettagliati
echo "GET https://api.example.com/api/v1/items" | \
  vegeta attack -duration=60s -rate=500/s | \
  vegeta report -type=text

# vegeta - Report con distribuzione latenza
echo "GET https://api.example.com/api/v1/items" | \
  vegeta attack -duration=60s -rate=500/s | \
  vegeta report -type='hist[0,5ms,10ms,25ms,50ms,100ms,250ms,500ms,1s]'

# hey - Load testing moderno
hey -n 10000 -c 200 -z 30s https://api.example.com/api/v1/items

# k6 - Load testing programmabile
k6 run --vus 100 --duration 60s load-test.js
```

---

## 10. Monitoring e Troubleshooting

### Metriche Chiave

Le metriche fondamentali da monitorare su un load balancer sono:

**Throughput**: numero di richieste al secondo (RPS). Una diminuzione improvvisa puo indicare problemi di backend o saturazione del load balancer.

**Latenza**: misurare i percentili p50, p95 e p99. La media e ingannevole perche nasconde i picchi. Un p99 elevato indica che l'1% delle richieste piu lente ha tempi inaccettabili, anche se il p50 e buono. Alert raccomandato: p99 > 2x rispetto al baseline.

**Error Rate**: percentuale di risposte 5xx sul totale. Distinguere tra errori del load balancer (502, 503, 504) ed errori del backend (500). Il 502 indica che il backend ha risposto con un errore o ha chiuso la connessione; il 503 che nessun backend e disponibile; il 504 che il backend non ha risposto entro il timeout.

**Active Connections**: numero di connessioni attive contemporaneamente. Un aumento costante senza corrispondente aumento di traffico indica connection leak.

**Backend Health**: numero di backend healthy vs total. Alert se il rapporto scende sotto una soglia critica.

**Queue Depth**: in HAProxy, il numero di richieste in coda in attesa di un backend disponibile. Un valore costantemente > 0 indica sotto-dimensionamento.

### HAProxy Statistics

```bash
# Abilitare la pagina statistiche (gia configurata nel cfg sopra)
# Accessibile su http://loadbalancer:8404/stats

# Esportare metriche in formato Prometheus con haproxy_exporter
docker run -d --name haproxy-exporter \
  -p 9101:9101 \
  quay.io/prometheus/haproxy-exporter \
  --haproxy.scrape-uri="http://admin:SecureP4ssw0rd!@haproxy:8404/stats;csv"

# Prometheus scrape config
# - job_name: haproxy
#   static_configs:
#     - targets: ['haproxy-exporter:9101']

# Query CSV dalle statistiche
echo "show stat" | socat stdio /var/run/haproxy/admin.sock | \
  awk -F',' '{print $1,$2,$5,$8,$18,$34,$37,$40}'
# pxname, svname, scur, stot, hrsp_5xx, bin, bout, rate
```

### Nginx Monitoring

```bash
# Abilitare stub_status (gia configurato nel nginx.conf sopra)
# Mostra: active connections, accepts, handled, requests, reading, writing, waiting
curl http://localhost:8080/nginx_status

# Output esempio:
# Active connections: 291
# server accepts handled requests
#  16630948 16630948 31070465
# Reading: 6 Writing: 179 Waiting: 106

# Nginx Prometheus Exporter
docker run -d --name nginx-exporter \
  -p 9113:9113 \
  nginx/nginx-prometheus-exporter \
  --nginx.scrape-uri=http://nginx:8080/nginx_status

# Log analysis - top IP per numero richieste
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -20

# Log analysis - distribuzione codici di risposta
awk '{print $9}' /var/log/nginx/access.log | sort | uniq -c | sort -rn

# Log analysis - richieste piu lente (usando il formato di log con rt=)
awk -F'rt=' '{print $2}' /var/log/nginx/access.log | awk '{print $1}' | \
  sort -rn | head -20
```

### Traefik Metrics

Traefik espone metriche Prometheus nativamente sull'entrypoint dedicato (configurato nella sezione 4). Le metriche principali:

- `traefik_entrypoint_requests_total`: contatore totale richieste per entrypoint, codice e metodo
- `traefik_service_request_duration_seconds_bucket`: istogramma latenza per servizio
- `traefik_service_requests_total`: contatore richieste per servizio e codice
- `traefik_entrypoint_open_connections`: connessioni attive
- `traefik_service_server_up`: stato dei backend (1=up, 0=down)

```yaml
# Esempio Grafana dashboard queries (PromQL)
# Request rate per servizio
# rate(traefik_service_requests_total{service="api-service@file"}[5m])

# Latenza p99
# histogram_quantile(0.99, rate(traefik_service_request_duration_seconds_bucket{service="api-service@file"}[5m]))

# Error rate
# rate(traefik_service_requests_total{code=~"5.."}[5m]) / rate(traefik_service_requests_total[5m])
```

### Debugging del Traffico

```bash
# tcpdump - Catturare traffico sul load balancer
sudo tcpdump -i eth0 -n port 443 -c 100 -w /tmp/capture.pcap

# tcpdump - Traffico verso un backend specifico
sudo tcpdump -i eth0 -n host 10.0.1.10 and port 8080 -A

# curl verbose per debug
curl -vvv --resolve api.example.com:443:10.0.0.5 \
  https://api.example.com/api/v1/health \
  -H "X-Request-ID: debug-12345" 2>&1

# Verificare quale backend risponde (header custom)
curl -s -D- https://api.example.com/api/v1/items | grep -i "x-served-by\|x-backend"

# Test connettivita TCP verso un backend
nc -zv 10.0.1.10 8080

# Verificare DNS resolution
dig +short api.example.com
nslookup api.example.com

# Verificare lo stato delle connessioni TCP
ss -tnp | grep ':8080' | awk '{print $4}' | sort | uniq -c | sort -rn

# Verificare connessioni in TIME_WAIT
ss -tan state time-wait | wc -l
```

### Problemi Comuni e Diagnosi

**502 Bad Gateway**: il load balancer non riesce a ottenere una risposta valida dal backend. Cause:
- Backend crashato o non in ascolto sulla porta configurata
- Backend che chiude la connessione prematuramente
- Risposta del backend con formato non valido
- Timeout del backend prima di inviare gli header di risposta

```bash
# Diagnosi 502
# 1. Verificare che il backend sia raggiungibile
curl -v http://10.0.1.10:8080/healthz

# 2. Controllare i log del backend
journalctl -u myapp -f

# 3. Controllare i log del load balancer
tail -f /var/log/nginx/error.log
tail -f /var/log/haproxy.log
```

**503 Service Unavailable**: nessun backend healthy disponibile. Cause:
- Tutti i backend hanno fallito gli health check
- Connection limit raggiunto (maxconn in HAProxy)
- Load balancer in maintenance mode

**504 Gateway Timeout**: il backend non ha risposto entro il timeout configurato. Cause:
- Query database lenta
- Deadlock applicativo
- Backend sovraccarico

**Connection Draining issues**: durante un deploy, le connessioni attive devono essere completate prima di rimuovere un backend. Se il deregistration delay e troppo breve, i client ricevono errori.

```bash
# Verifica connection draining
# HAProxy - drain mode
echo "set server backend_api/api-1 state drain" | socat stdio /var/run/haproxy/admin.sock
# Monitorare le connessioni residue
echo "show servers state" | socat stdio /var/run/haproxy/admin.sock | grep api-1

# Nginx - verificare connessioni attive su un backend
ss -tnp | grep 10.0.1.10:8080 | wc -l
```

---

## 11. Best Practices

### Security Hardening

1. **Minimizzare la superficie di attacco**: esporre solo le porte strettamente necessarie (80, 443). Proteggere le porte di management (stats page, admin API) con autenticazione e restrizioni IP.

2. **Disabilitare le informazioni server**: rimuovere o offuscare gli header che rivelano la versione del software.

```nginx
# Nginx
server_tokens off;
# Rimuovere header "Server"
more_set_headers "Server: ";
```

```
# HAProxy
http-response del-header Server
http-response set-header Server "webserver"
```

3. **Protezione DDoS di base**: configurare rate limiting su tutti gli endpoint pubblici, limitare la dimensione del body delle richieste, configurare timeout aggressivi per connessioni lente (slowloris protection).

```
# HAProxy - Protezione slowloris
timeout http-request 5s
timeout client 10s

# Limitare connessioni per IP
stick-table type ip size 100k expire 30s store conn_cur
acl too_many_conns sc0_conn_cur gt 50
tcp-request connection track-sc0 src
tcp-request connection reject if too_many_conns
```

4. **Header di sicurezza**: applicare sistematicamente HSTS, X-Content-Type-Options, X-Frame-Options, CSP, Referrer-Policy e Permissions-Policy su tutte le risposte.

5. **Aggiornamenti regolari**: monitorare CVE per HAProxy, Nginx e le librerie OpenSSL. Applicare patch di sicurezza tempestivamente. Sottoscrivere le mailing list di sicurezza dei software utilizzati.

### Logging Strategy

Una strategia di logging efficace per il load balancer deve bilanciare completezza e volume:

1. **Access logs**: registrare tutte le richieste con formato strutturato (JSON preferibile per parsing automatico). Includere: timestamp, client IP, metodo, URL, codice risposta, dimensione risposta, tempo di risposta, upstream server, upstream response time, request ID.

2. **Error logs**: livello warn o superiore in produzione. Includere stack trace e contesto.

3. **Retention**: conservare access logs per almeno 30 giorni online (per troubleshooting) e 90-365 giorni in archivio (per compliance e analisi).

4. **Centralizzazione**: inviare i log a un sistema centralizzato (ELK stack, Loki, Splunk) per correlazione e analisi.

5. **Sampling**: per volumi estremi (> 100K RPS), considerare il campionamento dei log di successo (es. 10%) mantenendo il 100% dei log di errore.

```nginx
# Nginx - Log format JSON strutturato
log_format json_combined escape=json
  '{'
    '"timestamp":"$time_iso8601",'
    '"remote_addr":"$remote_addr",'
    '"request_method":"$request_method",'
    '"request_uri":"$request_uri",'
    '"status":$status,'
    '"body_bytes_sent":$body_bytes_sent,'
    '"request_time":$request_time,'
    '"upstream_addr":"$upstream_addr",'
    '"upstream_response_time":"$upstream_response_time",'
    '"upstream_status":"$upstream_status",'
    '"http_user_agent":"$http_user_agent",'
    '"request_id":"$request_id"'
  '}';

access_log /var/log/nginx/access.json json_combined;
```

### Graceful Shutdown e Connection Draining

Durante un deploy o un maintenance, il load balancer deve consentire alle connessioni attive di completarsi prima di rimuovere un backend:

1. **Segnalare l'intenzione di rimuovere il backend**: mettere il server in drain mode (accetta solo le richieste gia avviate, rifiuta nuove connessioni).
2. **Attendere il completamento**: attendere che tutte le connessioni attive terminino, con un timeout massimo (deregistration delay).
3. **Rimuovere il backend**: dopo il drain, il server puo essere fermato in sicurezza.

```bash
# Procedura di deploy zero-downtime con HAProxy
# 1. Drain del vecchio server
echo "set server backend_api/api-old state drain" | socat stdio /var/run/haproxy/admin.sock

# 2. Attendere che le connessioni si svuotino (max 30 secondi)
for i in $(seq 1 30); do
  CONNS=$(echo "show servers state" | socat stdio /var/run/haproxy/admin.sock | \
    grep "api-old" | awk '{print $7}')
  if [ "$CONNS" -eq 0 ]; then
    echo "Drained after ${i}s"
    break
  fi
  sleep 1
done

# 3. Deploy della nuova versione e aggiunta del nuovo server
echo "set server backend_api/api-new state ready" | socat stdio /var/run/haproxy/admin.sock

# 4. Rimuovere il vecchio server
echo "set server backend_api/api-old state maint" | socat stdio /var/run/haproxy/admin.sock
```

### Configuration Management e Versioning

1. **Versionare tutte le configurazioni**: le configurazioni del load balancer devono risiedere in un repository Git. Ogni modifica deve passare attraverso un processo di code review.

2. **Validazione pre-deploy**: integrare nel CI/CD la validazione sintattica della configurazione prima del deploy.

```bash
# Validazione configurazione HAProxy
haproxy -c -f /etc/haproxy/haproxy.cfg

# Validazione configurazione Nginx
nginx -t -c /etc/nginx/nginx.conf

# Validazione configurazione Traefik
traefik healthcheck --configFile=/etc/traefik/traefik.yml
```

3. **Rollback rapido**: mantenere sempre disponibile la versione precedente della configurazione per un rollback immediato in caso di problemi.

4. **Infrastructure as Code**: per i cloud load balancer, usare Terraform, Pulumi o CloudFormation per gestire le risorse in modo dichiarativo e riproducibile.

### Disaster Recovery

1. **Multi-region deployment**: configurare load balancer in almeno due regioni geografiche con failover automatico tramite DNS-based routing o global load balancing.

2. **Backup della configurazione**: automatizzare il backup delle configurazioni del load balancer, dei certificati e delle ACL.

3. **Runbook documentato**: documentare le procedure di failover manuale per scenari in cui l'automazione fallisce.

4. **Test periodici**: eseguire regolarmente chaos engineering e failover test per validare le procedure di DR. Un piano di DR non testato e un piano che non funziona.

### Scalabilita Orizzontale

Il load balancer stesso puo diventare un bottleneck. Strategie di scalabilita:

- **Scale-up**: aumentare le risorse (CPU, memoria, banda di rete) della macchina del load balancer. HAProxy e Nginx sono estremamente efficienti e spesso un singolo server e sufficiente per milioni di richieste al secondo.
- **Scale-out con DNS**: usare DNS round-robin per distribuire il traffico su piu istanze di load balancer. Semplice ma senza health checking a livello DNS.
- **Scale-out con ECMP**: configurare il routing di rete per distribuire il traffico su piu load balancer usando Equal-Cost Multi-Path routing. Piu sofisticato del DNS, con failover a livello di rete.
- **Cloud-managed**: i load balancer cloud (ALB, GCP HTTP LB) scalano automaticamente in base al traffico. Non richiedono intervento manuale per la scalabilita.

### Compliance

Per ambienti soggetti a regolamentazione (PCI-DSS, HIPAA, GDPR, SOC2):

- **TLS obbligatorio**: disabilitare completamente HTTP. Usare TLS 1.2+ con cipher suites conformi.
- **Logging di accesso**: conservare i log per il periodo richiesto dalla normativa. Proteggere i log da manomissione (append-only storage).
- **Audit trail**: registrare tutte le modifiche alla configurazione del load balancer con timestamp e identita dell'operatore.
- **Segregazione di rete**: implementare segmentazione di rete tra ambienti diversi (produzione, staging, sviluppo). Il load balancer non deve consentire routing tra segmenti non autorizzati.

---

## 12. Envoy Proxy — Deep-Dive

### Architettura di Envoy

Envoy e un proxy ad alte prestazioni sviluppato originariamente da Lyft e oggi progetto graduato della CNCF. E scritto in C++ e progettato per ambienti cloud-native e service mesh. A differenza di HAProxy e Nginx, che nascono come componenti standalone, Envoy e pensato per operare come sidecar proxy affiancato a ogni istanza di servizio, formando il data plane di un service mesh.

L'architettura si compone di:
- **Listener**: punto di ingresso che definisce su quale indirizzo e porta Envoy accetta connessioni. Ogni listener ha una catena di filter (filter chain).
- **Filter chain**: sequenza ordinata di filtri che elaborano la connessione e le richieste. I filtri possono essere a livello di rete (L3/L4) o a livello HTTP (L7).
- **Cluster**: gruppo di endpoint upstream logicamente equivalenti. Corrisponde al concetto di backend in HAProxy o upstream in Nginx.
- **Endpoint**: singola istanza di un servizio (IP + porta) all'interno di un cluster.
- **Route**: regole di instradamento che associano richieste HTTP a cluster specifici.

### xDS API — Configurazione Dinamica

Il protocollo **xDS** (x Discovery Service) e il meccanismo con cui Envoy riceve la propria configurazione dinamicamente da un control plane. Il vantaggio fondamentale rispetto alla configurazione statica e che Envoy non necessita mai di reload: la configurazione viene aggiornata a runtime senza interruzione del servizio.

Le API xDS principali sono:

| API | Nome completo | Funzione |
|-----|--------------|----------|
| **LDS** | Listener Discovery Service | Configura i listener (porte, protocolli, filter chain) |
| **RDS** | Route Discovery Service | Configura le regole di routing HTTP |
| **CDS** | Cluster Discovery Service | Configura i cluster upstream |
| **EDS** | Endpoint Discovery Service | Configura gli endpoint di ciascun cluster |
| **SDS** | Secret Discovery Service | Distribuisce certificati TLS e chiavi |
| **ECDS** | Extension Config Discovery Service | Configura estensioni e filtri personalizzati |

Il control plane (Istio, Gloo Edge, custom) implementa le API xDS e Envoy le consuma tramite gRPC streaming o REST long-polling.

```yaml
# envoy.yaml — Configurazione con xDS dinamico
node:
  id: "proxy-01"
  cluster: "web-cluster"

dynamic_resources:
  lds_config:
    api_config_source:
      api_type: GRPC
      grpc_services:
        - envoy_grpc:
            cluster_name: xds_cluster
      set_node_on_first_message_only: true
  cds_config:
    api_config_source:
      api_type: GRPC
      grpc_services:
        - envoy_grpc:
            cluster_name: xds_cluster
      set_node_on_first_message_only: true

static_resources:
  clusters:
    - name: xds_cluster
      connect_timeout: 5s
      type: STRICT_DNS
      lb_policy: ROUND_ROBIN
      typed_extension_protocol_options:
        envoy.extensions.upstreams.http.v3.HttpProtocolOptions:
          "@type": type.googleapis.com/envoy.extensions.upstreams.http.v3.HttpProtocolOptions
          explicit_http_config:
            http2_protocol_options: {}
      load_assignment:
        cluster_name: xds_cluster
        endpoints:
          - lb_endpoints:
              - endpoint:
                  address:
                    socket_address:
                      address: control-plane.internal
                      port_value: 18000
```

**Configurazione statica di base** (senza xDS, per scenari semplici):

```yaml
# envoy.yaml — Configurazione statica completa
static_resources:
  listeners:
    - name: http_listener
      address:
        socket_address:
          address: 0.0.0.0
          port_value: 8080
      filter_chains:
        - filters:
            - name: envoy.filters.network.http_connection_manager
              typed_config:
                "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
                stat_prefix: ingress_http
                codec_type: AUTO
                access_log:
                  - name: envoy.access_loggers.file
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.access_loggers.file.v3.FileAccessLog
                      path: /var/log/envoy/access.log
                      log_format:
                        json_format:
                          timestamp: "%START_TIME%"
                          method: "%REQ(:METHOD)%"
                          path: "%REQ(X-ENVOY-ORIGINAL-PATH?:PATH)%"
                          protocol: "%PROTOCOL%"
                          response_code: "%RESPONSE_CODE%"
                          response_flags: "%RESPONSE_FLAGS%"
                          upstream_host: "%UPSTREAM_HOST%"
                          duration: "%DURATION%"
                route_config:
                  name: local_route
                  virtual_hosts:
                    - name: api_service
                      domains: ["api.example.com"]
                      routes:
                        - match:
                            prefix: "/api/v1"
                          route:
                            cluster: api_v1_cluster
                            timeout: 30s
                            retry_policy:
                              retry_on: "5xx,connect-failure,refused-stream"
                              num_retries: 3
                              per_try_timeout: 10s
                        - match:
                            prefix: "/api/v2"
                          route:
                            cluster: api_v2_cluster
                http_filters:
                  - name: envoy.filters.http.router
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.filters.http.router.v3.Router

  clusters:
    - name: api_v1_cluster
      connect_timeout: 5s
      type: STRICT_DNS
      lb_policy: LEAST_REQUEST
      health_checks:
        - timeout: 3s
          interval: 10s
          unhealthy_threshold: 3
          healthy_threshold: 2
          http_health_check:
            path: /healthz
      load_assignment:
        cluster_name: api_v1_cluster
        endpoints:
          - lb_endpoints:
              - endpoint:
                  address:
                    socket_address:
                      address: 10.0.1.10
                      port_value: 8080
              - endpoint:
                  address:
                    socket_address:
                      address: 10.0.1.11
                      port_value: 8080
```

### Filtri Envoy

I filtri sono il meccanismo di estensibilita principale di Envoy. Si dividono in filtri di rete (L3/L4) e filtri HTTP (L7).

**Filtri di rete notevoli**:
- `envoy.filters.network.tcp_proxy` — proxy TCP passthrough
- `envoy.filters.network.http_connection_manager` — gestione connessioni HTTP (contiene la filter chain HTTP)
- `envoy.filters.network.ext_authz` — autorizzazione esterna a livello di rete

**Filtri HTTP notevoli**:
- `envoy.filters.http.router` — routing HTTP (sempre presente, ultimo nella catena)
- `envoy.filters.http.ext_authz` — autorizzazione esterna HTTP (chiama un servizio gRPC o HTTP per verificare l'autorizzazione)
- `envoy.filters.http.rate_limit` — rate limiting esterno (chiama un servizio conforme all'API di rate limiting di Envoy)
- `envoy.filters.http.fault` — iniezione di fault (latenza, errori) per chaos engineering
- `envoy.filters.http.cors` — gestione CORS
- `envoy.filters.http.compressor` — compressione gzip/brotli
- `envoy.filters.http.lua` — esecuzione di script Lua inline
- `envoy.filters.http.wasm` — esecuzione di moduli WebAssembly per estensioni personalizzate

**Circuit breaking** — Envoy implementa circuit breaking a livello di cluster per prevenire cascade failure:

```yaml
clusters:
  - name: api_cluster
    circuit_breakers:
      thresholds:
        - priority: DEFAULT
          max_connections: 1024
          max_pending_requests: 1024
          max_requests: 1024
          max_retries: 3
          track_remaining: true
        - priority: HIGH
          max_connections: 2048
          max_pending_requests: 2048
          max_requests: 2048
```

**Outlier detection** — rimozione automatica degli endpoint che mostrano pattern di errore anomali:

```yaml
clusters:
  - name: api_cluster
    outlier_detection:
      consecutive_5xx: 5                  # Errori 5xx consecutivi prima dell'eject
      interval: 10s                        # Intervallo di valutazione
      base_ejection_time: 30s              # Durata minima dell'ejection
      max_ejection_percent: 50             # Max % di endpoint ejected
      enforcing_consecutive_5xx: 100       # % di probabilita di ejection
      success_rate_minimum_hosts: 3        # Minimo host per calcolo success rate
      success_rate_stdev_factor: 1900      # Deviazione standard per la soglia
```

### Osservabilita in Envoy

Envoy fornisce osservabilita nativa a tre livelli: metriche, tracing distribuito e access log strutturati.

**Metriche**: Envoy espone metriche Prometheus su un endpoint admin dedicato. Le metriche coprono listener, cluster, upstream, downstream, HTTP, circuit breaker e outlier detection.

```yaml
admin:
  address:
    socket_address:
      address: 0.0.0.0
      port_value: 9901

# Metriche chiave da monitorare:
# envoy_cluster_upstream_rq_total — richieste totali per cluster
# envoy_cluster_upstream_rq_xx — richieste per classe di status (2xx, 4xx, 5xx)
# envoy_cluster_upstream_rq_time — latenza delle richieste upstream
# envoy_cluster_membership_healthy — endpoint healthy nel cluster
# envoy_cluster_circuit_breakers_default_cx_open — circuit breaker aperto
# envoy_cluster_outlier_detection_ejections_active — endpoint ejected
# envoy_http_downstream_rq_total — richieste downstream totali
```

**Tracing distribuito**: Envoy propaga automaticamente i context header per tracing distribuito (Zipkin B3, Jaeger, OpenTelemetry/W3C Trace Context).

```yaml
tracing:
  http:
    name: envoy.tracers.opentelemetry
    typed_config:
      "@type": type.googleapis.com/envoy.config.trace.v3.OpenTelemetryConfig
      grpc_service:
        envoy_grpc:
          cluster_name: otel_collector
        timeout: 1s
      service_name: "envoy-proxy"
```

---

## 13. Confronto Avanzato degli Algoritmi di Bilanciamento

La scelta dell'algoritmo di bilanciamento ha un impatto significativo sulla distribuzione del carico, sulla latenza e sulla resilienza dell'architettura. Questa sezione approfondisce i criteri di scelta con analisi comparativa dettagliata.

### Matrice di Confronto Dettagliata

| Algoritmo | Distribuzione Uniforme | Sensibilita al Carico | Failover | Session Affinity | Complessita | Caso d'Uso Ideale |
|-----------|----------------------|----------------------|----------|-----------------|-------------|-------------------|
| Round-Robin | Alta (con server omogenei) | Nessuna | Nativo | No | Minima | Server omogenei, richieste uniformi |
| Weighted RR | Configurabile | Nessuna (statica) | Nativo | No | Bassa | Server eterogenei con capacita nota |
| Least Connections | Alta (adattiva) | Alta | Nativo | No | Media | Richieste a durata variabile |
| Weighted Least Conn | Ottima | Alta | Nativo | No | Media | Server eterogenei, carico variabile |
| IP Hash | Variabile | Nessuna | Limitato | Si (IP) | Bassa | Session persistence senza cookie |
| Consistent Hash | Variabile | Nessuna | Ottimo | Si | Alta | Cache distribuita, session senza cookie |
| Least Time (Nginx Plus) | Ottima | Molto alta | Nativo | No | Alta | Latenza minima, server eterogenei |
| Random Two Choices | Alta | Media | Nativo | No | Bassa | Grandi cluster, semplicita |
| Maglev (Envoy) | Alta | Nessuna | Eccellente | Si (hash) | Molto alta | Google-scale, consistenza hash superiore |
| Ring Hash (Envoy) | Variabile | Nessuna | Buono | Si (hash) | Alta | Cache distribuita in Envoy |

### Quando Usare Quale Algoritmo

**Round-Robin e Weighted Round-Robin**: punto di partenza predefinito. Adatto alla maggior parte degli scenari in cui i server hanno capacita simile e le richieste hanno un costo computazionale prevedibile. Il weighted e preferibile quando si mescolano generazioni hardware diverse (es. c5.xlarge e c6g.2xlarge sullo stesso backend pool).

**Least Connections**: preferire quando le richieste hanno durata altamente variabile (es. API che gestisce sia query rapide che report complessi). L'algoritmo si adatta automaticamente, inviando piu richieste ai server che le completano piu rapidamente. Attenzione: con server molto veloci, puo degenerare in round-robin perche il conteggio connessioni oscilla troppo rapidamente.

**Consistent Hashing**: essenziale per scenari di caching distribuito (es. Varnish, Redis cluster davanti al backend). Quando un nodo viene aggiunto o rimosso, solo una frazione delle chiavi viene redistribuita (1/N con N nodi), invece del 100% che si verifica con un hash tradizionale. Maglev (usato da Envoy e da Google internamente) migliora il consistent hashing standard con una distribuzione ancora piu uniforme e un lookup O(1).

**Random Two Choices (Power of 2 Choices)**: sorprendentemente efficace e sottovalutato. Seleziona casualmente due backend e sceglie quello con meno connessioni. Con overhead computazionale minimo raggiunge una distribuzione quasi ottimale (dimostrato matematicamente: il carico massimo passa da O(log N / log log N) con scelta singola a O(log log N) con due scelte). Ideale per cluster con centinaia di nodi dove il costo di mantenere un contatore di connessioni globale diventa significativo.

---

## 14. WebSocket, HTTP/2 e gRPC Load Balancing

### Sfide del Bilanciamento WebSocket

Il protocollo WebSocket introduce sfide specifiche per il load balancing a causa della natura persistente e stateful delle connessioni.

**Upgrade HTTP**: la connessione WebSocket inizia come una richiesta HTTP con header `Upgrade: websocket` e `Connection: Upgrade`. Il load balancer L7 deve riconoscere e propagare questo upgrade, mantenendo la connessione bidirezionale aperta.

**Connection pinning**: una volta stabilita, la connessione WebSocket resta legata a un singolo backend per tutta la sua durata (che puo essere di ore o giorni). Questo rende il bilanciamento inefficace dopo la fase iniziale di connessione: i nuovi server aggiunti con auto-scaling non ricevono traffico finche le connessioni esistenti non vengono chiuse e ristabilite.

**Timeout estesi**: i timeout standard del proxy (30-60 secondi) non sono adeguati per WebSocket. Configurare `proxy_read_timeout` (Nginx) o `timeout tunnel` (HAProxy) a valori elevati (3600s o piu).

```nginx
# Nginx — Configurazione WebSocket completa
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

upstream websocket_backend {
    ip_hash;    # Affinita per riconnessioni rapide
    server 10.0.5.10:8080;
    server 10.0.5.11:8080;
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

        # Timeout estesi per connessioni long-lived
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;

        # Disabilitare il buffering per messaggi in tempo reale
        proxy_buffering off;
        proxy_cache off;
    }
}
```

```
# HAProxy — WebSocket con timeout tunnel
backend backend_websocket
    mode http
    balance source
    option httpchk GET /ws/health HTTP/1.1\r\nHost:\ ws.example.com

    # Il timeout tunnel si applica dopo l'upgrade WebSocket
    timeout tunnel 86400s
    timeout server  86400s

    # Opzione per non chiudere la connessione server-side
    option http-server-close
    http-request set-header Connection "Upgrade"
    http-request set-header Upgrade "websocket"

    server ws-1 10.0.5.10:8080 check
    server ws-2 10.0.5.11:8080 check
```

### Bilanciamento HTTP/2

HTTP/2 introduce il multiplexing di stream su una singola connessione TCP. Questo crea un problema specifico per il load balancing: se il client apre una sola connessione HTTP/2 verso il load balancer, tutte le richieste multiplex passano su quella connessione. Se il load balancer a sua volta apre una sola connessione HTTP/2 verso ciascun backend, il bilanciamento diventa inefficace perche tutto il traffico di un client finisce su un solo backend.

**Strategia raccomandata**: terminare HTTP/2 al load balancer e usare HTTP/1.1 con connection pooling verso i backend. Ogni richiesta HTTP/1.1 puo essere instradata indipendentemente a un backend diverso.

```nginx
# Nginx — HTTP/2 frontend, HTTP/1.1 backend
server {
    listen 443 ssl;
    http2 on;    # Accetta HTTP/2 dai client

    location / {
        proxy_pass http://api_backend;
        proxy_http_version 1.1;          # HTTP/1.1 verso il backend
        proxy_set_header Connection "";  # Keepalive pool
    }
}
```

Se e necessario mantenere HTTP/2 end-to-end (es. per gRPC), il load balancer deve operare a livello di stream HTTP/2, non di connessione. Envoy supporta nativamente questo scenario. HAProxy dalla versione 2.0+ supporta HTTP/2 sia in frontend che in backend.

### Bilanciamento gRPC

gRPC utilizza HTTP/2 come trasporto, ereditando il problema del multiplexing. Inoltre, le connessioni gRPC sono tipicamente persistenti e long-lived, aggravando il problema del connection pinning.

**Bilanciamento L7 per gRPC**: il load balancer deve ispezionare i frame HTTP/2 e bilanciare a livello di singola RPC call, non di connessione TCP.

```nginx
# Nginx — gRPC load balancing
upstream grpc_services {
    least_conn;
    server 10.0.4.10:50051;
    server 10.0.4.11:50051;
    server 10.0.4.12:50051;
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name grpc.example.com;

    ssl_certificate     /etc/nginx/certs/grpc.pem;
    ssl_certificate_key /etc/nginx/certs/grpc-key.pem;

    location / {
        grpc_pass grpc://grpc_services;

        # Timeout per streaming lungo
        grpc_read_timeout 3600s;
        grpc_send_timeout 3600s;

        # Header per il tracing
        grpc_set_header X-Request-ID $request_id;

        # Error handling gRPC-specifico
        error_page 502 = /error502grpc;
    }

    location = /error502grpc {
        internal;
        default_type application/grpc;
        add_header grpc-status 14;
        add_header grpc-message "upstream unavailable";
        return 204;
    }
}
```

**Client-side load balancing per gRPC**: in architetture service mesh, il bilanciamento gRPC viene spesso implementato lato client tramite un sidecar proxy (Envoy) o direttamente nel client gRPC con un resolver personalizzato. La libreria gRPC supporta nativamente i resolver `dns:///` e `xds:///` per la discovery degli endpoint.

```yaml
# Envoy — gRPC load balancing con HTTP/2 end-to-end
clusters:
  - name: grpc_service
    connect_timeout: 5s
    type: STRICT_DNS
    lb_policy: ROUND_ROBIN
    typed_extension_protocol_options:
      envoy.extensions.upstreams.http.v3.HttpProtocolOptions:
        "@type": type.googleapis.com/envoy.extensions.upstreams.http.v3.HttpProtocolOptions
        explicit_http_config:
          http2_protocol_options:
            max_concurrent_streams: 100
    health_checks:
      - timeout: 3s
        interval: 10s
        grpc_health_check: {}
    load_assignment:
      cluster_name: grpc_service
      endpoints:
        - lb_endpoints:
            - endpoint:
                address:
                  socket_address:
                    address: grpc-service.internal
                    port_value: 50051
```

### Connection Draining per Protocolli Persistenti

La procedura di connection draining per WebSocket e gRPC richiede attenzione particolare perche le connessioni sono long-lived e la chiusura forzata causa errori visibili agli utenti.

**Strategia graduale**:
1. Segnalare al backend l'intenzione di drain (es. via signal SIGTERM)
2. Il backend smette di accettare nuove stream gRPC o nuove connessioni WebSocket
3. Le stream/connessioni esistenti vengono completate o chiuse gracefully con un GoAway frame (HTTP/2) o un Close frame (WebSocket)
4. Dopo un timeout configurabile (deregistration delay), il load balancer rimuove il backend

```bash
# Procedura con HAProxy
# 1. Drain mode: accetta solo connessioni gia esistenti
echo "set server backend_ws/ws-1 state drain" | socat stdio /var/run/haproxy/admin.sock

# 2. Monitorare le connessioni residue
watch -n 1 'echo "show servers state" | socat stdio /var/run/haproxy/admin.sock | grep ws-1'

# 3. Dopo che le connessioni si esauriscono (o dopo timeout)
echo "set server backend_ws/ws-1 state maint" | socat stdio /var/run/haproxy/admin.sock
```

---

## 15. Global Server Load Balancing (GSLB)

### Concetti Fondamentali

Il GSLB estende il load balancing oltre i confini di un singolo datacenter o regione, distribuendo il traffico su scala globale. A differenza del load balancing locale (che opera su connessioni TCP o richieste HTTP), il GSLB opera prevalentemente a livello DNS o a livello di rete IP (anycast).

**Obiettivi del GSLB**:
- Ridurre la latenza per gli utenti indirizzandoli al datacenter piu vicino
- Garantire disponibilita durante il failover tra regioni
- Distribuire il carico tra datacenter in base alla capacita
- Conformarsi ai requisiti di data residency (GDPR, SOC2)

### Approcci GSLB

**DNS-based GSLB**: il sistema GSLB intercede nella risoluzione DNS e restituisce l'indirizzo IP del datacenter ottimale in base a criteri configurati. E l'approccio piu comune e supportato da tutti i cloud provider (Route 53, Azure Traffic Manager, GCP Cloud DNS).

Criteri di decisione:
- **Geoproximity**: basato sulla posizione geografica del resolver DNS del client (impreciso se il client usa un resolver distante, es. Google 8.8.8.8)
- **Latency-based**: il sistema GSLB misura attivamente la latenza tra i propri PoP e i datacenter backend, scegliendo quello con latenza minore
- **Weighted**: distribuzione percentuale statica (es. 70% EU, 30% US)
- **Health-aware**: il GSLB verifica la salute dei datacenter e rimuove quelli non disponibili dalla rotazione DNS
- **Failover**: primario/secondario con switch automatico

```bash
# AWS Route 53 — Latency-based routing con health check
aws route53 create-health-check \
  --caller-reference "eu-west-health-$(date +%s)" \
  --health-check-config '{
    "Type": "HTTPS",
    "ResourcePath": "/healthz",
    "FullyQualifiedDomainName": "eu-api.example.com",
    "Port": 443,
    "RequestInterval": 10,
    "FailureThreshold": 3,
    "EnableSNI": true
  }'

# Record latency-based per EU
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890 \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.example.com",
        "Type": "A",
        "SetIdentifier": "eu-west",
        "Region": "eu-west-1",
        "AliasTarget": {
          "HostedZoneId": "Z32O12XQLNTSW2",
          "DNSName": "eu-alb-123456.eu-west-1.elb.amazonaws.com",
          "EvaluateTargetHealth": true
        },
        "HealthCheckId": "eu-health-check-id"
      }
    }]
  }'
```

**Anycast GSLB**: lo stesso indirizzo IP viene annunciato da piu datacenter tramite BGP. Il routing Internet dirige automaticamente i pacchetti al datacenter topologicamente piu vicino. Non richiede manipolazione DNS e opera a livello di rete, con failover quasi istantaneo (il tempo di convergenza BGP, tipicamente 1-3 secondi).

Vantaggi:
- Failover trasparente senza dipendenza dal TTL DNS
- Latenza ottimale grazie al routing nativo di Internet
- Resilienza DDoS (il traffico viene assorbito dal PoP piu vicino)

Svantaggi:
- Richiede l'uso di un proprio Autonomous System Number (ASN) o di un CDN che lo fornisce
- Il routing BGP non e deterministico: cambiamenti nelle rotte possono spostare il traffico tra PoP in modo imprevedibile
- Non adatto per connessioni TCP long-lived (un rerouting BGP puo causare reset della connessione)

**Application-level GSLB**: i load balancer globali dei cloud provider (Azure Front Door, GCP External HTTP(S) Load Balancer, AWS Global Accelerator) operano a livello applicativo. Mantengono PoP distribuiti globalmente che terminano la connessione TCP/TLS del client e inoltrano la richiesta al backend ottimale tramite la rete backbone del provider. Questo approccio combina i vantaggi del DNS-based (intelligenza nella selezione del backend) e dell'anycast (bassa latenza di primo miglio).

### Failover GSLB e TTL DNS

Il TTL DNS e il fattore critico per la velocita di failover nel GSLB DNS-based. Un TTL basso (es. 30 secondi) consente failover rapido ma aumenta il volume di query DNS. Un TTL alto (es. 300 secondi) riduce il traffico DNS ma rallenta il failover perche i resolver e i client continuano a usare l'IP cached del datacenter fallito.

Raccomandazione: TTL tra 30 e 60 secondi per record con failover critico. Per record stabili senza requisiti di failover rapido, TTL tra 300 e 3600 secondi.

```bash
# Verificare il TTL effettivo come visto dai client
dig +norecurse api.example.com @8.8.8.8

# Monitorare il failover DNS
watch -n 5 'dig +short api.example.com @1.1.1.1'
```

---

## 16. Pattern di Alta Disponibilita Avanzati

### VRRP e Keepalived — Deep-Dive

VRRP (Virtual Router Redundancy Protocol) e il protocollo standard per l'implementazione di failover active-passive tra load balancer. Keepalived e l'implementazione piu diffusa su Linux.

**Funzionamento**: due o piu nodi condividono un Virtual IP (VIP). Il nodo MASTER risponde al VIP; gli altri sono in stato BACKUP. I nodi si scambiano advertisement VRRP (multicast 224.0.0.18) a intervalli regolari (tipicamente 1 secondo). Se il BACKUP non riceve advertisement dal MASTER entro un timeout configurato, assume il ruolo di MASTER e prende il VIP tramite ARP gratuito.

```bash
# /etc/keepalived/keepalived.conf — Nodo MASTER

vrrp_script check_haproxy {
    script "/usr/bin/killall -0 haproxy"   # Verifica che HAProxy sia in esecuzione
    interval 2                              # Controlla ogni 2 secondi
    weight -20                              # Penalita se il check fallisce
    fall 3                                  # Numero di fallimenti prima di marcare down
    rise 2                                  # Numero di successi prima di marcare up
}

vrrp_instance VI_1 {
    state MASTER
    interface eth0
    virtual_router_id 51
    priority 100                           # Priorita (piu alta = preferito come MASTER)
    advert_int 1                           # Intervallo di advertisement (secondi)
    nopreempt                              # Non riprendere il ruolo MASTER automaticamente

    authentication {
        auth_type PASS
        auth_pass SecureVRRP!
    }

    virtual_ipaddress {
        192.168.1.100/24 dev eth0          # VIP
    }

    track_script {
        check_haproxy
    }

    notify_master "/etc/keepalived/scripts/notify-master.sh"
    notify_backup "/etc/keepalived/scripts/notify-backup.sh"
    notify_fault  "/etc/keepalived/scripts/notify-fault.sh"
}
```

```bash
# /etc/keepalived/keepalived.conf — Nodo BACKUP
vrrp_script check_haproxy {
    script "/usr/bin/killall -0 haproxy"
    interval 2
    weight -20
    fall 3
    rise 2
}

vrrp_instance VI_1 {
    state BACKUP
    interface eth0
    virtual_router_id 51
    priority 90                            # Priorita inferiore al MASTER
    advert_int 1

    authentication {
        auth_type PASS
        auth_pass SecureVRRP!
    }

    virtual_ipaddress {
        192.168.1.100/24 dev eth0
    }

    track_script {
        check_haproxy
    }
}
```

### Split-Brain e Prevenzione

Lo **split-brain** si verifica quando i due nodi VRRP perdono la comunicazione tra loro (ma sono entrambi operativi). Entrambi assumono di essere il MASTER e rispondono allo stesso VIP, causando conflitti ARP e routing imprevedibile.

**Strategie di mitigazione**:

1. **Fencing**: uno script di fencing verifica la raggiungibilita della rete esterna (es. gateway, DNS resolver) prima di assumere il ruolo MASTER. Se il nodo non raggiunge la rete esterna, si mette in stato FAULT anziche tentare di diventare MASTER.

```bash
# /etc/keepalived/scripts/check-network.sh
#!/bin/bash
# Verifica connettivita verso risorse esterne
TARGETS="8.8.8.8 1.1.1.1 192.168.1.1"
FAILED=0
for target in $TARGETS; do
    ping -c 1 -W 1 "$target" > /dev/null 2>&1 || FAILED=$((FAILED + 1))
done

# Se piu della meta dei target non e raggiungibile, considerarsi isolato
if [ "$FAILED" -gt $(($(echo $TARGETS | wc -w) / 2)) ]; then
    exit 1
fi
exit 0
```

2. **Unicast VRRP**: usare unicast invece di multicast per gli advertisement VRRP. In ambienti cloud dove il multicast non e supportato, questo e obbligatorio.

```
vrrp_instance VI_1 {
    state MASTER
    interface eth0
    virtual_router_id 51
    priority 100

    unicast_src_ip 10.0.1.10
    unicast_peer {
        10.0.1.11
        10.0.1.12
    }
}
```

3. **nopreempt**: impedisce al nodo con priorita piu alta di riprendere automaticamente il ruolo MASTER dopo un failover. Il failback deve essere eseguito manualmente per evitare flip-flap.

### Active-Active con ECMP

L'architettura active-active distribuisce il traffico su piu load balancer contemporaneamente, massimizzando l'utilizzo delle risorse. A differenza dell'active-passive, non c'e capacita sprecata in standby.

**ECMP (Equal-Cost Multi-Path)**: il router upstream mantiene piu next-hop verso lo stesso VIP e distribuisce i pacchetti tra di essi. La distribuzione avviene tipicamente tramite hash della tupla 5 (src IP, dst IP, src port, dst port, protocollo), garantendo che i pacchetti della stessa connessione TCP raggiungano sempre lo stesso load balancer.

**DSR (Direct Server Return)**: i backend rispondono direttamente al client senza passare attraverso il load balancer per il traffico di ritorno. Riduce drasticamente il carico sul load balancer (che gestisce solo il traffico in ingresso) ma richiede configurazione specifica a livello di rete.

---

## 17. Monitoring Avanzato dei Load Balancer

### Dashboard Design e Metriche Essenziali

Un dashboard efficace per il monitoring dei load balancer deve organizzare le metriche in tre livelli: panoramica globale, dettaglio per servizio e drill-down per singolo backend.

**Livello 1 — Panoramica Globale**:
- Throughput totale (RPS aggregato su tutti i frontend)
- Latenza p50, p95, p99 aggregata
- Error rate globale (5xx / totale)
- Connessioni attive totali
- Rapporto backend healthy / totali
- Utilizzo CPU e memoria del load balancer

**Livello 2 — Dettaglio per Servizio**:
- RPS per backend/servizio
- Latenza per servizio (distinguere latenza del proxy dalla latenza del backend)
- Error rate per servizio
- Queue depth (HAProxy) per servizio
- Connessioni per backend

**Livello 3 — Drill-Down per Backend**:
- Stato health check per ogni backend
- Connessioni attive per backend
- Byte in/out per backend
- Latenza per singolo backend
- Errori per singolo backend

### Alerting Rules con Prometheus

```yaml
# prometheus-rules.yml — Regole di alerting per load balancer

groups:
  - name: load_balancer_alerts
    rules:
      # Alta latenza p99
      - alert: HighLatencyP99
        expr: |
          histogram_quantile(0.99,
            rate(haproxy_backend_http_response_time_seconds_bucket[5m])
          ) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Latenza p99 superiore a 2s sul backend {{ $labels.proxy }}"
          description: "La latenza p99 e {{ $value }}s, superiore alla soglia di 2s per 5 minuti"

      # Error rate elevato
      - alert: HighErrorRate
        expr: |
          rate(haproxy_backend_http_responses_total{code="5xx"}[5m])
          /
          rate(haproxy_backend_http_responses_total[5m])
          > 0.05
        for: 3m
        labels:
          severity: critical
        annotations:
          summary: "Error rate 5xx superiore al 5% su {{ $labels.proxy }}"

      # Backend down
      - alert: BackendDown
        expr: haproxy_backend_active_servers < 2
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Backend {{ $labels.proxy }} ha meno di 2 server attivi"

      # Connessioni in coda
      - alert: HighQueueDepth
        expr: haproxy_backend_current_queue > 10
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Coda di connessioni elevata su {{ $labels.proxy }}: {{ $value }}"

      # CPU del load balancer
      - alert: HighCPUUsage
        expr: |
          100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle",instance=~"haproxy.*"}[5m])) * 100)
          > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU del load balancer {{ $labels.instance }} superiore all'80%"

      # Circuit breaker aperto (Envoy)
      - alert: CircuitBreakerOpen
        expr: envoy_cluster_circuit_breakers_default_cx_open > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Circuit breaker aperto per il cluster {{ $labels.cluster_name }}"

      # Outlier ejection attiva (Envoy)
      - alert: OutlierEjectionActive
        expr: envoy_cluster_outlier_detection_ejections_active > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "{{ $value }} endpoint ejected dal cluster {{ $labels.cluster_name }}"

      # Traffico asimmetrico tra backend
      - alert: TrafficImbalance
        expr: |
          (
            max(rate(haproxy_server_http_responses_total[5m])) by (proxy)
            /
            avg(rate(haproxy_server_http_responses_total[5m])) by (proxy)
          ) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Distribuzione traffico non uniforme su {{ $labels.proxy }}"

      # Certificato TLS in scadenza
      - alert: TLSCertificateExpiring
        expr: |
          (probe_ssl_earliest_cert_expiry - time()) / 86400 < 14
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Certificato TLS di {{ $labels.instance }} scade tra {{ $value }} giorni"

      # Nginx — Connessioni dropping
      - alert: NginxConnectionsDropping
        expr: |
          rate(nginx_connections_accepted[5m]) - rate(nginx_connections_handled[5m]) > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Nginx sta scartando connessioni su {{ $labels.instance }}"
```

### Grafana Dashboard Queries (PromQL)

```
# HAProxy — Throughput per backend
rate(haproxy_backend_http_responses_total[5m])

# HAProxy — Latenza media per backend
rate(haproxy_backend_response_time_average_seconds[5m])

# HAProxy — Error rate per backend
sum(rate(haproxy_backend_http_responses_total{code="5xx"}[5m])) by (proxy)
/
sum(rate(haproxy_backend_http_responses_total[5m])) by (proxy)

# Nginx — Request rate
rate(nginx_http_requests_total[5m])

# Nginx — Active connections
nginx_connections_active

# Traefik — Request rate per servizio
rate(traefik_service_requests_total[5m])

# Traefik — Latenza p99 per servizio
histogram_quantile(0.99, rate(traefik_service_request_duration_seconds_bucket[5m]))

# Envoy — Upstream request time p95
histogram_quantile(0.95, rate(envoy_cluster_upstream_rq_time_bucket[5m]))

# Envoy — Success rate per cluster
sum(rate(envoy_cluster_upstream_rq_xx{envoy_response_code_class="2"}[5m])) by (cluster_name)
/
sum(rate(envoy_cluster_upstream_rq_total[5m])) by (cluster_name)
```

### Log Analysis Automatizzata

Per volumi elevati di traffico (>100K RPS), l'analisi manuale dei log non e praticabile. Strategie raccomandate:

1. **Log strutturati in JSON**: tutti i load balancer devono produrre log in formato JSON per facilitare il parsing automatico (Loki, Elasticsearch, Splunk).

2. **Sampling intelligente**: campionare il 100% dei log di errore (4xx, 5xx), il 100% dei log con latenza superiore alla soglia (es. >1s) e una percentuale configurabile dei log di successo (es. 10%).

3. **Correlazione tramite Request-ID**: propagare un header `X-Request-ID` dal load balancer ai backend per correlare i log lungo l'intera catena di servizi.

```bash
# Generare X-Request-ID se non presente (Nginx)
# map $http_x_request_id $request_id_value {
#     default $http_x_request_id;
#     ""      $request_id;
# }
# proxy_set_header X-Request-ID $request_id_value;

# HAProxy — Generare unique-id
frontend https-in
    unique-id-format %{+X}o\ %ci:%cp_%fi:%fp_%Ts_%rt:%pid
    unique-id-header X-Request-ID
    http-request set-header X-Request-ID %[unique-id]
```

4. **Anomaly detection**: configurare alert basati su deviazioni statistiche (es. latenza >2 deviazioni standard sopra la media mobile) piuttosto che soglie fisse. Questo riduce i falsi positivi e cattura degradazioni graduali.

---

## Esercizi

1. **Configurazione HAProxy L7** — Installare HAProxy e configurare un frontend HTTP che distribuisca il traffico su 3 backend server (container Docker con Nginx che servono pagine diverse). Implementare: health check HTTP (path `/health`, intervallo 5s), sticky session basate su cookie e rate limiting a 100 req/s per IP. Verificare con `curl` e `ab` (Apache Benchmark).

2. **Nginx come reverse proxy con TLS** — Configurare Nginx come reverse proxy davanti a un'applicazione web. Implementare TLS termination con certificati Let's Encrypt (o self-signed per lab), redirect HTTP→HTTPS, header di sicurezza (HSTS, X-Content-Type-Options) e caching statico. Misurare la latenza aggiunta dal proxy con `wrk`.

3. **Traefik con service discovery** — Deployare Traefik su Docker Compose con provider Docker abilitato. Aggiungere 3 servizi con label Traefik per routing automatico basato su hostname. Implementare middleware: rate limiting, circuit breaker, retry. Scalare un servizio da 1 a 5 repliche e verificare il bilanciamento round-robin.

4. **Architettura multi-tier con cloud LB** — Progettare (su carta o Terraform) un'architettura a 3 tier su AWS: NLB (L4) per traffico TCP ad alto throughput → ALB (L7) per routing basato su path e hostname → target group con auto-scaling. Documentare le differenze di costo, funzionalità e limiti tra NLB e ALB.

5. **Chaos engineering sul load balancer** — Con un setup HAProxy o Nginx attivo, simulare failure scenario: terminare un backend server e verificare il failover automatico, saturare un backend con traffico e osservare il circuit breaking, iniettare latenza artificiale e verificare il timeout del health check. Documentare i tempi di recovery.

---

## Letture e Riferimenti

### Documentazione ufficiale

- HAProxy Documentation: <https://www.haproxy.com/documentation/> (consultato: 2026-05-24)
- Nginx Documentation: <https://nginx.org/en/docs/> (consultato: 2026-05-24)
- Traefik Documentation: <https://doc.traefik.io/traefik/> (consultato: 2026-05-24)
- AWS Elastic Load Balancing: <https://docs.aws.amazon.com/elasticloadbalancing/> (consultato: 2026-05-24)
- GCP Cloud Load Balancing: <https://cloud.google.com/load-balancing/docs> (consultato: 2026-05-24)
- Envoy Proxy — Load balancing: <https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/load_balancing/overview> (consultato: 2026-05-24)

### Libri

- DeJonghe, D. — *NGINX Cookbook* (2a ed.), O'Reilly, 2022
- Willy Tarreau et al. — *The HAProxy Documentation* (reference), HAProxy Technologies, 2024
- Turnbull, J. — *The Art of Monitoring*, Turnbull Press, 2016

---

## Riferimenti Incrociati

| Modulo | Titolo | Relazione con questo modulo |
|--------|--------|-----------------------------|
| [01-cloud-aws](01-cloud-aws.md) | Cloud AWS | ALB, NLB e Global Accelerator |
| [03-cloud-gcp](03-cloud-gcp.md) | Cloud GCP | GCP HTTP(S) Load Balancer e Network LB |
| [05-kubernetes](05-kubernetes.md) | Kubernetes | Ingress controller e Service type LoadBalancer |
| [09-service-mesh](09-service-mesh.md) | Service Mesh | Load balancing L7 nel data plane Envoy |
| [13-sicurezza-piattaforme](13-sicurezza-piattaforme.md) | Sicurezza Piattaforme | TLS termination, WAF e DDoS mitigation |
| [16-api-gateway](16-api-gateway.md) | API Gateway | Differenze tra reverse proxy, LB e API gateway |

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **Load balancer** | Componente di rete che distribuisce il traffico in ingresso su più server backend per garantire disponibilità e performance |
| **Reverse proxy** | Server intermedio che riceve le richieste dai client e le inoltra ai backend, aggiungendo funzionalità come caching, TLS e compressione |
| **L4 load balancing** | Bilanciamento a livello trasporto (TCP/UDP) basato su IP e porta, senza ispezione del contenuto applicativo |
| **L7 load balancing** | Bilanciamento a livello applicativo (HTTP/HTTPS) con capacità di routing basato su URL, header, cookie |
| **Health check** | Verifica periodica dello stato di salute dei backend server; può essere TCP (porta aperta), HTTP (status code) o applicativo (endpoint dedicato) |
| **TLS termination** | Processo di decifratura del traffico TLS/SSL al livello del load balancer o reverse proxy, inoltrando traffico in chiaro ai backend |
| **Sticky session** | Meccanismo che lega un client a un backend specifico per la durata della sessione, tipicamente tramite cookie o IP hash |
| **Round-robin** | Algoritmo di bilanciamento che distribuisce le richieste sequenzialmente tra i backend disponibili |
| **Least connections** | Algoritmo di bilanciamento che invia la richiesta al backend con il minor numero di connessioni attive |
| **Rate limiting** | Controllo del numero massimo di richieste per unità di tempo da un singolo client o IP, proteggendo da abuso e DDoS |
| **Circuit breaker** | Pattern che interrompe temporaneamente le richieste verso un backend in errore per permettere il recovery e prevenire cascade failure |
| **ECMP** | Equal-Cost Multi-Path routing — tecnica di rete che distribuisce il traffico su più percorsi a costo uguale verso la stessa destinazione |
| **Ingress controller** | Componente Kubernetes che implementa le regole Ingress utilizzando un reverse proxy (Nginx, Traefik, HAProxy) |
| **Connection draining** | Processo di chiusura graduale delle connessioni esistenti su un backend prima di rimuoverlo dal pool, evitando errori per richieste in corso |
| **SNI** | Server Name Indication — estensione TLS che consente al client di specificare l'hostname durante l'handshake, permettendo hosting multiplo su un singolo IP |
| **xDS** | Famiglia di API di discovery (LDS, RDS, CDS, EDS, SDS) usate da Envoy per ricevere configurazione dinamica da un control plane senza reload |
| **GSLB** | Global Server Load Balancing — distribuzione del traffico su scala globale tra datacenter e regioni, tipicamente via DNS o anycast |
| **VRRP** | Virtual Router Redundancy Protocol — protocollo che consente a piu nodi di condividere un Virtual IP per failover automatico |
| **Outlier detection** | Meccanismo (tipico di Envoy) che rileva endpoint con pattern di errore anomali e li rimuove temporaneamente dal pool di bilanciamento |
| **Stick table** | Tabella in memoria di HAProxy per tracking di sessioni, conteggi e rate per IP/utente, replicabile tra nodi peer |
| **DSR** | Direct Server Return — tecnica in cui il backend risponde direttamente al client senza passare dal load balancer per il traffico di ritorno |
- **Encryption**: per PCI-DSS, i dati dei titolari di carta devono essere cifrati in transito. SSL re-encryption (non solo termination) e richiesto se il tratto LB-backend attraversa una rete non fidata.
