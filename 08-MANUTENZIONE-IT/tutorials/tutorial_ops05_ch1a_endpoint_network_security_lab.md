# Tutorial: Sicurezza Endpoint e Rete — Hardening, EDR, Firewall — Hands-On Lab

> **Documento di riferimento:** `05-sicurezza-operativa.md` (sezioni 2-3: Sicurezza Endpoint e Sicurezza Rete)
> **Dominio:** Security Operations — Protezione Infrastruttura
> **Ambito:** Defense in depth, hardening Windows/Linux, Windows Defender/EDR, gestione vulnerabilità (CVSS/SLA), firewall audit, segmentazione rete, fail2ban, nmap, certificati SSL
> **Durata lab:** 4-5 ore
> **Livello:** Intermedio-Avanzato — richiede ops03a (Windows Server) e ops03b (Linux)
> **Prerequisiti:** DC-LAB-01, SRV-LINUX-01, WKS-LAB-01 operativi; connettività rete lab
> **Ambiente:** DC-LAB-01 (Windows Defender, Windows Firewall, GPO), SRV-LINUX-01 (fail2ban, SSH hardening, ufw), WKS-LAB-01 (test client)

---

## Lab Environment Setup

```powershell
# Su DC-LAB-01 — verifica pre-lab
Write-Host "=== VERIFICA PRE-LAB SICUREZZA ==="

# Windows Defender attivo?
$defState = Get-MpComputerStatus
Write-Host "Defender: $($defState.AntivirusEnabled) | RealTime: $($defState.RealTimeProtectionEnabled)"

# Windows Firewall attivo su tutti i profili?
$fw = Get-NetFirewallProfile
$fw | Select-Object Name, Enabled | Format-Table -AutoSize

# Spazio per log di sicurezza
$secLog = Get-WinEvent -ListLog Security
Write-Host "Security log: $([math]::Round($secLog.FileSize/1MB,1)) MB / $([math]::Round($secLog.MaximumSizeInBytes/1MB,1)) MB max"
```

```bash
# Su SRV-LINUX-01 — verifica pre-lab
echo "=== VERIFICA PRE-LAB SICUREZZA LINUX ==="
echo "SSH config:"; sudo sshd -T 2>/dev/null | grep -E "permitrootlogin|passwordauthentication|port" || echo "[INFO] sshd non attivo o no accesso"
echo "fail2ban:";   systemctl is-active fail2ban 2>/dev/null && fail2ban-client status 2>/dev/null | head -5 || echo "[INFO] fail2ban non installato"
echo "ufw:";        sudo ufw status 2>/dev/null | head -5 || echo "[INFO] ufw non attivo"
```

---

## PART A: FONDAMENTI — Sicurezza Operativa come Processo Continuo

> La sicurezza non è un prodotto che compri e installi. È un processo che continui ogni giorno. Non esiste un'infrastruttura "sicura per sempre" — le minacce evolvono, le vulnerabilità vengono scoperte, le configurazioni derivano nel tempo. Un sistema sicuro oggi può avere una vulnerabilità critica domani quando esce un nuovo CVE. Il lavoro del team IT Operations è mantenere un livello di sicurezza adeguato, reagire velocemente alle nuove minacce, e verificare costantemente l'efficacia dei controlli.

---

### Concetto A1: Defense in Depth — Non Dipendere da un Unico Scudo

> **Analogia.** Un castello medievale non si difendeva con un solo muro. Aveva: un fossato (moat), mura esterne, torri di guardia, una porta a saracinesca, mura interne, e infine la torre del donjon. Ogni layer doveva essere superato da un attaccante. Se il fossato veniva attraversato, rimanevano ancora 4 layer. La sicurezza IT funziona allo stesso modo: ogni controllo fallisce — progetta il sistema assumendo che ogni singolo layer possa essere compromesso.

**I 5 layer di Defense in Depth:**

```
LAYER 1 — PERIMETRO DI RETE
  Firewall, IDS/IPS, WAF
  Blocca: accessi non autorizzati, traffico malevolo noto
  Può fallire: exploit 0-day, misconfiguration, attacchi insider

LAYER 2 — RETE INTERNA (Segmentazione)
  VLAN, micro-segmentazione, ACL inter-VLAN
  Blocca: movimento laterale dopo compromissione iniziale
  Può fallire: misconfiguration VLAN, VLAN hopping

LAYER 3 — HOST/ENDPOINT (Hardening)
  EDR/AV, Windows Firewall locale, AppLocker
  Blocca: malware, exploit locali, escalation di privilegio
  Può fallire: exploit kernel, vulnerabilità EDR, policy gap

LAYER 4 — APPLICAZIONE
  HTTPS/TLS, autenticazione forte, input validation
  Blocca: SQL injection, XSS, credential theft
  Può fallire: bug applicativi, weak crypto

LAYER 5 — DATI
  Crittografia a riposo (BitLocker/LUKS), backup cifrati
  Blocca: accesso diretto ai dati anche se tutto il resto è compromesso
  Può fallire: furto chiavi crittografiche

PRINCIPIO: Un attaccante che supera il Layer 1 trova il Layer 2.
           Ogni layer aggiunge tempo e costo per l'attaccante.
           Più layer → più probabilità di rilevare l'attacco.
```

**Il NIST Cybersecurity Framework — ciclo continuo:**

```
IDENTIFY    → Inventario asset, valutazione rischio
PROTECT     → Controlli preventivi (hardening, firewall, AV)
DETECT      → Monitoraggio, IDS/IPS, log analysis, SIEM
RESPOND     → Incident response, isolamento, containment
RECOVER     → Ripristino, lesson learned, miglioramento
    ↑                                                   |
    └───────────────────────────────────────────────────┘
                    (ciclo continuo)
```

---

### Concetto A2: EDR/AV — La Protezione Endpoint Moderna

> **Analogia.** Il vecchio antivirus è come una lista della polizia dei criminali noti: se il criminale è nella lista, viene arrestato. Se usa un alias nuovo, passa. L'EDR (Endpoint Detection and Response) è come un poliziotto con intelligenza artificiale che osserva il comportamento: "Quest'uomo è entrato nella banca, ha puntato una pistola alla cassiera, sta cercando di aprire la cassaforte — è una rapina!" — anche se non è nella lista.

**Antivirus tradizionale vs EDR:**

```
ANTIVIRUS TRADIZIONALE (signature-based):
  Meccanismo: database di firme (hash di malware noti)
  Confronta ogni file con il database
  Aggiornamento firme: ogni ora / ogni giorno
  
  PRO: leggero, accurato su malware noti
  CONTRO: fileless malware, 0-day exploit, nuove varianti passano

EDR (Endpoint Detection and Response):
  Meccanismo: analisi comportamentale + ML + telemetria
  Osserva: processi, file system, registry, rete, memoria
  Risposta automatica: isola l'endpoint, termina processi, rollback
  
  PRO: rileva attacchi senza firma, risposta automatica
  CONTRO: più risorse, falsi positivi iniziali, richiede tuning

In produzione oggi:
  Windows: Microsoft Defender for Endpoint (incluso in M365 E3/E5)
  Enterprise: CrowdStrike Falcon, SentinelOne, Sophos Intercept X
  Nel lab: Windows Defender (base EDR integrato)
```

**Metriche di salute EDR da monitorare:**

```
% endpoint con agente attivo e aggiornato → obiettivo: > 99%
Endpoint con definizioni > 48 ore obsolete → Alert immediato
Mean Time to Detect (MTTD) → quanto velocemente viene rilevato un attacco
Tasso falsi positivi → se > 5%: il sistema è mal configurato
Endpoint isolati/in quarantena → ogni isolamento richiede investigazione
```

---

### Concetto A3: Hardening — Ridurre la Superficie di Attacco

> **Analogia.** Un'auto ha molte possibilità di accesso: portiere, bagagliaio, sportello benzina, OBD-II porta diagnostica, sistema di infotainment. Un ladro sfrutta la porta più debole. L'hardening è come mettere serrature migliori ovunque, rimuovere gli accessori non utilizzati, e togliere tutto ciò che non serve. Un server "hardened" ha meno servizi, meno porte aperte, meno account, meno software = meno possibilità di attacco.

**CIS Benchmarks — lo standard di riferimento:**

```
CIS (Center for Internet Security) pubblica guide di hardening per:
  - Windows Server 2022
  - Ubuntu 22.04
  - Red Hat Enterprise Linux
  - macOS
  - AWS, Azure, GCP
  ... e centinaia di altri sistemi

LIVELLI:
  Level 1: raccomandato per tutti i sistemi
            impatto minimo sull'operatività
            ~85% delle organizzazioni dovrebbe applicarlo
  Level 2: sicurezza avanzata
            può impattare alcune funzionalità
            per ambienti ad alto rischio

PROCESSO DI APPLICAZIONE:
  1. Scarica benchmark CIS per il tuo OS
  2. Esegui CIS-CAT Pro (o equivalente open source) → score iniziale
  3. Pianifica remediation per criterio (impatto vs complessità)
  4. Applica tramite GPO (Windows) o Ansible (Linux) — MAI manualmente
  5. Ri-esegui score → obiettivo: > 85% conformità Level 1
  6. Ripeti ogni trimestre e dopo ogni major OS update
```

**Principi fondamentali di hardening:**

```
1. MINIMO PRIVILEGIO
   Ogni utente/processo/servizio ha SOLO i permessi necessari
   Nessun utente lavora come admin nel quotidiano
   Service account hanno solo i permessi del servizio che gestiscono

2. SUPERFICIE DI ATTACCO MINIMA
   Disabilita servizi non usati (Print Spooler su un DB server? No.)
   Chiudi porte non necessarie (netstat -tlnp → ogni porta è una potenziale entry)
   Rimuovi software non necessario (ogni pacchetto = potenziale vulnerabilità)

3. DEFAULT DENY
   Firewall: nega tutto, poi consenti solo il necessario (non viceversa)
   Whitelist applicazioni vs blacklist (AppLocker vs solo AV)
   
4. FAIL SECURELY
   Se un servizio crasha, il sistema deve restare sicuro
   Non esporre dati sensibili negli stack trace
   Rate limiting su login failure (blocca dopo N tentativi)
```

---

### Concetto A4: Vulnerability Management — Trovare e Correggere Prima dei Criminali

> **Analogia.** Le vulnerabilità sono come crepe nei muri della tua fortezza. Alcuni le scoprono per aiutarti a ripararle (ricercatori, vendor). Altri le cercano per entrare (criminali). Il vulnerability management è il processo di ispezionare le tue mura regolarmente, classificare le crepe per gravità, e ripararle prima che qualcuno le sfrutti.

**CVSS — il sistema di scoring delle vulnerabilità:**

```
CVSS (Common Vulnerability Scoring System): score da 0.0 a 10.0

COMPONENTI del punteggio base:
  Attack Vector (AV):      Network (N) > Adjacent (A) > Local (L) > Physical (P)
  Attack Complexity (AC):  Low (L) vs High (H)
  Privileges Required (PR): None (N) > Low (L) > High (H)
  User Interaction (UI):   None (N) vs Required (R)
  Scope (S):               Changed (C) vs Unchanged (U)
  Confidentiality (C):     High (H) / Low (L) / None (N)
  Integrity (I):           High (H) / Low (L) / None (N)
  Availability (A):        High (H) / Low (L) / None (N)

ESEMPI:
  Log4Shell (CVE-2021-44228): CVSS 10.0 — Remote, No Auth, No Interaction
  PrintNightmare (CVE-2021-34527): CVSS 8.8 — Local network, Low priv
  Vulnerabilità XSS tipica: CVSS 6.1 — Network, User Interaction required

SLA DI REMEDIATION:
  CVSS 9.0-10.0 CRITICO:  72 ore
  CVSS 7.0-8.9  ALTO:     7 giorni
  CVSS 4.0-6.9  MEDIO:    30 giorni
  CVSS 0.1-3.9  BASSO:    90 giorni
```

**Vulnerabilità CVSS 10.0 vs sistema interno CVSS 7.0:**

```
Non basta il CVSS score! Considera anche:

Esposizione: 
  Server esposto a Internet con CVSS 7.0 → PRIORITÀ ALTA
  Server isolato in rete interna con CVSS 10.0 → priorità relativa

Exploit pubblico disponibile:
  CVSS 6.5 con exploit su ExploitDB/Metasploit → patch URGENTE
  CVSS 9.0 senza exploit noto → più tempo per patch

Criticità sistema:
  DB che contiene dati PCI/PII → massima priorità
  Server di sviluppo interno → priorità più bassa

"Vulnerability Score × Exposure × Exploit availability × Business Impact"
```

---

### Concetto A5: Firewall e Segmentazione — Il Labirinto di Difesa

> **Analogia.** Il firewall di rete è come il portiere di un edificio che controlla chi entra. Ma se un ospite malevolo riesce a passare il portiere, può andare in qualsiasi stanza dell'edificio. La segmentazione di rete è come avere portieri anche ad ogni piano, ad ogni corridoio, ad ogni ufficio — il movimento è limitato anche dopo l'ingresso.

**Architettura di rete sicura — zone:**

```
INTERNET
    │
   [FW1 — Perimetro]
    │
   DMZ (server esposti)
   ├── Web Server (80/443 in)
   ├── Mail Server (25/587 in)
   └── VPN Gateway (500/4500 in)
    │
   [FW2 — Interno]
    │
   ├── VLAN-10: Server di produzione
   │   ├── Database Server (solo da App VLAN)
   │   └── Application Server
   ├── VLAN-20: Workstation utenti
   ├── VLAN-30: Server IT/Management
   └── VLAN-99: Quarantine (device non conformi)
```

**Regole firewall — principi:**

```
PRINCIPIO 1: Default Deny
  Nega tutto il traffico → poi apri solo ciò che serve
  Non: "Permetti tutto → poi blocca il cattivo"
  
PRINCIPIO 2: Least Privilege per il traffico
  Non aprire /24 intere se serve solo un IP specifico
  Non aprire "all ports" se serve solo 443
  
PRINCIPIO 3: Documentazione obbligatoria
  Ogni regola ha: ticket change, proprietario, scopo, scadenza (se temporanea)
  Regole senza documentazione = candidate alla rimozione

PRINCIPIO 4: Audit trimestrale
  Regole con hit count = 0 per 90 giorni → investigare, probabilmente rimuovere
  Regole con "any any allow" → vietate, richiedono giustificazione eccezionale
  
PRINCIPIO 5: Segregation of duties
  Chi chiede la regola ≠ chi la approva ≠ chi la implementa
  (nei team piccoli almeno peer review)
```

---
---

## PART B: OPERAZIONI — Hardening e Monitoraggio Sicurezza nel Lab

---

### Esercizio B1: Audit Windows Defender — Stato Reale della Protezione Endpoint

**Obiettivo.** Verificare e documentare lo stato completo di Windows Defender su DC-LAB-01, comprendere ogni parametro e identificare eventuali gap di protezione.

**Background.** Windows Defender in Windows Server 2022 include sia le capacità antivirus tradizionali (signature-based) che capacità EDR di base (analisi comportamentale). In produzione aziendale viene sostituito da Microsoft Defender for Endpoint (MDE) che aggiunge telemetria al cloud, threat intelligence, automated investigation. Tuttavia, anche il Defender base fornisce protezione significativa se configurato correttamente.

**Step 1 — Audit completo dello stato Defender:**

```powershell
# Su DC-LAB-01 come Administrator

# Panoramica completa
$status = Get-MpComputerStatus
Write-Host "=== WINDOWS DEFENDER AUDIT ===" -ForegroundColor Cyan
Write-Host ""

# Stato protezione
Write-Host "STATO PROTEZIONE:" -ForegroundColor Yellow
Write-Host "  Antivirus attivo:      $($status.AntivirusEnabled)"
Write-Host "  Protezione real-time:  $($status.RealTimeProtectionEnabled)"
Write-Host "  Anti-spyware:          $($status.AntispywareEnabled)"
Write-Host "  Protezione rete:       $($status.NISEnabled)"
Write-Host ""

# Definizioni
Write-Host "AGGIORNAMENTO DEFINIZIONI:" -ForegroundColor Yellow
Write-Host "  Versione definizioni:  $($status.AntivirusSignatureVersion)"
$signatureAge = (Get-Date) - $status.AntivirusSignatureLastUpdated
Write-Host "  Ultimo aggiornamento:  $($status.AntivirusSignatureLastUpdated)"
Write-Host "  Età definizioni:       $([math]::Round($signatureAge.TotalHours,1)) ore" -ForegroundColor $(if ($signatureAge.TotalHours -gt 48) {"Red"} else {"Green"})
Write-Host ""

# Ultima scansione
Write-Host "SCANSIONI:" -ForegroundColor Yellow
Write-Host "  Ultima full scan:      $($status.FullScanEndTime)"
Write-Host "  Ultima quick scan:     $($status.QuickScanEndTime)"
$lastScan = if ($status.FullScanEndTime -gt $status.QuickScanEndTime) { $status.FullScanEndTime } else { $status.QuickScanEndTime }
$scanAge = (Get-Date) - $lastScan
Write-Host "  Età ultima scan:       $([math]::Round($scanAge.TotalHours,1)) ore" -ForegroundColor $(if ($scanAge.TotalHours -gt 168) {"Red"} elseif ($scanAge.TotalHours -gt 72) {"Yellow"} else {"Green"})
```

**Output atteso:**
```
=== WINDOWS DEFENDER AUDIT ===

STATO PROTEZIONE:
  Antivirus attivo:      True
  Protezione real-time:  True
  Anti-spyware:          True
  Protezione rete:       True

AGGIORNAMENTO DEFINIZIONI:
  Versione definizioni:  1.409.xxx.0
  Ultimo aggiornamento:  [data recente]
  Età definizioni:       X ore

SCANSIONI:
  Ultima full scan:      [data]
  Ultima quick scan:     [data]
  Età ultima scan:       X ore
```

**Step 2 — Verifica esclusioni (potenziale misconfiguration):**

```powershell
# Esclusioni configurate — OGNI esclusione è un potenziale gap di sicurezza!
Write-Host "=== ESCLUSIONI DEFENDER ===" -ForegroundColor Yellow
Write-Host "(Ogni esclusione deve avere una ragione documentata)" -ForegroundColor Gray
Write-Host ""

$pref = Get-MpPreference

Write-Host "Cartelle escluse:" -ForegroundColor Cyan
if ($pref.ExclusionPath) {
    $pref.ExclusionPath | ForEach-Object { Write-Host "  [!] $_" -ForegroundColor Red }
} else {
    Write-Host "  Nessuna" -ForegroundColor Green
}

Write-Host "Estensioni escluse:" -ForegroundColor Cyan
if ($pref.ExclusionExtension) {
    $pref.ExclusionExtension | ForEach-Object { Write-Host "  [!] *.$_" -ForegroundColor Yellow }
} else {
    Write-Host "  Nessuna" -ForegroundColor Green
}

Write-Host "Processi esclusi:" -ForegroundColor Cyan
if ($pref.ExclusionProcess) {
    $pref.ExclusionProcess | ForEach-Object { Write-Host "  [!] $_" -ForegroundColor Yellow }
} else {
    Write-Host "  Nessuna" -ForegroundColor Green
}
```

**Nota sulle esclusioni:** In produzione, alcune esclusioni sono necessarie (es: cartelle di DB SQL Server per evitare falsi positivi e lock sui file). Ma ogni esclusione riduce la protezione. Regola: esclusioni minime, documentate in CMDB, riviste ogni 90 giorni.

**Step 3 — Minacce rilevate e in quarantena:**

```powershell
# Quarantena
Write-Host "=== ELEMENTI IN QUARANTENA ===" -ForegroundColor Yellow
$quarantine = Get-MpThreat
if ($quarantine) {
    $quarantine | Select-Object ThreatID, ThreatName, SeverityID, Resources | Format-Table -AutoSize
    Write-Host "[ATTENZIONE] $($quarantine.Count) minacce rilevate — investigare!" -ForegroundColor Red
} else {
    Write-Host "  Nessuna minaccia in quarantena" -ForegroundColor Green
}

# Storia delle minacce
Write-Host ""
Write-Host "=== STORICO DETECTION (ultime 30 gg) ===" -ForegroundColor Yellow
$history = Get-MpThreatDetection | Where-Object {$_.InitialDetectionTime -gt (Get-Date).AddDays(-30)}
Write-Host "  Minacce rilevate: $($history.Count)"
if ($history.Count -gt 0) {
    $history | Select-Object ThreatID, InitialDetectionTime, ActionSuccess | 
        Sort-Object InitialDetectionTime -Descending | 
        Select-Object -First 10 | Format-Table -AutoSize
}
```

**Checkpoint di verifica B1:**
- [ ] Defender è attivo con protezione real-time
- [ ] Definizioni hanno meno di 48 ore
- [ ] Ultima scansione ha meno di 7 giorni
- [ ] Esclusioni documentate e giustificate
- [ ] Nessuna minaccia in quarantena non investigata

---

### Esercizio B2: Hardening SSH su SRV-LINUX-01 — Chiudere le Porte Pericolose

**Obiettivo.** Applicare la configurazione SSH sicura su SRV-LINUX-01 secondo le best practice CIS Level 1, testare le modifiche, e capire perché ogni parametro è importante.

**Background.** SSH è il servizio più attaccato su Internet. I bot eseguono continuamente tentativi di login (brute force) su ogni server con porta 22 aperta. La configurazione default di sshd è funzionale ma non sicura: permette login root, accetta password deboli, non ha limiti di tentativi. Un server esposto con SSH configurato di default viene compromesso in minuti tramite dizionario di password.

**Step 1 — Backup e audit configurazione attuale:**

```bash
# Su SRV-LINUX-01 come lab-admin

echo "=== AUDIT SSH PRE-HARDENING ==="
echo ""

# Configurazione attiva (include tutti i defaults)
sudo sshd -T 2>/dev/null | grep -E "^(port|permitrootlogin|passwordauthentication|pubkeyauthentication|permitemptypasswords|x11forwarding|maxauthtries|protocol|logingracetime|clientalivecountmax)" | sort

echo ""
echo "=== Utenti con login SSH possibile ==="
# Utenti con shell valida (possono fare login)
getent passwd | awk -F: '$7 !~ /nologin|false|shutdown|halt/ {print $1, "→", $7}'

echo ""
echo "=== File authorized_keys esistenti ==="
find /home /root -name "authorized_keys" 2>/dev/null
```

**Step 2 — Applica hardening SSH:**

```bash
# Backup config esistente
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup.$(date +%Y%m%d)

# Scrivi configurazione sicura
sudo tee /etc/ssh/sshd_config.d/99-hardening.conf > /dev/null <<'EOF'
# SSH Hardening — CIS Ubuntu 22.04 Level 1
# Applicato: 2026-07-15 — lab-admin

# Versione protocollo (SSH2 only, SSH1 è deprecato)
Protocol 2

# Porta (standard per lab, in produzione cambia a porta non-standard)
Port 22

# Autenticazione
PermitRootLogin no
PasswordAuthentication yes
PubkeyAuthentication yes
PermitEmptyPasswords no
ChallengeResponseAuthentication no

# Limiti
MaxAuthTries 3
MaxSessions 5
LoginGraceTime 60

# Riduci superficie di attacco
X11Forwarding no
AllowTcpForwarding no
PermitUserEnvironment no
UseDNS no

# Keep-alive per sessioni abbandonate
ClientAliveInterval 300
ClientAliveCountMax 2

# Algoritmi sicuri (elimina algoritmi deboli)
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group14-sha256
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com

# Logging
SyslogFacility AUTH
LogLevel VERBOSE
EOF

echo "File scritto. Verifica sintassi..."
sudo sshd -t && echo "[OK] Configurazione sintatticamente corretta" || echo "[ERRORE] Problema nella config!"
```

**Step 3 — Test, ricarica e verifica:**

```bash
# Ricarica sshd (NON restart — per non disconnettere sessioni attive)
sudo systemctl reload sshd
echo "sshd ricaricato. Status:"
systemctl status sshd | head -5

echo ""
echo "=== VERIFICA POST-HARDENING ==="
sudo sshd -T 2>/dev/null | grep -E "^(permitrootlogin|passwordauthentication|maxauthtries|x11forwarding|allowtcpforwarding|logingracetime)" | sort

echo ""
echo "=== TEST: login root deve fallire ==="
# Da WKS-LAB-01: ssh root@192.168.56.20
# Deve rispondere: "Permission denied (publickey)"
echo "Eseguire da WKS-LAB-01: ssh root@192.168.56.20"
echo "Risultato atteso: 'Permission denied'"
```

**Step 4 — Setup autenticazione a chiave pubblica (più sicuro delle password):**

```bash
# Su SRV-LINUX-01 — prepara per chiave pubblica
echo "=== SETUP CHIAVE SSH PER lab-admin ==="

# Genera coppia di chiavi (se non esistente)
if [ ! -f ~/.ssh/id_ed25519 ]; then
    ssh-keygen -t ed25519 -C "lab-admin@srv-linux-01-$(date +%Y%m%d)" -f ~/.ssh/id_ed25519 -N ""
    echo "[OK] Chiave generata: ~/.ssh/id_ed25519"
else
    echo "[INFO] Chiave esistente: ~/.ssh/id_ed25519"
fi

# Visualizza chiave pubblica (da copiare su altri host)
echo ""
echo "Chiave pubblica (copia per authorized_keys di altri host):"
cat ~/.ssh/id_ed25519.pub

# Imposta permessi corretti (SSH rifiuta se i permessi sono troppo aperti)
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519 2>/dev/null || true
chmod 644 ~/.ssh/id_ed25519.pub 2>/dev/null || true
[ -f ~/.ssh/authorized_keys ] && chmod 600 ~/.ssh/authorized_keys
echo "[OK] Permessi .ssh corretti"
```

**Checkpoint di verifica B2:**
- [ ] PermitRootLogin è `no`
- [ ] MaxAuthTries è `3`
- [ ] X11Forwarding è `no`
- [ ] `sudo sshd -t` restituisce zero errori
- [ ] Login da un'altra VM come lab-admin funziona
- [ ] Login come root viene rifiutato

---

### Esercizio B3: fail2ban — Protezione Automatica contro Brute Force

**Obiettivo.** Installare e configurare fail2ban su SRV-LINUX-01 per bloccare automaticamente IP che tentano brute force su SSH.

**Background.** fail2ban è un sistema di intrusion prevention che analizza i log in tempo reale. Quando rileva N tentativi di login falliti da un IP entro M secondi, aggiunge una regola iptables (o nftables) per bloccare quell'IP per X secondi. Blocca efficacemente i bot di brute force che provano milioni di password: dopo 5 tentativi, l'IP viene bloccato per 10 minuti, rendendo il brute force computazionalmente impossibile.

**Step 1 — Installazione e configurazione:**

```bash
# Installa fail2ban
sudo apt install -y fail2ban

# Crea configurazione locale (non modificare jail.conf — viene sovrascritto dagli update)
sudo tee /etc/fail2ban/jail.local > /dev/null <<'EOF'
[DEFAULT]
# Ban IP per 10 minuti al primo ban, progressivo dopo
bantime  = 10m
# Finestra di osservazione
findtime = 5m
# Numero tentativi prima del ban
maxretry = 5
# Backend per lettura log
backend  = systemd
# Azione di ban: blocca con iptables + notifica log
banaction = iptables-multiport
# Invia alert a syslog (in produzione: email all'admin)
action = %(action_mwl)s

[sshd]
enabled  = true
port     = ssh
logpath  = %(sshd_log)s
maxretry = 5
bantime  = 1h
EOF

sudo systemctl enable fail2ban
sudo systemctl restart fail2ban

echo "fail2ban status:"
sudo fail2ban-client status
```

**Step 2 — Verifica funzionamento:**

```bash
# Visualizza jail SSH attivo
sudo fail2ban-client status sshd

# Visualizza log fail2ban in tempo reale
sudo journalctl -u fail2ban -f --no-pager &
F2B_PID=$!

# (Da WKS-LAB-01, simula 6 tentativi falliti di login SSH)
# Eseguire da WKS-LAB-01: for i in {1..6}; do ssh baduser@192.168.56.20 2>/dev/null; done

echo ""
echo "=== STATO BAN ATTIVI (dopo test) ==="
sleep 5
sudo fail2ban-client status sshd | grep -E "Currently banned|IP list"

# Ferma il log tail
kill $F2B_PID 2>/dev/null

echo ""
echo "=== SBLOCCA UN IP (esempio) ==="
echo "Per sbloccare un IP: sudo fail2ban-client set sshd unbanip [IP]"
echo "Per ban manuale:     sudo fail2ban-client set sshd banip [IP]"
```

**Step 3 — Test simulato di brute force:**

```bash
# Da SRV-LINUX-01 stessa — simula tentativi falliti (popola log SSH)
echo "Simulazione tentativo login fallito su localhost..."
for i in $(seq 1 6); do
    # Tentativo con password sbagliata (non interattivo)
    sshpass -p "wrongpassword" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=2 \
        notexistentuser@127.0.0.1 2>/dev/null || true
    echo "Tentativo $i fatto"
    sleep 1
done

echo ""
echo "=== VERIFICA BAN ==="
sudo fail2ban-client status sshd

echo ""
echo "=== LOG FAIL2BAN ULTIMI EVENTI ==="
sudo journalctl -u fail2ban -n 20 --no-pager
```

**Output atteso dopo il test:**
```
Status for the jail: sshd
|- Filter
|  |- Currently failed: 0
|  |- Total failed:     6
|  `- File list:        /var/log/auth.log
`- Actions
   |- Currently banned: 1
   |- Total banned:     1
   `- Banned IP list:   127.0.0.1
```

**Checkpoint di verifica B3:**
- [ ] fail2ban è attivo (`systemctl is-active fail2ban` → `active`)
- [ ] Jail `sshd` è enabled
- [ ] Dopo 6 tentativi, l'IP risulta nei Banned
- [ ] `sudo fail2ban-client set sshd unbanip 127.0.0.1` sblocca correttamente

---

### Esercizio B4: Windows Firewall Audit — Regole e Profili

**Obiettivo.** Auditare le regole del Windows Firewall su DC-LAB-01, identificare regole permissive o non necessarie, e applicare una regola restrittiva per il servizio RDP.

**Background.** Windows Firewall gestisce 3 profili indipendenti: Domain (quando il computer è connesso al dominio), Private (rete casa/ufficio), Public (rete pubblica). Su un Domain Controller, il profilo Domain è quello attivo. Le regole built-in di Windows Server aprono molte porte necessarie per il funzionamento di AD, DNS, DHCP ecc. L'audit serve a identificare regole non necessarie che aumentano la superficie di attacco.

**Step 1 — Panoramica profili firewall:**

```powershell
# Su DC-LAB-01 come Administrator

Write-Host "=== WINDOWS FIREWALL — PROFILI ===" -ForegroundColor Cyan

Get-NetFirewallProfile | ForEach-Object {
    $color = if ($_.Enabled) { "Green" } else { "Red" }
    Write-Host "Profilo: $($_.Name)" -ForegroundColor Yellow
    Write-Host "  Abilitato:        $($_.Enabled)" -ForegroundColor $color
    Write-Host "  Default inbound:  $($_.DefaultInboundAction)"
    Write-Host "  Default outbound: $($_.DefaultOutboundAction)"
    Write-Host "  Log allowed:      $($_.LogAllowed)"
    Write-Host "  Log blocked:      $($_.LogBlocked)"
    Write-Host "  Log path:         $($_.LogFileName)"
    Write-Host ""
}
```

**Step 2 — Audit regole permissive:**

```powershell
Write-Host "=== REGOLE INBOUND ATTIVE ===" -ForegroundColor Cyan

# Regole abilitate in ingresso, ordinate per porta
$rules = Get-NetFirewallRule -Direction Inbound -Enabled True -Action Allow |
    Where-Object { $_.Profile -eq "Domain" -or $_.Profile -eq "Any" } |
    Sort-Object DisplayName

Write-Host "Totale regole Allow Inbound attive: $($rules.Count)"
Write-Host ""

# Identifica regole potenzialmente pericolose (Any remote address, Any port)
Write-Host "=== REGOLE CON REMOTE ADDRESS = ANY (analisi critica) ===" -ForegroundColor Yellow
foreach ($rule in $rules) {
    $filter = Get-NetFirewallAddressFilter -AssociatedNetFirewallRule $rule
    $portFilter = Get-NetFirewallPortFilter -AssociatedNetFirewallRule $rule
    
    if ($filter.RemoteAddress -eq "Any") {
        $localPort = if ($portFilter.LocalPort -eq "Any") { "TUTTE le porte" } else { $portFilter.LocalPort }
        Write-Host "  [?] $($rule.DisplayName)"
        Write-Host "      Porta: $localPort"
    }
}
```

**Step 3 — Restringi l'accesso RDP:**

```powershell
# RDP (3389) è aperto ma dovrebbe essere limitato alla rete lab
# Verifica regola RDP esistente
$rdpRule = Get-NetFirewallRule -DisplayName "Remote Desktop - User Mode (TCP-In)" -ErrorAction SilentlyContinue
if ($rdpRule) {
    $rdpAddr = Get-NetFirewallAddressFilter -AssociatedNetFirewallRule $rdpRule
    Write-Host "Regola RDP attuale:"
    Write-Host "  Remote Address: $($rdpAddr.RemoteAddress)"
}

# Modifica: limita RDP alla sola rete del lab
Write-Host ""
Write-Host "Limitando RDP alla rete lab 192.168.56.0/24..."
Set-NetFirewallRule -DisplayName "Remote Desktop - User Mode (TCP-In)" `
    -RemoteAddress "192.168.56.0/24" `
    -Enabled True

# Verifica modifica
$rdpAddr = Get-NetFirewallAddressFilter -AssociatedNetFirewallRule (
    Get-NetFirewallRule -DisplayName "Remote Desktop - User Mode (TCP-In)"
)
Write-Host "Regola RDP aggiornata:"
Write-Host "  Remote Address: $($rdpAddr.RemoteAddress)" -ForegroundColor Green

# Log degli accessi al firewall
$profile = Get-NetFirewallProfile -Profile Domain
if (-not $profile.LogBlocked) {
    Write-Host ""
    Write-Host "Abilitando log connessioni bloccate..."
    Set-NetFirewallProfile -Profile Domain -LogBlocked True -LogMaxSizeKilobytes 4096
    Write-Host "[OK] Log firewall abilitato: $($profile.LogFileName)"
}
```

**Step 4 — Crea regola personalizzata per il servizio GLPI:**

```powershell
# Permetti accesso a GLPI (porta 8080) solo dalla rete lab
New-NetFirewallRule `
    -DisplayName "GLPI Web Interface Lab" `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort 8080 `
    -RemoteAddress "192.168.56.0/24" `
    -Action Allow `
    -Profile Domain `
    -Description "GLPI accesso limitato alla rete lab - CHG-LAB-001" `
    -ErrorAction SilentlyContinue

Write-Host "Regola GLPI creata. Verifica:"
Get-NetFirewallRule -DisplayName "GLPI Web Interface Lab" | Select-Object DisplayName, Enabled, Action
```

**Checkpoint di verifica B4:**
- [ ] Tutti e 3 i profili firewall sono abilitati
- [ ] RDP è limitato a 192.168.56.0/24
- [ ] Log connessioni bloccate è attivo
- [ ] Regola GLPI creata e visibile

---

### Esercizio B5: Scansione Vulnerabilità con nmap — Vedere la Superficie di Attacco

**Obiettivo.** Eseguire una scansione di base della rete lab con nmap da WKS-LAB-01, comprendere cosa un attaccante vede dall'esterno, e confrontare con lo stato atteso.

**Background.** nmap (Network Mapper) è lo strumento standard per l'enumerazione di rete. Viene usato sia dagli attaccanti (per trovare target) che dai defender (per scoprire cosa è esposto). Conoscere cosa un attaccante vede della tua rete è il primo passo per ridurre la superficie di attacco. In produzione, si usano scanner più avanzati (Nessus, OpenVAS, Qualys) che oltre alle porte identificano le vulnerabilità note (CVE) sui servizi rilevati.

**Step 1 — Installa nmap su WKS-LAB-01:**

```powershell
# Su WKS-LAB-01 come lab-user (o Administrator)
# Scarica e installa nmap (o usa winget se disponibile)

# Verifica se già installato
if (Get-Command nmap -ErrorAction SilentlyContinue) {
    Write-Host "[OK] nmap già installato: $(nmap --version | head -1)"
} else {
    Write-Host "Installa nmap da: https://nmap.org/download.html"
    Write-Host "Oppure con winget: winget install Insecure.Nmap"
    # winget install Insecure.Nmap
}
```

```bash
# Alternativa: esegui da SRV-LINUX-01 (nmap disponibile su Linux)
sudo apt install -y nmap
nmap --version | head -1
```

**Step 2 — Scansione host discovery della rete lab:**

```bash
# Da SRV-LINUX-01 — scansiona la rete 192.168.56.0/24
echo "=== HOST DISCOVERY ==="
sudo nmap -sn 192.168.56.0/24 -oG -

echo ""
echo "=== HOST ATTIVI TROVATI ==="
sudo nmap -sn 192.168.56.0/24 | grep "Nmap scan report"
```

**Step 3 — Scansione porte DC-LAB-01:**

```bash
# Scansione porte su DC-LAB-01 (top 1000 porte TCP)
echo "=== SCANSIONE PORTE DC-LAB-01 ==="
sudo nmap -sV -T4 192.168.56.10 -p 21,22,25,53,80,135,139,443,445,389,636,3389,5985,8080 \
    --open --reason 2>/dev/null

echo ""
echo "Interpretazione:"
echo "  53/tcp  open → DNS server attivo"
echo "  389/tcp open → LDAP (Active Directory)"
echo "  445/tcp open → SMB (condivisione file)"
echo "  3389/tcp open → RDP (accesso remoto)"
echo "  135/tcp open → RPC Endpoint Mapper"
```

**Output atteso (parziale):**
```
PORT     STATE SERVICE       VERSION
53/tcp   open  domain        Microsoft DNS 10.0.x
135/tcp  open  msrpc         Microsoft Windows RPC
139/tcp  open  netbios-ssn   Microsoft Windows netbios-ssn
389/tcp  open  ldap          Microsoft Windows Active Directory LDAP
445/tcp  open  microsoft-ds  ?
3389/tcp open  ms-wbt-server Microsoft Terminal Services
```

**Step 4 — Confronta con baseline:**

```bash
# Scansione SRV-LINUX-01
echo "=== SCANSIONE PORTE SRV-LINUX-01 ==="
sudo nmap -sV -T4 192.168.56.20 -p 22,80,443,631,2049,3306,8080 --open 2>/dev/null

echo ""
echo "Porte ATTESE su SRV-LINUX-01:"
echo "  22/tcp  → SSH"
echo "  8080/tcp → GLPI"
echo ""
echo "Porte NON attese (da investigare se aperte):"
echo "  3306/tcp → MariaDB esposto direttamente? NON dovrebbe essere accessibile dall'esterno"
echo "  2049/tcp → NFS aperto su tutte le interfacce? Verifica exports"

# Verifica specifica NFS
echo ""
echo "=== VERIFICA EXPORT NFS ==="
showmount -e 192.168.56.20 2>/dev/null || echo "[INFO] NFS non attivo o non risponde"
```

**Checkpoint di verifica B5:**
- [ ] nmap installato e funzionante
- [ ] Tutti e 3 gli host lab sono rilevati in host discovery
- [ ] Le porte aperte corrispondono ai servizi configurati
- [ ] Nessuna porta inattesa aperta (es: MariaDB 3306 non accessibile da fuori)

---

### Esercizio B6: Hardening Windows — Checklist CIS Level 1

**Obiettivo.** Applicare e verificare i controlli CIS Level 1 fondamentali su DC-LAB-01.

**Background.** Il CIS Benchmark per Windows Server 2022 contiene centinaia di controlli. Qui applichiamo i più critici per il lab: disabilitazione SMB1, Credential Guard, configurazione PowerShell, LLMNR/NetBIOS.

**Step 1 — Verifica e disabilita SMB1:**

```powershell
# Su DC-LAB-01 come Administrator

Write-Host "=== CIS BENCHMARK — VERIFICA SMB1 ===" -ForegroundColor Cyan

# Controlla stato SMB1
$smb1Server = Get-SmbServerConfiguration | Select-Object EnableSMB1Protocol
$smb1Client = Get-WindowsOptionalFeature -Online -FeatureName SMB1Protocol 2>/dev/null

Write-Host "SMB1 Server attivo: $($smb1Server.EnableSMB1Protocol)"
Write-Host "SMB1 Feature Windows: $($smb1Client.State)"

if ($smb1Server.EnableSMB1Protocol) {
    Write-Host "[CRITICO] SMB1 è attivo — vulnerabile a EternalBlue/WannaCry!" -ForegroundColor Red
    Write-Host "Disabilitazione in corso..."
    
    Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force
    Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart
    
    Write-Host "[OK] SMB1 disabilitato" -ForegroundColor Green
} else {
    Write-Host "[OK] SMB1 già disabilitato" -ForegroundColor Green
}
```

**Step 2 — PowerShell Execution Policy e logging:**

```powershell
# Execution Policy — RemoteSigned per sicurezza
$policy = Get-ExecutionPolicy -Scope LocalMachine
Write-Host "PowerShell Execution Policy: $policy"

if ($policy -eq "Unrestricted" -or $policy -eq "Bypass") {
    Write-Host "[WARN] Policy troppo permissiva — impostando RemoteSigned" -ForegroundColor Yellow
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine -Force
    Write-Host "[OK] Impostata RemoteSigned" -ForegroundColor Green
}

# Abilita PowerShell Script Block Logging (registra TUTTI gli script eseguiti)
$regPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging"
if (-not (Test-Path $regPath)) {
    New-Item -Path $regPath -Force | Out-Null
}
Set-ItemProperty -Path $regPath -Name "EnableScriptBlockLogging" -Value 1 -Type DWord
Write-Host "[OK] Script Block Logging abilitato — ogni script PowerShell viene loggato in Event Log"
```

**Step 3 — Disabilita LLMNR e NetBIOS (prevenzione MITM):**

```powershell
# LLMNR (Link-Local Multicast Name Resolution) usato in attacchi Responder/NTLM capture
$llmnrPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient"
if (-not (Test-Path $llmnrPath)) {
    New-Item -Path $llmnrPath -Force | Out-Null
}
Set-ItemProperty -Path $llmnrPath -Name "EnableMulticast" -Value 0 -Type DWord
Write-Host "[OK] LLMNR disabilitato"

# NetBIOS over TCP/IP — disabilita su tutte le interfacce
Get-WmiObject Win32_NetworkAdapterConfiguration | 
    Where-Object {$_.IPEnabled -eq $true} | 
    ForEach-Object {
        $_.SetTcpipNetbios(2) | Out-Null  # 2 = Disable NetBIOS
        Write-Host "[OK] NetBIOS disabilitato su $($_.Description)"
    }
```

**Step 4 — Report conformità CIS riassuntivo:**

```powershell
Write-Host ""
Write-Host "=== REPORT CONFORMITÀ CIS LEVEL 1 (SUBSET LAB) ===" -ForegroundColor Cyan
Write-Host ""

$checks = @(
    @{Name="SMB1 disabilitato"; 
      Actual=(Get-SmbServerConfiguration).EnableSMB1Protocol -eq $false;
      Expected=$true},
    @{Name="PS Script Block Logging"; 
      Actual=(Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" -ErrorAction SilentlyContinue).EnableScriptBlockLogging -eq 1;
      Expected=$true},
    @{Name="LLMNR disabilitato"; 
      Actual=(Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" -ErrorAction SilentlyContinue).EnableMulticast -eq 0;
      Expected=$true},
    @{Name="Firewall Domain abilitato"; 
      Actual=(Get-NetFirewallProfile -Profile Domain).Enabled;
      Expected=$true},
    @{Name="Defender real-time attivo"; 
      Actual=(Get-MpComputerStatus).RealTimeProtectionEnabled;
      Expected=$true}
)

$passed = 0
foreach ($check in $checks) {
    $status = if ($check.Actual -eq $check.Expected) { "[PASS]"; $passed++ } else { "[FAIL]" }
    $color  = if ($check.Actual -eq $check.Expected) { "Green" } else { "Red" }
    Write-Host "  $status $($check.Name)" -ForegroundColor $color
}

Write-Host ""
Write-Host "Risultato: $passed/$($checks.Count) controlli conformi" -ForegroundColor $(if ($passed -eq $checks.Count) {"Green"} else {"Yellow"})
```

**Checkpoint di verifica B6:**
- [ ] SMB1 è disabilitato (Get-SmbServerConfiguration mostra False)
- [ ] Script Block Logging attivo nel Registry
- [ ] LLMNR disabilitato
- [ ] Il report finale mostra 5/5 PASS

---
---

## PART C: SISTEMATIZZARE — Dalla Verifica Manuale al Processo Ripetibile

---

### Progetto C1: SOP-SEC-001 — Security Health Check Settimanale

> **Scopo:** Procedure operative standard per la verifica settimanale della sicurezza dell'infrastruttura lab. Da eseguire ogni lunedì mattina prima dell'inizio delle attività, o integrato come task automatico settimanale tramite Task Scheduler / cron.

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  SOP-SEC-001 — Security Health Check Settimanale                            ║
║  Versione: 1.0 | Autore: lab-admin | Data: 2026-07-15                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  SCOPO                                                                       ║
║  Verificare lo stato di sicurezza dell'infrastruttura IT su base             ║
║  settimanale. Identificare deviazioni dalla baseline prima che               ║
║  diventino incidenti.                                                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  SCOPE                                                                       ║
║  DC-LAB-01 (Windows Server 2022 / AD)                                        ║
║  SRV-LINUX-01 (Ubuntu 22.04 / servizi Linux)                                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  FREQUENZA: Settimanale (lunedì, prima delle 09:00)                          ║
║  DURATA ATTESA: 20-30 minuti (manuale) / automatico con script               ║
║  ESCALATION: Qualsiasi CRITICO → aprire incidente P1 entro 15 minuti        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  CHECKLIST                                                                   ║
║                                                                              ║
║  PARTE 1 — ENDPOINT (DC-LAB-01, PowerShell)                                  ║
║  [ ] 1.1 Windows Defender attivo e definizioni < 48 ore                      ║
║  [ ] 1.2 Nessuna minaccia in quarantena non investigata                      ║
║  [ ] 1.3 Ultima scansione < 7 giorni                                         ║
║  [ ] 1.4 SMB1 rimane disabilitato                                            ║
║  [ ] 1.5 Windows Firewall attivo su tutti i profili                          ║
║  [ ] 1.6 Patch pendenti: nessuna CRITICA/ALTA non applicata > SLA            ║
║                                                                              ║
║  PARTE 2 — ACCESSI E ACCOUNT (DC-LAB-01)                                     ║
║  [ ] 2.1 Nessun account admin non autorizzato in Domain Admins               ║
║  [ ] 2.2 Account disabilitati dall'ultima settimana: verificare motivo       ║
║  [ ] 2.3 Nessun login fallito anomalo (> 50 in un'ora per un account)        ║
║  [ ] 2.4 Guest account disabilitato                                          ║
║                                                                              ║
║  PARTE 3 — LINUX HARDENING (SRV-LINUX-01)                                    ║
║  [ ] 3.1 fail2ban attivo e jail SSH enabled                                  ║
║  [ ] 3.2 IP bannati nell'ultima settimana: documentare se > 100              ║
║  [ ] 3.3 SSH config intatta (PermitRootLogin no, MaxAuthTries 3)             ║
║  [ ] 3.4 Aggiornamenti sicurezza disponibili: pianificare patch              ║
║  [ ] 3.5 Nessun processo anomalo in ascolto su nuove porte                  ║
║                                                                              ║
║  PARTE 4 — CERTIFICATI (verificare mensile, non settimanale)                 ║
║  [ ] 4.1 Certificati in scadenza entro 30 giorni: pianificare rinnovo       ║
║  [ ] 4.2 Certificati in scadenza entro 7 giorni: rinnovo urgente            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  OUTPUT                                                                      ║
║  Completare report su ticket GLPI categoria "Security Health Check"          ║
║  Stato: VERDE (tutti OK) / GIALLO (warning, piano azione) / ROSSO (critico) ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

### Progetto C2: Script — `security_health.sh` (SRV-LINUX-01)

```bash
#!/usr/bin/env bash
# security_health.sh — Security health check per SRV-LINUX-01
# Uso: sudo ./security_health.sh [--json]
# Genera report sicurezza e restituisce exit 0 (OK), 1 (WARNING), 2 (CRITICO)

set -euo pipefail

readonly SCRIPT_VERSION="1.0.0"
readonly TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
JSON_OUTPUT=false
[[ "${1:-}" == "--json" ]] && JSON_OUTPUT=true

# Codici colore
RED='\033[0;31m'; YELLOW='\033[1;33m'; GREEN='\033[0;32m'; NC='\033[0m'

# Status globale
GLOBAL_STATUS=0  # 0=OK, 1=WARNING, 2=CRITICO
FINDINGS=()

log_ok()   { [[ "$JSON_OUTPUT" == false ]] && echo -e "${GREEN}[OK]${NC}    $1" || true; }
log_warn() { [[ "$JSON_OUTPUT" == false ]] && echo -e "${YELLOW}[WARN]${NC}  $1" || true; FINDINGS+=("WARN: $1"); [[ $GLOBAL_STATUS -lt 1 ]] && GLOBAL_STATUS=1; }
log_crit() { [[ "$JSON_OUTPUT" == false ]] && echo -e "${RED}[CRIT]${NC}  $1" || true; FINDINGS+=("CRIT: $1"); GLOBAL_STATUS=2; }
log_info() { [[ "$JSON_OUTPUT" == false ]] && echo -e "        $1" || true; }

print_header() {
    [[ "$JSON_OUTPUT" == false ]] || return
    echo ""
    echo "═══════════════════════════════════════════════════════"
    echo "  Security Health Check — SRV-LINUX-01"
    echo "  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "═══════════════════════════════════════════════════════"
}

# ─── SEZIONE 1: SERVIZI DI SICUREZZA ────────────────────────────────────────

check_security_services() {
    [[ "$JSON_OUTPUT" == false ]] && echo "" && echo "── Servizi di Sicurezza ──"
    
    # fail2ban
    if systemctl is-active fail2ban &>/dev/null; then
        log_ok "fail2ban: attivo"
        
        # Verifica jail SSH
        if fail2ban-client status sshd &>/dev/null 2>&1; then
            local banned
            banned=$(fail2ban-client status sshd 2>/dev/null | grep "Currently banned:" | awk '{print $NF}')
            log_ok "fail2ban jail SSH: attivo (${banned:-0} IP bannati)"
            
            local total_banned
            total_banned=$(fail2ban-client status sshd 2>/dev/null | grep "Total banned:" | awk '{print $NF}')
            if [[ "${total_banned:-0}" -gt 100 ]]; then
                log_warn "fail2ban: ${total_banned} ban totali questa settimana — verifica se c'è un attacco in corso"
            fi
        else
            log_warn "fail2ban: jail SSH non attiva — SSH non è protetto da brute force"
        fi
    else
        log_crit "fail2ban: NON attivo — installare e configurare"
    fi
    
    # ufw
    local ufw_status
    ufw_status=$(ufw status 2>/dev/null | head -1 | awk '{print $2}')
    if [[ "$ufw_status" == "active" ]]; then
        log_ok "ufw firewall: attivo"
    else
        log_warn "ufw firewall: inattivo — considera abilitazione per Defense in Depth"
    fi
    
    # AppArmor
    if systemctl is-active apparmor &>/dev/null; then
        local aa_profiles
        aa_profiles=$(aa-status 2>/dev/null | grep "profiles are in enforce mode" | awk '{print $1}')
        log_ok "AppArmor: attivo (${aa_profiles:-?} profili enforce)"
    else
        log_warn "AppArmor: non attivo"
    fi
}

# ─── SEZIONE 2: CONFIGURAZIONE SSH ──────────────────────────────────────────

check_ssh_config() {
    [[ "$JSON_OUTPUT" == false ]] && echo "" && echo "── Configurazione SSH ──"
    
    if ! systemctl is-active ssh &>/dev/null && ! systemctl is-active sshd &>/dev/null; then
        log_info "SSH non attivo — skip"
        return
    fi
    
    local sshd_config
    sshd_config=$(sudo sshd -T 2>/dev/null)
    
    # PermitRootLogin
    local root_login
    root_login=$(echo "$sshd_config" | grep "^permitrootlogin" | awk '{print $2}')
    if [[ "${root_login,,}" == "no" ]]; then
        log_ok "SSH: PermitRootLogin=no"
    elif [[ "${root_login,,}" == "prohibit-password" ]]; then
        log_warn "SSH: PermitRootLogin=prohibit-password (solo chiavi, ma meglio 'no')"
    else
        log_crit "SSH: PermitRootLogin=${root_login} — root login con password consentito!"
    fi
    
    # MaxAuthTries
    local max_tries
    max_tries=$(echo "$sshd_config" | grep "^maxauthtries" | awk '{print $2}')
    if [[ "${max_tries:-6}" -le 5 ]]; then
        log_ok "SSH: MaxAuthTries=${max_tries} (≤5)"
    else
        log_warn "SSH: MaxAuthTries=${max_tries} — troppi tentativi prima del ban, impostare ≤5"
    fi
    
    # X11Forwarding
    local x11
    x11=$(echo "$sshd_config" | grep "^x11forwarding" | awk '{print $2}')
    if [[ "${x11,,}" == "no" ]]; then
        log_ok "SSH: X11Forwarding=no"
    else
        log_warn "SSH: X11Forwarding=yes — disabilitare se non necessario"
    fi
    
    # Protocol (SSH2)
    local protocol
    protocol=$(echo "$sshd_config" | grep "^protocol" | awk '{print $2}')
    if [[ "${protocol:-2}" == "2" ]]; then
        log_ok "SSH: Protocol 2 (SSH1 disabilitato)"
    else
        log_crit "SSH: Protocol=$protocol — SSH1 è vulnerabile!"
    fi
}

# ─── SEZIONE 3: AGGIORNAMENTI SICUREZZA ─────────────────────────────────────

check_security_updates() {
    [[ "$JSON_OUTPUT" == false ]] && echo "" && echo "── Aggiornamenti Sicurezza ──"
    
    if ! command -v apt &>/dev/null; then
        log_info "Non è un sistema apt — skip"
        return
    fi
    
    # Aggiorna lista pacchetti (silenzioso)
    apt-get update -qq 2>/dev/null || log_warn "apt update fallito — verifica connettività"
    
    # Conta aggiornamenti sicurezza disponibili
    local sec_updates
    sec_updates=$(apt list --upgradable 2>/dev/null | grep -c "security" || true)
    
    if [[ "$sec_updates" -eq 0 ]]; then
        log_ok "Aggiornamenti sicurezza: nessuno pendente"
    elif [[ "$sec_updates" -le 5 ]]; then
        log_warn "Aggiornamenti sicurezza: ${sec_updates} disponibili — pianificare patch entro SLA"
    else
        log_crit "Aggiornamenti sicurezza: ${sec_updates} disponibili — patch urgente richiesta"
    fi
    
    # Kernel updates (richiedono reboot)
    if [[ -f /var/run/reboot-required ]]; then
        log_warn "Reboot richiesto per applicare aggiornamenti kernel"
        if [[ -f /var/run/reboot-required.pkgs ]]; then
            local reboot_pkgs
            reboot_pkgs=$(cat /var/run/reboot-required.pkgs | tr '\n' ',' | sed 's/,$//')
            log_info "Pacchetti che richiedono reboot: $reboot_pkgs"
        fi
    fi
}

# ─── SEZIONE 4: PROCESSI E PORTE ────────────────────────────────────────────

check_listening_ports() {
    [[ "$JSON_OUTPUT" == false ]] && echo "" && echo "── Porte in Ascolto ──"
    
    # Porte ATTESE per SRV-LINUX-01 nel lab
    declare -A EXPECTED_PORTS=(
        [22]="SSH"
        [8080]="GLPI"
        [631]="CUPS"
    )
    
    # Recupera porte TCP in ascolto
    local listening
    listening=$(ss -tlnp 2>/dev/null | grep LISTEN | awk '{print $4}' | grep -oE '[0-9]+$' | sort -n | uniq)
    
    local unexpected=()
    while IFS= read -r port; do
        if [[ -v "EXPECTED_PORTS[$port]" ]]; then
            log_ok "Porta ${port}: ${EXPECTED_PORTS[$port]} (attesa)"
        else
            unexpected+=("$port")
        fi
    done <<< "$listening"
    
    if [[ ${#unexpected[@]} -gt 0 ]]; then
        for p in "${unexpected[@]}"; do
            local proc
            proc=$(ss -tlnp 2>/dev/null | grep ":$p " | awk '{print $NF}' | grep -oE '"[^"]+"' | head -1)
            log_warn "Porta ${p}: NON nella baseline — processo: ${proc:-sconosciuto} — investigare"
        done
    else
        log_ok "Tutte le porte in ascolto sono nella baseline"
    fi
}

# ─── SEZIONE 5: AUDIT LOG ────────────────────────────────────────────────────

check_auth_logs() {
    [[ "$JSON_OUTPUT" == false ]] && echo "" && echo "── Log di Autenticazione ──"
    
    # Login falliti SSH nelle ultime 24 ore
    local failed_logins
    failed_logins=$(journalctl -u ssh -u sshd --since "24 hours ago" 2>/dev/null | \
        grep -c "Failed password\|Invalid user\|authentication failure" || true)
    
    if [[ "$failed_logins" -lt 50 ]]; then
        log_ok "Login falliti SSH (24h): ${failed_logins}"
    elif [[ "$failed_logins" -lt 200 ]]; then
        log_warn "Login falliti SSH (24h): ${failed_logins} — possibile scan/brute force moderato"
    else
        log_crit "Login falliti SSH (24h): ${failed_logins} — attacco brute force in corso!"
    fi
    
    # IP con più tentativi falliti (top 5)
    local top_attackers
    top_attackers=$(journalctl -u ssh -u sshd --since "24 hours ago" 2>/dev/null | \
        grep -oE 'from [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | \
        awk '{print $2}' | sort | uniq -c | sort -rn | head -5 || true)
    
    if [[ -n "$top_attackers" ]]; then
        [[ "$JSON_OUTPUT" == false ]] && echo "        Top IP attaccanti:" 
        while IFS= read -r line; do
            local count ip
            count=$(echo "$line" | awk '{print $1}')
            ip=$(echo "$line" | awk '{print $2}')
            [[ "$JSON_OUTPUT" == false ]] && echo "          ${count}x tentativi da ${ip}"
        done <<< "$top_attackers"
    fi
    
    # Login root riusciti (non devono esserci!)
    local root_logins
    root_logins=$(journalctl --since "7 days ago" 2>/dev/null | \
        grep -c "session opened for user root\|Accepted.*root" || true)
    
    if [[ "$root_logins" -eq 0 ]]; then
        log_ok "Login root: nessuno (7 giorni)"
    else
        log_crit "Login root: ${root_logins} nelle ultime 7 giorni — investigare immediatamente!"
    fi
}

# ─── REPORT FINALE ───────────────────────────────────────────────────────────

generate_report() {
    local status_str
    case $GLOBAL_STATUS in
        0) status_str="VERDE — Tutti i controlli OK";;
        1) status_str="GIALLO — Warning presenti, azione pianificata richiesta";;
        2) status_str="ROSSO — Criticità rilevate, azione immediata richiesta";;
    esac
    
    if [[ "$JSON_OUTPUT" == true ]]; then
        local findings_json
        findings_json=$(printf '"%s",' "${FINDINGS[@]}")
        findings_json="[${findings_json%,}]"
        
        cat <<EOF
{
  "timestamp": "$TIMESTAMP",
  "host": "$(hostname)",
  "status_code": $GLOBAL_STATUS,
  "status": "$status_str",
  "findings_count": ${#FINDINGS[@]},
  "findings": $findings_json
}
EOF
    else
        echo ""
        echo "═══════════════════════════════════════════════════════"
        echo "  STATO FINALE: $status_str"
        if [[ ${#FINDINGS[@]} -gt 0 ]]; then
            echo ""
            echo "  FINDINGS RILEVATI:"
            for f in "${FINDINGS[@]}"; do
                echo "    → $f"
            done
        fi
        echo "═══════════════════════════════════════════════════════"
        echo ""
    fi
}

# ─── MAIN ────────────────────────────────────────────────────────────────────

main() {
    [[ $EUID -ne 0 ]] && { echo "Richiesto: sudo $0 $*"; exit 3; }
    
    print_header
    check_security_services
    check_ssh_config
    check_security_updates
    check_listening_ports
    check_auth_logs
    generate_report
    
    exit $GLOBAL_STATUS
}

main "$@"
```

**Installazione e uso:**
```bash
# Installa script
sudo install -m 750 -o root -g adm security_health.sh /usr/local/sbin/

# Esegui manualmente
sudo /usr/local/sbin/security_health.sh

# Output JSON (per integrazione con monitoring)
sudo /usr/local/sbin/security_health.sh --json

# Aggiungi a crontab (ogni lunedì alle 07:00)
echo "0 7 * * 1 root /usr/local/sbin/security_health.sh --json >> /var/log/security_health.log 2>&1" | \
    sudo tee /etc/cron.d/security-health-check

# Verifica exit code
sudo /usr/local/sbin/security_health.sh; echo "Exit: $?"
# 0 = OK, 1 = WARNING, 2 = CRITICO, 3 = Permessi insufficienti
```

---

### Progetto C3: Script — `windows_security_audit.ps1` (DC-LAB-01)

```powershell
<#
.SYNOPSIS
    Security health check per DC-LAB-01 (Windows Server 2022 / AD)
.DESCRIPTION
    Verifica lo stato di sicurezza di Windows Server:
    - Windows Defender (definizioni, scansioni, minacce)
    - Windows Firewall (profili, regole permissive)
    - Account AD (admin locali, account sospetti)
    - Hardening CIS Level 1 (SMB1, LLMNR, PS logging)
    - Patch pendenti
.PARAMETER Json
    Output in formato JSON (per integrazione monitoring)
.EXAMPLE
    .\windows_security_audit.ps1
    .\windows_security_audit.ps1 -Json
#>

[CmdletBinding()]
param(
    [switch]$Json
)

$Script:GlobalStatus = 0  # 0=OK, 1=WARNING, 2=CRITICO
$Script:Findings = @()
$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

function Write-Check {
    param([string]$Level, [string]$Message)
    if (-not $Json) {
        $color = switch ($Level) {
            "OK"   { "Green" }
            "WARN" { "Yellow" }
            "CRIT" { "Red" }
            default { "White" }
        }
        Write-Host "  [$Level] $Message" -ForegroundColor $color
    }
    if ($Level -eq "WARN" -and $Script:GlobalStatus -lt 1) { $Script:GlobalStatus = 1 }
    if ($Level -eq "CRIT") { $Script:GlobalStatus = 2 }
    if ($Level -in "WARN","CRIT") { $Script:Findings += "${Level}: $Message" }
}

function Write-Section {
    param([string]$Title)
    if (-not $Json) {
        Write-Host ""
        Write-Host "── $Title ──" -ForegroundColor Cyan
    }
}

# ─── SEZIONE 1: WINDOWS DEFENDER ────────────────────────────────────────────

Write-Section "Windows Defender"

try {
    $mpStatus = Get-MpComputerStatus -ErrorAction Stop
    
    # Stato attivazione
    if ($mpStatus.AntivirusEnabled) {
        Write-Check "OK" "Antivirus abilitato"
    } else {
        Write-Check "CRIT" "Antivirus DISABILITATO — endpoint non protetto!"
    }
    
    if ($mpStatus.RealTimeProtectionEnabled) {
        Write-Check "OK" "Real-time protection attiva"
    } else {
        Write-Check "CRIT" "Real-time protection DISABILITATA!"
    }
    
    # Età definizioni
    $sigAge = (Get-Date) - $mpStatus.AntivirusSignatureLastUpdated
    if ($sigAge.TotalHours -le 24) {
        Write-Check "OK" "Definizioni aggiornate ($([math]::Round($sigAge.TotalHours,1))h fa)"
    } elseif ($sigAge.TotalHours -le 48) {
        Write-Check "WARN" "Definizioni: $([math]::Round($sigAge.TotalHours,1)) ore — aggiornare"
    } else {
        Write-Check "CRIT" "Definizioni: $([math]::Round($sigAge.TotalHours,1)) ore — OBSOLETE!"
    }
    
    # Ultima scansione
    $lastScan = if ($mpStatus.FullScanEndTime -gt $mpStatus.QuickScanEndTime) {
        $mpStatus.FullScanEndTime
    } else {
        $mpStatus.QuickScanEndTime
    }
    $scanAge = (Get-Date) - $lastScan
    if ($scanAge.TotalHours -le 72) {
        Write-Check "OK" "Ultima scansione: $([math]::Round($scanAge.TotalHours,1)) ore fa"
    } elseif ($scanAge.TotalHours -le 168) {
        Write-Check "WARN" "Ultima scansione: $([math]::Round($scanAge.TotalDays,1)) giorni fa"
    } else {
        Write-Check "CRIT" "Ultima scansione: $([math]::Round($scanAge.TotalDays,1)) giorni fa — eseguire immediatamente"
    }
    
    # Minacce in quarantena
    $threats = Get-MpThreat -ErrorAction SilentlyContinue
    if (-not $threats) {
        Write-Check "OK" "Nessuna minaccia in quarantena"
    } else {
        Write-Check "CRIT" "$($threats.Count) minaccia/e in quarantena — investigare: $($threats.ThreatName -join ', ')"
    }

} catch {
    Write-Check "WARN" "Impossibile accedere a Windows Defender: $_"
}

# ─── SEZIONE 2: WINDOWS FIREWALL ────────────────────────────────────────────

Write-Section "Windows Firewall"

$profiles = Get-NetFirewallProfile
foreach ($profile in $profiles) {
    if ($profile.Enabled) {
        Write-Check "OK" "Profilo $($profile.Name): abilitato (default inbound: $($profile.DefaultInboundAction))"
    } else {
        Write-Check "CRIT" "Profilo $($profile.Name): DISABILITATO!"
    }
}

# Verifica SMB1
$smb1 = (Get-SmbServerConfiguration).EnableSMB1Protocol
if (-not $smb1) {
    Write-Check "OK" "SMB1: disabilitato"
} else {
    Write-Check "CRIT" "SMB1: ABILITATO — vulnerabile a EternalBlue/WannaCry! Disabilitare immediatamente"
}

# ─── SEZIONE 3: HARDENING CIS ────────────────────────────────────────────────

Write-Section "Hardening CIS Level 1"

# LLMNR
$llmnr = (Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" -ErrorAction SilentlyContinue).EnableMulticast
if ($llmnr -eq 0) {
    Write-Check "OK" "LLMNR: disabilitato"
} else {
    Write-Check "WARN" "LLMNR: abilitato — vulnerabile ad attacchi Responder/NTLM capture"
}

# PowerShell Script Block Logging
$psLog = (Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" -ErrorAction SilentlyContinue).EnableScriptBlockLogging
if ($psLog -eq 1) {
    Write-Check "OK" "PowerShell Script Block Logging: abilitato"
} else {
    Write-Check "WARN" "PowerShell Script Block Logging: disabilitato — script eseguiti non vengono loggati"
}

# ─── SEZIONE 4: ACCOUNT AD ───────────────────────────────────────────────────

Write-Section "Account e Privilegi AD"

try {
    Import-Module ActiveDirectory -ErrorAction Stop
    
    # Membri Domain Admins
    $domainAdmins = Get-ADGroupMember -Identity "Domain Admins" -ErrorAction Stop
    Write-Check "OK" "Domain Admins: $($domainAdmins.Count) membri ($($domainAdmins.Name -join ', '))"
    
    # Account Admin non disabilitati (escludi Administrator built-in)
    $activeAdmins = $domainAdmins | Where-Object {
        (Get-ADUser -Identity $_.SamAccountName -Properties Enabled).Enabled -eq $true
    }
    if ($activeAdmins.Count -gt 3) {
        Write-Check "WARN" "$($activeAdmins.Count) admin attivi — ogni admin in più è una superficie di attacco"
    }
    
    # Account con password non scadente (escl. service account noti)
    $neverExpire = Get-ADUser -Filter {PasswordNeverExpires -eq $true -and Enabled -eq $true} -Properties PasswordNeverExpires |
        Where-Object { $_.Name -notmatch "svc-|service-|krbtgt" }
    if ($neverExpire.Count -gt 0) {
        Write-Check "WARN" "$($neverExpire.Count) account con password senza scadenza: $($neverExpire.Name -join ', ')"
    } else {
        Write-Check "OK" "Nessun account utente con password senza scadenza"
    }
    
    # Account con ultimo login > 90 giorni (stale accounts)
    $staleDate = (Get-Date).AddDays(-90)
    $staleAccounts = Get-ADUser -Filter {LastLogonDate -lt $staleDate -and Enabled -eq $true} -Properties LastLogonDate |
        Where-Object { $_.Name -notmatch "krbtgt" }
    if ($staleAccounts.Count -gt 0) {
        Write-Check "WARN" "$($staleAccounts.Count) account attivi senza login da 90+ giorni — considerare disabilitazione"
    } else {
        Write-Check "OK" "Nessun account stale (> 90 giorni senza login)"
    }

} catch {
    Write-Check "WARN" "Modulo AD non disponibile o errore: $_"
}

# ─── REPORT FINALE ───────────────────────────────────────────────────────────

$statusText = switch ($Script:GlobalStatus) {
    0 { "VERDE - Tutti i controlli OK" }
    1 { "GIALLO - Warning presenti, azione pianificata richiesta" }
    2 { "ROSSO - Criticità rilevate, azione immediata richiesta" }
}

if ($Json) {
    [PSCustomObject]@{
        Timestamp    = $Timestamp
        Host         = $env:COMPUTERNAME
        StatusCode   = $Script:GlobalStatus
        Status       = $statusText
        FindingCount = $Script:Findings.Count
        Findings     = $Script:Findings
    } | ConvertTo-Json -Depth 3
} else {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
    $summaryColor = switch ($Script:GlobalStatus) { 0 {"Green"} 1 {"Yellow"} 2 {"Red"} }
    Write-Host "  STATO FINALE: $statusText" -ForegroundColor $summaryColor
    if ($Script:Findings.Count -gt 0) {
        Write-Host ""
        Write-Host "  FINDINGS:"
        $Script:Findings | ForEach-Object { Write-Host "    → $_" }
    }
    Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
}

exit $Script:GlobalStatus
```

**Installazione e uso:**
```powershell
# Su DC-LAB-01

# Esecuzione manuale
.\windows_security_audit.ps1

# Output JSON
.\windows_security_audit.ps1 -Json | ConvertFrom-Json | Format-List

# Pianificazione con Task Scheduler (ogni lunedì 07:00)
$action  = New-ScheduledTaskAction -Execute "powershell.exe" `
           -Argument "-ExecutionPolicy RemoteSigned -File C:\Scripts\windows_security_audit.ps1 -Json >> C:\Logs\security_audit.log"
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 07:00
Register-ScheduledTask -TaskName "Security Health Check" `
    -Action $action -Trigger $trigger -RunLevel Highest
```

---

### Integrazione ITIL

**Pratica ITIL applicata:** Security Management (Information Security Management)

```
GESTIONE DEGLI INCIDENTI DI SICUREZZA:
  Ogni CRITICO rilevato dagli script → Incidente P1
  Categoria: Security / Endpoint Protection
  
  Flusso:
  1. Script rileva CRITICO (exit code 2)
  2. Apre ticket GLPI automaticamente (API GLPI o email)
  3. Alert a team IT tramite notifica
  4. Team risponde entro SLA (P1 = 15 minuti per acknowledgement)
  5. Risoluzione documentata nel ticket
  6. Post-incident review se impatto > 30 minuti

GESTIONE DEI CAMBIAMENTI:
  Ogni modifica alla configurazione sicurezza (hardening, nuova regola, esclusione) →
  Change Request in GLPI
  Categoria: Security Configuration
  
  Approval workflow:
  - Minor (nuova regola firewall a basso rischio): approvazione IT Lead
  - Standard (cambio policy Defender): CAB mensile
  - Emergency (risposta a CVE critico): Emergency CAB entro 2 ore

GESTIONE DEL RISCHIO:
  Vulnerabilità non patchate = Rischi aperti nel registro
  Ogni vulnerabilità classificata CVSS → registrata con:
  - CVE ID
  - CVSS score
  - Sistema/i affetti
  - Data rilevamento
  - SLA di remediation (da CVSS score)
  - Owner
  - Piano di remediation

GESTIONE DELLA CONTINUITÀ (tramite Monitoring):
  Script security_health.sh e windows_security_audit.ps1 →
  Output JSON → raccolta da Prometheus o sistema SIEM →
  Dashboard Grafana →
  Alert se status = CRITICO
```

---

## Checklist di Validazione Lab

### Part A — Concetti
- [ ] Sai descrivere Defense in Depth con 3 esempi concreti del lab
- [ ] Sai spiegare la differenza EDR vs AV tradizionale
- [ ] Sai applicare la tabella CVSS per classificare una vulnerabilità e assegnare SLA
- [ ] Sai spiegare perché SMB1 è vietato (storia WannaCry/EternalBlue)
- [ ] Sai descrivere i 3 profili Windows Firewall e quando si attivano

### Part B — Operazioni
- [ ] B1: Windows Defender audit completato, definizioni < 48 ore
- [ ] B2: SSH hardening applicato su SRV-LINUX-01 (PermitRootLogin no, MaxAuthTries 3)
- [ ] B3: fail2ban installato, jail SSH attivo, test brute force completato
- [ ] B4: Windows Firewall audit completato, RDP limitato a 192.168.56.0/24
- [ ] B5: nmap scan completato, surface di attacco documentata
- [ ] B6: CIS checklist applicata, report 5/5 PASS

### Part C — Sistematizzazione
- [ ] SOP-SEC-001 compresa e potenzialmente adattata al proprio ambiente
- [ ] `security_health.sh` installato in `/usr/local/sbin/`, esecuzione manuale testata
- [ ] `windows_security_audit.ps1` eseguito su DC-LAB-01, output compreso
- [ ] Connessione ITIL stabilita: quale pratica ITIL gestisce la sicurezza?

---

## Appendice A: Riferimento Rapido Comandi Sicurezza

### Windows (PowerShell)

```powershell
# Defender
Get-MpComputerStatus | Select-Object AntivirusEnabled, RealTimeProtectionEnabled, AntivirusSignatureLastUpdated
Get-MpPreference | Select-Object ExclusionPath, ExclusionExtension
Get-MpThreat                                   # minacce in quarantena
Update-MpSignature                             # aggiorna definizioni manualmente
Start-MpScan -ScanType QuickScan              # avvia quick scan

# Firewall
Get-NetFirewallProfile | Select-Object Name, Enabled, DefaultInboundAction
Get-NetFirewallRule -Enabled True -Direction Inbound -Action Allow | Select-Object DisplayName, Profile
New-NetFirewallRule -DisplayName "Nome" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow
Set-NetFirewallRule -DisplayName "Nome" -RemoteAddress "192.168.56.0/24"
Remove-NetFirewallRule -DisplayName "Nome"

# SMB
Get-SmbServerConfiguration | Select-Object EnableSMB1Protocol, EnableSMB2Protocol
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force

# Account AD
Get-ADGroupMember -Identity "Domain Admins"
Get-ADUser -Filter {PasswordNeverExpires -eq $true -and Enabled -eq $true}
Get-ADUser -Filter {Enabled -eq $true} -Properties LastLogonDate | Where-Object {$_.LastLogonDate -lt (Get-Date).AddDays(-90)}
```

### Linux (Bash)

```bash
# SSH
sudo sshd -T                                   # config attiva completa
sudo sshd -T | grep -E "permitrootlogin|maxauthtries|passwordauthentication"
sudo sshd -t                                   # testa sintassi config (non ricarica)
sudo systemctl reload sshd                     # ricarica senza disconnettere

# fail2ban
sudo fail2ban-client status                    # lista jail
sudo fail2ban-client status sshd              # stato jail SSH
sudo fail2ban-client set sshd banip 1.2.3.4  # ban manuale
sudo fail2ban-client set sshd unbanip 1.2.3.4 # unban

# ufw
sudo ufw status verbose                       # stato con regole
sudo ufw allow from 192.168.56.0/24 to any port 22
sudo ufw deny 23/tcp                           # blocca telnet

# Porte in ascolto
sudo ss -tlnp                                  # TCP listening + processo
sudo ss -ulnp                                  # UDP listening

# Aggiornamenti sicurezza
sudo apt list --upgradable 2>/dev/null | grep security
sudo unattended-upgrades --dry-run            # simula aggiornamenti automatici

# Log autenticazione
sudo journalctl -u sshd --since "24 hours ago" | grep "Failed\|Invalid\|Accepted"
sudo lastb | head -20                          # tentativi login falliti
sudo last | head -20                           # login riusciti
```

---

## Appendice B: Tabella Strumenti Sicurezza — Lab vs Produzione

| Categoria | Lab (questo tutorial) | Enterprise (riferimento) |
|-----------|----------------------|--------------------------|
| Endpoint Protection | Windows Defender (built-in) | CrowdStrike Falcon, SentinelOne, Microsoft Defender for Endpoint |
| Vulnerability Scanner | nmap (port scan) | Nessus, Qualys, OpenVAS, Tenable.io |
| Firewall | Windows Firewall, ufw | Palo Alto NGFW, Fortinet FortiGate, pfSense |
| Brute Force Protection | fail2ban | fail2ban, CrowdSec, Cloudflare Rate Limiting |
| SIEM | journalctl/Event Viewer | Splunk, Microsoft Sentinel, Elastic SIEM |
| Compliance Scan | Script manuale (questo tutorial) | CIS-CAT Pro, Tenable.SC |
| Patch Management | apt / Windows Update | WSUS, Microsoft Endpoint Manager, Ansible |

---

## Appendice C: Decision Tree — Risposta a una Vulnerabilità Rilevata

```
Rilevata vulnerabilità su un sistema
         │
         ▼
[CVSS score?]
    │           │
  <4.0        4.0+
  Basso        │
  90 giorni    ▼
           [Sistema esposto su Internet?]
                │           │
               Sì           No
                │           │
                ▼           ▼
           [CVSS]        [Exploit
              │           disponibile?]
           7.0+              │    │
            → 72h           Sì   No
           4.0-7.0           │    │
            → 7 giorni       ▼    ▼
                        [7 giorni] [30 giorni]
                        
         PROCEDURA:
         1. Registra vulnerabilità in GLPI (categoria: Security / Vulnerability)
         2. Assegna SLA in base alla matrice sopra
         3. Identifica piano di remediation (patch, workaround, isolamento)
         4. Change Request per applicazione patch
         5. Verifica post-patch (ri-scansione)
         6. Chiudi ticket con evidenza di remediation
```

---

## Riferimenti

- CIS Benchmarks (https://www.cisecurity.org/cis-benchmarks) — guide di hardening per Windows Server 2022, Ubuntu 22.04
- NIST SP 800-53 — Security and Privacy Controls for Information Systems
- CVSS Calculator v3.1 (https://www.first.org/cvss/calculator/3.1)
- Microsoft Security Compliance Toolkit (per GPO hardening baseline)
- fail2ban Documentation (https://fail2ban.readthedocs.io)
- OpenSSH Server Manual — sshd_config(5)
- OWASP Top 10 — vulnerabilità web più comuni
