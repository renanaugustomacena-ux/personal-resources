# Tutorial Linux 01 — Filesystem e Gerarchia: FHS, Permessi, inode

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** Filesystem Hierarchy Standard, permessi Unix, inode, link, mount, xattr
> **Prerequisiti:** Nessuno — tutorial introduttivo
> **Durata stimata:** 10-14 ore
> **Distribuzione:** Debian/Ubuntu/RHEL/Arch

---

## Mappa concettuale

```
Filesystem Linux
│
├── FHS — Filesystem Hierarchy Standard
│   ├── /bin, /sbin — binari essenziali
│   ├── /etc — configurazione
│   ├── /var — dati variabili (log, spool, cache)
│   ├── /home — home utenti
│   ├── /tmp — temporanei (pulizia al reboot)
│   ├── /proc, /sys — pseudo-filesystem kernel
│   ├── /dev — device files
│   └── /mnt, /media — mount points
│
├── inode — metadati di ogni file
│   ├── permessi, UID/GID, timestamp
│   ├── dimensione, tipo
│   └── puntatori ai blocchi dati
│
├── Permessi Unix
│   ├── rwx per user/group/other
│   ├── chmod numerici e simbolici
│   ├── setuid, setgid, sticky bit
│   └── ACL (Access Control List)
│
├── Link
│   ├── Hard link — stesso inode
│   └── Symbolic link — punta a path
│
└── Mount
    ├── mount / umount
    ├── /etc/fstab — mount permanenti
    ├── tmpfs, proc, sysfs
    └── bind mount
```

---

# Parte A — Gerarchia del filesystem

---

## A1. FHS: la mappa del filesystem Linux

```
/ (root)
├── bin/     → binari essenziali (ls, cp, bash) — link a /usr/bin su sistemi moderni
├── boot/    → kernel, initramfs, GRUB
├── dev/     → device files (sda, null, zero, random, tty)
├── etc/     → configurazione di sistema (NON binari, NON dati utente)
│   ├── apt/
│   ├── nginx/
│   ├── systemd/
│   └── fstab, hosts, passwd, shadow
├── home/    → home directory utenti
│   └── mario/    → $HOME per l'utente mario
├── lib/     → librerie condivise
├── media/   → mount point automatici (USB, CD)
├── mnt/     → mount temporanei manuali
├── opt/     → software di terze parti (Oracle, VMware)
├── proc/    → pseudo-FS kernel (PID, cpu info, memory)
├── root/    → home root
├── run/     → dati runtime (PID files, socket)
├── srv/     → dati serviti (HTTP, FTP)
├── sys/     → pseudo-FS device/driver
├── tmp/     → temporanei (mondo-scrivibile, sticky bit)
├── usr/     → dati utente condivisi (read-only in produzione)
│   ├── bin/ → binari
│   ├── lib/ → librerie
│   └── share/ → dati condivisi
└── var/     → dati variabili
    ├── log/ → log di sistema
    ├── spool/ → code (mail, print)
    ├── cache/ → cache applicazioni
    └── lib/ → state delle applicazioni
```

```bash
# Esplora la gerarchia
ls -la /
ls -la /proc/
cat /proc/cpuinfo          # info CPU
cat /proc/meminfo          # info RAM
cat /proc/$(pgrep nginx)/status   # info processo nginx

# Quanto spazio usa ogni directory
du -sh /var/log/* 2>/dev/null | sort -h | tail -20
df -h                      # spazio sui filesystem montati
df -i                      # utilizzo inode
```

> **Analogia:** Il filesystem Linux è come un'azienda ben organizzata. `/etc` è l'ufficio HR con tutti i documenti di configurazione, `/var/log` è l'archivio dove vengono conservati i verbali delle riunioni (log), `/tmp` è il cestino sul tavolo — comodo ma svuotato ogni sera. `/proc` è la direzione interna: non ci sono veri file, è solo una finestra sul funzionamento interno del sistema.

---

# Parte B — inode e metadati

---

## B1. Capire gli inode

```bash
# Visualizza numero inode
ls -i /etc/passwd
# Output: 131073 /etc/passwd
# 131073 è il numero di inode

# Informazioni complete di un inode
stat /etc/passwd
# File: /etc/passwd
# Size: 1872      Blocks: 8     IO Block: 4096
# Device: 8,1     Inode: 131073  Links: 1
# Access: 2024-01-15 08:30:00
# Modify: 2024-01-10 12:00:00
# Change: 2024-01-10 12:00:00   ← cambia anche con chmod/chown

# Struttura inode (concettuale)
# inode 131073:
#   tipo: file regolare
#   permessi: 0644
#   uid: 0 (root)
#   gid: 0 (root)
#   dimensione: 1872 bytes
#   link_count: 1
#   atime, mtime, ctime
#   puntatori_blocchi: [blk1, blk2, ..., indirect_blk]

# Scopri quanti inode hai liberi
df -i /
# Se Iuse% è vicino a 100%, anche con spazio disco libero
# non puoi creare nuovi file!
```

---

# Parte C — Permessi Unix

---

## C1. Modello rwx

```bash
# Lettura permessi
ls -la /etc/passwd
# -rw-r--r-- 1 root root 1872 Jan 10 12:00 /etc/passwd
# │││││││││
# │││││││││ → altri (world): r-- = 4 (solo lettura)
# ││││││ → gruppo (root): r-- = 4 (solo lettura)
# │││ → proprietario (root): rw- = 6 (lettura+scrittura)
# │ → tipo: - (file), d (dir), l (link), b (block), c (char)

# Chmod numerico
# r=4, w=2, x=1
chmod 755 script.sh    # rwxr-xr-x
chmod 644 config.conf  # rw-r--r--
chmod 600 .env         # rw------- (solo proprietario)
chmod 400 chiave.pem   # r-------- (read-only, per SSH key)
chmod 700 /home/mario  # rwx------ (solo proprietario)

# Chmod simbolico
chmod u+x script.sh    # aggiungi exec per user
chmod g-w file.txt     # rimuovi write per group
chmod o= file.txt      # rimuovi tutti per others
chmod a+r file.txt     # aggiungi read per tutti (a=ugo)
chmod u=rwx,g=rx,o=r script.sh

# Chown / chgrp
chown mario:devs file.txt      # proprietario + gruppo
chown -R mario:devs /home/mario    # ricorsivo
chgrp www-data /var/www/html   # cambia solo gruppo
```

---

## C2. Bit speciali: setuid, setgid, sticky

```bash
# setuid (4) — esegui come proprietario del file, non come caller
ls -l /usr/bin/passwd
# -rwsr-xr-x 1 root root ... /usr/bin/passwd
#     ^ s = setuid — utente normale può cambiare la sua password
#       perché passwd gira come root

chmod u+s /usr/bin/mioprogramma
chmod 4755 /usr/bin/mioprogramma   # numerico

# setgid (2) — su directory: file nuovi ereditano il gruppo
mkdir /progetti/condiviso
chgrp devs /progetti/condiviso
chmod g+s /progetti/condiviso
# Ogni file creato in questa dir avrà gruppo=devs

# sticky bit (1) — su directory: solo il proprietario può eliminare il proprio file
ls -ld /tmp
# drwxrwxrwt ... /tmp
#          ^ t = sticky bit
# In /tmp tutti possono scrivere ma nessuno può eliminare i file degli altri

chmod +t /cartella/condivisa
chmod 1777 /cartella/condivisa   # numerico
```

---

## C3. ACL — Access Control List

```bash
# Installazione
apt install acl    # Debian/Ubuntu
# mount -o remount,acl /   # se non già abilitato

# Visualizza ACL
getfacl /var/www/html

# Imposta ACL per un utente specifico
setfacl -m u:mario:rwx /var/www/html
setfacl -m g:devs:rx /var/www/html
setfacl -m o::r /var/www/html     # others: solo lettura

# ACL default (ereditata da nuovi file)
setfacl -d -m u:mario:rwx /var/www/html
setfacl -d -m g:devs:rx /var/www/html

# Rimuovi ACL
setfacl -x u:mario /var/www/html
setfacl -b /var/www/html   # rimuovi tutte le ACL

# Copia ACL
getfacl /sorgente | setfacl --set-file=- /destinazione
```

---

# Parte D — Link e Mount

---

## D1. Hard link e symbolic link

```bash
# Hard link — due nomi per lo stesso inode
ln /etc/passwd /tmp/passwd_copia
stat /etc/passwd   # Links: 2
stat /tmp/passwd_copia   # stesso inode!
# Eliminare uno non elimina i dati (finché links > 0)
# NON funziona tra filesystem diversi

# Symbolic link (symlink) — puntatore al path
ln -s /etc/nginx/sites-available/miosito /etc/nginx/sites-enabled/miosito
ls -la /etc/nginx/sites-enabled/
# lrwxrwxrwx → /etc/nginx/sites-enabled/miosito -> ../sites-available/miosito

ln -s /opt/applicazione-v2.1.0 /opt/applicazione    # versioning
ln -sf /opt/applicazione-v2.2.0 /opt/applicazione   # -f = forza sostituzione

# Trova symlink rotti
find /etc/nginx -type l -! -e .
# Oppure
find /etc -xtype l   # symlink il cui target non esiste

# Risolvi symlink
readlink -f /etc/nginx/sites-enabled/miosito
# → /etc/nginx/sites-available/miosito (path assoluto risolto)
```

---

## D2. Mount

```bash
# Montare un disco
lsblk                     # lista block devices
fdisk -l /dev/sdb         # partizioni su /dev/sdb
mount /dev/sdb1 /mnt/disco

# Mount con opzioni
mount -o rw,noexec,nosuid /dev/sdb1 /mnt/sicuro

# Tmpfs in RAM
mount -t tmpfs -o size=512m tmpfs /tmp/ramfs

# Bind mount
mount --bind /var/www/html /mnt/preview-html

# fstab — mount permanenti
cat /etc/fstab
# UUID=abc-123  /home  ext4  defaults  0 2
# LABEL=DATA    /data  ext4  defaults,noatime  0 2

# Ottieni UUID dispositivo
blkid /dev/sdb1
# → /dev/sdb1: UUID="abc-123" TYPE="ext4"

# Mount tutto da fstab
mount -a   # monta tutte le voci non ancora montate

# Smontare
umount /mnt/disco
umount -l /mnt/disco   # lazy: smonta quando non più in uso
```

---

# Parte E — Riepilogo

## Permessi in breve

| Numerico | Simbolico | Significa |
|---|---|---|
| `777` | `rwxrwxrwx` | Tutti accesso completo (pericoloso!) |
| `755` | `rwxr-xr-x` | Standard per directory e script |
| `644` | `rw-r--r--` | Standard per file leggibili |
| `600` | `rw-------` | File privati (.env, chiavi) |
| `400` | `r--------` | Read-only (chiavi SSH) |

## Comandi essenziali

```bash
# Esplorazione
ls -lah           # lista dettagliata con size human-readable
stat file         # tutti i metadati
file file         # tipo di file
find / -name     # ricerca
locate file       # ricerca da index

# Permessi
chmod 755 f       # imposta permessi
chown user:grp f  # cambia proprietario
getfacl f         # leggi ACL
setfacl -m u:x:r f   # imposta ACL

# Spazio
df -h             # spazio filesystem
du -sh *          # spazio per directory
ncdu              # NCurses disk usage (interattivo)
```

## Prossimi passi

- `tutorial_linux_02_shell_mastery.md` — bash scripting, pipeline, job control
- `tutorial_linux_04_systemd.md` — gestire servizi con systemd
