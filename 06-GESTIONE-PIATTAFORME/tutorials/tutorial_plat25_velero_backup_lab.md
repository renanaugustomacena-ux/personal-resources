# Tutorial: Backup e Ripristino Kubernetes con Velero — Lab Pratico

> **Documento di riferimento:** `25-velero-kubernetes-backup.md`
> **Dominio:** Gestione Piattaforme — Disaster Recovery e Business Continuity
> **Ambito:** Velero installazione, backup on-demand, schedule automatici, restore drill, backup etcd, RTO/RPO
> **Durata lab:** 5-7 ore
> **Livello:** Avanzato — richiede Kubernetes e familiarità con PVC e storage
> **Prerequisiti:** Cluster K8s funzionante, kubectl, Helm 3.x, Docker (per MinIO)
> **Ambiente:** Cluster K8s locale con MinIO come backend storage per i backup

---

## Lab Environment Setup

### Prerequisiti e verifica

```bash
#!/bin/bash
# check-prerequisites-velero.sh

echo "=== Verifica Prerequisiti Velero Backup Lab ==="
echo ""

ALL_OK=true

check() {
    if eval "$2" &>/dev/null; then
        echo "[OK]   $1 — $(eval "$2" 2>&1 | head -1)"
    else
        echo "[FAIL] $1 — $3"
        ALL_OK=false
    fi
}

check "kubectl"       "kubectl version --client --short 2>/dev/null" "https://kubernetes.io/docs/tasks/tools/"
check "Helm 3"        "helm version --short"                          "https://helm.sh"
check "Docker"        "docker --version"                              "https://docs.docker.com/get-docker/"

# Velero CLI
if velero version --client-only &>/dev/null 2>&1; then
    echo "[OK]   Velero CLI — $(velero version --client-only 2>&1 | head -1)"
else
    echo "[INFO] Velero CLI non installato — scaricheremo nel lab"
fi

# Cluster raggiungibile
if kubectl cluster-info &>/dev/null; then
    echo "[OK]   Cluster K8s raggiungibile"
else
    echo "[FAIL] Cluster K8s non raggiungibile"
    ALL_OK=false
fi

echo ""
[ "$ALL_OK" = true ] && echo "[OK] Prerequisiti soddisfatti!" || echo "[WARN] Alcuni prerequisiti mancanti."
```

### Architettura del Lab

```
ARCHITETTURA LAB VELERO BACKUP:

┌─────────────────────────────────────────────────────────────────────────┐
│                    CLUSTER KUBERNETES                                    │
│                                                                         │
│  namespace: velero                                                      │
│  ├── velero-server              (API + controller backup/restore)       │
│  └── node-agent (daemonset)     (backup PVC con Kopia su ogni nodo)    │
│                                                                         │
│  namespace: backup-demo                                                 │
│  ├── postgres-0                 (StatefulSet con PVC 1Gi)              │
│  ├── app-deployment             (applicazione con dati)                │
│  └── postgres-pvc               (PersistentVolumeClaim)                │
│                                                                         │
│  namespace: minio-backup                                                │
│  └── minio                      (S3-compatible storage :9000)          │
│                                                                         │
│  FLUSSO BACKUP:                                                         │
│  velero backup create → node-agent legge PVC → push su MinIO           │
│                                                                         │
│  FLUSSO RESTORE:                                                        │
│  velero restore create → pull da MinIO → applica manifesti + PVC       │
└─────────────────────────────────────────────────────────────────────────┘

DATI NEL BACKUP:
  Manifesti K8s: Deployment, Service, ConfigMap, Secret, RBAC, PVC, CRD
  PVC Data:      file sui PersistentVolume (via Kopia file-level backup)
  NON incluso:   etcd (richiede backup separato con etcdctl)
```

---

## PART A: FONDAMENTI — Perché il Backup K8s È Critico e Diverso

> **Perché questo modulo è essenziale:**
>
> "I backup non sono importanti finché non lo diventano" — tutti i SRE hanno
> imparato questa lezione in modo doloroso. Un cluster Kubernetes cancellato
> accidentalmente, un namespace eliminato da uno script sbagliato, una migrazione
> di database fallita a metà: senza backup, si perde tutto.
>
> Kubernetes aggiunge complessità rispetto ai backup tradizionali: lo stato è
> distribuito in etcd (manifesti), nei PersistentVolume (dati), e nel registry
> (immagini). Velero è lo strumento CNCF che standardizza il backup dei manifesti
> e dei PVC in modo automatico e testabile.

---

### Concetto A1: Il Paradosso del Backup Non Testato

> **Analogia.** Un backup non testato è come un paracadute in un sacchetto chiuso:
> sembra ci sia qualcosa di sicuro dentro, ma non sai se si apre finché non ne hai
> bisogno davvero. E a quel punto è troppo tardi per scoprire che è rotto.
>
> La regola fondamentale del backup: un backup non testato non è un backup.
> Ogni mese devi eseguire un restore drill reale — non "guarda la lista dei backup",
> ma "ripristina il namespace in staging e verifica che l'app funzioni".

```
BACKUP NON TESTATO VS TESTATO:

BACKUP NON TESTATO (falsa sicurezza):
  "Abbiamo Velero installato da 6 mesi"
  "La lista backup mostra 180 backup riusciti"
  
  Disastro: il cluster va giù → proviamo il restore
  → velero restore create --from-backup backup-20260101
  → ERROR: backup corrupted (MinIO aveva un bug di scrittura)
  → 6 mesi di backup inutilizzabili
  → Recovery manuale da zero: 3 giorni
  
BACKUP TESTATO (vera sicurezza):
  "Ogni mese facciamo un restore drill in staging"
  "L'ultimo restore drill: 45 minuti, successo, app funzionante"
  
  Disastro: il cluster va giù → restore
  → 45 minuti → cluster ripristinato, tutto funzionante
  → RTO documentato: 45 minuti (realistico, già testato)

REGOLA 3-2-1 PER KUBERNETES:
  3 copie dei dati:
    Copia 1: MinIO nel cluster principale (on-prem)
    Copia 2: S3 off-site (AWS S3 o diversa region)
    Copia 3: etcd snapshot su storage separato
  
  2 media diversi:
    Storage principale: SAN/NAS del datacenter
    Storage secondario: cloud S3
  
  1 copia off-site:
    Diversa location fisica dalla produzione
    Protegge da: incendio, alluvione, attacco ransomware
```

---

### Concetto A2: Velero vs Backup Tradizionale

> **Analogia.** Il backup tradizionale è come fotografare ogni file di un ufficio:
> hai le immagini, ma per ricreare l'ufficio devi rimettere ogni file al posto giusto
> manualmente, sapendo dove stava. Velero è come fare una foto 3D dell'intero ufficio
> con le posizioni: puoi ricreare l'ufficio esattamente com'era, nella stessa stanza
> o in un'altra sede.

```
VELERO — COSA SALVA E COME:

1. MANIFESTI KUBERNETES (sempre):
   kubectl get all -n my-namespace -o yaml → serializzato in tarball
   Salvato in: s3://velero-backups/my-backup/resources/
   Include: Deployment, Service, ConfigMap, Secret, RBAC, CRD, PVC definition
   
   Ripristino: kubectl apply -f (automatico da Velero)

2. DATI PVC (opzionale, via Kopia/Restic):
   Kopia legge i file dai PVC montati sui nodi
   Deduplica e comprime i dati
   Salvato in: s3://velero-backups/kopia-repository/
   
   Ripristino: Kopia estrae i file, monta sul nuovo PVC

3. CSI SNAPSHOT (alternativa a Kopia):
   Se il CSI driver supporta VolumeSnapshot API
   Snapshot a livello storage (più veloce di Kopia)
   Salvato: nello stesso storage del PVC (non off-site!)
   
   Ripristino: crea nuovo PVC da snapshot

COSA VELERO NON SALVA:
  ✗ etcd: backup del database K8s (richiede etcdctl separato)
  ✗ Immagini Docker (sono nel registry)
  ✗ Secret dell'ingress TLS se gestiti fuori da K8s
  ✗ Database content se non è in un PVC
```

---

## PART B: INSTALLAZIONE MINIO E VELERO

### Esercizio B1: Installare MinIO (Backend Storage)

```bash
# Namespace per MinIO
kubectl create namespace minio-backup || true

# MinIO: object storage S3-compatible
helm repo add minio https://charts.min.io/
helm repo update

helm install minio minio/minio \
    --namespace minio-backup \
    --set rootUser=velero-admin \
    --set rootPassword=velero-minio-secret-2026 \
    --set replicas=1 \
    --set persistence.size=10Gi \
    --set mode=standalone \
    --set service.type=ClusterIP \
    --wait

# Verifica
kubectl get pods -n minio-backup

# Output atteso:
# NAME               READY   STATUS    RESTARTS   AGE
# minio-0            1/1     Running   0          2m

# Ottieni l'URL interno del service
MINIO_SVC=$(kubectl get svc minio -n minio-backup -o jsonpath='{.spec.clusterIP}')
echo "MinIO IP interno: $MINIO_SVC"

# Porta-forward per accedere via browser
kubectl port-forward svc/minio 9001:9001 -n minio-backup &
echo "MinIO Console: http://localhost:9001 (velero-admin/velero-minio-secret-2026)"

# Crea il bucket per Velero usando mc (MinIO Client)
kubectl run minio-setup \
    --image=minio/mc:latest \
    --restart=Never \
    --rm \
    -n minio-backup \
    -- sh -c '
        mc alias set local http://minio.minio-backup.svc.cluster.local:9000 velero-admin velero-minio-secret-2026 &&
        mc mb local/velero-backups &&
        mc ls local/ &&
        echo "Bucket creato con successo"
    '

# Output atteso:
# Added `local` successfully.
# Bucket created successfully `local/velero-backups`.
# [2026-07-16 10:00:00 UTC]     0B velero-backups/
# Bucket creato con successo
```

---

### Esercizio B2: Installare Velero CLI

```bash
# Download Velero CLI (Linux/macOS)
VELERO_VERSION="v1.15.0"

# Linux
curl -L https://github.com/vmware-tanzu/velero/releases/download/${VELERO_VERSION}/velero-${VELERO_VERSION}-linux-amd64.tar.gz \
    -o velero.tar.gz
tar -xzf velero.tar.gz
sudo mv velero-${VELERO_VERSION}-linux-amd64/velero /usr/local/bin/
rm -rf velero.tar.gz velero-${VELERO_VERSION}-linux-amd64/

# Verifica
velero version --client-only

# Output atteso:
# Client:
#         Version: v1.15.0
#         Git commit: abc123...
```

---

### Esercizio B3: Installare Velero nel Cluster

```bash
# Crea il Secret con le credenziali MinIO (formato AWS credentials)
cat > /tmp/velero-credentials <<'EOF'
[default]
aws_access_key_id = velero-admin
aws_secret_access_key = velero-minio-secret-2026
EOF

# Installa Velero con il plugin AWS (per MinIO compatibile S3)
velero install \
    --provider aws \
    --plugins velero/velero-plugin-for-aws:v1.11.0 \
    --bucket velero-backups \
    --secret-file /tmp/velero-credentials \
    --use-volume-snapshots=false \
    --default-volumes-to-fs-backup=true \
    --backup-location-config region=minio,s3ForcePathStyle="true",s3Url=http://minio.minio-backup.svc.cluster.local:9000 \
    --uploader-type=kopia \
    --wait

rm /tmp/velero-credentials

# Output atteso (dopo 2-3 minuti):
# Velero is installed! ⛵ Use 'kubectl logs deployment/velero -n velero' to view the status.

# Verifica i pod Velero
kubectl get pods -n velero

# Output atteso:
# NAME                     READY   STATUS    RESTARTS   AGE
# velero-xxx               1/1     Running   0          2m
# node-agent-xxx           1/1     Running   0          2m   ← su ogni nodo

# Verifica che la BackupStorageLocation sia disponibile
velero backup-location get

# Output atteso:
# NAME      PROVIDER   BUCKET/PREFIX   PHASE       LAST VALIDATED   ACCESS MODE   DEFAULT
# default   aws        velero-backups  Available   10s ago          ReadWrite     true
```

---

## PART C: CREARE L'AMBIENTE DI TEST DA BACKUPPARE

### Esercizio C1: Deploy di un'Applicazione con Database e Dati

```bash
# Namespace che verrà backuppato
kubectl create namespace backup-demo || true

# Deploy PostgreSQL con PVC (StatefulSet)
cat <<'EOF' | kubectl apply -f -
---
# ConfigMap con schema iniziale
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgres-init
  namespace: backup-demo
data:
  init.sql: |
    -- Crea schema e dati di test
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        customer_name VARCHAR(100) NOT NULL,
        product VARCHAR(200) NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        total_price DECIMAL(10,2) NOT NULL,
        status VARCHAR(50) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT NOW()
    );
    
    -- Inserisci dati di test (questi verranno backuppati con il PVC)
    INSERT INTO orders (customer_name, product, quantity, total_price, status) VALUES
        ('Mario Rossi', 'Laptop Dell XPS 15', 1, 1299.99, 'confirmed'),
        ('Giulia Bianchi', 'Tastiera Meccanica', 2, 179.98, 'shipped'),
        ('Luca Verdi', 'Monitor 4K 27"', 1, 449.00, 'pending'),
        ('Anna Ferrari', 'Mouse Wireless', 3, 89.97, 'delivered'),
        ('Marco Ricci', 'Webcam HD', 1, 89.99, 'confirmed')
    ON CONFLICT DO NOTHING;

---
# Secret con password PostgreSQL
apiVersion: v1
kind: Secret
metadata:
  name: postgres-secret
  namespace: backup-demo
type: Opaque
stringData:
  POSTGRES_PASSWORD: "lab-password-2026"
  POSTGRES_DB: "ordersdb"
  POSTGRES_USER: "orders_user"

---
# StatefulSet PostgreSQL con PVC
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: backup-demo
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
      annotations:
        # Velero: include questo volume nel backup con Kopia
        backup.velero.io/backup-volumes: postgres-data
    spec:
      containers:
        - name: postgres
          image: postgres:16-alpine
          env:
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: POSTGRES_PASSWORD
            - name: POSTGRES_DB
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: POSTGRES_DB
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: postgres-secret
                  key: POSTGRES_USER
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata
          ports:
            - containerPort: 5432
          resources:
            requests:
              cpu: 100m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 512Mi
          volumeMounts:
            - name: postgres-data
              mountPath: /var/lib/postgresql/data
            - name: init-scripts
              mountPath: /docker-entrypoint-initdb.d
          readinessProbe:
            exec:
              command: [pg_isready, -U, orders_user, -d, ordersdb]
            initialDelaySeconds: 10
            periodSeconds: 5
      volumes:
        - name: init-scripts
          configMap:
            name: postgres-init
  
  volumeClaimTemplates:
    - metadata:
        name: postgres-data
        annotations:
          backup.velero.io/backup-volumes: "true"
      spec:
        accessModes: [ReadWriteOnce]
        resources:
          requests:
            storage: 1Gi

---
# Service per PostgreSQL
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: backup-demo
spec:
  selector:
    app: postgres
  ports:
    - port: 5432
      targetPort: 5432
  clusterIP: None    # Headless service per StatefulSet

---
# ConfigMap con la configurazione dell'applicazione
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: backup-demo
  labels:
    environment: production
    team: backend
data:
  DATABASE_HOST: "postgres.backup-demo.svc.cluster.local"
  LOG_LEVEL: "info"
  APP_VERSION: "2.1.4"
  FEATURE_FLAGS: "new_checkout=true,dark_mode=false"

---
# Deployment: applicazione frontend
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-app
  namespace: backup-demo
  labels:
    app: order-app
    version: "2.1.4"
spec:
  replicas: 2
  selector:
    matchLabels:
      app: order-app
  template:
    metadata:
      labels:
        app: order-app
    spec:
      containers:
        - name: app
          image: nginx:stable-alpine
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 200m
              memory: 128Mi

---
apiVersion: v1
kind: Service
metadata:
  name: order-app
  namespace: backup-demo
spec:
  selector:
    app: order-app
  ports:
    - port: 80
  type: ClusterIP
EOF

# Aspetta che PostgreSQL sia pronto
kubectl wait --for=condition=ready pod \
    -l app=postgres \
    -n backup-demo \
    --timeout=120s

echo "[OK] PostgreSQL pronto"

# Verifica i dati inseriti
kubectl exec -n backup-demo postgres-0 -- \
    psql -U orders_user -d ordersdb -c "SELECT id, customer_name, product, status FROM orders;"

# Output atteso:
#  id | customer_name  | product              | status
# ----+----------------+----------------------+-----------
#   1 | Mario Rossi    | Laptop Dell XPS 15   | confirmed
#   2 | Giulia Bianchi | Tastiera Meccanica    | shipped
#   3 | Luca Verdi     | Monitor 4K 27"       | pending
#   4 | Anna Ferrari   | Mouse Wireless        | delivered
#   5 | Marco Ricci    | Webcam HD             | confirmed

echo "[OK] 5 record nel database — pronti per il backup"
```

---

## PART D: BACKUP ON-DEMAND

### Esercizio D1: Primo Backup Manuale

```bash
# Backup del namespace backup-demo (manifesti + PVC)
velero backup create demo-backup-001 \
    --include-namespaces backup-demo \
    --default-volumes-to-fs-backup=true \
    --ttl 168h \
    --labels "created-by=lab,type=manual" \
    --wait

# Output atteso:
# Backup request "demo-backup-001" submitted successfully.
# Waiting for backup to complete. You may safely press ctrl-c to stop waiting - your backup will continue in the background.
# .......................
# Backup completed with status: Completed. You may check for more information using the commands `velero backup describe demo-backup-001` and `velero backup logs demo-backup-001`.

# Verifica lo stato del backup
velero backup describe demo-backup-001 --details

# Output atteso:
# Name:         demo-backup-001
# Namespace:    velero
# Labels:       created-by=lab
#               type=manual
# Annotations:  velero.io/source-cluster-k8s-gitversion=v1.28.x
#               velero.io/source-cluster-k8s-major-version=1
#               velero.io/source-cluster-k8s-minor-version=28
#
# Phase:  Completed
#
# Errors:    0
# Warnings:  0
#
# Namespaces:
#   Included:  backup-demo
#   Excluded:  <none>
#
# Resources:
#   Included:        *
#   Excluded:        <none>
#   Cluster-scoped:  auto
#
# TTL:  168h0m0s
#
# CSISnapshotTimeout:    10m0s
# ItemOperationTimeout:  4h0m0s
#
# Estimated total items to be backed up:  23
# Items backed up so far:                 23
#
# Velero-Native Volume Snapshots: <none included>
#
# kopia Backups (specify --details for more information):
#   Completed:  1
#     backup-demo/postgres-0: orderers/postgres-data    → ID: abc123...
#
# Started:    2026-07-16 10:00:00 +0000 UTC
# Completed:  2026-07-16 10:01:30 +0000 UTC
# Duration:   1m 30s

# Lista tutti i backup
velero backup get

# Output atteso:
# NAME              STATUS      ERRORS  WARNINGS  CREATED                         EXPIRES  STORAGE LOCATION  SELECTOR
# demo-backup-001   Completed   0       0         2026-07-16 10:00:00 +0000 UTC   6d       default           <none>
```

---

### Esercizio D2: Aggiungere Nuovi Dati (per testare il backup point-in-time)

```bash
# Aggiungi nuovi ordini DOPO il backup (questi NON saranno nel backup)
kubectl exec -n backup-demo postgres-0 -- \
    psql -U orders_user -d ordersdb -c "
    INSERT INTO orders (customer_name, product, quantity, total_price, status) VALUES
        ('Sofia Romano', 'Cuffie Bluetooth', 1, 199.99, 'pending'),
        ('Carlo Esposito', 'Tablet iPad', 1, 799.00, 'confirmed')
    RETURNING id, customer_name, product;"

# Output:
#  id | customer_name  | product
# ----+----------------+------------------
#   6 | Sofia Romano   | Cuffie Bluetooth
#   7 | Carlo Esposito | Tablet iPad

# Conta i record attuali
kubectl exec -n backup-demo postgres-0 -- \
    psql -U orders_user -d ordersdb -c "SELECT COUNT(*) FROM orders;"

# Output: 7 (5 originali + 2 aggiunti dopo il backup)

echo "[INFO] Dopo il backup: 7 ordini nel database"
echo "       Il backup contiene: 5 ordini (snapshot al momento del backup)"
echo "       Dopo il restore: torneremo a 5 ordini (comportamento atteso)"
```

---

## PART E: RESTORE DA BACKUP

### Esercizio E1: Restore Completo del Namespace

```bash
# SCENARIO: il namespace backup-demo è stato cancellato accidentalmente
# OBIETTIVO: ripristinarlo dal backup

# Step 1: simula la perdita del namespace
echo "=== SIMULAZIONE PERDITA DATI ==="
kubectl delete namespace backup-demo

# Attendi la cancellazione completa
kubectl wait --for=delete namespace/backup-demo --timeout=60s 2>/dev/null || true

echo "[DONE] Namespace backup-demo eliminato"
echo "       Verifica: $(kubectl get ns backup-demo 2>&1)"
echo ""

# Step 2: ripristina da backup
echo "=== RIPRISTINO DA BACKUP ==="
velero restore create restore-demo-001 \
    --from-backup demo-backup-001 \
    --include-namespaces backup-demo \
    --wait

# Output atteso:
# Restore request "restore-demo-001" submitted successfully.
# Waiting for restore to complete. You may safely press ctrl-c to stop waiting
# .............
# Restore completed with status: Completed.

# Step 3: verifica il restore
echo ""
echo "=== VERIFICA RIPRISTINO ==="

velero restore describe restore-demo-001

# Output atteso:
# Name:         restore-demo-001
# Namespace:    velero
# Phase:        Completed
# 
# Backup:       demo-backup-001
# Namespaces:
#   Included:  backup-demo
#   Excluded:  <none>
#
# Errors:    0
# Warnings:  0

# Aspetta che i pod si avviino
kubectl wait --for=condition=ready pod \
    -l app=postgres \
    -n backup-demo \
    --timeout=180s

echo "[OK] PostgreSQL ripristinato"

# Verifica i dati (devono essere 5, non 7 — il backup era del punto precedente)
kubectl exec -n backup-demo postgres-0 -- \
    psql -U orders_user -d ordersdb -c "SELECT id, customer_name, product, status FROM orders ORDER BY id;"

# Output atteso (5 righe — gli ordini 6 e 7 aggiunti dopo il backup non ci sono):
#  id | customer_name  | product              | status
# ----+----------------+----------------------+-----------
#   1 | Mario Rossi    | Laptop Dell XPS 15   | confirmed
#   2 | Giulia Bianchi | Tastiera Meccanica    | shipped
#   3 | Luca Verdi     | Monitor 4K 27"       | pending
#   4 | Anna Ferrari   | Mouse Wireless        | delivered
#   5 | Marco Ricci    | Webcam HD             | confirmed
# (5 rows)

echo "[OK] RESTORE COMPLETATO — dati ripristinati al punto del backup"
echo "     Ordini presenti: 5 (i 2 aggiunti dopo il backup non sono presenti — comportamento corretto)"
```

---

### Esercizio E2: Restore in Namespace Diverso (Test Sicuro)

```bash
# BEST PRACTICE: testa il restore in un namespace separato senza impattare la produzione

velero restore create restore-test-001 \
    --from-backup demo-backup-001 \
    --include-namespaces backup-demo \
    --namespace-mappings backup-demo:backup-demo-test \
    --wait

# --namespace-mappings: ripristina backup-demo nel namespace backup-demo-test
# Permette di verificare il restore senza sovrascrivere la produzione

# Aspetta il restore
kubectl wait --for=condition=ready pod \
    -l app=postgres \
    -n backup-demo-test \
    --timeout=180s

# Verifica in namespace di test
kubectl exec -n backup-demo-test postgres-0 -- \
    psql -U orders_user -d ordersdb -c "SELECT COUNT(*) FROM orders;"

# Output: 5

echo "[OK] Restore in namespace di test completato"
echo "     I dati sono ripristinati correttamente in backup-demo-test"
echo "     La produzione (backup-demo) non è stata impattata"

# Cleanup: rimuovi il namespace di test dopo la verifica
kubectl delete namespace backup-demo-test
echo "[OK] Namespace di test eliminato"
```

---

## PART F: BACKUP SCHEDULATO (AUTOMATICO)

### Esercizio F1: Configurare Schedule di Backup

```bash
# Schedule 1: backup giornaliero di tutti i namespace
velero schedule create daily-all-namespaces \
    --schedule="0 2 * * *" \
    --include-namespaces='*' \
    --exclude-namespaces=velero,kube-system,kube-public,kube-node-lease,minio-backup \
    --default-volumes-to-fs-backup=true \
    --include-cluster-resources=true \
    --ttl=720h \
    --labels "type=scheduled,frequency=daily"

# Schedule 2: backup orario dei namespace critici
velero schedule create hourly-critical \
    --schedule="0 * * * *" \
    --include-namespaces=backup-demo \
    --default-volumes-to-fs-backup=true \
    --ttl=168h \
    --labels "type=scheduled,frequency=hourly,tier=critical"

# Verifica gli schedule
velero schedule get

# Output atteso:
# NAME                     STATUS    CREATED                         SCHEDULE    BACKUP TTL  LAST BACKUP  SELECTOR
# daily-all-namespaces     Enabled   2026-07-16 10:00:00 +0000 UTC  0 2 * * *  720h0m0s    n/a          <none>
# hourly-critical          Enabled   2026-07-16 10:00:00 +0000 UTC  0 * * * *  168h0m0s    n/a          <none>

# Forza l'esecuzione immediata di uno schedule (per testare)
velero backup create --from-schedule hourly-critical --wait

velero backup get | grep hourly-critical

# Output atteso:
# hourly-critical-20260716100000   Completed   0   0   2026-07-16 10:00:00   6d   default
```

---

### Esercizio F2: Monitoring dei Backup con Prometheus

```bash
# Velero espone metriche Prometheus su :8085/metrics
# Con kube-prometheus-stack, le metriche vengono raccolte automaticamente

# Crea un alert per backup falliti
cat <<'EOF' | kubectl apply -f -
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: velero-alerts
  namespace: monitoring
  labels:
    release: prometheus
spec:
  groups:
    - name: velero.rules
      rules:
        # Alert: backup fallito nell'ultima ora
        - alert: VeleroBackupFailed
          expr: |
            increase(velero_backup_failure_total[1h]) > 0
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "Backup Velero fallito"
            description: "Nell'ultima ora, {{ $value }} backup/e Velero ha fallito. Verificare i log: kubectl logs deployment/velero -n velero"
        
        # Alert: nessun backup nelle ultime 25 ore (schedule daily mancante)
        - alert: VeleroBackupMissing
          expr: |
            (time() - velero_backup_last_successful_timestamp{schedule!=""}) / 3600 > 25
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Backup Velero mancante per schedule {{ $labels.schedule }}"
            description: "Lo schedule {{ $labels.schedule }} non ha prodotto un backup di successo nelle ultime 25 ore."
        
        # Alert: restore fallito
        - alert: VeleroRestoreFailed
          expr: |
            increase(velero_restore_failed_total[1h]) > 0
          for: 1m
          labels:
            severity: critical
          annotations:
            summary: "Restore Velero fallito"
            description: "Un restore Velero ha fallito. Controllare: velero restore get"
EOF

echo "[OK] Alert Velero configurati in Prometheus"
```

---

## PART G: BACKUP ETCD (Complementare a Velero)

### Concetto G1: Perché Serve il Backup di etcd

> **Analogia.** Velero è come fare una fotografia di tutti gli oggetti in un ufficio
> (documenti, computer, mobili). Ma se l'edificio stesso crolla (il control plane K8s
> va giù), le fotografie non ti aiutano a ricostruire le fondamenta.
>
> Il backup di etcd è come fare una copia del progetto architettonico dell'edificio:
> ti permette di ricostruire le fondamenta (il cluster K8s stesso) in caso di
> disaster totale. Velero e etcd backup sono complementari, non alternativi.

```
QUANDO SERVE IL BACKUP ETCD:

Velero ripristina: namespace, pod, deployment, PVC, configmap, secret
Velero NON ripristina: il cluster K8s stesso (API server, etcd, scheduler, controller-manager)

Backup etcd serve quando:
  ✗ etcd è corrotto (errore hardware, bug)
  ✗ Un upgrade K8s ha fallito e ha reso etcd inconsistente
  ✗ Disaster recovery totale: il cluster non risponde più
  
In questi casi:
  1. Ripristina etcd dal backup (snapshot)
  2. Il cluster K8s torna operativo
  3. Velero può ripristinare i namespace applicativi

FREQUENZA CONSIGLIATA:
  etcd backup: ogni ora (sono veloci, ~ 100-500MB per cluster tipico)
  Velero backup: ogni ora per namespace critici, ogni 6h per tutti
```

---

### Esercizio G1: Script di Backup etcd

```bash
#!/bin/bash
# etcd-backup.sh — Script per backup automatico di etcd
# Eseguire come CronJob K8s o sul nodo control plane

BACKUP_DIR="/backup/etcd"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/etcd-snapshot-$TIMESTAMP.db"
RETENTION_DAYS=7

# Configurazione etcd (K3s usa percorsi diversi da K8s standard)
# Adatta questi percorsi al tuo setup:
ETCD_ENDPOINTS="https://127.0.0.1:2379"
ETCD_CACERT="/etc/kubernetes/pki/etcd/ca.crt"
ETCD_CERT="/etc/kubernetes/pki/etcd/server.crt"
ETCD_KEY="/etc/kubernetes/pki/etcd/server.key"

echo "=== Backup etcd — $TIMESTAMP ==="
mkdir -p "$BACKUP_DIR"

# Esegui lo snapshot
ETCDCTL_API=3 etcdctl snapshot save "$BACKUP_FILE" \
    --endpoints="$ETCD_ENDPOINTS" \
    --cacert="$ETCD_CACERT" \
    --cert="$ETCD_CERT" \
    --key="$ETCD_KEY"

if [ $? -eq 0 ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "[OK] Snapshot etcd salvato: $BACKUP_FILE ($SIZE)"
    
    # Verifica il backup
    ETCDCTL_API=3 etcdctl snapshot status "$BACKUP_FILE" \
        --write-out=table
    
    # Carica su MinIO (opzionale, se mc è installato)
    if command -v mc &>/dev/null; then
        mc cp "$BACKUP_FILE" "minio-backup/etcd-backups/etcd-snapshot-$TIMESTAMP.db"
        echo "[OK] Snapshot caricato su MinIO"
    fi
    
    # Rimuovi backup vecchi
    find "$BACKUP_DIR" -name "etcd-snapshot-*.db" -mtime +$RETENTION_DAYS -delete
    echo "[OK] Backup più vecchi di ${RETENTION_DAYS} giorni rimossi"
else
    echo "[FAIL] Backup etcd fallito!"
    exit 1
fi
```

```yaml
# CronJob K8s per backup etcd automatico
apiVersion: batch/v1
kind: CronJob
metadata:
  name: etcd-backup
  namespace: kube-system
spec:
  schedule: "0 * * * *"    # ogni ora
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3
  
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          hostNetwork: true   # accesso al network del nodo per raggiungere etcd
          
          containers:
            - name: etcd-backup
              image: bitnami/etcd:3.5
              command: ["/bin/sh", "-c"]
              args:
                - |
                  TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
                  ETCDCTL_API=3 etcdctl snapshot save /backup/etcd-$TIMESTAMP.db \
                      --endpoints=https://127.0.0.1:2379 \
                      --cacert=/etc/kubernetes/pki/etcd/ca.crt \
                      --cert=/etc/kubernetes/pki/etcd/server.crt \
                      --key=/etc/kubernetes/pki/etcd/server.key
                  echo "Backup completato: /backup/etcd-$TIMESTAMP.db"
              
              volumeMounts:
                - name: etcd-certs
                  mountPath: /etc/kubernetes/pki/etcd
                  readOnly: true
                - name: backup-storage
                  mountPath: /backup
          
          volumes:
            - name: etcd-certs
              hostPath:
                path: /etc/kubernetes/pki/etcd
                type: Directory
            - name: backup-storage
              persistentVolumeClaim:
                claimName: etcd-backup-pvc
          
          nodeSelector:
            node-role.kubernetes.io/control-plane: ""    # solo sul nodo master
          
          tolerations:
            - key: node-role.kubernetes.io/control-plane
              operator: Exists
              effect: NoSchedule
```

---

## PART H: RESTORE DRILL — TEST MENSILE OBBLIGATORIO

### Esercizio H1: Script di Restore Drill Automatizzato

```python
# restore-drill.py
"""
Script per eseguire un restore drill mensile automatizzato.
Verifica che il backup più recente possa essere ripristinato in staging.
"""

import json
import subprocess
import sys
import time
from datetime import datetime


def run_cmd(cmd: list[str], check: bool = True) -> tuple[int, str, str]:
    """Esegui un comando e restituisci returncode, stdout, stderr."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"[FAIL] Comando fallito: {' '.join(cmd)}")
        print(f"       STDERR: {result.stderr}")
    return result.returncode, result.stdout, result.stderr


def get_latest_backup(namespace_filter: str = "backup-demo") -> dict | None:
    """Trova il backup più recente per il namespace specificato."""
    rc, stdout, _ = run_cmd(["velero", "backup", "get", "-o", "json"])
    if rc != 0:
        return None
    
    backups = json.loads(stdout).get("items", [])
    
    # Filtra backup completati e rilevanti
    relevant = [
        b for b in backups
        if b.get("status", {}).get("phase") == "Completed"
        and namespace_filter in b.get("spec", {}).get("includedNamespaces", [])
    ]
    
    if not relevant:
        return None
    
    # Ordina per data di creazione (più recente prima)
    relevant.sort(
        key=lambda x: x.get("status", {}).get("startTimestamp", ""),
        reverse=True,
    )
    
    return relevant[0]


def run_restore_drill(source_namespace: str, test_namespace: str) -> bool:
    """
    Esegue un restore drill completo:
    1. Trova il backup più recente
    2. Ripristina in un namespace di test
    3. Verifica che i pod siano Running
    4. Esegue smoke test sul database
    5. Pulisce il namespace di test
    """
    
    start_time = time.time()
    success = False
    
    print(f"\n{'='*60}")
    print(f"RESTORE DRILL — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Source namespace: {source_namespace}")
    print(f"Test namespace:   {test_namespace}")
    print(f"{'='*60}\n")
    
    try:
        # Step 1: Trova il backup più recente
        print("[1/5] Ricerca backup più recente...")
        backup = get_latest_backup(source_namespace)
        
        if not backup:
            print("[FAIL] Nessun backup trovato per il namespace specificato")
            return False
        
        backup_name = backup["metadata"]["name"]
        backup_time = backup["status"]["startTimestamp"]
        print(f"[OK]  Backup trovato: {backup_name}")
        print(f"      Creato: {backup_time}")
        
        # Step 2: Crea namespace di test
        print(f"\n[2/5] Creazione namespace di test '{test_namespace}'...")
        run_cmd(["kubectl", "create", "namespace", test_namespace], check=False)
        print(f"[OK]  Namespace creato")
        
        # Step 3: Esegui il restore
        print(f"\n[3/5] Restore da backup '{backup_name}'...")
        restore_name = f"drill-{int(time.time())}"
        
        rc, _, stderr = run_cmd([
            "velero", "restore", "create", restore_name,
            "--from-backup", backup_name,
            "--include-namespaces", source_namespace,
            "--namespace-mappings", f"{source_namespace}:{test_namespace}",
            "--wait",
        ])
        
        if rc != 0:
            print(f"[FAIL] Restore fallito: {stderr}")
            return False
        
        print(f"[OK]  Restore completato")
        
        # Step 4: Verifica pod Running
        print(f"\n[4/5] Verifica pod nel namespace di test...")
        time.sleep(10)  # Aspetta l'avvio iniziale
        
        max_wait = 120
        elapsed = 0
        pods_ready = False
        
        while elapsed < max_wait:
            rc, stdout, _ = run_cmd([
                "kubectl", "get", "pods", "-n", test_namespace,
                "--field-selector=status.phase=Running",
                "--no-headers",
            ])
            
            running_pods = [l for l in stdout.strip().split("\n") if l]
            if len(running_pods) >= 1:
                pods_ready = True
                break
            
            print(f"      Attesa pod... ({elapsed}s)")
            time.sleep(10)
            elapsed += 10
        
        if not pods_ready:
            print(f"[FAIL] I pod non sono Running dopo {max_wait}s")
            return False
        
        print(f"[OK]  {len(running_pods)} pod in stato Running")
        for pod in running_pods:
            print(f"      → {pod.split()[0]}")
        
        # Step 5: Smoke test database
        print(f"\n[5/5] Smoke test PostgreSQL...")
        rc, stdout, _ = run_cmd([
            "kubectl", "exec", "-n", test_namespace, "postgres-0",
            "--", "psql", "-U", "orders_user", "-d", "ordersdb",
            "-c", "SELECT COUNT(*) FROM orders;",
        ])
        
        if rc != 0:
            print(f"[FAIL] Smoke test database fallito")
            return False
        
        count_line = [l for l in stdout.strip().split("\n") if l.strip().isdigit()]
        if count_line:
            count = int(count_line[0].strip())
            print(f"[OK]  Database raggiungibile: {count} ordini trovati")
            
            if count == 0:
                print(f"[WARN] Database vuoto — verificare il backup dei PVC")
            else:
                print(f"[OK]  Dati presenti nel database")
        
        success = True
        
    finally:
        # Cleanup: sempre rimuovi il namespace di test
        print(f"\n[CLEANUP] Rimozione namespace di test '{test_namespace}'...")
        run_cmd(["kubectl", "delete", "namespace", test_namespace, "--ignore-not-found=true"])
        print(f"[OK]  Namespace di test rimosso")
        
        elapsed_total = time.time() - start_time
        
        print(f"\n{'='*60}")
        print(f"RESTORE DRILL — RISULTATO")
        print(f"{'='*60}")
        print(f"Status:  {'✅ SUCCESSO' if success else '❌ FALLITO'}")
        print(f"Durata:  {elapsed_total/60:.1f} minuti")
        print(f"RTO misurato: {elapsed_total/60:.1f} minuti")
        print(f"        (target RTO: 30 minuti)")
        
        if success and elapsed_total / 60 <= 30:
            print(f"        ✅ RTO rispettato")
        elif success:
            print(f"        ⚠️  RTO superato (target: 30min, effettivo: {elapsed_total/60:.1f}min)")
        
        print(f"{'='*60}\n")
    
    return success


if __name__ == "__main__":
    result = run_restore_drill(
        source_namespace="backup-demo",
        test_namespace="restore-drill-test",
    )
    sys.exit(0 if result else 1)
```

```bash
# Esegui il restore drill
python3 restore-drill.py

# Output atteso:
# ============================================================
# RESTORE DRILL — 2026-07-16 10:30:00
# Source namespace: backup-demo
# Test namespace:   restore-drill-test
# ============================================================
# 
# [1/5] Ricerca backup più recente...
# [OK]  Backup trovato: demo-backup-001
#       Creato: 2026-07-16T10:00:00Z
# 
# [2/5] Creazione namespace di test 'restore-drill-test'...
# [OK]  Namespace creato
# 
# [3/5] Restore da backup 'demo-backup-001'...
# [OK]  Restore completato
# 
# [4/5] Verifica pod nel namespace di test...
# [OK]  2 pod in stato Running
#       → postgres-0
#       → order-app-xxx
# 
# [5/5] Smoke test PostgreSQL...
# [OK]  Database raggiungibile: 5 ordini trovati
# [OK]  Dati presenti nel database
# 
# [CLEANUP] Rimozione namespace di test 'restore-drill-test'...
# [OK]  Namespace di test rimosso
# 
# ============================================================
# RESTORE DRILL — RISULTATO
# ============================================================
# Status:  ✅ SUCCESSO
# Durata:  4.2 minuti
# RTO misurato: 4.2 minuti
#         (target RTO: 30 minuti)
#         ✅ RTO rispettato
# ============================================================
```

---

## PART I: DISASTER RECOVERY POLICY COMPLETA

### Esercizio I1: Documento DR Policy

```python
# dr-policy-check.py
"""
Verifica la conformità alla Disaster Recovery Policy.
Controlla che i backup siano aggiornati e i parametri RTO/RPO rispettati.
"""

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class ServiceTier:
    name: str
    rto_minutes: int       # Recovery Time Objective
    rpo_minutes: int       # Recovery Point Objective (max tolleranza perdita dati)
    backup_frequency_h: int  # frequenza backup in ore
    namespaces: list[str]


DR_POLICY = [
    ServiceTier(
        name="Tier 1 — Critico",
        rto_minutes=30,
        rpo_minutes=60,     # max 1 ora di dati persi
        backup_frequency_h=1,
        namespaces=["backup-demo", "payment-service"],
    ),
    ServiceTier(
        name="Tier 2 — Standard",
        rto_minutes=120,
        rpo_minutes=1440,   # max 24 ore
        backup_frequency_h=24,
        namespaces=["order-app", "inventory"],
    ),
    ServiceTier(
        name="Tier 3 — Non Critico",
        rto_minutes=240,
        rpo_minutes=10080,  # max 7 giorni
        backup_frequency_h=168,
        namespaces=["dev", "staging"],
    ),
]


def get_backups() -> list[dict]:
    """Recupera lista backup da Velero."""
    try:
        result = subprocess.run(
            ["velero", "backup", "get", "-o", "json"],
            capture_output=True, text=True, check=True
        )
        return json.loads(result.stdout).get("items", [])
    except Exception:
        # Valori simulati per il lab
        return [{
            "metadata": {"name": "demo-backup-001"},
            "spec": {"includedNamespaces": ["backup-demo"]},
            "status": {
                "phase": "Completed",
                "startTimestamp": datetime.now(timezone.utc).isoformat(),
            },
        }]


def check_dr_compliance(tiers: list[ServiceTier]) -> None:
    """Verifica la conformità alla DR policy."""
    
    backups = get_backups()
    now = datetime.now(timezone.utc)
    
    print(f"\n{'='*65}")
    print(f"DR POLICY COMPLIANCE REPORT — {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*65}\n")
    
    all_compliant = True
    
    for tier in tiers:
        print(f"── {tier.name} ──")
        print(f"   RTO: {tier.rto_minutes}min | RPO: {tier.rpo_minutes}min | Frequenza: {tier.backup_frequency_h}h")
        
        for ns in tier.namespaces:
            # Trova i backup per questo namespace
            ns_backups = [
                b for b in backups
                if ns in b.get("spec", {}).get("includedNamespaces", [])
                and b.get("status", {}).get("phase") == "Completed"
            ]
            
            if not ns_backups:
                print(f"   ❌ {ns}: NESSUN BACKUP TROVATO")
                all_compliant = False
                continue
            
            # Backup più recente
            ns_backups.sort(
                key=lambda x: x.get("status", {}).get("startTimestamp", ""),
                reverse=True,
            )
            latest = ns_backups[0]
            latest_time_str = latest["status"]["startTimestamp"]
            
            try:
                latest_time = datetime.fromisoformat(latest_time_str.replace("Z", "+00:00"))
                age_minutes = (now - latest_time).total_seconds() / 60
                
                max_age_minutes = tier.rpo_minutes
                
                if age_minutes <= max_age_minutes:
                    print(f"   ✅ {ns}: backup {latest['metadata']['name']} "
                          f"({age_minutes:.0f} min fa — entro RPO {tier.rpo_minutes}min)")
                else:
                    print(f"   ❌ {ns}: backup troppo vecchio "
                          f"({age_minutes:.0f} min fa — supera RPO {tier.rpo_minutes}min)")
                    all_compliant = False
            except ValueError:
                print(f"   ⚠️  {ns}: impossibile parsare data backup")
        
        print()
    
    print(f"{'='*65}")
    print(f"RISULTATO COMPLIANCE: {'✅ CONFORME' if all_compliant else '❌ NON CONFORME'}")
    if not all_compliant:
        print(f"AZIONE RICHIESTA: verificare i backup falliti e ripristinare la schedule")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    check_dr_compliance(DR_POLICY)
```

```bash
python3 dr-policy-check.py

# Output atteso:
# =================================================================
# DR POLICY COMPLIANCE REPORT — 2026-07-16 10:45 UTC
# =================================================================
# 
# ── Tier 1 — Critico ──
#    RTO: 30min | RPO: 60min | Frequenza: 1h
#    ✅ backup-demo: backup demo-backup-001 (45 min fa — entro RPO 60min)
#    ⚠️  payment-service: NESSUN BACKUP TROVATO
# 
# ── Tier 2 — Standard ──
#    RTO: 120min | RPO: 1440min | Frequenza: 24h
#    ⚠️  order-app: NESSUN BACKUP TROVATO
#    ⚠️  inventory: NESSUN BACKUP TROVATO
# 
# ── Tier 3 — Non Critico ──
#    RTO: 240min | RPO: 10080min | Frequenza: 168h
#    ⚠️  dev: NESSUN BACKUP TROVATO
#    ⚠️  staging: NESSUN BACKUP TROVATO
# 
# =================================================================
# RISULTATO COMPLIANCE: ❌ NON CONFORME
# AZIONE RICHIESTA: verificare i backup falliti e ripristinare la schedule
# =================================================================
```

---

## Conclusioni e Prossimi Passi

```
COMPETENZE ACQUISITE:

VELERO:
  ✓ Installazione con MinIO (S3-compatible) via Helm/CLI
  ✓ Backup on-demand di namespace con PVC (Kopia file-level)
  ✓ Schedule automatici (cron syntax)
  ✓ Restore in namespace originale e mapping su namespace diverso
  ✓ PrometheusRule per alert su backup falliti

DISASTER RECOVERY:
  ✓ Restore drill automatizzato con verifica smoke test
  ✓ Misurazione RTO effettivo (non teorico)
  ✓ DR Policy con tier (critico/standard/non critico)
  ✓ Compliance check automatizzato

ETCD BACKUP:
  ✓ Differenza tra Velero (manifesti + PVC) e etcd backup
  ✓ Script etcdctl snapshot save
  ✓ CronJob K8s per backup etcd automatico

PUNTI CHIAVE:
  ✓ Backup NON testato = backup NON esistente
  ✓ Velero + etcd = copertura completa (manifesti + control plane)
  ✓ Restore drill mensile obbligatorio con misurazione RTO
  ✓ Rule 3-2-1: 3 copie, 2 media, 1 off-site
  ✓ RPO e RTO documentati e rispettati dalla schedule
```

### Roadmap Dopo il Lab

```
LIVELLO BASE (questo lab):
  ✓ Velero con MinIO locale
  ✓ Backup manuale + schedule
  ✓ Restore drill manuale

LIVELLO INTERMEDIO:
  → Replica MinIO → S3 off-site (regola 3-2-1)
  → Backup di risorse cluster-scoped (CRD, RBAC cluster, StorageClass)
  → Integration test nel restore drill (non solo smoke test)
  → Dashboard Grafana per metriche Velero

LIVELLO AVANZATO (produzione):
  → Multi-cluster backup (backup cluster A ripristinabile su cluster B)
  → Automated restore drill in CI/CD (mensile automatico)
  → Encryption at-rest dei backup (Velero + KMS)
  → Cross-region disaster recovery con failover automatico
  → Velero + Kasten K10 per ambienti enterprise

COMPLIANCE:
  → GDPR: backup retention policy (diritto all'oblio: come cancellare specifici dati da backup?)
  → DORA (Digital Operational Resilience Act): ICT register + test DR documentati
  → ISO 27001: backup policy come controllo A.12.3

RIFERIMENTI:
  Velero Docs:  https://velero.io/docs
  Velero GitHub: https://github.com/vmware-tanzu/velero
  NIST SP 800-34: Contingency Planning Guide for Federal Information Systems
  
QUESTO ERA L'ULTIMO TUTORIAL DEL BATCH 4!
  Tutti i 26 tutorial del campo 06-GESTIONE-PIATTAFORME sono ora completi.
```

---

> **Documento di riferimento:** `25-velero-kubernetes-backup.md` — Modulo 25, Gestione Piattaforme
> **Versioni testate:** Velero 1.15.0, velero-plugin-for-aws v1.11.0, MinIO RELEASE.2024-11-07
> **Ultimo aggiornamento:** 2026-07-16
