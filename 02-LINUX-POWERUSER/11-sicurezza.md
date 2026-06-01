# Sicurezza Linux — Guida Completa

> **Modulo 11** · **Aggiornamento:** 2026-05-22

## Idee guida
1. **SELinux/AppArmor audit + rollback playbook: develop policy in permissive mode.**
2. **seccomp profile generation: `oci-seccomp-bpf-hook` o manual.**
3. **lynis + aide + osquery: hooks per compliance scan.**
4. **CIS Benchmark Debian/RHEL: 200+ controls.**
5. **Defense in depth: ogni layer compensa le debolezze degli altri.**
6. **Zero Trust: non fidarsi mai, verificare sempre — anche dentro il perimetro.**


## Indice

- [Panoramica](#panoramica)
- [Modello di Sicurezza Linux](#modello-di-sicurezza-linux)
  - [DAC — Discretionary Access Control](#dac--discretionary-access-control)
  - [MAC — Mandatory Access Control](#mac--mandatory-access-control)
  - [Linux Capabilities](#linux-capabilities)
  - [Seccomp](#seccomp)
  - [Namespaces](#namespaces)
  - [Cgroups e sicurezza](#cgroups-e-sicurezza)
- [Hardening Linux: Checklist](#hardening-linux-checklist)
- [Autenticazione Utente e PAM](#autenticazione-utente-e-pam)
  - [Struttura dello stack PAM](#struttura-dello-stack-pam)
  - [Deep Dive nei moduli PAM](#deep-dive-nei-moduli-pam)
  - [Password Policy](#password-policy)
  - [Account Locking con faillock](#account-locking-con-faillock)
  - [MFA con PAM](#mfa-con-pam)
- [sudo: Configurazione Avanzata](#sudo-configurazione-avanzata)
- [Sicurezza del Filesystem](#sicurezza-del-filesystem)
  - [Permessi tradizionali](#permessi-tradizionali)
  - [ACL — Access Control Lists](#acl--access-control-lists)
  - [Attributi estesi e flag immutabile](#attributi-estesi-e-flag-immutabile)
  - [Crittografia filesystem: LUKS](#crittografia-filesystem-luks)
  - [eCryptfs — Crittografia a livello directory](#ecryptfs--crittografia-a-livello-directory)
- [GPG — Crittografia File](#gpg--crittografia-file)
- [SELinux — Guida Operativa](#selinux--guida-operativa)
  - [Architettura e componenti](#architettura-e-componenti)
  - [Modalita](#modalita)
  - [Contesti e Label](#contesti-e-label)
  - [Boolean e Policy](#boolean-e-policy)
  - [Porte SELinux](#porte-selinux)
  - [Troubleshooting SELinux avanzato](#troubleshooting-selinux-avanzato)
  - [Scrivere policy SELinux custom](#scrivere-policy-selinux-custom)
- [AppArmor — Guida Operativa](#apparmor--guida-operativa)
  - [Architettura AppArmor](#architettura-apparmor)
  - [Gestione Profili](#gestione-profili)
  - [Creare Profili](#creare-profili)
  - [Profili avanzati](#profili-avanzati)
  - [Log e troubleshooting AppArmor](#log-e-troubleshooting-apparmor)
- [Kernel Hardening](#kernel-hardening)
  - [Parametri sysctl di sicurezza](#parametri-sysctl-di-sicurezza)
  - [Kernel Lockdown](#kernel-lockdown)
  - [Firma dei moduli kernel](#firma-dei-moduli-kernel)
  - [Hardening del boot](#hardening-del-boot)
- [Architettura Firewall](#architettura-firewall)
  - [iptables — Regole avanzate](#iptables--regole-avanzate)
  - [nftables — Il successore di iptables](#nftables--il-successore-di-iptables)
  - [Firewall zone-based](#firewall-zone-based)
  - [Firewall application-level](#firewall-application-level)
- [Sicurezza di Rete](#sicurezza-di-rete)
  - [Connection tracking avanzato](#connection-tracking-avanzato)
  - [Rate limiting e anti-DDoS](#rate-limiting-e-anti-ddos)
  - [Difesa da port scanning](#difesa-da-port-scanning)
  - [Network segmentation](#network-segmentation)
- [SSH Hardening](#ssh-hardening)
- [Audit Framework (auditd)](#audit-framework-auditd)
  - [Configurazione auditd](#configurazione-auditd)
  - [Regole di audit](#regole-di-audit)
  - [Query e report](#query-e-report)
  - [Audit per compliance](#audit-per-compliance)
- [Intrusion Detection](#intrusion-detection)
  - [AIDE — File Integrity Monitoring](#aide--file-integrity-monitoring)
  - [OSSEC e Wazuh](#ossec-e-wazuh)
  - [chkrootkit e rkhunter](#chkrootkit-e-rkhunter)
- [Log Monitoring per la Sicurezza](#log-monitoring-per-la-sicurezza)
  - [rsyslog e syslog-ng](#rsyslog-e-syslog-ng)
  - [Pattern sospetti da monitorare](#pattern-sospetti-da-monitorare)
  - [Centralizzazione dei log](#centralizzazione-dei-log)
- [Vulnerability Management](#vulnerability-management)
  - [Lynis — Audit di sicurezza](#lynis--audit-di-sicurezza)
  - [OpenVAS / Greenbone](#openvas--greenbone)
  - [Nessus](#nessus)
  - [CVE Monitoring e patching](#cve-monitoring-e-patching)
- [Sicurezza dei Container](#sicurezza-dei-container)
  - [Docker hardening](#docker-hardening)
  - [Podman — Rootless containers](#podman--rootless-containers)
  - [Image scanning](#image-scanning)
  - [Runtime protection](#runtime-protection)
- [Rootkit Detection e Forensics](#rootkit-detection-e-forensics)
- [fail2ban](#fail2ban)
- [Incident Response Workflow](#incident-response-workflow)
- [CIS Benchmarks — Implementazione](#cis-benchmarks--implementazione)
  - [CIS Level 1 — Ubuntu](#cis-level-1--ubuntu)
  - [CIS Level 2 — Ubuntu](#cis-level-2--ubuntu)
  - [CIS Level 1 — RHEL](#cis-level-1--rhel)
  - [CIS Level 2 — RHEL](#cis-level-2--rhel)
- [Security Hardening Checklist Pre-Deployment](#security-hardening-checklist-pre-deployment)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Best Practices](#best-practices)

---

## Panoramica

La sicurezza Linux è un approccio multilivello: dal hardening del sistema operativo (ridurre la superficie d'attacco) ai MAC (Mandatory Access Control con SELinux/AppArmor), dall'autenticazione (PAM, sudo) all'audit (auditd), dalla crittografia (LUKS, GPG) al monitoraggio (fail2ban, scanning). Non esiste una singola misura che renda un sistema sicuro — la sicurezza è la somma di molte pratiche applicate con disciplina.

Il modello di sicurezza Linux opera su più strati concentrici:

```
┌─────────────────────────────────────────────┐
│              Sicurezza Fisica               │
├─────────────────────────────────────────────┤
│         Boot Security (UEFI/GRUB)           │
├─────────────────────────────────────────────┤
│      Kernel Hardening (sysctl, lockdown)    │
├─────────────────────────────────────────────┤
│    MAC (SELinux / AppArmor / seccomp)       │
├─────────────────────────────────────────────┤
│     DAC (permessi, ACL, capabilities)       │
├─────────────────────────────────────────────┤
│   Autenticazione (PAM, sudo, MFA)          │
├─────────────────────────────────────────────┤
│     Rete (firewall, IDS, segmentazione)     │
├─────────────────────────────────────────────┤
│   Crittografia (LUKS, GPG, TLS)            │
├─────────────────────────────────────────────┤
│   Audit & Monitoring (auditd, SIEM, log)   │
├─────────────────────────────────────────────┤
│   Incident Response & Forensics            │
└─────────────────────────────────────────────┘
```

Ogni strato compensa le debolezze di quello superiore. Un attaccante che supera il firewall trova SELinux; se bypassa SELinux, trova le capabilities limitate; se ottiene accesso, trova auditd che registra ogni sua mossa.

---

## Modello di Sicurezza Linux

### DAC — Discretionary Access Control

Il DAC è il modello di sicurezza tradizionale di Unix/Linux. Il proprietario di un file decide chi può accedervi tramite permessi (owner, group, others) e ACL. Il problema fondamentale del DAC: un processo compromesso eredita tutti i permessi dell'utente che lo esegue.

```bash
# Il modello DAC si basa su tre entità:
# 1. Proprietario (user)    — chi possiede il file
# 2. Gruppo (group)         — gruppo associato al file
# 3. Altri (others)         — tutti gli altri utenti

# Permessi: r (read=4), w (write=2), x (execute=1)
# Per directory: r=list, w=create/delete, x=cd/traverse

# Permessi speciali:
# SUID (4000)  — il processo esegue con i permessi del proprietario del file
# SGID (2000)  — il processo esegue con il gruppo del file (su dir: ereditarietà)
# Sticky (1000) — su dir: solo il proprietario può cancellare i propri file

# Esempio critico: SUID su /usr/bin/passwd
ls -l /usr/bin/passwd
# -rwsr-xr-x 1 root root ... /usr/bin/passwd
# La 's' in posizione user-execute indica SUID
# passwd gira come root per poter scrivere /etc/shadow

# Rischio SUID: se il binario ha una vulnerabilità, l'attaccante ottiene root
# Audit periodico obbligatorio:
find / -perm -4000 -type f -exec ls -la {} \; 2>/dev/null
find / -perm -2000 -type f -exec ls -la {} \; 2>/dev/null

# Limitazione del DAC: un browser compromesso ha accesso a TUTTO
# ciò che l'utente può leggere ($HOME, .ssh, .gnupg, ecc.)
# Soluzione: MAC (SELinux, AppArmor) per confinare i processi
```

### MAC — Mandatory Access Control

Il MAC supera i limiti del DAC imponendo policy di sicurezza a livello kernel che nemmeno root può bypassare (a meno di disabilitare il sistema MAC stesso). Le due implementazioni principali su Linux sono SELinux e AppArmor.

```bash
# Differenza fondamentale DAC vs MAC:
#
# DAC: "L'utente root può fare tutto"
# MAC: "Anche root è soggetto alla policy. httpd_t può accedere solo a
#        httpd_sys_content_t, indipendentemente dai permessi DAC"

# DAC + MAC lavorano insieme: ENTRAMBI devono permettere l'accesso.
# Se DAC dice OK ma MAC dice NO → accesso negato
# Se MAC dice OK ma DAC dice NO → accesso negato

# SELinux (label-based): ogni oggetto ha un contesto di sicurezza
# user_u:role_r:type_t:level
# La policy definisce quali tipi possono interagire

# AppArmor (path-based): profili definiscono percorsi consentiti
# /usr/sbin/nginx { /var/www/** r, /var/log/nginx/** w, }

# LSM (Linux Security Modules): framework kernel che supporta entrambi
# SELinux e AppArmor sono implementati come LSM
# Solo un LSM maggiore può essere attivo alla volta
cat /sys/kernel/security/lsm
# Output tipico: lockdown,capability,landlock,yama,apparmor
```

### Linux Capabilities

Le capabilities frammentano i poteri di root in unità granulari. Anziché dare un binario SUID root (tutti i poteri), si assegnano solo le capability necessarie.

```bash
# Lista delle capability più importanti:
# CAP_NET_BIND_SERVICE  — bind a porte < 1024
# CAP_NET_RAW           — socket raw (ping, tcpdump)
# CAP_NET_ADMIN         — configurazione rete (iptables, route)
# CAP_SYS_ADMIN         — mount, swap, sethostname (troppo ampia, evitare)
# CAP_SYS_PTRACE        — debug di processi di altri utenti
# CAP_DAC_OVERRIDE      — bypass permessi DAC (lettura/scrittura)
# CAP_DAC_READ_SEARCH   — bypass controllo lettura file e directory
# CAP_SETUID            — cambiare UID
# CAP_SETGID            — cambiare GID
# CAP_CHOWN             — cambiare owner dei file
# CAP_KILL              — inviare segnali a processi di altri utenti
# CAP_SYS_BOOT          — reboot
# CAP_SYS_TIME          — modificare clock di sistema
# CAP_AUDIT_WRITE       — scrivere nel log di audit
# CAP_SYS_MODULE        — caricare/scaricare moduli kernel

# Verificare le capability di un file
getcap /usr/bin/ping
# /usr/bin/ping cap_net_raw=ep

# Assegnare capability (alternativa a SUID)
# Permetti a un web server non-root di ascoltare sulla porta 80
sudo setcap 'cap_net_bind_service=+ep' /usr/local/bin/mywebserver

# Rimuovere capability
sudo setcap -r /usr/local/bin/mywebserver

# Verificare capability di un processo in esecuzione
cat /proc/$(pgrep nginx)/status | grep Cap
# CapInh: capability ereditabili
# CapPrm: capability permesse (pool disponibile)
# CapEff: capability effettive (attualmente in uso)
# CapBnd: bounding set (limite massimo)
# CapAmb: capability ambientali

# Decodificare il valore esadecimale
capsh --decode=0000003fffffffff

# Thread capability: ogni thread ha il proprio set
# Effective ⊆ Permitted ⊆ Bounding
# Un processo può ridurre le proprie capability ma non aumentarle

# Esempio pratico: eliminare SUID da ping
sudo chmod u-s /usr/bin/ping
sudo setcap cap_net_raw+ep /usr/bin/ping
# Ora ping funziona senza SUID, con solo la capability necessaria

# Capability e container: Docker di default rimuove le capability pericolose
# docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE myapp
```

### Seccomp

Seccomp (Secure Computing Mode) filtra le syscall che un processo può eseguire. Riduce drasticamente la superficie d'attacco: se un processo non ha bisogno di `mount()`, `ptrace()` o `reboot()`, seccomp le blocca.

```bash
# Due modalità:
# 1. seccomp strict: solo read(), write(), _exit(), sigreturn()
# 2. seccomp-bpf: filtro personalizzabile con BPF (Berkeley Packet Filter)

# Verificare se seccomp è abilitato nel kernel
grep CONFIG_SECCOMP /boot/config-$(uname -r)
# CONFIG_SECCOMP=y
# CONFIG_SECCOMP_FILTER=y

# Verificare seccomp di un processo
grep Seccomp /proc/$(pgrep -f nginx)/status
# Seccomp:     2    → seccomp-bpf attivo
# Seccomp:     0    → seccomp non attivo
# Seccomp_filters: 1 → numero di filtri applicati

# Seccomp e Docker/Podman:
# Il profilo seccomp di default blocca ~44 syscall pericolose
# tra cui: mount, reboot, swapon, kexec_load, init_module
docker run --security-opt seccomp=unconfined myimage  # PERICOLOSO
docker run --security-opt seccomp=custom.json myimage  # Profilo custom

# Generare profilo seccomp automaticamente con oci-seccomp-bpf-hook:
# 1. Eseguire il container con hook attivo
# 2. Il hook registra le syscall usate
# 3. Genera un profilo JSON minimo

# Profilo seccomp JSON (esempio minimo)
# {
#   "defaultAction": "SCMP_ACT_ERRNO",
#   "architectures": ["SCMP_ARCH_X86_64"],
#   "syscalls": [
#     {
#       "names": ["read","write","open","close","stat","fstat",
#                 "mmap","mprotect","munmap","brk","exit_group"],
#       "action": "SCMP_ACT_ALLOW"
#     }
#   ]
# }

# Programmaticamente in C con libseccomp:
# scmp_filter_ctx ctx = seccomp_init(SCMP_ACT_KILL);
# seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(read), 0);
# seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(write), 0);
# seccomp_load(ctx);

# strace per identificare le syscall usate da un processo:
strace -c -f -S name /usr/bin/myapp 2>&1 | tail -20
# Produce la lista delle syscall usate → base per il profilo seccomp
```

### Namespaces

I Linux namespaces isolano le risorse di sistema, permettendo a un processo di avere una visione limitata del sistema. Fondamentali per i container, ma utilizzabili anche per sandbox di sicurezza.

```bash
# Tipi di namespace:
# PID namespace   — isolamento albero processi (PID 1 proprio)
# NET namespace   — stack di rete isolato (interfacce, routing, iptables)
# MNT namespace   — mount point isolati
# UTS namespace   — hostname e domainname isolati
# IPC namespace   — IPC isolato (shared memory, semafori)
# USER namespace  — UID/GID mapping (root nel namespace ≠ root nell'host)
# CGROUP namespace — vista isolata della gerarchia cgroup
# TIME namespace  — clock isolato (dal kernel 5.6)

# Verificare i namespace di un processo
ls -la /proc/$$/ns/
# lrwxrwxrwx 1 user user 0 ... cgroup -> 'cgroup:[4026531835]'
# lrwxrwxrwx 1 user user 0 ... ipc -> 'ipc:[4026531839]'
# lrwxrwxrwx 1 user user 0 ... mnt -> 'mnt:[4026531841]'
# ...

# Creare un namespace di rete isolato
sudo ip netns add sandbox
sudo ip netns exec sandbox ip link list
# → Vede solo interfaccia lo

# Eseguire un processo con namespace isolati (senza root):
unshare --user --pid --fork --mount-proc bash
# Ora si è "root" nel namespace utente ma non sull'host
id        # uid=0(root) — ma solo nel namespace
cat /proc/1/status | grep NSpid
# NSpid: <host-pid> 1

# USER namespace: la chiave per i rootless container
# Un utente non privilegiato può creare un namespace dove è root
# Ma le operazioni sono limitate al namespace
# Requisito kernel: /proc/sys/kernel/unprivileged_userns_clone = 1

# Sicurezza dei namespace:
# I namespace NON sono una barriera di sicurezza forte da soli
# Devono essere combinati con seccomp, capabilities e MAC
# Un processo con CAP_SYS_ADMIN può uscire da molti namespace
```

### Cgroups e sicurezza

I control groups (cgroups) limitano, contabilizzano e isolano le risorse hardware (CPU, memoria, I/O, rete) dei processi. Dal punto di vista della sicurezza, prevengono il resource exhaustion (DoS).

```bash
# cgroups v2 (unificato, default su kernel moderni)
# Montato su /sys/fs/cgroup/

# Verificare la versione
stat -fc %T /sys/fs/cgroup/
# cgroup2fs → v2
# tmpfs     → v1

# Limiti di sicurezza con cgroups v2
# Prevenire fork bomb:
echo 100 > /sys/fs/cgroup/user.slice/user-1000.slice/pids.max

# Limitare memoria per un servizio (via systemd):
sudo systemctl set-property myapp.service MemoryMax=512M
sudo systemctl set-property myapp.service MemoryHigh=400M

# Limitare CPU:
sudo systemctl set-property myapp.service CPUQuota=50%

# Limitare I/O:
sudo systemctl set-property myapp.service IOReadBandwidthMax="/dev/sda 10M"

# systemd integra cgroups nativamente:
# Ogni servizio ha il suo cgroup: /sys/fs/cgroup/system.slice/myapp.service/
# Ogni sessione utente: /sys/fs/cgroup/user.slice/user-1000.slice/

# Verificare i limiti di un cgroup:
cat /sys/fs/cgroup/system.slice/nginx.service/memory.max
cat /sys/fs/cgroup/system.slice/nginx.service/pids.max

# Uso sicurezza: prevenire DoS
# Un processo compromesso non può:
# - Consumare tutta la RAM (MemoryMax)
# - Creare migliaia di processi (pids.max)
# - Saturare il disco I/O (IOReadBandwidthMax)
# - Monopolizzare la CPU (CPUQuota)

# Configurazione via unit file systemd:
# [Service]
# MemoryMax=512M
# MemoryHigh=400M
# CPUQuota=50%
# TasksMax=100
# IPAddressDeny=any
# IPAddressAllow=10.0.0.0/8
```

---

## Hardening Linux: Checklist

### Post-Installazione

```bash
# 1. AGGIORNAMENTI
sudo apt update && sudo apt upgrade -y
sudo apt install unattended-upgrades   # Aggiornamenti sicurezza automatici
sudo dpkg-reconfigure -plow unattended-upgrades

# 2. UTENTI
# Disabilitare login root diretto
sudo passwd -l root                    # Blocca password root

# Rimuovere utenti non necessari
# Verificare /etc/passwd per utenti di servizio non usati

# 3. SERVIZI
# Disabilitare servizi non necessari
systemctl list-unit-files --type=service --state=enabled
sudo systemctl disable --now cups      # Esempio: stampa non necessaria su server
sudo systemctl disable --now avahi-daemon

# 4. PORTE
ss -tuln                               # Verificare porte in ascolto
# Ogni porta aperta è una superficie d'attacco potenziale

# 5. PERMESSI FILE
# File sensibili
chmod 600 /etc/shadow
chmod 644 /etc/passwd
chmod 600 /etc/ssh/sshd_config

# Cercare file con SUID/SGID
find / -perm -4000 -type f 2>/dev/null   # SUID
find / -perm -2000 -type f 2>/dev/null   # SGID
# Rimuovere SUID non necessari:
sudo chmod u-s /path/to/unnecessary/suid/binary

# 6. SYSCTL SICUREZZA
# /etc/sysctl.d/99-security.conf
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

# 7. BANNER
# /etc/issue e /etc/issue.net — rimuovere info sulla distribuzione
echo "Authorized access only. All activities are monitored." | sudo tee /etc/issue
```

### Hardening addizionale

```bash
# 8. RIMOZIONE COMPILATORI (su server di produzione)
sudo apt remove --purge gcc g++ make
# Impedisce a un attaccante di compilare exploit direttamente sul server

# 9. MOUNT SICURO — opzioni restrittive in /etc/fstab
# /tmp con noexec, nosuid, nodev:
# tmpfs  /tmp  tmpfs  defaults,noexec,nosuid,nodev,size=2G  0  0
# /var/tmp:
# /tmp   /var/tmp  none  bind  0  0
# oppure mount separato con stesse restrizioni

# Rimontare /tmp immediatamente:
sudo mount -o remount,noexec,nosuid,nodev /tmp

# 10. DISABILITARE PROTOCOLLI NON NECESSARI
# /etc/modprobe.d/disable-uncommon-protocols.conf
cat <<'EOF' | sudo tee /etc/modprobe.d/disable-uncommon-protocols.conf
install dccp /bin/true
install sctp /bin/true
install rds /bin/true
install tipc /bin/true
install cramfs /bin/true
install freevxfs /bin/true
install jffs2 /bin/true
install hfs /bin/true
install hfsplus /bin/true
install udf /bin/true
EOF

# 11. CORE DUMP — disabilitare per sicurezza
# /etc/security/limits.conf
# * hard core 0
echo "* hard core 0" | sudo tee -a /etc/security/limits.conf
# /etc/sysctl.d/99-security.conf
# fs.suid_dumpable = 0

# 12. CONTROLLO USB (server headless)
# /etc/modprobe.d/disable-usb-storage.conf
echo "install usb-storage /bin/true" | sudo tee /etc/modprobe.d/disable-usb-storage.conf
```

---

## Autenticazione Utente e PAM

PAM (Pluggable Authentication Modules) gestisce l'autenticazione, l'autorizzazione, la gestione sessione e la gestione password per tutti i servizi Linux. Comprendere PAM in profondità è essenziale per hardening e troubleshooting.

### Struttura dello stack PAM

```bash
# File di configurazione
/etc/pam.d/                         # Un file per servizio
/etc/pam.d/common-auth              # Autenticazione comune
/etc/pam.d/common-password          # Policy password
/etc/pam.d/common-session           # Gestione sessione
/etc/pam.d/common-account           # Verifica account
/etc/pam.d/sshd                     # Configurazione SSH
/etc/pam.d/login                    # Login console
/etc/pam.d/sudo                     # sudo

# Formato riga:
# tipo   controllo   modulo   [argomenti]
# auth   required    pam_unix.so

# TIPI DI MODULO:
# auth      — verifica identità (password, token, biometria)
# account   — verifica autorizzazione (account scaduto? bloccato? orario OK?)
# password  — gestione cambio password (quality, history)
# session   — setup/teardown sessione (variabili ambiente, limiti, log)

# CONTROLLI:
# required    — DEVE avere successo, ma continua a valutare gli altri moduli
#               (non rivela quale modulo ha fallito)
# requisite   — DEVE avere successo, FALLISCE IMMEDIATAMENTE se no
# sufficient  — se ha successo E nessun required precedente fallito → OK, stop
# optional    — il risultato importa solo se è l'unico modulo per quel tipo
# include     — include un altro file di configurazione PAM
# substack    — come include, ma il fallimento non propaga al chiamante

# ORDINE DI VALUTAZIONE:
# PAM processa i moduli dall'alto verso il basso
# L'ordine è CRITICO — un modulo sbagliato in posizione sbagliata
# può bloccare tutti i login o (peggio) bypassare l'autenticazione
```

### Deep Dive nei moduli PAM

```bash
# pam_unix.so — Autenticazione tradizionale Unix
# Verifica password contro /etc/shadow
# Argomenti comuni:
#   nullok       — permette password vuota (PERICOLOSO)
#   try_first_pass — usa la password già inserita prima di chiederne un'altra
#   sha512       — usa SHA-512 per hashing (default moderno)
#   remember=N   — ricorda le ultime N password (impedisce riutilizzo)
#   use_authtok  — usa la password già validata dal modulo precedente

# pam_faillock.so — Lockout dopo tentativi falliti
# Sostituto moderno di pam_tally2 (deprecato)
# Argomenti:
#   preauth     — fase pre-autenticazione (controlla se già bloccato)
#   authfail    — fase post-autenticazione (registra il fallimento)
#   authsucc    — fase post-autenticazione (registra il successo)
#   deny=N      — blocca dopo N tentativi falliti
#   unlock_time=N — sblocca dopo N secondi (0 = sblocco solo manuale)
#   fail_interval=N — finestra temporale per contare i fallimenti
#   even_deny_root — blocca anche root (usare con cautela)

# pam_pwquality.so — Controllo qualità password
# Verifica complessità, dizionario, somiglianza con password precedente
# Argomenti:
#   minlen=N    — lunghezza minima
#   dcredit=-N  — almeno N cifre (valore negativo = minimo richiesto)
#   ucredit=-N  — almeno N maiuscole
#   lcredit=-N  — almeno N minuscole
#   ocredit=-N  — almeno N caratteri speciali
#   difok=N     — N caratteri diversi dalla password precedente
#   maxrepeat=N — max caratteri consecutivi ripetuti
#   gecoscheck  — verifica che la password non contenga parole dal campo GECOS
#   dictcheck   — verifica contro dizionario (cracklib)
#   usercheck   — verifica che non contenga il nome utente

# pam_limits.so — Limiti di risorse per sessione
# Applica /etc/security/limits.conf
# Tipi: soft (avviso), hard (limite)
# Risorse: nofile, nproc, memlock, cpu, fsize, core, stack

# pam_access.so — Controllo accesso basato su origine
# Usa /etc/security/access.conf
# Formato: +|- : utente/gruppo : origine
# + : root : LOCAL
# - : ALL : ALL EXCEPT LOCAL 10.0.0.0/8

# pam_time.so — Restrizioni orarie
# Usa /etc/security/time.conf
# Formato: servizio;ttys;utenti;orari
# login ; * ; !admin ; Al0800-1800
# → login consentito solo tra 8:00 e 18:00 tranne admin

# pam_env.so — Impostazione variabili d'ambiente
# Usa /etc/security/pam_env.conf
# Imposta variabili in modo sicuro al login

# pam_nologin.so — Blocco login non-root
# Se esiste /etc/nologin, solo root può fare login
# Usato per manutenzione di emergenza
sudo touch /etc/nologin         # Blocca tutti tranne root
sudo rm /etc/nologin            # Riabilita login
```

### Password Policy

```bash
# /etc/security/pwquality.conf
minlen = 12                         # Lunghezza minima
difok = 4                           # Caratteri diversi dalla password precedente
ucredit = -1                        # Almeno 1 maiuscola
lcredit = -1                        # Almeno 1 minuscola
dcredit = -1                        # Almeno 1 cifra
ocredit = -1                        # Almeno 1 carattere speciale
maxrepeat = 3                       # Max caratteri ripetuti consecutivi
maxclassrepeat = 4                  # Max caratteri consecutivi della stessa classe

# Password aging (/etc/login.defs)
PASS_MAX_DAYS   90                  # Scadenza ogni 90 giorni
PASS_MIN_DAYS   7                   # Min giorni tra cambi
PASS_WARN_AGE   14                  # Avviso 14 giorni prima

# Per utente specifico
sudo chage -M 90 -m 7 -W 14 username
chage -l username                   # Visualizza policy utente

# Forzare cambio password al prossimo login
sudo chage -d 0 username

# Disabilitare un account (non eliminarlo)
sudo usermod -L username            # Blocca password
sudo usermod -e 1 username          # Scadenza immediata

# Verificare password deboli (con john)
sudo cat /etc/shadow > /tmp/shadow_audit
john --wordlist=/usr/share/wordlists/rockyou.txt /tmp/shadow_audit
shred -u /tmp/shadow_audit          # Distruggi il file dopo l'audit

# /etc/login.defs — parametri aggiuntivi
ENCRYPT_METHOD SHA512               # Algoritmo di hashing
SHA_CRYPT_MIN_ROUNDS 5000           # Minimo round di hashing
SHA_CRYPT_MAX_ROUNDS 10000          # Massimo round di hashing
LOGIN_RETRIES 3                     # Tentativi di login
LOGIN_TIMEOUT 60                    # Timeout in secondi
UMASK 027                           # Umask default per nuovi utenti
USERGROUPS_ENAB yes                 # Crea gruppo personale per ogni utente
```

### Account Locking con faillock

```bash
# Configurazione completa faillock
# /etc/pam.d/common-auth (Debian/Ubuntu)
auth    required    pam_faillock.so preauth deny=5 unlock_time=900 fail_interval=900
auth    [success=1 default=ignore] pam_unix.so nullok
auth    [default=die] pam_faillock.so authfail deny=5 unlock_time=900 fail_interval=900
auth    requisite   pam_deny.so
auth    required    pam_permit.so

# /etc/pam.d/common-account
account required pam_faillock.so

# Gestione faillock
faillock --user username             # Mostra fallimenti
faillock --user username --reset     # Reset contatore (sblocca)
faillock                             # Mostra tutti gli utenti

# Configurazione alternativa via file (RHEL 8+)
# /etc/security/faillock.conf
# deny = 5
# unlock_time = 900
# fail_interval = 900
# even_deny_root
# root_unlock_time = 60
# dir = /var/run/faillock
# audit
# silent

# ATTENZIONE: even_deny_root blocca anche root dopo N tentativi
# Impostare root_unlock_time basso o avere accesso fisico/console
```

### MFA con PAM

```bash
# Google Authenticator (TOTP)
sudo apt install libpam-google-authenticator

# Configurare per l'utente
google-authenticator
# → Scansiona QR con app TOTP (Google Authenticator, Authy, FreeOTP)
# → Salva i codici di emergenza in modo sicuro

# /etc/pam.d/sshd — aggiungere PRIMA di pam_unix:
auth required pam_google_authenticator.so nullok
# nullok: utenti senza TOTP configurato possono accedere con sola password
# RIMUOVERE nullok dopo che tutti gli utenti hanno configurato TOTP

# /etc/ssh/sshd_config
ChallengeResponseAuthentication yes
AuthenticationMethods publickey,keyboard-interactive
# → Richiede CHIAVE SSH + TOTP (massima sicurezza)
# Alternativa:
# AuthenticationMethods keyboard-interactive
# → Richiede PASSWORD + TOTP

# PAM U2F (chiave hardware FIDO2/U2F)
sudo apt install libpam-u2f
# Registrare la chiave:
pamu2fcfg > ~/.config/Yubico/u2f_keys
# /etc/pam.d/sudo — aggiungere:
auth required pam_u2f.so
# → sudo richiede la chiave hardware fisica
```

---

## sudo: Configurazione Avanzata

```bash
# Modificare sudoers (SEMPRE con visudo)
sudo visudo                         # Apre con verifica sintassi
sudo visudo -f /etc/sudoers.d/custom  # File drop-in

# Sintassi: chi  dove=(come_chi)  cosa
# user  ALL=(ALL:ALL)  ALL         → user può fare tutto
# user  ALL=(ALL)  NOPASSWD: ALL   → Senza password (NON consigliato)

# ESEMPI PRATICI
# Gruppo admin con tutti i permessi
%sudo   ALL=(ALL:ALL) ALL

# Utente deploy può riavviare nginx senza password
deploy  ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx, /usr/bin/systemctl reload nginx

# Utente monitor può solo leggere log
monitor ALL=(ALL) NOPASSWD: /usr/bin/journalctl, /usr/bin/cat /var/log/*

# Alias per raggruppare
Cmnd_Alias NETWORKING = /usr/sbin/iptables, /usr/sbin/ip, /usr/bin/ss
User_Alias NETADMINS = alice, bob
NETADMINS ALL=(ALL) NETWORKING

# SICUREZZA
Defaults    env_reset               # Reset variabili d'ambiente
Defaults    secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Defaults    use_pty                 # Esegui in pseudo-terminale
Defaults    logfile="/var/log/sudo.log"  # Log dedicato
Defaults    log_input, log_output   # Log input e output dei comandi
Defaults    timestamp_timeout=5     # Timeout password (minuti)
Defaults    passwd_tries=3          # Max tentativi password

# HARDENING AVANZATO
Defaults    requiretty              # Richiede TTY (previene automazione non interattiva)
Defaults    env_reset               # Non propagare variabili ambiente pericolose
Defaults    mail_badpass            # Notifica email su password errata
Defaults    mailto="admin@example.com"
Defaults    !visiblepw              # Non mostrare password se il terminale lo consente

# Impedire escape via editor
Defaults    noexec                  # Default: previeni esecuzione di sottocomandi
# Override per comandi specifici che devono lanciare sotto-processi:
deploy ALL=(ALL) EXEC: /usr/bin/systemctl restart nginx

# AUDIT: chi ha fatto cosa con sudo
sudo journalctl _COMM=sudo          # Log systemd
cat /var/log/sudo.log                # Log dedicato (se configurato)
```

---

## Sicurezza del Filesystem

### Permessi tradizionali

```bash
# UMASK — maschera di default per nuovi file/directory
# File: 666 - umask = permessi risultanti
# Dir:  777 - umask = permessi risultanti
# umask 022 → file 644, dir 755 (default Debian)
# umask 027 → file 640, dir 750 (più restrittivo)
# umask 077 → file 600, dir 700 (massima restrizione)

# Impostare umask per tutto il sistema
# /etc/login.defs: UMASK 027
# /etc/profile.d/umask.sh: umask 027

# Permessi critici per file di sistema
chmod 644 /etc/passwd           # Leggibile da tutti (necessario per resolver nomi)
chmod 000 /etc/shadow           # Solo root (spesso 640 con gruppo shadow)
chmod 640 /etc/shadow           # root:shadow
chmod 600 /etc/gshadow
chmod 644 /etc/group
chmod 600 /boot/grub/grub.cfg   # Impedisce lettura config di boot
chmod 700 /root                 # Home di root solo per root
chmod 600 /etc/ssh/sshd_config
chmod 600 /etc/ssh/ssh_host_*_key     # Chiavi private SSH host
chmod 644 /etc/ssh/ssh_host_*_key.pub # Chiavi pubbliche SSH host
chmod 600 /etc/crontab
chmod 700 /etc/cron.d
chmod 700 /etc/cron.daily
chmod 700 /etc/cron.hourly
chmod 700 /etc/cron.monthly
chmod 700 /etc/cron.weekly

# Trovare file e directory world-writable (pericolosi)
find / -xdev -type f -perm -0002 -exec ls -la {} \; 2>/dev/null
find / -xdev -type d -perm -0002 ! -perm -1000 -exec ls -la {} \; 2>/dev/null
# La seconda esclude directory con sticky bit (/tmp)

# Trovare file senza proprietario (potenziale compromissione)
find / -xdev -nouser -o -nogroup 2>/dev/null
```

### ACL — Access Control Lists

```bash
# Le ACL estendono il modello DAC tradizionale con permessi granulari
# per utenti e gruppi specifici, oltre al classico owner/group/others

# Prerequisiti: filesystem montato con opzione acl (default su ext4, xfs)
# Verificare: mount | grep acl

# Installare tool ACL
sudo apt install acl

# Visualizzare ACL
getfacl /srv/shared/docs/

# Aggiungere ACL per utente specifico
setfacl -m u:alice:rwx /srv/shared/docs/
setfacl -m u:bob:r-- /srv/shared/docs/

# Aggiungere ACL per gruppo
setfacl -m g:developers:rwx /srv/shared/docs/

# ACL di default (applicata automaticamente ai nuovi file nella directory)
setfacl -d -m u:alice:rwx /srv/shared/docs/
setfacl -d -m g:developers:rwx /srv/shared/docs/

# Rimuovere ACL specifico
setfacl -x u:alice /srv/shared/docs/

# Rimuovere TUTTE le ACL
setfacl -b /srv/shared/docs/

# ACL ricorsivo
setfacl -R -m g:developers:rwx /srv/shared/docs/

# Copiare ACL da un file all'altro
getfacl file1 | setfacl --set-file=- file2

# MASK: limita i permessi massimi per ACL
setfacl -m m::rx /srv/shared/docs/
# Tutti i permessi ACL sono mascherati: anche se alice ha rwx, l'effettivo è rx

# Backup e restore delle ACL (prima di operazioni bulk)
getfacl -R /srv/shared/ > /backup/acl_backup.txt
setfacl --restore=/backup/acl_backup.txt

# Nota: ls -l mostra '+' alla fine dei permessi se ci sono ACL
# -rwxrwx---+ 1 root developers ... file.txt
```

### Attributi estesi e flag immutabile

```bash
# Attributi estesi (xattr) aggiungono metadati ai file
# Usati da SELinux (security.selinux), capability (security.capability), ACL

# Visualizzare attributi estesi
getfattr -d -m- /path/to/file

# Attributi di file con chattr/lsattr
lsattr /etc/passwd
# ----i--------e-- /etc/passwd  → 'i' = immutabile

# FLAG IMPORTANTI:
# i  immutabile: non può essere modificato, cancellato, rinominato, linkato
#    nemmeno da root (richiede CAP_LINUX_IMMUTABLE per rimuovere)
# a  append-only: si può solo aggiungere in coda (perfetto per log)
# s  secure delete: il contenuto viene sovrascritto con zeri alla cancellazione
# u  undeletable: il contenuto è salvato per poter essere recuperato
# A  no atime update: non aggiorna il timestamp di accesso (performance)

# Rendere un file immutabile (protezione estrema)
sudo chattr +i /etc/passwd
sudo chattr +i /etc/shadow
sudo chattr +i /etc/group
sudo chattr +i /etc/gshadow
sudo chattr +i /etc/sudoers

# Per modificare il file: prima rimuovere il flag
sudo chattr -i /etc/passwd
# Modificare...
sudo chattr +i /etc/passwd

# Log in append-only (l'attaccante non può cancellare i log precedenti)
sudo chattr +a /var/log/auth.log
sudo chattr +a /var/log/syslog

# Verificare
lsattr /etc/passwd /etc/shadow /var/log/auth.log

# ATTENZIONE: chattr +i impedisce anche gli aggiornamenti del sistema
# Non usare su file che il package manager deve modificare
```

### Crittografia filesystem: LUKS

LUKS (Linux Unified Key Setup) è lo standard per la crittografia dei dischi su Linux.

```bash
# Creare partizione criptata
sudo cryptsetup luksFormat /dev/sdb1
# → Conferma con YES
# → Inserisci passphrase

# Aprire (decriptare)
sudo cryptsetup luksOpen /dev/sdb1 crypt_data
# Il dispositivo decriptato appare come /dev/mapper/crypt_data

# Creare filesystem e montare
sudo mkfs.ext4 /dev/mapper/crypt_data
sudo mount /dev/mapper/crypt_data /mnt/secure

# Chiudere
sudo umount /mnt/secure
sudo cryptsetup luksClose crypt_data

# Gestione chiavi
sudo cryptsetup luksDump /dev/sdb1                    # Info
sudo cryptsetup luksAddKey /dev/sdb1                   # Aggiungi chiave
sudo cryptsetup luksRemoveKey /dev/sdb1                # Rimuovi chiave
sudo cryptsetup luksChangeKey /dev/sdb1                # Cambia chiave

# Mount automatico al boot (con keyfile)
sudo dd if=/dev/urandom of=/root/.luks-keyfile bs=4096 count=1
sudo chmod 400 /root/.luks-keyfile
sudo cryptsetup luksAddKey /dev/sdb1 /root/.luks-keyfile

# /etc/crypttab
# crypt_data  UUID=xxxx  /root/.luks-keyfile  luks

# /etc/fstab
# /dev/mapper/crypt_data  /mnt/secure  ext4  defaults  0  2

# PARAMETRI DI SICUREZZA AVANZATI
# Specificare cifrario e dimensione chiave:
sudo cryptsetup luksFormat --cipher aes-xts-plain64 --key-size 512 \
  --hash sha512 --iter-time 5000 /dev/sdb1
# aes-xts-plain64: cifrario standard per FDE
# key-size 512: 256-bit AES-XTS (512 = 256 per encryption + 256 per tweak)
# iter-time 5000: millisecondi per derivazione chiave (più alto = più lento brute force)

# Backup header LUKS (CRITICO — senza header, dati persi per sempre)
sudo cryptsetup luksHeaderBackup /dev/sdb1 --header-backup-file /backup/sdb1-luks-header.bak
# Conservare il backup in luogo sicuro separato dal disco criptato

# Restore header:
sudo cryptsetup luksHeaderRestore /dev/sdb1 --header-backup-file /backup/sdb1-luks-header.bak

# Verificare stato del volume
sudo cryptsetup status crypt_data

# Benchmark cifrati disponibili
sudo cryptsetup benchmark
```

### eCryptfs — Crittografia a livello directory

```bash
# eCryptfs cripta singole directory anziché interi dischi
# Utile per crittografare $HOME senza LUKS sull'intero disco

# Installare
sudo apt install ecryptfs-utils

# Crittografare la home di un utente (fare logout dell'utente prima)
sudo ecryptfs-migrate-home -u username

# Login dell'utente → la home è automaticamente decriptata
# Logout → la home torna criptata

# Mount manuale di una directory criptata
sudo mount -t ecryptfs /srv/secret /srv/secret
# → Chiede passphrase e parametri di cifratura

# Creazione directory privata per utente corrente
ecryptfs-setup-private
# Crea ~/Private — montata automaticamente al login, smontata al logout

# Salvare la passphrase di wrapping:
ecryptfs-unwrap-passphrase
# SALVARE QUESTA PASSPHRASE! Senza di essa i dati sono irrecuperabili

# Nota: eCryptfs è considerato legacy
# Per nuove installazioni valutare:
# - LUKS per full disk encryption
# - fscrypt (nativo ext4/f2fs) per crittografia a livello directory
# - gocryptfs per directory criptate FUSE-based
```

---

## GPG — Crittografia File

```bash
# Generare chiave
gpg --full-generate-key             # Interattivo (scegliere RSA 4096 o ed25519)
gpg --list-keys                     # Lista chiavi
gpg --list-secret-keys              # Lista chiavi private

# Esportare
gpg --export -a "User Name" > public.key
gpg --export-secret-keys -a "User Name" > private.key

# Importare
gpg --import public.key

# Crittografare file
gpg -c file.txt                     # Crittografia simmetrica (passphrase)
gpg -e -r "Recipient Name" file.txt # Crittografia asimmetrica (chiave pubblica)
gpg -se -r "Recipient" file.txt     # Cripta + firma

# Decrittografare
gpg -d file.txt.gpg > file.txt
gpg file.txt.gpg                    # Auto-detect

# Firmare
gpg --sign file.txt                 # Firma (comprime)
gpg --clearsign file.txt            # Firma leggibile
gpg --detach-sign file.txt          # Firma separata (.sig)
gpg --verify file.txt.sig file.txt  # Verifica firma

# BEST PRACTICE GPG
# Usare sottochiavi (subkeys): la chiave master resta offline
gpg --edit-key "User Name"
# → addkey → selezionare tipo e scopo (sign, encrypt, auth)

# Esportare solo le sottochiavi (chiave master NON sul sistema in uso)
gpg --export-secret-subkeys -a "User Name" > subkeys.gpg

# Revocare chiave compromessa
gpg --gen-revoke "User Name" > revocation.asc
# Conservare il certificato di revoca offline
# In caso di compromissione:
gpg --import revocation.asc
gpg --keyserver keyserver.ubuntu.com --send-keys KEY_ID

# Crittografia di directory (con tar)
tar czf - /path/to/dir | gpg -c -o backup-encrypted.tar.gz.gpg
# Decrittografare:
gpg -d backup-encrypted.tar.gz.gpg | tar xzf -
```

---

## SELinux — Guida Operativa

SELinux (Security-Enhanced Linux) è un sistema MAC (Mandatory Access Control) sviluppato da NSA. Implementa il principio del minimo privilegio: ogni processo ha accesso solo alle risorse esplicitamente autorizzate dalla policy. Usato di default su RHEL, Fedora, CentOS.

### Architettura e componenti

```bash
# Componenti principali SELinux:
#
# 1. Policy — regole che definiscono gli accessi consentiti
#    - targeted: confina i demoni, il resto è unconfined (default RHEL)
#    - strict: confina TUTTO il sistema (raro, molto restrittivo)
#    - mls: Multi-Level Security (classificato/segreto — ambienti militari)
#
# 2. AVC (Access Vector Cache) — cache delle decisioni di accesso
#    Le violazioni producono messaggi "avc: denied" nei log
#
# 3. Security Server — componente kernel che valuta le regole
#
# 4. Object Manager — controlla l'accesso agli oggetti (file, porte, processi)
#
# 5. Policy database — compilato da .te (type enforcement), .if (interface),
#    .fc (file context) → modulo .pp

# Contesto di sicurezza: user:role:type:level
# Esempio: system_u:system_r:httpd_t:s0
#
# user   → identità SELinux (diversa da Unix user)
# role   → ruolo (server: system_r, utente: unconfined_r)
# type   → tipo (campo più importante per policy targeted)
# level  → livello MLS (s0 = base, s0-s15:c0.c1023 = range)

# Flusso decisionale:
# 1. DAC check (permessi Unix)  → negato? → STOP
# 2. SELinux check (tipo processo vs tipo risorsa) → negato? → AVC denied
# 3. Accesso concesso solo se ENTRAMBI i check passano
```

### Modalita

```bash
# Tre modalità:
# Enforcing:  le policy sono attive e applicate (blocca violazioni)
# Permissive: le policy sono attive ma solo loggano (non bloccano)
# Disabled:   SELinux completamente disabilitato

# Stato corrente
getenforce                          # Enforcing / Permissive / Disabled
sestatus                            # Stato dettagliato

# Cambiare modalità (temporaneo)
sudo setenforce 0                   # Permissive
sudo setenforce 1                   # Enforcing

# Cambiare modalità (persistente)
# /etc/selinux/config
SELINUX=enforcing
SELINUXTYPE=targeted

# ATTENZIONE: passare da Disabled a Enforcing richiede relabeling completo
# 1. Impostare SELINUX=permissive in /etc/selinux/config
# 2. Creare file: touch /.autorelabel
# 3. Reboot → il sistema fa relabeling di tutti i file
# 4. Verificare con ausearch che non ci siano violazioni gravi
# 5. Impostare SELINUX=enforcing e riavviare

# Permissive per singolo dominio (debugging senza disabilitare SELinux):
sudo semanage permissive -a httpd_t
# → Solo httpd è in permissive, tutto il resto è enforcing
# Rimuovere:
sudo semanage permissive -d httpd_t
```

### Contesti e Label

```bash
# Ogni file, processo e porta ha un contesto SELinux
ls -Z /var/www/html/                # Contesto file
ps -eZ | grep httpd                 # Contesto processo
# user:role:type:level
# system_u:system_r:httpd_t:s0

# Il "tipo" è il campo più importante per la policy targeted
# httpd_t può accedere a httpd_sys_content_t

# Cambiare contesto file
sudo chcon -t httpd_sys_content_t /var/www/custom/index.html
# chcon è temporaneo — perso con restorecon

# Ripristinare contesto originale
sudo restorecon -Rv /var/www/html/

# Cambiare contesto permanentemente
sudo semanage fcontext -a -t httpd_sys_content_t "/srv/web(/.*)?"
sudo restorecon -Rv /srv/web/

# Verificare quale contesto è previsto per un percorso
matchpathcon /var/www/html/index.html
# /var/www/html/index.html  system_u:object_r:httpd_sys_content_t:s0

# Contesti file comuni:
# httpd_sys_content_t     — contenuto web leggibile
# httpd_sys_rw_content_t  — contenuto web scrivibile (upload)
# httpd_log_t             — log web
# samba_share_t           — share Samba
# public_content_t        — contenuto condiviso fra servizi
# user_home_t             — file nella home utente
# etc_t                   — file di configurazione
# var_log_t               — file di log

# Transizione di tipo: quando un processo esegue un binario,
# il tipo del processo può cambiare automaticamente.
# Esempio: init_t esegue /usr/sbin/httpd → transizione a httpd_t
# Questo avviene grazie a regole "type_transition" nella policy.
```

### Boolean e Policy

```bash
# Boolean: switch on/off per funzionalità nella policy
getsebool -a                        # Tutti i boolean
getsebool httpd_can_network_connect # Specifico

# Abilitare (temporaneo)
sudo setsebool httpd_can_network_connect on

# Abilitare (permanente)
sudo setsebool -P httpd_can_network_connect on

# Boolean comuni per web server
httpd_can_network_connect           # httpd può fare connessioni di rete
httpd_can_network_connect_db        # httpd può connettersi al database
httpd_enable_cgi                    # httpd può eseguire CGI
httpd_use_nfs                       # httpd può accedere a NFS

# Boolean comuni per altri servizi
ftpd_anon_write                     # FTP: scrittura anonima
samba_enable_home_dirs              # Samba: accesso alle home
ssh_sysadm_login                    # SSH: login come sysadm_r
allow_user_exec_content             # utenti possono eseguire file nella home
deny_ptrace                         # blocca ptrace (anti-debugging)
selinuxuser_execmod                  # utenti possono eseguire stack/heap
container_manage_cgroup              # container possono gestire cgroups

# Cercare boolean per parola chiave
getsebool -a | grep httpd
getsebool -a | grep samba

# Documentazione boolean (se installata)
semanage boolean -l | grep httpd_can_network
```

### Porte SELinux

```bash
# Lista porte associate a tipi
sudo semanage port -l | grep http   # Porte HTTP
sudo semanage port -l | grep ssh

# Aggiungere porta
sudo semanage port -a -t http_port_t -p tcp 8080

# Modificare porta esistente
sudo semanage port -m -t http_port_t -p tcp 8443

# Eliminare porta custom
sudo semanage port -d -t http_port_t -p tcp 8080

# Errore comune: "Port tcp/8080 already defined"
# → usare -m (modify) anziché -a (add)

# Porte comuni:
# http_port_t         — 80, 443, 8080...
# ssh_port_t          — 22
# smtp_port_t         — 25
# postgresql_port_t   — 5432
# mysqld_port_t       — 3306
# dns_port_t          — 53
```

### Troubleshooting SELinux avanzato

```bash
# Log delle violazioni
sudo ausearch -m AVC -ts recent     # Audit log
sudo journalctl -t setroubleshoot   # Su sistemi con setroubleshoot
sudo cat /var/log/audit/audit.log | grep denied

# Generare modulo policy da log
sudo audit2allow -a                 # Mostra regole da permettere
sudo audit2allow -a -M mypolicy     # Crea modulo
sudo semodule -i mypolicy.pp        # Installa modulo

# setroubleshoot (su Fedora/RHEL con GUI)
sudo yum install setroubleshoot-server
sudo sealert -a /var/log/audit/audit.log

# WORKFLOW DI TROUBLESHOOTING STRUTTURATO:
# 1. Identificare il problema
sudo ausearch -m AVC -ts recent --raw | audit2why
# audit2why spiega PERCHÉ l'accesso è negato e suggerisce la fix

# 2. Verificare se è un problema di boolean
sudo ausearch -m AVC -ts recent --raw | audit2why | grep boolean
# Se dice "setsebool httpd_can_network_connect on" → è un boolean

# 3. Verificare se è un problema di contesto file
ls -Z /path/to/denied/file
matchpathcon /path/to/denied/file
# Se i contesti non corrispondono → restorecon -Rv

# 4. Verificare se serve un modulo custom
sudo ausearch -m AVC -ts recent --raw | audit2allow -m mypolicy
# Leggere le regole generate PRIMA di applicarle
# Non applicare ciecamente: audit2allow può concedere troppo

# 5. Verificare se il processo è nel tipo giusto
ps -eZ | grep myprocess
# Se il tipo è unconfined_t, il processo non è stato avviato correttamente

# Log AVC dettagliato:
# type=AVC msg=audit(1234567890.123:456):
#   avc:  denied  { read }
#   for  pid=1234 comm="httpd"
#   name="index.html" dev="sda1" ino=12345
#   scontext=system_u:system_r:httpd_t:s0      ← processo
#   tcontext=system_u:object_r:user_home_t:s0   ← file
#   tclass=file
#   permissive=0

# Lettura: httpd_t ha tentato di leggere un file con tipo user_home_t
# Fix: cambiare il tipo del file a httpd_sys_content_t
```

### Scrivere policy SELinux custom

```bash
# Per servizi custom che non hanno policy predefinita

# 1. Eseguire il servizio in permissive e raccogliere violazioni
sudo semanage permissive -a myapp_t
# Eseguire il servizio, fare tutte le operazioni normali
# Raccogliere le violazioni:
sudo ausearch -m AVC -c myapp --raw > /tmp/myapp_avc.log

# 2. Generare modulo policy
sudo audit2allow -i /tmp/myapp_avc.log -m myapp_policy > myapp_policy.te

# 3. Verificare e ridurre le regole (rimuovere quelle troppo ampie)
# Editare myapp_policy.te manualmente

# 4. Compilare e installare
checkmodule -M -m -o myapp_policy.mod myapp_policy.te
semodule_package -o myapp_policy.pp -m myapp_policy.mod
sudo semodule -i myapp_policy.pp

# 5. Rimuovere permissive
sudo semanage permissive -d myapp_t

# 6. Testare in enforcing
# Monitorare per nuovi AVC: sudo ausearch -m AVC -ts recent

# Gestione moduli SELinux:
sudo semodule -l                    # Lista moduli installati
sudo semodule -d myapp_policy       # Disabilita modulo
sudo semodule -e myapp_policy       # Riabilita modulo
sudo semodule -r myapp_policy       # Rimuovi modulo
```

---

## AppArmor — Guida Operativa

AppArmor è il sistema MAC usato su Debian, Ubuntu e SUSE. Più semplice di SELinux: i profili sono basati su percorso (path-based) anziché su label.

### Architettura AppArmor

```bash
# AppArmor usa profili che definiscono cosa un programma può fare
# Basato su path: le regole si applicano a percorsi filesystem
# Differenza con SELinux: non serve etichettare i file

# Componenti:
# /etc/apparmor.d/               — directory dei profili
# /etc/apparmor.d/abstractions/  — regole riutilizzabili (base, nameservice, etc.)
# /etc/apparmor.d/tunables/      — variabili (home, proc, sys)
# /etc/apparmor.d/local/         — override locali per i profili
# /sys/kernel/security/apparmor/ — interfaccia kernel

# Vantaggi rispetto a SELinux:
# + Più semplice da imparare e configurare
# + Non richiede relabeling del filesystem
# + Profili leggibili come testo
# + aa-genprof e aa-logprof automatizzano la creazione

# Svantaggi rispetto a SELinux:
# - Basato su path → file rinominato = diverso accesso
# - Policy meno granulari (no MLS/MCS)
# - Meno adatto a policy system-wide complesse
```

### Gestione Profili

```bash
# Stato
sudo aa-status                      # Profili caricati, modalità

# Modalità per profilo:
# enforce: blocca le violazioni
# complain: logga ma non blocca
# unconfined: nessuna restrizione

# Cambiare modalità
sudo aa-enforce /etc/apparmor.d/usr.sbin.nginx    # Enforce
sudo aa-complain /etc/apparmor.d/usr.sbin.nginx   # Complain
sudo aa-disable /etc/apparmor.d/usr.sbin.nginx    # Disabilita

# Ricaricare profili
sudo apparmor_parser -r /etc/apparmor.d/usr.sbin.nginx
sudo systemctl reload apparmor

# Ricaricare TUTTI i profili
sudo apparmor_parser -r /etc/apparmor.d/*

# Verificare quale profilo è applicato a un processo
cat /proc/$(pgrep nginx)/attr/current
# nginx (enforce)

# Installare profili aggiuntivi (Ubuntu)
sudo apt install apparmor-profiles apparmor-profiles-extra
```

### Creare Profili

```bash
# Generare profilo automaticamente
sudo aa-genprof /usr/bin/myapp
# → Esegui l'applicazione in un altro terminale
# → aa-genprof analizza le azioni e propone regole
# → Scegli (A)llow, (D)eny, (I)gnore per ogni azione
# → (S)ave per salvare il profilo

# Esempio profilo manuale
# /etc/apparmor.d/usr.local.bin.myapp
#include <tunables/global>

/usr/local/bin/myapp {
  #include <abstractions/base>
  #include <abstractions/nameservice>

  /usr/local/bin/myapp mr,
  /etc/myapp/** r,
  /var/lib/myapp/** rw,
  /var/log/myapp/** w,
  /tmp/myapp-* rw,

  network inet tcp,
  network inet udp,

  deny /etc/shadow r,
  deny /home/** rw,
}

# Permessi: r=read, w=write, m=mmap, x=execute, k=lock, l=link

# TIPI DI ESECUZIONE:
# ix   — inherit: esegue con lo stesso profilo del padre
# cx   — child: esegue con un sotto-profilo definito nel profilo corrente
# px   — profile: esegue con il profilo definito per quell'eseguibile
# ux   — unconfined: esegue senza restrizioni (PERICOLOSO)
# Px   — profile con fallback a unconfined se non esiste il profilo
# Cx   — child con fallback a unconfined

# Esempio con sotto-profilo (child):
/usr/sbin/myservice {
  /usr/bin/helper cx -> helper_profile,

  profile helper_profile {
    #include <abstractions/base>
    /usr/bin/helper mr,
    /var/lib/myservice/data/** r,
    deny network,
  }
}
```

### Profili avanzati

```bash
# Abstractions disponibili (regole predefinite riutilizzabili):
# /etc/apparmor.d/abstractions/
# base           — accessi minimi (libc, ld, locale)
# nameservice    — resolv.conf, nsswitch, DNS
# authentication — PAM, shadow, login
# apache2-common — accessi per Apache
# ssl_certs      — certificati SSL
# python         — interprete Python
# perl           — interprete Perl
# user-tmp       — /tmp utente

# Variabili in tunables:
# @{HOME}        — home dell'utente (/home/*)
# @{PROC}        — /proc/
# @{sys}         — /sys/
# @{run}         — /run/
# @{HOMEDIRS}    — directory base home (/home/)

# Capacità (capabilities) in AppArmor
/usr/sbin/myservice {
  capability net_bind_service,    # bind a porte < 1024
  capability dac_override,        # bypass controlli DAC
  capability setuid,              # cambiare UID
  capability setgid,              # cambiare GID
  # deny capability sys_admin,    # esplicitamente negare
}

# Rlimit (limiti risorse)
/usr/sbin/myservice {
  set rlimit nproc <= 100,
  set rlimit nofile <= 1024,
  set rlimit fsize <= 50M,
}

# Regole di rete
/usr/sbin/myservice {
  network inet stream,            # TCP IPv4
  network inet dgram,             # UDP IPv4
  network inet6 stream,           # TCP IPv6
  deny network raw,               # Nega raw socket
  deny network packet,            # Nega packet socket
}

# Montaggio
/usr/sbin/myservice {
  mount fstype=ext4 /dev/sd* -> /mnt/**,
  deny mount fstype=nfs,
}
```

### Log e troubleshooting AppArmor

```bash
# Log violazioni
sudo journalctl -k | grep apparmor
sudo dmesg | grep apparmor
cat /var/log/syslog | grep apparmor

# Con aa-logprof (analisi interattiva dei log)
sudo aa-logprof                     # Propone regole basate sui log

# WORKFLOW TROUBLESHOOTING:
# 1. Mettere il profilo in complain (non blocca)
sudo aa-complain /etc/apparmor.d/usr.sbin.problematic

# 2. Riprodurre il problema
# 3. Analizzare i log
sudo aa-logprof    # Aggiunge automaticamente le regole mancanti

# 4. Rimettere in enforce
sudo aa-enforce /etc/apparmor.d/usr.sbin.problematic

# 5. Verificare che funzioni
# Se ci sono ancora violazioni → ripetere dal passo 1

# Log dettagliato — abilitare audit per AppArmor:
# /etc/apparmor.d/usr.sbin.nginx
/usr/sbin/nginx flags=(audit) {
  ...
}
# → logga TUTTI gli accessi, non solo i denied

# Formato log tipico:
# apparmor="DENIED" operation="open"
#   profile="/usr/sbin/nginx" name="/etc/secret.conf"
#   pid=1234 comm="nginx" requested_mask="r"
#   denied_mask="r" fsuid=33 ouid=0

# Lettura: nginx (pid 1234) ha tentato di leggere /etc/secret.conf
# Fix: aggiungere "/etc/secret.conf r," al profilo
```

---

## Kernel Hardening

### Parametri sysctl di sicurezza

```bash
# /etc/sysctl.d/99-security.conf
# Applicare: sudo sysctl --system

# ═══ RETE ═══
# Protezione SYN flood
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2

# Protezione ICMP
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.icmp_echo_ignore_all = 0           # 1 = blocca tutti i ping

# Protezione routing
net.ipv4.conf.all.rp_filter = 1             # Reverse path filtering (anti-spoofing)
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.accept_redirects = 0      # Non accettare ICMP redirect
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0        # Non inviare ICMP redirect
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0   # Blocca source routing
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.conf.all.log_martians = 1          # Logga pacchetti con indirizzi impossibili
net.ipv4.conf.default.log_martians = 1

# IPv6 hardening (se non usato, disabilitare)
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_ra = 0             # Router Advertisement
net.ipv6.conf.default.accept_ra = 0
# Disabilitare IPv6 completamente:
# net.ipv6.conf.all.disable_ipv6 = 1
# net.ipv6.conf.default.disable_ipv6 = 1

# Non agire come router
net.ipv4.ip_forward = 0
net.ipv6.conf.all.forwarding = 0

# ═══ KERNEL ═══
# ASLR (Address Space Layout Randomization)
kernel.randomize_va_space = 2               # 2 = full ASLR (stack, heap, mmap, vdso)

# Restrizioni debug
kernel.dmesg_restrict = 1                   # Solo root può leggere dmesg
kernel.kptr_restrict = 2                    # Nascondi puntatori kernel in /proc
kernel.perf_event_paranoid = 3              # Blocca perf_event per non-root
kernel.yama.ptrace_scope = 1               # ptrace solo su figli diretti
# 0 = classico (tutti), 1 = solo figli, 2 = solo con CAP_SYS_PTRACE, 3 = disabilitato

# Protezione symlink e hardlink
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
fs.protected_fifos = 2                      # Protezione FIFO in /tmp
fs.protected_regular = 2                    # Protezione file regolari in /tmp

# Core dump
fs.suid_dumpable = 0                        # No core dump per SUID binaries

# SysRq (Magic SysRq Key)
kernel.sysrq = 0                            # Disabilitare (0) o limitare (176)
# 176 = sync + remount read-only + reboot (solo funzioni safe)

# BPF (Berkeley Packet Filter)
kernel.unprivileged_bpf_disabled = 1        # Solo root può usare BPF
net.core.bpf_jit_harden = 2                # Harden BPF JIT compiler

# User namespaces (se non necessari, restringere)
# kernel.unprivileged_userns_clone = 0      # Attenzione: rompe browser sandbox
# Valutare caso per caso

# Moduli kernel
kernel.modules_disabled = 0                 # 1 = blocca caricamento moduli (irreversibile!)
# ATTENZIONE: una volta impostato a 1, non si può tornare indietro senza reboot
```

### Kernel Lockdown

```bash
# Kernel Lockdown (dal kernel 5.4) impedisce modifiche al kernel in esecuzione
# Due livelli:
# integrity   — blocca modifiche alla configurazione del kernel
# confidentiality — come integrity + blocca lettura dati kernel sensibili

# Verificare stato
cat /sys/kernel/security/lockdown
# [none] integrity confidentiality

# Abilitare (via boot parameter in GRUB)
# /etc/default/grub:
# GRUB_CMDLINE_LINUX="lockdown=integrity"
# sudo update-grub && sudo reboot

# Cosa blocca lockdown=integrity:
# - Caricamento moduli non firmati
# - /dev/mem e /dev/kmem
# - ioperm/iopl
# - kexec di kernel non firmati
# - Scrittura su ACPI tables
# - Accesso diretto a PCI/MSR

# Cosa aggiunge lockdown=confidentiality:
# - Blocca lettura /proc/kcore
# - Blocca bpf read di memoria kernel
# - Blocca perf_event
# - Blocca tracefs/debugfs

# Requisito: Secure Boot abilitato in UEFI
# Senza Secure Boot, lockdown può essere bypassato
```

### Firma dei moduli kernel

```bash
# Verificare se il kernel richiede moduli firmati
grep CONFIG_MODULE_SIG /boot/config-$(uname -r)
# CONFIG_MODULE_SIG=y
# CONFIG_MODULE_SIG_FORCE=y    → SOLO moduli firmati
# CONFIG_MODULE_SIG_ALL=y      → firma tutti i moduli durante la build
# CONFIG_MODULE_SIG_SHA512=y   → algoritmo firma

# Verificare la firma di un modulo
modinfo modulename | grep sig
# sig_id:         PKCS#7
# signer:         Build time autogenerated kernel key
# sig_key:        ...

# Bloccare moduli specifici (anche se firmati)
# /etc/modprobe.d/blacklist-custom.conf
blacklist modulename
install modulename /bin/true

# Lista moduli caricati
lsmod

# Moduli pericolosi da considerare di bloccare su server:
# - usb-storage (se non serve USB)
# - firewire-ohci, firewire-core (DMA attack vector)
# - thunderbolt (DMA attack vector)
# - cramfs, freevxfs, jffs2, hfs, hfsplus, udf (filesystem non necessari)
# - dccp, sctp, rds, tipc (protocolli di rete non necessari)

# Impedire il caricamento di QUALSIASI nuovo modulo (estremo):
# echo 1 > /proc/sys/kernel/modules_disabled
# IRREVERSIBILE senza reboot! Usare solo su server hardened dopo boot completo.
```

### Hardening del boot

```bash
# Proteggere GRUB con password
# 1. Generare hash password
grub-mkpasswd-pbkdf2
# → Enter password: ****
# → PBKDF2 hash: grub.pbkdf2.sha512.10000.HASH

# 2. Aggiungere a /etc/grub.d/40_custom:
cat <<'EOF' | sudo tee -a /etc/grub.d/40_custom
set superusers="admin"
password_pbkdf2 admin grub.pbkdf2.sha512.10000.HASH
EOF

# 3. Aggiornare GRUB
sudo update-grub

# Ora modificare le opzioni di boot richiede la password GRUB

# Secure Boot (UEFI)
# Verificare se Secure Boot è attivo:
mokutil --sb-state
# SecureBoot enabled

# Lista chiavi registrate:
mokutil --list-enrolled

# ATTENZIONE: alcune distro richiedono moduli kernel firmati con chiave MOK
# Se si compilano moduli custom, registrare la propria chiave:
# mokutil --import /path/to/MOK.der

# Proteggere il BIOS/UEFI con password
# Fatto direttamente nel firmware — non configurabile da Linux
```

---

## Architettura Firewall

### iptables — Regole avanzate

```bash
# Template iptables hardened
#!/bin/bash
# Flush
iptables -F
iptables -X
iptables -t nat -F

# Policy default: DROP
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Loopback
iptables -A INPUT -i lo -j ACCEPT

# Connessioni stabilite
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Anti-spoofing
iptables -A INPUT -s 127.0.0.0/8 -i eth0 -j DROP
iptables -A INPUT -s 10.0.0.0/8 -i eth0 -j DROP     # Se eth0 è pubblica

# Rate limiting ICMP
iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 1/s -j ACCEPT

# SSH con rate limiting
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -m recent --set
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -m recent --update --seconds 60 --hitcount 4 -j DROP
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# HTTP/HTTPS
iptables -A INPUT -p tcp -m multiport --dports 80,443 -j ACCEPT

# Logging droppati
iptables -A INPUT -j LOG --log-prefix "IPT-DROP: " --log-level 4
iptables -A INPUT -j DROP

# ═══ REGOLE AGGIUNTIVE ═══
# Protezione da pacchetti invalidi
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# Protezione da scan XMAS
iptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP

# Protezione da scan NULL
iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP

# Protezione da SYN flood
iptables -A INPUT -p tcp --syn -m limit --limit 1/s --limit-burst 3 -j ACCEPT
iptables -A INPUT -p tcp --syn -j DROP

# Bloccare fragmented packets
iptables -A INPUT -f -j DROP

# Limitare connessioni per IP (anti-DoS)
iptables -A INPUT -p tcp --dport 80 -m connlimit --connlimit-above 50 -j REJECT

# GeoIP blocking (richiede xt_geoip)
# iptables -A INPUT -m geoip --src-cc CN,RU -j DROP

# Salvare regole (Debian/Ubuntu)
sudo iptables-save > /etc/iptables/rules.v4
sudo ip6tables-save > /etc/iptables/rules.v6
# Ripristino automatico: apt install iptables-persistent
```

### nftables — Il successore di iptables

```bash
# nftables è il sostituto moderno di iptables
# Vantaggi: sintassi unificata IPv4/IPv6, performance migliori, atomicità

# Verificare se nftables è attivo
nft list ruleset

# Configurazione base: /etc/nftables.conf
#!/usr/sbin/nft -f
flush ruleset

table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;

        # Loopback
        iif lo accept

        # Connessioni stabilite
        ct state established,related accept

        # Invalidi
        ct state invalid drop

        # ICMP rate limited
        ip protocol icmp icmp type echo-request limit rate 1/second accept
        ip6 nexthdr icmpv6 icmpv6 type echo-request limit rate 1/second accept

        # ICMPv6 necessario per IPv6
        ip6 nexthdr icmpv6 icmpv6 type { nd-neighbor-solicit, nd-router-advert,
                                          nd-neighbor-advert } accept

        # SSH rate limited
        tcp dport 22 ct state new limit rate 4/minute accept

        # HTTP/HTTPS
        tcp dport { 80, 443 } accept

        # Logging
        log prefix "nft-drop: " counter drop
    }

    chain forward {
        type filter hook forward priority 0; policy drop;
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}

# Set per blocklisting dinamico
table inet blocklist {
    set blocked_ips {
        type ipv4_addr
        flags timeout
        # IP rimossi automaticamente dopo il timeout
    }

    chain input {
        type filter hook input priority -10; policy accept;
        ip saddr @blocked_ips drop
    }
}

# Aggiungere IP al set di blocco (con timeout di 24h)
nft add element inet blocklist blocked_ips { 1.2.3.4 timeout 24h }

# Rate limiting avanzato con nftables
table inet ratelimit {
    chain input {
        type filter hook input priority 5; policy accept;

        # Limitare nuove connessioni SSH
        tcp dport 22 ct state new meter ssh_meter { ip saddr limit rate 3/minute } accept
        tcp dport 22 ct state new drop

        # Limitare HTTP per IP
        tcp dport 80 ct state new meter http_meter { ip saddr limit rate 100/minute } accept
        tcp dport 80 ct state new drop
    }
}

# Applicare configurazione
sudo nft -f /etc/nftables.conf
sudo systemctl enable nftables
```

### Firewall zone-based

```bash
# firewalld (RHEL/Fedora) — firewall zone-based
# Le zone raggruppano interfacce con lo stesso livello di fiducia

# Zone predefinite (da meno a più fiducia):
# drop       — tutto droppato, nessuna risposta
# block      — tutto rifiutato con ICMP prohibited
# public     — rete pubblica non fidata (default)
# external   — NAT masquerading
# dmz        — server accessibili dall'esterno (servizi limitati)
# work       — rete di lavoro (più fidata di public)
# home       — rete domestica
# internal   — rete interna
# trusted    — tutto accettato (PERICOLOSO)

# Gestione con firewall-cmd
sudo firewall-cmd --get-default-zone
sudo firewall-cmd --get-active-zones

# Assegnare interfaccia a zona
sudo firewall-cmd --zone=public --change-interface=eth0 --permanent

# Aggiungere servizio a zona
sudo firewall-cmd --zone=public --add-service=http --permanent
sudo firewall-cmd --zone=public --add-service=https --permanent

# Aggiungere porta
sudo firewall-cmd --zone=public --add-port=8080/tcp --permanent

# Rimuovere servizio
sudo firewall-cmd --zone=public --remove-service=ssh --permanent

# Rich rules (regole avanzate)
sudo firewall-cmd --zone=public --add-rich-rule='
  rule family="ipv4"
  source address="10.0.0.0/8"
  service name="ssh"
  accept' --permanent

# Rate limiting con rich rules
sudo firewall-cmd --zone=public --add-rich-rule='
  rule family="ipv4"
  service name="ssh"
  limit value="3/m"
  accept' --permanent

# Applicare modifiche
sudo firewall-cmd --reload

# Visualizzare tutte le regole
sudo firewall-cmd --zone=public --list-all
```

### Firewall application-level

```bash
# UFW (Uncomplicated Firewall) — frontend semplificato per iptables
# Default su Ubuntu

# Stato
sudo ufw status verbose

# Abilitare/Disabilitare
sudo ufw enable
sudo ufw disable

# Policy default
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Regole base
sudo ufw allow 22/tcp
sudo ufw allow 80,443/tcp
sudo ufw allow from 10.0.0.0/8 to any port 22

# Rate limiting SSH
sudo ufw limit 22/tcp
# → Blocca dopo 6 connessioni in 30 secondi

# Negare specifico
sudo ufw deny from 1.2.3.4

# Logging
sudo ufw logging on
sudo ufw logging medium  # low/medium/high/full

# Regole numerate (per inserimento/rimozione)
sudo ufw status numbered
sudo ufw delete 3
sudo ufw insert 1 deny from 1.2.3.4

# Application profiles
sudo ufw app list
sudo ufw allow 'Nginx Full'
```

---

## Sicurezza di Rete

### Connection tracking avanzato

```bash
# Il connection tracking (conntrack) è il cuore del firewall stateful
# Traccia ogni connessione e il suo stato

# Stati connessione:
# NEW        — primo pacchetto di una nuova connessione
# ESTABLISHED — connessione già vista in entrambe le direzioni
# RELATED    — nuova connessione relata a una esistente (es. FTP data)
# INVALID    — pacchetto che non appartiene a nessuna connessione nota
# UNTRACKED  — pacchetto esplicitamente escluso dal tracking

# Visualizzare connessioni tracciate
sudo conntrack -L
sudo conntrack -L -p tcp --dport 22    # Solo SSH
sudo conntrack -C                       # Conteggio

# Monitorare connessioni in tempo reale
sudo conntrack -E                       # Event mode

# Parametri conntrack importanti (/etc/sysctl.d/99-conntrack.conf)
# Massimo connessioni tracciate (aumentare per server ad alto traffico)
net.nf_conntrack_max = 262144
# Timeout per TCP established (default: 5 giorni → troppo per server)
net.netfilter.nf_conntrack_tcp_timeout_established = 86400
# Timeout per TCP FIN-WAIT
net.netfilter.nf_conntrack_tcp_timeout_fin_wait = 30
# Timeout per TIME-WAIT
net.netfilter.nf_conntrack_tcp_timeout_time_wait = 30

# Verificare uso corrente
cat /proc/sys/net/netfilter/nf_conntrack_count
cat /proc/sys/net/netfilter/nf_conntrack_max
# Se count si avvicina a max → connessioni droppate silenziosamente

# Diagnostica: conntrack table piena
dmesg | grep "nf_conntrack: table full"
# → Aumentare nf_conntrack_max o ridurre i timeout
```

### Rate limiting e anti-DDoS

```bash
# Rate limiting a livello kernel (sysctl)
# Limitare i SYN per prevenire SYN flood:
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 3

# Rate limiting con iptables (hashlimit per IP):
# Max 50 nuove connessioni HTTP al minuto per IP
iptables -A INPUT -p tcp --dport 80 -m conntrack --ctstate NEW \
  -m hashlimit --hashlimit-above 50/min --hashlimit-mode srcip \
  --hashlimit-name http_flood -j DROP

# Max 20 connessioni simultanee per IP
iptables -A INPUT -p tcp --dport 80 -m connlimit --connlimit-above 20 \
  --connlimit-mask 32 -j REJECT --reject-with tcp-reset

# Con nftables — meter per IP:
# tcp dport 80 meter http_limit { ip saddr limit rate over 50/minute } drop

# Protezione SYN cookies (già nel sysctl base)
net.ipv4.tcp_syncookies = 1

# Protezione da amplificazione DNS/NTP:
# Bloccare UDP su porte non necessarie
iptables -A INPUT -p udp --dport 0:1023 -j DROP
# Eccezione per servizi specifici:
iptables -I INPUT -p udp --dport 53 -j ACCEPT    # DNS server (se necessario)

# Anti-DDoS con ipset (lista IP ad alte performance)
sudo apt install ipset
sudo ipset create blacklist hash:ip timeout 86400
sudo iptables -A INPUT -m set --match-set blacklist src -j DROP
# Aggiungere IP alla blacklist:
sudo ipset add blacklist 1.2.3.4
# Script automatico con fail2ban per alimentare ipset
```

### Difesa da port scanning

```bash
# Detectare e bloccare port scanning con iptables

# Blocco scan SYN stealth (SYN senza ACK successivo)
iptables -N PORTSCAN
iptables -A PORTSCAN -p tcp --tcp-flags SYN,ACK,FIN,RST RST \
  -m limit --limit 1/s --limit-burst 2 -j RETURN
iptables -A PORTSCAN -j DROP

# Blocco scan FIN
iptables -A INPUT -p tcp --tcp-flags ALL FIN -j DROP

# Blocco scan XMAS (tutti i flag settati)
iptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP

# Blocco scan NULL (nessun flag)
iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP

# Tarpit: rallentare lo scanner (rispondere ma lentamente)
# Richiede xt_TARPIT
# iptables -A INPUT -p tcp -m tcp -j TARPIT

# PSAD (Port Scan Attack Detector):
sudo apt install psad
# /etc/psad/psad.conf
# EMAIL_ADDRESSES  admin@example.com;
# HOSTNAME         myserver;
# DANGER_LEVEL1    5;      # Log dopo 5 pacchetti scan
# DANGER_LEVEL2    15;     # Email dopo 15
# DANGER_LEVEL3    150;    # Auto-block dopo 150
# DANGER_LEVEL4    1500;   # Alert critico
# ENABLE_AUTO_IDS  Y;      # Auto-block scanner

# Analizzare scan detection
sudo psad --Status
sudo psad -S    # Sommario

# Nota: troppo logging/blocking può essere un DoS a se stesso
# Calibrare i limiti in base al traffico reale del server
```

### Network segmentation

```bash
# VLAN — separare il traffico di rete
# Principio: servizi diversi su reti diverse

# Esempio di segmentazione:
# VLAN 10 — Management (solo admin, SSH, IPMI)
# VLAN 20 — Applicazione (web server, app server)
# VLAN 30 — Database (solo raggiungibile dalla VLAN 20)
# VLAN 40 — DMZ (server esposti a internet)
# VLAN 50 — Monitoring (Prometheus, Grafana, log)

# Creare VLAN su Linux
sudo ip link add link eth0 name eth0.10 type vlan id 10
sudo ip addr add 10.10.10.1/24 dev eth0.10
sudo ip link set eth0.10 up

# Persistente con netplan (Ubuntu):
# /etc/netplan/01-vlans.yaml
# network:
#   vlans:
#     eth0.10:
#       id: 10
#       link: eth0
#       addresses: [10.10.10.1/24]

# Firewall tra VLAN (il server Linux fa da router/firewall):
iptables -A FORWARD -i eth0.20 -o eth0.30 -p tcp --dport 5432 -j ACCEPT
iptables -A FORWARD -i eth0.30 -o eth0.20 -m conntrack --ctstate ESTABLISHED -j ACCEPT
iptables -A FORWARD -j DROP
# → Solo la VLAN 20 può raggiungere PostgreSQL sulla VLAN 30
```

---

## SSH Hardening

Per la configurazione SSH completa, vedi il documento 10 (Networking). Qui le misure di sicurezza specifiche.

```bash
# /etc/ssh/sshd_config — parametri di sicurezza

# Protocollo e cifratura
Protocol 2                              # Solo SSH v2 (v1 è vulnerabile)
KexAlgorithms curve25519-sha256@libssh.org,diffie-hellman-group16-sha512
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes256-ctr
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com
HostKeyAlgorithms ssh-ed25519,rsa-sha2-512,rsa-sha2-256

# Autenticazione
PermitRootLogin no                      # Mai login diretto come root
PasswordAuthentication no               # Solo chiavi (disabilitare password)
PubkeyAuthentication yes
AuthenticationMethods publickey          # Solo chiave pubblica
# Per MFA: AuthenticationMethods publickey,keyboard-interactive
MaxAuthTries 3
LoginGraceTime 30                       # Secondi per completare il login

# Restrizioni utenti
AllowUsers alice bob deploy             # Solo utenti specifici
AllowGroups sshusers                    # O per gruppo
DenyUsers root guest nobody

# Sessione
ClientAliveInterval 300                 # Ping ogni 5 minuti
ClientAliveCountMax 2                   # Max 2 ping senza risposta → disconnessione
MaxSessions 3                           # Max sessioni per connessione

# Forwarding
AllowTcpForwarding no                   # Disabilitare se non necessario
X11Forwarding no
AllowAgentForwarding no
GatewayPorts no
PermitTunnel no

# Varie
Banner /etc/issue.net
PrintLastLog yes
UsePAM yes
StrictModes yes

# Chroot per utenti SFTP-only
Match Group sftponly
    ChrootDirectory /srv/sftp/%u
    ForceCommand internal-sftp
    AllowTcpForwarding no
    X11Forwarding no

# Dopo le modifiche:
sudo sshd -t                            # Test configurazione (PRIMA di restart!)
sudo systemctl restart sshd

# Chiavi SSH — best practice
# Generare chiave ED25519 (più sicura di RSA)
ssh-keygen -t ed25519 -C "user@host" -a 100
# -a 100: round di derivazione chiave (KDF)

# Se serve compatibilità, RSA con almeno 4096 bit:
ssh-keygen -t rsa -b 4096 -C "user@host"

# Rimuovere chiavi host obsolete (diffie-hellman-group1, dsa)
sudo rm /etc/ssh/ssh_host_dsa_key*
sudo rm /etc/ssh/ssh_host_ecdsa_key*    # Se si usa solo ed25519

# Rigenerare le chiavi host (dopo installazione da template/clone)
sudo rm /etc/ssh/ssh_host_*
sudo ssh-keygen -A
sudo systemctl restart sshd

# Verificare fingerprint della chiave host
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

---

## Audit Framework (auditd)

auditd è il framework di audit del kernel Linux. Monitora e logga eventi di sistema: accesso a file, syscall, modifiche utenti, comandi eseguiti.

### Configurazione auditd

```bash
sudo apt install auditd

# Configurazione principale: /etc/audit/auditd.conf
# Parametri chiave:
# log_file = /var/log/audit/audit.log
# log_format = ENRICHED              # Include nomi utente (non solo UID)
# max_log_file = 50                  # MB per file di log
# max_log_file_action = ROTATE       # Ruota quando raggiunge il max
# num_logs = 10                      # Numero file di log ruotati
# space_left = 100                   # MB — avviso spazio in esaurimento
# space_left_action = email          # Azione quando spazio < space_left
# admin_space_left_action = halt     # Azione estrema: ferma il sistema
# disk_full_action = halt            # Cosa fare se il disco è pieno
# disk_error_action = halt           # Cosa fare se errore disco

# ATTENZIONE: admin_space_left_action = halt ferma il server
# se lo spazio per i log si esaurisce. Questo garantisce che
# un attaccante non possa riempire il disco per fermare il logging.
# Alternativa meno drastica: syslog (invia ai log di sistema)

# Abilitare e avviare
sudo systemctl enable --now auditd
```

### Regole di audit

```bash
# REGOLE
# Monitorare accesso a file sensibili
sudo auditctl -w /etc/passwd -p wa -k passwd_changes
sudo auditctl -w /etc/shadow -p wa -k shadow_changes
sudo auditctl -w /etc/sudoers -p wa -k sudoers_changes
sudo auditctl -w /etc/ssh/sshd_config -p wa -k sshd_config

# -w: watch file
# -p: permessi (r=read, w=write, x=execute, a=attribute change)
# -k: chiave per filtrare nei log

# Monitorare comandi eseguiti come root
sudo auditctl -a always,exit -F arch=b64 -S execve -F euid=0 -k root_commands

# Monitorare mount
sudo auditctl -a always,exit -F arch=b64 -S mount -k mounts

# Monitorare cambio orario
sudo auditctl -a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time_change

# REGOLE PERSISTENTI: /etc/audit/rules.d/custom.rules
-w /etc/passwd -p wa -k passwd_changes
-w /etc/shadow -p wa -k shadow_changes
-w /etc/sudoers -p wa -k sudoers_changes
-a always,exit -F arch=b64 -S execve -F euid=0 -k root_commands

# ═══ REGOLE AGGIUNTIVE PER HARDENING ═══

# Monitorare moduli kernel
-w /sbin/insmod -p x -k kernel_modules
-w /sbin/rmmod -p x -k kernel_modules
-w /sbin/modprobe -p x -k kernel_modules
-a always,exit -F arch=b64 -S init_module -S delete_module -k kernel_modules

# Monitorare cambio hostname
-a always,exit -F arch=b64 -S sethostname -S setdomainname -k hostname_change

# Monitorare accessi a /etc/security/
-w /etc/security/ -p wa -k security_config

# Monitorare gestione utenti e gruppi
-w /usr/sbin/useradd -p x -k user_management
-w /usr/sbin/userdel -p x -k user_management
-w /usr/sbin/usermod -p x -k user_management
-w /usr/sbin/groupadd -p x -k group_management
-w /usr/sbin/groupdel -p x -k group_management
-w /usr/sbin/groupmod -p x -k group_management

# Monitorare cambi di identità (su, sudo)
-w /bin/su -p x -k privilege_escalation
-w /usr/bin/sudo -p x -k privilege_escalation

# Monitorare accesso a chiavi SSH
-w /home/ -p rwa -k user_home_access
-w /root/.ssh/ -p rwa -k root_ssh_access

# Monitorare file di cron
-w /etc/crontab -p wa -k cron_changes
-w /etc/cron.d/ -p wa -k cron_changes
-w /etc/cron.daily/ -p wa -k cron_changes
-w /etc/cron.hourly/ -p wa -k cron_changes
-w /etc/cron.monthly/ -p wa -k cron_changes
-w /etc/cron.weekly/ -p wa -k cron_changes
-w /var/spool/cron/ -p wa -k cron_changes

# Monitorare network configuration
-w /etc/hosts -p wa -k network_config
-w /etc/network/ -p wa -k network_config
-w /etc/sysconfig/network-scripts/ -p wa -k network_config  # RHEL

# Rendere le regole immutabili (nessuno può modificarle senza reboot)
-e 2
# ATTENZIONE: con -e 2, aggiungere o rimuovere regole richiede reboot

# Ricaricare regole
sudo augenrules --load
sudo systemctl restart auditd
```

### Query e report

```bash
# QUERY LOG
sudo ausearch -k passwd_changes     # Per chiave
sudo ausearch -m USER_AUTH          # Per tipo evento
sudo ausearch -ua root -ts today    # Per utente e tempo
sudo ausearch -f /etc/shadow        # Per file

# REPORT
sudo aureport                       # Sommario generale
sudo aureport --auth                # Report autenticazione
sudo aureport --login               # Report login
sudo aureport -f                    # Report file access

# Report avanzati
sudo aureport --failed              # Solo eventi falliti
sudo aureport --summary             # Sommario per tipo
sudo aureport --anomaly             # Anomalie detectate
sudo aureport -x --summary          # Eseguibili più frequenti
sudo aureport --key --summary       # Per chiave audit

# Stato
sudo auditctl -l                    # Regole attive
sudo auditctl -s                    # Stato

# Esportare log in formato leggibile
sudo ausearch -k root_commands --format text > /tmp/root_commands_report.txt

# Cercare eventi in un intervallo temporale
sudo ausearch -ts 2026-05-20 -te 2026-05-22 -k privilege_escalation
```

### Audit per compliance

```bash
# Regole audit allineate a CIS Benchmark e PCI-DSS

# CIS 4.1.4 — Monitorare login e logout
-w /var/log/faillog -p wa -k logins
-w /var/log/lastlog -p wa -k logins
-w /var/log/tallylog -p wa -k logins

# CIS 4.1.5 — Monitorare modifica sessione
-w /var/run/utmp -p wa -k session
-w /var/log/wtmp -p wa -k logins
-w /var/log/btmp -p wa -k logins

# CIS 4.1.6 — Monitorare DAC permission changes
-a always,exit -F arch=b64 -S chmod -S fchmod -S fchmodat -k perm_mod
-a always,exit -F arch=b64 -S chown -S fchown -S fchownat -S lchown -k perm_mod
-a always,exit -F arch=b64 -S setxattr -S lsetxattr -S fsetxattr -k perm_mod
-a always,exit -F arch=b64 -S removexattr -S lremovexattr -S fremovexattr -k perm_mod

# CIS 4.1.7 — Monitorare accesso non autorizzato a file
-a always,exit -F arch=b64 -S open -S openat -S creat -S truncate -S ftruncate \
  -F exit=-EACCES -k access
-a always,exit -F arch=b64 -S open -S openat -S creat -S truncate -S ftruncate \
  -F exit=-EPERM -k access

# CIS 4.1.8 — Monitorare mount
-a always,exit -F arch=b64 -S mount -k mounts

# CIS 4.1.9 — Monitorare cancellazione file
-a always,exit -F arch=b64 -S unlink -S unlinkat -S rename -S renameat -k delete
```

---

## Intrusion Detection

### AIDE — File Integrity Monitoring

```bash
# AIDE (Advanced Intrusion Detection Environment)
# Crea un database dei checksum di tutti i file di sistema
# e rileva modifiche non autorizzate

sudo apt install aide

# Configurazione: /etc/aide/aide.conf (Debian) o /etc/aide.conf (RHEL)
# Definire cosa monitorare e con quale granularità:
# p:  permessi
# i:  inode
# n:  link count
# u:  user
# g:  group
# s:  size
# b:  block count
# m:  mtime
# c:  ctime
# sha256: checksum SHA-256
# sha512: checksum SHA-512

# Esempio configurazione:
# /etc/     CONTENT_EX               # Hash + permessi + metadati
# /bin/     CONTENT_EX
# /sbin/    CONTENT_EX
# /usr/bin/ CONTENT_EX
# /usr/sbin/ CONTENT_EX
# /boot/    CONTENT_EX
# /lib/     CONTENT_EX
# !/var/log/.*                         # Escludere log (cambiano sempre)
# !/var/spool/.*                       # Escludere spool
# !/tmp/.*                             # Escludere tmp

# Inizializzare database (dopo installazione, PRIMA di mettere in produzione)
sudo aideinit
# → Genera /var/lib/aide/aide.db.new
sudo cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Verificare integrità (eseguire periodicamente via cron)
sudo aide --check
# → Mostra file aggiunti, rimossi, modificati

# Aggiornare database (dopo modifiche legittime: aggiornamenti, deploy)
sudo aide --update
sudo cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Cron job: check giornaliero
# /etc/cron.daily/aide-check
#!/bin/bash
LOGFILE=/var/log/aide/aide-$(date +%Y%m%d).log
aide --check > "$LOGFILE" 2>&1
if [ $? -ne 0 ]; then
    mail -s "AIDE: modifiche rilevate su $(hostname)" admin@example.com < "$LOGFILE"
fi

# BEST PRACTICE:
# - Conservare il database AIDE su storage read-only o remoto
#   Un attaccante con root può modificare il database locale
# - Eseguire check dopo ogni aggiornamento del sistema
# - Verificare i risultati: non tutti i cambiamenti sono compromissioni
```

### OSSEC e Wazuh

```bash
# OSSEC — HIDS (Host-based Intrusion Detection System)
# Wazuh — fork di OSSEC con UI moderna, API REST, compliance

# Wazuh è il successore raccomandato di OSSEC
# Componenti:
# - Wazuh Agent: installato su ogni host da monitorare
# - Wazuh Manager: server centrale che analizza gli eventi
# - Wazuh Indexer: storage e ricerca (basato su OpenSearch)
# - Wazuh Dashboard: interfaccia web

# Installazione Agent (su host da monitorare):
curl -s https://packages.wazuh.com/key/GPG-KEY-WAZUH | gpg --dearmor -o /usr/share/keyrings/wazuh.gpg
echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt/ stable main" | \
  sudo tee /etc/apt/sources.list.d/wazuh.list
sudo apt update
sudo apt install wazuh-agent

# Configurare l'agent per puntare al manager
# /var/ossec/etc/ossec.conf
# <client>
#   <server>
#     <address>wazuh-manager.example.com</address>
#   </server>
# </client>

sudo systemctl enable --now wazuh-agent

# Funzionalità di sicurezza:
# - File integrity monitoring (come AIDE ma centralizzato)
# - Log analysis e correlazione
# - Rootkit detection
# - Active response (blocco automatico IP)
# - Vulnerability detection
# - Regulatory compliance (PCI-DSS, GDPR, HIPAA)
# - Incident response
# - Cloud security (AWS, Azure, GCP)

# Regole custom Wazuh (esempio: alert su login root)
# /var/ossec/etc/rules/local_rules.xml
# <group name="local_rules,">
#   <rule id="100001" level="12">
#     <if_sid>5501</if_sid>
#     <user>root</user>
#     <description>Login diretto come root detectato</description>
#   </rule>
# </group>
```

### chkrootkit e rkhunter

```bash
# Rootkit detection — due tool complementari

# chkrootkit
sudo apt install chkrootkit
sudo chkrootkit
# Controlla:
# - Binari di sistema modificati (ls, ps, netstat, ecc.)
# - Interfacce in modalità promiscua
# - Ultime entry di log cancellate
# - Segni di rootkit noti (LPD, SHV5, ecc.)

# rkhunter (Rootkit Hunter)
sudo apt install rkhunter

# Aggiornare database di firme
sudo rkhunter --update
sudo rkhunter --propupd          # Aggiornare proprietà file

# Scan completo
sudo rkhunter --check --sk       # --sk = skip (non chiedere conferma)

# Cosa controlla:
# - Confronto hash dei binari di sistema
# - Rootkit noti (900+ firme)
# - File sospetti in /tmp, /dev, ecc.
# - Permessi di file critici
# - String sospette nei binari
# - Porte in ascolto sospette
# - Account con UID 0 (oltre root)
# - File nascosti in /dev

# Cron job: scan settimanale
# /etc/cron.weekly/rkhunter
#!/bin/bash
rkhunter --check --sk --report-warnings-only > /var/log/rkhunter-$(date +%Y%m%d).log 2>&1
if [ $? -ne 0 ]; then
    mail -s "rkhunter: anomalie su $(hostname)" admin@example.com < /var/log/rkhunter-$(date +%Y%m%d).log
fi

# Dopo aggiornamenti di sistema (falsi positivi):
sudo rkhunter --propupd         # Aggiorna database hash
```

---

## Log Monitoring per la Sicurezza

### rsyslog e syslog-ng

```bash
# rsyslog — il syslog standard su Debian/Ubuntu/RHEL

# Configurazione: /etc/rsyslog.conf e /etc/rsyslog.d/
# Facility: kern, auth, authpriv, cron, daemon, mail, user, local0-7
# Priority: emerg, alert, crit, err, warning, notice, info, debug

# Configurazione base sicurezza in /etc/rsyslog.d/security.conf:
# Log autenticazione separato
auth,authpriv.*                /var/log/auth.log
# Log kernel separato
kern.*                         /var/log/kern.log
# Tutti i messaggi critici
*.crit                         /var/log/critical.log

# Invio log a server remoto (TCP con TLS)
# Moduli necessari:
# module(load="imtcp")
# module(load="omfwd")
# action(
#   type="omfwd"
#   target="logserver.example.com"
#   port="6514"
#   protocol="tcp"
#   StreamDriverMode="1"
#   StreamDriver="gtls"
#   StreamDriverAuthMode="x509/name"
#   StreamDriverPermittedPeers="logserver.example.com"
# )

# syslog-ng — alternativa più potente per filtraggio e routing

# /etc/syslog-ng/syslog-ng.conf — esempio:
# source s_local {
#     system();
#     internal();
# };
#
# filter f_auth { facility(auth, authpriv); };
# filter f_crit { level(crit..emerg); };
#
# destination d_auth { file("/var/log/auth.log"); };
# destination d_remote { tcp("logserver.example.com" port(6514) tls()); };
#
# log { source(s_local); filter(f_auth); destination(d_auth); destination(d_remote); };
# log { source(s_local); filter(f_crit); destination(d_remote); };

# Protezione dei log:
# 1. Append-only flag
sudo chattr +a /var/log/auth.log
sudo chattr +a /var/log/syslog

# 2. Invio immediato a server remoto (l'attaccante non può cancellare)
# 3. Rotazione con compressione e firma
# 4. Permessi restrittivi
chmod 640 /var/log/auth.log
chown root:adm /var/log/auth.log
```

### Pattern sospetti da monitorare

```bash
# ═══ PATTERN DI ATTACCO NEI LOG ═══

# 1. Brute force SSH
grep "Failed password" /var/log/auth.log | awk '{print $11}' | sort | uniq -c | sort -rn | head
# Molti tentativi dallo stesso IP → brute force

# 2. Privilege escalation riuscita
grep "session opened for user root" /var/log/auth.log
grep "COMMAND=" /var/log/auth.log | grep -v "expected_commands"

# 3. Accessi a orari anomali (fuori orario lavorativo)
grep "Accepted" /var/log/auth.log | awk '{print $1, $2, $3}' | grep -E " (0[0-5]|2[2-3]):"

# 4. Utenti creati/modificati
grep -E "useradd|usermod|groupadd" /var/log/auth.log

# 5. Servizi riavviati in modo anomalo
journalctl --since "1 hour ago" -u sshd -u nginx -u mysql | grep -i "restart\|stop\|start"

# 6. Tentativi di accesso a file sensibili (da audit log)
sudo ausearch -k shadow_changes -ts today
sudo ausearch -k sudoers_changes -ts today

# 7. Connessioni di rete sospette
ss -tnp | grep -v -E ":(22|80|443) " | grep ESTABLISHED
# Connessioni established su porte non standard

# 8. Processi sospetti
ps auxf | grep -E "nc |ncat |socat |python.*-c.*import|perl.*-e.*socket"
# Reverse shell comuni

# 9. Crontab modificati
grep -r "crontab" /var/log/auth.log
ls -la /var/spool/cron/crontabs/     # Verificare timestamp

# 10. Moduli kernel caricati di recente
dmesg | grep -i "module\|insmod"
journalctl -k | grep -i "module"

# Script di monitoring automatizzato: salva come /usr/local/bin/security-monitor.sh
#!/bin/bash
# Eseguire via cron ogni 15 minuti
ALERT_EMAIL="admin@example.com"
LOG="/var/log/security-monitor.log"
THRESHOLD_FAILED_SSH=10

count=$(grep -c "Failed password" /var/log/auth.log 2>/dev/null)
if [ "$count" -gt "$THRESHOLD_FAILED_SSH" ]; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] ALERT: $count failed SSH attempts" >> "$LOG"
    # Invia alert se supera soglia
fi
```

### Centralizzazione dei log

```bash
# Perché centralizzare:
# - L'attaccante con root può cancellare i log locali
# - Correlazione eventi tra più server
# - Retention policy centralizzata
# - Analisi e ricerca più efficiente

# Stack raccomandato: Wazuh (SIEM open source)
# Alternativa leggera: rsyslog + Loki + Grafana
# Alternativa enterprise: Elastic SIEM, Splunk

# rsyslog come server di log centralizzato:
# Sul server di log — /etc/rsyslog.conf:
# module(load="imtcp")
# input(type="imtcp" port="514")
#
# template(name="RemoteLogs" type="string"
#   string="/var/log/remote/%HOSTNAME%/%PROGRAMNAME%.log")
#
# if $fromhost-ip != '127.0.0.1' then {
#   action(type="omfile" dynaFile="RemoteLogs")
#   stop
# }

# Sul client — /etc/rsyslog.d/remote.conf:
# *.* action(type="omfwd" target="logserver" port="514" protocol="tcp")

# Retention: conservare i log per almeno 90 giorni (PCI-DSS richiede 1 anno)
# logrotate: /etc/logrotate.d/rsyslog
# /var/log/remote/*/*.log {
#     daily
#     rotate 365
#     compress
#     delaycompress
#     missingok
#     notifempty
# }
```

---

## Vulnerability Management

### Lynis — Audit di sicurezza

```bash
# LYNIS — audit di sicurezza
sudo apt install lynis
sudo lynis audit system             # Audit completo
# → Produce report con score e raccomandazioni

# Opzioni avanzate
sudo lynis audit system --quick     # Scan veloce (no interattivo)
sudo lynis audit system --pentest   # Modalità pentest (più aggressiva)
sudo lynis audit system --profile /etc/lynis/custom.prf  # Profilo custom

# Report dettagliato
sudo lynis show details TEST-1234   # Dettagli test specifico
cat /var/log/lynis.log              # Log completo
cat /var/log/lynis-report.dat       # Dati strutturati

# Interpretare lo score (Hardening Index):
# 80-100: Buono — sistema ben hardened
# 60-79:  Discreto — miglioramenti necessari
# 40-59:  Sufficiente — rischi significativi
# 0-39:   Critico — hardening urgente

# Automatizzare scan periodici
# /etc/cron.weekly/lynis-scan
#!/bin/bash
lynis audit system --quick --no-colors > /var/log/lynis/weekly-$(date +%Y%m%d).log 2>&1
# Invia score via email
score=$(grep "Hardening index" /var/log/lynis/weekly-$(date +%Y%m%d).log | awk '{print $NF}')
echo "Lynis score: $score" | mail -s "Lynis weekly: $(hostname)" admin@example.com

# Profilo custom: /etc/lynis/custom.prf
# skip-test=FILE-6310               # Salta test specifico
# config-data=sysctl;net.ipv4.ip_forward;0  # Aspettativa personalizzata
```

### OpenVAS / Greenbone

```bash
# OpenVAS (Open Vulnerability Assessment Scanner)
# Ora parte di Greenbone Community Edition
# Scanner di vulnerabilità di rete con 100.000+ NVT (test)

# Installazione via container (raccomandato):
docker run -d --name greenbone \
  -p 9392:9392 \
  -v gvm-data:/var/lib/gvm \
  greenbone/community-edition:latest

# Accesso web: https://localhost:9392
# Default: admin / admin (CAMBIARE SUBITO)

# Workflow:
# 1. Creare Target (IP/range da scannare)
# 2. Creare Task (tipo di scan: Full and Fast, Deep, ecc.)
# 3. Eseguire il Task
# 4. Analizzare i risultati
# 5. Prioritizzare per severity (CVSS)
# 6. Remediation

# Scan dalla CLI (gvm-cli):
# gvm-cli --gmp-username admin --gmp-password pass tls \
#   --hostname localhost --port 9390 \
#   --xml '<get_tasks/>'

# Scansione ricorrente: schedulare task settimanali
# I risultati mostrano:
# - CVE con CVSS score
# - Descrizione della vulnerabilità
# - Remediation suggerita
# - Riferimenti a patch/advisory

# OpenSCAP — compliance check
sudo apt install libopenscap8 scap-security-guide
sudo oscap xccdf eval --profile xccdf_org.ssgproject.content_profile_cis \
  /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml
```

### Nessus

```bash
# Nessus — scanner di vulnerabilità commerciale (versione Essentials è gratuita)
# Più di 200.000 plugin, aggiornamenti costanti

# Download e installazione:
# 1. Scaricare da tenable.com/products/nessus
# 2. sudo dpkg -i Nessus-*.deb
# 3. sudo systemctl start nessusd
# 4. Accesso: https://localhost:8834

# Differenza con OpenVAS:
# - Nessus: più plugin, supporto commerciale, credential scanning potente
# - OpenVAS: open source, auto-hostable, community-driven

# Best practice per scan:
# 1. Scansionare in orari di basso traffico
# 2. Iniziare con scan non intrusivi (non provare exploit)
# 3. Usare credential scan (login SSH) per risultati più accurati
# 4. Escludere sistemi critici fragili (dispositivi medici, SCADA)
# 5. Documentare e prioritizzare per CVSS
# 6. Verificare i falsi positivi prima di allarmare

# Prioritizzazione:
# CVSS 9.0-10.0 → Critico: patch entro 24h
# CVSS 7.0-8.9  → Alto: patch entro 7 giorni
# CVSS 4.0-6.9  → Medio: patch entro 30 giorni
# CVSS 0.1-3.9  → Basso: piano di remediation
```

### CVE Monitoring e patching

```bash
# Monitorare le CVE rilevanti per il proprio stack

# Tool: vuls (open source vulnerability scanner)
# Analizza i pacchetti installati e confronta con database CVE

# Controllare CVE per pacchetti installati (Debian/Ubuntu):
apt list --upgradable 2>/dev/null | grep -i security

# Debian Security Tracker
# https://security-tracker.debian.org/

# Ubuntu USN (Ubuntu Security Notices)
# https://ubuntu.com/security/notices

# RHEL: controllare errata
sudo yum updateinfo list security

# Patching strategy:
# 1. CRITICO (CVE CVSS >= 9.0, exploit in the wild):
#    Patch entro 24-48h. Se non possibile, workaround/mitigazione immediata.
# 2. ALTO (CVSS 7.0-8.9):
#    Patch nella prossima finestra di manutenzione (7 giorni).
# 3. MEDIO (CVSS 4.0-6.9):
#    Patch nel ciclo mensile.
# 4. BASSO (CVSS < 4.0):
#    Patch nel ciclo trimestrale.

# Aggiornamenti automatici di sicurezza (Debian/Ubuntu):
sudo apt install unattended-upgrades
# /etc/apt/apt.conf.d/50unattended-upgrades
# Unattended-Upgrade::Allowed-Origins {
#     "${distro_id}:${distro_codename}-security";
# };
# Unattended-Upgrade::Mail "admin@example.com";
# Unattended-Upgrade::Automatic-Reboot "false";      # Non riavviare automaticamente
# Unattended-Upgrade::Remove-Unused-Dependencies "true";

# Verificare che unattended-upgrades funzioni:
sudo unattended-upgrade --dry-run --debug

# Per RHEL:
sudo yum install yum-cron
# /etc/yum/yum-cron.conf:
# update_cmd = security
# apply_updates = yes
```

---

## Sicurezza dei Container

### Docker hardening

```bash
# Docker di default gira come root → superficie d'attacco ampia
# Principi di hardening:

# 1. Non eseguire container come root
# Dockerfile:
# FROM ubuntu:22.04
# RUN groupadd -r appuser && useradd -r -g appuser appuser
# USER appuser
# CMD ["./myapp"]

# Verificare: docker inspect --format '{{.Config.User}}' container_name

# 2. Read-only filesystem
docker run --read-only --tmpfs /tmp:size=100M myimage

# 3. Droppare tutte le capabilities non necessarie
docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE myimage

# 4. Usare seccomp profile
docker run --security-opt seccomp=default.json myimage

# 5. No-new-privileges flag
docker run --security-opt no-new-privileges myimage
# Impedisce al processo di acquisire nuovi privilegi (setuid)

# 6. Limitare risorse (cgroups)
docker run --memory=512m --cpus=0.5 --pids-limit=100 myimage

# 7. Network isolation
docker network create --internal private_net
docker run --network=private_net myimage
# Container sulla rete internal non possono raggiungere internet

# 8. Montare filesystem con opzioni restrittive
docker run -v /data:/data:ro myimage    # Read-only mount

# 9. Docker socket NON montare nel container
# PERICOLOSO: -v /var/run/docker.sock:/var/run/docker.sock
# Equivale a dare root sull'host

# 10. Docker daemon hardening — /etc/docker/daemon.json:
{
  "icc": false,                         # Blocca inter-container communication
  "userns-remap": "default",            # User namespace remapping
  "no-new-privileges": true,            # Default: no new privileges
  "live-restore": true,                 # Container sopravvivono a daemon restart
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "default-ulimits": {
    "nofile": { "Name": "nofile", "Hard": 1024, "Soft": 1024 },
    "nproc": { "Name": "nproc", "Hard": 100, "Soft": 100 }
  }
}
```

### Podman — Rootless containers

```bash
# Podman è l'alternativa rootless a Docker
# Ogni container gira nel namespace utente → nessun demone root

# Installare
sudo apt install podman

# Eseguire container senza root (come utente normale)
podman run --rm -it alpine sh
# → Il container gira nel user namespace dell'utente
# → root nel container ≠ root sull'host

# Vantaggi di sicurezza vs Docker:
# - Nessun demone root in ascolto
# - User namespace di default (root nel container → utente non privilegiato sull'host)
# - Socket Unix per utente (non condiviso)
# - Compatibile con Dockerfile e registry Docker

# Podman con SELinux (RHEL/Fedora):
# I container sono automaticamente confinati con SELinux
podman run --security-opt label=type:container_t myimage

# Verificare che il container non sia root sull'host:
podman top container_id user huser
# user=root huser=1000 → root nel container, utente 1000 sull'host
```

### Image scanning

```bash
# Trivy — scanner di vulnerabilità per immagini container
# Scansiona: CVE, misconfiguration, secrets, license

# Installare
sudo apt install trivy
# Oppure: curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sudo sh

# Scansionare un'immagine
trivy image nginx:latest
trivy image --severity HIGH,CRITICAL myapp:v1.0

# Scansionare un Dockerfile
trivy config Dockerfile

# Scansionare il filesystem locale
trivy fs /path/to/project

# Scansionare per secrets esposti nell'immagine
trivy image --scanners secret myapp:v1.0

# Integrare nel CI/CD:
# trivy image --exit-code 1 --severity CRITICAL myapp:v1.0
# Se trova vulnerabilità CRITICAL → exit code 1 → pipeline fallisce

# Grype — alternativa di Anchore
# grype myapp:v1.0

# Best practice per immagini sicure:
# 1. Base image minimale (alpine, distroless, scratch)
# 2. Multi-stage build (solo artefatti finali nell'immagine)
# 3. Pinning versioni (FROM node:20.11.0-alpine, non node:latest)
# 4. Scansione in CI prima del push al registry
# 5. Aggiornare le base image regolarmente
# 6. Non includere segreti nell'immagine (usare secrets mount)
# 7. Firma delle immagini (cosign, Notary)
```

### Runtime protection

```bash
# Falco — runtime security per container (CNCF)
# Monitora syscall in tempo reale e detecta comportamenti anomali

# Installazione:
curl -fsSL https://falco.org/repo/falcosecurity-packages.asc | sudo gpg --dearmor -o /usr/share/keyrings/falco.gpg
echo "deb [signed-by=/usr/share/keyrings/falco.gpg] https://download.falco.org/packages/deb stable main" | \
  sudo tee /etc/apt/sources.list.d/falcosecurity.list
sudo apt update
sudo apt install falco

# Regole di default detectano:
# - Shell spawned nel container
# - Accesso a /etc/shadow dal container
# - Network tool nel container (nc, wget, curl)
# - Scrittura sotto /etc nel container
# - Container con privilege escalation
# - Mount di volumi sensibili

# Esempio output Falco:
# 14:25:11.123456 Warning: Shell spawned in container
#   (user=root container_id=abc123 container_name=web-1
#   shell=bash parent=entrypoint.sh cmdline=bash)

# Regola custom:
# - rule: Sensitive file opened in container
#   desc: An attempt to read sensitive files in a container
#   condition: >
#     container and open_read and
#     (fd.name startswith /etc/shadow or fd.name startswith /etc/passwd)
#   output: >
#     Sensitive file accessed in container
#     (user=%user.name container=%container.name file=%fd.name)
#   priority: WARNING
```

---

## Rootkit Detection e Forensics

```bash
# ═══ ROOTKIT DETECTION ═══

# I rootkit sono software che nascondono la presenza dell'attaccante
# Tipi:
# 1. User-space rootkit: sostituisce binari (ls, ps, netstat)
# 2. Kernel rootkit: modulo kernel che altera le syscall
# 3. Bootkit: infetta il bootloader/MBR
# 4. Firmware rootkit: infetta UEFI/BIOS (molto difficile da rilevare)

# Tool di detection (eseguire regolarmente):
sudo rkhunter --check --sk
sudo chkrootkit

# Confronto manuale dei binari (se si sospetta compromissione):
# Verificare hash dei binari critici contro il package manager
dpkg -V                             # Debian/Ubuntu: verifica tutti i pacchetti
rpm -Va                             # RHEL: verifica tutti i pacchetti
# Output: S.5....T. indica file modificato (S=size, 5=checksum, T=time)

# Verificare un singolo binario:
sha256sum /usr/bin/ls
dpkg -S /usr/bin/ls                 # Trovare il pacchetto
apt download coreutils              # Scaricare il pacchetto originale
dpkg-deb -x coreutils*.deb /tmp/coreutils
sha256sum /tmp/coreutils/usr/bin/ls # Confrontare

# ═══ FORENSICS DI BASE ═══

# REGOLA D'ORO: non modificare il sistema compromesso
# Acquisire evidenze prima di qualsiasi azione di remediation

# 1. Catturare stato della memoria (se possibile)
# Tool: LiME (Linux Memory Extractor)
# sudo insmod lime.ko "path=/tmp/memory.lime format=lime"

# 2. Catturare snapshot del disco
sudo dd if=/dev/sda of=/mnt/forensics/disk-image.raw bs=4M status=progress
# Calcolare hash per chain of custody:
sha256sum /mnt/forensics/disk-image.raw > /mnt/forensics/disk-image.sha256

# 3. Timeline del filesystem (senza montare il disco originale)
# Montare l'immagine in read-only:
sudo mount -o ro,loop /mnt/forensics/disk-image.raw /mnt/analysis

# Creare timeline con find:
find /mnt/analysis -type f -printf '%T+ %p\n' | sort > /mnt/forensics/timeline.txt

# 4. Analisi dei log (copiarli PRIMA di qualsiasi modifica)
cp -a /var/log/ /mnt/forensics/logs/
cp /var/log/auth.log /mnt/forensics/
cp /var/log/syslog /mnt/forensics/

# 5. Stato della rete al momento della scoperta
ss -tnp > /mnt/forensics/network-connections.txt
ip addr > /mnt/forensics/ip-addresses.txt
ip route > /mnt/forensics/routes.txt
iptables-save > /mnt/forensics/firewall-rules.txt

# 6. Processi e utenti attivi
ps auxf > /mnt/forensics/processes.txt
w > /mnt/forensics/active-users.txt
last -50 > /mnt/forensics/last-logins.txt
lastlog > /mnt/forensics/lastlog.txt

# 7. Crontab e job schedulati
for user in $(cut -f1 -d: /etc/passwd); do
    crontab -l -u "$user" 2>/dev/null > "/mnt/forensics/crontab-$user.txt"
done
ls -la /etc/cron.d/ > /mnt/forensics/cron.d-listing.txt

# 8. Moduli kernel caricati
lsmod > /mnt/forensics/loaded-modules.txt

# Tutti i file forensics: timestamp UTC ISO 8601
# Mantenere hashes per integrità della catena di custodia
```

---

## fail2ban

```bash
sudo apt install fail2ban

# /etc/fail2ban/jail.local (override della config default)
[DEFAULT]
bantime = 3600                      # Ban 1 ora
findtime = 600                      # Finestra 10 minuti
maxretry = 3                        # Max tentativi

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 7200                      # 2 ore per SSH

[nginx-http-auth]
enabled = true
port = http,https
filter = nginx-http-auth
logpath = /var/log/nginx/error.log

# Gestione
sudo fail2ban-client status         # Stato generale
sudo fail2ban-client status sshd    # Stato jail sshd
sudo fail2ban-client set sshd banip 1.2.3.4     # Ban manuale
sudo fail2ban-client set sshd unbanip 1.2.3.4   # Unban

# ═══ CONFIGURAZIONE AVANZATA ═══

# Jail per brute force su applicazioni web
[nginx-botsearch]
enabled  = true
port     = http,https
filter   = nginx-botsearch
logpath  = /var/log/nginx/access.log
maxretry = 5
bantime  = 86400                    # 24 ore

# Jail per tentativi su WordPress
[wordpress-auth]
enabled  = true
port     = http,https
filter   = wordpress-auth
logpath  = /var/log/nginx/access.log
maxretry = 5
bantime  = 3600

# Filtro custom: /etc/fail2ban/filter.d/wordpress-auth.conf
# [Definition]
# failregex = ^<HOST> .* "POST /wp-login.php
# ignoreregex =

# Azione con ipset (performance per migliaia di IP bannati)
# [DEFAULT]
# banaction = iptables-ipset-proto6

# Azione con notifica email
# [DEFAULT]
# action = %(action_mwl)s           # Ban + email con log
# destemail = admin@example.com
# sender = fail2ban@example.com

# Whitelist IP fidati
[DEFAULT]
ignoreip = 127.0.0.1/8 10.0.0.0/8 192.168.0.0/16

# Recidive: ban più lungo per IP bannati ripetutamente
[recidive]
enabled  = true
logpath  = /var/log/fail2ban.log
banaction = iptables-allports
bantime  = 604800                   # 1 settimana
findtime = 86400                    # 24 ore
maxretry = 3                        # 3 ban in 24h → ban 1 settimana
```

---

## Incident Response Workflow

```bash
# ═══ WORKFLOW DI RISPOSTA AGLI INCIDENTI ═══
#
# Fase 1: PREPARAZIONE (prima dell'incidente)
# Fase 2: IDENTIFICAZIONE (rilevamento)
# Fase 3: CONTENIMENTO (limitare il danno)
# Fase 4: ERADICAZIONE (rimuovere la minaccia)
# Fase 5: RECOVERY (ripristino)
# Fase 6: LESSONS LEARNED (post-mortem)

# ═══ FASE 1: PREPARAZIONE ═══
# Checklist pre-incidente:
# [ ] Backup verificati e testati (restore funzionante)
# [ ] Audit logging abilitato (auditd, log centralizzati)
# [ ] AIDE/Wazuh configurato e database aggiornato
# [ ] Contatti di escalation documentati
# [ ] Playbook IR stampato (non solo digitale — il server potrebbe essere compromesso)
# [ ] Kit forensics pronto (USB bootable, tool di acquisizione)
# [ ] Canale di comunicazione sicuro (non sul sistema compromesso)

# ═══ FASE 2: IDENTIFICAZIONE ═══
# Segnali di compromissione:
# - Alert da IDS/IPS (Wazuh, Falco)
# - AIDE: file di sistema modificati
# - Login anomali (orari, location, utenti)
# - Processi sospetti (crypto miner, reverse shell)
# - Traffico di rete anomalo (C2, exfiltration)
# - File sospetti in /tmp, /dev/shm, /var/tmp
# - Account creati senza autorizzazione
# - Crontab modificati

# Verifiche immediate:
# Chi è connesso ora?
w
who
last -20

# Processi sospetti?
ps auxf | head -50
# Cercare: processi senza nome noto, uso CPU/RAM anomalo, parent sospetto

# Connessioni di rete anomale?
ss -tnp | grep ESTABLISHED
# Cercare: connessioni a IP esterni sconosciuti, porte alte

# File recentemente modificati in aree critiche?
find /etc -mtime -1 -type f 2>/dev/null
find /usr/bin -mtime -1 -type f 2>/dev/null
find /tmp -type f -executable 2>/dev/null

# ═══ FASE 3: CONTENIMENTO ═══
# PRIORITA: fermare la propagazione e la perdita di dati

# Contenimento rapido (se confermata la compromissione):
# 1. NON spegnere il server (si perdono dati volatili)
# 2. Isolare dalla rete (se possibile, senza spegnere)
sudo iptables -A INPUT -j DROP
sudo iptables -A OUTPUT -j DROP
sudo iptables -I INPUT -s ADMIN_IP -j ACCEPT     # Mantenere accesso admin
sudo iptables -I OUTPUT -d ADMIN_IP -j ACCEPT

# 3. Bloccare l'account compromesso (senza eliminarlo)
sudo usermod -L compromised_user
sudo pkill -u compromised_user

# 4. Cambiare credenziali critiche
# - Password root (se compromessa)
# - Chiavi SSH host e utente
# - Token e API key che potrebbero essere stati esposti
# - Password database

# 5. Acquisire evidenze PRIMA di pulire (vedi sezione Forensics)

# ═══ FASE 4: ERADICAZIONE ═══
# Dopo aver raccolto le evidenze:

# 1. Identificare il vettore di ingresso
# Analizzare: come è entrato l'attaccante?
# Log SSH, log web, vulnerabilità applicativa, credenziali rubate?

# 2. Rimuovere la minaccia
# - Rimuovere backdoor (crontab, authorized_keys, servizi)
# - Rimuovere file dell'attaccante
# - Rimuovere account creati dall'attaccante
# - Ripristinare binari modificati dal package manager

# 3. Patchare la vulnerabilità sfruttata
# - Aggiornare il software vulnerabile
# - Rafforzare la configurazione
# - Aggiungere regole firewall/IDS

# ═══ FASE 5: RECOVERY ═══
# 1. Ripristinare da backup pulito (se la compromissione è profonda)
# 2. Verificare integrità con AIDE
# 3. Monitoraggio intensivo per 48-72h
# 4. Verificare che la vulnerabilità sia chiusa

# ═══ FASE 6: LESSONS LEARNED ═══
# Entro 5 giorni dall'incidente:
# 1. Timeline dell'incidente (UTC ISO 8601)
# 2. Vettore di attacco e root cause
# 3. Cosa ha funzionato nella risposta
# 4. Cosa va migliorato
# 5. Action items con responsabili e deadline
```

---

## CIS Benchmarks — Implementazione

### CIS Level 1 — Ubuntu

```bash
# CIS Benchmark Ubuntu 22.04 — Level 1 (Server)
# Controlli essenziali che non impattano funzionalità

# ═══ 1. FILESYSTEM ═══
# 1.1.1 — Disabilitare filesystem non necessari
cat <<'EOF' | sudo tee /etc/modprobe.d/cis-filesystem.conf
install cramfs /bin/true
install freevxfs /bin/true
install jffs2 /bin/true
install hfs /bin/true
install hfsplus /bin/true
install udf /bin/true
EOF

# 1.1.2 — /tmp su partizione separata con opzioni restrittive
# /etc/fstab:
# tmpfs  /tmp  tmpfs  defaults,rw,nosuid,nodev,noexec,relatime,size=2G  0  0
sudo mount -o remount,nosuid,nodev,noexec /tmp

# 1.1.3 — /var/tmp bind mount o partizione separata
sudo mount --bind /tmp /var/tmp

# 1.1.4 — /dev/shm con opzioni restrittive
# /etc/fstab:
# tmpfs  /dev/shm  tmpfs  defaults,noexec,nodev,nosuid  0  0
sudo mount -o remount,noexec,nodev,nosuid /dev/shm

# ═══ 2. SERVIZI ═══
# 2.1 — Disabilitare servizi non necessari
sudo systemctl disable --now avahi-daemon
sudo systemctl disable --now cups
sudo systemctl disable --now isc-dhcp-server
sudo systemctl disable --now rpcbind
sudo systemctl disable --now nfs-server

# ═══ 3. RETE ═══
# 3.1 — Disabilitare IPv6 se non usato
echo "net.ipv6.conf.all.disable_ipv6 = 1" | sudo tee -a /etc/sysctl.d/99-cis.conf
echo "net.ipv6.conf.default.disable_ipv6 = 1" | sudo tee -a /etc/sysctl.d/99-cis.conf

# 3.2 — Parametri di rete
cat <<'EOF' | sudo tee /etc/sysctl.d/99-cis-network.conf
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.tcp_syncookies = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
EOF
sudo sysctl --system

# ═══ 4. AUDIT ═══
# 4.1 — auditd abilitato
sudo apt install auditd
sudo systemctl enable --now auditd

# 4.2 — Regole audit CIS
cat <<'EOF' | sudo tee /etc/audit/rules.d/cis.rules
-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time-change
-a always,exit -F arch=b64 -S clock_settime -k time-change
-w /etc/localtime -p wa -k time-change
-w /etc/group -p wa -k identity
-w /etc/passwd -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/security/opasswd -p wa -k identity
-a always,exit -F arch=b64 -S sethostname -S setdomainname -k system-locale
-w /etc/issue -p wa -k system-locale
-w /etc/issue.net -p wa -k system-locale
-w /etc/hosts -p wa -k system-locale
-w /var/log/faillog -p wa -k logins
-w /var/log/lastlog -p wa -k logins
-w /var/log/tallylog -p wa -k logins
-w /var/run/utmp -p wa -k session
-w /var/log/wtmp -p wa -k logins
-w /var/log/btmp -p wa -k logins
-w /etc/sudoers -p wa -k actions
-w /etc/sudoers.d/ -p wa -k actions
EOF
sudo augenrules --load

# ═══ 5. AUTENTICAZIONE ═══
# 5.1 — Password quality
sudo apt install libpam-pwquality
# /etc/security/pwquality.conf:
# minlen = 14
# dcredit = -1
# ucredit = -1
# ocredit = -1
# lcredit = -1

# 5.2 — Account lockout
# /etc/pam.d/common-auth:
# auth required pam_faillock.so preauth deny=5 unlock_time=900
# auth [success=1 default=ignore] pam_unix.so
# auth [default=die] pam_faillock.so authfail deny=5 unlock_time=900

# 5.3 — Password aging
# /etc/login.defs:
# PASS_MAX_DAYS 365
# PASS_MIN_DAYS 1
# PASS_WARN_AGE 7

# ═══ 6. PERMESSI ═══
# 6.1 — Permessi su file critici
sudo chmod 644 /etc/passwd
sudo chmod 640 /etc/shadow
sudo chmod 644 /etc/group
sudo chmod 640 /etc/gshadow
sudo chmod 600 /etc/ssh/sshd_config
sudo chown root:root /etc/passwd /etc/shadow /etc/group /etc/gshadow
```

### CIS Level 2 — Ubuntu

```bash
# CIS Level 2 — controlli aggiuntivi (possono impattare funzionalità)

# ═══ KERNEL ═══
# Hardening kernel avanzato
cat <<'EOF' | sudo tee /etc/sysctl.d/99-cis-level2.conf
kernel.randomize_va_space = 2
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
kernel.yama.ptrace_scope = 1
kernel.perf_event_paranoid = 3
kernel.unprivileged_bpf_disabled = 1
net.core.bpf_jit_harden = 2
fs.suid_dumpable = 0
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
fs.protected_fifos = 2
fs.protected_regular = 2
EOF
sudo sysctl --system

# ═══ DISABILITARE PROTOCOLLI ═══
cat <<'EOF' | sudo tee /etc/modprobe.d/cis-protocols.conf
install dccp /bin/true
install sctp /bin/true
install rds /bin/true
install tipc /bin/true
EOF

# ═══ AUDIT AVANZATO ═══
cat <<'EOF' | sudo tee /etc/audit/rules.d/cis-level2.rules
-a always,exit -F arch=b64 -S chmod -S fchmod -S fchmodat -k perm_mod
-a always,exit -F arch=b64 -S chown -S fchown -S fchownat -S lchown -k perm_mod
-a always,exit -F arch=b64 -S setxattr -S lsetxattr -S fsetxattr -k perm_mod
-a always,exit -F arch=b64 -S removexattr -S lremovexattr -S fremovexattr -k perm_mod
-a always,exit -F arch=b64 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EACCES -k access
-a always,exit -F arch=b64 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EPERM -k access
-a always,exit -F arch=b64 -S mount -k mounts
-a always,exit -F arch=b64 -S unlink -S unlinkat -S rename -S renameat -k delete
-w /sbin/insmod -p x -k modules
-w /sbin/rmmod -p x -k modules
-w /sbin/modprobe -p x -k modules
-a always,exit -F arch=b64 -S init_module -S delete_module -k modules
-e 2
EOF
sudo augenrules --load

# ═══ CORE DUMP ═══
echo "* hard core 0" | sudo tee -a /etc/security/limits.conf
echo "fs.suid_dumpable = 0" | sudo tee -a /etc/sysctl.d/99-cis-level2.conf

# ═══ BANNER ═══
echo "Authorized access only." | sudo tee /etc/issue
echo "Authorized access only." | sudo tee /etc/issue.net
sudo chmod 644 /etc/issue /etc/issue.net

# ═══ SSH HARDENING ═══
cat <<'EOF' | sudo tee /etc/ssh/sshd_config.d/cis.conf
Protocol 2
LogLevel VERBOSE
MaxAuthTries 4
PermitRootLogin no
PermitEmptyPasswords no
HostbasedAuthentication no
IgnoreRhosts yes
X11Forwarding no
AllowTcpForwarding no
MaxStartups 10:30:60
Banner /etc/issue.net
ClientAliveInterval 300
ClientAliveCountMax 0
LoginGraceTime 60
EOF
sudo systemctl restart sshd
```

### CIS Level 1 — RHEL

```bash
# CIS Benchmark RHEL 8/9 — Level 1

# ═══ FILESYSTEM ═══
# Disabilitare filesystem non necessari
cat <<'EOF' | sudo tee /etc/modprobe.d/cis-filesystem.conf
install cramfs /bin/true
install squashfs /bin/true
install udf /bin/true
install vfat /bin/true
EOF

# Mount /tmp con opzioni restrittive
sudo systemctl unmask tmp.mount
cat <<'EOF' | sudo tee /etc/systemd/system/tmp.mount
[Unit]
Description=Temporary Directory /tmp
[Mount]
What=tmpfs
Where=/tmp
Type=tmpfs
Options=mode=1777,strictatime,nosuid,nodev,noexec,size=2G
[Install]
WantedBy=local-fs.target
EOF
sudo systemctl enable --now tmp.mount

# ═══ SERVIZI ═══
# Rimuovere/disabilitare servizi non necessari
sudo dnf remove xorg-x11-server-common   # Se headless
sudo systemctl disable --now rpcbind
sudo systemctl disable --now nfs-server
sudo systemctl disable --now avahi-daemon
sudo systemctl disable --now cups

# ═══ RETE ═══
cat <<'EOF' | sudo tee /etc/sysctl.d/99-cis-rhel.conf
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.tcp_syncookies = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_ra = 0
net.ipv6.conf.default.accept_ra = 0
EOF
sudo sysctl --system

# ═══ FIREWALL (firewalld) ═══
sudo systemctl enable --now firewalld
sudo firewall-cmd --set-default-zone=public
sudo firewall-cmd --remove-service=cockpit --zone=public --permanent
sudo firewall-cmd --reload

# ═══ AUTENTICAZIONE ═══
# Password quality
sudo dnf install libpwquality
# /etc/security/pwquality.conf:
sudo sed -i 's/^# minlen.*/minlen = 14/' /etc/security/pwquality.conf
sudo sed -i 's/^# dcredit.*/dcredit = -1/' /etc/security/pwquality.conf
sudo sed -i 's/^# ucredit.*/ucredit = -1/' /etc/security/pwquality.conf
sudo sed -i 's/^# ocredit.*/ocredit = -1/' /etc/security/pwquality.conf
sudo sed -i 's/^# lcredit.*/lcredit = -1/' /etc/security/pwquality.conf

# Account lockout (RHEL usa authselect)
sudo authselect select sssd with-faillock --force
# /etc/security/faillock.conf:
# deny = 5
# unlock_time = 900
```

### CIS Level 2 — RHEL

```bash
# CIS Level 2 RHEL — controlli avanzati

# ═══ KERNEL HARDENING ═══
cat <<'EOF' | sudo tee /etc/sysctl.d/99-cis-rhel-l2.conf
kernel.randomize_va_space = 2
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
kernel.yama.ptrace_scope = 1
kernel.perf_event_paranoid = 3
kernel.unprivileged_bpf_disabled = 1
net.core.bpf_jit_harden = 2
fs.suid_dumpable = 0
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
EOF
sudo sysctl --system

# ═══ SELinux (OBBLIGATORIO per CIS RHEL) ═══
# Verificare che sia enforcing
getenforce
# Se non è enforcing:
sudo sed -i 's/^SELINUX=.*/SELINUX=enforcing/' /etc/selinux/config
# Se era disabled → touch /.autorelabel && reboot

# ═══ AUDIT ═══
sudo systemctl enable --now auditd
# Stesse regole audit della sezione CIS Ubuntu Level 2
# /etc/audit/rules.d/cis-rhel.rules
# (Vedi sezione audit per compliance)

# ═══ SSH ═══
cat <<'EOF' | sudo tee /etc/ssh/sshd_config.d/cis-rhel.conf
Protocol 2
LogLevel INFO
MaxAuthTries 4
PermitRootLogin no
PermitEmptyPasswords no
HostbasedAuthentication no
IgnoreRhosts yes
X11Forwarding no
MaxStartups 10:30:60
Banner /etc/issue.net
ClientAliveInterval 300
ClientAliveCountMax 3
LoginGraceTime 60
AllowTcpForwarding no
Ciphers aes256-gcm@openssh.com,aes256-ctr,aes128-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com
KexAlgorithms curve25519-sha256,diffie-hellman-group16-sha512
EOF
sudo systemctl restart sshd

# ═══ VERIFICA COMPLIANCE ═══
# Usare oscap per verifica automatica
sudo dnf install openscap-scanner scap-security-guide
sudo oscap xccdf eval \
  --profile xccdf_org.ssgproject.content_profile_cis \
  --results /tmp/cis-results.xml \
  --report /tmp/cis-report.html \
  /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml
# Aprire cis-report.html per il report dettagliato
```

---

## Security Hardening Checklist Pre-Deployment

```bash
# ═══ CHECKLIST PRE-DEPLOYMENT ═══
# Verificare OGNI punto prima di mettere un server in produzione

# ── SISTEMA OPERATIVO ──
# [ ] OS aggiornato all'ultima versione stable
# [ ] Aggiornamenti sicurezza automatici abilitati (unattended-upgrades)
# [ ] Servizi non necessari disabilitati
# [ ] Compilatori rimossi (gcc, make) se non necessari
# [ ] Core dump disabilitato (fs.suid_dumpable = 0)

# ── KERNEL ──
# [ ] sysctl hardening applicato (/etc/sysctl.d/99-security.conf)
# [ ] ASLR abilitato (kernel.randomize_va_space = 2)
# [ ] Moduli kernel non necessari blacklistati
# [ ] dmesg ristretto (kernel.dmesg_restrict = 1)

# ── UTENTI E AUTENTICAZIONE ──
# [ ] Login root diretto disabilitato
# [ ] Password policy configurata (pwquality)
# [ ] Account lockout configurato (faillock)
# [ ] MFA abilitato per accessi critici
# [ ] Umask restrittivo (027 o 077)
# [ ] Account di servizio con shell nologin

# ── SSH ──
# [ ] PasswordAuthentication no (solo chiavi)
# [ ] PermitRootLogin no
# [ ] AllowUsers/AllowGroups configurato
# [ ] Cifrari deboli rimossi
# [ ] Banner configurato

# ── FIREWALL ──
# [ ] Firewall attivo con policy default DROP
# [ ] Solo porte necessarie aperte
# [ ] Rate limiting su SSH e servizi esposti
# [ ] Anti-spoofing abilitato (rp_filter)

# ── MAC ──
# [ ] SELinux in enforcing (RHEL) o AppArmor attivo (Ubuntu)
# [ ] Profili verificati per tutti i servizi esposti

# ── FILESYSTEM ──
# [ ] /tmp montato con nosuid,nodev,noexec
# [ ] File sensibili con permessi corretti (shadow, sshd_config)
# [ ] SUID/SGID non necessari rimossi
# [ ] World-writable files/directories verificati

# ── CRITTOGRAFIA ──
# [ ] Disco dati criptato (LUKS) se richiesto
# [ ] TLS configurato per tutti i servizi di rete
# [ ] Certificati TLS validi e non scaduti
# [ ] Chiavi SSH host rigenerate (se da template)

# ── AUDIT E MONITORING ──
# [ ] auditd abilitato con regole per file critici
# [ ] Log centralizzati su server remoto
# [ ] fail2ban abilitato per SSH e servizi web
# [ ] AIDE database inizializzato
# [ ] Monitoring attivo (uptime, spazio disco, processi)

# ── BACKUP ──
# [ ] Backup automatizzato e testato
# [ ] Backup criptato
# [ ] Restore testato (verifica periodica)
# [ ] Header LUKS backuppato (se disco criptato)

# ── RETE ──
# [ ] Nessun servizio non necessario in ascolto (ss -tuln)
# [ ] DNS resolver non pubblico (se non è DNS server)
# [ ] NTP configurato e funzionante
# [ ] IPv6 disabilitato se non usato

# ── DOCUMENTAZIONE ──
# [ ] Inventario servizi e porte documentato
# [ ] Playbook incident response disponibile
# [ ] Contatti di escalation aggiornati
# [ ] Change log delle configurazioni
```

---

## Troubleshooting

**"SELinux blocca il mio servizio"** → `sudo ausearch -m AVC -ts recent` per vedere cosa è bloccato. `sudo audit2allow -a` per suggerimenti. Spesso basta un `setsebool -P`. Verificare anche i contesti file con `ls -Z` e ripristinare con `restorecon -Rv`.

**"PAM: authentication failure"** → `journalctl -u systemd-logind` e `/var/log/auth.log` per dettagli. Verificare `/etc/pam.d/` per il servizio in questione. Un modulo PAM in ordine sbagliato può bloccare tutta l'autenticazione.

**"Account bloccato (troppi tentativi)"** → Se fail2ban: `fail2ban-client set sshd unbanip IP`. Se PAM faillock: `faillock --user username --reset`. Verificare anche se l'account è scaduto con `chage -l username`.

**"LUKS: No key available"** → Passphrase sbagliata. Se keyfile: verificare che il file esista e sia leggibile. `cryptsetup luksDump /dev/sdX` per verificare quanti key slot sono attivi. Se si è persa la passphrase e non c'è keyfile di backup: i dati sono persi.

**"AppArmor blocca l'applicazione dopo aggiornamento"** → I percorsi dei binari o delle librerie potrebbero essere cambiati. Mettere il profilo in complain (`aa-complain /etc/apparmor.d/profile`), riprodurre il problema, usare `aa-logprof` per aggiornare il profilo, rimettere in enforce.

**"auditd: dispatch error"** → Il buffer audit è pieno. Aumentare il buffer in `/etc/audit/auditd.conf`: `log_group = root`, `max_log_file_action = ROTATE`, `num_logs = 10`. Se il disco è pieno, liberare spazio e ruotare i log.

**"fail2ban non banna gli attaccanti"** → Verificare: 1) il jail è enabled (`fail2ban-client status`), 2) il logpath è corretto, 3) il filtro regex matcha il formato dei log, 4) il backend è corretto (auto, systemd, o polling). Test del filtro: `fail2ban-regex /var/log/auth.log /etc/fail2ban/filter.d/sshd.conf`.

**"Firewall blocca il traffico legittimo"** → Verificare le regole: `iptables -L -n -v` o `nft list ruleset`. I contatori dei pacchetti mostrano quale regola ha matchato. Aggiungere logging temporaneo: `iptables -I INPUT -j LOG --log-prefix "DEBUG: "`.

**"Conntrack table full"** → `dmesg | grep conntrack`. Aumentare il limite: `sysctl -w net.nf_conntrack_max=524288`. Ridurre i timeout per connessioni inattive. Verificare se c'è un attacco DDoS in corso con `conntrack -L | wc -l`.

**"Impossibile caricare modulo kernel dopo hardening"** → Se `kernel.modules_disabled = 1` è stato impostato, è necessario un reboot per caricare nuovi moduli. Se il modulo non è firmato e `CONFIG_MODULE_SIG_FORCE=y`, compilare il modulo con la chiave corretta.

**"Permesso negato nonostante chmod corretto"** → Verificare: 1) ACL con `getfacl`, 2) SELinux/AppArmor con `ls -Z` o `aa-status`, 3) attributi con `lsattr`, 4) flag immutabile (`chattr +i` attivo). Il problema è spesso su uno di questi layer aggiuntivi.

**"AIDE segnala file modificati dopo aggiornamento"** → Falso positivo se i file sono stati aggiornati dal package manager. Verificare con `dpkg -V` o `rpm -Va`. Se le modifiche sono legittime, aggiornare il database: `aide --update && cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db`.

**"SSH connection refused dopo hardening"** → Verificare: 1) sshd è in esecuzione (`systemctl status sshd`), 2) la porta è corretta (`ss -tlnp | grep ssh`), 3) il firewall permette la connessione (`iptables -L -n | grep 22`), 4) la configurazione è valida (`sshd -t`), 5) l'utente è nell'AllowUsers/AllowGroups.

**"Brute force SSH rilevato"** → 1) Verificare fail2ban status: `fail2ban-client status sshd`. 2) Controllare IP con più tentativi: `grep "Failed password" /var/log/auth.log | awk '{print $11}' | sort | uniq -c | sort -rn`. 3) Verificare se gli IP sono già bannati. 4) Considerare di spostare SSH su porta non standard o di usare port knocking.

**"Sospetta compromissione: processi sconosciuti"** → 1) Non terminare i processi immediatamente. 2) Identificare: `ps auxf`, `ls -la /proc/PID/exe`, `cat /proc/PID/cmdline`. 3) Verificare connessioni di rete: `ss -tnp | grep PID`. 4) Verificare file aperti: `lsof -p PID`. 5) Se confermato sospetto, seguire il workflow di incident response.

**"Privilege escalation: utente ha ottenuto root"** → 1) Verificare sudo log: `grep sudo /var/log/auth.log`. 2) Verificare su log: `grep su /var/log/auth.log`. 3) Verificare binari SUID: `find / -perm -4000 -newer /etc/passwd 2>/dev/null`. 4) Verificare kernel exploit: `dmesg | tail -50`. 5) Verificare crontab: `crontab -l -u utente_sospetto`.

**"Il server ha traffico di rete anomalo in uscita"** → Possibile data exfiltration o C2 (Command & Control). 1) Identificare connessioni: `ss -tnp | grep ESTABLISHED`. 2) Catturare traffico: `tcpdump -i eth0 -w /tmp/capture.pcap`. 3) Identificare i processi: `ss -tnp | grep IP_SOSPETTO`. 4) Verificare DNS sospetti: `tcpdump -i eth0 port 53`. 5) Bloccare temporaneamente: `iptables -A OUTPUT -d IP_SOSPETTO -j DROP`.

**"Crypto miner rilevato sul server"** → 1) Identificare il processo: `top` (cercare CPU 100%), `ps aux | sort -k3 -rn | head`. 2) Trovare il binario: `ls -la /proc/PID/exe`. 3) Verificare come è entrato: persistenza in crontab, systemd, `.bashrc`. 4) Terminare e rimuovere. 5) Patchare il vettore d'ingresso. 6) Verificare se ci sono altre backdoor.

**"Chiave SSH compromessa"** → 1) Revocare immediatamente la chiave: rimuovere la pubkey da `~/.ssh/authorized_keys` su tutti i server. 2) Generare una nuova coppia di chiavi. 3) Verificare accessi con la chiave compromessa nei log. 4) Controllare se l'attaccante ha inserito proprie chiavi in authorized_keys.

**"Certificato TLS scaduto o invalido"** → 1) Verificare: `openssl s_client -connect host:443 -servername host 2>/dev/null | openssl x509 -noout -dates`. 2) Rinnovare con certbot: `certbot renew --dry-run`. 3) Verificare che il cron di rinnovo sia attivo: `systemctl status certbot.timer`.

**"rkhunter segnala warning"** → Non tutti i warning sono compromissioni. Verificare: 1) `cat /var/log/rkhunter.log` per dettagli. 2) Confrontare i binari segnalati con il package manager: `dpkg -V pacchetto`. 3) Aggiornare le firme dopo aggiornamenti di sistema: `rkhunter --propupd`. 4) Falsi positivi comuni: inetd, xinetd modificati dopo aggiornamento.

---

## FAQ

**D: SELinux o AppArmor? Quale scegliere?**
R: Dipende dalla distribuzione. RHEL/Fedora/CentOS → SELinux (pre-installato, policy complete). Debian/Ubuntu/SUSE → AppArmor (pre-installato, più semplice). Non cambiare: la distro è ottimizzata per il proprio MAC. Se servono policy MLS/MCS (classificazione militare), SELinux è l'unica opzione.

**D: Posso disabilitare SELinux per risolvere un problema?**
R: No. `setenforce 0` (permissive) è accettabile per debug temporaneo. `SELINUX=disabled` è una pratica che elimina un intero layer di sicurezza. Risolvere il problema con `audit2allow`, boolean o contesti corretti è sempre preferibile.

**D: LUKS rallenta il disco?**
R: L'overhead di LUKS con AES-NI (istruzioni hardware presenti su qualsiasi CPU moderna) è circa 1-5% per I/O sequenziale. Per la maggior parte dei workload è trascurabile. Verificare con `cryptsetup benchmark`.

**D: Quanto deve essere lunga una password?**
R: CIS raccomanda minimo 14 caratteri. NIST SP 800-63B (2020) raccomanda minimo 8 ma preferibilmente passphrase lunghe. Una passphrase di 4+ parole casuali (es. "cavallo batteria graffetta corretto") è più sicura e più memorizzabile di "P@ssw0rd!23".

**D: Come gestire i falsi positivi di fail2ban?**
R: Aggiungere gli IP fidati a `ignoreip` in `/etc/fail2ban/jail.local`. Per utenti che sbagliano spesso la password, considerare MFA con chiave hardware anziché password. Monitorare `/var/log/fail2ban.log` per ban non intenzionali.

**D: Ogni quanto eseguire scan di vulnerabilità?**
R: Lynis: settimanale (leggero, locale). OpenVAS/Nessus: mensile per scan completo, settimanale per scan credenziali su sistemi critici. AIDE: giornaliero (file integrity). rkhunter: settimanale.

**D: I container sono isolati come le VM?**
R: No. I container condividono il kernel dell'host. Un exploit kernel nel container compromette l'host. Le VM hanno isolamento hardware (hypervisor). Per workload con requisiti di isolamento forte, usare VM o gVisor/Kata Containers (che eseguono un micro-kernel per ogni container).

**D: Come proteggere le chiavi LUKS?**
R: 1) Backup dell'header LUKS su storage separato e sicuro. 2) Usare keyfile + passphrase (due fattori). 3) Conservare la passphrase in un password manager o cassaforte fisica. 4) Considerare TPM per il boot automatico su hardware trusted.

**D: Perché i miei log non mostrano nulla dopo una compromissione?**
R: L'attaccante con root può cancellare i log locali. Soluzioni: 1) `chattr +a` sui log (append-only). 2) Centralizzare i log su server remoto in tempo reale. 3) Usare Wazuh/SIEM. 4) Il log centralizzato è l'unica garanzia che i log sopravvivano.

**D: Come hardening un server già in produzione senza downtime?**
R: 1) Iniziare con sysctl (applicabili a caldo). 2) Firewall regole additive (non flush in produzione). 3) AppArmor/SELinux in permissive (solo logging). 4) Abilitare auditd (non richiede restart). 5) fail2ban (servizio separato). 6) Per SSH, fare test con una seconda sessione prima di chiudere quella corrente.

**D: Qual è il rischio di `kernel.modules_disabled = 1`?**
R: Dopo l'impostazione, nessun nuovo modulo kernel può essere caricato fino al reboot. Questo significa: nessun nuovo driver, nessun nuovo filesystem, nessun modulo iptables aggiuntivo. Usare solo su server con configurazione stabile e testata. Non usare durante il setup iniziale.

**D: Come verificare se il server è stato compromesso?**
R: 1) AIDE check (file modificati). 2) rkhunter + chkrootkit (rootkit). 3) Verificare utenti/gruppi aggiunti: `diff <(getent passwd) backup_passwd`. 4) Verificare crontab: `for u in $(cut -d: -f1 /etc/passwd); do crontab -l -u $u 2>/dev/null; done`. 5) Verificare authorized_keys: `find / -name authorized_keys 2>/dev/null`. 6) Verificare binari: `dpkg -V` o `rpm -Va`. 7) Verificare connessioni: `ss -tnp`.

**D: Come funziona il secure boot e serve su server Linux?**
R: Secure Boot verifica che ogni componente della catena di boot (firmware → bootloader → kernel → moduli) sia firmato con chiave trusted. Su server: protegge da bootkit e da modifica del kernel/initramfs. Raccomandato se il server è accessibile fisicamente (datacenter condiviso, edge).

**D: Devo crittografare il disco del server in datacenter?**
R: Dipende dal modello di minaccia. Se il datacenter è fidato e il server non lascia mai il rack → LUKS è opzionale (protegge solo da furto fisico). Se compliance richiede encryption at rest (PCI-DSS, HIPAA) → LUKS obbligatorio. Se il server potrebbe essere dismesso senza wiping → LUKS protegge i dati residui.

**D: Come gestire security update che richiedono reboot?**
R: 1) `needrestart` mostra quali servizi necessitano restart. 2) Kernel update senza reboot: `kexec` (rischi) o Canonical Livepatch / RHEL kpatch per patch kernel a caldo. 3) Per reboot pianificato: programmare finestra di manutenzione, usare load balancer per zero-downtime.

**D: Il mio server deve avere un antivirus?**
R: I server Linux non richiedono antivirus tradizionale nella maggior parte dei casi. Eccezioni: 1) File server che serve client Windows (ClamAV per scansionare i file condivisi). 2) Mail server (scansione allegati). 3) Compliance che lo richiede esplicitamente. Preferire invece: MAC, IDS, file integrity monitoring, aggiornamenti tempestivi.

**D: Come gestire le chiavi SSH per un team?**
R: 1) Ogni membro ha la propria coppia di chiavi (mai condivise). 2) Distribuire le chiavi con strumenti di configuration management (Ansible, Puppet). 3) Ruotare le chiavi annualmente. 4) Usare SSH Certificate Authority per ambienti grandi. 5) Revocare immediatamente le chiavi di chi lascia il team.

**D: Qual è la differenza tra IDS e IPS?**
R: IDS (Intrusion Detection System) monitora e segnala attività sospette (passivo). IPS (Intrusion Prevention System) blocca automaticamente le minacce (attivo). AIDE e Wazuh sono IDS. fail2ban agisce come IPS (banna gli IP). Suricata può funzionare sia come IDS che IPS.

**D: Come proteggere un server esposto a internet con budget zero?**
R: 1) Firewall con iptables/nftables (incluso). 2) fail2ban per SSH e web (gratuito). 3) AppArmor profili per servizi esposti (incluso in Ubuntu). 4) auditd per logging (incluso). 5) AIDE per file integrity (gratuito). 6) Lynis per audit periodico (gratuito). 7) unattended-upgrades per patch automatiche (incluso). 8) Let's Encrypt per TLS (gratuito). 9) SSH con solo chiavi (nessun costo). Tutto questo copre il 90% delle necessità di sicurezza.

**D: Quanto spesso devo controllare i log di sicurezza?**
R: Ideale: monitoraggio continuo automatizzato con alert (Wazuh, ELK). Minimo accettabile: review giornaliera di auth.log e audit log. I log non letti sono inutili. Automatizzare la ricerca di pattern sospetti con script e cron job.

---

## Best Practices

1. **Principio del minimo privilegio**: ogni utente e processo ha solo i permessi strettamente necessari. sudo con comandi specifici, non `ALL`
2. **Defense in depth**: non affidarsi a una sola misura. Combinare: firewall + SELinux/AppArmor + audit + fail2ban + hardening
3. **Aggiornamenti automatici per security**: `unattended-upgrades` per patch di sicurezza. Le vulnerabilità note sono il vettore d'attacco più comune
4. **Audit tutto**: auditd per file sensibili e comandi root. Centralizzare i log (non tenere solo in locale — l'attaccante può cancellarli)
5. **Crittografia a riposo**: LUKS per dati sensibili su disco. La crittografia protegge in caso di furto fisico del disco
6. **Scan periodico**: Lynis/OpenSCAP almeno mensilmente. Automatizzare il report e monitorare il trend
7. **Backup delle chiavi**: le chiavi GPG, LUKS e SSH devono essere salvate in modo sicuro. Perdere la chiave LUKS = perdere i dati per sempre
8. **Separazione dei doveri**: chi amministra non è chi audita. Chi deploya non ha accesso ai dati di produzione. Utenti diversi per compiti diversi
9. **Immutabilità dove possibile**: flag immutabile su file critici, container read-only, infrastruttura immutabile (rebuild anziché patch)
10. **Incident response plan testato**: un piano che non è stato mai provato non funzionerà durante un incidente reale. Esercitazioni periodiche (tabletop o live)
11. **Documentazione aggiornata**: inventario dei servizi, porte aperte, utenti, policy. La documentazione obsoleta è pericolosa quanto la mancanza di documentazione
12. **Segmentazione di rete**: i servizi non devono poter raggiungere tutto. Database solo dalla rete applicativa, management separato dal traffico utente
13. **Monitoraggio delle dipendenze**: le librerie third-party sono un vettore d'attacco. Scan periodico per CVE nelle dipendenze (Trivy, Grype, Dependabot)
14. **Rotazione credenziali**: password, chiavi SSH, token API, certificati TLS — tutto ha una scadenza. Automatizzare la rotazione dove possibile
15. **Assume breach**: progettare assumendo che l'attaccante sia già dentro. Logging, segmentazione e least privilege limitano il danno di una compromissione

---

> **Riferimenti**: `man pam.d`, `man selinux`, `man apparmor.d`, `man auditctl`, `man cryptsetup`, `man sysctl.conf`, `man iptables`, `man nft`, `man sshd_config`, CIS Benchmarks (cisecurity.org), NIST SP 800-123, NIST SP 800-63B
