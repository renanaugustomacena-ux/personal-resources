# Tutorial Linux 24 — iptables e nftables: Firewall Avanzato

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** iptables avanzato, NAT, stateful, nftables, ipset, ebtables
> **Prerequisiti:** `tutorial_linux_05_networking.md`, `tutorial_linux_11_sicurezza.md`
> **Durata stimata:** 14-18 ore

---

## Mappa concettuale

```
Firewall Linux
│
├── iptables (Netfilter)
│   ├── Tables: filter, nat, mangle, raw
│   ├── Chains: INPUT, OUTPUT, FORWARD, PREROUTING, POSTROUTING
│   ├── Targets: ACCEPT, DROP, REJECT, LOG, RETURN
│   └── Extensions: state, limit, recent, iprange
│
├── nftables (successore)
│   ├── Sintassi unificata (sostituisce iptables/ip6tables/ebtables)
│   ├── Sets e maps nativi
│   └── /etc/nftables.conf
│
├── ipset
│   ├── Hash:ip set
│   ├── Hash:net per subnet
│   └── Blocklists efficiente
│
└── NAT e routing
    ├── SNAT/MASQUERADE
    ├── DNAT (port forwarding)
    └── Policy routing
```

---

# Parte A — iptables avanzato

---

## A1. Architettura Netfilter

```
Pacchetto in entrata:
  → PREROUTING (nat) → routing decision → INPUT (filter) → processo locale
                                        ↓
                                    FORWARD (filter) → POSTROUTING (nat) → out

Pacchetto in uscita (da processo locale):
  processo → OUTPUT (filter, nat) → POSTROUTING (nat) → out
```

```bash
# Tabelle:
# filter — default, filtraggio pacchetti (INPUT/OUTPUT/FORWARD)
# nat     — traduzione indirizzi (PREROUTING/POSTROUTING/OUTPUT)
# mangle  — modifica pacchetti (tutte le chain)
# raw     — bypass conntrack (PREROUTING/OUTPUT)

# Visualizza regole con numerazione
iptables -L -n -v --line-numbers           # filter
iptables -t nat -L -n -v --line-numbers    # nat
iptables -t mangle -L -n -v               # mangle

# Statistiche
iptables -L INPUT -v   # pacchetti/bytes per regola
```

> **Analogia:** iptables è come un sistema di checkpoint in aeroporto. Il PREROUTING decide dove andare prima di sapere se è destinato a questo aeroporto o a un volo di transito. INPUT controlla i passeggeri che entrano nel paese. FORWARD controlla quelli in transito. OUTPUT controlla chi parte. NAT è come il cambio valuta — trasforma indirizzi da pubblico a privato e viceversa.

---

## A2. Firewall stateful completo

```bash
#!/usr/bin/env bash
# /etc/firewall/rules.sh — Firewall stateful robusto
set -euo pipefail

# Variabili
IFACE_WAN="${IFACE_WAN:-eth0}"
IFACE_LAN="${IFACE_LAN:-eth1}"
LAN_SUBNET="10.0.0.0/24"
SSH_PORT="${SSH_PORT:-22}"
ADMIN_IP="${ADMIN_IP:-10.0.0.5}"

# Svuota regole
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X

# Policy default
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# ===== INPUT =====

# Loopback
iptables -A INPUT -i lo -j ACCEPT

# Connessioni stabilite/correlate
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Invalidi
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# ICMP (limitato)
iptables -A INPUT -p icmp --icmp-type echo-request \
    -m limit --limit 5/sec --limit-burst 10 -j ACCEPT

# SSH da admin IP
iptables -A INPUT -p tcp --dport "$SSH_PORT" -s "$ADMIN_IP" -j ACCEPT

# SSH pubblico con rate limit
iptables -A INPUT -p tcp --dport "$SSH_PORT" \
    -m recent --set --name ssh_ratelimit --rsource
iptables -A INPUT -p tcp --dport "$SSH_PORT" \
    -m recent --update --seconds 60 --hitcount 6 --name ssh_ratelimit --rsource \
    -j DROP
iptables -A INPUT -p tcp --dport "$SSH_PORT" -j ACCEPT

# HTTP/HTTPS
iptables -A INPUT -p tcp -m multiport --dports 80,443 \
    -m conntrack --ctstate NEW -j ACCEPT

# LAN — accesso completo da rete locale
iptables -A INPUT -s "$LAN_SUBNET" -i "$IFACE_LAN" -j ACCEPT

# Log + Drop (DEVE essere ultima)
iptables -A INPUT -m limit --limit 3/min --limit-burst 10 \
    -j LOG --log-prefix "FW-IN-DROP: " --log-level 4
iptables -A INPUT -j DROP

# ===== FORWARD (se questo host fa da router) =====

# LAN → WAN (accesso internet dalla rete locale)
iptables -A FORWARD -i "$IFACE_LAN" -o "$IFACE_WAN" \
    -m conntrack --ctstate NEW,ESTABLISHED,RELATED -j ACCEPT
iptables -A FORWARD -i "$IFACE_WAN" -o "$IFACE_LAN" \
    -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# ===== NAT =====

# MASQUERADE — condivisione connessione internet (router domestico/aziendale)
iptables -t nat -A POSTROUTING -s "$LAN_SUBNET" -o "$IFACE_WAN" -j MASQUERADE

# DNAT — port forwarding (porta pubblica → server interno)
# Esempio: porta 8080 pubblica → server interno 10.0.0.10:80
iptables -t nat -A PREROUTING -i "$IFACE_WAN" \
    -p tcp --dport 8080 -j DNAT --to-destination 10.0.0.10:80

# SNAT — sorgente specifica
# iptables -t nat -A POSTROUTING -s 10.0.0.5 -o "$IFACE_WAN" \
#     -j SNAT --to-source 203.0.113.100

# Abilita IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

# Salva
iptables-save > /etc/iptables/rules.v4
```

---

## A3. ipset per blocklist

```bash
# Installa
apt install ipset

# Crea set di IP bannati
ipset create blacklist hash:ip maxelem 65536

# Aggiungi IP
ipset add blacklist 1.2.3.4
ipset add blacklist 5.6.7.8

# Aggiungi subnet
ipset create blacklist-nets hash:net
ipset add blacklist-nets 192.0.2.0/24

# Usa nel firewall (PRIMA delle altre regole)
iptables -I INPUT -m set --match-set blacklist src -j DROP
iptables -I INPUT -m set --match-set blacklist-nets src -j DROP

# Salva e ripristina ipset
ipset save > /etc/ipset.conf
ipset restore < /etc/ipset.conf

# Scarica blocklist (es. da Spamhaus)
curl -s https://www.spamhaus.org/drop/drop.txt \
    | grep -v '^;' | awk '{print $1}' \
    | while read -r subnet; do
        ipset add blacklist-nets "$subnet" 2>/dev/null || true
    done

# Lista/verifica
ipset list blacklist | head -20
ipset test blacklist 1.2.3.4   # exit 0 se presente
```

---

# Parte B — nftables

---

## B1. nftables: il successore moderno

```bash
# nftables — installazione
apt install nftables

# Struttura:
# table → family (ip, ip6, inet, bridge, arp, netdev)
#   chain → type+hook+priority
#     rule → match → verdict

# /etc/nftables.conf
cat > /etc/nftables.conf << 'EOF'
#!/usr/sbin/nft -f

# Svuota tutte le tabelle
flush ruleset

# Tabella IPv4 + IPv6 (inet = dual-stack)
table inet filter {
    # Set per IP permessi
    set admin_ips {
        type ipv4_addr
        elements = { 10.0.0.5, 192.168.1.100 }
    }

    # Set per blocklist (caricata da ipset o aggiornata dinamicamente)
    set blacklist {
        type ipv4_addr
        flags dynamic
        timeout 1h    # entry scadono automaticamente
    }

    chain input {
        type filter hook input priority 0; policy drop;

        # Loopback
        iifname lo accept

        # Stateful
        ct state established,related accept
        ct state invalid drop

        # ICMP
        ip protocol icmp icmp type echo-request limit rate 5/second accept
        ip6 nexthdr ipv6-icmp accept

        # SSH solo da admin
        tcp dport 22 ip saddr @admin_ips accept

        # HTTP/HTTPS
        tcp dport { 80, 443 } accept

        # Blacklist
        ip saddr @blacklist drop

        # Log il resto
        log prefix "nft-drop: " flags all
        # drop è implicito per policy drop
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }

    chain forward {
        type filter hook forward priority 0; policy drop;
    }
}

# Tabella NAT
table ip nat {
    chain prerouting {
        type nat hook prerouting priority -100;
        # Port forwarding: 8080 → server interno
        iifname eth0 tcp dport 8080 dnat to 10.0.0.10:80
    }

    chain postrouting {
        type nat hook postrouting priority 100;
        # Masquerade per LAN
        oifname eth0 ip saddr 10.0.0.0/24 masquerade
    }
}
EOF

# Abilita e verifica
systemctl enable --now nftables
nft -c -f /etc/nftables.conf    # check senza applicare
nft -f /etc/nftables.conf       # applica

# Comandi nft
nft list ruleset                # mostra tutto
nft list table inet filter      # tabella specifica
nft list chain inet filter input  # chain specifica

# Aggiungi regola dinamicamente
nft add rule inet filter input ip saddr 1.2.3.4 drop

# Flush una chain
nft flush chain inet filter input
```

---

# Parte C — Logging e debug

---

## C1. Log firewall

```bash
# iptables log
iptables -A INPUT -j LOG \
    --log-prefix "FW: " \
    --log-level 4 \        # warning
    --log-ip-options \
    --log-tcp-options

# nftables log
nft add rule inet filter input log prefix "nft: " flags all counter

# Analisi log
grep "FW:" /var/log/kern.log | tail -20
grep "nft:" /var/log/kern.log | awk '{print $9}' | sort | uniq -c | sort -rn

# Real-time
dmesg -T --follow | grep "FW:\|nft:"
journalctl -k -f | grep -E "FW:|nft:"

# fail2ban per iptables
# Crea jail custom per nginx
cat > /etc/fail2ban/filter.d/nginx-404.conf << 'EOF'
[Definition]
failregex = <HOST> .* "GET .* HTTP.*" 404
ignoreregex =
EOF

cat >> /etc/fail2ban/jail.local << 'EOF'
[nginx-404]
enabled = true
filter = nginx-404
logpath = /var/log/nginx/access.log
maxretry = 20
findtime = 60
bantime = 600
EOF

systemctl restart fail2ban
```

---

# Parte E — Riepilogo

## iptables vs nftables

| Aspetto | iptables | nftables |
|---|---|---|
| Sintassi | Separata per tool | Unificata |
| IPv6 | ip6tables | Nativamente (inet) |
| Bridge | ebtables | Nativamente |
| Sets | ipset (esterno) | Nativamente |
| Performance | OK | Migliore (JIT) |
| Status | Legacy (mantenuto) | Raccomandato |

## Cheatsheet nft

```bash
# Lista tutto
nft list ruleset

# Aggiungi blocco IP
nft add element inet filter blacklist { 1.2.3.4 }

# Rimuovi blocco
nft delete element inet filter blacklist { 1.2.3.4 }

# Port forwarding temporaneo
nft add rule ip nat prerouting tcp dport 8080 dnat to 10.0.0.5:80

# Reload configurazione
nft -f /etc/nftables.conf
```

## Prossimi passi

- `tutorial_linux_25_zfs.md` — ZFS filesystem con snapshot
- `tutorial_linux_27_selinux_apparmor.md` — controllo accesso obbligatorio
