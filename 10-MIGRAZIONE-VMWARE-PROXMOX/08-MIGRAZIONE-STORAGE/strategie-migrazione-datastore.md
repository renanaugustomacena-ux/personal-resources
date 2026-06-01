# Strategie di Migrazione Datastore: da VMware a Proxmox VE

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 3 — Migrazione · Modulo 08.3 (vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** moduli 03.1, 03.2 (storage Proxmox), 08.1 (conversione VMDK), 08.2 (shared cutover); concetti di banda di rete e sincronizzazione incrementale (rsync, CBT, btrfs send/receive).
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. costruire un albero decisionale per scegliere il backend storage Proxmox (LVM, LVM-Thin, ZFS, NFS, CIFS, Ceph RBD, CephFS, iSCSI) sulla base dei requisiti di workload, capacity, performance, resilienza e budget;
> 2. distinguere i metodi di trasferimento dati (export+convert+import, network direct via `qemu-img convert -O rbd`, rsync block-level, dd over SSH, snapshot replication ZFS/Ceph) e calcolare i tempi di transfer in base a banda di rete disponibile;
> 3. dimensionare la banda dedicata alla migrazione (1/10/25/100 GbE), considerando overhead protocollare, encryption (SSH ~80% di linerate, plain TCP ~95%), parallelismo;
> 4. eseguire una sincronizzazione incrementale per VM grandi (1+ TB) usando rsync block-level con `--inplace --no-whole-file`, oppure ZFS `zfs send | zfs receive` quando il source e ZFS-backed;
> 5. costruire una procedura end-to-end di migrazione datastore: fase 1 prep (clone iniziale), fase 2 sync delta (delta sync), fase 3 cutover (final sync + power-on Proxmox), fase 4 validation;
> 6. compilare la checklist di decommissioning del datastore VMware (rimozione PR, unmount, scrubbing dati per disposal sicuro NIST 800-88).
> **Tempo stimato:** lettura 90-120 min · lab 240-360 min
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-26
> **Versioni di riferimento:** Proxmox VE 8.x; OpenZFS 2.2/2.3; Ceph Squid 19.2; LVM 2.03+.

## Mappa concettuale

```
+======================================================+
|  Datastore migration — albero di scelta              |
+======================================================+
|                                                      |
|   REQUIREMENT                                        |
|     +-- single nodo, no shared?                      |
|     |     +-> LVM-Thin (snapshot, thin)              |
|     |     +-> ZFS (snapshot, compression)            |
|     |                                                |
|     +-- shared cluster, snapshot needed?             |
|     |     +-> Ceph RBD (3+ nodes, replication)      |
|     |     +-> NFS + qcow2 (snapshot interno qcow2)   |
|     |                                                |
|     +-- shared cluster, no snapshot?                 |
|     |     +-> LVM su LUN iSCSI/FC condivisa         |
|     |                                                |
|     +-- read-mostly + alta capacity?                 |
|     |     +-> NFS read-cached + qcow2               |
|     |     +-> CephFS per file storage               |
|     |                                                |
|     +-- low-budget singolo nodo?                     |
|           +-> dir + qcow2 (semplice, no overhead)   |
|                                                      |
|   TRANSFER METHOD                                    |
|     +-- offline + small (< 100 GB):                  |
|     |     export OVA → qemu-img → import            |
|     |                                                |
|     +-- offline + large (TB):                        |
|     |     network direct: qemu-img convert -O rbd   |
|     |     o snapshot replication source-side        |
|     |                                                |
|     +-- online + bulk + delta:                       |
|     |     rsync --inplace --no-whole-file iterato   |
|     |     o ZFS send/recv incrementale              |
|     |                                                |
|     +-- application-aware:                           |
|           DB replication nativa (vedi 06.3, 09.2)   |
|                                                      |
|   CUTOVER ORCHESTRATION                              |
|     T-X: prep, clone iniziale                        |
|     T-Y: delta sync                                  |
|     T-0: final sync + power-on Proxmox               |
|     T+M: validate + decommission VMware              |
|                                                      |
+======================================================+
```

Idee guida del modulo:

1. **Backend storage = decisione architetturale.** La scelta non e "quale e meglio in assoluto" ma "quale serve per i miei workload e team". LVM-Thin per single nodo semplice; ZFS per single nodo con compression+snapshot; Ceph per cluster HCI; NFS per centralizzazione facile. Ognuno ha trade-off — sapere quali sono e cio che il modulo insegna.
2. **Banda di rete e SPESSO il vincolo.** 100 GB di VMDK su 1 GbE → ~14 minuti minimum (a 100 MB/s reali). Su 10 GbE → ~90 secondi. Su 25 GbE → ~35 sec. Pianificare la rete dedicata alla migrazione e *molto piu importante* della scelta del tool di conversione.
3. **`zfs send | zfs receive` e magico se entrambi i lati sono ZFS.** Trasferisce solo blocchi cambiati a livello block (super efficiente), con compression on-the-wire opzionale (`-c`). Per cluster ZFS source + ZFS target, e l'approccio piu veloce. Non funziona se source e VMware (VMFS) e target e ZFS — serve passaggio intermedio.
4. **Decommissioning sicuro = NIST SP 800-88.** Eliminare un datastore VMware non significa solo `Unmount` da vCenter. I dischi possono essere riutilizzati o smaltiti, e i dati residui vanno azzerati (NIST Clear/Purge/Destroy). Per LUN: `dd if=/dev/zero of=/dev/sdX bs=1M`, oppure crittografia preliminare e poi distruzione della chiave (Crypto-erase).
5. **Snapshot replication source-side: workflow elegante per VM grandi.** Se il source storage supporta snapshot (NetApp, Pure, ZFS-based array): take snapshot → replicate to target → boot test → take new snapshot → replicate delta → cutover. RPO target nei minuti.

## Indice
- [Panoramica](#panoramica)
- [Architettura Storage VMware](#architettura-storage-vmware)
- [Architettura Storage Proxmox VE](#architettura-storage-proxmox-ve)
- [Albero Decisionale per la Scelta del Backend Storage](#albero-decisionale-per-la-scelta-del-backend-storage)
- [Metodi di Trasferimento Dati](#metodi-di-trasferimento-dati)
- [Considerazioni sulla Banda di Rete](#considerazioni-sulla-banda-di-rete)
- [Sincronizzazione Incrementale per VM di Grandi Dimensioni](#sincronizzazione-incrementale-per-vm-di-grandi-dimensioni)
- [Procedura di Migrazione End-to-End](#procedura-di-migrazione-end-to-end)
- [Checklist di Decommissioning del Datastore VMware](#checklist-di-decommissioning-del-datastore-vmware)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

La migrazione dei datastore da VMware a Proxmox VE è un'operazione che va oltre la semplice copia di file: richiede una comprensione approfondita delle differenze architetturali tra i due ecosistemi storage, una pianificazione rigorosa dei metodi di trasferimento, e una strategia chiara per il cutover che minimizzi il downtime delle VM in produzione. In ambienti enterprise con decine di terabyte distribuiti su datastore VMFS, NFS e vSAN, l'approccio sbagliato può significare giorni di downtime non pianificato.

Questo documento fornisce un framework decisionale completo per mappare ogni tipo di datastore VMware al corrispondente backend storage Proxmox più appropriato. Vengono analizzati i metodi di trasferimento dati — da SCP per singole VM a rsync per sincronizzazioni incrementali, da NFS mount condivisi per trasferimenti in-place a trasporto fisico per volumi massicci — con le relative implicazioni su banda, tempo e rischio. Particolare attenzione è dedicata alla gestione di VM di grandi dimensioni (multi-terabyte) dove i tempi di trasferimento impongono l'uso di tecniche incrementali.

L'obiettivo finale è un processo ripetibile, documentato e reversibile che permetta di migrare l'intero ambiente storage VMware verso Proxmox con un downtime misurato in minuti per VM, non in ore. La fase di decommissioning dei datastore VMware chiude il ciclo con una checklist operativa che garantisce di non lasciare risorse orfane o licenze attive.

---

## Architettura Storage VMware

### VMFS (Virtual Machine File System)

VMFS è il filesystem a blocchi proprietario di VMware, progettato specificamente per storage di macchine virtuali su dispositivi a blocchi (SAN FC, iSCSI, SAS diretto). Le caratteristiche principali:

| Versione | Block Size Max | File Size Max | Extent Support |
|---|---|---|---|
| VMFS 5 | 1 MB (fisso) | 62 TB - 512 B | Fino a 32 extent |
| VMFS 6 | 1 MB (fisso) | 62 TB - 512 B | Fino a 32 extent |

VMFS utilizza un meccanismo di locking distribuito (on-disk locking con SCSI reservations o ATS per VAAI) che permette a più host ESXi di accedere allo stesso datastore contemporaneamente. Questo è fondamentale per vMotion e HA.

```
+------------------------------------------+
| VMFS Datastore (LUN SAN)                 |
|  +----------------+  +----------------+  |
|  | VM-Web/        |  | VM-DB/         |  |
|  |  vm-web.vmdk   |  |  vm-db.vmdk    |  |
|  |  vm-web.vmx    |  |  vm-db.vmx     |  |
|  |  vm-web.log    |  |  vm-db.log     |  |
|  +----------------+  +----------------+  |
+------------------------------------------+
         ↑                    ↑
    ESXi Host 1          ESXi Host 2
    (shared access via SCSI locking)
```

Ogni VM risiede in una directory dedicata contenente i file di configurazione (`.vmx`), i dischi virtuali (`.vmdk`), i log, e gli eventuali snapshot (`.vmsn`, delta `.vmdk`).

### NFS Datastore

VMware supporta NFS v3 e v4.1 come datastore per le VM. A differenza di VMFS, non è richiesto alcun filesystem proprietario: i file VMDK risiedono direttamente sul filesystem NFS esportato dal server storage.

```
NFS Server (es. NetApp, TrueNAS)
  Export: /vol/vmware-ds1
    ├── VM-Web/
    │   ├── vm-web.vmdk
    │   ├── vm-web-flat.vmdk
    │   └── vm-web.vmx
    └── VM-DB/
        ├── vm-db.vmdk
        ├── vm-db-flat.vmdk
        └── vm-db.vmx
```

Considerazioni importanti per la migrazione: i datastore NFS VMware possono essere rimontati direttamente da Proxmox (potenzialmente in modalità read-only) durante la migrazione, eliminando la necessità di copiare i dati attraverso la rete. Questa strategia è descritta nella sezione dedicata.

### vSAN (Virtual SAN)

VMware vSAN è un'architettura hyper-converged che aggrega i dischi locali di più host ESXi in un pool storage distribuito. I dati sono distribuiti e replicati attraverso i nodi secondo policy di storage (FTT = Failures To Tolerate).

```
+--------+    +--------+    +--------+
| ESXi 1 |    | ESXi 2 |    | ESXi 3 |
| SSD+HDD|    | SSD+HDD|    | SSD+HDD|
+---+----+    +---+----+    +---+----+
    |             |             |
    +------+------+------+------+
           |  vSAN Network  |
           |  (10/25 GbE)   |
           +-----------------+
           | vSAN Datastore  |
           | (distribuito)   |
           +-----------------+
```

La migrazione da vSAN è la più complessa poiché i dati non risiedono su un singolo dispositivo storage. Le VM devono essere esportate tramite vMotion su un datastore non-vSAN, oppure esportate come OVA/OVF, oppure i dischi devono essere copiati tramite l'API VMware.

### Inventario Pre-Migrazione

Prima di procedere, catalogare tutti i datastore:

```bash
# Da vCenter (PowerCLI)
Get-Datastore | Select-Object Name, Type, CapacityGB, FreeSpaceGB,
    @{N='UsedGB';E={[math]::Round($_.CapacityGB - $_.FreeSpaceGB, 2)}},
    @{N='VMCount';E={($_ | Get-VM).Count}} |
    Sort-Object UsedGB -Descending |
    Format-Table -AutoSize

# Output esempio:
# Name          Type  CapacityGB FreeSpaceGB UsedGB VMCount
# ----          ----  ---------- ----------- ------ -------
# DS-PROD-01    VMFS     2048.00      512.00 1536.00      24
# DS-PROD-02    VMFS     2048.00      820.00 1228.00      18
# DS-NFS-01     NFS      4096.00     1800.00 2296.00      35
# vsanDatastore vSAN     6144.00     2048.00 4096.00      52
```

```bash
# Dettaglio per VM: dimensione disco effettiva
Get-VM | Select-Object Name,
    @{N='ProvisionedGB';E={[math]::Round($_.ProvisionedSpaceGB, 2)}},
    @{N='UsedGB';E={[math]::Round($_.UsedSpaceGB, 2)}},
    @{N='Datastore';E={($_ | Get-Datastore).Name -join ', '}} |
    Sort-Object UsedGB -Descending |
    Export-Csv -Path "vm-inventory.csv" -NoTypeInformation
```

---

## Architettura Storage Proxmox VE

### Local Directory (/var/lib/vz)

Storage basato su filesystem locale. Supporta tutti i content type (VM images, ISO, templates, backups). I dischi delle VM sono file qcow2 o raw su ext4/xfs.

**Pro**: semplice, nessuna configurazione aggiuntiva, supporta qcow2 con tutte le sue funzionalità.
**Contro**: no shared storage (no live migration nativa), performance dipendenti dal filesystem sottostante, no thin provisioning nativo (dipende da sparse files).

### LVM (Logical Volume Manager)

Storage a blocchi con logical volumes dedicati per ogni disco VM. Il contenuto è raw.

```bash
# Configurazione tipica
pvcreate /dev/sdb
vgcreate vmdata /dev/sdb
# I volumi sono creati da Proxmox automaticamente:
# /dev/vmdata/vm-100-disk-0
```

**Pro**: performance raw ottime, gestione volumi flessibile.
**Contro**: thick provisioning (lo spazio è allocato completamente), no snapshot efficienti.

### LVM-Thin

Evoluzione di LVM con thin provisioning pool:

```bash
# Creazione thin pool
lvcreate -L 900G --thinpool thinpool vmdata
# Proxmox crea thin LV automaticamente:
# /dev/vmdata/vm-100-disk-0 (thin LV nel pool)
```

```
+----------------------------------+
| VG: vmdata                       |
|  +----------------------------+  |
|  | Thin Pool: thinpool (900G) |  |
|  |  +-----+  +-----+         |  |
|  |  |vm100|  |vm101|  (thin) |  |
|  |  | 50G |  | 80G |  LVs    |  |
|  |  +-----+  +-----+         |  |
|  |  Actual used: 65G          |  |
|  +----------------------------+  |
+----------------------------------+
```

**Pro**: thin provisioning, snapshot efficienti (CoW), performance raw.
**Contro**: no compressione, monitoring del thin pool obbligatorio, no shared storage nativo.

### ZFS

Filesystem avanzato con funzionalità enterprise integrate:

```bash
# Creazione pool
zpool create -f rpool mirror /dev/sda /dev/sdb
zfs create rpool/data

# Proxmox crea zvol automaticamente:
# rpool/data/vm-100-disk-0
```

**Pro**: compressione trasparente (lz4, zstd), snapshot istantanei, checksum per integrità dati, send/receive per replica, deduplicazione (con cautela).
**Contro**: consumo RAM significativo (ARC), overhead CPU per compressione/checksum, no shared storage nativo, performance di scrittura casuale inferiori con record size grandi.

### NFS

Mount di share NFS come storage Proxmox. Supporta content type per immagini disco (qcow2/raw), ISO e backup.

```bash
# Configurazione in Proxmox
pvesm add nfs nfs-storage --server 192.168.1.10 \
    --export /vol/proxmox-data --content images,iso,backup \
    --options vers=4.1
```

**Pro**: shared storage (live migration), riutilizzo infrastruttura NFS esistente, semplice da configurare.
**Contro**: performance dipendenti dalla rete, latenza aggiuntiva, single point of failure se il server NFS non è in HA.

### iSCSI + LVM

Combinazione di target iSCSI come physical volume per LVM:

```bash
# Proxmox configura l'initiator iSCSI
pvesm add iscsi iscsi-storage --portal 192.168.1.20 \
    --target iqn.2024-01.com.storage:proxmox-lun1

# Poi LVM sopra il dispositivo iSCSI
pvesm add lvm lvm-iscsi --vgname vg-iscsi --base iscsi-storage:0.0.0.scsi-lun0 \
    --content images
```

**Pro**: shared storage (live migration), performance blocchi, compatibilità con SAN esistenti.
**Contro**: configurazione complessa, dipendenza dalla rete, richiede multipathing per HA.

### Ceph (RBD)

Storage distribuito integrato nativamente in Proxmox:

```bash
# Ceph pool per VM
ceph osd pool create vm-pool 128
ceph osd pool set vm-pool size 3
pvesm add rbd ceph-storage --pool vm-pool --content images
```

**Pro**: shared storage nativo (live migration), nessun SPOF, auto-healing, scalabilità lineare.
**Contro**: richiede almeno 3 nodi, overhead di rete significativo, complessità operativa, latenza maggiore di storage locale.

---

## Albero Decisionale per la Scelta del Backend Storage

```
                         Serve shared storage
                        per live migration?
                       /                     \
                     Sì                       No
                    /                           \
        Budget per Ceph             Performance è
         (3+ nodi, rete             la priorità?
          dedicata)?               /            \
         /          \            Sì              No
       Sì           No          /                \
       |             |    Serve compressione    Serve thin
    Ceph RBD    Esiste già    o checksum?      provisioning?
                infrastruttura  /       \       /          \
                SAN/NAS?      Sì        No   Sì            No
               /       \      |          |    |              |
             Sì         No  ZFS zvol    LVM  LVM-Thin    Directory
            /             \                               (qcow2)
    È NFS o iSCSI?    NFS Server
      /        \       dedicato
    NFS     iSCSI+LVM
```

### Matrice di Mapping VMware → Proxmox

| Sorgente VMware | Use Case | Proxmox Raccomandato | Alternativa |
|---|---|---|---|
| VMFS su SAN FC | High-performance DB | LVM-Thin locale (NVMe) | Ceph RBD |
| VMFS su iSCSI | General purpose | LVM-Thin locale | iSCSI + LVM |
| VMFS locale | Single host, test | ZFS locale | LVM-Thin |
| NFS datastore | File server, general | NFS (riutilizzo) | ZFS locale |
| vSAN | Hyper-converged | Ceph RBD | ZFS + replica manuale |
| vSAN (piccolo) | 2-3 nodi | ZFS mirrored locale | LVM-Thin + backup |

---

## Metodi di Trasferimento Dati

### SCP (Secure Copy Protocol)

Il metodo più semplice per trasferire singoli file VMDK:

```bash
# Da Proxmox, scaricare VMDK da ESXi
scp root@esxi-01:/vmfs/volumes/DS-PROD-01/VM-Web/VM-Web.vmdk /tmp/
scp root@esxi-01:/vmfs/volumes/DS-PROD-01/VM-Web/VM-Web-flat.vmdk /tmp/

# Trasferimento con compressione on-the-fly
scp -C root@esxi-01:/vmfs/volumes/DS-PROD-01/VM-Web/VM-Web-flat.vmdk /tmp/
```

**Vantaggi**: semplice, crittografato, disponibile ovunque.
**Svantaggi**: non supporta resume, non preserva sparse files, no delta/incrementale, singolo stream (lento su alta latenza).

### rsync

Strumento preferito per trasferimenti che possono essere interrotti e ripresi:

```bash
# Trasferimento con progress, compressione e sparse file handling
rsync -avP --sparse \
    root@esxi-01:/vmfs/volumes/DS-PROD-01/VM-Web/ \
    /tmp/VM-Web/

# Con limitazione di banda (per non saturare il link di produzione)
rsync -avP --sparse --bwlimit=500000 \
    root@esxi-01:/vmfs/volumes/DS-PROD-01/VM-Web/ \
    /tmp/VM-Web/
# --bwlimit in KB/s, 500000 = ~500 MB/s
```

**Vantaggi**: resume automatico, delta transfer, preserva sparse files, compressione, rate limiting.
**Svantaggi**: il delta su file VMDK di grandi dimensioni richiede un checksum scan completo (lento per la prima esecuzione), SSH overhead.

### NFS Mount Condiviso

Quando il datastore sorgente è NFS, il metodo più efficiente è montare lo stesso export NFS anche da Proxmox:

```bash
# Su Proxmox, montare il datastore NFS VMware in sola lettura
mount -t nfs -o ro,vers=3 nfs-server:/vol/vmware-ds1 /mnt/vmware-nfs

# Conversione diretta dal mount NFS al storage locale
qemu-img convert -p -W -m 8 -f vmdk -O qcow2 \
    /mnt/vmware-nfs/VM-Web/VM-Web.vmdk \
    /var/lib/vz/images/100/vm-100-disk-0.qcow2

# Oppure importazione diretta
qm importdisk 100 /mnt/vmware-nfs/VM-Web/VM-Web.vmdk local-lvm --format raw
```

**Vantaggi**: nessuna copia intermedia, il dato transita direttamente da NFS al storage locale, massima efficienza.
**Svantaggi**: richiede che il server NFS sia raggiungibile da Proxmox, possibile conflitto di lock se il datastore è ancora attivo su ESXi.

### Esportazione OVA/OVF con ovftool

Per ambienti con vCenter, `ovftool` esporta VM complete:

```bash
# Esportare come OVA (singolo file archivio)
ovftool --diskMode=thin \
    'vi://administrator@vsphere.local@vcenter.example.com/DC/vm/VM-Web' \
    /tmp/VM-Web.ova

# Esportare come OVF (directory con file separati)
ovftool --diskMode=thin \
    'vi://administrator@vsphere.local@vcenter.example.com/DC/vm/VM-Web' \
    /tmp/VM-Web/VM-Web.ovf

# Esportazione batch
for vm in VM-Web VM-DB VM-App; do
    ovftool --diskMode=thin --noSSLVerify \
        "vi://admin:password@vcenter/DC/vm/${vm}" \
        "/export/${vm}.ova" &
done
wait
```

Importazione in Proxmox:

```bash
# Proxmox supporta l'importazione diretta di OVF
qm importovf 100 /tmp/VM-Web/VM-Web.ovf local-lvm

# Per OVA, prima estrarre
tar xvf /tmp/VM-Web.ova -C /tmp/VM-Web-extracted/
qm importovf 100 /tmp/VM-Web-extracted/VM-Web.ovf local-lvm
```

### Trasporto Fisico (Offline Migration)

Per volumi superiori a 10 TB o quando la rete è insufficiente, il trasporto fisico dei dischi è spesso la soluzione più veloce:

```bash
# Calcolo tempo di trasferimento via rete
# 20 TB a 10 Gbps = 20 * 1024 * 8 / 10 = 16384 secondi = ~4.5 ore (teorico)
# Reale con overhead: ~6-8 ore

# Con 1 Gbps: ~45 ore

# Procedura trasporto fisico:
# 1. Esportare su disco USB/SATA portatile
rsync -avP --sparse /vmfs/volumes/DS-PROD-01/ /mnt/usb-disk/DS-PROD-01/

# 2. Trasportare fisicamente il disco

# 3. Sul host Proxmox, montare e convertire
mount /dev/sdc1 /mnt/transport-disk
qemu-img convert -p -W -f vmdk -O raw \
    /mnt/transport-disk/DS-PROD-01/VM-DB/VM-DB.vmdk \
    /dev/pve/vm-101-disk-0
```

Soglia decisionale approssimativa:

```
+-------------------+-------------------+-------------------+
| Volume Dati       | 1 Gbps (reale)    | 10 Gbps (reale)   |
+-------------------+-------------------+-------------------+
| 1 TB              | ~3 ore            | ~20 minuti         |
| 5 TB              | ~14 ore           | ~1.5 ore           |
| 10 TB             | ~28 ore           | ~3 ore             |
| 20 TB             | ~56 ore           | ~6 ore             |
| 50 TB             | ~6 giorni         | ~15 ore            |
+-------------------+-------------------+-------------------+
Se trasporto fisico < tempo rete → usare trasporto fisico
Tipicamente conviene oltre 10 TB su 1 Gbps o 50 TB su 10 Gbps
```

---

## Considerazioni sulla Banda di Rete

### Dimensionamento della Rete di Migrazione

La rete di migrazione deve essere separata dalla rete di produzione per evitare impatti sulle VM in esecuzione.

```
ESXi Host                    Proxmox Host
+-----------+                +-----------+
| vmk0 mgmt|----[1GbE]------|  vmbr0    | Management
| vmk1 prod |----[10GbE]----|  vmbr1    | VM Traffic
| vmk2 migr |----[10GbE]----|  vmbr2    | Migration (dedicata)
+-----------+                +-----------+
```

### Calcolo Banda Effettiva

```
Banda effettiva = Banda fisica * efficienza_protocollo * (1 - overhead)

10 GbE:
  - Banda fisica: 10 Gbps = 1250 MB/s
  - Efficienza TCP: ~93% = 1162 MB/s
  - Overhead SSH/SCP: ~5% = 1104 MB/s
  - Overhead rsync: ~8% = 1070 MB/s
  - Con compressione (dati comprimibili): +30-50%

25 GbE:
  - Banda effettiva SCP: ~2700 MB/s
  - Banda effettiva rsync: ~2600 MB/s
```

### Ottimizzazione del Throughput

```bash
# Aumentare il buffer TCP per trasferimenti su link ad alta banda
sysctl -w net.core.rmem_max=67108864
sysctl -w net.core.wmem_max=67108864
sysctl -w net.ipv4.tcp_rmem="4096 87380 33554432"
sysctl -w net.ipv4.tcp_wmem="4096 65536 33554432"
sysctl -w net.ipv4.tcp_window_scaling=1

# Usare bbr come congestion algorithm
sysctl -w net.ipv4.tcp_congestion_control=bbr

# Per SCP/rsync, usare cifratura veloce
rsync -avP --sparse -e "ssh -c aes128-gcm@openssh.com -o Compression=no" \
    root@esxi:/vmfs/volumes/DS-PROD-01/VM-Web/ /tmp/VM-Web/
```

### Trasferimento Parallelo Multi-Stream

Per saturare link 10+ GbE con singoli file di grandi dimensioni:

```bash
# Usare pigz + ssh per compressione parallela
ssh root@esxi "cat /vmfs/volumes/DS-PROD-01/VM-DB/VM-DB-flat.vmdk" | \
    pigz -d | dd of=/tmp/VM-DB-flat.vmdk bs=4M status=progress

# Oppure split + trasferimento parallelo
# Sul sorgente
split -b 10G -d VM-DB-flat.vmdk VM-DB-part-

# Trasferimento parallelo
for part in VM-DB-part-*; do
    rsync -avP --sparse root@esxi:/tmp/split/$part /tmp/split/ &
done
wait

# Riassemblare
cat VM-DB-part-* > VM-DB-flat.vmdk
```

---

## Sincronizzazione Incrementale per VM di Grandi Dimensioni

Per VM con dischi multi-terabyte, il trasferimento completo può richiedere ore. La strategia incrementale riduce il downtime finale:

### Strategia Pre-Sync + Final Sync

```
Fase 1: Pre-sync (VM in esecuzione su VMware)
  - Copia iniziale completa del VMDK (ore)
  - La VM continua a funzionare su VMware

Fase 2: Delta sync (VM in esecuzione su VMware)
  - rsync incrementale, trasferisce solo i blocchi modificati (minuti-ore)
  - Ripetere fino a quando il delta è piccolo

Fase 3: Final sync + cutover (downtime)
  - Spegnere la VM su VMware
  - rsync finale (minuti)
  - Convertire e avviare su Proxmox
```

```bash
# Fase 1: copia iniziale (VM accesa, il disco viene modificato)
rsync -avP --sparse \
    root@esxi:/vmfs/volumes/DS-PROD-01/VM-DB/VM-DB-flat.vmdk \
    /tmp/VM-DB-flat.vmdk

# Fase 2: delta sync (ripetere fino a convergenza)
rsync -avP --sparse --inplace \
    root@esxi:/vmfs/volumes/DS-PROD-01/VM-DB/VM-DB-flat.vmdk \
    /tmp/VM-DB-flat.vmdk
# --inplace: aggiorna il file in-place senza creare una copia temporanea

# Monitorare la dimensione del delta
# Quando il trasferimento dura meno di 5-10 minuti, procedere alla Fase 3

# Fase 3: spegnere VM, sync finale, convertire
ssh root@esxi "vim-cmd vmsvc/power.off <vmid>"
rsync -avP --sparse --inplace \
    root@esxi:/vmfs/volumes/DS-PROD-01/VM-DB/VM-DB-flat.vmdk \
    /tmp/VM-DB-flat.vmdk

# Convertire
qemu-img convert -p -W -f vmdk -O raw /tmp/VM-DB-flat.vmdk /dev/pve/vm-101-disk-0

# Avviare su Proxmox
qm start 101
```

### CBT (Changed Block Tracking) via VMware API

Per delta più precisi, utilizzare il Changed Block Tracking di VMware tramite l'API VDDK. Questo richiede strumenti specializzati come `vmware-vddk` o tool commerciali come Veeam:

```python
# Esempio concettuale con pyvmomi/VDDK
# Abilitare CBT sulla VM
vm.ReconfigVM_Task(
    vim.vm.ConfigSpec(changeTrackingEnabled=True)
)

# Dopo un snapshot, ottenere i blocchi modificati
changes = vm.QueryChangedDiskAreas(
    snapshot=snapshot_ref,
    deviceKey=disk_key,
    startOffset=0,
    changeId="*"
)
# changes.changedArea contiene offset e lunghezza dei blocchi modificati
```

---

## Procedura di Migrazione End-to-End

### Fase 1: Inventario e Pianificazione

```bash
# 1.1 Elencare tutti i datastore e VM
Get-Datastore | ForEach-Object {
    $ds = $_
    Get-VM -Datastore $ds | Select-Object Name,
        @{N='Datastore';E={$ds.Name}},
        @{N='UsedGB';E={[math]::Round($_.UsedSpaceGB, 2)}},
        @{N='ProvisionedGB';E={[math]::Round($_.ProvisionedSpaceGB, 2)}},
        NumCpu, MemoryGB
}

# 1.2 Calcolare lo spazio totale necessario su Proxmox
# Spazio effettivo (usato) + 20% margine
```

### Fase 2: Preparazione Storage Proxmox

```bash
# 2.1 Esempio: creare LVM-Thin pool
pvcreate /dev/nvme0n1
vgcreate vm-storage /dev/nvme0n1
lvcreate -l 95%FREE --thinpool thinpool vm-storage

# 2.2 Registrare in Proxmox
pvesm add lvmthin local-nvme --vgname vm-storage --thinpool thinpool \
    --content images,rootdir

# 2.3 Oppure ZFS
zpool create -f tank mirror /dev/sda /dev/sdb
zfs create tank/vm-data
zfs set compression=lz4 tank/vm-data
pvesm add zfspool zfs-tank --pool tank/vm-data --content images,rootdir
```

### Fase 3: Migrazione delle VM (per batch)

Organizzare le VM in batch per priorità e dipendenza:

```
Batch 1 (Test):       VM-Test-01, VM-Test-02        (2 VM, basso rischio)
Batch 2 (Dev):        VM-Dev-Web, VM-Dev-DB          (4 VM, rischio medio)
Batch 3 (Staging):    VM-Staging-*                    (6 VM, rischio medio)
Batch 4 (Prod Low):   VM-Prod-Monitor, VM-Prod-Log   (3 VM, basso impatto)
Batch 5 (Prod High):  VM-Prod-Web, VM-Prod-App       (4 VM, alto impatto)
Batch 6 (Prod Crit):  VM-Prod-DB-Master              (1 VM, massimo rischio)
```

Per ogni VM nel batch:

```bash
# 3.1 Creare la VM su Proxmox (senza disco)
qm create 100 --name VM-Web --memory 4096 --cores 4 \
    --net0 virtio,bridge=vmbr0 --ostype l26 \
    --scsihw virtio-scsi-single --bios seabios

# 3.2 Trasferire e convertire il disco
qm importdisk 100 /tmp/VM-Web.vmdk local-nvme --format raw

# 3.3 Collegare il disco
qm set 100 --scsi0 local-nvme:vm-100-disk-0,iothread=1,discard=on

# 3.4 Configurare il boot
qm set 100 --boot order=scsi0

# 3.5 Avviare e verificare
qm start 100
```

### Fase 4: Validazione

```bash
# 4.1 Verificare boot e connettività
qm status 100
ping -c 5 <ip-vm>

# 4.2 Verificare servizi applicativi
curl -s http://<ip-vm>:80/health

# 4.3 Verificare performance I/O (nella VM)
fio --name=test --ioengine=libaio --rw=randread --bs=4k --numjobs=4 \
    --size=1G --runtime=30 --direct=1 --group_reporting
```

---

## Checklist di Decommissioning del Datastore VMware

Dopo la migrazione completa e la validazione di tutte le VM, procedere al decommissioning sistematico:

### Pre-Decommissioning

- [ ] Verificare che **tutte** le VM del datastore siano migrate e funzionanti su Proxmox
- [ ] Verificare che i backup delle VM migrate su Proxmox siano attivi e testati
- [ ] Mantenere i VMDK originali per almeno 30 giorni come rollback
- [ ] Documentare il mapping datastore VMware → storage Proxmox

### Decommissioning VM su VMware

```bash
# Per ogni VM migrata
# 1. Verificare che sia spenta
vim-cmd vmsvc/power.getstate <vmid>

# 2. Rimuovere dall'inventario (non elimina i file)
vim-cmd vmsvc/unregister <vmid>

# 3. Opzionale: rimuovere i file (solo dopo periodo di retention)
# rm -rf /vmfs/volumes/DS-PROD-01/VM-Web/
```

### Decommissioning Datastore

- [ ] Verificare che il datastore sia vuoto (nessun file residuo)
- [ ] Rimuovere il datastore da tutti gli host ESXi
- [ ] Se VMFS su LUN SAN: rimuovere lo zoning FC o la sessione iSCSI
- [ ] Se NFS: smontare l'export, ma mantenerlo disponibile per 30 giorni
- [ ] Aggiornare la documentazione di rete/storage
- [ ] Revocare le credenziali di accesso dedicate alla migrazione

### Decommissioning Licenze

- [ ] Annotare le licenze VMware liberate (vSphere, vSAN, vCenter)
- [ ] Se applicabile, restituire le licenze al pool o annullare il rinnovo
- [ ] Documentare la data di fine utilizzo per audit di compliance

### Decommissioning Hardware

Se i server ESXi verranno riutilizzati come nodi Proxmox:

- [ ] Reinstallare con Proxmox VE
- [ ] Configurare networking, storage, clustering
- [ ] Integrare nel cluster Proxmox esistente
- [ ] Migrare ulteriori VM dal cluster VMware ridotto

---

## Best Practices

- Eseguire sempre un inventario completo dei datastore con dimensioni effettive, numero di VM e tipo di storage prima di pianificare la migrazione.
- Separare la rete di migrazione dalla rete di produzione; utilizzare un link dedicato 10GbE o superiore per i trasferimenti.
- Migrare in batch ordinati per rischio crescente: prima ambienti test/dev, poi staging, infine produzione critica.
- Per datastore NFS VMware, montare lo stesso export in read-only da Proxmox per evitare copie intermedie.
- Utilizzare rsync con `--sparse --inplace` per la sincronizzazione incrementale di VM di grandi dimensioni, riducendo il downtime finale a minuti.
- Non eliminare i VMDK originali per almeno 30 giorni dopo la migrazione; mantenerli come piano di rollback.
- Monitorare attivamente l'utilizzo dello storage Proxmox thin-provisioned; configurare alert all'80% di utilizzo del pool.
- Per ogni VM migrata, documentare: datastore sorgente, storage destinazione, metodo di trasferimento, tempo impiegato, esito della verifica.
- Verificare che i backup Proxmox (PBS o vzdump) siano attivi e funzionanti prima di considerare il decommissioning dei datastore VMware.
- Testare il rollback su almeno una VM per batch prima di procedere con la migrazione di massa.
- Utilizzare `qm importdisk` o `qm importovf` quando possibile per una gestione automatizzata del naming e della registrazione dei dischi.
- Calcolare i tempi di trasferimento reali con un test su una VM rappresentativa prima di pianificare la finestra di migrazione per l'intero ambiente.

---

## Troubleshooting

### Problema: trasferimento SCP/rsync estremamente lento su link 10 GbE
**Sintomi**: il throughput di trasferimento è limitato a 100-300 MB/s su un link 10 GbE che dovrebbe raggiungere 1+ GB/s.
**Causa**: le cause più comuni sono: (1) buffer TCP troppo piccoli per il bandwidth-delay product del link; (2) cifratura SSH che limita il throughput a 300-400 MB/s per singolo stream; (3) MTU non ottimale (jumbo frames non configurati); (4) CPU bottleneck per cifratura.
**Soluzione**:
```bash
# Aumentare buffer TCP
sysctl -w net.core.rmem_max=67108864
sysctl -w net.core.wmem_max=67108864

# Usare cifratura leggera
rsync -avP -e "ssh -c aes128-gcm@openssh.com" source dest

# Configurare jumbo frames (MTU 9000) su entrambi gli endpoint
ip link set eth1 mtu 9000

# Verificare con iperf3
iperf3 -c <peer-ip> -t 10 -P 4
```
**Prevenzione**: testare il throughput di rete con `iperf3` prima di iniziare la migrazione e ottimizzare i parametri di rete in anticipo.

### Problema: rsync riporta "file has vanished" durante la sincronizzazione
**Sintomi**: rsync mostra warning "file has vanished" per file `.vmdk` di snapshot o log.
**Causa**: la VM sorgente è ancora in esecuzione e VMware crea/rimuove file temporanei (log rotation, snapshot consolidation). I file di log `.log` e i file di lock `.lck` cambiano continuamente.
**Soluzione**:
```bash
# Escludere i file volatili
rsync -avP --sparse \
    --exclude='*.log' --exclude='*.lck' --exclude='*.vswp' \
    --exclude='*-ctk.vmdk' \
    root@esxi:/vmfs/volumes/DS-PROD-01/VM-Web/ /tmp/VM-Web/
```
**Prevenzione**: per il sync finale, spegnere sempre la VM prima dell'ultima esecuzione di rsync.

### Problema: qm importovf fallisce con errore di formato OVF non supportato
**Sintomi**: `qm importovf` restituisce errore "unsupported OVF version" o "unknown hardware type".
**Causa**: la versione OVF esportata da VMware utilizza estensioni proprietarie (vmw: namespace) o versione hardware virtuale non supportata da Proxmox.
**Soluzione**: estrarre i file e importare manualmente i dischi:
```bash
# Estrarre l'OVA
tar xvf VM-Web.ova
# Convertire il VMDK manualmente
qemu-img convert -p -W -f vmdk -O qcow2 VM-Web-disk1.vmdk /tmp/vm-disk.qcow2
# Creare la VM manualmente e importare il disco
qm create 100 --name VM-Web --memory 4096 --cores 2
qm importdisk 100 /tmp/vm-disk.qcow2 local-lvm
```
**Prevenzione**: esportare con `ovftool` usando `--overwrite --lax` per massima compatibilità. Verificare la versione hardware della VM su VMware (hardware version 13-19 sono generalmente supportate).

### Problema: spazio insufficiente durante la migrazione batch
**Sintomi**: una conversione fallisce con ENOSPC a metà di un batch di migrazione.
**Causa**: la pianificazione dello spazio non ha considerato lo spazio temporaneo necessario per i VMDK intermedi prima della conversione, oppure il thin pool si è riempito più del previsto.
**Soluzione**: verificare lo spazio in tempo reale e pianificare un buffer:
```bash
# Monitorare continuamente durante il batch
watch -n 5 'lvs --noheadings -o lv_name,data_percent pve/data; echo "---"; df -h /tmp'

# Liberare spazio: rimuovere VMDK intermedi delle VM già verificate
rm -f /tmp/VM-Web.vmdk /tmp/VM-Web-flat.vmdk
```
**Prevenzione**: calcolare lo spazio necessario per il batch completo, includendo sia lo spazio finale che lo spazio temporaneo per i file intermedi. Regola: spazio necessario = spazio finale VM + dimensione della VM più grande del batch (per il file temporaneo). Monitorare il thin pool durante le conversioni.

### Problema: la VM migrata ha connettività di rete assente
**Sintomi**: la VM si avvia correttamente su Proxmox ma non ha connettività di rete.
**Causa**: il driver di rete è cambiato. VMware usa `vmxnet3` che non è disponibile in KVM. Proxmox assegna `virtio-net` per default, che richiede driver VirtIO nella VM guest. Inoltre, il nome dell'interfaccia potrebbe cambiare (da `ens192` a `ens18`) causando il mancato match con la configurazione di rete persistente.
**Soluzione**:
```bash
# Nella VM Linux, verificare le interfacce
ip link show
# Se l'interfaccia VirtIO è presente ma non configurata:
# Aggiornare la configurazione di rete con il nuovo nome

# Per RHEL/CentOS 7 con regole udev persistenti
rm -f /etc/udev/rules.d/70-persistent-net.rules
# Reboot

# Per sistemi con NetworkManager
nmcli device status
nmcli con mod "old-connection" connection.interface-name ens18
```
**Prevenzione**: installare i driver VirtIO nella VM guest prima della migrazione (su VMware). Per Windows, installare il pacchetto `virtio-win` drivers. Per Linux, i driver VirtIO sono inclusi nel kernel standard.

### Problema: migrazione vSAN — impossibile accedere ai VMDK direttamente
**Sintomi**: i VMDK su vSAN non sono accessibili via percorso filesystem standard come su VMFS.
**Causa**: vSAN utilizza un object store distribuito, non un filesystem tradizionale. I file VMDK non risiedono su un singolo dispositivo ma sono distribuiti come oggetti tra i nodi.
**Soluzione**: utilizzare uno dei seguenti metodi:
```bash
# Metodo 1: Storage vMotion della VM su un datastore VMFS/NFS temporaneo
# In vCenter: VM → Migrate → Change storage only → Selezionare datastore non-vSAN

# Metodo 2: Esportare via ovftool
ovftool --diskMode=thin \
    'vi://admin@vcenter/DC/vm/VM-vSAN' /tmp/VM-vSAN.ova

# Metodo 3: VMware VDDK API per download diretto
# (richiede tool specializzati)
```
**Prevenzione**: pianificare un datastore VMFS/NFS temporaneo come "staging area" per le VM vSAN da migrare. Dimensionare lo staging per contenere almeno il batch corrente di VM.

### Problema: performance degradate dopo migrazione da VMFS thick a LVM-thin
**Sintomi**: la VM migrata presenta latenza I/O superiore e IOPS inferiori rispetto all'ambiente VMware.
**Causa**: il passaggio da thick provisioning (spazio pre-allocato, I/O sequenziale) a thin provisioning (allocazione on-demand, potenziale frammentazione) introduce overhead. Inoltre, il cache mode potrebbe essere sub-ottimale.
**Soluzione**:
```bash
# 1. Verificare il cache mode
qm config 100 | grep scsi0
# Impostare cache writeback se lo storage ha protezione (BBU/capacitor)
qm set 100 --scsi0 local-nvme:vm-100-disk-0,cache=writeback,iothread=1

# 2. Verificare I/O scheduler
cat /sys/block/nvme0n1/queue/scheduler
# Per NVMe: none (noop)

# 3. Per LVM-thin, verificare la frammentazione
lvs -o+data_percent,metadata_percent pve/data
```
**Prevenzione**: eseguire benchmark I/O pre e post migrazione per avere un confronto oggettivo. Configurare il cache mode appropriato in base alla protezione write-cache dello storage hardware.

---

## Riferimenti

- [Proxmox VE Administration Guide — Storage](https://pve.proxmox.com/pve-docs/chapter-pvesm.html)
- [Proxmox Wiki — Storage](https://pve.proxmox.com/wiki/Storage)
- [VMware vSphere Documentation — Datastores](https://docs.vmware.com/en/VMware-vSphere/8.0/vsphere-storage/GUID-7BED10DD-3EF2-4670-BA7F-0EEB4EC6EB85.html)
- [VMware ovftool User Guide](https://docs.vmware.com/en/VMware-vSphere/8.0/ovf-tool-user-guide.pdf)
- [rsync Manual Page](https://download.samba.org/pub/rsync/rsync.1)
- [Linux LVM2 Thin Provisioning](https://man7.org/linux/man-pages/man7/lvmthin.7.html)
- [OpenZFS Documentation](https://openzfs.github.io/openzfs-docs/)
- [Ceph Documentation — Block Devices](https://docs.ceph.com/en/latest/rbd/)
- [Proxmox Wiki — Migration of servers to Proxmox VE](https://pve.proxmox.com/wiki/Migration_of_servers_to_Proxmox_VE)
- [VMware PowerCLI Documentation](https://developer.vmware.com/powercli)

---

## Approfondimenti — note del 2026-04-26

> **Approfondimento — `qemu-img convert -O rbd` direct su Ceph.** Trasferisce direttamente da source disk a Ceph RBD, scavalcando il filesystem locale. Comando: `qemu-img convert -p -O rbd /tmp/disk.vmdk rbd:rbd/vm-100-disk-0`. Limitazione: richiede `qemu-block-rbd` package (`apt install qemu-block-extra`) e che l'utente abbia keyring Ceph leggibile (`/etc/ceph/ceph.client.admin.keyring`). Performance: limitata dal CPU del client (single-thread su qemu-img < 9.x; multi-thread su 9.x+).

> **Errore comune — Calcolo banda errato.** Stima "1 TB su 10 GbE = 13 min" e ottimistica. Realta: 10 GbE in TCP plain raggiunge ~9.5 Gbps (~1.2 GB/s); con encryption SSH/TLS scende a ~7 Gbps (~870 MB/s); con qemu-img single-thread spesso non passa 1 GB/s perche CPU-bound. Calcolo realistico: 1 TB / 800 MB/s = ~21 min. Per parallelizzare e saturare 10 GbE in encryption, usare `mbuffer` o `pigz` prima di `ssh`.

> **Caso reale — Decommissioning datastore senza scrub.** Un datastore VMFS contenente VM con dati sensibili (HR, finanziari) e stato semplicemente "Unmount + remove from inventory" senza scrub. Mesi dopo, i dischi sono stati ricicalti per altro uso e parte dei dati erano ancora recuperabili (block-level). Per evitare: pre-decommissioning, eseguire (a) `dd if=/dev/zero of=/dev/sdX bs=1M status=progress` (ore per TB), oppure (b) full-disk encryption preliminare e poi distruggi la chiave (NIST 800-88 "Crypto-Erase", istantaneo). Per dischi rotanti, anche un singolo passaggio di zero e adeguato (data NIST 800-88 r1, sez. 2.4).

---

## Esercizi

1. **Concettuale — albero decisionale.** Per ognuno: (a) singolo nodo Proxmox con 1 TB SSD, 8 VM dev/staging; (b) 5 nodi Proxmox con 100 TB totali, target di RPO 5 min; (c) cluster a 3 nodi con archivio file 200 TB read-mostly; (d) lab solo 2 nodi senza storage condiviso. *Risposte:* (a) LVM-Thin o ZFS dataset; (b) Ceph RBD 3+1 replication; (c) CephFS o NFS centralizzato + qcow2; (d) ZFS replicato via `pve-zsync` (snapshot async).

2. **Lab — `zfs send | zfs receive` incrementale.** Su due nodi ZFS-based, eseguire: (a) snap source (`zfs snapshot tank/data@snap1`); (b) full send (`zfs send tank/data@snap1 | ssh target zfs receive backup/data`); (c) modify source; (d) new snap (`@snap2`); (e) incremental send (`zfs send -i @snap1 tank/data@snap2 | ssh target zfs receive backup/data`). Misurare bandwith reale.

3. **Scenario — datastore 50 TB su 1 GbE.** Hai 50 TB di dati su NFS source raggiungibile solo via 1 GbE. Stima realisticamente il tempo di copy iniziale e proponi 2 strategie alternative per accelerare. *Risposta:* a 1 GbE = ~100 MB/s effettivi → 50 TB = ~140 ore = ~6 giorni. Alternative: (a) shipping fisico (export su disco USB 18-22 TB, copia locale presso target); (b) sync su piu wave da gruppi piu piccoli per parallelizzare con piu giorni; (c) installare temporaneamente una connessione 10 GbE punto-a-punto fra source e target.

4. **Stretch — script orchestrator delta sync.** Scrivere uno script Python che, dato un file `vm-list.csv` con `vmid, source_path, target_path, size_gb`, esegue: (1) clone iniziale via rsync per ogni VM (parallel max 2); (2) loop di delta sync rsync ogni N minuti finche delta size < threshold; (3) trigger cutover (stop source, final sync, start target) per le VM con sync stabilizzato. Logging su `migration.log` con timestamps.

## Auto-valutazione

1. Tre criteri per scegliere fra LVM-Thin, ZFS, Ceph come backend Proxmox?
2. Differenza fra `qemu-img convert -O rbd` e `qemu-img convert -O raw - | rbd import`?
3. Quanto tempo serve trasferire 1 TB su 10 GbE in plain TCP vs SSH?
4. Cosa fa `zfs send -i @snap1 ds@snap2` e perche e veloce?
5. Quale tool serve per parallelizzare e saturare la banda su SSH transfer?
6. NIST 800-88 — i tre livelli di sanitization (Clear / Purge / Destroy)?
7. Cosa significa "snapshot replication source-side" e quale workflow segue?
8. Decommissioning datastore VMware — sequenza minima sicura?

## Letture primarie consigliate

- [`PVE-MIGRATE-V2V`] Proxmox VE Wiki — Migration of servers. https://pve.proxmox.com/wiki/Migration_of_servers_to_Proxmox_VE
- [`OPENZFS-MAN`] OpenZFS man pages (zfs send/receive). https://openzfs.github.io/openzfs-docs/man/master/index.html
- [`CEPH-DOCS`] Ceph — Block Devices (rbd). https://docs.ceph.com/en/latest/rbd/
- [`NIST-800-88`] NIST SP 800-88 — Media Sanitization. https://csrc.nist.gov/pubs/sp/800/88/r1/final
- mbuffer documentation. https://www.maier-komor.de/mbuffer.html
- pv (Pipe Viewer) — for ETA on transfers. https://www.ivarch.com/programs/pv.shtml
- VMware PowerCLI documentation. https://developer.vmware.com/powercli

## Collegamenti incrociati

- Modulo 03.1, 03.2 — `../03-STORAGE-AVANZATO-PROXMOX/`: backend storage.
- Modulo 08.1 — `conversione-vmdk-qcow2-raw.md`: tool conversione.
- Modulo 08.2 — `shared-storage-cutover-nfs-iscsi.md`: cutover NFS/iSCSI.
- Modulo 08.4 — `validazione-performance-storage.md`: validazione performance.
- Modulo 09.3 — `../09-SCENARI-MIGRAZIONE-SPECIFICI/migrazione-high-io-workloads.md`: applicazione a workload high-I/O.
- Modulo 11.1, 11.2 — `../11-BACKUP-E-RIPRISTINO-PROXMOX/`: backup post-migrazione.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Datastore (VMware)** | Oggetto di storage VMware (VMFS, NFS, vSAN). |
| **Storage backend (Proxmox)** | Implementazione fisica/logica dello storage (LVM, ZFS, NFS, Ceph...). |
| **Albero decisionale** | Flow chart per scegliere il backend giusto per workload e budget. |
| **`zfs send/receive`** | Comandi ZFS per replicare snapshot fra dataset. |
| **`pve-zsync`** | Tool Proxmox per replication ZFS asincrona fra nodi. |
| **Snapshot replication** | Replicazione asincrona basata su snapshot incrementali. |
| **`rsync --inplace --no-whole-file`** | Modalita rsync che fa update block-level invece di rewriting full file. |
| **`mbuffer`** | Buffer di memoria fra processi pipe; smussa traffico burst. |
| **`pigz`** | Parallel gzip — usa multi-thread per compressione. |
| **NIST 800-88 Clear** | Sanitization base: overwrite o reset (sufficiente per minaccia bassa). |
| **NIST 800-88 Purge** | Sanitization media: cryptographic erase, secure erase ATA, degaussing (per HDD). |
| **NIST 800-88 Destroy** | Distruzione fisica del media (shred, incinerate). |
| **Crypto-Erase** | Cancellazione tramite distruzione della chiave di encryption full-disk. |
| **Bandwidth budget** | Quantita di banda riservata alla migrazione, separata da traffic produzione. |
| **Network direct conversion** | `qemu-img convert -O rbd ...` o equivalente che scrive direttamente sul backend remoto. |
