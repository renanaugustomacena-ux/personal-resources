# Networking Linux — Guida Completa

> **Modulo 05** · **Aggiornamento:** 2026-05-22

## Idee guida
1. **`ip` > `ifconfig` (legacy).**
2. **netplan (Ubuntu) vs NetworkManager vs systemd-networkd.**
3. **eBPF + XDP per perf network.**
4. **`tcpdump`, `ss`, `ip -s link` diagnostic essential.**
5. **nftables > iptables per nuove installazioni.**
6. **Network namespace = isolamento senza VM.**
7. **WireGuard > OpenVPN per VPN point-to-point.**


## Indice

- [Panoramica](#panoramica)
- [Architettura dello Stack di Rete (L2–L7)](#architettura-dello-stack-di-rete-l2l7)
- [Fondamenti Networking Linux](#fondamenti-networking-linux)
- [Comando ip — Deep Dive](#comando-ip--deep-dive)
- [Configurazione Interfacce e IP](#configurazione-interfacce-e-ip)
- [NetworkManager vs systemd-networkd vs ifupdown](#networkmanager-vs-systemd-networkd-vs-ifupdown)
- [Netplan e NetworkManager](#netplan-e-networkmanager)
- [Routing e Tabelle](#routing-e-tabelle)
- [Network Namespace](#network-namespace)
- [VLAN (802.1Q) — Configurazione Avanzata](#vlan-8021q--configurazione-avanzata)
- [Bonding e Teaming](#bonding-e-teaming)
- [Bridge — Configurazione Avanzata](#bridge--configurazione-avanzata)
- [DNS — Catena di Risoluzione Completa](#dns--catena-di-risoluzione-completa)
- [Server DHCP (ISC, dnsmasq, Kea)](#server-dhcp-isc-dnsmasq-kea)
- [Firewall: iptables](#firewall-iptables)
- [Firewall: nftables](#firewall-nftables)
- [Firewall: firewalld](#firewall-firewalld)
- [TCP/IP Tuning (sysctl)](#tcpip-tuning-sysctl)
- [Wi-Fi (iw, wpa_supplicant, NetworkManager)](#wi-fi-iw-wpa_supplicant-networkmanager)
- [VPN: OpenVPN e WireGuard](#vpn-openvpn-e-wireguard)
- [Strumenti di Diagnosi Rete](#strumenti-di-diagnosi-rete)
- [tcpdump e Wireshark](#tcpdump-e-wireshark)
- [IPv6 — Configurazione Completa](#ipv6--configurazione-completa)
- [tc — Traffic Control e QoS](#tc--traffic-control-e-qos)
- [Strumenti Avanzati di Diagnosi Rete](#strumenti-avanzati-di-diagnosi-rete)
- [nftables — Sintassi Avanzata e Funzionalità](#nftables--sintassi-avanzata-e-funzionalità)
- [WireGuard — Configurazione Avanzata e Tuning](#wireguard--configurazione-avanzata-e-tuning)
- [eBPF e XDP per il Networking](#ebpf-e-xdp-per-il-networking)
- [Network Security Hardening](#network-security-hardening)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## Panoramica

Il networking è una competenza centrale per qualsiasi amministratore Linux. Dalla configurazione degli indirizzi IP alla gestione dei firewall, dal routing al VPN, dalla diagnosi dei problemi di rete all'analisi del traffico: ogni aspetto dell'infrastruttura moderna si basa sulla rete. Linux offre strumenti potenti sia a livello di configurazione (ip, nmcli, netplan) sia di analisi (ss, tcpdump, traceroute), oltre a stack firewall completi (iptables, nftables, firewalld).

---

## Architettura dello Stack di Rete (L2–L7)

Il kernel Linux implementa un network stack completo che copre i livelli dal Data Link (L2) fino all'Application (L7). Comprendere come i pacchetti attraversano questi livelli è fondamentale per il debug e l'ottimizzazione.

### Modello OSI e Mapping Linux

```
┌─────────────────────────────────────────────────────────────────┐
│  Livello   │  OSI        │  Protocolli      │  Strumenti Linux │
├────────────┼─────────────┼──────────────────┼──────────────────┤
│  L7        │ Application │ HTTP, DNS, SSH,  │ curl, dig, ssh   │
│            │             │ SMTP, SNMP       │ openssl s_client │
├────────────┼─────────────┼──────────────────┼──────────────────┤
│  L6        │ Presentation│ TLS/SSL, MIME    │ openssl, gnutls  │
├────────────┼─────────────┼──────────────────┼──────────────────┤
│  L5        │ Session     │ RPC, NetBIOS     │ rpcinfo, smbclient│
├────────────┼─────────────┼──────────────────┼──────────────────┤
│  L4        │ Transport   │ TCP, UDP, SCTP   │ ss, netstat, nc  │
├────────────┼─────────────┼──────────────────┼──────────────────┤
│  L3        │ Network     │ IP, ICMP, IPsec  │ ip route, ping,  │
│            │             │                  │ traceroute, nft   │
├────────────┼─────────────┼──────────────────┼──────────────────┤
│  L2        │ Data Link   │ Ethernet, ARP,   │ ip link, bridge, │
│            │             │ 802.1Q, STP      │ ip neigh, ethtool│
├────────────┼─────────────┼──────────────────┼──────────────────┤
│  L1        │ Physical    │ Cavi, segnali    │ ethtool, mii-tool│
└─────────────────────────────────────────────────────────────────┘
```

### Percorso di un Pacchetto nel Kernel (Ingress)

```
NIC (hardware) → Driver → Ring Buffer → NAPI Polling →
  → netfilter PREROUTING (raw → conntrack → mangle → nat/DNAT) →
    → Routing Decision:
       ├── Destinazione locale → INPUT chain → Socket applicazione
       └── Forward → FORWARD chain → POSTROUTING → NIC uscita
```

### Percorso di un Pacchetto (Egress)

```
Applicazione → Socket → OUTPUT chain →
  → Routing Decision → POSTROUTING (SNAT/MASQUERADE) →
    → Queuing Discipline (qdisc/tc) → Driver → NIC → Rete
```

### Livello 2 — Data Link

Il livello L2 gestisce i frame Ethernet, gli indirizzi MAC, le VLAN (802.1Q) e il protocollo ARP per la risoluzione MAC↔IP.

```bash
# Verificare stato fisico del link
ethtool eth0                       # Speed, duplex, autoneg
ethtool -S eth0                    # Statistiche hardware (errori CRC, collisioni)
ethtool -i eth0                    # Driver e firmware

# Tabella ARP / neighbor
ip neigh show                      # Cache ARP attuale
ip -s neigh show                   # Con statistiche
arping -I eth0 192.168.1.1         # ARP ping (verifica L2 raggiungibilità)

# Bridge (switch software L2)
bridge link show                   # Porte del bridge
bridge fdb show                    # Forwarding database (tabella MAC)
bridge vlan show                   # VLAN associate al bridge
```

### Livello 3 — Network

Il kernel gestisce routing, frammentazione IP, ICMP, e il connection tracking (conntrack) usato da netfilter/nftables.

```bash
# Tabella routing e decisioni
ip route show                      # Tabella routing
ip route get 8.8.8.8               # Quale percorso per un dato IP
ip rule show                       # Policy routing rules

# Connection tracking (conntrack)
sudo conntrack -L                  # Lista connessioni tracciate
sudo conntrack -C                  # Conteggio connessioni attive
sudo conntrack -S                  # Statistiche (drop, insert_failed, etc.)
cat /proc/sys/net/netfilter/nf_conntrack_count   # Connessioni correnti
cat /proc/sys/net/netfilter/nf_conntrack_max     # Limite massimo
```

### Livello 4 — Transport

TCP e UDP sono gestiti interamente nel kernel. Linux offre diverse implementazioni di congestion control (cubic, bbr, reno) configurabili via sysctl.

```bash
# Congestion control
sysctl net.ipv4.tcp_congestion_control              # Algoritmo attivo
sysctl net.ipv4.tcp_available_congestion_control     # Disponibili
sudo sysctl -w net.ipv4.tcp_congestion_control=bbr  # Impostare BBR

# Socket in ascolto e connessioni
ss -tuln                           # Porte in ascolto (TCP+UDP, numeric)
ss -tunap                          # Con PID/processo
ss -ti                             # Info TCP dettagliate (RTT, cwnd, etc.)
ss -s                              # Statistiche riassuntive
```

### Livelli 5–7 — Sessione, Presentazione, Applicazione

Gestiti in userspace dalle applicazioni e librerie (OpenSSL/GnuTLS per TLS, librerie DNS, server HTTP, ecc.). Il kernel espone i socket e i protocolli di trasporto, le applicazioni costruiscono sopra.

```bash
# Test TLS (L6)
openssl s_client -connect example.com:443 -servername example.com

# Test HTTP (L7)
curl -v https://example.com        # Verbose con handshake TLS

# Test DNS (L7)
dig +trace example.com             # Traccia la risoluzione DNS completa
```

---

## Fondamenti Networking Linux

### Stack di Rete del Kernel

Il kernel Linux implementa lo stack TCP/IP completo. Ogni interfaccia di rete è rappresentata come un oggetto nel kernel, gestibile tramite il tool `ip` (pacchetto iproute2, sostituto moderno di ifconfig/route/arp).

```bash
# Interfacce di rete
ip link show                       # Lista interfacce con stato
ip -s link show eth0               # Statistiche (pacchetti, byte, errori)
ip -br link show                   # Vista breve (brief)
ip -br addr show                   # IP in formato breve

# Informazioni socket e connessioni
ss -tuln                           # Socket TCP/UDP in ascolto
ss -tunap                          # Connessioni con processo associato
ss -s                              # Statistiche socket
ss -t state established            # Solo connessioni stabilite
ss -t dst 10.0.0.1                 # Connessioni verso un IP specifico
```

### File di Configurazione Rete

```bash
/etc/hostname                      # Nome host
/etc/hosts                         # Risoluzione nomi locale
/etc/resolv.conf                   # DNS resolver (spesso gestito da resolved/NM)
/etc/nsswitch.conf                 # Ordine di risoluzione nomi
/etc/network/interfaces            # Config rete legacy (Debian)
/etc/netplan/*.yaml                # Config rete moderna (Ubuntu)
/etc/sysconfig/network-scripts/    # Config rete (RHEL/CentOS legacy)
/etc/NetworkManager/               # Config NetworkManager
/proc/sys/net/                     # Parametri kernel rete
```

---

## Comando ip — Deep Dive

Il comando `ip` (pacchetto `iproute2`) è lo strumento universale per la gestione di rete in Linux. Sostituisce `ifconfig`, `route`, `arp`, `netstat`, `vconfig` e `brctl`. Ogni sotto-comando gestisce un oggetto del network stack.

### ip link — Gestione Interfacce

```bash
# Visualizzazione
ip link show                       # Tutte le interfacce
ip -br link show                   # Vista compatta (brief)
ip -d link show eth0               # Dettagli estesi (driver, qdisc, etc.)
ip -s link show eth0               # Statistiche (TX/RX bytes, errori, drop)
ip -j link show                    # Output JSON (per scripting)
ip link show type bridge           # Solo interfacce di tipo bridge
ip link show type vlan             # Solo VLAN
ip link show type bond             # Solo bond
ip link show master br0            # Interfacce slave di un bridge

# Gestione stato
ip link set eth0 up                # Attiva
ip link set eth0 down              # Disattiva
ip link set eth0 mtu 9000          # Jumbo frames (verificare supporto switch)
ip link set eth0 txqueuelen 10000  # Lunghezza coda di trasmissione
ip link set eth0 promisc on        # Modalità promiscua (sniffing)
ip link set eth0 allmulticast on   # Ricevi tutti i pacchetti multicast

# MAC address
ip link set eth0 address 00:11:22:33:44:55  # Cambia MAC
ip link set eth0 down && ip link set eth0 address AA:BB:CC:DD:EE:FF && ip link set eth0 up

# Creare interfacce virtuali
ip link add dummy0 type dummy                    # Interfaccia dummy
ip link add veth0 type veth peer name veth1      # Coppia veth (namespace)
ip link add macvlan0 link eth0 type macvlan mode bridge  # MACVLAN
ip link add ipvlan0 link eth0 type ipvlan mode l3  # IPVLAN L3

# Eliminare
ip link del dummy0
ip link del veth0                  # Elimina entrambi i peer
```

### ip addr — Gestione Indirizzi

```bash
# Visualizzazione
ip addr show                       # Tutti gli indirizzi
ip addr show dev eth0              # Solo un'interfaccia
ip -4 addr show                    # Solo IPv4
ip -6 addr show                    # Solo IPv6
ip addr show scope global          # Solo indirizzi con scope global
ip addr show dynamic               # Solo indirizzi ottenuti via DHCP
ip addr show permanent             # Solo indirizzi statici

# Aggiungere indirizzi
ip addr add 192.168.1.100/24 dev eth0                        # IP primario
ip addr add 192.168.1.101/24 dev eth0 label eth0:1           # IP alias (compatibilità ifconfig)
ip addr add 192.168.1.102/24 dev eth0 noprefixroute          # Senza aggiungere route
ip addr add 10.0.0.1/32 dev lo                               # IP su loopback (VIP, anycast)
ip addr add fd00::1/64 dev eth0                              # IPv6

# Rimuovere
ip addr del 192.168.1.100/24 dev eth0
ip addr flush dev eth0             # Tutti gli IP
ip addr flush dev eth0 scope global  # Solo scope global
ip -4 addr flush dev eth0          # Solo IPv4
```

### ip route — Gestione Routing

```bash
# Visualizzazione
ip route show                      # Tabella main
ip route show table local          # Tabella local (indirizzi locali)
ip route show table all            # Tutte le tabelle
ip route show cache                # Cache routing (deprecato in kernel recenti)
ip route get 8.8.8.8               # Quale route viene usata
ip route get 8.8.8.8 from 10.0.0.1 iif eth1  # Simulare ingresso

# Aggiungere route
ip route add 10.0.0.0/8 via 192.168.1.254                   # Via gateway
ip route add 10.0.0.0/8 via 192.168.1.254 dev eth0          # Con interfaccia esplicita
ip route add default via 192.168.1.1                          # Default gateway
ip route add default via 192.168.1.1 metric 100               # Con metrica (priorità)
ip route add 10.0.0.0/8 dev eth0 scope link                  # Route on-link
ip route add blackhole 192.168.99.0/24                        # Scarta silenziosamente
ip route add unreachable 10.99.0.0/16                         # Risposta ICMP unreachable
ip route add prohibit 172.16.99.0/24                          # Risposta ICMP prohibited

# Multipath (ECMP — Equal-Cost Multi-Path)
ip route add default \
  nexthop via 192.168.1.1 weight 1 \
  nexthop via 192.168.2.1 weight 1

# Rimuovere
ip route del 10.0.0.0/8 via 192.168.1.254
ip route del default
ip route flush table main          # Svuota tabella (ATTENZIONE: perdi connettività)
```

### ip rule — Policy Routing

Il policy routing permette di scegliere tabelle di routing diverse in base a sorgente IP, marca (fwmark), interfaccia di ingresso, e altro.

```bash
# Visualizzare le regole
ip rule show                       # Lista regole (priorità, selettore → tabella)

# Aggiungere regole
ip rule add from 10.0.1.0/24 table 100                      # Traffico da subnet → tabella 100
ip rule add from 10.0.1.0/24 to 10.0.2.0/24 table 200       # Sorgente + destinazione
ip rule add fwmark 0x1 table 100                              # Basato su marca nftables/iptables
ip rule add iif eth1 table 100                                # Basato su interfaccia di ingresso
ip rule add from 10.0.1.0/24 table 100 priority 100          # Con priorità esplicita

# Rimuovere
ip rule del from 10.0.1.0/24 table 100

# Creare tabelle di routing custom
# Aggiungere in /etc/iproute2/rt_tables:
#   100   isp1
#   200   isp2
ip route add default via 10.0.1.1 table 100
ip route add default via 10.0.2.1 table 200
```

**Caso d'uso: dual ISP con source-based routing:**

```bash
# ISP1: 10.0.1.0/24 via gateway 10.0.1.1
# ISP2: 10.0.2.0/24 via gateway 10.0.2.1
echo "100 isp1" >> /etc/iproute2/rt_tables
echo "200 isp2" >> /etc/iproute2/rt_tables

ip route add default via 10.0.1.1 table isp1
ip route add default via 10.0.2.1 table isp2

ip rule add from 10.0.1.0/24 table isp1
ip rule add from 10.0.2.0/24 table isp2

# Default: ECMP load balancing
ip route add default \
  nexthop via 10.0.1.1 weight 1 \
  nexthop via 10.0.2.1 weight 1
```

### ip neigh — Tabella ARP/NDP

```bash
# Visualizzare
ip neigh show                      # Cache ARP/NDP completa
ip neigh show dev eth0             # Solo un'interfaccia
ip -s neigh show                   # Con statistiche (used, confirmed, updated)

# Stati neighbor
# REACHABLE:  raggiungibile (confermato di recente)
# STALE:      non confermato di recente, ma potenzialmente valido
# DELAY:      in attesa di conferma
# PROBE:      invio di probe per conferma
# FAILED:     irraggiungibile
# PERMANENT:  entry statica

# Aggiungere entry statica
ip neigh add 192.168.1.1 lladdr 00:11:22:33:44:55 dev eth0 nud permanent
# nud = Neighbour Unreachability Detection state

# Rimuovere
ip neigh del 192.168.1.1 dev eth0
ip neigh flush dev eth0            # Svuota cache

# Proxy ARP
ip neigh add proxy 192.168.1.200 dev eth0  # Rispondi ARP per conto di un altro host
```

### ip netns — Network Namespace

Vedi sezione dedicata [Network Namespace](#network-namespace) più avanti.

```bash
# Anteprima rapida
ip netns list                      # Lista namespace
ip netns add test                  # Crea namespace
ip netns exec test ip addr show    # Esegui comando dentro il namespace
ip netns del test                  # Elimina
```

### ip monitor — Monitoraggio in Tempo Reale

```bash
ip monitor all                     # Tutti gli eventi (link, addr, route, neigh)
ip monitor link                    # Solo eventi link (up/down)
ip monitor route                   # Cambiamenti routing
ip monitor neigh                   # Cambiamenti ARP/NDP
ip monitor address                 # Cambiamenti indirizzi

# Utile per debug: apri in un terminale e osserva mentre modifichi la configurazione
```

---

## Configurazione Interfacce e IP

### Comandi ip (iproute2)

```bash
# INDIRIZZI IP
ip addr show                       # Lista tutti gli IP
ip addr show dev eth0              # IP di un'interfaccia specifica
ip addr add 192.168.1.100/24 dev eth0       # Aggiungi IP
ip addr add 192.168.1.101/24 dev eth0 label eth0:1  # IP alias
ip addr del 192.168.1.100/24 dev eth0       # Rimuovi IP
ip addr flush dev eth0             # Rimuovi tutti gli IP

# INTERFACCE (LINK)
ip link set eth0 up                # Attiva interfaccia
ip link set eth0 down              # Disattiva interfaccia
ip link set eth0 mtu 9000          # Cambia MTU (jumbo frame)
ip link set eth0 promisc on        # Modalità promiscua
ip link set eth0 name eno1         # Rinomina interfaccia
ip link set eth0 address 00:11:22:33:44:55  # Cambia MAC

# NEIGHBOUR (ARP)
ip neigh show                      # Tabella ARP
ip neigh add 192.168.1.1 lladdr 00:11:22:33:44:55 dev eth0  # Entry statica
ip neigh del 192.168.1.1 dev eth0  # Rimuovi entry
ip neigh flush dev eth0            # Svuota cache ARP

# NOTA: tutti i comandi ip sono temporanei (persi al reboot)
# Per persistenza: usare netplan, NetworkManager o systemd-networkd
```

### Configurazione DHCP Manuale

```bash
# dhclient (ISC DHCP client)
sudo dhclient eth0                 # Richiedi IP via DHCP
sudo dhclient -r eth0              # Rilascia IP DHCP

# systemd-networkd con DHCP: vedi sezione systemd-networkd

# Verificare IP ottenuto
ip addr show eth0
cat /var/lib/dhcp/dhclient.leases  # Lease DHCP
```

---

## Netplan e NetworkManager

### Netplan (Ubuntu 18.04+)

Netplan è il layer di astrazione per la configurazione di rete in Ubuntu. Genera configurazioni per NetworkManager o systemd-networkd.

```yaml
# /etc/netplan/01-config.yaml

# DHCP
network:
  version: 2
  renderer: networkd               # o NetworkManager
  ethernets:
    eth0:
      dhcp4: true
      dhcp6: false
```

```yaml
# Configurazione statica
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
        - 192.168.1.101/24         # IP multipli
      routes:
        - to: default
          via: 192.168.1.1
        - to: 10.0.0.0/8
          via: 192.168.1.254
      nameservers:
        addresses:
          - 8.8.8.8
          - 8.8.4.4
        search:
          - example.com
      mtu: 1500
```

```yaml
# Bond (aggregazione link)
network:
  version: 2
  bonds:
    bond0:
      interfaces:
        - eth0
        - eth1
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      parameters:
        mode: active-backup
        primary: eth0
        mii-monitor-interval: 100
```

```yaml
# Bridge (per VM/container)
network:
  version: 2
  bridges:
    br0:
      interfaces:
        - eth0
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      parameters:
        stp: false
```

```yaml
# VLAN
network:
  version: 2
  vlans:
    vlan100:
      id: 100
      link: eth0
      addresses:
        - 10.100.0.10/24
```

```bash
# Applicare la configurazione
sudo netplan generate              # Genera config (verifica sintassi)
sudo netplan apply                 # Applica
sudo netplan try                   # Applica con rollback automatico (120s)
```

### NetworkManager (nmcli)

NetworkManager è il gestore di rete predefinito su desktop e molte distro server.

```bash
# STATO
nmcli general status               # Stato generale
nmcli device status                # Stato interfacce
nmcli connection show              # Connessioni configurate
nmcli connection show "Wired 1"    # Dettagli connessione

# CREARE CONNESSIONE STATICA
nmcli connection add type ethernet con-name "server" \
  ifname eth0 \
  ipv4.method manual \
  ipv4.addresses "192.168.1.100/24" \
  ipv4.gateway "192.168.1.1" \
  ipv4.dns "8.8.8.8,8.8.4.4" \
  ipv4.dns-search "example.com"

# CREARE CONNESSIONE DHCP
nmcli connection add type ethernet con-name "dhcp" \
  ifname eth0 \
  ipv4.method auto

# MODIFICARE
nmcli connection modify "server" ipv4.dns "1.1.1.1"
nmcli connection modify "server" +ipv4.addresses "10.0.0.100/24"  # Aggiungere IP

# ATTIVARE/DISATTIVARE
nmcli connection up "server"
nmcli connection down "server"
nmcli device disconnect eth0

# WIFI
nmcli device wifi list             # Scan reti WiFi
nmcli device wifi connect "SSID" password "pass123"
nmcli connection modify "SSID" wifi-sec.key-mgmt wpa-psk

# DNS
nmcli connection modify "server" ipv4.dns "8.8.8.8 1.1.1.1"
nmcli connection modify "server" ipv4.ignore-auto-dns yes

# Applicare modifiche
nmcli connection up "server"       # Riapplica la connessione
```

---

## NetworkManager vs systemd-networkd vs ifupdown

Tre stack principali gestiscono la rete in modo persistente su Linux. Scegliere quello giusto dipende dal caso d'uso.

### Tabella Comparativa

```
┌──────────────────────┬─────────────────────┬──────────────────────┬─────────────────┐
│  Caratteristica      │  NetworkManager     │  systemd-networkd    │  ifupdown       │
├──────────────────────┼─────────────────────┼──────────────────────┼─────────────────┤
│  Uso tipico          │  Desktop, laptop,   │  Server, container,  │  Debian legacy, │
│                      │  server con GUI     │  headless            │  sistemi minimi │
├──────────────────────┼─────────────────────┼──────────────────────┼─────────────────┤
│  CLI                 │  nmcli, nmtui       │  networkctl          │  ifup, ifdown   │
├──────────────────────┼─────────────────────┼──────────────────────┼─────────────────┤
│  Config file         │  /etc/NetworkManager│  /etc/systemd/       │  /etc/network/  │
│                      │  /system-connections │  network/*.network   │  interfaces     │
├──────────────────────┼─────────────────────┼──────────────────────┼─────────────────┤
│  Wi-Fi               │  Eccellente         │  Limitato            │  wpa_supplicant │
│                      │                     │  (via wpa_supplicant)│  manuale        │
├──────────────────────┼─────────────────────┼──────────────────────┼─────────────────┤
│  VPN integrato       │  Sì (plugin)        │  No                  │  No             │
├──────────────────────┼─────────────────────┼──────────────────────┼─────────────────┤
│  VLAN, bond, bridge  │  Sì                 │  Sì                  │  Parziale       │
├──────────────────────┼─────────────────────┼──────────────────────┼─────────────────┤
│  Dispatcher script   │  Sì                 │  No (usa networkd-   │  pre-up/post-up │
│                      │                     │  dispatcher)         │                 │
├──────────────────────┼─────────────────────┼──────────────────────┼─────────────────┤
│  D-Bus API           │  Sì (ricca)         │  Sì (base)           │  No             │
├──────────────────────┼─────────────────────┼──────────────────────┼─────────────────┤
│  Hotplug             │  Automatico         │  Automatico          │  allow-hotplug  │
├──────────────────────┼─────────────────────┼──────────────────────┼─────────────────┤
│  Overhead memoria    │  ~15-30 MB          │  ~2-5 MB             │  Trascurabile   │
├──────────────────────┼─────────────────────┼──────────────────────┼─────────────────┤
│  Distro default      │  Fedora, Ubuntu     │  Arch, Ubuntu Server │  Debian (fino   │
│                      │  Desktop, RHEL      │  (via netplan)       │  a Bullseye)    │
└──────────────────────┴─────────────────────┴──────────────────────┴─────────────────┘
```

### systemd-networkd — Configurazione

```ini
# /etc/systemd/network/10-eth0.network
[Match]
Name=eth0

[Network]
Address=192.168.1.100/24
Gateway=192.168.1.1
DNS=8.8.8.8
DNS=8.8.4.4
Domains=example.com
DHCP=no
# Per DHCP: DHCP=yes e rimuovere Address/Gateway

[Route]
Gateway=192.168.1.254
Destination=10.0.0.0/8
Metric=100
```

```ini
# /etc/systemd/network/20-vlan100.netdev
[NetDev]
Name=vlan100
Kind=vlan

[VLAN]
Id=100
```

```ini
# /etc/systemd/network/20-vlan100.network
[Match]
Name=vlan100

[Network]
Address=10.100.0.10/24
```

```bash
# Gestione
sudo systemctl enable --now systemd-networkd
sudo systemctl enable --now systemd-resolved   # Per DNS
networkctl list                    # Lista interfacce
networkctl status eth0             # Dettagli interfaccia
networkctl reload                  # Ricarica configurazione
```

### ifupdown — Configurazione (Legacy Debian)

```bash
# /etc/network/interfaces
auto lo
iface lo inet loopback

# IP statico
auto eth0
iface eth0 inet static
    address 192.168.1.100
    netmask 255.255.255.0
    gateway 192.168.1.1
    dns-nameservers 8.8.8.8 8.8.4.4
    dns-search example.com

# DHCP
auto eth1
iface eth1 inet dhcp

# VLAN
auto eth0.100
iface eth0.100 inet static
    address 10.100.0.10
    netmask 255.255.255.0
    vlan-raw-device eth0

# Script personalizzati
auto eth0
iface eth0 inet static
    address 192.168.1.100/24
    gateway 192.168.1.1
    pre-up   echo "Preparazione eth0"
    post-up  ip route add 10.0.0.0/8 via 192.168.1.254
    pre-down ip route del 10.0.0.0/8 via 192.168.1.254
    post-down echo "eth0 spenta"
```

```bash
# Gestione
sudo ifup eth0                     # Attiva interfaccia
sudo ifdown eth0                   # Disattiva
sudo ifup -a                       # Attiva tutte le auto
sudo ifquery --list                # Lista interfacce configurate
```

### Quale Scegliere?

- **Server headless, container, cloud** → `systemd-networkd` (leggero, configurazione dichiarativa)
- **Desktop, laptop, Wi-Fi** → `NetworkManager` (gestione dinamica, GUI, VPN plugin)
- **Debian legacy, appliance minimali** → `ifupdown` (semplice, nessun demone extra)
- **Ubuntu** → `netplan` come astrazione sopra networkd o NM

> **Regola pratica:** non mescolare i gestori. Se usi NetworkManager, assicurati che systemd-networkd sia disabilitato e viceversa. Conflitti tra gestori sono una causa frequente di problemi di rete.

---

## Routing e Tabelle

```bash
# VISUALIZZARE
ip route show                      # Tabella routing
ip route show table all            # Tutte le tabelle
ip route get 8.8.8.8               # Quale route viene usata per un IP

# AGGIUNGERE ROUTE
ip route add 10.0.0.0/8 via 192.168.1.254          # Route statica
ip route add 172.16.0.0/12 via 192.168.1.254 dev eth0
ip route add default via 192.168.1.1                 # Default gateway
ip route add 10.0.0.0/8 via 192.168.1.254 metric 100  # Con metrica

# RIMUOVERE ROUTE
ip route del 10.0.0.0/8 via 192.168.1.254
ip route del default

# POLICY ROUTING (routing avanzato con tabelle multiple)
ip rule add from 10.0.1.0/24 table 100
ip route add default via 10.0.1.1 table 100

# IP FORWARDING (routing tra interfacce)
# Abilitare temporaneamente
sudo sysctl -w net.ipv4.ip_forward=1

# Abilitare permanentemente
# In /etc/sysctl.d/99-routing.conf:
# net.ipv4.ip_forward = 1
sudo sysctl -p /etc/sysctl.d/99-routing.conf

# Verificare
cat /proc/sys/net/ipv4/ip_forward
```

### Route Persistenti

```bash
# Con netplan (Ubuntu)
# routes: nella sezione dell'interfaccia

# Con NetworkManager
nmcli connection modify "server" +ipv4.routes "10.0.0.0/8 192.168.1.254"

# Con systemd-networkd
# [Route] nel file .network

# Con ip-route (Debian legacy)
# /etc/network/interfaces:
# up ip route add 10.0.0.0/8 via 192.168.1.254
```

---

## DNS Client

```bash
# /etc/resolv.conf — configurazione DNS (spesso gestito automaticamente)
nameserver 8.8.8.8
nameserver 8.8.4.4
search example.com lab.example.com
options timeout:2 attempts:3

# /etc/hosts — risoluzione locale (priorità su DNS)
127.0.0.1   localhost
192.168.1.10  server1.example.com server1

# /etc/nsswitch.conf — ordine di risoluzione
# hosts: files dns          → prima /etc/hosts, poi DNS
# hosts: files mdns4_minimal [NOTFOUND=return] dns

# DIAGNOSI DNS
host example.com                   # Query semplice
dig example.com                    # Query dettagliata
dig +short example.com             # Solo risposta
dig @8.8.8.8 example.com          # Query a server specifico
dig example.com MX                 # Record MX
dig example.com ANY                # Tutti i record
dig -x 8.8.8.8                    # Reverse lookup
nslookup example.com              # Tool legacy (ancora usato)

# Con systemd-resolved
resolvectl query example.com
resolvectl status
```

---

## Firewall: iptables

iptables è il firewall tradizionale di Linux. Lavora con il framework netfilter del kernel.

### Concetti Base

```
Tabelle → Catene → Regole

TABELLE:
  filter (default): filtro pacchetti (INPUT, FORWARD, OUTPUT)
  nat:              NAT/masquerading (PREROUTING, OUTPUT, POSTROUTING)
  mangle:           modifica pacchetti (tutte le catene)
  raw:              eccezioni al connection tracking

CATENE (filter):
  INPUT:    pacchetti destinati al sistema
  OUTPUT:   pacchetti generati dal sistema
  FORWARD:  pacchetti che attraversano il sistema (routing)

TARGET:
  ACCEPT:   accetta il pacchetto
  DROP:     scarta silenziosamente
  REJECT:   scarta con risposta ICMP
  LOG:      logga e continua
  SNAT/DNAT/MASQUERADE: per NAT
```

### Comandi iptables

```bash
# VISUALIZZARE
sudo iptables -L -n -v             # Lista regole (numeric, verbose)
sudo iptables -L -n -v --line-numbers  # Con numeri di riga
sudo iptables -t nat -L -n -v      # Tabella NAT

# REGOLE BASE
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT     # Accetta SSH
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT     # Accetta HTTP
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT    # Accetta HTTPS
sudo iptables -A INPUT -i lo -j ACCEPT                  # Accetta loopback
sudo iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# POLICY DI DEFAULT
sudo iptables -P INPUT DROP         # Default: scarta tutto l'ingresso
sudo iptables -P FORWARD DROP       # Default: scarta tutto il forward
sudo iptables -P OUTPUT ACCEPT      # Default: accetta tutto l'uscita

# INSERIRE (posizione specifica)
sudo iptables -I INPUT 1 -p tcp --dport 8080 -j ACCEPT  # Prima posizione

# ELIMINARE
sudo iptables -D INPUT -p tcp --dport 8080 -j ACCEPT    # Per regola
sudo iptables -D INPUT 3            # Per numero di riga

# REGOLE AVANZATE
# Range di porte
sudo iptables -A INPUT -p tcp --dport 8000:8999 -j ACCEPT

# IP sorgente
sudo iptables -A INPUT -s 10.0.0.0/8 -p tcp --dport 22 -j ACCEPT

# Limite connessioni (protezione brute force)
sudo iptables -A INPUT -p tcp --dport 22 -m connlimit --connlimit-above 3 -j DROP
sudo iptables -A INPUT -p tcp --dport 22 -m recent --set --name ssh
sudo iptables -A INPUT -p tcp --dport 22 -m recent --update --seconds 60 --hitcount 4 --name ssh -j DROP

# Logging
sudo iptables -A INPUT -j LOG --log-prefix "IPTABLES-DROP: " --log-level 4

# NAT (masquerade per Internet sharing)
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT
sudo iptables -A FORWARD -i eth0 -o eth1 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Port forwarding
sudo iptables -t nat -A PREROUTING -p tcp --dport 8080 -j DNAT --to-destination 192.168.1.100:80

# FLUSH (svuota tutte le regole)
sudo iptables -F                    # Svuota filter
sudo iptables -t nat -F             # Svuota NAT
sudo iptables -X                    # Elimina catene custom

# SALVARE E RIPRISTINARE
sudo iptables-save > /etc/iptables.rules
sudo iptables-restore < /etc/iptables.rules

# Persistenza (Debian/Ubuntu)
sudo apt install iptables-persistent
sudo netfilter-persistent save
```

---

## Firewall: nftables

nftables è il successore di iptables, con sintassi più pulita e migliori performance.

```bash
# /etc/nftables.conf
#!/usr/sbin/nft -f

flush ruleset

table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;

        # Connessioni stabilite
        ct state established,related accept

        # Loopback
        iifname "lo" accept

        # ICMP
        ip protocol icmp accept
        ip6 nexthdr icmpv6 accept

        # SSH
        tcp dport 22 accept

        # HTTP/HTTPS
        tcp dport { 80, 443 } accept

        # Logging pacchetti droppati
        log prefix "nftables-drop: " counter drop
    }

    chain forward {
        type filter hook forward priority 0; policy drop;
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}

# NAT
table inet nat {
    chain prerouting {
        type nat hook prerouting priority -100;
        # Port forwarding
        tcp dport 8080 dnat to 192.168.1.100:80
    }
    chain postrouting {
        type nat hook postrouting priority 100;
        oifname "eth0" masquerade
    }
}
```

```bash
# Comandi nft
sudo nft list ruleset               # Lista completa
sudo nft list table inet filter     # Lista tabella specifica
sudo nft add rule inet filter input tcp dport 8443 accept  # Aggiungi regola
sudo nft delete rule inet filter input handle 10           # Elimina per handle
sudo nft -a list ruleset            # Lista con handle numbers
sudo nft flush ruleset              # Svuota tutto

# Abilitare
sudo systemctl enable --now nftables
```

---

## Firewall: firewalld

firewalld è il frontend ad alto livello usato in Fedora/RHEL/CentOS. Gestisce zone di rete e servizi.

```bash
# STATO
sudo firewall-cmd --state
sudo firewall-cmd --get-active-zones
sudo firewall-cmd --get-default-zone
sudo firewall-cmd --list-all                # Regole zona attiva
sudo firewall-cmd --list-all --zone=public  # Regole zona specifica

# ZONE
# trusted, home, work, internal, public (default), external, dmz, block, drop
sudo firewall-cmd --set-default-zone=internal
sudo firewall-cmd --zone=internal --add-interface=eth1

# SERVIZI
sudo firewall-cmd --get-services             # Lista servizi disponibili
sudo firewall-cmd --add-service=http --permanent
sudo firewall-cmd --add-service=https --permanent
sudo firewall-cmd --remove-service=ssh --permanent

# PORTE
sudo firewall-cmd --add-port=8080/tcp --permanent
sudo firewall-cmd --add-port=5000-5100/tcp --permanent
sudo firewall-cmd --remove-port=8080/tcp --permanent

# PORT FORWARDING
sudo firewall-cmd --add-forward-port=port=8080:proto=tcp:toport=80:toaddr=192.168.1.100 --permanent

# RICH RULES (regole complesse)
sudo firewall-cmd --add-rich-rule='rule family="ipv4" source address="10.0.0.0/8" service name="ssh" accept' --permanent
sudo firewall-cmd --add-rich-rule='rule family="ipv4" source address="0.0.0.0/0" service name="ssh" limit value="3/m" accept' --permanent

# MASQUERADE (NAT)
sudo firewall-cmd --add-masquerade --permanent

# APPLICARE
sudo firewall-cmd --reload           # Applica le regole --permanent

# SERVIZI CUSTOM
# /etc/firewalld/services/myapp.xml
# <service>
#   <short>MyApp</short>
#   <port protocol="tcp" port="3000"/>
#   <port protocol="tcp" port="3001"/>
# </service>
```

---

## Bridge, Bonding e VLAN

### Bridge (ponte di rete)

Collega due o più interfacce a livello L2. Essenziale per VM e container.

```bash
# Creare bridge con ip
sudo ip link add br0 type bridge
sudo ip link set eth0 master br0
sudo ip link set eth1 master br0
sudo ip link set br0 up
sudo ip addr add 192.168.1.100/24 dev br0

# Con brctl (bridge-utils, legacy)
sudo brctl addbr br0
sudo brctl addif br0 eth0
sudo brctl show
```

### Bonding (aggregazione link)

Combina più interfacce fisiche per ridondanza o performance.

```bash
# Modalità bonding
# mode=0 (balance-rr):     round-robin, load balancing
# mode=1 (active-backup):  failover, una attiva alla volta
# mode=2 (balance-xor):    hash-based load balancing
# mode=4 (802.3ad/LACP):   aggregazione dinamica (richiede supporto switch)
# mode=5 (balance-tlb):    adaptive transmit load balancing
# mode=6 (balance-alb):    adaptive load balancing

# Con NetworkManager
nmcli connection add type bond con-name bond0 ifname bond0 \
  bond.options "mode=active-backup,miimon=100,primary=eth0"
nmcli connection add type ethernet con-name bond0-slave1 ifname eth0 master bond0
nmcli connection add type ethernet con-name bond0-slave2 ifname eth1 master bond0
nmcli connection modify bond0 ipv4.method manual ipv4.addresses "192.168.1.100/24"
nmcli connection up bond0

# Verificare
cat /proc/net/bonding/bond0
```

### VLAN (802.1Q)

```bash
# Creare VLAN con ip
sudo ip link add link eth0 name eth0.100 type vlan id 100
sudo ip addr add 10.100.0.10/24 dev eth0.100
sudo ip link set eth0.100 up

# Con NetworkManager
nmcli connection add type vlan con-name vlan100 \
  ifname eth0.100 dev eth0 id 100 \
  ipv4.method manual ipv4.addresses "10.100.0.10/24"
```

---

## VPN: OpenVPN e WireGuard

### WireGuard

VPN moderna, veloce e semplice. Integrata nel kernel Linux dalla versione 5.6.

```bash
# Installazione
sudo apt install wireguard          # Debian/Ubuntu
sudo dnf install wireguard-tools    # Fedora

# Generare chiavi
wg genkey | tee privatekey | wg pubkey > publickey

# SERVER: /etc/wireguard/wg0.conf
[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = <server_private_key>
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]
PublicKey = <client_public_key>
AllowedIPs = 10.0.0.2/32

# CLIENT: /etc/wireguard/wg0.conf
[Interface]
Address = 10.0.0.2/24
PrivateKey = <client_private_key>
DNS = 8.8.8.8

[Peer]
PublicKey = <server_public_key>
Endpoint = server.example.com:51820
AllowedIPs = 0.0.0.0/0             # Tutto il traffico via VPN
PersistentKeepalive = 25

# Gestione
sudo wg-quick up wg0               # Avvia
sudo wg-quick down wg0             # Ferma
sudo wg show                       # Stato
sudo systemctl enable --now wg-quick@wg0  # Avvio automatico
```

### OpenVPN (cenni)

```bash
# Installazione
sudo apt install openvpn easy-rsa

# Generare PKI con easy-rsa
make-cadir /etc/openvpn/easy-rsa
cd /etc/openvpn/easy-rsa
./easyrsa init-pki
./easyrsa build-ca
./easyrsa gen-req server nopass
./easyrsa sign-req server server
./easyrsa gen-dh
openvpn --genkey secret ta.key

# Avvio
sudo systemctl enable --now openvpn-server@server
```

---

## Strumenti di Diagnosi Rete

```bash
# CONNETTIVITÀ
ping -c 4 8.8.8.8                  # Test ICMP
ping -c 4 -I eth0 8.8.8.8         # Da interfaccia specifica
ping6 ::1                          # IPv6

# TRACEROUTE
traceroute 8.8.8.8                 # Traccia il percorso (ICMP/UDP)
traceroute -T -p 443 8.8.8.8      # Via TCP porta 443
mtr 8.8.8.8                       # Traceroute interattivo continuo
mtr --report -c 10 8.8.8.8        # Report (10 cicli)

# PORTE E SERVIZI
ss -tuln                           # Porte in ascolto
ss -tunap                          # Con processo associato
nmap -sT 192.168.1.100             # Port scan TCP
nmap -sU 192.168.1.100             # Port scan UDP
nmap -sV -p 22,80,443 192.168.1.100  # Versione servizi
nc -zv 192.168.1.100 80            # Test porta specifica
nc -l 8080                         # Ascolto su porta (server test)

# BANDWIDTH
iperf3 -s                          # Server
iperf3 -c server_ip                # Client (test bandwidth)
iperf3 -c server_ip -R             # Reverse (test download)

# INFORMAZIONI INTERFACCE
ethtool eth0                       # Info hardware NIC
ethtool -i eth0                    # Driver
ethtool -S eth0                    # Statistiche hardware

# ARP E NEIGHBOUR
ip neigh show                      # Cache ARP
arping -I eth0 192.168.1.1         # ARP ping

# CURL PER TEST HTTP
curl -I https://example.com        # Solo header
curl -v https://example.com        # Verbose (handshake TLS)
curl -o /dev/null -s -w "%{time_total}\n" https://example.com  # Tempo risposta
curl --resolve example.com:443:1.2.3.4 https://example.com     # Override DNS
```

---

## tcpdump e Wireshark

### tcpdump

```bash
# Cattura base
sudo tcpdump -i eth0               # Tutto il traffico su eth0
sudo tcpdump -i any                # Tutte le interfacce

# Filtri
sudo tcpdump -i eth0 host 10.0.0.1              # Da/verso un host
sudo tcpdump -i eth0 src 10.0.0.1               # Solo sorgente
sudo tcpdump -i eth0 dst 10.0.0.1               # Solo destinazione
sudo tcpdump -i eth0 port 80                     # Porta specifica
sudo tcpdump -i eth0 tcp port 443                # TCP porta 443
sudo tcpdump -i eth0 'tcp port 80 and host 10.0.0.1'  # Combinazione
sudo tcpdump -i eth0 'tcp[tcpflags] & (tcp-syn) != 0'  # Solo SYN
sudo tcpdump -i eth0 icmp                        # Solo ICMP
sudo tcpdump -i eth0 not port 22                 # Escludi SSH

# Opzioni output
sudo tcpdump -i eth0 -n             # No risoluzione DNS (più veloce)
sudo tcpdump -i eth0 -nn            # No risoluzione DNS e porte
sudo tcpdump -i eth0 -v             # Verbose
sudo tcpdump -i eth0 -X             # Hex + ASCII
sudo tcpdump -i eth0 -A             # Solo ASCII (utile per HTTP)
sudo tcpdump -i eth0 -c 100         # Cattura solo 100 pacchetti

# Salvare e leggere file
sudo tcpdump -i eth0 -w capture.pcap              # Salva in file
sudo tcpdump -r capture.pcap                       # Leggi da file
sudo tcpdump -r capture.pcap 'tcp port 80'        # Filtra da file
```

### Wireshark (tshark)

```bash
# tshark (versione CLI di Wireshark)
sudo tshark -i eth0                 # Cattura
sudo tshark -i eth0 -f "tcp port 80"  # Filtro cattura
sudo tshark -r capture.pcap -Y "http.request"  # Filtro display
sudo tshark -r capture.pcap -Y "tcp.stream eq 5"  # Segui stream TCP
sudo tshark -r capture.pcap -T fields -e http.host -e http.request.uri  # Estrai campi
```

---

## Network Namespace

I network namespace sono una delle primitive fondamentali di isolamento del kernel Linux. Ogni namespace possiede il proprio stack di rete completo: interfacce, tabella di routing, regole firewall, tabella ARP/NDP, socket e parametri sysctl. I container (Docker, Podman, LXC, systemd-nspawn) si basano interamente su questa primitiva per l'isolamento di rete.

### Anatomia di un Network Namespace

Quando si crea un nuovo network namespace, il kernel istanzia uno stack di rete vergine. All'interno esiste solo l'interfaccia loopback (`lo`), inizialmente in stato `DOWN`. Nessuna interfaccia fisica, nessuna route, nessuna regola firewall: è un ambiente completamente vuoto.

```bash
# Creare un namespace
sudo ip netns add ns_red
sudo ip netns add ns_blue

# Listare namespace
ip netns list

# Eseguire un comando dentro il namespace
sudo ip netns exec ns_red ip link show
# Output: solo lo (DOWN)

# Attivare loopback
sudo ip netns exec ns_red ip link set lo up

# Shell interattiva dentro il namespace
sudo ip netns exec ns_red bash

# Informazioni sul namespace dal PID
sudo ls -la /proc/<PID>/ns/net
```

### Collegare Namespace con Coppie veth

Le coppie veth (Virtual Ethernet) funzionano come un cavo virtuale: ogni pacchetto inviato a un'estremità emerge dall'altra. Questo è il meccanismo fondamentale usato dai container runtime per connettere il namespace del container al namespace dell'host.

```bash
# Creare coppia veth
sudo ip link add veth_red type veth peer name veth_blue

# Assegnare le estremità ai namespace
sudo ip link set veth_red netns ns_red
sudo ip link set veth_blue netns ns_blue

# Configurare IP e attivare in ns_red
sudo ip netns exec ns_red ip addr add 10.0.0.1/24 dev veth_red
sudo ip netns exec ns_red ip link set veth_red up

# Configurare IP e attivare in ns_blue
sudo ip netns exec ns_blue ip addr add 10.0.0.2/24 dev veth_blue
sudo ip netns exec ns_blue ip link set veth_blue up

# Test connettività
sudo ip netns exec ns_red ping -c 3 10.0.0.2
# ✓ I due namespace comunicano attraverso la coppia veth
```

### Connettere Namespace tramite Bridge

Per collegare più namespace tra loro (simulando una rete LAN con switch), si usa un bridge Linux nel namespace dell'host.

```bash
# Creare bridge nell'host
sudo ip link add br_lab type bridge
sudo ip link set br_lab up
sudo ip addr add 10.0.0.254/24 dev br_lab

# Namespace 1: ns_web
sudo ip netns add ns_web
sudo ip link add veth_web_host type veth peer name veth_web_ns
sudo ip link set veth_web_ns netns ns_web
sudo ip link set veth_web_host master br_lab
sudo ip link set veth_web_host up
sudo ip netns exec ns_web ip addr add 10.0.0.10/24 dev veth_web_ns
sudo ip netns exec ns_web ip link set veth_web_ns up
sudo ip netns exec ns_web ip link set lo up
sudo ip netns exec ns_web ip route add default via 10.0.0.254

# Namespace 2: ns_db
sudo ip netns add ns_db
sudo ip link add veth_db_host type veth peer name veth_db_ns
sudo ip link set veth_db_ns netns ns_db
sudo ip link set veth_db_host master br_lab
sudo ip link set veth_db_host up
sudo ip netns exec ns_db ip addr add 10.0.0.20/24 dev veth_db_ns
sudo ip netns exec ns_db ip link set veth_db_ns up
sudo ip netns exec ns_db ip link set lo up
sudo ip netns exec ns_db ip route add default via 10.0.0.254

# Test: ns_web → ns_db
sudo ip netns exec ns_web ping -c 2 10.0.0.20

# Test: ns_db → ns_web
sudo ip netns exec ns_db ping -c 2 10.0.0.10
```

### Accesso a Internet dai Namespace

Per dare accesso a Internet ai namespace, bisogna abilitare il forwarding e il NAT (masquerade) sull'host.

```bash
# Abilitare IP forwarding sull'host
sudo sysctl -w net.ipv4.ip_forward=1

# NAT con nftables per il traffico dei namespace
sudo nft add table inet ns_nat
sudo nft add chain inet ns_nat postrouting { type nat hook postrouting priority 100 \; }
sudo nft add rule inet ns_nat postrouting oifname "eth0" masquerade

# Oppure con iptables
sudo iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE
sudo iptables -A FORWARD -i br_lab -o eth0 -j ACCEPT
sudo iptables -A FORWARD -i eth0 -o br_lab -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Configurare DNS nel namespace
sudo mkdir -p /etc/netns/ns_web
echo "nameserver 8.8.8.8" | sudo tee /etc/netns/ns_web/resolv.conf

# Test
sudo ip netns exec ns_web ping -c 2 8.8.8.8
sudo ip netns exec ns_web curl -s https://example.com
```

### nsenter — Entrare in un Namespace Esistente

Il comando `nsenter` è più flessibile di `ip netns exec`: permette di entrare nel namespace di rete di un processo già in esecuzione, utile per il debug di container.

```bash
# Trovare il PID del processo container
docker inspect --format '{{.State.Pid}}' <container_name>

# Entrare nel namespace di rete del container
sudo nsenter --target <PID> --net -- ip addr show
sudo nsenter --target <PID> --net -- ss -tuln
sudo nsenter --target <PID> --net -- ip route show
sudo nsenter --target <PID> --net -- tcpdump -i eth0 -nn

# Entrare in più namespace contemporaneamente
sudo nsenter --target <PID> --net --mount --pid -- bash
```

### Namespace Persistenti con mount bind

I namespace creati con `ip netns add` sono già persistenti (creano un mount bind in `/var/run/netns/`). Per namespace creati da container runtime, si può rendere persistente il riferimento:

```bash
# Il file in /var/run/netns/ è il mount bind che tiene in vita il namespace
ls -la /var/run/netns/

# Creare un mount bind da un processo esistente
sudo touch /var/run/netns/my_container
sudo mount --bind /proc/<PID>/ns/net /var/run/netns/my_container

# Ora è visibile con ip netns
ip netns list
sudo ip netns exec my_container ip addr show
```

### Namespace per Testing di Rete Isolato

I namespace sono eccellenti per testare configurazioni di rete senza rischiare la connettività dell'host.

```bash
# Simulare un client e un server in namespace isolati
sudo ip netns add ns_client
sudo ip netns add ns_server

# Creare e collegare
sudo ip link add veth_c type veth peer name veth_s
sudo ip link set veth_c netns ns_client
sudo ip link set veth_s netns ns_server

sudo ip netns exec ns_client ip addr add 192.168.100.1/24 dev veth_c
sudo ip netns exec ns_client ip link set veth_c up
sudo ip netns exec ns_client ip link set lo up

sudo ip netns exec ns_server ip addr add 192.168.100.2/24 dev veth_s
sudo ip netns exec ns_server ip link set veth_s up
sudo ip netns exec ns_server ip link set lo up

# Avviare un server HTTP di test nel namespace server
sudo ip netns exec ns_server python3 -m http.server 8080 &

# Testare dal client
sudo ip netns exec ns_client curl http://192.168.100.2:8080

# Cleanup
sudo ip netns del ns_client
sudo ip netns del ns_server
```

### Come Docker Usa i Namespace

Quando Docker crea un container, segue esattamente questo pattern:

1. Crea un nuovo network namespace per il container
2. Crea una coppia veth: un'estremità nel namespace del container (diventa `eth0`), l'altra nell'host
3. Collega l'estremità host al bridge `docker0`
4. Assegna un IP dalla subnet del bridge al container via IPAM
5. Aggiunge una default route via il bridge
6. Configura regole iptables/nftables per NAT e isolamento tra network Docker

```bash
# Verificare il bridge Docker
ip link show docker0
bridge link show master docker0

# Vedere i veth connessi ai container
ip link show type veth

# Entrare nel namespace di un container Docker
PID=$(docker inspect --format '{{.State.Pid}}' mycontainer)
sudo nsenter --target $PID --net -- ip addr show
```

---

## VLAN (802.1Q) — Configurazione Avanzata

Le VLAN (Virtual LAN) implementano la segmentazione logica della rete a livello L2 secondo lo standard IEEE 802.1Q. Ogni frame Ethernet viene taggato con un VLAN ID (VID, 12 bit, valori 1-4094), permettendo di isolare il traffico su uno stesso collegamento fisico.

### Concetti Fondamentali

```
Frame Ethernet Standard:
┌──────────┬──────────┬──────┬─────────┬─────┐
│ Dst MAC  │ Src MAC  │ Type │ Payload │ FCS │
└──────────┴──────────┴──────┴─────────┴─────┘

Frame Ethernet con tag 802.1Q:
┌──────────┬──────────┬──────────────────────┬──────┬─────────┬─────┐
│ Dst MAC  │ Src MAC  │ 802.1Q Tag (4 byte)  │ Type │ Payload │ FCS │
│          │          │ TPID│PCP│DEI│VID      │      │         │     │
│          │          │0x8100│3b │1b │12bit   │      │         │     │
└──────────┴──────────┴──────────────────────┴──────┴─────────┴─────┘
```

- **TPID (Tag Protocol Identifier)**: sempre `0x8100` per 802.1Q
- **PCP (Priority Code Point)**: 3 bit per CoS (Class of Service, 0-7)
- **DEI (Drop Eligible Indicator)**: 1 bit, indica se il frame può essere scartato in caso di congestione
- **VID (VLAN Identifier)**: 12 bit, da 1 a 4094 (0 = priority tag, 4095 = riservato)

### Tipi di Porte Switch

- **Access port**: trasporta traffico di una sola VLAN, frame non taggati
- **Trunk port**: trasporta traffico di più VLAN, frame taggati con 802.1Q
- **Native VLAN**: la VLAN i cui frame transitano non taggati sulla trunk (default VLAN 1)

### Configurazione VLAN con ip

```bash
# Prerequisito: caricare il modulo 8021q
sudo modprobe 8021q
lsmod | grep 8021q

# Creare interfaccia VLAN
sudo ip link add link eth0 name eth0.100 type vlan id 100
sudo ip link add link eth0 name eth0.200 type vlan id 200
sudo ip link add link eth0 name eth0.300 type vlan id 300

# Configurare IP
sudo ip addr add 10.100.0.10/24 dev eth0.100
sudo ip addr add 10.200.0.10/24 dev eth0.200
sudo ip addr add 10.300.0.10/24 dev eth0.300

# Attivare
sudo ip link set eth0.100 up
sudo ip link set eth0.200 up
sudo ip link set eth0.300 up

# Verificare configurazione VLAN
ip -d link show eth0.100
# Mostra: vlan protocol 802.1Q id 100 <REORDER_HDR>

# Verificare tutte le VLAN
cat /proc/net/vlan/config

# Impostare MTU (considerare 4 byte overhead del tag 802.1Q)
sudo ip link set eth0.100 mtu 1496
# Oppure impostare MTU 9000 sul parent per jumbo frames
sudo ip link set eth0 mtu 9004
sudo ip link set eth0.100 mtu 9000

# Impostare la priorità VLAN (PCP/CoS mapping)
sudo ip link set eth0.100 type vlan egress-qos-map 0:0 1:1 2:2 3:3 4:4 5:5 6:6 7:7
sudo ip link set eth0.100 type vlan ingress-qos-map 0:0 1:1 2:2 3:3 4:4 5:5 6:6 7:7

# Eliminare VLAN
sudo ip link del eth0.100
```

### Configurazione VLAN con systemd-networkd

```ini
# /etc/systemd/network/10-eth0.network
[Match]
Name=eth0

[Network]
VLAN=vlan100
VLAN=vlan200
```

```ini
# /etc/systemd/network/20-vlan100.netdev
[NetDev]
Name=vlan100
Kind=vlan

[VLAN]
Id=100
```

```ini
# /etc/systemd/network/20-vlan100.network
[Match]
Name=vlan100

[Network]
Address=10.100.0.10/24
Gateway=10.100.0.1
DNS=8.8.8.8
```

### VLAN su Bond

Configurazione enterprise: VLAN sopra un bond LACP, per avere ridondanza + segmentazione.

```yaml
# Netplan: VLAN su bond LACP
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: false
    eth1:
      dhcp4: false
  bonds:
    bond0:
      interfaces: [eth0, eth1]
      parameters:
        mode: 802.3ad
        lacp-rate: fast
        mii-monitor-interval: 100
        transmit-hash-policy: layer3+4
  vlans:
    vlan100:
      id: 100
      link: bond0
      addresses: [10.100.0.10/24]
    vlan200:
      id: 200
      link: bond0
      addresses: [10.200.0.10/24]
```

### VLAN-Aware Bridge

Un bridge VLAN-aware gestisce il tagging/untagging per le porte e permette di configurare quali VLAN sono ammesse su ciascuna porta, replicando il comportamento di uno switch managed.

```bash
# Creare bridge VLAN-aware
sudo ip link add br0 type bridge vlan_filtering 1 vlan_default_pvid 1

# Aggiungere porte al bridge
sudo ip link set eth0 master br0
sudo ip link set eth1 master br0
sudo ip link set br0 up

# Configurare VLAN sulle porte
# eth0: trunk con VLAN 100 e 200
sudo bridge vlan add dev eth0 vid 100
sudo bridge vlan add dev eth0 vid 200

# eth1: access VLAN 100 (pvid = untagged ingress, untagged = untagged egress)
sudo bridge vlan add dev eth1 vid 100 pvid untagged
sudo bridge vlan del dev eth1 vid 1  # Rimuovere VLAN di default

# Verificare
bridge vlan show
bridge fdb show
```

### QinQ (802.1ad) — Double Tagging

QinQ (provider bridging) aggiunge un secondo tag VLAN (S-Tag) sopra il tag del cliente (C-Tag). Usato dai provider per trasportare VLAN dei clienti senza interferenze.

```bash
# Creare interfaccia QinQ
sudo ip link add link eth0 name eth0.100 type vlan proto 802.1ad id 100
sudo ip link add link eth0.100 name eth0.100.10 type vlan proto 802.1Q id 10
sudo ip addr add 10.0.0.1/24 dev eth0.100.10
sudo ip link set eth0.100 up
sudo ip link set eth0.100.10 up
```

---

## Bonding e Teaming

Il bonding (kernel module `bonding`) e il teaming (daemon `teamd`) aggregano più interfacce di rete fisiche in una sola interfaccia logica, per ottenere ridondanza (failover) e/o incremento di throughput.

### Modalità di Bonding Dettagliate

```
┌────────┬─────────────────┬───────────────────────────────────────────────────┐
│ Mode   │ Nome            │ Descrizione e requisiti                           │
├────────┼─────────────────┼───────────────────────────────────────────────────┤
│ 0      │ balance-rr      │ Round-robin. Pacchetti distribuiti sequenzialmente│
│        │                 │ Richiede: nessun supporto switch speciale         │
│        │                 │ Pro: incremento throughput, ridondanza             │
│        │                 │ Contro: può causare riordino pacchetti TCP        │
├────────┼─────────────────┼───────────────────────────────────────────────────┤
│ 1      │ active-backup   │ Solo uno slave attivo. Failover automatico.       │
│        │                 │ Richiede: nessun supporto switch speciale         │
│        │                 │ Pro: massima compatibilità, failover semplice     │
│        │                 │ Contro: nessun incremento di throughput            │
├────────┼─────────────────┼───────────────────────────────────────────────────┤
│ 2      │ balance-xor     │ Hash su src/dst MAC per scegliere lo slave.      │
│        │                 │ Richiede: nessun supporto switch speciale         │
│        │                 │ Pro: distribuzione deterministica                  │
├────────┼─────────────────┼───────────────────────────────────────────────────┤
│ 3      │ broadcast       │ Trasmette su tutti gli slave.                     │
│        │                 │ Pro: fault tolerance massima                       │
│        │                 │ Contro: nessun incremento throughput, duplicati    │
├────────┼─────────────────┼───────────────────────────────────────────────────┤
│ 4      │ 802.3ad (LACP)  │ Link Aggregation Control Protocol (IEEE 802.3ad).│
│        │                 │ Richiede: switch con supporto LACP                │
│        │                 │ Pro: throughput aggregato reale, negoziazione      │
│        │                 │ Contro: configurazione switch necessaria           │
├────────┼─────────────────┼───────────────────────────────────────────────────┤
│ 5      │ balance-tlb     │ Adaptive Transmit Load Balancing.                 │
│        │                 │ Richiede: nessun supporto switch speciale         │
│        │                 │ Pro: bilancia TX tra slave, RX su uno solo        │
├────────┼─────────────────┼───────────────────────────────────────────────────┤
│ 6      │ balance-alb     │ Adaptive Load Balancing (TX + RX).               │
│        │                 │ Richiede: driver con supporto per set_mac_address │
│        │                 │ Pro: bilancia sia TX che RX, nessun supporto      │
│        │                 │ switch necessario                                  │
└────────┴─────────────────┴───────────────────────────────────────────────────┘
```

### Bonding con ip e modprobe

```bash
# Caricare il modulo
sudo modprobe bonding mode=4 miimon=100 lacp_rate=1 xmit_hash_policy=layer3+4

# Creare interfaccia bond
sudo ip link add bond0 type bond mode 802.3ad
sudo ip link set bond0 type bond miimon 100
sudo ip link set bond0 type bond lacp_rate fast
sudo ip link set bond0 type bond xmit_hash_policy layer3+4

# Aggiungere slave (devono essere DOWN)
sudo ip link set eth0 down
sudo ip link set eth1 down
sudo ip link set eth0 master bond0
sudo ip link set eth1 master bond0

# Configurare IP e attivare
sudo ip addr add 192.168.1.100/24 dev bond0
sudo ip link set bond0 up

# Verificare stato
cat /proc/net/bonding/bond0
```

### Bonding con systemd-networkd

```ini
# /etc/systemd/network/10-bond0.netdev
[NetDev]
Name=bond0
Kind=bond

[Bond]
Mode=802.3ad
TransmitHashPolicy=layer3+4
MIIMonitorSec=100ms
LACPTransmitRate=fast
```

```ini
# /etc/systemd/network/10-eth0.network
[Match]
Name=eth0

[Network]
Bond=bond0
```

```ini
# /etc/systemd/network/10-eth1.network
[Match]
Name=eth1

[Network]
Bond=bond0
```

```ini
# /etc/systemd/network/20-bond0.network
[Match]
Name=bond0

[Network]
Address=192.168.1.100/24
Gateway=192.168.1.1
DNS=8.8.8.8
```

### Monitoraggio e Failover

```bash
# Stato bond in tempo reale
watch -n 1 cat /proc/net/bonding/bond0

# Simulare failover (mode 1 active-backup)
sudo ip link set eth0 down   # Slave primario cade
cat /proc/net/bonding/bond0  # Verificare switchover
sudo ip link set eth0 up     # Ripristino

# Forzare switchover (mode 1)
echo eth1 | sudo tee /sys/class/net/bond0/bonding/active_slave

# Statistiche
ip -s link show bond0
ethtool -S bond0
```

### Teaming (alternativa moderna al bonding)

`teamd` è un daemon userspace che offre funzionalità simili al bonding kernel ma con architettura modulare e runner intercambiabili.

```bash
# Installare
sudo apt install libteam-utils    # Debian/Ubuntu
sudo dnf install teamd            # Fedora/RHEL

# Creare team con nmcli (LACP)
nmcli connection add type team con-name team0 ifname team0 \
  config '{"runner": {"name": "lacp", "active": true, "fast_rate": true}}'
nmcli connection add type team-slave con-name team0-p1 ifname eth0 master team0
nmcli connection add type team-slave con-name team0-p2 ifname eth1 master team0
nmcli connection modify team0 ipv4.method manual ipv4.addresses "192.168.1.100/24"
nmcli connection up team0

# Stato team
teamdctl team0 state
teamdctl team0 port config dump eth0
```

---

## Bridge — Configurazione Avanzata

Un bridge Linux è uno switch software a livello L2. Collega più interfacce di rete, gestisce la forwarding table (MAC address table) e supporta STP (Spanning Tree Protocol) per la prevenzione dei loop.

### Creazione e Configurazione Completa

```bash
# Creare bridge
sudo ip link add br0 type bridge

# Parametri bridge
sudo ip link set br0 type bridge stp_state 1           # Abilitare STP
sudo ip link set br0 type bridge forward_delay 400      # 4 secondi (centesimi)
sudo ip link set br0 type bridge hello_time 200         # 2 secondi
sudo ip link set br0 type bridge max_age 2000           # 20 secondi
sudo ip link set br0 type bridge priority 32768         # Bridge priority (STP)
sudo ip link set br0 type bridge ageing_time 30000      # MAC age timeout (secondi * 100)

# Aggiungere porte
sudo ip link set eth0 master br0
sudo ip link set eth1 master br0

# Costo STP per porta
sudo ip link set eth0 type bridge_slave cost 100
sudo ip link set eth1 type bridge_slave cost 200

# Priorità per porta (STP)
sudo ip link set eth0 type bridge_slave priority 32

# Attivare
sudo ip link set br0 up
sudo ip addr add 192.168.1.100/24 dev br0

# Verificare
bridge link show
bridge fdb show br br0
bridge stp show
```

### Bridge per KVM/QEMU

```bash
# Bridge per macchine virtuali
sudo ip link add virbr_prod type bridge
sudo ip link set virbr_prod up
sudo ip addr add 192.168.122.1/24 dev virbr_prod

# Abilitare NAT per le VM
sudo nft add table inet vm_nat
sudo nft add chain inet vm_nat postrouting { type nat hook postrouting priority 100 \; }
sudo nft add rule inet vm_nat postrouting ip saddr 192.168.122.0/24 oifname "eth0" masquerade

# Abilitare forwarding
sudo sysctl -w net.ipv4.ip_forward=1

# In libvirt, definire la rete nel XML della VM:
# <interface type='bridge'>
#   <source bridge='virbr_prod'/>
#   <model type='virtio'/>
# </interface>
```

### Bridge con Netplan (Ubuntu)

```yaml
# /etc/netplan/01-bridge.yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: false
    eth1:
      dhcp4: false
  bridges:
    br0:
      interfaces: [eth0, eth1]
      addresses: [192.168.1.100/24]
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
      parameters:
        stp: true
        forward-delay: 4
        max-age: 20
```

---

## DNS — Catena di Risoluzione Completa

La risoluzione DNS su Linux attraversa una catena di componenti configurabili. Comprendere ogni anello è essenziale per il debug di problemi di risoluzione nomi.

### Flusso di Risoluzione (nsswitch → resolver → upstream)

```
Applicazione chiama getaddrinfo("example.com")
    ↓
glibc NSS (Name Service Switch)
    ↓ legge /etc/nsswitch.conf
    ↓ hosts: files mymachines resolve [!UNAVAIL=return] dns
    ↓
    ├─ files → /etc/hosts
    ├─ mymachines → systemd-machined (nomi VM/container locali)
    ├─ resolve → systemd-resolved (via D-Bus o stub 127.0.0.53)
    │     ├─ Cache locale
    │     ├─ mDNS (.local)
    │     ├─ LLMNR (link-local)
    │     ├─ DNSSEC (validazione firme)
    │     ├─ DNS-over-TLS (DoT, porta 853)
    │     └─ Split DNS (route diverse per domini diversi)
    └─ dns → resolver classico via /etc/resolv.conf
```

### /etc/nsswitch.conf — Ordine di Risoluzione

```bash
# Configurazione tipica moderna (con systemd-resolved)
hosts: mymachines resolve [!UNAVAIL=return] files dns

# Significato:
# mymachines  → cerca tra VM/container systemd
# resolve     → systemd-resolved (cache, mDNS, LLMNR, split DNS)
# [!UNAVAIL=return] → se resolved è disponibile, non proseguire a dns
# files       → /etc/hosts
# dns         → fallback diretto via /etc/resolv.conf

# Configurazione legacy (senza systemd-resolved)
hosts: files dns

# Con mDNS (Avahi)
hosts: files mdns4_minimal [NOTFOUND=return] dns
```

### systemd-resolved — Architettura e Configurazione

`systemd-resolved` è il resolver DNS moderno presente in quasi tutte le distribuzioni con systemd. Opera come un servizio locale che ascolta su `127.0.0.53:53` (stub listener) e gestisce cache, DNSSEC, DNS-over-TLS e split DNS.

```bash
# Stato completo
resolvectl status

# Output per ciascuna interfaccia:
# - DNS Server corrente
# - Domini di ricerca (search domains)
# - DNSSEC: yes/no/allow-downgrade
# - DNS over TLS: yes/no/opportunistic
# - mDNS: yes/no/resolve
# - LLMNR: yes/no/resolve

# Query diagnostica
resolvectl query example.com
resolvectl query --type=MX example.com
resolvectl query --type=AAAA example.com

# Cache DNS
resolvectl statistics                # Hit/miss della cache
resolvectl flush-caches              # Svuotare cache
resolvectl reset-statistics          # Azzerare statistiche

# Configurare DNS per interfaccia
resolvectl dns eth0 8.8.8.8 8.8.4.4
resolvectl domain eth0 example.com   # Search domain
resolvectl dnssec eth0 yes           # Abilitare DNSSEC
resolvectl dnsovertls eth0 yes       # Abilitare DoT
```

### Configurazione Persistente di systemd-resolved

```ini
# /etc/systemd/resolved.conf
[Resolve]
# Server DNS globali
DNS=9.9.9.9#dns.quad9.net 149.112.112.112#dns.quad9.net
# Fallback DNS (usati se nessun DNS per-link configurato)
FallbackDNS=1.1.1.1#cloudflare-dns.com 8.8.8.8#dns.google

# DNSSEC
DNSSEC=allow-downgrade
# Opzioni: yes (strict), allow-downgrade (best effort), no

# DNS over TLS
DNSOverTLS=opportunistic
# Opzioni: yes (obbligatorio), opportunistic (se disponibile), no

# Cache
Cache=yes
# Opzioni: yes, no, no-negative (cache solo risposte positive)

# mDNS
MulticastDNS=resolve
# Opzioni: yes (resolve+respond), resolve (solo resolve), no

# LLMNR
LLMNR=resolve

# Domini di ricerca globali
Domains=example.com internal.corp

# Stub listener
DNSStubListener=yes
# Se disabilitato, le app devono risolvere direttamente
```

```bash
# Dopo modifica, riavviare
sudo systemctl restart systemd-resolved
```

### Il File /etc/resolv.conf — Varianti di Symlink

Su sistemi moderni, `/etc/resolv.conf` può essere gestito in modi diversi. Capire quale variante è attiva è fondamentale per il debug DNS.

```bash
# Verificare cosa è /etc/resolv.conf
ls -la /etc/resolv.conf

# Variante 1: stub di systemd-resolved (raccomandato)
# /etc/resolv.conf → /run/systemd/resolve/stub-resolv.conf
# Contiene: nameserver 127.0.0.53
# Le app passano per il resolver locale con cache, DNSSEC, DoT

# Variante 2: resolv.conf diretto di systemd-resolved
# /etc/resolv.conf → /run/systemd/resolve/resolv.conf
# Contiene: i nameserver upstream effettivi
# Le app bypassano il resolver locale (no cache, no DNSSEC)

# Variante 3: file statico (gestito manualmente)
# /etc/resolv.conf è un file regolare
# Pieno controllo, ma sovrascitto da DHCP/NetworkManager se non protetto

# Variante 4: resolvconf (compatibility layer)
# /etc/resolv.conf → generato da resolvconf/openresolv
# Aggrega input da DHCP client, VPN, etc.

# Fix: forzare lo stub di systemd-resolved
sudo ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
```

### Split DNS (Routing DNS per Dominio)

Split DNS permette di inviare query per domini specifici a server DNS diversi. Essenziale con VPN aziendali.

```bash
# Con systemd-resolved: query per corp.example.com vanno al DNS aziendale
resolvectl domain wg0 "~corp.example.com" "~internal.corp"
resolvectl dns wg0 10.0.0.53

# Il "~" davanti al dominio indica che è un routing domain (non search domain)
# Le query per *.corp.example.com vengono inviate a 10.0.0.53
# Tutte le altre query usano il DNS di default

# Con NetworkManager
nmcli connection modify "vpn-work" ipv4.dns "10.0.0.53"
nmcli connection modify "vpn-work" ipv4.dns-search "~corp.example.com,~internal.corp"
```

### mDNS (Multicast DNS) e LLMNR

mDNS (RFC 6762) risolve nomi nel dominio `.local` sulla rete locale senza bisogno di un server DNS centralizzato. LLMNR (Link-Local Multicast Name Resolution) è un protocollo simile usato da Windows.

```bash
# Verificare supporto mDNS
resolvectl status | grep -i mdns

# Risolvere un host .local
resolvectl query myserver.local
avahi-resolve -n myserver.local         # Con Avahi
avahi-browse -at                         # Scoprire servizi sulla rete locale

# Pubblicare il proprio hostname via mDNS
sudo hostnamectl set-hostname myhost    # systemd pubblica myhost.local

# Firewall: aprire porta mDNS
sudo nft add rule inet filter input udp dport 5353 accept
```

### DNSSEC — Verifica delle Firme DNS

DNSSEC protegge contro la falsificazione delle risposte DNS verificando le firme crittografiche nella catena di trust dalla root DNS.

```bash
# Verificare che DNSSEC funzioni
resolvectl query --type=DNSKEY example.com
dig +dnssec example.com

# Test: dominio con DNSSEC valido
dig +dnssec +short sigok.verteiltesysteme.net
# Deve restituire un indirizzo IP

# Test: dominio con DNSSEC invalido (deve fallire)
dig +dnssec +short sigfail.verteiltesysteme.net
# Con DNSSEC attivo, la risoluzione deve fallire (SERVFAIL)

# Tracciare la catena DNSSEC
dig +trace +dnssec example.com
```

### DNS-over-TLS (DoT) e DNS-over-HTTPS (DoH)

```bash
# DoT con systemd-resolved (porta 853)
# In /etc/systemd/resolved.conf:
# DNS=9.9.9.9#dns.quad9.net
# DNSOverTLS=yes

# Verificare che DoT sia attivo
resolvectl status | grep "DNS over TLS"

# Test manuale DoT
openssl s_client -connect 9.9.9.9:853 -servername dns.quad9.net

# DoH con client dedicato (systemd-resolved non supporta DoH nativamente)
# Opzioni: dnscrypt-proxy, stubby, cloudflared
# Esempio con cloudflared:
# cloudflared proxy-dns --port 5053 --upstream https://dns.quad9.net/dns-query
```

---

## Server DHCP (ISC, dnsmasq, Kea)

### dnsmasq — DHCP + DNS Leggero

`dnsmasq` è ideale per reti piccole-medie: combina server DHCP, server DNS caching e server TFTP in un unico binario leggero.

```ini
# /etc/dnsmasq.conf

# Interfaccia
interface=eth1
bind-interfaces

# DHCP range
dhcp-range=192.168.10.100,192.168.10.200,255.255.255.0,12h

# Gateway
dhcp-option=option:router,192.168.10.1

# DNS
dhcp-option=option:dns-server,192.168.10.1,8.8.8.8

# Dominio
domain=lab.local

# Lease statici (MAC → IP)
dhcp-host=00:11:22:33:44:55,192.168.10.50,server1
dhcp-host=AA:BB:CC:DD:EE:FF,192.168.10.51,server2

# PXE boot
dhcp-boot=pxelinux.0,pxeserver,192.168.10.1

# DNS upstream
server=8.8.8.8
server=8.8.4.4

# Cache DNS
cache-size=1000

# Log
log-dhcp
log-queries
```

```bash
# Gestione
sudo systemctl enable --now dnsmasq
sudo systemctl status dnsmasq
# Lease attivi
cat /var/lib/misc/dnsmasq.leases
```

### ISC Kea — DHCP Server Moderno

ISC Kea è il successore di ISC DHCP server, con configurazione JSON, supporto database backend (MySQL, PostgreSQL) e API REST per la gestione.

```json
// /etc/kea/kea-dhcp4.conf (estratto)
{
  "Dhcp4": {
    "interfaces-config": {
      "interfaces": ["eth1"]
    },
    "lease-database": {
      "type": "memfile",
      "lfc-interval": 3600
    },
    "subnet4": [{
      "subnet": "192.168.10.0/24",
      "pools": [{"pool": "192.168.10.100 - 192.168.10.200"}],
      "option-data": [
        {"name": "routers", "data": "192.168.10.1"},
        {"name": "domain-name-servers", "data": "8.8.8.8, 8.8.4.4"},
        {"name": "domain-name", "data": "lab.local"}
      ],
      "reservations": [
        {
          "hw-address": "00:11:22:33:44:55",
          "ip-address": "192.168.10.50",
          "hostname": "server1"
        }
      ]
    }]
  }
}
```

```bash
sudo systemctl enable --now kea-dhcp4-server
```

---

## IPv6 — Configurazione Completa

IPv6 è lo standard di indirizzamento attuale. Il kernel Linux supporta IPv6 nativamente con stack completo: SLAAC, DHCPv6, NDP (Neighbor Discovery Protocol), privacy extensions e dual-stack.

### Indirizzi IPv6 — Tipi e Scope

```
┌──────────────────┬────────────────────────┬──────────────────────────────────────┐
│ Tipo             │ Prefisso               │ Descrizione                          │
├──────────────────┼────────────────────────┼──────────────────────────────────────┤
│ Link-local       │ fe80::/10              │ Automatico, non routabile, per ogni  │
│                  │                        │ interfaccia (come 169.254.x.x IPv4)  │
├──────────────────┼────────────────────────┼──────────────────────────────────────┤
│ Global Unicast   │ 2000::/3               │ Routabile su Internet (come IP       │
│ (GUA)            │                        │ pubblici IPv4)                       │
├──────────────────┼────────────────────────┼──────────────────────────────────────┤
│ Unique Local     │ fd00::/8 (fc00::/7)    │ Privato, non routabile su Internet   │
│ (ULA)            │                        │ (come 10.x.x.x, 192.168.x.x IPv4)   │
├──────────────────┼────────────────────────┼──────────────────────────────────────┤
│ Multicast        │ ff00::/8               │ Uno-a-molti (no broadcast in IPv6)   │
├──────────────────┼────────────────────────┼──────────────────────────────────────┤
│ Loopback         │ ::1/128                │ Equivalente di 127.0.0.1             │
├──────────────────┼────────────────────────┼──────────────────────────────────────┤
│ Unspecified      │ ::/128                 │ Equivalente di 0.0.0.0               │
└──────────────────┴────────────────────────┴──────────────────────────────────────┘
```

### Comandi ip -6

```bash
# Visualizzare indirizzi IPv6
ip -6 addr show
ip -6 addr show dev eth0
ip -6 addr show scope global      # Solo GUA
ip -6 addr show scope link        # Solo link-local
ip -6 addr show temporary         # Solo privacy addresses

# Aggiungere indirizzo IPv6 statico
ip -6 addr add 2001:db8::100/64 dev eth0
ip -6 addr add fd00:1::100/64 dev eth0   # ULA

# Routing IPv6
ip -6 route show
ip -6 route add default via 2001:db8::1
ip -6 route add 2001:db8:1::/48 via 2001:db8::1
ip -6 route get 2001:4860:4860::8888    # Quale route viene usata

# Neighbor Discovery (equivalente ARP per IPv6)
ip -6 neigh show
ip -6 neigh add 2001:db8::1 lladdr 00:11:22:33:44:55 dev eth0

# Test connettività IPv6
ping -6 ::1                        # Loopback
ping -6 fe80::1%eth0               # Link-local (serve specificare l'interfaccia)
ping -6 2001:4860:4860::8888       # Google DNS IPv6
traceroute -6 ipv6.google.com
```

### SLAAC (Stateless Address Autoconfiguration)

SLAAC permette ai dispositivi di auto-configurare un indirizzo IPv6 globale senza server DHCP, basandosi sui Router Advertisement (RA) inviati dal router locale.

```bash
# SLAAC è abilitato di default in Linux
# Il kernel ascolta i RA e genera automaticamente:
# 1. Link-local address (fe80::...)
# 2. Global address (dal prefisso ricevuto + interface ID)
# 3. Default route (via il router che invia il RA)

# Verificare che SLAAC sia abilitato
sysctl net.ipv6.conf.eth0.accept_ra
# 1 = accetta RA (se non è configurato come router)
# 2 = accetta RA anche se ip forwarding è abilitato

sysctl net.ipv6.conf.eth0.autoconf
# 1 = genera automaticamente indirizzi SLAAC
```

### Privacy Extensions (RFC 8981)

SLAAC standard genera l'interface ID dal MAC address, rendendo il dispositivo tracciabile. Le privacy extensions generano interface ID casuali con scadenza periodica.

```bash
# Abilitare privacy extensions
sudo sysctl -w net.ipv6.conf.all.use_tempaddr=2
sudo sysctl -w net.ipv6.conf.default.use_tempaddr=2
sudo sysctl -w net.ipv6.conf.eth0.use_tempaddr=2
# 0 = disabilitato
# 1 = genera indirizzi temporanei ma preferisce quelli stabili
# 2 = genera indirizzi temporanei e li preferisce (raccomandato)

# Durata degli indirizzi temporanei
sudo sysctl -w net.ipv6.conf.all.temp_valid_lft=604800    # 7 giorni
sudo sysctl -w net.ipv6.conf.all.temp_prefered_lft=86400  # 1 giorno

# Persistente in /etc/sysctl.d/40-ipv6-privacy.conf:
net.ipv6.conf.all.use_tempaddr = 2
net.ipv6.conf.default.use_tempaddr = 2

# Con NetworkManager
nmcli connection modify "server" ipv6.ip6-privacy 2

# Con systemd-networkd
# [Network]
# IPv6PrivacyExtensions=prefer-public
# oppure
# IPv6PrivacyExtensions=yes
```

### DHCPv6

DHCPv6 è l'alternativa stateful a SLAAC: il server assegna indirizzi e opzioni (DNS, NTP, ecc.).

```bash
# Configurare DHCPv6 client con systemd-networkd
# /etc/systemd/network/10-eth0.network
# [Network]
# DHCP=ipv6
# [DHCPv6]
# UseDNS=yes
# UseNTP=yes

# Con NetworkManager
nmcli connection modify "server" ipv6.method dhcp

# Con netplan
# network:
#   ethernets:
#     eth0:
#       dhcp6: true
```

### Router Advertisement con radvd

`radvd` invia Router Advertisement sulla rete locale, necessario per SLAAC.

```ini
# /etc/radvd.conf
interface eth1
{
    AdvSendAdvert on;
    MinRtrAdvInterval 30;
    MaxRtrAdvInterval 100;

    # Prefisso per SLAAC
    prefix 2001:db8:1::/64
    {
        AdvOnLink on;
        AdvAutonomous on;        # Abilita SLAAC
        AdvRouterAddr on;
        AdvValidLifetime 86400;
        AdvPreferredLifetime 14400;
    };

    # DNS ricorsivo (RDNSS, RFC 8106)
    RDNSS 2001:4860:4860::8888 2001:4860:4860::8844
    {
        AdvRDNSSLifetime 600;
    };
};
```

```bash
sudo systemctl enable --now radvd
# Verificare i RA con radvdump
radvdump
```

### Dual-Stack e Disabilitare IPv6

```bash
# Dual-stack è la configurazione di default: IPv4 e IPv6 coesistono

# Disabilitare IPv6 (se necessario, non raccomandato)
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=1
sudo sysctl -w net.ipv6.conf.default.disable_ipv6=1
# Persistente: aggiungere a /etc/sysctl.d/99-no-ipv6.conf

# Disabilitare solo su un'interfaccia
sudo sysctl -w net.ipv6.conf.eth0.disable_ipv6=1

# Riabilitare
sudo sysctl -w net.ipv6.conf.all.disable_ipv6=0

# Verificare stato
cat /proc/sys/net/ipv6/conf/all/disable_ipv6
```

---

## TCP/IP Tuning (sysctl)

Il tuning dei parametri del kernel è essenziale per ottenere performance ottimali su server ad alto carico, link ad alta larghezza di banda o collegamenti con alta latenza (WAN, intercontinentali). I parametri si gestiscono via `sysctl` e risiedono nel filesystem virtuale `/proc/sys/net/`.

### Buffer TCP — rmem e wmem

I buffer TCP determinano quanta memoria il kernel alloca per ciascun socket TCP in ricezione e trasmissione. I tre valori sono: minimo, default, massimo (in byte).

```bash
# Valori di default (generalmente troppo bassi per reti veloci)
sysctl net.ipv4.tcp_rmem
# 4096  131072  6291456  (min 4KB, default 128KB, max 6MB)

sysctl net.ipv4.tcp_wmem
# 4096  16384   4194304  (min 4KB, default 16KB, max 4MB)

# Per reti 10G
sudo sysctl -w net.ipv4.tcp_rmem="4096 131072 134217728"   # max 128MB
sudo sysctl -w net.ipv4.tcp_wmem="4096 131072 134217728"   # max 128MB

# Per reti 100G
sudo sysctl -w net.ipv4.tcp_rmem="4096 131072 536870912"   # max 512MB
sudo sysctl -w net.ipv4.tcp_wmem="4096 131072 536870912"   # max 512MB

# Buffer core (non TCP-specific, per tutti i protocolli)
sudo sysctl -w net.core.rmem_max=536870912
sudo sysctl -w net.core.wmem_max=536870912
sudo sysctl -w net.core.rmem_default=131072
sudo sysctl -w net.core.wmem_default=131072

# Nota: il kernel usa l'auto-tuning per allocare dinamicamente
# tra min e max. Aumentare il max non spreca memoria.
```

### BBR — Congestion Control Moderno

BBR (Bottleneck Bandwidth and Round-trip propagation time), sviluppato da Google, è superiore a CUBIC (default) sulle connessioni WAN, specialmente con packet loss. BBR non riduce la finestra di congestione al primo segnale di perdita, mantenendo throughput elevato.

```bash
# Verificare algoritmo corrente
sysctl net.ipv4.tcp_congestion_control
sysctl net.ipv4.tcp_available_congestion_control

# Abilitare BBR
sudo modprobe tcp_bbr
sudo sysctl -w net.ipv4.tcp_congestion_control=bbr

# qdisc raccomandato con BBR: fq (Fair Queue)
# BBR + fq abilita il pacing dei pacchetti per evitare burst
sudo sysctl -w net.core.default_qdisc=fq

# Persistente in /etc/sysctl.d/50-bbr.conf:
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr

# Verificare che BBR sia attivo sulle connessioni
ss -ti | grep bbr
```

### TCP Fast Open (TFO)

TFO riduce la latenza delle connessioni TCP ripetute, permettendo di inviare dati già nel SYN (primo pacchetto della connessione).

```bash
# Abilitare TFO
sudo sysctl -w net.ipv4.tcp_fastopen=3
# 0 = disabilitato
# 1 = abilitato lato client
# 2 = abilitato lato server
# 3 = abilitato entrambi (raccomandato)
```

### Backlog e Connessioni

```bash
# Coda di connessioni pendenti (listen backlog)
sudo sysctl -w net.core.somaxconn=65535
# Default: 4096 (era 128 su kernel vecchi)
# Per server HTTP/reverse proxy ad alto carico

# Coda SYN (connessioni half-open)
sudo sysctl -w net.ipv4.tcp_max_syn_backlog=65535

# Connessioni TIME_WAIT
sudo sysctl -w net.ipv4.tcp_tw_reuse=1
# Riuso dei socket in TIME_WAIT per nuove connessioni (sicuro)
# Nota: tcp_tw_recycle è stato rimosso dal kernel (pericoloso con NAT)

# Fin timeout (quanto restano in FIN_WAIT_2)
sudo sysctl -w net.ipv4.tcp_fin_timeout=15
# Default: 60 secondi (troppo per server ad alto carico)

# Keepalive (detect connessioni morte)
sudo sysctl -w net.ipv4.tcp_keepalive_time=600    # Prima probe dopo 600s
sudo sysctl -w net.ipv4.tcp_keepalive_intvl=30     # Intervallo tra probe
sudo sysctl -w net.ipv4.tcp_keepalive_probes=5     # Numero probe
```

### Parametri di Rete Generali

```bash
# Netdev budget — quanti pacchetti processare per poll NAPI
sudo sysctl -w net.core.netdev_budget=600
sudo sysctl -w net.core.netdev_budget_usecs=8000
# Aumentare su server con traffico intenso e NIC veloci

# Backlog di pacchetti in ingresso
sudo sysctl -w net.core.netdev_max_backlog=65536
# Default: 1000 (troppo basso per NIC 10G+)

# IP forwarding
sudo sysctl -w net.ipv4.ip_forward=1
sudo sysctl -w net.ipv6.conf.all.forwarding=1

# Numero massimo di connessioni conntrack
sudo sysctl -w net.netfilter.nf_conntrack_max=1048576
# Default: 65536 (troppo basso per firewall/NAT con molte connessioni)
# Ciascuna entry occupa ~320 byte: 1M entries ≈ 320MB di RAM

# Timeout conntrack (ridurre per liberare entry più velocemente)
sudo sysctl -w net.netfilter.nf_conntrack_tcp_timeout_established=3600
# Default: 432000 (5 giorni, eccessivo per la maggior parte degli usi)

# ARP cache
sudo sysctl -w net.ipv4.neigh.default.gc_thresh1=4096
sudo sysctl -w net.ipv4.neigh.default.gc_thresh2=8192
sudo sysctl -w net.ipv4.neigh.default.gc_thresh3=16384
```

### File sysctl.conf Completo per Server ad Alto Carico

```bash
# /etc/sysctl.d/90-network-performance.conf

# --- Buffer TCP ---
net.ipv4.tcp_rmem = 4096 131072 134217728
net.ipv4.tcp_wmem = 4096 131072 134217728
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.core.rmem_default = 131072
net.core.wmem_default = 131072

# --- Congestion Control ---
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr

# --- TCP Options ---
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_window_scaling = 1
net.ipv4.tcp_timestamps = 1
net.ipv4.tcp_sack = 1
net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_max_syn_backlog = 65535

# --- Connessioni ---
net.core.somaxconn = 65535
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_keepalive_probes = 5

# --- Backlog e NAPI ---
net.core.netdev_max_backlog = 65536
net.core.netdev_budget = 600
net.core.netdev_budget_usecs = 8000

# --- Conntrack ---
net.netfilter.nf_conntrack_max = 1048576
net.netfilter.nf_conntrack_tcp_timeout_established = 3600

# --- IP Forwarding ---
net.ipv4.ip_forward = 1
```

```bash
# Applicare
sudo sysctl -p /etc/sysctl.d/90-network-performance.conf
```

### NUMA-Aware Networking

Su server multi-socket, le interrupt della NIC e i buffer devono essere allocati sullo stesso nodo NUMA della NIC per minimizzare la latenza.

```bash
# Verificare nodo NUMA della NIC
cat /sys/class/net/eth0/device/numa_node

# Verificare distribuzione interrupt (IRQ)
cat /proc/interrupts | grep eth0

# Affinità interrupt: assegnare gli IRQ ai core del nodo NUMA corretto
# Esempio: NIC su NUMA node 0, core 0-7
echo 0-7 | sudo tee /proc/irq/<IRQ_NUM>/smp_affinity_list

# Receive Packet Steering (RPS) — distribuzione software dei pacchetti
echo "ff" | sudo tee /sys/class/net/eth0/queues/rx-0/rps_cpus

# Receive Flow Steering (RFS) — indirizzare pacchetti al core dell'applicazione
echo 32768 | sudo tee /proc/sys/net/core/rps_sock_flow_entries
echo 4096 | sudo tee /sys/class/net/eth0/queues/rx-0/rps_flow_cnt

# XPS (Transmit Packet Steering)
echo "ff" | sudo tee /sys/class/net/eth0/queues/tx-0/xps_cpus
```

---

## tc — Traffic Control e QoS

Il sottosistema `tc` (Traffic Control) del kernel Linux permette di modellare il traffico in uscita: limitare la banda, prioritizzare classi di traffico, simulare condizioni di rete e implementare QoS (Quality of Service). Opera nel path di egress, tra lo stack di rete e il driver della NIC.

### Architettura tc

```
Pacchetto in uscita dal kernel
    ↓
┌──────────────────────────────────────┐
│           Root Qdisc                 │
│  ┌──────────────────────────────┐    │
│  │  Classificatore (filter)     │    │
│  │  u32, flower, cgroup, bpf   │    │
│  └──────┬───────────┬──────────┘    │
│         ↓           ↓               │
│  ┌─────────┐ ┌─────────┐           │
│  │ Class 1 │ │ Class 2 │           │
│  │ (rate,  │ │ (rate,  │           │
│  │ ceil)   │ │ ceil)   │           │
│  └────┬────┘ └────┬────┘           │
│       ↓           ↓                 │
│  ┌─────────┐ ┌─────────┐           │
│  │ Leaf    │ │ Leaf    │           │
│  │ Qdisc  │ │ Qdisc  │           │
│  │(fq_codel│ │(fq_codel│           │
│  │ CAKE)  │ │ pfifo) │           │
│  └─────────┘ └─────────┘           │
└──────────────────────────────────────┘
    ↓
Driver NIC → Rete
```

**Componenti fondamentali:**

- **Qdisc (Queuing Discipline)**: algoritmo di accodamento e rilascio pacchetti
- **Classi**: suddivisioni gerarchiche con rate garantito e ceiling
- **Filtri**: regole che classificano i pacchetti nelle classi

### Qdisc Classless — fq_codel e CAKE

Le qdisc senza classi gestiscono il traffico senza suddivisioni.

```bash
# fq_codel (Fair Queue + Controlled Delay)
# Default su molte distro. Ottimo per ridurre il bufferbloat.
sudo tc qdisc replace dev eth0 root fq_codel

# Con parametri
sudo tc qdisc replace dev eth0 root fq_codel \
  target 5ms \         # Latenza target (default 5ms)
  interval 100ms \     # Intervallo di misurazione
  flows 1024 \         # Numero massimo di flussi
  quantum 1514 \       # Byte per round
  limit 10240          # Massimo pacchetti in coda

# CAKE (Common Applications Kept Enhanced)
# Evoluzione di fq_codel, tutto in uno: shaping + AQM + fairness
sudo tc qdisc replace dev eth0 root cake bandwidth 100mbit

# CAKE con opzioni avanzate
sudo tc qdisc replace dev eth0 root cake \
  bandwidth 100mbit \   # Limite banda
  besteffort \          # Modalità: besteffort, diffserv3, diffserv4, diffserv8
  flowblind \           # No isolamento per flusso (o: srchost, dsthost, hosts)
  nat \                 # Tenere conto del NAT per la fairness
  wash \                # Rimuovere DSCP marking
  ack-filter \          # Filtrare ACK ridondanti (riduce overhead su uplink asimmetrico)
  rtt 50ms              # RTT stimato della connessione

# Visualizzare statistiche
tc -s qdisc show dev eth0
```

### HTB — Hierarchical Token Bucket

HTB è la qdisc classful più usata. Permette di definire una gerarchia di classi con rate garantito e ceiling (burst), e di assegnare il traffico alle classi con filtri.

```bash
# Scenario: uplink 100 Mbps, tre classi di traffico
# 1:10  Critico (SSH, DNS)    — garantiti 40 Mbps, max 100 Mbps
# 1:20  Normale (HTTP/HTTPS)  — garantiti 40 Mbps, max 100 Mbps
# 1:30  Best-effort (altro)   — garantiti 20 Mbps, max 80 Mbps

# Eliminare qdisc esistente
sudo tc qdisc del dev eth0 root 2>/dev/null

# Root qdisc HTB
sudo tc qdisc add dev eth0 root handle 1: htb default 30

# Classe root (tetto totale)
sudo tc class add dev eth0 parent 1: classid 1:1 htb rate 100mbit ceil 100mbit

# Sottoclassi
sudo tc class add dev eth0 parent 1:1 classid 1:10 htb rate 40mbit ceil 100mbit prio 1
sudo tc class add dev eth0 parent 1:1 classid 1:20 htb rate 40mbit ceil 100mbit prio 2
sudo tc class add dev eth0 parent 1:1 classid 1:30 htb rate 20mbit ceil 80mbit prio 3

# Leaf qdisc per ogni classe (fq_codel per fairness intra-classe)
sudo tc qdisc add dev eth0 parent 1:10 handle 10: fq_codel
sudo tc qdisc add dev eth0 parent 1:20 handle 20: fq_codel
sudo tc qdisc add dev eth0 parent 1:30 handle 30: fq_codel

# Filtri per classificare il traffico
# SSH e DNS → classe critica (1:10)
sudo tc filter add dev eth0 parent 1: protocol ip prio 1 u32 \
  match ip dport 22 0xffff flowid 1:10
sudo tc filter add dev eth0 parent 1: protocol ip prio 1 u32 \
  match ip dport 53 0xffff flowid 1:10
sudo tc filter add dev eth0 parent 1: protocol ip prio 1 u32 \
  match ip sport 53 0xffff flowid 1:10

# HTTP/HTTPS → classe normale (1:20)
sudo tc filter add dev eth0 parent 1: protocol ip prio 2 u32 \
  match ip dport 80 0xffff flowid 1:20
sudo tc filter add dev eth0 parent 1: protocol ip prio 2 u32 \
  match ip dport 443 0xffff flowid 1:20

# Tutto il resto → best-effort (1:30) tramite il default

# Verificare configurazione
tc -s qdisc show dev eth0
tc -s class show dev eth0
tc -s filter show dev eth0
```

### Filtri flower (alternativa moderna a u32)

```bash
# Il filtro flower è più leggibile e potente di u32
# Classificare per porta destinazione
sudo tc filter add dev eth0 parent 1: protocol ip flower \
  ip_proto tcp dst_port 22 \
  classid 1:10

# Per IP sorgente
sudo tc filter add dev eth0 parent 1: protocol ip flower \
  src_ip 10.0.0.0/8 \
  classid 1:20

# Per DSCP
sudo tc filter add dev eth0 parent 1: protocol ip flower \
  ip_tos 0xb8/0xfc \
  classid 1:10
```

### Policing (Ingress)

tc opera normalmente sull'egress, ma supporta il policing in ingresso per limitare il traffico ricevuto.

```bash
# Aggiungere qdisc ingress
sudo tc qdisc add dev eth0 ingress

# Limitare il traffico in ingresso a 100 Mbps
sudo tc filter add dev eth0 parent ffff: protocol ip u32 \
  match u32 0 0 \
  police rate 100mbit burst 1mbit drop \
  flowid :1
```

### Simulare Condizioni di Rete con netem

`netem` (Network Emulator) simula latenza, jitter, packet loss e riordino. Essenziale per testing.

```bash
# Aggiungere latenza
sudo tc qdisc add dev eth0 root netem delay 100ms

# Latenza con jitter
sudo tc qdisc add dev eth0 root netem delay 100ms 20ms

# Packet loss (5%)
sudo tc qdisc add dev eth0 root netem loss 5%

# Duplicazione pacchetti (1%)
sudo tc qdisc add dev eth0 root netem duplicate 1%

# Riordino pacchetti
sudo tc qdisc add dev eth0 root netem delay 100ms reorder 25% 50%

# Combinazione: latenza + loss + jitter
sudo tc qdisc add dev eth0 root netem delay 50ms 10ms loss 2%

# Rimuovere
sudo tc qdisc del dev eth0 root
```

### Integrazione nftables + tc

nftables può marcare i pacchetti con un valore (meta mark), che poi tc usa per la classificazione tramite il filtro `fw`.

```bash
# In nftables: marcare il traffico
nft add rule inet filter output tcp dport 22 meta mark set 10
nft add rule inet filter output tcp dport { 80, 443 } meta mark set 20

# In tc: usare il filtro fw per leggere i mark
sudo tc filter add dev eth0 parent 1: protocol ip prio 1 handle 10 fw classid 1:10
sudo tc filter add dev eth0 parent 1: protocol ip prio 2 handle 20 fw classid 1:20
```

---

## Strumenti Avanzati di Diagnosi Rete

Questa sezione espande la diagnosi di rete con approfondimenti su `ss`, `ip`, `traceroute`, `mtr` e `tcpdump` per scenari complessi.

### ss — Socket Statistics (Deep Dive)

`ss` è il sostituto moderno di `netstat`, molto più veloce perché interroga direttamente le strutture del kernel via netlink.

```bash
# Connessioni TCP con informazioni interne dettagliate
ss -ti
# Output: RTT, cwnd (congestion window), retransmits, bytes_acked,
# pacing_rate, delivery_rate, busy_time, rcv_rtt, rcv_space

# Filtrare per stato
ss -t state established
ss -t state time-wait
ss -t state close-wait
ss -t state syn-sent
ss -t state listening

# Filtrare per porta
ss -tn sport = :443                 # Sorgente porta 443
ss -tn dport = :3306                # Destinazione porta 3306
ss -tn sport gt :1024               # Porte effimere
ss -tn '( dport = :80 or dport = :443 )'  # HTTP o HTTPS

# Filtrare per IP
ss -tn dst 10.0.0.0/8              # Destinazione subnet 10.x
ss -tn src 192.168.1.100           # Sorgente specifica

# Connessioni con dimensione coda
ss -tnl                             # Listen con Send-Q (backlog)
# Send-Q in stato LISTEN = backlog massimo
# Recv-Q in stato LISTEN = connessioni in attesa di accept()

# Socket con memoria dettagliata
ss -tm                              # Mostra allocazione memoria per socket
# skmem: rb=buffer_ricezione wmem_alloc=memoria_scrittura_allocata

# Socket UNIX
ss -xln                             # Socket UNIX in ascolto
ss -xp                              # Socket UNIX con processo

# Connessioni con timer
ss -tno                             # Timer: keepalive, retransmit, timewait

# Conteggio connessioni per stato
ss -s
# Output:
# Total: XXX
# TCP:   XXX (estab X, closed X, orphaned X, timewait X)
```

### mtr — Traceroute Avanzato

`mtr` combina traceroute e ping in un singolo tool interattivo, mostrando latenza e packet loss per ogni hop in tempo reale.

```bash
# Modalità interattiva
mtr 8.8.8.8

# Report (non interattivo, ideale per log e ticket)
mtr --report -c 100 8.8.8.8        # 100 cicli
mtr --report -c 100 -w 8.8.8.8     # Wide report (nomi host completi)

# JSON output (per parsing automatico)
mtr --json -c 50 8.8.8.8

# Via TCP (se ICMP è bloccato)
mtr --tcp -P 443 example.com       # TCP porta 443
mtr --tcp -P 80 example.com        # TCP porta 80

# Via UDP
mtr --udp -P 53 8.8.8.8

# Con specifica dell'interfaccia sorgente
mtr -I eth0 8.8.8.8
mtr -a 10.0.0.100 8.8.8.8          # IP sorgente specifico

# Leggere l'output:
# Loss% — percentuale pacchetti persi (>5% = problema)
# Snt   — pacchetti inviati
# Last  — latenza ultimo pacchetto (ms)
# Avg   — latenza media
# Best  — latenza minima
# Wrst  — latenza massima
# StDev — deviazione standard (alta = jitter)

# Attenzione: packet loss su un hop intermedio con 0% loss sull'hop finale
# indica rate limiting ICMP sul router, NON un problema reale
```

### tcpdump — Pattern Avanzati di Cattura

```bash
# Catturare solo il handshake TCP (SYN, SYN-ACK, ACK)
sudo tcpdump -i eth0 'tcp[tcpflags] & (tcp-syn|tcp-ack) != 0'

# Solo pacchetti RST (connessioni rifiutate/resettate)
sudo tcpdump -i eth0 'tcp[tcpflags] & (tcp-rst) != 0'

# Catturare DNS queries
sudo tcpdump -i eth0 -nn 'udp port 53'

# Catturare HTTP GET requests (in chiaro)
sudo tcpdump -i eth0 -A 'tcp port 80 and (((ip[2:2] - ((ip[0]&0xf)<<2)) - ((tcp[12]&0xf0)>>2)) != 0)'

# Catturare ARP
sudo tcpdump -i eth0 -nn arp

# Catturare con rotazione file (ideale per monitoraggio continuo)
sudo tcpdump -i eth0 -w /var/log/capture_%Y%m%d_%H%M%S.pcap \
  -G 3600 \           # Nuovo file ogni ora
  -W 24 \             # Mantieni max 24 file
  -Z root             # Privilegi

# Catturare con limite dimensione file
sudo tcpdump -i eth0 -w capture.pcap -C 100     # Nuovo file ogni 100MB

# Catturare solo header (senza payload)
sudo tcpdump -i eth0 -s 96 -w headers_only.pcap

# Leggere pcap con filtro temporale
sudo tcpdump -r capture.pcap -t 'tcp port 443' | head -50
```

### Workflow di Troubleshooting Sistematico

```bash
# 1. Verificare stack L1-L2
ip link show                        # Interfaccia UP?
ethtool eth0                        # Velocità, duplex, link detected?
ip -s link show eth0                # Errori, drop, overrun?

# 2. Verificare L3
ip addr show                        # IP assegnato?
ip route show                       # Route presenti?
ip route get 8.8.8.8                # Percorso per la destinazione?
ping -c 3 <gateway>                 # Gateway raggiungibile?
ping -c 3 8.8.8.8                   # Internet raggiungibile (bypassa DNS)?

# 3. Verificare DNS (L7)
resolvectl status                   # Stato resolver
dig +short example.com              # Funziona DNS?
dig @8.8.8.8 example.com            # Funziona con DNS esterno?
cat /etc/resolv.conf                # Nameserver configurati?

# 4. Verificare firewall
sudo nft list ruleset               # Regole nftables
sudo iptables -L -n -v              # Regole iptables
sudo conntrack -L | grep <IP>       # Connessioni tracciate

# 5. Verificare servizio
ss -tuln | grep <PORT>              # Porta in ascolto?
curl -v http://localhost:<PORT>     # Servizio risponde?
journalctl -u <service> -f          # Log servizio

# 6. Catturare traffico
sudo tcpdump -i eth0 -nn host <IP> and port <PORT>
```

---

## nftables — Sintassi Avanzata e Funzionalità

Questa sezione espande la trattazione di nftables con funzionalità avanzate: set, map, meter, flowtable, ct helper e logging strutturato.

### Set (Insiemi)

I set permettono di raggruppare elementi (IP, porte, interfacce) e usarli nelle regole.

```bash
# Set anonimo (inline nella regola)
nft add rule inet filter input tcp dport { 22, 80, 443, 8080, 8443 } accept

# Set con nome (riutilizzabile e aggiornabile a runtime)
nft add set inet filter allowed_ports { type inet_service \; }
nft add element inet filter allowed_ports { 22, 80, 443 }
nft add rule inet filter input tcp dport @allowed_ports accept

# Set di indirizzi IP
nft add set inet filter trusted_ips { type ipv4_addr \; }
nft add element inet filter trusted_ips { 10.0.0.1, 10.0.0.2, 192.168.1.0/24 }
nft add rule inet filter input ip saddr @trusted_ips accept

# Set con timeout (gli elementi scadono automaticamente)
nft add set inet filter recent_ssh { type ipv4_addr \; timeout 5m \; }

# Set con flag (interval per CIDR, timeout per scadenza)
nft add set inet filter blocklist { type ipv4_addr \; flags interval,timeout \; }
nft add element inet filter blocklist { 203.0.113.0/24 timeout 1h }

# Aggiungere/rimuovere elementi a runtime
nft add element inet filter blocklist { 198.51.100.5 }
nft delete element inet filter blocklist { 198.51.100.5 }

# Listare elementi
nft list set inet filter blocklist
```

### Map (Mappe) e Verdict Map

Le map associano una chiave a un valore o a un verdetto (accept, drop, jump).

```bash
# Map di porta → marca (per QoS)
nft add map inet filter port_to_mark { type inet_service : mark \; }
nft add element inet filter port_to_mark { 22 : 0x10, 80 : 0x20, 443 : 0x20 }
nft add rule inet filter output meta mark set tcp dport map @port_to_mark

# Verdict map: decisione per porta
nft add map inet filter port_policy { type inet_service : verdict \; }
nft add element inet filter port_policy { 22 : accept, 80 : accept, 443 : accept }
nft add rule inet filter input tcp dport vmap @port_policy

# Map per DNAT (port forwarding dinamico)
nft add map inet nat port_forward { type inet_service : ipv4_addr . inet_service \; }
nft add element inet nat port_forward { 8080 : 192.168.1.100 . 80, 8443 : 192.168.1.100 . 443 }
nft add rule inet nat prerouting dnat tcp dport map @port_forward
```

### Meter (Rate Limiting Avanzato)

I meter mantengono lo stato per sorgente IP, permettendo rate limiting per-IP.

```bash
# Rate limiting SSH: max 3 connessioni al minuto per IP sorgente
nft add rule inet filter input tcp dport 22 \
  meter ssh_meter { ip saddr limit rate 3/minute } accept

# Con burst
nft add rule inet filter input tcp dport 80 \
  meter http_meter { ip saddr limit rate 100/second burst 200 packets } accept

# Rate limiting con drop esplicito
nft add rule inet filter input tcp dport 22 \
  meter ssh_limit { ip saddr limit rate over 3/minute } drop
```

### Flowtable (Hardware Offload)

I flowtable permettono di bypassare completamente netfilter per le connessioni stabilite, delegando il forwarding all'hardware o al fast-path del kernel. Incremento di throughput significativo per router/firewall.

```bash
# Definire il flowtable
nft add flowtable inet filter ft_offload { hook ingress priority 0 \; devices = { eth0, eth1 } \; }

# Aggiungere le connessioni stabilite al flowtable
nft add rule inet filter forward ct state established,related flow add @ft_offload accept

# Verificare
nft list flowtable inet filter ft_offload
conntrack -L | grep OFFLOAD
```

### Connection Tracking Helpers

I ct helper gestiscono protocolli con dati su connessioni secondarie (FTP, SIP, H.323).

```bash
# Helper per FTP
nft add ct helper inet filter ftp-standard { type "ftp" protocol tcp \; }
nft add rule inet filter input ct state related ct helper "ftp-standard" accept
nft add rule inet filter input tcp dport 21 ct helper set "ftp-standard" accept

# Helper per SIP (VoIP)
nft add ct helper inet filter sip-standard { type "sip" protocol udp \; }
nft add rule inet filter input udp dport 5060 ct helper set "sip-standard" accept
```

### Logging Strutturato e Counter

```bash
# Counter con nome (persistente e consultabile)
nft add counter inet filter cnt_ssh_accept
nft add counter inet filter cnt_ssh_drop

# Regole con counter
nft add rule inet filter input tcp dport 22 counter name cnt_ssh_accept accept
nft add rule inet filter input tcp dport 22 counter name cnt_ssh_drop drop

# Consultare i counter
nft list counters

# Logging con prefix e livello
nft add rule inet filter input tcp dport 23 log prefix "TELNET-ATTEMPT: " level warn counter drop

# Logging con rate limiting (evitare log flooding)
nft add rule inet filter input log prefix "FW-DROP: " level info limit rate 5/minute counter drop

# Logging con flag (mostra tutti i dettagli del pacchetto)
nft add rule inet filter input tcp dport 23 log prefix "BLOCKED: " flags all counter drop
```

### Convertire da iptables a nftables

```bash
# Tool di conversione automatica
sudo iptables-save > /tmp/iptables-rules.txt
sudo iptables-restore-translate -f /tmp/iptables-rules.txt > /tmp/nftables-rules.nft

# Importare
sudo nft -f /tmp/nftables-rules.nft

# Oppure: tradurre regola singola
iptables-translate -A INPUT -p tcp --dport 22 -j ACCEPT
# Output: nft add rule ip filter INPUT tcp dport 22 counter accept
```

### Esempio Completo: Firewall Server di Produzione

```bash
#!/usr/sbin/nft -f
flush ruleset

# Definizioni
define LAN_NET = 192.168.1.0/24
define VPN_NET = 10.0.0.0/24
define DNS_SERVERS = { 8.8.8.8, 8.8.4.4, 9.9.9.9 }

table inet filter {

    set trusted_mgmt {
        type ipv4_addr
        flags interval
        elements = { 10.0.1.0/24, 192.168.100.0/24 }
    }

    set blocklist {
        type ipv4_addr
        flags interval, timeout
        timeout 24h
    }

    counter cnt_blocked { }
    counter cnt_ssh { }
    counter cnt_http { }

    chain input {
        type filter hook input priority 0; policy drop;

        # Blocklist
        ip saddr @blocklist counter name cnt_blocked drop

        # Connessioni stabilite
        ct state established,related accept
        ct state invalid drop

        # Loopback
        iifname "lo" accept

        # ICMP (con rate limiting)
        ip protocol icmp limit rate 10/second accept
        ip6 nexthdr icmpv6 limit rate 10/second accept

        # SSH solo da reti trusted (con rate limiting)
        tcp dport 22 ip saddr @trusted_mgmt \
            meter ssh_meter { ip saddr limit rate 5/minute burst 10 packets } \
            counter name cnt_ssh accept

        # HTTP/HTTPS
        tcp dport { 80, 443 } counter name cnt_http accept

        # DNS
        udp dport 53 ip daddr $DNS_SERVERS accept

        # Log e drop
        log prefix "nft-drop: " level info limit rate 5/minute
        counter drop
    }

    chain forward {
        type filter hook forward priority 0; policy drop;

        ct state established,related accept
        ct state invalid drop

        # LAN → Internet
        iifname "br0" oifname "eth0" ip saddr $LAN_NET accept
        # VPN → LAN
        iifname "wg0" oifname "br0" ip saddr $VPN_NET ip daddr $LAN_NET accept
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}

table inet nat {
    chain postrouting {
        type nat hook postrouting priority 100;
        oifname "eth0" masquerade
    }
}
```

---

## WireGuard — Configurazione Avanzata e Tuning

Oltre alla configurazione base (già trattata nella sezione VPN), WireGuard offre possibilità avanzate di deployment e ottimizzazione.

### Topologie WireGuard

```
Point-to-Point (due nodi):
  Server ←→ Client

Hub-and-Spoke (stella, VPN aziendale):
  Server ←→ Client1
         ←→ Client2
         ←→ Client3

Mesh (ogni nodo conosce tutti gli altri):
  Nodo1 ←→ Nodo2
        ←→ Nodo3
  Nodo2 ←→ Nodo3
```

### Multi-Peer (Hub-and-Spoke)

```ini
# SERVER: /etc/wireguard/wg0.conf
[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = <server_private_key>
# PostUp/PostDown per routing e firewall

[Peer]
# Client 1 — laptop aziendale
PublicKey = <client1_pubkey>
AllowedIPs = 10.0.0.10/32
PresharedKey = <psk_client1>

[Peer]
# Client 2 — ufficio remoto (intera subnet)
PublicKey = <client2_pubkey>
AllowedIPs = 10.0.0.20/32, 192.168.50.0/24
PresharedKey = <psk_client2>

[Peer]
# Client 3 — mobile
PublicKey = <client3_pubkey>
AllowedIPs = 10.0.0.30/32
PresharedKey = <psk_client3>
```

### PresharedKey — Protezione Post-Quantistica

WireGuard supporta un PresharedKey (PSK) opzionale per ogni coppia di peer, aggiungendo un livello simmetrico alla crittografia. Offre protezione contro futuri attacchi con computer quantistici (il PSK viene mescolato nel key derivation).

```bash
# Generare un PSK
wg genpsk > psk_client1.key

# Aggiungere a entrambi i peer:
# [Peer]
# PresharedKey = <contenuto di psk_client1.key>
```

### Tuning Kernel per WireGuard

```bash
# Buffer UDP (WireGuard è basato su UDP)
sudo sysctl -w net.core.rmem_max=26214400
sudo sysctl -w net.core.wmem_max=26214400

# Disabilitare conntrack per il traffico WireGuard
# (incremento throughput fino al 30%)
sudo nft add rule inet raw prerouting udp dport 51820 notrack
sudo nft add rule inet raw output udp sport 51820 notrack

# Impostare MTU ottimale
# WireGuard overhead: 32 byte (Noise) + 16 byte (MAC) + 4 byte (msg type) = ~80 byte
# Con IPv4+UDP: 80 + 20 (IP) + 8 (UDP) = 108 byte
# MTU WireGuard = MTU link - 108 (per IPv4) o - 128 (per IPv6)
# Esempio: link MTU 1500 → WireGuard MTU 1420 (default, corretto per IPv4)

# Per jumbo frames
sudo ip link set wg0 mtu 8892    # Se il link fisico ha MTU 9000
```

### Monitoraggio WireGuard

```bash
# Stato connessioni
sudo wg show
sudo wg show wg0 dump              # Output parsabile

# Dettagli peer
sudo wg show wg0 latest-handshakes
sudo wg show wg0 transfer          # Byte TX/RX per peer
sudo wg show wg0 endpoints         # IP:porta remoti dei peer

# Aggiungere peer a runtime (senza riavviare)
sudo wg set wg0 peer <pubkey> allowed-ips 10.0.0.40/32 endpoint 203.0.113.5:51820

# Rimuovere peer a runtime
sudo wg set wg0 peer <pubkey> remove
```

---

## eBPF e XDP per il Networking

eBPF (extended Berkeley Packet Filter) è una tecnologia rivoluzionaria del kernel Linux che permette di eseguire programmi sandboxed nel kernel senza modificarlo o caricare moduli. XDP (eXpress Data Path) è un hook eBPF posizionato nel path più precoce possibile del network stack, prima dell'allocazione di `sk_buff`, raggiungendo performance di milioni di pacchetti al secondo per core.

### Architettura eBPF/XDP

```
Pacchetto in arrivo dalla NIC
    ↓
┌─────────────────────────────────────────────┐
│  XDP Hook (nel driver o generic)            │
│                                             │
│  Programma eBPF:                            │
│    → XDP_DROP   (scarta, non entra nello    │
│                   stack — DDoS mitigation)  │
│    → XDP_PASS   (processa normalmente)      │
│    → XDP_TX     (rimanda dalla stessa NIC)  │
│    → XDP_REDIRECT (invia a altra NIC/CPU)   │
│    → XDP_ABORTED (errore, scarta + trace)   │
└─────────────┬───────────────────────────────┘
              ↓ (se XDP_PASS)
         sk_buff allocation
              ↓
┌─────────────────────────────────┐
│  TC hook (tc-bpf)               │
│  Ingress/Egress più avanti      │
│  nello stack, con accesso a     │
│  sk_buff e funzionalità L3/L4   │
└─────────────────────────────────┘
              ↓
         Netfilter (nftables)
              ↓
         Socket applicazione
```

### Modalità XDP

| Modalità | Performance | Supporto | Descrizione |
|----------|-------------|----------|-------------|
| **Native (driver)** | Alta (>10 Mpps/core) | Driver specifici | Esecuzione nel driver NIC, prima di sk_buff |
| **Generic (SKB)** | Media | Qualsiasi NIC | Esecuzione nel generic network path, dopo sk_buff |
| **Hardware offload** | Massima | NIC specifiche (Netronome, etc.) | Esecuzione direttamente sulla NIC |

```bash
# Verificare supporto driver
ethtool -i eth0 | grep driver
# Driver con supporto XDP nativo: ixgbe, i40e, mlx5, virtio_net, veth, tun
```

### Strumenti eBPF

```bash
# Installare toolchain
sudo apt install bpftool linux-tools-common    # Debian/Ubuntu
sudo dnf install bpftool                        # Fedora/RHEL

# bpftool: ispezionare programmi eBPF caricati
sudo bpftool prog list                 # Programmi eBPF attivi
sudo bpftool prog show id <ID>        # Dettagli programma
sudo bpftool map list                  # Mappe eBPF
sudo bpftool map dump id <MAP_ID>     # Contenuto mappa
sudo bpftool net list                  # Programmi eBPF attaccati a interfacce

# Caricare un programma XDP
sudo ip link set dev eth0 xdp obj xdp_prog.o sec xdp

# Rimuovere
sudo ip link set dev eth0 xdp off

# Verificare programma XDP attivo
ip link show eth0
# Mostra: xdp/id:XX nella riga del link

# bpftrace: tracing one-liner
sudo bpftrace -e 'tracepoint:net:net_dev_xmit { @[args->name] = count(); }'
# Conta pacchetti trasmessi per interfaccia
```

### XDP vs tc-bpf

```
┌───────────────┬──────────────────┬──────────────────────┐
│               │ XDP              │ tc-bpf               │
├───────────────┼──────────────────┼──────────────────────┤
│ Hook point    │ Pre-sk_buff      │ Post-sk_buff          │
│ Performance   │ Massima          │ Alta                  │
│ Accesso L3/L4 │ Parsing manuale │ Via sk_buff helpers    │
│ Direzione     │ Solo ingress     │ Ingress + Egress      │
│ Redirect      │ Sì (XDP_REDIRECT)│ Sì (bpf_redirect)    │
│ Modifica pkt  │ Limitata         │ Completa              │
│ Caso d'uso    │ DDoS, load bal.  │ Policy, monitoring    │
└───────────────┴──────────────────┴──────────────────────┘
```

### Caso d'Uso: DDoS Mitigation con XDP

XDP è lo strumento ideale per la mitigazione DDoS: il traffico malevolo viene scartato (XDP_DROP) prima di entrare nello stack di rete, senza consumare CPU per l'allocazione sk_buff, il routing o netfilter.

```
Performance tipiche (singolo core, commodity hardware):
- XDP_DROP:      ~24 Mpps (milioni di pacchetti al secondo)
- iptables DROP: ~3 Mpps
- nftables DROP: ~5 Mpps

Rapporto: XDP è 5-8x più veloce di netfilter per il drop puro.
```

### Progetti Basati su eBPF/XDP

- **Cilium**: networking e security per Kubernetes basato su eBPF, sostituisce kube-proxy e implementa network policy senza iptables
- **Katran**: load balancer L4 di Meta (Facebook), gestisce milioni di connessioni con XDP
- **Cloudflare**: usa XDP per mitigare attacchi DDoS da centinaia di Gbps
- **bcc (BPF Compiler Collection)**: toolkit per tracing e monitoring di rete (tcplife, tcpconnect, tcpretrans, tcptop)
- **Calico eBPF**: dataplane eBPF per Kubernetes, alternativa a iptables

```bash
# Esempi con bcc
sudo /usr/share/bcc/tools/tcpconnect         # Monitora nuove connessioni TCP
sudo /usr/share/bcc/tools/tcpretrans         # Ritrasmissioni TCP
sudo /usr/share/bcc/tools/tcplife            # Durata connessioni TCP
sudo /usr/share/bcc/tools/tcptop             # Throughput per connessione
```

---

## Network Security Hardening

L'hardening della rete va oltre il firewall: comprende parametri kernel, stack TCP, configurazione dei servizi e monitoraggio. Ogni parametro ha un impatto sulla superficie di attacco.

### sysctl — Parametri di Sicurezza Rete

```bash
# /etc/sysctl.d/80-network-hardening.conf

# === Protezione Routing ===

# Disabilitare source routing (impedisce attacchi che manipolano il percorso)
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# Disabilitare ICMP redirect (prevenire MitM via redirect falsificati)
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0

# Non inviare ICMP redirect (il server non è un router domestico)
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# Secure ICMP redirect (accettare solo da gateway nella default route)
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0

# Reverse Path Filtering (scarta pacchetti con IP sorgente spoofato)
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
# 0 = disabilitato, 1 = strict (raccomandato), 2 = loose

# Loggare pacchetti marziani (IP sorgente impossibile)
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# === Protezione TCP ===

# SYN cookies (protezione contro SYN flood)
net.ipv4.tcp_syncookies = 1

# Limiti SYN backlog
net.ipv4.tcp_max_syn_backlog = 65535

# Disabilitare timestamp TCP (può rivelare uptime del server)
# ATTENZIONE: i timestamp sono utili per PAWS e RTT; disabilitare solo
# se il rischio di information disclosure supera il beneficio
# net.ipv4.tcp_timestamps = 0

# === ICMP ===

# Ignorare ping broadcast (prevenire attacchi Smurf)
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Ignorare ICMP bogus error responses
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Rate limiting risposte ICMP
net.ipv4.icmp_ratelimit = 100
net.ipv4.icmp_ratemask = 88089

# === IPv6 ===

# Disabilitare Router Advertisement (se il server non è dietro un router IPv6 trusted)
net.ipv6.conf.all.accept_ra = 0
net.ipv6.conf.default.accept_ra = 0

# Limitare il numero di indirizzi IPv6 per interfaccia
net.ipv6.conf.all.max_addresses = 2
net.ipv6.conf.default.max_addresses = 2

# === ARP ===

# Limitare risposte ARP (prevenire ARP spoofing)
net.ipv4.conf.all.arp_ignore = 1
net.ipv4.conf.default.arp_ignore = 1
net.ipv4.conf.all.arp_announce = 2
net.ipv4.conf.default.arp_announce = 2
```

```bash
# Applicare
sudo sysctl -p /etc/sysctl.d/80-network-hardening.conf

# Verificare un parametro
sysctl net.ipv4.conf.all.rp_filter
```

### Blacklist Moduli Kernel Non Necessari

Disabilitare protocolli di rete non usati riduce la superficie di attacco kernel.

```bash
# /etc/modprobe.d/blacklist-network.conf

# Protocolli raramente necessari su server moderni
install dccp /bin/false              # DCCP (Datagram Congestion Control)
install sctp /bin/false              # SCTP (Stream Control Transmission)
install rds /bin/false               # RDS (Reliable Datagram Sockets)
install tipc /bin/false              # TIPC (Transparent Inter-Process Comm)

# Protocolli tunneling non usati
install gre /bin/false               # GRE (se non serve)
install ipip /bin/false              # IP-in-IP (se non serve)

# Wireless non necessario su server
install iwlwifi /bin/false           # Intel WiFi (su server)
install bluetooth /bin/false         # Bluetooth (su server)
```

### Audit e Monitoraggio Connessioni

```bash
# Connessioni sospette con ss
ss -tuanp | awk '$5 !~ /127.0.0.1|::1/ && $2 > 0'  # Connessioni con dati in coda
ss -tnp state established | awk '{ print $5 }' | sort | uniq -c | sort -rn  # Top destinazioni

# Conteggio connessioni per stato
ss -s

# Monitorare nuove connessioni in tempo reale con conntrack
sudo conntrack -E -e NEW

# Monitorare con eBPF (bcc tools)
sudo /usr/share/bcc/tools/tcpconnect          # Nuove connessioni TCP in uscita
sudo /usr/share/bcc/tools/tcpaccept           # Nuove connessioni TCP in ingresso

# Verificare porte in ascolto non autorizzate
ss -tuln | grep -v '127.0.0.1\|::1'          # Porte esposte

# Audit trail con auditd
sudo auditctl -a exit,always -F arch=b64 -S connect -k network_connect
sudo ausearch -k network_connect              # Cercare eventi
```

### Hardening dei Servizi di Rete

```bash
# SSH — hardening essenziale (/etc/ssh/sshd_config)
# PermitRootLogin no
# PasswordAuthentication no
# PubkeyAuthentication yes
# MaxAuthTries 3
# LoginGraceTime 30
# AllowUsers deploy admin
# Protocol 2
# ClientAliveInterval 300
# ClientAliveCountMax 2

# fail2ban — blocco automatico IP dopo tentativi falliti
sudo apt install fail2ban
# /etc/fail2ban/jail.local:
# [sshd]
# enabled = true
# port = ssh
# filter = sshd
# maxretry = 3
# bantime = 3600
# findtime = 600

# Verificare ban attivi
sudo fail2ban-client status sshd
```

---

## Wi-Fi (iw, wpa_supplicant, NetworkManager)

### Gestione Wi-Fi con iw

```bash
# Scansione reti
sudo iw dev wlan0 scan | grep -E "SSID|signal|freq"

# Informazioni interfaccia wireless
iw dev wlan0 info
iw dev wlan0 link                  # Stato connessione attuale
iw phy phy0 info                   # Capacità hardware (bande, canali, etc.)

# Modalità monitor (per analisi traffico)
sudo ip link set wlan0 down
sudo iw dev wlan0 set type monitor
sudo ip link set wlan0 up
# Per tornare a managed:
sudo ip link set wlan0 down
sudo iw dev wlan0 set type managed
sudo ip link set wlan0 up

# Impostare canale
sudo iw dev wlan0 set channel 6
sudo iw dev wlan0 set freq 5180     # Frequenza esatta (5 GHz)

# Potenza di trasmissione
sudo iw dev wlan0 set txpower fixed 1500   # 15 dBm

# Statistiche
iw dev wlan0 station dump          # Statistiche per stazione associata
```

### wpa_supplicant — Configurazione Diretta

```bash
# /etc/wpa_supplicant/wpa_supplicant.conf
ctrl_interface=/var/run/wpa_supplicant
ctrl_interface_group=netdev
update_config=1
country=IT

# WPA2-Personal
network={
    ssid="MiaRete"
    psk="password_segreta"
    key_mgmt=WPA-PSK
    proto=RSN
    pairwise=CCMP
    group=CCMP
}

# WPA2-Enterprise (802.1X con PEAP)
network={
    ssid="ReteAziendale"
    key_mgmt=WPA-EAP
    eap=PEAP
    identity="utente@dominio.com"
    password="password"
    ca_cert="/etc/ssl/certs/ca-bundle.crt"
    phase2="auth=MSCHAPV2"
}

# WPA3 (SAE)
network={
    ssid="ReteWPA3"
    key_mgmt=SAE
    sae_password="password_segreta"
    ieee80211w=2
}
```

```bash
# Avviare
sudo wpa_supplicant -B -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant.conf
sudo dhclient wlan0

# Gestione interattiva
sudo wpa_cli -i wlan0
> scan
> scan_results
> add_network
> set_network 0 ssid "SSID"
> set_network 0 psk "password"
> enable_network 0
> save_config
```

### Hostapd — Access Point Software

```bash
# /etc/hostapd/hostapd.conf
interface=wlan0
driver=nl80211
ssid=MioAP
hw_mode=a            # a=5GHz, g=2.4GHz
channel=36
ieee80211n=1         # 802.11n (HT)
ieee80211ac=1        # 802.11ac (VHT)
wmm_enabled=1

# Sicurezza
wpa=2
wpa_passphrase=PasswordSicura123
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP

# Gestione client
max_num_sta=20
macaddr_acl=0        # 0=nessun ACL, 1=whitelist, 2=blacklist
```

```bash
sudo systemctl enable --now hostapd
# Combinare con dnsmasq per DHCP e un bridge per il routing
```

---

## Best Practices

1. **ip > ifconfig**: usare sempre `ip` (iproute2) al posto dei vecchi `ifconfig`, `route`, `arp`, `netstat`. I vecchi tool sono deprecati e non supportano tutte le funzionalità moderne
2. **Firewall default-deny**: policy di default DROP su INPUT e FORWARD. Permettere esplicitamente solo il traffico necessario
3. **Persistenza**: ricordare che i comandi `ip` sono temporanei. Usare netplan, NetworkManager o systemd-networkd per la configurazione persistente
4. **WireGuard > OpenVPN**: per nuove installazioni VPN, preferire WireGuard: più veloce, più semplice, nel kernel, crittografia moderna
5. **Documentare le regole firewall**: ogni regola deve avere un commento che spiega perché esiste. Le regole senza spiegazione diventano "regole fantasma" che nessuno osa toccare
6. **Segmentare la rete**: usare VLAN per separare traffico di gestione, produzione e test. Defense in depth
7. **Monitorare**: abilitare logging per le regole firewall di DROP. Analizzare periodicamente con strumenti come fail2ban

---

## Troubleshooting

**"No route to host" / "Network unreachable"** → Verificare in ordine: (1) interfaccia attiva? `ip link show`, (2) IP configurato? `ip addr show`, (3) route presente? `ip route show`, (4) default gateway? `ip route get 8.8.8.8`, (5) firewall? `iptables -L -n`. Test: `ping gateway`, poi `ping 8.8.8.8`, poi `ping google.com`.

**"DNS non risolve"** → `ping 8.8.8.8` funziona ma `ping google.com` no? È DNS. Verificare: `cat /etc/resolv.conf` (nameserver presenti?), `dig @8.8.8.8 google.com` (funziona con DNS esterno?), `resolvectl status` (systemd-resolved attivo?). Fix: aggiungere nameserver manualmente o riavviare systemd-resolved.

**"Connection refused" vs "Connection timed out"** → Refused: il servizio non è in ascolto su quella porta (`ss -tuln | grep PORT`). Timed out: il firewall sta droppando il traffico, o il server non è raggiungibile. Due problemi diversi con soluzioni diverse.

**"Firewall bloccante dopo modifica"** → Se ci si blocca fuori via SSH: accesso fisico o console, `iptables -F` (flush), ripristinare regole corrette. Prevenzione: `iptables-apply` applica regole con rollback automatico, oppure `at now + 5 minutes` con restore delle regole vecchie prima di applicare le nuove.

**"Performance di rete scarsa"** → `ethtool eth0` per verificare speed/duplex (negoziazione auto fallita?), `mtr` per identificare latenza e packet loss per hop, `iperf3` per misurare bandwidth reale, controllare MTU (`ip link show`), verificare errori interfaccia (`ip -s link show eth0`).
