# SSH Avanzato — Guida Completa

> **Modulo 10** · **Aggiornamento:** 2026-05-22

## Idee guida
1. **Agent forwarding threat model: trust on remote.** Use `ssh -A` cautiously; `ProxyJump -J` preferred.
2. **SSH CA at scale: short-lived cert > authorized_keys management.**
3. **Revocation list `RevokedKeys`.**
4. **Audit log via Bastion (Teleport, Boundary) o sshd `AuditLogLevel`.**
5. **OpenSSH docs + RFC 4253 cite primarie.**


## Indice

- [Panoramica](#panoramica)
- [Interni del Protocollo SSH](#interni-del-protocollo-ssh)
  - [Architettura a Strati (RFC 4251–4254)](#architettura-a-strati-rfc-42514254)
  - [Transport Layer: Key Exchange](#transport-layer-key-exchange)
  - [Fase di Autenticazione](#fase-di-autenticazione)
  - [Connection Layer: Channel Multiplexing](#connection-layer-channel-multiplexing)
- [Fondamenti e Configurazione](#fondamenti-e-configurazione)
- [Chiavi SSH: Generazione e Gestione](#chiavi-ssh-generazione-e-gestione)
  - [Confronto Algoritmi: ed25519 vs RSA vs ECDSA](#confronto-algoritmi-ed25519-vs-rsa-vs-ecdsa)
  - [Generare Chiavi](#generare-chiavi)
  - [Distribuire Chiavi](#distribuire-chiavi)
  - [Gestione Chiavi](#gestione-chiavi)
  - [ssh-agent in Profondità](#ssh-agent-in-profondità)
  - [Rotazione Chiavi: Procedure e Automazione](#rotazione-chiavi-procedure-e-automazione)
  - [Revoca di Emergenza](#revoca-di-emergenza)
- [SSH Config File — Deep Dive](#ssh-config-file--deep-dive)
  - [Direttive Globali](#direttive-globali)
  - [ProxyJump e ProxyCommand](#proxyjump-e-proxycommand)
  - [ControlMaster, ControlPath, ControlPersist](#controlmaster-controlpath-controlpersist)
  - [Port Forwarding nel Config](#port-forwarding-nel-config)
  - [Match Blocks](#match-blocks)
  - [Direttive Avanzate](#direttive-avanzate)
  - [Config Completo Commentato](#config-completo-commentato)
- [SSH Tunneling — Masterclass](#ssh-tunneling--masterclass)
  - [Local Port Forwarding (-L)](#local-port-forwarding--l)
  - [Remote Port Forwarding (-R)](#remote-port-forwarding--r)
  - [Dynamic SOCKS Proxy (-D)](#dynamic-socks-proxy--d)
  - [ProxyJump Chains](#proxyjump-chains)
  - [Tunnel Persistenti con autossh](#tunnel-persistenti-con-autossh)
- [SSH Agent e Forwarding](#ssh-agent-e-forwarding)
  - [Agent Forwarding: Rischi e Alternative](#agent-forwarding-rischi-e-alternative)
- [Autenticazione Basata su Certificati](#autenticazione-basata-su-certificati)
  - [Setup della CA SSH](#setup-della-ca-ssh)
  - [Certificati Utente](#certificati-utente)
  - [Certificati Host](#certificati-host)
  - [Validità e Rinnovo](#validità-e-rinnovo)
  - [Revoca Certificati](#revoca-certificati)
- [SSHD Hardening](#sshd-hardening)
  - [Configurazione Server Sicura](#configurazione-server-sicura)
  - [Direttive CIS Benchmark](#direttive-cis-benchmark)
  - [Match Blocks nel sshd_config](#match-blocks-nel-sshd_config)
  - [Banner e MOTD](#banner-e-motd)
- [Bastion / Jump Host — Architettura](#bastion--jump-host--architettura)
  - [Design di un Bastion Host](#design-di-un-bastion-host)
  - [Configurazione del Bastion](#configurazione-del-bastion)
  - [Auditing e Logging](#auditing-e-logging)
- [SFTP — Configurazione Avanzata](#sftp--configurazione-avanzata)
  - [Chroot SFTP](#chroot-sftp)
  - [Accesso Ristretto](#accesso-ristretto)
  - [Trasferimenti Automatizzati](#trasferimenti-automatizzati)
- [SCP vs rsync vs SFTP — Confronto](#scp-vs-rsync-vs-sftp--confronto)
- [SCP, SFTP, rsync over SSH](#scp-sftp-rsync-over-ssh)
- [Multiplexing SSH](#multiplexing-ssh)
- [SSH e PAM — Integrazione e 2FA](#ssh-e-pam--integrazione-e-2fa)
  - [PAM e SSH](#pam-e-ssh)
  - [Google Authenticator (TOTP)](#google-authenticator-totp)
  - [Duo Security](#duo-security)
  - [Autenticazione LDAP](#autenticazione-ldap)
- [fail2ban per SSH — Configurazione Avanzata](#fail2ban-per-ssh--configurazione-avanzata)
  - [Installazione e Jail Base](#installazione-e-jail-base)
  - [Jail Personalizzate](#jail-personalizzate)
  - [Rate Limiting Avanzato](#rate-limiting-avanzato)
  - [Azioni Personalizzate](#azioni-personalizzate)
- [Port Knocking e Single Packet Authorization](#port-knocking-e-single-packet-authorization)
  - [Port Knocking Classico](#port-knocking-classico)
  - [fwknop — Single Packet Authorization](#fwknop--single-packet-authorization)
- [SSH Automation](#ssh-automation)
  - [expect](#expect)
  - [sshpass (e i suoi rischi)](#sshpass-e-i-suoi-rischi)
  - [Ansible SSH Transport](#ansible-ssh-transport)
- [Best Practices](#best-practices)
- [Troubleshooting — 25 Problemi Comuni](#troubleshooting--25-problemi-comuni)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)
- [Security Audit Checklist](#security-audit-checklist)

---

## Panoramica

SSH (Secure Shell) è il protocollo standard per l'accesso remoto sicuro ai sistemi Linux. Oltre alla shell remota, SSH offre: trasferimento file sicuro (SCP, SFTP), tunneling di porte (port forwarding), proxy SOCKS, agent forwarding, multiplexing di connessioni e molto altro. La configurazione avanzata di SSH, sia lato client che server, è una competenza essenziale per qualsiasi amministratore di sistema.

Il protocollo SSH è definito da una famiglia di RFC:
- **RFC 4251** — Architettura del protocollo SSH
- **RFC 4252** — Protocollo di autenticazione
- **RFC 4253** — Protocollo Transport Layer
- **RFC 4254** — Protocollo Connection Layer
- **RFC 4255** — DNS SSHFP Resource Records
- **RFC 4256** — Autenticazione interattiva generica (keyboard-interactive)
- **RFC 6668** — Integrità SHA-2 per il Transport Layer
- **RFC 8332** — RSA con SHA-256/512 per il Transport Layer
- **RFC 8709** — Ed25519 e Ed448 per il Transport Layer

OpenSSH è l'implementazione di riferimento (sviluppata dal team OpenBSD) e rappresenta oltre il 95% delle installazioni SSH su sistemi Unix/Linux.

---

## Interni del Protocollo SSH

### Architettura a Strati (RFC 4251–4254)

SSH è un protocollo stratificato che opera su TCP (porta 22 di default). L'architettura è composta da tre strati:

```
┌─────────────────────────────────────────────┐
│          Connection Layer (RFC 4254)        │  ← canali, sessioni, forwarding
├─────────────────────────────────────────────┤
│       User Authentication (RFC 4252)        │  ← publickey, password, keyboard-interactive
├─────────────────────────────────────────────┤
│         Transport Layer (RFC 4253)          │  ← key exchange, encryption, MAC, compression
├─────────────────────────────────────────────┤
│                  TCP/IP                      │  ← trasporto di rete
└─────────────────────────────────────────────┘
```

**Sequenza di connessione SSH:**

```
1. Client → Server:  TCP handshake (porta 22)
2. Client ↔ Server:  Scambio version string ("SSH-2.0-OpenSSH_9.x")
3. Client ↔ Server:  Key Exchange (algoritmo concordato, chiave di sessione derivata)
4. Client ↔ Server:  Verifica host key (known_hosts)
5. Client → Server:  Autenticazione utente (publickey / password / keyboard-interactive)
6. Client ↔ Server:  Apertura canali (session, direct-tcpip, forwarded-tcpip)
7. Client ↔ Server:  Richieste su canale (shell, exec, subsystem, env)
```

### Transport Layer: Key Exchange

Il Transport Layer stabilisce la connessione crittografata. Il key exchange (scambio di chiavi) è il meccanismo con cui client e server concordano una chiave di sessione condivisa senza trasmetterla in chiaro.

**Scambio Version String:**

```
# Cattura con tcpdump:
# Client: "SSH-2.0-OpenSSH_9.7 Ubuntu-2ubuntu1\r\n"
# Server: "SSH-2.0-OpenSSH_9.6p1 Debian-4\r\n"

# La version string rivela sistema operativo e versione OpenSSH.
# Hardening: UseDNS no + VersionAddendum none per limitare l'esposizione.
```

**Algoritmi di Key Exchange:**

```bash
# Visualizzare gli algoritmi supportati dal client
ssh -Q kex

# Algoritmi moderni consigliati (in ordine di preferenza):
# 1. sntrup761x25519-sha512@openssh.com  ← post-quantum hybrid (OpenSSH 9.0+)
# 2. curve25519-sha256                    ← Curve25519 ECDH
# 3. curve25519-sha256@libssh.org         ← alias del precedente
# 4. diffie-hellman-group16-sha512        ← DH group 4096-bit
# 5. diffie-hellman-group18-sha512        ← DH group 8192-bit

# Algoritmi da EVITARE (deprecati/deboli):
# diffie-hellman-group1-sha1              ← 1024-bit, rotto
# diffie-hellman-group14-sha1             ← SHA-1 debole
# ecdh-sha2-nistp256                      ← curve NIST, dubbi sulla backdoor
```

**Processo di key exchange Curve25519:**

```
1. Client genera coppia effimera Curve25519 (e_client_pub, e_client_priv)
2. Server genera coppia effimera Curve25519 (e_server_pub, e_server_priv)
3. Client → Server:  SSH_MSG_KEX_ECDH_INIT (e_client_pub)
4. Server → Client:  SSH_MSG_KEX_ECDH_REPLY (e_server_pub, host_key_pub, firma)
5. Entrambi calcolano: shared_secret = ECDH(e_client_priv, e_server_pub)
                                      = ECDH(e_server_priv, e_client_pub)
6. Da shared_secret si derivano (via hash):
   - Encryption key (client→server)
   - Encryption key (server→client)
   - Integrity key (client→server)
   - Integrity key (server→client)
   - IV (client→server)
   - IV (server→client)
7. Session ID = hash del primo key exchange (non cambia con rekey)
```

**Rekey periodico:**

```bash
# SSH esegue rekey automatico dopo:
# - 1 GB di dati trasferiti (default), oppure
# - Dopo un certo tempo (configurabile)

# Configurare rekey esplicito (client):
# ~/.ssh/config
Host *
    RekeyLimit 512M 1h    # Rekey dopo 512 MB o 1 ora
```

### Fase di Autenticazione

Dopo il key exchange, il canale è crittografato. L'autenticazione utente avviene dentro il tunnel cifrato.

**Metodi di autenticazione (RFC 4252):**

```
1. none          — Usato per scoprire i metodi accettati dal server
2. publickey     — Firma digitale con chiave privata dell'utente
3. password      — Password in chiaro (protetta dal tunnel cifrato)
4. keyboard-interactive — Challenge-response (usato per 2FA, PAM)
5. hostbased     — Autenticazione basata sull'host (raro, sconsigliato)
6. gssapi-with-mic — Kerberos/GSSAPI (ambienti enterprise)
```

**Flusso autenticazione publickey:**

```
1. Client → Server:  SSH_MSG_USERAUTH_REQUEST (username, "publickey", algorithm, pubkey)
2. Server verifica:  la pubkey è in authorized_keys?
3. Server → Client:  SSH_MSG_USERAUTH_PK_OK (conferma che la chiave è accettabile)
4. Client firma:     session_id + SSH_MSG_USERAUTH_REQUEST con la chiave privata
5. Client → Server:  SSH_MSG_USERAUTH_REQUEST (username, "publickey", algorithm, pubkey, firma)
6. Server verifica:  la firma è valida con la pubkey?
7. Server → Client:  SSH_MSG_USERAUTH_SUCCESS
```

**Ordine di autenticazione nel client OpenSSH:**

```bash
# Il client prova i metodi in questo ordine (configurabile):
# 1. gssapi-with-mic (se disponibile)
# 2. hostbased
# 3. publickey
# 4. keyboard-interactive
# 5. password

# Forzare un metodo specifico:
ssh -o PreferredAuthentications=publickey user@server

# Nel config:
Host server
    PreferredAuthentications publickey,keyboard-interactive
```

### Connection Layer: Channel Multiplexing

Il Connection Layer (RFC 4254) gestisce i canali multiplexati all'interno della singola connessione TCP crittografata. Ogni canale è indipendente con il proprio flusso di dati e controllo di flusso.

**Tipi di canale:**

```
session          — Shell interattiva, exec di comandi, subsystem (sftp)
direct-tcpip     — Port forwarding locale (-L)
forwarded-tcpip  — Port forwarding remoto (-R)
x11              — X11 forwarding
```

**Multiplexing in azione:**

```
Connessione TCP singola (porta 22)
│
├── Canale #0: session (shell interattiva)
├── Canale #1: direct-tcpip (forwarding locale porta 8080 → web:80)
├── Canale #2: direct-tcpip (forwarding locale porta 5432 → db:5432)
├── Canale #3: session (subsystem: sftp)
└── Canale #4: forwarded-tcpip (forwarding remoto porta 9090 → localhost:3000)
```

```bash
# Osservare i canali attivi (debug):
ssh -vvv user@server 2>&1 | grep "channel"
# Output esempio:
# debug2: channel 0: new [client-session]
# debug2: channel 0: open confirm rwindow 0 rmax 32768
# debug2: channel 1: new [direct-tcpip]
```

**Controllo di flusso per canale:**

Ogni canale ha una propria window size (finestra di ricezione). Il mittente non può inviare più dati di quanto la finestra del destinatario permetta. Quando il destinatario consuma dati, invia un `SSH_MSG_CHANNEL_WINDOW_ADJUST` per ampliare la finestra.

```bash
# Diagnosticare problemi di throughput legati alla window size:
ssh -vvv user@server 2>&1 | grep "rwindow"
# Se rwindow è piccola, il throughput sarà limitato

# Aumentare il buffer TCP (indirettamente aiuta SSH):
# /etc/sysctl.conf
# net.core.rmem_max = 16777216
# net.core.wmem_max = 16777216
```

---

## Fondamenti e Configurazione

```bash
# Connessione base
ssh user@hostname                   # Connessione con username
ssh -p 2222 user@hostname           # Porta non standard
ssh user@hostname comando           # Esegui comando remoto (senza shell interattiva)
ssh -v user@hostname                # Debug verbose (-vv e -vvv per più dettaglio)

# File e directory
~/.ssh/                             # Directory SSH utente
~/.ssh/config                       # Configurazione client
~/.ssh/known_hosts                  # Host conosciuti (fingerprint)
~/.ssh/authorized_keys              # Chiavi pubbliche autorizzate (sul server)
~/.ssh/id_ed25519                   # Chiave privata (ED25519)
~/.ssh/id_ed25519.pub               # Chiave pubblica
/etc/ssh/sshd_config                # Configurazione server SSH
/etc/ssh/ssh_config                 # Configurazione client globale
/etc/ssh/ssh_host_*                 # Host keys del server
/etc/ssh/sshd_config.d/             # Drop-in config directory (OpenSSH 8.4+)
/etc/ssh/ssh_config.d/              # Drop-in config directory client

# Permessi (FONDAMENTALI — SSH rifiuta file con permessi errati)
chmod 700 ~/.ssh
chmod 600 ~/.ssh/config
chmod 600 ~/.ssh/id_ed25519         # Chiave privata
chmod 644 ~/.ssh/id_ed25519.pub     # Chiave pubblica
chmod 600 ~/.ssh/authorized_keys
chmod 644 ~/.ssh/known_hosts

# Permessi lato server
chmod 755 /home/user                # Home NON deve essere group/world-writable
chmod 700 /home/user/.ssh
chmod 600 /home/user/.ssh/authorized_keys
# StrictModes yes in sshd_config enforce questi permessi
```

---

## Chiavi SSH: Generazione e Gestione

### Confronto Algoritmi: ed25519 vs RSA vs ECDSA

```
┌─────────────┬──────────────┬──────────────┬───────────────┬───────────────────────┐
│ Algoritmo   │ Dimensione   │ Dimensione   │ Sicurezza     │ Note                  │
│             │ chiave       │ firma        │ equivalente   │                       │
├─────────────┼──────────────┼──────────────┼───────────────┼───────────────────────┤
│ ed25519     │ 256 bit      │ 64 byte      │ ~128 bit      │ CONSIGLIATO.          │
│             │              │              │               │ Veloce, sicuro,       │
│             │              │              │               │ resistente a side     │
│             │              │              │               │ channel. Basato su    │
│             │              │              │               │ Curve25519 (Bernstein)│
├─────────────┼──────────────┼──────────────┼───────────────┼───────────────────────┤
│ rsa         │ 3072–4096 bit│ 256–512 byte │ ~128 bit      │ Solo per legacy.      │
│             │              │              │ (4096 bit)    │ Chiavi grandi, firma  │
│             │              │              │               │ lenta. Usare ≥3072.   │
│             │              │              │               │ RSA-1024 è ROTTO.     │
├─────────────┼──────────────┼──────────────┼───────────────┼───────────────────────┤
│ ecdsa       │ 256/384/521  │ 64–132 byte  │ ~128/192/256  │ SCONSIGLIATO.         │
│             │ bit          │              │ bit           │ Curve NIST, possibili │
│             │              │              │               │ backdoor. Vulnerabile │
│             │              │              │               │ a nonce deboli.       │
├─────────────┼──────────────┼──────────────┼───────────────┼───────────────────────┤
│ sk-ed25519  │ 256 bit      │ hardware     │ ~128 bit      │ Hardware key (FIDO2). │
│             │              │              │               │ Richiede YubiKey o    │
│             │              │              │               │ simile. Massima       │
│             │              │              │               │ sicurezza.            │
├─────────────┼──────────────┼──────────────┼───────────────┼───────────────────────┤
│ dsa         │ 1024 bit     │ 40 byte      │ ~80 bit       │ DEPRECATO. Rimosso    │
│             │              │              │               │ in OpenSSH 7.0+.      │
│             │              │              │               │ Non usare MAI.        │
└─────────────┴──────────────┴──────────────┴───────────────┴───────────────────────┘
```

**Raccomandazione chiara:**
- **Nuovo setup →** ed25519
- **Hardware key →** sk-ed25519 (FIDO2/U2F con YubiKey)
- **Compatibilità legacy →** RSA 4096 (mai meno di 3072)
- **Mai usare →** DSA, ECDSA (a meno di requisiti specifici FIPS)

### Generare Chiavi

```bash
# ED25519 (consigliato — veloce, sicuro, chiavi corte)
ssh-keygen -t ed25519 -C "admin@example.com"

# RSA (compatibilità con sistemi legacy, usare 4096 bit)
ssh-keygen -t rsa -b 4096 -C "admin@example.com"

# Con nome file specifico
ssh-keygen -t ed25519 -f ~/.ssh/id_server_prod -C "produzione"

# Chiave FIDO2 (richiede hardware key come YubiKey)
ssh-keygen -t ed25519-sk -C "admin@example.com"
# -sk = security key, la chiave privata risiede sull'hardware

# Chiave con KDF rounds aumentati (protezione brute force sulla passphrase)
ssh-keygen -t ed25519 -a 100 -f ~/.ssh/id_secure -C "high-security"
# -a 100 = 100 rounds di KDF (bcrypt). Default è 16.
# Aumenta il tempo di decrypt ma anche la resistenza al brute force.

# Opzioni
# -t: tipo (ed25519, rsa, ecdsa, ed25519-sk, ecdsa-sk)
# -b: bit (solo per RSA)
# -C: commento
# -f: file di output
# -N "": passphrase vuota (non consigliato per chiavi personali)
# -a: rounds KDF (default 16 per ed25519)

# Formato della chiave privata
# OpenSSH usa il formato proprietario "openssh-key-v1" di default (da OpenSSH 6.5+)
# Per compatibilità con sistemi vecchi:
ssh-keygen -t rsa -b 4096 -m PEM -f ~/.ssh/id_rsa_legacy
# -m PEM = formato PEM classico (richiesto da alcune librerie)

# Convertire formato esistente
ssh-keygen -p -f ~/.ssh/id_rsa -m PEM    # → PEM
ssh-keygen -p -f ~/.ssh/id_rsa -m RFC4716 # → RFC 4716
```

### Distribuire Chiavi

```bash
# Copiare la chiave pubblica sul server (metodo consigliato)
ssh-copy-id user@server
ssh-copy-id -i ~/.ssh/id_server_prod.pub user@server

# Manualmente
cat ~/.ssh/id_ed25519.pub | ssh user@server "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"

# Verificare
ssh user@server                     # Dovrebbe entrare senza password

# authorized_keys: opzioni avanzate
# Ogni riga in authorized_keys può avere opzioni prefisse:
# command="cmd"      — Forza esecuzione di un solo comando
# from="pattern"     — Limita l'accesso a specifici IP/host
# no-pty             — Vieta allocazione PTY (no shell interattiva)
# no-port-forwarding — Vieta port forwarding
# no-agent-forwarding — Vieta agent forwarding
# no-X11-forwarding  — Vieta X11 forwarding
# restrict           — Disabilita TUTTO, poi riabilita selettivamente
# expiry-time="data" — Scadenza della chiave (OpenSSH 9.2+)

# Esempio: chiave di backup limitata
# In ~/.ssh/authorized_keys:
# restrict,command="/usr/local/bin/backup.sh",from="10.0.1.0/24" ssh-ed25519 AAAA...

# Esempio: chiave con scadenza
# expiry-time="20261231" ssh-ed25519 AAAA...
```

### Gestione Chiavi

```bash
# Cambiare passphrase
ssh-keygen -p -f ~/.ssh/id_ed25519

# Visualizzare fingerprint
ssh-keygen -lf ~/.ssh/id_ed25519.pub
ssh-keygen -lvf ~/.ssh/id_ed25519.pub  # Con visual art (randomart)
# Output: 256 SHA256:xxxx... admin@example.com (ED25519)

# Fingerprint in diversi formati
ssh-keygen -lf ~/.ssh/id_ed25519.pub -E md5    # MD5 (legacy)
ssh-keygen -lf ~/.ssh/id_ed25519.pub -E sha256 # SHA256 (default)

# Estrarre chiave pubblica da chiave privata
ssh-keygen -yf ~/.ssh/id_ed25519 > ~/.ssh/id_ed25519.pub

# Rimuovere host da known_hosts (dopo reinstallazione server)
ssh-keygen -R hostname
ssh-keygen -R [hostname]:2222       # Porta non standard
ssh-keygen -R 10.0.1.100

# Trovare la chiave pubblica del server remoto (senza connettersi)
ssh-keyscan -t ed25519 hostname
ssh-keyscan -t ed25519 -p 2222 hostname    # Porta non standard
ssh-keyscan -H hostname >> ~/.ssh/known_hosts  # Aggiungere con hash

# Verificare integrità di known_hosts
ssh-keygen -lf ~/.ssh/known_hosts

# Testare se una chiave è protetta da passphrase
ssh-keygen -yf ~/.ssh/id_ed25519 2>/dev/null
# Se chiede passphrase → è protetta. Se stampa la pubkey → non protetta.
```

### ssh-agent in Profondità

L'ssh-agent è un demone che mantiene le chiavi private decriptate in memoria, evitando di digitare la passphrase ad ogni connessione.

```bash
# Avviare l'agent manualmente
eval $(ssh-agent -s)                # -s per output Bourne shell
eval $(ssh-agent -c)                # -c per output C shell

# Verificare che l'agent sia attivo
echo $SSH_AUTH_SOCK                  # Deve essere impostato
ssh-add -l                           # Lista chiavi (o "The agent has no identities")

# Aggiungere chiavi
ssh-add                             # Aggiunge chiave default (~/.ssh/id_*)
ssh-add ~/.ssh/id_prod              # Chiave specifica
ssh-add -t 3600 ~/.ssh/id_prod     # Con timeout (1 ora, poi viene rimossa)
ssh-add -t 28800 ~/.ssh/id_work    # 8 ore (giornata lavorativa)

# Lista chiavi caricate
ssh-add -l                          # Fingerprint
ssh-add -L                          # Chiavi pubbliche complete

# Rimuovere chiavi
ssh-add -d ~/.ssh/id_prod           # Rimuovi specifica
ssh-add -D                          # Rimuovi tutte

# Blocco/sblocco dell'agent (protezione quando si lascia il terminale)
ssh-add -x                          # Blocca con password
ssh-add -X                          # Sblocca

# Conferma interattiva per ogni utilizzo della chiave
ssh-add -c ~/.ssh/id_prod           # Chiede conferma ogni volta
# Utile contro l'abuso dell'agent forwarding

# Limiti di chiavi caricate
ssh-add -k                          # Non caricare chiavi dal PKCS#11

# Agent persistente via systemd (Linux desktop)
# ~/.config/systemd/user/ssh-agent.service
# [Unit]
# Description=SSH Agent
# [Service]
# Type=simple
# Environment=SSH_AUTH_SOCK=%t/ssh-agent.sock
# ExecStart=/usr/bin/ssh-agent -D -a %t/ssh-agent.sock
# [Install]
# WantedBy=default.target

# Poi in ~/.bashrc:
# export SSH_AUTH_SOCK="${XDG_RUNTIME_DIR}/ssh-agent.sock"

# macOS keychain integration
# In ~/.ssh/config:
# Host *
#     UseKeychain yes
#     AddKeysToAgent yes
```

### Rotazione Chiavi: Procedure e Automazione

La rotazione periodica delle chiavi SSH è una pratica di sicurezza fondamentale, spesso trascurata.

```bash
# === PROCEDURA MANUALE DI ROTAZIONE ===

# 1. Generare nuova chiave
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519_2026Q3 -C "admin@example.com 2026-Q3"

# 2. Distribuire nuova chiave su TUTTI i server (PRIMA di rimuovere la vecchia)
ssh-copy-id -i ~/.ssh/id_ed25519_2026Q3.pub user@server1
ssh-copy-id -i ~/.ssh/id_ed25519_2026Q3.pub user@server2
# ...ripetere per ogni server

# 3. Testare che la nuova chiave funzioni
ssh -i ~/.ssh/id_ed25519_2026Q3 user@server1 "echo OK"

# 4. Aggiornare ~/.ssh/config
# Cambiare IdentityFile alla nuova chiave

# 5. Rimuovere la vecchia chiave pubblica da tutti i server
ssh user@server1 "sed -i '/old-key-comment/d' ~/.ssh/authorized_keys"

# 6. Archiviare (o distruggere) la vecchia chiave privata
# Archiviare: spostare in backup cifrato
# Distruggere: shred -vfz -n 5 ~/.ssh/id_ed25519_2026Q2

# === AUTOMAZIONE CON SCRIPT ===

# Script di rotazione (esempio concettuale)
#!/bin/bash
# rotate-ssh-keys.sh
KEY_NAME="id_ed25519_$(date +%Y%m)"
SERVERS="server1 server2 server3"

# Genera nuova chiave
ssh-keygen -t ed25519 -f "$HOME/.ssh/$KEY_NAME" -N "" -C "admin $(date +%Y-%m)"

# Distribuisci su tutti i server
for srv in $SERVERS; do
    ssh-copy-id -i "$HOME/.ssh/${KEY_NAME}.pub" "admin@${srv}"
    echo "Chiave distribuita su $srv"
done

# Test
for srv in $SERVERS; do
    ssh -i "$HOME/.ssh/$KEY_NAME" "admin@${srv}" "echo 'OK: $srv'" || echo "ERRORE: $srv"
done

# === POLITICA DI ROTAZIONE CONSIGLIATA ===
# - Chiavi personali: ogni 6–12 mesi
# - Chiavi di servizio/automazione: ogni 3–6 mesi
# - Chiavi dopo incidente: IMMEDIATAMENTE
# - Chiavi di ex dipendenti: rimozione entro 24 ore dall'uscita
```

### Revoca di Emergenza

```bash
# In caso di compromissione di una chiave:

# 1. IMMEDIATAMENTE: rimuovere la chiave pubblica da tutti i server
# Script di revoca d'emergenza:
COMPROMISED_KEY_FINGERPRINT="SHA256:xxxxxxxxxxxx"
SERVERS="server1 server2 server3"

for srv in $SERVERS; do
    ssh root@"$srv" "
        grep -v '$COMPROMISED_KEY_FINGERPRINT' ~/.ssh/authorized_keys > /tmp/ak_clean
        mv /tmp/ak_clean ~/.ssh/authorized_keys
        chmod 600 ~/.ssh/authorized_keys
    "
done

# 2. Se si usano certificati SSH, aggiungere alla KRL (Key Revocation List)
ssh-keygen -k -f /etc/ssh/revoked_keys -s /etc/ssh/ca_key /etc/ssh/compromised_key.pub

# 3. Configurare sshd per controllare la KRL
# /etc/ssh/sshd_config:
# RevokedKeys /etc/ssh/revoked_keys

# 4. Rigenerare le host keys del server (se compromesse)
sudo rm /etc/ssh/ssh_host_*
sudo ssh-keygen -A                   # Rigenera tutte le host keys
sudo systemctl restart sshd

# 5. Documentare l'incidente (timestamp UTC ISO 8601)
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) - Chiave $COMPROMISED_KEY_FINGERPRINT revocata" >> /var/log/ssh-key-audit.log
```

---

## SSH Config File — Deep Dive

Il file `~/.ssh/config` è il modo più efficiente per gestire connessioni SSH multiple. Viene letto dall'alto verso il basso; la **prima corrispondenza** vince per ogni direttiva.

### Direttive Globali

```bash
# ~/.ssh/config — Sezione globale

Host *
    # === KEEPALIVE ===
    ServerAliveInterval 60          # Invia keepalive ogni 60 secondi
    ServerAliveCountMax 3           # 3 tentativi falliti → disconnetti
    TCPKeepAlive yes                # Keepalive a livello TCP

    # === CHIAVI ===
    AddKeysToAgent yes              # Aggiungi chiavi all'agent automaticamente
    IdentitiesOnly yes              # Usa SOLO la chiave specificata per IdentityFile
                                    # Senza questo, ssh prova TUTTE le chiavi nell'agent

    # === SICUREZZA ===
    HashKnownHosts yes              # Hash degli hostname in known_hosts (privacy)
    VisualHostKey yes               # Mostra randomart alla connessione

    # === MULTIPLEXING ===
    ControlMaster auto              # Riusa connessioni esistenti
    ControlPath ~/.ssh/sockets/%r@%h-%p
    ControlPersist 600              # Mantieni connessione master 10 minuti

    # === LOGGING ===
    LogLevel ERROR                  # Livello log (QUIET, FATAL, ERROR, INFO, VERBOSE, DEBUG)

    # === COMPRESSION ===
    Compression yes                 # Abilita compressione (utile su link lenti)

    # === STRICT HOST KEY CHECKING ===
    StrictHostKeyChecking ask       # ask (default), yes, no, accept-new
    # ask       = chiede conferma per host sconosciuti
    # yes       = rifiuta host non in known_hosts
    # no        = accetta tutto (INSICURO — solo per test)
    # accept-new = accetta nuovi, rifiuta cambiati (buon compromesso)
    UpdateHostKeys yes              # Aggiorna host keys automaticamente (OpenSSH 8.4+)
```

### ProxyJump e ProxyCommand

```bash
# ProxyJump — Metodo moderno (OpenSSH 7.3+)
Host internal-db
    HostName 10.0.1.200
    User dbadmin
    ProxyJump bastion               # Salta attraverso bastion

# Catena di jump multipli
Host deep-internal
    HostName 172.16.0.50
    User admin
    ProxyJump bastion1,bastion2     # bastion1 → bastion2 → target

# ProxyCommand — Metodo legacy (compatibilità)
Host internal-legacy
    HostName 10.0.1.100
    User admin
    ProxyCommand ssh -W %h:%p bastion
    # %h = hostname del target, %p = porta del target

# ProxyCommand con netcat (sistemi molto vecchi)
Host ancient-server
    HostName 10.0.1.5
    User admin
    ProxyCommand ssh bastion nc %h %p

# Comando personalizzato (tunnel via HTTP proxy)
Host behind-proxy
    HostName server.example.com
    ProxyCommand connect -H proxy.corp.com:8080 %h %p
    # 'connect' è un tool per tunnel HTTP CONNECT
```

### ControlMaster, ControlPath, ControlPersist

```bash
# ControlMaster: riusa una connessione TCP esistente
# Vantaggi: connessione istantanea, nessun nuovo handshake/autenticazione
Host *
    ControlMaster auto
    # auto     = riusa master se esiste, altrimenti diventa master
    # yes      = questa connessione è sempre il master
    # no       = non usare multiplexing
    # ask      = chiede conferma per diventare master
    # autoask  = riusa se esiste, chiede se deve diventare master

    ControlPath ~/.ssh/sockets/%r@%h-%p
    # %r = username remoto
    # %h = hostname remoto
    # %p = porta remota
    # %C = hash univoco di %l%h%p%r (alternativa compatta)
    # NOTA: il percorso non deve essere troppo lungo (limite socket Unix ~100 char)
    # Alternativa compatta:
    # ControlPath ~/.ssh/sockets/%C

    ControlPersist 600
    # Tempo in secondi per mantenere il master dopo la chiusura dell'ultimo client
    # yes = master rimane attivo indefinitamente
    # 600 = 10 minuti
    # 0 o no = chiudi master quando l'ultimo client esce

# Creare la directory per i socket
mkdir -p ~/.ssh/sockets
chmod 700 ~/.ssh/sockets

# Gestire connessioni master manualmente
ssh -O check server                 # Verifica se master è attivo
ssh -O stop server                  # Chiudi il master
ssh -O exit server                  # Termina il master
ssh -O forward -L 8080:localhost:80 server  # Aggiungere forwarding a connessione esistente
ssh -O cancel -L 8080:localhost:80 server   # Rimuovere forwarding

# Disabilitare multiplexing per una connessione specifica
ssh -o ControlMaster=no server
ssh -S none server                  # Equivalente
```

### Port Forwarding nel Config

```bash
# LocalForward — Servizio remoto accessibile localmente
Host tunnel-db
    HostName bastion.example.com
    User admin
    LocalForward 5432 db-server:5432     # PostgreSQL
    LocalForward 3306 db-server:3306     # MySQL
    LocalForward 6379 redis-server:6379  # Redis

# RemoteForward — Servizio locale esposto sul server
Host expose-dev
    HostName vps.example.com
    User admin
    RemoteForward 8080 localhost:3000    # Dev server locale esposto su VPS:8080

# DynamicForward — SOCKS proxy
Host socks-proxy
    HostName proxy-server.example.com
    User admin
    DynamicForward 1080                  # SOCKS5 su localhost:1080

# GatewayPorts — Binding su tutte le interfacce per RemoteForward
Host gateway
    HostName server.example.com
    User admin
    RemoteForward 0.0.0.0:8080 localhost:3000
    # Il server deve avere GatewayPorts yes in sshd_config

# ExitOnForwardFailure — Fallisci se il forwarding non riesce
Host critical-tunnel
    HostName server.example.com
    User admin
    LocalForward 5432 db:5432
    ExitOnForwardFailure yes            # Esci se la porta è già in uso
```

### Match Blocks

```bash
# Match permette condizioni avanzate (OpenSSH 6.5+)

# Basato su hostname
Match host "*.internal.example.com"
    ProxyJump bastion
    User admin

# Basato su utente
Match user "deploy"
    IdentityFile ~/.ssh/id_deploy
    ForwardAgent no

# Basato su rete locale (exec verifica la condizione)
Match exec "ip route get 10.0.0.1 2>/dev/null | grep -q 'dev eth0'"
    # Siamo nella rete interna, connessione diretta
    ProxyJump none

Match exec "! ip route get 10.0.0.1 2>/dev/null | grep -q 'dev eth0'"
    # Siamo fuori dalla rete, usa VPN/bastion
    ProxyJump bastion

# Combinare condizioni
Match host "prod-*" user "admin"
    IdentityFile ~/.ssh/id_prod
    RequestTTY no

# Match canonical — dopo la risoluzione dell'hostname
Match canonical host "*.example.com"
    User deploy
    Port 2222
```

### Direttive Avanzate

```bash
# === ESCAPE CHARACTER ===
EscapeChar ~                        # Default. ~. = disconnetti, ~C = command line, ~? = help
# EscapeChar none                  # Disabilita escape (utile per script/pipe binarie)

# === CIFRATURA ===
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com
MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org
HostKeyAlgorithms ssh-ed25519-cert-v01@openssh.com,ssh-ed25519

# === CANONICALIZZAZIONE ===
CanonicalizeHostname yes            # Risolvi hostname prima del matching
CanonicalDomains example.com corp.example.com
CanonicalizeMaxDots 0               # Solo hostname senza punti vengono canonicalizzati
CanonicalizeFallbackLocal yes       # Fallback a hostname originale se la risoluzione fallisce

# === MULTIPLEXING AVANZATO ===
ForkAfterAuthentication yes         # Equivalente a -f (background dopo auth)
RequestTTY auto                     # auto, yes, no, force

# === SEND/SET ENV ===
SetEnv LANG=en_US.UTF-8             # Imposta variabile d'ambiente sull'host remoto
SendEnv LANG LC_*                   # Invia variabili d'ambiente locali al server
# Il server deve avere AcceptEnv configurato in sshd_config

# === INCLUDE ===
Include ~/.ssh/config.d/*           # Include file aggiuntivi (OpenSSH 7.3+)
# Utile per organizzare config per progetto/cliente

# === CONNECTION TIMEOUT ===
ConnectTimeout 10                   # Timeout TCP in secondi (default: nessun limite)
ConnectionAttempts 3                # Numero di tentativi di connessione

# === FINGERPRINT HASH ===
FingerprintHash sha256              # sha256 (default) o md5

# === USER KNOWN HOSTS ===
UserKnownHostsFile ~/.ssh/known_hosts ~/.ssh/known_hosts.d/%k
# %k = tipo di host key
GlobalKnownHostsFile /etc/ssh/ssh_known_hosts
```

### Config Completo Commentato

```bash
# ~/.ssh/config — Esempio completo per ambienti reali

# Include config per progetto
Include ~/.ssh/config.d/*

# === DEFAULT GLOBALI ===
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
    AddKeysToAgent yes
    IdentitiesOnly yes
    HashKnownHosts yes
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%C
    ControlPersist 600
    Compression yes
    StrictHostKeyChecking accept-new
    UpdateHostKeys yes

# === BASTION / JUMP HOST ===
Host bastion
    HostName bastion.example.com
    User jumpuser
    IdentityFile ~/.ssh/id_bastion
    ControlPersist 1800              # 30 minuti (usato spesso)
    ForwardAgent no

# === SERVER PRODUZIONE ===
Host prod
    HostName 10.0.1.100
    User admin
    Port 22
    IdentityFile ~/.ssh/id_prod
    ProxyJump bastion
    ForwardAgent no

Host prod-db
    HostName 10.0.1.200
    User dbadmin
    IdentityFile ~/.ssh/id_prod
    ProxyJump bastion
    LocalForward 5432 localhost:5432  # PostgreSQL locale

Host prod-redis
    HostName 10.0.1.201
    User admin
    IdentityFile ~/.ssh/id_prod
    ProxyJump bastion
    LocalForward 6379 localhost:6379

# === SERVER STAGING ===
Host staging
    HostName staging.example.com
    User deploy
    IdentityFile ~/.ssh/id_staging

# === WILDCARD: tutti i server interni ===
Host 10.0.1.*
    User admin
    IdentityFile ~/.ssh/id_prod
    ProxyJump bastion

Host *.example.com
    User deploy
    IdentityFile ~/.ssh/id_deploy

# === TUNNEL PRECONFIGURATI ===
Host tunnel-db
    HostName bastion.example.com
    User admin
    LocalForward 5432 db-server:5432
    LocalForward 3306 mysql-server:3306
    IdentityFile ~/.ssh/id_bastion
    RequestTTY no
    ExitOnForwardFailure yes

Host socks
    HostName proxy.example.com
    User admin
    DynamicForward 1080
    RequestTTY no
    ExitOnForwardFailure yes

# === AMBIENTI DI SVILUPPO ===
Host dev-vm
    HostName 192.168.122.10
    User dev
    IdentityFile ~/.ssh/id_dev
    StrictHostKeyChecking no         # VM ricreate spesso
    UserKnownHostsFile /dev/null     # Non salvare fingerprint
    LogLevel ERROR

# === GITHUB ===
Host github.com
    User git
    IdentityFile ~/.ssh/id_github
    ControlMaster no                 # GitHub non supporta multiplexing

# === GITLAB ===
Host gitlab.example.com
    User git
    IdentityFile ~/.ssh/id_gitlab
    PreferredAuthentications publickey
```

---

## SSH Tunneling — Masterclass

Il tunneling SSH crea canali crittografati per trasportare traffico di rete arbitrario attraverso una connessione SSH.

### Local Port Forwarding (-L)

Rendi accessibile un servizio remoto come se fosse locale. Il client SSH ascolta su una porta locale e inoltra il traffico al server remoto.

```bash
# Sintassi: -L [bind_address:]local_port:remote_host:remote_port
ssh -L 8080:localhost:80 user@server
# Ora http://localhost:8080 accede alla porta 80 del server
# "localhost" qui è relativo al SERVER, non al client

# Database remoto accessibile localmente
ssh -L 5432:db-server:5432 user@bastion
# psql -h localhost -p 5432 connette al database remoto via bastion
# Il bastion si connette a db-server:5432

# Bind su tutte le interfacce (non solo localhost)
ssh -L 0.0.0.0:8080:localhost:80 user@server
# ATTENZIONE: altri nella rete possono accedere alla porta!

# Bind su interfaccia specifica
ssh -L 192.168.1.100:8080:localhost:80 user@server

# In background (senza shell interattiva)
ssh -fNL 8080:localhost:80 user@server
# -f = background    -N = no comando    -L = local forward

# Multiple forwards in una connessione
ssh -L 5432:db:5432 -L 6379:redis:6379 -L 8080:web:80 user@bastion

# Forward con tunnel UNIX socket (OpenSSH 6.7+)
ssh -L /tmp/local.sock:/var/run/remote.sock user@server

# Schema di flusso:
#
# Client                  SSH Server (bastion)        Target (db-server)
# ┌───────────┐           ┌───────────┐              ┌───────────┐
# │ app ──────┼──:5432───→│ tunnel ───┼──────────────→│ :5432     │
# │ localhost  │  SSH crip │           │  rete interna │ PostgreSQL│
# └───────────┘           └───────────┘              └───────────┘
```

### Remote Port Forwarding (-R)

Esponi un servizio locale attraverso il server remoto. Il server SSH ascolta su una porta e inoltra il traffico alla macchina locale.

```bash
# Sintassi: -R [bind_address:]remote_port:local_host:local_port
ssh -R 8080:localhost:3000 user@server
# Ora server:8080 accede alla porta 3000 della macchina locale

# Esporre servizio di sviluppo locale via VPS pubblico
ssh -R 80:localhost:3000 user@vps
# Il mondo può accedere a vps:80 → arriva al dev server locale

# Bind su tutte le interfacce del server remoto
ssh -R 0.0.0.0:8080:localhost:3000 user@server
# Richiede GatewayPorts yes in sshd_config del server

# GatewayPorts configurazione:
# no              → bind solo su loopback (default, sicuro)
# yes             → bind su tutte le interfacce
# clientspecified  → il client decide (con 0.0.0.0: o *:)

# In background
ssh -fNR 8080:localhost:3000 user@server

# Forward remoto dinamico (SOCKS inverso, OpenSSH 7.6+)
ssh -R 1080 user@server
# Crea un proxy SOCKS sul server, traffico torna al client

# Schema di flusso:
#
# Client locale                SSH Server (VPS)           Utente esterno
# ┌───────────┐               ┌───────────┐             ┌───────────┐
# │ :3000 ←───┼───tunnel──────┤ :8080 ←───┼─────────────┤ browser   │
# │ dev server│  SSH crip      │           │  internet    │           │
# └───────────┘               └───────────┘             └───────────┘
```

### Dynamic SOCKS Proxy (-D)

Crea un proxy SOCKS5 attraverso il server SSH. Tutto il traffico viene instradato attraverso il tunnel.

```bash
# Sintassi: -D [bind_address:]port
ssh -D 1080 user@server
# Configura il browser: SOCKS5 proxy su localhost:1080
# Tutto il traffico del browser passa per il server SSH

# In background
ssh -fND 1080 user@server

# Bind su interfaccia specifica
ssh -D 127.0.0.1:1080 user@server

# Usare con strumenti da riga di comando
curl --socks5-hostname localhost:1080 https://example.com
# --socks5-hostname = la risoluzione DNS passa anch'essa per il proxy

# Con wget
export http_proxy=socks5h://localhost:1080
export https_proxy=socks5h://localhost:1080
wget https://example.com

# Con tsocks o proxychains (per programmi che non supportano SOCKS)
# /etc/proxychains.conf:
# socks5 127.0.0.1 1080
proxychains curl https://example.com
proxychains nmap -sT target.com

# Schema di flusso:
#
# Client                     SSH Server               Internet
# ┌───────────┐             ┌───────────┐           ┌───────────┐
# │ browser ──┼──SOCKS5────→│ proxy ────┼──────────→│ siti web  │
# │ :1080     │  SSH crip    │           │ cleartext │           │
# └───────────┘             └───────────┘           └───────────┘
#
# NOTA: il traffico tra SSH server e destinazione finale NON è crittografato.
# SSH protegge solo il tratto client ↔ server.
```

### ProxyJump Chains

```bash
# Catena di jump host per raggiungere reti profonde
ssh -J bastion1,bastion2,bastion3 user@target

# Ogni hop usa una connessione SSH nidificata:
# client → bastion1 → bastion2 → bastion3 → target

# Nel config:
Host target
    HostName 172.16.0.50
    User admin
    ProxyJump bastion1,bastion2,bastion3

# Con opzioni diverse per ogni hop:
Host bastion1
    HostName bastion1.example.com
    User jump1
    IdentityFile ~/.ssh/id_bastion1

Host bastion2
    HostName 10.0.1.10
    User jump2
    IdentityFile ~/.ssh/id_bastion2
    ProxyJump bastion1

Host bastion3
    HostName 172.16.0.1
    User jump3
    IdentityFile ~/.ssh/id_bastion3
    ProxyJump bastion2

Host target
    HostName 172.16.0.50
    User admin
    IdentityFile ~/.ssh/id_target
    ProxyJump bastion3

# SCP/rsync attraverso catena di jump:
scp -J bastion1,bastion2 file.txt target:/tmp/
rsync -avz -e "ssh -J bastion1,bastion2" dir/ target:/backup/
```

### Tunnel Persistenti con autossh

```bash
# autossh mantiene tunnel SSH attivi automaticamente, riconnettendo in caso di caduta

# Installazione
sudo apt install autossh              # Debian/Ubuntu
sudo dnf install autossh              # Fedora/RHEL

# Tunnel locale persistente
autossh -M 0 -fNL 5432:db:5432 user@bastion
# -M 0 = usa ServerAliveInterval di OpenSSH per il monitoring (consigliato)
# -f   = background
# -N   = no comando remoto
# -L   = local forward

# Con parametri SSH per il keepalive
autossh -M 0 -o "ServerAliveInterval 30" -o "ServerAliveCountMax 3" \
    -fNL 5432:db:5432 user@bastion

# SOCKS proxy persistente
autossh -M 0 -fND 1080 user@proxy-server

# Come servizio systemd
# /etc/systemd/system/ssh-tunnel-db.service
# [Unit]
# Description=SSH Tunnel to Database
# After=network-online.target
# Wants=network-online.target
#
# [Service]
# Type=simple
# User=tunnel
# ExecStart=/usr/bin/autossh -M 0 -NL 5432:db:5432 user@bastion \
#     -o "ServerAliveInterval=30" -o "ServerAliveCountMax=3" \
#     -o "ExitOnForwardFailure=yes" \
#     -i /home/tunnel/.ssh/id_tunnel
# Restart=always
# RestartSec=10
#
# [Install]
# WantedBy=multi-user.target
```

---

## SSH Agent e Forwarding

### SSH Agent

L'SSH agent mantiene le chiavi private decriptate in memoria, evitando di digitare la passphrase ad ogni connessione.

```bash
# Avviare l'agent
eval $(ssh-agent)                   # Avvia agent e setta variabili
# Oppure: ssh-agent è spesso già avviato dal desktop environment

# Aggiungere chiavi
ssh-add                             # Aggiunge la chiave default
ssh-add ~/.ssh/id_prod              # Chiave specifica
ssh-add -t 3600 ~/.ssh/id_prod     # Con timeout (1 ora)

# Lista chiavi caricate
ssh-add -l                          # Fingerprint
ssh-add -L                          # Chiavi pubbliche complete

# Rimuovere
ssh-add -d ~/.ssh/id_prod           # Rimuovi specifica
ssh-add -D                          # Rimuovi tutte
```

### Agent Forwarding: Rischi e Alternative

L'agent forwarding (`ssh -A`) è pericoloso. Comprendere il modello di minaccia è fondamentale.

```bash
# === COME FUNZIONA ===
# L'agent forwarding crea un socket UNIX sul server remoto:
# /tmp/ssh-XXXX/agent.NNNN
# Questo socket è un proxy verso l'agent locale.

# Il RISCHIO: chiunque abbia accesso root sul server intermedio può:
# 1. Usare il socket per firmare richieste con le TUE chiavi
# 2. Impersonarti verso qualsiasi server a cui le tue chiavi danno accesso
# 3. Farlo SENZA che tu lo sappia

# Attacco (visuale):
# Tu → bastion (agent forwarding attivo)
#        ↓
#   root@bastion può usare il tuo agent socket
#        ↓
#   root@bastion → accede a QUALSIASI server con le tue chiavi

# === ALTERNATIVA SICURA: ProxyJump ===
# ProxyJump NON espone l'agent al server intermedio.
# La connessione SSH viene nidificata: il bastion vede solo traffico cifrato.

ssh -J bastion user@target          # L'agent NON è esposto sul bastion

# Equivalente nel config:
Host target
    ProxyJump bastion               # Sicuro, nessun agent forwarding

# === SE DEVI USARE AGENT FORWARDING ===
# 1. Solo verso server di cui ti fidi completamente
# 2. Usa -c (confirm) con ssh-add per richiedere conferma per ogni uso
ssh-add -c ~/.ssh/id_prod           # Conferma interattiva

# 3. Limita il tempo di vita dell'agent
ssh-add -t 300 ~/.ssh/id_prod      # 5 minuti

# 4. Usa Agent Restriction (OpenSSH 8.9+)
ssh -o "AddKeysToAgent confirm" -A user@bastion

# 5. Monitora l'uso dell'agent
# Sul bastion, root può fare:
SSH_AUTH_SOCK=/tmp/ssh-XXXX/agent.NNNN ssh-add -l
# Se puoi farlo, può farlo anche un attaccante.

# === CONFRONTO ===
# ┌──────────────────┬────────────────────────────────┐
# │ Agent Forwarding │ ProxyJump                      │
# ├──────────────────┼────────────────────────────────┤
# │ Espone chiavi    │ Non espone chiavi               │
# │ root può abusare │ root vede solo traffico cifrato │
# │ Funziona sempre  │ Richiede OpenSSH 7.3+           │
# │ ssh -A           │ ssh -J                          │
# └──────────────────┴────────────────────────────────┘
```

---

## Autenticazione Basata su Certificati

L'autenticazione con certificati SSH è la soluzione scalabile per organizzazioni con molti server e utenti. Elimina la necessità di gestire `authorized_keys` su ogni server.

### Setup della CA SSH

```bash
# Una CA (Certificate Authority) SSH è semplicemente una coppia di chiavi
# usata per firmare altre chiavi.

# === CREARE LA CA ===

# CA per utenti (firma le chiavi degli utenti)
ssh-keygen -t ed25519 -f /etc/ssh/ca_user_key -C "SSH User CA"
# Proteggere con passphrase FORTE. Questa chiave firma i certificati utente.

# CA per host (firma le chiavi dei server)
ssh-keygen -t ed25519 -f /etc/ssh/ca_host_key -C "SSH Host CA"
# Proteggere con passphrase FORTE. Questa chiave firma i certificati host.

# Permessi
chmod 600 /etc/ssh/ca_user_key /etc/ssh/ca_host_key
chmod 644 /etc/ssh/ca_user_key.pub /etc/ssh/ca_host_key.pub

# La chiave pubblica della CA va distribuita:
# - ca_user_key.pub → su TUTTI i server (TrustedUserCAKeys)
# - ca_host_key.pub → su TUTTI i client (@cert-authority in known_hosts)
```

### Certificati Utente

```bash
# === FIRMARE LA CHIAVE DI UN UTENTE ===

# L'utente fornisce la propria chiave PUBBLICA, la CA la firma
ssh-keygen -s /etc/ssh/ca_user_key \
    -I "admin-certificate-2026" \
    -n admin,deploy \
    -V +52w \
    -z 1001 \
    /path/to/user_key.pub

# Spiegazione opzioni:
# -s ca_key       = Chiave privata della CA per firmare
# -I identity     = Identificativo del certificato (per audit/log)
# -n principals   = Username permessi (separati da virgola)
# -V validity     = Periodo di validità (+52w = 52 settimane, +1d = 1 giorno)
# -z serial       = Numero seriale (per tracciamento/revoca)

# Output: user_key-cert.pub (il certificato)

# Validità tipiche:
# -V +8h          = 8 ore (certificato per singola sessione di lavoro)
# -V +1d          = 1 giorno
# -V +1w          = 1 settimana
# -V +52w         = 1 anno
# -V "20260101:20261231" = data esatta inizio:fine (YYYYMMDD o YYYYMMDDHHMMSS)

# Con opzioni restrittive (come authorized_keys):
ssh-keygen -s /etc/ssh/ca_user_key \
    -I "backup-agent" \
    -n backup \
    -V +24h \
    -O no-port-forwarding \
    -O no-pty \
    -O no-agent-forwarding \
    -O no-x11-forwarding \
    -O source-address=10.0.1.0/24 \
    -O force-command="/usr/local/bin/backup.sh" \
    backup_key.pub

# Opzioni -O disponibili:
# clear                = Rimuovi tutte le estensioni
# force-command=cmd    = Forza un comando specifico
# no-agent-forwarding  = Vieta agent forwarding
# no-port-forwarding   = Vieta port forwarding
# no-pty               = Vieta allocazione PTY
# no-user-rc           = Non eseguire ~/.ssh/rc
# no-x11-forwarding    = Vieta X11 forwarding
# permit-pty           = Permetti allocazione PTY
# source-address=CIDR  = Limita IP sorgente

# === VISUALIZZARE UN CERTIFICATO ===
ssh-keygen -Lf user_key-cert.pub
# Mostra: tipo, chiave pubblica, firmatario, identity, principals,
#         validità, opzioni, estensioni, numero seriale

# === CONFIGURARE IL SERVER PER ACCETTARE CERTIFICATI UTENTE ===
# /etc/ssh/sshd_config:
TrustedUserCAKeys /etc/ssh/ca_user_key.pub

# Con AuthorizedPrincipalsFile (mapping principals → utenti):
AuthorizedPrincipalsFile /etc/ssh/auth_principals/%u
# Creare il file per ogni utente:
# /etc/ssh/auth_principals/admin → contiene "admin" (un principal per riga)
# /etc/ssh/auth_principals/deploy → contiene "deploy"

# Se AuthorizedPrincipalsFile non è configurato, il principal nel certificato
# deve corrispondere ESATTAMENTE all'username di login.

# === LATO CLIENT: USARE IL CERTIFICATO ===
# L'utente posiziona user_key-cert.pub nella stessa directory della chiave privata
# SSH lo rileva automaticamente se il nome segue la convenzione:
# id_ed25519         (chiave privata)
# id_ed25519.pub     (chiave pubblica)
# id_ed25519-cert.pub (certificato)

# Oppure specificare esplicitamente:
ssh -i ~/.ssh/id_ed25519 -o CertificateFile=~/.ssh/id_ed25519-cert.pub user@server
```

### Certificati Host

I certificati host eliminano il messaggio "The authenticity of this host can't be established" — il client verifica il certificato del server firmato dalla CA.

```bash
# === FIRMARE LA HOST KEY DEL SERVER ===

# Sul server, copiare la host key pubblica:
# /etc/ssh/ssh_host_ed25519_key.pub

# Sulla CA, firmare:
ssh-keygen -s /etc/ssh/ca_host_key \
    -I "server1.example.com" \
    -h \
    -n server1.example.com,server1,10.0.1.100 \
    -V +52w \
    -z 2001 \
    /path/to/ssh_host_ed25519_key.pub

# -h = tipo HOST (non utente)
# -n = hostname validi (tutti i nomi/IP con cui ci si connette al server)

# Output: ssh_host_ed25519_key-cert.pub

# === CONFIGURARE IL SERVER ===
# Copiare il certificato sul server:
# /etc/ssh/ssh_host_ed25519_key-cert.pub

# /etc/ssh/sshd_config:
HostCertificate /etc/ssh/ssh_host_ed25519_key-cert.pub

# Restart:
sudo systemctl restart sshd

# === CONFIGURARE I CLIENT ===
# In ~/.ssh/known_hosts (o /etc/ssh/ssh_known_hosts):
@cert-authority *.example.com ssh-ed25519 AAAA...contenuto_di_ca_host_key.pub...

# Ora i client accetteranno automaticamente qualsiasi server con un certificato
# firmato dalla CA per il dominio *.example.com
# Nessun messaggio "fingerprint verification" per nuovi server.
```

### Validità e Rinnovo

```bash
# Controllare la scadenza di un certificato
ssh-keygen -Lf cert.pub | grep Valid
# Output: Valid: from 2026-01-01T00:00:00 to 2026-12-31T23:59:59

# === AUTOMAZIONE RINNOVO ===
# Script di rinnovo periodico (da eseguire con cron):
#!/bin/bash
CERT_FILE="$HOME/.ssh/id_ed25519-cert.pub"
CA_HOST="ca.example.com"

# Controlla se il certificato scade entro 7 giorni
if ssh-keygen -Lf "$CERT_FILE" 2>/dev/null | grep -q "Valid"; then
    EXPIRY=$(ssh-keygen -Lf "$CERT_FILE" | grep "Valid" | awk '{print $NF}')
    EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s 2>/dev/null)
    NOW_EPOCH=$(date +%s)
    DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))

    if [ "$DAYS_LEFT" -lt 7 ]; then
        echo "Certificato scade tra $DAYS_LEFT giorni. Rinnovo in corso..."
        # Invia la pubkey alla CA per la rifirma
        scp "$HOME/.ssh/id_ed25519.pub" "$CA_HOST:/tmp/renew_key.pub"
        ssh "$CA_HOST" "/usr/local/bin/sign-user-cert.sh /tmp/renew_key.pub"
        scp "$CA_HOST:/tmp/renew_key-cert.pub" "$CERT_FILE"
    fi
fi

# === CERTIFICATI SHORT-LIVED CON VAULT ===
# HashiCorp Vault può fungere da CA SSH automatica:
# vault write ssh-client-signer/sign/admin public_key=@$HOME/.ssh/id_ed25519.pub
# Genera certificati con validità breve (30 min) on-demand.
```

### Revoca Certificati

```bash
# === KEY REVOCATION LIST (KRL) ===

# Creare una KRL vuota
ssh-keygen -k -f /etc/ssh/revoked_keys

# Revocare un certificato per seriale
ssh-keygen -k -f /etc/ssh/revoked_keys -s /etc/ssh/ca_user_key -z 1001

# Revocare un certificato per chiave pubblica
ssh-keygen -k -f /etc/ssh/revoked_keys -s /etc/ssh/ca_user_key compromised_key.pub

# Revocare un certificato per identity
ssh-keygen -k -f /etc/ssh/revoked_keys -s /etc/ssh/ca_user_key \
    -z 1001-1010  # Revocare un range di seriali

# Aggiungere alla KRL esistente (update)
ssh-keygen -k -u -f /etc/ssh/revoked_keys -s /etc/ssh/ca_user_key new_compromised.pub

# Configurare sshd per usare la KRL
# /etc/ssh/sshd_config:
RevokedKeys /etc/ssh/revoked_keys

# Verificare il contenuto della KRL
ssh-keygen -Qlf /etc/ssh/revoked_keys

# === DISTRIBUZIONE KRL ===
# La KRL deve essere distribuita su TUTTI i server.
# Usare un meccanismo di distribuzione (rsync, Puppet, Ansible, Chef).
# La KRL è un file binario compatto, efficiente anche con migliaia di revoche.
```

---

## SSHD Hardening

### Configurazione Server Sicura

```bash
# /etc/ssh/sshd_config

# AUTENTICAZIONE
PermitRootLogin no                  # Disabilita login root (usare sudo)
# PermitRootLogin prohibit-password  # Root solo con chiave (alternativa)
PasswordAuthentication no           # Solo autenticazione con chiave
PubkeyAuthentication yes
AuthenticationMethods publickey     # Solo chiave pubblica
MaxAuthTries 3                      # Max tentativi
LoginGraceTime 30                   # Timeout login (secondi)

# UTENTI E GRUPPI
AllowUsers admin deploy             # Solo questi utenti (whitelist)
# AllowGroups ssh-users             # Solo questo gruppo
DenyUsers testuser                  # Blocca specifici utenti

# RETE
Port 22                             # Porta (cambiarla offre poca sicurezza reale)
ListenAddress 0.0.0.0              # Interfacce di ascolto
AddressFamily inet                  # Solo IPv4 (o inet6, o any)

# SICUREZZA
PermitEmptyPasswords no
X11Forwarding no                    # Disabilita X11 (a meno che necessario)
AllowTcpForwarding yes              # Necessario per tunnel/forwarding
AllowAgentForwarding no             # Disabilita se non necessario
PrintMotd no
PrintLastLog yes

# CRITTOGRAFIA (rimuovere algoritmi deboli)
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com
HostKeyAlgorithms ssh-ed25519-cert-v01@openssh.com,ssh-ed25519

# TIMEOUT
ClientAliveInterval 300             # Keepalive ogni 5 minuti
ClientAliveCountMax 2               # 2 tentativi prima di disconnettere
# = disconnessione dopo 10 minuti di inattività

# BANNER
Banner /etc/ssh/banner              # Banner pre-login (avviso legale)

# LOGGING
LogLevel VERBOSE                    # Log dettagliato
# SyslogFacility AUTH               # Default: AUTH
```

```bash
# Dopo le modifiche
sudo sshd -t                        # Test configurazione
sudo systemctl restart sshd

# IMPORTANTE: PRIMA di disabilitare password auth,
# verificare che la chiave funzioni in un'altra sessione!
```

### Direttive CIS Benchmark

Le seguenti direttive allineano la configurazione SSH con CIS (Center for Internet Security) Benchmark per Linux.

```bash
# /etc/ssh/sshd_config — CIS Benchmark compliance

# === CIS 5.2.1: Permessi sshd_config ===
# File: /etc/ssh/sshd_config deve avere: owner root, mode 0600
# sudo chown root:root /etc/ssh/sshd_config
# sudo chmod 600 /etc/ssh/sshd_config

# === CIS 5.2.2: Permessi chiavi private host ===
# /etc/ssh/ssh_host_*_key devono avere: owner root, mode 0600
# for f in /etc/ssh/ssh_host_*_key; do chmod 600 "$f"; chown root:root "$f"; done

# === CIS 5.2.3: Permessi chiavi pubbliche host ===
# /etc/ssh/ssh_host_*_key.pub devono avere: owner root, mode 0644
# for f in /etc/ssh/ssh_host_*_key.pub; do chmod 644 "$f"; chown root:root "$f"; done

# === CIS 5.2.4–5.2.7: Configurazione accesso ===
Protocol 2                          # Solo SSHv2 (implicito in OpenSSH 7.4+)
MaxAuthTries 4                      # CIS raccomanda ≤4
MaxSessions 10                      # Max sessioni per connessione
MaxStartups 10:30:60                # Rate limiting connessioni:
# 10 = connessioni non autenticate prima del rate limiting
# 30 = probabilità (%) di rifiuto per nuova connessione
# 60 = max connessioni non autenticate (rifiuto al 100%)

# === CIS 5.2.8–5.2.11: Autenticazione ===
PermitRootLogin no
PasswordAuthentication no
PermitEmptyPasswords no
ChallengeResponseAuthentication no   # Disabilita se non si usa PAM 2FA
UsePAM yes                           # Richiesto per PAM (account/session)
KbdInteractiveAuthentication no      # Nome alternativo per ChallengeResponseAuth

# === CIS 5.2.12: Idle timeout ===
ClientAliveInterval 300              # 5 minuti
ClientAliveCountMax 3                # 3 keepalive, poi disconnetti
# Timeout effettivo: 300 * 3 = 15 minuti

# === CIS 5.2.13–5.2.15: Restrizioni ===
PermitUserEnvironment no             # Non permettere all'utente di impostare env
AllowTcpForwarding no                # Disabilita se non necessario
X11Forwarding no
AllowAgentForwarding no

# === CIS 5.2.16: Banner ===
Banner /etc/ssh/banner
# /etc/ssh/banner deve contenere un avviso legale

# === CIS 5.2.17: UseDNS ===
UseDNS no                           # Disabilita reverse DNS lookup (velocizza login)

# === CIS 5.2.18: Login Grace Time ===
LoginGraceTime 60                   # Max 60 secondi per completare il login

# === CIS 5.2.19: Cifratura forte ===
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr
MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com,hmac-sha2-256,hmac-sha2-512

# === CIS: Moduli DH sicuri ===
# Rimuovere moduli DH deboli (<3072 bit):
# sudo awk '$5 >= 3071' /etc/ssh/moduli > /etc/ssh/moduli.safe
# sudo mv /etc/ssh/moduli.safe /etc/ssh/moduli

# === VERIFICA CONFIGURAZIONE ===
# Controllare che sshd compili la config senza errori:
sudo sshd -T                        # Dump della configurazione effettiva
sudo sshd -T -C user=admin          # Config effettiva per uno specifico utente
sudo sshd -t                        # Solo test syntax
```

### Match Blocks nel sshd_config

```bash
# Match permette di applicare direttive diverse per utente, gruppo, indirizzo o host

# Utenti SFTP-only (chroot)
Match Group sftp-users
    ForceCommand internal-sftp
    ChrootDirectory /home/%u
    AllowTcpForwarding no
    AllowAgentForwarding no
    X11Forwarding no
    PermitTunnel no

# Accesso deploy limitato
Match User deploy
    PasswordAuthentication no
    AllowTcpForwarding no
    PermitOpen none
    ForceCommand /usr/local/bin/deploy-only.sh

# Accesso dalla rete interna (più permissivo)
Match Address 10.0.0.0/8,172.16.0.0/12,192.168.0.0/16
    PasswordAuthentication yes       # Password consentita dalla LAN
    MaxAuthTries 5
    AllowTcpForwarding yes

# Accesso dalla rete esterna (più restrittivo)
Match Address *,!10.0.0.0/8,!172.16.0.0/12,!192.168.0.0/16
    PasswordAuthentication no
    MaxAuthTries 3
    AllowTcpForwarding no
    MaxSessions 2

# Combinare condizioni
Match User admin Address 10.0.1.0/24
    AllowTcpForwarding yes
    AllowAgentForwarding yes

# Utente di monitoraggio
Match User monitoring
    PasswordAuthentication no
    ForceCommand /usr/local/bin/health-check.sh
    AllowTcpForwarding no
    PermitTTY no
```

### Banner e MOTD

```bash
# === BANNER PRE-LOGIN ===
# Mostrato PRIMA dell'autenticazione. Usare per avvisi legali.

# /etc/ssh/banner
# ╔══════════════════════════════════════════════════════╗
# ║  ATTENZIONE: Sistema riservato. L'accesso non       ║
# ║  autorizzato è proibito e sarà perseguito a norma   ║
# ║  di legge. Tutte le attività sono monitorate e      ║
# ║  registrate.                                         ║
# ╚══════════════════════════════════════════════════════╝

# /etc/ssh/sshd_config:
Banner /etc/ssh/banner

# === MOTD POST-LOGIN ===
# Mostrato DOPO l'autenticazione.
# /etc/motd                        — File statico
# /etc/update-motd.d/              — Script dinamici (Ubuntu)

# Disabilitare MOTD nel sshd_config:
PrintMotd no                        # Lasciare che PAM gestisca il MOTD

# Disabilitare anche il PrintLastLog se non necessario:
PrintLastLog no

# Esempio script dinamico /etc/update-motd.d/10-info:
#!/bin/bash
# echo "Server: $(hostname)"
# echo "Uptime: $(uptime -p)"
# echo "Disco:  $(df -h / | tail -1 | awk '{print $5}') utilizzato"
# echo "Ultimo login: $(lastlog -u $USER | tail -1)"
```

---

## Bastion / Jump Host — Architettura

Un bastion host (o jump host) è l'unico punto di ingresso SSH in una rete protetta. Tutto il traffico SSH passa attraverso il bastion, che funge da gateway di auditing e controllo.

### Design di un Bastion Host

```
Internet                        Rete Interna
                ┌─────────────┐
                │   BASTION   │
  SSH (22) ────→│             │────→ Server App (10.0.1.x)
                │  • Audit    │────→ Server DB  (10.0.2.x)
                │  • 2FA      │────→ Server Web (10.0.3.x)
                │  • Logging  │
                └─────────────┘
                      ↑
              Firewall: solo porta 22
              da IP autorizzati

Principi architetturali:
1. UNICO punto di ingresso SSH nella rete
2. Nessun dato applicativo sul bastion
3. Software minimale (solo sshd, audit, 2FA)
4. OS hardened (CIS benchmark, SELinux/AppArmor)
5. Logging centralizzato e immutabile
6. 2FA obbligatorio
7. Sessioni registrate (session recording)
```

### Configurazione del Bastion

```bash
# /etc/ssh/sshd_config — Bastion host

# Solo autenticazione con chiave + 2FA
AuthenticationMethods publickey,keyboard-interactive
PubkeyAuthentication yes
PasswordAuthentication no
KbdInteractiveAuthentication yes    # Per 2FA via PAM

# Nessun agent forwarding (gli utenti usano ProxyJump)
AllowAgentForwarding no
AllowTcpForwarding yes              # Necessario per ProxyJump
PermitTunnel no
X11Forwarding no
GatewayPorts no

# Solo utenti autorizzati
AllowGroups bastion-users

# Sessione limitata
ClientAliveInterval 180             # 3 minuti keepalive
ClientAliveCountMax 2               # Max 6 minuti inattivi
MaxSessions 5                       # Max 5 sessioni per utente

# Rate limiting aggressivo
MaxStartups 5:50:10                 # 5 concorrenti non-auth, 50% drop, max 10

# Logging verboso
LogLevel VERBOSE
# Con OpenSSH 9.0+, si può usare LogVerbose per logging selettivo:
# LogVerbose kex.c:*,auth*.c:*

# Banner di avviso
Banner /etc/ssh/banner

# Disabilitare tutto ciò che non serve
PermitUserEnvironment no
PermitUserRC no                     # Non eseguire ~/.ssh/rc
DisableForwarding no                # Lasciare attivo per ProxyJump
# (DisableForwarding sovrascrive AllowTcpForwarding, AllowAgentForwarding, etc.)

# Ambiente minimale
AcceptEnv LANG LC_*
PermitTTY yes                       # Necessario per shell interattiva

# === RESTRIZIONI IP (firewall o sshd) ===
# Usare firewall (iptables/nftables) per limitare gli IP sorgente.
# In alternativa, in sshd_config:
# Match Address !10.0.0.0/8,!172.16.0.0/12
#     DenyUsers *
```

### Auditing e Logging

```bash
# === SESSION RECORDING ===
# Registrare tutte le sessioni SSH per audit.

# Metodo 1: script(1) forzato
# Aggiungere al .bashrc forzato (/etc/profile.d/session-record.sh):
# if [ -n "$SSH_CONNECTION" ] && [ -z "$SESSION_RECORDED" ]; then
#     export SESSION_RECORDED=1
#     LOGDIR="/var/log/ssh-sessions"
#     LOGFILE="$LOGDIR/$(whoami)_$(date +%Y%m%d_%H%M%S)_$$.log"
#     script -qf "$LOGFILE"
#     exit
# fi

# Metodo 2: OpenSSH ForceCommand
# /etc/ssh/sshd_config:
# Match Group bastion-users
#     ForceCommand /usr/local/bin/session-recorder.sh

# Metodo 3: Soluzioni enterprise
# - Teleport (https://goteleport.com) — session recording, RBAC, audit
# - Boundary (https://www.boundaryproject.io) — HashiCorp
# - StrongDM — auditing + accesso granulare

# === LOG ANALISI ===
# Visualizzare tentativi SSH
sudo journalctl -u sshd --since "1 hour ago"
sudo grep "sshd" /var/log/auth.log | tail -50

# Tentativi di login falliti
sudo grep "Failed password" /var/log/auth.log
sudo grep "Invalid user" /var/log/auth.log
sudo grep "Connection closed by authenticating user" /var/log/auth.log

# Login riusciti
sudo grep "Accepted publickey" /var/log/auth.log
sudo grep "Accepted keyboard-interactive" /var/log/auth.log

# Chiavi usate per il login (con LogLevel VERBOSE)
sudo grep "Found matching" /var/log/auth.log
# Output: Found matching ED25519 key: SHA256:xxxx

# === CENTRALIZZAZIONE LOG ===
# Inviare i log a un SIEM o server syslog centralizzato:
# /etc/rsyslog.d/50-ssh.conf:
# auth.* @@syslog-server.example.com:514

# Oppure via journald:
# /etc/systemd/journald.conf:
# ForwardToSyslog=yes
```

---

## SFTP — Configurazione Avanzata

### Chroot SFTP

Un ambiente chroot SFTP confina gli utenti nella propria home directory, senza accesso al resto del filesystem.

```bash
# === PREREQUISITI ===
# La directory chroot deve essere di proprietà di root:root con permessi 755.
# L'utente scrive SOLO dentro una subdirectory.

# 1. Creare il gruppo
sudo groupadd sftp-users

# 2. Creare l'utente
sudo useradd -m -g sftp-users -s /usr/sbin/nologin sftpuser
sudo passwd sftpuser

# 3. Preparare la directory chroot
sudo chown root:root /home/sftpuser      # Root possiede la chroot directory
sudo chmod 755 /home/sftpuser
sudo mkdir -p /home/sftpuser/upload      # Directory scrivibile
sudo chown sftpuser:sftp-users /home/sftpuser/upload
sudo chmod 755 /home/sftpuser/upload

# 4. Configurare sshd
# /etc/ssh/sshd_config:
# Commentare la riga:
# Subsystem sftp /usr/lib/openssh/sftp-server
# E sostituire con:
Subsystem sftp internal-sftp

Match Group sftp-users
    ChrootDirectory /home/%u
    ForceCommand internal-sftp
    AllowTcpForwarding no
    AllowAgentForwarding no
    X11Forwarding no
    PermitTunnel no

# 5. Restart
sudo systemctl restart sshd

# 6. Test
sftp sftpuser@localhost
# L'utente vede / come la propria home
# Può scrivere solo in /upload/

# === TROUBLESHOOTING CHROOT ===
# Errore: "fatal: bad ownership or modes for chroot directory"
# → La directory chroot e TUTTI i componenti del path fino a /
#   devono essere di proprietà di root e non scrivibili da gruppo/altri.
# Controllare: ls -la /home/sftpuser/
# Deve essere: drwxr-xr-x root root

# Errore: "Write failed: Permission denied"
# → L'utente cerca di scrivere nella directory chroot stessa.
#   Deve scrivere nella subdirectory (es. /upload/).
```

### Accesso Ristretto

```bash
# === SFTP con chiave SSH e restrizioni ===
# In authorized_keys dell'utente SFTP:
restrict,command="internal-sftp" ssh-ed25519 AAAA...

# Oppure con più opzioni:
restrict,command="internal-sftp",from="10.0.1.0/24" ssh-ed25519 AAAA...

# === QUOTA DISCO ===
# Usare quota del filesystem o directory separata con mount bind:
sudo mount -o bind /data/sftp/user1 /home/user1/upload
# Con quota sul filesystem /data/sftp:
sudo setquota -u user1 500M 600M 0 0 /data/sftp
# 500M soft limit, 600M hard limit

# === LOG SFTP ===
# Per logging dettagliato delle operazioni SFTP:
Subsystem sftp internal-sftp -l VERBOSE
# oppure:
Subsystem sftp internal-sftp -l INFO -f AUTH

# Log output (in /var/log/auth.log o journald):
# sshd: session opened for local user sftpuser
# internal-sftp: open "/upload/file.txt" flags WRITE,CREATE,TRUNCATE mode 0644
# internal-sftp: close "/upload/file.txt" bytes read 0 written 1234
```

### Trasferimenti Automatizzati

```bash
# === SFTP BATCH MODE ===
# File di comandi (/tmp/sftp-batch.txt):
# cd /upload
# put /local/data/*.csv
# bye

sftp -b /tmp/sftp-batch.txt sftpuser@server

# === CON CHIAVE SSH SENZA PASSPHRASE (automazione) ===
# Generare chiave dedicata senza passphrase:
ssh-keygen -t ed25519 -f ~/.ssh/id_sftp_auto -N "" -C "sftp-automation"

# In authorized_keys sul server (con restrizioni):
restrict,command="internal-sftp",from="10.0.1.50" ssh-ed25519 AAAA...key...

# Script di trasferimento automatico:
#!/bin/bash
REMOTE="sftpuser@sftp-server"
LOCAL_DIR="/data/export"
REMOTE_DIR="/upload"

sftp -i ~/.ssh/id_sftp_auto -b - "$REMOTE" <<EOF
cd $REMOTE_DIR
put ${LOCAL_DIR}/*.csv
bye
EOF

# === LFTP (client SFTP avanzato) ===
# lftp supporta mirror, retry, segmenting:
lftp -u sftpuser, sftp://server <<EOF
set sftp:connect-program "ssh -i ~/.ssh/id_sftp_auto"
mirror -R /local/dir /remote/dir
bye
EOF

# === CRON JOB per trasferimento periodico ===
# /etc/cron.d/sftp-export:
# 0 2 * * * automation /usr/local/bin/sftp-transfer.sh >> /var/log/sftp-transfer.log 2>&1
```

---

## SCP vs rsync vs SFTP — Confronto

```
┌──────────────┬─────────────────┬──────────────────┬──────────────────────┐
│ Caratterist. │ SCP             │ SFTP             │ rsync                │
├──────────────┼─────────────────┼──────────────────┼──────────────────────┤
│ Protocollo   │ SSH (deprecato) │ SSH (subsystem)  │ SSH (rsync protocol) │
├──────────────┼─────────────────┼──────────────────┼──────────────────────┤
│ Ripresa      │ No              │ Sì (get -a)      │ Sì (--partial)       │
│ trasferimento│                 │                  │                      │
├──────────────┼─────────────────┼──────────────────┼──────────────────────┤
│ Delta/increm.│ No (copia tutto)│ No (copia tutto) │ Sì (solo differenze) │
├──────────────┼─────────────────┼──────────────────┼──────────────────────┤
│ Compressione │ Sì (-C)         │ Sì (-C)          │ Sì (-z)              │
├──────────────┼─────────────────┼──────────────────┼──────────────────────┤
│ Interattivo  │ No              │ Sì (ls, cd, etc) │ No                   │
├──────────────┼─────────────────┼──────────────────┼──────────────────────┤
│ Chroot       │ No              │ Sì (internal-sftp)│ No (senza rsh)       │
├──────────────┼─────────────────┼──────────────────┼──────────────────────┤
│ Preserva     │ Sì (-p)         │ Sì               │ Sì (-a)              │
│ permessi     │                 │                  │                      │
├──────────────┼─────────────────┼──────────────────┼──────────────────────┤
│ Bandwidth    │ No              │ No               │ Sì (--bwlimit)       │
│ limit        │                 │                  │                      │
├──────────────┼─────────────────┼──────────────────┼──────────────────────┤
│ Delete remoto│ No              │ Manuale (rm)     │ Sì (--delete)        │
├──────────────┼─────────────────┼──────────────────┼──────────────────────┤
│ Stato        │ DEPRECATO       │ Attivo           │ Attivo               │
│              │ (OpenSSH 9.0+)  │                  │                      │
├──────────────┼─────────────────┼──────────────────┼──────────────────────┤
│ Quando usare │ MAI per nuovi   │ Accesso ristretto│ Backup, sync, file   │
│              │ setup. Solo     │ chroot. Upload/  │ grandi. Trasferimento│
│              │ legacy.         │ download batch.  │ incrementale.        │
│              │                 │ Utenti non-shell.│ Mirror di directory. │
└──────────────┴─────────────────┴──────────────────┴──────────────────────┘
```

**Raccomandazione:** usare `rsync` per trasferimenti tra server/workstation. Usare `sftp` per utenti limitati e ambienti chroot. Evitare `scp` su nuovi setup (deprecato dal protocollo SCP; le versioni recenti di OpenSSH usano internamente SFTP per `scp`).

---

## SCP, SFTP, rsync over SSH

### SCP (Secure Copy)

```bash
# NOTA: SCP è considerato deprecato (OpenSSH 9.0+ usa SFTP internamente per scp).
# Usare rsync o sftp per nuove implementazioni.

# Copia locale → remoto
scp file.txt user@server:/tmp/
scp -r directory/ user@server:/tmp/   # Ricorsivo
scp -P 2222 file.txt user@server:/tmp/  # Porta specifica

# Copia remoto → locale
scp user@server:/var/log/syslog ./

# Tra due server remoti (via la macchina locale)
scp user@server1:/file user@server2:/file

# Con alias SSH config
scp file.txt prod:/tmp/
```

### SFTP

```bash
sftp user@server
# Comandi interattivi:
# ls, cd, pwd         → navigazione remota
# lls, lcd, lpwd      → navigazione locale
# get file            → download
# put file            → upload
# mget *.log          → download multipli
# mput *.txt          → upload multipli
# mkdir, rmdir, rm    → gestione file remoti
# exit / bye          → esci

# Batch mode
sftp -b commands.txt user@server
```

### rsync over SSH

```bash
# Sincronizza locale → remoto
rsync -avz directory/ user@server:/backup/directory/
# -a = archive (ricorsivo, permessi, date, link, etc.)
# -v = verbose
# -z = compressione durante trasferimento

# Remoto → locale
rsync -avz user@server:/data/ ./data/

# Con porta specifica
rsync -avz -e "ssh -p 2222" directory/ user@server:/backup/

# Dry run (simula senza copiare)
rsync -avzn directory/ user@server:/backup/directory/

# Cancella file remoti non presenti localmente (mirror)
rsync -avz --delete directory/ user@server:/backup/directory/

# Esclusioni
rsync -avz --exclude='*.log' --exclude='.git' directory/ user@server:/backup/

# Con progress e bandwidth limit
rsync -avz --progress --bwlimit=5000 directory/ user@server:/backup/
# --bwlimit in KB/s

# Con alias SSH config
rsync -avz directory/ prod:/backup/

# Ripresa trasferimento interrotto
rsync -avz --partial --progress large-file.iso user@server:/data/
# --partial = mantieni file parziale (non cancellare se interrotto)

# Con checksum (più lento ma preciso)
rsync -avzc directory/ user@server:/backup/
# -c = usa checksum invece di timestamp/size per determinare i cambiamenti

# Backup incrementale con hardlink (snapshot)
rsync -avz --delete --link-dest=/backup/prev directory/ user@server:/backup/current/
# --link-dest = crea hardlink ai file invariati dalla directory di riferimento
```

---

## Multiplexing SSH

Il multiplexing riutilizza una connessione TCP/SSH esistente per sessioni successive. Elimina handshake, key exchange e autenticazione per le connessioni successive.

```bash
# === CONFIGURAZIONE ===
# ~/.ssh/config
Host *
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%r@%h-%p
    ControlPersist 600              # Mantieni la connessione 10 minuti

# Creare la directory per i socket
mkdir -p ~/.ssh/sockets
chmod 700 ~/.ssh/sockets

# === BENCHMARK ===
# Prima connessione (crea il master):
time ssh server "echo OK"
# real 0m0.850s (handshake + auth + exec)

# Seconda connessione (riusa master):
time ssh server "echo OK"
# real 0m0.050s (solo apertura canale)

# Speedup tipico: 10-20x per connessioni frequenti

# === GESTIRE CONNESSIONI MASTER ===
ssh -O check server                 # Verifica se master è attivo
# Output: Master running (pid=12345)

ssh -O stop server                  # Chiudi il master con grazia
ssh -O exit server                  # Termina il master immediatamente

# Aggiungere forwarding a connessione master esistente
ssh -O forward -L 8080:localhost:80 server
ssh -O forward -R 9090:localhost:3000 server

# Rimuovere forwarding
ssh -O cancel -L 8080:localhost:80 server

# === TROUBLESHOOTING ===
# Socket stale (processo master morto):
ssh -O check server
# Output: Control socket "..." does not exist

# Rimuovere socket stale manualmente:
rm ~/.ssh/sockets/user@server-22

# Disabilitare multiplexing per una singola connessione:
ssh -o ControlMaster=no server
# Oppure:
ssh -S none server

# === ATTENZIONE ===
# Il multiplexing NON funziona con:
# - GitHub/GitLab (chiudono la connessione dopo ogni operazione)
# - Server con timeout aggressivi
# - Connessioni che cambiano identità (sudo su -)

# Disabilitare per git hosting:
Host github.com gitlab.com
    ControlMaster no
```

---

## SSH e PAM — Integrazione e 2FA

### PAM e SSH

PAM (Pluggable Authentication Modules) è il framework di autenticazione di Linux. SSH lo usa per estendere l'autenticazione oltre le chiavi SSH.

```bash
# === COME SSH USA PAM ===
# /etc/ssh/sshd_config:
UsePAM yes
# Abilita PAM per:
# - account: verifica account (scadenza, blocco, orari)
# - session: setup sessione (limiti, umask, motd)
# - auth: autenticazione (2FA, LDAP, ecc.)

# Stack PAM per SSH:
# /etc/pam.d/sshd

# === FLUSSO AUTENTICAZIONE CON PAM ===
# 1. sshd verifica publickey
# 2. Se AuthenticationMethods include keyboard-interactive:
#    sshd invoca PAM auth stack
# 3. PAM esegue i moduli configurati (TOTP, LDAP, ecc.)
# 4. PAM esegue moduli account (verifica account valido)
# 5. PAM esegue moduli session (setup ambiente)
```

### Google Authenticator (TOTP)

Configurare 2FA con Google Authenticator (TOTP — Time-based One-Time Password, RFC 6238).

```bash
# === INSTALLAZIONE ===
sudo apt install libpam-google-authenticator    # Debian/Ubuntu
sudo dnf install google-authenticator           # Fedora/RHEL

# === SETUP PER UTENTE ===
# Ogni utente esegue:
google-authenticator
# Rispondere alle domande:
# - Time-based tokens? → y
# - Update .google_authenticator? → y
# - Disallow reuse? → y
# - Increase window? → n (default 30 sec è OK)
# - Rate limiting? → y (3 tentativi ogni 30 sec)

# Scannerizzare il QR code con l'app Google Authenticator / Authy / etc.
# SALVARE i codici di emergenza (recovery codes)!

# === CONFIGURAZIONE PAM ===
# /etc/pam.d/sshd — aggiungere DOPO @include common-auth:
auth required pam_google_authenticator.so nullok
# nullok = utenti senza configurazione possono ancora entrare
# Rimuovere nullok quando tutti gli utenti hanno configurato 2FA

# Opzioni pam_google_authenticator.so:
# nullok              = Permetti login anche senza .google_authenticator
# secret=/path/file   = Percorso alternativo per il file segreto
# no_increment_hotp   = Non incrementare contatore HOTP dopo fallimento
# echo_verification_code = Mostra il codice durante l'inserimento (debug)

# === CONFIGURAZIONE SSHD ===
# /etc/ssh/sshd_config:
ChallengeResponseAuthentication yes   # Abilita keyboard-interactive
# Su OpenSSH 9.0+:
KbdInteractiveAuthentication yes
UsePAM yes

# Per richiedere chiave SSH + TOTP:
AuthenticationMethods publickey,keyboard-interactive

# Solo TOTP (senza chiave SSH):
# AuthenticationMethods keyboard-interactive

# === RESTART ===
sudo systemctl restart sshd

# === TEST ===
# Da un ALTRO terminale (non chiudere la sessione corrente!):
ssh user@server
# 1. Verifica chiave SSH
# 2. Chiede: "Verification code: " → inserire il codice TOTP

# === RECOVERY ===
# Se si perde il dispositivo 2FA:
# 1. Usare i codici di emergenza (salvati durante il setup)
# 2. Accesso fisico/console: rimuovere ~/.google_authenticator
# 3. Rieseguire google-authenticator per rigenerare
```

### Duo Security

```bash
# Duo è una soluzione 2FA enterprise con push notifications.

# === INSTALLAZIONE ===
# Scaricare duo_unix dal sito ufficiale Duo:
# https://duo.com/docs/duounix
sudo apt install duo-unix              # Dalla repo Duo
# oppure compilare da sorgente:
# ./configure --with-pam --prefix=/usr
# make && sudo make install

# === CONFIGURAZIONE ===
# /etc/duo/pam_duo.conf:
# [duo]
# ikey = DIXXXXXXXXXXXXXXXXXX
# skey = xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# host = api-XXXXXXXX.duosecurity.com
# pushinfo = yes
# autopush = yes
# failmode = safe
# # failmode = safe → Se Duo non raggiungibile, consenti accesso
# # failmode = secure → Se Duo non raggiungibile, NEGA accesso

# Permessi:
# sudo chmod 600 /etc/duo/pam_duo.conf

# === PAM ===
# /etc/pam.d/sshd:
auth required pam_duo.so

# === SSHD ===
# /etc/ssh/sshd_config:
AuthenticationMethods publickey,keyboard-interactive
UsePAM yes

# L'utente riceve una push notification sul telefono dopo la verifica della chiave SSH.
```

### Autenticazione LDAP

```bash
# Integrare SSH con un directory LDAP (Active Directory, OpenLDAP, FreeIPA).

# === METODO 1: SSSD (consigliato) ===
sudo apt install sssd sssd-ldap       # Debian/Ubuntu
sudo dnf install sssd sssd-ldap       # Fedora/RHEL

# /etc/sssd/sssd.conf:
# [sssd]
# services = nss, pam, ssh
# domains = LDAP
#
# [domain/LDAP]
# id_provider = ldap
# auth_provider = ldap
# ldap_uri = ldaps://ldap.example.com
# ldap_search_base = dc=example,dc=com
# ldap_user_ssh_public_key = sshPublicKey
# # ↑ Attributo LDAP che contiene la chiave pubblica SSH
#
# [ssh]
# ssh_hash_known_hosts = true

# /etc/ssh/sshd_config:
AuthorizedKeysCommand /usr/bin/sss_ssh_authorizedkeys
AuthorizedKeysCommandUser nobody
# Questo recupera le chiavi SSH dall'LDAP automaticamente

# Permessi:
# sudo chmod 600 /etc/sssd/sssd.conf
# sudo systemctl restart sssd sshd

# === METODO 2: AuthorizedKeysCommand custom ===
# Script che interroga LDAP per le chiavi:
# /usr/local/bin/ldap-ssh-keys.sh:
#!/bin/bash
# USER=$1
# ldapsearch -x -H ldaps://ldap.example.com \
#     -b "dc=example,dc=com" \
#     "(uid=$USER)" sshPublicKey \
#     | grep "sshPublicKey:" | sed 's/sshPublicKey: //'

# /etc/ssh/sshd_config:
# AuthorizedKeysCommand /usr/local/bin/ldap-ssh-keys.sh
# AuthorizedKeysCommandUser nobody
```

---

## fail2ban per SSH — Configurazione Avanzata

### Installazione e Jail Base

```bash
# === INSTALLAZIONE ===
sudo apt install fail2ban              # Debian/Ubuntu
sudo dnf install fail2ban              # Fedora/RHEL

# === CONFIGURAZIONE ===
# NON modificare /etc/fail2ban/jail.conf (sovrascritto dagli aggiornamenti)
# Creare /etc/fail2ban/jail.local:

# /etc/fail2ban/jail.local
[DEFAULT]
# Ban IP dopo 5 tentativi falliti in 10 minuti
maxretry = 5
findtime = 600
bantime = 3600                        # 1 ora di ban
# bantime = -1                        # Ban permanente (NON consigliato senza whitelist)

# Ignorare IP fidati
ignoreip = 127.0.0.1/8 ::1 10.0.1.0/24

# Backend per monitorare i log
backend = systemd                     # Per sistemi con journald
# backend = auto                      # Autodetect (fallback a file)

# Email di notifica
# destemail = admin@example.com
# sender = fail2ban@example.com
# action = %(action_mwl)s             # Ban + email con log

[sshd]
enabled = true
port = ssh                            # Porta (o numero specifico: 2222)
filter = sshd
logpath = %(sshd_log)s                # Auto-detect (auth.log o journald)
maxretry = 3                          # Override del default per SSH
bantime = 3600                        # 1 ora
findtime = 600                        # Finestra di 10 minuti
```

```bash
# === COMANDI OPERATIVI ===
sudo systemctl enable --now fail2ban
sudo fail2ban-client status           # Stato generale
sudo fail2ban-client status sshd      # Stato jail SSH
# Output:
# |- Filter
# |  |- Currently failed: 2
# |  |- Total failed:     45
# |  `- File list: /var/log/auth.log
# `- Actions
#    |- Currently banned: 3
#    |- Total banned:     12
#    `- Banned IP list: 1.2.3.4 5.6.7.8 9.10.11.12

# Sbloccare un IP
sudo fail2ban-client set sshd unbanip 1.2.3.4

# Bloccare manualmente un IP
sudo fail2ban-client set sshd banip 1.2.3.4

# Verificare che un IP specifico sia bannato
sudo fail2ban-client get sshd banned 1.2.3.4

# Ricaricare configurazione
sudo fail2ban-client reload
```

### Jail Personalizzate

```bash
# === JAIL PER ATTACCHI LENTI (low and slow) ===
# Rileva tentativi distribuiti nel tempo
[sshd-slow]
enabled = true
port = ssh
filter = sshd
logpath = %(sshd_log)s
maxretry = 10                         # Più tentativi permessi...
findtime = 86400                      # ...ma su 24 ore
bantime = 604800                      # Ban per 1 settimana

# === JAIL PER SCANSIONI AGGRESSIVE ===
[sshd-aggressive]
enabled = true
port = ssh
filter = sshd[mode=aggressive]        # Filtro aggressivo (includi più pattern)
logpath = %(sshd_log)s
maxretry = 1                          # Un solo tentativo con username inesistente
findtime = 600
bantime = 86400                       # Ban 24 ore

# === JAIL PER CONNESSIONI SENZA AUTH ===
[sshd-ddos]
enabled = true
port = ssh
filter = sshd[mode=ddos]
logpath = %(sshd_log)s
maxretry = 3                          # 3 connessioni senza autenticazione
findtime = 60                         # In 1 minuto
bantime = 3600                        # Ban 1 ora
```

### Rate Limiting Avanzato

```bash
# === BAN PROGRESSIVO (recidivi) ===
# Aumentare il ban per IP che tornano

# /etc/fail2ban/jail.local:
[recidive]
enabled = true
filter = recidive
logpath = /var/log/fail2ban.log        # Monitora il log di fail2ban stesso
maxretry = 3                          # Se un IP viene bannato 3 volte...
findtime = 86400                      # ...in 24 ore...
bantime = 604800                      # ...ban per 1 settimana
# bantime = -1                        # ...ban permanente (con whitelist)

# === BAN ESPONENZIALE (personalizzato) ===
# Richiede fail2ban 0.11+
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = %(sshd_log)s
maxretry = 3
findtime = 600
bantime = 600                         # Ban iniziale: 10 minuti
bantime.increment = true              # Abilita incremento
bantime.factor = 2                    # Moltiplica x2 ogni volta
bantime.maxtime = 604800              # Max 1 settimana
bantime.formula = ban.Time * math.exp(float(ban.Count+1)*banFactor)/math.exp(1*banFactor)
# 1° ban: 10 min, 2° ban: 20 min, 3° ban: 40 min, ...fino a 1 settimana

# === RATE LIMITING SSH CON IPTABLES (alternativa) ===
# Senza fail2ban, rate limiting diretto con iptables:
sudo iptables -A INPUT -p tcp --dport 22 -m state --state NEW -m recent --set --name SSH
sudo iptables -A INPUT -p tcp --dport 22 -m state --state NEW -m recent \
    --update --seconds 60 --hitcount 4 --name SSH -j DROP
# Max 4 nuove connessioni SSH al minuto per IP.

# Con nftables:
# nft add rule inet filter input tcp dport 22 ct state new \
#     meter ssh-rate { ip saddr limit rate 3/minute } accept
# nft add rule inet filter input tcp dport 22 ct state new drop
```

### Azioni Personalizzate

```bash
# === AZIONE: BAN + NOTIFICA ===
# /etc/fail2ban/action.d/notify-admin.local:
# [Definition]
# actionban = iptables -I f2b-<name> 1 -s <ip> -j DROP
#             curl -s -X POST https://hooks.slack.com/services/XXX \
#             -d '{"text":"🚨 fail2ban: IP <ip> bannato su <name>"}'
# actionunban = iptables -D f2b-<name> -s <ip> -j DROP

# Riferire nella jail:
# [sshd]
# action = notify-admin

# === AZIONE: REPORT A ABUSEIPDB ===
# Segnalare automaticamente IP abusivi:
# action = %(action_)s
#          abuseipdb[abuseipdb_apikey="xxx", abuseipdb_category="18,22"]

# === CLOUDFLARE FIREWALL ===
# Bloccare tramite Cloudflare API:
# action = cloudflare[cfuser="email", cftoken="apikey"]
```

---

## Port Knocking e Single Packet Authorization

### Port Knocking Classico

Il port knocking nasconde la porta SSH dietro una sequenza di "bussate" su porte specifiche. Finché la sequenza non viene completata, la porta SSH è chiusa.

```bash
# === INSTALLAZIONE ===
sudo apt install knockd               # Debian/Ubuntu

# === CONFIGURAZIONE SERVER ===
# /etc/knockd.conf:
[options]
    UseSyslog
    Interface = eth0

[openSSH]
    sequence    = 7000,8000,9000      # Sequenza segreta
    seq_timeout = 5                    # 5 secondi per completare la sequenza
    command     = /sbin/iptables -I INPUT -s %IP% -p tcp --dport 22 -j ACCEPT
    tcpflags    = syn

[closeSSH]
    sequence    = 9000,8000,7000      # Sequenza inversa per chiudere
    seq_timeout = 5
    command     = /sbin/iptables -D INPUT -s %IP% -p tcp --dport 22 -j ACCEPT
    tcpflags    = syn

# Chiusura automatica dopo timeout:
[openSSH]
    sequence    = 7000,8000,9000
    seq_timeout = 5
    command     = /sbin/iptables -I INPUT -s %IP% -p tcp --dport 22 -j ACCEPT
    tcpflags    = syn
    cmd_timeout = 30                   # Chiudi automaticamente dopo 30 secondi
    stop_command = /sbin/iptables -D INPUT -s %IP% -p tcp --dport 22 -j ACCEPT

# Abilitare e avviare:
sudo systemctl enable --now knockd

# === PREREQUISITO: BLOCCARE SSH DI DEFAULT ===
sudo iptables -A INPUT -p tcp --dport 22 -j DROP
# (Solo DOPO aver configurato knockd e testato!)

# === USO LATO CLIENT ===
# Con il client knock:
knock server.example.com 7000 8000 9000
ssh user@server.example.com
knock server.example.com 9000 8000 7000   # Chiudi dopo

# Con nmap (alternativa):
for port in 7000 8000 9000; do
    nmap -Pn --max-retries 0 -p $port server.example.com
done
ssh user@server.example.com

# === LIMITI DEL PORT KNOCKING ===
# 1. La sequenza può essere sniffata sulla rete (non crittografato)
# 2. Vulnerability a replay attack
# 3. NAT e firewall possono riordinare i pacchetti
# 4. Non autentica il mittente
# → Per questi motivi, preferire fwknop (SPA) al port knocking classico.
```

### fwknop — Single Packet Authorization

fwknop (FireWall KNock OPerator) è l'evoluzione sicura del port knocking. Usa un singolo pacchetto crittografato e autenticato per aprire la porta SSH.

```bash
# === VANTAGGI RISPETTO AL PORT KNOCKING ===
# 1. Singolo pacchetto (non sequenza) — resiste a firewall/NAT
# 2. Crittografato — non sniffabile
# 3. Autenticato — nonce e timestamp prevengono replay
# 4. Non lascia porte aperte continuamente

# === INSTALLAZIONE ===
sudo apt install fwknop-server fwknop-client    # Debian/Ubuntu
sudo dnf install fwknop                          # Fedora/RHEL

# === CONFIGURAZIONE SERVER ===
# /etc/fwknop/fwknopd.conf:
# PCAP_INTF                 eth0;
# ENABLE_IPT_FORWARDING     N;
# ENABLE_IPT_LOCAL_NAT      N;
# ENABLE_IPT_OUTPUT         N;

# /etc/fwknop/access.conf:
# SOURCE         ANY
# KEY_BASE64     <chiave generata con fwknop --key-gen>
# HMAC_KEY_BASE64 <hmac key generata con fwknop --key-gen>
# OPEN_PORTS     tcp/22
# FW_ACCESS_TIMEOUT 30             # Porta aperta per 30 secondi

# Generare le chiavi:
fwknop --key-gen
# Output:
# KEY_BASE64: xxxx...
# HMAC_KEY_BASE64: yyyy...

# Avviare:
sudo systemctl enable --now fwknop-server

# === USO LATO CLIENT ===
# Configurare il client (~/.fwknoprc):
# [server]
# SPA_SERVER         server.example.com
# ACCESS             tcp/22
# KEY_BASE64         xxxx...         # Stessa chiave del server
# HMAC_KEY_BASE64    yyyy...         # Stessa HMAC key
# USE_HMAC           Y

# Inviare il pacchetto SPA:
fwknop -n server
# La porta 22 si apre per 30 secondi per il TUO IP

# Connettersi immediatamente:
ssh user@server.example.com

# Combinare in un comando:
fwknop -n server && ssh user@server.example.com

# === CON CHIAVE GPG (alternativa) ===
# fwknop supporta anche crittografia asimmetrica con GPG
# per ambienti che richiedono chiavi asimmetriche.
```

---

## SSH con Fabric e Paramiko (Python)

Fabric e Paramiko sono le librerie Python di riferimento per l'automazione SSH. Paramiko implementa il protocollo SSH2 a basso livello; Fabric lo wrappa con un'API ad alto livello orientata al deployment e all'esecuzione remota di comandi.

### Paramiko — Accesso programmatico SSH

```python
import paramiko

# === CONNESSIONE CON CHIAVE ===
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.RejectPolicy())  # MAI AutoAddPolicy in produzione
client.load_system_host_keys()

client.connect(
    hostname="10.0.1.100",
    username="admin",
    key_filename="/home/user/.ssh/id_ed25519",
    timeout=10,
    banner_timeout=15,
)

# Eseguire un comando
stdin, stdout, stderr = client.exec_command("df -h", timeout=30)
exit_code = stdout.channel.recv_exit_status()
output = stdout.read().decode("utf-8")
errors = stderr.read().decode("utf-8")

if exit_code != 0:
    raise RuntimeError(f"Comando fallito (exit {exit_code}): {errors}")
print(output)

client.close()
```

```python
# === SFTP CON PARAMIKO ===
transport = paramiko.Transport(("10.0.1.100", 22))
transport.connect(username="admin", pkey=paramiko.Ed25519Key.from_private_key_file("/home/user/.ssh/id_ed25519"))

sftp = paramiko.SFTPClient.from_transport(transport)

# Upload con progress callback
def progress(transferred, total):
    pct = transferred / total * 100
    print(f"\r  {pct:.1f}%", end="", flush=True)

sftp.put("/local/backup.tar.gz", "/remote/backup.tar.gz", callback=progress)

# Download
sftp.get("/remote/config.yaml", "/local/config.yaml")

# Elencare file remoti
for entry in sftp.listdir_attr("/var/log"):
    print(f"  {entry.filename:40s} {entry.st_size:>12d} bytes")

sftp.close()
transport.close()
```

### Fabric — Automazione deployment

```python
# fabfile.py
from fabric import Connection, task
from invoke import Responder

@task
def deploy(ctx, branch="main"):
    """Deploy dell'applicazione su un server remoto."""
    c = Connection(
        host="web1.example.com",
        user="deploy",
        connect_kwargs={"key_filename": "/home/user/.ssh/id_deploy"},
    )
    
    with c.cd("/opt/app"):
        # Pull del codice
        result = c.run(f"git fetch origin && git checkout {branch} && git pull", warn=True)
        if result.failed:
            print(f"Git pull fallito: {result.stderr}")
            return
        
        # Installare dipendenze
        c.run("pip install -r requirements.txt --quiet")
        
        # Migrazioni database
        c.run("alembic upgrade head")
        
        # Restart servizio
        c.sudo("systemctl restart myapp", pty=True)
        
        # Health check
        result = c.run("curl -sf http://localhost:8000/health", warn=True)
        if result.failed:
            print("HEALTH CHECK FALLITO — rollback necessario")
            c.run(f"git checkout HEAD~1")
            c.sudo("systemctl restart myapp", pty=True)
        else:
            print("Deploy completato con successo")

# Uso: fab deploy --branch=release/v2.1
```

```python
# === FABRIC CON BASTION / JUMP HOST ===
from fabric import Connection

bastion = Connection("bastion.example.com", user="admin")
target = Connection(
    "10.0.2.50",
    user="deploy",
    gateway=bastion,  # Usa il bastion come gateway SSH
    connect_kwargs={"key_filename": "/home/user/.ssh/id_internal"},
)

result = target.run("hostname && uptime")
print(result.stdout)
```

**Differenze chiave tra expect/sshpass e Paramiko/Fabric**: Paramiko/Fabric usano chiavi SSH (mai password), gestiscono il protocollo a livello nativo Python, supportano error handling robusto con exception, sono testabili e manutenibili come qualsiasi codice Python. expect e sshpass sono tool di emergenza per sistemi legacy dove non è possibile configurare l'autenticazione con chiave.

### Terraform SSH Provisioner

Terraform può usare SSH come meccanismo di provisioning per eseguire comandi e copiare file sui server appena creati. Il provisioner SSH è utile per il bootstrap iniziale — installare software, configurare il sistema, preparare il server per la gestione con Ansible o altri strumenti di configuration management.

```hcl
# Provisioner SSH in Terraform
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
  key_name      = aws_key_pair.deploy.key_name

  connection {
    type        = "ssh"
    user        = "ubuntu"
    private_key = file("~/.ssh/id_deploy")
    host        = self.public_ip
    timeout     = "5m"
  }

  # Copiare file di configurazione
  provisioner "file" {
    source      = "configs/nginx.conf"
    destination = "/tmp/nginx.conf"
  }

  # Eseguire comandi di setup
  provisioner "remote-exec" {
    inline = [
      "sudo apt-get update -qq",
      "sudo apt-get install -y nginx",
      "sudo mv /tmp/nginx.conf /etc/nginx/nginx.conf",
      "sudo systemctl enable --now nginx",
    ]
  }

  # Provisioner con bastion/jump host
  # connection {
  #   type         = "ssh"
  #   user         = "ubuntu"
  #   private_key  = file("~/.ssh/id_internal")
  #   host         = self.private_ip
  #   bastion_host = aws_instance.bastion.public_ip
  #   bastion_user = "admin"
  #   bastion_private_key = file("~/.ssh/id_bastion")
  # }
}
```

**Limitazioni del provisioner SSH**: è eseguito solo alla creazione o distruzione della risorsa — non per aggiornamenti successivi. Per la gestione continua della configurazione, usare Ansible, Puppet o Chef. Il provisioner è un tool di bootstrap, non di configuration management.

---

## SSH Automation

### expect

`expect` è un framework per automatizzare interazioni con programmi che richiedono input interattivo (come SSH con password).

```bash
# === INSTALLAZIONE ===
sudo apt install expect                # Debian/Ubuntu

# === SCRIPT EXPECT PER SSH ===
#!/usr/bin/expect -f
# ssh-auto.exp — Login automatico SSH (solo per test/legacy)

set timeout 30
set host [lindex $argv 0]
set user [lindex $argv 1]
set pass [lindex $argv 2]

spawn ssh $user@$host
expect {
    "yes/no" {
        send "yes\r"
        exp_continue
    }
    "password:" {
        send "$pass\r"
    }
    timeout {
        puts "Timeout raggiunto"
        exit 1
    }
}
expect "$ "
send "uptime\r"
expect "$ "
send "exit\r"
expect eof

# Uso: ./ssh-auto.exp server.example.com admin "password123"

# === RISCHI DI expect ===
# 1. La password è visibile nello script (o in argv → /proc/<pid>/cmdline)
# 2. Fragile: dipende dai prompt esatti del server
# 3. Non scalabile
# → Usare chiavi SSH per l'automazione. expect è solo per sistemi legacy
#   dove non si possono configurare chiavi.
```

### sshpass (e i suoi rischi)

```bash
# sshpass fornisce password a SSH in modo non interattivo.
# ATTENZIONE: la password è esposta in chiaro.

# === INSTALLAZIONE ===
sudo apt install sshpass               # Debian/Ubuntu

# === USO ===
# Via argomento (password visibile in ps/top!):
sshpass -p 'password123' ssh user@server

# Via file (leggermente meglio):
echo 'password123' > /tmp/sshpass.txt
chmod 600 /tmp/sshpass.txt
sshpass -f /tmp/sshpass.txt ssh user@server

# Via variabile d'ambiente:
export SSHPASS='password123'
sshpass -e ssh user@server

# === RISCHI ===
# 1. -p: password visibile a TUTTI gli utenti del sistema (ps aux, /proc/*/cmdline)
# 2. -f: il file può essere letto se i permessi non sono corretti
# 3. -e: la variabile d'ambiente è visibile in /proc/*/environ
# 4. Nessuno di questi metodi è sicuro per produzione
# 5. Viola la politica di sicurezza in qualsiasi organizzazione seria

# === QUANDO È ACCETTABILE ===
# - Script di test/CI in ambienti isolati
# - Migrazione di massa verso chiavi SSH (transizione)
# - Sistemi embedded legacy senza supporto chiavi
# SEMPRE preferire chiavi SSH per l'automazione.
```

### Ansible SSH Transport

```bash
# Ansible usa SSH come transport layer per comunicare con i nodi gestiti.
# Non richiede agent sui nodi (agentless).

# === CONFIGURAZIONE SSH PER ANSIBLE ===
# ~/.ssh/config (ottimizzato per Ansible):
Host *
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%C
    ControlPersist 600
    ServerAliveInterval 60
    ServerAliveCountMax 3
    Compression yes

# === ANSIBLE.CFG ===
# ansible.cfg:
[ssh_connection]
ssh_args = -o ControlMaster=auto -o ControlPersist=600 -o ControlPath=~/.ssh/sockets/%C
pipelining = True                     # Riduce il numero di connessioni SSH
# pipelining richiede: requiretty disabilitato in /etc/sudoers (o tramite Ansible)

# === INVENTORY CON PARAMETRI SSH ===
# inventory.yml:
# all:
#   hosts:
#     web1:
#       ansible_host: 10.0.1.100
#       ansible_user: admin
#       ansible_ssh_private_key_file: ~/.ssh/id_prod
#       ansible_port: 22
#     web2:
#       ansible_host: 10.0.1.101
#       ansible_user: admin
#       ansible_ssh_private_key_file: ~/.ssh/id_prod
#   vars:
#     ansible_ssh_common_args: '-o ProxyJump=bastion'

# === JUMP HOST CON ANSIBLE ===
# ansible.cfg:
# [ssh_connection]
# ssh_args = -o ProxyJump=bastion

# Oppure per host specifici:
# web_servers:
#   vars:
#     ansible_ssh_common_args: '-J jumpuser@bastion.example.com'

# === TIPS PERFORMANCE ===
# 1. Abilitare pipelining (riduce connessioni SSH del 50%+)
# 2. Usare ControlMaster (riusa connessioni)
# 3. Aumentare forks (parallelismo): ansible.cfg → forks = 20
# 4. Usare Mitogen (plugin SSH ottimizzato per Ansible):
#    pip install mitogen
#    ansible.cfg → strategy_plugins = /path/to/mitogen/ansible_mitogen/plugins/strategy
#    ansible.cfg → strategy = mitogen_linear
```

---

## Best Practices

1. **ED25519 > RSA**: usare chiavi ED25519 per nuove installazioni. Più veloci, più sicure, chiavi più corte. RSA 4096 solo per compatibilità con sistemi legacy che non supportano Ed25519 (OpenSSH < 6.5). La generazione è deterministica e non dipende dalla qualità del generatore di numeri casuali, a differenza di ECDSA che è vulnerabile a nonce deboli.

2. **Disabilitare password auth**: dopo aver configurato le chiavi, disabilitare `PasswordAuthentication no` nel sshd_config. Questo elimina il 99% degli attacchi brute force. Verificare PRIMA di disabilitare che l'autenticazione con chiave funzioni — connettersi in una seconda sessione prima di chiudere quella corrente. Errore comune: disabilitare le password, dimenticare di caricare la chiave pubblica, e restare bloccati fuori dal server.

3. **ProxyJump > Agent Forwarding**: ProxyJump (`-J`) è significativamente più sicuro dell'agent forwarding (`-A`). Con l'agent forwarding, un amministratore malintenzionato (o un attaccante) sul server intermedio può usare il socket dell'agent per autenticarsi verso altri server con le chiavi dell'utente. ProxyJump invece stabilisce un tunnel TCP attraverso il bastion — la chiave privata non lascia mai il client. L'agent forwarding è accettabile solo in ambienti completamente fidati e con `ssh-add -c` (conferma manuale per ogni uso della chiave).

4. **Multiplexing per efficienza**: abilitare ControlMaster per chi fa molte connessioni allo stesso server. La prima connessione stabilisce il canale crittografato; le successive lo riusano, risparmiando l'handshake TCP, il key exchange e l'autenticazione. Il risparmio è significativo: da ~1s per connessione a ~50ms. Configurare `ControlPersist 600` per mantenere il master socket per 10 minuti dopo la disconnessione dell'ultima sessione, e `ControlPath ~/.ssh/sockets/%C` con la directory creata manualmente (`mkdir -p ~/.ssh/sockets && chmod 700 ~/.ssh/sockets`).

5. **Passphrase sulle chiavi**: le chiavi private devono avere una passphrase. Senza passphrase, chiunque trovi il file (furto del laptop, backup non cifrato, esposizione accidentale su Git) ha accesso immediato a tutti i server. Con passphrase, il file è inutile senza la passphrase. Usare `ssh-agent` per evitare di digitarla ad ogni connessione: `ssh-add -t 3600` aggiunge la chiave con timeout di 1 ora. Su macOS, integrarsi con il Keychain: `ssh-add --apple-use-keychain`. Su Linux, integrare con `gnome-keyring` o `kwallet` per ambienti desktop.

6. **fail2ban**: installare su ogni server esposto a Internet. Un server SSH esposto riceve centinaia o migliaia di tentativi di brute force al giorno — anche con password auth disabilitato, il logging e il consumo di risorse sono significativi. fail2ban riduce il rumore e i costi computazionali bannando gli IP dopo pochi tentativi falliti. Configurare jail multiple per scenari diversi: attacchi veloci (3 tentativi in 10 min), attacchi lenti (10 tentativi in 24 ore), e recidivi (ban progressivo per IP che tornano). Integrare con `nftables` per performance migliori rispetto a `iptables` su set di IP bannati grandi.

7. **Audit regolare**: verificare periodicamente `authorized_keys` su tutti i server. Script di audit periodico:
```bash
# Elencare tutte le chiavi autorizzate su un server
for user_home in /home/*/; do
    user=$(basename "$user_home")
    auth_file="$user_home/.ssh/authorized_keys"
    if [ -f "$auth_file" ]; then
        echo "=== $user ==="
        while IFS= read -r line; do
            [[ "$line" =~ ^#|^$ ]] && continue
            fp=$(echo "$line" | ssh-keygen -lf - 2>/dev/null)
            echo "  $fp"
        done < "$auth_file"
    fi
done
```
Rimuovere chiavi di ex dipendenti/collaboratori immediatamente al momento dell'offboarding. Mantenere un inventario delle chiavi SSH con associazione chiave-persona-scopo.

8. **Certificati SSH per scale**: oltre 20 server/utenti, passare a certificati SSH. Invece di distribuire chiavi pubbliche su ogni server (`authorized_keys`), una CA (Certificate Authority) firma le chiavi degli utenti con un certificato che include: identità, data di scadenza, principals autorizzati, e estensioni (forwarding, PTY). Il server si fida della CA e accetta qualsiasi certificato da essa firmato. Vantaggi: onboarding immediato (firma la chiave, l'utente accede a tutti i server), offboarding istantaneo (Key Revocation List), scadenza automatica (certificati con validità limitata), e audit completo (ogni certificato ha un serial number tracciabile).

9. **2FA su bastion**: il bastion host è il punto di ingresso critico della rete — se compromesso, l'intera infrastruttura è esposta. Richiedere 2FA (chiave SSH + TOTP o push notification) aggiunge un secondo fattore che resiste al furto della chiave privata. Configurare con PAM + Google Authenticator o con chiavi hardware FIDO2 (`ed25519-sk`). L'autenticazione a due fattori deve essere obbligatoria anche per gli amministratori — anzi, soprattutto per gli amministratori.

10. **Principio del minimo privilegio**: ogni chiave SSH dovrebbe avere solo i permessi necessari. Usare `restrict` in `authorized_keys` (disabilita tutto: port forwarding, agent forwarding, X11, PTY, exec) e poi riabilitare selettivamente solo ciò che serve. Per chiavi di deploy automatico, usare `command="/usr/bin/git-shell"` o un wrapper specifico. Per chiavi di backup, `command="borg serve --restrict-to-path /backup"`. Esempio completo:
```
restrict,command="/usr/local/bin/backup-only.sh",from="10.0.1.0/24" ssh-ed25519 AAAA... backup-server
```

11. **Log centralizzati**: inviare i log SSH a un SIEM (Wazuh, ELK, Splunk). Un attaccante che compromette un server potrebbe alterare i log locali per cancellare le tracce. Log centralizzati in un sistema separato e protetto preservano l'evidenza. Monitorare e generare alert per: login falliti multipli dallo stesso IP, login riusciti da IP non previsti (geolocalizzazione anomala), login fuori orario lavorativo, uso di chiavi non censite nell'inventario, escalation di privilegi post-login.

12. **Rekey e rotazione**: SSH esegue automaticamente il rekey dopo una certa quantità di dati trasmessi, ma il default può essere troppo permissivo per connessioni long-lived. Configurare `RekeyLimit 512M 1h` per forzare il rinnovo delle chiavi di sessione ogni 512 MB o ogni ora, qualunque condizione si verifichi prima. Per le chiavi di identità (id_ed25519), stabilire una policy di rotazione: annuale per utenti normali, semestrale per amministratori, a ogni cambio di ruolo o sospetto di compromissione. Documentare la procedura di rotazione e testarla periodicamente.

13. **No root login diretto**: disabilitare con `PermitRootLogin no` nel sshd_config. Usare utenti nominali con sudo. L'accesso root diretto impedisce l'audit (tutti i login risultano come "root" — chi era?), non supporta 2FA in modo efficace, e un brute force riuscito dà immediatamente accesso completo. Con utenti nominali + sudo, ogni azione privilegiata è tracciabile, il sudo può essere limitato a comandi specifici, e l'account root può avere una password lunghissima nota solo per l'accesso fisico di emergenza.

14. **Cifratura forte**: rimuovere algoritmi deboli. Configurazione raccomandata per OpenSSH 9.x:
```
# /etc/ssh/sshd_config
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com
KexAlgorithms sntrup761x25519-sha512@openssh.com,curve25519-sha256,curve25519-sha256@libssh.org
HostKeyAlgorithms ssh-ed25519,rsa-sha2-512,rsa-sha2-256
```
Verificare la configurazione con `ssh-audit` prima e dopo la modifica. Non includere mai `diffie-hellman-group1-sha1`, `ssh-rsa` (SHA-1), `3des-cbc`, `arcfour`, o qualsiasi cifrario CBC. Per server che devono supportare client legacy, creare un `Match` block separato con cifrari più permissivi limitato agli IP di quei client.

15. **Moduli DH sicuri**: i moduli Diffie-Hellman predefiniti in `/etc/ssh/moduli` includono gruppi di dimensione inferiore a 2048 bit, vulnerabili ad attacchi come Logjam. Rimuovere tutti i moduli con meno di 3072 bit:
```bash
# Backup
cp /etc/ssh/moduli /etc/ssh/moduli.bak
# Rimuovere moduli deboli (< 3072 bit)
awk '$5 >= 3071' /etc/ssh/moduli > /etc/ssh/moduli.safe
mv /etc/ssh/moduli.safe /etc/ssh/moduli
# Generare nuovi moduli sicuri (operazione lunga, ~30 min)
ssh-keygen -M generate -O bits=3072 /etc/ssh/moduli.candidates
ssh-keygen -M screen -f /etc/ssh/moduli.candidates /etc/ssh/moduli
```

---

## Troubleshooting — 25 Problemi Comuni

**1. "Permission denied (publickey)"**
La chiave non è accettata. Verificare: (1) la chiave pubblica è in `~/.ssh/authorized_keys` sul server? (2) Permessi corretti? `chmod 700 ~/.ssh`, `chmod 600 ~/.ssh/authorized_keys`, (3) La home directory dell'utente non è world-writable, (4) `ssh -vvv` per debug dettagliato, (5) `IdentitiesOnly yes` ma chiave sbagliata nel config.

**2. "Host key verification failed"**
Il fingerprint del server è cambiato (server reinstallato, o attacco MITM). Se legittimo: `ssh-keygen -R hostname`. Se inaspettato: verificare con l'amministratore del server.

**3. "Connection refused"**
sshd non è in esecuzione (`systemctl status sshd`) o sta ascoltando su un'altra porta (`ss -tuln | grep ssh`), o il firewall blocca la porta.

**4. "Connection timed out"**
Il server non è raggiungibile (ping), firewall tra client e server (iptables, security group, rete aziendale), o il server è configurato per ascoltare su un indirizzo IP specifico diverso.

**5. "Broken pipe / Write failed"**
La connessione è caduta. Configurare keepalive: `ServerAliveInterval 60` e `ServerAliveCountMax 3` nel client config. Se il problema persiste: controllare firewall con timeout sessione, proxy, NAT con timeout basso.

**6. "Too many authentication failures"**
SSH ha provato troppe chiavi dall'agent prima di quella giusta. Soluzione: (1) `IdentitiesOnly yes` nel config, (2) specificare la chiave corretta con `IdentityFile`, (3) `ssh-add -D` e aggiungere solo le chiavi necessarie, (4) aumentare `MaxAuthTries` sul server (solo come workaround).

**7. "Agent admitted failure to sign using the key"**
L'ssh-agent non ha la chiave caricata. Soluzione: `ssh-add ~/.ssh/id_ed25519`. Verificare con `ssh-add -l`.

**8. "Bad owner or modes for ~/.ssh/config"**
Permessi errati sul file config. Soluzione: `chmod 600 ~/.ssh/config` e `chown $USER:$USER ~/.ssh/config`.

**9. "REMOTE HOST IDENTIFICATION HAS CHANGED!"**
Il fingerprint del server è cambiato. Se il server è stato reinstallato: `ssh-keygen -R hostname`. Se non ti aspettavi il cambio: potenziale attacco MITM. Verificare.

**10. "Could not resolve hostname"**
Il DNS non riesce a risolvere l'hostname. Verificare: (1) l'hostname è corretto, (2) il DNS funziona (`dig hostname`), (3) usare l'IP direttamente per testare.

**11. "channel 0: open failed: administratively prohibited"**
Il server ha disabilitato il tipo di canale richiesto. Per shell interattiva: verificare che l'utente abbia una shell valida (`/etc/passwd`). Per forwarding: verificare `AllowTcpForwarding yes` sul server.

**12. "bind: Address already in use"**
Un'altra connessione SSH (o un altro processo) sta già usando la porta locale per il forwarding. Soluzione: (1) trovare il processo: `ss -tuln | grep 8080`, (2) terminarlo o usare una porta diversa, (3) `ssh -O cancel` per rimuovere forwarding dalla connessione master.

**13. "Warning: Remote port forwarding failed"**
Il server non ha potuto aprire la porta remota. Cause: (1) la porta è già in uso sul server, (2) `GatewayPorts` non configurato (se si usa 0.0.0.0:), (3) permessi insufficienti per porte < 1024.

**14. "Received disconnect from host: Too many authentication failures"**
Lato server, `MaxAuthTries` raggiunto. Vedere punto 6.

**15. "Unable to negotiate a key exchange method"**
Client e server non hanno algoritmi in comune. Soluzione: (1) verificare `KexAlgorithms` su entrambi i lati, (2) su server vecchi, potrebbe essere necessario aggiungere algoritmi legacy al client: `ssh -o KexAlgorithms=+diffie-hellman-group14-sha1 user@old-server`.

**16. "no matching host key type found"**
Il server offre solo tipi di host key non accettati dal client. Soluzione: `ssh -o HostKeyAlgorithms=+ssh-rsa user@old-server` (solo per server legacy).

**17. "no matching cipher found"**
Nessun cifrario in comune. Soluzione: `ssh -o Ciphers=+aes128-ctr user@old-server` (solo per server legacy).

**18. "Tunnel device open failed: Operation not permitted"**
Il tunnel TUN/TAP richiede `PermitTunnel yes` sul server e privilegi root (o CAP_NET_ADMIN) sul client.

**19. "Control socket already exists"**
Un socket di multiplexing stale esiste nella directory dei socket. Soluzione: (1) `ssh -O check server` per verificare se il master è vivo, (2) se morto: `rm ~/.ssh/sockets/user@server-22`, (3) usare `ssh -S none server` per bypassare.

**20. "Pseudo-terminal will not be allocated because stdin is not a terminal"**
Si sta eseguendo un comando remoto che richiede un PTY ma stdin non è un terminale (es. pipe). Soluzione: `ssh -tt user@server "comando"` (doppio -t per forzare PTY).

**21. "key_load_public: No such file or directory"**
SSH cerca la chiave pubblica corrispondente alla privata ma non la trova. Non è un errore critico (warning), ma per eliminare il messaggio: `ssh-keygen -yf ~/.ssh/id_ed25519 > ~/.ssh/id_ed25519.pub`.

**22. "sign_and_send_pubkey: no mutual signature supported"**
Il server non accetta la firma SHA-1 per la chiave RSA (OpenSSH 8.8+ ha deprecato `ssh-rsa`). Soluzione: (1) usare ed25519 al posto di RSA, (2) aggiornare il server, (3) workaround temporaneo: `ssh -o PubkeyAcceptedAlgorithms=+ssh-rsa user@old-server`.

**23. Tunnel funziona ma è lento**
(1) Verificare se la compressione aiuta: `ssh -C`, (2) aumentare la window size TCP del server, (3) verificare la latenza del link con `ping`, (4) per trasferimenti, usare rsync con compressione, (5) verificare che il cifrario non sia troppo pesante per la CPU (chacha20 è buono su CPU moderne ma lento su CPU vecchie senza AES-NI — usare aes128-gcm in quel caso).

**24. SSH si blocca alla disconnessione (hang on exit)**
Di solito un processo in background mantiene aperta la connessione. Soluzione: (1) usare `ssh -o "LogLevel DEBUG3"` per vedere cosa blocca, (2) uscire con `~.` (escape character + punto), (3) verificare `AllowTcpForwarding` e forwarding attivi.

**25. Autenticazione 2FA non richiesta (TOTP ignorato)**
(1) Verificare `AuthenticationMethods publickey,keyboard-interactive` (con la virgola!), (2) verificare `UsePAM yes` e `ChallengeResponseAuthentication yes` (o `KbdInteractiveAuthentication yes`), (3) verificare `/etc/pam.d/sshd` contiene il modulo `pam_google_authenticator.so`, (4) verificare che l'utente abbia eseguito `google-authenticator`, (5) restart sshd dopo le modifiche.

---

## FAQ — Domande Frequenti

**Q1: È davvero necessario cambiare la porta SSH da 22 a un'altra?**
No. Cambiare la porta SSH ("security through obscurity") non offre protezione reale contro attacchi mirati. Uno scan di tutte le porte trova SSH in pochi secondi. Tuttavia riduce il rumore nei log dagli scanner automatici. Il consiglio: usare fail2ban + chiavi + 2FA piuttosto che cambiare porta.

**Q2: Come posso vedere quale chiave SSH è stata usata per un login?**
Con `LogLevel VERBOSE` in `sshd_config`, il log mostra il fingerprint della chiave usata: `grep "Accepted publickey" /var/log/auth.log` e `grep "Found matching" /var/log/auth.log`. Ogni riga contiene l'algoritmo e il fingerprint SHA256.

**Q3: Come funziona `StrictHostKeyChecking accept-new`?**
`accept-new` (OpenSSH 7.6+) accetta automaticamente le chiavi di host mai visti (nuovi), ma rifiuta connessioni dove la chiave è cambiata rispetto a quella memorizzata. È un buon compromesso tra sicurezza e usabilità.

**Q4: Posso usare la stessa chiave SSH per tutti i server?**
Tecnicamente sì, ma non è consigliato. Se la chiave viene compromessa, tutti i server sono esposti. Usare chiavi separate per: (1) ambienti diversi (prod/staging/dev), (2) ruoli diversi (admin/deploy/backup), (3) organizzazioni diverse.

**Q5: Come faccio SSH su un server dietro NAT senza VPN?**
Opzioni: (1) remote port forwarding: dal server NATtato verso un VPS pubblico, (2) servizi come ngrok/bore/cloudflared per tunnel inversi, (3) Tailscale/Zerotier per VPN mesh peer-to-peer, (4) fwknop per SPA se il server ha un IP pubblico ma firewall restrittivo.

**Q6: Come trasferire file tra due server remoti senza passare per il mio PC?**
(1) `rsync` direttamente tra i server: `ssh server1 "rsync -avz /data/ server2:/data/"` (richiede chiave o password su server1 per server2), (2) `scp -3 server1:/file server2:/file` (passa dal tuo PC, utile se i server non si vedono), (3) ProxyJump: `rsync -avz -e "ssh -J bastion" server1:/data/ server2:/data/`.

**Q7: SSH va in timeout dietro un firewall aziendale. Come risolvere?**
(1) `ServerAliveInterval 60` nel client config (keepalive SSH), (2) `TCPKeepAlive yes` (keepalive TCP), (3) usare SSH sulla porta 443 se il firewall blocca la 22 (molti firewall permettono 443), (4) usare `corkscrew` o `connect` per tunnel SSH via HTTP proxy.

**Q8: Come disabilitare l'accesso SSH per un utente senza eliminarlo?**
(1) `DenyUsers username` in sshd_config, (2) `usermod -s /usr/sbin/nologin username` (rimuove la shell), (3) `passwd -l username` (blocca la password, ma non le chiavi!), (4) rimuovere la chiave da `authorized_keys`, (5) bloccare con PAM: `pam_access.so`.

**Q9: È sicuro usare `ssh-copy-id` su una rete non fidata?**
`ssh-copy-id` usa SSH per copiare la chiave pubblica, quindi la connessione è crittografata. Il rischio è se non si verifica il fingerprint dell'host alla prima connessione (TOFU — Trust On First Use). Per massima sicurezza: ottenere il fingerprint del server via un canale sicuro prima della prima connessione.

**Q10: Come imposto un timeout per le sessioni SSH inattive?**
Lato server: `ClientAliveInterval 300` + `ClientAliveCountMax 2` in sshd_config (timeout dopo 10 minuti). Lato client: `ServerAliveInterval 60` + `ServerAliveCountMax 3` in ssh_config. Sono meccanismi complementari: il server disconnette gli inattivi, il client rileva connessioni morte.

**Q11: Qual è la differenza tra `ssh-keygen -R` e la modifica manuale di known_hosts?**
`ssh-keygen -R hostname` rimuove la riga corrispondente all'hostname (anche se hashato). La modifica manuale è necessaria quando known_hosts contiene hostname hashati (`HashKnownHosts yes`) e non si conosce la riga esatta.

**Q12: Come posso limitare i comandi che un utente può eseguire via SSH?**
(1) `ForceCommand` nel sshd_config (un solo comando), (2) `command="..."` in authorized_keys (per chiave), (3) `restrict` in authorized_keys (disabilita tutto, poi abilita selettivamente), (4) restricted shell (`rbash`), (5) `Match User` con `ForceCommand` nel sshd_config.

**Q13: Come funziona il rekey in SSH? È necessario configurarlo?**
SSH esegue automaticamente il rekey dopo 1 GB di dati o periodicamente (dipende dall'implementazione). `RekeyLimit 512M 1h` forza il rekey dopo 512 MB o 1 ora. Per la maggior parte degli usi, il default è sufficiente. Su connessioni long-lived con molto traffico (tunnel), configurare RekeyLimit è buona pratica.

**Q14: SSH funziona con IPv6?**
Sì. `ssh user@[::1]` per localhost IPv6, `ssh user@[2001:db8::1]` per IP specifici. In sshd_config: `AddressFamily any` (o `inet6` per solo IPv6). In ssh_config: `AddressFamily any`.

**Q15: Come verifico che la mia configurazione sshd sia conforme al CIS Benchmark?**
(1) Usare `ssh-audit` (https://github.com/jtesta/ssh-audit) per analisi automatica, (2) `sudo sshd -T` per il dump della configurazione effettiva, (3) confrontare con le raccomandazioni CIS (vedi sezione "Direttive CIS Benchmark"). (4) Strumenti come Lynis (`lynis audit system --tests-from-group "ssh"`) per audit completo.

**Q16: Come posso usare SSH con hardware key (YubiKey)?**
(1) Generare chiave: `ssh-keygen -t ed25519-sk` (richiede OpenSSH 8.2+), (2) la chiave privata è sul dispositivo hardware, il file locale è solo un handle, (3) ogni autenticazione richiede toccare fisicamente la YubiKey, (4) supporta anche `ecdsa-sk`, (5) per resident key (chiave interamente sulla YubiKey): `ssh-keygen -t ed25519-sk -O resident`.

**Q17: Come mi proteggo da SSH terrapin attack (CVE-2023-48795)?**
(1) Aggiornare OpenSSH a 9.6+ (patch inclusa), (2) il fix è una "strict key exchange" extension, (3) verificare con `ssh-audit` che il server supporti `strict-kex`, (4) rimuovere cifrari CBC e `chacha20-poly1305` su versioni non patchate.

---

## Security Audit Checklist

Checklist per l'audit di sicurezza dell'infrastruttura SSH. Ogni punto deve essere verificato periodicamente (consigliato: trimestralmente).

```
═══════════════════════════════════════════════════════════════════
                    SSH SECURITY AUDIT CHECKLIST
═══════════════════════════════════════════════════════════════════

▸ CONFIGURAZIONE SERVER (sshd_config)
  [ ] PermitRootLogin no (o prohibit-password)
  [ ] PasswordAuthentication no
  [ ] PermitEmptyPasswords no
  [ ] PubkeyAuthentication yes
  [ ] AuthenticationMethods publickey (o publickey,keyboard-interactive)
  [ ] X11Forwarding no (a meno che necessario)
  [ ] AllowAgentForwarding no (a meno che necessario)
  [ ] AllowUsers/AllowGroups configurato (whitelist)
  [ ] MaxAuthTries ≤ 4
  [ ] MaxSessions ≤ 10
  [ ] LoginGraceTime ≤ 60
  [ ] ClientAliveInterval configurato
  [ ] ClientAliveCountMax configurato
  [ ] LogLevel VERBOSE
  [ ] Banner configurato
  [ ] PermitUserEnvironment no
  [ ] UseDNS no
  [ ] Protocol 2 (implicito in OpenSSH 7.4+)
  [ ] StrictModes yes (default)

▸ CRITTOGRAFIA
  [ ] Solo cifrari forti in Ciphers (chacha20, aes-gcm, aes-ctr)
  [ ] Solo MAC forti in MACs (hmac-sha2-*-etm)
  [ ] Solo key exchange forti in KexAlgorithms (curve25519, DH group16/18)
  [ ] Moduli DH ≥ 3072 bit in /etc/ssh/moduli
  [ ] Host key ed25519 presente e prioritario
  [ ] Nessun algoritmo deprecato (DSA, RSA-SHA1, diffie-hellman-group1)

▸ PERMESSI FILE
  [ ] /etc/ssh/sshd_config: owner root, mode 0600
  [ ] /etc/ssh/ssh_host_*_key: owner root, mode 0600
  [ ] /etc/ssh/ssh_host_*_key.pub: owner root, mode 0644
  [ ] ~/.ssh/: mode 0700
  [ ] ~/.ssh/authorized_keys: mode 0600
  [ ] ~/.ssh/config: mode 0600
  [ ] ~/.ssh/id_*: mode 0600 (chiavi private)
  [ ] Home directory: non group/world-writable

▸ CHIAVI E CERTIFICATI
  [ ] Tutte le chiavi attive sono ≥ ed25519 o RSA 4096
  [ ] Nessuna chiave DSA o RSA < 2048
  [ ] Tutte le chiavi private hanno passphrase (verificare con ssh-keygen -yf)
  [ ] Chiavi di ex dipendenti rimosse da tutti i server
  [ ] authorized_keys non contiene chiavi sconosciute/non documentate
  [ ] Rotazione chiavi effettuata negli ultimi 12 mesi
  [ ] Se certificati SSH: CA key protetta e in storage sicuro
  [ ] Se certificati SSH: validità massima ≤ 52 settimane
  [ ] Se KRL: distribuita e aggiornata su tutti i server

▸ RETE E FIREWALL
  [ ] SSH accessibile solo da IP/reti autorizzate
  [ ] fail2ban attivo su tutti i server esposti a Internet
  [ ] Rate limiting configurato (MaxStartups o iptables)
  [ ] Bastion host come unico punto di ingresso (se applicabile)
  [ ] Nessun server SSH esposto direttamente su Internet senza protezione

▸ AUTENTICAZIONE E ACCESSO
  [ ] 2FA configurato sul bastion host
  [ ] Nessun utente con password auth se non strettamente necessario
  [ ] Nessun utente con authorized_keys senza restrizioni inutili
  [ ] ForceCommand usato per chiavi di servizio/automazione
  [ ] restrict usato per chiavi con permessi limitati

▸ LOGGING E MONITORING
  [ ] LogLevel VERBOSE su tutti i server
  [ ] Log centralizzati (SIEM, syslog remoto)
  [ ] Alert per login falliti multipli
  [ ] Alert per login da IP/geolocalizzazioni anomale
  [ ] Alert per login fuori orario
  [ ] Session recording attivo sul bastion (se applicabile)

▸ STRUMENTI DI AUDIT
  [ ] ssh-audit eseguito su tutti i server
      ssh-audit server.example.com
  [ ] Lynis SSH audit eseguito
      lynis audit system --tests-from-group "ssh"
  [ ] Nessuna vulnerabilità nota nella versione OpenSSH installata
      ssh -V

▸ PROCEDURE
  [ ] Procedura di rotazione chiavi documentata
  [ ] Procedura di revoca d'emergenza documentata e testata
  [ ] Procedura di offboarding (rimozione accesso SSH) documentata
  [ ] Contatti di emergenza per incidenti SSH documentati
  [ ] Ultimo audit completato: _____________ (data)
  [ ] Prossimo audit pianificato: _____________ (data)

═══════════════════════════════════════════════════════════════════
  Eseguire audit con: ssh-audit <host>
  Ref: CIS Benchmark, NIST SP 800-123, RFC 4253
═══════════════════════════════════════════════════════════════════
```
