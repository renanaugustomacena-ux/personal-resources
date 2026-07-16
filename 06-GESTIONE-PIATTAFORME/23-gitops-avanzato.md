---
corso: "Gestione Piattaforme e DevOps"
fase: "7 — Architetture Avanzate"
modulo: 23
titolo: "GitOps Avanzato: ArgoCD ApplicationSet, Flagger, Argo Rollouts"
versione: "ArgoCD 2.13 · ApplicationSet Controller 0.6 · Flagger 1.40 · Argo Rollouts 1.7 · Flux 2.4"
livello: "Avanzato"
prerequisiti:
  - "05-kubernetes.md"
  - "07-ci-cd.md"
  - "08-monitoring-observability.md"
obiettivi:
  - "Comprendere il modello GitOps push vs pull e i suoi invarianti"
  - "Usare ApplicationSet per gestire deployment multi-cluster e multi-ambiente"
  - "Implementare canary deployment con Flagger e analisi automatica delle metriche"
  - "Eseguire blue-green e canary deployment con Argo Rollouts"
  - "Configurare rollback automatico basato su SLO"
tag: [gitops, argocd, applicationset, flagger, argo-rollouts, canary, blue-green, progressive-delivery]
---

# GitOps Avanzato: ApplicationSet, Flagger, Argo Rollouts

> **Modulo 23** · **Aggiornamento:** 2026-07-16

## 1. GitOps — Il Modello Pull-Based

GitOps è un paradigma operativo in cui Git è la **single source of truth** per tutta
la configurazione del sistema. Il modello pull-based significa che l'operatore
(ArgoCD, Flux) effettua il pull dalla repository e applica le modifiche al cluster —
non viceversa.

### Principi GitOps (OpenGitOps v1.0, CNCF):

1. **Dichiarativo**: lo stato desiderato è espresso in modo dichiarativo
2. **Versionato**: lo stato desiderato è versionato in Git
3. **Pull automatico**: agenti approvati applicano automaticamente lo stato desiderato
4. **Riconciliazione continua**: agenti software si assicurano che lo stato attuale
   converga verso lo stato desiderato e segnalano le divergenze

```
PUSH vs PULL:

PUSH (tradizionale CI/CD):
  Pipeline → kubectl apply → Cluster
  Problemi:
    - La pipeline ha credenziali cluster (rischio sicurezza)
    - Se il cluster va offline durante il deploy → stato inconsistente
    - Nessuna riconciliazione continua (deriva possibile)

PULL (GitOps):
  Git Repo ← ArgoCD controller → Cluster
  ArgoCD vive DENTRO il cluster
  Vantaggi:
    - Nessuna credenziale cluster all'esterno
    - Riconciliazione automatica ogni 3 minuti
    - Deriva rilevata e corretta automaticamente
    - Git log = audit trail completo di tutti i cambiamenti
```

---

## 2. ArgoCD — Architettura

```
COMPONENTI ARGOCD:

argocd-server:           API server e UI web (porta 443/80)
argocd-repo-server:      clona e analizza i repo Git
argocd-application-controller: riconcilia lo stato K8s con Git
argocd-dex-server:       autenticazione OIDC/SAML
argocd-redis:            cache (sessioni, stato)
argocd-applicationset-controller: gestisce ApplicationSet (multi-app)

RISORSE CRD:
  Application:       singola applicazione con source e destination
  ApplicationSet:    genera N Application da un generatore
  AppProject:        limite di accesso (RBAC applicazioni)
  Repository:        credenziali repository Git
```

---

## 3. ApplicationSet — Deploy Multi-Ambiente e Multi-Cluster

`ApplicationSet` è un CRD che genera automaticamente multiple `Application`
ArgoCD a partire da template e generatori. Elimina la duplicazione di
configurazione quando si gestiscono molti ambienti o cluster.

### Generatori disponibili:

```yaml
# ApplicationSet con generatore List
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: my-service
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - env: development
            cluster: https://dev-k8s.myorg.com
            values:
              replicas: "1"
              cpu_limit: "500m"
          - env: staging
            cluster: https://staging-k8s.myorg.com
            values:
              replicas: "2"
              cpu_limit: "1000m"
          - env: production
            cluster: https://prod-k8s.myorg.com
            values:
              replicas: "5"
              cpu_limit: "2000m"
  
  template:
    metadata:
      name: "my-service-{{env}}"
    spec:
      project: default
      source:
        repoURL: https://github.com/myorg/my-service-config
        targetRevision: HEAD
        path: "environments/{{env}}"
        helm:
          parameters:
            - name: replicaCount
              value: "{{values.replicas}}"
            - name: resources.limits.cpu
              value: "{{values.cpu_limit}}"
      destination:
        server: "{{cluster}}"
        namespace: my-service
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true

---
# ApplicationSet con generatore Git (directory)
# Genera una Application per ogni cartella in infra/
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: infrastructure
  namespace: argocd
spec:
  generators:
    - git:
        repoURL: https://github.com/myorg/gitops-config
        revision: HEAD
        directories:
          - path: "infra/*"
            exclude: false
  
  template:
    metadata:
      name: "infra-{{path.basename}}"
    spec:
      project: default
      source:
        repoURL: https://github.com/myorg/gitops-config
        targetRevision: HEAD
        path: "{{path}}"
      destination:
        server: https://kubernetes.default.svc
        namespace: "{{path.basename}}"
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
```

---

## 4. Progressive Delivery — Canary e Blue-Green

Il **Progressive Delivery** è l'evoluzione del CD: invece di deployare tutto o niente,
si rilascia progressivamente il traffico alla nuova versione, verificando le metriche
ad ogni step. Se qualcosa va storto, il rollback è automatico.

```
CANARY DEPLOYMENT:

Step 1:  Nuova versione (canary) riceve il 10% del traffico
         → Metriche: error rate < 1%? latenza p99 < 200ms?
         → Se OK: continua

Step 2:  Canary riceve il 25% del traffico
         → Metriche: OK?
         → Se OK: continua

Step 3:  Canary riceve il 50% del traffico
         → Metriche: OK?
         → Se OK: continua

Step 4:  Canary riceve il 100% del traffico
         → Vecchia versione (primary) dismessa
         
Se in QUALSIASI step le metriche falliscono:
  → Rollback automatico a 0% canary (primary torna a 100%)
  → Alert inviato al team
```

---

## 5. Flagger — Canary Automatico con Analisi Metriche

Flagger è un controller K8s che automatizza il progressive delivery.
Funziona con: Istio, Linkerd, NGINX, Contour, App Mesh, Kubernetes Gateway API.

### Oggetti Flagger:

```yaml
# Canary object — definisce la strategia di rilascio progressivo
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: order-service
  namespace: production
spec:
  # Tipo di deployment da gestire
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: order-service
  
  # Virtual service (traffico con Istio)
  service:
    port: 80
    targetPort: 8080
    gateways:
      - istio-system/main-gateway
    hosts:
      - order-service.production.svc.cluster.local
  
  # Strategia di rilascio canary
  analysis:
    interval: 1m           # analisi ogni minuto
    threshold: 5           # max 5 analisi fallite prima del rollback
    maxWeight: 50          # max 50% traffico al canary
    stepWeight: 10         # incremento 10% per step
    
    # Metriche di successo
    metrics:
      - name: request-success-rate
        thresholdRange:
          min: 99          # almeno 99% di successo
        interval: 1m
      
      - name: request-duration
        thresholdRange:
          max: 500         # max 500ms p99
        interval: 1m
    
    # Webhook per test aggiuntivi durante il canary
    webhooks:
      - name: load-test
        url: http://flagger-loadtester.test/
        timeout: 5s
        metadata:
          cmd: "hey -z 1m -q 10 -c 2 http://order-service-canary.production/"
      
      - name: smoke-test
        type: pre-rollout    # eseguito PRIMA dell'inizio
        url: http://flagger-loadtester.test/
        timeout: 15s
        metadata:
          cmd: "curl -sf http://order-service-canary.production/health"
```

### Flusso Flagger:

```
FLUSSO CANARY FLAGGER:

1. Developer aggiorna il Deployment (nuova immagine nel tag)
   kubectl set image deployment/order-service app=myorg/order-service:v2.0
   
2. Flagger rileva il cambiamento (watch su Deployment)

3. Flagger crea:
   ├── order-service-primary (vecchia versione, 100%)
   └── order-service-canary  (nuova versione, 0%)

4. Flagger sposta traffico progressivamente:
   Minuto 0-1:   canary 10%, primary 90%  → analizza metriche
   Minuto 1-2:   canary 20%, primary 80%  → analizza metriche
   Minuto 2-3:   canary 30%, primary 70%  → analizza metriche
   ...
   Minuto 4-5:   canary 50%, primary 50%  → analizza metriche

5a. Se metriche OK:
    canary promosso → diventa il nuovo primary
    vecchio primary dismesso
    
5b. Se metriche falliscono (error rate > 1%):
    Rollback: canary → 0%, primary resta al 100%
    Evento K8s + alert Slack/PagerDuty
```

---

## 6. Argo Rollouts — Progressive Delivery Nativo

Argo Rollouts è un controller K8s che sostituisce `Deployment` con `Rollout`,
aggiungendo strategie avanzate di deployment.

```yaml
# Rollout con strategia canary
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: order-service
spec:
  replicas: 10
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
          image: myorg/order-service:v1.0
          ports:
            - containerPort: 8080
  
  strategy:
    canary:
      # Header-based routing (per test interni senza impatto su utenti reali)
      canaryService: order-service-canary
      stableService: order-service-stable
      trafficRouting:
        istio:
          virtualServices:
            - name: order-service-vs
              routes:
                - primary
      
      steps:
        - setWeight: 5         # 5% canary
        - pause:
            duration: 10m      # aspetta 10 minuti
        - setWeight: 20        # 20% canary
        - pause:
            duration: 10m
        - setWeight: 50        # 50% canary
        - pause: {}            # pause INDEFINITA: attende approvazione manuale
        - setWeight: 100       # promozione completa
      
      # Analisi automatica delle metriche
      analysis:
        templates:
          - templateName: success-rate-check
        startingStep: 2        # inizia a analizzare al secondo step
      
      # Anti-affinity: canary e stable su nodi diversi
      antiAffinity:
        requiredDuringSchedulingIgnoredDuringExecution: {}

---
# AnalysisTemplate: definisce le metriche da controllare
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate-check
spec:
  args:
    - name: service-name
  metrics:
    - name: success-rate
      interval: 1m
      successCondition: result[0] >= 0.99
      failureLimit: 3
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: |
            sum(rate(
              http_requests_total{
                job="{{args.service-name}}",
                status!~"5.."
              }[5m]
            )) /
            sum(rate(
              http_requests_total{
                job="{{args.service-name}}"
              }[5m]
            ))
    
    - name: avg-latency
      interval: 1m
      successCondition: result[0] <= 0.5
      failureLimit: 3
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: |
            histogram_quantile(0.99,
              rate(
                http_request_duration_seconds_bucket{
                  job="{{args.service-name}}"
                }[5m]
              )
            )

---
# Rollout con strategia Blue-Green
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: payment-service
spec:
  replicas: 5
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
          image: myorg/payment-service:v1.0
  
  strategy:
    blueGreen:
      activeService: payment-service-active     # serve il 100% traffico
      previewService: payment-service-preview   # traffico 0% (solo test interni)
      
      autoPromotionEnabled: false               # richiede approvazione manuale
      scaleDownDelaySeconds: 30                 # aspetta 30s prima di dismettere il vecchio
      
      prePromotionAnalysis:
        templates:
          - templateName: success-rate-check
        args:
          - name: service-name
            value: payment-service-preview       # testa la versione preview
      
      postPromotionAnalysis:
        templates:
          - templateName: success-rate-check
        args:
          - name: service-name
            value: payment-service-active        # verifica dopo la promozione
```

---

## 7. ApplicationSet con Rollout Multi-Cluster

```yaml
# ApplicationSet che deploya Argo Rollouts su tutti i cluster
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: order-service-rollout
  namespace: argocd
spec:
  generators:
    - matrix:
        generators:
          # Generator 1: cluster list
          - list:
              elements:
                - cluster: eu-west-1
                  server: https://eu-west-1.k8s.myorg.com
                  region: eu-west-1
                - cluster: us-east-1
                  server: https://us-east-1.k8s.myorg.com
                  region: us-east-1
          
          # Generator 2: ambienti per cluster
          - list:
              elements:
                - env: staging
                  canary_weight: "20"
                - env: production
                  canary_weight: "10"
  
  template:
    metadata:
      name: "order-service-{{cluster}}-{{env}}"
    spec:
      project: default
      source:
        repoURL: https://github.com/myorg/gitops-config
        targetRevision: HEAD
        path: "apps/order-service/{{env}}"
        helm:
          parameters:
            - name: canary.initialWeight
              value: "{{canary_weight}}"
            - name: region
              value: "{{region}}"
      destination:
        server: "{{server}}"
        namespace: "order-service-{{env}}"
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
          - RespectIgnoreDifferences=true
```

---

## 8. Confronto Strumenti Progressive Delivery

```
CONFRONTO:

FLAGGER:
  Pro:  integrazione service mesh (Istio/Linkerd), analisi metriche automatica
  Contro: richiede service mesh installato
  Casi d'uso: canary con analisi metriche real-time, ambienti con Istio

ARGO ROLLOUTS:
  Pro:  non richiede service mesh, UI dedicata, integrazione ArgoCD nativa
  Contro: sostituisce Deployment con Rollout (CRD custom)
  Casi d'uso: canary e blue-green senza service mesh, GitOps con ArgoCD

FLUX + FLAGGER:
  Pro:  GitOps pull-based completo (Flux) + progressive delivery (Flagger)
  Contro: due tool da gestire separatamente
  Casi d'uso: alternativa ad ArgoCD, uso enterprise

ARGOCD + ARGO ROLLOUTS:
  Combinazione raccomandata per team che già usano ArgoCD:
  ArgoCD gestisce il GitOps, Argo Rollouts gestisce la strategia di deployment.
  La UI ArgoCD mostra lo stato del Rollout in modo nativo.
```

---

## 9. Best Practices GitOps Avanzato

```
REGOLE D'ORO:

1. REPO SEPARATION (monorepo config vs codice)
   ✓ app-repo: codice sorgente, Dockerfile, test
   ✓ config-repo: manifesti K8s, helm values, kustomize
   ✓ La pipeline aggiorna il config-repo (immagine tag) → ArgoCD deploya
   ✗ Non: ArgoCD che guarda l'app-repo per i manifesti K8s

2. IMAGE TAG POLICY
   ✓ Tag immutabili (SHA digest): sha256:abc123...
   ✓ Mai tag :latest in produzione (non tracciabile in Git)
   ✓ Semantic versioning: v1.2.3
   ✗ Non: sovrascrivere tag esistenti

3. SYNC POLICY PRODUCTION
   ✓ staging: syncPolicy.automated (auto-sync da Git)
   ✓ production: syncPolicy NON automated (richiede approvazione)
   ✓ selfHeal: true in tutti gli ambienti (deriva corretta automaticamente)
   ✗ Non: auto-sync in produzione senza gate di approvazione

4. ROLLOUT CONFIGURATION
   ✓ steps progressivi: 5% → 20% → 50% → 100%
   ✓ pause tra ogni step (almeno 10 minuti per raccogliere metriche)
   ✓ failureLimit: massimo numero di analisi fallite prima del rollback
   ✗ Non: canary con step troppo grandi (salti 0% → 50%)

5. ANALISI METRICHE
   ✓ Almeno 2 metriche: error rate + latenza
   ✓ Window sufficientemente lunga (almeno 5 minuti) per dati stabili
   ✓ Threshold conservativi: meglio rollback eccessivo che degrado silenzioso
   ✗ Non: analisi solo sul canary (confronta sempre con baseline)

6. APPROVAZIONE MANUALE
   ✓ Production: sempre con gate di approvazione umana (pausa indefinita)
   ✓ L'approvazione è tracciata in Git (PR merge o annotation)
   ✗ Non: promozione automatica completa in produzione senza review
```

---

> **Versioni di riferimento:** ArgoCD 2.13 (2024-12), ApplicationSet Controller 0.6,
> Flagger 1.40 (2024-11), Argo Rollouts 1.7 (2024-10), Flux 2.4 (2024-11).
> OpenGitOps v1.0 Principles (CNCF TAG App Delivery, 2023).
> Progressive Delivery: Adam Zimman, LaunchDarkly, 2018 — termine introdotto.
