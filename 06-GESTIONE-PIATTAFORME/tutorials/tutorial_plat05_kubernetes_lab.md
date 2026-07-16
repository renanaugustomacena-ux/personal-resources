# Tutorial: Kubernetes — Orchestrazione Container — Lab Pratico

> **Documento di riferimento:** `05-kubernetes.md`
> **Dominio:** Gestione Piattaforme — Container Orchestration
> **Ambito:** K3s cluster locale, Pod/Deployment/Service/Ingress, ConfigMap/Secret, PV/PVC, RBAC, NetworkPolicy default-DENY, Pod Security Standards Restricted, HPA, StatefulSet, Helm 4, ArgoCD 3.x GitOps, troubleshooting CrashLoopBackOff/Pending
> **Durata lab:** 6-8 ore
> **Livello:** Intermedio-Avanzato — richiede conoscenza base di Docker e Linux CLI
> **Prerequisiti:** Docker Engine 29.x installato, kubectl installato, almeno 4GB RAM liberi, accesso internet per pull immagini
> **Ambiente:** K3s v1.35+ su macchina locale (singolo nodo), kubectl CLI, Helm 4, ArgoCD 3.x

---

## Lab Environment Setup

```bash
# === VERIFICA PREREQUISITI K8S LAB ===
echo "=== CHECK PREREQUISITI ==="

# Docker disponibile?
docker --version 2>/dev/null && echo "[OK] Docker disponibile" || echo "[FAIL] Docker mancante — installare Docker Engine 29.x"

# kubectl disponibile?
kubectl version --client 2>/dev/null && echo "[OK] kubectl disponibile" || echo "[WARN] kubectl non trovato — verrà installato con K3s"

# RAM disponibile (minimo 4GB raccomandato)
free_mb=$(free -m 2>/dev/null | awk 'NR==2{print $7}')
if [ -n "$free_mb" ]; then
  [ "$free_mb" -gt 3000 ] && echo "[OK] RAM disponibile: ${free_mb} MB" || echo "[WARN] RAM disponibile: ${free_mb} MB — minimo 4GB raccomandato"
fi

# Spazio disco (K3s + immagini richiedono ~3GB)
df -h / 2>/dev/null | awk 'NR==2{print "[INFO] Disco root:", $4, "disponibili"}'

# Porta 6443 (K3s API server) libera?
ss -tlnp 2>/dev/null | grep -q 6443 && echo "[WARN] Porta 6443 occupata — K3s potrebbe non avviarsi" || echo "[OK] Porta 6443 libera"

# Curl disponibile (per installare K3s)?
curl --version 2>/dev/null | head -1 && echo "[OK] curl disponibile" || echo "[FAIL] curl mancante"

echo ""
echo "=== AMBIENTE PRONTO PER IL LAB ==="
```

### Architettura del Lab

```
┌────────────────────────────────────────────────────────────────────┐
│                    MACCHINA LOCALE (HOST)                          │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              K3s Cluster (singolo nodo)                     │   │
│  │                                                             │   │
│  │  ┌──────────────────────────────────────────────────────┐   │   │
│  │  │                  CONTROL PLANE                       │   │   │
│  │  │  kube-apiserver :6443  │  etcd  │  scheduler         │   │   │
│  │  │  controller-manager    │  coredns :53                │   │   │
│  │  └──────────────────────────────────────────────────────┘   │   │
│  │                          │                                  │   │
│  │  ┌──────────────────────────────────────────────────────┐   │   │
│  │  │                  WORKER NODE (stesso nodo)           │   │   │
│  │  │                                                      │   │   │
│  │  │  namespace: default     namespace: kube-system       │   │   │
│  │  │  ┌──────────────┐       ┌──────────────────────┐     │   │   │
│  │  │  │ app-demo Pod │       │ traefik (Ingress)     │     │   │   │
│  │  │  │ :8080        │       │ :80, :443             │     │   │   │
│  │  │  └──────────────┘       └──────────────────────┘     │   │   │
│  │  │  ┌──────────────┐       ┌──────────────────────┐     │   │   │
│  │  │  │ postgres Pod │       │ falco (runtime sec)  │     │   │   │
│  │  │  │ :5432        │       │                      │     │   │   │
│  │  │  └──────────────┘       └──────────────────────┘     │   │   │
│  │  └──────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │   kubectl    │  │  Helm 4.x    │  │  ArgoCD UI :8080         │  │
│  │  (CLI tool)  │  │  (pkg mgr)   │  │  GitOps controller       │  │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

### Installazione K3s

```bash
# Installazione K3s (versione stabile 1.35.x)
# K3s è una distribuzione Kubernetes leggera (< 100MB) ideale per lab e sviluppo

curl -sfL https://get.k3s.io | INSTALL_K3S_VERSION="v1.35.0+k3s1" sh -

# Attendere che K3s sia pronto (30-60 secondi)
sudo k3s kubectl wait --for=condition=Ready node --all --timeout=120s

# Configurare kubectl per usare il cluster K3s
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $(id -u):$(id -g) ~/.kube/config

# Verificare che il cluster sia operativo
kubectl get nodes
# OUTPUT ATTESO:
# NAME          STATUS   ROLES                  AGE   VERSION
# lab-machine   Ready    control-plane,master   1m    v1.35.0+k3s1

kubectl get pods -A
# OUTPUT ATTESO: pod kube-system tutti in Running/Completed

echo "[OK] K3s cluster operativo"
```

### Installazione kubectl + Helm 4

```bash
# kubectl (se non già presente)
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# Helm 4 (rilasciato novembre 2025)
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
# Helm 4 viene installato automaticamente con lo stesso script
helm version
# OUTPUT ATTESO: version.BuildInfo{Version:"v4.x.x", ...}
```

---

## PART A: FONDAMENTI — Kubernetes come Orchestra

> Kubernetes risolve un problema concreto: quando hai 10 container, puoi gestirli a mano.
> Quando ne hai 1000, distribuiti su 20 macchine, con aggiornamenti continui e guasti imprevisti,
> hai bisogno di un sistema che prenda le decisioni al posto tuo. Kubernetes è quell'orchestratore.
> Il nome viene dal greco "kubernetes" (κυβερνήτης) — "timoniere" di una nave. Appropriato:
> tu definisci la rotta (stato desiderato), Kubernetes tiene il timone.

---

### Concetto A1: Lo Stato Desiderato vs Lo Stato Attuale

> **Analogia.** Immagina un termostato intelligente. Non gli dici "accendi il riscaldamento per
> 3 ore". Gli dici "voglio 21°C in questa stanza". Il termostato poi decide autonomamente quando
> accendere e spegnere, compensa le perdite di calore, e se il sensore guasta, entra in modalità
> sicura. Kubernetes funziona esattamente così: dichiari lo stato desiderato ("voglio 3 repliche
> di questa app"), e il sistema lavora continuamente per mantenere quella condizione —
> riavviando container che crashano, ridistribuendo sui nodi disponibili, scalando.

```
PARADIGMA IMPERATIVO (vecchio modo):
  "Avvia container A sul server 1"
  "Avvia container A sul server 2"
  "Avvia container A sul server 3"
  → Devi sapere dove avviarlo, devi ricordarti lo stato, devi gestire i guasti

PARADIGMA DICHIARATIVO (modo Kubernetes):
  "Voglio 3 repliche del container A, con 512MB RAM, porta 8080 esposta"
  → Kubernetes decide dove, monitora, ripara, scala
  → Tu descrivi il COSA, Kubernetes gestisce il COME

RECONCILIATION LOOP (ciclo di riconciliazione):
  ┌─────────────────────────────────────────────────┐
  │                                                 │
  │  STATO DESIDERATO         STATO ATTUALE         │
  │  (da YAML/etcd)           (nodi reali)          │
  │                                                 │
  │  replicas: 3    ──────→   replicas: 2           │
  │                                ↑                │
  │                     CONTROLLER vede la diff     │
  │                     e avvia 1 nuovo pod         │
  └─────────────────────────────────────────────────┘
  
  Questo ciclo gira ogni pochi secondi per OGNI oggetto.
```

```bash
# Vediamo il reconciliation loop in azione
kubectl create deployment demo --image=nginx:1.27 --replicas=3

# Eliminiamo manualmente un pod (simula un crash)
POD=$(kubectl get pods -l app=demo -o jsonpath='{.items[0].metadata.name}')
kubectl delete pod $POD

# Kubernetes crea immediatamente un nuovo pod per tornare a 3 repliche
kubectl get pods -w
# OUTPUT ATTESO: entro 10-15 secondi appare un nuovo pod in stato ContainerCreating → Running
```

---

### Concetto A2: L'Architettura a Due Livelli

> **Analogia.** In un grande ospedale ci sono due strutture distinte: la direzione sanitaria
> (prende decisioni su quale medico va dove, gestisce le risorse, monitora la situazione globale)
> e i reparti (dove avvengono effettivamente le cure). Kubernetes ha la stessa divisione:
> il Control Plane (la direzione) e i Worker Node (i reparti).

```
CONTROL PLANE — "il cervello"
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  kube-apiserver ── il receptionist: tutto passa da lui  │
│       ↕                                                 │
│  etcd ─────────── il registro: ogni decisione salvata   │
│       ↕                                                 │
│  kube-scheduler ─ l'assegnatore: "questo pod → nodo 3" │
│       ↕                                                 │
│  controller-mgr ─ il supervisore: "mancano 2 repliche" │
└─────────────────────────────────────────────────────────┘
           ↕ (HTTPS :6443)
WORKER NODE — "il braccio operativo"
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  kubelet ──────── "ricevuto ordine: avvia container A"  │
│       ↕                                                 │
│  containerd ───── il runtime: esegue il container       │
│       ↕                                                 │
│  kube-proxy ───── il postino: smista il traffico di rete│
└─────────────────────────────────────────────────────────┘

NOTA K3s: In K3s singolo nodo, Control Plane e Worker Node girano
          sullo stesso server fisico. Ottimo per lab, non per produzione.
```

```bash
# Esploriamo i componenti del cluster
kubectl get nodes -o wide
# Vediamo: nome nodo, status, ruoli, versione K8s, IP

kubectl get pods -n kube-system
# Vediamo tutti i componenti di sistema: coredns, traefik, metrics-server, ecc.

# Dettagli di un nodo
kubectl describe node $(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')
# Vediamo: risorse allocate, condizioni (MemoryPressure, DiskPressure, Ready)
```

---

### Concetto A3: I Namespace — Ambienti Virtuali nel Cluster

> **Analogia.** In un edificio per uffici, ogni azienda affittaria ha il suo piano: le risorse
> (sale riunioni, parcheggi) sono del palazzo, ma ogni azienda ha il suo spazio separato.
> I namespace in Kubernetes funzionano così: lo stesso cluster fisico ospita più ambienti
> logicamente separati (dev, staging, production, team-backend, team-frontend).

```
CLUSTER K8s
├── kube-system      ← componenti interni (non toccare!)
├── kube-public      ← dati pubblici del cluster
├── default          ← namespace predefinito (evitare in produzione)
├── production       ← app di produzione
├── staging          ← app di staging
├── monitoring       ← Prometheus, Grafana
└── argocd           ← GitOps controller

ISOLAMENTO nei namespace:
  - Pod nel namespace A non possono comunicare con B (con NetworkPolicy)
  - RBAC per namespace: il team-frontend vede solo il proprio namespace
  - ResourceQuota per namespace: limiti di CPU/RAM per team
```

```bash
# Creiamo i namespace per il lab
kubectl create namespace lab-app
kubectl create namespace lab-db
kubectl create namespace monitoring

# Vediamo tutti i namespace
kubectl get namespaces

# Lavorare in un namespace specifico
kubectl get pods -n lab-app
kubectl get all -n lab-app
```

---

## PART B: OGGETTI FONDAMENTALI — Pod, Deployment e Service

### Esercizio B1: Il Pod — L'Unità Base

Il Pod è la più piccola unità deployabile in Kubernetes. Contiene uno o più container che condividono la stessa rete (stesso IP) e lo stesso storage.

```bash
# Creiamo un file per il nostro primo Pod
cat > /tmp/pod-demo.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: pod-demo
  namespace: lab-app
  labels:
    app: demo
    versione: "1.0"
spec:
  containers:
  - name: app
    image: nginx:1.27-alpine
    ports:
    - containerPort: 80
    resources:
      requests:
        memory: "64Mi"
        cpu: "100m"
      limits:
        memory: "128Mi"
        cpu: "200m"
    readinessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 10
    livenessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 15
      periodSeconds: 20
EOF

# Applichiamo il manifesto
kubectl apply -f /tmp/pod-demo.yaml

# Monitorare il ciclo di vita del Pod
kubectl get pods -n lab-app -w
# OUTPUT ATTESO:
# NAME       READY   STATUS    RESTARTS   AGE
# pod-demo   0/1     Pending   0          0s
# pod-demo   0/1     ContainerCreating   0   1s
# pod-demo   1/1     Running   0          5s

# Dettagli completi del pod
kubectl describe pod pod-demo -n lab-app

# Log del container
kubectl logs pod-demo -n lab-app

# Entrare nel container (per debug)
kubectl exec -it pod-demo -n lab-app -- sh
# Dentro il container:
# / # wget -qO- localhost
# / # exit

# IMPORTANTE: i Pod sono EFFIMERI
# Se viene cancellato, non torna. Usare Deployment per produzione.
kubectl delete pod pod-demo -n lab-app
kubectl get pods -n lab-app
# Il pod è sparito. Un Deployment lo avrebbe ricreato.
```

---

### Esercizio B2: Il Deployment — Gestione Dichiarativa dei Pod

Il Deployment è il modo corretto per gestire applicazioni stateless. Mantiene sempre il numero desiderato di repliche, gestisce i rolling update e permette il rollback.

```bash
cat > /tmp/deployment-demo.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-demo
  namespace: lab-app
  labels:
    app: app-demo
spec:
  replicas: 3
  selector:
    matchLabels:
      app: app-demo
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1           # massimo 1 pod in più durante l'update
      maxUnavailable: 0     # zero downtime durante l'update
  template:
    metadata:
      labels:
        app: app-demo
        version: "1.0"
    spec:
      containers:
      - name: app
        image: nginx:1.27-alpine
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "200m"
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 10
EOF

kubectl apply -f /tmp/deployment-demo.yaml

# Monitorare il deployment
kubectl rollout status deployment/app-demo -n lab-app
# OUTPUT: Waiting for deployment "app-demo" rollout to finish...
#         deployment "app-demo" successfully rolled out

kubectl get pods -n lab-app
# OUTPUT: 3 pod in Running

# Simuliamo un crash: eliminiamo un pod
POD=$(kubectl get pods -n lab-app -o jsonpath='{.items[0].metadata.name}')
kubectl delete pod $POD -n lab-app

# Kubernetes ricrea immediatamente il pod
kubectl get pods -n lab-app
# Entro 10 secondi: di nuovo 3 pod Running

# Rolling update: aggiornamento senza downtime
kubectl set image deployment/app-demo app=nginx:1.28-alpine -n lab-app
kubectl rollout status deployment/app-demo -n lab-app
# Kubernetes aggiorna i pod uno alla volta, garantendo zero downtime

# Rollback all'immagine precedente
kubectl rollout undo deployment/app-demo -n lab-app
kubectl rollout history deployment/app-demo -n lab-app
# Mostra la cronologia degli aggiornamenti
```

---

### Esercizio B3: Il Service — Esposizione Stabile delle Applicazioni

I Pod hanno IP effimeri che cambiano ad ogni restart. Il Service fornisce un IP stabile e un DNS name per raggiungere un gruppo di Pod.

```bash
cat > /tmp/service-demo.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: svc-app-demo
  namespace: lab-app
spec:
  selector:
    app: app-demo         # seleziona i pod con questo label
  ports:
  - name: http
    protocol: TCP
    port: 80              # porta del Service (interna al cluster)
    targetPort: 80        # porta del container
  type: ClusterIP         # accessibile solo dentro il cluster
EOF

kubectl apply -f /tmp/service-demo.yaml

# Verificare che il Service veda i Pod
kubectl get endpoints svc-app-demo -n lab-app
# OUTPUT: mostra gli IP dei 3 pod collegati al Service

# Test: dal dentro del cluster (apriamo un pod di debug)
kubectl run debug --image=curlimages/curl:8.10 --rm -it -n lab-app -- \
  curl -s http://svc-app-demo.lab-app.svc.cluster.local
# OUTPUT: risposta HTML di nginx

# Il DNS interno funziona così:
# <nome-service>.<namespace>.svc.cluster.local
# Abbreviazione da stesso namespace: http://svc-app-demo

# Esponiamo verso l'esterno con NodePort (per test locali)
kubectl patch svc svc-app-demo -n lab-app \
  -p '{"spec": {"type": "NodePort"}}'

NODE_PORT=$(kubectl get svc svc-app-demo -n lab-app \
  -o jsonpath='{.spec.ports[0].nodePort}')
NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[0].address}')
echo "Apri: http://${NODE_IP}:${NODE_PORT}"
curl http://${NODE_IP}:${NODE_PORT}
# [OK] Se ricevi la pagina nginx, il lab funziona
```

---

## PART C: CONFIGURAZIONE E PERSISTENZA

### Esercizio C1: ConfigMap e Secret

```bash
# ConfigMap: configurazione non sensibile
cat > /tmp/configmap-demo.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: lab-app
data:
  APP_ENV: "production"
  LOG_LEVEL: "info"
  MAX_CONNECTIONS: "100"
  config.yaml: |
    server:
      port: 8080
      timeout: 30s
    database:
      pool_size: 10
EOF

kubectl apply -f /tmp/configmap-demo.yaml

# Secret: dati sensibili (codificati in base64, NON criptati di default)
kubectl create secret generic db-credentials \
  --from-literal=username=dbuser \
  --from-literal=password='S3cr3tP@ssw0rd!' \
  -n lab-app

# Verificare (password NON mostrata in chiaro)
kubectl get secret db-credentials -n lab-app -o yaml
# I valori sono in base64: echo "U2VjcmV0..." | base64 -d

# Usare ConfigMap e Secret in un Deployment
cat > /tmp/deployment-with-config.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-con-config
  namespace: lab-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: app-con-config
  template:
    metadata:
      labels:
        app: app-con-config
    spec:
      containers:
      - name: app
        image: nginx:1.27-alpine
        env:
        - name: APP_ENV
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: APP_ENV
        - name: DB_USERNAME
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: username
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
        volumeMounts:
        - name: config-volume
          mountPath: /etc/app/
          readOnly: true
      volumes:
      - name: config-volume
        configMap:
          name: app-config
          items:
          - key: config.yaml
            path: config.yaml
EOF

kubectl apply -f /tmp/deployment-with-config.yaml
kubectl exec -n lab-app \
  $(kubectl get pod -n lab-app -l app=app-con-config -o jsonpath='{.items[0].metadata.name}') \
  -- env | grep -E "APP_ENV|DB_"
# OUTPUT:
# APP_ENV=production
# DB_USERNAME=dbuser
# DB_PASSWORD=S3cr3tP@ssw0rd!
```

---

### Esercizio C2: PersistentVolume per PostgreSQL

```bash
cat > /tmp/postgres-statefulset.yaml << 'EOF'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: lab-db
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  storageClassName: local-path   # storage class di K3s

---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: lab-db
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:17-alpine
        env:
        - name: POSTGRES_DB
          value: "labdb"
        - name: POSTGRES_USER
          value: "labuser"
        - name: POSTGRES_PASSWORD
          value: "labpassword123"
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: local-path
      resources:
        requests:
          storage: 1Gi

---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: lab-db
spec:
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
  clusterIP: None   # Headless service per StatefulSet
EOF

kubectl apply -f /tmp/postgres-statefulset.yaml
kubectl wait --for=condition=Ready pod/postgres-0 -n lab-db --timeout=120s

# Test connessione database
kubectl exec -it postgres-0 -n lab-db -- \
  psql -U labuser -d labdb -c "SELECT version();"
# OUTPUT: PostgreSQL 17.x on aarch64/x86_64-...

echo "[OK] PostgreSQL operativo con storage persistente"

# I dati sopravvivono al riavvio del pod:
kubectl delete pod postgres-0 -n lab-db
kubectl wait --for=condition=Ready pod/postgres-0 -n lab-db --timeout=120s
kubectl exec -it postgres-0 -n lab-db -- \
  psql -U labuser -d labdb -c "SELECT version();"
# [OK] I dati sono ancora presenti
```

---

## PART D: SICUREZZA — RBAC, NetworkPolicy e Pod Security Standards

### Esercizio D1: RBAC — Controllo degli Accessi per Ruolo

> **Analogia.** In un'azienda, non tutti i dipendenti possono accedere a tutti i documenti.
> Un developer può leggere il codice sorgente ma non può modificare il database di produzione.
> Un DBA può gestire i database ma non può distribuire codice. Kubernetes RBAC funziona
> esattamente così: ogni ServiceAccount (identità di un'applicazione) ha solo i permessi
> strettamente necessari.

```bash
# Creiamo un ServiceAccount per la nostra app
kubectl create serviceaccount app-reader -n lab-app

# Creiamo un Role che permette solo la lettura dei pod
cat > /tmp/role-pod-reader.yaml << 'EOF'
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: lab-app
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log"]
  verbs: ["get", "list", "watch"]   # solo lettura
  # NON incluso: create, update, delete, patch
EOF

kubectl apply -f /tmp/role-pod-reader.yaml

# Associare il Role al ServiceAccount tramite RoleBinding
kubectl create rolebinding app-reader-binding \
  --role=pod-reader \
  --serviceaccount=lab-app:app-reader \
  -n lab-app

# Verificare i permessi del ServiceAccount
kubectl auth can-i list pods -n lab-app \
  --as=system:serviceaccount:lab-app:app-reader
# OUTPUT: yes

kubectl auth can-i delete pods -n lab-app \
  --as=system:serviceaccount:lab-app:app-reader
# OUTPUT: no

kubectl auth can-i list pods -n lab-db \
  --as=system:serviceaccount:lab-app:app-reader
# OUTPUT: no (non ha accesso ad altri namespace)

echo "[OK] RBAC least-privilege configurato correttamente"
```

---

### Esercizio D2: NetworkPolicy — Isolamento del Traffico

> **Analogia.** Immagina i namespace come uffici in un palazzo. Di default, tutti i pod
> possono comunicare con tutti gli altri (porte aperte ovunque). La NetworkPolicy è come
> installare porte blindate con badge: "solo l'ufficio marketing può accedere alla sala server",
> "la stampante è accessibile solo dal piano 3". Il default-DENY è la postura di sicurezza
> corretta: blocco tutto, poi esplicito solo ciò che è necessario.

```bash
# STEP 1: verificare che ora la comunicazione è aperta
kubectl run test-sender --image=curlimages/curl:8.10 --rm -it -n lab-app -- \
  curl -s http://svc-app-demo.lab-app.svc.cluster.local -m 5
# [WARN] Risposta ricevuta — traffico aperto a tutti

# STEP 2: Applicare default-DENY (blocca tutto il traffico in entrata)
cat > /tmp/networkpolicy-default-deny.yaml << 'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: lab-app
spec:
  podSelector: {}     # si applica a TUTTI i pod del namespace
  policyTypes:
  - Ingress           # blocca tutto il traffico in entrata
  # NON definire regole ingress = nega tutto
EOF

kubectl apply -f /tmp/networkpolicy-default-deny.yaml

# STEP 3: Verificare che il traffico sia bloccato
kubectl run test-blocked --image=curlimages/curl:8.10 --rm -it -n lab-app -- \
  curl -s http://svc-app-demo.lab-app.svc.cluster.local -m 5
# [OK] Timeout — traffico bloccato

# STEP 4: Permettere il traffico solo dal frontend al backend
cat > /tmp/networkpolicy-allow-frontend.yaml << 'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-app
  namespace: lab-app
spec:
  podSelector:
    matchLabels:
      app: app-demo       # questa policy protegge i pod "app-demo"
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          role: frontend  # solo i pod con questo label possono entrare
    ports:
    - protocol: TCP
      port: 80
EOF

kubectl apply -f /tmp/networkpolicy-allow-frontend.yaml

# Test: pod con il label giusto
kubectl run frontend-allowed --image=curlimages/curl:8.10 \
  --labels="role=frontend" --rm -it -n lab-app -- \
  curl -s http://svc-app-demo.lab-app.svc.cluster.local -m 5
# [OK] Risposta ricevuta

# Test: pod senza il label
kubectl run other-pod --image=curlimages/curl:8.10 --rm -it -n lab-app -- \
  curl -s http://svc-app-demo.lab-app.svc.cluster.local -m 5
# [OK] Timeout — bloccato correttamente
```

---

### Esercizio D3: Pod Security Standards — Restricted

```bash
# Pod Security Standards (PSS) sostituisce PodSecurityPolicy (rimossa in K8s 1.25)
# Livelli: privileged, baseline, restricted
# "restricted" = massima sicurezza: no root, no privilege escalation, seccomp obbligatorio

# Abilitare PSS Restricted per il namespace lab-app
kubectl label namespace lab-app \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/enforce-version=latest \
  pod-security.kubernetes.io/warn=restricted \
  pod-security.kubernetes.io/audit=restricted

# Proviamo a deployare un pod NON conforme (root, senza seccomp)
cat > /tmp/pod-insecure.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: pod-insecure
  namespace: lab-app
spec:
  containers:
  - name: app
    image: nginx:1.27
    securityContext:
      runAsRoot: true       # VIETATO in restricted
EOF

kubectl apply -f /tmp/pod-insecure.yaml
# OUTPUT ATTESO:
# Error from server (Forbidden): error when creating "...":
# pods "pod-insecure" is forbidden: violates PodSecurity "restricted:latest"

# Deploiamo un pod CONFORME con restricted
cat > /tmp/pod-secure.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: pod-secure
  namespace: lab-app
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    seccompProfile:
      type: RuntimeDefault   # profilo seccomp predefinito del runtime
  containers:
  - name: app
    image: nginxinc/nginx-unprivileged:1.27-alpine
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL               # rimuove tutte le Linux capabilities
    ports:
    - containerPort: 8080   # porta > 1024 (no root richiesto)
    volumeMounts:
    - name: tmp
      mountPath: /tmp
    - name: cache
      mountPath: /var/cache/nginx
    - name: run
      mountPath: /var/run
  volumes:
  - name: tmp
    emptyDir: {}
  - name: cache
    emptyDir: {}
  - name: run
    emptyDir: {}
EOF

kubectl apply -f /tmp/pod-secure.yaml
kubectl get pod pod-secure -n lab-app
# OUTPUT: pod-secure   1/1   Running   — conforme a PSS Restricted

echo "[OK] Pod Security Standards Restricted applicato"
```

---

## PART E: WORKLOAD AVANZATI — HPA e DaemonSet

### Esercizio E1: Horizontal Pod Autoscaler — Scaling Automatico

> **Analogia.** Un call center che gestisce il traffico stagionale: in estate ricevono
> 3x più chiamate. Un sistema manuale richiederebbe qualcuno che osserva i grafici
> e ordina "assumete altri 10 operatori". HPA fa questo automaticamente: monitora
> il carico (CPU, memoria, metriche custom) e scala il numero di repliche.

```bash
# Prerequisito: metrics-server (già incluso in K3s)
kubectl top nodes
kubectl top pods -n lab-app
# Se funziona, metrics-server è operativo

# Creiamo un'app con HPA
cat > /tmp/hpa-demo.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hpa-app
  namespace: lab-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: hpa-app
  template:
    metadata:
      labels:
        app: hpa-app
    spec:
      containers:
      - name: app
        image: php:8.3-apache
        resources:
          requests:
            cpu: "200m"       # OBBLIGATORIO per HPA su CPU
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "256Mi"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: hpa-app
  namespace: lab-app
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: hpa-app
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50    # scala se CPU media > 50%
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 30   # attendi 30s prima di scalare su
    scaleDown:
      stabilizationWindowSeconds: 300  # attendi 5 minuti prima di scalare giù
EOF

kubectl apply -f /tmp/hpa-demo.yaml
kubectl get hpa -n lab-app
# OUTPUT: hpa-app   Deployment/hpa-app   <unknown>/50%   1         10        1

# Generare carico artificiale per testare HPA
kubectl run load-generator --image=busybox:1.37 \
  -n lab-app --rm -it -- \
  sh -c "while true; do wget -q -O- http://hpa-app.lab-app.svc.cluster.local; done"

# In un altro terminale, osservare HPA
watch kubectl get hpa -n lab-app
# Entro 1-2 minuti: la CPU sale, HPA aumenta le repliche

# Quando interrompiamo il carico (Ctrl+C):
# Dopo 5 minuti (stabilizationWindow), le repliche tornano a 1
```

---

### Esercizio E2: DaemonSet — Un Pod su Ogni Nodo

```bash
# DaemonSet: garantisce che ogni nodo esegua una copia del pod
# Uso tipico: raccolta log, monitoring agent, network plugin

cat > /tmp/daemonset-nodeinfo.yaml << 'EOF'
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-monitor
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: node-monitor
  template:
    metadata:
      labels:
        app: node-monitor
    spec:
      tolerations:
      - key: node-role.kubernetes.io/control-plane
        effect: NoSchedule
        operator: Exists      # tollera anche i nodi control-plane
      containers:
      - name: monitor
        image: busybox:1.37
        command: ["/bin/sh", "-c"]
        args:
        - "while true; do echo \"[$(hostname)] $(date): CPU=$(cat /proc/loadavg)\"; sleep 30; done"
        volumeMounts:
        - name: proc
          mountPath: /proc
          readOnly: true
        resources:
          requests:
            cpu: "10m"
            memory: "32Mi"
          limits:
            cpu: "50m"
            memory: "64Mi"
      volumes:
      - name: proc
        hostPath:
          path: /proc
EOF

kubectl apply -f /tmp/daemonset-nodeinfo.yaml
kubectl get daemonset node-monitor -n kube-system
# OUTPUT: DESIRED=1, CURRENT=1, READY=1 (1 pod per nodo)

kubectl logs -l app=node-monitor -n kube-system
# OUTPUT: [lab-machine] Wed Jul 16 10:23:45 UTC 2026: CPU=0.42 0.38 0.35...
```

---

## PART F: HELM 4 E GITOPS CON ARGOCD

### Esercizio F1: Helm 4 — Package Manager per Kubernetes

> **Analogia.** `apt install nginx` in Ubuntu non installa solo il binario nginx: gestisce
> le dipendenze, crea gli utenti di sistema, configura systemd, mette i file nelle posizioni
> corrette. Helm fa la stessa cosa per Kubernetes: installa un'applicazione completa con
> tutti i manifest, le configurazioni, i secret, i service account — in un'operazione sola.

```bash
# Helm 4 è compatibile con Helm 3 per l'API, ma ha novità importanti:
# - Plugin system WASM
# - Server-Side Apply nativo
# - Wait migliorato

# Aggiungiamo repository chart
helm repo add stable https://charts.helm.sh/stable
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Cercare chart disponibili
helm search repo nginx
helm search repo prometheus

# Installare Prometheus (esempio reale)
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.enabled=true \
  --set prometheus.prometheusSpec.retention=7d

kubectl get pods -n monitoring
# OUTPUT: 10+ pod in Running (prometheus, grafana, alertmanager, exporters)

# Verificare la release
helm list -n monitoring
# OUTPUT: prometheus   monitoring   1   DEPLOYED   kube-prometheus-stack-x.x.x

# Aggiornare una release
helm upgrade prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --reuse-values \
  --set grafana.adminPassword=NuovaPassword!

# Rollback in caso di problemi
helm rollback prometheus 1 -n monitoring

# Disinstallare
# helm uninstall prometheus -n monitoring
```

---

### Esercizio F2: ArgoCD 3.x — GitOps Controller

```bash
# Installare ArgoCD 3.x
kubectl create namespace argocd
kubectl apply -n argocd \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Attendere che tutti i pod siano pronti
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/name=argocd-server \
  -n argocd --timeout=300s

# Recuperare la password admin generata automaticamente
ARGOCD_PASS=$(kubectl get secret argocd-initial-admin-secret \
  -n argocd -o jsonpath='{.data.password}' | base64 -d)
echo "Password ArgoCD: $ARGOCD_PASS"

# Port-forward per accedere alla UI
kubectl port-forward svc/argocd-server -n argocd 8080:443 &
echo "Apri: https://localhost:8080"
echo "User: admin  Password: $ARGOCD_PASS"

# Creare una Application ArgoCD da manifesto
cat > /tmp/argocd-app.yaml << 'EOF'
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: app-demo-gitops
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/argoproj/argocd-example-apps.git
    targetRevision: HEAD
    path: guestbook            # cartella con i manifest Kubernetes
  destination:
    server: https://kubernetes.default.svc
    namespace: lab-gitops
  syncPolicy:
    automated:
      prune: true              # elimina risorse rimosse dal git
      selfHeal: true           # ripristina se qualcuno modifica manualmente
    syncOptions:
    - CreateNamespace=true
EOF

kubectl apply -f /tmp/argocd-app.yaml

# Verificare lo stato
kubectl get application -n argocd
# OUTPUT: app-demo-gitops   Synced   Healthy

# ArgoCD monitora il repository Git e sincronizza automaticamente
# Se qualcuno modifica un manifest direttamente su K8s → ArgoCD ripristina
# Se aggiungiamo un file nel repo → ArgoCD lo deploya automaticamente
```

---

## PART G: TROUBLESHOOTING — Debug dei Problemi Comuni

### Esercizio G1: Debug CrashLoopBackOff

```bash
# CrashLoopBackOff: il pod si avvia, crasha, K8s lo riavvia, crasha ancora...
# Causa tipica: errore di configurazione, comando sbagliato, dipendenza non disponibile

# Creiamo un pod che crasha intenzionalmente
cat > /tmp/pod-crash.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: pod-crash
  namespace: lab-app
spec:
  containers:
  - name: app
    image: nginx:1.27-alpine
    command: ["/bin/sh", "-c", "echo 'Avvio app...' && sleep 5 && exit 1"]
EOF

kubectl apply -f /tmp/pod-crash.yaml

# Osservare il pattern CrashLoopBackOff
kubectl get pods -n lab-app -w
# OUTPUT:
# pod-crash   0/1   Running             0   5s
# pod-crash   0/1   Error               0   5s
# pod-crash   0/1   CrashLoopBackOff    1   10s
# pod-crash   0/1   Running             1   30s  (riavvio con backoff esponenziale)

# PROCEDURA DI DIAGNOSTICA:
# Step 1: leggi i log dell'ultimo crash
kubectl logs pod-crash -n lab-app --previous
# OUTPUT: Avvio app...

# Step 2: descrivi il pod per vedere gli eventi
kubectl describe pod pod-crash -n lab-app
# Cerca: "Exit Code: 1", "Restart Count: 3", "Back-off X seconds..."

# Step 3: verifica quante volte si è riavviato
kubectl get pod pod-crash -n lab-app \
  -o jsonpath='{.status.containerStatuses[0].restartCount}'
# OUTPUT: 3 (o più)

# SCHEMA DIAGNOSTICO:
echo "
CrashLoopBackOff — Checklist:
  1. kubectl logs <pod> --previous     → cosa ha scritto prima di morire?
  2. kubectl describe pod <pod>        → exit code, eventi, probe failures
  3. Exit code 1 = errore applicativo (controlla i log)
  4. Exit code 137 = OOMKilled (aumentare limits.memory)
  5. Exit code 126/127 = comando non trovato (controlla image e command)
  6. Probe failure = readiness/liveness troppo aggressiva (aumentare delays)
"

kubectl delete pod pod-crash -n lab-app
```

---

### Esercizio G2: Debug Pod Pending

```bash
# Pod Pending: K8s non riesce a schedulare il pod su nessun nodo
# Cause tipiche: risorse insufficienti, nessun nodo con i label richiesti,
#                PVC non disponibile, taint sui nodi

# Creiamo un pod che richiede più risorse di quelle disponibili
cat > /tmp/pod-pending.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: pod-pending
  namespace: lab-app
spec:
  containers:
  - name: app
    image: nginx:1.27-alpine
    resources:
      requests:
        memory: "50Gi"    # IMPOSSIBILE: lab ha 4-8GB di RAM
        cpu: "50"         # IMPOSSIBILE: lab ha 2-4 CPU core
EOF

kubectl apply -f /tmp/pod-pending.yaml

# Verificare lo stato
kubectl get pods -n lab-app
# OUTPUT: pod-pending   0/1   Pending   0   30s

# DIAGNOSTICA:
kubectl describe pod pod-pending -n lab-app
# Cercare nella sezione "Events":
# Warning  FailedScheduling  "0/1 nodes are available:
#   1 Insufficient memory, 1 Insufficient cpu.
#   preemption: 0/1 nodes are available:
#   1 No preemption victims found for incoming pod."

# Vedere le risorse disponibili sui nodi
kubectl describe nodes | grep -A 10 "Allocated resources"
# Mostra: CPU requests/limits usati vs disponibili

# SCHEMA DIAGNOSTICO:
echo "
Pod Pending — Checklist:
  1. kubectl describe pod <pod> → Events section
  2. 'Insufficient memory/cpu'  → ridurre requests o aggiungere nodi
  3. 'didn't match node selector' → verificare nodeSelector labels
  4. 'had untolerated taint'    → aggiungere toleration al pod
  5. 'no PVC bound'             → verificare PVC e StorageClass
  6. kubectl top nodes          → vedere risorse reali disponibili
"

kubectl delete pod pod-pending -n lab-app
```

---

### Esercizio G3: Debug OOMKilled — Out of Memory

```bash
# OOMKilled: il Linux kernel ha killato il container per mancanza di memoria

cat > /tmp/pod-oom.yaml << 'EOF'
apiVersion: v1
kind: Pod
metadata:
  name: pod-oom
  namespace: lab-app
spec:
  containers:
  - name: memory-eater
    image: polinux/stress:latest
    command: ["stress"]
    args: ["--vm", "1", "--vm-bytes", "200M", "--vm-hang", "0"]
    resources:
      requests:
        memory: "50Mi"
      limits:
        memory: "100Mi"    # limite 100MB, ma il processo vuole 200MB
EOF

kubectl apply -f /tmp/pod-oom.yaml

# Attendere il crash
kubectl get pods -n lab-app -w
# OUTPUT: pod-oom   0/1   OOMKilled   0   5s
#         pod-oom   0/1   CrashLoopBackOff   1   10s

kubectl describe pod pod-oom -n lab-app | grep -A5 "Last State"
# OUTPUT: Last State: Terminated
#           Reason: OOMKilled
#           Exit Code: 137

echo "
OOMKilled — Soluzione:
  1. Aumentare limits.memory nel manifest
  2. Profilare l'uso di memoria dell'applicazione con: kubectl top pod
  3. Verificare memory leak nell'applicazione
  4. Exit code 137 = SIGKILL da OOM killer del kernel
"

kubectl delete pod pod-oom -n lab-app
```

---

## PART H: AGGIORNAMENTO DEL CLUSTER — K3s Upgrade

```bash
# K3s supporta upgrade in-place con il system-upgrade-controller
# Aggiornamento K3s v1.35.x → versione successiva

# STEP 1: Verificare la versione corrente
kubectl get nodes -o wide
k3s --version

# STEP 2: Backup etcd prima dell'upgrade
sudo k3s etcd-snapshot save --name pre-upgrade-$(date +%Y%m%d)
ls /var/lib/rancher/k3s/server/db/snapshots/

# STEP 3: Installare il system-upgrade-controller
kubectl apply -f https://github.com/rancher/system-upgrade-controller/releases/latest/download/system-upgrade-controller.yaml

# STEP 4: Definire il piano di upgrade
cat > /tmp/k3s-upgrade-plan.yaml << 'EOF'
apiVersion: upgrade.cattle.io/v1
kind: Plan
metadata:
  name: k3s-server
  namespace: system-upgrade
spec:
  concurrency: 1
  cordon: true
  nodeSelector:
    matchExpressions:
    - key: node-role.kubernetes.io/control-plane
      operator: In
      values: ["true"]
  serviceAccountName: system-upgrade
  upgrade:
    image: rancher/k3s-upgrade
  channel: https://update.k3s.io/v1-release/channels/stable
EOF

kubectl apply -f /tmp/k3s-upgrade-plan.yaml
kubectl get plan -n system-upgrade
# Il controller scarica la nuova versione e aggiorna il nodo in modo controllato

# STEP 5: Monitorare l'upgrade
kubectl get jobs -n system-upgrade -w
kubectl get nodes
# Entro 5-10 minuti: nodo aggiornato alla versione stabile più recente
```

---

## PART I: METRICHE E MONITORING BASE

```bash
# K3s include già metrics-server
# Per monitoring completo, usiamo il kube-prometheus-stack già installato in PART F

# Metriche real-time dei pod
kubectl top pods -n lab-app
# OUTPUT:
# NAME         CPU(cores)   MEMORY(bytes)
# app-demo-*   2m           12Mi
# hpa-app-*    10m          64Mi
# postgres-0   50m          128Mi

# Metriche dei nodi
kubectl top nodes
# OUTPUT:
# NAME          CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
# lab-machine   250m         12%    1200Mi          30%

# Dashboard Grafana (se installato con Helm)
kubectl port-forward svc/prometheus-grafana -n monitoring 3000:80 &
echo "Grafana: http://localhost:3000  (admin/NuovaPassword!)"

# Dashboard utili in Grafana:
# ID 6417: Kubernetes Cluster
# ID 15757: Kubernetes Views - Global
# ID 8588: Kubernetes Deployment Statefulset Daemonset metrics
```

---

## Conclusioni e Prossimi Passi

Hai completato il lab pratico di Kubernetes. Ecco cosa hai appreso:

```
CONCETTI FONDAMENTALI:
  ✓ Stato desiderato vs stato attuale (reconciliation loop)
  ✓ Control Plane (API server, etcd, scheduler, controller) e Worker Node
  ✓ Namespace come confini logici tra ambienti

OGGETTI BASE:
  ✓ Pod, Deployment, Service, ConfigMap, Secret
  ✓ PersistentVolume + StatefulSet per dati persistenti
  ✓ DaemonSet per agenti su ogni nodo

SICUREZZA:
  ✓ RBAC least-privilege con ServiceAccount, Role, RoleBinding
  ✓ NetworkPolicy default-DENY + eccezioni esplicite
  ✓ Pod Security Standards Restricted (no root, no privilege escalation)

AUTOMAZIONE:
  ✓ HPA: scaling automatico in base a CPU/memoria
  ✓ Helm 4: installazione di applicazioni complete
  ✓ ArgoCD 3.x: GitOps — git è la fonte di verità

TROUBLESHOOTING:
  ✓ CrashLoopBackOff → kubectl logs --previous
  ✓ Pending → kubectl describe pod (Events section)
  ✓ OOMKilled → exit code 137, aumentare limits.memory

COMANDI ESSENZIALI:
  kubectl get/describe/logs/exec/apply/delete
  kubectl rollout status/undo/history
  kubectl auth can-i (verifica permessi RBAC)
  kubectl top (metriche risorse)
  helm install/upgrade/rollback/list
```

**Prossimi tutorial consigliati:**
- `tutorial_plat06_docker_avanzato_lab.md` — Dockerfile multi-stage, BuildKit, supply chain
- `tutorial_plat07_cicd_lab.md` — CI/CD con GitHub Actions + ArgoCD
- `tutorial_plat08_monitoring_observability_lab.md` — Prometheus + Grafana + Loki
- `tutorial_plat09_service_mesh_lab.md` — Istio mTLS e traffic management

```bash
# Pulizia del lab (opzionale)
kubectl delete namespace lab-app lab-db
# K3s rimane installato per i prossimi tutorial

echo "[OK] Lab Kubernetes completato con successo"
```

---

> **Nota versioni:** Tutorial validato con K3s v1.35.x (Kubernetes 1.35 "Timbernetes",
> dicembre 2025), Helm 4.0.x, ArgoCD 3.2.x. Breaking change da tenere in mente:
> Kubernetes 1.35 richiede cgroup v2 obbligatorio (cgroup v1 rimosso);
> verificare compatibilità del kernel host con `stat -fc %T /sys/fs/cgroup`.
