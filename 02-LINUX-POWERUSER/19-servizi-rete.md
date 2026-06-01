# Servizi di Rete Linux — Guida Completa

> **Modulo 19** · **Aggiornamento:** 2026-05-22

## Idee guida
1. **DNS: BIND9 (authoritative + recursive), Unbound (recursive puro), dnsmasq (reti piccole).**
2. **DHCP: ISC dhcpd legacy con failover; Kea è il successore moderno con backend database.**
3. **Mail: Postfix > sendmail; Dovecot per IMAP; opendkim + opendmarc + SPF per email authentication.**
4. **NFS v4.2 only; v3 legacy. Kerberos per autenticazione. autofs per mount on-demand.**
5. **Samba: membro Active Directory, file sharing, stampa. Non usare come DC primario in produzione.**
6. **LDAP: OpenLDAP + sssd per autenticazione centralizzata. Sempre TLS, mai LDAP in chiaro.**
7. **NTP: chrony > ntpd per la maggior parte dei casi. NTS per sicurezza tempo.**
8. **Proxy: Squid per caching HTTP. Mai intercettare HTTPS senza policy chiare e consenso.**
9. **RADIUS: FreeRADIUS per 802.1X e autenticazione rete enterprise.**
10. **VPN: WireGuard per semplicità, OpenVPN per compatibilità legacy.**


## Indice

- [Panoramica](#panoramica)
- [DNS: BIND9](#dns-bind9)
  - [Installazione e file di configurazione](#installazione-e-file-di-configurazione)
  - [Zone autoritativa](#zone-autoritativa)
  - [Zone file forward e reverse](#zone-file-forward-e-reverse)
  - [Server DNS secondario (slave)](#server-dns-secondario-slave)
  - [TSIG — Autenticazione trasferimenti zona](#tsig--autenticazione-trasferimenti-zona)
  - [Forwarders e recursion](#forwarders-e-recursion)
  - [Split-Horizon DNS (Views)](#split-horizon-dns-views)
  - [DNSSEC](#dnssec)
  - [Logging avanzato BIND9](#logging-avanzato-bind9)
  - [BIND9 — DNS over TLS (DoT)](#bind9-dot)
- [DNS: Unbound (Recursive Resolver)](#dns-unbound-recursive-resolver)
  - [Unbound — Servire DNS-over-TLS e DNS-over-HTTPS](#unbound-dot-doh)
- [DNS: dnsmasq](#dns-dnsmasq)
- [DNS: CoreDNS](#dns-coredns)
  - [Installazione standalone](#installazione-standalone)
  - [Corefile — Configurazione modulare](#corefile--configurazione-modulare)
  - [Zone file e registrazione servizi in etcd](#zone-file-e-registrazione-servizi-in-etcd)
- [DHCP Server (ISC dhcpd)](#dhcp-server-isc-dhcpd)
  - [Configurazione base](#configurazione-base-dhcp)
  - [Reservations e opzioni avanzate](#reservations-e-opzioni-avanzate)
  - [DHCP Failover](#dhcp-failover)
  - [DHCP Relay Agent](#dhcp-relay-agent)
- [DHCP Server: Kea](#dhcp-server-kea)
  - [Kea HA — Configurazione High Availability](#kea-ha)
  - [Kea — Hooks avanzati (2.6+)](#kea-hooks-avanzati)
  - [Kea DDNS — Aggiornamento DNS dinamico](#kea-ddns)
  - [Kea Stork — Interfaccia di gestione](#kea-stork)
- [NTP: chrony vs ntpd](#ntp-chrony-vs-ntpd)
  - [Chrony — Configurazione completa](#chrony--configurazione-completa)
  - [ntpd — Configurazione e confronto](#ntpd--configurazione-e-confronto)
  - [Gerarchia Stratum](#gerarchia-stratum)
  - [NTS — Network Time Security](#nts--network-time-security)
  - [Chrony come server NTS](#chrony-nts-server)
  - [Monitoraggio NTP](#monitoraggio-ntp)
- [FTP: vsftpd e SFTP](#ftp-vsftpd-e-sftp)
  - [SFTP via OpenSSH](#sftp-via-openssh)
  - [vsftpd — Configurazione completa](#vsftpd--configurazione-completa)
  - [Utenti virtuali vsftpd](#utenti-virtuali-vsftpd)
- [Samba](#samba)
  - [Samba come membro Active Directory](#samba-come-membro-active-directory)
  - [File sharing](#file-sharing-samba)
  - [Servizi di stampa](#servizi-di-stampa-samba)
  - [Controllo accessi e permessi](#controllo-accessi-e-permessi-samba)
  - [Performance tuning Samba](#performance-tuning-samba)
- [NFS — Network File System](#nfs--network-file-system)
  - [NFSv4 — Configurazione server](#nfsv4--configurazione-server)
  - [NFSv4 — Configurazione client](#nfsv4--configurazione-client)
  - [NFS con Kerberos](#nfs-con-kerberos)
  - [Performance tuning NFS](#performance-tuning-nfs)
  - [Automount con autofs](#automount-con-autofs)
- [LDAP: OpenLDAP](#ldap-openldap)
  - [Installazione e configurazione iniziale](#installazione-e-configurazione-iniziale-ldap)
  - [Schema e struttura directory](#schema-e-struttura-directory)
  - [ACL — Access Control Lists](#acl--access-control-lists)
  - [Replicazione (syncrepl)](#replicazione-syncrepl)
  - [Integrazione client con sssd](#integrazione-client-con-sssd)
- [Mail: Postfix e Dovecot](#mail-postfix-e-dovecot)
  - [Postfix — Configurazione completa](#postfix--configurazione-completa)
  - [TLS per Postfix](#tls-per-postfix)
  - [SPF, DKIM, DMARC](#spf-dkim-dmarc)
  - [Dovecot — IMAP/POP3](#dovecot--imappop3)
  - [Spam filtering](#spam-filtering)
- [Proxy Server: Squid](#proxy-server-squid)
  - [Configurazione base Squid](#configurazione-base-squid)
  - [Transparent proxy](#transparent-proxy)
  - [Caching](#caching-squid)
  - [ACL Squid](#acl-squid)
  - [HTTPS e considerazioni di sicurezza](#https-e-considerazioni-di-sicurezza)
- [RADIUS: FreeRADIUS](#radius-freeradius)
  - [Installazione e configurazione](#installazione-e-configurazione-radius)
  - [Integrazione 802.1X](#integrazione-8021x)
- [VPN: WireGuard e OpenVPN](#vpn-wireguard-e-openvpn)
  - [WireGuard — Topologie avanzate](#wireguard-avanzato)
  - [WireGuard — wg-easy (gestione via Web UI)](#wg-easy)
- [mDNS e Avahi](#mdns-e-avahi)
- [Strumenti di troubleshooting rete](#strumenti-di-troubleshooting-rete)
- [Matrice decisionale servizi di rete](#matrice-decisionale-servizi-di-rete)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## Panoramica

I servizi di rete sono l'infrastruttura fondamentale di qualsiasi ambiente IT: DNS per la risoluzione nomi, DHCP per l'assegnazione automatica degli IP, NTP per la sincronizzazione oraria, LDAP per l'autenticazione centralizzata, mail per la comunicazione, FTP/SFTP per il trasferimento file. L'amministratore Linux deve saper installare, configurare e gestire questi servizi, ma anche comprendere come interagiscono tra loro: un Kerberos non funziona senza NTP sincronizzato, un mail server non consegna senza DNS corretto, un file server Samba non autentica senza LDAP o AD.

Questo modulo copre ogni servizio in profondità, dalla configurazione base al tuning di produzione, passando per sicurezza, alta disponibilità e troubleshooting.

**Prerequisiti**: networking di base (modulo 05), firewall (modulo 11), systemd (modulo 04), SSH (modulo 10).

---

## DNS: BIND9

BIND9 (Berkeley Internet Name Domain) è il server DNS più diffuso al mondo. Supporta zone autoritativa, recursion, DNSSEC, views (split-horizon) e trasferimenti zona autenticati con TSIG.

### Installazione e file di configurazione

```bash
# Installazione su Debian/Ubuntu
sudo apt install bind9 bind9-utils bind9-dnsutils

# Su RHEL/Fedora
sudo dnf install bind bind-utils

# File di configurazione principali
/etc/bind/named.conf                      # Config principale (include gli altri)
/etc/bind/named.conf.options              # Opzioni globali (forwarders, recursion, etc.)
/etc/bind/named.conf.local                # Definizione zone locali
/etc/bind/named.conf.default-zones        # Zone di default (localhost, reverse, root hints)
/var/cache/bind/                          # Directory per zone file dinamiche
/etc/bind/zones/                          # Directory consigliata per zone file statiche

# Utente e permessi
# BIND gira come utente 'bind' in un chroot opzionale
ls -la /etc/bind/
# I file zona devono essere leggibili dall'utente bind
```

### Zone autoritativa

```bash
# /etc/bind/named.conf.options — configurazione globale
options {
    directory "/var/cache/bind";

    # Interfacce su cui ascoltare
    listen-on { any; };
    listen-on-v6 { any; };

    # Chi può fare query
    allow-query { 10.0.0.0/8; 192.168.0.0/16; 172.16.0.0/12; localhost; };

    # Forwarders — DNS upstream per risoluzioni non locali
    forwarders {
        9.9.9.9;         # Quad9 (con DNSSEC validation)
        149.112.112.112; # Quad9 secondario
    };

    # DNSSEC
    dnssec-validation auto;

    # Recursion — solo per client interni
    recursion yes;
    allow-recursion { 10.0.0.0/8; 192.168.0.0/16; 172.16.0.0/12; localhost; };

    # Trasferimenti zona — solo verso slave autorizzati
    allow-transfer { none; };

    # Sicurezza
    version "not available";          # Nasconde versione BIND
    minimal-responses yes;            # Riduce dimensione risposte

    # Rate limiting per mitigare amplification attacks
    rate-limit {
        responses-per-second 10;
        window 5;
    };
};

# /etc/bind/named.conf.local — definizione zone
zone "example.com" {
    type master;
    file "/etc/bind/zones/db.example.com";
    allow-transfer { 192.168.1.11; };      # Slave NS
    also-notify { 192.168.1.11; };         # Notifica slave su aggiornamento
    allow-update { none; };                # No dynamic updates
};

zone "1.168.192.in-addr.arpa" {
    type master;
    file "/etc/bind/zones/db.192.168.1";
    allow-transfer { 192.168.1.11; };
    also-notify { 192.168.1.11; };
};
```

### Zone file forward e reverse

```bash
# /etc/bind/zones/db.example.com — Forward Zone
$TTL    86400
@       IN      SOA     ns1.example.com. admin.example.com. (
                        2026052201 ; Serial (YYYYMMDDNN) — INCREMENTARE ad ogni modifica
                        3600       ; Refresh — slave controlla ogni ora
                        1800       ; Retry — riprova dopo 30 min se refresh fallisce
                        604800     ; Expire — slave smette di rispondere dopo 7 giorni
                        86400 )    ; Negative Cache TTL — cache risposta NXDOMAIN

; Name servers — OGNI zona DEVE avere almeno 2 NS
@       IN      NS      ns1.example.com.
@       IN      NS      ns2.example.com.

; A records — mappatura nome → IPv4
ns1     IN      A       192.168.1.10
ns2     IN      A       192.168.1.11
@       IN      A       192.168.1.100    ; example.com → 192.168.1.100
www     IN      A       192.168.1.100
mail    IN      A       192.168.1.20
db      IN      A       192.168.1.30
app     IN      A       192.168.1.40
ldap    IN      A       192.168.1.50
nfs     IN      A       192.168.1.60
proxy   IN      A       192.168.1.70

; AAAA records — mappatura nome → IPv6
ns1     IN      AAAA    fd00::10
www     IN      AAAA    fd00::100

; CNAME — alias (mai per MX o NS)
ftp     IN      CNAME   www.example.com.
webmail IN      CNAME   mail.example.com.
docs    IN      CNAME   www.example.com.

; MX — mail exchanger, priorità più bassa = preferito
@       IN      MX  10  mail.example.com.
@       IN      MX  20  mail-backup.example.com.

; TXT records
@       IN      TXT     "v=spf1 mx a ip4:192.168.1.20 ~all"
_dmarc  IN      TXT     "v=DMARC1; p=reject; rua=mailto:dmarc@example.com"

; SRV records — service discovery
_ldap._tcp      IN      SRV     0 100 389 ldap.example.com.
_kerberos._tcp  IN      SRV     0 100 88  kdc.example.com.

; CAA — Certification Authority Authorization
@       IN      CAA     0 issue "letsencrypt.org"
@       IN      CAA     0 iodef "mailto:security@example.com"
```

```bash
# /etc/bind/zones/db.192.168.1 — Reverse Zone (PTR)
$TTL    86400
@       IN      SOA     ns1.example.com. admin.example.com. (
                        2026052201
                        3600
                        1800
                        604800
                        86400 )

@       IN      NS      ns1.example.com.
@       IN      NS      ns2.example.com.

; PTR records — IP → nome (ultimo ottetto)
10      IN      PTR     ns1.example.com.
11      IN      PTR     ns2.example.com.
20      IN      PTR     mail.example.com.
30      IN      PTR     db.example.com.
40      IN      PTR     app.example.com.
50      IN      PTR     ldap.example.com.
100     IN      PTR     www.example.com.
```

```bash
# Verificare configurazione e zone
sudo named-checkconf                                            # Verifica sintassi config
sudo named-checkzone example.com /etc/bind/zones/db.example.com # Verifica zona forward
sudo named-checkzone 1.168.192.in-addr.arpa /etc/bind/zones/db.192.168.1  # Verifica reverse

sudo systemctl restart bind9
sudo rndc reload                           # Reload zone senza restart completo
sudo rndc reload example.com              # Reload singola zona

# Test risoluzione
dig @localhost example.com                 # Query A record
dig @localhost www.example.com A           # Query A record specifico
dig @localhost example.com MX              # Query MX
dig @localhost example.com ANY             # Tutti i record
dig @localhost -x 192.168.1.100           # Reverse lookup (PTR)
dig @localhost example.com AXFR            # Trasferimento zona completo (test)
dig @localhost example.com +dnssec        # Query con validazione DNSSEC
```

### Server DNS secondario (slave)

Un DNS secondario riceve copie delle zone dal primario tramite trasferimenti zona (AXFR/IXFR). Essenziale per ridondanza.

```bash
# Sul server SLAVE (ns2, 192.168.1.11)
# /etc/bind/named.conf.local
zone "example.com" {
    type slave;
    file "/var/cache/bind/db.example.com";      # File locale (scritto da BIND)
    masters { 192.168.1.10; };                  # IP del master
    allow-notify { 192.168.1.10; };             # Accetta NOTIFY dal master
};

zone "1.168.192.in-addr.arpa" {
    type slave;
    file "/var/cache/bind/db.192.168.1";
    masters { 192.168.1.10; };
    allow-notify { 192.168.1.10; };
};

# Sul server MASTER — assicurarsi di permettere il trasferimento:
# allow-transfer { 192.168.1.11; };
# also-notify { 192.168.1.11; };

# Verificare trasferimento
dig @192.168.1.11 example.com AXFR         # Test dal slave
sudo rndc retransfer example.com           # Forza retransfer sullo slave
```

### TSIG — Autenticazione trasferimenti zona

TSIG (Transaction Signature) autentica i trasferimenti zona tra master e slave usando una chiave condivisa HMAC, prevenendo zone transfer hijacking.

```bash
# Generare chiave TSIG
tsig-keygen -a hmac-sha256 transfer-key > /etc/bind/transfer.key

# Il file generato contiene:
# key "transfer-key" {
#     algorithm hmac-sha256;
#     secret "base64encodedkey==";
# };

# Copiare la stessa chiave su entrambi i server (master e slave)
# Usare scp o altro canale sicuro — MAI in chiaro

# Sul MASTER — /etc/bind/named.conf.local
include "/etc/bind/transfer.key";

zone "example.com" {
    type master;
    file "/etc/bind/zones/db.example.com";
    allow-transfer { key transfer-key; };      # Solo con chiave TSIG
    also-notify { 192.168.1.11; };
};

# Configurare anche il server clause per lo slave
server 192.168.1.11 {
    keys { transfer-key; };
};

# Sul SLAVE — /etc/bind/named.conf.local
include "/etc/bind/transfer.key";

zone "example.com" {
    type slave;
    file "/var/cache/bind/db.example.com";
    masters { 192.168.1.10 key transfer-key; };
};

# Permessi sul file chiave
sudo chown root:bind /etc/bind/transfer.key
sudo chmod 640 /etc/bind/transfer.key
```

### Forwarders e recursion

```bash
# Tre modalità di risoluzione BIND9:

# 1. Authoritative only — risponde solo per zone locali
options {
    recursion no;
    allow-query { any; };          # Chiunque può interrogare zone autoritative
};

# 2. Recursive resolver — risolve tutto per client autorizzati
options {
    recursion yes;
    allow-recursion { 10.0.0.0/8; localhost; };
    forwarders { };                # Nessun forwarder = risoluzione iterativa diretta
};

# 3. Forwarding resolver — inoltra query a upstream
options {
    recursion yes;
    allow-recursion { 10.0.0.0/8; localhost; };
    forwarders { 9.9.9.9; 149.112.112.112; };
    forward only;                  # "only" = usa solo forwarders
                                   # "first" = prova forwarders, poi risolvi direttamente
};

# ACL per organizzare le reti
acl "internal" {
    10.0.0.0/8;
    192.168.0.0/16;
    172.16.0.0/12;
    localhost;
};

options {
    allow-query { "internal"; };
    allow-recursion { "internal"; };
};
```

### Split-Horizon DNS (Views)

Split-horizon DNS serve risposte diverse a client interni ed esterni. Esempio: `www.example.com` → IP privato per interni, IP pubblico per esterni.

```bash
# /etc/bind/named.conf.local con views

acl "internal-nets" {
    10.0.0.0/8;
    192.168.0.0/16;
    172.16.0.0/12;
    127.0.0.0/8;
};

# Vista interna — serve prima, match per client interni
view "internal" {
    match-clients { "internal-nets"; };
    match-destinations { any; };

    # Recursion disponibile per interni
    recursion yes;
    allow-query { any; };

    zone "example.com" {
        type master;
        file "/etc/bind/zones/internal/db.example.com";
    };

    zone "1.168.192.in-addr.arpa" {
        type master;
        file "/etc/bind/zones/internal/db.192.168.1";
    };

    # Include zone di default per vista interna
    include "/etc/bind/named.conf.default-zones";
};

# Vista esterna — per tutti gli altri
view "external" {
    match-clients { any; };
    match-destinations { any; };

    # No recursion per esterni
    recursion no;

    zone "example.com" {
        type master;
        file "/etc/bind/zones/external/db.example.com";
    };
};

# Zone file interna — IP privati
# /etc/bind/zones/internal/db.example.com
www     IN      A       192.168.1.100    # IP privato
app     IN      A       192.168.1.40
mail    IN      A       192.168.1.20

# Zone file esterna — IP pubblici
# /etc/bind/zones/external/db.example.com
www     IN      A       203.0.113.100    # IP pubblico
mail    IN      A       203.0.113.20
```

**Attenzione**: con le views attive, **tutte** le zone devono essere dentro una view. Non si possono avere zone dentro e fuori le views contemporaneamente.

### DNSSEC

DNSSEC aggiunge firme crittografiche ai record DNS, prevenendo spoofing e cache poisoning. Il processo prevede: generare chiavi, firmare la zona, pubblicare i record DS nel dominio padre.

```bash
# Creare directory per le chiavi
sudo mkdir -p /etc/bind/keys
cd /etc/bind/keys

# 1. Generare Zone Signing Key (ZSK) — firma i record
sudo dnssec-keygen -a ECDSAP256SHA256 -n ZONE example.com
# Genera: Kexample.com.+013+NNNNN.key e .private

# 2. Generare Key Signing Key (KSK) — firma le chiavi (più forte)
sudo dnssec-keygen -a ECDSAP256SHA256 -n ZONE -f KSK example.com
# Genera: Kexample.com.+013+MMMMM.key e .private

# 3. Includere le chiavi pubbliche nel zone file
# Aggiungere alla fine di /etc/bind/zones/db.example.com:
$INCLUDE "/etc/bind/keys/Kexample.com.+013+NNNNN.key"
$INCLUDE "/etc/bind/keys/Kexample.com.+013+MMMMM.key"

# 4. Firmare la zona
sudo dnssec-signzone -A -3 $(head -c 1000 /dev/urandom | sha1sum | cut -b 1-16) \
    -N INCREMENT -o example.com -t \
    /etc/bind/zones/db.example.com

# Produce: db.example.com.signed

# 5. Aggiornare named.conf.local per usare la zona firmata
zone "example.com" {
    type master;
    file "/etc/bind/zones/db.example.com.signed";
    auto-dnssec maintain;          # Manutenzione automatica firme
    inline-signing yes;            # Firma inline (BIND 9.9+)
    key-directory "/etc/bind/keys";
};

# 6. Ricaricare
sudo rndc reload

# 7. Pubblicare il record DS presso il registrar
# Estrarre il DS record dal file dsset-example.com. generato
cat dsset-example.com.
# Copiare il record DS nel pannello del registrar del dominio

# Verificare DNSSEC
dig @localhost example.com +dnssec
dig example.com +dnssec +short
# Deve mostrare flag "ad" (Authenticated Data)

# Verificare catena di trust
delv @localhost example.com
# Deve mostrare "fully validated"

# Rotazione chiavi (ogni 3-6 mesi per ZSK, 1-2 anni per KSK)
# Procedura: pre-publish nuova chiave → attendere propagazione → firmare con nuova → rimuovere vecchia
```

### Logging avanzato BIND9

```bash
# /etc/bind/named.conf — sezione logging
logging {
    channel query_log {
        file "/var/log/bind/query.log" versions 5 size 50m;
        severity info;
        print-time yes;
        print-category yes;
        print-severity yes;
    };

    channel security_log {
        file "/var/log/bind/security.log" versions 5 size 20m;
        severity dynamic;
        print-time yes;
        print-severity yes;
    };

    channel xfer_log {
        file "/var/log/bind/xfer.log" versions 3 size 10m;
        severity info;
        print-time yes;
    };

    category queries { query_log; };
    category security { security_log; };
    category xfer-in { xfer_log; };
    category xfer-out { xfer_log; };
    category dnssec { security_log; };
};

# Creare directory log e assegnare permessi
sudo mkdir -p /var/log/bind
sudo chown bind:bind /var/log/bind

# Abilitare query logging temporaneamente (debug)
sudo rndc querylog on
# Disabilitare
sudo rndc querylog off

# Statistiche
sudo rndc stats
cat /var/cache/bind/named.stats
```

### BIND9 — DNS over TLS (DoT) {#bind9-dot}

A partire da BIND 9.18+, il supporto DNS-over-TLS è nativo. Il server può accettare query DNS crittografate sulla porta 853, proteggendo la privacy delle query tra client e resolver (o tra resolver e autoritativo).

```bash
# Prerequisito: certificato TLS valido (Let's Encrypt o PKI interna)
# I file devono essere leggibili dall'utente bind

# In /etc/bind/named.conf, aggiungere un blocco tls e il listener DoT:

tls local-tls {
    cert-file "/etc/letsencrypt/live/dns.example.com/fullchain.pem";
    key-file "/etc/letsencrypt/live/dns.example.com/privkey.pem";
    # Protocolli minimi raccomandati
    protocols { TLSv1.3; };
    # Cipher suite — lasciare vuoto per default sicuri di OpenSSL 3.x
    # oppure specificare esplicitamente:
    # ciphers "TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256";
};

# Listener DoT sulla porta 853
options {
    // ... opzioni esistenti ...

    listen-on port 853 tls local-tls { any; };
    listen-on-v6 port 853 tls local-tls { any; };
};

# Firewall — aprire porta 853 TCP
sudo ufw allow 853/tcp comment "DNS-over-TLS"

# Verificare che BIND ascolti su 853
sudo ss -tlnp | grep ':853'

# Test da client con kdig (pacchetto knot-dnsutils)
kdig @dns.example.com +tls example.com A
# oppure con dog:
# dog example.com A @dns.example.com --tls

# Monitoring — controllare handshake TLS
sudo rndc status | grep -i tls

# BIND 9.20+ aggiunge anche supporto DNS-over-HTTPS (DoH) nativo:
# listen-on port 443 tls local-tls http local-http { any; };
# http local-http {
#     endpoints { "/dns-query"; };
# };
```

**Considerazioni operative DoT/DoH su BIND9**: il certificato TLS deve essere rinnovato automaticamente (certbot con hook `rndc reload`). In ambienti con elevato traffico, il TLS handshake aggiunge latenza al primo pacchetto — considerare session resumption e TLS 1.3 0-RTT. Per resolver interni, un certificato da CA privata è sufficiente purché i client abbiano il CA root nel trust store.

---

## DNS: Unbound (Recursive Resolver)

Unbound è un resolver DNS ricorsivo, validante DNSSEC, ottimizzato per performance e sicurezza. Non è un server autoritativo — per quello usare BIND9 o Knot DNS.

```bash
# Installazione
sudo apt install unbound

# /etc/unbound/unbound.conf
server:
    # Interfacce di ascolto
    interface: 0.0.0.0
    interface: ::0
    port: 53

    # Accesso
    access-control: 10.0.0.0/8 allow
    access-control: 192.168.0.0/16 allow
    access-control: 172.16.0.0/12 allow
    access-control: 127.0.0.0/8 allow
    access-control: 0.0.0.0/0 refuse

    # DNSSEC — validazione automatica con root trust anchor
    auto-trust-anchor-file: "/var/lib/unbound/root.key"
    val-clean-additional: yes

    # Performance
    num-threads: 4                     # Numero CPU core
    msg-cache-size: 128m              # Cache risposte
    rrset-cache-size: 256m            # Cache resource record sets
    cache-min-ttl: 300                # TTL minimo cache (5 minuti)
    cache-max-ttl: 86400              # TTL massimo cache (24 ore)
    prefetch: yes                     # Pre-fetch record prima che scadano
    prefetch-key: yes                 # Pre-fetch chiavi DNSSEC

    # Sicurezza
    hide-identity: yes
    hide-version: yes
    harden-glue: yes
    harden-dnssec-stripped: yes
    use-caps-for-id: yes              # DNS 0x20 encoding per anti-spoofing
    qname-minimisation: yes           # Riduce info inviate ai server upstream

    # Logging
    verbosity: 1
    log-queries: no                   # Abilitare solo per debug
    logfile: "/var/log/unbound/unbound.log"

    # Blocco DNS (ad-blocking)
    # include: /etc/unbound/blocklist.conf

    # Zone locali
    private-domain: "example.lan"
    local-zone: "example.lan." static
    local-data: "server1.example.lan. IN A 192.168.1.10"
    local-data: "server2.example.lan. IN A 192.168.1.11"
    local-data-ptr: "192.168.1.10 server1.example.lan"
    local-data-ptr: "192.168.1.11 server2.example.lan"

# Forward zone — inoltra a server autoritativo interno per domini interni
forward-zone:
    name: "example.com"
    forward-addr: 192.168.1.10       # BIND9 autoritativo interno

# Forward zone opzionale — DNS upstream con TLS (DoT)
forward-zone:
    name: "."
    forward-tls-upstream: yes
    forward-addr: 9.9.9.9@853#dns.quad9.net
    forward-addr: 149.112.112.112@853#dns.quad9.net

# Verificare configurazione
sudo unbound-checkconf

# Gestione
sudo systemctl enable --now unbound
sudo unbound-control status
sudo unbound-control stats_noreset         # Statistiche senza reset
sudo unbound-control dump_cache            # Dump cache
sudo unbound-control flush example.com     # Flush singolo dominio
sudo unbound-control flush_zone example.com # Flush intera zona dalla cache

# Aggiornare root hints
sudo wget -O /etc/unbound/root.hints https://www.internic.net/domain/named.cache
# Aggiungere in unbound.conf:
# server:
#     root-hints: "/etc/unbound/root.hints"
```

**Quando usare Unbound vs BIND9**: Unbound è ideale come resolver ricorsivo puro (client-facing, caching). BIND9 è necessario quando serve anche funzionalità autoritativa. I due possono coesistere: BIND9 autoritativo per zone interne, Unbound come resolver che inoltra a BIND9 per domini interni e risolve direttamente per tutto il resto.

### Unbound — Servire DNS-over-TLS e DNS-over-HTTPS {#unbound-dot-doh}

Unbound supporta nativamente la ricezione di query DNS-over-TLS (DoT) dai client. Per DNS-over-HTTPS (DoH), dalla versione 1.21+ è supportato il listener HTTPS nativo, oppure si usa un proxy come `dnsproxy` di AdGuard.

```bash
# === DoT — DNS-over-TLS nativo (porta 853) ===
# In /etc/unbound/unbound.conf, sezione server:

server:
    # Listener standard (porta 53, non crittografato)
    interface: 0.0.0.0@53
    interface: ::0@53

    # Listener DoT (porta 853, crittografato)
    interface: 0.0.0.0@853
    interface: ::0@853
    tls-port: 853

    # Certificato TLS — stesso formato di qualsiasi servizio TLS
    tls-service-key: "/etc/unbound/tls/server.key"
    tls-service-pem: "/etc/unbound/tls/server.pem"

    # Ciphers — TLS 1.3 raccomandato
    tls-ciphersuites: "TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256"

    # Opzionale: upstream forwarding via DoT (client → Unbound → upstream DoT)
    # forward-zone:
    #     name: "."
    #     forward-tls-upstream: yes
    #     forward-addr: 1.1.1.1@853#cloudflare-dns.com
    #     forward-addr: 9.9.9.9@853#dns.quad9.net

# Firewall
sudo ufw allow 853/tcp comment "Unbound DNS-over-TLS"

# Test da client
kdig @resolver.example.com +tls example.com A

# === DoH — DNS-over-HTTPS via dnsproxy ===
# Per versioni Unbound < 1.21 senza DoH nativo

# Installare dnsproxy (binario Go, nessuna dipendenza)
wget https://github.com/AdguardTeam/dnsproxy/releases/latest/download/dnsproxy-linux-amd64-*.tar.gz
tar xzf dnsproxy-linux-amd64-*.tar.gz
sudo mv dnsproxy /usr/local/bin/

# dnsproxy ascolta DoH sulla 443, inoltra a Unbound locale sulla 53
sudo dnsproxy \
    --listen 0.0.0.0 \
    --port 443 \
    --https-port 443 \
    --tls-crt /etc/unbound/tls/server.pem \
    --tls-key /etc/unbound/tls/server.key \
    --upstream 127.0.0.1:53

# Creare un servizio systemd per dnsproxy in produzione
# Test DoH
curl -s -H 'accept: application/dns-json' \
    'https://resolver.example.com/dns-query?name=example.com&type=A'
```

**Nota sulla scelta DoT vs DoH**: DoT usa una porta dedicata (853) ed è facilmente filtrabile/monitorabile da firewall aziendali. DoH usa la porta 443, indistinguibile dal traffico HTTPS — più difficile da bloccare ma anche da controllare. In ambienti enterprise, preferire DoT per mantenere visibilità. Per utenti finali su reti non fidate, DoH offre migliore resistenza alla censura.

---

## DNS: dnsmasq

dnsmasq è un server DNS/DHCP leggero, ideale per reti piccole e medie, ambienti di sviluppo e reti virtuali (libvirt, Docker).

```bash
sudo apt install dnsmasq

# /etc/dnsmasq.conf
# --- DNS ---
listen-address=127.0.0.1,192.168.1.1
port=53
domain=example.lan
expand-hosts                               # Aggiunge dominio a nomi in /etc/hosts
bogus-priv                                 # Non inoltra reverse query per reti private
domain-needed                              # Non inoltra nomi senza dominio

# Upstream DNS
server=9.9.9.9
server=149.112.112.112
strict-order                               # Usa server nell'ordine elencato

# DNS condizionale — dominio specifico verso DNS interno
server=/internal.corp/10.0.0.53
server=/1.168.192.in-addr.arpa/10.0.0.53

# Cache DNS
cache-size=10000
neg-ttl=3600                               # Cache risposte negative
local-ttl=300                              # TTL per record locali

# Host statici (alternativa a /etc/hosts)
address=/server1.example.lan/192.168.1.10
address=/server2.example.lan/192.168.1.11

# Blocco DNS (wildcard)
address=/ads.example.com/0.0.0.0           # Blocca dominio

# File hosts aggiuntivo
addn-hosts=/etc/dnsmasq.hosts

# --- DHCP integrato ---
dhcp-range=192.168.1.100,192.168.1.200,255.255.255.0,12h
dhcp-option=option:router,192.168.1.1
dhcp-option=option:dns-server,192.168.1.1
dhcp-option=option:domain-name,example.lan
dhcp-option=option:ntp-server,192.168.1.1

# Lease statici
dhcp-host=00:11:22:33:44:55,server1,192.168.1.10,infinite
dhcp-host=00:11:22:33:44:66,server2,192.168.1.11,infinite

# PXE boot
dhcp-boot=pxelinux.0,pxeserver,192.168.1.5

# Logging
log-queries                                # Log tutte le query DNS
log-dhcp                                   # Log DHCP leases
log-facility=/var/log/dnsmasq.log

sudo systemctl enable --now dnsmasq

# Verificare
dig @192.168.1.1 server1.example.lan
cat /var/lib/misc/dnsmasq.leases           # Lease DHCP attivi
```

---

## DNS: CoreDNS {#dns-coredns}

CoreDNS è un server DNS modulare scritto in Go, nato come progetto CNCF e usato come DNS cluster di default in Kubernetes. Fuori da Kubernetes, è eccellente per service discovery interna, ambienti dinamici e infrastrutture moderne dove i record cambiano frequentemente.

### Installazione standalone

```bash
# CoreDNS è un singolo binario Go — nessuna dipendenza
# Release: https://github.com/coredns/coredns/releases
COREDNS_VERSION="1.12.1"
wget https://github.com/coredns/coredns/releases/download/v${COREDNS_VERSION}/coredns_${COREDNS_VERSION}_linux_amd64.tgz
tar xzf coredns_${COREDNS_VERSION}_linux_amd64.tgz
sudo mv coredns /usr/local/bin/
sudo chmod +x /usr/local/bin/coredns

# Creare utente di servizio
sudo useradd -r -s /usr/sbin/nologin coredns

# Creare directory configurazione
sudo mkdir -p /etc/coredns /var/lib/coredns

# Unit systemd
sudo cat > /etc/systemd/system/coredns.service << 'UNIT'
[Unit]
Description=CoreDNS DNS Server
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
User=coredns
Group=coredns
ExecStart=/usr/local/bin/coredns -conf /etc/coredns/Corefile
Restart=on-failure
RestartSec=5
LimitNOFILE=65535
AmbientCapabilities=CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now coredns
```

### Corefile — Configurazione modulare

CoreDNS usa un file di configurazione chiamato **Corefile** con sintassi a blocchi (derivata da Caddy). Ogni blocco definisce una zona e i plugin attivi.

```bash
# /etc/coredns/Corefile

# === Zona autoritativa interna ===
example.lan {
    # Servire record da zone file standard (formato BIND)
    file /etc/coredns/zones/db.example.lan

    # Logging query
    log

    # Errori
    errors

    # Metriche Prometheus
    prometheus :9153
}

# === Zona reverse ===
168.192.in-addr.arpa {
    file /etc/coredns/zones/db.192.168
    log
    errors
}

# === Service discovery dinamica con etcd ===
# CoreDNS può leggere record DNS direttamente da etcd,
# ideale per ambienti dove i servizi si registrano dinamicamente
services.internal {
    etcd {
        # Endpoint etcd (supporta cluster multipli)
        endpoint http://127.0.0.1:2379

        # Path prefix in etcd — formato SkyDNS
        path /skydns

        # Fallback se etcd non risponde
        fallthrough
    }
    log
    errors
    prometheus :9153
}

# === Catch-all — forwarding per tutto il resto ===
. {
    # Forward a resolver upstream
    forward . 1.1.1.1 9.9.9.9 {
        # Health check
        health_check 30s
    }

    # Cache risposte (TTL rispettato)
    cache 300

    # Risposte loop detection
    loop

    # Metriche aggregate
    prometheus :9153

    # Reload automatico Corefile ogni 30s
    reload 30s

    log
    errors
}
```

### Zone file e registrazione servizi in etcd

```bash
# === Zone file classico (db.example.lan) ===
# /etc/coredns/zones/db.example.lan
$ORIGIN example.lan.
$TTL 3600
@   IN  SOA ns1.example.lan. admin.example.lan. (
        2026052401 ; serial
        3600       ; refresh
        900        ; retry
        604800     ; expire
        300        ; minimum TTL
    )
@       IN  NS  ns1.example.lan.
ns1     IN  A   192.168.1.10
web     IN  A   192.168.1.20
db      IN  A   192.168.1.30
api     IN  A   192.168.1.40
*.apps  IN  A   192.168.1.50      ; wildcard per applicazioni

# === Registrare servizi in etcd per service discovery ===
# Formato SkyDNS: /skydns/<dominio invertito>
# Per registrare api.services.internal → 192.168.1.40:8080

etcdctl put /skydns/internal/services/api \
    '{"host":"192.168.1.40","port":8080,"priority":10}'

etcdctl put /skydns/internal/services/db-primary \
    '{"host":"192.168.1.30","port":5432,"priority":10}'

# Record SRV automatici — i client possono interrogare:
dig @localhost SRV api.services.internal

# Aggiungere/rimuovere servizi = aggiornare etcd
# CoreDNS riflette le modifiche immediatamente, senza reload

# === Plugin auto — zone file automatiche ===
# Monitorare una directory per nuovi zone file
# auto {
#     directory /etc/coredns/zones
#     reload 10s
# }
```

**Quando usare CoreDNS vs alternative**: CoreDNS eccelle in ambienti dinamici (container, microservizi, Kubernetes). Per zone statiche tradizionali, BIND9 o Knot DNS sono più maturi. Per reti piccole con DHCP integrato, dnsmasq resta più pratico. CoreDNS è la scelta naturale quando serve service discovery DNS-based e i record cambiano frequentemente via API (etcd, Consul, o plugin personalizzati).

---

## DHCP Server (ISC dhcpd)

ISC DHCP è il server DHCP di riferimento storico. Sebbene EOL (End of Life dal 2022), è ancora ampiamente usato. Il successore è Kea DHCP (sezione successiva).

### Configurazione base {#configurazione-base-dhcp}

```bash
sudo apt install isc-dhcp-server

# /etc/dhcp/dhcpd.conf
authoritative;                             # Questo server è autoritativo per la subnet
default-lease-time 43200;                  # 12 ore
max-lease-time 86400;                      # 24 ore
min-lease-time 3600;                       # 1 ora minimo

# Opzioni globali
option domain-name "example.com";
option domain-name-servers 192.168.1.10, 192.168.1.11;
option ntp-servers 192.168.1.1;

# Logging
log-facility local7;

# Subnet principale
subnet 192.168.1.0 netmask 255.255.255.0 {
    range 192.168.1.100 192.168.1.200;
    option routers 192.168.1.1;
    option broadcast-address 192.168.1.255;
    option subnet-mask 255.255.255.0;

    # Opzioni specifiche subnet
    option domain-search "example.com", "internal.example.com";
}

# Subnet senza pool (solo lease statici)
subnet 192.168.2.0 netmask 255.255.255.0 {
    option routers 192.168.2.1;
}

# /etc/default/isc-dhcp-server
INTERFACESv4="eth0"
# INTERFACESv6="eth0"   # Se si usa DHCPv6

sudo systemctl enable --now isc-dhcp-server

# Verificare lease assegnati
cat /var/lib/dhcp/dhcpd.leases
dhcp-lease-list                            # Se disponibile
```

### Reservations e opzioni avanzate

```bash
# Lease statici (reservations) — IP fisso basato su MAC
host server-web {
    hardware ethernet 00:11:22:33:44:55;
    fixed-address 192.168.1.10;
    option host-name "server-web";
}

host server-db {
    hardware ethernet 00:11:22:33:44:66;
    fixed-address 192.168.1.30;
    option host-name "server-db";
    # Opzioni specifiche per questo host
    next-server 192.168.1.5;               # TFTP server per PXE
    filename "pxelinux.0";
}

# Gruppo di host con opzioni comuni
group {
    option domain-name-servers 10.0.0.53;
    next-server 192.168.1.5;

    host pxe-client-1 {
        hardware ethernet AA:BB:CC:DD:EE:01;
        fixed-address 192.168.1.201;
    }
    host pxe-client-2 {
        hardware ethernet AA:BB:CC:DD:EE:02;
        fixed-address 192.168.1.202;
    }
}

# Classi — assegnazione basata su vendor class
class "printers" {
    match if substring(option vendor-class-identifier, 0, 6) = "Hewlett";
}

subnet 192.168.1.0 netmask 255.255.255.0 {
    pool {
        allow members of "printers";
        range 192.168.1.220 192.168.1.230;
    }
    pool {
        deny members of "printers";
        range 192.168.1.100 192.168.1.200;
    }
}

# Opzioni DHCP personalizzate
option space custom;
option custom.tftp-server code 150 = ip-address;

# PXE boot avanzato (UEFI vs BIOS)
if option architecture-type = 00:07 {
    filename "grubx64.efi";                # UEFI
} else {
    filename "pxelinux.0";                 # BIOS legacy
}
```

### DHCP Failover

ISC DHCP supporta failover tra due server per alta disponibilità. Un solo pool è diviso tra primary e secondary.

```bash
# SERVER PRIMARIO — /etc/dhcp/dhcpd.conf
failover peer "dhcp-failover" {
    primary;
    address 192.168.1.10;                  # IP di questo server
    port 647;
    peer address 192.168.1.11;             # IP del peer
    peer port 647;
    max-response-delay 60;
    max-unacked-updates 10;
    load balance max seconds 3;
    mclt 3600;                             # Maximum Client Lead Time
    split 128;                             # 128/256 = 50% del pool
    auto-partner-down 3600;                # Assume controllo totale dopo 1h
}

subnet 192.168.1.0 netmask 255.255.255.0 {
    pool {
        failover peer "dhcp-failover";
        range 192.168.1.100 192.168.1.200;
    }
    option routers 192.168.1.1;
}

# SERVER SECONDARIO — /etc/dhcp/dhcpd.conf
failover peer "dhcp-failover" {
    secondary;
    address 192.168.1.11;
    port 647;
    peer address 192.168.1.10;
    peer port 647;
    max-response-delay 60;
    max-unacked-updates 10;
    load balance max seconds 3;
}

subnet 192.168.1.0 netmask 255.255.255.0 {
    pool {
        failover peer "dhcp-failover";
        range 192.168.1.100 192.168.1.200;
    }
    option routers 192.168.1.1;
}

# Firewall — aprire porta 647/TCP tra i due server
# Verificare stato failover
sudo dhcpd -t                              # Test configurazione
omshell                                    # Shell interattiva per gestione DHCP
```

### DHCP Relay Agent

Quando i client DHCP e il server DHCP sono su subnet diverse, serve un relay agent sul router.

```bash
# Installare relay agent
sudo apt install isc-dhcp-relay

# Configurazione — /etc/default/isc-dhcp-relay
SERVERS="192.168.1.10"                     # IP del DHCP server
INTERFACES="eth0 eth1 eth2"               # Interfacce su cui fare relay
OPTIONS="-id eth0 -iu eth1"               # Downstream/upstream interfaces

sudo systemctl enable --now isc-dhcp-relay

# Alternativa: relay integrato nel router
# Su router Linux con ip forwarding:
# Inoltra broadcast DHCP dall'interfaccia eth1 (subnet client) al server
```

---

## DHCP Server: Kea

Kea è il successore ufficiale di ISC DHCP. Moderno, performante, con backend database (MySQL, PostgreSQL), API REST di gestione, supporto HA integrato e configurazione JSON.

```bash
# Installazione
sudo apt install kea

# File di configurazione principali
/etc/kea/kea-dhcp4.conf                   # DHCPv4
/etc/kea/kea-dhcp6.conf                   # DHCPv6
/etc/kea/kea-ctrl-agent.conf              # Control Agent (API REST)
/etc/kea/kea-dhcp-ddns.conf               # Dynamic DNS updates

# /etc/kea/kea-dhcp4.conf — configurazione DHCPv4
{
    "Dhcp4": {
        # Interfacce di ascolto
        "interfaces-config": {
            "interfaces": [ "eth0" ],
            "dhcp-socket-type": "raw"
        },

        # Lease database — file o database
        "lease-database": {
            "type": "memfile",
            "persist": true,
            "name": "/var/lib/kea/kea-leases4.csv",
            "lfc-interval": 3600
        },

        # Oppure backend PostgreSQL:
        # "lease-database": {
        #     "type": "postgresql",
        #     "name": "kea",
        #     "host": "localhost",
        #     "port": 5432,
        #     "user": "kea",
        #     "password": "kea_password"
        # },

        # Parametri lease globali
        "valid-lifetime": 43200,
        "renew-timer": 21600,
        "rebind-timer": 36000,

        # Subnet
        "subnet4": [
            {
                "id": 1,
                "subnet": "192.168.1.0/24",
                "pools": [
                    { "pool": "192.168.1.100 - 192.168.1.200" }
                ],
                "option-data": [
                    { "name": "routers", "data": "192.168.1.1" },
                    { "name": "domain-name-servers", "data": "192.168.1.10, 192.168.1.11" },
                    { "name": "domain-name", "data": "example.com" },
                    { "name": "ntp-servers", "data": "192.168.1.1" }
                ],

                # Reservations (lease statici)
                "reservations": [
                    {
                        "hw-address": "00:11:22:33:44:55",
                        "ip-address": "192.168.1.10",
                        "hostname": "server-web"
                    },
                    {
                        "hw-address": "00:11:22:33:44:66",
                        "ip-address": "192.168.1.30",
                        "hostname": "server-db"
                    }
                ]
            }
        ],

        # Logging
        "loggers": [
            {
                "name": "kea-dhcp4",
                "output_options": [
                    { "output": "/var/log/kea/kea-dhcp4.log" }
                ],
                "severity": "INFO"
            }
        ]
    }
}

# Control Agent — API REST per gestione
# /etc/kea/kea-ctrl-agent.conf
{
    "Control-agent": {
        "http-host": "127.0.0.1",
        "http-port": 8000,
        "control-sockets": {
            "dhcp4": {
                "socket-type": "unix",
                "socket-name": "/run/kea/kea4-ctrl-socket"
            }
        }
    }
}

# Gestione servizi
sudo systemctl enable --now kea-dhcp4-server
sudo systemctl enable --now kea-ctrl-agent

# Interazione via API REST
curl -s -X POST http://localhost:8000/ \
    -H "Content-Type: application/json" \
    -d '{"command": "config-get", "service": ["dhcp4"]}' | python3 -m json.tool

curl -s -X POST http://localhost:8000/ \
    -d '{"command": "lease4-get-all", "service": ["dhcp4"]}' | python3 -m json.tool

curl -s -X POST http://localhost:8000/ \
    -d '{"command": "statistic-get-all", "service": ["dhcp4"]}' | python3 -m json.tool

# HA — High Availability (hook library)
# Richiede kea-hook-ha e configurazione su entrambi i nodi
# Kea HA supporta modalità: load-balancing, hot-standby, passive-backup
```

### Kea HA — Configurazione High Availability {#kea-ha}

Kea supporta tre modalità HA tramite la hook library `libdhcp_ha.so`. I nodi comunicano tra loro via REST API (Control Agent sulla porta 8000).

```json
// Configurazione HA hot-standby — Nodo primario
// In /etc/kea/kea-dhcp4.conf, sezione "hooks-libraries"
{
    "hooks-libraries": [
        {
            "library": "/usr/lib/x86_64-linux-gnu/kea/hooks/libdhcp_lease_cmds.so"
        },
        {
            "library": "/usr/lib/x86_64-linux-gnu/kea/hooks/libdhcp_ha.so",
            "parameters": {
                "high-availability": [
                    {
                        "this-server-name": "kea-primary",
                        "mode": "hot-standby",
                        "heartbeat-delay": 10000,
                        "max-response-delay": 60000,
                        "max-ack-delay": 10000,
                        "max-unacked-clients": 5,
                        "sync-timeout": 60000,
                        "peers": [
                            {
                                "name": "kea-primary",
                                "url": "http://192.168.1.10:8000/",
                                "role": "primary",
                                "auto-failover": true
                            },
                            {
                                "name": "kea-standby",
                                "url": "http://192.168.1.11:8000/",
                                "role": "standby",
                                "auto-failover": true
                            }
                        ]
                    }
                ]
            }
        }
    ]
}
```

```json
// Configurazione HA load-balancing — distribuzione carico attiva/attiva
// Differenze chiave rispetto a hot-standby:
{
    "high-availability": [
        {
            "this-server-name": "kea-node1",
            "mode": "load-balancing",
            "heartbeat-delay": 10000,
            "max-response-delay": 60000,
            "max-ack-delay": 10000,
            "max-unacked-clients": 5,
            "peers": [
                {
                    "name": "kea-node1",
                    "url": "http://192.168.1.10:8000/",
                    "role": "primary",
                    "auto-failover": true
                },
                {
                    "name": "kea-node2",
                    "url": "http://192.168.1.11:8000/",
                    "role": "secondary",
                    "auto-failover": true
                }
            ]
        }
    ]
}
// In load-balancing, entrambi i nodi rispondono attivamente.
// L'hash del MAC address del client determina quale nodo risponde.
// Se un nodo cade, l'altro gestisce il 100% del traffico.
```

### Kea — Hooks avanzati (2.6+) {#kea-hooks-avanzati}

Kea 2.6 introduce hook libraries aggiuntive per ambienti enterprise:

```bash
# === RADIUS Hook ===
# Autenticazione e accounting DHCP via RADIUS
# Utile per reti 802.1X dove il DHCP lease dipende dall'autenticazione
# In kea-dhcp4.conf:
# {
#     "library": "/usr/lib/x86_64-linux-gnu/kea/hooks/libdhcp_radius.so",
#     "parameters": {
#         "access": {
#             "servers": [
#                 { "name": "192.168.1.50", "port": 1812, "secret": "radiussecret" }
#             ]
#         },
#         "accounting": {
#             "servers": [
#                 { "name": "192.168.1.50", "port": 1813, "secret": "radiussecret" }
#             ]
#         }
#     }
# }

# === Ping Check Hook ===
# Verifica che un indirizzo IP sia libero prima di assegnarlo (ICMP ping)
# Previene conflitti IP — essenziale in reti migrate o con BYOD
# "library": "/usr/lib/x86_64-linux-gnu/kea/hooks/libdhcp_ping_check.so",
# "parameters": {
#     "min-ping-requests": 1,
#     "reply-timeout": 100,
#     "enable-ping-check": true
# }

# === Performance Monitoring Hook (Kea 2.6+) ===
# Raccolta metriche dettagliate per ogni fase della transazione DHCP
# Durata DORA (Discover-Offer-Request-Ack), latenza per subnet
# Esportazione via Kea Control Agent + Prometheus

# === Verificare hooks caricati ===
curl -s -X POST http://localhost:8000/ \
    -d '{"command": "list-commands", "service": ["dhcp4"]}' | python3 -m json.tool

# Stato HA
curl -s -X POST http://localhost:8000/ \
    -d '{"command": "ha-heartbeat", "service": ["dhcp4"]}' | python3 -m json.tool

# Sincronizzazione lease manuale
curl -s -X POST http://localhost:8000/ \
    -d '{"command": "ha-sync", "service": ["dhcp4"], "arguments": {"server-name": "kea-standby", "max-period": 60}}' \
    | python3 -m json.tool
```

### Kea DDNS — Aggiornamento DNS dinamico {#kea-ddns}

Il componente `kea-dhcp-ddns` aggiorna automaticamente i record DNS (forward e reverse) quando un lease viene assegnato o rilasciato. Funziona con BIND9, Knot DNS o qualsiasi server che supporti RFC 2136 (Dynamic DNS Update).

```json
// /etc/kea/kea-dhcp-ddns.conf
{
    "DhcpDdns": {
        "ip-address": "127.0.0.1",
        "port": 53001,
        "dns-server-timeout": 500,
        "forward-ddns": {
            "ddns-domains": [
                {
                    "name": "example.lan.",
                    "dns-servers": [
                        { "ip-address": "192.168.1.10", "port": 53 }
                    ]
                }
            ]
        },
        "reverse-ddns": {
            "ddns-domains": [
                {
                    "name": "1.168.192.in-addr.arpa.",
                    "dns-servers": [
                        { "ip-address": "192.168.1.10", "port": 53 }
                    ]
                }
            ]
        }
    }
}
```

```bash
# Abilitare DDNS nella configurazione Kea DHCPv4
# In kea-dhcp4.conf, aggiungere:
# "dhcp-ddns": {
#     "enable-updates": true,
#     "server-ip": "127.0.0.1",
#     "server-port": 53001,
#     "qualifying-suffix": "example.lan",
#     "override-client-update": true,
#     "replace-client-name": "when-not-present"
# }

# Avviare i servizi
sudo systemctl enable --now kea-dhcp-ddns
sudo systemctl restart kea-dhcp4-server
```

### Kea Stork — Interfaccia di gestione {#kea-stork}

Stork è la piattaforma di monitoring e gestione per Kea (e BIND9). Fornisce dashboard web, visualizzazione lease, stato HA, grafici utilizzo subnet e alerting.

```bash
# Installazione Stork Server (richiede PostgreSQL)
# Repository ISC
curl -1sLf 'https://dl.cloudsmith.io/public/isc/stork/setup.deb.sh' | sudo bash

sudo apt install isc-stork-server isc-stork-agent

# Stork Server — configurazione database
sudo su - postgres -c "createuser stork -P"
sudo su - postgres -c "createdb stork -O stork"

# Configurare /etc/stork/server.env
# STORK_DATABASE_HOST=localhost
# STORK_DATABASE_PORT=5432
# STORK_DATABASE_NAME=stork
# STORK_DATABASE_USER_NAME=stork
# STORK_DATABASE_PASSWORD=<password>

# Avviare
sudo systemctl enable --now isc-stork-server   # Web UI porta 8080
sudo systemctl enable --now isc-stork-agent    # Agente locale

# Stork Agent si registra automaticamente con il server
# Dashboard accessibile su http://<server>:8080
# Mostra: lease attivi, utilizzo pool, stato HA, host reservations, metriche

# Backend PostgreSQL per Kea (alternativa a memfile)
# In kea-dhcp4.conf:
# "lease-database": {
#     "type": "postgresql",
#     "host": "localhost",
#     "port": 5432,
#     "name": "kea",
#     "user": "kea",
#     "password": "keapassword"
# }
# PostgreSQL è raccomandato per installazioni >1000 lease o con requisiti HA
```

---

## NTP: chrony vs ntpd

La sincronizzazione oraria è critica per: correlazione log, Kerberos, TLS, database distribuiti, cluster.

### Chrony — Configurazione completa

Chrony è il client/server NTP raccomandato per Linux moderno. Più veloce di ntpd nella sincronizzazione iniziale, gestisce meglio salti di rete e macchine virtuali.

```bash
sudo apt install chrony

# /etc/chrony/chrony.conf — configurazione completa

# --- Sorgenti NTP ---
# Pool pubblici (iburst = sincronizza subito al primo contatto)
pool ntp.ubuntu.com iburst maxsources 4
pool 0.pool.ntp.org iburst maxsources 2
pool 1.pool.ntp.org iburst maxsources 2

# Server NTP specifico con parametri
server time.google.com iburst prefer    # "prefer" = sorgente preferita
server time.cloudflare.com iburst

# --- Comportamento come server NTP ---
# Permetti client da queste reti
allow 192.168.1.0/24
allow 10.0.0.0/8

# Serve orario anche se non sincronizzato con upstream
# (utile per reti isolate)
local stratum 10

# --- Sicurezza ---
# Limita accesso chronyc (gestione)
bindcmdaddress 127.0.0.1
bindcmdaddress ::1
cmdallow 127.0.0.1

# --- Performance ---
# Registra frequenza stimata per sincronizzazione rapida dopo reboot
driftfile /var/lib/chrony/chrony.drift

# Salva stato clock su shutdown
dumpdir /var/lib/chrony

# Aggiorna RTC (hardware clock) ogni 11 minuti
rtcsync

# --- Correzione tempo ---
# Permetti salto di tempo grande se offset > 1s nei primi 3 aggiornamenti
makestep 1 3

# Massimo rate di correzione (slew): 500 PPM
maxslewrate 500

# Minimo numero sorgenti prima di sincronizzare
minsources 2

# --- Logging ---
logdir /var/log/chrony
log measurements statistics tracking refclocks

# File con chiavi per autenticazione NTP
keyfile /etc/chrony/chrony.keys

# --- NTS (Network Time Security) ---
# Sorgente NTS (chrony 4.0+)
# server time.cloudflare.com iburst nts
# ntstrustedcerts /etc/ssl/certs/ca-certificates.crt

# Operazioni quotidiane
sudo systemctl enable --now chrony

chronyc tracking                           # Stato sincronizzazione dettagliato
chronyc sources -v                         # Sorgenti NTP con statistiche
chronyc sourcestats                        # Statistiche dettagliate sorgenti
chronyc activity                           # Numero sorgenti online/offline
chronyc makestep                           # Forza step immediato (se permesso)
chronyc ntpdata                            # Dati NTP dettagliati per sorgente
chronyc clients                            # Lista client serviti (se server)

# Stato sistema
timedatectl                                # Stato orario sistema
timedatectl set-ntp true                   # Abilita sincronizzazione NTP
timedatectl timezones                      # Lista timezone disponibili
timedatectl set-timezone Europe/Rome       # Imposta timezone
```

### ntpd — Configurazione e confronto

ntpd è il demone NTP classico, ancora usato in ambienti legacy o dove è richiesta compatibilità con hardware NTP dedicato.

```bash
sudo apt install ntp

# /etc/ntp.conf
# Sorgenti
pool 0.pool.ntp.org iburst
pool 1.pool.ntp.org iburst
server time.google.com iburst prefer

# Restrizioni accesso
restrict default kod nomodify notrap nopeer noquery
restrict 127.0.0.1
restrict ::1
restrict 192.168.1.0 mask 255.255.255.0 nomodify notrap

# Drift file
driftfile /var/lib/ntp/ntp.drift

# Logging
statsdir /var/log/ntp/
statistics loopstats peerstats clockstats
filegen loopstats file loopstats type day enable
filegen peerstats file peerstats type day enable

sudo systemctl enable --now ntp

# Comandi ntpd
ntpq -p                                   # Lista peer con statistiche
ntpq -c rv                                # Variabili sistema
ntpstat                                    # Stato sincronizzazione
ntpdate -q time.google.com               # Query senza sincronizzare
```

**Confronto chrony vs ntpd**:

| Caratteristica | chrony | ntpd |
|---|---|---|
| Sincronizzazione iniziale | Molto veloce | Lenta (minuti) |
| VM e container | Ottimo | Problematico |
| Reti intermittenti | Gestisce bene | Problematico |
| Memoria | Leggero | Più pesante |
| NTS (Network Time Security) | Sì (4.0+) | No |
| Hardware reference clock | Supportato | Supporto migliore |
| Broadcast/multicast NTP | Limitato | Supporto completo |
| Raccomandato da RHEL/Ubuntu | Sì | No (deprecato) |

**Raccomandazione**: usare chrony salvo necessità specifiche di ntpd (hardware clock dedicato, broadcast NTP legacy).

### Gerarchia Stratum

```
Stratum 0 — Orologi atomici, GPS, segnali radio (non direttamente accessibili via NTP)
    ↓
Stratum 1 — Server direttamente connessi a Stratum 0 (es. time.google.com)
    ↓
Stratum 2 — Server sincronizzati con Stratum 1 (es. pool NTP pubblici)
    ↓
Stratum 3 — Server sincronizzati con Stratum 2 (es. NTP server aziendale)
    ↓
...fino a Stratum 15 (massimo). Stratum 16 = non sincronizzato.
```

Per ambienti enterprise, configurare almeno 4 sorgenti upstream di Stratum 1 o 2 e un server NTP locale che serve come Stratum 3 per tutti i client interni.

### NTS — Network Time Security

NTS (RFC 8915) aggiunge autenticazione TLS al protocollo NTP, prevenendo attacchi man-in-the-middle sull'orario.

```bash
# Client NTS con chrony (4.0+)
# /etc/chrony/chrony.conf
server time.cloudflare.com iburst nts
server nts.ntp.se iburst nts

# Certificati trust
ntstrustedcerts /etc/ssl/certs/ca-certificates.crt

# Directory per cookie NTS
ntsdumpdir /var/lib/chrony

# Verificare NTS
chronyc -N authdata
# Deve mostrare "NTS" nella colonna Mode e "1" in KeyID
```

### Chrony come server NTS {#chrony-nts-server}

Chrony può funzionare anche come **server NTS**, servendo tempo autenticato ai client della rete interna. Richiede un certificato TLS valido (il protocollo NTS-KE usa TLS 1.3 sulla porta 4460).

```bash
# In /etc/chrony/chrony.conf — configurazione server NTS

# Sorgenti upstream (il server deve essere sincronizzato)
server time.cloudflare.com iburst nts
server nts.netnod.se iburst nts

# Abilitare servizio NTP per la rete locale
allow 192.168.0.0/16
allow 10.0.0.0/8

# === Configurazione NTS server ===
# Certificato TLS — Let's Encrypt o CA interna
# Il CN/SAN deve corrispondere al nome usato dai client
ntsserverkey /etc/chrony/tls/server.key
ntsservercert /etc/chrony/tls/server.pem

# Directory per cookie NTS lato server (stato sessione)
ntsdumpdir /var/lib/chrony

# Porta NTS-KE (default 4460, TCP)
# ntsport 4460

# Rotazione chiavi NTS automatica
ntsrotate 86400

# Firewall — aprire porte NTP e NTS-KE
sudo ufw allow 123/udp comment "NTP"
sudo ufw allow 4460/tcp comment "NTS-KE"

# Verificare stato server NTS
chronyc -N serverstats
# Campi NTS: NTS-KE connections accepted, NTS cookies issued

# Test da un client
# Il client deve avere nella sua chrony.conf:
# server ntp.example.lan iburst nts
# ntstrustedcerts /path/to/ca-cert.pem   # se CA interna

# Confronto con systemd-timesyncd:
# systemd-timesyncd è un client SNTP minimale — NON supporta:
#   - modalità server (non può servire tempo ad altri)
#   - NTS (nessuna autenticazione)
#   - alta precisione (SNTP vs NTP completo)
#   - sorgenti multiple con selezione algoritmica
# Usare timesyncd solo su client semplici senza requisiti di sicurezza NTP
# Per server o client enterprise → chrony è l'unica scelta ragionevole
```

### Monitoraggio NTP

```bash
# Script di monitoraggio — controllare offset
#!/bin/bash
OFFSET=$(chronyc tracking | grep "System time" | awk '{print $4}')
THRESHOLD=0.1  # 100ms

if (( $(echo "$OFFSET > $THRESHOLD" | bc -l) )); then
    echo "ALERT: NTP offset ${OFFSET}s supera soglia ${THRESHOLD}s"
    # Inviare alert (mail, webhook, etc.)
fi

# Prometheus — chrony_exporter per metriche
# Metriche chiave da monitorare:
# - chrony_tracking_system_time_offset_seconds
# - chrony_tracking_root_delay_seconds
# - chrony_tracking_stratum
# - chrony_source_reachability
```

---

## FTP: vsftpd e SFTP

### SFTP via OpenSSH

SFTP è il metodo consigliato per il trasferimento file: usa SSH, quindi tutto è cifrato. Non richiede software aggiuntivo.

```bash
# SFTP è integrato in OpenSSH — nessuna installazione aggiuntiva

# Configurazione chroot per utenti SFTP-only
# /etc/ssh/sshd_config
Match Group sftp_users
    ChrootDirectory /srv/sftp/%u
    ForceCommand internal-sftp -l INFO     # Logging SFTP
    AllowTcpForwarding no
    X11Forwarding no
    PermitTunnel no
    AllowAgentForwarding no
    PasswordAuthentication yes             # O no, per solo chiave pubblica

# Setup utenti SFTP
sudo groupadd sftp_users
sudo useradd -m -G sftp_users -s /usr/sbin/nologin sftpuser1
sudo passwd sftpuser1

# Struttura directory chroot
# IMPORTANTE: ChrootDirectory deve essere owned da root e non scrivibile da altri
sudo mkdir -p /srv/sftp/sftpuser1/upload
sudo chown root:root /srv/sftp/sftpuser1          # Root owner per chroot
sudo chmod 755 /srv/sftp/sftpuser1
sudo chown sftpuser1:sftp_users /srv/sftp/sftpuser1/upload  # Utente può scrivere qui
sudo chmod 755 /srv/sftp/sftpuser1/upload

sudo systemctl restart sshd

# Test
sftp sftpuser1@server
sftp> ls
sftp> cd upload
sftp> put localfile.txt
sftp> get remotefile.txt
sftp> bye

# Automazione con sshpass (solo per script, mai in produzione con password)
# Preferire chiave pubblica SSH
sftp -o IdentityFile=~/.ssh/sftp_key sftpuser1@server <<EOF
put /local/path/file.tar.gz upload/
bye
EOF

# Logging SFTP
# Aggiungere a /etc/ssh/sshd_config:
Subsystem sftp internal-sftp -l INFO -f AUTH
# I log appaiono in /var/log/auth.log o journal
```

### vsftpd — Configurazione completa

vsftpd (Very Secure FTP Daemon) — usare solo se FTP è strettamente necessario (legacy, dispositivi che non supportano SFTP).

```bash
sudo apt install vsftpd

# /etc/vsftpd.conf — configurazione hardened
listen=YES
listen_ipv6=NO

# Accesso
anonymous_enable=NO
local_enable=YES
write_enable=YES

# Chroot
chroot_local_user=YES                      # Blocca utenti nella propria home
allow_writeable_chroot=YES
chroot_list_enable=YES                     # Eccezioni alla regola chroot
chroot_list_file=/etc/vsftpd.chroot_list   # Utenti NON chrooted

# Utenti permessi
userlist_enable=YES
userlist_file=/etc/vsftpd.userlist
userlist_deny=NO                           # Lista = utenti PERMESSI (non negati)

# Passive mode
pasv_enable=YES
pasv_min_port=40000
pasv_max_port=40100
pasv_address=203.0.113.100                 # IP pubblico per NAT

# TLS/SSL — OBBLIGATORIO
ssl_enable=YES
rsa_cert_file=/etc/ssl/certs/vsftpd.pem
rsa_private_key_file=/etc/ssl/private/vsftpd.key
force_local_data_ssl=YES                   # Forza TLS per dati
force_local_logins_ssl=YES                 # Forza TLS per login
ssl_tlsv1=NO                              # Disabilita TLSv1
ssl_sslv2=NO
ssl_sslv3=NO
ssl_ciphers=HIGH                           # Solo cipher forti
require_ssl_reuse=NO

# Logging
xferlog_enable=YES
xferlog_std_format=NO
vsftpd_log_file=/var/log/vsftpd.log
log_ftp_protocol=YES
dual_log_enable=YES

# Performance
idle_session_timeout=300
data_connection_timeout=120
max_clients=50
max_per_ip=5

# Sicurezza aggiuntiva
tcp_wrappers=YES
seccomp_sandbox=YES

# Generare certificato
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/vsftpd.key \
    -out /etc/ssl/certs/vsftpd.pem \
    -subj "/CN=ftp.example.com"

sudo systemctl enable --now vsftpd

# Test con TLS
lftp -u ftpuser -e "set ssl:verify-certificate no; ls; bye" ftp.example.com
```

### Utenti virtuali vsftpd

Utenti FTP non corrispondenti a utenti di sistema — più sicuro.

```bash
# Installare modulo PAM per database Berkeley DB
sudo apt install db-util

# Creare file utenti virtuali (testo piano, poi convertito)
# /etc/vsftpd/virtual_users.txt
# Formato: username su riga dispari, password su riga pari
ftpuser1
password1_here
ftpuser2
password2_here

# Convertire in database Berkeley DB
sudo db_load -T -t hash -f /etc/vsftpd/virtual_users.txt /etc/vsftpd/virtual_users.db
sudo chmod 600 /etc/vsftpd/virtual_users.db

# Configurazione PAM per utenti virtuali
# /etc/pam.d/vsftpd_virtual
auth    required    pam_userdb.so db=/etc/vsftpd/virtual_users
account required    pam_userdb.so db=/etc/vsftpd/virtual_users

# Aggiornare vsftpd.conf
guest_enable=YES
guest_username=vsftpd_virtual              # Utente di sistema mappato
pam_service_name=vsftpd_virtual
virtual_use_local_privs=NO

# Configurazione per-utente virtuale
user_sub_token=$USER
local_root=/srv/ftp/virtual/$USER
user_config_dir=/etc/vsftpd/user_conf

# Creare directory per ogni utente virtuale
sudo useradd -d /srv/ftp -s /usr/sbin/nologin vsftpd_virtual
sudo mkdir -p /srv/ftp/virtual/ftpuser1
sudo mkdir -p /srv/ftp/virtual/ftpuser2
sudo chown vsftpd_virtual:nogroup /srv/ftp/virtual/ftpuser1
sudo chown vsftpd_virtual:nogroup /srv/ftp/virtual/ftpuser2

# Configurazione specifica per ftpuser1
# /etc/vsftpd/user_conf/ftpuser1
write_enable=YES
local_umask=022
```

---

## Samba

Samba implementa il protocollo SMB/CIFS, permettendo a server Linux di fornire file sharing, servizi di stampa e integrazione con Active Directory.

### Samba come membro Active Directory

```bash
# Installazione
sudo apt install samba winbind libnss-winbind libpam-winbind krb5-user

# 1. Configurare Kerberos — /etc/krb5.conf
[libdefaults]
    default_realm = EXAMPLE.COM
    dns_lookup_realm = false
    dns_lookup_kdc = true
    ticket_lifetime = 24h
    renew_lifetime = 7d

[realms]
    EXAMPLE.COM = {
        kdc = dc1.example.com
        kdc = dc2.example.com
        admin_server = dc1.example.com
    }

[domain_realm]
    .example.com = EXAMPLE.COM
    example.com = EXAMPLE.COM

# 2. Configurare Samba — /etc/samba/smb.conf
[global]
    workgroup = EXAMPLE
    realm = EXAMPLE.COM
    security = ADS                         # Active Directory Security
    encrypt passwords = yes

    # Winbind
    idmap config * : backend = tdb
    idmap config * : range = 3000-7999
    idmap config EXAMPLE : backend = rid
    idmap config EXAMPLE : range = 10000-999999
    winbind use default domain = yes
    winbind enum users = yes
    winbind enum groups = yes
    winbind refresh tickets = yes

    # Kerberos
    kerberos method = secrets and keytab
    dedicated keytab file = /etc/krb5.keytab

    # Template per utenti AD
    template shell = /bin/bash
    template homedir = /home/%U

    # Logging
    log file = /var/log/samba/log.%m
    max log size = 5000
    log level = 1

    # Performance
    socket options = TCP_NODELAY IPTOS_LOWDELAY

# 3. Unire al dominio
sudo net ads join -U administrator
# Inserire password dell'amministratore di dominio

# 4. Configurare NSS — /etc/nsswitch.conf
passwd: files systemd winbind
group:  files systemd winbind

# 5. Avviare servizi
sudo systemctl enable --now smbd nmbd winbind

# 6. Verificare
sudo net ads testjoin                      # Test appartenenza dominio
wbinfo -u                                  # Lista utenti AD
wbinfo -g                                  # Lista gruppi AD
wbinfo -a 'EXAMPLE\utente%password'       # Test autenticazione
getent passwd 'EXAMPLE\utente'            # Verifica NSS
id 'EXAMPLE\utente'                       # UID/GID mappato

# 7. PAM per login — automatizzare creazione home
sudo pam-auth-update                       # Abilitare winbind e mkhomedir
```

### File sharing {#file-sharing-samba}

```bash
# Aggiungere in /etc/samba/smb.conf

# Share pubblica (accesso libero)
[pubblica]
    path = /srv/samba/pubblica
    browseable = yes
    read only = no
    guest ok = yes
    create mask = 0664
    directory mask = 0775
    force group = sambashare

# Share dipartimento con controllo accessi AD
[engineering]
    path = /srv/samba/engineering
    browseable = yes
    read only = no
    guest ok = no
    valid users = @"EXAMPLE\Engineering" @"EXAMPLE\Domain Admins"
    write list = @"EXAMPLE\Engineering"
    read list = @"EXAMPLE\Management"
    create mask = 0660
    directory mask = 0770
    force group = "EXAMPLE\Engineering"
    inherit permissions = yes
    inherit acls = yes

# Home directory utenti
[homes]
    comment = Home Directories
    browseable = no
    read only = no
    create mask = 0700
    directory mask = 0700
    valid users = %S

# Share con audit
[confidenziale]
    path = /srv/samba/confidenziale
    browseable = no
    read only = no
    valid users = @"EXAMPLE\Management"
    # Audit
    vfs objects = full_audit
    full_audit:prefix = %u|%I|%S
    full_audit:success = mkdir rmdir open read write rename unlink
    full_audit:failure = none
    full_audit:facility = local5
    full_audit:priority = notice

# Creare directory e impostare permessi
sudo mkdir -p /srv/samba/{pubblica,engineering,confidenziale}
sudo chown root:sambashare /srv/samba/pubblica
sudo chmod 2775 /srv/samba/pubblica

# Verificare configurazione
testparm                                   # Verifica smb.conf
smbclient -L //localhost -U utente        # Lista share
smbclient //server/engineering -U utente  # Connessione a share

# Gestione utenti Samba locali (se non si usa AD)
sudo smbpasswd -a utente                  # Aggiungere utente Samba
sudo smbpasswd -e utente                  # Abilitare
sudo smbpasswd -d utente                  # Disabilitare
sudo pdbedit -L                           # Lista utenti Samba
```

### Servizi di stampa {#servizi-di-stampa-samba}

```bash
# Samba può funzionare come print server per client Windows

[printers]
    comment = All Printers
    path = /var/spool/samba
    browseable = no
    guest ok = no
    printable = yes
    create mask = 0700

[print$]
    comment = Printer Drivers
    path = /var/lib/samba/printers
    browseable = yes
    read only = yes
    guest ok = no
    write list = @"EXAMPLE\Domain Admins"

# Prerequisiti: CUPS installato e configurato
sudo apt install cups
sudo systemctl enable --now cups

# Aggiungere stampante in CUPS (via web: http://localhost:631)
# Poi condividere via Samba
```

### Controllo accessi e permessi {#controllo-accessi-e-permessi-samba}

```bash
# ACL POSIX estese per permessi granulari
sudo apt install acl

# Impostare ACL su directory share
sudo setfacl -R -m g:"EXAMPLE\Engineering":rwx /srv/samba/engineering
sudo setfacl -R -m d:g:"EXAMPLE\Engineering":rwx /srv/samba/engineering   # Default ACL
sudo setfacl -R -m g:"EXAMPLE\Management":rx /srv/samba/engineering

# Verificare ACL
getfacl /srv/samba/engineering

# Permessi in smb.conf vs filesystem
# Samba applica il PIÙ RESTRITTIVO tra:
# 1. Permessi smb.conf (valid users, write list, read list)
# 2. Permessi filesystem (chmod/chown/ACL)
# 3. create mask / directory mask

# VFS Objects per funzionalità aggiuntive
vfs objects = recycle acl_xattr            # Cestino + ACL estese

# Configurazione cestino
recycle:repository = .recycle/%U           # Directory cestino per utente
recycle:keeptree = yes
recycle:versions = yes
recycle:maxsize = 0                        # 0 = nessun limite dimensione
```

### Performance tuning Samba

```bash
# /etc/samba/smb.conf — [global]

# Socket options
socket options = TCP_NODELAY IPTOS_LOWDELAY SO_RCVBUF=131072 SO_SNDBUF=131072

# Disabilitare feature non necessarie
load printers = no                         # Se non serve stampa
printing = bsd
printcap name = /dev/null
disable spoolss = yes

# Async I/O
aio read size = 16384
aio write size = 16384

# SMB versione — forzare SMB3 per performance e sicurezza
server min protocol = SMB2_10
server max protocol = SMB3_11
client min protocol = SMB2_10

# Signing
server signing = mandatory                 # Sicurezza (impatto performance ~10%)

# Multichannel (SMB3)
server multi channel support = yes

# Cache
max stat cache size = 512

# Monitoring performance
smbstatus                                  # Connessioni attive
smbstatus -L                              # Lock attivi
sudo net statistics srv                    # Statistiche server
```

---

## NFS — Network File System

NFS permette di condividere directory tra sistemi Linux/Unix via rete. NFSv4 è la versione corrente; NFSv3 è legacy.

### NFSv4 — Configurazione server

```bash
# Installazione server
sudo apt install nfs-kernel-server

# Creare directory da esportare
sudo mkdir -p /srv/nfs/shared
sudo mkdir -p /srv/nfs/home
sudo chown nobody:nogroup /srv/nfs/shared

# /etc/exports — definizione esportazioni
# Sintassi: directory client(opzioni)

# Esportazione base — rete interna
/srv/nfs/shared    192.168.1.0/24(rw,sync,no_subtree_check,no_root_squash)

# Esportazione con squash (sicura) — root del client mappato a nobody
/srv/nfs/shared    10.0.0.0/8(rw,sync,no_subtree_check,root_squash)

# Esportazione read-only
/srv/nfs/docs      192.168.1.0/24(ro,sync,no_subtree_check)

# Esportazione home directory
/srv/nfs/home      192.168.1.0/24(rw,sync,no_subtree_check)

# Esportazione a singolo host
/srv/nfs/backup    192.168.1.50(rw,sync,no_subtree_check,no_root_squash)

# Opzioni chiave:
# rw / ro           — lettura-scrittura / sola lettura
# sync              — scrittura sincrona (sicuro, più lento)
# async             — scrittura asincrona (veloce, rischio dati su crash)
# no_subtree_check  — disabilita check sottodirectory (performance)
# root_squash       — root del client → nobody (default, sicuro)
# no_root_squash    — root del client mantiene privilegi (pericoloso)
# all_squash        — tutti gli utenti → nobody
# anonuid/anongid   — UID/GID per utenti squashati

# NFSv4 — pseudo-filesystem root
# /etc/exports per NFSv4 con fsid=0 (root export)
/srv/nfs           192.168.1.0/24(rw,sync,fsid=0,crossmnt,no_subtree_check)
/srv/nfs/shared    192.168.1.0/24(rw,sync,no_subtree_check)
/srv/nfs/home      192.168.1.0/24(rw,sync,no_subtree_check)

# Applicare e verificare
sudo exportfs -ra                          # Ri-esporta tutto
sudo exportfs -v                           # Lista esportazioni attive
sudo exportfs -s                           # Mostra con opzioni

# Firewall — NFSv4 usa solo porta 2049/TCP
sudo ufw allow from 192.168.1.0/24 to any port 2049

sudo systemctl enable --now nfs-kernel-server

# ID mapping per NFSv4
# /etc/idmapd.conf
[General]
Domain = example.com
```

### NFSv4 — Configurazione client

```bash
# Installazione client
sudo apt install nfs-common

# Mount manuale
sudo mount -t nfs4 192.168.1.60:/shared /mnt/nfs/shared
sudo mount -t nfs4 192.168.1.60:/ /mnt/nfs            # Monta la radice NFSv4

# Verificare mount
mount | grep nfs
df -h | grep nfs
nfsstat -c                                 # Statistiche client NFS

# Mount persistente — /etc/fstab
192.168.1.60:/shared  /mnt/nfs/shared  nfs4  defaults,_netdev,noatime  0 0
192.168.1.60:/home    /mnt/nfs/home    nfs4  defaults,_netdev,noatime  0 0

# Opzioni mount importanti:
# _netdev        — aspetta rete prima di montare (ESSENZIALE per NFS)
# noatime        — non aggiorna access time (performance)
# soft           — ritorna errore se server non risponde (vs hard = blocca)
# timeo=600      — timeout in decimi di secondo
# retrans=2      — numero ritrasmissioni
# rsize=1048576  — read buffer 1MB (performance)
# wsize=1048576  — write buffer 1MB (performance)
# sec=krb5p      — sicurezza Kerberos (privacy + integrità)

# Mount con opzioni performance
192.168.1.60:/shared  /mnt/nfs/shared  nfs4  rw,_netdev,noatime,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2  0 0

# Smontare
sudo umount /mnt/nfs/shared
sudo umount -l /mnt/nfs/shared             # Lazy unmount (se busy)
```

### NFS con Kerberos

NFS con Kerberos fornisce autenticazione forte, integrità e cifratura dei dati.

```bash
# Livelli sicurezza NFS Kerberos:
# sec=sys      — autenticazione UID/GID di sistema (default, insicuro)
# sec=krb5     — autenticazione Kerberos
# sec=krb5i    — autenticazione + integrità (checksum)
# sec=krb5p    — autenticazione + integrità + privacy (cifratura)

# Prerequisiti:
# 1. KDC Kerberos funzionante (MIT o AD)
# 2. DNS forward e reverse funzionanti
# 3. NTP sincronizzato su tutti i nodi

# Sul KDC — creare principal per server e client NFS
kadmin.local
addprinc -randkey nfs/nfs-server.example.com@EXAMPLE.COM
addprinc -randkey nfs/nfs-client.example.com@EXAMPLE.COM
ktadd -k /tmp/nfs-server.keytab nfs/nfs-server.example.com@EXAMPLE.COM
ktadd -k /tmp/nfs-client.keytab nfs/nfs-client.example.com@EXAMPLE.COM

# Copiare keytab sui rispettivi server (via scp o canale sicuro)
# Poi installare come /etc/krb5.keytab

# Sul server NFS — /etc/exports con Kerberos
/srv/nfs/secure  192.168.1.0/24(rw,sync,sec=krb5p,no_subtree_check)

# Abilitare gssd (GSS-API daemon)
sudo systemctl enable --now rpc-gssd

# Sul server NFS — abilitare svcgssd
# /etc/default/nfs-kernel-server
NEED_SVCGSSD=yes

sudo systemctl restart nfs-kernel-server

# Sul client — mount con Kerberos
sudo mount -t nfs4 -o sec=krb5p nfs-server.example.com:/secure /mnt/secure

# /etc/fstab
nfs-server.example.com:/secure  /mnt/secure  nfs4  sec=krb5p,_netdev  0 0
```

### Performance tuning NFS

```bash
# Server — /etc/nfs.conf o parametri kernel
# Aumentare numero thread NFS
# /etc/default/nfs-kernel-server
RPCNFSDCOUNT=16                            # Default 8, aumentare per workload pesanti

# Parametri kernel — /etc/sysctl.d/nfs.conf
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.core.rmem_default = 1048576
net.core.wmem_default = 1048576

# Monitorare performance
nfsstat -s                                 # Statistiche server
nfsstat -c                                 # Statistiche client
nfsiostat 2                                # I/O statistics ogni 2 secondi
mountstats /mnt/nfs/shared                 # Statistiche dettagliate per mount point

# Client — opzioni mount per performance
# rsize/wsize: dimensione buffer lettura/scrittura (default 1MB in NFSv4)
# async: permetti write caching sul client
# nocto: non controllare attributi ad ogni open (per file read-mostly)

# Benchmark
dd if=/dev/zero of=/mnt/nfs/shared/testfile bs=1M count=1024 oflag=direct
dd if=/mnt/nfs/shared/testfile of=/dev/null bs=1M iflag=direct
# Rimuovere file test dopo benchmark
```

### Automount con autofs

autofs monta filesystem NFS on-demand quando acceduti, e li smonta dopo un timeout. Ideale per home directory e share opzionali.

```bash
# Installazione
sudo apt install autofs

# File di configurazione
/etc/auto.master                           # Mappa master
/etc/auto.nfs                              # Mappa per NFS (nome arbitrario)

# /etc/auto.master — definisce mount point base e mappe
# Mount point      Mappa              Opzioni
/mnt/auto          /etc/auto.nfs      --timeout=300

# Direct map (mount point esplicito)
/-                 /etc/auto.direct

# /etc/auto.nfs — mappa NFS
# Chiave    Opzioni                     Server:path
shared      -rw,noatime,nfsvers=4       192.168.1.60:/shared
docs        -ro,noatime,nfsvers=4       192.168.1.60:/docs
backup      -rw,noatime,nfsvers=4       192.168.1.60:/backup

# Risultato: /mnt/auto/shared, /mnt/auto/docs, /mnt/auto/backup
# Montati automaticamente al primo accesso, smontati dopo 300 secondi di inattività

# /etc/auto.direct — direct map
/data/projects  -rw,noatime,nfsvers=4   192.168.1.60:/projects

# Home directory automatiche (wildcard)
# /etc/auto.master
/home           /etc/auto.home

# /etc/auto.home
*               -rw,noatime,nfsvers=4   192.168.1.60:/home/&
# & = sostituito con il nome utente (chiave)

# Avviare autofs
sudo systemctl enable --now autofs

# Test — accedere alla directory per triggerare il mount
ls /mnt/auto/shared                        # Monta automaticamente
# Dopo 300s di inattività: smonta automaticamente

# Debug
sudo automount -f -v                       # Foreground + verbose
journalctl -u autofs
```

---

## LDAP: OpenLDAP

LDAP (Lightweight Directory Access Protocol) fornisce un servizio di directory centralizzato per autenticazione, autorizzazione e informazioni utente.

### Installazione e configurazione iniziale {#installazione-e-configurazione-iniziale-ldap}

```bash
# Installazione
sudo apt install slapd ldap-utils

# Configurazione iniziale interattiva
sudo dpkg-reconfigure slapd
# → Omit OpenLDAP config? → No
# → DNS domain: example.com → DC=example,DC=com
# → Organization name: Example Corp
# → Admin password: (password forte)
# → Database backend: MDB (consigliato)
# → Remove database when purged? → No
# → Move old database? → Yes

# Verificare installazione
sudo slapcat                               # Dump completo database
ldapsearch -x -H ldap://localhost -b "dc=example,dc=com" -LLL

# Configurazione runtime — cn=config (LDAP-based, non file)
# La configurazione è dentro l'albero LDAP stesso:
sudo ldapsearch -Y EXTERNAL -H ldapi:/// -b "cn=config" -LLL

# File di configurazione LDAP (deprecato in favore di cn=config ma utile per riferimento)
/etc/ldap/ldap.conf                       # Client defaults
/etc/ldap/slapd.d/                        # Config directory (cn=config)

# /etc/ldap/ldap.conf — defaults client
BASE    dc=example,dc=com
URI     ldap://ldap.example.com
TLS_CACERT /etc/ssl/certs/ca-certificates.crt
```

### Schema e struttura directory

```bash
# Struttura tipica directory LDAP
# dc=example,dc=com (root)
# ├── ou=People         (utenti)
# ├── ou=Groups         (gruppi)
# ├── ou=Services       (account servizio)
# ├── ou=Hosts          (computer)
# └── ou=Policies       (password policy, etc.)

# Creare Organizational Units — base.ldif
dn: ou=People,dc=example,dc=com
objectClass: organizationalUnit
ou: People

dn: ou=Groups,dc=example,dc=com
objectClass: organizationalUnit
ou: Groups

dn: ou=Services,dc=example,dc=com
objectClass: organizationalUnit
ou: Services

# Applicare
ldapadd -x -D "cn=admin,dc=example,dc=com" -W -f base.ldif

# Aggiungere utente — user.ldif
dn: uid=jsmith,ou=People,dc=example,dc=com
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
uid: jsmith
cn: John Smith
sn: Smith
givenName: John
mail: jsmith@example.com
uidNumber: 10001
gidNumber: 10001
homeDirectory: /home/jsmith
loginShell: /bin/bash
userPassword: {SSHA}hash_generato_con_slappasswd

# Generare hash password
slappasswd -s "password_utente"
# Output: {SSHA}xxxxxxxxxxxx — copiare in userPassword

ldapadd -x -D "cn=admin,dc=example,dc=com" -W -f user.ldif

# Aggiungere gruppo — group.ldif
dn: cn=developers,ou=Groups,dc=example,dc=com
objectClass: posixGroup
cn: developers
gidNumber: 10001
memberUid: jsmith

ldapadd -x -D "cn=admin,dc=example,dc=com" -W -f group.ldif

# Operazioni LDAP quotidiane
ldapsearch -x -b "dc=example,dc=com" "(uid=jsmith)"          # Cercare utente
ldapsearch -x -b "dc=example,dc=com" "(objectClass=posixGroup)" # Lista gruppi
ldapsearch -x -b "dc=example,dc=com" "(uid=*)" uid cn mail    # Cerca tutti, campi specifici

# Modificare entry — modify.ldif
dn: uid=jsmith,ou=People,dc=example,dc=com
changetype: modify
replace: mail
mail: john.smith@example.com
-
add: telephoneNumber
telephoneNumber: +39 02 12345678

ldapmodify -x -D "cn=admin,dc=example,dc=com" -W -f modify.ldif

# Eliminare entry
ldapdelete -x -D "cn=admin,dc=example,dc=com" -W "uid=olduser,ou=People,dc=example,dc=com"

# Cambiare password utente
ldappasswd -x -D "cn=admin,dc=example,dc=com" -W -S "uid=jsmith,ou=People,dc=example,dc=com"

# Schema — elencare schemi caricati
ldapsearch -Y EXTERNAL -H ldapi:/// -b "cn=schema,cn=config" -LLL dn

# Aggiungere schema aggiuntivo (es. sudo)
sudo ldapadd -Y EXTERNAL -H ldapi:/// -f /etc/ldap/schema/sudo.ldif
```

### ACL — Access Control Lists

```bash
# Le ACL LDAP controllano chi può leggere/scrivere quali attributi e entry.
# Configurate in cn=config via LDIF.

# Visualizzare ACL correnti
sudo ldapsearch -Y EXTERNAL -H ldapi:/// -b "olcDatabase={1}mdb,cn=config" olcAccess -LLL

# Esempio ACL — acl.ldif
dn: olcDatabase={1}mdb,cn=config
changetype: modify
replace: olcAccess
# Utenti possono cambiare la propria password
olcAccess: {0}to attrs=userPassword
  by self write
  by anonymous auth
  by dn="cn=admin,dc=example,dc=com" write
  by * none
# Utenti possono leggere i propri dati
olcAccess: {1}to attrs=shadowLastChange
  by self write
  by dn="cn=admin,dc=example,dc=com" write
  by * read
# Admin ha accesso completo
olcAccess: {2}to *
  by dn="cn=admin,dc=example,dc=com" write
  by users read
  by * none

sudo ldapmodify -Y EXTERNAL -H ldapi:/// -f acl.ldif

# Testare ACL — provare accesso come utente specifico
ldapsearch -x -D "uid=jsmith,ou=People,dc=example,dc=com" -W \
    -b "dc=example,dc=com" "(uid=*)" userPassword
# Deve fallire: jsmith non può leggere password di altri
```

### Replicazione (syncrepl)

```bash
# Replicazione provider-consumer (master-slave) per alta disponibilità.

# Sul PROVIDER (master) — abilitare overlay syncprov
# syncprov.ldif
dn: olcOverlay=syncprov,olcDatabase={1}mdb,cn=config
changetype: add
objectClass: olcOverlayConfig
objectClass: olcSyncProvConfig
olcOverlay: syncprov
olcSpCheckpoint: 100 10
olcSpSessionlog: 1000

sudo ldapmodify -Y EXTERNAL -H ldapi:/// -f syncprov.ldif

# Creare utente per replicazione — repl_user.ldif
dn: cn=replicator,dc=example,dc=com
objectClass: simpleSecurityObject
objectClass: organizationalRole
cn: replicator
userPassword: {SSHA}hash_password_replicatore

# ACL per il replicatore
olcAccess: {0}to *
  by dn="cn=replicator,dc=example,dc=com" read
  by dn="cn=admin,dc=example,dc=com" write
  ...

# Sul CONSUMER (slave) — configurare syncrepl
# syncrepl.ldif
dn: olcDatabase={1}mdb,cn=config
changetype: modify
add: olcSyncRepl
olcSyncRepl: rid=001
  provider=ldap://ldap-master.example.com
  type=refreshAndPersist
  retry="60 10 300 +"
  searchbase="dc=example,dc=com"
  attrs="*,+"
  bindmethod=simple
  binddn="cn=replicator,dc=example,dc=com"
  credentials=password_replicatore
  starttls=critical
  tls_cacert=/etc/ssl/certs/ca-certificates.crt

sudo ldapmodify -Y EXTERNAL -H ldapi:/// -f syncrepl.ldif

# Verificare replicazione
# Aggiungere un entry sul provider e verificare che appaia sul consumer
ldapsearch -x -H ldap://consumer.example.com -b "dc=example,dc=com" "(uid=jsmith)"
```

### TLS per OpenLDAP

```bash
# MAI usare LDAP in chiaro in produzione. Configurare TLS.

# Configurare TLS — tls.ldif
dn: cn=config
changetype: modify
replace: olcTLSCACertificateFile
olcTLSCACertificateFile: /etc/ssl/certs/ca-certificates.crt
-
replace: olcTLSCertificateFile
olcTLSCertificateFile: /etc/ssl/certs/ldap-server.crt
-
replace: olcTLSCertificateKeyFile
olcTLSCertificateKeyFile: /etc/ssl/private/ldap-server.key

sudo ldapmodify -Y EXTERNAL -H ldapi:/// -f tls.ldif

# Forzare TLS — disabilitare connessioni non cifrate
# security.ldif
dn: olcDatabase={1}mdb,cn=config
changetype: modify
add: olcSecurity
olcSecurity: tls=1

sudo ldapmodify -Y EXTERNAL -H ldapi:/// -f security.ldif

# Client — /etc/ldap/ldap.conf
TLS_CACERT /etc/ssl/certs/ca-certificates.crt
TLS_REQCERT demand                         # Verifica certificato server

# Test connessione TLS
ldapsearch -x -H ldaps://ldap.example.com -b "dc=example,dc=com" -LLL
ldapsearch -x -ZZ -H ldap://ldap.example.com -b "dc=example,dc=com" -LLL  # StartTLS
```

### Integrazione client con sssd

```bash
# sssd (System Security Services Daemon) è il modo raccomandato per integrare
# client Linux con LDAP, AD, o altri provider di identità.

# Installazione
sudo apt install sssd sssd-ldap sssd-tools libnss-sss libpam-sss

# /etc/sssd/sssd.conf
[sssd]
domains = example.com
services = nss, pam, ssh, sudo
config_file_version = 2

[domain/example.com]
id_provider = ldap
auth_provider = ldap
chpass_provider = ldap

ldap_uri = ldaps://ldap.example.com
ldap_search_base = dc=example,dc=com
ldap_user_search_base = ou=People,dc=example,dc=com
ldap_group_search_base = ou=Groups,dc=example,dc=com

# TLS
ldap_tls_reqcert = demand
ldap_tls_cacert = /etc/ssl/certs/ca-certificates.crt

# Bind DN per ricerche (non admin, account read-only dedicato)
ldap_default_bind_dn = cn=sssd-bind,ou=Services,dc=example,dc=com
ldap_default_authtok = password_bind_account

# Mappatura attributi (se diversi da default)
ldap_user_object_class = posixAccount
ldap_user_name = uid
ldap_user_uid_number = uidNumber
ldap_user_gid_number = gidNumber
ldap_user_home_directory = homeDirectory
ldap_user_shell = loginShell

# Cache
cache_credentials = true
entry_cache_timeout = 300

# Accesso
access_provider = ldap
ldap_access_filter = (objectClass=posixAccount)

# Sudo (opzionale)
sudo_provider = ldap
ldap_sudo_search_base = ou=SUDOers,dc=example,dc=com

# Permessi file — CRITICO: deve essere 600
sudo chmod 600 /etc/sssd/sssd.conf
sudo chown root:root /etc/sssd/sssd.conf

# Configurare NSS — /etc/nsswitch.conf
passwd: files sss
group:  files sss
shadow: files sss
sudoers: files sss

# Configurare PAM
sudo pam-auth-update                       # Abilitare SSS authentication e mkhomedir

# Avviare sssd
sudo systemctl enable --now sssd

# Verificare
getent passwd jsmith                       # Deve restituire utente LDAP
id jsmith                                  # UID, GID, gruppi
su - jsmith                               # Login come utente LDAP
sss_cache -E                              # Svuota cache sssd (troubleshooting)
```

---

## Mail: Postfix e Dovecot

### Postfix — Configurazione completa

Postfix è l'MTA (Mail Transfer Agent) raccomandato. Gestisce l'invio e la ricezione di email.

```bash
sudo apt install postfix

# Configurazione completa — /etc/postfix/main.cf
# Identità del server
myhostname = mail.example.com
mydomain = example.com
myorigin = $mydomain
mydestination = $myhostname, localhost.$mydomain, localhost, $mydomain

# Interfacce e reti
inet_interfaces = all
inet_protocols = all
mynetworks = 127.0.0.0/8, 10.0.0.0/8, [::1]/128

# Mailbox
home_mailbox = Maildir/                    # Formato Maildir (vs mbox)
mailbox_size_limit = 0                     # 0 = illimitato
message_size_limit = 52428800              # 50MB max per messaggio

# Alias
alias_maps = hash:/etc/aliases
alias_database = hash:/etc/aliases

# Relay — NON fare open relay
smtpd_relay_restrictions =
    permit_mynetworks,
    permit_sasl_authenticated,
    defer_unauth_destination

# Restrizioni SMTP
smtpd_helo_required = yes
smtpd_helo_restrictions =
    permit_mynetworks,
    reject_invalid_helo_hostname,
    reject_non_fqdn_helo_hostname

smtpd_sender_restrictions =
    permit_mynetworks,
    reject_non_fqdn_sender,
    reject_unknown_sender_domain

smtpd_recipient_restrictions =
    permit_mynetworks,
    permit_sasl_authenticated,
    reject_unauth_destination,
    reject_invalid_hostname,
    reject_non_fqdn_hostname,
    reject_non_fqdn_sender,
    reject_non_fqdn_recipient,
    reject_unknown_sender_domain,
    reject_unknown_recipient_domain,
    reject_rbl_client zen.spamhaus.org,
    reject_rbl_client bl.spamcop.net

# Gestione coda
maximal_queue_lifetime = 5d
bounce_queue_lifetime = 1d
queue_run_delay = 300s

sudo systemctl enable --now postfix
sudo newaliases                            # Rigenerare database alias

# Operazioni coda
mailq                                      # Vedi coda
sudo postqueue -f                          # Flush coda
sudo postqueue -p                          # Lista coda dettagliata
sudo postsuper -d ALL                      # Svuota tutta la coda
sudo postsuper -d QUEUE_ID                # Rimuovi messaggio specifico
sudo postsuper -H QUEUE_ID                # Rilascia messaggio hold
sudo qshape active                        # Analisi forma coda

# Log
sudo journalctl -u postfix -f
tail -f /var/log/mail.log
```

### TLS per Postfix

```bash
# /etc/postfix/main.cf — TLS per invio (SMTP submission)

# TLS server (ricezione)
smtpd_tls_cert_file = /etc/ssl/certs/mail.example.com.crt
smtpd_tls_key_file = /etc/ssl/private/mail.example.com.key
smtpd_tls_security_level = may            # Opportunistic TLS
smtpd_tls_auth_only = yes                 # Auth solo su TLS
smtpd_tls_mandatory_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1
smtpd_tls_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1
smtpd_tls_mandatory_ciphers = high
smtpd_tls_loglevel = 1
smtpd_tls_session_cache_database = btree:${data_directory}/smtpd_scache

# TLS client (invio verso altri server)
smtp_tls_security_level = may
smtp_tls_mandatory_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1
smtp_tls_protocols = !SSLv2, !SSLv3, !TLSv1, !TLSv1.1
smtp_tls_mandatory_ciphers = high
smtp_tls_loglevel = 1
smtp_tls_session_cache_database = btree:${data_directory}/smtp_scache

# Abilitare submission (porta 587) — /etc/postfix/master.cf
# Decommentare:
submission inet n       -       y       -       -       smtpd
  -o syslog_name=postfix/submission
  -o smtpd_tls_security_level=encrypt
  -o smtpd_sasl_auth_enable=yes
  -o smtpd_tls_auth_only=yes
  -o smtpd_reject_unlisted_recipient=no
  -o smtpd_recipient_restrictions=permit_sasl_authenticated,reject
  -o milter_macro_daemon_name=ORIGINATING

# SASL con Dovecot (autenticazione utenti)
smtpd_sasl_type = dovecot
smtpd_sasl_path = private/auth
smtpd_sasl_auth_enable = yes
smtpd_sasl_security_options = noanonymous
smtpd_sasl_local_domain = $myhostname

# Relay tramite smarthost (es. SES, Mailgun)
relayhost = [smtp.mailgun.org]:587
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_sasl_security_options = noanonymous
smtp_tls_security_level = encrypt

# /etc/postfix/sasl_passwd
[smtp.mailgun.org]:587 user@domain:api_key

sudo postmap /etc/postfix/sasl_passwd
sudo chmod 600 /etc/postfix/sasl_passwd*
```

### SPF, DKIM, DMARC

Email authentication per prevenire spoofing e migliorare deliverability.

```bash
# --- SPF (Sender Policy Framework) ---
# Record DNS TXT nella zona DNS:
# example.com.  IN  TXT  "v=spf1 mx a ip4:203.0.113.20 -all"
# -all = hard fail (rifiuta email da IP non autorizzati)
# ~all = soft fail (accetta ma marca)

# Verifica SPF su Postfix con policyd-spf
sudo apt install postfix-policyd-spf-python

# /etc/postfix/main.cf
policyd-spf_time_limit = 3600
smtpd_recipient_restrictions =
    ...existing restrictions...
    check_policy_service unix:private/policyd-spf

# /etc/postfix/master.cf
policyd-spf  unix  -  n  n  -  0  spawn
  user=policyd-spf argv=/usr/bin/policyd-spf

# --- DKIM (DomainKeys Identified Mail) ---
sudo apt install opendkim opendkim-tools

# Generare chiave
sudo mkdir -p /etc/opendkim/keys/example.com
sudo opendkim-genkey -b 2048 -d example.com -D /etc/opendkim/keys/example.com -s mail -v
# Genera: mail.private (chiave privata) e mail.txt (record DNS)

# /etc/opendkim.conf
Syslog                  yes
SyslogSuccess           yes
LogWhy                  yes
Mode                    sv              # Sign + Verify
Canonicalization        relaxed/simple
Domain                  example.com
Selector                mail
KeyFile                 /etc/opendkim/keys/example.com/mail.private
Socket                  inet:12301@localhost
PidFile                 /run/opendkim/opendkim.pid
OversignHeaders         From
TrustAnchorFile         /usr/share/dns/root.key
UserID                  opendkim

# Tabella firme — /etc/opendkim/signing.table
*@example.com    mail._domainkey.example.com

# Tabella chiavi — /etc/opendkim/key.table
mail._domainkey.example.com    example.com:mail:/etc/opendkim/keys/example.com/mail.private

# Tabella host fidati — /etc/opendkim/trusted.hosts
127.0.0.1
::1
localhost
*.example.com

# Integrare con Postfix — /etc/postfix/main.cf
milter_default_action = accept
milter_protocol = 6
smtpd_milters = inet:localhost:12301
non_smtpd_milters = inet:localhost:12301

# Record DNS DKIM — contenuto di mail.txt generato
# mail._domainkey.example.com. IN TXT ( "v=DKIM1; h=sha256; k=rsa; p=MIIBIjAN..." )

sudo systemctl enable --now opendkim

# --- DMARC (Domain-based Message Authentication, Reporting & Conformance) ---
sudo apt install opendmarc

# /etc/opendmarc.conf
AuthservID        mail.example.com
TrustedAuthservIDs mail.example.com
RejectFailures    true
Socket            inet:54321@localhost

# Integrare con Postfix
smtpd_milters = inet:localhost:12301, inet:localhost:54321

# Record DNS DMARC
# _dmarc.example.com. IN TXT "v=DMARC1; p=reject; sp=reject; rua=mailto:dmarc-reports@example.com; ruf=mailto:dmarc-forensic@example.com; adkim=s; aspf=s; pct=100"

sudo systemctl enable --now opendmarc

# Verificare configurazione email
# Inviare email di test e controllare header per:
# Authentication-Results: ... spf=pass dkim=pass dmarc=pass
```

### Dovecot — IMAP/POP3

Dovecot è il server IMAP/POP3 per la lettura della posta. Si integra con Postfix per l'autenticazione SASL.

```bash
sudo apt install dovecot-imapd dovecot-pop3d dovecot-lmtpd

# /etc/dovecot/dovecot.conf
protocols = imap lmtp
# POP3 solo se necessario: protocols = imap pop3 lmtp

# /etc/dovecot/conf.d/10-mail.conf
mail_location = maildir:~/Maildir          # Formato Maildir
mail_privileged_group = mail
namespace inbox {
    inbox = yes
    separator = /
}

# /etc/dovecot/conf.d/10-auth.conf
auth_mechanisms = plain login
disable_plaintext_auth = yes               # Richiede TLS per auth

# /etc/dovecot/conf.d/10-ssl.conf
ssl = required
ssl_cert = </etc/ssl/certs/mail.example.com.crt
ssl_key = </etc/ssl/private/mail.example.com.key
ssl_min_protocol = TLSv1.2
ssl_prefer_server_ciphers = yes

# /etc/dovecot/conf.d/10-master.conf — socket SASL per Postfix
service auth {
    unix_listener /var/spool/postfix/private/auth {
        mode = 0660
        user = postfix
        group = postfix
    }
}

# LMTP — delivery locale (alternativa a Postfix local delivery)
service lmtp {
    unix_listener /var/spool/postfix/private/dovecot-lmtp {
        mode = 0600
        user = postfix
        group = postfix
    }
}

# Integrare delivery in Postfix — /etc/postfix/main.cf
mailbox_transport = lmtp:unix:private/dovecot-lmtp

# /etc/dovecot/conf.d/15-mailboxes.conf — mailbox speciali
namespace inbox {
    mailbox Drafts {
        special_use = \Drafts
        auto = subscribe
    }
    mailbox Sent {
        special_use = \Sent
        auto = subscribe
    }
    mailbox Trash {
        special_use = \Trash
        auto = subscribe
    }
    mailbox Junk {
        special_use = \Junk
        auto = subscribe
    }
}

# /etc/dovecot/conf.d/20-imap.conf
imap_idle_notify_interval = 2 mins

sudo systemctl enable --now dovecot

# Test connessione IMAP
openssl s_client -connect mail.example.com:993 -quiet
# Poi: a login utente password
# a select inbox
# a logout

# Diagnostica Dovecot
doveadm user utente                        # Info utente
doveadm mailbox list -u utente            # Lista mailbox
doveadm search -u utente mailbox INBOX   # Cerca messaggi
doveadm quota get -u utente              # Quota utilizzata
```

### Spam filtering

```bash
# SpamAssassin — filtro anti-spam basato su regole e punteggi
sudo apt install spamassassin spamc

# /etc/spamassassin/local.cf
required_score 5.0                         # Soglia spam (5.0 default)
rewrite_header Subject [SPAM]              # Modifica oggetto se spam
report_safe 0                              # 0 = non allegare originale come MIME

# Abilitare Bayes (apprendimento)
use_bayes 1
bayes_auto_learn 1
bayes_auto_learn_threshold_spam 6.0
bayes_auto_learn_threshold_nonspam -1.0

# Network tests
skip_rbl_checks 0                          # Usa RBL
dns_available yes

# Whitelist/blacklist
whitelist_from *@example.com
blacklist_from spam@evil.com

sudo systemctl enable --now spamassassin

# Integrare con Postfix tramite spamass-milter
sudo apt install spamass-milter

# /etc/postfix/main.cf
smtpd_milters = inet:localhost:12301, inet:localhost:54321, unix:/var/spool/postfix/spamass/spamass.sock

# Alternativa: integrazione via Dovecot Sieve per filtraggio lato server
# /etc/dovecot/conf.d/90-sieve.conf
plugin {
    sieve = file:~/sieve;active=~/.dovecot.sieve
    sieve_default = /etc/dovecot/sieve/default.sieve
}

# /etc/dovecot/sieve/default.sieve
require ["fileinto"];
if header :contains "X-Spam-Flag" "YES" {
    fileinto "Junk";
    stop;
}

# Compilare sieve
sievec /etc/dovecot/sieve/default.sieve

# Training SpamAssassin
sa-learn --spam /path/to/spam/folder       # Insegna spam
sa-learn --ham /path/to/ham/folder         # Insegna ham (non-spam)
```

---

## Proxy Server: Squid

Squid è un proxy HTTP/HTTPS con caching, usato per controllo accessi, caching, e monitoring del traffico web.

### Configurazione base Squid

```bash
sudo apt install squid

# File di configurazione principale
/etc/squid/squid.conf

# /etc/squid/squid.conf — configurazione base
# Porte
http_port 3128                             # Porta proxy standard

# ACL di base (ordine importante — prima definire, poi applicare)
acl localnet src 10.0.0.0/8
acl localnet src 172.16.0.0/12
acl localnet src 192.168.0.0/16
acl SSL_ports port 443
acl Safe_ports port 80          # HTTP
acl Safe_ports port 443         # HTTPS
acl Safe_ports port 21          # FTP
acl Safe_ports port 70          # Gopher
acl Safe_ports port 210         # WAIS
acl Safe_ports port 1025-65535  # Porte alte
acl Safe_ports port 280         # HTTP-mgmt
acl Safe_ports port 488         # GSS-HTTP
acl Safe_ports port 591         # FileMaker
acl Safe_ports port 777         # Multiling HTTP
acl CONNECT method CONNECT

# Regole di accesso (ordine importante)
http_access deny !Safe_ports
http_access deny CONNECT !SSL_ports
http_access allow localhost manager
http_access deny manager
http_access allow localnet
http_access allow localhost
http_access deny all

# DNS
dns_nameservers 192.168.1.10 192.168.1.11

# Identità
visible_hostname proxy.example.com

# Logging
access_log daemon:/var/log/squid/access.log squid
cache_log /var/log/squid/cache.log
cache_store_log /var/log/squid/store.log

# Amministrazione
cache_mgr admin@example.com

sudo systemctl enable --now squid

# Ricaricare configurazione
sudo squid -k reconfigure

# Verificare
sudo squid -k parse                        # Controlla sintassi
curl -x http://proxy.example.com:3128 http://example.com
```

### Transparent proxy

Proxy trasparente — intercetta traffico HTTP senza configurare i client. Richiede redirect iptables/nftables.

```bash
# /etc/squid/squid.conf — porta intercept
http_port 3128
http_port 3129 intercept                   # Porta per traffic intercept

# Redirect iptables — tutto il traffico porta 80 viene inviato a Squid
sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 \
    -j REDIRECT --to-port 3129
sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 \
    -s 192.168.1.70 -j ACCEPT              # Escludere il proxy stesso

# NOTA: il transparent proxy funziona SOLO per HTTP.
# HTTPS non può essere intercettato in modo trasparente senza
# man-in-the-middle (ssl-bump), che richiede CA interna e
# distribuzione certificato a tutti i client.
```

### Caching {#caching-squid}

```bash
# /etc/squid/squid.conf — configurazione cache

# Cache in memoria
cache_mem 512 MB                           # RAM per oggetti hot
maximum_object_size_in_memory 4 MB

# Cache su disco
cache_dir ufs /var/spool/squid 10000 16 256
# ufs = tipo storage
# 10000 = 10GB di cache
# 16 = directory primo livello
# 256 = directory secondo livello

maximum_object_size 100 MB                 # Max dimensione oggetto in cache
minimum_object_size 0 KB

# Refresh patterns — quando ricaricare dalla sorgente
refresh_pattern ^ftp:           1440    20%     10080
refresh_pattern ^gopher:        1440    0%      1440
refresh_pattern -i (/cgi-bin/|\?) 0     0%      0
refresh_pattern .               0       20%     4320

# Cache peer — hierarchy (opzionale)
# cache_peer parent-proxy.example.com parent 3128 0 no-query

# Monitoraggio cache
sudo squidclient -h localhost cache_object://localhost/info
sudo squidclient -h localhost cache_object://localhost/counters
sudo squidclient -h localhost cache_object://localhost/mem
sudo squidclient -h localhost cache_object://localhost/utilization

# Svuotare cache
sudo squid -k shutdown
sudo rm -rf /var/spool/squid/*
sudo squid -z                              # Ricreare struttura cache
sudo systemctl start squid
```

### ACL Squid

```bash
# ACL avanzate per controllo accessi granulare

# Blocco siti
acl blocked_sites dstdomain .facebook.com .twitter.com .tiktok.com
http_access deny blocked_sites

# Blocco per URL regex
acl blocked_urls url_regex -i gambling betting casino porn
http_access deny blocked_urls

# Blocco per tipo MIME
acl blocked_types rep_mime_type -i video/
http_access deny blocked_types

# Fasce orarie
acl work_hours time MTWHF 08:00-18:00
acl lunch_break time MTWHF 12:30-13:30

# Social media solo in pausa pranzo
http_access allow lunch_break blocked_sites localnet
http_access deny work_hours blocked_sites

# Limiti dimensione download
reply_body_max_size 100 MB all

# Autenticazione utenti (LDAP)
auth_param basic program /usr/lib/squid/basic_ldap_auth \
    -b "dc=example,dc=com" \
    -f "uid=%s" \
    -h ldap.example.com
auth_param basic children 5
auth_param basic realm Proxy Authentication
auth_param basic credentialsttl 1 hour

acl authenticated proxy_auth REQUIRED
http_access allow authenticated
http_access deny all

# ACL basata su file esterno
acl whitelist_domains dstdomain "/etc/squid/whitelist.txt"
http_access allow whitelist_domains
```

### HTTPS e considerazioni di sicurezza

```bash
# Squid e HTTPS — opzioni disponibili:

# 1. CONNECT tunnel (default) — Squid non ispeziona il contenuto HTTPS
#    Squid vede solo il dominio (via SNI), non il contenuto.
#    Sicuro, nessuna CA necessaria.
acl allowed_ssl_sites dstdomain .example.com
http_access allow CONNECT allowed_ssl_sites
http_access deny CONNECT all

# 2. SSL Bump / HTTPS inspection — Squid decifra e re-cifra il traffico
#    RICHIEDE: CA interna, distribuzione certificato CA a tutti i client,
#    policy chiara e CONSENSO degli utenti.
#    Implicazioni legali e di privacy significative.

# Configurazione SSL Bump (solo se policy lo permette)
# http_port 3128 ssl-bump cert=/etc/squid/ssl/squid-ca.pem \
#     generate-host-certificates=on dynamic_cert_mem_cache_size=4MB
#
# sslcrtd_program /usr/lib/squid/security_file_certgen -s /var/lib/squid/ssl_db -M 4MB
#
# acl step1 at_step SslBump1
# ssl_bump peek step1
# ssl_bump bump all

# RACCOMANDAZIONE: preferire il CONNECT tunnel.
# SSL Bump solo se c'è un requisito di sicurezza specifico (DLP, compliance)
# e gli utenti sono informati e hanno dato il consenso.
```

---

## RADIUS: FreeRADIUS

FreeRADIUS è il server RADIUS open source più diffuso. Usato per autenticazione di rete (Wi-Fi 802.1X, VPN, switch port access).

### Installazione e configurazione {#installazione-e-configurazione-radius}

```bash
# Installazione
sudo apt install freeradius freeradius-utils freeradius-ldap

# File di configurazione principali
/etc/freeradius/3.0/radiusd.conf          # Config principale
/etc/freeradius/3.0/clients.conf          # Client NAS (switch, AP, VPN)
/etc/freeradius/3.0/users                 # Utenti locali (test/fallback)
/etc/freeradius/3.0/mods-enabled/         # Moduli abilitati
/etc/freeradius/3.0/sites-enabled/        # Virtual server abilitati

# /etc/freeradius/3.0/clients.conf — definire client NAS
client switch-core {
    ipaddr = 192.168.1.250
    secret = shared_secret_forte_qui        # DEVE essere forte e unico per client
    shortname = switch-core
    nas_type = other
}

client ap-wifi {
    ipaddr = 192.168.1.240
    secret = altro_secret_forte
    shortname = ap-wifi
    nas_type = other
}

client vpn-server {
    ipaddr = 192.168.1.200
    secret = vpn_radius_secret
    shortname = vpn-gateway
}

# Subnet intera (per molti AP)
client wifi-subnet {
    ipaddr = 192.168.2.0/24
    secret = wifi_shared_secret
    shortname = wifi-aps
}

# /etc/freeradius/3.0/users — utenti locali (test)
testuser  Cleartext-Password := "test_password"
    Reply-Message := "Hello, %{User-Name}",
    Framed-IP-Address = 10.0.0.100

# Integrazione LDAP — abilitare modulo
cd /etc/freeradius/3.0/mods-enabled
sudo ln -s ../mods-available/ldap ldap

# /etc/freeradius/3.0/mods-available/ldap
ldap {
    server = "ldaps://ldap.example.com"
    base_dn = "dc=example,dc=com"
    identity = "cn=radius-bind,ou=Services,dc=example,dc=com"
    password = "bind_password"

    user {
        base_dn = "${..base_dn}"
        filter = "(uid=%{%{Stripped-User-Name}:-%{User-Name}})"
    }

    group {
        base_dn = "${..base_dn}"
        filter = "(objectClass=posixGroup)"
        membership_attribute = "memberUid"
    }

    tls {
        ca_file = /etc/ssl/certs/ca-certificates.crt
        require_cert = "demand"
    }
}

# Avviare in modalità debug (SEMPRE per primo test)
sudo freeradius -X

# Test autenticazione
radtest testuser test_password localhost 0 testing123

# Produzione
sudo systemctl enable --now freeradius

# Accounting — log accessi
# /etc/freeradius/3.0/mods-available/detail
# Configurare per logging dettagliato in /var/log/freeradius/radacct/
```

### Integrazione 802.1X

802.1X è lo standard per autenticazione port-based su reti wired e wireless. FreeRADIUS fornisce il backend di autenticazione.

```bash
# Componenti 802.1X:
# Supplicant (client) → Authenticator (switch/AP) → Authentication Server (RADIUS)

# EAP configuration — /etc/freeradius/3.0/mods-available/eap
eap {
    default_eap_type = peap                # PEAP per wireless
    timer_expire = 60
    max_sessions = ${max_requests}

    tls-config tls-common {
        private_key_password = whatever
        private_key_file = /etc/freeradius/3.0/certs/server.key
        certificate_file = /etc/freeradius/3.0/certs/server.pem
        ca_file = /etc/freeradius/3.0/certs/ca.pem
        dh_file = ${certdir}/dh
        ca_path = ${cadir}
        tls_min_version = "1.2"
    }

    peap {
        default_eap_type = mschapv2
    }

    ttls {
        default_eap_type = mschapv2
    }
}

# Generare certificati per EAP-TLS
cd /etc/freeradius/3.0/certs
sudo make

# Configurazione switch per 802.1X (esempio Cisco IOS)
# aaa new-model
# aaa authentication dot1x default group radius
# radius-server host 192.168.1.10 auth-port 1812 acct-port 1813 key shared_secret
# interface GigabitEthernet0/1
#   dot1x port-control auto

# Configurazione AP Wi-Fi (esempio generico)
# SSID: Corporate-WiFi
# Security: WPA2-Enterprise
# RADIUS Server: 192.168.1.10
# RADIUS Port: 1812
# RADIUS Secret: shared_secret

# VLAN assignment basato su gruppo RADIUS
# /etc/freeradius/3.0/policy.d/vlan_assignment
# Se utente è nel gruppo "Engineering" → VLAN 100
# Se utente è nel gruppo "Management" → VLAN 200
# /etc/freeradius/3.0/users
DEFAULT Ldap-Group == "Engineering"
    Tunnel-Type = VLAN,
    Tunnel-Medium-Type = IEEE-802,
    Tunnel-Private-Group-Id = "100"

DEFAULT Ldap-Group == "Management"
    Tunnel-Type = VLAN,
    Tunnel-Medium-Type = IEEE-802,
    Tunnel-Private-Group-Id = "200"
```

---

## VPN: WireGuard e OpenVPN

Panoramica rapida. Per configurazione approfondita, fare riferimento al **Modulo 32 — VPN**.

```bash
# --- WireGuard ---
# Moderno, veloce, kernel-space, configurazione minimale.

sudo apt install wireguard

# Generare chiavi
wg genkey | tee /etc/wireguard/server_private.key | wg pubkey > /etc/wireguard/server_public.key
chmod 600 /etc/wireguard/server_private.key

# /etc/wireguard/wg0.conf — server
[Interface]
Address = 10.100.0.1/24
ListenPort = 51820
PrivateKey = <chiave_privata_server>
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]
PublicKey = <chiave_pubblica_client>
AllowedIPs = 10.100.0.2/32

# Avviare
sudo wg-quick up wg0
sudo systemctl enable wg-quick@wg0

# Stato
sudo wg show

# --- OpenVPN ---
# Maturo, supporto ampio, TLS-based, user-space.

sudo apt install openvpn easy-rsa

# Configurazione base server (riassunto)
# 1. Creare PKI con easy-rsa
# 2. Generare CA, certificato server, DH parameters
# 3. Configurare /etc/openvpn/server.conf
# 4. Generare certificati per ogni client

# Confronto rapido:
# WireGuard: più veloce, più semplice, kernel-space, stato-less
# OpenVPN: più funzionalità, più configurabile, supporto proxy, user-space

# Per dettagli completi → Modulo 32 — VPN
```

### WireGuard — Topologie avanzate {#wireguard-avanzato}

Oltre al classico client-server, WireGuard supporta topologie site-to-site e hub-and-spoke per interconnettere reti geograficamente distribuite.

```bash
# === Site-to-Site VPN ===
# Collegare due reti (Sede A: 10.0.1.0/24, Sede B: 10.0.2.0/24)
# Tunnel via rete overlay 10.100.0.0/24

# --- Sede A (10.0.1.0/24) ---
# /etc/wireguard/wg0.conf
[Interface]
PrivateKey = <chiave_privata_sede_A>
Address = 10.100.0.1/24
ListenPort = 51820
# MTU ottimale — 1420 per IPv4 over WireGuard, 1400 se behind NAT
MTU = 1420

# Abilitare IP forwarding
PostUp = sysctl -w net.ipv4.ip_forward=1
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT
PostUp = iptables -A FORWARD -o wg0 -j ACCEPT
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT
PostDown = iptables -D FORWARD -o wg0 -j ACCEPT

[Peer]
PublicKey = <chiave_pubblica_sede_B>
Endpoint = sede-b.example.com:51820
# AllowedIPs include sia l'IP tunnel che la rete remota
AllowedIPs = 10.100.0.2/32, 10.0.2.0/24
PersistentKeepalive = 25

# --- Sede B (10.0.2.0/24) ---
# /etc/wireguard/wg0.conf
[Interface]
PrivateKey = <chiave_privata_sede_B>
Address = 10.100.0.2/24
ListenPort = 51820
MTU = 1420

PostUp = sysctl -w net.ipv4.ip_forward=1
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT
PostUp = iptables -A FORWARD -o wg0 -j ACCEPT
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT
PostDown = iptables -D FORWARD -o wg0 -j ACCEPT

[Peer]
PublicKey = <chiave_pubblica_sede_A>
Endpoint = sede-a.example.com:51820
AllowedIPs = 10.100.0.1/32, 10.0.1.0/24
PersistentKeepalive = 25

# Attivare su entrambi i nodi
sudo systemctl enable --now wg-quick@wg0
# Verificare connettività inter-sede
ping -c 3 10.0.2.1   # Da Sede A verso rete Sede B
```

```bash
# === Hub-and-Spoke ===
# Hub centrale (data center) connette N sedi spoke
# Ogni spoke comunica con le altre sedi SOLO attraverso l'hub

# --- Hub (server centrale) ---
# /etc/wireguard/wg0.conf
[Interface]
PrivateKey = <chiave_privata_hub>
Address = 10.100.0.1/24
ListenPort = 51820
MTU = 1420

PostUp = sysctl -w net.ipv4.ip_forward=1
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT
PostUp = iptables -A FORWARD -o wg0 -j ACCEPT
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT
PostDown = iptables -D FORWARD -o wg0 -j ACCEPT

# Spoke 1 — Filiale Milano (10.0.10.0/24)
[Peer]
PublicKey = <pubkey_spoke1>
AllowedIPs = 10.100.0.2/32, 10.0.10.0/24
PersistentKeepalive = 25

# Spoke 2 — Filiale Roma (10.0.20.0/24)
[Peer]
PublicKey = <pubkey_spoke2>
AllowedIPs = 10.100.0.3/32, 10.0.20.0/24
PersistentKeepalive = 25

# Spoke 3 — Filiale Napoli (10.0.30.0/24)
[Peer]
PublicKey = <pubkey_spoke3>
AllowedIPs = 10.100.0.4/32, 10.0.30.0/24
PersistentKeepalive = 25

# --- Spoke (es. Milano) ---
[Interface]
PrivateKey = <chiave_privata_spoke1>
Address = 10.100.0.2/24
MTU = 1420

PostUp = sysctl -w net.ipv4.ip_forward=1

[Peer]
PublicKey = <pubkey_hub>
Endpoint = hub.example.com:51820
# AllowedIPs include tutte le reti raggiungibili via hub
AllowedIPs = 10.100.0.0/24, 10.0.10.0/24, 10.0.20.0/24, 10.0.30.0/24
PersistentKeepalive = 25
```

### WireGuard — wg-easy (gestione via Web UI) {#wg-easy}

wg-easy è un container Docker che fornisce un'interfaccia web per gestire peer WireGuard: aggiungere/rimuovere client, generare QR code per configurazione mobile, monitorare connessioni attive.

```bash
# Deploy con Docker Compose
# docker-compose.yml
version: "3.8"
services:
  wg-easy:
    image: ghcr.io/wg-easy/wg-easy:latest
    container_name: wg-easy
    environment:
      - LANG=it                           # Interfaccia in italiano
      - WG_HOST=vpn.example.com           # FQDN o IP pubblico del server
      - PASSWORD_HASH=$$2a$$12$$...       # bcrypt hash della password admin
      # Generare: docker run -it ghcr.io/wg-easy/wg-easy wgpw 'MyPassword'
      - WG_PORT=51820                     # Porta WireGuard
      - WG_DEFAULT_DNS=1.1.1.1,9.9.9.9   # DNS per i client
      - WG_DEFAULT_ADDRESS=10.8.0.x       # Range indirizzi client
      - WG_ALLOWED_IPS=0.0.0.0/0,::/0    # Split tunnel: specificare subnet
      - WG_PERSISTENT_KEEPALIVE=25
      - UI_TRAFFIC_STATS=true             # Statistiche traffico per peer
    volumes:
      - ./wg-easy:/etc/wireguard
    ports:
      - "51820:51820/udp"                 # WireGuard
      - "51821:51821/tcp"                 # Web UI
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    sysctls:
      - net.ipv4.ip_forward=1
      - net.ipv4.conf.all.src_valid_mark=1
    restart: unless-stopped

# Avviare
docker compose up -d

# Web UI accessibile su http://<server>:51821
# Funzionalità: aggiunta peer con un click, QR code per mobile,
# download configurazione, toggle peer on/off, statistiche traffico

# === Best practices operative WireGuard ===
# - Rotazione chiavi: generare nuove keypair ogni 12 mesi
# - Monitoraggio: wg show (stato peer, handshake, traffico)
# - MTU: 1420 standard, 1400 se behind NAT/PPPoE, 1280 minimo IPv6
# - Logging: WireGuard è volutamente silenzioso — abilitare debug solo se necessario:
#   echo module wireguard +p > /sys/kernel/debug/dynamic_debug/control
# - Backup: esportare /etc/wireguard/ — contiene le chiavi private
```

---

## mDNS e Avahi

mDNS (Multicast DNS) permette la risoluzione nomi e la scoperta servizi su reti locali senza un server DNS dedicato. Avahi è l'implementazione Linux di mDNS/DNS-SD (compatibile con Bonjour di Apple).

```bash
# Installazione
sudo apt install avahi-daemon avahi-utils libnss-mdns

# Il servizio avahi-daemon parte automaticamente
sudo systemctl enable --now avahi-daemon

# Configurazione — /etc/avahi/avahi-daemon.conf
[server]
host-name=server1                          # Nome .local del host
domain-name=local
use-ipv4=yes
use-ipv6=yes
allow-interfaces=eth0                      # Limitare a interfacce specifiche
deny-interfaces=docker0                    # Escludere interfacce

[publish]
publish-addresses=yes
publish-hinfo=no                           # Non pubblicare info hardware
publish-workstation=no

[reflector]
enable-reflector=no                        # Non fare riflettore tra interfacce

# NSS — /etc/nsswitch.conf
hosts: files mdns4_minimal [NOTFOUND=return] dns mdns4

# Scoperta servizi sulla rete locale
avahi-browse -a                            # Tutti i servizi
avahi-browse -at                           # Tutti i servizi (con TXT record)
avahi-browse _http._tcp                    # Server web
avahi-browse _ssh._tcp                     # Server SSH
avahi-browse _smb._tcp                     # Share Samba

# Risolvere nomi .local
avahi-resolve -n server1.local             # Nome → IP
avahi-resolve -a 192.168.1.10              # IP → Nome

# Ping via mDNS
ping server1.local

# Pubblicare servizio personalizzato
# /etc/avahi/services/my-webapp.service
<?xml version="1.0" standalone='no'?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name>My Web Application</name>
  <service>
    <type>_http._tcp</type>
    <port>8080</port>
    <txt-record>path=/app</txt-record>
  </service>
</service-group>

# Il servizio appare automaticamente nella rete locale
```

---

## Strumenti di troubleshooting rete

### DNS — dig, nslookup, host

```bash
# dig — il più completo per DNS troubleshooting
dig example.com                            # Query A record
dig example.com MX                         # Query MX
dig example.com ANY                        # Tutti i record
dig example.com +short                     # Solo risposta, formato compatto
dig example.com +trace                     # Traccia la risoluzione dalla root
dig @8.8.8.8 example.com                  # Query a server specifico
dig example.com AXFR @ns1.example.com     # Zone transfer
dig example.com +dnssec                   # Mostra record DNSSEC
dig -x 192.168.1.100                      # Reverse lookup (PTR)
dig example.com +norecurse                # Non usare recursion
dig example.com +tcp                      # Forza TCP (vs UDP)
dig +qr example.com                       # Mostra query inviata

# Batch query
dig -f domains.txt +short                  # Query multipli da file

# nslookup — più semplice, interattivo
nslookup example.com
nslookup -type=MX example.com
nslookup example.com 8.8.8.8              # Specifica server

# nslookup interattivo
nslookup
> server 8.8.8.8
> set type=MX
> example.com
> exit

# host — il più sintetico
host example.com                           # A record
host -t MX example.com                    # MX record
host -t AAAA example.com                  # IPv6
host -a example.com                       # Tutti i record
host 192.168.1.100                        # Reverse
```

### Connessioni — ss, netstat

```bash
# ss — sostituto moderno di netstat (più veloce)
ss -tuln                                   # TCP/UDP listening con numeri porta
ss -tulnp                                  # Come sopra + processo
ss -t state established                    # Connessioni TCP stabilite
ss -t state time-wait                      # Connessioni in TIME_WAIT
ss -s                                      # Sommario statistiche
ss -i                                      # Info dettagliate (RTT, congestion window)
ss dst 192.168.1.100                      # Connessioni verso IP specifico
ss sport = :80                            # Connessioni da porta sorgente 80
ss dport = :443                           # Connessioni verso porta 443
ss -o state established '( dport = :22 )' # SSH stabilite con timer

# netstat — legacy ma ancora utile
netstat -tuln                              # TCP/UDP listening
netstat -tulnp                             # Con PID/processo
netstat -an                                # Tutte le connessioni
netstat -rn                                # Routing table
netstat -s                                 # Statistiche per protocollo
netstat -i                                 # Statistiche interfacce
```

### Cattura traffico — tcpdump, nmap

```bash
# tcpdump — cattura pacchetti da linea di comando
sudo tcpdump -i eth0                       # Cattura tutto su eth0
sudo tcpdump -i eth0 port 53              # Solo DNS
sudo tcpdump -i eth0 port 80 or port 443  # HTTP/HTTPS
sudo tcpdump -i eth0 host 192.168.1.100   # Traffico da/verso host
sudo tcpdump -i eth0 src 192.168.1.100    # Solo sorgente
sudo tcpdump -i eth0 dst 192.168.1.100    # Solo destinazione
sudo tcpdump -i eth0 -n                    # Non risolvere nomi (più veloce)
sudo tcpdump -i eth0 -c 100               # Cattura 100 pacchetti e stop
sudo tcpdump -i eth0 -w /tmp/capture.pcap # Salva in file PCAP
sudo tcpdump -r /tmp/capture.pcap         # Leggi file PCAP
sudo tcpdump -i eth0 -A port 80           # Mostra contenuto ASCII (solo HTTP)
sudo tcpdump -i eth0 -X port 53           # Mostra hex + ASCII
sudo tcpdump -i eth0 'tcp[tcpflags] & (tcp-syn) != 0'  # Solo pacchetti SYN

# nmap — network scanner
nmap 192.168.1.0/24                        # Scan subnet (host discovery)
nmap -sP 192.168.1.0/24                   # Ping scan only
nmap -sV 192.168.1.100                    # Scan con version detection
nmap -sS 192.168.1.100                    # SYN scan (stealth)
nmap -p 1-65535 192.168.1.100             # Scan tutte le porte
nmap -p 22,80,443 192.168.1.100           # Porte specifiche
nmap -O 192.168.1.100                     # OS detection
nmap -A 192.168.1.100                     # Aggressive scan (OS + version + script + trace)
nmap --script vuln 192.168.1.100          # Vulnerability scan
nmap -sU -p 53,67,123 192.168.1.100      # Scan porte UDP

# ATTENZIONE: nmap solo su reti di propria competenza o con autorizzazione esplicita
```

### Tracciamento percorso — mtr, traceroute

```bash
# mtr — combina traceroute + ping continuo
mtr example.com                            # Traccia interattiva
mtr -r -c 100 example.com                # Report mode, 100 pacchetti
mtr -r -c 50 --tcp -P 443 example.com    # Traccia TCP sulla porta 443
mtr -r -c 50 -n example.com              # No DNS resolution

# traceroute
traceroute example.com                     # Traccia con UDP (default)
traceroute -T example.com                 # Traccia con TCP
traceroute -I example.com                 # Traccia con ICMP
traceroute -p 443 example.com            # Porta specifica
traceroute -n example.com                 # No DNS resolution

# tracepath — alternativa senza privilegi root
tracepath example.com
```

### Altre utility

```bash
# curl — test HTTP/HTTPS
curl -I https://example.com                # Solo header
curl -v https://example.com                # Verbose (mostra handshake TLS)
curl -o /dev/null -w "%{time_total}\n" https://example.com   # Solo tempo risposta
curl --resolve example.com:443:192.168.1.100 https://example.com  # Override DNS

# openssl — test TLS/SSL
openssl s_client -connect example.com:443 -servername example.com
openssl s_client -connect mail.example.com:993           # Test IMAPS
openssl s_client -connect mail.example.com:587 -starttls smtp  # Test SMTP StartTLS
openssl x509 -in cert.pem -text -noout                   # Dettagli certificato

# arp — tabella ARP
arp -a                                     # Tabella ARP
ip neigh show                              # Alternativa moderna

# ethtool — info interfaccia fisica
ethtool eth0                               # Velocità, duplex, link
ethtool -S eth0                            # Statistiche hardware

# iperf3 — bandwidth test
iperf3 -s                                  # Server
iperf3 -c 192.168.1.100                   # Client (test verso server)
iperf3 -c 192.168.1.100 -R               # Reverse (download test)
iperf3 -c 192.168.1.100 -P 4             # 4 stream paralleli
```

---

## Matrice decisionale servizi di rete

| Esigenza | Servizio consigliato | Alternativa | Note |
|---|---|---|---|
| DNS autoritativo | BIND9 | Knot DNS | BIND9 più documentato, Knot più performante |
| DNS resolver/caching | Unbound | BIND9 | Unbound più leggero e sicuro per solo resolving |
| DNS + DHCP piccola rete | dnsmasq | — | Ideale per <50 host, lab, sviluppo |
| DNS service discovery | CoreDNS | Consul DNS | Modulare, plugin etcd, nativo Kubernetes |
| DHCP enterprise | Kea | ISC dhcpd (legacy) | Kea è il successore ufficiale con API REST |
| DHCP HA | Kea con HA hooks | ISC dhcpd failover | Kea HA è più robusto |
| NTP | chrony | ntpd | chrony per 99% dei casi |
| File sharing Windows | Samba | — | Unica opzione per integrazione Windows |
| File sharing Linux | NFS v4 | Samba | NFS nativo, più performante tra Linux |
| Autenticazione centralizzata | sssd + LDAP | Winbind + AD | sssd più moderno e flessibile |
| Directory service | OpenLDAP | 389 DS | OpenLDAP più diffuso, 389 DS ha GUI migliore |
| Mail server | Postfix + Dovecot | — | Standard de facto |
| Proxy HTTP | Squid | — | Maturo, ben documentato |
| Auth rete (802.1X) | FreeRADIUS | — | Standard de facto |
| VPN moderna | WireGuard | OpenVPN | WireGuard per nuove installazioni |
| VPN legacy/complessa | OpenVPN | WireGuard | OpenVPN per compatibilità, proxy traverse |
| Trasferimento file | SFTP (SSH) | SCP, rsync | Mai FTP in chiaro |
| Service discovery LAN | Avahi (mDNS) | — | Automatico su rete locale |

---

## Best Practices

1. **SFTP > FTP**: usare sempre SFTP (SSH) al posto di FTP. FTP trasmette credenziali in chiaro. Se FTP è obbligatorio, configurare vsftpd con TLS (FTPS)
2. **DNS secondario**: avere sempre almeno due server DNS autoritativi. Se il primario cade, il secondario risponde. Usare TSIG per autenticare i trasferimenti zona
3. **NTP su ogni server**: la sincronizzazione oraria è critica per: correlazione log, Kerberos, TLS, database distribuiti, cluster. Tolleranza massima accettabile: 100ms
4. **DHCP lease statici per infrastruttura**: usare DHCP per workstation, IP statici (o reservation DHCP) per server, stampanti, switch, AP
5. **LDAP con TLS**: mai LDAP in chiaro. LDAPS (porta 636) o StartTLS obbligatorio. Le password transitano sulla rete
6. **Monitorare la coda mail**: una coda Postfix che cresce indica problemi (relay bloccato, DNS down, destinatario rifiuta). Alertare se > 100 messaggi in coda
7. **Email authentication**: configurare SPF, DKIM e DMARC su tutti i domini che inviano email. Senza, i messaggi finiscono in spam o vengono rifiutati
8. **Samba: SMB3 minimo**: disabilitare SMB1 (vulnerabilità note: EternalBlue/WannaCry). Forzare `server min protocol = SMB2_10` in produzione
9. **NFS: root_squash sempre**: non usare `no_root_squash` salvo necessità specifiche (backup, setup iniziale). Root di un client non deve avere root sul server NFS
10. **DNSSEC**: abilitare almeno la validazione DNSSEC sui resolver interni. La firma delle zone è consigliata per zone pubbliche
11. **Proxy non è firewall**: Squid controlla traffico HTTP/HTTPS ma non sostituisce un firewall. Usare entrambi. Non intercettare HTTPS senza policy chiare
12. **RADIUS secrets forti**: ogni client NAS (switch, AP) deve avere un secret RADIUS unico e forte (almeno 16 caratteri). Mai usare "testing123" in produzione
13. **Separare servizi**: un server = un servizio principale. Non mettere DNS, DHCP, mail e proxy sullo stesso host in produzione
14. **Backup configurazioni**: tutti i file di configurazione dei servizi sotto version control (git). Testare restore periodicamente
15. **Firewall per servizio**: aprire solo le porte necessarie per ogni servizio. Default deny. Documentare ogni regola

---

## Troubleshooting

**"DNS non risolve"**
`named-checkconf` e `named-checkzone` per errori di configurazione. `journalctl -u bind9` per log. Porta 53/TCP e 53/UDP aperta nel firewall? `dig @localhost domain` per testare direttamente. Se il server è Unbound: `unbound-checkconf` e `journalctl -u unbound`. Verificare `/etc/resolv.conf` — punta al server giusto?

**"DHCP non assegna IP"**
L'interfaccia in `/etc/default/isc-dhcp-server` è corretta? Il server è sulla stessa subnet dei client? `journalctl -u isc-dhcp-server`. Firewall: porta 67/UDP e 68/UDP aperte? Se su subnet diversa, c'è un relay agent configurato? `dhcpd -t` per testare configurazione.

**"NTP: offset alto"**
`chronyc tracking` per vedere l'offset. Se > 1 secondo: `chronyc makestep` (se permesso dalla config). Verificare che i server NTP siano raggiungibili: `chronyc sources -v`. Firewall: porta 123/UDP aperta? Se offset persiste, controllare che l'hardware clock non sia troppo impreciso (`hwclock --show`).

**"Email non inviata"**
`mailq` per la coda. `tail -50 /var/log/mail.log` per errori. Problemi comuni: DNS (MX record non risolvibile), firewall (porta 25/587), autenticazione smarthost fallita, SPF/DKIM/DMARC del dominio destinatario rifiuta il messaggio. `postconf -n` per vedere configurazione attiva.

**"Samba share non accessibile"**
`testparm` per verificare smb.conf. `smbstatus` per connessioni attive. Firewall: porte 139/TCP, 445/TCP aperte? `smbclient -L //server -U utente` per testare. Se AD: `net ads testjoin` — il join è ancora valido? `wbinfo -t` per testare trust. Permessi filesystem: l'utente ha i permessi POSIX sulla directory?

**"NFS mount fallisce"**
`showmount -e nfs-server` per vedere esportazioni (NFSv3). `exportfs -v` sul server per verificare. Firewall: porta 2049/TCP aperta? `mount -v` per output verboso. NFSv4: il dominio in `/etc/idmapd.conf` corrisponde su client e server? Kerberos: `klist` per verificare ticket valido.

**"LDAP: bind fallisce"**
`ldapsearch -x -H ldap://localhost -D "cn=admin,dc=example,dc=com" -W` — password corretta? `journalctl -u slapd` per errori. TLS: certificato valido? `openssl s_client -connect ldap.example.com:636` per testare. ACL: l'utente ha permessi di lettura? Verificare con `sudo ldapsearch -Y EXTERNAL -H ldapi:/// -b "olcDatabase={1}mdb,cn=config" olcAccess`.

**"sssd non funziona"**
`/etc/sssd/sssd.conf` ha permessi 600? `sss_cache -E` per svuotare cache. `journalctl -u sssd` per errori. `getent passwd utente_ldap` per verificare. Se LDAP: il bind DN in sssd.conf è corretto e ha accesso? `sss_debuglevel 6` per debug dettagliato.

**"Squid: access denied"**
`tail -f /var/log/squid/access.log` — quale ACL rifiuta? L'ordine delle ACL in squid.conf è corretto? (prima match vince). `squid -k parse` per errori di sintassi. Il client usa il proxy corretto? `curl -x http://proxy:3128 http://example.com` per testare.

**"FreeRADIUS: autenticazione fallisce"**
`freeradius -X` per debug (fermare il servizio prima). `radtest utente password localhost 0 testing123` per test locale. Log: `/var/log/freeradius/radius.log`. Shared secret uguale su client e server? Certificati EAP validi? `eapol_test` per test 802.1X.

**"WireGuard: peer non raggiungibile"**
`sudo wg show` per stato interfaccia e peer. Firewall: porta UDP configurata (default 51820) aperta? Le chiavi pubbliche sono corrette (scambiate)? `AllowedIPs` corretti? IP forwarding abilitato se serve routing? `sudo ip route` per verificare routing.

**"Avahi/mDNS: host .local non risolvibile"**
`avahi-daemon --check` per verificare stato. Firewall: porta 5353/UDP (multicast) aperta? `nsswitch.conf` include `mdns4`? L'interfaccia è elencata in `allow-interfaces` di avahi-daemon.conf? `avahi-browse -a` per verificare visibilità servizi.

**"Postfix: relay access denied"**
Il dominio destinatario è in `mydestination` o il mittente è autenticato/in `mynetworks`? `smtpd_relay_restrictions` è configurato correttamente? Se relay esterno: `relayhost` è impostato? Credenziali in `sasl_passwd` corrette? `postmap` eseguito dopo modifica?

**"Dovecot: login fallisce"**
`doveconf -n` per configurazione attiva. `journalctl -u dovecot` per errori. TLS configurato? `disable_plaintext_auth = yes` richiede TLS — il client lo supporta? `doveadm auth test utente password` per test autenticazione.

**"NFS performance degradata"**
`nfsstat -c` e `nfsiostat` per statistiche. Buffer `rsize/wsize` troppo piccoli? Rete satura? `async` vs `sync` — usare `async` per performance ma con rischio dati. Numero thread NFS sufficiente? (`RPCNFSDCOUNT`). Latenza rete: `ping -c 100` per verificare.

**"DHCP failover: stato split-brain"**
`omshell` per verificare stato failover. Connettività tra i due server sulla porta 647/TCP? Clocks sincronizzati (NTP)? Se uno dei due era down troppo a lungo, potrebbe servire reset manuale del failover state.

**"DNS DNSSEC: validation failure"**
`delv @resolver example.com` per diagnostica DNSSEC. `dig example.com +dnssec +cd` per query senza validazione (confronto). Chiavi scadute? Record DS nel registrar corrisponde alla KSK attuale? `dnssec-verify` sulla zona.

**"Certificati TLS scaduti su servizi"**
`openssl s_client -connect host:porta` per verificare certificato. `openssl x509 -enddate -noout -in cert.pem` per scadenza. Automatizzare rinnovo con certbot/ACME. Monitorare scadenza con cron o strumenti dedicati (almeno 30 giorni prima).

**"Kea DHCP: lease non assegnati"**
`journalctl -u kea-dhcp4-server` per errori. Configurazione JSON valida? (`kea-dhcp4 -t /etc/kea/kea-dhcp4.conf`). API REST funzionante? `curl http://localhost:8000/ -d '{"command":"status-get"}'`. Pool esaurito? Verificare lease attivi.

**"Samba: trasferimento file lento"**
Verificare versione protocollo: `smbstatus -b` — se SMB1, forzare SMB3 (`server min protocol = SMB2_10`). SMB signing ha overhead ~10%: se la rete è fidata, valutare `server signing = desired` invece di `mandatory`. MTU mismatch: verificare `ip link show` su entrambi i lati. Multichannel: se il server ha più NIC, abilitare `server multi channel support = yes`. Verificare `aio read size` e `aio write size` (almeno 16384). Antivirus on-access scanning sulla share può degradare performance: escludere la directory share dallo scan real-time.

**"LDAP replicazione in ritardo"**
Sul consumer: `ldapsearch -x -H ldap://consumer -b "dc=example,dc=com" -s base contextCSN` e confrontare con il provider. Se il CSN del consumer è indietro, verificare connettività di rete verso il provider. Log: `journalctl -u slapd` — errori di bind del replicatore? ACL: il DN del replicatore (`cn=replicator`) ha permessi di lettura su tutte le entry? TLS: certificato del provider valido e non scaduto? Se replicazione interrotta da tempo, potrebbe servire re-inizializzare il consumer con `slapcat` dal provider e `slapadd` sul consumer.

---

## FAQ

**D: Meglio BIND9 o Unbound come resolver interno?**
R: Unbound per solo resolving/caching — più leggero, più sicuro, DNSSEC validazione nativa. BIND9 se serve anche funzionalità autoritativa sulla stessa macchina. In ambienti enterprise, architettura consigliata: BIND9 autoritativo per zone interne + Unbound come resolver ricorsivo che forward le zone interne a BIND9.

**D: ISC DHCP è ancora supportato?**
R: ISC DHCP è End of Life dal 2022. Funziona ancora ma non riceve più aggiornamenti di sicurezza. Per nuove installazioni usare Kea. Per installazioni esistenti, pianificare migrazione a Kea.

**D: Come migrare da ISC DHCP a Kea?**
R: Kea include lo strumento `kea-dhcp4-migrate` per convertire la configurazione. Procedura: (1) installare Kea in parallelo, (2) convertire config, (3) importare lease con `kea-admin`, (4) testare, (5) switch DNS/DHCP relay al nuovo server, (6) rimuovere ISC dhcpd.

**D: Posso usare Samba come Domain Controller?**
R: Samba può funzionare come AD DC per piccoli ambienti (<100 utenti). Per produzione enterprise, preferire Windows AD o FreeIPA. Samba come AD DC ha limitazioni: no Group Policy Management Console nativo, supporto GPO limitato, no Azure AD connect.

**D: NFSv3 o NFSv4?**
R: NFSv4 sempre per nuove installazioni. Vantaggi: singola porta (2049), supporto ACL, Kerberos nativo, stateful operation, migliore performance su WAN. NFSv3 solo per compatibilità con sistemi legacy.

**D: Come configurare NFS con automount per home directory?**
R: Usare autofs con wildcard map. In `/etc/auto.master`: `/home /etc/auto.home`. In `/etc/auto.home`: `* -rw,nfsvers=4 nfs-server:/home/&`. Ogni accesso a `/home/username` monta automaticamente la home directory dal server NFS.

**D: chrony o ntpd?**
R: chrony per il 99% dei casi. ntpd solo se serve: broadcast/multicast NTP, hardware reference clock con driver specifici ntpd, o compatibilità con software legacy che si aspetta ntpd. RHEL 8+, Ubuntu 18.04+ e la maggior parte delle distribuzioni moderne usano chrony come default.

**D: Come verificare che SPF, DKIM e DMARC funzionino?**
R: Inviare una email a un indirizzo Gmail o Outlook. Aprire il messaggio, visualizzare header completi, cercare `Authentication-Results`. Deve mostrare `spf=pass`, `dkim=pass`, `dmarc=pass`. Strumenti online: mxtoolbox.com, mail-tester.com.

**D: Squid può fare HTTPS inspection?**
R: Sì, tramite SSL Bump. Richiede: (1) CA interna, (2) distribuzione certificato CA a tutti i client, (3) compilazione Squid con `--with-openssl`. ATTENZIONE: implicazioni legali e di privacy. Necessario consenso degli utenti e policy aziendale chiara. Non usare per reti con dispositivi BYOD senza consenso.

**D: Come dimensionare la cache Squid?**
R: Regola empirica: `cache_mem` = 25% della RAM disponibile (non totale). `cache_dir` = spazio disco dedicato, almeno 10GB per rete media. Monitorare hit rate con `squidclient cache_object://localhost/counters`. Hit rate < 30% indica che la cache è troppo piccola o che il traffico è prevalentemente HTTPS (non cacheable).

**D: FreeRADIUS supporta MFA/2FA?**
R: Sì, tramite moduli: `rlm_otp` per TOTP/HOTP, integrazione con servizi esterni (Duo, Google Authenticator via PAM). Configurare come secondo fattore dopo PEAP/MSCHAPv2 o EAP-TLS.

**D: Come monitorare i servizi di rete?**
R: Prometheus + Grafana con exporter specifici: `bind_exporter` per BIND9, `unbound_exporter` per Unbound, `kea_exporter` per Kea DHCP, `chrony_exporter` per NTP, `postfix_exporter` per mail. Nagios/Icinga per check di disponibilità (porta aperta, servizio risponde). Per SNMP: `snmpd` su ogni server.

**D: Come proteggere un server DNS da attacchi DDoS?**
R: (1) Rate limiting in BIND9 (`rate-limit`), (2) Response Rate Limiting (RRL), (3) disabilitare recursion per client esterni, (4) `minimal-responses yes`, (5) firewall con rate limiting sulla porta 53, (6) servizio anti-DDoS upstream (per zone pubbliche). Non esporre resolver ricorsivi su Internet.

**D: Posso usare dnsmasq in produzione enterprise?**
R: Per reti piccole (<100 host) sì. Per enterprise con requisiti di HA, DNSSEC, trasferimenti zona, audit: no. dnsmasq non supporta DNSSEC signing, zone transfer, views, logging granulare. In quel caso usare BIND9/Unbound + Kea.

**D: Come ruotare le chiavi DNSSEC senza downtime?**
R: Procedura Double-Signature o Pre-Publish. Per ZSK: (1) generare nuova ZSK, (2) pubblicare DNSKEY della nuova (pre-publish), (3) attendere 2x TTL per propagazione, (4) firmare con nuova ZSK, (5) rimuovere vecchia dopo 2x TTL. Per KSK: simile ma serve aggiornare il record DS presso il registrar. BIND9 con `auto-dnssec maintain` e `inline-signing yes` gestisce la rotazione ZSK automaticamente.
