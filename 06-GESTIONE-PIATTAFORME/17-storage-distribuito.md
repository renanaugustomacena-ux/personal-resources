---
corso: "Gestione Piattaforme e DevOps"
fase: "5 — Dati e Messaging"
modulo: 17
titolo: "Storage Distribuito"
versione: "Ceph 18.x (Reef); MinIO RELEASE.2024; Longhorn 1.6; Rook 1.14"
livello: "Avanzato"
prerequisiti: ["05-kubernetes", "11-database-management", "08-monitoring-observability"]
obiettivi:
  - "Progettare un cluster Ceph con replica e erasure coding per workload cloud-native"
  - "Deployare MinIO come object storage S3-compatible su Kubernetes"
  - "Configurare CSI driver, StorageClass e PVC per storage persistente in K8s"
  - "Implementare capacity planning e lifecycle management per volumi distribuiti"
  - "Valutare trade-off tra Ceph, MinIO, Longhorn e Rook-Ceph per scenari diversi"
tag: [storage, ceph, minio, csi, pvc, erasure-coding, longhorn, rook, kubernetes]
---

# Storage Distribuito — Documentazione Completa

> **Modulo 17** · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> Al completamento di questo modulo sarai in grado di:
> 1. Progettare un cluster Ceph con replica e erasure coding per workload cloud-native.
> 2. Deployare MinIO come object storage S3-compatible su Kubernetes.
> 3. Configurare CSI driver, StorageClass e PVC per storage persistente in K8s.
> 4. Implementare capacity planning e lifecycle management per volumi distribuiti.
> 5. Valutare trade-off tra Ceph, MinIO, Longhorn e Rook-Ceph per scenari diversi.

## Idee guida

1. **Ceph (block+file+object) per cloud-native private.**
2. **MinIO per S3-compatible object storage on-prem.**
3. **CSI driver per K8s.** PVC + StorageClass.
4. **Capacity planning: replica 3 = 33% efficiency; erasure coding 4+2 = 67%.**


## Indice

1. [Panoramica e Concetti Fondamentali](#1-panoramica-e-concetti-fondamentali)
2. [MinIO](#2-minio)
3. [Ceph](#3-ceph)
4. [GlusterFS](#4-glusterfs)
5. [S3-Compatible Storage](#5-s3-compatible-storage)
6. [NFS in Cloud e Container](#6-nfs-in-cloud-e-container)
7. [Storage su Kubernetes](#7-storage-su-kubernetes)
8. [Longhorn](#8-longhorn)
9. [OpenEBS](#9-openebs)
10. [Data Protection e Backup](#10-data-protection-e-backup)
11. [Performance e Tuning](#11-performance-e-tuning)
12. [Best Practices](#12-best-practices)
13. [Ceph Advanced](#13-ceph-advanced)
14. [MinIO Deep-Dive](#14-minio-deep-dive)
15. [Longhorn Deep-Dive](#15-longhorn-deep-dive)
16. [Storage Security](#16-storage-security)
17. [CSI Drivers Deep-Dive](#17-csi-drivers-deep-dive)
18. [Storage Monitoring Avanzato](#18-storage-monitoring-avanzato)
19. [Storage Performance Benchmarking Avanzato](#19-storage-performance-benchmarking-avanzato)
20. [Cloud Storage Comparison](#20-cloud-storage-comparison)

---

## 1. Panoramica e Concetti Fondamentali

### Tipi di Storage

Lo storage distribuito si classifica in tre categorie fondamentali, ciascuna con caratteristiche e casi d'uso distinti.

**Block Storage** espone dispositivi a blocchi raw ai sistemi operativi o alle applicazioni. Ogni blocco viene indirizzato individualmente e il filesystem viene gestito dal client. E' il tipo di storage con la latenza piu' bassa e il throughput piu' alto per operazioni sequenziali e random I/O.

Casi d'uso tipici: database (PostgreSQL, MySQL, MongoDB), virtual machines, applicazioni che richiedono accesso diretto al disco.

**File Storage** espone un filesystem gerarchico condiviso con directory e file. Supporta semantica POSIX (lock, permessi, hard/soft link) e consente accesso concorrente da parte di piu' client tramite protocolli come NFS o SMB/CIFS.

Casi d'uso tipici: home directory condivise, media repository, applicazioni legacy che richiedono un filesystem tradizionale.

**Object Storage** organizza i dati in oggetti piatti (flat namespace o con prefix-based hierarchy) composti da dati binari, metadati arbitrari e un identificatore univoco. Non supporta operazioni POSIX come lock o append in-place: ogni modifica sovrascrive l'intero oggetto.

Casi d'uso tipici: backup, archiving, data lake, content delivery, log storage, machine learning datasets.

### Storage Distribuito vs Centralizzato

Lo storage centralizzato (SAN, NAS singolo) offre semplicita' gestionale ma introduce un single point of failure e limiti di scalabilita' verticale. Lo storage distribuito distribuisce i dati su piu' nodi, offrendo:

- **Scalabilita' orizzontale**: aggiunta di nodi senza downtime
- **Fault tolerance**: sopravvivenza alla perdita di nodi multipli
- **Data locality**: dati vicini al compute che li utilizza
- **Throughput aggregato**: banda cumulativa di tutti i nodi

Il costo e' una complessita' operativa significativamente maggiore.

### Modelli di Consistenza

**Strong Consistency** garantisce che ogni lettura restituisca il valore dell'ultima scrittura completata. Tutte le repliche vedono lo stesso dato nello stesso istante. Impatto: latenza piu' alta per le scritture (attesa di quorum o conferma di tutte le repliche).

**Eventual Consistency** garantisce che, in assenza di ulteriori scritture, tutte le repliche convergeranno allo stesso valore. Nel frattempo, letture diverse possono restituire valori diversi. Impatto: latenza molto bassa per le scritture, adatto a workload dove la consistenza immediata non e' critica.

**Read-after-write Consistency** garantisce che, dopo una scrittura confermata, la lettura successiva dallo stesso client restituisca il valore scritto. Altre repliche possono essere ancora in ritardo.

### Replicazione

**Replicazione Sincrona**: la scrittura viene confermata solo quando tutte le repliche (o un quorum) hanno persistito il dato. Vantaggi: zero data loss (RPO = 0). Svantaggi: latenza proporzionale alla replica piu' lenta, impatto su throughput.

**Replicazione Asincrona**: la scrittura viene confermata appena il nodo primario ha persistito il dato. Le repliche vengono aggiornate in background. Vantaggi: latenza minima. Svantaggi: rischio di data loss in caso di failure del primario prima della propagazione.

### Erasure Coding

L'erasure coding divide un oggetto in `k` frammenti di dati e genera `m` frammenti di parita'. L'oggetto puo' essere ricostruito da qualsiasi `k` frammenti su `k+m` totali.

Esempio: con schema EC 4+2 (k=4, m=2), un oggetto viene diviso in 4 frammenti dati + 2 parita'. Puo' tollerare la perdita di 2 frammenti qualsiasi. L'overhead di storage e' del 50% (6/4 = 1.5x), rispetto al 200% della replicazione tripla (3x).

Tradeoff: l'erasure coding richiede piu' CPU per encode/decode e ha latenza di lettura superiore (deve leggere almeno k frammenti da nodi diversi).

### CAP Theorem Applicato allo Storage

Il teorema CAP stabilisce che un sistema distribuito puo' garantire al massimo due delle tre proprieta':

- **C (Consistency)**: tutti i nodi vedono lo stesso dato contemporaneamente
- **A (Availability)**: ogni richiesta riceve una risposta (successo o errore)
- **P (Partition tolerance)**: il sistema continua a funzionare nonostante perdita di messaggi tra nodi

In pratica, poiche' le partizioni di rete sono inevitabili, la scelta reale e' tra CP (consistente ma potenzialmente non disponibile durante partizioni) e AP (disponibile ma potenzialmente inconsistente).

Ceph sceglie **CP**: preferisce bloccare le operazioni piuttosto che restituire dati stale. MinIO in modalita' distribuita e' **CP** per le scritture (richiede quorum). GlusterFS con replica sincrona e' **CP**.

### Storage Tiers

| Tier     | Latenza       | Costo     | Uso                                    |
|----------|---------------|-----------|----------------------------------------|
| Hot      | < 1 ms        | Alto      | Database attivi, cache, real-time       |
| Warm     | 1-10 ms       | Medio     | Log recenti, dati analitici frequenti   |
| Cold     | 10-100 ms     | Basso     | Backup, log storici, compliance         |
| Archive  | secondi-ore   | Minimo    | Dati regolamentari, disaster recovery   |

### Data Locality

La data locality riduce la latenza posizionando i dati fisicamente vicino al compute. Strategie:

- **Rack awareness**: repliche distribuite tra rack diversi per fault tolerance
- **Zone awareness**: distribuzione tra zone di disponibilita'
- **Affinity rules**: scheduling dei workload sui nodi che ospitano i dati
- **Caching locale**: cache SSD locale per dati frequentemente acceduti da storage remoto

---

## 2. MinIO

### Architettura

MinIO e' un object storage ad alte prestazioni, compatibile con l'API S3 di AWS. L'architettura si basa su:

- **Erasure Coding**: MinIO divide ogni oggetto in frammenti di dati e parita' distribuiti su dischi e nodi. Lo schema di default e' EC:4 (meta' dati, meta' parita'), tollerando la perdita di meta' dei drive.
- **Bit-rot Healing**: ogni frammento viene verificato tramite hash (HighwayHash) ad ogni lettura. Frammenti corrotti vengono automaticamente rigenerati dalle copie sane.
- **Stateless architecture**: i nodi MinIO non mantengono stato in-memory. I metadati sono inline con gli oggetti sui dischi. Non esiste un metadata server separato.

### Installazione Single Node

```bash
# Download del binario
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/

# Creazione utente e directory dati
sudo useradd -r minio-user -s /sbin/nologin
sudo mkdir -p /data/minio
sudo chown minio-user:minio-user /data/minio

# Configurazione environment
sudo tee /etc/default/minio <<'ENVEOF'
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minio-secret-key-CHANGEME
MINIO_VOLUMES="/data/minio"
MINIO_OPTS="--console-address :9001"
ENVEOF

# Systemd service
sudo tee /etc/systemd/system/minio.service <<'SVCEOF'
[Unit]
Description=MinIO
Documentation=https://min.io/docs/minio/linux/index.html
Wants=network-online.target
After=network-online.target

[Service]
User=minio-user
Group=minio-user
EnvironmentFile=-/etc/default/minio
ExecStart=/usr/local/bin/minio server $MINIO_VOLUMES $MINIO_OPTS
Restart=always
RestartSec=5
LimitNOFILE=65536
TasksMax=infinity
TimeoutStopSec=infinity
SendSIGKILL=no

[Install]
WantedBy=multi-user.target
SVCEOF

sudo systemctl daemon-reload
sudo systemctl enable --now minio
sudo systemctl status minio
```

### Installazione Distributed Mode (Multi-Node)

Per un cluster distribuito con 4 nodi e 4 dischi ciascuno (16 dischi totali):

```bash
# Su ogni nodo: /etc/default/minio
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minio-secret-key-CHANGEME
MINIO_VOLUMES="http://minio{1...4}.example.com/data{1...4}/minio"
MINIO_OPTS="--console-address :9001"
MINIO_SERVER_URL="https://minio.example.com"
```

La sintassi `{1...4}` e' l'expansion syntax di MinIO (non bash expansion). MinIO richiede un minimo di 4 dischi per l'erasure coding distribuito.

### mc CLI (MinIO Client)

```bash
# Installazione
wget https://dl.min.io/client/mc/release/linux-amd64/mc
chmod +x mc && sudo mv mc /usr/local/bin/

# Configurazione alias
mc alias set local http://localhost:9000 minioadmin minio-secret-key-CHANGEME
mc alias set production https://minio.prod.example.com ACCESS_KEY SECRET_KEY

# Operazioni su bucket
mc mb local/my-bucket                          # Crea bucket
mc mb local/my-bucket --with-versioning        # Crea con versioning abilitato
mc ls local/                                   # Lista bucket
mc ls local/my-bucket --recursive              # Lista ricorsiva oggetti

# Upload e download
mc cp /path/to/file.tar.gz local/my-bucket/backups/
mc cp local/my-bucket/backups/file.tar.gz /tmp/restore/
mc cp --recursive /data/logs/ local/my-bucket/logs/

# Mirroring (sync bidirezionale)
mc mirror /data/source/ local/my-bucket/mirror/
mc mirror --watch /data/source/ local/my-bucket/mirror/   # Sync continuo

# Amministrazione
mc admin info local                            # Informazioni cluster
mc admin user add local newuser newpassword    # Aggiungi utente
mc admin policy attach local readwrite --user newuser
mc admin service restart local                 # Restart server
mc admin heal local/my-bucket --recursive      # Healing manuale
```

### Bucket Policies e IAM

```bash
# Policy personalizzata
cat > /tmp/readonly-policy.json <<'PEOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::my-bucket",
        "arn:aws:s3:::my-bucket/*"
      ]
    }
  ]
}
PEOF

mc admin policy create local readonly-mybucket /tmp/readonly-policy.json
mc admin policy attach local readonly-mybucket --user readonly-user
```

### Versioning e Object Locking

```bash
# Abilitare versioning
mc version enable local/compliance-bucket

# Object locking (WORM) — il bucket deve essere creato con lock abilitato
mc mb local/worm-bucket --with-lock
mc retention set --default COMPLIANCE 365d local/worm-bucket

# Impostare retention su un oggetto specifico
mc retention set GOVERNANCE 30d local/worm-bucket/document.pdf
```

### Lifecycle Management

```bash
# Configurazione lifecycle rules via JSON
cat > /tmp/lifecycle.json <<'LCEOF'
{
  "Rules": [
    {
      "ID": "expire-old-logs",
      "Status": "Enabled",
      "Filter": {"Prefix": "logs/"},
      "Expiration": {"Days": 90}
    },
    {
      "ID": "transition-to-cold",
      "Status": "Enabled",
      "Filter": {"Prefix": "data/"},
      "Transition": {
        "Days": 30,
        "StorageClass": "GLACIER"
      }
    }
  ]
}
LCEOF

mc ilm import local/my-bucket < /tmp/lifecycle.json
mc ilm ls local/my-bucket
```

### Server-Side Encryption

```bash
# SSE-S3 (chiave gestita da MinIO, auto-encryption)
# In /etc/default/minio:
MINIO_KMS_KES_ENDPOINT=https://kes.example.com:7373
MINIO_KMS_KES_KEY_FILE=/etc/minio/certs/kes-client.key
MINIO_KMS_KES_CERT_FILE=/etc/minio/certs/kes-client.cert
MINIO_KMS_KES_CAPATH=/etc/minio/certs/kes-ca.cert
MINIO_KMS_KES_KEY_NAME=minio-default-key

# SSE-C (chiave fornita dal client)
mc cp --enc-c "local/secure-bucket=MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5MDA=" \
  /tmp/secret.txt local/secure-bucket/secret.txt
```

### Notification (Event-Driven)

```bash
# Configurazione notifiche verso Kafka
mc admin config set local notify_kafka:primary \
  brokers="kafka1:9092,kafka2:9092" \
  topic="minio-events" \
  sasl_username="" \
  sasl_password=""

mc admin service restart local

# Sottoscrizione eventi su un bucket
mc event add local/my-bucket arn:minio:sqs::primary:kafka \
  --event put,delete --prefix uploads/ --suffix .csv
mc event ls local/my-bucket
```

### Bucket e Site Replication

```bash
# Bucket replication (unidirezionale)
mc replicate add local/source-bucket \
  --remote-bucket "https://ACCESS:SECRET@remote.example.com/target-bucket" \
  --replicate "delete,delete-marker,existing-objects"

# Site replication (tutti i bucket, policies, IAM)
mc admin replicate add local remote-site
mc admin replicate status local
```

### Monitoring con Prometheus

```bash
# Generazione scrape config per Prometheus
mc admin prometheus generate local

# Output da aggiungere a prometheus.yml:
# - job_name: minio-job
#   bearer_token: <token>
#   metrics_path: /minio/v2/metrics/cluster
#   scheme: http
#   static_configs:
#   - targets: ['localhost:9000']
```

### MinIO su Kubernetes (MinIO Operator)

```yaml
# Installazione via Helm
# helm repo add minio-operator https://operator.min.io
# helm install operator minio-operator/operator -n minio-operator --create-namespace

# Tenant MinIO
apiVersion: minio.min.io/v2
kind: Tenant
metadata:
  name: minio-tenant
  namespace: minio-tenant
spec:
  image: quay.io/minio/minio:RELEASE.2024-11-07T00-52-20Z
  pools:
    - servers: 4
      name: pool-0
      volumesPerServer: 4
      volumeClaimTemplate:
        metadata:
          name: data
        spec:
          accessModes:
            - ReadWriteOnce
          resources:
            requests:
              storage: 100Gi
          storageClassName: fast-ssd
      resources:
        requests:
          cpu: "2"
          memory: 4Gi
        limits:
          cpu: "4"
          memory: 8Gi
  requestAutoCert: true
  prometheusOperator: true
```

---

## 3. Ceph

### Architettura

Ceph e' un sistema di storage distribuito unificato che fornisce block, file e object storage da un singolo cluster. I componenti fondamentali sono:

- **RADOS** (Reliable Autonomic Distributed Object Store): il layer di storage sottostante. Tutti i tipi di storage (block, file, object) sono mappati su oggetti RADOS.
- **MON** (Monitor): mantiene la cluster map (OSD map, MON map, PG map, CRUSH map). Richiede un quorum dispari (3 o 5 per produzione).
- **OSD** (Object Storage Daemon): un daemon per ogni disco fisico. Gestisce la lettura/scrittura dei dati, la replicazione, il recovery e il rebalancing.
- **MDS** (Metadata Server): gestisce i metadati del filesystem POSIX per CephFS. Non necessario per block o object storage.
- **MGR** (Manager): fornisce monitoraggio, dashboard, metriche Prometheus e moduli aggiuntivi (orchestrator, balancer, autoscaler).

### Storage Types

**RBD (RADOS Block Device)**: block storage. Espone un dispositivo a blocchi striped su piu' oggetti RADOS. Supporta thin provisioning, snapshots, cloning. Usato per VM disks (libvirt/QEMU, OpenStack Cinder) e Kubernetes PV.

**CephFS**: POSIX-compliant distributed filesystem. Supporta snapshot, subvolume, quota. Richiede almeno un MDS attivo.

**RGW (RADOS Gateway)**: object storage compatibile con S3 e Swift. HTTP frontend che traduce richieste API in operazioni RADOS.

### CRUSH Algorithm

CRUSH (Controlled Replication Under Scalable Hashing) determina il placement dei dati senza lookup centralizzato. Ogni client calcola indipendentemente la posizione di ogni oggetto usando la CRUSH map, che descrive la topologia del cluster (datacenter, rack, host, OSD).

```bash
# Visualizzare la CRUSH map
ceph osd crush tree

# Output tipico:
# ID  CLASS  WEIGHT    TYPE NAME
# -1         12.00000  root default
# -3          4.00000      host ceph-node1
#  0    hdd   2.00000          osd.0
#  1    ssd   2.00000          osd.1
# -5          4.00000      host ceph-node2
#  2    hdd   2.00000          osd.2
#  3    ssd   2.00000          osd.3
# -7          4.00000      host ceph-node3
#  4    hdd   2.00000          osd.4
#  5    ssd   2.00000          osd.5

# Creare una CRUSH rule per SSD-only pool
ceph osd crush rule create-replicated ssd-rule default host ssd
```

### Installazione con cephadm

```bash
# Bootstrap del primo monitor
curl --silent --remote-name --location \
  https://download.ceph.com/rpm-squid/el9/noarch/cephadm
chmod +x cephadm
sudo ./cephadm bootstrap \
  --mon-ip 10.0.1.10 \
  --initial-dashboard-password=MySecurePass123 \
  --dashboard-password-noupdate \
  --allow-fqdn-hostname

# Aggiungere host al cluster
sudo ceph orch host add ceph-node2 10.0.1.11
sudo ceph orch host add ceph-node3 10.0.1.12

# Aggiungere OSD (tutti i dischi disponibili)
sudo ceph orch apply osd --all-available-devices

# Aggiungere OSD specifici
sudo ceph orch daemon add osd ceph-node1:/dev/sdb
sudo ceph orch daemon add osd ceph-node2:/dev/sdb

# Deployment di monitor aggiuntivi
sudo ceph orch apply mon --placement="ceph-node1,ceph-node2,ceph-node3"

# Deployment MDS per CephFS
sudo ceph orch apply mds myfs --placement="ceph-node1,ceph-node2"
```

### Installazione con Rook (Kubernetes)

```yaml
# CephCluster CRD per Rook
apiVersion: ceph.rook.io/v1
kind: CephCluster
metadata:
  name: rook-ceph
  namespace: rook-ceph
spec:
  cephVersion:
    image: quay.io/ceph/ceph:v19.2
    allowUnsupported: false
  dataDirHostPath: /var/lib/rook
  mon:
    count: 3
    allowMultiplePerNode: false
  mgr:
    count: 2
    modules:
      - name: pg_autoscaler
        enabled: true
  dashboard:
    enabled: true
    ssl: true
  storage:
    useAllNodes: true
    useAllDevices: true
    deviceFilter: "^sd[b-z]"
  network:
    provider: host
  resources:
    osd:
      requests:
        cpu: "2"
        memory: "4Gi"
      limits:
        cpu: "4"
        memory: "8Gi"
```

### Pool Creation e Configuration

```bash
# Pool replicato (3 copie)
ceph osd pool create mypool 128 128 replicated
ceph osd pool set mypool size 3
ceph osd pool set mypool min_size 2

# Pool con erasure coding
ceph osd erasure-code-profile set ec-42-profile \
  k=4 m=2 crush-failure-domain=host
ceph osd pool create ec-pool 128 128 erasure ec-42-profile

# Abilitare l'applicazione sul pool
ceph osd pool application enable mypool rbd
ceph osd pool application enable ec-pool rgw

# Calcolo PG (Placement Groups)
# Formula: PG = (OSD_totali * 100) / replica_size
# Arrotondare alla potenza di 2 piu' vicina
# Es: 12 OSD, replica 3 => (12 * 100) / 3 = 400 => 512 PG

# Verificare lo stato dei pool
ceph osd pool ls detail
ceph osd pool stats
```

### Erasure Coding Profiles

```bash
# Profili predefiniti
ceph osd erasure-code-profile ls
ceph osd erasure-code-profile get default

# Profilo personalizzato per archivio (alta efficienza storage)
ceph osd erasure-code-profile set archive-profile \
  plugin=jerasure \
  technique=reed_sol_van \
  k=8 m=3 \
  crush-failure-domain=host

# Profilo per performance (basso overhead di parita')
ceph osd erasure-code-profile set perf-profile \
  plugin=isa \
  technique=reed_sol_van \
  k=4 m=2 \
  crush-failure-domain=host
```

### CephFS

```bash
# Creazione filesystem
ceph fs volume create myfs
# oppure manualmente:
ceph osd pool create cephfs_data 128
ceph osd pool create cephfs_metadata 64
ceph fs new myfs cephfs_metadata cephfs_data

# Mount via kernel driver
sudo mkdir /mnt/cephfs
sudo mount -t ceph mon1:6789,mon2:6789:/ /mnt/cephfs \
  -o name=admin,secret=AQBxxxxxxxxxxxxxxxxxxxxxxx

# Mount via FUSE (piu' features, meno performance)
sudo ceph-fuse -m mon1:6789,mon2:6789 /mnt/cephfs

# Subvolumes
ceph fs subvolumegroup create myfs group1
ceph fs subvolume create myfs vol1 --group_name group1 --size 10737418240
ceph fs subvolume getpath myfs vol1 --group_name group1

# Snapshots
ceph fs subvolume snapshot create myfs vol1 snap1 --group_name group1
ceph fs subvolume snapshot ls myfs vol1 --group_name group1
```

### RADOS Gateway (S3/Swift)

```bash
# Deployment RGW
sudo ceph orch apply rgw mystore --placement="ceph-node1,ceph-node2" --port=8080

# Creazione utente S3
radosgw-admin user create \
  --uid=s3user \
  --display-name="S3 User" \
  --access-key=MY_ACCESS_KEY \
  --secret-key=MY_SECRET_KEY

# Test con aws cli
aws --endpoint-url http://ceph-rgw:8080 s3 mb s3://test-bucket
aws --endpoint-url http://ceph-rgw:8080 s3 cp file.txt s3://test-bucket/
```

### Monitoring

```bash
# Stato generale del cluster
ceph status        # oppure ceph -s
ceph health detail

# Stato OSD
ceph osd tree
ceph osd df
ceph osd perf

# Stato PG (Placement Groups)
ceph pg stat
ceph pg dump

# Performance I/O in tempo reale
ceph daemon osd.0 perf dump
ceph tell osd.* bench

# Dashboard
ceph mgr module enable dashboard
ceph dashboard create-self-signed-cert
ceph dashboard ac-user-create admin -i /tmp/dashboard-password administrator
```

---

## 4. GlusterFS

### Architettura

GlusterFS e' un filesystem distribuito scalabile che aggrega storage da piu' server in un singolo namespace globale. I componenti principali sono:

- **Brick**: l'unita' base di storage — una directory esportata da un server (es. `/data/brick1` su `server1`)
- **Volume**: una collezione logica di brick. I dati vengono distribuiti e/o replicati attraverso i brick secondo il tipo di volume
- **Translator**: moduli stackable che implementano le funzionalita' (distribuzione, replicazione, caching, encryption). I translator vengono composti in una pipeline per ogni volume
- **glusterd**: il management daemon che gestisce i volumi e il trusted storage pool
- **glusterfsd**: il brick daemon che serve i dati di ogni brick

### Tipi di Volume

**Distributed**: distribuisce i file tra i brick senza replicazione. Un file risiede su un singolo brick. Nessuna ridondanza: la perdita di un brick causa la perdita dei file su quel brick. Utile per workload dove la ridondanza non e' necessaria e si vuole massimizzare lo spazio.

**Replicated**: replica ogni file su tutti i brick del replica set. Con replica 3 e 3 brick, ogni file esiste in 3 copie. Alta ridondanza ma spazio utilizzabile = spazio totale / N repliche.

**Distributed-Replicated**: combina distribuzione e replicazione. I file vengono distribuiti tra gruppi di brick, e ogni gruppo replica internamente. Es: 6 brick con replica 3 = 2 gruppi da 3, ogni file replicato 3 volte.

**Dispersed**: usa erasure coding per distribuire i dati tra brick. Simile a RAID 5/6. Definito da `disperse N redundancy M`: N brick totali, M di ridondanza. Spazio utilizzabile = (N-M)/N.

**Distributed-Dispersed**: combina distribuzione e dispersed. Piu' gruppi di brick dispersed.

### Installazione e Peer Probing

```bash
# Installazione su CentOS/RHEL
sudo dnf install centos-release-gluster
sudo dnf install glusterfs-server
sudo systemctl enable --now glusterd

# Peer probing (da eseguire su un nodo)
sudo gluster peer probe server2
sudo gluster peer probe server3
sudo gluster peer probe server4

# Verifica stato del pool
sudo gluster peer status
sudo gluster pool list
```

### Creazione e Gestione Volumi

```bash
# Preparazione brick directories (su ogni server)
sudo mkdir -p /data/brick1/gv0

# Volume Replicated (3 repliche)
sudo gluster volume create gv-replica replica 3 \
  server1:/data/brick1/gv0 \
  server2:/data/brick1/gv0 \
  server3:/data/brick1/gv0

# Volume Distributed-Replicated (6 brick, replica 3 = 2 gruppi)
sudo gluster volume create gv-distrep replica 3 \
  server1:/data/brick1/gv1 server2:/data/brick1/gv1 server3:/data/brick1/gv1 \
  server4:/data/brick1/gv1 server5:/data/brick1/gv1 server6:/data/brick1/gv1

# Volume Dispersed (6 brick, ridondanza 2)
sudo gluster volume create gv-dispersed disperse 6 redundancy 2 \
  server{1..6}:/data/brick1/gv2

# Avvio del volume
sudo gluster volume start gv-replica

# Impostazioni di tuning
sudo gluster volume set gv-replica performance.cache-size 512MB
sudo gluster volume set gv-replica performance.io-thread-count 32
sudo gluster volume set gv-replica network.ping-timeout 10
sudo gluster volume set gv-replica cluster.self-heal-daemon on
sudo gluster volume set gv-replica server.allow-insecure on

# Informazioni e stato
sudo gluster volume info gv-replica
sudo gluster volume status gv-replica
sudo gluster volume status gv-replica detail
```

### Mount dei Volumi

```bash
# Mount nativo GlusterFS (consigliato)
sudo mount -t glusterfs server1:/gv-replica /mnt/glusterfs

# Entry in /etc/fstab
# server1:/gv-replica /mnt/glusterfs glusterfs defaults,_netdev,backup-volfile-servers=server2:server3 0 0

# Mount via NFS (abilitare NFS sul volume)
sudo gluster volume set gv-replica nfs.disable off
sudo mount -t nfs -o vers=3 server1:/gv-replica /mnt/gluster-nfs

# Mount via SMB/CIFS
sudo gluster volume set gv-replica user.smb enable
sudo gluster volume set gv-replica user.cifs enable
```

### Geo-Replication

```bash
# Configurazione geo-replication (sito primario -> sito secondario)
# 1. Creare sessione
sudo gluster volume geo-replication gv-replica \
  remote-server::gv-replica-backup create push-pem

# 2. Avviare la sessione
sudo gluster volume geo-replication gv-replica \
  remote-server::gv-replica-backup start

# 3. Verifica stato
sudo gluster volume geo-replication gv-replica \
  remote-server::gv-replica-backup status detail
```

### Self-Healing

```bash
# Stato del self-healing
sudo gluster volume heal gv-replica info
sudo gluster volume heal gv-replica info split-brain

# Trigger manuale del healing
sudo gluster volume heal gv-replica full

# Statistiche di heal
sudo gluster volume heal gv-replica statistics
```

### GlusterFS con Kubernetes

```yaml
# StorageClass con GlusterFS CSI
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: glusterfs-csi
provisioner: org.gluster.glusterfs
parameters:
  resturl: "http://heketi.example.com:8080"
  restuser: "admin"
  secretNamespace: "default"
  secretName: "heketi-secret"
  volumetype: "replicate:3"
reclaimPolicy: Delete
volumeBindingMode: Immediate
allowVolumeExpansion: true
---
# PVC per GlusterFS
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: gluster-pvc
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: glusterfs-csi
  resources:
    requests:
      storage: 50Gi
```

### Monitoring e Troubleshooting

```bash
# Log
sudo tail -f /var/log/glusterfs/glusterd.log
sudo tail -f /var/log/glusterfs/bricks/data-brick1-gv0.log

# Profiling
sudo gluster volume profile gv-replica start
sudo gluster volume profile gv-replica info
sudo gluster volume profile gv-replica stop

# Top operations
sudo gluster volume top gv-replica open brick server1:/data/brick1/gv0
sudo gluster volume top gv-replica read-perf
sudo gluster volume top gv-replica write-perf

# Statedump per debugging avanzato
sudo gluster volume statedump gv-replica
```

---

## 5. S3-Compatible Storage

### Standard S3 API

L'API S3 (Simple Storage Service) e' diventata lo standard de facto per l'object storage. Le operazioni principali seguono il pattern REST con endpoint basati su bucket e object key.

Struttura dell'indirizzamento:
- **Path-style**: `https://s3.example.com/bucket-name/object-key`
- **Virtual-hosted style**: `https://bucket-name.s3.example.com/object-key`

### Operazioni Principali

```bash
# PutObject — upload di un oggetto
aws s3api put-object \
  --bucket my-bucket \
  --key documents/report-2024.pdf \
  --body /tmp/report.pdf \
  --content-type application/pdf \
  --metadata '{"project":"analytics","version":"3"}'

# GetObject — download di un oggetto
aws s3api get-object \
  --bucket my-bucket \
  --key documents/report-2024.pdf \
  /tmp/downloaded-report.pdf

# ListObjectsV2 — elenco oggetti con paginazione
aws s3api list-objects-v2 \
  --bucket my-bucket \
  --prefix logs/2024/ \
  --max-keys 1000

# DeleteObject
aws s3api delete-object --bucket my-bucket --key old-file.txt

# HeadObject — solo metadati senza scaricare il contenuto
aws s3api head-object --bucket my-bucket --key documents/report-2024.pdf
```

### Multipart Upload

Per oggetti superiori a 100 MB, il multipart upload divide l'oggetto in parti caricate in parallelo.

```bash
# 1. Iniziare il multipart upload
UPLOAD_ID=$(aws s3api create-multipart-upload \
  --bucket my-bucket \
  --key large-file.tar.gz \
  --query 'UploadId' --output text)

# 2. Caricare le parti (5 MB minimo per parte, tranne l'ultima)
aws s3api upload-part \
  --bucket my-bucket \
  --key large-file.tar.gz \
  --part-number 1 \
  --upload-id "$UPLOAD_ID" \
  --body /tmp/part1

aws s3api upload-part \
  --bucket my-bucket \
  --key large-file.tar.gz \
  --part-number 2 \
  --upload-id "$UPLOAD_ID" \
  --body /tmp/part2

# 3. Completare il multipart upload
aws s3api complete-multipart-upload \
  --bucket my-bucket \
  --key large-file.tar.gz \
  --upload-id "$UPLOAD_ID" \
  --multipart-upload '{
    "Parts": [
      {"ETag": "etag-part1", "PartNumber": 1},
      {"ETag": "etag-part2", "PartNumber": 2}
    ]
  }'

# Upload semplificato con aws s3 (gestisce automaticamente multipart)
aws s3 cp /tmp/large-file.tar.gz s3://my-bucket/ \
  --expected-size 10737418240
```

### Presigned URLs

```bash
# Generare URL prefirmato per download (valido 1 ora)
aws s3 presign s3://my-bucket/documents/report.pdf --expires-in 3600

# Generare URL prefirmato per upload
aws s3api put-object \
  --bucket my-bucket \
  --key uploads/user-file.jpg \
  --generate-cli-skeleton output > /dev/null

# Con boto3 (Python):
```

```python
import boto3
from botocore.config import Config

s3 = boto3.client('s3',
    endpoint_url='https://minio.example.com',
    aws_access_key_id='ACCESS_KEY',
    aws_secret_access_key='SECRET_KEY',
    config=Config(signature_version='s3v4')
)

# Presigned URL per upload (PUT)
url = s3.generate_presigned_url(
    'put_object',
    Params={'Bucket': 'uploads', 'Key': 'user-file.jpg'},
    ExpiresIn=3600
)
print(f"Upload URL: {url}")

# Presigned URL per download (GET)
url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': 'uploads', 'Key': 'user-file.jpg'},
    ExpiresIn=86400
)
print(f"Download URL: {url}")
```

### Versioning e Lifecycle Policies

```bash
# Abilitare versioning
aws s3api put-bucket-versioning \
  --bucket my-bucket \
  --versioning-configuration Status=Enabled

# Elencare versioni di un oggetto
aws s3api list-object-versions \
  --bucket my-bucket \
  --prefix documents/report.pdf

# Lifecycle policy
aws s3api put-bucket-lifecycle-configuration \
  --bucket my-bucket \
  --lifecycle-configuration '{
    "Rules": [
      {
        "ID": "move-to-glacier-after-90-days",
        "Status": "Enabled",
        "Filter": {"Prefix": "archive/"},
        "Transitions": [
          {"Days": 90, "StorageClass": "GLACIER"},
          {"Days": 365, "StorageClass": "DEEP_ARCHIVE"}
        ]
      },
      {
        "ID": "expire-old-versions",
        "Status": "Enabled",
        "Filter": {},
        "NoncurrentVersionExpiration": {"NoncurrentDays": 30},
        "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7}
      }
    ]
  }'
```

### S3 Select

```bash
# Query CSV direttamente su S3 senza scaricare il file intero
aws s3api select-object-content \
  --bucket analytics \
  --key logs/access-2024-01.csv \
  --expression "SELECT s.ip, s.timestamp, s.status FROM s3object s WHERE s.status = '500'" \
  --expression-type SQL \
  --input-serialization '{"CSV": {"FileHeaderInfo": "USE"}}' \
  --output-serialization '{"CSV": {}}' \
  /tmp/errors.csv
```

### Servizi S3-Compatible

| Servizio       | Compatibilita'  | Note                                      |
|----------------|------------------|-------------------------------------------|
| MinIO          | Completa         | Self-hosted, alta performance              |
| Ceph RGW       | Completa         | Parte dell'ecosistema Ceph                 |
| Wasabi         | Quasi completa   | Cloud, pricing semplice                    |
| Backblaze B2   | Parziale         | Cloud, molto economico                     |
| Cloudflare R2  | Quasi completa   | Cloud, zero egress fees                    |

### AWS CLI per S3

```bash
# Configurazione endpoint per S3-compatible
aws configure set default.s3.endpoint_url https://minio.example.com
# oppure per ogni comando:
export AWS_ENDPOINT_URL=https://minio.example.com

# Operazioni comuni con aws s3
aws s3 ls                                    # Lista bucket
aws s3 ls s3://my-bucket/prefix/             # Lista oggetti
aws s3 mb s3://new-bucket                    # Crea bucket
aws s3 rb s3://empty-bucket                  # Rimuovi bucket vuoto
aws s3 cp file.txt s3://bucket/              # Upload
aws s3 cp s3://bucket/file.txt ./            # Download
aws s3 mv s3://bucket/old.txt s3://bucket/new.txt  # Rename
aws s3 rm s3://bucket/file.txt               # Delete
aws s3 sync /local/dir s3://bucket/prefix/   # Sync locale -> S3
aws s3 sync s3://bucket/prefix/ /local/dir   # Sync S3 -> locale

# Sync con filtri
aws s3 sync /backups s3://backup-bucket/ \
  --exclude "*.tmp" \
  --include "*.tar.gz" \
  --delete \
  --storage-class STANDARD_IA
```

### SDK Usage (boto3 Python)

```python
import boto3
from botocore.exceptions import ClientError

session = boto3.Session(
    aws_access_key_id='ACCESS_KEY',
    aws_secret_access_key='SECRET_KEY'
)

s3 = session.client('s3', endpoint_url='https://s3.example.com')

# Upload con metadati e content type
s3.upload_file(
    '/tmp/report.pdf',
    'documents',
    'reports/2024/q4-report.pdf',
    ExtraArgs={
        'ContentType': 'application/pdf',
        'Metadata': {'author': 'team-analytics'},
        'ServerSideEncryption': 'AES256'
    }
)

# Download
s3.download_file('documents', 'reports/2024/q4-report.pdf', '/tmp/report.pdf')

# Lista oggetti con paginazione
paginator = s3.get_paginator('list_objects_v2')
for page in paginator.paginate(Bucket='documents', Prefix='reports/'):
    for obj in page.get('Contents', []):
        print(f"{obj['Key']} - {obj['Size']} bytes - {obj['LastModified']}")

# Copia cross-bucket
s3.copy_object(
    CopySource={'Bucket': 'source-bucket', 'Key': 'file.txt'},
    Bucket='dest-bucket',
    Key='file.txt'
)

# Gestione errori
try:
    s3.head_object(Bucket='my-bucket', Key='nonexistent.txt')
except ClientError as e:
    if e.response['Error']['Code'] == '404':
        print("Oggetto non trovato")
    else:
        raise
```

---

## 6. NFS in Cloud e Container

### NFS Tradizionale

NFS (Network File System) e' il protocollo standard per la condivisione di filesystem in rete su sistemi Unix/Linux. NFSv4 e' la versione corrente, con miglioramenti significativi in sicurezza, performance e attraversamento firewall (porta singola 2049).

#### Server NFS

```bash
# Installazione server NFS
sudo apt install nfs-kernel-server    # Debian/Ubuntu
sudo dnf install nfs-utils            # RHEL/Fedora

# Configurazione exports
sudo tee /etc/exports <<'EXEOF'
# Sintassi: directory client(opzioni) [client(opzioni)] ...
/srv/nfs/shared    10.0.1.0/24(rw,sync,no_subtree_check,no_root_squash)
/srv/nfs/readonly  10.0.1.0/24(ro,sync,no_subtree_check,root_squash)
/srv/nfs/homes     10.0.1.0/24(rw,sync,no_subtree_check,all_squash,anonuid=1000,anongid=1000)
/srv/nfs/backup    10.0.1.50(rw,sync,no_subtree_check) 10.0.1.51(rw,sync,no_subtree_check)
EXEOF

# Opzioni principali:
# rw/ro           - lettura/scrittura o sola lettura
# sync            - scritture sincrone (sicuro, piu' lento)
# no_subtree_check - disabilita il subtree checking (migliore performance)
# root_squash     - mappa root remoto ad anonuid (sicuro)
# no_root_squash  - consente accesso root remoto (pericoloso)
# all_squash      - mappa tutti gli utenti ad anonuid

# Applicare le modifiche
sudo exportfs -arv   # re-export tutto
sudo exportfs -s     # mostra exports attivi

# Avvio servizio
sudo systemctl enable --now nfs-server
```

#### Client NFS

```bash
# Installazione client
sudo apt install nfs-common            # Debian/Ubuntu
sudo dnf install nfs-utils             # RHEL/Fedora

# Mount manuale
sudo mkdir -p /mnt/shared
sudo mount -t nfs4 nfs-server:/srv/nfs/shared /mnt/shared

# Mount con opzioni di performance
sudo mount -t nfs4 nfs-server:/srv/nfs/shared /mnt/shared \
  -o rw,hard,intr,rsize=1048576,wsize=1048576,timeo=600,retrans=2

# Entry in /etc/fstab
# nfs-server:/srv/nfs/shared /mnt/shared nfs4 rw,hard,intr,rsize=1048576,wsize=1048576,_netdev 0 0

# Verificare mount
mount | grep nfs
nfsstat -c    # Statistiche client NFS
showmount -e nfs-server  # Mostra exports del server
```

### NFS Managed Services

```bash
# AWS EFS — creazione via CLI
aws efs create-file-system \
  --performance-mode generalPurpose \
  --throughput-mode bursting \
  --encrypted \
  --tags Key=Name,Value=my-efs

# Creare mount target in ogni subnet
aws efs create-mount-target \
  --file-system-id fs-12345678 \
  --subnet-id subnet-abc123 \
  --security-groups sg-nfs-access

# Mount EFS
sudo mount -t nfs4 -o nfsvers=4.1,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2 \
  fs-12345678.efs.us-east-1.amazonaws.com:/ /mnt/efs

# Azure Files NFS
az storage account create \
  --name mystorageacct \
  --resource-group mygroup \
  --kind FileStorage \
  --sku Premium_LRS \
  --enable-nfs-v3 true

# GCP Filestore
gcloud filestore instances create nfs-server \
  --zone=us-central1-a \
  --tier=STANDARD \
  --file-share=name=data,capacity=1TB \
  --network=name=default
```

### NFS Provisioner per Kubernetes

```yaml
# NFS CSI Driver deployment
# helm repo add csi-driver-nfs https://raw.githubusercontent.com/kubernetes-csi/csi-driver-nfs/master/charts
# helm install csi-driver-nfs csi-driver-nfs/csi-driver-nfs -n kube-system

# StorageClass per NFS CSI
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs-csi
provisioner: nfs.csi.k8s.io
parameters:
  server: nfs-server.example.com
  share: /srv/nfs/k8s-volumes
  mountPermissions: "0775"
reclaimPolicy: Delete
volumeBindingMode: Immediate
mountOptions:
  - nfsvers=4.1
  - hard
  - rsize=1048576
  - wsize=1048576
---
# PVC con NFS
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data-nfs
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: nfs-csi
  resources:
    requests:
      storage: 10Gi
```

### Sicurezza NFS

```bash
# NFS con Kerberos (NFSv4 + sec=krb5p)
# Server: /etc/exports
/srv/nfs/secure gss/krb5p(rw,sync,no_subtree_check)

# Client: mount con Kerberos
sudo mount -t nfs4 -o sec=krb5p nfs-server:/srv/nfs/secure /mnt/secure

# Restrizioni firewall
sudo ufw allow from 10.0.1.0/24 to any port 2049 proto tcp
sudo ufw allow from 10.0.1.0/24 to any port 2049 proto udp
```

### Troubleshooting NFS

```bash
# Diagnostica
rpcdebug -m nfs -s all       # Debug client NFS
rpcdebug -m nfsd -s all      # Debug server NFS (abilitare)
rpcdebug -m nfs -c all       # Disabilitare debug

# Verifica connettivita'
rpcinfo -p nfs-server
showmount -e nfs-server

# Performance
nfsstat -c                    # Statistiche client
nfsstat -s                    # Statistiche server
nfsiostat 2                   # I/O stats ogni 2 secondi
mountstats /mnt/shared        # Stats dettagliate per mount point

# Problemi comuni:
# "stale file handle" -> rimontare il filesystem
# "permission denied" -> verificare uid/gid mapping e exports
# "connection timed out" -> firewall, rpcbind, NFS service
```

---

## 7. Storage su Kubernetes

### PersistentVolume (PV)

Un PersistentVolume rappresenta una risorsa di storage nel cluster, indipendente dal ciclo di vita dei Pod. Puo' essere provisioned staticamente dall'amministratore o dinamicamente tramite StorageClass.

```yaml
# PV statico con hostPath (solo dev/test, non produzione)
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-hostpath
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  hostPath:
    path: /data/pv-hostpath
    type: DirectoryOrCreate
---
# PV statico con NFS
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-nfs
spec:
  capacity:
    storage: 100Gi
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  nfs:
    server: nfs-server.example.com
    path: /srv/nfs/k8s-data
  mountOptions:
    - nfsvers=4.1
    - hard
    - rsize=1048576
    - wsize=1048576
---
# PV statico con Ceph RBD
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-ceph-rbd
spec:
  capacity:
    storage: 50Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Delete
  csi:
    driver: rbd.csi.ceph.com
    volumeHandle: pv-ceph-rbd-handle
    volumeAttributes:
      clusterID: "cluster-id-from-ceph-config"
      pool: "kubernetes"
      imageFeatures: "layering"
    nodeStageSecretRef:
      name: csi-rbd-secret
      namespace: ceph-csi
    controllerExpandSecretRef:
      name: csi-rbd-secret
      namespace: ceph-csi
```

### PersistentVolumeClaim (PVC)

```yaml
# PVC che richiede storage dinamico
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: database-storage
  namespace: production
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 50Gi
---
# PVC per storage condiviso (ReadWriteMany)
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-uploads
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: nfs-csi
  resources:
    requests:
      storage: 100Gi
---
# Pod che utilizza i PVC
apiVersion: v1
kind: Pod
metadata:
  name: app-with-storage
spec:
  containers:
    - name: app
      image: myapp:latest
      volumeMounts:
        - name: db-vol
          mountPath: /var/lib/postgresql/data
        - name: uploads-vol
          mountPath: /app/uploads
  volumes:
    - name: db-vol
      persistentVolumeClaim:
        claimName: database-storage
    - name: uploads-vol
      persistentVolumeClaim:
        claimName: shared-uploads
```

### StorageClass

```yaml
# StorageClass per SSD ad alta performance (AWS EBS gp3)
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "5000"
  throughput: "250"
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:us-east-1:123456789:key/key-id"
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
---
# StorageClass per Ceph RBD
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ceph-rbd
provisioner: rbd.csi.ceph.com
parameters:
  clusterID: ceph-cluster-id
  pool: kubernetes
  imageFeatures: "layering"
  csi.storage.k8s.io/provisioner-secret-name: csi-rbd-secret
  csi.storage.k8s.io/provisioner-secret-namespace: ceph-csi
  csi.storage.k8s.io/controller-expand-secret-name: csi-rbd-secret
  csi.storage.k8s.io/controller-expand-secret-namespace: ceph-csi
  csi.storage.k8s.io/node-stage-secret-name: csi-rbd-secret
  csi.storage.k8s.io/node-stage-secret-namespace: ceph-csi
reclaimPolicy: Delete
allowVolumeExpansion: true
mountOptions:
  - discard
```

### Access Modes

| Modo | Abbreviazione | Significato                                        |
|------|---------------|----------------------------------------------------|
| ReadWriteOnce | RWO  | Montabile in lettura/scrittura da un singolo nodo   |
| ReadOnlyMany  | ROX  | Montabile in sola lettura da piu' nodi              |
| ReadWriteMany | RWX  | Montabile in lettura/scrittura da piu' nodi         |
| ReadWriteOncePod | RWOP | Montabile in lettura/scrittura da un singolo Pod |

Non tutti i provisioner supportano tutti i modi. Block storage (EBS, Ceph RBD) tipicamente supporta solo RWO. File storage (NFS, CephFS, GlusterFS) supporta RWX.

### Volume Expansion

```bash
# Verificare che la StorageClass abbia allowVolumeExpansion: true
kubectl get storageclass fast-ssd -o jsonpath='{.allowVolumeExpansion}'

# Espandere un PVC (solo aumento, non riduzione)
kubectl patch pvc database-storage -p '{"spec":{"resources":{"requests":{"storage":"100Gi"}}}}'

# Verificare lo stato dell'espansione
kubectl get pvc database-storage -o jsonpath='{.status.conditions}'
# Se il tipo e' "FileSystemResizePending", il Pod deve essere riavviato
# per completare l'espansione del filesystem
```

### Volume Snapshots

```yaml
# VolumeSnapshotClass
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: csi-rbd-snapclass
driver: rbd.csi.ceph.com
deletionPolicy: Delete
parameters:
  clusterID: ceph-cluster-id
  csi.storage.k8s.io/snapshotter-secret-name: csi-rbd-secret
  csi.storage.k8s.io/snapshotter-secret-namespace: ceph-csi
---
# Creare un VolumeSnapshot
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: db-snapshot-2024-01-15
spec:
  volumeSnapshotClassName: csi-rbd-snapclass
  source:
    persistentVolumeClaimName: database-storage
---
# Ripristinare un PVC da snapshot
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: database-restored
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: ceph-rbd
  resources:
    requests:
      storage: 50Gi
  dataSource:
    name: db-snapshot-2024-01-15
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
```

### CSI (Container Storage Interface)

CSI e' lo standard per l'integrazione di sistemi di storage con Kubernetes. Un CSI driver implementa tre servizi gRPC:

- **Identity Service**: informazioni sul plugin
- **Controller Service**: provisioning, snapshot, espansione (eseguito una volta nel cluster)
- **Node Service**: mount/unmount sui nodi (eseguito su ogni nodo)

```bash
# CSI drivers comuni
# Ceph RBD (block)
helm install ceph-csi-rbd ceph-csi/ceph-csi-rbd -n ceph-csi --create-namespace

# CephFS (file)
helm install ceph-csi-cephfs ceph-csi/ceph-csi-cephfs -n ceph-csi

# Longhorn
helm install longhorn longhorn/longhorn -n longhorn-system --create-namespace

# OpenEBS
helm install openebs openebs/openebs -n openebs --create-namespace

# Local Path Provisioner (Rancher)
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/master/deploy/local-path-storage.yaml

# Verificare CSI drivers installati
kubectl get csidrivers
kubectl get csinodes
```

### Data Protection con Velero

```bash
# Installazione Velero con provider AWS (S3-compatible)
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.10.0 \
  --bucket velero-backups \
  --backup-location-config region=us-east-1,s3ForcePathStyle=true,s3Url=https://minio.example.com \
  --secret-file /tmp/velero-credentials \
  --use-volume-snapshots=true \
  --snapshot-location-config region=us-east-1

# Contenuto /tmp/velero-credentials:
# [default]
# aws_access_key_id = VELERO_ACCESS_KEY
# aws_secret_access_key = VELERO_SECRET_KEY
```

---

## 8. Longhorn

### Architettura

Longhorn e' un sistema di storage distribuito cloud-native per Kubernetes, sviluppato da Rancher/SUSE. L'architettura e' composta da:

- **Longhorn Manager**: un DaemonSet che gira su ogni nodo. Gestisce le API Longhorn, la creazione/cancellazione dei volumi, la schedulazione delle repliche e la comunicazione con il Kubernetes API server.
- **Longhorn Engine**: un controller di storage che implementa il volume come iSCSI block device. Ogni volume ha il proprio engine (microservice architecture). L'engine replica sinronamente le scritture su tutte le repliche.
- **Replicas**: copie dei dati distribuite su nodi diversi. Di default 3 repliche per volume. Ogni replica e' un file sparse su disco locale.

L'architettura microservice (un engine per volume) isola i failure: il crash di un engine impatta solo il suo volume.

### Installazione

```bash
# Prerequisiti
sudo apt install open-iscsi nfs-common   # Su ogni nodo
sudo systemctl enable --now iscsid

# Installazione via Helm
helm repo add longhorn https://charts.longhorn.io
helm repo update
helm install longhorn longhorn/longhorn \
  --namespace longhorn-system \
  --create-namespace \
  --set defaultSettings.defaultReplicaCount=3 \
  --set defaultSettings.defaultDataLocality=best-effort \
  --set defaultSettings.backupTarget=s3://longhorn-backups@us-east-1/ \
  --set defaultSettings.backupTargetCredentialSecret=longhorn-backup-secret \
  --set persistence.defaultClassReplicaCount=3

# Installazione via kubectl
kubectl apply -f https://raw.githubusercontent.com/longhorn/longhorn/v1.7.0/deploy/longhorn.yaml

# Verificare installazione
kubectl -n longhorn-system get pods
kubectl get storageclass longhorn
```

### StorageClass Configuration

```yaml
# StorageClass personalizzata
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: longhorn-fast
provisioner: driver.longhorn.io
allowVolumeExpansion: true
reclaimPolicy: Delete
volumeBindingMode: Immediate
parameters:
  numberOfReplicas: "3"
  staleReplicaTimeout: "2880"
  fromBackup: ""
  fsType: "ext4"
  dataLocality: "best-effort"
  diskSelector: "ssd"
  nodeSelector: "storage"
---
# StorageClass per volumi con 2 repliche (bilanciamento costo/ridondanza)
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: longhorn-standard
provisioner: driver.longhorn.io
allowVolumeExpansion: true
parameters:
  numberOfReplicas: "2"
  dataLocality: "disabled"
  fsType: "ext4"
---
# PVC con Longhorn
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: longhorn-fast
  resources:
    requests:
      storage: 20Gi
```

### Replica Management

```bash
# Verificare stato dei volumi
kubectl -n longhorn-system get volumes.longhorn.io
kubectl -n longhorn-system get replicas.longhorn.io

# Dettagli di un volume specifico
kubectl -n longhorn-system get volume pvc-abc123 -o yaml

# Eviction di repliche da un nodo (prima di maintenance)
# Via Longhorn UI: Node -> Scheduling -> Disable
# oppure:
kubectl -n longhorn-system patch nodes.longhorn.io worker-3 \
  --type=merge -p '{"spec":{"allowScheduling":false,"evictionRequested":true}}'
```

### Snapshots e Backup

```yaml
# Snapshot manuale
apiVersion: longhorn.io/v1beta2
kind: Snapshot
metadata:
  name: snap-app-data-20240115
  namespace: longhorn-system
spec:
  volume: pvc-abc123
---
# Secret per backup target S3
apiVersion: v1
kind: Secret
metadata:
  name: longhorn-backup-secret
  namespace: longhorn-system
type: Opaque
data:
  AWS_ACCESS_KEY_ID: BASE64_ACCESS_KEY
  AWS_SECRET_ACCESS_KEY: BASE64_SECRET_KEY
  AWS_ENDPOINTS: aHR0cHM6Ly9taW5pby5leGFtcGxlLmNvbQ==
```

```bash
# Configurare backup target via CLI
kubectl -n longhorn-system patch settings.longhorn.io backup-target \
  --type=merge -p '{"value":"s3://longhorn-backups@us-east-1/"}'

# Creare backup dal Longhorn UI o tramite VolumeSnapshot API
kubectl apply -f - <<'VSEOF'
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: backup-app-data
spec:
  volumeSnapshotClassName: longhorn-snapshot-vsc
  source:
    persistentVolumeClaimName: app-data
VSEOF
```

### Recurring Jobs

```yaml
# Job ricorrente per snapshot ogni 6 ore + backup giornaliero
apiVersion: longhorn.io/v1beta2
kind: RecurringJob
metadata:
  name: snapshot-6h
  namespace: longhorn-system
spec:
  cron: "0 */6 * * *"
  task: snapshot
  groups:
    - default
  retain: 8
  concurrency: 2
  labels:
    type: scheduled-snapshot
---
apiVersion: longhorn.io/v1beta2
kind: RecurringJob
metadata:
  name: backup-daily
  namespace: longhorn-system
spec:
  cron: "0 2 * * *"
  task: backup
  groups:
    - default
  retain: 14
  concurrency: 1
  labels:
    type: scheduled-backup
```

### Disaster Recovery

```bash
# Ripristino di un volume da backup in un cluster diverso
# 1. Configurare lo stesso backup target nel cluster DR
# 2. Longhorn UI -> Backup -> selezionare backup -> Restore

# oppure via PVC con dataSource
kubectl apply -f - <<'DREOF'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: restored-data
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: longhorn
  resources:
    requests:
      storage: 20Gi
  dataSource:
    name: backup-app-data
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
DREOF
```

### Longhorn UI

```bash
# Esporre la UI tramite Ingress
kubectl -n longhorn-system apply -f - <<'UIEOF'
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: longhorn-ingress
  namespace: longhorn-system
  annotations:
    nginx.ingress.kubernetes.io/auth-type: basic
    nginx.ingress.kubernetes.io/auth-secret: longhorn-basic-auth
    nginx.ingress.kubernetes.io/auth-realm: "Longhorn Authentication"
spec:
  ingressClassName: nginx
  rules:
    - host: longhorn.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: longhorn-frontend
                port:
                  number: 80
UIEOF
```

### Confronto con Altre Soluzioni

| Feature          | Longhorn       | Ceph RBD       | OpenEBS Mayastor |
|------------------|----------------|----------------|-------------------|
| Semplicita'      | Alta           | Bassa          | Media             |
| Performance      | Media          | Alta           | Alta              |
| RWX              | Via NFS        | Nativo CephFS  | No                |
| Snapshots        | Si             | Si             | Si                |
| Backup S3/NFS    | Nativo         | Esterno        | Esterno           |
| Risorse minime   | 3 nodi, 3 dischi | 3 nodi, 3 OSD | 3 nodi, NVMe    |
| Maturita'        | GA (CNCF)      | Molto maturo   | In maturazione    |

---

## 9. OpenEBS

### Architettura e Storage Engines

OpenEBS e' una piattaforma di storage per Kubernetes che implementa il pattern Container Attached Storage (CAS). Ogni volume e' gestito da un proprio set di microservizi, eliminando single point of failure.

**Storage Engines disponibili**:

- **Mayastor** (ora Replicated PV Mayastor): engine ad alte prestazioni basato su NVMe-oF e io_uring. Usa SPDK (Storage Performance Development Kit) per I/O in user-space bypassando il kernel. Richiede HugePages e NVMe drives.
- **cStor**: engine maturo con pool management, replicazione sincrona, snapshot/clone. Usa ZFS come backend per ogni pool.
- **Jiva**: engine leggero basato su Longhorn engine (fork). Semplice da usare, adatto per ambienti con risorse limitate. Non richiede dischi dedicati.
- **LocalPV**: espone direttamente il disco locale o una directory hostPath come PV. Nessuna replicazione. Performance massima per workload che gestiscono la replicazione a livello applicativo (es. Cassandra, MongoDB replica sets).

### LocalPV per Performance

```yaml
# StorageClass per LocalPV hostpath
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: openebs-hostpath
provisioner: openebs.io/local
parameters:
  basePath: "/var/openebs/local"
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
---
# StorageClass per LocalPV device (disco raw)
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: openebs-device
provisioner: openebs.io/local
parameters:
  devicesFilter: "^/dev/sd[b-z]$"
  fsType: "ext4"
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
---
# PVC per LocalPV (il Pod viene schedulato sul nodo con il volume)
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: cassandra-data
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: openebs-hostpath
  resources:
    requests:
      storage: 100Gi
```

### Mayastor (NVMe-oF)

Mayastor opera interamente in user-space tramite SPDK. Usa il protocollo NVMe-oF (NVMe over Fabrics) per la comunicazione tra nodi, offrendo latenza estremamente bassa.

Componenti Mayastor:
- **Mayastor I/O Engine**: DaemonSet che gestisce gli I/O in user-space su ogni nodo storage
- **Nexus**: il volume target che aggrega le repliche e implementa il mirroring sincrono
- **Control Plane**: gestisce scheduling, replicazione e failure recovery

```bash
# Prerequisiti per Mayastor
# 1. HugePages (2MB pages)
echo 1024 | sudo tee /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
# Persistente in /etc/sysctl.conf:
# vm.nr_hugepages = 1024

# 2. Modulo kernel nvme-tcp
sudo modprobe nvme-tcp
echo "nvme-tcp" | sudo tee /etc/modules-load.d/nvme-tcp.conf

# Installazione Mayastor via Helm
helm repo add mayastor https://openebs.github.io/mayastor-extensions
helm install mayastor mayastor/mayastor \
  -n mayastor --create-namespace \
  --set etcd.replicaCount=3 \
  --set loki-stack.enabled=true

# Labeling nodi per Mayastor
kubectl label node worker-1 openebs.io/engine=mayastor
kubectl label node worker-2 openebs.io/engine=mayastor
kubectl label node worker-3 openebs.io/engine=mayastor
```

```yaml
# DiskPool (espone un disco NVMe a Mayastor)
apiVersion: openebs.io/v1beta2
kind: DiskPool
metadata:
  name: pool-worker-1
  namespace: mayastor
spec:
  node: worker-1
  disks:
    - "aio:///dev/nvme0n1"
---
apiVersion: openebs.io/v1beta2
kind: DiskPool
metadata:
  name: pool-worker-2
  namespace: mayastor
spec:
  node: worker-2
  disks:
    - "aio:///dev/nvme0n1"
---
# StorageClass per Mayastor
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: mayastor-3
provisioner: io.openebs.csi-mayastor
parameters:
  ioTimeout: "30"
  protocol: nvmf
  repl: "3"
reclaimPolicy: Delete
volumeBindingMode: Immediate
allowVolumeExpansion: true
---
# PVC con Mayastor
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: high-perf-data
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: mayastor-3
  resources:
    requests:
      storage: 50Gi
```

### Installazione OpenEBS Completa

```bash
# Installazione via Helm (include tutti gli engines)
helm repo add openebs https://openebs.github.io/openebs
helm repo update
helm install openebs openebs/openebs \
  -n openebs --create-namespace \
  --set localprovisioner.enabled=true \
  --set ndm.enabled=true \
  --set cstor.enabled=true \
  --set mayastor.enabled=false  # Abilitare solo se HugePages e NVMe disponibili

# Verificare installazione
kubectl -n openebs get pods
kubectl get storageclass | grep openebs
kubectl get blockdevices -n openebs   # Dischi rilevati da NDM
```

### Snapshot e Clone

```yaml
# VolumeSnapshotClass per cStor
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: cstor-snapshot-class
driver: cstor.csi.openebs.io
deletionPolicy: Delete
---
# Creare snapshot
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: cstor-snap-1
spec:
  volumeSnapshotClassName: cstor-snapshot-class
  source:
    persistentVolumeClaimName: cstor-pvc
---
# Clone da snapshot (nuovo PVC)
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: cstor-clone
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: cstor-storage
  resources:
    requests:
      storage: 50Gi
  dataSource:
    name: cstor-snap-1
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
```

### Use Cases per Engine Type

| Engine    | Use Case                                   | Latenza  | Replicazione |
|-----------|--------------------------------------------|----------|--------------|
| LocalPV   | Cassandra, Kafka, Elasticsearch            | Minima   | No (app-level)|
| Mayastor  | PostgreSQL, MySQL, workload critici        | Molto bassa | Si (sincrona)|
| cStor     | Workload general purpose con snapshots      | Media    | Si (sincrona)|
| Jiva      | Ambienti piccoli, edge, risorse limitate   | Media    | Si (sincrona)|

---

## 10. Data Protection e Backup

### Velero per Backup Kubernetes

Velero e' lo strumento standard per il backup e il restore di risorse Kubernetes e persistent volumes. Supporta backup di oggetti API Kubernetes, snapshot di volumi CSI e backup filesystem-level con Restic/Kopia.

```bash
# Installazione Velero CLI
wget https://github.com/vmware-tanzu/velero/releases/download/v1.14.0/velero-v1.14.0-linux-amd64.tar.gz
tar xzf velero-v1.14.0-linux-amd64.tar.gz
sudo mv velero-v1.14.0-linux-amd64/velero /usr/local/bin/

# Installazione server-side con S3-compatible backend
velero install \
  --provider aws \
  --plugins velero/velero-plugin-for-aws:v1.10.0 \
  --bucket velero-backups \
  --backup-location-config \
    region=us-east-1,s3ForcePathStyle=true,s3Url=https://minio.example.com \
  --snapshot-location-config region=us-east-1 \
  --secret-file /tmp/velero-credentials \
  --use-node-agent \
  --default-volumes-to-fs-backup

# Verificare installazione
velero version
kubectl -n velero get pods
```

### Backup e Restore

```bash
# Backup completo del cluster
velero backup create full-backup-20240115

# Backup di un singolo namespace
velero backup create prod-backup \
  --include-namespaces production \
  --include-resources deployments,services,configmaps,secrets,pvc

# Backup con label selector
velero backup create app-backup \
  --selector app=myapp

# Backup escludendo risorse
velero backup create partial-backup \
  --exclude-namespaces kube-system,velero \
  --exclude-resources events

# Stato del backup
velero backup describe full-backup-20240115
velero backup logs full-backup-20240115

# Lista backup
velero backup get

# Restore completo
velero restore create --from-backup full-backup-20240115

# Restore di un namespace specifico
velero restore create --from-backup prod-backup \
  --include-namespaces production

# Restore con mapping namespace (cambiare nome del namespace)
velero restore create --from-backup prod-backup \
  --namespace-mappings production:staging

# Stato del restore
velero restore describe <restore-name>
velero restore logs <restore-name>
```

### Restic/Kopia Integration per PV Backup

```bash
# Abilitare backup Restic/Kopia per specifici Pod via annotation
kubectl annotate pod my-pod \
  backup.velero.io/backup-volumes=data-volume,config-volume

# oppure per tutti i volumi di un Pod
kubectl annotate pod my-pod \
  backup.velero.io/backup-volumes-excludes=scratch-volume
```

```yaml
# Pod con annotation per backup dei volumi
apiVersion: v1
kind: Pod
metadata:
  name: app-with-backup
  annotations:
    backup.velero.io/backup-volumes: "app-data,app-config"
spec:
  containers:
    - name: app
      image: myapp:latest
      volumeMounts:
        - name: app-data
          mountPath: /data
        - name: app-config
          mountPath: /config
        - name: scratch
          mountPath: /tmp/scratch
  volumes:
    - name: app-data
      persistentVolumeClaim:
        claimName: app-data-pvc
    - name: app-config
      persistentVolumeClaim:
        claimName: app-config-pvc
    - name: scratch
      emptyDir: {}
```

### Schedule Backup

```bash
# Backup giornaliero con retention di 30 giorni
velero schedule create daily-backup \
  --schedule="0 2 * * *" \
  --ttl 720h \
  --include-namespaces production,staging

# Backup settimanale con retention di 90 giorni
velero schedule create weekly-backup \
  --schedule="0 3 * * 0" \
  --ttl 2160h

# Backup orario per namespace critici
velero schedule create hourly-critical \
  --schedule="0 * * * *" \
  --ttl 48h \
  --include-namespaces database

# Lista schedule
velero schedule get
velero schedule describe daily-backup
```

### Disaster Recovery Cross-Cluster

```bash
# Cluster sorgente: creare backup
velero backup create dr-backup --include-namespaces production

# Cluster destinazione: configurare stesso backup location
velero backup-location create primary \
  --provider aws \
  --bucket velero-backups \
  --config region=us-east-1,s3ForcePathStyle=true,s3Url=https://minio.example.com \
  --credential=velero-credentials=cloud

# Sincronizzare backup dal bucket remoto
velero backup get   # I backup appaiono automaticamente

# Restore nel cluster DR
velero restore create dr-restore --from-backup dr-backup
```

### rclone per Cloud Storage Sync

```bash
# Installazione
curl https://rclone.org/install.sh | sudo bash

# Configurazione remote S3
rclone config create minio s3 \
  provider=Minio \
  access_key_id=ACCESS_KEY \
  secret_access_key=SECRET_KEY \
  endpoint=https://minio.example.com

# Sync locale -> remoto
rclone sync /data/backups minio:backup-bucket/daily/ \
  --progress \
  --transfers 8 \
  --checkers 16 \
  --fast-list

# Sync tra cloud providers
rclone sync minio:bucket aws-s3:bucket \
  --progress \
  --transfers 16

# Verifica integrita'
rclone check /data/backups minio:backup-bucket/daily/

# Mount S3 come filesystem (FUSE)
rclone mount minio:data-bucket /mnt/s3-data \
  --vfs-cache-mode full \
  --vfs-cache-max-size 10G \
  --daemon

# Cron job per backup giornaliero
# 0 3 * * * rclone sync /data/important minio:backups/$(date +\%Y-\%m-\%d)/ --log-file=/var/log/rclone-backup.log
```

### Retention Policies e Encryption

```bash
# MinIO: object lock per immutable backups (WORM)
mc retention set COMPLIANCE 90d minio/backups

# Velero: TTL sui backup
velero backup create secure-backup --ttl 2160h  # 90 giorni

# rclone: encryption at rest
rclone config create encrypted crypt \
  remote=minio:encrypted-bucket \
  password=$(rclone obscure "MySecretPassphrase") \
  password2=$(rclone obscure "MySalt")

rclone sync /data/sensitive encrypted: --progress
```

---

## 11. Performance e Tuning

### IOPS vs Throughput vs Latency

Tre metriche fondamentali dello storage:

- **IOPS** (Input/Output Operations Per Second): numero di operazioni I/O al secondo. Critico per workload con molte piccole letture/scritture random (database OLTP, email server). Un SSD NVMe tipico: 100.000-500.000+ IOPS.
- **Throughput** (MB/s o GB/s): volume di dati trasferiti al secondo. Critico per workload sequenziali (video streaming, backup, data pipeline). Un SSD NVMe: 3.000-7.000 MB/s.
- **Latency** (ms o us): tempo di completamento di una singola operazione I/O. Critico per applicazioni interattive e database real-time. Un SSD NVMe: 10-100 us. Un HDD: 2-10 ms. Storage di rete: aggiunge latenza di rete.

Relazione: Throughput = IOPS x Block Size. Un disco con 100.000 IOPS a 4KB = 400 MB/s throughput. Lo stesso disco con blocchi da 256KB: 1.600 IOPS necessari per 400 MB/s.

### Benchmarking

```bash
# fio — benchmark standard per storage
# Test IOPS random read 4K
fio --name=rand-read --ioengine=libaio --iodepth=64 \
  --rw=randread --bs=4k --direct=1 --size=4G \
  --numjobs=4 --runtime=60 --group_reporting \
  --filename=/mnt/storage/fio-test

# Test IOPS random mixed read/write 70/30
fio --name=mixed-rw --ioengine=libaio --iodepth=32 \
  --rw=randrw --rwmixread=70 --bs=4k --direct=1 --size=4G \
  --numjobs=4 --runtime=60 --group_reporting \
  --filename=/mnt/storage/fio-test

# Test throughput sequenziale
fio --name=seq-write --ioengine=libaio --iodepth=16 \
  --rw=write --bs=1M --direct=1 --size=8G \
  --numjobs=1 --runtime=60 --group_reporting \
  --filename=/mnt/storage/fio-test

# Test latenza (bassa queue depth)
fio --name=latency --ioengine=libaio --iodepth=1 \
  --rw=randread --bs=4k --direct=1 --size=1G \
  --numjobs=1 --runtime=30 --group_reporting \
  --lat_percentiles=1 \
  --filename=/mnt/storage/fio-test

# dd — test sequenziale veloce (meno preciso di fio)
dd if=/dev/zero of=/mnt/storage/dd-test bs=1M count=1024 conv=fdatasync status=progress
dd if=/mnt/storage/dd-test of=/dev/null bs=1M status=progress

# iozone — test completo multi-pattern
iozone -a -s 4G -r 4k -r 64k -r 1M -i 0 -i 1 -i 2 \
  -f /mnt/storage/iozone-test -b /tmp/iozone-results.xls
```

### Cache Strategies

```bash
# Read-ahead tuning (default 128 KB per block device)
# Aumentare per workload sequenziali
sudo blockdev --setra 4096 /dev/sdb   # 2 MB read-ahead
cat /sys/block/sdb/queue/read_ahead_kb

# Write-back vs Write-through
# Write-back: scritture in cache, flush periodico (piu' veloce, rischio data loss)
# Write-through: ogni scrittura va su disco (piu' lento, sicuro)

# Impostare scheduler I/O
echo "mq-deadline" | sudo tee /sys/block/nvme0n1/queue/scheduler  # Per SSD
echo "bfq" | sudo tee /sys/block/sda/queue/scheduler              # Per HDD

# Page cache tuning
sudo sysctl -w vm.dirty_ratio=20                    # % RAM prima di flush forzato
sudo sysctl -w vm.dirty_background_ratio=10          # % RAM per flush in background
sudo sysctl -w vm.dirty_expire_centisecs=3000        # 30 secondi prima di expire
sudo sysctl -w vm.dirty_writeback_centisecs=500      # Flush ogni 5 secondi
sudo sysctl -w vm.vfs_cache_pressure=50              # Meno aggressivo nel rilasciare inode/dentry cache
```

### Network Tuning per Storage Distribuito

```bash
# Jumbo frames (MTU 9000) — richiede supporto su tutti gli switch e NIC
sudo ip link set eth1 mtu 9000
# Persistente in /etc/netplan/ o /etc/network/interfaces

# Verificare MTU end-to-end
ping -M do -s 8972 storage-node-2   # 8972 + 28 byte header = 9000

# TCP tuning per storage di rete
sudo sysctl -w net.core.rmem_max=16777216
sudo sysctl -w net.core.wmem_max=16777216
sudo sysctl -w net.ipv4.tcp_rmem="4096 87380 16777216"
sudo sysctl -w net.ipv4.tcp_wmem="4096 65536 16777216"
sudo sysctl -w net.core.netdev_max_backlog=30000
sudo sysctl -w net.ipv4.tcp_window_scaling=1
sudo sysctl -w net.ipv4.tcp_timestamps=1
sudo sysctl -w net.ipv4.tcp_sack=1

# Rete dedicata per storage (separare traffico storage da traffico applicativo)
# Configurare VLAN o interfaccia dedicata per traffico RADOS, iSCSI, NFS
# Esempio: eth0 = management, eth1 = storage cluster, eth2 = storage public
```

### SSD vs HDD Tiers

```bash
# Ceph: configurare device class e CRUSH rules per tiering
ceph osd crush class ls
# Output: [hdd, ssd, nvme]

# Pool su SSD
ceph osd crush rule create-replicated ssd-rule default host ssd
ceph osd pool create fast-pool 128 128 replicated ssd-rule

# Pool su HDD
ceph osd crush rule create-replicated hdd-rule default host hdd
ceph osd pool create archive-pool 128 128 replicated hdd-rule

# Cache tiering in Ceph (SSD cache davanti a pool HDD)
ceph osd tier add archive-pool fast-pool
ceph osd tier cache-mode fast-pool writeback
ceph osd tier set-overlay archive-pool fast-pool
ceph osd pool set fast-pool hit_set_type bloom
ceph osd pool set fast-pool hit_set_count 8
ceph osd pool set fast-pool hit_set_period 300
ceph osd pool set fast-pool target_max_bytes 1073741824  # 1 GB
```

### Compression e Deduplicazione

```bash
# ZFS: compression trasparente
sudo zfs set compression=lz4 tank/data       # lz4: veloce, compression ratio moderato
sudo zfs set compression=zstd tank/archive    # zstd: piu' lento, ratio migliore
sudo zfs get compressratio tank/data

# Btrfs: compression
sudo mount -o compress=zstd:3 /dev/sdb1 /mnt/btrfs

# Ceph: compression per pool (BlueStore)
ceph osd pool set mypool compression_algorithm snappy
ceph osd pool set mypool compression_mode aggressive
# Modi: none, passive (solo se hint), aggressive (sempre), force

# VDO (Virtual Data Optimizer) per deduplicazione + compression
sudo dnf install vdo kmod-kvdo
sudo vdo create --name=vdo-storage --device=/dev/sdb \
  --vdoLogicalSize=100G --deduplication=enabled --compression=enabled
sudo mkfs.xfs /dev/mapper/vdo-storage
sudo mount /dev/mapper/vdo-storage /mnt/vdo

# Statistiche VDO
sudo vdostats --human-readable
```

### QoS per Storage

```bash
# cgroups v2: limitare I/O per processo
echo "252:0 rbps=10485760 wbps=5242880 riops=1000 wiops=500" \
  | sudo tee /sys/fs/cgroup/my-app/io.max
# 252:0 = major:minor del device
# rbps = read bytes/sec, wbps = write bytes/sec
# riops = read IOPS, wiops = write IOPS

# Kubernetes: resource limits per storage (non standard, dipende dal CSI driver)
# Longhorn QoS via StorageClass
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: longhorn-qos
provisioner: driver.longhorn.io
parameters:
  numberOfReplicas: "3"
  # QoS non nativo in Longhorn, ma applicabile via cgroups sul nodo
```

---

## 12. Best Practices

### Capacity Planning

La pianificazione della capacita' deve considerare non solo lo spazio grezzo ma anche l'overhead di replicazione, erasure coding, metadati e spazio di working per recovery.

```
Spazio utilizzabile = Spazio grezzo / Fattore di replicazione

Esempio replicazione 3x:
  12 TB grezzo -> 4 TB utilizzabile

Esempio erasure coding 4+2:
  12 TB grezzo -> 8 TB utilizzabile (overhead 50% vs 200%)

Regola pratica:
  Mantenere sempre almeno il 20% di spazio libero per:
  - Recovery e rebalancing dopo failure
  - Picchi temporanei di scrittura
  - Operazioni di manutenzione (scrubbing, compaction)
```

Proiezione crescita:
- Misurare il tasso di crescita mensile negli ultimi 6-12 mesi
- Proiettare a 12-18 mesi
- Pianificare l'acquisto hardware con 3-6 mesi di anticipo (lead time)
- Automatizzare alert quando l'utilizzo supera il 70%, 80%, 90%

### Monitoring

```yaml
# Metriche critiche da monitorare:

# 1. Utilizzo spazio
- cluster_storage_total_bytes
- cluster_storage_used_bytes
- cluster_storage_available_bytes
- pool_storage_utilization_percent

# 2. Performance I/O
- iops_read_total
- iops_write_total
- throughput_read_bytes_per_sec
- throughput_write_bytes_per_sec
- latency_read_ms (p50, p95, p99)
- latency_write_ms (p50, p95, p99)

# 3. Salute del cluster
- osd_up_count vs osd_total_count
- pg_degraded_count
- recovery_operations_in_progress
- scrub_errors_total

# 4. Rete
- network_bytes_transmitted (storage interface)
- network_errors_total
- network_retransmits_total

# Prometheus alert rules:
groups:
  - name: storage-alerts
    rules:
      - alert: StorageSpaceWarning
        expr: cluster_storage_used_bytes / cluster_storage_total_bytes > 0.80
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Storage cluster al {{ $value | humanizePercentage }} di utilizzo"

      - alert: StorageSpaceCritical
        expr: cluster_storage_used_bytes / cluster_storage_total_bytes > 0.90
        for: 5m
        labels:
          severity: critical

      - alert: StorageLatencyHigh
        expr: histogram_quantile(0.99, rate(storage_operation_duration_seconds_bucket[5m])) > 0.1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Latenza storage p99 superiore a 100ms"

      - alert: OSDDown
        expr: ceph_osd_up == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "OSD {{ $labels.osd }} e' down"
```

### Data Classification e Tiering

Classificare i dati per valore e frequenza di accesso:

| Classe         | Storage Tier | Retention | Esempio                         |
|----------------|-------------|-----------|----------------------------------|
| Business Critical | Hot (SSD/NVMe) | Illimitata | Database produzione           |
| Operational    | Hot/Warm    | 1-5 anni  | Log applicativi, metriche       |
| Compliance     | Warm/Cold   | Regolamentare | Audit trail, dati finanziari |
| Archive        | Cold/Archive| 7+ anni   | Backup storici, dati legacy     |
| Temporary      | Hot         | Ore/Giorni| Cache, scratch, build artifacts |

Implementare lifecycle policies automatiche per spostare i dati tra tier.

### Encryption at Rest

```bash
# LUKS per encryption a livello disco
sudo cryptsetup luksFormat /dev/sdb
sudo cryptsetup open /dev/sdb encrypted-disk
sudo mkfs.xfs /dev/mapper/encrypted-disk

# dm-crypt automatico al boot via /etc/crypttab
# encrypted-disk /dev/sdb none luks,discard

# MinIO: auto-encryption per tutti i bucket
# Configurare KMS (KES + Vault/AWS KMS)

# Ceph: encryption at OSD level
# cephadm bootstrap con --osd-encryption
# oppure per nuovi OSD:
ceph orch apply osd --all-available-devices --method raw --encrypted

# Kubernetes: StorageClass con parametro encrypted
# (dipende dal CSI driver e dal backend)
```

### Backup Strategy — Regola 3-2-1

La regola 3-2-1 e' il minimo per la protezione dei dati:

- **3** copie dei dati (1 originale + 2 backup)
- **2** tipi di media diversi (es. SSD locale + object storage)
- **1** copia off-site (cloud, datacenter remoto, nastro)

Estensione moderna (3-2-1-1-0):
- **1** copia immutabile (WORM, object lock)
- **0** errori di verifica (test regolari di restore)

```bash
# Implementazione con Velero + MinIO + rclone
# 1. Velero: backup Kubernetes -> MinIO locale
velero schedule create daily --schedule="0 2 * * *" --ttl 720h

# 2. rclone: sync MinIO locale -> cloud remoto
rclone sync minio:velero-backups cloudflare-r2:velero-dr/ \
  --transfers 8 --progress

# 3. Object lock su MinIO per immutabilita'
mc retention set COMPLIANCE 90d minio/velero-backups

# 4. Verifica automatica (script cron)
#!/bin/bash
# /usr/local/bin/verify-backup.sh
LATEST=$(velero backup get -o json | jq -r '.items | sort_by(.metadata.creationTimestamp) | last | .metadata.name')
velero restore create "verify-${LATEST}" --from-backup "${LATEST}" --namespace-mappings "production:verify-ns"
# Attendere completamento e verificare
kubectl -n verify-ns get pods
kubectl delete namespace verify-ns
```

### Disaster Recovery Testing

```bash
# Checklist DR test trimestrale:
# 1. Verificare che i backup siano completi e recenti
velero backup get
velero backup describe <latest-backup>

# 2. Restore in ambiente di test
velero restore create dr-test --from-backup <latest-backup> \
  --namespace-mappings "production:dr-test"

# 3. Verificare integrita' dei dati
kubectl -n dr-test exec -it db-pod -- pg_dump -t critical_table | md5sum
# Confrontare con hash noto

# 4. Misurare RTO (Recovery Time Objective)
# Tempo dall'inizio del restore al servizio funzionante

# 5. Verificare RPO (Recovery Point Objective)
# Delta tra ultimo dato nel backup e dato piu' recente in produzione

# 6. Documentare risultati e gap
# 7. Cleanup
kubectl delete namespace dr-test
```

### Naming Conventions

```
Bucket/Volume naming:
  {ambiente}-{team}-{applicazione}-{tipo}
  Esempi:
    prod-analytics-warehouse-data
    staging-backend-api-uploads
    dev-ml-training-datasets

PV/PVC naming:
  {applicazione}-{componente}-{tipo}
  Esempi:
    postgres-primary-data
    elasticsearch-hot-data
    redis-cache-data

Backup naming:
  {target}-{tipo}-{timestamp}
  Esempi:
    prod-full-20240115T020000Z
    staging-incremental-20240115T140000Z
```

### Access Control

```bash
# Principio del minimo privilegio:
# - Accesso read-only di default
# - Scrittura solo dove necessaria
# - Admin limitato a operatori certificati

# MinIO: policy granulari per utente/gruppo
mc admin policy create minio team-analytics /tmp/analytics-policy.json
mc admin policy attach minio team-analytics --group analytics

# Ceph: autenticazione per pool
ceph auth get-or-create client.app \
  mon 'allow r' \
  osd 'allow rw pool=app-pool' \
  -o /etc/ceph/ceph.client.app.keyring

# Kubernetes: RBAC per PVC
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pvc-reader
  namespace: production
rules:
  - apiGroups: [""]
    resources: ["persistentvolumeclaims"]
    verbs: ["get", "list"]
```

### Lifecycle Management e Cost Optimization

```bash
# Audit di utilizzo storage
kubectl get pvc --all-namespaces -o json | \
  jq -r '.items[] | [.metadata.namespace, .metadata.name, .spec.resources.requests.storage, .status.phase] | @tsv' | \
  sort -k3 -h

# Identificare PVC non utilizzati (non montati da alcun Pod)
kubectl get pvc --all-namespaces -o json | \
  jq -r '.items[] | select(.status.phase == "Bound") | .metadata.name' > /tmp/bound-pvcs.txt

kubectl get pods --all-namespaces -o json | \
  jq -r '.items[].spec.volumes[]?.persistentVolumeClaim.claimName // empty' | sort -u > /tmp/used-pvcs.txt

comm -23 <(sort /tmp/bound-pvcs.txt) <(sort /tmp/used-pvcs.txt)
# Output: PVC bound ma non montati da nessun Pod

# Strategie di riduzione costi:
# 1. Eliminare PVC orfani
# 2. Ridimensionare PVC sovradimensionati (se la StorageClass supporta shrink)
# 3. Spostare dati freddi su tier economici
# 4. Implementare lifecycle policies per eliminazione automatica
# 5. Usare erasure coding invece di replicazione dove possibile
# 6. Compressione per dati comprimibili (log, CSV, JSON)
# 7. Deduplicazione per ambienti con molti dati simili (VDI, CI/CD artifacts)
```

---

## 13. Ceph Advanced

### CRUSH Map: Struttura e Manipolazione

La CRUSH map e' il cuore del data placement in Ceph. Definisce la topologia fisica del cluster come un albero gerarchico (root -> datacenter -> room -> rack -> host -> OSD) e le regole che determinano come i dati vengono distribuiti attraverso questa topologia.

#### Struttura della CRUSH Map

La CRUSH map si compone di quattro sezioni:

- **Devices**: lista di tutti gli OSD con il loro ID e peso (weight). Il peso riflette la capacita' relativa del disco (tipicamente in TB).
- **Bucket Types**: definizione dei tipi di nodo nella gerarchia (root, datacenter, room, rack, host). Si possono aggiungere tipi custom per topologie complesse.
- **Bucket Instances**: definizione concreta dei nodi con i relativi figli e algoritmo di selezione.
- **Rules**: regole che specificano come selezionare gli OSD per ogni pool, definendo il failure domain e il tipo di device class.

```bash
# Esportare la CRUSH map in formato binario
ceph osd getcrushmap -o /tmp/crushmap.bin

# Decompilare in formato leggibile
crushtool -d /tmp/crushmap.bin -o /tmp/crushmap.txt

# Esempio di struttura decompilata
# device 0 osd.0 class hdd
# device 1 osd.1 class ssd
# device 2 osd.2 class nvme
#
# type 0 osd
# type 1 host
# type 2 rack
# type 3 room
# type 4 datacenter
# type 5 root
#
# host ceph-node1 {
#   id -3
#   alg straw2
#   hash 0
#   item osd.0 weight 2.000
#   item osd.1 weight 1.000
# }

# Compilare e iniettare la CRUSH map modificata
crushtool -c /tmp/crushmap.txt -o /tmp/crushmap-new.bin
ceph osd setcrushmap -i /tmp/crushmap-new.bin

# Aggiungere un rack alla topologia senza modificare la map manualmente
ceph osd crush add-bucket rack-02 rack
ceph osd crush move rack-02 root=default datacenter=dc-1
ceph osd crush move ceph-node3 rack=rack-02

# Cambiare il peso di un OSD (utile durante decommissioning graduale)
ceph osd crush reweight osd.5 0.5    # Riduce il peso a 0.5 TB
ceph osd crush reweight osd.5 0.0    # Drain completo dei dati dall'OSD
```

#### CRUSH Rules Avanzate

```bash
# Rule per distribuzione cross-datacenter (disaster tolerance)
ceph osd crush rule create-replicated cross-dc-rule default datacenter host

# Rule per device class specifiche con failure domain rack
ceph osd crush rule create-replicated nvme-rack-rule default rack nvme

# Verificare le regole e il loro utilizzo
ceph osd crush rule ls
ceph osd crush rule dump nvme-rack-rule

# Simulare il placement di un PG con una rule specifica
crushtool -i /tmp/crushmap.bin --test \
  --rule 3 --num-rep 3 --min-x 0 --max-x 1023 \
  --show-mappings --show-utilization
```

### FastEC (Erasure Coding Avanzato)

A partire da Ceph Tentacle (v20.2.0, novembre 2025), FastEC migliora significativamente le prestazioni dell'erasure coding per I/O di piccole dimensioni, raggiungendo un throughput 2-3 volte superiore rispetto alle versioni precedenti. Un profilo EC 6+2 con FastEC raggiunge circa il 50% delle prestazioni della replicazione tripla, utilizzando solo il 33% dello spazio.

```bash
# Profilo EC ottimizzato per workload misti (FastEC richiede Ceph >= v20)
ceph osd erasure-code-profile set fastec-profile \
  plugin=jerasure \
  technique=reed_sol_van \
  k=6 m=2 \
  crush-failure-domain=host \
  crush-device-class=ssd

# Pool EC con overwrites abilitati per RBD/CephFS
ceph osd pool create ec-rbd-pool 128 128 erasure fastec-profile
ceph osd pool set ec-rbd-pool allow_ec_overwrites true
ceph osd pool application enable ec-rbd-pool rbd

# Profilo EC per archivio a lungo termine (massima efficienza storage)
ceph osd erasure-code-profile set deep-archive-profile \
  plugin=jerasure \
  technique=liberation \
  k=10 m=4 \
  crush-failure-domain=rack

# Pool EC con profilo ISA-L (Intel Storage Acceleration Library)
# Richiede CPU con istruzioni SSE4/AVX; 30-50% piu' veloce di jerasure
ceph osd erasure-code-profile set isa-profile \
  plugin=isa \
  technique=reed_sol_van \
  k=4 m=2 \
  crush-failure-domain=host

# Verificare lo stato di un pool EC
ceph osd pool ls detail | grep -A5 ec-rbd-pool
rados -p ec-rbd-pool bench 60 write --no-cleanup
rados -p ec-rbd-pool bench 60 seq
```

### CephFS Avanzato

```bash
# Filesystem con data pool EC e metadata pool replicato
ceph osd pool create cephfs-meta 64 64 replicated
ceph osd pool create cephfs-data-rep 128 128 replicated
ceph osd pool create cephfs-data-ec 128 128 erasure fastec-profile
ceph osd pool set cephfs-data-ec allow_ec_overwrites true

ceph fs new production-fs cephfs-meta cephfs-data-rep
ceph fs add_data_pool production-fs cephfs-data-ec

# Configurare file layout per usare il pool EC per file grandi
setfattr -n ceph.dir.layout.pool -v cephfs-data-ec /mnt/cephfs/archive/

# Subvolume con quota e isolamento
ceph fs subvolumegroup create production-fs tenant-a
ceph fs subvolume create production-fs data-vol \
  --group_name tenant-a \
  --size 107374182400 \
  --mode 750 \
  --uid 1000 --gid 1000

# Quota per directory
setfattr -n ceph.quota.max_bytes -v 53687091200 /mnt/cephfs/tenant-a/   # 50 GB
setfattr -n ceph.quota.max_files -v 100000 /mnt/cephfs/tenant-a/        # 100k file

# MDS tuning per grandi directory (milioni di file)
ceph config set mds mds_dir_max_entries 500000
ceph config set mds mds_cache_memory_limit 8589934592   # 8 GB cache MDS

# MDS standby-replay per failover rapido (<5 secondi)
ceph fs set production-fs allow_standby_replay true
ceph orch apply mds production-fs --placement="3"   # 1 active + 2 standby

# Snapshot CephFS a livello filesystem
mkdir /mnt/cephfs/.snap/daily-20260524
ls /mnt/cephfs/.snap/   # Lista snapshot disponibili
```

### RGW Multisite e Bucket Sharding

```bash
# Configurazione multisite RGW (replica cross-datacenter)
# Sito primario: creare realm, zonegroup e zone
radosgw-admin realm create --rgw-realm=global --default
radosgw-admin zonegroup create --rgw-zonegroup=eu \
  --endpoints=http://rgw-dc1:8080 --master --default
radosgw-admin zone create --rgw-zonegroup=eu --rgw-zone=dc1 \
  --endpoints=http://rgw-dc1:8080 --master --default \
  --access-key=SYNC_KEY --secret=SYNC_SECRET

# Sito secondario: creare zone secondaria
radosgw-admin realm pull --url=http://rgw-dc1:8080 \
  --access-key=SYNC_KEY --secret-key=SYNC_SECRET
radosgw-admin zone create --rgw-zonegroup=eu --rgw-zone=dc2 \
  --endpoints=http://rgw-dc2:8080 \
  --access-key=SYNC_KEY --secret=SYNC_SECRET

# Verificare stato sync
radosgw-admin sync status
radosgw-admin data sync status --source-zone=dc1

# Bucket sharding per performance con milioni di oggetti
radosgw-admin bucket reshard --bucket=large-bucket \
  --num-shards=128 --yes-i-really-mean-it

# Dynamic resharding automatico
ceph config set rgw rgw_dynamic_resharding true
ceph config set rgw rgw_max_objs_per_shard 150000
```

---

## 14. MinIO Deep-Dive

### Erasure Coding Internals

MinIO implementa erasure coding per-oggetto (non per-volume come Ceph), utilizzando Reed-Solomon con implementazione assembly ottimizzata per x86 (AVX2/AVX-512) e ARM (NEON). Ogni oggetto viene autonomamente protetto, eliminando la necessita' di un RAID controller o di un layer di replicazione sottostante.

```bash
# In un cluster con 16 dischi, MinIO crea erasure sets
# Ogni erasure set contiene un sottoinsieme di dischi
# L'erasure coding di default e' N/2 dati + N/2 parita'

# Esempio: 4 nodi x 4 dischi = 16 dischi
# Erasure set size = 16
# Data shards = 8, Parity shards = 8
# Tolleranza: perdita di 8 dischi (50%)

# Per cambiare il livello di parita' (meno ridondanza, piu' spazio)
export MINIO_STORAGE_CLASS_STANDARD="EC:4"    # 4 parita' su 16 dischi
export MINIO_STORAGE_CLASS_RRS="EC:2"         # 2 parita' (Reduced Redundancy)

# Verificare la configurazione erasure coding
mc admin info local --json | jq '.info.erasure'

# Healing: verificare e riparare oggetti degradati
mc admin heal local/ --recursive --verbose
mc admin heal local/my-bucket --dry-run   # Solo report, nessuna azione

# Monitorare lo stato di healing
mc admin heal local/ --recursive --json | jq '.items_healed'
```

### ILM e Tiering Remoto

MinIO supporta Information Lifecycle Management (ILM) con transizione automatica degli oggetti verso tier di storage remoti, inclusi altri cluster MinIO, AWS S3, Azure Blob Storage e Google Cloud Storage.

```bash
# Configurare un tier remoto S3
mc ilm tier add s3 local COLD-TIER \
  --endpoint https://cold-storage.example.com \
  --access-key COLD_ACCESS_KEY \
  --secret-key COLD_SECRET_KEY \
  --bucket cold-archive \
  --region us-east-1 \
  --storage-class STANDARD

# Configurare un tier Azure
mc ilm tier add azure local AZURE-ARCHIVE \
  --account-name myaccount \
  --account-key BASE64_KEY \
  --bucket azure-container

# Configurare un tier GCS
mc ilm tier add gcs local GCS-NEARLINE \
  --credentials-file /etc/minio/gcs-creds.json \
  --bucket gcs-nearline-bucket

# Regola ILM: transizione a COLD-TIER dopo 60 giorni
mc ilm rule add local/data-bucket \
  --transition-days 60 \
  --transition-tier COLD-TIER \
  --noncurrent-transition-days 30 \
  --noncurrent-transition-tier COLD-TIER

# Regola ILM: scadenza oggetti + pulizia versioni
mc ilm rule add local/logs-bucket \
  --expiry-days 180 \
  --noncurrent-expiry-days 7 \
  --prefix "access-logs/"

# Visualizzare regole ILM attive
mc ilm rule ls local/data-bucket
mc ilm tier info local

# Verificare lo stato delle transizioni
mc ilm tier status local COLD-TIER
```

### Site Replication Bidirezionale

A differenza della bucket replication (unidirezionale per-bucket), la site replication sincronizza l'intero cluster: tutti i bucket, le policy IAM, gli utenti, i gruppi, e le configurazioni ILM.

```bash
# Prerequisiti: almeno 2 cluster MinIO con la stessa configurazione di base
# Tutti i siti devono avere lo stesso root user e password iniziale

# Aggiungere siti alla replication (da qualsiasi nodo)
mc admin replicate add site1 site2 site3

# Verificare stato replication
mc admin replicate status site1
mc admin replicate info site1

# Resync completo dopo un failure prolungato
mc admin replicate resync start site1 site2

# Rimuovere un sito dalla replication
mc admin replicate remove site1 --site-name site3 --force

# Monitorare lag di replication
mc admin replicate status site1 --json | \
  jq '.statuses[] | {site: .deploymentID, lag: .replicationLatency}'
```

### WORM e Object Locking Avanzato

MinIO supporta due modalita' di retention per l'immutabilita' degli oggetti, conformi allo standard SEC 17a-4(f) e CFTC 1.31(c)-(d).

**COMPLIANCE mode**: nessuno, incluso l'utente root, puo' eliminare o sovrascrivere l'oggetto fino alla scadenza della retention. Nemmeno la retention puo' essere ridotta. Adatto a requisiti normativi stringenti (finanza, sanita', PA).

**GOVERNANCE mode**: gli utenti con il permesso `s3:BypassGovernanceRetention` possono eliminare o modificare la retention. Adatto a protezione interna contro cancellazioni accidentali senza la rigidita' del compliance mode.

```bash
# Creare bucket con object locking abilitato
mc mb local/regulated-data --with-lock

# Impostare retention di default COMPLIANCE per 7 anni
mc retention set --default COMPLIANCE 2555d local/regulated-data

# Impostare legal hold su un oggetto specifico
mc legalhold set local/regulated-data/contract-2026.pdf

# Rimuovere legal hold (possibile in qualsiasi momento)
mc legalhold clear local/regulated-data/contract-2026.pdf

# Impostare GOVERNANCE retention su un oggetto specifico
mc retention set GOVERNANCE 365d local/regulated-data/report.pdf

# Bypassare governance mode (richiede permesso esplicito)
mc rm local/regulated-data/report.pdf --governance --bypass

# Verificare lo stato di retention di un oggetto
mc stat local/regulated-data/contract-2026.pdf
# Output include: X-Amz-Object-Lock-Mode, X-Amz-Object-Lock-Retain-Until-Date
```

### MinIO: Nota sulla Sostenibilita' del Progetto

A dicembre 2025 MinIO e' entrato in maintenance mode con un aggiornamento silenzioso del README su GitHub, senza annuncio ufficiale, guida alla migrazione o timeline. Il codice resta disponibile sotto licenza AGPLv3, ma non vengono accettate nuove modifiche. Questa situazione evidenzia il rischio di dipendere da progetti "open source" governati da una singola azienda senza governance comunitaria. Per deployment nuovi, valutare alternative con governance aperta come Ceph RGW, oppure pianificare una exit strategy verso servizi gestiti S3-compatible (Cloudflare R2, Wasabi, Backblaze B2).

---

## 15. Longhorn Deep-Dive

### V2 Data Engine

Longhorn V2 Data Engine introduce il supporto per NVMe over TCP (NVMe-oF) come protocollo di trasporto, sostituendo iSCSI e sfruttando SPDK (Storage Performance Development Kit) per I/O in user-space. Questo riduce significativamente la latenza e il consumo CPU rispetto al V1 engine basato su iSCSI kernel-mode.

```yaml
# Abilitare V2 Data Engine nella configurazione Longhorn
# Prerequisiti: kernel >= 5.15, HugePages, modulo nvme-tcp
apiVersion: longhorn.io/v1beta2
kind: Setting
metadata:
  name: v2-data-engine
  namespace: longhorn-system
value: "true"
---
# StorageClass con V2 engine
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: longhorn-v2
provisioner: driver.longhorn.io
parameters:
  numberOfReplicas: "3"
  dataEngine: "v2"
  fsType: "ext4"
  dataLocality: "best-effort"
allowVolumeExpansion: true
reclaimPolicy: Delete
```

```bash
# Prerequisiti per V2 Data Engine su ogni nodo
echo 1024 | sudo tee /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages
sudo modprobe nvme-tcp
echo "nvme-tcp" | sudo tee /etc/modules-load.d/nvme-tcp.conf

# Verificare lo stato del V2 engine
kubectl -n longhorn-system get setting v2-data-engine -o jsonpath='{.value}'
kubectl -n longhorn-system get instancemanagers -o wide
```

### RWX con NFS

Longhorn nativamente supporta solo ReadWriteOnce (RWO) per block storage. Per workload che richiedono ReadWriteMany (RWX), Longhorn espone un server NFS integrato sopra il volume block. Il server NFS viene deployato automaticamente quando un PVC richiede `ReadWriteMany`.

```yaml
# PVC ReadWriteMany con Longhorn (NFS automatico)
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: shared-data-rwx
spec:
  accessModes:
    - ReadWriteMany
  storageClassName: longhorn
  resources:
    requests:
      storage: 50Gi
---
# Deployment che usa il volume RWX su piu' repliche
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-app
  template:
    metadata:
      labels:
        app: web-app
    spec:
      containers:
        - name: app
          image: nginx:alpine
          volumeMounts:
            - name: shared
              mountPath: /usr/share/nginx/html
      volumes:
        - name: shared
          persistentVolumeClaim:
            claimName: shared-data-rwx
```

### DR Volumes Cross-Cluster

Longhorn supporta volumi Disaster Recovery (DR) che mantengono una copia stand-by in un cluster secondario, aggiornata periodicamente dai backup incrementali sul backup target condiviso (S3/NFS).

```bash
# Cluster primario: configurare backup target condiviso
kubectl -n longhorn-system patch settings.longhorn.io backup-target \
  --type=merge -p '{"value":"s3://shared-backups@us-east-1/"}'

# Cluster primario: creare backup ricorrente
kubectl -n longhorn-system apply -f - <<'EOF'
apiVersion: longhorn.io/v1beta2
kind: RecurringJob
metadata:
  name: dr-backup-5m
  namespace: longhorn-system
spec:
  cron: "*/5 * * * *"
  task: backup
  groups:
    - dr-critical
  retain: 12
  concurrency: 2
EOF

# Cluster DR: creare un DR volume che segue i backup del volume primario
# Via Longhorn UI: Backup -> selezionare l'ultimo backup del volume -> Create DR Volume
# Il DR volume rimane in stato "standby" e si aggiorna automaticamente

# Failover manuale: attivare il DR volume
# Longhorn UI: Volume -> selezionare DR volume -> Activate
# oppure via kubectl:
kubectl -n longhorn-system patch volumes.longhorn.io dr-volume-name \
  --type=merge -p '{"spec":{"standby":false}}'

# Verificare stato dei DR volumes
kubectl -n longhorn-system get volumes.longhorn.io -o custom-columns=\
NAME:.metadata.name,STATE:.status.state,STANDBY:.spec.standby,LAST-BACKUP:.status.lastBackup
```

### Volume Encryption

Longhorn supporta encryption at rest per singolo volume tramite dm-crypt/LUKS, gestito trasparentemente dal CSI driver.

```yaml
# Secret con la passphrase di encryption
apiVersion: v1
kind: Secret
metadata:
  name: longhorn-crypto-secret
  namespace: longhorn-system
type: Opaque
stringData:
  CRYPTO_KEY_VALUE: "my-secure-passphrase-min-32-chars!!"
  CRYPTO_KEY_PROVIDER: "secret"
  CRYPTO_KEY_CIPHER: "aes-xts-plain64"
  CRYPTO_KEY_HASH: "sha256"
  CRYPTO_KEY_SIZE: "256"
  CRYPTO_PBKDF: "argon2i"
---
# StorageClass con encryption abilitato
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: longhorn-encrypted
provisioner: driver.longhorn.io
parameters:
  numberOfReplicas: "3"
  encrypted: "true"
  csi.storage.k8s.io/provisioner-secret-name: longhorn-crypto-secret
  csi.storage.k8s.io/provisioner-secret-namespace: longhorn-system
  csi.storage.k8s.io/node-stage-secret-name: longhorn-crypto-secret
  csi.storage.k8s.io/node-stage-secret-namespace: longhorn-system
  csi.storage.k8s.io/node-publish-secret-name: longhorn-crypto-secret
  csi.storage.k8s.io/node-publish-secret-namespace: longhorn-system
reclaimPolicy: Delete
allowVolumeExpansion: true
```

---

## 16. Storage Security

### Encryption at Rest

L'encryption at rest protegge i dati quando sono scritti su disco fisico. Anche se un attaccante ottiene accesso fisico al disco (furto, smaltimento non corretto, accesso al datacenter), i dati restano illeggibili senza la chiave di cifratura.

#### LUKS/dm-crypt a Livello Disco

```bash
# Creazione volume LUKS2 con cifratura AES-256-XTS
sudo cryptsetup luksFormat --type luks2 \
  --cipher aes-xts-plain64 \
  --key-size 512 \
  --hash sha512 \
  --pbkdf argon2id \
  /dev/sdb

# Apertura e formattazione
sudo cryptsetup open /dev/sdb encrypted-data
sudo mkfs.xfs /dev/mapper/encrypted-data
sudo mount /dev/mapper/encrypted-data /mnt/secure-storage

# Automount via /etc/crypttab con keyfile (non interattivo)
sudo dd if=/dev/urandom of=/root/.luks-keyfile bs=4096 count=1
sudo chmod 400 /root/.luks-keyfile
sudo cryptsetup luksAddKey /dev/sdb /root/.luks-keyfile

# /etc/crypttab entry
# encrypted-data /dev/sdb /root/.luks-keyfile luks,discard,no-read-workqueue,no-write-workqueue

# Benchmark cifratura per valutare overhead
sudo cryptsetup benchmark
# Output tipico: AES-XTS 256b ~ 3500 MB/s encrypt, 3200 MB/s decrypt (con AES-NI)
```

#### Ceph OSD Encryption

```bash
# Bootstrap cluster con encryption di default per tutti gli OSD
sudo cephadm bootstrap --mon-ip 10.0.1.10 --osd-encryption

# Aggiungere OSD cifrati a un cluster esistente
sudo ceph orch apply osd --all-available-devices --encrypted

# Verifica che gli OSD usino encryption
ceph osd metadata osd.0 | grep -i encrypt
# Output: "encrypted": "true", "osd_objectstore": "bluestore"

# Ceph BlueStore encryption usa dm-crypt con chiavi gestite internamente
# Le chiavi vengono memorizzate nel MON database, cifrate con la chiave del cluster
```

### Encryption in Transit

L'encryption in transit protegge i dati durante la trasmissione sulla rete, prevenendo intercettazioni (sniffing), man-in-the-middle e tampering.

```bash
# Ceph: abilitare encryption in transit (messenger v2 con cephx + TLS)
ceph config set global ms_cluster_mode "secure crc"
ceph config set global ms_service_mode "secure crc"
ceph config set global ms_client_mode "secure crc"
# "secure" = cifratura completa, "crc" = fallback con solo integrity check

# Verificare la modalita' di connessione
ceph config get osd ms_cluster_mode

# MinIO: TLS obbligatorio
# Posizionare certificati in /etc/minio/certs/
# private.key e public.crt per il server
# CAs/ directory per CA certificates
sudo mkdir -p /etc/minio/certs/CAs
sudo cp server.crt /etc/minio/certs/public.crt
sudo cp server.key /etc/minio/certs/private.key
sudo chown -R minio-user:minio-user /etc/minio/certs/

# Forzare TLS 1.2+ come versione minima
# MINIO_TLS_MIN_VERSION=tls1.2 in /etc/default/minio

# NFS: Kerberos + encryption (sec=krb5p)
# krb5 = autenticazione, krb5i = +integrity, krb5p = +privacy (encryption)
sudo mount -t nfs4 -o sec=krb5p,vers=4.2 nfs-server:/export /mnt/secure-nfs
```

### Key Management con Vault e KES

La gestione centralizzata delle chiavi e' critica per lo storage distribuito. HashiCorp Vault con il MinIO Key Encryption Service (KES) implementa il pattern envelope encryption: una Data Encryption Key (DEK) cifra i dati, e una Key Encryption Key (KEK) gestita da Vault cifra la DEK.

```bash
# Architettura: MinIO -> KES -> Vault -> chiavi master
# 1. Vault genera/conserva le KEK (Key Encryption Keys)
# 2. KES media tra MinIO e Vault, cachea le KEK per performance
# 3. MinIO genera DEK per-oggetto, cifrate con KEK via KES

# Installazione KES
wget https://github.com/minio/kes/releases/latest/download/kes-linux-amd64
chmod +x kes-linux-amd64 && sudo mv kes-linux-amd64 /usr/local/bin/kes

# Configurazione KES con Vault backend
cat > /etc/kes/config.yml <<'KESEOF'
address: 0.0.0.0:7373
admin:
  identity: disabled
tls:
  key: /etc/kes/server.key
  cert: /etc/kes/server.crt
policy:
  minio:
    allow:
      - /v1/key/create/*
      - /v1/key/generate/*
      - /v1/key/decrypt/*
      - /v1/key/bulk/decrypt/*
    identities:
      - ${MINIO_IDENTITY}
keystore:
  vault:
    endpoint: https://vault.example.com:8200
    engine: kv-v2
    prefix: minio-keys
    approle:
      id: ${VAULT_ROLE_ID}
      secret: ${VAULT_SECRET_ID}
    tls:
      ca: /etc/kes/vault-ca.crt
KESEOF

# Configurazione MinIO per usare KES
# In /etc/default/minio:
MINIO_KMS_KES_ENDPOINT=https://kes.example.com:7373
MINIO_KMS_KES_KEY_FILE=/etc/minio/certs/kes-client.key
MINIO_KMS_KES_CERT_FILE=/etc/minio/certs/kes-client.crt
MINIO_KMS_KES_CAPATH=/etc/minio/certs/kes-ca.crt
MINIO_KMS_KES_KEY_NAME=minio-default-key

# Abilitare auto-encryption per tutti i bucket
mc admin config set local api auto_encryption=on
mc admin service restart local

# Vault: abilitare il secrets engine per KMIP (Enterprise)
# Vault KMIP consente a client KMIP-compatibili (database, storage)
# di richiedere chiavi direttamente a Vault usando il protocollo OASIS KMIP
vault secrets enable kmip
vault write kmip/config listen_addrs=0.0.0.0:5696
vault write kmip/scope/storage -f
vault write kmip/scope/storage/role/ceph-osd \
  tls_client_key_type=ec tls_client_key_bits=256 \
  operation_all=true
```

### Rotazione delle Chiavi

```bash
# MinIO: rotazione della KEK (la DEK viene re-cifrata, i dati non vengono riscritti)
kes key create minio-key-v2
mc admin config set local api encryption_key=minio-key-v2
mc admin service restart local

# Ceph: rotazione delle chiavi OSD (richiede reformat dell'OSD)
# Le chiavi OSD sono generate al momento della creazione del disco cifrato
# Per ruotare: drain OSD -> destroy -> ricreate con nuova chiave
ceph osd out osd.5
# Attendere migration completa
ceph osd purge osd.5 --yes-i-really-mean-it
# Ricreare l'OSD con nuova chiave
ceph orch daemon add osd ceph-node2:/dev/sdc --method raw --encrypted
```

---

## 17. CSI Drivers Deep-Dive

### Architettura CSI in Kubernetes

Il Container Storage Interface (CSI) separa la logica di storage dal core di Kubernetes tramite un'architettura basata su plugin gRPC. Un CSI driver viene deployato come due componenti:

**Controller Plugin** (tipicamente un Deployment/StatefulSet singolo nel cluster):
- Gestisce operazioni a livello cluster: CreateVolume, DeleteVolume, ControllerPublishVolume (attach), CreateSnapshot, ControllerExpandVolume
- Comunicazione via Unix domain socket con i sidecar container

**Node Plugin** (DaemonSet, un pod per ogni nodo):
- Gestisce operazioni a livello nodo: NodeStageVolume (format+mount al staging path), NodePublishVolume (bind mount al pod), NodeExpandVolume
- Richiede accesso privilegiato al filesystem del nodo

### Sidecar Containers

I sidecar containers sono il meccanismo di integrazione tra Kubernetes API e il driver CSI. Ogni sidecar gestisce una responsabilita' specifica:

```
+------------------------------------------+
|         Controller Pod                    |
|                                          |
|  +------------------+  +--------------+  |
|  | external-        |  | external-    |  |
|  | provisioner      |  | attacher     |  |
|  +--------+---------+  +------+-------+  |
|           |                   |           |
|           +-------+   +------+           |
|                   |   |                  |
|              +----v---v-----+            |
|              | CSI Driver   |            |
|              | (Controller) |            |
|              +------+-------+            |
|                     |                    |
|              Unix Domain Socket          |
+------------------------------------------+
```

| Sidecar | Funzione | Watch su |
|---------|----------|----------|
| external-provisioner | Crea/elimina volumi quando PVC viene creato/eliminato | PersistentVolumeClaim |
| external-attacher | Attach/detach volumi ai nodi | VolumeAttachment |
| external-snapshotter | Gestisce snapshot dei volumi | VolumeSnapshot |
| external-resizer | Espande volumi esistenti | PersistentVolumeClaim (size change) |
| livenessprobe | Health check del driver CSI | CSI Identity service |
| node-driver-registrar | Registra il driver CSI sul nodo (kubelet plugin) | N/A (init) |

```bash
# Verificare i CSI drivers registrati nel cluster
kubectl get csidrivers -o wide
kubectl get csinodes -o wide

# Verificare i sidecar containers di un CSI driver
kubectl -n ceph-csi get pods -l app=csi-rbdplugin-provisioner -o jsonpath=\
'{range .items[*].spec.containers[*]}{.name}{"\n"}{end}'
# Output tipico:
# csi-provisioner
# csi-attacher
# csi-snapshotter
# csi-resizer
# csi-rbdplugin

# Logs dei sidecar per troubleshooting
kubectl -n ceph-csi logs deploy/csi-rbdplugin-provisioner -c csi-provisioner
kubectl -n ceph-csi logs deploy/csi-rbdplugin-provisioner -c csi-attacher
```

### Troubleshooting PVC Pending

Un PVC in stato `Pending` indica che il provisioner non e' riuscito a creare il volume. Le cause piu' comuni:

```bash
# 1. Verificare gli events del PVC
kubectl describe pvc <pvc-name>
# Cercare eventi come:
# - "waiting for a volume to be created"
# - "no persistent volumes available"
# - "failed to provision volume with StorageClass"

# 2. Verificare che la StorageClass esista e il provisioner sia corretto
kubectl get storageclass <class-name> -o yaml

# 3. Verificare che il CSI driver sia running
kubectl get pods -n <csi-namespace> | grep provisioner

# 4. Verificare i logs del provisioner
kubectl -n ceph-csi logs deploy/csi-rbdplugin-provisioner -c csi-provisioner \
  --tail=100 | grep -i error

# 5. Verificare la connettivita' verso il backend storage
kubectl -n ceph-csi exec deploy/csi-rbdplugin-provisioner -c csi-rbdplugin -- \
  ceph -s --conf /etc/ceph/ceph.conf

# 6. Verificare i secrets (credenziali storage)
kubectl -n ceph-csi get secret csi-rbd-secret -o yaml

# 7. Topology-aware scheduling: se volumeBindingMode=WaitForFirstConsumer,
# il PVC resta Pending fino a quando un Pod lo richiede e viene schedulato
kubectl get storageclass <class-name> -o jsonpath='{.volumeBindingMode}'
```

### Topology Awareness

CSI supporta topology-aware provisioning per creare volumi nella stessa zona/rack/regione del pod che li consuma, riducendo latenza e costi di traffico cross-zone.

```yaml
# StorageClass con topologia
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ceph-rbd-topology
provisioner: rbd.csi.ceph.com
parameters:
  clusterID: ceph-cluster
  pool: kubernetes
  imageFeatures: "layering"
  csi.storage.k8s.io/provisioner-secret-name: csi-rbd-secret
  csi.storage.k8s.io/provisioner-secret-namespace: ceph-csi
  csi.storage.k8s.io/node-stage-secret-name: csi-rbd-secret
  csi.storage.k8s.io/node-stage-secret-namespace: ceph-csi
volumeBindingMode: WaitForFirstConsumer
allowedTopologies:
  - matchLabelExpressions:
      - key: topology.kubernetes.io/zone
        values:
          - zone-a
          - zone-b
```

---

## 18. Storage Monitoring Avanzato

### Ceph Exporter e Metriche

Ceph espone metriche Prometheus tramite il modulo MGR `prometheus`, attivo di default. L'endpoint e' disponibile sulla porta 9283 del MGR attivo.

```bash
# Verificare che il modulo prometheus sia abilitato
ceph mgr module ls | grep prometheus
ceph mgr module enable prometheus

# Configurare l'endpoint
ceph config set mgr mgr/prometheus/server_addr 0.0.0.0
ceph config set mgr mgr/prometheus/port 9283

# Prometheus scrape config
# - job_name: 'ceph'
#   honor_labels: true
#   static_configs:
#     - targets: ['ceph-mgr-active:9283']
```

Metriche chiave da monitorare:

```yaml
# Salute cluster
- ceph_health_status              # 0=OK, 1=WARN, 2=ERR
- ceph_mon_quorum_status          # 1=in quorum, 0=fuori

# Capacita'
- ceph_cluster_total_bytes        # Capacita' totale grezza
- ceph_cluster_total_used_bytes   # Spazio utilizzato
- ceph_pool_bytes_used            # Spazio usato per pool
- ceph_pool_stored                # Dati logici (pre-replica)

# Performance OSD
- ceph_osd_op_r_latency_sum / ceph_osd_op_r_latency_count    # Latenza media read
- ceph_osd_op_w_latency_sum / ceph_osd_op_w_latency_count    # Latenza media write
- ceph_osd_op_r                   # IOPS read per OSD
- ceph_osd_op_w                   # IOPS write per OSD

# Stato PG
- ceph_pg_active                  # PG attivi (dovrebbe essere = totale PG)
- ceph_pg_degraded                # PG degradati (repliche mancanti)
- ceph_pg_undersized              # PG con meno repliche del target
- ceph_pg_inconsistent            # PG con dati inconsistenti (scrub fallito)

# Recovery
- ceph_osd_recovery_ops           # Operazioni di recovery in corso
- ceph_osd_recovery_bytes         # Byte in recovery
```

### MinIO Prometheus Metrics

```bash
# MinIO espone metriche su tre endpoint
# /minio/v2/metrics/cluster   — metriche a livello cluster
# /minio/v2/metrics/node      — metriche per nodo
# /minio/v2/metrics/bucket    — metriche per bucket
# /minio/v2/metrics/resource  — risorse sistema (CPU, memoria, rete)

# Generare configurazione Prometheus
mc admin prometheus generate local

# Metriche MinIO chiave:
# minio_s3_requests_total                    — richieste S3 totali per tipo (GET, PUT, DELETE)
# minio_s3_requests_errors_total             — errori S3 per codice HTTP
# minio_s3_traffic_received_bytes            — traffico in ingresso
# minio_s3_traffic_sent_bytes                — traffico in uscita
# minio_s3_requests_ttfb_seconds_distribution — time-to-first-byte (latenza)
# minio_cluster_capacity_usable_total_bytes  — capacita' utilizzabile
# minio_cluster_capacity_usable_free_bytes   — spazio libero
# minio_heal_objects_total                   — oggetti in healing
# minio_node_disk_used_bytes                 — disco usato per nodo
```

### Grafana Dashboard Templates

```bash
# Dashboard Ceph ufficiali (importare via dashboard ID in Grafana)
# 2842  — Ceph Cluster Overview
# 5336  — Ceph OSD Performance
# 7056  — Ceph Pool Stats
# 13502 — Ceph RGW Overview

# Dashboard MinIO
# 13502 — MinIO Overview (Grafana Labs)
# Oppure generare dashboard custom:
mc admin prometheus generate local --type dashboard > minio-dashboard.json

# Dashboard Longhorn
# Longhorn espone metriche su /metrics di ogni longhorn-manager pod
# Metriche chiave:
# longhorn_volume_actual_size_bytes
# longhorn_volume_capacity_bytes
# longhorn_volume_state (1=attached, 0=detached)
# longhorn_volume_robustness (1=healthy, 2=degraded, 3=faulted)
# longhorn_node_storage_capacity_bytes
# longhorn_node_storage_usage_bytes
# longhorn_backup_actual_size_bytes

# node_exporter metriche disco (da correlare con metriche applicative)
# node_disk_io_time_seconds_total        — tempo totale in I/O
# node_disk_read_bytes_total             — byte letti
# node_disk_written_bytes_total          — byte scritti
# node_disk_reads_completed_total        — operazioni di lettura completate
# node_disk_writes_completed_total       — operazioni di scrittura completate
# node_filesystem_avail_bytes            — spazio libero filesystem
# node_filesystem_size_bytes             — dimensione totale filesystem
```

### Alert Rules Avanzate

```yaml
# Regole di alerting per storage distribuito
groups:
  - name: storage-advanced-alerts
    rules:
      - alert: CephOSDNearFull
        expr: ceph_osd_stat_bytes_used / ceph_osd_stat_bytes > 0.85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "OSD {{ $labels.osd }} al {{ $value | humanizePercentage }}"

      - alert: CephPGNotActive
        expr: ceph_pg_active < ceph_pg_total
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "{{ $value }} PG non attivi nel cluster Ceph"

      - alert: CephRecoveryTooSlow
        expr: rate(ceph_osd_recovery_bytes[30m]) < 10485760
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Recovery Ceph < 10 MB/s — possibile bottleneck di rete o disco"

      - alert: MinIODiskOffline
        expr: minio_cluster_drive_offline_total > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "{{ $value }} dischi offline nel cluster MinIO"

      - alert: LonghornVolumeDegraded
        expr: longhorn_volume_robustness == 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Volume Longhorn {{ $labels.volume }} degradato"

      - alert: StorageCapacityForecast
        expr: |
          predict_linear(
            ceph_cluster_total_used_bytes[7d], 30 * 24 * 3600
          ) > ceph_cluster_total_bytes * 0.90
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Il cluster Ceph superera' il 90% di utilizzo entro 30 giorni"
```

---

## 19. Storage Performance Benchmarking Avanzato

### Metodologia di Benchmarking

Un benchmark storage significativo deve seguire una metodologia strutturata:

1. **Profilare il workload reale**: analizzare i pattern I/O dell'applicazione (dimensione blocchi, rapporto read/write, sequenziale vs random, queue depth tipica).
2. **Preparare l'ambiente**: usare volumi dedicati, non condivisi con altri workload. Eseguire un pre-conditioning del disco SSD (scrivere l'intero volume almeno una volta) per eliminare performance artificialmente alte da celle vuote.
3. **Eseguire i test**: con parametri che riflettono il workload reale, non solo best-case sintetici.
4. **Misurare le metriche giuste**: concentrarsi su p99 latency, non solo IOPS di picco. Un disco puo' fare 100K IOPS con p99 a 50ms — inutile per un database che richiede p99 < 5ms.
5. **Ripetere e confrontare**: eseguire ogni test almeno 3 volte. Scartare il primo run (warm-up). Calcolare media e deviazione standard.

### fio Avanzato

```bash
# Pre-conditioning SSD (scrivere l'intero volume)
fio --name=precondition --ioengine=libaio --iodepth=64 \
  --rw=write --bs=1M --direct=1 --size=100% \
  --filename=/dev/nvme0n1 --loops=2

# Profilo database OLTP (PostgreSQL-like)
cat > /tmp/oltp.fio <<'FIOEOF'
[global]
ioengine=libaio
direct=1
runtime=300
time_based=1
group_reporting=1
lat_percentiles=1
clat_percentiles=1
percentile_list=50:90:95:99:99.9:99.99

[oltp-read]
rw=randread
bs=8k
iodepth=32
numjobs=8
size=10G
filename=/mnt/storage/fio-oltp

[oltp-write]
rw=randwrite
bs=8k
iodepth=16
numjobs=4
size=10G
filename=/mnt/storage/fio-oltp-w

[oltp-mixed]
rw=randrw
rwmixread=80
bs=8k
iodepth=32
numjobs=8
size=10G
filename=/mnt/storage/fio-oltp-mixed
FIOEOF

fio /tmp/oltp.fio --output-format=json+ --output=/tmp/oltp-results.json

# Profilo streaming/sequenziale (video, backup, data pipeline)
fio --name=sequential --ioengine=libaio --iodepth=16 \
  --rw=readwrite --rwmixread=50 --bs=1M --direct=1 \
  --size=20G --numjobs=4 --runtime=120 --time_based \
  --group_reporting --lat_percentiles=1 \
  --filename=/mnt/storage/fio-seq \
  --output-format=json+ --output=/tmp/seq-results.json

# Analizzare i risultati JSON con jq
jq '.jobs[] | {name: .jobname, 
  read_iops: .read.iops, 
  write_iops: .write.iops,
  read_bw_mb: (.read.bw / 1024),
  write_bw_mb: (.write.bw / 1024),
  read_lat_p99_us: .read.clat_ns.percentile."99.000000" / 1000,
  write_lat_p99_us: .write.clat_ns.percentile."99.000000" / 1000
}' /tmp/oltp-results.json
```

### ioping per Latenza

```bash
# Installazione
sudo apt install ioping   # Debian/Ubuntu
sudo dnf install ioping   # RHEL/Fedora

# Latenza singola operazione (come ping per il disco)
ioping -c 20 /mnt/storage

# Latenza random read 4K
ioping -c 100 -s 4k -R /mnt/storage

# Latenza sequenziale
ioping -c 100 -s 1M -S /mnt/storage

# Latenza con write
ioping -c 100 -s 4k -W /mnt/storage

# Output tipico (NVMe locale):
# 4 KiB <<< /mnt/storage (nvme0n1): request=1 time=42.1 us
# 4 KiB <<< /mnt/storage (nvme0n1): request=2 time=38.7 us
# min/avg/max/mdev = 35.2 us / 40.1 us / 52.3 us / 4.8 us

# Output tipico (Ceph RBD su rete 10Gbps):
# 4 KiB <<< /mnt/ceph (rbd0): request=1 time=580 us
# min/avg/max/mdev = 420 us / 650 us / 1.2 ms / 180 us
```

### Benchmarking Storage Distribuito

```bash
# fio distribuito su piu' nodi (client/server mode)
# Su ogni nodo worker:
fio --server --daemonize=/tmp/fio.pid

# Dal nodo coordinator:
fio --client=worker1,worker2,worker3 /tmp/distributed-test.fio

# Esempio job file per test distribuito
cat > /tmp/distributed-test.fio <<'DISTEOF'
[global]
ioengine=libaio
direct=1
runtime=120
time_based=1
group_reporting=1
lat_percentiles=1

[distributed-rw]
rw=randrw
rwmixread=70
bs=4k
iodepth=32
numjobs=4
size=5G
filename=/mnt/ceph-storage/fio-test-${HOSTNAME}
DISTEOF

# Benchmark specifico per Ceph RBD
rbd bench --io-type write --io-size 4K --io-threads 16 \
  --io-total 4G --pool kubernetes pvc-test-volume

rbd bench --io-type read --io-size 4K --io-threads 16 \
  --io-total 4G --pool kubernetes pvc-test-volume

# Benchmark Ceph RADOS diretto (livello piu' basso)
rados bench -p benchmark 60 write --no-cleanup
rados bench -p benchmark 60 seq
rados bench -p benchmark 60 rand
rados -p benchmark cleanup

# Benchmark MinIO con warp (tool ufficiale MinIO)
# https://github.com/minio/warp
warp mixed --host=minio{1...4}:9000 \
  --access-key=minioadmin --secret-key=minio-secret \
  --autoterm --concurrent 32 --obj.size 1MiB \
  --duration 5m --bucket warp-benchmark
```

### Interpretare i Risultati

| Metrica | Database OLTP | Data Lake | Backup/Archive |
|---------|--------------|-----------|----------------|
| IOPS 4K random | > 50.000 | Non critico | Non critico |
| Throughput seq | > 500 MB/s | > 2 GB/s | > 1 GB/s |
| Latenza p99 | < 2 ms | < 50 ms | < 500 ms |
| Latenza p99.9 | < 10 ms | < 200 ms | Non critico |

Regola pratica: se la latenza p99.9 e' piu' di 10x la latenza media, c'e' un problema di tail latency (garbage collection SSD, network jitter, noisy neighbor).

---

## 20. Cloud Storage Comparison

### Block Storage

| Parametro | AWS EBS gp3 | AWS EBS io2 | Azure Managed Disk Premium v2 | GCP Persistent Disk SSD |
|-----------|-------------|-------------|-------------------------------|-------------------------|
| IOPS max | 16.000 | 256.000 | 80.000 | 100.000 |
| Throughput max | 1.000 MB/s | 4.000 MB/s | 1.200 MB/s | 1.200 MB/s |
| Latenza tipica | < 1 ms | < 1 ms | < 1 ms | < 1 ms |
| Dimensione max | 16 TB | 64 TB | 64 TB | 64 TB |
| Prezzo base/GB/mese | ~$0.08 | ~$0.125 | ~$0.10 | ~$0.17 |
| Multi-attach | No (io2 si) | Si | Si | Si (read-only) |
| Encryption default | Si (KMS) | Si (KMS) | Si (PMK/CMK) | Si (CSEK/CMEK) |

Nota: gp3 include 3.000 IOPS e 125 MB/s nel prezzo base; IOPS e throughput aggiuntivi hanno costo separato. io2 scala IOPS indipendentemente dalla dimensione.

### File Storage

| Parametro | AWS EFS | Azure Files Premium | GCP Filestore |
|-----------|---------|---------------------|---------------|
| Protocollo | NFSv4.1 | NFS 4.1 + SMB 3.1.1 | NFSv3, NFSv4.1 |
| Throughput max | 10+ GB/s (elastic) | 10 GB/s | 16 GB/s (enterprise) |
| Latenza | < 1 ms (One Zone) | < 1 ms | sub-ms |
| Multi-AZ | Si (Standard) | ZRS disponibile | Regionale (Enterprise) |
| Prezzo/GB/mese | ~$0.30 (Standard) | ~$0.16 (Premium) | ~$0.20 (Basic HDD) |
| Scaling | Automatico (elastic) | Provisioned | Provisioned |
| Access K8s | EFS CSI driver | Azure Files CSI | Filestore CSI |

AWS EFS e' l'unico che scala automaticamente senza pre-provisioning. Azure Files e' l'unico che supporta sia NFS che SMB dallo stesso share. GCP Filestore Enterprise offre throughput piu' alto per istanza ma e' provisioned.

### Object Storage

| Parametro | AWS S3 Standard | Azure Blob Hot | GCP Standard | Cloudflare R2 |
|-----------|-----------------|----------------|--------------|----------------|
| Prezzo/GB/mese | $0.023 | $0.0184 | $0.020 | $0.015 |
| PUT (per 1K ops) | $0.005 | $0.0065 | $0.005 | $0.0045 |
| GET (per 1K ops) | $0.0004 | $0.0004 | $0.0004 | $0.0036 |
| Egress/GB | $0.09 (primi 10TB) | $0.087 | $0.12 (primo 1TB) | $0.00 (gratis) |
| Durabilita' | 99.999999999% (11 9s) | 99.999999999999% (14 9s, GRS) | 99.999999999% | 99.999999999% |
| Disponibilita' SLA | 99.99% | 99.9% (Hot) | 99.99% | 99.99% |
| Classi/Tiers | 7 (Standard, IA, One Zone-IA, Glacier IR, Glacier Flexible, Glacier Deep, Intelligent) | 5 (Hot, Cool, Cold, Archive, Premium) | 4 (Standard, Nearline, Coldline, Archive) + Autoclass | 1 (Standard) |
| S3-compatible | Nativo | Via endpoint S3 | Via interop XML API | Si (pienamente) |

#### Costi Nascosti

I costi reali dello storage cloud sono tipicamente 2-5 volte superiori al costo del solo storage per GB a causa di:

- **Egress**: trasferimento dati in uscita dal provider. Cloudflare R2 e' l'unico con egress gratuito, rendendolo ideale per content delivery.
- **API operations**: GET/PUT/LIST/DELETE hanno costi per-operazione. Workload con milioni di piccoli file possono generare costi API superiori al costo dello storage stesso.
- **Retrieval fees**: accedere a dati in tier cold/archive ha un costo aggiuntivo per-GB. S3 Glacier Flexible richiede $0.01/GB per retrieval standard.
- **Replicazione cross-region**: raddoppia o triplica il costo dello storage base.
- **Early deletion**: eliminare un oggetto da un tier cold prima del periodo minimo di retention ha un costo (es. Glacier Deep Archive ha un minimo di 180 giorni).

#### GCS Autoclass

GCS Autoclass e' una funzionalita' unica che sposta automaticamente gli oggetti tra le classi di storage in base ai pattern di accesso reali, senza necessita' di configurare lifecycle policies manuali. Autoclass monitora l'accesso e promuove/degrada gli oggetti tra Standard, Nearline, Coldline e Archive. Puo' ridurre i costi dello storage del 30-50% per workload con pattern di accesso variabili.

### Decision Matrix

| Scenario | Soluzione Consigliata |
|----------|-----------------------|
| Database OLTP ad alta performance | AWS EBS io2 / Azure Ultra Disk / on-prem NVMe con Ceph o Mayastor |
| File condivisi multi-pod K8s (RWX) | AWS EFS / Azure Files NFS / CephFS / Longhorn RWX |
| Data lake e analytics | S3 / GCS con Autoclass / Ceph RGW on-prem |
| Backup e disaster recovery | S3 Glacier / Azure Archive / Wasabi / MinIO on-prem con WORM |
| Content delivery ad alto egress | Cloudflare R2 (zero egress) |
| Compliance WORM (finanza, PA) | S3 Object Lock / MinIO WORM (COMPLIANCE mode) / Azure Immutable Blob |
| Multi-cloud portabilita' | MinIO / Ceph RGW on-prem come S3 gateway unificato |
| Edge / risorse limitate | Longhorn / OpenEBS Jiva |
| Massima performance K8s on-prem | Ceph RBD (NVMe pool) / OpenEBS Mayastor |

---

## Esercizi

1. **Ceph cluster lab** — Deploya un cluster Ceph a 3 nodi con cephadm (o con Rook-Ceph su Kubernetes). Crea un pool replicato (size 3) e un pool erasure coded (4+2). Confronta spazio effettivo utilizzabile, throughput in scrittura e tempo di recovery dopo il drain di un OSD.

2. **MinIO S3-compatible storage** — Deploya MinIO su Kubernetes con un StatefulSet a 4 repliche e erasure coding. Configura un bucket con lifecycle policy (eliminazione oggetti dopo 30 giorni). Testa upload/download con `mc` CLI e verifica la compatibilita' AWS SDK con uno script Python boto3.

3. **CSI driver e StorageClass** — Configura Rook-Ceph CSI driver in un cluster Kubernetes. Crea due StorageClass (una con replica 3, una con erasure coding). Deploya un Pod con PVC su ciascuna StorageClass, scrivi dati, e verifica persistenza dopo restart del Pod.

4. **Capacity planning e alerting** — Configura monitoring dello storage con Prometheus (ceph_exporter o Rook metrics). Crea alert per: utilizzo superiore all'80%, OSD down, PG degradati. Implementa un Grafana dashboard con proiezione di esaurimento capacita' basata su trend di crescita.

5. **Disaster recovery e migrazione** — Configura Ceph RBD mirroring tra due cluster (primario e secondario). Esegui un failover simulato: promuovi le immagini nel cluster secondario, aggiorna i PVC in Kubernetes, e verifica che le applicazioni riprendano senza perdita di dati.

---

## Letture e Riferimenti

### Documentazione ufficiale

- Ceph documentation. https://docs.ceph.com/en/latest/
- MinIO documentation. https://min.io/docs/minio/kubernetes/upstream/
- Rook-Ceph documentation. https://rook.io/docs/rook/latest/
- Longhorn documentation. https://longhorn.io/docs/
- Kubernetes Persistent Volumes. https://kubernetes.io/docs/concepts/storage/persistent-volumes/
- CSI specification. https://github.com/container-storage-interface/spec

### Libri

- van der Meulen, R. *Learning Ceph: A Practical Guide to Designing, Implementing, and Managing Ceph*. Packt, 2019.
- Haiying, M. *Mastering Ceph: Infrastructure Storage Solutions with the Latest Ceph Release*. Packt, 2019.

---

## Riferimenti Incrociati

| Modulo | Titolo | Relazione |
|---|---|---|
| [05-kubernetes](05-kubernetes.md) | Kubernetes | PVC, StorageClass e CSI driver sono primitive Kubernetes per consumare storage distribuito |
| [11-database-management](11-database-management.md) | Database Management | I database stateful su K8s richiedono storage persistente con garanzie di consistenza |
| [08-monitoring-observability](08-monitoring-observability.md) | Monitoring e Observability | Metriche Ceph/MinIO esposte a Prometheus per alerting su capacita' e salute cluster |
| [04-infrastructure-as-code](04-infrastructure-as-code.md) | Infrastructure as Code | Provisioning declarativo di StorageClass, pool Ceph e bucket MinIO via Terraform |
| [21-finops-cost-governance](21-finops-cost-governance.md) | FinOps + Cost Governance | Capacity planning e lifecycle policy per ottimizzare i costi dello storage |
| [18-troubleshooting-e-guide-pratiche](18-troubleshooting-e-guide-pratiche.md) | Troubleshooting | Diagnosi di PVC pending, OSD down, e PG degradati con procedure strutturate |

---

## Glossario

| Termine | Definizione |
|---|---|
| **Ceph** | Sistema di storage distribuito open source che offre block, file e object storage in un cluster unificato. |
| **OSD (Object Storage Daemon)** | Processo Ceph che gestisce un disco fisico e si occupa di replica, recovery e rebalancing. |
| **MON (Monitor)** | Processo Ceph che mantiene la cluster map e gestisce il consenso tramite Paxos. |
| **MDS (Metadata Server)** | Processo Ceph necessario per CephFS che gestisce il namespace del filesystem. |
| **CRUSH map** | Algoritmo e mappa che determinano la distribuzione dei dati nei nodi Ceph senza lookup centralizzato. |
| **Erasure coding** | Tecnica che divide i dati in frammenti con parita' (es. 4+2), offrendo fault tolerance con meno overhead della replica. |
| **PVC (PersistentVolumeClaim)** | Richiesta Kubernetes per storage persistente che viene soddisfatta da un PersistentVolume. |
| **StorageClass** | Risorsa Kubernetes che definisce il tipo di storage, il provisioner CSI e i parametri di configurazione. |
| **CSI (Container Storage Interface)** | Standard che permette ai driver di storage di integrarsi con Kubernetes e altri orchestratori. |
| **MinIO** | Object storage ad alte prestazioni compatibile con l'API S3 di AWS, deployabile on-prem o su cloud. |
| **Rook** | Operatore Kubernetes che automatizza il deployment e la gestione di Ceph su cluster K8s. |
| **Longhorn** | Motore di storage distribuito cloud-native per Kubernetes, sviluppato da SUSE/Rancher. |
| **RBD (RADOS Block Device)** | Interfaccia block storage di Ceph che espone volumi a VM e container. |
| **Placement Group (PG)** | Unita' logica di distribuzione dati in Ceph che mappa oggetti a OSD tramite CRUSH. |
| **Capacity planning** | Processo di stima e pianificazione delle risorse storage necessarie in base a crescita e SLA. |
