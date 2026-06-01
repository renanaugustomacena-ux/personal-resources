---
corso: "Gestione Piattaforme e DevOps"
fase: "3 — Containerizzazione e Orchestrazione"
modulo: 5
titolo: "Kubernetes (K8s) - Guida Completa"
versione: "Kubernetes 1.30+"
livello: "Avanzato"
prerequisiti: ["06-docker-avanzato", "04-infrastructure-as-code", "08-monitoring-observability"]
obiettivi:
  - "Comprendere l'architettura del control plane e dei worker node Kubernetes"
  - "Gestire workload con Deployment, StatefulSet, DaemonSet e Job/CronJob"
  - "Configurare networking con Service, Ingress, NetworkPolicy e service mesh"
  - "Implementare sicurezza con RBAC, Pod Security Standards, OPA/Kyverno e image scanning"
  - "Operare cluster in produzione: upgrade, backup, monitoring e disaster recovery"
tag: [kubernetes, k8s, pod, deployment, rbac, networkpolicy, helm, operator, ingress]
---

# Kubernetes (K8s) - Guida Completa

> **Modulo 05** · **Versioni:** Kubernetes 1.30+ · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Comprendere l'architettura del control plane e dei worker node Kubernetes
> 2. Gestire workload con Deployment, StatefulSet, DaemonSet e Job/CronJob
> 3. Configurare networking con Service, Ingress, NetworkPolicy e service mesh
> 4. Implementare sicurezza con RBAC, Pod Security Standards, OPA/Kyverno e image scanning
> 5. Operare cluster in produzione: upgrade, backup, monitoring e disaster recovery
>
> **Prerequisiti:** [Docker Avanzato](06-docker-avanzato.md) · [IaC](04-infrastructure-as-code.md) · [Monitoring](08-monitoring-observability.md)
> **Tempo stimato:** 90 min · **Livello:** Avanzato

## Idee guida

1. **Pod Security Standards Restricted = default per produzione.** Block privilege escalation.
2. **NetworkPolicy default-DENY.** Esplicita ogni ingress + egress.
3. **RBAC least-privilege.** ServiceAccount per workload, no `cluster-admin`.
4. **OPA/Kyverno > manual review.** Policy as code per admission control.
5. **`extensions/v1beta1` deprecated da anni.** Replaced da `apps/v1`, `networking.k8s.io/v1`.


## Indice

1. [Panoramica e Architettura](#panoramica-e-architettura)
2. [Installazione e Setup](#installazione-e-setup)
3. [Oggetti Fondamentali](#oggetti-fondamentali)
4. [Configurazione: ConfigMap e Secret](#configurazione-configmap-e-secret)
5. [Storage](#storage)
6. [Workload Avanzati](#workload-avanzati)
7. [Networking](#networking)
8. [Helm - Package Manager](#helm---package-manager)
9. [RBAC - Controllo degli Accessi](#rbac---controllo-degli-accessi)
10. [Monitoring](#monitoring)
11. [Logging](#logging)
12. [Troubleshooting](#troubleshooting)
13. [Managed Kubernetes](#managed-kubernetes)
14. [Sicurezza Avanzata](#sicurezza-avanzata)
15. [Observability Avanzata](#observability-avanzata)
16. [Autoscaling Avanzato](#autoscaling-avanzato)
17. [GitOps: ArgoCD e Flux](#gitops-argocd-e-flux)
18. [Gestione Multi-Cluster](#gestione-multi-cluster)
19. [Ottimizzazione dei Costi](#ottimizzazione-dei-costi)
20. [Service Mesh](#service-mesh)
21. [Pattern di Troubleshooting Avanzati](#pattern-di-troubleshooting-avanzati)
22. [Best Practices](#best-practices)

---

## Panoramica e Architettura

Kubernetes, spesso abbreviato in K8s, e' un sistema open-source per l'orchestrazione di container sviluppato originariamente da Google e successivamente donato alla Cloud Native Computing Foundation (CNCF). Il suo scopo principale e' automatizzare il deployment, lo scaling e la gestione di applicazioni containerizzate su cluster di macchine.

### Perche' Kubernetes

In un ambiente moderno di sviluppo software, le applicazioni vengono distribuite come microservizi all'interno di container. Gestire manualmente centinaia o migliaia di container diventa rapidamente insostenibile. Kubernetes risolve questo problema fornendo:

- **Orchestrazione automatica**: posizionamento intelligente dei container sui nodi disponibili
- **Self-healing**: riavvio automatico dei container falliti, sostituzione e rescheduling
- **Scaling orizzontale**: aumento o riduzione delle repliche in base al carico
- **Service discovery e load balancing**: esposizione automatica dei servizi con bilanciamento del traffico
- **Rollout e rollback**: aggiornamenti graduali con possibilita' di tornare alla versione precedente
- **Gestione della configurazione**: separazione tra configurazione e codice applicativo

### Architettura del Cluster

Un cluster Kubernetes e' composto da due tipologie principali di nodi: il **Control Plane** (piano di controllo) e i **Worker Node** (nodi di lavoro).

#### Control Plane

Il Control Plane e' il cervello del cluster. E' responsabile delle decisioni globali riguardanti lo stato desiderato del sistema e della risposta agli eventi del cluster. I suoi componenti principali sono:

**kube-apiserver**

L'API Server e' il punto di ingresso per tutte le operazioni REST che gestiscono il cluster. Ogni comando `kubectl`, ogni richiesta interna tra componenti e ogni interazione con il cluster passa attraverso l'API Server. Espone l'API Kubernetes, valida e processa le richieste, e aggiorna lo stato degli oggetti in etcd. L'API Server supporta l'autenticazione, l'autorizzazione e l'admission control, fungendo da gateway sicuro per l'intero cluster.

**etcd**

etcd e' un database distribuito key-value altamente affidabile che funge da archivio per tutti i dati del cluster. Ogni configurazione, stato dei pod, informazione sui servizi e metadato viene memorizzato in etcd. E' fondamentale per la consistenza del cluster: se etcd si corrompe o si perde, l'intero stato del cluster viene compromesso. Per questo motivo, in ambienti di produzione, etcd viene configurato in modalita' cluster con almeno tre istanze per garantire alta disponibilita' e tolleranza ai guasti. Il backup regolare di etcd e' una delle operazioni piu' critiche nella manutenzione di un cluster.

**kube-scheduler**

Lo Scheduler osserva i pod appena creati che non hanno ancora un nodo assegnato e seleziona il nodo piu' adatto per la loro esecuzione. La decisione di scheduling tiene conto di molteplici fattori: requisiti di risorse del pod (CPU, memoria), vincoli hardware e software, affinita' e anti-affinita', data locality, tolleranze verso i taint dei nodi e bilanciamento del carico complessivo. Lo Scheduler opera in due fasi: filtering (esclusione dei nodi non idonei) e scoring (classificazione dei nodi rimanenti).

**kube-controller-manager**

Il Controller Manager esegue i processi controller, ciascuno dei quali e' responsabile di monitorare lo stato attuale del cluster e di portarlo verso lo stato desiderato. I controller principali includono:

- **Node Controller**: monitora lo stato dei nodi e reagisce quando un nodo diventa irraggiungibile
- **Replication Controller**: mantiene il numero corretto di repliche per ogni ReplicaSet
- **Endpoints Controller**: popola gli oggetti Endpoints (associazione Service-Pod)
- **Service Account e Token Controller**: crea account predefiniti e token di accesso API per i nuovi namespace

**cloud-controller-manager**

Nei cluster gestiti su cloud provider, questo componente collega il cluster alle API specifiche del provider. Gestisce i load balancer cloud, le rotte di rete e il ciclo di vita dei nodi virtuali. Permette a Kubernetes di interfacciarsi in modo trasparente con le risorse del cloud sottostante.

#### Worker Node

I Worker Node sono le macchine (fisiche o virtuali) dove vengono effettivamente eseguiti i container applicativi. Ogni Worker Node esegue i seguenti componenti:

**kubelet**

Il kubelet e' un agente che gira su ogni nodo del cluster. Il suo compito principale e' assicurare che i container descritti nelle specifiche dei pod siano in esecuzione e funzionanti. Il kubelet riceve le specifiche dei pod dall'API Server, comunica con il container runtime per avviare o fermare i container, monitora lo stato di salute attraverso le probe (liveness, readiness, startup) e riporta lo stato del nodo e dei pod all'API Server.

**kube-proxy**

kube-proxy e' un network proxy che gira su ogni nodo e implementa le regole di rete di Kubernetes. Gestisce il routing del traffico di rete verso i pod appropriati basandosi sulle definizioni dei Service. Puo' operare in diverse modalita': iptables (default nella maggior parte delle distribuzioni), IPVS (piu' performante per cluster con molti servizi) o userspace (legacy). kube-proxy permette la comunicazione tra i servizi all'interno del cluster e dall'esterno.

**Container Runtime**

Il container runtime e' il software responsabile dell'esecuzione effettiva dei container. Kubernetes supporta qualsiasi runtime conforme alla Container Runtime Interface (CRI). I runtime piu' comuni sono:

- **containerd**: runtime leggero e performante, il piu' utilizzato negli ambienti di produzione
- **CRI-O**: runtime ottimizzato specificamente per Kubernetes, sviluppato dalla community
- **Docker Engine**: storicamente il runtime piu' diffuso, ora deprecato come runtime diretto in favore di containerd (che Docker stesso utilizza internamente)

---

## Installazione e Setup

Esistono diverse soluzioni per installare Kubernetes, ciascuna adatta a scenari specifici. La scelta dipende dal contesto: sviluppo locale, testing, ambienti di staging o produzione.

### Minikube - Sviluppo Locale

Minikube e' lo strumento ufficiale per eseguire un cluster Kubernetes a singolo nodo sulla propria macchina locale. E' ideale per lo sviluppo e l'apprendimento.

```bash
# Installazione su Linux
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Avvio del cluster con driver Docker
minikube start --driver=docker --cpus=4 --memory=8192

# Verifica dello stato
minikube status

# Abilitazione di addon utili
minikube addons enable ingress
minikube addons enable metrics-server
minikube addons enable dashboard

# Accesso alla dashboard
minikube dashboard

# Arresto del cluster
minikube stop

# Eliminazione completa del cluster
minikube delete
```

Minikube supporta diversi driver di virtualizzazione: Docker, VirtualBox, KVM2, Hyper-V. Il driver Docker e' generalmente il piu' rapido e leggero per ambienti Linux.

### K3s - Kubernetes Leggero

K3s e' una distribuzione Kubernetes leggera certificata, sviluppata da Rancher Labs (ora parte di SUSE). E' particolarmente adatta per ambienti con risorse limitate, edge computing, IoT e ambienti di sviluppo.

```bash
# Installazione del server (control plane + worker)
curl -sfL https://get.k3s.io | sh -

# Verifica dell'installazione
sudo k3s kubectl get nodes

# Copia del kubeconfig per l'uso con kubectl standard
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $(id -u):$(id -g) ~/.kube/config

# Aggiunta di un worker node (eseguire sul nodo worker)
# Il token si trova sul server in /var/lib/rancher/k3s/server/node-token
curl -sfL https://get.k3s.io | K3S_URL=https://server-ip:6443 \
  K3S_TOKEN=token-dal-server sh -

# Disinstallazione
/usr/local/bin/k3s-uninstall.sh
```

K3s utilizza SQLite come database predefinito al posto di etcd (sebbene supporti anche etcd, MySQL e PostgreSQL), ha un binario di circa 100MB e avvia un cluster funzionante in pochi secondi.

### Kind - Kubernetes in Docker

Kind (Kubernetes IN Docker) esegue cluster Kubernetes usando container Docker come nodi. E' particolarmente utile per testing automatizzati e pipeline CI/CD.

```bash
# Installazione
go install sigs.k8s.io/kind@latest
# oppure tramite download diretto del binario
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Creazione cluster semplice
kind create cluster --name mio-cluster

# Creazione cluster multi-nodo con file di configurazione
cat <<EOF > kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
- role: worker
EOF

kind create cluster --name cluster-test --config kind-config.yaml

# Caricamento di un'immagine locale nel cluster Kind
kind load docker-image mia-app:latest --name mio-cluster

# Elenco dei cluster
kind get clusters

# Eliminazione
kind delete cluster --name mio-cluster
```

### Kubeadm - Cluster di Produzione

Kubeadm e' lo strumento ufficiale per creare cluster Kubernetes di produzione. Richiede una preparazione piu' accurata dei nodi.

```bash
# Prerequisiti su tutti i nodi (Ubuntu/Debian)
sudo swapoff -a
sudo sed -i '/ swap / s/^/#/' /etc/fstab

# Caricamento moduli kernel necessari
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF
sudo modprobe overlay
sudo modprobe br_netfilter

# Parametri sysctl
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF
sudo sysctl --system

# Installazione di containerd
sudo apt-get update
sudo apt-get install -y containerd
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
sudo systemctl restart containerd

# Installazione di kubeadm, kubelet, kubectl
sudo apt-get install -y apt-transport-https ca-certificates curl
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.31/deb/Release.key | \
  sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] \
  https://pkgs.k8s.io/core:/stable:/v1.31/deb/ /' | \
  sudo tee /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl

# Inizializzazione del control plane (solo sul master)
sudo kubeadm init --pod-network-cidr=10.244.0.0/16 --control-plane-endpoint=master-ip

# Configurazione kubectl per l'utente corrente
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config

# Installazione del plugin di rete (Calico)
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/calico.yaml

# Aggiunta dei worker node (comando fornito dall'output di kubeadm init)
sudo kubeadm join master-ip:6443 --token <token> \
  --discovery-token-ca-cert-hash sha256:<hash>
```

---

## Oggetti Fondamentali

### Pod

Il Pod e' l'unita' minima di deployment in Kubernetes. Rappresenta uno o piu' container che condividono lo stesso network namespace, lo stesso indirizzo IP e possono condividere volumi di storage. Nella maggior parte dei casi, un Pod contiene un singolo container applicativo.

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-web
  namespace: produzione
  labels:
    app: web-frontend
    versione: "2.1"
    ambiente: produzione
  annotations:
    descrizione: "Pod del frontend web principale"
spec:
  containers:
  - name: app-container
    image: nginx:1.27-alpine
    ports:
    - containerPort: 80
      protocol: TCP
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
      limits:
        cpu: "500m"
        memory: "256Mi"
    livenessProbe:
      httpGet:
        path: /healthz
        port: 80
      initialDelaySeconds: 15
      periodSeconds: 10
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /ready
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 5
    startupProbe:
      httpGet:
        path: /healthz
        port: 80
      failureThreshold: 30
      periodSeconds: 10
    env:
    - name: APP_ENV
      value: "production"
    volumeMounts:
    - name: config-vol
      mountPath: /etc/app/config
      readOnly: true
  volumes:
  - name: config-vol
    configMap:
      name: app-config
  restartPolicy: Always
  terminationGracePeriodSeconds: 30
```

Le **probe** sono fondamentali per la gestione del ciclo di vita:

- **livenessProbe**: verifica se il container e' ancora vivo; se fallisce, il container viene riavviato
- **readinessProbe**: verifica se il container e' pronto a ricevere traffico; se fallisce, il pod viene rimosso dagli endpoint del Service
- **startupProbe**: verifica se l'applicazione e' avviata; utile per applicazioni con tempi di avvio lunghi

### ReplicaSet

Un ReplicaSet garantisce che un numero specificato di repliche identiche di un Pod sia sempre in esecuzione. Se un Pod fallisce, il ReplicaSet ne crea automaticamente uno nuovo per mantenere il numero desiderato.

```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: frontend-rs
  labels:
    app: frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: mia-app-frontend:1.5.0
        ports:
        - containerPort: 3000
        resources:
          requests:
            cpu: "200m"
            memory: "256Mi"
```

In pratica, non si crea quasi mai un ReplicaSet direttamente. Si utilizza un Deployment che gestisce automaticamente i ReplicaSet.

### Deployment

Il Deployment e' l'oggetto piu' utilizzato per gestire applicazioni stateless. Fornisce aggiornamenti dichiarativi per Pod e ReplicaSet, con supporto per strategie di rollout controllate.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-backend
  labels:
    app: api-backend
spec:
  replicas: 4
  revisionHistoryLimit: 10
  selector:
    matchLabels:
      app: api-backend
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: api-backend
        versione: "3.2.1"
    spec:
      containers:
      - name: api
        image: mia-api:3.2.1
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: "250m"
            memory: "512Mi"
          limits:
            cpu: "1000m"
            memory: "1Gi"
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8080
          initialDelaySeconds: 20
          periodSeconds: 15
        readinessProbe:
          httpGet:
            path: /api/ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - api-backend
              topologyKey: kubernetes.io/hostname
```

**Strategie di Deployment:**

- **RollingUpdate** (predefinita): aggiorna i pod gradualmente. `maxSurge` definisce quanti pod in eccesso possono essere creati durante l'aggiornamento, `maxUnavailable` definisce quanti pod possono essere non disponibili. Con `maxSurge: 1` e `maxUnavailable: 0` si garantisce zero downtime.
- **Recreate**: termina tutti i pod esistenti prima di crearne di nuovi. Comporta un periodo di downtime ma evita problemi di compatibilita' tra versioni diverse eseguite contemporaneamente.

```bash
# Operazioni comuni sui Deployment
kubectl rollout status deployment/api-backend
kubectl rollout history deployment/api-backend
kubectl rollout undo deployment/api-backend
kubectl rollout undo deployment/api-backend --to-revision=3
kubectl scale deployment/api-backend --replicas=6
kubectl set image deployment/api-backend api=mia-api:3.3.0
```

### Service

Un Service espone un gruppo di Pod come servizio di rete. Poiche' i Pod sono effimeri (possono essere creati e distrutti in qualsiasi momento), i Service forniscono un endpoint stabile attraverso il quale i client possono raggiungere l'applicazione.

```yaml
# ClusterIP - accessibile solo dall'interno del cluster
apiVersion: v1
kind: Service
metadata:
  name: api-service
spec:
  type: ClusterIP
  selector:
    app: api-backend
  ports:
  - name: http
    port: 80
    targetPort: 8080
    protocol: TCP

---
# NodePort - espone il servizio su una porta statica di ogni nodo
apiVersion: v1
kind: Service
metadata:
  name: web-nodeport
spec:
  type: NodePort
  selector:
    app: web-frontend
  ports:
  - port: 80
    targetPort: 8080
    nodePort: 30080

---
# LoadBalancer - provisiona un load balancer esterno (su cloud provider)
apiVersion: v1
kind: Service
metadata:
  name: web-lb
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
spec:
  type: LoadBalancer
  selector:
    app: web-frontend
  ports:
  - port: 443
    targetPort: 8443

---
# ExternalName - mappa il servizio a un nome DNS esterno
apiVersion: v1
kind: Service
metadata:
  name: database-esterno
spec:
  type: ExternalName
  externalName: db.servizio-esterno.com
```

**Tipi di Service:**

| Tipo | Visibilita' | Caso d'Uso |
|------|-------------|------------|
| ClusterIP | Solo interna al cluster | Comunicazione tra microservizi |
| NodePort | Esterna via porta del nodo (30000-32767) | Sviluppo, accesso diretto ai nodi |
| LoadBalancer | Esterna via load balancer cloud | Servizi esposti in produzione su cloud |
| ExternalName | Alias DNS verso servizio esterno | Integrazione con servizi fuori dal cluster |

### Namespace

I Namespace forniscono un meccanismo di isolamento logico all'interno di un cluster. Permettono di suddividere le risorse tra diversi team, ambienti o progetti.

```bash
# Creazione di un namespace
kubectl create namespace staging

# Elenco dei namespace
kubectl get namespaces

# Impostare il namespace predefinito per il contesto corrente
kubectl config set-context --current --namespace=staging
```

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: produzione
  labels:
    ambiente: produzione
---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: quota-produzione
  namespace: produzione
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    limits.memory: 80Gi
    pods: "100"
    services: "20"
---
apiVersion: v1
kind: LimitRange
metadata:
  name: limiti-default
  namespace: produzione
spec:
  limits:
  - default:
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:
      cpu: "100m"
      memory: "128Mi"
    type: Container
```

---

## Configurazione: ConfigMap e Secret

### ConfigMap

Le ConfigMap permettono di disaccoppiare la configurazione dalle immagini dei container. Possono contenere coppie chiave-valore, file di configurazione completi o anche directory.

```bash
# Creazione da valori letterali
kubectl create configmap app-config \
  --from-literal=DATABASE_HOST=postgres.db.svc.cluster.local \
  --from-literal=DATABASE_PORT=5432 \
  --from-literal=LOG_LEVEL=info

# Creazione da file
kubectl create configmap nginx-config --from-file=nginx.conf
kubectl create configmap app-properties --from-file=config/

# Visualizzazione
kubectl get configmap app-config -o yaml
```

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: produzione
data:
  DATABASE_HOST: "postgres.db.svc.cluster.local"
  DATABASE_PORT: "5432"
  LOG_LEVEL: "info"
  MAX_CONNECTIONS: "100"
  app.properties: |
    server.port=8080
    spring.datasource.url=jdbc:postgresql://postgres:5432/mydb
    spring.jpa.hibernate.ddl-auto=validate
    logging.level.root=INFO
```

### Secret

I Secret sono simili alle ConfigMap ma sono progettati per dati sensibili come password, token e chiavi. I valori sono codificati in base64 (non crittografati per default; per la crittografia a riposo e' necessario configurare encryption at rest su etcd).

```bash
# Creazione di un Secret generico
kubectl create secret generic db-credentials \
  --from-literal=username=admin \
  --from-literal=password='P@ssw0rd!Sicura123'

# Secret per TLS
kubectl create secret tls tls-secret \
  --cert=certificato.crt \
  --key=chiave-privata.key

# Secret per Docker registry
kubectl create secret docker-registry regcred \
  --docker-server=registry.esempio.com \
  --docker-username=utente \
  --docker-password=password \
  --docker-email=utente@esempio.com
```

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
  namespace: produzione
type: Opaque
data:
  username: YWRtaW4=          # echo -n 'admin' | base64
  password: UEBzc3cwcmQh     # echo -n 'P@ssw0rd!' | base64
stringData:                    # alternativa: valori in chiaro, codificati automaticamente
  api-key: "chiave-api-segreta-12345"
```

### Utilizzo nei Pod

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-con-config
spec:
  replicas: 2
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
        image: mia-app:2.0
        # Variabili d'ambiente dalla ConfigMap
        envFrom:
        - configMapRef:
            name: app-config
        # Variabili d'ambiente selettive dal Secret
        env:
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
        # Montaggio come volumi
        volumeMounts:
        - name: config-file
          mountPath: /etc/app/
          readOnly: true
        - name: secret-file
          mountPath: /etc/secrets/
          readOnly: true
      volumes:
      - name: config-file
        configMap:
          name: app-config
          items:
          - key: app.properties
            path: application.properties
      - name: secret-file
        secret:
          secretName: db-credentials
          defaultMode: 0400
```

---

## Storage

### PersistentVolume e PersistentVolumeClaim

Il modello di storage in Kubernetes separa il provisioning dello storage (PersistentVolume) dalla richiesta di storage da parte delle applicazioni (PersistentVolumeClaim).

```yaml
# PersistentVolume - definito dall'amministratore del cluster
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-database
  labels:
    tipo: ssd-locale
spec:
  capacity:
    storage: 50Gi
  volumeMode: Filesystem
  accessModes:
  - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: ssd-veloce
  hostPath:
    path: /mnt/data/database

---
# PersistentVolumeClaim - richiesta dall'applicazione
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-database
  namespace: produzione
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi
  storageClassName: ssd-veloce
  selector:
    matchLabels:
      tipo: ssd-locale
```

**Access Modes:**

| Modalita' | Abbreviazione | Descrizione |
|-----------|---------------|-------------|
| ReadWriteOnce | RWO | Montabile in lettura/scrittura da un singolo nodo |
| ReadOnlyMany | ROX | Montabile in sola lettura da piu' nodi |
| ReadWriteMany | RWX | Montabile in lettura/scrittura da piu' nodi |
| ReadWriteOncePod | RWOP | Montabile in lettura/scrittura da un singolo Pod |

### StorageClass e Dynamic Provisioning

Le StorageClass permettono il provisioning dinamico dei volumi: quando un PVC richiede storage tramite una StorageClass, il volume viene creato automaticamente.

```yaml
# StorageClass per AWS EBS
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3-standard
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Delete
allowVolumeExpansion: true

---
# PVC che utilizza il dynamic provisioning
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-dinamico
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: gp3-standard
  resources:
    requests:
      storage: 20Gi
```

La politica `WaitForFirstConsumer` rimanda il binding del volume fino a quando un Pod non lo richiede effettivamente, permettendo allo scheduler di scegliere il nodo migliore considerando la localita' dello storage.

### CSI Drivers (Container Storage Interface)

La CSI (Container Storage Interface) e' lo standard che permette ai vendor di storage di fornire driver per Kubernetes senza dover modificare il codice core dell'orchestratore. Prima della CSI, i plugin di storage erano compilati direttamente nel binario di Kubernetes (in-tree), creando dipendenze rigide e cicli di rilascio accoppiati. Con la CSI, i driver sono componenti esterni distribuiti come container, aggiornabili indipendentemente dalla versione di Kubernetes.

Un driver CSI e' composto da due componenti principali:

- **Controller Plugin**: gestisce il ciclo di vita dei volumi a livello di cluster. Risponde alle richieste di creazione, eliminazione, attach e detach dei volumi. Viene eseguito come Deployment con una singola replica (o con leader election per alta disponibilita').
- **Node Plugin**: gestisce il mounting dei volumi sui singoli nodi. Viene eseguito come DaemonSet su ogni nodo worker, per garantire che i volumi possano essere montati ovunque un Pod venga schedulato.

**Driver CSI per Cloud Provider:**

```yaml
# Esempio: installazione del driver EBS CSI per AWS
# Il driver sostituisce il provisioner in-tree kubernetes.io/aws-ebs
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ebs-gp3-encrypted
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:eu-west-1:123456789:key/uuid-della-chiave"
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Delete
allowVolumeExpansion: true

---
# Azure Disk CSI
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: azure-premium-zrs
provisioner: disk.csi.azure.com
parameters:
  skuName: PremiumV2_ZRS
  cachingmode: None
  DiskIOPSReadWrite: "5000"
  DiskMBpsReadWrite: "200"
volumeBindingMode: WaitForFirstConsumer
reclaimPolicy: Delete
allowVolumeExpansion: true
```

**Driver CSI per Storage Software-Defined:**

Per ambienti on-premise o ibridi, esistono soluzioni software-defined che forniscono storage distribuito gestito interamente via Kubernetes:

- **Longhorn** (CNCF Incubating): sistema di block storage progettato per Kubernetes che offre ridondanza dei dati, snapshot, backup su S3-compatible e disaster recovery integrati. E' la soluzione piu' semplice da installare e gestire per cluster di piccole-medie dimensioni.
- **Rook-Ceph**: operatore che gestisce cluster Ceph su Kubernetes, fornendo block, filesystem (CephFS) e object storage (S3-compatible). Ideale per cluster di grandi dimensioni che necessitano di storage unificato ad alte prestazioni.
- **OpenEBS**: framework di storage che supporta diverse engine (Mayastor per block storage ad alte prestazioni basato su NVMe-oF, LocalPV per storage locale con scheduling consapevole).

**Volume Snapshot e Cloning:**

A partire da Kubernetes 1.20, i VolumeSnapshot sono GA (Generally Available) e permettono di creare snapshot consistenti dei volumi:

```yaml
# VolumeSnapshotClass
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: csi-snapshot-class
driver: ebs.csi.aws.com
deletionPolicy: Retain

---
# Creazione di uno snapshot
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: snapshot-database-20260524
  namespace: produzione
spec:
  volumeSnapshotClassName: csi-snapshot-class
  source:
    persistentVolumeClaimName: pvc-database

---
# Ripristino da snapshot: creare un nuovo PVC dallo snapshot
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pvc-database-restored
  namespace: produzione
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: ebs-gp3-encrypted
  resources:
    requests:
      storage: 100Gi
  dataSource:
    name: snapshot-database-20260524
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
```

**Best practices per lo storage in produzione:**

- Abilitare sempre la crittografia at-rest per volumi che contengono dati sensibili, utilizzando chiavi gestite (KMS) del cloud provider
- Utilizzare `volumeBindingMode: WaitForFirstConsumer` per garantire la co-locazione tra Pod e volume nella stessa zona di disponibilita'
- Impostare `reclaimPolicy: Retain` per volumi con dati critici, per evitare la cancellazione accidentale
- Abilitare `allowVolumeExpansion: true` per permettere l'espansione dei volumi senza downtime (supportato dalla maggior parte dei driver CSI moderni)
- Implementare snapshot schedulati tramite CronJob o strumenti come Velero per backup regolari dei volumi

---

## Workload Avanzati

### StatefulSet

Gli StatefulSet sono progettati per applicazioni stateful come database, code di messaggi e sistemi di cache distribuiti. A differenza dei Deployment, garantiscono:

- Identita' di rete stabile e persistente (nomi prevedibili come `db-0`, `db-1`, `db-2`)
- Storage persistente dedicato per ogni replica
- Deployment e scaling ordinato (le repliche vengono create e terminate in ordine)

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres-headless
  replicas: 3
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
        image: postgres:16-alpine
        ports:
        - containerPort: 5432
          name: tcp-postgres
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        - name: PGDATA
          value: /var/lib/postgresql/data/pgdata
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2000m"
            memory: "4Gi"
  volumeClaimTemplates:
  - metadata:
      name: postgres-data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: gp3-standard
      resources:
        requests:
          storage: 100Gi

---
# Headless Service necessario per lo StatefulSet
apiVersion: v1
kind: Service
metadata:
  name: postgres-headless
spec:
  clusterIP: None
  selector:
    app: postgres
  ports:
  - port: 5432
    targetPort: 5432
```

### DaemonSet

Un DaemonSet garantisce che una copia di un Pod venga eseguita su ogni nodo del cluster (o su un sottoinsieme selezionato). E' ideale per agenti di monitoring, raccolta log e componenti di rete.

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: node-exporter
  template:
    metadata:
      labels:
        app: node-exporter
    spec:
      hostPID: true
      hostNetwork: true
      containers:
      - name: node-exporter
        image: prom/node-exporter:v1.8.0
        ports:
        - containerPort: 9100
          hostPort: 9100
        resources:
          requests:
            cpu: "50m"
            memory: "64Mi"
          limits:
            cpu: "200m"
            memory: "128Mi"
        volumeMounts:
        - name: proc
          mountPath: /host/proc
          readOnly: true
        - name: sys
          mountPath: /host/sys
          readOnly: true
      tolerations:
      - operator: Exists
      volumes:
      - name: proc
        hostPath:
          path: /proc
      - name: sys
        hostPath:
          path: /sys
```

### Job e CronJob

I Job eseguono task a completamento: uno o piu' Pod che devono terminare con successo. I CronJob sono Job schedulati periodicamente.

```yaml
# Job singolo - migrazione database
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration
spec:
  backoffLimit: 3
  activeDeadlineSeconds: 600
  ttlSecondsAfterFinished: 3600
  template:
    spec:
      containers:
      - name: migrazione
        image: mia-app:3.0-migrate
        command: ["./migrate", "--target", "latest"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: connection-string
      restartPolicy: Never

---
# CronJob - backup giornaliero
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup-database
spec:
  schedule: "0 2 * * *"    # Ogni giorno alle 02:00
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 7
  failedJobsHistoryLimit: 3
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: backup-tool:1.2
            command: ["/bin/sh", "-c"]
            args:
            - |
              pg_dump $DATABASE_URL | gzip > /backup/db-$(date +%Y%m%d).sql.gz
              aws s3 cp /backup/ s3://mio-bucket-backup/ --recursive
            volumeMounts:
            - name: backup-storage
              mountPath: /backup
          volumes:
          - name: backup-storage
            emptyDir:
              sizeLimit: 10Gi
          restartPolicy: OnFailure
```

### Horizontal Pod Autoscaler (HPA)

L'HPA regola automaticamente il numero di repliche di un Deployment, ReplicaSet o StatefulSet in base alle metriche osservate, come l'utilizzo di CPU, memoria o metriche custom.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-backend
  minReplicas: 3
  maxReplicas: 20
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 25
        periodSeconds: 120
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
```

L'HPA richiede che il `metrics-server` sia installato nel cluster per le metriche di base (CPU e memoria). Per metriche custom, e' necessario un adapter come Prometheus Adapter.

### Vertical Pod Autoscaler (VPA)

Il VPA regola automaticamente le richieste di CPU e memoria dei container in base all'utilizzo effettivo. A differenza dell'HPA che scala orizzontalmente (piu' repliche), il VPA scala verticalmente (piu' risorse per pod). Il VPA e' particolarmente utile per workload che non scalano bene orizzontalmente o per ottimizzare i limiti di risorse. Puo' operare in modalita' `Auto` (applica le raccomandazioni riavviando i pod), `Recreate` (simile ad Auto), `Initial` (imposta i valori solo alla creazione) oppure `Off` (fornisce solo raccomandazioni senza applicarle). Si noti che VPA e HPA non dovrebbero essere usati contemporaneamente sulle stesse metriche.

---

## Networking

### Modello di Rete dei Pod

Il networking in Kubernetes si basa su tre principi fondamentali:

1. Ogni Pod riceve un indirizzo IP unico nel cluster
2. Tutti i Pod possono comunicare tra loro senza NAT
3. Gli agenti sul nodo possono comunicare con tutti i Pod sullo stesso nodo

Questa rete piatta e' implementata da plugin CNI (Container Network Interface) come Calico, Cilium, Flannel o Weave Net. Ciascun plugin ha caratteristiche diverse in termini di prestazioni, supporto per NetworkPolicy e funzionalita' avanzate.

### NetworkPolicy

Le NetworkPolicy controllano il traffico di rete a livello di Pod, implementando un firewall a livello di cluster. Senza NetworkPolicy, tutti i Pod possono comunicare liberamente tra loro.

```yaml
# Nega tutto il traffico in ingresso per default nel namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: produzione
spec:
  podSelector: {}
  policyTypes:
  - Ingress

---
# Permetti traffico specifico verso l'API
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: consenti-traffico-api
  namespace: produzione
spec:
  podSelector:
    matchLabels:
      app: api-backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          nome: frontend
    - podSelector:
        matchLabels:
          app: web-frontend
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:   # Consenti DNS
    - namespaceSelector: {}
    ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53
```

### Ingress Controller con Nginx

L'Ingress e' un oggetto che gestisce l'accesso esterno ai servizi nel cluster, tipicamente tramite HTTP e HTTPS. Richiede un Ingress Controller installato nel cluster.

```bash
# Installazione di Nginx Ingress Controller tramite Helm
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace \
  --set controller.replicaCount=2
```

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-principale
  namespace: produzione
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - api.esempio.com
    - www.esempio.com
    secretName: tls-esempio-com
  rules:
  - host: www.esempio.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
  - host: api.esempio.com
    http:
      paths:
      - path: /v1
        pathType: Prefix
        backend:
          service:
            name: api-v1-service
            port:
              number: 80
      - path: /v2
        pathType: Prefix
        backend:
          service:
            name: api-v2-service
            port:
              number: 80
```

Per la gestione automatica dei certificati TLS con Let's Encrypt, si utilizza cert-manager:

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@esempio.com
    privateKeySecretRef:
      name: letsencrypt-prod-key
    solvers:
    - http01:
        ingress:
          class: nginx
```

### CoreDNS

CoreDNS e' il server DNS predefinito in Kubernetes. Fornisce la risoluzione dei nomi per i servizi e i pod all'interno del cluster. Ogni Service ottiene un record DNS nel formato `<nome-servizio>.<namespace>.svc.cluster.local`. Ad esempio, un servizio chiamato `api-service` nel namespace `produzione` e' raggiungibile all'indirizzo `api-service.produzione.svc.cluster.local`. Per i Pod, CoreDNS crea record nel formato `<ip-con-trattini>.<namespace>.pod.cluster.local`. La configurazione di CoreDNS e' gestita tramite una ConfigMap nel namespace `kube-system` ed e' personalizzabile per aggiungere zone DNS personalizzate, forwarding condizionale e plugin aggiuntivi.

### Container Network Interface (CNI) - Approfondimento

La CNI (Container Network Interface) e' lo standard che definisce come i plugin di rete configurano la connettivita' per i container in Kubernetes. Quando un Pod viene creato, il kubelet invoca il plugin CNI configurato per assegnare un indirizzo IP al Pod e configurare le interfacce di rete. La scelta del plugin CNI ha un impatto significativo sulle prestazioni, sulla sicurezza e sulle funzionalita' di rete disponibili nel cluster.

**Calico**

Calico e' uno dei plugin CNI piu' diffusi, che implementa networking L3 basato su BGP (Border Gateway Protocol). Offre un supporto completo per le NetworkPolicy di Kubernetes e aggiunge funzionalita' avanzate come policy a livello di nodo, policy DNS-aware e integrazione con firewall esterni. Calico puo' operare in diverse modalita': overlay con VXLAN o IP-in-IP per ambienti dove il routing diretto non e' possibile, oppure routing nativo BGP per prestazioni ottimali in ambienti che lo supportano. In ambienti cloud managed come EKS o GKE, Calico viene spesso utilizzato esclusivamente per la componente NetworkPolicy sopra il CNI nativo del provider.

**Cilium**

Cilium rappresenta una delle innovazioni piu' significative nel networking Kubernetes degli ultimi anni. Utilizza eBPF (extended Berkeley Packet Filter), una tecnologia del kernel Linux che permette di eseguire programmi nel kernel senza modificarlo. Questo approccio elimina la necessita' di proxy sidecar per molte funzionalita' di rete, offrendo prestazioni superiori con latenza inferiore del 40-60% rispetto alle soluzioni basate su proxy e un consumo di memoria ridotto del 50-70%. Cilium supporta NetworkPolicy native, aggiunge policy L7 (HTTP, gRPC, Kafka), fornisce osservabilita' di rete integrata tramite Hubble e offre funzionalita' di service mesh senza sidecar. A partire dal 2025, Cilium e' il CNI predefinito di GKE e viene adottato in modo crescente su EKS e AKS.

**Flannel**

Flannel e' il plugin CNI piu' semplice e leggero. Implementa una rete overlay utilizzando VXLAN e si concentra esclusivamente sulla connettivita' di base tra i Pod. Non supporta le NetworkPolicy (richiede un plugin aggiuntivo come Calico per questa funzionalita'). Flannel e' ideale per ambienti di sviluppo, cluster di piccole dimensioni o distribuzioni leggere come K3s dove la semplicita' e' prioritaria rispetto alle funzionalita' avanzate.

**Confronto sintetico dei plugin CNI:**

| Plugin | NetworkPolicy | Prestazioni | Funzionalita' Avanzate | Complessita' |
|--------|---------------|-------------|------------------------|--------------|
| Calico | Complete (L3/L4 + L7 con Enterprise) | Ottime con routing BGP | Policy DNS, encryption WireGuard | Media |
| Cilium | Complete (L3/L4/L7) | Eccellenti (eBPF) | Service mesh, Hubble, mTLS | Media-Alta |
| Flannel | Non supportate nativamente | Buone | Nessuna | Bassa |
| Weave Net | Base | Medie | Encryption automatica | Bassa |
| AWS VPC CNI | Dipende da configurazione | Ottime (IP nativi VPC) | Security groups per pod | Bassa (su EKS) |

### Gateway API - Il Futuro del Routing in Kubernetes

La Gateway API e' il successore ufficiale della risorsa Ingress, progettato per superare le limitazioni architetturali di Ingress. Mentre Ingress supporta solo terminazione TLS e routing HTTP basato su contenuto, la Gateway API supporta protocolli L4 e L7 inclusi TCP, UDP, HTTP, gRPC e TLS passthrough. La community Kubernetes ha annunciato il ritiro formale di Ingress-NGINX, con supporto best-effort fino a marzo 2026, dopo il quale non ricevera' piu' patch di sicurezza.

La Gateway API introduce un'architettura orientata ai ruoli che separa le responsabilita' in modo netto:

- **GatewayClass**: definita dall'operatore dell'infrastruttura, specifica il tipo di gateway disponibile (simile a StorageClass per lo storage)
- **Gateway**: definita dall'operatore del cluster, configura dove e come il traffico entra nel cluster (porte, protocolli, certificati TLS)
- **HTTPRoute / GRPCRoute / TCPRoute / TLPRoute**: definite dallo sviluppatore dell'applicazione, specificano come il traffico viene instradato ai Service

Questa separazione elimina il problema dell'annotation sprawl tipico di Ingress, dove funzionalita' avanzate venivano gestite tramite annotazioni non standardizzate e specifiche del controller.

```yaml
# GatewayClass - definisce l'implementazione del gateway
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: envoy-gateway
spec:
  controllerName: gateway.envoyproxy.io/gatewayclass-controller

---
# Gateway - configura il punto di ingresso del traffico
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: gateway-produzione
  namespace: infrastruttura
spec:
  gatewayClassName: envoy-gateway
  listeners:
  - name: https
    protocol: HTTPS
    port: 443
    tls:
      mode: Terminate
      certificateRefs:
      - kind: Secret
        name: tls-certificato-prod
    allowedRoutes:
      namespaces:
        from: Selector
        selector:
          matchLabels:
            gateway-access: "abilitato"
  - name: http-redirect
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: Same

---
# HTTPRoute - definisce le regole di routing
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: api-route
  namespace: produzione
spec:
  parentRefs:
  - name: gateway-produzione
    namespace: infrastruttura
    sectionName: https
  hostnames:
  - "api.esempio.com"
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /v2
    backendRefs:
    - name: api-v2-service
      port: 80
      weight: 90
    - name: api-v3-canary
      port: 80
      weight: 10
    filters:
    - type: RequestHeaderModifier
      requestHeaderModifier:
        add:
        - name: X-Request-Source
          value: gateway
  - matches:
    - path:
        type: PathPrefix
        value: /v1
    backendRefs:
    - name: api-v1-service
      port: 80
```

**Migrazione da Ingress a Gateway API:**

La migrazione non richiede un approccio big-bang: Gateway API e Ingress possono coesistere nello stesso cluster. La strategia raccomandata prevede di installare un controller Gateway API (come Envoy Gateway, Istio, Cilium o il provider cloud nativo) accanto al controller Ingress esistente, ciascuno con il proprio IP esterno. Lo strumento `ingress2gateway` automatizza la conversione delle risorse Ingress esistenti in risorse Gateway API, traducendo le annotazioni controller-specific in funzionalita' native della Gateway API. Si consiglia di migrare prima i servizi non critici, validare il comportamento, e poi procedere progressivamente con i servizi di produzione.

```bash
# Installazione del tool di migrazione
go install github.com/kubernetes-sigs/ingress2gateway@latest

# Conversione delle risorse Ingress del namespace
ingress2gateway print --namespace produzione --all-resources

# Installazione di Envoy Gateway come implementazione Gateway API
helm install eg oci://docker.io/envoyproxy/gateway-helm \
  --version v1.2.0 \
  --namespace envoy-gateway-system --create-namespace
```

---

## Helm - Package Manager

Helm e' il package manager di Kubernetes. Permette di definire, installare e aggiornare applicazioni Kubernetes complesse attraverso pacchetti chiamati **chart**.

### Struttura di un Chart

```
mio-chart/
  Chart.yaml          # Metadati del chart (nome, versione, dipendenze)
  values.yaml         # Valori di configurazione predefiniti
  charts/             # Chart dipendenti
  templates/          # Template dei manifest Kubernetes
    deployment.yaml
    service.yaml
    ingress.yaml
    configmap.yaml
    _helpers.tpl      # Template helper riutilizzabili
    NOTES.txt         # Note post-installazione
  .helmignore         # File da ignorare nel packaging
```

### Utilizzo di Helm

```bash
# Aggiunta di un repository
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Ricerca di chart
helm search repo postgresql
helm search hub grafana

# Visualizzazione dei valori configurabili
helm show values bitnami/postgresql > postgres-values.yaml

# Installazione con valori personalizzati
helm install mio-postgres bitnami/postgresql \
  --namespace database --create-namespace \
  --values postgres-values.yaml \
  --set auth.postgresPassword=password-sicura \
  --set primary.persistence.size=50Gi

# Elenco delle release installate
helm list --all-namespaces

# Aggiornamento di una release
helm upgrade mio-postgres bitnami/postgresql \
  --namespace database \
  --values postgres-values.yaml \
  --set primary.resources.requests.memory=2Gi

# Rollback a una revisione precedente
helm rollback mio-postgres 1 --namespace database

# Disinstallazione
helm uninstall mio-postgres --namespace database
```

### Creazione di un Chart Personalizzato

```bash
# Creazione della struttura di un nuovo chart
helm create mia-applicazione
```

```yaml
# Chart.yaml
apiVersion: v2
name: mia-applicazione
description: Chart Helm per la mia applicazione web
type: application
version: 1.0.0
appVersion: "3.2.1"
dependencies:
- name: postgresql
  version: "15.x.x"
  repository: https://charts.bitnami.com/bitnami
  condition: postgresql.enabled
```

```yaml
# values.yaml
replicaCount: 3

image:
  repository: mia-app
  tag: "3.2.1"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: true
  className: nginx
  hosts:
  - host: app.esempio.com
    paths:
    - path: /
      pathType: Prefix

resources:
  requests:
    cpu: 200m
    memory: 256Mi
  limits:
    cpu: 1000m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 15
  targetCPUUtilizationPercentage: 70

postgresql:
  enabled: true
  auth:
    database: appdb
```

### Helmfile

Helmfile e' un tool dichiarativo per gestire le release Helm. E' particolarmente utile quando si devono gestire molteplici chart e ambienti.

```yaml
# helmfile.yaml
repositories:
- name: bitnami
  url: https://charts.bitnami.com/bitnami
- name: ingress-nginx
  url: https://kubernetes.github.io/ingress-nginx
- name: prometheus-community
  url: https://prometheus-community.github.io/helm-charts

environments:
  staging:
    values:
    - environments/staging/values.yaml
  produzione:
    values:
    - environments/produzione/values.yaml

releases:
- name: ingress-nginx
  namespace: ingress-nginx
  chart: ingress-nginx/ingress-nginx
  version: 4.11.0
  values:
  - values/ingress.yaml

- name: mia-app
  namespace: {{ .Environment.Name }}
  chart: ./charts/mia-applicazione
  values:
  - values/app-common.yaml
  - values/app-{{ .Environment.Name }}.yaml

- name: monitoring
  namespace: monitoring
  chart: prometheus-community/kube-prometheus-stack
  version: 62.0.0
  values:
  - values/monitoring.yaml
```

```bash
# Applicazione di tutte le release per l'ambiente di produzione
helmfile -e produzione apply

# Diff prima dell'applicazione
helmfile -e produzione diff

# Sync di una release specifica
helmfile -e produzione -l name=mia-app sync
```

### Helm Hooks

I Helm hook permettono di eseguire operazioni specifiche in determinati momenti del ciclo di vita di una release. Sono utili per migrazioni di database, caricamento di dati iniziali, backup pre-upgrade e validazioni post-installazione. Gli hook vengono definiti tramite l'annotazione `helm.sh/hook` sui manifest delle risorse.

```yaml
# Hook pre-install: esegue la migrazione del database prima del deployment
apiVersion: batch/v1
kind: Job
metadata:
  name: "{{ .Release.Name }}-db-migrate"
  annotations:
    "helm.sh/hook": pre-install,pre-upgrade
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  backoffLimit: 3
  template:
    spec:
      containers:
      - name: migrate
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
        command: ["./migrate", "--target", "latest"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: "{{ .Release.Name }}-db-credentials"
              key: connection-string
      restartPolicy: Never

---
# Hook post-install: esegue smoke test dopo il deployment
apiVersion: batch/v1
kind: Job
metadata:
  name: "{{ .Release.Name }}-smoke-test"
  annotations:
    "helm.sh/hook": post-install,post-upgrade
    "helm.sh/hook-weight": "10"
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  backoffLimit: 1
  template:
    spec:
      containers:
      - name: test
        image: curlimages/curl:8.11.0
        command: ["sh", "-c"]
        args:
        - |
          sleep 10
          curl -sf http://{{ .Release.Name }}-service/health || exit 1
          echo "Smoke test superato"
      restartPolicy: Never
```

**Tipi di hook disponibili:**

| Hook | Momento di Esecuzione |
|------|----------------------|
| `pre-install` | Prima di installare qualsiasi risorsa del chart |
| `post-install` | Dopo che tutte le risorse sono state caricate |
| `pre-delete` | Prima di eliminare qualsiasi risorsa |
| `post-delete` | Dopo l'eliminazione di tutte le risorse |
| `pre-upgrade` | Prima dell'aggiornamento delle risorse |
| `post-upgrade` | Dopo l'aggiornamento |
| `pre-rollback` | Prima di un rollback |
| `post-rollback` | Dopo un rollback |
| `test` | Eseguito con `helm test` |

L'attributo `hook-weight` controlla l'ordine di esecuzione degli hook (valori piu' bassi vengono eseguiti prima). La policy `hook-delete-policy` determina quando le risorse degli hook vengono eliminate: `before-hook-creation` rimuove la risorsa precedente prima di creare quella nuova, `hook-succeeded` la rimuove dopo il completamento con successo, e `hook-failed` la rimuove dopo un fallimento.

### Helm e OCI Registry

A partire da Helm 3.8+, il supporto OCI (Open Container Initiative) per i chart e' GA. Questo permette di archiviare e distribuire chart Helm utilizzando gli stessi registry usati per le immagini container (Docker Hub, GitHub Container Registry, AWS ECR, Azure ACR, Google Artifact Registry), semplificando la gestione dell'infrastruttura e unificando l'autenticazione.

```bash
# Login al registry OCI
helm registry login ghcr.io -u utente -p token

# Packaging e push di un chart
helm package ./mia-applicazione
helm push mia-applicazione-1.0.0.tgz oci://ghcr.io/mia-org/charts

# Pull di un chart da OCI registry
helm pull oci://ghcr.io/mia-org/charts/mia-applicazione --version 1.0.0

# Installazione diretta da OCI registry
helm install mia-app oci://ghcr.io/mia-org/charts/mia-applicazione \
  --version 1.0.0 \
  --namespace produzione \
  --values values-prod.yaml

# Visualizzazione dei tag disponibili
helm show all oci://ghcr.io/mia-org/charts/mia-applicazione --version 1.0.0
```

L'uso di OCI registry elimina la necessita' di gestire server Helm chart repository separati (come ChartMuseum) e permette di sfruttare le policy di sicurezza, la scansione di vulnerabilita' e la replica geografica gia' configurate per i registry container.

### Helm Template Best Practices

Quando si sviluppano chart Helm personalizzati, seguire queste linee guida per la manutenibilita':

- Utilizzare il file `_helpers.tpl` per centralizzare le funzioni template riutilizzabili (nomi, labels, selectors)
- Definire valori predefiniti sensati in `values.yaml` con commenti che descrivano ogni parametro
- Validare i valori di input utilizzando la funzione `required` per parametri obbligatori e `fail` per combinazioni non valide
- Utilizzare `{{- include }}` anziche' `{{- template }}` per poter utilizzare l'output delle funzioni in pipeline
- Strutturare i values per ambiente utilizzando file separati (`values-dev.yaml`, `values-staging.yaml`, `values-prod.yaml`) e composizione con `--values`

---

## RBAC - Controllo degli Accessi

Il Role-Based Access Control (RBAC) in Kubernetes regola l'accesso alle risorse del cluster basandosi su ruoli assegnati a utenti, gruppi o service account.

### Role e ClusterRole

```yaml
# Role - limitato a un namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: sviluppatore
  namespace: sviluppo
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log", "pods/exec", "services", "configmaps"]
  verbs: ["get", "list", "watch", "create", "update", "delete"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list"]    # Solo lettura per i secret

---
# ClusterRole - valido in tutto il cluster
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: lettore-cluster
rules:
- apiGroups: [""]
  resources: ["nodes", "namespaces", "persistentvolumes"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "statefulsets", "daemonsets"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["networking.k8s.io"]
  resources: ["ingresses", "networkpolicies"]
  verbs: ["get", "list", "watch"]
```

### RoleBinding e ClusterRoleBinding

```yaml
# RoleBinding - assegna un Role a un utente nel namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: sviluppatore-binding
  namespace: sviluppo
subjects:
- kind: User
  name: mario.rossi@esempio.com
  apiGroup: rbac.authorization.k8s.io
- kind: Group
  name: team-sviluppo
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: sviluppatore
  apiGroup: rbac.authorization.k8s.io

---
# ClusterRoleBinding - assegna un ClusterRole a livello di cluster
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: lettore-cluster-binding
subjects:
- kind: Group
  name: team-supporto
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: lettore-cluster
  apiGroup: rbac.authorization.k8s.io
```

### ServiceAccount

I ServiceAccount forniscono un'identita' ai processi che girano nei Pod per interagire con l'API Server.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ci-cd-deployer
  namespace: produzione
  annotations:
    # Per AWS IRSA (IAM Roles for Service Accounts)
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789:role/deployer-role

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: deployer-role
  namespace: produzione
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch", "update", "patch"]
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get", "list", "watch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: deployer-binding
  namespace: produzione
subjects:
- kind: ServiceAccount
  name: ci-cd-deployer
  namespace: produzione
roleRef:
  kind: Role
  name: deployer-role
  apiGroup: rbac.authorization.k8s.io
```

Il principio del **least privilege** (minimo privilegio) e' fondamentale: ogni utente, gruppo o service account deve avere esclusivamente i permessi strettamente necessari per svolgere il proprio compito. Evitare l'uso di `cluster-admin` se non assolutamente indispensabile, preferire Role a ClusterRole quando possibile, e limitare i verbi concessi alle sole operazioni richieste.

---

## Monitoring

### Prometheus Stack (kube-prometheus-stack)

Lo stack kube-prometheus-stack e' la soluzione standard per il monitoring dei cluster Kubernetes. Include Prometheus per la raccolta delle metriche, Grafana per la visualizzazione e Alertmanager per le notifiche.

```bash
# Installazione tramite Helm
helm repo add prometheus-community \
  https://prometheus-community.github.io/helm-charts
helm repo update

helm install kube-prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set prometheus.prometheusSpec.retention=30d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=100Gi \
  --set grafana.adminPassword='GrafanaAdmin123!' \
  --set alertmanager.alertmanagerSpec.storage.volumeClaimTemplate.spec.resources.requests.storage=10Gi
```

```yaml
# ServiceMonitor per monitorare la propria applicazione
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: api-backend-monitor
  namespace: monitoring
  labels:
    release: kube-prometheus
spec:
  namespaceSelector:
    matchNames:
    - produzione
  selector:
    matchLabels:
      app: api-backend
  endpoints:
  - port: metrics
    interval: 15s
    path: /metrics

---
# PrometheusRule per definire alert
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: api-alerts
  namespace: monitoring
  labels:
    release: kube-prometheus
spec:
  groups:
  - name: api-backend.rules
    rules:
    - alert: HighErrorRate
      expr: |
        sum(rate(http_requests_total{job="api-backend",status=~"5.."}[5m]))
        /
        sum(rate(http_requests_total{job="api-backend"}[5m]))
        > 0.05
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "Alto tasso di errori sull'API backend"
        description: "Il tasso di errori 5xx supera il 5% da 5 minuti."
    - alert: HighLatency
      expr: |
        histogram_quantile(0.95,
          sum(rate(http_request_duration_seconds_bucket{job="api-backend"}[5m]))
          by (le)
        ) > 2
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "Latenza elevata sull'API backend"
        description: "Il 95esimo percentile della latenza supera i 2 secondi."
```

### Grafana Dashboard

Grafana viene installato automaticamente con kube-prometheus-stack e include dashboard predefinite per il monitoring del cluster. Le dashboard piu' utili includono: panoramica del cluster (utilizzo CPU, memoria, disco e rete per nodo), stato dei pod e dei deployment, performance dell'API Server e di etcd, e metriche specifiche dei namespace. E' possibile creare dashboard personalizzate tramite l'interfaccia web o dichiarativamente come ConfigMap.

### Metrics Server

Il metrics-server e' un componente leggero che raccoglie le metriche di utilizzo di CPU e memoria dai kubelet di ogni nodo. E' necessario per il funzionamento dell'HPA e per il comando `kubectl top`.

```bash
# Installazione
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Visualizzazione dell'utilizzo risorse dei nodi
kubectl top nodes

# Visualizzazione dell'utilizzo risorse dei pod
kubectl top pods --namespace produzione --sort-by=memory
kubectl top pods --all-namespaces --sort-by=cpu
```

---

## Logging

### Architettura di Logging Centralizzato

In un cluster Kubernetes, i log vengono generati da molteplici sorgenti: container applicativi, componenti di sistema, audit log dell'API Server e log dei nodi. Una soluzione di logging centralizzato raccoglie, processa e indicizza tutti questi log in un unico punto per facilitare l'analisi e il debugging.

### EFK/ELK Stack

Lo stack EFK (Elasticsearch, Fluentd, Kibana) o ELK (Elasticsearch, Logstash, Kibana) e' una soluzione tradizionale e consolidata per la gestione centralizzata dei log.

- **Elasticsearch**: motore di ricerca e indicizzazione distribuito che archivia i log
- **Fluentd/Logstash**: agente di raccolta e trasformazione dei log (Fluentd e' generalmente preferito in ambienti Kubernetes per il minor consumo di risorse)
- **Kibana**: interfaccia web per la visualizzazione, la ricerca e l'analisi dei log

Fluentd viene tipicamente deployato come DaemonSet, in modo che ogni nodo abbia un agente di raccolta che legge i log dai file di log dei container (`/var/log/containers/`) e li invia a Elasticsearch.

### Loki + Promtail

Loki e' un sistema di aggregazione log sviluppato da Grafana Labs, progettato per essere efficiente e facile da gestire. A differenza di Elasticsearch, Loki non indicizza il contenuto completo dei log ma solo i metadati (label), rendendolo significativamente piu' leggero in termini di risorse.

```bash
# Installazione di Loki Stack tramite Helm
helm repo add grafana https://grafana.github.io/helm-charts
helm install loki grafana/loki-stack \
  --namespace logging --create-namespace \
  --set promtail.enabled=true \
  --set loki.persistence.enabled=true \
  --set loki.persistence.size=50Gi
```

```yaml
# Configurazione di Promtail come DaemonSet
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: promtail
  namespace: logging
spec:
  selector:
    matchLabels:
      app: promtail
  template:
    metadata:
      labels:
        app: promtail
    spec:
      serviceAccountName: promtail
      containers:
      - name: promtail
        image: grafana/promtail:3.2.0
        args:
        - -config.file=/etc/promtail/promtail.yaml
        volumeMounts:
        - name: config
          mountPath: /etc/promtail
        - name: varlog
          mountPath: /var/log
          readOnly: true
        - name: containers
          mountPath: /var/lib/docker/containers
          readOnly: true
        resources:
          requests:
            cpu: 50m
            memory: 64Mi
          limits:
            cpu: 200m
            memory: 128Mi
      tolerations:
      - operator: Exists
      volumes:
      - name: config
        configMap:
          name: promtail-config
      - name: varlog
        hostPath:
          path: /var/log
      - name: containers
        hostPath:
          path: /var/lib/docker/containers
```

Loki si integra nativamente con Grafana, permettendo di correlare metriche di Prometheus con log di Loki nella stessa interfaccia. Questa integrazione e' particolarmente potente per il troubleshooting: si puo' partire da un alert sulle metriche e navigare direttamente ai log correlati.

---

## Troubleshooting

### Comandi kubectl Essenziali

```bash
# Informazioni generali sul cluster
kubectl cluster-info
kubectl get componentstatuses    # Stato dei componenti del control plane

# Stato dei nodi
kubectl get nodes -o wide
kubectl describe node nome-nodo
kubectl top nodes

# Stato dei pod
kubectl get pods -n produzione -o wide
kubectl get pods --all-namespaces --field-selector=status.phase!=Running

# Informazioni dettagliate su un pod
kubectl describe pod nome-pod -n produzione

# Log dei container
kubectl logs nome-pod -n produzione
kubectl logs nome-pod -n produzione -c nome-container   # Multi-container
kubectl logs nome-pod -n produzione --previous           # Log del container precedente (crashato)
kubectl logs nome-pod -n produzione -f                   # Follow in tempo reale
kubectl logs nome-pod -n produzione --since=1h           # Ultime ore
kubectl logs -l app=api-backend -n produzione            # Log per label

# Esecuzione di comandi nel container
kubectl exec -it nome-pod -n produzione -- /bin/sh
kubectl exec nome-pod -n produzione -- cat /etc/app/config.yaml

# Debug con container effimero (Kubernetes >= 1.25)
kubectl debug -it nome-pod -n produzione --image=busybox:1.36 --target=app-container

# Port forwarding per accesso locale
kubectl port-forward svc/api-service 8080:80 -n produzione
kubectl port-forward pod/postgres-0 5432:5432 -n database

# Copia file da/verso un pod
kubectl cp produzione/nome-pod:/var/log/app.log ./app.log

# Visualizzazione degli eventi del namespace
kubectl get events -n produzione --sort-by=.lastTimestamp
kubectl get events --field-selector type=Warning --all-namespaces
```

### Problemi Comuni e Soluzioni

**CrashLoopBackOff**

Il Pod continua a crashare e Kubernetes riprova con backoff esponenziale.

```bash
# Diagnostica
kubectl describe pod nome-pod -n namespace    # Controllare sezione Events e Exit Code
kubectl logs nome-pod -n namespace --previous  # Log del crash precedente
```

Cause comuni: errore nell'applicazione, configurazione errata (variabili d'ambiente mancanti, file di configurazione non trovati), probe di liveness troppo aggressive, risorse insufficienti (OOM). Soluzioni: correggere il codice o la configurazione, aumentare i limiti di risorse, regolare le probe impostando `initialDelaySeconds` e `failureThreshold` adeguati.

**ImagePullBackOff**

Kubernetes non riesce a scaricare l'immagine del container.

```bash
# Diagnostica
kubectl describe pod nome-pod -n namespace    # Controllare il messaggio di errore nella sezione Events
kubectl get events -n namespace | grep -i pull
```

Cause comuni: nome o tag dell'immagine errati, registry privato senza credenziali configurate, registry irraggiungibile, quota di pull esaurita. Soluzioni: verificare il nome dell'immagine, creare e associare un Secret `docker-registry`, controllare la connettivita' di rete verso il registry.

**OOMKilled**

Il container ha superato il limite di memoria assegnato ed e' stato terminato dal kernel.

```bash
# Diagnostica
kubectl describe pod nome-pod -n namespace    # Controllare Last State: Terminated, Reason: OOMKilled
kubectl top pod nome-pod -n namespace --containers
```

Soluzioni: aumentare il limite di memoria, ottimizzare l'applicazione per ridurre il consumo di memoria, verificare eventuali memory leak. Controllare sia `requests` che `limits`: i `requests` influenzano lo scheduling, i `limits` determinano il kill del processo.

**Pod in stato Pending**

Il Pod rimane in stato Pending e non viene schedulato su nessun nodo.

```bash
# Diagnostica
kubectl describe pod nome-pod -n namespace    # Controllare sezione Events per messaggi di scheduling
kubectl get nodes -o wide
kubectl describe nodes | grep -A 5 "Allocated resources"
```

Cause comuni: risorse insufficienti nel cluster (CPU o memoria), nessun nodo soddisfa i vincoli di nodeSelector, affinita' o tolerations, PersistentVolumeClaim in stato Pending, ResourceQuota del namespace esaurita. Soluzioni: aggiungere nodi al cluster, ridurre le risorse richieste, verificare i vincoli di scheduling, controllare lo stato dei PVC.

### Metodologia di Debugging

Una metodologia sistematica per il troubleshooting in Kubernetes segue questi passaggi:

1. **Identificare il sintomo**: determinare quale risorsa ha problemi (`kubectl get` con flag `-o wide`)
2. **Raccogliere informazioni**: usare `kubectl describe` per dettagli sulla risorsa e sugli eventi correlati
3. **Controllare i log**: esaminare i log del container corrente e precedente con `kubectl logs`
4. **Verificare la configurazione**: controllare ConfigMap, Secret, variabili d'ambiente e volumi montati
5. **Testare la connettivita'**: usare `kubectl exec` per verificare la rete dall'interno del pod, oppure `kubectl debug` per container minimali
6. **Controllare le risorse**: verificare l'utilizzo di CPU e memoria con `kubectl top` e confrontarlo con i limiti impostati
7. **Esaminare gli eventi**: `kubectl get events` fornisce una cronologia degli eventi che spesso indica la causa del problema
8. **Consultare i componenti di sistema**: controllare i log di kubelet, kube-proxy e dei controller se il problema non e' a livello applicativo

---

## Managed Kubernetes

### Confronto tra Servizi Managed

| Caratteristica | Amazon EKS | Azure AKS | Google GKE |
|---------------|------------|-----------|------------|
| **Costo Control Plane** | $0.10/ora (~$73/mese) | Gratuito (tier standard) | Gratuito (Autopilot e Standard) |
| **Versioni K8s** | Supporto fino a 4 versioni minori | Supporto fino a 3 versioni minori | Supporto fino a 3 versioni minori + canale Rapid |
| **Networking** | VPC CNI (IP nativi AWS) | Azure CNI / Kubenet | GKE networking nativo VPC |
| **Scaling** | Karpenter / Cluster Autoscaler | KEDA / Cluster Autoscaler | Autopilot / Cluster Autoscaler |
| **Service Mesh** | AWS App Mesh / Istio | Open Service Mesh / Istio | Anthos Service Mesh (Istio) |
| **Registro Container** | ECR | ACR | Artifact Registry |
| **Integrazione IAM** | IRSA / Pod Identity | Workload Identity | Workload Identity |
| **GPU Support** | Eccellente (ampia scelta istanze) | Buono | Eccellente (TPU incluse) |
| **Modalita' Serverless** | Fargate | Virtual Nodes (ACI) | Autopilot |
| **CLI** | eksctl | az aks | gcloud container |
| **Maturita'** | Molto maturo | Maturo | Molto maturo (nato in Google) |

### Managed vs Self-Hosted

**Vantaggi del Managed Kubernetes:**

- Il control plane e' gestito e mantenuto dal cloud provider con SLA garantito
- Aggiornamenti automatici o semplificati della versione di Kubernetes
- Integrazione nativa con i servizi cloud (load balancer, storage, IAM, monitoring)
- Riduzione del carico operativo sul team di infrastruttura
- Alta disponibilita' del control plane inclusa nel servizio
- Patch di sicurezza gestite dal provider per i componenti del control plane

**Vantaggi del Self-Hosted:**

- Controllo completo su tutti i componenti e la loro configurazione
- Nessun vendor lock-in verso un cloud provider specifico
- Possibilita' di esecuzione on-premise o in ambienti ibridi
- Costo potenzialmente inferiore per cluster di grandi dimensioni
- Personalizzazione avanzata del control plane (scheduler personalizzato, admission controller custom)
- Indipendenza dalle limitazioni e dalle policy del cloud provider

La scelta dipende dalle competenze del team, dal budget, dai requisiti di compliance e dalla scala dell'infrastruttura. Per la maggior parte delle organizzazioni, un servizio managed rappresenta la scelta piu' pragmatica, a meno che non ci siano requisiti specifici che richiedano il controllo totale dell'infrastruttura.

---

## Sicurezza Avanzata

### Pod Security Standards (PSS)

I Pod Security Standards sostituiscono le PodSecurityPolicy (rimosse in Kubernetes 1.25) e definiscono tre livelli di sicurezza progressivi applicati a livello di namespace tramite label:

- **Privileged**: nessuna restrizione, permette qualsiasi configurazione. Destinato esclusivamente a workload di sistema come i DaemonSet di logging o networking che richiedono accesso privilegiato al nodo.
- **Baseline**: restrizioni minime che prevengono le escalation di privilegi piu' comuni. Blocca `hostNetwork`, `hostPID`, `hostIPC` e container privilegiati, ma permette la maggior parte delle configurazioni standard. Adatto per applicazioni generiche che non necessitano di privilegi speciali.
- **Restricted**: restrizioni rigorose che seguono le best practice di hardening. Richiede `runAsNonRoot`, impedisce l'aggiunta di capability Linux, forza il drop di ALL capabilities, richiede `seccompProfile`, blocca volume hostPath. Questo e' il livello raccomandato per tutti i workload di produzione.

```yaml
# Applicazione dei Pod Security Standards via namespace label
apiVersion: v1
kind: Namespace
metadata:
  name: produzione
  labels:
    # Modalita': enforce (blocca), warn (avvisa), audit (solo log)
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: latest
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: latest

---
# Pod conforme al livello Restricted
apiVersion: v1
kind: Pod
metadata:
  name: app-sicura
  namespace: produzione
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 3000
    fsGroup: 2000
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: app
    image: mia-app:3.0
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
    resources:
      requests:
        cpu: "100m"
        memory: "128Mi"
      limits:
        cpu: "500m"
        memory: "256Mi"
    volumeMounts:
    - name: tmp
      mountPath: /tmp
  volumes:
  - name: tmp
    emptyDir:
      sizeLimit: 100Mi
```

La strategia raccomandata per l'adozione in cluster esistenti e' graduale: iniziare con la modalita' `audit` per identificare i workload non conformi senza interromperli, poi passare a `warn` per notificare gli sviluppatori, e infine attivare `enforce` quando tutti i workload sono stati adeguati.

### OPA Gatekeeper

Open Policy Agent (OPA) Gatekeeper e' un admission controller che valuta le richieste all'API Server di Kubernetes rispetto a policy definite nel linguaggio Rego. Gatekeeper opera come webhook di validazione: ogni richiesta di creazione o modifica di risorse viene intercettata e valutata prima di essere accettata dal cluster.

L'architettura di Gatekeeper si basa su due concetti:

- **ConstraintTemplate**: definisce la logica della policy in Rego, creando un nuovo tipo di vincolo riutilizzabile
- **Constraint**: istanza di un ConstraintTemplate con parametri specifici, applicata a determinate risorse

```yaml
# ConstraintTemplate: impedisce l'uso di immagini con tag 'latest'
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8sdisallowedtags
spec:
  crd:
    spec:
      names:
        kind: K8sDisallowedTags
      validation:
        openAPIV3Schema:
          type: object
          properties:
            tags:
              type: array
              items:
                type: string
  targets:
  - target: admission.k8s.gatekeeper.sh
    rego: |
      package k8sdisallowedtags
      violation[{"msg": msg}] {
        container := input.review.object.spec.containers[_]
        tag := [t | t := input.parameters.tags[_]; endswith(container.image, concat(":", ["", t]))]
        count(tag) > 0
        msg := sprintf("L'immagine '%v' usa un tag non consentito", [container.image])
      }
      violation[{"msg": msg}] {
        container := input.review.object.spec.containers[_]
        not contains(container.image, ":")
        msg := sprintf("L'immagine '%v' non specifica un tag (default 'latest' non consentito)", [container.image])
      }

---
# Constraint: applica la policy a tutti i pod nel cluster
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sDisallowedTags
metadata:
  name: no-latest-tag
spec:
  match:
    kinds:
    - apiGroups: [""]
      kinds: ["Pod"]
    - apiGroups: ["apps"]
      kinds: ["Deployment", "StatefulSet", "DaemonSet"]
    excludedNamespaces:
    - kube-system
    - gatekeeper-system
  parameters:
    tags: ["latest"]
```

### Kyverno

Kyverno e' un policy engine nativo per Kubernetes che utilizza YAML per la definizione delle policy, eliminando la necessita' di apprendere un linguaggio separato come Rego. Oltre alla validazione, Kyverno supporta la mutazione (modifica automatica delle risorse) e la generazione (creazione automatica di risorse basata su eventi). Kyverno e' un progetto CNCF Graduated.

```yaml
# Policy di validazione: richiede label obbligatorie
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: richiedi-labels-obbligatorie
  annotations:
    policies.kyverno.io/title: Richiedi Labels Obbligatorie
    policies.kyverno.io/severity: medium
spec:
  validationFailureAction: Enforce
  background: true
  rules:
  - name: verifica-label-app
    match:
      any:
      - resources:
          kinds:
          - Deployment
          - StatefulSet
          - DaemonSet
    validate:
      message: >-
        Le risorse devono avere le label 'app', 'versione' e 'team'
        definite nel template dei pod.
      pattern:
        spec:
          template:
            metadata:
              labels:
                app: "?*"
                versione: "?*"
                team: "?*"

---
# Policy di mutazione: aggiunge limiti di risorse predefiniti
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: aggiungi-limiti-default
spec:
  rules:
  - name: imposta-limiti-memoria
    match:
      any:
      - resources:
          kinds:
          - Pod
    exclude:
      any:
      - resources:
          namespaces:
          - kube-system
    mutate:
      patchStrategicMerge:
        spec:
          containers:
          - (name): "*"
            resources:
              limits:
                +(memory): "512Mi"
              requests:
                +(memory): "128Mi"

---
# Policy di generazione: crea NetworkPolicy per ogni nuovo namespace
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: genera-networkpolicy-default
spec:
  rules:
  - name: default-deny-ingress
    match:
      any:
      - resources:
          kinds:
          - Namespace
    exclude:
      any:
      - resources:
          names:
          - kube-system
          - kube-public
          - kube-node-lease
    generate:
      apiVersion: networking.k8s.io/v1
      kind: NetworkPolicy
      name: default-deny-ingress
      namespace: "{{ request.object.metadata.name }}"
      data:
        spec:
          podSelector: {}
          policyTypes:
          - Ingress
```

**Confronto OPA Gatekeeper vs Kyverno:**

| Aspetto | OPA Gatekeeper | Kyverno |
|---------|----------------|---------|
| Linguaggio policy | Rego (curva di apprendimento ripida) | YAML nativo Kubernetes |
| Validazione | Completa | Completa |
| Mutazione | Non supportata nativamente | Supportata |
| Generazione risorse | Non supportata | Supportata |
| Ambito d'uso | Generale (non solo K8s) | Specifico per Kubernetes |
| Complessita' operativa | Media-alta (OPA + Gatekeeper) | Bassa (singolo componente) |
| Policy library | Gatekeeper Library | Kyverno Policy Library (200+ policy) |
| Progetto CNCF | Graduated (OPA) | Graduated |

Per la maggior parte dei team Kubernetes, Kyverno rappresenta la scelta piu' accessibile grazie alla sintassi YAML nativa. OPA Gatekeeper e' preferibile quando si necessita di un motore policy unificato che operi anche al di fuori di Kubernetes (API gateway, pipeline CI/CD, microservizi).

### Image Scanning e Supply Chain Security

La sicurezza della supply chain delle immagini container e' fondamentale per prevenire l'introduzione di vulnerabilita' note o componenti malevoli nel cluster. Una strategia completa prevede:

- **Scansione vulnerabilita'**: integrare strumenti come Trivy, Grype o Snyk nella pipeline CI/CD per scansionare le immagini prima del push al registry. Configurare admission controller per bloccare il deployment di immagini con vulnerabilita' critiche non risolte.
- **Firma delle immagini**: utilizzare Cosign (parte del progetto Sigstore, CNCF Graduated) per firmare crittograficamente le immagini dopo la build. Configurare Kyverno o Gatekeeper per verificare le firme prima dell'ammissione nel cluster.
- **SBOM (Software Bill of Materials)**: generare e archiviare il SBOM per ogni immagine, documentando tutti i componenti e le dipendenze incluse. Strumenti come Syft generano SBOM in formato SPDX o CycloneDX.
- **Registry privato con policy di accesso**: configurare un registry privato con scansione automatica, policy di retention e accesso controllato. Evitare l'uso di immagini da registry pubblici non verificati in produzione.

---

## Observability Avanzata

### Prometheus Operator - Approfondimento

Il Prometheus Operator, distribuito come parte di kube-prometheus-stack, semplifica drasticamente il deployment e la configurazione di Prometheus su Kubernetes introducendo Custom Resource Definitions (CRD) che rendono la configurazione del monitoring dichiarativa e nativa Kubernetes.

Le CRD principali del Prometheus Operator sono:

- **Prometheus**: definisce un'istanza Prometheus, inclusi retention, storage, replicas, sharding e configurazione delle regole
- **ServiceMonitor**: configura il discovery dei target da monitorare basandosi su label dei Service Kubernetes
- **PodMonitor**: simile a ServiceMonitor ma opera direttamente sui Pod senza richiedere un Service
- **PrometheusRule**: definisce le regole di alerting e le recording rule di Prometheus
- **Alertmanager**: configura un'istanza Alertmanager per la gestione e il routing delle notifiche

```yaml
# PodMonitor per monitorare pod senza Service
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: batch-jobs-monitor
  namespace: monitoring
  labels:
    release: kube-prometheus
spec:
  namespaceSelector:
    matchNames:
    - batch-processing
  selector:
    matchLabels:
      monitoring: enabled
  podMetricsEndpoints:
  - port: metrics
    interval: 30s
    path: /metrics

---
# Alertmanager config per routing intelligente degli alert
apiVersion: monitoring.coreos.com/v1alpha1
kind: AlertmanagerConfig
metadata:
  name: routing-alert-produzione
  namespace: produzione
  labels:
    release: kube-prometheus
spec:
  route:
    receiver: team-platform
    groupBy: ['alertname', 'namespace']
    groupWait: 30s
    groupInterval: 5m
    repeatInterval: 4h
    routes:
    - matchers:
      - name: severity
        value: critical
      receiver: pagerduty-critical
      repeatInterval: 1h
    - matchers:
      - name: severity
        value: warning
      receiver: slack-warning
  receivers:
  - name: team-platform
    slackConfigs:
    - channel: '#alerts-platform'
      sendResolved: true
  - name: pagerduty-critical
    pagerdutyConfigs:
    - serviceKey:
        name: pagerduty-secret
        key: service-key
  - name: slack-warning
    slackConfigs:
    - channel: '#alerts-warning'
      sendResolved: true
```

### kube-state-metrics

kube-state-metrics e' un servizio che ascolta l'API Server di Kubernetes e genera metriche sullo stato degli oggetti del cluster (Deployment, Pod, Node, PVC, Job, ecc.). A differenza del metrics-server che fornisce metriche di utilizzo risorse in tempo reale (CPU/memoria), kube-state-metrics fornisce informazioni sullo stato desiderato e attuale degli oggetti Kubernetes.

Metriche chiave esposte da kube-state-metrics:

| Metrica | Descrizione | Uso Tipico |
|---------|-------------|------------|
| `kube_deployment_spec_replicas` | Repliche desiderate | Confronto con repliche disponibili |
| `kube_deployment_status_replicas_available` | Repliche effettivamente disponibili | Rilevamento deployment degradati |
| `kube_pod_status_phase` | Fase del pod (Pending/Running/Failed) | Monitoraggio salute dei pod |
| `kube_pod_container_status_restarts_total` | Numero totale di riavvii | Rilevamento CrashLoopBackOff |
| `kube_node_status_condition` | Condizioni del nodo (Ready, DiskPressure) | Monitoraggio salute dei nodi |
| `kube_persistentvolumeclaim_status_phase` | Stato del PVC (Bound/Pending) | Rilevamento problemi di storage |
| `kube_job_status_succeeded` | Job completati con successo | Monitoraggio pipeline batch |
| `kube_horizontalpodautoscaler_status_current_replicas` | Repliche attuali HPA | Monitoraggio autoscaling |

Queste metriche sono fondamentali per costruire dashboard e alert che riflettano lo stato operativo del cluster al di la' del semplice utilizzo di risorse.

### Distributed Tracing con OpenTelemetry

OpenTelemetry (OTel) e' il progetto CNCF che unifica la raccolta di tracce, metriche e log dalle applicazioni distribuite. In un ambiente Kubernetes con microservizi, il distributed tracing e' essenziale per comprendere il flusso delle richieste attraverso i servizi e identificare colli di bottiglia.

L'architettura consigliata prevede il deployment dell'OpenTelemetry Collector come DaemonSet (per la raccolta a livello di nodo) o come Deployment (per aggregazione e processing centralizzato). Le applicazioni inviano i dati di telemetria al Collector locale tramite OTLP (OpenTelemetry Protocol), e il Collector li processa e li esporta verso i backend di archiviazione (Jaeger, Tempo, Zipkin per le tracce; Prometheus per le metriche; Loki per i log).

```yaml
# OpenTelemetry Collector come DaemonSet
apiVersion: opentelemetry.io/v1beta1
kind: OpenTelemetryCollector
metadata:
  name: otel-collector
  namespace: observability
spec:
  mode: daemonset
  config:
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318
    processors:
      batch:
        send_batch_size: 1024
        timeout: 5s
      memory_limiter:
        check_interval: 1s
        limit_mib: 512
        spike_limit_mib: 128
    exporters:
      otlp/tempo:
        endpoint: tempo.observability:4317
        tls:
          insecure: true
      prometheus:
        endpoint: 0.0.0.0:8889
    service:
      pipelines:
        traces:
          receivers: [otlp]
          processors: [memory_limiter, batch]
          exporters: [otlp/tempo]
        metrics:
          receivers: [otlp]
          processors: [memory_limiter, batch]
          exporters: [prometheus]
```

---

## Autoscaling Avanzato

### KEDA (Kubernetes Event-Driven Autoscaling)

KEDA e' un progetto CNCF Graduated che estende l'HPA nativo di Kubernetes con autoscaling basato su eventi. Mentre l'HPA scala in base a metriche di risorse (CPU, memoria) o metriche custom, KEDA permette di scalare in base a eventi provenienti da sorgenti esterne come code di messaggi, database, stream di eventi e servizi cloud. KEDA supporta oltre 70 scaler integrati e permette lo scale-to-zero, una funzionalita' non disponibile con l'HPA standard.

KEDA non sostituisce l'HPA ma lo estende: crea e gestisce oggetti HPA alimentandoli con le metriche degli eventi esterni. L'architettura di KEDA comprende tre componenti:

- **Operator**: gestisce il ciclo di vita degli oggetti ScaledObject e ScaledJob
- **Metrics Server**: espone le metriche degli eventi esterni all'HPA
- **Admission Webhooks**: validano le configurazioni per prevenire conflitti

```bash
# Installazione di KEDA tramite Helm
helm repo add kedacore https://kedacore.github.io/charts
helm install keda kedacore/keda \
  --namespace keda --create-namespace \
  --set podAnnotations."prometheus\.io/scrape"="true"
```

```yaml
# ScaledObject: scala in base alla lunghezza di una coda RabbitMQ
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: worker-scaler
  namespace: produzione
spec:
  scaleTargetRef:
    name: worker-deployment
  pollingInterval: 15
  cooldownPeriod: 300
  minReplicaCount: 0            # Scale to zero quando la coda e' vuota
  maxReplicaCount: 50
  triggers:
  - type: rabbitmq
    metadata:
      host: "amqp://user:password@rabbitmq.messaging:5672/"
      queueName: task-queue
      queueLength: "5"          # 1 replica ogni 5 messaggi in coda
    authenticationRef:
      name: rabbitmq-auth

---
# ScaledObject: scala in base a metriche Prometheus custom
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: api-scaler
  namespace: produzione
spec:
  scaleTargetRef:
    name: api-backend
  pollingInterval: 10
  cooldownPeriod: 120
  minReplicaCount: 2
  maxReplicaCount: 30
  advanced:
    restoreToOriginalReplicaCount: true
    horizontalPodAutoscalerConfig:
      behavior:
        scaleDown:
          stabilizationWindowSeconds: 300
  triggers:
  - type: prometheus
    metadata:
      serverAddress: http://prometheus.monitoring:9090
      metricName: http_requests_per_second
      query: sum(rate(http_requests_total{namespace="produzione",service="api-backend"}[2m]))
      threshold: "100"

---
# ScaledJob: scala Job in base a messaggi Kafka
apiVersion: keda.sh/v1alpha1
kind: ScaledJob
metadata:
  name: kafka-consumer-job
  namespace: batch
spec:
  jobTargetRef:
    template:
      spec:
        containers:
        - name: consumer
          image: kafka-consumer:2.0
          env:
          - name: KAFKA_BROKERS
            value: "kafka.messaging:9092"
        restartPolicy: Never
  pollingInterval: 10
  maxReplicaCount: 20
  successfulJobsHistoryLimit: 5
  failedJobsHistoryLimit: 3
  triggers:
  - type: kafka
    metadata:
      bootstrapServers: kafka.messaging:9092
      consumerGroup: batch-consumer
      topic: events-topic
      lagThreshold: "10"
```

### Cluster Autoscaler e Karpenter

Il Cluster Autoscaler e Karpenter operano a livello di infrastruttura, aggiungendo o rimuovendo nodi dal cluster in base alla domanda di risorse.

**Cluster Autoscaler** e' la soluzione storica, supportata da tutti i cloud provider. Monitora i pod in stato Pending (che non possono essere schedulati per mancanza di risorse) e aggiunge nodi ai node group predefiniti. Quando i nodi sono sottoutilizzati, li rimuove dopo aver spostato i pod su altri nodi. Il Cluster Autoscaler opera su node group con dimensioni e tipi di istanza predefiniti, il che puo' portare a sprechi quando le dimensioni del node group non corrispondono precisamente alle esigenze dei workload.

**Karpenter** (CNCF Incubating, 2025) e' il successore del Cluster Autoscaler per AWS EKS ed e' in fase di adozione su altri provider. A differenza del Cluster Autoscaler, Karpenter non richiede la definizione di node group predefiniti: seleziona automaticamente il tipo di istanza ottimale in base ai requisiti dei pod in attesa, alla disponibilita' delle istanze e ai vincoli di costo. Karpenter provisiona un nuovo nodo in 30-60 secondi rispetto ai 3-5 minuti del Cluster Autoscaler, grazie al bypass della logica dei node group di auto scaling.

```yaml
# Karpenter NodePool: definisce i vincoli per il provisioning dei nodi
apiVersion: karpenter.sh/v1
kind: NodePool
metadata:
  name: default
spec:
  template:
    spec:
      requirements:
      - key: kubernetes.io/arch
        operator: In
        values: ["amd64"]
      - key: karpenter.sh/capacity-type
        operator: In
        values: ["on-demand", "spot"]
      - key: karpenter.k8s.aws/instance-category
        operator: In
        values: ["c", "m", "r"]
      - key: karpenter.k8s.aws/instance-generation
        operator: Gt
        values: ["5"]
      nodeClassRef:
        group: karpenter.k8s.aws
        kind: EC2NodeClass
        name: default
  limits:
    cpu: "1000"
    memory: 2000Gi
  disruption:
    consolidationPolicy: WhenEmptyOrUnderutilized
    consolidateAfter: 30s

---
apiVersion: karpenter.k8s.aws/v1
kind: EC2NodeClass
metadata:
  name: default
spec:
  amiSelectorTerms:
  - alias: al2023@latest
  subnetSelectorTerms:
  - tags:
      karpenter.sh/discovery: "mio-cluster"
  securityGroupSelectorTerms:
  - tags:
      karpenter.sh/discovery: "mio-cluster"
  blockDeviceMappings:
  - deviceName: /dev/xvda
    ebs:
      volumeSize: 100Gi
      volumeType: gp3
      encrypted: true
```

### Combinazione degli Autoscaler

La strategia di autoscaling piu' efficace combina tutti i livelli:

1. **HPA** per lo scaling orizzontale dei pod basato su CPU, memoria e metriche custom
2. **VPA** per l'ottimizzazione verticale delle risorse (in modalita' `Off` per le sole raccomandazioni, se si usa gia' HPA)
3. **KEDA** per lo scaling event-driven da sorgenti esterne (code, stream, metriche)
4. **Karpenter/Cluster Autoscaler** per lo scaling dell'infrastruttura sottostante

HPA e VPA non devono operare contemporaneamente sulla stessa metrica (es. CPU). La combinazione tipica e' HPA sulla CPU con VPA in modalita' raccomandazione per ottimizzare i valori di `requests` e `limits`.

---

## GitOps: ArgoCD e Flux

### Principi del GitOps

GitOps e' un framework operativo che utilizza Git come unica fonte di verita' per lo stato desiderato dell'infrastruttura e delle applicazioni. I quattro principi fondamentali del GitOps (definiti dal GitOps Working Group della CNCF) sono:

1. **Dichiarativo**: lo stato desiderato dell'intero sistema e' espresso in modo dichiarativo
2. **Versionato e immutabile**: lo stato desiderato e' archiviato in un modo che garantisce immutabilita', versionamento e storia completa
3. **Automaticamente applicato**: agenti software applicano automaticamente lo stato desiderato al sistema
4. **Riconciliazione continua**: gli agenti osservano lo stato attuale e tentano continuamente di riportarlo allo stato desiderato

In pratica, ogni modifica all'infrastruttura o alle applicazioni avviene tramite una modifica al repository Git (commit o merge di una pull request). Un agente GitOps nel cluster rileva la modifica e la applica automaticamente, garantendo che lo stato del cluster sia sempre allineato con il repository.

### ArgoCD

ArgoCD e' la soluzione GitOps piu' diffusa per Kubernetes, con un'interfaccia web completa per la visualizzazione e la gestione dello stato delle applicazioni. ArgoCD e' un progetto CNCF Graduated.

```bash
# Installazione di ArgoCD
kubectl create namespace argocd
kubectl apply -n argocd \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Recupero della password iniziale
argocd admin initial-password -n argocd

# Login tramite CLI
argocd login argocd-server.argocd.svc.cluster.local --grpc-web

# Registrazione di un cluster esterno (per deploy multi-cluster)
argocd cluster add nome-contesto-kubeconfig
```

```yaml
# Application: definisce un'applicazione da sincronizzare
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: api-backend-prod
  namespace: argocd
  finalizers:
  - resources-finalizer.argocd.argoproj.io
spec:
  project: produzione
  source:
    repoURL: https://github.com/mia-org/k8s-manifests.git
    targetRevision: main
    path: apps/api-backend/overlays/produzione
  destination:
    server: https://kubernetes.default.svc
    namespace: produzione
  syncPolicy:
    automated:
      prune: true           # Elimina risorse non piu' nel repo
      selfHeal: true         # Riporta lo stato al desiderato se modificato manualmente
      allowEmpty: false
    syncOptions:
    - CreateNamespace=true
    - PrunePropagationPolicy=foreground
    - ServerSideApply=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m

---
# AppProject: isolamento e policy per gruppo di applicazioni
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: produzione
  namespace: argocd
spec:
  description: "Progetto per le applicazioni di produzione"
  sourceRepos:
  - 'https://github.com/mia-org/k8s-manifests.git'
  - 'https://github.com/mia-org/helm-charts.git'
  destinations:
  - namespace: produzione
    server: https://kubernetes.default.svc
  - namespace: produzione-jobs
    server: https://kubernetes.default.svc
  clusterResourceWhitelist:
  - group: ''
    kind: Namespace
  namespaceResourceBlacklist:
  - group: ''
    kind: ResourceQuota
  roles:
  - name: deployer
    policies:
    - p, proj:produzione:deployer, applications, sync, produzione/*, allow
    - p, proj:produzione:deployer, applications, get, produzione/*, allow
    groups:
    - team-platform
```

**ApplicationSet** per la gestione di applicazioni multi-ambiente o multi-cluster:

```yaml
# ApplicationSet: genera Application per ogni ambiente
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: api-backend-ambienti
  namespace: argocd
spec:
  generators:
  - list:
      elements:
      - ambiente: sviluppo
        cluster: https://kubernetes.default.svc
        namespace: sviluppo
        revision: develop
      - ambiente: staging
        cluster: https://kubernetes.default.svc
        namespace: staging
        revision: release
      - ambiente: produzione
        cluster: https://prod-cluster:6443
        namespace: produzione
        revision: main
  template:
    metadata:
      name: 'api-backend-{{ambiente}}'
    spec:
      project: '{{ambiente}}'
      source:
        repoURL: https://github.com/mia-org/k8s-manifests.git
        targetRevision: '{{revision}}'
        path: 'apps/api-backend/overlays/{{ambiente}}'
      destination:
        server: '{{cluster}}'
        namespace: '{{namespace}}'
```

### Flux CD

Flux e' un toolkit GitOps leggero e modulare per Kubernetes, composto da controller specializzati che operano indipendentemente. Flux e' un progetto CNCF Graduated. A differenza di ArgoCD che fornisce un'interfaccia web integrata, Flux segue una filosofia piu' composable, dove ogni controller gestisce un aspetto specifico del workflow GitOps.

I controller principali di Flux sono:

- **Source Controller**: gestisce le sorgenti (Git repository, Helm repository, OCI repository, S3 bucket)
- **Kustomize Controller**: riconcilia le risorse Kustomize definite nelle sorgenti
- **Helm Controller**: gestisce le release Helm dichiarativamente tramite CRD HelmRelease
- **Notification Controller**: gestisce le notifiche in ingresso (webhook da Git provider) e in uscita (Slack, Teams, webhook)
- **Image Automation Controllers**: automatizzano l'aggiornamento delle immagini container nel repository Git

```bash
# Installazione di Flux tramite CLI
flux install

# Bootstrap: configura Flux e il repository Git in un singolo comando
flux bootstrap github \
  --owner=mia-org \
  --repository=fleet-infra \
  --branch=main \
  --path=./clusters/produzione \
  --personal
```

```yaml
# GitRepository: definisce la sorgente
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: infra-repo
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/mia-org/k8s-manifests.git
  ref:
    branch: main
  secretRef:
    name: git-credentials

---
# Kustomization: riconcilia un path del repository
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: api-backend
  namespace: flux-system
spec:
  interval: 5m
  sourceRef:
    kind: GitRepository
    name: infra-repo
  path: ./apps/api-backend/overlays/produzione
  prune: true
  healthChecks:
  - apiVersion: apps/v1
    kind: Deployment
    name: api-backend
    namespace: produzione
  timeout: 3m

---
# HelmRelease: gestione dichiarativa di release Helm
apiVersion: helm.toolkit.fluxcd.io/v2
kind: HelmRelease
metadata:
  name: monitoring-stack
  namespace: flux-system
spec:
  interval: 10m
  chart:
    spec:
      chart: kube-prometheus-stack
      version: "62.x"
      sourceRef:
        kind: HelmRepository
        name: prometheus-community
      interval: 1h
  targetNamespace: monitoring
  install:
    createNamespace: true
  values:
    prometheus:
      prometheusSpec:
        retention: 30d
    grafana:
      adminPassword:
        existingSecret: grafana-admin-secret
```

**Confronto ArgoCD vs Flux:**

| Aspetto | ArgoCD | Flux |
|---------|--------|------|
| UI Web | Integrata, completa | Assente (usa Weave GitOps o Capacitor) |
| Architettura | Monolitica (un deployment) | Modulare (controller separati) |
| Multi-tenancy | Nativa con AppProject | Tramite namespace e RBAC |
| Helm Support | Nativo | Tramite HelmController CRD |
| Image Automation | Argo CD Image Updater (separato) | Integrato (Image Reflector + Automation) |
| Risorse richieste | ~300MB RAM per controller | ~150MB RAM per controller set |
| Curva apprendimento | Bassa (UI intuitiva) | Media (CLI + CRD) |
| Multi-cluster | Nativo (gestione centralizzata) | Tramite bootstrap su ogni cluster |
| CNCF | Graduated | Graduated |

La scelta tra ArgoCD e Flux dipende dal contesto: ArgoCD e' preferibile per team che necessitano di un'interfaccia visuale e di gestione multi-cluster centralizzata; Flux e' ideale per team che preferiscono un approccio leggero, composable e fortemente integrato con Kustomize e Helm.

---

## Gestione Multi-Cluster

### Scenari Multi-Cluster

La gestione di piu' cluster Kubernetes e' una realta' consolidata nelle organizzazioni moderne. I principali scenari che richiedono un'architettura multi-cluster includono:

- **Alta disponibilita' geografica**: cluster in regioni diverse per resilienza a disastri regionali e riduzione della latenza per utenti distribuiti globalmente
- **Isolamento ambienti**: cluster separati per sviluppo, staging e produzione, con policy di accesso distinte
- **Compliance e residenza dei dati**: cluster dedicati per rispettare normative sulla localita' dei dati (GDPR, sovranita' dei dati)
- **Multi-cloud / hybrid cloud**: cluster su cloud provider diversi o combinazione cloud + on-premise per evitare vendor lock-in
- **Scalabilita' organizzativa**: cluster dedicati per business unit o team diversi con autonomia operativa

### Karmada

Karmada (Kubernetes Armada) e' un progetto CNCF Incubating che fornisce orchestrazione multi-cluster nativa Kubernetes. Karmada utilizza le stesse API di Kubernetes per definire i template delle risorse federate, rendendo la migrazione da single-cluster a multi-cluster trasparente per gli sviluppatori. Nei test di scala, Karmada ha dimostrato la capacita' di gestire 100 cluster con 500.000 nodi e oltre 2 milioni di pod contemporaneamente.

L'architettura di Karmada prevede un control plane centrale che gestisce la distribuzione dei workload sui cluster member. Le risorse vengono definite una volta sul control plane e distribuite automaticamente secondo le policy di propagazione configurate.

```yaml
# PropagationPolicy: distribuisce un Deployment su piu' cluster
apiVersion: policy.karmada.io/v1alpha1
kind: PropagationPolicy
metadata:
  name: api-backend-propagation
spec:
  resourceSelectors:
  - apiVersion: apps/v1
    kind: Deployment
    name: api-backend
  - apiVersion: v1
    kind: Service
    name: api-service
  placement:
    clusterAffinity:
      clusterNames:
      - cluster-eu-west
      - cluster-us-east
      - cluster-ap-southeast
    replicaScheduling:
      replicaDivisionPreference: Weighted
      replicaSchedulingType: Divided
      weightPreference:
        staticWeightList:
        - targetCluster:
            clusterNames:
            - cluster-eu-west
          weight: 50
        - targetCluster:
            clusterNames:
            - cluster-us-east
          weight: 30
        - targetCluster:
            clusterNames:
            - cluster-ap-southeast
          weight: 20
```

### Altre Soluzioni Multi-Cluster

- **ArgoCD multi-cluster**: ArgoCD supporta nativamente la gestione di applicazioni su cluster multipli da un singolo control plane. Ogni cluster viene registrato tramite `argocd cluster add` e le Application possono specificare il cluster di destinazione. Questa e' la soluzione piu' semplice quando si utilizza gia' ArgoCD per il GitOps.
- **Submariner**: progetto CNCF Sandbox che fornisce connettivita' di rete cross-cluster, permettendo ai pod e ai Service di comunicare tra cluster diversi come se fossero nello stesso cluster. Utile per architetture dove i microservizi sono distribuiti su cluster multipli.
- **Liqo**: piattaforma open-source che abilita il peering trasparente tra cluster Kubernetes, creando un "virtual cluster" unificato dove i pod possono essere schedulati su qualsiasi cluster peer in modo trasparente.
- **Cluster API**: progetto CNCF che fornisce API dichiarative per il provisioning e la gestione del ciclo di vita dei cluster Kubernetes stessi, astraendo le specificita' del provider di infrastruttura (AWS, Azure, GCP, vSphere, bare metal).

---

## Ottimizzazione dei Costi

### Il Problema del Costo in Kubernetes

Secondo un survey CNCF del 2025, il 68% delle organizzazioni che eseguono cluster Kubernetes in produzione spendono il 30-45% in piu' del necessario a causa di nodi sovradimensionati, pod inattivi e autoscaling mal configurato. L'ottimizzazione dei costi in Kubernetes richiede un approccio multilivello che coinvolge infrastruttura, configurazione dei workload e processi operativi.

### Right-Sizing dei Workload

Il right-sizing consiste nell'allineare le risorse richieste dai pod (requests e limits) all'utilizzo effettivo. L'over-provisioning e' il problema piu' comune: gli sviluppatori tendono a richiedere molte piu' risorse del necessario "per sicurezza", causando sprechi significativi.

**Strategia di right-sizing:**

1. Deployare il VPA in modalita' `Off` (solo raccomandazioni) per raccogliere dati sull'utilizzo reale
2. Analizzare le raccomandazioni del VPA dopo almeno 7 giorni di osservazione
3. Confrontare i requests attuali con l'utilizzo P95 riportato
4. Aggiornare i requests al valore P95 con un margine del 20% per gestire i picchi
5. Impostare i limits a 2-3x il valore dei requests per applicazioni con pattern di utilizzo variabile

```bash
# Visualizzare le raccomandazioni VPA
kubectl get vpa -n produzione -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.recommendation.containerRecommendations[*].target}{"\n"}{end}'

# Confrontare utilizzo attuale vs requests
kubectl top pods -n produzione --sort-by=cpu
kubectl top pods -n produzione --sort-by=memory
```

**Strumenti di analisi costi:**

- **Kubecost** (ora OpenCost, CNCF Sandbox): fornisce visibilita' granulare sui costi per namespace, deployment, label e pod. Identifica risorse inattive e over-provisioned.
- **VPA Recommender**: componente del VPA che analizza lo storico delle metriche e suggerisce valori ottimali per requests e limits.
- **Goldilocks** (Fairwinds): dashboard che visualizza le raccomandazioni VPA per tutti i deployment di un namespace, facilitando l'analisi comparativa.

### Spot Instances e Nodi Preemptible

Le spot instances (AWS), preemptible VMs (GCP) e spot VMs (Azure) offrono capacita' di calcolo a costi ridotti del 50-90% rispetto alle istanze on-demand, con la condizione che il cloud provider puo' reclaimare le istanze con un preavviso breve (tipicamente 2 minuti).

**Best practices per l'uso di spot instances:**

- Utilizzare spot instances solo per workload fault-tolerant: batch jobs, pipeline CI/CD, workload stateless con repliche multiple, ambienti di sviluppo e testing
- Mantenere i workload stateful e mission-critical su nodi on-demand
- Diversificare i tipi di istanza per ridurre il rischio di interruzione simultanea (se un tipo diventa scarso, altri restano disponibili)
- Configurare PodDisruptionBudget per garantire che le interruzioni dei nodi spot non eliminino troppe repliche contemporaneamente
- Utilizzare `topologySpreadConstraints` per distribuire le repliche tra nodi spot e on-demand

```yaml
# Toleration per nodi spot (esempio con Karpenter)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: worker-batch
spec:
  replicas: 10
  template:
    spec:
      tolerations:
      - key: "karpenter.sh/capacity-type"
        operator: "Equal"
        value: "spot"
        effect: "NoSchedule"
      nodeSelector:
        karpenter.sh/capacity-type: spot
      topologySpreadConstraints:
      - maxSkew: 1
        topologyKey: topology.kubernetes.io/zone
        whenUnsatisfiable: DoNotSchedule
        labelSelector:
          matchLabels:
            app: worker-batch
      terminationGracePeriodSeconds: 120
      containers:
      - name: worker
        image: worker:2.0
        lifecycle:
          preStop:
            exec:
              command: ["/bin/sh", "-c", "sleep 90 && kill -SIGTERM 1"]
```

### Altre Strategie di Ottimizzazione

- **Namespace ResourceQuota**: imporre limiti per namespace previene la crescita incontrollata dei costi per team o progetto
- **Pulizia risorse inattive**: automatizzare l'eliminazione di namespace di sviluppo, preview environment e risorse temporanee non piu' necessarie (strumenti come kube-janitor)
- **Scheduling bin-packing**: configurare lo scheduler per favorire il packing denso dei pod sui nodi esistenti prima di aggiungerne di nuovi, riducendo il numero di nodi necessari
- **Reserved Instances / Savings Plans**: per il baseline di capacita' prevedibile, utilizzare piani di risparmio del cloud provider con commitment annuale o triennale (risparmi del 30-60% rispetto a on-demand)
- **Storage tiering**: utilizzare classi di storage differenziate (SSD per database, HDD per log e archivi) per ottimizzare i costi di storage persistente

---

## Service Mesh

### Panoramica

Un service mesh e' un layer di infrastruttura dedicato che gestisce la comunicazione tra microservizi all'interno di un cluster Kubernetes. Fornisce funzionalita' come mutual TLS (mTLS) per la crittografia del traffico east-west, traffic management avanzato (canary deployment, circuit breaking, retry, timeout), osservabilita' (metriche, tracce distribuite, log di accesso) e controllo degli accessi tra servizi, il tutto senza richiedere modifiche al codice applicativo.

### Istio

Istio e' il service mesh piu' diffuso e maturo, con una vasta community e supporto enterprise. L'architettura tradizionale di Istio inietta un proxy Envoy come sidecar in ogni pod, che intercetta tutto il traffico di rete in ingresso e in uscita dal container applicativo.

Nel 2025, Istio ha raggiunto la General Availability della modalita' **Ambient Mesh**, un'architettura sidecarless che sostituisce i proxy per-pod con due componenti condivisi:

- **ztunnel**: agente per-nodo che gestisce L4 (TCP) con mTLS e routing semplice, condiviso tra tutti i pod del nodo
- **Waypoint proxy**: proxy Envoy opzionale per-service o per-namespace che gestisce le funzionalita' L7 (HTTP routing, header manipulation, authorization policy)

Ambient Mesh riduce drasticamente l'overhead di risorse rispetto al modello sidecar (l'8% di incremento di latenza per mTLS in ambient vs il 166% con sidecar) e semplifica le operazioni eliminando la complessita' dell'injection dei sidecar e degli upgrade coordinati.

```bash
# Installazione di Istio con profilo ambient
istioctl install --set profile=ambient --skip-confirmation

# Abilitare ambient mesh per un namespace
kubectl label namespace produzione istio.io/dataplane-mode=ambient

# Verifica dello stato del mesh
istioctl analyze -n produzione
istioctl proxy-status
```

```yaml
# VirtualService per traffic management avanzato
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: api-backend-routing
  namespace: produzione
spec:
  hosts:
  - api-backend
  http:
  - match:
    - headers:
        x-canary:
          exact: "true"
    route:
    - destination:
        host: api-backend
        subset: canary
  - route:
    - destination:
        host: api-backend
        subset: stable
      weight: 95
    - destination:
        host: api-backend
        subset: canary
      weight: 5
    retries:
      attempts: 3
      perTryTimeout: 2s
      retryOn: "5xx,reset,connect-failure"
    timeout: 10s

---
# DestinationRule per circuit breaking
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: api-backend-dr
  namespace: produzione
spec:
  host: api-backend
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        h2UpgradePolicy: DEFAULT
        http1MaxPendingRequests: 100
        http2MaxRequests: 1000
        maxRequestsPerConnection: 10
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
  subsets:
  - name: stable
    labels:
      versione: "3.2.1"
  - name: canary
    labels:
      versione: "3.3.0-beta"
```

### Cilium Service Mesh

Cilium, oltre al suo ruolo come CNI plugin, offre funzionalita' di service mesh native basate su eBPF che operano interamente nel kernel Linux, eliminando la necessita' di proxy sidecar o waypoint. Cilium ha superato 5.000 deployment in produzione nel 2025 e viene adottato da piattaforme di alto profilo.

I vantaggi principali di Cilium come service mesh sono:

- **Prestazioni**: latenza inferiore del 40-60% e memoria ridotta del 50-70% rispetto alle soluzioni basate su proxy, grazie all'elaborazione nel kernel via eBPF
- **Semplicita' operativa**: nessun sidecar da gestire, iniettare o aggiornare
- **Osservabilita' integrata**: Hubble fornisce visibilita' L3/L4/L7 sui flussi di rete, tracce distribuite e metriche senza instrumentazione aggiuntiva
- **NetworkPolicy L7**: supporto per policy che operano a livello applicativo (HTTP, gRPC, Kafka) oltre che a livello di rete

```yaml
# CiliumNetworkPolicy con filtri L7
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: api-l7-policy
  namespace: produzione
spec:
  endpointSelector:
    matchLabels:
      app: api-backend
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: web-frontend
    toPorts:
    - ports:
      - port: "8080"
        protocol: TCP
      rules:
        http:
        - method: GET
          path: "/api/v2/.*"
        - method: POST
          path: "/api/v2/orders"
          headers:
          - 'Content-Type: application/json'
  - fromEndpoints:
    - matchLabels:
        app: monitoring
    toPorts:
    - ports:
      - port: "9090"
        protocol: TCP
      rules:
        http:
        - method: GET
          path: "/metrics"
```

**Confronto sintetico dei service mesh:**

| Aspetto | Istio (Ambient) | Cilium | Linkerd |
|---------|-----------------|--------|---------|
| Architettura | ztunnel + waypoint | eBPF kernel | Sidecar (micro-proxy Rust) |
| mTLS | Nativo | Nativo (WireGuard o SPIFFE) | Nativo |
| Overhead latenza mTLS | ~8% | ~99% (benchmark 2024) | ~33% |
| Overhead CPU | Medio | Basso (miglior consumo CPU) | Basso |
| Policy L7 | Complete (Envoy-based) | HTTP, gRPC, Kafka | HTTP, gRPC |
| Traffic splitting | Completo (VirtualService) | Limitato (via Gateway API) | Completo (TrafficSplit) |
| Osservabilita' | Kiali, Prometheus, Jaeger | Hubble | Linkerd-viz |
| CNCF | Graduated | Graduated | Graduated |
| Complessita' operativa | Media | Bassa (se gia' CNI Cilium) | Bassa |

La scelta del service mesh dipende dal contesto: Istio Ambient per funzionalita' L7 complete con overhead ridotto, Cilium per prestazioni massime e integrazione nativa con il CNI, Linkerd per semplicita' operativa e basso footprint.

---

## Pattern di Troubleshooting Avanzati

### Debug Networking

I problemi di rete sono tra i piu' complessi da diagnosticare in Kubernetes. Un approccio sistematico prevede l'uso di pod di debug e strumenti specifici.

```bash
# Pod di debug con strumenti di rete completi
kubectl run netshoot --rm -it --image=nicolaka/netshoot -- /bin/bash

# Dall'interno del pod di debug:
# Verificare la risoluzione DNS
nslookup api-service.produzione.svc.cluster.local
dig +short api-service.produzione.svc.cluster.local

# Verificare la connettivita' TCP
nc -zv api-service.produzione.svc.cluster.local 8080

# Tracciare il percorso di rete
traceroute api-service.produzione.svc.cluster.local

# Analizzare il traffico (richiede container privilegiato)
tcpdump -i eth0 -nn port 8080

# Verificare le regole iptables su un nodo (via kubectl debug node)
kubectl debug node/nome-nodo -it --image=busybox -- chroot /host iptables -t nat -L -n
```

### Debug di Risorse e Scheduling

```bash
# Comprendere perche' un pod non viene schedulato
kubectl describe pod nome-pod -n namespace | grep -A 20 "Events"

# Verificare la capacita' dei nodi vs le richieste
kubectl describe nodes | grep -A 10 "Allocated resources"

# Trovare pod senza limiti di risorse (potenziale rischio)
kubectl get pods --all-namespaces -o json | \
  jq -r '.items[] | select(.spec.containers[].resources.limits == null) | .metadata.namespace + "/" + .metadata.name'

# Verificare i PDB che potrebbero bloccare il drain di un nodo
kubectl get pdb --all-namespaces

# Analizzare le priorityClass e il preemption
kubectl get priorityclass
kubectl get pods -n produzione -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.priorityClassName}{"\n"}{end}'
```

### Debug di Volumi e Storage

```bash
# Verificare lo stato dei PVC
kubectl get pvc --all-namespaces -o wide

# Diagnosticare PVC in stato Pending
kubectl describe pvc nome-pvc -n namespace

# Verificare i PV disponibili e il binding
kubectl get pv -o wide

# Controllare lo spazio disponibile nei volumi montati
kubectl exec nome-pod -n namespace -- df -h

# Verificare che i driver CSI siano funzionanti
kubectl get csidrivers
kubectl get csinodes
```

### Analisi delle Risorse del Control Plane

```bash
# Stato dei componenti del control plane
kubectl get componentstatuses 2>/dev/null || kubectl get --raw='/readyz?verbose'

# Metriche dell'API Server (latenza, rate di richieste)
kubectl get --raw /metrics | grep apiserver_request_duration

# Verifica dello stato di etcd
kubectl -n kube-system exec etcd-master -- etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health

# Dimensione del database etcd (soglia critica: >8GB)
kubectl -n kube-system exec etcd-master -- etcdctl \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint status --write-out=table

# Audit log per investigare chi ha fatto cosa
kubectl logs -n kube-system kube-apiserver-master --since=1h | grep audit
```

### Runbook di Incidenti Comuni

**Cluster non raggiungibile (API Server down):**
1. Verificare lo stato del processo kube-apiserver sul nodo control plane
2. Controllare la connettivita' di rete verso il nodo control plane
3. Verificare lo stato di etcd (e' il componente piu' critico)
4. Controllare lo spazio disco sul nodo control plane
5. Esaminare i log di sistema: `journalctl -u kubelet -f` sul nodo master

**Nodo in stato NotReady:**
1. Verificare la connettivita' di rete verso il nodo
2. Controllare lo stato del kubelet: `systemctl status kubelet`
3. Esaminare i log del kubelet: `journalctl -u kubelet --since="10 minutes ago"`
4. Verificare risorse del nodo (disco, memoria): `df -h`, `free -m`
5. Controllare i certificati del kubelet (scadenza)

**Prestazioni degradate del cluster:**
1. Controllare l'utilizzo risorse dei nodi: `kubectl top nodes`
2. Verificare la latenza dell'API Server tramite metriche Prometheus
3. Controllare lo stato di etcd e la latenza delle operazioni
4. Identificare pod con alto consumo: `kubectl top pods --all-namespaces --sort-by=cpu`
5. Verificare se ci sono molti pod in stato Pending o Evicted

---

## Best Practices

### 1. Definire Sempre Resource Requests e Limits

Ogni container deve avere `requests` e `limits` per CPU e memoria. I `requests` garantiscono le risorse minime e influenzano lo scheduling, mentre i `limits` prevengono che un singolo container monopolizzi le risorse del nodo. Utilizzare LimitRange per imporre valori predefiniti a livello di namespace.

### 2. Implementare Health Check Completi

Configurare sempre `livenessProbe`, `readinessProbe` e, per applicazioni con avvio lento, `startupProbe`. Una readinessProbe corretta previene l'invio di traffico a pod non ancora pronti. Impostare i parametri `initialDelaySeconds`, `periodSeconds` e `failureThreshold` in base al comportamento reale dell'applicazione.

### 3. Utilizzare Namespace e RBAC per l'Isolamento

Separare gli ambienti (sviluppo, staging, produzione) e i team in namespace distinti. Applicare ResourceQuota per limitare il consumo di risorse per namespace e configurare RBAC con il principio del minimo privilegio. Non utilizzare mai il namespace `default` per carichi di lavoro applicativi.

### 4. Gestire la Configurazione in Modo Dichiarativo

Mantenere tutti i manifest Kubernetes in un repository Git (approccio GitOps). Utilizzare strumenti come ArgoCD o Flux per la sincronizzazione automatica tra il repository e il cluster. Non effettuare mai modifiche manuali direttamente sul cluster (`kubectl edit` o `kubectl apply` da file locali) in ambienti di produzione.

### 5. Implementare NetworkPolicy

Adottare un approccio "deny-all" come default e aprire esplicitamente solo le comunicazioni necessarie tra i servizi. Le NetworkPolicy sono fondamentali per la sicurezza della rete interna al cluster e per limitare il raggio di una potenziale compromissione.

### 6. Utilizzare Pod Disruption Budget (PDB)

I PDB garantiscono che durante operazioni di manutenzione (drain di un nodo, aggiornamento del cluster) un numero minimo di repliche rimanga sempre disponibile.

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: api-pdb
spec:
  minAvailable: 2    # oppure maxUnavailable: 1
  selector:
    matchLabels:
      app: api-backend
```

### 7. Immagini Sicure e Aggiornate

Utilizzare sempre tag specifici e immutabili per le immagini (evitare `latest`). Preferire immagini base minimali come `alpine` o `distroless` per ridurre la superficie di attacco. Scansionare regolarmente le immagini per vulnerabilita' con strumenti come Trivy o Grype. Configurare admission controller come OPA Gatekeeper o Kyverno per impedire il deployment di immagini non conformi.

### 8. Backup e Disaster Recovery

Implementare una strategia di backup che includa: backup regolari di etcd, backup dei PersistentVolume critici, esportazione dei manifest delle risorse del cluster. Utilizzare strumenti come Velero per backup e restore dell'intero cluster o di singoli namespace. Testare periodicamente le procedure di restore.

### 9. Monitoraggio e Alerting Proattivi

Implementare monitoring a piu' livelli: metriche dell'infrastruttura (nodi, risorse), metriche dell'orchestratore (pod, deployment, scheduler), metriche applicative (latenza, error rate, throughput). Configurare alert significativi che richiedano azione (evitare alert noise) e definire runbook per ogni alert critico.

### 10. Automatizzare gli Aggiornamenti del Cluster

Pianificare aggiornamenti regolari del cluster Kubernetes (almeno per patch di sicurezza). Testare gli aggiornamenti in un ambiente di staging prima della produzione. Utilizzare il processo di upgrade graduale: aggiornare prima il control plane, poi i worker node uno alla volta con drain e uncordon. Per i servizi managed, sfruttare le funzionalita' di aggiornamento automatico quando disponibili, mantenendo una finestra di manutenzione definita.

---

## Riferimenti e Risorse

- **Documentazione ufficiale**: https://kubernetes.io/docs/
- **Kubernetes API Reference**: https://kubernetes.io/docs/reference/kubernetes-api/
- **Helm Documentation**: https://helm.sh/docs/
- **Prometheus Operator**: https://prometheus-operator.dev/
- **Kubernetes the Hard Way** (Kelsey Hightower): guida per comprendere ogni componente installando K8s manualmente

---

## Esercizi

1. **Deployment e Service Base (Base)**
   Creare un Deployment con 3 repliche di un'applicazione web (nginx o httpd). Esporre il deployment con un Service ClusterIP e un Ingress con TLS terminato. Configurare resource requests e limits, una liveness probe HTTP e una readiness probe. Verificare il rolling update modificando la versione dell'immagine.

2. **RBAC e Pod Security Standards (Intermedio)**
   Creare un namespace con Pod Security Standards a livello `restricted`. Definire un ServiceAccount dedicato con un Role che consenta solo operazioni di lettura su pod e log. Creare un RoleBinding che associ il ruolo al ServiceAccount. Verificare che un pod con `runAsNonRoot: false` o `privileged: true` venga rifiutato.

3. **NetworkPolicy e Segmentazione (Intermedio)**
   Implementare una policy default-deny per ingress e egress in un namespace. Creare tre deployment (frontend, backend, database). Scrivere NetworkPolicy che consentano: frontend → backend sulla porta 8080, backend → database sulla porta 5432, e nessun altro traffico. Verificare con `kubectl exec` e `curl`/`nc` che solo i flussi autorizzati funzionino.

4. **Helm Chart Custom con Values per Ambiente (Avanzato)**
   Creare un Helm chart per un'applicazione con template per Deployment, Service, Ingress, HPA e ConfigMap. Definire values separati per dev e prod (repliche, risorse, dominio Ingress). Implementare i test Helm (`helm test`). Deployare in due namespace distinti e verificare che le configurazioni siano corrette per ogni ambiente.

5. **Cluster Operations: Upgrade, Backup e DR (Avanzato)**
   Su un cluster di test (kind o k3s), eseguire un upgrade del control plane da una minor version alla successiva. Installare Velero e configurare un backup schedulato dell'intero cluster su un bucket S3/GCS. Simulare un disaster eliminando un namespace con workload attivi, poi eseguire il restore con Velero e verificare che tutte le risorse siano ripristinate correttamente.

---

## Letture e Riferimenti

**Documentazione ufficiale**

- Kubernetes Documentation — https://kubernetes.io/docs/home/ (consultato: 2026-05-24)
- Kubernetes API Reference v1.30 — https://kubernetes.io/docs/reference/kubernetes-api/ (consultato: 2026-05-24)
- Helm Documentation — https://helm.sh/docs/ (consultato: 2026-05-24)
- Kyverno Policy Engine — https://kyverno.io/docs/ (consultato: 2026-05-24)
- OPA Gatekeeper — https://open-policy-agent.github.io/gatekeeper/website/docs/ (consultato: 2026-05-24)
- Velero Backup & Restore — https://velero.io/docs/ (consultato: 2026-05-24)
- Prometheus Operator — https://prometheus-operator.dev/docs/ (consultato: 2026-05-24)
- Gateway API — https://gateway-api.sigs.k8s.io/ (consultato: 2026-05-24)

**Libri consigliati**

- *Kubernetes in Action* — Marko Lukša (Manning, 2ª edizione)
- *Production Kubernetes* — Josh Rosso, Rich Lander, Alex Brand, John Harris (O'Reilly)
- *Kubernetes Patterns* — Bilgin Ibryam, Roland Huß (O'Reilly, 2ª edizione)

---

## Riferimenti Incrociati

| Modulo | Titolo | Relazione |
|--------|--------|-----------|
| [06](06-docker-avanzato.md) | Docker Avanzato | Build di immagini, container runtime, prerequisito per K8s |
| [04](04-infrastructure-as-code.md) | Infrastructure as Code | Provisioning cluster con Terraform, Helm provider |
| [08](08-monitoring-observability.md) | Monitoring e Observability | Prometheus, Grafana, metriche cluster e applicative |
| [09](09-service-mesh.md) | Service Mesh | Istio, Linkerd, mTLS e traffic management su K8s |
| [13](13-sicurezza-piattaforme.md) | Sicurezza Piattaforme | Pod Security, image scanning, admission control |
| [22](22-multi-tenancy-isolation.md) | Multi-Tenancy e Isolation | Namespace isolation, resource quotas, vCluster |

---

## Glossario

| Termine | Definizione |
|---------|------------|
| **Control Plane** | Insieme dei componenti che gestiscono lo stato del cluster: API server, etcd, scheduler, controller manager |
| **DaemonSet** | Risorsa che garantisce l'esecuzione di un pod su ogni nodo (o su un sottoinsieme selezionato) del cluster |
| **Deployment** | Risorsa dichiarativa che gestisce il ciclo di vita dei pod con rolling update e rollback |
| **etcd** | Database key-value distribuito che archivia tutto lo stato del cluster Kubernetes |
| **Helm** | Package manager per Kubernetes che gestisce il deployment di applicazioni tramite chart riutilizzabili |
| **Ingress** | Risorsa che configura il routing HTTP/HTTPS esterno verso i Service interni del cluster |
| **Kyverno** | Policy engine nativo Kubernetes per validare, mutare e generare risorse tramite policy YAML |
| **NetworkPolicy** | Risorsa che definisce regole firewall a livello di pod per controllare il traffico di rete |
| **Pod** | Unità minima di deployment in Kubernetes, composta da uno o più container con rete e storage condivisi |
| **RBAC** | Sistema di autorizzazione che assegna permessi tramite Role, ClusterRole e relativi Binding |
| **StatefulSet** | Risorsa per workload stateful che garantisce identità di rete stabile e storage persistente per ogni pod |
| **Service** | Astrazione che espone un gruppo di pod come endpoint di rete stabile con bilanciamento del carico |
| **Taint/Toleration** | Meccanismo per impedire o consentire lo scheduling di pod su nodi specifici |
| **Velero** | Strumento per backup, restore e migrazione di risorse e volumi persistenti del cluster |
| **Worker Node** | Nodo del cluster che esegue i pod applicativi, gestito da kubelet e kube-proxy |
- **CNCF Landscape**: https://landscape.cncf.io/ - panoramica dell'ecosistema cloud-native
