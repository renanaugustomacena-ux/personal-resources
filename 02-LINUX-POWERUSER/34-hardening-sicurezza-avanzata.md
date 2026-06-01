---
Modulo del corso: "Linux per ingegneri di sistema"
Prerequisiti:
  - Amministrazione Linux intermedia (utenti, permessi, systemd, networking)
  - Familiarità con la riga di comando e gli editor di testo (vim/nano)
  - Conoscenza base di TCP/IP, firewall e concetti di sicurezza informatica
  - Esperienza con package manager (apt, dnf/yum)
Obiettivi:
  1. Applicare framework di hardening (CIS Benchmarks, DISA STIG, NIST SP 800-123) a sistemi Debian e RHEL
  2. Configurare il kernel hardening avanzato incluso lockdown mode, ASLR, Yama LSM
  3. Implementare boot sicuro con UEFI Secure Boot, GRUB2 password e measured boot TPM 2.0
  4. Progettare policy di audit con auditd e file integrity monitoring (AIDE, osquery)
  5. Applicare hardening di servizi systemd con sandboxing completo (ProtectSystem, namespaces, capabilities)
  6. Preparare il sistema per incident response con forensic readiness e log retention
Tempo stimato: 18-24 ore
Livello: proficient
Ultimo aggiornamento: 2026-05-23
Versioni di riferimento: CIS Benchmark v3.0.0+, Lynis 3.1.4+, OpenSCAP 1.4+, auditd 3.1+
---

# Hardening e Sicurezza Avanzata Linux — Guida Completa

> **Modulo 34** · **Aggiornamento:** 2026-05-23

## Mappa Concettuale

```
                     ┌─────────────────────────────┐
                     │   HARDENING LINUX            │
                     │   SICUREZZA AVANZATA         │
                     └──────────┬──────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
 ┌──────▼──────┐        ┌──────▼──────┐        ┌──────▼──────┐
 │  FRAMEWORK  │        │   SISTEMA   │        │ MONITORAGGIO│
 │  CIS L1/L2  │        │  Boot+Kernel│        │ E RISPOSTA  │
 │  DISA STIG  │        │  FS+Servizi │        │  INCIDENTI  │
 │  NIST 800-  │        │  Rete+SSH   │        │             │
 │  123        │        │  MAC+LUKS   │        │             │
 └──────┬──────┘        └──────┬──────┘        └──────┬──────┘
        │                      │                      │
  ┌─────┼─────┐       ┌───────┼───────┐       ┌──────┼──────┐
  ▼     ▼     ▼       ▼       ▼       ▼       ▼      ▼      ▼
Lynis OpenSCAP Ansi- SELinux systemd  User   auditd  FIM   Forensic
audit scanner  ble-  AppArm. sandbox  PAM    AIDE  osquery Readiness
             lockdown nftables Fail2Ban sudo  rkhunter     Log Reten.
```

## Idee guida
1. **CIS Benchmark Debian/RHEL: 200+ controls.**
2. **Kernel hardening: kASLR, SMEP/SMAP, KASLR.**
3. **Auditd: log syscall + file access.**
4. **Hardened kernel (Grsecurity: paid; linux-hardened: free).**


## Indice

- [Panoramica](#panoramica)
- [CIS Benchmarks — Implementazione](#cis-benchmarks--implementazione)
- [SELinux — Deep Dive](#selinux--deep-dive)
- [AppArmor — Profili e Gestione](#apparmor--profili-e-gestione)
- [Kernel Hardening con sysctl](#kernel-hardening-con-sysctl)
- [Firewall con nftables](#firewall-con-nftables)
- [Fail2Ban — Protezione dai Brute Force](#fail2ban--protezione-dai-brute-force)
- [SSH Hardening Avanzato](#ssh-hardening-avanzato)
- [File Integrity Monitoring](#file-integrity-monitoring)
- [Rootkit Detection](#rootkit-detection)
- [Audit Framework — auditd](#audit-framework--auditd)
- [Disk Encryption con LUKS](#disk-encryption-con-luks)
- [PAM — Configurazione e Hardening](#pam--configurazione-e-hardening)
- [Sudo Hardening](#sudo-hardening)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Framework di Hardening a Confronto](#framework-di-hardening-a-confronto)
- [Boot Security — UEFI, GRUB2, TPM 2.0](#boot-security--uefi-grub2-tpm-20)
- [Kernel Lockdown Mode e Restrizioni kexec](#kernel-lockdown-mode-e-restrizioni-kexec)
- [Filesystem Hardening Avanzato](#filesystem-hardening-avanzato)
- [User Account Hardening](#user-account-hardening)
- [Network Hardening Avanzato](#network-hardening-avanzato)
- [Systemd Service Hardening](#systemd-service-hardening)
- [SSH — Restrizioni authorized_keys](#ssh--restrizioni-authorized_keys)
- [File Integrity Monitoring Avanzato](#file-integrity-monitoring-avanzato)
- [Scansione Automatizzata — Lynis e OpenSCAP](#scansione-automatizzata--lynis-e-openscap)
- [Container Host Hardening](#container-host-hardening)
- [Preparazione agli Incidenti — Forensic Readiness](#preparazione-agli-incidenti--forensic-readiness)
- [Automazione CIS Benchmark — Compliance-as-Code](#automazione-cis-benchmark--compliance-as-code)
- [USBGuard — Protezione da Dispositivi USB Malevoli](#usbguard--protezione-da-dispositivi-usb-malevoli)
- [OSSEC HIDS — Intrusion Detection Host-Based](#ossec-hids--intrusion-detection-host-based)
- [Confronto MAC — SELinux vs AppArmor vs TOMOYO](#confronto-mac--selinux-vs-apparmor-vs-tomoyo)
- [Protezione della Memoria — Deep Dive](#protezione-della-memoria--deep-dive)
- [Esercizi Pratici](#esercizi-pratici)
- [Auto-valutazione](#auto-valutazione)
- [Letture Primarie](#letture-primarie)
- [Collegamenti Incrociati](#collegamenti-incrociati)
- [Glossario Locale](#glossario-locale)
- [Riferimenti](#riferimenti)

---

## Panoramica

L'hardening di un sistema Linux è il processo sistematico di riduzione della superficie di attacco. Non si tratta di installare un singolo tool, ma di applicare layer multipli di difesa (defense in depth) che, combinati, rendono il sistema significativamente più resistente a compromissioni.

Questo documento copre le tecniche avanzate di hardening: dai framework di riferimento come i CIS Benchmarks, ai Mandatory Access Control (SELinux, AppArmor), al kernel hardening, alla crittografia del disco, all'auditing. Ogni sezione include configurazioni reali, comandi e spiegazioni dettagliate del "perché" dietro ogni scelta.

### Principi Fondamentali

```
1. LEAST PRIVILEGE — Ogni utente, processo, servizio ha solo i permessi
   strettamente necessari per la propria funzione. Niente di più.

2. DEFENSE IN DEPTH — Multipli layer di sicurezza. Se uno cede, gli altri
   proteggono. Non affidarsi mai a un singolo controllo.

3. FAIL SECURE — In caso di errore, il sistema deve negare l'accesso,
   non permetterlo. Default deny, non default allow.

4. MINIMIZE ATTACK SURFACE — Rimuovere tutto ciò che non serve:
   pacchetti, servizi, porte, utenti, permessi SUID.

5. AUDIT EVERYTHING — Ciò che non si monitora non si può difendere.
   Log, audit, alerting su ogni evento significativo.
```

---

## CIS Benchmarks — Implementazione

I CIS (Center for Internet Security) Benchmarks sono lo standard de facto per l'hardening dei sistemi operativi. Forniscono checklist dettagliate con due livelli:

- **Level 1**: raccomandazioni base, basso impatto operativo, applicabili ovunque
- **Level 2**: hardening aggressivo, possibile impatto sulla funzionalità, per ambienti ad alta sicurezza

### Audit Automatico con CIS-CAT o Lynis

```bash
# Lynis — audit di sicurezza open-source
sudo apt install -y lynis    # Debian/Ubuntu
sudo dnf install -y lynis    # RHEL/CentOS

# Eseguire un audit completo
sudo lynis audit system

# Output parziale:
# [+] Boot and services
# ------------------------------------
#   - Checking presence GRUB2                    [ FOUND ]
#   - Checking boot loader password              [ WARNING ]
#
# [+] Kernel hardening
# ------------------------------------
#   - Comparing sysctl key pairs                 [ OK ]
#   - kernel.randomize_va_space (ASLR)           [ OK ]
#   - kernel.sysrq                               [ HARDENED ]
#
# Hardening index : 72 [##############        ]
# Tests performed : 256

# Eseguire solo una categoria
sudo lynis audit system --tests-from-group "firewalls"

# Report dettagliato
sudo lynis audit system --report-file /tmp/lynis-report.dat
```

### Implementazione delle Raccomandazioni CIS Principali

#### Filesystem Hardening

```bash
# 1. Partizioni separate per /tmp, /var, /var/log, /var/tmp, /home
# Verificare
df -h /tmp /var /var/log /home

# 2. Opzioni di mount restrittive
# /etc/fstab — aggiungere nodev, nosuid, noexec dove appropriato:
# /tmp:     defaults,nodev,nosuid,noexec
# /var/tmp: defaults,nodev,nosuid,noexec (o bind mount da /tmp)
# /home:    defaults,nodev,nosuid
# /dev/shm: defaults,nodev,nosuid,noexec

# Applicare senza reboot
sudo mount -o remount,nodev,nosuid,noexec /tmp
sudo mount -o remount,nodev,nosuid,noexec /dev/shm

# 3. Disabilitare il mounting automatico di filesystem non necessari
cat > /etc/modprobe.d/cis-filesystem.conf << 'EOF'
install cramfs /bin/false
install freevxfs /bin/false
install jffs2 /bin/false
install hfs /bin/false
install hfsplus /bin/false
install squashfs /bin/false
install udf /bin/false
install vfat /bin/false
EOF

# 4. Permessi su file critici
sudo chmod 644 /etc/passwd
sudo chmod 640 /etc/shadow
sudo chmod 644 /etc/group
sudo chmod 640 /etc/gshadow
sudo chmod 600 /boot/grub2/grub.cfg
sudo chmod 600 /etc/crontab
sudo chmod 700 /etc/cron.d
sudo chmod 700 /etc/cron.daily
sudo chmod 700 /etc/cron.hourly
sudo chmod 700 /etc/cron.monthly
sudo chmod 700 /etc/cron.weekly

# 5. Trovare e rimuovere SUID/SGID non necessari
sudo find / -xdev -type f \( -perm -4000 -o -perm -2000 \) -print 2>/dev/null
# Rimuovere SUID da binari non necessari:
# sudo chmod u-s /usr/bin/wall
# sudo chmod g-s /usr/bin/write
```

#### Servizi e Demoni

```bash
# Elencare servizi attivi
systemctl list-units --type=service --state=running

# Disabilitare servizi non necessari (CIS raccomanda di rimuovere)
sudo systemctl disable --now avahi-daemon
sudo systemctl disable --now cups
sudo systemctl disable --now rpcbind
sudo systemctl disable --now nfs-server
sudo systemctl disable --now vsftpd
sudo systemctl disable --now dovecot
sudo systemctl disable --now smb
sudo systemctl disable --now squid
sudo systemctl disable --now snmpd
sudo systemctl disable --now ypserv
sudo systemctl disable --now telnet.socket

# Verificare che nessun servizio ascolti su porte non necessarie
ss -tulnp | grep LISTEN
```

#### Password Policy

```bash
# /etc/login.defs — policy per nuove password
PASS_MAX_DAYS   365
PASS_MIN_DAYS   7
PASS_MIN_LEN    14
PASS_WARN_AGE   14

# Per utenti esistenti
sudo chage --maxdays 365 --mindays 7 --warndays 14 username

# /etc/security/pwquality.conf — complessità password
minlen = 14
dcredit = -1          # Almeno 1 cifra
ucredit = -1          # Almeno 1 maiuscola
ocredit = -1          # Almeno 1 carattere speciale
lcredit = -1          # Almeno 1 minuscola
minclass = 4          # Almeno 4 classi di caratteri
maxrepeat = 3         # Massimo 3 caratteri ripetuti consecutivamente
maxsequence = 3       # Massimo 3 caratteri in sequenza (abc, 123)
dictcheck = 1         # Controlla contro dizionario
enforcing = 1         # Applica le regole

# Bloccare account dopo tentativi falliti
# Configurare via PAM (vedi sezione PAM)
```

---

## SELinux — Deep Dive

SELinux (Security-Enhanced Linux) è un sistema di Mandatory Access Control (MAC) sviluppato dalla NSA. A differenza dei permessi Unix tradizionali (DAC — Discretionary Access Control), SELinux applica policy di sicurezza che nemmeno root può bypassare.

### Concetti Fondamentali

```
DAC (Discretionary Access Control):
  → Il proprietario del file decide chi può accedere
  → root può fare tutto
  → Un processo compromesso che gira come root ha accesso a TUTTO

MAC (Mandatory Access Control / SELinux):
  → La POLICY decide chi può accedere a cosa
  → Anche root è limitato dalla policy
  → Un processo compromesso è confinato al suo dominio
  → Ogni file, processo, porta ha un CONTESTO di sicurezza
```

### Modalità di SELinux

```bash
# Verificare lo stato corrente
getenforce
# Output: Enforcing, Permissive, o Disabled

sestatus
# Output:
# SELinux status:                 enabled
# SELinuxfs mount:                /sys/fs/selinux
# SELinux root directory:         /etc/selinux
# Loaded policy name:             targeted
# Current mode:                   enforcing
# Mode from config file:          enforcing
# Policy MLS status:              enabled
# Policy deny_unknown status:     allowed
# Memory protection checking:     actual (secure)

# Cambiare modalità temporaneamente
sudo setenforce 0    # Permissive (logga ma non blocca)
sudo setenforce 1    # Enforcing (logga e blocca)

# Cambiare modalità permanentemente
# /etc/selinux/config
SELINUX=enforcing     # enforcing | permissive | disabled
SELINUXTYPE=targeted  # targeted | minimum | mls
```

**ATTENZIONE**: passare da `disabled` a `enforcing` richiede un relabel completo del filesystem:

```bash
# Creare il file .autorelabel e rebootare
sudo touch /.autorelabel
sudo reboot
# Il primo boot sarà molto lungo (relabel di tutti i file)
```

### Contesti di Sicurezza

Ogni oggetto in SELinux ha un contesto nel formato `user:role:type:level`:

```bash
# Visualizzare il contesto dei file
ls -Z /var/www/html/
# -rw-r--r--. root root unconfined_u:object_r:httpd_sys_content_t:s0 index.html

# Visualizzare il contesto dei processi
ps auxZ | grep httpd
# system_u:system_r:httpd_t:s0    root  1234 ... /usr/sbin/httpd

# Visualizzare il contesto delle porte
sudo semanage port -l | grep http
# http_port_t   tcp   80, 81, 443, 488, 8008, 8009, 8443, 9000
```

Il campo più importante è il **type** (terzo campo):
- `httpd_sys_content_t` — file che Apache può leggere
- `httpd_t` — dominio in cui gira Apache
- `http_port_t` — porte su cui Apache può ascoltare

La policy definisce che il processo nel dominio `httpd_t` può leggere file con tipo `httpd_sys_content_t` e ascoltare su porte `http_port_t`.

### Gestione dei Contesti

```bash
# Cambiare il contesto di un file (temporaneo, si perde con relabel)
sudo chcon -t httpd_sys_content_t /var/www/custom/index.html

# Cambiare il contesto in modo permanente (sopravvive al relabel)
sudo semanage fcontext -a -t httpd_sys_content_t "/srv/web(/.*)?"
sudo restorecon -Rv /srv/web

# Ripristinare il contesto di default
sudo restorecon -Rv /var/www/html

# Verificare il contesto atteso vs attuale
sudo matchpathcon /var/www/html/index.html
# /var/www/html/index.html    system_u:object_r:httpd_sys_content_t:s0
```

### Booleans

I booleans sono interruttori on/off per funzionalità specifiche della policy:

```bash
# Elencare tutti i booleans
sudo getsebool -a

# Elencare booleans relativi a httpd
sudo getsebool -a | grep httpd
# httpd_can_network_connect --> off
# httpd_can_network_connect_db --> off
# httpd_can_sendmail --> off
# httpd_enable_cgi --> on
# httpd_enable_homedirs --> off
# httpd_read_user_content --> off
# httpd_use_nfs --> off

# Abilitare un boolean (temporaneo)
sudo setsebool httpd_can_network_connect on

# Abilitare un boolean (permanente, sopravvive al reboot)
sudo setsebool -P httpd_can_network_connect on

# Scenari comuni:
# Apache deve connettersi a un backend (API, database remoto)
sudo setsebool -P httpd_can_network_connect on

# Apache deve connettersi a un database
sudo setsebool -P httpd_can_network_connect_db on

# Apache deve servire file dalle home directory
sudo setsebool -P httpd_enable_homedirs on

# Samba deve condividere home directory
sudo setsebool -P samba_enable_home_dirs on

# NFS deve essere usato da httpd
sudo setsebool -P httpd_use_nfs on
```

### Troubleshooting SELinux

```bash
# 1. Controllare i log di audit
sudo ausearch -m AVC -ts recent
# Output:
# type=AVC msg=audit(1712930400.123:456): avc:  denied  { read } for
#   pid=1234 comm="httpd" name="config.php" dev="sda1" ino=654321
#   scontext=system_u:system_r:httpd_t:s0
#   tcontext=unconfined_u:object_r:user_home_t:s0
#   tclass=file permissive=0

# 2. Usare sealert per messaggi leggibili
sudo sealert -a /var/log/audit/audit.log
# Fornisce spiegazioni in linguaggio naturale e suggerimenti

# 3. Generare policy personalizzate con audit2allow
# Prima raccogliere i denial:
sudo ausearch -m AVC -ts recent | audit2allow -m mymodule
# Output:
# module mymodule 1.0;
# require {
#     type httpd_t;
#     type user_home_t;
#     class file read;
# }
# allow httpd_t user_home_t:file read;

# Generare e installare il modulo
sudo ausearch -m AVC -ts recent | audit2allow -M mymodule
sudo semodule -i mymodule.pp

# 4. Diagnosi completa con setroubleshoot
sudo dnf install -y setroubleshoot-server
# I messaggi appariranno in /var/log/messages con soluzioni suggerite

# 5. Workflow di troubleshooting
# a. Mettere SELinux in permissive per confermare che è lui il problema
sudo setenforce 0
# b. Testare se il servizio funziona
# c. Raccogliere i denial dal log
sudo ausearch -m AVC -ts recent
# d. Applicare le correzioni (contesto, boolean, o policy custom)
# e. Rimettere in enforcing
sudo setenforce 1
# f. Verificare
```

### Aggiungere Porte Personalizzate

```bash
# Apache deve ascoltare sulla porta 8443
sudo semanage port -a -t http_port_t -p tcp 8443

# Verificare
sudo semanage port -l | grep http_port_t

# SSH deve ascoltare sulla porta 2222
sudo semanage port -a -t ssh_port_t -p tcp 2222

# Rimuovere una porta personalizzata
sudo semanage port -d -t http_port_t -p tcp 8443
```

---

## AppArmor — Profili e Gestione

AppArmor è il MAC utilizzato da Debian, Ubuntu e SUSE. A differenza di SELinux che usa etichette (label-based), AppArmor usa path-based access control — le policy sono basate sui percorsi dei file.

### Stato e Gestione

```bash
# Verificare lo stato
sudo aa-status
# Output:
# apparmor module is loaded.
# 38 profiles are loaded.
# 38 profiles are in enforce mode.
# 0 profiles are in complain mode.
# 12 processes have profiles defined.

# Installare utility
sudo apt install -y apparmor-utils apparmor-profiles apparmor-profiles-extra

# Modalità dei profili:
# enforce  — blocca e logga le violazioni
# complain — logga ma non blocca (utile per sviluppo profili)
# disable  — profilo disattivato

# Mettere un profilo in complain mode
sudo aa-complain /usr/sbin/nginx

# Mettere un profilo in enforce mode
sudo aa-enforce /usr/sbin/nginx

# Disabilitare un profilo
sudo aa-disable /usr/sbin/nginx
```

### Creare un Profilo Personalizzato

```bash
# Metodo 1: aa-genprof (interattivo)
sudo aa-genprof /usr/local/bin/myapp
# 1. Avvia l'applicazione in un'altra shell
# 2. Usa tutte le funzionalità dell'applicazione
# 3. Torna alla shell di aa-genprof e premi 'S' per scansionare
# 4. Per ogni accesso rilevato, scegli Allow/Deny/Glob/etc.
# 5. Premi 'F' per finire e salvare

# Metodo 2: scrivere manualmente
# I profili sono in /etc/apparmor.d/
```

Esempio di profilo AppArmor per Nginx:

```conf
# /etc/apparmor.d/usr.sbin.nginx
#include <tunables/global>

/usr/sbin/nginx {
    #include <abstractions/base>
    #include <abstractions/nameservice>
    #include <abstractions/openssl>
    #include <abstractions/ssl_certs>

    # Capacità necessarie
    capability net_bind_service,
    capability setuid,
    capability setgid,
    capability dac_override,

    # Binario
    /usr/sbin/nginx mr,

    # Configurazione (lettura)
    /etc/nginx/** r,
    /etc/nginx/nginx.conf r,

    # Log (scrittura)
    /var/log/nginx/*.log w,
    /var/log/nginx/ r,

    # PID file
    /run/nginx.pid rw,

    # Contenuti web (lettura)
    /var/www/** r,
    /srv/www/** r,

    # Upload temporanei
    /var/lib/nginx/tmp/** rw,
    /var/cache/nginx/** rw,

    # Socket e rete
    network inet stream,
    network inet6 stream,

    # Deny esplicito
    deny /etc/shadow r,
    deny /etc/passwd w,
    deny /root/** rwx,

    # Processi figlio
    /usr/sbin/nginx ix,
}
```

```bash
# Caricare il profilo
sudo apparmor_parser -r /etc/apparmor.d/usr.sbin.nginx

# Verificare
sudo aa-status | grep nginx
```

---

## Kernel Hardening con sysctl

I parametri del kernel controllano il comportamento di rete, memoria e processi. Un hardening corretto riduce significativamente la superficie di attacco.

### Configurazione Completa

```bash
# /etc/sysctl.d/99-hardening.conf

# ============================================================
# NETWORK HARDENING
# ============================================================

# Disabilitare IP forwarding (a meno che il server sia un router)
net.ipv4.ip_forward = 0
net.ipv6.conf.all.forwarding = 0

# Ignorare ICMP redirect (prevenzione MITM)
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0

# Ignorare ICMP broadcast (prevenzione Smurf attack)
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Ignorare risposte ICMP bogus
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Abilitare reverse path filtering (prevenzione IP spoofing)
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Log dei pacchetti con indirizzo impossibile (martians)
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# Non accettare source routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# Protezione SYN flood (SYN cookies)
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 4096
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_syn_retries = 3

# Timeout TCP per connessioni half-open
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 60
net.ipv4.tcp_keepalive_probes = 5

# Disabilitare IPv6 se non utilizzato
# net.ipv6.conf.all.disable_ipv6 = 1
# net.ipv6.conf.default.disable_ipv6 = 1

# Disabilitare accettazione Router Advertisement
net.ipv6.conf.all.accept_ra = 0
net.ipv6.conf.default.accept_ra = 0

# ============================================================
# MEMORY / PROCESS HARDENING
# ============================================================

# ASLR (Address Space Layout Randomization) — massimo livello
kernel.randomize_va_space = 2

# Disabilitare SysRq (o limitarlo)
# 0 = disabilitato completamente
# 176 = solo sync, remount-ro, reboot (minimo utile)
kernel.sysrq = 0

# Limitare l'accesso a dmesg a root
kernel.dmesg_restrict = 1

# Limitare l'accesso a kernel pointers
kernel.kptr_restrict = 2

# Limitare l'accesso a perf_event
kernel.perf_event_paranoid = 3

# Limitare l'uso di ptrace (debug)
# 0 = tutti possono tracciare i propri processi
# 1 = solo processi con CAP_SYS_PTRACE
# 2 = solo admin
# 3 = nessuno (nemmeno root)
kernel.yama.ptrace_scope = 2

# Disabilitare il caricamento di moduli kernel (dopo il boot)
# ATTENZIONE: impedisce anche il caricamento legittimo di moduli!
# kernel.modules_disabled = 1

# Protezione degli hard link e symlink
fs.protected_hardlinks = 1
fs.protected_symlinks = 1
fs.protected_fifos = 2
fs.protected_regular = 2

# Limitare i core dump
fs.suid_dumpable = 0

# Limitare le BPF non privilegiate
kernel.unprivileged_bpf_disabled = 1
net.core.bpf_jit_harden = 2

# Disabilitare user namespaces non privilegiati (se non necessari)
# kernel.unprivileged_userns_clone = 0
```

```bash
# Applicare le modifiche
sudo sysctl --system

# Verificare un parametro specifico
sysctl net.ipv4.tcp_syncookies
# net.ipv4.tcp_syncookies = 1

# Verificare tutti i parametri di hardening
sysctl -a 2>/dev/null | grep -E "randomize_va_space|sysrq|dmesg_restrict|kptr_restrict|accept_redirects|rp_filter|syncookies"
```

---

## Firewall con nftables

nftables è il successore di iptables, con una sintassi più pulita, migliori performance e funzionalità unificate per IPv4/IPv6.

### Migrazione da iptables a nftables

```bash
# Verificare se nftables è disponibile
nft --version

# Esportare le regole iptables correnti in formato nftables
iptables-save | iptables-restore-translate > /etc/nftables/iptables-migrated.nft

# Installare nftables
sudo dnf install -y nftables     # RHEL
sudo apt install -y nftables     # Debian

# Abilitare
sudo systemctl enable --now nftables
```

### Configurazione Completa

```bash
# /etc/nftables.conf
#!/usr/sbin/nft -f

# Flush regole esistenti
flush ruleset

# Definire variabili
define LAN_NET = 10.0.0.0/24
define MGMT_NET = 10.0.1.0/24
define TRUSTED_IPS = { 10.0.0.5, 10.0.0.10, 10.0.1.0/24 }
define SSH_PORT = 2222
define WEB_PORTS = { 80, 443 }

# ============================================================
# Tabella per il filtraggio
# ============================================================
table inet filter {
    # Set per rate limiting
    set rate_limit_ssh {
        type ipv4_addr
        flags dynamic, timeout
        timeout 5m
    }

    # Set per IP bannati (aggiornabile a runtime)
    set blocked_ips {
        type ipv4_addr
        flags interval
        elements = {
            192.168.100.0/24,
            10.255.0.0/16
        }
    }

    # Set per porte aperte (facile da modificare)
    set allowed_tcp_ports {
        type inet_service
        elements = { $SSH_PORT, 80, 443, 8404 }
    }

    # --------------------------------------------------------
    # Chain INPUT
    # --------------------------------------------------------
    chain input {
        type filter hook input priority 0; policy drop;

        # Connessioni established/related — permettere
        ct state established,related accept

        # Connessioni invalid — droppare
        ct state invalid drop

        # Loopback — sempre permesso
        iifname "lo" accept

        # ICMP — permettere ping con rate limiting
        ip protocol icmp icmp type echo-request \
            limit rate 5/second burst 10 packets accept
        ip protocol icmp icmp type { destination-unreachable, time-exceeded } accept
        ip6 nexthdr icmpv6 icmpv6 type { echo-request, echo-reply, nd-neighbor-solicit, nd-neighbor-advert, nd-router-solicit, nd-router-advert } accept

        # Bloccare IP bannati
        ip saddr @blocked_ips drop

        # SSH — solo da reti trusted, con rate limiting
        tcp dport $SSH_PORT ip saddr $MGMT_NET accept
        tcp dport $SSH_PORT ip saddr != $MGMT_NET \
            add @rate_limit_ssh { ip saddr limit rate 3/minute burst 5 packets } accept

        # Porte TCP aperte (web)
        tcp dport @allowed_tcp_ports accept

        # Log dei pacchetti droppati (con rate limiting del log stesso)
        limit rate 10/minute burst 20 packets \
            log prefix "nftables-drop: " level info
    }

    # --------------------------------------------------------
    # Chain FORWARD (se il server è anche router/bridge)
    # --------------------------------------------------------
    chain forward {
        type filter hook forward priority 0; policy drop;

        # Permettere solo traffico dalla LAN verso internet
        # iifname "eth1" oifname "eth0" ip saddr $LAN_NET accept
        # ct state established,related accept
    }

    # --------------------------------------------------------
    # Chain OUTPUT
    # --------------------------------------------------------
    chain output {
        type filter hook output priority 0; policy accept;

        # Output generalmente permesso, ma si può limitare
        # per server molto sensibili:
        # ct state established,related accept
        # oifname "lo" accept
        # tcp dport { 53, 80, 443, 25 } accept
        # udp dport { 53, 123 } accept
        # drop
    }
}

# ============================================================
# Tabella per NAT (se necessario)
# ============================================================
table ip nat {
    chain prerouting {
        type nat hook prerouting priority -100; policy accept;

        # Port forwarding esempio
        # tcp dport 8080 dnat to 10.0.0.11:80
    }

    chain postrouting {
        type nat hook postrouting priority 100; policy accept;

        # Masquerade per NAT
        # oifname "eth0" masquerade
    }
}
```

### Gestione a Runtime

```bash
# Caricare la configurazione
sudo nft -f /etc/nftables.conf

# Visualizzare le regole
sudo nft list ruleset

# Aggiungere un IP al set dei bannati
sudo nft add element inet filter blocked_ips { 203.0.113.50 }

# Rimuovere un IP dal set
sudo nft delete element inet filter blocked_ips { 203.0.113.50 }

# Aggiungere una porta
sudo nft add element inet filter allowed_tcp_ports { 8080 }

# Elencare gli elementi di un set
sudo nft list set inet filter blocked_ips

# Aggiungere una regola singola
sudo nft add rule inet filter input tcp dport 9090 accept

# Statistiche
sudo nft list chain inet filter input -a
# Mostra i contatori per ogni regola

# Flush di una singola chain
sudo nft flush chain inet filter input

# Salvare le regole correnti
sudo nft list ruleset > /etc/nftables-backup.conf
```

---

## Fail2Ban — Protezione dai Brute Force

Fail2Ban monitora i log e banna automaticamente gli IP che mostrano comportamento malevolo (tentativi di login falliti, scan, exploit).

### Installazione e Configurazione

```bash
# Installare
sudo dnf install -y fail2ban     # RHEL
sudo apt install -y fail2ban     # Debian

# Non modificare mai i file in /etc/fail2ban/*.conf
# Creare override in /etc/fail2ban/*.local
```

```ini
# /etc/fail2ban/jail.local
[DEFAULT]
# Tempo di ban (10 minuti)
bantime = 600

# Finestra di osservazione
findtime = 600

# Tentativi prima del ban
maxretry = 5

# Backend per il log parsing
backend = systemd

# Azione di default: ban IP + invio email
action = %(action_mwl)s

# Email per notifiche
destemail = admin@example.com
sender = fail2ban@example.com
mta = sendmail

# IP da non bannare MAI
ignoreip = 127.0.0.1/8 ::1 10.0.1.0/24

# ============================================================
# JAIL: SSH
# ============================================================
[sshd]
enabled = true
port = ssh,2222
filter = sshd
logpath = %(sshd_log)s
maxretry = 3
bantime = 3600          # 1 ora per SSH
findtime = 300          # 5 minuti

# Ban progressivo per recidivi
[sshd-aggressive]
enabled = true
port = ssh,2222
filter = sshd[mode=aggressive]
logpath = %(sshd_log)s
maxretry = 1
bantime = 86400         # 24 ore
findtime = 86400

# ============================================================
# JAIL: Apache/Nginx
# ============================================================
[nginx-http-auth]
enabled = true
port = http,https
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 5

[nginx-botsearch]
enabled = true
port = http,https
filter = nginx-botsearch
logpath = /var/log/nginx/access.log
maxretry = 2
bantime = 86400

# ============================================================
# JAIL: Tentativi di exploit
# ============================================================
[nginx-bad-request]
enabled = true
port = http,https
filter = nginx-bad-request
logpath = /var/log/nginx/access.log
maxretry = 3
bantime = 86400

# ============================================================
# JAIL: Recidivi (ban permanente per chi viene bannato più volte)
# ============================================================
[recidive]
enabled = true
filter = recidive
logpath = /var/log/fail2ban.log
bantime = 604800        # 1 settimana
findtime = 86400        # 24 ore
maxretry = 3            # 3 ban in 24 ore = ban per 1 settimana
```

### Filtro Personalizzato

```ini
# /etc/fail2ban/filter.d/nginx-bad-request.conf
[Definition]
failregex = ^<HOST> .* "(GET|POST|HEAD) .*(wp-login|xmlrpc|phpmyadmin|\.env|\.git|shell|admin).*" (400|403|404)
ignoreregex =
```

### Gestione

```bash
# Avviare
sudo systemctl enable --now fail2ban

# Stato generale
sudo fail2ban-client status

# Stato di un jail specifico
sudo fail2ban-client status sshd
# Output:
# Status for the jail: sshd
# |- Filter
# |  |- Currently failed: 2
# |  |- Total failed:     156
# |  `- File list:        /var/log/auth.log
# `- Actions
#    |- Currently banned: 3
#    |- Total banned:     47
#    `- Banned IP list:   203.0.113.50 198.51.100.23 192.0.2.100

# Bannare un IP manualmente
sudo fail2ban-client set sshd banip 203.0.113.99

# Sbannare un IP
sudo fail2ban-client set sshd unbanip 203.0.113.99

# Testare un filtro contro un log
sudo fail2ban-regex /var/log/auth.log /etc/fail2ban/filter.d/sshd.conf
```

---

## SSH Hardening Avanzato

### Configurazione Sicura Completa

```bash
# /etc/ssh/sshd_config.d/99-hardening.conf

# Porta non standard
Port 2222

# Solo protocollo 2 (il default nelle versioni moderne)
Protocol 2

# Algoritmi sicuri — rimuovere algoritmi deboli
HostKeyAlgorithms ssh-ed25519,rsa-sha2-512,rsa-sha2-256
KexAlgorithms sntrup761x25519-sha512@openssh.com,curve25519-sha256,curve25519-sha256@libssh.org
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com

# Autenticazione
PermitRootLogin no
MaxAuthTries 3
MaxSessions 3
LoginGraceTime 30
PasswordAuthentication no
PermitEmptyPasswords no
PubkeyAuthentication yes
AuthenticationMethods publickey

# Disabilitare metodi di autenticazione deboli
ChallengeResponseAuthentication no
KerberosAuthentication no
GSSAPIAuthentication no
HostbasedAuthentication no

# Limitare utenti/gruppi che possono fare login
AllowGroups ssh-users admins

# Timeout sessione
ClientAliveInterval 300
ClientAliveCountMax 2

# Disabilitare funzionalità non necessarie
X11Forwarding no
AllowTcpForwarding no
AllowAgentForwarding no
PermitTunnel no
GatewayPorts no
PermitUserEnvironment no
PrintMotd no

# Logging
LogLevel VERBOSE
SyslogFacility AUTH

# Banner di avviso legale
Banner /etc/ssh/banner.txt

# Chroot per utenti SFTP
Match Group sftp-users
    ChrootDirectory /sftp/%u
    ForceCommand internal-sftp
    AllowTcpForwarding no
    X11Forwarding no
    PermitTunnel no
```

### SSH Certificates (oltre le semplici chiavi)

Le SSH certificates sono superiori alle chiavi SSH tradizionali: hanno una scadenza, possono essere revocate centralmente e non richiedono di distribuire chiavi pubbliche su ogni server.

```bash
# 1. Creare la CA (Certificate Authority)
ssh-keygen -t ed25519 -f /etc/ssh/ca_key -C "SSH CA"

# 2. Distribuire la chiave pubblica della CA sui server
# Su ogni server, aggiungere in /etc/ssh/sshd_config:
TrustedUserCAKeys /etc/ssh/ca_key.pub

# 3. Firmare la chiave di un utente
ssh-keygen -s /etc/ssh/ca_key \
  -I "mario.rossi@example.com" \
  -n mario,admin \
  -V +52w \
  -z 1 \
  /home/mario/.ssh/id_ed25519.pub

# Parametri:
# -s  chiave della CA
# -I  identificativo (appare nei log)
# -n  principals (utenti) consentiti
# -V  validità (+52w = 52 settimane)
# -z  serial number

# 4. Verificare il certificato
ssh-keygen -L -f /home/mario/.ssh/id_ed25519-cert.pub
# Output:
# Type: ssh-ed25519-cert-v01@openssh.com user certificate
# Public key: ED25519-CERT SHA256:...
# Signing CA: ED25519 SHA256:...
# Key ID: "mario.rossi@example.com"
# Serial: 1
# Valid: from 2026-04-12 to 2027-04-11
# Principals:
#         mario
#         admin

# 5. Host certificates (certificare i server)
ssh-keygen -s /etc/ssh/ca_key \
  -I "server1.example.com" \
  -h \
  -n server1.example.com,10.0.0.1 \
  -V +52w \
  /etc/ssh/ssh_host_ed25519_key.pub

# Sul client, in /etc/ssh/ssh_known_hosts o ~/.ssh/known_hosts:
# @cert-authority *.example.com <contenuto di ca_key.pub>
```

### Jump Host (Bastion)

```bash
# Configurazione SSH del client per usare un jump host
# ~/.ssh/config

Host bastion
    HostName bastion.example.com
    Port 2222
    User admin
    IdentityFile ~/.ssh/id_ed25519
    ForwardAgent no

Host internal-*
    ProxyJump bastion
    User admin
    IdentityFile ~/.ssh/id_ed25519

Host internal-web1
    HostName 10.0.0.11

Host internal-db1
    HostName 10.0.0.21

# Uso:
# ssh internal-web1
# Equivale a: ssh -J bastion 10.0.0.11
```

### Port Knocking

Port knocking richiede di "bussare" su una sequenza di porte prima che la porta SSH si apra.

```bash
# Installare knockd
sudo apt install -y knockd

# /etc/knockd.conf
[options]
    UseSyslog

[openSSH]
    sequence    = 7000,8000,9000
    seq_timeout = 5
    command     = /usr/sbin/nft add rule inet filter input ip saddr %IP% tcp dport 2222 accept
    tcpflags    = syn

[closeSSH]
    sequence    = 9000,8000,7000
    seq_timeout = 5
    command     = /usr/sbin/nft delete rule inet filter input handle $(nft -a list chain inet filter input | grep %IP% | grep 2222 | awk '{print $NF}')
    tcpflags    = syn

# Abilitare
sudo systemctl enable --now knockd

# Client: bussare
knock -v server.example.com 7000 8000 9000
ssh -p 2222 admin@server.example.com
# Dopo il logout, chiudere:
knock -v server.example.com 9000 8000 7000
```

---

## File Integrity Monitoring

### AIDE (Advanced Intrusion Detection Environment)

AIDE crea un database dei checksum di tutti i file del sistema e rileva modifiche non autorizzate.

```bash
# Installare
sudo dnf install -y aide     # RHEL
sudo apt install -y aide     # Debian

# Configurazione: /etc/aide/aide.conf (Debian) o /etc/aide.conf (RHEL)
```

```conf
# /etc/aide.conf

# Database
database_in = file:/var/lib/aide/aide.db.gz
database_out = file:/var/lib/aide/aide.db.new.gz
database_new = file:/var/lib/aide/aide.db.new.gz

# Regole personalizzate
NORMAL = p+i+n+u+g+s+m+c+acl+selinux+xattrs+sha256
PERMS = p+u+g+acl+selinux+xattrs
LOG = p+u+g+n+S+acl+selinux+xattrs
DATAONLY = p+n+u+g+s+acl+selinux+xattrs+sha256
DIR = p+i+n+u+g+acl+selinux+xattrs

# Directory da monitorare
/boot/   NORMAL
/bin/    NORMAL
/sbin/   NORMAL
/usr/bin/  NORMAL
/usr/sbin/ NORMAL
/lib/    NORMAL
/lib64/  NORMAL
/etc/    NORMAL

# File specifici critici
/etc/passwd   NORMAL
/etc/shadow   NORMAL
/etc/group    NORMAL
/etc/gshadow  NORMAL
/etc/sudoers  NORMAL
/etc/ssh/sshd_config NORMAL

# Esclusioni
!/var/log/
!/var/spool/
!/var/cache/
!/tmp/
!/run/
!/proc/
!/sys/
!/dev/
!/var/lib/aide/
```

```bash
# Inizializzare il database (prima esecuzione)
sudo aide --init
sudo mv /var/lib/aide/aide.db.new.gz /var/lib/aide/aide.db.gz

# Eseguire un check
sudo aide --check
# Output:
# AIDE found differences between database and filesystem!!
#
# Summary:
#   Total number of entries: 45678
#   Added entries:           2
#   Removed entries:         0
#   Changed entries:         5

# Aggiornare il database dopo modifiche legittime
sudo aide --update
sudo mv /var/lib/aide/aide.db.new.gz /var/lib/aide/aide.db.gz

# Automatizzare con cron
echo "0 5 * * * root /usr/sbin/aide --check | mail -s 'AIDE Report' admin@example.com" | sudo tee /etc/cron.d/aide-check
```

---

## Rootkit Detection

### rkhunter

```bash
# Installare
sudo dnf install -y rkhunter
sudo apt install -y rkhunter

# Aggiornare i database
sudo rkhunter --update
sudo rkhunter --propupd    # Aggiorna le proprietà dei file di sistema

# Eseguire una scansione
sudo rkhunter --check --skip-keypress

# Configurazione: /etc/rkhunter.conf
# Opzioni importanti:
MIRRORS_MODE=0
WEB_CMD=wget
UPDATE_MIRRORS=1
ALLOW_SSH_ROOT_USER=no
ALLOW_SSH_PROT_V1=0
ENABLE_TESTS="all"
DISABLE_TESTS="suspscan hidden_ports hidden_procs deleted_files packet_cap_apps"

# Report:
# [Rootkit checks...]
#   Checking for possible rootkit files and directories...
#   Performing check of known rootkit files and directories...
#   Checking for Ambient's Rootkit (ark)          [ Not found ]
#   Checking for Balaur Rootkit                   [ Not found ]
#   ...
# System checks summary
# =====================
# File properties checks...
#     Files checked: 136
#     Suspect files: 0

# Automatizzare
echo '0 3 * * 0 root /usr/bin/rkhunter --check --skip-keypress --report-warnings-only | mail -s "rkhunter weekly" admin@example.com' | sudo tee /etc/cron.d/rkhunter
```

### chkrootkit

```bash
# Installare
sudo apt install -y chkrootkit

# Eseguire
sudo chkrootkit

# Output:
# ROOTDIR is `/'
# Checking `amd'...                                          not found
# Checking `basename'...                                     not infected
# Checking `biff'...                                         not found
# Checking `chfn'...                                         not infected
# ...
# Checking `sniffer'...                                      lo: not promisc and no PF_PACKET sockets
```

---

## Audit Framework — auditd

Il sistema di audit del kernel Linux traccia eventi di sicurezza: accessi a file, chiamate di sistema, login, modifiche di configurazione.

### Installazione e Configurazione

```bash
# Installare
sudo dnf install -y audit audit-libs
sudo apt install -y auditd audispd-plugins

# Abilitare
sudo systemctl enable --now auditd
```

### Regole di Audit

```bash
# /etc/audit/rules.d/hardening.rules

# Eliminare regole precedenti
-D

# Buffer size (aumentare per sistemi occupati)
-b 8192

# Failure mode: 1=printk, 2=panic
-f 1

# ============================================================
# Monitorare modifiche a file critici
# ============================================================
# Modifiche a /etc/passwd, shadow, group
-w /etc/passwd -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/sudoers -p wa -k sudoers
-w /etc/sudoers.d/ -p wa -k sudoers

# Modifiche alla configurazione di sicurezza
-w /etc/selinux/ -p wa -k selinux
-w /etc/apparmor/ -p wa -k apparmor
-w /etc/apparmor.d/ -p wa -k apparmor

# SSH config
-w /etc/ssh/sshd_config -p wa -k sshd_config
-w /etc/ssh/sshd_config.d/ -p wa -k sshd_config

# Cron
-w /etc/crontab -p wa -k cron
-w /etc/cron.d/ -p wa -k cron
-w /etc/cron.daily/ -p wa -k cron
-w /etc/cron.hourly/ -p wa -k cron
-w /etc/cron.weekly/ -p wa -k cron
-w /etc/cron.monthly/ -p wa -k cron

# PAM
-w /etc/pam.d/ -p wa -k pam
-w /etc/security/ -p wa -k pam

# Network
-w /etc/hosts -p wa -k network
-w /etc/sysconfig/network -p wa -k network
-w /etc/resolv.conf -p wa -k network
-w /etc/nftables.conf -p wa -k firewall

# ============================================================
# Monitorare operazioni privilegiate
# ============================================================
# Login e logout
-w /var/log/lastlog -p wa -k login
-w /var/log/faillog -p wa -k login
-w /var/log/wtmp -p wa -k login
-w /var/log/btmp -p wa -k login

# Uso di sudo
-a always,exit -F arch=b64 -S execve -F euid=0 -F auid>=1000 -F auid!=-1 -k sudo_commands

# Modifiche a tempo e data
-a always,exit -F arch=b64 -S adjtimex -S settimeofday -S clock_settime -k time_change
-w /etc/localtime -p wa -k time_change

# Modifica di utenti/gruppi
-a always,exit -F arch=b64 -S setuid -S setgid -S setreuid -S setregid -k privilege_escalation

# Caricamento moduli kernel
-a always,exit -F arch=b64 -S init_module -S finit_module -S delete_module -k kernel_modules
-w /sbin/insmod -p x -k kernel_modules
-w /sbin/modprobe -p x -k kernel_modules
-w /sbin/rmmod -p x -k kernel_modules

# Mount/unmount
-a always,exit -F arch=b64 -S mount -S umount2 -k mounts

# Accesso a file fallito (potenziale tentativo di accesso non autorizzato)
-a always,exit -F arch=b64 -S open -S openat -F exit=-EACCES -k access_denied
-a always,exit -F arch=b64 -S open -S openat -F exit=-EPERM -k access_denied

# ============================================================
# Rendere le regole immutabili (richiede reboot per cambiarle)
# ============================================================
-e 2
```

```bash
# Caricare le regole
sudo augenrules --load

# Verificare le regole attive
sudo auditctl -l

# Report degli eventi
sudo aureport --summary

# Report dei login falliti
sudo aureport --failed --start today

# Report degli eventi sudo
sudo aureport -k sudo_commands --start today

# Cercare eventi specifici
sudo ausearch -k identity -ts today
sudo ausearch -k sshd_config -ts recent

# Report dettagliato per utente
sudo aureport -au --start this-week

# Interpretare un evento
sudo ausearch -k identity -ts recent -i
# -i interpreta UID/GID in nomi leggibili
```

---

## Disk Encryption con LUKS

LUKS (Linux Unified Key Setup) è lo standard per la crittografia del disco su Linux.

### Crittografare un Disco

```bash
# Installare cryptsetup
sudo dnf install -y cryptsetup
sudo apt install -y cryptsetup

# Crittografare una partizione (CANCELLA TUTTI I DATI!)
sudo cryptsetup luksFormat --type luks2 \
  --cipher aes-xts-plain64 \
  --key-size 512 \
  --hash sha512 \
  --pbkdf argon2id \
  --iter-time 5000 \
  /dev/sdb1

# Output:
# WARNING! This will overwrite data on /dev/sdb1 irrevocably.
# Are you sure? (Type 'yes' in capital letters): YES
# Enter passphrase for /dev/sdb1:
# Verify passphrase:

# Aprire il volume crittografato
sudo cryptsetup luksOpen /dev/sdb1 data_encrypted
# Crea /dev/mapper/data_encrypted

# Creare filesystem e montare
sudo mkfs.ext4 /dev/mapper/data_encrypted
sudo mount /dev/mapper/data_encrypted /mnt/encrypted

# Montaggio automatico al boot
# 1. Aggiungere a /etc/crypttab
echo "data_encrypted /dev/sdb1 none luks,discard" | sudo tee -a /etc/crypttab

# 2. Aggiungere a /etc/fstab
echo "/dev/mapper/data_encrypted /mnt/encrypted ext4 defaults 0 2" | sudo tee -a /etc/fstab
```

### Gestione delle Chiavi

```bash
# Verificare gli slot chiave
sudo cryptsetup luksDump /dev/sdb1
# Mostra informazioni LUKS inclusi gli slot occupati (0-7)

# Aggiungere una chiave (keyfile per backup/automazione)
sudo dd if=/dev/urandom of=/root/luks-keyfile bs=4096 count=1
sudo chmod 400 /root/luks-keyfile
sudo cryptsetup luksAddKey /dev/sdb1 /root/luks-keyfile

# Rimuovere una chiave
sudo cryptsetup luksRemoveKey /dev/sdb1
# Chiede quale passphrase rimuovere

# Cambiare la passphrase
sudo cryptsetup luksChangeKey /dev/sdb1

# Backup dell'header LUKS (CRITICO per il disaster recovery)
sudo cryptsetup luksHeaderBackup /dev/sdb1 --header-backup-file /root/luks-header-backup.img
# CONSERVARE QUESTO FILE IN UN LUOGO SICURO OFFLINE

# Ripristinare l'header
sudo cryptsetup luksHeaderRestore /dev/sdb1 --header-backup-file /root/luks-header-backup.img
```

### Automazione con Keyfile

Per server senza intervento manuale al boot:

```bash
# /etc/crypttab con keyfile
# data_encrypted /dev/sdb1 /root/luks-keyfile luks,discard

# Proteggere il keyfile
sudo chmod 400 /root/luks-keyfile
sudo chattr +i /root/luks-keyfile    # Immutabile

# ATTENZIONE: il keyfile sul disco non protegge da accesso fisico
# Per protezione completa, usare TPM o Network Bound Disk Encryption (NBDE/Clevis+Tang)
```

---

## PAM — Configurazione e Hardening

PAM (Pluggable Authentication Modules) è il framework di autenticazione di Linux. Ogni servizio (login, su, sudo, sshd) ha la propria configurazione PAM.

### Blocco Account dopo Tentativi Falliti

```bash
# /etc/pam.d/common-auth (Debian) o /etc/pam.d/system-auth (RHEL)
# Aggiungere PRIMA di pam_unix.so:

# Bloccare l'account dopo 5 tentativi falliti per 900 secondi
auth required pam_faillock.so preauth silent audit deny=5 unlock_time=900 fail_interval=900
auth sufficient pam_unix.so nullok
auth [default=die] pam_faillock.so authfail audit deny=5 unlock_time=900 fail_interval=900
auth required pam_deny.so

# In /etc/pam.d/common-account (Debian) o /etc/pam.d/system-auth (RHEL):
account required pam_faillock.so
```

```bash
# Verificare lo stato di un account
sudo faillock --user mario
# Output:
# mario:
# When                Type  Source              Valid
# 2026-04-12 10:30:01 RHOST 203.0.113.50       V
# 2026-04-12 10:30:05 RHOST 203.0.113.50       V
# 2026-04-12 10:30:08 RHOST 203.0.113.50       V

# Sbloccare un account
sudo faillock --user mario --reset
```

### Limiti sulle Risorse

```bash
# /etc/security/limits.conf

# Limitare i processi per utente (prevenire fork bomb)
*               hard    nproc           1024
*               soft    nproc           512
root            hard    nproc           unlimited

# Limitare le dimensioni dei file core
*               hard    core            0

# Limitare la dimensione massima dei file
*               hard    fsize           2097152    # 2 GB

# Limitare il numero di file aperti
*               hard    nofile          65535
*               soft    nofile          8192

# Limitare la memoria per utente
*               hard    as              4194304    # 4 GB
```

### Restrizioni su su

```bash
# /etc/pam.d/su
# Permettere su solo ai membri del gruppo wheel
auth required pam_wheel.so use_uid

# Aggiungere utenti al gruppo wheel
sudo usermod -aG wheel admin_user
```

---

## Sudo Hardening

### Configurazione Sicura

```bash
# Usare sempre visudo per editare
sudo visudo

# OPPURE creare file in /etc/sudoers.d/
sudo visudo -f /etc/sudoers.d/99-hardening
```

```bash
# /etc/sudoers.d/99-hardening

# Defaults di sicurezza
Defaults    env_reset                    # Reset delle variabili d'ambiente
Defaults    env_keep = "LANG LC_*"       # Mantenere solo locale
Defaults    secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Defaults    use_pty                      # Forzare l'uso di PTY (previene session hijacking)
Defaults    logfile="/var/log/sudo.log"  # Log dedicato
Defaults    log_input, log_output        # Registrare input E output
Defaults    iolog_dir="/var/log/sudo-io/%{user}"
Defaults    timestamp_timeout=5          # Timeout password (5 minuti)
Defaults    passwd_tries=3               # Massimo 3 tentativi di password
Defaults    insults                      # Messaggi divertenti per password sbagliata (opzionale)
Defaults    requiretty                   # Richiedere un terminale (previene cron sudo abuse)
Defaults    umask=0027                   # umask restrittiva per comandi sudo

# Disabilitare NOPASSWD per tutti
Defaults    !authenticate                # NO — MAI disabilitare autenticazione

# Regole granulari
# Formato: CHI DOVE=(COME) COSA

# Admin completo (ma con log)
%admins ALL=(ALL:ALL) ALL

# Web admin: può solo gestire nginx/apache
%webadmins ALL=(root) NOPASSWD: /usr/bin/systemctl restart nginx, \
                                /usr/bin/systemctl reload nginx, \
                                /usr/bin/systemctl status nginx, \
                                /usr/bin/nginx -t

# DBA: può solo gestire il database
%dbadmins ALL=(postgres) NOPASSWD: /usr/bin/psql, \
                                   /usr/bin/pg_dump, \
                                   /usr/bin/pg_restore

# Monitoraggio: può vedere log e status
%monitoring ALL=(root) NOPASSWD: /usr/bin/journalctl -u *, \
                                 /usr/bin/systemctl status *, \
                                 /usr/bin/ss -tulnp, \
                                 /usr/bin/df -h

# BLOCCARE comandi pericolosi per tutti tranne root
%admins ALL=(ALL) !/usr/bin/su, \
                  !/usr/bin/bash, \
                  !/usr/bin/sh, \
                  !/usr/bin/vi /etc/sudoers, \
                  !/usr/sbin/visudo, \
                  !/usr/bin/chmod 777 *
```

```bash
# Verificare la configurazione
sudo visudo -c
# /etc/sudoers: parsed OK
# /etc/sudoers.d/99-hardening: parsed OK

# Verificare cosa può fare un utente
sudo -l -U webadmin
# User webadmin may run the following commands on server:
#     (root) NOPASSWD: /usr/bin/systemctl restart nginx, ...

# Analizzare i log di sudo
sudo cat /var/log/sudo.log

# Replay delle sessioni sudo (se log_input,log_output attivi)
sudo sudoreplay -l
sudo sudoreplay <session_id>
```

---

## Framework di Hardening a Confronto

### Matrice Comparativa

```
┌──────────────────┬─────────────────────┬─────────────────────┬─────────────────────┐
│ Criterio         │ CIS Benchmarks      │ DISA STIG           │ NIST SP 800-123     │
├──────────────────┼─────────────────────┼─────────────────────┼─────────────────────┤
│ Destinatari      │ Qualsiasi organiz.  │ DoD / settore       │ Agenzie federali    │
│                  │ privata o pubblica  │ militare USA        │ USA + best practice │
├──────────────────┼─────────────────────┼─────────────────────┼─────────────────────┤
│ Granularità      │ Alta — centinaia    │ Molto alta — ogni   │ Media — principi    │
│                  │ di controlli con    │ parametro ha un     │ generali con        │
│                  │ remediation script  │ VulID, severità,    │ raccomandazioni     │
│                  │                     │ fix                 │                     │
├──────────────────┼─────────────────────┼─────────────────────┼─────────────────────┤
│ Livelli          │ Level 1 (base)      │ CAT I (critico)     │ N/A — linee guida   │
│                  │ Level 2 (aggressivo)│ CAT II (alto)       │ generali            │
│                  │                     │ CAT III (medio)     │                     │
├──────────────────┼─────────────────────┼─────────────────────┼─────────────────────┤
│ Formato          │ PDF + XCCDF/OVAL    │ XCCDF + SCAP        │ PDF (documento)     │
│ distribuzione    │ CIS-CAT scanner     │ STIG Viewer + SCAP  │                     │
├──────────────────┼─────────────────────┼─────────────────────┼─────────────────────┤
│ Automazione      │ CIS-CAT Pro,        │ oscap, SCAP         │ Manuale, riferim.   │
│                  │ Lynis, ansible-     │ Compliance Checker   │ ad altri framework  │
│                  │ lockdown            │                     │                     │
├──────────────────┼─────────────────────┼─────────────────────┼─────────────────────┤
│ Licenza          │ Gratuito (PDF)      │ Gratuito (pubblico) │ Gratuito (pubblico) │
│                  │ CIS-CAT Pro: a      │                     │                     │
│                  │ pagamento            │                     │                     │
├──────────────────┼─────────────────────┼─────────────────────┼─────────────────────┤
│ Aggiornamento    │ Ogni 6-12 mesi      │ Trimestrale         │ Occasionale         │
│ tipico           │                     │                     │                     │
├──────────────────┼─────────────────────┼─────────────────────┼─────────────────────┤
│ Copertura OS     │ Debian, Ubuntu,     │ RHEL, Ubuntu,       │ Generico (qualsiasi │
│                  │ RHEL, CentOS,       │ SLES, Oracle Linux  │ sistema server)     │
│                  │ SLES, Amazon Linux  │                     │                     │
└──────────────────┴─────────────────────┴─────────────────────┴─────────────────────┘
```

> **Fonte**: CIS Benchmarks v3.0.0, cisecurity.org; DISA STIG, public.cyber.mil;
> NIST SP 800-123, nist.gov. Consultati: 2026-05-23.

### CIS Benchmarks — Level 1 vs Level 2

```
Level 1 — "Prudent baseline"
  ✓ Applicabile a qualsiasi ambiente senza impatto operativo significativo
  ✓ Raccomandazioni: disabilitare servizi inutili, configurare firewall base,
    impostare password policy, restringere mount options (/tmp, /dev/shm)
  ✓ Esempio: "Ensure noexec option set on /tmp partition" (CIS 1.1.4)

Level 2 — "Defense in depth"
  ✓ Per ambienti ad alta sicurezza, può impattare funzionalità
  ✓ Raccomandazioni: auditd completo con regole immutabili, SELinux enforcing,
    kernel modules_disabled=1, restrizione ptrace_scope=3
  ✓ Esempio: "Ensure audit log storage size is configured" (CIS 4.1.2.1)
  ✓ Esempio: "Ensure kernel module loading and unloading is collected" (CIS 4.1.16)
```

### DISA STIG — Categorie di Severità

```bash
# CAT I (High) — compromissione immediata (es. HostbasedAuthentication no)
# CAT II (Medium) — rischio significativo (es. PAM SHA-512 obbligatorio)
# CAT III (Low) — impatto limitato (es. directory pubbliche owned by root)
# Download: https://public.cyber.mil/stigs/downloads/
```

### NIST SP 800-123 — Principi Guida

Principi architetturali (non checklist operativa): pianificare sicurezza prima del deployment, patch tempestive, rimuovere servizi non necessari, configurare autenticazione OS, installare IDS/FIM, testare, monitoraggio continuo.

> **Riferimento**: NIST SP 800-123, "Guide to General Server Security",
> Sezioni 3-6. Consultato: 2026-05-23.

---

## Boot Security — UEFI, GRUB2, TPM 2.0

Il boot sicuro protegge la catena dall'hardware al kernel — compromissione del bootloader invalida tutto ciò che gira sopra.

### UEFI Secure Boot

```
Catena di fiducia UEFI Secure Boot:
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Firmware   │───▶│  Shim (firmato│───▶│  GRUB2       │───▶│   Kernel     │
│   UEFI (PK)  │    │  da Microsoft│    │  (firmato da │    │  (firmato da │
│              │    │  + MOK)      │    │  distro)     │    │  distro)     │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
     Platform Key       Machine Owner      Bootloader         vmlinuz
     (OEM)              Key (MOK)          verificato         verificato
```

```bash
# Verificare se Secure Boot è attivo
mokutil --sb-state
# Output: SecureBoot enabled / disabled

# Verificare le chiavi registrate
mokutil --list-enrolled

# Se si usa un kernel personalizzato, firmarlo con MOK:
# 1. Generare chiave MOK
openssl req -new -x509 -newkey rsa:2048 -keyout MOK.priv -outform DER \
  -out MOK.der -nodes -days 36500 -subj "/CN=Custom Kernel Signing Key/"

# 2. Registrare la chiave MOK
sudo mokutil --import MOK.der
# Richiede password che verrà chiesta al prossimo reboot

# 3. Firmare il kernel
sudo sbsign --key MOK.priv --cert MOK.der \
  /boot/vmlinuz-$(uname -r) \
  --output /boot/vmlinuz-$(uname -r).signed

# 4. Reboot e confermare la registrazione nel MOK Manager
sudo reboot

# Verificare che il kernel sia firmato
sbverify --cert MOK.der /boot/vmlinuz-$(uname -r)
```

### GRUB2 Password

```bash
# Impedisce modifica parametri di boot (es. init=/bin/bash → root shell)
grub2-mkpasswd-pbkdf2   # Genera hash PBKDF2

cat > /etc/grub.d/01_password << 'GRUBEOF'
#!/bin/sh
set -e
cat << EOF
set superusers="grubadmin"
password_pbkdf2 grubadmin grub.pbkdf2.sha512.10000.<hash_generato>
EOF
GRUBEOF
chmod 700 /etc/grub.d/01_password

# --unrestricted in 10_linux: boot senza password, modifica con password
grub2-mkconfig -o /boot/grub2/grub.cfg   # RHEL (update-grub su Debian)
chmod 600 /boot/grub2/grub.cfg
```

### Crittografia di /boot

```bash
# /boot crittografato impedisce modifica di kernel/initramfs offline
# Preferire LUKS1 per /boot (compatibilità GRUB2)
# Procedura ad alto rischio — testare su VM prima
sudo cp -a /boot /boot.bak
sudo cryptsetup luksFormat --type luks1 /dev/sda2
sudo cryptsetup luksOpen /dev/sda2 boot_crypt
sudo mkfs.ext4 /dev/mapper/boot_crypt
sudo mount /dev/mapper/boot_crypt /boot
sudo cp -a /boot.bak/* /boot/
# Aggiornare /etc/fstab, /etc/crypttab, reinstallare GRUB
# NOTA: due password al boot (/boot + / se entrambi crittografati)
```

### Measured Boot con TPM 2.0

```bash
# TPM registra hash di ogni componente di boot nei PCR
ls -la /dev/tpm*                           # Verificare presenza TPM
sudo apt install -y tpm2-tools             # Debian (dnf su RHEL)

tpm2_pcrread sha256
# PCR 0=firmware, 1=config FW, 4=bootloader, 7=SecureBoot, 8-9=kernel

# Sblocco LUKS condizionato ai PCR (Clevis + TPM2)
sudo apt install -y clevis clevis-tpm2 clevis-luks
sudo clevis luks bind -d /dev/sda3 tpm2 '{"pcr_bank":"sha256","pcr_ids":"0,1,4,7,9"}'
sudo clevis luks list -d /dev/sda3

# Abilitare in initramfs
sudo dracut -f              # RHEL
sudo update-initramfs -u    # Debian
# NOTA: kernel update cambia PCR 8,9 → re-binding necessario
```

---

## Kernel Lockdown Mode e Restrizioni kexec

Introdotto nel kernel 5.4, limita le operazioni che anche root può eseguire con Secure Boot attivo.

### Modalità di Lockdown

```bash
# Verificare lo stato del lockdown
cat /sys/kernel/security/lockdown
# Output: [none] integrity confidentiality

# none          — Nessuna restrizione (default senza Secure Boot)
# integrity     — Impedisce modifiche al kernel in esecuzione
# confidentiality — integrity + impedisce lettura di dati sensibili del kernel

# Quando Secure Boot è attivo, il lockdown è tipicamente "integrity"
# Le seguenti operazioni sono BLOCCATE in modalità integrity:
#   - Caricamento di moduli kernel non firmati
#   - Accesso a /dev/mem e /dev/kmem
#   - Accesso a porte I/O (/dev/port)
#   - Scrittura diretta su MSR (Model Specific Registers)
#   - kexec di kernel non firmati
#   - Hibernazione (può esporre memoria kernel)
#   - Accesso a bpf(BPF_PROG_LOAD) per utenti non privilegiati

# Abilitare lockdown via kernel command line (GRUB):
# In /etc/default/grub, aggiungere:
# GRUB_CMDLINE_LINUX="... lockdown=integrity"
# oppure
# GRUB_CMDLINE_LINUX="... lockdown=confidentiality"

# Rigenerare GRUB
sudo grub2-mkconfig -o /boot/grub2/grub.cfg    # RHEL
sudo update-grub                                 # Debian
```

### Restrizioni kexec

```bash
# kexec permette di caricare un nuovo kernel senza reboot hardware.
# Un attaccante potrebbe usarlo per caricare un kernel malevolo.

# Verificare se kexec è abilitato
cat /proc/sys/kernel/kexec_load_disabled
# 0 = abilitato, 1 = disabilitato

# Disabilitare kexec (persistente via sysctl)
echo "kernel.kexec_load_disabled = 1" | sudo tee /etc/sysctl.d/90-kexec.conf
sudo sysctl -p /etc/sysctl.d/90-kexec.conf

# NOTA: una volta impostato a 1, NON può essere riportato a 0
# senza reboot (è un parametro "write-once")

# Verificare i moduli relativi
lsmod | grep kexec
# Se non serve, blacklistare il modulo:
echo "blacklist kexec" | sudo tee /etc/modprobe.d/kexec.conf
```

### Yama LSM — Parametri Avanzati

```bash
# Yama è un Linux Security Module che limita le operazioni di debug.
# Il parametro ptrace_scope è già coperto nella sezione sysctl.
# Qui approfondiamo l'integrazione con altri LSM.

# Verificare i LSM attivi
cat /sys/kernel/security/lsm
# Output tipico: lockdown,capability,yama,apparmor
# oppure:       lockdown,capability,yama,selinux

# Assicurarsi che Yama sia nella lista dei LSM attivi
# In /etc/default/grub:
# GRUB_CMDLINE_LINUX="... lsm=lockdown,capability,yama,apparmor"

# Parametri Yama in dettaglio:
# ptrace_scope=0 — classico: qualsiasi processo può tracciare i propri figli
# ptrace_scope=1 — solo processi con relazione parent possono tracciare
#                   (blocca gdb attach a processi arbitrari)
# ptrace_scope=2 — solo processi con CAP_SYS_PTRACE possono tracciare
# ptrace_scope=3 — ptrace completamente disabilitato (anche per root)
#                   ATTENZIONE: rompe gdb, strace, ltrace per chiunque

# Raccomandazione CIS: ptrace_scope >= 1
# Raccomandazione STIG: ptrace_scope = 2
# Ambienti critici: ptrace_scope = 3
```

---

## Filesystem Hardening Avanzato

Oltre alle opzioni di mount base (noexec, nosuid, nodev) già trattate nella sezione CIS, esistono tecniche avanzate per ridurre ulteriormente la superficie di attacco del filesystem.

### hidepid per /proc

```bash
# Di default, qualsiasi utente può vedere i processi di tutti gli altri utenti
# tramite /proc. hidepid limita questa visibilità.

# hidepid=0 — default, tutti vedono tutto
# hidepid=1 — utenti possono vedere solo i propri processi in /proc
#              (ma possono ancora accedere a /proc/PID se conoscono il PID)
# hidepid=2 — utenti vedono SOLO i propri processi, /proc/PID di altri
#              non è accessibile (come se non esistesse)
# hidepid=invisible — (kernel 5.8+) equivalente a hidepid=2 ma con
#                      supporto per il gruppo gid= exception

# Applicare hidepid=2 con eccezione per il gruppo monitoring
# 1. Creare il gruppo
sudo groupadd -r proc-readers

# 2. Aggiungere gli utenti che devono vedere tutti i processi
sudo usermod -aG proc-readers monitoring_user
sudo usermod -aG proc-readers nagios

# 3. Montare /proc con hidepid
# In /etc/fstab:
# proc /proc proc defaults,hidepid=2,gid=proc-readers 0 0

# Applicare senza reboot
sudo mount -o remount,hidepid=2,gid=$(getent group proc-readers | cut -d: -f3) /proc

# Verificare
su - normaluser -c "ls /proc/ | head -5"
# Deve mostrare solo i PID dell'utente + pseudo-file di sistema

# NOTA: alcuni servizi (es. Prometheus node_exporter, systemd-logind)
# potrebbero necessitare di essere nel gruppo proc-readers
```

### Hardening di tmpfs

```bash
# /dev/shm è un tmpfs usato per la shared memory POSIX.
# Senza hardening, può essere usato per eseguire payload malevoli.

# Verificare i mount attuali
mount | grep -E "tmpfs|shm"

# /etc/fstab — hardening dei tmpfs
# /dev/shm con restrizioni massime
tmpfs  /dev/shm  tmpfs  defaults,nodev,nosuid,noexec,size=256M  0 0

# /tmp come tmpfs separato (se non è già una partizione dedicata)
tmpfs  /tmp      tmpfs  defaults,nodev,nosuid,noexec,size=2G    0 0

# /run con dimensione limitata
tmpfs  /run      tmpfs  defaults,nodev,nosuid,mode=0755,size=512M  0 0

# Applicare
sudo mount -o remount,nodev,nosuid,noexec /dev/shm
sudo mount -o remount,nodev,nosuid,noexec /tmp

# Verificare che le restrizioni siano attive
mount | grep -E "/tmp|/dev/shm" | grep -o "noexec\|nosuid\|nodev"
```

### Protezione delle Directory World-Writable

```bash
# Trovare tutte le directory world-writable
sudo find / -xdev -type d -perm -0002 -print 2>/dev/null

# Impostare lo sticky bit dove manca (previene cancellazione
# di file altrui nelle directory condivise)
sudo find / -xdev -type d -perm -0002 ! -perm -1000 -exec chmod +t {} \;

# Trovare file world-writable (potenziale rischio)
sudo find / -xdev -type f -perm -0002 -print 2>/dev/null

# Trovare file senza proprietario (indicatore di compromissione)
sudo find / -xdev \( -nouser -o -nogroup \) -print 2>/dev/null
```

---

## User Account Hardening

### UMASK Restrittivo

```bash
# Il UMASK di default è spesso 022, che crea file leggibili da tutti.
# UMASK 027 impedisce a "others" di leggere i nuovi file.

# Impostare UMASK globale a 027
# In /etc/login.defs:
UMASK    027

# In /etc/profile.d/umask.sh (per sessioni di login):
umask 027

# In /etc/bashrc (RHEL) o /etc/bash.bashrc (Debian):
umask 027

# Verificare
umask
# Output: 0027

# Significato:
# File creati: 640 (rw-r-----)  → proprietario rw, gruppo r, altri nulla
# Dir create:  750 (rwxr-x---)  → proprietario rwx, gruppo rx, altri nulla
```

### login.defs — Configurazione Completa

```bash
# /etc/login.defs — parametri di default per nuovi account

# Password aging
PASS_MAX_DAYS   365          # Scadenza massima password
PASS_MIN_DAYS   7            # Giorni minimi tra cambi password
PASS_MIN_LEN    14           # Lunghezza minima (PAM ha priorità)
PASS_WARN_AGE   14           # Avviso prima della scadenza

# UID/GID ranges
UID_MIN         1000         # UID minimo per utenti normali
UID_MAX         60000        # UID massimo per utenti normali
SYS_UID_MIN     100          # UID minimo per utenti di sistema
SYS_UID_MAX     999          # UID massimo per utenti di sistema

# UMASK
UMASK           027          # Default per nuovi file/directory

# Crittografia password
ENCRYPT_METHOD  SHA512       # Usare SHA-512 (non MD5 o DES)
SHA_CRYPT_MIN_ROUNDS 10000   # Rounds minimo per SHA-512

# Home directory
CREATE_HOME     yes          # Creare la home directory automaticamente
HOME_MODE       0700         # Permessi della home directory (solo proprietario)

# Rimuovere file da /etc/skel se non necessari
# /etc/skel/ contiene i file copiati nelle nuove home directory

# Verificare la configurazione corrente
grep -v "^#\|^$" /etc/login.defs
```

### Shell nologin e Account di Servizio

```bash
# Gli account di servizio NON devono avere una shell di login.
# Usare /usr/sbin/nologin o /bin/false.

# Trovare account con shell di login che non dovrebbero averla
awk -F: '$3 >= 1000 && $7 != "/usr/sbin/nologin" && $7 != "/bin/false" {print $1, $7}' /etc/passwd

# Trovare account di sistema con shell di login (potenziale rischio)
awk -F: '$3 < 1000 && $3 != 0 && $7 != "/usr/sbin/nologin" && $7 != "/bin/false" {print $1, $7}' /etc/passwd

# Impostare nologin per account di servizio
sudo usermod -s /usr/sbin/nologin www-data
sudo usermod -s /usr/sbin/nologin mysql
sudo usermod -s /usr/sbin/nologin nobody
sudo usermod -s /usr/sbin/nologin postfix

# Bloccare account inutilizzati
sudo usermod -L old_user          # Blocca la password
sudo usermod -e 1 old_user        # Imposta account come scaduto

# Trovare account senza password (CRITICO)
sudo awk -F: '$2 == "" {print $1}' /etc/shadow

# Trovare account con UID 0 (solo root dovrebbe averlo)
awk -F: '$3 == 0 {print $1}' /etc/passwd
```

### Sudo Hardening — Parametri Aggiuntivi

```bash
# Complemento alla sezione Sudo Hardening precedente.
# Parametri spesso trascurati:

# /etc/sudoers.d/99-extra-hardening

# Rimuovere NOPASSWD da QUALSIASI regola legacy
# Verificare:
sudo grep -r "NOPASSWD" /etc/sudoers /etc/sudoers.d/
# Rimuovere ogni NOPASSWD non strettamente necessario

# Richiedere password anche per sudo -l (listing)
Defaults    listpw=always

# Non preservare la home directory dell'utente chiamante
Defaults    always_set_home

# Limitare i comandi sudo a quelli con path assoluto
Defaults    secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Notifica via mail per tentativi sudo falliti
Defaults    mail_badpass
Defaults    mail_no_user
Defaults    mailto="admin@example.com"

# Timeout più breve per ambienti critici (default 5 min)
Defaults    timestamp_timeout=3

# Richiedere un TTY (impedisce sudo da script non interattivi)
Defaults    requiretty
```

---

## Network Hardening Avanzato

Oltre ai parametri sysctl già coperti, il network hardening include la gestione di IPv6, TCP wrappers e restrizioni ICMP granulari.

### Disabilitare IPv6 se Non Utilizzato

```bash
# Se IPv6 non è necessario, disabilitarlo riduce la superficie di attacco.
# ATTENZIONE: alcune applicazioni (es. Java) potrebbero dipendere da IPv6
# anche per connessioni locali. Testare prima.

# Metodo 1: via sysctl (raccomandato)
cat > /etc/sysctl.d/90-disable-ipv6.conf << 'EOF'
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
net.ipv6.conf.lo.disable_ipv6 = 1
EOF
sudo sysctl --system

# Metodo 2: via kernel command line (più aggressivo, disabilita nel kernel)
# In /etc/default/grub:
# GRUB_CMDLINE_LINUX="... ipv6.disable=1"
# sudo grub2-mkconfig -o /boot/grub2/grub.cfg

# Verificare
ip -6 addr show
# Non deve mostrare indirizzi IPv6

# Se il sistema usa systemd-networkd o NetworkManager,
# disabilitare IPv6 anche nel profilo di connessione:
# [ipv6]
# method=disabled
```

### TCP Wrappers (hosts.allow / hosts.deny)

```bash
# TCP wrappers forniscono un layer ACL per servizi che li supportano.
# NOTA: molti servizi moderni non usano più TCP wrappers (sshd
# nelle versioni recenti di OpenSSH ha rimosso il supporto).
# Verificare: ldd /usr/sbin/sshd | grep libwrap

# /etc/hosts.deny — default deny
ALL: ALL

# /etc/hosts.allow — eccezioni specifiche
sshd: 10.0.0.0/24
sshd: 10.0.1.0/24
in.tftpd: 10.0.0.0/24

# Ordine di valutazione: hosts.allow prima, poi hosts.deny

# Verificare se un servizio supporta TCP wrappers
ldd /usr/sbin/sshd | grep libwrap
# Se presente: il servizio supporta TCP wrappers
# Se assente: usare firewall (nftables) per il controllo degli accessi
```

### Restrizioni ICMP Granulari

```bash
# Oltre ai parametri sysctl base, configurare restrizioni ICMP
# granulari tramite nftables:

# Limitare il rate dei ping in ingresso
# (già presente nella configurazione nftables base, qui approfondiamo)

# Bloccare ICMP timestamp requests (information disclosure)
sudo nft add rule inet filter input icmp type timestamp-request drop
sudo nft add rule inet filter input icmp type timestamp-reply drop

# Bloccare ICMP address mask requests
sudo nft add rule inet filter input icmp type address-mask-request drop
sudo nft add rule inet filter input icmp type address-mask-reply drop

# Permettere solo ICMP essenziali con rate limiting
# echo-request: ping (limitato)
# destination-unreachable: necessario per Path MTU Discovery
# time-exceeded: necessario per traceroute diagnostico
# parameter-problem: necessario per diagnostica

# Bloccare tutto il resto ICMP
sudo nft add rule inet filter input icmp type { \
    redirect, router-advertisement, router-solicitation, \
    info-request, info-reply \
} drop
```

### Hardening di Source Routing e Forwarding

```bash
# Source routing permette al mittente di specificare il percorso del pacchetto.
# Deve essere SEMPRE disabilitato su server non-router.

# Verificare (già in sysctl ma qui il check esplicito):
sysctl net.ipv4.conf.all.accept_source_route
sysctl net.ipv4.conf.all.send_redirects
sysctl net.ipv4.conf.all.rp_filter

# Se il server NON è un router, disabilitare IP forwarding:
sysctl net.ipv4.ip_forward
# Deve essere 0

# Reverse path filtering (anti-spoofing):
# rp_filter=1 — strict mode (raccomandato per server)
#   Accetta pacchetti solo se il percorso di ritorno usa la stessa interfaccia
# rp_filter=2 — loose mode (per server multi-homed)
#   Accetta se il percorso di ritorno esiste su qualsiasi interfaccia
```

---

## Systemd Service Hardening

systemd offre un set di direttive di sandboxing che limitano cosa un servizio può fare, anche se compromesso. Queste direttive sono la forma più pratica di privilege restriction per i servizi Linux moderni.

### Matrice delle Direttive di Sicurezza

```
┌────────────────────────┬───────────────────────────────────────────────┬────────┐
│ Direttiva              │ Effetto                                      │ Rischio│
│                        │                                              │ rottura│
├────────────────────────┼───────────────────────────────────────────────┼────────┤
│ ProtectSystem=strict   │ Monta / e /usr come read-only               │ Medio  │
│ ProtectSystem=full     │ Monta /usr e /boot come read-only           │ Basso  │
│ ProtectHome=yes        │ /home, /root, /run/user inaccessibili       │ Basso  │
│ ProtectHome=tmpfs      │ Monta tmpfs vuoto al posto di /home         │ Basso  │
│ PrivateTmp=yes         │ Mount namespace privato per /tmp e /var/tmp  │ Basso  │
│ PrivateDevices=yes     │ Solo /dev/null, /dev/zero, /dev/random       │ Basso  │
│ PrivateNetwork=yes     │ Namespace di rete isolato (no accesso rete)  │ Alto   │
│ PrivateUsers=yes       │ User namespace — servizio vede solo sé stesso│ Medio  │
│ NoNewPrivileges=yes    │ Impedisce escalation di privilegi            │ Basso  │
│ ProtectKernelTunables  │ /proc/sys, /sys read-only                   │ Basso  │
│ =yes                   │                                              │        │
│ ProtectKernelModules   │ Impedisce caricamento/scaricamento moduli    │ Basso  │
│ =yes                   │                                              │        │
│ ProtectKernelLogs=yes  │ Blocca accesso a /dev/kmsg e /proc/kmsg     │ Basso  │
│ ProtectControlGroups   │ Rende /sys/fs/cgroup read-only              │ Basso  │
│ =yes                   │                                              │        │
│ ProtectClock=yes       │ Impedisce modifica dell'orologio di sistema  │ Basso  │
│ ProtectHostname=yes    │ Impedisce modifica dell'hostname             │ Basso  │
│ RestrictNamespaces=yes │ Impedisce creazione di nuovi namespace       │ Medio  │
│ RestrictSUIDSGID=yes   │ Impedisce creazione di file SUID/SGID        │ Basso  │
│ LockPersonality=yes    │ Blocca la personalità del processo (ABI)     │ Basso  │
│ MemoryDenyWriteExecute │ Impedisce memoria W+X (anti-shellcode)       │ Medio  │
│ =yes                   │                                              │        │
│ RestrictRealtime=yes   │ Impedisce scheduling real-time               │ Basso  │
│ RemoveIPC=yes          │ Rimuove oggetti IPC all'uscita del servizio  │ Basso  │
│ SystemCallFilter=      │ Whitelist di syscall permesse                │ Alto   │
│  @system-service       │                                              │        │
│ SystemCallArchitectures│ Limita a x86-64 (blocca compat 32-bit)       │ Basso  │
│ =native                │                                              │        │
│ CapabilityBoundingSet= │ Limita le capabilities Linux disponibili     │ Medio  │
│                        │                                              │        │
│ ReadOnlyPaths=         │ Rende specifici percorsi read-only           │ Basso  │
│ InaccessiblePaths=     │ Rende specifici percorsi inaccessibili       │ Medio  │
│ ReadWritePaths=        │ Eccezioni read-write per ProtectSystem       │ Basso  │
└────────────────────────┴───────────────────────────────────────────────┴────────┘
```

### Esempio: Hardening Completo di un Servizio

```ini
# /etc/systemd/system/myapp.service.d/hardening.conf
# Override per aggiungere sandboxing a un servizio esistente

[Service]
# Filesystem
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
PrivateDevices=yes
ReadWritePaths=/var/lib/myapp /var/log/myapp

# Rete (rimuovere se il servizio necessita di rete)
# PrivateNetwork=yes

# Kernel
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectKernelLogs=yes
ProtectControlGroups=yes
ProtectClock=yes
ProtectHostname=yes

# Privilegi
NoNewPrivileges=yes
RestrictSUIDSGID=yes
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE

# Syscall
SystemCallFilter=@system-service
SystemCallFilter=~@mount @reboot @swap @clock @debug @raw-io @cpu-emulation
SystemCallArchitectures=native

# Memory
MemoryDenyWriteExecute=yes
LockPersonality=yes

# Namespace
RestrictNamespaces=yes
RestrictRealtime=yes

# Cleanup
RemoveIPC=yes

# User/Group (non eseguire come root se possibile)
User=myapp
Group=myapp
```

```bash
# Applicare l'override
sudo systemctl daemon-reload
sudo systemctl restart myapp

# Verificare le restrizioni attive
systemd-analyze security myapp
# Output: punteggio di sicurezza (target: < 5.0, ideale < 2.0)
# OVERALL EXPOSURE LEVEL for myapp.service: 1.4 OK

# Verificare che il servizio funzioni correttamente
systemctl status myapp
journalctl -u myapp --since "5 min ago"
```

### Socket Activation

```bash
# La socket activation permette di avviare un servizio solo quando
# arriva una connessione, riducendo la superficie di attacco temporale.

# Esempio: attivare myapp solo quando qualcuno si connette alla porta 8080

# /etc/systemd/system/myapp.socket
[Unit]
Description=MyApp Socket

[Socket]
ListenStream=8080
Accept=no
# Permessi del socket (per socket Unix):
# SocketMode=0660
# SocketUser=myapp
# SocketGroup=myapp

[Install]
WantedBy=sockets.target

# Il servizio myapp.service verrà avviato automaticamente al primo
# collegamento sulla porta 8080.

# Abilitare il socket (NON il service direttamente)
sudo systemctl enable --now myapp.socket
sudo systemctl disable myapp.service    # Disabilitare l'avvio diretto

# Verificare
sudo systemctl status myapp.socket
ss -tlnp | grep 8080
# Il socket è in ascolto, ma il servizio non è ancora avviato
```

---

## SSH — Restrizioni authorized_keys

Le restrizioni nel file `authorized_keys` permettono di limitare cosa una chiave SSH specifica può fare, anche se la chiave viene compromessa.

### Formato e Opzioni

```bash
# ~/.ssh/authorized_keys — formato esteso con restrizioni:
# opzioni chiave-tipo chiave-pubblica commento

# Restrizione per IP sorgente (from=)
# La chiave funziona SOLO se il client si connette da questi IP
from="10.0.0.0/24,10.0.1.5" ssh-ed25519 AAAA... admin@workstation

# Restrizione a un singolo comando (command=)
# La chiave può eseguire SOLO questo comando, indipendentemente
# da cosa il client richiede
command="/usr/local/bin/backup.sh" ssh-ed25519 AAAA... backup@cron

# Disabilitare port forwarding
no-port-forwarding ssh-ed25519 AAAA... restricted@user

# Disabilitare agent forwarding
no-agent-forwarding ssh-ed25519 AAAA... restricted@user

# Disabilitare allocazione PTY (no shell interattiva)
no-pty ssh-ed25519 AAAA... sftp-only@user

# Disabilitare X11 forwarding
no-X11-forwarding ssh-ed25519 AAAA... restricted@user

# Combinazione completa per una chiave di backup:
from="10.0.0.50",command="/usr/local/bin/backup.sh",no-port-forwarding,no-agent-forwarding,no-pty,no-X11-forwarding ssh-ed25519 AAAA... backup-key

# Variabile d'ambiente (restrict= è un alias per tutte le restrizioni)
# restrict equivale a: no-port-forwarding,no-agent-forwarding,
#   no-X11-forwarding,no-pty,no-user-rc
restrict,command="/usr/local/bin/status.sh" ssh-ed25519 AAAA... monitoring-key

# Permettere solo SFTP (con restrict + eccezione pty per alcune operazioni)
restrict,command="internal-sftp" ssh-ed25519 AAAA... sftp-user
```

### Scenari Operativi

```bash
# Scenario 1: chiave per backup rsync (solo dal server backup)
from="10.0.0.50",command="/usr/local/bin/validate-rsync.sh",restrict ssh-ed25519 AAAA... backup

# Lo script validate-rsync.sh verifica il comando originale:
cat > /usr/local/bin/validate-rsync.sh << 'SCRIPT'
#!/bin/bash
# $SSH_ORIGINAL_COMMAND contiene il comando che il client voleva eseguire
case "$SSH_ORIGINAL_COMMAND" in
    rsync\ --server\ --sender\ -logDtpre.iLsfxCIvu\ .\ /data/backup/*)
        exec $SSH_ORIGINAL_COMMAND
        ;;
    *)
        echo "ERRORE: comando non autorizzato: $SSH_ORIGINAL_COMMAND" >&2
        exit 1
        ;;
esac
SCRIPT
chmod 755 /usr/local/bin/validate-rsync.sh

# Scenario 2: chiave per monitoraggio Nagios/Zabbix
from="10.0.1.10",command="/usr/lib/nagios/plugins/check_disk -w 20% -c 10%",restrict ssh-ed25519 AAAA... nagios

# Scenario 3: chiave per deploy automatico (solo da CI/CD)
from="10.0.5.0/24",command="/opt/deploy/deploy.sh",restrict ssh-ed25519 AAAA... deploy-ci
```

---

## File Integrity Monitoring Avanzato

### AIDE — Configurazione Avanzata

Oltre alla configurazione base di AIDE già trattata, approfondiamo la personalizzazione delle regole e il workflow operativo.

```bash
# Regole personalizzate per ambienti specifici

# /etc/aide.conf — aggiunta di regole per web server
# Monitorare i binari di nginx/apache con hash SHA-512
WEBBIN = p+i+n+u+g+s+m+c+sha512

/usr/sbin/nginx WEBBIN
/usr/sbin/httpd WEBBIN
/usr/lib/apache2/modules/ WEBBIN

# Monitorare i contenuti web (detect defacement)
WEBDATA = p+n+u+g+sha256
/var/www/html/ WEBDATA
!/var/www/html/uploads/    # Escludere directory di upload dinamico

# Report in formato machine-readable
# In /etc/aide.conf:
report_url = file:/var/log/aide/aide-report.log
report_url = syslog:LOG_AUTH

# Check automatico con notifica strutturata
cat > /etc/cron.d/aide-daily << 'CRON'
0 4 * * * root /usr/sbin/aide --check 2>&1 | \
  grep -E "^(Added|Removed|Changed|Summary)" | \
  mail -s "[AIDE] $(hostname) - $(date +\%F) integrity report" admin@example.com
CRON
```

### Tripwire — Confronto con AIDE

```
┌──────────────────┬────────────────────────┬────────────────────────┐
│ Criterio         │ AIDE                   │ Tripwire (Open Source) │
├──────────────────┼────────────────────────┼────────────────────────┤
│ Licenza          │ GPL v2                 │ GPL v2 (OSS edition)   │
│ Complessità      │ Bassa — file config    │ Media — policy + config│
│ configurazione   │ singolo                │ separati, tw-encode    │
│ Hash supportati  │ SHA-256, SHA-512,      │ SHA-256, MD5,          │
│                  │ RIPEMD-160, CRC-32     │ CRC-32, Haval          │
│ Report           │ Testo, syslog          │ Testo, email           │
│ SELinux support  │ Sì (contesti nel check)│ Limitato               │
│ Performance      │ Veloce                 │ Comparabile            │
│ Pacchettizzato   │ apt/dnf in tutte le    │ EPEL per RHEL,         │
│                  │ distro principali      │ apt per Debian         │
│ Manutenzione     │ Attivo                 │ Meno attivo (OSS)      │
└──────────────────┴────────────────────────┴────────────────────────┘

Raccomandazione: AIDE nella maggior parte dei casi. Tripwire Enterprise (commerciale) per PCI DSS / SOX.
```

### osquery per File Integrity Monitoring

```bash
# Installare: https://osquery.io/downloads/official
sudo apt update && sudo apt install -y osquery

# /etc/osquery/osquery.conf — FIM con query SQL-like
cat > /etc/osquery/osquery.conf << 'OSQCONF'
{
  "file_paths": {
    "binaries": ["/usr/bin/%%", "/usr/sbin/%%", "/bin/%%", "/sbin/%%"],
    "configuration": ["/etc/%%"],
    "ssh_keys": ["/home/%/.ssh/%%", "/root/.ssh/%%"]
  },
  "schedule": {
    "file_events": { "query": "SELECT * FROM file_events;", "interval": 300 },
    "suid_binaries": { "query": "SELECT * FROM suid_bin;", "interval": 3600 }
  }
}
OSQCONF

sudo systemctl enable --now osqueryd
# osqueryi → SELECT * FROM file_events WHERE action = 'UPDATED' AND target_path LIKE '/etc/%';
```

## Scansione Automatizzata — Lynis e OpenSCAP

### Lynis — Audit Approfondito

```bash
sudo apt update && sudo apt install -y lynis
sudo lynis audit system --profile /etc/lynis/custom.prf

# Profilo personalizzato /etc/lynis/custom.prf
cat > /etc/lynis/custom.prf << 'LYNPRF'
skip-test=NETW-2705
skip-test=USB-1000
min-hardening-index=75
LYNPRF

# Audit per categoria
sudo lynis audit system --tests-from-group "kernel"

# Report e parsing
sudo lynis audit system --report-file /var/log/lynis-report.dat
grep "^hardening_index" /var/log/lynis-report.dat

# Cron settimanale
0 2 * * 0 root /usr/sbin/lynis audit system --cronjob --quiet
```

### OpenSCAP — Compliance Scanning

```bash
sudo apt install -y libopenscap8 openscap-scanner   # Debian
sudo dnf install -y openscap-scanner scap-security-guide   # RHEL

# Profili disponibili in scap-security-guide:
# cis_server_l1, cis_workstation_l2, stig, pci-dss
oscap info /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml

# Scansione CIS Level 1 con report HTML
sudo oscap xccdf eval \
  --profile xccdf_org.ssgproject.content_profile_cis_server_l1 \
  --results /tmp/oscap-cis-results.xml \
  --report /tmp/oscap-cis-report.html \
  /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml

# Generare fix script (revisionare SEMPRE prima di eseguire!)
sudo oscap xccdf generate fix --fix-type bash \
  --result-id "" /tmp/oscap-cis-results.xml > /tmp/oscap-remediation.sh

# Generare fix Ansible
sudo oscap xccdf generate fix --fix-type ansible \
  --result-id "" /tmp/oscap-cis-results.xml > /tmp/oscap-remediation.yml
```

---

## Container Host Hardening

Container compromesso = pivot per attaccare l'host se la configurazione non è corretta.

### Docker Daemon — Configurazione Sicura

```bash
# /etc/docker/daemon.json
{
  "icc": false,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "5"
  },
  "no-new-privileges": true,
  "userland-proxy": false,
  "live-restore": true,
  "userns-remap": "default",
  "storage-driver": "overlay2",
  "default-ulimits": {
    "nofile": {
      "Name": "nofile",
      "Hard": 65535,
      "Soft": 32768
    },
    "nproc": {
      "Name": "nproc",
      "Hard": 4096,
      "Soft": 2048
    }
  }
}

# icc:false=no inter-container, no-new-privileges=no escalation
# userland-proxy:false=nftables per port mapping, userns-remap=UID mapping
sudo systemctl restart docker
docker info | grep -E "Security|Remap|Storage|Logging"
```

### Docker Rootless Mode

```bash
# Daemon Docker come utente non-root — elimina container escape verso root
sudo apt install -y uidmap dbus-user-session fuse-overlayfs   # Debian
sudo usermod --add-subuids 100000-165535 --add-subgids 100000-165535 $USER
dockerd-rootless-setuptool.sh install
export DOCKER_HOST=unix://$XDG_RUNTIME_DIR/docker.sock
docker run --rm hello-world

# Limitazioni: no porte <1024, no --network host, I/O overlay più lento
```

### User Namespace Remapping

```bash
# Alternativa a rootless: "userns-remap": "default" in daemon.json
# Mappa UID 0 nel container → UID 100000 sull'host
# Richiede range in /etc/subuid e /etc/subgid (dockremap:100000:65536)
sudo systemctl restart docker
docker run --rm alpine id    # root nel container
ps aux | grep "alpine"       # UID 100000 sull'host
```

### AppArmor e seccomp per Container

```bash
# seccomp di default blocca ~44 syscall pericolose
docker run --rm alpine grep Seccomp /proc/self/status   # 2 = filter attivo
docker run --security-opt seccomp=/path/to/custom-seccomp.json myapp

# AppArmor: profilo docker-default automatico
docker run --security-opt apparmor=my-custom-profile myapp

# MAI --privileged in produzione (disabilita seccomp + AppArmor + tutte le cap)
docker inspect --format='{{.HostConfig.Privileged}} {{.HostConfig.SecurityOpt}}' $(docker ps -q)
```

---

## Preparazione agli Incidenti — Forensic Readiness

Preparazione forense NON opzionale — senza di essa, indagine post-incidente inaffidabile.

### Ordine di Raccolta dei Dati Volatili

```
RFC 3227 — "Guidelines for Evidence Collection and Archiving"

Raccogliere i dati in ordine di volatilità (dal più volatile al meno):

┌─────┬────────────────────────────┬───────────────────────────────┐
│ Pri │ Tipo di dato               │ Comando di raccolta           │
├─────┼────────────────────────────┼───────────────────────────────┤
│  1  │ Registri CPU, cache        │ (non catturabile da userspace)│
│  2  │ Tabelle di routing, ARP,   │ ip route; ip neigh;           │
│     │ connessioni di rete        │ ss -tulnpa; conntrack -L      │
│  3  │ Processi in esecuzione     │ ps auxf; /proc/*/cmdline      │
│  4  │ Memoria RAM                │ dd if=/dev/mem; LiME module   │
│     │                            │ avml (Microsoft, open-source) │
│  5  │ File temporanei, /tmp      │ find /tmp /var/tmp -ls        │
│  6  │ Disco (filesystem)         │ dd if=/dev/sda of=disk.img    │
│  7  │ Log remoti / SIEM          │ Già preservati se centralizzati│
│  8  │ Configurazione di rete     │ iptables-save; nft list       │
│     │ fisica (switch, router)    │ ruleset                       │
│  9  │ Media archiviali (backup)  │ Consultare policy di backup   │
└─────┴────────────────────────────┴───────────────────────────────┘

REGOLA: NON spegnere il sistema prima di aver raccolto i dati volatili.
Lo spegnimento distrugge: processi, connessioni, memoria, /proc.
```

### Log Retention Policy

```bash
# /etc/systemd/journald.conf
[Journal]
Storage=persistent
SystemMaxUse=4G
MaxRetentionSec=180d
Compress=yes
ForwardToSyslog=yes
# sudo systemctl restart systemd-journald

# /etc/logrotate.d/hardening-retention
/var/log/auth.log /var/log/syslog /var/log/kern.log {
    rotate 52
    weekly
    compress
    delaycompress
    create 0640 root adm
}

# CRITICO: log centralizzati su server remoto (rsyslog/syslog-ng)
# *.* @@logserver.example.com:514   ← sopravvivono a root compromise locale
```

### Toolkit di Risposta agli Incidenti

```bash
# Preparare PRIMA che serva. Conservare su USB write-protect.
# Contenuto: binari statici (busybox, strace, lsof, tcpdump, dd, ss, ps)
mkdir -p /opt/ir-toolkit/{bin,conf,hashes}
find /opt/ir-toolkit/bin -type f -exec sha256sum {} \; > /opt/ir-toolkit/hashes/manifest.sha256

# Script raccolta rapida dati volatili (RFC 3227)
cat > /opt/ir-toolkit/collect.sh << 'IRSCRIPT'
#!/bin/bash
OUTDIR="/tmp/ir-$(hostname)-$(date -u +%FT%H%M%SZ)"
mkdir -p "$OUTDIR"
ss -tulnpa > "$OUTDIR/net.txt" 2>&1
ip route show >> "$OUTDIR/net.txt" 2>&1
ip neigh show >> "$OUTDIR/net.txt" 2>&1
ps auxf > "$OUTDIR/procs.txt" 2>&1
who > "$OUTDIR/users.txt" 2>&1
find /tmp /var/tmp /dev/shm -ls > "$OUTDIR/temp.txt" 2>&1
lsmod > "$OUTDIR/modules.txt" 2>&1
IRSCRIPT
chmod 700 /opt/ir-toolkit/collect.sh
```

---

## Automazione CIS Benchmark — Compliance-as-Code

### Ansible Lockdown Roles

```bash
# https://github.com/ansible-lockdown — ruoli: RHEL9-CIS, UBUNTU22-CIS, DEBIAN12-CIS, RHEL9-STIG
ansible-galaxy install git+https://github.com/ansible-lockdown/RHEL9-CIS.git

cat > cis-hardening.yml << 'ANSIBLE'
---
- name: Applicare CIS Benchmark Level 1
  hosts: servers
  become: yes
  vars:
    rhel9cis_level_1: true
    rhel9cis_level_2: false
    rhel9cis_rule_1_4_1: false      # Secure Boot (gestito manualmente)
    rhel9cis_rule_3_4_1_1: false    # nftables (configurato separatamente)
  roles:
    - RHEL9-CIS
ANSIBLE

ansible-playbook cis-hardening.yml --check --diff   # Dry run
ansible-playbook cis-hardening.yml --diff            # Applicare
```

### Compliance-as-Code Pipeline

```bash
# CI/CD: OpenSCAP in staging ad ogni merge, blocca deploy se compliance < soglia
cat > compliance-check.sh << 'CICD'
#!/bin/bash
set -euo pipefail
PROFILE="xccdf_org.ssgproject.content_profile_cis_server_l1"
CONTENT="/usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml"
RESULTS="/tmp/compliance-results.xml"
THRESHOLD=90

oscap xccdf eval --profile "$PROFILE" --results "$RESULTS" "$CONTENT" || true
TOTAL=$(xmllint --xpath "count(//rule-result)" "$RESULTS")
PASS=$(xmllint --xpath "count(//rule-result[result='pass'])" "$RESULTS")
PERCENT=$((PASS * 100 / TOTAL))
echo "Compliance: ${PERCENT}% (${PASS}/${TOTAL})"
[ "$PERCENT" -lt "$THRESHOLD" ] && echo "FAIL: sotto soglia ${THRESHOLD}%" && exit 1
CICD
chmod 755 compliance-check.sh
```

## USBGuard — Protezione da Dispositivi USB Malevoli

### Il Problema: Attacchi via USB

I dispositivi USB rappresentano uno dei vettori di attacco fisico più pericolosi. Attacchi come **BadUSB**, **Rubber Ducky** e **USB Killer** sfruttano il fatto che i sistemi operativi, per impostazione predefinita, accettano qualsiasi dispositivo USB collegato senza alcuna verifica. Un dispositivo apparentemente innocuo (una chiavetta, un caricatore) può emulare una tastiera ed eseguire comandi arbitrari in pochi secondi, oppure estrarre dati sensibili tramite interfacce di rete emulate.

Il framework **USBGuard** risolve questo problema implementando una **policy di autorizzazione USB a livello kernel**, basata su regole di whitelist/blacklist che controllano quali dispositivi possono essere attivati sul sistema.

### Architettura di USBGuard

USBGuard opera attraverso tre componenti principali:

1. **usbguard-daemon**: il demone che intercetta gli eventi USB dal kernel tramite il sottosistema udev/sysfs e applica le regole di policy
2. **Policy file** (`/etc/usbguard/rules.conf`): contiene le regole di autorizzazione in formato dichiarativo
3. **IPC interface**: interfaccia di comunicazione che permette agli strumenti CLI (`usbguard`) di interagire con il demone

Il flusso operativo è il seguente:
- Quando un dispositivo USB viene collegato, il kernel lo rileva ma **non lo attiva**
- Il demone USBGuard valuta il dispositivo contro le regole di policy
- In base al risultato, il dispositivo viene **autorizzato** (`allow`), **bloccato** (`block`) o **rifiutato** (`reject`)
- La differenza tra `block` e `reject`: block mantiene il dispositivo visibile ma inattivo, reject lo rimuove completamente dal bus USB

### Installazione e Configurazione

```bash
# Installazione su distribuzioni RHEL/Fedora
dnf install usbguard

# Installazione su Debian/Ubuntu
apt install usbguard

# Generare la policy iniziale basata sui dispositivi attualmente collegati
# IMPORTANTE: eseguire solo quando tutti i dispositivi legittimi sono collegati
usbguard generate-policy > /etc/usbguard/rules.conf

# Abilitare e avviare il servizio
systemctl enable --now usbguard
```

### Sintassi delle Regole

La sintassi delle regole USBGuard è espressiva e permette di definire criteri granulari:

```
# Formato: <target> <device_specification>
# target: allow | block | reject

# Permettere tutti i dispositivi HID (tastiere, mouse) di un vendor specifico
allow id 046d:* with-interface equals { 03:01:01 03:01:02 }
  # 046d = Logitech, 03:01:01 = HID keyboard, 03:01:02 = HID mouse

# Permettere una specifica chiavetta USB per hash
allow id 0781:5581 serial "ABC123456789" hash "a1b2c3d4..."

# Bloccare dispositivi con interfacce miste (potenziale BadUSB)
# Un dispositivo che dichiara sia storage che HID è sospetto
block with-interface one-of { 08:*:* 03:00:* 03:01:* }

# Bloccare tutti i dispositivi di classe network (prevenire exfiltrazione)
block with-interface equals { 02:06:00 }

# Regola default: bloccare tutto ciò che non è esplicitamente permesso
block

# Rifiutare (reject) dispositivi con VID/PID non definiti
reject id *:*
```

### Regole Anti-BadUSB Avanzate

Il principale indicatore di un attacco BadUSB è un dispositivo che presenta **interfacce multiple incongruenti**. Una chiavetta USB legittima dichiara solo l'interfaccia Mass Storage (classe 08), mentre un dispositivo BadUSB potrebbe dichiarare sia Mass Storage che HID (classe 03):

```
# Bloccare dispositivi con combinazione sospetta di interfacce
# Mass Storage + HID = altamente sospetto
block with-interface all-of { 08:*:* 03:*:* }

# Bloccare dispositivi che cambiano interfaccia dopo il collegamento
# USBGuard rileva la modifica dell'interfaccia e applica la regola
block if changed-interface
```

### Gestione Operativa

```bash
# Listare tutti i dispositivi USB attualmente noti
usbguard list-devices

# Permettere temporaneamente un dispositivo (per ID sequenziale mostrato da list-devices)
usbguard allow-device 15

# Bloccare un dispositivo specifico
usbguard block-device 15

# Appendere una nuova regola permanente alla policy
usbguard append-rule "allow id 0781:5581 serial \"XYZ\" name \"SanDisk Ultra\""

# Monitorare in tempo reale gli eventi USB
usbguard watch
```

### Integrazione con auditd

Per tracciare tutti gli eventi USB nel sistema di audit:

```bash
# Regole auditd per monitorare USBGuard
-w /etc/usbguard/rules.conf -p wa -k usbguard-policy
-w /etc/usbguard/usbguard-daemon.conf -p wa -k usbguard-config

# Il demone USBGuard scrive inoltre i propri log in:
# /var/log/usbguard/usbguard-audit.log
```

### Considerazioni CIS/STIG

CIS Benchmark Level 2 raccomanda la disabilitazione di USB storage come controllo minimo (`blacklist usb-storage` in `/etc/modprobe.d/`). USBGuard va oltre, fornendo un controllo granulare a livello di dispositivo singolo anziché disabilitare un'intera classe di dispositivi, ed è quindi la soluzione preferita per ambienti che necessitano di un equilibrio tra sicurezza e usabilità.

---

## OSSEC HIDS — Intrusion Detection Host-Based

### Panoramica

**OSSEC** (Open Source Security Event Correlator) è un sistema di intrusion detection host-based (HIDS) maturo e ampiamente adottato. A differenza di AIDE che si limita al file integrity monitoring, OSSEC offre un framework completo che include:

- **File integrity monitoring** in tempo reale
- **Log analysis** con regole di correlazione
- **Rootkit detection** attiva
- **Active response** automatizzata (blocco IP, kill di processi)
- **Architettura manager/agent** per deployment distribuiti

Il fork attivamente mantenuto è **Wazuh**, che estende OSSEC con dashboard web, integrazione ELK e compliance mapping automatico a CIS/PCI-DSS/GDPR.

### Architettura Manager/Agent

```
┌──────────────────────────────────────────────────┐
│                  OSSEC Manager                     │
│  ┌─────────────┐  ┌──────────┐  ┌──────────────┐│
│  │ analysisd    │  │ remoted  │  │ maild        ││
│  │ (correlazione│  │ (comm    │  │ (alerting)   ││
│  │  eventi)     │  │  agent)  │  │              ││
│  └──────┬──────┘  └────┬─────┘  └──────────────┘│
│         │              │                          │
│         ▼              │                          │
│  ┌─────────────┐       │                          │
│  │ rules/       │       │                          │
│  │ decoders/    │       │                          │
│  └─────────────┘       │                          │
└────────────────────────┼──────────────────────────┘
                         │ porta 1514 (encrypted)
          ┌──────────────┼──────────────┐
          │              │              │
    ┌─────▼───┐   ┌─────▼───┐   ┌─────▼───┐
    │ Agent 1 │   │ Agent 2 │   │ Agent 3 │
    │ (web    │   │ (db     │   │ (app    │
    │  server)│   │  server)│   │  server)│
    └─────────┘   └─────────┘   └─────────┘
```

### Componenti dell'Agent

Ogni agent OSSEC esegue i seguenti moduli:

| Modulo | Funzione |
|--------|----------|
| `logcollector` | Raccolta log da file, syslog, journald, Windows EventLog |
| `syscheck` | File integrity monitoring — hash, permessi, owner, attributi |
| `rootcheck` | Scansione rootkit, file sospetti, porte nascoste |
| `agent-auth` | Registrazione e autenticazione al manager |

### Installazione e Configurazione Base

```bash
# Installazione manager (server centrale)
# Scaricare da https://www.ossec.net/downloads/
tar xzf ossec-hids-3.7.0.tar.gz
cd ossec-hids-3.7.0
./install.sh
# Selezionare "server" come tipo di installazione

# Installazione agent (su ogni host monitorato)
./install.sh
# Selezionare "agent" come tipo di installazione
# Indicare l'IP del manager

# Registrazione dell'agent sul manager
/var/ossec/bin/manage_agents
# Opzione (A) per aggiungere un agent
# Esportare la chiave e importarla sull'agent

# Avvio
/var/ossec/bin/ossec-control start
```

### Configurazione File Integrity Monitoring (syscheck)

```xml
<!-- /var/ossec/etc/ossec.conf — sezione syscheck -->
<syscheck>
  <!-- Frequenza di controllo in secondi (6 ore) -->
  <frequency>21600</frequency>

  <!-- Monitoraggio in tempo reale per directory critiche -->
  <directories realtime="yes" check_all="yes">/etc,/usr/bin,/usr/sbin</directories>
  <directories realtime="yes" check_all="yes">/boot,/usr/local/bin</directories>

  <!-- Monitorare le modifiche a file specifici -->
  <directories realtime="yes" report_changes="yes">/etc/passwd,/etc/shadow</directories>
  <directories realtime="yes" report_changes="yes">/etc/sudoers,/etc/ssh/sshd_config</directories>

  <!-- Directory da ignorare (log, temp, cache) -->
  <ignore>/etc/mtab</ignore>
  <ignore>/etc/resolv.conf</ignore>
  <ignore type="sregex">.log$|.tmp$</ignore>

  <!-- Registrare anche il diff delle modifiche ai file di testo -->
  <nodiff>/etc/ssl/private</nodiff>
</syscheck>
```

### Regole di Correlazione Custom

OSSEC permette di creare regole che correlano eventi da fonti diverse:

```xml
<!-- /var/ossec/rules/local_rules.xml -->

<!-- Rilevare tentativi di brute force SSH seguiti da login riuscito -->
<group name="attack,correlation">
  <rule id="100100" level="12">
    <if_matched_sid>5720</if_matched_sid>  <!-- SSH brute force -->
    <if_sid>5715</if_sid>                   <!-- SSH login riuscito -->
    <same_source_ip/>
    <timeout>600</timeout>
    <description>Possibile compromissione: brute force SSH seguita da login riuscito dallo stesso IP in 10 minuti</description>
    <group>authentication_success,attack,</group>
  </rule>

  <!-- Rilevare modifica file di sistema dopo login SSH -->
  <rule id="100101" level="14">
    <if_sid>5715</if_sid>                   <!-- SSH login -->
    <if_matched_sid>550</if_matched_sid>    <!-- File integrity change -->
    <same_user/>
    <timeout>300</timeout>
    <description>File di sistema modificato entro 5 minuti dal login SSH — possibile attività malevola</description>
    <group>syscheck,attack,</group>
  </rule>
</group>
```

### Active Response

OSSEC può rispondere automaticamente alle minacce rilevate:

```xml
<!-- Configurazione active response in ossec.conf -->
<active-response>
  <!-- Bloccare IP dopo 6 tentativi di autenticazione falliti -->
  <command>firewall-drop</command>
  <location>local</location>
  <rules_id>5720</rules_id>
  <timeout>3600</timeout>  <!-- Blocco per 1 ora -->
</active-response>

<active-response>
  <!-- Disabilitare un account utente se rilevata escalation di privilegi sospetta -->
  <command>disable-account</command>
  <location>local</location>
  <rules_id>5501</rules_id>
  <timeout>0</timeout>  <!-- Permanente, richiede intervento manuale -->
</active-response>
```

### OSSEC vs AIDE vs Wazuh — Confronto Rapido

| Caratteristica | AIDE | OSSEC | Wazuh |
|---------------|------|-------|-------|
| File integrity | Solo hash periodico | Hash + realtime | Hash + realtime + FIM API |
| Log analysis | No | Sì, con decoder/regole | Sì + ELK integrato |
| Active response | No | Sì | Sì + SOAR integration |
| Rootkit detection | No | Sì | Sì + CVE scanning |
| Dashboard web | No | No (solo CLI) | Sì (Kibana/OpenSearch) |
| Compliance mapping | No | Parziale | CIS, PCI-DSS, GDPR, HIPAA |
| Scalabilità | Singolo host | Manager + agent | Manager cluster + agent |

---

## Confronto MAC — SELinux vs AppArmor vs TOMOYO

### Panoramica dei Modelli MAC su Linux

Il **Mandatory Access Control** (MAC) su Linux è implementato attraverso il framework **LSM** (Linux Security Modules), che fornisce hook nel kernel per intercettare le chiamate di sistema e applicare policy di sicurezza aggiuntive rispetto al DAC tradizionale (chmod/chown). I tre principali moduli MAC sono SELinux, AppArmor e TOMOYO, ciascuno con un approccio architetturale distinto.

### Confronto Architetturale

| Aspetto | SELinux | AppArmor | TOMOYO |
|---------|---------|----------|--------|
| **Modello** | Label-based (Type Enforcement) | Path-based | Path-based |
| **Granularità** | Etichette su ogni oggetto (file, porta, socket, processo) | Profili per binario eseguibile | Profili per dominio con transizione |
| **Sviluppatore** | NSA / Red Hat | Canonical / SUSE | NTT Data (Giappone) |
| **Distribuzioni** | RHEL, Fedora, CentOS, Rocky Linux, AlmaLinux | Ubuntu, Debian, SUSE, openSUSE | Disponibile su tutte (non default) |
| **Complessità** | Alta — richiede comprensione dei type, ruoli, contesti | Media — profili leggibili e intuitivi | Bassa — learning mode con generazione automatica |
| **Policy default** | Targeted (solo servizi principali) o MLS | Profili per applicazioni specifiche | Nessuna policy preconfigurata |
| **Persistenza label** | Etichette memorizzate negli extended attributes (xattr) | No etichette — basato su path assoluto | No etichette — basato su path assoluto |
| **Rename/move** | La policy segue l'oggetto (etichetta persiste) | La policy si rompe se il path cambia | La policy si rompe se il path cambia |
| **Network control** | Sì — labeling di porte, socket, pacchetti | Limitato — solo regole di rete base | Limitato |
| **Learning mode** | Sì (`permissive` + `audit2allow`) | Sì (`complain` mode) | Sì (`learning` mode — punto di forza) |
| **Overhead kernel** | ~2-5% CPU su operazioni di I/O | ~1-3% | ~1-2% |
| **CIS/STIG support** | Pieno supporto nei benchmark | Supportato (Ubuntu CIS) | Non presente nei benchmark |

### TOMOYO — Il Terzo MAC

TOMOYO Linux merita una menzione speciale per il suo approccio unico al MAC:

- **Learning mode nativo**: TOMOYO può osservare il comportamento di un sistema in produzione e generare automaticamente le policy basate sulle operazioni effettivamente eseguite. Questo elimina la fase di scrittura manuale delle policy, che è il principale ostacolo nell'adozione di SELinux.

- **Domain Transition**: ogni processo appartiene a un "dominio" identificato dalla catena di esecuzione (es. `/sbin/init /usr/sbin/sshd /bin/bash`). Questo permette di avere policy diverse per la stessa applicazione a seconda del contesto di invocazione.

- **Policy come file di testo semplice**: le policy TOMOYO sono file di testo leggibili memorizzati in `/etc/tomoyo/`, estremamente facili da ispezionare e modificare rispetto alle policy compilate di SELinux.

```bash
# Abilitare TOMOYO (richiede kernel con supporto LSM TOMOYO)
# Aggiungere al bootloader: security=tomoyo

# Inizializzare la policy
/usr/lib/tomoyo/init_policy

# Attivare il learning mode per un dominio
tomoyo-loadpolicy -ef <<EOF
<kernel> /usr/sbin/sshd
use_profile 1
EOF
# Profile 0 = disabled, 1 = learning, 2 = permissive, 3 = enforcing

# Dopo un periodo di osservazione, convertire a enforcing
tomoyo-loadpolicy -ef <<EOF
<kernel> /usr/sbin/sshd
use_profile 3
EOF

# Ispezionare le policy generate automaticamente
tomoyo-editpolicy
```

### Quando Usare Quale MAC

| Scenario | Raccomandazione | Motivazione |
|----------|----------------|-------------|
| Server enterprise RHEL/CentOS | **SELinux** | Policy mature, supporto STIG/CIS, default |
| Desktop/laptop Ubuntu | **AppArmor** | Già configurato, profili per browser/snap |
| Ambiente di sviluppo/test | **TOMOYO** | Learning mode per generare policy baseline |
| Container host | **SELinux** (RHEL) / **AppArmor** (Ubuntu) | Integrazione con container runtime |
| Requisiti DoD/governativi | **SELinux MLS** | Unico con Multi-Level Security certificato |
| Rapido deployment senza competenze MAC | **AppArmor** | Curva di apprendimento più bassa |

### Coesistenza e Stack LSM

Dal kernel 5.1+, Linux supporta il **stacking LSM**, che permette di attivare più moduli LSM contemporaneamente. Nella pratica:

- I "minor LSM" (Yama, Lockdown, Landlock, BPF-LSM) possono coesistere con un "major LSM"
- Solo **un** major LSM (SELinux, AppArmor, TOMOYO, Smack) può essere attivo come primary
- Il parametro `lsm=` del kernel definisce l'ordine di priorità: `lsm=landlock,lockdown,yama,integrity,selinux,bpf`
- **Landlock** (dal kernel 5.13) è un LSM "unprivileged" che permette a processi non-root di auto-sandboxarsi, complementare al major LSM

---

## Protezione della Memoria — Deep Dive

### Perché la Memoria è un Bersaglio Primario

La maggior parte degli exploit moderni — buffer overflow, return-oriented programming (ROP), use-after-free, heap spray — mira a corrompere o manipolare la memoria di un processo per ottenere l'esecuzione di codice arbitrario. Le difese a livello di memoria sono quindi la prima e più critica linea di protezione contro l'exploitation.

Linux implementa multiple difese stratificate, sia in userspace che nel kernel stesso.

### ASLR — Address Space Layout Randomization

ASLR randomizza la posizione in memoria di stack, heap, librerie condivise e del binario eseguibile stesso ad ogni esecuzione, rendendo impossibile per un attaccante predire indirizzi di memoria fissi.

```bash
# Verificare lo stato di ASLR
cat /proc/sys/kernel/randomize_va_space
# 0 = disabilitato (PERICOLOSO, solo per debug)
# 1 = stack, VDSO, mmap randomizzati
# 2 = FULL — anche heap randomizzato (valore raccomandato)

# Assicurarsi che sia abilitato (CIS Benchmark requirement)
sysctl -w kernel.randomize_va_space=2
echo "kernel.randomize_va_space = 2" >> /etc/sysctl.d/90-memory-protection.conf
```

**ASLR e PIE**: l'ASLR è pienamente efficace solo se i binari sono compilati come **Position-Independent Executables** (PIE). Senza PIE, il segmento `.text` del binario rimane a un indirizzo fisso, fornendo "gadget" utilizzabili per attacchi ROP:

```bash
# Verificare se un binario è compilato con PIE
file /usr/bin/sshd
# Output deve contenere "shared object" (PIE) e NON "executable" (non-PIE)

# Oppure con checksec (da pwntools)
checksec --file=/usr/bin/sshd
# RELRO: Full RELRO, Stack: Canary found, NX: NX enabled, PIE: PIE enabled
```

### KASLR — Kernel ASLR

**KASLR** estende il concetto di ASLR al kernel stesso, randomizzando l'indirizzo base del kernel in memoria ad ogni boot. Questo rende molto più difficili gli attacchi che mirano a sfruttare vulnerabilità del kernel:

```bash
# Verificare che KASLR sia attivo (default nella maggior parte delle distro moderne)
cat /proc/cmdline | grep -o 'nokaslr' || echo "KASLR abilitato"

# KASLR lavora insieme a:
# - kptr_restrict: nasconde gli indirizzi del kernel da /proc/kallsyms
# - dmesg_restrict: limita l'accesso ai messaggi del kernel
sysctl -w kernel.kptr_restrict=2      # Nasconde completamente gli indirizzi kernel
sysctl -w kernel.dmesg_restrict=1     # Solo root può leggere dmesg
```

### NX Bit (No-eXecute) / XD (eXecute Disable)

Il bit NX (Intel lo chiama XD) è una protezione **hardware** implementata a livello di CPU e tabelle delle pagine. Marca le pagine di memoria contenenti dati (stack, heap) come **non eseguibili**, impedendo l'esecuzione di shellcode iniettato:

```bash
# Verificare il supporto NX nella CPU
grep -o 'nx' /proc/cpuinfo | head -1
# Se presente, il processore supporta NX

# NX è gestito automaticamente dal kernel e dal compilatore
# Per verificare che un binario rispetti NX:
readelf -l /usr/bin/sshd | grep GNU_STACK
# Output: GNU_STACK  0x... RW  0x10
# "RW" (no E) = stack non eseguibile (corretto)
# "RWE" = stack eseguibile (VULNERABILE)
```

### Stack Canaries (Stack Protector)

Le **stack canaries** sono valori sentinella posizionati dal compilatore tra le variabili locali e l'indirizzo di ritorno sullo stack. Se un buffer overflow corrompe lo stack, il valore canary viene sovrascritto; al ritorno dalla funzione, il runtime rileva la corruzione e termina il processo con `__stack_chk_fail`:

```bash
# I binari moderni sono compilati con -fstack-protector-strong
# Verificare la protezione di un binario
readelf -s /usr/bin/sshd | grep stack_chk
# Se presente __stack_chk_fail, lo stack protector è attivo

# Livelli di protezione GCC:
# -fstack-protector          → protegge solo funzioni con buffer char > 8 byte
# -fstack-protector-strong   → protegge funzioni con array locali, address-taken vars
# -fstack-protector-all      → protegge TUTTE le funzioni (overhead maggiore)

# Verificare i flag di compilazione dei pacchetti di sistema
# Su Debian/Ubuntu:
dpkg-buildflags --get CFLAGS
# Deve includere -fstack-protector-strong
```

### SMEP e SMAP — Protezioni Kernel dalla CPU

**SMEP** (Supervisor Mode Execution Prevention) e **SMAP** (Supervisor Mode Access Prevention) sono protezioni hardware che impediscono al kernel di eseguire o accedere a pagine di memoria userspace:

| Protezione | Funzione | Attacchi Mitigati |
|-----------|----------|-------------------|
| **SMEP** | Il kernel non può eseguire codice in pagine userspace | ret2usr: l'exploit sovrascrive un puntatore funzione kernel per saltare a shellcode in userspace |
| **SMAP** | Il kernel non può leggere/scrivere pagine userspace senza `stac`/`clac` | Data-only attacks che manipolano strutture kernel tramite dati userspace |

```bash
# Verificare supporto CPU
grep -E 'smep|smap' /proc/cpuinfo | head -2

# SMEP/SMAP sono abilitati automaticamente dal kernel se la CPU li supporta
# Per verificare che non siano stati disabilitati:
cat /proc/cmdline | grep -oE 'nosm[ae]p' || echo "SMEP/SMAP attivi"
```

### RELRO — Relocation Read-Only

**RELRO** (RELocation Read-Only) è una protezione del linker che rende le sezioni GOT (Global Offset Table) e PLT (Procedure Linkage Table) in sola lettura dopo il caricamento, impedendo attacchi che sovrascrivono puntatori a funzioni in queste tabelle:

```bash
# Verificare RELRO di un binario
readelf -l /usr/bin/sshd | grep GNU_RELRO
# Presenza di GNU_RELRO indica almeno Partial RELRO

readelf -d /usr/bin/sshd | grep BIND_NOW
# Se presente BIND_NOW → Full RELRO (tutte le risoluzioni al caricamento)
# Se assente → Partial RELRO (GOT ancora scrivibile per lazy binding)

# Full RELRO è raccomandato per tutti i binari di sicurezza critica
# Flag di compilazione: -Wl,-z,relro,-z,now
```

### Riepilogo Difese e Verifica Rapida

```bash
#!/bin/bash
# Script di verifica rapida delle protezioni memoria
echo "=== Protezioni Memoria del Sistema ==="

echo -n "ASLR: "
ASLR=$(cat /proc/sys/kernel/randomize_va_space)
[ "$ASLR" -eq 2 ] && echo "FULL (OK)" || echo "INSUFFICIENTE ($ASLR) - impostare a 2"

echo -n "KASLR: "
grep -q 'nokaslr' /proc/cmdline && echo "DISABILITATO (CRITICO)" || echo "ATTIVO (OK)"

echo -n "NX bit: "
grep -q 'nx' /proc/cpuinfo && echo "SUPPORTATO (OK)" || echo "NON SUPPORTATO (ATTENZIONE)"

echo -n "SMEP: "
grep -q 'smep' /proc/cpuinfo && echo "SUPPORTATO (OK)" || echo "NON PRESENTE"

echo -n "SMAP: "
grep -q 'smap' /proc/cpuinfo && echo "SUPPORTATO (OK)" || echo "NON PRESENTE"

echo -n "kptr_restrict: "
KPTR=$(cat /proc/sys/kernel/kptr_restrict)
[ "$KPTR" -ge 1 ] && echo "$KPTR (OK)" || echo "0 (impostare >= 1)"

echo -n "dmesg_restrict: "
DMESG=$(cat /proc/sys/kernel/dmesg_restrict)
[ "$DMESG" -eq 1 ] && echo "ATTIVO (OK)" || echo "DISABILITATO (impostare a 1)"

echo ""
echo "=== Verifica Binari Critici ==="
for BIN in /usr/bin/sshd /usr/sbin/sshd /usr/bin/sudo /usr/bin/passwd; do
  [ -f "$BIN" ] || continue
  echo "--- $BIN ---"
  file "$BIN" | grep -q "shared object" && echo "  PIE: SI" || echo "  PIE: NO (ATTENZIONE)"
  readelf -s "$BIN" 2>/dev/null | grep -q stack_chk && echo "  Stack Canary: SI" || echo "  Stack Canary: NO"
  readelf -l "$BIN" 2>/dev/null | grep -q GNU_RELRO && echo "  RELRO: SI" || echo "  RELRO: NO"
  readelf -l "$BIN" 2>/dev/null | grep GNU_STACK | grep -q " E " && echo "  NX Stack: NO (VULNERABILE)" || echo "  NX Stack: SI"
done
```

### sysctl di Protezione Memoria — Riepilogo Completo

```bash
# /etc/sysctl.d/90-memory-protection.conf

# ASLR completo (stack, heap, mmap, VDSO)
kernel.randomize_va_space = 2

# Nascondere indirizzi kernel (anti-info-leak)
kernel.kptr_restrict = 2

# Limitare accesso dmesg (anti-info-leak)
kernel.dmesg_restrict = 1

# Bloccare caricamento moduli kernel (dopo il boot)
# ATTENZIONE: da usare solo dopo aver caricato tutti i moduli necessari
# kernel.modules_disabled = 1

# Limitare ptrace (Yama LSM)
# 0 = nessuna restrizione, 1 = solo parent, 2 = solo admin, 3 = nessuno
kernel.yama.ptrace_scope = 2

# Disabilitare SysRq (evitare bypass dal keyboard)
kernel.sysrq = 0

# Limitare accesso a perf_event (anti-side-channel)
kernel.perf_event_paranoid = 3

# Disabilitare eBPF per utenti non privilegiati (anti-exploitation)
kernel.unprivileged_bpf_disabled = 1

# Disabilitare user namespaces non privilegiati (riduce superficie di attacco kernel)
# NOTA: può rompere browser sandboxing (Chrome) e container rootless
# user.max_user_namespaces = 0
```

---

## Best Practices

### Hardening Generale

1. **Principio del minimo privilegio**: ogni utente, servizio e processo deve avere solo i permessi strettamente necessari
2. **Defense in depth**: non affidarsi a un singolo controllo — combinare firewall + MAC + audit + encryption + IDS
3. **Patch management**: aggiornare regolarmente, soprattutto le patch di sicurezza
4. **Baseline di sicurezza**: applicare CIS Benchmarks come punto di partenza, personalizzare per il proprio ambiente
5. **Automatizzare l'hardening**: usare Ansible, Puppet o Chef per applicare e mantenere la configurazione di sicurezza

### MAC (SELinux/AppArmor)

1. **Mai disabilitare SELinux/AppArmor in produzione** — imparare a usarli, non disattivarli
2. **Usare permissive per il debugging**, enforcing in produzione
3. **Non usare `setenforce 0` come soluzione** — trovare la causa reale e correggere
4. **Documentare le policy personalizzate**: perché sono state create e cosa permettono

### Firewall

1. **Default deny**: tutto bloccato, aprire solo ciò che serve
2. **Least privilege sulle porte**: solo le porte necessarie, solo dalle reti necessarie
3. **Rate limiting**: proteggere da brute force e DDoS
4. **Logging**: registrare i pacchetti droppati per analisi

### Audit

1. **Monitorare tutto ciò che è critico**: file di configurazione, account, accessi privilegiati
2. **Proteggere i log**: centralizzare su un log server separato, rendere i log immutabili
3. **Alert in tempo reale**: non basta loggare, bisogna essere avvisati tempestivamente
4. **Review periodica**: analizzare i log regolarmente, non solo dopo un incidente

### Crittografia

1. **LUKS per tutti i dati sensibili**: disco di sistema e dati
2. **Backup dell'header LUKS**: senza l'header, i dati sono irrecuperabili
3. **Keyfile protetti**: permessi 400, attributo immutabile, su filesystem crittografato a sua volta
4. **Rotazione delle chiavi**: cambiare periodicamente le passphrase

---

## Troubleshooting

### SELinux — Problemi Comuni

```bash
# Problema: servizio non si avvia, AVC denied nel log
# 1. Verificare i denial
sudo ausearch -m AVC -ts recent

# 2. Usare sealert per spiegazione leggibile
sudo sealert -a /var/log/audit/audit.log

# 3. Verificare se è un problema di contesto
ls -Z /percorso/del/file
# Se il tipo è sbagliato:
sudo restorecon -Rv /percorso/del/file

# 4. Se serve un boolean
sudo getsebool -a | grep <servizio>
sudo setsebool -P <boolean> on

# 5. Se serve una porta personalizzata
sudo semanage port -a -t <type> -p tcp <porta>

# 6. Come ultima risorsa, creare un modulo personalizzato
sudo ausearch -m AVC -ts recent | audit2allow -M myfix
sudo semodule -i myfix.pp
```

### nftables — Problemi Comuni

```bash
# Problema: traffico legittimo bloccato
# 1. Verificare le regole attive
sudo nft list ruleset

# 2. Aggiungere logging temporaneo
sudo nft insert rule inet filter input log prefix \"debug: \" counter

# 3. Verificare i contatori
sudo nft list chain inet filter input -a
# I contatori mostrano quanti pacchetti hanno matchato ogni regola

# 4. Testare una regola specifica
sudo nft add rule inet filter input tcp dport 8080 counter accept
```

### Fail2Ban — Problemi Comuni

```bash
# Problema: IP legittimo bannato
# 1. Sbannare
sudo fail2ban-client set <jail> unbanip <IP>

# 2. Aggiungere a ignoreip
# In /etc/fail2ban/jail.local:
# ignoreip = 127.0.0.1/8 <IP_legittimo>

# Problema: fail2ban non banna
# 1. Testare il filtro
sudo fail2ban-regex /var/log/auth.log /etc/fail2ban/filter.d/sshd.conf --print-all-matched

# 2. Verificare il backend
sudo fail2ban-client get sshd logpath
sudo fail2ban-client get sshd journalmatch
```

### LUKS — Problemi Comuni

```bash
# Problema: dimenticata la passphrase
# Se si ha il backup dell'header E un keyfile:
sudo cryptsetup luksOpen --key-file /root/luks-keyfile /dev/sdb1 rescue

# Se non si ha nessuna chiave funzionante:
# I DATI SONO PERSI. Questa è una feature, non un bug.
# Per questo il backup dell'header è CRITICO.

# Problema: header corrotto
sudo cryptsetup luksHeaderRestore /dev/sdb1 --header-backup-file /root/luks-header-backup.img

# Problema: performance lente con LUKS
# Verificare il supporto AES-NI
grep -m1 aes /proc/cpuinfo
# Se presente, verificare il benchmark:
sudo cryptsetup benchmark
# Se le performance LUKS sono molto inferiori:
# Verificare che il modulo aesni_intel sia caricato
sudo modprobe aesni_intel
```

### Servizio Rotto dopo Hardening systemd

```bash
# Diagnosi: controllare journal per la restrizione che blocca
sudo journalctl -u myservice --since "10 min ago" -p err
# Cercare: "Permission denied", "Read-only file system", "Bad system call"

# Se syscall filtrata (SECCOMP killed):
sudo journalctl -u myservice | grep "syscall"
ausyscall 314   # Identificare la syscall → aggiungere a SystemCallFilter=

# Se ProtectSystem=strict blocca scritture → ReadWritePaths=/var/lib/myservice
# Verificare punteggio: systemd-analyze security myservice
```

### Utente Bloccato da PAM (pam_faillock)

```bash
sudo faillock --user username          # Verificare stato blocco
sudo faillock --user username --reset  # Sbloccare

# Se NESSUNO può autenticarsi: bootare single user / live USB,
# rimuovere pam_faillock da /etc/pam.d/common-auth (Debian)
# o /etc/pam.d/system-auth (RHEL)

# CRITICO: tenere sempre una sessione root aperta prima di
# modificare /etc/pam.d/ — testare da un'ALTRA sessione
```

### Audit Log Overflow (auditd)

```bash
du -sh /var/log/audit/   # Verificare dimensione

# Configurare rotazione in /etc/audit/auditd.conf:
max_log_file = 50
num_logs = 10
max_log_file_action = ROTATE
space_left = 150
space_left_action = SYSLOG
admin_space_left_action = SUSPEND   # NON usare HALT!

# Disco pieno: fermare auditd, eliminare log vecchi, riavviare
sudo systemctl stop auditd
sudo find /var/log/audit/ -name "audit.log.*" -mtime +30 -delete
sudo systemctl start auditd
# Ridurre regole troppo broad (es. -S open senza -F genera log enormi)
```

### SELinux Denial dopo Cambio Opzioni di Mount

```bash
# AVC denial dopo remount — contesti persi
sudo ausearch -m AVC -ts recent | head -30
sudo restorecon -Rv /tmp     # Ripristinare contesti

# Se filesystem ricreato (mkfs) → relabel completo:
sudo touch /.autorelabel && sudo reboot

# Verificare contesto: ls -Zd /tmp → deve essere tmp_t
# Correggere: semanage fcontext -a -t tmp_t "/tmp(/.*)?"
```

### GRUB2 Password — Lockout

```bash
# Con --unrestricted: boot normale funziona, solo modifica voci richiede password
# Se boot completamente bloccato: avviare da live USB
sudo mount /dev/sda1 /mnt
sudo rm /mnt/etc/grub.d/01_password   # oppure /mnt/boot/grub2/user.cfg
sudo chroot /mnt grub2-mkconfig -o /boot/grub2/grub.cfg
# Prevenzione: password GRUB in password manager o caveau fisico
```

### Chiave SSH Rifiutata dopo Hardening

```bash
ssh -vvv -p 2222 user@server   # Debug dal client

# Cause comuni:
# a. AllowUsers/AllowGroups non include l'utente
sudo grep -E "^Allow" /etc/ssh/sshd_config /etc/ssh/sshd_config.d/*
# b. HostKeyAlgorithms troppo restrittivo (client RSA, server solo ed25519)
# c. Permessi sbagliati: .ssh/ 700, authorized_keys 600, home non group-writable
# d. SELinux: ls -Z ~/.ssh/authorized_keys → deve essere ssh_home_t
sudo restorecon -Rv ~/.ssh/

# Log server:
sudo journalctl -u sshd --since "5 min ago" | grep -i "auth\|key\|refused"
```

### AIDE — Falsi Positivi dopo Aggiornamento Pacchetti

```bash
sudo aide --check 2>&1 | grep "Changed entries"
# Confrontare con log aggiornamento:
grep "upgrade" /var/log/dpkg.log | tail -50  # Debian
sudo dnf history info last                     # RHEL

# Se tutte le modifiche corrispondono → aggiornare DB AIDE:
sudo aide --update
sudo mv /var/lib/aide/aide.db.new.gz /var/lib/aide/aide.db.gz

# Prevenzione: post-hook in /etc/apt/apt.conf.d/99aide-update:
# DPkg::Post-Invoke {"aide --update && mv ... || true";};
```

### Docker Rotto da User Namespace Remapping

```bash
# Con userns-remap=default: UID 0 nel container = UID 100000 sull'host
# Volumi esistenti hanno permessi root (UID 0) → fix:
sudo chown -R 100000:100000 /data/myapp-volume/

# Container che DEVE girare come root reale:
docker run --userns=host mycontainer

# Rollback: rimuovere "userns-remap" da daemon.json,
# dati in /var/lib/docker/100000.100000/ — copiarli prima
```

### Lynis — Hardening Index Basso nonostante l'Hardening

```bash
sudo lynis audit system 2>&1 | grep -E "^\[" | sort | uniq -c | sort -rn

# Cause comuni punteggio basso:
# a. Security updates non installati
# b. NTP non configurato → timedatectl set-ntp true
# c. Banner legale SSH mancante → Banner /etc/ssh/banner.txt
# d. Swap non crittografato → dm-crypt random key
# e. Tool mancanti: clamav, aide, fail2ban, rkhunter
```

### Kernel Lockdown Blocca Operazioni Legittime

```bash
cat /sys/kernel/security/lockdown   # [none] integrity confidentiality

# Modulo non firmato: firmare con MOK key (soluzione corretta)
# Debug: disabilitare Secure Boot nel BIOS temporaneamente
# perf/bpftrace bloccati con confidentiality → usare integrity

dmesg | grep -i lockdown   # Verificare operazioni bloccate
```

### OpenSCAP — Profilo Non Trovato o Contenuto Mancante

```bash
oscap info /usr/share/xml/scap/ssg/content/ssg-*.xml 2>/dev/null

# Installare contenuto SCAP:
sudo apt install -y ssg-debian             # Debian
sudo dnf install -y scap-security-guide    # RHEL

# Versione incompatibile: verificare che il contenuto corrisponda all'OS
# Sistemi non supportati: https://github.com/ComplianceAsCode/content/releases
```

### Connessione di Rete Rotta dopo Hardening sysctl

```bash
sysctl net.ipv4.ip_forward           # Se router/gateway, deve essere 1
sysctl net.ipv4.tcp_keepalive_time   # Troppo basso = connessioni chiuse

# DNS rotto dopo disabilitare IPv6: resolver preferisce IPv6 → forzare IPv4
# Multi-homed: rp_filter=2 (loose) invece di 1 (strict)
# Rollback: sysctl -p /etc/sysctl.d/99-default.conf
```

### Cron Job Fallisce dopo requiretty in sudoers

```bash
sudo grep requiretty /etc/sudoers /etc/sudoers.d/*
# requiretty blocca sudo da cron/CI/CD — eccezione:
# In /etc/sudoers.d/cron-exception:
Defaults:cronuser !requiretty
# Alternativa: systemd timers (eseguono come utente specifico senza sudo)
```

---

## Esercizi Pratici

### Esercizio 1 — Hardening Completo di un Server Minimal

Obiettivo: applicare CIS Benchmark Level 1 a un server RHEL/Debian appena installato.

```
Requisiti:
- VM con installazione minimal (senza GUI)
- Accesso root

Procedura:
1. Eseguire Lynis e annotare l'hardening index iniziale
2. Applicare le seguenti categorie di hardening:
   a. Filesystem: mount options per /tmp, /var, /dev/shm
   b. Kernel: sysctl hardening completo (ASLR, ptrace, dmesg_restrict)
   c. Servizi: disabilitare tutti i servizi non necessari
   d. Password: configurare PAM pam_pwquality e pam_faillock
   e. SSH: configurazione sicura con soli algoritmi forti
   f. Firewall: nftables con policy deny di default
   g. Audit: auditd con regole per file critici e syscall
   h. FIM: AIDE inizializzato e cron configurato
3. Rieseguire Lynis e confrontare il punteggio
4. Documentare ogni modifica e il motivo

Criterio di successo: hardening index >= 80
```

### Esercizio 2 — Sandboxing di un Servizio con systemd

Obiettivo: applicare il massimo sandboxing possibile a un servizio web senza comprometterne la funzionalità.

```
Requisiti:
- Un servizio web funzionante (nginx, Apache, o app custom)
- systemd come init system

Procedura:
1. Verificare il punteggio di sicurezza iniziale:
   systemd-analyze security myservice
2. Creare un override con tutte le direttive di sandboxing
3. Aggiungere ReadWritePaths= per i percorsi necessari
4. Testare il servizio dopo ogni direttiva aggiunta
5. Risolvere eventuali errori (SystemCallFilter, ProtectSystem)
6. Verificare il punteggio finale (target: < 3.0)

Criterio di successo: servizio funzionante con punteggio < 3.0
```

### Esercizio 3 — Incident Response Drill

Obiettivo: simulare un incidente e praticare la raccolta di dati volatili.

```
Requisiti:
- Server hardened con auditd e AIDE configurati
- Un "attaccante simulato" (collega o script) che:
  a. Crea un utente non autorizzato
  b. Modifica un file di configurazione
  c. Installa un servizio non autorizzato

Procedura:
1. Dopo la "compromissione", raccogliere i dati volatili (RFC 3227)
2. Analizzare i log di auditd per trovare le modifiche
3. Eseguire AIDE --check per identificare i file modificati
4. Ricostruire la timeline dell'incidente
5. Scrivere un report con: cosa è successo, quando, come è stato rilevato

Criterio di successo: tutte le azioni dell'attaccante identificate
```

### Esercizio 4 — Compliance Pipeline con OpenSCAP

Obiettivo: creare una pipeline di compliance automatizzata.

```
Requisiti:
- OpenSCAP installato con scap-security-guide
- Accesso a un sistema target

Procedura:
1. Eseguire una scansione CIS Level 1 baseline
2. Generare il remediation script (Bash o Ansible)
3. Revisionare lo script e rimuovere i fix non applicabili
4. Applicare le remediation
5. Rieseguire la scansione e confrontare i risultati
6. Configurare un cron job per la scansione settimanale

Criterio di successo: compliance >= 90% con report HTML leggibile
```

---

## Auto-valutazione

### Domanda 1
Quale è la differenza principale tra CIS Benchmark Level 1 e Level 2?

<details>
<summary>Risposta</summary>

Level 1: baseline prudente, nessun impatto operativo significativo (firewall, password policy, servizi inutili disabilitati). Level 2: hardening aggressivo per ambienti ad alta sicurezza — auditd immutabile (-e 2), SELinux enforcing, kernel.modules_disabled=1, ptrace_scope=3. Level 2 include tutto Level 1 più controlli aggiuntivi che possono impattare la funzionalità.
</details>

### Domanda 2
Cosa impedisce il kernel lockdown mode in modalità "integrity"?

<details>
<summary>Risposta</summary>

Modalità "integrity": blocca modifica del kernel in esecuzione — moduli non firmati, /dev/mem, /dev/kmem, MSR, kexec non firmati, hibernazione, bpf non privilegiato. Modalità "confidentiality": aggiunge blocco lettura dati sensibili del kernel (contatori hardware via perf).
</details>

### Domanda 3
Perché hidepid=2 su /proc è una misura di sicurezza importante, e quale problema può causare?

<details>
<summary>Risposta</summary>

hidepid=2 nasconde i processi altrui in /proc — impedisce enumerazione, lettura argomenti CLI (password/token), e info-gathering per privilege escalation. Problema: servizi di monitoraggio (node_exporter, Nagios, Zabbix) e systemd-logind smettono di funzionare. Soluzione: parametro gid= per concedere accesso completo a un gruppo specifico (es. proc-readers).
</details>

### Domanda 4
Qual è l'ordine corretto di raccolta dei dati volatili secondo RFC 3227?

<details>
<summary>Risposta</summary>

Dal più al meno volatile: 1) registri CPU/cache, 2) routing/ARP/connessioni, 3) processi, 4) RAM (LiME/AVML), 5) file temporanei, 6) disco, 7) log remoti, 8) config rete fisica, 9) backup. Regola fondamentale: NON spegnere prima di raccogliere i punti 2-5.
</details>

### Domanda 5
Cosa fa la direttiva systemd NoNewPrivileges=yes e perché è a basso rischio di rottura?

<details>
<summary>Risposta</summary>

Imposta prctl(PR_SET_NO_NEW_PRIVS): impedisce acquisizione privilegi tramite SUID/SGID, transizioni SELinux, e file capabilities. Basso rischio perché i servizi normali non eseguono binari SUID dopo l'avvio. Eccezione: servizi con su/sudo interni.
</details>

### Domanda 6
Come funziona il measured boot con TPM 2.0 e Clevis per lo sblocco automatico di LUKS?

<details>
<summary>Risposta</summary>

TPM 2.0 registra hash di ogni componente di boot nei PCR (Platform Configuration Registers). Clevis sigilla la chiave LUKS nel TPM usando i PCR come policy: la chiave è rilasciata SOLO se i PCR corrispondono al binding originale. Modifica di kernel/bootloader/Secure Boot cambia i PCR e richiede password manuale. Esempio: `clevis luks bind -d /dev/sda3 tpm2 '{"pcr_ids":"0,1,4,7,9"}'`. Aggiornamento kernel richiede re-binding.
</details>

### Domanda 7
Qual è la differenza tra ProtectSystem=strict e ProtectSystem=full in systemd?

<details>
<summary>Risposta</summary>

`full`: monta /usr, /boot, /efi read-only — il servizio scrive ancora in /etc, /var. `strict`: monta TUTTO / read-only — serve ReadWritePaths= per ogni percorso di scrittura. Approccio raccomandato: partire con full, testare, passare a strict aggiungendo ReadWritePaths= per ogni errore "Read-only file system".
</details>

### Domanda 8
Perché è pericoloso eseguire container Docker con il flag --privileged?

<details>
<summary>Risposta</summary>

`--privileged` disabilita TUTTE le protezioni: seccomp, AppArmor/SELinux, concede tutte le capabilities, accesso a tutti i device host. Container privilegiato = root sull'host. Alternative: `--cap-add` per capabilities specifiche, `--device` per device specifici.
</details>

---

## Letture Primarie

| Risorsa | Tipo | Rilevanza |
|---------|------|-----------|
| CIS Benchmarks (Debian, RHEL) v3.0.0+ | Standard | Checklist operative per hardening L1/L2 |
| NIST SP 800-123 "Guide to General Server Security" | Guida | Principi architetturali per server sicuri |
| NIST SP 800-53 Rev. 5 "Security and Privacy Controls" | Framework | Catalogo completo dei controlli di sicurezza |
| DISA STIG per RHEL 9 / Ubuntu 22.04 | Standard | Finding con severità e fix per ambienti DoD |
| kernel.org — Documentation/admin-guide/sysctl/ | Docs | Documentazione ufficiale parametri kernel |
| kernel.org — Documentation/admin-guide/LSM/ | Docs | Linux Security Modules (Yama, lockdown) |
| RFC 3227 — Evidence Collection and Archiving | RFC | Ordine di raccolta dati volatili, chain of custody |
| OWASP Server Security Verification Standard | Guida | Checklist di sicurezza per server applicativi |
| systemd.exec(5) man page | Man page | Direttive di sandboxing systemd complete |
| ComplianceAsCode/content (GitHub) | Progetto | Contenuti SCAP open-source per compliance |

> Tutte le risorse consultate il 2026-05-23.

---

## Collegamenti Incrociati

- **Modulo 12 — Gestione utenti e permessi**: base per comprendere DAC, SUID/SGID, PAM
- **Modulo 18 — Systemd in profondità**: prerequisito per service hardening e socket activation
- **Modulo 22 — Networking avanzato**: complemento per la sezione network hardening, nftables
- **Modulo 28 — Logging e monitoring**: approfondimento su journald, rsyslog, centralizzazione log
- **Modulo 31 — Crittografia e PKI**: complemento per LUKS, SSH certificates, Secure Boot signing
- **Modulo 33 — SELinux e AppArmor**: approfondimento MAC, policy custom, troubleshooting
- **15-SECURITY — Sicurezza offensiva**: prospettiva dell'attaccante sulle stesse superfici difese qui

---

## Glossario Locale

| Termine | Definizione |
|---------|-------------|
| ASLR | Address Space Layout Randomization — randomizza gli indirizzi di memoria dei processi per rendere più difficili gli exploit |
| CIS | Center for Internet Security — organizzazione che pubblica benchmark di hardening |
| DAC | Discretionary Access Control — controllo degli accessi basato sul proprietario (chmod/chown) |
| DISA STIG | Defense Information Systems Agency Security Technical Implementation Guide |
| FIM | File Integrity Monitoring — monitoraggio delle modifiche ai file critici (AIDE, Tripwire, osquery) |
| hidepid | Opzione di mount per /proc che nasconde i processi degli altri utenti |
| kexec | Meccanismo per caricare un nuovo kernel senza reboot hardware |
| Lockdown mode | Modalità del kernel che limita le operazioni di root per proteggere l'integrità del kernel |
| LSM | Linux Security Module — framework kernel per moduli di sicurezza (SELinux, AppArmor, Yama) |
| MAC | Mandatory Access Control — controllo degli accessi basato su policy centrali (SELinux, AppArmor) |
| MOK | Machine Owner Key — chiave per firmare kernel/moduli custom con Secure Boot |
| OVAL | Open Vulnerability and Assessment Language — formato per descrivere vulnerabilità |
| PCR | Platform Configuration Register — registri nel TPM che memorizzano hash della catena di boot |
| SCAP | Security Content Automation Protocol — protocollo per compliance automatizzata |
| TPM | Trusted Platform Module — chip crittografico hardware per measured boot e key storage |
| XCCDF | Extensible Configuration Checklist Description Format — formato per checklist di sicurezza |
| KASLR | Kernel ASLR — randomizzazione dell'indirizzo base del kernel in memoria ad ogni boot |
| NX bit | No-eXecute bit — protezione hardware CPU che impedisce l'esecuzione di codice nelle pagine dati (stack, heap) |
| OSSEC | Open Source Security Event Correlator — HIDS con FIM, log analysis e active response |
| RELRO | RELocation Read-Only — protezione linker che rende GOT/PLT in sola lettura dopo il caricamento |
| SMEP | Supervisor Mode Execution Prevention — protezione CPU che impedisce al kernel di eseguire codice userspace |
| SMAP | Supervisor Mode Access Prevention — protezione CPU che impedisce al kernel di accedere a dati userspace |
| Stack canary | Valore sentinella sullo stack per rilevare buffer overflow prima del ritorno dalla funzione |
| TOMOYO | Linux Security Module MAC path-based con learning mode nativo per generazione automatica policy |
| USBGuard | Framework di autorizzazione USB a livello kernel per whitelist/blacklist dispositivi |
| Yama | Linux Security Module che limita ptrace e altre operazioni di debug |

---

## Riferimenti

- **CIS Benchmarks**: [https://www.cisecurity.org/cis-benchmarks](https://www.cisecurity.org/cis-benchmarks)
- **Lynis**: [https://cisofy.com/lynis/](https://cisofy.com/lynis/)
- **SELinux Project**: [https://selinuxproject.org/](https://selinuxproject.org/)
- **Red Hat SELinux Guide**: [https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html/using_selinux/](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/9/html/using_selinux/)
- **AppArmor Wiki**: [https://gitlab.com/apparmor/apparmor/-/wikis/](https://gitlab.com/apparmor/apparmor/-/wikis/)
- **nftables Wiki**: [https://wiki.nftables.org/](https://wiki.nftables.org/)
- **Fail2Ban**: [https://www.fail2ban.org/](https://www.fail2ban.org/)
- **AIDE**: [https://aide.github.io/](https://aide.github.io/)
- **auditd**: `man auditd`, `man auditctl`, `man aureport`
- **cryptsetup/LUKS**: [https://gitlab.com/cryptsetup/cryptsetup](https://gitlab.com/cryptsetup/cryptsetup)
- **OpenSSH**: [https://www.openssh.com/](https://www.openssh.com/)
- **OWASP**: [https://owasp.org/](https://owasp.org/)
- **NIST SP 800-123**: Guide to General Server Security — [https://csrc.nist.gov/pubs/sp/800/123/final](https://csrc.nist.gov/pubs/sp/800/123/final)
- **NIST SP 800-53 Rev. 5**: Security and Privacy Controls — [https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final)
- **DISA STIG**: [https://public.cyber.mil/stigs/downloads/](https://public.cyber.mil/stigs/downloads/)
- **OpenSCAP**: [https://www.open-scap.org/](https://www.open-scap.org/)
- **ComplianceAsCode/content**: [https://github.com/ComplianceAsCode/content](https://github.com/ComplianceAsCode/content)
- **ansible-lockdown**: [https://github.com/ansible-lockdown](https://github.com/ansible-lockdown)
- **osquery**: [https://osquery.io/](https://osquery.io/)
- **Kernel documentation — sysctl**: [https://www.kernel.org/doc/Documentation/admin-guide/sysctl/](https://www.kernel.org/doc/Documentation/admin-guide/sysctl/)
- **Kernel documentation — Lockdown**: [https://www.kernel.org/doc/Documentation/admin-guide/kernel-parameters.txt](https://www.kernel.org/doc/Documentation/admin-guide/kernel-parameters.txt)
- **Clevis (TPM/NBDE)**: [https://github.com/latchset/clevis](https://github.com/latchset/clevis)
- **USBGuard**: [https://usbguard.github.io/](https://usbguard.github.io/)
- **OSSEC**: [https://www.ossec.net/](https://www.ossec.net/)
- **Wazuh (fork OSSEC)**: [https://wazuh.com/](https://wazuh.com/)
- **TOMOYO Linux**: [https://tomoyo.osdn.jp/](https://tomoyo.osdn.jp/)
- **RFC 3227**: Guidelines for Evidence Collection and Archiving — [https://datatracker.ietf.org/doc/html/rfc3227](https://datatracker.ietf.org/doc/html/rfc3227)
- **Docker Security**: [https://docs.docker.com/engine/security/](https://docs.docker.com/engine/security/)
- **CIS Docker Benchmark**: [https://www.cisecurity.org/benchmark/docker](https://www.cisecurity.org/benchmark/docker)
