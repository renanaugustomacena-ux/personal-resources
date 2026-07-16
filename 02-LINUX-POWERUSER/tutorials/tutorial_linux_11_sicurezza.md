# Tutorial Linux 11 — Sicurezza: ufw, iptables, fail2ban, auditd, sudoers

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** hardening sistema, firewall, IDS, auditd, sudoers, PAM, apparmor
> **Prerequisiti:** `tutorial_linux_10_ssh_avanzato.md`, `tutorial_linux_04_systemd.md`
> **Durata stimata:** 14-18 ore

---

## Mappa concettuale

```
Sicurezza Linux
│
├── Firewall
│   ├── ufw — regole semplici
│   ├── iptables — regole avanzate
│   └── nftables — moderno
│
├── Intrusion Prevention
│   ├── fail2ban — ban IP per tentativi falliti
│   └── sshguard — alternativa fail2ban
│
├── Audit e Logging
│   ├── auditd — log syscall e file access
│   ├── ausearch / aureport
│   └── /var/log/auth.log
│
├── Accesso e Privilegi
│   ├── sudoers — controllo sudo
│   ├── PAM — authentication stack
│   └── polkit — accesso GUI
│
├── Hardening applicazioni
│   ├── AppArmor (Ubuntu)
│   ├── SELinux (RHEL) — tutorial_linux_27
│   └── seccomp — filtra syscall
│
└── Checklist CIS Benchmark
    ├── Partizioni separate
    ├── Servizi minimi
    └── Password policy
```

---

# Parte A — Firewall con ufw e iptables

---

## A1. ufw — configurazione produzione

```bash
# Stato iniziale
ufw status verbose

# Regola fondamentale: default deny in entrata
ufw default deny incoming
ufw default allow outgoing

# SSH — PRIMA di tutto! (o ti tagli fuori)
ufw allow 22/tcp      # oppure la porta SSH custom
ufw limit 22/tcp      # rate limit: max 6 tentativi/30s

# Web server
ufw allow 80/tcp
ufw allow 443/tcp

# Database — solo da IP specifici
ufw allow from 10.0.1.0/24 to any port 5432 proto tcp

# Monitoring
ufw allow from 10.0.0.100 to any port 9090 proto tcp   # Prometheus

# Abilita (dopo aver configurato le regole!)
ufw enable

# Log
ufw logging on          # medium, high, full
# Log in /var/log/ufw.log

# Regole numerate per rimozione
ufw status numbered
ufw delete 5            # rimuovi regola numero 5

# Reload
ufw reload
```

> **Analogia:** Un firewall è come il sistema di sicurezza di un condominio. Il "default deny incoming" è come una porta blindata chiusa: nessuno entra senza essere autorizzato. Ogni `allow` è come consegnare un badge per un piano specifico. `ufw limit 22/tcp` è come un portiere che blocca chi suona il campanello troppe volte di fila — fail2ban è il casiere che chiama la polizia se il tentativo persiste.

---

## A2. iptables avanzato

```bash
# Script firewall completo — salva come /etc/firewall.sh
#!/usr/bin/env bash
set -euo pipefail

# Variabili
SSH_PORT=2222
ADMIN_IP="10.0.0.5"

# Pulisce le regole esistenti
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X

# Policy di default
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Loopback — sempre permettere
iptables -A INPUT -i lo -j ACCEPT

# Connessioni stabilite (risposta a traffic outbound)
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# SSH solo da IP admin (più sicuro di aprirlo a tutti)
iptables -A INPUT -p tcp --dport "$SSH_PORT" -s "$ADMIN_IP" -j ACCEPT

# SSH con rate limiting (se deve essere accessibile da tutti)
iptables -A INPUT -p tcp --dport "$SSH_PORT" \
    -m recent --set --name ssh_ratelimit
iptables -A INPUT -p tcp --dport "$SSH_PORT" \
    -m recent --update --seconds 60 --hitcount 4 --name ssh_ratelimit \
    -j DROP
iptables -A INPUT -p tcp --dport "$SSH_PORT" -j ACCEPT

# HTTP/HTTPS
iptables -A INPUT -p tcp -m multiport --dports 80,443 -j ACCEPT

# ICMP ping (limitato)
iptables -A INPUT -p icmp --icmp-type echo-request \
    -m limit --limit 1/second -j ACCEPT

# Drop tutto il resto (già in policy DROP ma aggiungiamo log)
iptables -A INPUT -j LOG --log-prefix "FW-DROP: " --log-level 4
iptables -A INPUT -j DROP

# Salva
iptables-save > /etc/iptables/rules.v4
```

---

# Parte B — fail2ban

---

## B1. Configurazione fail2ban

```bash
# Installa
apt install fail2ban

# NON modificare /etc/fail2ban/jail.conf — sarà sovrascritto
# Crea /etc/fail2ban/jail.local
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
# Ban IP per 24 ore
bantime = 86400
# Trova tentativi in 10 minuti
findtime = 600
# Ban dopo 5 tentativi
maxretry = 5
# Backend di lettura log
backend = systemd
# Notifica email
destemail = admin@esempio.it
sendername = fail2ban
mta = sendmail

# Ignora IP locali e fidati
ignoreip = 127.0.0.1/8 ::1 10.0.0.0/8 192.168.0.0/16

[sshd]
enabled = true
port = 2222
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600    # 1 ora per SSH

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 10

[nginx-botsearch]
enabled = true
filter = nginx-botsearch
logpath = /var/log/nginx/access.log
maxretry = 2

# Jail custom per API
[api-auth]
enabled = true
filter = api-auth
logpath = /var/log/app/access.log
maxretry = 10
findtime = 300
bantime = 7200
EOF

# Crea filtro custom
cat > /etc/fail2ban/filter.d/api-auth.conf << 'EOF'
[Definition]
failregex = <HOST> .* "POST /api/login" (400|401|403)
ignoreregex =
EOF

systemctl enable --now fail2ban
```

```bash
# Gestione fail2ban
fail2ban-client status               # stato generale
fail2ban-client status sshd          # stato jail sshd
fail2ban-client set sshd unbanip 1.2.3.4   # sblocca IP
fail2ban-client banned               # lista tutti i banned IP

# Log in tempo reale
tail -f /var/log/fail2ban.log
journalctl -u fail2ban -f
```

---

# Parte C — auditd

---

## C1. Audit di sistema

```bash
# Installa
apt install auditd audispd-plugins

# Regole di audit
# /etc/audit/rules.d/audit.rules

cat > /etc/audit/rules.d/99-production.rules << 'EOF'
# Cancella regole esistenti
-D

# Buffer size
-b 8192

# Fallimento se non riesce a loggare
-f 2

# Monitora accessi file sensibili
-w /etc/passwd -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/sudoers -p wa -k sudoers
-w /etc/sudoers.d/ -p wa -k sudoers

# Monitora SSH
-w /etc/ssh/sshd_config -p wa -k sshd_config
-w /root/.ssh -p wa -k root_ssh

# Comandi privilegiati
-a always,exit -F arch=b64 -S execve -F euid=0 -k root_commands
-a always,exit -F arch=b64 -S setuid -F a0=0 -F exe=/usr/bin/sudo -k sudo

# Accessi a file di configurazione
-w /etc/crontab -p wa -k crontab
-w /etc/cron.d/ -p wa -k crontab
-w /var/spool/cron/ -p wa -k crontab

# Login/logout
-w /var/log/faillog -p wa -k logins
-w /var/log/lastlog -p wa -k logins
-w /var/run/faillock/ -p wa -k logins

# Rete
-a always,exit -F arch=b64 -S bind -k network_bind
EOF

# Ricarica regole
augenrules --load
systemctl restart auditd

# Ricerca nel log di audit
ausearch -k identity          # tutto ciò che ha toccato identity
ausearch -k sudoers -i        # modifiche a sudoers (-i = interpreta UID)
ausearch -ui 1000 -i          # azioni dell'utente 1000
ausearch -ts today -k root_commands  # comandi root oggi

# Report
aureport --login -i           # report login
aureport --failed             # solo tentativi falliti
aureport --file -i | head -20 # file più acceduti
aureport --summary            # riepilogo
```

---

# Parte D — sudoers e PAM

---

## D1. Configurazione sudoers

```bash
# SEMPRE modifica sudoers con visudo (verifica sintassi)
visudo

# Sintassi: utente host=(run_as) comando
# mario ALL=(ALL) ALL          # mario può fare tutto
# mario ALL=(ALL) NOPASSWD:ALL # senza password (pericoloso!)

# Gruppi (consigliato)
# %sudo  ALL=(ALL:ALL) ALL     # gruppo sudo
# %admin ALL=(ALL) ALL

# Comandi specifici senza password
mario ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx
mario ALL=(ALL) NOPASSWD: /usr/sbin/service nginx *

# Alias per gruppi di comandi
Cmnd_Alias WEBOPS = /usr/bin/systemctl * nginx, /usr/bin/systemctl * apache2
%webteam ALL=(ALL) NOPASSWD: WEBOPS

# Esegui come utente specifico (non root)
mario ALL=(postgres) /usr/bin/psql

# /etc/sudoers.d/ — file separati per modularità
cat > /etc/sudoers.d/webops << 'EOF'
# Web operations team
Cmnd_Alias NGINX = /usr/bin/systemctl start nginx, \
                   /usr/bin/systemctl stop nginx, \
                   /usr/bin/systemctl restart nginx, \
                   /usr/bin/systemctl reload nginx
%webops ALL=(ALL) NOPASSWD: NGINX
EOF
chmod 440 /etc/sudoers.d/webops
```

---

## D2. AppArmor (Ubuntu)

```bash
# Status
aa-status
apparmor_status

# Profili: enforce (blocca) vs complain (solo log)
aa-enforce /etc/apparmor.d/usr.bin.nginx       # forza profilo
aa-complain /etc/apparmor.d/usr.bin.nginx      # solo log violazioni

# Profilo AppArmor base per applicazione
cat > /etc/apparmor.d/opt.mia-app << 'EOF'
#include <tunables/global>

profile mia-app /opt/mia-app/venv/bin/python3 {
    #include <abstractions/base>
    #include <abstractions/python>
    #include <abstractions/ssl_certs>

    # Eseguibili
    /opt/mia-app/venv/bin/python3 mr,
    /usr/bin/python3.* mr,

    # File applicazione (lettura)
    /opt/mia-app/** r,

    # Log (scrittura)
    /var/log/mia-app/** w,

    # Rete
    network tcp,

    # Database socket
    /var/run/postgresql/.s.PGSQL.5432 rw,

    # Nega tutto il resto
    deny /etc/** w,
    deny /var/lib/** w,
}
EOF

# Carica e attiva
apparmor_parser -r /etc/apparmor.d/opt.mia-app
aa-enforce /etc/apparmor.d/opt.mia-app
```

---

# Parte E — Riepilogo

## Hardening checklist rapida

```bash
# 1. SSH hardening
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
systemctl reload sshd

# 2. Firewall
ufw default deny incoming
ufw allow 22/tcp
ufw enable

# 3. Aggiorna sistema
apt update && apt upgrade -y
apt install unattended-upgrades
dpkg-reconfigure unattended-upgrades

# 4. Rimuovi servizi non necessari
systemctl disable bluetooth cups avahi-daemon
systemctl stop bluetooth cups avahi-daemon

# 5. fail2ban
apt install fail2ban
systemctl enable --now fail2ban

# 6. Audit
apt install auditd
systemctl enable --now auditd
```

## Prossimi passi

- `tutorial_linux_12_utenti_e_gruppi.md` — gestione utenti avanzata
- `tutorial_linux_27_selinux_apparmor.md` — SELinux e AppArmor completi
