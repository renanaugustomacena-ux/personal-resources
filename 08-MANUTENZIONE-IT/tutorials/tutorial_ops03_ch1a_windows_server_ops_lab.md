# Tutorial: Gestione Windows Server — Operazioni Quotidiane e Avanzate — Hands-On Lab

> **Documento di riferimento:** `03-gestione-sistemi-operativi.md` (sezione Windows Server)
> **Dominio:** Gestione Sistemi Operativi
> **Ambito:** Windows Server 2022: patch management, Active Directory health, Group Policy, Event Log, performance monitoring
> **Durata lab:** 4-5 ore
> **Livello:** Intermedio — richiede lab ops00 configurato e nozioni ITIL (ops01a)
> **Prerequisiti:** `tutorial_ops00` (lab con DC-LAB-01 Windows Server 2022)
> **Ambiente:** Principalmente DC-LAB-01 (Windows Server 2022) + WKS-LAB-01 per Remote Desktop

---

## Lab Environment Setup

```powershell
# Verifica rapida da WKS-LAB-01
.\lab_healthcheck.ps1
# DC-LAB-01 deve rispondere su porta 3389 (RDP)
```

**Connessione RDP a DC-LAB-01 da WKS-LAB-01:**

Start → `mstsc.exe` → Computer: `192.168.56.10` → Connect
- Username: `Administrator`
- Password: `Lab@2024!`

Puoi anche aprire PowerShell remoto:
```powershell
# Da WKS-LAB-01
Enter-PSSession -ComputerName 192.168.56.10 -Credential "DC-LAB-01\Administrator"
```

---

## PART A: FONDAMENTI — Windows Server come Piattaforma Enterprise

> Windows Server non è "Windows con più RAM". È un sistema operativo progettato per erogare servizi a centinaia o migliaia di utenti simultaneamente, con caratteristiche di affidabilità, sicurezza e gestibilità che il Windows client non ha. Questa sezione costruisce il modello mentale necessario per gestirlo professionalmente.

---

### Concetto A1: Windows Server vs Windows Client — Le Differenze Fondamentali

> **Analogia.** Un'autovettura e un autobus hanno entrambi quattro ruote, un motore e dei sedili. Ma sono progettati per scopi radicalmente diversi: l'autovettura per il comfort e l'autonomia del singolo; l'autobus per la capacità, l'affidabilità e la servitù pubblica. Windows 10/11 è l'autovettura; Windows Server è l'autobus.

| Caratteristica | Windows 10/11 (Client) | Windows Server 2022 |
|---|---|---|
| **Utenti simultanei** | 1 interattivo | Centinaia via RDP, migliaia via servizi |
| **Aggiornamenti** | Gestiti dall'utente | Gestiti centralmente via WSUS/SCCM |
| **Riavvii** | Frequenti, accettati | Minimizzati (devono essere pianificati) |
| **Interfaccia** | Desktop Experience (default) | Server Core (default su nuove istall.) |
| **Ruoli disponibili** | No | AD DS, DNS, DHCP, File Server, IIS, Hyper-V |
| **Licenza** | Per utente/dispositivo | Per core (2-core pack) + CAL |
| **Ciclo di vita** | 10 anni | 10 anni (LTSC) / 3 anni (SAC) |
| **Memoria max** | 2 TB | 48 TB (Datacenter) |

**Windows Server Editions nel lab:**

Nel tutorial ops00 hai installato **Windows Server 2022 Standard Evaluation**. In produzione esistono 3 edizioni:

- **Essentials**: fino a 25 utenti / 50 dispositivi — per micro-aziende
- **Standard**: numero illimitato di utenti, 2 VM incluse per licenza
- **Datacenter**: VM illimitate, Hyper-V enhanced, Azure Stack HCI

**Ruoli vs Feature — La distinzione fondamentale:**

In Windows Server, le funzionalità si dividono in:
- **Roles (Ruoli)**: servizi principali che il server eroga (AD DS, DNS, Web Server, File Server)
- **Role Services**: sotto-componenti di un ruolo (es. Active Directory Certificate Services → CA, NDES, OCSP)
- **Features**: funzionalità di supporto che non sono servizi erogati direttamente (PowerShell, .NET Framework, RSAT)

```powershell
# Vedi i ruoli installati
Get-WindowsFeature | Where-Object {$_.InstallState -eq "Installed" -and $_.FeatureType -eq "Role"}

# Vedi tutti i ruoli disponibili (non ancora installati)
Get-WindowsFeature | Where-Object {$_.InstallState -ne "Installed" -and $_.FeatureType -eq "Role"} |
    Select-Object Name, DisplayName
```

---

### Concetto A2: Active Directory — Il Cuore del Windows Enterprise

> **Analogia.** Active Directory è come l'anagrafe + la polizia + la banca chiavi di un'azienda. L'anagrafe perché sa chi esiste (utenti, computer, gruppi). La polizia perché gestisce chi può accedere a cosa (permessi, policy). La banca chiavi perché custodisce e valida le credenziali di autenticazione (Kerberos). Se AD va down, l'azienda si ferma: nessuno riesce a fare login, i file server diventano inaccessibili, le applicazioni non riescono ad autenticare gli utenti.

**La struttura di Active Directory:**

```
FOREST (la struttura più grande)
  └── DOMAIN (lab.local — il dominio del lab)
        ├── Domain Controllers (server che gestiscono il dominio)
        │     └── DC-LAB-01 (il nostro DC)
        ├── Organizational Units (OU)
        │     ├── Users (utenti aziendali)
        │     ├── Computers (workstation e server)
        │     └── Groups (gruppi di sicurezza)
        └── Sites (siti fisici — per ambienti multi-sede)
```

**I 5 FSMO Roles — i ruoli speciali del Domain Controller:**

AD ha 5 ruoli speciali (Flexible Single Master Operation) che devono risiedere su un singolo DC per evitare conflitti:

| Ruolo FSMO | Funzione | Forest o Domain? |
|---|---|---|
| Schema Master | Gestisce le modifiche allo schema AD | Forest |
| Domain Naming Master | Aggiunge/rimuove domini dalla forest | Forest |
| PDC Emulator | Sync orario, lockout, compatibilità NT | Domain |
| RID Master | Distribuisce pool di SID | Domain |
| Infrastructure Master | Aggiorna riferimenti cross-domain | Domain |

In un lab con un solo DC, tutti e 5 i ruoli sono su DC-LAB-01.

```powershell
# Verifica dove sono i FSMO roles
netdom query fsmo
```

**I componenti critici da monitorare:**

1. **Replica AD**: se hai più DC, i cambiamenti (nuovi utenti, password reset) devono replicarsi tra tutti. Errori di replica = inconsistenze
2. **SYSVOL**: cartella condivisa che contiene Group Policy files. Deve replicarsi via DFSR
3. **DNS**: AD dipende completamente dal DNS. Se DNS è rotto, AD non funziona
4. **Kerberos**: protocollo di autenticazione AD. Il PDC Emulator è il master per l'orario — se l'orario è sfasato di più di 5 minuti tra DC e client, Kerberos fallisce

---

### Concetto A3: Group Policy — La Configurazione Centralizzata

> **Analogia.** Immagina di dover installare la stessa policy aziendale (sfondo del desktop, timeout password, disabilitazione USB) su 500 PC. Potresti farlo uno per uno — ci vorresti settimane. Oppure scrivi la policy una volta su un foglio (Group Policy Object) e la pubblichi sulla bacheca aziendale (AD): ogni PC la legge automaticamente al login e la applica. Questo è Group Policy.

**Come funziona la Group Policy:**

```
Amministratore IT crea GPO → GPO viene linkato a OU → DC distribuisce GPO ai membri dell'OU
     ↓                              ↓                              ↓
Crea regola                  "Questa policy vale per           Computer nella OU
"Block USB"                  tutti i PC in OU Computers"       applicano la policy
                                                                al riavvio/login
```

**GPO processing order — LSDOU:**

Le policy vengono applicate in quest'ordine (l'ultima vince sui conflitti):

```
1. Local Policy (impostazioni locali del PC)
2. Site (policy del sito AD)
3. Domain (policy del dominio)
4. OU (policy dell'Organizational Unit)
   └── Parent OU first, then child OU
```

**GPO inheritance — cosa succede con policy conflittuali:**

Se una GPO dice "password minima: 8 caratteri" e un'altra dice "password minima: 12 caratteri", vince quella più vicina all'oggetto (child OU batte parent OU). Si può usare `Enforced` (override di tutta la gerarchia) o `Block Inheritance` (ignora le policy dei livelli superiori).

---

### Concetto A4: Windows Event Log — Decodificare i Messaggi del Server

> **Analogia.** Ogni aereo registra i parametri di volo sulla scatola nera. Windows fa lo stesso: ogni evento significativo — login riuscito, login fallito, avvio servizio, crash applicazione, modifica permessi — viene registrato nell'Event Log con timestamp, ID numerico, sorgente e descrizione. Saper leggere l'Event Log è come saper decodificare la scatola nera.

**I log principali:**

| Log | Path | Cosa contiene |
|---|---|---|
| System | `%SystemRoot%\System32\winevt\Logs\System.evtx` | Kernel, driver, hardware, servizi di sistema |
| Application | `...\Application.evtx` | Applicazioni, .NET, database, software installato |
| Security | `...\Security.evtx` | Autenticazioni, audit, permessi, account changes |
| Setup | `...\Setup.evtx` | Installazioni software, patch |
| Forwarded Events | `...\ForwardedEvents.evtx` | Eventi ricevuti da altri server (WEF) |

**Event IDs critici da conoscere:**

| Event ID | Log | Significato | Criticità |
|---|---|---|---|
| 4624 | Security | Login riuscito | Info (utile per audit) |
| 4625 | Security | Login fallito | ⚠ 5+ consecutivi = bruteforce |
| 4720 | Security | Account utente creato | ⚠ Chi l'ha creato? Autorizzato? |
| 4728 | Security | Aggiunto a gruppo privilegiato | ⚠ monitorare Domain Admins |
| 4740 | Security | Account bloccato (lockout) | ⚠ Utente bloccato |
| 4771 | Security | Kerberos pre-auth fallita | ⚠ Password sbagliata |
| 6008 | System | Windows si è spento inaspettatamente | ⚠ Power failure o crash |
| 7045 | System | Nuovo servizio installato | ⚠ Possibile malware |
| 4099 | System | NTP sync failure | ⚠ Orario Kerberos a rischio |
| 1000 | Application | Application crash | ⚠ Applicazione instabile |
| 41 | System | Kernel-Power: riavvio inaspettato | ⚠ Crash di sistema |

---

### Concetto A5: Windows Server Performance Monitoring

> **Analogia.** Un pilota di aereo non guarda solo "l'aereo vola?". Guarda decine di indicatori: velocità, quota, carburante, temperatura motori, pressione cabin, autopilot status. Ogni indicatore da solo non basta; insieme danno un quadro completo dello stato del volo. Il monitoring di Windows Server funziona così: non basta sapere che "il server risponde" — devi sapere come risponde.

**I 4 indicatori fondamentali:**

**1. CPU Utilization**
- Normale: picchi fino a 80-90% per lavoro pesante temporaneo
- Problema: > 80% sostenuto per più di 15 minuti — identifica quale processo
- Critico: > 90% per più di 5 minuti — potenziale problema in arrivando

**2. Memory (RAM) Usage**
- Normale: alto utilizzo RAM non è necessariamente un problema (Windows usa RAM libera per cache)
- Problema: `Available MB` < 200 MB (paginazione al disco: swap = performance crolla)
- Indicatore chiave: `Page Faults/sec` > 20 = sistema sta swappando troppo

**3. Disk I/O**
- Indicatore critico: `Avg Disk Queue Length` > 2 = disco saturo (collo di bottiglia)
- `Avg Disk sec/Transfer` > 20ms = disco lento (HDD meccanico: normale fino a 10ms)
- Soluzione: upgrade a SSD, distribuzione carico, cache più aggressiva

**4. Network**
- `Bytes Total/sec` confrontato con la velocità dell'interfaccia
- `Output Queue Length` > 2 = saturazione uscita rete

```powershell
# Snapshot performance in un comando
Get-Counter @(
    "\Processor(_Total)\% Processor Time",
    "\Memory\Available MBytes",
    "\Memory\Page Faults/sec",
    "\PhysicalDisk(_Total)\Avg. Disk Queue Length",
    "\Network Interface(*)\Bytes Total/sec"
) | Select-Object -ExpandProperty CounterSamples | 
    Select-Object Path, @{N="Value"; E={[math]::Round($_.CookedValue, 2)}}
```

---

## PART B: OPERAZIONI — Amministrare Windows Server 2022 (DC-LAB-01)

> Tutti gli esercizi seguenti si eseguono su DC-LAB-01. Connettiti via RDP da WKS-LAB-01 oppure apri PowerShell direttamente sulla VM.

---

### Esercizio B1: Installare i Ruoli AD DS e DNS su DC-LAB-01

**Obiettivo.** Promuovere DC-LAB-01 a Domain Controller installando Active Directory Domain Services, configurare il dominio `lab.local`, e verificare il corretto funzionamento.

> Se hai già completato questo step in un tutorial precedente, salta a B2.

**Step 1 — Installa il ruolo AD DS**

Su DC-LAB-01, PowerShell come Administrator:

```powershell
# Installa Active Directory Domain Services e strumenti di gestione
Install-WindowsFeature -Name AD-Domain-Services `
    -IncludeManagementTools `
    -IncludeAllSubFeature

# Verifica installazione
Get-WindowsFeature | Where-Object {$_.Name -eq "AD-Domain-Services"} | 
    Select-Object Name, InstallState
```

Output atteso:
```
Name              InstallState
----              ------------
AD-Domain-Services    Installed
```

**Step 2 — Promuovi a Domain Controller (crea il dominio lab.local)**

```powershell
# Importa il modulo ADDSDeployment
Import-Module ADDSDeployment

# Crea una nuova forest con dominio lab.local
Install-ADDSForest `
    -DomainName "lab.local" `
    -DomainNetBiosName "LAB" `
    -ForestMode "WinThreshold" `
    -DomainMode "WinThreshold" `
    -SafeModeAdministratorPassword (ConvertTo-SecureString "Lab@2024!" -AsPlainText -Force) `
    -InstallDns `
    -Force
```

Il server si riavvia automaticamente. Dopo il riavvio, esegui il login come `LAB\Administrator` (nota il prefisso `LAB\`).

**Step 3 — Verifica il Domain Controller**

```powershell
# Verifica ruoli FSMO
netdom query fsmo

# Verifica che AD DS funzioni
Get-ADDomain | Select-Object DNSRoot, NetBIOSName, DomainMode, PDCEmulator

# Verifica DNS integrato con AD
Get-DnsServerZone | Select-Object ZoneName, ZoneType, IsReverseLookupZone
```

Output atteso di `netdom query fsmo`:
```
Schema master               DC-LAB-01.lab.local
Domain naming master        DC-LAB-01.lab.local
PDC                         DC-LAB-01.lab.local
RID pool manager            DC-LAB-01.lab.local
Infrastructure master       DC-LAB-01.lab.local
The command completed successfully.
```

**Checkpoint B1:**
- [ ] Ruolo AD DS installato con stato `Installed`
- [ ] Dominio `lab.local` creato, NetBIOS name `LAB`
- [ ] Login con `LAB\Administrator` / `Lab@2024!` funzionante
- [ ] `netdom query fsmo` mostra DC-LAB-01 per tutti i 5 ruoli

---

### Esercizio B2: Creare Struttura Organizzativa (OU, Utenti, Gruppi)

**Obiettivo.** Creare la struttura AD di un'azienda reale: Organizational Units per dipartimento, utenti, gruppi di sicurezza.

```powershell
# Crea la struttura OU aziendale
$domain = "DC=lab,DC=local"

$ous = @(
    "OU=Lab-Corp,$domain",
    "OU=Users,OU=Lab-Corp,$domain",
    "OU=Computers,OU=Lab-Corp,$domain",
    "OU=Groups,OU=Lab-Corp,$domain",
    "OU=Service-Accounts,OU=Lab-Corp,$domain",
    "OU=IT-Team,OU=Users,OU=Lab-Corp,$domain",
    "OU=Finance,OU=Users,OU=Lab-Corp,$domain",
    "OU=HR,OU=Users,OU=Lab-Corp,$domain"
)

foreach ($ou in $ous) {
    $name = ($ou -split ",")[0] -replace "OU=",""
    $path = ($ou -split ",",2)[1]
    try {
        New-ADOrganizationalUnit -Name $name -Path $path -ErrorAction Stop
        Write-Host "[ OK] OU creata: $ou" -ForegroundColor Green
    } catch {
        Write-Host "[SKIP] OU già esistente: $name" -ForegroundColor Yellow
    }
}

# Crea utenti di test
$users = @(
    @{ Name = "Mario Rossi";    SamAccount = "mario.rossi";    Department = "IT";      OU = "OU=IT-Team" },
    @{ Name = "Anna Bianchi";   SamAccount = "anna.bianchi";   Department = "Finance"; OU = "OU=Finance" },
    @{ Name = "Luca Ferrari";   SamAccount = "luca.ferrari";   Department = "HR";      OU = "OU=HR" }
)

$securePass = ConvertTo-SecureString "Lab@2024!" -AsPlainText -Force

foreach ($u in $users) {
    $parts = $u.Name -split " "
    try {
        New-ADUser `
            -Name $u.Name `
            -GivenName $parts[0] `
            -Surname $parts[1] `
            -SamAccountName $u.SamAccount `
            -UserPrincipalName "$($u.SamAccount)@lab.local" `
            -Path "$($u.OU),OU=Users,OU=Lab-Corp,DC=lab,DC=local" `
            -AccountPassword $securePass `
            -Department $u.Department `
            -Enabled $true `
            -PasswordNeverExpires $true `
            -ErrorAction Stop
        Write-Host "[ OK] Utente creato: $($u.Name)" -ForegroundColor Green
    } catch {
        Write-Host "[SKIP] Utente già esistente: $($u.Name)" -ForegroundColor Yellow
    }
}

# Crea gruppi di sicurezza
$groups = @(
    @{ Name = "GRP-IT-Admins";   Description = "Amministratori IT" },
    @{ Name = "GRP-Finance";     Description = "Accesso area finanziaria" },
    @{ Name = "GRP-HR";          Description = "Accesso HR" }
)

foreach ($g in $groups) {
    try {
        New-ADGroup `
            -Name $g.Name `
            -SamAccountName $g.Name `
            -GroupScope Global `
            -GroupCategory Security `
            -Path "OU=Groups,OU=Lab-Corp,DC=lab,DC=local" `
            -Description $g.Description `
            -ErrorAction Stop
        Write-Host "[ OK] Gruppo creato: $($g.Name)" -ForegroundColor Green
    } catch {
        Write-Host "[SKIP] Gruppo già esistente: $($g.Name)" -ForegroundColor Yellow
    }
}

# Aggiungi utenti ai gruppi appropriati
Add-ADGroupMember -Identity "GRP-IT-Admins" -Members "mario.rossi" -ErrorAction SilentlyContinue
Add-ADGroupMember -Identity "GRP-Finance"   -Members "anna.bianchi" -ErrorAction SilentlyContinue
Add-ADGroupMember -Identity "GRP-HR"        -Members "luca.ferrari" -ErrorAction SilentlyContinue

Write-Host "`nStruttura AD creata. Verifica:" -ForegroundColor Cyan
Get-ADUser -Filter * -SearchBase "OU=Lab-Corp,DC=lab,DC=local" | 
    Select-Object Name, SamAccountName, Enabled
```

**Checkpoint B2:**
- [ ] OU Lab-Corp con sotto-OU (Users, Computers, Groups, ecc.) create
- [ ] 3 utenti (mario.rossi, anna.bianchi, luca.ferrari) creati e abilitati
- [ ] 3 gruppi (GRP-IT-Admins, GRP-Finance, GRP-HR) creati
- [ ] Utenti assegnati ai gruppi corretti

---

### Esercizio B3: Health Check Completo di Active Directory

**Obiettivo.** Eseguire una verifica completa della salute di Active Directory — l'attività settimanale più importante per un Windows Server Administrator.

```powershell
# === HEALTH CHECK ACTIVE DIRECTORY ===
# Esegui su DC-LAB-01 come LAB\Administrator

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
Write-Host "`n=== AD HEALTH CHECK $timestamp ===" -ForegroundColor Cyan

# --- 1. DCDiag: diagnostica completa DC ---
Write-Host "`n[1] Esecuzione DCDiag..." -ForegroundColor Yellow
dcdiag /test:advertising /test:fsmocheck /test:replications /q 2>&1 | 
    Where-Object { $_ -match "(passed|failed|warning)" } |
    ForEach-Object {
        if ($_ -match "passed") { Write-Host "  $_" -ForegroundColor Green }
        elseif ($_ -match "failed") { Write-Host "  $_" -ForegroundColor Red }
        else { Write-Host "  $_" -ForegroundColor Yellow }
    }

# --- 2. Replica AD (importante solo con DC multipli) ---
Write-Host "`n[2] Stato Replica AD..." -ForegroundColor Yellow
repadmin /replsummary 2>&1 | Select-Object -First 20

# --- 3. SYSVOL integrità ---
Write-Host "`n[3] SYSVOL Share Status..." -ForegroundColor Yellow
$sysvolPath = "\\DC-LAB-01\SYSVOL"
if (Test-Path $sysvolPath) {
    Write-Host "  [ OK] SYSVOL share accessibile" -ForegroundColor Green
    $policiesCount = (Get-ChildItem "$sysvolPath\lab.local\Policies" -ErrorAction SilentlyContinue).Count
    Write-Host "  [ OK] $policiesCount Group Policy Objects in SYSVOL" -ForegroundColor Green
} else {
    Write-Host "  [ERR] SYSVOL share non accessibile!" -ForegroundColor Red
}

# --- 4. Kerberos / Time sync ---
Write-Host "`n[4] Orario NTP (critico per Kerberos)..." -ForegroundColor Yellow
$w32tm = w32tm /query /status 2>&1
$w32tm | Select-Object -First 8 | ForEach-Object { Write-Host "  $_" }

# --- 5. Account lockout / Logon failures (ultime 24h) ---
Write-Host "`n[5] Security Events (ultime 24h)..." -ForegroundColor Yellow
$since = (Get-Date).AddHours(-24)

$lockouts = Get-WinEvent -FilterHashtable @{
    LogName='Security'; Id=4740; StartTime=$since
} -ErrorAction SilentlyContinue

$failedLogins = Get-WinEvent -FilterHashtable @{
    LogName='Security'; Id=4625; StartTime=$since
} -ErrorAction SilentlyContinue

Write-Host "  Account lockout (4740): $($lockouts.Count)" -ForegroundColor $(if ($lockouts.Count -gt 0) { 'Yellow' } else { 'Green' })
Write-Host "  Login falliti (4625): $($failedLogins.Count)" -ForegroundColor $(if ($failedLogins.Count -gt 10) { 'Red' } elseif ($failedLogins.Count -gt 3) { 'Yellow' } else { 'Green' })

# --- 6. Account inattivi (>90 giorni) ---
Write-Host "`n[6] Account Inattivi (>90 giorni)..." -ForegroundColor Yellow
$inactiveUsers = Search-ADAccount -AccountInactive -TimeSpan (New-TimeSpan -Days 90) `
    -UsersOnly -SearchBase "OU=Lab-Corp,DC=lab,DC=local" -ErrorAction SilentlyContinue

if ($null -ne $inactiveUsers -and $inactiveUsers.Count -gt 0) {
    Write-Host "  [WARN] $($inactiveUsers.Count) account inattivi:" -ForegroundColor Yellow
    $inactiveUsers | Select-Object Name, LastLogonDate | Format-Table -AutoSize
} else {
    Write-Host "  [ OK] Nessun account inattivo (o nessun utente ha mai effettuato login)" -ForegroundColor Green
}

Write-Host "`n=== FINE AD HEALTH CHECK ===" -ForegroundColor Cyan
```

**Checkpoint B3:**
- [ ] DCDiag non mostra errori sui test Advertising, FsmoCheck
- [ ] SYSVOL share accessibile
- [ ] W32TM mostra sincronizzazione NTP attiva
- [ ] Nessun lockout account inaspettato nelle ultime 24h

---

### Esercizio B4: Group Policy — Creare e Applicare una Policy di Sicurezza

**Obiettivo.** Creare una Group Policy Object che applichi impostazioni di sicurezza standard alle workstation del laboratorio.

```powershell
# Installa GPMC (Group Policy Management Console) se non presente
Install-WindowsFeature -Name GPMC

# Crea la GPO di sicurezza base
$gpoName = "LAB-Security-Baseline"
$domain   = "lab.local"
$ouTarget = "OU=Computers,OU=Lab-Corp,DC=lab,DC=local"

$gpo = New-GPO -Name $gpoName -Domain $domain -Comment "Policy sicurezza base lab"
Write-Host "GPO creata: $($gpo.DisplayName) [ID: $($gpo.Id)]"

# Applica alcune impostazioni di sicurezza tramite registry-based policy
# (in ambiente reale si usano Security Templates o la console GPMC grafica)

# Imposta timeout screen saver 15 minuti
Set-GPRegistryValue -Name $gpoName -Domain $domain `
    -Key "HKCU\Control Panel\Desktop" `
    -ValueName "ScreenSaveTimeOut" `
    -Type String `
    -Value "900"

# Imposta screen saver abilitato
Set-GPRegistryValue -Name $gpoName -Domain $domain `
    -Key "HKCU\Control Panel\Desktop" `
    -ValueName "ScreenSaveActive" `
    -Type String `
    -Value "1"

# Imposta screen saver protetto da password
Set-GPRegistryValue -Name $gpoName -Domain $domain `
    -Key "HKCU\Control Panel\Desktop" `
    -ValueName "ScreenSaverIsSecure" `
    -Type String `
    -Value "1"

# Collega la GPO all'OU Computers
$link = New-GPLink -Name $gpoName -Target $ouTarget -LinkEnabled Yes
Write-Host "GPO collegata a: $ouTarget"

# Verifica il link
Get-GPInheritance -Target $ouTarget | Select-Object -ExpandProperty GpoLinks
```

**Verifica la GPO con gpresult:**

```powershell
# Verifica GPO risultanti (su WKS-LAB-01 dopo aver unito il dominio)
# Prima di unire WKS-LAB-01 al dominio, usa il computer locale:
gpresult /scope user /v
gpresult /scope computer /v
```

**Checkpoint B4:**
- [ ] GPO `LAB-Security-Baseline` creata
- [ ] Impostazioni screen saver applicate
- [ ] GPO collegata all'OU Computers
- [ ] `Get-GPInheritance` mostra la GPO nell'OU target

---

### Esercizio B5: Analisi Event Log — Investigare un Problema Simulato

**Obiettivo.** Praticare l'analisi dell'Event Log per investigare un problema simulato: accesso non autorizzato tentato sull'account Administrator.

**Simula il problema — Tentativi di login falliti:**

Da WKS-LAB-01, apri PowerShell e tenta deliberatamente login sbagliati:

```powershell
# Simula 5 tentativi di login falliti (password sbagliata)
for ($i = 1; $i -le 5; $i++) {
    try {
        $cred = New-Object System.Management.Automation.PSCredential(
            "LAB\mario.rossi",
            (ConvertTo-SecureString "WrongPassword$i!" -AsPlainText -Force)
        )
        Invoke-Command -ComputerName 192.168.56.10 -Credential $cred -ScriptBlock { "test" } -ErrorAction Stop
    } catch {}
    Start-Sleep -Seconds 1
}
Write-Host "Simulazione login falliti completata"
```

**Ora analizza l'Event Log su DC-LAB-01:**

```powershell
# Su DC-LAB-01: cerca i login falliti generati dalla simulazione
$since = (Get-Date).AddMinutes(-10)

$failedLogins = Get-WinEvent -FilterHashtable @{
    LogName  = 'Security'
    Id       = 4625          # Login fallito
    StartTime = $since
} -ErrorAction SilentlyContinue

Write-Host "Login falliti negli ultimi 10 minuti: $($failedLogins.Count)"

foreach ($evt in $failedLogins | Select-Object -First 5) {
    $xml = [xml]$evt.ToXml()
    $data = $xml.Event.EventData.Data
    
    $targetUser = ($data | Where-Object {$_.Name -eq "TargetUserName"})."#text"
    $sourceIP   = ($data | Where-Object {$_.Name -eq "IpAddress"})."#text"
    $failReason = ($data | Where-Object {$_.Name -eq "SubStatus"})."#text"
    
    Write-Host ""
    Write-Host "  Ora: $($evt.TimeCreated)"
    Write-Host "  Utente: $targetUser"
    Write-Host "  Da IP: $sourceIP"
    Write-Host "  Causa: $failReason"
}

# Cerca lockout dell'account
$lockouts = Get-WinEvent -FilterHashtable @{
    LogName = 'Security'; Id = 4740; StartTime = $since
} -ErrorAction SilentlyContinue

Write-Host "`nAccount bloccati: $($lockouts.Count)"
if ($lockouts.Count -gt 0) {
    foreach ($lock in $lockouts) {
        $xml = [xml]$lock.ToXml()
        $lockedUser = ($xml.Event.EventData.Data | Where-Object {$_.Name -eq "TargetUserName"})."#text"
        Write-Host "  Account bloccato: $lockedUser alle $($lock.TimeCreated)"
    }
}
```

**Interpreta e documenta i risultati in GLPI:**

Apri GLPI → Helpdesk → Tickets → Add:
- Tipo: Incident
- Categoria: Sicurezza → Tentativi Accesso Non Autorizzato
- Titolo: "Rilevati 5 tentativi login falliti per mario.rossi da 192.168.56.30"
- Priorità: P2 (alta urgenza — potenziale attacco)
- Descrizione: include timestamp, IP sorgente, numero di tentativi, se account è stato bloccato

**Checkpoint B5:**
- [ ] Login falliti simulati correttamente generati
- [ ] Event ID 4625 trovati nell'Event Log con i dettagli corretti
- [ ] IP sorgente identificato (192.168.56.30 = WKS-LAB-01)
- [ ] Ticket di sicurezza aperto in GLPI P2

---

### Esercizio B6: Performance Monitoring e Baseline

**Obiettivo.** Stabilire una baseline di performance per DC-LAB-01 e creare un Performance Counter log automatizzato.

```powershell
# Crea un Data Collector Set per monitoring continuo
# Questo registra automaticamente le metriche ogni 60 secondi

$collectorName = "LAB-Performance-Baseline"
$logPath = "C:\PerfLogs\LAB"
New-Item -ItemType Directory -Path $logPath -Force | Out-Null

# Crea il collector tramite logman
logman create counter $collectorName `
    -c "\Processor(_Total)\% Processor Time" `
       "\Memory\Available MBytes" `
       "\Memory\Pages/sec" `
       "\PhysicalDisk(_Total)\Avg. Disk Queue Length" `
       "\Network Interface(*)\Bytes Total/sec" `
    -si 60 `
    -o "$logPath\$collectorName" `
    -f bin

# Avvia la raccolta
logman start $collectorName

Write-Host "Data Collector '$collectorName' avviato."
Write-Host "Log in: $logPath"

# Attendi 5 minuti raccogliendo dati
Start-Sleep -Seconds 300

# Ferma e verifica
logman stop $collectorName
Get-ChildItem $logPath -Filter "*.blg" | Select-Object Name, @{N="Size(MB)";E={[math]::Round($_.Length/1MB,2)}}
```

**Snapshot manuale delle metriche correnti:**

```powershell
# Cattura snapshot performance (esegui più volte per vedere variazioni)
function Get-PerfSnapshot {
    $cpu = (Get-Counter "\Processor(_Total)\% Processor Time").CounterSamples[0].CookedValue
    $ramAvailMB = (Get-Counter "\Memory\Available MBytes").CounterSamples[0].CookedValue
    $ramTotalMB = (Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory / 1MB
    $ramUsedPct = [math]::Round((1 - $ramAvailMB / $ramTotalMB) * 100, 1)
    $diskQueue = (Get-Counter "\PhysicalDisk(_Total)\Avg. Disk Queue Length").CounterSamples[0].CookedValue
    
    [PSCustomObject]@{
        Timestamp     = Get-Date -Format "HH:mm:ss"
        "CPU%" = [math]::Round($cpu, 1)
        "RAM%" = $ramUsedPct
        "RAM Avail(MB)" = [math]::Round($ramAvailMB, 0)
        "Disk Queue" = [math]::Round($diskQueue, 3)
    }
}

Write-Host "Raccolta dati performance (3 campioni ogni 10 secondi):"
1..3 | ForEach-Object {
    Get-PerfSnapshot
    Start-Sleep -Seconds 10
} | Format-Table -AutoSize
```

**Checkpoint B6:**
- [ ] Data Collector Set creato e avviato
- [ ] File `.blg` generato in `C:\PerfLogs\LAB\`
- [ ] Snapshot manuale mostra metriche plausibili per un DC idle (CPU < 10%, RAM < 40%)
- [ ] Sai interpretare cosa significa `Disk Queue > 2`

---

## PART C: SISTEMATIZZARE — Governance delle Operazioni Windows Server

---

### Progetto C1: SOP Windows Server — Monthly Health Check

Crea il file `C:\Labs\SOPs\SOP-WIN-001_monthly_health_check.md`:

```markdown
# SOP-WIN-001: Windows Server Monthly Health Check

**Versione:** 1.0
**Data creazione:** 2026-07-15
**Owner:** IT Operations
**Review annuale:** Luglio 2027
**Applicabilità:** Tutti i Windows Server in produzione

---

## 1. Scopo

Definire le attività mensili minime per garantire la salute, sicurezza e affidabilità di ogni Windows Server.

## 2. Frequenza

Prima settimana del mese, nella giornata concordata con il business.

## 3. Ruoli

| Ruolo | Responsabilità |
|---|---|
| IT Ops Engineer | Esecuzione procedure |
| IT Lead | Approvazione esiti, escalation |
| Business Owner | Conferma maintenance window |

## 4. Prerequisiti

- [ ] Snapshot VM creato prima di qualsiasi modifica
- [ ] Ticket Change Request aperto in GLPI (stato: "Approvato")
- [ ] Maintenance window comunicata agli utenti
- [ ] Contatto on-call disponibile durante la maintenance

## 5. Procedura

### 5.1 Active Directory Health (15 min)

```powershell
# Eseguire su ogni Domain Controller
dcdiag /q
repadmin /replsummary
netdom query fsmo
Get-ADDomain | Select-Object PDCEmulator, DomainMode
```

Esito accettabile: nessun test dcdiag in "FAILED"

### 5.2 Event Log Security Review (20 min)

```powershell
$since = (Get-Date).AddDays(-30)
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625; StartTime=$since} |
    Group-Object -Property {([xml]$_.ToXml()).Event.EventData.Data |
        Where-Object {$_.Name -eq "TargetUserName"} | Select-Object -Exp "#text"} |
    Sort-Object Count -Descending | Select-Object -First 10 Name, Count
```

Azione richiesta se: account con > 20 tentativi falliti nell'ultimo mese

### 5.3 Performance Baseline (10 min)

```powershell
Get-PerfSnapshot  # dalla funzione definita nell'esercizio B6
```

Soglie di allerta:
- CPU media mensile > 70% → capacity review
- RAM disponibile < 500 MB → upgrade memoria
- Disk Queue > 2 → I/O bottleneck investigation

### 5.4 Verifica Certificati (5 min)

```powershell
Get-ChildItem Cert:\LocalMachine\My |
    Where-Object {$_.NotAfter -lt (Get-Date).AddDays(60)} |
    Select-Object Subject, NotAfter
```

### 5.5 Backup / Snapshot Verification (10 min)

```powershell
# Verifica lo snapshot mensile è stato creato
# In ambiente production: controlla il log del backup agent
Get-ChildItem "C:\Backups" -Filter "*$(Get-Date -Format 'yyyyMM')*"
```

## 6. Post-Esecuzione

- [ ] Compilare Post-Maintenance Review in GLPI
- [ ] Chiudere il ticket Change Request
- [ ] Aggiornare il log mensile in SharePoint/Confluence
- [ ] Comunicare agli utenti il completamento

## 7. Escalation

| Evento | Azione | Responsabile |
|---|---|---|
| DCDiag FAILED su test critici | Incident P1, escalation immediata | IT Lead |
| RAM disponibile < 100 MB | Emergenza — riavvio servizi o emergency patch | IT Ops + IT Lead |
| Certificato scaduto | Emergency change per rinnovo | IT Ops |
```

---

### Progetto C2: Script Automazione — AD Backup e Health Report

```powershell
#!/usr/bin/env pwsh
# Salva come: C:\Labs\Scripts\monthly_ad_health_report.ps1
# Esegui: Prima settimana del mese su DC-LAB-01

param(
    [string]$ReportPath = "C:\Labs\Reports",
    [string]$EmailTo   = "",   # Lascia vuoto se non c'è SMTP configurato
    [int]$LookbackDays = 30
)

$timestamp = Get-Date -Format "yyyy-MM-dd"
$reportFile = Join-Path $ReportPath "AD_Health_${timestamp}.txt"
New-Item -ItemType Directory -Path $ReportPath -Force | Out-Null

function Write-Section {
    param([string]$Title, [string]$Content)
    $line = "=" * 60
    "$line`n$Title`n$line`n$Content`n" | Add-Content $reportFile
}

# Header
"ACTIVE DIRECTORY MONTHLY HEALTH REPORT`nData: $timestamp`nDC: $env:COMPUTERNAME" |
    Set-Content $reportFile

# --- FSMO Roles ---
$fsmo = netdom query fsmo 2>&1 | Out-String
Write-Section "FSMO ROLES" $fsmo

# --- DCDiag Summary ---
$dcdiag = dcdiag /q 2>&1 | Out-String
$failCount = ($dcdiag -split '\n' | Where-Object {$_ -match 'failed'}).Count
Write-Section "DCDIAG ($failCount tests FAILED)" $dcdiag

# --- AD Replication ---
$repl = repadmin /replsummary 2>&1 | Out-String
Write-Section "REPLICATION SUMMARY" $repl

# --- User Statistics ---
$since = (Get-Date).AddDays(-$LookbackDays)
$totalUsers = (Get-ADUser -Filter * -SearchBase "DC=lab,DC=local" -ErrorAction SilentlyContinue).Count
$enabledUsers = (Get-ADUser -Filter {Enabled -eq $true} -SearchBase "DC=lab,DC=local" -ErrorAction SilentlyContinue).Count
$lockedUsers = (Search-ADAccount -LockedOut -UsersOnly -SearchBase "DC=lab,DC=local" -ErrorAction SilentlyContinue).Count
$inactiveUsers = (Search-ADAccount -AccountInactive -TimeSpan (New-TimeSpan -Days 90) -UsersOnly -SearchBase "DC=lab,DC=local" -ErrorAction SilentlyContinue).Count

$userStats = @"
Totale account: $totalUsers
Account abilitati: $enabledUsers
Account bloccati ora: $lockedUsers
Account inattivi (>90gg): $inactiveUsers
"@
Write-Section "USER STATISTICS" $userStats

# --- Security Events ---
$failedLogins = (Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625; StartTime=$since} -ErrorAction SilentlyContinue).Count
$accountCreated = (Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4720; StartTime=$since} -ErrorAction SilentlyContinue).Count
$adminAdded = (Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4728; StartTime=$since} -ErrorAction SilentlyContinue).Count
$lockouts = (Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4740; StartTime=$since} -ErrorAction SilentlyContinue).Count

$secEvents = @"
Periodo: ultimi $LookbackDays giorni
Login falliti (4625): $failedLogins
Account creati (4720): $accountCreated
Aggiunte a gruppi privilegiati (4728): $adminAdded
Account bloccati (4740): $lockouts
"@
Write-Section "SECURITY EVENTS (ultimi $LookbackDays giorni)" $secEvents

# --- Performance Snapshot ---
try {
    $cpu = [math]::Round((Get-Counter "\Processor(_Total)\% Processor Time").CounterSamples[0].CookedValue, 1)
    $ramMB = [math]::Round((Get-Counter "\Memory\Available MBytes").CounterSamples[0].CookedValue, 0)
    $diskQ = [math]::Round((Get-Counter "\PhysicalDisk(_Total)\Avg. Disk Queue Length").CounterSamples[0].CookedValue, 3)
    $perfData = "CPU: ${cpu}% | RAM disponibile: ${ramMB} MB | Disk Queue: $diskQ"
} catch {
    $perfData = "Performance counters non disponibili"
}
Write-Section "PERFORMANCE SNAPSHOT" $perfData

# --- Certificati in scadenza ---
$expCerts = Get-ChildItem Cert:\LocalMachine\My |
    Where-Object {$_.NotAfter -lt (Get-Date).AddDays(60)} |
    Select-Object Subject, @{N="ScadeIl";E={$_.NotAfter.ToString("yyyy-MM-dd")}} |
    Format-Table | Out-String
if (-not $expCerts.Trim()) { $expCerts = "Nessun certificato in scadenza nei prossimi 60 giorni" }
Write-Section "CERTIFICATI IN SCADENZA (60 giorni)" $expCerts

Write-Host "`nReport generato: $reportFile"
Get-Content $reportFile
```

---

### Progetto C3: Connessione ITIL — Dove Vive Questo Tutorial nelle Pratiche

**Mappatura delle attività Windows Server alle pratiche ITIL v4:**

| Attività Windows | Pratica ITIL v4 | Categoria |
|---|---|---|
| AD Health Check mensile | **Monitoring and Event Management** | Service Management |
| Configurazione Group Policy | **IT Configuration Management** | Service Management |
| Creazione/modifica utenti | **Identity and Access Management** | Service Management |
| Patching Windows Server | **Release Management** + **Change Control** | Service Management |
| Event Log analysis | **Problem Management** (identificazione cause) | Service Management |
| Performance monitoring | **Capacity and Performance Management** | Service Management |
| Backup System State AD | **Service Continuity Management** | Service Management |
| Incident management (lockout, crash) | **Incident Management** | Service Management |

**Le 5 domande ITIL che ogni Windows Admin deve saper rispondere:**

1. **"Il servizio è disponibile?"** → `Test-NetConnection 192.168.56.10 -Port 389` (LDAP porta 389)
2. **"Quando è cambiato qualcosa?"** → Event Log ID 4720, 4728, 7045, System log
3. **"Chi ha fatto cosa?"** → Security log con audit policy abilitata
4. **"Come torniamo alla configurazione precedente?"** → Snapshot VirtualBox / System State backup
5. **"Cosa hanno impattato gli utenti?"** → Ticket GLPI per ogni Incident

---

## Checklist di Validazione — Tutorial ops03a Completato

### Fondamenti (Part A)
- [ ] Sai spiegare 3 differenze fondamentali tra Windows Server e Windows Client
- [ ] Sai elencare e descrivere i 5 FSMO roles e capire perché esistono
- [ ] Sai spiegare cos'è l'ordine LSDOU in Group Policy e cosa succede in caso di conflitto
- [ ] Sai elencare 5 Event IDs critici e il loro significato di sicurezza
- [ ] Sai interpretare i 4 indicatori di performance (CPU%, RAM disponibile, Disk Queue, Page Faults)

### Operazioni (Part B)
- [ ] DC-LAB-01 promosso a Domain Controller con dominio `lab.local`
- [ ] Struttura OU creata: Lab-Corp → Users → IT-Team/Finance/HR
- [ ] 3 utenti (mario.rossi, anna.bianchi, luca.ferrari) creati e assegnati ai gruppi corretti
- [ ] `dcdiag /q` non mostra errori sui test principali
- [ ] `repadmin /replsummary` eseguito e interpretato
- [ ] SYSVOL share accessibile e contenente le GPO
- [ ] GPO `LAB-Security-Baseline` creata con impostazioni screen saver
- [ ] Login falliti simulati e trovati nell'Event Log con `Get-WinEvent -Id 4625`
- [ ] Ticket di sicurezza aperto in GLPI per i tentativi di login falliti
- [ ] Data Collector Set creato e avviato — file `.blg` verificato
- [ ] Performance snapshot manuale eseguito e interpretato

### Governance (Part C)
- [ ] SOP-WIN-001 creata con tutte le sezioni (scope, frequenza, procedura, escalation)
- [ ] Script `monthly_ad_health_report.ps1` eseguito con successo
- [ ] Report generato in `C:\Labs\Reports\`
- [ ] Sai mappare le attività Windows Server alle pratiche ITIL v4 corrispondenti

---

## Appendice A: Comandi Windows Server — Riferimento Rapido

### Active Directory
```powershell
# Struttura dominio
Get-ADDomain | Select-Object DNSRoot, NetBIOSName, DomainMode, PDCEmulator
Get-ADForest | Select-Object Name, ForestMode, SchemaMaster

# FSMO roles
netdom query fsmo
Get-ADDomainController -Discover | Select-Object Name, IPv4Address

# Replica
repadmin /replsummary
repadmin /showrepl
dcdiag /test:replications
dcdiag /q

# Utenti e gruppi
Get-ADUser -Filter * | Select-Object Name, SamAccountName, Enabled
Get-ADGroupMember "Domain Admins" | Select-Object Name, objectClass

# Account lockout
Search-ADAccount -LockedOut | Select-Object Name, LastLogonDate
Unlock-ADAccount -Identity "mario.rossi"
```

### Group Policy
```powershell
# Lista GPO
Get-GPO -All | Select-Object DisplayName, GpoStatus, CreationTime

# Stato GPO su un computer
gpresult /scope computer /r
gpresult /scope user /r
gpresult /h C:\gpreport.html  # Report HTML completo

# Forza applicazione immediata
gpupdate /force

# Backup e restore GPO
Backup-GPO -Name "LAB-Security-Baseline" -Path "C:\Labs\GPO-Backup"
Restore-GPO -Name "LAB-Security-Baseline" -Path "C:\Labs\GPO-Backup"
```

### Event Log
```powershell
# Ultimi 100 eventi Security
Get-WinEvent -LogName Security -MaxEvents 100 |
    Select-Object TimeCreated, Id, Message | Format-Table -Wrap

# Cerca eventi specifici
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625; StartTime=(Get-Date).AddHours(-1)}

# Evento XML completo (per estrarre campi)
$event = Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625} -MaxEvents 1
[xml]$event.ToXml()

# Export log per analisi offline
wevtutil epl Security C:\Labs\Logs\security_$(Get-Date -Format 'yyyyMMdd').evtx
```

### Performance
```powershell
# Performance corrente
Get-Counter "\Processor(_Total)\% Processor Time","\Memory\Available MBytes","\PhysicalDisk(_Total)\Avg. Disk Queue Length"

# Processi per CPU
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 Name, CPU, WorkingSet

# Processi per memoria
Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 10 Name, @{N="RAM(MB)";E={[math]::Round($_.WorkingSet/1MB,1)}}
```

---

## Appendice B: Soglie di Allerta — Quando Alzare la Mano

| Indicatore | Verde (OK) | Giallo (Attenzione) | Rosso (Critico — agire subito) |
|---|---|---|---|
| CPU % | < 60% | 60-80% per > 15 min | > 80% per > 30 min |
| RAM disponibile | > 2 GB | 500 MB - 2 GB | < 200 MB |
| Disk Queue | < 1 | 1-2 | > 2 (sostenuto) |
| DCDiag failed | 0 | 1-2 (non critici) | Advertising, FsmoCheck, Replications |
| Login falliti/giorno | < 10 | 10-50 | > 50 o pattern su account admin |
| Lockout account | 0 | 1-2 (utenti normali) | Admin account, service account |
| Certificati scadenza | > 90 gg | 30-90 gg | < 30 gg |
| SYSVOL replica lag | < 1 minuto | 1-15 minuti | > 15 minuti o errore DFSR |

---

## Appendice C: Troubleshooting Rapido — Problemi Comuni DC

### "Il login degli utenti è lento o fallisce"

```
1. Verifica DNS: nslookup lab.local → deve rispondere con IP di DC-LAB-01
2. Verifica orario: w32tm /query /status → deve mostrare sincronizzazione attiva
3. Verifica NETLOGON: Get-Service Netlogon → deve essere Running
4. Verifica DC raggiungibile: Test-NetConnection 192.168.56.10 -Port 389
5. Verifica replica: repadmin /replsummary → nessun errore
6. Event Log: cerca Event ID 4771 (Kerberos pre-auth failure) per errori specifici
```

### "Utente dice che la GPO non si applica"

```
1. Forza applicazione: gpupdate /force (sul PC dell'utente)
2. Verifica link GPO: Get-GPInheritance -Target "OU=Computers,OU=Lab-Corp,DC=lab,DC=local"
3. Controlla se Block Inheritance è attivo sull'OU
4. Genera report: gpresult /h C:\gpreport.html → verifica sezione "Applied GPOs"
5. Controlla security filtering: la GPO deve avere "Authenticated Users" con Apply
6. Event Log: Applications and Services → Microsoft → Windows → GroupPolicy → Operational
```

### "Spazio su disco critico su DC-LAB-01"

```
1. Identifica consumatori: Get-ChildItem C:\ -Recurse | Sort-Object Length -Desc | Select -First 20 FullName, @{N="MB";E={[math]::Round($_.Length/1MB,1)}}
2. Event Log cleanup: wevtutil el | ForEach-Object { wevtutil cl $_ } (⚠ solo se hai già esportato i log)
3. WinSxS cleanup: DISM /Online /Cleanup-Image /StartComponentCleanup
4. IIS log purge (se IIS installato): IIS logs in C:\inetpub\logs
5. WSUS cleanup (se WSUS installato): Invoke-WsusServerCleanup (vedi ops02b)
```

---

## Riferimenti

| Risorsa | Posizione | Contenuto |
|---|---|---|
| Documento sorgente | `../03-gestione-sistemi-operativi.md` (sez. Windows) | Gestione Windows Server |
| Microsoft Docs AD | docs.microsoft.com/en-us/windows-server/identity/ | Active Directory documentation |
| FSMO Roles | docs.microsoft.com/en-us/windows-server/identity/ad-ds/plan/planning-operations-master-role-placement | FSMO placement guide |
| Event ID Reference | docs.microsoft.com/en-us/windows/security/threat-protection/auditing/ | Security Event ID reference |
| DCDiag Reference | docs.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2012-r2 | DCDiag documentation |
| Tutorial ops03b | `tutorial_ops03_ch1b_linux_server_ops_lab.md` | Continuazione: Linux Server Ops |
| Tutorial ops04b | `tutorial_ops04_ch1b_active_directory_ldap_lab.md` | Active Directory avanzato |

---

*Fine tutorial ops03a — Prossimo: `tutorial_ops03_ch1b_linux_server_ops_lab.md`*
