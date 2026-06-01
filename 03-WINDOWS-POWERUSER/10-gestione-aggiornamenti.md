# Gestione Aggiornamenti Windows — Guida Completa

> **Modulo 10** · **Aggiornamento:** 2026-05-22

> **Modulo del corso:** Amministrazione Windows enterprise
> **Prerequisiti:** [Rete Windows](06-rete-windows.md) · [Group Policy](21-group-policy-guida-completa.md) · [PowerShell](02-powershell.md)
> **Obiettivi di apprendimento:**
> 1. Comprendere l'architettura di Windows Update, le tipologie di aggiornamento e il ciclo Patch Tuesday
> 2. Installare, configurare e manutenere WSUS per la gestione centralizzata delle patch
> 3. Configurare Windows Update for Business (WUfB) e ring di deployment tramite GPO e Intune
> 4. Implementare strategie di rollback e gestione degli aggiornamenti zero-day
> 5. Raggiungere compliance ≥ 95% entro 30 giorni dal rilascio degli aggiornamenti
> **Tempo stimato:** lettura 75 min · lab 55 min
> **Livello:** proficient
> **Ultimo aggiornamento:** 2026-05-23

## Idee guida
1. **Patch tuesday: 2nd Tuesday del mese.**
2. **Patch rollback per security KB problematic.**
3. **KB → OS-version mapping table.**
4. **Ring deployment: insider → canary → broad.**
5. **Defense in depth: patching è la prima linea di difesa contro gli exploit.**
6. **Compliance ≥ 95% entro 30 giorni dal rilascio: obiettivo minimo enterprise.**
7. **Zero-day = procedura accelerata: skip ring, deploy immediato con rollback pronto.**


## Indice

- [Panoramica](#panoramica)
- [Architettura Windows Update](#architettura-windows-update)
- [Tipologie di Aggiornamento](#tipologie-di-aggiornamento)
- [Windows Update Fondamenti](#windows-update-fondamenti)
- [Delivery Optimization](#delivery-optimization)
- [WSUS Deep Dive](#wsus-deep-dive)
  - [Installazione e Prerequisiti](#installazione-e-prerequisiti)
  - [Post-Installazione e Configurazione](#post-installazione-e-configurazione)
  - [Computer Groups e Approvazione](#computer-groups-e-approvazione)
  - [Regole di Approvazione Automatica](#regole-di-approvazione-automatica)
  - [Reporting WSUS](#reporting-wsus)
  - [Manutenzione WSUS](#manutenzione-wsus)
  - [WSUS Replica e Gerarchia](#wsus-replica-e-gerarchia)
- [GPO per Aggiornamenti](#gpo-per-aggiornamenti)
  - [GPO WSUS Client](#gpo-wsus-client)
  - [GPO Windows Update for Business](#gpo-windows-update-for-business)
  - [GPO Maintenance Window](#gpo-maintenance-window)
  - [GPO Deferral e Pause](#gpo-deferral-e-pause)
- [Windows Update for Business](#windows-update-for-business)
- [Intune Update Management](#intune-update-management)
  - [Update Rings](#update-rings)
  - [Feature Update Policies](#feature-update-policies)
  - [Expedited Updates](#expedited-updates)
  - [Driver Management via Intune](#driver-management-via-intune)
- [Patch Tuesday — Ciclo di Rilascio](#patch-tuesday--ciclo-di-rilascio)
- [Strategia di Patching Ring-Based](#strategia-di-patching-ring-based)
- [SCCM/MECM Patching](#sccmmecm-patching)
  - [Software Update Points (SUP)](#software-update-points-sup)
  - [Deployment Packages](#deployment-packages)
  - [Maintenance Windows SCCM](#maintenance-windows-sccm)
  - [Compliance Reporting SCCM](#compliance-reporting-sccm)
- [Gestione Patch Enterprise](#gestione-patch-enterprise)
- [Third-Party Patching](#third-party-patching)
- [Hotpatching](#hotpatching)
- [Update Compliance e Reporting](#update-compliance-e-reporting)
- [Driver Management](#driver-management)
- [Rollback Aggiornamenti](#rollback-aggiornamenti)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Checklist Processo di Patch Management](#checklist-processo-di-patch-management)
- [Procedura di Emergency Patching](#procedura-di-emergency-patching)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)

---

## Panoramica

La gestione degli aggiornamenti è critica per sicurezza e stabilità. Windows offre tre modalità principali: Windows Update diretto (per small business), WSUS (on-premise, controllo totale), e Windows Update for Business (cloud-based, GPO/Intune). Un processo di patch management maturo include: valutazione, test, approvazione, deploy graduale e rollback.

Il patching non è un'attività opzionale. Ogni mese Microsoft corregge decine di vulnerabilità, molte delle quali classificate come Critical o Important. Il tempo medio tra la pubblicazione di un exploit e il suo sfruttamento attivo (time-to-exploit) è sceso sotto i 15 giorni per le vulnerabilità più gravi. Un'infrastruttura non patchata è un'infrastruttura compromessa — è solo questione di tempo.

Questo modulo copre l'intero ciclo di vita degli aggiornamenti: dall'architettura interna del client Windows Update, passando per le diverse tipologie di aggiornamento, fino alle strategie enterprise con WSUS, SCCM/MECM e Intune. Include troubleshooting avanzato, gestione driver, hotpatching e procedure di emergenza.

---

## Architettura Windows Update

Il sistema Windows Update è composto da diversi componenti che collaborano per scansionare, scaricare, installare e finalizzare gli aggiornamenti.

### Componenti principali

```
ARCHITETTURA WINDOWS UPDATE — FLUSSO COMPLETO

┌──────────────────────────────────────────────────────────────────────┐
│                        MICROSOFT UPDATE CDN                         │
│            (windowsupdate.com / delivery.mp.microsoft.com)          │
└──────────────────┬──────────────────────────────────────┬────────────┘
                   │                                      │
                   ▼                                      ▼
        ┌──────────────────┐                   ┌──────────────────┐
        │   WSUS Server    │                   │ Windows Update   │
        │  (on-premise)    │                   │ for Business     │
        └────────┬─────────┘                   │ (cloud policy)   │
                 │                             └────────┬─────────┘
                 │                                      │
                 ▼                                      ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     WINDOWS UPDATE CLIENT                           │
│                                                                     │
│  ┌─────────────┐  ┌────────────┐  ┌──────────┐  ┌───────────────┐  │
│  │ Update       │  │ Update     │  │ BITS     │  │ Update        │  │
│  │ Orchestrator │  │ Session    │  │ Transfer │  │ Installer     │  │
│  │ (USO)       │  │ Orchestr.  │  │ Service  │  │ (TrustedInst.)│  │
│  └──────┬──────┘  └─────┬──────┘  └────┬─────┘  └──────┬────────┘  │
│         │               │              │               │            │
│         ▼               ▼              ▼               ▼            │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                  Windows Update Agent (WUA)                 │    │
│  │            wuauserv / Update Orchestrator Service           │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  Store locale: C:\Windows\SoftwareDistribution\                     │
│  Log:          C:\Windows\Logs\WindowsUpdate\                       │
│  CBS Log:      C:\Windows\Logs\CBS\CBS.log                          │
└──────────────────────────────────────────────────────────────────────┘
```

### Flusso di aggiornamento dettagliato

```
FASE 1 — SCAN (Scansione)
─────────────────────────
1. USO (Update Session Orchestrator) avvia la scansione
   Trigger: schedulazione automatica, GPO, usoclient StartScan, utente manuale
2. WUA (Windows Update Agent) contatta la ScanSource:
   - Microsoft Update CDN (default)
   - WSUS server (se configurato via GPO)
   - Dual Scan (WUfB + WSUS, deprecato in W10 1803+)
3. WUA scarica i metadata del catalogo aggiornamenti
4. WUA confronta metadata con lo stato locale (CBS store)
5. WUA genera la lista di aggiornamenti applicabili

FASE 2 — DOWNLOAD
──────────────────
1. WUA passa la lista a BITS (Background Intelligent Transfer Service)
2. BITS scarica i payload (.cab / .msu / .esd / .wim)
   - Download in background, rispetta banda disponibile
   - Supporta ripresa dopo interruzione
   - Se Delivery Optimization abilitata: download P2P (peer LAN/Internet)
3. I file scaricati finiscono in:
   C:\Windows\SoftwareDistribution\Download\
4. WUA verifica hash e firma digitale dei pacchetti

FASE 3 — INSTALL
─────────────────
1. WUA invoca il Component-Based Servicing (CBS) stack
2. CBS elabora i pacchetti:
   - Manifesti (.mum / .cat)
   - Payload dei componenti
3. TrustedInstaller (servizio) applica le modifiche al WinSxS store
4. Aggiornamenti che richiedono sostituzione di file in uso:
   → Staging dei file, installazione parziale
   → Pending.xml registra le operazioni da completare

FASE 4 — COMMIT / REBOOT
─────────────────────────
1. Se reboot necessario:
   - Windows segnala "Restart required"
   - Active Hours impedisce reboot automatico nelle ore lavorative
   - Engagement reminders notificano l'utente
2. Al reboot:
   - Fase online → offline boot
   - CBS applica le operazioni pending
   - "Working on updates... X% complete"
3. Al login successivo:
   - CBS verifica integrità post-installazione
   - WUA aggiorna lo stato nel datastore locale
   - WUA riporta compliance al WSUS/WUfB
```

### Servizi coinvolti

```powershell
# Servizi critici per Windows Update

# Windows Update (wuauserv) — core del WUA
Get-Service wuauserv | Format-List Name, DisplayName, Status, StartType

# Update Orchestrator Service (UsoSvc) — coordinatore W10/W11
Get-Service UsoSvc | Format-List Name, DisplayName, Status, StartType

# Background Intelligent Transfer Service (BITS) — download
Get-Service BITS | Format-List Name, DisplayName, Status, StartType

# Windows Modules Installer (TrustedInstaller) — installazione componenti
Get-Service TrustedInstaller | Format-List Name, DisplayName, Status, StartType

# Cryptographic Services (CryptSvc) — verifica firme
Get-Service CryptSvc | Format-List Name, DisplayName, Status, StartType

# Windows Installer (msiserver) — pacchetti MSI
Get-Service msiserver | Format-List Name, DisplayName, Status, StartType

# Delivery Optimization (DoSvc) — P2P download
Get-Service DoSvc | Format-List Name, DisplayName, Status, StartType

# Directory critiche
# C:\Windows\SoftwareDistribution\         → download e datastore WUA
# C:\Windows\SoftwareDistribution\Download → file scaricati
# C:\Windows\SoftwareDistribution\DataStore → database stato aggiornamenti
# C:\Windows\WinSxS\                       → component store (side-by-side)
# C:\Windows\Logs\CBS\CBS.log              → log Component-Based Servicing
# C:\Windows\Logs\WindowsUpdate\           → ETL trace files (W10+)
# C:\Windows\Panther\                      → log feature update / upgrade
```

### Generazione log Windows Update

```powershell
# Su Windows 10/11 il log non è più un file testo semplice
# Il vecchio C:\Windows\WindowsUpdate.log non viene più aggiornato
# I log sono in formato ETL (Event Trace Log)

# Generare il log leggibile:
Get-WindowsUpdateLog
# Output: ~/Desktop/WindowsUpdate.log

# Il comando converte i file ETL in:
# C:\Windows\Logs\WindowsUpdate\*.etl → testo leggibile

# Per analisi rapida dei log:
Get-WindowsUpdateLog | Out-Null
$log = Get-Content "$env:USERPROFILE\Desktop\WindowsUpdate.log"
$log | Select-String "FAILED|ERROR|WARNING" | Select-Object -Last 50
```

---

## Tipologie di Aggiornamento

Microsoft classifica gli aggiornamenti in diverse categorie, ciascuna con un ciclo di rilascio e un impatto diverso.

### Tabella riassuntiva

```
TIPO                    │ FREQUENZA           │ REBOOT  │ DIMENSIONE    │ NOTE
────────────────────────┼─────────────────────┼─────────┼───────────────┼──────────────────────────
Quality Updates         │ Mensile (Patch Tue)  │ Sì      │ 200-800 MB    │ Cumulativi, sicurezza+fix
  ├── B Release         │ 2° martedì          │ Sì      │               │ Principale, sicurezza
  ├── C Release         │ 3° settimana (prev.) │ Sì      │               │ Preview non-security
  └── D Release         │ 4° settimana (prev.) │ Sì      │               │ Eliminato da 2023
Feature Updates         │ Annuale (H2)         │ Sì      │ 2-4 GB        │ Nuova versione OS
Servicing Stack Updates │ Variabile            │ A volte │ 10-50 MB      │ Aggiornano il motore WU
(SSU)                   │                     │         │               │ stesso
Driver Updates          │ Variabile            │ A volte │ Variabile     │ Hardware-specifici
Firmware Updates        │ Variabile            │ Sì      │ Variabile     │ UEFI firmware via WU
Definition Updates      │ Più volte/giorno     │ No      │ 1-50 MB       │ Defender signatures
.NET Updates            │ Mensile              │ A volte │ 50-200 MB     │ Framework/Runtime
Microcode Updates       │ Variabile            │ Sì      │ <1 MB         │ CPU microcode (Spectre)
```

### Quality Updates — Dettaglio

```
QUALITY UPDATES (Cumulative Updates - CU)
──────────────────────────────────────────

Caratteristiche:
- CUMULATIVI: ogni CU contiene TUTTI i fix precedenti
  → Installando l'ultimo CU si ottengono tutte le patch dal rilascio dell'OS
- Rilasciati il 2° martedì del mese ("Patch Tuesday" / "B Release")
- Contengono: fix sicurezza + fix affidabilità + fix funzionalità
- KB number univoco per ogni release (es. KB5034441)

B Release (Patch Tuesday):
- Rilascio: 2° martedì del mese, ~10:00 AM PST
- Contenuto: security fixes + non-security fixes
- Obbligatorio per compliance di sicurezza
- Supportato da Security Update Guide di Microsoft

C Release (Preview / Optional):
- Rilascio: 3°-4° settimana del mese
- Contenuto: preview dei fix non-security del prossimo mese
- OPZIONALE — non contiene fix di sicurezza nuovi
- Scopo: validare i fix prima del B Release successivo
- NON distribuire in produzione senza test

Naming convention tipica:
  2024-01 Cumulative Update for Windows 11 Version 23H2
  for x64-based Systems (KB5034123)
```

### Feature Updates

```
FEATURE UPDATES
───────────────

Caratteristiche:
- Aggiornano la versione dell'OS (es. 23H2 → 24H2)
- Cadenza annuale (rilascio H2, tipicamente settembre-novembre)
- Dimensione: 2-4 GB (download differenziale riduce)
- Supporto: 24 mesi (Home/Pro), 36 mesi (Enterprise/Education)
- Processo simile a un upgrade in-place dell'OS

Ciclo di vita supporto (esempio):
  Windows 11 23H2 → rilascio ottobre 2023
    Home/Pro: supportato fino a novembre 2025
    Enterprise: supportato fino a novembre 2026
  Windows 11 24H2 → rilascio ottobre 2024
    Home/Pro: supportato fino a novembre 2026
    Enterprise: supportato fino a novembre 2027

Rollback:
- Possibile entro 10 giorni dall'installazione (default)
- Estendibile a 30/60 giorni via DISM o GPO
- Dopo il periodo di rollback: i file di rollback vengono eliminati

# Estendere il periodo di rollback a 30 giorni:
DISM /Online /Set-OSUninstallWindow /Value:30
```

### Servicing Stack Updates (SSU)

```
SERVICING STACK UPDATES (SSU)
─────────────────────────────

La "servicing stack" è il componente che installa gli aggiornamenti stessi.
Un SSU aggiorna il motore di aggiornamento prima di applicare altri update.

Componenti della servicing stack:
- CBS (Component-Based Servicing)
- CSI (Component Servicing Infrastructure)
- CMI (Component Management Infrastructure)
- DMI (Driver Management Infrastructure)

Punti chiave:
- Gli SSU devono essere installati PRIMA dei CU quando richiesto
- Da Windows 10 2004+: SSU e CU possono essere combinati (Combined SSU + CU)
  → Microsoft li rilascia come pacchetto unico
  → Il sistema installa prima l'SSU, poi il CU automaticamente
- Gli SSU NON possono essere disinstallati
- La mancata installazione di un SSU può bloccare l'installazione di CU successivi
```

### Driver Updates e Firmware Updates

```
DRIVER UPDATES
──────────────
- Distribuiti tramite Windows Update, WSUS o Windows Update Catalog
- Classificazione: "Driver Updates" nel catalogo WSUS
- Tipi:
  - Automatic (distribuiti automaticamente da WU)
  - Manual (disponibili solo su Windows Update Catalog)
  - Optional (visibili in Settings → Optional updates)
- Rischi: driver incompatibili possono causare BSOD
  → Per questo motivo, molte organizzazioni escludono i driver da WSUS

FIRMWARE UPDATES (UEFI Firmware)
────────────────────────────────
- Distribuiti tramite Windows Update come pacchetti driver
- Aggiornano il firmware UEFI senza richiedere boot da USB/CD
- Richiedono:
  - UEFI boot (non legacy BIOS)
  - Supporto del vendor hardware (Surface, Dell, HP, Lenovo)
  - BitLocker: la chiave di recovery potrebbe essere richiesta
- Rischio elevato: un firmware update fallito può brickare il dispositivo
  → SEMPRE avere backup e chiave BitLocker prima dell'aggiornamento
```

---

## Windows Update Fondamenti

```powershell
# Modulo PSWindowsUpdate (non nativo, da PSGallery)
Install-Module PSWindowsUpdate -Scope CurrentUser
Import-Module PSWindowsUpdate

# Verificare aggiornamenti disponibili
Get-WindowsUpdate

# Installare tutti gli aggiornamenti
Install-WindowsUpdate -AcceptAll -AutoReboot

# Installare solo aggiornamenti specifici
Install-WindowsUpdate -KBArticleID KB5001234

# Cronologia aggiornamenti
Get-WUHistory | Select-Object -First 20 Title, Date, Result

# Metodo nativo (senza modulo)
# Verificare ultimo aggiornamento
Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 10

# Servizio Windows Update
Get-Service wuauserv | Select-Object Status, StartType
Restart-Service wuauserv

# Forzare check aggiornamenti
usoclient StartScan           # Windows 10/11
wuauclt /detectnow            # Legacy (Windows Server 2012 R2 e precedenti)

# Tipi di aggiornamento:
# - Quality Updates    → Patch mensili cumulative (sicurezza + bug fix)
# - Feature Updates    → Aggiornamenti versione maggiore (1-2 all'anno, solo client)
# - Driver Updates     → Driver hardware
# - Definition Updates → Antivirus/antimalware signatures
```

### Comandi usoclient (Windows 10/11)

```powershell
# usoclient è il successore di wuauclt su Windows 10/11
# Utilizza il Update Session Orchestrator (USO)

usoclient StartScan              # Avvia scansione aggiornamenti
usoclient StartDownload          # Avvia download aggiornamenti trovati
usoclient StartInstall           # Avvia installazione aggiornamenti scaricati
usoclient RefreshSettings        # Ricarica le impostazioni (dopo cambio GPO)
usoclient RestartDevice          # Riavvia il dispositivo per completare l'installazione
usoclient ScanInstallWait        # Scansione + installazione + attende completamento
usoclient ResumeUpdate           # Riprende un aggiornamento in pausa
usoclient StartInteractiveScan   # Scansione con UI interattiva

# Forzare un ciclo completo (scan + download + install):
usoclient StartScan
Start-Sleep -Seconds 30
usoclient StartDownload
Start-Sleep -Seconds 60
usoclient StartInstall
```

### Verifica stato aggiornamenti via COM

```powershell
# Accesso diretto all'API COM di Windows Update Agent
# Utile quando PSWindowsUpdate non è disponibile

$session = New-Object -ComObject Microsoft.Update.Session
$searcher = $session.CreateUpdateSearcher()

# Cercare aggiornamenti non installati
$result = $searcher.Search("IsInstalled=0 and Type='Software'")

Write-Host "Aggiornamenti disponibili: $($result.Updates.Count)"
foreach ($update in $result.Updates) {
    [PSCustomObject]@{
        Titolo      = $update.Title
        KB          = ($update.KBArticleIDs | ForEach-Object { "KB$_" }) -join ", "
        Severità    = $update.MsrcSeverity
        Dimensione  = "{0:N2} MB" -f ($update.MaxDownloadSize / 1MB)
        AutoSelect  = $update.AutoSelectOnWebSites
        Obbligatorio = $update.IsMandatory
    }
}

# Cercare aggiornamenti installati recentemente
$searcher2 = $session.CreateUpdateSearcher()
$history = $searcher2.QueryHistory(0, 20)
foreach ($entry in $history) {
    [PSCustomObject]@{
        Data      = $entry.Date
        Titolo    = $entry.Title
        Risultato = switch ($entry.ResultCode) {
            0 { "Non iniziato" }
            1 { "In corso" }
            2 { "Completato" }
            3 { "Completato con errori" }
            4 { "Fallito" }
            5 { "Annullato" }
        }
        HResult   = "0x{0:X8}" -f $entry.HResult
    }
}
```

### Windows Update via Registry

```powershell
# Chiavi di registro principali per Windows Update
# HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate

# Verificare configurazione attuale
$wuRegPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate"
$wuAUPath  = "$wuRegPath\AU"

if (Test-Path $wuRegPath) {
    Get-ItemProperty $wuRegPath | Format-List
}
if (Test-Path $wuAUPath) {
    Get-ItemProperty $wuAUPath | Format-List
}

# Chiavi importanti:
# WUServer                → URL server WSUS
# WUStatusServer           → URL server statistiche WSUS
# DoNotConnectToWindowsUpdateInternetLocations → 1 = solo WSUS, no Microsoft
# DeferQualityUpdates      → 1 = abilita deferral quality updates
# DeferQualityUpdatesPeriodInDays → giorni di deferral (0-30)
# DeferFeatureUpdates      → 1 = abilita deferral feature updates
# DeferFeatureUpdatesPeriodInDays → giorni di deferral (0-365)
# PauseDeferrals           → 1 = pausa temporanea tutti gli aggiornamenti

# Verificare la ScanSource effettiva del client
$useWUServer = (Get-ItemProperty "$wuAUPath" -ErrorAction SilentlyContinue).UseWUServer
if ($useWUServer -eq 1) {
    $server = (Get-ItemProperty $wuRegPath).WUServer
    Write-Host "ScanSource: WSUS → $server"
} else {
    Write-Host "ScanSource: Microsoft Update (Internet)"
}
```

---

## Delivery Optimization

```powershell
# Delivery Optimization (DO) è il sistema P2P di Windows per distribuire
# aggiornamenti, app Store e altri contenuti tra peer nella rete

# Modalità di download:
# 0 = HTTP only (nessun P2P)
# 1 = HTTP + LAN peers
# 2 = HTTP + LAN peers (Group - stessa rete/dominio)  ← consigliato enterprise
# 3 = HTTP + LAN + Internet peers
# 99 = Simple download mode (nessun P2P, nessun BITS)
# 100 = Bypass mode (usa BITS, nessuna DO)

# Verificare configurazione DO attuale
Get-DeliveryOptimizationStatus | Format-List

# Statistiche di risparmio banda
Get-DeliveryOptimizationPerfSnap

# Monitorare download attivi
Get-DeliveryOptimizationLog | Select-Object -Last 20

# Configurazione via GPO:
# Computer → Administrative Templates → Windows Components → Delivery Optimization
#   - Download Mode: 2 (Group/LAN)
#   - Group ID: GUID del gruppo DO (per segmentare sedi diverse)
#   - Max Upload Bandwidth: limitare banda upload P2P
#   - Max Cache Size: percentuale disco per cache DO (default 20%)
#   - Max Cache Age: secondi prima di eliminare cache (default 259200 = 3 giorni)

# Configurazione via registry:
# HKLM:\SOFTWARE\Policies\Microsoft\Windows\DeliveryOptimization
# DODownloadMode = 2
# DOGroupId = "{GUID}"
# DOMaxCacheSize = 20
# DOMaxCacheAge = 604800

# Per ambienti con WSUS: DO può coesistere con WSUS
# I client scaricano da WSUS come sorgente primaria
# e usano DO per condividere tra peer (riduce carico WSUS)

# Connected Cache (Microsoft Connected Cache):
# Server cache on-premise integrato con SCCM/MECM
# I client DO scaricano da questo server locale invece che da Internet
# Richiede SCCM distribution point con Connected Cache abilitato
```

---

## WSUS Deep Dive

### Installazione e Prerequisiti

```powershell
# PREREQUISITI WSUS
# ─────────────────
# OS: Windows Server 2016/2019/2022/2025
# RAM: minimo 4 GB (8 GB consigliato, 16 GB per >10.000 client)
# Disco: 
#   - OS: 60 GB
#   - WSUS Content: 100-500 GB (dipende da prodotti selezionati)
#   - Database: 20-100 GB
# CPU: 2+ core (4+ consigliato)
# IIS: installato automaticamente con il ruolo WSUS
# .NET Framework: 4.8+
# Database: WID (Windows Internal Database) o SQL Server

# NOTA: WID è gratuito ma ha limitazioni:
#   - Non supporta gestione remota del DB
#   - Performance inferiori con >10.000 client
#   - Per grandi ambienti: usare SQL Server

# INSTALLAZIONE WSUS
# ───────────────────

# PowerShell — installazione con WID
Install-WindowsFeature UpdateServices -IncludeManagementTools

# PowerShell — installazione con SQL Server
Install-WindowsFeature UpdateServices-Services, UpdateServices-DB `
    -IncludeManagementTools

# Post-installazione: inizializzazione content directory
# La directory deve essere su un volume con spazio sufficiente
& "C:\Program Files\Update Services\Tools\WsusUtil.exe" postinstall `
    CONTENT_DIR=D:\WSUS_Content

# Se si usa SQL Server:
& "C:\Program Files\Update Services\Tools\WsusUtil.exe" postinstall `
    SQL_INSTANCE_NAME="SQL01\WSUS" CONTENT_DIR=D:\WSUS_Content

# Verificare installazione
Get-WindowsFeature UpdateServices* | Format-Table Name, InstallState

# Configurare IIS Application Pool per WSUS
Import-Module WebAdministration
# Aumentare Private Memory Limit (default 1843200 KB è troppo basso)
Set-ItemProperty "IIS:\AppPools\WsusPool" -Name processModel.maxWorkerProcesses -Value 0
Set-ItemProperty "IIS:\AppPools\WsusPool" -Name recycling.periodicRestart.privateMemory -Value 0
# 0 = illimitato. Alternativa: impostare a 4194304 (4 GB) o 8388608 (8 GB)

# Porta WSUS:
# Default HTTP:  8530
# Default HTTPS: 8531
# Per ambienti che richiedono SSL: configurare certificato su IIS
```

### Post-Installazione e Configurazione

```powershell
# Dopo l'installazione base (vedi 03-ruoli-server.md)

# Configurazione prodotti
$wsus = Get-WsusServer
$products = Get-WsusProduct
# Abilitare solo prodotti necessari
$products | Where-Object {
    $_.Product.Title -in @(
        "Windows Server 2022",
        "Windows Server 2019",
        "Windows 11",
        "Microsoft Defender Antivirus",
        "Microsoft Edge",
        "Microsoft Office 2019"
    )
} | Set-WsusProduct

# Classificazioni
Get-WsusClassification | Where-Object {
    $_.Classification.Title -in @(
        "Critical Updates",
        "Security Updates",
        "Update Rollups",
        "Service Packs",
        "Definition Updates"
    )
} | Set-WsusClassification

# Sincronizzazione schedulata
$subscription = $wsus.GetSubscription()
$subscription.SynchronizeAutomatically = $true
$subscription.SynchronizeAutomaticallyTimeOfDay = [TimeSpan]::New(2, 0, 0)  # 02:00
$subscription.NumberOfSynchronizationsPerDay = 1
$subscription.Save()

# Configurazione lingue (riduce spazio disco)
$config = $wsus.GetConfiguration()
$config.AllUpdateLanguagesEnabled = $false
$config.SetEnabledUpdateLanguages(@("en", "it"))
$config.Save()

# Avviare prima sincronizzazione manuale
$subscription.StartSynchronization()

# Monitorare progresso sincronizzazione
while (($subscription.GetSynchronizationStatus()) -ne 'NotProcessing') {
    $progress = $subscription.GetSynchronizationProgress()
    Write-Host "Fase: $($progress.Phase) - $($progress.ProcessedItems)/$($progress.TotalItems)"
    Start-Sleep -Seconds 10
}
Write-Host "Sincronizzazione completata"
```

### Computer Groups e Approvazione

```powershell
# Creare gruppi target (deploy graduale)
$wsus.CreateComputerTargetGroup("01-Test")
$wsus.CreateComputerTargetGroup("02-Pilot")
$wsus.CreateComputerTargetGroup("03-Production-Servers")
$wsus.CreateComputerTargetGroup("04-Production-Workstations")

# Creare sotto-gruppi per segmentazione avanzata
$prodServers = $wsus.GetComputerTargetGroups() |
    Where-Object { $_.Name -eq "03-Production-Servers" }
$wsus.CreateComputerTargetGroup("03a-App-Servers", $prodServers)
$wsus.CreateComputerTargetGroup("03b-DB-Servers", $prodServers)
$wsus.CreateComputerTargetGroup("03c-Domain-Controllers", $prodServers)

# Spostare computer in un gruppo
$computer = $wsus.GetComputerTargets() |
    Where-Object { $_.FullDomainName -eq "SRV-APP01.contoso.com" }
$targetGroup = $wsus.GetComputerTargetGroups() |
    Where-Object { $_.Name -eq "03a-App-Servers" }
$targetGroup.AddComputerTarget($computer)

# Modalità di assegnazione gruppi:
# 1. Server-side targeting: assegnazione manuale dalla console WSUS
# 2. Client-side targeting: assegnazione via GPO (consigliato enterprise)
#    GPO: "Enable client-side targeting" → Group name: "03-Production-Servers"

# Approvare manualmente per gruppi specifici
Get-WsusUpdate -Classification "Security Updates" -Approval Unapproved |
    Approve-WsusUpdate -Action Install -TargetGroupName "01-Test"

# Approvazione con deadline (forza installazione entro una data)
$update = Get-WsusUpdate -UpdateId "GUID-dell-aggiornamento"
$group = $wsus.GetComputerTargetGroups() |
    Where-Object { $_.Name -eq "03-Production-Servers" }
$deadline = [DateTime]::Now.AddDays(7)
$update.Approve("Install", $group, $deadline)

# Rifiutare aggiornamenti non necessari
Get-WsusUpdate -Status FailedOrNeeded | Where-Object {
    $_.Update.Title -like "*Itanium*" -or $_.Update.Title -like "*ARM*"
} | Deny-WsusUpdate

# Rifiutare aggiornamenti superati (superseded)
Get-WsusUpdate | Where-Object {
    $_.Update.IsSuperseded -and -not $_.Update.IsApproved
} | Deny-WsusUpdate
```

### Regole di Approvazione Automatica

```powershell
# Le regole di approvazione automatica sono fondamentali per:
# - Definition Updates: devono essere distribuiti immediatamente
# - Critical Updates: possono essere auto-approvati per il gruppo Test
# - Security Updates: auto-approvazione selettiva per ambienti non-critici

# Approvazione automatica per definizioni antivirus
$rule = $wsus.CreateInstallApprovalRule("Auto-Approve-Definitions")
$defClass = $wsus.GetUpdateClassifications() |
    Where-Object { $_.Title -eq "Definition Updates" }
$rule.GetUpdateClassifications().Add($defClass)
$allComputers = $wsus.GetComputerTargetGroups() |
    Where-Object { $_.Name -eq "All Computers" }
$rule.GetComputerTargetGroups().Add($allComputers)
$rule.Enabled = $true
$rule.Save()
$rule.ApplyRule()  # Applica retroattivamente agli aggiornamenti esistenti

# Approvazione automatica Critical/Security solo per gruppo Test
$ruleTest = $wsus.CreateInstallApprovalRule("Auto-Approve-Test-Ring")
$critClass = $wsus.GetUpdateClassifications() |
    Where-Object { $_.Title -in @("Critical Updates", "Security Updates") }
foreach ($c in $critClass) {
    $ruleTest.GetUpdateClassifications().Add($c)
}
$testGroup = $wsus.GetComputerTargetGroups() |
    Where-Object { $_.Name -eq "01-Test" }
$ruleTest.GetComputerTargetGroups().Add($testGroup)
$ruleTest.Enabled = $true
$ruleTest.Save()

# Elencare regole di approvazione esistenti
$wsus.GetInstallApprovalRules() | ForEach-Object {
    [PSCustomObject]@{
        Nome     = $_.Name
        ID       = $_.Id
        Abilitata = $_.Enabled
        Classi   = ($_.GetUpdateClassifications() | ForEach-Object { $_.Title }) -join ", "
        Gruppi   = ($_.GetComputerTargetGroups() | ForEach-Object { $_.Name }) -join ", "
    }
}

# Disabilitare una regola
$ruleToDisable = $wsus.GetInstallApprovalRules() |
    Where-Object { $_.Name -eq "Auto-Approve-Test-Ring" }
$ruleToDisable.Enabled = $false
$ruleToDisable.Save()
```

### Reporting WSUS

```powershell
# Report stato computer
Get-WsusComputer | Select-Object FullDomainName, OSDescription,
    LastReportedStatusTime, LastSyncTime |
    Sort-Object LastReportedStatusTime

# Report computer con patch mancanti
$scope = New-Object Microsoft.UpdateServices.Administration.ComputerTargetScope
$scope.IncludedInstallationStates =
    [Microsoft.UpdateServices.Administration.UpdateInstallationStates]::NotInstalled

$wsus.GetComputerTargets($scope) | ForEach-Object {
    $computerUpdates = $_.GetUpdateInstallationInfoPerUpdate()
    $needed = $computerUpdates | Where-Object {
        $_.UpdateInstallationState -eq 'NotInstalled'
    }
    [PSCustomObject]@{
        Computer       = $_.FullDomainName
        OS             = $_.OSDescription
        NeededUpdates  = $needed.Count
        LastContact    = $_.LastReportedStatusTime
        LastSync       = $_.LastSyncTime
        IPAddress      = $_.IPAddress
    }
} | Sort-Object NeededUpdates -Descending |
    Export-Csv "C:\Reports\PatchCompliance-$(Get-Date -Format yyyyMMdd).csv" -NoTypeInformation

# Report aggiornamenti per classificazione
$wsus.GetUpdateClassifications() | ForEach-Object {
    $classScope = New-Object Microsoft.UpdateServices.Administration.UpdateScope
    $classScope.UpdateClassifications.Add($_)
    $updates = $wsus.GetUpdates($classScope)
    [PSCustomObject]@{
        Classificazione = $_.Title
        Totale          = $updates.Count
        Approvati       = ($updates | Where-Object { $_.IsApproved }).Count
        Rifiutati       = ($updates | Where-Object { $_.IsDeclined }).Count
        Superati        = ($updates | Where-Object { $_.IsSuperseded }).Count
    }
}

# Report sincronizzazione
$syncHistory = $wsus.GetSubscription().GetSynchronizationHistory()
$syncHistory | Select-Object -First 10 | ForEach-Object {
    [PSCustomObject]@{
        Data        = $_.StartTime
        Risultato   = $_.Result
        NuoviUpdate = $_.NumberOfNewUpdates
        Revisionati = $_.NumberOfRevisedUpdates
        Errori      = $_.NumberOfErrors
    }
}

# Report computer non conformi (non contattano WSUS da X giorni)
$daysThreshold = 7
$cutoffDate = (Get-Date).AddDays(-$daysThreshold)
Get-WsusComputer | Where-Object {
    $_.LastSyncTime -lt $cutoffDate
} | Select-Object FullDomainName, LastSyncTime, IPAddress |
    Sort-Object LastSyncTime |
    Export-Csv "C:\Reports\StaleComputers.csv" -NoTypeInformation
```

### Manutenzione WSUS

```powershell
# WSUS usa WID (Windows Internal Database) o SQL Server
# WID richiede manutenzione periodica:

# Pulizia WSUS (critica per performance) — eseguire mensilmente
Invoke-WsusServerCleanup -CleanupObsoleteUpdates -CleanupUnneededContentFiles `
    -CompressUpdates -DeclineExpiredUpdates -DeclineSupersededUpdates

# Pulizia avanzata con output dettagliato
$cleanupManager = $wsus.GetCleanupManager()
$cleanupScope = New-Object Microsoft.UpdateServices.Administration.CleanupScope
$cleanupScope.CleanupObsoleteUpdates = $true
$cleanupScope.CleanupUnneededContentFiles = $true
$cleanupScope.CompressUpdates = $true
$cleanupScope.DeclineExpiredUpdates = $true
$cleanupScope.DeclineSupersededUpdates = $true
$cleanupScope.CleanupObsoleteComputers = $true
$result = $cleanupManager.PerformCleanup($cleanupScope)

Write-Host "Risultati pulizia:"
Write-Host "  Update superati rifiutati: $($result.SupersededUpdatesDeclined)"
Write-Host "  Update scaduti rifiutati:  $($result.ExpiredUpdatesDeclined)"
Write-Host "  Update obsoleti eliminati: $($result.ObsoleteUpdatesDeleted)"
Write-Host "  Update compressi:          $($result.UpdatesCompressed)"
Write-Host "  Revisioni eliminate:        $($result.ObsoleteRevisionsDeleted)"
Write-Host "  Spazio disco liberato:     $($result.DiskSpaceFreed / 1MB) MB"

# Reindex database WID
# Connessione WID: \\.\pipe\MICROSOFT##WID\tsql\query
# Eseguire via sqlcmd o SSMS:

# Script T-SQL per reindex WSUS (salvare come WSUS-Reindex.sql):
# USE SUSDB
# GO
# -- Reindex tutte le tabelle
# DECLARE @TableName NVARCHAR(256)
# DECLARE TableCursor CURSOR FOR
#   SELECT '[' + s.name + '].[' + t.name + ']'
#   FROM sys.tables t
#   INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
# OPEN TableCursor
# FETCH NEXT FROM TableCursor INTO @TableName
# WHILE @@FETCH_STATUS = 0
# BEGIN
#   EXEC('ALTER INDEX ALL ON ' + @TableName + ' REBUILD WITH (FILLFACTOR=90)')
#   FETCH NEXT FROM TableCursor INTO @TableName
# END
# CLOSE TableCursor
# DEALLOCATE TableCursor
# GO

# Eseguire reindex su WID:
& sqlcmd -S "\\.\pipe\MICROSOFT##WID\tsql\query" -i "C:\Scripts\WSUS-Reindex.sql"

# Monitorare spazio disco WSUS content
$contentDir = (Get-WsusServer).GetConfiguration().LocalContentPath
$disk = Get-PSDrive -Name ($contentDir.Substring(0,1))
Write-Host "WSUS Content: $contentDir"
Write-Host "Spazio usato: $([math]::Round($disk.Used / 1GB, 2)) GB"
Write-Host "Spazio libero: $([math]::Round($disk.Free / 1GB, 2)) GB"

# IIS Application Pool — verificare e configurare
Import-Module WebAdministration
$pool = Get-ItemProperty "IIS:\AppPools\WsusPool"
Write-Host "WsusPool State: $($pool.state)"
Write-Host "Memory Limit: $($pool.recycling.periodicRestart.privateMemory) KB"
# Se WSUS è lento: aumentare a 0 (illimitato) o almeno 4 GB:
# Set-ItemProperty "IIS:\AppPools\WsusPool" -Name recycling.periodicRestart.privateMemory -Value 0

# Schedulare manutenzione mensile (Task Scheduler)
# Creare script C:\Scripts\WSUS-Maintenance.ps1 con:
#   Import-Module UpdateServices
#   Invoke-WsusServerCleanup -CleanupObsoleteUpdates -CleanupUnneededContentFiles `
#       -CompressUpdates -DeclineExpiredUpdates -DeclineSupersededUpdates
#   & sqlcmd -S "\\.\pipe\MICROSOFT##WID\tsql\query" -i "C:\Scripts\WSUS-Reindex.sql"
# Schedulare con Task Scheduler: il 1° domenica di ogni mese alle 04:00
```

### WSUS Replica e Gerarchia

```
WSUS REPLICA / DOWNSTREAM SERVER
─────────────────────────────────

Scenario: organizzazione multi-sede con banda WAN limitata

Topologia tipica:

  [Microsoft Update CDN]
           │
           ▼
  ┌─────────────────────┐
  │  WSUS Upstream       │  (sede centrale — approva aggiornamenti)
  │  wsus-hq.contoso.com │
  └──────────┬───────────┘
             │ (sincronizzazione metadata + content)
      ┌──────┴──────┐
      ▼             ▼
┌──────────┐  ┌──────────┐
│ WSUS     │  │ WSUS     │  (sedi remote — replica o autonomo)
│ Replica  │  │ Autonomo │
│ Milano   │  │ Roma     │
└──────────┘  └──────────┘

Replica vs. Autonomo:
- Replica: eredita TUTTE le approvazioni dal server upstream
  → Usare quando tutte le sedi devono avere le stesse policy
  → I gruppi e le approvazioni sono gestiti centralmente
- Autonomo: scarica metadata dal server upstream ma gestisce le proprie approvazioni
  → Usare quando ogni sede ha esigenze diverse

Configurazione downstream server:
1. Installare WSUS sulla sede remota
2. Nel wizard, selezionare "Replica" o "Autonomous"
3. Specificare il server upstream: http://wsus-hq:8530
4. La sincronizzazione scarica metadata + content dal server upstream
   (non da Microsoft, risparmiando banda WAN)

# Verificare gerarchia WSUS
$wsus = Get-WsusServer
$config = $wsus.GetConfiguration()
Write-Host "Is Replica: $($config.IsReplicaServer)"
Write-Host "Upstream Server: $($config.UpstreamWsusServerName)"
Write-Host "Upstream Port: $($config.UpstreamWsusServerPortNumber)"
Write-Host "Upstream SSL: $($config.UpstreamWsusServerUseSsl)"
```

---

## GPO per Aggiornamenti

### GPO WSUS Client

```powershell
# WSUS via GPO
# Computer → Administrative Templates → Windows Components → Windows Update

# GPO chiave per WSUS:
# 1. Specify intranet Microsoft update service location:
#    - Intranet update service: http://wsus-server:8530
#    - Intranet statistics server: http://wsus-server:8530

# 2. Configure Automatic Updates:
#    - 2 = Notify before download
#    - 3 = Auto download, notify for install
#    - 4 = Auto download, schedule install (consigliato server)
#    - 5 = Allow local admin to choose (solo client)

# 3. Scheduled install day/time:
#    - Day: 0 (every day) o giorno specifico
#    - Time: 03:00 (fuori orario lavorativo)

# 4. Enable client-side targeting:
#    - Group name: es. "03-Production-Servers"
#    - Assegna automaticamente il computer al gruppo WSUS

# 5. No auto-restart with logged on users:
#    - Per server: Disabled (restart automatico)
#    - Per workstation: Enabled (non forzare restart se utente loggato)

# 6. Maintenance window (per server):
# Computer → Administrative Templates → Windows Components → Windows Update
#    → Configure Automatic Updates → Scheduled install time
#    → E configurare Active Hours per i client

# Elenco completo GPO critiche per WSUS:
#
# POLICY                                              │ VALORE CONSIGLIATO SERVER  │ VALORE WORKSTATION
# ────────────────────────────────────────────────────┼───────────────────────────┼────────────────────
# Specify intranet update service                     │ http://wsus:8530          │ http://wsus:8530
# Configure Automatic Updates                        │ 4 (auto download+install) │ 3 (auto download)
# Scheduled install day                               │ 0 (ogni giorno)           │ 0
# Scheduled install time                              │ 03:00                     │ 12:00
# Enable client-side targeting                        │ "Prod-Servers"            │ "Prod-WKS"
# No auto-restart with logged-on users                │ Disabled                  │ Enabled
# Always automatically restart at scheduled time      │ Enabled (15 min)          │ Disabled
# Do not connect to Windows Update Internet locations │ Enabled                   │ Enabled
# Allow signed updates from intranet WU location      │ Enabled                   │ Enabled

# Verifica GPO applicata su un client
gpresult /r /scope:computer | Select-String "WindowsUpdate|WSUS"

# Test connettività client → WSUS
Test-NetConnection -ComputerName wsus-server -Port 8530

# Forzare aggiornamento GPO
gpupdate /force
# Poi forzare scansione
usoclient RefreshSettings
usoclient StartScan
```

### GPO Windows Update for Business

```powershell
# GPO specifiche per WUfB:
# Computer → Administrative Templates → Windows Components → Windows Update
#   → Manage updates offered from Windows Update

# Select when Quality Updates are received:
#   - Enabled
#   - Deferral days: 0-30 (consigliato 7-14 per produzione)
#   - Pause Quality Updates: Enabled + data inizio (max 35 giorni)

# Select when Feature Updates are received:
#   - Enabled
#   - Semi-Annual Channel
#   - Deferral days: 0-365 (consigliato 60-120 per produzione)
#   - Pause Feature Updates: Enabled + data inizio (max 35 giorni)

# Manage preview builds:
#   - Disable preview builds (produzione)
#   - Enable preview builds: Release Preview (solo pilot/test)

# Do not include drivers with Windows Updates:
#   - Enabled → esclude driver da WU (gestione separata)

# Configure Active Hours:
#   - Start: 08:00
#   - End: 17:00
#   - Oppure: "Intelligent Active Hours" = Windows impara le abitudini utente

# GPO WUfB per deploy graduale (esempio 4 ring tramite 4 GPO separate):
#
# GPO "WUfB-Ring0-IT":
#   Quality Deferral: 0 giorni
#   Feature Deferral: 0 giorni
#   → Filtrare su OU o Security Group del team IT
#
# GPO "WUfB-Ring1-Pilot":
#   Quality Deferral: 3 giorni
#   Feature Deferral: 14 giorni
#   → Filtrare su OU Pilot (10% utenti early adopter)
#
# GPO "WUfB-Ring2-Broad":
#   Quality Deferral: 7 giorni
#   Feature Deferral: 60 giorni
#   → Filtrare su OU Production
#
# GPO "WUfB-Ring3-Critical":
#   Quality Deferral: 14 giorni
#   Feature Deferral: 120 giorni
#   → Filtrare su OU Mission-Critical
```

### GPO Maintenance Window

```powershell
# La finestra di manutenzione determina QUANDO il sistema può installare e riavviarsi

# Per Server (tramite GPO):
# Configure Automatic Updates:
#   - Option 4: Auto download and schedule the install
#   - Scheduled install day: 1 (Domenica, fuori orario lavorativo)
#   - Scheduled install time: 03:00
#   - Every week (default)

# Always automatically restart at the scheduled time:
#   - Enabled
#   - Restart timer: 15 minuti (dopo lo scheduled install time)

# Specify deadline before auto-restart for update installation:
#   - Quality Updates: 2 days
#   - Feature Updates: 7 days
#   → Dopo la deadline, il reboot è forzato anche con utente loggato

# Per Workstation:
# Active Hours:
#   - Impediscono reboot automatico durante le ore lavorative
#   - Range: massimo 18 ore
#   - Consigliato: 07:00 - 19:00

# Turn off auto-restart for updates during active hours:
#   - Enabled → nessun reboot durante Active Hours

# Specify Engaged restart transition and notification schedule:
#   - Transition days: 2 (dopo 2 giorni, mostra reminder persistente)
#   - Snooze: 3 (volte che l'utente può posporre)
#   - Deadline: 7 (dopo 7 giorni, reboot forzato)

# Per ambienti con SCCM/MECM:
# Le maintenance windows di SCCM hanno precedenza sulle GPO
# Configurabili per collection con granularità molto maggiore
# Vedere sezione SCCM più avanti
```

### GPO Deferral e Pause

```powershell
# DEFERRAL = ritardare di N giorni l'offerta dell'aggiornamento
# PAUSE = sospendere completamente per un massimo di 35 giorni

# Quality Updates deferral:
# GPO: Select when Quality Updates are received
# Registry: DeferQualityUpdatesPeriodInDays (0-30)
# Effetto: il client non vede il quality update per N giorni dopo il rilascio

# Feature Updates deferral:
# GPO: Select when Preview Builds and Feature Updates are received
# Registry: DeferFeatureUpdatesPeriodInDays (0-365)
# Effetto: il client non vede il feature update per N giorni dopo il rilascio

# Pause Quality Updates:
# GPO: Select when Quality Updates are received → Pause
# Registry: PauseQualityUpdatesStartTime (data ISO 8601)
# Durata: massimo 35 giorni dalla data di inizio
# ATTENZIONE: dopo la scadenza, il client deve installare TUTTI gli update
# accumulati prima di poter fare pause di nuovo

# Pause Feature Updates:
# GPO: Select when Preview Builds and Feature Updates are received → Pause
# Registry: PauseFeatureUpdatesStartTime (data ISO 8601)
# Stesse regole del quality pause

# Verificare stato deferral/pause su un client:
$wuPath = "HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UpdatePolicy\Settings"
if (Test-Path $wuPath) {
    Get-ItemProperty $wuPath | Select-Object *Defer*, *Pause*
}

# Safeguard Holds (Microsoft):
# Microsoft può bloccare automaticamente un Feature Update
# se rileva incompatibilità hardware/software sul dispositivo
# Visibile in: Settings → Windows Update → "Your device is not ready"
# NON forzare l'installazione ignorando i safeguard hold in produzione
# Registry per verificare:
# HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\TargetVersionUpgradeExperienceIndicators
```

---

## Windows Update for Business

```powershell
# WUfB usa GPO o Intune per controllare gli aggiornamenti
# I client scaricano da Microsoft Update (CDN), non da WSUS

# Vantaggi rispetto a WSUS:
# - Nessun server on-premise da gestire
# - Delivery Optimization peer-to-peer
# - Integrazione con Intune per gestione moderna
# - Sempre aggiornato, nessun catalogo da sincronizzare
# - Supporto nativo per safeguard holds (Microsoft blocca update problematici)

# Svantaggi rispetto a WSUS:
# - Nessun controllo granulare per KB singola
# - Non è possibile approvare/rifiutare singoli aggiornamenti
# - Richiede connettività Internet per ogni client
# - I client devono raggiungere gli endpoint Microsoft:
#   - *.windowsupdate.com
#   - *.delivery.mp.microsoft.com
#   - *.download.windowsupdate.com
#   - *.update.microsoft.com

# Configurazione via GPO:
# Computer → Administrative Templates → Windows Components → Windows Update
#   → Manage updates offered from Windows Update

# Deferral (ritardo installazione):
# - Quality Updates: ritardare fino a 30 giorni
# - Feature Updates: ritardare fino a 365 giorni

# Esempio: deploy graduale
# Ring 0 (IT): 0 giorni di deferral
# Ring 1 (Pilot): 7 giorni
# Ring 2 (Produzione): 14 giorni
# Ring 3 (Critico): 21 giorni

# Delivery Optimization
# Computer → Administrative Templates → Windows Components → Delivery Optimization
# - Download Mode: 2 (LAN) o 1 (Internet + LAN)
# - Risparmia banda scaricando da peer nella rete locale

# WUfB + WSUS coesistenza (Dual Scan):
# DEPRECATO da Windows 10 1803+
# Se si configura un WSUS server via GPO, il client usa SOLO WSUS
# Se si vuole WUfB: NON configurare "Specify intranet update service"
# Non è possibile usare entrambi sullo stesso client (scelta esclusiva)

# WUfB Reports (in Microsoft Entra / Intune):
# - Dashboard cloud per monitorare compliance
# - Richiede: Windows 10/11, dati diagnostici "Required" o superiore
# - Dati disponibili: stato aggiornamenti, errori, compliance per ring
```

---

## Intune Update Management

### Update Rings

```
INTUNE — UPDATE RINGS (Anelli di Aggiornamento)
────────────────────────────────────────────────

Gli Update Rings in Intune sono la versione cloud-managed delle GPO WUfB.
Permettono di configurare deferral, deadline, e comportamento di restart
per gruppi di dispositivi.

Configurazione: Intune Admin Center → Devices → Windows → Update rings

Parametri principali di un Update Ring:

┌─────────────────────────────────────────┬────────────────────────────────┐
│ Parametro                               │ Valori tipici                  │
├─────────────────────────────────────────┼────────────────────────────────┤
│ Quality update deferral                 │ 0-30 giorni                    │
│ Feature update deferral                 │ 0-365 giorni                   │
│ Automatic update behavior               │ Auto install at maintenance    │
│ Active hours start                       │ 08:00                         │
│ Active hours end                         │ 17:00                         │
│ Restart checks                           │ Allow (verifica prima restart)│
│ Quality update deadline                  │ 2-14 giorni                   │
│ Feature update deadline                  │ 2-30 giorni                   │
│ Grace period                             │ 0-7 giorni                    │
│ Auto reboot before deadline              │ Yes                           │
│ Option to pause quality updates          │ Enable (max 35 giorni)        │
│ Option to pause feature updates          │ Enable (max 35 giorni)        │
│ Uninstall feature update (days)          │ 10-60 giorni                  │
│ Uninstall quality update (days)          │ 7-60 giorni                   │
│ Enable pre-release builds                │ Not configured / Disabled     │
└─────────────────────────────────────────┴────────────────────────────────┘

Esempio di 4 ring in Intune:

Ring "Preview-IT":
  Assegnato a: gruppo "IT-Department"
  Quality deferral: 0 giorni
  Feature deferral: 0 giorni
  Deadline: 2 giorni
  Pre-release: Release Preview Channel (opzionale)

Ring "Pilot":
  Assegnato a: gruppo "Early-Adopters"
  Quality deferral: 3 giorni
  Feature deferral: 14 giorni
  Deadline: 3 giorni

Ring "Broad":
  Assegnato a: gruppo "All-Employees" (esclusi IT e Pilot)
  Quality deferral: 7 giorni
  Feature deferral: 60 giorni
  Deadline: 5 giorni

Ring "Critical-Systems":
  Assegnato a: gruppo "Mission-Critical"
  Quality deferral: 14 giorni
  Feature deferral: 120 giorni
  Deadline: 7 giorni
  Grace period: 2 giorni
```

### Feature Update Policies

```
INTUNE — FEATURE UPDATE POLICIES
─────────────────────────────────

Le Feature Update Policies permettono di "bloccare" un dispositivo
a una specifica versione di Windows e controllare quando riceve
la versione successiva.

Configurazione: Intune → Devices → Windows → Feature updates

Parametri:
- Feature update to deploy: selezionare la versione target
  Es. "Windows 11, version 24H2"
- Rollout options:
  - Make available as soon as possible
  - Make available on a specific date (data di inizio)
  - Gradual rollout: data inizio + data fine → Intune distribuisce
    automaticamente in modo graduale tra le due date

Caso d'uso tipico:
- Bloccare tutti i dispositivi su Windows 11 23H2
- Quando 24H2 è validato: creare una policy per 24H2
  con rollout graduale su 30 giorni
- I dispositivi riceveranno la nuova versione progressivamente

Safeguard Holds:
- Microsoft può bloccare il feature update su dispositivi con
  incompatibilità note
- Intune rispetta i safeguard hold per default
- NON disabilitare i safeguard hold in produzione
  (GPO: DisableWUfBSafeguards → NON abilitare)
```

### Expedited Updates

```
INTUNE — EXPEDITED QUALITY UPDATES
───────────────────────────────────

Le Expedited Updates bypassano i deferral configurati e forzano
l'installazione di un quality update specifico il prima possibile.

Caso d'uso: zero-day, vulnerabilità critica sfruttata attivamente

Configurazione: Intune → Devices → Windows → Quality updates → Create profile

Parametri:
- Expedite quality updates: selezionare il CU specifico da forzare
  Es. "2024-01 Cumulative Update (KB5034123)"
- Days until forced reboot: 1-3 giorni (dopo il download)
- Il dispositivo ignora il deferral configurato nell'Update Ring
- Il dispositivo scarica e installa il prima possibile
- L'utente riceve un countdown al reboot forzato

Limitazioni:
- Solo quality updates (non feature updates)
- Il dispositivo deve avere connettività Internet
- Richiede: Windows 10 20H2+ / Windows 11
- Richiede: dati diagnostici "Required" o superiore
- Il dispositivo deve essere registrato in WUfB Reports

Flusso:
1. Admin crea Expedited Update policy in Intune
2. Intune segnala al dispositivo di ignorare il deferral
3. Il dispositivo avvia immediatamente scan + download + install
4. Dopo il deadline: reboot forzato
5. Il dispositivo riporta compliance a Intune/WUfB Reports
```

### Driver Management via Intune

```
INTUNE — DRIVER MANAGEMENT
───────────────────────────

Intune supporta la gestione dei driver Windows Update
con approvazione manuale o automatica.

Configurazione: Intune → Devices → Windows → Driver updates

Funzionalità:
- Intune mostra i driver disponibili per i dispositivi gestiti
- L'admin può approvare o rifiutare singoli driver
- I driver approvati vengono distribuiti ai dispositivi

Policy di driver update:
- Automatic approval: Intune approva automaticamente i driver
  (con possibilità di impostare un deferral di N giorni)
- Manual approval: l'admin deve approvare ogni driver singolarmente
  (consigliato per ambienti critici)

Limitazioni:
- Solo driver pubblicati su Windows Update
- Non supporta driver custom del vendor (usare SCCM/app deployment)
- Richiede: Windows 10 20H2+ / Windows 11

Best practice:
- Usare Manual Approval per driver critici (GPU, storage, NIC)
- Usare un gruppo pilota per testare driver nuovi
- Monitorare i report per errori di installazione driver
- Escludere i driver da Windows Update via GPO per
  dispositivi gestiti interamente da Intune driver policies
```

---

## Patch Tuesday — Ciclo di Rilascio

```
PATCH TUESDAY — CALENDARIO E CICLO DI RILASCIO
───────────────────────────────────────────────

Il "Patch Tuesday" è il 2° martedì di ogni mese.
Microsoft rilascia gli aggiornamenti di sicurezza (B Release) in questa data.

CRONOLOGIA MENSILE TIPICA:
──────────────────────────

Giorno              │ Evento
────────────────────┼──────────────────────────────────────────────────
2° martedì (B)      │ Patch Tuesday: rilascio Security Updates (CU)
                    │ → Microsoft pubblica Security Update Guide
                    │ → CVE dettagliati con severity e exploitability
                    │ → MSRC blog post con highlights
2° mercoledì        │ Prime analisi della community (patch notes, known issues)
                    │ → Controllare: MSRC, Neowin, BleepingComputer,
                    │   Krebs on Security, PatchManagement.org
3° settimana        │ C Release (preview): non-security fixes preview
                    │ → Opzionale, per validazione pre-B del mese successivo
4° settimana        │ Eventuali Out-of-Band (OOB) se problemi critici nel CU
Fine mese           │ Preparazione per il prossimo ciclo

OUT-OF-BAND (OOB) UPDATES:
- Rilasciati fuori dal ciclo Patch Tuesday
- Motivi: bug critici nel CU, zero-day urgenti, problemi di stabilità
- Non hanno una schedulazione fissa
- Richiedono attenzione immediata se di sicurezza

ZERO-DAY RESPONSE:
- Microsoft può rilasciare patch di emergenza in qualsiasi momento
- Il MSRC (Microsoft Security Response Center) coordina
- Severity: se "Exploited = Yes" → patching immediato
- Se patch non disponibile: Microsoft pubblica mitigazione/workaround

RISORSE PER IL MONITORAGGIO:
- Microsoft Security Update Guide: https://msrc.microsoft.com/update-guide
- Microsoft Security Response Center Blog
- Windows Release Health: https://learn.microsoft.com/windows/release-health
- Known Issues: https://learn.microsoft.com/windows/release-health/status-windows-11-24H2
- KB article per ogni aggiornamento (dettagli fix, known issues, prerequisiti)

ESEMPIO TIMELINE REALE (mese tipo):
───────────────────────────────────
Martedì 14:   Microsoft rilascia KB5034123 (CU sicurezza)
Martedì 14:   Team IT scarica, legge CVE, valuta criticità
Mercoledì 15: Deploy su Ring 0 (lab/test) — test automatizzati
Giovedì 16:   Verifica Ring 0: nessuna regressione
Venerdì 17:   Deploy su Ring 1 (pilot, 10% utenti)
Lunedì 21:    Verifica Ring 1: 48h senza problemi
Mercoledì 23: Deploy su Ring 2 (produzione)
Lunedì 28:    Deploy su Ring 3 (mission-critical, fuori orario)
Venerdì 1°:   Report compliance — target 95%+
```

---

## Strategia di Patching Ring-Based

```
STRATEGIA RING-BASED — DEPLOY GRADUALE
───────────────────────────────────────

Il deploy graduale (ring-based) è il gold standard per il patch management.
Ogni ring ha un livello di rischio diverso e un tempo di validazione crescente.

RING 0 — TEST / LAB (Giorno 0-1)
─────────────────────────────────
Scopo: validazione tecnica iniziale
Dimensione: 5-10 macchine (VM di test, lab environment)
Target: rappresentativo dell'ambiente di produzione
Test:
  - Boot corretto dopo reboot
  - Servizi critici avviati
  - Applicazioni LOB funzionanti
  - Nessun BSOD / crash
  - Nessuna regressione di performance
  - Verifica Event Viewer per errori
Durata minima: 24 ore
Rollback: immediato (snapshot VM)
Automazione: test di smoke automatizzati se possibile

RING 1 — PILOT (Giorno 2-5)
────────────────────────────
Scopo: validazione con utenti reali in produzione
Dimensione: 5-10% degli utenti / server non critici
Target: early adopter volontari, team IT, dev environment
Test:
  - Tutto Ring 0 +
  - Workflow utente reale
  - Stampanti, VPN, Office 365
  - Applicazioni LOB in produzione
  - Performance sotto carico reale
  - Compatibilità driver hardware
Durata minima: 48-72 ore
Rollback: disinstallazione KB o restore da backup
Feedback: canale dedicato per segnalazioni pilot

RING 2 — BROAD / PRODUZIONE (Giorno 5-14)
──────────────────────────────────────────
Scopo: deploy alla maggior parte dell'organizzazione
Dimensione: 80% degli utenti / server non critici
Target: tutti gli utenti e server esclusi Ring 0, 1, 3
Deploy: schedulato fuori orario dove possibile
Monitoring:
  - Dashboard compliance (target: 95%+ in 7 giorni)
  - Ticket helpdesk per problemi correlati
  - Event Viewer centralizzato
  - Performance baselines
Rollback: pianificato, richiede approvazione change management

RING 3 — MISSION-CRITICAL (Giorno 14-21)
─────────────────────────────────────────
Scopo: patching dei sistemi più critici
Dimensione: 5-10% (Domain Controller, database, ERP, SCADA)
Target: sistemi il cui downtime ha impatto business significativo
Prerequisiti:
  - Ring 0, 1, 2 completati senza problemi
  - Change Request approvato
  - Backup/snapshot completato
  - Finestra di manutenzione concordata
  - Team di rollback in standby
  - Piano di comunicazione attivato
Deploy: fuori orario lavorativo, con presidio
Post-deploy: verifica manuale di tutti i servizi critici
Rollback: restore da snapshot/backup, con SLA definito

ECCEZIONE: EMERGENCY PATCH (Zero-Day)
──────────────────────────────────────
Trigger: CVE con "Exploited = Yes" o CVSS ≥ 9.0
Processo: skip ring, deploy accelerato
  1. Valutazione impatto (1-2 ore)
  2. Test minimo su Ring 0 (2-4 ore)
  3. Deploy su tutti i ring simultaneamente
  4. Monitoraggio intensivo post-deploy
  5. Rollback ready
Approvazione: CISO o delegato deve approvare
Documentazione: obbligatoria post-incidente
```

### Metodologia di Testing

```
TESTING METHODOLOGY — VALIDAZIONE PATCH
────────────────────────────────────────

Test automatizzati (Ring 0):
1. Boot test: la macchina si avvia correttamente?
2. Service test: tutti i servizi critici sono Running?
3. Network test: connettività LAN/WAN/DNS funziona?
4. App test: le applicazioni LOB rispondono?
5. Auth test: login dominio funziona?

# Script di validazione post-patch (esempio)
$tests = @(
    @{ Name = "Boot Time";      Test = { (Get-CimInstance Win32_OperatingSystem).LastBootUpTime } }
    @{ Name = "DNS Resolution"; Test = { Resolve-DnsName "dc01.contoso.com" -ErrorAction Stop } }
    @{ Name = "AD Auth";        Test = { Test-ComputerSecureChannel } }
    @{ Name = "BITS Service";   Test = { (Get-Service BITS).Status -eq 'Running' } }
    @{ Name = "WinRM";          Test = { Test-WSMan -ErrorAction Stop } }
    @{ Name = "Event Errors";   Test = {
        $errors = Get-WinEvent -FilterHashtable @{
            LogName = 'System'; Level = 1,2; StartTime = (Get-Date).AddHours(-2)
        } -ErrorAction SilentlyContinue
        $errors.Count -lt 5  # meno di 5 errori critici nelle ultime 2 ore
    }}
)

foreach ($t in $tests) {
    try {
        $result = & $t.Test
        Write-Host "[PASS] $($t.Name)" -ForegroundColor Green
    } catch {
        Write-Host "[FAIL] $($t.Name): $_" -ForegroundColor Red
    }
}

Test manuali (Ring 1):
1. Login utente e caricamento profilo
2. Apertura applicazioni LOB principali
3. Stampa su stampanti di rete
4. Connessione VPN
5. Accesso file share e SharePoint
6. Invio/ricezione email
7. Funzionalità specifiche del dipartimento
```

---

## SCCM/MECM Patching

### Software Update Points (SUP)

```
SCCM/MECM — SOFTWARE UPDATE POINT (SUP)
────────────────────────────────────────

Il SUP è il ruolo di SCCM che si interfaccia con WSUS per la gestione
degli aggiornamenti. SCCM NON sostituisce WSUS: lo usa come motore
di scansione sottostante.

Architettura:

  [Microsoft Update CDN]
           │
           ▼
  ┌─────────────────────┐
  │  WSUS (sottostante)  │ ← Installato sul site server o su server dedicato
  │  Gestito da SCCM     │    SCCM configura WSUS automaticamente
  └──────────┬───────────┘
             │
  ┌──────────┴───────────┐
  │  SCCM Site Server     │
  │  + SUP Role           │ ← Sincronizza metadata da WSUS
  │  + SMS Provider        │    Crea deployment packages
  │  + Site Database       │    Gestisce compliance reporting
  └──────────┬───────────┘
             │
      ┌──────┴──────┐
      ▼             ▼
  ┌──────────┐  ┌──────────┐
  │ SCCM     │  │ SCCM     │  Distribution Points
  │ DP #1    │  │ DP #2    │  (ospitano i content dei pacchetti)
  └──────────┘  └──────────┘

Installazione SUP:
1. Installare WSUS sul server (feature Windows Server)
2. NON configurare WSUS manualmente (SCCM lo fa)
3. In SCCM Console: Administration → Site Configuration → Sites
4. Selezionare il site → Add Site System Roles → Software Update Point
5. Configurare:
   - Prodotti da sincronizzare
   - Classificazioni
   - Sync schedule (consigliato: 1 volta/giorno)
   - Lingue

Sincronizzazione:
- SCCM sincronizza i metadata da WSUS nel site database
- I client SCCM usano il SUP locale per la scansione
- Il SUP restituisce la lista degli aggiornamenti applicabili
- SCCM confronta con le Software Update Groups per determinare compliance
```

### Deployment Packages

```
SCCM/MECM — DEPLOYMENT PACKAGES E ADR
──────────────────────────────────────

Software Update Group (SUG):
- Raggruppamento logico di aggiornamenti
- Es. "2024-01 Security Updates", "Critical .NET Updates"
- Associato a un Deployment Package (pacchetto di contenuti)

Deployment Package:
- Contenitore fisico dei file di aggiornamento (.cab, .msu)
- Distribuito ai Distribution Points (DP)
- Dimensione tipica: 1-10 GB per ciclo mensile
- Best practice: un package per mese, non accumulare

Automatic Deployment Rule (ADR):
- Automatizza l'intero processo: scarica → crea SUG → crea deployment
- Trigger: nuovi aggiornamenti disponibili dopo sincronizzazione
- Configurazione ADR tipica:
  1. Filtri: classificazione (Security, Critical), prodotto (Windows 11, Server 2022)
  2. Valutazione: schedule di compliance check
  3. Deployment: collection target, deadline, maintenance window
  4. Download: cartella temporanea, distribuzione ai DP
  5. SUG: nome (con variabile mese/anno), massimo aggiornamenti

Esempio ADR "Monthly Security Updates":
  Filtro: Classification = "Security Updates", "Critical Updates"
          Product = "Windows 11", "Windows Server 2022"
          Released = Last 1 month
  Collection: "All Windows Workstations"
  Available: immediately
  Deadline: 7 days from available
  Maintenance window: required for install
  SUG name: "%MonthName% %Year% - Security Updates"

Phased Deployment:
- SCCM supporta deployment in fasi (simile ai ring)
- Fase 1: Collection "Pilot" → deadline 3 giorni
- Fase 2: Collection "Production" → automatica dopo successo Fase 1
  con soglia di successo (es. 95% compliance in Fase 1)
```

### Maintenance Windows SCCM

```
SCCM/MECM — MAINTENANCE WINDOWS
────────────────────────────────

Le maintenance windows di SCCM definiscono QUANDO un client può
installare aggiornamenti e/o eseguire reboot.

Tipi di maintenance window:
1. All Deployments: si applica a tutto (software, updates, task sequences)
2. Software Updates: solo per aggiornamenti software
3. Task Sequences: solo per task sequences

Configurazione:
- SCCM Console → Assets and Compliance → Device Collections
- Selezionare collection → Properties → Maintenance Windows → Add

Esempio per server:
  Nome: "Monthly Patching Window - Domenica notte"
  Schedule: ogni 2° domenica del mese
  Inizio: 02:00, Durata: 4 ore (02:00-06:00)
  Tipo: Software Updates

Esempio per workstation:
  Nome: "Daily Update Window"
  Schedule: ogni giorno
  Inizio: 12:00, Durata: 2 ore (12:00-14:00)
  Tipo: Software Updates

Regole:
- Se nessuna maintenance window è configurata: gli aggiornamenti
  possono installarsi in qualsiasi momento
- Se una maintenance window è configurata: gli aggiornamenti
  si installano SOLO durante la finestra
- Se la finestra scade durante l'installazione: l'installazione
  continua fino al completamento
- Reboot: solo durante la maintenance window (a meno che
  "Override" non sia abilitato nel deployment)

Override maintenance window:
- Nel deployment si può selezionare:
  "System restart can be performed outside maintenance windows"
  → Se il reboot è critico, viene eseguito anche fuori finestra
```

### Compliance Reporting SCCM

```powershell
# SCCM offre reporting avanzato tramite SQL Reporting Services (SSRS)

# Report built-in per software updates:
# - Compliance 1 - Overall compliance
# - Compliance 2 - Specific software update
# - Compliance 3 - Software update group
# - Compliance 5 - Specific computer
# - Compliance 8 - Computers in non-compliant state
# - Management 1 - Updates in a deployment
# - Scan 1 - Last scan states by collection
# - Troubleshooting 1 - Scan errors

# Query WMI per verifica compliance da client:
# (eseguire sul client SCCM)
Get-WmiObject -Namespace "root\ccm\clientsdk" -Class CCM_SoftwareUpdate |
    Select-Object Name, ArticleID, ComplianceState, EvaluationState |
    Format-Table -AutoSize

# ComplianceState:
# 0 = Detected (necessario)
# 1 = Not Required
# 2 = Installed (compliant)

# EvaluationState:
# 0 = None
# 1 = Available
# 2 = Submitted
# 3 = Detecting
# 4 = PreDownload
# 5 = Downloading
# 6 = WaitInstall
# 7 = Installing
# 8 = PendingSoftReboot
# 9 = PendingHardReboot
# 10 = WaitReboot
# 11 = Verifying
# 12 = InstallComplete
# 13 = Error

# Forzare ciclo di valutazione aggiornamenti sul client:
Invoke-WmiMethod -Namespace "root\ccm" -Class SMS_Client `
    -Name TriggerSchedule -ArgumentList "{00000000-0000-0000-0000-000000000113}"
# {00000000-0000-0000-0000-000000000108} = Software Updates Scan
# {00000000-0000-0000-0000-000000000113} = Software Updates Deployment Evaluation
```

---

## Gestione Patch Enterprise

### Processo di Patch Management

```
CICLO MENSILE (Patch Tuesday = secondo martedì del mese)

Settimana 1 (Martedì-Venerdì):
├── Microsoft rilascia patch
├── Team IT scarica e analizza le patch
├── Verifica CVE critici e applicabilità
└── Deploy su Ring 0 (Test/Lab)

Settimana 2:
├── Verificare Ring 0: problemi? regressioni?
├── Se OK → Deploy su Ring 1 (Pilot: 10% utenti/server non critici)
└── Monitorare Event Viewer, performance, servizi

Settimana 3:
├── Verificare Ring 1: problemi?
├── Se OK → Deploy su Ring 2 (Produzione: server e workstation)
└── Escludere: server critici in periodo di picco, sistemi legacy

Settimana 4:
├── Deploy su Ring 3 (Critici: DC, DB, server mission-critical)
├── Fuori orario lavorativo con finestra di manutenzione
├── Verifica post-deploy
└── Report compliance

EMERGENZA (Zero-Day / CVE critico):
├── Valutazione immediata dell'impatto
├── Se sfruttato attivamente → deploy accelerato (skip Ring)
├── Se mitigazione possibile → applicare mitigazione, poi patching normale
└── Documentare decisione e approvazione
```

### Report Compliance

```powershell
# Report computer con patch mancanti
$wsus = Get-WsusServer
$scope = New-Object Microsoft.UpdateServices.Administration.ComputerTargetScope
$scope.IncludedInstallationStates = [Microsoft.UpdateServices.Administration.UpdateInstallationStates]::NotInstalled

$wsus.GetComputerTargets($scope) | ForEach-Object {
    [PSCustomObject]@{
        Computer = $_.FullDomainName
        NeededUpdates = $_.GetUpdateInstallationInfoPerUpdate($scope).Count
        LastContact = $_.LastReportedStatusTime
    }
} | Export-Csv "C:\Reports\PatchCompliance.csv" -NoTypeInformation

# PowerShell remoto per verifica rapida
Invoke-Command -ComputerName SRV01, SRV02 -ScriptBlock {
    Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 5
}

# Report compliance percentuale per gruppo WSUS
$wsus.GetComputerTargetGroups() | ForEach-Object {
    $groupScope = New-Object Microsoft.UpdateServices.Administration.ComputerTargetScope
    $groupScope.ComputerTargetGroups.Add($_)
    $computers = $wsus.GetComputerTargets($groupScope)
    $totalNeeded = 0
    $totalInstalled = 0
    foreach ($pc in $computers) {
        $info = $pc.GetUpdateInstallationInfoPerUpdate()
        $totalInstalled += ($info | Where-Object {
            $_.UpdateInstallationState -eq 'Installed' }).Count
        $totalNeeded += ($info | Where-Object {
            $_.UpdateInstallationState -eq 'NotInstalled' }).Count
    }
    $total = $totalInstalled + $totalNeeded
    $pct = if ($total -gt 0) { [math]::Round(($totalInstalled / $total) * 100, 1) } else { 100 }
    [PSCustomObject]@{
        Gruppo     = $_.Name
        Computer   = $computers.Count
        Installati = $totalInstalled
        Mancanti   = $totalNeeded
        Compliance = "$pct%"
    }
}
```

---

## Third-Party Patching

```
THIRD-PARTY PATCHING — STRUMENTI E STRATEGIA
─────────────────────────────────────────────

Windows Update e WSUS gestiscono solo prodotti Microsoft.
Le applicazioni di terze parti (Adobe, Java, Chrome, Firefox, 7-Zip, etc.)
richiedono strumenti dedicati.

STRUMENTI PRINCIPALI:
─────────────────────

1. SCUP (System Center Updates Publisher)
   - Gratuito, integrato con SCCM
   - Permette di importare cataloghi di aggiornamenti terze parti
   - Pubblica gli aggiornamenti nel WSUS usato da SCCM
   - Limitazioni: richiede cataloghi forniti dal vendor
   - Complessità: medio-alta (configurazione certificati, cataloghi)

2. Patch My PC
   - Commerciale, integrazione nativa con SCCM e Intune
   - Supporta 900+ applicazioni terze parti
   - Automatizza: download → creazione pacchetto → deployment
   - Funzionalità:
     - Auto-publishing in WSUS/SCCM
     - Intune app packaging (Win32 app / Microsoft Store)
     - Vulnerability scanning
     - Compliance reporting
   - Consigliato per ambienti SCCM/Intune enterprise

3. PDQ Deploy + PDQ Inventory
   - Commerciale, standalone (non richiede SCCM)
   - Ideale per PMI senza SCCM
   - PDQ Deploy: distribuzione software e patch
   - PDQ Inventory: scansione e reporting
   - Pre-built packages per applicazioni comuni
   - Scheduling e targeting per gruppi AD

4. ManageEngine Patch Manager Plus
   - Commerciale, standalone
   - Supporta Windows, macOS, Linux
   - Catalogo aggiornamenti terze parti ampio
   - Reporting e compliance dashboard

5. Ivanti Patch Management (ex Shavlik)
   - Enterprise-grade, agentless e agent-based
   - Catalogo molto ampio
   - Integrazione con ITSM tools

STRATEGIA THIRD-PARTY PATCHING:
───────────────────────────────
1. Inventariare TUTTE le applicazioni installate
   → PDQ Inventory, SCCM Software Inventory, o script PowerShell
2. Classificare per rischio:
   - Alto: browser, Java, Adobe Reader, Office plugins
   - Medio: utility, tool di sviluppo
   - Basso: applicazioni interne, tool raramente esposti
3. Definire frequenza di patching:
   - Alto rischio: entro 7 giorni dal rilascio
   - Medio rischio: entro 14 giorni
   - Basso rischio: ciclo mensile
4. Automatizzare dove possibile:
   - Cataloghi automatici (Patch My PC, SCUP)
   - Auto-update nativo dell'applicazione (Chrome, Firefox)
   - Deployment automatico per app a basso rischio
5. Monitorare compliance:
   - Dashboard con versioni installate vs. ultime disponibili
   - Alert per applicazioni con CVE noti e non patchate

# Script inventario applicazioni installate (baseline)
Get-CimInstance Win32_Product |
    Select-Object Name, Version, Vendor, InstallDate |
    Sort-Object Name |
    Export-Csv "C:\Reports\InstalledSoftware.csv" -NoTypeInformation

# Alternativa più rapida (registry-based, non usa Win32_Product):
$paths = @(
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
    "HKLM:\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
)
Get-ItemProperty $paths -ErrorAction SilentlyContinue |
    Where-Object { $_.DisplayName } |
    Select-Object DisplayName, DisplayVersion, Publisher, InstallDate |
    Sort-Object DisplayName |
    Export-Csv "C:\Reports\InstalledApps.csv" -NoTypeInformation
```

---

## Hotpatching

```
HOTPATCHING — AGGIORNAMENTI SENZA REBOOT
────────────────────────────────────────

L'hotpatching è la capacità di applicare aggiornamenti di sicurezza
al sistema operativo SENZA richiedere un reboot.

WINDOWS SERVER HOTPATCHING (via Azure Arc):
───────────────────────────────────────────

Disponibilità:
- Windows Server 2022 Datacenter: Azure Edition (VM Azure)
- Windows Server 2022/2025: on-premise con Azure Arc (preview/GA)
- Richiede: connessione ad Azure Arc, licenza appropriata

Come funziona:
1. L'hotpatch modifica il codice in memoria (in-memory patching)
2. I processi in esecuzione vengono aggiornati senza restart
3. Solo le patch di sicurezza che non richiedono modifiche al kernel
   possono essere distribuite come hotpatch
4. Ciclo trimestrale di "baseline" con reboot:
   - Gennaio, Aprile, Luglio, Ottobre: CU completo (richiede reboot)
   - Tutti gli altri mesi: hotpatch (nessun reboot)

Ciclo annuale con hotpatching:
  Gen: Baseline (reboot) ← CU completo
  Feb: Hotpatch (no reboot)
  Mar: Hotpatch (no reboot)
  Apr: Baseline (reboot) ← CU completo
  Mag: Hotpatch (no reboot)
  Giu: Hotpatch (no reboot)
  Lug: Baseline (reboot) ← CU completo
  Ago: Hotpatch (no reboot)
  Set: Hotpatch (no reboot)
  Ott: Baseline (reboot) ← CU completo
  Nov: Hotpatch (no reboot)
  Dic: Hotpatch (no reboot)

Benefici:
- Riduzione del 75% dei reboot annuali (4 reboot vs. 12)
- Minore downtime pianificato
- Minori finestre di manutenzione
- Sicurezza migliorata: le patch vengono applicate prima
  (nessuna attesa per la finestra di reboot)
- Ideale per server mission-critical con SLA elevati

Limitazioni:
- Non tutte le patch possono essere hotpatch
  (kernel changes, driver updates richiedono sempre reboot)
- Richiede Azure Arc enrollment
- Costo: incluso in Azure Edition, o licenza aggiuntiva per Arc on-premise
- Non disponibile per Windows client (solo Server)

Configurazione (Azure Arc):
1. Installare Azure Connected Machine Agent sul server on-premise
2. Registrare il server in Azure Arc
3. Abilitare Update Management via Azure Arc
4. Configurare hotpatch schedule policy
5. Azure gestisce automaticamente il ciclo baseline/hotpatch
```

---

## Update Compliance e Reporting

```
UPDATE COMPLIANCE — MONITORAGGIO E DASHBOARD
─────────────────────────────────────────────

Strumenti Microsoft per monitorare lo stato degli aggiornamenti:

1. WINDOWS UPDATE FOR BUSINESS REPORTS (ex Update Compliance)
───────────────────────────────────────────────────────────
- Soluzione cloud basata su Azure Monitor / Log Analytics
- Richiede: Windows 10/11, dati diagnostici "Required"+
- Mostra: stato aggiornamenti, errori, compliance per ring
- Gratuito (incluso nella licenza Windows E3/E5)

Configurazione:
  a. Creare workspace Log Analytics in Azure
  b. Configurare diagnostic data collection via GPO o Intune
  c. Collegare il workspace a WUfB Reports in Intune
  d. Attendere 24-48 ore per la popolazione iniziale dei dati

Dashboard disponibili:
  - Quality Updates status: quanti dispositivi compliant/non-compliant
  - Feature Updates status: progresso del rollout
  - Driver Updates: stato driver
  - Expedited Updates: stato delle patch accelerate
  - Device alerts: errori di installazione per dispositivo

Query KQL di esempio (Log Analytics):
  // Dispositivi con quality updates mancanti
  UCClient
  | where TimeGenerated > ago(7d)
  | where OSVersion == "10.0.22631"  // Windows 11 23H2
  | summarize arg_max(TimeGenerated, *) by DeviceName
  | where QualityUpdateAge > 30      // più di 30 giorni dall'ultimo CU
  | project DeviceName, OSVersion, QualityUpdateAge, LastScanTime

2. WSUS BUILT-IN REPORTS
─────────────────────────
- Console WSUS → Reports
- Report disponibili:
  - Update Status Summary
  - Update Detailed Status
  - Computer Status Summary
  - Computer Detailed Status
  - Synchronization Results
- Esportabili in PDF o XLS via SSRS (se configurato)

3. SCCM/MECM REPORTING
───────────────────────
- Report SSRS integrati (>200 report predefiniti)
- Personalizzabili con query SQL custom
- Dashboard nel SCCM Console (Monitoring → Overview → Software Updates)
- Power BI integration per dashboard avanzati

4. MICROSOFT DEFENDER VULNERABILITY MANAGEMENT
───────────────────────────────────────────────
- Integrato in Microsoft 365 Defender
- Mostra software non patchato con CVE associati
- Prioritizzazione basata su exploit attivi e esposizione
- Raccomandazioni di remediation
- Integrato con Intune per azioni automatiche
```

---

## Driver Management

```
DRIVER MANAGEMENT — GESTIONE AVANZATA
──────────────────────────────────────

DRIVER STORE (C:\Windows\System32\DriverStore)
──────────────────────────────────────────────
Il DriverStore è il repository locale dei driver.
Contiene tutti i driver (in-box e terze parti) disponibili per l'installazione.

Struttura:
  C:\Windows\System32\DriverStore\
  ├── FileRepository\       ← Driver installati (staging area)
  │   ├── driver1.inf_amd64_hash\
  │   ├── driver2.inf_amd64_hash\
  │   └── ...
  └── en-US\ (localizzazione)

# Elencare driver nel DriverStore
pnputil /enum-drivers

# Informazioni dettagliate su tutti i driver di terze parti
pnputil /enum-drivers /class "Net"   # solo driver di rete

# Aggiungere un driver al DriverStore (staging)
pnputil /add-driver C:\Drivers\mydriver.inf /install

# Aggiungere tutti i driver da una cartella (ricorsivo)
pnputil /add-driver C:\Drivers\*.inf /subdirs /install

# Rimuovere un driver dal DriverStore
pnputil /delete-driver oem42.inf /force

# Esportare driver installati (backup)
Export-WindowsDriver -Online -Destination "D:\DriverBackup"

# Verificare driver problematici
Get-WmiObject Win32_PnPSignedDriver |
    Where-Object { $_.IsSigned -eq $false } |
    Select-Object DeviceName, DriverVersion, InfName

PNP (PLUG AND PLAY) E DRIVER RANKING
─────────────────────────────────────
Quando Windows rileva un dispositivo, il PnP manager:
1. Cerca driver compatibili nel DriverStore
2. Se nessuno trovato: cerca su Windows Update (se non bloccato via GPO)
3. Classifica i driver candidati per:
   - Firma: Microsoft-signed > WHQL > self-signed > unsigned
   - Versione: più recente vince (a parità di firma)
   - Feature score: compatibilità hardware
4. Installa il driver con il ranking migliore

ESCLUSIONE DRIVER DA WINDOWS UPDATE
────────────────────────────────────
In ambienti enterprise, spesso si vuole impedire a WU di installare
driver non testati.

# GPO: Do not include drivers with Windows Updates
# Computer → Administrative Templates → Windows Components → Windows Update
#   → Manage updates offered from Windows Update
#   → "Do not include drivers with Windows Updates" = Enabled

# Registry equivalente:
# HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate
# ExcludeWUDriversInQualityUpdate = 1

# Per WSUS: non selezionare la classificazione "Driver Updates"
# nei prodotti sincronizzati

# Per Intune: configurare nell'Update Ring:
# "Windows Driver Updates" = Block

DRIVER STAGING PER DEPLOYMENT
─────────────────────────────
Per deployment OSD (SCCM/MDT) o provisioning:
1. Estrarre driver dal vendor (Dell Command, HP SoftPaq, Lenovo SCCM Pack)
2. Organizzare per modello: \\server\drivers\Dell\Latitude-5540\
3. Importare in SCCM Driver Package o MDT Out-of-Box Drivers
4. Associare al task sequence per modello hardware
5. PnPutil inietta i driver durante l'installazione OS

# Identificare modello hardware per download driver corretto
Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer, Model
Get-CimInstance Win32_BIOS | Select-Object SMBIOSBIOSVersion, SerialNumber

# Verificare driver caricati e problematici
Get-WmiObject Win32_PnPEntity | Where-Object { $_.Status -ne "OK" } |
    Select-Object Name, DeviceID, Status, ConfigManagerErrorCode
# ConfigManagerErrorCode:
# 1 = non configurato correttamente
# 10 = impossibile avviare il dispositivo
# 22 = disabilitato
# 28 = driver non installato
# 31 = impossibile caricare i driver
```

---

## Rollback Aggiornamenti

```powershell
# DISINSTALLARE AGGIORNAMENTO
# Windows Update (KB specifico)
wusa /uninstall /kb:5001234 /quiet /norestart

# PowerShell
Get-HotFix -Id KB5001234
# Se presente:
Remove-WindowsPackage -Online -PackageName (
    Get-WindowsPackage -Online |
    Where-Object PackageName -like "*KB5001234*"
).PackageName

# Elencare aggiornamenti disinstallabili
Get-WindowsPackage -Online | Where-Object {
    $_.PackageState -eq "Installed" -and $_.ReleaseType -eq "Update"
} | Select-Object PackageName, InstallTime

# FEATURE UPDATE ROLLBACK (solo Windows client, entro 10 giorni)
# Settings → Recovery → Go back to previous version
# O da WinRE → Troubleshoot → Advanced → Go back to previous build

# Estendere periodo di rollback (da 10 a 30 giorni):
DISM /Online /Set-OSUninstallWindow /Value:30

# Verificare se il rollback è ancora disponibile:
DISM /Online /Get-OSUninstallWindow

# SERVER: Rollback via snapshot VM
# PRIMA di ogni patch cycle: creare checkpoint Hyper-V
Checkpoint-VM -Name "SRV-PROD" -SnapshotName "Pre-Patch-$(Get-Date -Format yyyyMMdd)"

# Se problemi dopo patching:
Restore-VMCheckpoint -VMName "SRV-PROD" -Name "Pre-Patch-20240109" -Confirm:$false
Start-VM "SRV-PROD"

# DISM per riparazioni
DISM /Online /Cleanup-Image /CheckHealth
DISM /Online /Cleanup-Image /ScanHealth
DISM /Online /Cleanup-Image /RestoreHealth

# SFC per file di sistema
sfc /scannow

# Rollback cumulative update via DISM (offline, da WinRE):
# Quando il sistema non si avvia dopo un aggiornamento
# Boot in WinRE → Command Prompt:
DISM /Image:C:\ /Get-Packages | findstr "KB"
DISM /Image:C:\ /Remove-Package /PackageName:"Package_for_KB5034123~31bf..."

# Rollback via Safe Mode:
# 1. Boot in Safe Mode (F8 o msconfig)
# 2. wusa /uninstall /kb:5034123 /quiet
# 3. Reboot normale

# Bloccare reinstallazione di un aggiornamento problematico:
# Usare "Show or Hide Updates" troubleshooter (wushowhide.diagcab)
# O via GPO/WSUS: rifiutare l'aggiornamento specifico
```

---

## Best Practices

```
BEST PRACTICES — PATCH MANAGEMENT ENTERPRISE
─────────────────────────────────────────────

1. MAI PATCHARE TUTTO INSIEME
   Deploy graduale con ring di test (Lab → Pilot → Produzione → Critico)
   Ogni ring ha un tempo di stabilizzazione minimo prima di procedere

2. SNAPSHOT PRIMA DI PATCHARE SERVER
   Su VM: creare checkpoint Hyper-V / VMware snapshot
   Su fisici: System State backup via Windows Server Backup
   Su cloud: snapshot del disco / immagine VM

3. FINESTRA DI MANUTENZIONE DEFINITA
   Comunicata e concordata con il business
   Documentata nel CMDB / change management system
   Con tempo sufficiente per installazione + verifica + eventuale rollback

4. WSUS CLEANUP MENSILE
   Invoke-WsusServerCleanup per mantenere performance
   Reindex database trimestralmente
   Monitorare spazio disco content directory

5. MONITORARE COMPLIANCE
   Report settimanale sullo stato delle patch
   Target: 95%+ compliance entro 30 giorni dal rilascio
   Escalation automatica per dispositivi non conformi dopo 45 giorni

6. PATCH FUORI BANDA (ZERO-DAY)
   Avere un processo accelerato documentato e approvato
   Identificare chi ha autorità di approvare skip-ring
   Testare il processo almeno 1 volta all'anno (drill)

7. DOCUMENTARE ECCEZIONI
   Se un server non può essere patchato: documentare motivo,
   mitigazione applicata, data prevista per il patching, risk owner

8. SEPARARE DRIVER DA OS UPDATES
   Gestire i driver separatamente dagli aggiornamenti OS
   Escludere driver da WU via GPO in ambienti enterprise
   Testare driver in laboratorio prima del deploy

9. AUTOMATIZZARE DOVE POSSIBILE
   ADR in SCCM per deployment automatico
   Auto-approval per Definition Updates
   Script di validazione post-patch

10. COMUNICAZIONE
    Notificare gli utenti prima delle maintenance window
    Fornire canale di escalation per problemi post-patch
    Post-mortem per patch che causano problemi

11. BACKUP E DISASTER RECOVERY
    Verificare che i backup siano aggiornati prima del patching
    Testare il processo di restore regolarmente
    Piano di DR specifico per "patch gone wrong"

12. LIFECYCLE MANAGEMENT
    Non patchare sistemi fuori supporto (EOL) — pianificare la migrazione
    Monitorare le date di fine supporto per ogni OS version
    Budget per upgrade hardware/OS che non possono più essere patchati

13. TESTING THIRD-PARTY
    Le applicazioni di terze parti richiedono la stessa disciplina
    delle patch Microsoft. Inventariare, classificare, automatizzare.

14. METRICHE E KPI
    Tracciare: MTTR (Mean Time To Remediate), compliance %, eccezioni,
    patch failure rate, reboot compliance
```

---

## Troubleshooting

### Errori Windows Update comuni

**"Windows Update fallisce con errore 0x8024..."** → `DISM /Online /Cleanup-Image /RestoreHealth` poi `sfc /scannow`. Verificare connettività al server WSUS. Reset componenti WU: fermare servizi `wuauserv`, `cryptSvc`, `bits`, `msiserver`, rinominare `SoftwareDistribution` e `catroot2`, riavviare servizi.

**"WSUS console lenta o non risponde"** → IIS Application Pool WsusPool: aumentare Private Memory Limit, verificare RAM server. Eseguire cleanup e reindex database. Verificare spazio disco.

**"Computer non appare in WSUS"** → Verificare GPO applicata (`gpresult /r`), verificare connettività (`Test-NetConnection wsus-server -Port 8530`), forzare detection (`wuauclt /detectnow` o `usoclient StartScan`), verificare log `C:\Windows\WindowsUpdate.log` o `Get-WindowsUpdateLog`.

**"Aggiornamento causa BSOD"** → Boot in Safe Mode, disinstallare con `wusa /uninstall /kb:NNNNNNN`. Se non si avvia: WinRE → Command Prompt → `DISM /Image:C:\ /Remove-Package /PackageName:...`. Documentare e reportare a Microsoft.

### Problemi aggiuntivi e soluzioni

```
PROBLEMA 1: Windows Update bloccato su "Checking for updates" o "Downloading 0%"
────────────────────────────────────────────────────────────────────────────────
Causa: corruzione del datastore WUA, cache corrotta, o problemi di rete

Soluzione — Reset completo componenti Windows Update:
```

```powershell
# Script reset completo Windows Update
# Eseguire come Administrator

# 1. Fermare i servizi
Stop-Service wuauserv -Force
Stop-Service cryptSvc -Force
Stop-Service bits -Force
Stop-Service msiserver -Force

# 2. Rinominare le cartelle di cache
Rename-Item "C:\Windows\SoftwareDistribution" "C:\Windows\SoftwareDistribution.bak" -Force
Rename-Item "C:\Windows\System32\catroot2" "C:\Windows\System32\catroot2.bak" -Force

# 3. Riavviare i servizi
Start-Service bits
Start-Service cryptSvc
Start-Service msiserver
Start-Service wuauserv

# 4. Forzare nuova scansione
usoclient StartScan

# 5. Se funziona, eliminare le cartelle .bak dopo qualche giorno
# Remove-Item "C:\Windows\SoftwareDistribution.bak" -Recurse -Force
# Remove-Item "C:\Windows\System32\catroot2.bak" -Recurse -Force
```

```
PROBLEMA 2: Errore 0x80073712 — File CBS danneggiato
─────────────────────────────────────────────────────
Causa: Component-Based Servicing store corrotto

Soluzione:
```

```powershell
# Riparare il CBS store
DISM /Online /Cleanup-Image /CheckHealth
# Se riporta "repairable":
DISM /Online /Cleanup-Image /RestoreHealth
# Poi:
sfc /scannow

# Se DISM fallisce con errore source (no Internet o WSUS non ha il payload):
# Usare un'immagine ISO di Windows come sorgente:
DISM /Online /Cleanup-Image /RestoreHealth /Source:D:\sources\install.wim /LimitAccess
```

```
PROBLEMA 3: Spazio disco insufficiente per gli aggiornamenti
────────────────────────────────────────────────────────────
Causa: disco C: pieno, WinSxS troppo grande

Soluzione:
```

```powershell
# Verificare spazio disco
Get-PSDrive C | Select-Object Used, Free, @{N='FreeGB'; E={[math]::Round($_.Free/1GB,2)}}

# Pulizia WinSxS (component store)
DISM /Online /Cleanup-Image /StartComponentCleanup /ResetBase
# ATTENZIONE: /ResetBase rimuove TUTTE le versioni precedenti dei componenti
# Non sarà più possibile disinstallare aggiornamenti precedenti

# Pulizia generale
cleanmgr /d C: /VERYLOWDISK   # Disk Cleanup in modalità aggressiva

# Rimuovere versioni precedenti di Windows (post feature update)
DISM /Online /Cleanup-Image /StartComponentCleanup /ResetBase

# Comprimere binari OS (estremo, solo se necessario)
Compact /CompactOS:always

# Verificare dimensione WinSxS (la dimensione reale è inferiore
# a quella mostrata da Explorer a causa degli hard link)
DISM /Online /Cleanup-Image /AnalyzeComponentStore
```

```
PROBLEMA 4: WSUS sincronizzazione fallisce
──────────────────────────────────────────
Causa: connettività Internet, proxy, certificati SSL, timeout

Soluzione:
```

```powershell
# Verificare log sincronizzazione WSUS
$wsus = Get-WsusServer
$lastSync = $wsus.GetSubscription().GetLastSynchronizationInfo()
Write-Host "Ultimo tentativo: $($lastSync.StartTime)"
Write-Host "Risultato: $($lastSync.Result)"
Write-Host "Errore: $($lastSync.Error)"
Write-Host "Errori per categoria: $($lastSync.ErrorDetails)"

# Verificare connettività verso Microsoft Update
$endpoints = @(
    "windowsupdate.microsoft.com",
    "download.windowsupdate.com",
    "update.microsoft.com",
    "download.microsoft.com"
)
foreach ($ep in $endpoints) {
    $test = Test-NetConnection -ComputerName $ep -Port 443
    Write-Host "$ep : $($test.TcpTestSucceeded)"
}

# Se c'è un proxy:
# Configurare proxy per WSUS:
netsh winhttp show proxy
# Se necessario:
netsh winhttp set proxy proxy-server="http://proxy:8080" bypass-list="*.local"
# O nel contesto del servizio WSUS:
# Configurare proxy nella console WSUS → Options → Update Source and Proxy Server
```

```
PROBLEMA 5: Errore 0x800f0922 — Partizione EFI piena o connessione VPN
───────────────────────────────────────────────────────────────────────
Causa: System Reserved partition piena, o feature update fallisce con VPN attiva

Soluzione:
```

```powershell
# Se la partizione di sistema è piena:
# Verificare dimensione partizione EFI
mountvol S: /S          # Monta la partizione EFI su S:
dir S:\ /s              # Verifica contenuto
# Eliminare font non necessari o file temporanei dalla partizione EFI
# ATTENZIONE: operazione delicata, non eliminare file di boot

# Se il problema è la VPN:
# Disconnettere la VPN prima di installare il feature update
# La VPN può interferire con il download di componenti necessari
```

```
PROBLEMA 6: Riavvio in loop dopo aggiornamento
───────────────────────────────────────────────
Causa: aggiornamento non completato correttamente, conflitto driver

Soluzione:
```

```powershell
# 1. Attendere: a volte servono 2-3 riavvii per completare
# 2. Se persiste: boot in WinRE
#    → Troubleshoot → Advanced → Startup Settings → Safe Mode
# 3. In Safe Mode: disinstallare l'ultimo aggiornamento
wusa /uninstall /kb:NNNNNNN /quiet
# 4. Se Safe Mode non si avvia: WinRE → Command Prompt
DISM /Image:C:\ /Get-Packages | findstr "Installed"
DISM /Image:C:\ /Remove-Package /PackageName:"Package_name"
# 5. Se niente funziona: WinRE → System Restore (se abilitato)
#    oppure restore da backup
```

```
PROBLEMA 7: WUA riporta "Some settings are managed by your organization"
────────────────────────────────────────────────────────────────────────
Causa: GPO attive che configurano Windows Update

Soluzione:
```

```powershell
# Verificare quali GPO sono attive
gpresult /r /scope:computer | Select-String "Windows Update|WSUS"
# Report dettagliato:
gpresult /h "C:\Temp\GPResult.html" /f
# Aprire il file HTML e cercare "Windows Update" nella sezione
# Computer Configuration → Administrative Templates

# Se le GPO sono intenzionali (WSUS/WUfB): è il comportamento atteso
# Se non sono intenzionali: verificare con l'AD admin
```

```
PROBLEMA 8: Feature Update fallisce e torna alla versione precedente
───────────────────────────────────────────────────────────────────
Causa: incompatibilità hardware/software, driver, spazio disco

Soluzione:
```

```powershell
# Analizzare i log di setup:
# C:\$WINDOWS.~BT\Sources\Panther\setupact.log  (prima del reboot)
# C:\$WINDOWS.~BT\Sources\Panther\setuperr.log  (errori)
# C:\Windows\Panther\setupact.log                (dopo il reboot)

# Codici di errore comuni:
# 0xC1900101 - Driver error (aggiornare/rimuovere driver problematico)
# 0x80070070 - Spazio disco insufficiente (liberare spazio)
# 0xC1900208 - Applicazione incompatibile (disinstallare app bloccante)
# 0x800F0923 - Driver incompatibile (verificare vendor update)

# Controllare compatibilità:
# setupdiag.exe (Microsoft) analizza i log e identifica la causa
# Download: incluso in Windows 10 1903+ oppure scaricabile separatamente
# Eseguire dopo un feature update fallito:
& "C:\$WINDOWS.~BT\Sources\setupdiag.exe" /Output:"C:\Temp\SetupDiag.log"
```

```
PROBLEMA 9: WSUS client non reporta stato (Last Contact mai aggiornato)
──────────────────────────────────────────────────────────────────────
Causa: registrazione client fallita, GPO non applicata, firewall

Soluzione:
```

```powershell
# Sul client:
# 1. Verificare GPO
gpresult /r /scope:computer | Select-String "WSUS|WindowsUpdate"

# 2. Verificare connettività
Test-NetConnection -ComputerName wsus-server -Port 8530

# 3. Verificare registrazione
# La registrazione si trova in:
# HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate
$regPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate"
Get-ItemProperty $regPath -ErrorAction SilentlyContinue |
    Select-Object SusClientId, SusClientIdValidation

# 4. Re-registrare il client WSUS
wuauclt /resetauthorization /detectnow
# Su Windows 10+:
usoclient RefreshSettings
usoclient StartScan

# 5. Se persiste: eliminare il SusClientId e forzare re-registrazione
Stop-Service wuauserv
Remove-ItemProperty $regPath -Name SusClientId -ErrorAction SilentlyContinue
Remove-ItemProperty $regPath -Name SusClientIdValidation -ErrorAction SilentlyContinue
Start-Service wuauserv
usoclient StartScan
```

```
PROBLEMA 10: Errore 0x80244010 — Exceeded max server round trips
────────────────────────────────────────────────────────────────
Causa: WSUS con troppe categorie o aggiornamenti non rifiutati

Soluzione:
```

```powershell
# Sul server WSUS:
# 1. Eseguire cleanup aggressivo
Invoke-WsusServerCleanup -DeclineSupersededUpdates -DeclineExpiredUpdates `
    -CleanupObsoleteUpdates -CompressUpdates -CleanupUnneededContentFiles

# 2. Ridurre il numero di prodotti e classificazioni sincronizzati
# → Disabilitare prodotti non utilizzati nell'ambiente

# 3. Rifiutare aggiornamenti per architetture non presenti
Get-WsusUpdate | Where-Object {
    $_.Update.Title -match "Itanium|ARM64|x86" -and
    $_.Update.Title -notmatch "x64"  # adattare all'architettura dell'ambiente
} | Deny-WsusUpdate

# 4. Aumentare il maxXmlPerRequest nel web.config di WSUS
# IIS → Sites → WSUS Administration → web.config
# Modificare maxAllowedContentLength e maxRequestLength
```

```
PROBLEMA 11: "Undoing changes" dopo riavvio — aggiornamento annullato
────────────────────────────────────────────────────────────────────
Causa: conflitto di componenti, CBS error, file corrotti

Soluzione:
```

```powershell
# Dopo che il sistema torna su:
# 1. Verificare log CBS
Get-Content "C:\Windows\Logs\CBS\CBS.log" -Tail 100 |
    Select-String "FAILED|Error"

# 2. Riparare component store
DISM /Online /Cleanup-Image /RestoreHealth
sfc /scannow

# 3. Ritentare l'installazione dell'aggiornamento
# Se il problema persiste: scaricare il CU manualmente dal
# Microsoft Update Catalog (https://www.catalog.update.microsoft.com)
# e installare offline:
wusa C:\Temp\windows11-kb5034123-x64.msu /quiet /norestart
```

```
PROBLEMA 12: BITS errori di trasferimento (download fallisce)
────────────────────────────────────────────────────────────
Causa: proxy, firewall, corruzione cache BITS

Soluzione:
```

```powershell
# Verificare stato BITS
Get-BitsTransfer -AllUsers | Format-List DisplayName, JobState, ErrorDescription

# Cancellare trasferimenti bloccati
Get-BitsTransfer -AllUsers | Where-Object { $_.JobState -eq "Error" } |
    Remove-BitsTransfer

# Reset BITS
Stop-Service BITS
# Eliminare file di stato BITS
Remove-Item "$env:ALLUSERSPROFILE\Microsoft\Network\Downloader\*" -Force
Start-Service BITS
```

```
PROBLEMA 13: "Your device is not ready" per Feature Update
─────────────────────────────────────────────────────────
Causa: Safeguard Hold di Microsoft — incompatibilità nota

Soluzione:
- NON forzare l'installazione bypassando il safeguard hold
- Verificare il Known Issue specifico sulla pagina Windows Release Health
- Attendere che Microsoft rimuova il hold (dopo aver corretto il problema)
- Se urgente: identificare il componente bloccante e aggiornarlo/rimuoverlo
- Registry per verificare:
  HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\
    AppCompatFlags\TargetVersionUpgradeExperienceIndicators
```

```
PROBLEMA 14: Windows Update service si ferma automaticamente
────────────────────────────────────────────────────────────
Causa: comportamento normale (il servizio è demand-start),
       o malware che lo disabilita, o GPO che lo blocca

Soluzione:
```

```powershell
# Verificare il tipo di avvio del servizio
Get-Service wuauserv | Select-Object StartType
# Deve essere: Manual (Trigger Start) — NON Disabled

# Se è Disabled:
Set-Service wuauserv -StartupType Manual

# Verificare che non ci siano policy che lo bloccano
Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\wuauserv" |
    Select-Object Start, DelayedAutostart
# Start = 3 (Manual) = corretto
# Start = 4 (Disabled) = problema

# Verificare malware: molti malware disabilitano Windows Update
# Eseguire scan completo con Defender
Start-MpScan -ScanType FullScan
```

```
PROBLEMA 15: Aggiornamenti si reinstallano continuamente
────────────────────────────────────────────────────────
Causa: aggiornamento non completato correttamente,
       componente CBS corrotto, o reboot non eseguito

Soluzione:
```

```powershell
# 1. Verificare se ci sono operazioni pending
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending" -ErrorAction SilentlyContinue
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired" -ErrorAction SilentlyContinue

# 2. Se ci sono operazioni pending: riavviare il computer

# 3. Se dopo il riavvio il problema persiste:
DISM /Online /Cleanup-Image /RestoreHealth
sfc /scannow
# Poi ritentare l'installazione

# 4. Se il ciclo continua: controllare CBS.log per l'errore specifico
Get-Content "C:\Windows\Logs\CBS\CBS.log" | Select-String "KB5034123" |
    Select-Object -Last 20
```

```
PROBLEMA 16: Timeout durante il download di aggiornamenti da WSUS
────────────────────────────────────────────────────────────────
Causa: rete lenta, WSUS overloaded, content directory su disco lento

Soluzione:
```

```powershell
# Sul server WSUS:
# 1. Verificare carico IIS
Get-Counter "\Web Service(_Total)\Current Connections" -SampleInterval 5 -MaxSamples 3

# 2. Verificare performance disco della content directory
Get-Counter "\PhysicalDisk(*)\Avg. Disk Queue Length" -SampleInterval 5 -MaxSamples 3

# 3. Verificare che WsusPool non sia in stato di riciclo frequente
Import-Module WebAdministration
(Get-Item "IIS:\AppPools\WsusPool").Recycling.periodicRestart | Format-List

# Sul client:
# Aumentare timeout BITS
$wsusUrl = "http://wsus-server:8530"
$session = New-Object -ComObject Microsoft.Update.Session
$searcher = $session.CreateUpdateSearcher()
# BITS gestisce i retry automaticamente, ma verificare:
Get-BitsTransfer -AllUsers | Select-Object DisplayName, TransferType,
    BytesTransferred, BytesTotal, JobState
```

```
PROBLEMA 17: WSUS database (WID) molto grande e performance degradate
────────────────────────────────────────────────────────────────────
Causa: mancata manutenzione periodica del database

Soluzione:
```

```powershell
# 1. Verificare dimensione database WID
$widPath = "C:\Windows\WID\Data\SUSDB.mdf"
if (Test-Path $widPath) {
    $size = (Get-Item $widPath).Length / 1GB
    Write-Host "SUSDB size: $([math]::Round($size, 2)) GB"
}

# 2. Eseguire pulizia completa
Invoke-WsusServerCleanup -DeclineSupersededUpdates -DeclineExpiredUpdates `
    -CleanupObsoleteUpdates -CleanupObsoleteComputers `
    -CompressUpdates -CleanupUnneededContentFiles

# 3. Eseguire reindex (vedi sezione Manutenzione WSUS)
# & sqlcmd -S "\\.\pipe\MICROSOFT##WID\tsql\query" -i "C:\Scripts\WSUS-Reindex.sql"

# 4. Se il database è > 30 GB e la pulizia non riduce abbastanza:
# Considerare la migrazione a SQL Server
# O reinstallare WSUS con database pulito (esportare/reimportare approvazioni)

# 5. Shrink database (dopo cleanup e reindex):
# DBCC SHRINKDATABASE (SUSDB, 10)
# NOTA: lo shrink è una operazione pesante, eseguire fuori orario
```

```
PROBLEMA 18: Dual Scan — client scarica da Microsoft ignorando WSUS
───────────────────────────────────────────────────────────────────
Causa: GPO WUfB configurate insieme a GPO WSUS (conflitto)

Soluzione:
# Su Windows 10 1607-1709: Dual Scan era il comportamento default
# quando sia WUfB che WSUS erano configurati
# Il client scansionava Microsoft Update per quality/feature updates
# e WSUS solo per altri tipi

# Su Windows 10 1803+: Dual Scan è stato eliminato
# Se WSUS è configurato: il client usa SOLO WSUS
# Se si vuole WUfB: rimuovere la configurazione WSUS

# Verificare:
$auPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU"
$useWU = (Get-ItemProperty $auPath -ErrorAction SilentlyContinue).UseWUServer
$wufbPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate"
$deferQ = (Get-ItemProperty $wufbPath -ErrorAction SilentlyContinue).DeferQualityUpdates

if ($useWU -eq 1 -and $deferQ -eq 1) {
    Write-Warning "CONFLITTO: WSUS e WUfB configurati contemporaneamente"
    Write-Warning "Su W10 1803+: WUfB deferral viene ignorato, il client usa solo WSUS"
}
```

```
PROBLEMA 19: Errore "Some update files are missing or have problems"
───────────────────────────────────────────────────────────────────
Causa: file scaricati corrotti o incompleti

Soluzione:
```

```powershell
# 1. Eliminare cache download
Stop-Service wuauserv
Remove-Item "C:\Windows\SoftwareDistribution\Download\*" -Recurse -Force
Start-Service wuauserv
usoclient StartScan

# 2. Se persiste: download manuale dal Microsoft Update Catalog
# https://www.catalog.update.microsoft.com
# Cercare il KB number, scaricare il file .msu, installare offline:
wusa C:\Temp\windows11-kb5034123-x64.msu /quiet /norestart
```

```
PROBLEMA 20: Errore 0x80070005 — Access Denied durante l'aggiornamento
─────────────────────────────────────────────────────────────────────
Causa: permessi insufficienti, servizio non avviato come SYSTEM,
       antivirus che blocca l'operazione

Soluzione:
```

```powershell
# 1. Verificare che i servizi WU girino come Local System
Get-WmiObject Win32_Service -Filter "Name='wuauserv'" |
    Select-Object StartName
# Deve essere: LocalSystem

# 2. Verificare permessi sulla cartella SoftwareDistribution
$acl = Get-Acl "C:\Windows\SoftwareDistribution"
$acl.Access | Format-Table IdentityReference, FileSystemRights, AccessControlType

# 3. Disabilitare temporaneamente l'antivirus di terze parti
# Alcuni antivirus bloccano le operazioni di TrustedInstaller

# 4. Verificare che TrustedInstaller possa avviarsi
Get-Service TrustedInstaller | Select-Object Status, StartType
# Se Disabled: Set-Service TrustedInstaller -StartupType Manual
```

```
PROBLEMA 21: Update Orchestrator (USOsvc) non avvia la scansione pianificata
────────────────────────────────────────────────────────────────────────────
Causa: corruzione della registrazione del task in USOsvc, conflitto con
       software di ottimizzazione di terze parti, o dipendenze di servizio
       non soddisfatte (StateRepository, TokenBroker)

Soluzione:
```

```powershell
# 1. Verificare lo stato di USOsvc e delle sue dipendenze
Get-Service UsoSvc, StateRepository, TokenBroker |
    Select-Object Name, Status, StartType | Format-Table -AutoSize

# 2. Controllare i log ETW specifici dell'orchestratore
# USOsvc scrive nel log operativo dedicato, non in WindowsUpdate.log
Get-WinEvent -LogName "Microsoft-Windows-UpdateOrchestrator/Operational" `
    -MaxEvents 30 |
    Select-Object TimeCreated, Id, LevelDisplayName, Message |
    Format-Table -Wrap

# 3. Verificare che i task schedulati dell'orchestratore esistano
$usoTasks = Get-ScheduledTask -TaskPath "\Microsoft\Windows\UpdateOrchestrator\" `
    -ErrorAction SilentlyContinue
$usoTasks | Select-Object TaskName, State | Format-Table -AutoSize
# I task principali sono: Schedule Scan, Schedule Scan Static Task,
# Report policies, USO_UxBroker
# Se mancano: rigenerare con sfc /scannow o riparazione in-place

# 4. Se la scansione non parte: forzare manualmente il ciclo
# USOClient è il successore moderno di wuauclt su Windows 10+
usoclient StartInteractiveScan    # scansione con UI
usoclient StartScan               # scansione silente

# 5. Se USOsvc si blocca in stato "Starting" o "Stopping":
# Terminare forzatamente il processo e riavviare il servizio
$proc = Get-Process -Name "MoUsoCoreWorker" -ErrorAction SilentlyContinue
if ($proc) { Stop-Process $proc -Force }
Stop-Service UsoSvc -Force -ErrorAction SilentlyContinue
Start-Service UsoSvc

# 6. Controllare software di terze parti che potrebbe interferire
# Alcuni tool di "ottimizzazione" disabilitano USOsvc o i suoi task
# per ridurre il consumo di risorse — questo blocca completamente
# la scansione automatica degli aggiornamenti
# Verificare: CCleaner, IObit, Wise Care, e simili
# Ripristinare: Set-Service UsoSvc -StartupType AutomaticDelayedStart

# 7. Reset completo dell'orchestratore (ultimo resort)
Stop-Service UsoSvc -Force
Remove-Item "$env:ProgramData\USOPrivate\UpdateStore\*" -Recurse -Force `
    -ErrorAction SilentlyContinue
Remove-Item "$env:ProgramData\USOShared\Logs\*" -Recurse -Force `
    -ErrorAction SilentlyContinue
Start-Service UsoSvc
usoclient RefreshSettings
usoclient StartScan
# Il servizio ricostruirà il proprio stato dalla scansione successiva
```

---

## Checklist Processo di Patch Management

```
CHECKLIST — PROCESSO DI PATCH MANAGEMENT MENSILE
─────────────────────────────────────────────────

PRE-PATCHING (Giorno 0 — Patch Tuesday):
─────────────────────────────────────────
□ Leggere Security Update Guide e note di rilascio Microsoft
□ Identificare CVE critici (CVSS ≥ 7.0) e verificare exploitability
□ Verificare known issues per il CU corrente
□ Controllare bollettini vendor per applicazioni LOB
□ Comunicare ai team interessati (Service Desk, App Owner)
□ Verificare che i backup siano aggiornati e funzionanti
□ Creare snapshot/checkpoint per VM nei ring iniziali

RING 0 — TEST (Giorno 0-1):
────────────────────────────
□ Approvare aggiornamenti per il gruppo Test in WSUS/SCCM/Intune
□ Verificare download completato sui client di test
□ Verificare installazione e reboot completati
□ Eseguire test di smoke (boot, servizi, rete, applicazioni)
□ Controllare Event Viewer per errori critici
□ Documentare eventuali problemi

RING 1 — PILOT (Giorno 2-5):
─────────────────────────────
□ Verificare Ring 0 stabile per almeno 24 ore
□ Approvare aggiornamenti per il gruppo Pilot
□ Comunicare ai pilot user che riceveranno gli aggiornamenti
□ Monitorare ticket helpdesk per problemi correlati
□ Raccogliere feedback dai pilot user
□ Documentare eventuali problemi

RING 2 — PRODUZIONE (Giorno 5-14):
───────────────────────────────────
□ Verificare Ring 1 stabile per almeno 48 ore
□ Approvare aggiornamenti per il gruppo Production
□ Creare Change Request (se richiesto dal processo ITSM)
□ Comunicare la maintenance window agli utenti
□ Monitorare compliance e deployment progress
□ Gestire eccezioni e escalation

RING 3 — MISSION-CRITICAL (Giorno 14-21):
──────────────────────────────────────────
□ Verificare Ring 2 stabile per almeno 7 giorni
□ Creare e approvare Change Request con approvazione management
□ Creare backup/snapshot di tutti i sistemi critici
□ Comunicare la maintenance window a tutti gli stakeholder
□ Preparare team di rollback (in standby durante la maintenance)
□ Eseguire patching fuori orario con presidio
□ Verificare manualmente ogni servizio critico post-reboot
□ Aggiornare CMDB con lo stato degli aggiornamenti

POST-PATCHING (Giorno 21-30):
──────────────────────────────
□ Generare report compliance (target: 95%+)
□ Identificare sistemi non conformi e pianificare remediation
□ Documentare eccezioni con giustificazione e risk owner
□ Registrare problemi riscontrati per migliorare il processo futuro
□ Aggiornare la knowledge base con workaround trovati
□ Pulizia WSUS (se in uso)
□ Eliminare snapshot/checkpoint non più necessari
□ Archiviare report per audit trail
```

---

## Procedura di Emergency Patching

```
PROCEDURA DI EMERGENCY PATCHING (ZERO-DAY / CVE CRITICO)
─────────────────────────────────────────────────────────

CRITERI DI ATTIVAZIONE:
- CVE con "Exploited in the Wild = Yes"
- CVSS ≥ 9.0 con vettore di attacco Network e complessità Low
- Advisory CISA/CERT che impone patching entro 24-48 ore
- Evidenza di tentativo di exploit nel proprio ambiente

FASE 1 — TRIAGE (0-1 ora dal rilascio):
────────────────────────────────────────
□ Alert ricevuto: fonte (MSRC, CISA, vendor, SOC)
□ Identificare il CVE e il prodotto affetto
□ Valutare l'applicabilità nel proprio ambiente:
  - Quanti sistemi sono vulnerabili?
  - Il servizio/porta affetto è esposto?
  - Esistono mitigazioni temporanee (WAF, firewall rule, disabilitazione feature)?
□ Classificare la severità interna: CRITICAL / HIGH
□ Se CRITICAL: procedere con emergency patch
□ Se HIGH con mitigazione possibile: applicare mitigazione,
  poi seguire il processo standard accelerato

FASE 2 — APPROVAZIONE (1-2 ore):
─────────────────────────────────
□ Notificare CISO / IT Director / Change Advisory Board
□ Ottenere approvazione per emergency change (verbale + email = sufficiente)
□ Documentare: data/ora, chi ha approvato, giustificazione
□ Attivare il team di patching d'emergenza
□ Comunicare internamente: "Emergency patch in corso per CVE-YYYY-NNNNN"

FASE 3 — TEST MINIMO (2-4 ore):
────────────────────────────────
□ Scaricare la patch dal Microsoft Update Catalog
□ Testare su 1-2 macchine nel Ring 0 (lab)
□ Verificare: boot corretto, servizi attivi, nessun BSOD
□ Se il test fallisce: valutare se procedere comunque o applicare mitigazione
□ Documentare risultati test

FASE 4 — DEPLOY ACCELERATO (4-12 ore):
───────────────────────────────────────
□ Creare backup/snapshot dei sistemi critici PRIMA del deploy
□ Deploy su TUTTI i ring simultaneamente (skip ring graduale)
□ Priorità: sistemi esposti a Internet > sistemi interni > sistemi isolati
□ Monitorare in tempo reale:
  - WSUS/SCCM/Intune compliance dashboard
  - Event Viewer centralizzato
  - Ticket helpdesk
□ Gestire eccezioni immediatamente (sistemi che non possono essere patchati)
□ Per sistemi non patchabili: applicare mitigazione alternativa

FASE 5 — VERIFICA E CHIUSURA (12-24 ore):
──────────────────────────────────────────
□ Report compliance: verificare 100% dei sistemi affetti patchati
□ Verificare che nessun servizio sia stato degradato
□ Rimuovere mitigazioni temporanee (se non più necessarie)
□ Documentare:
  - Timeline completa (dalla scoperta alla chiusura)
  - Sistemi patchati e non patchati (con giustificazione)
  - Problemi riscontrati e soluzioni applicate
  - Lessons learned
□ Notificare chiusura a CISO / management
□ Aggiornare il runbook se il processo ha rivelato lacune

COMUNICAZIONE:
- Internal: email + Teams/Slack a tutti gli IT + service desk
- Management: briefing CISO con impatto e timeline
- Utenti: notifica solo se necessario riavvio forzato in orario lavorativo
- External (se applicabile): notifica a clienti/partner se il servizio è affetto

NOTA: questa procedura va testata almeno 1 volta all'anno con un drill
(simulazione di emergency patching su ambiente non produttivo)
```

---

## FAQ — Domande Frequenti

**D1: Qual è la differenza tra WSUS, SCCM e Intune per la gestione delle patch?**

WSUS è il motore base di scansione e distribuzione on-premise, gratuito con Windows Server. SCCM (ora MECM) usa WSUS come componente sottostante ma aggiunge orchestrazione avanzata: deployment packages, ADR, maintenance windows, phased deployment, compliance reporting via SSRS. Intune è la soluzione cloud-native che usa WUfB per controllare deferral e compliance senza infrastruttura on-premise. In molti ambienti coesistono: SCCM per server e workstation on-premise, Intune per dispositivi remoti/BYOD. La scelta dipende dall'infrastruttura esistente, dal livello di controllo richiesto e dalla strategia cloud dell'organizzazione.

---

**D2: Posso usare WSUS e Windows Update for Business insieme sullo stesso client?**

No, non dal Windows 10 1803 in poi. Se un client ha la GPO per il server WSUS attiva (`UseWUServer = 1`), il client usa esclusivamente WSUS e ignora qualsiasi impostazione WUfB (deferral, pause). Prima della 1803, esisteva il "Dual Scan" che causava confusione perche il client poteva scansionare sia WSUS che Microsoft Update. La scelta è esclusiva: o WSUS o WUfB per ogni client.

---

**D3: Come gestisco le patch su server fisici senza possibilità di snapshot?**

Usare Windows Server Backup per un System State backup prima del patching. Verificare che il backup sia completato e testato. In alternativa, configurare il server come nodo di un cluster (se applicabile) e patchare un nodo alla volta con failover. Per server standalone fisici critici: considerare la migrazione a VM per avere la protezione degli snapshot, oppure implementare hotpatching via Azure Arc per ridurre i riavvii.

---

**D4: Quanto spazio disco serve per WSUS?**

Dipende dal numero di prodotti e classificazioni sincronizzati. Un WSUS con Windows 10/11 + Windows Server 2019/2022 + Office + Defender richiede tipicamente 100-150 GB per la content directory. Aggiungere lingue moltiplica lo spazio. Best practice: selezionare solo i prodotti realmente presenti nell'ambiente, solo le lingue necessarie, ed eseguire il cleanup mensile. Il database (WID) tipicamente occupa 10-30 GB. Con SQL Server dedicato, lo spazio database non è sul server WSUS.

---

**D5: Cos'è un Servicing Stack Update e perche è importante?**

Il Servicing Stack Update (SSU) aggiorna il componente che installa gli aggiornamenti stessi (CBS, CSI, CMI). Se la servicing stack è vecchia o corrotta, il sistema non riesce a installare i Cumulative Update successivi. Da Windows 10 2004+, Microsoft combina SSU e CU in un pacchetto unico: il sistema installa prima l'SSU e poi il CU automaticamente. Un SSU non può essere disinstallato. Se un CU fallisce con errori CBS, verificare che l'SSU più recente sia installato.

---

**D6: Come funziona il rollback di un Feature Update?**

Entro 10 giorni (default) dall'installazione di un Feature Update, Windows mantiene una copia della versione precedente nella cartella `Windows.old`. L'utente può tornare indietro da Settings → Recovery → Go back. Il periodo è estendibile fino a 60 giorni con `DISM /Online /Set-OSUninstallWindow /Value:60`. Dopo la scadenza, i file di rollback vengono eliminati automaticamente per recuperare spazio disco. Su server virtuali, lo snapshot pre-upgrade è sempre preferibile perche non ha limiti temporali.

---

**D7: Come gestisco i driver tramite Windows Update senza rischiare incompatibilità?**

Abilitare la GPO "Do not include drivers with Windows Updates" per escludere i driver dalla distribuzione automatica. Gestire i driver separatamente: tramite SCCM Driver Packages (per deployment OSD), tramite Intune Driver Management (per dispositivi cloud-managed), o tramite tool del vendor (Dell Command Update, HP SoftPaq). Testare sempre i driver in laboratorio prima del deploy in produzione. I driver opzionali sono disponibili in Settings → Optional Updates e non si installano automaticamente.

---

**D8: Cosa succede se un aggiornamento causa BSOD su un server di produzione?**

1. Se il server è virtualizzato: restore immediato dallo snapshot pre-patch. 2. Se il server è fisico: boot in Safe Mode e disinstallare il KB con `wusa /uninstall /kb:NNNNNNN`. 3. Se Safe Mode non si avvia: boot da WinRE → Command Prompt → `DISM /Image:C:\ /Remove-Package`. 4. Documentare il BSOD (Stop Code, parametri) e aprire caso con Microsoft Support. 5. Rifiutare l'aggiornamento in WSUS per impedirne la reinstallazione. 6. Comunicare il problema al team e verificare se altri sistemi sono affetti.

---

**D9: Ogni quanto devo eseguire la manutenzione di WSUS?**

Cleanup mensile con `Invoke-WsusServerCleanup` dopo ogni Patch Tuesday. Reindex del database trimestralmente (o mensilmente se il database è grande). Monitoraggio settimanale dello spazio disco. Verifica quotidiana dello stato di sincronizzazione. Pulizia annuale dei prodotti e delle classificazioni (rimuovere OS non più in uso). Se si usa WID: valutare la migrazione a SQL Server se il database supera i 20 GB o se si gestiscono più di 10.000 client.

---

**D10: Come implemento un processo di patch management se non ne ho uno?**

Iniziare con: 1. Inventario di tutti i sistemi (OS, versione, ruolo). 2. Scegliere lo strumento (WSUS per ambienti piccoli, SCCM per enterprise, Intune per cloud). 3. Definire 4 ring di deployment. 4. Definire una maintenance window mensile (concordata con il business). 5. Creare una GPO per client WSUS/WUfB. 6. Implementare il primo ciclo di patching manuale. 7. Automatizzare progressivamente (ADR, auto-approval). 8. Implementare reporting e KPI. 9. Documentare eccezioni e procedure di rollback. 10. Drill annuale della procedura di emergency patching.

---

**D11: Qual è la differenza tra B Release, C Release e D Release?**

B Release (Patch Tuesday, 2° martedì): il rilascio principale con tutti i fix di sicurezza e affidabilità. Obbligatorio per compliance. C Release (3-4° settimana): preview opzionale dei fix non-security che saranno inclusi nel prossimo B Release. Utile per validare in anticipo. Non contiene nuovi fix di sicurezza. Non distribuire in produzione senza test. D Release: eliminato da Microsoft nel 2023, era un ulteriore preview nella 4° settimana.

---

**D12: Come gestisco i sistemi che non possono essere patchati (legacy, EOL)?**

Documentare ogni eccezione con: motivo del mancato patching, risk owner (chi accetta il rischio), mitigazioni applicate (segmentazione rete, firewall rules, application whitelisting), data prevista per la dismissione o migrazione. Implementare network segmentation per isolare i sistemi EOL. Monitorare con IDS/IPS per rilevare tentativi di exploit. Pianificare attivamente la migrazione. Mai esporre sistemi EOL a Internet o a segmenti di rete non trusted.

---

**D13: Hotpatching è disponibile per Windows client (desktop)?**

No, al 2026-05 l'hotpatching è disponibile solo per Windows Server (Azure Edition nativo, on-premise via Azure Arc). Non esiste hotpatching per Windows 10/11 client. I client devono sempre riavviare per applicare i Cumulative Updates. Microsoft potrebbe estendere la funzionalità in futuro, ma non ci sono annunci ufficiali per il client.

---

**D14: Come gestisco gli aggiornamenti per i dispositivi offline o disconnessi?**

Per dispositivi che non hanno accesso alla rete aziendale o a Internet: 1. Scaricare i pacchetti dal Microsoft Update Catalog. 2. Distribuire via USB, DVD, o file share raggiungibile. 3. Installare con `wusa file.msu /quiet`. 4. Per ambienti air-gapped: WSUS disconnesso — esportare metadata e content da un WSUS connesso, importare sul WSUS air-gapped con `WsusUtil.exe export/import`. 5. Per dispositivi mobili che tornano periodicamente in rete: configurare VPN split tunnel che permetta accesso a WSUS/WUfB.

---

**D15: Come verifico rapidamente se un server specifico ha un KB installato?**

```powershell
# Metodo rapido locale:
Get-HotFix -Id KB5034123

# Metodo rapido remoto:
Get-HotFix -Id KB5034123 -ComputerName SRV01, SRV02, SRV03

# Se Get-HotFix non trova il KB (non tutti i CU appaiono in Get-HotFix):
Get-WindowsPackage -Online | Where-Object { $_.PackageName -like "*KB5034123*" }

# Verifica remota su molti server:
$servers = Get-ADComputer -Filter { OperatingSystem -like "*Server*" } |
    Select-Object -ExpandProperty Name
Invoke-Command -ComputerName $servers -ScriptBlock {
    $kb = Get-HotFix -Id "KB5034123" -ErrorAction SilentlyContinue
    [PSCustomObject]@{
        Server    = $env:COMPUTERNAME
        Installato = [bool]$kb
        Data       = $kb.InstalledOn
    }
} | Sort-Object Installato | Format-Table
```

---

**D16: Come posso accelerare il download degli aggiornamenti nella rete aziendale?**

1. Delivery Optimization (DO) in modalità LAN/Group: i client condividono tra peer, riducendo il traffico verso WSUS/Internet. 2. Microsoft Connected Cache: cache locale integrata con SCCM distribution point, i client DO scaricano dal cache locale. 3. BranchCache: cache distribuita per sedi remote con banda WAN limitata. 4. WSUS downstream/replica: un server WSUS per sede, scarica i contenuti una sola volta dalla sede centrale. 5. BITS throttling: configurare limiti di banda per evitare saturazione della rete durante gli orari lavorativi.

---

**D17: Qual è la best practice per gestire gli aggiornamenti di Microsoft 365 Apps (Office)?**

Microsoft 365 Apps ha un proprio canale di aggiornamento indipendente da Windows Update. Opzioni: 1. Office CDN (default): i client scaricano direttamente da Microsoft. Configurare il canale (Current, Monthly Enterprise, Semi-Annual Enterprise) via GPO o Intune. 2. SCCM: gestire gli aggiornamenti di Office come software updates tramite il SUP. 3. Intune: configurare il canale e le policy di aggiornamento nel profilo di configurazione di Microsoft 365 Apps. Consiglio: usare Monthly Enterprise Channel per la maggior parte degli utenti (rilascio mensile, supportato per 2 mesi) e Current Channel solo per il pilot.

---

## Esercizi

1. Descrivi le differenze tra Cumulative Update, Security-only Update e Servicing Stack Update: in quale scenario ciascuno e rilevante?
2. **Lab:** Installa WSUS su un server Windows, crea almeno 3 computer group (Pilot, Produzione, Server Critici), configura una regola di approvazione automatica per gli aggiornamenti critici e di sicurezza, e verifica il reporting di compliance.
3. Un'azienda con 2000 endpoint ha una compliance del 70% a 30 giorni dal Patch Tuesday. Progetta un piano di remediation per raggiungere il 95%: quali ring, quali GPO, quale monitoraggio?
4. Ricerca i pro e contro di Windows Update for Business rispetto a WSUS per un'organizzazione di medie dimensioni (500-1000 endpoint). Quando ha senso una configurazione ibrida?

## Auto-valutazione

<details><summary>1. Cos'e il Patch Tuesday e perche e importante?</summary>
Il Patch Tuesday e il secondo martedi di ogni mese, quando Microsoft rilascia gli aggiornamenti cumulativi di sicurezza e qualita. E fondamentale per la pianificazione del ciclo di patching enterprise: testing nel ring pilota, approvazione e deployment nei ring successivi — vedi sezione Panoramica e Idee guida.
</details>

<details><summary>2. Che differenza c'e tra WSUS e Windows Update for Business?</summary>
WSUS e un server on-premises che scarica, approva e distribuisce aggiornamenti centralmente. WUfB e un servizio cloud-based configurabile via GPO/Intune che gestisce differimento e ring senza infrastruttura locale. Possono coesistere, ma non sullo stesso client — vedi sezioni WSUS e WUfB.
</details>

<details><summary>3. Cos'e un ring di deployment e quanti ne servono?</summary>
Un ring e un gruppo di dispositivi che riceve gli aggiornamenti con un ritardo specifico. Tipicamente: Ring 0 (IT pilot, 0 giorni), Ring 1 (early adopter, 7 giorni), Ring 2 (produzione, 14 giorni), Ring 3 (server critici, 21-30 giorni). Permette validazione progressiva — vedi sezione Ring deployment.
</details>

<details><summary>4. Come si gestisce un aggiornamento zero-day?</summary>
Procedura accelerata: si salta il ring normale, si distribuisce immediatamente con rollback pronto. Testare su un gruppo minimo (1 ora), poi broad deployment. Avere un piano di rollback con `wusa /uninstall /kb:KBNUMBER` o DISM — vedi Idee guida e sezione Rollback.
</details>

<details><summary>5. A cosa serve Delivery Optimization?</summary>
Delivery Optimization (DO) permette ai client di scaricare contenuti di aggiornamento da peer nella stessa LAN o gruppo, riducendo il traffico verso WSUS/Internet. Modalita: LAN (stesso subnet), Group (stesso AD site/group ID), Internet. Configurabile via GPO — vedi sezione Delivery Optimization.
</details>

<details><summary>6. Come si fa il rollback di un aggiornamento problematico?</summary>
Tramite `wusa /uninstall /kb:KBNUMBER /quiet /norestart`, oppure via DISM: `DISM /Online /Remove-Package /PackageName:...`. Per i feature update: Settings > Recovery > Go back (entro 10 giorni, estensibile via `DISM /Online /Set-OSUninstallWindow /Value:30`). Via WSUS: declinare il KB e rimuoverlo — vedi sezione Rollback.
</details>

<details><summary>7. Cosa sono i computer group in WSUS?</summary>
Gruppi logici di computer all'interno di WSUS che permettono di approvare aggiornamenti in modo selettivo per gruppi diversi (es. Pilot, Produzione, Server). L'assegnazione puo essere manuale (console WSUS) o automatica (GPO client-side targeting) — vedi sezione Computer Groups.
</details>

<details><summary>8. Come si verifica se un KB specifico e installato su piu server?</summary>
Con `Get-HotFix -Id KB5034123 -ComputerName SRV01,SRV02` oppure, per KB non visibili in Get-HotFix, con `Get-WindowsPackage -Online | Where-Object { $_.PackageName -like "*KB5034123*" }`. Per molti server: usare `Invoke-Command` con una lista da Active Directory — vedi FAQ D15.
</details>

## Letture primarie consigliate

- Microsoft Learn — Windows Update for Business: <https://learn.microsoft.com/windows/deployment/update/waas-manage-updates-wufb> (consultato: 2026-05-23)
- Microsoft Learn — WSUS overview: <https://learn.microsoft.com/windows-server/administration/windows-server-update-services/get-started/windows-server-update-services-wsus> (consultato: 2026-05-23)
- Microsoft Learn — Delivery Optimization: <https://learn.microsoft.com/windows/deployment/do/waas-delivery-optimization> (consultato: 2026-05-23)
- Microsoft Learn — Windows release health: <https://learn.microsoft.com/windows/release-health/> (consultato: 2026-05-23)
- Microsoft Learn — Update compliance: <https://learn.microsoft.com/windows/deployment/update/update-compliance-monitor> (consultato: 2026-05-23)

## Collegamenti incrociati

- [Group Policy](21-group-policy-guida-completa.md) — GPO per configurazione Windows Update e ring
- [Endpoint Management](12-endpoint-management.md) — gestione aggiornamenti tramite SCCM/MECM
- [Intune](26-intune-gestione-moderna.md) — WUfB e policy di aggiornamento cloud-based
- [Sicurezza Windows](05-sicurezza-windows.md) — patching come prima linea di difesa
- [Monitoraggio e Performance](09-monitoraggio-performance.md) — monitorare compliance e stato aggiornamenti

## Glossario locale

| Termine | Definizione |
|---------|-------------|
| Patch Tuesday | Secondo martedi del mese: data di rilascio degli aggiornamenti cumulativi Microsoft |
| WSUS | Windows Server Update Services: ruolo server per la gestione centralizzata degli aggiornamenti |
| WUfB | Windows Update for Business: servizio cloud per il controllo del differimento e dei ring di deployment |
| Cumulative Update (CU) | Aggiornamento mensile che include tutte le fix di sicurezza e qualita precedenti |
| Servicing Stack Update (SSU) | Aggiornamento del componente che installa gli altri aggiornamenti; prerequisito per i CU |
| Ring di deployment | Gruppo di dispositivi che riceve gli aggiornamenti con un ritardo specifico per validazione progressiva |
| Delivery Optimization (DO) | Tecnologia peer-to-peer per la distribuzione efficiente dei contenuti di aggiornamento nella LAN |
| KB (Knowledge Base) | Identificativo univoco di un aggiornamento Microsoft (es. KB5034123) |
| Feature Update | Aggiornamento annuale che porta una nuova versione di Windows (es. 23H2 → 24H2) |
| BranchCache | Tecnologia di cache distribuita per ottimizzare il download di contenuti in sedi remote |
