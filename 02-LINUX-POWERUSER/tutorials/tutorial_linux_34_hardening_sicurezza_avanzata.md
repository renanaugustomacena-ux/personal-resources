# Tutorial Linux 34 — Hardening e Sicurezza Avanzata

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** CIS Benchmark, lynis audit, USBGuard, AIDE, seccomp, capabilities reduction, kernel hardening
> **Prerequisiti:** `tutorial_linux_11_sicurezza.md`, `tutorial_linux_07_kernel.md`
> **Durata stimata:** 14-18 ore

---

## Mappa concettuale

```
Hardening Linux
│
├── Benchmark e audit
│   ├── CIS Benchmark (Center for Internet Security)
│   ├── lynis (audit automatico)
│   └── OpenSCAP (conformità standard)
│
├── Controllo fisico
│   ├── USBGuard (blocca dispositivi USB non autorizzati)
│   └── GRUB password
│
├── Integrità filesystem
│   └── AIDE (Advanced Intrusion Detection Environment)
│
├── Riduzione surface attack
│   ├── Capabilities Linux (cap_net_bind, cap_sys_admin, ...)
│   ├── seccomp (filtra syscall)
│   └── Namespace isolation
│
└── Kernel hardening
    ├── sysctl security params
    ├── GRUB lockdown
    └── kptr_restrict, dmesg_restrict
```

---

# Parte A — CIS Benchmark e Lynis

---

## A1. Lynis audit

```bash
# Lynis: tool di audit sicurezza open source
apt install lynis

# Audit completo sistema
lynis audit system

# Output include:
# [+] Boot and services
# [+] Kernel
# [+] Memory and Processes
# [+] Authentication
# [+] Shells
# [+] File systems
# [+] Hardening index: 65 [############        ] (max 100)
# Suggestions: ...

# Audit specifico
lynis audit system --test-from-group authentication
lynis audit system --tests-from-category "kernel"

# Genera report
lynis audit system --report-file /var/log/lynis-report.dat
lynis show details TEST-ID   # dettagli su un test specifico

# Leggi hardening suggestions
grep "Suggestion" /var/log/lynis.log | head -30
```

> **Analogia:** Lynis è come un ispettore di sicurezza che esamina sistematicamente ogni angolo del tuo sistema: porte, serrature, finestre, cassaforti. Alla fine produce un "indice di hardening" (0-100) e una lista di raccomandazioni prioritizzate — non ti dice solo che c'è un problema, ti dice anche come risolverlo.

---

## A2. CIS Benchmark manuale

```bash
# CIS Level 1 — raccomandazioni essenziali

# 1. Filesystem
# Disabilita filesystem non necessari
cat > /etc/modprobe.d/cis-filesystems.conf << 'EOF'
install cramfs /bin/false
install freevxfs /bin/false
install jffs2 /bin/false
install hfs /bin/false
install hfsplus /bin/false
install udf /bin/false
install vfat /bin/false   # solo se non usi FAT/USB boot
EOF

# 2. Partizioni con opzioni sicure (in /etc/fstab)
# /tmp: noexec, nosuid, nodev
# /var: nosuid
# /home: nodev
# /dev/shm: noexec, nosuid, nodev

# Esempio /tmp su tmpfs con opzioni sicure:
echo "tmpfs /tmp tmpfs defaults,noexec,nosuid,nodev,size=2G 0 0" >> /etc/fstab
mount -o remount /tmp

# 3. Software
# Rimuovi software non necessario
apt purge telnet rsh-client rsh-server nis talk talkd inetd xinetd

# Installa sicurezza essenziale
apt install libpam-pwquality auditd aide usbguard

# 4. Servizi di rete — disabilita non usati
systemctl disable avahi-daemon
systemctl disable cups
systemctl disable isc-dhcp-server
systemctl disable bind9    # se non sei un DNS server

# 5. Verifica servizi in ascolto
ss -tlnp
# Ogni porta aperta è attack surface
```

---

# Parte B — AIDE (Intrusion Detection)

---

## B1. Configurazione AIDE

```bash
# AIDE: controlla integrità file tramite hash crittografici
apt install aide

# Configurazione
cat > /etc/aide/aide.conf << 'EOF'
# Database
database_in=file:/var/lib/aide/aide.db
database_out=file:/var/lib/aide/aide.db.new
database_new=file:/var/lib/aide/aide.db.new
gzip_dbout=yes

# Gruppi di attributi da monitorare
# p=permissions, i=inode, n=number of links, u=user, g=group
# s=size, m=mtime, a=atime, c=ctime
# md5=MD5 checksum, sha256=SHA256 checksum

NORM = p+i+n+u+g+s+b+m+c+sha256
LOGS = p+i+n+u+g
PERMS = p+i+u+g

# File critici: monitor tutto
/etc NORM
/bin NORM
/sbin NORM
/lib NORM
/lib64 NORM
/usr/bin NORM
/usr/sbin NORM
/usr/lib NORM

# Log: solo permessi e metadata (non contenuto — cambiano spesso)
/var/log LOGS

# Escludi file che cambiano continuamente
!/var/log/wtmp
!/var/log/btmp
!/var/log/lastlog
!/proc
!/sys
!/dev
!/run
!/tmp
!/var/cache
!/var/tmp
EOF

# Inizializza database (dopo configurazione iniziale pulita)
aide --init
mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Verifica integrità (esegui regolarmente)
aide --check

# Output esempio:
# AIDE found differences between database and filesystem!!
# Changed: /etc/passwd       (p|i|n|s|mtime|ctime|sha256)
# Removed: /usr/bin/tool_rimosso
# Added: /usr/bin/tool_aggiunto

# Aggiorna database dopo modifiche legittime
aide --update
mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Automazione
cat > /etc/cron.d/aide-check << 'EOF'
# Controllo AIDE ogni giorno alle 03:00
0 3 * * * root /usr/bin/aide --check | mail -s "AIDE Report $(hostname)" admin@esempio.it
EOF
```

---

# Parte C — USBGuard e Controllo Dispositivi

---

## C1. USBGuard

```bash
# USBGuard: blocca automaticamente dispositivi USB non autorizzati

apt install usbguard

# Crea regole per dispositivi attuali (connetti SOLO dispositivi autorizzati prima)
usbguard generate-policy > /etc/usbguard/rules.conf

# Formato regola:
# allow id 046d:c534 serial "" name "USB Receiver" via-port "1-1.2"
# block id * serial "" name "" via-port "*"

# Modalità policy
# allow  = permetti
# block  = blocca (può essere riconnesso)
# reject = blocca e rimuovi (non più visibile al sistema)

# Configura policy di default
cat > /etc/usbguard/usbguard-daemon.conf << 'EOF'
RuleFile=/etc/usbguard/rules.conf
ImplicitPolicyTarget=block    # blocca tutto ciò che non è in rules.conf
PresentDevicePolicy=apply-policy   # applica policy ai device connessi all'avvio
InsertedDevicePolicy=apply-policy  # applica policy ai device inseriti
RestoreControllerDeviceState=false
DeviceManagerBackend=uevent
IPCAllowedUsers=root
IPCAllowedGroups=usbguard
PresentControllerPolicy=keep
EOF

systemctl enable --now usbguard

# Gestione runtime
usbguard list-devices         # lista tutti i device
usbguard list-rules           # lista regole
usbguard allow-device ID      # permetti device temporaneamente
usbguard block-device ID      # blocca device
usbguard reject-device ID     # rimuovi device

# Aggiungi device permanentemente
usbguard generate-policy >> /etc/usbguard/rules.conf
systemctl restart usbguard
```

---

# Parte D — Capabilities e seccomp

---

## D1. Linux Capabilities

```bash
# Le capabilities dividono i privilegi di root in unità separate
# Invece di "root o niente", puoi dare solo le capability necessarie

# Lista capability
man capabilities

# Principali:
# CAP_NET_BIND_SERVICE — bind a porte < 1024
# CAP_NET_RAW          — socket RAW (ping, tcpdump)
# CAP_SYS_ADMIN        — molte operazioni di sistema (da evitare)
# CAP_CHOWN            — cambia owner dei file
# CAP_SETUID           — cambia UID del processo
# CAP_KILL             — invia segnali a processi altrui
# CAP_DAC_OVERRIDE     — bypassa permessi filesystem

# Verifica capability di un eseguibile
getcap /usr/bin/ping
# /usr/bin/ping = cap_net_raw+ep

# Imposta capability (alternativa a setuid)
# Esempio: python può fare bind su porta 80 senza essere root
setcap 'cap_net_bind_service=+ep' /usr/bin/python3.12
# Ora: python3 -c "import socket; s=socket.socket(); s.bind(('', 80))"  # funziona!

# Rimuovi capability da eseguibile
setcap -r /usr/bin/python3.12

# Capability nel codice Python
import ctypes
PR_SET_SECCOMP = 22
SECCOMP_MODE_STRICT = 1

# Processo senza capability
# Nessun processo dovrebbe girare con CAP_SYS_ADMIN senza motivo

# Verifica capability di un processo in esecuzione
cat /proc/PID/status | grep Cap
capsh --decode=0000000000000400   # decodifica CapPrm
```

---

## D2. seccomp

```bash
# seccomp: filtra le system call che un processo può eseguire
# Docker usa seccomp per i container per default

# Profilo seccomp JSON per Docker
cat > /etc/docker/seccomp-custom.json << 'EOF'
{
    "defaultAction": "SCMP_ACT_ERRNO",
    "architectures": ["SCMP_ARCH_X86_64"],
    "syscalls": [
        {
            "names": [
                "read", "write", "open", "close",
                "stat", "fstat", "lstat",
                "poll", "lseek", "mmap", "mprotect",
                "munmap", "brk", "rt_sigaction", "rt_sigprocmask",
                "ioctl", "pread64", "pwrite64", "readv", "writev",
                "access", "pipe", "select", "sched_yield",
                "mremap", "msync", "mincore", "madvise",
                "shmget", "shmat", "shmctl",
                "dup", "dup2", "pause", "nanosleep",
                "getitimer", "alarm", "setitimer",
                "getpid", "sendfile", "socket", "connect",
                "accept", "sendto", "recvfrom", "sendmsg",
                "recvmsg", "shutdown", "bind", "listen",
                "getsockname", "getpeername", "socketpair",
                "setsockopt", "getsockopt",
                "clone", "fork", "vfork", "execve", "exit",
                "wait4", "kill", "uname",
                "fcntl", "flock", "fsync", "fdatasync",
                "truncate", "ftruncate", "getdents", "getcwd",
                "chdir", "rename", "mkdir", "rmdir",
                "creat", "link", "unlink", "symlink",
                "readlink", "chmod", "fchmod", "chown",
                "fchown", "umask", "gettimeofday", "getrlimit",
                "getrusage", "sysinfo", "times", "ptrace",
                "getuid", "syslog", "getgid", "setuid",
                "setgid", "geteuid", "getegid", "setpgid",
                "getppid", "getpgrp", "setsid", "setreuid",
                "setregid", "getgroups", "setgroups",
                "setresuid", "getresuid", "setresgid", "getresgid",
                "getpgid", "setfsuid", "setfsgid", "getsid",
                "sigaltstack", "utime", "mknod",
                "prctl", "arch_prctl", "adjtimex",
                "setrlimit", "chroot",
                "gettid", "futex", "sched_setaffinity",
                "sched_getaffinity", "set_thread_area",
                "io_setup", "io_destroy", "io_getevents",
                "io_submit", "io_cancel", "lookup_dcookie",
                "epoll_create", "epoll_ctl", "epoll_wait",
                "remap_file_pages", "getdents64",
                "set_tid_address", "restart_syscall",
                "semtimedop", "fadvise64", "timer_create",
                "timer_settime", "timer_gettime", "timer_getoverrun",
                "timer_delete", "clock_settime", "clock_gettime",
                "clock_getres", "clock_nanosleep", "exit_group",
                "epoll_wait", "epoll_ctl", "tgkill",
                "utimes", "waitid", "ioprio_set",
                "ioprio_get", "inotify_init", "inotify_add_watch",
                "inotify_rm_watch", "openat", "mkdirat",
                "mknodat", "fchownat", "futimesat",
                "newfstatat", "unlinkat", "renameat",
                "linkat", "symlinkat", "readlinkat",
                "fchmodat", "faccessat",
                "pselect6", "ppoll", "unshare",
                "set_robust_list", "get_robust_list",
                "splice", "tee", "sync_file_range",
                "vmsplice", "move_pages",
                "epoll_pwait", "signalfd", "timerfd_create",
                "eventfd", "fallocate", "timerfd_settime",
                "timerfd_gettime", "accept4", "signalfd4",
                "eventfd2", "epoll_create1", "dup3",
                "pipe2", "inotify_init1", "preadv",
                "pwritev", "rt_tgsigqueueinfo",
                "perf_event_open", "recvmmsg",
                "fanotify_init", "fanotify_mark",
                "prlimit64", "name_to_handle_at",
                "open_by_handle_at", "clock_adjtime",
                "syncfs", "sendmmsg", "setns",
                "getcpu", "process_vm_readv", "process_vm_writev",
                "kcmp", "finit_module", "sched_setattr",
                "sched_getattr", "renameat2", "seccomp",
                "getrandom", "memfd_create", "kexec_file_load",
                "bpf", "execveat", "userfaultfd",
                "membarrier", "mlock2", "copy_file_range",
                "preadv2", "pwritev2", "pkey_mprotect",
                "pkey_alloc", "pkey_free", "statx"
            ],
            "action": "SCMP_ACT_ALLOW"
        }
    ]
}
EOF

# Usa profilo custom con Docker
docker run --security-opt seccomp=/etc/docker/seccomp-custom.json mia-app
```

---

# Parte E — Kernel Hardening e Riepilogo

---

## E1. Sysctl sicurezza

```bash
cat > /etc/sysctl.d/99-hardening.conf << 'EOF'
# ===== Kernel pointer e dmesg =====
# Nascondi indirizzi kernel da utenti non privilegiati
kernel.kptr_restrict = 2

# Limita accesso a dmesg
kernel.dmesg_restrict = 1

# Disabilita SysRq (attacchi fisici)
kernel.sysrq = 0

# Proteggi ptrace (debug processi)
kernel.yama.ptrace_scope = 1   # solo processi figli

# Proteggi core dump
kernel.core_pattern = |/bin/false
fs.suid_dumpable = 0

# ===== Rete =====
# Previeni IP spoofing
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Disabilita ICMP redirect
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0

# Ignora ICMP broadcast
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Proteggi contro SYN flood
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_syn_retries = 5
net.ipv4.tcp_synack_retries = 2

# Non rivelare info kernel via TCP timestamps
net.ipv4.tcp_timestamps = 0

# Limita richieste ICMP
net.ipv4.icmp_ratelimit = 100

# ===== Filesystem =====
# Proteggi link simbolici/hard link
fs.protected_symlinks = 1
fs.protected_hardlinks = 1

# Proteggi FIFO (named pipe)
fs.protected_fifos = 2
fs.protected_regular = 2
EOF

sysctl --system
```

## E2. Checklist hardening

| Area | Controllo | Comando verifica |
|---|---|---|
| SSH | PasswordAuthentication no | `grep PasswordAuth /etc/ssh/sshd_config` |
| SSH | PermitRootLogin no | `grep PermitRoot /etc/ssh/sshd_config` |
| Filesystem | /tmp noexec | `mount \| grep /tmp` |
| Kernel | kptr_restrict=2 | `sysctl kernel.kptr_restrict` |
| Auditd | attivo | `systemctl is-active auditd` |
| AIDE | database inizializzata | `ls -la /var/lib/aide/aide.db` |
| USBGuard | attivo | `systemctl is-active usbguard` |
| Firewall | attivo | `ufw status` o `nft list ruleset` |
| AppArmor/SELinux | enforcing | `aa-status` / `getenforce` |
| PAM | password complexity | `grep pam_pwquality /etc/pam.d/*` |

## Prossimi passi

- `tutorial_linux_35_compliance.md` — OpenSCAP e compliance
- `tutorial_linux_11_sicurezza.md` — sicurezza base
- `tutorial_linux_27_selinux_apparmor.md` — MAC policies
