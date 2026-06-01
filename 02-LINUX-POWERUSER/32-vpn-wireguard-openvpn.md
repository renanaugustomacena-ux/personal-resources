# VPN: WireGuard e OpenVPN — Guida Approfondita

> **Modulo del corso:** Linux per ingegneri di sistema
> **Posizione nel percorso:** [00-SYLLABUS.md](00-SYLLABUS.md) → Modulo 32
> **Prerequisiti:** [05-networking.md](05-networking.md), [24-iptables-nftables-guida-completa.md](24-iptables-nftables-guida-completa.md), [11-sicurezza.md](11-sicurezza.md)
> **Obiettivi di apprendimento:**
> 1. Configurare tunnel WireGuard e OpenVPN per scenari road-warrior e site-to-site
> 2. Progettare una PKI con Easy-RSA e gestire il ciclo di vita dei certificati
> 3. Applicare il threat model VPN: identificare ciò che una VPN protegge e ciò che non protegge
> 4. Implementare split tunneling con policy routing e nftables
> 5. Configurare alta disponibilità VPN con failover automatico
> 6. Integrare Tailscale/Headscale come overlay mesh su WireGuard
> **Tempo stimato:** lettura 90 min · lab 180 min
> **Livello:** competent → proficient
> **Ultimo aggiornamento:** 2026-05-23
> **Versioni di riferimento:** WireGuard (kernel 6.1+), OpenVPN 2.6.x, Easy-RSA 3.2.x, Tailscale 1.76+

## Mappa concettuale

```
                        ┌─────────────────┐
                        │   VPN su Linux  │
                        └────────┬────────┘
               ┌─────────────┬──┴──┬──────────────┐
               ▼             ▼     ▼              ▼
        ┌──────────┐  ┌──────────┐ ┌─────────┐ ┌────────────┐
        │WireGuard │  │ OpenVPN  │ │Tailscale│ │ IPsec/     │
        │(kernel)  │  │(userspace│ │Headscale│ │ strongSwan │
        └────┬─────┘  └────┬─────┘ └────┬────┘ └────────────┘
             │              │            │
     ┌───────┼────┐   ┌────┼─────┐  ┌───┼────┐
     ▼       ▼    ▼   ▼    ▼     ▼  ▼   ▼    ▼
  Noise    PSK  Crypto  TLS  PKI  CRL DERP  ACL
  Protocol      key    1.3  X.509     relay  mesh
  IK            routing
```

> **Modulo 32** · **Aggiornamento:** 2026-05-23

## Idee guida
1. **WireGuard > OpenVPN per nuovi setup.** Faster, simpler, kernel-native.
2. **Tailscale wraps WireGuard con discovery + key mgmt.**
3. **OpenVPN legacy ma compatible piu firewall.**
4. **mTLS per VPN client auth oltre PSK.**


## Indice

- [Panoramica](#panoramica)
- [Fondamenti VPN](#fondamenti-vpn)
- [WireGuard: Architettura](#wireguard-architettura)
- [WireGuard: Installazione e Configurazione](#wireguard-installazione-e-configurazione)
- [WireGuard: Scenari Avanzati](#wireguard-scenari-avanzati)
- [OpenVPN: Architettura](#openvpn-architettura)
- [OpenVPN: Setup Server](#openvpn-setup-server)
- [OpenVPN: Certificati con Easy-RSA](#openvpn-certificati-con-easy-rsa)
- [OpenVPN: Setup Client](#openvpn-setup-client)
- [OpenVPN: Configurazione Avanzata](#openvpn-configurazione-avanzata)
- [Site-to-Site vs Road Warrior](#site-to-site-vs-road-warrior)
- [Confronto WireGuard vs OpenVPN](#confronto-wireguard-vs-openvpn)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Riferimenti](#riferimenti)
- [WireGuard: Internals del Modulo Kernel](#wireguard-internals-del-modulo-kernel)
- [wg-quick: Configurazione Avanzata](#wg-quick-configurazione-avanzata)
- [Topologie Multi-Peer](#topologie-multi-peer)
- [WireGuard over TCP: udp2raw e wstunnel](#wireguard-over-tcp-udp2raw-e-wstunnel)
- [OpenVPN: tls-crypt-v2 (Chiavi Per-Client)](#openvpn-tls-crypt-v2-chiavi-per-client)
- [OpenVPN Access Server](#openvpn-access-server)
- [VPN Performance Benchmarking](#vpn-performance-benchmarking)
- [DNS Leak Prevention Avanzata](#dns-leak-prevention-avanzata)
- [Kill Switch: Implementazione Completa](#kill-switch-implementazione-completa)
- [IPv6 over VPN: Approfondimento](#ipv6-over-vpn-approfondimento)
- [Rotazione Automatizzata delle Chiavi](#rotazione-automatizzata-delle-chiavi)
- [Monitoring VPN con Prometheus e Grafana](#monitoring-vpn-con-prometheus-e-grafana)
- [Client Mobili: iOS e Android](#client-mobili-ios-e-android)
- [Confronto IPsec/IKEv2 vs WireGuard](#confronto-ipsecikev2-vs-wireguard)

---

## Panoramica

Una VPN (Virtual Private Network) crea un tunnel cifrato tra due o più punti di una rete, permettendo comunicazioni sicure su infrastrutture non fidate come internet. Per un system administrator Linux, la VPN è uno strumento fondamentale per tre scenari principali: accesso remoto sicuro ai server (road warrior), interconnessione di sedi geograficamente distribuite (site-to-site) e protezione del traffico degli utenti.

WireGuard e OpenVPN sono le due soluzioni VPN open source dominanti su Linux, con filosofie radicalmente diverse. WireGuard, incluso nel kernel Linux dal 5.6 (2020), è minimalista: circa 4.000 righe di codice, una singola cipher suite (Curve25519, ChaCha20, Poly1305, BLAKE2s) e un modello di configurazione basato su chiavi pubbliche senza PKI. OpenVPN, maturo e consolidato da oltre 20 anni, opera in userspace, supporta molteplici configurazioni crittografiche, si basa su un'infrastruttura PKI (Public Key Infrastructure) con certificati X.509 e offre flessibilità estrema a costo di complessità.

Questo documento copre la configurazione completa di entrambe le soluzioni per scenari reali, dalla generazione delle chiavi alla configurazione dei client, dal NAT traversal al routing avanzato. L'obiettivo è fornire le competenze per scegliere la soluzione giusta per ogni scenario e configurarla in modo sicuro e operativo.

---

## Fondamenti VPN

### Topologie VPN

```
Road Warrior (client-to-site):
┌──────────┐                    ┌──────────────┐
│ Laptop   │───── Internet ─────│ VPN Server   │───── Rete aziendale
│ (client) │     (tunnel VPN)   │              │     10.0.0.0/24
└──────────┘                    └──────────────┘

Site-to-Site:
┌──────────────┐                    ┌──────────────┐
│ Sede A       │                    │ Sede B       │
│ 10.1.0.0/24  │───── Internet ─────│ 10.2.0.0/24  │
│ VPN Gateway  │     (tunnel VPN)   │ VPN Gateway  │
└──────────────┘                    └──────────────┘

Mesh (peer-to-peer):
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Nodo A   │─────│ Nodo B   │─────│ Nodo C   │
│          │     │          │     │          │
└──────────┘     └──────────┘     └──────────┘
     └──────────────────────────────────┘
```

### Encapsulation

```
┌─────────────────────────────────────────────┐
│ Pacchetto originale:                        │
│ [IP Header (src:10.0.0.5 dst:10.0.0.100)]  │
│ [TCP Header (port 443)]                     │
│ [Dati applicativi]                          │
└─────────────────────────────────────────────┘
                    ↓ encapsulation VPN
┌─────────────────────────────────────────────────────────┐
│ Pacchetto VPN:                                          │
│ [IP Header (src:203.0.113.1 dst:198.51.100.1)]         │
│ [UDP Header (port 51820)]                               │
│ [VPN Header + crittografia]                             │
│   [IP Header (src:10.0.0.5 dst:10.0.0.100)] ← cifrato│
│   [TCP Header (port 443)]                    ← cifrato│
│   [Dati applicativi]                         ← cifrato│
└─────────────────────────────────────────────────────────┘
```

---

## WireGuard: Architettura

WireGuard opera a livello kernel come interfaccia di rete virtuale. La sua architettura è radicalmente semplice:

- **Nessun concetto di server/client**: solo peer che comunicano tra loro
- **Cryptokey routing**: ogni peer ha una chiave pubblica e un set di IP consentiti
- **Nessuna negoziazione**: la cipher suite è fissa (non configurabile)
- **Silenzio**: non risponde a pacchetti non autenticati (stealth)
- **Roaming**: supporta cambio di IP/rete senza riconnessione

### Algoritmi Crittografici

| Funzione | Algoritmo |
|----------|-----------|
| Key exchange | Curve25519 (ECDH) |
| Cifratura simmetrica | ChaCha20 |
| MAC | Poly1305 |
| Hashing | BLAKE2s |
| Key derivation | HKDF |

### Handshake

Il Noise Protocol Framework (variante IK) stabilisce una sessione in un solo round-trip (1-RTT):

```
Initiator → Responder: ephemeral_public, encrypted(static_public), encrypted(timestamp)
Responder → Initiator: ephemeral_public, encrypted(empty)
```

Dopo l'handshake, i dati viaggiano cifrati con ChaCha20-Poly1305. L'handshake viene ripetuto ogni 2 minuti per perfect forward secrecy.

---

## WireGuard: Installazione e Configurazione

### Installazione

```bash
# Ubuntu/Debian (kernel 5.6+ ha WireGuard built-in)
sudo apt install wireguard wireguard-tools

# RHEL/CentOS
sudo dnf install wireguard-tools

# Verifica modulo kernel
modprobe wireguard
lsmod | grep wireguard
```

### Generazione Chiavi

```bash
# Genera coppia di chiavi (private + public)
wg genkey | tee /etc/wireguard/server_private.key | wg pubkey > /etc/wireguard/server_public.key

# Imposta permessi stretti sulla chiave privata
chmod 600 /etc/wireguard/server_private.key

# Genera preshared key (opzionale, per post-quantum resistance)
wg genpsk > /etc/wireguard/psk.key
chmod 600 /etc/wireguard/psk.key

# Genera chiavi per ogni client
wg genkey | tee /etc/wireguard/client1_private.key | wg pubkey > /etc/wireguard/client1_public.key
```

### Configurazione Server

```ini
# /etc/wireguard/wg0.conf — Server VPN

[Interface]
# Indirizzo IP dell'interfaccia WireGuard
Address = 10.10.0.1/24

# Porta UDP in ascolto
ListenPort = 51820

# Chiave privata del server
PrivateKey = <contenuto di server_private.key>

# Comandi post-up e post-down per NAT/firewall
PostUp = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT
PostUp = iptables -A FORWARD -o wg0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT
PostDown = iptables -D FORWARD -o wg0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# Salva configurazione automaticamente
SaveConfig = false

# ── Peer: Client 1 (laptop di Alice) ────────────
[Peer]
# Chiave pubblica del client
PublicKey = <contenuto di client1_public.key>

# Preshared key (opzionale)
PresharedKey = <contenuto di psk.key>

# IP consentiti per questo peer (cryptokey routing)
AllowedIPs = 10.10.0.2/32

# ── Peer: Client 2 (telefono di Bob) ────────────
[Peer]
PublicKey = <chiave_pubblica_client2>
AllowedIPs = 10.10.0.3/32

# ── Peer: Site-to-site con ufficio remoto ────────
[Peer]
PublicKey = <chiave_pubblica_ufficio>
AllowedIPs = 10.10.0.4/32, 192.168.10.0/24
# 192.168.10.0/24 = rete dietro il gateway dell'ufficio remoto
Endpoint = office.example.com:51820
PersistentKeepalive = 25
```

### Configurazione Client

```ini
# /etc/wireguard/wg0.conf — Client (laptop)

[Interface]
Address = 10.10.0.2/24
PrivateKey = <contenuto di client1_private.key>

# DNS (opzionale, utile per road warrior)
DNS = 1.1.1.1, 8.8.8.8

[Peer]
PublicKey = <chiave_pubblica_del_server>
PresharedKey = <contenuto di psk.key>
Endpoint = vpn.example.com:51820

# Split tunnel: solo traffico per la rete VPN
AllowedIPs = 10.10.0.0/24

# Full tunnel: tutto il traffico passa per la VPN
# AllowedIPs = 0.0.0.0/0, ::/0

# Keepalive per NAT traversal
PersistentKeepalive = 25
```

### Gestione con wg-quick

```bash
# Avvia l'interfaccia
wg-quick up wg0

# Ferma l'interfaccia
wg-quick down wg0

# Abilita al boot
systemctl enable wg-quick@wg0

# Stato dettagliato
wg show
wg show wg0

# Output esempio:
# interface: wg0
#   public key: xxxxx
#   private key: (hidden)
#   listening port: 51820
#
# peer: yyyyy
#   endpoint: 203.0.113.50:34567
#   allowed ips: 10.10.0.2/32
#   latest handshake: 34 seconds ago
#   transfer: 5.67 GiB received, 1.23 GiB sent
```

### Gestione Dinamica dei Peer

```bash
# Aggiungi peer senza riavviare
wg set wg0 peer <chiave_pubblica> allowed-ips 10.10.0.5/32

# Rimuovi peer
wg set wg0 peer <chiave_pubblica> remove

# Visualizza configurazione corrente
wg showconf wg0
```

### Prerequisiti Rete

```bash
# Abilita IP forwarding
echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.d/99-wireguard.conf
echo "net.ipv6.conf.all.forwarding = 1" >> /etc/sysctl.d/99-wireguard.conf
sysctl -p /etc/sysctl.d/99-wireguard.conf

# Apri porta UDP nel firewall
ufw allow 51820/udp
# oppure
iptables -A INPUT -p udp --dport 51820 -j ACCEPT
```

---

## WireGuard: Scenari Avanzati

### NAT Traversal

WireGuard gestisce il NAT traversal tramite `PersistentKeepalive`:

```ini
[Peer]
PublicKey = <chiave>
AllowedIPs = 10.10.0.2/32
# Invia un pacchetto keepalive ogni 25 secondi
# Questo mantiene aperta la mappatura NAT sul router
PersistentKeepalive = 25
```

Scenario: il client è dietro un NAT (router domestico, rete aziendale). Senza keepalive, il mapping NAT scade dopo un periodo di inattività e il server non può più raggiungere il client. Con `PersistentKeepalive = 25`, il client invia un pacchetto ogni 25 secondi, mantenendo il mapping attivo.

### Site-to-Site con WireGuard

```
Sede A (10.1.0.0/24)              Sede B (10.2.0.0/24)
┌──────────────────┐              ┌──────────────────┐
│ GW-A (10.1.0.1)  │── tunnel ───│ GW-B (10.2.0.1)  │
│ wg0: 10.10.0.1   │  WireGuard  │ wg0: 10.10.0.2   │
└──────────────────┘              └──────────────────┘
```

```ini
# GW-A: /etc/wireguard/wg0.conf
[Interface]
Address = 10.10.0.1/24
ListenPort = 51820
PrivateKey = <chiave_privata_GW_A>
PostUp = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]
PublicKey = <chiave_pubblica_GW_B>
Endpoint = gw-b.example.com:51820
AllowedIPs = 10.10.0.2/32, 10.2.0.0/24
PersistentKeepalive = 25
```

```ini
# GW-B: /etc/wireguard/wg0.conf
[Interface]
Address = 10.10.0.2/24
ListenPort = 51820
PrivateKey = <chiave_privata_GW_B>
PostUp = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]
PublicKey = <chiave_pubblica_GW_A>
Endpoint = gw-a.example.com:51820
AllowedIPs = 10.10.0.1/32, 10.1.0.0/24
PersistentKeepalive = 25
```

```bash
# Routing sui gateway (se non gestito da PostUp)
# Su GW-A:
ip route add 10.2.0.0/24 via 10.10.0.2 dev wg0
# Su GW-B:
ip route add 10.1.0.0/24 via 10.10.0.1 dev wg0
```

### Script di Provisioning Client

```bash
#!/bin/bash
# wg-add-client.sh — Aggiunge un nuovo client WireGuard

set -euo pipefail

CLIENT_NAME="${1:?Uso: $0 <nome_client>}"
SERVER_PUBLIC_KEY=$(cat /etc/wireguard/server_public.key)
SERVER_ENDPOINT="vpn.example.com:51820"
VPN_SUBNET="10.10.0"

# Trova il prossimo IP disponibile
LAST_IP=$(grep -oP 'AllowedIPs = 10\.10\.0\.\K[0-9]+' /etc/wireguard/wg0.conf | sort -n | tail -1)
NEXT_IP=$(( LAST_IP + 1 ))

if (( NEXT_IP > 254 )); then
    echo "Errore: subnet piena" >&2
    exit 1
fi

CLIENT_IP="${VPN_SUBNET}.${NEXT_IP}"

# Genera chiavi
CLIENT_PRIVATE=$(wg genkey)
CLIENT_PUBLIC=$(echo "$CLIENT_PRIVATE" | wg pubkey)
PSK=$(wg genpsk)

# Aggiungi peer alla configurazione del server
cat >> /etc/wireguard/wg0.conf <<EOF

# ${CLIENT_NAME} — aggiunto $(date +%Y-%m-%d)
[Peer]
PublicKey = ${CLIENT_PUBLIC}
PresharedKey = ${PSK}
AllowedIPs = ${CLIENT_IP}/32
EOF

# Ricarica WireGuard
wg syncconf wg0 <(wg-quick strip wg0)

# Genera configurazione client
CLIENT_CONF="/etc/wireguard/clients/${CLIENT_NAME}.conf"
mkdir -p /etc/wireguard/clients

cat > "$CLIENT_CONF" <<EOF
[Interface]
Address = ${CLIENT_IP}/24
PrivateKey = ${CLIENT_PRIVATE}
DNS = 1.1.1.1

[Peer]
PublicKey = ${SERVER_PUBLIC_KEY}
PresharedKey = ${PSK}
Endpoint = ${SERVER_ENDPOINT}
AllowedIPs = 10.10.0.0/24
PersistentKeepalive = 25
EOF

chmod 600 "$CLIENT_CONF"

echo "Client '${CLIENT_NAME}' creato:"
echo "  IP: ${CLIENT_IP}"
echo "  Config: ${CLIENT_CONF}"
echo ""
echo "Per generare QR code (mobile):"
echo "  qrencode -t ansiutf8 < ${CLIENT_CONF}"
```

---

## OpenVPN: Architettura

OpenVPN opera in userspace utilizzando il driver TUN/TAP del kernel. Supporta due modalità:

- **TUN (tunnel)**: opera a livello 3 (IP), crea un tunnel routed. Il più comune.
- **TAP (bridge)**: opera a livello 2 (Ethernet), crea un bridge. Necessario per protocolli non-IP.

### Crittografia

OpenVPN utilizza OpenSSL per la crittografia e supporta:
- **Data channel**: AES-256-GCM (raccomandato), AES-128-GCM, ChaCha20-Poly1305
- **Control channel**: TLS 1.2/1.3 con certificati X.509
- **HMAC authentication**: SHA-256 o SHA-512
- **tls-auth / tls-crypt**: HMAC per prevenire DoS e fingerprinting

---

## OpenVPN: Setup Server

### Installazione

```bash
sudo apt install openvpn easy-rsa
```

### Configurazione Server

```conf
# /etc/openvpn/server/server.conf

# Modalità e protocollo
port 1194
proto udp
dev tun

# Certificati e chiavi
ca /etc/openvpn/server/pki/ca.crt
cert /etc/openvpn/server/pki/issued/server.crt
key /etc/openvpn/server/pki/private/server.key
dh /etc/openvpn/server/pki/dh.pem
tls-crypt /etc/openvpn/server/pki/ta.key

# Rete VPN
server 10.8.0.0 255.255.255.0
# Mantieni associazione client-IP
ifconfig-pool-persist /var/log/openvpn/ipp.txt

# Routing
# Instrada traffico per la rete interna
push "route 10.0.0.0 255.255.0.0"

# DNS push
push "dhcp-option DNS 1.1.1.1"
push "dhcp-option DNS 8.8.8.8"

# Full tunnel (redirect tutto il traffico)
# push "redirect-gateway def1 bypass-dhcp"

# Connessioni e performance
keepalive 10 120
max-clients 100

# Crittografia
cipher AES-256-GCM
auth SHA256
tls-version-min 1.2
tls-cipher TLS-ECDHE-RSA-WITH-AES-256-GCM-SHA384:TLS-ECDHE-ECDSA-WITH-AES-256-GCM-SHA384

# Compressione (disabilitata per sicurezza — VORACLE attack)
compress

# Privilegi
user nobody
group nogroup
persist-key
persist-tun

# Logging
status /var/log/openvpn/status.log 10
log-append /var/log/openvpn/server.log
verb 3
mute 20

# Client-specific config directory
client-config-dir /etc/openvpn/ccd

# Revocation list
crl-verify /etc/openvpn/server/pki/crl.pem
```

---

## OpenVPN: Certificati con Easy-RSA

Easy-RSA è lo strumento ufficiale per gestire la PKI necessaria a OpenVPN.

### Setup PKI

```bash
# Inizializza PKI
cd /etc/openvpn/server
make-cadir pki-setup
cd pki-setup

# Configura vars
cat > vars <<'EOF'
set_var EASYRSA_REQ_COUNTRY    "IT"
set_var EASYRSA_REQ_PROVINCE   "Lombardia"
set_var EASYRSA_REQ_CITY       "Milano"
set_var EASYRSA_REQ_ORG        "MyOrg"
set_var EASYRSA_REQ_EMAIL      "admin@example.com"
set_var EASYRSA_REQ_OU         "Infrastructure"
set_var EASYRSA_KEY_SIZE       4096
set_var EASYRSA_CA_EXPIRE      3650    # 10 anni
set_var EASYRSA_CERT_EXPIRE    365     # 1 anno
set_var EASYRSA_CRL_DAYS       180
set_var EASYRSA_ALGO           ec
set_var EASYRSA_CURVE          secp384r1
EOF

# Inizializza
./easyrsa init-pki

# Crea CA (Certificate Authority)
./easyrsa build-ca nopass
# Common Name: MyOrg CA

# Genera certificato server
./easyrsa gen-req server nopass
./easyrsa sign-req server server

# Genera parametri DH (Diffie-Hellman)
./easyrsa gen-dh

# Genera tls-crypt key (anti-DoS)
openvpn --genkey secret /etc/openvpn/server/pki/ta.key

# Genera CRL iniziale
./easyrsa gen-crl

# Copia i file necessari
cp pki/ca.crt /etc/openvpn/server/pki/
cp pki/issued/server.crt /etc/openvpn/server/pki/issued/
cp pki/private/server.key /etc/openvpn/server/pki/private/
cp pki/dh.pem /etc/openvpn/server/pki/
cp pki/crl.pem /etc/openvpn/server/pki/
```

### Creazione Certificati Client

```bash
cd /etc/openvpn/server/pki-setup

# Genera richiesta e firma per un client
./easyrsa gen-req client1 nopass
./easyrsa sign-req client client1

# Per revocare un certificato
./easyrsa revoke client1
./easyrsa gen-crl
cp pki/crl.pem /etc/openvpn/server/pki/
# Reload OpenVPN per applicare la nuova CRL
systemctl restart openvpn-server@server
```

### Script di Generazione Client Config

```bash
#!/bin/bash
# gen-client-config.sh — Genera file .ovpn completo per un client

set -euo pipefail

CLIENT="${1:?Uso: $0 <nome_client>}"
PKI_DIR="/etc/openvpn/server/pki-setup"
OUTPUT_DIR="/etc/openvpn/clients"
SERVER_ADDR="vpn.example.com"
SERVER_PORT="1194"

mkdir -p "$OUTPUT_DIR"

# Genera certificato se non esiste
if [[ ! -f "${PKI_DIR}/pki/issued/${CLIENT}.crt" ]]; then
    cd "$PKI_DIR"
    ./easyrsa gen-req "$CLIENT" nopass
    ./easyrsa sign-req client "$CLIENT"
fi

# Genera file .ovpn inline (tutto-in-uno)
cat > "${OUTPUT_DIR}/${CLIENT}.ovpn" <<EOF
client
dev tun
proto udp
remote ${SERVER_ADDR} ${SERVER_PORT}
resolv-retry infinite
nobind
persist-key
persist-tun

remote-cert-tls server

cipher AES-256-GCM
auth SHA256
verb 3

# Compressione (deve corrispondere al server)
compress

key-direction 1

<ca>
$(cat "${PKI_DIR}/pki/ca.crt")
</ca>

<cert>
$(sed -n '/BEGIN CERTIFICATE/,/END CERTIFICATE/p' "${PKI_DIR}/pki/issued/${CLIENT}.crt")
</cert>

<key>
$(cat "${PKI_DIR}/pki/private/${CLIENT}.key")
</key>

<tls-crypt>
$(cat /etc/openvpn/server/pki/ta.key)
</tls-crypt>
EOF

chmod 600 "${OUTPUT_DIR}/${CLIENT}.ovpn"
echo "Configurazione creata: ${OUTPUT_DIR}/${CLIENT}.ovpn"
```

---

## OpenVPN: Setup Client

### Linux

```bash
# Installa client
sudo apt install openvpn

# Connetti con file .ovpn
sudo openvpn --config /path/to/client.ovpn

# Oppure come servizio systemd
sudo cp client.ovpn /etc/openvpn/client/client.conf
sudo systemctl enable --now openvpn-client@client
```

### Verifica Connessione

```bash
# Verifica interfaccia tun
ip addr show tun0

# Verifica routing
ip route | grep tun0

# Test connettività
ping 10.8.0.1  # server VPN

# Verifica IP pubblico (se full tunnel)
curl ifconfig.me
```

---

## OpenVPN: Configurazione Avanzata

### tls-auth vs tls-crypt

```conf
# tls-auth: HMAC sul control channel (previene DoS)
# Il key-direction è 0 su server, 1 su client
tls-auth ta.key 0

# tls-crypt: cifra E autentica tutto il control channel
# Più sicuro di tls-auth (nasconde anche il handshake TLS)
# Nessun key-direction necessario
tls-crypt ta.key
```

### Client-Specific Configuration

```bash
# Crea directory per configurazioni per-client
mkdir -p /etc/openvpn/ccd

# Assegna IP fisso a un client
echo "ifconfig-push 10.8.0.10 10.8.0.9" > /etc/openvpn/ccd/client1

# Instrada rete del client (site-to-site)
echo "iroute 192.168.10.0 255.255.255.0" > /etc/openvpn/ccd/office-gateway
# Nota: serve anche "route 192.168.10.0 255.255.255.0" nel server.conf
```

### Dual Stack (UDP + TCP)

```conf
# Server UDP (primario — performance migliori)
# /etc/openvpn/server/server-udp.conf
port 1194
proto udp
# ... resto della configurazione ...

# Server TCP (fallback — funziona dove UDP è bloccato)
# /etc/openvpn/server/server-tcp.conf
port 443
proto tcp-server
# ... resto della configurazione (con rete VPN diversa) ...
```

```conf
# Client con fallback
remote vpn.example.com 1194 udp
remote vpn.example.com 443 tcp
remote-random  # prova in ordine casuale
```

### NAT e IP Forwarding

```bash
# Prerequisiti sul server OpenVPN

# Abilita IP forwarding
echo "net.ipv4.ip_forward = 1" > /etc/sysctl.d/99-openvpn.conf
sysctl -p /etc/sysctl.d/99-openvpn.conf

# NAT per full tunnel
iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o eth0 -j MASQUERADE
iptables -A FORWARD -i tun0 -o eth0 -j ACCEPT
iptables -A FORWARD -i eth0 -o tun0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# Persistenza regole
apt install iptables-persistent
netfilter-persistent save
```

### Avvio come Servizio

```bash
# Abilita e avvia il server
systemctl enable --now openvpn-server@server

# Stato
systemctl status openvpn-server@server

# Log
journalctl -u openvpn-server@server -f
```

---

## Site-to-Site vs Road Warrior

### Road Warrior

Il caso d'uso più comune: utenti mobili (laptop, smartphone) si connettono a una rete aziendale.

**Caratteristiche:**
- Molti client, un server
- Client con IP dinamici, dietro NAT
- Split tunnel (solo traffico aziendale) o full tunnel (tutto il traffico)
- I client si connettono e disconnettono frequentemente

**WireGuard Road Warrior:**
```ini
# Server
[Interface]
Address = 10.10.0.1/24
ListenPort = 51820
PrivateKey = ...
PostUp = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

[Peer]
PublicKey = <client1>
AllowedIPs = 10.10.0.2/32
```

**OpenVPN Road Warrior:**
```conf
# Server
server 10.8.0.0 255.255.255.0
push "route 10.0.0.0 255.255.0.0"
push "dhcp-option DNS 10.0.0.53"
```

### Site-to-Site

Interconnessione permanente tra due o più sedi.

**Caratteristiche:**
- Pochi peer con IP statici (o DDNS)
- Connessione permanente
- Routing di intere subnet
- Failover e ridondanza importanti

**WireGuard Site-to-Site:**
Ogni gateway ha la configurazione dell'altro come peer con `AllowedIPs` che include la subnet remota (vedi sezione precedente).

**OpenVPN Site-to-Site:**
```conf
# Server (sede A)
mode server
tls-server
ifconfig 10.8.0.1 10.8.0.2
route 10.2.0.0 255.255.255.0

# Client (sede B)
tls-client
ifconfig 10.8.0.2 10.8.0.1
route 10.1.0.0 255.255.255.0
```

---

## Confronto WireGuard vs OpenVPN

| Caratteristica | WireGuard | OpenVPN |
|---------------|-----------|---------|
| **Codebase** | ~4.000 righe (kernel) | ~100.000 righe (userspace) |
| **Performance** | Superiore (kernel-space, ChaCha20) | Buona (userspace, AES-NI) |
| **Latenza** | Molto bassa | Bassa |
| **Handshake** | 1-RTT | Multi-RTT (TLS) |
| **Cipher suite** | Fissa (non negoziabile) | Configurabile |
| **PKI** | No (solo chiavi pubbliche) | Sì (X.509, CRL, OCSP) |
| **Gestione certificati** | Non necessaria | Richiesta (Easy-RSA) |
| **Revoca client** | Rimuovi peer dalla config | Revoca certificato + CRL |
| **NAT traversal** | PersistentKeepalive | UDP nativamente, TCP come fallback |
| **Protocollo** | Solo UDP | UDP o TCP |
| **Funziona dietro proxy** | No (solo UDP) | Sì (TCP/443) |
| **Stealth** | Sì (non risponde a non-autenticati) | Parziale |
| **Audit di sicurezza** | Completato (2020) | Completato (2017) |
| **Supporto mobile** | App ufficiale (iOS, Android) | App ufficiale (iOS, Android) |
| **Maturità** | In kernel dal 2020 | Dal 2001 |

### Quando scegliere WireGuard

- Performance è prioritaria
- Setup semplice e rapido
- Pochi peer gestiti manualmente
- Non serve TCP fallback
- Non serve PKI complessa

### Quando scegliere OpenVPN

- Serve TCP (per ambienti con UDP bloccato)
- Serve PKI con gestione certificati e revoca
- Compatibilità con client legacy
- Configurazione avanzata (plugin, script, auth LDAP)
- Compliance che richiede algoritmi specifici

---

## Best Practices

1. **Usa sempre WireGuard per nuove installazioni** a meno che non ci siano requisiti specifici che richiedono OpenVPN (TCP fallback, PKI, compliance).

2. **Mai disabilitare la crittografia**: Potrebbe sembrare ovvio, ma `cipher none` in OpenVPN è un'opzione reale. Non usarla mai, nemmeno per "testing".

3. **Genera chiavi forti**: Per WireGuard, usa `wg genkey`. Per OpenVPN, usa almeno RSA 4096 o EC secp384r1. Non riutilizzare chiavi tra ambienti.

4. **Usa tls-crypt in OpenVPN**: Protegge il control channel dall'analisi e previene attacchi DoS. È superiore a tls-auth.

5. **Disabilita la compressione in OpenVPN**: La compressione VPN è vulnerabile all'attacco VORACLE (simile a CRIME/BREACH). Usa `compress` senza argomenti per disabilitarla.

6. **Split tunnel quando possibile**: Instrada solo il traffico necessario attraverso la VPN. Il full tunnel spreca bandwidth del server VPN per traffico che non ne ha bisogno.

7. **Documenta ogni peer**: Commenta la configurazione WireGuard con il nome del proprietario e la data di creazione. In OpenVPN, usa nomi di certificato descrittivi.

8. **Ruota le chiavi periodicamente**: In WireGuard, rigenera le chiavi client almeno annualmente. In OpenVPN, imposta `EASYRSA_CERT_EXPIRE` a 365 giorni.

9. **Monitora la VPN**: Controlla lo stato dei peer WireGuard (`wg show`) e le connessioni OpenVPN (`/var/log/openvpn/status.log`) regolarmente.

10. **Firewall sul server VPN**: Il server VPN deve avere un firewall che limita il traffico VPN alle sole reti necessarie. Un client VPN non deve avere accesso a tutto.

---

## Troubleshooting

### Problema: WireGuard — Nessun handshake

**Sintomi**: `wg show` non mostra "latest handshake" per un peer, il traffico non passa.

**Causa**: Firewall blocca UDP 51820, endpoint errato, chiavi non corrispondenti.

**Soluzione**:
```bash
# Verifica porta aperta sul server
ss -ulnp | grep 51820

# Verifica raggiungibilità UDP dal client
nc -u -z vpn.example.com 51820

# Verifica chiavi
wg show wg0
# Confronta la public key mostrata con quella configurata sul peer remoto

# Controlla i log del kernel
dmesg | grep wireguard

# Verifica firewall
iptables -L INPUT -n -v | grep 51820
```

### Problema: OpenVPN — TLS handshake failed

**Sintomi**: Il log mostra `TLS Error: TLS handshake failed` o `TLS Error: TLS key negotiation failed`.

**Causa**: Certificati non corrispondenti, CA diversa, tls-auth/tls-crypt mismatch, o clock non sincronizzato.

**Soluzione**:
```bash
# Verifica che il certificato sia firmato dalla stessa CA
openssl verify -CAfile ca.crt client.crt

# Verifica che tls-crypt sia lo stesso su server e client
md5sum /etc/openvpn/server/pki/ta.key
# Confronta con il ta.key nel file .ovpn del client

# Verifica clock (certificati hanno validità temporale)
date
# Se il clock è sbagliato, i certificati risultano non validi

# Aumenta verbosità per debugging
# Aggiungi temporaneamente: verb 6
# nel file di configurazione, poi controlla i log
```

### Problema: Routing non funziona dopo connessione VPN

**Sintomi**: La VPN si connette ma non è possibile raggiungere le reti remote.

**Causa**: IP forwarding disabilitato sul server, regole iptables mancanti, o routing non configurato.

**Soluzione**:
```bash
# Sul server VPN:

# 1. Verifica IP forwarding
cat /proc/sys/net/ipv4/ip_forward  # deve essere 1

# 2. Verifica NAT
iptables -t nat -L POSTROUTING -n -v
# Deve esserci una regola MASQUERADE per la subnet VPN

# 3. Verifica forwarding
iptables -L FORWARD -n -v
# Deve consentire traffico da/verso l'interfaccia VPN

# 4. Verifica routing sul client
ip route | grep -E "tun|wg"
# Le rotte per le subnet remote devono puntare all'interfaccia VPN

# 5. Test passo passo
# Dal client: ping il server VPN (interfaccia VPN)
ping 10.10.0.1  # o 10.8.0.1 per OpenVPN
# Se funziona: il tunnel è OK, il problema è routing/NAT
# Se non funziona: il tunnel non è stabilito
```

### Problema: Performance VPN scarse

**Sintomi**: La velocità attraverso la VPN è molto inferiore a quella della connessione sottostante.

**Causa**: MTU non ottimale, mancanza di offload hardware, CPU bottleneck (OpenVPN in userspace).

**Soluzione**:
```bash
# WireGuard: imposta MTU
# L'MTU ottimale è tipicamente 1420 per WireGuard (1500 - 80 byte overhead)
ip link set wg0 mtu 1420

# Nella configurazione:
[Interface]
MTU = 1420

# OpenVPN: imposta MSS
# nel server.conf:
mssfix 1400
tun-mtu 1500
fragment 1400  # solo UDP

# Test MTU ottimale
ping -M do -s 1400 10.10.0.1
# Riduci fino a quando non ricevi risposte
# MTU ottimale = dimensione che funziona + 28 (header IP+ICMP)

# Per OpenVPN: verifica che AES-NI sia disponibile
grep aes /proc/cpuinfo
# Se disponibile, assicurati di usare AES-256-GCM (usa AES-NI)
```

---

## Riferimenti

- **WireGuard**: https://www.wireguard.com/
- **WireGuard Whitepaper**: https://www.wireguard.com/papers/wireguard.pdf
- **WireGuard Quick Start**: https://www.wireguard.com/quickstart/
- **OpenVPN Documentation**: https://openvpn.net/community-resources/
- **OpenVPN Hardening Guide**: https://community.openvpn.net/openvpn/wiki/Hardening
- **Easy-RSA**: https://github.com/OpenVPN/easy-rsa
- **Noise Protocol Framework**: http://www.noiseprotocol.org/
- `man wg`, `man wg-quick`
- `man openvpn`

---

## Protocolli VPN: Panoramica Storica e Tecnica

Prima di WireGuard e OpenVPN, il panorama VPN era dominato da protocolli con tradeoff molto diversi. Comprendere questa evoluzione aiuta a contestualizzare le scelte architetturali moderne.

### PPTP (Point-to-Point Tunneling Protocol)

Sviluppato da Microsoft nel 1999 (RFC 2637). Utilizza GRE (Generic Routing Encapsulation) per il tunneling e MS-CHAPv2 per l'autenticazione. **Da non usare mai**: MPPE (Microsoft Point-to-Point Encryption) è basato su RC4, crittograficamente rotto. MS-CHAPv2 è vulnerabile a dictionary attack (dimostrato da Moxie Marlinspike a DEFCON 2012 con CloudCracker). Alcuni firewall aziendali lo bloccano per policy.

### L2TP/IPsec

L2TP (RFC 3931) non offre crittografia nativa — viene sempre combinato con IPsec (RFC 4301-4309) per la cifratura. L'overhead è significativo: doppio incapsulamento (IPsec ESP + L2TP + PPP). Supporta autenticazione con certificati o PSK. Il problema principale è il NAT traversal: IPsec e NAT sono storicamente incompatibili, risolto parzialmente da NAT-T (RFC 3948, UDP/4500). Ancora usato in contesti enterprise legacy, specialmente con client Windows e macOS nativi.

### IPsec (Internet Protocol Security)

Suite di protocolli (AH, ESP, IKEv1/IKEv2) per proteggere il traffico IP a livello di rete. IKEv2 (RFC 7296) è il protocollo di scambio chiavi moderno: supporta MOBIKE per il roaming, rinegoziazione veloce, autenticazione EAP. Su Linux, l'implementazione di riferimento è strongSwan (successore di FreeS/WAN → Openswan). IPsec è l'unica opzione per scenari che richiedono interoperabilità con appliance hardware (Cisco ASA, Juniper SRX, Fortinet, Palo Alto).

```
Confronto overhead protocolli VPN:

Protocollo        Overhead (byte)   Algoritmi moderni   Stato
─────────────────────────────────────────────────────────────
PPTP/MPPE         ~24 (GRE+PPP)    RC4 (rotto)         ✗ Deprecato
L2TP/IPsec        ~58-70           AES-GCM + SHA-2     △ Legacy
IPsec (IKEv2)     ~50-73 (ESP)     AES-GCM, ChaCha20   ✓ Enterprise
OpenVPN (UDP)     ~60-70           AES-256-GCM          ✓ Attivo
WireGuard         ~32              ChaCha20-Poly1305    ✓ Preferito
```

### IPsec vs WireGuard/OpenVPN: Quando Serve IPsec

IPsec è necessario quando:
- **Interoperabilità hardware**: connessione a VPN gateway commerciali (Cisco, Fortinet, Palo Alto)
- **Compliance specifiche**: alcuni framework richiedono IPsec (es. FIPS 140-2 con moduli validati)
- **Site-to-site enterprise**: molti setup enterprise legacy usano IKEv2 con certificati X.509
- **Tunnel trasparente**: IPsec in modalità transport non modifica gli header IP (utile per protocolli sensibili al TTL)

Per nuove installazioni Linux-to-Linux, WireGuard è quasi sempre superiore.

---

## WireGuard: Approfondimento Architetturale

### Noise Protocol Framework — Variante IK

WireGuard utilizza il Noise Protocol Framework (Trevor Perrin, 2018) nella variante `Noise_IKpsk2`. La notazione indica:

- **I**: l'initiator trasmette la propria chiave statica nel primo messaggio
- **K**: il responder ha la chiave statica dell'initiator pre-condivisa (tramite configurazione)
- **psk2**: una pre-shared key opzionale viene miscelata dopo il secondo messaggio

```
Handshake dettagliato (1-RTT):

msg1: Initiator → Responder
  ├── unencrypted_ephemeral = Epub_i
  ├── encrypted_static = AEAD(key=DH(Epub_i, Spub_r), Spub_i)
  ├── encrypted_timestamp = AEAD(key=DH(...), TAI64N_timestamp)
  └── MAC1 = MAC(Hash(label ∥ Spub_r), msg1)      ← anti-replay
      MAC2 = MAC(cookie, msg1)                      ← anti-DoS (se richiesto)

msg2: Responder → Initiator
  ├── unencrypted_ephemeral = Epub_r
  ├── encrypted_nothing = AEAD(key=..., empty)
  └── MAC1, MAC2

Derivazione chiavi di trasporto:
  T_send, T_recv = KDF(chain_key)
  ├── ChaCha20-Poly1305 con counter a 64 bit
  └── Rekey ogni 2^64 messaggi o 120 secondi (whichever first)
```

### Timer e Gestione Sessione

WireGuard implementa una state machine con timer precisi:

| Timer | Valore | Scopo |
|-------|--------|-------|
| `REKEY_AFTER_MESSAGES` | 2^60 | Rekey dopo N messaggi trasmessi |
| `REJECT_AFTER_MESSAGES` | 2^64 - 2^4 - 1 | Rifiuta chiavi dopo N messaggi |
| `REKEY_AFTER_TIME` | 120 secondi | Rekey dopo N secondi |
| `REJECT_AFTER_TIME` | 180 secondi | Rifiuta chiave dopo N secondi |
| `REKEY_TIMEOUT` | 5 secondi | Timeout per retry handshake |
| `KEEPALIVE_TIMEOUT` | configurabile | `PersistentKeepalive` |

### Cookie Mechanism (Resistenza DoS)

Quando il server è sotto carico, risponde con un pacchetto cookie (non un handshake completo). Il client deve ripetere l'handshake includendo il cookie nel campo MAC2. Questo meccanismo, ispirato a DTLS (RFC 6347), impedisce amplification attack e SYN flood equivalents.

```
Flusso sotto carico:

1. Client → Server: msg1 (handshake initiation)
2. Server sotto carico: risponde con COOKIE_REPLY
   └── cookie = MAC(secret_cambia_ogni_2min, IP_sorgente)
3. Client → Server: msg1 (con MAC2 = MAC(cookie, msg1))
4. Server: verifica MAC2, procede con handshake
```

### Kernel vs Userspace: wireguard-go

L'implementazione kernel (C, ~4000 righe nel modulo `net/wireguard/`) è la più performante. Per sistemi senza supporto kernel nativo esiste `wireguard-go` (Go, userspace):

```bash
# Verifica implementazione in uso
wg show wg0
# Se il kernel module è caricato:
lsmod | grep wireguard
# wireguard    94208  0

# wireguard-go (macOS, Windows, userspace Linux)
# Automaticamente usato se il modulo kernel non è disponibile
# Performance ~3-5x inferiore rispetto a kernel
```

### WireGuard e Namespace di Rete

WireGuard si integra con i network namespace Linux per isolamento completo:

```bash
# Crea namespace isolato per un container/servizio
ip netns add vpn-isolated

# Sposta l'interfaccia WireGuard nel namespace
ip link set wg0 netns vpn-isolated

# Configura dentro il namespace
ip netns exec vpn-isolated wg setconf wg0 /etc/wireguard/wg0.conf
ip netns exec vpn-isolated ip addr add 10.10.0.2/24 dev wg0
ip netns exec vpn-isolated ip link set wg0 up
ip netns exec vpn-isolated ip route add default dev wg0

# Esegui un processo nel namespace (tutto il traffico via VPN)
ip netns exec vpn-isolated curl ifconfig.me
```

Questo pattern è usato da client VPN come Mullvad per garantire che nessun traffico sfugga al tunnel (kill switch a livello kernel).

### WireGuard con systemd-networkd

Alternativa a wg-quick per server che usano systemd-networkd:

```ini
# /etc/systemd/network/90-wg0.netdev
[NetDev]
Name = wg0
Kind = wireguard
Description = WireGuard VPN tunnel

[WireGuard]
ListenPort = 51820
PrivateKeyFile = /etc/wireguard/server_private.key

[WireGuardPeer]
PublicKey = <chiave_pubblica_client>
AllowedIPs = 10.10.0.2/32
PresharedKeyFile = /etc/wireguard/psk.key
```

```ini
# /etc/systemd/network/90-wg0.network
[Match]
Name = wg0

[Network]
Address = 10.10.0.1/24

[Route]
Destination = 10.10.0.0/24
```

```bash
# Applica
systemctl restart systemd-networkd
networkctl status wg0
```

Vantaggi rispetto a wg-quick: integrazione nativa con resolved (DNS), gestione centralizzata delle interfacce, nessuna dipendenza da script bash, compatibilità con `networkctl`.

### WireGuard e IPv6

WireGuard supporta nativamente dual-stack IPv4+IPv6:

```ini
[Interface]
Address = 10.10.0.1/24, fd00:vpn::1/64
ListenPort = 51820
PrivateKey = ...

[Peer]
PublicKey = ...
AllowedIPs = 10.10.0.2/32, fd00:vpn::2/128
```

```bash
# Full tunnel dual-stack (client)
[Peer]
AllowedIPs = 0.0.0.0/0, ::/0
```

> **Errore comune:** Molti dimenticano di aggiungere `::/0` in `AllowedIPs` per il full tunnel. Risultato: il traffico IPv6 bypassa la VPN, creando un leak di privacy. Strumenti come `ip6leak.com` verificano la presenza di leak IPv6.

### fwmark e Policy Routing

Il parametro `FwMark` in WireGuard marca i pacchetti VPN per evitare loop di routing quando si usa il full tunnel (`AllowedIPs = 0.0.0.0/0`):

```ini
[Interface]
FwMark = 51820
```

```bash
# wg-quick implementa automaticamente:
ip rule add not fwmark 51820 table 51820
ip rule add table main suppress_prefixlength 0
ip route add default dev wg0 table 51820

# Questo garantisce che:
# 1. Il traffico generato da WireGuard stesso (marcato 51820) usi la route normale
# 2. Tutto il resto del traffico vada via wg0
# 3. Le route locali (LAN) siano preservate
```

---

## Tailscale e Headscale: VPN Mesh su WireGuard

### Tailscale: Architettura

Tailscale è un overlay mesh network che usa WireGuard come data plane e aggiunge un control plane gestito (coordination server):

```
┌────────────┐        ┌──────────────────┐        ┌────────────┐
│  Nodo A    │◄──────►│  Coordination    │◄──────►│  Nodo B    │
│ tailscaled │        │  Server          │        │ tailscaled │
│            │        │ (login.tailscale │        │            │
│            │        │  .com)           │        │            │
│ WireGuard  │◄═══════╪═══════════════════╪═══════►│ WireGuard  │
│ tunnel     │  diretto (se possibile)    │        │ tunnel     │
└────────────┘        └──────────────────┘        └────────────┘
                             │
                      ┌──────┴──────┐
                      │ DERP Relay  │ ← solo se NAT/firewall
                      │ (fallback)  │   impedisce connessione diretta
                      └─────────────┘
```

**Componenti chiave:**

- **Coordination server**: distribuisce chiavi pubbliche, ACL, configurazioni DNS. Non vede il traffico dati.
- **DERP relay**: relay TCP encrypted per quando la connessione diretta UDP fallisce (NAT doppio, firewall restrittivi). Il traffico è E2E encrypted — DERP non può decifrarlo.
- **MagicDNS**: risolve `nodo.tailnet-name.ts.net` automaticamente.
- **Taildrop**: file sharing peer-to-peer criptato.
- **Exit nodes**: un nodo può fungere da gateway per il traffico internet degli altri.

```bash
# Installazione Tailscale su Linux
curl -fsSL https://tailscale.com/install.sh | sh
# NOTA: in produzione, verifica lo script prima di eseguirlo
# oppure installa dal repository ufficiale:
# apt/dnf install tailscale

# Login
tailscale up

# Stato
tailscale status
# 100.64.0.1  server-prod   user@   linux   -
# 100.64.0.2  laptop-dev    user@   linux   active; direct 203.0.113.5:41641

# Abilita come exit node
tailscale up --advertise-exit-node

# Usa un exit node specifico
tailscale up --exit-node=server-prod

# Advertise subnet routes (site-to-site)
tailscale up --advertise-routes=10.0.0.0/24,192.168.1.0/24

# Verifica connessione diretta vs relay
tailscale ping server-prod
# pong from server-prod (100.64.0.1) via 203.0.113.5:41641 in 12ms
```

### ACL (Access Control Lists) di Tailscale

```jsonc
// tailscale ACL policy (JSON o HuJSON)
{
  "groups": {
    "group:devs": ["user1@example.com", "user2@example.com"],
    "group:admins": ["admin@example.com"]
  },
  "acls": [
    // devs possono accedere solo a porte specifiche
    {"action": "accept", "src": ["group:devs"], "dst": ["tag:webserver:80,443"]},
    // admins accedono a tutto
    {"action": "accept", "src": ["group:admins"], "dst": ["*:*"]},
    // tutti possono pingare tutti (per diagnostica)
    {"action": "accept", "src": ["*"], "dst": ["*:*"], "proto": "icmp"}
  ],
  "tagOwners": {
    "tag:webserver": ["group:admins"],
    "tag:database": ["group:admins"]
  },
  "ssh": [
    {"action": "accept", "src": ["group:admins"], "dst": ["tag:webserver"], "users": ["root"]}
  ]
}
```

### Headscale: Tailscale Self-Hosted

Headscale è un'implementazione open source del coordination server Tailscale. Permette di avere un control plane completamente sotto il proprio controllo:

```bash
# Installazione Headscale
wget https://github.com/juanfont/headscale/releases/download/v0.23.0/headscale_0.23.0_linux_amd64.deb
dpkg -i headscale_*.deb

# Configurazione
cat /etc/headscale/config.yaml
# server_url: https://headscale.example.com
# listen_addr: 0.0.0.0:8080
# private_key_path: /var/lib/headscale/private.key
# noise:
#   private_key_path: /var/lib/headscale/noise_private.key
# db_type: sqlite3
# db_path: /var/lib/headscale/db.sqlite
# dns:
#   magic_dns: true
#   base_domain: vpn.example.com
#   nameservers:
#     - 1.1.1.1

# Crea un utente (namespace)
headscale users create infra

# Genera chiave di pre-autenticazione
headscale preauthkeys create --user infra --expiration 24h
# ← restituisce una chiave tipo: tskey-preauth-xxxxxxxxxxxx

# Sul client: connetti a Headscale invece che a Tailscale
tailscale up --login-server https://headscale.example.com --authkey tskey-preauth-xxxxxxxxxxxx

# Lista nodi
headscale nodes list
```

**Differenze Headscale vs Tailscale commerciale:**

| Feature | Tailscale | Headscale |
|---------|-----------|-----------|
| DERP relay | Gestito (globale) | Self-hosted o usa quelli Tailscale |
| ACL | GUI + GitOps | File YAML/JSON |
| SSO/OIDC | Integrato | Via OIDC (Keycloak, Authelia) |
| MagicDNS | Sì | Sì (dalla v0.20) |
| Taildrop | Sì | Parziale |
| SSH | Tailscale SSH | Non supportato |
| Prezzo | Free fino a 100 device | Gratuito (self-hosted) |

---

## OpenVPN: Funzionalità Avanzate

### Plugin di Autenticazione

OpenVPN supporta plugin C per estendere l'autenticazione oltre i certificati X.509:

```conf
# Autenticazione PAM (sistema locale)
plugin /usr/lib/openvpn/openvpn-plugin-auth-pam.so login

# Autenticazione LDAP
plugin /usr/lib/openvpn/openvpn-plugin-auth-ldap.so /etc/openvpn/auth-ldap.conf
```

```xml
<!-- /etc/openvpn/auth-ldap.conf -->
<LDAP>
    URL         ldaps://ldap.example.com:636
    BindDN      cn=openvpn,ou=services,dc=example,dc=com
    Password    ${LDAP_BIND_PASSWORD}
    Timeout     15
    TLSEnable   yes
    TLSCACertFile /etc/ssl/certs/ca.crt
</LDAP>

<Authorization>
    BaseDN      "ou=users,dc=example,dc=com"
    SearchFilter "(uid=%u)"
    RequireGroup true
    
    <Group>
        BaseDN      "ou=groups,dc=example,dc=com"
        SearchFilter "(cn=vpn-users)"
        MemberAttribute member
    </Group>
</Authorization>
```

### 2FA con Google Authenticator / TOTP

```bash
# Installa il modulo PAM
apt install libpam-google-authenticator

# Configura PAM per OpenVPN
cat >> /etc/pam.d/openvpn <<'EOF'
auth required pam_google_authenticator.so
auth required pam_unix.so
EOF

# Ogni utente esegue:
google-authenticator -t -d -f -r 3 -R 30 -w 3
# -t: time-based (TOTP)
# -d: disallow reuse
# -f: force write
# -r 3 -R 30: rate limit (3 tentativi ogni 30 secondi)

# OpenVPN server.conf
plugin /usr/lib/openvpn/openvpn-plugin-auth-pam.so openvpn
# Il client dovrà inserire: password + codice TOTP nel campo password
# Formato: password_realeOTP123456 (concatenati) o separati (dipende dal client)
```

### Management Interface

OpenVPN espone un'interfaccia di gestione per monitoraggio e controllo in tempo reale:

```conf
# server.conf
management 127.0.0.1 7505 /etc/openvpn/management-password
```

```bash
# Connetti all'interfaccia di gestione
telnet 127.0.0.1 7505

# Comandi utili:
# status          — mostra client connessi
# kill <cn>       — disconnetti un client per Common Name
# kill <ip:port>  — disconnetti per indirizzo
# log on          — abilita log in tempo reale
# bytecount 5    — statistiche traffico ogni 5 secondi
# client-deny <cid> <kid> "reason" — blocca un client
# client-auth <cid> <kid>          — autorizza un client
# signal SIGUSR1  — soft restart
# signal SIGTERM  — shutdown

# Script per monitoraggio automatizzato
#!/bin/bash
echo "status" | nc -q1 127.0.0.1 7505 | grep "CLIENT_LIST" | while read line; do
    CN=$(echo "$line" | cut -d',' -f2)
    REAL_ADDR=$(echo "$line" | cut -d',' -f3)
    BYTES_RX=$(echo "$line" | cut -d',' -f5)
    BYTES_TX=$(echo "$line" | cut -d',' -f6)
    CONNECTED=$(echo "$line" | cut -d',' -f7)
    echo "$CN from $REAL_ADDR — RX: $BYTES_RX TX: $BYTES_TX since $CONNECTED"
done
```

### OpenVPN e systemd: Hardening dell'Unità

```ini
# /etc/systemd/system/openvpn-server@server.service.d/hardening.conf
[Service]
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
NoNewPrivileges=true
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE CAP_NET_RAW CAP_SETUID CAP_SETGID CAP_DAC_READ_SEARCH
ReadWritePaths=/var/log/openvpn /run/openvpn
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictNamespaces=true
LockPersonality=true
MemoryDenyWriteExecute=true
RestrictRealtime=true
RestrictSUIDSGID=true
```

---

## Threat Model VPN: Cosa Protegge e Cosa No

> **Errore comune:** Molti credono che una VPN renda "anonimi" o "sicuri" online. Una VPN protegge il canale di trasporto, non l'endpoint né il comportamento dell'utente.

### Cosa protegge una VPN

| Minaccia | Protezione |
|----------|------------|
| Intercettazione traffico sulla rete locale (WiFi pubblico) | ✓ Il traffico è cifrato nel tunnel |
| ISP che monitora destinazioni DNS/HTTP | ✓ L'ISP vede solo traffico verso il server VPN |
| Censura basata su IP/dominio | ✓ Il server VPN agisce da proxy |
| Accesso remoto a reti private | ✓ Caso d'uso primario |
| Man-in-the-middle sulla rete locale | ✓ Autenticazione reciproca (chiavi/certificati) |

### Cosa NON protegge una VPN

| Minaccia | Perché la VPN non basta |
|----------|------------------------|
| Malware sull'endpoint | Il malware opera prima/dopo la cifratura VPN |
| Fingerprinting browser | Browser fingerprint non cambia con la VPN |
| DNS leak | Se il resolver DNS non è nel tunnel, le query DNS rivelano le destinazioni |
| IPv6 leak | Se IPv6 non è tunnelizzato, il traffico v6 bypassa la VPN |
| WebRTC leak | WebRTC può rivelare l'IP reale via STUN, anche con VPN attiva |
| Correlazione temporale | Un avversario che osserva sia l'ingresso che l'uscita del tunnel può correlare |
| Traffico HTTPS già cifrato | La VPN aggiunge un secondo strato, ma HTTPS protegge già il payload |

### DNS Leak Prevention

```bash
# WireGuard: specifica DNS nella configurazione
[Interface]
DNS = 10.10.0.53
# wg-quick configura /etc/resolv.conf o systemd-resolved

# Verifica con systemd-resolved
resolvectl status wg0
# DNS Servers: 10.10.0.53
# DNS Domain: ~.

# Test manuale DNS leak
dig +short whoami.akamai.net @ns1-1.akamaitech.net
# Deve restituire l'IP del server VPN, non il tuo IP reale

# OpenVPN: push DNS dal server
push "dhcp-option DNS 10.8.0.53"
push "block-outside-dns"  # Windows: blocca DNS non-tunnel
```

### Kill Switch (Prevenzione Leak)

Un kill switch garantisce che se la VPN cade, nessun traffico esce non cifrato:

```bash
# Kill switch con nftables per WireGuard
cat > /etc/nftables.d/vpn-killswitch.nft <<'EOF'
table inet vpn_killswitch {
    chain output {
        type filter hook output priority 0; policy drop;
        
        # Permetti traffico loopback
        oifname "lo" accept
        
        # Permetti traffico WireGuard (verso endpoint)
        udp dport 51820 accept
        
        # Permetti DHCP
        udp dport 67 accept
        udp sport 68 accept
        
        # Permetti tutto il traffico via wg0
        oifname "wg0" accept
        
        # Permetti traffico LAN
        ip daddr 10.0.0.0/8 accept
        ip daddr 172.16.0.0/12 accept
        ip daddr 192.168.0.0/16 accept
        
        # Tutto il resto: bloccato
        log prefix "VPN-KILLSWITCH-DROP: " counter drop
    }
}
EOF

nft -f /etc/nftables.d/vpn-killswitch.nft
```

---

## Split Tunneling Avanzato

### Policy Routing con ip rule

Split tunneling selettivo per instradare solo determinato traffico via VPN:

```bash
# Tabella di routing dedicata alla VPN
echo "100 vpn" >> /etc/iproute2/rt_tables

# Route di default via VPN nella tabella 100
ip route add default dev wg0 table vpn

# Regole: solo traffico verso reti specifiche usa la tabella vpn
ip rule add to 10.0.0.0/8 lookup vpn priority 100
ip rule add to 172.16.0.0/12 lookup vpn priority 100

# Oppure: inverso — tutto via VPN TRANNE reti specifiche
ip rule add to 0.0.0.0/0 lookup vpn priority 200
ip rule add to 192.168.1.0/24 lookup main priority 100  # LAN locale esclusa
```

### Split Tunneling per Processo (con cgroup)

```bash
# Crea un cgroup per processi che devono bypassare la VPN
mkdir -p /sys/fs/cgroup/net_cls/novpn
echo 0x00110011 > /sys/fs/cgroup/net_cls/novpn/net_cls.classid

# Regola iptables: i pacchetti con questo classid usano la route non-VPN
iptables -t mangle -A OUTPUT -m cgroup --cgroup 0x00110011 -j MARK --set-mark 0x1
ip rule add fwmark 0x1 lookup main priority 50

# Esegui un processo senza VPN
cgexec -g net_cls:novpn curl ifconfig.me
# Mostra l'IP reale, non quello del VPN
```

### nftables per Split Tunneling Granulare

```
table inet split_tunnel {
    chain prerouting {
        type filter hook prerouting priority mangle; policy accept;
        
        # Marca traffico verso reti aziendali per routing via VPN
        ip daddr 10.0.0.0/8 meta mark set 0x51820
        ip daddr 172.20.0.0/16 meta mark set 0x51820
    }
    
    chain output {
        type route hook output priority mangle; policy accept;
        
        # Stessa logica per traffico generato localmente
        ip daddr 10.0.0.0/8 meta mark set 0x51820
        ip daddr 172.20.0.0/16 meta mark set 0x51820
    }
}
```

---

## Alta Disponibilità VPN

### WireGuard HA con Keepalived (Active-Passive)

```
┌──────────────┐     VIP: 203.0.113.10     ┌──────────────┐
│  VPN-A       │◄──── keepalived VRRP ─────►│  VPN-B       │
│  wg0: active │                            │  wg0: standby│
│  priority 100│                            │  priority 90 │
└──────────────┘                            └──────────────┘
```

```bash
# /etc/keepalived/keepalived.conf — Nodo A (master)
vrrp_instance VPN_HA {
    state MASTER
    interface eth0
    virtual_router_id 51
    priority 100
    advert_int 1
    
    authentication {
        auth_type PASS
        auth_pass vpnha_secret
    }
    
    virtual_ipaddress {
        203.0.113.10/24
    }
    
    notify_master "/usr/local/bin/vpn-failover.sh master"
    notify_backup "/usr/local/bin/vpn-failover.sh backup"
}
```

```bash
#!/bin/bash
# /usr/local/bin/vpn-failover.sh
case "$1" in
    master)
        wg-quick up wg0
        logger "VPN HA: questo nodo è diventato MASTER, wg0 attivata"
        ;;
    backup)
        wg-quick down wg0
        logger "VPN HA: questo nodo è diventato BACKUP, wg0 disattivata"
        ;;
esac
```

### WireGuard HA con Sincronizzazione Configurazione

Per HA è fondamentale che entrambi i nodi abbiano la stessa configurazione WireGuard:

```bash
#!/bin/bash
# sync-wg-config.sh — sincronizza configurazione tra nodi HA
# Eseguire sul master dopo ogni modifica

PEER_HOST="vpn-b.internal"
CONFIG="/etc/wireguard/wg0.conf"

# Sincronizza (le chiavi private devono essere diverse sui due nodi)
# Sincronizza solo la sezione [Peer]
grep -A3 '^\[Peer\]' "$CONFIG" | ssh "$PEER_HOST" "cat > /tmp/peers.conf"
ssh "$PEER_HOST" "
    head -n \$(grep -n '^\[Peer\]' /etc/wireguard/wg0.conf | head -1 | cut -d: -f1 | xargs -I{} expr {} - 1) /etc/wireguard/wg0.conf > /tmp/wg0-new.conf
    cat /tmp/peers.conf >> /tmp/wg0-new.conf
    mv /tmp/wg0-new.conf /etc/wireguard/wg0.conf
    wg syncconf wg0 <(wg-quick strip wg0)
"
```

### OpenVPN HA con Floating IP

OpenVPN supporta HA tramite la direttiva `float` e persistent IP pool condiviso:

```conf
# Sul server OpenVPN master e slave, stessa configurazione con:
ifconfig-pool-persist /shared/nfs/ipp.txt
# Il file ipp.txt su NFS condiviso mantiene le assegnazioni IP
# Quando il failover avviene, i client riottengono lo stesso IP VPN
```

---

## Monitoring VPN

### Prometheus Exporter per WireGuard

```bash
# wireguard_exporter (Go)
# Espone metriche Prometheus da `wg show all dump`

# Installazione
wget https://github.com/mdlayher/wireguard_exporter/releases/latest/download/wireguard_exporter-linux-amd64
chmod +x wireguard_exporter-linux-amd64
mv wireguard_exporter-linux-amd64 /usr/local/bin/wireguard_exporter

# Esecuzione
wireguard_exporter -metrics.addr :9586

# Metriche esposte:
# wireguard_peer_last_handshake_seconds     — timestamp ultimo handshake
# wireguard_peer_receive_bytes_total        — byte ricevuti per peer
# wireguard_peer_transmit_bytes_total       — byte trasmessi per peer
# wireguard_peer_allowed_ips_info           — info AllowedIPs per peer
# wireguard_device_info                     — info interfaccia

# prometheus.yml
scrape_configs:
  - job_name: wireguard
    static_configs:
      - targets: ['vpn-server:9586']
```

### Alert per Peer Disconnessi

```yaml
# Prometheus alerting rule
groups:
  - name: vpn
    rules:
      - alert: WireGuardPeerDown
        expr: time() - wireguard_peer_last_handshake_seconds > 300
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "WireGuard peer {{ $labels.public_key }} non comunica da >5 minuti"
      
      - alert: WireGuardNoTraffic
        expr: rate(wireguard_peer_receive_bytes_total[10m]) == 0 and wireguard_peer_last_handshake_seconds > 0
        for: 15m
        labels:
          severity: info
        annotations:
          summary: "Peer {{ $labels.public_key }} connesso ma senza traffico"
```

### Script di Monitoraggio Leggero

```bash
#!/bin/bash
# wg-monitor.sh — monitoraggio WireGuard senza Prometheus

LOG="/var/log/wireguard-monitor.log"

wg show all dump | tail -n +2 | while IFS=$'\t' read -r iface pubkey psk endpoint allowed_ips last_handshake rx tx keepalive; do
    now=$(date +%s)
    handshake_age=$(( now - last_handshake ))
    
    peer_name=$(grep -B1 "PublicKey = $pubkey" /etc/wireguard/*.conf 2>/dev/null | grep '#' | sed 's/.*# //')
    peer_name="${peer_name:-$pubkey}"
    
    if (( handshake_age > 300 )); then
        echo "$(date -Iseconds) WARN peer=$peer_name handshake_age=${handshake_age}s endpoint=$endpoint" >> "$LOG"
    fi
    
    # Converti byte in formato leggibile
    rx_human=$(numfmt --to=iec "$rx" 2>/dev/null || echo "${rx}B")
    tx_human=$(numfmt --to=iec "$tx" 2>/dev/null || echo "${tx}B")
    
    echo "$(date -Iseconds) INFO peer=$peer_name rx=$rx_human tx=$tx_human last_handshake=${handshake_age}s" >> "$LOG"
done
```

---

## VPN in Container

### WireGuard in Docker

```yaml
# docker-compose.yml — WireGuard server in container
services:
  wireguard:
    image: lscr.io/linuxserver/wireguard:latest
    container_name: wireguard
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Rome
      - SERVERURL=vpn.example.com
      - SERVERPORT=51820
      - PEERS=alice,bob,charlie
      - PEERDNS=1.1.1.1
      - INTERNAL_SUBNET=10.10.0.0
      - ALLOWEDIPS=0.0.0.0/0
    volumes:
      - ./config:/config
      - /lib/modules:/lib/modules:ro
    ports:
      - 51820:51820/udp
    sysctls:
      - net.ipv4.conf.all.src_valid_mark=1
      - net.ipv4.ip_forward=1
    restart: unless-stopped
```

### VPN come Sidecar (Kubernetes Pattern)

```yaml
# Pod con sidecar WireGuard — tutto il traffico dell'app esce via VPN
apiVersion: v1
kind: Pod
metadata:
  name: app-with-vpn
spec:
  containers:
    - name: app
      image: myapp:latest
      # L'app usa la rete del pod, che è instradada via WireGuard
    - name: wireguard
      image: lscr.io/linuxserver/wireguard:latest
      securityContext:
        capabilities:
          add: ["NET_ADMIN", "SYS_MODULE"]
      volumeMounts:
        - name: wg-config
          mountPath: /config
  volumes:
    - name: wg-config
      secret:
        secretName: wireguard-config
```

---

## Deployment Automatizzato con Ansible

### Ruolo Ansible per WireGuard

```yaml
# roles/wireguard/tasks/main.yml
---
- name: Installa WireGuard
  ansible.builtin.package:
    name: "{{ wireguard_packages }}"
    state: present

- name: Genera chiave privata server
  ansible.builtin.command: wg genkey
  args:
    creates: /etc/wireguard/server_private.key
  register: server_private_key
  no_log: true

- name: Salva chiave privata
  ansible.builtin.copy:
    content: "{{ server_private_key.stdout }}"
    dest: /etc/wireguard/server_private.key
    mode: '0600'
    owner: root
    group: root
  when: server_private_key.changed
  no_log: true

- name: Genera chiave pubblica server
  ansible.builtin.shell: cat /etc/wireguard/server_private.key | wg pubkey
  register: server_public_key
  changed_when: false

- name: Template configurazione WireGuard
  ansible.builtin.template:
    src: wg0.conf.j2
    dest: /etc/wireguard/wg0.conf
    mode: '0600'
    owner: root
    group: root
  notify: restart wireguard

- name: Abilita IP forwarding
  ansible.posix.sysctl:
    name: "{{ item }}"
    value: '1'
    sysctl_file: /etc/sysctl.d/99-wireguard.conf
    reload: true
  loop:
    - net.ipv4.ip_forward
    - net.ipv6.conf.all.forwarding

- name: Abilita e avvia WireGuard
  ansible.builtin.systemd:
    name: wg-quick@wg0
    enabled: true
    state: started
```

```jinja2
{# roles/wireguard/templates/wg0.conf.j2 #}
[Interface]
Address = {{ wireguard_server_address }}
ListenPort = {{ wireguard_port | default(51820) }}
PrivateKey = {{ lookup('file', '/etc/wireguard/server_private.key') }}
PostUp = iptables -t nat -A POSTROUTING -o {{ wireguard_external_interface }} -j MASQUERADE
PostDown = iptables -t nat -D POSTROUTING -o {{ wireguard_external_interface }} -j MASQUERADE

{% for peer in wireguard_peers %}
# {{ peer.name }} — {{ peer.description | default('') }}
[Peer]
PublicKey = {{ peer.public_key }}
AllowedIPs = {{ peer.allowed_ips }}
{% if peer.endpoint is defined %}
Endpoint = {{ peer.endpoint }}
{% endif %}
{% if peer.persistent_keepalive is defined %}
PersistentKeepalive = {{ peer.persistent_keepalive }}
{% endif %}

{% endfor %}
```

---

## Considerazioni Post-Quantum

### WireGuard e Resistenza Post-Quantum

WireGuard utilizza Curve25519 (ECDH), vulnerabile ad attacchi di computer quantistici con l'algoritmo di Shor. Le contromisure attuali:

1. **PresharedKey (PSK)**: WireGuard supporta nativamente una PSK opzionale che viene miscelata nella derivazione delle chiavi. Se la PSK è generata con un buon PRNG e distribuita out-of-band, fornisce resistenza post-quantum anche se Curve25519 viene rotto.

```ini
[Peer]
PresharedKey = <256-bit PSK generata con wg genpsk>
# Questa PSK aggiunge una difesa post-quantum al tunnel
# Un avversario deve rompere ENTRAMBI Curve25519 E conoscere la PSK
```

2. **Rosenpass**: progetto sperimentale che aggiunge un handshake post-quantum (basato su Classic McEliece + Kyber) sopra WireGuard:

```bash
# Rosenpass: PQ key exchange per WireGuard
# https://rosenpass.eu/
# Genera chiavi PQ e le usa per derivare la PSK di WireGuard
# automaticamente, rotandola periodicamente
```

### OpenVPN e Post-Quantum

OpenVPN 2.6+ con OpenSSL 3.x può usare algoritmi post-quantum tramite il provider OQS (Open Quantum Safe):

```conf
# Abilitare cipher suite ibride (classica + PQ)
# Richiede OpenSSL 3.x con oqs-provider
tls-cipher DEFAULT:@SECLEVEL=2
# I gruppi di scambio chiavi PQ sono configurabili via OpenSSL
```

---

## Troubleshooting Avanzato

### WireGuard: Debug con tcpdump

```bash
# Cattura traffico WireGuard sulla porta UDP
tcpdump -i eth0 -n udp port 51820

# Cattura traffico dentro il tunnel (decifrato)
tcpdump -i wg0 -n

# Confronto: se vedi traffico su eth0:51820 ma non su wg0,
# il problema è nell'handshake (chiavi non corrispondono)

# Se vedi traffico su wg0 ma i pacchetti non raggiungono la destinazione,
# il problema è nel routing o nel firewall
```

### WireGuard: AllowedIPs Conflicts

```bash
# Errore: due peer con AllowedIPs sovrapposti
# WireGuard usa AllowedIPs come tabella di routing — non possono sovrapporsi

# SBAGLIATO:
# [Peer] Alice  AllowedIPs = 10.10.0.0/24
# [Peer] Bob    AllowedIPs = 10.10.0.0/24
# ← Risultato: solo l'ultimo peer riceve il traffico

# CORRETTO:
# [Peer] Alice  AllowedIPs = 10.10.0.2/32
# [Peer] Bob    AllowedIPs = 10.10.0.3/32
```

### OpenVPN: Certificate Chain Errors

```bash
# "VERIFY ERROR: depth=0, error=unable to get local issuer certificate"
# La catena di certificati è incompleta

# Verifica catena:
openssl verify -CAfile /etc/openvpn/ca.crt /etc/openvpn/server.crt

# Se ca.crt contiene un'intermediate CA, concatena:
cat intermediate.crt root.crt > ca-chain.crt
```

### OpenVPN: Slow Connection After Reconnect

```bash
# Causa: il server mantiene la vecchia sessione TLS per il timeout
# definito da "keepalive"

# Soluzione: abilita "explicit-exit-notify" nel client
explicit-exit-notify 2
# Il client invia una notifica al server prima di disconnettersi
# Il server libera immediatamente le risorse
```

### WireGuard: MTU e Frammentazione

```bash
# Sintomi: connessioni TCP si bloccano su pacchetti grandi (SCP lento, HTTP timeout)
# Causa: MTU troppo alto, pacchetti frammentati e persi

# Trova MTU ottimale:
ping -M do -s 1420 -c 5 10.10.0.1
# Se fallisce, riduci -s fino a trovare il valore che funziona
# MTU ottimale = valore_funzionante + 28

# WireGuard overhead: 32 byte (header) + 28 byte (UDP+IP)
# MTU standard: 1500 - 60 = 1440 (conservativo)
# Con PPPoE:    1492 - 60 = 1432

# Imposta nella configurazione:
[Interface]
MTU = 1420
```

### OpenVPN: High CPU e Slow Throughput

```bash
# OpenVPN opera in userspace — single-threaded per default
# Su server con molti client, la CPU è il collo di bottiglia

# Verifica:
top -p $(pidof openvpn)

# Soluzioni:
# 1. Usa AES-128-GCM (se AES-NI disponibile, più veloce di AES-256-GCM)
cipher AES-128-GCM

# 2. Verifica AES-NI
grep -o aes /proc/cpuinfo | head -1

# 3. Multiprocess (istanze separate su porte diverse)
# server-udp.conf: port 1194
# server-tcp.conf: port 443

# 4. Considera migrazione a WireGuard per performance
```

### DNS non Funziona con VPN Attiva

```bash
# Sintomi: la VPN si connette, ping funziona per IP, ma DNS non risolve

# WireGuard + systemd-resolved:
resolvectl status wg0
# Se il DNS non è impostato:
resolvectl dns wg0 10.10.0.53
resolvectl domain wg0 ~.

# Verifica ordine di risoluzione:
resolvectl query example.com

# OpenVPN: verifica che il push DNS funzioni
grep "dhcp-option" /var/log/openvpn/server.log
# Se il client ignora push DNS (Linux):
# Installa openvpn-systemd-resolved o usa update-resolv-conf script
script-security 2
up /etc/openvpn/update-resolv-conf
down /etc/openvpn/update-resolv-conf
```

### WireGuard: Peer Rimosso ma Traffico Ancora Presente

```bash
# wg set rimuove il peer dalla configurazione in memoria
# ma il file di configurazione non viene aggiornato automaticamente

# Procedura corretta:
# 1. Rimuovi dalla configurazione in memoria
wg set wg0 peer <chiave_pubblica> remove

# 2. Aggiorna il file di configurazione
# Edita /etc/wireguard/wg0.conf e rimuovi il blocco [Peer]

# Oppure usa syncconf (raccomandato):
wg syncconf wg0 <(wg-quick strip wg0)
# Questo sincronizza la configurazione del file con quella in memoria
# senza interrompere le connessioni esistenti
```

### Tabella Diagnostica Rapida

| Sintomo | Verifica | Causa probabile | Soluzione |
|---------|----------|-----------------|-----------|
| Nessun handshake WG | `wg show`, `ss -ulnp` | Firewall, endpoint errato | Apri UDP 51820, verifica IP |
| TLS handshake failed OVPN | `openssl verify` | CA mismatch, clock skew | Verifica catena cert, sincronizza NTP |
| Ping funziona, TCP no | `ping -M do -s 1400` | MTU troppo alto | Riduci MTU a 1420 |
| DNS non risolve | `resolvectl status` | DNS non configurato nel tunnel | Configura DNS nel tunnel |
| Routing non funziona | `ip route`, `sysctl` | ip_forward=0, MASQUERADE mancante | Abilita forwarding, aggiungi NAT |
| Performance scarse WG | `iperf3` | CPU (userspace), MTU | Verifica kernel module, ottimizza MTU |
| Performance scarse OVPN | `top`, `openssl speed` | Single-thread, no AES-NI | Usa AES-128-GCM, multi-process |
| Client si disconnette | `journalctl -u wg-quick@wg0` | Keepalive assente, NAT timeout | Aggiungi PersistentKeepalive |
| Full tunnel leak IPv6 | `curl -6 ifconfig.me` | AllowedIPs manca ::/0 | Aggiungi `::/0` in AllowedIPs |
| CRL scaduta OVPN | log "CRL has expired" | CRL non rigenerata | `easyrsa gen-crl`, copia, restart |

---

## WireGuard: Internals del Modulo Kernel

### Struttura del Sorgente nel Kernel

Il modulo WireGuard risiede in `net/wireguard/` nel kernel Linux. Dal merge nella mainline (v5.6, marzo 2020), il codice è parte integrante del networking stack. La struttura interna è organizzata in file con responsabilità chiare:

```
net/wireguard/
├── Kconfig            # Opzione di configurazione kernel (CONFIG_WIREGUARD)
├── Makefile           # Build del modulo
├── main.c             # Inizializzazione modulo, registrazione netlink
├── device.c           # Gestione interfaccia di rete virtuale (struct net_device)
├── noise.c            # Implementazione Noise Protocol Framework (handshake)
├── cookie.c           # Meccanismo cookie anti-DoS (MAC1/MAC2)
├── peer.c             # Gestione peer (creazione, distruzione, lookup)
├── allowedips.c       # Trie per il routing basato su AllowedIPs (longest prefix match)
├── queueing.c         # Coda pacchetti per encrypt/decrypt parallelo
├── send.c             # Percorso di trasmissione (encrypt + invio)
├── receive.c          # Percorso di ricezione (ricezione + decrypt)
├── timers.c           # State machine con timer (rekey, keepalive, expiry)
├── ratelimiter.c      # Rate limiting per handshake (protezione DoS)
├── peerlookup.c       # Lookup rapido dei peer via hashtable
├── messages.h         # Definizione strutture messaggi (4 tipi)
└── socket.c           # Gestione socket UDP (bind, send, receive)
```

### I Quattro Tipi di Messaggio

WireGuard definisce solo quattro tipi di messaggio nel protocollo, un'estrema semplificazione rispetto a IPsec (decine di tipi) o OpenVPN:

| Tipo | Nome | Dimensione | Scopo |
|------|------|------------|-------|
| 1 | `MESSAGE_HANDSHAKE_INITIATION` | 148 byte | Primo messaggio dell'handshake (Initiator → Responder) |
| 2 | `MESSAGE_HANDSHAKE_RESPONSE` | 92 byte | Risposta all'handshake (Responder → Initiator) |
| 3 | `MESSAGE_COOKIE_REPLY` | 64 byte | Cookie per resistenza DoS sotto carico |
| 4 | `MESSAGE_DATA` | variabile | Pacchetto dati cifrato (ChaCha20-Poly1305) |

```c
/* Struttura semplificata da messages.h */
struct message_header {
    __le32 type;         /* 1, 2, 3 o 4 */
};

struct message_data {
    struct message_header header;
    __le32 key_idx;      /* Indice della chiave di sessione */
    __le64 counter;      /* Counter per nonce (anti-replay) */
    u8 encrypted_data[]; /* Payload cifrato con ChaCha20-Poly1305 */
};
```

### Trie di AllowedIPs (allowedips.c)

Il cuore del cryptokey routing è un trie compresso (radix tree) che mappa prefissi IP a peer. Quando un pacchetto arriva su `wg0`, il kernel estrae l'IP di destinazione, lo cerca nel trie con longest prefix match e lo inoltra al peer corrispondente. Questa struttura è O(prefix_length) — costante per IPv4 (32 bit) e IPv6 (128 bit), indipendente dal numero di peer.

```bash
# Verifica la struttura del trie in runtime
cat /proc/net/wireguard_allowedips 2>/dev/null || \
    wg show wg0 allowed-ips
# Esempio:
# peer1_pubkey  10.10.0.2/32  fd00:vpn::2/128
# peer2_pubkey  10.10.0.3/32  192.168.10.0/24
```

### Parallelismo nel Data Path

WireGuard utilizza il framework `padata` del kernel per parallelizzare encrypt/decrypt su più core CPU. I pacchetti vengono accodati in batch e distribuiti ai core disponibili, mantenendo l'ordinamento FIFO per-peer. Questo è uno dei motivi principali della superiorità prestazionale rispetto a OpenVPN (single-threaded in userspace).

```bash
# Verifica il parallelismo:
# Su sistemi multi-core, WireGuard usa tutti i core disponibili
cat /proc/interrupts | grep wireguard
# Il modulo registra softirq per la gestione dei pacchetti

# Verifica il modulo caricato e le sue dipendenze
modinfo wireguard
# filename:       /lib/modules/$(uname -r)/kernel/drivers/net/wireguard/wireguard.ko
# depends:        udp_tunnel,ip6_udp_tunnel,curve25519-x86_64,libchacha20poly1305,libblake2s
```

### DKMS per Kernel Personalizzati

Per kernel non standard (custom build, vecchi kernel) è disponibile il modulo out-of-tree via DKMS:

```bash
# Installazione modulo out-of-tree (kernel < 5.6)
apt install wireguard-dkms wireguard-tools

# Verifica compilazione DKMS
dkms status
# wireguard/1.0.20220627, 5.4.0-150-generic, x86_64: installed

# Dopo aggiornamento kernel, DKMS ricompila automaticamente
# Se fallisce:
dkms autoinstall
```

---

## wg-quick: Configurazione Avanzata

### Anatomia di wg-quick

`wg-quick` è uno script bash (`/usr/bin/wg-quick`) che wrappa i comandi `wg`, `ip`, e `resolvconf`/`systemd-resolved`. Comprendere cosa fa internamente permette di diagnosticare problemi e di personalizzare il comportamento.

```bash
# Cosa fa wg-quick up wg0 internamente:
# 1. Legge /etc/wireguard/wg0.conf
# 2. Crea interfaccia:     ip link add wg0 type wireguard
# 3. Applica configurazione: wg setconf wg0 <(wg-quick strip wg0)
# 4. Imposta indirizzo:    ip addr add 10.10.0.1/24 dev wg0
# 5. Imposta MTU:          ip link set wg0 mtu 1420
# 6. Attiva interfaccia:   ip link set wg0 up
# 7. Aggiunge route:       ip route add ... dev wg0
# 8. Configura DNS:        resolvconf -a wg0 -m 0 -x
# 9. Esegue PostUp:        iptables -t nat -A POSTROUTING ...
```

### wg-quick strip e syncconf

`wg-quick strip` rimuove le direttive non-WireGuard (Address, DNS, MTU, PostUp, PostDown, SaveConfig, Table) dal file di configurazione, producendo un output compatibile con `wg setconf`:

```bash
# Mostra la configurazione "pulita" (solo direttive WireGuard)
wg-quick strip wg0
# Output: solo [Interface] con PrivateKey/ListenPort e [Peer] con PublicKey/AllowedIPs/etc.

# Aggiorna la configurazione live SENZA riavviare l'interfaccia
# (le connessioni esistenti non vengono interrotte)
wg syncconf wg0 <(wg-quick strip wg0)

# Pattern: modifica wg0.conf, poi applica
vim /etc/wireguard/wg0.conf   # aggiungi/rimuovi peer
wg syncconf wg0 <(wg-quick strip wg0)   # applica senza downtime
```

### Variabili e Parametri Avanzati

```ini
[Interface]
# Table — controlla in quale tabella di routing vengono inserite le route
# "auto" (default): tabella auto-generata per full tunnel
# "off": non aggiunge route (utile per gestione manuale)
# <numero>: tabella specifica
Table = off

# PreUp / PreDown — eseguiti PRIMA di up/down dell'interfaccia
PreUp = echo "Preparazione VPN..." | logger
PreDown = echo "Arresto VPN..." | logger

# PostUp / PostDown — eseguiti DOPO up/down
# Variabili disponibili: %i = nome interfaccia (wg0)
PostUp = iptables -t nat -A POSTROUTING -o eth0 -s 10.10.0.0/24 -j MASQUERADE; \
         iptables -A FORWARD -i %i -j ACCEPT
PostDown = iptables -t nat -D POSTROUTING -o eth0 -s 10.10.0.0/24 -j MASQUERADE; \
           iptables -D FORWARD -i %i -j ACCEPT

# SaveConfig — se true, wg-quick down salva la configurazione runtime
# ATTENZIONE: sovrascrive commenti e formattazione
SaveConfig = false

# DNS — può specificare anche domini di ricerca
DNS = 10.10.0.53, vpn.internal
```

### Hook con PostUp per Logging

```ini
[Interface]
Address = 10.10.0.1/24
PrivateKey = ...
ListenPort = 51820

# Log ogni connessione/disconnessione peer
PostUp = iptables -A INPUT -p udp --dport 51820 -j LOG --log-prefix "WG-CONN: " --log-level 4
PostUp = echo "WireGuard wg0 attivato $(date -Iseconds)" >> /var/log/wireguard-events.log

PostDown = echo "WireGuard wg0 disattivato $(date -Iseconds)" >> /var/log/wireguard-events.log
```

### Gestione Multipla Interfacce

```bash
# È possibile avere più interfacce WireGuard contemporanee
# Esempio: wg0 per road warrior, wg1 per site-to-site

# /etc/wireguard/wg0.conf — porta 51820, subnet 10.10.0.0/24
# /etc/wireguard/wg1.conf — porta 51821, subnet 10.20.0.0/24

systemctl enable wg-quick@wg0
systemctl enable wg-quick@wg1

# Stato di tutte le interfacce
wg show all
```

---

## Topologie Multi-Peer

### Hub-and-Spoke (Stella)

La topologia più comune: un server centrale (hub) con tutti i client (spoke) che si connettono ad esso. Tutto il traffico inter-client passa per l'hub.

```
         ┌────────┐
    ┌────│  Hub   │────┐
    │    │ Server │    │
    │    └───┬────┘    │
    │        │         │
    ▼        ▼         ▼
┌──────┐ ┌──────┐ ┌──────┐
│Spoke1│ │Spoke2│ │Spoke3│
│Client│ │Client│ │Client│
└──────┘ └──────┘ └──────┘
```

```ini
# Hub server — ogni spoke è un peer con il proprio /32
[Interface]
Address = 10.10.0.1/24
ListenPort = 51820
PrivateKey = <hub_private>

[Peer]  # Spoke 1
PublicKey = <spoke1_pub>
AllowedIPs = 10.10.0.2/32

[Peer]  # Spoke 2
PublicKey = <spoke2_pub>
AllowedIPs = 10.10.0.3/32

[Peer]  # Spoke 3
PublicKey = <spoke3_pub>
AllowedIPs = 10.10.0.4/32
```

**Vantaggi:** Semplice da gestire, un solo endpoint pubblico necessario, controllo centralizzato del traffico.
**Svantaggi:** Single point of failure, tutto il traffico inter-client attraversa l'hub, latenza raddoppiata per traffico spoke-to-spoke.

### Full Mesh

Ogni nodo ha un tunnel diretto verso ogni altro nodo. Ideale per pochi nodi (3-8) dove la latenza diretta è critica.

```
┌──────┐───────────────────┌──────┐
│Nodo A│                   │Nodo B│
└──┬───┘───────────────────└──┬───┘
   │  ╲                    ╱  │
   │    ╲                ╱    │
   │      ╲            ╱      │
   │        ╲        ╱        │
   │          ╲    ╱          │
   │            ╲╱            │
   │            ╱╲            │
└──┴───┐────╱────╲────┌──┴───┘
│Nodo C│              │Nodo D│
└──────┘──────────────└──────┘
```

```bash
# Con N nodi servono N*(N-1)/2 tunnel
# 4 nodi = 6 tunnel, 8 nodi = 28 tunnel, 16 nodi = 120 tunnel
# → Full mesh non scala oltre ~8-10 nodi senza automazione

# Script per generare configurazione full mesh
#!/bin/bash
NODES=("nodeA:10.10.0.1:pub_a:endpoint_a" "nodeB:10.10.0.2:pub_b:endpoint_b" ...)

for node in "${NODES[@]}"; do
    IFS=':' read -r name ip pub ep <<< "$node"
    echo "[Interface]"
    echo "Address = $ip/24"
    echo "PrivateKey = <$name privkey>"
    echo ""
    for peer in "${NODES[@]}"; do
        IFS=':' read -r pname pip ppub pep <<< "$peer"
        [[ "$name" == "$pname" ]] && continue
        echo "[Peer]  # $pname"
        echo "PublicKey = $ppub"
        echo "AllowedIPs = $pip/32"
        echo "Endpoint = $pep:51820"
        echo "PersistentKeepalive = 25"
        echo ""
    done
done
```

### Hub-and-Spoke con Relay

Variante ibrida: i client che possono comunicare direttamente lo fanno, altrimenti usano l'hub come relay. Tailscale/Headscale implementano esattamente questo pattern con DERP come relay di fallback.

```ini
# Spoke 1 — ha sia l'hub che lo spoke 2 come peer
# Il traffico verso spoke2 va diretto (se raggiungibile), altrimenti via hub

[Interface]
Address = 10.10.0.2/24
PrivateKey = <spoke1_private>

[Peer]  # Hub (relay e gateway)
PublicKey = <hub_pub>
Endpoint = hub.example.com:51820
AllowedIPs = 10.10.0.1/32, 10.10.0.0/24  # catch-all per subnet
PersistentKeepalive = 25

[Peer]  # Spoke 2 (connessione diretta quando possibile)
PublicKey = <spoke2_pub>
Endpoint = spoke2.example.com:51820
AllowedIPs = 10.10.0.3/32  # più specifico → ha priorità su /24 dell'hub
PersistentKeepalive = 25
```

> **Nota critica:** In WireGuard il routing funziona per longest prefix match sugli AllowedIPs. Il `/32` verso lo spoke 2 ha priorità sul `/24` dell'hub, quindi il traffico verso 10.10.0.3 va direttamente allo spoke 2 se raggiungibile. Se lo spoke 2 non risponde, non c'è failover automatico — WireGuard non ha path selection dinamico (a differenza di Tailscale/DERP).

---

## WireGuard over TCP: udp2raw e wstunnel

### Il Problema: UDP Bloccato

WireGuard funziona esclusivamente su UDP. In reti restrittive (hotel, aeroporti, reti aziendali, paesi con censura) l'UDP è spesso bloccato o fortemente limitato. Esistono due approcci per incapsulare WireGuard in TCP.

### udp2raw: UDP mascherato da TCP

`udp2raw` crea un tunnel che incapsula pacchetti UDP in segmenti TCP falsi (FakeTCP). I firewall vedono una connessione TCP legittima (3-way handshake simulato, numeri di sequenza), ma il contenuto è effettivamente UDP — niente congestion control, niente ritrasmissione. Perfetto per WireGuard che gestisce già la propria affidabilità.

```bash
# Installazione udp2raw
wget https://github.com/wangyu-/udp2raw/releases/download/20230206.0/udp2raw_binaries.tar.gz
tar xzf udp2raw_binaries.tar.gz
cp udp2raw_amd64 /usr/local/bin/udp2raw
chmod +x /usr/local/bin/udp2raw

# ── SERVER ──
# 1. WireGuard ascolta su localhost:51820
# 2. udp2raw ascolta su 0.0.0.0:443 (TCP) e inoltra a localhost:51820 (UDP)

# Modifica wg0.conf: ListenPort rimane 51820, ma WG ascolta solo su localhost
# (il traffico arriva da udp2raw, non direttamente dall'esterno)

udp2raw -s -l 0.0.0.0:443 -r 127.0.0.1:51820 \
    --raw-mode faketcp \
    -k "chiave_condivisa_segreta" \
    --cipher-mode xor \
    --auth-mode simple \
    -a

# ── CLIENT ──
# 1. udp2raw apre un tunnel TCP verso il server:443
# 2. Espone una porta UDP locale (es. 51821) per WireGuard

udp2raw -c -l 127.0.0.1:51821 -r server.example.com:443 \
    --raw-mode faketcp \
    -k "chiave_condivisa_segreta" \
    --cipher-mode xor \
    --auth-mode simple \
    -a

# 3. WireGuard client punta a localhost:51821 invece che al server remoto
# /etc/wireguard/wg0.conf (client):
# [Peer]
# Endpoint = 127.0.0.1:51821
# (tutto il resto rimane uguale)
```

### Servizio systemd per udp2raw

```ini
# /etc/systemd/system/udp2raw-server.service
[Unit]
Description=udp2raw tunnel (server mode)
After=network.target
Before=wg-quick@wg0.service

[Service]
Type=simple
ExecStart=/usr/local/bin/udp2raw -s \
    -l 0.0.0.0:443 -r 127.0.0.1:51820 \
    --raw-mode faketcp \
    -k "chiave_condivisa_segreta" \
    --cipher-mode xor --auth-mode simple -a
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
```

### wstunnel: WebSocket Tunnel

`wstunnel` incapsula il traffico UDP in un tunnel WebSocket (wss://), rendendolo indistinguibile dal traffico HTTPS standard. È più resistente alla deep packet inspection rispetto a udp2raw.

```bash
# Installazione wstunnel
wget https://github.com/erebe/wstunnel/releases/latest/download/wstunnel_linux_amd64
chmod +x wstunnel_linux_amd64
mv wstunnel_linux_amd64 /usr/local/bin/wstunnel

# ── SERVER ──
# wstunnel ascolta su HTTPS:443 e inoltra UDP a localhost:51820
wstunnel server \
    --restrict-to 127.0.0.1:51820 \
    wss://0.0.0.0:443 \
    --tls-certificate /etc/letsencrypt/live/vpn.example.com/fullchain.pem \
    --tls-private-key /etc/letsencrypt/live/vpn.example.com/privkey.pem

# ── CLIENT ──
# wstunnel apre tunnel locale UDP:51821 → server WebSocket → server WG
wstunnel client \
    --local-to-remote 'udp://51821:127.0.0.1:51820' \
    wss://vpn.example.com:443

# WireGuard client:
# [Peer]
# Endpoint = 127.0.0.1:51821
```

### Confronto udp2raw vs wstunnel

| Caratteristica | udp2raw | wstunnel |
|---------------|---------|----------|
| Protocollo tunnel | FakeTCP / ICMP | WebSocket (wss://) |
| Resistenza DPI | Media (FakeTCP non è TCP vero) | Alta (WebSocket legittimo) |
| Overhead | Basso (~20-30 byte) | Medio (~40-60 byte per frame WS) |
| Certificato TLS | Non necessario | Sì (per wss://) |
| Performance | Migliore (meno overhead) | Buona |
| Complessità setup | Bassa | Media |
| Caso d'uso ideale | Firewall che bloccano UDP | DPI che analizza i protocolli |

---

## OpenVPN: tls-crypt-v2 (Chiavi Per-Client)

### Evoluzione: tls-auth → tls-crypt → tls-crypt-v2

La protezione del control channel OpenVPN si è evoluta in tre generazioni:

1. **tls-auth**: HMAC statico condiviso. Autentica i pacchetti del control channel, previene DoS. Limite: una singola chiave per tutti i client — se compromessa, tutti sono esposti.

2. **tls-crypt**: Cifra e autentica il control channel. Nasconde l'handshake TLS da DPI. Stesso limite: chiave statica condivisa.

3. **tls-crypt-v2** (OpenVPN 2.5+): Ogni client ha la propria chiave, wrappata (cifrata) con la server key. Il server può decifrare la client key on-the-fly senza memorizzarla. Se un client è compromesso, solo quel client è esposto.

### Generazione e Configurazione

```bash
# 1. Genera la chiave server tls-crypt-v2
openvpn --genkey tls-crypt-v2-server /etc/openvpn/server/tls-crypt-v2-server.key

# 2. Genera una chiave per-client (wrappata con la server key)
openvpn --tls-crypt-v2 /etc/openvpn/server/tls-crypt-v2-server.key \
    --genkey tls-crypt-v2-client /etc/openvpn/clients/alice-tls-crypt-v2.key

# La chiave client contiene:
# - Client key (unica per questo client)
# - Wrapped metadata (cifrato con server key — server può leggerlo)

# 3. Opzionale: aggiungi metadata al client key (identificazione)
openvpn --tls-crypt-v2 /etc/openvpn/server/tls-crypt-v2-server.key \
    --genkey tls-crypt-v2-client /etc/openvpn/clients/bob-tls-crypt-v2.key \
    --tls-crypt-v2-genkey-metadata "user=bob,dept=engineering,issued=2026-05-24"
```

```conf
# server.conf — usa la server key
tls-crypt-v2 /etc/openvpn/server/tls-crypt-v2-server.key

# client.ovpn — usa la client key (o inline)
tls-crypt-v2 /path/to/alice-tls-crypt-v2.key

# Oppure inline nel file .ovpn:
<tls-crypt-v2>
-----BEGIN OpenVPN tls-crypt-v2 client key-----
# ... contenuto della chiave ...
-----END OpenVPN tls-crypt-v2 client key-----
</tls-crypt-v2>
```

### Verifica Server-Side con tls-crypt-v2-verify

```bash
#!/bin/bash
# /etc/openvpn/verify-tls-crypt-v2.sh
# Script richiamato da OpenVPN per validare i metadata della client key

METADATA="$1"

# Estrai campi dai metadata
user=$(echo "$METADATA" | grep -oP 'user=\K[^,]+')
issued=$(echo "$METADATA" | grep -oP 'issued=\K[^,]+')

# Esempio: rifiuta chiavi emesse più di 365 giorni fa
issued_epoch=$(date -d "$issued" +%s 2>/dev/null || echo 0)
now_epoch=$(date +%s)
age_days=$(( (now_epoch - issued_epoch) / 86400 ))

if (( age_days > 365 )); then
    echo "REJECT: chiave scaduta (emessa $age_days giorni fa)" >&2
    exit 1
fi

echo "ACCEPT: user=$user, issued=$issued, age=${age_days}d"
exit 0
```

```conf
# server.conf
tls-crypt-v2 /etc/openvpn/server/tls-crypt-v2-server.key
tls-crypt-v2-verify /etc/openvpn/verify-tls-crypt-v2.sh
script-security 2
```

### Migrazione da tls-crypt a tls-crypt-v2

```bash
# 1. Genera la nuova server key v2
openvpn --genkey tls-crypt-v2-server /etc/openvpn/server/tls-crypt-v2-server.key

# 2. Genera chiavi v2 per tutti i client esistenti
for client in /etc/openvpn/clients/*.ovpn; do
    name=$(basename "$client" .ovpn)
    openvpn --tls-crypt-v2 /etc/openvpn/server/tls-crypt-v2-server.key \
        --genkey tls-crypt-v2-client "/etc/openvpn/clients/${name}-v2.key"
done

# 3. Aggiorna server.conf: sostituisci "tls-crypt" con "tls-crypt-v2"
# 4. Distribuisci le nuove chiavi ai client
# 5. Aggiorna i file .ovpn: sostituisci <tls-crypt> con <tls-crypt-v2>
# NOTA: i client con la vecchia chiave tls-crypt non potranno connettersi
# → pianifica una finestra di migrazione
```

---

## OpenVPN Access Server

### Differenza: Community vs Access Server

OpenVPN esiste in due varianti:
- **Community Edition (CE)**: open source, gratuito, configurazione manuale tramite file di testo. Quello trattato nelle sezioni precedenti.
- **Access Server (AS)**: versione commerciale con interfaccia web di amministrazione, gestione utenti integrata, client pre-configurati e supporto professionale.

### Installazione su Ubuntu/Debian

```bash
# Aggiungi repository ufficiale OpenVPN Access Server
apt update && apt install -y ca-certificates wget net-tools gnupg
wget https://as-repository.openvpn.net/as-repo-public.asc -qO /etc/apt/trusted.gpg.d/as-repo.asc
echo "deb [arch=amd64] http://as-repository.openvpn.net/as/debian $(lsb_release -cs) main" \
    > /etc/apt/sources.list.d/openvpn-as.list

# Installa
apt update && apt install -y openvpn-as

# L'output mostra:
# Admin  UI: https://<IP>:943/admin
# Client UI: https://<IP>:943/
# Login: openvpn / <password_random>
```

### Amministrazione via CLI

```bash
# Cambio password admin
/usr/local/openvpn_as/scripts/sacli --user openvpn --new_pass 'NuovaPassword!' SetLocalPassword

# Aggiungi utente
/usr/local/openvpn_as/scripts/sacli --user alice --new_pass 'AlicePass!' SetLocalPassword
/usr/local/openvpn_as/scripts/sacli --user alice --key "type" --value "user_connect" UserPropPut

# Lista utenti connessi
/usr/local/openvpn_as/scripts/sacli VPNStatus

# Configura subnet VPN
/usr/local/openvpn_as/scripts/sacli --key "vpn.daemon.0.server.network" --value "10.8.0.0" ConfigPut
/usr/local/openvpn_as/scripts/sacli --key "vpn.daemon.0.server.netmask_bits" --value "24" ConfigPut

# Configura routing (push reti ai client)
/usr/local/openvpn_as/scripts/sacli --key "vpn.server.routing.private_network.0" \
    --value "10.0.0.0/8" ConfigPut

# Applica modifiche
/usr/local/openvpn_as/scripts/sacli start
```

### Licensing e Limiti

| Piano | Connessioni Simultanee | Prezzo (indicativo 2025) |
|-------|----------------------|--------------------------|
| Free | 2 | Gratuito |
| Subscription | 10-10.000+ | ~$15/connessione/anno |

> **Nota operativa:** Per la maggior parte degli scenari, la Community Edition con gestione certificati manuale è preferibile: costo zero, pieno controllo, nessun vendor lock-in. Access Server ha senso quando serve una GUI per amministratori non-CLI o gestione utenti integrata con LDAP/SAML senza scrivere plugin custom.

---

## VPN Performance Benchmarking

### Metodologia di Test con iperf3

Un benchmark VPN affidabile richiede una metodologia rigorosa. Misurare "la velocità della VPN" senza controllare le variabili produce dati inutili.

```bash
# ── SETUP ──
# Server iperf3 dietro la VPN (sulla rete remota)
iperf3 -s -p 5201

# ── TEST TCP THROUGHPUT ──
# Dal client VPN, attraverso il tunnel
iperf3 -c 10.10.0.1 -p 5201 -t 30 -P 4 --json > vpn_tcp_result.json
# -t 30: durata 30 secondi (minimo per risultati stabili)
# -P 4: 4 stream paralleli (simula traffico reale)
# --json: output parsabile

# ── TEST UDP THROUGHPUT ──
iperf3 -c 10.10.0.1 -p 5201 -u -b 1G -t 30 --json > vpn_udp_result.json
# -u: modalità UDP
# -b 1G: target bandwidth 1 Gbps (saturazione)

# ── BASELINE (senza VPN, stessa rete) ──
iperf3 -c <ip_diretto_server> -p 5201 -t 30 -P 4 --json > baseline_result.json

# ── CALCOLO OVERHEAD ──
# overhead = (1 - throughput_vpn / throughput_baseline) * 100
```

### Script di Benchmark Automatizzato

```bash
#!/bin/bash
# vpn-benchmark.sh — Confronto performance WireGuard vs OpenVPN vs baseline

set -euo pipefail

SERVER_IP_VPN_WG="10.10.0.1"     # Server via WireGuard
SERVER_IP_VPN_OV="10.8.0.1"      # Server via OpenVPN
SERVER_IP_DIRECT="192.168.1.100"  # Server diretto (baseline)
DURATION=30
STREAMS=4
RESULTS_DIR="./vpn-bench-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RESULTS_DIR"

run_test() {
    local label="$1" server="$2" proto="$3"
    local outfile="${RESULTS_DIR}/${label}_${proto}.json"
    
    echo "[$label] Test $proto verso $server..."
    
    if [[ "$proto" == "tcp" ]]; then
        iperf3 -c "$server" -t "$DURATION" -P "$STREAMS" --json > "$outfile"
    else
        iperf3 -c "$server" -t "$DURATION" -u -b 1G --json > "$outfile"
    fi
    
    # Estrai throughput
    local bps
    if [[ "$proto" == "tcp" ]]; then
        bps=$(jq '.end.sum_received.bits_per_second' "$outfile")
    else
        bps=$(jq '.end.sum.bits_per_second' "$outfile")
    fi
    local mbps=$(echo "scale=2; $bps / 1000000" | bc)
    echo "[$label] $proto: ${mbps} Mbps"
}

# Test latenza
echo "=== LATENZA ==="
for label_server in "baseline:$SERVER_IP_DIRECT" "wireguard:$SERVER_IP_VPN_WG" "openvpn:$SERVER_IP_VPN_OV"; do
    IFS=':' read -r label server <<< "$label_server"
    avg_rtt=$(ping -c 20 -q "$server" 2>/dev/null | grep 'avg' | cut -d'/' -f5)
    echo "[$label] RTT medio: ${avg_rtt}ms"
done

# Test throughput
echo "=== THROUGHPUT TCP ==="
run_test "baseline" "$SERVER_IP_DIRECT" "tcp"
run_test "wireguard" "$SERVER_IP_VPN_WG" "tcp"
run_test "openvpn" "$SERVER_IP_VPN_OV" "tcp"

echo "=== THROUGHPUT UDP ==="
run_test "baseline" "$SERVER_IP_DIRECT" "udp"
run_test "wireguard" "$SERVER_IP_VPN_WG" "udp"
run_test "openvpn" "$SERVER_IP_VPN_OV" "udp"

# CPU durante il test
echo "=== CPU USAGE (VPN server) ==="
echo "Eseguire sul server VPN durante il test:"
echo "  pidstat -p \$(pidof openvpn) 1 30"
echo "  mpstat -P ALL 1 30  # per WireGuard (kernel, non ha PID visibile)"

echo "Risultati salvati in: $RESULTS_DIR/"
```

### Risultati Tipici (Hardware x86-64 Moderno)

| Metrica | Baseline (no VPN) | WireGuard | OpenVPN (AES-256-GCM) | OpenVPN (ChaCha20) |
|---------|-------------------|-----------|----------------------|-------------------|
| TCP throughput (1 stream) | ~940 Mbps | ~880 Mbps | ~450 Mbps | ~380 Mbps |
| TCP throughput (4 stream) | ~940 Mbps | ~920 Mbps | ~520 Mbps | ~440 Mbps |
| UDP throughput | ~940 Mbps | ~900 Mbps | ~480 Mbps | ~400 Mbps |
| RTT overhead | 0 ms | +0.1-0.3 ms | +0.5-1.5 ms | +0.5-1.5 ms |
| CPU @ 500 Mbps | ~2% | ~15% (kernel) | ~65% (1 core) | ~75% (1 core) |

> **Nota:** Questi valori sono indicativi e variano enormemente in base a CPU (AES-NI presente?), tipo di virtualizzazione (bare metal vs VM vs container), latenza della rete sottostante e dimensione dei pacchetti. L'unica misura affidabile è il benchmark sul proprio hardware specifico.

### Profilazione CPU

```bash
# Identificare il bottleneck CPU su OpenVPN
perf top -p $(pidof openvpn)
# I simboli principali saranno EVP_EncryptUpdate, EVP_DecryptUpdate (OpenSSL)

# Per WireGuard (kernel space)
perf top -g
# Cercare simboli come chacha20_encrypt, poly1305_update

# Monitoraggio real-time CPU per processo
pidstat -p $(pidof openvpn) -u 1
# %CPU indica l'utilizzo su un singolo core
# Se raggiunge ~100%, OpenVPN è CPU-bound (single-threaded)
```

---

## DNS Leak Prevention Avanzata

### Architettura delle Leak DNS

Un DNS leak avviene quando le query DNS escono al di fuori del tunnel VPN, rivelando i siti visitati all'ISP o alla rete locale anche quando la VPN è attiva.

```
Scenario leak:
┌────────────┐       ┌──────────────────┐
│   Client   │──DNS──│ ISP DNS (fuori   │ ← LEAK: ISP vede le query
│   con VPN  │       │ dal tunnel VPN)  │
│            │──VPN──│ VPN Server       │ ← traffico dati cifrato
└────────────┘       └──────────────────┘

Scenario corretto:
┌────────────┐       ┌──────────────────┐
│   Client   │──VPN──│ VPN Server       │
│   con VPN  │       │  └── DNS interno │ ← DNS dentro il tunnel
└────────────┘       └──────────────────┘
```

### DNS over HTTPS (DoH) e DNS over TLS (DoT) nel Tunnel

Combinare una VPN con DoH/DoT aggiunge un ulteriore livello di protezione: anche se il DNS uscisse dal tunnel, le query sarebbero cifrate.

```bash
# Configura systemd-resolved per usare DoT dentro il tunnel VPN
mkdir -p /etc/systemd/resolved.conf.d/

cat > /etc/systemd/resolved.conf.d/vpn-dot.conf <<'EOF'
[Resolve]
# DNS server raggiungibili solo via VPN
DNS=10.10.0.53#dns.vpn.internal
FallbackDNS=
# Forza DoT per tutte le query
DNSOverTLS=yes
# Non usare mai DNS dalla DHCP locale quando VPN è attiva
LLMNR=no
MulticastDNS=no
EOF

systemctl restart systemd-resolved

# Verifica
resolvectl status
# Global:
#   DNS Servers: 10.10.0.53
#   DNSOverTLS: yes
```

### Split DNS: Risoluzioni Diverse per Domini Diversi

```bash
# Configura split DNS: domini interni via DNS del tunnel, il resto via DoH pubblico
resolvectl dns wg0 10.10.0.53
resolvectl domain wg0 '~internal.corp' '~vpn.local'

# Solo i domini *.internal.corp e *.vpn.local usano il DNS del tunnel
# Tutto il resto usa il DNS di sistema (es. 1.1.1.1 via DoH)

# Verifica quale DNS viene usato per un dominio specifico
resolvectl query server.internal.corp
# → risolto tramite 10.10.0.53 (wg0)

resolvectl query example.com
# → risolto tramite DNS di sistema
```

### Test Completo di Leak

```bash
#!/bin/bash
# dns-leak-check.sh — Verifica assenza di DNS leak

echo "=== DNS LEAK CHECK ==="

# 1. Verifica DNS in uso
echo "[1] DNS resolver attuale:"
resolvectl status 2>/dev/null | grep "DNS Servers" || cat /etc/resolv.conf | grep nameserver

# 2. Query DNS e verifica che passi per il tunnel
echo "[2] Test DNS query routing:"
dns_server_used=$(dig +short +identify whoami.akamai.net @ns1-1.akamaitech.net 2>/dev/null | head -1)
echo "    Query DNS risolta da: $dns_server_used"
echo "    (Deve essere l'IP del server VPN, non l'IP del client)"

# 3. Test DNS IPv6
echo "[3] Test DNS IPv6 leak:"
dns_v6=$(dig -6 +short AAAA example.com 2>/dev/null)
if [[ -n "$dns_v6" ]]; then
    echo "    WARN: DNS IPv6 risponde — verificare che passi per il tunnel"
else
    echo "    OK: Nessuna risposta DNS IPv6 (o IPv6 disabilitato)"
fi

# 4. Test con servizi di leak check
echo "[4] Verifica IP pubblico:"
echo "    IPv4: $(curl -4 -s ifconfig.me 2>/dev/null || echo 'N/A')"
echo "    IPv6: $(curl -6 -s ifconfig.me 2>/dev/null || echo 'N/A o bloccato')"
echo "    (Entrambi devono mostrare l'IP del server VPN)"
```

---

## Kill Switch: Implementazione Completa

### Kill Switch per OpenVPN

Il kill switch per OpenVPN è diverso da WireGuard perché OpenVPN opera in userspace e ha un PID monitorabile:

```bash
# Kill switch con nftables per OpenVPN
cat > /etc/nftables.d/openvpn-killswitch.nft <<'EOF'
table inet ovpn_killswitch {
    chain output {
        type filter hook output priority 0; policy drop;
        
        # Loopback
        oifname "lo" accept
        
        # Permetti traffico OpenVPN (verso server)
        tcp dport 1194 accept
        udp dport 1194 accept
        # Se il server usa porta 443:
        tcp dport 443 ip daddr <IP_SERVER_VPN> accept
        
        # DHCP
        udp dport 67 accept
        udp sport 68 accept
        
        # Traffico via tun0 (tunnel OpenVPN)
        oifname "tun0" accept
        
        # LAN locale (opzionale — commentare per isolamento totale)
        ip daddr 192.168.0.0/16 accept
        
        # Drop tutto il resto
        log prefix "OVPN-KS-DROP: " counter drop
    }
}
EOF

nft -f /etc/nftables.d/openvpn-killswitch.nft
```

### Kill Switch con systemd (Attivazione Automatica)

```ini
# /etc/systemd/system/vpn-killswitch.service
[Unit]
Description=VPN Kill Switch (nftables)
Before=wg-quick@wg0.service openvpn-client@client.service
After=network-pre.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/sbin/nft -f /etc/nftables.d/vpn-killswitch.nft
ExecStop=/usr/sbin/nft delete table inet vpn_killswitch

[Install]
WantedBy=multi-user.target
```

```bash
# Il kill switch si attiva PRIMA della VPN e si disattiva dopo
systemctl enable vpn-killswitch.service
systemctl start vpn-killswitch.service

# Sequenza: killswitch ON → VPN UP → traffico fluisce via tunnel
# Se VPN cade: killswitch blocca tutto (tranne traffico VPN per riconnessione)
```

### Kill Switch con Network Namespace (Massima Sicurezza)

L'approccio più sicuro: isola completamente il processo in un namespace di rete dove l'unica via di uscita è il tunnel VPN.

```bash
#!/bin/bash
# vpn-namespace-killswitch.sh — Kill switch a prova di leak

# Crea namespace
ip netns add vpn_safe

# Crea coppia veth per collegare namespace al sistema
ip link add veth-vpn type veth peer name veth-ns
ip link set veth-ns netns vpn_safe

# Configura IP
ip addr add 172.30.0.1/30 dev veth-vpn
ip link set veth-vpn up
ip netns exec vpn_safe ip addr add 172.30.0.2/30 dev veth-ns
ip netns exec vpn_safe ip link set veth-ns up
ip netns exec vpn_safe ip link set lo up

# Nel namespace, il default gateway è il veth verso il sistema
ip netns exec vpn_safe ip route add default via 172.30.0.1

# Avvia WireGuard NEL namespace
ip netns exec vpn_safe wg-quick up wg0

# Ora nel namespace, la default route è via wg0
# Se wg0 cade, non c'è fallback — nessun traffico esce

# Esegui applicazioni nel namespace isolato
ip netns exec vpn_safe firefox &
ip netns exec vpn_safe curl ifconfig.me  # → IP del server VPN
```

---

## IPv6 over VPN: Approfondimento

### Dual-Stack Completo

Una configurazione VPN dual-stack corretta richiede attenzione su entrambe le pile protocollari:

```ini
# Server WireGuard — dual-stack completo
[Interface]
Address = 10.10.0.1/24, fd00:wg::1/64
ListenPort = 51820
PrivateKey = ...

# NAT per IPv4, routing diretto per IPv6 (ULA)
PostUp = iptables -t nat -A POSTROUTING -o eth0 -s 10.10.0.0/24 -j MASQUERADE
PostUp = ip6tables -A FORWARD -i wg0 -j ACCEPT
PostUp = ip6tables -A FORWARD -o wg0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
PostDown = iptables -t nat -D POSTROUTING -o eth0 -s 10.10.0.0/24 -j MASQUERADE
PostDown = ip6tables -D FORWARD -i wg0 -j ACCEPT
PostDown = ip6tables -D FORWARD -o wg0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

[Peer]
PublicKey = ...
AllowedIPs = 10.10.0.2/32, fd00:wg::2/128
```

### Disabilitare IPv6 Fuori dal Tunnel

Se l'obiettivo è evitare leak IPv6 ma non si vuole tunnelizzare IPv6, la soluzione è disabilitare IPv6 sulle interfacce fisiche:

```bash
# Disabilita IPv6 su tutte le interfacce tranne wg0 e lo
cat > /etc/sysctl.d/99-disable-ipv6-except-vpn.conf <<'EOF'
net.ipv6.conf.default.disable_ipv6 = 1
net.ipv6.conf.all.disable_ipv6 = 1
# Riabilita su loopback e WireGuard
net.ipv6.conf.lo.disable_ipv6 = 0
net.ipv6.conf.wg0.disable_ipv6 = 0
EOF

sysctl -p /etc/sysctl.d/99-disable-ipv6-except-vpn.conf
```

### IPv6 Privacy Extensions e VPN

Le privacy extensions di IPv6 (RFC 8981) generano indirizzi temporanei per la privacy. Dentro un tunnel VPN con ULA (`fd00::/8`) le privacy extensions sono generalmente inutili (la rete è già privata) e possono complicare il debugging:

```bash
# Disabilita privacy extensions sull'interfaccia VPN
echo 0 > /proc/sys/net/ipv6/conf/wg0/use_tempaddr
# Oppure:
sysctl -w net.ipv6.conf.wg0.use_tempaddr=0
```

### NAT66: Perché Evitarlo

A differenza di IPv4, IPv6 è progettato per funzionare senza NAT. Usare NAT66 (ip6tables MASQUERADE per IPv6) nel tunnel VPN è un anti-pattern che elimina i vantaggi di IPv6 (end-to-end connectivity, tracciabilità del percorso). La soluzione corretta è usare:

- **ULA (Unique Local Addresses)** `fd00::/8` per la rete interna VPN
- **GUA (Global Unicast Addresses)** con prefisso delegato dal provider se serve accesso IPv6 globale dal tunnel
- **Routing diretto** senza NAT, con firewall per filtrare il traffico

---

## Rotazione Automatizzata delle Chiavi

### Perché Ruotare

A differenza dei certificati X.509 (che hanno una scadenza incorporata), le chiavi WireGuard non scadono mai. Senza rotazione esplicita, una chiave compromessa rimane valida indefinitamente. Le best practice attuali raccomandano rotazione ogni 90 giorni per ambienti standard, 30 giorni per ambienti ad alta sicurezza.

### Script di Rotazione con Rollback

```bash
#!/bin/bash
# wg-rotate-keys.sh — Rotazione chiavi WireGuard con rollback
# Uso: ./wg-rotate-keys.sh <peer_name>

set -euo pipefail

PEER_NAME="${1:?Uso: $0 <peer_name>}"
WG_CONF="/etc/wireguard/wg0.conf"
BACKUP_DIR="/etc/wireguard/backups"
CLIENT_DIR="/etc/wireguard/clients"
SERVER_PUBKEY=$(cat /etc/wireguard/server_public.key)
SERVER_ENDPOINT="vpn.example.com:51820"

# Backup configurazione corrente
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="${BACKUP_DIR}/wg0.conf.$(date +%Y%m%d-%H%M%S).bak"
cp "$WG_CONF" "$BACKUP_FILE"
echo "Backup salvato: $BACKUP_FILE"

# Genera nuove chiavi
NEW_PRIVATE=$(wg genkey)
NEW_PUBLIC=$(echo "$NEW_PRIVATE" | wg pubkey)
NEW_PSK=$(wg genpsk)

# Trova la vecchia chiave pubblica del peer
OLD_PUBKEY=$(grep -A1 "# ${PEER_NAME}" "$WG_CONF" | grep "PublicKey" | awk '{print $3}')

if [[ -z "$OLD_PUBKEY" ]]; then
    echo "Errore: peer '$PEER_NAME' non trovato in $WG_CONF" >&2
    exit 1
fi

# Trova l'IP del peer
PEER_IP=$(grep -A5 "# ${PEER_NAME}" "$WG_CONF" | grep "AllowedIPs" | awk '{print $3}' | cut -d'/' -f1)

# Aggiorna la configurazione server
sed -i "s|PublicKey = ${OLD_PUBKEY}|PublicKey = ${NEW_PUBLIC}|" "$WG_CONF"
# Aggiorna PSK se presente
OLD_PSK_LINE=$(grep -A3 "# ${PEER_NAME}" "$WG_CONF" | grep "PresharedKey" || true)
if [[ -n "$OLD_PSK_LINE" ]]; then
    OLD_PSK=$(echo "$OLD_PSK_LINE" | awk '{print $3}')
    sed -i "s|PresharedKey = ${OLD_PSK}|PresharedKey = ${NEW_PSK}|" "$WG_CONF"
fi

# Applica senza downtime
if wg syncconf wg0 <(wg-quick strip wg0) 2>/dev/null; then
    echo "Chiavi aggiornate sul server per '$PEER_NAME'"
else
    echo "Errore applicazione config — rollback" >&2
    cp "$BACKUP_FILE" "$WG_CONF"
    wg syncconf wg0 <(wg-quick strip wg0)
    exit 1
fi

# Genera nuova configurazione client
CLIENT_CONF="${CLIENT_DIR}/${PEER_NAME}.conf"
cat > "$CLIENT_CONF" <<EOF
[Interface]
Address = ${PEER_IP}/24
PrivateKey = ${NEW_PRIVATE}
DNS = 1.1.1.1

[Peer]
PublicKey = ${SERVER_PUBKEY}
PresharedKey = ${NEW_PSK}
Endpoint = ${SERVER_ENDPOINT}
AllowedIPs = 10.10.0.0/24
PersistentKeepalive = 25
EOF
chmod 600 "$CLIENT_CONF"

# Log rotazione
echo "$(date -Iseconds) ROTATED peer=$PEER_NAME old_pub=${OLD_PUBKEY:0:8}... new_pub=${NEW_PUBLIC:0:8}..." \
    >> /var/log/wireguard-key-rotation.log

echo "Nuova configurazione client: $CLIENT_CONF"
echo "Distribuire al client e riconnettere."
echo "QR code: qrencode -t ansiutf8 < $CLIENT_CONF"
```

### Automazione con cron

```bash
# Rotazione trimestrale automatica di tutti i peer
# /etc/cron.d/wg-key-rotation
0 3 1 */3 * root /usr/local/bin/wg-rotate-all-keys.sh >> /var/log/wg-rotation-cron.log 2>&1
```

```bash
#!/bin/bash
# wg-rotate-all-keys.sh — Ruota tutte le chiavi peer
PEERS=$(grep -oP '# \K\S+' /etc/wireguard/wg0.conf | sort -u)
for peer in $PEERS; do
    echo "=== Rotazione: $peer ==="
    /usr/local/bin/wg-rotate-keys.sh "$peer"
    echo ""
done

# Notifica (opzionale)
echo "Rotazione chiavi completata per $(echo "$PEERS" | wc -w) peer il $(date -Iseconds)" \
    | mail -s "[VPN] Rotazione chiavi completata" admin@example.com
```

---

## Monitoring VPN con Prometheus e Grafana

### OpenVPN Exporter

Oltre al WireGuard exporter (già trattato in sezione precedente), esiste un exporter dedicato per OpenVPN:

```bash
# openvpn_exporter — legge il file status.log di OpenVPN
# Installazione
wget https://github.com/kumina/openvpn_exporter/releases/latest/download/openvpn_exporter-linux-amd64
chmod +x openvpn_exporter-linux-amd64
mv openvpn_exporter-linux-amd64 /usr/local/bin/openvpn_exporter

# Esecuzione
openvpn_exporter -openvpn.status_paths /var/log/openvpn/status.log -web.listen-address :9176

# Metriche esposte:
# openvpn_server_connected_clients     — numero client connessi
# openvpn_server_route_bytes_in_total  — byte ricevuti per route
# openvpn_server_route_bytes_out_total — byte trasmessi per route
# openvpn_up                          — 1 se il server è attivo

# prometheus.yml
scrape_configs:
  - job_name: openvpn
    static_configs:
      - targets: ['vpn-server:9176']
```

### Dashboard Grafana per VPN

```json
{
  "dashboard": {
    "title": "VPN Monitoring",
    "panels": [
      {
        "title": "WireGuard — Peer Connessi",
        "type": "stat",
        "targets": [{"expr": "count(time() - wireguard_peer_last_handshake_seconds < 300)"}]
      },
      {
        "title": "WireGuard — Traffico per Peer",
        "type": "timeseries",
        "targets": [
          {"expr": "rate(wireguard_peer_receive_bytes_total[5m]) * 8", "legendFormat": "{{public_key}} RX"},
          {"expr": "rate(wireguard_peer_transmit_bytes_total[5m]) * 8", "legendFormat": "{{public_key}} TX"}
        ]
      },
      {
        "title": "OpenVPN — Client Connessi",
        "type": "stat",
        "targets": [{"expr": "openvpn_server_connected_clients"}]
      },
      {
        "title": "WireGuard — Ultimo Handshake (Peer più vecchio)",
        "type": "gauge",
        "targets": [{"expr": "max(time() - wireguard_peer_last_handshake_seconds)"}],
        "thresholds": {"steps": [
          {"color": "green", "value": 0},
          {"color": "yellow", "value": 180},
          {"color": "red", "value": 300}
        ]}
      },
      {
        "title": "Throughput Totale VPN",
        "type": "timeseries",
        "targets": [
          {"expr": "sum(rate(wireguard_peer_receive_bytes_total[5m])) * 8", "legendFormat": "WG RX bps"},
          {"expr": "sum(rate(wireguard_peer_transmit_bytes_total[5m])) * 8", "legendFormat": "WG TX bps"}
        ]
      }
    ]
  }
}
```

### Alert Avanzati per Prometheus

```yaml
# Estensione delle regole di alerting (in aggiunta a quelle già presenti)
groups:
  - name: vpn_advanced
    rules:
      - alert: VPNThroughputAnomaly
        expr: |
          abs(
            rate(wireguard_peer_receive_bytes_total[5m]) -
            avg_over_time(rate(wireguard_peer_receive_bytes_total[5m])[7d:1h])
          ) > 2 * stddev_over_time(rate(wireguard_peer_receive_bytes_total[5m])[7d:1h])
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Traffico anomalo per peer {{ $labels.public_key }}"
          description: "Il throughput è più di 2 deviazioni standard dalla media settimanale"

      - alert: OpenVPNServerDown
        expr: openvpn_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "OpenVPN server non raggiungibile"

      - alert: VPNHighClientCount
        expr: openvpn_server_connected_clients > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "OpenVPN si avvicina al limite client ({{ $value }}/100)"
```

---

## Client Mobili: iOS e Android

### WireGuard su iOS

L'app ufficiale WireGuard per iOS supporta tre metodi di importazione:

1. **QR Code** (raccomandato): il server genera la configurazione e la mostra come QR.
2. **File .conf**: importabile via AirDrop, Mail, Files app o link diretto.
3. **Creazione manuale**: inserimento diretto dei parametri nell'app.

```bash
# Sul server: genera QR code per un client mobile
apt install qrencode

# Genera configurazione e mostra come QR
qrencode -t ansiutf8 < /etc/wireguard/clients/iphone-alice.conf
# Scansiona il QR con l'app WireGuard su iOS

# Per salvare come immagine PNG:
qrencode -t png -o /tmp/iphone-alice-qr.png < /etc/wireguard/clients/iphone-alice.conf
```

```ini
# Configurazione ottimale per mobile (iOS/Android)
[Interface]
Address = 10.10.0.5/24
PrivateKey = <chiave_privata>
# DNS: usare DNS del tunnel per evitare leak
DNS = 10.10.0.53, 1.1.1.1

[Peer]
PublicKey = <server_pubkey>
PresharedKey = <psk>
Endpoint = vpn.example.com:51820
# Full tunnel per mobile (protegge WiFi pubblico)
AllowedIPs = 0.0.0.0/0, ::/0
# Keepalive più aggressivo per reti mobili instabili
PersistentKeepalive = 15
```

### WireGuard su Android

L'app Android offre le stesse modalità più l'integrazione con il sistema:

```bash
# Configurazione Android-specific:
# - On-demand: l'app può attivarsi automaticamente su reti non fidate
# - Always-on: Android mantiene la VPN attiva in background
# - Per-app VPN: solo app selezionate usano il tunnel

# Impostazioni Android (dopo importazione):
# Settings → Network → VPN → WireGuard → ⚙️
# "Always-on VPN" = ON
# "Block connections without VPN" = ON  ← kill switch nativo Android
```

### OpenVPN Connect su Mobile

```bash
# Genera profilo .ovpn compatibile con OpenVPN Connect (iOS/Android)
# Il file .ovpn deve essere self-contained (inline keys/certs)
# Vedi sezione "Script di Generazione Client Config" per lo script completo

# Dettagli specifici per mobile:
# 1. Usa UDP come protocollo primario (meno overhead, meglio per battery)
# 2. Imposta `connect-retry 5 30` per riconnessione rapida
# 3. Imposta `connect-timeout 30` per reti lente
# 4. Aggiungi `auth-retry interact` per riprovare autenticazione

# Nella configurazione client mobile:
client
dev tun
proto udp
remote vpn.example.com 1194
connect-retry 5 30
connect-timeout 30
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
cipher AES-256-GCM
auth SHA256
verb 3
auth-retry interact
```

### Confronto Esperienza Mobile

| Aspetto | WireGuard | OpenVPN Connect |
|---------|-----------|-----------------|
| Velocità connessione | Istantanea (1-RTT) | 5-15 secondi (TLS handshake) |
| Consumo batteria | Basso (kernel-space, idle=zero traffico) | Medio (userspace, polling) |
| Roaming WiFi↔4G | Seamless (cambio IP trasparente) | Riconnessione necessaria |
| Kill switch nativo | Via OS (Android) o app (iOS) | Via app |
| QR code import | Sì (nativo) | No (solo file .ovpn) |
| Always-on VPN | Sì (Android), On-Demand (iOS) | Sì (entrambi) |
| Per-app tunneling | No (OS-level su Android) | No |
| Dimensione app | ~5 MB | ~15 MB |

> **Raccomandazione mobile:** WireGuard è nettamente superiore per dispositivi mobili: consumo batteria minore, riconnessione istantanea al cambio rete, setup tramite QR code. OpenVPN Connect rimane utile solo quando si deve connettere a un'infrastruttura OpenVPN esistente che non supporta WireGuard.

---

## Confronto IPsec/IKEv2 vs WireGuard

### IPsec con strongSwan: Setup Base

strongSwan è l'implementazione di riferimento per IPsec/IKEv2 su Linux. A differenza di WireGuard, IPsec non è un modulo kernel autonomo ma utilizza il framework XFRM del kernel, con il demone userspace (`charon`) che gestisce IKE.

```bash
# Installazione strongSwan
apt install strongswan strongswan-pki libcharon-extra-plugins

# Genera PKI per IPsec
mkdir -p /etc/ipsec.d/{cacerts,certs,private}

# CA
pki --gen --type rsa --size 4096 --outform pem > /etc/ipsec.d/private/ca-key.pem
pki --self --ca --lifetime 3650 --in /etc/ipsec.d/private/ca-key.pem \
    --type rsa --dn "CN=VPN CA" --outform pem > /etc/ipsec.d/cacerts/ca-cert.pem

# Server certificate
pki --gen --type rsa --size 4096 --outform pem > /etc/ipsec.d/private/server-key.pem
pki --req --type rsa --in /etc/ipsec.d/private/server-key.pem \
    --dn "CN=vpn.example.com" --san vpn.example.com --outform pem | \
    pki --issue --lifetime 365 --cacert /etc/ipsec.d/cacerts/ca-cert.pem \
    --cakey /etc/ipsec.d/private/ca-key.pem \
    --flag serverAuth --flag ikeIntermediate --outform pem \
    > /etc/ipsec.d/certs/server-cert.pem
```

```conf
# /etc/ipsec.conf — configurazione base IKEv2
config setup
    charondebug="ike 2, knl 2, cfg 2"

conn ikev2-vpn
    auto=add
    type=tunnel
    keyexchange=ikev2
    
    # Algoritmi
    ike=aes256gcm16-sha384-ecp384!
    esp=aes256gcm16-sha384!
    
    # Server
    left=%any
    leftid=@vpn.example.com
    leftcert=server-cert.pem
    leftsendcert=always
    leftsubnet=0.0.0.0/0
    
    # Client
    right=%any
    rightid=%any
    rightauth=eap-mschapv2
    rightsourceip=10.9.0.0/24
    rightdns=1.1.1.1,8.8.8.8
    
    # Opzioni
    fragmentation=yes
    rekey=no
    dpdaction=clear
    dpddelay=300s
    dpdtimeout=60s
```

### Confronto Tecnico Dettagliato

| Aspetto | WireGuard | IPsec/IKEv2 (strongSwan) |
|---------|-----------|---------------------------|
| **Codebase kernel** | ~4.000 righe (modulo dedicato) | Framework XFRM (~30.000 righe) + charon userspace |
| **Configurazione** | File INI semplice (~20 righe) | ipsec.conf + swanctl.conf + PKI (~100+ righe) |
| **Handshake** | 1-RTT (Noise IK) | 4 messaggi IKE_SA_INIT + IKE_AUTH |
| **Cipher agility** | No (suite fissa) | Sì (negoziazione completa) |
| **MOBIKE** (cambio IP) | Nativo (senza protocollo aggiuntivo) | RFC 4555 (supportato) |
| **NAT traversal** | PersistentKeepalive | NAT-T (RFC 3948, UDP/4500) |
| **Interop hardware** | No (solo software WireGuard) | Sì (Cisco, Fortinet, Palo Alto, Juniper) |
| **Client nativi OS** | No (serve app) | Sì (Windows, macOS, iOS, Android built-in) |
| **Certificati** | No (solo chiavi statiche) | Sì (X.509, EAP, RADIUS) |
| **FIPS 140-2/3** | No | Sì (con moduli validati) |
| **Performance** | Superiore (kernel, parallelismo padata) | Buona (XFRM kernel + overhead IKE) |
| **Debugging** | Semplice (4 tipi messaggio) | Complesso (decine di payload IKE) |

### MOBIKE: Roaming a Confronto

MOBIKE (RFC 4555) è la capacità di IKEv2 di gestire cambi di indirizzo IP senza rinegoziare l'SA. WireGuard ha questa capacità nativamente:

```
WireGuard roaming (nativo):
1. Client si sposta WiFi → 4G
2. Il nuovo pacchetto dal client arriva da un IP diverso
3. Il server aggiorna l'endpoint del peer automaticamente
4. Nessuna rinegoziazione, nessun messaggio di controllo

IKEv2 MOBIKE:
1. Client si sposta WiFi → 4G
2. Client invia INFORMATIONAL con UPDATE_SA_ADDRESSES
3. Server verifica il nuovo indirizzo con NAT detection
4. Entrambe le parti aggiornano gli endpoint
5. Traffico riprende
```

### Quando IPsec è l'Unica Opzione

1. **Interoperabilità con appliance commerciali**: un tunnel verso Cisco ASA, Fortinet FortiGate o Palo Alto richiede IPsec. WireGuard non è supportato da questi vendor.

2. **Compliance FIPS 140-2/3**: ambienti governativi o finanziari che richiedono moduli crittografici validati FIPS. strongSwan con OpenSSL FIPS provider soddisfa questo requisito; WireGuard no.

3. **Client nativi OS senza app**: IKEv2 è supportato nativamente da Windows (tramite built-in VPN), macOS/iOS (profilo di configurazione), e Android (framework VPN). Non serve installare un'app.

4. **Transport mode**: IPsec può operare in transport mode (cifratura del payload senza incapsulamento IP), utile per protocolli sensibili al TTL o per protezione hop-by-hop. WireGuard opera sempre in tunnel mode.

---

## Esercizi

### Esercizio 1 — WireGuard Road Warrior (Concettuale + Lab)

Configura un server WireGuard su una VM Debian 12 con 3 peer:
- Un laptop (split tunnel verso 10.0.0.0/8)
- Uno smartphone (full tunnel con DNS 10.10.0.53)
- Un gateway di un ufficio remoto (site-to-site con subnet 192.168.10.0/24)

**Criteri di successo:**
- Tutti e 3 i peer completano l'handshake
- Il laptop raggiunge solo le reti split-tunnel
- Lo smartphone esce con l'IP del server VPN (`curl ifconfig.me`)
- Le macchine dietro il gateway remoto sono raggiungibili dal server

### Esercizio 2 — PKI OpenVPN con Revoca

Crea un'infrastruttura PKI con Easy-RSA:
1. Genera CA con EC secp384r1
2. Emetti 3 certificati client
3. Configura il server OpenVPN con tls-crypt
4. Connetti i 3 client e verifica il traffico
5. Revoca un certificato, rigenera la CRL e verifica che il client revocato non possa più connettersi
6. Documenta il processo di rinnovo per quando i certificati scadranno

### Esercizio 3 — Threat Model e Kill Switch

1. Connetti un client a una VPN WireGuard con full tunnel
2. Verifica l'assenza di DNS leak con `dig`, `resolvectl` e test online
3. Verifica l'assenza di IPv6 leak
4. Implementa un kill switch con nftables
5. Simula la caduta della VPN (`wg-quick down wg0`) e verifica che nessun traffico esca
6. Documenta cosa protegge e cosa non protegge la tua configurazione

### Esercizio 4 — Tailscale/Headscale Mesh (Design)

Progetta una rete mesh per un'azienda con:
- 3 server (produzione, staging, CI)
- 5 laptop sviluppatori
- 1 NAS ufficio con subnet routing

Definisci:
- ACL policy (chi accede a cosa)
- Exit node configuration
- DNS setup
- Scelta: Tailscale o Headscale self-hosted (giustifica)

---

## Auto-valutazione

1. **Quale cipher suite usa WireGuard e perché non è negoziabile?**
   <details><summary>Risposta</summary>
   WireGuard usa Curve25519 (ECDH), ChaCha20-Poly1305 (AEAD), BLAKE2s (hash), HKDF (KDF). Non è negoziabile perché: (a) riduce la superficie d'attacco — non ci sono downgrade attacks; (b) semplifica il codice — solo ~4000 righe; (c) segue il principio "cryptographic versioning": se un algoritmo viene rotto, l'intera suite viene sostituita con una nuova versione del protocollo, non configurata singolarmente.
   </details>

2. **Cosa succede se due peer WireGuard hanno AllowedIPs sovrapposti?**
   <details><summary>Risposta</summary>
   WireGuard usa AllowedIPs come tabella di routing (cryptokey routing). Se due peer hanno IP sovrapposti, l'ultimo peer configurato vince per quel range — i pacchetti vengono inviati solo a quel peer, l'altro non riceve traffico per quegli IP. Non c'è warning; è un errore silenzioso.
   </details>

3. **Perché la compressione in OpenVPN è sconsigliata?**
   <details><summary>Risposta</summary>
   L'attacco VORACLE (variante di CRIME/BREACH per VPN) sfrutta la compressione: un attaccante che può iniettare dati nel canale compresso (es. via JavaScript in un browser) osserva la dimensione dei pacchetti compressi per dedurre il contenuto del traffico. La direttiva `compress` senza argomenti la disabilita comunicando al peer di non comprimere.
   </details>

4. **Come si impedisce il DNS leak in una configurazione WireGuard con full tunnel?**
   <details><summary>Risposta</summary>
   Tre componenti: (1) `DNS = 10.10.0.53` in [Interface] per impostare il resolver nel tunnel; (2) `AllowedIPs = 0.0.0.0/0, ::/0` per instradare tutto il traffico (incluso DNS); (3) su sistemi con systemd-resolved, verificare con `resolvectl status wg0` che il DNS sia configurato e che il dominio sia `~.` (catch-all). Su Linux senza systemd-resolved, wg-quick modifica /etc/resolv.conf.
   </details>

5. **Qual è il ruolo del DERP relay in Tailscale?**
   <details><summary>Risposta</summary>
   DERP (Designated Encrypted Relay for Packets) è un relay TCP che trasporta pacchetti WireGuard quando la connessione UDP diretta tra due peer non è possibile (doppio NAT simmetrico, firewall restrittivi). Il relay non può decifrare il traffico — è E2E encrypted con le chiavi WireGuard dei peer. Tailscale tenta sempre prima la connessione diretta e cade su DERP solo come fallback.
   </details>

6. **Come funziona il meccanismo cookie di WireGuard per la resistenza DoS?**
   <details><summary>Risposta</summary>
   Quando il server è sotto carico, risponde con un COOKIE_REPLY invece di processare l'handshake. Il cookie è MAC(secret_rotante_ogni_2min, IP_sorgente). Il client deve ripresentare l'handshake con MAC2 = MAC(cookie, msg). Questo impedisce IP spoofing (il cookie è legato all'IP) e amplification (il server non alloca risorse finché il client non dimostra di poter ricevere il cookie).
   </details>

7. **Qual è la differenza tra tls-auth e tls-crypt in OpenVPN?**
   <details><summary>Risposta</summary>
   tls-auth aggiunge un HMAC al control channel — autentica i pacchetti TLS e previene DoS (pacchetti non firmati vengono scartati). tls-crypt fa lo stesso MA cifra anche l'intero control channel, nascondendo l'handshake TLS da deep packet inspection. tls-crypt è strettamente superiore e raccomandato. Entrambi usano una chiave statica condivisa, ma tls-auth richiede `key-direction` (0 server, 1 client) mentre tls-crypt no.
   </details>

8. **Come si implementa resistenza post-quantum con WireGuard oggi?**
   <details><summary>Risposta</summary>
   WireGuard supporta nativamente una PresharedKey (PSK) opzionale, mixata nella derivazione delle chiavi tramite HKDF. Se la PSK è generata con `wg genpsk` (256 bit casuali) e distribuita out-of-band (non via rete), un avversario quantistico dovrebbe rompere sia Curve25519 sia conoscere la PSK. Il progetto Rosenpass aggiunge un handshake post-quantum automatizzato basato su Classic McEliece/Kyber che rota la PSK periodicamente.
   </details>

---

## Letture primarie consigliate

- **WireGuard Whitepaper**: Jason A. Donenfeld, "WireGuard: Next Generation Kernel Network Tunnel", 2020 — https://www.wireguard.com/papers/wireguard.pdf (consultato: 2026-05-23)
- **Noise Protocol Framework**: Trevor Perrin, "The Noise Protocol Framework", Revision 34, 2018 — http://www.noiseprotocol.org/noise.html (consultato: 2026-05-23)
- **RFC 4301**: "Security Architecture for the Internet Protocol" (IPsec) — https://datatracker.ietf.org/doc/html/rfc4301 (consultato: 2026-05-23)
- **RFC 7296**: "Internet Key Exchange Protocol Version 2 (IKEv2)" — https://datatracker.ietf.org/doc/html/rfc7296 (consultato: 2026-05-23)
- **OpenVPN Security Overview**: OpenVPN community, "Hardening OpenVPN Security" — https://community.openvpn.net/openvpn/wiki/Hardening (consultato: 2026-05-23)
- **Rosenpass**: "Post-quantum WireGuard" — https://rosenpass.eu/ (consultato: 2026-05-23)
- **Tailscale Architecture**: "How Tailscale Works" — https://tailscale.com/blog/how-tailscale-works (consultato: 2026-05-23)
- **Headscale**: "An open source, self-hosted implementation of the Tailscale control server" — https://github.com/juanfont/headscale (consultato: 2026-05-23)
- **VORACLE Attack**: Ahamed Nafeez, "VORACLE Attack", DEFCON 2018 — https://i.blackhat.com/us-18/Wed-August-8/us-18-Nafeez-Compression-Oracle-Attacks-on-VPN-Networks.pdf (consultato: 2026-05-23)
- **Libro**: "WireGuard: A Modern VPN Protocol" — capitolo in "Linux Networking: Architecture, APIs, and Protocols" di Rami Rosen, Apress, 2024
- **udp2raw**: wangyu, "A Tunnel which Turns UDP Traffic into Encrypted FakeTCP/ICMP Traffic" — https://github.com/wangyu-/udp2raw (consultato: 2026-05-24)
- **wstunnel**: erebe, "Tunnel all your traffic over WebSocket" — https://github.com/erebe/wstunnel (consultato: 2026-05-24)
- **OpenVPN tls-crypt-v2 spec**: OpenVPN, "tls-crypt-v2.txt" — https://github.com/OpenVPN/openvpn/blob/master/doc/tls-crypt-v2.txt (consultato: 2026-05-24)
- **OpenVPN Access Server**: OpenVPN Inc., "Installation and Setup for Linux" — https://openvpn.net/as-docs/get---install-for-linux.html (consultato: 2026-05-24)
- **strongSwan**: "strongSwan IPsec VPN" — https://www.strongswan.org/ (consultato: 2026-05-24)
- **RFC 4555**: "IKEv2 Mobility and Multihoming Protocol (MOBIKE)" — https://datatracker.ietf.org/doc/html/rfc4555 (consultato: 2026-05-24)
- **RFC 8981**: "Temporary Address Extensions for Stateless Address Autoconfiguration in IPv6" — https://datatracker.ietf.org/doc/html/rfc8981 (consultato: 2026-05-24)
- **WireGuard kernel source**: "net/wireguard/ in mainline Linux" — https://github.com/WireGuard/wireguard-linux (consultato: 2026-05-24)
- **wireguard_exporter**: Matt Layher, "Prometheus exporter for WireGuard" — https://github.com/mdlayher/wireguard_exporter (consultato: 2026-05-24)
- **openvpn_exporter**: Kumina, "Prometheus exporter for OpenVPN" — https://github.com/kumina/openvpn_exporter (consultato: 2026-05-24)
- **VPN Performance Analysis**: "Empirical Performance Analysis of WireGuard vs. OpenVPN" — https://www.mdpi.com/2073-431X/14/8/326 (consultato: 2026-05-24)

---

## Collegamenti incrociati

- [05-networking.md](05-networking.md) — fondamenti TCP/IP, routing, bridge, VLAN
- [24-iptables-nftables-guida-completa.md](24-iptables-nftables-guida-completa.md) — regole firewall, NAT, MASQUERADE
- [11-sicurezza.md](11-sicurezza.md) — sicurezza Linux, crittografia, certificati
- [27-selinux-apparmor-guida-completa.md](27-selinux-apparmor-guida-completa.md) — MAC per il server VPN
- [34-hardening-sicurezza-avanzata.md](34-hardening-sicurezza-avanzata.md) — hardening del server che ospita la VPN
- [31-ansible-guida-operativa.md](31-ansible-guida-operativa.md) — automazione deploy VPN
- [19-servizi-rete.md](19-servizi-rete.md) — DNS, DHCP, NTP (servizi correlati alla VPN)
- [28-nginx-configurazione-avanzata.md](28-nginx-configurazione-avanzata.md) — reverse proxy e TLS (concetti condivisi)
- [35-compliance-scanning-automazione.md](35-compliance-scanning-automazione.md) — compliance e audit della configurazione VPN

---

## Glossario locale

| Termine | Definizione |
|---------|------------|
| **Cryptokey routing** | Meccanismo WireGuard che associa chiavi pubbliche a IP consentiti, combinando autenticazione e routing |
| **DERP** | Designated Encrypted Relay for Packets — relay TCP usato da Tailscale quando la connessione UDP diretta fallisce |
| **Easy-RSA** | Strumento CLI per gestire una PKI (Certificate Authority, emissione, revoca) usato con OpenVPN |
| **fwmark** | Marca (tag numerico) applicata ai pacchetti nel kernel Linux per policy routing |
| **Headscale** | Implementazione open source del coordination server Tailscale |
| **Kill switch** | Regole firewall che bloccano tutto il traffico non-VPN, prevenendo leak quando il tunnel cade |
| **MagicDNS** | Feature Tailscale che risolve automaticamente i nomi dei nodi nella rete mesh |
| **Noise Protocol** | Framework crittografico per handshake sicuri (usato da WireGuard nella variante IK) |
| **PresharedKey (PSK)** | Chiave simmetrica condivisa pre-distribuita, aggiunge un livello di protezione (inclusa post-quantum) |
| **Road warrior** | Topologia VPN con client mobili che si connettono a un server centrale |
| **Site-to-site** | Topologia VPN che interconnette due o più reti geograficamente separate |
| **Split tunnel** | Configurazione che instrada solo traffico selezionato via VPN, il resto esce direttamente |
| **tls-crypt** | Direttiva OpenVPN che cifra e autentica il control channel TLS con una chiave statica |
| **VORACLE** | Attacco alla compressione VPN (variante CRIME/BREACH) che deduce contenuto dal rapporto di compressione |
| **wg-quick** | Wrapper bash per WireGuard che semplifica la gestione delle interfacce |
| **udp2raw** | Tool che incapsula traffico UDP in segmenti FakeTCP per bypassare firewall che bloccano UDP |
| **wstunnel** | Tool che incapsula traffico UDP/TCP in tunnel WebSocket (wss://) per eludere DPI |
| **tls-crypt-v2** | Evoluzione di tls-crypt in OpenVPN: chiave unica per client, wrappata con server key |
| **padata** | Framework kernel Linux per parallelizzazione crittografica (usato da WireGuard per encrypt/decrypt multi-core) |
| **XFRM** | Framework kernel Linux per trasformazioni IPsec (encrypt, decrypt, encapsulate) |
| **MOBIKE** | Protocollo IKEv2 (RFC 4555) per il roaming di tunnel IPsec tra interfacce di rete |
| **strongSwan** | Implementazione open source di IPsec/IKEv2 per Linux, successore di FreeS/WAN |
| **NAT66** | NAT per IPv6, anti-pattern che annulla i vantaggi dell'end-to-end connectivity IPv6 |
| **ULA** | Unique Local Addresses (fd00::/8) — equivalente IPv6 degli indirizzi privati RFC 1918 |
| **DoH/DoT** | DNS over HTTPS / DNS over TLS — protocolli per cifrare le query DNS |
| **OpenVPN Access Server** | Versione commerciale di OpenVPN con GUI web di amministrazione e gestione utenti integrata |
