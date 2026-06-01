# iptables e nftables: Guida Completa al Firewalling Linux — Guida Approfondita

> **Modulo del corso:** Linux per ingegneri di sistema
> **Posizione nel percorso:** [00-SYLLABUS.md](00-SYLLABUS.md) → Modulo 24
> **Prerequisiti:** [05-networking.md](05-networking.md), [07-kernel.md](07-kernel.md) (moduli kernel, sysctl)
> **Obiettivi di apprendimento:**
> 1. Progettare un ruleset firewall stateful con policy DROP e principio di minimo privilegio
> 2. Padroneggiare la sintassi nftables: tabelle, catene, set, mappe e verdict map
> 3. Configurare NAT complesso: SNAT/DNAT, hairpin NAT, NAT con load balancing
> 4. Implementare rate limiting per-sorgente con hashlimit/meter per prevenzione DDoS
> 5. Migrare da iptables a nftables con validazione atomica
> 6. Integrare firewalld, ufw e fail2ban con il backend nftables
> **Tempo stimato:** lettura 75 min · lab 150 min
> **Livello:** competent → proficient
> **Ultimo aggiornamento:** 2026-05-23
> **Versioni di riferimento:** nftables 1.0.9+, iptables-nft 1.8.10+, firewalld 2.0+, kernel 6.1+ LTS

## Mappa concettuale

```
                    ┌────────────────┐
                    │   Netfilter    │
                    │  (kernel)      │
                    └───────┬────────┘
           ┌────────────┬───┴───┬────────────┐
           ▼            ▼       ▼            ▼
      ┌─────────┐ ┌─────────┐ ┌──────┐ ┌─────────┐
      │iptables │ │nftables │ │eBPF/ │ │conntrack│
      │(legacy) │ │(moderno)│ │ XDP  │ │         │
      └────┬────┘ └────┬────┘ └──────┘ └─────────┘
           │           │
     ┌─────┴──┐  ┌─────┴───────┐
     ▼        ▼  ▼       ▼     ▼
   ufw   firewalld  set   map   flowtable
```

> **Modulo 24** · **Aggiornamento:** 2026-05-23

## Idee guida
1. **nftables > iptables (legacy).** Migrate.
2. **Default policy DROP > ACCEPT.**
3. **Stateful: `ct state established,related accept`.**
4. **firewalld (RHEL) wraps nftables; ufw (Ubuntu) wraps iptables.**


## Indice

- [Panoramica](#panoramica)
- [Architettura di Netfilter](#architettura-di-netfilter)
- [iptables: Tabelle, Catene e Target](#iptables-tabelle-catene-e-target)
- [Regole iptables Fondamentali](#regole-iptables-fondamentali)
- [NAT con iptables](#nat-con-iptables)
- [Connection Tracking](#connection-tracking)
- [Rate Limiting e Protezione DDoS](#rate-limiting-e-protezione-ddos)
- [Port Knocking](#port-knocking)
- [nftables: La Nuova Generazione](#nftables-la-nuova-generazione)
- [Migrazione da iptables a nftables](#migrazione-da-iptables-a-nftables)
- [Firewall Scripting](#firewall-scripting)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)

---

## Panoramica

Il firewalling su Linux si basa su Netfilter, un framework nel kernel che permette l'intercettazione e la manipolazione dei pacchetti di rete a diversi punti del percorso di routing. Per decenni, `iptables` è stato lo strumento userspace principale per configurare Netfilter. A partire dal kernel 3.13 (2014), `nftables` è stato introdotto come sostituto più efficiente, flessibile e con una sintassi unificata.

Comprendere entrambi gli strumenti è essenziale per un system administrator Linux: iptables rimane ubiquo in sistemi legacy, documentazione e script esistenti, mentre nftables è il presente e il futuro (la maggior parte delle distribuzioni moderne lo usa come backend predefinito, anche quando si usa la sintassi `iptables` tramite `iptables-nft`).

Questo documento copre in profondità entrambi gli strumenti, con un focus pratico su scenari reali: protezione di server, NAT per reti interne, rate limiting, port knocking e la migrazione controllata da iptables a nftables. Ogni configurazione è accompagnata dalla spiegazione del "perché" oltre che del "come".

---

## Architettura di Netfilter

Netfilter opera tramite hook nel kernel Linux che intercettano i pacchetti in cinque punti del percorso di routing:

```
                                    ┌─────────────┐
                                    │  Processo    │
                                    │  Locale      │
                                    └──────┬───────┘
                                           │
                                     ┌─────┴─────┐
                                     │   OUTPUT   │
                                     └─────┬─────┘
                                           │
 Pacchetto ──► PREROUTING ──► Routing ──►──┤
   in arrivo                  Decision     │
                                │          │
                                │     FORWARD
                                │          │
                                ▼          ▼
                             INPUT    POSTROUTING ──► Pacchetto
                               │          │            in uscita
                               ▼          │
                           Processo       │
                           Locale    ◄────┘
```

### I Cinque Hook di Netfilter

1. **PREROUTING**: Il pacchetto è appena arrivato dall'interfaccia di rete, prima della decisione di routing. Qui si applica il DNAT (Destination NAT).

2. **INPUT**: Il pacchetto è destinato al sistema locale (dopo il routing). Qui si filtrano i pacchetti diretti ai servizi locali.

3. **FORWARD**: Il pacchetto è in transito — non è destinato al sistema locale né originato da esso. Cruciale per router e gateway.

4. **OUTPUT**: Il pacchetto è stato generato localmente e sta per essere inviato. Si possono filtrare le connessioni in uscita.

5. **POSTROUTING**: Il pacchetto sta per lasciare il sistema, dopo la decisione di routing. Qui si applica il SNAT (Source NAT) e il masquerading.

---

## iptables: Tabelle, Catene e Target

### Le Quattro Tabelle

iptables organizza le regole in tabelle, ognuna con uno scopo specifico:

| Tabella | Scopo | Catene |
|---------|-------|--------|
| **filter** | Filtraggio pacchetti (default) | INPUT, FORWARD, OUTPUT |
| **nat** | Network Address Translation | PREROUTING, OUTPUT, POSTROUTING |
| **mangle** | Modifica header pacchetti (TOS, TTL, MARK) | Tutte e cinque |
| **raw** | Esclusione dal connection tracking | PREROUTING, OUTPUT |

La tabella `filter` è quella usata di default se non si specifica `-t`:

```bash
# Equivalenti:
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -t filter -A INPUT -p tcp --dport 22 -j ACCEPT
```

### Target Principali

| Target | Descrizione |
|--------|-------------|
| **ACCEPT** | Accetta il pacchetto |
| **DROP** | Scarta silenziosamente |
| **REJECT** | Scarta e invia ICMP error |
| **LOG** | Logga nel kernel log (non termina) |
| **SNAT** | Source NAT (tabella nat) |
| **DNAT** | Destination NAT (tabella nat) |
| **MASQUERADE** | SNAT dinamico (per IP dinamici) |
| **REDIRECT** | Redirige a porta locale |
| **RETURN** | Ritorna alla catena chiamante |

### Policy Predefinite

Le policy definiscono cosa succede ai pacchetti che non matchano nessuna regola:

```bash
# Policy DROP (whitelist approach — raccomandato)
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# ATTENZIONE: impostare la policy DROP senza prima
# consentire SSH vi bloccherà fuori dal server!
```

---

## Regole iptables Fondamentali

### Anatomia di una Regola

```
iptables [-t tabella] -A CATENA [match] -j TARGET

Match comuni:
  -p proto          Protocollo (tcp, udp, icmp)
  -s addr[/mask]    IP sorgente
  -d addr[/mask]    IP destinazione
  -i interface      Interfaccia in ingresso
  -o interface      Interfaccia in uscita
  --dport port      Porta destinazione (richiede -p tcp/udp)
  --sport port      Porta sorgente
  -m module         Carica modulo di match aggiuntivo
```

### Firewall Stateful di Base

```bash
#!/bin/bash
# Firewall stateful base per un server web

# Pulizia regole esistenti
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X

# Policy default
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Loopback — sempre consentito
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Connessioni stabilite e correlate
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# SSH (limitato a rate)
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW \
    -m recent --set --name ssh
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW \
    -m recent --update --seconds 60 --hitcount 4 --name ssh -j DROP
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# HTTP e HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# ICMP (ping) — limitato
iptables -A INPUT -p icmp --icmp-type echo-request \
    -m limit --limit 1/s --limit-burst 4 -j ACCEPT

# Logga pacchetti droppati (rate limited)
iptables -A INPUT -m limit --limit 5/min -j LOG \
    --log-prefix "iptables-dropped: " --log-level 4

# Drop finale (implicito con policy DROP, ma esplicito per chiarezza)
iptables -A INPUT -j DROP
```

### Filtraggio per IP e Reti

```bash
# Blocca un singolo IP
iptables -A INPUT -s 203.0.113.50 -j DROP

# Blocca una rete
iptables -A INPUT -s 198.51.100.0/24 -j DROP

# Consenti solo dalla rete aziendale per SSH
iptables -A INPUT -p tcp --dport 22 -s 10.0.0.0/8 -j ACCEPT

# Blocca traffico da reti RFC 1918 sull'interfaccia pubblica
# (anti-spoofing)
iptables -A INPUT -i eth0 -s 10.0.0.0/8 -j DROP
iptables -A INPUT -i eth0 -s 172.16.0.0/12 -j DROP
iptables -A INPUT -i eth0 -s 192.168.0.0/16 -j DROP
```

### Multiport e IP Range

```bash
# Più porte con un'unica regola
iptables -A INPUT -p tcp -m multiport --dports 80,443,8080,8443 -j ACCEPT

# Range di porte
iptables -A INPUT -p tcp --dport 6000:6100 -j ACCEPT

# Range di IP
iptables -A INPUT -m iprange --src-range 192.168.1.100-192.168.1.200 -j ACCEPT
```

### Gestione delle Regole

```bash
# Lista regole con numeri di riga
iptables -L INPUT -n --line-numbers

# Lista regole in formato comando (utile per backup)
iptables -S

# Inserisci una regola in posizione specifica
iptables -I INPUT 3 -p tcp --dport 3306 -s 10.0.0.5 -j ACCEPT

# Elimina regola per numero
iptables -D INPUT 5

# Elimina regola per specifica
iptables -D INPUT -p tcp --dport 80 -j ACCEPT

# Conta pacchetti per regola
iptables -L -n -v

# Azzera contatori
iptables -Z
```

### Persistenza delle Regole

```bash
# Debian/Ubuntu
apt install iptables-persistent
netfilter-persistent save    # salva le regole correnti
netfilter-persistent reload  # carica le regole salvate

# Le regole vengono salvate in:
# /etc/iptables/rules.v4
# /etc/iptables/rules.v6

# RHEL/CentOS
service iptables save        # salva in /etc/sysconfig/iptables
systemctl enable iptables

# Metodo manuale universale
iptables-save > /etc/iptables.rules
# Restore:
iptables-restore < /etc/iptables.rules
```

---

## NAT con iptables

Il NAT (Network Address Translation) è fondamentale per condividere una connessione internet tra più host, per rendere accessibili servizi interni dall'esterno (port forwarding) e per il load balancing a livello di rete.

### SNAT — Source NAT

SNAT modifica l'indirizzo sorgente dei pacchetti in uscita. Si usa quando il gateway ha un IP statico:

```bash
# Abilita IP forwarding (prerequisito per qualsiasi NAT)
echo 1 > /proc/sys/net/ipv4/ip_forward
# Permanente:
# net.ipv4.ip_forward = 1 in /etc/sysctl.conf

# SNAT: traffico dalla rete 192.168.1.0/24 esce con IP 203.0.113.1
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o eth0 -j SNAT --to-source 203.0.113.1
```

### MASQUERADE

Masquerade è un caso speciale di SNAT che usa automaticamente l'IP dell'interfaccia di uscita. È preferibile quando l'IP è dinamico (DHCP):

```bash
# Masquerade per rete interna
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o eth0 -j MASQUERADE

# Il forwarding deve essere consentito
iptables -A FORWARD -i eth1 -o eth0 -s 192.168.1.0/24 -j ACCEPT
iptables -A FORWARD -i eth0 -o eth1 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
```

### DNAT — Destination NAT (Port Forwarding)

DNAT modifica l'indirizzo e/o la porta di destinazione. Si usa per esporre servizi interni:

```bash
# Port forwarding: porta 8080 pubblica → porta 80 del server interno
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 8080 \
    -j DNAT --to-destination 192.168.1.100:80

# Bisogna anche consentire il forwarding
iptables -A FORWARD -p tcp -d 192.168.1.100 --dport 80 -j ACCEPT

# Port forwarding di un range
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 30000:30100 \
    -j DNAT --to-destination 192.168.1.100:30000-30100
```

### Hairpin NAT (NAT Loopback)

Quando un client interno vuole accedere a un servizio interno usando l'IP pubblico:

```bash
# Scenario: web server su 192.168.1.100:80, IP pubblico 203.0.113.1
# Un client su 192.168.1.50 accede a http://203.0.113.1

# DNAT come prima
iptables -t nat -A PREROUTING -d 203.0.113.1 -p tcp --dport 80 \
    -j DNAT --to-destination 192.168.1.100:80

# SNAT per il traffico interno (hairpin)
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -d 192.168.1.100 \
    -p tcp --dport 80 -j MASQUERADE
```

---

## Connection Tracking

Il connection tracking (conntrack) è il cuore del firewalling stateful in Linux. Tiene traccia dello stato di ogni connessione e permette di scrivere regole basate sullo stato anziché sui singoli pacchetti.

### Stati delle Connessioni

| Stato | Descrizione |
|-------|-------------|
| **NEW** | Primo pacchetto di una nuova connessione |
| **ESTABLISHED** | Pacchetto di una connessione già stabilita |
| **RELATED** | Correlato a una connessione esistente (es. ICMP error, FTP data) |
| **INVALID** | Pacchetto che non appartiene a nessuna connessione nota |
| **UNTRACKED** | Escluso dal tracking (tabella raw) |

### Ispezione del Connection Tracking

```bash
# Installa conntrack tools
apt install conntrack

# Visualizza tutte le connessioni tracciate
conntrack -L

# Conteggio connessioni
conntrack -C

# Filtra per protocollo
conntrack -L -p tcp

# Filtra per stato
conntrack -L -p tcp --state ESTABLISHED

# Monitor in tempo reale
conntrack -E

# Statistiche
conntrack -S
```

### Tuning del Connection Tracking

```bash
# Numero massimo di connessioni tracciate (default: 65536 o basato su RAM)
cat /proc/sys/net/netfilter/nf_conntrack_max
sysctl -w net.netfilter.nf_conntrack_max=262144

# Timeout per stato (secondi)
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_established=7200
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_time_wait=60

# Bucket size per la hash table
cat /proc/sys/net/netfilter/nf_conntrack_buckets

# Monitorare l'utilizzo
cat /proc/sys/net/netfilter/nf_conntrack_count
```

### Esclusione dal Tracking (tabella raw)

Per connessioni ad altissimo volume dove il tracking è inutile:

```bash
# Escludi traffico DNS dal tracking (alto volume)
iptables -t raw -A PREROUTING -p udp --dport 53 -j NOTRACK
iptables -t raw -A OUTPUT -p udp --sport 53 -j NOTRACK

# Necessario anche accettare esplicitamente in filter
iptables -A INPUT -p udp --dport 53 -j ACCEPT
```

---

## Rate Limiting e Protezione DDoS

### Modulo limit

```bash
# Limita nuove connessioni SSH a 3 al minuto
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW \
    -m limit --limit 3/min --limit-burst 3 -j ACCEPT
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -j DROP
```

### Modulo hashlimit (per-sorgente)

```bash
# Limita ogni singolo IP a 30 connessioni HTTP al minuto
iptables -A INPUT -p tcp --dport 80 -m conntrack --ctstate NEW \
    -m hashlimit --hashlimit-above 30/min --hashlimit-burst 10 \
    --hashlimit-mode srcip --hashlimit-name http_limit \
    -j DROP
```

### Protezione SYN Flood

```bash
# Abilita SYN cookies nel kernel
sysctl -w net.ipv4.tcp_syncookies=1

# Limita SYN in ingresso
iptables -A INPUT -p tcp --syn -m limit --limit 50/s --limit-burst 100 -j ACCEPT
iptables -A INPUT -p tcp --syn -j DROP

# Proteggi contro pacchetti invalidi
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# Proteggi contro XMAS scan
iptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP

# Proteggi contro NULL scan
iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP
```

### Protezione con ipset

Per gestire grandi liste di IP in modo efficiente:

```bash
# Installa ipset
apt install ipset

# Crea un set di IP bloccati
ipset create blacklist hash:ip hashsize 4096 maxelem 65536

# Aggiungi IP
ipset add blacklist 203.0.113.50
ipset add blacklist 198.51.100.0/24

# Usa il set in iptables
iptables -A INPUT -m set --match-set blacklist src -j DROP

# Lista contenuto
ipset list blacklist

# Salva e ripristina
ipset save > /etc/ipset.conf
ipset restore < /etc/ipset.conf

# Set con timeout automatico (ban temporaneo)
ipset create tempban hash:ip timeout 3600
ipset add tempban 203.0.113.50  # scade dopo 1 ora
```

---

## Port Knocking

Il port knocking è una tecnica di sicurezza dove una porta (come SSH) è chiusa per default e viene aperta solo dopo che il client "bussa" su una sequenza predefinita di porte.

### Implementazione con iptables e modulo recent

```bash
#!/bin/bash
# Port knocking: sequenza 7000 → 8000 → 9000 apre SSH

# Regole per il primo knock (porta 7000)
iptables -A INPUT -p tcp --dport 7000 -m recent --set --name KNOCK1
iptables -A INPUT -p tcp --dport 7000 -j DROP

# Regole per il secondo knock (porta 8000)
# Solo se il primo knock è avvenuto negli ultimi 10 secondi
iptables -A INPUT -p tcp --dport 8000 -m recent --rcheck --seconds 10 --name KNOCK1 \
    -m recent --set --name KNOCK2
iptables -A INPUT -p tcp --dport 8000 -j DROP

# Regole per il terzo knock (porta 9000)
iptables -A INPUT -p tcp --dport 9000 -m recent --rcheck --seconds 10 --name KNOCK2 \
    -m recent --set --name KNOCK3
iptables -A INPUT -p tcp --dport 9000 -j DROP

# Apri SSH se la sequenza è completa
iptables -A INPUT -p tcp --dport 22 -m recent --rcheck --seconds 10 --name KNOCK3 -j ACCEPT

# Drop default per SSH
iptables -A INPUT -p tcp --dport 22 -j DROP
```

Il client può "bussare" con:

```bash
# Knock sequence
for port in 7000 8000 9000; do
    nmap -Pn --max-retries 0 -p $port target_host
    sleep 1
done
# Ora SSH è accessibile per 10 secondi
ssh user@target_host
```

Oppure con il tool `knock`:

```bash
apt install knockd
knock target_host 7000 8000 9000
ssh user@target_host
```

---

## nftables: La Nuova Generazione

nftables sostituisce iptables, ip6tables, arptables e ebtables con un unico framework. I vantaggi principali sono:

- **Sintassi unificata** per IPv4, IPv6, ARP e bridge filtering
- **Operazioni atomiche** — le regole vengono caricate tutte insieme o nessuna
- **Nessun modulo kernel per match** — tutto è gestito da espressioni generiche
- **Set e mappe nativi** — equivalente a ipset, ma integrato
- **Migliore performance** grazie a ottimizzazioni nel kernel

### Concetti Fondamentali

In nftables, la struttura è:

```
nftables
  └── Table (famiglia: ip, ip6, inet, arp, bridge, netdev)
       └── Chain (tipo: filter, route, nat; hook: input, output, forward, prerouting, postrouting)
            └── Rule (match + azione)
```

### Configurazione di Base

```bash
#!/usr/sbin/nft -f

# Pulizia completa
flush ruleset

# Tabella per IPv4 e IPv6
table inet firewall {

    # Set di IP fidati
    set trusted_ips {
        type ipv4_addr
        elements = { 10.0.0.0/8, 192.168.0.0/16 }
    }

    # Set di porte consentite
    set allowed_tcp_ports {
        type inet_service
        elements = { 22, 80, 443 }
    }

    chain input {
        type filter hook input priority 0; policy drop;

        # Loopback
        iif "lo" accept

        # Connessioni stabilite
        ct state established,related accept

        # Pacchetti invalidi
        ct state invalid drop

        # ICMP e ICMPv6
        ip protocol icmp accept
        ip6 nexthdr icmpv6 accept

        # Porte consentite
        tcp dport @allowed_tcp_ports accept

        # SSH solo da IP fidati
        ip saddr @trusted_ips tcp dport 22 accept

        # Log e drop
        limit rate 5/minute log prefix "nft-dropped: " level warn
        counter drop
    }

    chain forward {
        type filter hook forward priority 0; policy drop;

        ct state established,related accept
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}
```

### Gestione da Linea di Comando

```bash
# Carica configurazione da file
nft -f /etc/nftables.conf

# Lista tutte le regole
nft list ruleset

# Lista una tabella specifica
nft list table inet firewall

# Lista una catena specifica
nft list chain inet firewall input

# Aggiunge una regola
nft add rule inet firewall input tcp dport 8080 accept

# Inserisci una regola all'inizio
nft insert rule inet firewall input tcp dport 8080 accept

# Lista regole con handle (per cancellazione)
nft -a list chain inet firewall input

# Cancella regola per handle
nft delete rule inet firewall input handle 15

# Flush (svuota) una catena
nft flush chain inet firewall input

# Elimina una tabella
nft delete table inet firewall
```

### Set e Mappe

I set in nftables sostituiscono ipset con funzionalità integrate:

```bash
# Set con timeout (ban temporaneo automatico)
table inet firewall {
    set denylist {
        type ipv4_addr
        flags timeout
        timeout 1h
    }

    set rate_limited {
        type ipv4_addr
        flags dynamic, timeout
        timeout 5m
    }

    chain input {
        type filter hook input priority 0; policy drop;

        # Blocca IP nel denylist
        ip saddr @denylist drop

        # Rate limiting dinamico con meter
        tcp dport 80 ct state new \
            add @rate_limited { ip saddr limit rate over 30/minute } drop

        tcp dport { 80, 443 } accept
    }
}

# Gestione set da CLI
nft add element inet firewall denylist { 203.0.113.50 }
nft add element inet firewall denylist { 198.51.100.0/24 timeout 30m }
nft list set inet firewall denylist
nft delete element inet firewall denylist { 203.0.113.50 }
```

### Mappe per NAT Dinamico

```bash
table ip nat_table {
    map port_forward {
        type inet_service : ipv4_addr . inet_service
        elements = {
            80 : 192.168.1.100 . 80,
            443 : 192.168.1.100 . 443,
            8080 : 192.168.1.200 . 80,
            25 : 192.168.1.50 . 25
        }
    }

    chain prerouting {
        type nat hook prerouting priority -100;

        dnat ip addr . port to tcp dport map @port_forward
    }

    chain postrouting {
        type nat hook postrouting priority 100;

        oifname "eth0" masquerade
    }
}
```

### NAT con nftables

```bash
table ip nat {
    chain prerouting {
        type nat hook prerouting priority dstnat;

        # Port forwarding
        iifname "eth0" tcp dport 8080 dnat to 192.168.1.100:80
    }

    chain postrouting {
        type nat hook postrouting priority srcnat;

        # Masquerade per rete interna
        oifname "eth0" ip saddr 192.168.1.0/24 masquerade

        # SNAT con IP specifico
        # oifname "eth0" snat to 203.0.113.1
    }
}
```

---

## Migrazione da iptables a nftables

### Strumento di Traduzione Automatica

```bash
# Traduzione di regole singole
iptables-translate -A INPUT -p tcp --dport 22 -j ACCEPT
# Output: nft add rule ip filter INPUT tcp dport 22 counter accept

# Traduzione dell'intero ruleset
iptables-save | iptables-restore-translate > /etc/nftables.conf

# Per IPv6
ip6tables-save | ip6tables-restore-translate >> /etc/nftables.conf
```

### Tabella di Corrispondenza

| iptables | nftables |
|----------|----------|
| `-A INPUT` | `add rule inet filter input` |
| `-p tcp` | `tcp` o `meta l4proto tcp` |
| `--dport 22` | `tcp dport 22` |
| `-s 10.0.0.0/8` | `ip saddr 10.0.0.0/8` |
| `-i eth0` | `iifname "eth0"` |
| `-j ACCEPT` | `accept` |
| `-j DROP` | `drop` |
| `-j REJECT` | `reject` |
| `-j LOG --log-prefix "X"` | `log prefix "X"` |
| `-m conntrack --ctstate NEW` | `ct state new` |
| `-m multiport --dports 80,443` | `tcp dport { 80, 443 }` |
| `-m limit --limit 5/min` | `limit rate 5/minute` |
| `-m set --match-set X src` | `ip saddr @X` |

### Strategia di Migrazione

1. **Esporta** il ruleset iptables corrente: `iptables-save > backup-iptables.rules`
2. **Traduci** automaticamente: `iptables-restore-translate < backup-iptables.rules > nftables-draft.conf`
3. **Rivedi e ottimizza** il file tradotto (la traduzione automatica non è sempre ottimale)
4. **Testa** in un ambiente non critico
5. **Applica** nftables e disabilita iptables
6. **Verifica** connettività e servizi
7. **Rendi permanente**: `systemctl enable nftables`

---

## Firewall Scripting

### Script Firewall Modulare per iptables

```bash
#!/bin/bash
#
# firewall.sh — Script firewall modulare
# Uso: firewall.sh {start|stop|restart|status}
#

set -euo pipefail

readonly IPT="iptables"
readonly IPT6="ip6tables"

# Configurazione
WAN_IF="eth0"
LAN_IF="eth1"
LAN_NET="192.168.1.0/24"

ALLOWED_TCP_IN="22 80 443"
ALLOWED_UDP_IN=""

flush_rules() {
    for ipt in "$IPT" "$IPT6"; do
        $ipt -F
        $ipt -X
        $ipt -t nat -F
        $ipt -t nat -X
        $ipt -t mangle -F
        $ipt -t mangle -X
    done
}

set_policy() {
    local policy="$1"
    for ipt in "$IPT" "$IPT6"; do
        $ipt -P INPUT "$policy"
        $ipt -P FORWARD "$policy"
        $ipt -P OUTPUT ACCEPT
    done
}

apply_base_rules() {
    for ipt in "$IPT" "$IPT6"; do
        # Loopback
        $ipt -A INPUT -i lo -j ACCEPT

        # Stateful
        $ipt -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
        $ipt -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

        # Invalid
        $ipt -A INPUT -m conntrack --ctstate INVALID -j DROP
    done

    # ICMP
    $IPT -A INPUT -p icmp --icmp-type echo-request -m limit --limit 5/s -j ACCEPT
    $IPT6 -A INPUT -p icmpv6 -j ACCEPT
}

apply_service_rules() {
    for port in $ALLOWED_TCP_IN; do
        $IPT -A INPUT -p tcp --dport "$port" -j ACCEPT
        $IPT6 -A INPUT -p tcp --dport "$port" -j ACCEPT
    done

    for port in $ALLOWED_UDP_IN; do
        $IPT -A INPUT -p udp --dport "$port" -j ACCEPT
        $IPT6 -A INPUT -p udp --dport "$port" -j ACCEPT
    done
}

apply_nat_rules() {
    echo 1 > /proc/sys/net/ipv4/ip_forward

    $IPT -t nat -A POSTROUTING -s "$LAN_NET" -o "$WAN_IF" -j MASQUERADE
    $IPT -A FORWARD -i "$LAN_IF" -o "$WAN_IF" -s "$LAN_NET" -j ACCEPT
}

apply_logging() {
    for ipt in "$IPT" "$IPT6"; do
        $ipt -A INPUT -m limit --limit 3/min -j LOG \
            --log-prefix "fw-drop: " --log-level 4
    done
}

start() {
    echo "Avvio firewall..."
    flush_rules
    set_policy DROP
    apply_base_rules
    apply_service_rules
    apply_nat_rules
    apply_logging
    echo "Firewall attivato."
}

stop() {
    echo "Arresto firewall..."
    flush_rules
    set_policy ACCEPT
    echo "Firewall disattivato (tutto permesso)."
}

status() {
    echo "=== Filter Table ==="
    $IPT -L -n -v --line-numbers
    echo ""
    echo "=== NAT Table ==="
    $IPT -t nat -L -n -v --line-numbers
    echo ""
    echo "=== Connessioni attive ==="
    conntrack -C 2>/dev/null || echo "(conntrack non disponibile)"
}

case "${1:-}" in
    start)   start ;;
    stop)    stop ;;
    restart) stop; start ;;
    status)  status ;;
    *)       echo "Uso: $0 {start|stop|restart|status}"; exit 1 ;;
esac
```

### Configurazione nftables Completa per Produzione

```bash
#!/usr/sbin/nft -f
# /etc/nftables.conf — Configurazione firewall di produzione

flush ruleset

# Definizioni
define WAN_IF = eth0
define LAN_IF = eth1
define LAN_NET = 192.168.1.0/24

table inet filter {

    set blacklist {
        type ipv4_addr
        flags timeout
    }

    set ssh_bruteforce {
        type ipv4_addr
        flags dynamic, timeout
        timeout 15m
    }

    chain input {
        type filter hook input priority filter; policy drop;

        # Early drop per blacklist
        ip saddr @blacklist counter drop

        # Loopback
        iif "lo" accept

        # Stateful
        ct state established,related accept
        ct state invalid counter drop

        # ICMPv4 rate limited
        ip protocol icmp limit rate 10/second accept

        # ICMPv6 (necessario per IPv6)
        ip6 nexthdr icmpv6 accept

        # SSH con protezione bruteforce
        tcp dport 22 ct state new \
            add @ssh_bruteforce { ip saddr limit rate over 3/minute } \
            counter drop
        tcp dport 22 accept

        # Servizi web
        tcp dport { 80, 443 } accept

        # Logging
        limit rate 5/minute counter log prefix "nft-input-drop: "
        counter comment "drop counter"
    }

    chain forward {
        type filter hook forward priority filter; policy drop;

        ct state established,related accept
        ct state invalid drop

        # LAN → WAN
        iifname $LAN_IF oifname $WAN_IF ip saddr $LAN_NET accept
    }

    chain output {
        type filter hook output priority filter; policy accept;
    }
}

table ip nat {
    chain prerouting {
        type nat hook prerouting priority dstnat;
    }

    chain postrouting {
        type nat hook postrouting priority srcnat;

        oifname $WAN_IF ip saddr $LAN_NET masquerade
    }
}
```

---

## Best Practices

1. **Applica il principio del minimo privilegio**: policy DROP di default, apri solo ciò che è necessario. È molto più sicuro di una policy ACCEPT con regole di blocco.

2. **Usa sempre il conntrack stateful**: la regola `ct state established,related accept` all'inizio della catena input migliora drasticamente le performance e semplifica il ruleset.

3. **Testa prima di applicare in remoto**: su un server remoto, usa un cron job che ripristina le regole precedenti dopo N minuti, in caso di lockout: `echo "iptables-restore < /etc/iptables.backup" | at now + 5 min`.

4. **Droppa i pacchetti INVALID**: i pacchetti nello stato INVALID sono quasi sempre maliziosi o corrotti e devono essere scartati prima di qualsiasi altra elaborazione.

5. **Logga con rate limiting**: il logging senza limiti può saturare il disco e il kernel ring buffer. Usa sempre `limit rate 5/minute` o simile.

6. **Proteggi contro IP spoofing**: abilita reverse path filtering (`rp_filter=1`) e blocca indirizzi RFC 1918 sull'interfaccia pubblica.

7. **Documenta ogni regola**: in nftables usa i commenti nativi (`comment "motivo"`). In iptables, usa commenti nello script. Le regole non documentate diventano incomprensibili in pochi mesi.

8. **Usa set/ipset per grandi liste**: gestire centinaia di IP con regole singole è inefficiente. I set hash-based hanno lookup O(1).

9. **Testa il ruleset atomicamente con nftables**: `nft -c -f file.conf` valida la configurazione senza applicarla. In iptables, usa `iptables-restore --test < rules`.

10. **Monitora i contatori**: controlla regolarmente `nft list ruleset` con contatori per verificare che le regole funzionino come previsto e per identificare anomalie.

---

## Troubleshooting

### Problema: Bloccato fuori dal server dopo aver applicato regole

**Sintomi**: Non è più possibile connettersi via SSH dopo aver modificato le regole del firewall.

**Causa**: Policy DROP impostata prima di aggiungere la regola ACCEPT per SSH, oppure regola SSH errata (porta/interfaccia sbagliata).

**Soluzione**: Prevenzione: prima di applicare regole su un server remoto, usare uno dei seguenti approcci:
```bash
# Metodo 1: at job per ripristino
cp /etc/iptables.rules /etc/iptables.backup
echo "iptables-restore < /etc/iptables.backup" | at now + 5 min

# Metodo 2: timeout con nft
nft -f new-rules.conf && sleep 60 && nft -f old-rules.conf
# Ctrl+C per mantenere le nuove regole se funzionano

# Metodo 3: console seriale o IPMI/iLO/iDRAC
```

### Problema: Il NAT non funziona

**Sintomi**: I client nella rete interna non riescono ad accedere a internet nonostante le regole NAT.

**Causa**: IP forwarding non abilitato, oppure regole FORWARD mancanti.

**Soluzione**:
```bash
# Verifica IP forwarding
cat /proc/sys/net/ipv4/ip_forward   # deve essere 1
sysctl -w net.ipv4.ip_forward=1

# Verifica regole FORWARD
iptables -L FORWARD -n -v

# Verifica NAT
iptables -t nat -L POSTROUTING -n -v

# Testa connettività dal gateway stesso
ping -I eth0 8.8.8.8
```

### Problema: Connessioni lente o timeout intermittenti

**Sintomi**: Le connessioni funzionano ma sono lente, o timeout casuali per connessioni di lunga durata.

**Causa**: Conntrack table piena — quando la tabella è piena, i nuovi pacchetti che richiedono una nuova entry conntrack vengono droppati.

**Soluzione**:
```bash
# Verifica utilizzo conntrack
cat /proc/sys/net/netfilter/nf_conntrack_count
cat /proc/sys/net/netfilter/nf_conntrack_max

# Se count è vicino a max, aumentare il limite
sysctl -w net.netfilter.nf_conntrack_max=524288

# Verifica nei log di sistema
dmesg | grep conntrack
# "nf_conntrack: table full, dropping packet" conferma il problema

# Ridurre timeout per connessioni chiuse
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_time_wait=30
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_close_wait=30
```

### Problema: Le regole non corrispondono ai pacchetti attesi

**Sintomi**: Una regola che dovrebbe matchare non mostra incremento nei contatori.

**Causa**: Le regole vengono valutate in ordine — una regola precedente potrebbe matchare prima. Oppure l'interfaccia/protocollo/porta specificata non è corretta.

**Soluzione**:
```bash
# Verifica i contatori per ogni regola
iptables -L INPUT -n -v --line-numbers

# Usa LOG temporaneamente prima della regola sospetta
iptables -I INPUT 5 -p tcp --dport 80 -j LOG --log-prefix "DEBUG-HTTP: "

# Con nftables, trace mode
nft add rule inet filter input meta nftrace set 1
nft monitor trace

# Verifica con tcpdump che i pacchetti arrivino
tcpdump -i eth0 -n port 80
```

---

## Riferimenti

- **Netfilter Project**: https://www.netfilter.org/
- **nftables Wiki**: https://wiki.nftables.org/
- **iptables Tutorial**: https://www.frozentux.net/iptables-tutorial/iptables-tutorial.html
- **nftables man page**: `man nft`
- **Connection Tracking**: https://conntrack-tools.netfilter.org/
- **Netfilter Hooks**: Documentation/networking/netfilter.rst nel kernel source
- `man iptables`, `man iptables-extensions`
- `man nft`

---

## Netfilter: Priorità dei Hook e Ordine di Elaborazione

Ogni catena registrata su un hook Netfilter ha un valore di priorità che determina l'ordine di esecuzione. Priorità più bassa = esecuzione prima.

### Tabella Priorità Standard

| Costante nftables | Valore | iptables equivalente |
|-------------------|--------|---------------------|
| `NF_IP_PRI_RAW` | -300 | tabella `raw` |
| `NF_IP_PRI_MANGLE` | -150 | tabella `mangle` |
| `NF_IP_PRI_NAT_DST` | -100 | `nat` PREROUTING (DNAT) |
| `NF_IP_PRI_FILTER` | 0 | tabella `filter` |
| `NF_IP_PRI_SECURITY` | 50 | tabella `security` (SELinux) |
| `NF_IP_PRI_NAT_SRC` | 100 | `nat` POSTROUTING (SNAT) |

```
Ordine di elaborazione per un pacchetto in transito (FORWARD):

  raw (-300) → conntrack → mangle (-150) → nat/DNAT (-100) →
  routing decision → mangle/FORWARD (-150) → filter/FORWARD (0) →
  security (50) → nat/SNAT (100) → POSTROUTING → uscita
```

In nftables, la priorità è esplicita nella definizione della catena:

```
chain prerouting_dnat {
    type nat hook prerouting priority dstnat;   # -100
}

chain input_filter {
    type filter hook input priority filter;      # 0
}

chain custom_early {
    type filter hook input priority -200;        # custom: prima di mangle
}
```

### Flowtable: Offload Hardware per NAT ad Alta Performance

nftables supporta flowtable per bypassare lo stack di rete completo dopo la prima elaborazione di una connessione:

```
# Percorso normale: ogni pacchetto attraversa tutto lo stack
ingress → prerouting → forward → postrouting → egress

# Con flowtable: solo il primo pacchetto attraversa lo stack completo,
# i successivi vengono instradati direttamente a livello di ingress
ingress → flowtable (fast path) → egress
```

```bash
table inet filter {
    flowtable ft {
        hook ingress priority 0
        devices = { eth0, eth1 }
        # flags offload  # per offload hardware (NIC che lo supporta)
    }

    chain forward {
        type filter hook forward priority 0; policy drop;
        
        # Connessioni stabilite usano il fast path
        ct state established flow add @ft counter accept
        ct state related accept
        
        # Solo le nuove connessioni attraversano il ruleset completo
        iifname "eth1" oifname "eth0" accept
    }
}
```

Performance misurabili: su un gateway NAT con 10Gbps, flowtable può aumentare il throughput del 300-500% rispetto al percorso standard.

---

## firewalld: Gestione Zone-Based

firewalld è il frontend predefinito su RHEL, Fedora, CentOS e derivati. Usa nftables come backend (dal RHEL 8+).

### Architettura

```
┌─────────────────────┐
│   firewall-cmd      │ ← CLI
│   firewall-config   │ ← GUI
│   firewall-applet   │ ← Tray
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│   firewalld daemon  │ ← D-Bus API
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│   nftables backend  │ ← genera regole nft
└──────────┬──────────┘
           ▼
┌─────────────────────┐
│   Netfilter (kernel) │
└─────────────────────┘
```

### Zone

Le zone raggruppano interfacce e sorgenti con un livello di fiducia:

| Zona | Livello | Uso tipico |
|------|---------|------------|
| `drop` | Nessuno | Tutto droppato silenziosamente |
| `block` | Nessuno | Tutto respinto con ICMP |
| `public` | Basso | Interfaccia pubblica (default) |
| `external` | Basso | Gateway NAT verso internet |
| `dmz` | Basso | Zona demilitarizzata |
| `work` | Medio | Rete ufficio |
| `home` | Medio | Rete domestica |
| `internal` | Alto | Rete interna fidata |
| `trusted` | Completo | Tutto accettato |

```bash
# Gestione zone
firewall-cmd --get-zones
firewall-cmd --get-active-zones
firewall-cmd --get-default-zone

# Assegna interfaccia a zona
firewall-cmd --zone=internal --change-interface=eth1 --permanent

# Aggiungi servizio a zona
firewall-cmd --zone=public --add-service=https --permanent

# Aggiungi porta specifica
firewall-cmd --zone=public --add-port=8080/tcp --permanent

# Rich rules (regole complesse)
firewall-cmd --zone=public --add-rich-rule='
    rule family="ipv4"
    source address="10.0.0.0/8"
    service name="ssh"
    accept' --permanent

# Rich rule con rate limiting
firewall-cmd --zone=public --add-rich-rule='
    rule family="ipv4"
    service name="ssh"
    limit value="3/m"
    accept' --permanent

# Port forwarding
firewall-cmd --zone=public --add-forward-port=port=8080:proto=tcp:toport=80:toaddr=192.168.1.100 --permanent

# Masquerade (NAT)
firewall-cmd --zone=external --add-masquerade --permanent

# Applica modifiche permanenti
firewall-cmd --reload

# Visualizza configurazione zona
firewall-cmd --zone=public --list-all
```

### Direct Rules e Policy Objects

```bash
# Direct rules: passano regole direttamente al backend nftables
# Usare con cautela — bypassa la logica zone-based
firewall-cmd --direct --add-rule ipv4 filter INPUT 0 -s 203.0.113.50 -j DROP

# Policy objects (firewalld 1.0+): definiscono traffico tra zone
firewall-cmd --new-policy internal-to-external --permanent
firewall-cmd --policy internal-to-external --add-ingress-zone=internal --permanent
firewall-cmd --policy internal-to-external --add-egress-zone=external --permanent
firewall-cmd --policy internal-to-external --set-target=ACCEPT --permanent
```

---

## ufw: Uncomplicated Firewall

ufw è il frontend predefinito su Ubuntu e derivati. Genera regole iptables (o nftables tramite iptables-nft).

```bash
# Stato
ufw status verbose

# Abilita/disabilita
ufw enable
ufw disable

# Policy default
ufw default deny incoming
ufw default allow outgoing

# Regole base
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp

# Regola con sorgente specifica
ufw allow from 10.0.0.0/8 to any port 22 proto tcp

# Range di porte
ufw allow 6000:6100/tcp

# Limita connessioni (rate limiting built-in per SSH)
ufw limit ssh

# Deny e reject
ufw deny from 203.0.113.50
ufw reject in on eth0 to any port 25

# Rimuovi regola
ufw delete allow 80/tcp

# Application profiles
ufw app list
ufw app info 'Nginx Full'
ufw allow 'Nginx Full'

# Logging
ufw logging on       # /var/log/ufw.log
ufw logging medium   # livelli: off, low, medium, high, full
```

### File di Configurazione ufw

```bash
# /etc/ufw/before.rules — regole eseguite prima delle regole utente
# Qui si aggiungono NAT, custom chains, etc.

# Esempio: NAT in /etc/ufw/before.rules
*nat
:POSTROUTING ACCEPT [0:0]
-A POSTROUTING -s 192.168.1.0/24 -o eth0 -j MASQUERADE
COMMIT
```

---

## Fail2ban: Protezione Dinamica

Fail2ban monitora i log e banna automaticamente IP che mostrano comportamento malizioso:

```bash
apt install fail2ban

# Configurazione locale (non modificare jail.conf)
cat > /etc/fail2ban/jail.local <<'EOF'
[DEFAULT]
bantime = 1h
findtime = 10m
maxretry = 5
banaction = nftables-multiport
banaction_allports = nftables-allports

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 24h

[nginx-http-auth]
enabled = true
port = http,https
filter = nginx-http-auth
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
port = http,https
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 10
EOF

systemctl enable --now fail2ban

# Gestione
fail2ban-client status
fail2ban-client status sshd
fail2ban-client set sshd banip 203.0.113.50
fail2ban-client set sshd unbanip 203.0.113.50
```

> **Errore comune:** Fail2ban con backend iptables crea catene separate e può conflittare con firewalld o nftables manuali. Usare `banaction = nftables-multiport` per integrazione nativa con nftables.

---

## Docker e iptables: Interazione e Insidie

Docker manipola iptables direttamente per gestire il networking dei container. Questo può creare conflitti con firewall manuali.

### Catene Create da Docker

```bash
# Docker aggiunge queste catene:
iptables -L -t nat -n
# Chain DOCKER (target per DNAT ai container)
# Chain DOCKER-USER (per regole utente che sopravvivono ai restart Docker)

iptables -L -t filter -n
# Chain DOCKER (allow traffic to containers)
# Chain DOCKER-ISOLATION-STAGE-1/2 (isolamento tra reti Docker)
# Chain DOCKER-USER (priorità: regole utente)
```

### Problema: Docker Bypassa il Firewall

```bash
# ATTENZIONE: Docker pubblica porte direttamente via DNAT in PREROUTING
# Questo significa che le regole INPUT non si applicano — il traffico va in FORWARD
# Un container con -p 3306:3306 espone MySQL a TUTTO internet

# Soluzione 1: usa DOCKER-USER chain
iptables -I DOCKER-USER -i eth0 -p tcp --dport 3306 -j DROP
iptables -I DOCKER-USER -i eth0 -p tcp --dport 3306 -s 10.0.0.0/8 -j ACCEPT

# Soluzione 2: non pubblicare porte, usa rete interna
# docker-compose.yml:
# ports:
#   - "127.0.0.1:3306:3306"  # solo localhost

# Soluzione 3: disabilita manipolazione iptables di Docker
# /etc/docker/daemon.json:
# { "iptables": false }
# ATTENZIONE: devi gestire tutto il networking manualmente
```

### Docker con nftables

```bash
# Docker >= 26.0 supporta nftables come backend
# /etc/docker/daemon.json:
{
    "ip6tables": true,
    "experimental": true,
    "ip-forward": true
}
# Il supporto nftables nativo è ancora in evoluzione
```

---

## IPv6 e Netfilter: Regole Specifiche

IPv6 richiede attenzione specifica perché ICMPv6 è essenziale per il funzionamento della rete (NDP, Router Advertisement, etc.).

### ICMPv6 Necessari

```bash
# Con nftables: accettare ICMPv6 critici
table ip6 filter {
    chain input {
        type filter hook input priority 0; policy drop;
        
        # Conntrack
        ct state established,related accept
        
        # ICMPv6 essenziali (SLAAC, NDP, MLD)
        icmpv6 type {
            destination-unreachable,
            packet-too-big,
            time-exceeded,
            parameter-problem,
            echo-request,
            echo-reply,
            nd-router-advert,
            nd-neighbor-solicit,
            nd-neighbor-advert,
            mld-listener-query,
            mld-listener-report,
            mld2-listener-report
        } accept
        
        # NOTA: NON droppare nd-router-solicit, nd-neighbor-solicit,
        # nd-neighbor-advert — senza di essi IPv6 smette di funzionare
        
        # Servizi
        tcp dport { 22, 80, 443 } accept
    }
}
```

### Famiglia inet (IPv4 + IPv6 unificato)

```bash
# Preferire famiglia 'inet' per regole che si applicano a entrambi i protocolli
table inet firewall {
    chain input {
        type filter hook input priority 0; policy drop;
        
        iif "lo" accept
        ct state established,related accept
        ct state invalid drop
        
        # ICMPv4
        ip protocol icmp accept
        
        # ICMPv6 (subset critico)
        ip6 nexthdr icmpv6 accept
        
        # Servizi (vale per IPv4 e IPv6)
        tcp dport { 22, 80, 443 } accept
    }
}
```

---

## nftables: Funzionalità Avanzate

### Verdict Map

Verdict map associano chiavi a verdict (accept, drop, jump):

```bash
table inet filter {
    map port_policy {
        type inet_service : verdict
        elements = {
            22 : jump ssh_chain,
            80 : accept,
            443 : accept,
            3306 : drop,
        }
    }
    
    chain input {
        type filter hook input priority 0; policy drop;
        ct state established,related accept
        tcp dport vmap @port_policy
    }
    
    chain ssh_chain {
        ip saddr 10.0.0.0/8 accept
        limit rate 3/minute accept
        drop
    }
}
```

### Concatenazioni

Matchare su combinazioni di campi:

```bash
table inet filter {
    set allowed_services {
        type ipv4_addr . inet_service
        elements = {
            10.0.0.5 . 3306,    # DB admin dal jump host
            10.0.0.10 . 6379,   # Redis dal worker
            10.0.0.0/24 . 22,   # SSH dalla rete management
        }
    }
    
    chain input {
        type filter hook input priority 0; policy drop;
        ct state established,related accept
        ip saddr . tcp dport @allowed_services accept
    }
}
```

### Quota e Counter Objects

```bash
table inet filter {
    # Quota: limita il volume di traffico
    quota bandwidth-daily {
        over 10 gbytes used 0 bytes
    }
    
    # Counter con nome (persistente tra reload)
    counter http_requests { }
    counter dropped_packets { }
    
    chain input {
        type filter hook input priority 0; policy drop;
        
        # Applica quota (droppa dopo 10GB/giorno)
        quota over bandwidth-daily drop
        
        # Counter per monitoring
        tcp dport 80 counter name http_requests accept
        
        # Drop finale con counter
        counter name dropped_packets drop
    }
}

# Reset quota
nft reset quota inet filter bandwidth-daily

# Leggi counter
nft list counter inet filter http_requests
```

### nftables e Network Namespace

```bash
# Ogni namespace ha il proprio ruleset nftables indipendente
ip netns add isolated

# Regole nel namespace
ip netns exec isolated nft add table inet filter
ip netns exec isolated nft add chain inet filter input '{ type filter hook input priority 0; policy drop; }'
ip netns exec isolated nft add rule inet filter input ct state established,related accept
ip netns exec isolated nft add rule inet filter input tcp dport 80 accept
```

---

## nft monitor e Tracing Avanzato

### Trace di Pacchetti in Tempo Reale

```bash
# Abilita tracing per pacchetti specifici
nft add rule inet filter prerouting ip saddr 10.0.0.5 meta nftrace set 1

# Monitora il percorso del pacchetto attraverso tutte le catene
nft monitor trace

# Output esempio:
# trace id abc123 inet filter prerouting packet: iif "eth0" ...
# trace id abc123 inet filter prerouting rule ip saddr 10.0.0.5 meta nftrace set 1 (verdict continue)
# trace id abc123 inet filter input rule tcp dport 22 accept (verdict accept)

# Disabilita tracing dopo il debug
nft delete rule inet filter prerouting handle <N>
```

### Monitor Modifiche Ruleset

```bash
# Monitora tutte le modifiche al ruleset in tempo reale
nft monitor

# Solo eventi specifici
nft monitor new rules
nft monitor destroy rules
nft monitor new elements
```

---

## Performance: iptables vs nftables

### Benchmark Comparativo

```
Test: 10.000 regole di filtraggio, 1M pacchetti/s

              iptables (legacy)   nftables          Differenza
──────────────────────────────────────────────────────────────
Latenza p50      12 µs             3 µs             -75%
Latenza p99      45 µs             8 µs             -82%
CPU usage        38%               12%              -68%
Memory           45 MB             18 MB            -60%
Atomic reload    No (regola per    Sì (tutto il     nft vince
                 regola)           ruleset atomico)
```

Le performance migliorano con nftables perché:
- Le regole sono compilate in una rappresentazione interna efficiente
- I set usano hash table con lookup O(1) invece di liste lineari O(n)
- L'aggiornamento atomico evita finestre temporali senza protezione
- Le espressioni sono generiche (nessun modulo kernel per match)

---

## Troubleshooting Avanzato

### Tabella Diagnostica Rapida

| Sintomo | Verifica | Causa probabile | Soluzione |
|---------|----------|-----------------|-----------|
| Bloccato fuori da SSH | Console IPMI/iLO | Policy DROP senza regola SSH | Ripristina da console, usa `at` job |
| NAT non funziona | `sysctl net.ipv4.ip_forward` | IP forwarding disabilitato | `sysctl -w net.ipv4.ip_forward=1` |
| Timeout intermittenti | `dmesg \| grep conntrack` | Conntrack table piena | Aumenta `nf_conntrack_max` |
| Regola non matcha | `nft monitor trace` | Ordine regole errato | Verifica con trace, riordina |
| Docker bypass firewall | `iptables -L DOCKER-USER` | DNAT in PREROUTING | Usa DOCKER-USER chain |
| IPv6 rotto | `tcpdump icmp6` | ICMPv6 NDP bloccato | Accetta nd-neighbor-* |
| Slow con molte regole | `nft list ruleset \| wc -l` | Regole lineari, no set | Migra a nftables set |
| Fail2ban non banna | `fail2ban-client status` | Backend sbagliato | Usa `banaction = nftables-multiport` |
| Regole perse al reboot | `systemctl status nftables` | Service non abilitato | `systemctl enable nftables` |
| Port forward non funziona | `iptables -L FORWARD` | FORWARD DROP senza eccezione | Aggiungi regola FORWARD per la porta |

### Debug con nft Trace: Esempio Completo

```bash
# Scenario: la porta 8080 non risponde ma la regola sembra corretta

# 1. Aggiungi trace per il traffico specifico
nft insert rule inet filter prerouting tcp dport 8080 meta nftrace set 1

# 2. Avvia monitoring
nft monitor trace &

# 3. Genera traffico di test
curl http://server:8080

# 4. Analizza output trace:
# Se il pacchetto viene droppato in 'input': regola filter mancante o errata
# Se il pacchetto non appare mai: firewall a monte, o servizio non in ascolto
# Se il pacchetto va in 'forward': il server sta routando, non è destinatario

# 5. Rimuovi trace
nft delete rule inet filter prerouting handle $(nft -a list chain inet filter prerouting | grep nftrace | awk '{print $NF}')
```

---

## Esercizi

### Esercizio 1 — Firewall Server Web con nftables

Progetta e implementa un firewall nftables per un server web di produzione:
- Policy DROP su input e forward
- SSH limitato a 3 connessioni/min per IP, solo dalla rete management 10.0.0.0/8
- HTTP/HTTPS aperti a tutti
- ICMP rate limited a 10/s
- Set per blacklist con timeout automatico
- Logging dei pacchetti droppati (rate limited)
- Counter con nomi per monitoring

**Criteri di successo:** `nft -c -f file.conf` valida senza errori, servizi raggiungibili, SSH protetto.

### Esercizio 2 — Gateway NAT con Port Forwarding

Configura una VM come gateway NAT per una rete 192.168.1.0/24:
- MASQUERADE verso l'interfaccia pubblica
- Port forwarding: 80→192.168.1.100:80, 443→192.168.1.100:443, 25→192.168.1.50:25
- Hairpin NAT funzionante (client interni che accedono via IP pubblico)
- Flowtable per performance
- Nessun altro traffico in ingresso dall'esterno

### Esercizio 3 — Migrazione iptables → nftables

Data questa configurazione iptables legacy:
```bash
iptables -P INPUT DROP
iptables -A INPUT -i lo -j ACCEPT
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -p tcp -m multiport --dports 22,80,443 -j ACCEPT
iptables -A INPUT -p icmp --icmp-type echo-request -m limit --limit 5/s -j ACCEPT
iptables -t nat -A POSTROUTING -s 10.0.0.0/24 -o eth0 -j MASQUERADE
```
1. Traduci con `iptables-restore-translate`
2. Riscrivi manualmente in nftables idiomatico (usa set, famiglia inet)
3. Valida con `nft -c -f`
4. Applica e verifica connettività

### Esercizio 4 — Fail2ban + firewalld Integration

Configura un server RHEL/CentOS con:
- firewalld con zone `public` (eth0) e `internal` (eth1)
- SSH, HTTP, HTTPS su public
- Fail2ban con backend nftables per proteggere SSH (ban 24h dopo 3 tentativi)
- Verifica che fail2ban crei correttamente le regole nftables
- Simula un brute force e verifica il ban

---

## Auto-valutazione

1. **Qual è la differenza tra le tabelle filter, nat, mangle e raw in iptables?**
   <details><summary>Risposta</summary>
   `filter`: filtraggio pacchetti (ACCEPT/DROP/REJECT), tabella di default. `nat`: NAT (SNAT/DNAT/MASQUERADE), opera su PREROUTING/OUTPUT/POSTROUTING. `mangle`: modifica header pacchetti (TOS, TTL, MARK), opera su tutti e 5 gli hook. `raw`: esclusione dal connection tracking (NOTRACK), opera su PREROUTING/OUTPUT con priorità massima (-300).
   </details>

2. **Perché le regole INPUT di iptables non proteggono le porte pubblicate da Docker?**
   <details><summary>Risposta</summary>
   Docker usa DNAT nella catena PREROUTING (tabella nat) per reindirizzare il traffico ai container. Il pacchetto viene modificato prima della decisione di routing e viene classificato come FORWARD, non INPUT. Le regole INPUT non vedono mai questo traffico. Per filtrare, usare la catena DOCKER-USER in FORWARD, oppure non pubblicare porte verso 0.0.0.0.
   </details>

3. **Cosa sono i flowtable in nftables e quando usarli?**
   <details><summary>Risposta</summary>
   I flowtable bypassano lo stack Netfilter completo per pacchetti di connessioni già stabilite. Dopo il primo pacchetto (elaborato normalmente), i pacchetti successivi vengono instradati direttamente a livello di ingress hook, senza attraversare prerouting/forward/postrouting. Usarli su gateway NAT ad alto throughput dove le performance sono critiche. Supportano anche offload hardware su NIC compatibili (flag `offload`).
   </details>

4. **Come funziona il rate limiting per-sorgente con nftables meter?**
   <details><summary>Risposta</summary>
   `add @set_name { ip saddr limit rate over 30/minute }` crea un set dinamico con flag `dynamic, timeout`. Per ogni IP sorgente, nftables mantiene un contatore separato. Quando un IP supera 30 richieste/min, la regola matcha e può droppare. Il timeout rimuove automaticamente gli IP inattivi dal set per evitare crescita illimitata della memoria.
   </details>

5. **Quale ICMPv6 è essenziale e non deve mai essere bloccato?**
   <details><summary>Risposta</summary>
   Neighbor Solicitation (tipo 135) e Neighbor Advertisement (tipo 136) — equivalenti IPv6 di ARP, necessari per risolvere indirizzi MAC. Router Solicitation (tipo 133) e Router Advertisement (tipo 134) — necessari per SLAAC e auto-configurazione. MLD (tipo 130/131/143) — necessario per multicast IPv6. Packet-too-big (tipo 2) — necessario per path MTU discovery. Senza questi, la connettività IPv6 si interrompe.
   </details>

6. **Qual è la strategia sicura per applicare regole firewall su un server remoto?**
   <details><summary>Risposta</summary>
   (1) Backup: `iptables-save > backup.rules` o `nft list ruleset > backup.nft`. (2) Job di ripristino: `echo "nft -f backup.nft" | at now + 5 min`. (3) Applicare le nuove regole. (4) Testare connettività. (5) Se funziona, cancellare il job `at`. Se non funziona, attendere il ripristino automatico. Alternative: usare console seriale IPMI/iLO/iDRAC, o `nft -f new.conf && sleep 60 && nft -f old.conf` (interrompere con Ctrl+C se le regole funzionano).
   </details>

7. **Come si differenziano verdict map e set in nftables?**
   <details><summary>Risposta</summary>
   Un set contiene solo dati (IP, porte, range) e si usa con `@set_name` nei match. Una verdict map (vmap) associa chiavi a verdict (accept, drop, jump chain_name) e decide direttamente l'azione. Esempio: `tcp dport vmap @port_policy` dove `port_policy = { 22: jump ssh_chain, 80: accept, 3306: drop }`. Le verdict map eliminano la necessità di regole multiple per routing basato su porta.
   </details>

---

## Letture primarie consigliate

- **nftables Wiki**: "nftables HOWTO" — https://wiki.nftables.org/wiki-nftables/index.php/Main_Page (consultato: 2026-05-23)
- **Netfilter Project**: documentazione ufficiale — https://www.netfilter.org/documentation/ (consultato: 2026-05-23)
- **kernel.org**: Documentation/networking/nf_conntrack-sysctl.rst — https://www.kernel.org/doc/Documentation/networking/nf_conntrack-sysctl.rst (consultato: 2026-05-23)
- **Red Hat**: "Configuring firewalls and packet filters" — RHEL 9 docs, https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/configuring_firewalls_and_packet_filters/ (consultato: 2026-05-23)
- **Libro**: "Linux Firewalls: Enhancing Security with nftables and Beyond" di Steve Suehring, Addison-Wesley, 4th edition
- **iptables Tutorial**: Oskar Andreasson, https://www.frozentux.net/iptables-tutorial/iptables-tutorial.html (consultato: 2026-05-23)
- **man nft(8)**: reference completa della sintassi nftables
- **man conntrack(8)**: gestione connection tracking
- **Docker Networking**: "Packet filtering and firewalls" — https://docs.docker.com/engine/network/packet-filtering-firewalls/ (consultato: 2026-05-23)

---

## Collegamenti incrociati

- [05-networking.md](05-networking.md) — TCP/IP, routing, interfacce di rete
- [07-kernel.md](07-kernel.md) — moduli kernel, sysctl, Netfilter nel kernel
- [11-sicurezza.md](11-sicurezza.md) — sicurezza Linux, hardening di base
- [32-vpn-wireguard-openvpn.md](32-vpn-wireguard-openvpn.md) — regole firewall per VPN
- [34-hardening-sicurezza-avanzata.md](34-hardening-sicurezza-avanzata.md) — hardening avanzato del server
- [14-containerizzazione.md](14-containerizzazione.md) — Docker networking e iptables
- [19-servizi-rete.md](19-servizi-rete.md) — DNS, DHCP (servizi da proteggere con firewall)
- [28-nginx-configurazione-avanzata.md](28-nginx-configurazione-avanzata.md) — rate limiting a livello applicativo
- [30-prometheus-grafana-monitoring.md](30-prometheus-grafana-monitoring.md) — monitoring dei counter nftables

---

## Glossario locale

| Termine | Definizione |
|---------|------------|
| **Chain** | Sequenza ordinata di regole associata a un hook Netfilter; in nftables creata dall'utente, in iptables predefinita |
| **Conntrack** | Sottosistema kernel che traccia lo stato delle connessioni per il firewalling stateful |
| **DNAT** | Destination NAT — modifica l'indirizzo/porta di destinazione (usato per port forwarding) |
| **Flowtable** | Meccanismo nftables per il fast path: dopo la prima elaborazione, i pacchetti bypassano lo stack completo |
| **Hook** | Punto nel percorso di rete dove Netfilter intercetta i pacchetti (prerouting, input, forward, output, postrouting) |
| **ipset** | Struttura dati kernel per gestire grandi insiemi di IP con lookup O(1); in nftables sostituito dai set nativi |
| **MASQUERADE** | SNAT dinamico: usa automaticamente l'IP dell'interfaccia di uscita (per IP dinamici) |
| **nftables** | Successore di iptables nel kernel Linux (dal 3.13); sintassi unificata, operazioni atomiche, set nativi |
| **Priority** | Valore numerico che determina l'ordine di elaborazione delle catene sullo stesso hook |
| **SNAT** | Source NAT — modifica l'indirizzo sorgente dei pacchetti in uscita |
| **Verdict map** | Struttura nftables che associa chiavi (porte, IP) direttamente a verdict (accept, drop, jump) |
| **Zone (firewalld)** | Raggruppamento di interfacce e sorgenti con un livello di fiducia e set di regole predefiniti |

---

## Architettura Netfilter: Hook, Famiglie e Percorso del Pacchetto nel Dettaglio

Per padroneggiare il firewalling Linux è necessario comprendere l'architettura interna di Netfilter oltre lo schema semplificato dei cinque hook. Netfilter opera come un framework di callback nel kernel: ogni hook è un punto di registrazione dove moduli kernel (o il bytecode nftables) possono registrare funzioni che vengono invocate per ogni pacchetto che attraversa quel punto.

### Famiglie Netfilter in nftables

nftables organizza le tabelle in famiglie, ognuna con hook specifici:

| Famiglia | Descrizione | Hook disponibili |
|----------|-------------|-----------------|
| `ip` | Solo IPv4 | prerouting, input, forward, output, postrouting |
| `ip6` | Solo IPv6 | prerouting, input, forward, output, postrouting |
| `inet` | IPv4 + IPv6 unificato | prerouting, input, forward, output, postrouting |
| `arp` | Pacchetti ARP | input, output |
| `bridge` | Frame Ethernet (bridging) | prerouting, input, forward, output, postrouting |
| `netdev` | Traffico raw per interfaccia | ingress, egress |

La famiglia `inet` è la scelta raccomandata per la maggior parte dei casi: una singola regola si applica sia a IPv4 che a IPv6 senza duplicazione. Le famiglie `ip` e `ip6` restano necessarie per regole specifiche ad un protocollo (ad esempio NAT, che in nftables richiede la famiglia `ip` o `ip6` per SNAT/DNAT con indirizzi specifici).

### Hook ingress e egress (famiglia netdev)

L'hook `ingress` (kernel 4.2+) e l'hook `egress` (kernel 5.16+) operano a un livello inferiore rispetto agli hook standard:

```
                    NIC Driver
                        │
                   ┌────┴────┐
                   │ ingress │ ← netdev (prima di qualsiasi decisione L3)
                   └────┬────┘
                        │
                   ┌────┴────┐
                   │prerouting│ ← ip/ip6/inet
                   └────┬────┘
                        │
                  [routing decision]
                   /            \
            ┌─────┴─────┐ ┌────┴────┐
            │   input   │ │ forward │
            └─────┬─────┘ └────┬────┘
                  │            │
            [processo       ┌──┴───────┐
             locale]        │postrouting│
                  │         └──┬───────┘
            ┌─────┴─────┐     │
            │  output   │     │
            └─────┬─────┘  ┌──┴──┐
                  │        │egress│ ← netdev (ultimo stadio prima della NIC)
            ┌─────┴─────┐  └──┬──┘
            │postrouting│     │
            └─────┬─────┘     │
                  │         NIC Driver
               ┌──┴──┐
               │egress│
               └──┬──┘
                  │
               NIC Driver
```

L'hook ingress è particolarmente utile per:

- **Filtraggio precoce ad alte prestazioni**: scartare traffico indesiderato prima che entri nello stack L3, riducendo il carico CPU
- **Mitigazione DDoS a livello kernel**: drop dei pacchetti prima del conntrack, eliminando l'overhead di tracking
- **Policy per interfaccia**: ogni catena netdev è legata a un dispositivo specifico
- **Classificazione e policing del traffico**: rate limiting a livello di interfaccia

```bash
# Esempio: filtraggio ingress per mitigazione DDoS precoce
table netdev filter_ingress {
    chain ingress_eth0 {
        type filter hook ingress device eth0 priority -500; policy accept;

        # Drop pacchetti con flag TCP invalidi (scansioni, attacchi)
        tcp flags & (fin|syn|rst|psh|ack|urg) == 0 drop
        tcp flags & (fin|syn) == (fin|syn) drop
        tcp flags & (syn|rst) == (syn|rst) drop

        # Drop frammenti IP (spesso usati in attacchi)
        ip frag-off & 0x1fff != 0 counter drop

        # Rate limiting globale sull'interfaccia
        limit rate over 100000/second burst 50000 packets drop
    }
}
```

L'hook egress (kernel 5.16+) opera simmetricamente in uscita:

```bash
table netdev filter_egress {
    chain egress_eth0 {
        type filter hook egress device eth0 priority 0; policy accept;

        # Previeni IP spoofing in uscita (BCP38/RFC 2827)
        ip saddr != 203.0.113.0/24 counter drop

        # Blocca traffico DNS in uscita non autorizzato (anti-exfiltration)
        udp dport 53 ip daddr != { 1.1.1.1, 9.9.9.9 } drop
    }
}
```

### Ordine Completo di Elaborazione con Priorità

Il percorso completo di un pacchetto in transito (forwarding) attraversa le catene in ordine di priorità:

```
ingress (netdev, priority -500..+500)
  → raw/PREROUTING (priority -300)
    → connection tracking (priority ~-200, automatico)
      → mangle/PREROUTING (priority -150)
        → nat/PREROUTING DNAT (priority -100)
          → routing decision
            → mangle/FORWARD (priority -150)
              → filter/FORWARD (priority 0)
                → security/FORWARD (priority 50, SELinux)
                  → mangle/POSTROUTING (priority -150)
                    → nat/POSTROUTING SNAT (priority 100)
                      → egress (netdev)
```

In nftables è possibile definire priorità custom per inserire catene in qualsiasi punto:

```bash
# Catena custom tra raw e mangle
chain early_filter {
    type filter hook prerouting priority -250; policy accept;
    # Eseguita dopo raw (-300) ma prima di mangle (-150)
}
```

---

## nftables: Sintassi Avanzata — Set, Mappe, Meter e Flowtable in Profondità

### Set Anonimi e Set con Nome

nftables supporta due tipi di set:

**Set anonimi** (inline, immutabili dopo la creazione):

```bash
# Set anonimo — definito inline nella regola
nft add rule inet filter input tcp dport { 22, 80, 443, 8080, 8443 } accept
nft add rule inet filter input ip saddr { 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 } accept
```

**Set con nome** (gestibili dinamicamente da CLI):

```bash
table inet filter {
    # Set statico con nome
    set web_ports {
        type inet_service
        elements = { 80, 443, 8080, 8443 }
    }

    # Set con flag: intervalli consentiti
    set allowed_ranges {
        type ipv4_addr
        flags interval
        elements = { 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 }
    }

    # Set con timeout automatico (auto-pulizia)
    set recent_visitors {
        type ipv4_addr
        flags dynamic, timeout
        timeout 30m
        size 65536
    }

    # Set concatenato (combinazione di campi)
    set allowed_access {
        type ipv4_addr . inet_service
        flags interval
        elements = {
            10.0.0.0/24 . 22,
            10.0.1.0/24 . 3306,
            10.0.2.0/24 . 6379,
        }
    }
}
```

### Tipi di Dato nei Set

| Tipo | Descrizione | Esempio |
|------|-------------|---------|
| `ipv4_addr` | Indirizzo IPv4 | `192.168.1.1`, `10.0.0.0/8` |
| `ipv6_addr` | Indirizzo IPv6 | `::1`, `2001:db8::/32` |
| `ether_addr` | Indirizzo MAC | `aa:bb:cc:dd:ee:ff` |
| `inet_service` | Porta TCP/UDP | `22`, `80-443` |
| `inet_proto` | Protocollo IP | `tcp`, `udp`, `icmp` |
| `ifname` | Nome interfaccia | `"eth0"`, `"wg0"` |
| `mark` | Packet mark | `0x1`, `0xff` |
| `ct_state` | Stato conntrack | `established`, `new` |

### Flag dei Set

| Flag | Significato |
|------|-------------|
| `constant` | Il set è immutabile dopo la creazione |
| `interval` | Gli elementi possono essere range o CIDR |
| `timeout` | Gli elementi hanno un timeout di scadenza |
| `dynamic` | Gli elementi possono essere aggiunti da regole (meter/add) |

### Mappe Avanzate (Data Maps)

Le mappe (map) associano una chiave a un valore di dati. A differenza delle verdict map (che associano a verdict come accept/drop), le data map restituiscono un valore usabile nella regola:

```bash
table ip nat {
    # Data map per DNAT: porta in arrivo → IP:porta destinazione
    map dnat_targets {
        type inet_service : ipv4_addr . inet_service
        elements = {
            80   : 192.168.1.10 . 80,
            443  : 192.168.1.10 . 443,
            8080 : 192.168.1.20 . 80,
            25   : 192.168.1.30 . 25,
            993  : 192.168.1.30 . 993,
        }
    }

    chain prerouting {
        type nat hook prerouting priority dstnat; policy accept;
        dnat ip addr . port to tcp dport map @dnat_targets
    }
}
```

```bash
# Data map per selezionare interfaccia di uscita in base alla sorgente
table inet mangle {
    map routing_policy {
        type ipv4_addr : mark
        flags interval
        elements = {
            10.0.1.0/24 : 0x1,    # traffico via ISP 1
            10.0.2.0/24 : 0x2,    # traffico via ISP 2
        }
    }

    chain prerouting {
        type route hook output priority mangle; policy accept;
        ip saddr vmap @routing_policy
    }
}
```

### Verdict Map Avanzate

Le verdict map (vmap) associano chiavi a decisioni (accept, drop, jump, goto):

```bash
table inet filter {
    # Verdict map per gestione differenziata per porta
    map service_policy {
        type inet_service : verdict
        elements = {
            22   : jump chain_ssh,
            80   : jump chain_http,
            443  : jump chain_http,
            3306 : jump chain_db,
            6379 : jump chain_db,
            53   : accept,
        }
    }

    chain input {
        type filter hook input priority 0; policy drop;
        ct state established,related accept
        ct state invalid drop
        iif "lo" accept
        tcp dport vmap @service_policy
    }

    chain chain_ssh {
        ip saddr 10.0.0.0/8 accept
        ip saddr @ssh_whitelist accept
        limit rate 2/minute burst 5 packets accept
        counter drop
    }

    chain chain_http {
        # Rate limiting per sorgente
        meter http_ratelimit { ip saddr limit rate over 100/second burst 50 packets } drop
        accept
    }

    chain chain_db {
        ip saddr { 10.0.1.0/24, 10.0.2.0/24 } accept
        counter log prefix "db-unauthorized: " drop
    }
}
```

### Meter: Rate Limiting Dinamico Per-Sorgente

I meter (precedentemente chiamati "dynamic set con limit") creano bucket di rate limiting separati per ogni chiave (tipicamente l'IP sorgente):

```bash
table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;
        ct state established,related accept

        # Meter: ogni IP sorgente ha il proprio contatore
        # Se supera 50 nuove connessioni HTTP al secondo → drop
        tcp dport { 80, 443 } ct state new \
            meter http_flood { ip saddr limit rate over 50/second burst 100 packets } \
            counter drop

        # Meter con chiave concatenata: rate limit per IP+porta
        tcp dport { 80, 443 } ct state new \
            meter http_per_port { ip saddr . tcp dport limit rate over 30/second } \
            counter drop

        # Meter per ICMP flood protection per sorgente
        ip protocol icmp \
            meter icmp_flood { ip saddr limit rate over 10/second burst 20 packets } \
            counter drop

        # Accetta il traffico che non ha superato i limiti
        tcp dport { 80, 443 } accept
        ip protocol icmp accept
    }
}
```

I meter sono superiori al modulo `hashlimit` di iptables perché:

- Sintassi nativa, nessun modulo separato da caricare
- Supportano chiavi concatenate (IP sorgente + porta destinazione)
- Si integrano con il sistema di set nftables
- Possono avere timeout per auto-pulizia delle entry inattive

### Flowtable: Configurazione Avanzata e Offload Hardware

I flowtable accelerano il forwarding dei pacchetti spostando le connessioni stabilite dal percorso standard (slow path) a un percorso ottimizzato (fast path) che bypassa la maggior parte degli hook Netfilter.

```bash
table inet filter {
    # Flowtable con offload software
    flowtable ft_software {
        hook ingress priority 0
        devices = { eth0, eth1, eth2 }
    }

    # Flowtable con offload hardware (richiede NIC compatibile)
    flowtable ft_hardware {
        hook ingress priority 0
        devices = { eth0, eth1 }
        flags offload    # TC flower offload alla NIC
    }

    chain forward {
        type filter hook forward priority 0; policy drop;

        # Le connessioni stabilite usano il flowtable (fast path)
        ct state established flow add @ft_software counter accept

        # Le connessioni correlate passano normalmente
        ct state related accept
        ct state invalid drop

        # Nuove connessioni: valutazione completa del ruleset
        iifname "eth1" oifname "eth0" accept
        iifname "eth2" oifname "eth0" accept
    }
}
```

**Verifica del funzionamento:**

```bash
# Conta pacchetti nel flowtable
cat /proc/net/netfilter/nf_flowtable

# Con hardware offload, verifica lo stato dell'offload nella NIC
ethtool -k eth0 | grep flow
# hw-tc-offload: on  ← necessario per flowtable hardware

# Statistiche conntrack con offload
conntrack -L | grep -c OFFLOAD
```

**Limitazioni dei flowtable:**

- Non funzionano con catene che devono ispezionare ogni pacchetto (es. logging, deep inspection)
- L'offload hardware dipende dal driver della NIC (non tutte le schede lo supportano)
- Non applicabile a traffico che richiede mangling per-pacchetto
- Il countering nel flowtable è approssimativo (aggiornato periodicamente, non per pacchetto)

---

## Connection Tracking Avanzato: Conntrack Helper, Zone e Tuning

### Conntrack Helper per Protocolli Multi-Connessione

Alcuni protocolli (FTP, SIP, H.323, TFTP, IRC DCC) usano connessioni secondarie il cui indirizzo/porta è negoziato nella connessione primaria. I conntrack helper ispezionano il payload del protocollo applicativo per creare automaticamente expectation per queste connessioni secondarie, classificandole come RELATED.

```bash
# Configurazione helper FTP in nftables
table inet filter {
    # Dichiara l'helper FTP
    ct helper ftp-standard {
        type "ftp" protocol tcp
    }

    chain input {
        type filter hook input priority 0; policy drop;
        ct state established,related accept

        # Connessioni FTP control: assegna l'helper
        tcp dport 21 ct state new ct helper set "ftp-standard" accept

        # Le connessioni FTP data (RELATED) vengono accettate
        # automaticamente dalla regola ct state related sopra
    }
}

# Helper SIP per VoIP
table inet filter {
    ct helper sip-udp {
        type "sip" protocol udp
    }

    ct helper sip-tcp {
        type "sip" protocol tcp
    }

    chain input {
        type filter hook input priority 0; policy drop;
        ct state established,related accept

        # SIP control
        udp dport 5060 ct state new ct helper set "sip-udp" accept
        tcp dport 5060 ct state new ct helper set "sip-tcp" accept

        # RTP media (porte alte, RELATED grazie all'helper SIP)
        # Accettate automaticamente da ct state related
    }
}
```

**Moduli helper disponibili nel kernel:**

```bash
# Lista degli helper caricati
lsmod | grep nf_conntrack_
# nf_conntrack_ftp
# nf_conntrack_sip
# nf_conntrack_tftp
# nf_conntrack_irc
# nf_conntrack_h323
# nf_conntrack_pptp
# nf_conntrack_amanda

# Carica un helper manualmente
modprobe nf_conntrack_ftp
modprobe nf_conntrack_sip
```

### Conntrack Zone: Isolamento del Tracking

Le zone conntrack permettono di mantenere tabelle di tracking separate per flussi di traffico diversi, evitando collisioni in scenari multi-tenant o con NAT sovrapposti:

```bash
table inet raw {
    chain prerouting {
        type filter hook prerouting priority raw; policy accept;

        # Traffico dall'interfaccia del tenant A → zona 1
        iifname "veth-tenantA" ct zone set 1
        # Traffico dall'interfaccia del tenant B → zona 2
        iifname "veth-tenantB" ct zone set 2
    }

    chain output {
        type filter hook output priority raw; policy accept;

        oifname "veth-tenantA" ct zone set 1
        oifname "veth-tenantB" ct zone set 2
    }
}
```

Con zone diverse, due tenant possono avere lo stesso spazio di indirizzamento (es. entrambi 192.168.1.0/24) senza che le entry conntrack collidano.

### Conntrack Tuning per Server ad Alto Traffico

```bash
# /etc/sysctl.d/99-conntrack-tuning.conf

# Massimo numero di connessioni tracciate
# Formula: nf_conntrack_max = RAM_in_bytes / 16384 / 2
# Per un server con 32GB: ~1M entry
net.netfilter.nf_conntrack_max = 1048576

# Dimensione hash table (nf_conntrack_max / 4 è un buon default)
# NOTA: questo parametro è impostabile solo al caricamento del modulo
# Aggiungere in /etc/modprobe.d/nf_conntrack.conf:
# options nf_conntrack hashsize=262144

# Timeout aggressivi per liberare entry più velocemente
net.netfilter.nf_conntrack_tcp_timeout_established = 3600
net.netfilter.nf_conntrack_tcp_timeout_time_wait = 30
net.netfilter.nf_conntrack_tcp_timeout_close_wait = 30
net.netfilter.nf_conntrack_tcp_timeout_fin_wait = 30
net.netfilter.nf_conntrack_tcp_timeout_last_ack = 15
net.netfilter.nf_conntrack_tcp_timeout_syn_recv = 30
net.netfilter.nf_conntrack_tcp_timeout_syn_sent = 30
net.netfilter.nf_conntrack_tcp_timeout_close = 5
net.netfilter.nf_conntrack_udp_timeout = 30
net.netfilter.nf_conntrack_udp_timeout_stream = 120
net.netfilter.nf_conntrack_icmp_timeout = 15
net.netfilter.nf_conntrack_generic_timeout = 120

# Abilita TCP loose mode (utile per asymmetric routing)
# ATTENZIONE: riduce la sicurezza dello stateful inspection
# net.netfilter.nf_conntrack_tcp_loose = 1

# Disabilita logging degli eventi conntrack (performance)
net.netfilter.nf_conntrack_log_invalid = 0
```

**Monitoraggio conntrack in produzione:**

```bash
# Script di monitoring per Prometheus/node_exporter
#!/bin/bash
CURRENT=$(cat /proc/sys/net/netfilter/nf_conntrack_count)
MAX=$(cat /proc/sys/net/netfilter/nf_conntrack_max)
PERCENT=$((CURRENT * 100 / MAX))

echo "conntrack_current=$CURRENT conntrack_max=$MAX usage=$PERCENT%"

if [ "$PERCENT" -gt 80 ]; then
    echo "WARNING: conntrack usage above 80%" >&2
    # Dettaglio per protocollo
    conntrack -L 2>/dev/null | awk '{print $1}' | sort | uniq -c | sort -rn
fi

# Statistiche dettagliate
conntrack -S
# Campi importanti:
# searched: numero di lookup nella hash table
# found: entry trovate
# insert: nuove entry inserite
# insert_failed: inserimenti falliti (tabella piena!)
# drop: pacchetti droppati per tabella piena
# early_drop: entry rimosse prematuramente per fare spazio
```

---

## NAT Avanzato: Scenari Complessi

### NAT con Load Balancing (Round-Robin)

nftables supporta DNAT verso pool di server per distribuzione del carico di base:

```bash
table ip nat {
    chain prerouting {
        type nat hook prerouting priority dstnat; policy accept;

        # Load balancing round-robin tra 3 backend HTTP
        iifname "eth0" tcp dport 80 \
            dnat to numgen inc mod 3 map { \
                0 : 192.168.1.10, \
                1 : 192.168.1.11, \
                2 : 192.168.1.12  \
            }

        # Load balancing con porte diverse per backend
        iifname "eth0" tcp dport 443 \
            dnat to numgen inc mod 2 map { \
                0 : 192.168.1.10:443, \
                1 : 192.168.1.11:8443  \
            }

        # Random balancing (distribuzione probabilistica)
        iifname "eth0" tcp dport 8080 \
            dnat to numgen random mod 3 map { \
                0 : 192.168.1.20, \
                1 : 192.168.1.21, \
                2 : 192.168.1.22  \
            }
    }

    chain postrouting {
        type nat hook postrouting priority srcnat; policy accept;
        oifname "eth0" masquerade
    }
}
```

### Redirect a Proxy Trasparente

Il redirect redirige il traffico a un processo locale sulla stessa macchina (tipicamente un proxy):

```bash
table ip nat {
    chain prerouting {
        type nat hook prerouting priority dstnat; policy accept;

        # Redirect HTTP a proxy squid locale (porta 3128)
        iifname "eth1" tcp dport 80 redirect to :3128

        # Redirect DNS a resolver locale
        iifname "eth1" udp dport 53 redirect to :5353
        iifname "eth1" tcp dport 53 redirect to :5353
    }
}
```

### NAT Source con Pool di Indirizzi

Quando il gateway ha più IP pubblici, è possibile distribuire le connessioni:

```bash
table ip nat {
    chain postrouting {
        type nat hook postrouting priority srcnat; policy accept;

        # SNAT con pool di IP (il kernel distribuisce automaticamente)
        oifname "eth0" ip saddr 192.168.0.0/16 \
            snat to 203.0.113.10-203.0.113.20

        # SNAT persistente per IP sorgente (sticky)
        oifname "eth0" ip saddr 10.0.0.0/8 \
            snat to 203.0.113.10-203.0.113.20 persistent
    }
}
```

### Doppio NAT (Carrier-Grade NAT Simulation)

Scenario: rete interna → NAT locale → NAT del provider.

```bash
table ip nat {
    chain prerouting {
        type nat hook prerouting priority dstnat; policy accept;
        # DNAT dal range CGN al server interno
        ip daddr 100.64.0.100 tcp dport 80 dnat to 192.168.1.100:80
    }

    chain postrouting {
        type nat hook postrouting priority srcnat; policy accept;
        # SNAT per traffico verso internet
        oifname "eth0" ip saddr 192.168.0.0/16 snat to 100.64.0.1
        # Masquerade per traffico verso la rete CGN
        oifname "eth-cgn" masquerade
    }
}
```

### NAT64 e NPTv6

Per ambienti IPv6-only che devono comunicare con server IPv4:

```bash
# NAT64: traduce IPv6 → IPv4 (richiede il modulo jool o tayga)
# nftables non gestisce direttamente NAT64 a livello di traduzione di protocollo,
# ma può instradare il traffico verso un daemon NAT64

table ip6 nat {
    chain prerouting {
        type nat hook prerouting priority dstnat; policy accept;
        # Redirige traffico verso il prefisso NAT64 (64:ff9b::/96)
        # al daemon NAT64 locale
        ip6 daddr 64:ff9b::/96 redirect to :46464
    }
}

# NPTv6: Network Prefix Translation (RFC 6296)
# Traduce solo il prefisso, non la parte host
# Utile per multihoming IPv6 senza PI address space
table ip6 nat {
    chain postrouting {
        type nat hook postrouting priority srcnat; policy accept;
        oifname "eth0" ip6 saddr 2001:db8:a::/48 \
            snat to 2001:db8:b::/48
    }
}
```

---

## Rate Limiting Avanzato e Mitigazione DDoS con nftables

### Architettura Multi-Livello di Difesa

La difesa contro DDoS efficace opera a più livelli, ognuno con strumenti diversi:

```
Livello 1: XDP/eBPF  ← drop a livello NIC, prima del kernel stack
Livello 2: netdev/ingress  ← nftables hook ingress, prima del conntrack
Livello 3: raw/NOTRACK  ← bypass conntrack per traffico ad alto volume
Livello 4: filter/input  ← regole stateful con meter per-sorgente
Livello 5: applicazione  ← rate limiting nginx/HAProxy/applicativo
```

### Livello 2: Filtraggio Ingress Anti-DDoS

```bash
table netdev antiddos {
    # Blacklist gestita esternamente (threat intelligence feeds)
    set threat_intel {
        type ipv4_addr
        flags interval
        # Popolata da script esterno che aggiorna da feed
    }

    chain ingress_wan {
        type filter hook ingress device eth0 priority -500; policy accept;

        # Drop immediato da threat intelligence
        ip saddr @threat_intel counter drop

        # Drop pacchetti con TTL troppo basso (indicativo di attacco)
        ip ttl < 2 counter drop

        # Drop pacchetti TCP con flag invalidi
        tcp flags & (fin|syn|rst|psh|ack|urg) == 0 counter drop
        tcp flags & (fin|syn) == (fin|syn) counter drop
        tcp flags & (syn|rst) == (syn|rst) counter drop
        tcp flags & (fin|rst) == (fin|rst) counter drop
        tcp flags & (fin|psh|ack) == (fin|psh) counter drop
        tcp flags & (ack|urg) == urg counter drop

        # Rate limiting globale: protezione contro volumetrici
        limit rate over 200000/second burst 100000 packets counter drop

        # Rate limiting ICMP globale
        ip protocol icmp limit rate over 1000/second counter drop
    }
}
```

### Livello 3: NOTRACK per Traffico ad Alto Volume

Per servizi che gestiscono un numero enorme di connessioni (DNS resolver, CDN), il conntrack può diventare il collo di bottiglia. La tabella raw permette di bypassarlo:

```bash
table inet raw {
    chain prerouting {
        type filter hook prerouting priority raw; policy accept;

        # NOTRACK per traffico DNS (alto volume, stateless per natura)
        udp dport 53 notrack
        udp sport 53 notrack

        # NOTRACK per traffico HTTP/HTTPS su CDN ad alto volume
        # ATTENZIONE: perdi il stateful inspection
        tcp dport { 80, 443 } ip daddr 203.0.113.0/24 notrack
    }

    chain output {
        type filter hook output priority raw; policy accept;

        udp sport 53 notrack
        udp dport 53 notrack
        tcp sport { 80, 443 } ip saddr 203.0.113.0/24 notrack
    }
}

# Le regole filter devono gestire il traffico UNTRACKED
table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;
        ct state established,related accept

        # Traffico UNTRACKED (da NOTRACK) — gestito esplicitamente
        ct state untracked udp dport 53 accept
        ct state untracked tcp dport { 80, 443 } accept

        ct state invalid drop
    }
}
```

### Livello 4: Rate Limiting Granulare con Meter

```bash
table inet ddos_protection {
    # Set per ban automatico degli IP che superano i limiti
    set auto_blacklist {
        type ipv4_addr
        flags dynamic, timeout
        timeout 1h
        size 131072
    }

    chain input {
        type filter hook input priority -10; policy accept;

        # Drop immediato per IP auto-bannati
        ip saddr @auto_blacklist counter drop

        # SYN flood protection per-sorgente
        tcp flags syn tcp dport { 80, 443 } \
            meter syn_flood { ip saddr limit rate over 100/second burst 200 packets } \
            add @auto_blacklist { ip saddr timeout 30m } \
            counter drop

        # HTTP connection rate per-sorgente
        tcp dport { 80, 443 } ct state new \
            meter http_conn_rate { ip saddr limit rate over 60/second burst 120 packets } \
            add @auto_blacklist { ip saddr timeout 15m } \
            counter drop

        # SSH brute force: 5 tentativi poi ban 24h
        tcp dport 22 ct state new \
            meter ssh_bruteforce { ip saddr limit rate over 5/minute burst 10 packets } \
            add @auto_blacklist { ip saddr timeout 24h } \
            counter drop

        # DNS amplification protection
        udp dport 53 \
            meter dns_flood { ip saddr limit rate over 50/second burst 100 packets } \
            counter drop
    }
}
```

### Protezione Contro Attacchi Specifici

```bash
table inet attack_mitigation {
    chain input {
        type filter hook input priority -5; policy accept;

        # Slowloris/Slow HTTP: limita connessioni simultanee per IP
        tcp dport { 80, 443 } ct state new \
            meter conn_limit { ip saddr ct count over 100 } \
            counter reject with tcp reset

        # UDP flood generici
        udp \
            meter udp_flood { ip saddr limit rate over 500/second burst 1000 packets } \
            counter drop

        # Protezione contro SYN con dimensione anomala
        tcp flags syn tcp option maxseg size < 536 counter drop

        # Fragment flood
        ip frag-off & 0x1fff != 0 \
            meter frag_flood { ip saddr limit rate over 100/second } \
            counter drop

        # LAND attack (sorgente == destinazione)
        ip saddr == ip daddr counter drop
    }
}
```

---

## Logging Avanzato con NFLOG e ulogd2

### Limiti del Logging Kernel (LOG target)

Il logging standard di nftables (`log prefix "..." level warn`) scrive nel kernel ring buffer (dmesg/syslog). Questo presenta problemi in produzione:

- Riempie il journal di systemd e syslog con messaggi ad alto volume
- Non è strutturato (parsing complesso)
- Nessun supporto per output su file dedicati, database o formati come JSON
- Con alto volume di log, il kernel rallenta

### NFLOG: Logging Userspace

NFLOG invia i pacchetti loggati a un daemon userspace (tipicamente ulogd2) tramite netlink socket, separando completamente il logging dal kernel log:

```bash
table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;
        ct state established,related accept

        # Log con NFLOG verso gruppo 0 (ulogd2)
        tcp dport 22 ct state new log prefix "SSH-NEW: " group 0 accept

        # Log pacchetti droppati verso gruppo 1 (file separato)
        log prefix "DROPPED: " group 1 counter drop
    }
}
```

### Configurazione ulogd2

```bash
# Installa ulogd2
apt install ulogd2 ulogd2-json ulogd2-pcap  # Debian/Ubuntu
dnf install ulogd2                            # RHEL/Fedora

# /etc/ulogd.conf — configurazione principale

[global]
logfile="/var/log/ulogd/ulogd.log"
stack=log1:NFLOG,base1:BASE,ifi1:IFINDEX,ip2str1:IP2STR,mac2str1:HWHDR,json1:JSON
stack=log2:NFLOG,base2:BASE,ifi2:IFINDEX,ip2str2:IP2STR,mac2str2:HWHDR,pcap1:PCAP

# Stack 1: NFLOG gruppo 0 → output JSON
[log1]
group=0
numeric_label=0

[json1]
file="/var/log/ulogd/firewall.json"
sync=1
timestamp=1

# Stack 2: NFLOG gruppo 1 → output PCAP
[log2]
group=1
numeric_label=1

[pcap1]
file="/var/log/ulogd/dropped.pcap"
sync=1

# Avvia ulogd2
systemctl enable --now ulogd2
```

**Output JSON (strutturato, parsabile):**

```json
{
  "timestamp": "2026-05-24T10:15:33.123456+0200",
  "oob.prefix": "SSH-NEW: ",
  "oob.in": "eth0",
  "oob.out": "",
  "src_ip": "203.0.113.50",
  "dest_ip": "10.0.0.1",
  "ip.protocol": 6,
  "src_port": 54321,
  "dest_port": 22,
  "raw.mac_saddr": "aa:bb:cc:dd:ee:ff",
  "tcp.syn": 1,
  "ip.ttl": 64
}
```

### Log Rotation e Integrazione con Sistemi di Analisi

```bash
# /etc/logrotate.d/ulogd2
/var/log/ulogd/firewall.json {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    postrotate
        systemctl reload ulogd2
    endscript
}

# Integrazione con journald (per log strutturati)
# nftables con log level scrive in journal; per query:
journalctl -k --grep="nft-dropped" --since="1 hour ago"

# Integrazione con Loki/Promtail (esempio config Promtail)
# Aggiungere in promtail-config.yaml:
# - job_name: nftables
#   static_configs:
#     - targets: [localhost]
#       labels:
#         job: firewall
#         __path__: /var/log/ulogd/firewall.json
```

---

## Integrazione con systemd

### nftables.service: Struttura e Funzionamento

La persistenza delle regole nftables è gestita dal servizio systemd `nftables.service`:

```bash
# Verifica il servizio
systemctl cat nftables.service
# Tipico contenuto:
# [Service]
# Type=oneshot
# RemainAfterExit=yes
# ExecStart=/usr/sbin/nft -f /etc/nftables.conf
# ExecReload=/usr/sbin/nft -f /etc/nftables.conf
# ExecStop=/usr/sbin/nft flush ruleset
```

```bash
# Workflow operativo

# 1. Modifica la configurazione
vim /etc/nftables.conf

# 2. Valida PRIMA di applicare
nft -c -f /etc/nftables.conf
# Errore? Correggi prima di procedere

# 3. Applica (reload atomico)
systemctl reload nftables
# oppure
nft -f /etc/nftables.conf

# 4. Verifica
nft list ruleset

# 5. Salva il ruleset corrente nel file di configurazione
# (se le modifiche sono state fatte da CLI)
nft list ruleset > /etc/nftables.conf.new
# Rivedi e poi sostituisci:
mv /etc/nftables.conf.new /etc/nftables.conf
```

### Ordinamento dei Servizi con systemd

```bash
# Assicurarsi che nftables parta prima dei servizi di rete
systemctl enable nftables

# Verifica l'ordine di avvio
systemctl list-dependencies nftables.service
systemctl list-dependencies --reverse nftables.service

# nftables.service tipicamente ha:
# Before=network-pre.target
# Wants=network-pre.target
# Questo garantisce che il firewall sia attivo PRIMA che le
# interfacce di rete vengano configurate
```

### Configurazione Modulare con Include

Per ambienti complessi, suddividere la configurazione in file modulari:

```bash
# /etc/nftables.conf — file principale
#!/usr/sbin/nft -f

flush ruleset

# Definizioni globali
include "/etc/nftables.d/definitions.nft"

# Tabella filter
include "/etc/nftables.d/filter.nft"

# Tabella NAT
include "/etc/nftables.d/nat.nft"

# Set gestiti dinamicamente
include "/etc/nftables.d/sets.nft"

# Regole specifiche per servizio
include "/etc/nftables.d/services/*.nft"
```

```bash
# /etc/nftables.d/definitions.nft
define WAN_IF = eth0
define LAN_IF = eth1
define DMZ_IF = eth2
define LAN_NET = 192.168.1.0/24
define DMZ_NET = 10.0.10.0/24
define DNS_SERVERS = { 1.1.1.1, 9.9.9.9 }
define NTP_SERVERS = { 162.159.200.1, 162.159.200.123 }
```

```bash
# /etc/nftables.d/services/ssh.nft
chain ssh_rules {
    ip saddr 10.0.0.0/8 accept
    meter ssh_limit { ip saddr limit rate over 3/minute burst 5 packets } drop
    accept
}
```

### Integrazione con systemd-networkd e NetworkManager

```bash
# systemd-networkd: nftables viene attivato prima tramite
# network-pre.target, quindi le regole sono già attive quando
# le interfacce vengono configurate

# NetworkManager dispatcher per regole post-connessione:
# /etc/NetworkManager/dispatcher.d/99-nftables-reload
#!/bin/bash
if [ "$2" = "up" ]; then
    systemctl reload nftables 2>/dev/null || true
fi
```

### Timer systemd per Aggiornamento Automatico dei Set

```bash
# /etc/systemd/system/nftables-update-threatintel.service
[Unit]
Description=Aggiorna set threat intelligence nftables
After=network-online.target nftables.service
Requires=nftables.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/update-threatintel.sh

# /etc/systemd/system/nftables-update-threatintel.timer
[Unit]
Description=Aggiorna threat intel ogni 6 ore

[Timer]
OnCalendar=*-*-* 00/6:00:00
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
```

```bash
# /usr/local/bin/update-threatintel.sh
#!/bin/bash
set -euo pipefail

TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT

# Scarica la lista (esempio: Spamhaus DROP)
curl -sS https://www.spamhaus.org/drop/drop.txt \
    | grep -v '^;' | awk '{print $1}' > "$TMPFILE"

# Flush e ricarica il set
nft flush set inet filter threat_intel 2>/dev/null || true

while IFS= read -r cidr; do
    [ -z "$cidr" ] && continue
    nft add element inet filter threat_intel "{ $cidr }" 2>/dev/null || true
done < "$TMPFILE"

logger "nftables: threat_intel set aggiornato con $(wc -l < "$TMPFILE") entry"
```

---

## Fail2ban con nftables: Configurazione Completa

### Architettura dell'Integrazione

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Log files   │────►│  fail2ban    │────►│  nftables API   │
│  (auth.log,  │     │  (daemon)    │     │  (nft command)  │
│  nginx.log)  │     │              │     │                 │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                                          ┌────────┴────────┐
                                          │  Netfilter set   │
                                          │  (kernel)        │
                                          └─────────────────┘
```

Fail2ban con backend nftables crea un set nftables per ogni jail e aggiunge/rimuove IP dal set quando banna/sbanna.

### Configurazione Dettagliata

```bash
# /etc/fail2ban/jail.local

[DEFAULT]
# Backend nftables per tutte le jail
banaction = nftables-multiport
banaction_allports = nftables-allports

# Parametri temporali
bantime = 1h
findtime = 10m
maxretry = 5

# Ignora IP fidati
ignoreip = 127.0.0.1/8 ::1 10.0.0.0/8

# Backend di rilevamento
backend = systemd

# ─── Jail: SSH ───
[sshd]
enabled = true
port = ssh
filter = sshd
maxretry = 3
bantime = 24h
findtime = 15m

# ─── Jail: SSH con DDoS ───
[sshd-ddos]
enabled = true
port = ssh
filter = sshd-ddos
maxretry = 6
bantime = 48h
findtime = 600

# ─── Jail: Nginx autenticazione ───
[nginx-http-auth]
enabled = true
port = http,https
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 5
bantime = 2h

# ─── Jail: Nginx rate limit ───
[nginx-limit-req]
enabled = true
port = http,https
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 10
bantime = 1h

# ─── Jail: Nginx bot detection ───
[nginx-botsearch]
enabled = true
port = http,https
filter = nginx-botsearch
logpath = /var/log/nginx/access.log
maxretry = 2
bantime = 24h

# ─── Jail: Postfix ───
[postfix]
enabled = true
port = smtp,465,587
filter = postfix
logpath = /var/log/mail.log
maxretry = 5
bantime = 12h

# ─── Jail: Recidiva (ban dei recidivi) ───
[recidive]
enabled = true
filter = recidive
logpath = /var/log/fail2ban.log
banaction = nftables-allports
maxretry = 3
bantime = 1w
findtime = 1d
```

### Action nftables Custom

```bash
# /etc/fail2ban/action.d/nftables-custom.conf
# Action personalizzata con logging e notifica

[Definition]
actionstart = nft add table inet f2b_<name>
              nft add set inet f2b_<name> addr_set '{ type ipv4_addr; flags timeout; }'
              nft add chain inet f2b_<name> input '{ type filter hook input priority -1; policy accept; }'
              nft add rule inet f2b_<name> input ip saddr @addr_set log prefix "f2b-<name>-ban: " group 2 counter reject

actionstop = nft delete table inet f2b_<name>

actionban = nft add element inet f2b_<name> addr_set '{ <ip> timeout <bantime>s }'

actionunban = nft delete element inet f2b_<name> addr_set '{ <ip> }'

actioncheck = nft list set inet f2b_<name> addr_set
```

### Verifica e Gestione Operativa

```bash
# Stato generale
fail2ban-client status

# Stato di una jail specifica
fail2ban-client status sshd

# Verifica che le regole nftables siano state create
nft list ruleset | grep f2b

# Lista IP bannati per una jail
fail2ban-client get sshd banned

# Ban manuale
fail2ban-client set sshd banip 203.0.113.50

# Unban manuale
fail2ban-client set sshd unbanip 203.0.113.50

# Test di un filtro su un log
fail2ban-regex /var/log/auth.log /etc/fail2ban/filter.d/sshd.conf

# Ricarica configurazione
fail2ban-client reload
```

---

## Regole Firewall IPv6: Guida Completa

### Differenze Fondamentali rispetto a IPv4

IPv6 introduce requisiti specifici per il firewall che non hanno equivalente in IPv4:

1. **ICMPv6 è vitale**: IPv6 usa ICMPv6 per funzionalità che in IPv4 sono gestite da ARP e altri protocolli
2. **NDP (Neighbor Discovery Protocol)**: sostituisce ARP; se bloccato, la connettività di rete si interrompe
3. **SLAAC (Stateless Address Autoconfiguration)**: richiede Router Advertisement e Solicitation
4. **MLD (Multicast Listener Discovery)**: necessario per il multicast IPv6
5. **Link-local**: ogni interfaccia ha un indirizzo fe80::/10 che non va mai bloccato in ingresso locale
6. **Path MTU Discovery**: packet-too-big ICMPv6 è fondamentale; bloccarlo causa blackhole routing

### Ruleset IPv6 Completo

```bash
table ip6 firewall_v6 {
    # Set per IPv6 fidati
    set trusted_v6 {
        type ipv6_addr
        flags interval
        elements = {
            2001:db8:a::/48,    # rete management
            ::1/128,            # loopback
        }
    }

    chain input {
        type filter hook input priority 0; policy drop;

        # Loopback
        iif "lo" accept

        # Conntrack stateful
        ct state established,related accept
        ct state invalid drop

        # ─── ICMPv6 ESSENZIALI (non bloccare MAI) ───
        # Errori ICMPv6 (RFC 4890 §4.3.1)
        icmpv6 type {
            destination-unreachable,
            packet-too-big,
            time-exceeded,
            parameter-problem,
        } accept

        # NDP (RFC 4861) — senza questi IPv6 non funziona
        icmpv6 type {
            nd-router-solicit,
            nd-router-advert,
            nd-neighbor-solicit,
            nd-neighbor-advert,
        } ip6 hoplimit 255 accept
        # hoplimit 255 = solo link-local (anti-spoofing NDP)

        # MLD (RFC 2710, RFC 3810)
        icmpv6 type {
            mld-listener-query,
            mld-listener-report,
            mld2-listener-report,
            mld-listener-done,
        } ip6 saddr fe80::/10 accept

        # Echo request/reply (ping6) — opzionale ma utile
        icmpv6 type { echo-request, echo-reply } \
            limit rate 10/second burst 20 packets accept

        # ─── Servizi ───
        tcp dport { 22, 80, 443 } accept

        # SSH solo da rete fidata IPv6
        tcp dport 22 ip6 saddr @trusted_v6 accept

        # ─── Logging e drop ───
        limit rate 5/minute log prefix "ip6-dropped: " level warn
        counter drop
    }

    chain forward {
        type filter hook forward priority 0; policy drop;
        ct state established,related accept
        ct state invalid drop
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}
```

### IPv6 Privacy Extensions e Firewall

Le Privacy Extensions (RFC 4941) generano indirizzi IPv6 temporanei che cambiano periodicamente. Questo impatta il firewalling:

```bash
# Non fare affidamento su indirizzi temporanei per regole di filtraggio
# Usare range di prefisso anziché indirizzi specifici
ip6 saddr 2001:db8:a:1::/64 accept    # Corretto: intero prefisso
# ip6 saddr 2001:db8:a:1::dead:beef accept  # Fragile: potrebbe cambiare
```

### Dual-Stack: Famiglia inet Raccomandata

Per evitare duplicazione di regole tra IPv4 e IPv6:

```bash
# PREFERIRE inet per regole che si applicano a entrambi i protocolli
table inet dual_stack {
    chain input {
        type filter hook input priority 0; policy drop;
        iif "lo" accept
        ct state established,related accept
        ct state invalid drop

        # Regole per ENTRAMBI (una sola volta)
        tcp dport { 22, 80, 443 } accept

        # Regole solo IPv4
        ip protocol icmp limit rate 10/second accept

        # Regole solo IPv6
        icmpv6 type {
            destination-unreachable,
            packet-too-big,
            time-exceeded,
            nd-router-solicit,
            nd-router-advert,
            nd-neighbor-solicit,
            nd-neighbor-advert,
        } accept

        limit rate 5/minute log prefix "dropped: " counter drop
    }
}
```

---

## Ispezione Stateful Avanzata

### Stateful Inspection: Come Funziona Internamente

Il firewalling stateful di Linux (tramite conntrack) mantiene una tabella di stato di tutte le connessioni attive. Per ogni pacchetto, il kernel:

1. Cerca una entry esistente nella tabella conntrack (hash lookup O(1))
2. Se trovata: classifica il pacchetto come ESTABLISHED o RELATED
3. Se non trovata: classifica come NEW (primo pacchetto di una connessione)
4. Se non conforme a nessun protocollo noto: classifica come INVALID
5. Se è stato escluso dal tracking (NOTRACK): classifica come UNTRACKED

### Metadati Conntrack Disponibili per Matching

nftables espone numerosi metadati conntrack per regole avanzate:

```bash
table inet stateful_advanced {
    chain input {
        type filter hook input priority 0; policy drop;

        # Match per stato (classico)
        ct state established,related accept
        ct state invalid drop

        # Match per direzione originale/reply
        ct direction original counter
        ct direction reply counter

        # Match per marca conntrack (per routing policy)
        ct mark 0x1 accept

        # Imposta marca conntrack
        ct state new tcp dport 80 ct mark set 0x1

        # Match per conteggio connessioni per IP
        tcp dport 22 ct state new \
            meter conn_count { ip saddr ct count over 5 } reject

        # Match per helper assegnato
        ct helper "ftp" accept

        # Match per etichetta conntrack (per SELinux/secmark)
        # ct label != 0 log prefix "labeled: "

        # Match per stato aspettato (expectation)
        ct status expected accept

        # Match per zona conntrack
        ct zone 1 accept
    }
}
```

### Stateful Inspection per Protocolli Complessi

```bash
# PPTP VPN: richiede helper GRE
table inet filter {
    ct helper pptp-helper {
        type "pptp" protocol tcp
    }

    chain input {
        type filter hook input priority 0; policy drop;
        ct state established,related accept

        # PPTP control channel
        tcp dport 1723 ct state new ct helper set "pptp-helper" accept

        # GRE (protocollo 47) — usato come tunneling da PPTP
        ip protocol gre accept
    }
}

# H.323 (videoconferenza legacy)
table inet filter {
    ct helper h323-helper {
        type "h323" protocol tcp
    }

    chain input {
        type filter hook input priority 0; policy drop;
        ct state established,related accept

        # H.323 signaling
        tcp dport 1720 ct state new ct helper set "h323-helper" accept
        # I canali media dinamici vengono tracciati come RELATED dall'helper
    }
}
```

### Conntrack Accounting e Byte Counter

```bash
# Abilita accounting conntrack
sysctl -w net.netfilter.nf_conntrack_acct=1

# Ora conntrack -L mostra anche byte/pacchetti per connessione:
# tcp      6 431900 ESTABLISHED src=10.0.0.5 dst=203.0.113.1 sport=54321 dport=443
#   packets=15234 bytes=1245678
#   src=203.0.113.1 dst=10.0.0.5 sport=443 dport=54321
#   packets=12456 bytes=98765432

# Utile per:
# - Identificare connessioni con traffico anomalo
# - Billing per volume di traffico
# - Forensics (quale connessione ha trasferito più dati)

# Query conntrack con filtri
conntrack -L --src 10.0.0.5 -p tcp --dport 443 -o extended
```

---

## Docker e Container Networking: Firewall Rules Avanzate

### Architettura del Networking Docker con nftables

A partire da Docker 29.0, è disponibile il backend nftables (sperimentale). L'architettura cambia significativamente:

```
┌────────────────────────────────────────────┐
│              Host Network Stack             │
├─────────────┬──────────────┬───────────────┤
│  docker0    │  br-custom   │  eth0 (WAN)   │
│  (bridge)   │  (user net)  │               │
│  172.17.0.1 │  172.18.0.1  │  203.0.113.1  │
└──────┬──────┴──────┬───────┴───────┬───────┘
       │             │               │
  ┌────┴────┐   ┌────┴────┐         │
  │veth-c1  │   │veth-c2  │    Netfilter/
  │container│   │container│    nftables
  │  :80    │   │  :3306  │    (firewall)
  └─────────┘   └─────────┘
```

### Configurazione Docker con Backend nftables

```bash
# /etc/docker/daemon.json
{
    "firewall-backend": "nftables",
    "iptables": true,
    "ip-forward": true,
    "ip6tables": true,
    "default-address-pools": [
        {"base": "172.17.0.0/12", "size": 24}
    ]
}

# Riavvia Docker
systemctl restart docker

# Verifica le tabelle nftables create da Docker
nft list tables
# table ip docker
# table ip6 docker
```

### Regole DOCKER-USER Equivalenti in nftables

Con il backend iptables, Docker crea la catena DOCKER-USER per le regole utente. Con nftables, la logica è simile ma organizzata in tabelle nft:

```bash
# Con backend iptables: regole nella catena DOCKER-USER
# Queste regole sopravvivono ai restart di Docker

# Protezione porta MySQL (esposta da Docker ma limitata)
iptables -I DOCKER-USER -i eth0 -p tcp --dport 3306 \
    -j DROP
iptables -I DOCKER-USER -i eth0 -p tcp --dport 3306 \
    -s 10.0.0.0/8 -j ACCEPT

# Con backend nftables (Docker 29+): tabella separata
table inet docker_user_rules {
    chain forward {
        type filter hook forward priority -1; policy accept;
        # Priorità -1: eseguita PRIMA delle regole Docker (priorità 0)

        # Blocca accesso diretto da internet a MySQL container
        iifname "eth0" tcp dport 3306 counter drop

        # Consenti MySQL solo dalla rete interna
        iifname "eth0" ip saddr 10.0.0.0/8 tcp dport 3306 counter accept

        # Blocca Redis da internet
        iifname "eth0" tcp dport 6379 counter drop
    }
}
```

### Best Practice: Container Networking Sicuro

```bash
# 1. NON esporre porte su 0.0.0.0
# docker-compose.yml:
# ports:
#   - "127.0.0.1:3306:3306"     # solo localhost
#   - "10.0.0.1:8080:80"        # solo dalla rete interna

# 2. Usare reti Docker isolate
# docker network create --internal isolated_net
# I container su --internal non hanno accesso a internet

# 3. Regole nftables per isolare reti Docker
table inet container_isolation {
    chain forward {
        type filter hook forward priority -5; policy accept;

        # Impedisci comunicazione tra reti Docker diverse
        # (a meno che non sia esplicitamente consentito)
        iifname "br-net1" oifname "br-net2" counter drop
        iifname "br-net2" oifname "br-net1" counter drop

        # Permetti solo traffico specifico tra frontend e backend
        iifname "br-frontend" oifname "br-backend" \
            tcp dport { 3306, 6379 } accept
        iifname "br-frontend" oifname "br-backend" drop
    }
}
```

### Kubernetes kube-proxy con nftables

A partire da Kubernetes 1.29, kube-proxy supporta il mode `nftables` (beta in 1.31+, GA previsto in 1.33):

```bash
# Configurazione kube-proxy per nftables mode
# /var/lib/kube-proxy/config.yaml (o via ConfigMap)
apiVersion: kubeproxy.config.k8s.io/v1alpha1
kind: KubeProxyConfiguration
mode: "nftables"
nftables:
  masqueradeAll: false
  masqueradeBit: 14
  syncPeriod: "30s"
  minSyncPeriod: "1s"
```

Vantaggi di kube-proxy in mode nftables rispetto a iptables:

- Performance O(1) per Service lookup (vs O(n) con iptables)
- Regole atomiche (nessuna finestra temporale senza regole durante sync)
- Supporto nativo per set (un set per tutti gli endpoint di un Service)
- Overhead significativamente ridotto in cluster con migliaia di Service

---

## Performance Tuning Avanzato

### Tabella raw e NOTRACK: Quando e Come

La tabella raw opera a priorità -300, prima del connection tracking (-200). Usare NOTRACK per traffico dove il tracking stateful non serve o è troppo costoso:

```bash
table inet raw {
    chain prerouting {
        type filter hook prerouting priority raw; policy accept;

        # Scenari dove NOTRACK è appropriato:

        # 1. DNS server ad alto volume
        udp dport 53 notrack
        tcp dport 53 notrack

        # 2. Server web CDN (migliaia di connessioni/s)
        #    SOLO se non serve stateful inspection
        # tcp dport { 80, 443 } notrack

        # 3. Traffico di monitoring/health check dalla rete interna
        ip saddr 10.0.0.0/8 tcp dport 9090 notrack

        # 4. Traffico multicast/broadcast
        ip daddr 224.0.0.0/4 notrack

        # 5. GRE tunnel (già incapsulato, tracking superfluo)
        ip protocol gre notrack
    }

    chain output {
        type filter hook output priority raw; policy accept;

        # Simmetrico al prerouting per le risposte
        udp sport 53 notrack
        tcp sport 53 notrack
        ip daddr 10.0.0.0/8 tcp sport 9090 notrack
    }
}
```

**Impatto prestazionale del NOTRACK:**

```
Benchmark: DNS resolver con 100k query/s

              Con conntrack    Con NOTRACK    Differenza
─────────────────────────────────────────────────────────
CPU usage        45%              18%          -60%
Latenza p50      0.8ms            0.3ms        -63%
Latenza p99      5.2ms            1.1ms        -79%
Conntrack mem    180MB            0MB          -100%
Max qps          120k             310k         +158%
```

### Ottimizzazione della Struttura del Ruleset

```bash
# REGOLA: le regole più matchate devono essere in cima alla catena

# MALE: ordine casuale
chain input_bad {
    type filter hook input priority 0; policy drop;
    tcp dport 25 accept          # 10 match/s
    tcp dport 3306 accept        # 5 match/s
    tcp dport { 80, 443 } accept # 50000 match/s  ← qui il 99.9% dei match
    ct state established accept  # 500000 match/s ← dovrebbe essere PRIMA
}

# BENE: ordine ottimizzato
chain input_good {
    type filter hook input priority 0; policy drop;
    ct state established,related accept  # Primo: cattura il grosso
    ct state invalid drop
    tcp dport { 80, 443 } accept         # Secondo: traffico web
    tcp dport 25 accept                  # Raro
    tcp dport 3306 accept                # Raro
}
```

### Uso Efficiente dei Set per Ridurre Regole

```bash
# MALE: una regola per IP (O(n) nel worst case con iptables)
# iptables -A INPUT -s 1.2.3.4 -j DROP
# iptables -A INPUT -s 5.6.7.8 -j DROP
# ... × 10000 regole

# BENE: un set con lookup O(1)
table inet filter {
    set blocklist {
        type ipv4_addr
        flags interval
        # 10000 IP → stesso tempo di lookup di 1 IP
    }

    chain input {
        type filter hook input priority 0; policy drop;
        ip saddr @blocklist counter drop
    }
}
```

### Profiling del Ruleset

```bash
# Identifica regole che non matchano mai (regole morte)
nft list ruleset | grep 'counter packets 0'

# Identifica regole con alto conteggio (candidati per ottimizzazione)
nft list ruleset -a | grep counter | sort -t'=' -k2 -rn | head -20

# Misura il tempo di elaborazione per pacchetto
perf stat -e cycles -a -- timeout 10 cat /dev/null
# Confronta con/senza regole per misurare l'overhead

# Verifica la dimensione del ruleset compilato
nft -j list ruleset | wc -c
# Ruleset troppo grandi impattano il tempo di caricamento atomico
```

---

## Scenari di Produzione Completi

### Scenario 1: Web Server Hardened con WAF Integration

```bash
#!/usr/sbin/nft -f
# Firewall per web server in produzione con proxy WAF upstream

flush ruleset

define WAN_IF = eth0
define MGMT_IF = eth1
define MGMT_NET = 10.0.0.0/8

table inet production {
    set geo_block {
        type ipv4_addr
        flags interval
        # Popolato da script geo-ip esterno
    }

    set auto_ban {
        type ipv4_addr
        flags dynamic, timeout
        timeout 2h
        size 131072
    }

    set rate_limited_ips {
        type ipv4_addr
        flags dynamic, timeout
        timeout 10m
    }

    chain input {
        type filter hook input priority 0; policy drop;

        # ── Fast path ──
        ct state established,related accept
        ct state invalid counter drop
        iif "lo" accept

        # ── Blacklist ──
        ip saddr @geo_block counter drop
        ip saddr @auto_ban counter drop

        # ── Management ──
        iifname $MGMT_IF ip saddr $MGMT_NET tcp dport 22 accept

        # ── ICMPv4 ──
        ip protocol icmp limit rate 10/second burst 20 packets accept

        # ── ICMPv6 ──
        icmpv6 type {
            destination-unreachable, packet-too-big,
            time-exceeded, parameter-problem,
            nd-router-advert, nd-neighbor-solicit,
            nd-neighbor-advert, echo-request,
        } accept

        # ── HTTP/HTTPS con rate limiting ──
        tcp dport { 80, 443 } ct state new \
            meter http_rate { ip saddr limit rate over 100/second burst 200 packets } \
            add @auto_ban { ip saddr timeout 1h } \
            counter drop

        tcp dport { 80, 443 } accept

        # ── Monitoring (solo management) ──
        iifname $MGMT_IF tcp dport { 9090, 9100 } accept

        # ── Logging ──
        limit rate 10/minute log prefix "prod-drop: " group 1
        counter comment "total drops"
    }

    chain output {
        type filter hook output priority 0; policy accept;
        # In produzione: considerare policy DROP anche in output
        # per limitare l'exfiltration di dati
    }
}
```

### Scenario 2: Gateway Multi-WAN con Failover

```bash
#!/usr/sbin/nft -f
# Gateway con due connessioni WAN e failover

flush ruleset

define WAN1 = eth0
define WAN2 = eth1
define LAN = eth2
define LAN_NET = 192.168.0.0/16

table inet gateway {
    flowtable ft {
        hook ingress priority 0
        devices = { eth0, eth1, eth2 }
    }

    chain input {
        type filter hook input priority 0; policy drop;
        ct state established,related accept
        ct state invalid drop
        iif "lo" accept

        # Management SSH solo dalla LAN
        iifname $LAN tcp dport 22 accept

        # DHCP server sulla LAN
        iifname $LAN udp dport { 67, 68 } accept

        # DNS locale
        iifname $LAN tcp dport 53 accept
        iifname $LAN udp dport 53 accept

        # ICMP per diagnostica
        ip protocol icmp accept
        icmpv6 type {
            destination-unreachable, packet-too-big,
            nd-neighbor-solicit, nd-neighbor-advert,
        } accept
    }

    chain forward {
        type filter hook forward priority 0; policy drop;

        # Fast path per connessioni stabilite
        ct state established flow add @ft counter accept
        ct state related accept
        ct state invalid drop

        # LAN → WAN (qualsiasi)
        iifname $LAN oifname { $WAN1, $WAN2 } accept

        # Drop WAN → LAN non sollecitato
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}

table ip nat {
    chain postrouting {
        type nat hook postrouting priority srcnat; policy accept;

        # Masquerade su entrambe le WAN
        oifname $WAN1 masquerade
        oifname $WAN2 masquerade
    }
}

# Il failover WAN è gestito a livello di routing (ip route)
# con metric diverse e script di health check
```

---

## Esercizi Avanzati Aggiuntivi

### Esercizio 5 — Mitigazione DDoS Multi-Livello

Progetta un sistema di mitigazione DDoS a tre livelli:
1. **Ingress (netdev)**: drop di pacchetti con flag TCP invalidi, rate limit globale a 100k pps
2. **Raw (NOTRACK)**: bypass conntrack per traffico DNS ad alto volume
3. **Filter (meter)**: rate limiting per-sorgente per HTTP (50 conn/s), SSH (3/min), auto-ban in set con timeout 1h

Requisiti:
- Counter con nome su ogni livello per monitoraggio
- Set threat_intel popolato da script esterno
- Logging NFLOG verso ulogd2 per i pacchetti droppati
- Valida con `nft -c -f`

### Esercizio 6 — Firewall Container con Micro-Segmentazione

Configura un ambiente Docker con tre reti:
- `frontend` (172.18.0.0/24): container web, esposti su porta 443
- `backend` (172.19.0.0/24): container API
- `data` (172.20.0.0/24): container database (PostgreSQL, Redis)

Regole nftables:
- frontend può parlare solo con backend (porte 8080, 8443)
- backend può parlare solo con data (porte 5432, 6379)
- frontend NON può parlare direttamente con data
- Nessun container può avviare connessioni verso internet (solo risposte a richieste in entrata)
- Logging di ogni tentativo di violazione della segmentazione

### Esercizio 7 — Configurazione Completa fail2ban + nftables + firewalld

Su un server CentOS/RHEL con firewalld:
1. Configura firewalld con zone `public`, `internal`, `dmz`
2. Assegna le interfacce: `eth0`→public, `eth1`→internal, `eth2`→dmz
3. Aggiungi servizi alle zone appropriate
4. Configura fail2ban con backend `nftables-multiport` per SSH, nginx, postfix
5. Aggiungi jail `recidive` per ban prolungati dei recidivi
6. Verifica che fail2ban e firewalld non conflittuino
7. Testa simulando un brute force SSH e verifica il ban nel set nftables

### Esercizio 8 — IPv6 Dual-Stack con Privacy Extensions

Configura un firewall nftables dual-stack (famiglia inet) per un server che:
- Usa IPv6 con Privacy Extensions (indirizzi temporanei)
- Accetta HTTP/HTTPS su entrambi i protocolli
- Accetta SSH solo da rete management IPv4 e prefisso IPv6 specifico
- Gestisce correttamente tutti i tipi ICMPv6 necessari (NDP, MLD, PMTUD)
- Rate limiting separato per IPv4 e IPv6
- Logging differenziato (prefisso diverso per v4 e v6)

---

## Auto-valutazione Avanzata

8. **Qual è la differenza tra un set anonimo e un set con nome in nftables?**
   <details><summary>Risposta</summary>
   Un set anonimo è definito inline nella regola (es. `tcp dport { 80, 443 }`) ed è immutabile — non può essere modificato dopo la creazione se non riscrivendo la regola. Un set con nome è dichiarato nella tabella con un identificatore (es. `set web_ports { type inet_service; elements = { 80, 443 }; }`) e referenziato con `@web_ports`. I set con nome possono essere modificati dinamicamente da CLI (`nft add/delete element`) e possono avere flag come `dynamic`, `timeout`, `interval`. Per regole statiche un set anonimo è sufficiente; per gestione dinamica (blacklist, rate limiting) servono set con nome.
   </details>

9. **Quando è appropriato usare NOTRACK e quali sono i rischi?**
   <details><summary>Risposta</summary>
   NOTRACK è appropriato per: (1) traffico ad altissimo volume dove il conntrack diventa collo di bottiglia (DNS resolver, CDN), (2) traffico intrinsecamente stateless (UDP broadcast/multicast), (3) traffico di monitoring/health check dalla rete fidata. I rischi sono: (a) perdi la protezione stateful — non puoi usare `ct state established,related accept`, (b) ogni pacchetto deve essere accettato/rifiutato individualmente, (c) NAT non funziona senza conntrack, (d) i conntrack helper (FTP, SIP) non operano, (e) devi gestire esplicitamente il traffico UNTRACKED nelle regole filter.
   </details>

10. **Come funziona il flowtable con offload hardware? Quali NIC lo supportano?**
    <details><summary>Risposta</summary>
    Il flowtable con flag `offload` usa TC flower per scaricare il forwarding dei pacchetti direttamente sulla NIC. La NIC esegue il forwarding in hardware senza coinvolgere la CPU del server. Richiede: (1) kernel 5.13+, (2) driver NIC con supporto `hw-tc-offload` (verificabile con `ethtool -k eth0 | grep hw-tc-offload`), (3) NIC compatibili: Mellanox ConnectX-5+, Broadcom NetXtreme-E, Intel E810, Netronome NFP. Il throughput può superare i 40Gbps con latenza sub-microsecondo. Limitazione: non è possibile applicare mangling, logging o deep inspection sui pacchetti offloadati.
    </details>

11. **Come si configura fail2ban per usare nftables come backend?**
    <details><summary>Risposta</summary>
    In `/etc/fail2ban/jail.local`: impostare `banaction = nftables-multiport` per ban su porte specifiche o `banaction = nftables-allports` per ban su tutte le porte, nella sezione `[DEFAULT]`. Fail2ban crea automaticamente una tabella nftables dedicata (es. `f2b-sshd`) con un set di tipo `ipv4_addr` e una regola che droppa/rejecta il traffico da IP nel set. Quando banna, aggiunge l'IP al set con timeout. Verificare con `nft list ruleset | grep f2b`. Per il jail recidive (che banna i recidivi), usare `banaction = nftables-allports` per bloccare tutto il traffico dall'IP recidivo.
    </details>

12. **Perché Docker bypassa le regole INPUT e come proteggersi?**
    <details><summary>Risposta</summary>
    Docker usa DNAT nella catena PREROUTING (tabella nat) per redirigere traffico ai container. Il pacchetto modificato viene classificato come FORWARD dopo il routing decision, quindi le regole INPUT non lo vedono mai. Protezioni: (1) usare la catena DOCKER-USER (iptables) o una catena forward con priorità -1 (nftables) per filtrare il traffico verso i container, (2) non pubblicare porte su `0.0.0.0` ma solo su `127.0.0.1` o IP specifici, (3) usare reti Docker `--internal` per container che non devono accedere a internet, (4) con Docker 29+ e backend nftables, le regole sono più trasparenti e prevedibili. (5) Non disabilitare `"iptables": false` nel daemon.json a meno che non si gestisca manualmente tutto il networking.
    </details>

13. **Qual è il vantaggio di NFLOG rispetto al LOG target standard?**
    <details><summary>Risposta</summary>
    LOG scrive nel kernel ring buffer (dmesg), mescolando i log firewall con tutti gli altri messaggi kernel. Con alto volume, satura il buffer e rallenta il kernel. NFLOG invia i pacchetti via netlink a un daemon userspace (ulogd2) che può: (1) scrivere in file dedicati, (2) emettere formato JSON strutturato per Loki/ELK, (3) catturare in formato PCAP per analisi con Wireshark, (4) inviare a database (MySQL, PostgreSQL), (5) operare senza impattare il kernel log. NFLOG è la scelta obbligata per qualsiasi ambiente di produzione con volume di log significativo.
    </details>

14. **Come si gestisce la persistenza delle regole nftables con systemd?**
    <details><summary>Risposta</summary>
    Il servizio `nftables.service` è di tipo `oneshot` con `RemainAfterExit=yes`. All'avvio esegue `nft -f /etc/nftables.conf` (il percorso varia per distribuzione). Il workflow è: (1) modificare `/etc/nftables.conf`, (2) validare con `nft -c -f /etc/nftables.conf`, (3) applicare con `systemctl reload nftables`, (4) abilitare con `systemctl enable nftables` per persistenza al boot. Il servizio ha `Before=network-pre.target` per garantire che il firewall sia attivo prima delle interfacce di rete. Per configurazioni complesse, usare `include` per suddividere in file modulari sotto `/etc/nftables.d/`.
    </details>
