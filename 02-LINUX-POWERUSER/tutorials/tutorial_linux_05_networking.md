# Tutorial Linux 05 — Networking: ip, ss, netplan, iptables, NetworkManager

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** configurazione rete, troubleshooting, firewall, bonding, VLAN
> **Prerequisiti:** `tutorial_linux_04_systemd.md`
> **Durata stimata:** 14-18 ore

---

## Mappa concettuale

```
Networking Linux
│
├── Configurazione indirizzo
│   ├── ip addr/link/route — iproute2 (moderno)
│   ├── netplan — Ubuntu 18.04+
│   └── NetworkManager — desktop/server
│
├── Diagnostica
│   ├── ss — socket statistics (replace netstat)
│   ├── ping, traceroute, mtr
│   ├── nmap, netcat
│   └── tcpdump — packet capture
│
├── Firewall
│   ├── iptables / ip6tables
│   ├── nftables (moderno)
│   └── ufw — wrapper iptables
│
├── Funzioni avanzate
│   ├── Bonding (LACP, active-backup)
│   ├── VLAN (802.1Q)
│   └── Bridge (VM/container)
│
└── DNS
    ├── /etc/resolv.conf
    ├── systemd-resolved
    └── dnsmasq
```

---

# Parte A — iproute2: ip command

---

## A1. Gestione indirizzi e interfacce

```bash
# Lista interfacce
ip link show
ip link show eth0    # solo eth0

# Attiva/disattiva interfaccia
ip link set eth0 up
ip link set eth0 down

# Lista indirizzi IP
ip addr show
ip addr show eth0

# Aggiungi indirizzo temporaneo (perso al reboot)
ip addr add 192.168.1.100/24 dev eth0
ip addr add 10.0.0.50/16 dev eth0 label eth0:1   # alias

# Rimuovi indirizzo
ip addr del 192.168.1.100/24 dev eth0

# Tabella di routing
ip route show
# default via 192.168.1.1 dev eth0 proto dhcp src 192.168.1.100

# Aggiungi/rimuovi route
ip route add 10.10.0.0/16 via 192.168.1.254
ip route add default via 192.168.1.1
ip route del 10.10.0.0/16

# Route per interfaccia specifica
ip route add 172.16.0.0/12 dev eth1

# Verifica quale route usa un IP
ip route get 8.8.8.8

# Statistiche interfaccia
ip -s link show eth0    # pacchetti TX/RX, errori

# Cambio MTU
ip link set eth0 mtu 9000   # jumbo frames
```

---

## A2. Socket statistics con ss

```bash
# ss sostituisce netstat (più veloce, più funzionale)

# Lista tutte le connessioni
ss -a           # all
ss -t           # TCP
ss -u           # UDP
ss -l           # listening
ss -p           # mostra processo

# Combinazioni comuni
ss -tulpn               # TCP+UDP listening con processo e porta
ss -tnp                 # TCP established con processo
ss -tlnp | grep :80     # chi ascolta su porta 80

# Filtra per stato
ss -t state established
ss -t state time-wait
ss -t state close-wait

# Filtra per indirizzo
ss -t dst 8.8.8.8       # connessioni verso Google DNS
ss -t sport = :443      # connessioni da porta sorgente 443
ss -t dport = :5432     # connessioni a PostgreSQL

# Output esteso
ss -e           # dettagli socket
ss -m           # memoria socket
ss -i           # informazioni TCP interne

# Equivalenza netstat → ss
# netstat -tulpn → ss -tulpn
# netstat -anp   → ss -anp
# netstat -rn    → ip route show
```

---

# Parte B — Configurazione permanente

---

## B1. Netplan (Ubuntu 18.04+)

```yaml
# /etc/netplan/01-rete.yaml

network:
  version: 2
  renderer: networkd    # o NetworkManager

  ethernets:
    # Indirizzo statico
    eth0:
      dhcp4: no
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [1.1.1.1, 8.8.8.8]
        search: [esempio.it]
      mtu: 1500

    # DHCP
    eth1:
      dhcp4: yes
      dhcp6: no

  # VLAN
  vlans:
    vlan10:
      id: 10
      link: eth0
      addresses:
        - 10.0.10.1/24

  # Bonding
  bonds:
    bond0:
      interfaces: [eth0, eth1]
      parameters:
        mode: active-backup      # o 802.3ad per LACP
        primary: eth0
        mii-monitor-interval: 100
      addresses:
        - 192.168.1.50/24
      routes:
        - to: default
          via: 192.168.1.1
```

```bash
# Applica configurazione (dry-run prima)
netplan try          # testa per 120s, poi ripristina
netplan apply        # applica definitivamente
netplan generate     # genera configurazione backend
```

---

## B2. NetworkManager

```bash
# Strumento CLI: nmcli
nmcli device status          # lista dispositivi
nmcli connection show        # lista connessioni

# Connessione ethernet statica
nmcli connection add \
    type ethernet \
    ifname eth0 \
    con-name "rete-ufficio" \
    ipv4.method manual \
    ipv4.addresses "192.168.1.100/24" \
    ipv4.gateway "192.168.1.1" \
    ipv4.dns "8.8.8.8,1.1.1.1"

# Modifica connessione esistente
nmcli connection modify "rete-ufficio" ipv4.dns "1.1.1.1,8.8.8.8"

# Attiva/disattiva
nmcli connection up "rete-ufficio"
nmcli connection down "rete-ufficio"

# WiFi
nmcli radio wifi on
nmcli device wifi list
nmcli device wifi connect "SSID-Rete" password "password123"

# Visualizza dettagli interfaccia
nmcli device show eth0
```

---

# Parte C — Diagnostica di rete

---

## C1. Strumenti fondamentali

```bash
# ping — verifica connettività base
ping -c 4 8.8.8.8          # 4 pacchetti
ping -I eth0 8.8.8.8       # usa interfaccia specifica
ping -s 1472 8.8.8.8       # MTU test (1500-28=1472)

# traceroute — percorso pacchetti
traceroute 8.8.8.8
traceroute -T 8.8.8.8      # TCP invece di UDP

# mtr — combinazione ping+traceroute interattivo
mtr 8.8.8.8
mtr --report 8.8.8.8       # report una volta

# DNS
host www.google.com
nslookup www.google.com
dig www.google.com
dig www.google.com @8.8.8.8    # usa DNS specifico
dig MX esempio.it              # record MX
dig +trace www.google.com      # trace query DNS completo

# Netcat — test porte e connessioni
nc -zv 192.168.1.1 22          # test porta 22 aperta
nc -zv -w 5 server.it 443      # timeout 5 secondi
echo "GET / HTTP/1.0" | nc www.google.com 80   # richiesta HTTP raw

# curl per test HTTP
curl -I https://www.google.com        # solo headers
curl -v https://api.esempio.it        # verbose
curl --connect-timeout 5 http://host  # timeout connessione
curl -k https://self-signed.it        # ignora SSL (solo test!)
```

---

## C2. tcpdump: cattura pacchetti

```bash
# Installa
apt install tcpdump

# Cattura su interfaccia
tcpdump -i eth0                        # tutto
tcpdump -i eth0 -n                     # no DNS resolution
tcpdump -i eth0 -nn                    # no DNS + no porta names

# Filtri comuni
tcpdump -i eth0 host 192.168.1.50      # traffico da/verso IP
tcpdump -i eth0 port 80                # traffico su porta 80
tcpdump -i eth0 tcp                    # solo TCP
tcpdump -i eth0 udp port 53            # query DNS
tcpdump -i eth0 'tcp[tcpflags] & tcp-syn != 0'   # solo SYN

# Salva su file
tcpdump -i eth0 -w /tmp/capture.pcap
tcpdump -r /tmp/capture.pcap           # leggi file

# Limita cattura
tcpdump -i eth0 -c 100                 # ferma dopo 100 pacchetti
tcpdump -i eth0 -G 60 -w dump_%Y%m%d_%H%M%S.pcap  # ruota ogni 60s
```

---

# Parte D — Firewall

---

## D1. ufw (Ubuntu Uncomplicated Firewall)

```bash
# Abilita/disabilita
ufw enable
ufw disable
ufw status verbose

# Regole base
ufw allow 22/tcp           # SSH
ufw allow 80/tcp           # HTTP
ufw allow 443/tcp          # HTTPS
ufw allow 8080             # porta 8080 (qualsiasi protocollo)

# Nega porte
ufw deny 23/tcp            # blocca Telnet
ufw reject 3306/tcp        # rifiuta con risposta (vs drop silenzioso)

# Da/verso IP specifici
ufw allow from 192.168.1.0/24 to any port 22
ufw allow from 10.0.0.50 to any port 5432

# Rimuovi regole
ufw delete allow 80/tcp
ufw delete deny 23/tcp

# Regole numbered
ufw status numbered
ufw delete 3             # elimina regola numero 3

# Applicazioni predefinite
ufw app list
ufw allow 'Nginx Full'
ufw allow 'OpenSSH'

# Default policy
ufw default deny incoming
ufw default allow outgoing
```

---

## D2. iptables essenziale

```bash
# Lista regole
iptables -L                    # lista
iptables -L -n -v --line-numbers  # verbose con numeri

# Catene principali
# INPUT: traffico in entrata verso questo host
# OUTPUT: traffico generato da questo host
# FORWARD: traffico che transita (router)

# Aggiungi regole
iptables -A INPUT -p tcp --dport 22 -j ACCEPT     # permetti SSH
iptables -A INPUT -p tcp --dport 80 -j ACCEPT     # permetti HTTP
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -i lo -j ACCEPT                 # loopback
iptables -A INPUT -j DROP                         # DROP tutto il resto

# Inserisci in posizione specifica
iptables -I INPUT 1 -s 10.0.0.0/8 -j ACCEPT      # in testa

# Rimuovi regola
iptables -D INPUT -p tcp --dport 23 -j DROP
iptables -D INPUT 3              # per numero

# Salva/ripristina regole
# Debian/Ubuntu:
iptables-save > /etc/iptables/rules.v4
iptables-restore < /etc/iptables/rules.v4

# Installa persistenza
apt install iptables-persistent
netfilter-persistent save
```

---

# Parte E — Riepilogo

## Diagnostica rapida

```bash
# Rete funziona?
ping -c 1 8.8.8.8 && echo "Internet OK" || echo "No Internet"

# Quale processo usa la porta 80?
ss -tlnp | grep :80

# Routing OK?
ip route get 8.8.8.8

# DNS funziona?
dig +short google.com @8.8.8.8

# Interfacce attive
ip link show | grep "state UP"
```

## Quick reference: strumenti

| Strumento | Uso principale |
|---|---|
| `ip addr` | Indirizzi IP interfacce |
| `ip route` | Tabella routing |
| `ss -tulpn` | Porte in ascolto |
| `ping` | Connettività base |
| `traceroute` | Percorso pacchetti |
| `dig` | Query DNS |
| `tcpdump` | Cattura pacchetti |
| `nc` | Test connettività TCP |
| `curl` | Test HTTP |
| `ufw` | Firewall semplice |

## Prossimi passi

- `tutorial_linux_06_storage.md` — LVM, RAID, filesystem
- `tutorial_linux_10_ssh_avanzato.md` — SSH tunneling e port forwarding
