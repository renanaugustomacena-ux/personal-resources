# Tutorial Linux 19 — Servizi di Rete: DNS, DHCP, NFS, Samba, SMTP

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** bind9/unbound DNS, dnsmasq DHCP, NFS v4, Samba SMB, Postfix SMTP
> **Prerequisiti:** `tutorial_linux_05_networking.md`, `tutorial_linux_04_systemd.md`
> **Durata stimata:** 14-16 ore

---

## Mappa concettuale

```
Servizi di Rete Linux
│
├── DNS
│   ├── bind9 — autoritativo/ricorsivo
│   ├── unbound — resolver cache
│   └── dnsmasq — tutto-in-uno (piccole reti)
│
├── DHCP
│   ├── isc-dhcp-server
│   └── dnsmasq DHCP
│
├── File Sharing
│   ├── NFS v4 (Linux → Linux)
│   └── Samba (Linux → Windows/Mac)
│
├── Email
│   ├── Postfix — MTA
│   └── Dovecot — IMAP/POP3
│
└── Monitoraggio servizi
    ├── systemd checks
    └── netstat / ss per porte
```

---

# Parte A — DNS

---

## A1. dnsmasq: DNS + DHCP leggero

```bash
# Ideale per reti home, VM lab, container
apt install dnsmasq

# /etc/dnsmasq.conf
cat > /etc/dnsmasq.conf << 'EOF'
# Interfaccia su cui ascoltare
interface=eth0
bind-interfaces

# Non usare /etc/resolv.conf
no-resolv

# Upstream DNS
server=1.1.1.1
server=8.8.8.8

# Cache
cache-size=1000
neg-ttl=300

# Dominio locale
domain=lab.interno
local=/lab.interno/

# Record statici
address=/server1.lab.interno/10.0.0.10
address=/server2.lab.interno/10.0.0.11
address=/nas.lab.interno/10.0.0.20

# PTR (reverse lookup)
ptr-record=10.0.0.10.in-addr.arpa,server1.lab.interno

# DHCP
dhcp-range=10.0.0.100,10.0.0.200,24h
dhcp-option=option:router,10.0.0.1
dhcp-option=option:dns-server,10.0.0.1

# DHCP statico per MAC
dhcp-host=aa:bb:cc:dd:ee:ff,server3,10.0.0.30

# Log
log-queries
log-facility=/var/log/dnsmasq.log
EOF

systemctl enable --now dnsmasq

# Test
dig @10.0.0.1 server1.lab.interno
nslookup server2.lab.interno 10.0.0.1
```

---

## A2. unbound: resolver cache ricorsivo

```bash
# Per reti aziendali che usano resolver caching locale
apt install unbound

cat > /etc/unbound/unbound.conf.d/locale.conf << 'EOF'
server:
    interface: 0.0.0.0
    port: 53
    do-ip4: yes
    do-ip6: no
    do-tcp: yes
    do-udp: yes
    
    # Forza root hints
    root-hints: "/etc/unbound/root.hints"
    
    # Sicurezza
    hide-identity: yes
    hide-version: yes
    
    # DNSSEC
    auto-trust-anchor-file: "/var/lib/unbound/root.key"
    
    # Cache
    cache-max-ttl: 86400
    cache-min-ttl: 0
    num-threads: 2
    
    # Rete locale — non vai su internet
    private-address: 10.0.0.0/8
    private-address: 172.16.0.0/12
    private-address: 192.168.0.0/16
    
    # Zona locale
    local-zone: "lab.interno." static
    local-data: "server1.lab.interno. A 10.0.0.10"
    local-data: "server2.lab.interno. A 10.0.0.11"
    local-data-ptr: "10.0.0.10 server1.lab.interno"

# Forward to upstream
forward-zone:
    name: "."
    forward-addr: 1.1.1.1
    forward-addr: 8.8.8.8
EOF

# Scarica root hints
wget -O /etc/unbound/root.hints https://www.internic.net/domain/named.root

systemctl enable --now unbound

# Test
dig @127.0.0.1 google.com
unbound-control status
```

---

> **Analogia:** DNS è come la rubrica telefonica di internet — trasforma nomi leggibili (google.com) in indirizzi IP numerici. Un resolver cache come unbound è come un segretario che ricorda i numeri già cercati per rispondere subito alla prossima volta. Un server autoritativo (bind9) è come la rubrica stessa — contiene le informazioni originali.

---

# Parte B — NFS v4

---

## B1. Server NFS

```bash
# Server
apt install nfs-kernel-server

# /etc/exports — definisce cosa esportare
cat > /etc/exports << 'EOF'
# /percorso_locale  client(opzioni)

# Solo lettura per tutti sulla rete
/var/www/contenuto  10.0.0.0/24(ro,sync,no_subtree_check)

# Lettura/scrittura per client specifico
/home/condiviso     10.0.0.10(rw,sync,no_root_squash,no_subtree_check)

# NFS v4 — usa auth Kerberos (ideale produzione)
/mnt/dati           *(rw,sync,no_subtree_check,sec=krb5p)

# root_squash (default) = root del client → nfsnobody
# no_root_squash = root client ha root su server (PERICOLO!)
# no_subtree_check = migliori performance, meno sicurezza
EOF

# Applica modifiche
exportfs -arv
# exporting 10.0.0.0/24:/var/www/contenuto
# exporting 10.0.0.10:/home/condiviso

# Verifica
showmount -e localhost
exportfs -v

systemctl enable --now nfs-kernel-server
```

```bash
# Client
apt install nfs-common

# Mount temporaneo
mount -t nfs4 10.0.0.1:/home/condiviso /mnt/nfs-home

# Mount permanente in /etc/fstab
echo "10.0.0.1:/home/condiviso  /mnt/nfs-home  nfs4  rw,sync,_netdev,nofail  0 0" >> /etc/fstab
mount -a

# Opzioni client utili
# rw = lettura/scrittura
# ro = sola lettura
# sync = scrittura sincrona (più lento ma sicuro)
# async = scrittura asincrona (più veloce, rischio dati persi)
# hard = riprova indefinitamente se server irraggiungibile
# soft = fallisce dopo timeout
# _netdev = monta dopo la rete
# nofail = boot continua anche senza il mount

# Verifica mount
df -h /mnt/nfs-home
mount | grep nfs
```

---

# Parte C — Samba

---

## C1. Samba: file sharing con Windows/Mac

```bash
# Installazione
apt install samba samba-common smbclient

# /etc/samba/smb.conf
cat > /etc/samba/smb.conf << 'EOF'
[global]
    workgroup = WORKGROUP
    server string = File Server Linux
    netbios name = linuxserver
    security = user
    
    # Versioni SMB supportate
    server min protocol = SMB2
    server max protocol = SMB3
    
    # Sicurezza
    smb encrypt = desired    # auto-negozia crittografia
    guest account = nobody
    map to guest = bad user
    
    # Log
    log file = /var/log/samba/log.%m
    log level = 1

[dati-condivisi]
    comment = Dati aziendali condivisi
    path = /srv/samba/dati
    browseable = yes
    read only = no
    valid users = @smbusers
    create mask = 0664
    directory mask = 0775
    force group = smbusers

[home-utenti]
    comment = Home utenti
    path = /home/%S
    browseable = no
    read only = no
    valid users = %S
    create mask = 0600
    directory mask = 0700

[pubblico]
    comment = Cartella pubblica (sola lettura)
    path = /srv/samba/pubblico
    browseable = yes
    read only = yes
    guest ok = yes
EOF

# Crea directory
mkdir -p /srv/samba/{dati,pubblico}
groupadd smbusers
chown root:smbusers /srv/samba/dati
chmod 2770 /srv/samba/dati

# Crea utente Samba (deve esistere anche come utente Linux)
useradd -M -s /usr/sbin/nologin mario
smbpasswd -a mario       # imposta password Samba
smbpasswd -e mario       # abilita utente
usermod -aG smbusers mario

# Verifica configurazione
testparm

# Avvia
systemctl enable --now smbd nmbd

# Test locale
smbclient //localhost/dati -U mario
```

```bash
# Client Linux
# Mount share Samba
mount -t cifs //10.0.0.1/dati /mnt/samba \
    -o username=mario,password=PASSWORD,vers=3.0

# In /etc/fstab con credentials file (non in chiaro)
echo "username=mario" > /etc/.samba-creds
echo "password=SEGRETO" >> /etc/.samba-creds
chmod 600 /etc/.samba-creds

echo "//10.0.0.1/dati  /mnt/samba  cifs  credentials=/etc/.samba-creds,vers=3.0,_netdev  0 0" >> /etc/fstab
```

---

# Parte D — Postfix (invio email)

---

## D1. Postfix relay SMTP

```bash
# Postfix configurato come relay (invia email via provider SMTP)
apt install postfix libsasl2-modules

# /etc/postfix/main.cf — configurazione principale
postconf -e "relayhost = [smtp.gmail.com]:587"
postconf -e "smtp_use_tls = yes"
postconf -e "smtp_sasl_auth_enable = yes"
postconf -e "smtp_sasl_security_options = noanonymous"
postconf -e "smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd"
postconf -e "smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt"

# Credenziali SMTP
echo "[smtp.gmail.com]:587 utente@gmail.com:APP-PASSWORD" > /etc/postfix/sasl_passwd
postmap /etc/postfix/sasl_passwd
chmod 600 /etc/postfix/sasl_passwd{,.db}

systemctl restart postfix

# Test invio
echo "Test email da $(hostname)" | mail -s "Test" admin@esempio.it
# Verifica coda
mailq

# Log
tail -f /var/log/mail.log
```

---

# Parte E — Riepilogo

## Porte standard servizi

| Servizio | Porta | Protocollo |
|---|---|---|
| DNS | 53 | UDP/TCP |
| DHCP server | 67 | UDP |
| DHCP client | 68 | UDP |
| NFS | 2049 | TCP/UDP |
| SMB/Samba | 445 | TCP |
| SMTP | 25, 587 (submission) | TCP |
| IMAP | 143, 993 (SSL) | TCP |
| POP3 | 110, 995 (SSL) | TCP |

## Verifica servizi attivi

```bash
# Quali servizi ascoltano su quali porte?
ss -tulpn

# Verifica configurazione
testparm              # Samba
exportfs -v           # NFS
named-checkconf       # BIND9
unbound-checkconf     # Unbound
postfix check         # Postfix
dnsmasq --test        # dnsmasq
```

## Prossimi passi

- `tutorial_linux_20_monitoring.md` — Prometheus + Grafana + alerting
- `tutorial_linux_32_vpn.md` — WireGuard e OpenVPN
