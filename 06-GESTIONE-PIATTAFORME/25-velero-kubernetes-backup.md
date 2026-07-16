---
corso: "Gestione Piattaforme e DevOps"
fase: "7 — Architetture Avanzate"
modulo: 25
titolo: "Backup e Ripristino Kubernetes con Velero"
versione: "Velero 1.15 · Restic 0.17 · MinIO RELEASE.2024 · kopia 0.18"
livello: "Avanzato"
prerequisiti:
  - "05-kubernetes.md"
  - "17-storage-distribuito.md"
obiettivi:
  - "Comprendere le strategie di backup K8s (etcd, PVC, manifesti)"
  - "Installare e configurare Velero con MinIO come backend di storage"
  - "Eseguire backup on-demand e schedulati di namespace e cluster completo"
  - "Ripristinare da backup (namespace, risorse selettive, cluster diverso)"
  - "Implementare una disaster recovery policy con RTO/RPO documentati"
tag: [velero, backup, kubernetes, disaster-recovery, rto-rpo, etcd, pvc, minio, restic]
---

# Backup e Ripristino Kubernetes con Velero — Documentazione Completa

> **Modulo 25** · **Aggiornamento:** 2026-07-16

## 1. Perché il Backup K8s è Diverso

Backup in Kubernetes è più complesso che in sistemi tradizionali perché lo stato
è distribuito in più luoghi.

```
DOVE VIVE LO STATO IN KUBERNETES:

1. etcd (database K8s):
   Contiene: tutti i manifesti K8s (Pod, Deployment, Service, ConfigMap, Secret, CRD, RBAC)
   Backup: etcdctl snapshot save
   Rischio: corruzione etcd → cluster irrecuperabile senza backup
   
2. Persistent Volumes (PVC):
   Contiene: dati delle applicazioni (database, file, etc.)
   Backup: CSI snapshot, Restic, Kopia
   Rischio: dati applicazione persi
   
3. Container Registry:
   Contiene: immagini Docker
   Backup: replication del registry su più region
   Rischio: perdita di un'immagine specifica (gestibile con immutable tags)

4. Git (GitOps):
   Contiene: manifesti K8s, configurazione
   Backup: GitHub/GitLab con repliche
   Rischio: perdita della history Git

STRUMENTI DI BACKUP K8s:
  Velero:    backup di manifesti K8s + PVC (via Restic/Kopia)
  etcdctl:   backup diretto di etcd
  Kasten K10: enterprise backup per K8s (SaaS)
  Stash:     backup K8s + plugin per DB (appuniclabs)
  CloudCasa: SaaS backup K8s
  
  RACCOMANDAZIONE:
  Velero: backup manifesti + PVC, open source, community CNCF
  etcdctl: backup etcd separato (Velero non fa backup di etcd)
  Entrambi necessari per un disaster recovery completo
```

---

## 2. Velero — Architettura

```
ARCHITETTURA VELERO:

velero (client CLI):
  Interagisce con l'API K8s per creare oggetti Backup/Restore/Schedule

velero-server (in-cluster):
  Componente server che esegue i backup/restore
  Watch su oggetti Backup/Restore/Schedule

velero-node-agent (daemonset):
  Un pod su ogni nodo
  Esegue il backup dei PVC tramite Restic o Kopia (file-level backup)

Object Storage (MinIO/S3/GCS/Azure Blob):
  Dove vengono salvati i backup
  Struttura: velero/backups/<nome-backup>/

OGGETTI CRD VELERO:
  Backup:         un singolo backup (on-demand o generato da Schedule)
  Restore:        un singolo restore da un Backup
  Schedule:       schedulazione di backup periodici (cron syntax)
  BackupLocation: dove salvare i backup (S3, GCS, Azure)
  VolumeSnapshotLocation: dove salvare le snapshot dei PVC
  
PLUGIN STORAGE:
  AWS S3:         velero-plugin-for-aws
  GCS:            velero-plugin-for-gcp
  Azure Blob:     velero-plugin-for-microsoft-azure
  MinIO/S3-compat: velero-plugin-for-aws (usa MinIO endpoint custom)
  
FILE BACKUP (PVC):
  Restic:  storico, stabile, più lento
  Kopia:   moderno, più veloce, raccomandata da Velero 1.12+
```

---

## 3. Backup vs Snapshot — Differenze Critiche

```
VELERO BACKUP MANIFESTI (sempre inclusi):
  ✓ Tutti gli oggetti K8s nel namespace: Deployment, Service, ConfigMap, Secret, RBAC
  ✓ Metadata: labels, annotations, ownerReferences
  ✓ CRD (opzionale: --include-cluster-resources)
  ✗ NON include: dati nei PersistentVolume
  
  Usato per: ripristinare la configurazione dell'applicazione

VELERO BACKUP PVC CON RESTIC/KOPIA:
  ✓ Backup file-level dei dati nei PVC (file, directory)
  ✓ Deduplica e compressione
  ✓ Incrementale
  ✗ Richiede: annotazione sul pod (opt-in) o --default-volumes-to-fs-backup
  ✗ Più lento delle snapshot CSI
  
  Usato per: backup completo dei dati applicazione (database, file)

CSI SNAPSHOT (alternativo a Restic/Kopia):
  ✓ Velocissimo (snapshot a livello di storage, non file)
  ✓ Application-consistent (se il driver CSI lo supporta)
  ✗ Richiede: CSI driver che supporti VolumeSnapshot
  ✗ Snapshot nello stesso storage (non off-site)
  
  Usato per: backup veloci di volumi grandi, pre-upgrade

RTO/RPO TIPICI:
  Velero + Restic: RPO = frequenza schedule, RTO = 15-60 minuti (dipende da size)
  CSI snapshot:    RPO = frequenza schedule, RTO = 5-15 minuti
  etcd snapshot:   RPO = frequenza schedule, RTO = 30-120 minuti (rebuild cluster)
```

---

## 4. Configurazione Velero con MinIO

```yaml
# Configurazione BackupStorageLocation per MinIO (S3-compatible)
apiVersion: velero.io/v1
kind: BackupStorageLocation
metadata:
  name: default
  namespace: velero
spec:
  provider: aws         # usa il plugin AWS (compatibile con MinIO)
  
  objectStorage:
    bucket: velero-backups
    prefix: cluster-production   # organizza per cluster
  
  config:
    region: minio            # nome arbitrario per MinIO
    s3ForcePathStyle: "true"  # MinIO richiede path-style (non virtual-hosted)
    s3Url: http://minio.storage.svc.cluster.local:9000
    publicUrl: http://minio.internal:9000

---
# Secret con credenziali MinIO
apiVersion: v1
kind: Secret
metadata:
  name: cloud-credentials
  namespace: velero
type: Opaque
stringData:
  cloud: |
    [default]
    aws_access_key_id = velero-user
    aws_secret_access_key = velero-password-change-in-production
```

---

## 5. Schedule — Backup Automatici

```yaml
# Schedule: backup giornaliero di tutti i namespace (escluso kube-system)
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: daily-full-backup
  namespace: velero
spec:
  schedule: "0 2 * * *"    # ogni giorno alle 02:00 UTC
  
  template:
    includedNamespaces:
      - "*"                  # tutti i namespace
    excludedNamespaces:
      - kube-system          # non necessario (solo manifesti K8s interni)
      - kube-public
      - kube-node-lease
      - velero               # evita auto-backup di Velero stesso
    
    # Backup anche delle risorse cluster-scoped (RBAC, CRD, StorageClass)
    includeClusterResources: true
    
    # Backup dei PVC con Kopia (file-level backup)
    defaultVolumesToFsBackup: true
    
    # Retention: quante copie tenere
    ttl: 720h    # 30 giorni (720 ore)
    
    # Labels per identificare il backup
    storageLocation: default
    
    labels:
      backup-type: scheduled
      schedule: daily

---
# Schedule: backup orario solo namespace critici
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: hourly-critical-backup
  namespace: velero
spec:
  schedule: "0 * * * *"    # ogni ora
  template:
    includedNamespaces:
      - payment-service    # namespace critici
      - orders-service
    defaultVolumesToFsBackup: true
    ttl: 168h              # 7 giorni
    storageLocation: default
    labels:
      backup-type: scheduled
      schedule: hourly
      tier: critical
```

---

## 6. Restore — Ripristino da Backup

```yaml
# Restore: ripristino di un namespace specifico
apiVersion: velero.io/v1
kind: Restore
metadata:
  name: restore-orders-20260715
  namespace: velero
spec:
  backupName: daily-full-backup-20260715020000    # nome del backup da cui ripristinare
  
  includedNamespaces:
    - orders-service         # solo questo namespace
  
  # Ripristina i PVC (file-level)
  restorePVs: true
  
  # Mapping namespace: ripristina in un namespace diverso
  # (utile per test del ripristino senza impattare la produzione)
  namespaceMapping:
    orders-service: orders-service-restore-test
  
  # Escludi risorse già presenti (non sovrascrivere)
  existingResourcePolicy: none   # none | update

---
# Restore parziale: solo certi tipi di risorse
apiVersion: velero.io/v1
kind: Restore
metadata:
  name: restore-configmaps-only
  namespace: velero
spec:
  backupName: daily-full-backup-20260715020000
  includedNamespaces:
    - orders-service
  includedResources:
    - configmaps
    - secrets
  restorePVs: false    # non ripristinare i dati
```

---

## 7. Disaster Recovery Policy

```
DISASTER RECOVERY POLICY — VELERO:

TIER 1 — CRITICO (payment, orders, auth):
  RPO (Recovery Point Objective): 1 ora
  RTO (Recovery Time Objective):  30 minuti
  
  Backup: ogni ora con Kopia (PVC) + manifesti
  Test: restore drill mensile in ambiente staging
  Location: MinIO on-prem + replica su S3 off-site
  Retention: 30 giorni
  
TIER 2 — STANDARD (frontend, reporting, analytics):
  RPO: 24 ore
  RTO: 2 ore
  
  Backup: giornaliero alle 02:00
  Test: restore drill trimestrale
  Location: MinIO on-prem
  Retention: 30 giorni
  
TIER 3 — NON CRITICO (dev, staging, test):
  RPO: 7 giorni
  RTO: 4 ore
  
  Backup: settimanale
  Test: annuale
  Location: MinIO on-prem
  Retention: 7 giorni

DISASTER RECOVERY RUNBOOK:

Scenario 1: Namespace corrotto/cancellato accidentalmente
  1. kubectl velero backup get → trova il backup più recente
  2. kubectl velero restore create --from-backup <nome-backup> --include-namespaces <ns>
  3. Monitora il restore: kubectl velero restore describe <restore-name>
  4. Verifica: kubectl get pods -n <ns>
  Tempo atteso: 5-30 minuti (dipende da size PVC)

Scenario 2: Cluster completo perso (disaster recovery su nuovo cluster)
  1. Installa Velero sul nuovo cluster con le stesse credenziali MinIO
  2. Configura BackupStorageLocation con stesso bucket
  3. Velero sincronizza la lista dei backup disponibili
  4. Esegui restore completo: velero restore create --from-backup <backup>
  5. Rindirizza il DNS al nuovo cluster
  Tempo atteso: 30-120 minuti

Scenario 3: Corruzione etcd (diverso da perdita dati applicazione)
  1. etcdctl snapshot restore <backup.db> --data-dir /var/lib/etcd-restore
  2. Riconfigura etcd per usare il data dir ripristinato
  3. Riavvia il cluster K8s
  NOTA: Velero NON gestisce questo scenario — richiede backup etcd separato
```

---

## 8. Best Practices Backup Kubernetes

```
REGOLE FONDAMENTALI:

1. BACKUP VERIFICATO = BACKUP TESTATO
   ✓ Restore drill mensile (non annuale)
   ✓ Test in ambiente staging, non solo "leggi la lista backup"
   ✓ Documenta il tempo effettivo di restore (per RTO realistico)
   ✗ Non: assumere che il backup funzioni senza testarlo

2. BACKUP MULTIPLI (3-2-1 rule):
   ✓ 3 copie dei dati
   ✓ 2 supporti/location diversi (es: MinIO locale + S3 off-site)
   ✓ 1 copia off-site (diversa regione geografica)

3. VELERO + etcd (backup complementari):
   ✓ Velero: manifesti + PVC (cosa gira nel cluster)
   ✓ etcd: database K8s (stato del control plane)
   ✗ Non: scegliere solo uno dei due

4. ANNOTAZIONI ESPLICITE PER PVC:
   ✓ Scegli modalità globale (--default-volumes-to-fs-backup) per backup completo
   ✓ O annotazione pod-level (backup.velero.io/backup-volumes) per selettivo
   ✗ Non: assumere che i PVC siano inclusi di default (Velero < 1.12)

5. RETENTION POLICY:
   ✓ Allinea TTL con i requisiti normativi (GDPR: considera anche il diritto all'oblio)
   ✓ Tiers diversi per criticità (30gg critici, 7gg standard)
   ✗ Non: retention illimitata (costi storage non controllati)

6. MONITORING:
   ✓ Alert su backup falliti (Velero Prometheus metrics: velero_backup_failure_total)
   ✓ Alert su backup scaduti/mancanti
   ✓ Dashboard Grafana per stato backup nel tempo

METRICHE VELERO (Prometheus):
  velero_backup_total:              numero totale di backup
  velero_backup_success_total:      backup riusciti
  velero_backup_failure_total:      backup falliti → alert!
  velero_backup_duration_seconds:   durata backup (istogramma)
  velero_restore_total:             restore totali
  velero_restore_failed_total:      restore falliti → alert!
```

---

> **Versioni di riferimento:** Velero 1.15 (2024-11, CNCF incubating),
> Restic 0.17 (2024), Kopia 0.18 (2024), MinIO RELEASE.2024-11-07.
> CSI spec v1.11 (VolumeSnapshot API stable da K8s 1.20).
> Disaster Recovery best practices: NIST SP 800-34 Rev.1 (Contingency Planning Guide).
> 3-2-1 backup rule: originariamente fotografica, ampiamente adottata in IT.
