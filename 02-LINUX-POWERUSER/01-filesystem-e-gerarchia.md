# Filesystem e Gerarchia Linux — Guida Completa

> **Modulo 01** · **Aggiornamento:** 2026-05-22

## Idee guida
1. **FHS (Filesystem Hierarchy Standard) è ancorato.** `/etc`, `/var`, `/usr`, `/opt` significato fisso.
2. **`mount` namespace per isolation containers.**
3. **ACL via `setfacl`/`getfacl` quando standard rwx insufficient.**
4. **Quote XFS/ext4 + ZFS quota: contention disk space.**
5. **Inode = identità reale del file.** Il nome è solo un'etichetta nella directory entry.
6. **LVM separa lo storage logico dal fisico.** Ridimensionamento senza downtime.
7. **GPT > MBR** su tutti i dischi moderni (>2 TiB, 128 partizioni, checksum).


## Indice

- [Panoramica](#panoramica)
- [Filesystem Hierarchy Standard (FHS) 3.0 — Deep Dive](#filesystem-hierarchy-standard-fhs-30--deep-dive)
- [Inode, Link e Struttura Interna](#inode-link-e-struttura-interna)
- [Tipi di File nel Filesystem Linux](#tipi-di-file-nel-filesystem-linux)
- [Permessi e Ownership — Deep Dive](#permessi-e-ownership--deep-dive)
- [ACL — Access Control List](#acl--access-control-list)
- [Mount, fstab e Opzioni di Montaggio](#mount-fstab-e-opzioni-di-montaggio)
- [Confronto Filesystem: ext4 vs XFS vs Btrfs vs ZFS](#confronto-filesystem-ext4-vs-xfs-vs-btrfs-vs-zfs)
- [Partizionamento Disco: fdisk, gdisk, parted](#partizionamento-disco-fdisk-gdisk-parted)
- [LVM — Logical Volume Manager](#lvm--logical-volume-manager)
- [Gestione File e Directory Avanzata](#gestione-file-e-directory-avanzata)
- [Attributi Estesi e Filesystem Speciali](#attributi-estesi-e-filesystem-speciali)
- [/proc e /sys — Virtual Filesystem Deep Dive](#proc-e-sys--virtual-filesystem-deep-dive)
- [tmpfs e ramfs](#tmpfs-e-ramfs)
- [Manutenzione Filesystem](#manutenzione-filesystem)
- [Quote Disco](#quote-disco)
- [Performance Tuning per Workload](#performance-tuning-per-workload)
- [Best Practices](#best-practices)
- [Troubleshooting — 25+ Problemi Reali e Soluzioni](#troubleshooting--25-problemi-reali-e-soluzioni)
- [Errori Comuni e Anti-Pattern](#errori-comuni-e-anti-pattern)
- [Esercizi Pratici](#esercizi-pratici)
- [FAQ — 25 Domande e Risposte](#faq--25-domande-e-risposte)

---

## Panoramica

Il filesystem Linux è una struttura gerarchica ad albero singolo con radice `/`. Ogni file, directory, dispositivo e processo ha una rappresentazione nel filesystem. Comprendere la gerarchia, i permessi, gli inode e i mount point è fondamentale per qualsiasi operazione di amministrazione — dalla gestione dei servizi alla sicurezza, dal backup al troubleshooting.

A differenza di Windows (dove ogni disco ha una lettera: `C:\`, `D:\`), Linux ha un singolo albero. Dischi aggiuntivi vengono **montati** in punti specifici dell'albero (mount point). Questo design permette trasparenza: un'applicazione accede a `/data/backup` senza sapere se è un disco locale, un NFS remoto o un volume cifrato.

### Concetti fondamentali

| Concetto | Descrizione |
|---|---|
| **Inode** | Struttura dati che contiene tutti i metadati di un file (eccetto il nome) |
| **Directory entry** | Associazione nome → numero inode all'interno di una directory |
| **Mount point** | Directory dove un filesystem aggiuntivo viene innestato nell'albero |
| **Block device** | Dispositivo che legge/scrive dati in blocchi (dischi, partizioni) |
| **VFS (Virtual Filesystem Switch)** | Livello di astrazione del kernel che unifica l'accesso a filesystem diversi |
| **Superblock** | Metadati del filesystem stesso (dimensione, stato, conteggio blocchi liberi) |

Il kernel gestisce tutti i filesystem attraverso il **VFS**: che si tratti di ext4, XFS, NFS o procfs, le system call (`open`, `read`, `write`, `stat`) sono identiche. Il VFS traduce queste chiamate nelle operazioni specifiche del driver del filesystem sottostante.

---

## Filesystem Hierarchy Standard (FHS) 3.0 — Deep Dive

Lo standard FHS (attualmente versione 3.0, mantenuto dalla Linux Foundation) definisce la struttura delle directory e il contenuto previsto per ciascuna. La conformità FHS garantisce che software, amministratori e script possano fare assunzioni affidabili su dove trovare file e binari.

### Albero completo

```
/                   Root del filesystem — punto di partenza
├── /bin            Binari essenziali (ls, cp, mv, cat, bash)
├── /sbin           Binari di sistema (fsck, iptables, shutdown)
├── /etc            File di configurazione di sistema
├── /home           Home directory degli utenti
├── /root           Home directory di root
├── /var            File variabili (dati che cambiano in runtime)
├── /tmp            File temporanei (puliti al reboot)
├── /usr            Programmi e risorse utente (read-only)
├── /lib            Librerie essenziali e moduli kernel
├── /lib64          Librerie 64-bit (su sistemi multilib)
├── /opt            Software di terze parti
├── /dev            Device file
├── /proc           Filesystem virtuale — kernel e processi
├── /sys            Filesystem virtuale — dispositivi e driver
├── /mnt            Mount point temporanei (mount manuale)
├── /media          Mount point automatici (USB, CD)
├── /boot           Kernel, initramfs, GRUB
├── /run            File di runtime (PID, socket, stato volatile)
└── /srv            Dati serviti da servizi (web, FTP)
```

### Directory per directory

#### `/` — Root

La radice dell'intero filesystem. Ogni percorso assoluto parte da qui. Il filesystem root dovrebbe contenere solo le directory previste dallo standard. Non creare file o directory arbitrarie direttamente in `/`.

```bash
# Verificare il filesystem root
df -hT /
# Esempio output:
# Filesystem     Type  Size  Used Avail Use% Mounted on
# /dev/sda2      ext4   50G   12G   35G  26% /
```

#### `/bin` — Binari essenziali utente

Contiene i comandi fondamentali necessari in **single-user mode** e durante il boot, prima che `/usr` sia montato. Comandi tipici: `ls`, `cp`, `mv`, `rm`, `cat`, `echo`, `bash`, `sh`, `mount`, `umount`, `grep`, `sed`, `awk`.

> **Nota moderna:** Nelle distribuzioni recenti (Fedora, Debian 12+, Ubuntu 22.04+, Arch), `/bin` è un symlink a `/usr/bin` (usr-merge). Concettualmente la distinzione resta valida.

```bash
# Verificare se /bin è un symlink (usr-merge)
ls -ld /bin
# lrwxrwxrwx 1 root root 7 Jan  1 00:00 /bin -> usr/bin

# Binari tipici
ls /bin/{ls,cp,mv,bash,grep,mount}
```

#### `/sbin` — Binari di sistema (system binaries)

Comandi di amministrazione che richiedono privilegi di root: `fdisk`, `mkfs`, `fsck`, `iptables`, `ip`, `shutdown`, `reboot`, `modprobe`, `lvm`, `mdadm`. Su sistemi usr-merge, `/sbin` → `/usr/sbin`.

```bash
# Esempi di comandi in /sbin
which fdisk    # /usr/sbin/fdisk
which iptables # /usr/sbin/iptables
which fsck     # /usr/sbin/fsck

# Un utente non-root non ha /sbin nel PATH di default
echo $PATH  # /usr/local/bin:/usr/bin:/bin (no sbin)
```

#### `/etc` — Configurazione di sistema

**Tutto ciò che configura il sistema** risiede qui. File di testo, non binari. Il nome viene da "et cetera" storicamente, ma oggi è di fatto "Editable Text Configuration".

```bash
# File critici in /etc
/etc/fstab           # Mount point permanenti
/etc/passwd          # Database utenti (UID, GID, home, shell)
/etc/shadow          # Hash delle password (leggibile solo da root)
/etc/group           # Database gruppi
/etc/hostname        # Nome host della macchina
/etc/hosts           # Risoluzione nomi statici
/etc/resolv.conf     # Server DNS
/etc/nsswitch.conf   # Ordine di ricerca name service (file, dns, ldap)
/etc/sudoers         # Configurazione sudo (editare SOLO con visudo!)
/etc/ssh/sshd_config # Configurazione server SSH
/etc/systemd/        # Override delle unit systemd
/etc/crontab         # Crontab di sistema
/etc/default/        # Valori default per servizi
/etc/sysctl.conf     # Parametri kernel a runtime
/etc/security/       # PAM, limits.conf, access.conf
/etc/apt/            # Configurazione APT (Debian/Ubuntu)
/etc/yum.repos.d/    # Repository YUM/DNF (RHEL/Fedora)

# Versionare /etc con etckeeper
apt install etckeeper    # Debian/Ubuntu
etckeeper init           # Inizializza repo git in /etc
etckeeper commit "baseline configuration"
```

#### `/home` — Home directory utenti

Ogni utente ha una directory in `/home/<username>`. Contiene file personali, configurazioni applicative (dotfile), chiavi SSH, cache. Separare `/home` su una partizione dedicata è una best practice critica — permette reinstallazione del sistema senza perdere dati utente.

```bash
# Struttura tipica di una home
/home/user/
├── .bashrc              # Configurazione shell interattiva
├── .bash_profile        # Login shell
├── .profile             # Alternativa a .bash_profile
├── .ssh/                # Chiavi SSH e config
│   ├── id_ed25519       # Chiave privata (permessi: 600)
│   ├── id_ed25519.pub   # Chiave pubblica
│   ├── authorized_keys  # Chiavi autorizzate per login SSH (600)
│   ├── config           # Configurazione client SSH
│   └── known_hosts      # Fingerprint host conosciuti
├── .config/             # Configurazioni XDG (standard moderno)
├── .local/              # Dati locali utente (XDG_DATA_HOME)
├── .cache/              # Cache applicazioni (XDG_CACHE_HOME)
├── .gnupg/              # Keyring GPG (permessi: 700)
└── Documents/, Downloads/, ...

# Creare utente con home directory
useradd -m -s /bin/bash newuser

# Skeleton: template per nuove home
ls /etc/skel/    # .bashrc, .profile, ecc. copiati alla creazione utente
```

#### `/root` — Home di root

Home directory del superutente. Separata da `/home` perché root deve poter operare anche quando `/home` non è montato (es. recovery). Permessi: `700` (solo root).

```bash
ls -la /root/
# drwx------ 5 root root 4096 May 20 10:00 .
```

#### `/var` — File variabili

Dati che cambiano durante il funzionamento del sistema. La crescita di `/var` è il motivo più comune di "disk full" su server. Partizione dedicata fortemente consigliata.

```bash
/var/log/            # Log di sistema e servizi
  /var/log/syslog    # Log generale (Debian) o /var/log/messages (RHEL)
  /var/log/auth.log  # Log autenticazione
  /var/log/kern.log  # Log kernel
  /var/log/journal/  # Log systemd (binario, leggere con journalctl)
  /var/log/nginx/    # Log Nginx
  /var/log/audit/    # Log audit (auditd)

/var/lib/            # Dati di stato persistenti dei servizi
  /var/lib/docker/   # Immagini e container Docker
  /var/lib/mysql/    # Database MySQL/MariaDB
  /var/lib/postgresql/  # Database PostgreSQL
  /var/lib/dpkg/     # Database pacchetti dpkg

/var/cache/          # Cache rigenerabili
  /var/cache/apt/    # Cache pacchetti scaricati
  /var/cache/man/    # Cache manpages

/var/spool/          # Code di lavoro
  /var/spool/mail/   # Caselle di posta locali
  /var/spool/cron/   # Crontab utente
  /var/spool/cups/   # Coda di stampa

/var/tmp/            # File temporanei persistenti (sopravvivono reboot)
                     # systemd: puliti dopo 30 giorni (default)

# Monitorare crescita /var
du -sh /var/log/ /var/lib/ /var/cache/ /var/spool/
```

#### `/tmp` — File temporanei

File temporanei che possono essere cancellati al reboot. Molte distribuzioni montano `/tmp` come tmpfs (in RAM). Qualsiasi utente può scrivere in `/tmp` — lo **sticky bit** impedisce che utenti cancellino file altrui.

```bash
# Verificare se /tmp è tmpfs
df -hT /tmp
# Filesystem     Type   Size  Used Avail Use% Mounted on
# tmpfs          tmpfs  4.0G   12M  4.0G   1% /tmp

# Sticky bit su /tmp
ls -ld /tmp
# drwxrwxrwt 15 root root 4096 May 22 10:00 /tmp
#          ^-- t = sticky bit attivo

# Sicurezza: montare /tmp con opzioni restrittive
# In /etc/fstab:
# tmpfs  /tmp  tmpfs  defaults,noexec,nosuid,nodev,size=4G  0  0
```

#### `/usr` — Unix System Resources

Contiene la maggior parte dei programmi, librerie e documentazione installati. Pensato come **read-only** — i dati variabili vanno in `/var`. Nelle distribuzioni moderne con usr-merge, `/usr` è di fatto il cuore del sistema.

```bash
/usr/bin/          # La maggior parte dei comandi utente
/usr/sbin/         # Comandi di amministrazione
/usr/lib/          # Librerie condivise
/usr/lib64/        # Librerie 64-bit
/usr/include/      # Header file C/C++ per compilazione
/usr/share/        # Dati architettura-indipendenti
  /usr/share/man/  # Pagine di manuale
  /usr/share/doc/  # Documentazione pacchetti
  /usr/share/locale/  # File di localizzazione
  /usr/share/zoneinfo/ # Database timezone
/usr/local/        # Software installato localmente (fuori dal package manager)
  /usr/local/bin/
  /usr/local/lib/
  /usr/local/etc/
/usr/src/          # Sorgenti (es. linux-headers)

# /usr/local ha la stessa struttura di /usr
# ma è riservato all'amministratore per installazioni manuali
# Il package manager NON tocca /usr/local
```

#### `/lib` e `/lib64` — Librerie essenziali

Librerie condivise necessarie ai binari in `/bin` e `/sbin`. Contiene anche i moduli del kernel.

```bash
/lib/modules/$(uname -r)/   # Moduli kernel per la versione corrente
/lib/firmware/               # Firmware per dispositivi hardware
/lib/systemd/                # Unit file systemd di default

# Su sistemi usr-merge: /lib → /usr/lib
ls -ld /lib
# lrwxrwxrwx 1 root root 7 Jan  1 00:00 /lib -> usr/lib
```

#### `/opt` — Software opzionale

Software di terze parti che non segue la struttura standard `/usr`. Ogni pacchetto ha la sua sottodirectory autocontenuta.

```bash
/opt/
├── google/chrome/       # Google Chrome
├── containerd/          # Container runtime
├── 1Password/           # 1Password
└── custom-app/          # Software aziendale custom
    ├── bin/
    ├── lib/
    └── etc/

# Convenzione: /opt/<vendor>/<package>
# Configurazione locale in /etc/opt/<package>
# Dati variabili in /var/opt/<package>
```

#### `/dev` — Device file

Ogni dispositivo hardware (e alcuni pseudo-dispositivi) è rappresentato come file in `/dev`. Gestito da **udev** che crea/rimuove device file automaticamente.

```bash
# Dispositivi a blocchi (storage)
/dev/sda           # Primo disco SATA/SCSI
/dev/sda1          # Prima partizione di sda
/dev/nvme0n1       # Primo disco NVMe
/dev/nvme0n1p1     # Prima partizione NVMe
/dev/vda           # Disco virtuale (KVM/QEMU)
/dev/mapper/       # Device mapper (LVM, LUKS, dm-crypt)

# Pseudo-dispositivi fondamentali
/dev/null          # Scarta tutto l'input (buco nero)
/dev/zero          # Genera stream infinito di byte nulli
/dev/random        # Numeri casuali (bloccante se entropia insufficiente)
/dev/urandom       # Numeri casuali (non bloccante, preferito)
/dev/full          # Simula disco pieno (test)
/dev/tty           # Terminale corrente
/dev/console       # Console di sistema
/dev/pts/          # Pseudo-terminali (SSH, terminali grafici)
/dev/loop0         # Loop device (monta file come disco)

# Esempi pratici
dd if=/dev/zero of=testfile bs=1M count=100  # Crea file da 100MB
dd if=/dev/urandom bs=32 count=1 | base64    # Genera token casuale
echo "test" > /dev/null                       # Scarta output

# Creare device file (raro, udev gestisce automaticamente)
mknod /dev/mydevice c 240 0   # Character device, major 240, minor 0
```

#### `/proc` — Process filesystem (procfs)

Filesystem virtuale generato dal kernel in tempo reale. Non occupa spazio su disco. Fornisce informazioni su processi, kernel, hardware e permette di modificare parametri del kernel a runtime.

```bash
/proc/cpuinfo        # Dettagli CPU (modello, core, flag)
/proc/meminfo        # Stato memoria (MemTotal, MemFree, Buffers, Cached)
/proc/loadavg        # Load average (1, 5, 15 minuti)
/proc/uptime         # Uptime in secondi
/proc/version        # Versione kernel
/proc/cmdline        # Parametri boot del kernel
/proc/mounts         # Filesystem montati (equivale a mount senza argomenti)
/proc/partitions     # Partizioni riconosciute dal kernel
/proc/filesystems    # Filesystem supportati dal kernel
/proc/net/           # Statistiche di rete
/proc/sys/           # Parametri kernel tunable (sysctl)
/proc/[PID]/         # Directory per ogni processo in esecuzione
```

#### `/sys` — Sysfs

Filesystem virtuale che espone informazioni su dispositivi, driver e bus del kernel. Più strutturato di `/proc`, organizzato per classi di dispositivi.

```bash
/sys/class/net/       # Interfacce di rete
/sys/class/block/     # Dispositivi a blocchi
/sys/class/thermal/   # Sensori temperatura
/sys/devices/         # Topologia dispositivi (per bus)
/sys/fs/              # Informazioni filesystem
/sys/kernel/          # Parametri kernel
/sys/power/           # Power management
/sys/module/          # Moduli kernel caricati

# Esempio: temperatura CPU
cat /sys/class/thermal/thermal_zone0/temp
# 45000 → 45.0°C (valore in milligradi)
```

#### `/boot` — File di boot

Contiene tutto il necessario per il boot: kernel, initramfs, configurazione bootloader.

```bash
/boot/
├── vmlinuz-6.17.0-29-generic     # Kernel compresso
├── initrd.img-6.17.0-29-generic  # Initial RAM disk
├── config-6.17.0-29-generic      # Configurazione compilazione kernel
├── System.map-6.17.0-29-generic  # Mappa simboli kernel
├── grub/
│   ├── grub.cfg                  # Configurazione GRUB (generata!)
│   └── grubenv                   # Variabili ambiente GRUB
└── efi/                          # Partizione EFI (su sistemi UEFI)

# Non editare grub.cfg direttamente! Usare:
update-grub                 # Debian/Ubuntu
grub2-mkconfig -o /boot/grub2/grub.cfg  # RHEL/Fedora

# Partizione /boot: 500MB-1GB sufficienti
# Partizione EFI (/boot/efi): 256-512MB, FAT32
```

#### `/run` — Runtime data

Filesystem temporaneo (tmpfs) creato all'avvio. Contiene dati volatili di runtime: PID file, socket, lock. Sostituisce il vecchio `/var/run`.

```bash
/run/
├── lock/            # Lock file
├── user/1000/       # Runtime data per utente (systemd)
├── systemd/         # Socket e state systemd
├── docker.sock      # Socket Docker
├── sshd.pid         # PID server SSH
└── mount/           # Runtime mount info

# /var/run è un symlink a /run nelle distribuzioni moderne
ls -ld /var/run
# lrwxrwxrwx 1 root root 4 Jan  1 00:00 /var/run -> /run
```

#### `/mnt` e `/media` — Mount point

`/mnt` è per mount manuali temporanei dell'amministratore. `/media` è per media rimovibili montati automaticamente (udev/udisks).

```bash
# Mount manuale
mount /dev/sdb1 /mnt
mount -o loop disk.iso /mnt/iso  # Montare ISO

# Mount automatico USB
# udisks monta in /media/<username>/<label>
ls /media/$USER/

# Non usare /mnt per mount permanenti — usare directory dedicate
# Esempio: /data, /backup, /nfs-share
```

#### `/srv` — Service data

Dati serviti dai servizi della macchina. Usata per contenuti web, FTP, repository. Spesso sottovalutata e sostituita da directory custom.

```bash
/srv/
├── www/         # Contenuti web server
├── ftp/         # File FTP
└── git/         # Repository Git bare

# Convenzione: /srv/<protocollo>/<dominio>
# /srv/www/example.com/
```

---

## Inode, Link e Struttura Interna

### Architettura degli Inode

Un **inode** (index node) è la struttura dati fondamentale del filesystem che descrive un file. Quando il kernel accede a un file, prima legge l'inode per ottenere i metadati e i puntatori ai blocchi dati.

#### Contenuto di un inode

| Campo | Descrizione |
|---|---|
| **File type** | Regular file, directory, symlink, device, socket, FIFO |
| **Permessi** | rwx per owner, group, others + bit speciali |
| **UID** | User ID del proprietario |
| **GID** | Group ID del proprietario |
| **Size** | Dimensione in byte |
| **Timestamp atime** | Ultimo accesso in lettura |
| **Timestamp mtime** | Ultima modifica del contenuto |
| **Timestamp ctime** | Ultima modifica dei metadati (permessi, owner, ecc.) |
| **Hard link count** | Numero di nomi (directory entry) che puntano a questo inode |
| **Block pointers** | Puntatori diretti + indiretti ai blocchi dati su disco |

**Cosa NON contiene un inode:** il nome del file. Il nome è memorizzato nella **directory entry** della directory padre, come coppia `(nome, numero_inode)`.

```bash
# Visualizzare il numero inode
ls -i file.txt
# 1234567 file.txt

# Tutti i metadati dell'inode
stat file.txt
# Output:
#   File: file.txt
#   Size: 4096       Blocks: 8          IO Block: 4096   regular file
#   Device: 802h/2050d    Inode: 1234567    Links: 1
#   Access: (0644/-rw-r--r--)  Uid: ( 1000/   user)   Gid: ( 1000/   user)
#   Access: 2026-05-22 10:00:00.000000000 +0200
#   Modify: 2026-05-20 15:30:00.000000000 +0200
#   Change: 2026-05-20 15:30:00.000000000 +0200
#   Birth: 2026-05-15 08:00:00.000000000 +0200
```

#### Struttura dei puntatori a blocco (ext4)

Un inode ext4 usa un sistema di **extent** (più efficiente dei vecchi puntatori diretti/indiretti di ext2/3):

```
Inode
├── Extent 1: blocchi 1000-1100 (100 blocchi contigui)
├── Extent 2: blocchi 5000-5050 (50 blocchi contigui)
└── Extent 3: blocchi 8000-8200 (200 blocchi contigui)

# Ogni extent descrive un intervallo contiguo di blocchi.
# Massimo 4 extent direttamente nell'inode.
# Per file frammentati: extent tree (albero B-tree di extent).
```

#### Inode Table e allocazione

La **inode table** è l'area del filesystem dove tutti gli inode sono memorizzati. Il numero massimo di inode è fissato alla creazione del filesystem (per ext4).

```bash
# Informazioni sulla inode table
tune2fs -l /dev/sda2 | grep -i inode
# Inode count:              3276800
# Free inodes:              3100000
# Inodes per group:         8192
# Inode blocks per group:   512
# Inode size:               256

# Verificare utilizzo inode
df -i
# Filesystem      Inodes   IUsed   IFree IUse% Mounted on
# /dev/sda2      3276800  176800 3100000    6% /
# /dev/sdb1      6553600   12345 6541255    1% /data

# df -ih per formato human-readable
df -ih
```

#### Inode exhaustion — problema critico

L'esaurimento degli inode si verifica quando tutti gli inode sono allocati (IUse% = 100%) anche se c'è spazio disco libero. Tipico con milioni di file piccoli (cache, sessioni PHP, mail queue).

```bash
# Diagnosi: disco con spazio ma "No space left on device"
df -h /     # Spazio OK
df -i /     # IUse% = 100% → INODE ESAURITI

# Trovare directory con più file (consumo inode)
find / -xdev -printf '%h\n' | sort | uniq -c | sort -rn | head -20
# 1234567 /var/spool/postfix/maildrop
#  456789 /tmp/php-sessions
#   98765 /var/cache/nginx/proxy

# Contare file per directory
for d in /var/spool/* /var/cache/* /tmp/*/; do
  echo "$(find "$d" -type f 2>/dev/null | wc -l) $d"
done | sort -rn | head -10

# Soluzioni:
# 1. Eliminare file inutili nella directory colpevole
# 2. Ricreare il filesystem con più inode:
#    mkfs.ext4 -N 10000000 /dev/sdX  (specifica numero inode)
# 3. Usare un filesystem senza limite fisso di inode (XFS, Btrfs)
```

### Hard Link vs Symbolic Link

```bash
# === HARD LINK ===
# Due (o più) nomi che puntano allo STESSO inode.
# Non è una copia: è lo stesso file con due nomi.

ln file.txt hardlink.txt

ls -li file.txt hardlink.txt
# 1234567 -rw-r--r-- 2 user user 4096 May 22 10:00 file.txt
# 1234567 -rw-r--r-- 2 user user 4096 May 22 10:00 hardlink.txt
# ^^^^^^^             ^
# Stesso inode        Link count = 2

# Proprietà hard link:
# - Stesso inode → stessi dati, stessi permessi, stessa dimensione
# - Funziona SOLO nello stesso filesystem (gli inode sono locali al fs)
# - Se cancelli l'originale, l'hard link resta funzionante
# - Il file viene eliminato dal disco solo quando link count = 0
# - NON può linkare directory (per evitare loop nell'albero)

# === SYMBOLIC LINK (symlink) ===
# File speciale che contiene il percorso di un altro file.

ln -s /percorso/assoluto/file.txt symlink.txt
ln -s ../relative/file.txt symlink_rel.txt

ls -li file.txt symlink.txt
# 1234567 -rw-r--r-- 1 user user 4096 May 22 10:00 file.txt
# 7654321 lrwxrwxrwx 1 user user   28 May 22 10:00 symlink.txt -> /percorso/...
# ^^^^^^^                                           ^^^^^^^^^^^^^
# Inode diverso                                     Mostra il target

# Proprietà symlink:
# - Inode diverso dall'originale
# - Funziona tra filesystem diversi
# - Può linkare directory
# - Se l'originale viene cancellato → dangling symlink (link rotto)
# - I permessi mostrati (lrwxrwxrwx) sono irrilevanti: contano quelli del target

# Trovare tutti gli hard link di un file
find / -xdev -inum $(stat -c %i file.txt) 2>/dev/null

# Trovare symlink rotti
find /etc -xtype l 2>/dev/null    # -xtype l = symlink che punta a nulla

# Trovare tutti i symlink in una directory
find /usr/bin -type l -ls
```

---

## Tipi di File nel Filesystem Linux

Linux distingue 7 tipi di file, identificabili dal primo carattere nell'output di `ls -l`:

| Carattere | Tipo | Descrizione |
|---|---|---|
| `-` | Regular file | File ordinario (testo, binario, immagine, archivio) |
| `d` | Directory | Contiene directory entry (coppie nome→inode) |
| `l` | Symbolic link | Puntatore a un altro percorso |
| `c` | Character device | Dispositivo a caratteri (accesso sequenziale) |
| `b` | Block device | Dispositivo a blocchi (accesso casuale) |
| `s` | Socket | Endpoint comunicazione inter-processo (locale) |
| `p` | FIFO (named pipe) | Pipe con nome nel filesystem |

### Esempi pratici per ogni tipo

```bash
# --- Regular file (-) ---
ls -l /etc/hostname
# -rw-r--r-- 1 root root 11 May 22 10:00 /etc/hostname

# --- Directory (d) ---
ls -ld /etc/
# drwxr-xr-x 135 root root 12288 May 22 10:00 /etc/

# --- Symbolic link (l) ---
ls -l /usr/bin/python3
# lrwxrwxrwx 1 root root 9 Jan  1 00:00 /usr/bin/python3 -> python3.12

# --- Character device (c) ---
# Dispositivi a flusso continuo: terminali, /dev/null, /dev/random
ls -l /dev/null
# crw-rw-rw- 1 root root 1, 3 May 22 10:00 /dev/null
#                         ^^^^
#                         major,minor number

ls -l /dev/tty
# crw-rw-rw- 1 root tty 5, 0 May 22 10:00 /dev/tty

# --- Block device (b) ---
# Dispositivi storage: dischi, partizioni
ls -l /dev/sda
# brw-rw---- 1 root disk 8, 0 May 22 10:00 /dev/sda
ls -l /dev/sda1
# brw-rw---- 1 root disk 8, 1 May 22 10:00 /dev/sda1

# --- Socket (s) ---
# Comunicazione tra processi sullo stesso host (Unix domain socket)
ls -l /run/docker.sock
# srw-rw---- 1 root docker 0 May 22 10:00 /run/docker.sock

ls -l /run/snapd.socket
# srw-rw-rw- 1 root root 0 May 22 10:00 /run/snapd.socket

# Utile per servizi locali: database, Docker, systemd
# Più veloce di TCP loopback (niente overhead di rete)

# --- FIFO / Named pipe (p) ---
# Pipe con nome persistente nel filesystem
mkfifo /tmp/mypipe
ls -l /tmp/mypipe
# prw-r--r-- 1 user user 0 May 22 10:00 /tmp/mypipe

# Uso: comunicazione tra processi
# Terminale 1:
echo "messaggio" > /tmp/mypipe   # Blocca finché non c'è un lettore
# Terminale 2:
cat /tmp/mypipe                   # Legge "messaggio"

# Identificare il tipo con file e stat
file /dev/null
# /dev/null: character special (1/3)

stat -c "%F" /etc/hostname
# regular file

stat -c "%F" /dev/sda
# block special file
```

---

## Permessi e Ownership — Deep Dive

### Permessi Base (rwx)

```bash
# Formato output ls -l:
# -rwxr-xr-- 1 user group 4096 Jan 1 12:00 file.txt
# │└┬┘ └┬┘ └┬┘
# │ │   │   └── others: read only (r--)
# │ │   └────── group: read + execute (r-x)
# │ └────────── owner: read + write + execute (rwx)
# └──────────── tipo: - file, d directory, l symlink, c/b device, s socket, p pipe

# Significato di rwx per FILE:
# r (4) = leggere il contenuto
# w (2) = modificare il contenuto
# x (1) = eseguire come programma

# Significato di rwx per DIRECTORY:
# r (4) = elencare il contenuto (ls)
# w (2) = creare/eliminare file nella directory
# x (1) = attraversare la directory (cd, accedere ai file al suo interno)
# NOTA: w senza x su una directory non permette di creare file!
#       x senza r permette di accedere a file noti ma non di elencare
```

### chmod — Modifica permessi

```bash
# Notazione ottale
chmod 755 script.sh     # rwxr-xr-x
chmod 644 file.txt      # rw-r--r--
chmod 600 secret.key    # rw-------
chmod 700 .ssh/         # rwx------
chmod 750 /shared/      # rwxr-x---
chmod 000 locked.txt    # ----------

# Notazione simbolica
chmod u+x script.sh              # Aggiunge x per owner
chmod g+w file.txt                # Aggiunge w per group
chmod o-rwx private.txt           # Rimuove tutti per others
chmod a+r public.txt              # Aggiunge r per tutti (a = all)
chmod u=rwx,g=rx,o=r file.txt    # Imposta esattamente
chmod go= secret.key              # Rimuove tutto per group e others

# Ricorsivo
chmod -R 755 /var/www/html/       # Ricorsivo su tutti i file e directory
# ATTENZIONE: 755 su file dà x a tutti, raramente voluto per file normali

# Pattern sicuro: directory 755, file 644
find /var/www -type d -exec chmod 755 {} \;
find /var/www -type f -exec chmod 644 {} \;
```

### chown — Modifica proprietario

```bash
chown user file.txt                # Cambia solo owner
chown user:group file.txt          # Cambia owner e group
chown :group file.txt              # Cambia solo group
chgrp group file.txt               # Alternativa per cambiare solo group

chown -R www-data:www-data /var/www/  # Ricorsivo

# Solo root può cambiare l'owner di un file
# Un utente può cambiare il group solo a un gruppo di cui è membro
```

### Permessi speciali: SUID, SGID, Sticky Bit

```bash
# === SUID (Set User ID) — 4000 ===
# Il programma viene eseguito con i privilegi del PROPRIETARIO del file,
# non dell'utente che lo lancia.
# Indicato da 's' nella posizione x dell'owner.

ls -l /usr/bin/passwd
# -rwsr-xr-x 1 root root 68208 May 22 10:00 /usr/bin/passwd
#    ^-- s = SUID attivo

# passwd ha SUID perché deve scrivere /etc/shadow (proprietà root)
# anche quando eseguito da un utente normale.

chmod u+s /usr/local/bin/myprog   # Attiva SUID
chmod 4755 /usr/local/bin/myprog  # Equivalente in ottale

# SICUREZZA: SUID su binari è un vettore di attacco classico
# Trovare tutti i file SUID nel sistema:
find / -perm -4000 -type f -ls 2>/dev/null

# === SGID (Set Group ID) — 2000 ===
# Su file: eseguito con i privilegi del GROUP del file
# Su directory: i file creati al suo interno ereditano il GROUP della directory
#               (invece del group primario dell'utente che li crea)

chmod g+s /progetto/shared/       # SGID su directory
ls -ld /progetto/shared/
# drwxrwsr-x 2 root developers 4096 May 22 10:00 /progetto/shared/
#       ^-- s = SGID attivo

# Scenario: directory condivisa dal team
mkdir /progetto/shared
chown :developers /progetto/shared
chmod 2775 /progetto/shared
# Ora tutti i file creati dentro avranno group = developers

# Trovare file/directory con SGID:
find / -perm -2000 -ls 2>/dev/null

# === Sticky Bit — 1000 ===
# Su directory: solo il proprietario del file (o root) può eliminarlo.
# Fondamentale per directory condivise come /tmp.

chmod +t /tmp/
chmod 1777 /tmp/                  # Equivalente

ls -ld /tmp/
# drwxrwxrwt 15 root root 4096 May 22 10:00 /tmp/
#          ^-- t = sticky bit attivo

# Senza sticky bit: chiunque con w sulla directory potrebbe cancellare
# i file di altri utenti.

# Tabella riassuntiva permessi speciali in ottale:
# 4000 = SUID
# 2000 = SGID
# 1000 = Sticky bit
# Combinazione: 4755 = SUID + rwxr-xr-x
#               2775 = SGID + rwxrwxr-x
#               1777 = Sticky + rwxrwxrwx
```

### umask — Permessi di default

```bash
# umask definisce quali permessi vengono RIMOSSI dai nuovi file/directory
umask                  # Mostra umask corrente (es. 0022)

# Calcolo:
# File: permessi base 666 (no execute di default)
# Directory: permessi base 777
#
# Con umask 022:
#   File:      666 AND NOT 022 = 644 (rw-r--r--)
#   Directory: 777 AND NOT 022 = 755 (rwxr-xr-x)
#
# Con umask 027:
#   File:      666 AND NOT 027 = 640 (rw-r-----)
#   Directory: 777 AND NOT 027 = 750 (rwxr-x---)
#
# Con umask 077:
#   File:      666 AND NOT 077 = 600 (rw-------)
#   Directory: 777 AND NOT 077 = 700 (rwx------)

umask 027              # Imposta per la sessione corrente

# Impostare permanentemente
# Per un utente: ~/.bashrc o ~/.profile
echo "umask 027" >> ~/.bashrc
# Per tutto il sistema: /etc/profile o /etc/login.defs
# UMASK 027    (in /etc/login.defs)
```

---

## ACL — Access Control List

Le ACL estendono il modello rwx standard permettendo permessi granulari per utenti e gruppi specifici, senza modificare owner o group del file.

### Prerequisiti

```bash
# Il filesystem deve supportare ACL (ext4, XFS, Btrfs lo fanno di default)
# Verificare:
mount | grep acl
tune2fs -l /dev/sda2 | grep "Default mount options"
# Default mount options:    user_xattr acl

# Se non abilitato, aggiungere in fstab:
# /dev/sda2  /  ext4  defaults,acl  0  1
# Oppure:
mount -o remount,acl /
```

### Operazioni ACL

```bash
# Impostare ACL per utente
setfacl -m u:mario:rx /progetto/          # Mario: read+execute
setfacl -m u:anna:rwx /progetto/          # Anna: full access
setfacl -m u:guest:--- /progetto/         # Guest: nessun permesso

# Impostare ACL per gruppo
setfacl -m g:developers:rwx /progetto/    # Gruppo developers: full
setfacl -m g:auditors:r /progetto/        # Gruppo auditors: solo lettura

# Permessi per "others" via ACL
setfacl -m o::--- /progetto/              # Others: nessun permesso

# ACL di default (per nuovi file creati nella directory)
setfacl -d -m u:mario:rx /progetto/       # Default per mario
setfacl -d -m g:developers:rwx /progetto/ # Default per developers

# Visualizzare ACL
getfacl /progetto/
# # file: progetto/
# # owner: root
# # group: root
# user::rwx
# user:mario:r-x
# user:anna:rwx
# group::r-x
# group:developers:rwx
# mask::rwx
# other::---
# default:user::rwx
# default:user:mario:r-x
# default:group::r-x
# default:group:developers:rwx
# default:mask::rwx
# default:other::---

# La mask limita i permessi EFFETTIVI di tutte le entry ACL (tranne owner e other)
setfacl -m m::rx /progetto/    # Mask: max r-x → developers perde w effettivo

# Rimuovere ACL specifiche
setfacl -x u:mario /progetto/             # Rimuove ACL di mario
setfacl -x g:auditors /progetto/          # Rimuove ACL di auditors

# Rimuovere TUTTE le ACL
setfacl -b /progetto/

# Ricorsivo
setfacl -R -m g:developers:rwx /progetto/ # Applica ricorsivamente

# Backup e restore ACL
getfacl -R /progetto/ > acl_backup.txt
setfacl --restore=acl_backup.txt

# Indicatore ACL in ls
ls -l /progetto/
# drwxrwx---+ 2 root root 4096 May 22 10:00 progetto/
#           ^-- il + indica la presenza di ACL
```

### ACL e interazione con permessi standard

```bash
# L'ACL mask limita i permessi effettivi:
# Se mask = r-x, un'entry ACL g:dev:rwx diventa effettivamente r-x
# chmod su group modifica la mask, NON il group entry nelle ACL
# Questo è un errore comune: chmod g-w dopo setfacl cambia la mask

# Ordine di valutazione:
# 1. Owner match → usa permessi owner
# 2. Named user ACL match → usa quella entry (limitata dalla mask)
# 3. Group match (owning group o named group) → usa entry (limitata dalla mask)
# 4. Other → usa permessi other
```

---

## Mount, fstab e Opzioni di Montaggio

### Comandi di Mount

```bash
# Montare un filesystem
mount /dev/sdb1 /mnt/dati                 # Mount con auto-detect tipo
mount -t ext4 /dev/sdb1 /mnt/dati         # Specificando il tipo
mount -t xfs /dev/sdc1 /mnt/storage       # XFS
mount -t nfs server:/share /mnt/nfs       # NFS remoto
mount -t cifs //server/share /mnt/smb -o user=admin  # SMB/CIFS

# Opzioni di mount
mount -o ro /dev/sdb1 /mnt/               # Read-only
mount -o rw,noexec,nosuid /dev/sdb1 /mnt/ # Read-write, no execute, no SUID
mount -o remount,rw /                      # Rimontare con opzioni diverse

# Smontare
umount /mnt/dati
umount -l /mnt/dati                        # Lazy: smonta quando non più in uso
umount -f /mnt/nfs                         # Force: utile per NFS hang

# Chi sta usando il mount point?
fuser -mv /mnt/dati       # Mostra processi che usano il mount
lsof +D /mnt/dati         # File aperti nel mount point

# Visualizzare mount correnti
mount | column -t          # Tutti i mount
df -hT                     # Spazio disco per filesystem con tipo
lsblk -f                   # Dispositivi con UUID, label, tipo, mount
findmnt                    # Albero dei mount point
findmnt -t ext4,xfs        # Solo filesystem specifici
cat /proc/mounts           # Mount reali dal kernel
```

### Bind Mount

Un bind mount monta una directory esistente in un secondo punto dell'albero. Non è un symlink — è lo stesso filesystem montato in due punti.

```bash
# Bind mount: rende /data/www accessibile anche come /var/www/html
mount --bind /data/www /var/www/html

# Bind mount read-only
mount --bind /data/www /var/www/html
mount -o remount,ro,bind /var/www/html

# In fstab:
# /data/www  /var/www/html  none  bind  0  0

# Uso tipico:
# - Esporre una directory in un chroot
# - Condividere dati tra container/namespace
# - Mount read-only di directory altrimenti scrivibili
```

### /etc/fstab — Campo per campo

```bash
# Formato:
# <device>      <mount>    <type>  <options>         <dump> <pass>

# Esempio completo:
UUID=a1b2c3d4   /          ext4    defaults           0      1
UUID=e5f6g7h8   /home      ext4    defaults,nodev     0      2
UUID=i9j0k1l2   /var       xfs     defaults,noatime   0      2
UUID=m3n4o5p6   /tmp       ext4    defaults,noexec,nosuid,nodev  0  2
UUID=q7r8s9t0   swap       swap    defaults           0      0
/dev/sdb1       /data      xfs     defaults,nofail    0      2
tmpfs           /tmp       tmpfs   defaults,noexec,nosuid,nodev,size=4G  0  0
//server/share  /mnt/smb   cifs    credentials=/root/.smbcred,uid=1000  0  0
server:/export  /mnt/nfs   nfs     defaults,_netdev   0      0
```

**Campo 1 — Device:**

```bash
# UUID (raccomandato): non cambia se si riordina i dischi
UUID=a1b2c3d4-e5f6-7890-abcd-ef1234567890

# Trovare UUID:
blkid                      # Tutti i dispositivi
blkid /dev/sda1            # Specifico
lsblk -f                   # Con UUID e label

# LABEL: nome assegnato al filesystem
LABEL=dati

# Assegnare label:
e2label /dev/sdb1 dati          # ext4
xfs_admin -L dati /dev/sdb1    # XFS

# Device path (SCONSIGLIATO per dischi — può cambiare)
/dev/sda1                  # Può diventare /dev/sdb1 dopo aggiunta disco

# Device mapper (LVM, LUKS)
/dev/mapper/vg0-lv_data

# PARTUUID (per partizioni GPT, usato da systemd-boot)
PARTUUID=12345678-01
```

**Campo 2 — Mount point:** Directory dove il filesystem viene montato. Deve esistere.

**Campo 3 — Type:** `ext4`, `xfs`, `btrfs`, `zfs`, `swap`, `tmpfs`, `nfs`, `cifs`, `vfat`, `ntfs`, `auto`.

**Campo 4 — Options:**

```bash
# Opzioni comuni
defaults        # rw,suid,dev,exec,auto,nouser,async (tutto abilitato)
ro              # Read-only
rw              # Read-write (default)
noexec          # Impedisce esecuzione di binari (sicurezza per /tmp)
nosuid          # Ignora SUID/SGID bit (sicurezza per /tmp, /home)
nodev           # Ignora device file (sicurezza: impedisce device fake)
noatime         # Non aggiornare atime (performance: meno scritture)
relatime        # Aggiorna atime solo se mtime è più recente (default moderno)
nodiratime      # Non aggiornare atime delle directory
sync            # I/O sincrono (più lento, più sicuro per USB)
async           # I/O asincrono (default, più veloce)
auto            # Montato automaticamente al boot (default)
noauto          # Non montare al boot (mount manuale)
user            # Permetti a utenti normali di montare
nouser          # Solo root può montare (default)
nofail          # Non bloccare il boot se il dispositivo non c'è
_netdev         # Il device richiede rete (NFS, iSCSI, CIFS)
x-systemd.automount  # Monta al primo accesso (systemd)
discard         # Abilita TRIM per SSD
barrier=0       # Disabilita write barrier (pericoloso, performance)
commit=60       # Intervallo commit dati su disco (secondi)
```

**Campo 5 — Dump:** `0` = no backup dump, `1` = backup. Praticamente obsoleto.

**Campo 6 — Pass (fsck order):**
- `0` = non controllare al boot
- `1` = controllare per primo (solo per `/`)
- `2` = controllare dopo il root filesystem

```bash
# Applicare modifiche a fstab senza reboot
mount -a              # Monta tutto ciò che è in fstab e non ancora montato
systemctl daemon-reload  # Se si usano opzioni systemd

# Verificare fstab PRIMA del reboot!
findmnt --verify      # Controlla errori di sintassi in fstab
mount -a              # Testa il mount
```

---

## Confronto Filesystem: ext4 vs XFS vs Btrfs vs ZFS

### Matrice di confronto

| Caratteristica | **ext4** | **XFS** | **Btrfs** | **ZFS** |
|---|---|---|---|---|
| **Maturità** | Molto alta | Molto alta | Alta | Molto alta |
| **Dimensione max volume** | 1 EiB | 8 EiB | 16 EiB | 256 ZiB |
| **Dimensione max file** | 16 TiB | 8 EiB | 16 EiB | 16 EiB |
| **Snapshot** | No | No | Sì (nativo) | Sì (nativo) |
| **Compressione** | No | No | Sì (zlib, lzo, zstd) | Sì (lz4, zstd, gzip) |
| **Deduplicazione** | No | No | Offline | Online/Offline |
| **Checksum dati** | No (solo metadati) | No (solo metadati) | Sì | Sì |
| **RAID nativo** | No (usa md/LVM) | No (usa md/LVM) | Sì (RAID 0,1,5,6,10) | Sì (RAID-Z1,Z2,Z3) |
| **Copy-on-Write** | No | No | Sì | Sì |
| **Shrink (riduzione)** | Sì | No | Sì | No |
| **Grow (espansione)** | Sì (online) | Sì (online) | Sì (online) | Sì (online) |
| **Riparazione online** | No | No | Parziale (scrub) | Sì (scrub + resilver) |
| **Licenza kernel** | GPL | GPL | GPL | CDDL (modulo esterno) |
| **Default distro** | Debian, Ubuntu | RHEL, Rocky, SUSE | Fedora, openSUSE | FreeBSD, Ubuntu (opzionale) |

### ext4 — Il workhouse affidabile

Il filesystem più maturo e testato. Evoluzione di ext3 con extent, allocazione ritardata e journal con checksum.

```bash
# Creare ext4
mkfs.ext4 /dev/sdb1
mkfs.ext4 -L dati -N 10000000 /dev/sdb1  # Con label e inode specifici

# Informazioni
tune2fs -l /dev/sdb1
dumpe2fs /dev/sdb1 | less

# Tuning
tune2fs -c 30 /dev/sdb1      # Forza fsck ogni 30 mount
tune2fs -i 90d /dev/sdb1     # Forza fsck ogni 90 giorni
tune2fs -m 1 /dev/sdb1       # Spazio riservato: 1% (default 5%)
tune2fs -o journal_data_writeback /dev/sdb1  # Performance (meno sicuro)

# Quando usare: desktop, server generici, VM root disk, quando serve shrink
```

### XFS — Performance con file grandi

Eccellente con file grandi e I/O parallelo. Non supporta shrink, ma la sua allocazione parallela per allocation group lo rende velocissimo sotto carico.

```bash
# Creare XFS
mkfs.xfs /dev/sdb1
mkfs.xfs -L storage /dev/sdb1

# Informazioni
xfs_info /dev/sdb1
xfs_info /mnt/storage     # O dal mount point

# Espandere (solo grow, no shrink!)
xfs_growfs /mnt/storage   # Espande al massimo dello spazio disponibile

# Defrag online
xfs_fsr /mnt/storage      # File system reorganizer

# Quando usare: database (PostgreSQL, MySQL), storage grandi file,
# media server, backup, qualsiasi carico I/O-intensivo
```

### Btrfs — Il filesystem moderno Linux

Copy-on-Write con snapshot, compressione e RAID integrati. In rapido miglioramento, default su Fedora.

```bash
# Creare Btrfs
mkfs.btrfs /dev/sdb1
mkfs.btrfs -L nas /dev/sdb1 /dev/sdc1  # RAID1 su due dischi

# Subvolumi (partizioni logiche dentro Btrfs)
btrfs subvolume create /mnt/@
btrfs subvolume create /mnt/@home
btrfs subvolume create /mnt/@snapshots

# Snapshot (istantaneo, copy-on-write)
btrfs subvolume snapshot /mnt/@ /mnt/@snapshots/2026-05-22
btrfs subvolume snapshot -r /mnt/@ /mnt/@snapshots/readonly  # Read-only

# Compressione
mount -o compress=zstd /dev/sdb1 /mnt

# Scrub (verifica integrità)
btrfs scrub start /mnt
btrfs scrub status /mnt

# Balance (ribilanciamento RAID/allocazione)
btrfs balance start /mnt

# Quando usare: desktop con snapshot, NAS domestico, sviluppo (rollback facile),
# dual-boot (subvolumi per OS diversi)
```

### ZFS — Enterprise-grade integrity

Il filesystem più robusto per integrità dati. Checksum end-to-end, RAID-Z, ARC cache, pool di storage. Su Linux tramite OpenZFS (modulo kernel separato, licenza CDDL).

```bash
# Installare OpenZFS (Ubuntu)
apt install zfsutils-linux

# Creare pool
zpool create tank /dev/sdb             # Disco singolo
zpool create tank mirror /dev/sdb /dev/sdc  # Mirror (RAID1)
zpool create tank raidz1 /dev/sdb /dev/sdc /dev/sdd  # RAID-Z1

# Dataset (equivalente dei subvolumi)
zfs create tank/data
zfs create tank/backup

# Snapshot
zfs snapshot tank/data@2026-05-22
zfs list -t snapshot
zfs rollback tank/data@2026-05-22

# Compressione
zfs set compression=lz4 tank/data

# Quota e reservation
zfs set quota=100G tank/data
zfs set reservation=50G tank/data

# Scrub (verifica integrità)
zpool scrub tank
zpool status tank     # Mostra stato, errori, ultimo scrub

# Quando usare: NAS enterprise, storage critico, server di backup,
# ambienti dove l'integrità dati è priorità assoluta
```

### Matrice decisionale rapida

| Scenario | Filesystem consigliato | Motivo |
|---|---|---|
| Server generico | ext4 | Maturo, prevedibile, ben supportato |
| Database PostgreSQL/MySQL | XFS | Performance I/O parallelo, file grandi |
| NAS domestico / piccolo ufficio | Btrfs | Snapshot, compressione, RAID semplice |
| Storage enterprise critico | ZFS | Integrità, RAID-Z, scrub, resilienza |
| Root filesystem desktop | ext4 o Btrfs | ext4: affidabilità; Btrfs: snapshot rollback |
| File temporanei / build | tmpfs | In RAM, velocità massima |
| Boot partition (/boot) | ext4 | Compatibilità universale con bootloader |
| Partizione EFI | FAT32 (vfat) | Richiesto dallo standard UEFI |

---

## Partizionamento Disco: fdisk, gdisk, parted

### MBR vs GPT

| Aspetto | **MBR** (Master Boot Record) | **GPT** (GUID Partition Table) |
|---|---|---|
| Introdotto | 1983 | ~2005 (con UEFI) |
| Dimensione max disco | 2 TiB | 9.4 ZiB |
| Partizioni primarie | 4 (3 + 1 extended) | 128 |
| Ridondanza | Nessuna | Backup GPT in fondo al disco |
| Checksum | No | CRC32 su header e tabella |
| Boot | BIOS (legacy) | UEFI (+ BIOS con BIOS boot partition) |
| Identificazione | Tipo byte (0x83 = Linux) | GUID tipo partizione |

**Regola:** usare GPT su tutti i dischi nuovi. MBR solo per compatibilità con hardware legacy.

### fdisk — Partizionamento MBR (e GPT moderno)

```bash
# fdisk interattivo (MBR di default, supporta GPT nelle versioni moderne)
fdisk /dev/sdb

# Comandi fdisk:
# m = mostra help
# p = stampa tabella partizioni
# n = nuova partizione
# d = elimina partizione
# t = cambia tipo partizione
# w = scrivi e esci
# q = esci senza salvare
# g = crea nuova tabella GPT
# o = crea nuova tabella MBR

# Esempio non-interattivo con sfdisk
echo ",,L" | sfdisk /dev/sdb   # Una partizione Linux, tutto il disco

# Visualizzare partizioni
fdisk -l /dev/sdb
```

### gdisk — Partizionamento GPT

```bash
# gdisk è l'equivalente di fdisk specifico per GPT
gdisk /dev/sdb

# Comandi gdisk:
# p = stampa partizioni
# n = nuova partizione
# d = elimina
# t = cambia tipo
# w = scrivi e esci
# i = info partizione
# o = crea nuova tabella GPT vuota

# Esempio: disco GPT con partizione EFI + root + home
gdisk /dev/sdb
# n → 1 → first sector: default → last sector: +512M → type: EF00 (EFI)
# n → 2 → first sector: default → last sector: +50G → type: 8300 (Linux)
# n → 3 → first sector: default → last sector: default → type: 8300 (Linux)
# w
```

### parted — Partizionamento avanzato

```bash
# parted supporta MBR e GPT, operazioni immediate (non a buffer come fdisk)
# ATTENZIONE: parted applica i cambiamenti immediatamente!

# Creare tabella GPT
parted /dev/sdb mklabel gpt

# Creare partizioni
parted /dev/sdb mkpart primary ext4 1MiB 513MiB    # EFI
parted /dev/sdb mkpart primary ext4 513MiB 50GiB    # Root
parted /dev/sdb mkpart primary ext4 50GiB 100%      # Home

# Impostare flag EFI
parted /dev/sdb set 1 esp on

# Verificare allineamento
parted /dev/sdb align-check optimal 1
# 1 aligned

# Stampa info
parted /dev/sdb print
```

### Allineamento partizioni

L'allineamento a 1 MiB (2048 settori da 512 byte) è lo standard moderno. Garantisce che le partizioni siano allineate con le erase block degli SSD e i boundary dei RAID.

```bash
# Verificare allineamento
parted /dev/sdb align-check optimal 1

# fdisk: il settore iniziale di default è già allineato (2048)
# parted: usare MiB come unità (1MiB, 513MiB, ecc.)

# Allineamento errato causa:
# - Calo performance SSD (write amplification)
# - Calo performance RAID (operazioni cross-stripe)
# - Overhead I/O su tutte le operazioni

# Dopo il partizionamento, informare il kernel
partprobe /dev/sdb
# oppure
blockdev --rereadpt /dev/sdb
```

---

## LVM — Logical Volume Manager

LVM aggiunge un livello di astrazione tra i dischi fisici e i filesystem. Permette ridimensionamento, snapshot e gestione flessibile dello storage senza vincoli rigidi delle partizioni tradizionali.

### Architettura LVM

```
Physical Volumes (PV)     Volume Groups (VG)     Logical Volumes (LV)
┌─────────┐               ┌───────────────┐       ┌──────────────┐
│ /dev/sdb1│──┐            │               │       │ lv_root      │ → ext4 → /
└─────────┘  ├──────────→  │    vg0         │──────→│ lv_home      │ → xfs  → /home
┌─────────┐  │            │               │       │ lv_data      │ → xfs  → /data
│ /dev/sdc1│──┘            │               │       │ lv_swap      │ → swap
└─────────┘               └───────────────┘       └──────────────┘

PV: disco o partizione fisica marcata per LVM
VG: pool di storage che raggruppa uno o più PV
LV: "partizione virtuale" creata dal VG, su cui si crea il filesystem
```

### Physical Volume (PV)

```bash
# Creare PV
pvcreate /dev/sdb1
pvcreate /dev/sdc1
pvcreate /dev/sdd         # Intero disco (senza partizionare)

# Visualizzare PV
pvs                        # Riepilogo compatto
pvdisplay                  # Dettagli completi
pvdisplay /dev/sdb1        # Specifico

# Rimuovere PV (dopo aver svuotato)
pvremove /dev/sdb1
```

### Volume Group (VG)

```bash
# Creare VG
vgcreate vg0 /dev/sdb1 /dev/sdc1

# Estendere VG con nuovo disco
vgextend vg0 /dev/sdd1

# Ridurre VG (rimuovere disco)
pvmove /dev/sdb1           # Migra dati da sdb1 ad altri PV
vgreduce vg0 /dev/sdb1    # Rimuove sdb1 dal VG

# Visualizzare VG
vgs                        # Riepilogo
vgdisplay                  # Dettagli
vgdisplay vg0

# Info VG:
# VG Size: spazio totale del pool
# PE Size: Physical Extent size (default 4 MiB, unità di allocazione)
# Free PE: extent liberi
```

### Logical Volume (LV)

```bash
# Creare LV
lvcreate -L 50G -n lv_root vg0        # 50 GB
lvcreate -L 100G -n lv_home vg0       # 100 GB
lvcreate -l 100%FREE -n lv_data vg0   # Tutto lo spazio rimanente
lvcreate -L 8G -n lv_swap vg0         # 8 GB per swap

# Creare filesystem sui LV
mkfs.ext4 /dev/vg0/lv_root
mkfs.xfs /dev/vg0/lv_home
mkfs.xfs /dev/vg0/lv_data
mkswap /dev/vg0/lv_swap

# Montare
mount /dev/vg0/lv_root /mnt/root
mount /dev/vg0/lv_home /mnt/home

# fstab con LVM
# /dev/vg0/lv_root  /     ext4  defaults  0  1
# /dev/vg0/lv_home  /home xfs   defaults  0  2

# Visualizzare LV
lvs                        # Riepilogo
lvdisplay                  # Dettagli
lvdisplay /dev/vg0/lv_root
```

### Ridimensionamento LVM

```bash
# === ESPANSIONE (la più comune) ===

# 1. Estendere il LV
lvextend -L +20G /dev/vg0/lv_home       # Aggiungi 20 GB
lvextend -l +100%FREE /dev/vg0/lv_data   # Usa tutto lo spazio libero
lvextend -L 150G /dev/vg0/lv_home        # Porta a 150 GB totali

# 2. Espandere il filesystem (ONLINE, senza smontare)
resize2fs /dev/vg0/lv_home              # ext4
xfs_growfs /mnt/home                     # XFS (usa il mount point!)

# Shortcut: lvextend + resize in un comando
lvextend -r -L +20G /dev/vg0/lv_home    # -r = resize filesystem automatico

# === RIDUZIONE (solo ext4, non XFS!) ===
# ATTENZIONE: operazione rischiosa, fare backup prima!

# 1. Smontare
umount /mnt/home

# 2. Controllare filesystem
e2fsck -f /dev/vg0/lv_home

# 3. Ridurre il filesystem
resize2fs /dev/vg0/lv_home 80G

# 4. Ridurre il LV
lvreduce -L 80G /dev/vg0/lv_home

# 5. Rimontare
mount /dev/vg0/lv_home /mnt/home
```

### LVM Snapshot

```bash
# Creare snapshot (copy-on-write)
lvcreate -L 10G -s -n snap_home /dev/vg0/lv_home

# Lo snapshot contiene solo i blocchi che cambiano dopo la creazione.
# 10G = spazio per i delta. Se si riempie, lo snapshot diventa invalido.

# Montare lo snapshot (read-only per backup)
mount -o ro /dev/vg0/snap_home /mnt/snap

# Ripristinare dallo snapshot
umount /mnt/home
lvconvert --merge /dev/vg0/snap_home
# Il LV originale torna allo stato dello snapshot al prossimo mount

# Rimuovere snapshot
lvremove /dev/vg0/snap_home

# Monitorare utilizzo snapshot
lvs
# LV        VG   Attr       LSize  Pool Origin Data%
# snap_home vg0  swi-a-s--- 10.00g      lv_home 15.3%
```

### Thin Provisioning

Allocazione "thin" — il LV mostra una dimensione ma consuma spazio solo per i dati realmente scritti.

```bash
# Creare thin pool
lvcreate -L 200G --thinpool thin_pool vg0

# Creare thin LV (sovrallocazione)
lvcreate -V 100G --thin -n lv_vm1 vg0/thin_pool
lvcreate -V 100G --thin -n lv_vm2 vg0/thin_pool
lvcreate -V 100G --thin -n lv_vm3 vg0/thin_pool
# Totale: 300G allocati logicamente su 200G fisici

# Monitorare utilizzo reale
lvs -a
# LV        Data%   # Percentuale realmente usata

# ATTENZIONE: monitorare attentamente!
# Se il thin pool si riempie al 100%, tutti i thin LV si bloccano.
```

---

## Gestione File e Directory Avanzata

### Find — Ricerca Avanzata

```bash
# Per nome
find /var/log -name "*.log"                # Case-sensitive
find / -iname "readme*"                    # Case-insensitive

# Per tipo
find /etc -type f                          # Solo file
find /etc -type d                          # Solo directory
find /dev -type l                          # Solo symlink
find /dev -type b                          # Solo block device
find /dev -type c                          # Solo character device
find /run -type s                          # Solo socket

# Per dimensione
find / -size +100M                         # File > 100MB
find / -size +1G                           # File > 1GB
find /tmp -size 0 -type f                  # File vuoti

# Per tempo
find /var/log -mtime -7                    # Modificati negli ultimi 7 giorni
find /tmp -atime +30                       # Non acceduti da 30+ giorni
find / -newer /etc/passwd                  # Più recenti di /etc/passwd
find / -newermt "2026-05-01"               # Più recenti di una data

# Per permessi
find / -perm -4000 -type f                 # File con SUID bit
find / -perm -2000 -type f                 # File con SGID bit
find /home -perm -o+w -type f              # File world-writable
find / -nouser -o -nogroup                 # File senza owner o group valido

# Per owner
find /var -user www-data                   # File di www-data
find / -group docker                       # File del gruppo docker

# Azioni
find /tmp -name "*.tmp" -delete            # Cancella
find . -name "*.sh" -exec chmod +x {} \;   # Esegui comando
find /var/log -name "*.log" -size +50M -exec ls -lh {} \;
find /tmp -mtime +7 -exec rm -f {} +       # + è più efficiente di \;

# Combinazioni
find / -type f -size +100M -mtime +30 -name "*.log"
find / -type f \( -name "*.log" -o -name "*.tmp" \) -size +10M
```

### Compressione e Archiviazione

```bash
# tar: archivia (e opzionalmente comprime)
tar czf archivio.tar.gz /directory/        # Crea archivio gzip
tar cjf archivio.tar.bz2 /directory/       # Crea archivio bzip2
tar cJf archivio.tar.xz /directory/        # Crea archivio xz (migliore compressione)
tar xzf archivio.tar.gz                    # Estrai gzip
tar xzf archivio.tar.gz -C /destinazione/  # Estrai in directory specifica
tar tzf archivio.tar.gz                    # Lista contenuto senza estrarre

# gzip, bzip2, xz: compressione singolo file
gzip file.log                              # → file.log.gz (originale eliminato)
gunzip file.log.gz                         # → file.log
bzip2 file.log                             # Migliore compressione di gzip
xz file.log                               # Migliore compressione assoluta

# zstd: compressione moderna (veloce + buon rapporto)
zstd file.log                              # → file.log.zst
zstd -d file.log.zst                       # Decomprimi
tar --zstd -cf archivio.tar.zst /dir/      # tar + zstd

# rsync: copia/sincronizzazione avanzata
rsync -avz /source/ /destination/                  # Locale
rsync -avz -e ssh /source/ user@host:/dest/        # Remoto via SSH
rsync -avz --delete /source/ /destination/         # Sincronizza (cancella extra)
rsync -avz --exclude="*.log" /source/ /dest/       # Escludi pattern
rsync -avz --progress --partial /source/ /dest/    # Mostra progresso, riprendi
```

---

## Attributi Estesi e Filesystem Speciali

### Attributi Immutabili (chattr)

```bash
# Rendere un file immutabile (nemmeno root può modificarlo/cancellarlo)
chattr +i /etc/critical-config
# Rimuovere immutabilità
chattr -i /etc/critical-config

# Append-only (si può solo aggiungere, non modificare/cancellare)
chattr +a /var/log/audit.log

# No dump (escludi da backup dump)
chattr +d /tmp/cache

# Secure deletion (sovrascrittura a zero alla cancellazione — solo ext2/3)
chattr +s /sensitive/file

# Visualizzare attributi
lsattr /etc/critical-config
# ----i--------e-- /etc/critical-config

lsattr -R /etc/ | grep -- "-i-"  # Trovare file immutabili

# SICUREZZA: usare +i su file critici che non dovrebbero mai cambiare
# Esempio: /etc/passwd, /etc/shadow, /etc/sudoers dopo configurazione
# ATTENZIONE: impedisce anche aggiornamenti di sistema su quei file!
```

### Extended Attributes (xattr)

```bash
# Attributi user-defined
setfattr -n user.description -v "File di configurazione backup" /etc/backup.conf
getfattr -n user.description /etc/backup.conf
getfattr -d /etc/backup.conf  # Tutti gli attributi

# Namespace:
# user.*     — attributi utente (qualsiasi utente con permessi)
# security.* — SELinux, capabilities
# system.*   — ACL (system.posix_acl_access)
# trusted.*  — solo root
```

---

## /proc e /sys — Virtual Filesystem Deep Dive

### /proc — Informazioni kernel e processi

```bash
# === INFORMAZIONI HARDWARE ===
cat /proc/cpuinfo          # Modello CPU, core, flag (avx2, aes, ecc.)
cat /proc/meminfo          # Memoria dettagliata
cat /proc/version          # Versione kernel completa
cat /proc/modules          # Moduli kernel caricati (= lsmod)
cat /proc/interrupts       # Interrupt hardware
cat /proc/ioports          # Porte I/O
cat /proc/dma              # Canali DMA
cat /proc/partitions       # Partizioni riconosciute
cat /proc/filesystems      # Filesystem supportati
cat /proc/swaps            # Dispositivi swap attivi
cat /proc/cmdline          # Parametri boot kernel

# === INFORMAZIONI RETE ===
cat /proc/net/dev          # Statistiche interfacce di rete
cat /proc/net/tcp          # Connessioni TCP attive
cat /proc/net/udp          # Connessioni UDP attive
cat /proc/net/arp          # Tabella ARP
cat /proc/net/route        # Tabella routing
cat /proc/net/snmp         # Statistiche SNMP (errori, retransmit)

# === PER-PROCESSO ===
# Ogni processo ha una directory /proc/[PID]/
ls /proc/1/                # PID 1 = systemd (o init)

cat /proc/1/status         # Stato processo (nome, stato, memoria, thread)
cat /proc/1/cmdline        # Command line (separata da \0)
cat /proc/1/environ        # Variabili ambiente
cat /proc/1/maps           # Mappatura memoria (librerie, heap, stack)
cat /proc/1/fd/            # File descriptor aperti (symlink ai file)
ls -l /proc/1/fd/          # Vedere a cosa puntano i fd
cat /proc/1/limits         # Resource limits (ulimit)
cat /proc/1/io             # Statistiche I/O (byte letti/scritti)
cat /proc/1/oom_score      # Score per l'OOM killer
cat /proc/1/cgroup         # Appartenenza a cgroup

# Processo corrente: /proc/self
cat /proc/self/status

# === PARAMETRI KERNEL TUNABLE (/proc/sys/) ===
# Leggere
cat /proc/sys/vm/swappiness               # Tendenza allo swap (0-200)
cat /proc/sys/vm/dirty_ratio               # % RAM dirty prima di flush
cat /proc/sys/vm/dirty_background_ratio    # % RAM dirty per flush background
cat /proc/sys/vm/overcommit_memory         # Politica overcommit
cat /proc/sys/vm/vfs_cache_pressure        # Pressione su cache dentry/inode

cat /proc/sys/net/ipv4/ip_forward          # Forwarding IPv4
cat /proc/sys/net/core/somaxconn           # Backlog max connessioni
cat /proc/sys/net/ipv4/tcp_max_syn_backlog # Backlog SYN TCP

cat /proc/sys/fs/file-max                  # Max file descriptor di sistema
cat /proc/sys/fs/file-nr                   # fd allocati/usati/max
cat /proc/sys/fs/inotify/max_user_watches  # Max watch inotify

cat /proc/sys/kernel/pid_max               # Max PID
cat /proc/sys/kernel/threads-max           # Max thread

# Modificare temporaneamente (non persiste al reboot)
echo 10 > /proc/sys/vm/swappiness
echo 1 > /proc/sys/net/ipv4/ip_forward

# Modificare persistentemente via sysctl
sysctl vm.swappiness=10
sysctl -w net.ipv4.ip_forward=1

# Persistente in /etc/sysctl.conf o /etc/sysctl.d/99-custom.conf
# vm.swappiness = 10
# net.ipv4.ip_forward = 1
sysctl -p    # Ricarica
```

### /sys — Sysfs Device Information

```bash
# === RETE ===
cat /sys/class/net/eth0/address        # MAC address
cat /sys/class/net/eth0/operstate      # up/down
cat /sys/class/net/eth0/speed          # Velocità link (Mbps)
cat /sys/class/net/eth0/mtu            # MTU

# === STORAGE ===
cat /sys/block/sda/size                # Dimensione in settori (×512 = byte)
cat /sys/block/sda/queue/scheduler     # Scheduler I/O
cat /sys/block/sda/queue/nr_requests   # Profondità coda I/O
cat /sys/block/sda/queue/read_ahead_kb # Read-ahead
cat /sys/block/sda/queue/rotational    # 1=HDD, 0=SSD

# === TEMPERATURA ===
cat /sys/class/thermal/thermal_zone0/temp  # milligradi
cat /sys/class/thermal/thermal_zone0/type  # tipo sensore

# === POWER ===
cat /sys/class/power_supply/BAT0/capacity  # % batteria
cat /sys/class/power_supply/BAT0/status    # Charging/Discharging

# === RESCAN DISPOSITIVI ===
echo 1 > /sys/block/sda/device/rescan     # Rescan disco (hot-plug/resize)
echo "- - -" > /sys/class/scsi_host/host0/scan  # Scan SCSI bus
```

---

## tmpfs e ramfs

### tmpfs

Filesystem in memoria RAM (con possibilità di swap). I dati vengono persi al reboot.

```bash
# Montare tmpfs
mount -t tmpfs -o size=2G tmpfs /mnt/ramdisk

# In fstab:
# tmpfs  /mnt/ramdisk  tmpfs  defaults,size=2G,noexec,nosuid  0  0

# Usi comuni:
# /tmp        — file temporanei
# /run        — dati runtime (PID, socket)
# /dev/shm    — shared memory POSIX (IPC)

# Verificare tmpfs montati
df -hT | grep tmpfs

# Vantaggi:
# - Velocissimo (nessun I/O disco)
# - Dimensione dinamica (usa RAM solo per i dati effettivi)
# - Può usare swap se la RAM non basta
# - Automaticamente pulito al reboot

# Sizing:
# - Default: 50% della RAM
# - Specificare con size=: percentuale o valore assoluto
mount -t tmpfs -o size=50% tmpfs /mnt/ramdisk  # 50% RAM
mount -t tmpfs -o size=4G tmpfs /mnt/ramdisk    # 4 GB fissi

# Sicurezza per /tmp:
mount -t tmpfs -o size=4G,noexec,nosuid,nodev tmpfs /tmp
# noexec: impedisce esecuzione di binari
# nosuid: ignora SUID/SGID
# nodev:  ignora device file
```

### ramfs

Filesystem in RAM pura (senza swap, senza limite). Meno comune di tmpfs — da usare solo in casi specifici.

```bash
# Montare ramfs
mount -t ramfs ramfs /mnt/ramdisk

# DIFFERENZE da tmpfs:
# - ramfs non ha limite di dimensione: può consumare TUTTA la RAM
# - ramfs non usa swap
# - ramfs non supporta l'opzione size=
# - ramfs non è visibile in df

# Uso: situazioni dove lo swap non è accettabile (crypto keys in memoria)
# Per tutto il resto: preferire tmpfs
```

### /dev/shm — Shared Memory

```bash
# Shared memory POSIX — tmpfs montato automaticamente
df -hT /dev/shm
# tmpfs  tmpfs  16G  4.0M  16G  1% /dev/shm

# Usato per:
# - IPC tra processi (sem_open, shm_open)
# - PostgreSQL shared_buffers (quando huge_pages = off)
# - Chromium/Firefox shared memory
# - Container Docker (default 64M, spesso insufficiente)

# Ridimensionare:
mount -o remount,size=4G /dev/shm
```

---

## Manutenzione Filesystem

### fsck — Filesystem Check

```bash
# REGOLA D'ORO: MAI fsck su filesystem montato!

# Controllare ext4
fsck.ext4 /dev/sdb1                # Check base
e2fsck -f /dev/sdb1                # Force check (anche se "clean")
e2fsck -f -y /dev/sdb1             # Auto-fix (risponde "yes" a tutto)
e2fsck -f -n /dev/sdb1             # Dry-run (solo diagnosi, no modifiche)

# Controllare XFS
xfs_repair /dev/sdb1               # Riparazione XFS
xfs_repair -n /dev/sdb1            # Dry-run
xfs_repair -L /dev/sdb1            # Forza reset log (ultimo resort!)

# Controllare Btrfs
btrfs check /dev/sdb1              # Check (read-only)
btrfs check --repair /dev/sdb1     # Riparazione (pericoloso, ultimo resort)
btrfs scrub start /mnt             # Verifica integrità online (preferito)

# Forzare fsck al prossimo boot
touch /forcefsck                   # Crea file sentinella
# oppure
tune2fs -C 100 /dev/sda2          # Imposta mount count alto

# Controllare stato journal
dumpe2fs /dev/sdb1 | grep -i journal
```

### tune2fs — Tuning ext4

```bash
# Informazioni complete
tune2fs -l /dev/sdb1

# Parametri importanti
tune2fs -m 1 /dev/sdb1          # Spazio riservato: 1% (default 5%)
                                  # Su disco da 2 TB, 5% = 100 GB sprecati!
tune2fs -c 0 /dev/sdb1          # Disabilita fsck periodico per mount count
tune2fs -i 0 /dev/sdb1          # Disabilita fsck periodico per tempo
tune2fs -c 30 -i 180d /dev/sdb1 # fsck ogni 30 mount O 180 giorni

# Abilitare/disabilitare feature
tune2fs -O ^has_journal /dev/sdb1  # Rimuovi journal (sconsigliato)
tune2fs -o journal_data /dev/sdb1  # Journal completo (dati + metadati)

# Cambiare label
tune2fs -L "MyData" /dev/sdb1
e2label /dev/sdb1 "MyData"        # Alternativa

# Cambiare UUID (raro, usare con cautela)
tune2fs -U random /dev/sdb1
```

### xfs_admin e xfs_repair

```bash
# Informazioni XFS
xfs_info /mnt/data                 # Da mount point
xfs_info /dev/sdb1                 # Da device

# Cambiare label/UUID
xfs_admin -L "Storage" /dev/sdb1   # Label
xfs_admin -U generate /dev/sdb1    # Nuovo UUID

# Riparazione
xfs_repair /dev/sdb1               # Riparazione standard
xfs_repair -n /dev/sdb1            # Dry-run
xfs_repair -L /dev/sdb1            # Reset log (dati nel log vengono persi!)

# Defrag online
xfs_fsr /mnt/data                  # Riorganizza file frammentati
xfs_fsr -v /mnt/data               # Verbose

# Diagnostica
xfs_db /dev/sdb1                   # Debug interattivo
xfs_metadump /dev/sdb1 meta.dump   # Dump metadati per analisi
```

---

## Quote Disco

Le quote limitano lo spazio disco e il numero di inode per utente o gruppo. Fondamentali su server multi-utente, mail server, hosting.

### Attivazione quote

```bash
# 1. Abilitare le opzioni in fstab
# /dev/sdb1  /home  ext4  defaults,usrquota,grpquota  0  2

# Per XFS:
# /dev/sdb1  /home  xfs  defaults,usrquota,grpquota  0  2

# 2. Rimontare
mount -o remount /home

# 3. Per ext4: creare file di quota e attivare
quotacheck -cugm /home     # Crea aquota.user e aquota.group
quotaon /home               # Attiva quote

# Per XFS: le quote sono gestite dal kernel, non servono quotacheck/quotaon
# Basta l'opzione in fstab
```

### Gestire quote utente

```bash
# Impostare quota per un utente
edquota -u mario
# Apre l'editor con:
# Filesystem  blocks  soft   hard   inodes  soft  hard
# /dev/sdb1   1024    5242880  6291456  100    0     0
#                     5 GB soft  6 GB hard

# Spiegazione limiti:
# soft limit: avviso quando superato, grace period per rientrare
# hard limit: limite assoluto, non superabile
# blocks: spazio in KB
# inodes: numero di file

# Impostare quota da command line
setquota -u mario 5242880 6291456 0 0 /home
# Formato: softblock hardblock softinode hardinode

# Impostare grace period
edquota -t                 # Periodo di grazia (default 7 giorni)
# Block grace period: 7 days
# Inode grace period: 7 days

# Copiare quota da un utente a un altro
edquota -p mario anna      # Anna riceve le stesse quote di mario
```

### Gestire quote gruppo

```bash
edquota -g developers      # Quota per il gruppo developers
setquota -g developers 10485760 12582912 0 0 /home  # 10 GB soft, 12 GB hard
```

### Monitorare quote

```bash
# Report quote di tutti gli utenti
repquota /home
repquota -a                # Tutti i filesystem con quote

# Esempio output:
# *** Report for user quotas on device /dev/sdb1
# Block grace time: 7days; Inode grace time: 7days
#                   Block limits                File limits
# User          used  soft    hard  grace  used  soft  hard  grace
# ----          ----  ----    ----  -----  ----  ----  ----  -----
# mario    -- 1048576 5242880 6291456          234     0     0
# anna     -+ 5500000 5242880 6291456  6days  1200     0     0
#            ^-- + indica soft limit superato, con grace period attivo

# Quota di un singolo utente
quota -u mario
quota -g developers

# Verificare
quotacheck -avugm          # Ricalcola quote (ext4, filesystem smontato o ro!)
```

---

## Performance Tuning per Workload

### Database (PostgreSQL, MySQL)

```bash
# Filesystem: XFS (preferito) o ext4
# XFS eccelle con I/O parallelo e file grandi (WAL, tablespace)

# Opzioni mount per database:
# /dev/vg0/lv_pgdata  /var/lib/postgresql  xfs  defaults,noatime,nodiratime,nobarrier  0  2
# noatime: elimina scritture atime (inutili per DB)
# nobarrier: performance (solo con controller RAID con batteria!)

# Scheduler I/O per SSD:
echo none > /sys/block/sda/queue/scheduler    # noop/none per SSD
echo mq-deadline > /sys/block/sda/queue/scheduler  # Per HDD

# Persistente in /etc/udev/rules.d/60-scheduler.rules:
# ACTION=="add|change", KERNEL=="sd*", ATTR{queue/rotational}=="0", ATTR{queue/scheduler}="none"
# ACTION=="add|change", KERNEL=="sd*", ATTR{queue/rotational}=="1", ATTR{queue/scheduler}="mq-deadline"

# Read-ahead per database (aumentare per letture sequenziali)
blockdev --setra 4096 /dev/sda    # 2 MB (4096 × 512 byte)

# sysctl per database
# vm.swappiness = 1              # Minimizza swap (non 0: l'OOM killer è più aggressivo)
# vm.dirty_ratio = 40            # % RAM dirty prima di flush sincrono
# vm.dirty_background_ratio = 5  # % RAM dirty per flush background
# vm.overcommit_memory = 2       # No overcommit (PostgreSQL raccomanda)
# vm.overcommit_ratio = 90       # Max commit = swap + 90% RAM

# Transparent Huge Pages: DISABILITARE per database
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag
# Persistente in /etc/default/grub: transparent_hugepage=never
```

### Web Server (Nginx, Apache)

```bash
# Filesystem: ext4 o XFS per contenuti statici
# Separare /var/log su partizione dedicata

# Mount per web content:
# /dev/vg0/lv_www  /var/www  ext4  defaults,noatime,nodev,nosuid  0  2
# nodev,nosuid: sicurezza (nessun device file o SUID in web root)

# sysctl per web server ad alto traffico
# net.core.somaxconn = 65535
# net.ipv4.tcp_max_syn_backlog = 65535
# net.core.netdev_max_backlog = 65535
# net.ipv4.tcp_tw_reuse = 1
# fs.file-max = 2097152
# fs.inotify.max_user_watches = 524288

# Limiti file descriptor per il processo web server
# In /etc/security/limits.conf:
# www-data  soft  nofile  65535
# www-data  hard  nofile  65535

# Oppure nella unit systemd:
# [Service]
# LimitNOFILE=65535
```

### Logging (alta scrittura sequenziale)

```bash
# Filesystem: XFS o ext4
# Dedicare partizione a /var/log (impedisce che log pieni blocchino il sistema)

# Mount per log:
# /dev/vg0/lv_log  /var/log  xfs  defaults,noatime,nodev,nosuid,noexec  0  2
# noexec: impedisce esecuzione di script mascherati da log (sicurezza)

# Write-back per performance logging
# In /etc/fstab per ext4:
# /dev/vg0/lv_log  /var/log  ext4  defaults,noatime,data=writeback,barrier=0,commit=60  0  2
# data=writeback: solo journal metadati (rischio minimo con log sacrificabili)
# commit=60: flush ogni 60 secondi (batch write)

# Log rotation (logrotate) — fondamentale!
# /etc/logrotate.d/myapp:
# /var/log/myapp/*.log {
#     daily
#     rotate 14
#     compress
#     delaycompress
#     missingok
#     notifempty
#     create 640 root adm
# }

# tmpfs per log temporanei (test, sviluppo)
mount -t tmpfs -o size=1G tmpfs /var/log/myapp
```

### SSD Optimization

```bash
# Verificare che sia SSD
cat /sys/block/sda/queue/rotational   # 0 = SSD, 1 = HDD

# Abilitare TRIM
# Opzione 1: TRIM continuo (mount option)
# UUID=xxx  /  ext4  defaults,discard  0  1
# Pro: semplice. Contro: piccolo overhead su ogni delete.

# Opzione 2: TRIM periodico (raccomandato)
systemctl enable fstrim.timer
systemctl start fstrim.timer
# Esegue fstrim settimanale su tutti i filesystem

# Esecuzione manuale
fstrim -v /           # TRIM sul root filesystem
fstrim -av            # TRIM su tutti i filesystem

# Scheduler: none (noop) per SSD NVMe, mq-deadline per SSD SATA
cat /sys/block/nvme0n1/queue/scheduler
echo none > /sys/block/nvme0n1/queue/scheduler

# Ridurre swappiness per SSD
# vm.swappiness = 10  (in /etc/sysctl.d/99-ssd.conf)
```

---

## Best Practices

1. **Separare /var, /home, /tmp su partizioni/LV dedicati**: previene che log o file temporanei riempiano il root filesystem. In caso di /var pieno, il sistema continua a funzionare.

2. **noexec,nosuid,nodev su /tmp e /var/tmp**: impedisce esecuzione di binari, SUID e device file nelle directory temporanee. Riduce la superficie di attacco.

3. **Monitorare spazio disco E inode**: `df -h` e `df -i`. Alerting automatico quando > 80%. Usare Prometheus node_exporter o semplice cron + mail.

4. **UUID in fstab, non device name**: i device name (`/dev/sda`) possono cambiare (aggiunta disco, cambio ordine SCSI). Gli UUID sono stabili.

5. **Permessi minimi**: ogni file e directory con i permessi minimi necessari. Default sicuro: 644 per file, 755 per directory, 600 per chiavi e secret.

6. **ACL per casi complessi**: quando owner/group/other non bastano, usare ACL. Non creare workaround con gruppi ad-hoc o permessi troppo larghi.

7. **Backup di /etc**: versionare `/etc` con `etckeeper` (git) per tracciare ogni modifica alla configurazione di sistema.

8. **LVM per flessibilità**: usare LVM su server. Permette ridimensionamento, snapshot, migrazione senza downtime.

9. **TRIM per SSD**: abilitare `fstrim.timer` per mantenere performance SSD nel tempo.

10. **Spazio riservato ext4**: ridurre da 5% (default) a 1% su partizioni dati grandi. `tune2fs -m 1 /dev/sdX`.

11. **Log rotation**: configurare logrotate per tutti i servizi. Log non ruotati sono la causa #1 di disk full su server.

12. **Testare fstab prima del reboot**: `findmnt --verify` e `mount -a` dopo ogni modifica a fstab. Un errore in fstab può rendere il sistema non avviabile.

13. **Separare /boot**: partizione dedicata (500MB-1GB), ext4, per compatibilità universale con bootloader.

14. **Documentare i mount**: commentare ogni riga di fstab con il motivo delle opzioni scelte.

---

## Troubleshooting — 25+ Problemi Reali e Soluzioni

### 1. "No space left on device" — Disco pieno

```bash
# Diagnosi
df -h                    # Quale filesystem è pieno?
du -sh /* | sort -rh | head -20   # Directory più grandi nel root
du -sh /var/log/* | sort -rh | head -10  # Spesso è /var/log

# Cause comuni e soluzioni:
# a) Log non ruotati
journalctl --vacuum-size=500M        # Limita journal a 500 MB
truncate -s 0 /var/log/syslog        # Svuota log (brutale ma efficace)
logrotate -f /etc/logrotate.conf     # Forza rotazione

# b) Cache Docker
docker system prune -a               # Rimuove tutto il non usato
docker system df                     # Mostra utilizzo Docker

# c) Pacchetti cache APT
apt clean                            # Svuota cache APT

# d) File cancellati ma ancora aperti
lsof +L1 | grep deleted             # File "deleted" ancora aperti
# Il file non libera spazio finché il processo non lo chiude
# Soluzione: riavviare il servizio (es. systemctl restart nginx)

# e) Snapshot LVM pieni
lvs | grep snap                      # Controllare Data%
lvremove /dev/vg0/snap_old           # Rimuovere snapshot vecchi
```

### 2. "No space left on device" ma df mostra spazio libero — Inode esauriti

```bash
df -i /                  # IUse% = 100% → INODE ESAURITI
# Spazio disco OK ma nessun inode disponibile per creare nuovi file

# Trovare directory con più file
find / -xdev -printf '%h\n' | sort | uniq -c | sort -rn | head -20

# Soluzioni:
# 1. Eliminare file nella directory colpevole
find /var/spool/postfix/maildrop -type f -delete
# 2. Ricreare filesystem con più inode
mkfs.ext4 -N 20000000 /dev/sdX
# 3. Migrare a XFS o Btrfs (inode allocati dinamicamente)
```

### 3. Permessi negati nonostante permessi corretti

```bash
# Checklist diagnostica:
# 1. Permessi della directory padre
namei -l /percorso/completo/file.txt
# Verifica x (execute/traverse) su ogni directory nel percorso

# 2. SELinux/AppArmor
getenforce                           # SELinux: Enforcing/Permissive/Disabled
ls -Z /percorso/file.txt             # Contesto SELinux
restorecon -Rv /percorso/            # Ripristina contesto SELinux

aa-status                            # AppArmor: profili attivi
aa-complain /usr/sbin/nginx          # Metti profilo in complain mode

# 3. Attributi immutabili
lsattr /percorso/file.txt
# Se mostra 'i': chattr -i /percorso/file.txt

# 4. Mount options
mount | grep $(df --output=source /percorso/file.txt | tail -1)
# noexec → non si possono eseguire binari
# ro → filesystem read-only

# 5. ACL
getfacl /percorso/file.txt
# Una ACL potrebbe sovrascrivere i permessi standard

# 6. Capability
getcap /percorso/file.txt
# File capability potrebbe limitare o estendere permessi
```

### 4. Filesystem corrotto dopo crash/power loss

```bash
# REGOLA: boot in recovery mode o single-user PRIMA di fsck

# ext4
e2fsck -f /dev/sda2                  # Force check
e2fsck -f -y /dev/sda2              # Auto-fix
# Se molto corrotto:
e2fsck -f -y -b 32768 /dev/sda2    # Usa superblock di backup

# XFS
xfs_repair /dev/sda2
xfs_repair -L /dev/sda2             # Reset log (ultimo resort)

# Btrfs
btrfs check /dev/sda2               # Diagnosi
btrfs check --repair /dev/sda2      # Riparazione (rischioso)
# Alternativa: montare con recovery
mount -o recovery,ro /dev/sda2 /mnt
```

### 5. Sistema non si avvia — errore in fstab

```bash
# Sintomo: boot si blocca con "A start job is running for..."
# Causa: fstab referenzia un device inesistente senza nofail

# Soluzione:
# 1. Boot in recovery/single-user mode
# 2. Rimontare root rw:
mount -o remount,rw /
# 3. Editare fstab:
#    - Commentare la riga problematica
#    - Oppure aggiungere nofail
# 4. Reboot

# Prevenzione: SEMPRE usare nofail per device non critici
# /dev/sdb1  /data  xfs  defaults,nofail  0  2
```

### 6. LV non si espande — spazio insufficiente nel VG

```bash
vgs                          # Controllare VFree
# Se VFree = 0: servono nuovi PV

pvcreate /dev/sdd1
vgextend vg0 /dev/sdd1      # Aggiunge disco al VG
lvextend -r -L +50G /dev/vg0/lv_data  # Ora c'è spazio
```

### 7. Mount NFS appeso — il server NFS non risponde

```bash
# Sintomo: qualsiasi comando che tocca il mount NFS si blocca
# Causa: server NFS non raggiungibile, mount di default è "hard"

# Soluzione immediata:
umount -f /mnt/nfs           # Force unmount
umount -l /mnt/nfs           # Lazy unmount se -f non funziona

# Prevenzione:
# Server:/share  /mnt/nfs  nfs  defaults,soft,timeo=30,retrans=3,_netdev  0  0
# soft: fallisce invece di bloccare
# timeo=30: timeout 3 secondi
# _netdev: aspetta la rete prima di montare
```

### 8. Disco nuovo non visibile

```bash
# 1. Rescan SCSI bus
echo "- - -" > /sys/class/scsi_host/host0/scan
echo "- - -" > /sys/class/scsi_host/host1/scan

# 2. Verificare
lsblk
fdisk -l

# 3. Se virtuale (KVM/VMware): rescan virtio
echo 1 > /sys/block/vdb/device/rescan

# 4. Partizionare e creare filesystem
gdisk /dev/sdb    # Creare partizione
mkfs.xfs /dev/sdb1
```

### 9. Swap insufficiente — OOM Killer attivato

```bash
# Verificare swap
free -h
swapon --show

# Aggiungere swap file (no partizione necessaria)
dd if=/dev/zero of=/swapfile bs=1M count=4096  # 4 GB
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile

# Persistente in fstab:
# /swapfile  swap  swap  defaults  0  0

# Controllare OOM events
dmesg | grep -i "oom\|killed"
journalctl -k | grep -i "oom\|killed"
```

### 10. File system read-only improvvisamente

```bash
# Causa: errore I/O, filesystem corrotto, disco che sta morendo
# Il kernel rimonta automaticamente in read-only per proteggere i dati

dmesg | tail -50           # Cercare errori I/O
dmesg | grep -i "error\|fault\|fail\|readonly"

# Diagnosi disco
smartctl -a /dev/sda       # SMART status (installare smartmontools)
smartctl -H /dev/sda       # Quick health check

# Se disco OK: remount rw e fsck al prossimo reboot
mount -o remount,rw /
touch /forcefsck           # Forza fsck al boot

# Se disco in errore: BACKUP IMMEDIATO, sostituire disco
```

### 11. Symlink circolari o rotti

```bash
# Trovare symlink rotti
find / -xtype l 2>/dev/null

# Trovare symlink circolari (causano "Too many levels of symbolic links")
find / -follow -maxdepth 0 2>&1 | grep "Too many"

# Correggere: ricreare il symlink correttamente
rm /percorso/symlink_rotto
ln -s /percorso/corretto/target /percorso/symlink_rotto
```

### 12. Device busy — impossibile smontare

```bash
# Chi sta usando il mount point?
fuser -mv /mnt/data        # Processi che usano il mount
lsof +D /mnt/data          # File aperti

# Soluzioni:
# 1. Chiudere i processi
fuser -k /mnt/data         # Kill processi (ATTENZIONE!)
# 2. Lazy unmount
umount -l /mnt/data        # Smonta quando non più in uso
# 3. Verificare la shell corrente
pwd                        # Sei dentro il mount point?
```

### 13. Disco pieno al 100% — impossibile cancellare file (no space for journal)

```bash
# In emergenza, liberare spazio dal reserved space:
tune2fs -m 0 /dev/sda2   # Temporaneamente rimuovi spazio riservato
# Ora puoi cancellare file
rm -f /var/log/giant.log
# Ripristinare spazio riservato
tune2fs -m 1 /dev/sda2
```

### 14. Inode con timestamp futuro — problemi con make/build

```bash
# Diagnosi
find / -newer /tmp/now -type f 2>/dev/null | head
# Causa: orologio di sistema errato durante la creazione

# Soluzione: sincronizzare NTP e toccare i file
timedatectl set-ntp true
find /problematic/dir -type f -exec touch {} +
```

### 15. Quota superata — utente non può creare file

```bash
repquota -u /home          # Verificare stato quote
edquota -u mario           # Aumentare limiti se necessario
quota -u mario             # Mostrare all'utente la sua situazione
```

### 16. File troppo grande per il filesystem

```bash
# ext4 con 1K block size: max file 16 GiB
# ext4 con 4K block size: max file 16 TiB
# FAT32: max file 4 GiB

# Diagnosi
tune2fs -l /dev/sdb1 | grep "Block size"
df -hT /mnt/usb     # Tipo filesystem

# Soluzione per USB: riformattare come exFAT
mkfs.exfat /dev/sdb1
```

### 17. Permission denied su script con permessi corretti

```bash
# Possibili cause:
# 1. Mount con noexec
mount | grep $(df --output=source . | tail -1)

# 2. Shebang errato o mancante
head -1 script.sh    # Deve iniziare con #!/bin/bash

# 3. File creato su Windows con CR/LF
file script.sh       # Se dice "CRLF line terminators"
dos2unix script.sh   # Converte

# 4. Filesystem FAT/NTFS (non supporta permessi Unix)
# Montare con opzioni fmask/dmask:
# mount -t vfat -o fmask=0022,dmask=0022 /dev/sdb1 /mnt
```

### 18. Performance I/O degradata

```bash
# Diagnosi
iostat -xz 1 5           # Statistiche I/O per device
iotop -o                  # Processi con più I/O
vmstat 1 5                # wa (iowait) alto?

# Se iowait alto:
# 1. Identificare processo colpevole: iotop
# 2. Controllare scheduler I/O
cat /sys/block/sda/queue/scheduler
# 3. Controllare se SSD è in modalità HDD
cat /sys/block/sda/queue/rotational
# 4. Controllare TRIM
fstrim -v /
# 5. Controllare frammentazione (ext4)
e4defrag -c /dev/sda2
```

### 19. /boot pieno — impossibile aggiornare il kernel

```bash
# Verificare
df -h /boot

# Rimuovere kernel vecchi (Debian/Ubuntu)
apt autoremove --purge

# Manualmente: identificare kernel corrente e rimuovere gli altri
uname -r    # Kernel in uso — NON rimuovere!
dpkg -l 'linux-image-*' | grep ^ii
apt remove linux-image-5.15.0-old
```

### 20. LVM snapshot pieno — Volume corrotto

```bash
lvs | grep snap
# Se Data% = 100% → lo snapshot è invalido

lvremove /dev/vg0/snap_broken
# Creare nuovo snapshot con più spazio
lvcreate -L 20G -s -n snap_new /dev/vg0/lv_data
```

### 21. UUID duplicato dopo clone disco

```bash
# Dopo clonazione, due dischi hanno lo stesso UUID
blkid | grep -i uuid

# Generare nuovo UUID
# ext4:
tune2fs -U random /dev/sdb1
# XFS:
xfs_admin -U generate /dev/sdb1
# Aggiornare fstab con il nuovo UUID!
```

### 22. File con caratteri speciali nel nome — impossibile cancellare

```bash
# Metodo 1: escape del carattere
rm -- "--file-con-trattino"
rm ./-file-con-trattino

# Metodo 2: per inode
ls -i                    # Trovare inode number
find . -inum 12345 -delete

# Metodo 3: glob
rm ./file*problematico*
```

### 23. Disco esterno non riconosciuto

```bash
# 1. Verificare se il kernel lo vede
dmesg | tail -20        # Dopo aver collegato il disco

# 2. Verificare dispositivo
lsblk
lsusb                   # Per dischi USB

# 3. Se il filesystem non è supportato
apt install exfat-fuse ntfs-3g

# 4. Mount manuale
mount /dev/sdb1 /mnt/usb
mount -t ntfs-3g /dev/sdb1 /mnt/usb    # NTFS
```

### 24. Btrfs balance / scrub bloccato

```bash
# Controllare stato
btrfs balance status /mnt
btrfs scrub status /mnt

# Cancellare operazione bloccata
btrfs balance cancel /mnt
btrfs scrub cancel /mnt

# Riprovare con filtri meno aggressivi
btrfs balance start -dusage=50 -musage=50 /mnt
```

### 25. ZFS pool degradato

```bash
zpool status
# Se un disco mostra DEGRADED o FAULTED:

# Sostituire disco fisico, poi:
zpool replace tank /dev/old_disk /dev/new_disk
# ZFS inizia il resilver automaticamente

# Monitorare resilver
zpool status tank
# scan: resilver in progress ...

# Scrub dopo resilver
zpool scrub tank
```

---

## Errori Comuni e Anti-Pattern

### 1. chmod 777 "per risolvere i permessi"
**Problema:** Dà accesso completo a chiunque. Vulnerabilità di sicurezza critica. Qualsiasi utente del sistema può leggere, modificare ed eseguire il file — inclusi eventuali attaccanti che ottengono accesso con un utente non privilegiato. In ambienti web, un `chmod 777` su una directory di upload significa che un file PHP caricato può essere eseguito dal web server.
**Soluzione corretta:** Diagnosticare il problema reale con `namei -l /percorso/completo` (mostra i permessi di ogni directory nel path), `getfacl` (verifica ACL), `getenforce` (verifica se SELinux blocca l'accesso). Impostare i permessi minimi necessari: tipicamente `644` per file, `755` per directory, `600` per file sensibili.

### 2. Non usare UUID in fstab
**Problema:** I nomi dei device (`/dev/sda`, `/dev/sdb`) sono assegnati dal kernel in base all'ordine di rilevamento, che può cambiare dopo l'aggiunta di un disco, un cambio di cavo SATA, o un aggiornamento del firmware del controller. Il sistema monta la partizione sbagliata o non si avvia.
**Soluzione:** Usare sempre `UUID=` in fstab. Ottenere gli UUID con `blkid`. Per device con etichetta, `LABEL=` è un'alternativa leggibile. Per device multipath o SAN, usare i percorsi `/dev/disk/by-id/` che sono stabili e basati sull'hardware.
```bash
# Trovare UUID di tutti i device
blkid
# Trovare UUID di un device specifico
blkid /dev/sda1
# Percorsi stabili alternativi
ls -la /dev/disk/by-uuid/
ls -la /dev/disk/by-id/
ls -la /dev/disk/by-label/
```

### 3. Un'unica partizione per tutto
**Problema:** Con una singola partizione, un processo che genera log incontrollati o un utente che riempie la home può saturare il disco. Quando la partizione root è piena, il sistema diventa inutilizzabile: SSH non accetta connessioni, i servizi crashano, il database si corrompe, impossibile fare login anche da console perché il sistema non riesce a scrivere file temporanei di sessione.
**Soluzione:** Separare `/var` (log e dati variabili), `/home` (dati utente), `/tmp` (file temporanei) su partizioni o LV dedicati. Con LVM, la separazione è flessibile: si può ridimensionare online. Schema minimo consigliato per server: `/` (20-50 GB), `/var` (dimensionato per il volume di log), `/home` (dimensionato per gli utenti), `/tmp` (1-5 GB o tmpfs), swap (1-2x RAM fino a 16 GB, poi 16 GB fissi).

### 4. Non monitorare gli inode
**Problema:** "No space left on device" con disco quasi vuoto. Questo errore confonde perché `df -h` mostra spazio libero, ma il filesystem ha esaurito gli inode. Ogni file e directory consuma un inode. Milioni di file piccoli (sessioni PHP, cache, mail queue) esauriscono gli inode prima dello spazio disco. Su ext4, il numero di inode è fisso alla creazione del filesystem.
**Soluzione:** Monitorare `df -i` oltre a `df -h`. Alert su IUse% > 80%. Per identificare la directory colpevole: `find /var -xdev -printf '%h\n' | sort | uniq -c | sort -rn | head -10`. Per prevenire: su ext4, al momento della formattazione, specificare `mkfs.ext4 -i 8192` (un inode ogni 8 KB) se si prevedono molti file piccoli. Su XFS e Btrfs, gli inode sono allocati dinamicamente e il problema non si verifica.

### 5. fsck su filesystem montato
**Problema:** Corruzione del filesystem garantita. `fsck` legge e modifica strutture interne del filesystem (superblock, bitmap, inode table). Se il filesystem è montato, il kernel e fsck competono per le stesse strutture, causando corruzione irreparabile. Il risultato può essere la perdita totale dei dati sulla partizione.
**Regola:** MAI fsck su filesystem montato. Smontare prima con `umount`, o fare da recovery mode (boot da live USB). L'unica eccezione è `fsck -n` (dry run, solo lettura) che può essere usato su filesystem montati per una verifica non distruttiva. Per i filesystem moderni con journaling (ext4, XFS), il recovery automatico dopo un crash è gestito dal journal al mount — fsck manuale è raramente necessario.

### 6. Dimenticare nofail per device non critici
**Problema:** Il server entra in emergency mode durante il boot perché un disco USB, un mount NFS, o un volume iSCSI elencato in fstab non è disponibile. In produzione, il server resta inaccessibile finché qualcuno non interviene fisicamente o da console remota — un downtime completamente evitabile.
**Soluzione:** Aggiungere `nofail` nelle opzioni di fstab per tutto ciò che non è il root filesystem. Per mount NFS, aggiungere anche `_netdev` (aspetta la rete) e `bg` (mount in background). Per iSCSI, `_netdev,nofail`. Per dispositivi rimovibili, `nofail,x-systemd.device-timeout=5` per evitare attese lunghe.
```
# /etc/fstab — opzioni robuste
UUID=abc123  /mnt/dati   ext4  defaults,nofail  0 2
nfs.srv:/share /mnt/nfs  nfs4  defaults,nofail,_netdev,bg,soft,timeo=30  0 0
```

### 7. Spazio riservato ext4 al 5% su partizioni grandi
**Problema:** ext4 riserva il 5% dello spazio al superuser per prevenire la frammentazione e garantire che i processi di sistema possano scrivere anche quando il disco è "pieno" per gli utenti normali. Su disco da 4 TB, il 5% = 200 GB di spazio inaccessibile — un enorme spreco su partizioni dati dove i processi di sistema non scrivono.
**Soluzione:** `tune2fs -m 1 /dev/sdX` per partizioni dati (1% è sufficiente). `tune2fs -m 0 /dev/sdX` per partizioni usate solo come storage (NAS, backup). Lasciare il 5% solo per la partizione root `/` dove il sistema operativo deve poter scrivere anche in condizioni critiche.

### 8. Non configurare logrotate
**Problema:** `/var/log` cresce indefinitamente fino a riempire il disco. Un singolo servizio con debug logging abilitato per errore può generare GB di log in poche ore. Senza rotazione, i file di log diventano anche impossibili da analizzare (aprire un file da 50 GB con `less` è impraticabile).
**Soluzione:** Verificare che ogni servizio abbia una configurazione logrotate in `/etc/logrotate.d/`. Configurazione minima per un servizio custom:
```
/var/log/myapp/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 640 root adm
    postrotate
        systemctl reload myapp > /dev/null 2>&1 || true
    endscript
}
```
Per servizi che loggano via syslog/journald, configurare la retention di journald: `SystemMaxUse=500M` in `/etc/systemd/journald.conf`.

### 9. Hard link tra filesystem diversi
**Problema:** `ln file.txt /other_mount/link.txt` fallisce con "Invalid cross-device link".
**Motivo:** Gli hard link funzionano solo nello stesso filesystem perché condividono lo stesso inode, e gli inode sono locali al filesystem. Due filesystem diversi hanno spazi inode indipendenti — un inode numero 12345 su `/dev/sda1` e un inode 12345 su `/dev/sdb1` sono entità completamente diverse.
**Soluzione:** Usare symlink (`ln -s`) per link cross-filesystem. I symlink sono file speciali che contengono il percorso del target e funzionano attraverso filesystem diversi. Lo svantaggio è che diventano "dangling" se il target viene rimosso o rinominato. Alternative: bind mount (`mount --bind /sorgente /destinazione`) per rendere disponibile una directory in un altro punto del filesystem tree.

### 10. Ignorare SMART warnings
**Problema:** Il disco mostra errori SMART (Self-Monitoring Analysis and Reporting Technology) ma viene ignorato perché "funziona ancora". I dischi non muoiono all'improvviso — danno segnali premonitori: settori riallocati in crescita, errori di lettura, temperature anomale. Ignorare questi segnali porta alla perdita di dati.
**Soluzione:** Installare `smartmontools`, abilitare il daemon `smartd` per il monitoraggio continuo. Controllare regolarmente con `smartctl -a /dev/sda`. I parametri critici da monitorare: `Reallocated_Sector_Ct` (settori danneggiati rimappati — se cresce, il disco sta morendo), `Current_Pending_Sector` (settori in attesa di rimappatura), `Offline_Uncorrectable` (errori non correggibili). Sostituire il disco al primo segnale di errore — non aspettare il fallimento completo.

### 11. Thin provisioning senza monitoraggio
**Problema:** I thin LV allocano spazio solo quando i dati vengono effettivamente scritti, permettendo di creare volumi logici la cui dimensione totale supera lo spazio fisico disponibile (overcommit). Se i dati scritti superano lo spazio fisico del thin pool, tutti i thin LV che dipendono da quel pool si bloccano con errori di I/O. Il recovery richiede l'estensione del pool o la rimozione di dati — operazione critica sotto pressione.
**Soluzione:** Impostare alert quando il thin pool supera il 70% di utilizzo. Configurare l'auto-estensione in `/etc/lvm/lvm.conf`:
```
thin_pool_autoextend_threshold = 70
thin_pool_autoextend_percent = 20
```
Monitorare con `lvs -o +data_percent,metadata_percent`. Non superare mai un overcommit ratio di 3:1 (3x volumi logici rispetto allo spazio fisico) senza un piano di crescita documentato.

### 12. Snapshot LVM senza politica di pulizia
**Problema:** Gli snapshot LVM (tipo CoW classico, non thin) consumano spazio nel VG per ogni blocco modificato dopo la creazione dello snapshot. Più dati cambiano, più lo snapshot cresce. Se lo snapshot raggiunge la dimensione massima allocata, diventa invalido e viene automaticamente rimosso dal kernel — perdendo la possibilità di rollback. Inoltre, gli snapshot CoW degradano le performance di scrittura del 30-50% perché ogni scrittura richiede prima la copia del blocco originale nello snapshot.
**Soluzione:** Definire una politica chiara: (1) gli snapshot sono temporanei, non backup — usarli per operazioni rischiose (upgrade, migrazione) e rimuoverli entro ore, non giorni. (2) Automatizzare creazione/eliminazione con script:
```bash
# Creare snapshot prima di operazione rischiosa
lvcreate -s -n snap_root -L 5G /dev/vg0/root
# Operazione rischiosa...
# Se OK: rimuovere lo snapshot
lvremove -f /dev/vg0/snap_root
# Se KO: rollback
lvconvert --merge /dev/vg0/snap_root
```
(3) Monitorare `Data%` con `lvs -o lv_name,data_percent`. Alert se > 50%. (4) Per snapshot frequenti (es. testing), preferire thin snapshot che sono più efficienti.

---

## Esercizi Pratici

### Esercizio 1 — Analisi filesystem e inode

```bash
# 1. Verificare lo spazio disco e l'utilizzo inode su tutti i filesystem
df -hT
df -ih

# 2. Trovare le 10 directory più grandi in /var
du -sh /var/*/ | sort -rh | head -10

# 3. Trovare le directory con più file (consumo inode)
find /var -xdev -printf '%h\n' | sort | uniq -c | sort -rn | head -10

# 4. Creare un file e verificare il suo inode
touch /tmp/test_inode
stat /tmp/test_inode
ls -i /tmp/test_inode
```

### Esercizio 2 — Hard link e symlink

```bash
# 1. Creare un file con contenuto
echo "contenuto originale" > /tmp/originale.txt

# 2. Creare hard link
ln /tmp/originale.txt /tmp/hardlink.txt

# 3. Creare symlink
ln -s /tmp/originale.txt /tmp/symlink.txt

# 4. Verificare inode
ls -li /tmp/originale.txt /tmp/hardlink.txt /tmp/symlink.txt

# 5. Cancellare l'originale. Cosa succede?
rm /tmp/originale.txt
cat /tmp/hardlink.txt     # Funziona (stesso inode)
cat /tmp/symlink.txt      # Errore: dangling symlink

# 6. Pulizia
rm /tmp/hardlink.txt /tmp/symlink.txt
```

### Esercizio 3 — Permessi e ACL

```bash
# 1. Creare struttura directory condivisa
sudo mkdir -p /progetto/shared
sudo groupadd developers
sudo usermod -aG developers $USER

# 2. Impostare SGID per ereditarietà group
sudo chown :developers /progetto/shared
sudo chmod 2775 /progetto/shared

# 3. Impostare ACL per un utente specifico
sudo setfacl -m u:nobody:r /progetto/shared
sudo setfacl -d -m g:developers:rwx /progetto/shared

# 4. Verificare
getfacl /progetto/shared
ls -ld /progetto/shared    # Notare il +

# 5. Pulizia
sudo rm -rf /progetto
sudo groupdel developers
```

### Esercizio 4 — LVM (ambiente di test)

```bash
# ATTENZIONE: usare un disco di test, NON il disco di sistema!

# 1. Creare file come "disco virtuale" per simulare
dd if=/dev/zero of=/tmp/disk1.img bs=1M count=500
dd if=/dev/zero of=/tmp/disk2.img bs=1M count=500

# 2. Associare a loop device
sudo losetup /dev/loop10 /tmp/disk1.img
sudo losetup /dev/loop11 /tmp/disk2.img

# 3. Creare PV, VG, LV
sudo pvcreate /dev/loop10 /dev/loop11
sudo vgcreate vg_test /dev/loop10 /dev/loop11
sudo lvcreate -L 400M -n lv_test vg_test

# 4. Creare filesystem e montare
sudo mkfs.ext4 /dev/vg_test/lv_test
sudo mkdir /mnt/test_lvm
sudo mount /dev/vg_test/lv_test /mnt/test_lvm
df -h /mnt/test_lvm

# 5. Espandere
sudo lvextend -r -L +200M /dev/vg_test/lv_test
df -h /mnt/test_lvm

# 6. Pulizia
sudo umount /mnt/test_lvm
sudo lvremove -f /dev/vg_test/lv_test
sudo vgremove vg_test
sudo pvremove /dev/loop10 /dev/loop11
sudo losetup -d /dev/loop10 /dev/loop11
rm -f /tmp/disk1.img /tmp/disk2.img
sudo rmdir /mnt/test_lvm
```

### Esercizio 5 — Troubleshooting simulato

```bash
# Scenario 1: Trovare file cancellati ma ancora aperti
# Terminale 1:
tail -f /var/log/syslog &     # Processo che tiene aperto il file
# Terminale 2:
sudo lsof +L1 | grep deleted  # Trovare il file

# Scenario 2: Testare mount options
mkdir /tmp/test_mount
mount -t tmpfs -o size=10M,noexec tmpfs /tmp/test_mount
echo '#!/bin/bash' > /tmp/test_mount/test.sh
echo 'echo "hello"' >> /tmp/test_mount/test.sh
chmod +x /tmp/test_mount/test.sh
/tmp/test_mount/test.sh    # Deve fallire con "Permission denied" (noexec)
umount /tmp/test_mount
rmdir /tmp/test_mount

# Scenario 3: Simulare inode exhaustion
mkdir /tmp/inode_test
mount -t tmpfs -o size=1M,nr_inodes=100 tmpfs /tmp/inode_test
for i in $(seq 1 100); do touch /tmp/inode_test/file$i; done
touch /tmp/inode_test/extra    # Dovrebbe fallire: no inode left
df -i /tmp/inode_test
umount /tmp/inode_test
rmdir /tmp/inode_test
```

### Esercizio 6 — Quote disco

```bash
# Simulare con tmpfs e quote (richiede sistema con quota installato)
# 1. Verificare che il pacchetto quota sia installato
which edquota || sudo apt install quota

# 2. Creare un filesystem di test con quote
# (Usare un loop device o partizione di test)
# Aggiungere usrquota,grpquota alle opzioni mount
# Eseguire quotacheck, quotaon
# Configurare limiti con edquota o setquota
# Verificare con repquota
```

### Esercizio 7 — Monitoring completo dello storage

```bash
# Creare uno script di monitoring che verifica tutti gli aspetti dello storage

#!/bin/bash
# storage-health-check.sh — verifica completa dello stato dello storage

echo "=== SPAZIO DISCO ==="
df -hT | grep -v tmpfs | grep -v devtmpfs

echo ""
echo "=== UTILIZZO INODE ==="
df -iT | grep -v tmpfs | grep -v devtmpfs | awk '$6+0 > 70 {print "WARN:", $0}'

echo ""
echo "=== TOP 10 DIRECTORY PER DIMENSIONE ==="
du -sh /var/*/ 2>/dev/null | sort -rh | head -10

echo ""
echo "=== LVM STATUS ==="
if command -v lvs &>/dev/null; then
    echo "-- Volume Groups --"
    vgs --noheadings -o vg_name,vg_size,vg_free 2>/dev/null
    echo "-- Logical Volumes --"
    lvs --noheadings -o lv_name,lv_size,data_percent,origin 2>/dev/null
fi

echo ""
echo "=== SMART HEALTH ==="
for disk in /dev/sd?; do
    [ -b "$disk" ] || continue
    health=$(smartctl -H "$disk" 2>/dev/null | grep "overall-health" | awk '{print $NF}')
    reallocated=$(smartctl -A "$disk" 2>/dev/null | grep "Reallocated_Sector" | awk '{print $NF}')
    echo "$disk: health=$health reallocated_sectors=$reallocated"
done

echo ""
echo "=== MOUNT OPTIONS ==="
# Verificare mount options critiche
mount | grep -E "ext4|xfs|btrfs" | while read -r line; do
    mp=$(echo "$line" | awk '{print $3}')
    opts=$(echo "$line" | grep -oP '\(.*\)')
    echo "$mp $opts"
done

echo ""
echo "=== FILE APERTI MA CANCELLATI ==="
lsof +L1 2>/dev/null | grep deleted | head -10

# Exit code basato su problemi trovati
problems=0
# Controllare spazio disco > 85%
df -h | awk 'NR>1 && $5+0 > 85 {print "CRITICAL: " $6 " al " $5; exit 1}' && ((problems++))
# Controllare inode > 80%
df -i | awk 'NR>1 && $5+0 > 80 {print "CRITICAL: inode " $6 " al " $5; exit 1}' && ((problems++))

exit $problems
```

Integrare questo script con un sistema di monitoraggio (Prometheus node_exporter, Zabbix, o un cron job che invia email/Slack) per rilevare problemi prima che diventino critici. Il monitoraggio proattivo dello storage previene la maggior parte degli incidenti legati al filesystem — un disco pieno è un problema completamente evitabile con alerting appropriato.

---

## FAQ — 25 Domande e Risposte

**Q1: Qual è la differenza tra `/bin` e `/usr/bin`?**
Storicamente, `/bin` conteneva i binari essenziali per il boot e recovery, mentre `/usr/bin` conteneva i programmi utente. Nelle distribuzioni moderne con **usr-merge**, `/bin` è un symlink a `/usr/bin` — la distinzione è solo storica.

**Q2: Perché `/tmp` è montato come tmpfs?**
tmpfs usa la RAM, rendendolo velocissimo per file temporanei. Viene automaticamente pulito al reboot. Riduce l'usura degli SSD. Lo svantaggio è che consuma RAM (ma solo per i dati effettivamente presenti).

**Q3: Posso ridurre (shrink) un filesystem XFS?**
No. XFS supporta solo l'espansione (grow), mai la riduzione. Per ridurre: backup dati → ricreare filesystem più piccolo → restore. Alternativa: migrare a ext4 se serve shrink.

**Q4: Qual è la differenza tra `df` e `du`?**
`df` mostra lo spazio usato/libero per filesystem (dal superblock). `du` calcola lo spazio effettivo dei file in una directory. Possono differire per via di file cancellati ma ancora aperti (visibili in `df` ma non in `du`), sparse file, e blocchi riservati.

**Q5: Come trovo quale processo sta usando un file/mount point?**
`fuser -mv /mount/point` mostra i processi. `lsof +D /mount/point` mostra i file aperti. `lsof +L1` mostra file cancellati ma ancora aperti.

**Q6: Qual è la differenza tra `atime`, `mtime` e `ctime`?**
`atime` = ultimo accesso in lettura. `mtime` = ultima modifica del contenuto. `ctime` = ultima modifica dei metadati (permessi, owner, inode). Non è "creation time" — per quello serve `crtime`/`btime` (supportato da ext4 e stat con `--format=%W`).

**Q7: Devo usare `noatime` o `relatime`?**
`relatime` è il default moderno e un buon compromesso: aggiorna atime solo se è più vecchio di mtime. `noatime` offre un piccolo vantaggio di performance ma rompe applicazioni che dipendono da atime (es. mutt per mail non letta). Consiglio: `relatime` per default, `noatime` per partizioni database/storage dove nessuno usa atime.

**Q8: Come funziona il Copy-on-Write (CoW) di Btrfs/ZFS?**
Quando un blocco viene modificato, il filesystem scrive una nuova copia del blocco in una posizione libera e aggiorna i metadati. Il blocco originale resta intatto fino a quando non è più referenziato (da nessuno snapshot). Vantaggi: snapshot istantanei, integrità dati. Svantaggio: frammentazione con file grandi e modifiche frequenti.

**Q9: Come posso sapere se il mio disco è SSD o HDD?**
`cat /sys/block/sda/queue/rotational` → 0 = SSD, 1 = HDD. Anche `lsblk -d -o NAME,ROTA`.

**Q10: Cos'è un "dangling symlink" e come lo trovo?**
Un symlink il cui target non esiste più. `find / -xtype l 2>/dev/null` trova tutti i symlink rotti.

**Q11: Perché `/dev/urandom` è preferito a `/dev/random`?**
`/dev/random` storicamente si bloccava quando l'entropia era insufficiente. `/dev/urandom` non si blocca mai ed è crittograficamente sicuro per tutti gli usi pratici. Nelle versioni recenti del kernel (5.6+), anche `/dev/random` non si blocca più dopo l'inizializzazione del CSPRNG.

**Q12: Come gestisco filesystem su dischi cifrati (LUKS)?**
```bash
# Creare volume cifrato
cryptsetup luksFormat /dev/sdb1
# Aprire
cryptsetup open /dev/sdb1 encrypted_vol
# Creare filesystem
mkfs.ext4 /dev/mapper/encrypted_vol
# Montare
mount /dev/mapper/encrypted_vol /mnt/secret
# In fstab + /etc/crypttab per automazione al boot
```

**Q13: Qual è la dimensione massima consigliata per la partizione `/boot`?**
500 MB - 1 GB. Deve contenere kernel, initramfs e configurazione bootloader. Con DKMS e kernel multipli, 1 GB è più sicuro.

**Q14: Come faccio a montare un file ISO?**
```bash
mount -o loop,ro image.iso /mnt/iso
```

**Q15: Cos'è un "sparse file" e come lo creo?**
Un file che contiene "buchi" (blocchi di zeri non allocati su disco). Occupa meno spazio di quanto appare con `ls -l`. `du` mostra lo spazio reale; `ls -l` mostra la dimensione apparente.
```bash
# Creare sparse file da 1 GB che occupa 0 byte su disco
truncate -s 1G sparse.img
ls -lh sparse.img    # 1.0G
du -h sparse.img     # 0
```

**Q16: Come verifico l'integrità di un filesystem senza smontare?**
Per Btrfs: `btrfs scrub start /mnt`. Per ZFS: `zpool scrub tank`. Per ext4/XFS: non è possibile un check completo online — pianificare fsck durante la manutenzione con filesystem smontato.

**Q17: Qual è la differenza tra bind mount e symlink?**
Un bind mount è un mount reale — il kernel vede lo stesso filesystem in due punti. Un symlink è un file speciale che contiene un percorso. Il bind mount funziona anche dove i symlink falliscono (es. dentro chroot, container, con applicazioni che non seguono i symlink).

**Q18: Come trovo file modificati negli ultimi 24 ore?**
```bash
find / -mtime -1 -type f 2>/dev/null
# O con data specifica:
find / -newermt "2026-05-21" -type f 2>/dev/null
```

**Q19: Come posso recuperare un file cancellato?**
Su ext4: `extundelete /dev/sda2 --restore-file /percorso/file` (meglio da live USB, filesystem smontato). Su XFS/Btrfs: molto più difficile. La prevenzione (backup) è migliore del recovery.

**Q20: Cos'è la differenza tra partizione e volume logico LVM?**
Una partizione è una divisione fisica del disco, rigida e difficile da ridimensionare. Un LV (Logical Volume) è una divisione logica di un pool di storage (VG), ridimensionabile online, può spanare più dischi, supporta snapshot.

**Q21: Come funziona RAID-Z di ZFS vs RAID tradizionale?**
RAID-Z scrive stripe completi (non parziali come RAID5), eliminando il "RAID5 write hole". RAID-Z1 = tolleranza 1 disco, RAID-Z2 = 2 dischi, RAID-Z3 = 3 dischi. I checksum end-to-end permettono self-healing durante gli scrub.

**Q22: Devo abilitare journal su tutte le partizioni?**
Il journal protegge l'integrità dei metadati (e opzionalmente dei dati) in caso di crash. Disabilitarlo risparmia un po' di I/O ma rende il recovery dopo crash molto più lento e incerto. Consiglio: lasciare il journal attivo sempre, tranne su filesystem effimeri (build, test).

**Q23: Come funziona il TRIM per SSD e devo preoccuparmene?**
Il TRIM informa l'SSD dei blocchi non più in uso, permettendogli di ottimizzare la garbage collection interna. Senza TRIM, le performance dell'SSD degradano nel tempo. Abilitare `fstrim.timer` (trim settimanale) è il metodo raccomandato.

**Q24: Posso convertire un filesystem ext4 in XFS senza perdere dati?**
No. Non esiste conversione in-place tra filesystem diversi. Procedura: backup → formato → mkfs → restore. Per la migrazione, `rsync -avHAX` preserva permessi, ACL, xattr e hardlink.

**Q25: Come monitoro la salute dei dischi in produzione?**
```bash
# SMART monitoring
apt install smartmontools
smartctl -a /dev/sda         # Report completo
smartctl -H /dev/sda         # Health check rapido
# In /etc/smartd.conf: monitoraggio continuo con alert via mail

# I/O monitoring
iostat -xz 5                 # Ogni 5 secondi
iotop -o                     # Top I/O per processo

# Filesystem monitoring
df -hT                       # Spazio
df -i                        # Inode
# Integrare con Prometheus node_exporter per alerting automatico
```
