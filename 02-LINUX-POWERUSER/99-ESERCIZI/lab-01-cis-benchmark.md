# Lab 01 — Applicazione CIS Benchmark Debian 12 Level 1+2

> **Modulo di riferimento:** [34-hardening-sicurezza-avanzata.md](../34-hardening-sicurezza-avanzata.md)
> **Tempo stimato:** 3-4 ore
> **Livello:** proficient
> **Prerequisiti:** VM Debian 12 con accesso root, completamento moduli 01, 04, 11
> **Ultimo aggiornamento:** 2026-05-23

---

## Obiettivo

Applicare sistematicamente le raccomandazioni CIS Benchmark Level 1 e Level 2 per Debian 12, documentando ogni modifica e ogni eccezione giustificata.

---

## Ambiente

- VM Debian 12 (installazione minimale, nessun desktop environment)
- 2 vCPU, 2 GB RAM, 20 GB disco
- Accesso root via console (non SSH inizialmente)
- Snapshot della VM prima di iniziare

---

## Parte 1 — Audit Iniziale (30 min)

### 1.1 Installare Lynis e eseguire audit baseline

```bash
apt update && apt install -y lynis

lynis audit system --no-colors | tee /root/lynis-baseline.log

grep "Hardening index" /root/lynis-baseline.log
```

Annotare il punteggio iniziale. Target finale: ≥ 85.

### 1.2 Documentare lo stato pre-hardening

```bash
# Kernel parameters
sysctl -a > /root/sysctl-before.txt

# Servizi attivi
systemctl list-units --type=service --state=running > /root/services-before.txt

# Porte in ascolto
ss -tlnp > /root/ports-before.txt

# Utenti con shell di login
grep -v '/nologin\|/false' /etc/passwd > /root/users-login-before.txt

# Permessi SUID/SGID
find / -type f \( -perm -4000 -o -perm -2000 \) -exec ls -la {} \; 2>/dev/null > /root/suid-sgid-before.txt
```

---

## Parte 2 — Filesystem e Partizioni (30 min)

### 2.1 Mount options di sicurezza

Verificare e applicare le opzioni di mount richieste dal CIS:

```bash
# Verificare mount options attuali
findmnt --noheadings -o TARGET,OPTIONS

# /tmp deve avere noexec,nosuid,nodev
# Se /tmp è sullo stesso filesystem di /, creare un tmpfs dedicato:
cat >> /etc/fstab << 'EOF'
tmpfs /tmp tmpfs defaults,noexec,nosuid,nodev,size=512M 0 0
EOF

# /var/tmp: bind mount o partizione separata
# /dev/shm: verificare noexec,nosuid,nodev
findmnt /dev/shm
# Se mancano opzioni:
# mount -o remount,noexec,nosuid,nodev /dev/shm
```

### 2.2 Disabilitare filesystem non necessari

```bash
cat > /etc/modprobe.d/cis-filesystem.conf << 'EOF'
install cramfs /bin/false
install freevxfs /bin/false
install hfs /bin/false
install hfsplus /bin/false
install jffs2 /bin/false
install udf /bin/false
install squashfs /bin/false
EOF
```

### 2.3 Verificare permessi file critici

```bash
# /etc/passwd deve essere 644 root:root
chmod 644 /etc/passwd
chown root:root /etc/passwd

# /etc/shadow deve essere 640 root:shadow
chmod 640 /etc/shadow
chown root:shadow /etc/shadow

# /etc/group deve essere 644 root:root
chmod 644 /etc/group
chown root:root /etc/group

# /etc/gshadow deve essere 640 root:shadow
chmod 640 /etc/gshadow
chown root:shadow /etc/gshadow
```

---

## Parte 3 — Kernel Hardening (30 min)

### 3.1 Sysctl hardening

```bash
cat > /etc/sysctl.d/99-cis-hardening.conf << 'EOF'
# CIS Benchmark - Network
net.ipv4.ip_forward = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.tcp_syncookies = 1

# IPv6
net.ipv6.conf.all.accept_ra = 0
net.ipv6.conf.default.accept_ra = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# CIS Benchmark - Kernel
kernel.randomize_va_space = 2
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
kernel.yama.ptrace_scope = 2
kernel.sysrq = 0
kernel.core_uses_pid = 1
fs.suid_dumpable = 0
EOF

sysctl --system
```

### 3.2 Disabilitare core dump

```bash
# Via limits.conf
echo "* hard core 0" >> /etc/security/limits.d/cis-coredump.conf

# Via systemd
mkdir -p /etc/systemd/coredump.conf.d
cat > /etc/systemd/coredump.conf.d/disable.conf << 'EOF'
[Coredump]
Storage=none
ProcessSizeMax=0
EOF

systemctl daemon-reload
```

---

## Parte 4 — Account e Autenticazione (45 min)

### 4.1 Password policy con pam_pwquality

```bash
apt install -y libpam-pwquality

cat > /etc/security/pwquality.conf << 'EOF'
minlen = 14
dcredit = -1
ucredit = -1
ocredit = -1
lcredit = -1
minclass = 4
maxrepeat = 3
maxclassrepeat = 3
gecoscheck = 1
EOF
```

### 4.2 Configurare faillock

```bash
# /etc/pam.d/common-auth: aggiungere faillock
# Dopo 5 tentativi falliti, blocco di 900 secondi
cat > /etc/security/faillock.conf << 'EOF'
deny = 5
unlock_time = 900
fail_interval = 900
audit
even_deny_root
root_unlock_time = 60
EOF
```

### 4.3 Password aging

```bash
# /etc/login.defs
sed -i 's/^PASS_MAX_DAYS.*/PASS_MAX_DAYS   365/' /etc/login.defs
sed -i 's/^PASS_MIN_DAYS.*/PASS_MIN_DAYS   1/' /etc/login.defs
sed -i 's/^PASS_WARN_AGE.*/PASS_WARN_AGE   7/' /etc/login.defs

# UMASK 027
sed -i 's/^UMASK.*/UMASK           027/' /etc/login.defs

# Verificare utenti esistenti
for user in $(awk -F: '($3 >= 1000 && $7 != "/usr/sbin/nologin" && $7 != "/bin/false") {print $1}' /etc/passwd); do
    chage --maxdays 365 --mindays 1 --warndays 7 "$user"
done
```

### 4.4 Disabilitare account non necessari

```bash
# Verificare account senza password
awk -F: '($2 == "" ) {print $1}' /etc/shadow

# Bloccare account di sistema non necessari
for user in games gnats irc list news uucp; do
    usermod -L -s /usr/sbin/nologin "$user" 2>/dev/null
done
```

---

## Parte 5 — SSH Hardening (30 min)

### 5.1 Configurazione sshd

```bash
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak

cat > /etc/ssh/sshd_config.d/cis-hardening.conf << 'EOF'
Protocol 2
LogLevel VERBOSE
MaxAuthTries 3
MaxSessions 4
PermitRootLogin no
PermitEmptyPasswords no
PasswordAuthentication no
PubkeyAuthentication yes
HostbasedAuthentication no
IgnoreRhosts yes
X11Forwarding no
AllowTcpForwarding no
AllowAgentForwarding no
PermitUserEnvironment no
Banner /etc/issue.net
UsePAM yes
ClientAliveInterval 300
ClientAliveCountMax 3
LoginGraceTime 60
MaxStartups 10:30:60

# Crittografia forte
KexAlgorithms sntrup761x25519-sha512@openssh.com,curve25519-sha256,curve25519-sha256@libssh.org
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com
HostKeyAlgorithms ssh-ed25519,rsa-sha2-512,rsa-sha2-256
EOF

# Banner
echo "Authorized access only. All activity is monitored and logged." > /etc/issue.net

# Verificare configurazione
sshd -t && systemctl reload sshd
```

### 5.2 Permessi file SSH

```bash
chmod 600 /etc/ssh/sshd_config
chown root:root /etc/ssh/sshd_config
chmod 600 /etc/ssh/ssh_host_*_key
chmod 644 /etc/ssh/ssh_host_*_key.pub
```

---

## Parte 6 — Audit System (30 min)

### 6.1 Configurare auditd

```bash
apt install -y auditd audispd-plugins

cat > /etc/audit/rules.d/cis.rules << 'AUDIT_EOF'
# CIS Benchmark audit rules

# Ensure events that modify date and time information are collected
-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time-change
-a always,exit -F arch=b32 -S adjtimex -S settimeofday -S stime -k time-change
-a always,exit -F arch=b64 -S clock_settime -k time-change
-a always,exit -F arch=b32 -S clock_settime -k time-change
-w /etc/localtime -p wa -k time-change

# Ensure events that modify user/group information are collected
-w /etc/group -p wa -k identity
-w /etc/passwd -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/security/opasswd -p wa -k identity

# Ensure events that modify the system's network environment are collected
-a always,exit -F arch=b64 -S sethostname -S setdomainname -k system-locale
-a always,exit -F arch=b32 -S sethostname -S setdomainname -k system-locale
-w /etc/issue -p wa -k system-locale
-w /etc/issue.net -p wa -k system-locale
-w /etc/hosts -p wa -k system-locale
-w /etc/network -p wa -k system-locale

# Ensure events that modify the system's Mandatory Access Controls are collected
-w /etc/apparmor/ -p wa -k MAC-policy
-w /etc/apparmor.d/ -p wa -k MAC-policy

# Ensure login and logout events are collected
-w /var/log/faillog -p wa -k logins
-w /var/log/lastlog -p wa -k logins
-w /var/log/tallylog -p wa -k logins

# Ensure session initiation information is collected
-w /var/run/utmp -p wa -k session
-w /var/log/wtmp -p wa -k session
-w /var/log/btmp -p wa -k session

# Ensure discretionary access control permission modification events are collected
-a always,exit -F arch=b64 -S chmod -S fchmod -S fchmodat -k perm_mod
-a always,exit -F arch=b32 -S chmod -S fchmod -S fchmodat -k perm_mod
-a always,exit -F arch=b64 -S chown -S fchown -S fchownat -S lchown -k perm_mod
-a always,exit -F arch=b32 -S chown -S fchown -S fchownat -S lchown -k perm_mod

# Ensure unsuccessful unauthorized file access attempts are collected
-a always,exit -F arch=b64 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EACCES -k access
-a always,exit -F arch=b32 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EACCES -k access
-a always,exit -F arch=b64 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EPERM -k access
-a always,exit -F arch=b32 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EPERM -k access

# Ensure use of privileged commands is collected
# Generate with: find / -xdev -type f -perm -4000 -o -perm -2000
-a always,exit -F path=/usr/bin/sudo -F perm=x -k privileged
-a always,exit -F path=/usr/bin/su -F perm=x -k privileged
-a always,exit -F path=/usr/bin/passwd -F perm=x -k privileged
-a always,exit -F path=/usr/bin/chfn -F perm=x -k privileged
-a always,exit -F path=/usr/bin/chsh -F perm=x -k privileged
-a always,exit -F path=/usr/bin/newgrp -F perm=x -k privileged

# Ensure kernel module loading and unloading is collected
-w /sbin/insmod -p x -k modules
-w /sbin/rmmod -p x -k modules
-w /sbin/modprobe -p x -k modules
-a always,exit -F arch=b64 -S init_module -S delete_module -k modules

# Make the configuration immutable (requires reboot to change)
-e 2
AUDIT_EOF

# Caricare le regole
augenrules --load
systemctl enable auditd
```

---

## Parte 7 — Servizi e Network (30 min)

### 7.1 Disabilitare servizi non necessari

```bash
# Lista servizi da disabilitare (Level 2)
for svc in avahi-daemon cups bluetooth rpcbind; do
    systemctl stop "$svc" 2>/dev/null
    systemctl disable "$svc" 2>/dev/null
    systemctl mask "$svc" 2>/dev/null
done
```

### 7.2 Firewall base con nftables

```bash
cat > /etc/nftables.conf << 'NFT_EOF'
#!/usr/sbin/nft -f
flush ruleset

table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;

        iif "lo" accept
        ct state established,related accept
        ct state invalid drop

        # SSH dalla rete management
        tcp dport 22 ip saddr 10.0.0.0/24 ct state new accept

        # ICMP limitato
        ip protocol icmp icmp type echo-request limit rate 1/second accept
        ip6 nexthdr icmpv6 icmpv6 type { nd-neighbor-solicit, nd-router-advert, nd-neighbor-advert } accept

        # Log e drop
        limit rate 5/minute log prefix "[nftables-DROP] " drop
    }

    chain forward {
        type filter hook forward priority 0; policy drop;
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}
NFT_EOF

systemctl enable nftables
nft -f /etc/nftables.conf
```

---

## Parte 8 — Verifica Finale (30 min)

### 8.1 Re-scan con Lynis

```bash
lynis audit system --no-colors | tee /root/lynis-post.log

grep "Hardening index" /root/lynis-post.log
```

### 8.2 Confronto

```bash
# Confrontare punteggi
echo "=== BEFORE ==="
grep "Hardening index" /root/lynis-baseline.log
echo "=== AFTER ==="
grep "Hardening index" /root/lynis-post.log

# Confrontare sysctl
diff /root/sysctl-before.txt <(sysctl -a 2>/dev/null) | head -50

# Confrontare servizi
diff /root/services-before.txt <(systemctl list-units --type=service --state=running)
```

### 8.3 Documentazione eccezioni

Per ogni raccomandazione CIS **non** applicata, documentare:

| # CIS | Raccomandazione | Motivo eccezione | Rischio accettato |
|-------|----------------|------------------|-------------------|
| Es. 1.1.1.4 | Disable squashfs | Necessario per snap | Basso — snap confinato |

---

## Criteri di Completamento

- [ ] Lynis score ≥ 85
- [ ] Tutte le modifiche documentate
- [ ] Eccezioni giustificate nel registro
- [ ] SSH funzionante con sola autenticazione a chiave pubblica
- [ ] auditd attivo con regole CIS caricate
- [ ] nftables attivo con policy DROP
- [ ] Nessun servizio non necessario in esecuzione
- [ ] Snapshot post-hardening creato

---

## Riferimenti

- CIS Benchmark Debian 12 — https://www.cisecurity.org/benchmark/debian (consultato: 2026-05-23)
- [34-hardening-sicurezza-avanzata.md](../34-hardening-sicurezza-avanzata.md)
- [11-sicurezza.md](../11-sicurezza.md)
- [24-iptables-nftables-guida-completa.md](../24-iptables-nftables-guida-completa.md)
- [10-ssh-avanzato.md](../10-ssh-avanzato.md)
