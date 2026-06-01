# Certificati SSL/TLS in Proxmox VE

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 5 — Operativita post-migrazione · Modulo 12.1 (apre sezione sicurezza, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 02 (architettura Proxmox cluster); modulo 04 (DNS interno); concetti PKI: CA, CSR, X.509, SAN, OCSP; familiarita con Let's Encrypt e ACME (RFC 8555).
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. sostituire i **certificati self-signed** Proxmox con certificati validi (ACME Let's Encrypt o CA interna), comprendendo l'impatto su web GUI, API, cluster comm, console SPICE/noVNC;
> 2. configurare **ACME/Let's Encrypt** con HTTP-01 challenge (richiede 80/tcp esposto) o DNS-01 (richiede plugin DNS provider, supportato per certificati wildcard); rinnovo automatico via cron job + `pvenode acme cert order`;
> 3. configurare una **CA interna** (es. step-ca, HashiCorp Vault PKI, OpenSSL CA) per ambienti senza accesso Internet; importazione cert + chain in `/etc/pve/local/pveproxy-ssl.pem`;
> 4. configurare **OCSP stapling** (verifica revoca) e CRL Distribution Point per CA interna;
> 5. gestire **wildcard certificates** vs SAN list (multipli FQDN); pinning di nomi host vs IP;
> 6. configurare **mTLS per comunicazione cluster** fra nodi Proxmox, comprendere il ruolo di `pve-root-ca.pem` come trust anchor;
> 7. implementare **HSTS** tramite reverse proxy (nginx/HAProxy) e **SSL pinning** per client API;
> 8. selezionare **cipher suite** appropriate per conformita PCI-DSS, NIST, FIPS 140-2;
> 9. implementare **monitoraggio certificati** con Prometheus, node_exporter e alerting automatico;
> 10. validare la configurazione: `openssl s_client -connect pve1.example.com:8006`, `curl -v https://pve1.example.com:8006`, browser inspector, `testssl.sh` per audit completo (cipher suite, TLS 1.2/1.3, HSTS, OCSP).
> **Tempo stimato:** lettura 90-120 min · lab 300-420 min (deploy ACME + CA interna + mTLS + HSTS + audit completo)
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-05-22
> **Versioni di riferimento:** Proxmox VE 8.x; ACME RFC 8555; step-ca 0.25+; HashiCorp Vault 1.16+; OpenSSL 3.x; testssl.sh 3.x; nginx 1.24+.

## Mappa concettuale

```
+============================================================+
|     Certificati Proxmox: opzioni e flusso ACME              |
+============================================================+
|                                                            |
|   POSIZIONI CERTIFICATI                                    |
|   /etc/pve/local/pveproxy-ssl.pem    cert per web GUI      |
|   /etc/pve/local/pveproxy-ssl.key    chiave privata        |
|   /etc/pve/local/pve-ssl.pem         cert per cluster comm |
|   /etc/pve/local/pve-ssl.key         chiave cluster        |
|   /etc/pve/pve-www.key               chiave HTTP API       |
|   /etc/pve/pve-root-ca.pem           CA root cluster       |
|   /etc/pve/priv/pve-root-ca.key      chiave CA root        |
|                                                            |
|   ACME FLOW (Let's Encrypt, HTTP-01)                       |
|   1. pvenode acme account register                         |
|   2. pvenode config set --acme domains=pve1.example.com    |
|   3. pvenode acme cert order                               |
|      -> ACME server emette challenge                       |
|      -> Proxmox espone /.well-known/acme-challenge/...     |
|      -> ACME server verifica HTTP                          |
|      -> Emette cert (X.509 firmato da ISRG Root)           |
|      -> Cert + key salvati in /etc/pve/local/pveproxy-ssl.*|
|   4. cron job: pvenode acme cert order (ogni 60-89 giorni) |
|                                                            |
|   ACME FLOW (DNS-01, per wildcards)                        |
|   1. pvenode acme plugin add dns example                   |
|   2. configurare API token DNS provider                    |
|   3. Proxmox aggiunge TXT record _acme-challenge.*         |
|   4. ACME server verifica DNS                              |
|   5. Cert wildcard *.example.com emesso                    |
|                                                            |
|   CA INTERNA (alternativa per air-gapped)                  |
|   - step-ca o Vault PKI o openssl manuale                  |
|   - root cert distribuito ai client (OS trust store)       |
|   - emissione cert: openssl req + openssl ca               |
|   - import: pvecm updatecerts (per cluster) o file system  |
|                                                            |
|   mTLS CLUSTER                                             |
|   - pve-root-ca.pem = trust anchor condiviso               |
|   - ogni nodo ha pve-ssl.pem firmato dalla CA cluster      |
|   - corosync usa crittografia con libknet + knet crypto    |
|   - pmxcfs replica cert via cluster filesystem             |
|                                                            |
|   HSTS + REVERSE PROXY                                     |
|   - pveproxy non supporta HSTS nativo                      |
|   - nginx/HAProxy davanti a pveproxy per HSTS header       |
|   - SSL termination al reverse proxy o pass-through        |
|                                                            |
|   MONITORAGGIO                                             |
|   - x509_certificate_expiry_seconds metric                 |
|   - blackbox_exporter per probe SSL                        |
|   - alertmanager: alert 30/7/1 giorni prima scadenza       |
|                                                            |
+============================================================+
```

Idee guida del modulo:

1. **Self-signed in produzione e antipattern.** Browser warnings, broken HSTS, broken WebAuthn, broken certain SPICE features. ACME e gratis e automatico per ambienti con DNS pubblico — non c'e scusa.
2. **DNS-01 per wildcards e ambienti senza port 80 esposto.** HTTP-01 richiede 80/tcp inbound; per Proxmox interno con firewall strict, DNS-01 e l'opzione standard.
3. **Rinnovo automatico va monitorato.** Cert scaduto = web GUI inaccessibile. Schedulare il rinnovo a 60 giorni per certificati 90-giorni Let's Encrypt; alert se rinnovo fallisce.
4. **Per air-gapped, step-ca o Vault PKI.** OpenSSL CA manuale e legacy e error-prone. step-ca offre ACME compatibile in interno; integrazione perfetta con Proxmox.
5. **Audit cipher suite e TLS version.** `testssl.sh` valida configurazione TLS contro best practice corrente. Disabilitare TLS 1.0/1.1, RC4, 3DES; abilitare HSTS preload.
6. **mTLS cluster e il cuore della fiducia inter-nodo.** La CA interna del cluster (`pve-root-ca.pem`) firma i certificati di ogni nodo; compromettere la CA root compromette l'intero cluster.
7. **HSTS richiede reverse proxy.** Proxmox pveproxy non emette l'header HSTS; per compliance occorre un reverse proxy configurato davanti alla web GUI.

---

## Introduzione

La gestione dei certificati SSL/TLS e un aspetto critico della sicurezza in qualsiasi infrastruttura di virtualizzazione. I certificati proteggono la comunicazione tra gli amministratori e la web GUI, tra i nodi del cluster, tra le console delle VM e i client SPICE/noVNC, e tra i componenti dell'ecosistema Proxmox (PVE, PBS, PMG).

In VMware, la gestione dei certificati e storicamente uno dei punti piu problematici: il vCenter Certificate Manager e noto per la sua complessita e fragilita. In Proxmox VE, la gestione dei certificati e significativamente piu semplice, grazie all'integrazione nativa con il protocollo ACME (Let's Encrypt) e alla possibilita di gestire i certificati direttamente dalla GUI o dalla CLI.

Questo documento fornisce una guida completa alla gestione dei certificati in Proxmox VE, dalla sostituzione dei certificati self-signed alla configurazione di una PKI interna, dal mTLS cluster al monitoraggio automatico della scadenza, dall'hardening delle cipher suite all'implementazione di HSTS tramite reverse proxy.

---

## 1. Fondamenti PKI e TLS per Ambienti di Virtualizzazione

### 1.1 Richiamo su X.509 e Catena di Fiducia

Un certificato X.509 contiene: soggetto (CN + SAN), chiave pubblica, issuer (CA firmataria), validita temporale, estensioni (key usage, extended key usage, OCSP responder URI, CRL distribution point). La catena di fiducia funziona cosi:

```
Root CA (auto-firmata, nel trust store)
    |
    +-- Intermediate CA (firmata dalla Root)
            |
            +-- Server Certificate (firmato dall'Intermediate)
                    |
                    +-- Presentato al client durante TLS handshake
```

Il client verifica: (1) il cert server e firmato da una CA nel trust store; (2) la catena e completa; (3) il cert non e revocato (OCSP/CRL); (4) il CN o SAN corrisponde all'hostname; (5) il cert non e scaduto.

### 1.2 TLS Handshake: Cosa Succede su Porta 8006

Quando un browser accede a `https://pve1.example.com:8006`:

```
Client                           pveproxy (porta 8006)
  |                                   |
  |--- ClientHello (TLS version,      |
  |    cipher suites supportate,      |
  |    SNI hostname) --------------->|
  |                                   |
  |<--- ServerHello (cipher scelta,   |
  |     certificato server,           |
  |     catena intermedi) -----------|
  |                                   |
  |--- Verifica certificato           |
  |    (trust chain, SAN, OCSP)       |
  |                                   |
  |--- ClientKeyExchange ----------->|
  |                                   |
  |<--- Finished --------------------|
  |                                   |
  |=== Canale TLS stabilito ==========|
```

### 1.3 Differenza tra TLS 1.2 e TLS 1.3

| Aspetto | TLS 1.2 | TLS 1.3 |
|---------|---------|---------|
| Round-trip per handshake | 2 RTT | 1 RTT (0-RTT con resumption) |
| Cipher suite | Negoziabili individualmente | Solo AEAD (AES-GCM, ChaCha20-Poly1305) |
| Forward Secrecy | Opzionale (dipende dalla cipher) | Obbligatorio (solo ECDHE/DHE) |
| Compression | Supportata (ma disabilitata per CRIME) | Rimossa |
| Renegotiation | Supportata | Rimossa |
| 0-RTT Resumption | No | Si (con rischi di replay) |

Proxmox VE 8.x supporta sia TLS 1.2 che TLS 1.3 tramite OpenSSL 3.x.

---

## 2. Certificati Predefiniti (Self-Signed)

### 2.1 Certificati Generati all'Installazione

Proxmox VE genera automaticamente certificati self-signed durante l'installazione:

```bash
# Certificato del nodo PVE (usato dalla web GUI e dalle API)
ls -la /etc/pve/local/pve-ssl.pem
ls -la /etc/pve/local/pve-ssl.key

# Certificato CA del cluster PVE
ls -la /etc/pve/pve-root-ca.pem
ls -la /etc/pve/priv/pve-root-ca.key

# Visualizzare il certificato attuale
openssl x509 -in /etc/pve/local/pve-ssl.pem -noout -text | head -30

# Verificare la scadenza
openssl x509 -in /etc/pve/local/pve-ssl.pem -noout -dates

# Verificare il Subject e il SAN
openssl x509 -in /etc/pve/local/pve-ssl.pem -noout -subject -ext subjectAltName

# Verificare la chiave pubblica
openssl x509 -in /etc/pve/local/pve-ssl.pem -noout -pubkey | openssl pkey -pubin -text -noout

# Fingerprint per confronto manuale
openssl x509 -in /etc/pve/local/pve-ssl.pem -noout -fingerprint -sha256
```

### 2.2 Struttura dei Certificati nel Cluster

| File | Posizione | Replicato | Scopo |
|------|-----------|-----------|-------|
| `pve-root-ca.pem` | `/etc/pve/pve-root-ca.pem` | Si (cluster-wide) | CA root del cluster |
| `pve-root-ca.key` | `/etc/pve/priv/pve-root-ca.key` | Si (cluster-wide) | Chiave privata CA |
| `pve-ssl.pem` | `/etc/pve/local/pve-ssl.pem` | No (per nodo) | Certificato del nodo |
| `pve-ssl.key` | `/etc/pve/local/pve-ssl.key` | No (per nodo) | Chiave privata del nodo |
| `pveproxy-ssl.pem` | `/etc/pve/local/pveproxy-ssl.pem` | No (per nodo) | Certificato custom per pveproxy |
| `pveproxy-ssl.key` | `/etc/pve/local/pveproxy-ssl.key` | No (per nodo) | Chiave privata custom per pveproxy |

> **Nota:** I file in `/etc/pve/local/` sono in realta symlink a `/etc/pve/nodes/<nodename>/`, che e specifico per ogni nodo ma memorizzato nel cluster filesystem pmxcfs.

### 2.3 Gerarchia di Precedenza dei Certificati

Proxmox segue una gerarchia di precedenza per i certificati usati da pveproxy:

```
1. /etc/pve/local/pveproxy-ssl.pem  (custom cert, massima priorita)
   Se presente, pveproxy usa questo certificato.

2. /etc/pve/local/pve-ssl.pem       (cert generato dalla CA cluster)
   Se pveproxy-ssl.pem non esiste, usa il cert cluster.

3. Self-signed generato all'installazione (fallback)
```

Quando si installa un certificato ACME o custom, Proxmox lo salva come `pveproxy-ssl.pem`, che ha priorita massima.

### 2.4 Problemi con i Certificati Self-Signed

| Problema | Impatto | Soluzione |
|----------|---------|-----------|
| Browser mostra avviso di sicurezza | UX scadente, potenziale confusione | Installare certificati validi |
| SPICE client rifiuta la connessione | Console VM non funzionante | Importare CA nel client o usare noVNC |
| Automazione API fallisce | Script e integrazioni non funzionano | Importare CA o usare `--insecure` (non consigliato) |
| WebAuthn/FIDO2 non funziona | 2FA hardware non disponibile | Richiede certificato valido (non self-signed) |
| Monitoraggio esterno | Alert falsi positivi | Importare CA nel sistema di monitoraggio |
| HSTS non configurabile | Non conforme a PCI-DSS | Reverse proxy con cert valido |
| Client mobile rifiuta connessione | App Proxmox non funziona | Certificato valido o import CA |

---

## 3. Let's Encrypt con ACME Plugin

### 3.1 Prerequisiti

Per utilizzare Let's Encrypt, i nodi Proxmox devono:

- Avere un FQDN valido risolvibile pubblicamente (per HTTP-01 challenge)
- OPPURE avere accesso API al provider DNS (per DNS-01 challenge)
- La porta 80 deve essere raggiungibile dall'esterno (solo per HTTP-01)

### 3.2 Registrazione Account ACME

```bash
# Registrare un account ACME con Let's Encrypt (produzione)
pvenode acme account register default admin@studio-lavoro.local \
  --directory https://acme-v02.api.letsencrypt.org/directory

# Per test iniziali, usare l'ambiente di staging (nessun rate limit)
pvenode acme account register staging-account admin@studio-lavoro.local \
  --directory https://acme-staging-v02.api.letsencrypt.org/directory

# Verificare gli account registrati
pvenode acme account list

# Visualizzare i dettagli di un account
pvenode acme account info default

# Deregistrare un account (se necessario)
pvenode acme account deactivate staging-account
```

### 3.3 Metodo HTTP-01 Challenge

Adatto per nodi con accesso diretto da Internet sulla porta 80:

```bash
# Configurare il dominio per il nodo
pvenode config set --acme domains=pve-node01.studio-lavoro.com

# Richiedere il certificato (HTTP-01 e il default)
pvenode acme cert order

# Verificare il certificato ottenuto
openssl x509 -in /etc/pve/local/pveproxy-ssl.pem -noout -dates -subject

# Il servizio pveproxy viene riavviato automaticamente

# Verificare che la GUI risponda con il nuovo certificato
curl -v https://pve-node01.studio-lavoro.com:8006 2>&1 | grep "subject:"
```

**Funzionamento interno di HTTP-01:**

```
1. Proxmox genera una coppia chiave/CSR
2. Invia il CSR a Let's Encrypt
3. Let's Encrypt risponde con un token
4. Proxmox espone il token su http://pve-node01:80/.well-known/acme-challenge/<token>
5. Let's Encrypt fa una richiesta HTTP al token
6. Se la risposta e corretta, emette il certificato
7. Proxmox salva cert e key in /etc/pve/local/pveproxy-ssl.*
8. Riavvia pveproxy
```

> **Attenzione:** HTTP-01 richiede che la porta 80/tcp sia raggiungibile dall'esterno. Se il nodo e dietro un firewall/NAT, e necessario configurare port forwarding o usare DNS-01.

### 3.4 Metodo DNS-01 Challenge (Consigliato per Ambienti Interni)

Il metodo DNS-01 non richiede accesso diretto da Internet e supporta anche wildcard certificates.

**Plugin DNS supportati da Proxmox:**

| Provider DNS | Plugin ID | Note |
|-------------|-----------|------|
| Cloudflare | `1` | Piu comune |
| DigitalOcean | `2` | |
| DNS Made Easy | `3` | |
| Gandi Live DNS | `4` | |
| GoDaddy | `5` | |
| Hetzner | `6` | |
| OVH | `7` | |
| PowerDNS | `8` | Per DNS interni |
| RFC 2136 (nsupdate) | `9` | Per BIND/PowerDNS interni |
| Azure DNS | `10` | |
| AWS Route 53 | `11` | |
| Google Cloud DNS | `12` | |
| Standalone | Custom | Per script personalizzati |

**Esempio con Cloudflare:**

```bash
# Creare il plugin DNS per Cloudflare
pvenode acme plugin add dns cloudflare-plugin \
  --api cf \
  --data "CF_Account_ID=ACCOUNT_ID_HERE\nCF_Token=API_TOKEN_HERE"

# Configurare il nodo con il plugin DNS
pvenode config set \
  --acme "account=default" \
  --acmedomain0 "domain=pve-node01.studio-lavoro.com,plugin=cloudflare-plugin"

# Richiedere il certificato
pvenode acme cert order

# Verificare il record TXT creato durante la validazione
dig TXT _acme-challenge.pve-node01.studio-lavoro.com
```

**Esempio con RFC 2136 (DNS interno con BIND):**

```bash
# Generare una chiave TSIG per l'aggiornamento DNS
tsig-keygen -a hmac-sha256 proxmox-acme > /etc/pve/priv/acme-tsig.key

# Configurare il plugin RFC 2136
pvenode acme plugin add dns rfc2136-plugin \
  --api nsupdate \
  --data "NSUPDATE_SERVER=dns.studio-lavoro.local\nNSUPDATE_KEY=/etc/pve/priv/acme-tsig.key"

# Configurare il dominio
pvenode config set \
  --acme "account=default" \
  --acmedomain0 "domain=pve-node01.studio-lavoro.local,plugin=rfc2136-plugin"

# Richiedere il certificato
pvenode acme cert order
```

**Esempio con PowerDNS:**

```bash
# Configurare il plugin PowerDNS
pvenode acme plugin add dns pdns-plugin \
  --api pdns \
  --data "PDNS_Url=http://powerdns.studio-lavoro.local:8081\nPDNS_ServerId=localhost\nPDNS_Token=API_KEY_HERE"

# Configurare il dominio
pvenode config set \
  --acme "account=default" \
  --acmedomain0 "domain=pve-node01.studio-lavoro.local,plugin=pdns-plugin"

# Richiedere il certificato
pvenode acme cert order
```

**Esempio con AWS Route 53:**

```bash
# Configurare il plugin Route 53
pvenode acme plugin add dns route53-plugin \
  --api aws \
  --data "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\nAWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

# Configurare il dominio
pvenode config set \
  --acme "account=default" \
  --acmedomain0 "domain=pve-node01.studio-lavoro.com,plugin=route53-plugin"

# Richiedere il certificato
pvenode acme cert order
```

### 3.5 Wildcard Certificates vs SAN List

| Aspetto | Wildcard (`*.example.com`) | SAN List (multi-FQDN) |
|---------|---------------------------|----------------------|
| Copertura | Tutti i sottodomini di un livello | Solo i FQDN elencati |
| Richiede DNS-01 | Si | No (HTTP-01 possibile) |
| Gestione | Un cert per tutti i nodi | Un cert per nodo |
| Rischio sicurezza | Se compromesso, vale per tutti i sottodomini | Scope limitato |
| Rinnovo | Singolo rinnovo per tutti | Un rinnovo per nodo |
| Uso consigliato | Cluster grandi (>10 nodi), ambienti dinamici | Cluster piccoli (<10 nodi) |

**Configurazione wildcard con Cloudflare:**

```bash
# Wildcard richiede DNS-01
pvenode config set \
  --acme "account=default" \
  --acmedomain0 "domain=*.pve.studio-lavoro.com,plugin=cloudflare-plugin" \
  --acmedomain1 "domain=pve.studio-lavoro.com,plugin=cloudflare-plugin"

pvenode acme cert order
```

> **Nota:** Per wildcard, il certificato copre `*.pve.studio-lavoro.com` ma NON `pve.studio-lavoro.com` stesso. Aggiungere entrambi come SAN se necessario.

### 3.6 Configurazione tramite GUI

1. Navigare a **Datacenter -> ACME**
2. **Account** tab:
   - Cliccare **Add** per registrare un nuovo account
   - Inserire email e selezionare la directory (produzione o staging)
3. **Challenge Plugins** tab:
   - Cliccare **Add** per aggiungere un plugin DNS
   - Selezionare il tipo di API DNS
   - Inserire le credenziali
4. Per ogni nodo (**Node -> Certificates**):
   - Tab **ACME**: configurare i domini
   - Cliccare **Order Certificates Now**

### 3.7 Rinnovo Automatico

Proxmox VE gestisce automaticamente il rinnovo dei certificati ACME:

```bash
# Verificare il timer di rinnovo
systemctl status pve-daily-update.timer
systemctl list-timers | grep pve

# Il rinnovo viene tentato automaticamente 30 giorni prima della scadenza
# Verificare i log di rinnovo
journalctl -u pve-daily-update | grep -i acme

# Forzare il rinnovo manuale
pvenode acme cert renew

# Verificare la data di scadenza
pvenode acme cert info

# Verificare la scadenza con openssl
openssl x509 -in /etc/pve/local/pveproxy-ssl.pem -noout -enddate
```

### 3.8 Let's Encrypt Rate Limits

| Limite | Valore | Conseguenza |
|--------|--------|-------------|
| Certificates per Registered Domain | 50/settimana | Max 50 cert per `*.example.com` a settimana |
| Duplicate Certificate | 5/settimana | Max 5 cert con lo stesso set di SAN |
| New Orders | 300/3 ore | Max 300 nuovi ordini per account |
| Failed Validations | 5/hostname/ora | Dopo 5 fallimenti, 1 ora di blocco |
| Pending Authorizations | 300/account | Max 300 auth pendenti |

**Strategie per cluster grandi (>10 nodi):**

1. Usare un singolo wildcard cert `*.cluster.example.com` invece di N cert separati
2. Usare staging environment per test (nessun rate limit, cert non trusted)
3. Monitorare l'uso vs limit con `pvenode acme account info`
4. Per cluster >50 nodi, considerare una CA interna con step-ca

---

## 4. Certificati da CA Personalizzata (Custom CA)

### 4.1 Installazione di Certificati Custom

Per ambienti che utilizzano una CA interna (Microsoft AD CS, HashiCorp Vault PKI, CFSSL, ecc.):

```bash
# Passo 1: Generare una CSR (Certificate Signing Request) per il nodo
openssl req -new -newkey rsa:4096 -keyout /tmp/pve-node01.key -out /tmp/pve-node01.csr -nodes \
  -subj "/C=IT/ST=Lazio/L=Roma/O=Studio Lavoro/OU=Infrastruttura/CN=pve-node01.studio-lavoro.local" \
  -addext "subjectAltName=DNS:pve-node01.studio-lavoro.local,DNS:pve-node01,IP:10.10.1.10"

# Passo 2: Firmare la CSR con la CA interna
# Esempio con openssl (CA interna semplice):
openssl x509 -req -in /tmp/pve-node01.csr \
  -CA /path/to/ca.pem -CAkey /path/to/ca.key -CAcreateserial \
  -out /tmp/pve-node01.pem -days 365 \
  -extfile <(printf "subjectAltName=DNS:pve-node01.studio-lavoro.local,DNS:pve-node01,IP:10.10.1.10\nkeyUsage=digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth")

# Passo 3: Verificare il certificato generato
openssl x509 -in /tmp/pve-node01.pem -noout -text | grep -A5 "Subject:"
openssl verify -CAfile /path/to/ca.pem /tmp/pve-node01.pem

# Passo 4: Installare il certificato su Proxmox
# Copiare la chiave privata
cp /tmp/pve-node01.key /etc/pve/local/pveproxy-ssl.key
chmod 600 /etc/pve/local/pveproxy-ssl.key

# Copiare il certificato (con la chain completa)
cat /tmp/pve-node01.pem /path/to/intermediate-ca.pem > /etc/pve/local/pveproxy-ssl.pem

# Passo 5: Riavviare pveproxy
systemctl restart pveproxy

# Passo 6: Verificare
openssl s_client -connect localhost:8006 </dev/null 2>/dev/null | openssl x509 -noout -dates -subject -issuer
```

### 4.2 Installazione tramite GUI

1. Navigare a **Node -> Certificates**
2. Tab **Upload Custom Certificate**
3. Incollare il contenuto del certificato (PEM) nel campo **Certificate (PEM)**
4. Incollare il contenuto della chiave privata nel campo **Key (PEM)**
5. Se necessario, includere i certificati intermedi nella chain
6. Cliccare **Upload**
7. pveproxy viene riavviato automaticamente

### 4.3 Installazione tramite API

```bash
# Usando pvesh per installare un certificato custom
pvesh set /nodes/pve-node01/certificates/custom \
  --certificates "$(cat /tmp/pve-node01.pem)" \
  --key "$(cat /tmp/pve-node01.key)" \
  --restart 1 \
  --force 1

# Verificare tramite API
pvesh get /nodes/pve-node01/certificates/info --output-format json-pretty
```

### 4.4 Distribuzione della CA su Tutti i Nodi

```bash
# Per ogni nodo del cluster, importare la CA interna
for node in pve-node01 pve-node02 pve-node03; do
  scp /path/to/internal-ca.pem ${node}:/usr/local/share/ca-certificates/internal-ca.crt
  ssh ${node} "update-ca-certificates"
done

# Verificare su ogni nodo
openssl verify -CApath /etc/ssl/certs/ /etc/pve/local/pveproxy-ssl.pem

# Verificare che curl non dia errori SSL
for node in pve-node01 pve-node02 pve-node03; do
  curl -s -o /dev/null -w "%{http_code} %{ssl_verify_result}" "https://${node}:8006/api2/json/version"
  echo " $node"
done
```

---

## 5. mTLS e Comunicazione Cluster

### 5.1 Come Funziona la CA Cluster Interna

Proxmox crea automaticamente una CA interna (`pve-root-ca.pem`) durante la creazione del cluster. Questa CA firma i certificati di ogni nodo per la comunicazione inter-nodo. Il flusso:

```
pve-root-ca.pem (CA root cluster)
    |
    +-- pve-ssl.pem su node1 (firmato dalla CA cluster)
    +-- pve-ssl.pem su node2 (firmato dalla CA cluster)
    +-- pve-ssl.pem su node3 (firmato dalla CA cluster)
```

La comunicazione tra nodi (API calls inter-cluster, replica storage, migration) usa questi certificati per autenticazione mutua (mTLS): ogni nodo verifica che l'altro nodo presenti un certificato firmato dalla stessa CA cluster.

```bash
# Verificare la CA cluster
openssl x509 -in /etc/pve/pve-root-ca.pem -noout -subject -issuer -dates

# Verificare che il cert del nodo sia firmato dalla CA cluster
openssl verify -CAfile /etc/pve/pve-root-ca.pem /etc/pve/local/pve-ssl.pem

# Verificare la connessione mTLS tra nodi
openssl s_client -connect pve-node02:8006 -CAfile /etc/pve/pve-root-ca.pem </dev/null 2>&1 | grep "Verify return code"
```

### 5.2 Corosync e Crittografia di Rete

Corosync, il componente che gestisce il cluster membership e il quorum, supporta la crittografia del traffico inter-nodo tramite libknet:

```bash
# Verificare la configurazione corosync
cat /etc/pve/corosync.conf | grep -A5 "totem"

# La sezione totem contiene le impostazioni di crittografia:
# totem {
#     ...
#     crypto_cipher: aes256
#     crypto_hash: sha256
#     ...
# }

# Verificare lo stato del cluster con crittografia
pvecm status

# Verificare le chiavi corosync
ls -la /etc/corosync/authkey

# Rigenerare la chiave corosync (richiede cluster quiescente)
# ATTENZIONE: operazione rischiosa, ferma tutte le operazioni cluster prima
# corosync-keygen
# pvecm updatecerts
```

### 5.3 Rinnovo Certificati Cluster

I certificati del cluster (`pve-ssl.pem`) vengono rinnovati automaticamente da Proxmox. Se necessario rinnovare manualmente:

```bash
# Rigenerare il certificato di un nodo (signed dalla CA cluster)
pvecm updatecerts --force

# Verificare il nuovo certificato
openssl x509 -in /etc/pve/local/pve-ssl.pem -noout -dates -subject

# Verificare lo stato su tutti i nodi
pvecm nodes
pvecm status
```

### 5.4 Separazione tra Certificati Custom e Cluster

Un punto critico: installare un certificato ACME o custom (`pveproxy-ssl.pem`) NON sostituisce il certificato cluster (`pve-ssl.pem`). I due coesistono:

```
pveproxy-ssl.pem  → usato da pveproxy per la web GUI e le API (visibile ai browser)
pve-ssl.pem       → usato per la comunicazione inter-nodo (non visibile ai browser)
```

Questo design permette di avere un certificato Let's Encrypt per la GUI (trusted dai browser) e contemporaneamente un certificato cluster interno per la comunicazione mTLS tra nodi.

---

## 6. Certificati per Proxmox Backup Server (PBS)

### 6.1 Struttura Certificati PBS

```bash
# Certificati PBS
ls -la /etc/proxmox-backup/proxy.pem    # Certificato
ls -la /etc/proxmox-backup/proxy.key    # Chiave privata

# Verificare il certificato attuale
openssl x509 -in /etc/proxmox-backup/proxy.pem -noout -dates -subject
```

### 6.2 ACME per PBS

```bash
# PBS supporta ACME nativamente
proxmox-backup-manager acme account register default admin@studio-lavoro.local

# Aggiungere un plugin DNS (esempio Cloudflare)
proxmox-backup-manager acme plugin add dns cf-plugin --api cf \
  --data "CF_Token=API_TOKEN"

# Configurare il dominio
proxmox-backup-manager node config set \
  --acme "account=default" \
  --acmedomain0 "domain=pbs01.studio-lavoro.com,plugin=cf-plugin"

# Richiedere il certificato
proxmox-backup-manager acme cert order

# Verificare
proxmox-backup-manager acme cert info
```

### 6.3 Certificati Custom per PBS

```bash
# Installare un certificato custom su PBS
cp /tmp/pbs01.pem /etc/proxmox-backup/proxy.pem
cp /tmp/pbs01.key /etc/proxmox-backup/proxy.key
chmod 640 /etc/proxmox-backup/proxy.key

# Riavviare il servizio
systemctl restart proxmox-backup-proxy

# Verificare
openssl s_client -connect localhost:8007 </dev/null 2>/dev/null | openssl x509 -noout -dates -subject
```

### 6.4 Trust Reciproco PVE-PBS

Per il backup da PVE a PBS, il nodo PVE deve fidarsi del certificato PBS:

```bash
# Ottenere il fingerprint del certificato PBS
proxmox-backup-manager cert info 2>/dev/null | grep -i fingerprint

# Configurare PVE per fidarsi di PBS
pvesm add pbs pbs-store \
  --server pbs01.studio-lavoro.local \
  --username backup@pbs \
  --datastore datastore1 \
  --fingerprint "ab:cd:ef:12:34:56:..."

# Se PBS usa un cert trusted (ACME o CA importata nel trust store),
# il fingerprint puo essere omesso
```

---

## 7. Certificati per Console SPICE

### 7.1 Configurazione SPICE con Certificati

La console SPICE utilizza i certificati del nodo Proxmox per la connessione sicura. Il client SPICE (virt-viewer/remote-viewer) verifica il certificato del server.

```bash
# Verificare la configurazione SPICE
# Il certificato usato da SPICE e lo stesso di pveproxy
cat /etc/pve/local/pveproxy-ssl.pem

# Esportare il certificato CA per i client SPICE
cp /etc/pve/pve-root-ca.pem /var/www/html/pve-ca.crt

# I client possono scaricarlo:
# wget https://pve-node01:8006/pve-ca.crt
```

### 7.2 Configurazione del Client SPICE

Per i client Windows:

```
1. Scaricare il certificato CA da https://pve-node01:8006
2. Doppio clic sul file .crt
3. "Installa certificato" -> "Computer locale" -> "Autorita di certificazione radice attendibili"
```

Per i client Linux:

```bash
# Importare la CA PVE nel trust store
sudo cp pve-ca.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates

# Il client SPICE (virt-viewer) utilizzera il trust store di sistema
```

Per i client macOS:

```bash
# Importare nel keychain di sistema
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain pve-ca.crt
```

### 7.3 Alternativa: noVNC

noVNC utilizza la connessione WebSocket attraverso la stessa porta HTTPS (8006) di pveproxy, quindi beneficia automaticamente di qualsiasi certificato configurato per la web GUI. Questo elimina la necessita di configurare certificati separati per le console.

---

## 8. Automazione del Rinnovo Certificati

### 8.1 Script di Rinnovo per Certificati Custom

```bash
#!/bin/bash
# renew-pve-certificates.sh
# Script per il rinnovo dei certificati da CA interna

set -euo pipefail

NODES="pve-node01 pve-node02 pve-node03"
CA_CERT="/etc/pve/priv/internal-ca/ca.pem"
CA_KEY="/etc/pve/priv/internal-ca/ca.key"
CERT_DIR="/tmp/pve-certs-renewal"
DAYS_BEFORE_EXPIRY=30
CERT_VALIDITY_DAYS=365
LOG="/var/log/pve-cert-renewal.log"

log() { echo "$(date -Is) $1" | tee -a "$LOG"; }

mkdir -p "$CERT_DIR"

for NODE in $NODES; do
    log "=== Verifica certificato per $NODE ==="

    # Ottenere la data di scadenza
    EXPIRY=$(ssh "$NODE" "openssl x509 -in /etc/pve/local/pveproxy-ssl.pem -noout -enddate 2>/dev/null" | cut -d= -f2)

    if [ -z "$EXPIRY" ]; then
        log "  AVVISO: Impossibile leggere il certificato su $NODE"
        continue
    fi

    EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
    NOW_EPOCH=$(date +%s)
    DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))

    log "  Scadenza: $EXPIRY ($DAYS_LEFT giorni rimanenti)"

    if [ "$DAYS_LEFT" -lt "$DAYS_BEFORE_EXPIRY" ]; then
        log "  RINNOVO NECESSARIO!"

        NODE_IP=$(ssh "$NODE" "hostname -I | awk '{print \$1}'")
        NODE_FQDN="${NODE}.studio-lavoro.local"

        # Generare nuova CSR
        openssl req -new -newkey rsa:4096 \
          -keyout "${CERT_DIR}/${NODE}.key" \
          -out "${CERT_DIR}/${NODE}.csr" \
          -nodes \
          -subj "/C=IT/ST=Lazio/L=Roma/O=Studio Lavoro/OU=Infrastruttura/CN=${NODE_FQDN}" \
          -addext "subjectAltName=DNS:${NODE_FQDN},DNS:${NODE},IP:${NODE_IP}" 2>/dev/null

        # Firmare il certificato
        openssl x509 -req -in "${CERT_DIR}/${NODE}.csr" \
          -CA "$CA_CERT" -CAkey "$CA_KEY" -CAcreateserial \
          -out "${CERT_DIR}/${NODE}.pem" -days "$CERT_VALIDITY_DAYS" \
          -extfile <(printf "subjectAltName=DNS:${NODE_FQDN},DNS:${NODE},IP:${NODE_IP}\nkeyUsage=digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth") 2>/dev/null

        # Creare la chain completa
        cat "${CERT_DIR}/${NODE}.pem" "$CA_CERT" > "${CERT_DIR}/${NODE}-fullchain.pem"

        # Installare il certificato
        scp "${CERT_DIR}/${NODE}-fullchain.pem" "${NODE}:/etc/pve/local/pveproxy-ssl.pem"
        scp "${CERT_DIR}/${NODE}.key" "${NODE}:/etc/pve/local/pveproxy-ssl.key"
        ssh "$NODE" "chmod 600 /etc/pve/local/pveproxy-ssl.key && systemctl restart pveproxy"

        # Verificare
        sleep 2
        VERIFY=$(ssh "$NODE" "openssl x509 -in /etc/pve/local/pveproxy-ssl.pem -noout -enddate")
        log "  Rinnovo completato. Nuova scadenza: $VERIFY"
    else
        log "  OK - Certificato valido per altri $DAYS_LEFT giorni"
    fi
done

# Cleanup file temporanei
rm -rf "$CERT_DIR"
log "=== Verifica completata ==="
```

### 8.2 Monitoraggio Scadenza Certificati

```bash
#!/bin/bash
# check-pve-cert-expiry.sh
# Script di monitoraggio per Prometheus/Nagios/Zabbix

WARN_DAYS=30
CRIT_DAYS=7

CERT="/etc/pve/local/pveproxy-ssl.pem"

if [ ! -f "$CERT" ]; then
    echo "CRITICAL: Certificato non trovato: $CERT"
    exit 2
fi

EXPIRY=$(openssl x509 -in "$CERT" -noout -enddate | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$EXPIRY" +%s)
NOW_EPOCH=$(date +%s)
DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))

if [ "$DAYS_LEFT" -lt "$CRIT_DAYS" ]; then
    echo "CRITICAL: Certificato PVE scade tra $DAYS_LEFT giorni ($EXPIRY)"
    exit 2
elif [ "$DAYS_LEFT" -lt "$WARN_DAYS" ]; then
    echo "WARNING: Certificato PVE scade tra $DAYS_LEFT giorni ($EXPIRY)"
    exit 1
else
    echo "OK: Certificato PVE valido per $DAYS_LEFT giorni ($EXPIRY)"
    exit 0
fi
```

### 8.3 Monitoraggio con Prometheus e blackbox_exporter

```yaml
# prometheus.yml - scrape config per monitoraggio certificati
scrape_configs:
  - job_name: 'blackbox-ssl'
    metrics_path: /probe
    params:
      module: [tls_connect]
    static_configs:
      - targets:
          - pve-node01.studio-lavoro.local:8006
          - pve-node02.studio-lavoro.local:8006
          - pve-node03.studio-lavoro.local:8006
          - pbs01.studio-lavoro.local:8007
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115
```

```yaml
# blackbox.yml - modulo per probe TLS
modules:
  tls_connect:
    prober: tcp
    timeout: 10s
    tcp:
      tls: true
      tls_config:
        insecure_skip_verify: false
```

```yaml
# alertmanager rules per scadenza certificati
groups:
  - name: ssl_certificate_alerts
    rules:
      - alert: SSLCertificateExpiringSoon
        expr: probe_ssl_earliest_cert_expiry - time() < 86400 * 30
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Certificato SSL in scadenza entro 30 giorni"
          description: "Il certificato su {{ $labels.instance }} scade tra {{ $value | humanizeDuration }}"

      - alert: SSLCertificateExpiringCritical
        expr: probe_ssl_earliest_cert_expiry - time() < 86400 * 7
        for: 1h
        labels:
          severity: critical
        annotations:
          summary: "CRITICO: Certificato SSL in scadenza entro 7 giorni"
          description: "Il certificato su {{ $labels.instance }} scade tra {{ $value | humanizeDuration }}. Intervento immediato richiesto."

      - alert: SSLCertificateExpired
        expr: probe_ssl_earliest_cert_expiry - time() < 0
        for: 0m
        labels:
          severity: critical
        annotations:
          summary: "CRITICO: Certificato SSL SCADUTO"
          description: "Il certificato su {{ $labels.instance }} e SCADUTO. La GUI potrebbe essere inaccessibile."
```

### 8.4 Script di Monitoraggio Multi-Nodo con Metriche

```bash
#!/bin/bash
# pve-cert-metrics.sh
# Genera metriche Prometheus per node_exporter (textfile collector)

METRICS_FILE="/var/lib/prometheus/node-exporter/pve_cert.prom"
TMPFILE=$(mktemp)

check_cert() {
    local name="$1"
    local certfile="$2"
    local port="${3:-}"

    if [ -f "$certfile" ]; then
        local expiry_epoch
        expiry_epoch=$(openssl x509 -in "$certfile" -noout -enddate 2>/dev/null | cut -d= -f2)
        if [ -n "$expiry_epoch" ]; then
            local epoch
            epoch=$(date -d "$expiry_epoch" +%s)
            echo "pve_certificate_expiry_timestamp_seconds{name=\"$name\",file=\"$certfile\"} $epoch" >> "$TMPFILE"
            local remaining=$(( epoch - $(date +%s) ))
            echo "pve_certificate_remaining_seconds{name=\"$name\",file=\"$certfile\"} $remaining" >> "$TMPFILE"
        fi
    fi
}

echo "# HELP pve_certificate_expiry_timestamp_seconds Timestamp di scadenza del certificato" > "$TMPFILE"
echo "# TYPE pve_certificate_expiry_timestamp_seconds gauge" >> "$TMPFILE"
echo "# HELP pve_certificate_remaining_seconds Secondi rimanenti prima della scadenza" >> "$TMPFILE"
echo "# TYPE pve_certificate_remaining_seconds gauge" >> "$TMPFILE"

check_cert "pveproxy" "/etc/pve/local/pveproxy-ssl.pem"
check_cert "pve-ssl" "/etc/pve/local/pve-ssl.pem"
check_cert "pve-root-ca" "/etc/pve/pve-root-ca.pem"

mv "$TMPFILE" "$METRICS_FILE"
chmod 644 "$METRICS_FILE"
```

Schedulare con cron ogni ora:

```bash
echo '0 * * * * root /usr/local/bin/pve-cert-metrics.sh' > /etc/cron.d/pve-cert-metrics
```

---

## 9. Setup di una CA Interna

### 9.1 CA con OpenSSL (Approccio Semplice)

Per ambienti che non hanno una CA esistente (es. Microsoft AD CS):

```bash
# Creare la directory per la CA
mkdir -p /etc/pve/priv/internal-ca/{certs,crl,newcerts}
cd /etc/pve/priv/internal-ca
touch index.txt
echo 1000 > serial
echo 1000 > crlnumber

# Generare la chiave della CA Root
openssl genrsa -aes256 -out ca.key 4096
chmod 600 ca.key

# Creare il certificato CA Root (validita 10 anni)
openssl req -new -x509 -days 3650 -key ca.key -sha256 -out ca.pem \
  -subj "/C=IT/ST=Lazio/L=Roma/O=Studio Lavoro/OU=IT Security/CN=Studio Lavoro Internal CA"

# Creare la configurazione OpenSSL per la CA
cat > openssl-ca.cnf << 'EOF'
[ca]
default_ca = CA_default

[CA_default]
dir               = /etc/pve/priv/internal-ca
certs             = $dir/certs
crl_dir           = $dir/crl
new_certs_dir     = $dir/newcerts
database          = $dir/index.txt
serial            = $dir/serial
crlnumber         = $dir/crlnumber
crl               = $dir/crl/ca.crl.pem
certificate       = $dir/ca.pem
private_key       = $dir/ca.key
default_days      = 365
default_crl_days  = 30
default_md        = sha256
preserve          = no
policy            = policy_loose
copy_extensions   = copy

[policy_loose]
countryName             = optional
stateOrProvinceName     = optional
localityName            = optional
organizationName        = optional
organizationalUnitName  = optional
commonName              = supplied
emailAddress            = optional

[server_cert]
basicConstraints = CA:FALSE
nsSertType = server
nsComment = "Cert emesso dalla CA interna Studio Lavoro"
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid,issuer:always
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
authorityInfoAccess = OCSP;URI:http://ocsp.studio-lavoro.local
crlDistributionPoints = URI:http://crl.studio-lavoro.local/ca.crl.pem
EOF

# Script per firmare certificati per i nodi
cat > sign-node-cert.sh << 'SIGNEOF'
#!/bin/bash
set -euo pipefail
NODE=$1
IP=$2

if [ -z "$NODE" ] || [ -z "$IP" ]; then
    echo "Uso: $0 <hostname> <ip>"
    exit 1
fi

FQDN="${NODE}.studio-lavoro.local"
CA_DIR="/etc/pve/priv/internal-ca"

# Generare chiave e CSR
openssl req -new -newkey rsa:4096 -keyout "${CA_DIR}/certs/${NODE}.key" -out "${CA_DIR}/certs/${NODE}.csr" -nodes \
  -subj "/C=IT/ST=Lazio/L=Roma/O=Studio Lavoro/OU=Infrastruttura/CN=${FQDN}"

# Creare l'estensione SAN
cat > "${CA_DIR}/certs/${NODE}.ext" << EXTEOF
basicConstraints = CA:FALSE
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = DNS:${FQDN},DNS:${NODE},IP:${IP}
authorityInfoAccess = OCSP;URI:http://ocsp.studio-lavoro.local
crlDistributionPoints = URI:http://crl.studio-lavoro.local/ca.crl.pem
EXTEOF

# Firmare il certificato
openssl x509 -req -in "${CA_DIR}/certs/${NODE}.csr" \
  -CA "${CA_DIR}/ca.pem" -CAkey "${CA_DIR}/ca.key" -CAcreateserial \
  -out "${CA_DIR}/certs/${NODE}.pem" -days 365 \
  -extfile "${CA_DIR}/certs/${NODE}.ext"

echo "Certificato generato: ${CA_DIR}/certs/${NODE}.pem"
echo "Chiave privata: ${CA_DIR}/certs/${NODE}.key"
echo "Scadenza: $(openssl x509 -in ${CA_DIR}/certs/${NODE}.pem -noout -enddate)"
SIGNEOF

chmod +x sign-node-cert.sh
```

### 9.2 Gestione CRL (Certificate Revocation List)

```bash
# Generare la CRL iniziale
openssl ca -config openssl-ca.cnf -gencrl -out crl/ca.crl.pem

# Revocare un certificato (es. nodo decommissionato)
openssl ca -config openssl-ca.cnf -revoke certs/pve-node04.pem

# Rigenerare la CRL dopo la revoca
openssl ca -config openssl-ca.cnf -gencrl -out crl/ca.crl.pem

# Verificare la CRL
openssl crl -in crl/ca.crl.pem -noout -text | head -20

# Distribuire la CRL (via web server)
cp crl/ca.crl.pem /var/www/html/ca.crl.pem

# Schedulare rigenerazione CRL periodica
cat > /etc/cron.d/pve-ca-crl << 'EOF'
0 0 * * 0 root cd /etc/pve/priv/internal-ca && openssl ca -config openssl-ca.cnf -gencrl -out crl/ca.crl.pem && cp crl/ca.crl.pem /var/www/html/ca.crl.pem 2>&1 | logger -t pve-ca-crl
EOF
```

### 9.3 CA con step-ca (Approccio Moderno)

Per una soluzione piu completa e con supporto ACME interno:

```bash
# Installare step CLI e step-ca
wget https://dl.smallstep.com/cli/docs-cli-install/latest/step-cli_amd64.deb
wget https://dl.smallstep.com/certificates/docs-ca-install/latest/step-ca_amd64.deb
dpkg -i step-cli_amd64.deb step-ca_amd64.deb

# Inizializzare la CA
step ca init \
  --name "Studio Lavoro Internal CA" \
  --dns "ca.studio-lavoro.local" \
  --address ":8443" \
  --provisioner "admin@studio-lavoro.local" \
  --deployment-type standalone

# Abilitare il provisioner ACME
step ca provisioner add acme --type ACME

# Configurare la durata dei certificati
step ca provisioner update acme --x509-min-dur 24h --x509-max-dur 8760h --x509-default-dur 720h

# Creare il servizio systemd
cat > /etc/systemd/system/step-ca.service << 'EOF'
[Unit]
Description=step-ca - Smallstep Certificate Authority
After=network-online.target
Wants=network-online.target

[Service]
User=step
Group=step
ExecStart=/usr/bin/step-ca /etc/step-ca/config/ca.json --password-file /etc/step-ca/password.txt
Restart=on-failure
RestartSec=10
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now step-ca

# Ora i nodi Proxmox possono usare questa CA come server ACME
# Configurare in Proxmox:
pvenode acme account register internal-ca admin@studio-lavoro.local \
  --directory https://ca.studio-lavoro.local:8443/acme/acme/directory

# Importare il root cert della step-ca nel trust store
step ca root > /usr/local/share/ca-certificates/step-ca-root.crt
update-ca-certificates

# Richiedere certificati
pvenode config set --acme "account=internal-ca"
pvenode config set --acmedomain0 "domain=pve-node01.studio-lavoro.local"
pvenode acme cert order
```

### 9.4 Integrazione con HashiCorp Vault PKI

```bash
# Configurare il secrets engine PKI in Vault
vault secrets enable pki
vault secrets tune -max-lease-ttl=87600h pki

# Generare il certificato root
vault write pki/root/generate/internal \
  common_name="Studio Lavoro Root CA" \
  ttl=87600h

# Configurare gli URL per CRL e OCSP
vault write pki/config/urls \
  issuing_certificates="https://vault.studio-lavoro.local:8200/v1/pki/ca" \
  crl_distribution_points="https://vault.studio-lavoro.local:8200/v1/pki/crl" \
  ocsp_servers="https://vault.studio-lavoro.local:8200/v1/pki/ocsp"

# Creare un ruolo per i certificati Proxmox
vault write pki/roles/proxmox-nodes \
  allowed_domains="studio-lavoro.local" \
  allow_subdomains=true \
  max_ttl=8760h \
  key_type=rsa \
  key_bits=4096 \
  require_cn=false \
  allow_ip_sans=true

# Richiedere un certificato
vault write -format=json pki/issue/proxmox-nodes \
  common_name="pve-node01.studio-lavoro.local" \
  alt_names="pve-node01" \
  ip_sans="10.10.1.10" \
  ttl=8760h | tee /tmp/vault-cert.json

# Estrarre cert e key dal JSON
jq -r '.data.certificate' /tmp/vault-cert.json > /tmp/pve-node01.pem
jq -r '.data.private_key' /tmp/vault-cert.json > /tmp/pve-node01.key
jq -r '.data.issuing_ca' /tmp/vault-cert.json >> /tmp/pve-node01.pem  # append chain

# Installare su Proxmox
cp /tmp/pve-node01.pem /etc/pve/local/pveproxy-ssl.pem
cp /tmp/pve-node01.key /etc/pve/local/pveproxy-ssl.key
chmod 600 /etc/pve/local/pveproxy-ssl.key
systemctl restart pveproxy

# Cleanup
rm -f /tmp/vault-cert.json /tmp/pve-node01.pem /tmp/pve-node01.key
```

---

## 10. OCSP Stapling

### 10.1 Concetto e Benefici

OCSP (Online Certificate Status Protocol) permette al client di verificare se un certificato e stato revocato. OCSP stapling elimina la necessita che il client contatti direttamente l'OCSP responder: il server include ("staple") la risposta OCSP firmata nella TLS handshake.

```
Senza OCSP Stapling:
  Client --> Server (cert) --> Client --> OCSP Responder --> Client (verifica revoca)
  Problema: privacy (l'OCSP responder vede quali siti visita il client), latenza

Con OCSP Stapling:
  Server --> OCSP Responder (periodicamente) --> Server (cache risposta)
  Client --> Server (cert + OCSP response stapled) --> Client (verifica locale)
  Beneficio: privacy, velocita
```

### 10.2 Verificare se OCSP Stapling e Attivo

```bash
# Verificare OCSP stapling con openssl
openssl s_client -connect pve-node01.studio-lavoro.com:8006 -status </dev/null 2>&1 | grep -A5 "OCSP Response"

# Se l'output dice "OCSP Response: no response sent", stapling non e attivo
# Se dice "OCSP Response Status: successful", stapling e attivo

# Verificare l'OCSP responder dal certificato
openssl x509 -in /etc/pve/local/pveproxy-ssl.pem -noout -ocsp_uri
```

### 10.3 Configurare OCSP Stapling con Reverse Proxy

Proxmox pveproxy non supporta OCSP stapling nativamente. Per abilitarlo, usare un reverse proxy nginx:

```nginx
# /etc/nginx/sites-available/proxmox-proxy
upstream proxmox_backend {
    server 127.0.0.1:8006;
}

server {
    listen 443 ssl http2;
    server_name pve-node01.studio-lavoro.com;

    ssl_certificate     /etc/pve/local/pveproxy-ssl.pem;
    ssl_certificate_key /etc/pve/local/pveproxy-ssl.key;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    ssl_trusted_certificate /path/to/ca-chain.pem;
    resolver 10.0.1.10 10.0.1.11 valid=300s;
    resolver_timeout 5s;

    location / {
        proxy_pass https://proxmox_backend;
        proxy_ssl_verify off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (per noVNC/xterm.js)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 11. HSTS (HTTP Strict Transport Security)

### 11.1 Perche HSTS e Importante

HSTS istruisce il browser a usare sempre HTTPS per un dato dominio, prevenendo attacchi SSL stripping (es. sslstrip). Senza HSTS, un attaccante MITM puo downgrade la connessione a HTTP.

Proxmox pveproxy NON supporta l'header HSTS nativamente. Per abilitarlo, ci sono due opzioni:

### 11.2 Opzione 1: Reverse Proxy con nginx

```nginx
# Aggiungere nella configurazione nginx precedente:
server {
    listen 443 ssl http2;
    server_name pve-node01.studio-lavoro.com;

    # ... (SSL config come sopra) ...

    # HSTS - max-age 1 anno, include subdomains
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Header di sicurezza aggiuntivi
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:;" always;

    # Redirect HTTP -> HTTPS
    location / {
        proxy_pass https://proxmox_backend;
        # ... (proxy config come sopra) ...
    }
}

# Redirect HTTP a HTTPS
server {
    listen 80;
    server_name pve-node01.studio-lavoro.com;
    return 301 https://$host$request_uri;
}
```

### 11.3 Opzione 2: HAProxy per HSTS

```
# /etc/haproxy/haproxy.cfg
frontend ft_proxmox
    bind *:443 ssl crt /etc/haproxy/certs/pve-combined.pem alpn h2,http/1.1
    mode http

    # HSTS
    http-response set-header Strict-Transport-Security "max-age=31536000; includeSubDomains"

    # Security headers
    http-response set-header X-Content-Type-Options "nosniff"
    http-response set-header X-Frame-Options "SAMEORIGIN"

    default_backend bk_proxmox

backend bk_proxmox
    mode http
    server pve1 127.0.0.1:8006 ssl verify none

frontend ft_redirect
    bind *:80
    mode http
    redirect scheme https code 301
```

---

## 12. Hardening TLS e Selezione Cipher Suite

### 12.1 Configurazione Cipher Suite per pveproxy

```bash
# Configurare cifrature sicure per pveproxy
cat > /etc/default/pveproxy << 'EOF'
# TLS minimum version (1.2)
# Proxmox 8.x supporta TLS 1.2 e 1.3 per default

# Cifrature TLS 1.2 consentite (ordinate per preferenza)
CIPHERS="ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256"

# Cifrature TLS 1.3 (configurate separatamente)
CIPHERSUITES="TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256"

# Preferire le cifrature del server
HONOR_CIPHER_ORDER=1

# Parametri DH personalizzati
DHPARAMS="/etc/pve/local/dhparams.pem"
EOF

# Generare parametri DH (4096 bit, richiede tempo)
openssl dhparam -out /etc/pve/local/dhparams.pem 4096

# Riavviare pveproxy
systemctl restart pveproxy
```

### 12.2 Cipher Suite per Conformita

| Standard | Cipher Suite Richieste | Note |
|----------|----------------------|------|
| PCI-DSS 3.2+ | TLS 1.2+ con AEAD (AES-GCM, ChaCha20) | No TLS 1.0/1.1, no RC4, no 3DES |
| NIST SP 800-52r2 | TLS 1.2+ con ECDHE + AES-GCM | Forward secrecy obbligatorio |
| FIPS 140-2 | AES-128/256-GCM con SHA-256/384 | No ChaCha20 (non FIPS) |
| BSI TR-02102-2 | TLS 1.2+ con ECDHE, RSA >= 2048 | Standard tedesco, simile a NIST |

### 12.3 Verifica della Configurazione TLS con testssl.sh

```bash
# Installare testssl.sh
git clone --depth 1 https://github.com/drwetter/testssl.sh.git /opt/testssl

# Eseguire un audit completo
/opt/testssl/testssl.sh --wide --color 3 https://pve-node01:8006

# Eseguire solo specifici test
/opt/testssl/testssl.sh --protocols https://pve-node01:8006       # Versioni TLS
/opt/testssl/testssl.sh --ciphers https://pve-node01:8006         # Cipher suite
/opt/testssl/testssl.sh --headers https://pve-node01:8006         # Security headers
/opt/testssl/testssl.sh --vulnerabilities https://pve-node01:8006 # DROWN, BEAST, POODLE, etc.
/opt/testssl/testssl.sh --starttls ldap ldaps://dc01:636          # Test LDAPS

# Output JSON per automazione
/opt/testssl/testssl.sh --jsonfile /tmp/testssl-results.json https://pve-node01:8006

# Interpretazione output chiave:
# "OK" = conforme
# "WARN" = potenziale problema, valutare
# "NOT ok" / "VULNERABLE" = da correggere immediatamente
```

**Cosa cercare nell'output di testssl.sh:**

| Check | Atteso | Se Fallisce |
|-------|--------|-------------|
| SSLv2 | `not offered` | Disabilitare immediatamente |
| SSLv3 | `not offered` | Disabilitare immediatamente |
| TLS 1.0 | `not offered` | Disabilitare (PCI-DSS 3.2+) |
| TLS 1.1 | `not offered` | Disabilitare (PCI-DSS 3.2+) |
| TLS 1.2 | `offered` | OK |
| TLS 1.3 | `offered` | OK, ma non strettamente richiesto |
| BEAST | `not vulnerable` | Mitigazione tramite cipher order |
| POODLE | `not vulnerable` | Disabilitare SSLv3 |
| Heartbleed | `not vulnerable` | Aggiornare OpenSSL |
| CCS | `not vulnerable` | Aggiornare OpenSSL |
| ROBOT | `not vulnerable` | Disabilitare RSA key exchange |
| Forward Secrecy | `offered` | Usare ECDHE cipher suites |

### 12.4 Verifica con openssl e nmap

```bash
# Testare le cifrature supportate con nmap
nmap --script ssl-enum-ciphers -p 8006 localhost

# Testare TLS 1.2
openssl s_client -connect localhost:8006 -tls1_2 </dev/null 2>&1 | head -5

# Testare TLS 1.3
openssl s_client -connect localhost:8006 -tls1_3 </dev/null 2>&1 | head -5

# Verificare che TLS 1.0 e 1.1 siano disabilitati
openssl s_client -connect localhost:8006 -tls1 </dev/null 2>&1 | grep -i "protocol"
# Atteso: errore o "no protocols available"

openssl s_client -connect localhost:8006 -tls1_1 </dev/null 2>&1 | grep -i "protocol"
# Atteso: errore o "no protocols available"

# Verificare la cipher suite negoziata
openssl s_client -connect localhost:8006 </dev/null 2>&1 | grep "Cipher is"

# Verificare il certificato completo
openssl s_client -connect localhost:8006 -showcerts </dev/null 2>&1

# Verificare la catena di certificazione
openssl s_client -connect localhost:8006 -CApath /etc/ssl/certs/ </dev/null 2>&1 | grep "Verify return code"
```

### 12.5 Tabella Conformita TLS

| Requisito | Standard | Configurazione |
|-----------|----------|---------------|
| TLS 1.2 minimo | PCI-DSS, NIST | Default in Proxmox 8.x |
| TLS 1.3 supportato | Best practice | Supportato nativamente |
| No TLS 1.0/1.1 | PCI-DSS 3.2+ | Disabilitato per default |
| No SSLv3 | Tutti | Disabilitato per default |
| Forward Secrecy | NIST, Best practice | ECDHE cipher suites |
| Chiavi >= 2048 bit | PCI-DSS, NIST | RSA 4096 consigliato |
| SHA-256+ per firma | Tutti | Default per nuovi certificati |
| HSTS | OWASP | Richiede reverse proxy (vedi sezione 11) |
| OCSP Stapling | Best practice | Richiede reverse proxy (vedi sezione 10) |

---

## 13. SSL Pinning per Client API

### 13.1 Concetto di Certificate Pinning

SSL/TLS pinning vincola un client a fidarsi solo di uno specifico certificato (o chiave pubblica), ignorando il trust store di sistema. Utile per script di automazione e API client che devono comunicare solo con un server specifico.

### 13.2 Pinning con curl

```bash
# Estrarre il fingerprint SHA-256 del certificato
openssl s_client -connect pve-node01:8006 </dev/null 2>/dev/null | \
  openssl x509 -outform DER | openssl dgst -sha256 -binary | base64

# Usare curl con pinnig
curl --pinnedpubkey "sha256//YhKJG5...=" \
  https://pve-node01.studio-lavoro.local:8006/api2/json/version

# Alternativa: pinning basato su file certificato
curl --cacert /path/to/pve-ca.pem \
  https://pve-node01.studio-lavoro.local:8006/api2/json/version
```

### 13.3 Pinning in Script Python

```python
import requests
import hashlib
import ssl

# Pinning basato su fingerprint
PVE_CERT_FINGERPRINT = "ab:cd:ef:12:34:56:78:90:..."
PVE_API_URL = "https://pve-node01.studio-lavoro.local:8006/api2/json"

# Opzione 1: CA file specifico
session = requests.Session()
session.verify = "/path/to/pve-ca.pem"
response = session.get(f"{PVE_API_URL}/version")

# Opzione 2: Verifica fingerprint post-connessione
import urllib3
conn = urllib3.HTTPSConnectionPool(
    "pve-node01.studio-lavoro.local",
    port=8006,
    cert_reqs="CERT_REQUIRED",
    ca_certs="/path/to/pve-ca.pem",
    assert_fingerprint=PVE_CERT_FINGERPRINT
)
```

---

## 14. Troubleshooting Certificati

### 14.1 Problemi Comuni e Soluzioni

| Problema | Sintomo | Causa | Soluzione |
|----------|---------|-------|-----------|
| Certificato scaduto | Browser mostra `NET::ERR_CERT_DATE_INVALID` | Rinnovo non eseguito | `pvenode acme cert renew` o rinnovo manuale |
| CA non trusted | Browser mostra `NET::ERR_CERT_AUTHORITY_INVALID` | CA non importata nel trust store | `update-ca-certificates` |
| SAN mismatch | Browser mostra `NET::ERR_CERT_COMMON_NAME_INVALID` | CN/SAN non corrisponde all'hostname | Rigenerare con SAN corretti |
| Chain incompleta | Alcuni client funzionano, altri no | Intermediate CA mancante nel file PEM | `cat server.pem intermediate.pem > fullchain.pem` |
| Chiave privata non corrispondente | pveproxy non si avvia | Key e cert non sono una coppia | Verificare con `openssl x509 -noout -modulus -in cert.pem | md5sum` |
| Permessi file errati | pveproxy non legge il cert | Permission troppo aperte o restrittive | `chmod 600` per key, `chmod 644` per cert |
| ACME challenge fallisce | `pvenode acme cert order` errore | Porta 80 bloccata o DNS non risolvibile | Verificare firewall e DNS |
| Rinnovo ACME fallisce silentemente | Certificato scade senza avviso | Timer systemd non attivo | `systemctl enable pve-daily-update.timer` |

### 14.2 Comandi Diagnostici Essenziali

```bash
# === Verifica certificato locale ===
# Mostrare tutte le info del certificato
openssl x509 -in /etc/pve/local/pveproxy-ssl.pem -noout -text

# Solo le date
openssl x509 -in /etc/pve/local/pveproxy-ssl.pem -noout -dates

# Solo il subject e il SAN
openssl x509 -in /etc/pve/local/pveproxy-ssl.pem -noout -subject -ext subjectAltName

# Verificare che key e cert corrispondano
diff <(openssl x509 -noout -modulus -in /etc/pve/local/pveproxy-ssl.pem | md5sum) \
     <(openssl rsa -noout -modulus -in /etc/pve/local/pveproxy-ssl.key | md5sum)
# Se l'output e identico, key e cert corrispondono

# === Verifica connessione remota ===
openssl s_client -connect pve-node01.studio-lavoro.local:8006 -servername pve-node01.studio-lavoro.local </dev/null 2>&1

# Verificare la catena completa
openssl s_client -connect pve-node01.studio-lavoro.local:8006 -showcerts </dev/null 2>&1

# === Verifica ACME ===
pvenode acme account list
pvenode acme cert info
journalctl -u pve-daily-update --since "7 days ago" | grep -i acme

# === Verifica servizio ===
systemctl status pveproxy
journalctl -u pveproxy --since "1 hour ago" | grep -iE "(ssl|cert|tls|error)"
```

### 14.3 Ripristino da Certificato Corrotto

```bash
# Se il certificato custom e corrotto e la GUI non e accessibile:

# 1. Accedere via SSH (il cert custom non influisce su SSH)
ssh root@pve-node01

# 2. Rimuovere il certificato custom (tornare al self-signed)
rm /etc/pve/local/pveproxy-ssl.pem
rm /etc/pve/local/pveproxy-ssl.key

# 3. Riavviare pveproxy (usera il cert cluster pve-ssl.pem)
systemctl restart pveproxy

# 4. La GUI e ora accessibile (con avviso self-signed del browser)

# 5. Rigenerare e installare il certificato corretto
pvenode acme cert order  # se ACME era configurato
# oppure installare un nuovo certificato custom
```

---

## 15. Checklist Certificati

### Checklist per l'Implementazione

| # | Attivita | Priorita | Stato |
|---|---------|----------|-------|
| 1 | Decidere la strategia certificati (ACME, CA interna, custom) | Alta | [ ] |
| 2 | Se ACME: registrare l'account e configurare il plugin DNS | Alta | [ ] |
| 3 | Se CA interna: installare la CA e distribuire il certificato root | Alta | [ ] |
| 4 | Generare e installare i certificati per ogni nodo PVE | Alta | [ ] |
| 5 | Configurare i certificati per PBS (se presente) | Alta | [ ] |
| 6 | Verificare la catena di certificazione su ogni nodo | Alta | [ ] |
| 7 | Testare l'accesso alla GUI senza avvisi del browser | Media | [ ] |
| 8 | Testare la console SPICE con i nuovi certificati | Media | [ ] |
| 9 | Testare le chiamate API con i nuovi certificati | Media | [ ] |
| 10 | Configurare il rinnovo automatico | Alta | [ ] |
| 11 | Configurare il monitoraggio della scadenza (Prometheus/alert) | Alta | [ ] |
| 12 | Hardening TLS (cifrature, DH parameters) | Media | [ ] |
| 13 | Configurare HSTS tramite reverse proxy | Media | [ ] |
| 14 | Configurare OCSP stapling (se reverse proxy) | Bassa | [ ] |
| 15 | Audit con testssl.sh | Alta | [ ] |
| 16 | Documentare la procedura di rinnovo e di emergenza | Media | [ ] |
| 17 | Testare WebAuthn/FIDO2 con i nuovi certificati | Bassa | [ ] |
| 18 | Verificare la comunicazione mTLS inter-nodo nel cluster | Alta | [ ] |
| 19 | Configurare SSL pinning per script API critici | Bassa | [ ] |
| 20 | Implementare monitoraggio CRL/OCSP per CA interna | Media | [ ] |

### Confronto con VMware vCenter

| Aspetto | VMware vCenter | Proxmox VE |
|---------|---------------|------------|
| Gestione certificati | Certificate Manager (complesso) | CLI/GUI (semplice) |
| ACME/Let's Encrypt | Non supportato nativamente | Supportato nativamente |
| Self-signed default | Si | Si |
| Custom CA | Si (complesso) | Si (semplice) |
| Rinnovo automatico | Limitato | Completo (ACME) |
| Impatto rinnovo | Possibile downtime servizi | Riavvio pveproxy (secondi) |
| Certificati per componenti | Separati per ogni servizio (molti) | Unificati per nodo |
| Certificate Store | VECS (VMware Endpoint Certificate Store) | Filesystem standard |
| mTLS cluster | Si (VMCA interna) | Si (pve-root-ca.pem) |
| OCSP Stapling | Configurabile | Richiede reverse proxy |
| HSTS | Configurabile | Richiede reverse proxy |
| Cipher suite config | Tramite vSphere Client | File `/etc/default/pveproxy` |
| Monitoraggio scadenza | vCenter alarm | Custom (Prometheus/script) |

---

## Conclusione

La gestione dei certificati in Proxmox VE e significativamente piu semplice e flessibile rispetto a VMware vCenter. L'integrazione nativa con ACME (Let's Encrypt) e il supporto per plugin DNS eliminano la necessita di soluzioni complesse per il rinnovo automatico. Per ambienti interni, la possibilita di utilizzare una CA interna con step-ca o HashiCorp Vault PKI offre un'alternativa enterprise-grade.

La priorita durante la migrazione da VMware dovrebbe essere la sostituzione dei certificati self-signed con certificati validi (ACME o CA interna), per garantire la sicurezza delle comunicazioni e il corretto funzionamento di funzionalita come WebAuthn e la console SPICE.

Per ambienti con requisiti di compliance (PCI-DSS, NIST), e fondamentale complementare la configurazione di base con: hardening delle cipher suite, implementazione di HSTS tramite reverse proxy, OCSP stapling, e monitoraggio automatico della scadenza con alerting. Il mTLS cluster, gestito automaticamente da Proxmox tramite la CA interna, garantisce la sicurezza della comunicazione inter-nodo senza configurazione aggiuntiva.

---

## Approfondimenti — note del 2026-05-22

> **Approfondimento — Let's Encrypt rate limits.** Importante: Let's Encrypt ha rate limits per evitare abuso: 50 cert/registrazione account/settimana, 5 cert duplicati per FQDN/settimana, 300 nuovi orders/account/3 ore. Per cluster grandi (es. 50 nodi Proxmox), considerare: (a) un singolo wildcard cert `*.cluster.example.com` invece di 50 cert separati; (b) usare staging environment di Let's Encrypt durante test (no rate limit, ma cert non trusted); (c) per produzione, monitorare uso vs limit. Fonte: [Let's Encrypt — Rate Limits](https://letsencrypt.org/docs/rate-limits/), retrieved 2026-05-22.

> **Approfondimento — DNS-01 con plugin Cloudflare/Route53/DigitalOcean.** Proxmox supporta plugin per provider DNS principali. Setup tipico (Cloudflare): (1) creare API token Cloudflare con permessi `Zone:DNS:Edit` solo per il dominio target; (2) `pvenode acme plugin add dns cf --data API_Token=<token> --validation-delay 60`; (3) `pvenode config set --acme domains=*.cluster.example.com`; (4) `pvenode acme cert order`. Il plugin gestisce automaticamente l'aggiunta/rimozione del TXT record `_acme-challenge.cluster.example.com`. Validation-delay di 60s e il tempo di propagazione DNS tipico; aumentare a 120-300 per provider DNS lenti. Fonte: [Proxmox VE — ACME DNS Plugin](https://pve.proxmox.com/wiki/Certificate_Management#sysadmin_certs_acme), retrieved 2026-05-22.

> **Approfondimento — HSTS preload list.** Per protezione massima contro SSL stripping, un dominio puo essere incluso nella HSTS preload list dei browser (hstspreload.org). Requisiti: (1) cert valido (non self-signed); (2) redirect HTTP -> HTTPS; (3) header HSTS con `max-age >= 31536000; includeSubDomains; preload`. Attenzione: una volta nella preload list, il dominio non puo tornare indietro facilmente (mesi di attesa per la rimozione). Non appropriato per ambienti di lab o staging; consigliato solo per infrastrutture permanenti con FQDN pubblico stabile.

> **Approfondimento — pveproxy e curve ECDHE.** Proxmox 8.x usa OpenSSL 3.x che supporta le curve ECDHE P-256, P-384, P-521 e X25519. La curva predefinita e X25519 per TLS 1.3 e P-256 per TLS 1.2. Per ambienti FIPS, usare solo P-256 e P-384 (X25519 non e FIPS-approved). La configurazione avviene in `/etc/default/pveproxy` con il parametro `CURVES`.

---

## Esercizi

1. **Concettuale — scegli il flow ACME.** Per ognuno: HTTP-01 o DNS-01? (a) Proxmox single-node con IP pubblico; (b) Proxmox cluster 5 nodi dietro firewall, no port 80 esposto; (c) cluster con dominio non gestito da DNS provider con API; (d) ambiente air-gapped no Internet. *Risposte:* (a) HTTP-01; (b) DNS-01; (c) CA interna con step-ca; (d) CA interna.

2. **Lab — ACME + DNS-01 con wildcard.** (a) Configurare un dominio test su Cloudflare; (b) creare API token con permessi minimi; (c) ottenere wildcard cert `*.lab.example.com` per Proxmox; (d) verificare con `openssl s_client` e browser; (e) testare il rinnovo simulato (forzare order anche se non scaduto); (f) verificare con `testssl.sh`.

3. **Lab — mTLS cluster audit.** (a) Verificare la CA cluster `pve-root-ca.pem`; (b) verificare che ogni nodo abbia un cert firmato dalla CA cluster; (c) verificare la connessione mTLS tra nodi con `openssl s_client`; (d) documentare la catena di fiducia. Domanda bonus: cosa succede se la CA cluster viene compromessa?

4. **Lab — HSTS con reverse proxy.** (a) Installare nginx su un nodo; (b) configurare come reverse proxy per pveproxy; (c) abilitare HSTS; (d) verificare con `curl -I` che l'header sia presente; (e) testare con testssl.sh che HSTS venga riportato.

5. **Lab — monitoraggio certificati.** (a) Configurare blackbox_exporter per monitorare i certificati di tutti i nodi; (b) creare le regole Prometheus per alert a 30/7/1 giorni; (c) testare l'alert con un certificato con scadenza prossima; (d) configurare notifica via webhook o email.

6. **Stretch — step-ca interno + ACME interno.** Deploy step-ca su una VM Linux; configurare Proxmox per usare step-ca come ACME server (compatibile RFC 8555); emettere cert per il cluster; configurare CRL e OCSP responder. Documentare il processo end-to-end.

7. **Stretch — audit completo PCI-DSS.** Eseguire un audit TLS completo con `testssl.sh`, documentare ogni finding in formato: controllo, stato, raccomandazione. Produrre un report di compliance per PCI-DSS 3.2+ con evidenze.

## Auto-valutazione

1. Differenza fra HTTP-01 e DNS-01 ACME challenge.
2. Quale challenge serve per wildcard cert?
3. Cosa fa `pvenode acme cert order`?
4. Dove Proxmox memorizza i file dei certificati? (paths completi)
5. Differenza tra `pveproxy-ssl.pem` e `pve-ssl.pem` — quale ha la priorita per la web GUI?
6. OCSP stapling: cosa fa e perche e raccomandato?
7. Let's Encrypt rate limit per dominio: quanti nuovi cert/settimana?
8. step-ca vs OpenSSL CA manuale: principali vantaggi.
9. Come si verifica che key e cert corrispondano? (comando)
10. Cos'e HSTS e perche pveproxy non lo supporta nativamente?
11. Cosa succede se la CA cluster (`pve-root-ca.pem`) viene compromessa?
12. Come si monitora la scadenza dei certificati con Prometheus?
13. Cos'e mTLS e come lo usa Proxmox per la comunicazione cluster?
14. Quale comando testssl.sh rileva vulnerabilita come Heartbleed, BEAST, POODLE?
15. Differenza tra TLS 1.2 e TLS 1.3 in termini di handshake e forward secrecy.

## Letture primarie consigliate

- Proxmox VE Wiki — Certificate Management. https://pve.proxmox.com/wiki/Certificate_Management (retrieved 2026-05-22).
- RFC 8555 — Automatic Certificate Management Environment (ACME). https://datatracker.ietf.org/doc/html/rfc8555 (retrieved 2026-05-22).
- Let's Encrypt — Documentation. https://letsencrypt.org/docs/ (retrieved 2026-05-22).
- step-ca — Documentation. https://smallstep.com/docs/step-ca/ (retrieved 2026-05-22).
- HashiCorp Vault — PKI Secrets Engine. https://developer.hashicorp.com/vault/docs/secrets/pki (retrieved 2026-05-22).
- testssl.sh — TLS audit tool. https://testssl.sh/ (retrieved 2026-05-22).
- NIST SP 800-52 Rev. 2 — Guidelines for TLS Implementations. https://csrc.nist.gov/publications/detail/sp/800-52/rev-2/final (retrieved 2026-05-22).
- Mozilla SSL Configuration Generator. https://ssl-config.mozilla.org/ (retrieved 2026-05-22).
- OWASP — Transport Layer Security Cheat Sheet. https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html (retrieved 2026-05-22).

## Collegamenti incrociati

- Modulo 12.2 — `autenticazione-ldap-ad-proxmox.md`: LDAPS/LDAP with TLS dipende da cert validi.
- Modulo 12.3 — `sicurezza-compliance.md`: cert come parte della compliance baseline.
- Modulo 14.2 — `../14-AUTOMAZIONE-E-INFRASTRUCTURE-AS-CODE/proxmox-api-automazione-script.md`: API con SSL pinning.

## Glossario locale

| Termine | Definizione |
|---|---|
| **ACME** | Automatic Certificate Management Environment (RFC 8555). |
| **Let's Encrypt** | CA gratuita pubblica che usa ACME. |
| **HTTP-01 challenge** | Validazione: server espone file su porta 80. |
| **DNS-01 challenge** | Validazione: TXT record DNS aggiunto. |
| **TLS-ALPN-01** | Validazione via ALPN extension TLS (raro). |
| **CA interna** | Certificate Authority ospitata internamente. |
| **step-ca** | Open-source CA con supporto ACME. |
| **OCSP** | Online Certificate Status Protocol; verifica revoca cert. |
| **OCSP stapling** | Server presenta proof di non-revoca con cert. |
| **CRL** | Certificate Revocation List; lista cert revocati. |
| **SAN (Subject Alternative Name)** | Estensione X.509 con FQDN multipli. |
| **Wildcard cert** | Cert valido per `*.example.com`. |
| **HSTS** | HTTP Strict Transport Security; force HTTPS. |
| **`testssl.sh`** | Tool per audit configurazione TLS server. |
| **mTLS** | Mutual TLS; autenticazione bidirezionale client-server. |
| **Forward Secrecy** | Proprieta per cui la compromissione della chiave privata non compromette sessioni passate. |
| **ECDHE** | Elliptic Curve Diffie-Hellman Ephemeral; key exchange con forward secrecy. |
| **AEAD** | Authenticated Encryption with Associated Data (es. AES-GCM). |
| **pve-root-ca.pem** | CA root del cluster Proxmox, firma i cert di ogni nodo. |
| **pveproxy** | Servizio Proxmox che serve la web GUI e le API su porta 8006. |
| **SSL pinning** | Vincolo del client a fidarsi solo di un certificato specifico. |
| **blackbox_exporter** | Componente Prometheus per probe esterne (HTTP, TCP, DNS, ICMP). |
| **DH parameters** | Parametri Diffie-Hellman per key exchange; generati con `openssl dhparam`. |
| **FIPS 140-2** | Standard di sicurezza per moduli crittografici (US federal). |
| **PCI-DSS** | Payment Card Industry Data Security Standard. |
