# NFS e iSCSI - Storage Condiviso per Proxmox VE

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 1 — Fondamenti · Modulo 03.2 (vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 03.1 (LVM/LVM-Thin); networking di base (subnetting, routing, MTU/jumbo frames); concetti TCP, NFSv3 vs v4, iSCSI initiator/target/LUN.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. distinguere file-level (NFS) da block-level (iSCSI) e identificare le implicazioni operative su locking, performance, multipath, snapshot;
> 2. configurare un server NFS (Linux con `nfs-kernel-server`, oppure NAS dedicato) e montarlo su Proxmox in `/etc/pve/storage.cfg`;
> 3. configurare un target iSCSI (`targetcli` su Linux, o un NAS), scoprire dall'initiator Proxmox (`iscsiadm --discovery`), e collegare LUN come storage block-level;
> 4. dimensionare il networking dedicato per traffico storage (rete privata, jumbo frames MTU 9000, separazione dal traffico VM/management);
> 5. abilitare multipath (`multipath-tools`, `multipath.conf`) per HA del path con failover deterministico e leggere lo stato (`multipath -ll`);
> 6. mappare scenari VMware tipici (NFS datastore, iSCSI VMFS) su pendant Proxmox e capire dove la migrazione e diretta e dove richiede ridisegno (snapshot su iSCSI shared, locking su NFS sopra Proxmox).
> **Tempo stimato:** lettura 90-120 min · lab 180-240 min
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-26
> **Versioni di riferimento:** Proxmox VE 8.x, NFSv3/v4.1/v4.2, iSCSI software adapter (open-iscsi 2.1.x), multipath-tools 0.9+.

## Mappa concettuale

```
+======================================================+
|  Storage condiviso — NFS vs iSCSI                    |
+======================================================+
|                                                      |
|              NFS (file-level)                        |
|     +-----------------------------+                  |
|     |  NFS Server                 |                  |
|     |  /export/proxmox-vms        |                  |
|     |    +- vm-100/disk.qcow2     |                  |
|     |    +- vm-101/disk.qcow2     |                  |
|     +-------------+---------------+                  |
|                   |                                  |
|        TCP/2049 (or RDMA)                            |
|                   |                                  |
|     +-------------v---------------+                  |
|     |  Proxmox Cluster (multi-nodo)                  |
|     |  /mnt/pve/nas-vms (mountpoint)                 |
|     |  storage.cfg: nfs                              |
|     |  Snapshot via qcow2 internal                   |
|     +------------------------------+                 |
|                                                      |
|              iSCSI (block-level)                     |
|     +-----------------------------+                  |
|     |  iSCSI Target               |                  |
|     |  iqn.YYYY-MM.example:lun-0  |                  |
|     |  (LUN 100 GB block device)  |                  |
|     +-------------+---------------+                  |
|                   |                                  |
|        TCP/3260 (with optional CHAP)                 |
|                   |                                  |
|     +-------------v---------------+                  |
|     |  Proxmox initiator                             |
|     |  /dev/disk/by-id/scsi-3600... (raw block)      |
|     |  storage.cfg:                                  |
|     |    iscsi  (raw)                                |
|     |    lvm    (LVM su LUN, *no snapshot*)          |
|     +------------------------------+                 |
|                                                      |
|     Per multipath: 2+ path verso 2+ portal,          |
|     `multipath-tools` aggrega in /dev/mapper/mpathN  |
|                                                      |
+======================================================+
```

Idee guida del modulo:

1. **Block vs file: il bivio iniziale.** Proxmox usa NFS per immagini qcow2 (snapshot interni, file-level locking) o iSCSI per LVM su LUN (block-level, no snapshot Proxmox-managed senza qcow2 sopra). VMware via VMFS uniforma la scelta sopra una LUN; lato Proxmox e una decisione esplicita: quando vuoi snapshot su shared storage senza Ceph, usi NFS + qcow2.
2. **NFSv4.1 fa locking serio. NFSv3 no.** NFSv3 si appoggia a NLM/NSM, non sempre robusti in cluster moderni. NFSv4.1 ha lease management nativo, byte-range locking, sessioni. Per cluster Proxmox, raccomandato NFSv4.1+. Sintassi mount: opzioni `vers=4.1`, `proto=tcp`, eventualmente `nconnect=4` (multi-connessione kernel ≥ 5.3).
3. **iSCSI senza multipath e SPOF.** Una rotta sola = un punto di failure (NIC, switch, cavo). Best practice: 2+ portal, 2+ NIC dedicate, `multipath-tools` con policy `round-robin` o `service-time`. Modello tipico: due bridge L2 separati o due VLAN dedicate, MTU 9000.
4. **Jumbo frames hanno costi.** MTU 9000 riduce overhead per grossi trasferimenti (backup, vMotion-like) ma deve essere *coerente end-to-end*: NIC + switch + server. Mismatch produce frammentazione TCP visibile come latenza erratica. Verificare con `ping -M do -s 8972 <target>` (8972 = 9000 - 28 byte di header IP+ICMP).
5. **CHAP minimum, IPsec optional.** iSCSI in chiaro su rete interna isolata e accettabile in molti ambienti; per traffico su rete condivisa, abilitare CHAP bidirezionale (`mutual`) e considerare iSCSI su IPsec o IPsec tunnel separato. NFS over Kerberos (`sec=krb5p`) e l'analogo per NFS.

## Indice

1. [Introduzione allo Storage Condiviso](#introduzione-allo-storage-condiviso)
2. [NFS - Network File System](#nfs---network-file-system)
3. [NFS Server Setup](#nfs-server-setup)
4. [NFS Client e Proxmox](#nfs-client-e-proxmox)
5. [NFSv3 vs NFSv4](#nfsv3-vs-nfsv4)
6. [NFS Performance Tuning](#nfs-performance-tuning)
7. [iSCSI - Internet Small Computer Systems Interface](#iscsi---internet-small-computer-systems-interface)
8. [iSCSI Target Setup](#iscsi-target-setup)
9. [iSCSI Initiator su Proxmox](#iscsi-initiator-su-proxmox)
10. [Multipath I/O](#multipath-io)
11. [LUN Management](#lun-management)
12. [Confronto NFS vs iSCSI](#confronto-nfs-vs-iscsi)
13. [Scenari di Migrazione da VMware](#scenari-di-migrazione-da-vmware)
14. [Troubleshooting](#troubleshooting)

---

## Introduzione allo Storage Condiviso

Lo storage condiviso (shared storage) è un requisito fondamentale per funzionalità enterprise come **live migration**, **High Availability** e **backup centralizzati** in un cluster Proxmox VE. NFS e iSCSI sono i protocolli di storage di rete piu diffusi e maturi, utilizzati ampiamente sia in ambienti VMware che Proxmox.

### Mappatura VMware → Proxmox

| VMware | Proxmox Equivalente |
|---|---|
| NFS Datastore | NFS Storage |
| VMFS su iSCSI LUN | LVM su iSCSI LUN |
| vSphere Storage I/O Control | Linux I/O scheduler + QoS |
| Storage vMotion (NFS) | Live Migration (NFS) |
| VAAI (NFS) | NFS server-side copy |
| VAAI (iSCSI) | SCSI UNMAP/WRITE SAME |

### Architettura Storage Condiviso

```
┌─────────────────────────────────────────────────────────────┐
│                  Cluster Proxmox VE                          │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐               │
│  │  PVE1    │    │  PVE2    │    │  PVE3    │               │
│  │          │    │          │    │          │               │
│  │ NFS mount│    │ NFS mount│    │ NFS mount│               │
│  │ iSCSI    │    │ iSCSI    │    │ iSCSI    │               │
│  │ initiator│    │ initiator│    │ initiator│               │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘               │
│       │               │               │                     │
│  ─────┼───────────────┼───────────────┼──── Storage Network │
│       │               │               │     (10/25 GbE)     │
│       │               │               │                     │
│  ┌────▼───────────────▼───────────────▼─────────────────┐   │
│  │              Storage Server / NAS / SAN               │   │
│  │                                                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │   │
│  │  │  NFS Export  │  │ iSCSI Target│  │  RAID Array  │  │   │
│  │  │ /export/vms  │  │ iqn.2026... │  │ RAID6/10     │  │   │
│  │  └─────────────┘  └─────────────┘  └──────────────┘  │   │
│  │                                                       │   │
│  │  Hardware: TrueNAS, Synology, NetApp, Pure Storage    │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## NFS - Network File System

NFS è un protocollo di file sharing basato su rete che permette l'accesso trasparente a filesystem remoti. In Proxmox, NFS è comunemente utilizzato per storage condiviso di immagini ISO, template, backup e, in alcuni casi, dischi VM.

### Vantaggi di NFS per Proxmox

- **Semplicità:** Configurazione minima, nessun software aggiuntivo
- **Flessibilità:** Supporta diversi tipi di contenuto (images, iso, backup, vztmpl, snippets)
- **Live Migration:** Supporto nativo per migrazione live delle VM
- **File-level access:** Gestione diretta dei file (cp, mv, ls)
- **Formato qcow2:** Supporto snapshot qcow2 su NFS

### Limitazioni di NFS

- Performance inferiori rispetto a iSCSI per workload block-level
- Overhead del protocollo su high IOPS workload
- Sensibilità alla latenza di rete
- Possibili problemi di locking con accesso concorrente intensivo

---

## NFS Server Setup

### Server NFS su Linux (Debian/Ubuntu)

```bash
# Installare NFS server
apt update
apt install nfs-kernel-server

# Creare le directory di export
mkdir -p /export/proxmox/images
mkdir -p /export/proxmox/iso
mkdir -p /export/proxmox/backup
mkdir -p /export/proxmox/templates

# Impostare permessi
chown -R nobody:nogroup /export/proxmox
chmod -R 755 /export/proxmox

# Configurare /etc/exports
cat << 'EOF' > /etc/exports
# Proxmox VM Images (accesso da rete storage 10.10.10.0/24)
/export/proxmox/images   10.10.10.0/24(rw,sync,no_subtree_check,no_root_squash)

# ISO Images (read-only per i nodi, rw per admin)
/export/proxmox/iso      10.10.10.0/24(rw,sync,no_subtree_check,no_root_squash)

# Backup (rw per tutti i nodi)
/export/proxmox/backup   10.10.10.0/24(rw,sync,no_subtree_check,no_root_squash)

# Container Templates
/export/proxmox/templates 10.10.10.0/24(rw,sync,no_subtree_check,no_root_squash)
EOF

# Applicare la configurazione
exportfs -arv
# exporting 10.10.10.0/24:/export/proxmox/images
# exporting 10.10.10.0/24:/export/proxmox/iso
# exporting 10.10.10.0/24:/export/proxmox/backup
# exporting 10.10.10.0/24:/export/proxmox/templates

# Verificare gli export attivi
exportfs -v
showmount -e localhost

# Abilitare e avviare il servizio
systemctl enable --now nfs-kernel-server
systemctl status nfs-kernel-server

# Firewall (se attivo)
ufw allow from 10.10.10.0/24 to any port nfs
# Oppure:
ufw allow from 10.10.10.0/24 to any port 2049
ufw allow from 10.10.10.0/24 to any port 111
```

### Opzioni Export Dettagliate

| Opzione | Descrizione | Raccomandazione |
|---|---|---|
| `rw` | Lettura/scrittura | Sì per images/backup |
| `ro` | Solo lettura | Per ISO se solo download |
| `sync` | Scritture sincrone (sicuro) | Sempre per VM storage |
| `async` | Scritture asincrone (veloce ma rischioso) | Solo backup non critici |
| `no_subtree_check` | Disabilita subtree checking | Sempre (performance) |
| `no_root_squash` | Mantiene permessi root | Necessario per Proxmox |
| `root_squash` | Mappa root a nobody | Non usare per Proxmox |
| `all_squash` | Mappa tutti a nobody | Non usare per Proxmox |
| `crossmnt` | Attraversa mount points | Se export contiene sottomount |
| `fsid=0` | Root export per NFSv4 | Solo per NFSv4 puro |
| `sec=sys` | Autenticazione Unix standard | Default |
| `sec=krb5p` | Kerberos con privacy | Ambienti ad alta sicurezza |

### Server NFS su TrueNAS

```
Configurazione via GUI TrueNAS:

1. Storage → Pools → Create Dataset
   - Name: proxmox-images
   - Compression: lz4
   - Sync: Standard
   - Case Sensitivity: Sensitive

2. Sharing → NFS → Add
   - Path: /mnt/tank/proxmox-images
   - Authorized Networks: 10.10.10.0/24
   - Maproot User: root
   - Maproot Group: wheel
   - Enabled: Yes

3. Services → NFS → Enable
   - NFSv4: Enabled
   - Number of servers: 16 (o numero di CPU core)
   - Bind IP: 10.10.10.254 (interfaccia storage network)
```

---

## NFS Client e Proxmox

### Aggiungere NFS Storage dalla GUI

```
Datacenter → Storage → Add → NFS

Parametri:
- ID: nfs-images
- Server: 10.10.10.254
- Export: /export/proxmox/images
- Content: Disk image, Container
- Nodes: All (o selezionare nodi specifici)
- Enable: Yes
- Max Backups: 5 (se usato per backup)
```

### Aggiungere NFS Storage dalla CLI

```bash
# Storage per VM disk images
pvesm add nfs nfs-images \
    --server 10.10.10.254 \
    --export /export/proxmox/images \
    --content images,rootdir \
    --options vers=4.2,soft,timeo=150,retrans=3

# Storage per ISO
pvesm add nfs nfs-iso \
    --server 10.10.10.254 \
    --export /export/proxmox/iso \
    --content iso,vztmpl

# Storage per backup
pvesm add nfs nfs-backup \
    --server 10.10.10.254 \
    --export /export/proxmox/backup \
    --content backup \
    --maxfiles 5

# Verificare gli storage NFS
pvesm status
pvesm nfsscan 10.10.10.254

# Verificare il mount
mount | grep nfs
df -h | grep nfs

# Test di scrittura
dd if=/dev/zero of=/mnt/pve/nfs-images/testfile bs=1M count=100
rm /mnt/pve/nfs-images/testfile
```

### Mount Options Raccomandate

```bash
# Opzioni di mount NFS per Proxmox (in /etc/pve/storage.cfg o via pvesm)
# vers=4.2       → Usare NFSv4.2 per massime prestazioni
# soft            → Timeout e errore (non bloccare la VM indefinitamente)
# timeo=150       → Timeout 15 secondi
# retrans=3       → 3 tentativi prima di errore
# rsize=1048576   → Read buffer 1MB
# wsize=1048576   → Write buffer 1MB
# noatime         → Disabilita access time update
# _netdev         → Mount dopo che la rete è attiva

# Esempio mount manuale con opzioni ottimizzate
mount -t nfs -o vers=4.2,soft,timeo=150,retrans=3,rsize=1048576,wsize=1048576,noatime \
    10.10.10.254:/export/proxmox/images /mnt/pve/nfs-images
```

---

## NFSv3 vs NFSv4

### Confronto Dettagliato

| Caratteristica | NFSv3 | NFSv4 | NFSv4.1 | NFSv4.2 |
|---|---|---|---|---|
| **Porte** | Multiple (portmapper) | Singola (2049) | Singola (2049) | Singola (2049) |
| **Firewall** | Complesso | Semplice | Semplice | Semplice |
| **Stato** | Stateless | Stateful | Stateful | Stateful |
| **Locking** | NLM separato | Integrato | Integrato | Integrato |
| **Sicurezza** | AUTH_SYS | Kerberos | Kerberos | Kerberos |
| **Compound ops** | No | Si | Si | Si |
| **pNFS** | No | No | Si | Si |
| **Server-side copy** | No | No | No | Si |
| **Sparse files** | No | No | No | Si |
| **Space reservation** | No | No | No | Si (fallocate) |
| **ACL** | POSIX ACL | NFSv4 ACL | NFSv4 ACL | NFSv4 ACL |
| **Performance** | Buona | Buona+ | Molto buona | Eccellente |
| **Compatibilità** | Universale | Ampia | Buona | Crescente |

### Configurazione NFSv4 sul Server

```bash
# Forzare NFSv4 sul server
# /etc/default/nfs-kernel-server
RPCMOUNTDOPTS="--manage-gids"
NEED_SVCGSSD=""

# /etc/default/nfs-common
NEED_STATD="no"
NEED_IDMAPD="yes"

# Configurare ID mapping
# /etc/idmapd.conf
[General]
Domain = lab.local
Verbosity = 0

[Mapping]
Nobody-User = nobody
Nobody-Group = nogroup

# Riavviare servizi
systemctl restart nfs-kernel-server
systemctl restart nfs-idmapd

# Verificare versione NFS in uso
nfsstat -s
cat /proc/fs/nfsd/versions
# -2 +3 +4 +4.1 +4.2
```

### Configurazione NFSv4 sul Client (Proxmox)

```bash
# Verificare versione NFS montata
nfsstat -m
# /mnt/pve/nfs-images from 10.10.10.254:/export/proxmox/images
# Flags: rw,relatime,vers=4.2,rsize=1048576,wsize=1048576,namlen=255,...

# Forzare NFSv4.2
mount -t nfs4 -o vers=4.2 10.10.10.254:/export/proxmox/images /mnt/test

# Verificare il supporto server-side copy (NFSv4.2)
# Se disponibile, operazioni come "cp" tra file sullo stesso NFS
# vengono eseguite sul server senza trasferire dati sulla rete
```

---

## NFS Performance Tuning

### Lato Server

```bash
# Aumentare il numero di thread NFS
# /etc/default/nfs-kernel-server
RPCNFSDCOUNT=32    # Default 8, impostare = numero CPU core

# Oppure runtime:
echo 32 > /proc/fs/nfsd/threads

# Tuning kernel per NFS server
cat << 'EOF' >> /etc/sysctl.d/99-nfs-tuning.conf
# Network buffer sizes
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.core.rmem_default = 1048576
net.core.wmem_default = 1048576
net.ipv4.tcp_rmem = 4096 1048576 16777216
net.ipv4.tcp_wmem = 4096 1048576 16777216

# TCP tuning
net.ipv4.tcp_timestamps = 1
net.ipv4.tcp_window_scaling = 1
net.ipv4.tcp_sack = 1
net.core.netdev_max_backlog = 30000
net.core.somaxconn = 4096

# NFS cache
sunrpc.tcp_slot_table_entries = 128
EOF
sysctl -p /etc/sysctl.d/99-nfs-tuning.conf

# Filesystem sottostante: XFS è raccomandato per NFS server
mkfs.xfs -f -d agcount=32 -l size=256m,lazy-count=1 /dev/vg-nfs/lv-export
```

### Lato Client (Proxmox)

```bash
# Tuning mount options in /etc/pve/storage.cfg
# nfs: nfs-images
#     export /export/proxmox/images
#     path /mnt/pve/nfs-images
#     server 10.10.10.254
#     content images
#     options vers=4.2,rsize=1048576,wsize=1048576,soft,timeo=150,retrans=3,noatime

# Tuning slot table NFS client
echo 128 > /proc/sys/sunrpc/tcp_slot_table_entries
echo "options sunrpc tcp_slot_table_entries=128" >> /etc/modprobe.d/sunrpc.conf

# Network tuning sul client
cat << 'EOF' >> /etc/sysctl.d/99-nfs-client-tuning.conf
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 1048576 16777216
net.ipv4.tcp_wmem = 4096 1048576 16777216
EOF
sysctl -p /etc/sysctl.d/99-nfs-client-tuning.conf

# Jumbo frames (se supportato dall'infrastruttura di rete)
ip link set eth1 mtu 9000
# Aggiungere in /etc/network/interfaces:
# auto eth1
# iface eth1 inet static
#     address 10.10.10.1/24
#     mtu 9000
```

### Benchmark NFS

```bash
# Test throughput sequenziale
dd if=/dev/zero of=/mnt/pve/nfs-images/testfile bs=1M count=1024 oflag=direct
dd if=/mnt/pve/nfs-images/testfile of=/dev/null bs=1M iflag=direct

# Test con fio
fio --name=nfs-seq-write \
    --directory=/mnt/pve/nfs-images \
    --rw=write \
    --bs=1M \
    --size=1G \
    --numjobs=4 \
    --direct=1 \
    --group_reporting

fio --name=nfs-rand-rw \
    --directory=/mnt/pve/nfs-images \
    --rw=randrw \
    --bs=4k \
    --size=512M \
    --numjobs=8 \
    --iodepth=32 \
    --direct=1 \
    --group_reporting

# Monitorare NFS statistics
nfsstat -c    # Client stats
nfsstat -s    # Server stats
nfsiostat 5   # I/O stats ogni 5 secondi
mountstats /mnt/pve/nfs-images  # Statistiche dettagliate mount
```

---

## iSCSI - Internet Small Computer Systems Interface

iSCSI è un protocollo che trasporta comandi SCSI su rete TCP/IP, permettendo l'accesso a storage di blocco (block-level) attraverso la rete. Rispetto a NFS, iSCSI offre performance migliori per workload VM grazie all'accesso diretto ai blocchi.

### Terminologia iSCSI

```
┌──────────────────────────────────────────────────────────┐
│                    iSCSI Terminology                      │
│                                                           │
│  TARGET (Server)                                          │
│  ┌────────────────────────────────────────────────────┐   │
│  │  IQN: iqn.2026-03.com.lab:storage.target01        │   │
│  │                                                    │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐   │   │
│  │  │  LUN 0     │  │  LUN 1     │  │  LUN 2     │   │   │
│  │  │  100 GB    │  │  200 GB    │  │  500 GB    │   │   │
│  │  │  (vm-100)  │  │  (vm-101)  │  │  (backup)  │   │   │
│  │  └────────────┘  └────────────┘  └────────────┘   │   │
│  └────────────────────────────────────────────────────┘   │
│                                                           │
│  INITIATOR (Client - Proxmox)                             │
│  ┌────────────────────────────────────────────────────┐   │
│  │  IQN: iqn.2026-03.com.lab:pve1.initiator          │   │
│  │                                                    │   │
│  │  Login → Target → Accesso a LUN come /dev/sdX      │   │
│  │  /dev/sdb (LUN 0) → LVM → VM disk                 │   │
│  │  /dev/sdc (LUN 1) → LVM → VM disk                 │   │
│  └────────────────────────────────────────────────────┘   │
│                                                           │
│  IQN Format: iqn.YYYY-MM.reverse-domain:identifier       │
│  Portal: IP:Port (default 3260)                          │
│  LUN: Logical Unit Number (disco virtuale nel target)    │
│  ACL: Access Control List (chi può accedere)             │
│  CHAP: Challenge-Handshake Authentication Protocol        │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## iSCSI Target Setup

### Setup con targetcli (Linux)

```bash
# Installare targetcli
apt install targetcli-fb

# Avviare targetcli
targetcli

# Dentro targetcli (interactive shell):

# 1. Creare backstores (dischi fisici o LV da esporre)
/backstores/block create lun0 /dev/vg-iscsi/lv-lun0
/backstores/block create lun1 /dev/vg-iscsi/lv-lun1

# Oppure usando file come backstore (meno performante):
/backstores/fileio create lun-file /export/iscsi/disk0.img 100G

# 2. Creare il target iSCSI
/iscsi create iqn.2026-03.com.lab:storage.target01

# 3. Configurare il portal (indirizzo di ascolto)
/iscsi/iqn.2026-03.com.lab:storage.target01/tpg1/portals create 10.10.10.254 3260

# 4. Creare le LUN nel target
/iscsi/iqn.2026-03.com.lab:storage.target01/tpg1/luns create /backstores/block/lun0
/iscsi/iqn.2026-03.com.lab:storage.target01/tpg1/luns create /backstores/block/lun1

# 5. Configurare ACL (chi può accedere)
/iscsi/iqn.2026-03.com.lab:storage.target01/tpg1/acls create iqn.2026-03.com.lab:pve1
/iscsi/iqn.2026-03.com.lab:storage.target01/tpg1/acls create iqn.2026-03.com.lab:pve2
/iscsi/iqn.2026-03.com.lab:storage.target01/tpg1/acls create iqn.2026-03.com.lab:pve3

# 6. Configurare CHAP authentication (opzionale ma raccomandato)
/iscsi/iqn.2026-03.com.lab:storage.target01/tpg1/acls/iqn.2026-03.com.lab:pve1 set auth userid=pve1user
/iscsi/iqn.2026-03.com.lab:storage.target01/tpg1/acls/iqn.2026-03.com.lab:pve1 set auth password=SecureP@ss123

# 7. Salvare e uscire
saveconfig
exit

# Verificare la configurazione
targetcli ls /

# Abilitare il servizio
systemctl enable --now rtslib-fb-targetctl

# Firewall
ufw allow 3260/tcp
```

### Setup iSCSI Target su TrueNAS

```
Configurazione via GUI TrueNAS:

1. Sharing → Block Shares (iSCSI)

2. Target Global Configuration:
   - Base Name: iqn.2026-03.com.lab
   - ISNS Servers: (vuoto o server ISNS)

3. Portals → Add:
   - Description: Proxmox Portal
   - IP Address: 10.10.10.254
   - Port: 3260

4. Initiator Groups → Add:
   - Allowed Initiators:
     iqn.2026-03.com.lab:pve1
     iqn.2026-03.com.lab:pve2
     iqn.2026-03.com.lab:pve3

5. Targets → Add:
   - Target Name: proxmox-storage
   - Portal Group: 1
   - Initiator Group: 1

6. Extents → Add:
   - Name: lun-vm-storage
   - Type: Device
   - Device: zvol/tank/iscsi-lun0
   - Logical Block Size: 4096

7. Associated Targets → Add:
   - Target: proxmox-storage
   - LUN ID: 0
   - Extent: lun-vm-storage
```

---

## iSCSI Initiator su Proxmox

### Configurazione dell'Initiator

```bash
# Installare open-iscsi (preinstallato su Proxmox)
apt install open-iscsi

# Configurare l'initiator name
echo "InitiatorName=iqn.2026-03.com.lab:pve1" > /etc/iscsi/initiatorname.iscsi

# Configurare autenticazione CHAP (se richiesta)
# /etc/iscsi/iscsid.conf
# node.session.auth.authmethod = CHAP
# node.session.auth.username = pve1user
# node.session.auth.password = SecureP@ss123

# Tuning parametri iSCSI
# /etc/iscsi/iscsid.conf
# node.session.timeo.replacement_timeout = 120
# node.conn[0].timeo.login_timeout = 15
# node.conn[0].timeo.logout_timeout = 15
# node.conn[0].timeo.noop_out_interval = 5
# node.conn[0].timeo.noop_out_timeout = 5
# node.session.initial_login_retry_max = 8
# node.session.queue_depth = 128
# node.session.cmds_max = 128

# Riavviare il servizio
systemctl restart iscsid
systemctl enable iscsid

# Scoprire i target disponibili
iscsiadm -m discovery -t sendtargets -p 10.10.10.254:3260
# Output:
# 10.10.10.254:3260,1 iqn.2026-03.com.lab:storage.target01

# Login al target
iscsiadm -m node -T iqn.2026-03.com.lab:storage.target01 -p 10.10.10.254:3260 --login

# Verificare le sessioni attive
iscsiadm -m session -P 3
# Output dettagliato con LUN, device paths, etc.

# I nuovi dispositivi appaiono come /dev/sdX
lsblk
lsscsi

# Configurare login automatico al boot
iscsiadm -m node -T iqn.2026-03.com.lab:storage.target01 -p 10.10.10.254:3260 \
    --op update -n node.startup -v automatic

# Logout
iscsiadm -m node -T iqn.2026-03.com.lab:storage.target01 -p 10.10.10.254:3260 --logout
```

### Aggiungere iSCSI Storage in Proxmox

```bash
# Aggiungere iSCSI target dalla CLI
pvesm add iscsi iscsi-storage \
    --portal 10.10.10.254 \
    --target iqn.2026-03.com.lab:storage.target01 \
    --content none

# Aggiungere LVM su iSCSI LUN
# 1. Prima, creare PV e VG sulla LUN iSCSI
pvcreate /dev/sdb    # La LUN appare come /dev/sdb
vgcreate vg-iscsi /dev/sdb

# 2. Aggiungere come storage LVM
pvesm add lvm iscsi-lvm \
    --vgname vg-iscsi \
    --content images,rootdir \
    --shared 1 \
    --base iscsi-storage:0.0.0.scsi-iqn.2026-03.com.lab:storage.target01-lun-0

# Oppure usare LVM-Thin su iSCSI
lvcreate -l 95%FREE -T vg-iscsi/thin-pool
pvesm add lvmthin iscsi-thin \
    --vgname vg-iscsi \
    --thinpool thin-pool \
    --content images,rootdir

# Dalla GUI:
# Datacenter → Storage → Add → iSCSI
# - ID: iscsi-storage
# - Portal: 10.10.10.254
# - Target: selezionare dal dropdown
#
# Poi: Datacenter → Storage → Add → LVM
# - ID: iscsi-lvm
# - Base Storage: iscsi-storage
# - Volume Group: vg-iscsi
# - Shared: Yes
```

---

## Multipath I/O

Multipath I/O fornisce ridondanza e load balancing per le connessioni iSCSI, utilizzando percorsi multipli tra l'initiator e il target.

### Configurazione Multipath

```bash
# Installare multipath-tools
apt install multipath-tools

# Configurare /etc/multipath.conf
cat << 'EOF' > /etc/multipath.conf
defaults {
    polling_interval     10
    path_grouping_policy multibus
    path_selector        "round-robin 0"
    failback             immediate
    no_path_retry        5
    user_friendly_names  yes
    find_multipaths      yes
}

blacklist {
    devnode "^(ram|raw|loop|fd|md|dm-|sr|scd|st)[0-9]*"
    devnode "^sd[a]$"    # Escludere il disco OS
}

devices {
    device {
        vendor                  "LIO-ORG"
        product                 ".*"
        path_grouping_policy    multibus
        path_selector           "round-robin 0"
        path_checker            tur
        failback                immediate
        no_path_retry           5
        rr_min_io_rq            1
    }
    device {
        vendor                  "TrueNAS"
        product                 "iSCSI Disk"
        path_grouping_policy    multibus
        path_selector           "round-robin 0"
        path_checker            tur
        failback                immediate
        no_path_retry           queue
    }
}
EOF

# Abilitare multipath
systemctl enable --now multipathd

# Configurare due percorsi iSCSI
# Percorso 1 (interfaccia eth1)
iscsiadm -m discovery -t sendtargets -p 10.10.10.254:3260
iscsiadm -m node -T iqn.2026-03.com.lab:storage.target01 -p 10.10.10.254:3260 --login

# Percorso 2 (interfaccia eth2)
iscsiadm -m discovery -t sendtargets -p 10.10.20.254:3260
iscsiadm -m node -T iqn.2026-03.com.lab:storage.target01 -p 10.10.20.254:3260 --login

# Verificare multipath
multipath -ll
# mpathb (360014380a2b4xxxx) dm-2 LIO-ORG,IBLOCK
# size=100G features='1 queue_if_no_path' hwhandler='1 alua'
# `-+- policy='round-robin 0' prio=50 status=active
#   |- 3:0:0:0  sdb 8:16 active ready running
#   `- 4:0:0:0  sdc 8:32 active ready running

# Il device multipath è /dev/mapper/mpathb
# Usare QUESTO per LVM:
pvcreate /dev/mapper/mpathb
vgcreate vg-iscsi-mpath /dev/mapper/mpathb

# Monitorare lo stato dei percorsi
multipathd show paths
multipathd show maps
```

### Architettura Multipath

```
┌─────────────────────────────────────────────────────────────┐
│                    Multipath I/O                             │
│                                                              │
│  ┌──────────────────────────────────┐                        │
│  │         Proxmox VE Node          │                        │
│  │                                  │                        │
│  │  ┌──────────────────────────┐    │                        │
│  │  │  /dev/mapper/mpathb      │    │                        │
│  │  │  (device-mapper multipath)│   │                        │
│  │  └──────┬────────┬──────────┘    │                        │
│  │         │        │               │                        │
│  │  ┌──────▼──┐  ┌──▼────────┐     │                        │
│  │  │/dev/sdb │  │/dev/sdc   │     │                        │
│  │  │(path 1) │  │(path 2)   │     │                        │
│  │  └────┬────┘  └────┬──────┘     │                        │
│  │       │            │             │                        │
│  │  ┌────▼────┐  ┌────▼──────┐     │                        │
│  │  │ eth1    │  │ eth2      │     │                        │
│  │  │10.10.10 │  │10.10.20   │     │                        │
│  │  └────┬────┘  └────┬──────┘     │                        │
│  └───────┼────────────┼────────────┘                        │
│          │            │                                      │
│  ════════╪════════════╪══════  Storage Network (2x10GbE)    │
│          │            │                                      │
│  ┌───────▼────────────▼────────────────────┐                │
│  │         iSCSI Target / SAN              │                │
│  │  Portal 1: 10.10.10.254:3260           │                │
│  │  Portal 2: 10.10.20.254:3260           │                │
│  │  LUN 0: 100GB (vm-storage)             │                │
│  └─────────────────────────────────────────┘                │
│                                                              │
│  Vantaggi:                                                   │
│  - Ridondanza: se un path fallisce, l'altro subentra        │
│  - Performance: round-robin tra i path disponibili          │
│  - Bandwidth: aggregazione della banda (2x 10Gbps)         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## LUN Management

### Gestione LUN dal Target

```bash
# targetcli: aggiungere una nuova LUN
targetcli

/backstores/block create lun2 /dev/vg-iscsi/lv-lun2
/iscsi/iqn.2026-03.com.lab:storage.target01/tpg1/luns create /backstores/block/lun2

saveconfig
exit

# Ridimensionare una LUN (se il backstore è un LV)
# 1. Espandere il LV
lvextend -L +100G /dev/vg-iscsi/lv-lun0
# 2. Il target riconosce automaticamente la nuova dimensione
# 3. Sul client, rescan dei dispositivi
iscsiadm -m node -T iqn.2026-03.com.lab:storage.target01 -R

# Rimuovere una LUN (assicurarsi che non sia in uso!)
targetcli
/iscsi/iqn.2026-03.com.lab:storage.target01/tpg1/luns delete lun2
/backstores/block delete lun2
saveconfig
exit
```

### Gestione LUN dal Client (Proxmox)

```bash
# Rescan per nuove LUN
iscsiadm -m session --rescan

# Elencare i dispositivi iSCSI
lsscsi
# [3:0:0:0]  disk    LIO-ORG  IBLOCK           4.0  /dev/sdb
# [3:0:0:1]  disk    LIO-ORG  IBLOCK           4.0  /dev/sdc
# [4:0:0:0]  disk    LIO-ORG  IBLOCK           4.0  /dev/sdd

# Informazioni sulla sessione iSCSI
iscsiadm -m session -P 3

# Verificare il target WWID per multipath
scsi_id -g -u /dev/sdb
# 360014380a2b4xxxx

# Monitorare I/O sulle sessioni iSCSI
iscsiadm -m session -s
```

---

## Confronto NFS vs iSCSI

### Tabella Comparativa

| Criterio | NFS | iSCSI |
|---|---|---|
| **Protocollo** | File-level | Block-level |
| **Performance random I/O** | Buona | Molto buona |
| **Performance sequential I/O** | Molto buona | Eccellente |
| **Latenza** | 0.5-2ms | 0.2-0.8ms |
| **CPU overhead** | Medio | Basso |
| **Formato disco** | qcow2, raw (file) | raw (LV/block) |
| **Snapshot** | qcow2 snapshot | LVM snapshot |
| **Thin provisioning** | qcow2 sparse | LVM-Thin |
| **Complessità setup** | Bassa | Media |
| **Multipath** | Non applicabile | Si |
| **Live Migration** | Si (nativo) | Si (con shared LVM) |
| **Multiple VM per LUN** | Si (file per VM) | Richiede LVM/cluster FS |
| **Gestione spazio** | Semplice (file) | Complessa (LUN/LV) |
| **Backup** | Facile (file copy) | Richiede snapshot |
| **Firewall** | Porta 2049 (NFSv4) | Porta 3260 |
| **Encryption nativa** | Kerberos (NFSv4) | IPsec o CHAP |

### Quando Usare NFS

- Storage per ISO, template e backup
- Cluster piccoli/medi senza SAN dedicata
- Quando serve semplicità di gestione
- Quando si usano snapshot qcow2
- TrueNAS/Synology come storage backend
- Migrazione rapida da VMware (NFS datastore → NFS Proxmox)

### Quando Usare iSCSI

- VM con workload I/O intensivo (database)
- Infrastruttura SAN esistente (NetApp, Pure, Dell EMC)
- Necessità di multipath per ridondanza
- Performance sono prioritarie sulla semplicità
- Grandi cluster con SAN enterprise

---

## Scenari di Migrazione da VMware

### Scenario 1: VMware NFS Datastore → Proxmox NFS

```bash
# La migrazione più semplice: stessi export NFS
# 1. Aggiungere lo stesso NFS server come storage Proxmox
pvesm add nfs nfs-vmware-migration \
    --server 10.10.10.254 \
    --export /export/vmware-vms \
    --content images

# 2. Convertire i VMDK presenti sull'NFS
cd /mnt/pve/nfs-vmware-migration
qemu-img convert -f vmdk -O qcow2 vm-disk.vmdk vm-disk.qcow2

# 3. Importare nella VM Proxmox
qm importdisk 100 /mnt/pve/nfs-vmware-migration/vm-disk.qcow2 nfs-images

# 4. Dopo la migrazione, rimuovere i VMDK originali
```

### Scenario 2: VMware VMFS su iSCSI → Proxmox LVM su iSCSI

```bash
# 1. Disconnettere le VM VMware dalla LUN
# 2. Rimuovere il datastore VMFS da vCenter
# 3. Ripresentare la LUN a Proxmox

# Sul target iSCSI, modificare le ACL:
targetcli
/iscsi/iqn.2026-03.com.lab:storage.target01/tpg1/acls delete iqn.vmware.esxi1
/iscsi/iqn.2026-03.com.lab:storage.target01/tpg1/acls create iqn.2026-03.com.lab:pve1
saveconfig
exit

# Sul nodo Proxmox:
iscsiadm -m discovery -t sendtargets -p 10.10.10.254:3260
iscsiadm -m node --login

# La LUN contiene ancora VMFS - riformattare per LVM
wipefs -a /dev/sdb    # Rimuovere firma VMFS
pvcreate /dev/sdb
vgcreate vg-migrated /dev/sdb
lvcreate -l 95%FREE -T vg-migrated/thin-pool

pvesm add lvmthin migrated-storage \
    --vgname vg-migrated \
    --thinpool thin-pool \
    --content images,rootdir \
    --shared 1

# Importare le VM precedentemente convertite
qm importdisk 100 /tmp/converted-vm-disk.raw migrated-storage
```

### Scenario 3: Migrazione Graduale (VMware e Proxmox coesistono)

```bash
# Usare una LUN dedicata alla migrazione, accessibile da entrambi
# tramite NFS (più semplice per la coesistenza)

# 1. Creare un NFS share dedicato alla migrazione
# Sul NFS server:
mkdir -p /export/migration
echo "/export/migration 10.10.10.0/24(rw,sync,no_subtree_check,no_root_squash)" >> /etc/exports
exportfs -arv

# 2. Montare su VMware (datastore NFS)
# vCenter → Add Storage → NFS Datastore

# 3. Montare su Proxmox
pvesm add nfs migration-share \
    --server 10.10.10.254 \
    --export /export/migration \
    --content images,iso,backup

# 4. Esportare VM da VMware come OVA/VMDK sull'NFS share
# 5. Convertire e importare su Proxmox
# 6. Validare e decommissionare le VM VMware
```

---

## Troubleshooting

### NFS Troubleshooting

```bash
# NFS mount fallisce
# Verificare connettività
ping 10.10.10.254
telnet 10.10.10.254 2049

# Verificare gli export dal client
showmount -e 10.10.10.254

# Verificare mount corrente
mount | grep nfs
cat /proc/mounts | grep nfs

# NFS stale file handle
# Smontare e rimontare
umount -f /mnt/pve/nfs-images
mount /mnt/pve/nfs-images

# Performance lente
nfsiostat 5
# Controllare: ops/s, rtt, exe (execution time)
# rtt alto → problema di rete
# exe alto → server NFS lento

# Debug NFS
rpcdebug -m nfs -s all    # Abilitare debug client
rpcdebug -m nfsd -s all   # Abilitare debug server
# I log vanno in dmesg/syslog
rpcdebug -m nfs -c all    # Disabilitare debug

# NFSv4 delegation issues
echo 0 > /proc/sys/fs/leases-enable  # Temporaneo, sul server
```

### iSCSI Troubleshooting

```bash
# Discovery fallisce
iscsiadm -m discovery -t sendtargets -p 10.10.10.254:3260 --debug 8 2>&1 | head -50

# Login fallisce
iscsiadm -m node -T iqn.2026-03.com.lab:storage.target01 -p 10.10.10.254:3260 --login
# Se errore CHAP: verificare username/password in /etc/iscsi/iscsid.conf

# Sessione disconnessa
iscsiadm -m session
# Se vuoto, rifare login:
iscsiadm -m node --loginall=automatic

# LUN non visibile dopo login
iscsiadm -m session --rescan
echo "- - -" > /sys/class/scsi_host/hostX/scan  # X = numero host

# Multipath: un path down
multipathd show paths
# Se un path è "faulty":
multipathd reconfigure

# iSCSI timeout durante I/O pesante
# Aumentare timeout in /etc/iscsi/iscsid.conf:
# node.session.timeo.replacement_timeout = 300
# node.conn[0].timeo.noop_out_interval = 10
# node.conn[0].timeo.noop_out_timeout = 15

# Riavviare iscsid senza perdere sessioni
systemctl restart iscsid    # Le sessioni persistono

# Rimuovere completamente un target
iscsiadm -m node -T iqn.2026-03.com.lab:storage.target01 --logout
iscsiadm -m node -T iqn.2026-03.com.lab:storage.target01 -o delete
iscsiadm -m discoverydb -t sendtargets -p 10.10.10.254:3260 -o delete
```

### Monitoring Condiviso NFS/iSCSI

```bash
# Monitorare latenza di rete storage
ping -c 100 -i 0.1 10.10.10.254 | tail -1
# rtt min/avg/max/mdev = 0.123/0.145/0.234/0.021 ms

# Monitorare bandwidth
iperf3 -s    # Sul storage server
iperf3 -c 10.10.10.254 -t 30 -P 4    # Sul client Proxmox

# Monitorare I/O dei dispositivi
iostat -xz 5
# Cercare: await (latency), %util (saturation)

# Monitoring con Prometheus
# NFS exporter: https://github.com/prometheus/node_exporter (include NFS metrics)
# iSCSI: monitorare via node_exporter + custom textfile collector
```

---

## Riferimenti

- [Proxmox VE Storage - NFS](https://pve.proxmox.com/wiki/Storage:_NFS)
- [Proxmox VE Storage - iSCSI](https://pve.proxmox.com/wiki/Storage:_iSCSI)
- [Linux NFS HOWTO](https://tldp.org/HOWTO/NFS-HOWTO/)
- [targetcli Documentation](https://github.com/open-iscsi/targetcli-fb)
- [Open-iSCSI Documentation](https://github.com/open-iscsi/open-iscsi)
- [Linux Multipath](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html/managing_storage_devices/configuring-device-mapper-multipath_managing-storage-devices)
- [TrueNAS iSCSI Guide](https://www.truenas.com/docs/core/sharing/iscsi/)

---

> **Prossimo:** [GlusterFS - Integrazione con Proxmox](glusterfs-integrazione-proxmox.md) - Storage distribuito alternativo a Ceph

---

## Approfondimenti — note del 2026-04-26

> **Approfondimento — `nconnect` su mount NFSv4.1+.** L'opzione di mount `nconnect=N` (kernel ≥ 5.3) apre N connessioni TCP parallele verso il server NFS, aumentando il throughput su link 10/25/40 GbE quando una singola connessione TCP non satura il link (limite tipico ~6-8 Gbps su una sola TCP stream). Tipico: `mount -t nfs4 -o vers=4.1,nconnect=4,proto=tcp server:/export /mnt/pve/nfs`. Per Proxmox la opzione si aggiunge in `/etc/pve/storage.cfg` come `options vers=4.1,nconnect=4`. Verifica throughput con `dd if=/dev/zero of=/mnt/pve/nfs/test.bin bs=1M count=10000 oflag=direct status=progress`.

> **Errore comune — MTU mismatch su rete iSCSI/NFS.** Sintomo: trasferimenti grandi (backup multi-GB, copy disk) che si bloccano a metà o presentano latenze erratiche, ping piccoli che funzionano, ping con `-M do -s 8972` che falliscono. Causa: una NIC, uno switch, una bridge interface ha MTU < 9000. Diagnosi rapida: `ip link show | grep mtu`, `ethtool eth0 | grep -i mtu`, `bridge link show`. Soluzione: allineare MTU end-to-end. Su Proxmox bridge: aggiungere `mtu 9000` nella stanza del bridge in `/etc/network/interfaces` e `ifreload -a`.

> **Caso reale — locking NFSv3 su cluster Proxmox + Veeam restore concorrenti.** Un cluster a 4 nodi Proxmox con storage NFSv3 condiviso. Veeam restore concorrenti producevano stale file handle e file locks orfani che richiedevano restart manuale di `rpc.statd`/`rpc.lockd`. Soluzione: passaggio a NFSv4.1, lease management nativo gestiva i lock anche con clients non graceful. Lezione: per cluster con scritture concorrenti su file shared (anche solo per lock files PID), preferire NFSv4.1+ a NFSv3, sempre.

---

## Esercizi

1. **Concettuale — perche LVM su LUN condivisa NON supporta snapshot?** Spiegare in 5-7 righe perche, anche se LVM-Thin supporta snapshot in locale, *LVM-on-shared-LUN* in Proxmox non li abilita. *Risposta:* su LUN condivisa l'attivazione concorrente di LV con thin pool richiederebbe coordinamento cluster sul lock del metadata; LVM2 non implementa cluster-aware metadata locking dal deprecato `clvm`. Per snapshot su shared, le scelte sono: (a) NFS con immagini qcow2 (snapshot interno), (b) Ceph RBD (snapshot RBD), (c) ZFS over iSCSI con plugin (storage `zfsoveriscsi` di Proxmox).

2. **Lab — NFS + nconnect.** Configurare un server NFSv4.1 (un nodo Linux, anche LXC) ed esportare `/export/proxmox-vms`. Su Proxmox aggiungere lo storage NFS via Web UI o `pvesm add nfs nas-vms --server 10.x.x.x --export /export/proxmox-vms --content images,iso,vztmpl`. Misurare throughput con e senza `nconnect=4` su un disco di test 10 GB. Documentare il delta.

3. **Scenario — iSCSI multipath con 2 NIC.** Hai 2 NIC dedicate sui nodi Proxmox e un target iSCSI che espone 2 portal (IP1 e IP2). Configurare `iscsiadm` per scoprire entrambi, `multipath-tools` con `path_grouping_policy multibus`, `path_selector "service-time 0"`. Verificare con `multipath -ll` che entrambi i path siano `active ready running`. Simulare il failure di una NIC (`ip link set ens6 down`) e verificare che l'I/O continui senza interruzioni. Documentare i tempi di failover (deve essere < 5 s con `polling_interval 5`).

4. **Stretch — NFS over Kerberos.** Configurare un realm Kerberos (MIT KDC o Active Directory) e abilitare `sec=krb5p` su un mount NFS. Verificare che senza ticket Kerberos valido, il mount sia respinto. *Riferimento:* RFC 7530 (NFSv4) §3, FreeIPA docs (per Kerberos integrato), Microsoft "NFS Server Kerberos Authentication" su Active Directory.

## Auto-valutazione

1. Differenza fra NFSv3 e NFSv4.1 su lease/lock management — perche conta per cluster Proxmox?
2. Cos'e un IQN e come si genera (formato standardizzato)?
3. Cosa fa `iscsiadm --mode discovery --type sendtargets --portal <ip>`?
4. Differenza fra `path_grouping_policy multibus` e `failover` in `multipath.conf`.
5. Quale `path_selector` distribuisce in modo proporzionale ai tempi di servizio dei path?
6. Cosa succede se il MTU di una NIC e 9000 ma il bridge ha MTU 1500 — frammentazione, drop, o silenzioso degrado?
7. Sintassi `pvesm add` per un mount NFS e per un target iSCSI?
8. Quando preferire CHAP `mutual` vs CHAP unidirezionale?

## Letture primarie consigliate

- [`PVE-STORAGE`] Proxmox VE Wiki — Storage: NFS e iSCSI. https://pve.proxmox.com/wiki/Storage
- RFC 7530 — NFSv4 (Network File System Version 4 Protocol). https://datatracker.ietf.org/doc/html/rfc7530
- RFC 8881 — NFSv4.1. https://datatracker.ietf.org/doc/html/rfc8881
- RFC 7143 — Internet Small Computer System Interface (iSCSI) Protocol. https://datatracker.ietf.org/doc/html/rfc7143
- Open-iSCSI documentation. https://github.com/open-iscsi/open-iscsi
- targetcli-fb (LIO/targetcli). https://github.com/open-iscsi/targetcli-fb
- Red Hat — Configuring device mapper multipath (RHEL 9). https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html/managing_storage_devices/configuring-device-mapper-multipath_managing-storage-devices
- TrueNAS iSCSI Guide. https://www.truenas.com/docs/core/sharing/iscsi/

## Collegamenti incrociati

- Modulo 03.1 — `lvm-e-lvm-thin-proxmox.md`: storage block locale; LVM-on-shared-LUN si lega a iSCSI come backend.
- Modulo 04.1 — `../04-NETWORKING-AVANZATO-PROXMOX/linux-bridge-vlan-bonding.md`: rete dedicata storage, MTU 9000, VLAN.
- Modulo 08.2 — `../08-MIGRAZIONE-STORAGE/shared-storage-cutover-nfs-iscsi.md`: cutover NFS/iSCSI in produzione.
- Modulo 10.3 — `../10-CLUSTER-HA-PROXMOX-POST-MIGRAZIONE/live-migration-proxmox-interna.md`: live migration richiede shared storage o `--with-local-disks`.
- Modulo 12.3 — `../12-SICUREZZA-E-COMPLIANCE/certificati-ssl-tls-proxmox.md`: certificati TLS, ipotesi per iSCSI over TLS / NFS over TLS.
- Modulo 17.4 — `../17-TROUBLESHOOTING-E-GUIDE-PRATICHE/troubleshooting-storage-performance.md`: troubleshooting performance NFS/iSCSI post-migrazione.

## Glossario locale

| Termine | Definizione |
|---|---|
| **NFS** | Network File System; protocollo file-level over TCP. Versioni: v3 (no lease), v4.0/4.1/4.2 (lease, sessions, byte-range locking, ACLs). |
| **`nfs-kernel-server`** | Pacchetto Debian/Ubuntu che fornisce il server NFS in kernel space (tipicamente piu performante di `unfs3` user-space). |
| **`/etc/exports`** | File di configurazione che lista directory esportate, client autorizzati e opzioni (`rw`, `no_root_squash`, `sync`/`async`, ...). |
| **`exportfs -ra`** | Ricarica le esportazioni dopo modifica di `/etc/exports`. |
| **`nconnect=N`** | Mount option NFS (kernel ≥ 5.3): apre N connessioni TCP parallele al server. |
| **iSCSI** | Internet SCSI: protocollo block-level che incapsula comandi SCSI su TCP/IP. Porta default 3260. |
| **IQN (iSCSI Qualified Name)** | Identificatore univoco di iniziatore/target. Formato: `iqn.YYYY-MM.<reverse-domain>:<descrittore>`. |
| **Initiator** | Lato client iSCSI (es. Proxmox). Pacchetti: `open-iscsi`. |
| **Target** | Lato server iSCSI. Implementazioni: LIO/targetcli (Linux), TrueNAS, Nimble, Pure, ecc. |
| **LUN (Logical Unit Number)** | Volume esposto da un target. Vista su Proxmox come `/dev/sd*` o `/dev/disk/by-id/scsi-...`. |
| **Portal** | Coppia IP:porta su cui un target accetta connessioni. Multi-portal = path multipli per multipath. |
| **CHAP** | Challenge-Handshake Authentication Protocol per iSCSI. Modalita unidirezionale o `mutual`. |
| **multipath-tools** | Suite Linux che aggrega path multipli verso lo stesso LUN in un device unico (`/dev/mapper/mpathN`). |
| **`path_grouping_policy`** | Policy multipath: `failover` (1 attivo, altri standby), `multibus` (tutti attivi). |
| **`path_selector`** | Algoritmo di scelta del path attivo: `round-robin 0`, `service-time 0`, `queue-length 0`. |
| **MTU 9000 (jumbo frames)** | Frame Ethernet di 9000 byte (vs 1500 standard). Riduce overhead, deve essere coerente end-to-end. |
| **`pvesm`** | Proxmox Storage Manager CLI: `pvesm add/status/list/...`. |
