# Tutorial Linux 10 — SSH Avanzato: Chiavi, Config, Tunneling, ProxyJump

> **Campo:** 02-LINUX-POWERUSER
> **Scope:** autenticazione a chiave, ~/.ssh/config, tunneling, agent forwarding, hardening
> **Prerequisiti:** `tutorial_linux_05_networking.md`
> **Durata stimata:** 10-14 ore

---

## Mappa concettuale

```
SSH Avanzato
│
├── Autenticazione
│   ├── ed25519 / RSA — generazione chiavi
│   ├── authorized_keys — lato server
│   ├── ssh-agent — gestione chiavi in memoria
│   └── ssh-add / ssh-keygen
│
├── Config file (~/.ssh/config)
│   ├── Host alias
│   ├── IdentityFile per host
│   ├── ProxyJump — bastion host
│   └── ControlMaster — connessioni multiplexed
│
├── Tunneling
│   ├── -L Local port forwarding
│   ├── -R Remote port forwarding
│   ├── -D SOCKS5 proxy dinamico
│   └── -N no command (solo tunnel)
│
├── Hardening sshd
│   ├── /etc/ssh/sshd_config
│   ├── Disabilita PasswordAuthentication
│   ├── AllowUsers / AllowGroups
│   └── Port, MaxAuthTries
│
└── Tecniche avanzate
    ├── SSH certificate authority
    ├── Escape sequences
    └── Multiplexing ControlMaster
```

---

# Parte A — Chiavi SSH

---

## A1. Generazione e configurazione chiavi

```bash
# Genera coppia di chiavi (raccomandato: ed25519)
ssh-keygen -t ed25519 -C "mario@laptop" -f ~/.ssh/id_ed25519
# -t: tipo (ed25519 è più sicuro e compatto di rsa)
# -C: commento (aiuta a identificare la chiave)
# -f: file (default: ~/.ssh/id_ed25519)

# RSA (4096 bit) per compatibilità con sistemi vecchi
ssh-keygen -t rsa -b 4096 -C "mario@laptop" -f ~/.ssh/id_rsa_legacy

# Chiave con passphrase diversa
ssh-keygen -t ed25519 -N "mia-passphrase-sicura" -f ~/.ssh/id_ed25519_server

# Modifica passphrase chiave esistente
ssh-keygen -p -f ~/.ssh/id_ed25519

# Visualizza fingerprint chiave
ssh-keygen -l -f ~/.ssh/id_ed25519.pub
# 256 SHA256:abc... mario@laptop (ED25519)

# Visualizza public key (da copiare su server)
cat ~/.ssh/id_ed25519.pub

# Copia chiave pubblica sul server
ssh-copy-id -i ~/.ssh/id_ed25519.pub mario@server.esempio.it
ssh-copy-id -p 2222 mario@server.esempio.it   # porta custom

# Manualmente (se ssh-copy-id non disponibile)
cat ~/.ssh/id_ed25519.pub | ssh mario@server "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

# Permessi obbligatori (SSH rifiuta se troppo permissivi)
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
chmod 600 ~/.ssh/authorized_keys
chmod 644 ~/.ssh/known_hosts
```

> **Analogia:** La coppia di chiavi SSH è come un lucchetto aperto. Distribuisci il lucchetto (chiave pubblica) ai server su cui vuoi accedere — ci mettono il lucchetto nella loro "cassettina autorizzata". Tu tieni la chiave privata (l'unica che apre quel lucchetto) nel tuo portafoglio. Nessuno può entrare solo con il lucchetto; serve la chiave privata che solo tu hai.

---

## A2. ssh-agent: gestione chiavi in memoria

```bash
# Avvia ssh-agent (solitamente già avviato da DE/PAM)
eval "$(ssh-agent -s)"
# Agent pid 12345

# Aggiungi chiave all'agent (chiede passphrase una volta)
ssh-add ~/.ssh/id_ed25519
# Identity added: /home/mario/.ssh/id_ed25519

# Aggiungi con scadenza (dopo 8 ore chiede di nuovo la passphrase)
ssh-add -t 8h ~/.ssh/id_ed25519

# Lista chiavi in agent
ssh-add -l

# Rimuovi chiave dall'agent
ssh-add -d ~/.ssh/id_ed25519

# Rimuovi tutte le chiavi
ssh-add -D

# Agent forwarding — usa le chiavi locali su server remoto
ssh -A mario@server.esempio.it
# Poi dal server puoi connetterti ad altri con le tue chiavi locali
# ATTENZIONE: abilita solo su server fidati (admin può abusarne)
```

---

# Parte B — File di configurazione SSH

---

## B1. ~/.ssh/config

```ini
# ~/.ssh/config
# Ordine: le regole più specifiche prima

# Server di produzione
Host prod
    HostName 10.0.0.5
    User deploy
    IdentityFile ~/.ssh/id_ed25519_prod
    Port 2222
    ServerAliveInterval 60
    ServerAliveCountMax 3

# Server di staging attraverso bastion host
Host staging
    HostName 10.0.1.5
    User mario
    ProxyJump bastion

# Bastion host (jump server)
Host bastion
    HostName jump.esempio.it
    User mario
    IdentityFile ~/.ssh/id_ed25519
    Port 22

# Tutti i server interni passano per bastion
Host 10.0.*
    ProxyJump bastion
    User mario
    StrictHostKeyChecking no    # Solo in ambienti fidati

# GitHub
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_github

# Bitbucket con diversa chiave
Host bitbucket.org
    HostName bitbucket.org
    User git
    IdentityFile ~/.ssh/id_ed25519_bitbucket

# Opzioni globali per tutti gli host
Host *
    AddKeysToAgent yes          # aggiungi chiave all'agent automaticamente
    IdentitiesOnly yes          # usa solo le chiavi specificate
    ServerAliveInterval 30
    ServerAliveCountMax 6
    Compression yes
    ControlMaster auto          # multiplexing
    ControlPath ~/.ssh/sockets/%r@%h:%p
    ControlPersist 10m          # mantieni connessione per 10 minuti
```

```bash
# Uso con config
ssh prod                       # connetti a "prod" con tutte le opzioni
scp file.tar.gz prod:/var/www  # copia su prod
rsync -av ./dist/ staging:/var/www/  # rsync tramite proxy

# ProxyJump da riga di comando
ssh -J mario@bastion.it mario@server-interno.it
ssh -J mario@bastion.it:2222 mario@10.0.0.5   # porta custom

# Test configurazione senza connettersi
ssh -G prod                    # mostra configurazione per "prod"
ssh -v prod                    # verbose per debug
```

---

# Parte C — Tunneling SSH

---

## C1. Local Port Forwarding (-L)

```bash
# Forwarding locale: porta locale → porta su server remoto
# -L [bind_addr:]porta_locale:host_remoto:porta_remota

# Accedi al database PostgreSQL remoto come se fosse locale
ssh -N -L 5432:localhost:5432 mario@server.it
# Ora: psql -h localhost -U app → connette al DB remoto

# Database che non è sul server SSH ma in rete interna
ssh -N -L 5432:db-interno.it:5432 mario@bastion.it

# Accedi a interfaccia web admin (non esposta su internet)
ssh -N -L 8080:localhost:8080 mario@server.it
# Apri http://localhost:8080 nel browser locale

# Bind su indirizzo specifico (non 127.0.0.1)
ssh -N -L 0.0.0.0:8080:localhost:8080 mario@server.it
# Ora altri su rete locale possono usare il tunnel

# Come servizio systemd user
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/ssh-tunnel-postgres.service << 'EOF'
[Unit]
Description=SSH Tunnel PostgreSQL
After=network.target

[Service]
ExecStart=/usr/bin/ssh -N -o ServerAliveInterval=60 \
    -L 5432:localhost:5432 mario@server.it
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF

systemctl --user enable --now ssh-tunnel-postgres
```

---

## C2. Remote Port Forwarding (-R)

```bash
# Forwarding remoto: porta sul server → porta locale
# Utile quando il server deve raggiungere qualcosa sulla tua macchina

# Esponi server web locale (5000) su porta remota (8080)
ssh -N -R 8080:localhost:5000 mario@server.it
# Sul server: curl localhost:8080 → tua applicazione locale

# Esponi RDP locale su server (per supporto remoto)
ssh -N -R 3389:localhost:3389 mario@server.it

# Richiede GatewayPorts yes in /etc/ssh/sshd_config del server
# per rendere accessibile anche da fuori il server
ssh -N -R 0.0.0.0:8080:localhost:5000 mario@server.it
```

---

## C3. SOCKS5 Proxy (-D)

```bash
# Proxy SOCKS5 dinamico — tutto il traffico passa per il server SSH
ssh -N -D 1080 mario@server.it

# Configura browser per usare proxy SOCKS5 su localhost:1080
# Firefox: Settings → Network → Manual proxy → SOCKS5 localhost 1080

# curl con SOCKS5
curl --socks5 localhost:1080 https://api.servizio.it

# Tutto il traffico in una rete privata
ssh -N -D 8888 mario@bastion.it
export https_proxy="socks5://127.0.0.1:8888"
curl https://server-interno.it   # passa per bastion
```

---

# Parte D — Hardening sshd

---

## D1. /etc/ssh/sshd_config sicuro

```bash
# /etc/ssh/sshd_config — configurazione server SSH

# Porta non standard (oscurità, non sicurezza reale)
Port 2222

# Solo IPv4 (se non usi IPv6)
# AddressFamily inet

# Protocollo (solo SSH-2, mai SSH-1)
# Protocol 2   # default già SSH-2 nelle versioni moderne

# Autenticazione
PermitRootLogin no                    # MAI root via SSH
PasswordAuthentication no             # Solo chiavi, NIENTE password
PubkeyAuthentication yes
AuthenticationMethods publickey

# Limita utenti/gruppi che possono fare SSH
AllowGroups sshusers admins
# AllowUsers mario giovanni deploy

# Timeout e tentativi
LoginGraceTime 30
MaxAuthTries 3
MaxSessions 10

# Disabilita funzionalità non necessarie
X11Forwarding no
AllowAgentForwarding no              # abilita solo se necessario
AllowTcpForwarding yes               # per tunneling
PrintLastLog yes
Banner /etc/ssh/banner.txt           # messaggio legale

# Keep-alive
ClientAliveInterval 300              # 5 minuti
ClientAliveCountMax 2                # max 2 miss = 10 min poi disconnette

# Algoritmi sicuri (SSH audit: ssh-audit.com)
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com

# Testa configurazione
sshd -t              # syntax check
sshd -T              # dump configurazione effettiva

# Ricarica (senza disconnettere sessioni attive)
systemctl reload sshd
```

---

# Parte E — Riepilogo

## Escape sequences SSH

```bash
# Durante una sessione SSH, digita ~ seguito da:
~.   # Disconnetti (utile se la sessione è appesa)
~B   # Break signal
~C   # Command line SSH (per aggiungere tunnel al volo)
~Z   # Sospendi sessione SSH (come Ctrl+Z)
~#   # Lista connessioni forwarded
~?   # Help escape sequences

# ~C apre una prompt ssh> dove puoi digitare:
# -L 8080:localhost:8080  → aggiungi local forward
# -R 8080:localhost:8080  → aggiungi remote forward
# -KL 8080               → rimuovi local forward
```

## Quick reference tunneling

| Tipo | Opzione | Direzione | Uso tipico |
|---|---|---|---|
| Local | `-L local:host:remote` | Locale → Remoto | Accedere DB/app interna |
| Remote | `-R remote:host:local` | Remoto → Locale | Esporre servizio locale |
| SOCKS5 | `-D porta` | Proxy dinamico | Navigare nella rete remota |
| ProxyJump | `-J jump-host` | Bastion | Raggiungere host in rete privata |

## Prossimi passi

- `tutorial_linux_11_sicurezza.md` — hardening sistema, ufw, fail2ban
- `tutorial_linux_22_troubleshooting.md` — debug connessioni SSH problematiche
