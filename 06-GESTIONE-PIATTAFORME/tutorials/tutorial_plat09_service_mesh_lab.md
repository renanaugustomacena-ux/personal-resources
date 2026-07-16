# Tutorial: Service Mesh — Istio, mTLS e Traffic Management su K3s — Lab Pratico

> **Documento di riferimento:** `09-service-mesh.md`
> **Dominio:** Gestione Piattaforme — Networking Avanzato
> **Ambito:** Architettura service mesh (control plane/data plane, sidecar Envoy), Istio 1.24 su K3s, mTLS automatico (PeerAuthentication), traffic management (VirtualService, DestinationRule, canary deployment), authorization policies, fault injection, circuit breaking, osservabilità con Kiali, confronto Istio vs Cilium vs Linkerd
> **Durata lab:** 6-8 ore
> **Livello:** Avanzato — richiede Kubernetes (tutorial_plat05) completato
> **Prerequisiti:** K3s cluster funzionante, kubectl, istioctl, 8GB RAM (Istio è pesante!), Helm 4.x
> **Ambiente:** K3s v1.35 + Istio 1.24 ambient mesh o sidecar mode, applicazione demo (bookinfo)

---

## Lab Environment Setup

```bash
# === VERIFICA PREREQUISITI SERVICE MESH LAB ===
echo "=== CHECK PREREQUISITI ==="

# K3s cluster attivo
kubectl get nodes --no-headers 2>/dev/null | grep -q "Ready" && \
  echo "[OK] Cluster K8s disponibile" || {
  echo "[FAIL] Avviare K3s prima di questo lab"
  echo "  curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION=v1.35.0+k3s1 sh -"
  echo "  export KUBECONFIG=/etc/rancher/k3s/k3s.yaml"
}

# istioctl
istioctl version 2>/dev/null | head -1 && echo "[OK] istioctl disponibile" || {
  echo "[INFO] Installare istioctl:"
  echo "  curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.24.0 sh -"
  echo "  export PATH=\$PWD/istio-1.24.0/bin:\$PATH"
}

# Helm
helm version --short 2>/dev/null && echo "[OK] Helm disponibile" || \
  echo "[INFO] Helm opzionale per questo lab"

# RAM disponibile (Istio richiede ~2-3GB aggiuntivi)
free_mb=$(free -m 2>/dev/null | awk 'NR==2{print $2}')
[ -n "$free_mb" ] && {
  [ "$free_mb" -gt 7000 ] && echo "[OK] RAM: ${free_mb}MB (sufficiente per Istio)" || \
    echo "[WARN] RAM: ${free_mb}MB — Istio richiede ~8GB totali"
}

echo ""
echo "=== SETUP DIRECTORY LAB ==="
mkdir -p ~/service-mesh-lab/{manifests/{bookinfo,istio-config},scripts}
cd ~/service-mesh-lab

echo "[OK] Directory lab: ~/service-mesh-lab"
```

### Architettura del Lab

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    SERVICE MESH LAB — ARCHITETTURA                       │
│                                                                          │
│  ISTIO CONTROL PLANE (namespace: istio-system)                          │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  istiod (Pilot + Citadel + Galley fusionati)                   │     │
│  │  ├── Pilot: distribuisce configurazione routing ai sidecar     │     │
│  │  ├── Citadel: genera certificati mTLS (SPIFFE/SVID)           │     │
│  │  └── Galley: valida e traduce risorse Istio                    │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  DATA PLANE (ogni pod ha un sidecar Envoy)                              │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  Pod productpage                                                │     │
│  │  ┌──────────────┬─────────────┐                                │     │
│  │  │ app: Python  │ sidecar:    │  ← Envoy intercetta tutto     │     │
│  │  │ port:9080    │ Envoy :15001│    il traffico TCP             │     │
│  │  └──────────────┴─────────────┘                                │     │
│  │              ↕ mTLS automatico ↕                               │     │
│  │  Pod reviews (v1, v2, v3)                                      │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  OSSERVABILITÀ                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  Kiali :20001      — topologia servizi, traffic flow           │     │
│  │  Prometheus :9090  — metriche Envoy/Istio                      │     │
│  │  Jaeger :16686     — distributed tracing                       │     │
│  └─────────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## PART A: FONDAMENTI — Cos'è un Service Mesh

> Prima del service mesh, ogni microservizio doveva implementare da solo:
> autenticazione (chi sei?), autorizzazione (cosa puoi fare?), retry intelligenti,
> circuit breaker, timeout, distribuzione del traffico, raccolta di metriche,
> distributed tracing. Ogni team duplicava questo codice in ogni microservizio.
> Un service mesh sposta tutta questa logica in un livello di rete trasparente —
> un sidecar proxy (Envoy) affiancato ad ogni pod — che si occupa di tutto
> questo in modo uniforme, senza modificare il codice dell'applicazione.

---

### Concetto A1: Control Plane e Data Plane

> **Analogia.** Un service mesh funziona come una rete telefonica aziendale.
> Il centralino (control plane, istiod) sa come instradare ogni chiamata:
> chi può chiamare chi, quali linee sono disponibili, come bilanciare il traffico.
> I telefoni (data plane, Envoy) eseguono le chiamate seguendo le istruzioni
> del centralino. Il centralino non gestisce le singole chiamate — le gestiscono
> i telefoni — ma dice ai telefoni come comportarsi.

```
ARCHITETTURA ISTIO 1.24:

CONTROL PLANE (istiod):
  - xDS API server: distribui configurazione a tutti gli Envoy
  - Certificate Authority: emette certificati SVID (SPIFFE)
  - Webhook: inietta automaticamente il sidecar Envoy nei pod

DATA PLANE (Envoy sidecar per ogni pod):
  - Intercetta traffico in/out del pod (iptables redirect)
  - Gestisce: mTLS, retry, timeout, circuit breaker
  - Raccoglie: metriche L7, trace (Jaeger/Zipkin)
  - Riceve config da istiod via xDS (gRPC streaming)

RISORSE ISTIO (CRD):
  VirtualService    → routing regole (50% v1, 50% v2)
  DestinationRule   → policy per destinazione (loadbalancing, TLS)
  Gateway           → ingress del mesh (sostituisce Ingress K8s)
  PeerAuthentication → mTLS (strict/permissive/disable)
  AuthorizationPolicy → chi può chiamare chi (RBAC a livello L7)
  ServiceEntry      → registrare servizi esterni nel mesh

MODALITÀ ISTIO (2024):
  Sidecar mode: un container Envoy aggiunto ad ogni pod (classico)
  Ambient mode: nessun sidecar — Envoy a livello nodo (più leggero)
                → GA in Istio 1.22 (maggio 2024)
                → Raccomandato per nuove installazioni
```

---

### Concetto A2: Perché (e quando) Usare un Service Mesh

```
QUANDO IL SERVICE MESH VALE:
  ✓ 10+ microservizi in comunicazione
  ✓ Requisiti di security: mTLS zero-trust tra servizi
  ✓ Canary deployment progressivi (5% → 20% → 100%)
  ✓ Troubleshooting latenza (dove si accumula?)
  ✓ Multi-tenant: isolare traffico tra namespace/team

QUANDO NON VALE (overengineering):
  ✗ Monolite o pochi microservizi (< 5)
  ✗ Team piccolo senza expertise K8s avanzata
  ✗ Budget CPU/RAM limitato (Istio = +15-30% overhead)
  ✗ Problemi di latenza dove i ms contano (trading, gaming)

ALTERNATIVE PER CASI SEMPLICI:
  NetworkPolicy K8s: isola namespace (no mTLS, no L7)
  cert-manager: certificati mTLS senza mesh overhead
  Nginx/Traefik: routing A/B senza sidecar

CONFRONTO SERVICE MESH:

Istio sidecar:  maturo, ricco di feature, overhead medio (~5-15ms latency add)
Istio ambient:  GA 2024, nessun sidecar, meno overhead, raccomandato
Linkerd:        leggero, Go-based proxy (non Envoy), più semplice di Istio
Cilium mesh:    eBPF, zero sidecar, il più veloce, richiede Cilium CNI
Consul Connect: HashiCorp, multi-datacenter, on-prem friendly
```

---

## PART B: INSTALLARE ISTIO SU K3s

### Esercizio B1: Installazione Istio con Ambient Mode

```bash
# Istio Ambient Mode (consigliato da Istio 1.22+):
# - Nessun sidecar nei pod
# - Un daemonset "ztunnel" su ogni nodo per mTLS L4
# - Waypoint proxy (Envoy) solo per policy L7 opzionali

# Download istioctl 1.24
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.24.0 sh - 2>/dev/null
export PATH=$PWD/istio-1.24.0/bin:$PATH
echo "export PATH=$PWD/istio-1.24.0/bin:\$PATH" >> ~/.bashrc

istioctl version

# Pre-verifica compatibilità del cluster
istioctl x precheck 2>&1 | tail -10

# Installare Istio in ambient mode (consigliato)
istioctl install --set profile=ambient --skip-confirmation

# Attendere che tutti i componenti siano pronti
kubectl wait -n istio-system \
  pod -l app=istiod \
  --for=condition=Ready \
  --timeout=120s

kubectl wait -n istio-system \
  pod -l app=istio-cni \
  --for=condition=Ready \
  --timeout=120s

echo "[OK] Istio installato in ambient mode"
kubectl get pods -n istio-system

# Installare addon: Kiali, Prometheus, Jaeger
kubectl apply -f istio-1.24.0/samples/addons/prometheus.yaml
kubectl apply -f istio-1.24.0/samples/addons/jaeger.yaml
kubectl apply -f istio-1.24.0/samples/addons/kiali.yaml

echo "Attendo addon..."
kubectl wait -n istio-system pod -l app=kiali \
  --for=condition=Ready --timeout=120s

echo "[OK] Addon installati"
kubectl get pods -n istio-system
```

---

### Esercizio B2: Deploy dell'App Demo Bookinfo

```bash
# Bookinfo: app demo Istio (come usata in tutti gli esempi ufficiali)
# Architettura:
#   browser → productpage → details (v1)
#                        → reviews (v1: nessuna stella, v2: stelle nere, v3: stelle rosse)
#                                → ratings (v1)

# Creare namespace per l'app
kubectl create namespace bookinfo

# In ambient mode: abilitare il mesh per il namespace
kubectl label namespace bookinfo istio.io/dataplane-mode=ambient

# Deploy dell'applicazione
kubectl apply -n bookinfo -f istio-1.24.0/samples/bookinfo/platform/kube/bookinfo.yaml

# Attendere che tutti i pod siano pronti
kubectl wait -n bookinfo pod --all --for=condition=Ready --timeout=120s

echo "[OK] Bookinfo deployato"
kubectl get pods -n bookinfo

# Verifica interna: la pagina è raggiungibile?
kubectl exec -n bookinfo \
  $(kubectl get pod -n bookinfo -l app=productpage -o name | head -1) \
  -- curl -s productpage:9080/productpage | grep -o "<title>.*</title>"

# Esporre tramite Istio Gateway
kubectl apply -n bookinfo -f istio-1.24.0/samples/bookinfo/networking/bookinfo-gateway.yaml

# Ottenere l'indirizzo del gateway
GATEWAY_URL=$(kubectl get svc istio-ingressgateway -n istio-system \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)

# Su K3s con ServiceLB, l'IP è quello del nodo
[ -z "$GATEWAY_URL" ] && \
  GATEWAY_URL=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[0].address}')

GATEWAY_PORT=$(kubectl -n istio-system get service istio-ingressgateway \
  -o jsonpath='{.spec.ports[?(@.name=="http2")].nodePort}')

echo "[INFO] Bookinfo disponibile: http://$GATEWAY_URL:$GATEWAY_PORT/productpage"

# Test: aggiornare la pagina più volte — si alterna tra reviews v1, v2, v3 (random)
for i in $(seq 1 6); do
  REVIEW=$(curl -s "http://$GATEWAY_URL:$GATEWAY_PORT/productpage" | \
    grep -o "glyphicon-star.*" | head -1)
  echo "Request $i: $REVIEW"
done
```

---

## PART C: TRAFFIC MANAGEMENT

### Esercizio C1: Canary Deployment con VirtualService

> **Analogia.** Immagina di dover sostituire tutti i semafori di una città.
> Non lo fai di notte in una volta sola — rischi che qualcuno rimanga bloccato
> per ore se qualcosa va storto. Lo fai gradualmente: prima 5% delle strade con
> i nuovi semafori, monitora, poi 20%, poi 50%, poi 100%. Il service mesh fa
> la stessa cosa con il traffico: puoi mandare il 5% degli utenti alla versione
> nuova del tuo servizio, mantenere il 95% sulla versione stabile, e scalare
> progressivamente basandoti su metriche reali.

```bash
cd ~/service-mesh-lab/manifests

# Prima: applicare DestinationRule (definisce i subset/versioni disponibili)
cat > bookinfo-destination-rules.yaml << 'EOF'
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: reviews
  namespace: bookinfo
spec:
  host: reviews
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http2MaxRequests: 1000
        maxRequestsPerConnection: 10
    outlierDetection:        # Circuit breaker: ejection di pod problematici
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
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
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: productpage
  namespace: bookinfo
spec:
  host: productpage
  subsets:
  - name: v1
    labels:
      version: v1
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: ratings
  namespace: bookinfo
spec:
  host: ratings
  subsets:
  - name: v1
    labels:
      version: v1
EOF

kubectl apply -f bookinfo-destination-rules.yaml
echo "[OK] DestinationRule applicate"

# STEP 1: Tutto il traffico va a reviews v1 (nessuna stella)
cat > vs-reviews-v1-100.yaml << 'EOF'
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: reviews
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
EOF

kubectl apply -f vs-reviews-v1-100.yaml
echo "[OK] 100% traffico → reviews v1"

sleep 3
for i in $(seq 1 3); do
  curl -s "http://$GATEWAY_URL:$GATEWAY_PORT/productpage" | \
    grep -c "glyphicon-star" || echo "0 stelle (v1)"
done

# STEP 2: Canary — 20% va a v3 (stelle rosse)
cat > vs-reviews-canary-20.yaml << 'EOF'
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: reviews
  namespace: bookinfo
spec:
  hosts:
  - reviews
  http:
  - route:
    - destination:
        host: reviews
        subset: v1
      weight: 80
    - destination:
        host: reviews
        subset: v3
      weight: 20
EOF

kubectl apply -f vs-reviews-canary-20.yaml
echo "[OK] Canary attivo: 80% v1, 20% v3"

# Test: distribuire le richieste
V1_COUNT=0; V3_COUNT=0
for i in $(seq 1 20); do
  STARS=$(curl -s "http://$GATEWAY_URL:$GATEWAY_PORT/productpage" | \
    grep -o 'glyphicon-star[^"]*' | head -1)
  if echo "$STARS" | grep -q "empty"; then
    ((V3_COUNT++))  # stelle vuote/colorate = v3
  else
    ((V1_COUNT++))
  fi
done
echo "Distribuzione 20 richieste: v1=$V1_COUNT, v3=$V3_COUNT (atteso ~16:4)"

# STEP 3: Promozione — 50% a v3
cat > vs-reviews-canary-50.yaml << 'EOF'
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: reviews
  namespace: bookinfo
spec:
  hosts:
  - reviews
  http:
  - route:
    - destination:
        host: reviews
        subset: v1
      weight: 50
    - destination:
        host: reviews
        subset: v3
      weight: 50
EOF

kubectl apply -f vs-reviews-canary-50.yaml
echo "[OK] Canary avanzato: 50% v1, 50% v3"
```

---

### Esercizio C2: Header-Based Routing

```bash
# Routing basato su header HTTP: utile per:
# - Test in produzione (header X-Test-User: beta-tester)
# - A/B test per specifici utenti
# - Compatibilità: versioni specifiche per certi client

cat > vs-reviews-header-routing.yaml << 'EOF'
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: reviews
  namespace: bookinfo
spec:
  hosts:
  - reviews
  http:
  # Regola 1: utenti "jason" → sempre v2 (stelle nere)
  - match:
    - headers:
        end-user:
          exact: jason
    route:
    - destination:
        host: reviews
        subset: v2

  # Regola 2: beta tester → v3 (stelle rosse)
  - match:
    - headers:
        x-beta-user:
          exact: "true"
    route:
    - destination:
        host: reviews
        subset: v3

  # Regola 3: tutti gli altri → v1 (default)
  - route:
    - destination:
        host: reviews
        subset: v1
EOF

kubectl apply -f vs-reviews-header-routing.yaml
echo "[OK] Header-based routing attivo"

# Test: login come "jason" → deve vedere v2
# Nota: il bookinfo usa cookie "user" per simulare il login
curl -s "http://$GATEWAY_URL:$GATEWAY_PORT/productpage" \
  -H "end-user: jason" | grep -o "Reviewer1\|Reviewer2\|No reviews"
```

---

## PART D: SICUREZZA — mTLS E AUTHORIZATION POLICIES

### Esercizio D1: mTLS Automatico (PeerAuthentication)

> **Analogia.** In un ambiente senza mTLS, quando il servizio A chiama il servizio B,
> è come una chiamata telefonica senza identificativo chiamante: B non sa se chi chiama
> è davvero A o qualcuno che si spaccia per A. Con mTLS, ogni servizio ha un certificato
> firmato da un'autorità fidata (istiod), e ogni connessione presenta e verifica il
> certificato prima di scambiare dati. È come richiedere che entrambi i lati della
> telefonata si identifichino con documento prima di parlare.

```bash
# Verificare che mTLS sia attivo (ambient mode lo abilita automaticamente)
kubectl exec -n bookinfo \
  $(kubectl get pod -n bookinfo -l app=productpage -o name | head -1) \
  -c productpage \
  -- curl -v "http://reviews:9080/reviews/0" 2>&1 | grep -E "TLS|SSL|Connected"

# Forzare STRICT mTLS: rifiuta traffico non cifrato
cat > peer-auth-strict.yaml << 'EOF'
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: bookinfo
spec:
  mtls:
    mode: STRICT   # Solo connessioni mTLS — rifiuta HTTP plain
EOF

kubectl apply -f peer-auth-strict.yaml
echo "[OK] STRICT mTLS abilitato nel namespace bookinfo"

# In ambient mode, ztunnel gestisce mTLS automaticamente:
kubectl get pods -n istio-system -l app=ztunnel -o wide

# Verificare certificati emessi da istiod
istioctl proxy-config secret \
  $(kubectl get pod -n bookinfo -l app=productpage -o name | head -1).bookinfo 2>/dev/null | \
  head -10 || echo "[INFO] Comando disponibile solo in sidecar mode"
```

---

### Esercizio D2: Authorization Policy — Zero Trust

```bash
# Authorization Policy: controllo RBAC a livello L7 del mesh
# In ambiente zero-trust: per default NESSUNA comunicazione è permessa;
# si aggiungono regole esplicite per permettere ciò che serve

# STEP 1: Deny-all per default (zero trust)
cat > authz-deny-all.yaml << 'EOF'
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: deny-all
  namespace: bookinfo
spec:
  {}  # Nessuna regola = nega tutto
EOF

kubectl apply -f authz-deny-all.yaml
echo "[OK] Deny-all attivo — ora nulla funziona (zero trust base)"

sleep 2
# Verificare: productpage non può più chiamare reviews
curl -s "http://$GATEWAY_URL:$GATEWAY_PORT/productpage" | \
  grep -i "error\|unavailable" || echo "Pagina caricata ma reviews è inaccessibile"

# STEP 2: Permettere l'accesso da ingress gateway a productpage
cat > authz-ingress-to-productpage.yaml << 'EOF'
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-ingress-to-productpage
  namespace: bookinfo
spec:
  selector:
    matchLabels:
      app: productpage
  action: ALLOW
  rules:
  - from:
    - source:
        principals:
          - "cluster.local/ns/istio-system/sa/istio-ingressgateway-service-account"
    to:
    - operation:
        methods: ["GET"]
        paths: ["/productpage", "/static/*", "/login", "/logout"]
EOF

kubectl apply -f authz-ingress-to-productpage.yaml

# STEP 3: Permettere productpage → details, reviews
cat > authz-productpage-to-services.yaml << 'EOF'
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-productpage-to-details
  namespace: bookinfo
spec:
  selector:
    matchLabels:
      app: details
  action: ALLOW
  rules:
  - from:
    - source:
        principals:
          - "cluster.local/ns/bookinfo/sa/bookinfo-productpage"
    to:
    - operation:
        methods: ["GET"]
---
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-productpage-to-reviews
  namespace: bookinfo
spec:
  selector:
    matchLabels:
      app: reviews
  action: ALLOW
  rules:
  - from:
    - source:
        principals:
          - "cluster.local/ns/bookinfo/sa/bookinfo-productpage"
    to:
    - operation:
        methods: ["GET"]
---
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-reviews-to-ratings
  namespace: bookinfo
spec:
  selector:
    matchLabels:
      app: ratings
  action: ALLOW
  rules:
  - from:
    - source:
        principals:
          - "cluster.local/ns/bookinfo/sa/bookinfo-reviews"
    to:
    - operation:
        methods: ["GET"]
EOF

kubectl apply -f authz-productpage-to-services.yaml
echo "[OK] Authorization policies configurate — solo traffico necessario permesso"

sleep 3
curl -s "http://$GATEWAY_URL:$GATEWAY_PORT/productpage" | grep -c "bookinfo" && \
  echo "[OK] Applicazione funziona con zero-trust policy"
```

---

## PART E: FAULT INJECTION E CIRCUIT BREAKING

### Esercizio E1: Fault Injection per Test di Resilienza

```bash
# Fault injection: simulare guasti in produzione (chaos engineering)
# Fondamentale per testare: retry, fallback, timeout, error handling

# Simulare delay di 5 secondi per 50% delle richieste ai ratings
cat > fault-injection-delay.yaml << 'EOF'
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: ratings
  namespace: bookinfo
spec:
  hosts:
  - ratings
  http:
  - fault:
      delay:
        percentage:
          value: 50.0
        fixedDelay: 5s      # 5 secondi di ritardo artificiale
    route:
    - destination:
        host: ratings
        subset: v1
EOF

kubectl apply -f fault-injection-delay.yaml
echo "[OK] Fault injection delay attivo (50% richieste → 5s delay)"

# Misurare impatto sulla latenza dell'applicazione
echo "Test latenza (con fault injection 5s delay):"
for i in $(seq 1 5); do
  START=$(date +%s%N)
  curl -s "http://$GATEWAY_URL:$GATEWAY_PORT/productpage" > /dev/null
  END=$(date +%s%N)
  LATENCY=$(( (END - START) / 1000000 ))
  echo "  Richiesta $i: ${LATENCY}ms"
done

# Simulare errori HTTP 500 per il 20% delle richieste
cat > fault-injection-abort.yaml << 'EOF'
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: ratings
  namespace: bookinfo
spec:
  hosts:
  - ratings
  http:
  - fault:
      abort:
        percentage:
          value: 20.0
        httpStatus: 503     # Service Unavailable
    route:
    - destination:
        host: ratings
        subset: v1
EOF

kubectl apply -f fault-injection-abort.yaml
echo "[OK] Fault injection abort attivo (20% richieste → HTTP 503)"

# Testare come l'app gestisce gli errori
for i in $(seq 1 5); do
  RESP=$(curl -s "http://$GATEWAY_URL:$GATEWAY_PORT/productpage" | \
    grep -o "Ratings service is currently unavailable" || echo "OK")
  echo "  Richiesta $i: $RESP"
done

# Ripristinare il routing normale
kubectl delete virtualservice ratings -n bookinfo 2>/dev/null
echo "[OK] Fault injection rimossa"
```

---

### Esercizio E2: Circuit Breaker con DestinationRule

```bash
# Circuit breaker: se un pod risponde con troppi errori, viene "escluso"
# temporaneamente dal load balancer (ejection) — dà tempo di recuperare
# senza che il traffico continui a fallire

cat > circuit-breaker-reviews.yaml << 'EOF'
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: reviews
  namespace: bookinfo
spec:
  host: reviews
  trafficPolicy:
    # Limiti connessione (protezione contro overload)
    connectionPool:
      tcp:
        maxConnections: 10          # Max 10 connessioni TCP totali
      http:
        http1MaxPendingRequests: 5  # Max 5 richieste in attesa
        maxRequestsPerConnection: 1 # Una richiesta per connessione (HTTP/1.1)
    
    # Outlier detection (circuit breaker):
    outlierDetection:
      consecutive5xxErrors: 3       # Dopo 3 errori 5xx consecutivi...
      interval: 10s                 # ...nell'intervallo di 10 secondi...
      baseEjectionTime: 30s         # ...eject il pod per 30 secondi
      maxEjectionPercent: 50        # Al massimo il 50% dei pod può essere ejected
      splitExternalLocalOriginErrors: false
  
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
EOF

kubectl apply -f circuit-breaker-reviews.yaml
echo "[OK] Circuit breaker configurato su reviews"

# Verificare la configurazione outlier detection
istioctl proxy-config cluster \
  $(kubectl get pod -n bookinfo -l app=productpage -o name | head -1).bookinfo \
  --direction outbound -o json 2>/dev/null | \
  python3 -c "
import json,sys
for c in json.load(sys.stdin):
  if 'reviews' in c.get('name',''):
    od = c.get('outlierDetection',{})
    if od:
      print('Circuit breaker:', od)
" 2>/dev/null || echo "[INFO] Proxy config disponibile in sidecar mode"
```

---

## PART F: OSSERVABILITÀ — KIALI E METRICHE ISTIO

### Esercizio F1: Kiali — Topologia del Service Mesh

```bash
# Aprire Kiali (browser)
kubectl port-forward -n istio-system svc/kiali 20001:20001 &
echo "[INFO] Kiali disponibile: http://localhost:20001"
echo "  → Graph: visualizza le chiamate tra servizi in tempo reale"
echo "  → Namespace bookinfo selezionato"

# Generare traffico per popolare i grafici Kiali
echo "Generando traffico..."
for i in $(seq 1 100); do
  curl -s "http://$GATEWAY_URL:$GATEWAY_PORT/productpage" > /dev/null
  sleep 0.1
done &
TRAFFIC_PID=$!

sleep 15

# Metriche Istio disponibili in Prometheus
# Aprire Prometheus: http://localhost:9090
kubectl port-forward -n istio-system svc/prometheus 9090:9090 &

cat << 'METRICS'
═══════════════════════════════════════════════════════════════
METRICHE ISTIO IN PROMQL
═══════════════════════════════════════════════════════════════

# Request rate (richieste/secondo) per servizio
rate(istio_requests_total[5m])

# Error rate per servizio (HTTP 5xx)
sum(rate(istio_requests_total{response_code=~"5.."}[5m])) by (destination_service)
/
sum(rate(istio_requests_total[5m])) by (destination_service)
* 100

# Latenza P99 per ogni coppia source → destination
histogram_quantile(0.99,
  sum(rate(istio_request_duration_milliseconds_bucket[5m]))
  by (le, source_app, destination_service)
)

# TCP bytes trasferiti (utile per data services)
sum(rate(istio_tcp_sent_bytes_total[5m])) by (destination_service)

# Richieste bloccate da AuthorizationPolicy
sum(rate(istio_requests_total{response_flags="UAEX"}[5m])) by (source_app, destination_service)
# UAEX = "Unauthorized External" = bloccato da policy
═══════════════════════════════════════════════════════════════
METRICS

# Fermare generazione traffico
kill $TRAFFIC_PID 2>/dev/null

# Distributed tracing in Jaeger
kubectl port-forward -n istio-system svc/tracing 16686:80 &
echo "[INFO] Jaeger UI: http://localhost:16686"
echo "  → Service: bookinfo-productpage.bookinfo"
echo "  → Vedere la cascata di chiamate: productpage → reviews → ratings"
```

---

## Conclusioni e Prossimi Passi

```
SERVICE MESH — RIEPILOGO:

FONDAMENTI:
  ✓ Control plane (istiod): distribui config, emette certificati mTLS
  ✓ Data plane (Envoy): intercetta traffico, gestisce policy
  ✓ Ambient mode (Istio 1.22+): nessun sidecar, più leggero
  ✓ Usare solo se >10 microservizi o requisiti zero-trust

TRAFFIC MANAGEMENT:
  ✓ VirtualService: routing intelligente (% peso, header, path)
  ✓ DestinationRule: policy per destinazione (subset, loadbalancing)
  ✓ Canary deployment: 5% → 20% → 50% → 100% senza downtime
  ✓ Header routing: utenti specifici → versione specifica
  ✓ Gateway: punto di ingresso al mesh (sostituisce Ingress)

SICUREZZA ZERO-TRUST:
  ✓ PeerAuthentication STRICT: solo mTLS tra pod del mesh
  ✓ AuthorizationPolicy: chi può chiamare chi (L7 RBAC)
  ✓ Deny-all per default, allow esplicito per ciò che serve
  ✓ SPIFFE/SVID: identità crittografica per ogni workload

FAULT INJECTION:
  ✓ Delay: aggiungere latenza artificiale (test timeout)
  ✓ Abort: restituire HTTP 5xx artificiali (test fallback)
  ✓ Combinabile: delay per alcuni utenti, abort per altri
  ✓ Essenziale per chaos engineering

CIRCUIT BREAKER:
  ✓ outlierDetection: ejection pod problematici
  ✓ connectionPool: limite connessioni (protezione overload)
  ✓ baseEjectionTime: tempo di recupero prima di rientrare

OSSERVABILITÀ ISTIO:
  ✓ Kiali: topologia L7, request graph, config validator
  ✓ Prometheus: metriche istio_requests_total, latency histogram
  ✓ Jaeger: distributed tracing automatico (zero code change)
  ✓ Grafana: dashboard Istio predefinite

CONFRONTO MESH:
  Istio ambient: nuovo default, no sidecar, mTLS L4+L7
  Linkerd: più semplice, proxy Rust, meno feature di Istio
  Cilium: eBPF kernel-level, più veloce, richiede Cilium CNI
```

**Prossimi tutorial:**
- `tutorial_plat10_load_balancer_lab.md` — Nginx, HAProxy, Traefik
- `tutorial_plat13_sicurezza_piattaforme_lab.md` — Falco, OPA/Kyverno

```bash
# Pulizia lab
kubectl delete -f ~/service-mesh-lab/manifests/ --ignore-not-found 2>/dev/null
kubectl delete namespace bookinfo --ignore-not-found

# Disinstallare Istio (ATTENZIONE: rimuove il mesh da tutto il cluster)
# istioctl uninstall --purge --skip-confirmation
# kubectl delete namespace istio-system

kill $(lsof -t -i:20001) 2>/dev/null
kill $(lsof -t -i:9090) 2>/dev/null
kill $(lsof -t -i:16686) 2>/dev/null

rm -rf ~/service-mesh-lab

echo "[OK] Lab Service Mesh completato"
```

---

> **Nota versioni:** Tutorial validato con Istio 1.24.x (dicembre 2024), ambient mode GA in 1.22.
> Breaking change Istio 1.22: ambient mode non richiede CNI multiplo se si usa Cilium.
> Istio 1.24 depreca le API v1alpha1 (usare v1beta1 e v1) — le configurazioni in questo tutorial usano v1beta1.
> Linkerd 2.15+ (2024): Rust proxy (linkerd2-proxy), più leggero di Envoy per carichi REST/gRPC standard.
> Cilium 1.16+ (2024): WireGuard encryption nativa, Tetragon per eBPF-based runtime security.
