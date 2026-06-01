# Scenario 03 — Boot Rescue: GRUB Recovery e Chroot Fix

> **Modulo di riferimento:** [01-filesystem-e-gerarchia.md](../01-filesystem-e-gerarchia.md), [07-kernel.md](../07-kernel.md)
> **Tempo stimato:** 1-1.5 ore
> **Livello:** competent → proficient
> **Prerequisiti:** VM Debian 12 + ISO live, completamento moduli 01, 06, 07
> **Ultimo aggiornamento:** 2026-05-23

---

## Scenario

Un server non si avvia dopo un aggiornamento kernel fallito. Il sistema si presenta alla console `grub rescue>`. Il tuo compito è:

1. Diagnosticare il problema dal prompt GRUB rescue
2. Avviare il sistema da ISO live
3. Eseguire chroot e riparare /boot
4. Ripristinare il bootloader

---

## Setup Lab (10 min)

### Simulare un /boot corrotto

```bash
# Su una VM Debian 12 funzionante, PRIMA di rompere:
# Creare uno snapshot della VM!

# Simulare corruzione: rimuovere il kernel
mv /boot/vmlinuz-$(uname -r) /boot/vmlinuz-$(uname -r).bak
mv /boot/initrd.img-$(uname -r) /boot/initrd.img-$(uname -r).bak

# Corrompere la configurazione GRUB
mv /boot/grub/grub.cfg /boot/grub/grub.cfg.bak

# Reboot → il sistema non si avvierà
# reboot
```

---

## Fase 1 — Diagnosi da GRUB Rescue (15 min)

### 1.1 Orientarsi nel prompt GRUB rescue

Al prompt `grub rescue>`:

```
# Listar le partizioni visibili
ls

# Output esempio:
# (hd0) (hd0,msdos1) (hd0,msdos2) (hd0,msdos5)
# oppure per GPT:
# (hd0) (hd0,gpt1) (hd0,gpt2) (hd0,gpt3)

# Cercare la partizione con /boot
ls (hd0,gpt2)/
ls (hd0,gpt2)/boot/
# Cercare vmlinuz-* e initrd.img-*

# Se /boot è su partizione separata:
ls (hd0,gpt1)/
```

### 1.2 Boot manuale da GRUB rescue (se possibile)

```
# Se i file del kernel esistono ma grub.cfg è corrotto:
set root=(hd0,gpt2)
set prefix=(hd0,gpt2)/boot/grub
insmod normal
normal

# Da qui si può accedere al menu GRUB e scegliere un kernel
```

### 1.3 Se il kernel è assente

Se non si trovano file vmlinuz/initrd, passare al boot da live ISO.

---

## Fase 2 — Boot da Live ISO (10 min)

### 2.1 Avviare da ISO

1. Inserire la ISO Debian 12 live nella VM
2. Impostare il boot order per avviare da CD/ISO
3. Selezionare "Live" dal menu
4. Aprire un terminale root

### 2.2 Identificare le partizioni del sistema

```bash
# Identificare dischi e partizioni
lsblk -f

# Output esempio:
# NAME   FSTYPE LABEL  UUID                                 MOUNTPOINT
# vda
# ├─vda1 vfat   EFI    XXXX-XXXX
# ├─vda2 ext4          xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
# └─vda3 swap          xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Identificare la root e la boot
blkid
```

---

## Fase 3 — Chroot e Riparazione (20 min)

### 3.1 Montare il filesystem

```bash
# Montare la root
mount /dev/vda2 /mnt

# Se /boot è separato:
# mount /dev/vda1 /mnt/boot

# Se EFI:
mount /dev/vda1 /mnt/boot/efi

# Montare filesystem virtuali
mount --bind /dev /mnt/dev
mount --bind /dev/pts /mnt/dev/pts
mount --bind /proc /mnt/proc
mount --bind /sys /mnt/sys
mount --bind /run /mnt/run

# Se la rete serve (per apt):
cp /etc/resolv.conf /mnt/etc/resolv.conf
```

### 3.2 Entrare nel chroot

```bash
chroot /mnt /bin/bash

# Verificare di essere nel sistema corretto
cat /etc/hostname
cat /etc/os-release
ls /boot/
```

### 3.3 Reinstallare il kernel

```bash
# Aggiornare i pacchetti disponibili
apt update

# Reinstallare il kernel
apt install --reinstall linux-image-amd64

# Se il pacchetto specifico è noto:
# apt install --reinstall linux-image-6.1.0-XX-amd64

# Verificare
ls -la /boot/vmlinuz-*
ls -la /boot/initrd.img-*
```

### 3.4 Rigenerare initrd

```bash
# Rigenerare initramfs per tutti i kernel installati
update-initramfs -u -k all

# Verificare
ls -la /boot/initrd.img-*
```

### 3.5 Reinstallare GRUB

```bash
# Per BIOS/MBR:
grub-install /dev/vda

# Per UEFI:
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=debian

# Rigenerare grub.cfg
update-grub

# Verificare
cat /boot/grub/grub.cfg | grep menuentry
# Devono apparire le entry per i kernel installati
```

### 3.6 Uscire e riavviare

```bash
# Uscire dal chroot
exit

# Smontare tutto
umount -R /mnt

# Rimuovere la ISO dal boot order
# Riavviare
reboot
```

---

## Fase 4 — Verifica Post-Recovery (10 min)

### 4.1 Verificare il boot

```bash
# Dopo il reboot verificare:
uname -r
# Deve mostrare la versione del kernel installato

# Verificare GRUB
grub-install --version

# Verificare /boot
ls -la /boot/vmlinuz-* /boot/initrd.img-*

# Verificare fstab
findmnt --verify

# Verificare che tutti i servizi siano partiti
systemctl --failed
```

### 4.2 Prevenzione

```bash
# Mantenere almeno 2 kernel installati
dpkg -l | grep linux-image | grep ^ii

# Verificare spazio su /boot
df -h /boot

# Configurare apt per mantenere kernel precedenti
cat /etc/apt/apt.conf.d/01autoremove
# Verificare che il kernel precedente non venga rimosso automaticamente
```

---

## Varianti dello Scenario

### Variante A: fstab corrotto

```bash
# Se il sistema non monta / correttamente:
# Dal chroot, verificare /etc/fstab
cat /etc/fstab
blkid

# Correggere UUID se necessario
# vim /etc/fstab
```

### Variante B: LVM root

```bash
# Se root è su LVM:
apt install lvm2  # nella live
vgscan
vgchange -ay
mount /dev/mapper/vgname-root /mnt
```

### Variante C: ZFS root

```bash
# Se root è su ZFS:
apt install zfsutils-linux  # nella live
zpool import -f rpool
zfs mount rpool/ROOT/debian
# Procedere con chroot
```

---

## Criteri di Completamento

- [ ] Guasto simulato (kernel rimosso, grub.cfg corrotto)
- [ ] Boot da live ISO riuscito
- [ ] Chroot configurato correttamente (dev, proc, sys montati)
- [ ] Kernel reinstallato
- [ ] initramfs rigenerato
- [ ] GRUB reinstallato e grub.cfg rigenerato
- [ ] Sistema avviato normalmente dopo recovery
- [ ] Tutti i servizi attivi post-recovery

---

## Riferimenti

- GNU GRUB Manual — https://www.gnu.org/software/grub/manual/ (consultato: 2026-05-23)
- [01-filesystem-e-gerarchia.md](../01-filesystem-e-gerarchia.md)
- [07-kernel.md](../07-kernel.md)
- [06-storage.md](../06-storage.md)
