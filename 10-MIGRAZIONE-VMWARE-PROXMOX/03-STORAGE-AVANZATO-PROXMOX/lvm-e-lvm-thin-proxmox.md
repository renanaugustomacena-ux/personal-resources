# LVM e LVM-Thin su Proxmox VE

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 1 — Fondamenti · Modulo 03.1 (vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 02.1 (architettura Proxmox, in particolare scelta storage in installer); LVM concettuale (PV/VG/LV); concetti di copy-on-write.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. distinguere LVM "classico" e LVM-Thin (thin provisioning) e ricavare le loro differenze su tre dimensioni: allocazione, snapshot, performance overhead;
> 2. creare un Volume Group e un Thin Pool su Proxmox via CLI (`pvcreate`, `vgcreate`, `lvcreate -T`) e via Web UI, registrando il backend in `/etc/pve/storage.cfg`;
> 3. interpretare lo stato di un Thin Pool (`Data%`, `Meta%`, allocation, fragmentation) e definire soglie di alert ragionevoli per produzione (default ~80% data, ~80% metadata);
> 4. eseguire snapshot LVM-Thin e capire perche con LVM "classico" gli snapshot sono possibili ma performance-fragili (CoW lineare, non recursive);
> 5. recuperare un Thin Pool quasi pieno o un Pool con metadata corrotti (procedura `--repair`, `lvconvert --repair`);
> 6. confrontare LVM/LVM-Thin con ZFS e Ceph e scegliere consapevolmente il backend per ogni use case (singolo nodo, cluster a 3 nodi, hyperconverged).
> **Tempo stimato:** lettura 60-90 min · lab 120-180 min
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-26
> **Versioni di riferimento:** Proxmox VE 8.x (lvm2 ≥ 2.03.x, kernel 6.x con dm-thin); per le novita di **PVE 9.x** sui snapshot LVM come volume chain, vedi callout «Approfondimento».

## Mappa concettuale

```
+======================================================+
|  LVM su Proxmox — gerarchia e cosa cambia con Thin   |
+======================================================+
|                                                      |
|  HARDWARE / RAID                                     |
|     /dev/sdb (HW RAID) o /dev/md0 (mdadm)            |
|         |                                            |
|         v                                            |
|  PHYSICAL VOLUME (PV)                                |
|     pvcreate /dev/sdb                                |
|         |                                            |
|         v                                            |
|  VOLUME GROUP (VG)                                   |
|     vgcreate pve-data /dev/sdb                       |
|         |                                            |
|         v                                            |
|  +-- LVM CLASSICO --------------------+              |
|  |  lvcreate -L 100G -n vm-100-disk pve-data        |
|  |  -> spazio prealloc, snapshot CoW lineare        |
|  |     fragili sotto carico, no over-commit         |
|  +---------------------------------------------+    |
|                                                      |
|  +-- LVM-THIN -----------------------+              |
|  |  lvcreate -L 1.8T -T pve-data/data              |
|  |  -> THIN POOL (data + metadata)                  |
|  |     |                                            |
|  |     +-- lvcreate -V 100G -T -n vm-100 ...        |
|  |     +-- lvcreate -V  50G -T -n vm-101 ...        |
|  |     -> volumi virtuali sopra il pool             |
|  |     -> snapshot O(1), thin clone, over-commit    |
|  +---------------------------------------------+    |
|                                                      |
|  REGISTRAZIONE PROXMOX                              |
|     /etc/pve/storage.cfg                             |
|       lvm:        local-lvm-old                      |
|       lvmthin:    local-lvm                          |
|                                                      |
+======================================================+
```

Idee guida del modulo:

1. **LVM classico funziona ma e per ambienti senza overcommit.** Allocazione spazio prealloc, snapshot CoW lineari = degrado prestazionale crescente con scritture (il "snapshot writeback" si fa serial sul base LV). Va benissimo per workload steady-state piccoli o per archiviazione, non per VM ad alto write con snapshot frequenti.
2. **LVM-Thin e il default per buon motivo.** Snapshot O(1), thin clone, over-commit dello storage. Trade-off: monitoring del Thin Pool e *obbligatorio* — se data o metadata si riempiono, il pool va in `out-of-data-space` e tutte le VM si bloccano. Lo strumento di emergenza e `lvextend` del pool, lo strumento di prevenzione e l'alerting su `Data%` / `Meta%`.
3. **Thin Pool metadata vanno dimensionati a parte.** Default 1% del data, ma in cluster con molti snapshot/clone si arriva a saturazione. `lvextend --poolmetadatasize +1G` e una manovra che si fa una volta in pre-prod, non in emergenza con il pool quasi pieno.
4. **LVM e backend a singolo nodo.** Per cluster condiviso, la combinazione "LVM su LUN condivisa" e l'unica forma "shared" ma *senza snapshot* e con locking SCSI delicato. Per cluster shared *con* snapshot, la scelta nativa Proxmox e Ceph RBD. ZFS non e shared, ma e replicabile via `pve-zsync` e snapshot incrementali.
5. **Migrazione VMDK su LVM-Thin: usare `qm importdisk`.** L'allocazione thin si attiva automaticamente. Lo "spazio occupato" iniziale corrisponde ai blocchi non-zero del VMDK; per ottimizzare, fare `fstrim -av` *dentro al guest* dopo l'import per liberare i blocchi unmappati.

## Indice

1. [Introduzione a LVM](#introduzione-a-lvm)
2. [Concetti Fondamentali: PV, VG, LV](#concetti-fondamentali-pv-vg-lv)
3. [Creazione LVM Storage su Proxmox](#creazione-lvm-storage-su-proxmox)
4. [LVM-Thin Provisioning](#lvm-thin-provisioning)
5. [Snapshot con LVM e LVM-Thin](#snapshot-con-lvm-e-lvm-thin)
6. [Comandi Operativi](#comandi-operativi)
7. [LVM su Proxmox: Configurazione Avanzata](#lvm-su-proxmox-configurazione-avanzata)
8. [Confronto: LVM vs LVM-Thin vs ZFS vs Ceph](#confronto-lvm-vs-lvm-thin-vs-zfs-vs-ceph)
9. [Scenari di Utilizzo](#scenari-di-utilizzo)
10. [Migrazione da VMware: Considerazioni LVM](#migrazione-da-vmware-considerazioni-lvm)
11. [Troubleshooting](#troubleshooting)

---

## Introduzione a LVM

**LVM** (Logical Volume Manager) è il sistema di gestione volumi logici standard di Linux. Su Proxmox VE, LVM rappresenta l'opzione storage più semplice e consolidata per lo storage locale delle VM, con una lunga storia di stabilità e affidabilità in ambienti di produzione.

Nel contesto di una migrazione da VMware a Proxmox, LVM è paragonabile ai concetti di VMFS datastore e disk groups, offrendo tuttavia una maggiore flessibilità nella gestione dello spazio disco.

### Perché LVM nella Migrazione da VMware

| Aspetto | VMware VMFS/vSAN | LVM/LVM-Thin Proxmox |
|---|---|---|
| Complessità | Media | Bassa |
| Overhead | Significativo | Minimo |
| Thin provisioning | Nativo (VMDK thin) | LVM-Thin |
| Snapshot | Nativo | LVM-Thin (non LVM standard) |
| Hardware RAID richiesto | Spesso sì | Opzionale (mdadm o hw RAID) |
| Licenze aggiuntive | Enterprise license | Nessuna |
| Curva di apprendimento | Media | Bassa (admin Linux standard) |

---

## Concetti Fondamentali: PV, VG, LV

### Architettura LVM

```
┌─────────────────────────────────────────────────────────────┐
│                      LVM Architecture                        │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                 Logical Volumes (LV)                    │  │
│  │                                                         │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │  │
│  │  │  lv-vm-100   │  │  lv-vm-101   │  │  lv-data     │  │  │
│  │  │   100 GB     │  │    50 GB     │  │   200 GB     │  │  │
│  │  │  (raw disk)  │  │  (raw disk)  │  │ (filesystem) │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │  │
│  └────────────────────────┬───────────────────────────────┘  │
│                           │                                  │
│  ┌────────────────────────▼───────────────────────────────┐  │
│  │              Volume Group (VG): pve                     │  │
│  │                                                         │  │
│  │  Spazio totale: 1.8 TB                                  │  │
│  │  Spazio usato:  350 GB                                  │  │
│  │  Spazio libero: 1.45 TB                                 │  │
│  │  PE size: 4 MB                                          │  │
│  └────────────────────────┬───────────────────────────────┘  │
│                           │                                  │
│  ┌────────────────────────▼───────────────────────────────┐  │
│  │            Physical Volumes (PV)                        │  │
│  │                                                         │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │  │
│  │  │   /dev/sda3  │  │   /dev/sdb   │  │   /dev/sdc   │  │  │
│  │  │   200 GB     │  │   800 GB     │  │   800 GB     │  │  │
│  │  │  (partition) │  │ (whole disk) │  │ (whole disk) │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│                     Physical Disks                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   /dev/sda   │  │   /dev/sdb   │  │   /dev/sdc   │       │
│  │   (240GB SSD)│  │  (800GB SSD) │  │  (800GB SSD) │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Physical Volume (PV)

Il **Physical Volume** è il livello base di LVM. Corrisponde a un disco fisico o una partizione preparata per l'uso con LVM:

```bash
# Inizializzare un disco come PV
pvcreate /dev/sdb
# Physical volume "/dev/sdb" successfully created.

# Inizializzare una partizione
pvcreate /dev/sda3

# Inizializzare più dischi contemporaneamente
pvcreate /dev/sd{b,c,d}

# Visualizzare informazioni sui PV
pvs
# PV         VG   Fmt  Attr PSize    PFree
# /dev/sda3  pve  lvm2 a--  199.00g  20.00g
# /dev/sdb   pve  lvm2 a--  799.87g  799.87g
# /dev/sdc        lvm2 ---  799.87g  799.87g

# Informazioni dettagliate
pvdisplay /dev/sdb
# --- Physical volume ---
# PV Name               /dev/sdb
# VG Name               pve
# PV Size               800.00 GiB / not usable 3.00 MiB
# Allocatable           yes
# PE Size               4.00 MiB
# Total PE              204799
# Free PE               204799
# Allocated PE          0
# PV UUID               abcdef-1234-5678-9abc-def012345678
```

### Volume Group (VG)

Il **Volume Group** aggrega uno o piu PV in un pool di spazio unificato:

```bash
# Creare un VG da uno o più PV
vgcreate vg-storage /dev/sdb /dev/sdc

# Visualizzare informazioni VG
vgs
# VG          #PV #LV #SN Attr   VSize   VFree
# pve           1   3   0 wz--n- 199.00g  20.00g
# vg-storage    2   0   0 wz--n-   1.56t   1.56t

# Informazioni dettagliate
vgdisplay vg-storage

# Estendere un VG con un nuovo disco
pvcreate /dev/sdd
vgextend vg-storage /dev/sdd

# Ridurre un VG (rimuovere un PV - SOLO se non contiene dati)
pvmove /dev/sdc    # Sposta dati da sdc ad altri PV
vgreduce vg-storage /dev/sdc
pvremove /dev/sdc

# Rinominare VG
vgrename vg-storage vg-vm-production
```

### Logical Volume (LV)

Il **Logical Volume** è il volume utilizzabile, equivalente a una partizione virtuale:

```bash
# Creare un LV di dimensione specifica
lvcreate -L 100G -n lv-vm-100 vg-storage

# Creare un LV che usa una percentuale dello spazio libero
lvcreate -l 50%FREE -n lv-data vg-storage

# Creare un LV che usa tutto lo spazio libero
lvcreate -l 100%FREE -n lv-remaining vg-storage

# Creare un LV con stripe (distribuzione su più PV per performance)
lvcreate -L 200G -n lv-fast -i 2 -I 64K vg-storage
# -i 2: stripe su 2 PV
# -I 64K: stripe size 64KB

# Visualizzare LV
lvs
# LV        VG          Attr       LSize   Pool Origin Data%
# lv-vm-100 vg-storage  -wi-a----- 100.00g
# lv-data   vg-storage  -wi-a----- 780.00g

# Informazioni dettagliate
lvdisplay vg-storage/lv-vm-100

# Ridimensionare un LV (espandere)
lvextend -L +50G vg-storage/lv-vm-100
# Oppure a dimensione specifica
lvextend -L 200G vg-storage/lv-vm-100
# Oppure percentuale
lvextend -l +100%FREE vg-storage/lv-vm-100

# Ridurre un LV (ATTENZIONE: ridurre PRIMA il filesystem!)
# Per ext4:
e2fsck -f /dev/vg-storage/lv-data
resize2fs /dev/vg-storage/lv-data 500G
lvreduce -L 500G vg-storage/lv-data

# Eliminare un LV
lvremove vg-storage/lv-vm-100

# Rinominare LV
lvrename vg-storage lv-vm-100 lv-vm-100-old
```

---

## Creazione LVM Storage su Proxmox

### Storage LVM Standard

L'installazione predefinita di Proxmox VE crea automaticamente un VG chiamato `pve` con un LV `data` (LVM-Thin) e `root`:

```bash
# Struttura default di Proxmox dopo installazione
lvs pve
# LV   VG  Attr       LSize   Pool Origin Data%
# data pve twi-a-t--- 150.00g             25.00
# root pve -wi-ao----  40.00g
# swap pve -wi-ao----   8.00g

# Aggiungere un nuovo LVM storage da CLI
pvesm add lvm lvm-storage \
    --vgname vg-storage \
    --content images,rootdir \
    --shared 0

# Dalla GUI: Datacenter → Storage → Add → LVM
# Parametri:
# - ID: nome identificativo
# - Volume Group: selezionare il VG
# - Content: images, rootdir
# - Shared: No (LVM standard è locale)
```

### Preparazione Dischi per Nuovo LVM Storage

```bash
# Scenario: aggiungere 4 SSD da 1TB per VM storage

# 1. Identificare i dischi
lsblk -d -o NAME,SIZE,MODEL,SERIAL
# sdb  1000G  Samsung 870 EVO  S5xxxx0001
# sdc  1000G  Samsung 870 EVO  S5xxxx0002
# sdd  1000G  Samsung 870 EVO  S5xxxx0003
# sde  1000G  Samsung 870 EVO  S5xxxx0004

# 2. Creare RAID (opzionale ma raccomandato)
# RAID10 con mdadm per massime performance + ridondanza
mdadm --create /dev/md0 --level=10 --raid-devices=4 /dev/sd{b,c,d,e}

# Attendere la sincronizzazione
cat /proc/mdstat
# md0 : active raid10 sde[3] sdd[2] sdc[1] sdb[0]
#       1953259520 blocks super 1.2 512K chunks 2 near-copies [4/4] [UUUU]
#       [=>...................]  resync =  5.2% finish=120.0min

# Salvare configurazione RAID
mdadm --detail --scan >> /etc/mdadm/mdadm.conf
update-initramfs -u

# 3. Creare PV, VG, LV
pvcreate /dev/md0
vgcreate vg-vm-storage /dev/md0

# 4. Aggiungere come storage Proxmox
pvesm add lvm vm-lvm-storage \
    --vgname vg-vm-storage \
    --content images,rootdir

# OPPURE senza RAID, usando LVM direttamente:
pvcreate /dev/sd{b,c,d,e}
vgcreate vg-vm-storage /dev/sd{b,c,d,e}
pvesm add lvm vm-lvm-storage \
    --vgname vg-vm-storage \
    --content images,rootdir
```

---

## LVM-Thin Provisioning

### Cos'è LVM-Thin

**LVM-Thin** (thin provisioning) separa la dimensione allocata dalla dimensione effettivamente utilizzata. Un thin LV di 100GB potrebbe occupare fisicamente solo 10GB se solo 10GB sono stati scritti:

```
┌─────────────────────────────────────────────────────────────┐
│              LVM Standard vs LVM-Thin                        │
│                                                              │
│  LVM STANDARD (Thick Provisioning):                          │
│  ┌──────────────────────┐                                    │
│  │  LV: vm-100 (100GB)  │  ← Allocati 100GB sul disco       │
│  │  ███████░░░░░░░░░░░░ │  ← Usati solo 30GB                │
│  │  30GB scritti         │  ← 70GB sprecati!                 │
│  └──────────────────────┘                                    │
│                                                              │
│  LVM-THIN (Thin Provisioning):                               │
│  ┌──────────────────────┐                                    │
│  │  LV: vm-100 (100GB)  │  ← "Promessi" 100GB alla VM       │
│  │  ███████              │  ← Solo 30GB occupati realmente   │
│  └──────────────────────┘                                    │
│  Thin Pool: [██████████░░░░░░░░░░░░░░░░░░░░░░░░]            │
│             30GB usati / 500GB pool totale                   │
│                                                              │
│  OVERCOMMIT possibile:                                       │
│  vm-100: 100GB allocati, 30GB usati                          │
│  vm-101: 100GB allocati, 25GB usati                          │
│  vm-102: 200GB allocati, 40GB usati                          │
│  vm-103: 200GB allocati, 55GB usati                          │
│  ─────────────────────────────────                           │
│  Totale allocato: 600GB (overcommit!)                        │
│  Totale reale:    150GB su 500GB pool                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Creare un Thin Pool

```bash
# Creare un thin pool dal VG
lvcreate -L 900G -T vg-storage/thin-pool
# -T: crea un thin pool
# LVM riserva automaticamente ~1% per i metadati

# Oppure specificare pool dati e metadati separatamente
lvcreate -L 895G -n tp-data vg-storage
lvcreate -L 5G -n tp-meta vg-storage
lvconvert --type thin-pool --poolmetadata vg-storage/tp-meta vg-storage/tp-data

# Creare thin LV dal thin pool
lvcreate -V 100G -T vg-storage/thin-pool -n vm-100-disk-0
lvcreate -V 200G -T vg-storage/thin-pool -n vm-101-disk-0
lvcreate -V 500G -T vg-storage/thin-pool -n vm-102-disk-0
# Totale allocato: 800GB da un pool di 900GB (è possibile overcommittare)

# Verificare thin pool
lvs -a vg-storage
# LV                VG          Attr       LSize   Pool      Origin Data%  Meta%
# thin-pool         vg-storage  twi-a-t--- 900.00g                  16.67   8.33
# vm-100-disk-0     vg-storage  Vwi-a-t--- 100.00g thin-pool        30.00
# vm-101-disk-0     vg-storage  Vwi-a-t--- 200.00g thin-pool        12.50
# vm-102-disk-0     vg-storage  Vwi-a-t--- 500.00g thin-pool         8.00

# Dettagli thin pool
lvs -o +lv_all vg-storage/thin-pool
```

### LVM-Thin su Proxmox

```bash
# Proxmox default LVM-Thin (creato durante installazione)
# VG: pve, Thin Pool: data

# Aggiungere un nuovo LVM-Thin storage
pvesm add lvmthin vm-thin-storage \
    --vgname vg-storage \
    --thinpool thin-pool \
    --content images,rootdir

# Dalla GUI: Datacenter → Storage → Add → LVM-Thin
# - ID: vm-thin-storage
# - Volume Group: vg-storage
# - Thin Pool: thin-pool
# - Content: Disk image, Container

# Verificare
pvesm status
# Name              Type      Status  Total       Used     Available  %
# local             dir       active  40G         8G       30G        22%
# local-lvm         lvmthin   active  150G        37G      112G       25%
# vm-thin-storage   lvmthin   active  900G        150G     750G       16%
```

### Monitoraggio Thin Pool

```bash
# Spazio reale utilizzato nel thin pool
lvs -o +lv_metadata_size,data_percent,metadata_percent vg-storage/thin-pool

# Monitoring continuo (importante per prevenire il riempimento!)
watch -n 10 'lvs -o lv_name,lv_size,data_percent,metadata_percent vg-storage/thin-pool'

# Configurare alert threshold
lvchange --monitor y vg-storage/thin-pool

# dmeventd monitora automaticamente i thin pool
# Threshold di default: 70% per warning
# Configurare in /etc/lvm/lvm.conf:
# thin_pool_autoextend_threshold = 80
# thin_pool_autoextend_percent = 20

# Espandere il thin pool se necessario
# Opzione 1: Aggiungere spazio dal VG
lvextend -L +100G vg-storage/thin-pool

# Opzione 2: Aggiungere un nuovo PV e estendere
pvcreate /dev/sdf
vgextend vg-storage /dev/sdf
lvextend -L +800G vg-storage/thin-pool

# Espandere i metadati (raramente necessario)
lvextend --poolmetadatasize +2G vg-storage/thin-pool
```

> **Attenzione critica:** Se un thin pool raggiunge il 100% di utilizzo, TUTTE le VM che lo usano andranno in errore I/O. Monitorare SEMPRE l'utilizzo reale del thin pool e configurare alert appropriati.

---

## Snapshot con LVM e LVM-Thin

### Snapshot LVM Standard

Gli snapshot LVM standard (thick) hanno limitazioni significative:

```bash
# Creare snapshot LVM thick (RICHIEDE spazio libero nel VG)
lvcreate -L 20G -s -n vm-100-snap vg-storage/vm-100-disk-0
# -s: snapshot
# -L 20G: spazio riservato per le modifiche (COW)

# Il COW space deve essere sufficiente per tutte le modifiche
# durante la vita dello snapshot, altrimenti lo snapshot diventa INVALIDO

# Verificare snapshot
lvs vg-storage
# LV            VG          Attr       LSize   Pool Origin         Data%
# vm-100-disk-0 vg-storage  owi-a-s--- 100.00g
# vm-100-snap   vg-storage  swi-a-s---  20.00g      vm-100-disk-0  15.00

# Merge (rollback) dello snapshot
lvconvert --merge vg-storage/vm-100-snap
# La VM deve essere spenta; il merge avviene al prossimo mount

# Eliminare snapshot
lvremove vg-storage/vm-100-snap
```

**Limitazioni snapshot LVM thick:**
- Degradano le performance (overhead COW su ogni scrittura al volume originale)
- Spazio fisso pre-allocato per le modifiche
- Se lo spazio snapshot si esaurisce, lo snapshot diventa invalido
- Solo un livello di snapshot (no catene)

### Snapshot LVM-Thin

Gli snapshot thin sono significativamente superiori:

```bash
# Creare snapshot thin (NON richiede spazio pre-allocato)
lvcreate -s -n vm-100-snap-20260324 vg-storage/vm-100-disk-0
# Per thin LV, non serve specificare -L (usa il thin pool)

# Vantaggi:
# - Zero overhead iniziale
# - Spazio consumato solo per le differenze effettive
# - Multiple snapshot senza impatto significativo
# - Snapshot di snapshot supportati

# Creare multiple snapshot
lvcreate -s -n vm-100-pre-upgrade vg-storage/vm-100-disk-0
lvcreate -s -n vm-100-post-upgrade vg-storage/vm-100-disk-0
lvcreate -s -n vm-100-pre-patch vg-storage/vm-100-disk-0

# Elencare snapshot thin
lvs -o lv_name,origin,lv_size,data_percent vg-storage | grep snap

# Ripristinare (merge)
lvconvert --merge vg-storage/vm-100-pre-upgrade

# Eliminare
lvremove vg-storage/vm-100-post-upgrade
```

### Snapshot in Proxmox

```bash
# Proxmox gestisce automaticamente gli snapshot LVM-Thin
# dalla GUI: VM → Snapshots → Take Snapshot

# Dalla CLI:
qm snapshot 100 pre-upgrade --description "Prima dell'aggiornamento OS"

# Elencare snapshot
qm listsnapshot 100

# Rollback
qm rollback 100 pre-upgrade

# Eliminare
qm delsnapshot 100 pre-upgrade
```

---

## Comandi Operativi

### Cheat Sheet Completo

```bash
# ═══════════════════════════════════════════════════
# PHYSICAL VOLUME (PV) Commands
# ═══════════════════════════════════════════════════

pvcreate /dev/sdX            # Inizializzare PV
pvremove /dev/sdX            # Rimuovere PV
pvs                          # Elenco PV breve
pvdisplay                    # Elenco PV dettagliato
pvscan                       # Scansione PV
pvmove /dev/sdX              # Migrare dati da un PV
pvresize /dev/sdX            # Ridimensionare PV
pvck /dev/sdX                # Check PV

# ═══════════════════════════════════════════════════
# VOLUME GROUP (VG) Commands
# ═══════════════════════════════════════════════════

vgcreate vg-name /dev/sdX    # Creare VG
vgremove vg-name             # Rimuovere VG
vgextend vg-name /dev/sdY    # Aggiungere PV al VG
vgreduce vg-name /dev/sdX    # Rimuovere PV dal VG
vgs                          # Elenco VG breve
vgdisplay                    # Elenco VG dettagliato
vgscan                       # Scansione VG
vgrename old-name new-name   # Rinominare VG
vgchange -a y vg-name        # Attivare VG
vgchange -a n vg-name        # Disattivare VG
vgck vg-name                 # Check VG

# ═══════════════════════════════════════════════════
# LOGICAL VOLUME (LV) Commands
# ═══════════════════════════════════════════════════

# Thick LV
lvcreate -L 100G -n lv-name vg-name         # Creare LV
lvremove vg-name/lv-name                      # Rimuovere LV
lvextend -L +50G vg-name/lv-name             # Espandere LV
lvreduce -L -20G vg-name/lv-name             # Ridurre LV
lvrename vg-name old-lv new-lv               # Rinominare
lvs                                           # Elenco breve
lvdisplay                                     # Elenco dettagliato

# Thin Pool
lvcreate -L 500G -T vg-name/pool-name        # Creare thin pool
lvextend -L +100G vg-name/pool-name           # Espandere thin pool

# Thin LV
lvcreate -V 100G -T vg-name/pool -n lv-name  # Creare thin LV
lvcreate -s -n snap-name vg-name/lv-name      # Snapshot thin

# Snapshot (thick)
lvcreate -L 10G -s -n snap vg-name/lv-name   # Creare snapshot
lvconvert --merge vg-name/snap                # Merge (rollback)
```

### Operazioni di Manutenzione

```bash
# Verificare integrità metadata LVM
vgck vg-storage
pvck /dev/sdb

# Backup metadata LVM (automatico, ma verificare)
ls /etc/lvm/backup/
ls /etc/lvm/archive/

# Ripristinare metadata LVM da backup
vgcfgrestore -f /etc/lvm/archive/vg-storage_00042.vg vg-storage

# Migrare dati tra PV (senza downtime per le VM)
pvmove /dev/sdb /dev/sdd
# Sposta tutti i dati da sdb a sdd, online

# Migrare solo LV specifici
pvmove -n vg-storage/vm-100-disk-0 /dev/sdb /dev/sdd

# Monitorare progresso pvmove
lvs -a -o +devices vg-storage

# TRIM/Discard per SSD
# Abilitare discard nel thin pool
lvchange --discards passdown vg-storage/thin-pool

# Eseguire TRIM manuale (fstrim su filesystem dentro LV)
fstrim -v /mountpoint

# Per LVM-Thin, il discard è gestito automaticamente
# quando le VM eseguono TRIM
```

---

## LVM su Proxmox: Configurazione Avanzata

### Configurazione /etc/lvm/lvm.conf

```bash
# Parametri chiave per Proxmox in /etc/lvm/lvm.conf

# Filtrare dispositivi (evitare che LVM scansioni dischi non desiderati)
# filter = [ "a|/dev/sd.*|", "a|/dev/md.*|", "r|.*|" ]

# Thin pool autoextend (espansione automatica)
# activation {
#     thin_pool_autoextend_threshold = 80
#     thin_pool_autoextend_percent = 20
#     monitoring = 1
# }

# Issue TRIM ai dispositivi sottostanti
# devices {
#     issue_discards = 1
# }

# Verificare la configurazione corrente
lvm dumpconfig activation/thin_pool_autoextend_threshold
lvm dumpconfig activation/thin_pool_autoextend_percent
```

### Multi-Path e LVM

Per storage SAN con multipath:

```bash
# Installare multipath-tools
apt install multipath-tools

# Configurare /etc/multipath.conf
# blacklist {
#     devnode "^sd[a-z]"   # Escludere dischi locali
# }
# devices {
#     device {
#         vendor  "NETAPP"
#         product "LUN.*"
#     }
# }

# Creare PV su device multipath
pvcreate /dev/mapper/mpathX

# LVM filtro per multipath
# filter = [ "a|/dev/mapper/mpath.*|", "a|/dev/sd[a]|", "r|.*|" ]
```

### LVM con LUKS (Encryption)

```bash
# Creare volume cifrato sotto LVM
cryptsetup luksFormat /dev/vg-storage/lv-encrypted
cryptsetup luksOpen /dev/vg-storage/lv-encrypted crypt-storage

# Usare il volume cifrato come PV per un nuovo VG
pvcreate /dev/mapper/crypt-storage
vgcreate vg-encrypted /dev/mapper/crypt-storage

# Auto-unlock al boot con keyfile
dd if=/dev/urandom of=/root/.keyfile bs=4096 count=1
chmod 0400 /root/.keyfile
cryptsetup luksAddKey /dev/vg-storage/lv-encrypted /root/.keyfile
# Aggiungere a /etc/crypttab:
# crypt-storage /dev/vg-storage/lv-encrypted /root/.keyfile luks
```

---

## Confronto: LVM vs LVM-Thin vs ZFS vs Ceph

### Tabella Comparativa Completa

| Funzionalità | LVM | LVM-Thin | ZFS | Ceph (RBD) |
|---|---|---|---|---|
| **Tipo** | Locale | Locale | Locale | Distribuito |
| **Thin Provisioning** | No | Si | Si (dataset) | Si |
| **Snapshot** | Limitati | Buoni | Eccellenti | Eccellenti |
| **Compressione** | No | No | Si (inline) | Si (inline) |
| **Deduplication** | No | No | Si (costosa) | No |
| **Checksum** | No | No | Si | Si |
| **RAID Software** | No (usa mdadm) | No (usa mdadm) | Si (nativo) | Si (replica) |
| **Live Migration** | No | No | No (usa replica) | Si |
| **Shared Storage** | No | No | No | Si |
| **RAM Overhead** | Minimo | Minimo | Alto (ARC) | Medio (OSD) |
| **CPU Overhead** | Minimo | Minimo | Medio | Medio |
| **Complessità** | Bassa | Bassa | Media | Alta |
| **Expand Online** | Si | Si | Si | Si |
| **Shrink Online** | Si | Si | No | No |
| **Max Scalabilità** | Singolo nodo | Singolo nodo | Singolo nodo | Multi-nodo |
| **Performance I/O** | Eccellente | Molto buona | Molto buona | Buona |
| **Maturità** | 20+ anni | 10+ anni | 15+ anni | 10+ anni |

### Performance a Confronto

| Metrica | LVM | LVM-Thin | ZFS (lz4) | Ceph RBD |
|---|---|---|---|---|
| IOPS random 4K read | 120K | 110K | 100K | 80K |
| IOPS random 4K write | 80K | 70K | 60K | 40K |
| Latenza write (P99) | 0.2ms | 0.3ms | 0.5ms | 1.0ms |
| Throughput seq. write | 1.2 GB/s | 1.1 GB/s | 1.0 GB/s | 800 MB/s |
| Overhead snapshot | 15-30% | 5-10% | < 1% | < 1% |

> **Nota:** Valori indicativi su SSD NVMe, singolo nodo. Le performance reali dipendono dal hardware e dal workload.

### Albero Decisionale

```
┌─────────────────────────────────────────┐
│  Quale storage scegliere per Proxmox?   │
└────────────────┬────────────────────────┘
                 │
         Serve HA/Live Migration?
         ┌───────┴────────┐
        Sì               No
         │                │
    Shared storage    Storage locale
    necessario            │
         │          ┌─────┴──────┐
    ┌────┴────┐   Budget/        Performance
    │         │   Semplicità?    prioritaria?
    │         │   ┌───┴────┐    ┌─────┴──────┐
   Ceph   NFS/   Sì      No    Sì           No
  (RBD)  iSCSI   │       │     │             │
                LVM-     ZFS   LVM         LVM-Thin
                Thin           (thick)     + ZFS per
                               + mdadm     backup
```

---

## Scenari di Utilizzo

### Scenario 1: Piccolo Cluster (3 nodi, budget limitato)

```bash
# Storage locale LVM-Thin per VM
# + ZFS Replication per HA

# Su ogni nodo:
# Disco OS: SSD 256GB (ext4/ZFS)
# VM Storage: 2x SSD 1TB in RAID1 (mdadm) → LVM-Thin

mdadm --create /dev/md0 --level=1 --raid-devices=2 /dev/sdb /dev/sdc
pvcreate /dev/md0
vgcreate vg-vms /dev/md0
lvcreate -l 95%FREE -T vg-vms/thin-pool

pvesm add lvmthin vm-storage \
    --vgname vg-vms \
    --thinpool thin-pool \
    --content images,rootdir
```

### Scenario 2: Cluster Medio (5-10 nodi, storage misto)

```bash
# Ceph per storage distribuito (VM live migration)
# LVM-Thin per storage locale ad alte prestazioni
# ZFS per backup locale con compressione

# LVM-Thin per VM ad alte prestazioni (locale)
# Su ogni nodo con NVMe locale:
pvcreate /dev/nvme0n1
vgcreate vg-fast /dev/nvme0n1
lvcreate -l 95%FREE -T vg-fast/thin-fast

pvesm add lvmthin fast-local \
    --vgname vg-fast \
    --thinpool thin-fast \
    --content images,rootdir
```

### Scenario 3: Sostituzione VMFS Thick con LVM

```bash
# VMware usava thick provisioning su VMFS
# Equivalente su Proxmox: LVM standard (thick)

# Per VM che richiedono performance garantite:
pvcreate /dev/sdb
vgcreate vg-thick /dev/sdb

pvesm add lvm thick-storage \
    --vgname vg-thick \
    --content images,rootdir

# Lo spazio viene allocato immediatamente (come VMDK thick)
# Nessun overcommit, nessun rischio di esaurimento thin pool
```

---

## Migrazione da VMware: Considerazioni LVM

### Importazione Dischi VM

```bash
# Dopo la conversione VMDK → raw (vedi guida conversione)

# Importare in LVM storage
qm importdisk 100 /tmp/vm-disk.raw vm-lvm-storage --format raw

# Importare in LVM-Thin storage
qm importdisk 100 /tmp/vm-disk.raw vm-thin-storage --format raw

# Il disco viene creato come LV nel VG/thin pool
# Verificare
lvs | grep vm-100

# Associare il disco alla VM
qm set 100 --scsi0 vm-thin-storage:vm-100-disk-0
```

### Confronto con VMware Storage Policies

| VMware Storage Policy | Equivalente LVM/Proxmox |
|---|---|
| Thick Eager Zeroed | LVM standard (thick) |
| Thick Lazy Zeroed | LVM standard (dati precedenti visibili) |
| Thin | LVM-Thin |
| Encryption | LVM + LUKS |
| FTT=1 (RAID1) | mdadm RAID1 + LVM |
| FTT=1 RAID5 | mdadm RAID5 + LVM |
| Stripe width | lvcreate -i (striping) |
| IOPS limit | cgroup v2 / IO scheduler |

---

## Troubleshooting

### Problemi Comuni

```bash
# Thin pool pieno
lvs -o lv_name,data_percent,metadata_percent vg-storage/thin-pool
# Se data_percent > 95%:
# 1. Espandere il thin pool
lvextend -L +100G vg-storage/thin-pool
# 2. Oppure eliminare snapshot non necessari
lvremove vg-storage/old-snapshot

# Thin pool metadata pieno
# CRITICO: se metadata_percent raggiunge 100%, il pool è compromesso
# Prevenzione:
lvextend --poolmetadatasize +2G vg-storage/thin-pool

# Riparare thin pool danneggiato
# 1. Disattivare
lvchange -an vg-storage/thin-pool
# 2. Riparare
lvconvert --repair vg-storage/thin-pool
# 3. Riattivare
lvchange -ay vg-storage/thin-pool

# PV mancante (disco rimosso/guasto)
vgs
# VG          #PV #LV #SN Attr   VSize   VFree
# vg-storage    2   5   0 wz--n-p 1.56t  400.00g   ← 'p' = partial (problema!)

# Se il PV è perso e i dati sono irrecuperabili:
vgreduce --removemissing vg-storage
# ATTENZIONE: i LV sul PV perso saranno eliminati

# LV non si attiva
lvchange -ay vg-storage/lv-name
# Se fallisce, verificare:
lvs -o +devices vg-storage/lv-name
dmsetup status

# Performance degradate con thin pool
# Verificare frammentazione
lvs -o lv_name,data_percent,metadata_percent,chunk_size vg-storage/thin-pool
# Verificare I/O del thin pool
iostat -x 1 | grep dm-

# Backup della configurazione LVM
vgcfgbackup vg-storage
# File salvato in /etc/lvm/backup/vg-storage
```

### Monitoring Script

```bash
#!/bin/bash
# /usr/local/bin/check-thin-pool.sh
# Monitoraggio thin pool con alert

THRESHOLD=80
VG="vg-storage"
POOL="thin-pool"

DATA_PCT=$(lvs --noheadings -o data_percent ${VG}/${POOL} | tr -d ' ')
META_PCT=$(lvs --noheadings -o metadata_percent ${VG}/${POOL} | tr -d ' ')

DATA_INT=${DATA_PCT%.*}
META_INT=${META_PCT%.*}

if [ "$DATA_INT" -gt "$THRESHOLD" ]; then
    echo "ALERT: Thin pool data usage at ${DATA_PCT}% (threshold: ${THRESHOLD}%)" | \
        mail -s "LVM Thin Pool Alert - $(hostname)" admin@domain.com
fi

if [ "$META_INT" -gt "$THRESHOLD" ]; then
    echo "CRITICAL: Thin pool METADATA at ${META_PCT}%!" | \
        mail -s "LVM Thin Pool METADATA Alert - $(hostname)" admin@domain.com
fi

# Cron: ogni 5 minuti
# */5 * * * * /usr/local/bin/check-thin-pool.sh
```

---

## Riferimenti

- [LVM Administrator Guide (Red Hat)](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/configuring_and_managing_logical_volumes/)
- [Proxmox VE Storage - LVM](https://pve.proxmox.com/wiki/Storage:_LVM)
- [Proxmox VE Storage - LVM-Thin](https://pve.proxmox.com/wiki/Storage:_LVM_Thin)
- [dm-thin Documentation (kernel.org)](https://www.kernel.org/doc/Documentation/device-mapper/thin-provisioning.txt)
- [LVM HOWTO](https://tldp.org/HOWTO/LVM-HOWTO/)

---

> **Prossimo:** [NFS e iSCSI - Storage Condiviso](nfs-iscsi-storage-condiviso.md) - Configurare storage di rete per Proxmox

---

## Approfondimenti — note del 2026-04-26

> **Approfondimento — LVM snapshot come volume chain in Proxmox VE 9.** Proxmox VE 9.x introduce gli snapshot LVM **come volume chain**: ogni snapshot e un LV separato che condivide blocchi con il padre via la mappa di `dm-thin`, anziche essere un overlay CoW lineare sopra il LV genitore (LVM classico) o vivere implicitamente nel thin pool (LVM-Thin pre-9). Conseguenza pratica: snapshot LVM "classico" diventano competitivi con LVM-Thin in performance, e in alcuni casi superiori per workload con scritture random pesanti, perche eliminano il vincolo "writeback serial" sul base LV. Per migrazioni nuove su PVE 9.x, valutare LVM "classico" + snapshot chain come alternativa a LVM-Thin se non serve il thin provisioning. Riferimento: [`PVE-STORAGE`] `https://pve.proxmox.com/wiki/Storage` e changelog PVE 9.

> **Errore comune — Thin Pool con data al 100%.** Sintomo: tutte le VM si bloccano con I/O error. `lvs` mostra `Data%: 100.00`. **Cosa NON fare:** spegnere VM in modo brutale (peggiora la frammentazione del metadata). **Cosa fare:** (a) estendere il VG aggiungendo un disco; (b) `lvextend -L+50G pve/data` (estende il pool); (c) verificare che le VM riprendano l'I/O; (d) impostare immediatamente alert su `Data%` con soglia 75% e `Meta%` con soglia 70%. Per pool di metadata sat: `lvextend --poolmetadatasize +1G pve/data` (se rimane spazio nel VG). In emergenza, se non c'e spazio nel VG, eliminare snapshot orfani (`lvremove pve/snap_*`) prima di tutto.

> **Caso reale — VG `pve` esteso a posteriori senza riallineare.** Un cluster Proxmox installato con il default 64-128 GB nel VG `pve` (su disco 1 TB) e poi mai esteso. La GUI segnala `local-lvm` quasi pieno con il disco fisico per il 90% libero. Causa: in fase di installazione, `hdsize` lasciato al default ha riservato solo una porzione del disco. Soluzione: `pvresize /dev/sdaN` poi `lvextend -L+800G pve/data --resizefs` (per LVM-Thin: `lvextend -L+800G pve/data && lvextend --poolmetadatasize +500M pve/data`). Lezione: in installazione lab, accettare il default; in installazione produzione, dimensionare `hdsize` a tutta la capacita del disco se non si riserva spazio per altri VG.

---

## Esercizi

1. **Concettuale — perche LVM snapshot classici degradano sotto carico?** Spiegare in 5-7 righe perche, su un LV con uno snapshot LVM classico attivo, ogni write al base LV richiede una copia del blocco originale al delta dello snapshot prima del write effettivo (CoW). Quanti I/O minimi richiede un singolo write 4 KB sul base LV con N snapshot attivi? *Risposta:* 1 read del blocco originale + N write a ciascun delta + 1 write al base LV = 2N+1 I/O minimo; con N=3 snapshot, un write 4 KB diventa 7 I/O. Per LVM-Thin il costo e ~costante (1 write al pool + lookup nel mapping table); per ZFS/qcow2 il costo e simile a thin (CoW non lineare).

2. **Lab — Thin Pool con monitoring e alert.** Sul lab Proxmox, creare un Thin Pool da 50 GB con metadata 1 GB. Creare 3 VM thin con 30 GB ciascuna (over-commit 80% del pool). Riempire le VM al 50% e verificare `Data%` con `lvs`. Configurare lo script di check fornito a fine modulo (sezione Comandi Operativi) come cron */5 e generare un alert simulato riempiendo una VM oltre soglia. *Verifica:* lo script invia mail solo quando `Data%` supera la soglia.

3. **Scenario — restore di una VM Windows da backup PBS su LVM-Thin saturo.** Pool al 90%, hai bisogno di restore di 200 GB di una VM critica (immagine compressa 80 GB). Argomenta in 12 righe: (a) sequenza per liberare spazio (eliminare snapshot orfani, verificare se ci sono `vm-NNN-disk-X` orfani senza VM associata via `qm config`), (b) eventuale estensione del pool, (c) restore con `qmrestore` su uno storage *diverso* (`local` o NFS) come fallback temporaneo. *Risposta attesa:* il fallback su storage diverso permette di avere subito la VM up, poi si fa `qm move_disk` quando il pool LVM-Thin e di nuovo sano.

4. **Stretch — LVM su LUN condivisa cluster-wide.** Costruire un piccolo lab a 2 nodi Proxmox + 1 target iSCSI (TrueNAS o simile). Creare una LUN da 100 GB, scoprirla dai 2 nodi, registrarla come storage `lvm` shared (non `lvmthin`) in `/etc/pve/storage.cfg`. Creare 2 VM su nodi diversi che usano questo storage. Documentare: (a) e possibile fare snapshot? (no — LVM classico shared non supporta snapshot via Proxmox); (b) e possibile migrazione live? (si, perche storage shared); (c) come si comporta con SCSI reservations? *Riferimento:* [`PVE-STORAGE`] e wiki "Storage: LVM Shared".

## Auto-valutazione

1. Differenza fra `pvcreate`, `vgcreate`, `lvcreate` — input e output di ciascuno.
2. Cosa contiene un Thin Pool (due aree distinte)?
3. Comando per verificare la percentuale data e metadata di un Thin Pool.
4. Differenza fra `lvcreate -L 100G` e `lvcreate -V 100G -T pool/...` — quale crea un thin volume?
5. Snapshot LVM classico vs LVM-Thin: quale ha overhead lineare e quale O(1)?
6. Cosa fa `discard=on` su un disco VM che vive su LVM-Thin (vs LVM classico)?
7. Come si recupera un Thin Pool con metadata corrotti (`lvconvert --repair`)?
8. Differenza fra `lvextend` semplice e `lvextend --resizefs` — quando l'una basta e quando serve l'altra?

## Letture primarie consigliate

- [`PVE-STORAGE`] Proxmox VE Wiki — Storage. https://pve.proxmox.com/wiki/Storage — sezioni "LVM" e "LVM-Thin".
- [`LVM2-MAN`] LVM2 manpages (Debian package `lvm2`). https://manpages.debian.org/bookworm/lvm2/
- [`LVM-LWN`] LVM-Thin overview (LWN.net, 2011). https://lwn.net/Articles/465740/
- Red Hat — Configuring and Managing Logical Volumes (RHEL 9). https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/configuring_and_managing_logical_volumes/
- Kernel doc — Device Mapper Thin Provisioning. https://www.kernel.org/doc/Documentation/device-mapper/thin-provisioning.txt
- LVM HOWTO (TLDP). https://tldp.org/HOWTO/LVM-HOWTO/

## Collegamenti incrociati

- Modulo 02.1 — `../02-FONDAMENTI-PROXMOX-VE/architettura-installazione-proxmox.md`: scelta storage backend in fase di installazione.
- Modulo 02.2 — `../02-FONDAMENTI-PROXMOX-VE/gestione-vm-container-proxmox.md`: assegnazione storage alle VM (`--scsi0 local-lvm:32,...`).
- Modulo 03.2 — `nfs-iscsi-storage-condiviso.md`: storage condiviso (NFS / iSCSI) come alternativa per cluster.
- Modulo 06.1, 06.2 — `../06-STRATEGIE-E-METODI-MIGRAZIONE/`: strategie di migrazione che usano LVM-Thin come destination.
- Modulo 08.1 — `../08-MIGRAZIONE-STORAGE/conversione-vmdk-qcow2-raw.md`: conversione VMDK → qcow2/raw con import in LVM-Thin.
- Modulo 17.4 — `../17-TROUBLESHOOTING-E-GUIDE-PRATICHE/troubleshooting-storage-performance.md`: troubleshooting performance storage post-migrazione.

## Glossario locale

| Termine | Definizione |
|---|---|
| **PV (Physical Volume)** | Disco fisico o partizione marcato per uso LVM. Creato con `pvcreate`. |
| **VG (Volume Group)** | Pool di PV uniti in un singolo namespace di allocazione. Creato con `vgcreate`. |
| **LV (Logical Volume)** | "Disco virtuale" allocato dentro un VG. Puo essere classico (prealloc), thin volume, o snapshot. |
| **LVM-Thin (Thin Pool)** | LV speciale (`-T`) che funge da pool dentro cui si creano thin volumes (`-V`). Permette over-commit. |
| **Thin volume** | LV virtuale dentro un Thin Pool; alloca blocchi solo quando scritti. |
| **Metadata LV** | LV interno al Thin Pool che mappa blocchi virtuali a blocchi fisici. Va dimensionato 1-2% del data. |
| **PE (Physical Extent)** | Unita minima di allocazione LVM (default 4 MB). |
| **dm-thin** | Modulo kernel device-mapper che implementa thin provisioning. |
| **CoW (Copy-on-Write)** | Tecnica di snapshot: il blocco originale e copiato al delta prima del write. |
| **`Data%` / `Meta%`** | Percentuali di utilizzo del Thin Pool, da `lvs` o `vgs`. Soglie alert tipiche 75/70. |
| **`fstrim` / discard** | Trim/UNMAP che libera blocchi non piu usati dal filesystem; per LVM-Thin riduce `Data%`. |
| **Snapshot chain (PVE 9)** | Nuova architettura di snapshot LVM in Proxmox VE 9.x: snapshot come LV separati condividenti blocchi via dm-thin. |
| **LVM shared** | Modalita storage cluster Proxmox: LVM classico su LUN iSCSI/FC condivisa; supporta migrazione live ma non snapshot. |
