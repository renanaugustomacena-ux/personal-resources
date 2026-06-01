---
corso: "Gestione Piattaforme e DevOps"
fase: "4 — Osservabilità e Networking"
modulo: 9
titolo: "Service Mesh"
versione: "Istio 1.24 / Cilium 1.16 / Linkerd 2.x / Envoy 1.31"
livello: "Avanzato"
prerequisiti: ["05-kubernetes", "08-monitoring-observability", "10-load-balancer-reverse-proxy"]
obiettivi:
  - "Comprendere l'architettura control plane / data plane e il ruolo di Envoy proxy"
  - "Configurare Istio con traffic management, mTLS automatico e authorization policies"
  - "Valutare le alternative: Cilium eBPF (sidecarless), Linkerd (lightweight), ambient mesh"
  - "Implementare canary deployment, circuit breaking e fault injection tramite service mesh"
  - "Monitorare il service mesh con metriche Istio/Envoy integrate in Prometheus e Grafana"
tag: [service-mesh, istio, cilium, linkerd, envoy, mtls, traffic-management, ebpf]
---

# Service Mesh — Documentazione Completa

> **Modulo 09** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Comprendere l'architettura control plane / data plane e il ruolo di Envoy proxy
> 2. Configurare Istio con traffic management, mTLS automatico e authorization policies
> 3. Valutare le alternative: Cilium eBPF (sidecarless), Linkerd (lightweight), ambient mesh
> 4. Implementare canary deployment, circuit breaking e fault injection tramite service mesh
> 5. Monitorare il service mesh con metriche Istio/Envoy integrate in Prometheus e Grafana
>
> **Prerequisiti:** [Kubernetes](05-kubernetes.md) · [Monitoring e Observability](08-monitoring-observability.md) · [Load Balancer e Reverse Proxy](10-load-balancer-reverse-proxy.md)
> **Tempo stimato:** 8-10 ore · **Livello:** Avanzato

## Idee guida

1. **Service mesh = mTLS + observability + traffic management.** Tre features in uno.
2. **Istio sidecar vs Cilium eBPF.** Cilium piu leggero, no sidecar.
3. **Service mesh complica.** Use solo se 10+ microservizi; meno = overengineering.
4. **mTLS automatico = security win, ma cost CPU 5-15%.**


## Indice

1. [Panoramica e Concetti Fondamentali](#1-panoramica-e-concetti-fondamentali)
2. [Istio — Architettura](#2-istio--architettura)
3. [Istio — Traffic Management](#3-istio--traffic-management)
4. [Istio — Security](#4-istio--security)
5. [Istio — Observability](#5-istio--observability)
6. [Linkerd](#6-linkerd)
7. [Consul Connect](#7-consul-connect)
8. [Pattern Avanzati](#8-pattern-avanzati)
9. [Deployment Strategies con Service Mesh](#9-deployment-strategies-con-service-mesh)
10. [Troubleshooting](#10-troubleshooting)
11. [Best Practices](#11-best-practices)
12. [Istio Ambient Mesh — Deep Dive](#12-istio-ambient-mesh--deep-dive)
13. [Cilium Service Mesh — Architettura eBPF](#13-cilium-service-mesh--architettura-ebpf)
14. [Sicurezza Avanzata — SPIFFE, SPIRE e Zero-Trust Identity](#14-sicurezza-avanzata--spiffe-spire-e-zero-trust-identity)
15. [Gateway API Integration](#15-gateway-api-integration)
16. [Performance Impact e Benchmarks Comparativi](#16-performance-impact-e-benchmarks-comparativi)
17. [Testing del Service Mesh](#17-testing-del-service-mesh)
18. [Strategie di Migrazione](#18-strategie-di-migrazione)

---

## 1. Panoramica e Concetti Fondamentali

### Cos'e un Service Mesh e Perche Serve

Un service mesh e un layer infrastrutturale dedicato che gestisce la comunicazione service-to-service all'interno di un'architettura a microservizi. Invece di implementare la logica di rete (retry, timeout, circuit breaking, load balancing, mutual TLS) direttamente nel codice applicativo di ogni servizio, il service mesh la delega a un proxy trasparente che intercetta tutto il traffico in entrata e in uscita.

Il problema fondamentale che un service mesh risolve e la **proliferazione della logica di rete distribuita**: quando un sistema cresce da pochi servizi a centinaia, gestire manualmente le politiche di comunicazione, la sicurezza e l'osservabilita diventa insostenibile. Senza un service mesh, ogni team deve reimplementare la stessa logica di resilienza, spesso con librerie diverse e in linguaggi diversi, creando inconsistenze e punti ciechi operativi.

### Pattern Sidecar Proxy

Il pattern architetturale alla base del service mesh tradizionale e il **sidecar proxy**. Per ogni Pod Kubernetes (o istanza di servizio), viene iniettato un container aggiuntivo — il sidecar — che funge da proxy trasparente. Tutto il traffico di rete del servizio passa attraverso questo proxy prima di raggiungere la rete e viceversa.

```
┌──────────────────────────────────┐
│           Pod                    │
│  ┌──────────┐  ┌──────────────┐ │
│  │ App      │──│ Sidecar      │ │
│  │ Container│  │ Proxy (Envoy)│ │
│  └──────────┘  └──────┬───────┘ │
│                       │         │
└───────────────────────┼─────────┘
                        │
                   Rete (mesh)
```

Il sidecar proxy intercetta le connessioni tramite regole **iptables** (o eBPF nelle architetture piu recenti) che redirigono il traffico in ingresso e in uscita attraverso il proxy. L'applicazione non ha bisogno di modifiche: comunica normalmente con `localhost` o con i nomi DNS dei servizi, e il proxy gestisce tutto in modo trasparente.

### Data Plane vs Control Plane

Un service mesh si compone di due piani logici distinti:

**Data Plane** — Costituito dall'insieme di tutti i sidecar proxy distribuiti nel cluster. Gestisce direttamente il traffico: forwarding, load balancing, health checking, autenticazione, metriche. Ogni proxy opera in modo autonomo con la configurazione ricevuta dal control plane. Envoy e il proxy data plane piu diffuso.

**Control Plane** — Componente centralizzato che configura e coordina i proxy del data plane. Definisce le politiche di routing, sicurezza e osservabilita, poi le distribuisce a tutti i proxy. Non gestisce il traffico direttamente: si limita a programmare i proxy. In Istio, il control plane e rappresentato da `istiod`.

### Problemi Risolti dal Service Mesh

| Problema | Soluzione Service Mesh |
|---|---|
| **Service Discovery** | Risoluzione automatica degli endpoint, aggiornamento dinamico |
| **Load Balancing** | Algoritmi avanzati (round-robin, least connections, consistent hashing) |
| **Circuit Breaking** | Isolamento automatico di servizi degradati per prevenire cascade failure |
| **Retry e Timeout** | Politiche configurabili per classe di errore, con exponential backoff |
| **mTLS** | Crittografia e autenticazione reciproca automatica tra servizi |
| **Osservabilita** | Metriche, tracing distribuito e logging senza modifiche al codice |
| **Traffic Management** | Canary deployment, A/B testing, traffic mirroring |
| **Authorization** | Politiche di accesso granulari a livello di servizio |

### Quando Usare un Service Mesh

Un service mesh e giustificato quando:

- Il numero di microservizi supera una soglia critica (indicativamente 10-20+ servizi in produzione) e la gestione manuale della comunicazione diventa insostenibile.
- Servono requisiti stringenti di **sicurezza** (mTLS obbligatorio, zero-trust networking) imposti da normative o da policy aziendali.
- L'osservabilita end-to-end e un requisito non negoziabile e non si vogliono modificare i singoli servizi per instrumentarli.
- Si adottano strategie di deployment avanzate (canary, blue-green, traffic mirroring) che richiedono controllo granulare sul routing.
- Il sistema e **poliglotta** (servizi in Go, Java, Python, Node.js) e si vuole un layer uniforme di rete indipendente dal linguaggio.

### Quando NON Usare un Service Mesh

- **Pochi servizi** (meno di 5-10): la complessita operativa del mesh supera i benefici. Un API gateway o un service discovery semplice (Consul, CoreDNS) sono sufficienti.
- **Team piccolo senza esperienza Kubernetes avanzata**: il service mesh aggiunge un layer significativo di complessita operativa e di debugging.
- **Requisiti di latenza ultra-bassi**: ogni hop attraverso il sidecar aggiunge latenza (tipicamente 1-3ms per hop). Per sistemi HFT o real-time critici, questo overhead puo essere inaccettabile.
- **Ambienti non containerizzati**: i service mesh sono progettati per Kubernetes. Adottarli su VM tradizionali e possibile ma aumenta drasticamente la complessita.

### Overhead e Complessita

L'adozione di un service mesh comporta costi misurabili:

- **Latenza aggiuntiva**: ogni request attraversa due proxy (sidecar sorgente e sidecar destinazione), aggiungendo tipicamente 2-5ms di latenza totale.
- **Consumo di risorse**: ogni sidecar Envoy consuma circa 50-100MB di RAM e 0.1-0.5 vCPU a regime. Con 200 Pod, questo si traduce in 10-20GB di RAM e 20-100 vCPU dedicati ai sidecar.
- **Complessita operativa**: il control plane richiede manutenzione, aggiornamenti, e competenze specifiche. Il debugging di problemi di rete diventa piu stratificato.
- **Curve di apprendimento**: le CRD (Custom Resource Definitions) di Istio aggiungono decine di nuovi oggetti da padroneggiare.

---

## 2. Istio — Architettura

### Componenti Principali

Istio e il service mesh piu diffuso e feature-rich dell'ecosistema Kubernetes. A partire dalla versione 1.5, l'architettura e stata semplificata unificando i componenti del control plane in un singolo binario: **istiod**.

**istiod** integra tre funzionalita precedentemente separate:

- **Pilot**: responsabile della configurazione del routing e del traffic management. Traduce le regole di alto livello (VirtualService, DestinationRule) in configurazione Envoy (xDS API) e la distribuisce ai proxy.
- **Citadel**: gestisce l'infrastruttura PKI (Public Key Infrastructure) per mTLS. Genera, distribuisce e ruota i certificati X.509 per tutti i workload nel mesh.
- **Galley**: originariamente responsabile della validazione e della distribuzione della configurazione. Ora integrato in istiod.

**Envoy Proxy** e il sidecar data plane. E un proxy L4/L7 ad alte prestazioni scritto in C++, sviluppato originariamente da Lyft. Caratteristiche chiave:

- Hot restart senza downtime
- Estensibilita tramite filtri (inclusi filtri WASM)
- Supporto nativo per HTTP/1.1, HTTP/2, gRPC
- Health checking attivo e passivo
- Configurazione dinamica tramite xDS API

### Architettura Classica (Sidecar)

```
┌──────────────────────────────────────────────────┐
│                Control Plane                     │
│  ┌────────────────────────────────────────────┐  │
│  │              istiod                        │  │
│  │  ┌────────┐  ┌─────────┐  ┌────────────┐  │  │
│  │  │ Pilot  │  │ Citadel │  │   Galley   │  │  │
│  │  └────────┘  └─────────┘  └────────────┘  │  │
│  └──────────────────┬─────────────────────────┘  │
│                     │ xDS API                    │
└─────────────────────┼────────────────────────────┘
                      │
      ┌───────────────┼───────────────┐
      │               │               │
┌─────┴─────┐  ┌──────┴────┐  ┌──────┴────┐
│  Pod A    │  │  Pod B    │  │  Pod C    │
│ ┌───┐┌──┐│  │ ┌───┐┌──┐│  │ ┌───┐┌──┐│
│ │App││EP││  │ │App││EP││  │ │App││EP││
│ └───┘└──┘│  │ └───┘└──┘│  │ └───┘└──┘│
└──────────┘  └──────────┘  └──────────┘
              EP = Envoy Proxy
```

### Architettura Ambient Mesh (Sidecar-less)

A partire da Istio 1.18+, l'architettura **ambient mesh** elimina il sidecar per-pod. Il traffico viene gestito da due componenti:

- **ztunnel** (zero-trust tunnel): un proxy L4 per-node che gestisce mTLS e l'autorizzazione base. Opera come DaemonSet, un'istanza per nodo.
- **waypoint proxy**: un proxy L7 opzionale per-namespace o per-service, necessario solo quando servono funzionalita L7 (routing avanzato, header manipulation, fault injection).

Vantaggi dell'ambient mesh:
- Riduzione drastica del consumo di risorse (niente sidecar per Pod)
- Lifecycle del proxy indipendente dall'applicazione (nessun restart necessario dell'app per aggiornare il proxy)
- Onboarding semplificato (basta etichettare il namespace)

### Ingress e Egress Gateway

**istio-ingressgateway**: gestisce il traffico in ingresso al mesh. E un deployment Envoy dedicato che funge da punto di ingresso per il traffico esterno, configurato tramite risorse Gateway e VirtualService.

**istio-egressgateway**: gestisce il traffico in uscita dal mesh verso servizi esterni. Permette di centralizzare e controllare le connessioni verso l'esterno, applicando politiche di sicurezza e osservabilita.

### Installazione con istioctl

```bash
# Scaricare istioctl
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.22.0 sh -
cd istio-1.22.0
export PATH=$PWD/bin:$PATH

# Verificare i prerequisiti del cluster
istioctl x precheck

# Installazione con profilo demo (include tutti i componenti per test)
istioctl install --set profile=demo -y

# Profili disponibili:
# - default: produzione (istiod + ingress gateway)
# - demo: tutte le funzionalita attive (non per produzione)
# - minimal: solo istiod
# - ambient: architettura ambient mesh
# - remote: per cluster remoti in configurazione multi-cluster

# Verificare lo stato dell'installazione
istioctl verify-install

# Abilitare l'injection automatica del sidecar per un namespace
kubectl label namespace default istio-injection=enabled

# Verificare i componenti installati
kubectl get pods -n istio-system
kubectl get svc -n istio-system
```

### Installazione con Helm

```bash
# Aggiungere il repository Helm di Istio
helm repo add istio https://istio-release.storage.googleapis.com/charts
helm repo update

# Creare il namespace istio-system
kubectl create namespace istio-system

# Installare il componente base (CRD e risorse cluster-wide)
helm install istio-base istio/base -n istio-system --wait

# Installare istiod (control plane)
helm install istiod istio/istiod -n istio-system --wait \
  --set pilot.resources.requests.cpu=500m \
  --set pilot.resources.requests.memory=2Gi \
  --set pilot.resources.limits.cpu=1000m \
  --set pilot.resources.limits.memory=4Gi

# Installare l'ingress gateway
kubectl create namespace istio-ingress
helm install istio-ingress istio/gateway -n istio-ingress --wait

# Verificare l'installazione
helm ls -n istio-system
kubectl get pods -n istio-system
```

### Installazione Ambient Mesh

```bash
# Installare con profilo ambient
istioctl install --set profile=ambient -y

# Abilitare ambient mode per un namespace (senza sidecar injection)
kubectl label namespace default istio.io/dataplane-mode=ambient

# Verificare ztunnel (DaemonSet)
kubectl get pods -n istio-system -l app=ztunnel

# Creare un waypoint proxy per funzionalita L7
istioctl x waypoint apply --namespace default --name default-waypoint
```

---

## 3. Istio — Traffic Management

### Custom Resource Definitions per il Traffic Management

Istio utilizza quattro risorse principali per gestire il traffico:

- **VirtualService**: definisce le regole di routing per il traffico diretto verso un servizio. Specifica come instradare le request in base a header, URI, weight e altre condizioni.
- **DestinationRule**: definisce le politiche applicate dopo il routing (load balancing, connection pool, circuit breaking, TLS settings).
- **Gateway**: configura i punti di ingresso/uscita del mesh (load balancer esposti all'esterno).
- **ServiceEntry**: registra servizi esterni nel mesh, permettendo di applicare le stesse politiche di routing e sicurezza.

### VirtualService — Routing Base

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews-routing
  namespace: bookinfo
spec:
  hosts:
    - reviews                          # servizio di destinazione
  http:
    - route:
        - destination:
            host: reviews
            subset: v1                 # definito nella DestinationRule
          weight: 100
```

### DestinationRule — Subset e Load Balancing

```yaml
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: reviews-destination
  namespace: bookinfo
spec:
  host: reviews
  trafficPolicy:
    loadBalancer:
      simple: LEAST_REQUEST           # algoritmo di load balancing
    connectionPool:
      tcp:
        maxConnections: 100
        connectTimeout: 30ms
      http:
        h2UpgradePolicy: DEFAULT
        http1MaxPendingRequests: 100
        http2MaxRequests: 1000
        maxRequestsPerConnection: 10
        maxRetries: 3
  subsets:
    - name: v1
      labels:
        version: v1
    - name: v2
      labels:
        version: v2
    - name: v3
      labels:
        version: v3
```

### Header-Based Routing

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews-header-routing
  namespace: bookinfo
spec:
  hosts:
    - reviews
  http:
    # Utenti interni (header x-user-type: internal) -> v3
    - match:
        - headers:
            x-user-type:
              exact: internal
      route:
        - destination:
            host: reviews
            subset: v3
    # Utenti beta tester -> v2
    - match:
        - headers:
            x-beta-tester:
              exact: "true"
      route:
        - destination:
            host: reviews
            subset: v2
    # Tutti gli altri -> v1
    - route:
        - destination:
            host: reviews
            subset: v1
```

### Weight-Based Traffic Splitting (Canary)

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews-canary
  namespace: bookinfo
spec:
  hosts:
    - reviews
  http:
    - route:
        - destination:
            host: reviews
            subset: v1
          weight: 90                   # 90% del traffico a v1
        - destination:
            host: reviews
            subset: v2
          weight: 10                   # 10% del traffico a v2
```

### Blue-Green Deployment

```yaml
# Fase 1: tutto il traffico su blue (v1)
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews-blue-green
  namespace: bookinfo
spec:
  hosts:
    - reviews
  http:
    - route:
        - destination:
            host: reviews
            subset: blue              # v1 attiva
          weight: 100
---
# Fase 2: switch istantaneo a green (v2)
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews-blue-green
  namespace: bookinfo
spec:
  hosts:
    - reviews
  http:
    - route:
        - destination:
            host: reviews
            subset: green             # v2 attiva
          weight: 100
```

### Traffic Mirroring (Shadowing)

Il mirroring invia una copia del traffico live a un servizio di test senza influenzare la risposta al client. Le risposte dal mirror vengono scartate.

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews-mirror
  namespace: bookinfo
spec:
  hosts:
    - reviews
  http:
    - route:
        - destination:
            host: reviews
            subset: v1
          weight: 100
      mirror:
        host: reviews
        subset: v2
      mirrorPercentage:
        value: 100.0                   # percentuale di traffico da specchiare
```

### Fault Injection

Utile per testare la resilienza dell'applicazione in modo controllato.

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: ratings-fault
  namespace: bookinfo
spec:
  hosts:
    - ratings
  http:
    - fault:
        delay:
          percentage:
            value: 10.0               # 10% delle request
          fixedDelay: 5s               # ritardo artificiale di 5 secondi
        abort:
          percentage:
            value: 5.0                # 5% delle request
          httpStatus: 503              # risposta con errore 503
      route:
        - destination:
            host: ratings
            subset: v1
```

### Circuit Breaking

```yaml
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: reviews-circuit-breaker
  namespace: bookinfo
spec:
  host: reviews
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 50             # max connessioni TCP simultanee
      http:
        http1MaxPendingRequests: 25    # max request in coda
        http2MaxRequests: 50           # max request attive
        maxRequestsPerConnection: 5    # max request per connessione
    outlierDetection:
      consecutive5xxErrors: 5          # errori consecutivi per ejection
      interval: 10s                    # finestra di analisi
      baseEjectionTime: 30s           # durata base dell'ejection
      maxEjectionPercent: 50          # max % di host rimossi
      minHealthPercent: 30            # minimo % di host sani richiesto
```

### Retry e Timeout

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews-retry-timeout
  namespace: bookinfo
spec:
  hosts:
    - reviews
  http:
    - timeout: 10s                     # timeout globale per la request
      retries:
        attempts: 3                    # numero massimo di retry
        perTryTimeout: 3s             # timeout per singolo tentativo
        retryOn: 5xx,reset,connect-failure,retriable-4xx
        retryRemoteLocalities: true   # retry su localita diverse
      route:
        - destination:
            host: reviews
            subset: v1
```

### Gateway e ServiceEntry

```yaml
# Gateway per traffico esterno
apiVersion: networking.istio.io/v1
kind: Gateway
metadata:
  name: bookinfo-gateway
  namespace: bookinfo
spec:
  selector:
    istio: ingressgateway
  servers:
    - port:
        number: 443
        name: https
        protocol: HTTPS
      tls:
        mode: SIMPLE
        credentialName: bookinfo-tls-cert    # Secret Kubernetes con certificato
      hosts:
        - "bookinfo.example.com"
    - port:
        number: 80
        name: http
        protocol: HTTP
      hosts:
        - "bookinfo.example.com"
      tls:
        httpsRedirect: true                  # redirect HTTP -> HTTPS
---
# ServiceEntry per servizio esterno
apiVersion: networking.istio.io/v1
kind: ServiceEntry
metadata:
  name: external-api
  namespace: bookinfo
spec:
  hosts:
    - api.external-service.com
  ports:
    - number: 443
      name: https
      protocol: TLS
  location: MESH_EXTERNAL
  resolution: DNS
```

---

## 4. Istio — Security

### Mutual TLS (mTLS)

Istio implementa mTLS in modo trasparente: i sidecar proxy negoziano automaticamente connessioni TLS reciproche tra servizi. Ogni workload riceve un certificato X.509 con identita SPIFFE (`spiffe://cluster.local/ns/<namespace>/sa/<service-account>`).

Due modalita principali:

- **STRICT**: solo traffico mTLS accettato. Qualsiasi connessione plain-text viene rifiutata. Ideale per ambienti production dove tutti i servizi sono nel mesh.
- **PERMISSIVE**: accetta sia traffico mTLS che plain-text. Utile durante la migrazione graduale al mesh, quando non tutti i servizi hanno il sidecar.

### PeerAuthentication

```yaml
# mTLS STRICT a livello di mesh (tutti i namespace)
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system              # a livello mesh
spec:
  mtls:
    mode: STRICT
---
# mTLS PERMISSIVE per un namespace specifico (override)
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: default
  namespace: legacy-services
spec:
  mtls:
    mode: PERMISSIVE
---
# mTLS STRICT per un workload specifico con eccezione per una porta
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: payment-mtls
  namespace: production
spec:
  selector:
    matchLabels:
      app: payment-service
  mtls:
    mode: STRICT
  portLevelMtls:
    8080:
      mode: PERMISSIVE                # porta health check senza mTLS
```

### RequestAuthentication (JWT)

```yaml
apiVersion: security.istio.io/v1
kind: RequestAuthentication
metadata:
  name: jwt-auth
  namespace: production
spec:
  selector:
    matchLabels:
      app: api-gateway
  jwtRules:
    - issuer: "https://auth.example.com"
      jwksUri: "https://auth.example.com/.well-known/jwks.json"
      audiences:
        - "api.example.com"
      forwardOriginalToken: true       # inoltra il token JWT al servizio
      outputPayloadToHeader: "x-jwt-payload"
    - issuer: "https://accounts.google.com"
      jwksUri: "https://www.googleapis.com/oauth2/v3/certs"
```

### AuthorizationPolicy

Le AuthorizationPolicy definiscono regole di accesso granulari. Istio supporta tre azioni: **ALLOW**, **DENY** e **CUSTOM**.

```yaml
# DENY: bloccare traffico da namespace non autorizzati
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: deny-external-namespaces
  namespace: production
spec:
  action: DENY
  rules:
    - from:
        - source:
            notNamespaces:
              - production
              - monitoring
              - istio-system
---
# ALLOW: accesso granulare basato su source e operazione
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: production
spec:
  selector:
    matchLabels:
      app: backend-api
  action: ALLOW
  rules:
    - from:
        - source:
            principals:
              - "cluster.local/ns/production/sa/frontend"
            namespaces:
              - production
      to:
        - operation:
            methods: ["GET", "POST"]
            paths: ["/api/v1/*"]
      when:
        - key: request.headers[x-api-version]
          values: ["v1", "v2"]
---
# DENY: proteggere endpoint admin
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: deny-admin-access
  namespace: production
spec:
  selector:
    matchLabels:
      app: backend-api
  action: DENY
  rules:
    - to:
        - operation:
            paths: ["/admin/*", "/internal/*"]
      from:
        - source:
            notPrincipals:
              - "cluster.local/ns/production/sa/admin-service"
---
# ALLOW con condizione JWT
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: require-jwt-claims
  namespace: production
spec:
  selector:
    matchLabels:
      app: api-gateway
  action: ALLOW
  rules:
    - from:
        - source:
            requestPrincipals: ["https://auth.example.com/*"]
      when:
        - key: request.auth.claims[role]
          values: ["admin", "editor"]
```

### Certificate Management

```bash
# Verificare i certificati mTLS attivi in un Pod
istioctl proxy-config secret <pod-name> -n <namespace>

# Verificare l'identita SPIFFE di un workload
istioctl proxy-config secret deploy/reviews -n bookinfo -o json | \
  jq '.dynamicActiveSecrets[0].secret.tlsCertificate.certificateChain.inlineBytes' | \
  tr -d '"' | base64 -d | openssl x509 -text -noout

# Ruotare i certificati (forzare il rinnovo)
kubectl rollout restart deployment/istiod -n istio-system
```

### External CA Integration

```yaml
# Configurare Istio per utilizzare una CA esterna (cert-manager)
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  values:
    pilot:
      env:
        EXTERNAL_CA: ISTIOD_RA_KUBERNETES_API
    global:
      caAddress: cert-manager-istio-csr.cert-manager.svc:443
```

### Secure Ingress con TLS

```bash
# Creare un Secret TLS per l'ingress gateway
kubectl create -n istio-system secret tls bookinfo-credential \
  --key=server.key \
  --cert=server.crt

# Creare il Secret con CA per mTLS verso client esterni
kubectl create -n istio-system secret generic bookinfo-credential \
  --from-file=tls.key=server.key \
  --from-file=tls.crt=server.crt \
  --from-file=ca.crt=ca.crt
```

```yaml
# Gateway con mTLS verso client esterni
apiVersion: networking.istio.io/v1
kind: Gateway
metadata:
  name: secure-gateway
  namespace: production
spec:
  selector:
    istio: ingressgateway
  servers:
    - port:
        number: 443
        name: https
        protocol: HTTPS
      tls:
        mode: MUTUAL                   # richiede certificato client
        credentialName: bookinfo-credential
      hosts:
        - "secure.example.com"
```

---

## 5. Istio — Observability

### Metriche Automatiche

Istio genera automaticamente metriche standard per tutto il traffico nel mesh, senza alcuna modifica al codice applicativo. Le metriche principali seguono il modello RED (Rate, Errors, Duration):

| Metrica | Tipo | Descrizione |
|---|---|---|
| `istio_requests_total` | Counter | Numero totale di request, con label per response_code, source, destination |
| `istio_request_duration_milliseconds` | Histogram | Distribuzione della latenza delle request |
| `istio_request_bytes` | Histogram | Dimensione del body delle request in ingresso |
| `istio_response_bytes` | Histogram | Dimensione del body delle risposte |
| `istio_tcp_connections_opened_total` | Counter | Connessioni TCP aperte |
| `istio_tcp_connections_closed_total` | Counter | Connessioni TCP chiuse |
| `istio_tcp_sent_bytes_total` | Counter | Byte inviati su connessioni TCP |
| `istio_tcp_received_bytes_total` | Counter | Byte ricevuti su connessioni TCP |

Ogni metrica include label dettagliate: `source_workload`, `destination_workload`, `source_namespace`, `destination_namespace`, `response_code`, `request_protocol`, `connection_security_policy`.

### Integrazione Prometheus

```yaml
# Installare Prometheus per Istio
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.22/samples/addons/prometheus.yaml

# Verificare che Prometheus stia scraping le metriche Istio
kubectl port-forward svc/prometheus 9090:9090 -n istio-system
```

Query PromQL utili per il monitoring del mesh:

```promql
# Request rate per servizio (ultimi 5 minuti)
rate(istio_requests_total{reporter="destination"}[5m])

# Error rate (5xx) per servizio
sum(rate(istio_requests_total{reporter="destination",response_code=~"5.."}[5m]))
by (destination_workload, destination_namespace)
/
sum(rate(istio_requests_total{reporter="destination"}[5m]))
by (destination_workload, destination_namespace)

# Latenza P99 per servizio
histogram_quantile(0.99,
  sum(rate(istio_request_duration_milliseconds_bucket{reporter="destination"}[5m]))
  by (le, destination_workload, destination_namespace)
)

# Connessioni TCP attive per servizio
sum(istio_tcp_connections_opened_total{reporter="destination"})
by (destination_workload)
-
sum(istio_tcp_connections_closed_total{reporter="destination"})
by (destination_workload)
```

### Grafana Dashboards

```bash
# Installare Grafana con dashboard predefinite per Istio
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.22/samples/addons/grafana.yaml

# Accedere alla dashboard
kubectl port-forward svc/grafana 3000:3000 -n istio-system
```

Dashboard predefinite incluse:

- **Mesh Dashboard**: panoramica globale del mesh (request rate, error rate, latenza per tutti i servizi)
- **Service Dashboard**: dettaglio per singolo servizio (incoming/outgoing traffic, latenza per percentile, error breakdown)
- **Workload Dashboard**: metriche a livello di workload (Pod-level)
- **Performance Dashboard**: metriche di performance del control plane (istiod CPU, memoria, tempo di push configurazione)
- **Istio Control Plane Dashboard**: stato di salute di istiod (xDS push errors, active connections, pilot push time)

### Distributed Tracing

Istio propaga automaticamente gli header di tracing (B3, W3C Trace Context), ma l'applicazione deve inoltrare questi header nelle chiamate interne per mantenere la correlazione. Header da propagare:

- `x-request-id`
- `x-b3-traceid`, `x-b3-spanid`, `x-b3-parentspanid`, `x-b3-sampled`, `x-b3-flags`
- `traceparent`, `tracestate` (W3C)

```bash
# Installare Jaeger per il tracing distribuito
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.22/samples/addons/jaeger.yaml

# Accedere all'interfaccia Jaeger
kubectl port-forward svc/tracing 16686:80 -n istio-system

# Configurare il sampling rate (default 1% in produzione)
istioctl install --set meshConfig.defaultConfig.tracing.sampling=10.0
```

```yaml
# Configurazione tracing tramite Telemetry API
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: tracing-config
  namespace: istio-system
spec:
  tracing:
    - providers:
        - name: jaeger
      randomSamplingPercentage: 10.0     # campionare il 10% delle request
      customTags:
        environment:
          literal:
            value: production
```

### Kiali — Service Mesh Visualization

Kiali e la console di osservabilita dedicata per Istio. Fornisce una visualizzazione in tempo reale della topologia del mesh, del flusso di traffico e dello stato di salute dei servizi.

```bash
# Installare Kiali
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.22/samples/addons/kiali.yaml

# Accedere all'interfaccia
kubectl port-forward svc/kiali 20001:20001 -n istio-system
```

Funzionalita principali di Kiali:
- **Graph**: visualizzazione interattiva della topologia del mesh con metriche in tempo reale
- **Applications**: stato di salute e configurazione per applicazione
- **Workloads**: dettaglio per workload con log e metriche
- **Services**: configurazione Istio applicata per servizio
- **Istio Config**: validazione delle risorse Istio (VirtualService, DestinationRule, ecc.)

### Access Logging

```yaml
# Abilitare l'access logging per tutto il mesh
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: mesh-logging
  namespace: istio-system
spec:
  accessLogging:
    - providers:
        - name: envoy
      filter:
        expression: "response.code >= 400"   # loggare solo errori
---
# Access logging dettagliato per un workload specifico
apiVersion: telemetry.istio.io/v1
kind: Telemetry
metadata:
  name: reviews-logging
  namespace: bookinfo
spec:
  selector:
    matchLabels:
      app: reviews
  accessLogging:
    - providers:
        - name: envoy
```

```bash
# Visualizzare i log del sidecar proxy di un Pod
kubectl logs <pod-name> -c istio-proxy -n <namespace> --tail=100

# Formato di log Envoy predefinito:
# [%START_TIME%] "%REQ(:METHOD)% %REQ(X-ENVOY-ORIGINAL-PATH?:PATH)% %PROTOCOL%"
# %RESPONSE_CODE% %RESPONSE_FLAGS% %RESPONSE_CODE_DETAILS%
# %CONNECTION_TERMINATION_DETAILS% "%UPSTREAM_TRANSPORT_FAILURE_REASON%"
# %BYTES_RECEIVED% %BYTES_SENT% %DURATION% %RESP(X-ENVOY-UPSTREAM-SERVICE-TIME)%
# "%REQ(X-FORWARDED-FOR)%" "%REQ(USER-AGENT)%"
# "%REQ(X-REQUEST-ID)%" "%REQ(:AUTHORITY)%" "%UPSTREAM_HOST%"
```

---

## 6. Linkerd

### Filosofia e Architettura

Linkerd e un service mesh progettato con tre principi fondamentali: **semplicita**, **performance** e **sicurezza by default**. A differenza di Istio che offre un set massivo di funzionalita, Linkerd adotta un approccio minimalista: include solo le feature considerate essenziali e le implementa nel modo piu semplice possibile.

Linkerd utilizza un proxy data plane custom scritto in **Rust** — `linkerd2-proxy` — invece di Envoy. Questa scelta ha implicazioni significative:

- **Performance**: il proxy Rust e significativamente piu leggero di Envoy. Consuma circa 10-20MB di RAM per sidecar (vs 50-100MB di Envoy) e aggiunge latenza sub-millisecondo (tipicamente 0.5ms p99).
- **Sicurezza**: Rust elimina intere classi di vulnerabilita (buffer overflow, use-after-free) che affliggono il codice C++ di Envoy.
- **Semplicita**: il proxy implementa solo le funzionalita necessarie per un service mesh, senza la complessita generica di Envoy.

### Componenti

**Control Plane** — Deployment nel namespace `linkerd`:
- **destination**: service discovery e configurazione del routing. Riceve le informazioni dai Kubernetes Service e Endpoint e le distribuisce ai proxy.
- **identity**: gestisce la PKI per mTLS. Genera certificati per ogni proxy e li ruota automaticamente (durata predefinita: 24 ore).
- **proxy-injector**: webhook di Kubernetes che inietta automaticamente il sidecar nei Pod dei namespace annotati.

**Data Plane** — `linkerd2-proxy` iniettato come sidecar:
- Proxy L4/L7 in Rust
- mTLS automatico senza configurazione
- Metriche golden signals automatiche
- Retry e timeout automatici basati su service profile
- Load balancing EWMA (Exponentially Weighted Moving Average)

### Installazione

```bash
# Installare la CLI linkerd
curl --proto '=https' --tlsv1.2 -sSfL https://run.linkerd.io/install | sh
export PATH=$HOME/.linkerd2/bin:$PATH

# Verificare i prerequisiti del cluster
linkerd check --pre

# Installare il control plane
linkerd install --crds | kubectl apply -f -
linkerd install | kubectl apply -f -

# Verificare l'installazione
linkerd check

# Installare le estensioni di osservabilita (Prometheus, Grafana, dashboard)
linkerd viz install | kubectl apply -f -
linkerd viz check

# Iniettare il sidecar in un namespace
kubectl annotate namespace default linkerd.io/inject=enabled

# Iniettare il sidecar in un deployment esistente
kubectl get deploy reviews -o yaml | linkerd inject - | kubectl apply -f -

# Accedere alla dashboard integrata
linkerd viz dashboard &
```

### Service Profile

I service profile definiscono il comportamento del proxy per un servizio: routing, retry, timeout. Sono l'equivalente Linkerd di VirtualService + DestinationRule di Istio, ma piu semplici.

```yaml
apiVersion: linkerd.io/v1alpha2
kind: ServiceProfile
metadata:
  name: reviews.bookinfo.svc.cluster.local
  namespace: bookinfo
spec:
  routes:
    - name: GET /api/v1/reviews
      condition:
        method: GET
        pathRegex: /api/v1/reviews
      isRetryable: true                # abilitare retry automatici
      timeout: 5s                      # timeout per questa route
    - name: POST /api/v1/reviews
      condition:
        method: POST
        pathRegex: /api/v1/reviews
      isRetryable: false               # POST non e idempotente, no retry
      timeout: 10s
  retryBudget:
    retryRatio: 0.2                    # max 20% di request aggiuntive per retry
    minRetriesPerSecond: 10            # minimo retry al secondo
    ttl: 10s                           # finestra temporale per il budget
```

```bash
# Generare un service profile automaticamente da un file OpenAPI/Swagger
linkerd profile --open-api swagger.yaml reviews | kubectl apply -f -

# Generare un service profile osservando il traffico live (tap)
linkerd profile --tap deploy/reviews --tap-duration 60s reviews
```

### Traffic Splitting

```yaml
# Traffic split tra due versioni (canary)
apiVersion: split.smi-spec.io/v1alpha4
kind: TrafficSplit
metadata:
  name: reviews-split
  namespace: bookinfo
spec:
  service: reviews                     # servizio apex
  backends:
    - service: reviews-v1
      weight: 900                      # 90%
    - service: reviews-v2
      weight: 100                      # 10%
```

### mTLS Automatico

Linkerd abilita mTLS automaticamente per tutto il traffico tra i proxy senza alcuna configurazione. Non esiste un equivalente di PeerAuthentication: mTLS e sempre attivo in modalita opportunistica (se entrambi i lati hanno il sidecar, la connessione e mTLS).

```bash
# Verificare lo stato mTLS di una connessione
linkerd viz edges deployment -n bookinfo
# Output mostra SRC, DST e se la connessione e SECURED (mTLS) o non secured

# Verificare le identita dei certificati
linkerd identity -n bookinfo

# Dettaglio connessioni TLS attive
linkerd viz stat deploy -n bookinfo -o wide
```

### Dashboard Integrato

```bash
# Visualizzare metriche live per un namespace
linkerd viz stat deploy -n bookinfo

# Output esempio:
# NAME       MESHED   SUCCESS   RPS   LATENCY_P50   LATENCY_P95   LATENCY_P99
# reviews    1/1      100.00%   2.0   5ms           10ms          15ms
# ratings    1/1      98.50%    1.5   3ms           8ms           12ms

# Top delle request live (simile a 'top' di Linux)
linkerd viz top deploy/reviews -n bookinfo

# Tap: osservare le request in tempo reale
linkerd viz tap deploy/reviews -n bookinfo --to deploy/ratings
```

### Confronto Linkerd vs Istio

| Aspetto | Linkerd | Istio |
|---|---|---|
| **Complessita** | Minimale, poche CRD | Elevata, molte CRD e opzioni |
| **Proxy** | linkerd2-proxy (Rust, ~20MB RAM) | Envoy (C++, ~100MB RAM) |
| **Latenza aggiunta** | ~0.5ms p99 | ~2-3ms p99 |
| **mTLS** | Automatico, sempre attivo | Configurabile (STRICT/PERMISSIVE) |
| **Traffic Management** | Base (split, retry, timeout) | Avanzato (mirroring, fault injection, header routing) |
| **Extensibility** | Limitata | Elevata (WASM, Lua filters, EnvoyFilter) |
| **Multi-cluster** | Supportato | Supportato con piu opzioni |
| **Curva di apprendimento** | Bassa (1-2 giorni produttivi) | Alta (1-2 settimane per le basi) |
| **CNCF Status** | Graduated | Graduated |
| **Caso d'uso ideale** | Semplicita, performance, mTLS rapido | Controllo granulare, funzionalita avanzate |

---

## 7. Consul Connect

### Architettura

HashiCorp Consul e originariamente un sistema di service discovery e key-value store distribuito. **Consul Connect** aggiunge funzionalita di service mesh, estendendo Consul con mTLS automatico, autorizzazione service-to-service e traffic management.

A differenza di Istio e Linkerd che sono nativi Kubernetes, Consul e progettato per ambienti **eterogenei**: funziona su Kubernetes, VM, bare metal e ambienti multi-cloud. Questa e la sua differenziazione principale.

Componenti architetturali:

- **Consul Server**: cluster di nodi server (tipicamente 3 o 5) che mantengono lo stato del catalogo servizi, la configurazione e le policy di sicurezza. Utilizzano il protocollo Raft per il consenso.
- **Consul Client (Agent)**: agente leggero eseguito su ogni nodo che registra i servizi locali, esegue health check e inoltra le query ai server.
- **Sidecar Proxy**: Envoy (raccomandato) o il proxy built-in di Consul. Gestisce mTLS e il routing del traffico.
- **Consul Connect CA**: autorita di certificazione integrata per la generazione e distribuzione di certificati mTLS.

### Installazione su Kubernetes

```bash
# Aggiungere il repository Helm di HashiCorp
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo update

# Installare Consul su Kubernetes
helm install consul hashicorp/consul \
  --namespace consul \
  --create-namespace \
  --values consul-values.yaml
```

```yaml
# consul-values.yaml
global:
  name: consul
  datacenter: dc1
  tls:
    enabled: true                      # TLS per comunicazione interna
  acls:
    manageSystemACLs: true             # gestione automatica ACL

server:
  replicas: 3                          # cluster di 3 server per HA
  storage: 10Gi
  resources:
    requests:
      memory: 256Mi
      cpu: 250m

connectInject:
  enabled: true                        # abilitare service mesh
  default: false                       # injection manuale (non automatica)

controller:
  enabled: true                        # abilitare il controller per CRD

meshGateway:
  enabled: true                        # gateway per multi-datacenter
  replicas: 2

ui:
  enabled: true
  service:
    type: LoadBalancer
```

### Service Discovery

```bash
# Registrare un servizio via CLI
consul services register -name=web -port=8080 -address=10.0.1.5

# Query dei servizi registrati
consul catalog services

# Health check di un servizio
consul health checks web

# DNS-based service discovery (integrato)
dig @127.0.0.1 -p 8600 web.service.consul
```

```yaml
# Registrazione servizio su Kubernetes tramite annotazioni
apiVersion: v1
kind: Pod
metadata:
  name: web
  annotations:
    consul.hashicorp.com/connect-inject: "true"
    consul.hashicorp.com/connect-service: "web"
    consul.hashicorp.com/connect-service-port: "8080"
    consul.hashicorp.com/connect-service-upstreams: "api:9091,db:9092"
spec:
  containers:
    - name: web
      image: web:latest
      ports:
        - containerPort: 8080
      env:
        - name: API_URL
          value: "http://localhost:9091"     # traffico verso 'api' via sidecar
        - name: DB_URL
          value: "http://localhost:9092"     # traffico verso 'db' via sidecar
```

### Intentions (ACL Service-to-Service)

Le intentions definiscono le regole di autorizzazione tra servizi. Funzionano come firewall a livello di servizio.

```bash
# Creare un'intention: web puo comunicare con api
consul intention create web api

# Negare l'accesso: web non puo comunicare con db
consul intention create -deny web db

# Elencare le intentions
consul intention list

# Eliminare un'intention
consul intention delete web api
```

```yaml
# Intentions via CRD su Kubernetes
apiVersion: consul.hashicorp.com/v1alpha1
kind: ServiceIntentions
metadata:
  name: api-intentions
spec:
  destination:
    name: api
  sources:
    - name: web
      action: allow
      permissions:
        - http:
            pathPrefix: /api/v1
            methods: ["GET", "POST"]
    - name: admin
      action: allow
    - name: "*"                        # default deny per tutti gli altri
      action: deny
```

### Multi-Datacenter

Consul eccelle nel supporto multi-datacenter, una delle sue funzionalita distintive.

```yaml
# Configurazione per mesh gateway multi-datacenter
global:
  name: consul
  datacenter: dc1
  tls:
    enabled: true
  federation:
    enabled: true
    createFederationSecret: true       # creare il secret per la federazione

meshGateway:
  enabled: true
  replicas: 2
  wanAddress:
    source: Service
    port: 443
```

```bash
# Federare due datacenter
# Sul DC primario: esportare il secret di federazione
kubectl get secret consul-federation -n consul -o yaml > federation-secret.yaml

# Sul DC secondario: applicare il secret e configurare il join
kubectl apply -f federation-secret.yaml -n consul

# Verificare la federazione
consul members -wan
```

### Integrazione con Vault

```yaml
# Configurare Consul per utilizzare Vault come CA
global:
  tls:
    enabled: true
  secretsBackend:
    vault:
      enabled: true
      consulServerRole: consul-server
      consulClientRole: consul-client
      consulCARole: consul-ca
      connectCA:
        address: https://vault.vault.svc:8200
        rootPKIPath: connect-root
        intermediatePKIPath: connect-intermediate
        authMethodPath: kubernetes
```

---

## 8. Pattern Avanzati

### Multi-Cluster Mesh

Un service mesh multi-cluster permette ai servizi di comunicare in modo trasparente tra cluster Kubernetes diversi, mantenendo mTLS, routing e osservabilita end-to-end.

Istio supporta tre topologie multi-cluster:

- **Primary-Remote**: un cluster primario ospita il control plane, i cluster remoti utilizzano un control plane remoto che si connette al primario.
- **Multi-Primary**: ogni cluster ha il proprio control plane, i cluster si sincronizzano tra loro.
- **External Control Plane**: il control plane e ospitato su un cluster separato dedicato.

```yaml
# Configurazione multi-cluster Istio (Primary cluster)
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: istio-primary
spec:
  values:
    global:
      meshID: mesh1
      multiCluster:
        clusterName: cluster1
      network: network1
  meshConfig:
    defaultConfig:
      proxyMetadata:
        ISTIO_META_DNS_CAPTURE: "true"
        ISTIO_META_DNS_AUTO_ALLOCATE: "true"
```

```bash
# Configurare l'accesso remoto tra cluster
istioctl create-remote-secret \
  --name=cluster2 \
  --context=cluster2-context | \
  kubectl apply -f - --context=cluster1-context

# Verificare la connettivita multi-cluster
istioctl remote-clusters --context=cluster1-context
```

### Mesh Federation

La federazione permette a mesh indipendenti di comunicare tra loro mantenendo autonomia amministrativa.

```yaml
# Esportare un servizio da un mesh per renderlo accessibile ad altri mesh
apiVersion: networking.istio.io/v1
kind: ServiceEntry
metadata:
  name: external-mesh-service
  namespace: istio-system
spec:
  hosts:
    - payments.mesh2.global
  location: MESH_EXTERNAL
  ports:
    - number: 443
      name: https
      protocol: TLS
  resolution: DNS
  endpoints:
    - address: payments-gateway.mesh2.example.com
      ports:
        https: 15443                   # porta mTLS standard Istio
```

### Egress Control

Il controllo del traffico in uscita e critico per la sicurezza: impedisce ai servizi compromessi di comunicare con endpoint esterni non autorizzati.

```yaml
# Politica globale: bloccare tutto il traffico in uscita per default
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  meshConfig:
    outboundTrafficPolicy:
      mode: REGISTRY_ONLY             # solo destinazioni esplicitamente registrate
---
# Consentire traffico verso un servizio esterno specifico
apiVersion: networking.istio.io/v1
kind: ServiceEntry
metadata:
  name: allowed-external-api
  namespace: production
spec:
  hosts:
    - api.stripe.com
  ports:
    - number: 443
      name: https
      protocol: TLS
  location: MESH_EXTERNAL
  resolution: DNS
---
# Routing del traffico esterno tramite egress gateway
apiVersion: networking.istio.io/v1
kind: Gateway
metadata:
  name: egress-gateway
  namespace: istio-system
spec:
  selector:
    istio: egressgateway
  servers:
    - port:
        number: 443
        name: tls
        protocol: TLS
      hosts:
        - api.stripe.com
      tls:
        mode: PASSTHROUGH
---
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: route-via-egress
  namespace: production
spec:
  hosts:
    - api.stripe.com
  gateways:
    - mesh
    - istio-system/egress-gateway
  tls:
    - match:
        - gateways:
            - mesh
          port: 443
          sniHosts:
            - api.stripe.com
      route:
        - destination:
            host: istio-egressgateway.istio-system.svc.cluster.local
            port:
              number: 443
    - match:
        - gateways:
            - istio-system/egress-gateway
          port: 443
          sniHosts:
            - api.stripe.com
      route:
        - destination:
            host: api.stripe.com
            port:
              number: 443
```

### Rate Limiting

```yaml
# Rate limiting globale con Envoy
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: rate-limit-filter
  namespace: istio-system
spec:
  configPatches:
    - applyTo: HTTP_FILTER
      match:
        context: SIDECAR_INBOUND
        listener:
          filterChain:
            filter:
              name: envoy.filters.network.http_connection_manager
      patch:
        operation: INSERT_BEFORE
        value:
          name: envoy.filters.http.local_ratelimit
          typed_config:
            "@type": type.googleapis.com/udpa.type.v1.TypedStruct
            type_url: type.googleapis.com/envoy.extensions.filters.http.local_ratelimit.v3.LocalRateLimit
            value:
              stat_prefix: http_local_rate_limiter
              token_bucket:
                max_tokens: 100
                tokens_per_fill: 100
                fill_interval: 60s        # 100 request al minuto
              filter_enabled:
                runtime_key: local_rate_limit_enabled
                default_value:
                  numerator: 100
                  denominator: HUNDRED
              filter_enforced:
                runtime_key: local_rate_limit_enforced
                default_value:
                  numerator: 100
                  denominator: HUNDRED
              response_headers_to_add:
                - append_action: OVERWRITE_IF_EXISTS_OR_ADD
                  header:
                    key: x-local-rate-limit
                    value: "true"
```

### WASM Extensibility

WebAssembly (WASM) permette di estendere Envoy con filtri custom senza ricompilare il proxy. I filtri WASM possono essere scritti in Rust, Go, C++ o AssemblyScript.

```yaml
# Applicare un filtro WASM custom
apiVersion: extensions.istio.io/v1alpha1
kind: WasmPlugin
metadata:
  name: custom-auth-filter
  namespace: production
spec:
  selector:
    matchLabels:
      app: api-gateway
  url: oci://registry.example.com/wasm-filters/custom-auth:v1.0
  phase: AUTHN                         # fase nel filter chain
  pluginConfig:
    allowed_issuers:
      - "https://auth.example.com"
    cache_ttl_seconds: 300
  imagePullPolicy: IfNotPresent
  vmConfig:
    env:
      - name: LOG_LEVEL
        value: info
```

### Custom Authorization

```yaml
# AuthorizationPolicy con provider CUSTOM (external authorizer)
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: external-authz
  namespace: production
spec:
  selector:
    matchLabels:
      app: api-gateway
  action: CUSTOM
  provider:
    name: opa-authz                    # definito nella meshConfig
  rules:
    - to:
        - operation:
            paths: ["/api/*"]
---
# Configurazione del provider nella meshConfig
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  meshConfig:
    extensionProviders:
      - name: opa-authz
        envoyExtAuthzGrpc:
          service: opa.opa-system.svc.cluster.local
          port: 9191
          includeRequestBodyInCheck:
            maxRequestBytes: 4096
            allowPartialMessage: true
```

---

## 9. Deployment Strategies con Service Mesh

### Canary Release Step-by-Step

Una canary release espone progressivamente una nuova versione a una percentuale crescente di traffico, monitorando le metriche di salute ad ogni step.

**Step 1**: Deployare la nuova versione senza traffico.

```bash
# Deployare v2 con 0 repliche (o con traffic weight 0)
kubectl apply -f reviews-v2-deployment.yaml
kubectl scale deployment reviews-v2 --replicas=2 -n bookinfo
```

**Step 2**: Inviare il 5% del traffico alla nuova versione.

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews-canary
  namespace: bookinfo
spec:
  hosts:
    - reviews
  http:
    - route:
        - destination:
            host: reviews
            subset: v1
          weight: 95
        - destination:
            host: reviews
            subset: v2
          weight: 5
```

**Step 3**: Monitorare le metriche di salute.

```bash
# Verificare l'error rate della nuova versione
kubectl exec -n istio-system deploy/prometheus -- \
  promtool query instant http://localhost:9090 \
  'sum(rate(istio_requests_total{destination_workload="reviews-v2",response_code=~"5.."}[5m])) / sum(rate(istio_requests_total{destination_workload="reviews-v2"}[5m]))'

# Verificare la latenza p99
kubectl exec -n istio-system deploy/prometheus -- \
  promtool query instant http://localhost:9090 \
  'histogram_quantile(0.99, sum(rate(istio_request_duration_milliseconds_bucket{destination_workload="reviews-v2"}[5m])) by (le))'
```

**Step 4**: Se le metriche sono soddisfacenti, incrementare progressivamente (5% -> 25% -> 50% -> 100%).

**Step 5**: Completare la migrazione.

```yaml
# 100% del traffico su v2
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews-canary
  namespace: bookinfo
spec:
  hosts:
    - reviews
  http:
    - route:
        - destination:
            host: reviews
            subset: v2
          weight: 100
```

### Progressive Delivery con Flagger

Flagger automatizza il processo di canary release, incrementando il traffico automaticamente in base alle metriche.

```bash
# Installare Flagger per Istio
helm repo add flagger https://flagger.app
helm install flagger flagger/flagger \
  --namespace istio-system \
  --set meshProvider=istio \
  --set metricsServer=http://prometheus.istio-system:9090
```

```yaml
# Definire una Canary resource per automatizzare il rollout
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: reviews
  namespace: bookinfo
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: reviews
  progressDeadlineSeconds: 600         # timeout massimo per il rollout
  service:
    port: 9080
    targetPort: 9080
    gateways:
      - bookinfo-gateway
    hosts:
      - reviews.bookinfo.svc.cluster.local
  analysis:
    interval: 1m                       # frequenza di analisi
    threshold: 5                       # numero massimo di metriche fallite
    maxWeight: 50                      # massimo peso per la canary
    stepWeight: 10                     # incremento per step (10% alla volta)
    metrics:
      - name: request-success-rate
        thresholdRange:
          min: 99                      # minimo 99% di successo
        interval: 1m
      - name: request-duration
        thresholdRange:
          max: 500                     # massimo 500ms di latenza p99
        interval: 1m
    webhooks:
      - name: load-test
        type: rollout
        url: http://flagger-loadtester.test/
        timeout: 5s
        metadata:
          cmd: "hey -z 1m -q 10 -c 2 http://reviews.bookinfo:9080/"
```

```bash
# Monitorare lo stato del canary
kubectl get canary reviews -n bookinfo -w

# Output esempio:
# NAME      STATUS        WEIGHT   LASTTRANSITIONTIME
# reviews   Progressing   10       2024-01-15T10:30:00Z
# reviews   Progressing   20       2024-01-15T10:31:00Z
# reviews   Progressing   30       2024-01-15T10:32:00Z
# reviews   Succeeded     0        2024-01-15T10:35:00Z

# Descrivere gli eventi del canary
kubectl describe canary reviews -n bookinfo
```

### A/B Testing

L'A/B testing instrada il traffico in base a caratteristiche della request (header, cookie) invece che in base al peso percentuale.

```yaml
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews-ab-test
  namespace: bookinfo
spec:
  hosts:
    - reviews
  http:
    # Gruppo A: utenti con cookie ab-group=A
    - match:
        - headers:
            cookie:
              regex: ".*ab-group=A.*"
      route:
        - destination:
            host: reviews
            subset: v1
    # Gruppo B: utenti con cookie ab-group=B
    - match:
        - headers:
            cookie:
              regex: ".*ab-group=B.*"
      route:
        - destination:
            host: reviews
            subset: v2
    # Default: v1
    - route:
        - destination:
            host: reviews
            subset: v1
```

### Traffic Mirroring per Validation

Prima di instradare traffico reale alla nuova versione, il mirroring permette di validare il comportamento della nuova versione con traffico di produzione reale senza rischi.

```yaml
# Fase 1: Mirror del traffico per validazione (nessun impatto sugli utenti)
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews-validation
  namespace: bookinfo
spec:
  hosts:
    - reviews
  http:
    - route:
        - destination:
            host: reviews
            subset: v1
          weight: 100
      mirror:
        host: reviews
        subset: v2
      mirrorPercentage:
        value: 50.0                    # specchiare il 50% del traffico
```

```bash
# Confrontare le metriche tra v1 (produzione) e v2 (mirror)
# Error rate v1
kubectl exec -n istio-system deploy/prometheus -- \
  promtool query instant http://localhost:9090 \
  'sum(rate(istio_requests_total{destination_workload="reviews-v1",response_code=~"5.."}[10m]))'

# Error rate v2 (traffico mirror)
kubectl exec -n istio-system deploy/prometheus -- \
  promtool query instant http://localhost:9090 \
  'sum(rate(istio_requests_total{destination_workload="reviews-v2",response_code=~"5.."}[10m]))'
```

### Rollback Automatico Basato su Metriche

```yaml
# Flagger con rollback automatico
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: reviews-auto-rollback
  namespace: bookinfo
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: reviews
  service:
    port: 9080
  analysis:
    interval: 30s
    threshold: 3                       # dopo 3 metriche fallite -> rollback
    maxWeight: 50
    stepWeight: 10
    metrics:
      - name: request-success-rate
        thresholdRange:
          min: 99.0
        interval: 30s
      - name: request-duration
        thresholdRange:
          max: 500
        interval: 30s
      - name: "404s-percentage"        # metrica custom
        templateRef:
          name: not-found-percentage
          namespace: istio-system
        thresholdRange:
          max: 5
        interval: 30s
    alerts:
      - name: slack-notification
        severity: error
        providerRef:
          name: slack
          namespace: istio-system
---
# Metrica custom per Flagger
apiVersion: flagger.app/v1beta1
kind: MetricTemplate
metadata:
  name: not-found-percentage
  namespace: istio-system
spec:
  provider:
    type: prometheus
    address: http://prometheus.istio-system:9090
  query: |
    100 - sum(
      rate(istio_requests_total{
        reporter="destination",
        destination_workload_namespace="{{ namespace }}",
        destination_workload=~"{{ target }}",
        response_code!="404"
      }[{{ interval }}])
    ) / sum(
      rate(istio_requests_total{
        reporter="destination",
        destination_workload_namespace="{{ namespace }}",
        destination_workload=~"{{ target }}"
      }[{{ interval }}])
    ) * 100
```

---

## 10. Troubleshooting

### Problemi Comuni

#### 1. Sidecar Injection Failure

Il sidecar non viene iniettato nei Pod nonostante il namespace sia etichettato.

**Cause possibili**:
- Il namespace non ha la label `istio-injection=enabled`
- Il Pod ha l'annotazione `sidecar.istio.io/inject: "false"`
- Il webhook `istio-sidecar-injector` non e configurato o non e raggiungibile
- Il Pod e in un namespace di sistema (kube-system) che e escluso per default
- Problemi di risorse: il sidecar non viene schedulato per mancanza di CPU/memoria

```bash
# Verificare la label del namespace
kubectl get namespace default --show-labels

# Verificare il webhook
kubectl get mutatingwebhookconfigurations istio-sidecar-injector -o yaml

# Verificare che il Pod abbia il sidecar iniettato
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].name}'
# Output atteso: app-container istio-proxy

# Forzare l'injection manuale
kubectl get deployment reviews -n bookinfo -o yaml | \
  istioctl kube-inject -f - | kubectl apply -f -

# Controllare i log del sidecar injector
kubectl logs deploy/istiod -n istio-system | grep "injection"
```

#### 2. mTLS Handshake Errors

Errori di connessione TLS tra servizi, tipicamente manifesti come `connection reset by peer` o `upstream connect error`.

```bash
# Verificare la policy mTLS attiva per un namespace
kubectl get peerauthentication -n <namespace>

# Verificare se un servizio specifico ha mTLS attivo
istioctl authn tls-check <pod-name>.<namespace> <service>.<namespace>.svc.cluster.local

# Verificare lo stato dei certificati
istioctl proxy-config secret <pod-name> -n <namespace>

# Controllare la scadenza dei certificati
istioctl proxy-config secret <pod-name> -n <namespace> -o json | \
  jq -r '.dynamicActiveSecrets[].secret.tlsCertificate.certificateChain.inlineBytes' | \
  base64 -d | openssl x509 -noout -dates

# Scenario comune: un servizio senza sidecar tenta di connettersi
# a un servizio con PeerAuthentication STRICT.
# Soluzione: impostare PERMISSIVE temporaneamente o aggiungere il sidecar.
```

#### 3. Routing Misconfiguration

Il traffico non segue le regole di routing definite nelle VirtualService.

```bash
# Analizzare la configurazione con istioctl analyze
istioctl analyze -n bookinfo
# Identifica problemi comuni: host non trovati, conflitti tra VirtualService,
# subset non definiti nella DestinationRule

# Verificare la configurazione Envoy effettiva per un Pod
istioctl proxy-config routes <pod-name> -n <namespace>

# Verificare i cluster configurati nel proxy
istioctl proxy-config clusters <pod-name> -n <namespace>

# Verificare gli endpoint disponibili per un servizio
istioctl proxy-config endpoints <pod-name> -n <namespace> \
  --cluster "outbound|9080||reviews.bookinfo.svc.cluster.local"

# Dump completo della configurazione del proxy
istioctl proxy-config all <pod-name> -n <namespace> -o json > proxy-dump.json
```

#### 4. Performance Degradation

Latenza elevata o throughput ridotto dopo l'adozione del mesh.

```bash
# Verificare le risorse consumate dai sidecar
kubectl top pods -n <namespace> --containers | grep istio-proxy

# Controllare la dimensione della configurazione xDS
istioctl proxy-status
# La colonna CDS/EDS/LDS/RDS mostra il numero di risorse.
# Valori elevati (>1000) indicano un mesh sovradimensionato.

# Verificare il numero di connessioni attive
istioctl proxy-config listeners <pod-name> -n <namespace>

# Controllare il connection pool
istioctl proxy-config clusters <pod-name> -n <namespace> -o json | \
  jq '.[] | select(.name | contains("reviews")) | .circuitBreakers'

# Ottimizzare: limitare gli scope di discovery con Sidecar resource
```

```yaml
# Sidecar resource per limitare la visibilita del proxy
# Riduce la configurazione xDS e migliora le performance
apiVersion: networking.istio.io/v1
kind: Sidecar
metadata:
  name: reviews-sidecar
  namespace: bookinfo
spec:
  workloadSelector:
    labels:
      app: reviews
  egress:
    - hosts:
        - "./ratings.bookinfo.svc.cluster.local"
        - "./productpage.bookinfo.svc.cluster.local"
        - "istio-system/*"             # necessario per telemetria
```

### Comandi di Debug Essenziali

```bash
# Stato generale del mesh
istioctl proxy-status
# Output mostra: SYNCED (ok), NOT SENT (non configurato), STALE (non aggiornato)

# Analisi automatica della configurazione
istioctl analyze --all-namespaces
# Rileva: conflitti, risorse orfane, configurazioni non valide

# Verificare la versione del proxy di ogni Pod
istioctl proxy-status | awk '{print $1, $NF}'

# Confrontare la configurazione desiderata vs effettiva
istioctl proxy-config route <pod-name> -n <namespace> -o json --name 9080

# Dashboard diagnostica interattiva
istioctl dashboard envoy <pod-name> -n <namespace>

# Abilitare log di debug per un proxy specifico
istioctl proxy-config log <pod-name> -n <namespace> \
  --level connection:debug,http:debug,router:debug

# Ripristinare il livello di log
istioctl proxy-config log <pod-name> -n <namespace> --level info

# Trace di una request specifica
kubectl logs <pod-name> -c istio-proxy -n <namespace> | grep <request-id>
```

### Log Analysis

```bash
# Abilitare access log dettagliato per debug temporaneo
istioctl install --set meshConfig.accessLogFile=/dev/stdout \
  --set meshConfig.accessLogEncoding=JSON

# Filtrare i log per errori specifici
kubectl logs <pod-name> -c istio-proxy -n <namespace> | \
  grep -E '"response_code":(4|5)[0-9]{2}'

# Response flags comuni di Envoy:
# UH  = upstream host non raggiungibile
# UF  = upstream connection failure
# UO  = upstream overflow (circuit breaker aperto)
# NR  = no route configurata
# URX = request rifiutata per superamento retry
# DC  = downstream connection terminata
# RL  = rate limited
# UAEX = external authorization denied

# Analizzare i response flags
kubectl logs <pod-name> -c istio-proxy -n <namespace> | \
  grep -oP '"response_flags":"[^"]*"' | sort | uniq -c | sort -rn
```

---

## 11. Best Practices

### Adozione Graduale

Non attivare il service mesh sull'intero cluster in una volta. Seguire un approccio incrementale:

1. **Fase 0 — Preparazione**: installare il control plane, configurare il monitoring, formare il team sulle CRD fondamentali (VirtualService, DestinationRule, PeerAuthentication).

2. **Fase 1 — Osservazione**: abilitare il mesh su un namespace non critico con mTLS PERMISSIVE. Raccogliere metriche e verificare che il mesh funzioni correttamente senza impattare il traffico esistente.

3. **Fase 2 — Sicurezza**: passare gradualmente a mTLS STRICT, namespace per namespace, verificando che tutti i servizi comunichino correttamente.

4. **Fase 3 — Traffic Management**: introdurre VirtualService e DestinationRule per il routing avanzato (canary, traffic splitting).

5. **Fase 4 — Produzione completa**: estendere il mesh a tutti i namespace, con AuthorizationPolicy e configurazione completa dell'osservabilita.

### Namespace-Level Injection

Preferire l'injection a livello di namespace piuttosto che a livello di singolo Pod. Questo garantisce uniformita e riduce il rischio di dimenticare servizi non meshati.

```bash
# Abilitare injection per namespace
kubectl label namespace production istio-injection=enabled

# Escludere specifici Pod dall'injection se necessario
# (aggiungere annotazione al Pod)
```

```yaml
# Eccezione per Pod specifici
metadata:
  annotations:
    sidecar.istio.io/inject: "false"   # escludere questo Pod dall'injection
```

### Resource Limits per Sidecar

Configurare sempre limiti di risorse per i sidecar proxy per prevenire il consumo eccessivo di risorse e garantire la schedulazione prevedibile.

```yaml
# Configurazione globale dei limiti risorse per i sidecar
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  meshConfig:
    defaultConfig:
      concurrency: 2                   # thread worker Envoy (default: 2)
  values:
    global:
      proxy:
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 256Mi
---
# Override per un workload specifico ad alto traffico
apiVersion: v1
kind: Pod
metadata:
  annotations:
    sidecar.istio.io/proxyCPU: "250m"
    sidecar.istio.io/proxyCPULimit: "1000m"
    sidecar.istio.io/proxyMemory: "256Mi"
    sidecar.istio.io/proxyMemoryLimit: "512Mi"
```

### Versioning delle API

Utilizzare i subset di Istio per gestire versioni multiple delle API in modo trasparente.

```yaml
# Supportare multiple versioni API con routing basato su header
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: api-versioning
  namespace: production
spec:
  hosts:
    - api-service
  http:
    - match:
        - headers:
            api-version:
              exact: "v2"
      route:
        - destination:
            host: api-service
            subset: v2
    - match:
        - uri:
            prefix: /api/v2
      route:
        - destination:
            host: api-service
            subset: v2
    - route:
        - destination:
            host: api-service
            subset: v1
```

### Security Hardening

```yaml
# 1. Abilitare mTLS STRICT a livello mesh
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system
spec:
  mtls:
    mode: STRICT
---
# 2. Default deny per tutto il traffico
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: default-deny
  namespace: production
spec:
  {}                                   # nessuna regola = deny all
---
# 3. Consentire solo traffico esplicitamente autorizzato
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: allow-frontend
  namespace: production
spec:
  selector:
    matchLabels:
      app: backend
  action: ALLOW
  rules:
    - from:
        - source:
            principals:
              - "cluster.local/ns/production/sa/frontend"
      to:
        - operation:
            methods: ["GET"]
---
# 4. Bloccare traffico in uscita non autorizzato
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  meshConfig:
    outboundTrafficPolicy:
      mode: REGISTRY_ONLY
```

### Observability Baseline

Stabilire una baseline di osservabilita prima di adottare il mesh in produzione.

```bash
# Installare lo stack completo di osservabilita
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.22/samples/addons/prometheus.yaml
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.22/samples/addons/grafana.yaml
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.22/samples/addons/jaeger.yaml
kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.22/samples/addons/kiali.yaml

# Verificare che tutti gli addon siano funzionanti
kubectl get pods -n istio-system -l app.kubernetes.io/part-of=istio
```

Definire SLO (Service Level Objectives) basati sulle metriche del mesh:

```yaml
# Alert rule per violazione SLO (esempio: success rate < 99.9%)
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: mesh-slo-alerts
  namespace: istio-system
spec:
  groups:
    - name: mesh-slo
      rules:
        - alert: HighErrorRate
          expr: |
            sum(rate(istio_requests_total{reporter="destination",response_code=~"5.."}[5m]))
            by (destination_workload, destination_namespace)
            /
            sum(rate(istio_requests_total{reporter="destination"}[5m]))
            by (destination_workload, destination_namespace)
            > 0.001
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "Error rate superiore allo 0.1% per {{ $labels.destination_workload }}"
            description: "Il servizio {{ $labels.destination_workload }} nel namespace {{ $labels.destination_namespace }} ha un error rate del {{ $value | humanizePercentage }}."
        - alert: HighLatency
          expr: |
            histogram_quantile(0.99,
              sum(rate(istio_request_duration_milliseconds_bucket{reporter="destination"}[5m]))
              by (le, destination_workload, destination_namespace)
            ) > 1000
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Latenza P99 superiore a 1 secondo per {{ $labels.destination_workload }}"
```

### Quando NON Usare un Service Mesh

Nonostante i benefici, un service mesh non e sempre la scelta giusta. Evitarlo quando:

- **Il sistema ha meno di 10 microservizi**: l'overhead operativo supera i benefici. Utilizzare soluzioni piu leggere: librerie client-side per retry/circuit breaking (Resilience4j, Polly), service discovery nativo Kubernetes (CoreDNS), network policies per la sicurezza base.

- **Il team non ha competenze Kubernetes avanzate**: un service mesh aggiunge un layer significativo di complessita. Il debugging richiede comprensione di Envoy, xDS, iptables, mTLS. Senza queste competenze, i problemi di rete diventano opachi e difficili da diagnosticare.

- **L'applicazione e monolitica o legacy**: i service mesh sono progettati per architetture a microservizi. Aggiungere un sidecar a un monolito non fornisce benefici significativi e aggiunge solo overhead.

- **Budget limitato**: il consumo di risorse dei sidecar (RAM, CPU) e significativo. In cluster con vincoli di risorse stretti, il costo puo essere proibitivo.

- **Requisiti di latenza estremi**: per sistemi dove ogni millisecondo conta (trading ad alta frequenza, gaming real-time), l'overhead del proxy puo essere inaccettabile. Valutare soluzioni kernel-level (eBPF, Cilium) che operano a livello di rete senza proxy userspace.

---

## 12. Istio Ambient Mesh — Deep Dive

### Motivazioni Architetturali

L'architettura sidecar tradizionale di Istio, pur essendo funzionalmente completa, presenta limitazioni strutturali che emergono a scala:

- **Overhead di risorse per Pod**: ogni sidecar Envoy consuma 50-100MB di RAM e 0.1-0.5 vCPU. In un cluster con 1000 Pod, questo si traduce in 50-100GB di RAM e 100-500 vCPU dedicati esclusivamente ai proxy — un costo infrastrutturale significativo.
- **Accoppiamento del ciclo di vita**: il sidecar condivide il ciclo di vita del Pod. Aggiornare il proxy richiede il restart del Pod applicativo, con conseguente disruption del servizio. Questo rende gli aggiornamenti del data plane un'operazione rischiosa e lenta.
- **Complessita iptables**: l'intercettazione del traffico tramite regole iptables introduce complessita di debugging e puo interferire con applicazioni che gestiscono il proprio networking (es. database, sistemi di messaging).
- **Blast radius elevato**: un bug nel sidecar proxy impatta direttamente l'applicazione co-locata, poiche condividono lo stesso Pod e le stesse risorse.

Istio ambient mesh, disponibile in General Availability a partire dalla versione 1.22 (2024), risolve questi problemi separando le funzionalita di mesh in due layer distinti con cicli di vita indipendenti.

### Architettura a Due Layer

L'ambient mesh opera su un modello architetturale a due livelli che separa nettamente le responsabilita L4 (trasporto) e L7 (applicazione).

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Nodo Kubernetes                            │
│                                                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │  Pod A   │  │  Pod B   │  │  Pod C   │  │  Pod D   │          │
│  │ (no      │  │ (no      │  │ (no      │  │ (no      │          │
│  │  sidecar)│  │  sidecar)│  │  sidecar)│  │  sidecar)│          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│       │              │              │              │               │
│       └──────────────┼──────────────┼──────────────┘               │
│                      │              │                              │
│              ┌───────┴──────────────┴───────┐                      │
│              │        ztunnel (L4)          │ ← DaemonSet per nodo │
│              │  mTLS · AuthZ L4 · Metrics  │                      │
│              └─────────────┬───────────────┘                      │
│                            │ HBONE tunnel                         │
└────────────────────────────┼──────────────────────────────────────┘
                             │
                   ┌─────────┴─────────┐
                   │  Waypoint Proxy   │ ← Deployment opzionale
                   │  (Envoy L7)       │   per namespace/service
                   │  Routing · Policy │
                   │  Fault Injection  │
                   └───────────────────┘
```

### ztunnel — Il Proxy L4 per Nodo

ztunnel (Zero-Trust Tunnel) e il componente fondamentale dell'ambient mesh. Si tratta di un proxy L4 scritto in **Rust**, deployato come DaemonSet con un'istanza per nodo. Le sue responsabilita sono circoscritte e intenzionalmente limitate:

- **mTLS trasparente**: negozia e termina connessioni mTLS per tutti i Pod sul nodo, senza che le applicazioni debbano essere modificate. Ogni workload riceve un'identita SPIFFE (`spiffe://cluster.local/ns/<namespace>/sa/<service-account>`) e un certificato X.509 associato.
- **Autorizzazione L4**: applica AuthorizationPolicy di livello L4 (basate su IP sorgente, namespace, service account, porta di destinazione). Le policy L7 (basate su path HTTP, header, metodi) vengono delegate al waypoint proxy.
- **Telemetria L4**: genera metriche TCP (connessioni aperte/chiuse, byte trasferiti) e le espone a Prometheus.
- **Tunneling HBONE**: utilizza il protocollo HBONE (HTTP-Based Overlay Network Encapsulation), basato su HTTP/2 CONNECT, per incapsulare il traffico tra nodi. Questo protocollo trasporta il traffico mTLS attraverso la rete del cluster in modo efficiente.

Caratteristiche tecniche di ztunnel:

| Proprieta | Valore |
|---|---|
| **Linguaggio** | Rust |
| **Consumo RAM** | ~20-40MB per nodo (vs 50-100MB per sidecar Envoy per Pod) |
| **Consumo CPU** | ~0.05-0.1 vCPU a regime |
| **Protocollo tunnel** | HBONE (HTTP/2 CONNECT) |
| **Certificati** | X.509-SVID, rotazione automatica ogni 24h |
| **Scope** | L3/L4 esclusivamente |

```bash
# Verificare lo stato dei ztunnel nel cluster
kubectl get pods -n istio-system -l app=ztunnel -o wide

# Esaminare i log di ztunnel per un nodo specifico
kubectl logs -n istio-system -l app=ztunnel --field-selector spec.nodeName=node-1

# Verificare le connessioni HBONE attive
kubectl exec -n istio-system $(kubectl get pod -n istio-system -l app=ztunnel \
  --field-selector spec.nodeName=node-1 -o jsonpath='{.items[0].metadata.name}') \
  -- curl -s localhost:15020/debug/connections

# Metriche ztunnel esposte su porta 15020
kubectl exec -n istio-system <ztunnel-pod> -- curl -s localhost:15020/metrics | head -50
```

### Waypoint Proxy — L7 On-Demand

Il waypoint proxy e un deployment Envoy opzionale che gestisce le funzionalita L7. A differenza del sidecar tradizionale (uno per Pod), il waypoint proxy opera a livello di **namespace** o di **singolo servizio**, e viene deployato solo quando servono funzionalita L7.

Funzionalita gestite dal waypoint proxy:

- Routing basato su header, URI, metodo HTTP (VirtualService)
- Fault injection (delay, abort)
- Traffic mirroring
- Retry e timeout avanzati con condizioni L7
- AuthorizationPolicy L7 (basate su path, header, JWT claims)
- Header manipulation
- Rate limiting L7

```bash
# Creare un waypoint proxy per un intero namespace
istioctl waypoint apply --namespace production --name production-waypoint

# Creare un waypoint proxy per un servizio specifico
istioctl waypoint apply --namespace production --name reviews-waypoint \
  --for service --service-account reviews

# Verificare i waypoint proxy attivi
istioctl waypoint list --namespace production

# Verificare lo stato del waypoint proxy
kubectl get pods -n production -l gateway.networking.k8s.io/gateway-name=production-waypoint

# Eliminare un waypoint proxy quando le funzionalita L7 non servono piu
istioctl waypoint delete --namespace production --name production-waypoint
```

```yaml
# Waypoint proxy dichiarativo tramite Gateway API
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: production-waypoint
  namespace: production
  labels:
    istio.io/waypoint-for: service      # scope: service o namespace
spec:
  gatewayClassName: istio-waypoint
  listeners:
    - name: mesh
      port: 15008
      protocol: HBONE
```

### Flusso del Traffico in Ambient Mode

Il percorso di una request in ambient mesh attraversa piu componenti a seconda della necessita di elaborazione L7:

**Scenario L4-only (senza waypoint)**:
1. Il Pod sorgente invia traffico normalmente verso l'IP del servizio di destinazione.
2. ztunnel sul nodo sorgente intercetta il traffico tramite eBPF redirect (non iptables).
3. ztunnel stabilisce un tunnel HBONE con mTLS verso ztunnel sul nodo di destinazione.
4. ztunnel sul nodo di destinazione consegna il traffico al Pod target.

**Scenario L7 (con waypoint)**:
1. Il Pod sorgente invia traffico normalmente.
2. ztunnel sul nodo sorgente intercetta il traffico e rileva che il servizio di destinazione ha un waypoint associato.
3. ztunnel inoltra il traffico via HBONE al waypoint proxy.
4. Il waypoint proxy applica le policy L7 (routing, fault injection, authorization).
5. Il waypoint proxy inoltra il traffico via HBONE a ztunnel sul nodo di destinazione.
6. ztunnel consegna il traffico al Pod target.

### Migrazione da Sidecar ad Ambient

La migrazione da sidecar ad ambient puo avvenire gradualmente, namespace per namespace, e i due modelli possono coesistere nello stesso cluster.

```bash
# Step 1: Verificare la compatibilita del namespace
istioctl analyze -n production

# Step 2: Rimuovere la label di sidecar injection
kubectl label namespace production istio-injection-

# Step 3: Abilitare ambient mode
kubectl label namespace production istio.io/dataplane-mode=ambient

# Step 4: Riavviare i Pod per rimuovere i sidecar esistenti
kubectl rollout restart deployment -n production

# Step 5: Verificare che i sidecar siano stati rimossi
kubectl get pods -n production -o jsonpath='{range .items[*]}{.metadata.name}{": "}{.spec.containers[*].name}{"\n"}{end}'
# Non dovrebbe piu comparire "istio-proxy"

# Step 6: (Opzionale) Deployare waypoint proxy se servono funzionalita L7
istioctl waypoint apply --namespace production --name production-waypoint

# Step 7: Verificare la connettivita mTLS tramite ztunnel
kubectl exec -n production <pod> -- curl -s http://other-service:8080/health

# Rollback se necessario: tornare a sidecar
kubectl label namespace production istio.io/dataplane-mode-
kubectl label namespace production istio-injection=enabled
kubectl rollout restart deployment -n production
```

### Limitazioni Attuali di Ambient Mesh

- **Protocolli non-HTTP**: il waypoint proxy gestisce HTTP/1.1, HTTP/2 e gRPC. Protocolli custom o TCP puro sono gestiti a L4 da ztunnel ma senza le funzionalita L7. Per workload che utilizzano protocolli binari proprietari (es. protocolli gaming, IoT custom), le funzionalita di traffic management L7 non sono disponibili in ambient mode.
- **EnvoyFilter**: le risorse EnvoyFilter non sono supportate con i waypoint proxy. Per estensioni custom, utilizzare WasmPlugin. Questo impatta i team che hanno investito in filtri EnvoyFilter custom per la modalita sidecar — la migrazione richiede la riscrittura come moduli WASM.
- **Multi-network**: il supporto multi-network in ambient mesh e ancora in fase di maturazione rispetto alla modalita sidecar. Cluster che operano su reti diverse (es. VPC peering, multi-cloud) devono valutare attentamente la maturita del supporto per la propria topologia.
- **Debugging piu distribuito**: il traffico attraversa componenti su nodi diversi (ztunnel sorgente → waypoint → ztunnel destinazione), rendendo il debugging piu complesso rispetto al modello sidecar dove tutto passa per un singolo proxy co-locato. Strumenti come `istioctl proxy-config` funzionano in modo diverso con ztunnel rispetto ai sidecar Envoy.
- **Kernel requirements**: ztunnel richiede supporto eBPF nel kernel per l'intercettazione efficiente del traffico. Kernel piu vecchi (< 5.7) o ambienti con restrizioni eBPF (alcune configurazioni hardened) possono non supportare la modalita ambient.

---

## 13. Cilium Service Mesh — Architettura eBPF

### Cos'e Cilium e il Paradigma eBPF

Cilium e una soluzione di networking, osservabilita e sicurezza per Kubernetes basata interamente su **eBPF** (extended Berkeley Packet Filter). A differenza di Istio e Linkerd che operano nello userspace con proxy (Envoy o linkerd2-proxy), Cilium esegue la logica di networking direttamente nel **kernel Linux**, eliminando la necessita di sidecar proxy e riducendo drasticamente l'overhead.

eBPF consente di eseguire programmi sandboxed all'interno del kernel Linux senza modificarne il codice sorgente e senza caricare moduli kernel. I programmi eBPF vengono verificati staticamente dal kernel prima dell'esecuzione, garantendo sicurezza e stabilita. Questo approccio offre tre vantaggi fondamentali:

1. **Performance**: il processing del traffico avviene direttamente nel kernel, bypassando l'overhead dello stack di rete userspace. Il traffico non deve essere copiato tra kernel space e user space come avviene con i sidecar proxy.
2. **Efficienza risorse**: nessun container proxy aggiuntivo per Pod. Le funzionalita di mesh sono implementate a livello di nodo, condivise tra tutti i Pod.
3. **Visibilita profonda**: eBPF ha accesso diretto ai socket, ai pacchetti e alle syscall, fornendo un livello di osservabilita impossibile da ottenere con proxy userspace.

### Architettura Cilium Service Mesh

```
┌─────────────────────────────────────────────────────────────┐
│                     Nodo Kubernetes                         │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │  Pod A   │  │  Pod B   │  │  Pod C   │                 │
│  │ (no      │  │ (no      │  │ (no      │                 │
│  │ sidecar) │  │ sidecar) │  │ sidecar) │                 │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                 │
│       │              │              │                       │
│  ─────┴──────────────┴──────────────┴──── kernel boundary  │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           Cilium eBPF Data Plane (kernel)              │ │
│  │                                                        │ │
│  │  ┌─────────┐  ┌──────────┐  ┌───────────┐            │ │
│  │  │ L3/L4   │  │ mTLS     │  │ L7 Policy │            │ │
│  │  │ Policy  │  │ (WireGrd)│  │ (Envoy    │            │ │
│  │  │ Engine  │  │          │  │  on-demand)│            │ │
│  │  └─────────┘  └──────────┘  └───────────┘            │ │
│  │                                                        │ │
│  │  ┌──────────────────────────────────────────────────┐ │ │
│  │  │          Hubble (osservabilita)                   │ │ │
│  │  │  Flow logs · Metriche · Network graph            │ │ │
│  │  └──────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────┐                                     │
│  │ Cilium Agent      │ ← DaemonSet per nodo                │
│  │ (userspace)       │   Gestisce programmi eBPF            │
│  └───────────────────┘                                     │
└─────────────────────────────────────────────────────────────┘
```

Componenti principali:

- **Cilium Agent**: DaemonSet che gestisce il ciclo di vita dei programmi eBPF. Riceve la configurazione dal control plane Kubernetes e compila/carica i programmi eBPF nel kernel.
- **Cilium Operator**: gestisce risorse cluster-wide, allocazione IP (IPAM), garbage collection di risorse eBPF orfane.
- **Hubble**: layer di osservabilita che sfrutta eBPF per raccogliere flow log, metriche e tracce di rete senza overhead applicativo. Fornisce una UI web (Hubble UI) e una CLI (hubble).
- **Envoy proxy (opzionale)**: per le funzionalita L7 che eBPF non puo gestire direttamente (HTTP routing avanzato, header manipulation), Cilium utilizza un'istanza Envoy condivisa per nodo, non un sidecar per Pod.

### Installazione e Configurazione

```bash
# Installare Cilium CLI
CILIUM_CLI_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/cilium-cli/main/stable.txt)
curl -L --fail --remote-name-all \
  https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-linux-amd64.tar.gz
sudo tar xzvfC cilium-linux-amd64.tar.gz /usr/local/bin

# Installare Cilium con service mesh abilitato
cilium install --version 1.16.4 \
  --set kubeProxyReplacement=true \
  --set k8sServiceHost=<API_SERVER_IP> \
  --set k8sServicePort=6443

# Abilitare Hubble per osservabilita
cilium hubble enable --ui

# Verificare l'installazione
cilium status
cilium connectivity test
```

```yaml
# Installazione Helm con service mesh completo
# values-cilium-mesh.yaml
kubeProxyReplacement: true
k8sServiceHost: "api-server.example.com"
k8sServicePort: 6443

hubble:
  enabled: true
  relay:
    enabled: true
  ui:
    enabled: true
  metrics:
    enabled:
      - dns
      - drop
      - tcp
      - flow
      - port-distribution
      - icmp
      - httpV2:exemplars=true;labelsContext=source_ip,source_namespace,source_workload,destination_ip,destination_namespace,destination_workload,traffic_direction

# Abilitare mTLS via WireGuard (encryption trasparente)
encryption:
  enabled: true
  type: wireguard
  nodeEncryption: true        # cifrare anche traffico tra nodi

# Abilitare Envoy per L7 policy
envoy:
  enabled: true

# Gateway API support
gatewayAPI:
  enabled: true
```

```bash
# Installazione via Helm
helm repo add cilium https://helm.cilium.io/
helm install cilium cilium/cilium --version 1.16.4 \
  --namespace kube-system \
  --values values-cilium-mesh.yaml
```

### CiliumNetworkPolicy — Policy L3/L4/L7

Cilium estende le NetworkPolicy native di Kubernetes con CiliumNetworkPolicy, che supportano regole a tutti i livelli dello stack.

```yaml
# Policy L3/L4: limitare accesso per namespace e porta
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-frontend-to-api
  namespace: production
spec:
  endpointSelector:
    matchLabels:
      app: api-server
  ingress:
    - fromEndpoints:
        - matchLabels:
            app: frontend
            io.kubernetes.pod.namespace: production
      toPorts:
        - ports:
            - port: "8080"
              protocol: TCP
---
# Policy L7: filtrare per path HTTP e metodo
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: api-l7-policy
  namespace: production
spec:
  endpointSelector:
    matchLabels:
      app: api-server
  ingress:
    - fromEndpoints:
        - matchLabels:
            app: frontend
      toPorts:
        - ports:
            - port: "8080"
              protocol: TCP
          rules:
            http:
              - method: GET
                path: "/api/v1/.*"
              - method: POST
                path: "/api/v1/orders"
                headers:
                  - 'Content-Type: application/json'
---
# Policy DNS/FQDN: controllare egress per dominio
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-external-api
  namespace: production
spec:
  endpointSelector:
    matchLabels:
      app: payment-service
  egress:
    - toFQDNs:
        - matchName: "api.stripe.com"
        - matchName: "api.paypal.com"
      toPorts:
        - ports:
            - port: "443"
              protocol: TCP
    - toEndpoints:
        - matchLabels:
            io.kubernetes.pod.namespace: kube-system
            k8s-app: kube-dns
      toPorts:
        - ports:
            - port: "53"
              protocol: UDP
          rules:
            dns:
              - matchPattern: "*.stripe.com"
              - matchPattern: "*.paypal.com"
```

### Hubble — Osservabilita Kernel-Level

Hubble e il layer di osservabilita di Cilium. Sfrutta eBPF per raccogliere flow log completi di tutto il traffico nel cluster senza alcun overhead applicativo.

```bash
# Osservare i flussi di rete in tempo reale
hubble observe --namespace production --protocol http

# Filtrare per codice di risposta HTTP
hubble observe --namespace production --http-status 500-599

# Filtrare flussi tra due servizi specifici
hubble observe --from-label app=frontend --to-label app=api-server

# Esportare metriche per Prometheus
hubble observe --output json | jq '.flow | {src: .source.labels, dst: .destination.labels, verdict: .verdict}'

# Accedere alla UI di Hubble
cilium hubble ui

# Verificare le policy applicate e i drop
hubble observe --verdict DROPPED --namespace production
```

### Confronto Cilium vs Istio vs Linkerd

| Aspetto | Cilium | Istio (Ambient) | Linkerd |
|---|---|---|---|
| **Data plane** | eBPF (kernel) | ztunnel + waypoint (userspace) | linkerd2-proxy (userspace) |
| **Sidecar** | No | No | Si (leggero, Rust) |
| **Latenza aggiunta** | ~0.1-0.3ms | ~0.5-1.5ms | ~0.3-0.5ms |
| **RAM overhead/nodo** | ~150-250MB (agent) | ~20-40MB (ztunnel) | ~10-20MB per Pod |
| **mTLS** | WireGuard (L3) o IPsec | X.509 mTLS (L4) | X.509 mTLS |
| **L7 policy** | Envoy on-demand per nodo | Waypoint proxy on-demand | Service Profile |
| **Osservabilita** | Hubble (eBPF native) | Prometheus/Jaeger/Kiali | Linkerd Viz |
| **Gateway API** | Si (conformance v1.4) | Si (conformance) | Parziale |
| **Adozione cloud** | GKE, AKS, EKS default | OpenShift, molti distro | Indipendente |
| **Caso d'uso** | Performance-critical, platform | Feature-rich, enterprise | Semplicita, lightweight |

---

## 14. Sicurezza Avanzata — SPIFFE, SPIRE e Zero-Trust Identity

### Il Problema dell'Identita nei Microservizi

In un'architettura a microservizi, l'identita dei workload e il fondamento della sicurezza zero-trust. La domanda centrale e: "Come puo il servizio A verificare crittograficamente che sta comunicando con il servizio B legittimo, e non con un attaccante che ha compromesso la rete?"

Le soluzioni tradizionali — chiavi API statiche, certificati manuali, credenziali condivise — non scalano in ambienti dinamici dove i Pod vengono creati e distrutti continuamente. Servono identita **effimere**, **verificabili** e **automatiche**.

### SPIFFE — Secure Production Identity Framework for Everyone

SPIFFE e uno standard CNCF Graduated che definisce un framework per l'identita dei workload. Non e un'implementazione, ma una **specifica** che stabilisce:

**SPIFFE ID**: un identificatore univoco per ogni workload, nella forma di un URI:

```
spiffe://trust-domain/path

# Esempi concreti:
spiffe://cluster.local/ns/production/sa/payment-service
spiffe://mycompany.com/region/eu-west/service/api-gateway
spiffe://prod.example.org/k8s/cluster-1/ns/default/sa/frontend
```

Il trust domain (es. `cluster.local`) rappresenta il confine di fiducia. I workload all'interno dello stesso trust domain si fidano reciprocamente. La comunicazione tra trust domain diversi richiede bundle federation.

**SVID — SPIFFE Verifiable Identity Document**: il documento crittografico che incarna l'identita del workload. Esistono due formati:

- **X.509-SVID**: un certificato X.509 standard in cui lo SPIFFE ID e inserito nel campo Subject Alternative Name (SAN) come URI. Questo formato si integra nativamente con mTLS — ogni connessione TLS reciproca verifica automaticamente l'identita SPIFFE della controparte.
- **JWT-SVID**: un token JWT firmato che contiene lo SPIFFE ID nel claim `sub`. Utilizzato per scenari dove mTLS non e praticabile (es. comunicazione tramite load balancer L7 che terminano TLS).

Caratteristiche chiave degli SVID:
- **Breve durata**: tipicamente 1-24 ore, poi vengono ruotati automaticamente.
- **Nessun segreto statico**: eliminano la necessita di chiavi API, password o certificati a lungo termine.
- **Attestazione automatica**: il workload riceve la propria identita senza dover gestire credenziali.

### SPIRE — SPIFFE Runtime Environment

SPIRE e l'implementazione di riferimento CNCF Graduated di SPIFFE. E composto da due componenti:

**SPIRE Server**: l'autorita centrale che:
- Gestisce la CA (Certificate Authority) per la generazione degli SVID.
- Mantiene il registro delle identita (Registration Entries) che mappano i workload ai loro SPIFFE ID.
- Distribuisce i trust bundle per la federazione cross-domain.

**SPIRE Agent**: eseguito su ogni nodo (DaemonSet in Kubernetes), svolge tre funzioni:
- **Node attestation**: verifica l'identita del nodo su cui gira (tramite AWS IID, GCP metadata, token Kubernetes, TPM).
- **Workload attestation**: verifica l'identita del workload che richiede un SVID (tramite cgroup, namespace, service account, label Kubernetes).
- **SVID delivery**: consegna gli SVID ai workload tramite la Workload API (un Unix domain socket).

```
┌─────────────────────────────────────────────────────┐
│                  SPIRE Server                       │
│  ┌──────┐  ┌───────────────┐  ┌────────────────┐  │
│  │  CA  │  │ Registration  │  │ Trust Bundle   │  │
│  │      │  │ Entries       │  │ Federation     │  │
│  └──────┘  └───────────────┘  └────────────────┘  │
└──────────────────────┬──────────────────────────────┘
                       │ Node attestation
         ┌─────────────┼─────────────┐
         │             │             │
┌────────┴───┐  ┌──────┴─────┐  ┌───┴──────────┐
│ SPIRE Agent│  │ SPIRE Agent│  │ SPIRE Agent  │
│ (Nodo 1)   │  │ (Nodo 2)   │  │ (Nodo 3)     │
│            │  │            │  │              │
│ ┌────────┐ │  │ ┌────────┐ │  │ ┌────────┐   │
│ │Workload│ │  │ │Workload│ │  │ │Workload│   │
│ │API sock│ │  │ │API sock│ │  │ │API sock│   │
│ └────────┘ │  │ └────────┘ │  │ └────────┘   │
└────────────┘  └────────────┘  └──────────────┘
```

### Integrazione SPIFFE con Istio

Istio utilizza nativamente SPIFFE per l'identita dei workload. Istiod agisce come CA e genera automaticamente X.509-SVID per ogni proxy nel mesh. Lo SPIFFE ID viene codificato nel SAN del certificato.

```bash
# Verificare l'identita SPIFFE di un workload Istio
istioctl proxy-config secret deploy/reviews -n bookinfo -o json | \
  jq -r '.dynamicActiveSecrets[0].secret.tlsCertificate.certificateChain.inlineBytes' | \
  base64 -d | openssl x509 -noout -ext subjectAltName

# Output atteso:
# X509v3 Subject Alternative Name:
#   URI:spiffe://cluster.local/ns/bookinfo/sa/bookinfo-reviews
```

Per scenari piu complessi (multi-cluster, multi-cloud, ambienti ibridi), e possibile sostituire la CA interna di Istio con SPIRE:

```yaml
# Configurare Istio per utilizzare SPIRE come identity provider
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  meshConfig:
    trustDomain: mycompany.com
  values:
    pilot:
      env:
        EXTERNAL_CA: ISTIOD_RA_KUBERNETES_API
    global:
      caAddress: spire-server.spire-system.svc:8081
  components:
    pilot:
      k8s:
        env:
          - name: PILOT_CERT_PROVIDER
            value: spiffe
```

### Federazione Cross-Cluster con SPIFFE

La federazione SPIFFE consente a workload in trust domain diversi di autenticarsi reciprocamente:

```bash
# Sul cluster A: esportare il trust bundle
kubectl exec -n spire-system spire-server-0 -- \
  /opt/spire/bin/spire-server bundle show -format spiffe \
  > cluster-a-bundle.json

# Sul cluster B: registrare il trust bundle del cluster A
kubectl exec -n spire-system spire-server-0 -- \
  /opt/spire/bin/spire-server bundle set \
  -id spiffe://cluster-a.example.com \
  -path /run/spire/bundles/cluster-a-bundle.json

# Creare una registration entry per consentire la comunicazione federata
kubectl exec -n spire-system spire-server-0 -- \
  /opt/spire/bin/spire-server entry create \
  -spiffeID spiffe://cluster-b.example.com/ns/production/sa/api \
  -parentID spiffe://cluster-b.example.com/k8s-node \
  -selector k8s:ns:production \
  -selector k8s:sa:api \
  -federatesWith spiffe://cluster-a.example.com
```

---

## 15. Gateway API Integration

### Da Ingress a Gateway API

La Kubernetes **Gateway API** e il successore designato delle risorse Ingress e delle CRD proprietarie dei service mesh (VirtualService, DestinationRule di Istio). E un progetto ufficiale di Kubernetes SIG-Network che mira a fornire un'API unificata, espressiva e portabile per il routing del traffico.

Vantaggi rispetto alle API proprietarie:
- **Portabilita**: le stesse risorse funzionano con Istio, Cilium, Envoy Gateway, Kong, HAProxy e altri provider senza riscrivere la configurazione.
- **Separazione dei ruoli**: Gateway API distingue chiaramente tra infrastruttura (GatewayClass), configurazione cluster (Gateway) e routing applicativo (HTTPRoute), allineandosi ai ruoli organizzativi (platform team vs application team).
- **Espressivita**: supporta nativamente header matching, weight-based routing, URL rewriting, request mirroring e traffic splitting — funzionalita che con Ingress richiedevano annotazioni proprietarie.

### Risorse Fondamentali

```
GatewayClass (infrastruttura)
  └── Gateway (punto di ingresso)
        └── HTTPRoute (routing applicativo)
        └── GRPCRoute (routing gRPC)
        └── TCPRoute (routing TCP)
        └── TLSRoute (routing TLS)
```

**GatewayClass**: definisce il tipo di gateway (chi lo implementa). Equivalente a IngressClass.

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: istio
spec:
  controllerName: istio.io/gateway-controller
```

**Gateway**: un'istanza concreta del gateway. Definisce listener, porte, TLS.

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: production-gateway
  namespace: production
spec:
  gatewayClassName: istio
  listeners:
    - name: https
      port: 443
      protocol: HTTPS
      tls:
        mode: Terminate
        certificateRefs:
          - name: production-tls-cert
      allowedRoutes:
        namespaces:
          from: Selector
          selector:
            matchLabels:
              gateway-access: "true"
    - name: http
      port: 80
      protocol: HTTP
      allowedRoutes:
        namespaces:
          from: Same
```

**HTTPRoute**: regole di routing L7 (il sostituto portabile di VirtualService).

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: reviews-route
  namespace: bookinfo
spec:
  parentRefs:
    - name: production-gateway
      namespace: production
  hostnames:
    - "bookinfo.example.com"
  rules:
    # Canary: 90/10 traffic split
    - backendRefs:
        - name: reviews-v1
          port: 9080
          weight: 90
        - name: reviews-v2
          port: 9080
          weight: 10
    # Header-based routing per beta tester
    - matches:
        - headers:
            - name: x-beta-tester
              value: "true"
      backendRefs:
        - name: reviews-v2
          port: 9080
    # URL-based routing
    - matches:
        - path:
            type: PathPrefix
            value: /api/v2
      backendRefs:
        - name: api-v2
          port: 8080
      filters:
        - type: RequestHeaderModifier
          requestHeaderModifier:
            add:
              - name: x-api-version
                value: "v2"
```

### GAMMA — Gateway API per Mesh e Altro

L'iniziativa **GAMMA** (Gateway API for Mesh Management and Administration) estende la Gateway API per gestire il traffico **east-west** (service-to-service) oltre al tradizionale traffico **north-south** (ingress). Questo significa che le stesse risorse HTTPRoute usate per configurare l'ingress possono gestire il routing tra servizi interni al mesh.

```yaml
# HTTPRoute per traffico east-west (service mesh)
# Nessun parentRef verso un Gateway: il mesh stesso agisce come parent
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: reviews-mesh-route
  namespace: bookinfo
spec:
  parentRefs:
    - group: ""
      kind: Service
      name: reviews                      # il Service e il "parent" per east-west
  rules:
    - matches:
        - headers:
            - name: x-canary
              value: "true"
      backendRefs:
        - name: reviews-v2
          port: 9080
    - backendRefs:
        - name: reviews-v1
          port: 9080
          weight: 95
        - name: reviews-v2
          port: 9080
          weight: 5
```

### GRPCRoute

```yaml
# Routing specifico per servizi gRPC
apiVersion: gateway.networking.k8s.io/v1
kind: GRPCRoute
metadata:
  name: grpc-reviews
  namespace: bookinfo
spec:
  parentRefs:
    - name: production-gateway
      namespace: production
  hostnames:
    - "grpc.bookinfo.example.com"
  rules:
    - matches:
        - method:
            service: bookinfo.Reviews
            method: GetReviews
      backendRefs:
        - name: reviews-grpc
          port: 50051
    - matches:
        - method:
            service: bookinfo.Reviews
            method: SubmitReview
      backendRefs:
        - name: reviews-grpc-write
          port: 50052
```

### Migrazione da VirtualService a Gateway API

La migrazione dalle CRD proprietarie di Istio alla Gateway API puo avvenire gradualmente. Istio supporta entrambe le API simultaneamente.

```yaml
# PRIMA: Istio VirtualService (proprietario)
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews-routing
spec:
  hosts:
    - reviews
  http:
    - match:
        - headers:
            x-beta: { exact: "true" }
      route:
        - destination: { host: reviews, subset: v2 }
    - route:
        - destination: { host: reviews, subset: v1, weight: 90 }
        - destination: { host: reviews, subset: v2, weight: 10 }

# DOPO: Gateway API HTTPRoute (standard, portabile)
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: reviews-routing
spec:
  parentRefs:
    - group: ""
      kind: Service
      name: reviews
  rules:
    - matches:
        - headers:
            - name: x-beta
              value: "true"
      backendRefs:
        - name: reviews-v2
          port: 9080
    - backendRefs:
        - name: reviews-v1
          port: 9080
          weight: 90
        - name: reviews-v2
          port: 9080
          weight: 10
```

Strategia di migrazione raccomandata:

1. **Installare le CRD Gateway API** nel cluster (`kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.0/standard-install.yaml`).
2. **Creare le risorse Gateway API in parallelo** alle risorse Istio esistenti. Entrambe coesistono senza conflitti.
3. **Verificare** che il routing tramite Gateway API funzioni identicamente.
4. **Rimuovere gradualmente** le VirtualService e DestinationRule proprietarie.
5. **Mantenere** le risorse Istio-specifiche (PeerAuthentication, AuthorizationPolicy) che non hanno ancora equivalenti nella Gateway API.

### Stato di Conformance per Provider (2025)

| Provider | Gateway API Version | Conformance Level |
|---|---|---|
| Istio | v1.2+ | Full (incluso GAMMA) |
| Cilium | v1.4 | Full |
| Envoy Gateway | v1.2+ | Full |
| Kong | v1.1+ | Full |
| Linkerd | v1.0 | Parziale (HTTPRoute) |
| HAProxy Ingress | v1.0 | Parziale |

---

## 16. Performance Impact e Benchmarks Comparativi

### Metodologia di Benchmarking

Per valutare l'impatto reale di un service mesh sulle performance, e necessario misurare tre dimensioni:

1. **Latenza**: il tempo aggiuntivo introdotto dal mesh per ogni request (misurato ai percentili P50, P95, P99).
2. **Throughput**: la capacita massima del sistema in request per secondo (RPS) prima della saturazione.
3. **Consumo risorse**: CPU e RAM aggiuntivi consumati dai componenti del mesh.

Strumenti di benchmarking consigliati:

```bash
# Fortio (sviluppato dal team Istio) — benchmark HTTP/gRPC
fortio load -c 64 -qps 1000 -t 60s -json results.json \
  http://reviews.bookinfo.svc.cluster.local:9080/

# Vegeta — load testing HTTP
echo "GET http://reviews:9080/" | vegeta attack -duration=60s -rate=500/s | \
  vegeta report -type=text

# wrk2 — benchmark a rate fisso con latenza accurata
wrk2 -t4 -c64 -d60s -R1000 --latency http://reviews:9080/

# hey — load testing semplice con distribuzione latenza
hey -z 60s -q 500 -c 50 http://reviews:9080/
```

### Benchmarks Comparativi (dati 2025)

I seguenti dati provengono da benchmark indipendenti condotti in condizioni controllate (cluster dedicato, carico uniforme, applicazione di riferimento identica) su Kubernetes 1.30.

#### Latenza Aggiuntiva (P99, carico 200 RPS)

| Soluzione | P99 Latenza vs Baseline | Delta Assoluto |
|---|---|---|
| **No mesh (baseline)** | — | 3.2ms |
| **Linkerd 2.x** | +0.5ms | 3.7ms |
| **Cilium (eBPF)** | +0.3-0.8ms | 3.5-4.0ms |
| **Istio Ambient** | +1.0-1.5ms | 4.2-4.7ms |
| **Istio Sidecar** | +2.5-5.0ms | 5.7-8.2ms |

A carichi elevati (2000+ RPS), la differenza tra Istio sidecar e gli altri si amplifica significativamente. Istio sidecar mostra fino a 22ms di latenza aggiuntiva al P99 rispetto a Linkerd.

#### Impatto mTLS sulla Latenza

L'abilitazione di mTLS ha un costo misurabile che varia per implementazione:

| Soluzione | Incremento Latenza con mTLS |
|---|---|
| **Istio Sidecar** | +166% rispetto a senza mTLS |
| **Cilium (WireGuard)** | +99% |
| **Linkerd** | +33% |
| **Istio Ambient** | +8% |

L'ambient mesh mostra l'overhead mTLS piu basso perche ztunnel e ottimizzato specificamente per la gestione TLS e opera con un codice Rust molto piu snello rispetto a Envoy.

#### Consumo Risorse per Cluster (100 Pod)

| Soluzione | RAM Totale Mesh | CPU Totale Mesh |
|---|---|---|
| **Istio Sidecar** | 5-10GB (100 sidecar × 50-100MB) | 10-50 vCPU |
| **Istio Ambient** | 200-600MB (ztunnel DaemonSet) | 0.5-2 vCPU |
| **Linkerd** | 1-2GB (100 sidecar × 10-20MB) | 2-5 vCPU |
| **Cilium** | 500MB-1GB (agent DaemonSet) | 0.5-3 vCPU |

### Impatto sulle Risorse per Nodo

```bash
# Misurare il consumo dei componenti mesh per nodo
# Sidecar Envoy (Istio)
kubectl top pods -n production --containers | grep istio-proxy | \
  awk '{sum_cpu+=$3; sum_mem+=$4; count++} END {printf "Avg CPU: %dm, Avg MEM: %dMi, Count: %d\n", sum_cpu/count, sum_mem/count, count}'

# ztunnel (Istio Ambient)
kubectl top pods -n istio-system -l app=ztunnel

# Cilium Agent
kubectl top pods -n kube-system -l k8s-app=cilium

# Linkerd proxy
kubectl top pods -n production --containers | grep linkerd-proxy
```

### Ottimizzazione delle Performance

Strategie per ridurre l'impatto del mesh sulle performance:

**1. Limitare lo scope di discovery con Sidecar resource (Istio)**

La risorsa Sidecar limita la configurazione xDS inviata a ciascun proxy. Per default, ogni sidecar riceve la configurazione di TUTTI i servizi nel mesh — un problema significativo in cluster con centinaia di servizi.

```yaml
# Ridurre la configurazione xDS: il proxy di reviews vede solo i servizi necessari
apiVersion: networking.istio.io/v1
kind: Sidecar
metadata:
  name: reviews-sidecar
  namespace: bookinfo
spec:
  workloadSelector:
    labels:
      app: reviews
  egress:
    - hosts:
        - "./ratings.bookinfo.svc.cluster.local"
        - "istio-system/*"
```

**2. Tuning del connection pool**

```yaml
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: reviews-performance
  namespace: bookinfo
spec:
  host: reviews
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 200
        connectTimeout: 10ms
        tcpKeepalive:
          time: 7200s
          interval: 75s
      http:
        h2UpgradePolicy: DEFAULT
        http2MaxRequests: 500
        maxRequestsPerConnection: 100
        idleTimeout: 60s
```

**3. Concurrency tuning per Envoy**

```yaml
# Ridurre il numero di worker thread Envoy per workload a basso traffico
apiVersion: v1
kind: Pod
metadata:
  annotations:
    proxy.istio.io/config: |
      concurrency: 1                      # 1 thread invece del default 2
```

**4. Protocol detection bypass**

```yaml
# Dichiarare esplicitamente il protocollo per evitare il detection overhead
apiVersion: v1
kind: Service
metadata:
  name: reviews
spec:
  ports:
    - name: http-web                       # prefisso "http-" = protocol sniffing disabilitato
      port: 9080
      targetPort: 9080
      protocol: TCP
```

---

## 17. Testing del Service Mesh

### Strategia di Testing

Il testing di un service mesh richiede un approccio multi-livello che copra configurazione, sicurezza, resilienza e performance. Un mesh mal configurato puo causare outage diffusi perche impatta tutto il traffico del cluster.

### Test di Configurazione

Validare la configurazione Istio prima di applicarla in produzione:

```bash
# Analisi statica della configurazione (istioctl analyze)
# Rileva: conflitti tra VirtualService, subset mancanti, policy orfane
istioctl analyze -n production --all-namespaces

# Dry-run: verificare la configurazione senza applicarla
kubectl apply -f virtual-service.yaml --dry-run=server

# Validare la sintassi delle risorse Istio
istioctl validate -f virtual-service.yaml

# Verificare la configurazione effettiva applicata a un proxy
istioctl proxy-config routes deploy/reviews -n bookinfo -o json
```

### Test di Connettivita e mTLS

Verificare che mTLS sia correttamente attivo e che le AuthorizationPolicy funzionino:

```bash
# Verificare che la connessione tra due servizi sia mTLS
istioctl proxy-config secret deploy/reviews -n bookinfo

# Test di connettivita da dentro il mesh
kubectl exec deploy/productpage -n bookinfo -- \
  curl -sS -o /dev/null -w "%{http_code}" http://reviews:9080/

# Test di connettivita da fuori il mesh (deve fallire con mTLS STRICT)
kubectl run test-pod --image=curlimages/curl --restart=Never --rm -it -- \
  curl -sS -o /dev/null -w "%{http_code}" http://reviews.bookinfo:9080/
# Atteso: connection reset (il Pod senza sidecar non puo comunicare con mTLS STRICT)

# Verificare le AuthorizationPolicy con test positivi e negativi
# Test positivo: frontend -> backend (consentito)
kubectl exec deploy/frontend -n production -- \
  curl -sS -w "\n%{http_code}" http://backend:8080/api/v1/data
# Atteso: 200

# Test negativo: database -> backend (non consentito)
kubectl exec deploy/database -n production -- \
  curl -sS -w "\n%{http_code}" http://backend:8080/api/v1/data
# Atteso: 403 RBAC: access denied
```

### Chaos Engineering con Fault Injection

Utilizzare il fault injection del mesh per validare la resilienza dell'applicazione in modo controllato:

```yaml
# Test plan: verificare che il frontend gestisca timeout del backend
# Step 1: Iniettare delay nel servizio reviews
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews-chaos-test
  namespace: bookinfo
spec:
  hosts:
    - reviews
  http:
    - fault:
        delay:
          percentage:
            value: 100.0                  # 100% delle request
          fixedDelay: 10s                  # delay di 10 secondi
      route:
        - destination:
            host: reviews
            subset: v1
---
# Step 2: Verificare che il frontend mostri un errore graceful
# (non un timeout del browser, ma un messaggio di fallback)
# Step 3: Verificare che il circuit breaker si attivi
# Step 4: Rimuovere il fault e verificare il recovery
```

```bash
# Monitorare l'impatto del fault injection sulle metriche
watch -n 5 'kubectl exec -n istio-system deploy/prometheus -- \
  promtool query instant http://localhost:9090 \
  "histogram_quantile(0.99, sum(rate(istio_request_duration_milliseconds_bucket{destination_workload=\"reviews\"}[1m])) by (le))"'

# Verificare che il circuit breaker si sia attivato
kubectl exec deploy/productpage -n bookinfo -c istio-proxy -- \
  curl -s localhost:15000/clusters | grep reviews | grep "outlier"
```

### Test di Circuit Breaking

```bash
# Generare carico per verificare il circuit breaking
# Configurazione: maxConnections=50, http2MaxRequests=50
# Inviare 100 connessioni simultanee per triggare il circuit breaker
fortio load -c 100 -qps 0 -t 30s -loglevel warning \
  http://reviews.bookinfo:9080/

# Verificare le metriche di overflow (circuit breaker attivato)
kubectl exec deploy/productpage -n bookinfo -c istio-proxy -- \
  curl -s localhost:15000/stats | grep "upstream_rq_pending_overflow"
# Un valore > 0 indica che il circuit breaker ha rifiutato request

# Verificare gli host espulsi dall'outlier detection
kubectl exec deploy/productpage -n bookinfo -c istio-proxy -- \
  curl -s localhost:15000/clusters | grep -A 5 "reviews" | grep "health_flags"
```

### Test di Traffic Splitting

Verificare che il traffic splitting funzioni con le percentuali configurate:

```bash
# Inviare 1000 request e contare la distribuzione
for i in $(seq 1 1000); do
  kubectl exec deploy/productpage -n bookinfo -- \
    curl -sS -o /dev/null -w "%{http_code}\n" http://reviews:9080/ 2>/dev/null
done | sort | uniq -c

# Analisi del traffic splitting tramite metriche Istio
kubectl exec -n istio-system deploy/prometheus -- \
  promtool query instant http://localhost:9090 \
  'sum(rate(istio_requests_total{destination_workload=~"reviews-.*",reporter="destination"}[5m])) by (destination_workload)'
# Verificare che il rapporto tra reviews-v1 e reviews-v2 corrisponda ai weight configurati
```

### Test Pre-Produzione Automatizzati

Integrare i test del mesh nella pipeline CI/CD:

```yaml
# Esempio di Job Kubernetes per test automatizzati del mesh
apiVersion: batch/v1
kind: Job
metadata:
  name: mesh-smoke-test
  namespace: test
spec:
  backoffLimit: 2
  template:
    spec:
      serviceAccountName: mesh-tester
      containers:
        - name: mesh-test
          image: curlimages/curl:latest
          command:
            - /bin/sh
            - -c
            - |
              set -e
              echo "Test 1: Connettivita base"
              curl -sf http://reviews.bookinfo:9080/ > /dev/null || exit 1

              echo "Test 2: mTLS enforcement (atteso 000/reset da Pod non-mesh)"
              # Questo test passa solo se il Pod corrente NON ha il sidecar
              # e il servizio target ha mTLS STRICT
              STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
                http://strict-service.production:8080/ 2>/dev/null || echo "000")
              [ "$STATUS" = "000" ] || exit 1

              echo "Test 3: AuthorizationPolicy (atteso 403)"
              STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
                http://restricted-service.production:8080/admin)
              [ "$STATUS" = "403" ] || exit 1

              echo "Tutti i test superati"
      restartPolicy: Never
```

### Conformance Testing

Verificare che l'implementazione del mesh rispetti le specifiche:

```bash
# Istio: verificare la conformance con il profilo installato
istioctl verify-install

# Cilium: test di connettivita e conformance
cilium connectivity test

# Gateway API: test di conformance per il provider
# (richiede il suite di test ufficiale del progetto Gateway API)
go test -v ./conformance/... -gateway-class=istio \
  -supported-features=HTTPRoute,GRPCRoute,TLSRoute
```

---

## 18. Strategie di Migrazione

### Valutazione Pre-Migrazione

Prima di introdurre un service mesh in un cluster esistente, e necessaria una valutazione sistematica:

**1. Inventario dei servizi**

```bash
# Mappare tutti i servizi e le loro dipendenze
kubectl get services --all-namespaces -o custom-columns=\
  NAMESPACE:.metadata.namespace,NAME:.metadata.name,\
  TYPE:.spec.type,PORTS:.spec.ports[*].port

# Identificare i protocolli utilizzati (HTTP, gRPC, TCP raw)
# Servizi con nomi porta non standard possono richiedere configurazione extra
kubectl get services --all-namespaces -o json | \
  jq -r '.items[] | "\(.metadata.namespace)/\(.metadata.name): \(.spec.ports[].name // "unnamed")"'

# Contare i Pod per namespace (stima dell'overhead sidecar)
kubectl get pods --all-namespaces --field-selector status.phase=Running | \
  awk '{print $1}' | sort | uniq -c | sort -rn
```

**2. Compatibilita applicativa**

Verificare le applicazioni per potenziali incompatibilita:

- **Applicazioni che gestiscono TLS internamente**: se un servizio gia implementa mTLS (es. database con TLS client cert), il double-encryption con il sidecar puo causare problemi. Opzione: disabilitare mTLS per porte specifiche tramite `portLevelMtls`.
- **Protocolli non-HTTP**: MySQL, MongoDB, Redis, Kafka usano protocolli binari. Il sidecar li gestisce come traffico TCP opaco — funziona, ma senza le funzionalita L7.
- **Applicazioni con server-first protocols**: protocolli dove il server invia dati prima del client (es. MySQL greeting packet) possono richiedere configurazione specifica.
- **Init containers che fanno networking**: le regole iptables del sidecar vengono installate prima dell'avvio dei container applicativi, ma gli init container eseguono prima del sidecar. Le connessioni di rete dagli init container possono fallire.

### Pattern di Migrazione Graduale

#### Pattern 1: Namespace-by-Namespace

Il pattern piu sicuro e la migrazione namespace per namespace, partendo dagli ambienti meno critici.

```bash
# Fase 1: Installare il control plane senza injection attiva
istioctl install --set profile=default -y

# Fase 2: Ambiente di staging/test
kubectl label namespace staging istio-injection=enabled
kubectl rollout restart deployment -n staging
# Monitorare per 1-2 settimane

# Fase 3: Servizi interni non critici
kubectl label namespace internal-tools istio-injection=enabled
kubectl rollout restart deployment -n internal-tools
# Monitorare per 1 settimana

# Fase 4: Produzione - servizi non customer-facing
kubectl label namespace batch-processing istio-injection=enabled
kubectl rollout restart deployment -n batch-processing

# Fase 5: Produzione - servizi customer-facing
# Utilizzare mTLS PERMISSIVE durante la transizione
kubectl apply -f - <<EOF
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: PERMISSIVE
EOF

kubectl label namespace production istio-injection=enabled
kubectl rollout restart deployment -n production
# Monitorare attentamente metriche e latenza

# Fase 6: Passare a mTLS STRICT solo dopo che tutti i servizi sono nel mesh
kubectl apply -f - <<EOF
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT
EOF
```

#### Pattern 2: Canary del Mesh Stesso

Utilizzare il traffic splitting per testare il mesh su un sottoinsieme di traffico:

```bash
# Deployare una seconda istanza del servizio con sidecar
# mentre l'istanza originale rimane senza sidecar
kubectl apply -f reviews-with-sidecar.yaml -n production

# Usare un Kubernetes Service con due deployment:
# reviews-no-mesh (deployment originale, senza sidecar)
# reviews-meshed (deployment con sidecar)
# Il Service bilancia tra i due, creando una canary del mesh
```

#### Pattern 3: Migrazione da Sidecar ad Ambient

Per cluster che gia utilizzano Istio con sidecar e vogliono passare ad ambient mesh:

```bash
# Pre-requisito: Istio >= 1.22 con supporto ambient
# Il cluster deve supportare eBPF (kernel >= 5.7 consigliato)

# Step 1: Installare i componenti ambient (ztunnel)
istioctl install --set profile=ambient -y
# Questo non impatta i namespace con sidecar esistenti

# Step 2: Migrare un namespace non critico
# Rimuovere sidecar injection e abilitare ambient
kubectl label namespace staging istio-injection-
kubectl label namespace staging istio.io/dataplane-mode=ambient
kubectl rollout restart deployment -n staging

# Step 3: Verificare la connettivita
istioctl proxy-status
kubectl exec -n staging deploy/test-app -- curl -s http://other-service:8080/

# Step 4: Se servono funzionalita L7, deployare un waypoint
istioctl waypoint apply --namespace staging --name staging-waypoint

# Step 5: Monitorare le metriche per 1-2 settimane
# Confrontare latenza P99, error rate, throughput con i dati pre-migrazione

# Step 6: Ripetere per i namespace successivi
# L'ordine consigliato: staging -> internal -> batch -> production
```

### Migrazione da un Mesh a un Altro

Lo scenario piu complesso: migrare da Istio a Cilium (o viceversa). Strategie:

**1. Gateway API come layer di astrazione**

Se le regole di routing sono gia definite con Gateway API (HTTPRoute), la migrazione tra provider e trasparente: basta cambiare la GatewayClass.

```yaml
# Cambiare da Istio a Cilium: unico cambio necessario
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: mesh-gateway
spec:
  controllerName: io.cilium/gateway-controller    # era: istio.io/gateway-controller
```

**2. Migrazione delle policy di sicurezza**

Le AuthorizationPolicy di Istio devono essere tradotte in CiliumNetworkPolicy:

```yaml
# Istio AuthorizationPolicy
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: allow-frontend
  namespace: production
spec:
  selector:
    matchLabels:
      app: backend
  action: ALLOW
  rules:
    - from:
        - source:
            principals: ["cluster.local/ns/production/sa/frontend"]
      to:
        - operation:
            methods: ["GET"]
            paths: ["/api/v1/*"]

# Equivalente CiliumNetworkPolicy
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-frontend
  namespace: production
spec:
  endpointSelector:
    matchLabels:
      app: backend
  ingress:
    - fromEndpoints:
        - matchLabels:
            app: frontend
            io.kubernetes.pod.namespace: production
      toPorts:
        - ports:
            - port: "8080"
              protocol: TCP
          rules:
            http:
              - method: GET
                path: "/api/v1/.*"
```

### Checklist di Migrazione

Prima di dichiarare la migrazione completata:

- [ ] Tutti i servizi nel mesh comunicano correttamente (test di connettivita)
- [ ] mTLS e attivo e verificato su tutte le connessioni (istioctl/hubble)
- [ ] Le metriche di osservabilita (Prometheus, Grafana) mostrano dati coerenti
- [ ] La latenza P99 e entro i limiti accettabili (confronto pre/post mesh)
- [ ] Le AuthorizationPolicy sono testate con test positivi e negativi
- [ ] Il circuit breaking e configurato per i servizi critici
- [ ] I runbook di troubleshooting sono aggiornati con i comandi specifici del mesh
- [ ] Il team ha completato il training sulle CRD e sugli strumenti di debug
- [ ] I dashboard di monitoring includono le metriche del mesh
- [ ] Il piano di rollback e documentato e testato
- [ ] Le risorse del cluster sono sufficienti (accounting dell'overhead del mesh)
- [ ] Gli alert sono configurati per degradazione del mesh (istiod down, ztunnel crash, Cilium agent restart)

### Anti-Pattern di Migrazione

Errori comuni da evitare:

- **Big bang**: attivare il mesh su tutti i namespace contemporaneamente. Un errore di configurazione impatta l'intero cluster.
- **Saltare mTLS PERMISSIVE**: passare direttamente a STRICT senza una fase PERMISSIVE causa outage per i servizi che non hanno ancora il sidecar.
- **Ignorare gli init container**: i container di inizializzazione che fanno chiamate di rete falliranno se il sidecar non e ancora pronto.
- **Non testare il rollback**: il piano di rollback deve essere verificato prima della migrazione, non durante un incidente.
- **Sottodimensionare le risorse**: non tenere conto dell'overhead dei sidecar porta a OOM kill e scheduling failure.
- **Migrare senza baseline**: senza metriche di performance pre-mesh, e impossibile valutare l'impatto della migrazione.

---

## Esercizi

1. **Installazione e configurazione Istio** — Installare Istio con profilo `demo` su un cluster Kubernetes locale (kind o k3d con almeno 4GB RAM). Deployare l'applicazione Bookinfo, abilitare l'injection del sidecar Envoy e verificare che il traffico tra servizi passi attraverso i proxy con `istioctl proxy-status`.

2. **Traffic management avanzato** — Partendo dall'applicazione Bookinfo, configurare: un VirtualService con routing basato su header (utenti beta → v2), un DestinationRule con circuit breaking (maxConnections: 100, consecutiveErrors: 5), e un canary deployment 90/10 tra v1 e v2 di un servizio. Verificare con `curl` e metriche Istio.

3. **mTLS e authorization policy** — Abilitare mTLS strict mode nel mesh. Creare AuthorizationPolicy che consenta solo comunicazioni specifiche tra servizi (es. frontend → productpage → reviews, ma non frontend → details diretto). Verificare con test di connettività che le policy siano enforced.

4. **Fault injection e resilienza** — Configurare fault injection tramite VirtualService: aggiungere 500ms di delay al 50% delle richieste verso un servizio e abort HTTP 503 al 10%. Osservare l'impatto sulle metriche e implementare retry e timeout nel servizio chiamante per mitigare i fault.

5. **Confronto Istio vs Cilium** — Su due cluster separati, deployare la stessa applicazione con Istio (sidecar) e con Cilium service mesh (eBPF, senza sidecar). Confrontare: consumo risorse (CPU/RAM per pod), latenza aggiunta (P50, P99), facilità di configurazione e debugging. Documentare i trade-off.

---

## Letture e Riferimenti

### Documentazione ufficiale

- Istio Documentation: <https://istio.io/latest/docs/> (consultato: 2026-05-24)
- Cilium Documentation: <https://docs.cilium.io/en/stable/> (consultato: 2026-05-24)
- Linkerd Documentation: <https://linkerd.io/2/overview/> (consultato: 2026-05-24)
- Envoy Proxy Documentation: <https://www.envoyproxy.io/docs/envoy/latest/> (consultato: 2026-05-24)
- Istio — Security best practices: <https://istio.io/latest/docs/ops/best-practices/security/> (consultato: 2026-05-24)
- Cilium — Service Mesh with eBPF: <https://docs.cilium.io/en/stable/network/servicemesh/> (consultato: 2026-05-24)

### Libri

- Calcote, L.; Butcher, Z. — *Istio: Up and Running* (2a ed.), O'Reilly, 2022
- Morgan, W. — *Linkerd: Up and Running*, O'Reilly, 2022
- Posta, C. — *Istio in Action*, Manning, 2022

---

## Riferimenti Incrociati

| Modulo | Titolo | Relazione con questo modulo |
|--------|--------|-----------------------------|
| [05-kubernetes](05-kubernetes.md) | Kubernetes | Piattaforma su cui opera il service mesh |
| [08-monitoring-observability](08-monitoring-observability.md) | Monitoring e Observability | Metriche e trace generati dal mesh (Envoy, Istio) |
| [10-load-balancer-reverse-proxy](10-load-balancer-reverse-proxy.md) | Load Balancer e Reverse Proxy | Ingress gateway e bilanciamento L7 nel mesh |
| [13-sicurezza-piattaforme](13-sicurezza-piattaforme.md) | Sicurezza Piattaforme | mTLS, authorization policy, zero-trust networking |
| [16-api-gateway](16-api-gateway.md) | API Gateway | Differenze e complementarità tra API gateway e ingress mesh |
| [22-multi-tenancy-isolation](22-multi-tenancy-isolation.md) | Multi-Tenancy e Isolation | Isolamento del traffico tra tenant tramite namespace e mesh policy |

---

## Glossario

| Termine | Definizione |
|---------|-------------|
| **Service mesh** | Layer di infrastruttura dedicato alla gestione della comunicazione service-to-service, trasparente all'applicazione |
| **Control plane** | Componente centralizzato del mesh che gestisce configurazione, policy e distribuzione delle regole ai proxy data plane |
| **Data plane** | Insieme dei proxy sidecar o kernel-level che intercettano e gestiscono il traffico effettivo tra servizi |
| **Envoy proxy** | Proxy L4/L7 ad alte prestazioni scritto in C++, utilizzato come data plane in Istio e altri service mesh |
| **Sidecar** | Container proxy deployato accanto a ogni pod applicativo per intercettare tutto il traffico in entrata e uscita |
| **mTLS** | Mutual TLS — autenticazione bidirezionale in cui sia client che server presentano certificati, garantendo identità e cifratura |
| **VirtualService** | Risorsa Istio che definisce regole di routing del traffico verso le versioni dei servizi |
| **DestinationRule** | Risorsa Istio che configura policy di load balancing, circuit breaking e connection pool per un servizio destinazione |
| **Circuit breaking** | Pattern di resilienza che interrompe le richieste verso un servizio degradato, prevenendo il cascade failure |
| **Ambient mesh** | Architettura Istio senza sidecar (da v1.18+) che utilizza ztunnel per L4 e waypoint proxy per L7 |
| **eBPF** | Extended Berkeley Packet Filter — tecnologia kernel Linux che consente l'esecuzione di programmi nel kernel per networking e osservabilità senza overhead userspace |
| **Fault injection** | Tecnica di test che introduce deliberatamente errori (delay, abort) per verificare la resilienza del sistema |
| **xDS API** | Famiglia di API di discovery (CDS, EDS, LDS, RDS) usate dal control plane per configurare dinamicamente i proxy Envoy |
| **Ingress gateway** | Punto di ingresso del mesh per il traffico esterno, tipicamente un deployment Envoy dedicato |

Alternativa leggera per scenari intermedi: **Cilium** con eBPF fornisce osservabilita L3/L4, network policies e mTLS senza sidecar, operando direttamente nel kernel Linux con overhead minimo.
