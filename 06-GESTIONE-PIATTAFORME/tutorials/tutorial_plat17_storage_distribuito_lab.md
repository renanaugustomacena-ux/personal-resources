# Tutorial: Storage Distribuito — MinIO, Longhorn su K3s e CSI Driver

> **Documento di riferimento:** `17-storage-distribuito.md`
> **Dominio:** Gestione Piattaforme — Dati e Messaging
> **Ambito:** MinIO S3-compatible object storage, Longhorn block storage su K3s, StorageClass e PVC Kubernetes, CSI driver lifecycle, lifecycle policies, benchmark I/O, backup e restore
> **Durata lab:** 6-7 ore
> **Livello:** Avanzato — richiede K3s cluster, helm, Docker
> **Prerequisiti:** K3s cluster locale (16GB RAM raccomandati), helm 3.x, kubectl, Docker Engine
> **Ambiente:** MinIO RELEASE.2024-xx via Docker, Longhorn 1.7.x via Helm su K3s

---

## Lab Environment Setup

```bash
# === VERIFICA PREREQUISITI STORAGE LAB ===
echo "=== PREREQUISITI ==="

kubectl version --client --short 2>/dev/null && echo "[OK] kubectl" || echo "[FAIL] kubectl richiesto"
helm version --short 2>/dev/null && echo "[OK] helm" || echo "[FAIL] helm richiesto"
docker --version && echo "[OK] Docker" || echo "[FAIL] Docker richiesto"

# Verificare risorse cluster
echo ""
echo "--- Risorse cluster ---"
kubectl get nodes -o custom-columns="NODE:.metadata.name,CPU:.status.capacity.cpu,RAM:.status.capacity.memory" 2>/dev/null

# Verificare che il filesystem del nodo abbia spazio
df -h /var/lib/longhorn 2>/dev/null || df -h /

# Installare mc (MinIO Client CLI) se non presente
if ! command -v mc &>/dev/null; then
  curl -sSf https://dl.min.io/client/mc/release/linux-amd64/mc -o /usr/local/bin/mc 2>/dev/null && \
    chmod +x /usr/local/bin/mc && echo "[OK] mc (MinIO Client) installato" || \
    echo "[INFO] mc opzionale — istruzioni: https://min.io/docs/minio/linux/reference/minio-mc.html"
fi

mkdir -p ~/storage-lab/{minio,longhorn,benchmarks}
cd ~/storage-lab

echo "[OK] Directory lab: ~/storage-lab"
```

### Architettura Storage Distribuito

```
┌──────────────────────────────────────────────────────────────────────────┐
│                  STORAGE DISTRIBUITO — PANORAMICA                        │
│                                                                          │
│  TIPO 1: OBJECT STORAGE (S3-compatible)                                 │
│  MinIO ─────────────────────────── S3 API: GET/PUT/DELETE               │
│  ├── Bucket: backup, media, logs, artifacts                             │
│  ├── Policy: lifecycle (transition→GLACIER, expire→DELETE)             │
│  └── Replication: multi-site, versioning                                │
│                                                                          │
│  TIPO 2: BLOCK STORAGE (per DB, stateful workloads)                     │
│  Longhorn ─────────────── CSI Driver → PVC → Pod volume                │
│  ├── Replica: 3 copie su nodi diversi                                   │
│  ├── Snapshot: on-demand e schedulato                                   │
│  └── Backup: a S3/MinIO remoto                                          │
│                                                                          │
│  TIPO 3: FILE STORAGE (NFS, condivisione tra pod)                       │
│  NFS / CephFS ─────────── ReadWriteMany PVC                            │
│                                                                          │
│  QUANDO USARE:                                                           │
│  Object → media, backups, archivi, artifacts immutabili                 │
│  Block → database, code base di log strutturati, stateful apps          │
│  File → condivisione tra pod, configurazioni condivise                  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## PART A: FONDAMENTI — Tipi di Storage

> Immaginate di dover scegliere come archiviare i documenti di un ufficio.
> Un hard disk esterno (block storage) è veloce e permette di lavorare
> direttamente sui file, ma è collegato a un solo computer alla volta.
> Una cartella condivisa in rete (file storage) permette a tutti di accedere
> agli stessi documenti contemporaneamente, ma può diventare lenta.
> Un cloud drive come Google Drive (object storage) è ideale per archiviare
> milioni di file con accesso HTTP, ma non per modificare documenti in tempo reale.
> La scelta dipende da chi usa i dati, quanto spesso, e in che modo.

---

### Concetto A1: Block vs File vs Object Storage

```
CONFRONTO STORAGE TYPES:

BLOCK STORAGE:
  Esempio: disco aggiuntivo su un server (EBS, Longhorn, Ceph RBD)
  Accesso: read/write diretto su blocchi (come un disco locale)
  Protocollo: iSCSI, NVMe-oF, SCSI
  Casi d'uso: database PostgreSQL, MySQL, etcd Kubernetes
  Latenza: ~1ms (SSD), ottimale per I/O intensivo
  Limitazione: accessibile da UN solo nodo alla volta (ReadWriteOnce)
  K8s AccessMode: ReadWriteOnce (RWO)

FILE STORAGE:
  Esempio: NFS, CephFS, EFS (AWS), Azure Files
  Accesso: mount come filesystem, più nodi in contemporanea
  Protocollo: NFS, SMB/CIFS, FUSE
  Casi d'uso: configurazioni condivise, content management, CI artifacts
  Latenza: ~5-20ms (dipende da rete), non ideale per DB
  Vantaggio: ReadWriteMany (più pod in contemporanea)
  K8s AccessMode: ReadWriteMany (RWX)

OBJECT STORAGE:
  Esempio: S3 (AWS), MinIO, GCS, Azure Blob
  Accesso: HTTP API (GET/PUT/DELETE), non montabile come filesystem
  Protocollo: HTTP/S REST (S3 API), nativo per web
  Casi d'uso: backups, media files, log archives, ML datasets, artifacts
  Latenza: ~50-200ms per prima risposta, ottimo per file grandi
  Vantaggio: scalabilità orizzontale praticamente illimitata, lifecycle
  K8s: non si usa PVC, si accede con SDK (boto3, mc, gsutil)

REGOLA PRATICA:
  Database PostgreSQL in K8s → Longhorn (block, RWO)
  Log condivisi tra pod → NFS (file, RWX)
  Backup notturni + artifacts CI → MinIO (object)
  Media upload users → MinIO o cloud provider S3
```

---

### Concetto A2: CSI Driver — Come Kubernetes gestisce lo Storage

```
CSI (Container Storage Interface) — ARCHITETTURA:

Problema senza CSI (pre 2019):
  Ogni storage provider (AWS EBS, GCE PD, Ceph, Longhorn)
  richiedeva codice specifico nel core di Kubernetes.
  Ogni nuova versione K8s poteva rompere i driver.

Soluzione CSI (da K8s 1.13 — stabile da 1.17):
  Driver CSI come plugin separato (container)
  K8s definisce l'interfaccia → driver implementa i dettagli
  Aggiornamento driver ≠ aggiornamento cluster

FLUSSO PVC → VOLUME:

  Developer crea PVC:
  apiVersion: v1
  kind: PersistentVolumeClaim
  metadata:
    name: my-database-pvc
  spec:
    storageClassName: longhorn          ← indica il CSI driver
    accessModes: [ReadWriteOnce]
    resources:
      requests:
        storage: 10Gi

  K8s Storage Controller:
  1. Vede PVC → cerca StorageClass "longhorn"
  2. Chiama CSI Driver Longhorn: CreateVolume(10Gi)
  3. Longhorn crea il volume e le repliche
  4. K8s crea PersistentVolume automaticamente
  5. PVC → bound → Pod può montare il volume

  StorageClass (definisce il driver e le opzioni):
  apiVersion: storage.k8s.io/v1
  kind: StorageClass
  metadata:
    name: longhorn
  provisioner: driver.longhorn.io
  parameters:
    numberOfReplicas: "3"              ← 3 copie per HA
    staleReplicaTimeout: "2880"
  volumeBindingMode: WaitForFirstConsumer  ← crea volume dove il pod viene schedulato
  reclaimPolicy: Delete              ← elimina volume quando PVC eliminata
```

---

## PART B: MINIO — OBJECT STORAGE S3-COMPATIBLE

### Esercizio B1: Setup MinIO

```bash
cd ~/storage-lab

cat > compose-minio.yaml << 'EOF'
name: "storage-lab-minio"

networks:
  storage-net:
    driver: bridge

volumes:
  minio-data:

services:
  minio:
    image: minio/minio:RELEASE.2024-11-07T00-52-20Z
    container_name: minio
    hostname: minio-lab
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: "minio-lab-password-2026"
      
      # Abilitare compressione per dati testuali
      MINIO_COMPRESSION_ENABLED: "on"
      MINIO_COMPRESSION_EXTENSIONS: ".txt,.log,.json,.csv"
      
      # Prometheus metrics
      MINIO_PROMETHEUS_AUTH_TYPE: "public"
    ports:
      - "9000:9000"    # S3 API
      - "9001:9001"    # Console UI
    volumes:
      - minio-data:/data
    networks: [storage-net]
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 30s
      timeout: 20s
      retries: 3
EOF

docker compose -f compose-minio.yaml up -d

echo "Attendo MinIO..."
until curl -s http://localhost:9000/minio/health/live 2>/dev/null; do
  sleep 3
done

echo "[OK] MinIO avviato"
echo "[INFO] Console UI: http://localhost:9001 (minioadmin:minio-lab-password-2026)"
echo "[INFO] S3 API: http://localhost:9000"

# Configurare mc (MinIO Client)
mc alias set lab http://localhost:9000 minioadmin minio-lab-password-2026

# Verificare connessione
mc admin info lab
```

---

### Esercizio B2: Bucket, Policy e Lifecycle

```bash
echo "=== MINIO BUCKET E GESTIONE ==="

# Creare bucket per diversi use case
mc mb lab/backups       # backup database
mc mb lab/artifacts     # build artifacts CI/CD
mc mb lab/logs          # log archive
mc mb lab/media         # file media utenti

# Abilitare versioning (permette recupero versioni precedenti)
mc version enable lab/backups
mc version enable lab/artifacts

echo ""
echo "--- Upload di file di test ---"
# Creare dati di test
for i in $(seq 1 5); do
  echo "Backup $i - timestamp $(date -u +%Y%m%d-%H%M%S) - database_dump_${i}" > /tmp/backup-${i}.sql
  mc cp /tmp/backup-${i}.sql lab/backups/2026/01/
done

# Log file simulati
for i in $(seq 1 3); do
  echo '{"time":"2026-01-15T10:0'$i':00Z","level":"INFO","msg":"request completed","latency_ms":45}' \
    > /tmp/app-${i}.log
  mc cp /tmp/app-${i}.log lab/logs/2026/01/15/
done

# Verificare contenuto bucket
echo ""
mc ls lab/backups/2026/01/
mc ls lab/logs/2026/01/15/

echo ""
echo "--- Lifecycle Policy (retention automatica) ---"

# Policy lifecycle per backups: 30 giorni poi elimina
cat > minio/lifecycle-backups.json << 'EOF'
{
  "Rules": [
    {
      "ID": "expire-old-backups",
      "Status": "Enabled",
      "Filter": {
        "Prefix": ""
      },
      "Expiration": {
        "Days": 30
      }
    },
    {
      "ID": "expire-old-versions",
      "Status": "Enabled",
      "Filter": {
        "Prefix": ""
      },
      "NoncurrentVersionExpiration": {
        "NoncurrentDays": 7
      }
    }
  ]
}
EOF

mc ilm import lab/backups < minio/lifecycle-backups.json
echo "[OK] Lifecycle policy applicata a backups"

# Lifecycle per logs: 90 giorni
cat > minio/lifecycle-logs.json << 'EOF'
{
  "Rules": [
    {
      "ID": "expire-logs-90days",
      "Status": "Enabled",
      "Filter": {"Prefix": ""},
      "Expiration": {"Days": 90}
    }
  ]
}
EOF

mc ilm import lab/logs < minio/lifecycle-logs.json
echo "[OK] Lifecycle policy applicata a logs"

# Verificare policy
mc ilm ls lab/backups
```

---

### Esercizio B3: Accesso con Python SDK

```bash
cat > scripts/minio_demo.py << 'PYTHON'
"""Demo MinIO S3 con Python (boto3 — stessa API di AWS S3)."""
import boto3
import json
from datetime import datetime
from io import BytesIO

# Client S3 (boto3) puntato a MinIO locale
s3 = boto3.client(
    "s3",
    endpoint_url="http://localhost:9000",
    aws_access_key_id="minioadmin",
    aws_secret_access_key="minio-lab-password-2026",
    region_name="us-east-1",      # MinIO ignora la region ma boto3 la richiede
)

BUCKET = "artifacts"

print("=== MINIO DEMO — PYTHON SDK (boto3) ===\n")

# Upload di un artifact (bytes in memoria — no file su disco)
build_metadata = {
    "version": "1.2.3",
    "commit": "abc123",
    "branch": "main",
    "built_at": datetime.utcnow().isoformat() + "Z",
    "tests_passed": 42,
    "coverage_pct": 87.5,
}

artifact_key = f"builds/v{build_metadata['version']}/build-metadata.json"

s3.put_object(
    Bucket=BUCKET,
    Key=artifact_key,
    Body=json.dumps(build_metadata, indent=2).encode("utf-8"),
    ContentType="application/json",
    Metadata={
        "uploaded-by": "ci-pipeline",
        "environment": "staging",
    }
)
print(f"[OK] Artifact caricato: s3://{BUCKET}/{artifact_key}")

# Download e verifica
response = s3.get_object(Bucket=BUCKET, Key=artifact_key)
content = json.loads(response["Body"].read())
print(f"[OK] Download: version={content['version']}, tests={content['tests_passed']}")
print(f"     Metadata: {response['Metadata']}")

# Generare Presigned URL (permette accesso temporaneo senza credenziali)
presigned = s3.generate_presigned_url(
    "get_object",
    Params={"Bucket": BUCKET, "Key": artifact_key},
    ExpiresIn=3600    # valido 1 ora
)
print(f"\n[OK] Presigned URL (1h): {presigned[:80]}...")

# Listare oggetti nel bucket
response = s3.list_objects_v2(Bucket=BUCKET, Prefix="builds/")
print(f"\n[OK] Oggetti in builds/:")
for obj in response.get("Contents", []):
    size_kb = obj["Size"] / 1024
    print(f"  {obj['Key']}: {size_kb:.1f}KB, modificato={obj['LastModified'].strftime('%Y-%m-%d %H:%M')}")

# Server-side encryption (SSE)
s3.put_object(
    Bucket=BUCKET,
    Key="secure/encrypted-config.json",
    Body=json.dumps({"api_url": "https://api.example.com"}).encode("utf-8"),
    ServerSideEncryption="AES256",   # SSE-S3 (chiave gestita da MinIO)
)
print(f"\n[OK] File cifrato con SSE-S3")

print("\n=== DEMO COMPLETATA ===")
PYTHON

python3 scripts/minio_demo.py
```

---

## PART C: LONGHORN — BLOCK STORAGE SU KUBERNETES

### Esercizio C1: Installare Longhorn

```bash
cd ~/storage-lab

echo "=== LONGHORN — BLOCK STORAGE K8S ==="

# Prerequisiti nodo per Longhorn
echo "--- Verifica prerequisiti nodo ---"
kubectl get nodes -o wide
df -h /var/lib/longhorn 2>/dev/null || echo "[INFO] Directory /var/lib/longhorn verrà creata da Longhorn"

# Installare Longhorn via Helm
helm repo add longhorn https://charts.longhorn.io --force-update
helm repo update

helm upgrade --install longhorn longhorn/longhorn \
  --namespace longhorn-system \
  --create-namespace \
  --set defaultSettings.defaultReplicaCount=1 \   # 1 per single-node lab (produzione: 3)
  --set defaultSettings.storageMinimalAvailablePercentage=10 \
  --set csi.attacherReplicaCount=1 \
  --set csi.provisionerReplicaCount=1 \
  --set csi.resizerReplicaCount=1 \
  --set csi.snapshotterReplicaCount=1 \
  --wait \
  --timeout 300s

kubectl -n longhorn-system get pods

echo "[OK] Longhorn installato"
echo "[INFO] UI: kubectl -n longhorn-system port-forward svc/longhorn-frontend 8080:80"

# Vedere la StorageClass creata da Longhorn
kubectl get storageclass
```

---

### Esercizio C2: PVC e StatefulSet

```bash
echo "=== LONGHORN PVC + STATEFULSET ==="

# StorageClass Longhorn con replica e configurazione
cat > longhorn/storage-class.yaml << 'EOF'
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: longhorn-ssd
  annotations:
    storageclass.kubernetes.io/is-default-class: "false"
parameters:
  numberOfReplicas: "1"         # single-node lab (produzione: 3)
  staleReplicaTimeout: "2880"   # 2 giorni
  fromBackup: ""
  diskSelector: ""
  nodeSelector: ""
provisioner: driver.longhorn.io
allowVolumeExpansion: true       # permette espansione senza downtime
reclaimPolicy: Retain            # non elimina il volume quando la PVC è eliminata
volumeBindingMode: WaitForFirstConsumer
EOF

kubectl apply -f longhorn/storage-class.yaml

# StatefulSet PostgreSQL con Longhorn storage
cat > longhorn/postgres-statefulset.yaml << 'EOF'
apiVersion: v1
kind: Service
metadata:
  name: postgres-sts
  namespace: default
spec:
  clusterIP: None    # Headless service (richiesto da StatefulSet)
  selector:
    app: postgres-sts
  ports:
    - port: 5432

---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres-sts
  namespace: default
  annotations:
    description: >
      PostgreSQL con Longhorn storage.
      StatefulSet garantisce: ordine deploy, pod identity stabile,
      PVC dedicata per ogni replica (postgres-sts-0, postgres-sts-1...).
spec:
  serviceName: postgres-sts
  replicas: 1    # single per lab
  selector:
    matchLabels:
      app: postgres-sts
  
  template:
    metadata:
      labels:
        app: postgres-sts
    spec:
      containers:
        - name: postgres
          image: postgres:17-alpine
          env:
            - name: POSTGRES_DB
              value: labdb
            - name: POSTGRES_USER
              value: labuser
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: password
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata  # subdir per compatibilità
          
          ports:
            - containerPort: 5432
          
          resources:
            requests:
              cpu: "100m"
              memory: "256Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          
          volumeMounts:
            - name: pgdata
              mountPath: /var/lib/postgresql/data
          
          readinessProbe:
            exec:
              command: ["pg_isready", "-U", "labuser", "-d", "labdb"]
            initialDelaySeconds: 10
            periodSeconds: 10
  
  # Template PVC — Longhorn crea automaticamente una PVC per ogni replica
  volumeClaimTemplates:
    - metadata:
        name: pgdata
      spec:
        storageClassName: longhorn-ssd
        accessModes: [ReadWriteOnce]
        resources:
          requests:
            storage: 5Gi
EOF

# Creare il secret password
kubectl create secret generic postgres-secret \
  --from-literal=password=lab-postgres-password-2026 \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -f longhorn/postgres-statefulset.yaml

echo "Attendo PostgreSQL StatefulSet ready..."
kubectl rollout status statefulset/postgres-sts --timeout=120s && \
  echo "[OK] PostgreSQL con Longhorn storage avviato" || \
  echo "[INFO] Verificare: kubectl describe statefulset postgres-sts"

echo ""
echo "--- Verificare PVC Longhorn ---"
kubectl get pvc
kubectl get pv

echo ""
echo "--- Test: scrivere dati persistenti ---"
kubectl exec postgres-sts-0 -- psql -U labuser -d labdb -c \
  "CREATE TABLE IF NOT EXISTS test_persistence (id SERIAL PRIMARY KEY, value TEXT, created_at TIMESTAMP DEFAULT NOW());"

kubectl exec postgres-sts-0 -- psql -U labuser -d labdb -c \
  "INSERT INTO test_persistence (value) VALUES ('dato persistente 1'), ('dato persistente 2');"

kubectl exec postgres-sts-0 -- psql -U labuser -d labdb -c \
  "SELECT * FROM test_persistence;"

echo ""
echo "[INFO] I dati sopra sopravvivono anche se il Pod viene riavviato!"
```

---

### Esercizio C3: Snapshot e Backup

```bash
echo "=== LONGHORN SNAPSHOT E BACKUP ==="

cat > longhorn/volume-snapshot.yaml << 'EOF'
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: postgres-snapshot-manual
  namespace: default
  annotations:
    description: "Snapshot manuale pre-migrazione"
spec:
  volumeSnapshotClassName: longhorn
  source:
    persistentVolumeClaimName: pgdata-postgres-sts-0   # nome automatico dal StatefulSet
EOF

kubectl apply -f longhorn/volume-snapshot.yaml 2>/dev/null

echo ""
echo "--- Scheduled Backup con Longhorn ---"
cat > longhorn/recurring-job.yaml << 'EOF'
apiVersion: longhorn.io/v1beta2
kind: RecurringJob
metadata:
  name: daily-backup
  namespace: longhorn-system
spec:
  cron: "0 2 * * *"    # ogni notte alle 02:00
  task: backup
  groups: [default]
  retain: 7             # mantieni 7 backup
  concurrency: 2
  labels:
    backup-type: daily
EOF

kubectl apply -f longhorn/recurring-job.yaml 2>/dev/null

# Vedere snapshot esistenti
kubectl get volumesnapshots 2>/dev/null

echo ""
echo "=== STORAGE BENCHMARK (fio — opzionale) ==="
cat << 'BENCH'
# Benchmark I/O su volume Longhorn (se fio è disponibile):

kubectl run fio-bench --image=nixery.dev/fio \
  --overrides='{"spec":{"volumes":[{"name":"test","persistentVolumeClaim":{"claimName":"pgdata-postgres-sts-0"}}],"containers":[{"name":"fio-bench","image":"nixery.dev/fio","command":["fio","--name=test","--rw=randrw","--bs=4k","--numjobs=4","--iodepth=32","--runtime=60","--filename=/mnt/test.dat","--size=1G","--direct=1"],"volumeMounts":[{"name":"test","mountPath":"/mnt"}]}]}}'

# Metriche target per storage K8s produzione:
# IOPS random read/write: > 1000 IOPS
# Latenza p99 write: < 5ms
# Throughput sequenziale: > 100MB/s
BENCH
```

---

## PART D: STORAGECLASS E RECLAIM POLICY

### Esercizio D1: Gestione del Lifecycle dei Volumi

```bash
echo "=== GESTIONE LIFECYCLE VOLUMI K8S ==="

cat << 'GUIDE'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECLAIM POLICY — COSA SUCCEDE QUANDO SI ELIMINA UNA PVC
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Delete (default per cloud providers):
  PVC eliminata → PV eliminato → Storage fisico eliminato
  Usare per: dati temporanei, test, cache
  RISCHIO: eliminazione PVC accidentale = PERDITA DATI

Retain:
  PVC eliminata → PV diventa "Released" (non riutilizzabile)
  Storage fisico PRESERVATO
  Admin deve: ispezionare, recuperare dati, poi eliminare PV manualmente
  Usare per: database, dati critici
  
Recycle (deprecato in K8s 1.20):
  PVC eliminata → PV svuotato (rm -rf) → disponibile per nuova PVC
  Non usare — sostituito da provisioning dinamico

BEST PRACTICE:
  ✓ Database: reclaimPolicy: Retain + backup automatici
  ✓ Temp/cache: reclaimPolicy: Delete
  ✓ AllowVolumeExpansion: true (sempre — permette resize senza downtime)
  ✓ volumeBindingMode: WaitForFirstConsumer (topologia-aware)

VOLUME EXPANSION (senza downtime con K8s 1.24+):
  1. Modificare PVC: spec.resources.requests.storage: 20Gi (era 10Gi)
  2. K8s notifica il CSI driver → espande il volume online
  3. Il filesystem viene espeso al prossimo mount (o online se supportato)
  
  kubectl patch pvc pgdata-postgres-sts-0 -p '{"spec":{"resources":{"requests":{"storage":"20Gi"}}}}'
  # Verifica: kubectl describe pvc pgdata-postgres-sts-0 | grep "Capacity:"

ACCESS MODES K8S:
  ReadWriteOnce (RWO): un solo nodo monta in lettura/scrittura → block storage
  ReadOnlyMany (ROX): più nodi montano in sola lettura
  ReadWriteMany (RWX): più nodi montano in lettura/scrittura → NFS, CephFS
  ReadWriteOncePod (RWOP): solo UN pod (non solo un nodo) — K8s 1.29+

CAPACITY PLANNING:
  Replica 3 (Longhorn default): efficienza 33% (100GB usabili = 300GB storage)
  Erasure coding 4+2 (MinIO): efficienza 67% (100GB usabili = 150GB storage)
  Ceph EC 8+2: efficienza 80%
  
  Formula: storage_needed = dati_totali / efficienza
  Esempio: 1TB dati, Longhorn 3x = 3TB dischi
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GUIDE

# Verificare lo stato attuale dello storage
echo ""
echo "=== STATO STORAGE NEL CLUSTER ==="
kubectl get pv
echo ""
kubectl get pvc -A
echo ""
kubectl get storageclass
```

---

## Conclusioni e Prossimi Passi

```
STORAGE DISTRIBUITO — RIEPILOGO:

MINIO:
  ✓ API S3-compatible: stesso SDK di AWS (boto3, mc, s3cmd)
  ✓ Lifecycle policy: expire automatica dopo N giorni
  ✓ Versioning: recupero versioni precedenti degli oggetti
  ✓ SSE: cifratura at rest (AES256 o KMS custom key)
  ✓ Presigned URL: accesso temporaneo senza credenziali

LONGHORN:
  ✓ CSI driver: integrazione nativa K8s (PVC, VolumeSnapshot)
  ✓ Replication: N copie su nodi diversi (default 3)
  ✓ Snapshot: manuale o schedulato (RecurringJob)
  ✓ Backup: a S3/MinIO per DR
  ✓ Volume expansion: resize online senza downtime

CSI / PVC BEST PRACTICE:
  ✓ reclaimPolicy: Retain per database (mai Delete!)
  ✓ allowVolumeExpansion: true sempre
  ✓ WaitForFirstConsumer: non crea volume finché pod non è schedulato
  ✓ volumeClaimTemplates in StatefulSet: PVC dedicata per ogni replica

QUANDO SCEGLIERE:
  PostgreSQL, MySQL, etcd → Longhorn/Ceph RBD (block, RWO)
  Shared content, CI cache → NFS/CephFS (file, RWX)
  Backups, media, ML data → MinIO/Ceph RGW/S3 (object)
  Single-node K3s → Longhorn (ottimo, overhead basso)
  Multi-node on-prem → Rook-Ceph (tutto-in-uno: block+file+object)
  Cloud → EBS/EFS/S3 (managed, zero ops)

CAPACITY PLANNING:
  ✓ Longhorn 3x replica: serve 3× lo spazio dati
  ✓ MinIO erasure coding 4+2: serve 1.5× lo spazio dati
  ✓ Alert su 80% utilizzo (non aspettare il 100%)
  ✓ Longhorn UI mostra disk usage per nodo

BACKUP E DR:
  ✓ 3-2-1 rule: 3 copie, 2 media diversi, 1 offsite
  ✓ Backup PostgreSQL: pg_dump + carica su MinIO bucket
  ✓ Longhorn backup: snapshot → MinIO remote backup
  ✓ Testare il restore almeno mensilmente!
```

```bash
# Pulizia lab
kubectl delete statefulset postgres-sts 2>/dev/null
kubectl delete pvc pgdata-postgres-sts-0 2>/dev/null
kubectl delete secret postgres-secret 2>/dev/null
kubectl delete -f longhorn/ --ignore-not-found=true 2>/dev/null
helm uninstall longhorn -n longhorn-system 2>/dev/null
docker compose -f compose-minio.yaml down -v 2>/dev/null
rm -rf ~/storage-lab
echo "[OK] Lab Storage Distribuito completato"
```

---

> **Nota versioni:** MinIO RELEASE.2024-11-07 (novembre 2024), Longhorn 1.7.x (Helm chart 103.x.x, ottobre 2024).
> Rook-Ceph 1.15 (compatibile con Ceph 18.x Reef, ottobre 2024).
> Ceph 18.2.x (Reef): nuova dashboard (Ceph Manager), miglioramenti RBD mirroring.
> K8s VolumeSnapshot API: stable (v1) da Kubernetes 1.20.
> ReadWriteOncePod (RWOP): stable da K8s 1.29 (gennaio 2024).
> CSI Spec 1.10: aggiunge volume group snapshot (beta in K8s 1.31).
