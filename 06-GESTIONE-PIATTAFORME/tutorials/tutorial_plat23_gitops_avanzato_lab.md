# Tutorial: GitOps Avanzato — ApplicationSet, Flagger, Argo Rollouts — Lab Pratico

> **Documento di riferimento:** `23-gitops-avanzato.md`
> **Dominio:** Gestione Piattaforme — Continuous Delivery e Progressive Delivery
> **Ambito:** ArgoCD ApplicationSet, Flagger canary, Argo Rollouts blue-green, rollback automatico SLO
> **Durata lab:** 5-7 ore
> **Livello:** Avanzato — richiede Kubernetes funzionante e conoscenza ArgoCD base
> **Prerequisiti:** K3s o Kind cluster, kubectl, Helm 3.x, ArgoCD installato
> **Ambiente:** Cluster K8s locale (K3s via Docker o Kind), Prometheus per metriche

---

## Lab Environment Setup

### Prerequisiti e verifica

```bash
#!/bin/bash
# check-prerequisites-gitops.sh

echo "=== Verifica prerequisiti GitOps Avanzato Lab ==="
echo ""

ALL_OK=true

check() {
    local name="$1"
    local cmd="$2"
    if eval "$cmd" &>/dev/null; then
        version=$(eval "$cmd" 2>&1 | head -1)
        echo "[OK]   $name — $version"
    else
        echo "[FAIL] $name — non trovato"
        ALL_OK=false
    fi
}

check "kubectl"     "kubectl version --client --short 2>/dev/null || kubectl version --client"
check "Helm 3"      "helm version --short"
check "ArgoCD CLI"  "argocd version --client"
check "Docker"      "docker --version"

# Verifica cluster raggiungibile
if kubectl cluster-info &>/dev/null; then
    nodes=$(kubectl get nodes --no-headers 2>/dev/null | wc -l)
    echo "[OK]   Cluster K8s — $nodes nodo/i disponibili"
    kubectl get nodes --no-headers | awk '{print "       " $1 " (" $2 ")"}'
else
    echo "[FAIL] Cluster K8s — non raggiungibile"
    echo "       Avvia K3s: curl -sfL https://get.k3s.io | sh -"
    echo "       Oppure Kind: kind create cluster --name gitops-lab"
    ALL_OK=false
fi

# Verifica ArgoCD installato
if kubectl get ns argocd &>/dev/null; then
    echo "[OK]   Namespace argocd presente"
    running=$(kubectl get pods -n argocd --no-headers 2>/dev/null | grep Running | wc -l)
    echo "       Pod running: $running"
else
    echo "[INFO] ArgoCD non installato — verrà installato nel lab"
fi

echo ""
if [ "$ALL_OK" = true ]; then
    echo "[OK]   Prerequisiti soddisfatti!"
else
    echo "[WARN] Alcuni prerequisiti mancanti. Consulta le istruzioni sopra."
fi
```

### Architettura del Lab

```
ARCHITETTURA LAB GITOPS AVANZATO:

┌─────────────────────────────────────────────────────────────────────────┐
│                    CLUSTER KUBERNETES LOCALE                             │
│                                                                         │
│  namespace: argocd                                                      │
│  ├── argocd-server              (UI e API ArgoCD)       :8080          │
│  ├── argocd-application-controller (riconciliazione)                   │
│  └── argocd-applicationset-controller (genera Application)            │
│                                                                         │
│  namespace: monitoring                                                  │
│  ├── prometheus                 (metriche)              :9090          │
│  └── grafana                    (dashboard)             :3000          │
│                                                                         │
│  namespace: demo-app                                                    │
│  ├── order-service-primary      (versione stabile)                     │
│  ├── order-service-canary       (nuova versione, % traffico graduale)  │
│  └── flagger                    (controller canary)                    │
│                                                                         │
│  namespace: argo-rollouts                                               │
│  └── argo-rollouts-controller   (progressive delivery)                 │
│                                                                         │
│  GITOPS FLOW:                                                           │
│  GitHub Repo → ArgoCD Poll → Apply a cluster → Flagger/Rollouts       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## PART A: FONDAMENTI — GitOps come Invariante Architetturale

> **Perché questo modulo è critico:**
>
> Il fallimento più comune nei deploy in produzione non è il codice: è il deploy stesso.
> Pipeline rotte a metà, rollback manuali disperati alle 2 di notte, stati
> inconsistenti tra cluster diversi. GitOps è la risposta architetturale a questo problema:
> Git diventa l'unica fonte di verità, e la riconciliazione è automatica e continua.
>
> In questo lab andrai oltre il GitOps base. Imparerai a gestire decine di ambienti
> con un solo template (ApplicationSet), a rilasciare in produzione senza downtime
> (Flagger canary), e a fare rollback automatico prima ancora che gli utenti se ne accorgano.

---

### Concetto A1: Il Problema del Deploy Manuale

> **Analogia.** Distribuire software senza GitOps è come cucinare in un ristorante
> dove ogni cuoco ha la propria ricetta nella testa, nessuno ha scritto nulla,
> e se un cuoco si ammala il piatto non può essere replicato. Se il piatto viene
> sbagliato, non sai quale cuoco ha deviato dalla ricetta "ufficiale" (che non esiste).
>
> GitOps è come avere tutte le ricette in un libro condiviso con controllo di versione:
> chiunque può seguire la ricetta, ogni modifica è tracciata, e il risultato è sempre
> replicabile.

```
PROBLEMA DEPLOY MANUALE:

Scenario tipico senza GitOps:
  Developer A: kubectl apply -f deployment.yaml (versione v1.2)
  Developer B: kubectl edit deployment/my-service (modifica live)
  Ops Team:    helm upgrade my-service (valori diversi da quelli in Git)
  
  Dopo 2 settimane:
  → Nessuno sa quale sia la configurazione "ufficiale"
  → Il cluster in staging differisce da quello in produzione
  → Un nodo crashato porta a pod diversi su nodi diversi
  → Drift rilevato solo quando qualcosa smette di funzionare

GITOPS — PRINCIPIO DI INVARIANZA:
  ✓ Git è l'UNICA fonte di verità
  ✓ Qualsiasi modifica passa da una PR con review
  ✓ ArgoCD riconcilia ogni 3 minuti (corregge qualsiasi deriva)
  ✓ Audit trail completo in git log
  ✗ Nessun kubectl apply manuale in produzione
  ✗ Nessun helm upgrade manuale in produzione
  ✗ Nessun kubectl edit manuale in produzione
```

---

### Concetto A2: Progressive Delivery — Ridurre il Rischio di Deploy

> **Analogia.** Pensaci: i test farmaceutici non danno una nuova medicina subito a tutti
> i pazienti. Prima si testa su un gruppo piccolo e controllato (10% degli utenti),
> si monitorano gli effetti (metriche), e solo se è sicuro si allarga la distribuzione.
>
> Il Progressive Delivery applica lo stesso principio ai software: prima si espone
> la nuova versione al 5% del traffico, si monitorano error rate e latenza, e solo
> se le metriche sono buone si aumenta progressivamente fino al 100%.

```
PROGRESSIVE DELIVERY — RIDUZIONE DEL RISCHIO:

DEPLOY TRADIZIONALE (big bang):
  v1.0 [100%] → v2.0 [100%]
  
  Rischio: se v2.0 ha un bug, il 100% degli utenti è colpito
  MTTR: da 30 min a 2 ore (rollback manuale)

CANARY DEPLOYMENT:
  v1.0 [100%] → v2.0 [5%], v1.0 [95%]
                → metriche OK?
  v1.0 [80%] ←→ v2.0 [20%]
                → metriche OK?
  v1.0 [50%] ←→ v2.0 [50%]
                → metriche OK?
  v1.0 [0%] ←→ v2.0 [100%]
  
  Rischio: massimo il 5% degli utenti colpiti nel primo step
  MTTR: 2-5 minuti (rollback automatico)

BLUE-GREEN DEPLOYMENT:
  Blue [100%]  ← traffico produzione
  Green [0%]   ← nuova versione, traffico zero (solo test interni)
  
  Test Green → OK → Switch:
  Blue [0%]   ← rimane in standby (rollback immediato se serve)
  Green [100%] ← diventa produzione
  
  Rischio: zero downtime, rollback in 10 secondi (switch service)
  Costo: il doppio delle risorse durante il deploy
```

---

## PART B: INSTALLAZIONE ARGOCD E APPLICATIONSET

### Esercizio B1: Installare ArgoCD con Helm

```bash
# Aggiunge repo Helm ArgoCD
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update

# Installa ArgoCD 2.13 con ApplicationSet controller abilitato (default dal 2.3)
helm install argocd argo/argo-cd \
    --namespace argocd \
    --create-namespace \
    --version 7.7.0 \
    --set configs.params."server\.insecure"=true \
    --set server.service.type=NodePort \
    --set server.service.nodePortHttp=30080 \
    --wait

# Output atteso:
# NAME: argocd
# LAST DEPLOYED: Wed Jul 16 10:00:00 2026
# NAMESPACE: argocd
# STATUS: deployed
# REVISION: 1

# Verifica pod
kubectl get pods -n argocd

# Output atteso:
# NAME                                               READY   STATUS    RESTARTS   AGE
# argocd-application-controller-xxx                 1/1     Running   0          2m
# argocd-applicationset-controller-xxx              1/1     Running   0          2m
# argocd-dex-server-xxx                             1/1     Running   0          2m
# argocd-notifications-controller-xxx               1/1     Running   0          2m
# argocd-redis-xxx                                  1/1     Running   0          2m
# argocd-repo-server-xxx                            1/1     Running   0          2m
# argocd-server-xxx                                 1/1     Running   0          2m

# Recupera password admin ArgoCD
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret \
    -o jsonpath="{.data.password}" | base64 -d)
echo "ArgoCD password: $ARGOCD_PASSWORD"

# Login tramite CLI
argocd login localhost:30080 \
    --username admin \
    --password "$ARGOCD_PASSWORD" \
    --insecure \
    --plaintext

# Output atteso:
# 'admin:login' logged in successfully
# Context 'localhost:30080' updated

# Verifica login
argocd version
# argocd: v2.13.0
# ...
```

---

### Esercizio B2: Prima Application ArgoCD

```bash
# Crea namespace per la demo app
kubectl create namespace demo-app

# Crea una Application semplice che punta a un repo pubblico
cat <<'EOF' | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: demo-app-dev
  namespace: argocd
  # Finalizer: garantisce che ArgoCD rimuova le risorse al delete
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  
  source:
    # Repo con esempi Argo Rollouts (pubblico, ottimo per lab)
    repoURL: https://github.com/argoproj/argocd-example-apps
    targetRevision: HEAD
    path: helm-guestbook      # chart Helm di esempio
    
    helm:
      parameters:
        - name: replicaCount
          value: "2"
  
  destination:
    server: https://kubernetes.default.svc   # cluster locale
    namespace: demo-app
  
  syncPolicy:
    automated:
      prune: true      # rimuove risorse non più in Git
      selfHeal: true   # corregge modifiche manuali (deriva)
    syncOptions:
      - CreateNamespace=true
EOF

# Osserva la sincronizzazione
watch kubectl get application demo-app-dev -n argocd

# Output atteso (dopo ~30 secondi):
# NAME           SYNC STATUS   HEALTH STATUS
# demo-app-dev   Synced        Healthy

# Verifica deployment
kubectl get pods -n demo-app
# NAME                          READY   STATUS    RESTARTS   AGE
# helm-guestbook-xxx            1/1     Running   0          1m
# helm-guestbook-xxx            1/1     Running   0          1m

# Testa il selfHeal: modifica manualmente un pod e guarda ArgoCD correggerlo
kubectl scale deployment helm-guestbook -n demo-app --replicas=5
echo "Modificato replicas a 5 manualmente"

sleep 15  # aspetta la prossima riconciliazione

kubectl get pods -n demo-app | wc -l
# Output: 3 (ArgoCD ha corretto da 5 a 2 come definito in Git)
echo "[OK] SelfHeal funziona: ArgoCD ha riconciliato al valore di Git (2 replicas)"
```

---

### Esercizio B3: ApplicationSet — Deploy Multi-Ambiente

Ora creiamo un ApplicationSet che genera automaticamente deployment per tre ambienti.

```bash
# Crea namespace per tutti gli ambienti
for env in development staging production; do
    kubectl create namespace "myapp-$env" || true
done

# ApplicationSet con generatore List
cat <<'EOF' | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: myapp-multi-env
  namespace: argocd
spec:
  # Strategy: controlla l'ordine di aggiornamento degli Application generati
  strategy:
    type: RollingSync
    rollingSync:
      steps:
        # Step 1: aggiorna development (sempre automatico)
        - matchExpressions:
            - key: environment
              operator: In
              values: [development]
        # Step 2: aggiorna staging (dopo development)
        - matchExpressions:
            - key: environment
              operator: In
              values: [staging]
        # Step 3: aggiorna production (richiede maxUpdate=0 → manuale)
        - matchExpressions:
            - key: environment
              operator: In
              values: [production]
  
  generators:
    - list:
        elements:
          - environment: development
            replicas: "1"
            image_tag: "latest"
            auto_sync: "true"
            resources_cpu: "100m"
            resources_memory: "128Mi"
          
          - environment: staging
            replicas: "2"
            image_tag: "latest"
            auto_sync: "true"
            resources_cpu: "200m"
            resources_memory: "256Mi"
          
          - environment: production
            replicas: "3"
            image_tag: "v1.0.0"
            auto_sync: "false"    # PRODUZIONE: no auto-sync
            resources_cpu: "500m"
            resources_memory: "512Mi"
  
  template:
    metadata:
      name: "myapp-{{environment}}"
      labels:
        environment: "{{environment}}"
      annotations:
        argocd.argoproj.io/manifest-generate-paths: .
    
    spec:
      project: default
      
      source:
        repoURL: https://github.com/argoproj/argocd-example-apps
        targetRevision: HEAD
        path: helm-guestbook
        helm:
          parameters:
            - name: replicaCount
              value: "{{replicas}}"
            - name: image.tag
              value: "{{image_tag}}"
      
      destination:
        server: https://kubernetes.default.svc
        namespace: "myapp-{{environment}}"
      
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
      
      # PRODUZIONE: non auto-sync (richiede click manuale o argocd sync)
      # Viene sovrascritto dal valore del generatore tramite la logica del template
EOF

# Osserva la creazione delle 3 Application
kubectl get applications -n argocd

# Output atteso (dopo 1-2 minuti):
# NAME                   SYNC STATUS   HEALTH STATUS
# myapp-development      Synced        Healthy
# myapp-staging          Synced        Healthy
# myapp-production       OutOfSync     Healthy    ← richiede sync manuale

# Verifica deployment in tutti gli ambienti
for env in development staging production; do
    echo "=== myapp-$env ==="
    kubectl get deployment -n "myapp-$env" -o wide 2>/dev/null || echo "Non ancora deployato"
done

# Sync manuale di produzione (simula approvazione umana)
echo ""
echo "Sincronizzazione manuale produzione:"
argocd app sync myapp-production --revision HEAD
# Output:
# TIMESTAMP          GROUP  KIND        NAMESPACE         NAME           STATUS  HEALTH   HOOK  MESSAGE
# 2026-07-16T10:...  apps   Deployment  myapp-production  helm-guestbook Synced  Healthy        ...
```

---

### Esercizio B4: ApplicationSet con Generatore Git (Directory)

Questo generatore è particolarmente potente: scopre automaticamente le applicazioni
in base alla struttura delle directory nel repo.

```bash
# Crea una struttura di directory simulata per il lab
mkdir -p gitops-config/{apps/{order-service,payment-service,inventory-service},infra/{monitoring,networking}}

# Crea kustomization.yaml in ogni directory app
for app in order-service payment-service inventory-service; do
    cat > "gitops-config/apps/$app/kustomization.yaml" <<YAML
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
YAML
    
    cat > "gitops-config/apps/$app/deployment.yaml" <<YAML
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: $app
  template:
    metadata:
      labels:
        app: $app
    spec:
      containers:
        - name: app
          image: nginx:stable-alpine
          ports:
            - containerPort: 80
YAML
done

# In un ambiente reale, pushiamo su GitHub.
# Per il lab, usiamo un ApplicationSet con repo già esistente e path fisso.

# Questo ApplicationSet mostra la struttura del generatore Git
cat <<'APPSET' 
# Esempio ApplicationSet con Git Directory Generator
# (Richiede repo Git reale con la struttura sopra descritta)
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: git-discovery
  namespace: argocd
spec:
  generators:
    - git:
        repoURL: https://github.com/myorg/gitops-config
        revision: HEAD
        directories:
          - path: "apps/*"    # ogni sottocartella di apps/ diventa una Application
  
  template:
    metadata:
      name: "{{path.basename}}"    # nome = nome della cartella
    spec:
      project: default
      source:
        repoURL: https://github.com/myorg/gitops-config
        targetRevision: HEAD
        path: "{{path}}"           # path = percorso completo della cartella
      destination:
        server: https://kubernetes.default.svc
        namespace: "{{path.basename}}"
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
APPSET

echo "[INFO] Esempio ApplicationSet Git Directory Generator mostrato sopra"
echo "[INFO] Richiede repo Git reale — in questo lab usiamo il generatore List (già fatto)"
```

---

## PART C: ARGO ROLLOUTS — PROGRESSIVE DELIVERY

### Concetto C1: Rollout vs Deployment

> **Analogia.** Un `Deployment` Kubernetes è come un interruttore della luce:
> on/off, tutto o niente. Quando aggiorni l'immagine, Kubernetes aggiorna tutti
> i pod (rolling update) ma senza nessun meccanismo di analisi delle metriche.
>
> Un `Rollout` di Argo Rollouts è come un dimmer: vai da 0 a 100% gradualmente,
> ti fermi a ogni step, misuri se la luce è troppo intensa o troppo fioca
> (metriche), e solo quando sei soddisfatto continui. Se qualcosa va storto,
> torni automaticamente all'impostazione precedente.

```
DEPLOYMENT vs ROLLOUT:

DEPLOYMENT K8s (rolling update):
  replicas: 5, maxUnavailable: 1, maxSurge: 1
  
  Inizia: Pod1(v1) Pod2(v1) Pod3(v1) Pod4(v1) Pod5(v1)
  Step 1: Pod1(v2) Pod2(v1) Pod3(v1) Pod4(v1) Pod5(v1)
  Step 2: Pod1(v2) Pod2(v2) Pod3(v1) Pod4(v1) Pod5(v1)
  ...
  Fine:   Pod1(v2) Pod2(v2) Pod3(v2) Pod4(v2) Pod5(v2)
  
  Nessuna analisi metriche. Rollback manuale.

ROLLOUT Argo Rollouts (canary):
  replicas: 5, steps: [5%, 20%, 50%, 100%]
  
  Stato 0: stable(v1)=5,  canary(v2)=0
  Step 1:  stable(v1)=4,  canary(v2)=1  → 20% traffico a v2
           Analisi: error rate < 1%? latenza p99 < 200ms?
           → OK → continua
  Step 2:  stable(v1)=3,  canary(v2)=2  → 40% traffico a v2
           Analisi: metriche ancora OK?
           → OK → continua
  Step 3:  stable(v1)=0,  canary(v2)=5  → 100%
           v2 promosso a stable
  
  Se in qualsiasi step metriche falliscono:
           stable(v1)=5,  canary(v2)=0  → rollback automatico
```

---

### Esercizio C1: Installare Argo Rollouts

```bash
# Installa Argo Rollouts
kubectl create namespace argo-rollouts || true

helm install argo-rollouts argo/argo-rollouts \
    --namespace argo-rollouts \
    --version 2.37.7 \
    --set dashboard.enabled=true \
    --set dashboard.service.type=NodePort \
    --set dashboard.service.nodePort=30081 \
    --wait

# Verifica installazione
kubectl get pods -n argo-rollouts

# Output atteso:
# NAME                             READY   STATUS    RESTARTS   AGE
# argo-rollouts-xxx                1/1     Running   0          2m
# argo-rollouts-dashboard-xxx      1/1     Running   0          2m

# Installa kubectl plugin per Argo Rollouts
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts

# Verifica plugin
kubectl argo rollouts version
# argo-rollouts: v1.7.0
```

---

### Esercizio C2: Canary Deployment con Argo Rollouts

Prima di tutto, creiamo l'applicazione demo che useremo per il canary.

```bash
# Namespace per il lab canary
kubectl create namespace rollouts-demo || true
```

```bash
# Crea file rollout-canary.yaml
cat > rollout-canary.yaml << 'EOF'
---
# Il Rollout sostituisce il Deployment
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: order-service
  namespace: rollouts-demo
spec:
  replicas: 5
  selector:
    matchLabels:
      app: order-service
  template:
    metadata:
      labels:
        app: order-service
    spec:
      containers:
        - name: app
          # Versione 1: blue (nginx con pagina di default)
          image: nginx:1.26-alpine
          ports:
            - name: http
              containerPort: 80
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 100m
              memory: 128Mi
          # Health checks: fondamentali per il canary (Rollouts non promuove se unhealthy)
          livenessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 10
            periodSeconds: 5
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 3
  
  strategy:
    canary:
      # Service per il canary (peso gestito da Rollouts via Kubernetes Service)
      canaryService: order-service-canary     # service che punta al canary
      stableService: order-service-stable     # service che punta alla versione stabile
      
      steps:
        # Step 1: 10% del traffico al canary
        - setWeight: 10
        # Pausa 2 minuti per osservare metriche
        - pause:
            duration: 2m
        # Step 2: 25% del traffico al canary
        - setWeight: 25
        - pause:
            duration: 2m
        # Step 3: 50% del traffico al canary
        - setWeight: 50
        - pause:
            duration: 2m
        # Step 4: pausa indefinita (richiede approvazione manuale in PRODUZIONE)
        # Per il lab: commentiamo questo step
        # - pause: {}
        # Step 5: promozione completa
        - setWeight: 100

---
# Service per la versione stabile (primary)
apiVersion: v1
kind: Service
metadata:
  name: order-service-stable
  namespace: rollouts-demo
spec:
  selector:
    app: order-service
  ports:
    - port: 80
      targetPort: 80
  type: ClusterIP

---
# Service per il canary
apiVersion: v1
kind: Service
metadata:
  name: order-service-canary
  namespace: rollouts-demo
spec:
  selector:
    app: order-service
  ports:
    - port: 80
      targetPort: 80
  type: ClusterIP

---
# Service principale (esposto all'esterno, bilancia tra stable e canary)
apiVersion: v1
kind: Service
metadata:
  name: order-service
  namespace: rollouts-demo
spec:
  selector:
    app: order-service
  ports:
    - port: 80
      targetPort: 80
  type: ClusterIP
EOF

kubectl apply -f rollout-canary.yaml

# Verifica che il Rollout sia healthy
kubectl argo rollouts status order-service -n rollouts-demo --watch

# Output atteso:
# Progressing - more replicas need to be updated
# Paused - CanaryPauseStep
# Healthy
```

---

### Esercizio C3: Aggiornare il Canary (simulare un deploy)

```bash
# Aggiorna l'immagine per avviare un canary deployment
# Cambiamo da nginx:1.26 a nginx:1.27 (simuliamo v2.0)
kubectl argo rollouts set image order-service \
    app=nginx:1.27-alpine \
    -n rollouts-demo

# Monitora il canary in tempo reale
kubectl argo rollouts get rollout order-service -n rollouts-demo --watch

# Output atteso (si aggiorna ogni pochi secondi):
# Name:            order-service
# Namespace:       rollouts-demo
# Status:          ॥ Paused
# Message:         CanaryPauseStep
# Strategy:        Canary
#   Step:          1/5
#   SetWeight:     10
#   ActualWeight:  10
#
# IMAGE                    TAG           WEIGHT  PODS
# nginx                    1.26-alpine   90      4
# nginx                    1.27-alpine   10      1
#
# [Dopo 2 minuti]:
# Status: ॥ Paused
# Step: 2/5, SetWeight: 25, ActualWeight: 25
# ...

# In parallelo (apri altro terminale): osserva i pod
watch kubectl get pods -n rollouts-demo \
    -o 'custom-columns=NAME:.metadata.name,IMAGE:.spec.containers[0].image,STATUS:.status.phase'

# Output atteso:
# NAME                    IMAGE               STATUS
# order-service-xxx-aaa   nginx:1.26-alpine   Running  ← stable
# order-service-xxx-bbb   nginx:1.26-alpine   Running  ← stable
# order-service-xxx-ccc   nginx:1.26-alpine   Running  ← stable
# order-service-xxx-ddd   nginx:1.26-alpine   Running  ← stable
# order-service-yyy-eee   nginx:1.27-alpine   Running  ← canary (10%)

# Dopo il completamento automatico degli step:
# order-service-yyy-aaa   nginx:1.27-alpine   Running  ← tutti promossi
# order-service-yyy-bbb   nginx:1.27-alpine   Running
# order-service-yyy-ccc   nginx:1.27-alpine   Running
# order-service-yyy-ddd   nginx:1.27-alpine   Running
# order-service-yyy-eee   nginx:1.27-alpine   Running

echo "[OK] Canary completato: tutti i pod ora usano nginx:1.27-alpine"
```

---

### Esercizio C4: Rollback Manuale e Automatico

```bash
# Scenario 1: Rollback MANUALE (aborti un canary in corso)
# Avvia un nuovo canary
kubectl argo rollouts set image order-service \
    app=nginx:1.28-alpine \
    -n rollouts-demo

# Aspetta che sia al 10%
sleep 30

# Controlla stato
kubectl argo rollouts get rollout order-service -n rollouts-demo

# Aborti il canary (rollback immediato a versione stabile)
kubectl argo rollouts abort order-service -n rollouts-demo

# Output atteso:
# rollout 'order-service' aborted

kubectl argo rollouts get rollout order-service -n rollouts-demo

# Output atteso:
# Status: ✖ Degraded
# Message: RolloutAborted: Rollout aborted update to revision 3
# 
# IMAGE                    TAG           WEIGHT  PODS
# nginx                    1.27-alpine   100     5    ← torna a 1.27 (la stabile)
# nginx                    1.28-alpine   0       0    ← azzerato

# Per rimettere in stato Healthy dopo un abort:
kubectl argo rollouts undo order-service -n rollouts-demo

# Output atteso:
# Status: ✔ Healthy
```

---

### Esercizio C5: Blue-Green Deployment

```bash
cat > rollout-blue-green.yaml << 'EOF'
---
# Blue-Green Rollout per payment-service
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: payment-service
  namespace: rollouts-demo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: payment-service
  template:
    metadata:
      labels:
        app: payment-service
    spec:
      containers:
        - name: app
          image: nginx:1.26-alpine
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 100m
              memory: 128Mi
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 3
  
  strategy:
    blueGreen:
      # Service per il traffico produzione (BLUE → diventa GREEN dopo promozione)
      activeService: payment-service-active
      
      # Service per il preview (NUOVA versione, traffico 0% — solo test interni)
      previewService: payment-service-preview
      
      # NON promuovere automaticamente — richiede approvazione manuale
      autoPromotionEnabled: false
      
      # Quanto aspettare prima di ridurre i vecchi pod a 0 dopo la promozione
      scaleDownDelaySeconds: 60

---
# Service ACTIVE (produzione, 100% traffico)
apiVersion: v1
kind: Service
metadata:
  name: payment-service-active
  namespace: rollouts-demo
spec:
  selector:
    app: payment-service
  ports:
    - port: 80
      targetPort: 80

---
# Service PREVIEW (nuova versione, 0% traffico reale)
apiVersion: v1
kind: Service
metadata:
  name: payment-service-preview
  namespace: rollouts-demo
spec:
  selector:
    app: payment-service
  ports:
    - port: 80
      targetPort: 80
EOF

kubectl apply -f rollout-blue-green.yaml

# Aspetta che sia Healthy
kubectl argo rollouts status payment-service -n rollouts-demo

# Aggiorna immagine → avvia blue-green
kubectl argo rollouts set image payment-service \
    app=nginx:1.27-alpine \
    -n rollouts-demo

# Osserva: la nuova versione (GREEN/preview) parte ma il traffico resta su BLUE/active
kubectl argo rollouts get rollout payment-service -n rollouts-demo

# Output atteso:
# Name:            payment-service
# Namespace:       rollouts-demo
# Status:          ॥ Paused
# Message:         BlueGreenPause
# Strategy:        BlueGreen
#
# NAME               KIND        STATUS     AGE  INFO
# payment-service    Rollout     Paused     1m
# ├ # revision:2
# │ └ payment-service-yyy   ReplicaSet  Healthy  30s  preview
# └ # revision:1
#   └ payment-service-xxx   ReplicaSet  Healthy  2m   active

echo ""
echo "=== VERIFICA PRE-PROMOZIONE ==="
echo "La versione GREEN (preview) è deployata ma riceve 0% traffico"
echo "Esegui i tuoi smoke test sulla preview service:"

# Esempio smoke test sulla versione preview
kubectl port-forward svc/payment-service-preview 8888:80 -n rollouts-demo &
PF_PID=$!
sleep 3

curl -sf http://localhost:8888/ | head -5
echo "[OK] Preview service risponde correttamente"

kill $PF_PID 2>/dev/null

echo ""
echo "=== PROMOZIONE MANUALE (simula approvazione) ==="
# Promuovi la versione preview a active (switch del traffico)
kubectl argo rollouts promote payment-service -n rollouts-demo

# Output atteso:
# rollout 'payment-service' promoted

kubectl argo rollouts get rollout payment-service -n rollouts-demo

# Output atteso:
# Status:          ✔ Healthy
# Strategy:        BlueGreen
#
# NAME               KIND        STATUS     AGE  INFO
# payment-service    Rollout     Healthy    5m
# ├ # revision:2
# │ └ payment-service-yyy   ReplicaSet  Healthy  3m   active     ← promossa!
# └ # revision:1
#   └ payment-service-xxx   ReplicaSet  Healthy  5m   delay:28s  ← in scale-down
```

---

## PART D: FLAGGER — CANARY CON ANALISI METRICHE AUTOMATICA

### Concetto D1: Flagger vs Argo Rollouts

> **Analogia.** Argo Rollouts è come un semaforo con timer: avanza di 10% ogni 2 minuti
> indipendentemente da quello che sta succedendo nel traffico. È efficace, ma non sa
> se ci sono incidenti.
>
> Flagger è come un sistema di traffico intelligente: avanza solo se i sensori di traffico
> (Prometheus) confermano che non ci sono incidenti. Se rileva un incidente durante
> il canary, torna automaticamente allo stato precedente — senza che nessuno debba
> guardare le dashboard alle 3 di notte.

```
FLUSSO FLAGGER CON ANALISI METRICHE:

Developer: kubectl set image deployment/order-service app=v2.0
                            ↓
Flagger rileva il cambio sul Deployment
                            ↓
Crea order-service-canary (nuova versione, 0% traffico)
                            ↓
Ogni X secondi (interval: 1m):
  1. Chiede a Prometheus: request-success-rate degli ultimi 5 min
     Risposta: 99.5% ✓ (threshold: min 99%)
  2. Chiede a Prometheus: request-duration p99 degli ultimi 5 min
     Risposta: 180ms ✓ (threshold: max 500ms)
  → Metriche OK → aumenta peso canary di 10%
                            ↓
Dopo 5 step (10% → 20% → 30% → 40% → 50%):
  Se TUTTE le metriche sono state OK: promozione → v2.0 diventa primary
  Se UNA metrica fallisce: rollback → primary resta al 100%
```

---

### Esercizio D1: Installare Flagger con Nginx

```bash
# Installa Flagger (usa nginx ingress come mesh per il lab — non richiede Istio)
helm repo add flagger https://flagger.app
helm repo update

# Installa ingress-nginx prima di Flagger
helm install ingress-nginx ingress-nginx/ingress-nginx \
    --namespace ingress-nginx \
    --create-namespace \
    --set controller.metrics.enabled=true \
    --set "controller.podAnnotations.prometheus\.io/scrape=true" \
    --set "controller.podAnnotations.prometheus\.io/port=10254" \
    --wait

# Installa Flagger con provider nginx
helm install flagger flagger/flagger \
    --namespace ingress-nginx \
    --set metricsServer=http://prometheus-operated.monitoring:9090 \
    --set meshProvider=nginx \
    --wait

kubectl get pods -n ingress-nginx

# Output atteso:
# NAME                           READY  STATUS   RESTARTS  AGE
# ingress-nginx-controller-xxx   1/1    Running  0         2m
# flagger-xxx                    1/1    Running  0         1m
```

---

### Esercizio D2: Installare Prometheus per le Metriche

```bash
# Installa kube-prometheus-stack (Prometheus + Grafana + AlertManager)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
    --namespace monitoring \
    --create-namespace \
    --set grafana.service.type=NodePort \
    --set grafana.service.nodePort=30082 \
    --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
    --wait

echo "[OK] Prometheus installato nel namespace monitoring"
echo "     Grafana disponibile su: http://localhost:30082 (admin/prom-operator)"
```

---

### Esercizio D3: Creare Canary Object Flagger

```bash
# Namespace per demo Flagger
kubectl create namespace flagger-demo || true

# Deployment base (Flagger gestirà questo Deployment)
cat <<'EOF' | kubectl apply -f -
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-service
  namespace: flagger-demo
  labels:
    app: api-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: api-service
  template:
    metadata:
      labels:
        app: api-service
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8080"
        prometheus.io/path: "/metrics"
    spec:
      containers:
        - name: app
          image: ghcr.io/stefanprodan/podinfo:6.7.0    # app demo con metriche Prometheus
          ports:
            - name: http
              containerPort: 9898
          env:
            - name: PODINFO_UI_COLOR
              value: "#blue"           # cambia colore per visualizzare la versione
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 200m
              memory: 256Mi
          readinessProbe:
            httpGet:
              path: /readyz
              port: 9898
            initialDelaySeconds: 5
            periodSeconds: 3
          livenessProbe:
            httpGet:
              path: /healthz
              port: 9898
            initialDelaySeconds: 10
            periodSeconds: 5

---
# Service per l'app
apiVersion: v1
kind: Service
metadata:
  name: api-service
  namespace: flagger-demo
spec:
  selector:
    app: api-service
  ports:
    - name: http
      port: 80
      targetPort: 9898

---
# HorizontalPodAutoscaler (Flagger lo rispetta)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-service
  namespace: flagger-demo
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
EOF

# Ora crea l'oggetto Canary (Flagger prende il controllo del Deployment)
cat <<'EOF' | kubectl apply -f -
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: api-service
  namespace: flagger-demo
spec:
  # Il Deployment da gestire
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-service
  
  # L'HPA da rispettare
  autoscalerRef:
    apiVersion: autoscaling/v2
    kind: HorizontalPodAutoscaler
    name: api-service
  
  # Configurazione del Service (porta 80 → porta 9898 del pod)
  service:
    port: 80
    targetPort: 9898
    portName: http
  
  # Strategia canary
  analysis:
    interval: 1m         # analizza ogni minuto
    threshold: 5         # max 5 analisi consecutive fallite prima del rollback
    maxWeight: 50        # massimo 50% al canary
    stepWeight: 10       # incrementa del 10% per step
    
    # Metriche di successo (usa metriche nginx dell'ingress controller)
    metrics:
      # Success rate: almeno 99% delle richieste deve avere successo (non 5xx)
      - name: request-success-rate
        # provider: usa provider built-in di Flagger per nginx
        thresholdRange:
          min: 99
        interval: 1m
      
      # Latenza: meno di 500ms per il 99° percentile
      - name: request-duration
        thresholdRange:
          max: 500
        interval: 1m
    
    # Webhooks: test automatici durante il canary
    webhooks:
      # Smoke test: verifica che il canary risponda correttamente
      - name: smoke-test
        type: pre-rollout
        url: http://flagger-loadtester.flagger-demo/
        timeout: 15s
        metadata:
          type: bash
          cmd: >
            curl -sf
            http://api-service-canary.flagger-demo/
            | grep -q "greetings from podinfo"
      
      # Load test: genera traffico durante il canary per avere dati metriche
      - name: load-test
        url: http://flagger-loadtester.flagger-demo/
        timeout: 5s
        metadata:
          type: cmd
          cmd: >
            hey -z 1m -q 5 -c 2
            http://api-service-canary.flagger-demo/
EOF

# Flagger Load Tester (genera carico per avere metriche durante il canary)
helm install flagger-loadtester flagger/loadtester \
    --namespace flagger-demo

# Aspetta che Flagger inizializzi il Canary
kubectl get canary api-service -n flagger-demo --watch

# Output atteso (può richiedere 1-2 minuti):
# NAME          STATUS         WEIGHT  LASTTRANSITIONTIME
# api-service   Initializing   0       2026-07-16T10:00:00Z
# api-service   Initialized    0       2026-07-16T10:01:00Z

echo "[OK] Flagger ha inizializzato il canary"
echo "     Ha creato automaticamente:"
kubectl get deployments -n flagger-demo
# api-service-primary   ← versione stabile (Flagger crea questo)
# api-service           ← canary (controllato da Flagger)
```

---

### Esercizio D4: Avviare un Canary con Flagger

```bash
# Avvia il canary aggiornando l'immagine del Deployment
# NOTA: aggiorna il Deployment originale (non primary)
kubectl set image deployment/api-service \
    app=ghcr.io/stefanprodan/podinfo:6.8.0 \
    -n flagger-demo

# Osserva il progresso del canary
kubectl get canary api-service -n flagger-demo --watch

# Output atteso (ogni minuto aggiorna):
# NAME          STATUS        WEIGHT  LASTTRANSITIONTIME
# api-service   Progressing   0       2026-07-16T10:05:00Z
# api-service   Progressing   10      2026-07-16T10:06:00Z   ← 10% canary
# api-service   Progressing   20      2026-07-16T10:07:00Z   ← 20% canary
# api-service   Progressing   30      2026-07-16T10:08:00Z   ← 30% canary
# api-service   Progressing   40      2026-07-16T10:09:00Z   ← 40% canary
# api-service   Progressing   50      2026-07-16T10:10:00Z   ← 50% canary
# api-service   Promoting     50      2026-07-16T10:11:00Z   ← promuovendo
# api-service   Finalising    0       2026-07-16T10:12:00Z   ← finalizzando
# api-service   Succeeded     0       2026-07-16T10:13:00Z   ← completato!

# Verifica che primary ora usi la nuova immagine
kubectl get deployment api-service-primary -n flagger-demo \
    -o jsonpath='{.spec.template.spec.containers[0].image}'
# ghcr.io/stefanprodan/podinfo:6.8.0

echo "[OK] Canary completato! api-service-primary usa la nuova versione 6.8.0"
```

---

### Esercizio D5: Simulare un Canary Fallito (Rollback Automatico)

```bash
# Avvia un canary con una versione "rotta" che genera errori
# podinfo supporta flag --grpc-port e variabili per simulare errori
kubectl set env deployment/api-service \
    PODINFO_DELAY=3 \
    -n flagger-demo

# (Oppure: aggiorna a un'immagine che simula errori HTTP)
kubectl set image deployment/api-service \
    app=ghcr.io/stefanprodan/podinfo:6.9.0 \
    -n flagger-demo

# Nota: la versione 6.9.0 con PODINFO_DELAY=3 causerà latenza > 500ms
# → Flagger rileverà che la metrica request-duration supera il threshold
# → Dopo 5 analisi consecutive fallite → rollback automatico

kubectl get canary api-service -n flagger-demo --watch

# Output atteso (rollback in ~5 minuti):
# NAME          STATUS        WEIGHT  LASTTRANSITIONTIME
# api-service   Progressing   10      10:20:00Z
# api-service   Progressing   10      10:21:00Z   ← latenza alta, no avanzamento
# api-service   Progressing   10      10:22:00Z   ← ancora alta
# api-service   Progressing   10      10:23:00Z   ← threshold: 3/5 failure
# api-service   Progressing   10      10:24:00Z   ← threshold: 4/5 failure
# api-service   Failed        0       10:25:00Z   ← ROLLBACK! 5 failure consecutivi

# Verifica eventi Flagger per capire il motivo del rollback
kubectl get events -n flagger-demo \
    --field-selector reason=CanaryFailed \
    --sort-by=lastTimestamp

# Output atteso:
# LAST SEEN  TYPE     REASON        OBJECT             MESSAGE
# 1m         Warning  CanaryFailed  canary/api-service  Halt api-service.flagger-demo
#                                                       advancement request-duration
#                                                       500.00 > 500.00

echo "[OK] Rollback automatico avvenuto — primary non è stato modificato"
kubectl get deployment api-service-primary -n flagger-demo \
    -o jsonpath='{.spec.template.spec.containers[0].image}'
# ghcr.io/stefanprodan/podinfo:6.8.0  ← resta la versione precedente
```

---

## PART E: INTEGRAZIONE ARGOCD + ARGO ROLLOUTS

### Esercizio E1: ArgoCD Application che Gestisce un Rollout

```bash
# La combinazione ArgoCD + Argo Rollouts è la più potente per GitOps:
# ArgoCD sincronizza i manifesti da Git, Argo Rollouts gestisce la strategia di deploy

# Crea un Application ArgoCD che punta al namespace con il Rollout
cat <<'EOF' | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: payment-service-gitops
  namespace: argocd
spec:
  project: default
  
  source:
    # In produzione: repo con i manifesti del Rollout
    # Per il lab: usiamo i manifesti già applicati localmente
    repoURL: https://github.com/argoproj/argo-rollouts
    targetRevision: stable
    path: examples/nginx     # esempi ufficiali con Rollout + nginx
  
  destination:
    server: https://kubernetes.default.svc
    namespace: rollouts-demo-gitops
  
  # Importante: ArgoCD deve ignorare le diff sullo stato del Rollout
  # (il canary weight viene modificato da Argo Rollouts, non da Git)
  ignoreDifferences:
    - group: argoproj.io
      kind: Rollout
      jsonPointers:
        - /spec/replicas    # gestito dall'HPA
        - /spec/paused      # gestito dal canary
  
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
      - RespectIgnoreDifferences=true   # rispetta ignoreDifferences sopra
EOF

echo "[INFO] Application ArgoCD creata per gestire Rollout"
echo "       Apri http://localhost:30080 per visualizzare lo stato nell'UI ArgoCD"
echo ""
echo "       Nota: l'UI ArgoCD mostra lo stato del Rollout con barre di avanzamento"
echo "       e permette di promuovere/abortire il canary direttamente dalla UI"
```

---

## PART F: DASHBOARD E MONITORING

### Esercizio F1: Argo Rollouts Dashboard

```bash
# La dashboard di Argo Rollouts mostra lo stato di tutti i Rollout
echo "Argo Rollouts Dashboard disponibile su: http://localhost:30081"
echo ""
echo "Dalla dashboard puoi:"
echo "  1. Vedere tutti i Rollout nel cluster"
echo "  2. Visualizzare il progresso del canary con barra colorata"
echo "  3. Promuovere o abortire un canary con un click"
echo "  4. Vedere la storia dei deployment (revision history)"
echo ""

# Visualizza tutti i Rollout via CLI
kubectl argo rollouts list rollouts --all-namespaces

# Output atteso:
# NAMESPACE       NAME              DESIRED  CURRENT  UP-TO-DATE  AVAILABLE  STATUS        LABELS
# rollouts-demo   order-service     5        5        5           5          Healthy       app=order-service
# rollouts-demo   payment-service   3        3        3           3          Healthy       app=payment-service
```

---

### Esercizio F2: Query Prometheus per Rollout Metrics

```bash
# Port-forward Prometheus
kubectl port-forward svc/prometheus-operated 9090:9090 -n monitoring &
PROM_PID=$!
sleep 3

echo "=== QUERY PROMETHEUS PER GITOPS METRICS ==="
echo ""

# Query 1: Success rate per namespace
echo "1. Success rate dei servizi nelle ultime ore:"
curl -sf "http://localhost:9090/api/v1/query" \
    --data-urlencode 'query=sum(rate(nginx_ingress_controller_requests{status!~"5.."}[5m])) by (ingress) / sum(rate(nginx_ingress_controller_requests[5m])) by (ingress)' | \
    python3 -c "
import sys, json
data = json.load(sys.stdin)
for r in data.get('data', {}).get('result', []):
    ingress = r['metric'].get('ingress', 'N/A')
    value = float(r['value'][1]) * 100
    print(f'  {ingress}: {value:.2f}%')
" 2>/dev/null || echo "  [INFO] Nessuna metrica ingress disponibile (ingress non ha traffico)"

echo ""

# Query 2: Rollout status
echo "2. Pod per versione (canary vs stable):"
kubectl get pods --all-namespaces \
    -o jsonpath='{range .items[*]}{.metadata.namespace}{"\t"}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}' | \
    grep -E "rollouts|flagger" | head -20

kill $PROM_PID 2>/dev/null
```

---

## Conclusioni e Prossimi Passi

```
COMPETENZE ACQUISITE IN QUESTO LAB:

GITOPS:
  ✓ ArgoCD: installazione via Helm, Application con sync automatico
  ✓ SelfHeal: ArgoCD corregge automaticamente la deriva
  ✓ ApplicationSet: genera N Application da template + generatori
  ✓ Strategie RollingSync per progressione controllata degli ambienti

PROGRESSIVE DELIVERY:
  ✓ Argo Rollouts: canary con step progressivi (10% → 25% → 50% → 100%)
  ✓ Argo Rollouts: blue-green con promozione manuale
  ✓ Rollback manuale (abort) e tramite undo
  ✓ Flagger: canary con analisi metriche Prometheus automatica
  ✓ Flagger: rollback automatico su threshold superato

INTEGRAZIONE:
  ✓ ArgoCD + Argo Rollouts: GitOps che gestisce Rollout (ignoreDifferences)
  ✓ Flagger + Prometheus: analisi automatica della salute del canary
  ✓ Load testing durante il canary (flagger-loadtester)

DIFFERENZE CHIAVE:
  Argo Rollouts: step temporali (ogni N minuti avanza), nessuna metrica auto
  Flagger: step basati su metriche (avanza solo se salute OK)
  Combinazione: ArgoCD (GitOps) + Argo Rollouts (strategia delivery)
```

### Quando Usare Cosa

```
ARGOCD APPLICATIONSET:
  → Gestione multi-ambiente (dev/staging/prod) con un template
  → Multi-cluster con configurazioni diverse per cluster
  → Scoperta automatica di applicazioni da struttura Git

ARGO ROLLOUTS CANARY:
  → Release graduale con step temporali
  → Non hai Istio/Linkerd ma vuoi canary
  → Integrazione con ArgoCD già presente

FLAGGER CANARY:
  → Rollback automatico basato su metriche Prometheus
  → Hai Istio o NGINX ingress
  → Vuoi analisi metriche automatica senza supervisione manuale

BLUE-GREEN:
  → Servizi stateful o con lunga inizializzazione
  → Cambio di schema database (migrazione → smoke test → switch)
  → Quando il rollback istantaneo è più importante del costo risorse
```

### Riferimenti

```
DOCUMENTAZIONE:
  ArgoCD:          https://argo-cd.readthedocs.io
  ApplicationSet:  https://argocd-applicationset.readthedocs.io
  Argo Rollouts:   https://argoproj.github.io/argo-rollouts/
  Flagger:         https://docs.flagger.app
  OpenGitOps:      https://opengitops.dev

PROSSIMO TUTORIAL:
  → tutorial_plat24_sre_lab.md
     Site Reliability Engineering: error budget, toil automation, chaos engineering come pratica
```

---

> **Documento di riferimento:** `23-gitops-avanzato.md` — Modulo 23, Gestione Piattaforme
> **Versioni testate:** ArgoCD 2.13 (Helm chart 7.7.0), Argo Rollouts 1.7 (Helm 2.37.7),
> Flagger 1.40, kube-prometheus-stack 65.x
> **Ultimo aggiornamento:** 2026-07-16
