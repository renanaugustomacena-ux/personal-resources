# Tutorial: Audit Accessi, PAM, RBAC e Compliance — Hands-On Lab

> **Documento di riferimento:** `05-sicurezza-operativa.md` (sezioni Audit e Compliance, Gestione Accessi, Log Audit)
> **Dominio:** Security Operations — Governance degli Accessi
> **Ambito:** Gestione identità e accessi (IAM), PAM, RBAC, audit log Windows/Linux, compliance ISO 27001/GDPR/NIS2, Identity Lifecycle (onboarding/offboarding), certificazione degli accessi
> **Durata lab:** 4-5 ore
> **Livello:** Intermedio-Avanzato — richiede ops03a (Windows Server AD) e ops05_ch1a (sicurezza endpoint)
> **Prerequisiti:** DC-LAB-01 con AD DS, SRV-LINUX-01 con utenti configurati
> **Ambiente:** DC-LAB-01 (Active Directory, Event Viewer, PowerShell), SRV-LINUX-01 (audit log, account)

---

## Lab Environment Setup

```powershell
# Su DC-LAB-01 — verifica pre-lab
Write-Host "=== VERIFICA PRE-LAB AUDIT ACCESSI ==="

# AD module disponibile?
if (Get-Module -ListAvailable -Name ActiveDirectory) {
    Write-Host "[OK] Modulo ActiveDirectory disponibile"
    Import-Module ActiveDirectory
    $users = (Get-ADUser -Filter *).Count
    Write-Host "[OK] Utenti in AD: $users"
} else {
    Write-Host "[WARN] Modulo AD non disponibile — installa RSAT"
}

# Security Event Log configurato?
$secLog = Get-WinEvent -ListLog Security
Write-Host "Security Log: $([math]::Round($secLog.FileSize/1MB,1)) MB / $([math]::Round($secLog.MaximumSizeInBytes/1MB,1)) MB max"

# Audit policy configurata?
$auditPol = auditpol /get /subcategory:"Logon" 2>$null
Write-Host "Audit Logon: $auditPol"
```

```bash
# Su SRV-LINUX-01 — verifica pre-lab
echo "=== VERIFICA PRE-LAB LINUX ==="
echo "Utenti locali con shell:"
getent passwd | awk -F: '$7 !~ /nologin|false/ {print $1, "UID="$3, "shell="$7}'
echo ""
echo "Audit log:"
journalctl -u ssh --since "7 days ago" --no-pager | wc -l | xargs echo "SSH log entries (7gg):"
```

---

## PART A: FONDAMENTI — Identità, Accessi e Responsabilità

> La sicurezza degli accessi risponde a tre domande fondamentali: **Chi** può accedere? **A cosa** può accedere? **Quando** e **come** è avvenuto l'accesso? Il primo e il secondo punto sono gestiti da IAM (Identity and Access Management) e RBAC. Il terzo è gestito dall'audit trail. Senza un audit trail completo e integro, non puoi rispondere a "Chi ha cancellato quel file il 15 luglio?" — e non puoi dimostrare conformità a nessun framework regolatorio.

---

### Concetto A1: Identity and Access Management (IAM) — Il Sistema di Controllo delle Chiavi

> **Analogia.** In un grande edificio ci sono migliaia di porte. Alcune sono aperte a tutti (corridoi), alcune solo ai dipendenti (uffici), alcune solo ai dirigenti (sala board), alcune a personale specifico (sala server). Le chiavi fisiche sono difficili da gestire: chi ne ha una può copiarla, chi lascia l'azienda potrebbe non restituirla. Un sistema IAM è come un controllo accessi elettronico centralizzato: da un pannello centrale puoi vedere chi ha accesso a cosa, revocare un accesso istantaneamente, e vedere il log di ogni porta aperta.

**Il ciclo di vita dell'identità digitale:**

```
                    [ONBOARDING]
HR assume nuovo dipendente Mario Rossi
         │
         ▼
IT crea identità digitale:
  - Account AD: mario.rossi@lab.local
  - Password temporanea (cambio obbligatorio al primo accesso)
  - Assegnazione ruoli in base alla funzione
  - Accesso email, VPN, applicazioni
         │
         ▼
         [UTILIZZO NORMALE]
Mario lavora, usa le risorse assegnate
Cambio di ruolo → update dei permessi
          │
          ▼
         [OFFBOARDING]
Mario lascia l'azienda (o viene licenziato)
         │
         ├── Licenziamento → disabilita IMMEDIATAMENTE (stesso giorno)
         └── Dimissioni → disabilita l'ultimo giorno lavorativo
         │
         ▼
Dopo 30 giorni: verifica che nessuno richieda l'account
Dopo 30 giorni: cancella l'account (archivia i dati)

RISCHIO principale: account non disabilitati di ex-dipendenti
  → Accesso non autorizzato mesi dopo l'uscita
  → Insider threat da personale scontento
```

**Perché il timing dell'offboarding è critico:**

```
Caso reale tipico:
  Dipendente licenziato accede ai sistemi 3 giorni dopo il licenziamento
  usando le credenziali mai disabilitate → scarica dati cliente
  
  Impatto: violazione GDPR → notifica al Garante entro 72 ore
            rischio sanzione fino al 4% del fatturato annuo
  
  Causa radice: processo di offboarding manuale = ritardo
  Soluzione: automazione (HR notifica IT → workflow automatico)
```

---

### Concetto A2: RBAC — Permessi per Ruolo, non per Persona

> **Analogia.** In un ospedale, ogni ruolo ha accesso diverso: il medico accede alle cartelle cliniche, l'infermiera ai piani di cura, l'amministrativo alla prenotazione, il tecnico agli strumenti. Non si assegna l'accesso a ciascun dipendente singolarmente — si definiscono i ruoli una volta sola e si assegna ogni persona al suo ruolo. Se assumono 50 nuove infermiere, le accessi vengono assegnate automaticamente assegnando il ruolo "Infermiera". Questo è RBAC.

**RBAC vs assegnazione diretta:**

```
ASSEGNAZIONE DIRETTA (problema):
  Mario  → ha accesso a: File Vendite, CRM, Email, Sharepoint-Marketing
  Giulia → ha accesso a: File Vendite, CRM, Email, Sharepoint-HR
  Laura  → ha accesso a: File Contabilità, SAP, Email
  
  Problemi:
  - Se Mario cambia ruolo, devo ricordare cosa togliergli
  - Non so "chi ha accesso a cosa" senza interrogare ogni utente
  - Role creep: Mario accumula permessi con ogni cambio di progetto
  - Difficile fare audit: qual è la "baseline" corretta?

RBAC (soluzione):
  Ruolo "Commerciale" → File Vendite, CRM, Email, Sharepoint-Marketing
  Ruolo "HR" → File HR, HRIS, Email, Sharepoint-HR
  Ruolo "Contabilità" → File Contabilità, SAP, Email
  
  Mario → assegnato a ruolo "Commerciale"
  Giulia → assegnata a ruoli "Commerciale" + "HR" (doppio ruolo)
  
  Se Mario cambia a Marketing: rimuovi "Commerciale" → aggiungi "Marketing"
  Se assumi 10 nuovi commerciali: assegna ruolo "Commerciale" a tutti
```

**Matrice RBAC — strumento fondamentale:**

```
            | File Vendite | CRM | File HR | SAP Contab | VPN |
Commerciale |     RW       |  RW |    -    |     -      |  R  |
HR          |      -       |   - |   RW    |     -      |  R  |
Contabilità |      -       |   - |    -    |    RW      |  R  |
IT Admin    |     RW       |  RW |   RW    |    RW      | RW  |
Management  |      R       |   R |    R    |     R      |  R  |

R = Read, W = Write (include modifica e cancellazione)
- = nessun accesso (negato esplicitamente o per mancanza di regola)

REGOLA: Se un'autorizzazione non è nella matrice, non viene assegnata.
        Chi chiede un'eccezione → processo di approvazione formale.
```

---

### Concetto A3: PAM — Gestione degli Accessi Privilegiati

> **Analogia.** In una banca, le chiavi della cassaforte principale sono custodite in modo speciale: non le tiene nessun singolo dipendente, vengono estratte solo quando necessario con due persone presenti, ogni accesso viene registrato su video, e le chiavi vengono cambiate dopo ogni utilizzo. PAM (Privileged Access Management) applica lo stesso principio agli account amministratori IT: le password non le conosce nessuno, vengono generate automaticamente, ogni sessione viene registrata integralmente.

**Perché gli accessi privilegiati sono il bersaglio più prezioso:**

```
Un account utente normale compromesso può:
  → Leggere/modificare i file dell'utente
  → Inviare email a nome dell'utente
  → Accedere alle applicazioni con i permessi dell'utente

Un account Domain Admin compromesso può:
  → Accedere a TUTTI i file di TUTTI gli utenti
  → Resettare le password di CHIUNQUE (incluso il CEO)
  → Cancellare i log che tracciano l'attacco
  → Installare malware su qualsiasi server del dominio
  → Distruggere i backup
  → Estrarre tutte le credenziali del dominio (NTDS.dit)
  
Tempo medio per un attaccante da "compromissione iniziale" 
a "Domain Admin" in un ambiente senza PAM: 15-30 minuti

Soluzione PAM:
  - Nessun account admin permanente (just-in-time access)
  - Ogni sessione privilegiata registrata (session recording)
  - Password generate e cambiate automaticamente (vault)
  - Alert in tempo reale su attività ad alto rischio
```

**Strumenti PAM nel mercato:**

```
ENTERPRISE:
  CyberArk PAM: leader di mercato, altissima sicurezza, costo elevato
  BeyondTrust: buone capacità PAM per ambienti misti Windows/Linux
  
OPEN SOURCE / BUDGET RIDOTTO:
  Teleport: accesso SSH/RDP/K8s con audit trail, open source
  HashiCorp Vault: gestione segreti e credenziali dinamiche
  Apache Guacamole: gateway web per RDP/SSH con registrazione sessione
  
NEL LAB:
  Simulazione del concetto con:
  - Password temporanee AD (ruolo concesso per 2 ore, poi revocato)
  - Event ID Windows per audit delle azioni admin
  - journalctl per audit delle sessioni sudo su Linux
```

---

### Concetto A4: Audit dei Log — La Memoria Integra del Sistema

> **Analogia.** In un'aula di tribunale, la prova regina è l'evidenza scritta e non alterata. I log di sistema sono l'equivalente digitale di questa evidenza: registrano ogni azione, con chi l'ha fatta, quando, e da dove. Ma le evidenze devono essere **integre** (non modificabili) e **complete** (senza lacune). Un log modificato dall'attaccante è come una testimonianza alterata — inutile. Un sistema di logging centralizzato e protetto garantisce che l'evidenza sia affidabile.

**Event ID Windows critici per la sicurezza:**

```
AUTENTICAZIONE:
  4624 → Login riuscito (Logon Type: 2=interattivo, 3=rete, 10=RDP)
  4625 → Login fallito (SubStatus: 0xC000006A=password sbagliata)
  4634 → Logoff
  4648 → Login con credenziali esplicite (pass-the-hash pattern)
  4768 → Richiesta TGT Kerberos (autenticazione dominio)
  4771 → Pre-autenticazione Kerberos fallita (brute force Kerberos)

GESTIONE ACCOUNT:
  4720 → Account utente creato
  4722 → Account utente abilitato
  4723 → Password cambiata
  4724 → Password reimpostata da admin
  4725 → Account utente disabilitato
  4726 → Account utente cancellato
  4728 → Membro aggiunto a gruppo security globale (es: Domain Admins)
  4732 → Membro aggiunto a gruppo security locale

AZIONI PRIVILEGIATE:
  4672 → Accesso con privilegi speciali assegnati (admin login)
  4673 → Servizio privilegiato chiamato
  4688 → Processo creato (richiede audit policy specifico)
  4104 → PowerShell Script Block Logging

SISTEMA:
  1102 → Audit log cancellato (!) → CRITICO, probabile attacco
  7045 → Nuovo servizio installato nel sistema
  4719 → System audit policy modificata
```

**Linux — sorgenti di log per sicurezza:**

```
/var/log/auth.log (Debian/Ubuntu) o /var/log/secure (RHEL):
  → Tutti gli eventi di autenticazione SSH, sudo, su
  
journalctl -u sshd:
  → Events SSH (login, logout, key authentication)
  
/var/log/syslog:
  → Log di sistema generale
  
/var/log/audit/audit.log (auditd):
  → Tracking file access, syscall, permessi se auditd configurato
  → Esempio: ogni lettura del file /etc/passwd, ogni exec di sudo
  
last / lastb / lastlog:
  → Storia login riusciti / falliti / per utente
```

---

### Concetto A5: Compliance — Perché le Regole Contano

> **Analogia.** La conformità normativa è come le norme di sicurezza stradale: non guidi senza cintura perché "probabilmente non ci sarà un incidente", ma perché la legge lo richiede e perché in caso di incidente la tua responsabilità dipende dal rispetto delle norme. Se i dati dei clienti vengono violati e tu non rispettavi il GDPR, la sanzione non dipende solo dal danno causato ma dal fatto che non hai implementato "misure adeguate".

**Framework principali per un team IT Operations:**

```
ISO 27001 (Information Security Management System):
  Cosa è: standard internazionale per la gestione della sicurezza
  Applicabile a: qualsiasi organizzazione che vuole certificarsi
  Controlli chiave per IT Ops:
    A.5.15  → Access control (IAM, RBAC)
    A.8.8   → Vulnerability management
    A.8.9   → Configuration management
    A.8.15  → Logging
  Audit: certificazione annuale da organismo accreditato

GDPR (Regolamento UE 2016/679):
  Cosa è: protezione dati personali cittadini UE
  Applicabile a: TUTTI che trattano dati di persone UE
  Obblighi tecnici IT Ops:
    → Crittografia dei dati personali (in transito e a riposo)
    → Log degli accessi ai dati personali
    → Capacità di notifica data breach entro 72 ore
    → Pseudonimizzazione nei test environment
    → Data retention policy (non conservare più del necessario)

NIS2 (Direttiva UE 2022/2555 → D.Lgs. 138/2024 Italia):
  Cosa è: sicurezza reti e sistemi informativi per settori critici
  Applicabile a: soggetti essenziali (energia, trasporti, sanità...)
              e soggetti importanti (corrieri, gestori rifiuti...)
  Obblighi tecnici:
    → Analisi dei rischi documentata
    → Gestione incidenti (notifica CSIRT entro 24h)
    → Continuità operativa
    → Sicurezza supply chain (verificare i fornitori IT)
    → MFA obbligatoria per accessi critici

PCI DSS v4.0 (Payment Card Industry Data Security Standard):
  Cosa è: standard sicurezza per chi gestisce dati carte di pagamento
  Applicabile a: merchant, payment processor, service provider
  Controlli chiave:
    → Req. 1: Firewall e segmentazione rete
    → Req. 2: Hardening (nessun default vendor)
    → Req. 5: Antivirus/EDR su tutti i sistemi
    → Req. 8: MFA per accesso CDE (Cardholder Data Environment)
    → Req. 10: Logging (almeno 12 mesi, 3 immediatamente accessibili)
```

---
---

## PART B: OPERAZIONI — Audit Accessi e Conformità nel Lab

---

### Esercizio B1: Audit Account Active Directory — Chi Ha Accesso a Cosa

**Obiettivo.** Eseguire un audit completo degli account in Active Directory su DC-LAB-01, identificare account stale, verificare appartenenze ai gruppi privilegiati, e rilevare configurazioni non conformi.

**Background.** L'audit degli account AD è il fondamento di qualsiasi programma di sicurezza in ambiente Windows. Active Directory controlla l'autenticazione e l'autorizzazione di ogni risorsa del dominio. Account non gestiti sono porte spalancate: ex-dipendenti che possono ancora autenticarsi, service account con password senza scadenza, utenti con privilegi non necessari.

**Step 1 — Inventario completo degli utenti:**

```powershell
# Su DC-LAB-01 come Administrator
Import-Module ActiveDirectory

Write-Host "=== INVENTARIO ACCOUNT AD ===" -ForegroundColor Cyan
Write-Host ""

# Statistiche generali
$allUsers = Get-ADUser -Filter * -Properties Enabled, PasswordLastSet, LastLogonDate, PasswordNeverExpires, PasswordExpired
Write-Host "Utenti totali nel dominio:       $($allUsers.Count)"
Write-Host "  Abilitati:                     $(($allUsers | Where-Object Enabled).Count)"
Write-Host "  Disabilitati:                  $(($allUsers | Where-Object {-not $_.Enabled}).Count)"
Write-Host ""

# Distribuzione per OU
Write-Host "Distribuzione per OU:" -ForegroundColor Yellow
Get-ADOrganizationalUnit -Filter * | ForEach-Object {
    $ouName = $_.Name
    $count = (Get-ADUser -Filter * -SearchBase $_.DistinguishedName -SearchScope OneLevel).Count
    if ($count -gt 0) { Write-Host "  $ouName → $count utenti" }
}
```

**Step 2 — Identifica account stale (dormienti):**

```powershell
Write-Host ""
Write-Host "=== ACCOUNT STALE (> 90 giorni senza login) ===" -ForegroundColor Yellow

$staleCutoff = (Get-Date).AddDays(-90)
$staleAccounts = Get-ADUser -Filter {Enabled -eq $true} -Properties LastLogonDate, Description |
    Where-Object { $_.LastLogonDate -lt $staleCutoff -or $_.LastLogonDate -eq $null } |
    Select-Object Name, SamAccountName, LastLogonDate, Description |
    Sort-Object LastLogonDate

if ($staleAccounts.Count -gt 0) {
    Write-Host "TROVATI $($staleAccounts.Count) account stale:" -ForegroundColor Red
    $staleAccounts | Format-Table -AutoSize
    Write-Host "AZIONE RICHIESTA: verificare con i responsabili → disabilitare se non necessari" -ForegroundColor Yellow
} else {
    Write-Host "Nessun account stale trovato" -ForegroundColor Green
}

# Account mai usati (LastLogonDate = null)
$neverLogged = $allUsers | Where-Object { $_.Enabled -and $_.LastLogonDate -eq $null }
if ($neverLogged.Count -gt 0) {
    Write-Host ""
    Write-Host "Account abilitati ma mai usati: $($neverLogged.Count)" -ForegroundColor Yellow
    $neverLogged | Select-Object Name, SamAccountName | Format-Table -AutoSize
}
```

**Step 3 — Audit gruppi privilegiati:**

```powershell
Write-Host ""
Write-Host "=== AUDIT GRUPPI PRIVILEGIATI ===" -ForegroundColor Yellow

$privilegedGroups = @("Domain Admins", "Enterprise Admins", "Schema Admins", 
                       "Administrators", "Account Operators", "Backup Operators")

foreach ($group in $privilegedGroups) {
    try {
        $members = Get-ADGroupMember -Identity $group -ErrorAction Stop
        if ($members.Count -gt 0) {
            $color = if ($members.Count -gt 3) { "Yellow" } else { "Green" }
            Write-Host ""
            Write-Host "  $group ($($members.Count) membri):" -ForegroundColor $color
            foreach ($m in $members) {
                $user = Get-ADUser -Identity $m.SamAccountName -Properties Enabled, LastLogonDate -ErrorAction SilentlyContinue
                if ($user) {
                    $enabledStr = if ($user.Enabled) { "ATTIVO" } else { "DISABILITATO" }
                    $lastLogin = if ($user.LastLogonDate) { $user.LastLogonDate.ToString("yyyy-MM-dd") } else { "MAI" }
                    $warn = if (-not $user.Enabled) { "[WARN: disabilitato nel gruppo admin!]" } else { "" }
                    Write-Host "    → $($m.Name) ($enabledStr, ultimo login: $lastLogin) $warn"
                }
            }
        }
    } catch {
        Write-Host "  $group: non trovato o errore" -ForegroundColor Gray
    }
}
```

**Step 4 — Account con password problematiche:**

```powershell
Write-Host ""
Write-Host "=== PASSWORD POLICY ISSUES ===" -ForegroundColor Yellow

# Password senza scadenza
$noPwdExpiry = Get-ADUser -Filter {PasswordNeverExpires -eq $true -and Enabled -eq $true} `
    -Properties PasswordNeverExpires, Description |
    Where-Object { $_.Name -notmatch "krbtgt|MSOL_|AAD_" }  # Escludi account di sistema

Write-Host "Account utenti con password senza scadenza: $($noPwdExpiry.Count)"
if ($noPwdExpiry.Count -gt 0) {
    $noPwdExpiry | Select-Object Name, SamAccountName, Description | Format-Table -AutoSize
    Write-Host "NOTE: Solo i service account dovrebbero avere PasswordNeverExpires (e devono essere documentati)" -ForegroundColor Yellow
}

# Password non cambiata da > 180 giorni
$oldPwd = Get-ADUser -Filter {Enabled -eq $true} -Properties PasswordLastSet |
    Where-Object { $_.PasswordLastSet -lt (Get-Date).AddDays(-180) -and $_.PasswordLastSet -ne $null }

Write-Host ""
Write-Host "Account con password invariata da > 180 giorni: $($oldPwd.Count)"
if ($oldPwd.Count -gt 0) {
    $oldPwd | Select-Object Name, SamAccountName, PasswordLastSet | 
        Sort-Object PasswordLastSet | Format-Table -AutoSize
}

# Account disabilitati ancora in gruppi privilegiati (sicurezza residua)
Write-Host ""
Write-Host "=== ACCOUNT DISABILITATI IN GRUPPI PRIVILEGIATI ===" -ForegroundColor Yellow
foreach ($group in @("Domain Admins", "Administrators")) {
    try {
        $members = Get-ADGroupMember -Identity $group | Where-Object { $_.objectClass -eq "user" }
        foreach ($m in $members) {
            $user = Get-ADUser -Identity $m.SamAccountName -Properties Enabled -ErrorAction SilentlyContinue
            if ($user -and -not $user.Enabled) {
                Write-Host "  [!] $($user.Name) è disabilitato ma ancora in $group — rimuovere!" -ForegroundColor Red
            }
        }
    } catch { }
}
```

**Output atteso (ambiente lab base):**
```
=== INVENTARIO ACCOUNT AD ===
Utenti totali nel dominio:       5
  Abilitati:                     4
  Disabilitati:                  1

=== ACCOUNT STALE (> 90 giorni senza login) ===
Nessun account stale trovato

=== AUDIT GRUPPI PRIVILEGIATI ===
  Domain Admins (1 membri):
    → Administrator (ATTIVO, ultimo login: 2026-07-15)
```

**Checkpoint di verifica B1:**
- [ ] Inventario completo eseguito (tutti gli utenti elencati)
- [ ] Nessun account stale non giustificato
- [ ] Domain Admins ha solo gli account previsti
- [ ] Nessun account disabilitato rimane in gruppi privilegiati

---

### Esercizio B2: Audit Event Log Windows — Tracciare le Azioni degli Utenti

**Obiettivo.** Interrogare il Security Event Log di DC-LAB-01 per identificare tentativi di login falliti, accessi privilegiati, e modifiche agli account — le stesse interrogazioni che un analista SOC esegue durante un'investigazione.

**Background.** Il Security Event Log di Windows è la fonte principale di evidenze per le investigazioni di sicurezza in ambiente AD. In produzione viene raccolto da un SIEM (Splunk, Microsoft Sentinel). Nel lab impariamo a interrogarlo direttamente con PowerShell — le competenze sono le stesse, cambia solo lo strumento.

**Step 1 — Configura la policy di audit (prerequisito):**

```powershell
# Verifica audit policy attiva
Write-Host "=== AUDIT POLICY ATTIVA ===" -ForegroundColor Cyan
auditpol /get /category:"Logon/Logoff","Account Logon","Account Management","Privilege Use" 2>$null

# Abilita audit essenziale se non attivo
Write-Host ""
Write-Host "Abilitando audit policy per security monitoring..."

# Tramite GPO (preferito in produzione) o direttamente:
auditpol /set /subcategory:"Logon" /success:enable /failure:enable 2>$null
auditpol /set /subcategory:"Account Lockout" /success:enable /failure:enable 2>$null
auditpol /set /subcategory:"User Account Management" /success:enable /failure:enable 2>$null
auditpol /set /subcategory:"Security Group Management" /success:enable /failure:enable 2>$null
auditpol /set /subcategory:"Audit Policy Change" /success:enable /failure:enable 2>$null
auditpol /set /subcategory:"Sensitive Privilege Use" /success:enable /failure:enable 2>$null

Write-Host "[OK] Audit policy configurata"
```

**Step 2 — Analisi login falliti (brute force detection):**

```powershell
Write-Host "=== LOGIN FALLITI — ULTIME 24 ORE ===" -ForegroundColor Yellow

$since = (Get-Date).AddHours(-24)
try {
    $failedLogins = Get-WinEvent -FilterHashtable @{
        LogName   = 'Security'
        Id        = 4625
        StartTime = $since
    } -ErrorAction Stop |
    ForEach-Object {
        $xml = [xml]$_.ToXml()
        [PSCustomObject]@{
            Time        = $_.TimeCreated
            Account     = $xml.Event.EventData.Data | Where-Object {$_.Name -eq "TargetUserName"} | Select-Object -ExpandProperty '#text'
            WorkStation = $xml.Event.EventData.Data | Where-Object {$_.Name -eq "WorkstationName"} | Select-Object -ExpandProperty '#text'
            SourceIP    = $xml.Event.EventData.Data | Where-Object {$_.Name -eq "IpAddress"} | Select-Object -ExpandProperty '#text'
            SubStatus   = $xml.Event.EventData.Data | Where-Object {$_.Name -eq "SubStatus"} | Select-Object -ExpandProperty '#text'
        }
    }
    
    Write-Host "Totale login falliti: $($failedLogins.Count)"
    
    if ($failedLogins.Count -gt 0) {
        Write-Host ""
        Write-Host "Top account con più fallimenti:"
        $failedLogins | Group-Object Account | Sort-Object Count -Descending | 
            Select-Object -First 5 | Format-Table Count, Name -AutoSize
        
        Write-Host "Top IP sorgente:"
        $failedLogins | Group-Object SourceIP | Sort-Object Count -Descending |
            Select-Object -First 5 | Format-Table Count, Name -AutoSize
    }
    
    # Alert se > 50 fallimenti
    if ($failedLogins.Count -gt 50) {
        Write-Host "[ALERT] > 50 login falliti in 24h — possibile attacco brute force!" -ForegroundColor Red
    }
} catch {
    Write-Host "Nessun evento trovato o log non disponibile" -ForegroundColor Gray
    Write-Host "(Genera qualche tentativo fallito per testare: ssh baduser@dc-lab-01 o login sbagliato RDP)"
}
```

**Step 3 — Analisi accessi privilegiati:**

```powershell
Write-Host ""
Write-Host "=== ACCESSI PRIVILEGIATI — ULTIMA SETTIMANA ===" -ForegroundColor Yellow

$since7d = (Get-Date).AddDays(-7)
try {
    $adminLogins = Get-WinEvent -FilterHashtable @{
        LogName   = 'Security'
        Id        = 4672
        StartTime = $since7d
    } -ErrorAction Stop |
    ForEach-Object {
        $xml = [xml]$_.ToXml()
        [PSCustomObject]@{
            Time    = $_.TimeCreated
            Account = $xml.Event.EventData.Data | Where-Object {$_.Name -eq "SubjectUserName"} | Select-Object -ExpandProperty '#text'
            Domain  = $xml.Event.EventData.Data | Where-Object {$_.Name -eq "SubjectDomainName"} | Select-Object -ExpandProperty '#text'
        }
    } | Where-Object { $_.Account -ne "SYSTEM" -and $_.Account -ne "LOCAL SERVICE" -and $_.Account -ne "NETWORK SERVICE" }
    
    Write-Host "Accessi privilegiati (Event 4672): $($adminLogins.Count)"
    
    $adminLogins | Group-Object Account | Sort-Object Count -Descending |
        Format-Table Count, Name, @{L="LastSeen";E={($_.Group | Sort-Object Time -Desc | Select-Object -First 1).Time}} -AutoSize
        
} catch {
    Write-Host "Nessun evento trovato" -ForegroundColor Gray
}
```

**Step 4 — Modifiche agli account (governance IAM):**

```powershell
Write-Host ""
Write-Host "=== MODIFICHE ACCOUNT — ULTIMI 7 GIORNI ===" -ForegroundColor Yellow

# Event IDs per gestione account
$accountMgmtEvents = @{
    4720 = "Account creato"
    4722 = "Account abilitato"
    4723 = "Password cambiata"
    4724 = "Password reimpostata"
    4725 = "Account disabilitato"
    4726 = "Account cancellato"
    4728 = "Aggiunto a Domain Admins"
    4732 = "Aggiunto a gruppo locale"
}

foreach ($eventId in $accountMgmtEvents.Keys | Sort-Object) {
    try {
        $events = Get-WinEvent -FilterHashtable @{
            LogName   = 'Security'
            Id        = $eventId
            StartTime = $since7d
        } -ErrorAction Stop
        
        if ($events.Count -gt 0) {
            Write-Host "  EventID $eventId — $($accountMgmtEvents[$eventId]): $($events.Count) occorrenze" -ForegroundColor Yellow
            $events | Select-Object -First 3 | ForEach-Object {
                Write-Host "    $($_.TimeCreated) | $($_.Message -replace '\r?\n.*', '')"
            }
        }
    } catch { }
}

# CRITICO: audit log cancellato
try {
    $logCleared = Get-WinEvent -FilterHashtable @{
        LogName   = 'Security'
        Id        = 1102
        StartTime = $since7d
    } -ErrorAction Stop
    
    if ($logCleared.Count -gt 0) {
        Write-Host ""
        Write-Host "[CRITICO] Log di sicurezza cancellato $($logCleared.Count) volte — investigare immediatamente!" -ForegroundColor Red
        $logCleared | Format-Table TimeCreated, Message -AutoSize
    }
} catch { }
```

**Checkpoint di verifica B2:**
- [ ] Audit policy abilitata per Logon, Account Management, Privilege Use
- [ ] Query Event ID 4625 funzionante
- [ ] Query Event ID 4672 mostra accessi admin
- [ ] Nessun Event ID 1102 (log cancellato) nel periodo

---

### Esercizio B3: Audit Log di Autenticazione Linux

**Obiettivo.** Analizzare i log di autenticazione su SRV-LINUX-01, identificare pattern sospetti, e costruire un report degli accessi privilegiati (sudo).

**Step 1 — Analisi login SSH:**

```bash
# Su SRV-LINUX-01 come lab-admin

echo "=== AUDIT LOGIN SSH — ULTIMI 7 GIORNI ==="

# Login riusciti SSH
echo "Login SSH riusciti:"
journalctl -u sshd --since "7 days ago" 2>/dev/null | \
    grep "Accepted" | \
    awk '{print $1, $2, $3, $9, "da", $11}' | \
    head -20

echo ""
echo "Login SSH falliti:"
journalctl -u sshd --since "7 days ago" 2>/dev/null | \
    grep -E "Failed password|Invalid user" | \
    awk '{print $1, $2, $3, $9, "utente:", $11, "da:", $13}' | \
    head -20

echo ""
echo "Statistiche (conteggi):"
echo "  Login riusciti SSH (7gg):    $(journalctl -u sshd --since '7 days ago' 2>/dev/null | grep -c 'Accepted' || echo 0)"
echo "  Login falliti SSH (7gg):     $(journalctl -u sshd --since '7 days ago' 2>/dev/null | grep -cE 'Failed|Invalid' || echo 0)"
echo "  Utenti unici che hanno fallito: $(journalctl -u sshd --since '7 days ago' 2>/dev/null | grep -oE 'invalid user \S+|Failed password for \S+' | awk '{print $NF}' | sort -u | wc -l)"
```

**Step 2 — Audit uso sudo:**

```bash
echo ""
echo "=== AUDIT SUDO — ULTIMI 7 GIORNI ==="

# Comandi eseguiti via sudo
echo "Comandi sudo eseguiti:"
journalctl --since "7 days ago" 2>/dev/null | \
    grep "sudo:" | \
    grep "COMMAND=" | \
    awk -F'COMMAND=' '{print $1, "→", $2}' | \
    head -20

echo ""
echo "Utenti che hanno usato sudo:"
journalctl --since "7 days ago" 2>/dev/null | \
    grep "sudo:" | \
    grep "COMMAND=" | \
    grep -oE '\w+ : TTY' | \
    awk '{print $1}' | \
    sort | uniq -c | sort -rn

echo ""
echo "Comandi sudo ad alto rischio (rm, passwd, useradd, chmod 777):"
journalctl --since "7 days ago" 2>/dev/null | \
    grep "sudo:" | \
    grep -E "COMMAND=.*(rm -rf|passwd|useradd|userdel|chmod 777|visudo)" | \
    awk -F'COMMAND=' '{print $1, "→", $2}'
```

**Step 3 — Audit accessi root:**

```bash
echo ""
echo "=== AUDIT ACCESSO ROOT ==="

# Login diretti root (devono essere zero con SSH configurato correttamente)
echo "Login root diretti (SSH):"
journalctl -u sshd --since "7 days ago" 2>/dev/null | grep "root" | grep "Accepted"
echo "(se vuoto: PermitRootLogin=no funziona correttamente)"

echo ""
echo "Sessioni su root via sudo su / su -:"
journalctl --since "7 days ago" 2>/dev/null | grep -E "su\[|sudo.*\-s.*root" | head -10

echo ""
echo "=== UTENTI LOCALI CON UID 0 (equivalenti root) ==="
awk -F: '$3==0 {print $1, "UID=0"}' /etc/passwd
echo "(solo 'root' dovrebbe avere UID=0)"
```

**Step 4 — Genera report accessi:**

```bash
echo ""
echo "=== REPORT ACCESSI SETTIMANALE — $(date '+%Y-%m-%d') ==="
echo ""

# Ultimi login riusciti per utente
echo "Ultimo accesso per utente (last):"
last -w -n 20 2>/dev/null | grep -v "^wtmp\|^$\|reboot" | head -15

echo ""
echo "Accessi falliti recenti (lastb - richiede root):"
sudo lastb 2>/dev/null | head -10 || echo "(lastb non disponibile senza privilegi root)"

echo ""
echo "=== FINE REPORT ==="
```

**Checkpoint di verifica B3:**
- [ ] Analisi journalctl SSH completata (login riusciti e falliti)
- [ ] Audit sudo mostra comandi eseguiti
- [ ] Nessun login root diretto via SSH
- [ ] Nessun utente con UID=0 oltre a root

---

### Esercizio B4: Simulazione RBAC in Active Directory

**Obiettivo.** Creare una struttura RBAC in AD con gruppi per ruolo, assegnare permessi ai gruppi, e verificare che l'accesso segua il principio del minimo privilegio.

**Background.** In un dominio AD, il RBAC si implementa con Gruppi di Sicurezza: si creano gruppi con nomi che rappresentano ruoli (es: "Commerciali", "HR", "IT Helpdesk"), si assegnano i permessi ai gruppi, e gli utenti vengono messi nei gruppi corrispondenti al loro ruolo. Questa struttura semplifica la gestione: quando un utente cambia ruolo, si sposta tra gruppi.

**Step 1 — Crea struttura RBAC di esempio:**

```powershell
# Su DC-LAB-01 come Administrator
Import-Module ActiveDirectory

Write-Host "=== SETUP RBAC — CREAZIONE RUOLI ==="

# Crea OU per la struttura RBAC
$rbacOUs = @("LAB-Users", "LAB-Security-Groups", "LAB-Service-Accounts")
foreach ($ou in $rbacOUs) {
    try {
        New-ADOrganizationalUnit -Name $ou -Path "DC=lab,DC=local" -ErrorAction Stop
        Write-Host "[OK] OU creata: $ou"
    } catch {
        Write-Host "[INFO] OU già esistente: $ou"
    }
}

# Crea gruppi di sicurezza (ruoli)
$roles = @{
    "LAB-Role-Commerciali"    = "Accesso CRM, File Vendite, Email"
    "LAB-Role-HR"             = "Accesso File HR, HRIS, Email"
    "LAB-Role-IT-Helpdesk"    = "Accesso strumenti helpdesk, lettura AD"
    "LAB-Role-Contabilita"    = "Accesso SAP, File Contabilità"
    "LAB-Role-Management"     = "Lettura report consolidati"
}

foreach ($role in $roles.Keys) {
    try {
        New-ADGroup -Name $role `
            -GroupScope Global `
            -GroupCategory Security `
            -Description $roles[$role] `
            -Path "OU=LAB-Security-Groups,DC=lab,DC=local" `
            -ErrorAction Stop
        Write-Host "[OK] Gruppo creato: $role — $($roles[$role])"
    } catch {
        Write-Host "[INFO] Gruppo già esistente: $role"
    }
}
```

**Step 2 — Crea utenti demo e assegna ruoli:**

```powershell
Write-Host ""
Write-Host "=== CREAZIONE UTENTI DEMO ==="

$testUsers = @(
    @{Name="Mario Rossi";    Sam="mario.rossi";  Role="LAB-Role-Commerciali"; Dept="Vendite"},
    @{Name="Giulia Bianchi"; Sam="giulia.bianchi"; Role="LAB-Role-HR"; Dept="HR"},
    @{Name="Luca Ferrari";   Sam="luca.ferrari";  Role="LAB-Role-Contabilita"; Dept="Amministrazione"},
    @{Name="Sara Verdi";     Sam="sara.verdi";    Role="LAB-Role-IT-Helpdesk"; Dept="IT"}
)

$secPwd = ConvertTo-SecureString "Lab@2024!" -AsPlainText -Force

foreach ($u in $testUsers) {
    try {
        New-ADUser -Name $u.Name `
            -SamAccountName $u.Sam `
            -UserPrincipalName "$($u.Sam)@lab.local" `
            -Department $u.Dept `
            -Path "OU=LAB-Users,DC=lab,DC=local" `
            -AccountPassword $secPwd `
            -Enabled $true `
            -PasswordNeverExpires $false `
            -ErrorAction Stop
        Write-Host "[OK] Utente creato: $($u.Name) ($($u.Sam))"
    } catch {
        Write-Host "[INFO] Utente già esistente: $($u.Sam)"
    }
    
    # Assegna ruolo
    try {
        Add-ADGroupMember -Identity $u.Role -Members $u.Sam -ErrorAction Stop
        Write-Host "[OK] Ruolo assegnato: $($u.Sam) → $($u.Role)"
    } catch {
        Write-Host "[INFO] Già membro del gruppo"
    }
}
```

**Step 3 — Verifica struttura RBAC:**

```powershell
Write-Host ""
Write-Host "=== VERIFICA STRUTTURA RBAC ===" -ForegroundColor Cyan

# Per ogni ruolo, mostra i membri
$roleGroups = Get-ADGroup -Filter {Name -like "LAB-Role-*"} -Properties Description
foreach ($group in $roleGroups) {
    $members = Get-ADGroupMember -Identity $group
    Write-Host ""
    Write-Host "Ruolo: $($group.Name)" -ForegroundColor Yellow
    Write-Host "       $($group.Description)"
    if ($members.Count -gt 0) {
        $members | ForEach-Object { Write-Host "  → $($_.Name) ($($_.SamAccountName))" }
    } else {
        Write-Host "  → (nessun membro)" -ForegroundColor Gray
    }
}

# Per ogni utente, mostra i ruoli
Write-Host ""
Write-Host "=== MATRICE UTENTE → RUOLO ===" -ForegroundColor Cyan
$labUsers = Get-ADUser -Filter * -SearchBase "OU=LAB-Users,DC=lab,DC=local" -ErrorAction SilentlyContinue
if ($labUsers) {
    foreach ($user in $labUsers) {
        $userGroups = Get-ADPrincipalGroupMembership -Identity $user.SamAccountName |
            Where-Object { $_.Name -like "LAB-Role-*" } |
            Select-Object -ExpandProperty Name
        Write-Host "$($user.Name) → $($userGroups -join ', ')"
    }
}
```

**Step 4 — Simula cambio ruolo (onboarding/offboarding parziale):**

```powershell
Write-Host ""
Write-Host "=== SIMULAZIONE CAMBIO RUOLO ===" -ForegroundColor Yellow
Write-Host "Scenario: Mario Rossi passa da Vendite a Management"
Write-Host ""

# Rimuovi vecchio ruolo
Remove-ADGroupMember -Identity "LAB-Role-Commerciali" -Members "mario.rossi" -Confirm:$false
Write-Host "[OK] Rimosso da LAB-Role-Commerciali"

# Assegna nuovo ruolo
Add-ADGroupMember -Identity "LAB-Role-Management" -Members "mario.rossi"
Write-Host "[OK] Aggiunto a LAB-Role-Management"

# Verifica
$newGroups = Get-ADPrincipalGroupMembership -Identity "mario.rossi" |
    Where-Object { $_.Name -like "LAB-Role-*" }
Write-Host "Nuovi ruoli di Mario Rossi: $($newGroups.Name -join ', ')"
Write-Host "(NON ha più accesso a File Vendite e CRM — principio minimo privilegio)"
```

**Checkpoint di verifica B4:**
- [ ] OU LAB-Users e LAB-Security-Groups create
- [ ] 4 gruppi di ruolo creati con descrizione appropriata
- [ ] 4 utenti demo creati e assegnati ai rispettivi ruoli
- [ ] Cambio ruolo eseguito correttamente (vecchio ruolo rimosso, nuovo assegnato)

---

### Esercizio B5: Audit Certificati TLS — Controllare la Scadenza

**Obiettivo.** Verificare la scadenza dei certificati TLS sui servizi lab e scrivere uno script di monitoraggio che avvisa prima della scadenza.

**Background.** I certificati TLS scaduti causano interruzioni immediate: browser bloccano l'accesso, servizi rifiutano connessioni, autenticazioni falliscono. In produzione, un certificato scaduto inaspettatamente è quasi sempre un incidente P1. Il monitoring proattivo con alert a 90/60/30/7 giorni dalla scadenza previene questi incidenti.

**Step 1 — Verifica certificati su SRV-LINUX-01:**

```bash
# Su SRV-LINUX-01

echo "=== AUDIT CERTIFICATI TLS ==="

# Controlla certificato GLPI (se HTTPS configurato, altrimenti HTTP)
# Per HTTP puro, non c'è certificato da verificare — mostra esempio openssl

echo "1. Verifica certificato self-signed DC-LAB-01 (AD LDAPS/HTTPS):"
echo | openssl s_client -connect 192.168.56.10:443 -servername dc-lab-01 2>/dev/null | \
    openssl x509 -noout -dates -subject 2>/dev/null || \
    echo "   [INFO] Nessun servizio HTTPS su DC-LAB-01:443 nel lab base"

echo ""
echo "2. Verifica certificati locali installati:"
# Elenca certificati nel sistema
ls /etc/ssl/certs/ 2>/dev/null | head -10
echo "(Certificati CA di sistema, non servizi custom)"

echo ""
echo "3. Genera certificato self-signed di esempio (per test):"
openssl req -x509 -newkey rsa:2048 -keyout /tmp/test-key.pem -out /tmp/test-cert.pem \
    -days 365 -nodes -subj "/CN=srv-linux-01.lab.local/O=Lab/C=IT" 2>/dev/null && \
    echo "[OK] Certificato di test creato in /tmp/"

echo ""
echo "4. Ispeziona il certificato di test:"
openssl x509 -in /tmp/test-cert.pem -noout -text | grep -E "Subject:|Not Before:|Not After:|Issuer:"
```

**Step 2 — Script monitoraggio scadenza certificati:**

```bash
# Funzione per controllare scadenza certificato su host:porta
check_cert_expiry() {
    local host=$1
    local port=${2:-443}
    local warn_days=${3:-30}
    
    local expiry
    expiry=$(echo | openssl s_client -connect "${host}:${port}" -servername "${host}" 2>/dev/null | \
        openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)
    
    if [ -z "$expiry" ]; then
        echo "[INFO] $host:$port — certificato non accessibile o non TLS"
        return
    fi
    
    local expiry_epoch now_epoch days_left
    expiry_epoch=$(date -d "$expiry" +%s 2>/dev/null)
    now_epoch=$(date +%s)
    days_left=$(( (expiry_epoch - now_epoch) / 86400 ))
    
    if [ "$days_left" -lt 0 ]; then
        echo "[CRIT] $host:$port — SCADUTO da $((days_left * -1)) giorni!"
    elif [ "$days_left" -lt 7 ]; then
        echo "[CRIT] $host:$port — scade tra $days_left giorni — URGENTE!"
    elif [ "$days_left" -lt 30 ]; then
        echo "[WARN] $host:$port — scade tra $days_left giorni"
    else
        echo "[OK]   $host:$port — scade tra $days_left giorni ($expiry)"
    fi
}

# Test con host pubblici (se connettività esterna disponibile)
echo "=== MONITORAGGIO CERTIFICATI ==="
check_cert_expiry "google.com" 443
check_cert_expiry "github.com" 443

# Certificato locale di test (auto-generato sopra, 365 giorni)
echo ""
echo "Certificato self-signed di test:"
expiry=$(openssl x509 -in /tmp/test-cert.pem -noout -enddate 2>/dev/null | cut -d= -f2)
echo "  Scade: $expiry"
expiry_epoch=$(date -d "$expiry" +%s 2>/dev/null)
now_epoch=$(date +%s)
days_left=$(( (expiry_epoch - now_epoch) / 86400 ))
echo "  Giorni rimanenti: $days_left"
```

**Step 3 — Verifica certificati Windows (DC-LAB-01):**

```powershell
# Su DC-LAB-01 — audit certificati nel certificate store

Write-Host "=== AUDIT CERTIFICATI WINDOWS ===" -ForegroundColor Cyan

$threshold30  = (Get-Date).AddDays(30)
$threshold7   = (Get-Date).AddDays(7)

# Certificati per tutti i computer/server stores
$stores = @("LocalMachine\My", "LocalMachine\WebHosting")

foreach ($storePath in $stores) {
    $certs = Get-ChildItem "Cert:\$storePath" -ErrorAction SilentlyContinue
    if ($certs.Count -gt 0) {
        Write-Host ""
        Write-Host "Store: $storePath ($($certs.Count) certificati)"
        
        foreach ($cert in $certs) {
            $daysLeft = ($cert.NotAfter - (Get-Date)).Days
            $color = if ($daysLeft -lt 0) { "Red" } 
                     elseif ($daysLeft -lt 7) { "Red" }
                     elseif ($daysLeft -lt 30) { "Yellow" } 
                     else { "Green" }
            
            Write-Host "  $(if ($daysLeft -lt 0) {'[SCADUTO]'} elseif ($daysLeft -lt 30) {'[WARN]'} else {'[OK]'})" `
                -ForegroundColor $color -NoNewline
            Write-Host " $($cert.Subject) — scade: $($cert.NotAfter.ToString('yyyy-MM-dd')) ($daysLeft giorni)"
        }
    }
}

Write-Host ""
Write-Host "=== RINNOVO CERTBOT (se applicabile) ==="
Write-Host "Per Let's Encrypt: certbot renew --dry-run"
Write-Host "Per AD CS: Get-CATemplate, certenroll"
```

**Checkpoint di verifica B5:**
- [ ] Certificato self-signed generato e ispezionato con openssl
- [ ] Funzione check_cert_expiry funzionante
- [ ] Audit Windows certificate store completato
- [ ] Nessun certificato scaduto trovato

---

### Esercizio B6: Simulazione Offboarding — Deprovisioning Sicuro

**Obiettivo.** Simulare il processo di offboarding completo di un utente AD, eseguendo tutte le operazioni nella sequenza corretta e documentando l'evidenza.

**Background.** L'offboarding è il momento più critico dell'identity lifecycle. Un accesso non disabilitato è una backdoor permanente. In molte organizzazioni, la sequenza è: HR notifica IT → IT esegue checklist → si documenta. La velocità dipende dal tipo di uscita: per licenziamento, le credenziali devono essere disabilitate prima che l'interessato venga informato.

**Step 1 — Esegui offboarding completo di mario.rossi:**

```powershell
# Su DC-LAB-01 come Administrator
Import-Module ActiveDirectory

$userName = "mario.rossi"
$exitDate = Get-Date -Format "yyyy-MM-dd"

Write-Host "=== OFFBOARDING: $userName — Data: $exitDate ===" -ForegroundColor Yellow
Write-Host ""

# 1. Verifica che l'utente esista
$user = Get-ADUser -Identity $userName -Properties * -ErrorAction SilentlyContinue
if (-not $user) {
    Write-Host "[ERRORE] Utente $userName non trovato" -ForegroundColor Red
    return
}
Write-Host "Utente trovato: $($user.Name) — $($user.Department)"

# 2. Disabilita account
Disable-ADAccount -Identity $userName
Write-Host "[OK] Account DISABILITATO"

# 3. Reimposta password (previene accesso anche se account non venisse disabilitato)
$newPwd = ConvertTo-SecureString ([System.Web.Security.Membership]::GeneratePassword(20, 4)) -AsPlainText -Force 2>$null
if (-not $?) {
    # Fallback password sicura
    $newPwd = ConvertTo-SecureString "X#$(Get-Random -Min 10000 -Max 99999)!$(Get-Random -Min 10000 -Max 99999)zK" -AsPlainText -Force
}
Set-ADAccountPassword -Identity $userName -NewPassword $newPwd -Reset
Write-Host "[OK] Password reimpostata a valore casuale (non noto a nessuno)"

# 4. Revoca tutti i gruppi AD (tranne Domain Users che è il default)
$groups = Get-ADPrincipalGroupMembership -Identity $userName | 
    Where-Object { $_.Name -ne "Domain Users" }

foreach ($group in $groups) {
    Remove-ADGroupMember -Identity $group.Name -Members $userName -Confirm:$false
    Write-Host "[OK] Rimosso dal gruppo: $($group.Name)"
}

# 5. Sposta l'account in OU "Disabled" (per pulizia, non cancellazione immediata)
try {
    # Crea OU Disabled se non esiste
    New-ADOrganizationalUnit -Name "Disabled-Accounts" -Path "DC=lab,DC=local" -ErrorAction SilentlyContinue
    Move-ADObject -Identity $user.DistinguishedName -TargetPath "OU=Disabled-Accounts,DC=lab,DC=local"
    Write-Host "[OK] Account spostato in OU Disabled-Accounts"
} catch {
    Write-Host "[INFO] Spostamento OU non riuscito (possibile già in posizione): $_"
}

# 6. Aggiungi nota sulla disabilitazione
Set-ADUser -Identity $userName -Description "DISABILITATO: $exitDate — Offboarding procedure"
Write-Host "[OK] Description aggiornata con data offboarding"

# 7. Report di evidenza
Write-Host ""
Write-Host "=== EVIDENZA OFFBOARDING ===" -ForegroundColor Cyan
Write-Host "Utente:          $($user.Name) ($userName)"
Write-Host "Data/ora:        $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "Eseguito da:     $env:USERNAME su $env:COMPUTERNAME"
Write-Host "Azioni eseguite:"
Write-Host "  [x] Account disabilitato"
Write-Host "  [x] Password reimpostata"
Write-Host "  [x] Rimosso da $($groups.Count) gruppi"
Write-Host "  [x] Account spostato in OU Disabled"
Write-Host "  [x] Description aggiornata"
Write-Host ""
Write-Host "AZIONI RIMANENTI (manuali):"
Write-Host "  [ ] Revocare accesso VPN"
Write-Host "  [ ] Revocare badge accesso fisico"
Write-Host "  [ ] Reindirizzare casella email al manager"
Write-Host "  [ ] Revocare sessioni OAuth applicazioni SaaS"
Write-Host "  [ ] Informare il responsabile della coda email"
```

**Step 2 — Verifica che l'account non possa più autenticarsi:**

```powershell
# Verifica stato post-offboarding
$userState = Get-ADUser -Identity $userName -Properties Enabled, MemberOf, Description
Write-Host ""
Write-Host "Verifica post-offboarding per $userName:"
Write-Host "  Abilitato: $($userState.Enabled)  (deve essere False)"
Write-Host "  Gruppi: $($userState.MemberOf.Count) (deve essere 1 - solo Domain Users)"
Write-Host "  Descrizione: $($userState.Description)"
```

**Checkpoint di verifica B6:**
- [ ] Account mario.rossi disabilitato (Enabled = False)
- [ ] Password cambiata (casuale e non nota)
- [ ] Rimosso da tutti i gruppi di ruolo
- [ ] Description aggiornata con data offboarding
- [ ] Checklist azioni manuali restanti identificata

---
---

## PART C: SISTEMATIZZARE — Audit Accessi come Processo Ricorrente

---

### Progetto C1: SOP-ACCESS-001 — Revisione Trimestrale degli Accessi

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  SOP-ACCESS-001 — Revisione Trimestrale degli Accessi (Access Review)       ║
║  Versione: 1.0 | Data: 2026-07-15 | Frequenza: Trimestrale                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  SCOPO                                                                       ║
║  Garantire che ogni utente abbia solo gli accessi necessari per il suo       ║
║  ruolo attuale. Rilevare e rimuovere: account stale, role creep,            ║
║  privilege sprawl. Produrre evidenza documentata per audit di compliance.   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  OWNER: IT Security / Identity Team                                          ║
║  APPROVAZIONE: IT Manager                                                    ║
║  DISTRIBUZIONE: Team IT, Responsabili HR, Responsabili di funzione          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  FASE 1 — PREPARAZIONE (settimana 1)                                         ║
║  [ ] Genera report: lista tutti gli account abilitati + gruppi di           ║
║      appartenenza + ultimo accesso (script ad_access_audit.ps1)             ║
║  [ ] Genera report: account stale (> 90 gg senza login)                    ║
║  [ ] Genera report: password non cambiate > 180 gg                         ║
║  [ ] Genera report: utenti in gruppi privilegiati (Domain Admins, etc.)     ║
║  [ ] Divide il report per responsabile di funzione (HR, Vendite, IT...)     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  FASE 2 — REVISIONE RESPONSABILI (settimane 2-3)                             ║
║  Ogni responsabile riceve la lista dei propri collaboratori                  ║
║  Per ogni accesso risponde: CONFERMA o REVOCA                               ║
║  [ ] Account di ex-dipendenti → REVOCA immediata                           ║
║  [ ] Account di dipendenti cambiati di ruolo → revisione permessi          ║
║  [ ] Accessi non utilizzati da 90 gg → REVOCA o giustificazione            ║
║  SLA: Responsabili devono rispondere entro 10 giorni lavorativi            ║
║  Escalation: accessi non confermati entro SLA → revoca automatica          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  FASE 3 — IMPLEMENTAZIONE REVOCHE (settimana 4)                              ║
║  [ ] Applica tutte le revoche approvate in AD                               ║
║  [ ] Disabilita account stale non confermati                                ║
║  [ ] Verifica che le revoche siano effettive (re-test accesso)             ║
║  [ ] Documenta ogni modifica con ticket GLPI (categoria: IAM)              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  FASE 4 — DOCUMENTAZIONE E REPORT (fine trimestre)                           ║
║  [ ] Genera report finale: account revocati, account confermati            ║
║  [ ] Archivia evidenze (export CSV con hash SHA256) per 2 anni             ║
║  [ ] Pianifica prossimo ciclo (+3 mesi)                                    ║
║  Output: ticket GLPI chiuso con allegato report firmato                     ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  METRICHE DI SUCCESSO                                                        ║
║  % account revocati vs confermati → obiettivo: < 10% revocati              ║
║  % responsabili che hanno risposto entro SLA → obiettivo: > 90%            ║
║  Account stale rilevati → target: zero dopo ogni ciclo                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

### Progetto C2: Script — `ad_access_audit.ps1` (DC-LAB-01)

```powershell
<#
.SYNOPSIS
    Audit completo degli accessi Active Directory per revisione trimestrale
.DESCRIPTION
    Genera report in formato CSV e testo:
    - Inventario account con ultimo accesso
    - Account stale (> 90 giorni senza login)
    - Membri gruppi privilegiati
    - Account con configurazioni non conformi (password senza scadenza, ecc.)
    - Registro modifiche recenti (Event Log)
.PARAMETER OutputDir
    Cartella dove salvare i report (default: C:\SecurityAudit\<data>)
.PARAMETER StaleDays
    Numero di giorni per considerare un account stale (default: 90)
.EXAMPLE
    .\ad_access_audit.ps1
    .\ad_access_audit.ps1 -OutputDir "C:\Audit\Q3-2026" -StaleDays 60
#>

[CmdletBinding()]
param(
    [string]$OutputDir   = "C:\SecurityAudit\$(Get-Date -Format 'yyyy-MM-dd')",
    [int]   $StaleDays   = 90,
    [switch]$IncludeEventLog
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Import-Module ActiveDirectory -ErrorAction Stop

# Crea directory output
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
Write-Host "Output directory: $OutputDir" -ForegroundColor Cyan

$AuditDate  = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$StaleDate  = (Get-Date).AddDays(-$StaleDays)
$PwdOldDate = (Get-Date).AddDays(-180)

Write-Host "Data audit:   $AuditDate"
Write-Host "Soglia stale: $StaleDays giorni (prima del $($StaleDate.ToString('yyyy-MM-dd')))"
Write-Host ""

# ─── 1. INVENTARIO COMPLETO ACCOUNT ─────────────────────────────────────────

Write-Host "1/5 Inventario account..." -NoNewline

$allUsers = Get-ADUser -Filter * -Properties `
    Enabled, Department, Title, Manager,
    LastLogonDate, PasswordLastSet, PasswordNeverExpires,
    PasswordExpired, LockedOut, Description,
    MemberOf, Created, Modified |
ForEach-Object {
    $user = $_
    $managerName = if ($user.Manager) { 
        (Get-ADUser -Identity $user.Manager -ErrorAction SilentlyContinue).Name 
    } else { "N/A" }
    
    $staleDays = if ($user.LastLogonDate) {
        [math]::Round(((Get-Date) - $user.LastLogonDate).TotalDays, 0)
    } else { -1 }  # -1 = mai usato
    
    [PSCustomObject]@{
        SamAccountName     = $user.SamAccountName
        DisplayName        = $user.Name
        Enabled            = $user.Enabled
        Department         = $user.Department
        Title              = $user.Title
        Manager            = $managerName
        LastLogonDate      = if ($user.LastLogonDate) { $user.LastLogonDate.ToString("yyyy-MM-dd") } else { "MAI" }
        DaysSinceLogin     = $staleDays
        PasswordLastSet    = if ($user.PasswordLastSet) { $user.PasswordLastSet.ToString("yyyy-MM-dd") } else { "N/A" }
        PasswordNeverExp   = $user.PasswordNeverExpires
        PasswordExpired    = $user.PasswordExpired
        AccountLocked      = $user.LockedOut
        GroupCount         = $user.MemberOf.Count
        Created            = $user.Created.ToString("yyyy-MM-dd")
        Description        = $user.Description
    }
}

$inventoryPath = Join-Path $OutputDir "01_inventory_all_accounts.csv"
$allUsers | Export-Csv -Path $inventoryPath -NoTypeInformation -Encoding UTF8
Write-Host " OK ($($allUsers.Count) account)" -ForegroundColor Green

# ─── 2. ACCOUNT STALE ────────────────────────────────────────────────────────

Write-Host "2/5 Account stale..." -NoNewline

$staleAccounts = $allUsers | Where-Object {
    $_.Enabled -eq $true -and ($_.DaysSinceLogin -gt $StaleDays -or $_.DaysSinceLogin -eq -1)
}

$stalePath = Join-Path $OutputDir "02_stale_accounts.csv"
$staleAccounts | Export-Csv -Path $stalePath -NoTypeInformation -Encoding UTF8
Write-Host " OK ($($staleAccounts.Count) account stale)" -ForegroundColor $(if ($staleAccounts.Count -gt 0) {"Yellow"} else {"Green"})

# ─── 3. GRUPPI PRIVILEGIATI ───────────────────────────────────────────────────

Write-Host "3/5 Gruppi privilegiati..." -NoNewline

$privilegedGroups = @(
    "Domain Admins", "Enterprise Admins", "Schema Admins",
    "Administrators", "Account Operators", "Backup Operators",
    "Server Operators", "Print Operators", "Group Policy Creator Owners"
)

$privReport = @()
foreach ($groupName in $privilegedGroups) {
    try {
        $members = Get-ADGroupMember -Identity $groupName -ErrorAction Stop
        foreach ($m in $members) {
            if ($m.objectClass -eq "user") {
                $u = Get-ADUser -Identity $m.SamAccountName -Properties Enabled, LastLogonDate -ErrorAction SilentlyContinue
                $privReport += [PSCustomObject]@{
                    Group         = $groupName
                    UserName      = $m.SamAccountName
                    DisplayName   = $m.Name
                    Enabled       = if ($u) { $u.Enabled } else { "N/A" }
                    LastLogonDate = if ($u -and $u.LastLogonDate) { $u.LastLogonDate.ToString("yyyy-MM-dd") } else { "MAI" }
                    Risk          = if ($u -and -not $u.Enabled) { "ALTO — disabilitato ma ancora nel gruppo" }
                                    elseif ($u -and $u.LastLogonDate -lt $StaleDate) { "MEDIO — stale" }
                                    else { "Normale" }
                }
            }
        }
    } catch {
        $privReport += [PSCustomObject]@{
            Group="$groupName"; UserName="ERROR"; DisplayName="$_"
            Enabled="N/A"; LastLogonDate="N/A"; Risk="N/A"
        }
    }
}

$privPath = Join-Path $OutputDir "03_privileged_group_members.csv"
$privReport | Export-Csv -Path $privPath -NoTypeInformation -Encoding UTF8
Write-Host " OK ($($privReport.Count) membri privilegiati)" -ForegroundColor Green

# ─── 4. CONFIGURAZIONI NON CONFORMI ─────────────────────────────────────────

Write-Host "4/5 Configurazioni non conformi..." -NoNewline

$nonConformant = @()

# Password senza scadenza su utenti non-service
$pwdNoExpiry = $allUsers | Where-Object {
    $_.Enabled -eq $true -and $_.PasswordNeverExp -eq $true -and
    $_.SamAccountName -notmatch "^svc-|^service-|^krbtgt|^MSOL_|^AAD_"
}
foreach ($u in $pwdNoExpiry) {
    $nonConformant += [PSCustomObject]@{
        Issue          = "PasswordNeverExpires"
        SamAccountName = $u.SamAccountName
        DisplayName    = $u.DisplayName
        Detail         = "Account abilitato con password senza scadenza — non è service account riconosciuto"
        Severity       = "MEDIO"
    }
}

# Password vecchia (> 180 giorni)
$pwdOld = $allUsers | Where-Object {
    $_.Enabled -eq $true -and $_.PasswordLastSet -ne "N/A" -and
    [datetime]::Parse($_.PasswordLastSet) -lt $PwdOldDate
}
foreach ($u in $pwdOld) {
    $nonConformant += [PSCustomObject]@{
        Issue          = "PasswordOldAge"
        SamAccountName = $u.SamAccountName
        DisplayName    = $u.DisplayName
        Detail         = "Password invariata dal $($u.PasswordLastSet) (> 180 giorni)"
        Severity       = "BASSO"
    }
}

# Account bloccati
$locked = $allUsers | Where-Object { $_.AccountLocked -eq $true }
foreach ($u in $locked) {
    $nonConformant += [PSCustomObject]@{
        Issue          = "AccountLocked"
        SamAccountName = $u.SamAccountName
        DisplayName    = $u.DisplayName
        Detail         = "Account bloccato — verificare causa e sbloccare se legittimo"
        Severity       = "INFO"
    }
}

$nonConfPath = Join-Path $OutputDir "04_non_conformant_accounts.csv"
$nonConformant | Export-Csv -Path $nonConfPath -NoTypeInformation -Encoding UTF8
Write-Host " OK ($($nonConformant.Count) problemi)" -ForegroundColor $(if ($nonConformant.Count -gt 0) {"Yellow"} else {"Green"})

# ─── 5. RIEPILOGO ESECUTIVO ──────────────────────────────────────────────────

Write-Host "5/5 Riepilogo..." -NoNewline

$summaryPath = Join-Path $OutputDir "00_RIEPILOGO.txt"
@"
═══════════════════════════════════════════════════════
  AUDIT ACCESSI ACTIVE DIRECTORY
  Data: $AuditDate
  Dominio: $(Get-ADDomain | Select-Object -ExpandProperty DNSRoot)
═══════════════════════════════════════════════════════

STATISTICHE:
  Utenti totali:                $($allUsers.Count)
  Utenti abilitati:             $(($allUsers | Where-Object Enabled).Count)
  Utenti disabilitati:          $(($allUsers | Where-Object {-not $_.Enabled}).Count)
  Account stale (> $StaleDays gg):    $($staleAccounts.Count)
  Problemi conformità:          $($nonConformant.Count)

GRUPPI PRIVILEGIATI:
$(foreach ($g in ($privReport | Group-Object Group)) { "  $($g.Name): $($g.Count) membri" })

AZIONI RICHIESTE:
$(if ($staleAccounts.Count -gt 0) {"  ! $($staleAccounts.Count) account stale da rivedere (02_stale_accounts.csv)"})
$(if (($nonConformant | Where-Object Severity -eq "MEDIO").Count -gt 0) {"  ! $(($nonConformant | Where-Object Severity -eq 'MEDIO').Count) problemi MEDI da risolvere"})
$(if (($privReport | Where-Object Risk -like "ALTO*").Count -gt 0) {"  ! $(($privReport | Where-Object Risk -like 'ALTO*').Count) account privilegiati ad alto rischio"})

FILE GENERATI:
  01_inventory_all_accounts.csv
  02_stale_accounts.csv
  03_privileged_group_members.csv
  04_non_conformant_accounts.csv

Archivia questi file con hash SHA256 per evidenza di audit.
SHA256 inventario: $((Get-FileHash $inventoryPath -Algorithm SHA256).Hash)
═══════════════════════════════════════════════════════
"@ | Set-Content -Path $summaryPath -Encoding UTF8

Write-Host " OK" -ForegroundColor Green
Write-Host ""
Get-Content $summaryPath
Write-Host ""
Write-Host "Report salvati in: $OutputDir" -ForegroundColor Cyan
```

**Uso:**
```powershell
# Installa script
New-Item -ItemType Directory -Path C:\Scripts -Force | Out-Null
Copy-Item .\ad_access_audit.ps1 C:\Scripts\

# Esecuzione audit trimestrale
.\C:\Scripts\ad_access_audit.ps1

# Con Event Log (accessi recenti)
.\C:\Scripts\ad_access_audit.ps1 -OutputDir "C:\Audit\Q3-2026" -StaleDays 90

# Pianifica come Scheduled Task (ogni primo lunedì del trimestre)
$action  = New-ScheduledTaskAction -Execute "powershell.exe" `
           -Argument "-ExecutionPolicy RemoteSigned -File C:\Scripts\ad_access_audit.ps1"
$trigger = New-ScheduledTaskTrigger -Weekly -WeeksInterval 13 -DaysOfWeek Monday -At 06:00
Register-ScheduledTask -TaskName "Quarterly Access Audit" `
    -Action $action -Trigger $trigger -RunLevel Highest
```

---

### Progetto C3: Script — `linux_auth_audit.sh` (SRV-LINUX-01)

```bash
#!/usr/bin/env bash
# linux_auth_audit.sh — Audit autenticazione e accessi Linux
# Uso: sudo ./linux_auth_audit.sh [--days N] [--json]
# Report: accessi SSH, uso sudo, anomalie, account locali

set -euo pipefail

readonly SCRIPT_VERSION="1.0.0"
DAYS=30
JSON_OUTPUT=false

while [[ "${1:-}" != "" ]]; do
    case $1 in
        --days)  shift; DAYS=$1 ;;
        --json)  JSON_OUTPUT=true ;;
    esac
    shift
done

readonly SINCE="$DAYS days ago"
readonly REPORT_DATE=$(date '+%Y-%m-%d %H:%M:%S')

FINDINGS=()
STATUS=0

log_ok()   { [[ "$JSON_OUTPUT" == false ]] && printf '\e[32m[OK]\e[0m   %s\n' "$1" || true; }
log_warn() { [[ "$JSON_OUTPUT" == false ]] && printf '\e[33m[WARN]\e[0m %s\n' "$1" || true; FINDINGS+=("WARN: $1"); [[ $STATUS -lt 1 ]] && STATUS=1; }
log_crit() { [[ "$JSON_OUTPUT" == false ]] && printf '\e[31m[CRIT]\e[0m %s\n' "$1" || true; FINDINGS+=("CRIT: $1"); STATUS=2; }
log_info() { [[ "$JSON_OUTPUT" == false ]] && printf '       %s\n' "$1" || true; }
section()  { [[ "$JSON_OUTPUT" == false ]] && printf '\n\e[36m── %s ──\e[0m\n' "$1" || true; }

# ─── SEZIONE 1: ACCOUNT LOCALI ───────────────────────────────────────────────

section "Account locali"

# Utenti con shell interattiva (possono fare login)
mapfile -t login_users < <(getent passwd | awk -F: '$7 !~ /nologin|false|sync|shutdown|halt/ && $3 >= 1000 {print $1":"$3}')
log_info "Utenti con login possibile: ${#login_users[@]}"
for u in "${login_users[@]}"; do
    log_info "  → $u"
done

# Utenti con UID 0 oltre a root
extra_root=$(awk -F: '$3==0 && $1!="root" {print $1}' /etc/passwd)
if [[ -n "$extra_root" ]]; then
    log_crit "Utenti con UID=0 oltre root: $extra_root"
else
    log_ok "Nessun utente non-root con UID=0"
fi

# Utenti nel gruppo sudo
sudo_members=$(getent group sudo 2>/dev/null | cut -d: -f4)
if [[ -n "$sudo_members" ]]; then
    sudo_count=$(echo "$sudo_members" | tr ',' '\n' | wc -l)
    log_info "Membri gruppo sudo ($sudo_count): $sudo_members"
    if [[ "$sudo_count" -gt 3 ]]; then
        log_warn "Più di 3 utenti nel gruppo sudo — verificare se tutti necessari"
    else
        log_ok "Numero utenti sudo: $sudo_count (accettabile)"
    fi
fi

# ─── SEZIONE 2: ACCESSI SSH ──────────────────────────────────────────────────

section "Accessi SSH (ultimi $DAYS giorni)"

ssh_success=$(journalctl -u ssh -u sshd --since "$SINCE" 2>/dev/null | \
    grep -c "Accepted" 2>/dev/null || echo 0)
ssh_failed=$(journalctl -u ssh -u sshd --since "$SINCE" 2>/dev/null | \
    grep -cE "Failed password|Invalid user" 2>/dev/null || echo 0)

log_info "Login SSH riusciti: $ssh_success"
log_info "Login SSH falliti: $ssh_failed"

# Ratio falliti/riusciti
if [[ "$ssh_success" -gt 0 && "$ssh_failed" -gt $(( ssh_success * 5 )) ]]; then
    log_warn "Alto rapporto falliti/riusciti ($ssh_failed/$ssh_success) — possibile scanning"
elif [[ "$ssh_failed" -gt 200 ]]; then
    log_crit "Oltre 200 login falliti SSH — verifica fail2ban e origin IP"
elif [[ "$ssh_failed" -gt 50 ]]; then
    log_warn "Più di 50 login falliti SSH — monitorare"
else
    log_ok "Tentativi login falliti SSH: $ssh_failed (normale)"
fi

# Top IP che hanno fallito
section_top=$(journalctl -u ssh -u sshd --since "$SINCE" 2>/dev/null | \
    grep -oE 'from [0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | awk '{print $2}' | \
    sort | uniq -c | sort -rn | head -5 2>/dev/null || true)
if [[ -n "$section_top" ]]; then
    log_info "Top IP con tentativi falliti:"
    while IFS= read -r line; do
        log_info "  $line"
    done <<< "$section_top"
fi

# Login root SSH
root_ssh=$(journalctl -u ssh -u sshd --since "$SINCE" 2>/dev/null | \
    grep "Accepted.*root" | wc -l || echo 0)
if [[ "$root_ssh" -gt 0 ]]; then
    log_crit "Login root SSH riusciti: $root_ssh — root non dovrebbe poter fare login!"
else
    log_ok "Nessun login root SSH (PermitRootLogin=no funziona)"
fi

# ─── SEZIONE 3: USO SUDO ────────────────────────────────────────────────────

section "Uso sudo (ultimi $DAYS giorni)"

sudo_total=$(journalctl --since "$SINCE" 2>/dev/null | \
    grep "sudo:.*COMMAND=" | wc -l || echo 0)
log_info "Comandi sudo eseguiti: $sudo_total"

# Comandi ad alto rischio
for risky_cmd in "rm -rf" "passwd " "useradd " "userdel " "visudo" "chmod 777" "dd if="; do
    risky_count=$(journalctl --since "$SINCE" 2>/dev/null | \
        grep "sudo:.*COMMAND=.*${risky_cmd}" | wc -l || echo 0)
    if [[ "$risky_count" -gt 0 ]]; then
        log_warn "Comando ad alto rischio eseguito via sudo ($risky_count volte): $risky_cmd"
    fi
done

# Utenti che usano sudo
sudo_users=$(journalctl --since "$SINCE" 2>/dev/null | \
    grep "sudo:.*COMMAND=" | grep -oE '^\w+ \w+ \S+ \w+' | \
    awk '{print $4}' | sort -u 2>/dev/null || true)
if [[ -n "$sudo_users" ]]; then
    log_info "Utenti che hanno usato sudo:"
    while IFS= read -r u; do
        local_count=$(journalctl --since "$SINCE" 2>/dev/null | \
            grep "sudo:.*$u.*COMMAND=" | wc -l 2>/dev/null || echo "?")
        log_info "  $u: $local_count comandi"
    done <<< "$sudo_users"
fi

# ─── SEZIONE 4: ANOMALIE E SICUREZZA ────────────────────────────────────────

section "Anomalie (ultimi $DAYS giorni)"

# Login da IP inusuali
public_ip_logins=$(journalctl -u ssh -u sshd --since "$SINCE" 2>/dev/null | \
    grep "Accepted" | \
    grep -vE "from (10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|127\.)" | \
    wc -l || echo 0)
if [[ "$public_ip_logins" -gt 0 ]]; then
    log_warn "Login SSH da IP pubblici (non RFC1918): $public_ip_logins — verificare se attesi (VPN gap?)"
else
    log_ok "Nessun login SSH da IP pubblici"
fi

# Modifiche recenti a /etc/passwd, /etc/shadow, /etc/sudoers
for sensitive_file in /etc/passwd /etc/shadow /etc/sudoers; do
    if [[ -f "$sensitive_file" ]]; then
        mtime=$(stat -c %Y "$sensitive_file" 2>/dev/null)
        days_since=$(( ($(date +%s) - mtime) / 86400 ))
        if [[ "$days_since" -lt "$DAYS" ]]; then
            log_warn "$sensitive_file modificato $days_since giorni fa — verificare se modifica autorizzata"
        fi
    fi
done

# ─── REPORT FINALE ───────────────────────────────────────────────────────────

if [[ "$JSON_OUTPUT" == true ]]; then
    local findings_json
    findings_json=$(printf '"%s",' "${FINDINGS[@]:-}" 2>/dev/null | sed 's/,$//')
    cat <<EOF
{
  "timestamp": "$REPORT_DATE",
  "host": "$(hostname)",
  "period_days": $DAYS,
  "status_code": $STATUS,
  "ssh_success": $ssh_success,
  "ssh_failed": $ssh_failed,
  "sudo_commands": $sudo_total,
  "findings_count": ${#FINDINGS[@]},
  "findings": [${findings_json:-}]
}
EOF
else
    printf '\n\e[36m═══ RIEPILOGO AUDIT ACCESSI (%s) ═══\e[0m\n' "$REPORT_DATE"
    local status_color
    case $STATUS in
        0) status_color='\e[32m'; status_text="VERDE — Nessuna anomalia" ;;
        1) status_color='\e[33m'; status_text="GIALLO — Warning presenti" ;;
        2) status_color='\e[31m'; status_text="ROSSO — Criticità rilevate" ;;
    esac
    printf "Stato: ${status_color}%s\e[0m\n" "$status_text"
    if [[ ${#FINDINGS[@]} -gt 0 ]]; then
        printf "Findings:\n"
        for f in "${FINDINGS[@]}"; do printf "  → %s\n" "$f"; done
    fi
fi

exit $STATUS
```

**Uso:**
```bash
# Installa
sudo install -m 750 -o root -g adm linux_auth_audit.sh /usr/local/sbin/

# Esecuzione manuale (ultimi 30 giorni)
sudo /usr/local/sbin/linux_auth_audit.sh

# Output JSON per integrazione monitoring
sudo /usr/local/sbin/linux_auth_audit.sh --json

# Ultima settimana
sudo /usr/local/sbin/linux_auth_audit.sh --days 7

# Pianifica settimanalmente
echo "0 8 * * 1 root /usr/local/sbin/linux_auth_audit.sh --json >> /var/log/auth_audit.log" | \
    sudo tee /etc/cron.d/linux-auth-audit
```

---

### Integrazione ITIL

**Pratica ITIL: Identity and Access Management (inclusa in Information Security Management)**

```
IDENTITÀ COME ASSET:
  Le identità digitali sono asset IT come i server e i certificati.
  Devono essere inventariate, monitorate, e rimosse quando non servono.
  
  Processo ITIL correlato: Asset and Configuration Management
  → Ogni account è un Configuration Item (CI) nel CMDB
  → Attributi: proprietario, ruolo, data creazione, data ultima verifica
  → Relazioni: CI "mario.rossi" → CI "DC-LAB-01" (accesso), CI "File-Server-01"

CHANGE MANAGEMENT PER GLI ACCESSI:
  Ogni modifica a permessi = Change Request
  
  Standard Change (approvazione pre-autorizzata):
    → Onboarding nuovo dipendente in ruolo standard
    → Rinnovo password scaduta
    → Sblocco account
    
  Normal Change (approvazione del Change Manager):
    → Aggiunta utente a gruppo privilegiato
    → Creazione nuovo service account
    → Estensione di accesso temporaneo
    
  Emergency Change:
    → Disabilitazione immediata account compromesso
    → Rotazione password di emergenza dopo breach

INCIDENT MANAGEMENT PER ACCESSI:
  Incidenti tipo:
  - "Account ex-dipendente ancora attivo" → P2 (risoluzione 2 ore)
  - "Credential stuffing rilevato" → P1 (isolamento immediato)
  - "Utente bloccato non riesce a lavorare" → P3 (sblocco entro 4h)

CERTIFICAZIONE ACCESSI E AUDIT:
  La revisione trimestrale (SOP-ACCESS-001) produce evidenze per:
  - ISO 27001 (A.5.18: Access rights, A.5.15: Access control)
  - GDPR (accountability, controllo accessi ai dati personali)
  - NIS2 (Articolo 21: misure tecniche sicurezza, gestione accessi)
  - PCI DSS (Req. 8: identify users, authenticate access)
  
  Conservazione evidenze: 24 mesi (GDPR requirement)
```

---

## Checklist di Validazione Lab

### Part A — Concetti
- [ ] Sai descrivere il ciclo di vita dell'identità (onboarding → uso → offboarding)
- [ ] Sai spiegare la differenza tra assegnazione diretta e RBAC (con esempio)
- [ ] Sai elencare 3 rischi degli accessi privilegiati non gestiti con PAM
- [ ] Sai citare 5 Event ID Windows critici per la sicurezza (con il loro significato)
- [ ] Sai spiegare cosa richiede il GDPR in termini di accessi e log (almeno 3 obblighi)

### Part B — Operazioni
- [ ] B1: Audit AD completato, stale accounts identificati, gruppi privilegiati verificati
- [ ] B2: Event Log interrogato (4625, 4672, 4720), nessun 1102 sospetto
- [ ] B3: Auth log Linux analizzato, nessun login root SSH, sudo audit completato
- [ ] B4: Struttura RBAC creata in AD (OU, gruppi ruolo, utenti demo)
- [ ] B5: Certificati verificati con openssl, funzione check_cert_expiry testata
- [ ] B6: Offboarding mario.rossi completato (account disabilitato, password cambiata, gruppi revocati)

### Part C — Sistematizzazione
- [ ] SOP-ACCESS-001 compresa (4 fasi: prep → revisione → implementazione → doc)
- [ ] `ad_access_audit.ps1` eseguito su DC-LAB-01, report CSV generati
- [ ] `linux_auth_audit.sh` installato e testato su SRV-LINUX-01
- [ ] Connessione ITIL stabilita: quale pratica ITIL gestisce le identità?

---

## Appendice A: Event ID Windows — Riferimento Rapido

```powershell
# Query rapide per investigazione (PowerShell)

# Tutti i login falliti (ultime 4 ore)
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625; StartTime=(Get-Date).AddHours(-4)}

# Chi ha resettato una password specifica?
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4724} |
    Where-Object {$_.Message -match "mario.rossi"}

# Quando è stato aggiunto qualcuno a Domain Admins?
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4728} |
    Where-Object {$_.Message -match "Domain Admins"}

# Il security log è stato cancellato?
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=1102}

# Tutti gli account creati nell'ultima settimana
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4720; StartTime=(Get-Date).AddDays(-7)}

# Login da workstation specifica
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4624} |
    Where-Object {$_.Message -match "WKS-LAB-01"}
```

---

## Appendice B: Tabella Compliance — Chi Richiede Cosa

| Requisito | ISO 27001 | GDPR | NIS2 | PCI DSS |
|-----------|-----------|------|------|---------|
| IAM / Gestione accessi | A.5.15 | Art. 32 | Art. 21 | Req. 8 |
| Logging e audit | A.8.15 | Art. 32 | Art. 21 | Req. 10 |
| Revisione periodica accessi | A.5.18 | Art. 32 | Art. 21 | Req. 8 |
| MFA per accessi privilegiati | A.8.5 | Art. 32 | Art. 21 | Req. 8 |
| Offboarding tempestivo | A.5.18 | Art. 5 | Art. 21 | Req. 8 |
| Retention log sicurezza | A.8.15 | Art. 5 | Art. 21 | Req. 10 (12 mesi) |
| Password policy | A.8.5 | Art. 32 | Art. 21 | Req. 8 |
| Certificati TLS | A.8.24 | Art. 32 | Art. 21 | Req. 4 |

---

## Appendice C: Matrice SLA Offboarding per Tipo di Uscita

```
Tipo di uscita           Timing disabilitazione        Note
─────────────────────────────────────────────────────────────────────
Licenziamento            Immediato (prima del          Coordinare con HR
                         colloquio di uscita)          Accesso fisico: revoca contestuale

Dimissioni volontarie    Fine dell'ultimo giorno       Possibile trasferimento conoscenze
                         lavorativo                    Reindirizzamento email: 30-90 giorni

Fine contratto           Fine del contratto            Stessa procedura dimissioni

Pensionamento            Fine dell'ultimo giorno       Archivio dati più lungo (memoria storica)

Trasferimento interno    Cambio stesso giorno          Revoca vecchi accessi + assegna nuovi
                         del trasferimento              contestualmente (nessun gap, nessun overlap)

Congedo (maternità,     Sospendere accessi             Riattivare al rientro con verifica
aspettativa)             (non disabilitare)            permanenza ruolo
```

---

## Riferimenti

- NIST SP 800-207 — Zero Trust Architecture (principi IAM moderni)
- CIS Control 5 — Account Management (controllo 5 della CIS Critical Security Controls)
- Microsoft Identity Architecture — best practice AD, MFA, Conditional Access
- OWASP Cheat Sheet: Authentication (regole di autenticazione sicura)
- GDPR Art. 5, 25, 32 — principi, privacy by design, misure tecniche
- ISO/IEC 27001:2022 — Annex A controls per Information Security Management
- Regolamento eIDAS (EU) 910/2014 — identità digitale in EU
