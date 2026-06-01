# Windows Defender e Endpoint Security — Guida Approfondita

> **Modulo 24** · **Aggiornamento:** 2026-05-23

| Campo | Valore |
|---|---|
| **Corso** | Windows per ingegneri di sistema |
| **Fase** | Sicurezza endpoint e hardening |
| **Modulo del corso** | 24 — Windows Defender e Endpoint Security |
| **Versioni di riferimento** | Windows 11 24H2, Windows Server 2025, Microsoft Defender Antivirus Engine 1.1.24060.x, MDE Plan 2 (Maggio 2026), Intune 2405+ |
| **Livello** | Proficient (avanzato) |
| **Prerequisiti** | Padronanza di PowerShell (→ `02-powershell.md`), sicurezza Windows base (→ `05-sicurezza-windows.md`), concetti di networking (→ `21-networking-avanzato.md`), familiarità con Group Policy (→ `28-group-policy-avanzato.md`) |
| **Obiettivi di apprendimento** | 1) Configurare Microsoft Defender Antivirus con cloud-delivered protection, MAPS e automatic sample submission · 2) Progettare e distribuire policy WDAC con supplemental policies, Managed Installer e ISG · 3) Implementare tutte le ASR rules con mappatura MITRE ATT&CK e rollout graduale · 4) Configurare Exploit Protection (ASLR, DEP, CFG, SEHOP) a livello sistema e per-processo · 5) Eseguire onboarding MDE e investigare alert con Advanced Hunting (KQL) · 6) Gestire Tamper Protection, Network Protection e Controlled Folder Access in ambienti enterprise · 7) Confrontare WDAC e AppLocker e scegliere la soluzione appropriata per lo scenario · 8) Risolvere problemi comuni: falsi positivi ASR, WDAC blocking, scan performance, connettività MDE |
| **Tempo stimato** | 24–32 ore (studio + esercizi + laboratorio) |
| **Ultimo aggiornamento** | 2026-05-23 |
| **Tag** | `endpoint-security`, `defender-antivirus`, `WDAC`, `AppLocker`, `ASR`, `EDR`, `MDE`, `exploit-protection`, `tamper-protection`, `network-protection`, `controlled-folder-access`, `intune`, `KQL`, `MITRE-ATT&CK` |

## Idee guida
1. **Defender ASR (Attack Surface Reduction) rules.**
2. **Defender for Endpoint (paid): EDR + investigation.**
3. **Cloud-delivered protection on by default.**
4. **Tamper protection bisogna abilitare via Intune.**

### Mappa Concettuale

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                    MICROSOFT DEFENDER — STACK DI SICUREZZA ENDPOINT              │
├──────────────────┬──────────────────┬──────────────────┬──────────────────────────┤
│  PREVENZIONE     │  RILEVAMENTO     │  RISPOSTA        │  GESTIONE                │
│                  │                  │                  │                          │
│ ┌──────────────┐ │ ┌──────────────┐ │ ┌──────────────┐ │ ┌──────────────────────┐ │
│ │Defender AV   │ │ │EDR Sensor    │ │ │Automated     │ │ │ Microsoft 365        │ │
│ │Real-Time     │ │ │Telemetry     │ │ │Investigation │ │ │ Defender Portal      │ │
│ │Cloud Protect.│ │ │Process/Net/  │ │ │& Response    │ │ │ security.microsoft   │ │
│ │MAPS + BAFS   │ │ │File/Registry │ │ │(AIR)         │ │ │ .com                 │ │
│ └──────────────┘ │ └──────────────┘ │ └──────────────┘ │ └──────────────────────┘ │
│ ┌──────────────┐ │ ┌──────────────┐ │ ┌──────────────┐ │ ┌──────────────────────┐ │
│ │WDAC          │ │ │Advanced      │ │ │Live Response │ │ │ Microsoft Intune     │ │
│ │App Whitelist │ │ │Hunting (KQL) │ │ │Device Isolat.│ │ │ Endpoint Security    │ │
│ │UMCI + KMCI   │ │ │Custom Detect.│ │ │File Quarant. │ │ │ Profiles             │ │
│ └──────────────┘ │ └──────────────┘ │ └──────────────┘ │ └──────────────────────┘ │
│ ┌──────────────┐ │ ┌──────────────┐ │ ┌──────────────┐ │ ┌──────────────────────┐ │
│ │ASR Rules     │ │ │Threat        │ │ │Indicators of │ │ │ Group Policy         │ │
│ │Office, LSASS │ │ │Analytics     │ │ │Compromise    │ │ │ Administrative       │ │
│ │Script, WMI   │ │ │MITRE mapping │ │ │Custom IoC    │ │ │ Templates            │ │
│ └──────────────┘ │ └──────────────┘ │ └──────────────┘ │ └──────────────────────┘ │
│ ┌──────────────┐ │ ┌──────────────┐ │                  │ ┌──────────────────────┐ │
│ │Exploit Prot. │ │ │Device Health │ │                  │ │ PowerShell           │ │
│ │DEP ASLR CFG  │ │ │Attestation   │ │                  │ │ Get/Set-MpPreference │ │
│ │SEHOP EAF ACG │ │ │Boot Integrity│ │                  │ │ Start-MpScan         │ │
│ └──────────────┘ │ └──────────────┘ │                  │ └──────────────────────┘ │
│ ┌──────────────┐ │                  │                  │ ┌──────────────────────┐ │
│ │Controlled    │ │                  │                  │ │ Security Baselines   │ │
│ │Folder Access │ │                  │                  │ │ Windows, MDE, Edge   │ │
│ │Ransomware    │ │                  │                  │ │ Office 365           │ │
│ └──────────────┘ │                  │                  │ └──────────────────────┘ │
│ ┌──────────────┐ │                  │                  │                          │
│ │Network Prot. │ │                  │                  │                          │
│ │SmartScreen   │ │                  │                  │                          │
│ │Web Filtering │ │                  │                  │                          │
│ └──────────────┘ │                  │                  │                          │
│ ┌──────────────┐ │                  │                  │                          │
│ │Tamper Prot.  │ │                  │                  │                          │
│ │Cloud-managed │ │                  │                  │                          │
│ └──────────────┘ │                  │                  │                          │
├──────────────────┴──────────────────┴──────────────────┴──────────────────────────┤
│  IDENTITY LAYER: Microsoft Defender for Identity (MDI) — AD threat detection     │
├──────────────────────────────────────────────────────────────────────────────────┤
│  CORRELATION: Microsoft Intelligent Security Graph — ML, global telemetry        │
└──────────────────────────────────────────────────────────────────────────────────┘
```

## Indice
- [Panoramica](#panoramica)
- [Microsoft Defender Antivirus](#microsoft-defender-antivirus)
- [Real-Time Protection e Cloud Protection](#real-time-protection-e-cloud-protection)
- [WDAC vs AppLocker — Confronto Architetturale](#wdac-vs-applocker--confronto-architetturale)
- [Attack Surface Reduction (ASR) Rules](#attack-surface-reduction-asr-rules)
- [ASR Rules — Mappatura MITRE ATT&CK Completa](#asr-rules--mappatura-mitre-attck-completa)
- [Controlled Folder Access](#controlled-folder-access)
- [Network Protection — Approfondimento](#network-protection--approfondimento)
- [Exploit Protection — Configurazione Avanzata](#exploit-protection--configurazione-avanzata)
- [Tamper Protection — Deep Dive](#tamper-protection--deep-dive)
- [Microsoft Defender for Endpoint (EDR)](#microsoft-defender-for-endpoint-edr)
- [EDR — Telemetria e Advanced Hunting Avanzato](#edr--telemetria-e-advanced-hunting-avanzato)
- [Threat Analytics e Automated Investigation](#threat-analytics-e-automated-investigation)
- [Attack Simulation e Training](#attack-simulation-e-training)
- [Device Health Attestation](#device-health-attestation)
- [Microsoft Defender for Identity](#microsoft-defender-for-identity)
- [Windows Defender Application Control (WDAC)](#windows-defender-application-control-wdac)
- [WDAC — Code Integrity: UMCI vs KMCI](#wdac--code-integrity-umci-vs-kmci)
- [WDAC — Strategie Avanzate di Policy](#wdac--strategie-avanzate-di-policy)
- [AppLocker — Regole per Tipo di File](#applocker--regole-per-tipo-di-file)
- [Exploit Protection](#exploit-protection)
- [Network Protection e Web Protection](#network-protection-e-web-protection)
- [Tamper Protection e Security Intelligence](#tamper-protection-e-security-intelligence)
- [Microsoft Intune — Integrazione Defender](#microsoft-intune--integrazione-defender)
- [Gestione con PowerShell e GPO](#gestione-con-powershell-e-gpo)
- [PowerShell — Cmdlet di Riferimento Completi](#powershell--cmdlet-di-riferimento-completi)
- [Group Policy vs Intune — Confronto per Funzionalità](#group-policy-vs-intune--confronto-per-funzionalità)
- [Event ID di Riferimento — Tabella Completa](#event-id-di-riferimento--tabella-completa)
- [Integrazione SIEM e Log Forwarding](#integrazione-siem-e-log-forwarding)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)
- [Esercizi](#esercizi)
- [Letture Primarie Consigliate](#letture-primarie-consigliate)
- [Collegamenti Incrociati](#collegamenti-incrociati)
- [Glossario Locale](#glossario-locale)
- [Riferimenti](#riferimenti)

---

## Panoramica

La sicurezza degli endpoint rappresenta la prima linea di difesa in qualsiasi architettura di sicurezza aziendale moderna. Microsoft ha investito significativamente nell'evoluzione della propria piattaforma di protezione, trasformando quello che era un semplice antivirus (Windows Defender) in un ecosistema di sicurezza integrato che copre prevenzione, rilevamento, risposta e remediation delle minacce su endpoint Windows, macOS, Linux, iOS e Android.

L'ecosistema Microsoft Defender si articola in più prodotti complementari: **Microsoft Defender Antivirus** fornisce la protezione preventiva tradizionale (antimalware, real-time protection); **Microsoft Defender for Endpoint** (MDE, precedentemente Microsoft Defender ATP) aggiunge capacità di Endpoint Detection and Response (EDR), threat hunting e automated investigation; **Attack Surface Reduction (ASR) rules** blocca comportamenti comunemente sfruttati dal malware; **Windows Defender Application Control (WDAC)** implementa il whitelisting delle applicazioni; **Exploit Protection** mitiga le tecniche di exploitation a livello di memoria.

Questa guida analizza in profondità ogni componente, fornendo configurazioni pratiche tramite PowerShell, Group Policy e Microsoft Intune, con l'obiettivo di costruire una postura di sicurezza defense-in-depth sugli endpoint Windows.

---

## Microsoft Defender Antivirus

Microsoft Defender Antivirus è il motore antimalware integrato in Windows 10/11 e Windows Server 2016+. Utilizza un approccio multi-layer per la rilevazione delle minacce:

1. **Signature-based detection** — Database di firme aggiornato tramite Security Intelligence Updates
2. **Heuristic detection** — Analisi comportamentale locale che identifica pattern sospetti
3. **Cloud-delivered protection** — Analisi in tempo reale nel cloud Microsoft tramite il Microsoft Intelligent Security Graph
4. **Machine learning** — Modelli ML che classificano file sconosciuti basandosi su miliardi di segnali

### Configurazione Base

```powershell
# Verificare lo stato di Defender
Get-MpComputerStatus | Select-Object AMRunningMode, AMServiceEnabled,
    AntispywareEnabled, AntivirusEnabled, BehaviorMonitorEnabled,
    IoavProtectionEnabled, NISEnabled, OnAccessProtectionEnabled,
    RealTimeProtectionEnabled

# Verificare la versione delle definizioni
Get-MpComputerStatus | Select-Object AntivirusSignatureLastUpdated,
    AntivirusSignatureVersion, AntispywareSignatureVersion,
    NISSignatureVersion

# Aggiornare le definizioni
Update-MpSignature

# Aggiornamento da percorso specifico (per ambienti disconnessi)
Update-MpSignature -UpdateSource FileShares `
    -DefinitionUpdateFileSharesSources "\\fileserver\WDDefinitions"

# Eseguire una scansione completa
Start-MpScan -ScanType FullScan

# Eseguire una scansione rapida
Start-MpScan -ScanType QuickScan

# Eseguire una scansione personalizzata
Start-MpScan -ScanType CustomScan -ScanPath "D:\Downloads"
```

### Esclusioni

Le esclusioni sono necessarie per evitare falsi positivi e impatti sulle prestazioni per applicazioni note. Ogni esclusione aumenta la superficie di attacco, quindi vanno configurate con precisione.

```powershell
# Esclusioni per percorso
Add-MpPreference -ExclusionPath "D:\SQL\Data"
Add-MpPreference -ExclusionPath "D:\Hyper-V\VHDs"

# Esclusioni per estensione
Add-MpPreference -ExclusionExtension ".mdf", ".ldf", ".ndf"  # SQL Server
Add-MpPreference -ExclusionExtension ".vhdx", ".avhdx"       # Hyper-V

# Esclusioni per processo
Add-MpPreference -ExclusionProcess "sqlservr.exe"
Add-MpPreference -ExclusionProcess "vmms.exe"
Add-MpPreference -ExclusionProcess "vmwp.exe"

# Verificare le esclusioni configurate
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath
Get-MpPreference | Select-Object -ExpandProperty ExclusionExtension
Get-MpPreference | Select-Object -ExpandProperty ExclusionProcess

# Rimuovere un'esclusione
Remove-MpPreference -ExclusionPath "D:\Temp"
```

### Scansioni Pianificate

```powershell
# Configurare la scansione rapida giornaliera
Set-MpPreference -ScanScheduleQuickScanTime 12:00:00

# Configurare la scansione completa settimanale (domenica alle 02:00)
Set-MpPreference -ScanScheduleDay 1 -ScanScheduleTime 02:00:00

# Limitare l'utilizzo CPU durante la scansione
Set-MpPreference -ScanAvgCPULoadFactor 30  # Massimo 30% CPU

# Configurare il comportamento in caso di rilevamento
Set-MpPreference -ThreatDefaultAction_SevereLevels Quarantine
Set-MpPreference -ThreatDefaultAction_HighLevels Quarantine
Set-MpPreference -ThreatDefaultAction_ModerateLevels Quarantine
Set-MpPreference -ThreatDefaultAction_LowLevels Allow
```

---

## Real-Time Protection e Cloud Protection

### Real-Time Protection

La protezione in tempo reale monitora continuamente il filesystem, il registry e i processi per intercettare malware nel momento in cui viene creato, scaricato o eseguito.

```powershell
# Verificare e configurare la real-time protection
Set-MpPreference -DisableRealtimeMonitoring $false
Set-MpPreference -DisableBehaviorMonitoring $false
Set-MpPreference -DisableIOAVProtection $false  # Scansione download Internet
Set-MpPreference -DisableScriptScanning $false   # Scansione script (AMSI)

# Configurare il monitoraggio delle attività di rete
Set-MpPreference -DisableInboundConnectionFiltering $false
Set-MpPreference -EnableNetworkProtection Enabled
```

### Cloud-Delivered Protection

La protezione cloud invia metadati di file sospetti al Microsoft Intelligent Security Graph per un'analisi avanzata. Questo permette di bloccare minacce zero-day in pochi secondi dalla prima osservazione globale.

```powershell
# Abilitare la cloud protection
Set-MpPreference -MAPSReporting Advanced  # Invia metadati e campioni
Set-MpPreference -SubmitSamplesConsent SendAllSamples

# Configurare il cloud block timeout (tempo di attesa per il verdetto cloud)
Set-MpPreference -CloudBlockLevel HighPlus  # Livello di blocco aggressivo
Set-MpPreference -CloudExtendedTimeout 50    # Attesa extra di 50 secondi per verdetto cloud

# Block at First Sight — blocca file sconosciuti fino al verdetto cloud
# Richiede: Cloud Protection = Abilitato, Sample Submission = Automatico
# Abilitato per default quando cloud protection è attiva
```

### AMSI (Antimalware Scan Interface)

AMSI è un'interfaccia che permette alle applicazioni di inviare contenuto a Defender per la scansione. È particolarmente efficace contro il malware fileless che opera interamente in memoria tramite PowerShell, VBScript, JScript e macro Office.

```
Flusso AMSI:
┌──────────────┐     ┌───────────┐     ┌──────────────────┐
│ PowerShell   │────>│   AMSI    │────>│ Defender Engine   │
│ Script       │     │ Interface │     │ (scansione        │
│ (deoffuscato)│<────│           │<────│  contenuto)       │
│              │     │           │     │                   │
│ Blocco se    │     │           │     │ Signature + ML    │
│ malevolo     │     │           │     │ analysis          │
└──────────────┘     └───────────┘     └──────────────────┘
```

---

## WDAC vs AppLocker — Confronto Architetturale

La scelta tra Windows Defender Application Control (WDAC) e AppLocker è una decisione architetturale fondamentale per il whitelisting delle applicazioni. I due prodotti differiscono radicalmente per modello di esecuzione, sicurezza e gestibilità.

### Differenze Fondamentali

| Caratteristica | WDAC | AppLocker |
|---|---|---|
| **Livello di esecuzione** | Kernel-mode (driver ci.dll) | User-mode (servizio AppIDSvc) |
| **Aggirabilità da admin locale** | No — il kernel non può essere bypassato senza disabilitare Secure Boot | Sì — un admin locale può fermare il servizio AppIDSvc o modificare le regole |
| **Policy merge behavior** | Additive: policy multiple si sommano, il file è consentito se QUALSIASI policy lo autorizza | Ultima GPO applicata vince (LSDOU), le regole si sovrascrivono |
| **Supplemental policies** | Sì (da Windows 10 1903) — base + supplementari indipendenti | No — un unico set di regole per GPO |
| **Managed Installer** | Sì — autorizza automaticamente il software distribuito da MECM/Intune | No |
| **Intelligent Security Graph** | Sì — delegazione della reputazione al cloud Microsoft | No |
| **Controllo driver kernel** | Sì (KMCI — Kernel Mode Code Integrity) | No — AppLocker non controlla i driver |
| **Supporto UMCI** | Sì (User Mode Code Integrity) | Solo applicazioni utente |
| **Piattaforme** | Windows 10/11 Enterprise, Education, Pro (1903+), Server 2016+ | Windows 10/11 Enterprise, Education; Server 2016+ |
| **Gestione** | PowerShell, GPO, Intune, MECM | GPO, PowerShell (limitato) |
| **Complessità** | Alta — richiede pianificazione, testing approfondito, golden image | Media — regole più intuitive, deploy più semplice |
| **Raccomandazione Microsoft** | Soluzione primaria per nuovi deployment | Legacy, supportato ma non evoluto |

Fonte: https://learn.microsoft.com/en-us/windows/security/application-security/application-control/windows-defender-application-control/wdac-and-applocker-overview (consultato: 2026-05-23)

### Quando Usare AppLocker

AppLocker resta appropriato in scenari specifici:

- **Ambienti senza Secure Boot** — WDAC senza Secure Boot perde la protezione kernel
- **Policy per utente** — AppLocker supporta regole per utente/gruppo AD; WDAC è device-wide
- **Transizione graduale** — AppLocker come primo passo verso il whitelisting, poi migrazione a WDAC
- **Requisiti di DLL rules** — AppLocker può controllare singole DLL (con impatto prestazionale), utile per ambienti con requisiti di compliance specifici

### Coesistenza WDAC + AppLocker

WDAC e AppLocker possono coesistere sullo stesso sistema. WDAC opera a livello kernel (enforcement più forte), AppLocker a livello utente (regole più granulari per utente/gruppo). In caso di conflitto, WDAC ha precedenza: se WDAC blocca un file, AppLocker non può autorizzarlo.

```powershell
# Verificare lo stato di entrambi i sistemi
# WDAC: verificare le policy Code Integrity attive
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
    Select-Object CodeIntegrityPolicyEnforcementStatus,
    UsermodeCodeIntegrityPolicyEnforcementStatus

# AppLocker: verificare il servizio e le regole
Get-Service AppIDSvc | Select-Object Status, StartType
Get-AppLockerPolicy -Effective | Select-Object -ExpandProperty RuleCollections
```

---

## Attack Surface Reduction (ASR) Rules

Le ASR rules bloccano comportamenti specifici comunemente utilizzati dal malware e dagli attacchi basati su Office, script e credential theft. Ogni regola ha un GUID univoco e può essere configurata in tre modalità: Block, Audit e Warn.

### Regole Principali

```powershell
# Tabella delle ASR rules più importanti
$asrRules = @{
    # Bloccare creazione di processi figlio da applicazioni Office
    "D4F940AB-401B-4EFC-AADC-AD5F3C50688A" = "Block Office apps from creating child processes"

    # Bloccare le applicazioni Office dalla creazione di contenuto eseguibile
    "3B576869-A4EC-4529-8536-B80A7769E899" = "Block Office apps from creating executable content"

    # Bloccare le applicazioni Office dall'iniettare codice in altri processi
    "75668C1F-73B5-4CF0-BB93-3ECF5CB7CC84" = "Block Office apps from injecting into other processes"

    # Bloccare JavaScript/VBScript dal lanciare contenuto scaricato
    "D3E037E1-3EB8-44C8-A917-57927947596D" = "Block JS/VBS from launching downloaded executable content"

    # Bloccare l'esecuzione di script potenzialmente offuscati
    "5BEB7EFE-FD9A-4556-801D-275E5FFC04CC" = "Block execution of potentially obfuscated scripts"

    # Bloccare chiamate API Win32 da macro Office
    "92E97FA1-2EDF-4476-BDD6-9DD0B4DDDC7B" = "Block Win32 API calls from Office macros"

    # Bloccare il furto di credenziali da lsass.exe
    "9E6C4E1F-7D60-472F-BA1A-A39EF669E4B2" = "Block credential stealing from LSASS"

    # Bloccare i processi non attendibili da USB
    "B2B3F03D-6A65-4F7B-A9C7-1C7EF74A9BA4" = "Block untrusted processes from USB"

    # Bloccare la creazione di processi da WMI event subscription
    "E6DB77E5-3DF2-4CF1-B95A-636979351E5B" = "Block process creations from WMI"

    # Bloccare la persistenza tramite WMI event subscription
    "D1E49AAC-8F56-4280-B9BA-993A6D77406C" = "Block persistence through WMI event subscription"

    # Usare advanced protection contro ransomware
    "C1DB55AB-C21A-4637-BB3F-A12568109D35" = "Use advanced protection against ransomware"
}

# Abilitare tutte le regole ASR in modalità Block
foreach ($ruleId in $asrRules.Keys) {
    Add-MpPreference -AttackSurfaceReductionRules_Ids $ruleId `
        -AttackSurfaceReductionRules_Actions Enabled
}

# Abilitare una regola specifica in modalità Audit (per testing)
Add-MpPreference -AttackSurfaceReductionRules_Ids "D4F940AB-401B-4EFC-AADC-AD5F3C50688A" `
    -AttackSurfaceReductionRules_Actions AuditMode

# Verificare le regole ASR configurate
Get-MpPreference | Select-Object -ExpandProperty AttackSurfaceReductionRules_Ids
Get-MpPreference | Select-Object -ExpandProperty AttackSurfaceReductionRules_Actions

# Monitorare gli eventi ASR nel log
Get-WinEvent -LogName "Microsoft-Windows-Windows Defender/Operational" |
    Where-Object { $_.Id -in 1121, 1122 } |
    Select-Object TimeCreated, Id,
        @{N='Action';E={if($_.Id -eq 1121){'Blocked'}else{'Audited'}}},
        Message | Format-Table -Wrap
```

### Configurazione tramite GPO

```
Computer Configuration → Policies → Administrative Templates
    → Windows Components → Microsoft Defender Antivirus
        → Microsoft Defender Exploit Guard → Attack Surface Reduction:
            - Configure Attack Surface Reduction rules: Enabled
              (Specificare GUID=Action per ogni regola)
```

### Esclusioni ASR

```powershell
# Escludere un processo specifico dalle regole ASR
Add-MpPreference -AttackSurfaceReductionOnlyExclusions "C:\App\TrustedApp.exe"

# Escludere un percorso
Add-MpPreference -AttackSurfaceReductionOnlyExclusions "C:\Development\Projects"
```

### ASR Rules — Implementazione Graduale Raccomandata

L'attivazione delle ASR rules richiede un approccio graduale per evitare interruzioni operative:

```
Fase 1 — Audit (settimana 1-4):
├── Abilitare TUTTE le regole in Audit Mode
├── Monitorare Event ID 1122 nel log operativo
├── Identificare i falsi positivi
└── Documentare le applicazioni che richiedono esclusioni

Fase 2 — Warn per regole ad alto impatto (settimana 5-6):
├── Passare le regole a basso rischio in Block Mode:
│   ├── Block executable content from email client
│   ├── Block untrusted processes from USB
│   └── Use advanced protection against ransomware
├── Passare le regole ad alto impatto in Warn Mode:
│   ├── Block Office from creating child processes
│   ├── Block Win32 API calls from Office macros
│   └── Block credential stealing from LSASS
└── Raccogliere feedback dagli utenti

Fase 3 — Block completo (settimana 7+):
├── Passare tutte le regole in Block Mode
├── Mantenere le esclusioni configurate
├── Monitorare continuamente Event ID 1121
└── Revisione periodica trimestrale delle esclusioni
```

```powershell
# Script per implementare la fase graduale
function Set-ASRPhase {
    param(
        [ValidateSet("Audit", "Warn", "Block")]
        [string]$Phase
    )

    $actionMap = @{
        "Audit" = "AuditMode"
        "Warn"  = "Warn"
        "Block" = "Enabled"
    }

    $rules = @(
        "D4F940AB-401B-4EFC-AADC-AD5F3C50688A",  # Office child processes
        "3B576869-A4EC-4529-8536-B80A7769E899",  # Office executable content
        "75668C1F-73B5-4CF0-BB93-3ECF5CB7CC84",  # Office code injection
        "D3E037E1-3EB8-44C8-A917-57927947596D",  # JS/VBS downloaded content
        "5BEB7EFE-FD9A-4556-801D-275E5FFC04CC",  # Obfuscated scripts
        "92E97FA1-2EDF-4476-BDD6-9DD0B4DDDC7B",  # Win32 API from macros
        "9E6C4E1F-7D60-472F-BA1A-A39EF669E4B2",  # Credential stealing LSASS
        "B2B3F03D-6A65-4F7B-A9C7-1C7EF74A9BA4",  # Untrusted USB processes
        "C1DB55AB-C21A-4637-BB3F-A12568109D35",  # Advanced ransomware protection
        "E6DB77E5-3DF2-4CF1-B95A-636979351E5B",  # WMI process creation
        "D1E49AAC-8F56-4280-B9BA-993A6D77406C"   # WMI persistence
    )

    $action = $actionMap[$Phase]
    foreach ($rule in $rules) {
        Add-MpPreference -AttackSurfaceReductionRules_Ids $rule `
            -AttackSurfaceReductionRules_Actions $action
    }
    Write-Output "ASR rules impostate in modalità: $Phase ($action)"
}

# Uso:
Set-ASRPhase -Phase "Audit"    # Fase 1
Set-ASRPhase -Phase "Warn"     # Fase 2
Set-ASRPhase -Phase "Block"    # Fase 3
```

### ASR Rules — Report di Conformità

```powershell
# Generare un report delle ASR rules con stato e statistiche
function Get-ASRReport {
    $prefs = Get-MpPreference
    $ruleNames = @{
        "D4F940AB-401B-4EFC-AADC-AD5F3C50688A" = "Block Office child processes"
        "3B576869-A4EC-4529-8536-B80A7769E899" = "Block Office executable content"
        "75668C1F-73B5-4CF0-BB93-3ECF5CB7CC84" = "Block Office code injection"
        "D3E037E1-3EB8-44C8-A917-57927947596D" = "Block JS/VBS downloaded content"
        "5BEB7EFE-FD9A-4556-801D-275E5FFC04CC" = "Block obfuscated scripts"
        "92E97FA1-2EDF-4476-BDD6-9DD0B4DDDC7B" = "Block Win32 API from macros"
        "9E6C4E1F-7D60-472F-BA1A-A39EF669E4B2" = "Block credential stealing from LSASS"
        "B2B3F03D-6A65-4F7B-A9C7-1C7EF74A9BA4" = "Block untrusted USB processes"
        "C1DB55AB-C21A-4637-BB3F-A12568109D35" = "Advanced ransomware protection"
        "E6DB77E5-3DF2-4CF1-B95A-636979351E5B" = "Block WMI process creation"
        "D1E49AAC-8F56-4280-B9BA-993A6D77406C" = "Block WMI persistence"
        "BE9BA2D9-53EA-4CDC-84E5-9B1EEEE46550" = "Block executable content from email"
        "01443614-CD74-433A-B99E-2ECDC07BFC25" = "Block exe unless meet criteria"
        "26190899-1602-49E8-8B27-EB1D0A1CE869" = "Block Office comm app child process"
        "7674BA52-37EB-4A4F-A9A1-F0F9A1619A2C" = "Block Adobe Reader child processes"
        "56A863A9-875E-4185-98A7-B882C64B5CE5" = "Block abuse of exploited vulnerable signed drivers"
    }

    $actionNames = @{ 0 = "Disabled"; 1 = "Block"; 2 = "Audit"; 6 = "Warn" }

    $ids = $prefs.AttackSurfaceReductionRules_Ids
    $actions = $prefs.AttackSurfaceReductionRules_Actions

    if (-not $ids) {
        Write-Warning "Nessuna regola ASR configurata."
        return
    }

    for ($i = 0; $i -lt $ids.Count; $i++) {
        $ruleId = $ids[$i].ToUpper()
        $action = if ($i -lt $actions.Count) { $actions[$i] } else { 0 }
        [PSCustomObject]@{
            RuleId   = $ruleId
            Name     = if ($ruleNames[$ruleId]) { $ruleNames[$ruleId] } else { "Unknown" }
            Mode     = if ($actionNames.ContainsKey([int]$action)) { $actionNames[[int]$action] } else { $action }
        }
    }
}

Get-ASRReport | Format-Table -AutoSize
```

---

## ASR Rules — Mappatura MITRE ATT&CK Completa

Ogni regola ASR mappa direttamente a una o più tecniche MITRE ATT&CK. Questa mappatura è essenziale per comprendere quale superficie di attacco viene ridotta e per giustificare l'attivazione delle regole durante i risk assessment.

| GUID Regola | Nome Regola | Tecnica MITRE | Tactic | Impatto Tipico |
|---|---|---|---|---|
| `D4F940AB-401B-4EFC-AADC-AD5F3C50688A` | Block Office apps from creating child processes | T1566.001 (Spearphishing Attachment) | Initial Access | Alto — molte macro legittime creano processi |
| `3B576869-A4EC-4529-8536-B80A7769E899` | Block Office apps from creating executable content | T1204.002 (Malicious File) | Execution | Medio — blocca dropper da Office |
| `75668C1F-73B5-4CF0-BB93-3ECF5CB7CC84` | Block Office apps from injecting code into other processes | T1055 (Process Injection) | Defense Evasion | Basso — raro per applicazioni legittime |
| `D3E037E1-3EB8-44C8-A917-57927947596D` | Block JS/VBS from launching downloaded executable content | T1059.007 (JavaScript) | Execution | Medio — script legittimi di deploy |
| `5BEB7EFE-FD9A-4556-801D-275E5FFC04CC` | Block execution of potentially obfuscated scripts | T1027 (Obfuscated Files or Information) | Defense Evasion | Alto — può bloccare script minificati legittimi |
| `92E97FA1-2EDF-4476-BDD6-9DD0B4DDDC7B` | Block Win32 API calls from Office macros | T1106 (Native API) | Execution | Alto — macro complesse usano Win32 API |
| `9E6C4E1F-7D60-472F-BA1A-A39EF669E4B2` | Block credential stealing from LSASS | T1003.001 (LSASS Memory) | Credential Access | Basso — rarissimi FP, altamente raccomandato |
| `B2B3F03D-6A65-4F7B-A9C7-1C7EF74A9BA4` | Block untrusted and unsigned processes from USB | T1091 (Replication Through Removable Media) | Lateral Movement | Basso — blocca solo unsigned da USB |
| `BE9BA2D9-53EA-4CDC-84E5-9B1EEEE46550` | Block executable content from email client and webmail | T1566.001 (Spearphishing Attachment) | Initial Access | Medio — allegati legittimi bloccati |
| `01443614-CD74-433A-B99E-2ECDC07BFC25` | Block executable files unless they meet prevalence, age, or trusted list criteria | T1204.002 (Malicious File) | Execution | Alto — blocca exe rari/nuovi |
| `C1DB55AB-C21A-4637-BB3F-A12568109D35` | Use advanced protection against ransomware | T1486 (Data Encrypted for Impact) | Impact | Basso — analisi reputazione pre-esecuzione |
| `26190899-1602-49E8-8B27-EB1D0A1CE869` | Block Office communication application from creating child processes | T1566.001 (Spearphishing Attachment) | Initial Access | Basso — Outlook non deve creare processi figlio |
| `7674BA52-37EB-4A4F-A9A1-F0F9A1619A2C` | Block Adobe Reader from creating child processes | T1203 (Exploitation for Client Execution) | Execution | Basso — PDF exploit mitigation |
| `E6DB77E5-3DF2-4CF1-B95A-636979351E5B` | Block process creations originating from PSExec and WMI commands | T1047 (Windows Management Instrumentation) | Execution | Medio — tool di gestione legittimi usano WMI |
| `D1E49AAC-8F56-4280-B9BA-993A6D77406C` | Block persistence through WMI event subscription | T1546.003 (WMI Event Subscription) | Persistence | Basso — tecnica rara per software legittimo |
| `56A863A9-875E-4185-98A7-B882C64B5CE5` | Block abuse of exploited vulnerable signed drivers | T1068 (Exploitation for Privilege Escalation) | Privilege Escalation | Basso — usa la block list Microsoft |
| `33ddedf1-c6e0-47cb-833e-de6133960387` | Block rebooting machine in Safe Mode | T1562.009 (Safe Mode Boot) | Defense Evasion | Basso — raro per utenti normali |
| `c0033c00-d16d-4114-a5a0-dc9b3a7d2ceb` | Block use of copied or impersonated system tools | T1036.003 (Rename System Utilities) | Defense Evasion | Medio — tool copiati per automazione |

Fonte: https://learn.microsoft.com/en-us/defender-endpoint/attack-surface-reduction-rules-reference (consultato: 2026-05-23)
Fonte MITRE: https://attack.mitre.org/techniques/enterprise/ (consultato: 2026-05-23)

### ASR Rules — Deployment via Intune

La distribuzione tramite Intune è il metodo raccomandato per ambienti enterprise perché offre reporting centralizzato, compliance monitoring e rollback controllato.

```
Endpoint Manager → Endpoint security → Attack surface reduction:

1. Creare un profilo ASR:
   Platform: Windows 10 and later
   Profile type: Attack surface reduction rules

2. Configurare ogni regola individualmente:
   Regola                                    → Modalità
   ──────────────────────────────────────────────────────
   Block Office child processes              → Block
   Block Office executable content           → Block
   Block Office code injection               → Block
   Block JS/VBS downloaded content           → Block
   Block obfuscated scripts                  → Audit (alto FP)
   Block Win32 API from macros               → Warn (alto FP)
   Block credential stealing from LSASS      → Block
   Block untrusted USB processes             → Block
   Block executable content from email       → Block
   Block exe unless criteria met             → Audit (alto FP)
   Advanced ransomware protection            → Block
   Block WMI process creation                → Audit (impatto IT ops)
   Block WMI persistence                     → Block
   Block vulnerable signed drivers           → Block

3. Assegnare a gruppi:
   - Pilota (IT team) → tutte le regole in Block per 2 settimane
   - Produzione fase 1 → regole a basso impatto in Block
   - Produzione fase 2 → tutte le regole in Block con esclusioni
```

---

## Controlled Folder Access

Controlled Folder Access protegge le cartelle designate da modifiche non autorizzate, bloccando l'accesso in scrittura da processi non attendibili. È una difesa efficace contro il ransomware.

```powershell
# Abilitare Controlled Folder Access
Set-MpPreference -EnableControlledFolderAccess Enabled

# Modalità Audit (raccomandato prima dell'attivazione in produzione)
Set-MpPreference -EnableControlledFolderAccess AuditMode

# Aggiungere cartelle protette (oltre a quelle di default)
Add-MpPreference -ControlledFolderAccessProtectedFolders "D:\FinanceData"
Add-MpPreference -ControlledFolderAccessProtectedFolders "E:\Progetti"

# Cartelle protette di default:
# - Documenti, Desktop, Immagini, Video, Musica, Preferiti
# - OneDrive (cartelle di sincronizzazione)

# Aggiungere applicazioni consentite (whitelist)
Add-MpPreference -ControlledFolderAccessAllowedApplications "C:\Program Files\CustomApp\app.exe"
Add-MpPreference -ControlledFolderAccessAllowedApplications "C:\Program Files\Backup\backup.exe"

# Verificare la configurazione
Get-MpPreference | Select-Object EnableControlledFolderAccess,
    ControlledFolderAccessProtectedFolders,
    ControlledFolderAccessAllowedApplications

# Monitorare i blocchi
Get-WinEvent -LogName "Microsoft-Windows-Windows Defender/Operational" |
    Where-Object { $_.Id -eq 1123 -or $_.Id -eq 1124 } |
    Select-Object TimeCreated, Message | Format-Table -Wrap
```

---

## Network Protection — Approfondimento

Network Protection estende le capacità di Microsoft SmartScreen a livello di stack di rete, operando come un filtro trasparente su tutte le connessioni TCP/IP in uscita — non solo quelle dei browser. Questa sezione approfondisce gli aspetti avanzati non trattati nella sezione base.

### Web Content Filtering

Quando combinato con MDE Plan 2, Network Protection abilita il **Web Content Filtering** — la capacità di bloccare l'accesso a categorie di siti web tramite policy centralizzate:

```
Categorie disponibili (configurabili nel portale MDE):
├── Adult Content
│   ├── Nudity, Pornography, Violence
├── High Bandwidth
│   ├── Streaming Media, Peer-to-Peer
├── Legal Liability
│   ├── Gambling, Weapons, Drugs, Hacking
├── Leisure
│   ├── Games, Social Networking, Chat
└── Uncategorized
    └── Newly registered domains, Parked domains

Configurazione:
security.microsoft.com → Settings → Endpoints → Web content filtering
→ Add policy → Selezionare categorie → Assegnare a device groups
```

### Custom Indicators per Network Protection

Oltre alle categorie predefinite, è possibile creare indicatori personalizzati che Network Protection applicherà:

```powershell
# Tipi di indicatori di rete supportati (gestiti da portale MDE o API):
# - URL: blocco/audit di URL specifiche
# - Domain: blocco/audit di interi domini
# - IP Address: blocco/audit di indirizzi IP

# Esempio di creazione indicatore via API (richiede MDE Plan 2)
$indicator = @{
    indicatorValue     = "suspicious-cdn.example.com"
    indicatorType      = "DomainName"
    action             = "AlertAndBlock"
    title              = "C2 domain - Campagna APT rilevata"
    description        = "Blocco preventivo dominio C2 - Threat Intel Team"
    severity           = "High"
    generateAlert      = $true
    expirationTime     = (Get-Date).AddDays(30).ToString("yyyy-MM-ddTHH:mm:ssZ")
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://api.securitycenter.microsoft.com/api/indicators" `
    -Method POST -Headers @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" } `
    -Body $indicator
```

### Network Protection — Event ID Specifici

| Event ID | Log | Significato |
|---|---|---|
| 1125 | Windows Defender/Operational | Connessione bloccata da Network Protection |
| 1126 | Windows Defender/Operational | Connessione auditata (modalità audit) |
| 5007 | Windows Defender/Operational | Modifica configurazione Network Protection |

Fonte: https://learn.microsoft.com/en-us/defender-endpoint/network-protection (consultato: 2026-05-23)

---

## Exploit Protection — Configurazione Avanzata

### Mitigazioni Sistema-Wide vs Per-Processo

Exploit Protection offre due livelli di configurazione: mitigazioni **system-wide** (applicate a tutti i processi) e mitigazioni **per-processo** (override specifici per singole applicazioni).

```powershell
# ─── CONFIGURAZIONE SYSTEM-WIDE ───

# DEP (Data Execution Prevention)
# Impedisce l'esecuzione di codice da pagine di memoria marcate come dati
Set-ProcessMitigation -System -Enable DEP
# Modalità OptOut: DEP attivo per tutti tranne quelli esplicitamente esclusi
Set-ProcessMitigation -System -Enable DEP, ATLThunkEmulation

# ASLR (Address Space Layout Randomization)
# Randomizza gli indirizzi base di immagini, stack, heap
Set-ProcessMitigation -System -Enable ForceRelocateImages  # Bottom-Up ASLR
Set-ProcessMitigation -System -Enable HighEntropy           # High Entropy ASLR (64-bit)

# CFG (Control Flow Guard)
# Valida i target dei salti indiretti (call/jmp tramite puntatore)
Set-ProcessMitigation -System -Enable CFG
Set-ProcessMitigation -System -Enable StrictCFG  # Modalità strict: blocca target non registrati

# SEHOP (Structured Exception Handler Overwrite Protection)
# Protegge la catena SEH dalla corruzione
Set-ProcessMitigation -System -Enable SEHOP

# ─── CONFIGURAZIONE PER-PROCESSO ───

# Configurazione specifica per applicazioni critiche
Set-ProcessMitigation -Name "iexplore.exe" -Enable `
    DEP, SEHOP, ForceRelocateImages, HighEntropy, CFG, `
    HeapTerminate, BlockDynamicCode, ExtensionPointDisable

# Configurazione per browser moderni (già compilati con mitigazioni)
Set-ProcessMitigation -Name "msedge.exe" -Enable `
    DEP, CFG, ForceRelocateImages, HighEntropy

# ─── EXPORT/IMPORT PER DISTRIBUZIONE GPO ───

# Esportare la configurazione completa in XML
Get-ProcessMitigation -RegistryConfigFilePath "C:\Security\ExploitProtection-Config.xml"

# Importare (applicare) su un altro sistema
Set-ProcessMitigation -PolicyFilePath "C:\Security\ExploitProtection-Config.xml"

# Distribuire via GPO:
# Computer Configuration → Administrative Templates → Windows Components
#   → Windows Defender Exploit Guard → Exploit Protection
#     → "Use a common set of exploit protection settings": Enabled
#     → File path: \\server\share\ExploitProtection-Config.xml
```

### Tabella Dettagliata delle Mitigazioni

| Mitigazione | Tipo | Descrizione Tecnica | Compatibilità |
|---|---|---|---|
| **DEP** | Sistema/Processo | Marca pagine dati come NX (No eXecute); CPU trap su esecuzione da dati | Universale, rarissime incompatibilità |
| **ASLR Bottom-Up** | Sistema/Processo | Randomizza base di allocazione per heap, stack, memory-mapped files | Alta — problemi con DLL legacy senza /DYNAMICBASE |
| **ASLR High Entropy** | Sistema/Processo | Usa 1 TB di entropia per 64-bit ASLR vs 256 MB standard | Solo 64-bit; alta compatibilità |
| **CFG** | Processo | Valida salti indiretti contro bitmap di target validi | Richiede compilazione con /guard:cf; binari legacy ignorati |
| **SEHOP** | Processo | Inserisce un cookie alla fine della catena SEH per rilevare sovrascritture | Alta — problemi con software che manipola SEH manualmente |
| **EAF** | Processo | Filtra accesso alle export table di kernel32/ntdll/kernelbase | Media — può rompere debugger, tool di instrumentazione |
| **IAF** | Processo | Filtra accesso alle import table | Media — stesse considerazioni di EAF |
| **ACG** | Processo | Blocca allocazione di pagine W+X (writable e executable) | Bassa — incompatibile con JIT (Java, .NET, V8) |
| **Heap Terminate** | Processo | Termina il processo se viene rilevata corruzione dell'heap | Alta — crash preventivo, nessun FP |
| **Block Dynamic Code** | Processo | Impedisce la generazione di codice runtime (VirtualAlloc + PAGE_EXECUTE) | Bassa — incompatibile con JIT e plugin dinamici |

Fonte: https://learn.microsoft.com/en-us/defender-endpoint/exploit-protection-reference (consultato: 2026-05-23)

---

## Tamper Protection — Deep Dive

Tamper Protection è un meccanismo di auto-protezione di Defender che impedisce a qualsiasi processo locale — inclusi quelli con privilegi SYSTEM — di modificare le impostazioni di sicurezza. Questa sezione approfondisce il modello di gestione e le implicazioni operative.

### Modello di Gestione: Solo Cloud

Tamper Protection è progettata per essere gestita esclusivamente dal cloud:

```
Metodi di gestione supportati:
├── Microsoft 365 Defender Portal (security.microsoft.com)
│   └── Settings → Endpoints → Advanced features → Tamper Protection
├── Microsoft Intune
│   └── Endpoint security → Antivirus → Tamper Protection: Enabled
├── Microsoft 365 Defender API
│   └── POST /api/settings/tamperProtection
└── NON supportati (bloccati quando TP è attiva):
    ├── PowerShell Set-MpPreference
    ├── Group Policy (GPO)
    ├── Registry Editor (regedit)
    ├── WMI/CIM
    └── Script locali di qualsiasi tipo
```

### Cosa Protegge Tamper Protection

Quando attiva, Tamper Protection impedisce modifiche a:

1. **DisableRealtimeMonitoring** — non è possibile disabilitare la protezione real-time
2. **DisableBehaviorMonitoring** — il monitoraggio comportamentale resta attivo
3. **DisableIOAVProtection** — la scansione dei download non può essere disattivata
4. **DisableOnAccessProtection** — la protezione on-access resta abilitata
5. **CloudBlockLevel** — il livello di protezione cloud non può essere ridotto
6. **MAPSReporting** — non è possibile disabilitare MAPS
7. **ExclusionPath/Extension/Process** — le esclusioni non possono essere modificate localmente
8. **Aggiornamenti di Security Intelligence** — non possono essere cancellati o degradati

### Implicazioni Operative

```
Scenario: un team IT deve aggiungere un'esclusione urgente.

CON Tamper Protection attiva:
1. L'admin NON può usare Set-MpPreference localmente → fallisce silenziosamente
2. L'admin deve accedere al portale Intune o MDE
3. Creare/modificare la policy antivirus con la nuova esclusione
4. Attendere la sincronizzazione Intune (default: 8 ore; forzabile con Sync)
5. Verificare l'applicazione sul client

SENZA Tamper Protection:
1. L'admin esegue Set-MpPreference -ExclusionPath "X:\path" → funziona
2. MA: anche il malware può eseguire lo stesso comando
3. Rischio: malware disabilita Defender prima di eseguire il payload
```

Fonte: https://learn.microsoft.com/en-us/defender-endpoint/prevent-changes-to-security-settings-with-tamper-protection (consultato: 2026-05-23)

---

## Microsoft Defender for Endpoint (EDR)

Microsoft Defender for Endpoint (MDE) è la piattaforma EDR (Endpoint Detection and Response) enterprise di Microsoft. Va oltre la protezione antivirus tradizionale fornendo visibilità completa sulle attività degli endpoint, rilevamento di minacce avanzate, capacità di threat hunting e risposta automatizzata agli incidenti.

### Architettura

```
┌─────────────────────────────────────────────────────────────┐
│                   Microsoft 365 Defender Portal              │
│                   (security.microsoft.com)                   │
├────────────┬──────────────┬──────────────┬──────────────────┤
│ Endpoint   │ Email        │ Identity     │ Cloud Apps       │
│ (MDE)      │ (MDO)        │ (MDI)        │ (MDA)            │
├────────────┴──────────────┴──────────────┴──────────────────┤
│              Microsoft Intelligent Security Graph             │
│         (Correlazione segnali, ML, Threat Intelligence)      │
├──────────────────────────────────────────────────────────────┤
│                        Endpoint Sensor                        │
│   ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│   │ Process  │ Network  │ File     │ Registry │ Memory   │  │
│   │ creation │ activity │ creation │ changes  │ activity │  │
│   │ events   │ events   │ events   │ events   │ events   │  │
│   └──────────┴──────────┴──────────┴──────────┴──────────┘  │
│                     Windows Endpoint                          │
└──────────────────────────────────────────────────────────────┘
```

### Onboarding

L'onboarding degli endpoint in MDE può avvenire tramite diverse modalità:

```powershell
# Metodo 1: Script di onboarding locale (scaricato dal portale MDE)
# Il pacchetto contiene WindowsDefenderATPLocalOnboardingScript.cmd
& "C:\Temp\WindowsDefenderATPLocalOnboardingScript.cmd"

# Metodo 2: Via Group Policy
# Copiare il pacchetto in SYSVOL e configurare una Scheduled Task via GPO

# Metodo 3: Via Microsoft Intune
# Configurazione automatica tramite profilo di configurazione endpoint

# Metodo 4: Via Microsoft Endpoint Configuration Manager (MECM/SCCM)
# Client settings → Endpoint Protection → Windows Defender ATP

# Verificare lo stato di onboarding
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows Advanced Threat Protection\Status" |
    Select-Object OnboardingState, OrgId

# Test di rilevamento (generare un alert di test)
powershell.exe -NoExit -ExecutionPolicy Bypass -WindowStyle Hidden `
    (New-Object System.Net.WebClient).DownloadFile(
        'http://127.0.0.1/1.exe', 'C:\test-MDATP-test\invoice.exe'
    )
```

### Advanced Hunting (KQL)

Microsoft Defender for Endpoint utilizza Kusto Query Language (KQL) per il threat hunting avanzato:

```kusto
// Trovare processi PowerShell sospetti con encoding base64
DeviceProcessEvents
| where Timestamp > ago(7d)
| where FileName =~ "powershell.exe"
| where ProcessCommandLine has_any ("-encodedcommand", "-enc", "-e ")
| project Timestamp, DeviceName, AccountName, ProcessCommandLine
| order by Timestamp desc

// Rilevare lateral movement via PsExec
DeviceProcessEvents
| where Timestamp > ago(24h)
| where FileName =~ "psexec.exe" or FileName =~ "psexesvc.exe"
| project Timestamp, DeviceName, AccountName, ProcessCommandLine, InitiatingProcessFileName

// Identificare download sospetti da browser
DeviceFileEvents
| where Timestamp > ago(7d)
| where InitiatingProcessFileName in~ ("chrome.exe", "msedge.exe", "firefox.exe")
| where FileName endswith ".exe" or FileName endswith ".dll" or FileName endswith ".ps1"
| where FolderPath startswith @"C:\Users"
| summarize DownloadCount = count() by FileName, SHA256
| where DownloadCount < 5
| order by DownloadCount

// Monitorare le connessioni a IP noti come malevoli
DeviceNetworkEvents
| where Timestamp > ago(24h)
| where RemoteIPType == "Public"
| where ActionType == "ConnectionSuccess"
| summarize ConnectionCount = count(), Devices = make_set(DeviceName)
    by RemoteIP, RemotePort, InitiatingProcessFileName
| where ConnectionCount > 100
| order by ConnectionCount desc
```

### Live Response

Live Response consente agli analisti SOC di connettersi in tempo reale a un endpoint per investigare e rispondere a incidenti direttamente dal portale MDE:

```
Comandi Live Response disponibili:

Investigazione:
├── dir                    — Listare file e directory
├── fileinfo <path>        — Informazioni dettagliate su un file
├── findfile <name>        — Cercare un file sul dispositivo
├── getfile <path>         — Scaricare un file dal dispositivo per analisi
├── processes              — Listare processi in esecuzione
├── registry               — Query chiavi di registro
├── scheduledtasks         — Listare scheduled tasks
├── services               — Listare servizi
├── trace                  — Abilitare logging diagnostico
└── connections            — Connessioni di rete attive

Remediation (richiede ruolo elevato):
├── remediate file <path>  — Quarantena file
├── remediate process <pid>— Terminare processo
├── undo file <path>       — Ripristinare file dalla quarantena
├── run <script>           — Eseguire script PowerShell dalla libreria
└── putfile <path>         — Caricare file dalla libreria sul dispositivo
```

### Device Isolation

Per contenere una minaccia attiva, è possibile isolare un dispositivo dalla rete mantenendo la connettività al servizio MDE:

```powershell
# Isolare un dispositivo tramite API (richiede MDE Plan 2)
$headers = @{
    Authorization  = "Bearer $accessToken"
    "Content-Type" = "application/json"
}

$body = @{
    Comment = "Isolamento per investigazione INC-1234 - possibile ransomware"
    IsolationType = "Full"  # Full = nessun traffico tranne MDE; Selective = consente Outlook, Teams
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://api.securitycenter.microsoft.com/api/machines/$machineId/isolate" `
    -Method POST -Headers $headers -Body $body

# Rilasciare l'isolamento dopo l'investigazione
$releaseBody = @{
    Comment = "Investigazione INC-1234 completata - minaccia contenuta"
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://api.securitycenter.microsoft.com/api/machines/$machineId/unisolate" `
    -Method POST -Headers $headers -Body $releaseBody
```

---

## Threat Analytics e Automated Investigation

### Threat Analytics

Threat Analytics nel portale MDE fornisce report curati dal team Microsoft Threat Intelligence sulle minacce attive globali, con indicazione dell'esposizione dell'organizzazione e raccomandazioni di mitigazione.

Ogni report include:
- **Analyst report** — Descrizione tecnica della minaccia
- **Impacted assets** — Dispositivi dell'organizzazione esposti
- **Mitigations** — Azioni consigliate (patching, configurazione ASR, etc.)
- **Detection details** — Regole di rilevamento applicabili

### Automated Investigation and Response (AIR)

AIR automatizza l'investigazione degli alert, riducendo il carico sugli analisti SOC. Quando viene generato un alert, AIR:

1. Raccoglie evidenze automaticamente (processi, file, network connections)
2. Analizza le evidenze con playbook automatizzati
3. Determina il verdetto (Malicious, Suspicious, No threats found)
4. Propone o esegue azioni di remediation (quarantena file, isolamento dispositivo, blocco URL)

```
Flusso AIR:
Alert → Investigazione Automatica → Raccolta Evidenze → Analisi
    → Verdetto → Azione di Remediation (automatica o con approvazione)
```

Le azioni di remediation disponibili includono:
- Quarantine file
- Stop process and quarantine
- Remove registry key
- Isolate device from network
- Block URL/IP at network level
- Run antivirus scan

---

## EDR — Telemetria e Advanced Hunting Avanzato

### Raccolta Telemetria

Il sensore EDR di MDE raccoglie telemetria continua dagli endpoint senza agenti addizionali (utilizza il servizio `Sense`). I dati vengono trasmessi al cloud Microsoft e resi disponibili nelle tabelle di Advanced Hunting.

```
Tabelle Advanced Hunting principali:
┌──────────────────────────┬─────────────────────────────────────────────────┐
│ Tabella                  │ Dati raccolti                                   │
├──────────────────────────┼─────────────────────────────────────────────────┤
│ DeviceProcessEvents      │ Creazione processi, command line, parent proc.  │
│ DeviceNetworkEvents      │ Connessioni TCP/UDP, DNS, protocollo            │
│ DeviceFileEvents         │ Creazione/modifica/eliminazione file            │
│ DeviceRegistryEvents     │ Creazione/modifica chiavi e valori di registro  │
│ DeviceLogonEvents        │ Login interattivi, di rete, via RDP             │
│ DeviceImageLoadEvents    │ Caricamento DLL nei processi                    │
│ DeviceEvents             │ Eventi generici (USB, PnP, AMSI, etc.)         │
│ DeviceInfo               │ Informazioni hw/sw del dispositivo              │
│ DeviceAlertEvents        │ Alert generati e stato investigazione           │
│ DeviceTvmSoftwareInventory│ Inventario software installato                 │
│ DeviceTvmVulnerabilities │ Vulnerabilità rilevate (CVE)                    │
│ EmailEvents              │ Email ricevute/inviate (con MDO)                │
│ IdentityLogonEvents      │ Autenticazioni AD (con MDI)                    │
└──────────────────────────┴─────────────────────────────────────────────────┘
```

### Query KQL Avanzate per Threat Hunting

```kusto
// ─── RILEVARE PERSISTENCE VIA SCHEDULED TASK ───
DeviceProcessEvents
| where Timestamp > ago(7d)
| where FileName =~ "schtasks.exe"
| where ProcessCommandLine has "/create"
| where ProcessCommandLine has_any ("/sc ONSTART", "/sc ONLOGON", "/sc MINUTE")
| project Timestamp, DeviceName, AccountName,
    ProcessCommandLine, InitiatingProcessFileName
| order by Timestamp desc

// ─── RILEVARE LATERAL MOVEMENT VIA REMOTE SERVICE CREATION ───
DeviceProcessEvents
| where Timestamp > ago(7d)
| where FileName =~ "sc.exe"
| where ProcessCommandLine has "\\\\%"
    or ProcessCommandLine matches regex @"\\\\[0-9]{1,3}\.[0-9]{1,3}"
| project Timestamp, DeviceName, AccountName,
    ProcessCommandLine, InitiatingProcessFileName

// ─── RILEVARE POWERSHELL DOWNLOAD CRADLES ───
DeviceProcessEvents
| where Timestamp > ago(7d)
| where FileName in~ ("powershell.exe", "pwsh.exe")
| where ProcessCommandLine has_any (
    "DownloadString", "DownloadFile", "DownloadData",
    "Net.WebClient", "Invoke-WebRequest", "iwr",
    "Start-BitsTransfer", "wget", "curl"
)
| where ProcessCommandLine !has "WindowsUpdate"
| project Timestamp, DeviceName, AccountName, ProcessCommandLine
| order by Timestamp desc

// ─── RILEVARE MIMIKATZ E TOOL DI CREDENTIAL DUMPING ───
DeviceProcessEvents
| where Timestamp > ago(7d)
| where FileName has_any ("mimikatz", "procdump", "nanodump")
    or ProcessCommandLine has_any (
        "sekurlsa::logonpasswords", "lsadump::dcsync",
        "token::elevate", "-ma lsass"
    )
| project Timestamp, DeviceName, AccountName,
    FileName, ProcessCommandLine, InitiatingProcessFileName

// ─── RILEVARE DNS TUNNELING (QUERY ANOMALE) ───
DeviceNetworkEvents
| where Timestamp > ago(1d)
| where RemotePort == 53
| where ActionType == "DnsQueryResponse"
| extend DomainLength = strlen(RemoteUrl)
| where DomainLength > 50  // Domini molto lunghi → possibile tunneling
| summarize QueryCount = count(), AvgLength = avg(DomainLength)
    by DeviceName, RemoteUrl
| where QueryCount > 100
| order by QueryCount desc

// ─── CUSTOM DETECTION RULE: RANSOMWARE BEHAVIOR ───
// Cercare processi che rinominano/crittografano molti file in poco tempo
DeviceFileEvents
| where Timestamp > ago(1h)
| where ActionType == "FileRenamed"
| where FileName endswith_any (".encrypted", ".locked", ".crypto",
    ".crypt", ".enc", ".ransom")
| summarize RenamedFiles = count(), FileList = make_set(FileName, 20)
    by DeviceName, InitiatingProcessFileName, bin(Timestamp, 5m)
| where RenamedFiles > 50
```

### Live Response — Sessioni Avanzate

Live Response consente investigazioni remote in tempo reale. Oltre ai comandi base, le sessioni avanzate (richieste di ruolo elevato) permettono:

```
Sessione Live Response avanzata:

1. Raccogliere memoria volatile per analisi forense:
   > run CollectForensicData.ps1
   (script dalla libreria Live Response — caricato dal team SOC)

2. Eseguire comandi PowerShell personalizzati:
   > run Get-Process | Where-Object { $_.WorkingSet -gt 500MB }

3. Caricare tool forensi:
   > putfile "C:\Tools\Autoruns.exe"     # Upload dalla libreria
   > run "C:\Tools\Autoruns.exe" -a *    # Eseguire sul dispositivo

4. Raccogliere artefatti:
   > getfile "C:\Windows\System32\config\SAM"      # Download file
   > getfile "C:\Windows\Prefetch\MALWARE.EXE-*.pf" # Prefetch

5. Remediation:
   > remediate file "C:\Users\Public\malware.exe"   # Quarantena
   > remediate process 4567                          # Termina processo
```

Fonte: https://learn.microsoft.com/en-us/defender-endpoint/live-response (consultato: 2026-05-23)

---

## Attack Simulation e Training

### Attack Simulation Training (Microsoft 365 Defender)

Attack Simulation Training è una funzionalità di Microsoft Defender for Office 365 che permette di eseguire simulazioni di phishing, social engineering e attacchi payload-based contro gli utenti dell'organizzazione per misurare la resilienza e migliorare la consapevolezza.

```
Tipi di simulazione disponibili:
├── Credential Harvest
│   └── Pagina di login falsa che raccoglie credenziali inserite
├── Malware Attachment
│   └── Email con allegato simulato (nessun payload reale)
├── Link in Attachment
│   └── Allegato con link che porta a pagina di credential harvest
├── Link to Malware
│   └── Link nell'email che simula un download malevolo
├── Drive-by URL
│   └── URL che simula un exploit browser/plugin
└── OAuth Consent Grant
    └── App OAuth malevola che richiede permessi eccessivi

Configurazione:
security.microsoft.com → Email & collaboration
    → Attack simulation training → Simulations → Launch a simulation

Report generati:
- Percentuale utenti che hanno aperto l'email
- Percentuale utenti che hanno cliccato il link
- Percentuale utenti che hanno inserito credenziali
- Percentuale utenti che hanno segnalato l'email come phishing
- Tempo medio di compromissione
```

### SafeLinks e SafeAttachments (Defender for Office 365)

Complementari alla protezione endpoint, queste funzionalità proteggono il vettore email:

- **SafeLinks**: riscrive gli URL nelle email per farli passare attraverso il filtro di reputazione Microsoft al momento del click (time-of-click protection, non solo time-of-delivery)
- **SafeAttachments**: apre gli allegati in una sandbox (detonation chamber) prima di consegnarli all'utente, rilevando malware zero-day non coperto da firme

Fonte: https://learn.microsoft.com/en-us/defender-office-365/safe-links-about (consultato: 2026-05-23)

---

## Device Health Attestation

Device Health Attestation (DHA) verifica l'integrità del processo di avvio di un dispositivo Windows, garantendo che non sia stato compromesso da rootkit, bootkit o modifiche non autorizzate al boot chain.

### Funzionamento

```
Boot process attestato:
┌──────────────────┐
│ UEFI Secure Boot │ → Verifica firme digitali bootloader
├──────────────────┤
│ TPM 2.0 Measured │ → Misura e registra ogni componente caricato
│ Boot              │   nei PCR (Platform Configuration Registers)
├──────────────────┤
│ Boot Log         │ → TCG log con hash di ogni componente
│ (TCGLog)         │   UEFI → bootmgr → winload → kernel → driver
├──────────────────┤
│ DHA Client       │ → Invia il TCG log al DHA cloud service
├──────────────────┤
│ DHA Service      │ → Valida le misurazioni, emette un DHA report
│ (cloud)          │   con le health claims
├──────────────────┤
│ MDM / Intune     │ → Riceve il DHA report e valuta compliance
│ Compliance       │   del dispositivo
└──────────────────┘
```

### Health Claims Verificate

| Claim | Significato | Rischio se fallisce |
|---|---|---|
| Secure Boot | Il bootloader è firmato Microsoft/OEM | Bootkit potenzialmente presente |
| BitLocker | Crittografia del volume OS attiva | Dati a rischio se il device è perso/rubato |
| Code Integrity | Policy WDAC/HVCI attive durante il boot | Driver non firmati possono essere caricati |
| Boot Manager Version | Versione del boot manager | Boot manager vulnerabile se non aggiornato |
| Early Launch Antimalware (ELAM) | Driver ELAM caricato prima di driver di terze parti | Driver malevoli possono caricarsi prima dell'AV |
| DEP | Data Execution Prevention attivo a livello kernel | Exploit kernel facilitati |
| VSM (Virtual Secure Mode) | Credential Guard / HVCI attivi | Protezione credenziali indebolita |

```powershell
# Verificare lo stato di attestazione locale
# Il TPM deve essere presente e attivo
Get-Tpm | Select-Object TpmPresent, TpmReady, TpmEnabled, TpmActivated

# Verificare Secure Boot
Confirm-SecureBootUEFI

# Verificare lo stato di ELAM
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
    Select-Object SecurityServicesRunning, SecurityServicesConfigured,
    VirtualizationBasedSecurityStatus
```

Fonte: https://learn.microsoft.com/en-us/windows/security/hardware-security/tpm/how-windows-uses-the-tpm (consultato: 2026-05-23)

---

## Microsoft Defender for Identity

Microsoft Defender for Identity (MDI, precedentemente Azure ATP) monitora il traffico Active Directory per rilevare attacchi basati sull'identità come Pass-the-Hash, Pass-the-Ticket, Golden Ticket, DCSync e reconnaissance LDAP.

### Architettura

MDI utilizza sensori installati direttamente sui domain controller che analizzano il traffico di rete (port mirroring non necessario) e gli eventi del security log.

```
┌──────────────────────────────┐
│   Microsoft 365 Defender      │
│   Portal                      │
├──────────────────────────────┤
│   MDI Cloud Service           │
│   (Analisi comportamentale,   │
│    ML, correlazione)          │
├──────────────────────────────┤
│   MDI Sensor                  │
│   (installato su DC)          │
│                               │
│   Monitora:                   │
│   - NTLM authentication      │
│   - Kerberos transactions     │
│   - LDAP queries              │
│   - DNS queries               │
│   - Event logs 4776, 4624...  │
└──────────────────────────────┘
```

### Rilevamenti Principali

| Categoria | Rilevamento | Tecnica MITRE |
|-----------|-------------|---------------|
| Reconnaissance | Account enumeration | T1087 |
| Reconnaissance | Network mapping | T1018 |
| Credential Access | Brute force | T1110 |
| Credential Access | AS-REP Roasting | T1558.004 |
| Credential Access | Kerberoasting | T1558.003 |
| Lateral Movement | Pass-the-Hash | T1550.002 |
| Lateral Movement | Pass-the-Ticket | T1550.003 |
| Lateral Movement | Overpass-the-Hash | T1550.002 |
| Domain Dominance | DCSync | T1003.006 |
| Domain Dominance | Golden Ticket | T1558.001 |
| Domain Dominance | Skeleton Key | T1556.001 |
| Exfiltration | Data exfiltration over DNS | T1048.003 |

---

## Windows Defender Application Control (WDAC)

WDAC (precedentemente Device Guard Code Integrity) è la soluzione Microsoft per l'application whitelisting. A differenza di AppLocker, WDAC opera a livello kernel e può controllare non solo le applicazioni utente ma anche i driver e il codice kernel.

```powershell
# Creare una policy WDAC base da un sistema di riferimento ("golden image")
$policyPath = "C:\WDAC\BasePolicy.xml"
New-CIPolicy -Level Publisher -FilePath $policyPath -UserPEs `
    -ScanPath "C:\Windows", "C:\Program Files", "C:\Program Files (x86)"

# Aggiungere una regola per un'applicazione specifica
$app = Get-SystemDriver -ScanPath "C:\Program Files\CustomApp" -UserPEs
Merge-CIPolicy -PolicyPaths $policyPath -Rules $app.Rules -OutputFilePath $policyPath

# Convertire la policy XML in formato binario
$binaryPath = "C:\WDAC\BasePolicy.bin"
ConvertFrom-CIPolicy -XmlFilePath $policyPath -BinaryFilePath $binaryPath

# Deployare la policy (audit mode prima!)
# Aggiungere l'opzione di audit nella policy XML:
Set-RuleOption -FilePath $policyPath -Option 3  # Audit Mode

# Rimuovere audit mode per enforcement
Set-RuleOption -FilePath $policyPath -Option 3 -Delete

# Deployare tramite GPO:
# Computer Configuration → Administrative Templates → System → Device Guard
#   → Deploy Windows Defender Application Control: Enabled
#   → File path: \\server\share\policy.bin

# Monitorare gli eventi WDAC (Code Integrity)
Get-WinEvent -LogName "Microsoft-Windows-CodeIntegrity/Operational" -MaxEvents 50 |
    Where-Object { $_.Id -eq 3076 -or $_.Id -eq 3077 } |
    Select-Object TimeCreated, Id,
        @{N='Mode';E={if($_.Id -eq 3076){'Audit'}else{'Block'}}},
        Message | Format-Table -Wrap
```

---

## WDAC — Code Integrity: UMCI vs KMCI

WDAC implementa il controllo delle applicazioni attraverso due componenti distinti di Code Integrity che operano a livelli diversi dello stack.

### KMCI — Kernel Mode Code Integrity

KMCI controlla il codice che viene caricato nel kernel space: driver, moduli kernel e componenti di sistema. È la linea di difesa contro rootkit e driver malevoli.

```
KMCI verifica:
├── Driver firmati (obbligatorio da Windows 10 1607 per driver kernel)
├── Firma WHQL (Windows Hardware Quality Labs)
├── Firma EV (Extended Validation) del publisher
├── Corrispondenza con la Microsoft Recommended Driver Block Rules
└── Hash del file contro la policy WDAC

KMCI è SEMPRE attivo quando WDAC è deployato.
Non può essere disabilitato separatamente dalla policy WDAC.
```

### UMCI — User Mode Code Integrity

UMCI controlla il codice user-mode: applicazioni (.exe), librerie (.dll), script, MSI installer e packaged apps. È opzionale e va abilitato esplicitamente nella policy WDAC.

```powershell
# Verificare se UMCI è attivo
$dg = Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard
$dg | Select-Object UsermodeCodeIntegrityPolicyEnforcementStatus
# 0 = Off, 1 = Audit, 2 = Enforced

# Abilitare UMCI nella policy WDAC
# UMCI è controllata dalla regola Option 0
Set-RuleOption -FilePath "C:\WDAC\Policy.xml" -Option 0  # Enabled: UMCI
```

### Microsoft Recommended Driver Block Rules

Microsoft mantiene una lista aggiornata di driver noti vulnerabili che vengono bloccati automaticamente da WDAC/KMCI. Questi driver, pur essendo firmati legittimamente, contengono vulnerabilità sfruttabili per escalation di privilegio al livello kernel (tecnica BYOVD — Bring Your Own Vulnerable Driver).

```powershell
# Integrare la block list Microsoft nella policy WDAC
# Scaricare la policy XML aggiornata:
# https://learn.microsoft.com/en-us/windows/security/application-security/
#   application-control/windows-defender-application-control/design/
#   microsoft-recommended-driver-block-rules

# Unire con la policy base
Merge-CIPolicy -PolicyPaths "C:\WDAC\BasePolicy.xml", `
    "C:\WDAC\MicrosoftRecommendedDriverBlockRules.xml" `
    -OutputFilePath "C:\WDAC\MergedPolicy.xml"

# La ASR rule "Block abuse of exploited vulnerable signed drivers"
# (56A863A9-875E-4185-98A7-B882C64B5CE5) usa la stessa block list
# ma è meno potente di WDAC perché non opera a livello kernel
```

Fonte: https://learn.microsoft.com/en-us/windows/security/application-security/application-control/windows-defender-application-control/design/microsoft-recommended-driver-block-rules (consultato: 2026-05-23)

---

## WDAC — Strategie Avanzate di Policy

### Livelli di Autorizzazione WDAC

WDAC supporta diversi livelli di granularità per autorizzare il codice, ciascuno con un bilanciamento diverso tra sicurezza e gestibilità:

| Livello | Descrizione | Sicurezza | Gestibilità |
|---------|-------------|-----------|-------------|
| Hash | Autorizza un singolo file tramite hash SHA256 | Massima | Difficile (ogni aggiornamento richiede nuovi hash) |
| FileName | Autorizza per nome file (OriginalFileName nell'header PE) | Bassa | Facile ma aggirabile |
| FilePath | Autorizza tutti i file in un percorso | Bassa | Facile ma rischiosa |
| Publisher | Autorizza per certificato del publisher | Alta | Buona (sopravvive agli aggiornamenti) |
| FilePublisher | Publisher + nome file + versione minima | Molto alta | Buona |
| SignedVersion | Publisher + versione specifica | Alta | Media |
| LeafCertificate | Certificato specifico (non CA) | Molto alta | Media |
| PcaCertificate | Certificato CA root | Media | Facile |

### Policy Multiple e Supplementari (Windows 10 1903+)

Da Windows 10 1903, WDAC supporta **policy multiple**: una base policy e una o più supplementary policy. Questo permette scenari come: una policy base restrittiva gestita dal team security, con policy supplementari gestite dai team applicativi per le proprie eccezioni.

```powershell
# Creare una base policy con ID specifico
$basePolicy = "C:\WDAC\BasePolicy.xml"
Set-CIPolicyIdInfo -FilePath $basePolicy -BasePolicyID "{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}"

# Permettere policy supplementari
Set-RuleOption -FilePath $basePolicy -Option 17  # Allow supplemental policies

# Creare una policy supplementare
$suppPolicy = "C:\WDAC\SupplementaryPolicy-TeamDev.xml"
New-CIPolicy -Level Publisher -FilePath $suppPolicy -UserPEs `
    -ScanPath "C:\Program Files\DevTools"

# Collegare la supplementare alla base
Set-CIPolicyIdInfo -FilePath $suppPolicy `
    -BasePolicyID "{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}" `
    -SupplementsBasePolicyID "{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}"

# Convertire e deployare entrambe
ConvertFrom-CIPolicy -XmlFilePath $basePolicy -BinaryFilePath "C:\WDAC\BasePolicy.cip"
ConvertFrom-CIPolicy -XmlFilePath $suppPolicy -BinaryFilePath "C:\WDAC\SupplementaryPolicy.cip"

# Deployare sul sistema
Copy-Item "C:\WDAC\*.cip" "C:\Windows\System32\CodeIntegrity\CiPolicies\Active\" -Force
```

### Managed Installer

La regola **Managed Installer** autorizza automaticamente il software distribuito tramite un installer gestito (MECM/SCCM, Intune). Questo elimina la necessità di creare regole esplicite per ogni applicazione distribuita centralmente.

```powershell
# Abilitare la regola Managed Installer nella policy WDAC
Set-RuleOption -FilePath $basePolicy -Option 13  # Enabled: Managed Installer

# Configurare MECM come Managed Installer
# Richiede la configurazione nel portale MECM:
# Administration → Client Settings → Default → Application Management
#   → Enable managed installer: Yes

# Verificare quali processi sono marcati come Managed Installer
$miApps = Get-CimInstance -Namespace root/Microsoft/Windows/CI -ClassName MI_ManagedInstallerInfo
$miApps | Select-Object Name, ProcessId, InstallerFilePath
```

### Intelligent Security Graph (ISG) Integration

WDAC può delegare la decisione di autorizzazione al Microsoft Intelligent Security Graph, che classifica i file in base alla reputazione globale:

```powershell
# Abilitare ISG nella policy WDAC
Set-RuleOption -FilePath $basePolicy -Option 14  # Enabled: Intelligent Security Graph authorization

# ISG autorizza automaticamente file con buona reputazione
# File sconosciuti o con cattiva reputazione vengono bloccati
# Richiede connettività internet per le query al cloud Microsoft
```

### WDAC Wizard

Microsoft fornisce il **WDAC Wizard** (tool grafico) per creare e modificare policy WDAC senza editare XML manualmente. Disponibile come applicazione MSIX su GitHub: `microsoft/WDAC-Toolkit`.

```
WDAC Wizard permette di:
1. Creare policy base da:
   - Default Windows policy (consente solo componenti Windows)
   - Allow Microsoft mode (Windows + software firmato Microsoft)
   - Scan sistema di riferimento (golden image)
2. Aggiungere regole:
   - Per publisher (certificato)
   - Per file hash
   - Per percorso
   - Da log eventi CodeIntegrity (convertire audit in regole)
3. Creare policy supplementari
4. Unire policy esistenti
5. Impostare opzioni di policy (audit, ISG, managed installer)
```

---

## AppLocker — Regole per Tipo di File

Sebbene WDAC sia la soluzione raccomandata, AppLocker resta rilevante in molti ambienti. Questa sezione documenta i cinque tipi di regola AppLocker e le tre condizioni di matching.

### Tipi di Regole (Rule Collections)

```
AppLocker Rule Collections:
├── 1. Executable Rules (.exe, .com)
│   └── Controllano l'esecuzione di programmi
├── 2. Windows Installer Rules (.msi, .msp, .mst)
│   └── Controllano l'installazione di software tramite MSI
├── 3. Script Rules (.ps1, .bat, .cmd, .vbs, .js)
│   └── Controllano l'esecuzione di script
├── 4. Packaged App Rules (APPX/MSIX)
│   └── Controllano le app UWP/MSIX dal Microsoft Store
└── 5. DLL Rules (.dll, .ocx)
    └── Controllano il caricamento di DLL (ATTENZIONE: impatto prestazionale)
    └── Disabilitato di default — abilitare solo se necessario per compliance
```

### Condizioni di Matching

Ogni regola AppLocker usa una di tre condizioni per identificare i file:

```powershell
# ─── PUBLISHER (RACCOMANDATO) ───
# Identifica il file tramite la firma digitale del publisher.
# Sopravvive agli aggiornamenti: la firma resta valida dopo l'update.

# Esempio: consentire tutte le applicazioni firmate da Microsoft
# Publisher: O=MICROSOFT CORPORATION, L=REDMOND, S=WASHINGTON, C=US
# Può specificare anche: Product Name, File Name, File Version (>=)

# ─── PATH ───
# Identifica il file tramite il percorso nel filesystem.
# Semplice ma meno sicuro: un utente con permessi di scrittura
# sul percorso può sostituire il file.
# Supporta wildcards: %PROGRAMFILES%\*, %WINDIR%\*

# ─── HASH ───
# Identifica il file tramite hash SHA256/Authenticode.
# Massima sicurezza ma massima manutenzione: ogni aggiornamento
# del software richiede un nuovo hash nella regola.

# ─── VISUALIZZARE LE REGOLE APPLOCKER ATTIVE ───
Get-AppLockerPolicy -Effective | Select-Object -ExpandProperty RuleCollections |
    ForEach-Object {
        $collection = $_.RuleCollectionType
        $_.Rules | ForEach-Object {
            [PSCustomObject]@{
                Collection = $collection
                Name       = $_.Name
                Action     = $_.Action
                Type       = $_.GetType().Name
                Condition  = if ($_.Conditions) {
                    $_.Conditions[0].GetType().Name -replace 'Condition$', ''
                } else { 'N/A' }
            }
        }
    } | Format-Table -AutoSize

# ─── CREARE REGOLE APPLOCKER ───

# Regola Publisher: consentire Adobe Reader firmato da Adobe
New-AppLockerPolicy -RuleType Publisher -RuleNamePrefix "Allow" `
    -FileInformation (Get-AppLockerFileInformation "C:\Program Files\Adobe\Acrobat Reader\AcroRd32.exe") `
    -User "Everyone" -Optimize

# Regola Path: consentire tutto da Program Files
New-AppLockerPolicy -RuleType Path -RuleNamePrefix "Allow" `
    -FileInformation (Get-AppLockerFileInformation "%PROGRAMFILES%\*") `
    -User "Everyone"

# Regola Hash: consentire un file specifico per hash
New-AppLockerPolicy -RuleType Hash -RuleNamePrefix "Allow" `
    -FileInformation (Get-AppLockerFileInformation "C:\Tools\custom-tool.exe") `
    -User "Everyone"

# Deployare via GPO:
# Computer Configuration → Windows Settings → Security Settings
#   → Application Control Policies → AppLocker
#     → Executable Rules / Windows Installer Rules / Script Rules / etc.
```

### AppLocker — Best Practices

1. **Sempre regole default**: creare le regole default prima di quelle personalizzate per evitare il lockout del sistema
2. **Audit prima di Enforce**: configurare `Enforcement Mode = Audit Only` per ogni collection prima di passare a `Enforce Rules`
3. **Publisher > Path > Hash**: preferire regole Publisher per manutenibilità, Path come seconda scelta, Hash solo per file non firmati
4. **Servizio AppIDSvc**: deve essere in esecuzione (`Set-Service AppIDSvc -StartupType Automatic`)
5. **Non usare DLL rules** salvo requisiti di compliance specifici — l'overhead prestazionale è significativo

Fonte: https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-locker/applocker-overview (consultato: 2026-05-23)

---

## Exploit Protection

Exploit Protection fornisce mitigazioni a livello di sistema e per applicazione contro le tecniche di exploitation comuni (buffer overflow, ROP, heap spray).

```powershell
# Verificare le impostazioni di sistema
Get-ProcessMitigation -System

# Configurare mitigazioni a livello di sistema
Set-ProcessMitigation -System -Enable DEP, EmulateAtlThunks
Set-ProcessMitigation -System -Enable ASLR, BottomUp, HighEntropy
Set-ProcessMitigation -System -Enable CFG, StrictCFG

# Configurare mitigazioni per applicazione specifica
Set-ProcessMitigation -Name "chrome.exe" -Enable DEP, CFG, ASLR
Set-ProcessMitigation -Name "iexplore.exe" -Enable DEP, SEHOP, ASLR, HeapTerminate

# Esportare la configurazione per distribuzione
Get-ProcessMitigation -RegistryConfigFilePath "C:\WDEG\ExploitProtection.xml"

# Importare la configurazione (via GPO o script)
Set-ProcessMitigation -PolicyFilePath "C:\WDEG\ExploitProtection.xml"
```

### Mitigazioni Disponibili

| Mitigazione | Descrizione |
|-------------|-------------|
| DEP (Data Execution Prevention) | Impedisce l'esecuzione di codice da regioni di memoria dati |
| ASLR (Address Space Layout Randomization) | Randomizza gli indirizzi di memoria per complicare gli exploit |
| CFG (Control Flow Guard) | Verifica che i salti di codice indiretto siano verso target validi |
| SEHOP (SEH Overwrite Protection) | Protegge la catena di structured exception handler |
| Heap Integrity | Protegge l'integrità dell'heap |
| Image Randomization (ASLR) | Randomizza la base degli eseguibili |
| Export Address Filtering (EAF) | Filtra l'accesso alle export table delle DLL di sistema |
| Import Address Filtering (IAF) | Filtra l'accesso alle import table |
| Arbitrary Code Guard (ACG) | Impedisce la generazione di codice dinamico |

---

## Network Protection e Web Protection

### Network Protection

Network Protection estende le funzionalità di SmartScreen a livello di rete, bloccando le connessioni in uscita verso domini e IP malevoli indipendentemente dal browser o dall'applicazione.

```powershell
# Abilitare Network Protection
Set-MpPreference -EnableNetworkProtection Enabled

# Modalità Audit
Set-MpPreference -EnableNetworkProtection AuditMode

# Verificare lo stato
Get-MpPreference | Select-Object EnableNetworkProtection

# Monitorare i blocchi di Network Protection
Get-WinEvent -LogName "Microsoft-Windows-Windows Defender/Operational" |
    Where-Object { $_.Id -eq 1125 -or $_.Id -eq 1126 } |
    Select-Object TimeCreated, Message | Format-Table -Wrap
```

### Web Content Filtering

Quando integrato con MDE, il web content filtering permette di bloccare l'accesso a categorie di siti web (adult content, gambling, social media, etc.) tramite policy centralizzate nel portale Microsoft 365 Defender.

---

## Tamper Protection e Security Intelligence

### Tamper Protection

Tamper Protection impedisce la disabilitazione o modifica delle funzionalità di sicurezza di Defender da parte di malware, script o utenti non autorizzati — inclusi gli amministratori locali. Quando abilitata, le seguenti modifiche vengono bloccate anche con privilegi elevati:

- Disabilitazione della protezione in tempo reale
- Disabilitazione della protezione cloud
- Disabilitazione del monitoraggio comportamentale
- Disabilitazione dell'IOAV (scansione download)
- Rimozione degli aggiornamenti di security intelligence
- Modifica delle esclusioni via script o registry diretto

```powershell
# Verificare lo stato di Tamper Protection
Get-MpComputerStatus | Select-Object IsTamperProtected

# Tamper Protection NON può essere configurata via PowerShell locale o GPO
# DEVE essere gestita tramite:
# 1. Microsoft 365 Defender portal (security.microsoft.com)
#    → Settings → Endpoints → Advanced features → Tamper protection: On
# 2. Microsoft Intune
#    → Endpoint security → Antivirus → Create policy
#    → Tamper Protection: Enabled

# Verificare il registro per lo stato di Tamper Protection
$tpStatus = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows Defender\Features" `
    -Name "TamperProtection" -ErrorAction SilentlyContinue
switch ($tpStatus.TamperProtection) {
    0 { "Tamper Protection: DISABILITATA" }
    1 { "Tamper Protection: ABILITATA (gestita dal portale)" }
    2 { "Tamper Protection: ABILITATA (gestita da Intune)" }
    4 { "Tamper Protection: NON CONFIGURATA" }
    5 { "Tamper Protection: ABILITATA" }
}
```

### Security Intelligence Updates — Gestione Avanzata

La gestione degli aggiornamenti delle definizioni (Security Intelligence Updates) è critica per l'efficacia della protezione. In ambienti enterprise, è possibile configurare più sorgenti di aggiornamento con fallback:

```powershell
# Configurare l'ordine delle sorgenti di aggiornamento
Set-MpPreference -SignatureFallbackOrder "MicrosoftUpdateServer|MMPC|FileShares"

# Sorgenti disponibili:
# MicrosoftUpdateServer — Windows Update / WSUS
# MMPC — Microsoft Malware Protection Center (download diretto)
# FileShares — Share di rete locale
# InternalDefinitionUpdateServer — Server interno personalizzato

# Configurare una share di rete come sorgente di fallback
Set-MpPreference -DefinitionUpdateFileSharesSources "\\fileserver\WDDefinitions"

# Configurare l'intervallo di check per gli aggiornamenti
# Via GPO: Computer Configuration → Administrative Templates
#   → Windows Components → Microsoft Defender Antivirus → Security Intelligence Updates
#   → Specify the interval to check for security intelligence updates: 4 (ore)

# Script per scaricare e distribuire le definizioni offline
function Update-DefenderDefinitionsOffline {
    param([string]$SharePath = "\\fileserver\WDDefinitions")

    $urls = @{
        "x64" = "https://go.microsoft.com/fwlink/?LinkID=121721&arch=x64"
        "x86" = "https://go.microsoft.com/fwlink/?LinkID=121721&arch=x86"
    }

    foreach ($arch in $urls.Keys) {
        $destDir = Join-Path $SharePath $arch
        New-Item -Path $destDir -ItemType Directory -Force
        $destFile = Join-Path $destDir "mpam-fe.exe"

        Write-Output "Scaricando definizioni $arch..."
        Invoke-WebRequest -Uri $urls[$arch] -OutFile $destFile -UseBasicParsing
        Write-Output "Salvato: $destFile ($(([math]::Round((Get-Item $destFile).Length / 1MB, 1))) MB)"
    }

    Write-Output "`nPer applicare manualmente su un endpoint offline:"
    Write-Output "  cd $SharePath\x64 && mpam-fe.exe"
}
```

### Platform Updates vs Security Intelligence Updates

È importante distinguere tra due tipi di aggiornamenti Defender:

| Tipo | Contenuto | Frequenza | Canale |
|------|-----------|-----------|--------|
| Security Intelligence Updates | Firme malware, regole euristiche | Più volte al giorno | Windows Update, WSUS, MMPC |
| Platform Updates | Motore antimalware, CSE, client | Mensile (Patch Tuesday) | Windows Update, WSUS |
| Engine Updates | Defender Engine (mpengine.dll) | Mensile o su necessità | Windows Update, WSUS |

```powershell
# Verificare le versioni attuali di tutti i componenti
$status = Get-MpComputerStatus
[PSCustomObject]@{
    "Signature Version"    = $status.AntivirusSignatureVersion
    "Signature Age (hrs)"  = [math]::Round((New-TimeSpan -Start $status.AntivirusSignatureLastUpdated).TotalHours, 1)
    "Engine Version"       = $status.AMEngineVersion
    "Platform Version"     = $status.AMProductVersion
    "Service Version"      = $status.AMServiceVersion
    "NIS Engine Version"   = $status.NISEngineVersion
    "NIS Signature Ver"    = $status.NISSignatureVersion
} | Format-List
```

---

## Microsoft Intune — Integrazione Defender

### Profili di Configurazione Endpoint Security

Microsoft Intune fornisce profili dedicati per la gestione centralizzata di tutte le funzionalità Defender sugli endpoint managed:

```
Endpoint Manager → Endpoint security:

1. Antivirus
   ├── Microsoft Defender Antivirus
   │   ├── Real-time protection: Enabled
   │   ├── Cloud-delivered protection: Enabled
   │   ├── Cloud-delivered protection level: High Plus
   │   ├── Cloud extended timeout: 50 seconds
   │   ├── Submit samples consent: Send all samples automatically
   │   ├── Scan parameters (schedule, CPU limit, exclusions)
   │   └── Tamper Protection: Enabled
   └── Microsoft Defender Antivirus Exclusions
       ├── Excluded paths
       ├── Excluded extensions
       └── Excluded processes

2. Attack Surface Reduction
   ├── ASR Rules (per-rule Block/Audit/Warn/Off)
   ├── Controlled Folder Access: Enabled/Audit
   │   ├── Protected folders (additional)
   │   └── Allowed applications
   └── Exploit Protection
       └── XML configuration file upload

3. Endpoint Detection and Response
   ├── Onboarding package (auto-enrollment)
   ├── Sample sharing: All
   └── Expedite telemetry reporting: Enabled

4. Firewall
   ├── Domain profile settings
   ├── Private profile settings
   └── Public profile settings

5. Device Compliance
   ├── Require Microsoft Defender Antimalware
   ├── Require real-time protection
   ├── Minimum Defender Antimalware version
   └── Machine risk score (from MDE): Clear / Low / Medium
```

### Compliance Policy Basata su Defender Risk Score

Intune può integrare il risk score di Microsoft Defender for Endpoint nelle policy di compliance, condizionando l'accesso alle risorse aziendali:

```
Flusso: MDE Risk Score → Intune Compliance → Conditional Access

1. MDE assegna un risk score al dispositivo:
   - Clear: nessun rischio rilevato
   - Low: rischio basso
   - Medium: rischio medio
   - High: rischio alto (minaccia attiva)

2. Intune valuta la compliance basandosi sul risk score
3. Azure AD Conditional Access blocca l'accesso a Exchange/SharePoint/Teams
   per dispositivi non compliant

Configurazione:
Endpoint Manager → Devices → Compliance policies → Create policy:
    Platform: Windows 10 and later
    Settings:
    → Microsoft Defender for Endpoint:
        "Require the device to be at or under the machine risk score": Medium
```

### Security Baselines Intune

Intune include Security Baselines preconfigurate basate sulle raccomandazioni Microsoft:

```
Endpoint Manager → Endpoint security → Security baselines:

Baseline disponibili:
├── Security Baseline for Windows 10 and later
│   (equivalente delle Microsoft Security Baselines per GPO)
├── Microsoft Defender for Endpoint Baseline
│   (configurazione ottimale di MDE)
├── Microsoft Edge Baseline
│   (sicurezza browser Edge)
├── Microsoft 365 Apps for Enterprise Baseline
│   (sicurezza Office)
└── Windows 365 Cloud PC Security Baseline
    (per Azure Virtual Desktop / Windows 365)

Ogni baseline può essere:
- Assegnata a gruppi di dispositivi/utenti
- Personalizzata (override di singole impostazioni)
- Monitorata per conformità (report di compliance)
```

```powershell
# Verificare le policy Intune applicate sul client
# Diagnostica MDM su Windows
Start-Process "ms-settings:workplace"  # Impostazioni → Account → Access work or school

# Report diagnostico MDM completo
mdmdiagnosticstool.exe -area "DeviceEnrollment;DeviceProvisioning;Autopilot" -zip "C:\Temp\MDMDiag.zip"

# Verificare le policy MDM applicate via registry
Get-ChildItem "HKLM:\SOFTWARE\Microsoft\PolicyManager\current\device\Defender" -ErrorAction SilentlyContinue |
    Get-ItemProperty | Format-List
```

---

## Gestione con PowerShell e GPO

### Configurazione Completa via GPO

```
Computer Configuration → Policies → Administrative Templates
    → Windows Components → Microsoft Defender Antivirus:

    Real-time Protection:
    - Turn on behavior monitoring: Enabled
    - Scan all downloaded files and attachments: Enabled
    - Turn on process scanning: Enabled

    Cloud-delivered Protection:
    - Join Microsoft MAPS: Enabled (Advanced MAPS)
    - Send file samples when further analysis is required: Enabled (Send all)
    - Configure the 'Block at First Sight' feature: Enabled
    - Configure extended cloud check: Enabled (50 seconds)

    Scan:
    - Scan archive files: Enabled
    - Turn on heuristics: Enabled
    - Scan removable drives: Enabled
    - Turn on e-mail scanning: Enabled
    - Schedule scan type: Full scan (weekly)
    - Specify CPU utilization: 30

    Microsoft Defender Exploit Guard:
    - Attack Surface Reduction:
        Configure ASR rules: Enabled (lista GUID=1)
    - Controlled Folder Access:
        Configure Controlled Folder Access: Enabled
    - Network Protection:
        Prevent users and apps from accessing dangerous websites: Enabled (Block)
```

### Script di Audit Completo

```powershell
# Report completo dello stato di sicurezza dell'endpoint
function Get-EndpointSecurityReport {
    $status = Get-MpComputerStatus
    $prefs = Get-MpPreference

    [PSCustomObject]@{
        ComputerName             = $env:COMPUTERNAME
        DefenderEnabled          = $status.AntivirusEnabled
        RealTimeProtection       = $status.RealTimeProtectionEnabled
        CloudProtection          = $prefs.MAPSReporting -ne 0
        BehaviorMonitoring       = $status.BehaviorMonitorEnabled
        NetworkProtection        = $prefs.EnableNetworkProtection -eq 1
        ControlledFolderAccess   = $prefs.EnableControlledFolderAccess -eq 1
        ASRRulesCount            = ($prefs.AttackSurfaceReductionRules_Ids | Where-Object { $_ }).Count
        SignatureVersion         = $status.AntivirusSignatureVersion
        SignatureAge             = (New-TimeSpan -Start $status.AntivirusSignatureLastUpdated).TotalHours
        EngineVersion            = $status.AMEngineVersion
        ProductVersion           = $status.AMProductVersion
        TamperProtection         = $status.IsTamperProtected
        ExclusionPaths           = ($prefs.ExclusionPath | Measure-Object).Count
        ExclusionProcesses       = ($prefs.ExclusionProcess | Measure-Object).Count
        LastFullScan             = $status.FullScanEndTime
        LastQuickScan            = $status.QuickScanEndTime
    }
}

Get-EndpointSecurityReport | Format-List
```

---

## PowerShell — Cmdlet di Riferimento Completi

Riferimento completo dei cmdlet PowerShell per la gestione di Microsoft Defender Antivirus, organizzati per funzione operativa.

### Cmdlet di Interrogazione

```powershell
# ─── Get-MpComputerStatus ───
# Restituisce lo stato completo del motore Defender sull'endpoint
Get-MpComputerStatus
# Proprietà chiave:
#   AMRunningMode           → Normal | Passive | EDR Block | SxS Passive
#   RealTimeProtectionEnabled → $true/$false
#   IsTamperProtected       → $true/$false
#   AntivirusSignatureVersion → es. 1.421.123.0
#   AntivirusSignatureLastUpdated → DateTime ultimo aggiornamento firme
#   AMEngineVersion         → versione del motore antimalware
#   AMProductVersion        → versione della piattaforma Defender
#   QuickScanAge            → giorni dall'ultima scansione rapida
#   FullScanAge             → giorni dall'ultima scansione completa

# ─── Get-MpPreference ───
# Restituisce TUTTE le preferenze/configurazione di Defender
Get-MpPreference
# Proprietà chiave:
#   DisableRealtimeMonitoring     → $true/$false
#   MAPSReporting                 → 0=Off, 1=Basic, 2=Advanced
#   SubmitSamplesConsent          → 0=AlwaysPrompt, 1=Safe, 2=Never, 3=All
#   CloudBlockLevel               → 0=Default, 1=Moderate, 2=High, 4=HighPlus, 6=ZeroTolerance
#   CloudExtendedTimeout          → secondi extra per verdetto cloud
#   EnableNetworkProtection       → 0=Off, 1=Enabled, 2=Audit
#   EnableControlledFolderAccess  → 0=Off, 1=Enabled, 2=Audit
#   ScanAvgCPULoadFactor          → 0-100 (percentuale CPU massima)
#   AttackSurfaceReductionRules_Ids     → array di GUID
#   AttackSurfaceReductionRules_Actions → array di azioni (0,1,2,6)
#   ExclusionPath/Extension/Process     → array di esclusioni

# ─── Get-MpThreat ───
# Restituisce le minacce rilevate (stato attuale, non storico)
Get-MpThreat | Select-Object ThreatID, ThreatName, SeverityID,
    IsActive, DidThreatExecute, Resources

# ─── Get-MpThreatDetection ───
# Restituisce lo storico dei rilevamenti con timestamp
Get-MpThreatDetection | Select-Object ThreatName, DomainUser,
    ProcessName, InitialDetectionTime, LastThreatStatusChangeTime,
    ActionSuccess, Resources | Sort-Object InitialDetectionTime -Descending

# ─── Get-MpThreatCatalog ───
# Restituisce il catalogo completo delle minacce note nel database firme
# (output molto grande — filtrare per nome o severity)
Get-MpThreatCatalog | Where-Object { $_.SeverityID -ge 4 } |
    Select-Object ThreatName, SeverityID, CategoryID -First 20
```

### Cmdlet di Configurazione

```powershell
# ─── Set-MpPreference ───
# Configura le preferenze di Defender. Parametri principali:

# Protezione real-time
Set-MpPreference -DisableRealtimeMonitoring $false
Set-MpPreference -DisableBehaviorMonitoring $false
Set-MpPreference -DisableIOAVProtection $false
Set-MpPreference -DisableScriptScanning $false

# Cloud protection
Set-MpPreference -MAPSReporting Advanced
Set-MpPreference -SubmitSamplesConsent SendAllSamples
Set-MpPreference -CloudBlockLevel HighPlus
Set-MpPreference -CloudExtendedTimeout 50

# Scansioni
Set-MpPreference -ScanScheduleQuickScanTime 12:00:00
Set-MpPreference -ScanScheduleDay 1             # 0=Ogni giorno, 1=Domenica...7=Sabato
Set-MpPreference -ScanScheduleTime 02:00:00
Set-MpPreference -ScanAvgCPULoadFactor 30
Set-MpPreference -EnableLowCpuPriority $true
Set-MpPreference -ScanOnlyIfIdleEnabled $true
Set-MpPreference -CheckForSignaturesBeforeRunningScan $true

# ─── Add-MpPreference ───
# Aggiunge valori agli array (esclusioni, ASR rules)
Add-MpPreference -ExclusionPath "D:\Data"
Add-MpPreference -ExclusionExtension ".mdf"
Add-MpPreference -ExclusionProcess "sqlservr.exe"
Add-MpPreference -AttackSurfaceReductionRules_Ids "GUID" `
    -AttackSurfaceReductionRules_Actions Enabled

# ─── Remove-MpPreference ───
# Rimuove valori dagli array
Remove-MpPreference -ExclusionPath "D:\Data"

# ─── Start-MpScan ───
Start-MpScan -ScanType QuickScan
Start-MpScan -ScanType FullScan
Start-MpScan -ScanType CustomScan -ScanPath "C:\Suspect"

# ─── Update-MpSignature ───
Update-MpSignature
Update-MpSignature -UpdateSource FileShares `
    -DefinitionUpdateFileSharesSources "\\server\WDDefs"

# ─── Start-MpWDOScan ───
# Esegue un test di connettività cloud Defender
Start-MpWDOScan
```

Fonte: https://learn.microsoft.com/en-us/powershell/module/defender/ (consultato: 2026-05-23)

---

## Group Policy vs Intune — Confronto per Funzionalità

La tabella seguente confronta i due metodi di gestione principali per ogni funzionalità Defender, indicando quale offre maggiore controllo e quale è raccomandato.

| Funzionalità | Group Policy | Intune | Raccomandato | Note |
|---|---|---|---|---|
| **Real-Time Protection** | Sì (Admin Templates) | Sì (Endpoint security → Antivirus) | Intune | GPO bloccata da Tamper Protection |
| **Cloud Protection (MAPS)** | Sì (Cloud-delivered protection) | Sì (Cloud protection level) | Intune | Intune permette CloudBlockLevel granulare |
| **ASR Rules** | Sì (configure ASR rules) | Sì (Attack surface reduction profiles) | Intune | Intune offre reporting per-regola e per-device |
| **Controlled Folder Access** | Sì (Configure CFA) | Sì (CFA settings) | Intune | Pari funzionalità |
| **Network Protection** | Sì (Prevent dangerous websites) | Sì (Network protection settings) | Intune | Intune integra web content filtering |
| **Exploit Protection** | Sì (XML file deployment) | Sì (XML upload nel profilo) | Pari | Stesso meccanismo XML |
| **Tamper Protection** | NO | Sì | Intune | TP può essere gestita solo da cloud |
| **WDAC** | Sì (Deploy WDAC policy) | Sì (App Control for Business) | Intune | Intune semplifica il deployment di supplemental policies |
| **Esclusioni** | Sì (Exclusion settings) | Sì (AV exclusions profile) | Intune | Con TP attiva, solo Intune funziona |
| **Scansioni pianificate** | Sì (Scan settings) | Sì (AV policy → Scan) | Pari | Stessa granularità |
| **Aggiornamento definizioni** | Sì (Signature updates) | Sì (Update settings) | GPO/WSUS | GPO/WSUS più granulare per sorgenti di fallback |
| **MDE Onboarding** | Sì (via scheduled task) | Sì (EDR profile, auto) | Intune | Intune: onboarding automatico con compliance |
| **Security Baselines** | Sì (SCM baselines) | Sì (Endpoint security baselines) | Intune | Intune baselines integrate e versionabili |
| **Reporting/Compliance** | No nativo (richiede SIEM) | Sì (Intune compliance reports) | Intune | Intune offre dashboard nativi |

### Regola Generale

- **Ambienti cloud-first / Intune-managed**: usare Intune per TUTTA la configurazione Defender
- **Ambienti on-premises / AD tradizionale**: usare GPO + Intune co-management
- **Ambienti ibridi**: Intune per Defender, GPO per legacy settings non coperte da Intune

Fonte: https://learn.microsoft.com/en-us/mem/intune/protect/endpoint-security (consultato: 2026-05-23)

---

## Event ID di Riferimento — Tabella Completa

Tabella completa degli Event ID di Microsoft Defender raggruppati per componente. Fonte log: `Microsoft-Windows-Windows Defender/Operational` salvo diversa indicazione.

### Defender Antivirus — Rilevamento e Azione

| Event ID | Significato | Severità | Azione Consigliata |
|---|---|---|---|
| 1006 | Motore antimalware aggiornato | Informational | Nessuna |
| 1007 | Piattaforma antimalware aggiornata | Informational | Nessuna |
| 1008 | Errore aggiornamento piattaforma | Warning | Verificare connettività WSUS/WU |
| 1116 | **Malware o software potenzialmente indesiderato rilevato** | Warning | Verificare l'azione eseguita (1117) |
| 1117 | **Azione eseguita su minaccia rilevata** (quarantina, rimozione, blocco) | Informational | Verificare successo azione |
| 1118 | Azione su minaccia fallita | Error | Investigare manualmente, verificare permessi |
| 1119 | Errore critico durante tentativo di azione su minaccia | Critical | Escalation immediata, possibile evasione |
| 1120 | Enumerazione minacce — lista di minacce attive | Informational | Usare per inventario |

### ASR e Controlled Folder Access

| Event ID | Significato | Severità | Azione Consigliata |
|---|---|---|---|
| 1121 | **ASR rule ha bloccato un'operazione** | Warning | Verificare se legittimo; se FP, aggiungere esclusione |
| 1122 | ASR rule in audit — operazione consentita ma registrata | Informational | Analizzare per preparare il passaggio a Block |
| 1123 | **Controlled Folder Access ha bloccato una scrittura** | Warning | Aggiungere app alla whitelist se legittima |
| 1124 | Controlled Folder Access in audit — scrittura consentita | Informational | Analizzare per preparare enforcement |
| 1125 | **Network Protection ha bloccato una connessione** | Warning | Verificare dominio/IP; se FP, creare indicatore Allow |
| 1126 | Network Protection in audit — connessione consentita | Informational | Analizzare per preparare enforcement |
| 1127 | Network Protection — connessione bloccata localmente | Warning | Verificare indicatori locali |

### Stato del Servizio e Configurazione

| Event ID | Significato | Severità | Azione Consigliata |
|---|---|---|---|
| 2000 | Definizioni aggiornate con successo | Informational | Nessuna |
| 2001 | Errore aggiornamento definizioni | Error | Verificare connettività, sorgente definizioni |
| 2010 | Errore motore — utilizzato per rilevare evasione | Warning | Investigare possibile tampering |
| 2012 | Errore durante caricamento del motore | Error | Riavviare servizio WinDefend |
| 2050 | Errore critico motore | Critical | Possibile corruzione, reinstallare piattaforma |
| 5000 | Real-time protection abilitata | Informational | Nessuna |
| **5001** | **Real-time protection disabilitata** | **Warning** | **Investigare immediatamente — possibile compromissione** |
| 5004 | Configurazione protezione real-time modificata | Informational | Verificare chi ha effettuato la modifica |
| **5007** | **Configurazione antimalware modificata** | **Warning** | **Audit trail — verificare l'autore della modifica** |
| 5008 | Errore motore antimalware | Error | Verificare integrità dell'installazione |
| **5010** | **Scansione disabilitata tramite policy** | **Warning** | **Verificare GPO/Intune — potenziale misconfiguration** |
| **5012** | **Scansione fallita** | **Error** | **Verificare esclusioni, spazio disco, permessi** |

### Code Integrity (WDAC)

Log: `Microsoft-Windows-CodeIntegrity/Operational`

| Event ID | Significato | Severità | Azione Consigliata |
|---|---|---|---|
| **3076** | **File bloccato in modalità Audit** (sarebbe stato bloccato) | Informational | Creare regola se legittimo, o confermare che il blocco è desiderato |
| **3077** | **File bloccato in modalità Enforcement** | Warning | Se legittimo, creare regola supplementare |
| 3089 | Policy Code Integrity caricata con successo | Informational | Nessuna |
| 3099 | Policy Code Integrity non caricata (errore) | Error | Verificare formato policy, Secure Boot |

Fonte: https://learn.microsoft.com/en-us/defender-endpoint/troubleshoot-microsoft-defender-antivirus (consultato: 2026-05-23)

---

## Best Practices

**Centralizzare la gestione con Microsoft 365 Defender:** Per ambienti enterprise, configurare tutte le policy Defender attraverso il portale Microsoft 365 Defender (security.microsoft.com) o tramite Intune. La gestione centralizzata garantisce coerenza delle configurazioni, visibilità aggregata degli alert su tutti gli endpoint e la possibilità di rispondere agli incidenti da un'unica console.

**Non disabilitare mai la real-time protection:** La protezione in tempo reale è la prima linea di difesa. Le esclusioni devono essere chirurgiche e documentate, mai applicate a intere unità o percorsi ampi come `C:\`.

**Implementare ASR rules in modalità Audit prima di Block:** Abilitare tutte le regole ASR in modalità Audit per almeno 30 giorni, analizzare gli eventi nel log, risolvere i falsi positivi con esclusioni mirate, quindi passare a modalità Block.

**Mantenere le definizioni aggiornate:** Configurare aggiornamenti delle definizioni ogni 4-8 ore. Per ambienti disconnessi, configurare una share di rete come sorgente delle definizioni con un processo automatizzato di aggiornamento.

**Abilitare Cloud-Delivered Protection e Block at First Sight:** Queste funzionalità forniscono protezione in tempo reale contro minacce zero-day, con latenza di pochi secondi per il verdetto. Il trade-off è l'invio di metadati e campioni al cloud Microsoft.

**Utilizzare Tamper Protection:** Tamper Protection impedisce la disabilitazione delle funzionalità di sicurezza da parte di malware o utenti non autorizzati. Si configura tramite Intune o il portale Microsoft 365 Defender.

**Monitorare attivamente gli eventi:** Configurare il forwarding degli eventi Defender verso un SIEM o un sistema di log centralizzato. Gli eventi chiave sono: 1116 (malware detected), 1117 (action taken), 1121 (ASR block), 1123 (CFA block), 5007 (configuration change).

**Implementare WDAC per ambienti ad alta sicurezza:** Per sistemi critici come i domain controller, server infrastrutturali e workstation in ambienti sensibili, WDAC fornisce il livello di protezione più elevato attraverso l'application whitelisting.

**Segmentare le policy per ruolo del server:** Non applicare la stessa configurazione Defender a tutti i server. I domain controller, i file server, i server SQL e i web server hanno profili di rischio e requisiti di esclusione diversi. Creare gruppi di policy specifici per ruolo, ciascuno con esclusioni ottimizzate per ridurre i falsi positivi senza indebolire la protezione. Ad esempio, i server SQL necessitano di esclusioni per i file `.mdf`, `.ndf` e `.ldf`, mentre i server Exchange richiedono esclusioni per i database delle caselle postali e i file di log delle transazioni.

**Integrare con Microsoft Defender for Identity:** Per una protezione completa dell'infrastruttura Active Directory, integrare Microsoft Defender for Endpoint con Defender for Identity. Questa integrazione correla i segnali degli endpoint con le attività sospette a livello di directory (Kerberoasting, DCSync, Golden Ticket), fornendo una visione unificata della kill chain degli attaccanti. La correlazione tra i due prodotti avviene automaticamente attraverso il portale Microsoft 365 Defender, con incident che aggregano alert da entrambe le sorgenti.

---

## Troubleshooting

### Problema: Defender Disabilitato e Non Si Riattiva

**Sintomi**: Windows Security mostra "La protezione in tempo reale è disattivata" e l'attivazione manuale fallisce o si disattiva immediatamente.

**Causa**: Un antivirus di terze parti è installato e registrato come provider di sicurezza, oppure policy di gruppo o chiavi di registry disabilitano Defender, oppure il servizio WinDefend è disabilitato.

**Soluzione**:

```powershell
# Verificare se un antivirus di terze parti è registrato
Get-CimInstance -Namespace "root/SecurityCenter2" -ClassName AntiVirusProduct |
    Select-Object displayName, productState

# Verificare le GPO che disabilitano Defender
Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender" -Name "DisableAntiSpyware" -ErrorAction SilentlyContinue

# Rimuovere la policy che disabilita Defender
Remove-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender" -Name "DisableAntiSpyware" -ErrorAction SilentlyContinue

# Verificare il servizio
Get-Service WinDefend | Select-Object Status, StartType
Set-Service WinDefend -StartupType Automatic
Start-Service WinDefend
```

### Problema: Falsi Positivi Frequenti su Applicazioni Aziendali

**Sintomi**: Defender blocca ripetutamente file legittimi di un'applicazione aziendale, causando interruzioni operative.

**Causa**: L'applicazione utilizza tecniche che attivano le euristiche di Defender (packing, self-modifying code, accesso a regioni di memoria sensibili) oppure le firme sono troppo aggressive per quel contesto.

**Soluzione**:

```powershell
# 1. Identificare il file bloccato
Get-MpThreatDetection | Select-Object ThreatName, Resources, ActionSuccess, DetectionSourceTypeID |
    Sort-Object InitialDetectionTime -Descending | Select-Object -First 20

# 2. Verificare il file su VirusTotal prima di escluderlo
# (manuale: caricare su virustotal.com)

# 3. Creare esclusioni mirate (più specifiche possibile)
# Preferire esclusioni per processo piuttosto che per percorso
Add-MpPreference -ExclusionProcess "C:\Program Files\CustomApp\app.exe"

# 4. Se ASR rules bloccano l'applicazione, escludere solo per ASR
Add-MpPreference -AttackSurfaceReductionOnlyExclusions "C:\Program Files\CustomApp\app.exe"

# 5. Sottomettere il falso positivo a Microsoft
# https://www.microsoft.com/en-us/wdsi/filesubmission
```

### Problema: Scansioni Lente che Impattano le Prestazioni

**Sintomi**: Durante le scansioni pianificate, il sistema diventa lento e gli utenti segnalano degradazione delle prestazioni.

**Causa**: La scansione sta analizzando file di grandi dimensioni (database, archivi, VHD) senza esclusioni appropriate, oppure il limite CPU è troppo alto.

**Soluzione**:

```powershell
# Ridurre il limite CPU
Set-MpPreference -ScanAvgCPULoadFactor 20

# Configurare la priorità di scansione come bassa
Set-MpPreference -EnableLowCpuPriority $true

# Escludere file di grandi dimensioni che non necessitano scansione
Add-MpPreference -ExclusionPath "D:\SQLData"
Add-MpPreference -ExclusionExtension ".mdf", ".ndf", ".ldf", ".bak"

# Pianificare le scansioni fuori dall'orario di lavoro
Set-MpPreference -ScanScheduleDay 1 -ScanScheduleTime 02:00:00

# Abilitare la scansione solo dei file modificati
Set-MpPreference -ScanOnlyIfIdleEnabled $true
```

---

## Integrazione SIEM e Log Forwarding

### Windows Event Forwarding per Eventi Defender

Per un monitoraggio centralizzato efficace, gli eventi di sicurezza generati da Microsoft Defender devono essere inoltrati a un SIEM (Security Information and Event Management) come Microsoft Sentinel, Splunk, QRadar o Elastic Security.

```powershell
# Configurare Windows Event Forwarding per gli eventi Defender
# Sul collector (server SIEM/WEC):
wecutil qc /q  # Configurare il servizio Windows Event Collector

# Creare una subscription per gli eventi Defender
$subscriptionXml = @"
<Subscription xmlns="http://schemas.microsoft.com/2006/03/windows/events/subscription">
    <SubscriptionId>DefenderEvents</SubscriptionId>
    <SubscriptionType>SourceInitiated</SubscriptionType>
    <Description>Raccolta eventi Microsoft Defender</Description>
    <Enabled>true</Enabled>
    <Uri>http://schemas.microsoft.com/wbem/wsman/1/windows/EventLog</Uri>
    <ConfigurationMode>MinLatency</ConfigurationMode>
    <Query>
        <![CDATA[
        <QueryList>
            <Query Id="0" Path="Microsoft-Windows-Windows Defender/Operational">
                <Select Path="Microsoft-Windows-Windows Defender/Operational">
                    *[System[(EventID=1116 or EventID=1117 or EventID=1118 or
                    EventID=1119 or EventID=1121 or EventID=1122 or
                    EventID=1123 or EventID=1124 or EventID=5001 or
                    EventID=5007 or EventID=5010 or EventID=5012)]]
                </Select>
            </Query>
        </QueryList>
        ]]>
    </Query>
    <ReadExistingEvents>true</ReadExistingEvents>
    <TransportName>HTTP</TransportName>
    <Locale Language="en-US"/>
</Subscription>
"@

$subscriptionXml | Out-File "C:\Temp\DefenderSubscription.xml" -Encoding UTF8
wecutil cs "C:\Temp\DefenderSubscription.xml"
```

### Dashboard di Sicurezza con PowerShell

```powershell
# Script per generare un dashboard di sicurezza giornaliero
function Get-DailySecurityDashboard {
    $today = (Get-Date).Date

    # 1. Rilevamenti malware nelle ultime 24 ore
    $threats = Get-MpThreatDetection |
        Where-Object { $_.InitialDetectionTime -ge $today } |
        Group-Object ThreatName | Sort-Object Count -Descending

    # 2. Tentativi bloccati da ASR
    $asrBlocks = Get-WinEvent -FilterHashtable @{
        LogName = "Microsoft-Windows-Windows Defender/Operational"
        ID = 1121
        StartTime = $today
    } -ErrorAction SilentlyContinue

    # 3. Blocchi di Controlled Folder Access
    $cfaBlocks = Get-WinEvent -FilterHashtable @{
        LogName = "Microsoft-Windows-Windows Defender/Operational"
        ID = 1123
        StartTime = $today
    } -ErrorAction SilentlyContinue

    # 4. Stato aggiornamento definizioni
    $status = Get-MpComputerStatus
    $sigAge = (New-TimeSpan -Start $status.AntivirusSignatureLastUpdated -End (Get-Date)).TotalHours

    # 5. Blocchi Network Protection
    $npBlocks = Get-WinEvent -FilterHashtable @{
        LogName = "Microsoft-Windows-Windows Defender/Operational"
        ID = 1125
        StartTime = $today
    } -ErrorAction SilentlyContinue

    [PSCustomObject]@{
        Date                    = $today.ToString("yyyy-MM-dd")
        ComputerName            = $env:COMPUTERNAME
        ThreatsDetected         = ($threats | Measure-Object -Property Count -Sum).Sum
        UniqueThreats           = $threats.Count
        TopThreat               = if ($threats) { $threats[0].Name } else { "Nessuno" }
        ASRBlockedEvents        = if ($asrBlocks) { $asrBlocks.Count } else { 0 }
        CFABlockedEvents        = if ($cfaBlocks) { $cfaBlocks.Count } else { 0 }
        NetworkProtectionBlocks = if ($npBlocks) { $npBlocks.Count } else { 0 }
        SignatureAgeHours       = [math]::Round($sigAge, 1)
        SignatureVersion        = $status.AntivirusSignatureVersion
        EngineVersion           = $status.AMEngineVersion
        RealTimeProtection      = $status.RealTimeProtectionEnabled
        TamperProtection        = $status.IsTamperProtected
        OverallHealth           = if ($status.RealTimeProtectionEnabled -and $sigAge -lt 48) { "Healthy" } else { "Attention Required" }
    }
}

$dashboard = Get-DailySecurityDashboard
$dashboard | Format-List

# Esportare per aggregazione centralizzata
$dashboard | Export-Csv "C:\Reports\SecurityDashboard-$(Get-Date -Format 'yyyyMMdd').csv" -NoTypeInformation -Append
```

### Indicatori di Compromissione (IoC) Custom

Microsoft Defender for Endpoint supporta l'importazione di indicatori personalizzati per bloccare o segnalare minacce specifiche dell'organizzazione.

```powershell
# Aggiungere IoC tramite Graph API (richiede MDE Plan 2)
$ioc = @{
    indicatorValue = "malicious-domain.com"
    indicatorType = "DomainName"
    action = "AlertAndBlock"
    title = "Dominio malevolo identificato dal team SOC"
    description = "Blocco C2 domain - Ticket INC-5678"
    severity = "High"
    recommendedActions = "Investigare i dispositivi che hanno comunicato con questo dominio"
    expirationTime = (Get-Date).AddDays(90).ToString("yyyy-MM-ddTHH:mm:ssZ")
    generateAlert = $true
} | ConvertTo-Json

$headers = @{
    Authorization = "Bearer $accessToken"
    "Content-Type" = "application/json"
}

Invoke-RestMethod -Uri "https://api.securitycenter.microsoft.com/api/indicators" `
    -Method POST -Headers $headers -Body $ioc

# Tipi di indicatori supportati:
# - FileSha1, FileSha256, FileMd5 (hash di file)
# - IpAddress (indirizzi IP)
# - DomainName (domini)
# - Url (URL complete)
# - CertificateThumbprint (certificati)

# Azioni disponibili:
# - Alert (solo notifica)
# - AlertAndBlock (notifica e blocco)
# - Allowed (whitelist esplicita)
```

### Problema: ASR Rules Bloccano Applicazioni Aziendali Legittime

**Sintomi**: Dopo l'attivazione delle ASR rules, alcune applicazioni aziendali smettono di funzionare. Gli utenti segnalano errori durante l'uso di macro Office, script PowerShell aziendali o tool di automazione.

**Causa**: Le ASR rules sono progettate per bloccare comportamenti comunemente sfruttati dal malware, ma alcune applicazioni legittime utilizzano le stesse tecniche (es. macro Office che chiamano Win32 API, script che lanciano processi figlio da Office).

**Soluzione**:

```powershell
# 1. Identificare quale regola ASR sta bloccando
Get-WinEvent -FilterHashtable @{
    LogName = "Microsoft-Windows-Windows Defender/Operational"
    ID = 1121  # ASR Block
} -MaxEvents 50 | ForEach-Object {
    $xml = [xml]$_.ToXml()
    [PSCustomObject]@{
        Time      = $_.TimeCreated
        RuleId    = ($xml.Event.EventData.Data | Where-Object { $_.Name -eq "ID" }).'#text'
        Process   = ($xml.Event.EventData.Data | Where-Object { $_.Name -eq "Process Name" }).'#text'
        Path      = ($xml.Event.EventData.Data | Where-Object { $_.Name -eq "Path" }).'#text'
    }
} | Format-Table -AutoSize

# 2. Passare la regola specifica in Audit Mode temporaneamente
$ruleId = "D4F940AB-401B-4EFC-AADC-AD5F3C50688A"  # Esempio: Block Office child processes
Add-MpPreference -AttackSurfaceReductionRules_Ids $ruleId `
    -AttackSurfaceReductionRules_Actions AuditMode

# 3. Aggiungere esclusione per il processo specifico (non per intere cartelle)
Add-MpPreference -AttackSurfaceReductionOnlyExclusions "C:\Program Files\AziendaApp\trusted.exe"

# 4. Ritornare in Block mode dopo aver configurato l'esclusione
Add-MpPreference -AttackSurfaceReductionRules_Ids $ruleId `
    -AttackSurfaceReductionRules_Actions Enabled
```

### Problema: Controlled Folder Access Blocca Applicazioni di Backup

**Sintomi**: Il software di backup aziendale non riesce a scrivere nelle cartelle protette da Controlled Folder Access. Il backup fallisce con errori di accesso negato.

**Causa**: Il processo del software di backup non è nella whitelist di Controlled Folder Access. Solo le applicazioni Microsoft "attendibili" e le applicazioni esplicitamente autorizzate possono scrivere nelle cartelle protette.

**Soluzione**:

```powershell
# Identificare i blocchi CFA nel log
Get-WinEvent -FilterHashtable @{
    LogName = "Microsoft-Windows-Windows Defender/Operational"
    ID = 1123  # CFA Block
} -MaxEvents 20 | Select-Object TimeCreated, Message | Format-Table -Wrap

# Aggiungere l'applicazione di backup alla whitelist
Add-MpPreference -ControlledFolderAccessAllowedApplications "C:\Program Files\Veeam\Backup\Veeam.Backup.Agent.exe"
Add-MpPreference -ControlledFolderAccessAllowedApplications "C:\Program Files\BackupSoft\backup-service.exe"

# Verificare la whitelist
Get-MpPreference | Select-Object -ExpandProperty ControlledFolderAccessAllowedApplications
```

### Problema: MDE Onboarding Fallisce — Stato "Inactive"

**Sintomi**: Dopo l'esecuzione dello script di onboarding, il dispositivo non compare nel portale MDE oppure mostra stato "Inactive".

**Causa**: Problemi di connettività verso gli endpoint cloud di MDE, proxy non configurato, certificato client non valido, oppure prerequisiti mancanti (Windows versione minima, spazio disco).

**Soluzione**:

```powershell
# Verificare lo stato di onboarding
$onboarding = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows Advanced Threat Protection\Status" -ErrorAction SilentlyContinue
$onboarding | Select-Object OnboardingState, SenseIsRunning, OrgId

# Verificare che il servizio MsSense sia in esecuzione
Get-Service "Sense" | Select-Object Status, StartType

# Eseguire il test di connettività MDE (Client Connectivity Analyzer)
# Download: https://go.microsoft.com/fwlink/p/?linkid=823109
# Oppure test manuale degli endpoint:
$endpoints = @(
    "winatp-gw-cus.microsoft.com",
    "winatp-gw-eus.microsoft.com",
    "winatp-gw-weu.microsoft.com",
    "eu-v20.events.data.microsoft.com",
    "settings-win.data.microsoft.com"
)

foreach ($ep in $endpoints) {
    $result = Test-NetConnection -ComputerName $ep -Port 443 -WarningAction SilentlyContinue
    Write-Output "$ep : $($result.TcpTestSucceeded)"
}

# Se dietro proxy, configurare il proxy per MDE
netsh winhttp set proxy proxy-server="http://proxy.contoso.com:8080" bypass-list="*.contoso.com"

# Rieseguire l'onboarding
& "C:\Temp\WindowsDefenderATPLocalOnboardingScript.cmd"
```

### Problema: WDAC in Audit Mode Genera Troppi Eventi

**Sintomi**: Dopo l'attivazione di WDAC in Audit Mode, il log eventi CodeIntegrity genera migliaia di eventi al giorno, rendendo l'analisi impraticabile.

**Causa**: La policy è troppo restrittiva per l'ambiente, oppure mancano regole per applicazioni legittime comunemente utilizzate (tool di sistema, script, utilità).

**Soluzione**:

```powershell
# Analizzare gli eventi CodeIntegrity aggregandoli per file bloccato
$events = Get-WinEvent -FilterHashtable @{
    LogName = "Microsoft-Windows-CodeIntegrity/Operational"
    ID = 3076  # Audit block
} -MaxEvents 5000

$events | ForEach-Object {
    $xml = [xml]$_.ToXml()
    [PSCustomObject]@{
        File   = ($xml.Event.EventData.Data | Where-Object { $_.Name -eq "FileName" }).'#text'
        Signer = ($xml.Event.EventData.Data | Where-Object { $_.Name -eq "PublisherName" }).'#text'
    }
} | Group-Object File | Sort-Object Count -Descending | Select-Object -First 30 Count, Name

# Convertire gli eventi audit in regole WDAC
# Usare il WDAC Wizard o:
New-CIPolicy -Audit -Level Publisher -FilePath "C:\WDAC\AuditRules.xml" -UserPEs

# Unire le regole audit con la policy base
Merge-CIPolicy -PolicyPaths "C:\WDAC\BasePolicy.xml", "C:\WDAC\AuditRules.xml" `
    -OutputFilePath "C:\WDAC\MergedPolicy.xml"
```

### Problema: Network Protection Blocca Accesso a Siti Interni Aziendali

**Sintomi**: Dopo l'attivazione di Network Protection, gli utenti non riescono ad accedere a siti web interni o applicazioni web aziendali. Il browser mostra un blocco SmartScreen.

**Causa**: Network Protection utilizza il database di reputazione Microsoft SmartScreen. Siti interni non nel database, siti con certificati self-signed, o siti il cui dominio è simile a domini malevoli noti possono essere bloccati.

**Soluzione**:

```powershell
# Identificare i blocchi di Network Protection
Get-WinEvent -FilterHashtable @{
    LogName = "Microsoft-Windows-Windows Defender/Operational"
    ID = 1125, 1126  # Network Protection Block/Audit
} -MaxEvents 50 | Select-Object TimeCreated, Message | Format-Table -Wrap

# Creare indicatori "Allow" nel portale MDE per i siti interni
# security.microsoft.com → Settings → Endpoints → Indicators → URLs/Domains
# Aggiungere il dominio interno con action "Allow"

# Oppure configurare Custom Network Indicators via GPO
# Computer Configuration → Administrative Templates →
#   Windows Components → Microsoft Defender Antivirus →
#     Microsoft Defender Exploit Guard → Network Protection:
#       "Prevent users and apps from accessing dangerous websites": Block
#       (e usare gli indicatori nel portale per le esclusioni)
```

### Problema: Defender Definitions Obsolete in Ambienti Isolati

**Sintomi**: In ambienti air-gapped o con accesso internet limitato, le definizioni Defender diventano obsolete. Il campo "Signature age" mostra valori superiori a 7 giorni.

**Causa**: L'endpoint non riesce a raggiungere Windows Update, WSUS o il Microsoft Malware Protection Center (MMPC) per scaricare gli aggiornamenti.

**Soluzione**:

```powershell
# Configurare una share di rete come sorgente definizioni
Set-MpPreference -SignatureFallbackOrder "FileShares|InternalDefinitionUpdateServer"
Set-MpPreference -DefinitionUpdateFileSharesSources "\\air-gap-server\WDDefs"

# Script per aggiornare la share da una macchina con accesso internet
# (da eseguire su un jump host o via scheduled task)
$defUrls = @{
    "mpam-fe-x64.exe" = "https://go.microsoft.com/fwlink/?LinkID=121721&arch=x64"
    "mpam-fe-x86.exe" = "https://go.microsoft.com/fwlink/?LinkID=121721&arch=x86"
    "nis_full.exe"    = "https://go.microsoft.com/fwlink/?LinkId=211054"
}

$sharePath = "\\air-gap-server\WDDefs"
foreach ($file in $defUrls.Keys) {
    Invoke-WebRequest -Uri $defUrls[$file] -OutFile (Join-Path $sharePath $file) -UseBasicParsing
}

# Applicare le definizioni manualmente su un endpoint
& "\\air-gap-server\WDDefs\mpam-fe-x64.exe"
```

### Problema: Event ID 5007 — Configurazione Defender Modificata Inaspettatamente

**Sintomi**: I log mostrano Event ID 5007 con modifiche alla configurazione di Defender che non sono state autorizzate. Le esclusioni cambiano, la real-time protection si disabilita o le ASR rules vengono modificate.

**Causa**: Se Tamper Protection è disabilitata, malware o script malevoli possono modificare la configurazione di Defender. Anche GPO conflittuali tra più livelli LSDO possono causare modifiche inattese.

**Soluzione**:

```powershell
# Analizzare gli eventi 5007 per capire cosa è cambiato
Get-WinEvent -FilterHashtable @{
    LogName = "Microsoft-Windows-Windows Defender/Operational"
    ID = 5007
} -MaxEvents 20 | ForEach-Object {
    [PSCustomObject]@{
        Time    = $_.TimeCreated
        Change  = $_.Message -replace "Microsoft Defender Antivirus Configuration has changed.*\n", ""
    }
} | Format-Table -Wrap

# Verificare se le modifiche vengono da GPO
gpresult /H C:\Temp\gpresult-defender.html /F
# Cercare nel report: "Windows Components → Microsoft Defender Antivirus"

# Abilitare Tamper Protection (richiede Intune o portale M365 Defender)
# Verificare lo stato attuale:
(Get-MpComputerStatus).IsTamperProtected
```

### Problema: Tamper Protection Blocca Modifiche Amministrative Legittime

**Sintomi**: Un amministratore tenta di modificare le esclusioni di Defender, disabilitare una ASR rule o aggiornare la configurazione tramite PowerShell o GPO, ma le modifiche vengono ignorate silenziosamente o revertite entro pochi secondi.

**Causa**: Tamper Protection (TP) impedisce qualsiasi modifica alla configurazione di sicurezza da processi locali, inclusi script amministrativi e GPO. Quando TP è abilitata (default con MDE), solo il portale Microsoft 365 Defender o Intune possono modificare la configurazione.

**Soluzione**:

```powershell
# Verificare lo stato di Tamper Protection
(Get-MpComputerStatus).IsTamperProtected

# Se necessario modificare la configurazione localmente per troubleshooting:
# 1. Disabilitare TP temporaneamente dal portale MDE
#    Security.microsoft.com → Settings → Endpoints → Advanced features → Tamper Protection → Off
# 2. Effettuare le modifiche necessarie
# 3. Riabilitare TP immediatamente

# Per esclusioni gestite centralmente (raccomandato):
# Usare Intune: Endpoint security → Antivirus → Policy → Exclusions
# Oppure Microsoft Defender portal: Settings → Endpoints → Indicators
```

### Problema: Defender Entra in Passive Mode Inaspettatamente

**Sintomi**: Defender Antivirus mostra lo stato "Passive Mode" nonostante nessun antivirus di terze parti sia installato. La protezione real-time è disattivata, le scansioni automatiche non vengono eseguite.

**Causa**: Un antivirus precedente è stato disinstallato in modo incompleto e rimane registrato nel Windows Security Center (WSC). Oppure un software di gestione endpoint registra un componente antivirus nel WSC. In rari casi, una chiave di registro corrotta forza il passive mode.

**Soluzione**:

```powershell
# Verificare quale AV è registrato nel Security Center
Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct |
  Select-Object displayName, productState, pathToSignedReportingExe

# Se compare un AV non più installato, rimuoverne la registrazione
# Metodo 1: Reinstallare e disinstallare correttamente il vecchio AV
# Metodo 2: Usare il tool di rimozione del vendor (es. Norton Remove and Reinstall, McAfee MCPR)

# Verificare la chiave di registro ForceDefenderPassiveMode
Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows Advanced Threat Protection" -Name ForceDefenderPassiveMode -ErrorAction SilentlyContinue

# Se il valore è 1, rimuoverlo (se non richiesto da policy)
# Remove-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows Advanced Threat Protection" -Name ForceDefenderPassiveMode

# Verificare lo stato finale
(Get-MpComputerStatus).AMRunningMode
# Deve restituire "Normal" per protezione attiva completa
```

### Problema: Cloud Protection Timeout in Ambienti con Proxy

**Sintomi**: Le scansioni impiegano molto tempo, la cloud protection mostra errori di connettività, Event ID 2010 nel log di Defender. La Block at First Sight non funziona — file sospetti vengono eseguiti senza analisi cloud.

**Causa**: Il proxy aziendale blocca o rallenta le connessioni verso i servizi Microsoft Defender cloud (`*.wdcp.microsoft.com`, `*.wd.microsoft.com`). Il proxy non supporta le connessioni SSL pinned di Defender, oppure richiede autenticazione che il servizio Defender non può fornire.

**Soluzione**:

```powershell
# Testare la connettività cloud di Defender
Start-MpWDOScan  # Cloud connectivity test

# Verificare la raggiungibilità degli endpoint cloud
$endpoints = @(
    "https://wdcp.microsoft.com",
    "https://wdcpalt.microsoft.com",
    "https://definitionupdates.microsoft.com"
)
foreach ($url in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10
        Write-Host "$url → $($response.StatusCode)" -ForegroundColor Green
    } catch {
        Write-Host "$url → FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Configurare il proxy per Defender (specifico per il servizio, non sistema)
Set-MpPreference -ProxyServer "http://proxy.azienda.local:8080"
Set-MpPreference -ProxyBypass "*.local;10.*"

# Oppure: configurare via Netsh per WinHTTP (usato da servizi)
netsh winhttp set proxy proxy-server="http://proxy.azienda.local:8080" bypass-list="*.local;10.*"
```

### Problema: Exploit Protection Causa Crash di Applicazioni Specifiche

**Sintomi**: Un'applicazione aziendale (es. ERP, CAD, software legacy) crasha all'avvio o durante operazioni specifiche dopo l'abilitazione di Exploit Protection. I log mostrano eccezioni hardware o violazioni di accesso.

**Causa**: Le mitigazioni di Exploit Protection (DEP, ASLR, CFG, EAF) sono incompatibili con applicazioni che usano tecniche di allocazione memoria non standard, JIT compilation aggressiva, o plugin legacy.

**Soluzione**:

```powershell
# Identificare quale mitigazione causa il problema
# Controllare Event ID 1 nel log di Exploit Protection
Get-WinEvent -FilterHashtable @{
    LogName = "Microsoft-Windows-Security-Mitigations/KernelMode"
    ID = 1
} -MaxEvents 10 | ForEach-Object { $_.Message }

# Disabilitare mitigazioni specifiche per l'applicazione problematica
Set-ProcessMitigation -Name "app.exe" -Disable DEP, ForceRelocateImages

# Esportare la configurazione attuale per backup
Get-ProcessMitigation -RegistryConfigFilePath C:\Temp\exploit-protection-backup.xml

# Verificare le mitigazioni attive per un processo
Get-ProcessMitigation -Name "app.exe"

# Best practice: disabilitare una mitigazione alla volta per isolare il problema
# DEP → ASLR → CFG → EAF → nell'ordine fino a trovare la causa
```

### Problema: Advanced Hunting (MDE) Non Restituisce Risultati

**Sintomi**: Le query KQL in Advanced Hunting restituiscono risultati vuoti o parziali, nonostante gli endpoint siano onboarded e attivi.

**Causa**: I dati di telemetria hanno un ritardo di ingestione (fino a 30 minuti), le tabelle hanno retention limitata (30 giorni default), gli endpoint non inviano telemetria completa (sensor ridotto, banda limitata, o privacy settings), oppure la query ha filtri troppo restrittivi.

**Soluzione**:

```kusto
// Verificare che l'endpoint invii dati (query diagnostica)
DeviceInfo
| where Timestamp > ago(1d)
| summarize LastSeen = max(Timestamp), DataTypes = dcount(ReportId) by DeviceName
| sort by LastSeen asc

// Se un device non compare, verificare lato endpoint:
// 1. Il servizio "Sense" (MDE sensor) è in esecuzione
// 2. L'onboarding è completato: OnboardingState = 1
// 3. Il device comunica con il cloud: connettività verso *.securitycenter.windows.com

// Verificare la retention dei dati nella tabella
DeviceEvents
| where Timestamp > ago(30d)
| summarize EarliestEvent = min(Timestamp), LatestEvent = max(Timestamp)

// Tip: per query su periodi più lunghi, usare Custom Detection rules
// che possono salvare risultati incrementali in tabelle personalizzate
```

---

## FAQ — Domande Frequenti

### 1. Microsoft Defender Antivirus funziona insieme ad altri antivirus?

No, per design. Quando un antivirus di terze parti viene installato e registrato nel Security Center, Defender Antivirus entra in **passive mode**: le scansioni in tempo reale vengono disabilitate, ma il motore resta disponibile per le scansioni on-demand. Se Microsoft Defender for Endpoint (EDR) è attivo, Defender Antivirus resta in passive mode ma continua a inviare telemetria al cloud. In ambienti con MDE Plan 2, è possibile abilitare "EDR in block mode" per permettere a Defender di agire come livello di protezione secondario anche in presenza di un AV di terze parti.

### 2. Le ASR rules richiedono una licenza specifica?

Le ASR rules sono disponibili con Windows 10/11 Enterprise, Education e Pro. Tuttavia, la gestione centralizzata tramite Intune o il portale MDE richiede una licenza Microsoft Defender for Endpoint Plan 1 o Plan 2. La configurazione via GPO o PowerShell locale è disponibile senza licenza aggiuntiva.

### 3. Qual è la differenza tra Block, Audit e Warn nelle ASR rules?

- **Block**: Il comportamento viene bloccato e viene generato un evento 1121.
- **Audit**: Il comportamento è consentito ma viene registrato un evento 1122 per analisi.
- **Warn**: L'utente riceve un popup di avvertimento e può scegliere di consentire l'azione (utile per la fase di transizione).

### 4. WDAC sostituisce AppLocker?

Funzionalmente sì, WDAC è il successore raccomandato di AppLocker. WDAC opera a livello kernel, supporta policy supplementari, Managed Installer e ISG integration. AppLocker opera a livello utente ed è aggirabile da utenti con privilegi amministrativi. Microsoft raccomanda WDAC per nuovi deployment, ma continua a supportare AppLocker per compatibilità.

### 5. Come posso verificare se un endpoint è protetto da MDE?

```powershell
# Verifica rapida
$mdeSensor = Get-Service "Sense" -ErrorAction SilentlyContinue
$onboardState = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows Advanced Threat Protection\Status" -ErrorAction SilentlyContinue).OnboardingState

[PSCustomObject]@{
    ServiceRunning = ($mdeSensor.Status -eq "Running")
    Onboarded      = ($onboardState -eq 1)
    OrgId          = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows Advanced Threat Protection\Status" -ErrorAction SilentlyContinue).OrgId
}
```

### 6. Controlled Folder Access protegge anche le cartelle di rete?

No, Controlled Folder Access protegge solo le cartelle locali. Le cartelle mappate come drive di rete non sono protette. Per proteggere i file server, è necessario configurare CFA direttamente sul server e aggiungere le cartelle condivise come cartelle protette.

### 7. La Cloud Protection invia i miei file al cloud Microsoft?

Dipende dalla configurazione di `SubmitSamplesConsent`:
- **SendSafeSamples** (default): Solo file PE (eseguibili) considerati sospetti.
- **SendAllSamples**: Tutti i file sospetti, inclusi documenti.
- **AlwaysPrompt**: Chiede conferma all'utente.
- **NeverSend**: Non invia campioni (solo metadati).

In tutti i casi, i **metadati** vengono sempre inviati (hash, path, comportamento). I file completi vengono inviati solo quando necessario per l'analisi cloud.

### 8. Network Protection funziona con browser di terze parti (Chrome, Firefox)?

Sì. A differenza di SmartScreen (che protegge solo Microsoft Edge), Network Protection opera a livello di stack TCP/IP e protegge tutte le connessioni in uscita, indipendentemente dal browser o dall'applicazione. Questo include Chrome, Firefox, client email, applicazioni personalizzate e qualsiasi processo che apre connessioni di rete.

### 9. Come monitoro centralmente lo stato di Defender su tutti gli endpoint senza MDE?

Senza MDE, le opzioni sono:
- **WSUS Reporting**: Mostra lo stato degli aggiornamenti delle definizioni.
- **Windows Event Forwarding**: Centralizzare gli eventi Defender verso un collector/SIEM.
- **PowerShell Remoting**: Script periodico con `Invoke-Command` verso tutti gli endpoint.
- **MECM/SCCM**: Endpoint Protection dashboard se si usa Configuration Manager.

### 10. Quanto impatto hanno le ASR rules sulle prestazioni?

L'impatto è generalmente trascurabile. Le ASR rules monitorano comportamenti specifici (creazione processi, accesso a LSASS, esecuzione script) e intervengono solo quando il pattern corrisponde. In benchmark Microsoft, l'overhead delle ASR rules è inferiore all'1% del tempo CPU. L'unica regola con potenziale impatto misurabile è "Block credential stealing from LSASS" su server con molte autenticazioni simultanee.

### 11. Posso usare Defender for Endpoint su Linux e macOS?

Sì. MDE supporta:
- **Linux**: Ubuntu 18.04+, RHEL 7.2+, CentOS 7.2+, Debian 9+, SUSE 12+, Oracle Linux 7.2+, Amazon Linux 2, Fedora 33+
- **macOS**: Big Sur (11) e successivi
- **iOS/iPadOS**: 15.0+
- **Android**: 8.0+

Su Linux e macOS, MDE fornisce: antimalware, EDR, vulnerability management e network protection. La gestione avviene tramite lo stesso portale Microsoft 365 Defender.

### 12. Come funziona la Automated Investigation and Response? Può essere pericolosa?

AIR segue playbook predefiniti e propone azioni di remediation. Il comportamento dipende dal livello di automazione configurato:
- **Full automation**: Le azioni vengono eseguite automaticamente (quarantena file, isolamento device).
- **Semi automation**: Le azioni vengono proposte e attendono l'approvazione di un analista.
- **No automation**: Solo investigazione automatica, tutte le azioni richiedono approvazione manuale.

Per ambienti nuovi, si raccomanda di iniziare con **Semi automation** e passare a Full solo dopo aver validato il comportamento.

### 13. Come disabilito temporaneamente Defender per installare un software legittimo che viene bloccato?

Non disabilitare mai la protezione in tempo reale. Invece:
1. Aggiungere un'**esclusione** per il file specifico (per hash o percorso).
2. Sottomettere il file a Microsoft come falso positivo.
3. Se è un'esclusione temporanea, rimuoverla dopo l'installazione.

```powershell
# Esclusione temporanea per installazione
Add-MpPreference -ExclusionPath "C:\Temp\Installer"
# ... installare ...
Remove-MpPreference -ExclusionPath "C:\Temp\Installer"
```

### 14. Exploit Protection è compatibile con tutti i software?

No. Alcune mitigazioni possono causare incompatibilità con software legacy o specializzato. In particolare:
- **Arbitrary Code Guard (ACG)** è incompatibile con applicazioni che usano JIT compilation (Java, .NET runtime vecchi, alcuni browser).
- **Export Address Filtering (EAF)** può causare problemi con debugger e tool di sviluppo.
- **SEHOP** può essere incompatibile con software compilato con vecchi compilatori.

Testare sempre in audit mode prima dell'enforcement per applicazione.

### 15. Cosa succede se disabilito Cloud Protection per motivi di privacy?

Disabilitare la Cloud Protection riduce significativamente l'efficacia di Defender. Senza cloud, il motore si affida esclusivamente alle firme locali e alle euristiche — perde la capacità di:
- Bloccare minacce zero-day in tempo reale (Block at First Sight)
- Analizzare file sconosciuti con ML avanzato
- Ricevere aggiornamenti di protezione rapidi (cloud signature delivery)

Per ambienti con vincoli di privacy, configurare `SubmitSamplesConsent = NeverSend` per inviare solo metadati (hash, path) senza campioni di file. Questo mantiene la maggior parte dei benefici della cloud protection senza inviare contenuto di file sensibili.

### 16. Come configuro Defender per un ambiente VDI (Virtual Desktop Infrastructure)?

Per VDI persistente (desktop dedicato), la configurazione è identica a un desktop fisico. Per VDI non-persistente (pooled desktops), configurare:

```powershell
# Ottimizzazioni per VDI non-persistente
Set-MpPreference -DisableArchiveScanning $true          # Riduce I/O
Set-MpPreference -ScanAvgCPULoadFactor 20               # CPU limitato
Set-MpPreference -DisableScanningMappedNetworkDrivesForFullScan $true
Set-MpPreference -DisableScanningNetworkFiles $true     # Per VM con profilo roaming
Set-MpPreference -SharedSignaturesPath "\\fileserver\WDDefinitions"  # Definizioni condivise
# Configurare la scansione rapida (non completa) come scansione pianificata
Set-MpPreference -ScanParameters 1  # 1 = Quick scan
```

### 17. Quali sono gli Event ID più importanti di Defender da monitorare?

| Event ID | Log | Significato |
|----------|-----|------------|
| 1006 | Operational | Motore aggiornato |
| 1116 | Operational | Malware rilevato |
| 1117 | Operational | Azione eseguita su malware |
| 1118 | Operational | Azione su malware fallita |
| 1119 | Operational | Errore critico durante azione |
| 1121 | Operational | ASR rule block |
| 1122 | Operational | ASR rule audit |
| 1123 | Operational | Controlled Folder Access block |
| 1125 | Operational | Network Protection block |
| 2050 | Operational | Errore motore — possibile evasione |
| 3076 | CodeIntegrity | WDAC audit block |
| 3077 | CodeIntegrity | WDAC enforcement block |
| 5001 | Operational | Real-time protection disabilitata |
| 5007 | Operational | Configurazione modificata |
| 5010 | Operational | Scansione disabilitata tramite policy |
| 5012 | Operational | Scansione fallita |

---

## Esercizi

### Domande a Risposta Aperta

**1.** Un'organizzazione sta valutando se implementare WDAC o AppLocker per il whitelisting delle applicazioni. L'ambiente include workstation Windows 11 Enterprise gestite da Intune, con utenti che hanno privilegi di amministratore locale per ragioni operative. Quale soluzione consiglieresti e perché? Descrivi i vantaggi architetturali della scelta raccomandata in questo specifico scenario.

**2.** Descrivi il processo completo di rollout delle ASR rules in un'organizzazione con 2.000 endpoint, partendo dalla fase di assessment fino all'enforcement completo. Indica le tempistiche raccomandate per ogni fase, come gestire i falsi positivi, e quali Event ID monitorare durante ogni fase.

**3.** Un analista SOC rileva tramite Advanced Hunting (KQL) che un endpoint ha eseguito `powershell.exe -encodedcommand [base64]` seguito da connessioni verso un IP esterno sconosciuto. Descrivi il workflow completo di investigazione e risposta utilizzando le capacità di MDE: quali tabelle KQL interrogare, quali azioni di Live Response eseguire, e come contenere la minaccia.

**4.** Spiega la differenza tra UMCI e KMCI in WDAC, indicando cosa controlla ciascun componente, quando è appropriato abilitare UMCI, e quale ruolo giocano le Microsoft Recommended Driver Block Rules nella protezione del kernel.

**5.** Un'organizzazione con requisiti di privacy stringenti deve configurare Microsoft Defender Antivirus minimizzando i dati inviati al cloud Microsoft, ma senza rinunciare completamente alla protezione cloud. Descrivi la configurazione ottimale e il trade-off in termini di efficacia della protezione.

### Vero / Falso

**1.** Tamper Protection può essere configurata tramite Group Policy (GPO) quando il dispositivo è gestito da Active Directory on-premises senza Intune.
→ **Falso.** Tamper Protection può essere gestita esclusivamente tramite il portale Microsoft 365 Defender o Microsoft Intune. Le GPO locali e gli script PowerShell non possono abilitare o disabilitare Tamper Protection. Fonte: https://learn.microsoft.com/en-us/defender-endpoint/prevent-changes-to-security-settings-with-tamper-protection (consultato: 2026-05-23)

**2.** AppLocker opera a livello kernel ed è quindi immune al bypass da parte di utenti con privilegi di amministratore locale.
→ **Falso.** AppLocker opera a livello user-mode tramite il servizio AppIDSvc. Un amministratore locale può fermare il servizio, modificare le regole, o aggirare le protezioni. WDAC, non AppLocker, opera a livello kernel.

**3.** La ASR rule "Block credential stealing from LSASS" (9E6C4E1F-7D60-472F-BA1A-A39EF669E4B2) mappa alla tecnica MITRE ATT&CK T1003.001 (LSASS Memory).
→ **Vero.** Questa regola impedisce ai processi non attendibili di aprire un handle verso il processo LSASS per leggere le credenziali dalla memoria, bloccando tool come Mimikatz.

**4.** Quando WDAC e AppLocker sono entrambi attivi sullo stesso sistema e una regola AppLocker consente un file che WDAC blocca, AppLocker ha la precedenza perché le sue regole sono più specifiche.
→ **Falso.** WDAC ha sempre la precedenza. Poiché WDAC opera a livello kernel (prima del caricamento del codice), se WDAC blocca un file, AppLocker non può autorizzarlo.

**5.** Network Protection protegge solo le connessioni effettuate tramite Microsoft Edge, analogamente a SmartScreen.
→ **Falso.** A differenza di SmartScreen (che protegge solo Edge), Network Protection opera a livello di stack TCP/IP e protegge tutte le connessioni in uscita da qualsiasi browser o applicazione.

### Esercizi Basati su Scenario

**Scenario 1 — WDAC Blocking Critico:** Dopo aver deployato una policy WDAC in enforcement mode, l'applicazione ERP aziendale smette di funzionare. Il log CodeIntegrity mostra Event ID 3077 per `erp-client.exe`. L'applicazione è firmata dal vendor ma non era nella golden image usata per creare la policy. Descrivi i passi per risolvere il problema senza disabilitare WDAC completamente.

→ **Soluzione attesa:** 1) Identificare il publisher del certificato dall'evento 3077; 2) Creare una supplemental policy con `New-CIPolicy -Level Publisher` che scansiona il percorso dell'applicazione ERP; 3) Collegare la supplemental policy alla base policy tramite `Set-CIPolicyIdInfo`; 4) Convertire con `ConvertFrom-CIPolicy` e deployare in `C:\Windows\System32\CodeIntegrity\CiPolicies\Active\`; 5) In alternativa, usare il WDAC Wizard per generare regole dagli eventi audit.

**Scenario 2 — ASR False Positive in Produzione:** Il team finance segnala che una macro Excel critica per la chiusura mensile ha smesso di funzionare. L'analisi mostra Event ID 1121 per la regola `92E97FA1-2EDF-4476-BDD6-9DD0B4DDDC7B` (Block Win32 API calls from Office macros). La macro chiama funzioni Win32 API per interagire con un sistema legacy. Come gestisci la situazione bilanciando sicurezza e operatività?

→ **Soluzione attesa:** 1) Passare temporaneamente la regola in Warn mode per non bloccare il lavoro; 2) Identificare l'eseguibile specifico della macro (il processo Excel che carica il file); 3) Aggiungere un'esclusione ASR chirurgica per il file Excel specifico, NON per tutto Excel; 4) Valutare con il team finance se la macro può essere riscritta senza chiamate Win32 API dirette; 5) Ripristinare la regola in Block mode dopo aver configurato l'esclusione; 6) Documentare l'esclusione per la revisione trimestrale.

**Scenario 3 — MDE Connectivity Failure:** 50 endpoint in una branch office risultano "Inactive" nel portale MDE da 3 giorni. I dispositivi sono onboarded (OnboardingState = 1) e il servizio Sense è in esecuzione. Il test di connettività verso `winatp-gw-weu.microsoft.com:443` fallisce. La branch office usa un proxy autenticato. Come diagnostichi e risolvi?

→ **Soluzione attesa:** 1) Verificare che il proxy sia configurato per il servizio MDE: `netsh winhttp show proxy`; 2) Configurare il proxy per WinHTTP: `netsh winhttp set proxy proxy-server="proxy:8080" bypass-list="*.local"`; 3) Se il proxy richiede autenticazione, MDE non supporta l'autenticazione proxy — configurare un'eccezione sul proxy per gli URL MDE senza autenticazione; 4) URL da aggiungere alle eccezioni: `*.securitycenter.windows.com`, `*.events.data.microsoft.com`, `*.blob.core.windows.net`; 5) Rieseguire il test di connettività e verificare che gli endpoint tornino "Active" nel portale.

**Scenario 4 — Ransomware Defense Validation:** Il CISO chiede una dimostrazione che le difese endpoint possono resistere a un attacco ransomware. Utilizzando le funzionalità native di Windows Defender (senza tool di terze parti), descrivi quali layer di protezione attivare e come verificarne il funzionamento con le simulazioni di attacco di MDE.

→ **Soluzione attesa:** Layer di protezione: 1) Controlled Folder Access in Block mode per proteggere documenti dalla cifratura; 2) ASR rule C1DB55AB "Advanced ransomware protection" in Block mode; 3) ASR rule per bloccare processi da WMI e script offuscati; 4) Cloud Protection con CloudBlockLevel HighPlus per bloccare eseguibili sconosciuti; 5) Network Protection per bloccare connessioni C2. Verifica: usare Attack Simulation Training nel portale MDE per simulare un payload ransomware, monitorare gli Event ID 1121 (ASR block), 1123 (CFA block), e verificare nel portale che l'alert viene generato e AIR avvia l'investigazione automatica.

**Scenario 5 — Scan Performance su File Server:** Un file server Windows Server 2025 con 15 TB di dati mostra utilizzo CPU al 100% durante le scansioni pianificate notturne, causando timeout nelle sessioni SMB degli utenti in fuso orario diverso. Come ottimizzi la configurazione senza compromettere la sicurezza?

→ **Soluzione attesa:** 1) Ridurre il limite CPU: `Set-MpPreference -ScanAvgCPULoadFactor 15`; 2) Abilitare priorità bassa: `Set-MpPreference -EnableLowCpuPriority $true`; 3) Escludere i file di database e i file server-specific: `.mdf`, `.ldf`, `.edb`, `.dit`; 4) Escludere i processi del file server: `dfsr.exe`, `dfsrs.exe`, `ntfrs.exe`; 5) Configurare la scansione solo in stato idle: `Set-MpPreference -ScanOnlyIfIdleEnabled $true`; 6) Passare alla scansione rapida settimanale + scansione completa mensile invece che settimanale; 7) Verificare che la real-time protection resti attiva (la scansione pianificata è un supplemento, non la protezione primaria).

---

## Letture Primarie Consigliate

1. **Microsoft Defender Antivirus — Panoramica e configurazione**
   https://learn.microsoft.com/en-us/defender-endpoint/microsoft-defender-antivirus-windows
   (consultato: 2026-05-23) — Documentazione ufficiale completa per la configurazione di Defender Antivirus, cloud protection e MAPS.

2. **Attack Surface Reduction rules reference**
   https://learn.microsoft.com/en-us/defender-endpoint/attack-surface-reduction-rules-reference
   (consultato: 2026-05-23) — Riferimento completo di ogni regola ASR con GUID, descrizione, impatto e MITRE mapping.

3. **WDAC design guide**
   https://learn.microsoft.com/en-us/windows/security/application-security/application-control/windows-defender-application-control/design/wdac-design-guide
   (consultato: 2026-05-23) — Guida progettuale per WDAC: livelli di autorizzazione, policy merge, supplemental policies, Managed Installer.

4. **WDAC and AppLocker overview**
   https://learn.microsoft.com/en-us/windows/security/application-security/application-control/windows-defender-application-control/wdac-and-applocker-overview
   (consultato: 2026-05-23) — Confronto ufficiale tra WDAC e AppLocker.

5. **Exploit Protection reference**
   https://learn.microsoft.com/en-us/defender-endpoint/exploit-protection-reference
   (consultato: 2026-05-23) — Riferimento delle mitigazioni Exploit Protection con compatibilità e configurazione XML.

6. **Microsoft Defender for Endpoint — Advanced Hunting**
   https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-overview
   (consultato: 2026-05-23) — Guida completa ad Advanced Hunting con KQL, tabelle disponibili e query di esempio.

7. **Tamper Protection — Protezione delle impostazioni di sicurezza**
   https://learn.microsoft.com/en-us/defender-endpoint/prevent-changes-to-security-settings-with-tamper-protection
   (consultato: 2026-05-23) — Documentazione ufficiale su Tamper Protection, modello di gestione e implicazioni operative.

8. **MITRE ATT&CK — Enterprise Techniques**
   https://attack.mitre.org/techniques/enterprise/
   (consultato: 2026-05-23) — Framework di riferimento per le tecniche di attacco mappate nelle ASR rules e nei rilevamenti MDE.

9. **Microsoft Recommended Driver Block Rules**
   https://learn.microsoft.com/en-us/windows/security/application-security/application-control/windows-defender-application-control/design/microsoft-recommended-driver-block-rules
   (consultato: 2026-05-23) — Lista aggiornata dei driver vulnerabili bloccati da WDAC/KMCI.

10. **Intune Endpoint Security**
    https://learn.microsoft.com/en-us/mem/intune/protect/endpoint-security
    (consultato: 2026-05-23) — Gestione centralizzata di tutte le funzionalità Defender tramite Microsoft Intune.

---

## Collegamenti Incrociati

| Modulo | Relazione con questo modulo |
|---|---|
| → `05-sicurezza-windows.md` | Fondamenti di sicurezza Windows: UAC, Security Center, Windows Firewall — prerequisiti per comprendere il contesto in cui opera Defender |
| → `21-networking-avanzato.md` | Network stack Windows, DNS, proxy configuration — necessari per diagnosticare problemi di connettività MDE e Network Protection |
| → `28-group-policy-avanzato.md` | Configurazione avanzata GPO: LSDOU, security filtering, WMI filters — per il deployment di Defender settings via Group Policy |
| → `29-active-directory-security.md` | Sicurezza Active Directory: Kerberoasting, DCSync, lateral movement — complementa i rilevamenti di Microsoft Defender for Identity |
| → `22-powershell-scripting-avanzato.md` | PowerShell avanzato: remoting, error handling, moduli — per comprendere i cmdlet Defender e gli script di automazione |

---

## Glossario Locale

| Termine | Definizione |
|---|---|
| **AMSI** | Antimalware Scan Interface — interfaccia Windows che consente alle applicazioni (PowerShell, Office, browser) di inviare contenuto deoffuscato al motore antimalware per la scansione prima dell'esecuzione |
| **ASR** | Attack Surface Reduction — insieme di regole che bloccano comportamenti specifici comunemente sfruttati dal malware (creazione processi da Office, accesso a LSASS, script offuscati) |
| **BAFS** | Block at First Sight — funzionalità che blocca l'esecuzione di file sconosciuti fino a quando il verdetto cloud è disponibile; richiede cloud protection e automatic sample submission |
| **BYOVD** | Bring Your Own Vulnerable Driver — tecnica di attacco in cui l'attaccante carica un driver firmato ma vulnerabile per ottenere esecuzione di codice nel kernel |
| **CFA** | Controlled Folder Access — funzionalità anti-ransomware che impedisce a processi non attendibili di scrivere nelle cartelle protette (Documenti, Desktop, etc.) |
| **CFG** | Control Flow Guard — mitigazione che valida i target dei salti indiretti (call/jmp tramite puntatore) contro una bitmap di destinazioni valide compilata staticamente |
| **DHA** | Device Health Attestation — servizio che verifica l'integrità del boot chain utilizzando le misurazioni TPM per garantire che il dispositivo non sia stato compromesso |
| **EDR** | Endpoint Detection and Response — capacità di rilevamento e risposta post-compromissione che raccoglie telemetria dagli endpoint per threat hunting, investigazione e remediation |
| **ELAM** | Early Launch Antimalware — driver che si carica prima di tutti gli altri driver di terze parti durante il boot, garantendo che il motore antimalware sia attivo prima di qualsiasi codice potenzialmente malevolo |
| **HVCI** | Hypervisor-Protected Code Integrity — utilizza la virtualizzazione hardware per isolare il processo di verifica dell'integrità del codice dal kernel, impedendo al malware kernel-level di disabilitare le verifiche |
| **ISG** | Intelligent Security Graph — servizio cloud Microsoft che classifica file e URL basandosi sulla telemetria globale di miliardi di dispositivi; utilizzato da WDAC per autorizzare file con buona reputazione |
| **KMCI** | Kernel Mode Code Integrity — componente WDAC che verifica la firma e l'integrità di tutti i driver e moduli caricati nel kernel space |
| **KQL** | Kusto Query Language — linguaggio di query utilizzato in Advanced Hunting (MDE), Microsoft Sentinel e Azure Data Explorer per interrogare grandi dataset di telemetria |
| **LSASS** | Local Security Authority Subsystem Service — processo Windows (`lsass.exe`) che gestisce l'autenticazione locale e contiene credenziali in memoria; target primario per tool di credential dumping |
| **MAPS** | Microsoft Active Protection Service — servizio cloud che riceve metadati di file sospetti dagli endpoint e restituisce verdetti di classificazione in tempo reale |
| **MDE** | Microsoft Defender for Endpoint — piattaforma EDR enterprise che include sensore endpoint, advanced hunting, automated investigation, threat analytics e vulnerability management |
| **MDI** | Microsoft Defender for Identity — servizio cloud che monitora il traffico Active Directory per rilevare attacchi basati sull'identità (Pass-the-Hash, Kerberoasting, DCSync) |
| **SEHOP** | Structured Exception Handler Overwrite Protection — mitigazione che protegge la catena SEH dalla corruzione inserendo un cookie di validazione alla fine della catena |
| **UMCI** | User Mode Code Integrity — componente WDAC che verifica la firma e l'integrità del codice user-mode (applicazioni, DLL, script, MSI) prima del caricamento |
| **WDAC** | Windows Defender Application Control — soluzione di application whitelisting che opera a livello kernel per controllare quali applicazioni e driver possono essere eseguiti |

---

## Riferimenti

- Microsoft Docs: Microsoft Defender Antivirus — https://learn.microsoft.com/en-us/microsoft-365/security/defender-endpoint/microsoft-defender-antivirus-windows (consultato: 2026-05-23)
- Microsoft Docs: Attack Surface Reduction — https://learn.microsoft.com/en-us/microsoft-365/security/defender-endpoint/attack-surface-reduction (consultato: 2026-05-23)
- Microsoft Docs: ASR Rules Reference — https://learn.microsoft.com/en-us/defender-endpoint/attack-surface-reduction-rules-reference (consultato: 2026-05-23)
- Microsoft Docs: WDAC — https://learn.microsoft.com/en-us/windows/security/application-security/application-control/windows-defender-application-control/wdac (consultato: 2026-05-23)
- Microsoft Docs: WDAC and AppLocker Overview — https://learn.microsoft.com/en-us/windows/security/application-security/application-control/windows-defender-application-control/wdac-and-applocker-overview (consultato: 2026-05-23)
- Microsoft Docs: AppLocker — https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-locker/applocker-overview (consultato: 2026-05-23)
- Microsoft Docs: Exploit Protection — https://learn.microsoft.com/en-us/microsoft-365/security/defender-endpoint/exploit-protection (consultato: 2026-05-23)
- Microsoft Docs: Exploit Protection Reference — https://learn.microsoft.com/en-us/defender-endpoint/exploit-protection-reference (consultato: 2026-05-23)
- Microsoft Docs: Defender for Endpoint — https://learn.microsoft.com/en-us/microsoft-365/security/defender-endpoint/ (consultato: 2026-05-23)
- Microsoft Docs: Advanced Hunting — https://learn.microsoft.com/en-us/defender-xdr/advanced-hunting-overview (consultato: 2026-05-23)
- Microsoft Docs: Live Response — https://learn.microsoft.com/en-us/defender-endpoint/live-response (consultato: 2026-05-23)
- Microsoft Docs: Defender for Identity — https://learn.microsoft.com/en-us/defender-for-identity/ (consultato: 2026-05-23)
- Microsoft Docs: Tamper Protection — https://learn.microsoft.com/en-us/microsoft-365/security/defender-endpoint/prevent-changes-to-security-settings-with-tamper-protection (consultato: 2026-05-23)
- Microsoft Docs: Network Protection — https://learn.microsoft.com/en-us/microsoft-365/security/defender-endpoint/network-protection (consultato: 2026-05-23)
- Microsoft Docs: Intune Endpoint Security — https://learn.microsoft.com/en-us/mem/intune/protect/endpoint-security (consultato: 2026-05-23)
- Microsoft Docs: Microsoft Recommended Driver Block Rules — https://learn.microsoft.com/en-us/windows/security/application-security/application-control/windows-defender-application-control/design/microsoft-recommended-driver-block-rules (consultato: 2026-05-23)
- Microsoft Docs: SafeLinks — https://learn.microsoft.com/en-us/defender-office-365/safe-links-about (consultato: 2026-05-23)
- Microsoft Docs: Device Health Attestation — https://learn.microsoft.com/en-us/windows/security/hardware-security/tpm/how-windows-uses-the-tpm (consultato: 2026-05-23)
- Microsoft Docs: Defender PowerShell Module — https://learn.microsoft.com/en-us/powershell/module/defender/ (consultato: 2026-05-23)
- MITRE ATT&CK Framework — https://attack.mitre.org/ (consultato: 2026-05-23)
- MITRE ATT&CK Enterprise Techniques — https://attack.mitre.org/techniques/enterprise/ (consultato: 2026-05-23)
- WDAC Wizard — https://github.com/MicrosoftDocs/WDAC-Toolkit (consultato: 2026-05-23)
