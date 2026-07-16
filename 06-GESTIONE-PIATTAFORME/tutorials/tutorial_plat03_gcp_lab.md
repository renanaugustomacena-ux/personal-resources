# Tutorial: Google Cloud Platform — Fondamenti, GKE e Cloud Run — Lab Pratico

> **Documento di riferimento:** `03-cloud-gcp.md`
> **Dominio:** Gestione Piattaforme — Cloud Provider GCP
> **Ambito:** Architettura GCP (Organization/Project/Folder), IAM con Service Account e Workload Identity, VPC globale, Cloud Storage con emulatore locale (fake-gcs-server), Pub/Sub emulator, GKE Autopilot, Cloud Run serverless, BigQuery fondamenti, Cloud Monitoring
> **Durata lab:** 5-6 ore
> **Livello:** Intermedio — richiede conoscenza base di Kubernetes e networking
> **Prerequisiti:** gcloud CLI, Docker Engine 29.x, Python 3.10+, account GCP Free Tier (opzionale — sezioni emulabili localmente sono indicate)
> **Ambiente:** fake-gcs-server (emulatore Cloud Storage), gcloud Pub/Sub emulator, gcloud CLI in modalità reference per il resto

---

## Lab Environment Setup

```bash
# === VERIFICA PREREQUISITI GCP LAB ===
echo "=== CHECK PREREQUISITI ==="

# gcloud CLI
gcloud --version 2>/dev/null | head -1 && echo "[OK] gcloud CLI disponibile" || {
  echo "[FAIL] Installare Google Cloud CLI"
  echo "  Linux: curl https://sdk.cloud.google.com | bash"
  echo "  Windows: https://cloud.google.com/sdk/docs/install"
}

# Docker
docker --version && echo "[OK] Docker disponibile" || echo "[FAIL] Docker richiesto"

# Python 3.10+ (per Cloud Functions e test)
python3 --version | grep -E "3\.(1[0-9])" && echo "[OK] Python >= 3.10" || \
  echo "[WARN] Raccomandato Python 3.10+"

# kubectl (per GKE)
kubectl version --client 2>/dev/null | head -1 && \
  echo "[OK] kubectl disponibile" || echo "[INFO] kubectl opzionale (sezione GKE)"

echo ""
echo "=== SETUP DIRECTORY LAB ==="
mkdir -p ~/gcp-lab/{storage,pubsub,cloudrun,gke,terraform}
cd ~/gcp-lab

echo "[OK] Directory lab: ~/gcp-lab"
```

### Architettura del Lab

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         GCP LAB — AMBIENTE                               │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  EMULATORI LOCALI (Docker)                                     │     │
│  │                                                                 │     │
│  │  fake-gcs-server :4443  (emulatore Cloud Storage)             │     │
│  │  gcloud pubsub emulator :8085 (emulatore Pub/Sub)             │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │  GCP FREE TIER / REFERENCE (account GCP reale — opzionale)    │     │
│  │                                                                 │     │
│  │  GKE Autopilot    — cluster Kubernetes senza gestire nodi     │     │
│  │  Cloud Run        — container serverless                       │     │
│  │  BigQuery sandbox — analisi dati 1TB/mese gratuiti            │     │
│  │  Cloud Monitoring — metriche e alert                           │     │
│  └─────────────────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────────────────┘

NOTA: GCP offre 300 USD di crediti per 90 giorni nel Free Trial.
      GKE Autopilot: cluster gratuito (1 cluster Autopilot per account),
      si paga solo per i pod in esecuzione.
```

### Avvio Emulatori GCP Locali

```bash
cd ~/gcp-lab

cat > compose.yaml << 'EOF'
name: "gcp-lab"

services:
  # Emulatore Cloud Storage (GCS) — compatibile con la libreria google-cloud-storage
  fake-gcs:
    image: fsouza/fake-gcs-server:1.51
    container_name: fake-gcs-server
    command: -scheme http -port 4443 -public-host localhost
    ports:
      - "4443:4443"
    volumes:
      - ./storage-data:/data
    restart: unless-stopped

  # Emulatore Pub/Sub — ufficiale Google
  pubsub-emulator:
    image: gcr.io/google.com/cloudsdktool/cloud-sdk:latest
    container_name: pubsub-emulator
    command: gcloud beta emulators pubsub start --host-port=0.0.0.0:8085 --project=lab-project-001
    ports:
      - "8085:8085"
    restart: unless-stopped

EOF

docker compose up -d

echo "Attendo emulatori..."
sleep 10

# Verificare fake-gcs
curl -s http://localhost:4443/ | grep -q "fake-gcs" && \
  echo "[OK] fake-gcs-server operativo" || echo "[INFO] fake-gcs in avvio..."

echo "[OK] Emulatori GCP avviati"

# Configurare variabili di ambiente per gli emulatori
export STORAGE_EMULATOR_HOST=http://localhost:4443
export PUBSUB_EMULATOR_HOST=localhost:8085

# gcloud login (opzionale — solo per risorse GCP reali)
# gcloud auth login
# gcloud config set project tuo-project-id
```

---

## PART A: FONDAMENTI — La Filosofia GCP

> Google ha costruito le tecnologie fondamentali del cloud computing molto prima di
> offrirle come servizio commerciale. Kubernetes nasce da Borg (il sistema di
> orchestrazione interno di Google). BigQuery nasce da Dremel. Pub/Sub nasce da
> un sistema interno per lo streaming di eventi. GCP è, in un certo senso, la
> versione commerciale dell'infrastruttura che fa girare Google Search, YouTube
> e Gmail. Questo porta un vantaggio concreto: le tecnologie sono state testate
> a scala enorme prima di arrivare al pubblico.

---

### Concetto A1: Gerarchia Organization → Project

> **Analogia.** GCP usa una gerarchia a tre livelli: Organization (la holding aziendale),
> Folder (le divisioni aziendali), Project (i singoli team o applicazioni).
> È come un'azienda con più filiali: la sede centrale (Organization) stabilisce
> le regole generali valide per tutti; le filiali (Folder) possono avere regole
> aggiuntive; ogni reparto di ogni filiale (Project) è l'unità operativa
> dove girano le risorse. Ogni quota, ogni fattura, ogni set di permessi IAM
> è associato a un Project specifico.

```
GERARCHIA GCP (diversa da AWS e Azure):

Organization: acme-corporation.com
  ├── Folder: produzione
  │     ├── Project: prod-webapp-20240101      ← tutto in prod-webapp
  │     │     ├── GKE Cluster
  │     │     ├── Cloud SQL
  │     │     └── Cloud Storage bucket
  │     └── Project: prod-data-platform-2024   ← team data
  │           ├── BigQuery dataset
  │           └── Pub/Sub topics
  ├── Folder: non-produzione
  │     ├── Project: dev-team-2024
  │     └── Project: qa-team-2024
  └── Folder: infrastruttura-condivisa
        └── Project: network-hub-2024
              └── Shared VPC host project

DIFFERENZE DA AWS/AZURE:
  AWS:   Account = unit of billing + isolation
  Azure: Subscription + Resource Group
  GCP:   Project = unit of billing + IAM + quota

VPC IN GCP — DIFFERENZA FONDAMENTALE:
  AWS/Azure: VPC è REGIONALE (ogni regione ha la sua VPC)
  GCP: VPC è GLOBALE (una VPC attraversa tutte le regioni!)
  → Puoi avere VM in Europe e US-West nella stessa VPC,
    che comunicano privatamente senza VPN
```

```bash
# Configurazione gcloud locale
# Lista dei componenti installati
gcloud components list 2>/dev/null | head -20 || \
  echo "[INFO] gcloud non disponibile — installare Google Cloud CLI"

# Autenticazione (interattiva — richiede browser)
cat << 'AUTH'
# LOGIN CON ACCOUNT GCP:
gcloud auth login

# Creare un progetto di lab
gcloud projects create lab-platform-tutorial \
  --name="Platform Lab Tutorial" \
  --set-as-default

# Abilitare le API necessarie
gcloud services enable \
  container.googleapis.com \      # GKE
  run.googleapis.com \            # Cloud Run
  storage.googleapis.com \        # Cloud Storage
  pubsub.googleapis.com \         # Pub/Sub
  bigquery.googleapis.com \       # BigQuery
  monitoring.googleapis.com \     # Cloud Monitoring
  logging.googleapis.com          # Cloud Logging

# Verificare progetto attivo
gcloud config get-value project
AUTH
```

---

### Concetto A2: IAM GCP — Service Account e Workload Identity

> **Analogia.** In GCP, un Service Account è come un dipendente robot — ha una
> identità, può avere permessi, può essere "indossato" da risorse come VM o pod.
> Il problema storico era che questo robot aveva delle chiavi fisiche (file JSON
> con chiave privata) che potevano essere rubate. Workload Identity risolve
> il problema: il robot non ha più chiavi fisiche, ma un documento d'identità
> elettronico verificato da GCP in tempo reale. Nessun file da gestire,
> nessuna chiave da ruotare.

```bash
cat << 'IAM_GUIDE'
═══════════════════════════════════════════════════════════════
IAM GCP — CONCETTI CHIAVE
═══════════════════════════════════════════════════════════════

TIPI DI IDENTITÀ:
  google Account:      utente@gmail.com (persona fisica)
  Service Account:     nome@project.iam.gserviceaccount.com (app/robot)
  Google Group:        gruppo@googlegroups.com
  Domain:              tutta la directory Workspace acme.com

RUOLI PREDEFINITI (simili ad AWS):
  roles/owner         = tutto, incluso IAM
  roles/editor        = tutte le risorse, no IAM
  roles/viewer        = sola lettura
  roles/storage.objectAdmin    = gestire oggetti GCS
  roles/container.developer    = gestire workload GKE
  roles/bigquery.dataEditor    = scrivere in BigQuery

REGOLA ORO:
  - No chiavi Service Account per risorse DENTRO GCP
  - Usare Workload Identity (GKE) o Application Default Credentials (ADC)
  - Chiavi SA solo per sistemi esterni a GCP (on-prem, altri cloud)

SERVICE ACCOUNT — MODALITÀ D'USO:
  VM: associa SA alla VM (come EC2 Instance Profile)
  GKE: Workload Identity Federation (SA K8s → SA GCP)
  Cloud Run: SA assegnato alla revisione del servizio
  GitHub Actions: Workload Identity Federation (GitHub → SA GCP)

WORKLOAD IDENTITY FEDERATION (GKE):
  [Pod K8s] → ha K8s Service Account
  [K8s SA]  → è annotato con: iam.gke.io/gcp-service-account=app-sa@project.iam.gserviceaccount.com
  [GCP SA]  → ha policy: roles/iam.workloadIdentityUser per il K8s SA
  → Il pod ottiene token GCP senza file JSON
═══════════════════════════════════════════════════════════════
IAM_GUIDE

# Comandi IAM con account GCP reale
cat << 'IAM_COMMANDS'
# Creare un Service Account per l'applicazione
gcloud iam service-accounts create app-backend-sa \
  --project=lab-platform-tutorial \
  --description="Service Account per il backend dell'applicazione" \
  --display-name="App Backend SA"

# Assegnare permessi minimi (least privilege)
gcloud projects add-iam-policy-binding lab-platform-tutorial \
  --member="serviceAccount:app-backend-sa@lab-platform-tutorial.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer" \    # sola lettura su GCS
  --condition="None"

# Workload Identity per GKE
gcloud iam service-accounts add-iam-policy-binding \
  app-backend-sa@lab-platform-tutorial.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:lab-platform-tutorial.svc.id.goog[default/app-backend-k8s-sa]"

# Audit: chi ha quali permessi
gcloud projects get-iam-policy lab-platform-tutorial \
  --format="table(bindings.role,bindings.members)"
IAM_COMMANDS
```

---

## PART B: CLOUD STORAGE — CON EMULATORE LOCALE

### Esercizio B1: Operazioni Cloud Storage (fake-gcs-server)

```bash
cd ~/gcp-lab/storage

# Installare libreria Python Cloud Storage
pip3 install --quiet google-cloud-storage 2>/dev/null || \
  pip install --quiet google-cloud-storage 2>/dev/null

# Script Python per usare Cloud Storage con l'emulatore
cat > gcs_demo.py << 'PYTHON'
"""
Demo Cloud Storage con fake-gcs-server locale
La stessa logica funziona con GCP reale (rimuovendo client_options)
"""
import os
from google.cloud import storage
from google.auth.credentials import AnonymousCredentials

EMULATOR_HOST = os.environ.get("STORAGE_EMULATOR_HOST", "http://localhost:4443")
PROJECT_ID = "lab-project-001"

def get_client():
    """Client che usa l'emulatore locale (o GCP se STORAGE_EMULATOR_HOST non è settato)."""
    if "STORAGE_EMULATOR_HOST" in os.environ:
        # Modalità emulatore
        return storage.Client(
            credentials=AnonymousCredentials(),
            project=PROJECT_ID,
            client_options={"api_endpoint": EMULATOR_HOST}
        )
    # Modalità GCP reale (usa Application Default Credentials)
    return storage.Client(project=PROJECT_ID)


def setup_bucket(client, bucket_name):
    """Crea o ottiene un bucket con configurazione sicura."""
    try:
        bucket = client.get_bucket(bucket_name)
        print(f"[INFO] Bucket {bucket_name} già esistente")
    except Exception:
        bucket = client.create_bucket(bucket_name, location="europe-west8")
        print(f"[OK] Bucket creato: gs://{bucket_name}")
    return bucket


def upload_file(bucket, source_path: str, destination_name: str, content_type: str):
    """Carica un file nel bucket."""
    blob = bucket.blob(destination_name)
    blob.content_type = content_type
    
    with open(source_path, "rb") as f:
        blob.upload_from_file(f)
    
    print(f"[OK] Caricato: gs://{bucket.name}/{destination_name}")
    return blob


def download_file(bucket, blob_name: str, destination_path: str):
    """Scarica un file dal bucket."""
    blob = bucket.blob(blob_name)
    blob.download_to_filename(destination_path)
    print(f"[OK] Scaricato: {destination_path}")


def list_blobs(bucket, prefix: str = ""):
    """Lista gli oggetti nel bucket."""
    blobs = list(bucket.list_blobs(prefix=prefix))
    print(f"[INFO] Oggetti in gs://{bucket.name}/{prefix}:")
    for blob in blobs:
        print(f"  {blob.name} ({blob.size} bytes)")
    return blobs


def generate_signed_url(blob, expiration_minutes: int = 60):
    """
    Genera un URL firmato per accesso temporaneo.
    Nota: con emulatore usa URL non firmati.
    """
    # In GCP reale: blob.generate_signed_url(expiration=datetime.timedelta(minutes=expiration_minutes))
    print(f"[INFO] URL oggetto: {blob.public_url}")
    return blob.public_url


if __name__ == "__main__":
    import json
    
    client = get_client()
    bucket = setup_bucket(client, "lab-artifacts-gcp")
    
    # Creare file di test
    with open("/tmp/gcp-manifest.json", "w") as f:
        json.dump({
            "version": "1.0.0",
            "platform": "gcp",
            "region": "europe-west8",
            "build": "20260716"
        }, f, indent=2)
    
    # Upload
    blob = upload_file(
        bucket,
        "/tmp/gcp-manifest.json",
        "releases/v1.0.0/manifest.json",
        "application/json"
    )
    
    # Lista
    list_blobs(bucket)
    
    # Download e verifica
    download_file(bucket, "releases/v1.0.0/manifest.json", "/tmp/gcp-downloaded.json")
    with open("/tmp/gcp-downloaded.json") as f:
        data = json.load(f)
    print(f"[OK] Verifica download: versione={data['version']} regione={data['region']}")
PYTHON

# Eseguire la demo
python3 gcs_demo.py && echo "[OK] Demo Cloud Storage completata"

# Listare i bucket via API REST dell'emulatore
curl -s "http://localhost:4443/storage/v1/b?project=lab-project-001" | \
  python3 -c "import json,sys; d=json.load(sys.stdin); print([b['name'] for b in d.get('items',[])])"
```

---

## PART C: PUB/SUB — MESSAGGISTICA ASINCRONA

### Esercizio C1: Topic, Subscription e Consumer

> **Analogia.** Pub/Sub è come una bacheca delle comunicazioni aziendali.
> Chi pubblica (publisher) appende avvisi alla bacheca (topic) senza sapere
> chi li leggerà. Chi è interessato si "abbona" alla bacheca (subscription)
> e riceve automaticamente tutti i nuovi avvisi. Questo disaccoppia mittente
> e ricevente: il publisher non aspetta che il consumer legga il messaggio,
> e il consumer può elaborare i messaggi quando vuole (entro 7 giorni).

```bash
cd ~/gcp-lab/pubsub

# Configurare l'emulatore Pub/Sub
export PUBSUB_EMULATOR_HOST=localhost:8085

# Installare libreria
pip3 install --quiet google-cloud-pubsub 2>/dev/null

cat > pubsub_demo.py << 'PYTHON'
"""Demo Pub/Sub con emulatore locale."""
import os, json, time
from concurrent.futures import TimeoutError
from google.cloud import pubsub_v1

PROJECT_ID = "lab-project-001"
TOPIC_ID = "artifact-events"
SUBSCRIPTION_ID = "artifact-events-processor"


def create_topic_and_subscription():
    """Crea topic e subscription."""
    publisher = pubsub_v1.PublisherClient()
    subscriber = pubsub_v1.SubscriberClient()
    
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
    sub_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)
    
    # Creare topic
    try:
        topic = publisher.create_topic(request={"name": topic_path})
        print(f"[OK] Topic creato: {topic.name}")
    except Exception as e:
        print(f"[INFO] Topic già esistente: {e}")
    
    # Creare subscription con dead-letter policy
    try:
        dlq_path = publisher.topic_path(PROJECT_ID, f"{TOPIC_ID}-dlq")
        try:
            publisher.create_topic(request={"name": dlq_path})
        except Exception:
            pass
        
        subscription = subscriber.create_subscription(request={
            "name": sub_path,
            "topic": topic_path,
            "ack_deadline_seconds": 60,
            "dead_letter_policy": {
                "dead_letter_topic": dlq_path,
                "max_delivery_attempts": 5
            },
            "retry_policy": {
                "minimum_backoff": {"seconds": 10},
                "maximum_backoff": {"seconds": 300}
            }
        })
        print(f"[OK] Subscription creata: {subscription.name}")
    except Exception as e:
        print(f"[INFO] Subscription già esistente: {e}")
    
    return publisher, subscriber, topic_path, sub_path


def publish_messages(publisher, topic_path, count=5):
    """Pubblica messaggi di eventi."""
    print(f"\n[INFO] Pubblicando {count} messaggi...")
    
    for i in range(count):
        message_data = json.dumps({
            "event_type": "artifact.uploaded",
            "artifact_id": f"artifact-{i+1:04d}",
            "version": f"1.{i}.0",
            "timestamp": time.time()
        })
        
        # Gli attributi sono metadati chiave-valore per il routing
        future = publisher.publish(
            topic_path,
            data=message_data.encode("utf-8"),
            artifact_type="docker-image",    # attributo per filtering
            environment="lab"
        )
        message_id = future.result()  # blocca fino alla conferma
        print(f"  Pubblicato: ID={message_id} artifact={i+1}")
    
    print(f"[OK] {count} messaggi pubblicati")


def consume_messages(subscriber, sub_path, timeout=10):
    """Consuma messaggi dalla subscription."""
    received = []
    
    def callback(message):
        data = json.loads(message.data.decode("utf-8"))
        print(f"  Ricevuto: {data['event_type']} - {data['artifact_id']}")
        received.append(data)
        message.ack()  # conferma ricezione (rimuove dalla coda)
    
    streaming_pull = subscriber.subscribe(sub_path, callback=callback)
    print(f"\n[INFO] In ascolto per {timeout} secondi...")
    
    try:
        streaming_pull.result(timeout=timeout)
    except TimeoutError:
        streaming_pull.cancel()
        streaming_pull.result()
    
    return received


if __name__ == "__main__":
    publisher, subscriber, topic_path, sub_path = create_topic_and_subscription()
    publish_messages(publisher, topic_path, count=3)
    time.sleep(1)
    received = consume_messages(subscriber, sub_path, timeout=10)
    print(f"\n[OK] Ricevuti e processati: {len(received)} messaggi")
PYTHON

python3 pubsub_demo.py && echo "[OK] Demo Pub/Sub completata"
```

---

## PART D: GKE AUTOPILOT — KUBERNETES SENZA GESTIRE I NODI

> **Analogia.** GKE Standard è come noleggiare una flotta di camion: sei tu che
> decidi quanti camion, di che taglia, dove parcheggiarli, chi fa manutenzione
> (anche se Google aiuta). GKE Autopilot è come affidarsi a un servizio di
> spedizioni: dici solo "ho bisogno di trasportare X" e il servizio si occupa
> di tutto — camion, autisti, percorso, manutenzione. Paghi per il carico
> trasportato, non per il camion fermo in garage.

---

### Esercizio D1: GKE Autopilot — Cluster e Deployment

```bash
cat << 'GKE_GUIDE'
═══════════════════════════════════════════════════════════════
GKE AUTOPILOT — DIFFERENZE DA GKE STANDARD
═══════════════════════════════════════════════════════════════

GKE STANDARD:
  + Controllo totale sui nodi (tipo, dimensione, OS, GPU)
  + Workload privilegiati (DaemonSet su nodi dedicati)
  - Devi gestire nodi (patching, dimensionamento)
  - Paghi per i nodi, non per i pod

GKE AUTOPILOT (preferito per la maggior parte dei casi):
  + Nessun nodo da gestire (node pool gestiti da Google)
  + Paghi solo per CPU/RAM/Storage richiesti dai pod
  + Aggiornamento automatico di Kubernetes
  + Conformità automatica CIS Benchmark e SLSA
  - Nessun DaemonSet (Google ne gestisce propri)
  - Nessun pod privilegiato (security policy più strict)
  - Nessun accesso SSH ai nodi

COSTO (luglio 2026):
  Standard: 0.10 USD/ora per il management fee + costo nodi
  Autopilot: nessun management fee + 0.0445 USD/vCPU/ora + 0.00485 USD/GiB-RAM/ora
  → Autopilot più economico per carichi intermittenti/piccoli

VINCOLI AUTOPILOT:
  - Pod devono avere request CPU/memory (obbligatorio)
  - Nessun privileged container
  - Nessun hostPath volume (no accesso filesystem host)
  - Nessun NET_ADMIN capability
═══════════════════════════════════════════════════════════════
GKE_GUIDE

# Creare cluster GKE Autopilot (con account GCP reale)
cat << 'GKE_COMMANDS'
# Creare cluster Autopilot (gratuito 1 cluster/account)
gcloud container clusters create-auto lab-autopilot-cluster \
  --region=europe-west8 \
  --project=lab-platform-tutorial \
  --release-channel=regular \          # aggiornamenti stabili ogni ~2 mesi
  --workload-pool=lab-platform-tutorial.svc.id.goog  # Workload Identity

# Ottenere credenziali
gcloud container clusters get-credentials lab-autopilot-cluster \
  --region=europe-west8 \
  --project=lab-platform-tutorial

# Verifica
kubectl get nodes
# → GKE Autopilot non mostra nodi fissi — i nodi sono effimeri e creati
# automaticamente per accogliere i pod

kubectl get node --show-labels | head -3
GKE_COMMANDS

# Manifest per Autopilot (devono avere resource requests)
mkdir -p ~/gcp-lab/gke

cat > ~/gcp-lab/gke/workload-identity-sa.yaml << 'EOF'
# Service Account K8s con Workload Identity
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-backend-k8s-sa
  namespace: default
  annotations:
    # Collegamento al Service Account GCP tramite Workload Identity
    iam.gke.io/gcp-service-account: app-backend-sa@lab-platform-tutorial.iam.gserviceaccount.com
EOF

cat > ~/gcp-lab/gke/deployment-autopilot.yaml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-api
  namespace: default
  labels:
    app: backend-api
    version: "1.0.0"
    managed-by: kubectl
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend-api
  template:
    metadata:
      labels:
        app: backend-api
    spec:
      serviceAccountName: app-backend-k8s-sa  # Usa Workload Identity
      
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        seccompProfile:
          type: RuntimeDefault
      
      containers:
      - name: api
        image: europe-west8-docker.pkg.dev/lab-platform-tutorial/app-repo/backend:latest
        ports:
        - containerPort: 8080
        
        # OBBLIGATORIO in GKE Autopilot
        resources:
          requests:
            cpu: "500m"           # 0.5 vCPU
            memory: "512Mi"       # 512 MiB RAM
            ephemeral-storage: "1Gi"
          limits:
            cpu: "1000m"
            memory: "1Gi"
            ephemeral-storage: "2Gi"
        
        env:
        - name: GCS_BUCKET
          value: "lab-artifacts-gcp"
        - name: GOOGLE_CLOUD_PROJECT
          value: "lab-platform-tutorial"
        
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]        # Autodrop in Autopilot — obbligatorio
          readOnlyRootFilesystem: true
        
        readinessProbe:
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 10
        
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 20
---
apiVersion: v1
kind: Service
metadata:
  name: backend-api-svc
spec:
  selector:
    app: backend-api
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
---
# HPA: scaling automatico basato su CPU
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-api
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

echo "[OK] Manifest GKE Autopilot creati in ~/gcp-lab/gke/"
echo "[INFO] Applicare con: kubectl apply -f ~/gcp-lab/gke/ (richiede cluster GKE)"
```

---

## PART E: CLOUD RUN — CONTAINER SERVERLESS

> **Analogia.** Cloud Run è come un cameriere a chiamata per un container.
> Hai un container Docker che serve richieste HTTP. Cloud Run lo tiene "ibernato"
> quando non c'è traffico (scala a zero), lo sveglia in pochi secondi quando
> arriva una richiesta, gestisce automaticamente lo scaling (da 0 a migliaia
> di istanze), e lo riiberna dopo. Non paghi nulla quando non c'è traffico.
> Perfetto per API, webhook, microservizi a traffico intermittente.

---

### Esercizio E1: Deploy su Cloud Run

```bash
cd ~/gcp-lab/cloudrun

# App Python per Cloud Run (serve richieste HTTP)
cat > app.py << 'PYTHON'
"""App Python minimale per Cloud Run."""
import os
import json
import logging
from flask import Flask, jsonify, request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/healthz')
def health():
    return jsonify({"status": "ok", "version": "1.0.0"})

@app.route('/api/process', methods=['POST'])
def process():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Body JSON richiesto"}), 400
    
    logger.info("Processing request: %s", json.dumps(data))
    
    # Elaborazione (simulata)
    result = {
        "processed": True,
        "input": data,
        "project": os.environ.get("GOOGLE_CLOUD_PROJECT", "local"),
        "service": os.environ.get("K_SERVICE", "local")
    }
    
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
PYTHON

cat > Dockerfile << 'EOF'
FROM python:3.12-slim

# Non root user
RUN useradd -m -u 1000 appuser

WORKDIR /app
RUN pip install --no-cache-dir flask==3.1.0 gunicorn==23.0.0

COPY app.py .

USER 1000
EXPOSE 8080

# Cloud Run usa PORT env var per la porta
CMD exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 2 app:app
EOF

# Build locale per test
docker build -t cloud-run-demo:latest .

# Test locale
docker run -d -p 18080:8080 -e PORT=8080 --name cloud-run-test cloud-run-demo:latest
sleep 2
curl -sf http://localhost:18080/healthz | python3 -m json.tool && echo "[OK] App locale funziona"
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"artifact": "my-app", "version": "1.0.0"}' \
  http://localhost:18080/api/process | python3 -m json.tool

docker stop cloud-run-test && docker rm cloud-run-test

# Deploy su Cloud Run (con account GCP)
cat << 'DEPLOY_COMMANDS'
# Deploy con gcloud (costruisce e pubblica automaticamente su Artifact Registry)
gcloud run deploy backend-api \
  --source . \
  --region europe-west8 \
  --platform managed \
  --allow-unauthenticated \                 # per API pubbliche (rimuovere per API private)
  --service-account=app-backend-sa@lab-platform-tutorial.iam.gserviceaccount.com \
  --set-env-vars GOOGLE_CLOUD_PROJECT=lab-platform-tutorial \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \                      # scala a zero = zero costi a idle
  --max-instances 10 \
  --concurrency 80 \                       # 80 richieste simultanee per istanza
  --timeout 30s \
  --project lab-platform-tutorial

# Vedere l'URL del servizio
gcloud run services describe backend-api \
  --region europe-west8 \
  --format="value(status.url)"

# Testare il servizio deployato
SERVICE_URL=$(gcloud run services describe backend-api \
  --region europe-west8 \
  --format="value(status.url)")

curl -sf "$SERVICE_URL/healthz" | python3 -m json.tool
DEPLOY_COMMANDS

echo "[OK] Cloud Run demo completata"
```

---

## PART F: BIGQUERY — ANALISI DATI

> **Analogia.** BigQuery è come avere una biblioteca infinita con un bibliotecario
> ultra-veloce. Invece di dover cercare libro per libro (query su un database
> tradizionale, limitato da RAM e I/O), BigQuery usa migliaia di "lettori" in
> parallelo che scansionano tutti i libri contemporaneamente. Puoi analizzare
> terabyte di dati in pochi secondi, senza gestire server, indici o vacuum.
> Il prezzo? Paghi per i dati scansionati (5 USD/TB), non per il tempo di query.

---

### Esercizio F1: BigQuery Fondamenti

```bash
cat << 'BQ_GUIDE'
═══════════════════════════════════════════════════════════════
BIGQUERY — SQL PER ANALISI DI GRANDI DATASET
═══════════════════════════════════════════════════════════════

CONCETTI CHIAVE:
  Dataset    = schema (gruppo di tabelle)
  Table      = tabella dati (flat o nested)
  View       = query salvata come tabella virtuale
  Job        = query/load/extract in esecuzione
  Slot       = unità di CPU BigQuery (on-demand: 2000 slot/progetto)

SQL BIGQUERY (dialetto Standard SQL):

-- Query base: performance delle ultime 24 ore
SELECT
  FORMAT_TIMESTAMP('%Y-%m-%d %H:00', TIMESTAMP_TRUNC(timestamp, HOUR)) AS hour,
  COUNT(*) AS total_requests,
  COUNTIF(status_code >= 500) AS errors,
  ROUND(COUNTIF(status_code >= 500) / COUNT(*) * 100, 2) AS error_rate_pct,
  ROUND(AVG(latency_ms), 1) AS avg_latency_ms,
  APPROX_QUANTILES(latency_ms, 100)[OFFSET(99)] AS p99_latency_ms
FROM `lab-platform-tutorial.monitoring.api_requests`
WHERE TIMESTAMP_TRUNC(timestamp, DAY) = CURRENT_DATE()
GROUP BY hour
ORDER BY hour DESC

-- Query su tabella partizionata per data (efficiente → no full scan)
SELECT *
FROM `lab-platform-tutorial.logs.application`
WHERE DATE(_PARTITIONTIME) = "2026-07-16"
  AND severity = "ERROR"
  AND json_payload.service = "backend-api"
LIMIT 1000

-- Partizione + clustering per performance ottimale
CREATE TABLE IF NOT EXISTS `lab-platform-tutorial.monitoring.api_requests`
PARTITION BY DATE(timestamp)
CLUSTER BY service, status_code
OPTIONS (
  partition_expiration_days = 90,
  require_partition_filter = true    -- forza a specificare la data nella WHERE
) AS
SELECT
  CURRENT_TIMESTAMP() AS timestamp,
  "backend-api" AS service,
  200 AS status_code,
  45 AS latency_ms
WHERE 1=0  -- tabella vuota

-- Materializzare una view per query frequenti
CREATE OR REPLACE MATERIALIZED VIEW `lab.monitoring.daily_summary`
OPTIONS (enable_refresh = true, refresh_interval_minutes = 60)
AS
SELECT
  DATE(timestamp) AS date,
  service,
  COUNT(*) AS total,
  COUNTIF(status_code >= 500) AS errors
FROM `lab.monitoring.api_requests`
GROUP BY 1, 2

-- BigQuery ML: creare un modello senza uscire da SQL
CREATE OR REPLACE MODEL `lab.ml.request_volume_forecast`
OPTIONS (
  model_type = 'ARIMA_PLUS',
  time_series_timestamp_col = 'timestamp',
  time_series_data_col = 'request_count',
  auto_arima = TRUE,
  data_frequency = 'HOURLY',
  horizon = 24   -- previsione 24 ore future
) AS
SELECT
  TIMESTAMP_TRUNC(timestamp, HOUR) AS timestamp,
  COUNT(*) AS request_count
FROM `lab.monitoring.api_requests`
GROUP BY 1
ORDER BY 1

═══════════════════════════════════════════════════════════════
BQ_GUIDE

# Comandi gcloud per BigQuery
cat << 'BQ_COMMANDS'
# Creare dataset
bq mk --dataset \
  --location=EU \
  --default_table_expiration=0 \
  --description="Dataset per monitoring lab" \
  lab-platform-tutorial:monitoring

# Caricare CSV da GCS
bq load \
  --source_format=CSV \
  --skip_leading_rows=1 \
  --autodetect \
  lab-platform-tutorial:monitoring.api_requests \
  gs://lab-artifacts-gcp/data/requests.csv

# Query da CLI
bq query --use_legacy_sql=false \
  "SELECT service, COUNT(*) AS total FROM monitoring.api_requests
   WHERE DATE(timestamp) = CURRENT_DATE()
   GROUP BY service ORDER BY total DESC LIMIT 10"

# Esportare risultati su GCS
bq extract \
  --destination_format=NEWLINE_DELIMITED_JSON \
  lab-platform-tutorial:monitoring.api_requests \
  gs://lab-artifacts-gcp/exports/requests-*.json
BQ_COMMANDS
```

---

## Conclusioni e Prossimi Passi

```
GCP — RIEPILOGO:

GERARCHIA E STRUTTURA:
  ✓ Organization → Folder → Project (project = unità base)
  ✓ VPC globale: una VPC attraversa tutte le regioni (unico in GCP)
  ✓ Organization Policy: regole imposte su tutta la gerarchia
  ✓ VPC Service Controls: perimetrare l'accesso ai servizi PaaS

IAM:
  ✓ Service Account: identità per applicazioni
  ✓ Workload Identity Federation: K8s pod ↔ GCP senza key file
  ✓ ADC (Application Default Credentials): autenticazione automatica
  ✓ No chiavi SA per risorse dentro GCP (usare Workload Identity)

CLOUD STORAGE:
  ✓ Classi: Standard → Nearline (30d) → Coldline (90d) → Archive (365d)
  ✓ Object versioning e soft delete per recovery
  ✓ Signed URL per accesso temporaneo senza autenticazione
  ✓ Uniform bucket-level access (no ACL per oggetto)

PUB/SUB:
  ✓ Publisher: pubblica messaggi su topic (fire and forget)
  ✓ Subscription: consumer riceve messaggi (push o pull)
  ✓ Dead Letter Queue: messaggi non elaborati dopo N tentativi
  ✓ Ordering key: ordine garantito per messaggi con stessa chiave

GKE AUTOPILOT:
  ✓ Nessun nodo da gestire (Google gestisce node pool)
  ✓ Paghi CPU/RAM richiesta dai pod (non i nodi interi)
  ✓ Resource requests OBBLIGATORIE
  ✓ No privileged containers, no hostPath
  ✓ Workload Identity per accesso GCP senza credenziali nel pod

CLOUD RUN:
  ✓ Scala a zero (0 costi a idle)
  ✓ Scala fino a 1000 istanze in secondi
  ✓ Container qualsiasi (HTTP su PORT env var)
  ✓ Service Account per accesso ad altri servizi GCP

BIGQUERY:
  ✓ SQL su TB in secondi (storage colonnare + compute distribuito)
  ✓ Partizionamento per data: riduce costi scansione
  ✓ Clustering: ordine dati su disco per query veloci
  ✓ Materialized View: query frequenti pre-calcolate
  ✓ BQML: ML in SQL (ARIMA, regressione, classificazione)

COMANDI CHIAVE gcloud:
  gcloud projects create/list/delete
  gcloud services enable/list
  gcloud iam service-accounts create/list/keys create
  gcloud storage cp/ls/cat/rm
  gcloud container clusters create-auto/get-credentials
  gcloud run deploy/services list
  bq query/mk/load/extract
```

**Prossimi tutorial:**
- `tutorial_plat04_iac_lab.md` — Terraform avanzato con moduli, OpenTofu, Ansible
- `tutorial_plat09_service_mesh_lab.md` — Istio su GKE (mTLS, traffic management)

```bash
# Pulizia lab
cd ~/gcp-lab
docker stop cloud-run-test 2>/dev/null
docker compose down -v
rm -rf ~/gcp-lab /tmp/gcp-{manifest,downloaded}.json

echo "[OK] Lab GCP completato"
```

---

> **Nota versioni:** Tutorial validato con gcloud CLI 502.x (luglio 2026), GKE 1.31.x,
> Cloud Run managed, fake-gcs-server 1.51, BigQuery Standard SQL.
> GKE Autopilot: da versione 1.29 supporta Spot Pods (equivalente Spot Instances — fino a 90% risparmio).
> Cloud Run: da luglio 2026 supporta GPU T4 per inferenza ML (preview pubblica).
> BigQuery: partitioned tables obbligatorie per tabelle oltre 1TB per contenere i costi.
