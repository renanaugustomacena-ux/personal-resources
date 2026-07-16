# Tutorial Linux 32 — VPN: WireGuard e OpenVPN

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** WireGuard (wg0.conf, wg-quick, PostUp/PostDown), OpenVPN (PKI, client config), site-to-site, split tunnel
> **Prerequisiti:** `tutorial_linux_05_networking.md`, `tutorial_linux_11_sicurezza.md`
> **Durata stimata:** 12-16 ore

---

## Mappa concettuale

```
VPN Linux
│
├── WireGuard (moderno, veloce)
│   ├── Architettura: peer-to-peer
│   ├── Crittografia: ChaCha20-Poly1305
│   ├── wg0.conf (Interface + Peer)
│   ├── wg-quick (routing automatico)
│   └── PostUp/PostDown (iptables NAT)
│
├── OpenVPN (enterprise, PKI)
│   ├── PKI: Easy-RSA (CA, server cert, client cert)
│   ├── server.conf
│   ├── client.ovpn
│   └── TLS Auth / TLS Crypt
│
└── Topologie
    ├── Road warrior (client remoti → server)
    ├── Site-to-site (rete A ↔ rete B)
    └── Split tunnel vs Full tunnel
```

---

# Parte A — WireGuard

---

## A1. Installazione e generazione chiavi

```bash
# Installa WireGuard
apt install wireguard-tools   # Ubuntu 22.04+
# Kernel module incluso da kernel 5.6+

# Genera coppia di chiavi (per ogni peer)
# Server
wg genkey | tee /etc/wireguard/server_private.key \
    | wg pubkey > /etc/wireguard/server_public.key

chmod 600 /etc/wireguard/server_private.key

# Client (ripeti per ogni client)
wg genkey | tee /etc/wireguard/client1_private.key \
    | wg pubkey > /etc/wireguard/client1_public.key

# Pre-shared key (opzionale, sicurezza post-quantum extra)
wg genpsk > /etc/wireguard/psk_server_client1

# Visualizza chiavi
cat /etc/wireguard/server_public.key
cat /etc/wireguard/client1_public.key
```

> **Analogia:** WireGuard funziona come il sistema di caselle postali pubbliche/private della crittografia asimmetrica, ma estremamente semplificato. Ogni peer ha una chiave pubblica (indirizzo della cassetta postale) e una privata (la chiave per aprirla). Sai con chi vuoi comunicare? Aggiungi la sua chiave pubblica come "peer" e il traffico si cifra automaticamente — nessun certificato, nessuna CA, nessun handshake complicato.

---

## A2. Configurazione server WireGuard

```bash
# /etc/wireguard/wg0.conf (server)
cat > /etc/wireguard/wg0.conf << EOF
[Interface]
# Chiave privata del server
PrivateKey = $(cat /etc/wireguard/server_private.key)

# IP dell'interfaccia tunnel (VPN network)
Address = 10.10.0.1/24

# Porta UDP in ascolto
ListenPort = 51820

# NAT: permetti ai client di accedere a internet via server
# eth0 = interfaccia internet del server
PostUp = iptables -A FORWARD -i %i -j ACCEPT; \
         iptables -A FORWARD -o %i -j ACCEPT; \
         iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; \
           iptables -D FORWARD -o %i -j ACCEPT; \
           iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# Client 1
[Peer]
PublicKey = $(cat /etc/wireguard/client1_public.key)
PresharedKey = $(cat /etc/wireguard/psk_server_client1)
# IP assegnato a questo client
AllowedIPs = 10.10.0.2/32

# Client 2 (aggiungi altri [Peer] per ogni client)
[Peer]
PublicKey = CHIAVE_PUBBLICA_CLIENT2
AllowedIPs = 10.10.0.3/32
EOF

chmod 600 /etc/wireguard/wg0.conf

# Abilita IP forwarding
sysctl -w net.ipv4.ip_forward=1
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.d/99-wireguard.conf

# Avvia e abilita
wg-quick up wg0
systemctl enable wg-quick@wg0

# Verifica
wg show wg0
```

---

## A3. Configurazione client WireGuard

```bash
# /etc/wireguard/wg0.conf (client)
cat > /etc/wireguard/wg0.conf << EOF
[Interface]
PrivateKey = $(cat /etc/wireguard/client1_private.key)
Address = 10.10.0.2/24
DNS = 10.10.0.1    # DNS del server VPN

[Peer]
PublicKey = CHIAVE_PUBBLICA_SERVER
PresharedKey = $(cat /etc/wireguard/psk_server_client1)
Endpoint = IP_PUBBLICO_SERVER:51820

# Full tunnel (tutto il traffico via VPN)
AllowedIPs = 0.0.0.0/0, ::/0

# Split tunnel (solo traffico verso 10.10.0.0/24 via VPN)
# AllowedIPs = 10.10.0.0/24

# Keepalive (per NAT traversal — mantieni tunnel attivo)
PersistentKeepalive = 25
EOF

wg-quick up wg0

# Test
ping 10.10.0.1             # ping al server
curl ifconfig.me           # verifica IP pubblico (deve essere IP server se full tunnel)
```

---

## A4. WireGuard site-to-site

```
Rete A: 192.168.1.0/24          Rete B: 192.168.2.0/24
  Server A (wg0: 10.10.0.1) ←→ Server B (wg0: 10.10.0.2)
```

```bash
# Server A — /etc/wireguard/wg0.conf
[Interface]
PrivateKey = CHIAVE_PRIVATA_A
Address = 10.10.0.1/30
ListenPort = 51820

[Peer]
PublicKey = CHIAVE_PUBBLICA_B
Endpoint = IP_SERVER_B:51820
# AllowedIPs: traffico verso rete B
AllowedIPs = 10.10.0.2/32, 192.168.2.0/24
PersistentKeepalive = 25

# Server B — /etc/wireguard/wg0.conf
[Interface]
PrivateKey = CHIAVE_PRIVATA_B
Address = 10.10.0.2/30
ListenPort = 51820

[Peer]
PublicKey = CHIAVE_PUBBLICA_A
Endpoint = IP_SERVER_A:51820
AllowedIPs = 10.10.0.1/32, 192.168.1.0/24
PersistentKeepalive = 25

# Su entrambi i server: aggiungi route alle reti locali
# Route già aggiunta da wg-quick via AllowedIPs
# Ma le macchine della LAN devono sapere che il gateway verso l'altra rete è il server WireGuard:
ip route add 192.168.2.0/24 via 192.168.1.1  # su macchine rete A
# Oppure aggiungi route sul router della LAN
```

---

# Parte B — OpenVPN

---

## B1. PKI con Easy-RSA

```bash
# Installa Easy-RSA
apt install easy-rsa

# Setup PKI
mkdir /etc/openvpn/easy-rsa
cp -r /usr/share/easy-rsa/* /etc/openvpn/easy-rsa/
cd /etc/openvpn/easy-rsa

# Configura vars
cat > vars << 'EOF'
set_var EASYRSA_REQ_COUNTRY    "IT"
set_var EASYRSA_REQ_PROVINCE   "Milano"
set_var EASYRSA_REQ_CITY       "Milano"
set_var EASYRSA_REQ_ORG        "MiaAzienda"
set_var EASYRSA_REQ_EMAIL      "admin@esempio.it"
set_var EASYRSA_REQ_OU         "IT"
set_var EASYRSA_KEY_SIZE       4096
set_var EASYRSA_ALGO           ec
set_var EASYRSA_CURVE          prime256v1
set_var EASYRSA_CA_EXPIRE      3650
set_var EASYRSA_CERT_EXPIRE    825
EOF

# Inizializza PKI
./easyrsa init-pki

# Crea CA (Certificate Authority)
./easyrsa build-ca nopass   # nopass = no password sulla CA (per automazione)

# Crea certificato server
./easyrsa gen-req server nopass
./easyrsa sign-req server server

# Parametri Diffie-Hellman
./easyrsa gen-dh

# Crea TLS Auth Key
openvpn --genkey secret /etc/openvpn/ta.key

# Crea certificati client
./easyrsa gen-req client1 nopass
./easyrsa sign-req client client1
```

---

## B2. Server OpenVPN

```bash
# /etc/openvpn/server/server.conf
cat > /etc/openvpn/server/server.conf << 'EOF'
# Porta e protocollo
port 1194
proto udp

# Interfaccia tunnel
dev tun

# Certificati e chiavi
ca /etc/openvpn/easy-rsa/pki/ca.crt
cert /etc/openvpn/easy-rsa/pki/issued/server.crt
key /etc/openvpn/easy-rsa/pki/private/server.key
dh /etc/openvpn/easy-rsa/pki/dh.pem
tls-auth /etc/openvpn/ta.key 0   # 0 = server

# VPN network
server 10.8.0.0 255.255.255.0

# Routing client
# Full tunnel: spingi default route
push "redirect-gateway def1 bypass-dhcp"
push "dhcp-option DNS 1.1.1.1"
push "dhcp-option DNS 8.8.8.8"

# Split tunnel: solo LAN
# push "route 192.168.1.0 255.255.255.0"

# Mantieni assegnazioni IP client
ifconfig-pool-persist /var/log/openvpn/ipp.txt

# Keepalive
keepalive 10 120

# Sicurezza
cipher AES-256-GCM
auth SHA256
tls-version-min 1.2
tls-cipher TLS-ECDHE-ECDSA-WITH-AES-256-GCM-SHA384

# User/group ridotti
user nobody
group nogroup

# Persisti (evita riapertura file dopo revoca privilege)
persist-key
persist-tun

# Log
status /var/log/openvpn/openvpn-status.log
log-append /var/log/openvpn/openvpn.log
verb 3

# Gestione client
client-to-client   # i client possono parlarsi tra loro
max-clients 50
EOF

# Abilita e avvia
systemctl enable --now openvpn-server@server

# Verifica
systemctl status openvpn-server@server
cat /var/log/openvpn/openvpn-status.log
```

---

## B3. Client OpenVPN

```bash
# Genera file .ovpn (bundle tutto-in-uno)
cat > /etc/openvpn/client1.ovpn << EOF
client
dev tun
proto udp
remote IP_SERVER_VPN 1194
resolv-retry infinite
nobind
persist-key
persist-tun
remote-cert-tls server
cipher AES-256-GCM
auth SHA256
verb 3
key-direction 1

<ca>
$(cat /etc/openvpn/easy-rsa/pki/ca.crt)
</ca>

<cert>
$(cat /etc/openvpn/easy-rsa/pki/issued/client1.crt)
</cert>

<key>
$(cat /etc/openvpn/easy-rsa/pki/private/client1.key)
</key>

<tls-auth>
$(cat /etc/openvpn/ta.key)
</tls-auth>
EOF

# Sul client Linux
openvpn --config client1.ovpn

# O come servizio
cp client1.ovpn /etc/openvpn/client/client1.conf
systemctl enable --now openvpn-client@client1
```

---

# Parte C — Confronto e Best Practice

---

## C1. WireGuard vs OpenVPN

| Aspetto | WireGuard | OpenVPN |
|---|---|---|
| Complessità setup | Bassa | Media-Alta (PKI) |
| Performance | Eccellente (kernel space) | Buona (userspace) |
| Crittografia | ChaCha20-Poly1305 (fisso) | Configurabile (AES-256-GCM) |
| Audit codice | ~4000 righe | ~70000 righe |
| PKI | No (solo chiavi) | Sì (CA, cert, revoca) |
| Revoca client | Rimuovi peer dal conf | CRL (Certificate Revocation List) |
| OS supportati | Linux, Win, Mac, iOS, Android | Praticamente tutti |
| Protocollo | UDP only | UDP/TCP |
| Ideal per | Road warrior, moderno | Enterprise, PKI esistente |

---

# Parte E — Riepilogo

## Troubleshooting WireGuard

```bash
# Debug
wg show                         # stato interfaccia + peer
wg show wg0 handshakes          # ultimo handshake per peer (ogni 120s)
ip route show table all         # routing

# Test connettività
ping 10.10.0.1              # server WireGuard
traceroute 8.8.8.8          # se full tunnel, passa via server

# Log kernel
dmesg | grep wireguard
journalctl -u wg-quick@wg0 -f

# Problemi comuni:
# - Handshake mai avvenuto → firewall blocca UDP 51820
# - Ping fallisce → IP forwarding non abilitato
# - Internet non funziona → NAT PostUp non applicato
# - DNS non risolve → DNS leak (controlla DNS in [Interface])
```

## Gestione certificati OpenVPN

```bash
# Revoca client
cd /etc/openvpn/easy-rsa
./easyrsa revoke client1
./easyrsa gen-crl

# Aggiungi CRL alla configurazione server
echo "crl-verify /etc/openvpn/easy-rsa/pki/crl.pem" >> /etc/openvpn/server/server.conf
systemctl reload openvpn-server@server

# Lista client connessi
cat /var/log/openvpn/openvpn-status.log
```

## Prossimi passi

- `tutorial_linux_33_high_availability.md` — HA clustering
- `tutorial_linux_05_networking.md` — networking base
