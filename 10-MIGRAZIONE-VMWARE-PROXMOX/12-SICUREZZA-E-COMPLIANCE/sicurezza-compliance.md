# Sicurezza e Compliance nella Migrazione VMware to Proxmox VE

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 5 — Operativita post-migrazione · Modulo 12.3 (chiude sezione sicurezza, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** moduli 12.1 (TLS) e 12.2 (LDAP/AD); concetti di hardening Linux, network isolation, audit logging, GDPR/HIPAA/PCI-DSS, ISO 27001.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. applicare **CIS Benchmark Debian** sul nodo Proxmox: ssh hardening, firewall (Proxmox FW + nft), kernel sysctl, audit (auditd), file integrity (AIDE);
> 2. configurare RBAC fine-grained con `pveum` (ruoli, gruppi, ACL su pool/node/storage), least-privilege per ogni gruppo;
> 3. configurare **network isolation**: VLAN per management/cluster/storage/VM, firewall L4/L7, microsegmentation guest-level;
> 4. implementare **audit logging**: `journald` persistente, forward a SIEM (Wazuh, Splunk, Elastic), correlation con eventi cluster;
> 5. mappare i requisiti compliance (GDPR data residency, HIPAA PHI, PCI-DSS scope) alle feature Proxmox e gap;
> 6. eseguire **incident response** post-incidente: isolamento nodo, preservazione evidenza, root cause analysis;
> 7. mantenere un programma di **vulnerability management**: subscription updates, monitoring CVE Proxmox/Debian, patch cycle.
> **Tempo stimato:** lettura 90-120 min · lab 360-480 min (hardening + audit + drill compliance)
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-27
> **Versioni di riferimento:** Proxmox VE 8.x; CIS Debian 12 Benchmark; GDPR (2016/679); ISO/IEC 27001:2022.

## Mappa concettuale

```
+============================================================+
|     Sicurezza Proxmox: stack di difesa multi-layer         |
+============================================================+
|                                                            |
|   LIVELLO 1: HARDENING SO                                  |
|   - SSH: key-only, no root login, fail2ban                 |
|   - Firewall: Proxmox FW + nft, default DROP               |
|   - Kernel: sysctl hardening                               |
|   - File integrity: AIDE/Tripwire                          |
|   - Updates: auto-updates security only                    |
|                                                            |
|   LIVELLO 2: AUTH & RBAC                                   |
|   - LDAP/AD realm con LDAPS                                |
|   - 2FA TOTP o RADIUS                                      |
|   - RBAC fine-grained (pveum)                              |
|   - Least-privilege gruppi                                 |
|                                                            |
|   LIVELLO 3: NETWORK ISOLATION                             |
|   - VLAN management (out-of-band)                          |
|   - VLAN cluster (corosync)                                |
|   - VLAN storage (Ceph/iSCSI)                              |
|   - VLAN VM produzione                                     |
|   - VLAN VM DMZ/test                                       |
|                                                            |
|   LIVELLO 4: VM SECURITY                                   |
|   - Guest hardening (CIS per OS)                           |
|   - Microsegmentation L4 (Proxmox FW guest level)          |
|   - Encryption at rest (LUKS, ZFS native)                  |
|                                                            |
|   LIVELLO 5: MONITORING & AUDIT                            |
|   - journald persistente                                   |
|   - SIEM forward (Wazuh, Splunk)                           |
|   - Alert correlazione                                     |
|   - Audit trail tampering detection                        |
|                                                            |
|   LIVELLO 6: COMPLIANCE                                    |
|   - GDPR data residency                                    |
|   - HIPAA PHI segregation                                  |
|   - PCI-DSS scope reduction                                |
|   - ISO 27001 controls                                     |
|                                                            |
+============================================================+
```

Idee guida del modulo:

1. **Migrazione e *occasione* per migliorare la security baseline.** Spesso ambienti VMware legacy hanno tech debt: cert self-signed, SSH password, no MFA, no audit. Proxmox green-field permette di ricominciare con baseline corretta.
2. **Compliance non e solo carta — e processo.** Avere documenti GDPR DPIA non protegge se i log non sono raccolti, le password sono condivise, e nessuno fa drill incident response. La security operativa supporta la compliance, non viceversa.
3. **Hardening incrementale > big-bang.** Applicare CIS Benchmark al 100% dal day 1 puo rompere applicazioni. Approccio: baseline minima accettabile day 1, aggiungere ogni mese 2-3 controlli, validare nessuna regressione.
4. **Network isolation e il maggior moltiplicatore.** Un'attacco in zona produzione non puo lateralmente raggiungere management se VLAN sono isolate, il firewall e default-DROP, e l'accesso management e via VPN/jumphost.

---

## Indice

1. [Proxmox Hardening](#1-proxmox-hardening)
2. [User Management e RBAC](#2-user-management-e-rbac)
3. [Integrazione LDAP/Active Directory](#3-integrazione-ldapactive-directory)
4. [Certificati SSL/TLS](#4-certificati-ssltls)
5. [Audit Logging](#5-audit-logging)
6. [Network Isolation](#6-network-isolation)
7. [Compliance GDPR e ISO 27001](#7-compliance-gdpr-e-iso-27001)
8. [Vulnerability Scanning e Patching](#8-vulnerability-scanning-e-patching)
9. [Confronto Sicurezza VMware vs Proxmox](#9-confronto-sicurezza-vmware-vs-proxmox)

---

## 1. Proxmox Hardening

### 1.1 SSH Hardening

Configurazione `/etc/ssh/sshd_config`:

```bash
# Disabilitare root login con password
PermitRootLogin prohibit-password

# Solo autenticazione a chiave
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys

# Protocollo e algoritmi sicuri
Protocol 2
KexAlgorithms curve25519-sha256@libssh.org,ecdh-sha2-nistp521
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com

# Limitazioni accesso
MaxAuthTries 3
MaxSessions 5
LoginGraceTime 30
ClientAliveInterval 300
ClientAliveCountMax 2
AllowUsers adminpve@10.0.0.0/24

# Disabilitare funzionalita' non necessarie
X11Forwarding no
AllowTcpForwarding no
AllowAgentForwarding no
```

```bash
# Applicare e verificare
systemctl restart sshd
sshd -T | grep -E "permitrootlogin|passwordauthentication|pubkeyauthentication"
```

### 1.2 Fail2ban

```bash
apt install fail2ban -y
```

Configurazione `/etc/fail2ban/jail.local`:

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
banaction = iptables-multiport
backend = systemd

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 7200

[proxmox-gui]
enabled = true
port = 8006
filter = proxmox-gui
logpath = /var/log/daemon.log
maxretry = 5
bantime = 3600
```

Filter custom `/etc/fail2ban/filter.d/proxmox-gui.conf`:

```ini
[Definition]
failregex = pvedaemon\[.*authentication failure; rhost=<HOST> user=.* msg=.*
ignoreregex =
```

```bash
systemctl enable --now fail2ban
fail2ban-client status
fail2ban-client status sshd
```

### 1.3 Sysctl Hardening

File `/etc/sysctl.d/99-proxmox-hardening.conf`:

```bash
# Network hardening
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2

# Protezione memoria
kernel.randomize_va_space = 2
kernel.kptr_restrict = 2
kernel.dmesg_restrict = 1
kernel.yama.ptrace_scope = 1
fs.suid_dumpable = 0

# Limiti connessioni
net.ipv4.ip_local_port_range = 1024 65535
net.core.somaxconn = 65535
```

```bash
sysctl --system
```

### 1.4 Aggiornamenti Automatici

```bash
apt install unattended-upgrades apt-listchanges -y
```

File `/etc/apt/apt.conf.d/50unattended-upgrades`:

```
Unattended-Upgrade::Origins-Pattern {
    "origin=Debian,codename=${distro_codename},label=Debian-Security";
    "origin=Proxmox,codename=${distro_codename},label=Proxmox";
};
Unattended-Upgrade::Mail "admin@azienda.it";
Unattended-Upgrade::MailReport "on-change";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Automatic-Reboot-Time "03:00";
```

### 1.5 Sicurezza Web Interface

```bash
# Limitare accesso alla GUI solo da management network
iptables -A INPUT -p tcp --dport 8006 -s 10.0.100.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 8006 -j DROP

# Salvare regole persistenti
apt install iptables-persistent -y
netfilter-persistent save
```

Modificare `/etc/default/pveproxy` per TLS hardening:

```
CIPHERS="ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384"
HONOR_CIPHER_ORDER=1
DENY_FROM=all
ALLOW_FROM=10.0.100.0/24,192.168.1.0/24
```

```bash
systemctl restart pveproxy
```

---

## 2. User Management e RBAC

### 2.1 Realms Disponibili

| Realm | Descrizione | Uso tipico |
|-------|-------------|------------|
| `pam` | Linux PAM locale | Amministratori host |
| `pve` | Proxmox VE interno | Utenti senza account Linux |
| `ldap` | Server LDAP generico | Directory aziendale |
| `ad` | Active Directory | Ambiente Windows enterprise |
| `openid` | OpenID Connect | SSO moderno (Keycloak, Azure AD) |

### 2.2 Ruoli Predefiniti e Custom

| Ruolo | Privilegi chiave | Target |
|-------|-----------------|--------|
| `Administrator` | Tutti i privilegi | Super admin |
| `PVEAdmin` | Quasi tutti, no Sys.PowerMgmt | Admin delegato |
| `PVEVMAdmin` | Gestione completa VM/CT | Team virtualizzazione |
| `PVEVMUser` | Start/stop, console, backup | Operatori |
| `PVEAuditor` | Solo lettura | Auditor/monitoring |
| `PVEPoolUser` | Gestione VM nel pool assegnato | Utenti dipartimento |

Creazione ruolo custom:

```bash
# Ruolo per operatore di migrazione
pveum role add MigrationOperator -privs \
  "VM.Allocate VM.Clone VM.Config.Disk VM.Config.CPU VM.Config.Memory \
   VM.Config.Network VM.Config.Options VM.Console VM.Monitor \
   VM.PowerMgmt VM.Snapshot VM.Migrate \
   Datastore.AllocateSpace Datastore.Audit \
   SDN.Audit Pool.Audit"

# Ruolo per help desk
pveum role add HelpDesk -privs \
  "VM.Console VM.PowerMgmt VM.Audit VM.Snapshot \
   Pool.Audit Datastore.Audit SDN.Audit"
```

### 2.3 Gestione Utenti e Permessi

```bash
# Creare utente
pveum user add mario.rossi@pve -comment "Mario Rossi - Sysadmin" \
  -email "mario.rossi@azienda.it" -firstname "Mario" -lastname "Rossi"
pveum passwd mario.rossi@pve

# Creare gruppo
pveum group add team-infrastruttura -comment "Team Infrastruttura IT"
pveum user modify mario.rossi@pve -groups team-infrastruttura

# Creare pool risorse
pveum pool add pool-produzione -comment "VM di produzione"
# Aggiungere VM al pool (da GUI oppure via API)

# Assegnare permessi
pveum acl modify /pool/pool-produzione -group team-infrastruttura -role PVEVMAdmin
pveum acl modify /nodes/pve01 -user mario.rossi@pve -role PVEAdmin
pveum acl modify / -group auditors -role PVEAuditor
```

### 2.4 API Tokens

```bash
# Creare token con privilegi separati
pveum user token add mario.rossi@pve automation -privsep 1 \
  -comment "Token per automazione Terraform"
# Output: token_id e secret -> salvare in vault sicuro

# Assegnare permessi specifici al token
pveum acl modify /vms -token 'mario.rossi@pve!automation' -role PVEVMAdmin

# Uso del token
curl -H "Authorization: PVEAPIToken=mario.rossi@pve!automation=UUID-TOKEN-HERE" \
  https://pve01:8006/api2/json/nodes
```

### 2.5 Two-Factor Authentication (2FA)

```bash
# Abilitare TOTP per utente (da CLI)
pveum user modify mario.rossi@pve -totp "type=totp,step=30,digits=6"

# Forzare 2FA per realm
pveum realm modify pve -tfa type=totp

# Supporta anche:
# - TOTP (Google Authenticator, Authy)
# - WebAuthn/FIDO2 (YubiKey)
# - Recovery keys
```

**Matrice RBAC consigliata per progetto migrazione:**

```
+---------------------+------------------+---------+----------+---------+
| Ruolo Progetto      | Realm            | Role PVE| Scope    | 2FA     |
+---------------------+------------------+---------+----------+---------+
| Project Manager     | ad               | Auditor | /        | TOTP    |
| Migration Engineer  | pve              | Custom  | /vms,/st | TOTP    |
| Sysadmin Senior     | pam              | Admin   | /        | WebAuthn|
| Operatore           | pve              | VMUser  | /pool/*  | TOTP    |
| Auditor esterno     | pve              | Auditor | /        | TOTP    |
| Automazione         | pve (token)      | Custom  | /vms     | N/A     |
+---------------------+------------------+---------+----------+---------+
```

---

## 3. Integrazione LDAP/Active Directory

### 3.1 Configurazione AD Realm

Via CLI:

```bash
pveum realm add azienda.local -type ad \
  -domain azienda.local \
  -server1 dc01.azienda.local \
  -server2 dc02.azienda.local \
  -port 636 \
  -secure 1 \
  -default 0 \
  -base_dn "DC=azienda,DC=local" \
  -user_attr sAMAccountName \
  -bind_dn "CN=svc-proxmox,OU=Service Accounts,DC=azienda,DC=local" \
  -comment "Active Directory Aziendale" \
  -tfa type=totp
```

File risultante `/etc/pve/domains.cfg`:

```
ad: azienda.local
    base_dn DC=azienda,DC=local
    bind_dn CN=svc-proxmox,OU=Service Accounts,DC=azienda,DC=local
    comment Active Directory Aziendale
    domain azienda.local
    port 636
    secure 1
    server1 dc01.azienda.local
    server2 dc02.azienda.local
    tfa type=totp
    user_attr sAMAccountName
```

### 3.2 Group Sync

```bash
# Sincronizzare gruppi AD
pveum realm sync azienda.local --scope both --enable-new 0

# Mappare gruppi AD a permessi Proxmox
pveum group add ad-admins -comment "Mapped from AD Domain Admins"
pveum acl modify / -group ad-admins -role PVEAdmin

pveum group add ad-operators -comment "Mapped from AD IT-Operators"
pveum acl modify /pool/pool-produzione -group ad-operators -role PVEVMUser
```

### 3.3 LDAPS e Certificati

```bash
# Importare CA certificate aziendale
cp azienda-ca.crt /usr/local/share/ca-certificates/
update-ca-certificates

# Verificare connessione LDAPS
openssl s_client -connect dc01.azienda.local:636 -CApath /etc/ssl/certs
ldapsearch -H ldaps://dc01.azienda.local:636 \
  -D "CN=svc-proxmox,OU=Service Accounts,DC=azienda,DC=local" \
  -W -b "DC=azienda,DC=local" "(sAMAccountName=testuser)"
```

**Diagramma flusso autenticazione:**

```
+--------+     +----------+     +-----------+     +------+
| Utente |---->| PVE GUI  |---->| pvedaemon |---->|  AD  |
| browser|     | :8006    |     | auth check|     | LDAPS|
+--------+     +----------+     +-----------+     +------+
                                      |                |
                                      |<-- user found -|
                                      |                |
                                +-----v------+
                                | RBAC check |
                                | /etc/pve/  |
                                | user.cfg   |
                                +-----+------+
                                      |
                                +-----v------+
                                | 2FA verify |
                                | TOTP/FIDO2 |
                                +------------+
```

---

## 4. Certificati SSL/TLS

### 4.1 Let's Encrypt con ACME

```bash
# Registrare account ACME
pvenode acme account register default admin@azienda.it --directory \
  https://acme-v02.api.letsencrypt.org/directory

# Configurare plugin DNS (esempio Cloudflare)
pvenode acme plugin add dns cloudflare-plugin --type dns \
  --data "CF_Token=il-tuo-api-token" --api cf

# Ordinare certificato
pvenode config set --acme domains=pve01.azienda.it
pvenode acme cert order

# Verificare
pvenode acme cert info
openssl x509 -in /etc/pve/nodes/pve01/pveproxy-ssl.pem -noout -dates
```

Rinnovo automatico via systemd timer (gia' incluso in Proxmox):

```bash
systemctl status pve-daily-update.timer
# Il timer esegue pvenode acme cert renew quotidianamente
```

### 4.2 CA Custom Aziendale

```bash
# Posizionare certificati
cp azienda-chain.pem /etc/pve/nodes/pve01/pveproxy-ssl.pem
cp azienda-key.pem /etc/pve/nodes/pve01/pveproxy-ssl.key
chmod 640 /etc/pve/nodes/pve01/pveproxy-ssl.key

# Riavviare proxy
systemctl restart pveproxy

# Distribuire CA ai client
cp azienda-ca.crt /usr/local/share/ca-certificates/
update-ca-certificates
```

### 4.3 Automazione Rinnovo (CA Custom)

Script `/usr/local/bin/renew-pve-cert.sh`:

```bash
#!/bin/bash
CERT_DIR="/etc/pve/nodes/$(hostname)"
DAYS_BEFORE=30

EXPIRY=$(openssl x509 -in "$CERT_DIR/pveproxy-ssl.pem" -noout -enddate | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
NOW_EPOCH=$(date +%s)
DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))

if [ "$DAYS_LEFT" -lt "$DAYS_BEFORE" ]; then
    # Richiedere nuovo certificato (adattare al sistema CA aziendale)
    /usr/local/bin/request-cert.sh "$CERT_DIR"
    systemctl restart pveproxy
    echo "Certificato rinnovato. Giorni rimanenti erano: $DAYS_LEFT" | \
      mail -s "PVE Cert Renewed on $(hostname)" admin@azienda.it
fi
```

---

## 5. Audit Logging

### 5.1 Log Nativi Proxmox

| File/Sorgente | Contenuto | Rotazione |
|---------------|-----------|-----------|
| `/var/log/pveproxy/access.log` | Accessi GUI/API | logrotate |
| `/var/log/pve/tasks/` | Task asincroni (migrate, backup) | Automatica |
| `/var/log/syslog` | Eventi sistema, auth, cluster | logrotate |
| `/var/log/auth.log` | Autenticazione SSH e PAM | logrotate |
| `/var/log/daemon.log` | pvedaemon, pveproxy events | logrotate |
| `/var/log/pve-firewall.log` | Dropped packets firewall PVE | logrotate |
| Journalctl | Tutti i servizi systemd | journald |

```bash
# Consultare task recenti
pvesh get /cluster/tasks --limit 50

# Log di uno specifico task
cat /var/log/pve/tasks/A/B/UPID

# Filtrare eventi autenticazione
journalctl -u pvedaemon --since "1 hour ago" | grep -i auth
```

### 5.2 Centralizzazione con Loki + Grafana

Installare Promtail su ogni nodo PVE - `/etc/promtail/config.yml`:

```yaml
server:
  http_listen_port: 9080

positions:
  filename: /var/lib/promtail/positions.yaml

clients:
  - url: http://loki.monitoring.local:3100/loki/api/v1/push

scrape_configs:
  - job_name: proxmox-syslog
    static_configs:
      - targets: [localhost]
        labels:
          job: proxmox
          host: pve01
          __path__: /var/log/syslog

  - job_name: proxmox-auth
    static_configs:
      - targets: [localhost]
        labels:
          job: proxmox-auth
          host: pve01
          __path__: /var/log/auth.log

  - job_name: proxmox-access
    static_configs:
      - targets: [localhost]
        labels:
          job: proxmox-access
          host: pve01
          __path__: /var/log/pveproxy/access.log

  - job_name: proxmox-firewall
    static_configs:
      - targets: [localhost]
        labels:
          job: proxmox-fw
          host: pve01
          __path__: /var/log/pve-firewall.log
```

### 5.3 Cosa Monitorare (Security Events)

| Evento | Sorgente | Severita' | Alert |
|--------|----------|-----------|-------|
| Login fallito GUI | daemon.log | WARNING | >5 in 10 min |
| Login fallito SSH | auth.log | WARNING | >3 in 5 min |
| Nuovo utente creato | pvedaemon | INFO | Sempre |
| Permessi modificati | pvedaemon | WARNING | Sempre |
| VM eliminata | task log | CRITICAL | Sempre |
| Firewall rule cambiata | pvedaemon | WARNING | Sempre |
| Certificato in scadenza | cronjob | WARNING | <30 giorni |
| Root login | auth.log | CRITICAL | Sempre |
| Storage quasi pieno | metrics | WARNING | >85% |

---

## 6. Network Isolation

### 6.1 Architettura VLAN Segmentata

```
+------------------------------------------------------------------+
|                     PROXMOX HOST (pve01)                         |
|                                                                  |
|  vmbr0 (Management)    vmbr1 (VM Traffic)    vmbr2 (Storage)    |
|  VLAN 100               Trunk               VLAN 200            |
|  10.0.100.0/24          VLAN 10,20,30,40    10.0.200.0/24       |
|                                                                  |
+------+------------------+-------------------+--------------------+
       |                  |                   |
       |            +-----+------+            |
       |            |  Switch L3 |            |
       |            +-----+------+            |
       |                  |                   |
       |     +------------+------------+      |
       |     |            |            |      |
       | VLAN 10     VLAN 20     VLAN 30     |
       | Produzione  DMZ         Sviluppo    |
       | 10.10.0/24  10.20.0/24  10.30.0/24  |
+------+-----+------+----+------+-----+------+----+
| Trust Zone: |  HIGH |   MEDIUM  |    LOW    | STORAGE |
+--------------+------+-----------+-----------+---------+
```

### 6.2 Configurazione VLAN in Proxmox

File `/etc/network/interfaces`:

```bash
auto lo
iface lo inet loopback

# Physical NIC - trunk
auto eno1
iface eno1 inet manual

# Management bridge - VLAN 100
auto vmbr0
iface vmbr0 inet static
    address 10.0.100.11/24
    gateway 10.0.100.1
    bridge-ports eno1.100
    bridge-stp off
    bridge-fd 0

# VM traffic bridge - trunk
auto vmbr1
iface vmbr1 inet manual
    bridge-ports eno1
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    bridge-vids 10 20 30 40

# Storage bridge - VLAN 200 (dedicata, no VM access)
auto eno2
iface eno2 inet manual

auto vmbr2
iface vmbr2 inet static
    address 10.0.200.11/24
    bridge-ports eno2.200
    bridge-stp off
    bridge-fd 0
```

### 6.3 Proxmox Firewall (Micro-Segmentazione)

Cluster level `/etc/pve/firewall/cluster.fw`:

```ini
[OPTIONS]
enable: 1
policy_in: DROP
policy_out: ACCEPT
log_ratelimit: enable=1,rate=1/second,burst=5

[RULES]
# Management SSH
IN ACCEPT -source 10.0.100.0/24 -dest +management -p tcp -dport 22 -log info
# Web GUI
IN ACCEPT -source 10.0.100.0/24 -dest +management -p tcp -dport 8006 -log info
# Corosync cluster
IN ACCEPT -source 10.0.100.0/24 -p udp -dport 5405:5412
# Live migration
IN ACCEPT -source 10.0.100.0/24 -p tcp -dport 60000:60050
# Ceph
IN ACCEPT -source 10.0.200.0/24 -p tcp -dport 6789
IN ACCEPT -source 10.0.200.0/24 -p tcp -dport 6800:7300

[IPSET management]
10.0.100.11
10.0.100.12
10.0.100.13
```

VM-level firewall (per singola VM):

```ini
[OPTIONS]
enable: 1
policy_in: DROP
dhcp: 0
ipfilter: 1
macfilter: 1

[RULES]
# Web server - accetta solo HTTP/HTTPS dalla DMZ
IN ACCEPT -source 10.20.0.0/24 -p tcp -dport 80,443
# SSH solo da management
IN ACCEPT -source 10.0.100.0/24 -p tcp -dport 22
# ICMP limitato
IN ACCEPT -p icmp -log nolog
```

### 6.4 Trust Zones

| Zona | VLAN | Scopo | Accesso consentito |
|------|------|-------|-------------------|
| Management | 100 | Admin, cluster | Solo admin IP |
| Produzione | 10 | VM produzione | Inter-VLAN controllato |
| DMZ | 20 | Servizi esposti | Internet in, limitato out |
| Sviluppo | 30 | Test e dev | Isolato da produzione |
| Storage | 200 | Ceph/NFS/iSCSI | Solo nodi PVE |
| Backup | 210 | PBS | Solo nodi PVE + PBS |

---

## 7. Compliance GDPR e ISO 27001

### 7.1 GDPR - Requisiti per la Migrazione

| Requisito GDPR | Implementazione Proxmox |
|----------------|------------------------|
| Art. 5 - Localizzazione dati | VM con dati personali su storage/nodi in UE; documentare datacenter |
| Art. 25 - Privacy by design | Template VM hardened, crittografia default, VLAN isolamento |
| Art. 30 - Registro trattamenti | Inventario VM con classificazione dati nel CMDB |
| Art. 32 - Sicurezza trattamento | Encryption at rest (LUKS/ZFS), in transit (TLS), RBAC |
| Art. 33 - Notifica data breach | Monitoring, alert, procedure incident response |
| Art. 35 - DPIA | Valutazione impatto prima della migrazione |

**Encryption at Rest:**

```bash
# ZFS encryption (dataset level)
zfs create -o encryption=aes-256-gcm -o keyformat=passphrase rpool/encrypted-vms

# LUKS per LVM-thin
cryptsetup luksFormat /dev/sdb1
cryptsetup open /dev/sdb1 encrypted-data
pvcreate /dev/mapper/encrypted-data
vgcreate vg-encrypted /dev/mapper/encrypted-data
lvcreate -l 100%FREE -T vg-encrypted/thin-pool
```

### 7.2 ISO 27001 - Mapping Controlli

| Controllo ISO 27001 | Implementazione |
|---------------------|-----------------|
| A.5 - Information security policies | Documentazione hardening, policy RBAC |
| A.6 - Organization | RACI matrix, ruoli e responsabilita' |
| A.8 - Asset management | Inventario VM/host, classificazione |
| A.9 - Access control | RBAC, 2FA, LDAP, API tokens |
| A.10 - Cryptography | TLS 1.3, LUKS/ZFS encryption, cert management |
| A.12 - Operations security | Logging, monitoring, change management |
| A.13 - Communications security | VLAN, firewall, VPN |
| A.14 - System acquisition | Hardening template, vulnerability scanning |
| A.16 - Incident management | Alert, escalation, runbook |
| A.17 - Business continuity | HA cluster, backup PBS, DR plan |
| A.18 - Compliance | Audit trail, GDPR mapping, review periodiche |

### 7.3 Audit Trail durante la Migrazione

```bash
# Script per logging strutturato di ogni migrazione
#!/bin/bash
LOG_FILE="/var/log/migration-audit/$(date +%Y%m%d)_migration.log"

log_migration_event() {
    local VMID=$1 ACTION=$2 STATUS=$3 OPERATOR=$4 NOTES=$5
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)|$VMID|$ACTION|$STATUS|$OPERATOR|$NOTES" \
      >> "$LOG_FILE"
}

# Utilizzo
log_migration_event "VM-100" "EXPORT_START" "OK" "mario.rossi" "Exported from ESXi 7.0"
log_migration_event "VM-100" "IMPORT_COMPLETE" "OK" "mario.rossi" "Imported to pve01"
log_migration_event "VM-100" "VALIDATION" "OK" "mario.rossi" "All checks passed"
```

---

## 8. Vulnerability Scanning e Patching

### 8.1 Lynis Audit

```bash
apt install lynis -y
lynis audit system --quick

# Report dettagliato
lynis audit system > /var/log/lynis-audit-$(date +%Y%m%d).log

# Aree critiche da verificare
lynis show details FIRE-4513  # Firewall
lynis show details SSH-7408   # SSH config
lynis show details AUTH-9286  # Password policy
```

**Score target post-hardening: >= 80/100**

### 8.2 Gestione Aggiornamenti

```bash
# Repository Proxmox (enterprise vs no-subscription)
cat /etc/apt/sources.list.d/pve-enterprise.list
# deb https://enterprise.proxmox.com/debian/pve bookworm pve-enterprise

# Verificare aggiornamenti disponibili
apt update && apt list --upgradable

# Aggiornamento rolling (nodo per nodo nel cluster)
# 1. Migrare VM dal nodo
pvesh create /nodes/pve01/migrateall --target pve02
# 2. Aggiornare
apt dist-upgrade -y
# 3. Riavviare se necessario (kernel update)
pve-efiboot-tool refresh  # per sistemi EFI
reboot
# 4. Verificare stato cluster
pvecm status
```

### 8.3 Workflow Patching in Cluster

```
+----------+     +---------+     +---------+
|  pve01   |     |  pve02  |     |  pve03  |
|  (patch) |     | (attivo)|     | (attivo)|
+----+-----+     +----+----+     +----+----+
     |                |               |
 1. Migrate VMs out   |               |
 2. apt upgrade       |               |
 3. Reboot            |               |
 4. Verify health     |               |
 5. Migrate VMs back  |               |
     |                |               |
     |           6. Migrate VMs out   |
     |           7. apt upgrade       |
     |           8. Reboot            |
     |           9. Verify            |
     |           10. Migrate back     |
     |                |               |
     |                |          11. Repeat
     |                |          12-15. Same
```

### 8.4 CVE Tracking

```bash
# Monitorare CVE per Proxmox/QEMU/kernel
# Feed RSS: https://security-tracker.debian.org/tracker/

# Script controllo CVE
apt install debsecan -y
debsecan --suite bookworm --only-fixed  # CVE con fix disponibile
```

---

## 9. Confronto Sicurezza VMware vs Proxmox

### 9.1 Tabella Comparativa

| Area | VMware vSphere | Proxmox VE |
|------|---------------|------------|
| **Autenticazione** | vCenter SSO, AD/LDAP, SAML | PAM, PVE, AD/LDAP, OpenID Connect |
| **2FA** | RSA SecurID, Smart Card | TOTP, WebAuthn/FIDO2, Recovery keys |
| **RBAC** | Ruoli granulari predefiniti + custom | Ruoli custom, path-based ACL |
| **Encryption at Rest** | vSAN Encryption, VM Encryption (vTPM) | LUKS, ZFS encryption |
| **Encryption in Transit** | vMotion encryption nativo | SSH tunnel, TLS (manuale per live migration) |
| **Firewall** | NSX micro-segmentazione (costo aggiuntivo) | Firewall integrato, nftables (incluso) |
| **Audit Log** | vRealize Log Insight (licenza separata) | Syslog, journald, integrazione Loki (gratuito) |
| **Vulnerability scan** | Carbon Black (acquisizione) | Lynis, OpenVAS, debsecan (open source) |
| **Certificati** | VMCA integrata | ACME/Let's Encrypt integrato |
| **Hardening guide** | DISA STIG ufficiale | Community guide, CIS parziale |
| **CVE History** | CVE frequenti su vCenter (log4j, etc.) | Superficie di attacco minore, CVE QEMU/kernel |
| **Costo sicurezza** | NSX + vRealize = costo significativo | Tutti gli strumenti inclusi/open source |

### 9.2 Gap Analysis e Mitigazioni

| Gap Proxmox vs VMware | Mitigazione |
|----------------------|-------------|
| No STIG ufficiale | Applicare CIS Debian + hardening custom documentato |
| No vTPM nativo equivalente | LUKS + swtpm (emulato, in miglioramento) |
| No vMotion encryption nativo | SSH tunnel per migration, VLAN dedicata |
| Meno audit trail strutturato | Loki/ELK + script logging custom |
| No NSX equivalente | PVE firewall + OPNsense/pfSense VM per advanced |
| No built-in IDS/IPS | Suricata/Snort su bridge, Wazuh agent |

### 9.3 Checklist Sicurezza Pre-Go-Live

```
[ ] SSH hardened (chiavi, no root password, fail2ban)
[ ] Sysctl hardened (network, kernel)
[ ] Firewall PVE abilitato (cluster + VM level)
[ ] RBAC configurato (ruoli, utenti, gruppi)
[ ] 2FA abilitato per tutti gli utenti admin
[ ] LDAP/AD integrato con LDAPS
[ ] Certificati SSL validi su tutti i nodi
[ ] Logging centralizzato operativo
[ ] Monitoring + alerting attivo
[ ] VLAN segmentazione verificata
[ ] Encryption at rest per storage sensibili
[ ] Unattended upgrades configurato
[ ] Lynis score >= 80
[ ] Backup encryption abilitata su PBS
[ ] Documentazione sicurezza aggiornata
[ ] Penetration test schedulato
```

---

## Riferimenti

- Proxmox VE Administration Guide - Security: https://pve.proxmox.com/pve-docs/
- CIS Debian Benchmark: https://www.cisecurity.org/benchmark/debian_linux
- GDPR Testo ufficiale: https://eur-lex.europa.eu/eli/reg/2016/679/oj
- ISO/IEC 27001:2022: https://www.iso.org/standard/27001
- Proxmox Forum Security: https://forum.proxmox.com/forums/proxmox-ve-security/

---

## Esercizi

1. **Concettuale — gap analysis security.** Per un'infrastruttura migrata da VMware, fai un assessment in 15-20 punti su: cert TLS, MFA, RBAC, network isolation, audit log, patch management. Per ognuno, indica gap-frequente e azione di rimedio.

2. **Lab — applicare CIS Benchmark Debian a Proxmox.** Scaricare il CIS Debian 12 Benchmark, scegliere 10 controlli prioritari (es. SSH hardening, kernel sysctl, audit log persistente), applicarli a un nodo Proxmox di test, validare che il cluster funzioni ancora.

3. **Stretch — SIEM integration.** Configurare un Wazuh manager (free) e installare l'agent su un nodo Proxmox; configurare le rules per detection di: login falliti, modifiche a `/etc/pve/`, esecuzione di `qm migrate` non schedulata.

## Auto-valutazione

1. Quali sono le 6 layer del defense-in-depth applicate a Proxmox?
2. Cos'e CIS Debian Benchmark e come applicarlo a Proxmox?
3. GDPR data residency: cosa significa e impatto su Proxmox cluster multi-region?
4. Network isolation: quali VLAN minime per produzione?
5. Audit logging: cosa raccogliere e dove inviarlo?
6. Patch management Proxmox: subscription Enterprise vs No-Subscription, differenze.

## Letture primarie consigliate

- Proxmox VE Administration Guide — Security. https://pve.proxmox.com/pve-docs/ (retrieved 2026-04-27).
- CIS Debian Linux Benchmark. https://www.cisecurity.org/benchmark/debian_linux (retrieved 2026-04-27).
- GDPR Regulation (EU) 2016/679. https://eur-lex.europa.eu/eli/reg/2016/679/oj (retrieved 2026-04-27).
- ISO/IEC 27001:2022. https://www.iso.org/standard/27001 (retrieved 2026-04-27).
- NIST SP 800-53 Rev 5 — Security and Privacy Controls. https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final (retrieved 2026-04-27).
- Wazuh — Open Source SIEM. https://wazuh.com/platform/ (retrieved 2026-04-27).

## Collegamenti incrociati

- Modulo 12.1 — `certificati-ssl-tls-proxmox.md`: TLS layer.
- Modulo 12.2 — `autenticazione-ldap-ad-proxmox.md`: auth + RBAC.
- Modulo 11.2 — `../11-BACKUP-E-RIPRISTINO-PROXMOX/proxmox-backup-server-configurazione.md`: encryption backup.

## Glossario locale

| Termine | Definizione |
|---|---|
| **CIS Benchmark** | Linee guida hardening del Center for Internet Security. |
| **Defense in depth** | Architettura security multi-layer. |
| **Network isolation** | Separazione VLAN per ridurre blast radius. |
| **Microsegmentation** | Firewall L4 a livello di singolo guest. |
| **AIDE** | Advanced Intrusion Detection Environment; file integrity. |
| **`auditd`** | Linux audit daemon per syscall logging. |
| **SIEM** | Security Information and Event Management. |
| **Wazuh** | Open-source SIEM/HIDS. |
| **GDPR** | EU regulation 2016/679 sulla protezione dati. |
| **HIPAA** | US legislation per dati sanitari. |
| **PCI-DSS** | Payment Card Industry Data Security Standard. |
| **ISO 27001** | Standard internazionale ISMS (Information Security Management System). |
| **DPIA** | Data Protection Impact Assessment (GDPR Art. 35). |
| **Scope reduction (PCI)** | Limitare i sistemi soggetti a PCI per ridurre cost compliance. |
