# Cutover dello Shared Storage: NFS, iSCSI e Ceph

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 3 — Migrazione · Modulo 08.2 (vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 03.2 (NFS/iSCSI condiviso), modulo 08.1 (conversione VMDK), modulo 06.3 (live cutover concept), familiarita con Ceph (anche solo concettuale).
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. distinguere i 3 scenari di cutover dello shared storage (NFS, iSCSI, Ceph) e identificare i pre-requisiti specifici di ciascuno;
> 2. eseguire un cutover NFS preservando il path del datastore (Proxmox monta lo stesso export con stesso percorso) o cambiandolo (con migrazione dati intermedia);
> 3. gestire un cutover iSCSI che condivide la stessa LUN fra VMware (in maintenance) e Proxmox (in test), considerando i lock SCSI-3 PR e l'ordine di mount/unmount;
> 4. presentare Ceph come sostituto di vSAN — con metodologia di trasferimento dati (Ceph RBD import, image streaming, snapshot replication da array origine);
> 5. pianificare il cutover end-to-end con validazione HA sul nuovo storage, verificando snapshot, backup, e failover;
> 6. troubleshootare i problemi comuni (NFS stale handle, iSCSI MPIO confusion, Ceph PG stuck inactive, lock VMFS6 ereditati).
> **Tempo stimato:** lettura 60-90 min · lab 240-360 min
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-26
> **Versioni di riferimento:** NFSv3/v4.1, iSCSI software adapter (open-iscsi 2.1.x), Ceph Quincy (17.2)/Reef (18.2)/Squid (19.2).

## Mappa concettuale

```
+======================================================+
|  Shared storage cutover: 3 scenari                   |
+======================================================+
|                                                      |
|     [Scenario A: NFS preservato]                     |
|       NFS export resta uguale, Proxmox lo monta      |
|       in /mnt/pve/<storage-name> con stesso percorso |
|       VM trovano dischi qcow2 al boot                |
|                                                      |
|     [Scenario B: NFS migrazione path]                |
|       Cambio storage server (es. da NetApp a TrueNAS)|
|       Sequence: copy data (rsync), unmount Proxmox,  |
|       remount nuovo path, update storage.cfg         |
|                                                      |
|     [Scenario C: iSCSI shared LUN cross-hypervisor]  |
|       Stessa LUN visibile a VMware E a Proxmox       |
|       Rischio: SCSI-3 PR conflict, double-mount      |
|       Procedura: VMFS in maintenance, Proxmox import |
|       VMDK, poi unmount VMware definitivamente       |
|                                                      |
|     [Scenario D: Ceph al posto di vSAN]              |
|       Ceph cluster pre-creato (3+ nodi OSD)          |
|       Trasferimento dati: rbd import / qemu-img      |
|       convert direttamente verso RBD                 |
|       Snapshot post: rbd snap                        |
|                                                      |
|     PRE-CUTOVER                                      |
|       +-- backup full PRE                            |
|       +-- pause su workload non-essenziale           |
|       +-- maintenance mode su origine                |
|         |                                            |
|         v                                            |
|     CUTOVER                                          |
|       +-- mount su Proxmox                           |
|       +-- import disks (qm importdisk)               |
|       +-- VM start                                   |
|       +-- validation                                 |
|         |                                            |
|         v                                            |
|     POST-CUTOVER                                     |
|       +-- HA test (failover su nodo)                 |
|       +-- backup ricreato post-migration             |
|       +-- snapshot test                              |
|       +-- monitoring metrics                         |
|                                                      |
+======================================================+
```

Idee guida del modulo:

1. **NFS cutover e il piu semplice. Prediligilo se possibile.** Stesso server NFS, stesso export, Proxmox monta dove montava VMware. Il cutover si riduce a: stop VM su VMware, unmount NFS su VMware, mount NFS su Proxmox, import VMDK come qcow2, start VM. Tempo: 5-30 min per VM, dipende da dimensione disco.
2. **iSCSI cross-hypervisor richiede coordinamento SCSI lock.** VMFS6 ha SCSI-3 PR (Persistent Reservation) e lock ATS che persistono finche il filesystem e montato. Se Proxmox prende la LUN mentre VMware la tiene ancora, possibile data corruption. Procedura sicura: VMware unmounta prima (`esxcli storage core device set --state=off`), poi Proxmox monta. Mai contemporaneamente.
3. **Ceph e una scelta architetturale, non solo storage.** Migrare a Ceph significa adottare: CRUSH map design, fault domain (host/rack/dc), replication factor (3 minimo), MON/OSD ratio, CPU/RAM budget per OSD (4-6 GB RAM per OSD all-flash). Non si "migra a Ceph" senza piano architetturale completo (modulo 03.x, capacity planning 05.3).
4. **`rbd import` per Ceph.** Il modo "bash-friendly" di portare un VMDK su Ceph: `qemu-img convert -p -O rbd disk.vmdk rbd:rbd/vm-100-disk-0`. Scrive direttamente sul pool Ceph. Alternativa: `qemu-img convert -O raw disk.vmdk - | rbd import - rbd/vm-100-disk-0`. Performance: limitata dalla CPU del client.
5. **HA test e step finale obbligatorio.** Dopo il cutover, *prima* di considerarlo concluso, simulare il fault: spegnere brutalmente un nodo Proxmox e verificare che (a) le VM HA-protette si riavviino su altro nodo entro RTO; (b) lo storage shared non perda dati (NFS lease torna entro 60 s, iSCSI session timeout configurato correttamente); (c) il fencing si attiva e isola il nodo "fuori" dal cluster.

## Indice
- [Panoramica](#panoramica)
- [NFS Shared Storage: da VMware a Proxmox](#nfs-shared-storage-da-vmware-a-proxmox)
- [iSCSI Shared Storage](#iscsi-shared-storage)
- [Ceph come Sostituto di vSAN](#ceph-come-sostituto-di-vsan)
- [Pianificazione del Cutover](#pianificazione-del-cutover)
- [Validazione HA sul Nuovo Storage](#validazione-ha-sul-nuovo-storage)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

In un ambiente virtualizzato enterprise, lo shared storage è il fondamento su cui poggiano funzionalità critiche come la live migration, l'high availability e il bilanciamento automatico dei carichi. In VMware, queste funzionalità sono garantite da datastore condivisi — VMFS su SAN FC/iSCSI, NFS export montati da tutti gli host ESXi, o vSAN come soluzione hyper-converged. La migrazione a Proxmox VE richiede la riconfigurazione dello shared storage per mantenere queste capacità operative senza interruzione.

Questo documento copre in dettaglio le tre principali architetture di shared storage utilizzabili con Proxmox: NFS per la sua semplicità e compatibilità con infrastrutture esistenti, iSCSI per ambienti che richiedono performance a livello di blocchi con SAN tradizionali, e Ceph per chi necessita di una soluzione distribuita e fault-tolerant che sostituisca funzionalmente VMware vSAN. Per ciascuna tecnologia vengono analizzate la configurazione, le ottimizzazioni di performance, e le procedure operative di cutover.

Il cutover dello shared storage è il momento più delicato dell'intera migrazione: un errore può causare downtime su tutte le VM che dipendono da quel storage. La pianificazione del cutover, la validazione dell'high availability, e le procedure di rollback sono quindi trattate con particolare attenzione, includendo scenari di test e checklist operative.

---

## NFS Shared Storage: da VMware a Proxmox

### Architettura NFS in VMware

VMware ESXi monta NFS export come datastore. Ogni host nel cluster monta lo stesso export, permettendo vMotion e HA:

```
NFS Server (NetApp / TrueNAS / Linux)
  Export: /vol/vmware-prod
    ├── VM-Web/
    │   ├── VM-Web.vmdk
    │   └── VM-Web-flat.vmdk
    └── VM-DB/
        ├── VM-DB.vmdk
        └── VM-DB-flat.vmdk

     ┌──────────┐  ┌──────────┐  ┌──────────┐
     │  ESXi 1  │  │  ESXi 2  │  │  ESXi 3  │
     │ NFS mount│  │ NFS mount│  │ NFS mount│
     └──────────┘  └──────────┘  └──────────┘
           ↑              ↑              ↑
           └──────── NFS v3/v4.1 ────────┘
```

### Configurazione NFS Server per Proxmox

#### /etc/exports — Configurazione Base

Il server NFS deve esportare una directory accessibile da tutti i nodi Proxmox:

```bash
# /etc/exports sul server NFS Linux
# Sintassi: directory  client(opzioni)

# Export per Proxmox cluster (subnet 10.0.1.0/24)
/vol/proxmox-data  10.0.1.0/24(rw,sync,no_subtree_check,no_root_squash)

# Export con singoli host specificati
/vol/proxmox-data  pve-node1(rw,sync,no_subtree_check,no_root_squash) \
                   pve-node2(rw,sync,no_subtree_check,no_root_squash) \
                   pve-node3(rw,sync,no_subtree_check,no_root_squash)
```

Analisi delle opzioni critiche:

| Opzione | Significato | Obbligatorio |
|---|---|---|
| `rw` | Lettura e scrittura | Sì |
| `sync` | Scritture sincrone (dati su disco prima di ACK) | Sì per integrità |
| `no_subtree_check` | Disabilita subtree check, migliora performance | Raccomandato |
| `no_root_squash` | Root sul client mantiene privilegi root | Sì per Proxmox |
| `crossmnt` | Permette accesso a filesystem montati sotto l'export | Se necessario |

```bash
# Applicare la configurazione
exportfs -ra

# Verificare gli export attivi
exportfs -v
# /vol/proxmox-data  10.0.1.0/24(rw,wdelay,no_root_squash,no_subtree_check,sync,...)

# Verificare le connessioni NFS attive
ss -tnlp | grep -E '2049|111'
```

#### NFS v3 vs NFS v4 / v4.1

| Caratteristica | NFS v3 | NFS v4.0 | NFS v4.1 |
|---|---|---|---|
| Porte | 2049 + portmapper + mountd | Solo 2049 | Solo 2049 |
| Autenticazione | AUTH_SYS (UID/GID) | Kerberos opz. | Kerberos opz. |
| Locking | NLM separato (statd, lockd) | Integrato | Integrato |
| Firewall | Complesso (porte multiple) | Semplice (2049) | Semplice (2049) |
| Performance | Ottima (maturo) | Buona | Buona + pNFS |
| VMware support | Completo | Non supportato | Supportato (6.0+) |
| Proxmox support | Completo | Completo | Completo |

**Raccomandazione**: per la migrazione, se l'infrastruttura esistente usa NFS v3 con VMware, mantenere NFS v3 inizialmente anche per Proxmox per ridurre le variabili. Passare a NFS v4.1 in una fase successiva di ottimizzazione.

```bash
# Forzare NFS v3 su Proxmox
pvesm add nfs nfs-shared --server 10.0.1.50 \
    --export /vol/proxmox-data --content images,iso,backup \
    --options vers=3

# Oppure NFS v4.1
pvesm add nfs nfs-shared --server 10.0.1.50 \
    --export /vol/proxmox-data --content images,iso,backup \
    --options vers=4.1
```

#### Performance Tuning: rsize e wsize

I parametri `rsize` (read size) e `wsize` (write size) definiscono la dimensione massima dei blocchi di dati trasferiti in una singola operazione NFS:

```bash
# Valori di default: 1048576 (1 MB) su kernel moderni
# Verificare i valori correnti
nfsstat -m
# /mnt/nfs-shared from 10.0.1.50:/vol/proxmox-data
#  Flags: rw,relatime,vers=3,rsize=1048576,wsize=1048576,namlen=255,...

# Mount manuale con parametri personalizzati
mount -t nfs -o rw,vers=3,rsize=1048576,wsize=1048576,hard,intr,tcp \
    10.0.1.50:/vol/proxmox-data /mnt/nfs-shared

# Per Proxmox, configurare via /etc/pve/storage.cfg
# oppure direttamente in /etc/fstab per mount personalizzato
```

Ottimizzazione lato server NFS (Linux):

```bash
# Aumentare il numero di thread NFS server
# /etc/default/nfs-kernel-server (Debian/Ubuntu)
RPCNFSDCOUNT=32   # Default spesso 8, aumentare per carichi elevati

# /etc/nfs.conf (sistemi più recenti)
[nfsd]
threads=32

# Ottimizzare il buffer di rete
sysctl -w net.core.rmem_max=16777216
sysctl -w net.core.wmem_max=16777216

# Rendere persistente
cat >> /etc/sysctl.d/99-nfs-tuning.conf << 'EOF'
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.core.rmem_default = 1048576
net.core.wmem_default = 1048576
EOF

# Riavviare NFS server
systemctl restart nfs-kernel-server
```

### Strategia di Cutover NFS

La strategia più efficiente per NFS è il "dual-mount": durante la transizione, sia VMware che Proxmox montano lo stesso export NFS.

```
Fase 1: Dual Mount
  NFS Server: /vol/vmware-prod
    ├── Montato da ESXi (rw, datastore VMware)
    └── Montato da Proxmox (ro, per conversione)

Fase 2: Conversione VM
  Per ogni VM su NFS:
    1. Spegnere su VMware
    2. Convertire VMDK → qcow2/raw direttamente dal mount NFS
    3. Importare in Proxmox
    4. Avviare su Proxmox

Fase 3: Cutover
  1. Smontare l'export da tutti gli ESXi
  2. Riorganizzare l'export per Proxmox (nuovo export o rinominare)
  3. Configurare come storage Proxmox rw
```

```bash
# Fase 1: mount read-only da Proxmox per accedere ai VMDK
mount -t nfs -o ro,vers=3 10.0.1.50:/vol/vmware-prod /mnt/vmware-nfs

# Fase 2: conversione diretta (nessuna copia intermedia)
qemu-img convert -p -W -m 8 -f vmdk -O qcow2 \
    /mnt/vmware-nfs/VM-Web/VM-Web.vmdk \
    /var/lib/vz/images/100/vm-100-disk-0.qcow2

# Se la destinazione è anche NFS (nuovo export per Proxmox)
qemu-img convert -p -W -m 8 -f vmdk -O qcow2 \
    /mnt/vmware-nfs/VM-Web/VM-Web.vmdk \
    /mnt/proxmox-nfs/images/100/vm-100-disk-0.qcow2
```

### Creazione di un Nuovo Export Dedicato a Proxmox

È raccomandato creare un export NFS separato per Proxmox piuttosto che riutilizzare quello VMware, per evitare conflitti di struttura directory:

```bash
# Sul server NFS
mkdir -p /vol/proxmox-data/{images,iso,backup,template}
chown -R root:root /vol/proxmox-data

# Aggiungere l'export
echo '/vol/proxmox-data 10.0.1.0/24(rw,sync,no_subtree_check,no_root_squash)' \
    >> /etc/exports
exportfs -ra

# Su Proxmox
pvesm add nfs nfs-proxmox --server 10.0.1.50 \
    --export /vol/proxmox-data --content images,iso,vztmpl,backup
```

---

## iSCSI Shared Storage

### Architettura iSCSI per Proxmox

iSCSI trasporta comandi SCSI su TCP/IP, permettendo l'accesso a dispositivi a blocchi remoti. In Proxmox, un target iSCSI viene utilizzato come base per LVM o LVM-thin:

```
iSCSI Target (TrueNAS / targetcli / SAN)
  LUN 0: 500GB (per VM disks)
  LUN 1: 200GB (per backup)

     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
     │  Proxmox 1   │  │  Proxmox 2   │  │  Proxmox 3   │
     │  iscsiadm     │  │  iscsiadm     │  │  iscsiadm     │
     │  LVM/LVM-thin │  │  LVM/LVM-thin │  │  LVM/LVM-thin │
     └──────────────┘  └──────────────┘  └──────────────┘
           ↑                  ↑                  ↑
           └─────── iSCSI (10/25 GbE) ──────────┘
```

### Configurazione Target con targetcli (Linux)

```bash
# Installare targetcli
apt install targetcli-fb    # Debian/Ubuntu
dnf install targetcli       # RHEL/Rocky

# Avviare targetcli
targetcli

# Creare un backing store (file-based o block device)
/> /backstores/block create pve-lun0 /dev/sdb
# Oppure file-based:
/> /backstores/fileio create pve-lun0 /var/iscsi/pve-lun0.img 500G

# Creare il target iSCSI
/> /iscsi create iqn.2024-01.com.lab:proxmox-storage

# Creare il LUN nel target
/> /iscsi/iqn.2024-01.com.lab:proxmox-storage/tpg1/luns create /backstores/block/pve-lun0

# Configurare l'ACL (per ogni initiator Proxmox)
/> /iscsi/iqn.2024-01.com.lab:proxmox-storage/tpg1/acls create iqn.2024-01.com.proxmox:pve-node1
/> /iscsi/iqn.2024-01.com.lab:proxmox-storage/tpg1/acls create iqn.2024-01.com.proxmox:pve-node2
/> /iscsi/iqn.2024-01.com.lab:proxmox-storage/tpg1/acls create iqn.2024-01.com.proxmox:pve-node3

# Configurare l'autenticazione CHAP (opzionale ma raccomandato)
/> /iscsi/iqn.2024-01.com.lab:proxmox-storage/tpg1/acls/iqn.2024-01.com.proxmox:pve-node1 set auth userid=proxmox1 password=SecretPass123

# Impostare il portal (indirizzo di ascolto)
/> /iscsi/iqn.2024-01.com.lab:proxmox-storage/tpg1/portals create 10.0.1.50

# Salvare e uscire
/> saveconfig
/> exit

# Abilitare il servizio
systemctl enable --now target
```

### Configurazione Target con TrueNAS

Su TrueNAS (Core o SCALE), la configurazione iSCSI è tramite web UI:

1. **Sharing → Block (iSCSI) → Portals**: creare un portal con IP e porta 3260
2. **Sharing → Block (iSCSI) → Targets**: creare il target con IQN
3. **Sharing → Block (iSCSI) → Extents**: creare un extent (zvol o file)
4. **Sharing → Block (iSCSI) → Associated Targets**: collegare extent al target
5. **Sharing → Block (iSCSI) → Initiators**: configurare gli initiator autorizzati

```
TrueNAS iSCSI Configuration:
  Portal: 10.0.1.50:3260
  Target: iqn.2024-01.com.truenas:proxmox-pool
  Extent: tank/iscsi/pve-lun0 (500G zvol)
  Auth: CHAP (proxmox-user / S3cureP@ss)
```

### Configurazione Initiator su Proxmox (iscsiadm)

```bash
# Installare open-iscsi (generalmente pre-installato su Proxmox)
apt install open-iscsi

# Configurare l'initiator name (deve corrispondere all'ACL sul target)
echo "InitiatorName=iqn.2024-01.com.proxmox:pve-node1" > /etc/iscsi/initiatorname.iscsi

# Configurare CHAP (se utilizzato)
# /etc/iscsi/iscsid.conf
node.session.auth.authmethod = CHAP
node.session.auth.username = proxmox1
node.session.auth.password = SecretPass123

# Configurare parametri di connessione
node.conn[0].timeo.noop_out_interval = 5
node.conn[0].timeo.noop_out_timeout = 5
node.session.timeo.replacement_timeout = 120

# Riavviare iscsid
systemctl restart iscsid

# Discover dei target
iscsiadm -m discovery -t sendtargets -p 10.0.1.50:3260
# 10.0.1.50:3260,1 iqn.2024-01.com.lab:proxmox-storage

# Login al target
iscsiadm -m node -T iqn.2024-01.com.lab:proxmox-storage -p 10.0.1.50:3260 --login

# Verificare la connessione
iscsiadm -m session -P 3
# Target: iqn.2024-01.com.lab:proxmox-storage (non-flash)
#   Current Portal: 10.0.1.50:3260,1
#   Attached scsi disk sdc  State: running

# Configurare login automatico al boot
iscsiadm -m node -T iqn.2024-01.com.lab:proxmox-storage -p 10.0.1.50 \
    --op update -n node.startup -v automatic
```

### LVM su iSCSI

Una volta che il dispositivo iSCSI è visibile come disco locale (`/dev/sdc`), creare LVM-thin sopra di esso:

```bash
# Creare PV, VG e thin pool
pvcreate /dev/sdc
vgcreate vg-iscsi /dev/sdc
lvcreate -l 95%FREE --thinpool thinpool vg-iscsi

# Registrare in Proxmox come storage
pvesm add lvmthin iscsi-thin --vgname vg-iscsi --thinpool thinpool \
    --content images,rootdir --shared 1

# IMPORTANTE: --shared 1 è necessario per shared storage (HA, live migration)
# Tutti i nodi del cluster devono avere lo stesso setup iSCSI + LVM
```

### Multipathing (DM-Multipath)

Per alta disponibilità e performance con iSCSI, configurare multipathing con percorsi ridondanti:

```
                    ┌─────────┐
                    │ iSCSI   │
                    │ Target  │
                    │ NIC1:   │──── Rete Storage A (10.0.1.0/24)
                    │ 10.0.1.50│
                    │ NIC2:   │──── Rete Storage B (10.0.2.0/24)
                    │ 10.0.2.50│
                    └─────────┘
                         ↕
  Proxmox Node:
    NIC1 (10.0.1.10) ──── Rete Storage A ──── Path 1
    NIC2 (10.0.2.10) ──── Rete Storage B ──── Path 2
                         ↓
                    dm-multipath
                    /dev/mapper/mpath0
                         ↓
                    LVM / LVM-thin
```

```bash
# Installare multipath-tools
apt install multipath-tools

# Configurare /etc/multipath.conf
cat > /etc/multipath.conf << 'EOF'
defaults {
    polling_interval    2
    path_selector       "round-robin 0"
    path_grouping_policy    multibus
    failback            immediate
    no_path_retry       5
    user_friendly_names yes
}

blacklist {
    devnode "^(ram|raw|loop|fd|md|dm-|sr|scd|st)[0-9]*"
    devnode "^sd[a-b]"   # Escludere dischi OS locali
}

multipaths {
    multipath {
        wwid    3600508b400105e210000600001490000
        alias   iscsi-pve-lun0
    }
}
EOF

# Scoprire entrambi i path
iscsiadm -m discovery -t sendtargets -p 10.0.1.50:3260
iscsiadm -m discovery -t sendtargets -p 10.0.2.50:3260

# Login su entrambi i path
iscsiadm -m node -T iqn.2024-01.com.lab:proxmox-storage -p 10.0.1.50 --login
iscsiadm -m node -T iqn.2024-01.com.lab:proxmox-storage -p 10.0.2.50 --login

# Avviare multipath
systemctl enable --now multipathd
multipath -ll
# iscsi-pve-lun0 (3600508b400105e210000600001490000) dm-2 LIO-ORG,pve-lun0
# size=500G features='1 queue_if_no_path' hwhandler='1 alua' wp=rw
# `-+- policy='round-robin 0' prio=50 status=active
#   |- 3:0:0:0 sdc 8:32 active ready running
#   `- 4:0:0:0 sdd 8:48 active ready running

# Usare il device multipath per LVM
pvcreate /dev/mapper/iscsi-pve-lun0
vgcreate vg-iscsi /dev/mapper/iscsi-pve-lun0
lvcreate -l 95%FREE --thinpool thinpool vg-iscsi
```

---

## Ceph come Sostituto di vSAN

### Confronto Architetturale vSAN vs Ceph

```
VMware vSAN:                          Ceph:
+--------+--------+--------+         +--------+--------+--------+
| ESXi 1 | ESXi 2 | ESXi 3 |         | PVE 1  | PVE 2  | PVE 3  |
| vSAN   | vSAN   | vSAN   |         | OSD+MON| OSD+MON| OSD+MON|
| Agent  | Agent  | Agent  |         |        |        |        |
+--------+--------+--------+         +--------+--------+--------+
    ↕         ↕         ↕                 ↕         ↕         ↕
  vSAN Network (10/25 GbE)            Ceph Cluster Network (10/25 GbE)
       vSAN Datastore                    Ceph RADOS Pool (RBD)
```

| Aspetto | vSAN | Ceph |
|---|---|---|
| Licenza | Proprietaria (inclusa in vSphere+) | Open source |
| Nodi minimi | 2 (con witness) / 3 | 3 (per pool replicated x3) |
| Rete | 10 GbE dedicata | 10 GbE dedicata (25 GbE raccomandato) |
| Fault tolerance | Policy-based (FTT) | Pool-level (size, min_size) |
| Scaling | Aggiungi host | Aggiungi OSD |
| Tiering | Disk groups (SSD cache + HDD) | Device class + CRUSH rules |
| Integrazione Proxmox | N/A | Nativa (pveceph) |

### Installazione Ceph su Proxmox (pveceph)

```bash
# Su OGNI nodo Proxmox del cluster (eseguire su ciascuno)
pveceph install --repository no-subscription

# Inizializzare Ceph (solo sul primo nodo)
pveceph init --network 10.0.2.0/24 --cluster-network 10.0.3.0/24
# --network: rete pubblica (client → OSD)
# --cluster-network: rete di replica (OSD → OSD)

# Creare i MON (monitor) — almeno 3 per quorum
pveceph mon create          # Sul nodo corrente
# Ripetere sugli altri 2 nodi

# Creare i MGR (manager) — almeno 2 per HA
pveceph mgr create          # Sul nodo corrente

# Creare gli OSD — per ogni disco dati
pveceph osd create /dev/sdb   # Nodo 1
pveceph osd create /dev/sdc   # Nodo 1
# Ripetere per ogni disco su ogni nodo
```

### Creazione Pool e Configurazione PG

Il numero di Placement Groups (PG) è critico per le performance e la distribuzione dei dati:

```bash
# Formula: PG totali = (OSD_count * 100) / replica_size
# Arrotondare alla potenza di 2 più vicina

# Esempio: 9 OSD, replica 3
# PG = (9 * 100) / 3 = 300 → arrotondare a 256

# Creare il pool per le VM
ceph osd pool create vm-pool 256
ceph osd pool set vm-pool size 3        # 3 repliche
ceph osd pool set vm-pool min_size 2    # Minimo 2 repliche per I/O
ceph osd pool application enable vm-pool rbd

# Registrare in Proxmox
pvesm add rbd ceph-vm --pool vm-pool --content images,rootdir

# Verificare
ceph status
# cluster:
#   id:     a1b2c3d4-...
#   health: HEALTH_OK
# osd: 9 osds: 9 up, 9 in
# pools: 1 pools, 256 pgs
```

### Importazione VM da VMware a Ceph RBD

```bash
# Metodo 1: conversione con qemu-img verso RBD
# (richiede che il nodo Proxmox abbia accesso a Ceph)
qemu-img convert -p -W -f vmdk -O raw \
    /tmp/VM-Web.vmdk rbd:vm-pool/vm-100-disk-0

# Metodo 2: conversione a raw temporaneo, poi importazione
qemu-img convert -p -W -f vmdk -O raw /tmp/VM-Web.vmdk /tmp/vm-web.raw
rbd import /tmp/vm-web.raw vm-pool/vm-100-disk-0

# Metodo 3: via qm importdisk
qm importdisk 100 /tmp/VM-Web.vmdk ceph-vm --format raw

# Verificare l'immagine RBD
rbd info vm-pool/vm-100-disk-0
# rbd image 'vm-100-disk-0':
#   size 100 GiB in 25600 objects
#   order 22 (4 MiB objects)
#   snapshot_count: 0
#   id: 1a2b3c
#   block_name_prefix: rbd_data.1a2b3c
#   format: 2
#   features: layering, exclusive-lock, object-map, fast-diff, deep-flatten
```

### Ottimizzazione Ceph Post-Installazione

```bash
# Abilitare autoscale dei PG (Ceph Nautilus+)
ceph osd pool set vm-pool pg_autoscale_mode on

# Configurare tiering se si hanno SSD + HDD
# Creare una CRUSH rule per device class
ceph osd crush rule create-replicated ssd-rule default host ssd
ceph osd pool set vm-pool crush_rule ssd-rule

# Abilitare compressione BlueStore (opzionale)
ceph osd pool set vm-pool compression_algorithm snappy
ceph osd pool set vm-pool compression_mode aggressive

# Tuning OSD
ceph config set osd bluestore_cache_size 4294967296  # 4 GB cache per OSD
ceph config set osd osd_memory_target 4294967296      # 4 GB memory target
```

---

## Pianificazione del Cutover

### Timeline di Cutover Tipica

```
T-7 giorni:  Preparazione
  - Validare configurazione storage Proxmox
  - Test di migrazione su VM non-critica
  - Verificare backup di tutte le VM

T-3 giorni:  Pre-sync
  - Iniziare rsync/copia dei VMDK più grandi
  - Primo delta sync

T-1 giorno:  Preparazione finale
  - Delta sync finale delle VM grandi
  - Comunicazione agli stakeholder
  - Preparare procedure di rollback

T-0 (Cutover Window):
  00:00  Inizio finestra di manutenzione
  00:10  Spegnimento VM batch 1 su VMware
  00:15  Sync finale dischi batch 1
  00:45  Conversione e importazione batch 1
  01:00  Avvio VM batch 1 su Proxmox
  01:15  Validazione batch 1
  01:30  Spegnimento VM batch 2 su VMware
  ...    (ripetere per ogni batch)
  04:00  Tutti i batch completati
  04:30  Validazione globale
  05:00  Fine finestra di manutenzione (o rollback se problemi)

T+1 giorno:  Monitoraggio intensivo
T+7 giorni:  Decommissioning VMware (se tutto ok)
T+30 giorni: Cancellazione VMDK originali
```

### Procedura di Rollback

Il rollback deve essere pianificato prima del cutover:

```bash
# Scenario rollback: VM non funziona su Proxmox
# 1. Spegnere su Proxmox
qm stop 100

# 2. Riaccendere su VMware (i VMDK originali sono intatti)
ssh root@esxi "vim-cmd vmsvc/power.on <vmid>"

# 3. Verificare operatività
# 4. Investigare la causa del fallimento
# 5. Ripianificare la migrazione
```

### Checklist Pre-Cutover

- [ ] Storage Proxmox configurato e testato su tutti i nodi
- [ ] Live migration testata tra tutti i nodi Proxmox sullo shared storage
- [ ] Backup completo di tutte le VM da migrare
- [ ] VMDK pre-sincronizzati per VM di grandi dimensioni
- [ ] Procedure di rollback documentate e testate
- [ ] Contatti di emergenza e escalation definiti
- [ ] Finestra di manutenzione comunicata e approvata
- [ ] DNS TTL ridotto a 5 minuti (se cambiano gli IP)
- [ ] Monitoraggio storage attivo su Proxmox

---

## Validazione HA sul Nuovo Storage

### Test di Live Migration

```bash
# Verificare che la live migration funzioni sullo shared storage
qm migrate 100 pve-node2 --online

# Monitorare il progresso
qm status 100
# status: running
# Ha: ...
# node: pve-node2  (verificare che sia cambiato)

# Migrare indietro
qm migrate 100 pve-node1 --online
```

### Test di HA (Simulazione Failover)

```bash
# Configurare HA per la VM
ha-manager add vm:100 --state started --group ha-group1

# Verificare lo stato HA
ha-manager status
# vm:100 started pve-node1

# Simulare un failover: riavviare il nodo che ospita la VM
# ATTENZIONE: questo è distruttivo, eseguire solo in ambiente di test
ssh pve-node1 "reboot"

# Dopo 30-60 secondi, verificare che la VM sia stata riavviata su un altro nodo
ha-manager status
# vm:100 started pve-node2  (migrata automaticamente)
```

### Test di Storage Failure (Ceph)

```bash
# Simulare la perdita di un OSD
ceph osd out 3
# Verificare che Ceph esegua il recovery
ceph -w
# health: HEALTH_WARN 1 osds down
# ...
# recovery: 15% complete

# Ripristinare l'OSD
ceph osd in 3
```

### Validazione Performance Post-Cutover

```bash
# Benchmark I/O dalla VM migrata
fio --name=validate --ioengine=libaio --rw=randrw --rwmixread=70 \
    --bs=4k --numjobs=4 --size=1G --runtime=60 --direct=1 \
    --group_reporting --filename=/tmp/fio-test

# Confrontare con il baseline VMware documentato prima della migrazione
```

---

## Best Practices

- Creare un export NFS dedicato per Proxmox piuttosto che riutilizzare l'export VMware; questo evita conflitti di struttura directory e permette di ottimizzare i permessi.
- Per NFS, utilizzare `sync` e `no_root_squash` negli export; `sync` garantisce l'integrità dei dati, `no_root_squash` è necessario per le operazioni di Proxmox.
- Configurare multipathing per tutti gli accessi iSCSI in produzione; un singolo path rappresenta un single point of failure inaccettabile.
- Per Ceph, utilizzare una rete cluster dedicata separata dalla rete pubblica; il traffico di replica tra OSD può saturare la rete se condivisa con il traffico client.
- Dimensionare correttamente i Placement Groups di Ceph con la formula `(OSD * 100) / size` arrotondato alla potenza di 2 più vicina; un numero errato di PG causa squilibrio nella distribuzione dei dati.
- Testare la live migration su ogni tipo di shared storage prima del cutover in produzione; un fallimento di live migration durante il cutover è critico.
- Pianificare il cutover con batch ordinati per criticità crescente e includere sempre un piano di rollback testato per ogni batch.
- Monitorare proattivamente lo stato dello storage durante e dopo il cutover: thin pool usage per LVM-thin, Ceph health status, latenza NFS/iSCSI.
- Per iSCSI, configurare i timeout di sessione appropriatamente; valori troppo brevi causano disconnessioni spurie, troppo lunghi ritardano il failover.
- Mantenere i VMDK originali su VMware per almeno 30 giorni dopo il cutover come ultima possibilità di rollback.
- Validare l'HA con un test di failover reale (reboot di un nodo) prima di dichiarare la migrazione completata.
- Documentare tutti i parametri di configurazione storage (export NFS, IQN iSCSI, pool Ceph) in un registro centralizzato accessibile a tutto il team.

---

## Troubleshooting

### Problema: NFS mount fallisce con "access denied by server"
**Sintomi**: il comando `mount -t nfs` da Proxmox restituisce "access denied by server while mounting".
**Causa**: il server NFS non autorizza il client Proxmox. Le cause specifiche possono essere: (1) l'IP del nodo Proxmox non è nell'elenco dei client autorizzati in `/etc/exports`; (2) `root_squash` è attivo e Proxmox tenta operazioni come root; (3) la rete tra client e server non è raggiungibile sulla porta NFS.
**Soluzione**:
```bash
# Sul server NFS, verificare gli export
exportfs -v
# Verificare che l'IP del client Proxmox sia incluso
# Aggiornare /etc/exports se necessario e ricaricare
exportfs -ra

# Verificare connettività
telnet nfs-server 2049
# Per NFS v3, verificare anche portmapper
rpcinfo -p nfs-server

# Verificare firewall
iptables -L -n | grep 2049
```
**Prevenzione**: testare il mount NFS da ogni nodo Proxmox del cluster prima del cutover. Usare subnet notation (`10.0.1.0/24`) invece di hostname singoli per semplificare la gestione.

### Problema: sessioni iSCSI si disconnettono periodicamente
**Sintomi**: le VM su storage iSCSI subiscono freeze temporanei o I/O error. I log mostrano "iSCSI connection lost" seguito da reconnect.
**Causa**: i timeout di sessione iSCSI sono troppo aggressivi per la latenza della rete, oppure un componente di rete (switch, NIC) ha problemi intermittenti. Anche la MTU mismatch tra initiator e target può causare frammentazione e perdita di pacchetti.
**Soluzione**:
```bash
# Verificare i log
journalctl -u iscsid --since "1 hour ago" | grep -i error

# Aumentare i timeout
iscsiadm -m node -T <target-iqn> -p <portal> --op update \
    -n node.conn[0].timeo.noop_out_interval -v 10
iscsiadm -m node -T <target-iqn> -p <portal> --op update \
    -n node.conn[0].timeo.noop_out_timeout -v 15
iscsiadm -m node -T <target-iqn> -p <portal> --op update \
    -n node.session.timeo.replacement_timeout -v 180

# Verificare MTU consistency
ip link show | grep mtu
# Deve essere identico su initiator, target, e tutti gli switch intermedi
```
**Prevenzione**: configurare multipathing con almeno 2 percorsi indipendenti. Utilizzare jumbo frames (MTU 9000) end-to-end verificando ogni hop.

### Problema: Ceph HEALTH_WARN con "too few PGs per OSD"
**Sintomi**: `ceph status` mostra `HEALTH_WARN: too few PGs per OSD (X < min Y)`.
**Causa**: il numero di Placement Groups nel pool è insufficiente per il numero di OSD. Questo causa una distribuzione non uniforme dei dati e potenziali hotspot di I/O.
**Soluzione**:
```bash
# Verificare il conteggio PG attuale
ceph osd pool get vm-pool pg_num
# Calcolare il valore corretto: (OSD * 100) / size
# Aumentare (mai diminuire drasticamente)
ceph osd pool set vm-pool pg_num 256
ceph osd pool set vm-pool pgp_num 256

# Oppure abilitare autoscaling
ceph osd pool set vm-pool pg_autoscale_mode on
ceph osd pool autoscale-status
```
**Prevenzione**: calcolare i PG correttamente prima della creazione del pool. Abilitare `pg_autoscale_mode on` per gestione automatica.

### Problema: live migration fallisce con "storage not shared"
**Sintomi**: il tentativo di live migration con `qm migrate --online` fallisce con errore "can't migrate - storage 'X' is not shared".
**Causa**: lo storage backend non è configurato come shared nella configurazione di Proxmox. Anche se fisicamente è uno storage condiviso (NFS, iSCSI, Ceph), Proxmox deve saperlo esplicitamente.
**Soluzione**:
```bash
# Verificare la configurazione storage
pvesm status
# Controllare la colonna "Shared"

# Per NFS, è automaticamente shared
# Per LVM su iSCSI, aggiungere --shared
pvesm set iscsi-thin --shared 1

# Verificare /etc/pve/storage.cfg
cat /etc/pve/storage.cfg | grep -A 5 iscsi-thin
# Deve contenere: shared 1
```
**Prevenzione**: quando si configura storage su iSCSI o altro backend condiviso, specificare sempre `--shared 1` durante la creazione. Per Ceph RBD, la proprietà shared è impostata automaticamente.

### Problema: performance NFS degradate dopo migrazione, latenza elevata
**Sintomi**: le VM su NFS mostrano latenza I/O di 5-20 ms dove su VMware era 1-3 ms.
**Causa**: parametri NFS non ottimizzati. Le cause specifiche includono: (1) versione NFS diversa (v4 con lock manager attivo vs v3); (2) `rsize`/`wsize` troppo piccoli; (3) `async` non configurato sul server (per workload write-heavy); (4) numero insufficiente di thread NFS server; (5) congestione di rete.
**Soluzione**:
```bash
# Verificare i parametri del mount
nfsstat -m

# Aumentare i thread NFS server
echo 32 > /proc/fs/nfsd/threads

# Misurare la latenza NFS
ping -c 100 nfs-server | tail -1
# Se latenza di rete > 1ms, è un problema di rete

# Test di throughput diretto
dd if=/dev/zero of=/mnt/nfs-storage/test bs=1M count=1024 oflag=direct
dd if=/mnt/nfs-storage/test of=/dev/null bs=1M iflag=direct
```
**Prevenzione**: eseguire benchmark NFS da Proxmox prima della migrazione delle VM per avere un baseline. Ottimizzare rsize/wsize e il numero di thread NFS server in anticipo.

### Problema: Ceph OSD flapping (continuo up/down)
**Sintomi**: i log Ceph mostrano OSD che alternano rapidamente tra stati up e down. Le VM subiscono I/O stall intermittenti.
**Causa**: tipicamente causato da: (1) rete cluster instabile o troppo lenta; (2) disco di un OSD con errori hardware; (3) risorse insufficienti sul nodo (RAM, CPU) che causano timeout heartbeat; (4) clock skew tra i nodi.
**Soluzione**:
```bash
# Identificare l'OSD problematico
ceph health detail

# Verificare i log dell'OSD
journalctl -u ceph-osd@3 --since "30 minutes ago" | tail -50

# Verificare il disco
smartctl -a /dev/sdb
dmesg | grep -i error

# Verificare la rete cluster
iperf3 -c <altro-nodo> -t 10 -B <cluster-ip>

# Se il disco è degradato, sostituire l'OSD
ceph osd out 3
# Attendere recovery completo
ceph osd purge 3 --yes-i-really-mean-it
# Sostituire il disco e creare nuovo OSD
pveceph osd create /dev/sdb-new
```
**Prevenzione**: monitorare proattivamente la salute dei dischi con SMART. Configurare una rete cluster Ceph dedicata con latenza < 1 ms tra i nodi. Assicurare che ogni nodo OSD abbia almeno 4 GB di RAM per OSD.

### Problema: dopo il cutover iSCSI, LVM non vede il VG su un nodo
**Sintomi**: su uno o più nodi Proxmox, `vgscan` non trova il volume group iSCSI, anche se la sessione iSCSI è attiva.
**Causa**: il dispositivo iSCSI è connesso ma LVM non ha eseguito lo scan. Può anche essere causato da un filtro LVM in `/etc/lvm/lvm.conf` che esclude il dispositivo, o da un ordine di avvio errato (LVM scan eseguito prima della connessione iSCSI).
**Soluzione**:
```bash
# Verificare che il dispositivo iSCSI sia visibile
lsblk
iscsiadm -m session -P 3

# Forzare lo scan LVM
pvscan --cache
vgscan
vgchange -ay vg-iscsi

# Verificare il filtro LVM
grep -E "filter|global_filter" /etc/lvm/lvm.conf
# Assicurarsi che il dispositivo non sia escluso
# filter = [ "a|/dev/sd.*|", "a|/dev/mapper/.*|", "r|.*|" ]
```
**Prevenzione**: configurare LVM filter in `/etc/lvm/lvm.conf` per includere esplicitamente i dispositivi iSCSI. Configurare le dipendenze systemd affinché LVM scan avvenga dopo la connessione iSCSI.

---

## Riferimenti

- [Proxmox VE Administration Guide — Storage: NFS](https://pve.proxmox.com/pve-docs/chapter-pvesm.html#storage_nfs)
- [Proxmox VE Administration Guide — Storage: iSCSI](https://pve.proxmox.com/pve-docs/chapter-pvesm.html#storage_open_iscsi)
- [Proxmox VE Administration Guide — Ceph](https://pve.proxmox.com/pve-docs/chapter-pveceph.html)
- [Linux NFS Documentation](https://www.kernel.org/doc/html/latest/admin-guide/nfs/index.html)
- [exports(5) Manual Page](https://man7.org/linux/man-pages/man5/exports.5.html)
- [open-iscsi Documentation](https://github.com/open-iscsi/open-iscsi)
- [targetcli Documentation](https://github.com/open-iscsi/targetcli-fb)
- [Ceph Documentation — Installation](https://docs.ceph.com/en/latest/install/)
- [Ceph Documentation — Placement Groups](https://docs.ceph.com/en/latest/rados/operations/placement-groups/)
- [Linux DM-Multipath Documentation](https://www.kernel.org/doc/html/latest/admin-guide/device-mapper/dm-multipath.html)
- [Proxmox Wiki — High Availability](https://pve.proxmox.com/wiki/High_Availability)
- [TrueNAS Documentation — iSCSI](https://www.truenas.com/docs/scale/scaletutorials/shares/iscsi/)
- [RFC 7530 — NFS Version 4 Protocol](https://tools.ietf.org/html/rfc7530)
- [RFC 8881 — NFS Version 4.1 Protocol](https://tools.ietf.org/html/rfc8881)

---

## Approfondimenti — note del 2026-04-26

> **Approfondimento — `rbd import` con feature image moderne.** Quando importi un disco grande in Ceph via `qemu-img convert -O rbd`, l'immagine creata di default ha feature `layering, exclusive-lock, object-map, fast-diff, deep-flatten`. Per workload performance-sensitive, considerare disabilitare `exclusive-lock` (riduce overhead di rituals di lock) — ma occhio a non farlo se si usa migration live cross-cluster. Per cluster single-tenant, layering + fast-diff e abbastanza. Riferimento: [`CEPH-DOCS`] sezione "rbd image features".

> **Errore comune — VMFS6 lock SCSI-3 ereditato dopo unmount.** Sintomo: dopo unmount di una LUN su VMware, Proxmox non riesce a fare `pvcreate` o LVM operations: errore "device is busy" o "PR (Persistent Reservation) held by another initiator". Causa: VMware ha rilasciato il filesystem ma non il SCSI-3 PR. Soluzione: sul array (TrueNAS, Pure, ecc.) rimuovere manualmente le reservation per l'IQN VMware, oppure usare `sg_persist --clear --param-rk=$KEY /dev/sdX`. In emergenza: `sg_persist --clear --param-rk=0 -d /dev/sdX` con `--param-rk` reservation key letta da `sg_persist --read-keys`.

> **Caso reale — NFS stale handle dopo migrate.** Una VM Proxmox montava lo stesso NFS export migrato, ma alcune operazioni I/O fallivano con "Stale file handle". Causa: il server NFS (Linux con `no_subtree_check`) avesse generato file handle nuovi dopo restart, e il client Proxmox aveva cached i vecchi. Soluzione: `umount -lf /mnt/pve/<storage>` poi remount; in alternativa, riavviare il client (`systemctl restart nfs-client.target`). Per evitare in futuro: configurare `no_subtree_check` + `fsid=<UUID>` esplicito sull'export, o passare a NFSv4 (handle stabili).

---

## Esercizi

1. **Concettuale — scelta scenario.** Per ognuno: (a) cluster VMware con NetApp NFS che resta in uso; (b) array iSCSI Pure obsolescente, da sostituire; (c) vSAN cluster da decommissionare entro 6 mesi. *Risposte:* (a) Scenario A (NFS path preservato); (b) Scenario B (data migration parallela su nuovo storage); (c) Scenario D (Ceph hyperconverged Proxmox come sostituzione).

2. **Lab — rbd import di una VM Linux.** Su un cluster Ceph di test (anche 3 nodi minimi), creare un pool `rbd-vm`. Esportare un VMDK 20 GB da VMware. Eseguire `qemu-img convert -p -O rbd /tmp/disk.vmdk rbd:rbd-vm/vm-100-disk-0`. Misurare il tempo. Importare in Proxmox con `qm create 100 ... --scsi0 ceph-vm:vm-100-disk-0`. Boot test.

3. **Scenario — cutover iSCSI mismanaged.** Hai una LUN da 2 TB su array iSCSI Pure, con VMFS6 da VMware. Devi spostarla a Proxmox preservando il path. Argomenta in 12 righe: (a) procedura corretta per evitare SCSI-3 PR conflict; (b) ordine di unmount VMware vs mount Proxmox; (c) cosa fare se si scopre che VMware non ha rilasciato il PR. *Risposta:* (a) prima `vMotion` di tutte le VM su altri datastore, poi `Unmount Datastore` da vCenter, poi `Detach Device` da ogni host ESXi che la usava, poi sul array rimuovere le initiator binding; (b) ordine: VMware unmount → array confirma rilascio → Proxmox `iscsiadm --discovery` + `iscsiadm --login` + `pvcreate` o `vgcreate` su `/dev/sdX`; (c) rimuovere PR via `sg_persist`.

4. **Stretch — Ceph CRUSH map customization.** Su un cluster Ceph 6 nodi distribuiti su 2 rack, configurare la CRUSH map per garantire che le 3 repliche siano su rack diversi (RPO 0 anche con guasto rack). Verificare con `ceph osd crush rule dump` e `ceph pg dump | grep stuck`.

## Auto-valutazione

1. Differenza fra Scenario A (NFS preservato) e Scenario B (NFS migrazione path) — quando preferire l'uno o l'altro?
2. Cos'e SCSI-3 Persistent Reservation e perche conta per cutover iSCSI cross-hypervisor?
3. Comando per importare un disco direttamente in Ceph RBD?
4. Differenza fra `qemu-img convert -O rbd` e `qemu-img convert -O raw - | rbd import`?
5. Comando per leggere e rimuovere SCSI-3 PR reservation con sg_persist?
6. Quali feature image RBD sono attive di default e quali considerare disabilitare?
7. Cos'e NFS stale handle e come si risolve?
8. Test minimo per validare HA dopo cutover dello shared storage?

## Letture primarie consigliate

- [`PVE-STORAGE`] Proxmox VE Wiki — Storage. https://pve.proxmox.com/wiki/Storage
- [`CEPH-DOCS`] Ceph Documentation. https://docs.ceph.com/en/latest/
- Ceph rbd command reference. https://docs.ceph.com/en/latest/man/8/rbd/
- TrueNAS iSCSI Documentation. https://www.truenas.com/docs/scale/scaletutorials/shares/iscsi/
- [`RFC-2131`] RFC 2131 — DHCP. https://datatracker.ietf.org/doc/html/rfc2131
- RFC 7530 — NFSv4. https://datatracker.ietf.org/doc/html/rfc7530
- RFC 8881 — NFSv4.1. https://datatracker.ietf.org/doc/html/rfc8881
- sg3_utils (sg_persist man page). https://sg.danny.cz/sg/

## Collegamenti incrociati

- Modulo 03.2 — `../03-STORAGE-AVANZATO-PROXMOX/nfs-iscsi-storage-condiviso.md`: NFS/iSCSI base.
- Modulo 08.1 — `conversione-vmdk-qcow2-raw.md`: conversione VMDK preliminare.
- Modulo 08.3 — `strategie-migrazione-datastore.md`: strategie globali datastore.
- Modulo 10.1, 10.2 — `../10-CLUSTER-HA-PROXMOX-POST-MIGRAZIONE/`: HA e fencing post-cutover.
- Modulo 17.4 — `../17-TROUBLESHOOTING-E-GUIDE-PRATICHE/troubleshooting-storage-performance.md`: troubleshooting performance.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Shared storage** | Storage accessibile da piu host del cluster (NFS, iSCSI, Ceph, FC). |
| **NFS export** | Direttoria esportata da un server NFS, accessibile via mount remoto. |
| **iSCSI LUN** | Logical Unit esposta da un target iSCSI; vista dal client come block device. |
| **SCSI-3 PR** | Persistent Reservation — meccanismo di lock cluster-aware per dischi SCSI. |
| **Initiator binding** | Mappatura sull'array dello storage di "quali host vedono questa LUN". |
| **Ceph RBD** | RADOS Block Device — block storage Ceph. |
| **Pool Ceph** | Container logico di oggetti in Ceph (con replication factor, CRUSH rule). |
| **CRUSH map** | Mappa Ceph che definisce dove piazzare i dati (basata su weight e fault domain). |
| **PG (Placement Group)** | Unita Ceph di distribuzione: gruppo di oggetti gestito coerentemente. |
| **MON / OSD / MDS** | Ruoli Ceph: Monitor (cluster state), Object Storage Daemon (dati), Metadata Server (CephFS). |
| **`rbd import` / `rbd export`** | Comandi per portare immagini block fra Ceph e file system. |
| **NFS stale handle** | Errore `Stale file handle` — il file handle del client e invalido per il server. |
| **`sg_persist`** | Comando Linux per gestire SCSI-3 Persistent Reservations. |
| **`pvecm` / `ha-manager`** | CLI Proxmox per cluster e HA. |
| **Failover RTO** | Tempo entro cui le VM HA-protette devono ripartire su nodo diverso (target tipico < 2 min). |
