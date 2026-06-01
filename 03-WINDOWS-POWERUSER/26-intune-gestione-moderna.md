# Microsoft Intune e Gestione Moderna degli Endpoint — Guida Approfondita

> **Modulo 26** · **Aggiornamento:** 2026-05-22

> **Modulo del corso:** Amministrazione Windows enterprise
> **Prerequisiti:** [12-endpoint-management.md](12-endpoint-management.md), [13-azure-ad-identita-ibrida.md](13-azure-ad-identita-ibrida.md), [05-sicurezza-windows.md](05-sicurezza-windows.md)
> **Obiettivi di apprendimento:**
> 1. Configurare l'enrollment dei dispositivi tramite Intune con metodi diversi (Autopilot, bulk, BYOD)
> 2. Progettare compliance policies con Conditional Access per accesso condizionale alle risorse
> 3. Distribuire applicazioni Win32 e LOB tramite il packaging .intunewin
> 4. Implementare App Protection Policies (MAM) per scenari BYOD
> 5. Integrare Intune con SCCM in scenari di co-management e tenant attach
> **Tempo stimato:** lettura 90 min · lab 180 min
> **Livello:** proficient
> **Ultimo aggiornamento:** 2026-05-23

## Idee guida
1. **Intune = MDM + MAM cloud.**
2. **Compliance Policy + Conditional Access combo.**
3. **Win32 app deploy via .intunewin packaging.**
4. **Configuration Profiles via OMA-URI per advanced.**


## Indice
- [Panoramica](#panoramica)
- [Architettura di Intune](#architettura-di-intune)
- [Enrollment dei Dispositivi](#enrollment-dei-dispositivi)
- [Compliance Policies](#compliance-policies)
- [Configuration Profiles](#configuration-profiles)
- [Distribuzione Applicazioni](#distribuzione-applicazioni)
- [Windows Autopilot](#windows-autopilot)
- [Conditional Access Integration](#conditional-access-integration)
- [Endpoint Analytics](#endpoint-analytics)
- [Windows Update for Business con Intune](#windows-update-for-business-con-intune)
- [App Protection Policies — MAM Deep Dive](#app-protection-policies--mam-deep-dive)
- [Intune vs SCCM/ConfigMgr — Confronto Dettagliato](#intune-vs-sccmconfigmgr--confronto-dettagliato)
- [Co-Management con SCCM/MECM](#co-management-con-sccmmecm)
- [Tenant Attach](#tenant-attach)
- [Reporting e Graph API](#reporting-e-graph-api)
- [Automazione Avanzata con Graph API](#automazione-avanzata-con-graph-api)
- [Script Proattivi e Remediation Avanzata](#script-proattivi-e-remediation-avanzata)
- [Gestione dei Dispositivi Multipiattaforma](#gestione-dei-dispositivi-multipiattaforma)
- [Intune Suite e Funzionalità Premium](#intune-suite-e-funzionalità-premium)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Domande e Risposte](#domande-e-risposte)
- [Esercizi Pratici](#esercizi-pratici)
- [Riferimenti](#riferimenti)

---

## Panoramica

La gestione moderna degli endpoint rappresenta un cambio di paradigma rispetto all'approccio tradizionale basato su Active Directory e Group Policy. Mentre il modello tradizionale assume che i dispositivi siano all'interno della rete aziendale e raggiungibili dai domain controller, la gestione moderna è progettata per un mondo cloud-first e mobile-first, dove i dispositivi possono essere ovunque e devono essere gestiti attraverso Internet senza la necessità di VPN o connettività diretta alla rete aziendale.

Microsoft Intune, parte della suite Microsoft Endpoint Manager (ora rinominata Microsoft Intune family), è la piattaforma di Mobile Device Management (MDM) e Mobile Application Management (MAM) di Microsoft. Intune permette di gestire dispositivi Windows, macOS, iOS, iPadOS e Android da un unico portale cloud, definendo policy di compliance, configurazioni, distribuzione di applicazioni e aggiornamenti.

L'integrazione nativa con Azure Active Directory (Entra ID), Microsoft Defender for Endpoint e Conditional Access crea un ecosistema di sicurezza Zero Trust in cui l'accesso alle risorse aziendali è condizionato alla conformità del dispositivo, all'identità dell'utente e al livello di rischio valutato in tempo reale.

### Il Modello Zero Trust con Intune

Il principio Zero Trust si basa su tre pilastri che Intune indirizza direttamente:

```
┌──────────────────────────────────────────────────────────────────┐
│                    ZERO TRUST con Intune                         │
│                                                                  │
│  1. VERIFICA ESPLICITA                                          │
│     - Identity: Azure AD / Entra ID (MFA, risk-based auth)     │
│     - Device: Intune Compliance (BitLocker, antivirus, patch)   │
│     - App: App Protection Policy (PIN, encryption, wipe)        │
│                                                                  │
│  2. ACCESSO CON MINIMO PRIVILEGIO                                │
│     - Conditional Access: Grant solo se tutti i criteri OK      │
│     - MAM: Separazione dati personali/aziendali                 │
│     - Scope tags: Segmentazione amministrativa                   │
│                                                                  │
│  3. ASSUME BREACH                                                │
│     - MDE integration: risk score per device                     │
│     - Endpoint Analytics: detection proattiva                    │
│     - Proactive Remediation: auto-fix issues                     │
└──────────────────────────────────────────────────────────────────┘
```

### Licenze e Prerequisiti

Intune è disponibile in diverse modalità di licenza:

| Licenza | Include Intune | Funzionalità |
|---------|----------------|-------------|
| Microsoft 365 E3 | Intune Plan 1 | MDM, MAM, compliance, config profiles |
| Microsoft 365 E5 | Intune Plan 1 | Come E3 + MDE P2 integration |
| EMS E3 | Intune Plan 1 | Senza Office, solo identity + device |
| EMS E5 | Intune Plan 1 | Come EMS E3 + Azure AD P2, MDE |
| Intune Plan 1 (standalone) | Sì | Funzionalità core MDM/MAM |
| Intune Plan 2 (add-on) | Add-on | Tunnel, specialty devices |
| Intune Suite (add-on) | Add-on | Remote Help, EPM, Advanced Analytics |

---

## Architettura di Intune

```
┌─────────────────────────────────────────────────────────┐
│                Microsoft Intune Cloud Service             │
│                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐│
│  │Compliance│  │Config    │  │App       │  │Update    ││
│  │Policies  │  │Profiles  │  │Deployment│  │Rings     ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘│
│                                                           │
│  ┌─────────────────────┐  ┌─────────────────────────┐   │
│  │ Azure AD / Entra ID │  │ Conditional Access      │   │
│  │ (Identity Provider) │  │ (Policy Engine)         │   │
│  └─────────────────────┘  └─────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│                     Internet (HTTPS)                      │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│ Windows  │ macOS    │ iOS      │ Android  │ Linux       │
│ MDM      │ MDM      │ MDM/MAM  │ MDM/MAM  │ (preview)   │
│ Client   │ Client   │ Client   │ Client   │             │
└──────────┴──────────┴──────────┴──────────┴─────────────┘
```

### Canali di Comunicazione

I dispositivi gestiti da Intune comunicano con il servizio cloud attraverso HTTPS (porta 443). Il canale di comunicazione è bidirezionale:

- **Device → Intune**: Il dispositivo fa check-in periodico (ogni 8 ore per Windows, con sync istantanea via push notification)
- **Intune → Device**: Per azioni immediate (wipe, lock, sync), Intune invia una push notification tramite WNS (Windows Notification Service) o APNs (Apple Push Notification Service)

Frequenze di check-in per piattaforma:

| Piattaforma | Check-in regolare | Check-in dopo enrollment | Push notification |
|-------------|-------------------|--------------------------|-------------------|
| Windows | Ogni 8 ore | Ogni 15 min per 6 ore | WNS |
| iOS/iPadOS | Ogni 8 ore | Ogni 15 min per 6 ore | APNs |
| Android | Ogni 8 ore | Ogni 15 min per 6 ore | FCM |
| macOS | Ogni 8 ore | Ogni 15 min per 6 ore | APNs |

```powershell
# Verificare lo stato di enrollment MDM su Windows
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Enrollments\*" |
    Where-Object { $_.ProviderId -eq "MS DM Server" } |
    Select-Object EnrollmentType, ProviderID, UPN

# Forzare un sync con Intune
Start-Process "ms-device-enrollment:?mode=mdm"

# Via script (trigger scheduled task)
Get-ScheduledTask -TaskPath "\Microsoft\Windows\EnterpriseMgmt\*" |
    Where-Object { $_.TaskName -like "*sync*" } | Start-ScheduledTask

# Verificare il canale di comunicazione MDM
$enrollmentPath = "HKLM:\SOFTWARE\Microsoft\Enrollments"
Get-ChildItem $enrollmentPath | ForEach-Object {
    $props = Get-ItemProperty $_.PSPath
    if ($props.ProviderID -eq "MS DM Server") {
        [PSCustomObject]@{
            EnrollmentID = Split-Path $_.PSPath -Leaf
            UPN          = $props.UPN
            AADTenantID  = $props.AADTenantID
            EnrollType   = $props.EnrollmentType
            DMPServer    = $props.DMPCertThumbPrint
        }
    }
}

# Verificare gli endpoint Intune raggiungibili
$intuneEndpoints = @(
    "https://manage.microsoft.com"
    "https://enrollment.manage.microsoft.com"
    "https://portal.manage.microsoft.com"
    "https://login.microsoftonline.com"
    "https://graph.microsoft.com"
    "https://config.office.com"
    "https://enterpriseregistration.windows.net"
)

foreach ($url in $intuneEndpoints) {
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10
        Write-Output "OK: $url ($($response.StatusCode))"
    } catch {
        Write-Warning "FAIL: $url - $($_.Exception.Message)"
    }
}
```

### Intune Management Extension (IME)

L'Intune Management Extension è un agente installato sui dispositivi Windows che estende le capacità MDM native. È necessario per:
- Distribuzione di app Win32 (.intunewin)
- Esecuzione di script PowerShell
- Proactive Remediations
- Win32 app detection scripts personalizzati

```powershell
# Verificare che l'IME sia installata e in esecuzione
Get-Service -Name "IntuneManagementExtension" | Select-Object Name, Status, StartType

# Percorso dei log dell'IME
$imeLogs = "C:\ProgramData\Microsoft\IntuneManagementExtension\Logs"
Get-ChildItem $imeLogs | Select-Object Name, Length, LastWriteTime | Sort-Object LastWriteTime -Descending

# Leggere gli ultimi eventi dal log principale
Get-Content "$imeLogs\IntuneManagementExtension.log" -Tail 100 |
    Select-String "error|warning|failed" -CaseSensitive:$false

# Verificare la versione dell'IME
$imeVersion = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\IntuneManagementExtension" -ErrorAction SilentlyContinue).Version
Write-Output "IME Version: $imeVersion"
```

---

## Enrollment dei Dispositivi

### Windows Enrollment

**Auto-enrollment via Azure AD Join:**

Quando un dispositivo viene unito ad Azure AD, può essere automaticamente registrato in Intune se l'auto-enrollment è configurato. Questo è il metodo più comune per i dispositivi aziendali.

```
Flusso Azure AD Join + Auto-enrollment:
1. Utente accede a Settings → Accounts → Access work or school → Connect
2. Inserisce le credenziali Azure AD
3. Il dispositivo viene registrato in Azure AD
4. Azure AD trigger l'auto-enrollment MDM in Intune
5. Intune invia le policy di compliance e configuration al dispositivo
6. Il dispositivo si conforma e diventa "Compliant"
```

Configurazione dell'auto-enrollment:
- Azure AD Portal → Mobility (MDM and MAM) → Microsoft Intune
- MDM User scope: All (o un gruppo specifico)
- MDM URLs: configurate automaticamente

**Bulk Enrollment con Provisioning Package:**

```powershell
# Creare un provisioning package con Windows Configuration Designer (WCD)
# WCD fa parte di Windows ADK
# File .ppkg risultante contiene:
# - Azure AD tenant info
# - MDM enrollment settings
# - WiFi profile (opzionale)
# - Certificati (opzionali)

# Applicare un provisioning package
Install-ProvisioningPackage -Path "C:\Packages\enrollment.ppkg" -QuietInstall

# Creare un provisioning package tramite riga di comando
# (dopo aver installato Windows Configuration Designer)
# ICD.exe /Build-ProvisioningPackage /CustomizationXML:"C:\Config\bulk-enrollment.xml" `
#     /PackagePath:"C:\Packages\enrollment.ppkg" /StoreFile:"C:\Config\store.icdprj"
```

**Enrollment tramite GPO (Hybrid Azure AD Join + Auto-Enrollment):**

Per dispositivi già joinati al dominio AD on-premises, è possibile configurare l'auto-enrollment MDM tramite GPO:

```
Computer Configuration → Administrative Templates → Windows Components
  → MDM → Enable automatic MDM enrollment using default Azure AD credentials

Prerequisiti:
  1. Azure AD Connect configurato con Hybrid Azure AD Join
  2. Auto-enrollment MDM configurato in Azure AD
  3. Dispositivo deve essere Windows 10 1709+ o Windows 11
  4. L'utente deve avere una licenza Intune assegnata
```

### BYOD Enrollment — Scenari Dettagliati

Il BYOD (Bring Your Own Device) richiede un equilibrio tra sicurezza aziendale e privacy dell'utente. Intune offre diversi livelli di gestione per i dispositivi personali:

```
┌─────────────────────────────────────────────────────────────┐
│           BYOD ENROLLMENT MATRIX                             │
│                                                              │
│  Livello 1: MAM-Only (Nessun enrollment)                    │
│  ├── L'utente installa le app aziendali (Outlook, Teams)    │
│  ├── App Protection Policy protegge i dati dentro le app     │
│  ├── Zero visibilità sul dispositivo                         │
│  ├── Zero controllo sul dispositivo                          │
│  └── Ideale per: contractor, utenti esterni, privacy max     │
│                                                              │
│  Livello 2: Azure AD Registration + MAM                     │
│  ├── L'utente registra il dispositivo (non join)             │
│  ├── Conditional Access può verificare la registrazione      │
│  ├── MAM protegge le app                                     │
│  ├── Nessuna gestione del dispositivo                        │
│  └── Ideale per: BYOD con accesso a risorse base             │
│                                                              │
│  Livello 3: MDM Enrollment (User Enrollment per iOS)        │
│  ├── Enrollment completo MDM                                 │
│  ├── Compliance Policies applicate                           │
│  ├── Wi-Fi/VPN profiles distribuiti                          │
│  ├── Il reparto IT può fare wipe selettivo                  │
│  ├── L'utente vede cosa l'IT può/non può vedere              │
│  └── Ideale per: BYOD con accesso a dati sensibili          │
└─────────────────────────────────────────────────────────────┘
```

```powershell
# Verificare il tipo di enrollment di un dispositivo via Graph API
$deviceId = "device-id-here"
$headers = @{ Authorization = "Bearer $accessToken" }
$device = Invoke-RestMethod -Uri "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices/$deviceId" `
    -Headers $headers

[PSCustomObject]@{
    DeviceName     = $device.deviceName
    OS             = $device.operatingSystem
    Ownership      = $device.managedDeviceOwnerType  # "company" o "personal"
    EnrollmentType = $device.deviceEnrollmentType
    JoinType       = $device.joinType
    Compliance     = $device.complianceState
    LastSync       = $device.lastSyncDateTime
}

# Configurare le Device Enrollment Restrictions
# Limitare le piattaforme ammesse per BYOD
$restrictionBody = @{
    displayName = "BYOD - Solo iOS e Android"
    platformRestrictions = @{
        androidRestriction = @{
            platformBlocked = $false
            personalDeviceEnrollmentBlocked = $false
            osMinimumVersion = "13.0"
        }
        iosRestriction = @{
            platformBlocked = $false
            personalDeviceEnrollmentBlocked = $false
            osMinimumVersion = "16.0"
        }
        windowsRestriction = @{
            platformBlocked = $false
            personalDeviceEnrollmentBlocked = $true  # Bloccare BYOD Windows
        }
    }
} | ConvertTo-Json -Depth 5
```

### iOS/iPadOS Enrollment

Per i dispositivi Apple, Intune supporta:
- **Automated Device Enrollment (ADE)** via Apple Business Manager — Zero-touch, il dispositivo si registra automaticamente all'accensione
- **User Enrollment** — L'utente scarica Company Portal e registra volontariamente il dispositivo. Privacy-focused per BYOD
- **Device Enrollment (con o senza user affinity)** — Per dispositivi condivisi

```
Configurazione ADE (Automated Device Enrollment):
1. In Apple Business Manager: assegnare i dispositivi al server MDM Intune
2. In Intune: Devices → Enroll devices → Apple enrollment → Enrollment program tokens
3. Caricare il token Apple MDM Push Certificate
4. Creare un Enrollment Profile:
   - User Affinity: Yes (per dispositivi personali di un singolo utente)
   - Supervised Mode: Yes (per dispositivi aziendali, massimo controllo)
   - Setup Assistant customization:
     Skip: Diagnostics, Location Services, Apple Pay, Terms
     Show: Passcode, Display Zoom

5. Assegnare il profilo ai dispositivi importati da ABM
```

### Android Enrollment

- **Android Enterprise (Work Profile)** — Profilo di lavoro separato sul dispositivo personale (BYOD)
- **Android Enterprise (Fully Managed)** — Gestione completa del dispositivo aziendale
- **Android Enterprise (Dedicated)** — Per kiosk e dispositivi condivisi
- **Android Enterprise (Corporate-Owned Work Profile)** — Dispositivo aziendale con profilo personale separato

```
Matrice di scelta Android Enterprise:

Proprietà dispositivo:  PERSONALE          AZIENDALE
                        ─────────          ─────────
Solo lavoro:            N/A                Fully Managed
Lavoro + Personale:     Work Profile       COPE (Corporate-Owned
                                           Work Profile)
Kiosk/Condiviso:        N/A                Dedicated Device

Enrollment methods:
  - Work Profile: Company Portal → enroll
  - Fully Managed: QR code / NFC / Zero-touch (Google)
  - Dedicated: QR code / NFC / Token
  - COPE: QR code / NFC / Zero-touch
```

---

## Compliance Policies

Le compliance policies definiscono i requisiti minimi che un dispositivo deve soddisfare per essere considerato "compliant". Lo stato di compliance è il fondamento per il Conditional Access: un dispositivo non compliant può essere bloccato dall'accesso alle risorse aziendali.

### Esempio di Compliance Policy per Windows

```json
{
    "displayName": "Windows 11 - Compliance Baseline",
    "platform": "windows10",
    "settings": {
        "deviceHealthSettings": {
            "bitLockerEnabled": true,
            "secureBootEnabled": true,
            "codeIntegrityEnabled": true
        },
        "devicePropertySettings": {
            "osMinimumVersion": "10.0.22631",
            "osMaximumVersion": null,
            "storageRequireEncryption": true
        },
        "systemSecuritySettings": {
            "passwordRequired": true,
            "passwordMinimumLength": 8,
            "passwordRequiredType": "alphanumeric",
            "passwordMinutesOfInactivityBeforeLock": 15,
            "firewallEnabled": true,
            "antivirusRequired": true,
            "antiSpywareRequired": true,
            "defenderEnabled": true,
            "defenderVersion": "current",
            "signatureOutOfDate": 3,
            "rtpEnabled": true
        },
        "defenderForEndpointSettings": {
            "requireMachineRiskScore": "medium"
        }
    },
    "scheduledActionsForRule": [
        {
            "ruleName": "PasswordRequired",
            "scheduledActionConfigurations": [
                {
                    "actionType": "block",
                    "gracePeriodHours": 72,
                    "notificationTemplateId": "default"
                },
                {
                    "actionType": "retire",
                    "gracePeriodHours": 720
                }
            ]
        }
    ]
}
```

### Compliance Policy per iOS

```json
{
    "displayName": "iOS - Compliance Baseline",
    "platform": "iOS",
    "settings": {
        "deviceHealthSettings": {
            "jailBroken": "blocked",
            "managedEmailProfileRequired": true
        },
        "devicePropertySettings": {
            "osMinimumVersion": "16.0",
            "osMaximumVersion": null
        },
        "systemSecuritySettings": {
            "passcodeRequired": true,
            "passcodeMinimumLength": 6,
            "passcodeBlockSimple": true,
            "passcodeMinutesOfInactivityBeforeLock": 5,
            "passcodeExpirationDays": null,
            "passcodeMinimumCharacterSetCount": 2,
            "securityBlockJailbrokenDevices": true
        }
    }
}
```

### Compliance Policy per Android Enterprise

```json
{
    "displayName": "Android Enterprise - Compliance Baseline",
    "platform": "androidForWork",
    "settings": {
        "deviceHealthSettings": {
            "rootedDevicesBlocked": true,
            "googlePlayServicesEnabled": true,
            "upToDateSecurityProviders": true,
            "safetyNetAttestationBasicIntegrity": true,
            "safetyNetAttestationCertifiedDevice": true
        },
        "systemSecuritySettings": {
            "passwordRequired": true,
            "passwordMinimumLength": 6,
            "passwordRequiredType": "numericComplex",
            "storageRequireEncryption": true
        }
    }
}
```

### Azioni per Non-Compliance

Intune permette di configurare azioni progressive quando un dispositivo non è compliant:

1. **Mark device non-compliant** — Immediato o con grace period
2. **Send email notification** — Avvisare l'utente
3. **Send push notification** — Notifica via Company Portal
4. **Remote lock** — Bloccare il dispositivo
5. **Retire** — Rimuovere i dati aziendali (wipe selettivo)

```
Timeline tipica di azioni per non-compliance:

Giorno 0:  Dispositivo diventa non-compliant
           → Notifica email all'utente
           → Grace period inizia

Giorno 3:  Se ancora non-compliant (grace period scaduta)
           → Dispositivo marcato ufficialmente "Non-Compliant"
           → Conditional Access blocca accesso a risorse

Giorno 7:  Se ancora non-compliant
           → Push notification reminder
           → Email al manager dell'utente (custom workflow)

Giorno 14: Se ancora non-compliant
           → Remote lock del dispositivo

Giorno 30: Se ancora non-compliant
           → Retire (rimozione dati aziendali)
           → Notifica al team IT per follow-up
```

```powershell
# Verificare lo stato di compliance via Graph API
$uri = "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices?`$filter=complianceState eq 'noncompliant'"
$headers = @{ Authorization = "Bearer $accessToken" }
$response = Invoke-RestMethod -Uri $uri -Headers $headers -Method GET
$response.value | Select-Object deviceName, complianceState, lastSyncDateTime,
    operatingSystem, userPrincipalName

# Report dettagliato di compliance per policy
$uri = "https://graph.microsoft.com/v1.0/deviceManagement/deviceCompliancePolicyDeviceStateSummary"
$summary = Invoke-RestMethod -Uri $uri -Headers $headers
[PSCustomObject]@{
    Compliant    = $summary.compliantDeviceCount
    NonCompliant = $summary.nonCompliantDeviceCount
    InGrace      = $summary.inGracePeriodCount
    Error        = $summary.errorCount
    Unknown      = $summary.unknownDeviceCount
    NotApplicable = $summary.notApplicableDeviceCount
}
```

### Custom Compliance Scripts

Intune supporta script PowerShell personalizzati per verificare condizioni di compliance non coperte dai settings built-in:

```powershell
# Script di discovery per custom compliance (eseguito sul dispositivo)
# Deve restituire JSON con le proprietà da verificare

$result = @{}

# Verificare che un agente di sicurezza sia installato
$secAgent = Get-Service -Name "CrowdStrike Falcon Sensor" -ErrorAction SilentlyContinue
$result.SecurityAgentRunning = if ($secAgent -and $secAgent.Status -eq 'Running') { $true } else { $false }

# Verificare la versione del BIOS
$bios = Get-CimInstance Win32_BIOS
$result.BIOSVersion = $bios.SMBIOSBIOSVersion

# Verificare lo spazio disco libero
$disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
$result.FreeSpaceGB = [math]::Round($disk.FreeSpace / 1GB, 2)

# Verificare che la cifratura sia attiva
$bitlocker = Get-BitLockerVolume -MountPoint "C:" -ErrorAction SilentlyContinue
$result.BitLockerEnabled = if ($bitlocker -and $bitlocker.ProtectionStatus -eq 'On') { $true } else { $false }

# Output JSON
$result | ConvertTo-Json -Compress

# Il JSON di compliance rules corrispondente (da caricare su Intune):
# {
#   "Rules": [
#     {
#       "SettingName": "SecurityAgentRunning",
#       "Operator": "IsEquals",
#       "DataType": "Boolean",
#       "Operand": true,
#       "MoreInfoUrl": "https://wiki.contoso.com/security-agent",
#       "RemediationStrings": [
#         {
#           "Language": "it_IT",
#           "Title": "Agente di sicurezza non in esecuzione",
#           "Description": "Avviare CrowdStrike Falcon o contattare l'IT"
#         }
#       ]
#     },
#     {
#       "SettingName": "FreeSpaceGB",
#       "Operator": "GreaterEquals",
#       "DataType": "Double",
#       "Operand": 10.0,
#       "RemediationStrings": [
#         {
#           "Language": "it_IT",
#           "Title": "Spazio disco insufficiente",
#           "Description": "Liberare almeno 10 GB sul disco C:"
#         }
#       ]
#     }
#   ]
# }
```

---

## Configuration Profiles

I configuration profiles sono l'equivalente cloud delle Group Policy. Permettono di configurare centinaia di impostazioni sui dispositivi gestiti. Intune supporta diversi tipi di profilo:

### Settings Catalog (Raccomandato)

Il Settings Catalog è il metodo più moderno e flessibile per configurare i dispositivi. Espone migliaia di impostazioni MDM searchable e categorizzate.

```
Esempio: Configurare Windows Firewall
Devices → Configuration profiles → Create profile
  Platform: Windows 10 and later
  Profile type: Settings catalog

  Impostazioni selezionate:
  - Firewall > EnableFirewall (Domain/Private/Public): True
  - Firewall > DisableInboundNotifications: True
  - Firewall > DefaultInboundAction: Block
  - Firewall > DefaultOutboundAction: Allow
  - Firewall > LogFilePath: %SystemRoot%\System32\LogFiles\Firewall\pfirewall.log
  - Firewall > LogMaxFileSize: 16384
```

### Administrative Templates (ADMX-backed)

Intune può applicare le stesse impostazioni dei template ADMX disponibili in GPO:

```
Devices → Configuration profiles → Create profile
  Platform: Windows 10 and later
  Profile type: Templates → Administrative Templates

  Configurare le stesse impostazioni disponibili in GPMC:
  - Computer Configuration → Windows Components → BitLocker Drive Encryption
  - User Configuration → Start Menu and Taskbar
  - Computer Configuration → Windows Components → Windows Update
```

### Custom ADMX Ingestion

Per applicazioni di terze parti con template ADMX custom (es. Google Chrome, Mozilla Firefox, Adobe Acrobat):

```
1. Importare il file ADMX nel portale Intune:
   Devices → Configuration profiles → Import ADMX
   Caricare: chrome.admx + chrome.adml (lingua)

2. Dopo l'importazione, le impostazioni appaiono nel Settings Catalog
   sotto la categoria corrispondente (es. "Google Chrome")

3. Creare un profilo Settings Catalog con le impostazioni desiderate

Esempio Google Chrome via Settings Catalog (dopo ADMX import):
  - DefaultBrowserSettingEnabled: Disabled
  - PasswordManagerEnabled: Disabled
  - AutofillAddressEnabled: Disabled
  - HomepageLocation: https://intranet.contoso.com
  - BlockExternalExtensions: Enabled
```

### Device Restrictions

```
Esempio: Restrizioni per dispositivi aziendali
Devices → Configuration profiles → Create profile
  Profile type: Templates → Device restrictions

  General:
  - Block screen capture: Yes
  - Block manual unenrollment: Yes

  Password:
  - Password type: Alphanumeric
  - Minimum password length: 8
  - Minutes of inactivity before lock screen: 5

  App Store:
  - Block installing apps from unknown sources: Yes

  Cloud and Storage:
  - Block Microsoft Account: Yes

  Reporting and Telemetry:
  - Share usage data: Diagnostic data off
```

### Endpoint Protection Profile

```
Configurare Defender via Intune:
Devices → Configuration profiles → Create profile
  Profile type: Templates → Endpoint protection

  Microsoft Defender Firewall:
  - Enable for all network types

  Microsoft Defender Exploit Guard:
  - Attack Surface Reduction rules: Configure each rule
  - Controlled Folder Access: Enable
  - Network Protection: Enable

  Microsoft Defender SmartScreen:
  - SmartScreen for Microsoft Edge: Require
  - Block malicious site access: Yes
  - Block unverified file download: Yes
```

### OMA-URI per Configurazioni Avanzate

Per impostazioni non disponibili nei template standard, è possibile utilizzare profili Custom con OMA-URI:

```
Devices → Configuration profiles → Create profile
  Profile type: Templates → Custom

Esempio: Configurare il timeout di blocco schermo preciso
  Name: Screen Lock Timeout
  OMA-URI: ./Device/Vendor/MSFT/Policy/Config/DeviceLock/MaxInactivityTimeDeviceLock
  Data type: Integer
  Value: 5  (minuti)

Esempio: Configurare le impostazioni di Windows Hello for Business
  Name: WHfB - PIN complexity
  OMA-URI: ./Device/Vendor/MSFT/PassportForWork/{TenantID}/Policies/PINComplexity/MinimumPINLength
  Data type: Integer
  Value: 6

Esempio: Disabilitare USB storage
  Name: Block USB Storage
  OMA-URI: ./Device/Vendor/MSFT/Policy/Config/Storage/RemovableDiskDenyWriteAccess
  Data type: Integer
  Value: 1
```

### Gestione dei Conflitti tra Profili

Quando un dispositivo riceve impostazioni in conflitto da profili diversi, Intune segue queste regole:

```
Priorità di risoluzione conflitti:
1. Security baselines (priorità più alta)
2. Configuration profiles (Settings Catalog / Templates)
3. Compliance policies
4. GPO locale (se co-managed, dipende dal workload owner)

Se due profili dello stesso tipo configurano la stessa impostazione
con valori diversi:
  → L'impostazione va in stato "Conflict"
  → Nessuno dei due valori viene applicato
  → Il dispositivo mantiene il valore precedente o il default

Per risolvere:
  Devices → [dispositivo] → Device configuration → Per-setting status
  Filtrare per stato "Conflict"
  Consolidare le impostazioni in un unico profilo o usare filtri di assegnazione
```

---

## Distribuzione Applicazioni

### Win32 App (IntuneWin)

Le applicazioni Win32 sono il metodo più flessibile per distribuire software desktop tramite Intune. Richiedono il packaging dell'installer in formato `.intunewin` usando il Microsoft Win32 Content Prep Tool.

```powershell
# 1. Scaricare il Win32 Content Prep Tool
# https://github.com/microsoft/Microsoft-Win32-Content-Prep-Tool

# 2. Creare il package .intunewin
.\IntuneWinAppUtil.exe `
    -c "C:\SourceApps\7zip"        `  # Cartella sorgente
    -s "7z2301-x64.msi"            `  # File installer
    -o "C:\IntunePackages"          `  # Output
    -q                                 # Quiet mode
```

Configurazione nel portale Intune:

```
Apps → Windows → Add → App type: Windows app (Win32)

App information:
  Name: 7-Zip 23.01
  Description: File archiver
  Publisher: Igor Pavlov

Program:
  Install command: msiexec /i "7z2301-x64.msi" /qn
  Uninstall command: msiexec /x "{23170F69-40C1-2702-2301-000001000000}" /qn
  Install behavior: System
  Device restart behavior: App install may force a device restart

Requirements:
  OS architecture: 64-bit
  Minimum OS version: Windows 10 21H2
  Disk space required: 50 MB
  Physical memory required: 512 MB

Detection rules:
  Rule type: MSI (auto-detect from package)
  -- oppure --
  Rule type: File
    Path: C:\Program Files\7-Zip
    File: 7z.exe
    Detection method: File or folder exists

  -- oppure --
  Rule type: Registry
    Key path: HKLM\SOFTWARE\7-Zip
    Value name: Path
    Detection method: Key exists

  -- oppure --
  Rule type: Custom detection script (PowerShell)

Dependencies: (nessuna per 7-Zip)
Supersedence: (configurare se sostituisce una versione precedente)
```

### Detection Script Personalizzato

```powershell
# Script di detection per applicazioni complesse
# Deve restituire exit code 0 e scrivere su STDOUT per "detected"
# Deve restituire exit code 1 (o nessun output) per "not detected"

# Esempio: verificare versione specifica di un'applicazione
$appPath = "C:\Program Files\CustomApp\app.exe"
$requiredVersion = [version]"3.5.0"

if (Test-Path $appPath) {
    $installedVersion = [version](Get-Item $appPath).VersionInfo.FileVersion
    if ($installedVersion -ge $requiredVersion) {
        Write-Output "CustomApp $installedVersion detected"
        exit 0  # Installata, versione OK
    }
}
exit 1  # Non installata o versione troppo vecchia
```

### Requirement Script Personalizzato

```powershell
# Script per verificare requisiti aggiuntivi prima dell'installazione
# Deve restituire output che corrisponde al tipo configurato in Intune

# Esempio: verificare se è disponibile abbastanza spazio disco
$disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:'"
$freeGB = [math]::Round($disk.FreeSpace / 1GB, 2)

# Il tipo configurato in Intune è "Integer", il valore atteso è >= 5
Write-Output $freeGB
```

### MSI App

Per installer MSI semplici, Intune può gestirli direttamente senza il passaggio di packaging Win32:

```
Apps → Windows → Add → App type: Line-of-business app
Upload: applicazione.msi

L'MSI viene analizzato automaticamente per:
- Product code
- Version
- Command line parameters
```

### Microsoft Store Apps (Nuovo)

```
Apps → Windows → Add → App type: Microsoft Store app (new)
Cercare l'app nel catalogo Microsoft Store for Business
Assegnare ai gruppi di utenti o dispositivi

Il nuovo Microsoft Store app type:
  - Non richiede Microsoft Store for Business (deprecato)
  - Si integra direttamente con il Windows Package Manager (winget)
  - Supporta aggiornamenti automatici dal Microsoft Store
  - Disponibile per utenti e dispositivi
```

### App Assignments — Logica di Assegnazione

```
Tipi di assegnazione per le app:
  - Required: L'app viene installata automaticamente senza intervento utente
  - Available: L'app appare nel Company Portal per installazione opzionale
  - Uninstall: L'app viene disinstallata se presente

Filtri di assegnazione:
  - Per gruppo di utenti o dispositivi
  - Con filtri (es. solo Windows 11, solo dispositivi aziendali)
  - Con eccezioni (escludi un gruppo specifico)

Priorità se un dispositivo riceve sia Required che Uninstall:
  → Required vince
  → (un gruppo "Required" esclude automaticamente il gruppo "Uninstall")
```

---

## Windows Autopilot

Windows Autopilot è il servizio di provisioning zero-touch di Microsoft che permette di configurare nuovi dispositivi Windows direttamente dalla fabbrica o dal primo avvio, senza la necessità di creare e mantenere immagini personalizzate.

### Flusso di Deployment

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│ OEM registra   │     │ Dispositivo    │     │ Utente fa      │
│ hardware hash  │ ──> │ acceso per la  │ ──> │ logon con      │
│ in Autopilot   │     │ prima volta    │     │ Azure AD cred  │
└────────────────┘     └────────────────┘     └────────────────┘
                              │                       │
                              v                       v
                    ┌────────────────┐     ┌────────────────┐
                    │ Si connette a  │     │ Intune invia   │
                    │ Autopilot      │     │ policies, apps,│
                    │ service        │     │ configuration  │
                    └────────────────┘     └────────────────┘
                              │
                              v
                    ┌────────────────┐
                    │ OOBE           │
                    │ personalizzato │
                    │ (branding,     │
                    │ skip steps)    │
                    └────────────────┘
```

### Profili Autopilot

**User-Driven Mode:** L'utente accende il dispositivo, si connette a Internet, inserisce le proprie credenziali Azure AD e il dispositivo si configura automaticamente.

**Self-Deploying Mode:** Il dispositivo si configura senza alcun intervento utente. Richiede TPM 2.0. Ideale per kiosk e dispositivi condivisi.

**Pre-Provisioned (White Glove):** Il reparto IT (o il partner) completa la configurazione tecnica prima di consegnare il dispositivo all'utente. L'utente finale deve solo fare logon.

```powershell
# Registrare un dispositivo in Autopilot (raccogliere l'hardware hash)
Install-Module WindowsAutopilotIntuneCommunity -Force
Install-Script Get-WindowsAutopilotInfo -Force

# Raccogliere l'hash e caricarlo direttamente in Intune
Get-WindowsAutopilotInfo -Online

# Raccogliere l'hash in un file CSV
Get-WindowsAutopilotInfo -OutputFile "C:\Temp\autopilot.csv"

# Importare il CSV nel portale Intune:
# Devices → Enroll devices → Windows enrollment → Devices
# Import → Upload CSV

# Creare un Autopilot Deployment Profile via Graph API
$body = @{
    displayName = "Autopilot - User Driven Standard"
    description = "Profilo standard per utenti aziendali"
    extractHardwareHash = $true
    outOfBoxExperienceSettings = @{
        hidePrivacySettings = $true
        hideEULA = $true
        userType = "standard"  # L'utente sarà Standard, non Admin
        skipKeyboardSelectionPage = $true
        hideEscapeLink = $true
    }
    enrollmentStatusScreenSettings = @{
        hideInstallationProgress = $false
        allowDeviceUseBeforeProfileAndAppInstallComplete = $false
        blockDeviceSetupRetryByUser = $false
        allowLogCollectionOnInstallFailure = $true
        installProgressTimeoutInMinutes = 60
    }
} | ConvertTo-Json -Depth 5
```

### Autopilot Reset

Autopilot Reset permette di "ripristinare" un dispositivo senza reinstallare Windows. Utile quando un utente lascia l'azienda e il dispositivo deve essere riassegnato:

```
Due modalità:
1. Remote Reset (dal portale Intune):
   Devices → [dispositivo] → Autopilot Reset
   - Rimuove tutti gli utenti e le app
   - Mantiene Azure AD join e Intune enrollment
   - Mantiene Wi-Fi e region settings
   - Il prossimo utente fa logon e riceve le sue policy/app

2. Local Reset (dal dispositivo):
   Durante il logon: Ctrl+Win+R (se configurato)
   - Stesso comportamento del remote reset
   - Utile quando il dispositivo non è raggiungibile dal cloud
```

### Enrollment Status Page (ESP)

L'ESP mostra il progresso dell'installazione durante il provisioning Autopilot, impedendo all'utente di accedere al desktop prima che tutte le policy e le applicazioni critiche siano installate.

```
Devices → Enroll devices → Enrollment Status Page → Create

Settings:
  - Show app and profile configuration progress: Yes
  - Show an error when installation takes longer than (minutes): 60
  - Show custom message when time limit error occurs: Yes
    Message: "Contattare l'helpdesk IT al 800-123-456"
  - Allow users to collect logs about installation errors: Yes
  - Only show page to devices provisioned by OOBE: Yes
  - Block device use until all apps and profiles are installed: Yes
  - Allow users to reset device if installation error occurs: Yes
  - Allow users to use device if installation error occurs: No

Blocking apps (app che devono essere installate prima che l'utente acceda):
  - Microsoft 365 Apps
  - Company VPN Client
  - Security Agent (CrowdStrike / MDE)
  - Certificati radice aziendali
```

---

## Conditional Access Integration

Conditional Access è il motore decisionale Zero Trust che valuta ogni richiesta di accesso e determina se consentirla, bloccarla o richiedere controlli aggiuntivi (MFA, device compliance, ecc.).

```
┌─────────────────────────────────────────────────────┐
│              Conditional Access Policy                │
│                                                       │
│  IF:                                                  │
│    User: All users (exclude Break Glass accounts)     │
│    Cloud app: All cloud apps                          │
│    Conditions:                                        │
│      - Device platforms: Windows                      │
│      - Locations: Any location                        │
│      - Client apps: Browser, Mobile apps              │
│      - Sign-in risk: Medium, High                     │
│                                                       │
│  THEN:                                                │
│    Grant:                                             │
│      - Require multi-factor authentication            │
│      - Require device to be marked as compliant       │
│      - Require approved client app                    │
│      (All of the above)                               │
│                                                       │
│    Session:                                           │
│      - Sign-in frequency: 8 hours                     │
│      - Persistent browser session: Never persistent   │
│                                                       │
│  Enable policy: Report-only → On                      │
└─────────────────────────────────────────────────────┘
```

### Policy Tipiche

**Policy 1: Richiedere MFA per tutti gli utenti:**
- Assignments: All users (escludere break glass)
- Cloud apps: All cloud apps
- Grant: Require MFA

**Policy 2: Richiedere device compliant per l'accesso a dati sensibili:**
- Assignments: All users
- Cloud apps: SharePoint Online, Exchange Online
- Grant: Require compliant device AND Require MFA

**Policy 3: Bloccare l'accesso da paesi non autorizzati:**
- Assignments: All users
- Cloud apps: All cloud apps
- Conditions: Locations → Include: Any location, Exclude: Named locations (Italia, EU)
- Grant: Block access

**Policy 4: Richiedere app protection policy su dispositivi mobili:**
- Assignments: All users
- Cloud apps: Office 365
- Conditions: Device platforms → iOS, Android
- Grant: Require app protection policy

**Policy 5: Bloccare legacy authentication:**
- Assignments: All users
- Cloud apps: All cloud apps
- Conditions: Client apps → Exchange ActiveSync clients, Other clients
- Grant: Block access

---

## Endpoint Analytics

Endpoint Analytics fornisce visibilità sulle prestazioni e sull'esperienza utente dei dispositivi gestiti, identificando problemi proattivamente.

### Metriche Principali

**Startup Performance:**
- Boot time (tempo dall'accensione al desktop utilizzabile)
- Core boot time, Group Policy processing time, Sign-in time
- Dispositivi con startup lento vengono identificati con raccomandazioni

**Application Reliability:**
- App crash frequency per applicazione
- App hang events
- App not responding count
- Trend temporali di stabilità

**User Experience Score:**
- Endpoint Analytics Score (0-100)
- Composito di: Startup Performance + App Reliability + Work From Anywhere
- Confronto con il baseline dell'organizzazione e con la media del settore

**Work From Anywhere Score:**
- Windows version currency (quanto è aggiornato l'OS)
- Cloud management capability
- Cloud identity capability

### Proactive Remediations

Script che vengono eseguiti periodicamente sui dispositivi per rilevare e correggere problemi automaticamente.

```powershell
# Esempio: Remediation script per svuotare la cache del browser
# Detection Script (deve restituire exit code 1 se il problema esiste)
$chromeCache = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache"
$cacheSize = (Get-ChildItem $chromeCache -Recurse -ErrorAction SilentlyContinue |
    Measure-Object Length -Sum).Sum / 1MB

if ($cacheSize -gt 500) {
    Write-Output "Chrome cache is $([math]::Round($cacheSize))MB - needs cleanup"
    exit 1  # Problema rilevato
} else {
    Write-Output "Chrome cache is $([math]::Round($cacheSize))MB - OK"
    exit 0  # Nessun problema
}

# Remediation Script (eseguito solo se detection rileva il problema)
$chromeCache = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache"
$chromeCacheCode = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Code Cache"

try {
    # Terminare Chrome se in esecuzione
    Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 2

    Remove-Item "$chromeCache\*" -Force -Recurse -ErrorAction SilentlyContinue
    Remove-Item "$chromeCacheCode\*" -Force -Recurse -ErrorAction SilentlyContinue

    Write-Output "Chrome cache cleaned successfully"
    exit 0
} catch {
    Write-Error "Failed to clean cache: $_"
    exit 1
}
```

---

## Windows Update for Business con Intune

Windows Update for Business (WUfB) gestito tramite Intune permette di controllare il deployment degli aggiornamenti Windows senza la necessità di un server WSUS on-premises.

### Update Rings

```
Devices → Windows 10 and later updates → Update rings

Ring 1: "Pilot - IT Team" (10% dei dispositivi)
  Quality updates deferral: 0 days
  Feature updates deferral: 0 days
  Assigned to: GRP-IT-Pilot

Ring 2: "Early Adopters" (20% dei dispositivi)
  Quality updates deferral: 7 days
  Feature updates deferral: 14 days
  Assigned to: GRP-Early-Adopters

Ring 3: "Broad Deployment" (70% dei dispositivi)
  Quality updates deferral: 14 days
  Feature updates deferral: 30 days
  Assigned to: GRP-All-Users (exclude Pilot e Early Adopters)

Impostazioni comuni per tutti i ring:
  - Automatic update behavior: Auto install at maintenance time
  - Active hours start/end: 8:00 - 18:00
  - Restart checks: Yes (check for pending restarts)
  - Option to pause updates: Yes (for 35 days max)
  - Uninstall period: 10 days (for quality), 30 days (for feature)
  - Delivery optimization: HTTP blended with peering behind NAT
```

### Feature Update Policies

```
Devices → Windows 10 and later updates → Feature updates

Policy: "Upgrade to Windows 11 24H2"
  Feature update to deploy: Windows 11, version 24H2
  Rollout options:
    - Make available as soon as possible: Yes
    - Gradual rollout:
      First group: 2026-05-01
      Final group: 2026-06-30
      Days between groups: 7
  Assigned to: GRP-Win11-Eligible
```

### Driver Updates

```
Devices → Windows 10 and later updates → Driver updates

Policy: "Automatic Driver Updates"
  Automatic driver approval: Yes (recommended drivers only)
  -- oppure --
  Manual approval: Review and approve each driver update

  Assigned to: GRP-All-Managed-Devices
```

### Windows Autopatch

Windows Autopatch è il servizio gestito da Microsoft che automatizza completamente la gestione degli aggiornamenti:

```
Windows Autopatch automatizza:
  - Creazione e gestione degli update rings
  - Monitoraggio dell'avanzamento del deployment
  - Rollback automatico se un aggiornamento causa problemi
  - Reporting sulla compliance degli aggiornamenti

Requisiti:
  - Microsoft 365 E3 o superiore
  - Intune enrollment dei dispositivi
  - Windows 10/11 Enterprise o Education
  - Azure AD Premium P1

Rings automatici:
  Test ring:    1% dei dispositivi, 0 days deferral
  First ring:   9% dei dispositivi, 1 day deferral
  Fast ring:   21% dei dispositivi, 6 days deferral
  Broad ring:  69% dei dispositivi, 9 days deferral
```

### Windows Autopatch — Evoluzione 2025

Nel 2025, Windows Autopatch ha subito cambiamenti significativi che ne semplificano l'adozione e ne espandono la portata:

**Hotpatch (aggiornamenti senza riavvio)**: la funzionalità più attesa. Gli hotpatch applicano correzioni di sicurezza critiche senza richiedere il riavvio del sistema operativo. Questo è possibile perché le patch vengono iniettate direttamente nella memoria del kernel e dei componenti interessati durante l'esecuzione. Su base trimestrale, un aggiornamento "baseline" completo richiede comunque il riavvio, ma nei mesi intermedi gli hotpatch eliminano il downtime. La funzionalità richiede Windows 11 24H2+ Enterprise/Education e processore supportato (AMD64/ARM64 con VBS abilitato).

```
Ciclo Hotpatch trimestrale:

Mese 1 (Gennaio, Aprile, Luglio, Ottobre):
  → Baseline update (Patch Tuesday classico)
  → RICHIEDE riavvio
  → Include aggiornamenti cumulativi completi + nuove baseline di sicurezza

Mese 2 (Febbraio, Maggio, Agosto, Novembre):
  → Hotpatch
  → NESSUN riavvio
  → Patch di sicurezza iniettate in memoria

Mese 3 (Marzo, Giugno, Settembre, Dicembre):
  → Hotpatch
  → NESSUN riavvio
  → Patch di sicurezza iniettate in memoria

Risultato: da 12 riavvii/anno → 4 riavvii/anno per aggiornamenti di sicurezza

Configurazione in Intune:
  Devices → Windows updates → Quality updates → Create policy
  → Hotpatch enabled: Yes
  → Assigned to: GRP-Hotpatch-Eligible
```

**Licensing espanso**: Autopatch non è più limitato a Microsoft 365 E3/E5. Dal 2025, è disponibile anche con Microsoft 365 Business Premium, Microsoft 365 A3+ (Education) e Windows 365 Enterprise. Questo amplia significativamente la base di organizzazioni che possono adottarlo.

**Processo di attivazione ritirato**: Microsoft ha eliminato il processo manuale di attivazione (activation wizard) per Autopatch. Le organizzazioni con licenze idonee hanno Autopatch automaticamente disponibile nel portale Intune, senza dover completare prerequisiti o wizard di configurazione. Le funzionalità Autopatch sono integrate direttamente nella gestione degli aggiornamenti di Intune.

```
Modello di sicurezza migliorato (2025):

Autopatch Group-Based Management:
  ┌────────────────────────────────────────────────────┐
  │ Autopatch Groups                                    │
  │                                                     │
  │  Ogni "Autopatch group" definisce:                  │
  │  ├── Device set (gruppi Azure AD)                   │
  │  ├── Deployment cadence (ring velocità)              │
  │  ├── Update content (quality, feature, drivers)     │
  │  └── Monitoring & rollback rules                    │
  │                                                     │
  │  Esempio configurazione:                            │
  │  Group: "Sviluppatori"                              │
  │    Ring 1 (Test):     5% - 0 days deferral          │
  │    Ring 2 (Pilot):   15% - 3 days deferral          │
  │    Ring 3 (General): 80% - 7 days deferral          │
  │    Auto-rollback: se KPI incident > 2%              │
  │                                                     │
  │  Group: "Produzione/Frontline"                      │
  │    Ring 1 (Test):     2% - 0 days deferral          │
  │    Ring 2 (Pilot):    8% - 7 days deferral          │
  │    Ring 3 (General): 90% - 14 days deferral         │
  │    Auto-rollback: se KPI incident > 1%              │
  └────────────────────────────────────────────────────┘

Reporting avanzato:
  - Windows quality update report: stato per ring con timeline
  - Hotpatch compliance: percentuale dispositivi con hotpatch attivo
  - Incident report: dispositivi con problemi post-update
  - Autopatch alerts: notifiche proattive per anomalie nel rollout
```

---

## App Protection Policies — MAM Deep Dive

Le App Protection Policies (APP), note anche come MAM policies, sono il meccanismo per proteggere i dati aziendali a livello di applicazione, senza richiedere il device enrollment. Questo è fondamentale per scenari BYOD dove l'utente non vuole (o l'azienda non può) gestire l'intero dispositivo.

### Architettura MAM

```
┌─────────────────────────────────────────────────────────┐
│              DISPOSITIVO PERSONALE (BYOD)                │
│                                                          │
│  ┌─────────────────────┐  ┌─────────────────────┐      │
│  │ ZONA PERSONALE      │  │ ZONA AZIENDALE      │      │
│  │                     │  │ (Protetta da MAM)    │      │
│  │ WhatsApp            │  │ Outlook ──────┐      │      │
│  │ Instagram           │  │ Teams   ──────┤ MAM  │      │
│  │ Facebook            │  │ OneDrive ─────┤ SDK  │      │
│  │ Chrome personale    │  │ Edge    ──────┤      │      │
│  │ Foto personali      │  │ SharePoint ───┘      │      │
│  │                     │  │                      │      │
│  │ Zero restrizioni    │  │ App PIN richiesto    │      │
│  │ Nessun monitoraggio │  │ Copy/paste bloccato  │      │
│  │                     │  │ Dati cifrati         │      │
│  │                     │  │ Wipe selettivo       │      │
│  └─────────────────────┘  └─────────────────────┘      │
│                                                          │
│           NESSUN ENROLLMENT MDM RICHIESTO                │
└─────────────────────────────────────────────────────────┘
```

### Configurazione App Protection Policy — iOS

```
Apps → App protection policies → Create policy → iOS/iPadOS

Target apps:
  - Target to all apps (raccomandato per copertura completa)
  -- oppure --
  - Select specific apps:
    - Microsoft Outlook
    - Microsoft Teams
    - Microsoft OneDrive
    - Microsoft SharePoint
    - Microsoft Edge

Data protection:
  - Send org data to other apps: Policy managed apps
    (impedisce copia dati verso app non gestite)
  - Receive data from other apps: All apps
    (permette importazione da qualsiasi app)
  - Restrict cut, copy, and paste between other apps: Policy managed apps with paste in
  - Save copies of org data: Block
    (impedisce "Save As" verso servizi non autorizzati)
  - Allow user to save copies to selected services: OneDrive for Business, SharePoint
  - Org data notification: Block org data
    (impedisce anteprima dati aziendali nelle notifiche lock screen)
  - Encrypt org data: Require
  - Sync policy managed app data with native apps: Block
    (impedisce sync contatti/calendario con app native)

Access requirements:
  - PIN for access: Require
  - PIN type: Numeric
  - Simple PIN: Block
  - PIN length: 6
  - Biometric instead of PIN: Allow
  - PIN reset after number of days: 90
  - Org credentials for access: Not required

Conditional launch:
  - Max PIN attempts: 5 → Reset PIN
  - Offline grace period: 720 minutes → Block access
  - Jailbroken/rooted devices: Block access
  - Min OS version: 16.0 → Block access
  - Max threat level: Secured → Block access (con MDE integration)
  - Disabled account: Block access
```

### Configurazione App Protection Policy — Android

```
Apps → App protection policies → Create policy → Android

Data protection:
  - Backup org data to Android backup services: Block
  - Send org data to other apps: Policy managed apps
  - Receive data from other apps: All apps
  - Restrict cut, copy, paste: Policy managed apps with paste in
  - Screen capture and Google Assistant: Block
  - Approved keyboards: Require (configurare solo tastiere fidate)
  - Encrypt org data: Require

Access requirements:
  - PIN for access: Require
  - PIN type: Numeric
  - Simple PIN: Block
  - PIN length: 6
  - Fingerprint instead of PIN: Allow
  - Override biometrics with PIN after timeout: Require (24 hours)
  - Work or school account credentials: Not required

Conditional launch:
  - Max PIN attempts: 5 → Wipe data
  - Offline grace period: 720 minutes → Block access
  - Jailbroken/rooted devices: Wipe data
  - SafetyNet device attestation: Basic integrity and certified devices → Block access
  - Require threat scan on apps: Require → Block access
  - Max OS version: Latest-2 → Warn
```

### Wipe Selettivo MAM

```powershell
# Wipe selettivo dei dati aziendali (MAM only, non tocca dati personali)
$uri = "https://graph.microsoft.com/v1.0/users/{userId}/managedAppRegistrations"
$headers = @{ Authorization = "Bearer $accessToken" }
$registrations = Invoke-RestMethod -Uri $uri -Headers $headers

# Per ogni app registrata con MAM, inviare il wipe command
foreach ($reg in $registrations.value) {
    $wipeUri = "https://graph.microsoft.com/v1.0/users/{userId}/wipeManagedAppRegistrationsByDeviceTag"
    $wipeBody = @{ deviceTag = $reg.deviceTag } | ConvertTo-Json
    Invoke-RestMethod -Uri $wipeUri -Method POST -Headers $headers -Body $wipeBody -ContentType "application/json"
    Write-Output "Wipe MAM inviato per device: $($reg.deviceName)"
}
```

---

## Intune vs SCCM/ConfigMgr — Confronto Dettagliato

La scelta tra Intune e SCCM (ora Microsoft Endpoint Configuration Manager / MECM) dipende dallo scenario specifico dell'organizzazione. Entrambi hanno punti di forza e limitazioni:

```
┌──────────────────────────────────────────────────────────────────┐
│                    INTUNE vs SCCM/MECM                           │
│                                                                  │
│  Aspetto              │ Intune              │ SCCM/MECM          │
│  ─────────────────────┼─────────────────────┼────────────────────│
│  Infrastruttura       │ Cloud-only          │ On-premises server │
│  Connettività         │ Internet (HTTPS)    │ Rete aziendale     │
│  Gestione OS deploy   │ Autopilot (limited) │ Task Sequence      │
│  Imaging custom       │ No                  │ Sì (OSD, PXE)     │
│  Software metering    │ Limitato            │ Completo           │
│  Patch mgmt granulare │ WUfB rings          │ WSUS + SUG         │
│  App deploy complesso │ Win32 app           │ Packages + Apps    │
│  Scripting            │ PowerShell scripts  │ PowerShell + CMPivot│
│  Inventory            │ Limitato            │ HW/SW dettagliato  │
│  Reporting            │ Graph API + Log An. │ SSRS + CMPivot     │
│  Agent required       │ No (MDM nativo)     │ Sì (CCMClient)    │
│  macOS/iOS/Android    │ Nativo              │ Limitato (con plug)│
│  Costo infrastruttura │ Zero (cloud)        │ Server + DB + DPs  │
│  Scalabilità          │ Illimitata          │ Pianificazione req. │
│  Velocità policy      │ 8h check-in         │ Immediato (TCP)    │
│  OS deployment bare   │ No                  │ Sì (PXE, USB, Task)│
│  metal                │                     │                    │
│  RBAC                 │ Scope tags + roles  │ Security scopes    │
│  Bandwidth control    │ Delivery Optim.     │ BranchCache + DPs  │
│  VPN/cert deploy      │ Sì                  │ Sì                 │
│  Compliance assess    │ Nativo + CA         │ Baselines + DCM    │
└──────────────────────────────────────────────────────────────────┘

Quando scegliere INTUNE:
  ✓ Organizzazione cloud-first o cloud-only
  ✓ Workforce prevalentemente remota
  ✓ Dispositivi iOS/Android da gestire
  ✓ Scenari BYOD importanti
  ✓ Nessuna infrastruttura on-premises disponibile
  ✓ Nuovi deployment senza legacy

Quando scegliere SCCM/MECM:
  ✓ OS deployment bare-metal richiesto (PXE, task sequence)
  ✓ Software distribution complesso (con script pre/post install)
  ✓ Inventory hardware/software dettagliato necessario
  ✓ Compliance baselines molto specifiche
  ✓ Reti con banda limitata verso Internet
  ✓ Migliaia di applicazioni legacy da gestire

Quando scegliere CO-MANAGEMENT:
  ✓ Migrazione graduale da SCCM a Intune
  ✓ Necessità di entrambe le piattaforme durante la transizione
  ✓ Scenari ibridi con workload specifici per piattaforma
```

---

## Co-Management con SCCM/MECM

Il co-management è un modello di transizione che permette di gestire i dispositivi Windows simultaneamente con Microsoft Endpoint Configuration Manager (MECM/SCCM) e Microsoft Intune. Questo approccio consente una migrazione graduale dei workload da SCCM a Intune senza interruzioni.

### Workload di Co-Management

Ogni workload può essere assegnato indipendentemente a SCCM o a Intune:

| Workload | Descrizione | Raccomandazione |
|----------|-------------|-----------------|
| Compliance Policies | Valutazione della conformità del dispositivo | Intune (per Conditional Access) |
| Device Configuration | Profili di configurazione | Graduale migrazione a Intune |
| Resource Access Policies | Certificati, WiFi, VPN profiles | Intune |
| Endpoint Protection | Antivirus, firewall, ASR | Intune (per MDE integration) |
| Windows Update Policies | Gestione aggiornamenti | Intune (WUfB) |
| Office Click-to-Run | Distribuzione e aggiornamento Office | SCCM o Intune |
| Client Apps | Distribuzione applicazioni | Graduale, dipende dalla complessità |

```powershell
# Verificare lo stato di co-management su un dispositivo
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\CCM" -Name "CoManagementFlags" -ErrorAction SilentlyContinue

# Verificare quali workload sono gestiti da Intune
# 0 = SCCM, 1 = Pilot Intune, 2 = Intune
# Il valore è una bitmask dei workload

# Verificare la connettività con entrambi i servizi di gestione
$sccm = Get-WmiObject -Namespace "root\CCM" -Class "SMS_Client" -ErrorAction SilentlyContinue
$mdm = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Enrollments\*" |
    Where-Object { $_.ProviderID -eq "MS DM Server" }

[PSCustomObject]@{
    SCCMClient  = if ($sccm) { "Installato (v$($sccm.ClientVersion))" } else { "Non presente" }
    MDMEnrolled = if ($mdm) { "Registrato (UPN: $($mdm.UPN))" } else { "Non registrato" }
}
```

### Migrazione dei Workload

La migrazione da SCCM a Intune segue tipicamente queste fasi:

```
Fase 1: Preparazione (2-4 settimane)
├── Configurare Azure AD Connect (hybrid join)
├── Abilitare co-management in SCCM
├── Configurare auto-enrollment MDM in Azure AD
└── Verificare la connettività cloud dai client

Fase 2: Pilot (4-8 settimane)
├── Spostare Compliance Policies su Intune (gruppo pilot)
├── Spostare Endpoint Protection su Intune
├── Monitorare con Endpoint Analytics
└── Risolvere i problemi identificati

Fase 3: Broad Deployment (8-16 settimane)
├── Spostare tutti i workload su Intune gradualmente
├── Configurare WUfB per gli aggiornamenti
├── Migrare i profili di configurazione
└── Migrare la distribuzione delle applicazioni

Fase 4: Decommissioning SCCM (opzionale)
├── Verificare che tutti i workload siano su Intune
├── Rimuovere il client SCCM dai dispositivi
└── Dismettere l'infrastruttura SCCM
```

---

## Tenant Attach

Il Tenant Attach è una funzionalità che connette l'infrastruttura SCCM/MECM on-premises al cloud Intune senza richiedere il co-management completo. Permette di visualizzare i dispositivi gestiti da SCCM nel portale cloud di Intune e di eseguire azioni remote dal cloud.

### Architettura Tenant Attach

```
┌─────────────────────────────────────────────────────────┐
│           Microsoft Intune Admin Center (Cloud)          │
│                                                          │
│  Visibilità dispositivi SCCM + Azioni remote            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │Timeline  │  │CMPivot   │  │Scripts   │              │
│  │eventi    │  │(cloud)   │  │(cloud)   │              │
│  └──────────┘  └──────────┘  └──────────┘              │
│                       ▲                                  │
│                       │ Service Connection Point         │
│                       │ (outbound HTTPS only)            │
├───────────────────────┼──────────────────────────────────┤
│           SCCM/MECM On-Premises                          │
│                       │                                  │
│  ┌──────────────────────────────────────────┐            │
│  │ Device Collection "All Desktop and       │            │
│  │ Server Clients"                          │            │
│  │                                          │            │
│  │ PC-001, PC-002, SRV-001, SRV-002 ...    │            │
│  └──────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────┘
```

### Funzionalità Tenant Attach

```
Con Tenant Attach puoi:
  1. Visualizzare tutti i dispositivi SCCM nel portale Intune
  2. Eseguire CMPivot queries dal cloud (senza VPN al site server)
  3. Eseguire script PowerShell dal cloud
  4. Visualizzare la timeline degli eventi del dispositivo
  5. Applicare Endpoint Security policies da Intune a dispositivi SCCM
  6. Visualizzare le applicazioni installate e la compliance

NON è co-management:
  - I workload restano su SCCM
  - Non c'è MDM enrollment in Intune
  - Non c'è Conditional Access (nessun compliance state in Azure AD)
  - È un "ponte di visibilità", non una gestione dual

Configurazione:
  SCCM Console → Administration → Cloud Services → Co-management
  → Configure co-management → Sign in → Enable cloud attach
  → Upload all devices to Microsoft Endpoint Manager
```

```powershell
# Verificare lo stato del Service Connection Point
$scp = Get-WmiObject -Namespace "root\SMS\site_XXX" -Class SMS_SCI_SysResUse `
    -Filter "RoleName='SMS Service Connection Point'"
$scp | Select-Object ServerName, NetworkOSPath

# Verificare la connettività cloud dal Service Connection Point
$tenantAttachEndpoints = @(
    "https://login.microsoftonline.com"
    "https://graph.microsoft.com"
    "https://configmgrbmsweu.azurewebsites.net"
)
foreach ($ep in $tenantAttachEndpoints) {
    try {
        Invoke-WebRequest $ep -UseBasicParsing -TimeoutSec 10
        Write-Output "OK: $ep"
    } catch {
        Write-Warning "FAIL: $ep"
    }
}
```

---

## Reporting e Graph API

Microsoft Graph API fornisce accesso programmatico a tutti i dati di Intune per reporting e automazione avanzati.

```powershell
# Autenticazione con Graph API (app registration)
$tenantId = "your-tenant-id"
$clientId = "your-app-client-id"
$clientSecret = "your-client-secret"

$body = @{
    grant_type    = "client_credentials"
    client_id     = $clientId
    client_secret = $clientSecret
    scope         = "https://graph.microsoft.com/.default"
}

$token = (Invoke-RestMethod -Uri "https://login.microsoftonline.com/$tenantId/oauth2/v2.0/token" `
    -Method POST -Body $body).access_token

$headers = @{ Authorization = "Bearer $token" }

# Report: dispositivi non compliant
$nonCompliant = Invoke-RestMethod -Uri "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices?`$filter=complianceState eq 'noncompliant'&`$select=deviceName,complianceState,lastSyncDateTime,userPrincipalName,operatingSystem" `
    -Headers $headers

$nonCompliant.value | ForEach-Object {
    [PSCustomObject]@{
        Device     = $_.deviceName
        User       = $_.userPrincipalName
        OS         = $_.operatingSystem
        LastSync   = $_.lastSyncDateTime
        Compliance = $_.complianceState
    }
} | Format-Table -AutoSize

# Report: applicazioni installate su un dispositivo
$deviceId = "device-id-here"
$apps = Invoke-RestMethod -Uri "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices/$deviceId/detectedApps" -Headers $headers

$apps.value | Select-Object displayName, version, sizeInByte |
    Sort-Object displayName | Format-Table -AutoSize

# Report: stato deployment di un'applicazione
$appId = "app-id-here"
$status = Invoke-RestMethod -Uri "https://graph.microsoft.com/v1.0/deviceAppManagement/mobileApps/$appId/deviceStatuses" -Headers $headers

$status.value | Group-Object installState |
    Select-Object Name, Count | Format-Table -AutoSize
```

---

## Automazione Avanzata con Graph API

```powershell
# Azione remota: sincronizzare un dispositivo
$deviceId = "device-id-here"
Invoke-RestMethod -Uri "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices/$deviceId/syncDevice" `
    -Method POST -Headers $headers

# Azione remota: wipe selettivo (rimuove solo dati aziendali)
Invoke-RestMethod -Uri "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices/$deviceId/retire" `
    -Method POST -Headers $headers

# Azione remota: wipe completo (factory reset)
$wipeBody = @{
    keepEnrollmentData = $false
    keepUserData = $false
} | ConvertTo-Json
Invoke-RestMethod -Uri "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices/$deviceId/wipe" `
    -Method POST -Headers $headers -Body $wipeBody -ContentType "application/json"

# Report automatizzato giornaliero
function Get-IntuneDailyReport {
    param(
        [string]$AccessToken,
        [string]$OutputPath = "C:\Reports"
    )
    $headers = @{ Authorization = "Bearer $AccessToken" }
    $date = Get-Date -Format "yyyy-MM-dd"

    # Raccogliere dati
    $allDevices = Invoke-RestMethod -Uri "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices?`$select=deviceName,complianceState,operatingSystem,lastSyncDateTime,userPrincipalName,managedDeviceOwnerType" `
        -Headers $headers

    $report = $allDevices.value | ForEach-Object {
        [PSCustomObject]@{
            Device     = $_.deviceName
            User       = $_.userPrincipalName
            OS         = $_.operatingSystem
            Compliance = $_.complianceState
            Ownership  = $_.managedDeviceOwnerType
            LastSync   = $_.lastSyncDateTime
            StaleDays  = if ($_.lastSyncDateTime) {
                (New-TimeSpan -Start ([datetime]$_.lastSyncDateTime) -End (Get-Date)).Days
            } else { 999 }
        }
    }

    # Sommario
    $summary = [PSCustomObject]@{
        ReportDate       = $date
        TotalDevices     = $report.Count
        Compliant        = ($report | Where-Object Compliance -eq 'compliant').Count
        NonCompliant     = ($report | Where-Object Compliance -eq 'noncompliant').Count
        Unknown          = ($report | Where-Object Compliance -eq 'unknown').Count
        StaleOver7Days   = ($report | Where-Object StaleDays -gt 7).Count
        StaleOver30Days  = ($report | Where-Object StaleDays -gt 30).Count
        Corporate        = ($report | Where-Object Ownership -eq 'company').Count
        Personal         = ($report | Where-Object Ownership -eq 'personal').Count
    }

    # Esportare
    $report | Export-Csv "$OutputPath\IntuneDevices-$date.csv" -NoTypeInformation -Encoding UTF8
    $summary | Format-List

    return $summary
}

# Bulk device rename via Graph API
function Rename-IntuneDevices {
    param(
        [string]$AccessToken,
        [string]$CsvPath  # CSV con colonne: DeviceId, NewName
    )
    $headers = @{
        Authorization = "Bearer $AccessToken"
        "Content-Type" = "application/json"
    }

    $devices = Import-Csv $CsvPath
    foreach ($device in $devices) {
        $body = @{ deviceName = $device.NewName } | ConvertTo-Json
        try {
            Invoke-RestMethod -Uri "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices/$($device.DeviceId)/setDeviceName" `
                -Method POST -Headers $headers -Body $body
            Write-Output "Renamed: $($device.DeviceId) → $($device.NewName)"
        } catch {
            Write-Warning "Failed to rename $($device.DeviceId): $_"
        }
    }
}
```

---

## Script Proattivi e Remediation Avanzata

### Esempio: Verificare e Aggiornare la Timezone

```powershell
# Detection Script
$expectedTimezone = "W. Europe Standard Time"
$currentTimezone = (Get-TimeZone).Id

if ($currentTimezone -ne $expectedTimezone) {
    Write-Output "Timezone is $currentTimezone, expected $expectedTimezone"
    exit 1
} else {
    Write-Output "Timezone OK: $currentTimezone"
    exit 0
}

# Remediation Script
$expectedTimezone = "W. Europe Standard Time"
try {
    Set-TimeZone -Id $expectedTimezone
    Write-Output "Timezone set to $expectedTimezone"
    exit 0
} catch {
    Write-Error "Failed to set timezone: $_"
    exit 1
}
```

### Esempio: Verificare lo Stato di BitLocker

```powershell
# Detection Script
$volume = Get-BitLockerVolume -MountPoint "C:" -ErrorAction SilentlyContinue
if (-not $volume -or $volume.ProtectionStatus -ne 'On') {
    Write-Output "BitLocker not active on C:"
    exit 1
} elseif ($volume.EncryptionPercentage -lt 100) {
    Write-Output "BitLocker encryption in progress: $($volume.EncryptionPercentage)%"
    exit 1
} else {
    Write-Output "BitLocker fully active on C:"
    exit 0
}

# Remediation Script
try {
    Enable-BitLocker -MountPoint "C:" -EncryptionMethod XtsAes256 `
        -RecoveryPasswordProtector -SkipHardwareTest
    $recoveryKey = (Get-BitLockerVolume -MountPoint "C:").KeyProtector |
        Where-Object KeyProtectorType -eq 'RecoveryPassword' |
        Select-Object -ExpandProperty RecoveryPassword
    Write-Output "BitLocker enabled. Recovery Key: $recoveryKey"
    # La recovery key viene automaticamente salvata in Azure AD/Intune
    exit 0
} catch {
    Write-Error "Failed to enable BitLocker: $_"
    exit 1
}
```

### Esempio: Pulizia Profili Utente Obsoleti

```powershell
# Detection Script
$threshold = 90  # giorni
$profiles = Get-CimInstance Win32_UserProfile |
    Where-Object {
        -not $_.Special -and
        $_.LocalPath -notmatch "\\(Default|Public|Administrator)$" -and
        $_.LastUseTime -lt (Get-Date).AddDays(-$threshold)
    }

if ($profiles.Count -gt 0) {
    $totalSizeMB = ($profiles | ForEach-Object {
        (Get-ChildItem $_.LocalPath -Recurse -ErrorAction SilentlyContinue |
            Measure-Object Length -Sum).Sum
    } | Measure-Object -Sum).Sum / 1MB

    Write-Output "$($profiles.Count) stale profiles found, ~$([math]::Round($totalSizeMB)) MB recoverable"
    exit 1
} else {
    Write-Output "No stale profiles"
    exit 0
}

# Remediation Script
$threshold = 90
$profiles = Get-CimInstance Win32_UserProfile |
    Where-Object {
        -not $_.Special -and
        $_.LocalPath -notmatch "\\(Default|Public|Administrator)$" -and
        $_.LastUseTime -lt (Get-Date).AddDays(-$threshold)
    }

foreach ($profile in $profiles) {
    try {
        $profile | Remove-CimInstance
        Write-Output "Removed profile: $($profile.LocalPath)"
    } catch {
        Write-Warning "Failed to remove $($profile.LocalPath): $_"
    }
}
exit 0
```

### Custom Compliance Scripts — Pattern avanzati

Le **Custom Compliance Scripts** di Intune estendono le compliance policy standard, permettendo di verificare condizioni arbitrarie tramite script PowerShell. Lo script viene eseguito sul dispositivo, restituisce un JSON con le proprietà rilevate, e Intune confronta i valori con le regole definite nel JSON di detection.

```
Flusso Custom Compliance:

┌──────────────────────────────────────────────────────────────┐
│ Intune Portal                                                 │
│                                                               │
│  1. Upload detection script (PowerShell)                      │
│     → Lo script raccoglie dati dal dispositivo                │
│     → Ritorna JSON con coppie chiave/valore                   │
│                                                               │
│  2. Upload compliance rules (JSON)                            │
│     → Definisce le condizioni per ogni proprietà              │
│     → Include messaggi di remediation localizzati             │
│                                                               │
│  3. Assegna alla compliance policy                            │
│     → Devices → Compliance → Create → Custom Compliance      │
│     → Seleziona script + JSON                                 │
│     → Assegna a gruppi                                        │
└──────────────────────────────────────────────────────────────┘
```

```powershell
# Custom Compliance Script avanzato — Verifica sicurezza completa
# Controlla: antivirus, firewall, secure boot, certificato aziendale

$result = @{}

# Verifica Windows Defender real-time protection
$mpStatus = Get-MpComputerStatus -ErrorAction SilentlyContinue
$result["AntivirusEnabled"] = $mpStatus.AntivirusEnabled
$result["RealTimeProtectionEnabled"] = $mpStatus.RealTimeProtectionEnabled
$result["AntivirusSignatureAge"] = $mpStatus.AntivirusSignatureAge  # giorni

# Verifica Windows Firewall (tutti i profili)
$fwProfiles = Get-NetFirewallProfile -ErrorAction SilentlyContinue
$allEnabled = ($fwProfiles | Where-Object { $_.Enabled -eq $false }).Count -eq 0
$result["AllFirewallProfilesEnabled"] = $allEnabled

# Verifica Secure Boot
$secureBoot = Confirm-SecureBootUEFI -ErrorAction SilentlyContinue
$result["SecureBootEnabled"] = ($secureBoot -eq $true)

# Verifica presenza certificato root aziendale
$certThumbprint = "AB1234CD5678EF..."  # Thumbprint del cert aziendale
$cert = Get-ChildItem Cert:\LocalMachine\Root |
    Where-Object { $_.Thumbprint -eq $certThumbprint }
$result["CorporateRootCertInstalled"] = ($cert -ne $null)

# Verifica che PowerShell execution policy non sia Unrestricted
$policy = Get-ExecutionPolicy -Scope LocalMachine
$result["ExecutionPolicySecure"] = ($policy -ne "Unrestricted")

# Verifica data ultimo riavvio (dispositivi che non riavviano da 30+ giorni)
$lastBoot = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
$daysSinceBoot = ((Get-Date) - $lastBoot).Days
$result["DaysSinceLastReboot"] = $daysSinceBoot

# Output JSON per Intune
return $result | ConvertTo-Json -Compress
```

```json
{
  "Rules": [
    {
      "SettingName": "AntivirusEnabled",
      "Operator": "IsEquals",
      "DataType": "Boolean",
      "Operand": true,
      "MoreInfoUrl": "https://docs.contoso.com/security/antivirus",
      "RemediationStrings": [
        { "Language": "it_IT",
          "Title": "Antivirus non attivo",
          "Description": "Windows Defender deve essere abilitato su tutti i dispositivi aziendali." }
      ]
    },
    {
      "SettingName": "AntivirusSignatureAge",
      "Operator": "IsLessThan",
      "DataType": "Int64",
      "Operand": 3,
      "RemediationStrings": [
        { "Language": "it_IT",
          "Title": "Firme antivirus obsolete",
          "Description": "Le firme antivirus devono essere aggiornate negli ultimi 3 giorni." }
      ]
    },
    {
      "SettingName": "SecureBootEnabled",
      "Operator": "IsEquals",
      "DataType": "Boolean",
      "Operand": true,
      "RemediationStrings": [
        { "Language": "it_IT",
          "Title": "Secure Boot disabilitato",
          "Description": "Secure Boot deve essere abilitato nel BIOS/UEFI del dispositivo." }
      ]
    },
    {
      "SettingName": "DaysSinceLastReboot",
      "Operator": "IsLessThan",
      "DataType": "Int64",
      "Operand": 30,
      "RemediationStrings": [
        { "Language": "it_IT",
          "Title": "Riavvio necessario",
          "Description": "Il dispositivo non viene riavviato da oltre 30 giorni. Riavviare per applicare aggiornamenti." }
      ]
    }
  ]
}
```

### Script di Remediation — best practice di scrittura

Gli script di remediation devono seguire regole precise per funzionare correttamente in Intune:

```
Regole per Remediation Scripts in Intune:

1. Exit codes:
   ├── Detection script:
   │   exit 0 = nessun problema rilevato (compliant)
   │   exit 1 = problema rilevato → esegui remediation
   │
   └── Remediation script:
       exit 0 = remediation riuscita
       exit 1 = remediation fallita (errore loggato in Intune)

2. Output:
   ├── Write-Output → visibile nei log Intune
   ├── Write-Error → visibile come errore nei log
   └── Massimo 2048 caratteri di output catturati

3. Contesto di esecuzione:
   ├── System context: eseguito come SYSTEM (default)
   │   → Accesso a HKLM, servizi, file di sistema
   │   → NO accesso al profilo utente ($env:USERPROFILE)
   ├── User context: opzione "Run this script using
   │   the logged-on credentials"
   │   → Accesso a HKCU, profilo utente
   │   → NO accesso admin (a meno che l'utente sia admin)
   └── Scheduling: ogni 1, 4, 8, 12, 24 ore (configurabile)

4. Idempotenza obbligatoria:
   ├── Lo script verrà eseguito più volte
   ├── Deve produrre lo stesso risultato se eseguito 2 volte
   └── No side-effect indesiderati su esecuzioni ripetute

5. Timeout:
   └── Massimo 60 minuti per l'esecuzione dello script
       → Script che superano il timeout vengono terminati
```

---

## Gestione dei Dispositivi Multipiattaforma

### macOS Management con Intune

```
Enrollment macOS:
  - Automated Device Enrollment (ADE) via Apple Business Manager
  - User Enrollment (utente installa Company Portal)

Funzionalità disponibili:
  - Configuration profiles (PLIST-based)
  - Compliance policies (FileVault, password, OS version)
  - App deployment (.dmg, .pkg, App Store apps)
  - Shell scripts (eseguiti come script management)
  - Platform SSO (Single Sign-On)
  - Microsoft Edge deployment e configurazione
  - FileVault encryption management
  - Privacy Preferences (TCC) profiles

Limitazioni rispetto a Windows:
  - Nessun Settings Catalog (solo Custom config profiles)
  - Proactive Remediations non supportate
  - Win32 app packaging non applicabile
```

### Platform SSO per macOS — Deep Dive

**Platform SSO** (PSSO) è la funzionalità che porta l'esperienza Single Sign-On nativa a macOS, integrando l'autenticazione Entra ID direttamente nel sistema operativo. A differenza del precedente SSO Extension (basato su Kerberos o redirect), Platform SSO opera a livello di login screen macOS, sincronizzando la password locale con Entra ID o sostituendola completamente con autenticazione passwordless.

```
Architettura Platform SSO su macOS:

┌────────────────────────────────────────────────────────────┐
│ macOS Device (gestito via Intune + ADE)                     │
│                                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Login Screen macOS                                     │ │
│  │  ├── Utente inserisce password locale                  │ │
│  │  │   OPPURE Touch ID / SmartCard / Passkey             │ │
│  │  └── Platform SSO intercetta → autentica con Entra ID  │ │
│  └──────────────────┬─────────────────────────────────────┘ │
│                     │                                        │
│  ┌──────────────────▼─────────────────────────────────────┐ │
│  │ SSO Extension (Microsoft Enterprise SSO plug-in)       │ │
│  │  ├── Primary Refresh Token (PRT) → sessione SSO       │ │
│  │  ├── Secure Enclave binding → chiave device-bound      │ │
│  │  ├── Token cache → accesso silenzioso a M365, SaaS    │ │
│  │  └── Kerberos ticket (se configurato) → accesso AD     │ │
│  └──────────────────┬─────────────────────────────────────┘ │
│                     │                                        │
│  ┌──────────────────▼─────────────────────────────────────┐ │
│  │ Applicazioni                                           │ │
│  │  ├── Safari / Edge → SSO automatico verso M365         │ │
│  │  ├── App native (Teams, Outlook) → PRT silenzioso      │ │
│  │  └── App terze parti con SAML/OIDC → redirect SSO     │ │
│  └────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

**Secure Enclave binding**: quando Platform SSO è configurato, la chiave crittografica del dispositivo viene archiviata nel **Secure Enclave** del chip Apple (T2 o Apple Silicon). Questo significa che il token di autenticazione è legato fisicamente al dispositivo hardware — non può essere estratto, copiato o utilizzato su un altro Mac. Equivale funzionalmente alla TPM binding di Windows Hello for Business.

**Metodi di autenticazione supportati**:

```
Platform SSO supporta tre metodi di autenticazione:

1. Password Sync (Sincronizzazione password):
   ├── La password locale macOS viene sincronizzata con Entra ID
   ├── Cambio password in uno dei due sistemi → aggiornato nell'altro
   ├── Utile come primo passo di migrazione verso PSSO
   └── Richiede: Microsoft Enterprise SSO plug-in + Company Portal

2. Secure Enclave (Passwordless - Raccomandato):
   ├── Autenticazione tramite chiave hardware nel Secure Enclave
   ├── L'utente sblocca con Touch ID, password locale, o SmartCard
   ├── La chiave Secure Enclave firma la richiesta di autenticazione
   ├── Nessuna password trasmessa verso Entra ID
   ├── Phishing-resistant (non intercettabile)
   └── Richiede: macOS 14+ (Sonoma), Apple Silicon o T2

3. SmartCard:
   ├── Certificato su SmartCard fisica o PIV virtual card
   ├── Utilizzato in ambienti governativi / alta sicurezza
   └── Richiede: lettore SmartCard + infrastruttura PKI

Configurazione Intune (Settings Catalog):
  Devices → macOS → Configuration → Settings Catalog
  → Extensible Single Sign On (SSO)
  → Platform SSO:

  Authentication Method: "User Secure Enclave Key"
  Registration Token: "<token-generato-da-Entra-ID>"
  Enable Registration During Setup: Yes  ← per ADE (zero-touch)
  Screen Locked Behavior: "Do Not Handle"
  Use Shared Device Keys: No
```

**Integrazione con Automated Device Enrollment (ADE)**: quando `EnableRegistrationDuringSetup` è impostato su `Yes`, il Mac si registra in Platform SSO durante il Setup Assistant (il flusso iniziale di configurazione del Mac). L'utente completa l'ADE, crea il proprio account locale, e il sistema registra automaticamente la chiave Secure Enclave con Entra ID. Dal login successivo, l'autenticazione è completamente integrata. Questo elimina il passaggio separato "apri Company Portal e registrati" che era necessario con l'approccio legacy.

### Linux Management — Stato aggiornato 2025

```
Piattaforme supportate (aggiornamento 2025):
  - Ubuntu Desktop 22.04, 24.04 LTS
  - Ubuntu Server 22.04, 24.04 LTS
  - RedHat Enterprise Linux 8.x, 9.x
  - Fedora 38+ (preview)
  - Nota: Ubuntu 20.04 è stato deprecato dal supporto Intune

Funzionalità disponibili:
  - Device compliance verification
  - Conditional Access support (via Edge browser)
  - Compliance policies: encryption, OS version, password
  - Custom compliance scripts (Bash)
  - Microsoft Edge deployment e managed browser
  - Microsoft Defender for Endpoint (agente Linux nativo)
```

**Nuovo flusso di enrollment SSO (2024-2025)**: Microsoft ha sostituito il vecchio componente di autenticazione basato su `microsoft-identity-broker` con un nuovo flusso integrato in Microsoft Edge. L'utente non deve più installare un componente separato per l'autenticazione. Il processo aggiornato funziona così:

```
Flusso di enrollment Linux aggiornato:

1. Prerequisiti:
   ├── Microsoft Edge installato (apt/dnf)
   ├── Microsoft Intune app installata
   │   (pacchetto .deb o .rpm dal packages.microsoft.com)
   └── Connettività verso login.microsoftonline.com

2. Enrollment:
   ├── L'utente apre Edge → naviga a portal.manage.microsoft.com
   ├── Si autentica con credenziali Entra ID
   ├── Edge gestisce il flusso SSO e device registration
   ├── Il dispositivo viene registrato in Entra ID + Intune
   └── Le compliance policies vengono applicate

3. Post-enrollment:
   ├── Edge mantiene la sessione SSO (PRT-like)
   ├── L'accesso a risorse M365 via Edge è automatico
   ├── Conditional Access valuta: compliance + device health
   └── L'utente accede a SharePoint, Teams Web, ecc. senza re-auth

Compliance policies disponibili per Linux:
  ┌──────────────────────────────────┬──────────────────────┐
  │ Setting                          │ Supporto              │
  ├──────────────────────────────────┼──────────────────────┤
  │ OS version (min/max)             │ ✓ Supportato          │
  │ Password required                │ ✓ Supportato          │
  │ Password complexity              │ ✓ Supportato          │
  │ Disk encryption (LUKS/dm-crypt)  │ ✓ Supportato          │
  │ Custom compliance script (Bash)  │ ✓ Supportato          │
  │ Firewall enabled                 │ ✗ Non disponibile     │
  │ Antivirus status                 │ Parziale (MDE check)  │
  └──────────────────────────────────┴──────────────────────┘

Limitazioni importanti:
  - Nessun configuration profile (non si possono distribuire settings)
  - Nessun app deployment (le app si installano manualmente)
  - Nessun device wipe/remote lock
  - Solo compliance + Conditional Access
  - L'esperienza è significativamente più limitata vs Windows/macOS
```

---

## Intune Suite e Funzionalità Premium

### Remote Help

Remote Help è la soluzione di assistenza remota integrata in Intune, alternativa a TeamViewer/AnyDesk per scenari enterprise:

```
Funzionalità:
  - Full control o view-only
  - Richiede autenticazione Azure AD di entrambi (helpdesk e utente)
  - Audit completo delle sessioni in Intune logs
  - Supporto per dispositivi Windows e Android
  - RBAC: solo utenti autorizzati possono dare assistenza
  - Compliance check: helpdesk vede lo stato compliance del dispositivo

Configurazione:
  Tenant admin → Connectors and tokens → Remote Help
  → Enable Remote Help: Yes
  → Allow remote help to unenrolled devices: No (raccomandato)
```

### Endpoint Privilege Management (EPM)

EPM permette agli utenti standard di eseguire operazioni specifiche con privilegi elevati senza concedere i diritti di amministratore locale:

```
Scenari:
  - Installazione di software approvato (senza admin rights)
  - Esecuzione di tool diagnostici che richiedono elevation
  - Aggiornamento di driver specifici

Configurazione:
  Endpoint security → Endpoint Privilege Management → Policies

Esempio policy:
  Rule: Allow elevation for 7z-installer
  File: 7z2301-x64.msi
  Publisher: Igor Pavlov
  Action: Allow elevation with user justification
  Elevation type: User confirmed (utente deve confermare)
  Reporting: All elevations logged to Intune
```

### Endpoint Privilege Management — Funzionalità avanzate

EPM nel 2025 ha aggiunto **support-approved elevations** e **managed elevations con regole basate su certificato**. Il flusso support-approved permette all'utente di richiedere un'elevazione che viene approvata da un membro del team helpdesk tramite il portale Intune, con scadenza temporale automatica.

```
Flusso EPM Support-Approved:

1. Utente fa clic destro → "Run with elevated access"
2. EPM agent rileva che non esiste una regola automatica
3. Mostra dialog: "Richiesta inviata al supporto IT"
4. Nel portale Intune → Endpoint security → EPM → Pending requests:
   ├── Dettagli: utente, dispositivo, file, hash, publisher
   ├── Azione: Approve (con durata: 1h, 4h, 8h, 24h) / Deny
   └── Justification obbligatoria per audit
5. Se approvato → l'utente riceve notifica → può eseguire
6. Dopo la scadenza → il permesso viene revocato automaticamente

Regole certificate-based:
  Rule: Allow elevation for internal tools
  Certificate: CN=InternalTools-CodeSign, O=AziendaSRL
  Action: Allow automatic elevation (no prompt)
  → Tutti gli eseguibili firmati dal certificato aziendale
    vengono elevati automaticamente
```

### Advanced Analytics (Intune Suite)

Advanced Analytics estende Endpoint Analytics con capacità predittive e query personalizzate tramite **KQL (Kusto Query Language)** direttamente dal portale Intune. Mentre Endpoint Analytics base offre metriche predefinite (startup performance, app reliability), Advanced Analytics permette di scrivere query custom su dati telemetrici raccolti dai dispositivi gestiti.

```
Funzionalità Advanced Analytics:

1. Device Query (query in tempo reale):
   ├── Esegui query KQL su un dispositivo specifico in tempo reale
   ├── Accesso a: processi, servizi, hardware, software, registry
   ├── Esempio: query tutti i processi con CPU > 50%
   └── Utile per troubleshooting senza accesso remoto

   Esempio query:
   DeviceProcesses
   | where CPUUsage > 50
   | project ProcessName, PID, CPUUsage, MemoryUsageMB
   | sort by CPUUsage desc
   | take 10

2. Custom reporting:
   ├── Report personalizzati con filtri KQL
   ├── Dati storici fino a 30 giorni
   ├── Export in CSV/JSON
   └── Schedulazione report ricorrenti

3. Anomaly detection:
   ├── ML-based: rileva dispositivi con comportamento anomalo
   ├── Battery health prediction: stima vita residua batteria
   ├── App crash correlation: identifica pattern di crash
   └── Alerting configurabile su soglie custom

Licensing: richiede Intune Suite add-on o Intune Plan 2
```

### Cloud PKI (Intune Suite)

Cloud PKI è un servizio **PKI completamente gestito** che elimina la necessità di infrastruttura on-premises (ADCS, NDES, proxy connector). Microsoft gestisce la CA (Certificate Authority), il certificate lifecycle, e la distribuzione tramite SCEP profile.

```
Architettura Cloud PKI:

┌──────────────────────────────────────────────────────────┐
│ Microsoft Cloud                                           │
│                                                           │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Cloud PKI Service                                  │   │
│  │  ├── Root CA (Microsoft-hosted, HSM-backed)        │   │
│  │  ├── Issuing CA (per tenant, isolata)              │   │
│  │  ├── CRL / OCSP distribution                       │   │
│  │  └── Certificate lifecycle management              │   │
│  └──────────────────────┬─────────────────────────────┘   │
│                         │ SCEP protocol                    │
│  ┌──────────────────────▼─────────────────────────────┐   │
│  │ Intune Service                                     │   │
│  │  ├── SCEP certificate profile                      │   │
│  │  ├── Assignment a gruppi dispositivi               │   │
│  │  └── Compliance policy (verifica certificato)      │   │
│  └──────────────────────┬─────────────────────────────┘   │
└─────────────────────────┼─────────────────────────────────┘
                          │
┌─────────────────────────▼─────────────────────────────────┐
│ Dispositivo gestito                                        │
│  ├── Riceve SCEP profile → richiede certificato            │
│  ├── Certificato installato nel certificate store          │
│  ├── Usato per: Wi-Fi 802.1x, VPN, S/MIME, app auth      │
│  └── Rinnovo automatico prima della scadenza              │
└────────────────────────────────────────────────────────────┘

Vantaggi vs ADCS on-premises:
  - Zero infrastruttura da gestire (no server CA, no NDES, no connector)
  - HSM-backed root CA (sicurezza hardware)
  - Alta disponibilità garantita da Microsoft
  - Certificati distribuiti anche a dispositivi mai connessi a rete corporate
  - Supporta BYOD senza VPN verso infrastruttura interna
  - CRL e OCSP gestiti automaticamente
```

### Enterprise Application Management (Intune Suite)

Enterprise Application Management (EAM) fornisce un **catalogo curato di applicazioni third-party** direttamente nel portale Intune, con aggiornamenti automatici gestiti da Microsoft. Anziché scaricare, pacchettizzare e distribuire manualmente ogni aggiornamento di applicazioni come Chrome, Zoom, Adobe Reader, 7-Zip, ecc., EAM mantiene un catalogo sempre aggiornato.

```
Enterprise Application Management:

Catalogo app disponibili (esempi):
  ├── Browser: Google Chrome, Mozilla Firefox
  ├── Comunicazione: Zoom, Slack
  ├── Produttività: Adobe Acrobat Reader, Notepad++, 7-Zip
  ├── Sviluppo: Visual Studio Code, Git, Python
  ├── Sicurezza: KeePass, WinSCP
  └── Utility: VLC, PuTTY, WinRAR

Funzionalità:
  - App auto-update: Microsoft monitora nuove versioni e le
    rende disponibili nel catalogo. L'admin può configurare
    l'aggiornamento automatico o manuale (review + approve).
  - Self-service catalog: gli utenti vedono le app approvate
    nel Company Portal e le installano autonomamente.
  - Dependency handling: alcune app includono prerequisiti
    (es. .NET Runtime) installati automaticamente.

Configurazione:
  Apps → All apps → Add → Enterprise App Catalog app
  → Cerca l'applicazione nel catalogo
  → Seleziona versione e architettura
  → Configura: auto-update = Yes / No
  → Assegna a gruppi (Required / Available)
```

---

## Copilot in Intune

**Microsoft Copilot in Intune** è l'integrazione di AI generativa direttamente nel portale di amministrazione Intune, progettata per assistere gli amministratori IT nella gestione quotidiana. Non si tratta di un chatbot generico, ma di un assistente contestuale che comprende la configurazione specifica del tenant, le policy distribuite e lo stato dei dispositivi.

### Capacità principali

```
Copilot in Intune — Funzionalità:

1. Natural Language to KQL:
   ├── Domanda: "Quanti dispositivi hanno Windows 11 23H2?"
   ├── Copilot genera: Devices | where OSVersion contains "23H2"
   │                    | summarize count()
   ├── Esegue la query e mostra i risultati
   └── L'admin può modificare il KQL generato

2. Policy Summarization:
   ├── Seleziona una configuration policy complessa
   ├── Copilot: "Questa policy configura BitLocker con
   │   recovery key backup in Azure AD, richiede TPM 2.0,
   │   e abilita la crittografia dell'intero disco"
   └── Utile per audit e revisione policy legacy

3. Error Analysis:
   ├── Un dispositivo mostra errore di compliance
   ├── Copilot analizza i log e suggerisce:
   │   "Il dispositivo non è conforme perché la policy
   │    BitLocker richiede TPM 2.0 ma il dispositivo
   │    ha solo TPM 1.2. Opzioni: escludere il dispositivo
   │    dal gruppo o aggiornare l'hardware."
   └── Context-aware: conosce le policy assegnate al device

4. Configuration Comparison:
   ├── Confronta due policy o profili di configurazione
   ├── Evidenzia differenze e potenziali conflitti
   └── Suggerisce consolidamento dove possibile
```

### I quattro agenti Copilot per Intune (Preview 2025)

Microsoft ha annunciato quattro **agenti specializzati** per Copilot in Intune, ciascuno progettato per automatizzare un flusso di lavoro specifico:

```
Agenti Copilot in Intune:

┌──────────────────────────────────────────────────────────────┐
│ 1. Change Review Agent                                        │
│    ├── Monitora modifiche alle policy e configurazioni        │
│    ├── Genera report giornaliero: "Ieri sono state           │
│    │   modificate 3 policy. La policy 'BitLocker-Prod' ha    │
│    │   cambiato il metodo di recovery da AD a Azure AD"      │
│    ├── Rileva potenziali impatti: "Questa modifica            │
│    │   potrebbe bloccare 150 dispositivi non compatibili"    │
│    └── Raccomanda: rollback o conferma                       │
├──────────────────────────────────────────────────────────────┤
│ 2. Policy Configuration Agent                                 │
│    ├── Genera policy da descrizioni in linguaggio naturale    │
│    ├── Input: "Crea una policy che richieda BitLocker,        │
│    │   password di 12+ caratteri, e blocchi USB"             │
│    ├── Output: profilo di configurazione pronto da           │
│    │   revisionare e distribuire                              │
│    └── Include best practice e spiegazioni per ogni setting  │
├──────────────────────────────────────────────────────────────┤
│ 3. Vulnerability Remediation Agent                            │
│    ├── Integrazione con Microsoft Defender TVM                │
│    ├── Riceve alert: "CVE-2025-XXXX su 200 dispositivi"      │
│    ├── Propone azione: "Distribuire la patch KB5034xxx        │
│    │   tramite expedited quality update"                     │
│    ├── Crea automaticamente la policy di remediation          │
│    └── Monitora il rollout e riporta la compliance           │
├──────────────────────────────────────────────────────────────┤
│ 4. Device Offboarding Agent                                   │
│    ├── Gestisce il ciclo di vita di dismissione dispositivo   │
│    ├── Input: "Offboard il dispositivo LAPTOP-HR-042"        │
│    ├── Esegue: revoca certificati, rimuove da gruppi,        │
│    │   disabilita in Entra ID, wipe selettivo, archivia      │
│    │   in Autopilot                                          │
│    └── Genera report di compliance per audit                 │
└──────────────────────────────────────────────────────────────┘
```

### Licensing Copilot in Intune

```
Copilot in Intune — Modello di costo:

Pricing: Security Compute Units (SCU)
  - Costo: $4 USD / ora per SCU
  - Provisioning: minimo 1 SCU (= $4/ora = ~$2,880/mese)
  - Scaling: aggiungere SCU in base al carico
  - Shared: le SCU sono condivise tra tutti i workload
    Microsoft Security Copilot (Defender, Intune, Purview, ecc.)

Raccomandazione:
  - Iniziare con 1 SCU per valutazione (proof of concept)
  - Monitorare l'utilizzo nel portale Copilot Analytics
  - Scale-up basato su usage patterns reali
  - Considerare che l'uso sporadico (poche query/giorno) potrebbe
    non giustificare il costo di una SCU always-on
  - SCU può essere provisioned/deprovisioned on-demand
```

---

## Integrazione Intune e Microsoft Defender for Endpoint

L'integrazione tra **Intune** e **Microsoft Defender for Endpoint (MDE)** è bidirezionale e profonda. Intune gestisce la configurazione e la compliance dei dispositivi, mentre MDE fornisce la visibilità sulle minacce e le vulnerabilità. L'integrazione principale avviene tramite **Threat & Vulnerability Management (TVM)** e i **Security Tasks**.

### Architettura dell'integrazione

```
Flusso integrato Intune ↔ Microsoft Defender for Endpoint:

┌──────────────────────────────────────────────────────────────┐
│ Microsoft Defender XDR Portal                                 │
│                                                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ Threat & Vulnerability Management (TVM)                 │ │
│  │  ├── Scansione continua software installato              │ │
│  │  ├── Correlazione con CVE database                       │ │
│  │  ├── Risk score per dispositivo                          │ │
│  │  └── Genera "Security Recommendations"                   │ │
│  └──────────────────────┬──────────────────────────────────┘ │
│                         │ Security Task                       │
│  ┌──────────────────────▼──────────────────────────────────┐ │
│  │ Intune Portal                                           │ │
│  │  ├── Riceve Security Tasks da MDE                       │ │
│  │  ├── Mostra: vulnerabilità, dispositivi impattati,      │ │
│  │  │   remediation raccomandata                            │ │
│  │  ├── Admin azione: crea policy di remediation            │ │
│  │  │   (app update, configuration change, ecc.)           │ │
│  │  └── Stato riportato indietro a MDE                      │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### Security Tasks — flusso operativo

Quando MDE rileva una vulnerabilità software su un dispositivo gestito da Intune, può generare automaticamente un **Security Task** visibile nel portale Intune. L'amministratore Intune vede il task, comprende l'impatto e agisce direttamente senza dover passare al portale Defender.

```
Esempio di Security Task flow:

1. MDE rileva: Chrome 120.x installato su 350 dispositivi
   → CVE-2025-1234 (Critical, CVSS 9.8, RCE)

2. TVM genera Security Recommendation:
   → "Update Google Chrome to version 121.x or later"
   → Impatto: 350 dispositivi, risk score: Critical

3. Security Task appare in Intune:
   Endpoint security → Security tasks
   ├── Task: "Update Google Chrome"
   ├── Severity: Critical
   ├── Affected devices: 350
   ├── Recommendation: Deploy Chrome 121.x
   └── Actions: Accept / Reject

4. Admin accetta → crea app deployment:
   ├── Se usa Enterprise App Management (EAM):
   │   App già nel catalogo → force update automatico
   ├── Se usa Win32 app:
   │   Upload nuovo .intunewin → deploy come Required
   └── Deadline: 24-48h per criticità Critical

5. Post-remediation:
   ├── Intune riporta deployment status a MDE
   ├── MDE ri-scansiona e verifica la versione
   └── Security Task chiuso se tutti i dispositivi aggiornati
```

### Vulnerability Remediation Agent (Preview 2025)

Il **Vulnerability Remediation Agent** è uno dei quattro agenti Copilot annunciati per Intune nel maggio 2025. Questo agente automatizza il flusso Security Task → remediation, riducendo l'intervento manuale dell'amministratore per le vulnerabilità con remediation note.

```
Flusso automatizzato con Vulnerability Remediation Agent:

  MDE rileva CVE critica → Agent riceve notifica
  ↓
  Agent analizza:
  ├── Tipo di remediation disponibile (app update, config change)
  ├── Numero dispositivi impattati
  ├── Impatto operativo stimato
  └── Finestra di manutenzione disponibile
  ↓
  Agent propone piano:
  "Distribuire Chrome 121.x a 350 dispositivi.
   Piano: 10% (pilot) → wait 4h → 90% (broad).
   Rollback automatico se crash rate > 5%."
  ↓
  Admin approva → Agent esegue:
  ├── Crea app deployment o expedited quality update
  ├── Configura ring di distribuzione
  ├── Monitora il rollout in tempo reale
  └── Chiude il Security Task al completamento
```

### Device Risk Level e Conditional Access

L'integrazione più potente tra MDE e Intune è l'uso del **device risk level** nelle policy di Conditional Access. MDE assegna un livello di rischio (Clear, Low, Medium, High) a ogni dispositivo in base agli alert attivi. Intune può usare questo livello come condizione di compliance.

```
Configurazione Device Risk Level:

1. Abilitare il connettore MDE in Intune:
   Tenant admin → Connectors and tokens →
   Microsoft Defender for Endpoint → Connect

2. Creare compliance policy con risk level:
   Devices → Compliance → Create → Windows 10/11
   → Microsoft Defender for Endpoint:
     "Require the device to be at or under the machine risk score"
     → Maximum allowed: Medium (o Low per ambienti critici)

3. Creare Conditional Access policy:
   Security → Conditional Access → New policy
   → Conditions: Device must be compliant
   → Grant: Block access if not compliant

Risultato:
  - Dispositivo con alert MDE "High" → non compliant
  - Non compliant → Conditional Access blocca accesso a M365
  - Utente riceve notifica: "Dispositivo non conforme,
    contatta IT" con link a Company Portal
  - Dopo remediation → MDE aggiorna risk level → accesso ripristinato
```

### Configurazione Endpoint Detection and Response (EDR) tramite Intune

Intune è il metodo raccomandato per distribuire e configurare le impostazioni EDR di Microsoft Defender for Endpoint, sostituendo i metodi legacy (GPO, script, SCCM) con un approccio cloud-native.

```
Distribuzione MDE tramite Intune:

1. Onboarding package:
   Endpoint security → Endpoint detection and response → Create policy
   → Platform: Windows 10/11
   → Profile: Endpoint detection and response
   
   Settings:
   ├── Microsoft Defender for Endpoint client configuration package type:
   │   → Auto from connector (raccomandato)
   │   → Usa il connettore Intune-MDE per distribuzione automatica
   ├── Sample sharing: Send all samples (o Send safe samples only)
   ├── Telemetry reporting frequency: Normal (default)
   └── Assigned to: GRP-All-Managed-Devices

2. Antivirus policy (gestita da Intune, applicata a MDE):
   Endpoint security → Antivirus → Create policy
   → Microsoft Defender Antivirus
   
   Settings chiave:
   ├── Cloud-delivered protection: Enabled
   ├── Cloud-delivered protection level: High
   ├── Cloud extended timeout: 50 seconds
   ├── Real-time protection: Enabled
   ├── PUA protection: Audit mode (poi Block in produzione)
   ├── Scan all downloaded files: Yes
   └── Submission consent: Send safe samples automatically

3. Attack Surface Reduction (ASR) rules:
   Endpoint security → Attack surface reduction → Create policy
   
   Regole ASR raccomandate (in ordine di priorità):
   ├── Block executable content from email: Block
   ├── Block Office apps from creating child processes: Block
   ├── Block credential stealing from LSASS: Block
   ├── Block untrusted/unsigned processes from USB: Block
   ├── Use advanced ransomware protection: Block
   ├── Block persistence through WMI event subscription: Block
   └── Block abuse of exploited vulnerable signed drivers: Block
   
   Nota: abilitare prima in Audit mode per 2-4 settimane
   per identificare falsi positivi prima di passare a Block.

4. Firewall rules (gestite centralmente):
   Endpoint security → Firewall → Create policy
   → Microsoft Defender Firewall Rules
   
   Esempio regola:
   ├── Name: Block Telnet Outbound
   ├── Direction: Outbound
   ├── Protocol: TCP
   ├── Remote port: 23
   ├── Action: Block
   └── Profile: Domain, Private, Public
```

Questa configurazione centralizzata tramite Intune garantisce che tutti i dispositivi gestiti abbiano una baseline di sicurezza coerente, con visibilità completa nel portale Defender XDR e compliance verificabile tramite le policy Intune.

### Network Protection e Web Content Filtering via Intune

Intune consente di gestire centralmente le funzionalità di **Network Protection** e **Web Content Filtering** di MDE, estendendo il perimetro di sicurezza oltre il dispositivo verso il traffico di rete.

```
Network Protection:
  Endpoint security → Attack surface reduction → Create policy
  → Microsoft Defender Exploit Guard → Network protection
  
  Settings:
  ├── Enable network protection: Enabled (Block mode)
  │   → Blocca connessioni verso domini/IP malevoli noti
  │   → Protegge da phishing, C2 callbacks, exploit kit
  ├── Block dangerous downloads: Enabled
  └── Protected domains: aggiungere domini aziendali trusted

Web Content Filtering:
  Microsoft Defender portal → Settings → Web content filtering
  → Create policy
  
  Categorie bloccabili (esempi):
  ├── Adult content
  ├── High bandwidth (streaming non aziendale)
  ├── Legal liability (torrenti, pirateria)
  ├── Uncategorized (siti non classificati)
  └── Custom indicators: URL/dominio specifici

  L'enforcement avviene tramite il Network Protection engine
  di MDE, indipendentemente dal browser utilizzato.
  
  Reporting:
  ├── Web activity report: visualizza tentativi bloccati
  ├── Categorizzazione per utente/dispositivo/sito
  └── Export dati per analisi in SIEM/SOAR

Prerequisiti:
  - MDE onboarded (Plan 2)
  - Network Protection abilitato (come sopra)
  - SmartScreen abilitato per Edge
  - Per browser non-Microsoft: Network Protection opera a livello rete
    (intercetta a prescindere dal browser)
```

---

## Best Practices

**Iniziare con Report-Only per Conditional Access:** Ogni nuova policy di Conditional Access deve essere creata in modalità Report-Only per almeno 1-2 settimane, analizzando i sign-in logs per identificare impatti inattesi prima dell'enforcement.

**Usare gruppi dinamici per gli assignment:** Sfruttare i gruppi dinamici di Azure AD basati su attributi del dispositivo (OS version, enrollment profile, compliance state) per automatizzare l'assegnamento di policy e applicazioni.

**Implementare update rings graduali:** Non distribuire mai gli aggiornamenti a tutti i dispositivi contemporaneamente. Usare almeno 3 ring (Pilot → Early Adopters → Broad) con deferrimento crescente.

**Configurare l'ESP per Autopilot:** L'Enrollment Status Page è critica per garantire che i dispositivi siano completamente configurati prima che l'utente inizi a lavorare. Senza ESP, l'utente potrebbe accedere a un desktop senza policy di sicurezza applicate.

**Mantenere break glass accounts:** Avere almeno 2 account di emergenza esclusi da tutte le policy di Conditional Access, con password complesse memorizzate in modo sicuro e con monitoraggio degli accessi.

**Non sovraccaricare i dispositivi con troppe policy:** Ogni policy e ogni profilo aggiungono complessità e potenziali conflitti. Consolidare le configurazioni dove possibile e documentare ogni policy creata.

**Testare le applicazioni Win32 accuratamente:** Validare install command, uninstall command e detection rules in un ambiente di test prima del deployment in produzione. Detection rules errate causano reinstallazioni ripetute o mancato rilevamento.

**Monitorare la compliance continuamente:** Configurare alert per dispositivi che diventano non-compliant e implementare azioni automatiche (notifica utente, blocco dopo grace period, wipe selettivo dopo periodo esteso).

**Implementare Endpoint Analytics:** Monitorare metriche come il tempo di avvio, i crash delle applicazioni e i riavvii con errori stop per identificare proattivamente i dispositivi problematici prima che gli utenti li segnalino.

**Pianificare la strategia di App Protection Policy:** Per i dispositivi BYOD non gestiti, le App Protection Policy sono l'unico strumento per proteggere i dati aziendali. Configurare policy MAM che richiedano PIN, impediscano il copia-incolla verso app personali, cifrino i dati dell'app e permettano il wipe selettivo.

**Documentare e versionare le configurazioni:** Trattare le policy e i profili Intune come infrastruttura-as-code. Esportare regolarmente le configurazioni tramite Graph API e mantenerle in un repository Git per tracciare le modifiche nel tempo.

**Utilizzare Scope Tags per la segmentazione:** In organizzazioni con più sedi o dipartimenti IT, usare Scope Tags per limitare la visibilità e la gestione di dispositivi, policy e app ai soli amministratori autorizzati per quel segmento.

**Implementare filtri di assegnazione:** Usare i filtri (Intune Filters) per raffinare le assegnazioni senza creare gruppi complessi. I filtri possono basarsi su proprietà del dispositivo (manufacturer, model, OS version, enrollment profile).

---

## Troubleshooting

### Problema: Dispositivo Non Si Registra in Intune (Enrollment Fallisce)

**Sintomi**: L'utente tenta di registrare il dispositivo ma riceve errori durante il processo. Il dispositivo non appare nel portale Intune.

**Causa**: Le cause comuni includono: l'utente non ha una licenza Intune assegnata, il limite di dispositivi per utente è raggiunto, l'auto-enrollment MDM non è configurato, problemi di connettività ai servizi Microsoft, o il dispositivo non soddisfa i requisiti di versione OS.

**Soluzione**:

```powershell
# Verificare la licenza dell'utente in Azure AD
# Portal: Azure AD → Users → [utente] → Licenses
# Deve avere: Microsoft Intune (o suite che include Intune: M365 E3/E5, EMS E3/E5)

# Verificare il limite dispositivi
# Portal: Intune → Devices → Enroll devices → Device enrollment restrictions
# Default limit: 15 dispositivi per utente

# Verificare la connettività agli endpoint Intune
$endpoints = @(
    "https://manage.microsoft.com"
    "https://enrollment.manage.microsoft.com"
    "https://portal.manage.microsoft.com"
    "https://login.microsoftonline.com"
    "https://graph.microsoft.com"
)

foreach ($url in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10
        Write-Output "OK: $url ($($response.StatusCode))"
    } catch {
        Write-Warning "FAIL: $url - $($_.Exception.Message)"
    }
}

# Raccogliere i log MDM diagnostici
mdmdiagnosticstool.exe -area DeviceEnrollment -zip "C:\Temp\MDMLogs.zip"

# Verificare i log enrollment nel Event Viewer
Get-WinEvent -LogName "Microsoft-Windows-DeviceManagement-Enterprise-Diagnostics-Provider/Admin" `
    -MaxEvents 50 | Select-Object TimeCreated, Id, Message | Format-Table -Wrap

# Errori comuni:
# 0x80180014 = Limite dispositivi raggiunto
# 0x80180018 = Utente non autorizzato per l'enrollment
# 0x801c0003 = Errore di discovery del servizio MDM
# 0x80192ee2 = Errore di connettività (proxy/firewall)
```

### Problema: Configuration Profile Non Si Applica

**Sintomi**: Un profilo di configurazione è assegnato al dispositivo ma le impostazioni non hanno effetto. Nel portale Intune, il profilo mostra stato "Pending" o "Error".

**Causa**: Conflitto con un'altra policy (GPO locale o altro profilo Intune), il dispositivo non ha fatto sync recente, il profilo è assegnato a un gruppo che non include il dispositivo, o l'impostazione non è supportata dalla versione del sistema operativo.

**Soluzione**:

```powershell
# Forzare un sync con Intune
$enrollmentPath = "HKLM:\SOFTWARE\Microsoft\Enrollments"
$enrollmentId = (Get-ChildItem $enrollmentPath |
    Where-Object { (Get-ItemProperty $_.PSPath).ProviderID -eq "MS DM Server" }).PSChildName

if ($enrollmentId) {
    $taskPath = "\Microsoft\Windows\EnterpriseMgmt\$enrollmentId\"
    Get-ScheduledTask -TaskPath $taskPath | Where-Object { $_.TaskName -like "*Schedule*" } |
        Start-ScheduledTask
    Write-Output "Sync avviato per enrollment: $enrollmentId"
}

# Raccogliere diagnostica completa
mdmdiagnosticstool.exe -area DeviceProvisioning;DeviceEnrollment;Autopilot `
    -zip "C:\Temp\MDMDiag.zip"

# Verificare i conflitti tra policy nel portale Intune:
# Devices → [dispositivo] → Device configuration → Per-setting status
# I conflitti sono evidenziati con icona di warning

# Verificare la policy applicata localmente via registry
Get-ChildItem "HKLM:\SOFTWARE\Microsoft\PolicyManager\current\device" -Recurse |
    Get-ItemProperty | Where-Object { $_.PSPath -match "firewall|password|bitlocker" }
```

### Problema: Applicazione Win32 Installata ma Rilevata come Non Installata

**Sintomi**: L'applicazione è fisicamente installata sul dispositivo, ma Intune continua a tentare la reinstallazione perché la detection rule fallisce.

**Causa**: La detection rule non corrisponde allo stato reale dell'installazione. Esempi: il percorso del file è diverso (x86 vs x64), la versione nel registry non corrisponde, il file di detection è stato spostato o rinominato.

**Soluzione**:

```powershell
# Verificare localmente cosa cerca la detection rule
# Se detection basata su file:
Test-Path "C:\Program Files\App\app.exe"
(Get-Item "C:\Program Files\App\app.exe").VersionInfo.FileVersion

# Se detection basata su registry:
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*" |
    Where-Object DisplayName -like "*NomeApp*" |
    Select-Object DisplayName, DisplayVersion, InstallLocation, UninstallString

# Verificare i log di Intune Management Extension
Get-Content "C:\ProgramData\Microsoft\IntuneManagementExtension\Logs\IntuneManagementExtension.log" -Tail 200 |
    Select-String "detection|install|error" -CaseSensitive:$false

# Verificare anche nel registro x86 (per app 32-bit su OS 64-bit)
Get-ItemProperty "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*" |
    Where-Object DisplayName -like "*NomeApp*" |
    Select-Object DisplayName, DisplayVersion
```

### Problema: Autopilot ESP Bloccato al 100%

**Sintomi**: L'Enrollment Status Page rimane bloccata al progresso o mostra "Identifying..." per un tempo prolungato durante il provisioning Autopilot.

**Causa**: Un'applicazione nella lista delle blocking apps fallisce l'installazione, il dispositivo non riesce a contattare i servizi cloud, oppure un profilo di configurazione non si applica.

**Soluzione**:

```powershell
# Raccogliere i log ESP
mdmdiagnosticstool.exe -area Autopilot -zip "C:\Temp\AutopilotDiag.zip"

# Verificare le app bloccanti
# Nel portale Intune: Devices → Enroll devices → Enrollment Status Page
# Verificare la lista delle "Blocking apps"
# Rimuovere temporaneamente le app problematiche dalla lista

# Verificare il timeout ESP
# Se il timeout è raggiunto, l'utente vede un messaggio di errore
# Aumentare il timeout se le app richiedono più tempo

# Log utili durante ESP:
# %ProgramData%\Microsoft\IntuneManagementExtension\Logs\
# Event Log: Microsoft-Windows-DeviceManagement-Enterprise-Diagnostics-Provider
```

---

## Domande e Risposte

**D: Qual è la differenza tra MDM e MAM?**
R: MDM (Mobile Device Management) gestisce l'intero dispositivo: può applicare policy, distribuire app, forzare cifratura e fare wipe completo. MAM (Mobile Application Management) gestisce solo le applicazioni specifiche: protegge i dati dentro le app senza gestire il dispositivo. MDM richiede enrollment, MAM no. In scenari BYOD, MAM-only è spesso preferibile per rispettare la privacy dell'utente.

**D: Posso gestire dispositivi personali senza enrollment?**
R: Sì, tramite App Protection Policies (MAM without enrollment). L'utente installa le app aziendali (Outlook, Teams) e le APP proteggono i dati dentro quelle app senza che il dispositivo sia registrato in Intune. Il reparto IT non vede e non può gestire il dispositivo, ma può fare wipe selettivo dei dati aziendali dentro le app.

**D: Come funziona il Conditional Access con Intune?**
R: Conditional Access valuta le condizioni di accesso (utente, dispositivo, app, posizione, rischio) e applica controlli (MFA, require compliant device, block). Intune fornisce lo stato di compliance del dispositivo ad Azure AD, che lo usa come segnale nelle policy di Conditional Access. Un dispositivo non-compliant in Intune viene bloccato dall'accesso se una policy CA lo richiede.

**D: Cosa succede se un dispositivo perde la connettività con Intune per settimane?**
R: Il dispositivo mantiene le policy e le app già ricevute. Al prossimo check-in riceverà tutti gli aggiornamenti accumulati. Tuttavia, il Conditional Access potrebbe bloccarlo se la policy richiede un last sync recente. Configurare azioni di non-compliance con grace period per gestire questi scenari.

**D: Come gestisco gli aggiornamenti Windows senza WSUS?**
R: Con Windows Update for Business (WUfB) gestito tramite Intune. Creare Update Rings con diversi livelli di deferrimento (Pilot 0 days, Early 7 days, Broad 14 days). WUfB scarica gli aggiornamenti direttamente da Windows Update / Delivery Optimization, senza server WSUS.

**D: Qual è la differenza tra co-management e tenant attach?**
R: Co-management gestisce i dispositivi con entrambi SCCM e Intune simultaneamente, con workload divisi tra i due. Tenant attach è solo visibilità: i dispositivi SCCM appaiono nel portale Intune per operazioni remote (CMPivot, scripts), ma i workload restano interamente su SCCM. Co-management richiede MDM enrollment; tenant attach no.

**D: Come gestisco le app Win32 che richiedono reboot?**
R: Configurare il "Device restart behavior" nella definizione dell'app Win32. Le opzioni sono: Determine behavior based on return codes (usa i codici di ritorno MSI standard), App install may force restart (mostra notifica all'utente), No specific action (nessun reboot), Intune will force a mandatory restart (riavvio forzato dopo un periodo).

**D: Come posso testare una Compliance Policy prima di applicarla in produzione?**
R: Creare un gruppo pilota di dispositivi di test. Assegnare la compliance policy solo a quel gruppo. Monitorare i risultati per 1-2 settimane nel portale Intune (Devices → Monitor → Setting compliance). Solo dopo la validazione, assegnare al gruppo produzione. Per il Conditional Access correlato, usare Report-Only mode.

**D: Come funzionano gli Scope Tags?**
R: Gli Scope Tags segmentano l'ambiente Intune per delegare l'amministrazione. Ogni oggetto (dispositivo, policy, app) può avere uno o più scope tags. Gli amministratori vedono solo gli oggetti che hanno i loro scope tags assegnati. Esempio: IT Roma vede solo i dispositivi con tag "Roma", IT Milano vede solo "Milano". Utile in organizzazioni distribuite o multi-tenant.

**D: Come gestisco i certificati sui dispositivi?**
R: Intune supporta diverse tipologie di profili certificato: SCEP (Simple Certificate Enrollment Protocol) per certificati basati su CA enterprise, PKCS (Public Key Cryptography Standards) per certificati importati, PKCS imported per certificati pre-generati. I certificati sono utilizzati per autenticazione WiFi, VPN, email e web. Richiedono un Intune Certificate Connector installato on-premises.

---

## Esercizi Pratici

### Esercizio 1: Configurare una Compliance Policy Base
Creare una compliance policy per Windows che richieda:
- BitLocker attivo
- Firewall attivo
- Antivirus aggiornato (non più di 3 giorni di ritardo)
- Password di almeno 8 caratteri alfanumerici
- OS version minima: Windows 10 21H2
- Grace period di 72 ore prima del blocco
- Email di notifica all'utente per non-compliance

**Verifica**: Assegnare la policy a un dispositivo di test e verificare che tutti i controlli passino nel portale Intune → Devices → [dispositivo] → Device compliance.

### Esercizio 2: Creare e Distribuire un'App Win32
1. Scaricare l'installer di Notepad++ (MSI o EXE)
2. Usare il Win32 Content Prep Tool per creare il file .intunewin
3. Caricare l'app in Intune con:
   - Install command corretto
   - Uninstall command corretto
   - Detection rule basata su file (verificare che l'exe esista in Program Files)
4. Assegnare come "Available" a un gruppo di test
5. Verificare l'installazione dal Company Portal del dispositivo di test

**Verifica**: Controllare che la detection rule funzioni verificando lo stato dell'app nel portale Intune e nei log dell'IME.

### Esercizio 3: Implementare un Proactive Remediation
Scrivere un detection script e un remediation script per:
- Detection: verificare se il servizio Windows Search è in esecuzione e sta consumando più di 200 MB di memoria
- Remediation: riavviare il servizio Windows Search se il detection rileva il problema

**Verifica**: Creare il remediation in Intune (Devices → Remediations → Create), assegnarlo a un gruppo, e verificare l'esecuzione nel portale Intune.

### Esercizio 4: Configurare Autopilot per un Dispositivo di Test
1. Su un dispositivo Windows di test, raccogliere l'hardware hash con `Get-WindowsAutopilotInfo`
2. Importare l'hash nel portale Intune
3. Creare un Autopilot Deployment Profile (User-Driven)
4. Configurare l'Enrollment Status Page
5. Fare reset del dispositivo e verificare il flusso Autopilot completo

**Verifica**: Il dispositivo deve completare il provisioning Autopilot, mostrare l'ESP con il progresso, e alla fine l'utente deve poter accedere con le policy e le app configurate.

### Esercizio 5: Creare un Report Automatizzato con Graph API
1. Creare un'App Registration in Azure AD con i permessi DeviceManagementManagedDevices.Read.All
2. Scrivere uno script PowerShell che:
   - Si autentichi con Graph API
   - Recuperi tutti i dispositivi gestiti
   - Calcoli: totale dispositivi, compliance rate, dispositivi stale (>7 giorni senza sync)
   - Esporti il risultato in CSV
3. Configurare uno Scheduled Task per eseguire lo script quotidianamente

**Verifica**: Eseguire lo script e verificare che il CSV contenga dati accurati confrontandoli con il portale Intune.

### Esercizio 6: Implementare MAM per BYOD
1. Creare un'App Protection Policy per iOS che:
   - Richieda un PIN di 6 cifre
   - Blocchi il copia-incolla verso app non gestite
   - Blocchi il backup su iCloud
   - Richieda un OS minimo di iOS 16
   - Configuri un wipe dei dati dopo 5 tentativi di PIN falliti
2. Creare una Conditional Access Policy che richieda APP per accedere a Exchange Online da iOS

**Verifica**: Su un dispositivo iOS personale (non enrolled), installare Outlook e verificare che l'APP si applichi (PIN richiesto, copia-incolla bloccato verso app personali).

---

## Riferimenti

- Microsoft Docs: Microsoft Intune Documentation — https://learn.microsoft.com/en-us/mem/intune/
- Microsoft Docs: Windows Autopilot — https://learn.microsoft.com/en-us/autopilot/
- Microsoft Docs: Conditional Access — https://learn.microsoft.com/en-us/entra/identity/conditional-access/
- Microsoft Docs: Windows Update for Business — https://learn.microsoft.com/en-us/windows/deployment/update/waas-manage-updates-wufb
- Microsoft Docs: Endpoint Analytics — https://learn.microsoft.com/en-us/mem/analytics/
- Microsoft Docs: App Protection Policies — https://learn.microsoft.com/en-us/mem/intune/apps/app-protection-policies
- Microsoft Docs: Win32 App Management — https://learn.microsoft.com/en-us/mem/intune/apps/apps-win32-app-management
- Microsoft Docs: Co-management — https://learn.microsoft.com/en-us/mem/configmgr/comanage/overview
- Microsoft Docs: Tenant Attach — https://learn.microsoft.com/en-us/mem/configmgr/tenant-attach/
- Microsoft Docs: Intune Graph API — https://learn.microsoft.com/en-us/graph/api/resources/intune-graph-overview
- Microsoft Docs: Windows Autopatch — https://learn.microsoft.com/en-us/windows/deployment/windows-autopatch/

---

## Auto-valutazione

<details>
<summary>1. Qual è la differenza tra MDM enrollment e MAM-only, e quando si usa ciascuno?</summary>

MDM enrollment registra l'intero dispositivo in Intune: l'organizzazione può gestire configurazioni, compliance, wipe remoto e distribuzione app. Si usa per dispositivi corporate. MAM-only (MAM without enrollment) protegge solo le app aziendali senza registrare il dispositivo — ideale per BYOD dove l'utente non vuole cedere il controllo del proprio device.
</details>

<details>
<summary>2. Come funziona il ciclo Compliance Policy → Conditional Access?</summary>

Intune valuta periodicamente le compliance policies sui dispositivi (ogni 8 ore + check-in). Se un dispositivo risulta non-conforme, Entra ID Conditional Access può bloccare l'accesso a risorse come Exchange Online, SharePoint o Teams. Il dispositivo deve tornare conforme per riottenere l'accesso. La grace period consente un periodo di tolleranza prima del blocco.
</details>

<details>
<summary>3. Quali sono i passaggi per distribuire un'app Win32 tramite Intune?</summary>

1) Preparare l'installer con il Win32 Content Prep Tool per generare il file `.intunewin`. 2) Caricare in Intune specificando install command, uninstall command e detection rules (file, registry o script). 3) Configurare requirement rules (OS version, disk space). 4) Assegnare a gruppi come Required, Available o Uninstall. 5) L'Intune Management Extension (IME) sul client esegue l'installazione e riporta lo stato.
</details>

<details>
<summary>4. Cosa distingue il co-management dal tenant attach in SCCM/MECM?</summary>

Il co-management richiede che i dispositivi siano registrati sia in SCCM che in Intune, e permette di spostare gradualmente i workload (compliance, updates, endpoint protection) da SCCM a Intune. Il tenant attach è più leggero: collega il tenant SCCM al cloud Microsoft senza dual-enrollment, permettendo di vedere i dispositivi SCCM nel portale Intune e di eseguire azioni remote, ma senza spostare workload.
</details>

<details>
<summary>5. Come funzionano le Proactive Remediations di Intune?</summary>

Sono composte da due script PowerShell: un detection script che verifica una condizione (es. servizio in stato errato, file di configurazione mancante) e un remediation script che corregge il problema se rilevato. Intune li esegue periodicamente sui dispositivi target. Il portale mostra i risultati: quanti dispositivi hanno il problema, quanti sono stati rimediati, e quanti hanno fallito.
</details>

<details>
<summary>6. Qual è il flusso completo di Windows Autopilot user-driven?</summary>

1) L'hardware hash del dispositivo viene pre-registrato in Intune. 2) L'utente accende il dispositivo e si collega a internet. 3) Windows riconosce il dispositivo come Autopilot e mostra la pagina di login dell'organizzazione. 4) L'utente accede con le credenziali Entra ID. 5) L'Enrollment Status Page (ESP) mostra il progresso: enrollment, compliance check, app installation. 6) Al completamento, l'utente ha il desktop con tutte le policy e app configurate.
</details>

<details>
<summary>7. Quando si usa OMA-URI nei Configuration Profiles rispetto alle opzioni native?</summary>

I Configuration Profiles nativi di Intune coprono le impostazioni più comuni con UI guidata. OMA-URI si usa per impostazioni avanzate non ancora esposte nell'interfaccia nativa: CSP (Configuration Service Provider) specifici, registry-backed settings, o configurazioni di vendor terzi. È utile anche per applicare impostazioni da ADMX templates importati.
</details>

---

## Letture primarie consigliate

- Microsoft Learn — Intune Training Modules — https://learn.microsoft.com/en-us/training/browse/?products=mem-intune
- Microsoft Learn — Conditional Access Design Guide — https://learn.microsoft.com/en-us/entra/identity/conditional-access/plan-conditional-access
- Microsoft Docs — Win32 App Troubleshooting — https://learn.microsoft.com/en-us/mem/intune/apps/troubleshoot-app-install
- Microsoft Docs — Proactive Remediations — https://learn.microsoft.com/en-us/mem/intune/fundamentals/remediations
- Microsoft Docs — Configuration Service Providers Reference — https://learn.microsoft.com/en-us/windows/client-management/mdm/

---

## Collegamenti incrociati

- [12-endpoint-management.md](12-endpoint-management.md) — Fondamenti endpoint management e confronto strumenti
- [13-azure-ad-identita-ibrida.md](13-azure-ad-identita-ibrida.md) — Entra ID, identità ibrida, sincronizzazione
- [32-intune-mdm-mam.md](32-intune-mdm-mam.md) — Approfondimento MDM vs MAM, App Protection Policies, Autopilot
- [24-windows-defender-endpoint-security.md](24-windows-defender-endpoint-security.md) — Defender for Endpoint, integrazione con Intune compliance
- [30-identita-ibrida-azure-ad-dettaglio.md](30-identita-ibrida-azure-ad-dettaglio.md) — Conditional Access avanzato, hybrid join, device trust

---

## Glossario locale

| Termine | Definizione |
|---------|------------|
| **Compliance Policy** | Policy Intune che definisce i requisiti minimi di sicurezza per un dispositivo (BitLocker, antivirus, OS version) |
| **Conditional Access** | Meccanismo Entra ID che concede o blocca l'accesso in base a condizioni su utente, dispositivo e rischio |
| **Configuration Profile** | Profilo Intune che applica impostazioni (Wi-Fi, VPN, restrizioni, certificati) ai dispositivi gestiti |
| **Co-management** | Gestione parallela SCCM + Intune con migrazione graduale dei workload verso il cloud |
| **ESP** | Enrollment Status Page — pagina che mostra il progresso del provisioning Autopilot |
| **IME** | Intune Management Extension — agent sul client Windows per esecuzione script e installazione app Win32 |
| **OMA-URI** | Open Mobile Alliance Uniform Resource Identifier — formato per configurazioni MDM avanzate via CSP |
| **Proactive Remediation** | Coppia detection/remediation script eseguita periodicamente per rilevare e correggere problemi |
| **Tenant Attach** | Collegamento del tenant SCCM al cloud per visibilità e azioni remote senza dual-enrollment |
| **Win32 Content Prep Tool** | Utility Microsoft per pacchettizzare installer in formato `.intunewin` per distribuzione Intune |
- Microsoft Docs: Endpoint Privilege Management — https://learn.microsoft.com/en-us/mem/intune/protect/epm-overview
