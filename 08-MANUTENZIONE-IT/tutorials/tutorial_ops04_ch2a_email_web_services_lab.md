# Tutorial: Servizi Email e Web Server — Manutenzione e Sicurezza — Hands-On Lab

> **Documento di riferimento:** `04-servizi-infrastruttura.md` (sezioni Manutenzione Email e Web Server)
> **Dominio:** Infrastruttura di Rete — Servizi Applicativi
> **Ambito:** Email security (SPF/DKIM/DMARC), SMTP testing, Nginx su Linux, IIS su Windows, monitoraggio applicazioni web, certificati SSL, log rotation
> **Durata lab:** 4-5 ore
> **Livello:** Intermedio — richiede ops04a (DNS/DHCP/NTP), ops03b (Linux Server)
> **Prerequisiti:** SRV-LINUX-01 operativo con Nginx (installato con GLPI), DC-LAB-01 con IIS (opzionale), WKS-LAB-01 per test client
> **Ambiente:** SRV-LINUX-01 (Nginx, email testing), DC-LAB-01 (IIS), WKS-LAB-01 (browser test)
> **Nota lab:** Il tutorial usa Nginx su SRV-LINUX-01 (già presente con GLPI) e SMTP con Postfix. Non è richiesto un server Exchange reale.

---

## Lab Environment Setup

```bash
# Su SRV-LINUX-01 — verifica pre-lab
echo "=== VERIFICA PRE-LAB EMAIL/WEB ==="

# Nginx presente (usato da GLPI)?
if command -v nginx &>/dev/null; then
    echo "[OK] Nginx installato: $(nginx -v 2>&1)"
else
    echo "[WARN] Nginx non installato — installarlo: sudo apt install -y nginx"
fi

# GLPI risponde?
HTTP=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/glpi --max-time 5 2>/dev/null)
echo "[INFO] GLPI HTTP status: $HTTP"

# Porta 25 (SMTP) in ascolto?
if ss -tlnp | grep -q ":25 "; then
    echo "[OK] Porta SMTP 25 in ascolto"
else
    echo "[INFO] SMTP non configurato — lo faremo nel tutorial"
fi

# DNS funzionante per test SPF/DKIM?
if dig +short MX lab.local @192.168.56.10 &>/dev/null; then
    echo "[OK] DNS raggiungibile"
fi
```

---

## PART A: FONDAMENTI — Email e Web come Servizi Critici di Produttività

> Ogni azienda ha due servizi che non possono mai fermarsi: la posta elettronica e il sito web/portale aziendale. Se la mail si ferma per un'ora in una PMI, il personale è bloccato, i clienti non ricevono risposta, le offerte non arrivano. Se il sito web è offline, l'azienda è invisibile su internet. La manutenzione di questi servizi non è solo tecnica — è business continuity.

---

### Concetto A1: L'Ecosistema Email — Come Funziona la Posta Aziendale

> **Analogia.** Spedire un'email è come spedire una lettera raccomandata con un sistema di verifiche multiple. Il mittente (il tuo server email) consegna la lettera all'ufficio postale (server SMTP del destinatario). L'ufficio postale verifica: "Questo mittente è autorizzato a inviare lettere per conto di quest'azienda?" (SPF), "La firma sulla lettera è quella dell'azienda?" (DKIM), "Cosa faccio se la verifica fallisce?" (DMARC). Senza queste verifiche, chiunque potrebbe mandare email fingendosi la tua azienda.

**Il percorso di una email aziendale:**

```
MITTENTE (Marco in azienda.it)
        │ Compone email su Outlook/Gmail
        ▼
SERVER EMAIL MITTENTE (mail.azienda.it, porta 587 con TLS)
        │ Firma l'email con DKIM
        │ Controlla SPF: "Sono autorizzato a inviare per azienda.it?"
        ▼
DNS LOOKUP → Dove si trova il server email di destinatario.com?
             dig MX destinatario.com → mail.destinatario.com
        ▼
SERVER EMAIL DESTINATARIO (mail.destinatario.com, porta 25)
        │ Verifica SPF: "Questo IP è autorizzato per azienda.it?"
        │ Verifica DKIM: "La firma è valida?"
        │ Verifica DMARC: "Cosa faccio se le verifiche falliscono?"
        ▼
INBOX (Giulia su destinatario.com)
```

**I protocolli email fondamentali:**

| Protocollo | Porta | Scopo | Analogia |
|---|---|---|---|
| **SMTP** | 25 (server-to-server) | Consegna email tra server | Postino che consegna la lettera |
| **SMTP** | 587 (client-to-server) | Invio email dal client | Tu che porti la lettera all'ufficio postale |
| **IMAP** | 993 (TLS) | Leggi email sul server | Accedi alla tua cassetta postale remota |
| **POP3** | 995 (TLS) | Scarica email (legacy) | Svuoti la cassetta postale nel tuo PC |

---

### Concetto A2: SPF, DKIM e DMARC — Il Trittico di Sicurezza Email

> **Analogia.** Immagina di ricevere una lettera con il logo della tua banca che ti chiede di cliccare su un link. Come fai a sapere se è vera? SPF dice "la busta viene davvero dalla sede postale della banca" (IP autorizzato), DKIM dice "c'è la firma digitale autentica della banca sulla lettera" (crittografia), DMARC dice "cosa deve fare il postino se busta o firma non corrispondono" (policy di azione). Insieme, questi tre meccanismi rendono quasi impossibile falsificare email di un'azienda che li implementa correttamente.

**SPF — Sender Policy Framework:**

```
Record DNS TXT per il dominio mittente:
  lab.local.  IN  TXT  "v=spf1 ip4:192.168.56.10 -all"
                        │      │                  │
                        │      └── IP autorizzato └── tutti gli altri: RIFIUTA
                        └── versione SPF

Lettura:
  "Solo i server con IP 192.168.56.10 sono autorizzati a inviare
   email per conto di lab.local. Rifiuta tutto il resto."

Meccanismi comuni:
  ip4:x.x.x.x/24  → range IPv4 specifico
  include:spf.X.com → includi le regole di un altro dominio (es. M365)
  -all             → fail (rifiuta email non autorizzate)
  ~all             → softfail (marca ma non blocca — solo per testing)
  +all             → pass (autorizza tutti — INSICURO, non usare mai)
```

**DKIM — DomainKeys Identified Mail:**

```
Come funziona la firma DKIM:

1. Il server email mittente ha una CHIAVE PRIVATA (segreta)
   Firma ogni email con questa chiave → produce una firma univoca

2. La chiave PUBBLICA è pubblicata nel DNS:
   selector1._domainkey.lab.local IN TXT "v=DKIM1; k=rsa; p=MIIBIjANBg..."
   
3. Il server destinatario legge la chiave pubblica dal DNS
   e verifica la firma nell'email → se corrisponde: autentico

Header email con firma DKIM:
  DKIM-Signature: v=1; a=rsa-sha256; d=lab.local; s=selector1;
    h=from:to:subject:date; b=<firma crittografica>

Rotazione raccomandata: ogni 6-12 mesi
  Processo: crea nuovo selector → pubblica su DNS → aspetta 48h
  → configura server → rimuovi vecchio selector dopo 7 giorni
```

**DMARC — Domain-based Message Authentication, Reporting and Conformance:**

```
Record DMARC (sempre su _dmarc.dominio):
_dmarc.lab.local IN TXT "v=DMARC1; p=reject; rua=mailto:dmarc@lab.local"
                          │         │          │
                          │         │          └── invia report aggregati qui
                          │         └── policy: none/quarantine/reject
                          └── versione DMARC

Policy progression (come adottare DMARC senza bloccare email legittime):
  
  FASE 1: p=none     → solo monitoraggio, nessuna azione
          "Osserva chi invia email con il mio dominio"
          ↓ (2-4 settimane)
  
  FASE 2: p=quarantine; pct=25  → metti in spam 25% delle email sospette
          "Inizia a bloccare le email non autorizzate parzialmente"
          ↓ (2-4 settimane)
  
  FASE 3: p=quarantine; pct=100 → tutte le email sospette in spam
          ↓ (2-4 settimane)
  
  FASE 4: p=reject   → rifiuta le email non autorizzate
          "Obiettivo finale — protezione completa"
```

---

### Concetto A3: Web Server — Nginx vs IIS

> **Analogia.** Un web server è come un ristorante. I clienti (browser) arrivano e fanno ordinazioni (richieste HTTP). Il cameriere (Nginx/IIS) prende l'ordinazione e la porta in cucina (applicazione backend). La cucina prepara il piatto (risposta) e il cameriere lo consegna al cliente. Nginx e un cameriere super-efficiente che può servire migliaia di clienti contemporaneamente con pochissime risorse. IIS è il cameriere Microsoft, integrato con Windows e ideale per applicazioni .NET.

**Nginx vs IIS — confronto:**

| Caratteristica | Nginx | IIS |
|---|---|---|
| Sistema operativo | Linux (principalmente), anche Windows | Solo Windows |
| Modello | Event-driven, asincrono | Thread-based (Workers) |
| Caso d'uso tipico | Proxy inverso, siti statici, PHP, Python, Node.js | Applicazioni .NET/ASP.NET, Windows-integrated auth |
| Nel nostro lab | SRV-LINUX-01 (con GLPI) | DC-LAB-01 (opzionale, disponibile) |
| Configurazione | `/etc/nginx/` (file testo) | IIS Manager (GUI) + ApplicationHost.config |
| Logging | `/var/log/nginx/access.log` e `error.log` | `C:\inetpub\logs\LogFiles\` |

**Anatomia di una richiesta HTTP — cosa fa il web server:**

```
Browser richiede: GET http://192.168.56.20:8080/glpi/
                          │
                          ▼
              Nginx riceve la richiesta sulla porta 8080
                          │
              Controlla la configurazione:
              "Qual è il virtual host per la porta 8080?"
                          │
              Trova: proxy_pass http://127.0.0.1:80/
              (GLPI gira come container Docker su porta 80 interna)
                          │
              Nginx fa da "intermediario" (reverse proxy):
              Forward la richiesta al container Docker
                          │
              Il container risponde con HTML
                          │
              Nginx invia la risposta al browser
                          │
              Browser mostra la pagina GLPI
```

---

### Concetto A4: Certificati SSL/TLS — La Sicurezza delle Connessioni Web

> **Analogia.** Quando parli di finanze con il tuo banchiere nel suo ufficio, la conversazione è privata. Ma se lo chiami in un bar affollato, chiunque può sentire. HTTP è come parlare al bar — tutto in chiaro. HTTPS è l'ufficio privato: la conversazione è cifrata e il tuo interlocutore ha un "documento d'identità" (certificato) che prova chi è.

**Struttura di un certificato SSL/TLS:**

```
Certificato SSL per glpi.lab.local
├── Subject: CN=glpi.lab.local (il nome del sito)
├── SAN (Subject Alternative Names):
│   ├── glpi.lab.local
│   └── srv-linux-01.lab.local
├── Issuer: CN=Lab Root CA (chi l'ha firmato)
├── Valid From: 2026-07-15
├── Valid Until: 2027-07-15 (1 anno tipicamente)
├── Public Key: RSA 2048 bit o ECDSA P-256
└── Signature Algorithm: SHA256withRSA
```

**Curva di vita di un certificato e il suo rinnovo:**

```
Emissione certificato (Let's Encrypt: 90 giorni, CA aziendale: 1-2 anni)
         ↓
Periodo valido — HTTPS funziona normalmente
         ↓
30 giorni prima della scadenza → ALERT (rinnova ora!)
         ↓
14 giorni prima → WARNING CRITICO
         ↓
Scadenza → certificato non valido
           Browser mostra "La tua connessione non è privata"
           Utenti non possono accedere (o ignorano il warning)
           
Automazione con Let's Encrypt + certbot:
  certbot renew → controlla e rinnova automaticamente
  Schedulato come cron job: 0 3 * * * certbot renew --quiet
```

---

### Concetto A5: Monitoraggio Web — Cosa Misurare

> **Perché mi interessa?** Un'applicazione web "lenta" è quasi peggio di una "offline". Gli utenti tollerano l'indisponibilità temporanea; non tollerano attendere 10 secondi per caricare una pagina ogni giorno. Monitorare le performance web è misurare l'esperienza degli utenti prima che si lamentino.

**Le 4 metriche fondamentali di performance web:**

```
1. DNS Resolution Time: < 50ms
   Quanto ci vuole per risolvere il nome in IP
   Problema: DNS lento o non cachato

2. TCP Connect Time: < 100ms
   Tempo per stabilire la connessione TCP (3-way handshake)
   Problema: latenza di rete, firewall lento

3. TLS Handshake Time: < 200ms
   Negoziazione crittografia SSL/TLS
   Problema: certificato pesante, algoritmi lenti

4. Time To First Byte (TTFB): < 500ms
   Tempo dal momento della richiesta alla prima risposta del server
   Problema: applicazione lenta, database lento, cache non configurata

TOTALE atteso: < 2 secondi per la prima pagina
```

**Codici di risposta HTTP — cosa significano:**

```
2xx — Successo
  200 OK           → richiesta riuscita, contenuto restituito
  201 Created      → risorsa creata (API REST POST)
  204 No Content   → successo ma nessun contenuto da restituire

3xx — Reindirizzamento
  301 Moved Permanently → il sito si è spostato definitivamente
  302 Found             → redirect temporaneo
  304 Not Modified      → usa la versione in cache (ottimo!)

4xx — Errore del client
  400 Bad Request       → richiesta malformata
  401 Unauthorized      → autenticazione richiesta
  403 Forbidden         → accesso negato (autenticato ma non autorizzato)
  404 Not Found         → risorsa non trovata
  
5xx — Errore del server (PROBLEMI DA MONITORARE)
  500 Internal Server Error → bug nell'applicazione
  502 Bad Gateway           → il backend non risponde
  503 Service Unavailable   → server sovraccarico o in manutenzione
  504 Gateway Timeout       → il backend è troppo lento
```

---

---

## PART B: OPERAZIONI — Configurare e Monitorare Email e Web

---

### Esercizio B1: Email Security — Configura SPF/DKIM/DMARC nel DNS del Lab

**Obiettivo.** Aggiungere i record DNS di autenticazione email per il dominio `lab.local` su DC-LAB-01: SPF per autorizzare DC-LAB-01 come server email, un record DKIM di esempio, e un record DMARC in modalità monitoraggio.

**Background.** Nel nostro lab non abbiamo un server Exchange reale, ma possiamo simulare la corretta configurazione DNS che un dominio produttivo avrebbe. Questo ti insegna sia la sintassi dei record che come verificarli — competenze direttamente applicabili in produzione.

---

**Step 1 — Aggiungi il record MX (Mail Exchanger)**

```powershell
# Su DC-LAB-01

# Aggiungi un record MX che punta a DC-LAB-01 come server email
Add-DnsServerResourceRecord `
    -ZoneName "lab.local" `
    -MX `
    -Name "@" `
    -MailExchange "dc-lab-01.lab.local." `
    -Preference 10

# Verifica
Resolve-DnsName -Name "lab.local" -Type MX -Server 192.168.56.10
```

Output atteso:
```
Name                                     Type   TTL   Section    NameExchange              Preference
----                                     ----   ---   -------    ------------              ----------
lab.local                                MX     1200  Answer     dc-lab-01.lab.local       10
```

---

**Step 2 — Aggiungi il record SPF**

```powershell
# Record SPF — autorizza DC-LAB-01 (192.168.56.10) come server email del dominio
Add-DnsServerResourceRecord `
    -ZoneName "lab.local" `
    -TXT `
    -Name "@" `
    -DescriptiveText "v=spf1 ip4:192.168.56.10 -all"

# Verifica il record SPF
Resolve-DnsName -Name "lab.local" -Type TXT -Server 192.168.56.10 |
    Where-Object { $_.Strings -like "*v=spf1*" }
```

Output atteso:
```
Name                                     Type   TTL   Section    Strings
----                                     ----   ---   -------    -------
lab.local                                TXT    1200  Answer     {v=spf1 ip4:192.168.56.10 -all}
```

**Lettura del record:** "Solo il server con IP 192.168.56.10 è autorizzato a inviare email per conto di lab.local. Ogni altro server deve essere rifiutato (`-all`)."

---

**Step 3 — Aggiungi un record DKIM di esempio**

```powershell
# In produzione la chiave pubblica DKIM viene generata dal server email.
# Nel lab usiamo una chiave di esempio per simulare la configurazione.

# Formato: selector1._domainkey.lab.local
$dkimKey = "v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2mX2M5b+LABexample"

Add-DnsServerResourceRecord `
    -ZoneName "lab.local" `
    -TXT `
    -Name "selector1._domainkey" `
    -DescriptiveText $dkimKey

# Verifica
Resolve-DnsName -Name "selector1._domainkey.lab.local" -Type TXT -Server 192.168.56.10
```

Output atteso:
```
Name                                     Type   TTL   Section    Strings
----                                     ----   ---   -------    -------
selector1._domainkey.lab.local           TXT    1200  Answer     {v=DKIM1; k=rsa; p=MIIBIjANB...}
```

---

**Step 4 — Aggiungi il record DMARC (modalità monitoraggio)**

```powershell
# DMARC in modalità "none" — monitoraggio senza azione
# rua = indirizzo dove ricevere i report aggregati
Add-DnsServerResourceRecord `
    -ZoneName "lab.local" `
    -TXT `
    -Name "_dmarc" `
    -DescriptiveText "v=DMARC1; p=none; rua=mailto:dmarc-reports@lab.local; pct=100"

# Verifica tutti e 3 i record di sicurezza email
Write-Host "=== VERIFICA SICUREZZA EMAIL ===" -ForegroundColor Cyan

Write-Host "`n[MX Record]"
Resolve-DnsName "lab.local" -Type MX -Server 192.168.56.10 | Select-Object Name, NameExchange, Preference

Write-Host "`n[SPF Record]"
Resolve-DnsName "lab.local" -Type TXT -Server 192.168.56.10 | 
    Where-Object { $_.Strings -like "*v=spf1*" } | Select-Object Name, Strings

Write-Host "`n[DKIM Record]"
Resolve-DnsName "selector1._domainkey.lab.local" -Type TXT -Server 192.168.56.10 |
    Select-Object Name, Strings

Write-Host "`n[DMARC Record]"
Resolve-DnsName "_dmarc.lab.local" -Type TXT -Server 192.168.56.10 |
    Select-Object Name, Strings
```

---

**Step 5 — Verifica dalla linea di comando Linux**

```bash
# Su SRV-LINUX-01 — verifica i record email dal lato Linux

# MX Record
dig @192.168.56.10 lab.local MX

# SPF Record
dig @192.168.56.10 lab.local TXT | grep "v=spf1"

# DKIM Record
dig @192.168.56.10 selector1._domainkey.lab.local TXT

# DMARC Record
dig @192.168.56.10 _dmarc.lab.local TXT
```

Output atteso per SPF:
```
;; ANSWER SECTION:
lab.local.              1200    IN      TXT     "v=spf1 ip4:192.168.56.10 -all"
```

---

### Esercizio B2: SMTP Testing — Verifica il Flusso Email con Postfix

**Obiettivo.** Installare un relay SMTP semplice con Postfix su SRV-LINUX-01, testare l'invio di email tra i nodi del lab, e verificare i log SMTP.

**Background.** Anche senza Exchange, saper testare il flusso SMTP via `nc` (netcat) o Postfix è una competenza fondamentale. Molti problemi di email in produzione si debuggano esattamente così.

---

**Step 1 — Installa Postfix su SRV-LINUX-01**

```bash
# Su SRV-LINUX-01 via SSH

# Installa Postfix (sceglie "Internet Site" se chiesto)
sudo DEBIAN_FRONTEND=noninteractive apt install -y postfix mailutils

# Configura il dominio email
sudo postconf -e "myhostname = srv-linux-01.lab.local"
sudo postconf -e "mydomain = lab.local"
sudo postconf -e "myorigin = lab.local"
sudo postconf -e "inet_interfaces = loopback-only"
sudo postconf -e "mydestination = lab.local, localhost"

# Riavvia Postfix
sudo systemctl restart postfix
sudo systemctl status postfix
```

Output atteso:
```
● postfix.service - Postfix Mail Transport Agent
     Loaded: loaded (/lib/systemd/system/postfix.service; enabled)
     Active: active (running) since Wed 2026-07-15 10:00:00 UTC; 5s ago
```

---

**Step 2 — Test SMTP manuale con netcat**

```bash
# Test della connessione SMTP sulla porta 25 (locale)
nc -v 127.0.0.1 25
```

Dopo la connessione, esegui questa sequenza SMTP manuale:
```
EHLO srv-linux-01.lab.local
MAIL FROM:<test@lab.local>
RCPT TO:<lab-admin@lab.local>
DATA
Subject: Test SMTP Lab
From: test@lab.local

Questo e un test SMTP manuale dal tutorial ops04c.
.
QUIT
```

Output atteso (il server SMTP risponde con codici a 3 cifre):
```
220 srv-linux-01.lab.local ESMTP Postfix (Ubuntu)
250-srv-linux-01.lab.local
250 PIPELINING
250 2.1.0 Ok
250 2.1.5 Ok
354 End data with <CR><LF>.<CR><LF>
250 2.0.0 Ok: queued as XXXXXXXX
221 2.0.0 Bye
```

I codici SMTP chiave:
```
220 → Server pronto
250 → Successo
354 → Invia il corpo del messaggio
221 → Chiudi la connessione
4xx → Errore temporaneo (riprova)
5xx → Errore permanente (non riprovare)
```

---

**Step 3 — Invia un'email di test con mail**

```bash
# Invia un'email usando il comando mail
echo "Test email dal tutorial ops04c - $(date)" | mail -s "Test Lab Email" lab-admin@lab.local

# Verifica che sia stata consegnata
ls -la /var/mail/lab-admin 2>/dev/null || mail -u lab-admin
```

---

**Step 4 — Analizza i log SMTP**

```bash
# Log Postfix in tempo reale
sudo journalctl -u postfix -f &
LOG_PID=$!

# Invia un'altra email per vedere il log
echo "Test log analysis" | mail -s "Log Test" lab-admin@lab.local

sleep 3
kill $LOG_PID 2>/dev/null

# Analisi degli ultimi 20 log email
sudo journalctl -u postfix -n 20 --no-pager
```

Output atteso (campi importanti):
```
Jul 15 10:15:30 srv-linux-01 postfix/smtp[1234]: from=<test@lab.local>, size=120
Jul 15 10:15:30 srv-linux-01 postfix/local[1235]: from=<test@lab.local>, 
  to=<lab-admin@lab.local>, relay=local, delay=0.5,
  status=sent (delivered to mailbox)
```

---

**Step 5 — Verifica record SPF con simulazione manuale**

```bash
# Simula la verifica SPF lato destinatario:
# "L'email arriva da 192.168.56.10 — è autorizzato per lab.local?"
dig @192.168.56.10 lab.local TXT | grep "v=spf1"
# Output: "v=spf1 ip4:192.168.56.10 -all"
# Conclusione: 192.168.56.10 è nell'ip4 → PASS SPF

# Simula un server NON autorizzato (es. 10.0.0.1):
# 10.0.0.1 NON è in "ip4:192.168.56.10" → FAIL SPF (-all) → email rifiutata
echo "[OK] SPF check: 192.168.56.10 → PASS (autorizzato nel record)"
echo "[INFO] SPF check: 10.0.0.1 → FAIL (non autorizzato, -all)"
```

---

### Esercizio B3: Nginx — Configurazione e Monitoraggio

**Obiettivo.** Verificare la configurazione Nginx su SRV-LINUX-01, configurare un virtual host per un sito di test, analizzare i log di accesso, e impostare la rotazione automatica dei log.

**Background.** Nginx su SRV-LINUX-01 già serve GLPI tramite reverse proxy. Imparare a configurare virtual host, analizzare log e ruotarli è fondamentale per chi gestisce applicazioni web Linux.

---

**Step 1 — Verifica la configurazione Nginx corrente**

```bash
# Su SRV-LINUX-01

# Nginx installato?
nginx -v 2>&1

# Verifica la configurazione (syntax check)
sudo nginx -t
```

Output atteso:
```
nginx version: nginx/1.18.0 (Ubuntu)
nginx: the configuration is OK
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

```bash
# Visualizza la configurazione completa
sudo nginx -T 2>/dev/null | head -80

# Elenca i virtual host abilitati
ls -la /etc/nginx/sites-enabled/

# Visualizza la configurazione di default
cat /etc/nginx/sites-available/default
```

---

**Step 2 — Crea un virtual host di test**

```bash
# Crea un virtual host per il sito di test "lab-status.lab.local"
sudo tee /etc/nginx/sites-available/lab-status << 'NGINXCONF'
server {
    listen 8090;
    server_name lab-status.lab.local 192.168.56.20;
    
    root /var/www/lab-status;
    index index.html;
    
    # Log separati per questo virtual host
    access_log /var/log/nginx/lab-status_access.log;
    error_log  /var/log/nginx/lab-status_error.log warn;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    # Endpoint health check (restituisce 200 sempre)
    location /health {
        return 200 'OK\n';
        add_header Content-Type text/plain;
    }
    
    # Blocca accesso ai file nascosti (.htpasswd, .git, ecc.)
    location ~ /\. {
        deny all;
        return 404;
    }
}
NGINXCONF

# Crea la directory e la pagina HTML
sudo mkdir -p /var/www/lab-status
sudo tee /var/www/lab-status/index.html << 'HTML'
<!DOCTYPE html>
<html>
<head><title>Lab IT Status</title></head>
<body>
<h1>Stato Infrastruttura Lab</h1>
<p>Server: SRV-LINUX-01 | IP: 192.168.56.20</p>
<p>Ambiente: Lab IT Operations Tutorial</p>
<ul>
  <li>GLPI: <a href="http://192.168.56.20:8080/glpi">http://192.168.56.20:8080/glpi</a></li>
  <li>DNS: 192.168.56.10 (DC-LAB-01)</li>
</ul>
</body>
</html>
HTML

# Abilita il virtual host
sudo ln -sf /etc/nginx/sites-available/lab-status /etc/nginx/sites-enabled/

# Verifica la sintassi e ricarica Nginx
sudo nginx -t && sudo systemctl reload nginx
```

Output atteso:
```
nginx: the configuration is OK
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

---

**Step 3 — Testa il virtual host**

```bash
# Test locale su SRV-LINUX-01
curl -v http://127.0.0.1:8090/

# Test endpoint health
curl http://127.0.0.1:8090/health

# Misura i tempi di risposta
curl -w "\nDNS:%{time_namelookup}s Connect:%{time_connect}s TTFB:%{time_starttransfer}s Total:%{time_total}s\n" \
     -o /dev/null -s http://127.0.0.1:8090/
```

Output atteso:
```
DNS:0.000012s Connect:0.000104s TTFB:0.001850s Total:0.001930s
```

```powershell
# Da WKS-LAB-01 — testa il virtual host
Invoke-WebRequest -Uri "http://192.168.56.20:8090/" -UseBasicParsing |
    Select-Object StatusCode, ContentType, @{N="Size";E={$_.Content.Length}}

# Test endpoint health
Invoke-WebRequest -Uri "http://192.168.56.20:8090/health" -UseBasicParsing |
    Select-Object StatusCode, Content
```

---

**Step 4 — Analisi dei log Nginx**

```bash
# Genera alcune richieste di test per popolare i log
for i in 1 2 3 4 5; do
    curl -s http://127.0.0.1:8090/ > /dev/null
    curl -s http://127.0.0.1:8090/health > /dev/null
    curl -s http://127.0.0.1:8090/nonexistente > /dev/null  # genera 404
done

# Visualizza il log di accesso
tail -20 /var/log/nginx/lab-status_access.log
```

Output atteso (formato Combined Log):
```
127.0.0.1 - - [15/Jul/2026:10:30:00 +0000] "GET / HTTP/1.1" 200 312 "-" "curl/7.81.0"
127.0.0.1 - - [15/Jul/2026:10:30:01 +0000] "GET /health HTTP/1.1" 200 3 "-" "curl/7.81.0"
127.0.0.1 - - [15/Jul/2026:10:30:02 +0000] "GET /nonexistente HTTP/1.1" 404 153 "-" "curl/7.81.0"
```

Lettura del formato Combined Log:
```
IP       - - [timestamp]          "METODO /percorso HTTP/1.1" STATUS SIZE "referer" "user-agent"
127.0.0.1  -  - [15/Jul/2026...]  "GET /        HTTP/1.1"    200   312   "-"       "curl/7.81.0"
```

```bash
# Analisi log: conta le risposte per codice HTTP
echo "=== Distribuzione codici HTTP ==="
awk '{print $9}' /var/log/nginx/lab-status_access.log | sort | uniq -c | sort -rn

# Top 5 URL più richieste
echo -e "\n=== Top URL ==="
awk '{print $7}' /var/log/nginx/lab-status_access.log | sort | uniq -c | sort -rn | head -5

# Errori 5xx delle ultime 24 ore (se esistono)
echo -e "\n=== Errori 5xx ==="
awk '$9 ~ /^5/ {print $0}' /var/log/nginx/access.log 2>/dev/null | tail -10
```

---

**Step 5 — Configura la rotazione automatica dei log**

```bash
# Verifica la configurazione logrotate esistente per Nginx
cat /etc/logrotate.d/nginx

# Crea una configurazione logrotate specifica per lab-status
sudo tee /etc/logrotate.d/nginx-lab-status << 'LOGROTATE'
/var/log/nginx/lab-status_*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 $(cat /var/run/nginx.pid)
    endscript
}
LOGROTATE

# Testa la configurazione logrotate (dry run — non fa nulla)
sudo logrotate -d /etc/logrotate.d/nginx-lab-status
```

Output del dry run (mostra cosa farebbe senza -d):
```
reading config file /etc/logrotate.d/nginx-lab-status
Handling 1 logs

rotating pattern: /var/log/nginx/lab-status_*.log  after 1 days (30 rotations)
empty log files are not rotated, old logs are compressed
```

---

### Esercizio B4: Monitoraggio Web — Health Check e Tempi di Risposta

**Obiettivo.** Creare uno script di monitoraggio che verifica periodicamente la salute delle applicazioni web del lab (GLPI e il nuovo lab-status site) e segnala anomalie.

**Background.** Il monitoraggio degli endpoint web è la prima linea di difesa contro le interruzioni di servizio. Uno script che controlla ogni minuto che GLPI risponda con 200 è più veloce di qualsiasi alert Zabbix nel rilevare un problema.

---

**Step 1 — Script di health check per endpoint web**

```bash
# Su SRV-LINUX-01 — crea lo script
sudo tee /opt/lab-scripts/web_health_check.sh << 'SCRIPT'
#!/bin/bash
# web_health_check.sh — Verifica la salute degli endpoint web del lab
# Esegui: bash /opt/lab-scripts/web_health_check.sh

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[ OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERR]${NC} $1"; }

ENDPOINTS=(
    "GLPI|http://127.0.0.1:8080/glpi|200|5"
    "Lab-Status|http://127.0.0.1:8090|200|3"
    "Health Check|http://127.0.0.1:8090/health|200|2"
)

echo ""
echo "========================================="
echo " WEB HEALTH CHECK — $(hostname) — $(date '+%Y-%m-%d %H:%M')"
echo "========================================="

ERRORS=0

for entry in "${ENDPOINTS[@]}"; do
    IFS='|' read -r name url expected_code timeout <<< "$entry"
    
    # Misura risposta con curl
    result=$(curl -s -o /dev/null -w "%{http_code} %{time_total} %{time_starttransfer}" \
        --connect-timeout "$timeout" --max-time $((timeout * 2)) "$url" 2>/dev/null)
    
    http_code=$(echo "$result" | awk '{print $1}')
    time_total=$(echo "$result" | awk '{print $2}')
    ttfb=$(echo "$result" | awk '{print $3}')
    
    if [ "$http_code" = "$expected_code" ]; then
        ok "$name: HTTP $http_code | Total: ${time_total}s | TTFB: ${ttfb}s"
    elif [ -z "$http_code" ]; then
        err "$name: TIMEOUT dopo ${timeout}s — servizio non raggiungibile"
        ERRORS=$((ERRORS + 1))
    else
        warn "$name: HTTP $http_code (atteso $expected_code) | ${time_total}s"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""
echo "========================================="
if [ "$ERRORS" -eq 0 ]; then
    echo " ESITO: TUTTO OK — $ERRORS errori"
else
    echo " ESITO: $ERRORS PROBLEMA/I RILEVATO/I"
fi
echo "========================================="
exit $ERRORS
SCRIPT

sudo chmod +x /opt/lab-scripts/web_health_check.sh

# Esegui il check
/opt/lab-scripts/web_health_check.sh
```

---

**Step 2 — Pianifica l'health check ogni 5 minuti con cron**

```bash
# Aggiungi il cron job
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/lab-scripts/web_health_check.sh >> /var/log/web-health.log 2>&1") | crontab -

# Verifica il crontab
crontab -l
```

---

**Step 3 — Simula un'interruzione di servizio e verifica il rilevamento**

```bash
# Ferma temporaneamente Nginx (simula un crash)
sudo systemctl stop nginx
echo "[SIM] Nginx fermato — simula un'interruzione"

# Esegui il check — deve rilevare i problemi
/opt/lab-scripts/web_health_check.sh

# Riavvia Nginx
sudo systemctl start nginx
echo "[SIM] Nginx riavviato — servizio ripristinato"

# Esegui il check — deve rilevare il ripristino
/opt/lab-scripts/web_health_check.sh
```

---

**Step 4 — Analisi dei log Nginx per errori 5xx**

```bash
# Script di analisi del tasso di errore Nginx
cat << 'EOF'
# Analisi log Nginx: errori 5xx nelle ultime 60 minuti
LOGFILE="/var/log/nginx/access.log"
ONE_HOUR_AGO=$(date -d '60 minutes ago' '+%d/%b/%Y:%H:%M' 2>/dev/null || date -v -60M '+%d/%b/%Y:%H:%M')

# Conta errori 5xx
ERRORS_5XX=$(awk -v date="$ONE_HOUR_AGO" '
    $4 > "[" date && $9 ~ /^5/ {count++}
    END {print count+0}
' "$LOGFILE" 2>/dev/null)

# Conta totale richieste
TOTAL_REQ=$(awk -v date="$ONE_HOUR_AGO" '
    $4 > "[" date {count++}
    END {print count+0}
' "$LOGFILE" 2>/dev/null)

if [ "$TOTAL_REQ" -gt 0 ]; then
    ERROR_RATE=$(echo "scale=2; $ERRORS_5XX * 100 / $TOTAL_REQ" | bc 2>/dev/null || echo "0")
    echo "Richieste totali (1h): $TOTAL_REQ"
    echo "Errori 5xx (1h): $ERRORS_5XX"
    echo "Error rate: ${ERROR_RATE}%"
    if (( $(echo "$ERROR_RATE > 5" | bc -l) )); then
        echo "[WARN] Error rate > 5% — investigare!"
    fi
else
    echo "Nessuna richiesta nell'ultima ora"
fi
EOF

# Esegui la versione pratica
awk '{print $9}' /var/log/nginx/access.log 2>/dev/null | sort | uniq -c | sort -rn
```

---

### Esercizio B5: Verifica SSL/TLS — Certificati e Sicurezza HTTPS

**Obiettivo.** Verificare i certificati SSL/TLS di GLPI e del lab-status site, misurare le date di scadenza, e testare la sicurezza TLS con strumenti da linea di comando.

**Background.** Un certificato scaduto è tra le cause più frequenti di interruzioni di servizio "misteriose" — il servizio gira perfettamente ma nessuno può accedere perché il browser blocca la connessione. Monitorare le date di scadenza è fondamentale.

---

**Step 1 — Genera un certificato self-signed per il lab-status**

```bash
# Su SRV-LINUX-01

# Crea la directory per i certificati lab
sudo mkdir -p /etc/ssl/lab

# Genera un certificato self-signed per il lab (valido 1 anno)
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/lab/lab-status.key \
    -out /etc/ssl/lab/lab-status.crt \
    -subj "/C=IT/ST=Lab/L=Lab/O=IT Operations Lab/CN=lab-status.lab.local" \
    -addext "subjectAltName=DNS:lab-status.lab.local,DNS:srv-linux-01.lab.local,IP:192.168.56.20"

echo "[OK] Certificato self-signed generato"

# Verifica il certificato
openssl x509 -in /etc/ssl/lab/lab-status.crt -noout -text | grep -E "Subject:|Not Before:|Not After:|DNS:|IP:"
```

Output atteso:
```
        Subject: C = IT, ST = Lab, L = Lab, O = IT Operations Lab, CN = lab-status.lab.local
            Not Before: Jul 15 10:00:00 2026 GMT
            Not After : Jul 15 10:00:00 2027 GMT
                DNS:lab-status.lab.local
                DNS:srv-linux-01.lab.local
                IP Address:192.168.56.20
```

---

**Step 2 — Configura HTTPS sul virtual host lab-status**

```bash
# Aggiorna il virtual host per supportare HTTPS (porta 8443)
sudo tee /etc/nginx/sites-available/lab-status << 'NGINXCONF'
server {
    listen 8090;
    server_name lab-status.lab.local 192.168.56.20;
    
    # Redirect HTTP → HTTPS
    return 301 https://$host:8443$request_uri;
}

server {
    listen 8443 ssl;
    server_name lab-status.lab.local 192.168.56.20;
    
    ssl_certificate     /etc/ssl/lab/lab-status.crt;
    ssl_certificate_key /etc/ssl/lab/lab-status.key;
    
    # Protocolli sicuri (disabilita SSLv3, TLSv1.0, TLSv1.1)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    
    root /var/www/lab-status;
    index index.html;
    
    access_log /var/log/nginx/lab-status_access.log;
    error_log  /var/log/nginx/lab-status_error.log warn;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    location /health {
        return 200 'OK\n';
        add_header Content-Type text/plain;
    }
}
NGINXCONF

sudo nginx -t && sudo systemctl reload nginx

# Test HTTPS (ignora errore certificato self-signed con -k)
curl -k https://127.0.0.1:8443/health
```

---

**Step 3 — Verifica il certificato con openssl**

```bash
# Verifica il certificato tramite connessione TLS
echo | openssl s_client -connect 127.0.0.1:8443 -servername lab-status.lab.local 2>/dev/null | \
    openssl x509 -noout -dates -subject

# Calcola i giorni alla scadenza
EXPIRY=$(openssl x509 -in /etc/ssl/lab/lab-status.crt -noout -enddate | cut -d= -f2)
EXPIRY_TS=$(date -d "$EXPIRY" +%s 2>/dev/null || date -j -f "%b %d %T %Y %Z" "$EXPIRY" +%s)
NOW_TS=$(date +%s)
DAYS_LEFT=$(( (EXPIRY_TS - NOW_TS) / 86400 ))

echo "Scadenza certificato: $EXPIRY"
echo "Giorni rimanenti: $DAYS_LEFT"

if [ "$DAYS_LEFT" -lt 30 ]; then
    echo "[WARN] Certificato in scadenza in meno di 30 giorni!"
elif [ "$DAYS_LEFT" -lt 14 ]; then
    echo "[ERR] Certificato in scadenza CRITICO!"
else
    echo "[OK] Certificato valido per $DAYS_LEFT giorni"
fi
```

---

**Step 4 — Script di monitoraggio scadenza certificati**

```bash
# Crea script per monitorare i certificati
sudo tee /opt/lab-scripts/cert_expiry_check.sh << 'CERTSCRIPT'
#!/bin/bash
# cert_expiry_check.sh — Verifica scadenza certificati SSL
# Modifica CERT_FILES per aggiungere altri certificati

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

CERT_FILES=(
    "/etc/ssl/lab/lab-status.crt"
)

WARN_DAYS=30
CRIT_DAYS=14

echo ""
echo "=== VERIFICA SCADENZA CERTIFICATI SSL ==="

for cert in "${CERT_FILES[@]}"; do
    if [ ! -f "$cert" ]; then
        echo -e "${RED}[ERR]${NC} File non trovato: $cert"
        continue
    fi
    
    CN=$(openssl x509 -in "$cert" -noout -subject 2>/dev/null | sed 's/.*CN = //')
    EXPIRY=$(openssl x509 -in "$cert" -noout -enddate 2>/dev/null | cut -d= -f2)
    EXPIRY_TS=$(date -d "$EXPIRY" +%s 2>/dev/null)
    NOW_TS=$(date +%s)
    DAYS=$(( (EXPIRY_TS - NOW_TS) / 86400 ))
    
    if [ "$DAYS" -lt 0 ]; then
        echo -e "${RED}[SCADUTO]${NC} $CN: scaduto da $(( -DAYS )) giorni ($cert)"
    elif [ "$DAYS" -lt "$CRIT_DAYS" ]; then
        echo -e "${RED}[CRITICO]${NC} $CN: scade in $DAYS giorni ($cert)"
    elif [ "$DAYS" -lt "$WARN_DAYS" ]; then
        echo -e "${YELLOW}[WARN]${NC} $CN: scade in $DAYS giorni ($cert)"
    else
        echo -e "${GREEN}[ OK]${NC} $CN: valido per $DAYS giorni"
    fi
done
CERTSCRIPT

sudo chmod +x /opt/lab-scripts/cert_expiry_check.sh
/opt/lab-scripts/cert_expiry_check.sh
```

---

---

## PART C: SISTEMATIZZARE — Governance dei Servizi Email e Web

---

### Progetto C1: SOP — Manutenzione Mensile Email e Web Server

```markdown
# SOP-WEB-001: Manutenzione Mensile Servizi Email e Web

**Versione:** 1.0 | **Data:** 2026-07-15 | **Owner:** Infrastructure Team
**Frequenza:** Prima settimana di ogni mese | **Durata stimata:** 45 minuti

---

## 1. Manutenzione Email Security (15 minuti)

### 1.1 Verifica record SPF
```bash
dig @192.168.56.10 lab.local TXT | grep "v=spf1"
```
Verifica: record presente e corretto (tutti i server di invio inclusi, policy -all)

### 1.2 Verifica record DKIM
```bash
dig @192.168.56.10 selector1._domainkey.lab.local TXT
```
Verifica: chiave pubblica presente e non scaduta

### 1.3 Verifica record DMARC
```bash
dig @192.168.56.10 _dmarc.lab.local TXT
```
Verifica: policy avanzata da none → quarantine → reject seguendo il piano

### 1.4 Analisi code SMTP (se Exchange/Postfix presente)
```bash
# Postfix
sudo postqueue -p
# Se ci sono messaggi in coda da >1h: investigare
```

### 1.5 Test flusso email
```bash
echo "Test mensile" | mail -s "Test $(date)" admin@lab.local
# Verifica che arrivi entro 2 minuti
```

---

## 2. Manutenzione Web Server Nginx (20 minuti)

### 2.1 Verifica configurazione
```bash
sudo nginx -t
```
Atteso: "configuration is OK"

### 2.2 Verifica certificati in scadenza
```bash
/opt/lab-scripts/cert_expiry_check.sh
```
Atteso: tutti i certificati con >30 giorni di validità

### 2.3 Analisi log errori ultimi 30 giorni
```bash
awk '$9 ~ /^5/ {count++} END {print "Errori 5xx:", count+0}' /var/log/nginx/access.log
awk '$9 == "404" {count++} END {print "404 Not Found:", count+0}' /var/log/nginx/access.log
```
Soglia: errori 5xx > 1% del totale richieste → investigare

### 2.4 Controllo dimensione log
```bash
du -sh /var/log/nginx/
```
Se > 1 GB → verificare logrotate o ruotare manualmente

### 2.5 Health check endpoint
```bash
/opt/lab-scripts/web_health_check.sh
```
Atteso: tutti gli endpoint restituiscono 200

### 2.6 Pulizia log vecchi (> 90 giorni)
```bash
find /var/log/nginx/ -name "*.log.*.gz" -mtime +90 -delete
```

---

## 3. Manutenzione IIS (10 minuti — se applicabile)

### 3.1 Stato application pool
```powershell
Get-IISAppPool | Select-Object Name, State
```
Atteso: tutti gli app pool in stato "Started"

### 3.2 Certificati SSL in scadenza
```powershell
Get-ChildItem Cert:\LocalMachine\My |
    Where-Object { $_.NotAfter -lt (Get-Date).AddDays(30) } |
    Select-Object Subject, NotAfter
```

### 3.3 Log IIS vecchi (> 90 giorni)
```powershell
Get-ChildItem "C:\inetpub\logs\LogFiles" -Recurse -Filter "*.log" |
    Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-90) } |
    Remove-Item -WhatIf
# Rimuovere -WhatIf dopo la verifica
```

---

## 4. Escalation

| Problema | Soglia | Azione |
|---|---|---|
| Certificato SSL in scadenza | <30 giorni | Rinnova o pianifica RFC Standard Change |
| Error rate 5xx | >5% | Apri INC P2, analisi log immediata |
| Coda SMTP bloccata | >10 messaggi in attesa >1h | Apri INC P2 |
| Record SPF mancante o sbagliato | Qualsiasi | RFC Normal Change per aggiornamento DNS |
| DMARC policy = none >6 mesi | >6 mesi | Apri CHG per avanzare a quarantine |
```

---

### Progetto C2: Script — Web + Email Health Check Completo

```bash
#!/bin/bash
# web_email_health.sh — Health check completo Web + Email
# Esegui su SRV-LINUX-01: bash /opt/lab-scripts/web_email_health.sh

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[ OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()  { echo -e "${RED}[ERR]${NC} $1"; }

ERRORS=0
WARNINGS=0

echo ""
echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN} WEB + EMAIL HEALTH CHECK — $(date '+%Y-%m-%d %H:%M')${NC}"
echo -e "${CYAN}================================================${NC}"

# ===== EMAIL SECURITY =====
echo -e "\n${CYAN}[ EMAIL SECURITY ]${NC}"

DNS_SERVER="192.168.56.10"
DOMAIN="lab.local"

# SPF
SPF=$(dig @$DNS_SERVER $DOMAIN TXT +short 2>/dev/null | grep "v=spf1")
if [ -n "$SPF" ]; then
    ok "SPF record presente: $SPF"
else
    warn "SPF record NON trovato per $DOMAIN"
    WARNINGS=$((WARNINGS + 1))
fi

# DKIM
DKIM=$(dig @$DNS_SERVER selector1._domainkey.$DOMAIN TXT +short 2>/dev/null)
if [ -n "$DKIM" ]; then
    ok "DKIM record presente (selector1._domainkey.$DOMAIN)"
else
    warn "DKIM record NON trovato — verificare configurazione"
    WARNINGS=$((WARNINGS + 1))
fi

# DMARC
DMARC=$(dig @$DNS_SERVER _dmarc.$DOMAIN TXT +short 2>/dev/null)
if [ -n "$DMARC" ]; then
    ok "DMARC record presente: $DMARC"
    if echo "$DMARC" | grep -q "p=none"; then
        warn "DMARC policy=none — solo monitoraggio, nessuna protezione attiva"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    warn "DMARC record NON trovato"
    WARNINGS=$((WARNINGS + 1))
fi

# SMTP (se Postfix attivo)
if systemctl is-active --quiet postfix 2>/dev/null; then
    QUEUE_SIZE=$(sudo postqueue -p 2>/dev/null | tail -1 | awk '{print $1}' 2>/dev/null || echo "0")
    ok "Postfix attivo | Coda: ${QUEUE_SIZE:-0} messaggi"
else
    warn "Postfix non attivo (OK se non usato)"
fi

# ===== WEB SERVER =====
echo -e "\n${CYAN}[ WEB SERVER ]${NC}"

# Nginx config check
if sudo nginx -t 2>/dev/null; then
    ok "Nginx: configurazione valida"
else
    err "Nginx: errore nella configurazione"
    ERRORS=$((ERRORS + 1))
fi

# Nginx attivo
if systemctl is-active --quiet nginx; then
    ok "Nginx: servizio attivo"
else
    err "Nginx: servizio NON attivo"
    ERRORS=$((ERRORS + 1))
fi

# ===== ENDPOINT HEALTH =====
echo -e "\n${CYAN}[ ENDPOINT HEALTH ]${NC}"

check_endpoint() {
    local name="$1"
    local url="$2"
    local expected="$3"
    local timeout="${4:-5}"
    
    result=$(curl -s -o /dev/null -w "%{http_code} %{time_total}" \
        --connect-timeout "$timeout" --max-time $((timeout * 2)) "$url" \
        -k 2>/dev/null)
    
    code=$(echo "$result" | awk '{print $1}')
    time=$(echo "$result" | awk '{print $2}')
    
    if [ "$code" = "$expected" ]; then
        ok "$name: HTTP $code (${time}s)"
    elif [ -z "$code" ]; then
        err "$name: TIMEOUT — non raggiungibile"
        ERRORS=$((ERRORS + 1))
    else
        warn "$name: HTTP $code (atteso $expected, ${time}s)"
        WARNINGS=$((WARNINGS + 1))
    fi
}

check_endpoint "GLPI" "http://127.0.0.1:8080/glpi" "302"
check_endpoint "Lab-Status" "http://127.0.0.1:8090" "301"
check_endpoint "Lab-Status HTTPS" "https://127.0.0.1:8443" "200"
check_endpoint "Health Check" "https://127.0.0.1:8443/health" "200"

# ===== CERTIFICATI =====
echo -e "\n${CYAN}[ CERTIFICATI SSL ]${NC}"

for cert in /etc/ssl/lab/*.crt; do
    [ -f "$cert" ] || continue
    CN=$(openssl x509 -in "$cert" -noout -subject 2>/dev/null | sed 's/.*CN = //')
    EXPIRY=$(openssl x509 -in "$cert" -noout -enddate 2>/dev/null | cut -d= -f2)
    EXPIRY_TS=$(date -d "$EXPIRY" +%s 2>/dev/null)
    DAYS=$(( (EXPIRY_TS - $(date +%s)) / 86400 ))
    
    if [ "$DAYS" -lt 14 ]; then
        err "CRITICO: $CN scade in $DAYS giorni"
        ERRORS=$((ERRORS + 1))
    elif [ "$DAYS" -lt 30 ]; then
        warn "$CN scade in $DAYS giorni — rinnovare presto"
        WARNINGS=$((WARNINGS + 1))
    else
        ok "$CN: valido per $DAYS giorni"
    fi
done

# ===== LOG ERRORS =====
echo -e "\n${CYAN}[ ANALISI LOG (ultime 24h) ]${NC}"

if [ -f /var/log/nginx/access.log ]; then
    total=$(awk 'NR>0' /var/log/nginx/access.log | wc -l)
    errors5xx=$(awk '$9 ~ /^5/' /var/log/nginx/access.log | wc -l)
    
    if [ "$total" -gt 0 ]; then
        rate=$(echo "scale=1; $errors5xx * 100 / $total" | bc 2>/dev/null || echo "0")
        if (( $(echo "$rate > 5" | bc -l 2>/dev/null || echo 0) )); then
            err "Error rate 5xx: ${rate}% (>5% — investigare)"
            ERRORS=$((ERRORS + 1))
        else
            ok "Error rate 5xx: ${rate}% ($errors5xx su $total richieste)"
        fi
    else
        ok "Nessuna richiesta nei log (server nuovo o log ruotato)"
    fi
fi

# ===== RIEPILOGO =====
echo ""
echo -e "${CYAN}================================================${NC}"
if [ "$ERRORS" -eq 0 ] && [ "$WARNINGS" -eq 0 ]; then
    echo -e " ${GREEN}ESITO: TUTTO OK${NC}"
elif [ "$ERRORS" -eq 0 ]; then
    echo -e " ${YELLOW}ESITO: $WARNINGS WARNING${NC}"
else
    echo -e " ${RED}ESITO: $ERRORS ERRORI + $WARNINGS WARNING${NC}"
fi
echo -e "${CYAN}================================================${NC}"

exit $ERRORS
```

**Installazione:**

```bash
sudo cp /tmp/web_email_health.sh /opt/lab-scripts/
sudo chmod +x /opt/lab-scripts/web_email_health.sh

# Pianifica: ogni giorno alle 08:00
(crontab -l 2>/dev/null; echo "0 8 * * * /opt/lab-scripts/web_email_health.sh >> /var/log/web-email-health.log 2>&1") | crontab -

echo "[OK] Script installato e pianificato"
```

---

### Progetto C3: Integrazione ITIL — Email e Web nelle Pratiche ITSM

**Incident Management — come classificare i problemi Email/Web:**

```
TICKET EMAIL

P1 — Server email completamente offline
     → nessuna email in entrata o uscita
     → impatto: intera organizzazione

P2 — Coda SMTP bloccata con messaggi in attesa > 1h
     → delivery delay ma non perdita
     → impatto: comunicazioni rallentate

P3 — Email di singolo utente non funzionante
     → problema di configurazione client
     → impatto: 1 persona

SR (Service Request) — Nuovo account email
                     → richiesta pianificata, nessun impatto

---

TICKET WEB

P1 — Applicazione web principale offline (GLPI, ERP)
     → tutti gli utenti non possono lavorare
     
P2 — Applicazione web degradata (lenta, errori sporadici)
     → utenti lavorano con difficoltà
     
P3 — Sito web di informazione offline (non critico per ops)

P4 — Redirect non funziona, errore grafico minore
```

**KPI per Email e Web:**

| KPI | Formula | Target | Fonte |
|---|---|---|---|
| Email Delivery Rate | Email consegnate / Email inviate | > 99.9% | Log SMTP |
| Spam False Positive | Email legittime in quarantena / Totale | < 0.1% | Log filtro |
| Web Uptime | Minuti disponibili / Minuti totali | > 99.5% | Health check log |
| TTFB Medio | Media Time To First Byte | < 500ms | Nginx log |
| SSL Cert Days Left | Min giorni alla scadenza | > 30 gg | cert_expiry_check.sh |
| 5xx Error Rate | Errori 5xx / Richieste totali | < 1% | Nginx access.log |

---

## Checklist di Validazione — Tutorial ops04c Completato

### Fondamenti (Part A)
- [ ] Sai descrivere il percorso di una email dalla composizione alla delivery (SMTP, MX, SPF, DKIM, DMARC)
- [ ] Sai spiegare la differenza tra SPF, DKIM e DMARC con un'analogia
- [ ] Sai descrivere la progressione DMARC (none → quarantine → reject)
- [ ] Sai spiegare le 4 metriche di performance web (DNS, TCP, TLS, TTFB) e le soglie target
- [ ] Sai leggere i codici HTTP 2xx/3xx/4xx/5xx e spiegare cosa significano
- [ ] Sai spiegare quando usare HTTPS e cosa garantisce un certificato SSL/TLS

### Operazioni (Part B)
- [ ] B1: Record MX, SPF, DKIM (esempio) e DMARC aggiunti al DNS di lab.local
- [ ] B1: `dig @192.168.56.10 lab.local TXT` mostra il record SPF
- [ ] B2: Postfix installato e funzionante su SRV-LINUX-01
- [ ] B2: Email di test inviata con `mail` e log SMTP analizzato
- [ ] B2: Dialogo SMTP manuale con `nc` completato con successo
- [ ] B3: Virtual host lab-status.lab.local creato su Nginx (porta 8090)
- [ ] B3: `nginx -t` → "configuration is OK"
- [ ] B3: Log analysis completata — distribuzione codici HTTP calcolata
- [ ] B3: Logrotate configurato per i log di lab-status
- [ ] B4: Script `web_health_check.sh` eseguito — tutti gli endpoint OK
- [ ] B4: Interruzione di servizio simulata e rilevata dallo script
- [ ] B5: Certificato self-signed generato per lab-status
- [ ] B5: HTTPS configurato su porta 8443 con TLS 1.2/1.3
- [ ] B5: Script `cert_expiry_check.sh` eseguito — giorni alla scadenza verificati

### Governance (Part C)
- [ ] SOP-WEB-001 letta e compresa
- [ ] Script `web_email_health.sh` eseguito senza errori
- [ ] Sai classificare i problemi email/web in P1-P4 per GLPI

---

## Appendice A: Cheat Sheet Email e Web

### Email DNS Records
```bash
# Verifica MX
dig @192.168.56.10 lab.local MX

# Verifica SPF
dig @192.168.56.10 lab.local TXT | grep "v=spf1"

# Verifica DKIM
dig @192.168.56.10 selector1._domainkey.lab.local TXT

# Verifica DMARC
dig @192.168.56.10 _dmarc.lab.local TXT
```

### Test SMTP
```bash
# Test porta SMTP
nc -v mailserver.lab.local 25
Test-NetConnection -ComputerName mailserver.lab.local -Port 25

# Test invio con curl (SMTP auth)
# curl --url "smtp://mailserver:587" --ssl-reqd --user "user:pass" \
#      --mail-from "from@lab.local" --mail-rcpt "to@lab.local" \
#      --upload-file /tmp/message.txt

# Postfix status
sudo systemctl status postfix
sudo postqueue -p           # messaggi in coda
sudo postqueue -f           # forza delivery di tutti i messaggi in coda
```

### Nginx
```bash
# Syntax check
sudo nginx -t

# Ricarica senza downtime
sudo systemctl reload nginx

# Visualizza config attuale
sudo nginx -T 2>/dev/null | grep -A5 "server {"

# Log analysis
tail -f /var/log/nginx/access.log          # live
awk '$9 ~ /^5/' /var/log/nginx/access.log  # solo errori 5xx
awk '{print $9}' /var/log/nginx/access.log | sort | uniq -c | sort -rn  # distribuzione

# Test endpoint con timing
curl -w "DNS:%{time_namelookup}s TCP:%{time_connect}s TLS:%{time_appconnect}s TTFB:%{time_starttransfer}s Total:%{time_total}s\n" \
     -o /dev/null -s http://127.0.0.1:8090/
```

### SSL/TLS
```bash
# Verifica certificato da file
openssl x509 -in cert.crt -noout -text | grep -E "Subject:|Not After:|DNS:|IP:"

# Verifica certificato da connessione live
echo | openssl s_client -connect host:443 -servername host 2>/dev/null | openssl x509 -noout -dates

# Giorni alla scadenza
openssl x509 -in cert.crt -noout -enddate | cut -d= -f2 | xargs -I{} date -d {} +%s | \
    xargs -I{} bash -c "echo $(( ({} - $(date +%s)) / 86400 )) giorni alla scadenza"

# Test TLS versioni supportate
nmap --script ssl-enum-ciphers -p 443 host.lab.local
```

---

## Appendice B: Troubleshooting Email — Flowchart

```
Email non consegnata
        │
        ▼
Il mittente ha ricevuto NDR (Non-Delivery Report)?
   SÌ → leggi il codice errore SMTP:
        5xx permanente → destinatario sbagliato, dominio non esiste,
                         blacklist, SPF fail
        4xx temporaneo → server destinazione occupato, riprova tra poco
   NO  → continua ▼

La email è in coda SMTP?  [postqueue -p]
   SÌ → perché non viene consegnata? (Last error nel log)
        "Connection refused" → porta 25 bloccata (firewall)
        "Name or service not known" → DNS MX non risolve
        "Message rejected" → blacklist, SPF/DKIM fail
   NO  → continua ▼

Il filtro antispam l'ha bloccata?  [controlla quarantena]
   SÌ → release dalla quarantena, aggiungi mittente alla whitelist
   NO  → continua ▼

I record SPF/DKIM/DMARC sono corretti?
   dig TXT lab.local → verifica SPF
   dig TXT _dmarc.lab.local → verifica policy
   → se sbagliati: RFC per aggiornamento DNS
```

---

## Riferimenti

| Risorsa | Posizione | Contenuto |
|---|---|---|
| Documento sorgente | `../04-servizi-infrastruttura.md` (sez. Email e Web) | Configurazioni Exchange, Nginx, IIS |
| Tutorial ops03b | `tutorial_ops03_ch1b_linux_server_ops_lab.md` | Linux base (prerequisito Nginx) |
| Tutorial ops04a | `tutorial_ops04_ch1a_dns_dhcp_ntp_lab.md` | DNS (prerequisito per record email) |
| RFC 7208 (SPF) | tools.ietf.org/html/rfc7208 | SPF standard |
| RFC 6376 (DKIM) | tools.ietf.org/html/rfc6376 | DKIM standard |
| RFC 7489 (DMARC) | tools.ietf.org/html/rfc7489 | DMARC standard |
| OWASP TLS Cheat Sheet | cheatsheetseries.owasp.org/cheatsheets/TLS_Cipher_String_Cheat_Sheet.html | TLS best practices |

---

*Fine tutorial ops04c — Prossimo: `tutorial_ops04_ch2b_storage_database_ops_lab.md`*
