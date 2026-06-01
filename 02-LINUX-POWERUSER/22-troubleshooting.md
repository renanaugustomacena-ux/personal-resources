# Troubleshooting Linux — Guida Completa

> **Modulo 22** · **Aggiornamento:** 2026-05-22

## Idee guida
1. **ASCII decision tree > prosa.** Step-by-step diagnostic clear.
2. **chroot+GRUB `/boot` bind-mount caveat: rescue scenari.**
3. **`dmesg`, `journalctl -p err`, `systemctl --failed` first stop.**
4. **strace/ltrace per syscall trace; bpftrace modern.**


## Indice

- [Panoramica](#panoramica)
- [Metodologia di Troubleshooting](#metodologia-di-troubleshooting)
  - [Framework in 6 Passi](#framework-in-6-passi)
  - [Albero Decisionale: Osservare→Ipotizzare→Testare→Risolvere→Documentare](#albero-decisionale)
  - [Livelli di Severità e Priorità](#livelli-di-severità-e-priorità)
  - [Comandi di Primo Soccorso](#comandi-di-primo-soccorso)
  - [Strumenti Diagnostici Fondamentali](#strumenti-diagnostici-fondamentali)
- [Troubleshooting Boot e GRUB](#troubleshooting-boot-e-grub)
  - [Il Sistema Non Si Avvia](#il-sistema-non-si-avvia)
  - [GRUB Rescue Shell](#grub-rescue-shell)
  - [Initramfs Shell](#initramfs-shell)
  - [Emergency e Rescue Mode (systemd)](#emergency-e-rescue-mode-systemd)
  - [Ricostruzione dracut/initramfs](#ricostruzione-drautinitramfs)
  - [Errori fstab che Bloccano il Boot](#errori-fstab-che-bloccano-il-boot)
  - [Problemi Comuni di Boot](#problemi-comuni-di-boot)
- [Kernel Panic](#kernel-panic)
  - [Leggere i Messaggi di Panic](#leggere-i-messaggi-di-panic)
  - [Configurazione kdump](#configurazione-kdump)
  - [Analisi Crash con crash utility](#analisi-crash-con-crash-utility)
  - [Kernel Panic Comuni e Soluzioni](#kernel-panic-comuni-e-soluzioni)
- [Troubleshooting Disco e Filesystem](#troubleshooting-disco-e-filesystem)
  - [Remount Read-Only e Recovery](#remount-read-only-e-recovery)
  - [Procedure fsck Dettagliate](#procedure-fsck-dettagliate)
  - [Superblock Corrotto](#superblock-corrotto)
  - [Journal Recovery](#journal-recovery)
  - [Problemi Spazio Disco](#problemi-spazio-disco)
  - [Pulizia Spazio: Journal, Cache, Kernel, /tmp, /var/log](#pulizia-spazio)
- [Troubleshooting Rete](#troubleshooting-rete)
  - [Diagnosi Sistematica Layer per Layer](#diagnosi-sistematica-layer-per-layer)
  - [tcpdump — Cattura e Analisi Pacchetti](#tcpdump)
  - [ss — Stato Socket Avanzato](#ss-stato-socket-avanzato)
  - [ip e route — Diagnostica Routing](#ip-e-route)
  - [Problemi Comuni di Rete](#problemi-comuni-di-rete)
- [Troubleshooting DNS](#troubleshooting-dns)
  - [/etc/resolv.conf e Configurazione](#etcresolvconf-e-configurazione)
  - [systemd-resolved](#systemd-resolved)
  - [nsswitch.conf](#nsswitchconf)
  - [Debug con dig/nslookup/host](#debug-con-dignslookuphost)
  - [Problemi DNS Comuni](#problemi-dns-comuni)
- [Troubleshooting Servizi (systemd)](#troubleshooting-servizi-systemd)
  - [Analisi Journal Avanzata](#analisi-journal-avanzata)
  - [Problemi di Dipendenza tra Unit](#problemi-di-dipendenza-tra-unit)
  - [Socket Activation Problems](#socket-activation-problems)
  - [Servizi in Crash Loop](#servizi-in-crash-loop)
  - [Timer e Scheduled Units](#timer-e-scheduled-units)
- [Troubleshooting Permessi](#troubleshooting-permessi)
  - [ACL Debugging](#acl-debugging)
  - [SELinux Denials](#selinux-denials)
  - [AppArmor Denials](#apparmor-denials)
  - [Linux Capabilities](#linux-capabilities)
  - [Problemi Permessi Comuni](#problemi-permessi-comuni)
- [Troubleshooting Memoria](#troubleshooting-memoria)
  - [OOM Killer — Analisi e Tuning](#oom-killer)
  - [Memory Leak Detection](#memory-leak-detection)
  - [Swap Storm](#swap-storm)
  - [Hugepage Misconfiguration](#hugepage-misconfiguration)
- [Troubleshooting CPU](#troubleshooting-cpu)
  - [Load Average Alto](#load-average-alto)
  - [Processi in D-State](#processi-in-d-state)
  - [CPU Throttling](#cpu-throttling)
  - [Interrupt Storm](#interrupt-storm)
- [Troubleshooting Performance Avanzato](#troubleshooting-performance-avanzato)
  - [Profiling Sistematico](#profiling-sistematico)
  - [perf — Linux Profiler](#perf)
  - [eBPF/bpftrace](#ebpfbpftrace)
  - [I/O Saturation](#io-saturation)
  - [Diagnosi Rapida 60 Secondi](#diagnosi-rapida-60-secondi)
- [Troubleshooting Package Management](#troubleshooting-package-management)
  - [Dipendenze Rotte (APT)](#dipendenze-rotte-apt)
  - [Dipendenze Rotte (DNF/YUM)](#dipendenze-rotte-dnfyum)
  - [Pacchetti Held/Bloccati](#pacchetti-heldbloccati)
  - [Repository Problems](#repository-problems)
  - [dpkg/rpm Corrotto](#dpkgrpm-corrotto)
- [Troubleshooting SSH](#troubleshooting-ssh)
  - [Connection Refused](#connection-refused)
  - [Key Rejected](#key-rejected)
  - [Timeout](#timeout)
  - [SSH Agent Problems](#ssh-agent-problems)
  - [SSH Tunneling e Port Forwarding Issues](#ssh-tunneling)
- [Troubleshooting Container (Docker/Podman)](#troubleshooting-container)
  - [Networking Issues](#container-networking)
  - [Storage e Volume Issues](#container-storage)
  - [Container OOM](#container-oom)
  - [Image Problems](#container-image-problems)
  - [Docker Daemon Issues](#docker-daemon-issues)
- [Troubleshooting Hardware](#troubleshooting-hardware)
  - [SMART Monitoring Dischi](#smart-monitoring)
  - [Errori Memoria (mcelog/EDAC)](#errori-memoria)
  - [Monitoraggio Temperatura](#monitoraggio-temperatura)
  - [PCIe e Dispositivi USB](#pcie-e-usb)
- [Analisi Log — Pattern e Tecniche](#analisi-log)
  - [Firme di Errore Comuni](#firme-di-errore-comuni)
  - [Parsing Syslog Avanzato](#parsing-syslog-avanzato)
  - [Correlazione Temporale tra Log](#correlazione-temporale)
  - [Log Centralizzato](#log-centralizzato)
- [Emergency Recovery](#emergency-recovery)
  - [Single User Mode](#single-user-mode)
  - [Live USB Recovery](#live-usb-recovery)
  - [Chroot Repair Completo](#chroot-repair-completo)
  - [Recovery Password Root](#recovery-password-root)
  - [Recovery Dati da Disco Guasto](#recovery-dati)
- [Scenari di Troubleshooting (30+ Casi)](#scenari-di-troubleshooting)
- [Ambiente Rescue e Recovery](#ambiente-rescue-e-recovery)
- [Guida Installazione Server Completo](#guida-installazione-server-completo)
- [Guida Hardening Completo](#guida-hardening-completo)
- [Best Practices](#best-practices)
- [FAQ — Domande Frequenti (20+ Q&A)](#faq)
- [Emergency Quick Reference Card](#emergency-quick-reference-card)

---

## Panoramica

Il troubleshooting è l'arte di diagnosticare e risolvere problemi in modo sistematico. Non è indovinare — è un processo: raccogliere dati, formulare ipotesi, testare, iterare. Questo documento raccoglie le procedure di troubleshooting per ogni area dell'amministrazione Linux, più guide pratiche complete per installazione e hardening di un server.

Il troubleshooting efficace si distingue dal "tentare a caso" per tre proprietà:

1. **Ripetibilità** — seguendo lo stesso metodo, chiunque arriva alla stessa diagnosi
2. **Misurabilità** — ogni passo produce dati osservabili, non impressioni
3. **Documentabilità** — il percorso diagnostico è tracciabile e riutilizzabile

Ogni sezione di questo documento segue la struttura: **sintomo → diagnosi → cause possibili → risoluzione → prevenzione**.

---

## Metodologia di Troubleshooting

### Framework in 6 Passi

```
1. IDENTIFICARE il problema
   → Qual è il sintomo? Cosa non funziona? Da quando?
   → Chi è impattato? Quanto è critico?
   → È riproducibile? Intermittente? Peggiorativo?
   → Cosa è cambiato di recente? (deploy, aggiornamento, config)

2. RACCOGLIERE DATI
   → Log: journalctl, /var/log/, dmesg
   → Stato: systemctl status, ss, ps, df, free
   → Cambiamenti recenti: git log, apt history, auth.log
   → Metriche: CPU, RAM, I/O, rete (vmstat, iostat, sar)
   → Confronto: questo server vs. altro identico funzionante

3. FORMULARE IPOTESI
   → Basandosi sui dati, non sull'intuizione
   → Partire dalla causa più probabile
   → Considerare: cosa è cambiato? cosa dice il log?
   → Principio di Occam: la spiegazione più semplice prima
   → Ranking ipotesi per probabilità e impatto del test

4. TESTARE l'ipotesi
   → Un cambiamento alla volta
   → Misurare prima e dopo
   → Se il test invalida l'ipotesi: tornare al passo 2
   → Non fare assunzioni — verificare

5. RISOLVERE
   → Applicare la correzione
   → Documentare cosa è stato fatto
   → Verificare che il problema sia effettivamente risolto
   → Verificare che non si siano creati nuovi problemi

6. PREVENIRE
   → Monitoring/alert per rilevare prima
   → Automazione per prevenire ricorrenza
   → Documentare per il team
   → Root Cause Analysis (RCA) per problemi critici
   → Post-mortem se ha impattato utenti/servizi
```

### Albero Decisionale

```
Il sistema ha un problema
│
├── Il sistema non risponde affatto?
│   ├── SÌ → Boot failure? → Sezione Boot/GRUB
│   │        Kernel panic? → Sezione Kernel Panic
│   │        Hardware morto? → Sezione Hardware
│   └── NO → Il sistema è lento?
│            ├── SÌ → CPU alta? → Sezione CPU
│            │        Memoria piena? → Sezione Memoria
│            │        I/O saturo? → Sezione Performance
│            │        Rete lenta? → Sezione Rete
│            └── NO → Un servizio specifico non funziona?
│                     ├── SÌ → Errore permessi? → Sezione Permessi
│                     │        Errore configurazione? → Sezione Servizi
│                     │        Porta in uso? → Sezione Servizi
│                     │        Spazio disco? → Sezione Disco
│                     └── NO → Problema intermittente?
│                              ├── SÌ → Analizzare pattern temporale nei log
│                              │        → Correlazione con cron jobs?
│                              │        → Correlazione con carico utenti?
│                              │        → Correlazione con backup?
│                              └── NO → Raccogliere più dati, ricominciare
```

### Livelli di Severità e Priorità

```
┌──────────┬──────────────────────────────────────┬────────────┐
│ Livello  │ Descrizione                          │ Tempo Max  │
├──────────┼──────────────────────────────────────┼────────────┤
│ P0-CRIT  │ Servizio in produzione DOWN          │ 15 min     │
│          │ Perdita dati in corso                 │            │
│          │ Breach di sicurezza attiva            │            │
├──────────┼──────────────────────────────────────┼────────────┤
│ P1-HIGH  │ Servizio degradato significativamente│ 1 ora      │
│          │ Funzionalità critica compromessa      │            │
│          │ Impatto su molti utenti               │            │
├──────────┼──────────────────────────────────────┼────────────┤
│ P2-MED   │ Funzionalità secondaria compromessa  │ 4 ore      │
│          │ Workaround disponibile                │            │
│          │ Impatto limitato                      │            │
├──────────┼──────────────────────────────────────┼────────────┤
│ P3-LOW   │ Problema cosmetico o minore           │ 24 ore     │
│          │ Nessun impatto utente diretto         │            │
│          │ Miglioramento prestazionale           │            │
└──────────┴──────────────────────────────────────┴────────────┘
```

### Comandi di Primo Soccorso

```bash
# "Cosa sta succedendo?" — Script di triage rapido
uptime                      # Load average
dmesg -T | tail -30         # Messaggi kernel recenti
journalctl -p err --since "1 hour ago"  # Errori recenti
systemctl --failed          # Servizi falliti
df -h                       # Spazio disco
free -h                     # Memoria
ss -tuln                    # Porte in ascolto
ps auxf | head -30          # Top processi
ip addr show                # Configurazione rete

# Script one-liner di triage completo
echo "=== UPTIME ===" && uptime && \
echo "=== MEMORY ===" && free -h && \
echo "=== DISK ===" && df -h && \
echo "=== FAILED SERVICES ===" && systemctl --failed && \
echo "=== RECENT ERRORS ===" && journalctl -p err --since "30 min ago" --no-pager | tail -20 && \
echo "=== LISTENING PORTS ===" && ss -tuln && \
echo "=== TOP PROCESSES ===" && ps aux --sort=-%cpu | head -10
```

### Strumenti Diagnostici Fondamentali

```bash
# Strumenti di base — devono essere sempre installati
# Pacchetti: procps, iproute2, util-linux, coreutils (già presenti di default)

# Strumenti avanzati — installare su ogni server
# Debian/Ubuntu:
sudo apt install sysstat htop iotop strace ltrace lsof \
  tcpdump net-tools dnsutils mtr-tiny smartmontools \
  ncdu tree pv

# RHEL/Fedora:
sudo dnf install sysstat htop iotop strace ltrace lsof \
  tcpdump net-tools bind-utils mtr smartmontools \
  ncdu tree pv

# Tabella strumenti per area
#
# ┌──────────────┬──────────────────────────────────────────┐
# │ Area         │ Strumenti                                │
# ├──────────────┼──────────────────────────────────────────┤
# │ CPU          │ top, htop, mpstat, pidstat, perf          │
# │ Memoria      │ free, vmstat, slabtop, /proc/meminfo     │
# │ Disco/I/O    │ iostat, iotop, blktrace, smartctl        │
# │ Rete         │ ss, ip, tcpdump, mtr, dig, ethtool       │
# │ Processi     │ ps, pstree, strace, ltrace, lsof         │
# │ Filesystem   │ df, du, ncdu, lsblk, blkid, fsck         │
# │ Servizi      │ systemctl, journalctl                    │
# │ Kernel       │ dmesg, sysctl, /proc/*, /sys/*           │
# │ Sicurezza    │ ausearch, aureport, aa-status, sestatus  │
# │ Performance  │ perf, bpftrace, sar, vmstat               │
# └──────────────┴──────────────────────────────────────────┘
```

---

## Troubleshooting Boot e GRUB

### Il Sistema Non Si Avvia

```bash
# GRUB non appare
# → Tenere premuto SHIFT (BIOS) o ESC (UEFI) durante il boot
# → Se GRUB è corrotto: avviare da live USB

# GRUB appare ma il kernel non parte
# → In GRUB: selezionare un kernel precedente (Advanced options)
# → Se nessun kernel funziona: boot da live USB

# Kernel panic
# → "not syncing: VFS: Unable to mount root fs"
# → Root device sbagliato in GRUB o initramfs mancante/corrotto
# → Boot da live USB, chroot, rigenera initramfs

# Riparare GRUB da Live USB
sudo mount /dev/sda2 /mnt              # Partizione root
sudo mount /dev/sda1 /mnt/boot/efi     # Partizione EFI (se UEFI)
sudo mount --bind /dev /mnt/dev
sudo mount --bind /proc /mnt/proc
sudo mount --bind /sys /mnt/sys
sudo chroot /mnt

# Dentro il chroot:
grub-install /dev/sda                   # BIOS
grub-install --target=x86_64-efi --efi-directory=/boot/efi  # UEFI
update-grub
update-initramfs -u                     # Rigenera initramfs
exit

sudo umount -R /mnt

# Rescue mode da GRUB
# In GRUB, premere 'e' per editare, aggiungere al kernel:
# systemd.unit=rescue.target    → Rescue mode (shell root, filesystem montato)
# systemd.unit=emergency.target → Emergency (shell root, filesystem read-only)
# init=/bin/bash                → Shell diretta (ultimo resort)
```

### GRUB Rescue Shell

Quando GRUB non riesce a caricare la configurazione si finisce nella shell `grub rescue>`. Questo ambiente ha comandi molto limitati.

```bash
# Situazione: schermo mostra "grub rescue>"
# GRUB non trova la partizione con /boot

# 1. Elencare i dischi e partizioni visibili da GRUB
grub rescue> ls
# Output tipico: (hd0) (hd0,msdos1) (hd0,msdos2) (hd0,gpt1) (hd0,gpt2) ...

# 2. Cercare la partizione con /boot/grub
grub rescue> ls (hd0,msdos1)/boot/grub
# Se risponde con elenco file → trovata!
# Se "error: unknown filesystem" → provare la prossima

grub rescue> ls (hd0,msdos2)/boot/grub
# Provare ogni partizione finché non si trovano i file GRUB

# 3. Una volta trovata (esempio: hd0,msdos2)
grub rescue> set root=(hd0,msdos2)
grub rescue> set prefix=(hd0,msdos2)/boot/grub

# 4. Caricare i moduli necessari
grub rescue> insmod normal
grub rescue> normal
# → Appare il menu GRUB standard

# 5. Dopo il boot, reinstallare GRUB correttamente
sudo grub-install /dev/sda
sudo update-grub

# Per sistemi GPT/UEFI la partizione sarà tipo (hd0,gpt2)
# e i comandi sono analoghi:
grub rescue> ls (hd0,gpt2)/boot/grub
grub rescue> set root=(hd0,gpt2)
grub rescue> set prefix=(hd0,gpt2)/boot/grub
grub rescue> insmod normal
grub rescue> normal
```

**Cause comuni della GRUB rescue shell:**

```
┌─────────────────────────────────────┬──────────────────────────────────────┐
│ Causa                               │ Soluzione                            │
├─────────────────────────────────────┼──────────────────────────────────────┤
│ Partizione spostata/ridimensionata  │ Aggiornare prefix/root come sopra   │
│ UUID partizione cambiato            │ Reinstallare GRUB da live USB       │
│ /boot su partizione separata        │ Montare /boot prima di update-grub  │
│   e la partizione è corrotta        │                                      │
│ Dual-boot: altro OS ha             │ Reinstallare GRUB da live USB       │
│   sovrascritto il bootloader        │                                      │
│ Disco clonato con UUID duplicato    │ Rigenerare UUID: tune2fs -U random  │
└─────────────────────────────────────┴──────────────────────────────────────┘
```

### Initramfs Shell

Se il kernel si avvia ma l'initramfs non riesce a montare il root filesystem, si finisce nella shell `(initramfs)`.

```bash
# Situazione: schermo mostra "(initramfs)" prompt
# Il kernel è partito ma non trova il root filesystem

# 1. Vedere i messaggi di errore precedenti
# Scorrere in su con SHIFT+PgUp per leggere gli errori

# 2. Elencare i dispositivi a blocchi disponibili
(initramfs) blkid
# Mostra UUID e tipo filesystem di ogni partizione

# 3. Caso comune: UUID sbagliato in /etc/fstab o in GRUB
# Prendere nota dell'UUID corretto dall'output di blkid

# 4. Provare a montare manualmente il root filesystem
(initramfs) mount /dev/sda2 /root
# Se funziona, il problema è nell'UUID/path configurato

# 5. Se il filesystem è corrotto
(initramfs) fsck /dev/sda2
# fsck.ext4 è disponibile nell'initramfs
# Rispondere 'y' alle richieste di riparazione

# 6. Se il filesystem è LVM
(initramfs) lvm vgscan
(initramfs) lvm vgchange -ay
(initramfs) mount /dev/mapper/vg-root /root

# 7. Se il filesystem è cifrato (LUKS)
(initramfs) cryptsetup luksOpen /dev/sda2 crypt_root
(initramfs) mount /dev/mapper/crypt_root /root

# 8. Uscire dall'initramfs dopo aver risolto
(initramfs) exit
# Il boot continua normalmente

# Se niente funziona: boot da live USB → chroot → rigenerare initramfs
```

### Emergency e Rescue Mode (systemd)

```bash
# RESCUE MODE (systemd.unit=rescue.target)
# - Monta i filesystem da fstab
# - Avvia servizi minimi
# - Shell root con password
# - Rete disponibile (spesso)
# Uso: problemi di configurazione, servizi che bloccano il boot

# EMERGENCY MODE (systemd.unit=emergency.target)
# - Monta solo / in read-only
# - Nessun servizio avviato
# - Shell root con password
# - Nessuna rete
# Uso: fstab corrotto, filesystem corrotto, problemi gravi

# Come accedere:
# Metodo 1: da GRUB
# → Premere 'e' sulla entry di boot
# → Aggiungere alla riga linux: systemd.unit=rescue.target
# → Premere Ctrl+X o F10 per avviare

# Metodo 2: da sistema avviato (se possibile)
sudo systemctl isolate rescue.target
sudo systemctl isolate emergency.target

# In emergency mode: rimontare / in read-write
mount -o remount,rw /

# Dopo aver fatto le correzioni:
systemctl default    # Torna al target normale
# oppure
reboot

# Se la password root non è impostata e non si riesce ad accedere:
# In GRUB, aggiungere alla riga linux:
# init=/bin/bash
# Dopo il boot:
mount -o remount,rw /
passwd root
exec /sbin/init
# oppure reboot con: /sbin/reboot -f
```

### Ricostruzione dracut/initramfs

```bash
# == DEBIAN/UBUNTU: update-initramfs ==

# Rigenerare initramfs per il kernel corrente
sudo update-initramfs -u

# Rigenerare initramfs per un kernel specifico
sudo update-initramfs -u -k 6.8.0-45-generic

# Rigenerare tutti gli initramfs
sudo update-initramfs -u -k all

# Creare initramfs per un nuovo kernel (se mancante)
sudo update-initramfs -c -k 6.8.0-45-generic

# Verbose per debug
sudo update-initramfs -u -v 2>&1 | tee /tmp/initramfs-rebuild.log

# File di configurazione:
# /etc/initramfs-tools/initramfs.conf  → opzioni globali
# /etc/initramfs-tools/modules         → moduli da includere
# /etc/initramfs-tools/conf.d/         → override configurazione

# == RHEL/FEDORA: dracut ==

# Rigenerare initramfs per il kernel corrente
sudo dracut --force

# Rigenerare per un kernel specifico
sudo dracut --force /boot/initramfs-6.8.0-100.fc40.x86_64.img 6.8.0-100.fc40.x86_64

# Verbose per debug
sudo dracut --force -v 2>&1 | tee /tmp/dracut-rebuild.log

# Includere un modulo mancante
sudo dracut --force --add "module_name"

# Aggiungere un driver specifico (es. raid, lvm)
sudo dracut --force --add-drivers "raid1 dm-raid"

# Elencare il contenuto di un initramfs (debug)
# Debian:
lsinitramfs /boot/initrd.img-$(uname -r)
# RHEL:
lsinitrd /boot/initramfs-$(uname -r).img

# File di configurazione dracut:
# /etc/dracut.conf       → opzioni globali
# /etc/dracut.conf.d/    → override per modulo

# Problemi comuni initramfs:
# 1. Modulo mancante (driver disco, RAID, LVM, crypt)
#    → Aggiungere in /etc/initramfs-tools/modules (Debian)
#    → add_drivers+="modulo" in /etc/dracut.conf.d/ (RHEL)
#
# 2. initramfs troppo grande (non entra in /boot)
#    → Pulire kernel vecchi: sudo apt autoremove
#    → Verificare spazio: df -h /boot
#
# 3. Firmware mancante (warning durante rebuild)
#    → Installare linux-firmware (aggiornato)
#    → I warning firmware sono spesso innocui
```

### Errori fstab che Bloccano il Boot

```bash
# Se /etc/fstab contiene un errore (partizione inesistente, UUID sbagliato,
# tipo filesystem errato), il boot si blocca durante il mount.

# Sintomo: il sistema entra automaticamente in emergency mode
# oppure rimane bloccato su "A start job is running for /mount/point"

# Soluzione passo per passo:

# 1. Entrare in emergency mode (se non ci si è già)
# In GRUB: aggiungere systemd.unit=emergency.target

# 2. Rimontare root in read-write
mount -o remount,rw /

# 3. Editare fstab
vi /etc/fstab
# oppure
nano /etc/fstab

# 4. Identificare la riga problematica:
# - UUID che non corrisponde a nessun dispositivo
# - Percorso dispositivo che non esiste
# - Tipo filesystem sbagliato
# - Opzioni incompatibili

# Controllare UUID reali:
blkid

# 5. Commentare la riga problematica (aggiungere # davanti)
# oppure correggere UUID/dispositivo

# 6. Testare le modifiche SENZA riavviare
mount -a
# Se nessun errore → le modifiche sono corrette

# 7. Ricaricare le unit systemd e riavviare
systemctl daemon-reload
reboot

# PREVENZIONE: usare nofail nelle opzioni di fstab per mount non critici
# Esempio:
# UUID=xxxx  /data  ext4  defaults,nofail  0  2
# Con nofail, il boot continua anche se il mount fallisce

# Opzione x-systemd.device-timeout= per impostare timeout
# UUID=xxxx  /net-share  nfs  defaults,nofail,x-systemd.device-timeout=10  0  0
```

### Problemi Comuni di Boot

```bash
# Filesystem read-only dopo boot
mount -o remount,rw /                   # Rimonta in read-write
# Se fallisce: filesystem corrotto → fsck dal rescue mode

# Servizio che blocca il boot
# Boot in rescue mode → systemctl disable servizio_problematico

# fstab con errore (mount fallisce → boot bloccato)
# Boot con: systemd.unit=emergency.target
# Editare /etc/fstab, commentare la riga problematica
# systemctl daemon-reload
# reboot

# "A start job is running for..." bloccato per 90+ secondi
# Un mount o un servizio sta aspettando un timeout
# 1. Attendere il timeout (90s default)
# 2. Identificare cosa aspetta dal messaggio
# 3. Dopo il boot: systemctl list-jobs per vedere cosa è ancora in pending
# 4. Correggere il mount/servizio problematico

# Plymouth (splash screen) nasconde i messaggi di errore
# Rimuovere "quiet splash" dalla riga kernel in GRUB per vedere i dettagli
# In GRUB: premere 'e', rimuovere "quiet splash", Ctrl+X

# Boot in loop: initramfs → boot → crash → initramfs
# 1. Boot con kernel precedente da GRUB (Advanced Options)
# 2. Se funziona: rimuovere kernel problematico, aggiornare initramfs
# 3. Se nessun kernel funziona: live USB → chroot → reinstallare kernel

# Disk order changed (BIOS vs UEFI, aggiunto disco)
# Il GRUB cerca il root su disco sbagliato
# Soluzione: usare UUID in GRUB e fstab, non /dev/sdX
# grub-mkconfig usa UUID di default → update-grub
```

---

## Kernel Panic

### Leggere i Messaggi di Panic

```bash
# Un kernel panic è il crash fatale del kernel Linux.
# Il sistema si ferma completamente, nessun processo può girare.

# Anatomia di un messaggio kernel panic:

# Kernel panic - not syncing: <motivo>                  ← 1. CAUSA
# CPU: 0 PID: 1 Comm: swapper/0 Not tainted 6.8.0-45   ← 2. CONTESTO
# Hardware name: ...
# Call Trace:                                            ← 3. STACK TRACE
#  <IRQ>
#  dump_stack_lvl+0x48/0x60
#  panic+0x1f4/0x370
#  mount_block_root+0x1a7/0x270                         ← 4. FUNZIONE COLPEVOLE
#  prepare_namespace+0x8e/0x190
#  kernel_init_freeable+0x2e0/0x310
#  kernel_init+0x15/0x1b0
#  ret_from_fork+0x2c/0x50
# ---[ end Kernel panic - not syncing: ... ]---

# Come leggere:
# 1. CAUSA: la riga "Kernel panic - not syncing:" indica il motivo
# 2. CONTESTO: il PID, il comando, la versione kernel
# 3. STACK TRACE: la sequenza di chiamate che ha portato al panic
# 4. FUNZIONE COLPEVOLE: la funzione più specifica prima del panic()

# Tipi di panic più comuni:

# "VFS: Unable to mount root fs on unknown-block(0,0)"
# → Il kernel non trova il root filesystem
# → Causa: UUID sbagliato, initramfs non contiene i driver del disco,
#          dispositivo root cambiato

# "Attempted to kill init!"
# → PID 1 (init/systemd) è crashato
# → Causa: binario init corrotto, librerie mancanti,
#          configurazione systemd gravemente corrotta

# "not syncing: Fatal exception in interrupt"
# → Eccezione fatale durante gestione interrupt
# → Causa spesso hardware: RAM difettosa, CPU surriscaldata

# "Kernel panic - not syncing: Out of memory and no killable processes"
# → Memoria esaurita e OOM killer non riesce a liberare nulla
# → Causa: memory leak nel kernel, configurazione swap assente

# Dopo un panic, se il sistema si riavvia:
# I messaggi sono nel log precedente:
journalctl -b -1 -p emerg    # Log del boot precedente, solo emergency
journalctl -b -1 -k          # Solo messaggi kernel del boot precedente
dmesg -T                      # Messaggi kernel del boot corrente
```

### Configurazione kdump

```bash
# kdump cattura un dump della memoria del kernel al momento del crash,
# permettendo analisi post-mortem dettagliata.

# == Installazione ==

# Debian/Ubuntu
sudo apt install linux-crashdump kdump-tools crash
# Durante l'installazione: rispondere YES a "Enable kdump"

# RHEL/Fedora
sudo dnf install kexec-tools crash kernel-debuginfo

# == Configurazione ==

# 1. Riservare memoria per kdump nel kernel
# Editare /etc/default/grub (Debian) o /etc/default/grub2 (RHEL):
# GRUB_CMDLINE_LINUX="... crashkernel=256M"
# 256M è sufficiente per la maggior parte dei server
# Per server con molta RAM: crashkernel=512M

# Applicare le modifiche GRUB:
sudo update-grub          # Debian/Ubuntu
sudo grub2-mkconfig -o /boot/grub2/grub.cfg  # RHEL/Fedora

# 2. Configurare dove salvare il dump
# Debian: /etc/default/kdump-tools
# KDUMP_COREDIR="/var/crash"
# KDUMP_COMPRESSOR="lz4"     # Compressione veloce

# RHEL: /etc/kdump.conf
# path /var/crash
# core_collector makedumpfile -l --message-level 7 -d 31

# 3. Abilitare e avviare il servizio
sudo systemctl enable kdump
sudo systemctl start kdump

# 4. Verificare che kdump è attivo
sudo systemctl status kdump
# Deve mostrare "active (exited)" o "operational"

# Verificare che crashkernel è riservato:
cat /proc/cmdline | grep crashkernel
# Verificare la memoria riservata:
cat /sys/kernel/kexec_crash_size

# == Test ==
# ATTENZIONE: questo CAUSA un kernel panic! Solo su sistemi di test.
# echo c > /proc/sysrq-trigger

# Dopo il reboot, il dump sarà in /var/crash/
# Il file vmcore è il dump della memoria del kernel
```

### Analisi Crash con crash utility

```bash
# Il tool 'crash' è un debugger interattivo per analizzare vmcore dumps

# Aprire un crash dump
sudo crash /usr/lib/debug/lib/modules/$(uname -r)/vmlinux /var/crash/*/vmcore

# Comandi crash essenziali:

# Informazioni sul crash
crash> sys
# Mostra: versione kernel, hostname, data crash, motivo panic

# Stack trace del task che ha causato il panic
crash> bt
# Mostra il backtrace del processo colpevole

# Stack trace di tutti i processi
crash> foreach bt

# Log del kernel (dmesg del momento del crash)
crash> log
# Cercare qui i messaggi di errore

# Processi attivi al momento del crash
crash> ps
# Cercare processi in stato D (uninterruptible sleep) o R (running)

# Informazioni su un processo specifico
crash> task <PID>

# Stato memoria al momento del crash
crash> kmem -i
# Mostra allocazione memoria kernel

# Informazioni sui moduli caricati
crash> mod

# Uscire
crash> exit

# Se non si ha crash, analisi base con dmesg/journalctl:
# 1. Cercare "Call Trace" nel log precedente
journalctl -b -1 | grep -A 30 "Call Trace"

# 2. Cercare il modulo colpevole
journalctl -b -1 | grep -B 5 "kernel panic"

# 3. Se il modulo è di terze parti (es. driver NVIDIA, VirtualBox):
# → Aggiornare o rimuovere il modulo
# → Testare con il modulo blacklistato:
echo "blacklist modulo_sospetto" | sudo tee /etc/modprobe.d/blacklist-debug.conf
sudo update-initramfs -u
```

### Kernel Panic Comuni e Soluzioni

```
┌─────────────────────────────────────┬──────────────────────────────────────┐
│ Messaggio Panic                     │ Causa e Soluzione                    │
├─────────────────────────────────────┼──────────────────────────────────────┤
│ VFS: Unable to mount root fs        │ Root device non trovato.             │
│                                     │ → Verificare UUID in GRUB config     │
│                                     │ → Rigenerare initramfs con driver    │
│                                     │   del controller disco               │
├─────────────────────────────────────┼──────────────────────────────────────┤
│ Attempted to kill init!             │ PID 1 è crashato.                    │
│                                     │ → Reinstallare systemd/init          │
│                                     │ → Verificare librerie: ldd /sbin/init│
│                                     │ → Boot con init=/bin/bash e riparare │
├─────────────────────────────────────┼──────────────────────────────────────┤
│ Fatal exception in interrupt        │ Problema hardware probabile.         │
│                                     │ → Testare RAM: memtest86+            │
│                                     │ → Verificare temperatura CPU         │
│                                     │ → Testare con kernel precedente      │
├─────────────────────────────────────┼──────────────────────────────────────┤
│ Out of memory and no killable       │ RAM + swap esauriti.                  │
│ processes                           │ → Aggiungere swap                    │
│                                     │ → Identificare memory leak           │
│                                     │ → Aumentare RAM                      │
├─────────────────────────────────────┼──────────────────────────────────────┤
│ BUG: unable to handle page fault    │ Dereferenza puntatore NULL/invalido. │
│                                     │ → Spesso driver/modulo buggy         │
│                                     │ → Aggiornare kernel                  │
│                                     │ → Blacklist modulo sospetto          │
├─────────────────────────────────────┼──────────────────────────────────────┤
│ Kernel panic - not syncing: Watchdog│ CPU bloccata per troppo tempo.       │
│ detected hard LOCKUP on cpu N       │ → Problema hardware o driver         │
│                                     │ → Verificare interrupt storm         │
│                                     │ → Aggiornare firmware/BIOS           │
├─────────────────────────────────────┼──────────────────────────────────────┤
│ general protection fault            │ Accesso memoria illegale nel kernel. │
│                                     │ → Modulo buggy, aggiornare kernel    │
│                                     │ → Testare RAM con memtest86+         │
└─────────────────────────────────────┴──────────────────────────────────────┘
```

---

## Troubleshooting Disco e Filesystem

### Remount Read-Only e Recovery

```bash
# Il kernel rimonta automaticamente un filesystem in read-only quando
# rileva errori I/O o corruzione. È un meccanismo di protezione.

# Sintomi:
# - "Read-only file system" su ogni operazione di scrittura
# - dmesg mostra "EXT4-fs error" o "Remounting filesystem read-only"
# - Applicazioni crashano perché non possono scrivere

# Diagnosi:
dmesg -T | grep -i "read.only\|ext4.fs error\|I/O error\|remount"
# Cercare la CAUSA del remount:
# "EXT4-fs error: ... I/O failure" → disco fisico guasto
# "EXT4-fs error: ... corrupt" → filesystem corrotto
# "I/O error, dev sd*" → errore disco hardware

# Procedura di recovery:
# 1. Verificare la salute del disco
sudo smartctl -H /dev/sda          # Quick health check
sudo smartctl -a /dev/sda          # Dettagli completi SMART
# Se SMART dice FAILED → disco in fin di vita, backup IMMEDIATO

# 2. Se il disco è sano, tentare remount rw
sudo mount -o remount,rw /
# Se funziona → il problema era transitorio (bug driver, cavo)
# Se fallisce → serve fsck

# 3. Per fsck: il filesystem DEVE essere smontato
# Se è il root filesystem → boot da live USB
# Se è un mount point secondario:
sudo umount /mount/point
sudo fsck -f /dev/sdXN
sudo mount /mount/point

# 4. Se non riesci a smontare (filesystem in uso):
sudo lsof +D /mount/point          # Chi lo usa?
# Terminare i processi che lo usano, poi umount
# Come ultima risorsa: umount -l (lazy unmount)
# Il filesystem viene smontato quando nessun processo lo usa più
```

### Procedure fsck Dettagliate

```bash
# fsck (File System Consistency Check) verifica e ripara filesystem

# REGOLA FONDAMENTALE: MAI eseguire fsck su filesystem montati!
# Eccezione: fsck su / in read-only durante boot è sicuro (fatto automaticamente)

# == EXT4 ==
# Check standard (interattivo)
sudo e2fsck -f /dev/sda1

# Check automatico (ripara tutto senza chiedere)
sudo e2fsck -fy /dev/sda1

# Check verboso con progresso
sudo e2fsck -fvy /dev/sda1

# Solo check, nessuna riparazione (safe mode)
sudo e2fsck -fn /dev/sda1

# Opzioni importanti:
# -f  forza check anche se il filesystem sembra pulito
# -y  rispondi yes a tutto (batch mode)
# -n  rispondi no a tutto (solo check)
# -p  ripara automaticamente problemi sicuri (preen mode)
# -c  cerca bad blocks (molto lento, ne vale la pena su disco sospetto)

# Check con ricerca bad blocks (lento ma completo)
sudo e2fsck -fc /dev/sda1

# == XFS ==
# XFS usa xfs_repair, non fsck
sudo xfs_repair /dev/sda1

# Dry run (solo check)
sudo xfs_repair -n /dev/sda1

# Se xfs_repair dice "dirty log": prima montare e smontare pulito
sudo mount /dev/sda1 /mnt && sudo umount /mnt
sudo xfs_repair /dev/sda1

# Se il log è irrecuperabile (ultimo resort, può perdere dati):
sudo xfs_repair -L /dev/sda1

# == BTRFS ==
sudo btrfs check /dev/sda1

# Con riparazione (ATTENZIONE: sperimentale su versioni vecchie)
sudo btrfs check --repair /dev/sda1

# Btrfs scrub (verifica online, filesystem montato)
sudo btrfs scrub start /mount/point
sudo btrfs scrub status /mount/point

# == Forzare fsck al prossimo boot ==
# Metodo 1: file nel root
sudo touch /forcefsck

# Metodo 2: tune2fs (solo ext4)
sudo tune2fs -C 100 /dev/sda1   # Imposta mount count alto → trigger fsck

# Metodo 3: parametro kernel in GRUB
# Aggiungere: fsck.mode=force
```

### Superblock Corrotto

```bash
# Il superblock contiene i metadati fondamentali del filesystem.
# Se corrotto, il filesystem è inaccessibile.

# Sintomi:
# "can't read superblock" durante mount
# "bad magic number in super-block" durante fsck
# Il filesystem semplicemente non si monta

# == Recovery superblock ext4 ==

# 1. Trovare i backup del superblock
sudo dumpe2fs /dev/sda1 | grep -i superblock
# Output tipico:
# Primary superblock at 0, ...
# Backup superblock at 32768, ...
# Backup superblock at 98304, ...
# Backup superblock at 163840, ...

# Se dumpe2fs non funziona, calcolare le posizioni:
sudo mke2fs -n /dev/sda1
# -n = dry run, NON formatta, mostra solo le posizioni dei superblock

# 2. Usare un superblock di backup per il check
sudo e2fsck -b 32768 /dev/sda1

# 3. Se il check riesce, montare con superblock di backup
sudo mount -o sb=32768 /dev/sda1 /mnt

# 4. Dopo il mount, copiare i dati importanti altrove come precauzione

# 5. Ripristinare il superblock primario
# Il modo più affidabile: e2fsck con superblock backup
# e2fsck ripara automaticamente il superblock primario quando
# usa un backup come riferimento

# == Recovery superblock XFS ==
# XFS ha un superblock secondario a blocco 1
sudo xfs_repair /dev/sda1
# xfs_repair cerca automaticamente superblock alternativi

# == Se niente funziona ==
# Ultimo resort: testdisk per recuperare dati
sudo apt install testdisk
sudo testdisk /dev/sda
# testdisk può trovare partizioni perse e recuperare file
```

### Journal Recovery

```bash
# Il journal (log) del filesystem tiene traccia delle operazioni
# in corso per garantire consistenza dopo un crash.

# == ext4 Journal Recovery ==

# Stato del journal:
sudo dumpe2fs /dev/sda1 | grep -i journal
# "Journal features: ... journal_incompat_revoke" → journal attivo
# "Journal size: 128M" → dimensione

# Il journal viene riprodotto automaticamente al mount dopo un crash
# Se il replay fallisce:

# 1. Tentare fsck con replay forzato
sudo e2fsck -fy /dev/sda1

# 2. Se il journal è irrecuperabile:
# ATTENZIONE: si perdono le operazioni nel journal!
# Rimuovere e ricreare il journal:
sudo tune2fs -O ^has_journal /dev/sda1
sudo e2fsck -fy /dev/sda1
sudo tune2fs -O has_journal /dev/sda1
sudo e2fsck -fy /dev/sda1

# == XFS Journal Recovery ==
# Il journal XFS si chiama "log"
# Il replay è automatico al mount. Se fallisce:

# Montare senza replay (read-only, per salvare dati)
sudo mount -o ro,norecovery /dev/sda1 /mnt

# Forzare azzeramento log (PERDITA DATI nel journal)
sudo xfs_repair -L /dev/sda1

# == Btrfs Journal ==
# Btrfs usa COW (Copy-On-Write), non ha un journal tradizionale
# Recovery: usare snapshot precedenti
sudo btrfs subvolume list /mount/point
sudo btrfs subvolume snapshot /mount/point/old /mount/point/recovered
```

### Problemi Spazio Disco

```bash
# SPAZIO DISCO
df -h                                   # Spazio per filesystem
df -ih                                  # Inode disponibili
du -sh /var/* | sort -h | tail -20      # Directory più grandi

# "No space left on device" ma df mostra spazio
# → Inode esauriti: df -i
# → File cancellati ma aperti: lsof +D /mount | grep deleted
# → Quota raggiunta: quota -u user

# Trovare file grandi — metodi multipli:

# 1. du classico (top 20 directory più grandi)
sudo du -sh /* 2>/dev/null | sort -h | tail -20
sudo du -sh /var/* 2>/dev/null | sort -h | tail -20
sudo du -sh /var/log/* 2>/dev/null | sort -h | tail -20

# 2. du ricorsivo per file singoli > 100MB
sudo find / -xdev -type f -size +100M -exec ls -lh {} \; 2>/dev/null | sort -k5 -h

# 3. ncdu — interfaccia interattiva (il migliore per esplorazione)
sudo ncdu /                    # Analisi completa
sudo ncdu /var                 # Solo /var
# Navigazione: frecce, 'd' per cancellare, 'q' per uscire

# 4. du con esclusione mount secondari
sudo du -sh --exclude=/proc --exclude=/sys --exclude=/dev /* 2>/dev/null | sort -h

# File cancellati ma ancora aperti (spazio non rilasciato)
sudo lsof +L1
# Mostra file con link count 0 (cancellati) ma ancora aperti
# Soluzione: riavviare il processo che tiene aperto il file
# oppure troncare il file descriptor:
# > /proc/<PID>/fd/<FD_NUMBER>    # Tronca a 0 byte

# Inode esauriti (raro ma devastante)
df -ih
# Se %IUse è 100% → troppi piccoli file
# Trovare directory con troppi file:
sudo find / -xdev -printf "%h\n" | sort | uniq -c | sort -rn | head -20
# Tipico colpevole: mail queue, session files, cache files
```

### Pulizia Spazio

```bash
# == 1. PULIZIA JOURNAL systemd ==
# I journal di systemd possono crescere molto

# Vedere dimensione attuale
journalctl --disk-usage

# Pulire i log più vecchi di 7 giorni
sudo journalctl --vacuum-time=7d

# Limitare a 500MB
sudo journalctl --vacuum-size=500M

# Configurazione permanente in /etc/systemd/journald.conf:
# SystemMaxUse=500M          # Massimo spazio su disco
# SystemMaxFileSize=50M      # Massimo per singolo file
# MaxRetentionSec=1month     # Massima retention

# Applicare:
sudo systemctl restart systemd-journald

# == 2. PULIZIA CACHE PACCHETTI ==

# Debian/Ubuntu — cache APT
sudo du -sh /var/cache/apt/archives/    # Dimensione cache
sudo apt clean                           # Rimuove TUTTI i .deb scaricati
sudo apt autoclean                       # Rimuove solo .deb obsoleti

# RHEL/Fedora — cache DNF
sudo du -sh /var/cache/dnf/
sudo dnf clean all

# == 3. RIMOZIONE KERNEL VECCHI ==

# Debian/Ubuntu
# Elencare kernel installati:
dpkg -l | grep linux-image | grep -v $(uname -r)

# Rimuovere kernel specifico:
sudo apt remove --purge linux-image-X.X.X-XX-generic
sudo apt autoremove --purge          # Rimuove tutti i kernel non necessari
sudo update-grub                      # Aggiorna GRUB dopo rimozione

# RHEL/Fedora
# Elencare kernel installati:
rpm -qa | grep kernel | sort

# DNF tiene gli ultimi N kernel (default 3)
# Configurazione in /etc/dnf/dnf.conf: installonly_limit=3
# Rimuovere manualmente:
sudo dnf remove kernel-X.X.X

# == 4. PULIZIA /tmp ==
# /tmp dovrebbe essere pulito automaticamente (tmpfiles.d)
# Verificare la configurazione:
cat /usr/lib/tmpfiles.d/tmp.conf
# "q /tmp 1777 root root 10d" → file più vecchi di 10 giorni rimossi

# Pulizia manuale di file vecchi in /tmp
sudo find /tmp -type f -atime +7 -delete          # File non acceduti da 7+ giorni
sudo find /tmp -type d -empty -delete 2>/dev/null  # Directory vuote

# == 5. PULIZIA /var/log ==
# I log sono gestiti da logrotate ma possono crescere

# Trovare log grandi
sudo du -sh /var/log/* 2>/dev/null | sort -h | tail -10

# Troncare un log grande (non cancellare! Il processo potrebbe non riaprirlo)
sudo truncate -s 0 /var/log/syslog.1
# Mai: rm /var/log/syslog ← il servizio potrebbe non ricreare il file

# Forzare rotazione di tutti i log
sudo logrotate -f /etc/logrotate.conf

# Verificare configurazione logrotate per un servizio
cat /etc/logrotate.d/nginx

# == 6. PULIZIA SNAP (Ubuntu) ==
# Gli snap mantengono revisioni vecchie
snap list --all | grep -v "^Name" | awk '/disabled/{print "sudo snap remove --purge " $1 " --revision=" $3}'
# Eseguire i comandi generati per rimuovere le revisioni disabilitate

# == 7. PULIZIA DOCKER (se installato) ==
# Docker può consumare enormi quantità di spazio
docker system df                        # Panoramica uso spazio
docker system prune -a                  # Rimuove tutto il non-usato
docker volume prune                     # Rimuove volumi orfani

# == 8. PULIZIA FLATPAK (se installato) ==
flatpak uninstall --unused              # Rimuove runtime non usati

# == 9. PULIZIA UTENTE ==
du -sh ~/.cache/*   | sort -h | tail -10    # Cache utente
du -sh ~/.local/*   | sort -h | tail -10    # Dati locali
# Browser cache, IDE cache, pip cache, npm cache sono i soliti sospetti
```

---

## Troubleshooting Rete

### Diagnosi Sistematica Layer per Layer

```bash
# Approccio bottom-up: dal livello fisico all'applicazione
# Se un layer è rotto, quelli sopra non possono funzionare

# ┌─────────────────────────────────────────────────────────┐
# │ Layer 7: Applicazione  (curl, wget, browser)            │
# │ Layer 4: Trasporto     (TCP/UDP, ss, nc)                 │
# │ Layer 3: Rete          (IP, routing, ping, traceroute)   │
# │ Layer 2: Data Link     (ARP, MAC, VLAN)                  │
# │ Layer 1: Fisico        (cavo, link, ethtool)              │
# └─────────────────────────────────────────────────────────┘

# == LAYER 1: Link Fisico ==
ip link show                            # Interfaccia UP?
# state UP → link attivo
# state DOWN → cavo scollegato o interfaccia disabilitata
# NO-CARRIER → cavo scollegato

ethtool eth0                            # Speed, duplex, link detected?
# Speed: 1000Mb/s → gigabit OK
# Duplex: Full → OK (Half = problema)
# Link detected: yes → cavo OK

# Portare su un'interfaccia:
sudo ip link set eth0 up

# == LAYER 2: Connettività Locale ==
ip addr show                            # IP configurato?
ip neigh show                           # ARP, gateway visibile?
arping -I eth0 192.168.1.1              # Il gateway risponde?

# Se l'IP non è configurato:
# DHCP:
sudo dhclient eth0
# oppure:
sudo dhcpcd eth0

# Statico:
sudo ip addr add 192.168.1.100/24 dev eth0

# == LAYER 3: Routing ==
ip route show                           # Route presente?
ip route get 8.8.8.8                    # Quale route per internet?
ping -c 3 192.168.1.1                   # Gateway raggiungibile?
ping -c 3 8.8.8.8                       # Internet raggiungibile?
traceroute 8.8.8.8                      # Dove si ferma?
mtr -r -c 10 8.8.8.8                    # Traceroute + statistiche

# Se manca default gateway:
sudo ip route add default via 192.168.1.1

# == LAYER 4: Trasporto ==
ss -tuln                                # Porte in ascolto
nc -zv host 80                          # Porta raggiungibile?
nc -zv host 22                          # SSH aperto?

# Test con timeout
nc -z -w 3 host 443                     # Timeout 3 secondi

# == LAYER 7: Applicazione ==
curl -v https://example.com             # HTTP funziona?
curl -I https://example.com             # Solo headers

# == DNS (trasversale) ==
dig example.com                         # Risoluzione DNS
dig @8.8.8.8 example.com               # DNS alternativo
cat /etc/resolv.conf                    # Configurazione DNS

# == FIREWALL ==
sudo iptables -L -n -v                 # Regole firewall
sudo iptables -L -n -v | grep DROP     # Cosa viene droppato?
sudo nft list ruleset                    # nftables (sistemi moderni)
```

### tcpdump

```bash
# tcpdump è l'analizzatore di pacchetti CLI fondamentale

# Catturare tutto il traffico su un'interfaccia
sudo tcpdump -i eth0

# Catturare solo traffico verso/da un host specifico
sudo tcpdump -i eth0 host 192.168.1.100

# Catturare solo traffico su una porta
sudo tcpdump -i eth0 port 80
sudo tcpdump -i eth0 port 443

# Catturare traffico DNS (porta 53)
sudo tcpdump -i any port 53

# Catturare e salvare in file pcap (apribile con Wireshark)
sudo tcpdump -i eth0 -w /tmp/capture.pcap -c 1000
# -c 1000 = cattura solo 1000 pacchetti (evita file enormi)

# Leggere un file pcap salvato
tcpdump -r /tmp/capture.pcap

# Filtri avanzati
# SYN packets (nuove connessioni TCP)
sudo tcpdump -i eth0 'tcp[tcpflags] & (tcp-syn) != 0'

# Traffico HTTP (GET/POST)
sudo tcpdump -i eth0 -A -s 0 'tcp port 80'
# -A = ASCII dump del payload
# -s 0 = cattura intero pacchetto

# ICMP (ping)
sudo tcpdump -i eth0 icmp

# Traffico da/verso una subnet
sudo tcpdump -i eth0 net 192.168.1.0/24

# Combinare filtri
sudo tcpdump -i eth0 'host 10.0.0.5 and port 443'
sudo tcpdump -i eth0 'src host 10.0.0.5 and dst port 80'

# Opzioni utili
# -n    non risolvere nomi (più veloce)
# -nn   non risolvere nomi né porte
# -X    hex + ASCII dump
# -v    verbose (-vv, -vvv per più dettaglio)
# -c N  cattura solo N pacchetti
# -e    mostra MAC address

# Esempio pratico: debug connessione HTTPS fallita
sudo tcpdump -i eth0 -nn 'host example.com and port 443' -v
# Cercare:
# - SYN inviato ma nessun SYN-ACK → firewall blocca
# - SYN-ACK ricevuto ma RST subito → TLS handshake fallito
# - Connessione stabilita ma RST dopo → applicazione rifiuta
```

### ss — Stato Socket Avanzato

```bash
# ss è il sostituto moderno di netstat, più veloce e informativo

# Tutte le connessioni TCP
ss -ta

# Solo socket in ascolto (server)
ss -tuln
# -t = TCP
# -u = UDP
# -l = listening (solo in ascolto)
# -n = numerico (non risolvere nomi)

# Connessioni stabilite
ss -tn state established

# Vedere quale processo possiede un socket
ss -tulnp
# -p = mostra processo (richiede root per processi di altri utenti)

# Statistiche dettagliate su una connessione
ss -ti
# Mostra: RTT, cwnd, retransmits, MSS — utile per debug performance TCP

# Contare connessioni per stato
ss -s
# Total, TCP, UDP, UNIX socket counts e statistiche

# Trovare tutte le connessioni verso un host remoto
ss -tn dst 10.0.0.5

# Trovare chi usa una porta specifica
ss -tulnp | grep :8080
# Alternativa:
sudo lsof -i :8080

# Connessioni in TIME_WAIT (potenziale port exhaustion)
ss -tn state time-wait | wc -l

# Connessioni in CLOSE_WAIT (possibile connection leak nel codice)
ss -tn state close-wait
# Molte CLOSE_WAIT = l'applicazione non chiude correttamente le connessioni

# Socket UNIX domain
ss -lxp
# Utile per debug IPC tra servizi (es. docker.sock, php-fpm.sock)
```

### ip e route

```bash
# Comando 'ip' — lo strumento universale di networking moderno

# == Interfacce ==
ip addr show                    # Tutti gli indirizzi
ip addr show eth0               # Solo eth0
ip -br addr show                # Formato breve e leggibile

# Aggiungere/rimuovere indirizzo
sudo ip addr add 192.168.1.100/24 dev eth0
sudo ip addr del 192.168.1.100/24 dev eth0

# == Link (Layer 2) ==
ip link show                    # Stato interfacce
ip -s link show eth0            # Con statistiche (errori, drop, collisioni)
# RX errors alto → possibile cavo difettoso
# TX dropped alto → possibile congestione

sudo ip link set eth0 up       # Attivare
sudo ip link set eth0 down     # Disattivare

# == Routing ==
ip route show                   # Tabella routing
ip route get 8.8.8.8            # Route specifica per una destinazione
# Utile per capire da quale interfaccia e gateway esce il traffico

# Aggiungere route
sudo ip route add 10.0.0.0/8 via 192.168.1.1
sudo ip route add default via 192.168.1.1

# Rimuovere route
sudo ip route del 10.0.0.0/8

# Route policy (multiple tabelle routing)
ip rule show
ip route show table main
ip route show table local

# == ARP/Neighbor ==
ip neigh show                   # Cache ARP
# REACHABLE → host visto di recente
# STALE → non verificato di recente
# FAILED → ARP resolution fallita (host non esiste sulla LAN)

# Flush cache ARP (debug)
sudo ip neigh flush dev eth0

# == Monitoraggio in tempo reale ==
ip monitor                      # Tutti gli eventi di rete
ip monitor route                # Solo cambiamenti routing
ip monitor link                 # Solo cambiamenti link

# == Debug connettività rapido ==
# 1. Ho un IP?
ip -br addr show | grep UP
# 2. Ho un gateway?
ip route show | grep default
# 3. Raggiungo il gateway?
ping -c 1 $(ip route show | grep default | awk '{print $3}')
# 4. Raggiungo internet?
ping -c 1 8.8.8.8
# 5. Il DNS funziona?
dig +short example.com
```

### Problemi Comuni di Rete

```bash
# "Network unreachable" → Manca il default gateway
ip route add default via 192.168.1.1

# "Connection refused" → Servizio non in ascolto
ss -tuln | grep PORT

# "Connection timed out" → Firewall, rete, server down
# Verificare in ordine: ping, traceroute, iptables

# "Name resolution failure" → Problema DNS
# Ping per IP funziona ma per nome no → DNS
# Fix rapido: aggiungere nameserver in /etc/resolv.conf

# Interfaccia che perde IP dopo sleep/resume (laptop)
# NetworkManager gestisce male il resume
sudo systemctl restart NetworkManager

# MTU mismatch (pacchetti grandi non passano, piccoli sì)
# Sintomo: SSH funziona, ma download/upload grandi si bloccano
ping -c 3 -M do -s 1472 host     # Testa MTU 1500 (1472 + 28 header)
# Se timeout: ridurre -s finché non funziona
# Fix: sudo ip link set eth0 mtu 1400

# Bonding/Team interface down
# Verificare stato slave:
cat /proc/net/bonding/bond0
# o
teamdctl team0 state
```

---

## Troubleshooting DNS

### /etc/resolv.conf e Configurazione

```bash
# /etc/resolv.conf è il file di configurazione DNS primario
cat /etc/resolv.conf

# Contenuto tipico:
# nameserver 8.8.8.8
# nameserver 8.8.4.4
# search example.com
# options timeout:2 attempts:3

# ATTENZIONE: su sistemi moderni /etc/resolv.conf è spesso un symlink
# gestito da systemd-resolved, NetworkManager, o resolvconf
ls -la /etc/resolv.conf
# Se punta a /run/systemd/resolve/stub-resolv.conf → systemd-resolved
# Se punta a /run/NetworkManager/* → NetworkManager

# Verificare chi gestisce il file:
# Se c'è un commento "Generated by" → non editare direttamente

# Se il file viene sovrascritto dopo ogni modifica manuale:
# Opzione 1: configurare tramite NetworkManager
sudo nmcli con mod "Nome-Connessione" ipv4.dns "8.8.8.8 8.8.4.4"
sudo nmcli con up "Nome-Connessione"

# Opzione 2: configurare tramite systemd-resolved
sudo vim /etc/systemd/resolved.conf
# [Resolve]
# DNS=8.8.8.8 8.8.4.4
# FallbackDNS=1.1.1.1
sudo systemctl restart systemd-resolved

# Opzione 3: rendere il file immutabile (sconsigliato, hack)
sudo chattr +i /etc/resolv.conf    # Nessun processo può modificarlo
# Per rimuovere: sudo chattr -i /etc/resolv.conf
```

### systemd-resolved

```bash
# systemd-resolved è il resolver DNS moderno su distribuzioni systemd
# Ascolta su 127.0.0.53:53 come stub resolver locale

# Stato del servizio
systemctl status systemd-resolved

# Stato DNS dettagliato
resolvectl status
# Mostra: DNS server per interfaccia, DNSSEC, DNS-over-TLS

# Query DNS via resolvectl
resolvectl query example.com

# Cache DNS — svuotare
resolvectl flush-caches

# Statistiche cache
resolvectl statistics

# Configurazione principale: /etc/systemd/resolved.conf
# [Resolve]
# DNS=8.8.8.8 1.1.1.1
# FallbackDNS=9.9.9.9
# DNSSEC=allow-downgrade
# DNSOverTLS=opportunistic
# Cache=yes
# DNSStubListener=yes

# Problema comune: /etc/resolv.conf non punta al stub resolver
# Deve contenere: nameserver 127.0.0.53
# Ricreare il symlink:
sudo ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf

# Per bypassare systemd-resolved temporaneamente:
# Usare il resolver reale direttamente:
sudo ln -sf /run/systemd/resolve/resolv.conf /etc/resolv.conf
# (contiene i nameserver effettivi senza il stub)

# Log dettagliato di risoluzione DNS
sudo resolvectl log-level debug
journalctl -u systemd-resolved -f
# Ripristinare: sudo resolvectl log-level info
```

### nsswitch.conf

```bash
# /etc/nsswitch.conf controlla l'ORDINE in cui il sistema risolve i nomi
cat /etc/nsswitch.conf

# Riga rilevante per DNS:
# hosts: files dns myhostname
#
# Significato:
# files  → cerca prima in /etc/hosts
# dns    → poi usa i nameserver DNS
# myhostname → per ultimo, il nome dell'host locale

# Se manca "dns" dalla riga hosts → il sistema non usa DNS!
# Se "files" è dopo "dns" → /etc/hosts viene ignorato

# Su sistemi con systemd-resolved:
# hosts: files resolve [!UNAVAIL=return] dns myhostname
#
# resolve → usa systemd-resolved (con caching, DNSSEC)
# [!UNAVAIL=return] → se resolved non è disponibile, passa a dns

# Se nss-resolve non è installato:
# hosts: files dns myhostname (senza resolve)
# Il sistema usa direttamente i nameserver in /etc/resolv.conf

# Debug: getent usa nsswitch.conf
getent hosts example.com
# Se restituisce risultato → nsswitch funziona
# Se non restituisce niente → problema in nsswitch o DNS

getent ahosts example.com     # Con tutti gli indirizzi (IPv4+IPv6)
```

### Debug con dig/nslookup/host

```bash
# dig è il tool di debug DNS più potente

# Query base
dig example.com
# Sezioni importanti dell'output:
# ;; QUESTION SECTION   → cosa hai chiesto
# ;; ANSWER SECTION     → la risposta
# ;; AUTHORITY SECTION  → nameserver autoritativo
# ;; ADDITIONAL SECTION → info extra (glue records)
# ;; Query time: 23 msec → tempo di risposta
# ;; SERVER: 127.0.0.53#53 → quale server ha risposto

# Query solo risposta (compatto)
dig +short example.com

# Query tipo specifico
dig example.com MX        # Mail exchanger
dig example.com NS        # Nameserver
dig example.com TXT       # Record TXT
dig example.com AAAA      # IPv6
dig example.com SOA       # Start of Authority
dig example.com ANY       # Tutti i record (non sempre funziona)

# Usare un DNS server specifico
dig @8.8.8.8 example.com        # Google DNS
dig @1.1.1.1 example.com        # Cloudflare
dig @192.168.1.1 example.com    # DNS locale/router

# Tracciare la risoluzione dalla root
dig +trace example.com
# Mostra ogni passaggio: root → TLD → autoritativo → risposta
# Utile per trovare dove la risoluzione si rompe

# Reverse DNS lookup
dig -x 8.8.8.8

# Verificare propagazione DNSSEC
dig +dnssec example.com

# Verificare se un record è in cache
dig +norecurse @dns-server example.com
# Se risponde → è in cache
# Se NXDOMAIN/SERVFAIL → non in cache

# Confronto rapido tra DNS diversi (debug propagazione)
for dns in 8.8.8.8 1.1.1.1 9.9.9.9; do
  echo "=== $dns ==="
  dig @$dns +short example.com
done
```

### Problemi DNS Comuni

```
┌─────────────────────────────────────┬──────────────────────────────────────┐
│ Problema                            │ Diagnosi e Soluzione                 │
├─────────────────────────────────────┼──────────────────────────────────────┤
│ "Temporary failure in name          │ DNS server non raggiungibile.        │
│  resolution"                        │ → Verificare /etc/resolv.conf        │
│                                     │ → Ping al nameserver                 │
│                                     │ → dig @8.8.8.8 test.com             │
├─────────────────────────────────────┼──────────────────────────────────────┤
│ Risoluzione lenta (5+ secondi)      │ Timeout su DNS primario.             │
│                                     │ → Il primo nameserver non risponde   │
│                                     │ → Spostare DNS funzionante in cima   │
│                                     │ → IPv6 lookup timeout: options       │
│                                     │   single-request-reopen in resolv.   │
├─────────────────────────────────────┼──────────────────────────────────────┤
│ /etc/hosts ignorato                 │ nsswitch.conf: "dns" prima di        │
│                                     │ "files" nell'ordine hosts.           │
│                                     │ → Mettere "files" prima di "dns"     │
├─────────────────────────────────────┼──────────────────────────────────────┤
│ resolv.conf viene sovrascritto      │ Gestito da NetworkManager/resolved.  │
│ dopo ogni reboot                    │ → Configurare via nmcli o resolved   │
│                                     │ → Non editare resolv.conf a mano     │
├─────────────────────────────────────┼──────────────────────────────────────┤
│ Risoluzione funziona con dig ma     │ nsswitch.conf non include "dns"     │
│ non con ping/curl                   │ oppure getent non trova il risultato │
│                                     │ → Verificare nsswitch.conf           │
│                                     │ → Verificare che libnss_dns è        │
│                                     │   installato                          │
├─────────────────────────────────────┼──────────────────────────────────────┤
│ NXDOMAIN per dominio che esiste     │ Cache DNS negativa.                   │
│                                     │ → resolvectl flush-caches            │
│                                     │ → systemd-resolve --flush-caches     │
│                                     │ → Attendere TTL negativo (10 min)    │
├─────────────────────────────────────┼──────────────────────────────────────┤
│ DNS funziona via 8.8.8.8 ma non     │ DNS locale/ISP ha problemi.         │
│ con DNS predefinito                  │ → Cambiare nameserver               │
│                                     │ → Verificare firewall porta 53      │
└─────────────────────────────────────┴──────────────────────────────────────┘
```

---

## Troubleshooting Servizi (systemd)

### Analisi Journal Avanzata

```bash
# SERVIZIO NON SI AVVIA
systemctl status myservice              # Stato e ultimi log
journalctl -xeu myservice              # Log dettagliati
systemctl cat myservice                 # Configurazione unit

# Check comuni:
# 1. Il binario ExecStart esiste ed è eseguibile?
which /path/to/binary && ls -la /path/to/binary

# 2. L'utente User= esiste?
id username

# 3. Le directory WorkingDirectory= esistono?
ls -la /path/to/workdir

# 4. Le porte sono già in uso?
ss -tuln | grep PORT

# 5. I file di configurazione sono validi?
nginx -t                                # Nginx
apachectl configtest                    # Apache
named-checkconf                         # BIND
postconf -n                             # Postfix

# == Journal Analysis Avanzata ==

# Log di un servizio con timestamp
journalctl -u nginx --since "2024-01-01 00:00" --until "2024-01-01 12:00"

# Solo errori e peggio
journalctl -u myservice -p err

# Follow in tempo reale (tail -f equivalente)
journalctl -u myservice -f

# Output JSON per parsing
journalctl -u myservice -o json-pretty

# Log del boot precedente
journalctl -u myservice -b -1

# Log con contesto (mostra anche messaggi kernel correlati)
journalctl -u myservice -x

# Cercare pattern nei log
journalctl -u myservice --grep="error|fail|timeout"

# Log per un PID specifico (utile se il servizio forka)
journalctl _PID=12345

# Log per un UID specifico (tutti i processi di un utente)
journalctl _UID=1000

# Correlare log di più servizi contemporaneamente
journalctl -u nginx -u php-fpm --since "10 minutes ago"

# Esportare log per analisi esterna
journalctl -u myservice --since today > /tmp/service-debug.log
```

### Problemi di Dipendenza tra Unit

```bash
# systemd gestisce le dipendenze tra servizi (unit)
# Problemi di dipendenza causano: avvio ritardato, fallimento, deadlock

# Vedere le dipendenze di un servizio
systemctl list-dependencies myservice

# Dipendenze inverse (chi dipende da me?)
systemctl list-dependencies --reverse myservice

# Albero di boot completo
systemd-analyze critical-chain myservice
# Mostra cosa ha ritardato l'avvio del servizio

# Tempo di boot per ogni unit
systemd-analyze blame | head -20

# Grafico SVG dei tempi di boot (molto utile)
systemd-analyze plot > /tmp/boot-timeline.svg

# Tipi di dipendenza systemd:
# Requires=  → hard dependency (se fallisce → fallisco anch'io)
# Wants=     → soft dependency (se fallisce → continuo)
# After=     → ordine (aspetto che parta prima)
# Before=    → ordine (parto prima di)
# Conflicts= → non possono girare contemporaneamente
# BindsTo=   → come Requires ma si ferma se l'altro si ferma

# Problemi comuni:
# 1. Dipendenza circolare
systemd-analyze verify myservice.service
# Segnala: "Found ordering cycle"

# 2. Servizio che aspetta una dipendenza che non arriverà mai
systemctl list-jobs
# Mostra i job in corso/bloccati

# 3. Servizio che parte prima della rete
# → Aggiungere: After=network-online.target
# → E: Wants=network-online.target

# 4. Servizio che parte prima del mount di un filesystem
# → Aggiungere: RequiresMountsFor=/path/to/mountpoint
```

### Socket Activation Problems

```bash
# Socket activation: systemd ascolta su un socket e avvia il servizio
# solo quando arriva una connessione. Efficiente ma può essere confuso.

# Verificare quali socket sono attivi
systemctl list-sockets --all

# Esempio: SSH socket activation
# sshd.socket ascolta sulla porta 22
# sshd@.service viene avviato per ogni connessione

# Problemi comuni:

# 1. Servizio e socket entrambi attivi → conflitto porta
# Se sia myservice.service che myservice.socket sono enabled:
systemctl status myservice.socket
systemctl status myservice.service
# Soluzione: usare l'uno O l'altro, non entrambi
# Se si usa socket activation: disable myservice.service

# 2. Socket non accetta connessioni
systemctl status myservice.socket
# Se "failed" → verificare la configurazione:
systemctl cat myservice.socket
# [Socket]
# ListenStream=8080     # Deve corrispondere alla porta voluta
# Accept=yes            # Per servizi istanziati (@)

# 3. Socket attivo ma servizio non si avvia alla connessione
journalctl -u myservice.socket -u myservice.service
# Cercare errori nel servizio che viene attivato

# 4. Riavviare socket activation
sudo systemctl restart myservice.socket
# Non riavviare il .service, solo il .socket
```

### Servizi in Crash Loop

```bash
# SERVIZIO CHE CRASHA IN LOOP
# "Start request repeated too quickly"
# systemd ferma il servizio dopo troppi restart in poco tempo

# Vedere il rate limiting:
systemctl show myservice | grep -i limit
# StartLimitIntervalSec=10   → finestra temporale
# StartLimitBurst=5          → max restart nella finestra

# Reset dello stato "failed" per riprovare
systemctl reset-failed myservice
systemctl start myservice

# Cercare la causa del crash
journalctl -u myservice --since "10 minutes ago"  # Cercare l'errore

# Se il servizio crasha subito dopo l'avvio:
# → Avviare il binario manualmente per vedere l'errore:
/usr/bin/myservice --config /etc/myservice.conf
# → Verificare con strace:
strace -f /usr/bin/myservice --config /etc/myservice.conf 2>&1 | tail -50

# Override dei limiti (se necessario, non nascondere il problema):
sudo systemctl edit myservice
# [Service]
# StartLimitBurst=0     # Disabilita il limite (non raccomandato)
# RestartSec=5           # Attendi 5 secondi tra restart
# Restart=on-failure     # Restart solo su failure, non su exit 0

# SERVIZIO LENTO
strace -p PID -c                        # Profilo syscall
strace -p PID -e trace=network          # Problemi rete?
strace -p PID -e trace=file             # Problemi file?
```

### Timer e Scheduled Units

```bash
# I timer systemd sostituiscono cron per molti usi

# Elencare tutti i timer
systemctl list-timers --all

# Se un timer non si attiva:
# 1. È enabled?
systemctl status mytimer.timer

# 2. La unit associata esiste?
# mytimer.timer deve avere un mytimer.service corrispondente
# (o specificare Unit= nel file .timer)

# 3. Il calendario è corretto?
systemd-analyze calendar "Mon..Fri *-*-* 08:00:00"
# Verifica che l'espressione calendario è valida
# Mostra quando sarà la prossima attivazione

# 4. Attivare manualmente il servizio del timer per test
systemctl start mytimer.service    # Esegue subito

# 5. Verificare i log dell'ultima esecuzione
journalctl -u mytimer.service --since "1 day ago"
```

---

## Troubleshooting Permessi

### ACL Debugging

```bash
# "Permission denied"
ls -la /path/to/file                    # Permessi e proprietario
id                                      # Chi sono?
namei -l /path/to/file                  # Permessi lungo tutto il path

# CHECKLIST:
# 1. Permessi file (rwx)
# 2. Proprietario (user:group)
# 3. Permessi directory padre (x per attraversare)
# 4. ACL: getfacl /path/to/file
# 5. SELinux: ls -Z /path/to/file
# 6. AppArmor: aa-status
# 7. Attributi: lsattr /path/to/file

# == ACL (Access Control Lists) ==
# Le ACL estendono i permessi Unix tradizionali permettendo
# permessi granulari per utenti/gruppi specifici

# Vedere le ACL di un file
getfacl /path/to/file
# Se l'output mostra solo user::, group::, other:: → no ACL extra
# Se ci sono righe user:username: o group:groupname: → ACL attive

# Il '+' alla fine dei permessi in ls -la indica ACL
# -rw-r--r--+ 1 root root ... → il '+' indica ACL presenti

# Impostare ACL
setfacl -m u:alice:rwx /path/to/file      # Utente alice: rwx
setfacl -m g:developers:rx /path/to/file   # Gruppo: r-x

# ACL default per nuovi file in una directory
setfacl -d -m u:alice:rwx /path/to/dir    # Nuovi file ereditano ACL

# Rimuovere una ACL specifica
setfacl -x u:alice /path/to/file

# Rimuovere tutte le ACL
setfacl -b /path/to/file

# Problemi comuni ACL:
# 1. ACL troppo restrittive che nascondono permessi apparentemente OK
#    → getfacl mostra la mask: se la mask è r--, anche se user ha rwx,
#      i permessi effettivi sono r--
# 2. ACL default che sovrascrivono umask
#    → I file creati nella directory ereditano le ACL default
# 3. rsync/cp che non preservano ACL
#    → rsync -A (preserve ACL) / cp -a (preserve all)
```

### SELinux Denials

```bash
# SELinux (Security-Enhanced Linux) — usato su RHEL, Fedora, CentOS

# Verificare stato SELinux
getenforce
# Enforcing → SELinux attivo e blocca
# Permissive → SELinux registra ma non blocca
# Disabled → SELinux disabilitato

# Stato dettagliato
sestatus

# Cambiare modalità temporaneamente (non sopravvive al reboot)
sudo setenforce 0    # Permissive
sudo setenforce 1    # Enforcing

# Cambiare permanentemente: /etc/selinux/config
# SELINUX=enforcing

# == Diagnosi SELinux Denial ==

# 1. Cercare gli errori SELinux
sudo ausearch -m AVC --start recent
# oppure
sudo ausearch -m AVC -ts today

# 2. Output tipico di un denial:
# type=AVC msg=audit(1234567890.123:456): avc:  denied  { read }
# for pid=1234 comm="httpd" name="index.html"
# scontext=system_u:system_r:httpd_t:s0
# tcontext=unconfined_u:object_r:user_home_t:s0

# Traduzione:
# httpd_t (Apache) ha provato a leggere un file con contesto user_home_t
# Apache non ha il permesso di leggere file home degli utenti

# 3. Usare audit2why per spiegazione leggibile
sudo ausearch -m AVC --start recent | audit2why

# 4. Soluzioni possibili (in ordine di preferenza):

# a) Correggere il contesto del file (soluzione preferita)
sudo restorecon -Rv /path/to/file
# Ripristina il contesto SELinux corretto basandosi sulle policy

# b) Impostare un contesto specifico
sudo semanage fcontext -a -t httpd_sys_content_t "/web/content(/.*)?"
sudo restorecon -Rv /web/content

# c) Abilitare un boolean SELinux
sudo getsebool -a | grep httpd
# Se serve che Apache legga da home:
sudo setsebool -P httpd_enable_homedirs on

# d) Creare un modulo policy personalizzato (ultimo resort)
sudo ausearch -m AVC --start recent | audit2allow -M mypolicy
sudo semodule -i mypolicy.pp

# == Label comuni ==
# httpd_sys_content_t → file serviti da Apache
# var_log_t → file di log in /var/log
# tmp_t → file in /tmp
# user_home_t → file nelle home directory
```

### AppArmor Denials

```bash
# AppArmor — usato su Ubuntu, Debian, SUSE

# Stato AppArmor
sudo aa-status
# Mostra: profili in enforce, complain, unconfined

# Modalità:
# enforce → blocca e registra
# complain → solo registra (utile per debug)
# unconfined → nessuna restrizione

# == Diagnosi AppArmor Denial ==

# 1. Cercare nel log
sudo dmesg | grep -i apparmor
# oppure
journalctl -k | grep -i apparmor
# oppure
sudo grep "apparmor" /var/log/syslog

# 2. Output tipico:
# apparmor="DENIED" operation="open" profile="/usr/sbin/nginx"
# name="/data/web/index.html" pid=1234 comm="nginx"

# 3. Mettere un profilo in complain mode (permette tutto, registra)
sudo aa-complain /etc/apparmor.d/usr.sbin.nginx

# 4. Dopo aver raccolto abbastanza log, generare regole
sudo aa-logprof
# Interattivo: propone regole basate sulle denial registrate

# 5. Rimettere in enforce
sudo aa-enforce /etc/apparmor.d/usr.sbin.nginx

# == Gestione profili ==
# Ricaricare un profilo dopo modifica
sudo apparmor_parser -r /etc/apparmor.d/usr.sbin.nginx

# Disabilitare un profilo (non raccomandato in produzione)
sudo ln -s /etc/apparmor.d/usr.sbin.nginx /etc/apparmor.d/disable/
sudo apparmor_parser -R /etc/apparmor.d/usr.sbin.nginx

# Creare un profilo per un nuovo programma
sudo aa-genprof /path/to/program
# Poi eseguire il programma in un altro terminale
# Tornare a aa-genprof e fare scan per le regole
```

### Linux Capabilities

```bash
# Le capabilities suddividono i privilegi di root in unità granulari
# Un binario può avere solo le capability che servono, non il pieno root

# Vedere le capability di un file
getcap /usr/bin/ping
# /usr/bin/ping cap_net_raw=ep
# → ping ha cap_net_raw (può inviare pacchetti ICMP raw) senza essere SUID

# Elencare tutti i file con capability
sudo getcap -r / 2>/dev/null

# Impostare una capability
sudo setcap cap_net_bind_service=ep /usr/bin/myapp
# → myapp può fare bind su porte < 1024 senza essere root

# Rimuovere capability
sudo setcap -r /usr/bin/myapp

# Capability di un processo in esecuzione
cat /proc/<PID>/status | grep -i cap
# CapPrm (Permitted), CapEff (Effective), CapInh (Inherited)
# Decodificare: capsh --decode=<hex_value>

# Capability più comuni:
# cap_net_bind_service → bind porte privilegiate (<1024)
# cap_net_raw → socket raw (ping, tcpdump)
# cap_sys_admin → varie operazioni admin (mount, namespace)
# cap_dac_override → bypassa permessi file DAC (rwx)
# cap_setuid → cambiare UID
# cap_sys_ptrace → tracciare altri processi (strace, gdb)

# Problema: "Permission denied" ma il file ha permessi corretti
# e non c'è SELinux/AppArmor → verificare capability mancante
# Esempio: un webserver non riesce a fare bind su porta 80
# → serve cap_net_bind_service
```

### Problemi Permessi Comuni

```bash
# Fix comuni
sudo chown user:group file
sudo chmod 644 file                     # File: rw-r--r--
sudo chmod 755 directory                # Directory: rwxr-xr-x
sudo restorecon -Rv /path              # Ripristina contesto SELinux

# Permessi SSH troppo aperti
# "Permissions 0777 for '/home/user/.ssh/id_rsa' are too open"
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub
chmod 600 ~/.ssh/authorized_keys
chmod 600 ~/.ssh/config

# Permessi home directory
# Se altri utenti vedono i tuoi file:
chmod 750 /home/username    # Solo owner e gruppo

# File immutabili (chattr)
# Se chmod/chown non funziona:
lsattr /path/to/file
# Se mostra 'i' → file immutabile, nemmeno root può modificarlo
sudo chattr -i /path/to/file    # Rimuovere immutabilità

# Sticky bit su /tmp
# /tmp ha sticky bit (t) → un utente può cancellare solo i suoi file
ls -ld /tmp
# drwxrwxrwt → la 't' è lo sticky bit
# Se manca: sudo chmod +t /tmp
```

---

## Troubleshooting Memoria

### OOM Killer

```bash
# OOM Killer (Out-Of-Memory) — il kernel uccide processi quando la
# memoria è esaurita per evitare un crash totale del sistema.

# == Verificare se OOM Killer ha agito ==
dmesg | grep -i "out of memory\|oom"
journalctl -k | grep -i "oom"

# Output tipico:
# Out of memory: Killed process 1234 (java) total-vm:4096000kB,
# anon-rss:3500000kB, file-rss:0kB, shmem-rss:0kB, UID:1000,
# pgtables:8000kB, oom_score_adj:0

# Informazioni chiave:
# - Quale processo è stato ucciso (java)
# - Quanta memoria usava (anon-rss)
# - Il suo oom_score_adj

# == OOM Score ==
# Ogni processo ha un punteggio OOM (0-1000)
# Il processo con il punteggio più alto viene ucciso per primo

# Vedere lo score di un processo
cat /proc/<PID>/oom_score
cat /proc/<PID>/oom_score_adj    # -1000 a 1000, ajustment

# Proteggere un processo dall'OOM Killer
echo -1000 > /proc/<PID>/oom_score_adj
# -1000 = mai uccidere (usare con cautela!)

# Per un servizio systemd, aggiungere nel [Service]:
# OOMScoreAdjust=-999

# == Monitoraggio Memoria ==
# Situazione attuale
free -h
# Attenzione a "available" non a "free"
# "available" include cache riciclabile

# Dettaglio /proc/meminfo
cat /proc/meminfo | head -20
# MemTotal, MemFree, MemAvailable, Buffers, Cached, SwapTotal, SwapFree

# Processi per consumo memoria
ps aux --sort=-%mem | head -15

# Memoria per processo (dettagliata)
pmap -x <PID>
# oppure
cat /proc/<PID>/smaps_rollup

# == Tuning OOM ==
# Controllare il comportamento dell'OOM:
cat /proc/sys/vm/overcommit_memory
# 0 = euristic overcommit (default)
# 1 = always overcommit (pericoloso!)
# 2 = strict, non overcommit mai

cat /proc/sys/vm/overcommit_ratio
# Con overcommit_memory=2: memoria commit massima = RAM * ratio% + swap
# Default: 50 → commit max = RAM * 0.5 + swap

# Consiglio per server: overcommit_memory=2, overcommit_ratio=80
# Previene OOM, le applicazioni ricevono ENOMEM e possono reagire
```

### Memory Leak Detection

```bash
# Un memory leak è un processo che consuma sempre più memoria
# senza mai rilasciarla.

# 1. Identificare il sospetto
# Monitorare RSS nel tempo:
while true; do
  ps -o pid,rss,comm -p <PID> >> /tmp/memtrack.log
  sleep 60
done
# RSS che cresce costantemente = leak probabile

# 2. Analisi con /proc/<PID>/smaps
cat /proc/<PID>/smaps_rollup
# Rss:      crescita continua = leak
# Anonymous: la componente che cresce in un leak heap

# 3. Tool specifici per linguaggio:
# C/C++: valgrind --leak-check=full ./program
# Java: jmap -heap <PID>, jcmd <PID> GC.heap_info
# Python: tracemalloc, memory_profiler
# Node.js: --inspect, Chrome DevTools Memory tab

# 4. Soluzione temporanea: limitare la memoria del servizio
# In systemd unit [Service]:
# MemoryMax=2G
# MemoryHigh=1.5G  (rallenta il processo sopra questa soglia)

# 5. Con cgroups direttamente:
# cgroup v2:
echo 2G > /sys/fs/cgroup/myservice/memory.max

# 6. Monitoraggio continuo:
# Usare sar per storico
sar -r 1 5    # Report memoria ogni secondo, 5 campioni
# Usare sar storico (se sysstat è configurato):
sar -r -f /var/log/sysstat/sa$(date +%d)    # Oggi
```

### Swap Storm

```bash
# Swap storm: il sistema sposta continuamente pagine tra RAM e swap
# causando rallentamento estremo (thrashing)

# Sintomi:
# - Sistema molto lento ma non completamente fermo
# - Load average alto
# - si/so alti in vmstat
# - kswapd consuma molta CPU

# Diagnosi:
vmstat 1 10
# Colonne importanti:
# si (swap in) e so (swap out) → pagine spostate da/verso swap
# Se si/so sono costantemente > 0 → swapping attivo
# Se > 1000 → swap storm

free -h
# Se "available" è vicino a 0 e swap è in uso → troppa poca RAM

# Vedere chi usa la swap
for pid in $(ls /proc/ | grep -E '^[0-9]+$'); do
  swap=$(awk '/VmSwap/{print $2}' /proc/$pid/status 2>/dev/null)
  if [ -n "$swap" ] && [ "$swap" -gt 0 ]; then
    comm=$(cat /proc/$pid/comm 2>/dev/null)
    echo "$swap kB $pid $comm"
  fi
done | sort -n -r | head -20

# Soluzioni:

# 1. Ridurre swappiness (riduce la tendenza a swappare)
cat /proc/sys/vm/swappiness     # Default: 60
sudo sysctl vm.swappiness=10    # Server: 10 è un buon valore
# Permanente: aggiungere in /etc/sysctl.d/99-swap.conf:
# vm.swappiness=10

# 2. Aumentare RAM (soluzione vera)

# 3. Identificare e correggere il processo che consuma troppa memoria

# 4. Se necessario, aggiungere swap temporaneo
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
# Permanente: aggiungere in /etc/fstab:
# /swapfile none swap sw 0 0

# 5. Svuotare la swap (forza il ritorno in RAM — serve RAM libera!)
sudo swapoff -a && sudo swapon -a
# ATTENZIONE: funziona solo se c'è abbastanza RAM libera
```

### Hugepage Misconfiguration

```bash
# Le hugepage (2MB o 1GB invece di 4KB) migliorano la performance
# per applicazioni con grandi working set (database, JVM)

# Vedere la configurazione attuale
cat /proc/meminfo | grep -i huge
# HugePages_Total: 0        → hugepage non configurate
# HugePages_Free: 0         → disponibili
# HugePages_Rsvd: 0         → riservate
# Hugepagesize: 2048 kB     → 2MB per pagina

# Problemi comuni:

# 1. Hugepage allocate ma non usate → RAM sprecata
# HugePages_Total: 512 ma HugePages_Free: 512
# → L'applicazione non le usa. Ridurre o disabilitare.

# 2. Hugepage insufficienti → applicazione non parte
# Es. Oracle DB, PostgreSQL, JVM con hugepage
# Errore tipico: "Cannot allocate memory" per mmap con MAP_HUGETLB

# Soluzione: aumentare hugepage
sudo sysctl vm.nr_hugepages=512    # 512 * 2MB = 1GB riservato
# Permanente: /etc/sysctl.d/99-hugepages.conf
# vm.nr_hugepages=512

# 3. Transparent Huge Pages (THP) causano latenza
# THP è diverso dalle hugepage statiche
# Può causare latency spike per compaction/defragmentation
cat /sys/kernel/mm/transparent_hugepage/enabled
# [always] madvise never

# Per database (Redis, MongoDB): disabilitare THP
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag
# Permanente: creare un servizio systemd o aggiungere in rc.local

# 4. NUMA node imbalance con hugepage
# Su sistemi multi-socket, le hugepage possono essere allocate
# su un solo nodo NUMA
cat /sys/devices/system/node/node*/meminfo | grep -i huge
# Bilanciare manualmente:
echo 256 > /sys/devices/system/node/node0/hugepages/hugepages-2048kB/nr_hugepages
echo 256 > /sys/devices/system/node/node1/hugepages/hugepages-2048kB/nr_hugepages
```

---

## Troubleshooting CPU

### Load Average Alto

```bash
# Il load average rappresenta il numero medio di processi
# in stato runnable (R) o uninterruptible sleep (D)

# Leggere il load average
uptime
# load average: 4.50, 3.20, 2.10
# 1 min, 5 min, 15 min

# Interpretazione (per un sistema con N CPU):
# Load < N → CPU non satura, OK
# Load = N → CPU pienamente utilizzata, al limite
# Load > N → processi in coda, sistema sovraccarico
# Load >> N → problemi seri

# Quante CPU?
nproc    # Numero di CPU logiche

# Load alto → cosa lo causa?

# Caso 1: CPU-bound (processi in R state)
top -b -n 1 | head -20
# %Cpu: us (user) alto → processi utente consumano CPU
# %Cpu: sy (system) alto → kernel consuma CPU (syscall, interrupt)
# %Cpu: wa (iowait) basso → non è I/O
pidstat -u 1 5    # Chi usa la CPU

# Caso 2: I/O-bound (processi in D state)
# %Cpu: wa (iowait) alto → processi bloccati in attesa di I/O
# Load alto ma CPU idle alto → il load è da processi in D-state
iostat -xz 1 3    # Quale disco è saturo?
iotop              # Quali processi fanno I/O?

# Caso 3: Molti processi in coda (fork bomb, script impazzito)
ps aux | wc -l    # Contare i processi
# Se > 1000 → troppe istanze di qualcosa
ps aux | awk '{print $11}' | sort | uniq -c | sort -rn | head -10
# Mostra quante istanze di ogni comando
```

### Processi in D-State

```bash
# Lo stato D (uninterruptible sleep) indica un processo bloccato
# in attesa di I/O che non può essere interrotto (nemmeno da kill -9)

# Trovare processi in D-state
ps aux | awk '$8 ~ /D/ {print}'
# oppure
ps -eo pid,stat,comm | grep "^.*D"

# D-state è NORMALE per brevi periodi (I/O in corso)
# D-state PROLUNGATO (minuti/ore) → problema

# Cause di D-state prolungato:
# 1. Disco fisico guasto/lentissimo
# 2. NFS mount bloccato (server NFS down)
# 3. Driver storage bloccato
# 4. Deadlock nel kernel

# Diagnosi:
# Vedere cosa sta facendo il processo in D-state
cat /proc/<PID>/wchan
# Mostra la funzione kernel in cui il processo è bloccato
# Esempio: "nfs_wait_on_request" → NFS bloccato

# Stack trace del kernel per il processo
cat /proc/<PID>/stack
# Mostra l'intera call chain kernel

# Soluzione NFS bloccato:
# Il processo in D-state su NFS non può essere ucciso finché NFS non risponde
# Opzioni:
# 1. Ripristinare il server NFS
# 2. Smontare NFS forzato: umount -f /nfs/mount
# 3. Lazy unmount: umount -l /nfs/mount
# 4. Montare con opzione soft (timeout invece di blocco)
#    mount -o soft,timeo=10,retrans=3 server:/share /mnt
#    (soft fa fallire le operazioni dopo il timeout invece di bloccare)

# Se è un disco locale in D-state:
dmesg | tail -30    # Cercare errori I/O
smartctl -H /dev/sdX    # Verificare salute disco
```

### CPU Throttling

```bash
# CPU throttling: la CPU riduce la frequenza per motivi termici,
# energetici, o di configurazione.

# Verificare la frequenza attuale di ogni CPU
cat /proc/cpuinfo | grep "cpu MHz"
# oppure
lscpu | grep MHz

# Vedere la policy del governor
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
# performance → frequenza massima sempre
# powersave → frequenza minima (risparmio energetico)
# ondemand/schedutil → scala dinamicamente

# Frequenza minima e massima
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_min_freq
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq

# Impostare governor performance (tutte le CPU)
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
  echo performance | sudo tee $cpu
done

# Thermal throttling — la CPU si rallenta per calore
# Controllare temperatura:
sensors    # Richiede lm-sensors
cat /sys/class/thermal/thermal_zone*/temp
# Valore in milligradi Celsius: 85000 = 85°C

# Se la CPU è throttled per temperatura:
dmesg | grep -i "thermal\|throttl"
# "CPU: Temperature above threshold, cpu clock throttled"

# Soluzioni:
# 1. Migliorare il raffreddamento (ventole, pasta termica)
# 2. Ridurre il carico di lavoro
# 3. Aumentare il limite termico (sconsigliato, rischio hardware):
#    echo 95000 > /sys/class/thermal/thermal_zone0/trip_point_0_temp
```

### Interrupt Storm

```bash
# Interrupt storm: un dispositivo genera troppi interrupt,
# monopolizzando la CPU nella gestione degli interrupt.

# Vedere gli interrupt
cat /proc/interrupts
# Colonna per CPU, conteggio interrupt per device

# Monitorare interrupt nel tempo
watch -n 1 'cat /proc/interrupts'
# Se un contatore cresce molto rapidamente → interrupt storm

# Quale CPU gestisce quali interrupt
cat /proc/irq/*/smp_affinity_list

# Troppi interrupt da scheda di rete:
# Sintomo: softirq alto in top, CPU kernel time alto
# %Cpu: si (soft interrupt) > 30%

# Soluzioni per rete:
# 1. Abilitare interrupt coalescing (riduce frequenza interrupt)
ethtool -C eth0 rx-usecs 100 tx-usecs 100

# 2. Distribuire interrupt su più CPU (RSS: Receive Side Scaling)
# Verificare se supportato:
ethtool -l eth0

# 3. Abilitare NAPI (la maggior parte dei driver moderni lo usa già)
# NAPI alterna tra interrupt mode e polling mode
# Riduce il costo degli interrupt ad alto traffico

# Interrupt storm da disco:
# Spesso causato da disco guasto che genera errori continui
dmesg | grep -i "error\|fault\|reset"
# Soluzione: sostituire il disco guasto
```

---

## Troubleshooting Performance Avanzato

### Profiling Sistematico

```bash
# DIAGNOSI RAPIDA (60 secondi)
uptime                                  # Load average
vmstat 1 5                              # CPU, memoria, I/O
iostat -xz 1 3                          # I/O disco
free -h                                 # Memoria
ss -s                                   # Connessioni

# CPU ALTA
# Load alto + %usr alto → processo CPU-bound
pidstat -u 1 5                          # Chi usa la CPU?
# Load alto + %wa alto → I/O wait
iotop                                   # Chi fa I/O?

# MEMORIA
# "available" basso → poca memoria effettiva
# swap in uso (si > 0 in vmstat) → servono più RAM o c'è un memory leak
ps aux --sort=-%mem | head              # Top consumer
# Crescita continua della memoria di un processo = memory leak

# I/O LENTO
# %util ~100% in iostat → disco saturo
# await alto → latenza disco alta
# iotop per identificare il processo

# RETE LENTA
mtr target                              # Dove si perde tempo?
iperf3 -c server                        # Bandwidth effettiva
ethtool eth0                            # Negoziazione speed/duplex ok?
```

### perf

```bash
# perf è il profiler del kernel Linux, il più potente strumento
# di analisi performance disponibile.

# Installazione
sudo apt install linux-tools-$(uname -r)    # Debian/Ubuntu
sudo dnf install perf                         # RHEL/Fedora

# Profiling CPU: dove il sistema spende il tempo
sudo perf top
# Interfaccia interattiva simile a top ma per funzioni/simboli

# Registrare un profilo di un processo
sudo perf record -g -p <PID> -- sleep 30
# -g = include call graph (stack trace)
# sleep 30 = registra per 30 secondi

# Analizzare il profilo registrato
sudo perf report
# Navigare con frecce, Enter per espandere

# Profilo di un comando dall'inizio alla fine
sudo perf record -g ./mycommand args

# Flamegraph (visualizzazione grafica del profilo)
# 1. Registrare
sudo perf record -g -a -- sleep 30    # -a = tutto il sistema
# 2. Generare il grafico
sudo perf script | stackcollapse-perf.pl | flamegraph.pl > /tmp/flame.svg
# (richiede FlameGraph tools: https://github.com/brendangregg/FlameGraph)

# Contare eventi hardware
sudo perf stat -d ./mycommand
# Cache miss, branch misprediction, instructions per cycle

# Contare context switch
sudo perf stat -e context-switches -p <PID> -- sleep 10

# Contare page fault
sudo perf stat -e page-faults -p <PID> -- sleep 10

# Trace delle syscall (alternativa a strace, meno overhead)
sudo perf trace -p <PID>
sudo perf trace -e open,read,write -p <PID>
```

### eBPF/bpftrace

```bash
# eBPF è la tecnologia moderna per tracing/profiling del kernel Linux
# bpftrace è il tool ad alto livello per scrivere programmi eBPF

# Installazione
sudo apt install bpftrace bpfcc-tools    # Debian/Ubuntu
sudo dnf install bpftrace bcc-tools      # RHEL/Fedora

# == bpftrace one-liner utili ==

# Distribuzione latenza I/O disco
sudo bpftrace -e 'tracepoint:block:block_rq_complete {
  @us = hist(args.ns / 1000);
}'

# File aperti da un processo
sudo bpftrace -e 'tracepoint:syscalls:sys_enter_openat /pid == 1234/ {
  printf("%s\n", str(args.filename));
}'

# Contare syscall per processo
sudo bpftrace -e 'tracepoint:raw_syscalls:sys_enter {
  @[comm] = count();
}'
# Ctrl+C per terminare e vedere il conteggio

# Latenza di connessione TCP
sudo bpftrace -e 'kretprobe:tcp_v4_connect {
  @us = hist(nsecs / 1000);
}'

# == BCC tools (script pronti) ==
# Installati con bpfcc-tools, disponibili in /usr/share/bcc/tools/

# Tracing apertura file
sudo opensnoop-bpfcc

# Tracing latenza I/O
sudo biolatency-bpfcc

# Tracing latenza DNS
sudo gethostlatency-bpfcc

# Tracing connessioni TCP
sudo tcpconnect-bpfcc

# Tracing lifecycle TCP
sudo tcplife-bpfcc

# CPU profile per funzione
sudo profile-bpfcc -F 99 30    # 99 Hz per 30 secondi

# Cache hit rate
sudo cachestat-bpfcc 1         # Ogni secondo
```

### I/O Saturation

```bash
# Disco I/O saturo è una delle cause più comuni di performance degradata

# Diagnosi:
iostat -xz 1 5
# Colonne importanti:
# %util → percentuale tempo in cui il disco è occupato
#          100% = saturo (per HDD; SSD possono essere al 100% e performanti)
# r_await/w_await → latenza media in ms (alto = lento)
# avgqu-sz → profondità coda (alto = molte richieste in attesa)
# r/s, w/s → operazioni al secondo
# rMB/s, wMB/s → throughput

# Chi causa l'I/O?
sudo iotop -oa
# -o = mostra solo processi con I/O attivo
# -a = accumula (mostra totale dall'avvio di iotop)

# I/O per processo (alternativa a iotop)
pidstat -d 1 5
# kB_rd/s, kB_wr/s per processo

# Tracing I/O avanzato
sudo blktrace -d /dev/sda -o /tmp/blktrace -w 10
blkparse /tmp/blktrace.blktrace.0

# Soluzioni per I/O saturo:
# 1. Identificare e ottimizzare il processo colpevole
# 2. Spostare dati su disco più veloce (SSD)
# 3. Aggiungere caching (Redis, memcached per query DB)
# 4. Ottimizzare query database (indici, EXPLAIN ANALYZE)
# 5. I/O scheduler: per SSD usare "none" o "mq-deadline"
cat /sys/block/sda/queue/scheduler
echo mq-deadline | sudo tee /sys/block/sda/queue/scheduler
# 6. Tune read-ahead per workload sequenziale
cat /sys/block/sda/queue/read_ahead_kb
echo 256 | sudo tee /sys/block/sda/queue/read_ahead_kb
```

### Diagnosi Rapida 60 Secondi

```bash
# Netflix USE Method: per ogni risorsa, verificare
# Utilization, Saturation, Errors

# Questo script copre i 60 secondi di triage di un server

echo "=== 1. UPTIME ==="
uptime

echo "=== 2. KERNEL ERRORS ==="
dmesg -T | tail -10

echo "=== 3. VMSTAT (CPU, mem, I/O) ==="
vmstat 1 5

echo "=== 4. CPU per core ==="
mpstat -P ALL 1 3

echo "=== 5. PER-PROCESS CPU ==="
pidstat 1 3

echo "=== 6. DISK I/O ==="
iostat -xz 1 3

echo "=== 7. MEMORY ==="
free -h
echo "---"
cat /proc/meminfo | grep -E "MemTotal|MemFree|MemAvailable|Buffers|Cached|SwapTotal|SwapFree"

echo "=== 8. NETWORK ==="
sar -n DEV 1 3 2>/dev/null || ip -s link show

echo "=== 9. TCP STATS ==="
ss -s

echo "=== 10. FAILED SERVICES ==="
systemctl --failed
```

---

## Troubleshooting Package Management

### Dipendenze Rotte (APT)

```bash
# "You have held broken packages" / "Unmet dependencies"

# 1. Diagnosi
sudo apt --fix-broken install
# Tenta di risolvere automaticamente le dipendenze rotte

# 2. Se il fix automatico non funziona
sudo dpkg --configure -a
# Configura i pacchetti rimasti in stato "half-configured"

# 3. Forzare la risoluzione
sudo apt install -f
# Installa le dipendenze mancanti

# 4. Vedere i pacchetti rotti
dpkg -l | grep -E "^(iU|iF|iH|rc)"
# i = installato, U = unpacked ma non configurato
# rc = rimosso ma config ancora presente

# 5. Rimuovere un pacchetto rotto specifico
sudo dpkg --remove --force-remove-reinstreq package-name

# 6. Se tutto il resto fallisce: reinstallare il pacchetto
sudo apt download package-name
sudo dpkg -i --force-overwrite package-name*.deb
sudo apt --fix-broken install

# 7. Se il database apt è corrotto
sudo rm /var/lib/apt/lists/lock
sudo rm /var/cache/apt/archives/lock
sudo rm /var/lib/dpkg/lock
sudo rm /var/lib/dpkg/lock-frontend
sudo dpkg --configure -a
sudo apt update

# 8. Problema: "dpkg was interrupted, run dpkg --configure -a"
sudo dpkg --configure -a
# Se ci sono errori: risolvere uno alla volta

# 9. Conflitto tra versioni
apt policy package-name
# Mostra tutte le versioni disponibili e le priorità
# Installare una versione specifica:
sudo apt install package-name=versione-specifica
```

### Dipendenze Rotte (DNF/YUM)

```bash
# RHEL/Fedora: dnf gestisce le dipendenze con libsolv

# 1. Verificare problemi
sudo dnf check

# 2. Risolvere automaticamente
sudo dnf distro-sync
# Sincronizza tutti i pacchetti alle versioni del repository

# 3. Rimuovere pacchetti orfani
sudo dnf autoremove

# 4. Ricostruire il database RPM
sudo rpm --rebuilddb

# 5. Se dnf è completamente rotto
sudo dnf clean all
sudo rm -rf /var/cache/dnf/*
sudo dnf makecache

# 6. Pacchetto che non si installa per conflitto
sudo dnf install --allowerasing package-name
# Rimuove i pacchetti in conflitto (ATTENZIONE: verificare cosa rimuove)

# 7. Downgrade a versione precedente
sudo dnf downgrade package-name

# 8. History e undo
sudo dnf history
sudo dnf history info <ID>
sudo dnf history undo <ID>    # Annulla una transazione specifica
```

### Pacchetti Held/Bloccati

```bash
# I pacchetti "held" non vengono aggiornati

# == APT ==
# Vedere pacchetti held
apt-mark showhold
dpkg --get-selections | grep hold

# Mettere in hold (bloccare aggiornamenti)
sudo apt-mark hold package-name

# Rimuovere hold (sbloccare)
sudo apt-mark unhold package-name

# == DNF ==
# Vedere pacchetti esclusi
dnf list --exclude
cat /etc/dnf/dnf.conf | grep exclude

# Escludere un pacchetto da aggiornamenti
# In /etc/dnf/dnf.conf:
# exclude=package-name

# Aggiornare temporaneamente ignorando esclusioni
sudo dnf update --disableexcludes=all

# == Se un pacchetto held blocca altri aggiornamenti ==
# Esempio: "linux-image held but linux-headers depends on new version"
# Soluzioni:
# 1. Rimuovere il hold e aggiornare tutto
sudo apt-mark unhold package-name
sudo apt upgrade

# 2. Se il hold è intenzionale: aggiornare tutto tranne quello
sudo apt upgrade --ignore-hold  # Sconsigliato, può rompere
```

### Repository Problems

```bash
# "404 Not Found" durante apt update
# → Il repository è stato rimosso, spostato, o è temporaneamente down

# 1. Vedere i repository configurati
# APT:
cat /etc/apt/sources.list
ls /etc/apt/sources.list.d/

# DNF:
ls /etc/yum.repos.d/
dnf repolist --all

# 2. Disabilitare un repository problematico
# APT: commentare la riga in sources.list
# oppure rimuovere il file .list in sources.list.d/

# DNF:
sudo dnf config-manager --set-disabled repo-name

# 3. Repository con chiave GPG scaduta/mancante
# APT:
# "The following signatures couldn't be verified"
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys CHIAVE
# Metodo moderno (apt-key è deprecato):
wget -qO- https://repo.example.com/key.gpg | sudo gpg --dearmor -o /etc/apt/keyrings/repo.gpg

# DNF:
sudo rpm --import https://repo.example.com/RPM-GPG-KEY
# oppure in /etc/yum.repos.d/repo.repo:
# gpgcheck=0 (temporaneo, sconsigliato!)

# 4. Mirror lento → cambiare mirror
# Ubuntu: Software & Updates → Download from → "Other" → "Select Best Server"
# Manuale: cercare e sostituire il mirror in sources.list

# 5. PPA (Ubuntu) rotto
sudo add-apt-repository --remove ppa:user/ppa-name
```

### dpkg/rpm Corrotto

```bash
# == Database dpkg corrotto ==

# Backup del database (fare PRIMA di qualsiasi tentativo)
sudo cp -a /var/lib/dpkg /var/lib/dpkg.backup

# Verificare l'integrità
sudo dpkg --audit

# Ricostruire il database da /var/lib/dpkg/available
sudo dpkg --clear-avail
sudo apt-cache dumpavail | sudo dpkg --update-avail

# Se /var/lib/dpkg/status è corrotto:
# Il backup è in /var/lib/dpkg/status-old
sudo cp /var/lib/dpkg/status-old /var/lib/dpkg/status
sudo dpkg --configure -a
sudo apt update

# == Database RPM corrotto ==

# Backup
sudo cp -a /var/lib/rpm /var/lib/rpm.backup

# Ricostruire
sudo rpm --rebuilddb

# Verificare integrità di un pacchetto installato
rpm -V package-name
# Output: file modificati rispetto all'originale
# S = size, M = mode, 5 = MD5, T = mtime, U = user, G = group

# Reinstallare un pacchetto senza dipendenze
sudo rpm -ivh --force package.rpm
# oppure con dnf:
sudo dnf reinstall package-name
```

---

## Troubleshooting SSH

### Connection Refused

```bash
# "ssh: connect to host X port 22: Connection refused"
# → Il servizio SSH non è in ascolto sulla porta

# Diagnosi sistematica:

# 1. Il servizio SSH è in esecuzione?
systemctl status sshd
systemctl status ssh    # Ubuntu usa 'ssh' non 'sshd'

# Se non è in esecuzione:
sudo systemctl start sshd

# 2. Su quale porta è in ascolto?
ss -tuln | grep ssh
# Se non c'è → il servizio non è configurato o ha un errore
sudo sshd -t    # Test della configurazione
# Se errore: correggere /etc/ssh/sshd_config

# 3. Il firewall blocca?
sudo iptables -L -n | grep 22
sudo ufw status    # Se usa UFW
sudo firewall-cmd --list-all    # Se usa firewalld
# Aprire la porta:
sudo ufw allow ssh
# oppure
sudo firewall-cmd --add-service=ssh --permanent && sudo firewall-cmd --reload

# 4. TCP Wrappers (/etc/hosts.allow e /etc/hosts.deny)
cat /etc/hosts.deny
# Se contiene "ALL: ALL" o "sshd: ALL" → SSH bloccato
# Aggiungere in /etc/hosts.allow: sshd: IP-permesso

# 5. Da remoto: la porta è raggiungibile?
nc -zv host 22
# Se timeout → firewall di rete (non locale) blocca
```

### Key Rejected

```bash
# "Permission denied (publickey)" / "No matching key"

# 1. Verificare che la chiave pubblica sia nel server
cat ~/.ssh/authorized_keys    # Sul server

# 2. Verificare che la chiave privata corrisponda
ssh-keygen -y -f ~/.ssh/id_rsa    # Estrae la pub dalla priv
# Confrontare con la riga in authorized_keys

# 3. Permessi (causa #1 di key rejected!)
# Sul server:
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
# La home directory NON deve essere world-writable
chmod 750 /home/username
# Il proprietario deve essere corretto:
chown -R username:username ~/.ssh

# 4. SSH verbose per debug
ssh -vvv user@host
# Cercare:
# "Offering public key: ..." → quale chiave sta provando
# "Server accepts key: ..." → accettata
# "No more authentication methods to try" → tutte le chiavi rifiutate

# 5. Configurazione server (/etc/ssh/sshd_config)
# PubkeyAuthentication yes    ← deve essere yes
# AuthorizedKeysFile .ssh/authorized_keys    ← path corretto
# StrictModes yes    ← controlla permessi (lasciare yes)

# 6. SELinux contesto sbagliato
restorecon -Rv ~/.ssh/    # Ripristina contesto

# 7. Formato chiave sbagliato
# Le chiavi OpenSSH >= 8.0 usano formato diverso di default
# Se il server ha OpenSSH vecchio:
ssh-keygen -m PEM -t rsa -b 4096    # Genera in formato PEM vecchio
```

### Timeout

```bash
# "ssh: connect to host X: Connection timed out"
# → Il pacchetto SYN non riceve risposta

# Cause in ordine di probabilità:
# 1. Firewall (locale, remoto, di rete) blocca porta 22
# 2. Host non raggiungibile (routing, host down)
# 3. IP sbagliato

# Diagnosi:
# Il host è raggiungibile?
ping -c 3 host
traceroute host

# La porta è raggiungibile?
nc -zv -w 5 host 22    # Timeout 5 secondi

# == SSH keep-alive per prevenire timeout durante la sessione ==
# Client-side: ~/.ssh/config
# Host *
#   ServerAliveInterval 30
#   ServerAliveCountMax 3
# → Invia un keep-alive ogni 30s, disconnette dopo 3 mancati

# Server-side: /etc/ssh/sshd_config
# ClientAliveInterval 30
# ClientAliveCountMax 3

# == Connessione SSH lenta (login lento) ==
# Causa comune: reverse DNS lookup
# Fix server-side:
# UseDNS no    in /etc/ssh/sshd_config

# Causa: GSSAPI authentication timeout
# Fix client-side:
ssh -o GSSAPIAuthentication=no user@host
# Permanente: aggiungere in ~/.ssh/config:
# GSSAPIAuthentication no
```

### SSH Agent Problems

```bash
# L'SSH agent gestisce le chiavi private per evitare di inserire
# la passphrase ogni volta

# Verificare se l'agent è in esecuzione
echo $SSH_AUTH_SOCK
# Se vuoto → agent non in esecuzione

# Avviare l'agent
eval $(ssh-agent -s)

# Aggiungere una chiave
ssh-add ~/.ssh/id_rsa

# Elencare chiavi caricate
ssh-add -l

# Se "Could not open a connection to your authentication agent"
# → $SSH_AUTH_SOCK non punta a un socket valido
# → L'agent non è in esecuzione nel contesto corrente

# Fix: riavviare l'agent
eval $(ssh-agent -s)
ssh-add

# SSH agent forwarding (usare le chiavi locali su server remoto)
ssh -A user@jump-host
# Sul jump host: ssh-add -l mostra le chiavi locali
# ATTENZIONE: sicurezza! Chi ha root sul jump host può usare le tue chiavi
# Preferire ProxyJump:
ssh -J user@jump-host user@final-host
# Equivalente in ~/.ssh/config:
# Host final-host
#   ProxyJump jump-host
```

### SSH Tunneling

```bash
# == Local port forwarding ==
# Accedere a servizio remoto come se fosse locale
ssh -L 8080:localhost:80 user@remote
# localhost:8080 → remote:80

# == Remote port forwarding ==
# Esporre un servizio locale attraverso il server remoto
ssh -R 8080:localhost:3000 user@remote
# remote:8080 → localhost:3000

# == SOCKS proxy ==
ssh -D 1080 user@remote
# Crea un proxy SOCKS5 su localhost:1080
# Configurare browser/applicazione per usare SOCKS5 localhost:1080

# Problemi comuni tunnel SSH:

# 1. "bind: Address already in use"
# La porta locale è già in uso
ss -tuln | grep 8080
# Usare una porta diversa o uccidere il processo che occupa la porta

# 2. "channel: open failed: administratively prohibited"
# Il server non permette il forwarding
# In /etc/ssh/sshd_config: AllowTcpForwarding yes

# 3. Il tunnel si chiude dopo inattività
# Aggiungere in ~/.ssh/config:
# ServerAliveInterval 30
# Oppure:
ssh -o ServerAliveInterval=30 -L 8080:localhost:80 user@remote

# 4. Tunnel persistente con autossh
autossh -M 0 -f -N -L 8080:localhost:80 user@remote
# -M 0 = usa le opzioni ServerAlive di SSH
# -f = background
# -N = no shell, solo tunnel
```

---

## Troubleshooting Container

### Container Networking

```bash
# == Docker networking ==

# Elencare le reti Docker
docker network ls

# Ispezionare una rete
docker network inspect bridge
# Mostra: subnet, gateway, container collegati

# Il container ha connettività?
docker exec container_name ping -c 3 8.8.8.8

# Il container raggiunge altri container?
# Nella stessa rete docker:
docker exec container_name ping -c 3 other_container_name
# Il DNS interno Docker risolve i nomi dei container nella stessa rete

# DNS non funziona nel container
docker exec container_name cat /etc/resolv.conf
# Deve puntare a 127.0.0.11 (DNS interno Docker)

# Porta non raggiungibile dall'esterno
docker port container_name
# Mostra le porte mappate
# Se vuoto → il container non ha porte pubblicate
# Riavviare con: docker run -p 8080:80 image

# iptables di Docker (regole aggiunte automaticamente)
sudo iptables -t nat -L -n | grep DOCKER
sudo iptables -L DOCKER -n

# Container non raggiunge internet
# 1. Verificare IP forwarding:
cat /proc/sys/net/ipv4/ip_forward    # Deve essere 1
sudo sysctl net.ipv4.ip_forward=1

# 2. Firewall blocca bridge:
sudo iptables -A FORWARD -i docker0 -j ACCEPT
sudo iptables -A FORWARD -o docker0 -j ACCEPT

# == Podman networking ==
# Podman rootless non usa bridge: usa slirp4netns
# Conseguenze: performance rete inferiore, no ICMP, porte > 1024

# Podman: creare rete personalizzata
podman network create mynet
podman run --network mynet image
```

### Container Storage

```bash
# Spazio disco Docker
docker system df
# TYPE          TOTAL   ACTIVE  SIZE    RECLAIMABLE
# Images        15      5       8.5GB   5.2GB
# Containers    8       3       2.1GB   1.8GB
# Local Volumes 12      4       3.2GB   2.1GB
# Build Cache   -       -       1.5GB   1.5GB

# Pulizia aggressiva
docker system prune -a --volumes
# Rimuove: container fermi, immagini non usate, volumi orfani, build cache

# Volume non montato correttamente
docker inspect container_name | grep -A 10 Mounts
# Verificare: Source (host) e Destination (container) corretti
# Verificare permessi sulla Source directory

# Errore "no space left on device" dentro il container
# 1. Verificare spazio host:
df -h /var/lib/docker
# 2. Se /var/lib/docker è pieno:
docker system prune
# 3. Se il container ha un limite storage:
docker inspect container_name | grep -i storage

# Overlay2 storage driver: file corrotti
# Raro ma devastante. Se i layer sono corrotti:
# 1. Fermare Docker
sudo systemctl stop docker
# 2. Backup /var/lib/docker
# 3. Rimuovere layer corrotto (identificato dai log)
# 4. docker pull per riscaricare l'immagine
```

### Container OOM

```bash
# Docker OOM: il container supera il limite di memoria

# Verificare se un container è stato ucciso per OOM
docker inspect container_name | grep -i oom
# "OOMKilled": true → ucciso per memoria

# Vedere i limiti di memoria
docker stats container_name
# MEM USAGE / LIMIT

# Log dell'OOM nel kernel
dmesg | grep -i "oom\|killed process"
journalctl -k | grep -i "oom"

# Soluzioni:
# 1. Aumentare il limite di memoria
docker run -m 2g image    # 2 GB

# 2. Aggiungere swap al container
docker run -m 2g --memory-swap 4g image
# 2GB RAM + 2GB swap = 4GB totale

# 3. Configurare il comportamento OOM
docker run --oom-kill-disable image    # Disabilita OOM kill (PERICOLOSO)
docker run --oom-score-adj -500 image  # Meno probabilità di essere ucciso

# 4. Diagnosticare il memory leak nel container
docker exec container_name cat /proc/1/status | grep -i vm
# VmRSS: memoria residente del processo principale

# 5. Con cgroup v2, vedere i limiti:
cat /sys/fs/cgroup/system.slice/docker-<container_id>.scope/memory.max
cat /sys/fs/cgroup/system.slice/docker-<container_id>.scope/memory.current
```

### Container Image Problems

```bash
# Immagine non si scarica
docker pull image:tag
# "Error response from daemon: manifest unknown" → tag non esiste
# "Error response from daemon: unauthorized" → credenziali necessarie
docker login registry.example.com

# Immagine non si builda
docker build -t myimage .
# Errori comuni:
# 1. "COPY failed: file not found" → file non nel build context
#    → Verificare .dockerignore
# 2. "RUN apt-get update: failed" → problema DNS durante build
#    → docker build --network=host
# 3. "no space left on device" durante build
#    → docker builder prune

# Immagine troppo grande
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
# Ridurre:
# 1. Multi-stage build
# 2. Usare alpine come base
# 3. Minimizzare i layer (combinare RUN)
# 4. Aggiungere .dockerignore

# Ispezionare i layer dell'immagine
docker history image:tag
# Mostra ogni layer e la sua dimensione
# Layer grande → trovare e ottimizzare il RUN corrispondente

# Vulnerabilità nell'immagine
docker scout cves image:tag
# oppure (strumento esterno):
trivy image image:tag
```

### Docker Daemon Issues

```bash
# Il daemon Docker non si avvia

# 1. Stato e log
sudo systemctl status docker
sudo journalctl -xeu docker

# 2. Errori comuni:

# "failed to start daemon: Error initializing network controller"
# → Conflitto IP con reti Docker esistenti
# Fix: rimuovere reti orfane
sudo rm -rf /var/lib/docker/network/files/
sudo systemctl restart docker

# "failed to start daemon: ... is already running"
# → PID file rimasto da crash precedente
sudo rm /var/run/docker.pid
sudo systemctl start docker

# "no space left on device"
# → /var/lib/docker pieno
df -h /var/lib/docker
docker system prune -a

# 3. Docker daemon non risponde (hang)
sudo kill -SIGUSR1 $(pidof dockerd)
# Scrive un goroutine dump in journalctl
sudo journalctl -u docker | tail -100

# 4. Spostare /var/lib/docker su un altro disco
# Editare /etc/docker/daemon.json:
# {
#   "data-root": "/new/path/docker"
# }
sudo systemctl stop docker
sudo rsync -a /var/lib/docker/ /new/path/docker/
sudo systemctl start docker
```

---

## Troubleshooting Hardware

### SMART Monitoring

```bash
# S.M.A.R.T. (Self-Monitoring, Analysis and Reporting Technology)
# Rileva problemi nei dischi prima del guasto totale

# Installazione
sudo apt install smartmontools    # Debian/Ubuntu
sudo dnf install smartmontools    # RHEL/Fedora

# Quick health check
sudo smartctl -H /dev/sda
# "PASSED" = OK, "FAILED" = disco in fin di vita, backup immediato!

# Report completo
sudo smartctl -a /dev/sda

# Attributi SMART critici da monitorare:
# - Reallocated_Sector_Ct (ID 5) → settori riallocati, se cresce = disco morente
# - Current_Pending_Sector (ID 197) → settori in attesa di riallocazione
# - Offline_Uncorrectable (ID 198) → errori non correggibili
# - UDMA_CRC_Error_Count (ID 199) → errori cavo SATA, controllare il cavo!
# - Temperature_Celsius → temperatura del disco

# Test SMART (non distruttivi)
sudo smartctl -t short /dev/sda    # Test breve (~2 min)
sudo smartctl -t long /dev/sda     # Test completo (~ore)
# Risultati dopo il test:
sudo smartctl -l selftest /dev/sda

# Abilitare monitoraggio continuo
sudo systemctl enable smartd
sudo systemctl start smartd
# Configurazione: /etc/smartd.conf
# /dev/sda -a -o on -S on -s (S/../.././02|L/../../6/03) -m root
# → short test ogni giorno alle 2, long test sabato alle 3, email a root

# Per SSD: verificare anche
# - Wear_Leveling_Count → usura NAND
# - Media_Wearout_Indicator → vita residua
# - Total_LBAs_Written → dati scritti totali
sudo smartctl -a /dev/sda | grep -i "wear\|written"

# Per dischi NVMe
sudo smartctl -a /dev/nvme0
sudo nvme smart-log /dev/nvme0

# FILESYSTEM CORROTTO
sudo e2fsck -f /dev/sda1               # ext4 (deve essere smontato!)
sudo xfs_repair /dev/sda1              # XFS
sudo btrfs check /dev/sda1             # Btrfs

# DISCO IN READ-ONLY (remount fallito)
dmesg | tail -30                        # Errori I/O?
sudo smartctl -H /dev/sda              # Salute SMART
# Se disco guasto: backup immediato dei dati leggibili

# LVM
sudo pvs                               # Physical Volumes
sudo vgs                               # Volume Groups (spazio libero?)
sudo lvs                               # Logical Volumes

# MOUNT FALLITO
mount -v /dev/sdb1 /mnt                # Verbose per dettaglio errore
blkid /dev/sdb1                        # Tipo filesystem corretto?
```

### Errori Memoria

```bash
# Errori RAM causano: crash random, dati corrotti, kernel panic

# == mcelog (legacy, x86) ==
sudo apt install mcelog
sudo systemctl enable --now mcelog
# Log in /var/log/mcelog
# oppure:
sudo mcelog --client

# == EDAC (moderno, preferito) ==
# Error Detection and Correction
# Il kernel Linux include supporto EDAC nativo

# Verificare il sottosistema EDAC
ls /sys/devices/system/edac/mc/

# Contatori errori
cat /sys/devices/system/edac/mc/mc0/ce_count    # Correctable errors
cat /sys/devices/system/edac/mc/mc0/ue_count    # Uncorrectable errors
# ce = l'ECC ha corretto l'errore (la RAM funziona ma ha problemi)
# ue = errore non correggibile (critico, crash probabile)

# Tool edac-util
sudo apt install edac-utils
edac-util --status
edac-util --report=full

# == Test RAM con memtest86+ ==
# 1. Installare: sudo apt install memtest86+
# 2. update-grub (appare nel menu GRUB)
# 3. Riavviare e selezionare "Memory Test" dal menu GRUB
# 4. Lasciare girare per almeno 2 passaggi completi (ore)
# Un singolo errore = DIMM difettoso → sostituire

# == Identificare quale DIMM è guasta ==
sudo dmidecode -t memory | grep -A 5 "Memory Device"
# Correlare con gli errori EDAC che indicano channel e DIMM slot

# Log kernel per errori memoria
dmesg | grep -i "ecc\|memory\|mce\|hardware error"
journalctl -k | grep -i "hardware error\|mce"
```

### Monitoraggio Temperatura

```bash
# == lm-sensors ==
sudo apt install lm-sensors
sudo sensors-detect    # Rileva i sensori (rispondere YES a tutto)
sensors                # Legge le temperature

# Output tipico:
# coretemp-isa-0000
#   Core 0:        +45.0°C  (high = +80.0°C, crit = +100.0°C)
#   Core 1:        +43.0°C  (high = +80.0°C, crit = +100.0°C)

# Soglie:
# < 60°C → OK
# 60-80°C → sotto carico, normale
# 80-90°C → caldo, verificare raffreddamento
# > 90°C → critico, throttling attivo, rischio danni

# Monitorare in tempo reale
watch -n 2 sensors

# == Temperature disco ==
sudo smartctl -a /dev/sda | grep Temperature
# Dischi HDD: < 45°C ideale, < 55°C accettabile
# SSD: < 70°C generalmente OK

# == GPU (NVIDIA) ==
nvidia-smi    # Se driver NVIDIA installato
# Temperature GPU, utilizzo, memoria

# == Zone termiche del kernel ==
for zone in /sys/class/thermal/thermal_zone*; do
  echo "$(cat $zone/type): $(cat $zone/temp)m°C"
done

# == hddtemp (per dischi, se disponibile) ==
sudo hddtemp /dev/sda
```

### PCIe e USB

```bash
# == Dispositivi PCIe ==
lspci                        # Elenco dispositivi PCI
lspci -v                     # Dettagli
lspci -k                     # Con driver kernel in uso
lspci -s 01:00.0 -vvv       # Dettagli massimi per un dispositivo

# Problemi PCIe:
dmesg | grep -i "pci\|error\|link\|speed"
# "PCIe Bus Error" → slot PCIe difettoso o scheda problematica
# "lnksta: Speed" → negoziazione velocità link PCIe
# Se la velocità è inferiore a quella attesa → risiedere la scheda

# == Dispositivi USB ==
lsusb                        # Elenco dispositivi USB
lsusb -t                     # Albero con velocità
lsusb -v                     # Dettagli completi

# Problemi USB:
dmesg | grep -i usb
# "device not accepting address" → dispositivo difettoso o hub overloaded
# "cannot reset port" → problema power, provare un'altra porta
# "device descriptor read/64, error -71" → cavo difettoso

# Reset porta USB (senza scollegare)
# 1. Trovare il device
lsusb
# Bus 001 Device 005: ID 1234:5678 ...

# 2. Trovare il path sysfs
echo '1-2' | sudo tee /sys/bus/usb/drivers/usb/unbind
echo '1-2' | sudo tee /sys/bus/usb/drivers/usb/bind
# (sostituire 1-2 con il path corretto)

# Power USB
# Se un dispositivo non si accende:
cat /sys/bus/usb/devices/*/power/level
# "auto" → USB autosuspend attivo (può spegnere dispositivi)
echo on | sudo tee /sys/bus/usb/devices/1-2/power/level
```

---

## Analisi Log

### Firme di Errore Comuni

```bash
# Pattern da cercare nei log per diagnostica rapida

# == Kernel ==
dmesg -T | grep -iE "error|fail|panic|oops|bug|warn|out of memory"

# Firme critiche:
# "Kernel panic" → crash fatale, vedi sezione Kernel Panic
# "Out of memory" → OOM killer attivo
# "I/O error" → disco guasto
# "EXT4-fs error" → filesystem corrotto
# "ACPI Error" → BIOS/firmware problem (spesso innocuo)
# "CPU: Core temperature above threshold" → surriscaldamento
# "Hardware Error" → errore hardware (MCE/ECC)
# "soft lockup" → CPU bloccata per troppo tempo
# "hung_task_timeout" → task bloccato (spesso I/O)

# == Autenticazione ==
journalctl -u sshd | grep -i "failed\|invalid\|refused"
# Firme:
# "Failed password" → tentativo brute-force
# "Invalid user" → utente inesistente
# "Connection closed by authenticating user" → chiave non accettata
# "Too many authentication failures" → troppe chiavi provate

# Contare tentativi per IP
journalctl -u sshd | grep "Failed password" | awk '{print $(NF-3)}' | sort | uniq -c | sort -rn | head -10

# == Servizi ==
journalctl -p err --since "1 hour ago" --no-pager
# Firme:
# "segfault" → crash del processo (bug, corruzione memoria)
# "error binding" → porta in uso
# "permission denied" → problemi permessi
# "no such file" → file/configurazione mancante
# "timeout" → connessione o operazione troppo lenta
# "connection refused" → backend/database non raggiungibile
```

### Parsing Syslog Avanzato

```bash
# journalctl è il metodo preferito su sistemi systemd
# Ma per file di log tradizionali (/var/log/syslog, /var/log/messages):

# Cercare un pattern con contesto
grep -B 2 -A 5 "error" /var/log/syslog
# -B 2 = 2 righe prima
# -A 5 = 5 righe dopo

# Filtrare per data/ora
grep "May 22 1[0-5]:" /var/log/syslog    # Tra le 10 e le 15

# Estrarre IP da auth.log
grep "Failed password" /var/log/auth.log | \
  grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" | \
  sort | uniq -c | sort -rn | head -20

# Top 10 messaggi di errore (raggruppati)
journalctl -p err --since "1 day ago" --no-pager | \
  awk '{for(i=5;i<=NF;i++) printf "%s ",$i; print ""}' | \
  sort | uniq -c | sort -rn | head -10

# Distribuzione errori per ora
journalctl -p err --since "1 day ago" --no-pager | \
  awk '{print $3}' | cut -d: -f1 | sort | uniq -c

# Seguire più log contemporaneamente
multitail /var/log/syslog /var/log/auth.log
# oppure con journalctl:
journalctl -f -u nginx -u php-fpm -u mysql
```

### Correlazione Temporale

```bash
# Correlare eventi tra log diversi per capire la sequenza

# 1. Trovare il timestamp del problema
journalctl -u myservice | grep "error" | tail -5
# Nota il timestamp esatto

# 2. Cercare eventi correlati nello stesso periodo
journalctl --since "2024-01-15 10:30:00" --until "2024-01-15 10:35:00"

# 3. Cercare in log specifici con lo stesso intervallo
journalctl -u nginx --since "10:30" --until "10:35"
journalctl -k --since "10:30" --until "10:35"    # Kernel

# 4. Timeline completa:
# - Errore servizio alle 10:32 → cercare causa
# - dmesg alle 10:31: "I/O error dev sdb" → disco!
# - Correlazione: il disco ha avuto un errore, il servizio ha fallito
#   perché non poteva scrivere/leggere

# 5. Automatizzare la correlazione:
# Raccogliere tutti i log in un intervallo e ordinare per timestamp
journalctl --since "10:30" --until "10:35" -o short-precise --no-pager | sort -k3
```

### Log Centralizzato

```bash
# Per più server: centralizzare i log per analisi

# == journald → syslog remoto ==
# In /etc/systemd/journald.conf:
# ForwardToSyslog=yes

# rsyslog: inviare a server remoto
# In /etc/rsyslog.d/50-remote.conf:
# *.* @@logserver.example.com:514     # TCP
# *.* @logserver.example.com:514      # UDP

# == journald → journal-remote ==
# Server: systemd-journal-remote
# Client: systemd-journal-upload
# Nativo systemd, mantiene il formato journal

# == Stack ELK (Elasticsearch + Logstash + Kibana) ==
# Per ambienti enterprise. Non trattato in dettaglio qui.
# Alternativa leggera: Loki + Grafana

# == Verifica che i log arrivano ==
logger "Test log message from $(hostname)"
# Verificare sul server remoto
```

---

## Emergency Recovery

### Single User Mode

```bash
# Single user mode / rescue mode: accesso root con servizi minimi
# Utile per: reset password, riparazione filesystem, debug boot

# Come accedere:
# 1. In GRUB: premere 'e' sulla entry di boot
# 2. Trovare la riga che inizia con "linux" o "linux16"
# 3. Aggiungere alla fine: single  (o: 1, o: systemd.unit=rescue.target)
# 4. Premere Ctrl+X o F10 per avviare

# Differenze:
# single / 1           → runlevel 1, shell root, servizi minimi
# rescue.target        → systemd rescue, filesystem montati, shell root
# emergency.target     → solo /, read-only, nessun servizio
# init=/bin/bash       → shell diretta, niente systemd

# Una volta dentro:
# Rimontare in read-write se necessario:
mount -o remount,rw /

# Fare le riparazioni necessarie
# Poi: exit (o reboot)
```

### Live USB Recovery

```bash
# BOOT DA LIVE USB
# 1. Scaricare ISO live (Ubuntu Server, SystemRescue)
# 2. Creare USB avviabile: sudo dd if=image.iso of=/dev/sdX bs=4M status=progress
# 3. Boot dalla USB

# ISO raccomandate per recovery:
# - SystemRescue (specializzata per recovery)
#   https://www.system-rescue.org/
# - Ubuntu Server/Desktop live
# - Fedora live

# Creare USB avviabile (metodi):
# dd (linux):
sudo dd if=systemrescue.iso of=/dev/sdX bs=4M status=progress oflag=sync
# Ventoy (multi-ISO su una USB):
# https://www.ventoy.net/ — copia le ISO sulla USB, boot menu automatico

# Dopo il boot da live USB:

# 1. Identificare le partizioni del sistema installato
lsblk -f
# Mostra: device, filesystem, UUID, mountpoint

# 2. Se usa LVM:
sudo vgscan
sudo vgchange -ay
sudo lvs
# I logical volume appaiono in /dev/mapper/

# 3. Se usa LUKS (disco cifrato):
sudo cryptsetup luksOpen /dev/sda2 crypt_root
# Chiede la password di cifratura
# Appare /dev/mapper/crypt_root
```

### Chroot Repair Completo

```bash
# CHROOT NEL SISTEMA INSTALLATO
# Identificare le partizioni
lsblk -f

# Montare
sudo mount /dev/sda2 /mnt              # Root
sudo mount /dev/sda1 /mnt/boot/efi     # EFI (se esiste)
sudo mount --bind /dev /mnt/dev
sudo mount --bind /dev/pts /mnt/dev/pts
sudo mount --bind /proc /mnt/proc
sudo mount --bind /sys /mnt/sys
sudo mount --bind /run /mnt/run

# Se /boot è su partizione separata:
sudo mount /dev/sda3 /mnt/boot

# Per sistemi con EFI: montare anche efivars
sudo mount --bind /sys/firmware/efi/efivars /mnt/sys/firmware/efi/efivars 2>/dev/null

# DNS nel chroot (per apt/dnf):
sudo cp /etc/resolv.conf /mnt/etc/resolv.conf

# Chroot
sudo chroot /mnt /bin/bash

# Ora si è "dentro" il sistema installato
# Si possono: riparare GRUB, reinstallare pacchetti, editare configurazione,
# resettare password, rigenerare initramfs

# Operazioni comuni nel chroot:

# 1. Reinstallare GRUB
grub-install /dev/sda                      # BIOS
grub-install --target=x86_64-efi \
  --efi-directory=/boot/efi                 # UEFI
update-grub

# 2. Rigenerare initramfs
update-initramfs -u -k all                  # Debian/Ubuntu
dracut --force                               # RHEL/Fedora

# 3. Reinstallare kernel
apt install --reinstall linux-image-$(uname -r)  # Debian
dnf reinstall kernel                               # RHEL

# 4. Fix pacchetti rotti
apt --fix-broken install
dpkg --configure -a

# 5. Reset password
passwd root
passwd username

# 6. Verificare/riparare fstab
cat /etc/fstab
blkid    # Confrontare UUID

# Uscire dal chroot
exit
sudo umount -R /mnt
sudo reboot
```

### Recovery Password Root

```bash
# Metodo 1: da GRUB (il più comune)
# 1. In GRUB: premere 'e'
# 2. Alla riga linux: aggiungere init=/bin/bash
# 3. Ctrl+X per avviare
# 4. Rimontare / in read-write:
mount -o remount,rw /
# 5. Cambiare password:
passwd root
# 6. Riavviare:
/sbin/reboot -f
# oppure: exec /sbin/init

# Metodo 2: da live USB + chroot
# (vedi sezione Chroot Repair sopra)
# Nel chroot:
passwd root
passwd username

# Metodo 3: rescue mode systemd
# Boot con systemd.unit=rescue.target
# Inserire la password root corrente
# Se non si ricorda → usare metodo 1 o 2

# Se GRUB è protetto da password:
# → Boot da live USB (metodo 2) è l'unica opzione

# Dopo il reset: considerare di documentare la password
# in un password manager (non in chiaro su disco!)
```

### Recovery Dati

```bash
# Recovery dati da disco guasto o filesystem corrotto

# REGOLA #1: NON SCRIVERE sul disco guasto!
# Fare una copia bit-per-bit prima di tutto

# == Copia disco con dd/ddrescue ==
# dd (per dischi con pochi errori):
sudo dd if=/dev/sda of=/backup/disk.img bs=4M conv=noerror,sync status=progress

# ddrescue (per dischi con errori - MOLTO meglio):
sudo apt install gddrescue
sudo ddrescue -r 3 /dev/sda /backup/disk.img /tmp/rescue.log
# -r 3 = riprova 3 volte i settori falliti
# Il log permette di riprendere se interrotto

# Dopo la copia, lavorare sull'immagine (non sul disco originale!)

# == Recovery file da immagine ==

# testdisk — recupera partizioni e file
sudo apt install testdisk
sudo testdisk /backup/disk.img
# Interfaccia interattiva: Analyze → Quick Search → recupera

# photorec — recupera file per tipo (anche da partizioni formattate)
sudo photorec /backup/disk.img
# Recupera: JPG, PDF, DOC, ZIP, database, etc.
# I file recuperati perdono il nome originale

# ext4magic — specifico per ext4 (se il journal è intatto)
sudo apt install ext4magic
sudo ext4magic /dev/sda1 -r -d /recovery/output/
# Recupera file cancellati recentemente dal journal ext4

# == Montare partizione dall'immagine ==
# Trovare l'offset della partizione:
fdisk -l /backup/disk.img
# Esempio: Start=2048, sector size=512
# Offset = 2048 * 512 = 1048576
sudo mount -o loop,offset=1048576,ro /backup/disk.img /mnt
# -ro = read-only (importante!)
```

---

## Scenari di Troubleshooting

### Scenario 1: Server Non Raggiungibile via SSH

```bash
# Situazione: ssh user@server → timeout o connection refused

# 1. Il server è online?
ping -c 3 server-ip
# Se no → console IPMI/iLO/iDRAC, o accesso fisico

# 2. La porta è aperta?
nc -zv -w 3 server-ip 22
# Connection refused → SSH non in ascolto o firewall locale
# Timeout → firewall di rete o server non raggiungibile

# 3. Via console: verificare SSH
systemctl status sshd
ss -tuln | grep 22
iptables -L -n | grep 22

# 4. Firewall
ufw status
firewall-cmd --list-all

# 5. fail2ban ha bannato il tuo IP
sudo fail2ban-client status sshd
sudo fail2ban-client set sshd unbanip TUO_IP
```

### Scenario 2: Servizio Web 502 Bad Gateway

```bash
# Nginx restituisce 502 → il backend (PHP-FPM, Gunicorn, Node) non risponde

# 1. Backend è in esecuzione?
systemctl status php-fpm    # o gunicorn, node, etc.

# 2. Il socket è attivo?
ls -la /run/php/php-fpm.sock
# Se non esiste → PHP-FPM non è partito
# Permessi: www-data deve poter accedere

# 3. Log Nginx
tail -50 /var/log/nginx/error.log
# "connect() to unix:/run/php/php-fpm.sock failed (2: No such file)"
# → Socket non esiste, avviare PHP-FPM
# "connect() to unix:/run/php/php-fpm.sock failed (13: Permission denied)"
# → Permessi sbagliati sul socket

# 4. Log backend
journalctl -u php-fpm --since "10 minutes ago"
```

### Scenario 3: Disco 100% Pieno, Servizi Down

```bash
# 1. Cosa occupa spazio?
df -h
du -sh /* | sort -h | tail -10

# 2. Quick win: log enormi
sudo truncate -s 0 /var/log/syslog
sudo truncate -s 0 /var/log/kern.log

# 3. Cache pacchetti
sudo apt clean

# 4. Journal systemd
sudo journalctl --vacuum-size=200M

# 5. File cancellati ma aperti
sudo lsof +L1

# 6. Kernel vecchi
sudo apt autoremove --purge

# 7. Docker (se installato)
docker system prune -a
```

### Scenario 4: Applicazione Lenta, CPU 100%

```bash
# 1. Identificare il processo
top -b -n 1 | head -15

# 2. Cosa sta facendo?
strace -p PID -c -t 10
# oppure
perf top -p PID

# 3. Se è un processo noto (es. MySQL):
# → Verificare query lente
# → EXPLAIN su query problematiche
# → Verificare indici

# 4. Se è uno script impazzito:
# → Verificare per loop infiniti
# → Kill del processo se necessario: kill -9 PID
```

### Scenario 5: OOM Killer Uccide il Database

```bash
# 1. Confermare l'OOM
dmesg | grep -i "oom\|killed process"

# 2. Proteggere il database
echo -1000 > /proc/$(pidof postgres)/oom_score_adj
# Permanente nel systemd unit: OOMScoreAdjust=-1000

# 3. Trovare il vero consumatore di memoria
ps aux --sort=-%mem | head -10

# 4. Configurare limiti memoria per il servizio colpevole (non il DB)
# Nel systemd unit del servizio che consuma troppa memoria:
# MemoryMax=2G
```

### Scenario 6: NFS Mount Bloccato

```bash
# Processi in D-state, operazioni su /nfs-mount bloccate

# 1. Verificare connettività con il server NFS
ping nfs-server
showmount -e nfs-server

# 2. Tentare umount forzato
sudo umount -f /nfs-mount

# 3. Se umount -f fallisce (device busy):
sudo umount -l /nfs-mount    # Lazy unmount

# 4. Prevenzione: montare con soft + timeout
# In /etc/fstab:
# nfs-server:/share /mnt/nfs nfs soft,timeo=100,retrans=3 0 0
```

### Scenario 7: GRUB Non Trova il Kernel Dopo Update

```bash
# Dopo apt upgrade, GRUB non vede il nuovo kernel

# 1. Da GRUB: avviare il kernel precedente (Advanced Options)

# 2. Una volta dentro:
ls /boot/vmlinuz-*
# Il nuovo kernel è presente?

# 3. Rigenerare configurazione GRUB
sudo update-grub

# 4. Se update-grub non trova i kernel:
# Verificare che /boot è montato (se su partizione separata)
mount | grep boot
# Se non montato: mount /boot (o da fstab)
# Poi: sudo update-grub

# 5. Se /boot è pieno:
df -h /boot
sudo apt autoremove --purge    # Rimuove kernel vecchi
```

### Scenario 8: Certificato TLS Scaduto

```bash
# 1. Verificare la scadenza
echo | openssl s_client -connect host:443 2>/dev/null | openssl x509 -noout -dates
# notAfter=...  → data di scadenza

# 2. Se scaduto:
# Certbot (Let's Encrypt):
sudo certbot renew --force-renewal

# 3. Verificare il timer di rinnovo automatico
systemctl list-timers | grep certbot

# 4. Test HTTPS
curl -v https://host 2>&1 | grep -i "expire\|certificate\|SSL"
```

### Scenario 9: Swap Storm con Database

```bash
# 1. Confermare swap storm
vmstat 1 5    # si/so > 0 continuamente
free -h       # swap in uso

# 2. Per database: disabilitare swap
# (i database gestiscono la propria memoria)
# MySQL/PostgreSQL: configurare buffer pool/shared_buffers
# Redis: vm.overcommit_memory=1

# 3. Ridurre swappiness
sudo sysctl vm.swappiness=1

# 4. Liberare swap (se c'è RAM sufficiente):
sudo swapoff -a && sudo swapon -a
```

### Scenario 10: Time Drift tra Server

```bash
# 1. Verificare il tempo attuale
timedatectl
date
# "System clock synchronized: no" → problema!

# 2. Verificare NTP
chronyc tracking    # Se usa chrony
ntpq -p             # Se usa ntpd
timedatectl timesync-status    # Se usa systemd-timesyncd

# 3. Forzare sincronizzazione
sudo chronyc makestep
# oppure
sudo ntpd -gq
# oppure
sudo systemctl restart systemd-timesyncd

# 4. Verificare che il firewall permette NTP (UDP 123)
ss -uln | grep 123
```

### Scenario 11: Kernel Module Non Si Carica

```bash
# 1. Tentare il caricamento
sudo modprobe module_name
# "modprobe: FATAL: Module not found" → non installato
# "modprobe: ERROR: could not insert" → conflitto o parametri sbagliati

# 2. Verificare se è blacklistato
grep -r "module_name" /etc/modprobe.d/

# 3. Cercare il modulo
find /lib/modules/$(uname -r) -name "module_name*"

# 4. Se mancante: installare kernel-modules o driver specifico
sudo apt install linux-modules-extra-$(uname -r)
```

### Scenario 12: Processo Zombie Che Non Muore

```bash
# Zombie: processo terminato ma il parent non ha fatto wait()
ps aux | grep Z
# USER  PID  ... Z ... <defunct>

# Non si possono uccidere con kill! Sono già morti.
# Il loro parent deve fare wait().

# 1. Trovare il parent
ps -o pid,ppid,stat,comm | grep Z
# PPID = parent PID

# 2. Il parent è il problema
# Opzione A: segnalare al parent di raccogliere lo zombie
kill -SIGCHLD PPID

# Opzione B: uccidere il parent (gli zombie vengono adottati da init
# che fa automaticamente wait())
kill PPID
```

### Scenario 13: Container Docker Non Si Avvia

```bash
# 1. Log del container
docker logs container_name --tail 50

# 2. Ispezionare
docker inspect container_name | grep -A 5 "State"
# ExitCode: 137 → OOM killed
# ExitCode: 1 → errore applicazione
# ExitCode: 127 → comando non trovato
# ExitCode: 126 → permessi esecuzione

# 3. Avviare interattivamente per debug
docker run -it --entrypoint /bin/sh image_name
```

### Scenario 14: Filesystem Read-Only Improvviso

```bash
# 1. Verificare la causa
dmesg -T | tail -30
# "EXT4-fs error" → corruzione
# "I/O error" → disco guasto

# 2. SMART check
sudo smartctl -H /dev/sda

# 3. Se disco OK: tentare remount
sudo mount -o remount,rw /

# 4. Se disco guasto: backup immediato!
# Copiare tutto il possibile su un altro disco
```

### Scenario 15: Cron Job Non Si Esegue

```bash
# 1. Verificare che cron è in esecuzione
systemctl status cron    # Debian
systemctl status crond   # RHEL

# 2. Verificare la crontab
crontab -l                # Utente corrente
sudo crontab -u user -l   # Altro utente

# 3. Log di cron
journalctl -u cron --since "1 hour ago"
grep CRON /var/log/syslog

# 4. Problemi comuni:
# - PATH non impostato → usare path assoluti nello script
# - Variabili d'ambiente mancanti → impostarle nel crontab
# - Output non rediretto → aggiungere 2>&1 >> /var/log/myjob.log
# - Permessi script → chmod +x /path/to/script
# - SHELL diversa → aggiungere SHELL=/bin/bash in cima al crontab
```

### Scenario 16: Connessione Database Rifiutata

```bash
# 1. Il database è in esecuzione?
systemctl status postgresql    # o mysql, mariadb

# 2. Su quale socket/porta ascolta?
ss -tuln | grep 5432           # PostgreSQL default
ss -tuln | grep 3306           # MySQL default
# o con socket UNIX:
ls -la /var/run/postgresql/.s.PGSQL.5432
ls -la /var/run/mysqld/mysqld.sock

# 3. Configurazione accesso
# PostgreSQL: /etc/postgresql/*/main/pg_hba.conf
# MySQL: verificare bind-address in /etc/mysql/mysql.conf.d/mysqld.cnf

# 4. Firewall
sudo ufw status | grep 5432
```

### Scenario 17: Alta Latenza di Rete

```bash
# 1. Dove è la latenza?
mtr -r -c 20 target

# 2. Pacchetti persi?
ping -c 100 target | tail -3

# 3. Bandwidth test
iperf3 -c server

# 4. Interfaccia di rete: errori?
ip -s link show eth0
# RX errors, TX errors, dropped → problema cavo/switch

# 5. Buffer overflow?
cat /proc/net/snmp | grep -i "Tcp"
# RetransSegs alto → ritrasmissioni (perdita pacchetti)
```

### Scenario 18: Audit Log Pieno

```bash
# /var/log/audit/ troppo grande

# 1. Dimensione attuale
du -sh /var/log/audit/

# 2. Configurare rotazione in /etc/audit/auditd.conf:
# max_log_file = 50          # MB per file
# num_logs = 5               # File da mantenere
# max_log_file_action = ROTATE

# 3. Applicare
sudo systemctl restart auditd

# 4. Pulizia manuale (con cautela)
sudo find /var/log/audit/ -name "audit.log.*" -mtime +30 -delete
```

### Scenario 19: Segmentation Fault di un'Applicazione

```bash
# 1. Core dump abilitato?
ulimit -c
# 0 = core dump disabilitato
ulimit -c unlimited

# 2. Dove vanno i core dump?
cat /proc/sys/kernel/core_pattern
# Tipico: |/usr/share/apport/apport %p %s %c %d %P %E

# 3. Con coredumpctl (systemd)
coredumpctl list
coredumpctl info PID
coredumpctl gdb PID    # Apre gdb con il core

# 4. Debug con gdb
gdb /path/to/binary core
(gdb) bt               # Backtrace
(gdb) bt full           # Backtrace con variabili locali
```

### Scenario 20: LVM Logical Volume Pieno

```bash
# 1. Verificare spazio nel Volume Group
sudo vgs
# VFree → spazio libero nel VG

# 2. Se c'è spazio nel VG, estendere il LV
sudo lvextend -L +10G /dev/mapper/vg-lv
# oppure usa tutto lo spazio disponibile:
sudo lvextend -l +100%FREE /dev/mapper/vg-lv

# 3. Ridimensionare il filesystem
sudo resize2fs /dev/mapper/vg-lv       # ext4
sudo xfs_growfs /mount/point           # XFS (si espande solo online)

# 4. Se il VG è pieno:
# Aggiungere un disco fisico:
sudo pvcreate /dev/sdb
sudo vgextend vg /dev/sdb
# Poi estendere il LV come sopra
```

### Scenario 21: IP Conflict sulla Rete

```bash
# Sintomo: connettività intermittente, ARP warning in dmesg

# 1. Verificare
dmesg | grep -i "arp\|duplicate"
# "arp: X.X.X.X is at xx:xx:xx:xx:xx:xx on eth0 (from xx:xx:xx:xx:xx:xx)"

# 2. Trovare chi ha lo stesso IP
arping -D -I eth0 192.168.1.100
# Se risponde → conflitto!

# 3. Trovare il MAC address colpevole
arp -a | grep 192.168.1.100
# Cercare il MAC nella lista dei dispositivi DHCP del router
```

### Scenario 22: Inode Esauriti

```bash
# "No space left on device" ma df -h mostra spazio libero

# 1. Confermare
df -ih
# IUse% 100% → inode esauriti

# 2. Trovare dove sono concentrati
sudo find / -xdev -printf "%h\n" | sort | uniq -c | sort -rn | head -10

# 3. Colpevoli tipici:
# - /var/spool/mail (milioni di email)
# - /tmp (file di sessione)
# - /var/cache (cache applicazione)

# 4. Pulizia
find /path/to/problematic/dir -type f -delete
```

### Scenario 23: systemd-resolved Non Funziona

```bash
# 1. Stato
resolvectl status
systemctl status systemd-resolved

# 2. Il symlink è corretto?
ls -la /etc/resolv.conf
# Deve puntare a /run/systemd/resolve/stub-resolv.conf

# 3. Fix
sudo ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
sudo systemctl restart systemd-resolved
```

### Scenario 24: Server Lento Dopo Aggiornamento Kernel

```bash
# 1. Quale kernel è in uso?
uname -r

# 2. Confrontare con il precedente
# Avviare il kernel precedente da GRUB → funziona meglio?

# 3. Se il kernel vecchio è meglio:
# → Tenerlo come default finché il nuovo kernel non è fixato
sudo grub-set-default "Advanced options for Ubuntu>Ubuntu, with Linux X.X.X-old"
sudo update-grub

# 4. Cercare regressioni note
dmesg | grep -i "warn\|error\|firmware"
```

### Scenario 25: Connessione SSH Lenta

```bash
# 1. Debug verbose
ssh -vvv user@host 2>&1 | grep -i "auth\|dns\|gssapi"

# 2. Cause comuni e fix:
# DNS reverse lookup lento → UseDNS no in sshd_config
# GSSAPI timeout → GSSAPIAuthentication no nel client
# Troppo chiavi provate → IdentitiesOnly yes nel client config
```

### Scenario 26: Fail2ban Banna Utenti Legittimi

```bash
# 1. Verificare chi è bannato
sudo fail2ban-client status sshd

# 2. Sbannare un IP
sudo fail2ban-client set sshd unbanip 192.168.1.100

# 3. Whitelist in /etc/fail2ban/jail.local:
# [DEFAULT]
# ignoreip = 127.0.0.1/8 ::1 192.168.1.0/24

# 4. Dopo la modifica:
sudo systemctl restart fail2ban
```

### Scenario 27: Errore "Too Many Open Files"

```bash
# 1. Limiti attuali per il processo
cat /proc/<PID>/limits | grep "open files"
# Max open files → il limite

# 2. File aperti attualmente
ls /proc/<PID>/fd | wc -l

# 3. Aumentare il limite
# Per sessione: ulimit -n 65536
# Permanente in /etc/security/limits.conf:
# username  hard  nofile  65536
# username  soft  nofile  65536
# Per servizio systemd: LimitNOFILE=65536 nel [Service]

# 4. Limite globale del sistema
cat /proc/sys/fs/file-max
# Aumentare se necessario:
sudo sysctl fs.file-max=500000
```

### Scenario 28: NetworkManager vs systemd-networkd Conflitto

```bash
# Due network manager in conflitto causano: IP perso, routing rotto

# 1. Verificare cosa è attivo
systemctl status NetworkManager
systemctl status systemd-networkd

# 2. Sceglierne uno e disabilitare l'altro
# Server: systemd-networkd è preferibile
sudo systemctl disable --now NetworkManager
sudo systemctl enable --now systemd-networkd

# Desktop: NetworkManager è preferibile
sudo systemctl disable --now systemd-networkd
sudo systemctl enable --now NetworkManager
```

### Scenario 29: PostgreSQL Non Accetta Connessioni Remote

```bash
# 1. Verificare listen_addresses
sudo grep listen_addresses /etc/postgresql/*/main/postgresql.conf
# listen_addresses = 'localhost' → solo locale!
# Cambiare in: listen_addresses = '*' (o IP specifico)

# 2. Verificare pg_hba.conf
sudo grep -v "^#" /etc/postgresql/*/main/pg_hba.conf | grep -v "^$"
# Aggiungere: host all all 192.168.1.0/24 scram-sha-256

# 3. Riavviare
sudo systemctl restart postgresql

# 4. Firewall
sudo ufw allow 5432/tcp
```

### Scenario 30: Boot Loop Dopo fsck Fallito

```bash
# Il sistema tenta fsck all'avvio, fallisce, e riavvia in loop

# 1. Boot con init=/bin/bash (da GRUB, premere 'e')

# 2. Rimontare /
mount -o remount,rw /

# 3. Disabilitare fsck al boot (temporaneo!)
# In /etc/fstab: cambiare l'ultimo campo da 1/2 a 0
# Esempio: UUID=xxx / ext4 defaults 0 0
#                                       ^ questo campo

# 4. Reboot, il sistema parte

# 5. Ora fare fsck manualmente dal sistema funzionante
# (smontare il filesystem se possibile, o usare live USB)
```

### Scenario 31: Errore "Cannot Allocate Memory" ma RAM Disponibile

```bash
# Il kernel rifiuta allocazioni pur avendo RAM libera

# 1. Verificare overcommit
cat /proc/sys/vm/overcommit_memory
# 2 = strict mode, può rifiutare

# 2. Verificare committed memory
grep -i commit /proc/meminfo
# CommitLimit: massimo commit permesso
# Committed_AS: commit attuale
# Se Committed_AS > CommitLimit → nuove allocazioni rifiutate

# 3. Se overcommit_memory=2 e il commit è saturo:
# Aumentare il ratio:
sudo sysctl vm.overcommit_ratio=90
# O tornare a heuristic (default):
sudo sysctl vm.overcommit_memory=0
```

### Scenario 32: RAID Degradato

```bash
# 1. Verificare stato RAID
cat /proc/mdstat
# [UU] = OK, [U_] = degradato (un disco mancante)

# 2. Dettagli
sudo mdadm --detail /dev/md0

# 3. Sostituire il disco guasto
sudo mdadm /dev/md0 --remove /dev/sdb1
# Sostituire fisicamente il disco
sudo mdadm /dev/md0 --add /dev/sdc1
# Il rebuild inizia automaticamente
cat /proc/mdstat    # Mostra progresso rebuild
```

---

## Ambiente Rescue e Recovery

```bash
# BOOT DA LIVE USB
# 1. Scaricare ISO live (Ubuntu Server, SystemRescue)
# 2. Creare USB avviabile: sudo dd if=image.iso of=/dev/sdX bs=4M status=progress
# 3. Boot dalla USB

# CHROOT NEL SISTEMA INSTALLATO
# Identificare le partizioni
lsblk -f

# Montare
sudo mount /dev/sda2 /mnt              # Root
sudo mount /dev/sda1 /mnt/boot/efi     # EFI (se esiste)
sudo mount --bind /dev /mnt/dev
sudo mount --bind /dev/pts /mnt/dev/pts
sudo mount --bind /proc /mnt/proc
sudo mount --bind /sys /mnt/sys
sudo mount --bind /run /mnt/run

# Chroot
sudo chroot /mnt /bin/bash

# Ora si è "dentro" il sistema installato
# Si possono: riparare GRUB, reinstallare pacchetti, editare configurazione,
# resettare password, rigenerare initramfs

# Resettare password root
passwd root

# Uscire dal chroot
exit
sudo umount -R /mnt
```

---

## Guida Installazione Server Completo

### Checklist Post-Installazione

```bash
# 1. AGGIORNAMENTI
sudo apt update && sudo apt upgrade -y
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# 2. HOSTNAME E TIMEZONE
sudo hostnamectl set-hostname server-name
sudo timedatectl set-timezone Europe/Rome

# 3. UTENTE ADMIN
sudo adduser admin
sudo usermod -aG sudo admin
# Copiare chiave SSH
su - admin
mkdir ~/.ssh && chmod 700 ~/.ssh
# Aggiungere chiave pubblica in ~/.ssh/authorized_keys

# 4. SSH HARDENING
sudo vim /etc/ssh/sshd_config
# PermitRootLogin no
# PasswordAuthentication no
# PubkeyAuthentication yes
# MaxAuthTries 3
sudo systemctl restart sshd

# 5. FIREWALL
sudo apt install ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# 6. FAIL2BAN
sudo apt install fail2ban
sudo systemctl enable --now fail2ban

# 7. NTP
sudo apt install chrony
sudo systemctl enable --now chrony

# 8. MONITORING BASE
sudo apt install htop iotop sysstat
# Abilitare sysstat

# 9. LOG ROTATION
# Verificare logrotate configurato per i servizi

# 10. BACKUP
# Configurare backup automatizzato (BorgBackup/Restic)
```

---

## Guida Hardening Completo

```bash
# 1. Kernel hardening (/etc/sysctl.d/99-hardening.conf)
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.tcp_syncookies = 1
kernel.randomize_va_space = 2
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
fs.protected_hardlinks = 1
fs.protected_symlinks = 1

# 2. Rimuovere SUID non necessari
find / -perm -4000 -type f 2>/dev/null
# Valutare e rimuovere: sudo chmod u-s /path

# 3. Disabilitare servizi non necessari
systemctl list-unit-files --type=service --state=enabled
# Disabilitare tutto ciò che non serve

# 4. Limiti utente (/etc/security/limits.conf)
* hard core 0                           # No core dump

# 5. Audit
sudo apt install auditd
# Configurare regole per file sensibili

# 6. AppArmor/SELinux
# Verificare che sia in enforce mode
sudo aa-status                           # AppArmor
# getenforce                             # SELinux

# 7. Scan periodico
sudo apt install lynis
sudo lynis audit system

# 8. Aggiornamenti automatici sicurezza
# unattended-upgrades già configurato al punto 1
```

---

## Best Practices

1. **Documentare ogni intervento**: data, problema, causa, soluzione, prevenzione. Il prossimo a risolvere lo stesso problema potrebbe essere te stesso tra 6 mesi
2. **Non modificare in produzione senza backup**: prima dell'intervento: snapshot, backup config, nota del stato precedente
3. **Un cambio alla volta**: quando si diagnostica, testare una modifica alla volta. Modifiche multiple rendono impossibile capire cosa ha funzionato
4. **Leggere i log prima di agire**: il 90% dei problemi è documentato nei log. `journalctl -p err --since "1 hour ago"` è sempre il primo comando
5. **Avere un piano di rollback**: prima di ogni modifica, sapere come tornare indietro. Se il rollback non è possibile: non procedere senza approvazione
6. **Automatizzare la prevenzione**: ogni problema risolto manualmente due volte deve essere automatizzato: monitoring per rilevare, script per risolvere, alert per notificare
7. **Usare il metodo scientifico**: osservare → ipotizzare → testare → verificare. Non indovinare.
8. **Conoscere i propri strumenti**: padroneggiare i comandi diagnostici riduce il tempo di risoluzione da ore a minuti
9. **Mantenere aggiornati gli strumenti di recovery**: live USB funzionante, accesso console (IPMI/iDRAC), password di recovery documentate
10. **Non ignorare i warning**: i warning di oggi diventano gli errori di domani. Investigare e risolvere proattivamente

---

## FAQ

### Q1: Il mio sistema è lento. Da dove comincio?

```
Sequenza diagnostica dei 60 secondi:
1. uptime → load average
2. vmstat 1 5 → CPU/memoria/I/O
3. free -h → memoria disponibile
4. df -h → spazio disco
5. iostat -xz 1 3 → I/O disco
6. top/htop → processi top

Se load alto + CPU idle alto → I/O bound (disco)
Se load alto + CPU user alto → CPU bound (processo)
Se available memory basso → memoria insufficiente
Se disco pieno → liberare spazio
```

### Q2: Come faccio a sapere se il disco sta per guastarsi?

```
sudo smartctl -H /dev/sda → PASSED o FAILED
sudo smartctl -a /dev/sda → dettagli completi

Attributi critici:
- Reallocated_Sector_Ct che cresce → disco morente
- Current_Pending_Sector > 0 → problemi incipient
- UDMA_CRC_Error_Count → cavo SATA difettoso

Abilitare smartd per monitoraggio continuo.
```

### Q3: Come ripristino GRUB da live USB?

```
1. Boot da live USB
2. Montare: root, boot/efi, dev, proc, sys
3. chroot /mnt
4. grub-install /dev/sda (BIOS) o con --target=x86_64-efi (UEFI)
5. update-grub
6. exit, umount -R /mnt, reboot
Procedura dettagliata nella sezione "Chroot Repair Completo".
```

### Q4: Come trovo quale processo usa più memoria?

```bash
ps aux --sort=-%mem | head -10
# oppure
top -b -n 1 -o %MEM | head -15
# oppure per un singolo processo nel tempo:
watch -n 5 'ps -o pid,rss,vsz,comm -p PID'
```

### Q5: Come leggo i log di un servizio crashato?

```bash
journalctl -xeu service-name        # Log dettagliati con spiegazioni
journalctl -u service-name -b -1    # Log del boot precedente
journalctl -u service-name -p err   # Solo errori
```

### Q6: Il DNS non funziona ma internet va con gli IP. Cosa faccio?

```
1. ping 8.8.8.8 → OK (rete funziona)
2. dig @8.8.8.8 example.com → OK? → DNS locale rotto
3. cat /etc/resolv.conf → nameserver corretto?
4. resolvectl status → systemd-resolved funziona?
5. Fix: configurare DNS funzionante in resolved o resolv.conf
```

### Q7: Come aumento lo spazio di una partizione LVM?

```bash
# Se c'è spazio nel VG:
sudo lvextend -L +10G /dev/mapper/vg-lv
sudo resize2fs /dev/mapper/vg-lv      # ext4
sudo xfs_growfs /mount/point          # XFS
# Se il VG è pieno: aggiungere disco con pvcreate + vgextend
```

### Q8: Come faccio debug di un servizio che non si avvia?

```
1. systemctl status servizio → stato e ultimi log
2. journalctl -xeu servizio → log completi
3. systemctl cat servizio → configurazione unit
4. Verificare: binario esiste? utente esiste? directory esiste?
5. Porte in uso? ss -tuln | grep PORTA
6. Config valida? servizio -t (se supportato)
7. Avviare il binario manualmente per vedere l'errore
```

### Q9: Come resetto la password root se non la ricordo?

```
1. In GRUB: premere 'e', aggiungere init=/bin/bash alla riga linux
2. Ctrl+X per avviare
3. mount -o remount,rw /
4. passwd root
5. /sbin/reboot -f
Alternativa: boot da live USB → chroot → passwd root
```

### Q10: Come verifico se il firewall blocca il traffico?

```bash
# iptables:
sudo iptables -L -n -v | grep DROP
sudo iptables -L -n -v | grep REJECT
# Log dei drop:
sudo iptables -A INPUT -j LOG --log-prefix "FW-DROP: "
journalctl -k | grep "FW-DROP"
# UFW:
sudo ufw status verbose
# nftables:
sudo nft list ruleset
```

### Q11: Come trovo file grandi su disco?

```bash
# Top 20 file più grandi
sudo find / -xdev -type f -size +100M -exec ls -lh {} \; | sort -k5 -h
# Top 20 directory più grandi
sudo du -sh /* | sort -h | tail -20
# Interattivo:
sudo ncdu /
```

### Q12: Come monitoro le connessioni di rete in tempo reale?

```bash
# Connessioni attive:
watch -n 1 'ss -tn state established | wc -l'
# Dettaglio per processo:
ss -tulnp
# Traffico in tempo reale:
sudo iftop -i eth0
# Cattura pacchetti:
sudo tcpdump -i eth0 -nn port 80
```

### Q13: Perché un processo va in stato "D" e non risponde a kill -9?

```
D = Uninterruptible Sleep. Il processo è bloccato in una syscall kernel
(tipicamente I/O) che non può essere interrotta.
Cause: disco guasto/lento, NFS bloccato, driver bloccato.
Non si può uccidere un processo in D-state: serve risolvere il problema
I/O sottostante. Vedi sezione "Processi in D-State".
```

### Q14: Come verifico se il sistema ha subito un OOM kill?

```bash
dmesg | grep -i "oom\|killed process"
journalctl -k | grep -i "oom"
# Se presente: mostra il processo ucciso e il suo consumo memoria.
# Proteggere processi critici: OOMScoreAdjust=-1000 nel systemd unit
```

### Q15: Come faccio a far persistere una route statica dopo il reboot?

```bash
# Metodo 1: NetworkManager
sudo nmcli con mod "Connection" +ipv4.routes "10.0.0.0/8 192.168.1.1"
sudo nmcli con up "Connection"

# Metodo 2: systemd-networkd
# In /etc/systemd/network/10-static.network:
# [Route]
# Destination=10.0.0.0/8
# Gateway=192.168.1.1

# Metodo 3: netplan (Ubuntu)
# In /etc/netplan/01-config.yaml:
# routes:
#   - to: 10.0.0.0/8
#     via: 192.168.1.1
```

### Q16: Come verifico la velocità effettiva del disco?

```bash
# Test scrittura sequenziale
dd if=/dev/zero of=/tmp/test bs=1M count=1024 oflag=dsync
# Test lettura sequenziale
dd if=/tmp/test of=/dev/null bs=1M
rm /tmp/test

# Test più accurato con fio:
sudo apt install fio
fio --name=seqread --rw=read --bs=1M --size=1G --numjobs=1 --runtime=30
fio --name=randread --rw=randread --bs=4K --size=1G --numjobs=4 --runtime=30
```

### Q17: Come faccio il debug di una connessione TLS/SSL che fallisce?

```bash
# Verbose con openssl
openssl s_client -connect host:443 -showcerts
# Mostra: certificato, chain, errori

# Con curl verbose
curl -v https://host 2>&1 | grep -i "ssl\|tls\|certificate"

# Verificare certificato specifico
openssl x509 -in cert.pem -noout -text
openssl verify -CAfile ca.pem cert.pem
```

### Q18: Come gestisco un kernel panic al boot di un server remoto?

```
1. Accedere via IPMI/iLO/iDRAC (console remota)
2. Leggere il messaggio di panic dalla console
3. Se possibile: riavviare con kernel precedente (GRUB)
4. Se il disco è accessibile: kdump cattura il vmcore
5. Se il server non risponde alla console: power cycle via IPMI
```

### Q19: Perché `apt upgrade` dice "kept back" per alcuni pacchetti?

```bash
# "kept back" = il pacchetto richiede l'installazione di nuove dipendenze
# o la rimozione di pacchetti esistenti, e apt upgrade non lo fa.

# Soluzione:
sudo apt full-upgrade
# oppure installare singolarmente:
sudo apt install package-name
```

### Q20: Come faccio il boot da rete (PXE) per recovery?

```
1. Server TFTP + DHCP con opzione next-server e filename
2. Il client fa boot PXE dalla scheda di rete
3. Scarica pxelinux.0 → menu → kernel + initrd
4. Può avviare un ambiente live di recovery via rete

Configurazione minima DHCP (dnsmasq):
dhcp-boot=pxelinux.0
enable-tftp
tftp-root=/var/lib/tftpboot
```

### Q21: Il sistema è sotto attacco brute-force SSH. Cosa faccio subito?

```bash
# 1. Verificare i tentativi
journalctl -u sshd | grep "Failed password" | tail -20

# 2. Bloccare l'IP attaccante immediatamente
sudo iptables -A INPUT -s IP_ATTACCANTE -j DROP

# 3. Verificare fail2ban
sudo fail2ban-client status sshd

# 4. Hardening SSH:
# PasswordAuthentication no → solo chiavi
# MaxAuthTries 3
# PermitRootLogin no
# AllowUsers user1 user2 → whitelist

# 5. Cambiare porta SSH (security through obscurity, ma riduce il rumore)
# Port 2222 in sshd_config
```

### Q22: Come faccio a capire perché un container Docker è stato ucciso?

```bash
docker inspect container_name --format '{{.State.ExitCode}}'
# 137 = killed by signal 9 (OOM o kill manuale)
# 143 = killed by signal 15 (SIGTERM, stop normale)
# 1 = errore applicazione
# 0 = uscita normale

docker inspect container_name --format '{{.State.OOMKilled}}'
# true = ucciso per Out Of Memory

# Log degli ultimi momenti
docker logs container_name --tail 50

# Log kernel per conferma OOM
dmesg | grep -i "oom\|killed process"
```

---

## Emergency Quick Reference Card

```
╔══════════════════════════════════════════════════════════════════════╗
║                    EMERGENCY QUICK REFERENCE                        ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  ▸ SISTEMA NON BOOTA                                                ║
║    GRUB rescue → ls → set root/prefix → insmod normal → normal     ║
║    Initramfs → blkid → mount /dev/sdXN /root → exit                ║
║    Live USB → mount → chroot → grub-install → update-grub          ║
║                                                                      ║
║  ▸ FILESYSTEM READ-ONLY                                             ║
║    mount -o remount,rw /                                             ║
║    Se fallisce → dmesg | tail → smartctl -H /dev/sda               ║
║    Se disco OK → fsck da rescue mode                                 ║
║    Se disco FAILED → BACKUP IMMEDIATO                                ║
║                                                                      ║
║  ▸ DISCO 100% PIENO                                                 ║
║    1. journalctl --vacuum-size=200M                                  ║
║    2. apt clean                                                      ║
║    3. truncate -s 0 /var/log/syslog (se enorme)                      ║
║    4. find / -xdev -size +100M (file grandi)                        ║
║    5. lsof +L1 (file cancellati ma aperti)                          ║
║                                                                      ║
║  ▸ SERVIZIO NON PARTE                                                ║
║    systemctl status → journalctl -xeu → systemctl cat              ║
║    Verificare: binario, utente, directory, porta, config             ║
║                                                                      ║
║  ▸ RETE NON FUNZIONA                                                ║
║    ip link show → ip addr → ip route → ping gw → ping 8.8.8.8     ║
║    → dig → curl → iptables -L                                       ║
║                                                                      ║
║  ▸ SSH NON VA                                                        ║
║    systemctl status sshd → ss -tuln | grep 22                       ║
║    → firewall → /etc/hosts.deny → fail2ban                          ║
║    → ssh -vvv per debug client                                       ║
║                                                                      ║
║  ▸ OOM KILL                                                          ║
║    dmesg | grep -i oom → ps aux --sort=-%mem                        ║
║    Proteggere: echo -1000 > /proc/PID/oom_score_adj                  ║
║                                                                      ║
║  ▸ PASSWORD ROOT PERSA                                               ║
║    GRUB → 'e' → init=/bin/bash → Ctrl+X                            ║
║    → mount -o remount,rw / → passwd root → reboot -f                ║
║                                                                      ║
║  ▸ KERNEL PANIC                                                      ║
║    Leggere il messaggio → journalctl -b -1 -p emerg                 ║
║    Boot kernel precedente → aggiornare/rollback                      ║
║    Se hardware → memtest86+, smartctl                                ║
║                                                                      ║
║  ▸ COMANDI DI PRIMO SOCCORSO                                        ║
║    uptime | dmesg -T | tail | journalctl -p err --since "1h ago"    ║
║    systemctl --failed | df -h | free -h | ss -tuln | ps auxf       ║
║                                                                      ║
║  ▸ MAGIC SYSRQ (ultimo resort, tastiera fisica)                     ║
║    Alt+SysRq + R E I S U B                                          ║
║    R=Raw keyboard E=tErm all I=kIll all S=Sync U=Umount B=reBoot   ║
║    Mnemonico: "Reboot Even If System Utterly Broken"                ║
║    Attendere qualche secondo tra ogni tasto                          ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```
