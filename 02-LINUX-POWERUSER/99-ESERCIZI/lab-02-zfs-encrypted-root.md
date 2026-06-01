# Lab 02 — ZFS Encrypted Root con Auto-Unlock

> **Modulo di riferimento:** [25-zfs-guida-operativa.md](../25-zfs-guida-operativa.md), [06-storage.md](../06-storage.md)
> **Tempo stimato:** 2-3 ore
> **Livello:** proficient
> **Prerequisiti:** VM con 2 dischi (20 GB + 10 GB), completamento moduli 01, 06
> **Ultimo aggiornamento:** 2026-05-23

---

## Obiettivo

Installare un sistema Debian 12 con root filesystem su ZFS con cifratura nativa, auto-unlock via chiave su partizione separata, snapshot policy automatizzata e procedura di recovery documentata.

---

## Ambiente

- VM con 2 dischi virtuali:
  - `/dev/vda` (20 GB) — disco principale per ZFS
  - `/dev/vdb` (10 GB) — disco per chiave di unlock + backup
- 4 GB RAM minimo (per ARC)
- ISO Debian 12 (live o netinst)
- Accesso console

---

## Parte 1 — Preparazione Dischi (20 min)

### 1.1 Boot dalla live e installare ZFS

```bash
# Dalla live Debian
apt update
apt install -y debootstrap gdisk dkms dpkg-dev \
    linux-headers-$(uname -r) zfs-dkms zfsutils-linux

modprobe zfs
```

### 1.2 Partizionamento disco principale

```bash
# Pulire il disco
sgdisk --zap-all /dev/vda

# Creare partizioni
sgdisk -n1:1M:+512M    -t1:EF00 -c1:"EFI"    /dev/vda   # EFI System Partition
sgdisk -n2:0:+1G       -t2:BF01 -c2:"BOOT"   /dev/vda   # Boot pool (non cifrato)
sgdisk -n3:0:0         -t3:BF00 -c3:"ROOT"   /dev/vda   # Root pool (cifrato)

# Partizione per la chiave sul secondo disco
sgdisk --zap-all /dev/vdb
sgdisk -n1:1M:+64M     -t1:8300 -c1:"KEYPART" /dev/vdb
sgdisk -n2:0:0         -t2:8300 -c2:"BACKUP"  /dev/vdb
```

### 1.3 Formattare EFI

```bash
mkfs.vfat -F 32 -n EFI /dev/vda1
```

---

## Parte 2 — Creazione Pool ZFS (30 min)

### 2.1 Generare la chiave di cifratura

```bash
# Formattare partizione chiave
mkfs.ext4 -L KEYPART /dev/vdb1

# Montare e generare chiave
mkdir -p /mnt/keypart
mount /dev/vdb1 /mnt/keypart
dd if=/dev/urandom of=/mnt/keypart/rpool.key bs=32 count=1
chmod 000 /mnt/keypart/rpool.key
```

### 2.2 Creare il boot pool (non cifrato)

```bash
zpool create \
    -o ashift=12 \
    -o autotrim=on \
    -O acltype=posixacl \
    -O canmount=off \
    -O compression=lz4 \
    -O devices=off \
    -O normalization=formD \
    -O relatime=on \
    -O xattr=sa \
    -O mountpoint=/boot \
    bpool /dev/vda2
```

### 2.3 Creare il root pool (cifrato)

```bash
zpool create \
    -o ashift=12 \
    -o autotrim=on \
    -O acltype=posixacl \
    -O canmount=off \
    -O compression=zstd \
    -O dnodesize=auto \
    -O normalization=formD \
    -O relatime=on \
    -O xattr=sa \
    -O encryption=aes-256-gcm \
    -O keylocation=file:///mnt/keypart/rpool.key \
    -O keyformat=raw \
    -O mountpoint=/ \
    rpool /dev/vda3
```

### 2.4 Creare i dataset

```bash
# Root dataset con container structure
zfs create -o canmount=off -o mountpoint=none rpool/ROOT
zfs create -o canmount=noauto -o mountpoint=/ rpool/ROOT/debian
zfs mount rpool/ROOT/debian

# Dataset separati per gestione snapshot e quota
zfs create                                    rpool/home
zfs create -o mountpoint=/root               rpool/home/root
zfs create                                    rpool/var
zfs create -o com.sun:auto-snapshot=false     rpool/var/cache
zfs create                                    rpool/var/log
zfs create -o com.sun:auto-snapshot=false     rpool/var/tmp
zfs create -o com.sun:auto-snapshot=false     rpool/tmp

# Permessi tmp
chmod 1777 /mnt/rpool/tmp
chmod 1777 /mnt/rpool/var/tmp

# Boot dataset
zfs create -o canmount=off -o mountpoint=none bpool/BOOT
zfs create -o canmount=noauto -o mountpoint=/boot bpool/BOOT/debian
zfs mount bpool/BOOT/debian
```

### 2.5 Verificare il layout

```bash
zfs list -o name,mountpoint,encryption,keystatus
```

Output atteso:
```
NAME                MOUNTPOINT    ENCRYPTION       KEYSTATUS
rpool               /             aes-256-gcm      available
rpool/ROOT          none          aes-256-gcm      available
rpool/ROOT/debian   /             aes-256-gcm      available
rpool/home          /home         aes-256-gcm      available
rpool/var           /var          aes-256-gcm      available
rpool/var/log       /var/log      aes-256-gcm      available
...
bpool               /boot         off              -
```

---

## Parte 3 — Installazione Sistema (45 min)

### 3.1 Debootstrap

```bash
debootstrap bookworm /mnt/rpool

# Montare filesystem necessari
mount --bind /dev  /mnt/rpool/dev
mount --bind /dev/pts /mnt/rpool/dev/pts
mount --bind /proc /mnt/rpool/proc
mount --bind /sys  /mnt/rpool/sys

# Montare EFI
mkdir -p /mnt/rpool/boot/efi
mount /dev/vda1 /mnt/rpool/boot/efi

# Copiare la chiave nel sistema installato
mkdir -p /mnt/rpool/etc/zfs
cp /mnt/keypart/rpool.key /mnt/rpool/etc/zfs/rpool.key
chmod 000 /mnt/rpool/etc/zfs/rpool.key
```

### 3.2 Configurazione base in chroot

```bash
chroot /mnt/rpool /bin/bash

# Hostname
echo "zfs-lab" > /etc/hostname

# Timezone
ln -sf /usr/share/zoneinfo/Europe/Rome /etc/localtime

# Locale
apt install -y locales
echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
locale-gen

# Password root
passwd

# Installare kernel e ZFS
apt update
apt install -y linux-image-amd64 linux-headers-amd64 \
    zfs-initramfs zfs-dkms grub-efi-amd64 \
    systemd-timesyncd openssh-server

# Configurare chiave di auto-unlock per initramfs
echo "rpool /etc/zfs/rpool.key" > /etc/zfs/keylocation
```

### 3.3 Configurare auto-unlock in initramfs

```bash
# Script hook per caricare la chiave durante il boot
cat > /etc/initramfs-tools/hooks/zfs-keymount << 'HOOK_EOF'
#!/bin/sh
PREREQ=""
prereqs() { echo "$PREREQ"; }
case $1 in prereqs) prereqs; exit 0;; esac

. /usr/share/initramfs-tools/hook-functions

# Includere i tool necessari
copy_exec /sbin/blkid
copy_exec /bin/mount
copy_exec /bin/umount
mkdir -p "${DESTDIR}/etc/zfs"
HOOK_EOF
chmod 755 /etc/initramfs-tools/hooks/zfs-keymount

# Script per montare la partizione chiave e caricare la chiave
cat > /etc/initramfs-tools/scripts/local-top/zfs-keyload << 'SCRIPT_EOF'
#!/bin/sh
PREREQ=""
prereqs() { echo "$PREREQ"; }
case $1 in prereqs) prereqs; exit 0;; esac

# Montare la partizione con la chiave
mkdir -p /run/keypart
KEYDEV=$(blkid -l -t LABEL=KEYPART -o device)
if [ -n "$KEYDEV" ]; then
    mount -o ro "$KEYDEV" /run/keypart
    if [ -f /run/keypart/rpool.key ]; then
        cp /run/keypart/rpool.key /etc/zfs/rpool.key
        zfs load-key rpool 2>/dev/null || true
    fi
    umount /run/keypart
fi
SCRIPT_EOF
chmod 755 /etc/initramfs-tools/scripts/local-top/zfs-keyload

# Ricostruire initramfs
update-initramfs -c -k all
```

### 3.4 Installare GRUB

```bash
# Configurare GRUB
cat >> /etc/default/grub << 'EOF'
GRUB_CMDLINE_LINUX="root=ZFS=rpool/ROOT/debian"
EOF

grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=debian
update-grub
```

---

## Parte 4 — Snapshot Policy (30 min)

### 4.1 Installare zfs-auto-snapshot

```bash
apt install -y zfs-auto-snapshot
```

### 4.2 Configurare retention

```bash
# Verificare i timer installati
systemctl list-timers | grep zfs

# Personalizzare retention:
# - Ogni 15 minuti: keep 4 (1 ora)
# - Orario: keep 24
# - Giornaliero: keep 30
# - Settimanale: keep 12
# - Mensile: keep 6

# Override per snapshot orario
mkdir -p /etc/systemd/system/zfs-auto-snapshot-hourly.timer.d
cat > /etc/systemd/system/zfs-auto-snapshot-hourly.timer.d/override.conf << 'EOF'
[Timer]
OnCalendar=
OnCalendar=hourly
EOF

# Verificare che i dataset di cache siano esclusi
zfs get com.sun:auto-snapshot rpool/var/cache rpool/var/tmp rpool/tmp
# Devono avere valore "false"
```

### 4.3 Script di pruning personalizzato

```bash
cat > /usr/local/sbin/zfs-snapshot-prune.sh << 'PRUNE_EOF'
#!/bin/bash
set -euo pipefail

# Retention policy
HOURLY_KEEP=24
DAILY_KEEP=30
WEEKLY_KEEP=12
MONTHLY_KEEP=6

log() { logger -t zfs-prune "$*"; echo "$*"; }

prune_snapshots() {
    local pool="$1"
    local prefix="$2"
    local keep="$3"

    local count
    count=$(zfs list -H -t snapshot -o name -S creation "$pool" 2>/dev/null \
        | grep "@${prefix}" | wc -l)

    if [ "$count" -gt "$keep" ]; then
        local to_delete=$((count - keep))
        log "Pruning $to_delete '$prefix' snapshots from $pool (keeping $keep)"
        zfs list -H -t snapshot -o name -S creation "$pool" \
            | grep "@${prefix}" \
            | tail -n "$to_delete" \
            | while read -r snap; do
                log "  Destroying $snap"
                zfs destroy "$snap"
            done
    fi
}

# Applicare a tutti i dataset con auto-snapshot abilitato
zfs list -H -o name -r rpool | while read -r ds; do
    auto=$(zfs get -H -o value com.sun:auto-snapshot "$ds" 2>/dev/null)
    [ "$auto" = "false" ] && continue

    prune_snapshots "$ds" "zfs-auto-snap_hourly"  "$HOURLY_KEEP"
    prune_snapshots "$ds" "zfs-auto-snap_daily"   "$DAILY_KEEP"
    prune_snapshots "$ds" "zfs-auto-snap_weekly"  "$WEEKLY_KEEP"
    prune_snapshots "$ds" "zfs-auto-snap_monthly" "$MONTHLY_KEEP"
done

log "Pruning complete."
PRUNE_EOF
chmod 755 /usr/local/sbin/zfs-snapshot-prune.sh
```

### 4.4 Systemd timer per pruning

```bash
cat > /etc/systemd/system/zfs-snapshot-prune.service << 'EOF'
[Unit]
Description=ZFS snapshot pruning
After=zfs.target

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/zfs-snapshot-prune.sh
EOF

cat > /etc/systemd/system/zfs-snapshot-prune.timer << 'EOF'
[Unit]
Description=Run ZFS snapshot pruning daily

[Timer]
OnCalendar=*-*-* 03:30:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

systemctl daemon-reload
systemctl enable zfs-snapshot-prune.timer
```

---

## Parte 5 — Verifica e Recovery (30 min)

### 5.1 Verificare il boot

```bash
# Reboot e verificare
reboot

# Dopo il boot, verificare
zpool status
zfs list -o name,used,avail,mountpoint,encryption,keystatus
mount | grep zfs
```

### 5.2 Test di recovery: simulare perdita chiave

```bash
# Creare snapshot di test
zfs snapshot -r rpool@before-keytest

# Smontare e bloccare il pool
# (NON farlo sul sistema in esecuzione — usare un dataset di test)
zfs create rpool/test-encrypted
echo "test data" > /rpool/test-encrypted/testfile

# Verificare che la chiave funziona
zfs unload-key rpool/test-encrypted
zfs load-key rpool/test-encrypted
cat /rpool/test-encrypted/testfile
```

### 5.3 Test di recovery: rollback da snapshot

```bash
# Creare dati di test
echo "data before snapshot" > /root/testfile
zfs snapshot rpool/home/root@test-rollback
echo "data after snapshot — will be lost" > /root/testfile

# Rollback
zfs rollback rpool/home/root@test-rollback
cat /root/testfile
# Deve mostrare "data before snapshot"

# Cleanup
zfs destroy rpool/home/root@test-rollback
```

### 5.4 Backup della chiave

```bash
# Backup della chiave sul secondo disco
mkfs.ext4 -L KEYBAK /dev/vdb2
mkdir -p /mnt/keybak
mount /dev/vdb2 /mnt/keybak
cp /etc/zfs/rpool.key /mnt/keybak/rpool.key.bak
chmod 000 /mnt/keybak/rpool.key.bak
umount /mnt/keybak

# Verificare integrità
sha256sum /etc/zfs/rpool.key
mount /dev/vdb2 /mnt/keybak
sha256sum /mnt/keybak/rpool.key.bak
umount /mnt/keybak
```

---

## Criteri di Completamento

- [ ] Sistema avviato con root su ZFS cifrato
- [ ] Auto-unlock funzionante senza intervento manuale
- [ ] Layout dataset corretto (ROOT, home, var, var/log, tmp separati)
- [ ] Snapshot automatici configurati con retention corretta
- [ ] Pruning automatico attivo via systemd timer
- [ ] Backup chiave su disco separato con hash verificato
- [ ] Test rollback eseguito con successo
- [ ] Documentato il layout dei dataset e la procedura di recovery

---

## Sfide Extra

1. **Mirror**: aggiungere un terzo disco e configurare `rpool` come mirror. Testare il recovery da disco degradato.
2. **Send/Recv**: configurare backup incrementale via `zfs send -i` verso il secondo disco.
3. **Cambio chiave**: ruotare la chiave di cifratura con `zfs change-key`.

---

## Riferimenti

- OpenZFS Documentation — https://openzfs.github.io/openzfs-docs/ (consultato: 2026-05-23)
- [25-zfs-guida-operativa.md](../25-zfs-guida-operativa.md)
- [06-storage.md](../06-storage.md)
- [01-filesystem-e-gerarchia.md](../01-filesystem-e-gerarchia.md)
