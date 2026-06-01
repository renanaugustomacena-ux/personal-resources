# Storage Linux — Guida Completa

> **Modulo 06** · **Aggiornamento:** 2026-05-24

## Idee guida
1. **LVM thin pool: snapshot + thin provision; CoW perf cliff oltre 80% used.**
2. **ZFS degraded recovery: `zpool replace`, vdev replace ETA math.**
3. **Snapshot retention: ZFS auto via sanoid; LVM manual.**
4. **Scrub I/O impact: schedula in basso carico; `zpool scrub -s` per pause.**
5. **Block device stack: disco fisico → partizione → device-mapper → filesystem → VFS → userspace.**
6. **LUKS header backup: perdere l'header = perdere tutti i dati. `cryptsetup luksHeaderBackup` obbligatorio.**
7. **TRIM per SSD: senza TRIM periodico, write amplification degrada performance e longevità.**
8. **Ceph/Gluster: storage distribuito per scalabilità orizzontale; non sostituiscono RAID locale.**
9. **LVM VDO: deduplicazione e compressione inline a livello blocco; UDS index richiede minimo 250 MB RAM.**
10. **Stratis 3.x: gestione storage semplificata con pool, filesystem XFS e snapshot; non sostituto LVM per scenari avanzati.**
11. **bcachefs: filesystem CoW con checksum, cifratura e compressione nativi; rimosso dal kernel mainline 6.18, disponibile solo via DKMS.**
12. **NVMe-oF: accesso storage NVMe remoto via TCP/RDMA/FC; latenza sub-millisecondo su fabric RDMA.**
13. **dm-integrity: tag di integrità a livello blocco; combinabile con dm-crypt per cifratura autenticata (AEAD).**
14. **SSD health monitoring: `smartctl` per SATA, `nvme smart-log` per NVMe; TBW e percentage_used come indicatori chiave.**


## Indice

- [Panoramica](#panoramica)
- [Architettura dei Dispositivi a Blocchi](#architettura-dei-dispositivi-a-blocchi)
- [Identificazione e Diagnostica Dischi](#identificazione-e-diagnostica-dischi)
- [Tabelle delle Partizioni: MBR vs GPT](#tabelle-delle-partizioni-mbr-vs-gpt)
- [Partizionamento: fdisk, gdisk e parted](#partizionamento-fdisk-gdisk-e-parted)
- [Filesystem: ext4, XFS, Btrfs](#filesystem-ext4-xfs-btrfs)
- [LVM — Logical Volume Manager](#lvm--logical-volume-manager)
- [LVM VDO — Deduplicazione e Compressione](#lvm-vdo--deduplicazione-e-compressione)
- [Stratis 3.x — Gestione Storage Semplificata](#stratis-3x--gestione-storage-semplificata)
- [RAID Software (mdadm)](#raid-software-mdadm)
- [ZFS](#zfs)
- [Btrfs Avanzato](#btrfs-avanzato)
- [bcachefs — Filesystem Copy-on-Write di Nuova Generazione](#bcachefs--filesystem-copy-on-write-di-nuova-generazione)
- [iSCSI](#iscsi)
- [NVMe over Fabrics (NVMe-oF)](#nvme-over-fabrics-nvme-of)
- [NFS](#nfs)
- [Samba (Condivisione Windows)](#samba-condivisione-windows)
- [GlusterFS](#glusterfs)
- [Ceph — Nozioni Base](#ceph--nozioni-base)
- [Monitoraggio I/O Disco](#monitoraggio-io-disco)
- [Gestione SSD](#gestione-ssd)
- [SSD Health Monitoring Avanzato](#ssd-health-monitoring-avanzato)
- [Crittografia Disco — LUKS e dm-crypt](#crittografia-disco--luks-e-dm-crypt)
- [dm-integrity — Integrità a Livello Blocco](#dm-integrity--integrità-a-livello-blocco)
- [Quote Disco](#quote-disco)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## Panoramica

La gestione dello storage è una competenza critica per l'amministratore Linux. Copre tutto il percorso dalla preparazione fisica del disco (partizionamento) alla creazione del filesystem, dalla gestione logica dei volumi (LVM) alla ridondanza (RAID), fino alla condivisione in rete (NFS, Samba, iSCSI). Filesystem avanzati come ZFS e Btrfs aggiungono funzionalità enterprise come snapshot, compressione e self-healing.

Lo stack di storage Linux è stratificato: il kernel espone i dispositivi fisici come block device in `/dev`, il sottosistema device-mapper permette trasformazioni (LVM, dm-crypt, multipath), e il Virtual File System (VFS) astrae il filesystem specifico dall'accesso utente. Comprendere ogni strato è essenziale per diagnosi, performance tuning e architetture complesse.

---

## Architettura dei Dispositivi a Blocchi

### Lo Stack I/O del Kernel

```
 Applicazione utente
        │
        ▼
 VFS (Virtual File System)
        │
        ▼
 Filesystem (ext4, XFS, Btrfs, ZFS)
        │
        ▼
 Block Layer (I/O scheduler, merging, queue)
        │
        ▼
 Device-Mapper (LVM, dm-crypt, multipath)
        │
        ▼
 SCSI / NVMe / virtio subsystem
        │
        ▼
 Hardware (HDD, SSD, NVMe, disco virtuale)
```

### Device Node e Numerazione

Ogni dispositivo a blocchi in `/dev` è identificato da un **major number** (tipo di driver) e un **minor number** (istanza specifica).

```bash
# Visualizzare major/minor
ls -l /dev/sda /dev/sda1 /dev/nvme0n1
# brw-rw---- 1 root disk 8, 0 mag 22 10:00 /dev/sda       ← major 8, minor 0
# brw-rw---- 1 root disk 8, 1 mag 22 10:00 /dev/sda1      ← major 8, minor 1

# Major number comuni:
#   8   = SCSI/SATA (sd*)
#   259 = NVMe (nvme*)
#   253 = device-mapper (dm-*)
#   9   = md RAID (md*)
#   254 = virtio-blk

# Visualizzare tutti i block device con major/minor
cat /proc/devices | grep -i block
lsblk -o NAME,MAJ:MIN,SIZE,TYPE
```

### Naming Convention

| Prefisso | Tecnologia | Esempio |
|---|---|---|
| `sd` | SCSI, SATA, USB, SAS | `/dev/sda`, `/dev/sdb1` |
| `nvme` | NVMe (PCIe) | `/dev/nvme0n1`, `/dev/nvme0n1p1` |
| `vd` | Virtio (KVM/QEMU) | `/dev/vda`, `/dev/vda1` |
| `xvd` | Xen virtual | `/dev/xvda` |
| `hd` | IDE legacy | `/dev/hda` (rarissimo oggi) |
| `md` | RAID software | `/dev/md0`, `/dev/md127` |
| `dm-` | Device-mapper | `/dev/dm-0` (link da `/dev/mapper/`) |
| `loop` | Loop device | `/dev/loop0` |

### Il Sottosistema udev

udev gestisce la creazione dinamica dei device node e l'applicazione di regole personalizzate.

```bash
# Monitorare eventi udev in tempo reale
udevadm monitor --environment --kernel

# Interrogare un dispositivo
udevadm info --query=all --name=/dev/sda
udevadm info --attribute-walk --name=/dev/sda

# Le regole udev risiedono in:
# /lib/udev/rules.d/    ← regole di sistema (pacchetti)
# /etc/udev/rules.d/    ← regole personalizzate (priorità superiore)

# Esempio: regola per assegnare un nome persistente a un disco USB
# /etc/udev/rules.d/99-usb-storage.rules
# SUBSYSTEM=="block", ATTRS{serial}=="ABC123", SYMLINK+="disco_backup"
# Risultato: /dev/disco_backup → /dev/sdc (o qualsiasi assegnazione dinamica)

# Ricaricare le regole
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### sysfs — Informazioni dal Kernel

```bash
# Ogni block device espone attributi in /sys/block/
ls /sys/block/
# sda  sdb  nvme0n1  dm-0  md0 ...

# Scheduler I/O corrente
cat /sys/block/sda/queue/scheduler
# [mq-deadline] kyber bfq none

# Cambiare scheduler (temporaneo)
echo "bfq" | sudo tee /sys/block/sda/queue/scheduler

# Profondità coda I/O
cat /sys/block/sda/queue/nr_requests

# Dimensione settore logico/fisico
cat /sys/block/sda/queue/logical_block_size     # tipicamente 512
cat /sys/block/sda/queue/physical_block_size    # 512 o 4096 (Advanced Format)

# Disco rotazionale (1) o SSD (0)
cat /sys/block/sda/queue/rotational

# Supporto TRIM/discard
cat /sys/block/sda/queue/discard_max_bytes      # >0 = supportato
```

### Device-Mapper

Device-mapper è il framework kernel che realizza LVM, dm-crypt, dm-multipath e dm-raid.

```bash
# Visualizzare le mappature attive
sudo dmsetup ls
sudo dmsetup info
sudo dmsetup table                   # Tabella di mappatura per ogni device

# Relazione tra dm-X e nomi logici
ls -la /dev/mapper/

# Esempio output:
# vg_data-lv_app → ../dm-0
# vg_data-lv_home → ../dm-1
# luks-uuid → ../dm-2

# Statistiche I/O per device-mapper
sudo dmsetup status
```

---

## Identificazione e Diagnostica Dischi

### lsblk — Vista ad Albero

```bash
# Vista base
lsblk

# Vista completa con tutte le colonne utili
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,UUID,LABEL,MODEL,SERIAL,ROTA,DISC-MAX,TRAN

# Solo dischi (senza partizioni)
lsblk -d

# Output JSON (per scripting)
lsblk -J -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS

# Mostrare le relazioni di dipendenza
lsblk -t

# Visualizzare anche i dispositivi vuoti
lsblk -a

# Colonne utili:
# NAME       = nome dispositivo
# SIZE       = dimensione
# TYPE       = disk, part, lvm, raid, crypt, loop
# FSTYPE     = tipo filesystem (ext4, xfs, swap, LVM2_member, crypto_LUKS)
# MOUNTPOINT = punto di mount
# UUID       = identificatore univoco
# LABEL      = etichetta filesystem
# MODEL      = modello hardware
# SERIAL     = seriale disco
# ROTA       = 1=rotazionale (HDD), 0=solido (SSD)
# DISC-MAX   = max discard (TRIM) supportato
# TRAN       = trasporto (sata, nvme, usb, sas)
# HCTL       = Host:Channel:Target:Lun (SCSI address)
```

### blkid — Identificazione Filesystem

```bash
# Tutti i dispositivi con filesystem riconosciuto
sudo blkid

# Dispositivo specifico
sudo blkid /dev/sda1

# Solo UUID
sudo blkid -s UUID -o value /dev/sda1

# Solo tipo filesystem
sudo blkid -s TYPE -o value /dev/sda1

# Output completo con formato tag
sudo blkid -o full /dev/sda1
# /dev/sda1: UUID="a1b2c3d4-..." TYPE="ext4" PARTUUID="abc123-..." LABEL="root"

# Cercare per UUID
sudo blkid -U "a1b2c3d4-e5f6-..."

# Cercare per label
sudo blkid -L "dati"

# Forzare re-scan di tutti i dispositivi (cache può essere stale)
sudo blkid -g           # garbage collect cache
sudo blkid -p /dev/sda1 # probe senza cache
```

### smartctl — Diagnostica S.M.A.R.T.

S.M.A.R.T. (Self-Monitoring, Analysis and Reporting Technology) permette il monitoraggio proattivo della salute dei dischi.

```bash
# Installazione
sudo apt install smartmontools       # Debian/Ubuntu
sudo dnf install smartmontools       # Fedora/RHEL

# Informazioni complete
sudo smartctl -a /dev/sda

# Solo stato di salute
sudo smartctl -H /dev/sda
# PASSED = disco sano
# FAILED = sostituzione immediata!

# Attributi critici da monitorare:
# ID  Nome                    Pericolo se...
#  5  Reallocated_Sector_Ct   > 0 (settori riallocati)
#  9  Power_On_Hours          indicazione età
# 10  Spin_Retry_Count        > 0 (problemi meccanici)
# 187 Reported_Uncorrect      > 0 (errori non correggibili)
# 188 Command_Timeout         valore crescente
# 197 Current_Pending_Sector  > 0 (settori instabili)
# 198 Offline_Uncorrectable   > 0 (settori non recuperabili)

# Avviare test diagnostico
sudo smartctl -t short /dev/sda      # Test breve (~2 min)
sudo smartctl -t long /dev/sda       # Test completo (~ore)
sudo smartctl -t conveyance /dev/sda # Test post-trasporto

# Vedere risultati del test
sudo smartctl -l selftest /dev/sda

# Log errori
sudo smartctl -l error /dev/sda

# Per dischi NVMe
sudo smartctl -a /dev/nvme0n1

# Per dischi dietro controller RAID hardware
sudo smartctl -a /dev/sda -d megaraid,0
sudo smartctl -a /dev/sda -d cciss,0

# Abilitare il monitoraggio automatico (daemon)
sudo systemctl enable --now smartd

# Configurare smartd per alert email
# /etc/smartd.conf
# /dev/sda -a -o on -S on -s (S/../.././02|L/../../6/03) -m admin@example.com
# -s = schedule: Short test ogni giorno alle 02, Long test sabato alle 03
# -m = email per alert
```

### hdparm — Parametri e Benchmark Disco

```bash
# Informazioni dettagliate del disco
sudo hdparm -I /dev/sda

# Sezioni rilevanti nell'output:
# Model Number, Serial Number, Firmware Revision
# Transport: SATA 3.0 (6.0 Gb/s)
# Commands/features:
#   SMART, NCQ, TRIM, Write cache

# Benchmark lettura sequenziale (buffered)
sudo hdparm -tT /dev/sda
# /dev/sda:
#  Timing cached reads:   20000 MB in  2.00 seconds = 10000.00 MB/sec  ← cache CPU
#  Timing buffered disk reads: 600 MB in  3.01 seconds = 199.34 MB/sec ← disco reale

# Verificare stato write cache
sudo hdparm -W /dev/sda
# /dev/sda: write-caching = 1 (on)

# Disabilitare write cache (per sicurezza dati, penalizza performance)
sudo hdparm -W 0 /dev/sda

# Verificare supporto TRIM
sudo hdparm -I /dev/sda | grep -i trim

# Stato Advanced Power Management
sudo hdparm -B /dev/sda
# 1-127 = modalità risparmio energetico attiva
# 128-254 = performance
# 255 = APM disabilitato

# Verificare stato Acoustic Management
sudo hdparm -M /dev/sda

# Per NVMe usare nvme-cli (hdparm non è compatibile con NVMe)
sudo apt install nvme-cli
sudo nvme list                        # Lista dispositivi NVMe
sudo nvme id-ctrl /dev/nvme0n1       # Informazioni controller
sudo nvme id-ns /dev/nvme0n1 -n 1   # Informazioni namespace
sudo nvme smart-log /dev/nvme0n1     # Log SMART
sudo nvme error-log /dev/nvme0n1     # Log errori
```

---

## Tabelle delle Partizioni: MBR vs GPT

### Confronto Approfondito

| Aspetto | MBR (DOS) | GPT (GUID) |
|---|---|---|
| Max dimensione disco | 2 TB | 9.4 ZB |
| Max partizioni | 4 primarie (o 3+1 estesa) | 128 (modificabile) |
| Boot | BIOS | UEFI (e BIOS con grub-pc) |
| Ridondanza tabella | No | Sì (copia primaria e backup a fine disco) |
| Checksum | No | CRC32 su header e tabella |
| Dimensione indirizzo | 32 bit (LBA) | 64 bit (LBA) |
| Protective MBR | N/A | Presente (compatibilità con tool vecchi) |
| Tipo partizione | Byte singolo (0x83=Linux, 0x82=swap) | GUID 128 bit |
| Posizione tabella | Settore 0 (primo settore disco) | LBA 1 (con backup a fine disco) |
| Uso consigliato | Legacy, dischi < 2TB, BIOS | Standard moderno, UEFI |

### Struttura MBR

```
Settore 0 (512 byte):
├── Bootloader code     (446 byte)
├── Partition table      (64 byte = 4 entry × 16 byte)
└── Boot signature       (2 byte: 0x55AA)

Limiti:
- 4 entry = max 4 partizioni primarie
- Workaround: 3 primarie + 1 estesa (che contiene partizioni logiche)
- Indirizzo LBA a 32 bit: max 2^32 × 512 byte = 2 TiB
```

### Struttura GPT

```
LBA 0:  Protective MBR (compatibilità)
LBA 1:  GPT Header (versione, CRC32, GUID disco, puntatori)
LBA 2-33:  Partition Entry Array (128 entry × 128 byte)
...
LBA -33 a -2:  Backup Partition Entry Array
LBA -1:  Backup GPT Header

Ogni entry contiene:
- Partition Type GUID (es. EBD0A0A2-... = Microsoft Basic Data)
- Unique Partition GUID
- First LBA / Last LBA
- Attributes (bit 0 = richiesta dalla piattaforma, bit 2 = legacy BIOS bootable)
- Name (UTF-16, max 36 caratteri)
```

### GUID Tipo Partizione Comuni

| GUID | Tipo |
|---|---|
| `C12A7328-F81F-...` | EFI System Partition (ESP) |
| `0FC63DAF-8483-...` | Linux filesystem |
| `0657FD6D-A4AB-...` | Linux swap |
| `E6D6D379-F507-...` | Linux LVM |
| `A19D880F-05FC-...` | Linux RAID |
| `EBD0A0A2-B9E5-...` | Microsoft basic data |
| `DE94BBA4-06D1-...` | Microsoft reserved |

### Conversione tra MBR e GPT

```bash
# Da MBR a GPT con gdisk (non distruttivo se c'è spazio)
sudo gdisk /dev/sdb
# w → scrivi tabella GPT

# Da MBR a GPT con sgdisk
sudo sgdisk -g /dev/sdb

# Verificare la tabella corrente
sudo fdisk -l /dev/sdb | head -5
# Disklabel type: gpt   ← o "dos" per MBR

# Da GPT a MBR (attenzione: si perdono partizioni > 4)
sudo sgdisk -m 1:2:3:4 /dev/sdb   # Converte le partizioni 1-4 a MBR

# Ripristinare backup GPT header (se l'header primario è corrotto)
sudo gdisk /dev/sdb
# r → recovery
# b → use backup GPT header
# w → scrivi
```

---

## Partizionamento: fdisk, gdisk e parted

### fdisk (MBR e GPT)

```bash
# Visualizzare le partizioni
sudo fdisk -l                      # Tutti i dischi
sudo fdisk -l /dev/sda             # Disco specifico

# Partizionare (interattivo)
sudo fdisk /dev/sdb
# Comandi interattivi:
#   g → crea nuova tabella GPT
#   o → crea nuova tabella MBR
#   n → nuova partizione
#   d → elimina partizione
#   t → cambia tipo partizione
#   p → stampa tabella corrente
#   w → scrivi modifiche ed esci
#   q → esci senza salvare

# lsblk — vista ad albero dei dispositivi a blocchi
lsblk                              # Albero dispositivi
lsblk -f                           # Con filesystem e UUID
lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINT,UUID
```

### gdisk (GPT nativo)

gdisk è lo strumento specializzato per tabelle GPT, con funzionalità di recovery e conversione.

```bash
# Partizionamento interattivo GPT
sudo gdisk /dev/sdb
# Comandi interattivi:
#   o → nuova tabella GPT vuota
#   n → nuova partizione
#   d → elimina partizione
#   t → cambia tipo partizione (usa codici hex GPT, es. 8300=Linux, 8200=swap)
#   p → stampa tabella corrente
#   i → info dettagliata su una partizione
#   l → lista tipi partizione disponibili
#   c → cambia nome partizione
#   w → scrivi ed esci
#   q → esci senza salvare
#   r → menu recovery e trasformazione
#   x → menu extra funzionalità

# Menu recovery (r):
#   b → usa backup GPT header
#   c → carica backup partition table
#   d → usa header primario
#   e → carica main partition table
#   f → carica tabella MBR e costruisci GPT
#   g → converti GPT a MBR (perde partizioni > 4)
#   h → crea hybrid MBR (dual boot BIOS+UEFI)

# sgdisk — gdisk non-interattivo (per script)
# Creare tabella GPT con 3 partizioni
sudo sgdisk --zap-all /dev/sdb                          # Azzerare tabella
sudo sgdisk -n 1:0:+512M -t 1:EF00 /dev/sdb           # ESP (EFI System)
sudo sgdisk -n 2:0:+4G -t 2:8200 /dev/sdb             # Linux swap
sudo sgdisk -n 3:0:0 -t 3:8300 /dev/sdb               # Linux filesystem (tutto il resto)

# Clonare tabella partizioni da un disco a un altro
sudo sgdisk -R /dev/sdc /dev/sdb       # Copia tabella sdb → sdc
sudo sgdisk -G /dev/sdc                # Rigenera GUID unici su sdc

# Backup/restore tabella partizioni
sudo sgdisk --backup=sdb_table.bak /dev/sdb
sudo sgdisk --load-backup=sdb_table.bak /dev/sdb

# Verificare allineamento partizioni (importante per SSD e Advanced Format)
sudo sgdisk -v /dev/sdb
# Ogni partizione dovrebbe iniziare a un multiplo di 2048 settori (1 MiB)
```

### parted (MBR e GPT)

```bash
# Visualizzare
sudo parted -l                     # Tutti i dischi

# Interattivo
sudo parted /dev/sdb

# Non-interattivo
sudo parted /dev/sdb mklabel gpt
sudo parted /dev/sdb mkpart primary ext4 0% 100%    # Intera partizione
sudo parted /dev/sdb mkpart primary ext4 1MiB 50%   # Prima metà
sudo parted /dev/sdb mkpart primary ext4 50% 100%   # Seconda metà
sudo parted /dev/sdb set 1 boot on                   # Flag boot

# Ridimensionare
sudo parted /dev/sdb resizepart 1 100%

# Allineamento ottimale (parted lo fa di default con %)
sudo parted /dev/sdb align-check optimal 1
# 1 aligned  ← OK

# Stampare in formato machine-readable (per script)
sudo parted -m /dev/sdb print
```

### Creare Filesystem

```bash
# ext4 (più diffuso)
sudo mkfs.ext4 /dev/sdb1
sudo mkfs.ext4 -L "dati" /dev/sdb1              # Con label
sudo mkfs.ext4 -m 1 /dev/sdb1                   # 1% riservato (default 5%)
sudo mkfs.ext4 -T largefile /dev/sdb1            # Pochi inode, file grandi
sudo mkfs.ext4 -O ^has_journal /dev/sdb1         # Senza journal (solo uso specifico!)
sudo mkfs.ext4 -b 4096 -i 16384 /dev/sdb1       # Block size 4k, bytes/inode ratio
sudo mkfs.ext4 -E stride=128,stripe-width=512 /dev/sdb1  # Allineamento per RAID

# XFS
sudo mkfs.xfs /dev/sdb1
sudo mkfs.xfs -L "dati" /dev/sdb1
sudo mkfs.xfs -f /dev/sdb1                      # Forza (sovrascrivere)
sudo mkfs.xfs -d su=256k,sw=3 /dev/sdb1         # Stripe unit/width per RAID

# Btrfs
sudo mkfs.btrfs /dev/sdb1
sudo mkfs.btrfs -L "dati" /dev/sdb1
sudo mkfs.btrfs -f /dev/sdb1                    # Forza
sudo mkfs.btrfs -m raid1 -d raid1 /dev/sdb /dev/sdc  # RAID 1 su 2 dischi

# Swap
sudo mkswap /dev/sdb2
sudo swapon /dev/sdb2

# Verificare
blkid /dev/sdb1                    # UUID, tipo, label
```

### Filesystem Tuning

```bash
# === tune2fs — tuning ext4 ===
sudo tune2fs -l /dev/sda1                   # Info filesystem
sudo tune2fs -m 1 /dev/sda1                 # Riduci spazio riservato a 1%
sudo tune2fs -L "mydata" /dev/sda1          # Cambia label
sudo tune2fs -c 30 /dev/sda1               # Check ogni 30 mount
sudo tune2fs -i 180d /dev/sda1             # Check ogni 180 giorni
sudo tune2fs -c 0 -i 0 /dev/sda1           # Disabilita check automatici
sudo tune2fs -o journal_data_writeback /dev/sda1  # Modalità journal (più veloce, meno sicuro)
sudo tune2fs -O ^has_journal /dev/sda1      # Rimuovi journal (pericoloso)
sudo tune2fs -O has_journal /dev/sda1       # Riaggiungi journal
sudo tune2fs -U random /dev/sda1            # Genera nuovo UUID
sudo tune2fs -e remount-ro /dev/sda1        # Su errore: rimonta read-only

# === xfs_admin — tuning XFS ===
sudo xfs_admin -l /dev/sda1                 # Mostra label
sudo xfs_admin -L "mydata" /dev/sda1        # Imposta label
sudo xfs_admin -u /dev/sda1                 # Mostra UUID
sudo xfs_admin -U generate /dev/sda1        # Genera nuovo UUID

# === Opzioni mount per performance ===
# ext4:  noatime,commit=60,data=writeback,barrier=0
# XFS:   noatime,logbufs=8,logbsize=256k,allocsize=64m
# Btrfs: noatime,compress=zstd:3,space_cache=v2,ssd
```

### Mount e fstab

```bash
# Mount manuale
sudo mount /dev/sdb1 /mnt/dati
sudo mount -t ext4 /dev/sdb1 /mnt/dati
sudo mount -o ro,noexec /dev/sdb1 /mnt/dati     # Read-only, no exec
sudo umount /mnt/dati

# Mount per UUID (più affidabile di /dev/sdX)
sudo mount UUID="abc123-def456" /mnt/dati

# /etc/fstab — mount persistente al boot
# <device>                                <mount>      <type> <options>          <dump> <pass>
UUID=abc123-def456-789                     /mnt/dati    ext4   defaults           0      2
UUID=def789-abc123-456                     /mnt/backup  xfs    defaults,noatime   0      2
UUID=swap-uuid                             none         swap   sw                 0      0
//server/share                             /mnt/share   cifs   credentials=/etc/samba/creds,uid=1000  0  0
server:/export                             /mnt/nfs     nfs    defaults,_netdev   0      0

# Opzioni mount comuni:
# defaults    = rw, suid, dev, exec, auto, nouser, async
# noatime     = non aggiornare access time (performance)
# noexec      = non permettere esecuzione binari
# nosuid      = ignorare bit suid
# ro          = read-only
# _netdev     = aspettare la rete prima di montare
# nofail      = non bloccare il boot se il device manca
# x-systemd.automount = mount on-demand (systemd)

# Validare fstab senza riavviare
sudo mount -a                      # Monta tutto ciò che non è montato
sudo findmnt --verify              # Verifica sintassi fstab

# findmnt — visualizzazione avanzata dei mount
findmnt                            # Albero di tutti i mount
findmnt -t ext4                    # Solo ext4
findmnt --fstab                    # Cosa è definito in fstab
findmnt -S UUID=abc123...          # Cerca per sorgente
```

---

## Filesystem: ext4, XFS, Btrfs

### Confronto

| Aspetto | ext4 | XFS | Btrfs |
|---|---|---|---|
| Uso tipico | Generale, boot | File grandi, server | Desktop, snapshot |
| Max volume | 1 EB | 8 EB | 16 EB |
| Max file | 16 TB | 8 EB | 16 EB |
| Ridimensionamento | Grow + shrink | Solo grow | Grow + shrink |
| Snapshot | No | No | Sì (nativo) |
| Compressione | No | No | Sì (zstd, lzo) |
| RAID nativo | No | No | Sì |
| Copy-on-Write | No | No | Sì |
| Deduplicazione | No | No | Sì (offline) |
| Checksum dati | No (solo metadati) | No (solo metadati) | Sì |
| Self-healing | No | No | Sì (con RAID) |
| Maturità | Molto stabile | Molto stabile | Stabile (migliorando) |

### Operazioni ext4

```bash
# Informazioni
sudo tune2fs -l /dev/sda1          # Info dettagliate
sudo dumpe2fs /dev/sda1            # Dump completo

# Modifica parametri
sudo tune2fs -m 1 /dev/sda1       # Riduci spazio riservato a 1%
sudo tune2fs -L "mydata" /dev/sda1 # Cambia label
sudo tune2fs -c 30 /dev/sda1      # Check ogni 30 mount
sudo tune2fs -i 180d /dev/sda1    # Check ogni 180 giorni

# Controllo e riparazione (filesystem smontato!)
sudo e2fsck -f /dev/sda1          # Forza check
sudo e2fsck -p /dev/sda1          # Auto-repair
sudo e2fsck -y /dev/sda1          # Sì a tutto

# Ridimensionamento
sudo resize2fs /dev/sda1           # Espandi al massimo
sudo resize2fs /dev/sda1 50G      # Ridimensiona a 50GB
```

### Operazioni XFS

```bash
# Informazioni
xfs_info /dev/sda1                 # Info filesystem
xfs_info /mnt/dati                 # Anche per mount point

# Riparazione
sudo xfs_repair /dev/sda1         # Ripara (smontato)
sudo xfs_repair -L /dev/sda1      # Forza riparazione log

# Crescita (solo online, solo expand)
sudo xfs_growfs /mnt/dati         # Espandi al massimo

# Defrag (online)
sudo xfs_fsr /mnt/dati            # Defrag
sudo xfs_fsr -v /mnt/dati         # Verbose

# Backup/restore
sudo xfsdump -l 0 -f /backup/dati.dump /mnt/dati
sudo xfsrestore -f /backup/dati.dump /mnt/restore

# Tuning avanzato XFS
sudo xfs_admin -L "mydata" /dev/sda1       # Imposta label
sudo xfs_admin -U generate /dev/sda1       # Genera nuovo UUID
```

---

## LVM — Logical Volume Manager

LVM aggiunge un layer di astrazione tra i dischi fisici e i filesystem, permettendo ridimensionamento, snapshot e gestione flessibile dello storage.

### Concetti

```
Disco fisico (/dev/sdb)
  → Physical Volume (PV): disco o partizione preparato per LVM
    → Volume Group (VG): pool di storage formato da uno o più PV
      → Logical Volume (LV): "partizione virtuale" su cui creare il filesystem
```

### Operazioni Base

```bash
# PHYSICAL VOLUME
sudo pvcreate /dev/sdb /dev/sdc    # Inizializza dischi come PV
sudo pvs                            # Lista breve PV
sudo pvdisplay                      # Dettaglio PV
sudo pvremove /dev/sdc              # Rimuovi PV

# VOLUME GROUP
sudo vgcreate vg_data /dev/sdb /dev/sdc  # Crea VG da più PV
sudo vgs                            # Lista breve VG
sudo vgdisplay vg_data              # Dettaglio VG
sudo vgextend vg_data /dev/sdd     # Aggiungi disco al VG
sudo vgreduce vg_data /dev/sdc     # Rimuovi disco dal VG

# LOGICAL VOLUME
sudo lvcreate -L 50G -n lv_app vg_data       # LV da 50GB
sudo lvcreate -l 100%FREE -n lv_data vg_data # Tutto lo spazio libero
sudo lvcreate -l 50%VG -n lv_app vg_data     # 50% del VG
sudo lvs                            # Lista breve LV
sudo lvdisplay                      # Dettaglio LV

# Creare filesystem
sudo mkfs.ext4 /dev/vg_data/lv_app
sudo mount /dev/vg_data/lv_app /mnt/app

# In fstab: usare il path /dev/vg_data/lv_app o UUID
```

### Ciclo di Vita Completo PV/VG/LV

```bash
# === FASE 1: Preparazione ===
# Partizionare il disco con tipo LVM (opzionale ma consigliato)
sudo fdisk /dev/sdb    # → n, t, 8e (Linux LVM), w
# Oppure usare il disco intero senza partizioni
sudo pvcreate /dev/sdb

# === FASE 2: Pool di Storage ===
sudo vgcreate -s 32M vg_prod /dev/sdb /dev/sdc   # -s = PE size (default 4M)
# PE size più grande = meno overhead, max LV size maggiore
# PE size 4M  → max LV = 256 GiB × PE
# PE size 32M → max LV = 2 TiB × PE

# === FASE 3: Volumi Logici ===
sudo lvcreate -L 100G -n lv_db vg_prod
sudo lvcreate -L 50G -n lv_app vg_prod
sudo lvcreate -l 100%FREE -n lv_logs vg_prod

# === FASE 4: Filesystem e Mount ===
sudo mkfs.xfs /dev/vg_prod/lv_db
sudo mkfs.ext4 /dev/vg_prod/lv_app
sudo mkfs.ext4 /dev/vg_prod/lv_logs
# Aggiungere entry in /etc/fstab

# === FASE 5: Migrazione PV (spostare dati da un disco a un altro) ===
sudo pvmove /dev/sdb /dev/sdd      # Sposta tutti i PE da sdb a sdd
sudo pvmove -n lv_db /dev/sdb      # Sposta solo il LV specificato
sudo vgreduce vg_prod /dev/sdb     # Rimuovi PV vuoto dal VG
sudo pvremove /dev/sdb             # Pulisci metadati LVM dal disco

# === FASE 6: Rimozione ===
sudo umount /dev/vg_prod/lv_db
sudo lvremove /dev/vg_prod/lv_db
sudo vgremove vg_prod              # Rimuove VG (tutti i LV devono essere rimossi)
sudo pvremove /dev/sdb /dev/sdc    # Pulisci PV

# === Diagnostica LVM ===
sudo pvs -o +pv_used,pv_free       # Spazio usato/libero per PV
sudo vgs -o +vg_free,lv_count      # Spazio libero e numero LV per VG
sudo lvs -o +lv_size,data_percent,snap_percent  # Dettagli LV
sudo lvmdiskscan                    # Scansione tutti i dischi per LVM
```

### Ridimensionamento LVM

```bash
# ESPANDERE un LV + filesystem
sudo lvextend -L +20G /dev/vg_data/lv_app       # +20GB
sudo lvextend -l +100%FREE /dev/vg_data/lv_app   # Tutto lo spazio libero
sudo resize2fs /dev/vg_data/lv_app                # Espandi ext4
# Per XFS: sudo xfs_growfs /mnt/app

# Tutto in un comando
sudo lvextend -r -L +20G /dev/vg_data/lv_app    # -r = resize filesystem

# RIDURRE un LV + filesystem (solo ext4, NON XFS)
sudo umount /mnt/app
sudo e2fsck -f /dev/vg_data/lv_app
sudo resize2fs /dev/vg_data/lv_app 30G           # Riduci FS a 30GB
sudo lvreduce -L 30G /dev/vg_data/lv_app         # Riduci LV a 30GB
sudo mount /dev/vg_data/lv_app /mnt/app
```

### Snapshot LVM

```bash
# Creare snapshot (classico, copy-on-write)
sudo lvcreate -s -L 5G -n snap_app /dev/vg_data/lv_app

# Lo snapshot è montabile
sudo mount -o ro /dev/vg_data/snap_app /mnt/snapshot

# Ripristinare da snapshot
sudo umount /mnt/app
sudo lvconvert --merge /dev/vg_data/snap_app
sudo mount /dev/vg_data/lv_app /mnt/app

# Rimuovere snapshot
sudo lvremove /dev/vg_data/snap_app
```

### Thin Provisioning

```bash
# Thin pool: permette overcommit dello storage
sudo lvcreate -T -L 100G vg_data/thinpool

# Creare thin pool con metadata separato (produzione)
sudo lvcreate -L 100G -n thinpool_data vg_data
sudo lvcreate -L 1G -n thinpool_meta vg_data     # ~1% del data, min 2MiB
sudo lvconvert --type thin-pool \
  --poolmetadata vg_data/thinpool_meta \
  vg_data/thinpool_data

# Thin volume: usa spazio dal thin pool solo quando scritto
sudo lvcreate -V 500G -T vg_data/thinpool -n thin_vol1
sudo lvcreate -V 500G -T vg_data/thinpool -n thin_vol2
# 1TB allocata "virtualmente" ma solo 100GB disponibili fisicamente

# Thin snapshot (quasi istantanei, poco spazio)
sudo lvcreate -s -n thin_snap /dev/vg_data/thin_vol1

# Monitorare l'uso effettivo
sudo lvs -o +data_percent
sudo lvs -o lv_name,lv_size,data_percent,pool_lv vg_data

# Autoextend del thin pool (evita che si riempia)
# /etc/lvm/lvm.conf
# thin_pool_autoextend_threshold = 80    # Estendi quando raggiunge 80%
# thin_pool_autoextend_percent = 20      # Estendi del 20%

# ATTENZIONE: se il thin pool raggiunge il 100% senza autoextend,
# tutti i thin volume entrano in modalità errore. I dati NON sono persi
# ma i filesystem vanno in read-only. Per recuperare:
sudo lvextend -L +50G vg_data/thinpool       # Espandi pool
# Poi riattivare i thin volume
sudo lvchange -an vg_data/thin_vol1
sudo lvchange -ay vg_data/thin_vol1
```

### LVM VDO — Deduplicazione e Compressione

VDO (Virtual Data Optimizer) integrato in LVM fornisce deduplicazione e compressione inline a livello blocco. Il motore UDS (Universal Deduplication Service) mantiene un indice dei blocchi già scritti e elimina duplicati prima della scrittura su disco, mentre la compressione LZ4 riduce ulteriormente lo spazio occupato.

**Requisiti:** kernel ≥ 6.2 con modulo `kvdo`, pacchetto `lvm2` ≥ 2.03.23. UDS richiede minimo 250 MB di RAM per l'indice (fino a 1 GB per volumi > 4 TB).

```bash
# Creare un volume VDO su un VG esistente
# --type vdo crea automaticamente un VDO pool + VDO logical volume
# Il virtual size può essere maggiore del physical size (thin provisioning implicito)
sudo lvcreate --type vdo --name vdo_data \
  --size 500G \
  --virtualsize 1T \
  vg_data

# Il filesystem va creato sul VDO LV
sudo mkfs.xfs -K /dev/vg_data/vdo_data    # -K salta il discard iniziale
sudo mount /dev/vg_data/vdo_data /mnt/vdo

# ──── Gestione deduplicazione e compressione ────

# Stato attuale
sudo lvs -o+vdo_compression,vdo_deduplication vg_data/vdo_data

# Abilitare/disabilitare compressione a caldo
sudo lvchange --compression y vg_data/vdo_data    # Abilita
sudo lvchange --compression n vg_data/vdo_data    # Disabilita

# Abilitare/disabilitare deduplicazione a caldo
sudo lvchange --deduplication y vg_data/vdo_data   # Abilita
sudo lvchange --deduplication n vg_data/vdo_data   # Disabilita

# ──── Monitoraggio ────

# Statistiche VDO (spazio fisico usato, rapporto dedup/compressione)
sudo vdostats --human-readable
# Device              Size    Used   Avail  Use%  Savings%
# /dev/mapper/...     500G    120G    380G   24%    62%

# Savings% indica il risparmio combinato dedup + compressione.
# Valori tipici: backup VM = 60-80%, database = 20-40%, media = 5-15%.

# ──── Tuning VDO ────

# Dimensione indice UDS: influisce su quanti blocchi possono essere deduplicati
# "sparse" = meno RAM, indice su disco (default)
# "dense" = più RAM, indice in memoria (più veloce)
# Configurabile solo alla creazione:
sudo lvcreate --type vdo --name vdo_fast \
  --size 500G --virtualsize 2T \
  --config 'allocation/vdo_index_memory_size_mb=1024' \
  vg_data

# ATTENZIONE: non superare un rapporto virtualsize/physicalsize > 10:1
# Oltre 10:1 il rischio di esaurimento spazio fisico è troppo alto.
# Monitorare SEMPRE con vdostats e configurare alerting su soglia 80%.
```

**Quando usare VDO:** ambienti con dati altamente duplicati — server di backup, repository container image, ambienti di virtualizzazione con molte VM simili. Non adatto per database transazionali ad alte IOPS dove l'overhead di dedup/compressione penalizza la latenza.

#### Thin Provisioning — Lifecycle Avanzato

Il thin provisioning LVM alloca spazio su disco solo quando i blocchi vengono effettivamente scritti. Questo permette di over-committare lo storage: la somma delle dimensioni virtuali dei thin volume può superare lo spazio fisico del thin pool. La gestione corretta del lifecycle richiede attenzione costante.

```bash
# ──── Over-provisioning responsabile ────

# Verificare lo stato di allocazione del thin pool
sudo lvs -o+lv_size,pool_lv,origin,data_percent,metadata_percent vg_data

# Rapporto over-provisioning consigliato:
# - Dev/test: fino a 10:1 (aggressive)
# - Produzione: max 3:1 (conservativo)
# - Database: 1.5:1 o nessun over-provisioning

# ──── Reclaim spazio (fstrim su thin volume) ────

# Quando si cancellano file, il filesystem libera blocchi ma il thin pool
# non lo sa finché non riceve DISCARD. fstrim invia i DISCARD al pool.
sudo fstrim -v /mnt/thin_vol1
# /mnt/thin_vol1: 45.2 GiB (48547white bytes) trimmed

# Abilitare discard automatico nel mount (impatto performance):
# /dev/vg_data/thin_vol1 /mnt/thin ext4 defaults,discard 0 2

# ──── Monitoraggio automatico con alerting ────

# Script di monitoraggio per cron (ogni 5 minuti):
# Invia alert se data_percent > 85%
sudo lvs --noheadings -o lv_name,data_percent --select 'pool_lv=""' vg_data 2>/dev/null | \
  awk '{if ($2+0 > 85) print "ALERT: pool " $1 " at " $2 "%"}'

# dmeventd: daemon che monitora thin pool e attiva autoextend
# Verificare che sia attivo:
sudo systemctl status dm-event
```

### LVM Cache (lvmcache)

LVM cache permette di usare un SSD come cache per un HDD, accelerando le operazioni I/O.

```bash
# Prerequisito: un PV veloce (SSD) e un PV lento (HDD) nello stesso VG
sudo pvcreate /dev/ssd1 /dev/hdd1
sudo vgcreate vg_cached /dev/ssd1 /dev/hdd1

# Creare il LV dati sull'HDD
sudo lvcreate -L 500G -n lv_data vg_cached /dev/hdd1

# Creare il pool cache sull'SSD
sudo lvcreate -L 50G -n lv_cache vg_cached /dev/ssd1        # Cache data
sudo lvcreate -L 500M -n lv_cache_meta vg_cached /dev/ssd1  # Cache metadata

# Convertire in cache pool
sudo lvconvert --type cache-pool \
  --poolmetadata vg_cached/lv_cache_meta \
  vg_cached/lv_cache

# Agganciare il cache pool al LV dati
sudo lvconvert --type cache \
  --cachepool vg_cached/lv_cache \
  vg_cached/lv_data

# Modalità cache:
# --cachemode writethrough  ← default, sicuro (scritture sincrone)
# --cachemode writeback     ← performance, rischio dati se SSD muore

# Verificare stato cache
sudo lvs -o +cache_total_blocks,cache_used_blocks,cache_read_hits,cache_write_hits vg_cached

# Rimuovere cache (senza perdere dati)
sudo lvconvert --uncache vg_cached/lv_data

# Metodo alternativo semplificato (dm-writecache per SSD NVMe)
sudo lvconvert --type writecache \
  --cachevol vg_cached/lv_cache \
  vg_cached/lv_data
```

### LVM Striping

Lo striping distribuisce i dati su più PV in parallelo, aumentando il throughput I/O.

```bash
# Creare LV con striping su 3 PV
sudo lvcreate -L 100G -n lv_fast -i 3 -I 256k vg_data
# -i 3   = numero di stripe (PV su cui distribuire)
# -I 256k = stripe interleave size (dimensione del chunk)

# Il VG deve avere almeno 3 PV con sufficiente spazio libero
# Lo striping è trasparente al filesystem soprastante

# Verificare configurazione stripe
sudo lvs -o +stripes,stripe_size vg_data/lv_fast
sudo lvdisplay -m /dev/vg_data/lv_fast  # Mostra mapping fisico

# Combinare striping e mirror per massima performance+ridondanza
sudo lvcreate --type raid10 -L 100G -n lv_perf \
  -i 2 -m 1 vg_data
# RAID 10: 2 stripe, ciascuno mirrorato = serve min 4 PV
```

### LVM Mirroring

```bash
# Mirror classico (legge dal mirror più veloce)
sudo lvcreate --type mirror -L 50G -m 1 -n lv_mirror vg_data
# -m 1 = 1 copia mirror (totale 2 copie dei dati)
# -m 2 = 2 copie mirror (totale 3 copie)

# Mirror basato su RAID1 (preferito, più robusto)
sudo lvcreate --type raid1 -L 50G -m 1 -n lv_raid1 vg_data

# Verificare stato sync
sudo lvs -o +sync_percent,copy_percent,raid_sync_action vg_data/lv_raid1

# Convertire un LV esistente in mirror
sudo lvconvert --type raid1 -m 1 vg_data/lv_existing

# Rimuovere un mirror leg (tornare a non-mirrorato)
sudo lvconvert -m 0 vg_data/lv_raid1

# Sostituire un mirror leg guasto
sudo lvconvert --repair vg_data/lv_raid1

# Mirror log: dove salvare il log di sync
# --mirrorlog core     = in RAM (veloce, perde sync state al reboot)
# --mirrorlog disk     = su disco (default, persistente)
# --mirrorlog mirrored = log mirrorato (max affidabilità)
```

---

## Stratis 3.x — Gestione Storage Semplificata

Stratis è un gestore di volumi sviluppato da Red Hat che integra thin provisioning, snapshot e filesystem management in un'interfaccia unificata. Internamente usa device-mapper (thin provisioning + cache) e XFS, ma astrae la complessità di LVM+mkfs in comandi semplici.

**Versione corrente:** Stratis 3.9.0 (aprile 2026) introduce crittografia/decrittazione online dei pool e avvio pool senza cache. Disponibile su Fedora, RHEL 9+, Ubuntu 24.04+.

```bash
# ──── Installazione ────
sudo apt install stratisd stratis-cli     # Debian/Ubuntu
sudo dnf install stratisd stratis-cli     # Fedora/RHEL

# Avviare e abilitare il daemon
sudo systemctl enable --now stratisd

# ──── Pool e Filesystem ────

# Creare un pool (thin provisioning automatico)
sudo stratis pool create mypool /dev/sdb /dev/sdc

# Aggiungere disco a pool esistente
sudo stratis pool add-data mypool /dev/sdd

# Aggiungere cache tier (SSD per accelerare pool su HDD)
sudo stratis pool add-cache mypool /dev/nvme0n1

# Creare filesystem (XFS creato automaticamente, thin-provisioned)
sudo stratis filesystem create mypool fs_progetti
sudo stratis filesystem create mypool fs_backup

# Montare — i device Stratis appaiono in /dev/stratis/
sudo mount /dev/stratis/mypool/fs_progetti /mnt/progetti

# Per fstab usare x-systemd.requires=stratisd.service:
# /dev/stratis/mypool/fs_progetti /mnt/progetti xfs defaults,x-systemd.requires=stratisd.service 0 0

# ──── Snapshot ────

# Snapshot = copia CoW del filesystem (istantanea, spazio zero iniziale)
sudo stratis filesystem snapshot mypool fs_progetti fs_progetti_snap_20260524

# Montare lo snapshot per recovery
sudo mount /dev/stratis/mypool/fs_progetti_snap_20260524 /mnt/recovery

# Elencare snapshot e filesystem
sudo stratis filesystem list mypool

# Eliminare snapshot
sudo stratis filesystem destroy mypool fs_progetti_snap_20260524

# ──── Crittografia (Stratis 3.x) ────

# Pool cifrato con passphrase in kernel keyring
sudo stratis key set --capture-key mykey
sudo stratis pool create --key-desc mykey pool_cifrato /dev/sde

# Stratis 3.9.0: crittografia online di pool esistente
sudo stratis pool encrypt mypool --key-desc mykey

# ──── Monitoraggio ────

# Stato pool (spazio fisico allocato vs usato)
sudo stratis pool list
# Name      Total Physical  Properties  UUID
# mypool    1.5 TiB         ~Ca,~Cr     xxxxxxxx

sudo stratis blockdev list mypool    # Dischi nel pool
sudo stratis filesystem list mypool  # Filesystem e uso
```

**Stratis vs LVM:** Stratis semplifica operazioni comuni ma non supporta RAID (usa mdadm sotto), striping configurabile, o cache write-back granulare. Per scenari enterprise complessi, LVM resta superiore. Stratis eccelle come soluzione rapida per workstation e server semplici dove la gestione manuale LVM+mkfs è overkill.

```bash
# ──── Stratis 3.x: funzionalità avanzate ────

# Rinominare filesystem
sudo stratis filesystem rename mypool fs_progetti fs_produzione

# Distruggere pool (ATTENZIONE: irreversibile)
sudo stratis pool destroy mypool

# D-Bus API: Stratis espone un'interfaccia D-Bus per automazione
# Usare stratis-dbus-client o chiamate dirette per scripting avanzato
busctl introspect org.storage.stratis3 /org/storage/stratis3

# Limitazioni note Stratis 3.x:
# - Filesystem massimo per pool: 100 (soft limit)
# - No shrink del pool (solo grow)
# - No RAID nativo (usare mdadm sotto il pool)
# - XFS non supporta shrink → filesystem Stratis non si riducono
# - No quota per-filesystem (XFS project quotas disponibili manualmente)
```

---

## RAID Software (mdadm)

### Livelli RAID

| RAID | Min dischi | Capacità | Tolleranza | Uso |
|---|---|---|---|---|
| 0 (stripe) | 2 | N×disco | Nessuna | Performance pura |
| 1 (mirror) | 2 | 1×disco | 1 disco | Boot, OS |
| 5 (stripe+parità) | 3 | (N-1)×disco | 1 disco | Storage generale |
| 6 (stripe+2parità) | 4 | (N-2)×disco | 2 dischi | Alta affidabilità |
| 10 (mirror+stripe) | 4 | N/2×disco | 1 per mirror | Database, alta performance |

### Layout RAID 10

```
RAID 10 con 4 dischi:

     Stripe 0          Stripe 1
  ┌───────────┐    ┌───────────┐
  │  Disco A  │    │  Disco C  │     ← Dati
  │  (copia 1)│    │  (copia 1)│
  └───────────┘    └───────────┘
  ┌───────────┐    ┌───────────┐
  │  Disco B  │    │  Disco D  │     ← Mirror
  │  (copia 2)│    │  (copia 2)│
  └───────────┘    └───────────┘

Near layout (default):  mirror → stripe (migliore per read sequenziali)
Far layout:             stripe → mirror (migliore per read random)
sudo mdadm --create /dev/md0 --level=10 --layout=f2 ...  # Far layout
```

### Operazioni mdadm

```bash
# CREARE RAID
sudo mdadm --create /dev/md0 --level=1 --raid-devices=2 /dev/sdb1 /dev/sdc1  # RAID 1
sudo mdadm --create /dev/md0 --level=5 --raid-devices=3 /dev/sdb1 /dev/sdc1 /dev/sdd1
sudo mdadm --create /dev/md0 --level=10 --raid-devices=4 /dev/sd{b,c,d,e}1

# Con spare (disco di riserva per rebuild automatico)
sudo mdadm --create /dev/md0 --level=5 --raid-devices=3 \
  --spare-devices=1 /dev/sdb1 /dev/sdc1 /dev/sdd1 /dev/sde1

# Chunk size personalizzato (default 512K)
sudo mdadm --create /dev/md0 --level=5 --raid-devices=3 \
  --chunk=256 /dev/sdb1 /dev/sdc1 /dev/sdd1

# STATO
cat /proc/mdstat                    # Stato in tempo reale
sudo mdadm --detail /dev/md0       # Dettaglio array
sudo mdadm --examine /dev/sdb1     # Info sul disco membro

# Creare filesystem e montare
sudo mkfs.ext4 /dev/md0
sudo mount /dev/md0 /mnt/raid

# PERSISTENZA
sudo mdadm --detail --scan >> /etc/mdadm/mdadm.conf
sudo update-initramfs -u           # Debian/Ubuntu

# GESTIONE GUASTI
sudo mdadm /dev/md0 --fail /dev/sdc1     # Marca come guasto
sudo mdadm /dev/md0 --remove /dev/sdc1   # Rimuovi
sudo mdadm /dev/md0 --add /dev/sdf1      # Aggiungi sostituto (rebuild)

# Monitorare rebuild
watch cat /proc/mdstat

# FERMARE E DISTRUGGERE
sudo umount /dev/md0
sudo mdadm --stop /dev/md0
sudo mdadm --zero-superblock /dev/sdb1 /dev/sdc1
```

### Monitoraggio e Alert

```bash
# Avviare il daemon di monitoraggio
sudo mdadm --monitor --scan --daemonise --mail=admin@example.com --delay=300
# --delay=300 = controlla ogni 300 secondi
# --mail = notifica email su eventi (degraded, rebuild, fail)

# Monitoraggio via systemd (metodo moderno)
sudo systemctl enable --now mdmonitor

# Configurazione in /etc/mdadm/mdadm.conf
# MAILADDR admin@example.com
# PROGRAM /usr/local/bin/mdadm-alert.sh     # Script custom su evento

# Esempio script alert:
# #!/bin/bash
# echo "RAID Event: $1 on $2" | mail -s "mdadm alert" admin@example.com

# Test alert (simula un evento)
sudo mdadm --monitor --scan --oneshot --test
```

### Bitmap e Resync Veloce

```bash
# Write-intent bitmap: traccia i blocchi modificati durante un downtime
# Permette resync parziale invece di resync completo dopo un reboot

# Aggiungere bitmap a un array esistente
sudo mdadm --grow /dev/md0 --bitmap=internal

# Bitmap esterno (su filesystem separato, più veloce)
sudo mdadm --grow /dev/md0 --bitmap=/var/lib/mdadm/md0.bitmap

# Rimuovere bitmap
sudo mdadm --grow /dev/md0 --bitmap=none

# Verificare stato bitmap
sudo mdadm --detail /dev/md0 | grep -i bitmap
```

### Crescita e Reshape

```bash
# Aggiungere un disco a un RAID 5 (expand)
sudo mdadm --grow /dev/md0 --raid-devices=4 --add /dev/sde1
# Il reshape redistribuisce i dati su 4 dischi
# Monitorare: watch cat /proc/mdstat

# Cambiare livello RAID (reshape)
# Da RAID 1 a RAID 5 (aggiungere disco)
sudo mdadm --grow /dev/md0 --level=5 --raid-devices=3 --add /dev/sdd1

# Cambiare chunk size
sudo mdadm --grow /dev/md0 --chunk=256

# ATTENZIONE: il reshape è un'operazione lunga e rischiosa.
# Assicurarsi di avere backup prima di procedere.
# Se il sistema crasha durante il reshape, il checkpoint permette di riprendere.
# Verificare: cat /proc/mdstat (mostra la percentuale di completamento)
```

---

## ZFS

ZFS è un filesystem e volume manager avanzato con checksum, snapshot, compressione, deduplicazione, RAID integrato e self-healing.

```bash
# Installazione (Debian/Ubuntu)
sudo apt install zfsutils-linux

# CREARE POOL
sudo zpool create tank /dev/sdb                     # Pool singolo disco
sudo zpool create tank mirror /dev/sdb /dev/sdc     # Mirror (RAID 1)
sudo zpool create tank raidz1 /dev/sdb /dev/sdc /dev/sdd  # RAIDZ1 (RAID 5)
sudo zpool create tank raidz2 /dev/sdb /dev/sdc /dev/sdd /dev/sde  # RAIDZ2 (RAID 6)
sudo zpool create tank raidz3 /dev/sdb /dev/sdc /dev/sdd /dev/sde /dev/sdf  # RAIDZ3

# Pool con vdev multipli (espandibilità)
sudo zpool create tank \
  mirror /dev/sdb /dev/sdc \
  mirror /dev/sdd /dev/sde
# Equivalente a RAID 10: 2 mirror in stripe

# Usare disk-by-id per persistenza (raccomandato!)
sudo zpool create tank mirror \
  /dev/disk/by-id/ata-WDC_WD10... \
  /dev/disk/by-id/ata-WDC_WD10...

# STATO POOL
sudo zpool status                   # Stato tutti i pool
sudo zpool status tank              # Stato specifico
sudo zpool list                     # Spazio usato/disponibile
sudo zpool iostat 5                 # I/O stats ogni 5 secondi
sudo zpool history tank             # Cronologia comandi sul pool

# DATASET (come sottocartelle gestite)
sudo zfs create tank/data           # Crea dataset
sudo zfs create tank/data/progetti
sudo zfs create -o mountpoint=/opt/app tank/app
sudo zfs list                       # Lista dataset
sudo zfs get all tank/data          # Tutte le proprietà

# PROPRIETÀ
sudo zfs set compression=zstd tank/data      # Compressione
sudo zfs set quota=100G tank/data            # Quota
sudo zfs set reservation=50G tank/data       # Spazio garantito
sudo zfs set atime=off tank/data             # Disabilita access time
sudo zfs set recordsize=1M tank/data/media   # Record size per file grandi

# SNAPSHOT
sudo zfs snapshot tank/data@2024-01-15       # Crea snapshot
sudo zfs list -t snapshot                     # Lista snapshot
sudo zfs rollback tank/data@2024-01-15       # Rollback
sudo zfs destroy tank/data@2024-01-15        # Elimina snapshot

# Gli snapshot sono accessibili in .zfs/snapshot/
ls /tank/data/.zfs/snapshot/2024-01-15/

# SEND/RECEIVE (replica)
sudo zfs send tank/data@snap1 | ssh remote sudo zfs receive backup/data
sudo zfs send -i tank/data@snap1 tank/data@snap2 | ssh remote sudo zfs receive backup/data  # Incrementale

# SCRUB (verifica integrità)
sudo zpool scrub tank               # Avvia scrub
sudo zpool status tank               # Monitorare progresso
sudo zpool scrub -s tank             # Interrompere scrub
sudo zpool scrub -p tank             # Mettere in pausa (riprendere con scrub senza flag)

# ESPANDERE
sudo zpool add tank /dev/sdf         # Aggiungi disco (NON mirror, attenzione!)
sudo zpool add tank mirror /dev/sdf /dev/sdg  # Aggiungi mirror pair
```

### ARC, L2ARC, ZIL e SLOG

ZFS utilizza un sistema di caching multi-livello sofisticato per bilanciare performance e affidabilità.

```
 ┌──────────────────────────────────────────────┐
 │                 ARC (RAM)                     │  Cache lettura primaria
 │   Risiede interamente in RAM del sistema      │  Adaptive Replacement Cache
 └──────────────────────┬───────────────────────┘
                        │ eviction
 ┌──────────────────────▼───────────────────────┐
 │              L2ARC (SSD opzionale)            │  Cache lettura secondaria
 │   Estende ARC su dispositivo veloce           │  Solo letture, volatile
 └──────────────────────────────────────────────┘

 ┌──────────────────────────────────────────────┐
 │              ZIL (su pool)                    │  ZFS Intent Log
 │   Log delle scritture sincrone in-flight      │  Risiede nel pool di default
 └──────────────────────────────────────────────┘
                        │ accelerato da
 ┌──────────────────────▼───────────────────────┐
 │              SLOG (SSD/NVMe opzionale)        │  Separate Log device
 │   Sposta lo ZIL su dispositivo veloce         │  Critico per sync writes
 └──────────────────────────────────────────────┘
```

#### ARC (Adaptive Replacement Cache)

```bash
# ARC è la cache di lettura in RAM. Si dimensiona automaticamente,
# usando tutta la RAM disponibile (fino al limite configurato).

# Verificare dimensione ARC corrente
cat /proc/spl/kstat/zfs/arcstats | grep -E "^(size|c_max|c_min|hits|misses)"
# size    = dimensione corrente in byte
# c_max   = limite massimo
# hits    = cache hit
# misses  = cache miss

# Hit ratio ARC (dovrebbe essere > 90%)
arc_summary                          # Tool dedicato (pacchetto zfsutils-linux)

# Limitare ARC (utile se ZFS compete con le applicazioni per la RAM)
# /etc/modprobe.d/zfs.conf
# options zfs zfs_arc_max=8589934592    # 8 GiB max
# options zfs zfs_arc_min=2147483648    # 2 GiB min

# Applicare senza reboot
echo 8589934592 | sudo tee /sys/module/zfs/parameters/zfs_arc_max

# Statistiche dettagliate ARC
sudo arcstat 5                       # Aggiorna ogni 5 secondi
# (colonne: read, hit%, miss%, dmis%, pmis%, mmis%, arcsz, c)
```

#### L2ARC (Level 2 ARC)

```bash
# L2ARC estende ARC usando un SSD. Cache di sola lettura.
# Utile quando il working set supera la RAM disponibile.

# Aggiungere un dispositivo L2ARC
sudo zpool add tank cache /dev/nvme0n1p1

# Verificare stato L2ARC
sudo zpool status tank | grep cache
sudo zpool iostat -v tank

# L2ARC statistiche
cat /proc/spl/kstat/zfs/arcstats | grep l2

# Rimuovere L2ARC (senza perdita dati, è solo cache)
sudo zpool remove tank /dev/nvme0n1p1

# NOTA: L2ARC consuma RAM (~70 byte per blocco cached).
# Con L2ARC da 500GB e recordsize 128K: ~280MB di ARC header in RAM.
# Non aggiungere L2ARC se non hai abbastanza RAM per gli header.

# Tuning L2ARC
# /etc/modprobe.d/zfs.conf
# options zfs l2arc_write_max=67108864     # Max scrittura L2ARC: 64MB/s
# options zfs l2arc_headroom=4             # Moltiplicatore feed rate
# options zfs l2arc_noprefetch=0           # Cachea anche prefetch (0=sì)
```

#### ZIL e SLOG

```bash
# ZIL (ZFS Intent Log): registra le scritture sincrone in-flight.
# Di default, lo ZIL risiede nel pool stesso (sui dischi dati).

# SLOG (Separate Log): sposta lo ZIL su un dispositivo dedicato
# più veloce (SSD/NVMe). Migliora drasticamente le sync write.
# Casi d'uso: NFS server, database, iSCSI target, VM storage.

# Aggiungere SLOG (raccomandato: mirror per protezione)
sudo zpool add tank log mirror /dev/nvme1n1p1 /dev/nvme1n1p2

# Verificare
sudo zpool status tank | grep log

# Rimuovere SLOG
sudo zpool remove tank /dev/nvme1n1p1

# Dimensionamento SLOG:
# Serve solo pochi GB (5-20GB tipicamente).
# Deve sostenere 10 secondi di sync writes al peak throughput.
# Esempio: 500MB/s sync write peak → 5GB di SLOG bastano.

# IMPORTANTE: se il SLOG muore, le scritture in-flight vanno perse.
# Per questo si usa SEMPRE un mirror per lo SLOG.
# Se un SLOG singolo muore con dati in-flight = possibile corruzione.

# Dispositivi adatti per SLOG:
# - Intel Optane (ideale: bassa latenza, alta endurance)
# - NVMe enterprise con PLP (Power Loss Protection)
# - NON usare SSD consumer senza PLP!
```

### ZFS Degraded Recovery

```bash
# Quando un disco in un pool ridondante (mirror/raidz) guasta:
sudo zpool status tank
# state: DEGRADED
#   mirror-0
#     sdb    ONLINE
#     sdc    FAULTED    ← disco guasto

# Sostituire il disco guasto
sudo zpool replace tank /dev/sdc /dev/sdf
# ZFS avvia il resilver (ricostruzione) automaticamente

# Monitorare il resilver
sudo zpool status tank
# scan: resilver in progress since...
#   123G scanned out of 456G at 200M/s, 0h28m to go

# Calcolo ETA resilver:
# Dati totali / velocità resilver = tempo stimato
# 500GB / 200MB/s ≈ 42 minuti

# Se il disco originale è ancora presente ma guasto:
sudo zpool offline tank /dev/sdc       # Metti offline
# Sostituire fisicamente, poi:
sudo zpool replace tank /dev/sdc       # Usa lo stesso slot

# Cancellare errori dopo la riparazione
sudo zpool clear tank
```

---

## Btrfs Avanzato

```bash
# Creare filesystem Btrfs
sudo mkfs.btrfs /dev/sdb1
sudo mkfs.btrfs -d raid1 -m raid1 /dev/sdb /dev/sdc  # RAID 1 nativo

# SUBVOLUMI (isolamento logico, snapshot indipendenti)
sudo btrfs subvolume create /mnt/btrfs/@
sudo btrfs subvolume create /mnt/btrfs/@home
sudo btrfs subvolume create /mnt/btrfs/@snapshots
sudo btrfs subvolume list /mnt/btrfs

# Subvolume ID e gestione
sudo btrfs subvolume show /mnt/btrfs/@
sudo btrfs subvolume delete /mnt/btrfs/@old

# Impostare subvolume di default (montato senza subvol=)
sudo btrfs subvolume set-default 256 /mnt/btrfs

# Mount subvolume specifico
sudo mount -o subvol=@ /dev/sdb1 /mnt/root
sudo mount -o subvol=@home /dev/sdb1 /home

# SNAPSHOT
sudo btrfs subvolume snapshot /mnt/btrfs/@ /mnt/btrfs/@snapshots/root-2024-01-15
sudo btrfs subvolume snapshot -r /mnt/btrfs/@ /mnt/btrfs/@snapshots/root-readonly  # Read-only

# COMPRESSIONE
sudo mount -o compress=zstd /dev/sdb1 /mnt/btrfs
# O per tutto il filesystem:
sudo btrfs property set /mnt/btrfs compression zstd

# Livelli compressione: zstd:1 (veloce) a zstd:15 (massima)
sudo mount -o compress=zstd:3 /dev/sdb1 /mnt/btrfs

# Comprimere file esistenti (riscrittura)
sudo btrfs filesystem defragment -r -czstd /mnt/btrfs/

# STATO
sudo btrfs filesystem show
sudo btrfs filesystem df /mnt/btrfs
sudo btrfs filesystem usage /mnt/btrfs
sudo btrfs device stats /mnt/btrfs

# SCRUB
sudo btrfs scrub start /mnt/btrfs
sudo btrfs scrub status /mnt/btrfs
sudo btrfs scrub cancel /mnt/btrfs

# BILANCIAMENTO (dopo aggiunta disco o per redistribuire)
sudo btrfs balance start /mnt/btrfs
sudo btrfs balance status /mnt/btrfs
sudo btrfs balance cancel /mnt/btrfs

# Balance con filtro (più controllato)
sudo btrfs balance start -dusage=50 /mnt/btrfs    # Solo chunk dati usati < 50%
sudo btrfs balance start -musage=50 /mnt/btrfs    # Solo chunk metadati usati < 50%
sudo btrfs balance start -dusage=50 -musage=50 /mnt/btrfs  # Entrambi

# AGGIUNGERE/RIMUOVERE DISCO
sudo btrfs device add /dev/sdc /mnt/btrfs
sudo btrfs device remove /dev/sdb /mnt/btrfs
```

### Btrfs RAID

```bash
# Profili RAID Btrfs
# raid0:  stripe senza ridondanza
# raid1:  mirror (2 copie)
# raid1c3: mirror (3 copie)
# raid1c4: mirror (4 copie)
# raid5:  stripe + parità (NON raccomandato — bug noti, write hole)
# raid6:  stripe + 2 parità (NON raccomandato — stessa ragione)
# raid10: mirror + stripe
# single: nessuna ridondanza (default dati)
# dup:    duplicazione su stesso disco (default metadati su singolo disco)

# Creare con RAID
sudo mkfs.btrfs -d raid1 -m raid1 /dev/sdb /dev/sdc
# -d = profilo dati
# -m = profilo metadati (SEMPRE almeno raid1 o dup per i metadati!)

# Convertire profilo RAID online
sudo btrfs balance start -dconvert=raid1 -mconvert=raid1 /mnt/btrfs

# Aggiungere disco e convertire
sudo btrfs device add /dev/sdd /mnt/btrfs
sudo btrfs balance start -dconvert=raid10 /mnt/btrfs

# Sostituzione disco guasto
sudo btrfs device add /dev/sdd /mnt/btrfs           # Aggiungi nuovo
sudo btrfs device remove /dev/sdb /mnt/btrfs          # Rimuovi guasto
# Oppure:
sudo btrfs replace start /dev/sdb /dev/sdd /mnt/btrfs # Sostituzione diretta
sudo btrfs replace status /mnt/btrfs
```

### Btrfs Send/Receive

Send/receive permette la replica incrementale di snapshot tra filesystem Btrfs.

```bash
# Send/receive base: trasferire uno snapshot a un altro filesystem
# Lo snapshot DEVE essere read-only per il send
sudo btrfs subvolume snapshot -r /mnt/src/@ /mnt/src/@snap1

# Send locale
sudo btrfs send /mnt/src/@snap1 | sudo btrfs receive /mnt/dst/

# Send via rete (SSH)
sudo btrfs send /mnt/src/@snap1 | ssh remote sudo btrfs receive /mnt/backup/

# Send incrementale (solo le differenze tra due snapshot)
# Prerequisito: il parent snapshot deve esistere sia su src che su dst
sudo btrfs subvolume snapshot -r /mnt/src/@ /mnt/src/@snap2
sudo btrfs send -p /mnt/src/@snap1 /mnt/src/@snap2 | sudo btrfs receive /mnt/dst/

# Send incrementale con compressione (per rete lenta)
sudo btrfs send -p /mnt/src/@snap1 /mnt/src/@snap2 | \
  zstd | ssh remote "zstd -d | sudo btrfs receive /mnt/backup/"

# Send con clone source (per snapshot multipli)
sudo btrfs send -p /mnt/src/@snap1 \
  -c /mnt/src/@snap_other \
  /mnt/src/@snap2 | sudo btrfs receive /mnt/dst/

# Script di backup incrementale Btrfs
# 1. Creare snapshot read-only con data
# 2. Send incrementale rispetto all'ultimo snapshot
# 3. Cancellare snapshot vecchi (retention policy)
# 4. Tool consigliato: btrbk (automatizza tutto questo)
# sudo apt install btrbk
# /etc/btrbk/btrbk.conf
```

---

## bcachefs — Filesystem Copy-on-Write di Nuova Generazione

bcachefs è un filesystem CoW sviluppato da Kent Overstreet, nato dal layer di caching bcache. Combina funzionalità tipiche di ZFS e Btrfs in un unico filesystem: checksumming, cifratura nativa, compressione, snapshot, tiering multi-device e replicazione.

**Stato kernel (maggio 2026):** bcachefs è stato incluso nel kernel mainline dalla versione 6.7 alla 6.17. È stato **rimosso dal kernel 6.18** (dicembre 2025) a causa di violazioni delle linee guida di sviluppo del kernel. Da quel momento è disponibile **esclusivamente via DKMS** per kernel ≥ 6.16. Non trattarlo come filesystem mainline stabile per produzione.

```bash
# ──── Installazione (DKMS, kernel ≥ 6.16) ────
# Repository ufficiale: https://evilpiepirate.org/git/bcachefs.git
sudo apt install bcachefs-tools          # Strumenti userspace
# Il modulo kernel va compilato via DKMS dal sorgente

# ──── Creazione filesystem ────

# Singolo device con compressione e checksum
sudo bcachefs format \
  --compression=lz4 \
  --data_checksum=crc32c \
  --metadata_checksum=crc32c \
  /dev/sdb

# Multi-device con replicazione (simile a RAID1)
sudo bcachefs format \
  --replicas=2 \
  --compression=zstd \
  /dev/sdb /dev/sdc

# Multi-device con tiering (SSD cache + HDD storage)
sudo bcachefs format \
  --label=ssd.ssd1 /dev/nvme0n1 \
  --label=hdd.hdd1 /dev/sdb \
  --foreground_target=ssd \
  --promote_target=ssd \
  --background_target=hdd

sudo mount -t bcachefs /dev/nvme0n1:/dev/sdb /mnt/bcachefs

# ──── Cifratura nativa ────

# Cifratura ChaCha20/Poly1305 (no dm-crypt necessario)
sudo bcachefs format \
  --encrypted \
  --compression=zstd:3 \
  /dev/sdb
# Chiede passphrase alla creazione; richiesta ad ogni mount

sudo bcachefs unlock /dev/sdb     # Sblocca prima del mount
sudo mount -t bcachefs /dev/sdb /mnt/cifrato

# ──── Snapshot ────

# Creare subvolume (prerequisito per snapshot)
sudo bcachefs subvolume create /mnt/bcachefs/dati

# Snapshot del subvolume
sudo bcachefs subvolume snapshot \
  /mnt/bcachefs/dati /mnt/bcachefs/snap_20260524

# Eliminare snapshot
sudo bcachefs subvolume delete /mnt/bcachefs/snap_20260524

# ──── Amministrazione ────

sudo bcachefs fs usage /mnt/bcachefs   # Uso spazio dettagliato
sudo bcachefs device usage /dev/sdb    # Uso per singolo device
sudo bcachefs data rereplicate /mnt/bcachefs  # Ri-replicare dopo aggiunta disco
```

**bcachefs vs Btrfs vs ZFS:**

| Aspetto | bcachefs | Btrfs | ZFS |
|---|---|---|---|
| Stato kernel | DKMS only (da 6.18) | Mainline | Out-of-tree (OpenZFS) |
| Cifratura nativa | Sì (ChaCha20) | No (serve dm-crypt) | Sì |
| Compressione | LZ4, gzip, Zstandard | LZO, zlib, Zstandard | LZ4, gzip, Zstandard |
| Checksum | crc32c, xxhash, sha256 | crc32c, xxhash, sha256 | fletcher4, sha256, blake3 |
| RAID nativo | Replicazione + erasure coding | RAID 0/1/5/6/10 | RAID-Z1/Z2/Z3, mirror |
| Maturità produzione | Sperimentale | Maturo (con cautela su RAID5/6) | Molto maturo |

**Raccomandazione:** bcachefs è promettente ma non production-ready a maggio 2026. Usare per test, workstation personali, o ambienti dove la cifratura nativa senza dm-crypt è un requisito specifico. Per produzione, preferire ZFS (massima maturità e affidabilità) o Btrfs (mainline, buon supporto community). Monitorare lo stato di bcachefs: un eventuale rientro nel kernel mainline in futuro potrebbe cambiare questa valutazione, ma la rimozione dal kernel 6.18 impone cautela nell'adozione enterprise.

---

## iSCSI

iSCSI permette di accedere a storage remoto via rete TCP/IP come se fosse un disco locale.

```bash
# === TARGET (server che espone lo storage) ===
sudo apt install targetcli-fb

sudo targetcli
# /backstores/block create disk1 /dev/sdb
# /iscsi create iqn.2024-01.com.example:storage
# /iscsi/iqn.2024-01.com.example:storage/tpg1/luns create /backstores/block/disk1
# /iscsi/iqn.2024-01.com.example:storage/tpg1/acls create iqn.2024-01.com.example:client1
# exit
sudo systemctl enable --now target

# === INITIATOR (client che si connette) ===
sudo apt install open-iscsi

# Configurare IQN del client
echo "InitiatorName=iqn.2024-01.com.example:client1" | sudo tee /etc/iscsi/initiatorname.iscsi

# Scoprire target
sudo iscsiadm -m discovery -t st -p 192.168.1.100:3260

# Connettere
sudo iscsiadm -m node -T iqn.2024-01.com.example:storage -p 192.168.1.100:3260 --login

# Il disco appare come /dev/sdX
lsblk
sudo mkfs.ext4 /dev/sdc
sudo mount /dev/sdc /mnt/iscsi

# Login automatico
sudo iscsiadm -m node -T iqn.2024-01.com.example:storage -p 192.168.1.100 -o update -n node.startup -v automatic

# Disconnettere
sudo iscsiadm -m node -T iqn.2024-01.com.example:storage -p 192.168.1.100:3260 --logout
```

### iSCSI Avanzato

```bash
# === AUTENTICAZIONE CHAP ===
# Sul target (targetcli):
# /iscsi/iqn.../tpg1 set attribute authentication=1
# /iscsi/iqn.../tpg1/acls/iqn...client1 set auth userid=user password=secret12
# Mutual CHAP (target si autentica anche al client):
# /iscsi/iqn.../tpg1/acls/iqn...client1 set auth mutual_userid=target mutual_password=secret34

# Sul client:
# /etc/iscsi/iscsid.conf
# node.session.auth.authmethod = CHAP
# node.session.auth.username = user
# node.session.auth.password = secret12
# node.session.auth.username_in = target        # Mutual CHAP
# node.session.auth.password_in = secret34      # Mutual CHAP

# === MULTIPATH (ridondanza percorso) ===
# Con 2 interfacce di rete verso lo stesso target:
sudo iscsiadm -m discovery -t st -p 192.168.1.100:3260
sudo iscsiadm -m discovery -t st -p 192.168.2.100:3260
# Configurare dm-multipath per gestire i path multipli

# === PARAMETRI PERFORMANCE ===
# /etc/iscsi/iscsid.conf
# node.session.cmds_max = 128               # Comandi in parallelo
# node.session.queue_depth = 32             # Profondità coda
# node.conn[0].iscsi.MaxRecvDataSegmentLength = 262144  # 256K

# Stato sessioni
sudo iscsiadm -m session -P 3              # Dettaglio completo sessioni

# Rescan LUN (dopo aggiunta LUN su target)
sudo iscsiadm -m session --rescan
```

---

## NVMe over Fabrics (NVMe-oF)

NVMe-oF estende il protocollo NVMe oltre il bus PCIe locale, permettendo accesso a storage NVMe remoto via rete con latenza prossima a quella locale. A differenza di iSCSI (che incapsula SCSI su TCP), NVMe-oF trasporta comandi NVMe nativi, eliminando la traduzione di protocollo.

### Trasporti supportati

| Trasporto | Modulo kernel | Porta | Latenza tipica | Uso |
|---|---|---|---|---|
| TCP (`nvme-tcp`) | `nvme_tcp` / `nvmet_tcp` | 4420 | 100-500 µs | Datacenter standard, no hardware speciale |
| RDMA (`nvme-rdma`) | `nvme_rdma` / `nvmet_rdma` | 4420 | 10-50 µs | HPC, bassa latenza, richiede InfiniBand/RoCE |
| Fibre Channel | `nvme_fc` | N/A | 10-30 µs | SAN enterprise esistenti |

### Configurazione Target (server)

Il target NVMe-oF usa il sottosistema kernel `nvmet` configurato tramite `configfs`.

```bash
# ──── Prerequisiti ────
sudo modprobe nvmet
sudo modprobe nvmet-tcp           # Per trasporto TCP

# ──── Creare subsystem ────
cd /sys/kernel/config/nvmet/subsystems
sudo mkdir mysubsys
cd mysubsys

# Permettere accesso a qualsiasi host (dev/test)
echo 1 | sudo tee attr_allow_any_host

# ──── Aggiungere namespace (il disco NVMe da esportare) ────
sudo mkdir namespaces/1
cd namespaces/1
echo "/dev/nvme0n1" | sudo tee device_path
echo 1 | sudo tee enable

# ──── Creare porta di ascolto ────
cd /sys/kernel/config/nvmet/ports
sudo mkdir 1
cd 1
echo "0.0.0.0" | sudo tee addr_traddr     # IP di ascolto
echo "4420" | sudo tee addr_trsvcid        # Porta
echo "tcp" | sudo tee addr_trtype          # Trasporto
echo "ipv4" | sudo tee addr_adrfam         # Famiglia indirizzo

# Associare subsystem alla porta
sudo ln -s /sys/kernel/config/nvmet/subsystems/mysubsys \
  /sys/kernel/config/nvmet/ports/1/subsystems/mysubsys

# ──── Controllo accesso (produzione) ────
# Disabilitare accesso aperto
echo 0 | sudo tee /sys/kernel/config/nvmet/subsystems/mysubsys/attr_allow_any_host

# Creare host autorizzato (usare NQN del client)
sudo mkdir /sys/kernel/config/nvmet/hosts/nqn.2026-05.com.example:client1
sudo ln -s /sys/kernel/config/nvmet/hosts/nqn.2026-05.com.example:client1 \
  /sys/kernel/config/nvmet/subsystems/mysubsys/allowed_hosts/
```

### Configurazione Initiator (client)

```bash
# Installare strumenti NVMe
sudo apt install nvme-cli

# Discovery: trovare subsystem disponibili
sudo nvme discover -t tcp -a 192.168.1.100 -s 4420

# Connessione al subsystem
sudo nvme connect -t tcp -n mysubsys -a 192.168.1.100 -s 4420

# Verificare connessione
sudo nvme list              # Il disco remoto appare come /dev/nvmeXn1
lsblk                       # Visibile come block device normale

# Disconnessione
sudo nvme disconnect -n mysubsys

# Connessione persistente (sopravvive reboot)
# /etc/nvme/discovery.conf:
# --transport=tcp --traddr=192.168.1.100 --trsvcid=4420

# Multipath: connessione a più percorsi
sudo nvme connect -t tcp -n mysubsys -a 192.168.1.100 -s 4420
sudo nvme connect -t tcp -n mysubsys -a 192.168.1.101 -s 4420
# Il kernel NVMe multipath unifica i percorsi automaticamente
```

### Performance Tuning e Troubleshooting NVMe-oF

```bash
# ──── Tuning target ────

# Aumentare queue depth per namespace
echo 128 | sudo tee /sys/kernel/config/nvmet/subsystems/mysubsys/namespaces/1/queue_size 2>/dev/null

# ──── Tuning client ────

# Queue depth e keep-alive
sudo nvme connect -t tcp -n mysubsys -a 192.168.1.100 -s 4420 \
  --queue-size=1024 \
  --nr-io-queues=8 \
  --keep-alive-tmo=15

# Verificare parametri connessione attiva
sudo nvme list-subsys /dev/nvme1n1
# Mostra: trasporto, indirizzo, stato, live/dead paths

# ──── Diagnostica ────

# Statistiche I/O per controller NVMe-oF
sudo nvme smart-log /dev/nvme1
# Funziona anche su device remoti via NVMe-oF

# Controllare connettività
sudo nvme discover -t tcp -a 192.168.1.100 -s 4420
# Se fallisce: verificare firewall (porta 4420/tcp), moduli kernel, daemon target

# Log kernel per debug
sudo dmesg | grep -i nvme
# "nvme nvme1: creating X I/O queues" = connessione riuscita
# "nvme nvme1: Connect command failed" = errore connessione
```

**NVMe-oF vs iSCSI:** NVMe-oF TCP offre 2-4x throughput e 30-60% meno latenza rispetto a iSCSI su stessa rete, grazie all'eliminazione della traduzione SCSI. Per infrastrutture nuove con storage NVMe, NVMe-oF TCP è la scelta raccomandata. iSCSI resta valido per storage legacy SATA/SAS.

---

## NFS

NFS (Network File System) è il protocollo standard per condividere filesystem tra sistemi Linux/Unix.

### NFSv3 vs NFSv4

| Aspetto | NFSv3 | NFSv4 |
|---|---|---|
| Protocollo | UDP/TCP | Solo TCP |
| Porte | Molte (portmapper, mountd, nfsd, lockd) | Singola (2049) |
| Firewall | Complesso (porte dinamiche) | Semplice (solo 2049/tcp) |
| Sicurezza | AUTH_SYS (UID/GID) | Kerberos (RPCSEC_GSS) nativo |
| Mount | Per-export mount path | Pseudofilesystem unificato |
| Locking | NLM (separato, stateful) | Integrato nel protocollo |
| ACL | Limitato | NFSv4 ACL native |
| UTF-8 | No | Sì |
| Deleghe | No | Sì (client può cacheare) |

### Server NFS

```bash
# === SERVER ===
sudo apt install nfs-kernel-server

# Configurare export
# /etc/exports
/srv/nfs/share  192.168.1.0/24(rw,sync,no_subtree_check,no_root_squash)
/srv/nfs/public 192.168.1.0/24(ro,sync,no_subtree_check)
/srv/nfs/home   192.168.1.0/24(rw,sync,no_subtree_check,root_squash)

# Opzioni:
# rw/ro         = lettura-scrittura / sola lettura
# sync          = scrittura sincrona (sicuro)
# no_subtree_check = migliori performance
# root_squash   = root remoto mappato a nobody (sicurezza)
# no_root_squash = root remoto mantiene privilegi (necessario per alcuni scenari)
# all_squash    = tutti gli utenti mappati a nobody
# anonuid=1000  = UID per utenti squashed
# anongid=1000  = GID per utenti squashed
# sec=krb5p     = richiedi Kerberos con crittografia

# NFSv4: pseudofilesystem e fsid
# /etc/exports (NFSv4 style)
/srv/nfs         192.168.1.0/24(rw,sync,fsid=0,no_subtree_check,crossmnt)
/srv/nfs/share   192.168.1.0/24(rw,sync,no_subtree_check)
/srv/nfs/home    192.168.1.0/24(rw,sync,no_subtree_check)
# fsid=0 = root del pseudofilesystem NFSv4
# crossmnt = esporta automaticamente i sotto-mount

# Applicare
sudo exportfs -ra                  # Ri-esporta tutto
sudo exportfs -v                   # Lista export attivi

sudo systemctl enable --now nfs-kernel-server
```

### Client NFS

```bash
# === CLIENT ===
sudo apt install nfs-common

# Mount
sudo mount -t nfs server:/srv/nfs/share /mnt/nfs
sudo mount -t nfs -o vers=4,soft,timeo=100 server:/srv/nfs/share /mnt/nfs

# NFSv4 mount (path relativo al pseudofilesystem)
sudo mount -t nfs4 server:/share /mnt/nfs       # Nota: /share, non /srv/nfs/share

# Opzioni mount NFS rilevanti
# vers=4.2     = forza versione specifica
# soft          = ritorna errore dopo timeout (vs hard: blocca infinito)
# timeo=100     = timeout in decimi di secondo (10 sec)
# retrans=3     = retry prima di errore (con soft)
# rsize=1048576 = read buffer 1MB (performance)
# wsize=1048576 = write buffer 1MB (performance)
# nolock        = disabilita locking (utile per /boot NFS)
# _netdev       = aspetta rete prima di montare

# In fstab
# server:/srv/nfs/share  /mnt/nfs  nfs  defaults,_netdev,nofail  0  0
# Per NFSv4:
# server:/share  /mnt/nfs  nfs4  defaults,_netdev,nofail  0  0

# Automount con autofs (mount on-demand)
sudo apt install autofs
# /etc/auto.master:  /mnt/nfs  /etc/auto.nfs  --timeout=300
# /etc/auto.nfs:     share  -fstype=nfs4,rw  server:/share

# Verificare
showmount -e server                # Export disponibili sul server
nfsstat                            # Statistiche NFS
nfsstat -c                         # Solo client
nfsstat -s                         # Solo server
mountstats /mnt/nfs                # Statistiche per mount point
```

### NFS con Kerberos

```bash
# NFS + Kerberos fornisce autenticazione forte e crittografia.
# Prerequisiti: KDC (Key Distribution Center) configurato, keytab generati.

# Livelli sicurezza NFS Kerberos:
# sec=krb5    = solo autenticazione (identità verificata)
# sec=krb5i   = autenticazione + integrità (protezione da modifica)
# sec=krb5p   = autenticazione + integrità + privacy (crittografia completa)

# === Setup server ===
# 1. Ottenere keytab dal KDC per nfs/server.example.com@REALM
# 2. Installare il keytab in /etc/krb5.keytab
# 3. Export con sec:
# /etc/exports
# /srv/nfs/secure  192.168.1.0/24(rw,sync,sec=krb5p,no_subtree_check)

# 4. Abilitare gssproxy/rpc.gssd
sudo systemctl enable --now nfs-server rpc-gssd

# === Setup client ===
# 1. Installare keytab per nfs/client.example.com@REALM
# 2. Mount con sec=krb5p
sudo mount -t nfs4 -o sec=krb5p server:/secure /mnt/secure

# 3. Verificare ticket Kerberos
klist -e

# ID mapping (NFSv4 + Kerberos)
# /etc/idmapd.conf
# [General]
# Domain = example.com
# [Mapping]
# Nobody-User = nobody
# Nobody-Group = nogroup
sudo systemctl restart nfs-idmapd
```

---

## Samba (Condivisione Windows)

Samba permette a Linux di condividere file e stampanti con client Windows (protocollo SMB/CIFS).

```bash
# Installazione
sudo apt install samba

# /etc/samba/smb.conf
[global]
   workgroup = WORKGROUP
   server string = File Server
   security = user
   map to guest = never
   min protocol = SMB2          # Blocca SMBv1 (vulnerabile!)
   server signing = mandatory   # Firma obbligatoria
   smb encrypt = desired        # Crittografia preferita

[share]
   path = /srv/samba/share
   browsable = yes
   writable = yes
   valid users = @samba_users
   create mask = 0664
   directory mask = 0775

[public]
   path = /srv/samba/public
   browsable = yes
   writable = no
   guest ok = yes

# Creare utente Samba
sudo smbpasswd -a username         # Aggiunge utente (deve esistere come utente Linux)
sudo smbpasswd -e username         # Abilita
sudo smbpasswd -x username         # Rimuovi

# Verificare e riavviare
testparm                            # Verifica configurazione
sudo systemctl restart smbd nmbd
sudo systemctl enable smbd nmbd

# CLIENT LINUX (montare share Windows/Samba)
sudo mount -t cifs //server/share /mnt/samba -o username=user,password=pass
sudo mount -t cifs //server/share /mnt/samba -o credentials=/etc/samba/creds

# /etc/samba/creds (chmod 600)
# username=user
# password=pass
# domain=WORKGROUP

# In fstab
# //server/share /mnt/samba cifs credentials=/etc/samba/creds,uid=1000,gid=1000 0 0

# smbclient (client interattivo)
smbclient -L //server -U user      # Lista share
smbclient //server/share -U user   # Connetti

# Versioni protocollo SMB/CIFS
# SMB1/CIFS:  DEPRECATO, vulnerabile (WannaCry). Mai usare.
# SMB2:       Windows Vista+. Minimo accettabile.
# SMB3:       Windows 8+. Crittografia nativa. Raccomandato.
# SMB3.1.1:   Windows 10+. Pre-auth integrity. Ideale.

# Forzare versione su mount
sudo mount -t cifs //server/share /mnt -o vers=3.0,credentials=/etc/samba/creds
```

---

## GlusterFS

GlusterFS è un filesystem distribuito scalabile che aggrega storage da server multipli in un unico namespace.

### Concetti

```
 ┌──────────┐  ┌──────────┐  ┌──────────┐
 │  Nodo 1  │  │  Nodo 2  │  │  Nodo 3  │    ← Server (brick provider)
 │  /brick1 │  │  /brick2 │  │  /brick3 │
 └────┬─────┘  └────┬─────┘  └────┬─────┘
      │              │              │
      └──────────────┼──────────────┘
                     │
              ┌──────▼──────┐
              │   Volume    │    ← Aggregazione logica dei brick
              │ (replicated,│
              │  distributed│
              │  o striped) │
              └──────┬──────┘
                     │
              ┌──────▼──────┐
              │   Client    │    ← FUSE mount o NFS/SMB gateway
              └─────────────┘
```

### Tipi di Volume

| Tipo | Descrizione | Min nodi |
|---|---|---|
| Distributed | File distribuiti tra brick (no ridondanza) | 2 |
| Replicated | Copia di ogni file su N brick | 2 |
| Distributed-Replicated | Distributed + Replicated | 4 |
| Dispersed | Erasure coding (simile a RAID 5/6) | 3 |
| Distributed-Dispersed | Distributed + Dispersed | 6 |

### Setup GlusterFS

```bash
# === Installazione (su TUTTI i nodi) ===
sudo apt install glusterfs-server glusterfs-client
sudo systemctl enable --now glusterd

# === Formazione cluster (da un nodo) ===
sudo gluster peer probe node2.example.com
sudo gluster peer probe node3.example.com
sudo gluster peer status

# === Creare volumi ===

# Distributed-Replicated (2 repliche, 4 brick, 2 coppie)
sudo gluster volume create vol_data replica 2 transport tcp \
  node1:/brick/data node2:/brick/data \
  node3:/brick/data node4:/brick/data
# I file sono distribuiti tra 2 coppie, ciascuna con replica

# Replicated (3 copie, alta affidabilità)
sudo gluster volume create vol_critical replica 3 transport tcp \
  node1:/brick/critical node2:/brick/critical node3:/brick/critical

# Avviare il volume
sudo gluster volume start vol_data
sudo gluster volume info vol_data

# === Client mount ===
sudo mount -t glusterfs node1:/vol_data /mnt/gluster

# In fstab
# node1:/vol_data  /mnt/gluster  glusterfs  defaults,_netdev,backup-volfile-servers=node2:node3  0  0

# === Gestione ===
sudo gluster volume status vol_data          # Stato dettagliato
sudo gluster volume heal vol_data info       # Stato self-heal
sudo gluster volume heal vol_data full       # Forza self-heal
sudo gluster volume rebalance vol_data start # Ribilanciamento dopo add brick
sudo gluster volume add-brick vol_data \
  node5:/brick/data node6:/brick/data        # Espandi (in multipli di replica)

# === Tuning ===
sudo gluster volume set vol_data performance.cache-size 256MB
sudo gluster volume set vol_data performance.io-thread-count 32
sudo gluster volume set vol_data network.ping-timeout 10
```

---

## Ceph — Nozioni Base

Ceph è una piattaforma di storage distribuito che offre object storage, block storage (RBD) e filesystem (CephFS) in un sistema unificato.

### Architettura

```
 ┌──────────────────────────────────────────────────────────┐
 │                     Ceph Cluster                         │
 │                                                          │
 │  ┌───────┐  ┌───────┐  ┌───────┐                        │
 │  │ MON 1 │  │ MON 2 │  │ MON 3 │   ← Monitor (quorum)  │
 │  └───────┘  └───────┘  └───────┘     Mappa cluster,     │
 │                                       consenso Paxos     │
 │  ┌───────┐  ┌───────┐  ┌───────┐                        │
 │  │ OSD 1 │  │ OSD 2 │  │ OSD 3 │   ← Object Storage    │
 │  │(/dev/ │  │(/dev/ │  │(/dev/ │     Daemon              │
 │  │ sdb)  │  │ sdb)  │  │ sdb)  │     1 OSD per disco    │
 │  └───────┘  └───────┘  └───────┘                        │
 │                                                          │
 │  ┌───────┐                                               │
 │  │  MDS  │   ← Metadata Server (solo per CephFS)        │
 │  └───────┘                                               │
 │                                                          │
 │  ┌───────┐                                               │
 │  │  MGR  │   ← Manager (dashboard, telemetria, moduli)  │
 │  └───────┘                                               │
 └──────────────────────────────────────────────────────────┘

 Client accede via:
 - RBD:    block device (come disco virtuale per VM)
 - CephFS: filesystem POSIX distribuito
 - RGW:    S3/Swift compatible object gateway
 - librados: accesso diretto a RADOS
```

### Operazioni Base Ceph

```bash
# === Setup con cephadm (metodo moderno) ===
# Bootstrap (su primo nodo)
sudo cephadm bootstrap --mon-ip 192.168.1.10 --initial-dashboard-password secret

# Aggiungere nodi
sudo ceph orch host add node2 192.168.1.11
sudo ceph orch host add node3 192.168.1.12

# Aggiungere OSD (tutti i dischi disponibili)
sudo ceph orch apply osd --all-available-devices
# Oppure specifico:
sudo ceph orch daemon add osd node1:/dev/sdb

# === Stato cluster ===
sudo ceph status                    # Stato riassuntivo (HEALTH_OK/WARN/ERR)
sudo ceph osd tree                 # Albero OSD
sudo ceph osd df                   # Spazio per OSD
sudo ceph df                       # Spazio per pool
sudo ceph health detail            # Dettaglio problemi

# === Pool ===
sudo ceph osd pool create mypool 128     # 128 = placement groups
sudo ceph osd pool set mypool size 3     # 3 repliche
sudo ceph osd pool set mypool min_size 2 # Min repliche per I/O

# === RBD (Block Device) ===
sudo rbd create mypool/disk1 --size 100G
sudo rbd map mypool/disk1               # Mappa come /dev/rbdX
sudo mkfs.ext4 /dev/rbd0
sudo mount /dev/rbd0 /mnt/rbd

# Snapshot RBD
sudo rbd snap create mypool/disk1@snap1
sudo rbd snap ls mypool/disk1
sudo rbd snap rollback mypool/disk1@snap1

# === CephFS ===
sudo ceph fs volume create myfs
# Mount via kernel driver
sudo mount -t ceph mon1:6789:/ /mnt/cephfs -o name=admin,secret=AQD...

# Mount via FUSE (più lento, meno privilegi richiesti)
sudo ceph-fuse /mnt/cephfs

# === Manutenzione ===
sudo ceph osd scrub 0               # Scrub OSD 0
sudo ceph osd deep-scrub 0          # Deep scrub
sudo ceph pg repair 1.a3            # Ripara placement group
```

---

## Monitoraggio I/O Disco

### iostat — Statistiche I/O

```bash
# Installazione
sudo apt install sysstat

# Statistiche base (aggiorna ogni 2 secondi, 5 iterazioni)
iostat -xz 2 5

# Colonne chiave:
# r/s, w/s      = letture/scritture per secondo
# rkB/s, wkB/s  = throughput in KB/s
# await          = tempo medio di completamento I/O (ms) — CRITICO
# r_await, w_await = await separato per read/write
# %util          = percentuale di utilizzo — 100% = saturazione
# avgqu-sz       = lunghezza media coda I/O

# await > 20ms su SSD o > 50ms su HDD = possibile problema
# %util ~100% con basso throughput = collo di bottiglia

# Solo un disco specifico
iostat -xz 2 /dev/sda

# Con timestamp
iostat -xzt 2

# Per dispositivi LVM/dm
iostat -xz -p ALL 2
```

### iotop — I/O per Processo

```bash
# Installazione
sudo apt install iotop

# Mostra processi con I/O attivo
sudo iotop

# Solo processi con I/O attivo (non idle)
sudo iotop -o

# Batch mode (per scripting/log)
sudo iotop -b -n 5 -d 2             # 5 campioni, ogni 2 secondi

# iotop-c (alternativa con meno overhead)
sudo apt install iotop-c
sudo iotop-c -o

# Alternativa con pidstat (da sysstat)
pidstat -d 2                          # I/O per processo ogni 2 secondi
pidstat -d -p 1234 1                 # Solo PID 1234
```

### blktrace — Tracing I/O a Basso Livello

```bash
# blktrace cattura ogni singolo evento I/O nel block layer.
# Utile per analisi profonde di pattern I/O.

sudo apt install blktrace

# Catturare eventi per 30 secondi
sudo blktrace -d /dev/sda -w 30

# Analizzare con blkparse
blkparse -i sda -o sda_parsed.txt

# Visualizzazione con btt (block trace timing)
btt -i sda.blktrace.0 -o btt_output

# Alternativa moderna: BPF-based tools (meno overhead)
# Richiedono bpfcc-tools o bpftrace
sudo apt install bpfcc-tools

# biosnoop: ogni I/O con latenza
sudo biosnoop-bpfcc

# biolatency: istogramma latenze I/O
sudo biolatency-bpfcc

# biotop: top-like per I/O
sudo biotop-bpfcc
```

### fio — Benchmark I/O

```bash
# fio è lo standard per benchmark dello storage
sudo apt install fio

# Test lettura sequenziale
sudo fio --name=seqread --rw=read --bs=1M --size=1G \
  --numjobs=1 --runtime=30 --filename=/dev/sdb --direct=1

# Test scrittura sequenziale
sudo fio --name=seqwrite --rw=write --bs=1M --size=1G \
  --numjobs=1 --runtime=30 --filename=/dev/sdb --direct=1

# Test random read (simula workload database)
sudo fio --name=randread --rw=randread --bs=4k --size=1G \
  --numjobs=4 --iodepth=32 --runtime=60 --filename=/dev/sdb --direct=1

# Test random mixed read/write 70/30
sudo fio --name=mixed --rw=randrw --rwmixread=70 --bs=4k --size=1G \
  --numjobs=4 --iodepth=16 --runtime=60 --filename=/dev/sdb --direct=1

# Metriche importanti nell'output fio:
# IOPS:       operazioni I/O al secondo
# BW:         bandwidth (throughput)
# lat (usec): latenza (avg, p50, p95, p99)
# clat:       completion latency

# ATTENZIONE: --filename=/dev/sdX DISTRUGGE I DATI!
# Per testare su filesystem esistente, usare un file:
sudo fio --name=test --rw=randread --bs=4k --size=1G \
  --directory=/mnt/test --direct=1 --runtime=30
```

---

## Gestione SSD

### TRIM e Discard

TRIM comunica all'SSD quali blocchi non sono più in uso, permettendo al controller di ottimizzare il garbage collection interno e ridurre il write amplification.

```bash
# Verificare supporto TRIM
sudo lsblk --discard
# DISC-GRAN = granularità discard (> 0 = supportato)
# DISC-MAX  = max dimensione discard (> 0 = supportato)

# Metodo 1: TRIM periodico con fstrim (RACCOMANDATO)
sudo fstrim -v /                     # TRIM manuale su /
sudo fstrim -v /home                 # TRIM manuale su /home
sudo fstrim -av                      # TRIM su tutti i filesystem montati

# Timer systemd per TRIM settimanale (già incluso in molte distro)
sudo systemctl enable --now fstrim.timer
sudo systemctl status fstrim.timer
# Esegue fstrim su tutti i filesystem supportati ogni settimana

# Metodo 2: Discard continuo (mount option)
# /etc/fstab
# UUID=xxx  /  ext4  defaults,discard  0  1
# NOTA: "discard" come mount option esegue TRIM ad ogni delete.
# Può ridurre le performance. fstrim periodico è generalmente preferibile.

# TRIM con LVM (passthrough)
# /etc/lvm/lvm.conf
# issue_discards = 1
# Poi: sudo lvchange --discards passdown vg_data/lv_app

# TRIM con dm-crypt/LUKS
# crypttab: opzione "discard"
# /etc/crypttab
# luks-xxx  UUID=xxx  none  luks,discard
# NOTA SICUREZZA: discard su LUKS rivela i pattern di utilizzo.
# Un attaccante può dedurre quali blocchi sono usati/vuoti.
# Per dati sensibili, NON usare discard con LUKS.

# Verificare che TRIM funzioni end-to-end
sudo fstrim -v /
# /: 12.5 GiB (13421772800 bytes) trimmed  ← OK
# Se stampa 0 bytes trimmed e il disco non è pieno = qualcosa non passa
```

### Wear Leveling e Salute SSD

```bash
# Gli SSD hanno un numero limitato di cicli di scrittura per cella.
# Il controller interno distribuisce le scritture (wear leveling).

# Monitorare usura con smartctl
sudo smartctl -a /dev/sda | grep -i "wear\|life\|endurance\|written"
# Media_Wearout_Indicator:    valore 1-100 (100=nuovo, 1=fine vita)
# Wear_Leveling_Count:        cicli P/E medi
# Total_LBAs_Written:         settori totali scritti
# Host_Writes_32MiB:          dati scritti dall'host

# Per NVMe: informazioni SMART specifiche
sudo nvme smart-log /dev/nvme0n1
# percentage_used:  0%           ← usura (> 100% = oltre la garanzia)
# data_units_written: 12345678   ← unità da 512 byte × 1000 scritte
# data_units_read:   23456789
# power_on_hours:    8760

# Calcolo TBW (Terabyte Written) effettivo per NVMe:
# TBW = data_units_written × 512000 / 1e12
# Confrontare con TBW garantito dal produttore.

# Over-Provisioning
# Riservare 10-20% del disco non partizionato.
# Il controller SSD usa lo spazio non allocato per wear leveling e GC.
# Esempio: su SSD da 1TB, creare partizioni per soli 800-900GB.

# I/O scheduler ottimale per SSD
cat /sys/block/sda/queue/scheduler
# SSD: usare "none" (noop) o "mq-deadline"
# Non usare "bfq" o "cfq" su SSD (overhead inutile)
echo "none" | sudo tee /sys/block/sda/queue/scheduler

# Persistente via udev rule:
# /etc/udev/rules.d/60-scheduler.rules
# ACTION=="add|change", KERNEL=="sd*[!0-9]", ATTR{queue/rotational}=="0", ATTR{queue/scheduler}="none"
# ACTION=="add|change", KERNEL=="nvme*", ATTR{queue/scheduler}="none"
```

---

## SSD Health Monitoring Avanzato

Oltre a TRIM e scheduler, il monitoraggio proattivo della salute degli SSD previene perdite dati catastrofiche. Gli SSD hanno una vita finita misurata in TBW (TeraBytes Written); superata la soglia, l'affidabilità degrada rapidamente.

### SATA SSD — smartctl

```bash
# Installare smartmontools
sudo apt install smartmontools

# Attributi SMART critici per SSD SATA
sudo smartctl -A /dev/sda

# Attributi chiave da monitorare:
# ID  Attributo                    Significato
# 5   Reallocated_Sector_Ct       Settori riallocati (bad blocks rimappati)
# 177 Wear_Leveling_Count         Cicli P/E medi delle celle NAND
# 181 Program_Fail_Cnt_Total      Fallimenti di programmazione NAND
# 187 Reported_Uncorrect          Errori non correggibili
# 194 Temperature_Celsius         Temperatura operativa
# 231 SSD_Life_Left               Vita residua percentuale
# 241 Total_LBAs_Written          Byte totali scritti

# ALERT se:
# - Reallocated_Sector_Ct > 100: disco in degradazione
# - SSD_Life_Left < 10%: sostituzione imminente
# - Reported_Uncorrect > 0: possibile corruzione dati

# Test SMART breve e lungo
sudo smartctl -t short /dev/sda     # ~2 minuti
sudo smartctl -t long /dev/sda      # ~10-30 minuti
sudo smartctl -l selftest /dev/sda  # Risultati test

# Calcolo TBW consumati (SATA)
# Total_LBAs_Written × 512 byte = byte totali scritti
# Esempio: 3,500,000,000 LBA × 512 = 1.79 TB scritti
```

### NVMe SSD — nvme-cli

```bash
# Smart log NVMe (molto più dettagliato di SMART SATA)
sudo nvme smart-log /dev/nvme0n1

# Campi critici:
# percentage_used     : usura cumulativa (0-100%, può superare 100%)
# available_spare     : spare blocks rimanenti (%)
# available_spare_threshold : soglia minima spare (%)
# data_units_written  : unità da 512KB scritte
# media_errors        : errori media non correggibili
# critical_warning    : bitmap allarmi critici

# Calcolo TBW consumati (NVMe):
# data_units_written × 512 × 1000 byte = byte totali
# Esempio: data_units_written = 5,000,000
# 5,000,000 × 512 × 1000 = 2.56 TB scritti

# Error log NVMe
sudo nvme error-log /dev/nvme0n1

# Temperatura dettagliata (tutti i sensori)
sudo nvme smart-log /dev/nvme0n1 | grep -i temp

# ──── Monitoraggio automatico ────

# smartd: daemon per monitoraggio continuo
# /etc/smartd.conf:
# /dev/sda -a -W 5,45,55 -m admin@example.com -M exec /usr/share/smartmontools/smartd_warning.sh
# -W 5,45,55: avvisa se temp cambia >5°C, warn a 45°C, crit a 55°C
# -m: email su errore
sudo systemctl enable --now smartd

# Script di controllo rapido per tutti i dischi
for dev in /dev/sd? /dev/nvme?n1; do
  echo "=== $dev ==="
  if [[ "$dev" == /dev/nvme* ]]; then
    sudo nvme smart-log "$dev" 2>/dev/null | grep -E "percentage_used|available_spare|data_units_written"
  else
    sudo smartctl -A "$dev" 2>/dev/null | grep -E "Reallocated|Wear_Level|Life_Left|LBAs_Written"
  fi
done
```

**Soglie di intervento:** percentage_used > 80% o available_spare < spare_threshold → pianificare sostituzione. Reallocated_Sector_Ct in crescita costante → backup immediato e sostituzione. media_errors > 0 su NVMe → indagine urgente.

---

## Crittografia Disco — LUKS e dm-crypt

### Concetti

```
 ┌─────────────────────────────┐
 │   Filesystem (ext4, XFS)    │
 └──────────────┬──────────────┘
                │
 ┌──────────────▼──────────────┐
 │   dm-crypt (device-mapper)  │  Crittografia trasparente
 │   /dev/mapper/luks-xxx      │  a livello di blocco
 └──────────────┬──────────────┘
                │
 ┌──────────────▼──────────────┐
 │   LUKS Header + Key Slots   │  8 slot per passphrase/keyfile
 │   (primo 2-16 MB del disco) │  Metadati crittografici
 └──────────────┬──────────────┘
                │
 ┌──────────────▼──────────────┐
 │   Disco/Partizione fisica   │
 │   /dev/sdb1                 │
 └─────────────────────────────┘
```

### Ciclo di Vita LUKS

```bash
# === CREAZIONE ===
# Formattare una partizione con LUKS
sudo cryptsetup luksFormat /dev/sdb1
# Chiede conferma (YES maiuscolo) e passphrase

# Opzioni raccomandate per LUKS2
sudo cryptsetup luksFormat --type luks2 \
  --cipher aes-xts-plain64 \
  --key-size 512 \
  --hash sha512 \
  --iter-time 5000 \
  /dev/sdb1
# --type luks2     = formato moderno (default su distro recenti)
# --cipher         = algoritmo (aes-xts-plain64 è standard)
# --key-size 512   = 256 bit effettivi per AES-XTS
# --hash sha512    = hash per derivazione chiave
# --iter-time 5000 = millisecondi per PBKDF2 (anti brute-force)

# === APERTURA ===
sudo cryptsetup luksOpen /dev/sdb1 crypt_data
# Oppure con nome esplicito:
sudo cryptsetup open --type luks /dev/sdb1 crypt_data
# Crea /dev/mapper/crypt_data

# === FILESYSTEM E MOUNT ===
sudo mkfs.ext4 /dev/mapper/crypt_data
sudo mount /dev/mapper/crypt_data /mnt/encrypted

# === CHIUSURA ===
sudo umount /mnt/encrypted
sudo cryptsetup luksClose crypt_data

# === MOUNT AUTOMATICO AL BOOT ===
# /etc/crypttab
# crypt_data  UUID=abc123...  none  luks
# Poi in /etc/fstab:
# /dev/mapper/crypt_data  /mnt/encrypted  ext4  defaults  0  2

# Con keyfile (per mount senza interazione)
sudo dd if=/dev/urandom of=/root/luks_keyfile bs=4096 count=1
sudo chmod 400 /root/luks_keyfile
sudo cryptsetup luksAddKey /dev/sdb1 /root/luks_keyfile
# /etc/crypttab:
# crypt_data  UUID=abc123...  /root/luks_keyfile  luks
```

### Gestione Chiavi e Key Slot

```bash
# LUKS supporta fino a 8 key slot (LUKS1) o 32 (LUKS2)
# Ogni slot può contenere una passphrase o un keyfile diverso

# Visualizzare lo stato dei key slot
sudo cryptsetup luksDump /dev/sdb1

# Aggiungere una nuova passphrase (occupa un nuovo slot)
sudo cryptsetup luksAddKey /dev/sdb1
# Chiede prima la passphrase esistente, poi la nuova

# Aggiungere un keyfile
sudo cryptsetup luksAddKey /dev/sdb1 /root/luks_keyfile

# Rimuovere una passphrase (per slot)
sudo cryptsetup luksRemoveKey /dev/sdb1
# Chiede la passphrase da rimuovere

# Rimuovere per slot number
sudo cryptsetup luksKillSlot /dev/sdb1 1

# Cambiare passphrase
sudo cryptsetup luksChangeKey /dev/sdb1

# Testare se una passphrase funziona (senza aprire)
sudo cryptsetup luksDump /dev/sdb1 --dump-master-key
# Oppure tentare di aprire con --test-passphrase
sudo cryptsetup open --test-passphrase /dev/sdb1
```

### Backup e Recovery LUKS Header

```bash
# CRITICO: se l'header LUKS viene corrotto (primo 2-16 MB del disco),
# TUTTI I DATI SONO IRRECUPERABILI. Nessun backup dell'header = rischio totale.

# Backup dell'header
sudo cryptsetup luksHeaderBackup /dev/sdb1 \
  --header-backup-file /root/luks_header_sdb1.bak
# Conservare il backup OFFLINE (USB separato, cassaforte)

# Restore dell'header
sudo cryptsetup luksHeaderRestore /dev/sdb1 \
  --header-backup-file /root/luks_header_sdb1.bak

# Header detached (header separato dal disco dati)
# Vantaggiabile se il disco viene rubato: senza header = dati inaccessibili
sudo cryptsetup luksFormat --header /root/header_detached.img /dev/sdb1
sudo cryptsetup open --header /root/header_detached.img /dev/sdb1 crypt_data

# Dimensione header LUKS2: fino a 16 MiB (configurable con --luks2-metadata-size)
```

### Full Disk Encryption in Pratica

```bash
# === Crittografia disco OS completo (tipico setup) ===
# Layout consigliato:
# /dev/sda1  → /boot/efi  (FAT32, 512M, non crittografato)
# /dev/sda2  → /boot      (ext4, 1G, non crittografato)
# /dev/sda3  → LUKS → LVM:
#                 vg_crypt/lv_root → /
#                 vg_crypt/lv_swap → swap
#                 vg_crypt/lv_home → /home

# Setup manuale (post-installazione è complesso — preferire installer)
sudo cryptsetup luksFormat /dev/sda3
sudo cryptsetup open /dev/sda3 crypt_lvm
sudo pvcreate /dev/mapper/crypt_lvm
sudo vgcreate vg_crypt /dev/mapper/crypt_lvm
sudo lvcreate -L 50G -n lv_root vg_crypt
sudo lvcreate -L 8G -n lv_swap vg_crypt
sudo lvcreate -l 100%FREE -n lv_home vg_crypt

# Benchmark crittografia (impatto performance)
sudo cryptsetup benchmark
# Algorithm |  Key | Encryption |  Decryption
# aes-xts    512b   3000.0 MiB/s  3200.0 MiB/s  ← con AES-NI hardware
# L'overhead su CPU moderna con AES-NI è < 5%.
# Senza AES-NI: overhead 20-40%.
```

---

## dm-integrity — Integrità a Livello Blocco

dm-integrity è un target device-mapper che aggiunge tag di integrità a ogni settore scritto su disco. Rileva corruzione silenziosa (bit rot) che filesystem tradizionali come ext4 e XFS non possono individuare. Può operare standalone o in combinazione con dm-crypt per cifratura autenticata (AEAD).

### Modalità operative

| Modalità | Flag | Pro | Contro |
|---|---|---|---|
| Journal (default) | `--journal-integrity` | Atomicità garantita, no corruzione dopo crash | Overhead I/O ~30-50%, journal occupa spazio |
| Bitmap | `--integrity-bitmap-mode` | Avvio rapido, overhead ridotto | Dopo crash non-pulito serve verifica completa |

### Algoritmi di integrità

| Algoritmo | Tag size | Velocità | Uso |
|---|---|---|---|
| crc32c | 4 byte | Molto veloce | Default, rileva errori accidentali |
| xxhash64 | 8 byte | Veloce | Alternativa a crc32c con meno collisioni |
| sha256 | 32 byte | Lento | Sicurezza crittografica |
| hmac-sha256 | 32 byte | Lento | Integrità autenticata (richiede chiave) |

```bash
# ──── Installazione ────
sudo apt install integritysetup        # Parte di cryptsetup

# ──── Standalone: solo integrità ────

# Formattare dispositivo con integrità (crc32c, journal mode)
sudo integritysetup format /dev/sdc

# Aprire il dispositivo integrity
sudo integritysetup open /dev/sdc integrity_disk

# Il device /dev/mapper/integrity_disk è ora protetto
# Creare filesystem normalmente
sudo mkfs.ext4 /dev/mapper/integrity_disk
sudo mount /dev/mapper/integrity_disk /mnt/integrity

# Con algoritmo specifico e bitmap mode (più veloce)
sudo integritysetup format --integrity sha256 \
  --integrity-bitmap-mode /dev/sdc
sudo integritysetup open --integrity sha256 \
  --integrity-bitmap-mode /dev/sdc integrity_sha

# ──── Combinazione dm-crypt + dm-integrity (AEAD) ────

# Cifratura autenticata: ogni settore è cifrato E verificato
# dm-crypt gestisce la cifratura, dm-integrity i tag
# Il risultato è protezione contro manomissione E corruzione

# Metodo 1: LUKS2 con integrità integrata
sudo cryptsetup luksFormat --type luks2 \
  --cipher aes-xts-plain64 \
  --integrity hmac-sha256 \
  /dev/sdc

sudo cryptsetup open /dev/sdc crypt_integrity
sudo mkfs.xfs /dev/mapper/crypt_integrity
sudo mount /dev/mapper/crypt_integrity /mnt/sicuro

# Metodo 2: dm-integrity esplicito sotto dm-crypt
# (più controllo, stessa protezione)
sudo integritysetup format --integrity hmac-sha256 \
  --integrity-key-size 32 --integrity-key-file /root/hmac.key \
  /dev/sdc
sudo integritysetup open --integrity hmac-sha256 \
  --integrity-key-size 32 --integrity-key-file /root/hmac.key \
  /dev/sdc int_layer
sudo cryptsetup luksFormat /dev/mapper/int_layer
sudo cryptsetup open /dev/mapper/int_layer crypt_layer

# ──── Monitoraggio ────

# Stato dispositivo integrity
sudo integritysetup status integrity_disk
# Mostra: algoritmo, tag size, settori protetti, journal size

# I/O errors da integrità appaiono in dmesg:
# "device-mapper: integrity: ...checksum failed"
sudo dmesg | grep "integrity"

# Chiusura
sudo umount /mnt/integrity
sudo integritysetup close integrity_disk
```

**Overhead:** dm-integrity con journal aggiunge ~30-50% overhead in scrittura e ~4-32 byte per settore (dipende dall'algoritmo). Per storage dove l'integrità dati è critica (backup, archivi, database) il compromesso è accettabile. Per workload ad alte IOPS (database transazionali), valutare bitmap mode o affidarsi al checksum del filesystem (ZFS, Btrfs).

**dm-integrity vs checksum filesystem:** dm-integrity opera sotto il filesystem, protegge qualsiasi filesystem (anche ext4/XFS che non hanno checksum nativi). ZFS e Btrfs hanno checksum integrati e non necessitano di dm-integrity.

---

## Quote Disco

Le quote limitano l'uso dello spazio disco per utente o gruppo.

```bash
# Abilitare quote (ext4)
# In fstab aggiungere opzioni: usrquota,grpquota
# UUID=xxx /home ext4 defaults,usrquota,grpquota 0 2
sudo mount -o remount /home
sudo quotacheck -cugm /home        # Crea file quote
sudo quotaon /home                 # Abilita

# Impostare quote per utente
sudo edquota -u username
# Oppure in modo non-interattivo:
sudo setquota -u username 500000 600000 0 0 /home
# soft=500MB, hard=600MB, no limiti inode

# Verificare
sudo quota -u username             # Quote utente
sudo repquota -a                   # Report tutte le quote

# Grace period (tempo per rientrare dal soft limit)
sudo edquota -t                    # Modifica grace period

# Quote XFS (più integrate)
# Mount con: uquota,gquota,pquota (project quota)
sudo xfs_quota -x -c 'limit bsoft=500m bhard=600m username' /home
sudo xfs_quota -x -c 'report -h' /home
```

---

## Best Practices

1. **LVM su tutto**: usare LVM per quasi tutti i filesystem (tranne /boot). La flessibilità di ridimensionamento e snapshot ripaga ampiamente la minima complessità aggiuntiva
2. **UUID in fstab**: usare sempre UUID (o label) in fstab, mai `/dev/sdX`. L'ordine dei dischi può cambiare tra i riavvii
3. **Monitorare lo spazio**: `df -h` e alert automatici quando lo spazio supera l'80%. Un filesystem pieno al 100% causa problemi gravi
4. **Scrub periodico**: per ZFS e Btrfs, eseguire scrub settimanale. Rileva e corregge la corruzione dati silente (bit rot)
5. **Testare i restore**: gli snapshot e i backup sono inutili se non si verifica regolarmente che il restore funzioni
6. **RAID non è backup**: RAID protegge dal guasto hardware di un disco, non dalla cancellazione accidentale, dalla corruzione software o dal ransomware. Servono backup separati
7. **Separare i dati**: filesystem separati per `/`, `/home`, `/var`, `/var/log`. Un `/var/log` pieno non deve bloccare il sistema operativo
8. **SMART monitoring sempre attivo**: abilitare `smartd` su ogni server. Un disco che mostra Reallocated_Sector_Ct > 0 va sostituito proattivamente
9. **TRIM settimanale per SSD**: abilitare il timer `fstrim.timer`. Senza TRIM le performance SSD degradano nel tempo
10. **Backup header LUKS**: se si usa crittografia disco, il backup dell'header LUKS è obbligatorio. Senza header = dati irrecuperabili
11. **Allineamento partizioni**: verificare che le partizioni inizino a multipli di 1 MiB (2048 settori). Disallineamento = penalità performance su SSD e Advanced Format HDD
12. **LVM thin pool sotto 80%**: monitorare i thin pool e configurare autoextend. Oltre 80% le performance CoW degradano rapidamente

---

## Troubleshooting

**"No space left on device" ma df mostra spazio** → Possibili cause: (1) inode esauriti — `df -i` per verificare, (2) file cancellati ma ancora aperti da un processo — `lsof +D /mount | grep deleted`, (3) spazio riservato a root — `tune2fs -m 0` per azzerare temporaneamente.

**"Filesystem read-only"** → Errore del filesystem o disco guasto. `dmesg | tail` per errori kernel. Se ext4: `sudo e2fsck -f /dev/sdXN` (da smontato). Se XFS: `sudo xfs_repair /dev/sdXN`. Verificare anche la salute del disco con `smartctl -a /dev/sdX`.

**"LVM: Insufficient free space"** → `sudo vgs` per vedere lo spazio libero nel VG. Se pieno: aggiungere un disco (`pvcreate` + `vgextend`). Se thin pool pieno: espandere con `lvextend`.

**"mdadm: array degradato"** → `cat /proc/mdstat` mostra lo stato. Un disco è guasto: sostituire fisicamente, poi `mdadm --add /dev/md0 /dev/sdX1` per avviare il rebuild. Monitorare con `watch cat /proc/mdstat`.

**"NFS: mount.nfs: access denied"** → Verificare: (1) l'IP del client è nel range dell'export, (2) `exportfs -v` sul server, (3) firewall aperto porta 2049/tcp, (4) `showmount -e server` dal client. Se NFSv4: verificare ID mapping e permessi directory.

**"NFS: Stale file handle"** → Il server ha ri-esportato o il filesystem sottostante è cambiato. Smontare e rimontare: `sudo umount -l /mnt/nfs && sudo mount /mnt/nfs`. Se persistente: verificare che l'export sia attivo (`exportfs -v`) e che il filesystem non sia stato ricreato (UUID cambiato).

**"LVM thin pool pieno al 100%"** → I thin volume vanno in errore I/O. NON rimuovere nulla. (1) Espandere il pool: `sudo lvextend -L +50G vg/thinpool`, (2) Disattivare e riattivare i thin volume: `lvchange -an/-ay`, (3) Verificare i filesystem con fsck. Per prevenire: configurare autoextend in lvm.conf (threshold=80, percent=20).

**"ZFS pool DEGRADED"** → `sudo zpool status` identifica il disco guasto. Sostituire: `sudo zpool replace tank /dev/guasto /dev/nuovo`. Se l'errore è correctable: `sudo zpool scrub tank` corregge automaticamente. Se FAULTED: il pool non è accessibile finché non si ripristina la ridondanza.

**"Btrfs: balance start stallo / durata infinita"** → Balance su filesystem quasi pieno è lentissimo. (1) Cancellare: `sudo btrfs balance cancel /mnt`, (2) Liberare spazio (eliminare snapshot vecchi), (3) Rifare balance con filtro: `sudo btrfs balance start -dusage=50 /mnt` per processare solo chunk poco usati.

**"iSCSI: connection timeout / login failed"** → Verificare: (1) connettività TCP alla porta 3260 (`telnet target 3260`), (2) IQN del client corrisponde all'ACL del target, (3) CHAP credentials corrette in `/etc/iscsi/iscsid.conf`, (4) target service attivo (`systemctl status target`).

**"LUKS: No key available with this passphrase"** → Passphrase sbagliata o header corrotto. (1) Provare tutte le passphrase conosciute, (2) Verificare header: `sudo cryptsetup luksDump /dev/sdb1` — se fallisce l'header è corrotto, (3) Ripristinare da header backup: `cryptsetup luksHeaderRestore /dev/sdb1 --header-backup-file backup.img`.

**"SMART: FAILING_NOW / Current_Pending_Sector > 0"** → Disco in fase di guasto. (1) Backup immediato dei dati, (2) Se in RAID: marcare come guasto e sostituire (`mdadm --fail`), (3) Non fidarsi di un disco con settori pending per dati importanti, (4) Ordinare sostituzione e pianificare la migrazione.

**"mdadm: rebuild molto lento"** → Il rebuild compete con I/O normale. (1) Aumentare velocità minima: `echo 200000 > /proc/sys/dev/raid/speed_limit_min`, (2) Aumentare velocità massima: `echo 500000 > /proc/sys/dev/raid/speed_limit_max`, (3) Ridurre carico applicativo durante il rebuild, (4) Usare bitmap per resync parziale se possibile.

**"fstrim: errore discard not supported"** → La catena completa deve supportare TRIM: disco → partizione → dm-crypt → LVM → filesystem. Verificare: `lsblk --discard` (DISC-MAX > 0 per ogni livello). Per LVM: `issue_discards = 1` in lvm.conf. Per LUKS: `discard` in crypttab.

**"LVM: metadata corruption / inconsistent"** → (1) NON scrivere sul disco, (2) `sudo vgcfgrestore --list vg_data` per vedere i backup automatici dei metadati, (3) Ripristinare: `sudo vgcfgrestore -f /etc/lvm/archive/vg_data_xxxxx.vg vg_data`, (4) Riattivare: `sudo vgchange -ay vg_data`.

**"RAID: superblock mismatch / cannot assemble"** → (1) Esaminare i superblock: `sudo mdadm --examine /dev/sd{b,c,d}1`, (2) Verificare che gli UUID corrispondano, (3) Assemblare forzando: `sudo mdadm --assemble --force /dev/md0 /dev/sdb1 /dev/sdc1`, (4) Se i superblock sono diversi il disco potrebbe essere stato usato in un altro array.

**"Tabella partizioni persa"** → (1) NON scrivere sul disco, (2) Usare `testdisk` per recuperare: `sudo testdisk /dev/sdb`, (3) Selezionare tipo tabella (GPT/MBR), (4) Analyse → Quick Search → Deep Search, (5) Scrivere la tabella recuperata. Per GPT: provare anche il backup header con `gdisk /dev/sdb` → recovery.

**"Disk I/O 100% util ma basso throughput"** → Collo di bottiglia tipico. (1) `iostat -xz 2`: controllare `await` (latenza) e `avgqu-sz` (coda), (2) Se await alto + coda lunga = disco saturo, (3) Identificare il processo: `sudo iotop -o`, (4) Possibili cause: random I/O su HDD, thin pool frammentato, filesystem quasi pieno, bad blocks. Soluzione dipende dalla causa root.

**"Disco sparito dopo reboot / ordine /dev/sd* cambiato"** → (1) Usare UUID o /dev/disk/by-id in fstab e mdadm.conf, (2) Verificare cavi e controller: `lsblk`, `dmesg | grep sd`, (3) Se il disco è visibile in BIOS ma non nel kernel: controllare il driver AHCI/NVMe, (4) Per SCSI/SAS: `echo "- - -" > /sys/class/scsi_host/hostX/scan` per rescan.

**"Btrfs: ENOSPC nonostante spazio disponibile"** → Btrfs alloca chunk di spazio. (1) `sudo btrfs filesystem usage /mnt` per vedere chunk allocati vs usati, (2) Lo spazio "available" potrebbe essere zero anche se "used" è basso, (3) Balance per consolidare: `sudo btrfs balance start -dusage=10 /mnt`, (4) Eliminare snapshot per liberare chunk.

**"ZFS ARC usa troppa RAM"** → ARC è progettato per usare RAM disponibile. (1) Verificare dimensione: `arc_summary | head -20`, (2) Limitare: `echo 8589934592 > /sys/module/zfs/parameters/zfs_arc_max`, (3) Rendere persistente: aggiungere `options zfs zfs_arc_max=8589934592` in `/etc/modprobe.d/zfs.conf`, (4) Rigenerare initramfs.

**"Samba: NT_STATUS_ACCESS_DENIED"** → (1) Verificare utente Samba esiste: `sudo pdbedit -L`, (2) Permessi directory filesystem: l'utente Linux deve avere accesso, (3) Configurazione share in smb.conf: `valid users`, `write list`, (4) SELinux/AppArmor: `sudo setsebool -P samba_enable_home_dirs on` o verificare i contesti.

**"GlusterFS: split-brain"** → (1) Identificare: `sudo gluster volume heal vol_data info split-brain`, (2) Risolvere manualmente: scegliere il brick corretto come sorgente, (3) `sudo gluster volume heal vol_data split-brain source-brick node1:/brick/data`, (4) Prevenire: usare arbiter volume (3 brick, terzo solo metadati).

---

## FAQ

**D: Quando usare LVM vs partizioni dirette?**
R: Usare LVM quasi sempre. Le partizioni dirette sono rigide: per ridimensionarle serve spazio contiguo e spesso smontare. LVM permette ridimensionamento online, snapshot, migrazione tra dischi. Le uniche eccezioni: `/boot` (troppo presto nel boot per LVM su alcune configurazioni) e filesystem disposable temporanei.

**D: ZFS o Btrfs?**
R: ZFS è più maturo e affidabile per storage critico (server, NAS, backup). Btrfs è più integrato nel kernel Linux e più semplice da gestire per desktop e uso generale. ZFS eccelle con pool grandi e molti dischi. Btrfs RAID 5/6 ha bug noti e non è raccomandato — usare solo RAID 1 o 10 con Btrfs. Per produzione con RAID: ZFS. Per desktop con snapshot: Btrfs.

**D: RAID 5 o RAID 6?**
R: Con dischi moderni da 4TB+ il rebuild di RAID 5 richiede ore, durante le quali un secondo guasto significa perdita totale. RAID 6 (o RAIDZ2 per ZFS) tollera 2 guasti simultanei. Regola pratica: RAID 5 solo con dischi < 2TB e max 4 dischi. Altrimenti RAID 6 o RAID 10.

**D: Il journal ext4 rallenta le scritture?**
R: Minimamente. Il journal aggiunge una scrittura extra, ma protegge dalla corruzione dopo crash. L'overhead è tipicamente < 5%. Non disabilitare il journal a meno che si tratti di un filesystem temporaneo e dispensabile. Per performance massima, usare `data=writeback` (journal solo metadati) piuttosto che rimuovere il journal.

**D: Come scegliere il record size ZFS?**
R: Default 128K è buono per uso generale. Per database (random read/write piccoli): 8K-16K. Per file grandi (video, backup): 1M. Per VM disk images: 64K. Il record size si imposta per dataset: `zfs set recordsize=16K tank/database`. Cambiare il record size non modifica i blocchi esistenti, solo quelli nuovi.

**D: Quanto spazio riservare per SSD over-provisioning?**
R: I produttori già includono OP internamente (7-28%). Per uso enterprise, lasciare un 10-20% addizionale non partizionato. Esempio: su SSD da 1TB, partizionare solo 800-900GB. Questo migliora la durata e le performance sotto carico sostenuto. Per uso desktop il OP del produttore è sufficiente.

**D: Posso usare ZFS come root filesystem?**
R: Sì, ma richiede configurazione specifica. Ubuntu lo supporta con `zsys`. Su altre distro serve configurare initramfs per importare il pool ZFS al boot. Layout tipico: pool `rpool` con dataset per root, home, var. Si ottengono boot snapshot e rollback. La complessità è superiore a ext4 su LVM.

**D: dm-crypt/LUKS rallenta il disco?**
R: Su CPU moderne con AES-NI (tutte dal 2010+), l'overhead è < 5% in throughput. La latenza aggiuntiva è trascurabile. Senza AES-NI l'overhead può essere 20-40%. Verificare: `grep -o aes /proc/cpuinfo | head -1`. Se presente, la crittografia è praticamente gratuita.

**D: Come migrare i dati da un filesystem a un altro senza downtime?**
R: Con LVM: (1) creare un nuovo LV con il filesystem target, (2) montare entrambi, (3) copiare con `rsync -aAXv`, (4) fare un sync finale (`rsync --delete`), (5) aggiornare fstab e swap i mount point. Con ZFS: `zfs send/receive` per migrare tra pool. Downtime minimo durante lo switch finale del mount.

**D: Come funziona il RAID write hole e come prevenirlo?**
R: In RAID 5/6, se il sistema crasha durante una scrittura, i dati e la parità possono essere inconsistenti (write hole). mdadm mitiga con bitmap. ZFS non ha write hole perché usa CoW (non aggiorna mai i blocchi in-place). Btrfs RAID 5/6 ha il write hole ed è per questo che non è raccomandato. Per prevenire: usare ZFS RAIDZ, o mdadm con bitmap, o batteria BBU nel controller RAID hardware.

**D: Quando usare iSCSI vs NFS?**
R: iSCSI espone un block device: il client ha controllo totale sul filesystem. Ideale per: VM disk, database, cluster storage che richiede accesso a blocchi. NFS espone un filesystem già formato: il server gestisce il filesystem. Ideale per: home directory condivise, file sharing, build farm. NFS è più semplice; iSCSI è più flessibile e performante per workload specifici.

**D: Come interpretare l'output di iostat?**
R: Le colonne critiche sono: `%util` (saturazione: 100% = disco al limite), `await` (latenza media: > 20ms su SSD o > 50ms su HDD = problema), `avgqu-sz` (coda: > 1 = richieste in attesa). Se `%util` è alto ma `r/s + w/s` è basso, il disco è lento o gestisce I/O random. Se `await` è alto con coda lunga, il disco non riesce a smaltire le richieste.

**D: Come gestire lo storage in un ambiente con molti dischi (> 20)?**
R: (1) Usare `/dev/disk/by-id/` per identificare i dischi fisici in modo persistente, (2) Documentare la mappatura disco-slot con etichette o un inventario, (3) Per ZFS/Ceph: usare `by-id` nella configurazione, (4) Abilitare SMART monitoring su tutti i dischi, (5) Considerare Ceph o GlusterFS per gestione distribuita, (6) Usare hotspare per rebuild automatico.

**D: Cos'è il thin provisioning e quando usarlo?**
R: Il thin provisioning alloca storage virtualmente senza consumare spazio fisico finché non viene scritto. Utile per: ambienti con molte VM (allocare 100GB a ciascuna senza avere 100GB × N dischi), storage lab/dev, qualsiasi scenario dove l'uso reale è molto inferiore all'allocazione. Rischio: se lo spazio fisico si esaurisce e l'autoextend non è configurato, tutti i thin volume vanno in errore.

**D: GlusterFS o Ceph per storage distribuito?**
R: GlusterFS è più semplice da installare e gestire, buono per file sharing distribuito e ambienti medio-piccoli. Ceph è più complesso ma offre object storage (S3), block device (RBD) e filesystem (CephFS) in un sistema unificato, ideale per cloud privato, OpenStack, Kubernetes. Per pochi nodi e file sharing: GlusterFS. Per infrastruttura cloud-scale: Ceph.
