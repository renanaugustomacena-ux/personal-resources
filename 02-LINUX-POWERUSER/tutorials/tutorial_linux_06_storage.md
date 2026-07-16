# Tutorial Linux 06 — Storage: LVM, RAID, filesystem, fdisk

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** fdisk/gdisk, mkfs, LVM (pv/vg/lv), RAID software, /etc/fstab avanzato
> **Prerequisiti:** `tutorial_linux_01_filesystem.md`, `tutorial_linux_05_networking.md`
> **Durata stimata:** 14-18 ore

---

## Mappa concettuale

```
Storage Linux
│
├── Partizioni
│   ├── fdisk — MBR (BIOS, <2TB)
│   ├── gdisk/parted — GPT (UEFI, >2TB)
│   └── lsblk, blkid, df, du
│
├── Filesystem
│   ├── ext4 — standard Linux
│   ├── xfs — alta performance, grandi file
│   ├── btrfs — CoW, snapshot, compressione
│   └── vfat/ntfs — interoperabilità
│
├── LVM (Logical Volume Manager)
│   ├── PV — Physical Volume (disco/partizione)
│   ├── VG — Volume Group (pool di storage)
│   ├── LV — Logical Volume (volume virtuale)
│   └── Snapshot, thin provisioning
│
├── RAID Software (mdadm)
│   ├── RAID 0 — stripe (performance, no ridondanza)
│   ├── RAID 1 — mirror (ridondanza)
│   ├── RAID 5 — stripe con parity
│   └── RAID 6 — stripe con doppia parity
│
└── Mounting avanzato
    ├── /etc/fstab con opzioni
    ├── LUKS — crittografia disco
    └── NFS/CIFS mount
```

---

# Parte A — Partizioni e dischi

---

## A1. Esplorazione dischi

```bash
# Lista tutti i block device
lsblk
# NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINTS
# sda      8:0    0  100G  0 disk
# ├─sda1   8:1    0    1G  0 part /boot
# ├─sda2   8:2    0    2G  0 part [SWAP]
# └─sda3   8:3    0   97G  0 part /

# Dettagli con filesystem
lsblk -f
# Colonne: NAME FSTYPE LABEL UUID FSAVAIL FSUSE% MOUNTPOINTS

# UUID e label
blkid /dev/sda1
# /dev/sda1: UUID="abc-123" LABEL="boot" TYPE="ext4"

# Geometria dischi
fdisk -l                   # tutti i dischi
fdisk -l /dev/sdb          # disco specifico

# Uso spazio
df -h                      # spazio filesystem
df -i                      # inode usage
du -sh /var/*              # spazio per directory
du -sh /* 2>/dev/null | sort -h | tail -20
```

---

## A2. Partizionamento con fdisk (MBR/GPT)

```bash
# fdisk — interattivo
fdisk /dev/sdb
# Comandi nel menu:
# g — crea tabella GPT (invece di m per MBR)
# n — nuova partizione
# p — stampa tabella
# d — cancella partizione
# t — cambia tipo (83=Linux, 82=swap, 8e=LVM, fd=RAID)
# w — scrivi e esci
# q — esci senza salvare

# Esempio non interattivo (scripting)
parted /dev/sdb --script \
    mklabel gpt \
    mkpart primary ext4 1MiB 50GiB \
    mkpart primary linux-swap 50GiB 54GiB \
    mkpart primary 54GiB 100%

# Dopo la partizione, aggiorna il kernel
partprobe /dev/sdb

# Crea filesystem
mkfs.ext4 /dev/sdb1                    # ext4
mkfs.ext4 -L "dati" /dev/sdb1         # con label
mkfs.xfs /dev/sdb2                     # XFS
mkfs.btrfs /dev/sdb3                   # btrfs
mkswap /dev/sdb4                       # swap

# Attiva swap
swapon /dev/sdb4
swapoff /dev/sdb4
swapon --show
```

> **Analogia:** Un disco fisico è come un pezzo di terreno non delimitato. Le partizioni sono i lotti: definisci i confini, assegni le destinazioni d'uso. LVM è come comprare lotti e poi decidere muri divisori flessibili: puoi spostare confini e unire lotti senza dover traslocare. Il filesystem è la pavimentazione: rende il terreno utilizzabile per costruire sopra.

---

# Parte B — LVM

---

## B1. Creare volumi LVM

```bash
# 1. Prepara i Physical Volume (PV)
pvcreate /dev/sdb /dev/sdc
pvs                    # lista PV
pvdisplay /dev/sdb     # dettagli

# 2. Crea Volume Group (VG) — pool di storage
vgcreate dati-vg /dev/sdb /dev/sdc
vgs                    # lista VG
vgdisplay dati-vg      # dettagli

# 3. Crea Logical Volume (LV)
lvcreate -L 50G -n web-lv dati-vg      # 50GB
lvcreate -l 100%FREE -n db-lv dati-vg  # tutto lo spazio rimanente
lvs                    # lista LV
lvdisplay /dev/dati-vg/web-lv

# Il device path del LV è:
# /dev/dati-vg/web-lv  o  /dev/mapper/dati--vg-web--lv

# 4. Formatta e monta
mkfs.ext4 /dev/dati-vg/web-lv
mkdir /var/www
mount /dev/dati-vg/web-lv /var/www
```

---

## B2. Ridimensionamento a caldo

```bash
# Espandi LV (online, senza unmount su ext4/xfs)
lvextend -L +10G /dev/dati-vg/web-lv          # aggiungi 10GB
lvextend -l +100%FREE /dev/dati-vg/web-lv     # tutto lo spazio libero

# Dopo lvextend, ridimensiona il filesystem
resize2fs /dev/dati-vg/web-lv          # ext4
xfs_growfs /var/www                     # xfs (usa mountpoint)

# Oppure in un solo comando:
lvextend -r -L +10G /dev/dati-vg/web-lv  # -r = resize filesystem automatico

# Riduci LV (solo offline, e solo ext4)
# 1. Smonta
umount /var/www

# 2. Verifica filesystem
e2fsck -f /dev/dati-vg/web-lv

# 3. Riduci filesystem a 40G
resize2fs /dev/dati-vg/web-lv 40G

# 4. Riduci LV
lvreduce -L 40G /dev/dati-vg/web-lv

# 5. Rimonta
mount /dev/dati-vg/web-lv /var/www
```

---

## B3. Snapshot LVM

```bash
# Crea snapshot (CoW — Copy on Write)
lvcreate -L 5G -s -n web-snap /dev/dati-vg/web-lv
# -s = snapshot, -L = dimensione area CoW

# Monta snapshot (read-only per backup)
mkdir /mnt/snap
mount -o ro /dev/dati-vg/web-snap /mnt/snap

# Backup dal snapshot (senza bloccare il servizio)
rsync -av /mnt/snap/ /backup/web/

# Rimuovi snapshot
umount /mnt/snap
lvremove /dev/dati-vg/web-snap

# Ripristino da snapshot
# ATTENZIONE: distrugge i dati correnti del LV!
lvconvert --merge /dev/dati-vg/web-snap
```

---

# Parte C — RAID software con mdadm

---

## C1. Creare array RAID

```bash
# Installa mdadm
apt install mdadm

# RAID 1 (mirror) con 2 dischi
mdadm --create /dev/md0 \
    --level=1 \
    --raid-devices=2 \
    /dev/sdb /dev/sdc

# RAID 5 con 3 dischi
mdadm --create /dev/md1 \
    --level=5 \
    --raid-devices=3 \
    /dev/sdd /dev/sde /dev/sdf

# Monitora la costruzione
cat /proc/mdstat
# Personalities : [raid1]
# md0 : active raid1 sdb[0] sdc[1]
#       100G blocks super 1.2 [2/2] [UU]
#       [=========>...........] resync = 47.6% (49888/100000) finish=2.1min

# Salva configurazione
mdadm --detail --scan >> /etc/mdadm/mdadm.conf
update-initramfs -u   # aggiorna initrd

# Formatta e monta
mkfs.ext4 /dev/md0
mount /dev/md0 /data
```

---

## C2. Gestione RAID

```bash
# Stato array
mdadm --detail /dev/md0
cat /proc/mdstat

# Simula guasto disco
mdadm /dev/md0 --fail /dev/sdb

# Rimuovi disco guasto
mdadm /dev/md0 --remove /dev/sdb

# Aggiungi nuovo disco
mdadm /dev/md0 --add /dev/sdg
# La ricostruzione parte automaticamente

# Aggiungi hot spare
mdadm /dev/md0 --add /dev/sdh
# Se già 2/2, viene aggiunto come spare

# Ferma array (es. manutenzione)
mdadm --stop /dev/md0
mdadm --assemble /dev/md0 /dev/sdb /dev/sdc  # riassembla
```

---

# Parte D — /etc/fstab avanzato

---

## D1. Opzioni mount

```bash
# Formato /etc/fstab:
# <device> <mountpoint> <fstype> <options> <dump> <pass>

# UUID (raccomandato — non cambia al riconnettere)
UUID=abc-123  /var/www  ext4  defaults,noatime  0 2

# Label
LABEL=dati  /data  xfs  defaults  0 2

# LVM
/dev/dati-vg/web-lv  /var/www  ext4  defaults  0 2

# Opzioni comuni:
# defaults = rw,suid,dev,exec,auto,nouser,async
# noatime  = non aggiornare atime (performance)
# nodiratime = come noatime ma per directory
# noexec   = no esecuzione binari (sicurezza)
# nosuid   = ignora setuid bit
# ro       = read-only
# rw       = read-write
# user     = utenti possono montare
# nofail   = non fallire al boot se assente (es. USB)
# x-systemd.automount  = monta solo quando acceduto

# Tmpfs in RAM
tmpfs  /tmp  tmpfs  defaults,noatime,size=2G  0 0

# NFS
server:/export/dati  /mnt/nfs  nfs  nfsvers=4,_netdev,nofail  0 0

# Testa senza reboot
mount -a                   # monta tutto da fstab
mount -a --verbose         # verbose

# Opzione nofail — importante per disk non critici!
UUID=xyz  /backup  ext4  defaults,nofail  0 0
```

---

## D2. LUKS — crittografia disco

```bash
# Installa
apt install cryptsetup

# Crea volume LUKS
cryptsetup luksFormat /dev/sdb1
# Inserisci passphrase

# Apri il volume
cryptsetup luksOpen /dev/sdb1 dati-cifrati
# Ora accessibile come /dev/mapper/dati-cifrati

# Formatta e monta
mkfs.ext4 /dev/mapper/dati-cifrati
mount /dev/mapper/dati-cifrati /mnt/sicuro

# Chiudi il volume
umount /mnt/sicuro
cryptsetup luksClose dati-cifrati

# Mount automatico al boot con /etc/crypttab
# /etc/crypttab: <name> <device> <keyfile> <options>
dati-cifrati  UUID=xxx  none  luks

# /etc/fstab
/dev/mapper/dati-cifrati  /mnt/sicuro  ext4  defaults  0 2
```

---

# Parte E — Riepilogo

## Workflow tipico nuovo disco

```bash
# 1. Identifica il disco
lsblk
fdisk -l /dev/sdb

# 2. Partiziona
fdisk /dev/sdb
# g (GPT), n (nuova), w (scrivi)

# 3. Crea filesystem
mkfs.ext4 /dev/sdb1

# 4. Ottieni UUID
blkid /dev/sdb1

# 5. Crea mount point
mkdir -p /dati/backup

# 6. Aggiungi a fstab
echo 'UUID=abc-123  /dati/backup  ext4  defaults,nofail  0 2' >> /etc/fstab

# 7. Monta
mount -a
df -h /dati/backup
```

## Comandi LVM essenziali

| Livello | Crea | Lista | Dettagli | Rimuovi |
|---|---|---|---|---|
| PV | `pvcreate` | `pvs` | `pvdisplay` | `pvremove` |
| VG | `vgcreate` | `vgs` | `vgdisplay` | `vgremove` |
| LV | `lvcreate` | `lvs` | `lvdisplay` | `lvremove` |

## Prossimi passi

- `tutorial_linux_07_kernel.md` — moduli kernel, sysctl
- `tutorial_linux_08_performance.md` — vmstat, iostat, benchmarking
