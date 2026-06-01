# Intune MDM/MAM — Modern Endpoint Management

> **Modulo 32** · **Aggiornamento:** 2026-05-23

> **Modulo del corso:** Amministrazione Windows enterprise
> **Prerequisiti:** [26-intune-gestione-moderna.md](26-intune-gestione-moderna.md), [13-azure-ad-identita-ibrida.md](13-azure-ad-identita-ibrida.md), [24-windows-defender-endpoint-security.md](24-windows-defender-endpoint-security.md)
> **Obiettivi di apprendimento:**
> 1. Distinguere scenari MDM (device ownership) e MAM (BYOD) e scegliere la strategia corretta
> 2. Configurare App Protection Policies con data loss prevention e PIN enforcement
> 3. Progettare Configuration Profiles con OMA-URI, ADMX ingestion e Security Baselines
> 4. Implementare il flusso Autopilot end-to-end con Enrollment Status Page
> 5. Utilizzare Endpoint Privilege Management per elevazione JIT senza admin permanente
> **Tempo stimato:** lettura 80 min · lab 150 min
> **Livello:** proficient
> **Ultimo aggiornamento:** 2026-05-23

## Idee guida

1. **MDM (Mobile Device Management) controlla l'intero dispositivo — ownership aziendale.**
2. **MAM (Mobile App Management) controlla solo le app aziendali — scenario BYOD.**
3. **Intune si integra con Conditional Access, Defender for Endpoint e Entra ID.**
4. **Compliance Policy + remediation automatica = postura di sicurezza continua.**
5. **Endpoint Privilege Management per elevazione JIT (just-in-time) senza admin permanente.**

## Mappa concettuale

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     MICROSOFT INTUNE — ARCHITETTURA                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐  │
│  │   ENROLLMENT     │    │  POLICY ENGINE   │    │   APP DELIVERY   │  │
│  │                  │    │                  │    │                  │  │
│  │ • Autopilot      │───▶│ • Compliance     │───▶│ • Win32 (.intune │  │
│  │ • Auto-enrollment│    │ • Configuration  │    │   win)           │  │
│  │ • Bulk (PPKG)    │    │ • Security       │    │ • M365 Apps      │  │
│  │ • Company Portal │    │   Baselines      │    │ • Store apps     │  │
│  │ • DEP/ADE (Apple)│    │ • Custom (OMA)   │    │ • LOB            │  │
│  │ • Android Ent.   │    │ • ADMX ingestion │    │ • MSIX App Attach│  │
│  └──────────────────┘    └────────┬─────────┘    └──────────────────┘  │
│                                   │                                     │
│          ┌────────────────────────┼────────────────────────┐            │
│          ▼                        ▼                        ▼            │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐      │
│  │  CONDITIONAL │    │    ENDPOINT      │    │   REPORTING &    │      │
│  │   ACCESS     │    │   SECURITY       │    │   ANALYTICS      │      │
│  │              │    │                  │    │                  │      │
│  │ Device-based │    │ • Defender       │    │ • Endpoint       │      │
│  │ App-based    │    │ • EPM (JIT)      │    │   Analytics      │      │
│  │ Risk-based   │    │ • LAPS           │    │ • Proactive      │      │
│  │              │    │ • WDAC/AppLocker │    │   Remediations   │      │
│  └──────┬───────┘    └──────────────────┘    │ • Graph API      │      │
│         │                                     └──────────────────┘      │
│         ▼                                                               │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                         ENTRA ID                                 │   │
│  │     Identity ←→ Device Registration ←→ Conditional Access        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────┐   ┌─────────────────┐   ┌──────────────────────────┐  │
│  │   MDM       │   │      MAM        │   │    CO-MANAGEMENT         │  │
│  │ Device-level│   │ App-level only  │   │ ConfigMgr + Intune       │  │
│  │ Full control│   │ BYOD scenario   │   │ Workload slider          │  │
│  └─────────────┘   └─────────────────┘   └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## Indice

- [Architettura Intune](#architettura-intune)
- [Licensing e Prerequisiti](#licensing-e-prerequisiti)
- [Enrollment MDM — Metodi di Registrazione](#enrollment-mdm--metodi-di-registrazione)
- [Device Compliance Policies](#device-compliance-policies)
- [Conditional Access Integration](#conditional-access-integration)
- [Configuration Profiles](#configuration-profiles)
- [App Deployment — Distribuzione Applicazioni](#app-deployment--distribuzione-applicazioni)
- [App Protection Policies (MAM)](#app-protection-policies-mam)
- [Windows Autopilot](#windows-autopilot)
- [Co-Management con Configuration Manager](#co-management-con-configuration-manager)
- [Endpoint Analytics](#endpoint-analytics)
- [Remote Actions](#remote-actions)
- [Custom Compliance Scripts](#custom-compliance-scripts)
- [PowerShell Scripts Deployment](#powershell-scripts-deployment)
- [Endpoint Privilege Management](#endpoint-privilege-management)
- [Windows Update for Business](#windows-update-for-business)
- [Windows LAPS via Intune](#windows-laps-via-intune)
- [Device Categories, Scope Tags e Filters](#device-categories-scope-tags-e-filters)
- [DFCI — Device Firmware Configuration Interface](#dfci--device-firmware-configuration-interface)
- [Intune Reporting e Automazione Graph API](#intune-reporting-e-automazione-graph-api)
- [Sicurezza e Best Practices](#sicurezza-e-best-practices)
- [Microsoft Intune Suite — Funzionalità Avanzate](#microsoft-intune-suite--funzionalità-avanzate)
- [Microsoft Cloud PKI](#microsoft-cloud-pki)
- [Intune e Defender for Endpoint — Integrazione Avanzata](#intune-e-defender-for-endpoint--integrazione-avanzata)
- [Windows Autopatch](#windows-autopatch)
- [Tenant Attach — Approfondimento](#tenant-attach--approfondimento)
- [Strumenti di Troubleshooting Avanzati](#strumenti-di-troubleshooting-avanzati)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Esercizi](#esercizi)
- [Letture](#letture)
- [Glossario](#glossario)

---

## Architettura Intune

### Panoramica del Servizio

Microsoft Intune è un servizio cloud-native di Unified Endpoint Management (UEM) parte della suite Microsoft Intune (ex Endpoint Manager). Intune gestisce dispositivi Windows, macOS, iOS/iPadOS, Android e Linux da un unico portale: l'Intune admin center (`intune.microsoft.com`).

L'architettura è composta da:

| Componente | Ruolo |
|---|---|
| **Intune Service** | Motore cloud, policy engine, app distribution |
| **Entra ID (Azure AD)** | Identity provider, device registration, Conditional Access |
| **Microsoft Graph API** | API REST per automazione e integrazione |
| **Intune Management Extension (IME)** | Agent Windows per script PowerShell e Win32 app |
| **Company Portal** | App utente per enrollment, app catalog, self-service |
| **Intune Connector** | Bridge per SCEP/PKCS certificate, Exchange on-premises |

### Flusso di Comunicazione

```
Device → Intune Service (HTTPS 443) → Entra ID
                ↕                        ↕
        Graph API / Reporting     Conditional Access
                ↕
     Intune Management Extension (IME)
        ↕              ↕
   Win32 Apps     PowerShell Scripts
```

Il dispositivo comunica con Intune tramite HTTPS (porta 443) verso gli endpoint Microsoft. Non è necessaria una VPN: il protocollo è progettato per funzionare attraverso NAT e firewall aziendali, purché il traffico HTTPS in uscita verso `*.manage.microsoft.com`, `*.microsoftonline.com` e gli endpoint correlati sia consentito.

### Ciclo di Check-in

I dispositivi effettuano check-in periodici con Intune per ricevere policy aggiornate:

| Piattaforma | Intervallo Standard | Dopo enrollment |
|---|---|---|
| Windows | Ogni 8 ore | Ogni 15 minuti (prime 24h) |
| iOS/iPadOS | Ogni 8 ore | Ogni 15 minuti (prime 24h) |
| Android | Ogni 8 ore | Ogni 15 minuti (prime 24h) |
| macOS | Ogni 8 ore | Ogni 15 minuti (prime 24h) |

Il check-in può essere forzato manualmente dall'admin (azione `Sync`) o dall'utente tramite Company Portal.

### Intune Management Extension (IME)

L'IME è un agent installato automaticamente su dispositivi Windows 10/11 gestiti da Intune (Entra ID joined o Hybrid Entra ID joined). Funziona come broker per:

- Esecuzione di script PowerShell
- Installazione di app Win32 (formato `.intunewin`)
- Custom compliance script evaluation
- Proactive remediations (Endpoint Analytics)
- Win32 app detection rules

```powershell
# Percorso dell'IME sul dispositivo
# C:\Program Files (x86)\Microsoft Intune Management Extension\

# Log dell'IME
# C:\ProgramData\Microsoft\IntuneManagementExtension\Logs\IntuneManagementExtension.log

# Verifica servizio IME
Get-Service -Name IntuneManagementExtension

# Riavvio forzato dell'IME per troubleshooting
Restart-Service -Name IntuneManagementExtension -Force
```

### Tenant e Multi-Tenant

Ogni tenant Intune è associato a un singolo tenant Entra ID. Non è possibile gestire dispositivi da più tenant Intune contemporaneamente sullo stesso dispositivo. Per scenari multi-tenant (acquisizioni, partner), si utilizzano:

- **Azure Lighthouse** per delega amministrativa
- **Multi-tenant management** nel portale Microsoft 365
- **GDAP (Granular Delegated Admin Privileges)** per MSP/partner

---

## Licensing e Prerequisiti

### Licenze Richieste

| Licenza | MDM | MAM | Autopilot | Endpoint Analytics | EPM |
|---|---|---|---|---|---|
| **Intune Plan 1** (incluso in M365 E3/E5, EMS E3) | Si | Si | Si | Base | No |
| **Intune Plan 2** (add-on) | Si | Si | Si | Avanzato | No |
| **Intune Suite** (add-on premium) | Si | Si | Si | Completo | Si |
| **M365 Business Premium** | Si | Si | Si | Base | No |

### Prerequisiti Infrastrutturali

1. **Tenant Entra ID** con dominio personalizzato verificato
2. **DNS CNAME** per auto-discovery enrollment:
   - `EnterpriseEnrollment.dominio.com` → `EnterpriseEnrollment-s.manage.microsoft.com`
   - `EnterpriseRegistration.dominio.com` → `EnterpriseRegistration.windows.net`
3. **MDM Authority** impostata su Intune (non Configuration Manager standalone)
4. **Licenze assegnate** agli utenti nel portale Microsoft 365
5. **Firewall** con traffico HTTPS in uscita verso endpoint Microsoft

```powershell
# Verifica DNS CNAME per enrollment
Resolve-DnsName -Name "EnterpriseEnrollment.contoso.com" -Type CNAME
Resolve-DnsName -Name "EnterpriseRegistration.contoso.com" -Type CNAME

# Test connettività verso endpoint Intune
Test-NetConnection -ComputerName "manage.microsoft.com" -Port 443
Test-NetConnection -ComputerName "enrollment.manage.microsoft.com" -Port 443
```

### Ruoli RBAC in Intune

Intune supporta Role-Based Access Control granulare:

| Ruolo Built-in | Permessi |
|---|---|
| **Intune Administrator** | Accesso completo |
| **Help Desk Operator** | Remote actions, view devices, basic troubleshooting |
| **Application Manager** | Gestione app e policy app |
| **Endpoint Security Manager** | Compliance, Conditional Access, security baselines |
| **Read Only Operator** | Sola lettura su tutti gli oggetti |
| **School Administrator** | Gestione dispositivi education |

```powershell
# Creazione ruolo custom via Graph API
$params = @{
    displayName = "Deployment Technician"
    description = "Può gestire enrollment e device configuration"
    permissions = @(
        @{ actions = @(
            "Microsoft.Intune_Organization_Read",
            "Microsoft.Intune_Devices_Read",
            "Microsoft.Intune_Devices_Update",
            "Microsoft.Intune_DeviceConfigurations_Read",
            "Microsoft.Intune_DeviceConfigurations_Assign"
        )}
    )
    isBuiltIn = $false
}
```

---

## Enrollment MDM — Metodi di Registrazione

### Panoramica dei Metodi

| Metodo | Piattaforma | Ownership | Interazione Utente | Complessità |
|---|---|---|---|---|
| **Auto-enrollment (GPO/MDM)** | Windows | Corporate | Minima | Bassa |
| **Windows Autopilot** | Windows | Corporate | Minima | Media |
| **Bulk enrollment (provisioning package)** | Windows | Corporate | Nessuna | Media |
| **Company Portal** | Tutte | BYOD/Corporate | Richiesta | Bassa |
| **Apple DEP/ADE** | iOS/macOS | Corporate | Minima | Media |
| **Android Enterprise** | Android | Corporate/BYOD | Variabile | Media |
| **Co-management** | Windows | Corporate | Nessuna | Alta |

### Auto-Enrollment via GPO (Hybrid Entra ID Join)

Per dispositivi Windows già joinati ad Active Directory on-premises con Hybrid Entra ID Join configurato:

```
Computer Configuration → Administrative Templates → Windows Components →
  MDM → Enable automatic MDM enrollment using default Azure AD credentials
```

```powershell
# Verifica via registry
Get-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\CurrentVersion\MDM" `
    -Name "AutoEnrollMDM" -ErrorAction SilentlyContinue

# Valore atteso: AutoEnrollMDM = 1

# Trigger manuale dell'enrollment scheduled task
$task = Get-ScheduledTask -TaskPath "\Microsoft\Windows\EnterpriseMgmt\*" `
    -TaskName "Schedule #3 created by enrollment client"
Start-ScheduledTask -InputObject $task

# Verifica enrollment status
Get-ChildItem -Path "HKLM:\SOFTWARE\Microsoft\Enrollments\" | ForEach-Object {
    $props = Get-ItemProperty -Path $_.PSPath
    [PSCustomObject]@{
        EnrollmentID = $_.PSChildName
        UPN          = $props.UPN
        ProviderID   = $props.ProviderId
    }
}
```

### Auto-Enrollment via Entra ID Join

Quando un utente esegue il join a Entra ID (Settings → Accounts → Access work or school → Connect → Join Azure AD), se l'MDM scope è configurato in Entra ID (Mobility → MDM/MAM), l'enrollment in Intune è automatico.

Configurazione nel portale Entra ID:

1. Navigare a **Entra ID** → **Mobility (MDM and MAM)** → **Microsoft Intune**
2. **MDM user scope**: Tutti oppure gruppo specifico
3. **MAM user scope**: Tutti oppure gruppo specifico (per MAM senza enrollment)
4. **MDM URLs**: auto-popolati

### Bulk Enrollment con Provisioning Package

Per scenari di deployment massivo senza Autopilot:

```powershell
# 1. Installare Windows Configuration Designer (WCD) da Microsoft Store
# 2. Creare un nuovo provisioning package

# Template: Advanced Provisioning
# Runtime settings → Workplace → Enrollments → UPN

# Impostazioni chiave nel package:
# - AuthPolicy: OnPremise o Certificate
# - DiscoveryServiceFullURL: https://enrollment.manage.microsoft.com/enrollmentserver/discovery.svc
# - EnrollmentServiceFullURL: (auto-populated)
# - PolicyServiceFullURL: (auto-populated)
# - Secret: Bulk enrollment token

# 3. Esportare come .ppkg
# 4. Applicare durante OOBE o post-installazione

# Applicazione via PowerShell
Install-ProvisioningPackage -PackagePath "C:\Packages\IntuneEnroll.ppkg" -ForceInstall -QuietInstall
```

### Enrollment BYOD (Company Portal)

Per dispositivi personali, l'utente installa Company Portal e avvia l'enrollment:

1. Installare **Company Portal** dal Microsoft Store
2. Accedere con credenziali aziendali
3. Accettare i termini di utilizzo
4. Il dispositivo viene registrato come **Personal** in Intune
5. Le policy MAM e/o MDM (a seconda della configurazione) vengono applicate

```powershell
# Verifica tipo di enrollment su un dispositivo
$enrollment = Get-ChildItem "HKLM:\SOFTWARE\Microsoft\Enrollments\" | Where-Object {
    (Get-ItemProperty $_.PSPath).ProviderId -eq "MS DM Server"
}
$enrollProps = Get-ItemProperty $enrollment.PSPath
Write-Output "Ownership: $($enrollProps.DeviceOwnership)"
# 1 = Corporate, 2 = Personal
```

### Enrollment Restrictions

Intune consente di limitare quali dispositivi possono effettuare l'enrollment:

```
Intune Admin Center → Devices → Enrollment → Device platform restrictions
```

| Restrizione | Descrizione |
|---|---|
| **Platform restriction** | Blocca piattaforme specifiche (es. Android personale) |
| **Device limit** | Max dispositivi per utente (default: 15) |
| **Device type** | Corporate-only, BYOD-only, o entrambi |
| **OS version** | Versione minima/massima del sistema operativo |
| **Manufacturer** | Limita a produttori specifici (Android) |

```powershell
# Query enrollment restrictions via Graph API
$uri = "https://graph.microsoft.com/v1.0/deviceManagement/deviceEnrollmentConfigurations"
$restrictions = Invoke-MgGraphRequest -Method GET -Uri $uri
$restrictions.value | Format-Table displayName, priority, platformType
```

**Priorità delle Enrollment Restrictions:**

Le restrictions sono valutate in ordine di priorità (valore più basso = priorità più alta). La restriction "Default" ha sempre la priorità più bassa e si applica a tutti gli utenti non coperti da restrictions custom. Per scenari differenziati:

```
Priorità 1: "Executive-Enrollment" → Solo iOS 17+, solo corporate, max 3 device
Priorità 2: "BYOD-Restricted"     → Solo iOS/Android, blocca Windows personal
Priorità 3: "Default"              → Tutte le piattaforme, max 15 device
```

```powershell
# Creare enrollment restriction personalizzata via Graph API
$body = @{
    "@odata.type" = "#microsoft.graph.deviceEnrollmentPlatformRestriction"
    displayName   = "Block Personal Android"
    description   = "Blocca enrollment di dispositivi Android personali"
    platformRestriction = @{
        androidForWorkRestriction = @{
            platformBlocked = $false
            personalDeviceEnrollmentBlocked = $true
            osMinimumVersion = "13.0"
            osMaximumVersion = ""
        }
        androidRestriction = @{
            platformBlocked = $true
        }
    }
} | ConvertTo-Json -Depth 5

Invoke-MgGraphRequest -Method POST `
    -Uri "https://graph.microsoft.com/v1.0/deviceManagement/deviceEnrollmentConfigurations" `
    -Body $body -ContentType "application/json"
```

> **Caso reale:** Organizzazioni che non configurano enrollment restrictions spesso scoprono dispositivi personali registrati da utenti che hanno inserito le credenziali aziendali durante la configurazione iniziale del telefono. Questo crea una flotta non pianificata di dispositivi BYOD senza APP policy, visibili in Intune ma senza protezione. Best practice: configurare le restrictions prima del rollout agli utenti.

### Apple Device Enrollment Program (DEP/ADE)

Per dispositivi iOS/macOS aziendali acquistati tramite Apple Business Manager:

1. Collegare **Apple Business Manager** a Intune (certificato push MDM Apple)
2. Assegnare i numeri di serie al server MDM Intune
3. Creare un **Enrollment Profile** con configurazioni:
   - Supervisione (obbligatoria per management completo)
   - Setup Assistant steps da mostrare/nascondere
   - Entra ID join durante Setup Assistant
4. L'utente accende il dispositivo → enrollment automatico

### Android Enterprise Enrollment

| Modalità | Descrizione | Ownership |
|---|---|---|
| **Fully managed** | Intero dispositivo gestito | Corporate |
| **Dedicated device** | Kiosk/shared device | Corporate |
| **Work Profile** | Profilo separato per app aziendali | BYOD |
| **Corporate-owned Work Profile** | Device gestito + work profile | Corporate |

---

## Device Compliance Policies

### Concetto di Compliance

Una Compliance Policy definisce i requisiti minimi che un dispositivo deve soddisfare per essere considerato "conforme" (compliant). La compliance è il fondamento del Conditional Access: solo dispositivi conformi possono accedere alle risorse aziendali.

### Impostazioni di Compliance per Windows

```
Intune Admin Center → Devices → Compliance → Create policy → Windows 10/11
```

| Categoria | Impostazione | Esempio |
|---|---|---|
| **Device Health** | BitLocker richiesto | Abilitato |
| **Device Health** | Secure Boot richiesto | Abilitato |
| **Device Health** | Code integrity richiesto | Abilitato |
| **Device Properties** | OS version minima | 10.0.19045 |
| **Device Properties** | OS version massima | (vuoto = nessun limite) |
| **System Security** | Password richiesta | Si |
| **System Security** | Password complessità | Alfanumerica |
| **System Security** | Lunghezza minima password | 8 caratteri |
| **System Security** | Scadenza password | 90 giorni |
| **System Security** | Encryption storage | Richiesta |
| **System Security** | Firewall | Richiesto |
| **System Security** | Antivirus | Richiesto |
| **System Security** | Antispyware | Richiesto |
| **System Security** | Microsoft Defender Antimalware | Richiesto |
| **System Security** | Defender version minima | Aggiornata |
| **System Security** | Real-time protection | Richiesta |
| **Defender for Endpoint** | Risk score massimo | Medium o Low |
| **Microsoft Defender** | ATP risk level | Clear (nessun rischio) |

### Azioni di Non-Compliance

Quando un dispositivo non è conforme, Intune esegue azioni schedulate:

```
Compliance Policy → Actions for noncompliance
```

| Azione | Timing | Effetto |
|---|---|---|
| **Mark device noncompliant** | Immediato o delay X giorni | Device flag = non-compliant |
| **Send email to end user** | Dopo X giorni | Notifica utente |
| **Send push notification** | Dopo X giorni | Company Portal notification |
| **Remotely lock device** | Dopo X giorni | Lock screen |
| **Retire noncompliant device** | Dopo X giorni | Rimuove dati aziendali |
| **Add device to retire list** | Dopo X giorni | Coda per review admin |

### Compliance Policy per Piattaforma

```powershell
# Esempio: Creare compliance policy via Graph API
$body = @{
    "@odata.type" = "#microsoft.graph.windows10CompliancePolicy"
    displayName = "Standard Windows Compliance"
    description = "Policy compliance base per dispositivi Windows"
    bitLockerEnabled = $true
    secureBootEnabled = $true
    codeIntegrityEnabled = $true
    passwordRequired = $true
    passwordMinimumLength = 8
    passwordRequiredType = "alphanumeric"
    osMinimumVersion = "10.0.19045"
    storageRequireEncryption = $true
    firewallEnabled = $true
    antivirusRequired = $true
    defenderEnabled = $true
    rtpEnabled = $true
    scheduledActionsForRule = @(
        @{
            ruleName = "PasswordRequired"
            scheduledActionConfigurations = @(
                @{
                    actionType = "block"
                    gracePeriodHours = 72
                    notificationTemplateId = ""
                }
            )
        }
    )
} | ConvertTo-Json -Depth 5

Invoke-MgGraphRequest -Method POST `
    -Uri "https://graph.microsoft.com/v1.0/deviceManagement/deviceCompliancePolicies" `
    -Body $body -ContentType "application/json"
```

### Compliance State Machine

```
Dispositivo registrato → Valutazione compliance (ogni 8h)
    ↓
Compliant → Accesso consentito (via Conditional Access)
    ↓
Non-compliant → Grace period (configurabile)
    ↓
Azioni di remediation automatiche
    ↓
Ancora non-compliant → Block access / Retire
```

---

## Conditional Access Integration

### Compliance + Conditional Access

Il Conditional Access è configurato in Entra ID ma si integra strettamente con Intune. Il flusso tipico:

1. Utente tenta di accedere a una risorsa cloud (Exchange Online, SharePoint, ecc.)
2. Entra ID valuta le Conditional Access policies
3. Se la policy richiede "device compliant", Entra ID interroga Intune
4. Intune restituisce lo stato di compliance del dispositivo
5. Accesso consentito o bloccato

### Policy Conditional Access Tipiche

```
Entra ID → Security → Conditional Access → New policy
```

**Policy 1 — Richiedi dispositivo conforme per Office 365:**

| Impostazione | Valore |
|---|---|
| Users | Tutti gli utenti (esclusi break-glass accounts) |
| Cloud apps | Office 365 |
| Conditions | Tutte le piattaforme |
| Grant | Require device to be marked as compliant |
| Session | N/A |

**Policy 2 — Block legacy authentication:**

| Impostazione | Valore |
|---|---|
| Users | Tutti |
| Cloud apps | Tutte |
| Conditions | Client apps = Exchange ActiveSync, Other clients |
| Grant | Block access |

**Policy 3 — Require APP per dispositivi non gestiti:**

| Impostazione | Valore |
|---|---|
| Users | Tutti |
| Cloud apps | Office 365 |
| Conditions | Device state = Not Hybrid Entra ID joined, Not compliant |
| Grant | Require app protection policy |

### Device-Based vs App-Based Conditional Access

| Tipo | Requisito | Scenario |
|---|---|---|
| **Device-based** | Dispositivo registrato e conforme | Corporate-owned |
| **App-based** | App con policy di protezione | BYOD senza enrollment |
| **Combinato** | Entrambi | Massima sicurezza |

```powershell
# Query Conditional Access policies via Graph API
$policies = Invoke-MgGraphRequest -Method GET `
    -Uri "https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies"

$policies.value | ForEach-Object {
    [PSCustomObject]@{
        Name      = $_.displayName
        State     = $_.state
        GrantType = ($_.grantControls.builtInControls -join ", ")
    }
} | Format-Table -AutoSize
```

---

## Configuration Profiles

### Tipi di Configuration Profile

I Configuration Profile distribuiscono impostazioni ai dispositivi gestiti. Intune supporta diversi template:

| Tipo | Descrizione | Formato |
|---|---|---|
| **Templates** | Profili pre-costruiti per scenari comuni | GUI |
| **Settings Catalog** | Tutte le impostazioni disponibili, ricercabili | GUI granulare |
| **Custom (OMA-URI)** | Impostazioni via OMA-DM URI | XML/URI |
| **Administrative Templates (ADMX)** | Equivalente GPO nel cloud | ADMX-backed |
| **Imported ADMX** | ADMX custom di terze parti | Upload ADMX |
| **Security Baselines** | Set pre-configurati Microsoft | Best practices |

### Profilo Wi-Fi

```
Intune → Devices → Configuration → Create → Windows 10/11 → Templates → Wi-Fi
```

| Impostazione | Valore |
|---|---|
| Network name | Corporate-WiFi |
| SSID | CORP-SECURE |
| Connect automatically | Si |
| Security type | WPA2-Enterprise |
| EAP type | EAP-TLS |
| Certificate server names | radius.contoso.com |
| Root certificate | Certificato CA radice |
| Authentication method | Certificate (SCEP/PKCS) |
| Client certificate | Profilo SCEP collegato |

### Profilo VPN

```
Intune → Devices → Configuration → Create → Windows 10/11 → Templates → VPN
```

```xml
<!-- Esempio VPN Profile - Always On VPN -->
<VPNProfile>
  <RememberCredentials>true</RememberCredentials>
  <AlwaysOn>true</AlwaysOn>
  <DnsSuffix>contoso.com</DnsSuffix>
  <TrustedNetworkDetection>contoso.com</TrustedNetworkDetection>
  <NativeProfile>
    <Servers>vpn.contoso.com</Servers>
    <NativeProtocolType>IKEv2</NativeProtocolType>
    <Authentication>
      <MachineMethod>Certificate</MachineMethod>
    </Authentication>
    <RoutingPolicyType>SplitTunnel</RoutingPolicyType>
  </NativeProfile>
  <Route>
    <Address>10.0.0.0</Address>
    <PrefixSize>8</PrefixSize>
  </Route>
  <TrafficFilter>
    <App>
      <Id>%ProgramFiles%\Microsoft Office</Id>
    </App>
    <Protocol>6</Protocol>
    <RemotePortRanges>443</RemotePortRanges>
  </TrafficFilter>
</VPNProfile>
```

### Profilo Email

```
Intune → Devices → Configuration → Create → Templates → Email
```

| Impostazione | Valore |
|---|---|
| Email server | outlook.office365.com |
| Account name | Email Aziendale |
| Username attribute | UPN da Entra ID |
| Email address attribute | Primary SMTP |
| Authentication method | Certificato o username/password |
| SSL | Abilitato |
| S/MIME | Opzionale (richiede certificati) |

### Profilo Certificati (SCEP)

La distribuzione di certificati via Intune richiede:

1. **Trusted certificate profile** — distribuisce il certificato CA radice
2. **SCEP certificate profile** — richiede certificati utente/dispositivo
3. **NDES server** (on-premises) con **Intune Certificate Connector**

```
Flusso SCEP:
Dispositivo → Intune → NDES/Certificate Connector → CA interna → Certificato emesso
```

| Impostazione SCEP | Valore |
|---|---|
| Certificate type | User o Device |
| Subject name format | CN={{UserPrincipalName}} |
| SAN | UPN, Email |
| Key usage | Digital Signature, Key Encipherment |
| Key size | 2048 |
| Hash algorithm | SHA-2 |
| Root certificate | Profilo trusted certificate |
| SCEP Server URLs | https://ndes.contoso.com/certsrv/mscep/mscep.dll |
| Renewal threshold | 20% |
| Extended key usage | Client Authentication (1.3.6.1.5.5.7.3.2) |

### Profilo PKCS

Alternativa a SCEP con **PFX Certificate Connector**:

```powershell
# Installazione PKCS Certificate Connector
# Download da Intune Admin Center → Tenant administration → Connectors and tokens → Certificate connectors

# Il connettore si installa su un server Windows con accesso alla CA
# Richiede: .NET Framework 4.7.2+, IIS non necessario (a differenza di NDES)
```

### Settings Catalog — Configurazione Granulare

Il Settings Catalog offre migliaia di impostazioni ricercabili per nome:

```
Intune → Devices → Configuration → Create → Settings Catalog
```

Esempi di impostazioni frequenti:

| Categoria | Impostazione | Valore |
|---|---|---|
| **Windows Update** | Active Hours Start | 8 |
| **Windows Update** | Active Hours End | 17 |
| **BitLocker** | Encrypt method (OS Drive) | XTS-AES 256-bit |
| **BitLocker** | Recovery password rotation | Enable for Entra ID joined |
| **Edge Browser** | Homepage URL | https://intranet.contoso.com |
| **Edge Browser** | Block third-party cookies | Enabled |
| **Defender** | Cloud protection level | High |
| **Defender** | Submit samples consent | Send safe samples automatically |
| **Experience** | Allow Cortana | Block |
| **Experience** | Allow telemetry | Security only |

### Administrative Templates (ADMX)

Equivalenti alle GPO tradizionali, distribuiti via cloud:

```
Intune → Devices → Configuration → Create → Administrative Templates
```

Impostazioni comuni:

- **Computer Configuration** → Windows Components → Windows Update → Configure Automatic Updates
- **User Configuration** → Start Menu and Taskbar → Remove access to Task Manager (no)
- **Computer Configuration** → System → Logon → Always wait for network at startup

### Custom OMA-URI

Per impostazioni non disponibili nei template standard:

```
Intune → Devices → Configuration → Create → Custom
```

```xml
<!-- Esempio: Disabilitare USB storage -->
OMA-URI: ./Device/Vendor/MSFT/Policy/Config/Storage/RemovableDiskDenyWriteAccess
Data type: Integer
Value: 1

<!-- Esempio: Configurare Windows Hello PIN complexity -->
OMA-URI: ./Device/Vendor/MSFT/PassportForWork/{TenantId}/Policies/PINComplexity/MinimumPINLength
Data type: Integer
Value: 6

<!-- Esempio: Bloccare screenshot -->
OMA-URI: ./Device/Vendor/MSFT/Policy/Config/Experience/AllowScreenCapture
Data type: Integer
Value: 0
```

### Security Baselines

Microsoft fornisce baseline di sicurezza pre-configurate:

| Baseline | Descrizione |
|---|---|
| **MDM Security Baseline** | Impostazioni sicurezza Windows raccomandate |
| **Microsoft Defender for Endpoint** | Configurazione Defender |
| **Microsoft Edge** | Sicurezza browser |
| **Microsoft 365 Apps** | Office security |
| **Windows 365 Cloud PC** | Baseline per Cloud PC |

```
Intune → Endpoint Security → Security Baselines → MDM Security Baseline for Windows
```

---

## App Deployment — Distribuzione Applicazioni

### Tipi di App Supportate

| Tipo | Formato | Piattaforma | Gestione |
|---|---|---|---|
| **Microsoft Store app** | Store link | Windows | Automatica |
| **Win32 app** | `.intunewin` | Windows | Completa |
| **Microsoft 365 Apps** | Configurazione XML | Windows | Integrata |
| **LOB (Line of Business)** | `.msi`, `.appx`, `.appxbundle` | Windows | Base |
| **Web link** | URL | Tutte | Link |
| **Managed Google Play** | APK/Bundle | Android | Store gestito |
| **iOS Store app** | App Store link | iOS | Apple VPP |
| **macOS app** | `.dmg`, `.pkg` | macOS | LOB/Store |

### Win32 App Deployment

Il deployment Win32 è il metodo più flessibile per Windows. Richiede il packaging in formato `.intunewin`:

```powershell
# 1. Download dell'IntuneWinAppUtil
# https://github.com/microsoft/Microsoft-Win32-Content-Prep-Tool

# 2. Packaging dell'applicazione
.\IntuneWinAppUtil.exe `
    -c "C:\Packages\7zip" `          # Source folder
    -s "7z2301-x64.exe" `            # Setup file
    -o "C:\Packages\Output" `        # Output folder
    -q                                # Quiet mode

# Output: 7z2301-x64.intunewin
```

**Configurazione Win32 app in Intune:**

| Sezione | Campo | Esempio |
|---|---|---|
| **App information** | Name | 7-Zip 23.01 x64 |
| **App information** | Publisher | Igor Pavlov |
| **App information** | Version | 23.01 |
| **Program** | Install command | `7z2301-x64.exe /S` |
| **Program** | Uninstall command | `"C:\Program Files\7-Zip\Uninstall.exe" /S` |
| **Program** | Install behavior | System |
| **Program** | Device restart | App install may force device restart |
| **Requirements** | OS architecture | 64-bit |
| **Requirements** | Minimum OS | Windows 10 1607 |
| **Detection rules** | Rule type | File |
| **Detection rules** | Path | `C:\Program Files\7-Zip` |
| **Detection rules** | File | `7z.exe` |
| **Detection rules** | Detection method | File or folder exists |
| **Dependencies** | N/A | (nessuna per 7-Zip) |
| **Supersedence** | N/A | (versione precedente opzionale) |
| **Assignments** | Required | Gruppo "All Corporate Devices" |

### Detection Rules

Le detection rules verificano se l'app è già installata:

| Tipo | Esempio |
|---|---|
| **MSI product code** | `{23170F69-40C1-2702-2301-000001000000}` |
| **File/Folder** | `C:\Program Files\App\app.exe` esiste |
| **File version** | `app.exe` versione >= 23.01 |
| **File size** | `app.exe` dimensione in MB |
| **Registry** | `HKLM\SOFTWARE\App\Version` = "23.01" |
| **Custom script** | Script PowerShell che restituisce exit code 0 |

```powershell
# Esempio detection script PowerShell per app custom
$appPath = "C:\Program Files\CustomApp\app.exe"
$requiredVersion = [version]"2.5.0"

if (Test-Path $appPath) {
    $installedVersion = [version](Get-Item $appPath).VersionInfo.FileVersion
    if ($installedVersion -ge $requiredVersion) {
        Write-Output "App detected: v$installedVersion"
        exit 0   # Rilevata
    }
}
exit 1   # Non rilevata
```

### Requirement Rules Custom

```powershell
# Esempio requirement script: verifica RAM minima
$minRAM_GB = 8
$totalRAM = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 0)

if ($totalRAM -ge $minRAM_GB) {
    Write-Output "RAM sufficiente: ${totalRAM}GB"
    exit 0
}
else {
    Write-Output "RAM insufficiente: ${totalRAM}GB (richiesto: ${minRAM_GB}GB)"
    exit 1
}
```

### App Assignment Types

| Tipo | Comportamento |
|---|---|
| **Required** | Installazione automatica, l'utente non può rimuoverla |
| **Available** | Visibile nel Company Portal, l'utente sceglie se installare |
| **Uninstall** | Rimozione automatica (se precedentemente installata) |

### Microsoft 365 Apps Deployment

```
Intune → Apps → All apps → Add → Microsoft 365 Apps → Windows 10 and later
```

| Configurazione | Valore Esempio |
|---|---|
| Suite | Microsoft 365 Apps for Enterprise |
| Architecture | 64-bit |
| Update channel | Monthly Enterprise Channel |
| Apps incluse | Word, Excel, PowerPoint, Outlook, Teams, OneDrive |
| Apps escluse | Access, Publisher |
| Languages | it-IT (primaria), en-US (fallback) |
| Shared computer activation | Si (per VDI/RDS) |
| Accept EULA | Si |
| Version to install | Latest |

### MSIX e App Attach

MSIX è il formato moderno di packaging Microsoft:

```powershell
# MSIX packaging via MSIX Packaging Tool
# 1. Installare MSIX Packaging Tool da Microsoft Store
# 2. Creare package da installer esistente
# 3. Upload come LOB app in Intune

# Per Azure Virtual Desktop: MSIX App Attach
# Separazione tra OS e app, mount dinamico
```

### Supersedence (Sostituzione App)

La supersedence permette di aggiornare automaticamente un'app con una versione più recente:

```
App nuova → Supersedence → Seleziona app precedente → Update o Replace
```

| Azione | Comportamento |
|---|---|
| **Update** | Installa nuova versione, mantiene dati app |
| **Replace** | Disinstalla vecchia, installa nuova |

### Dependency (Dipendenze)

Le dependency garantiscono che i prerequisiti siano installati prima dell'app principale:

```
App principale → Dependencies → Seleziona prerequisiti → Auto install: Si
```

Esempio: un'app Java richiede JRE come dependency.

---

## App Protection Policies (MAM)

### MAM Senza Enrollment

Le App Protection Policies (APP) proteggono i dati aziendali a livello di app senza richiedere l'enrollment del dispositivo. Ideale per BYOD.

### Configurazione APP

```
Intune → Apps → App protection policies → Create policy → Windows / iOS / Android
```

**Impostazioni Data Protection:**

| Impostazione | Valore | Effetto |
|---|---|---|
| **Receive data from** | Policy managed apps only | Blocca ricezione da app personali |
| **Send data to** | Policy managed apps only | Blocca invio a app personali |
| **Restrict cut, copy, paste** | Policy managed apps with paste in | Limite clipboard |
| **Encrypt org data** | Require | Crittografia dati aziendali |
| **Save copies of org data** | Block | Blocca salvataggio locale |
| **Allow org data to other apps** | Policy managed apps only | Solo app gestite |
| **Print org data** | Block | Blocca stampa |
| **Backup org data to Android backup services** | Block | Blocca backup su cloud personale |
| **Screen capture** | Block | Blocca screenshot (Android) |

**Impostazioni Access Requirements:**

| Impostazione | Valore |
|---|---|
| **PIN for access** | Require |
| **PIN type** | Numeric |
| **Simple PIN** | Block |
| **PIN length** | 6 |
| **Fingerprint instead of PIN** | Allow |
| **PIN reset after (days)** | 90 |
| **Work or school account credentials** | Require |

**Impostazioni Conditional Launch:**

| Condizione | Azione | Valore |
|---|---|---|
| **Max PIN attempts** | Reset PIN | 5 tentativi |
| **Offline grace period** | Block access | 720 minuti |
| **Jailbroken/rooted device** | Wipe data | Immediato |
| **Min OS version** | Warn | iOS 16.0 / Android 13 |
| **Max allowed device threat level** | Block access | Secured |
| **Min app version** | Block access | Versione specifica |

### Selective Wipe (MAM Wipe)

Il selective wipe rimuove solo i dati aziendali dall'app, senza toccare i dati personali:

```
Intune → Apps → App selective wipe → Create wipe request
```

```powershell
# Selective wipe via Graph API
$params = @{
    "@odata.type" = "#microsoft.graph.managedDeviceMobileAppConfiguration"
}

# Wipe specifico utente/dispositivo
Invoke-MgGraphRequest -Method POST `
    -Uri "https://graph.microsoft.com/v1.0/deviceAppManagement/managedAppRegistrations/{id}/operations" `
    -Body ($params | ConvertTo-Json)
```

### App Gestite Supportate

Le APP funzionano con app che integrano l'Intune App SDK o sono wrappate con l'Intune App Wrapping Tool:

| App | Piattaforma | MAM Support |
|---|---|---|
| **Microsoft Outlook** | iOS, Android, Windows | Nativo |
| **Microsoft Teams** | iOS, Android, Windows | Nativo |
| **Microsoft Edge** | iOS, Android, Windows | Nativo |
| **Microsoft OneDrive** | iOS, Android | Nativo |
| **Adobe Acrobat Reader** | iOS, Android | Integrato |
| **App custom** | Tutte | Richiede SDK/Wrapping |

---

## Windows Autopilot

### Panoramica

Windows Autopilot automatizza il provisioning di dispositivi Windows nuovi o re-imaged. L'utente accende il dispositivo, si autentica, e il dispositivo si configura automaticamente con app, policy e impostazioni aziendali.

### Flusso Autopilot

```
1. OEM registra hardware hash nel tenant → Autopilot devices
2. Admin crea Autopilot deployment profile
3. Utente accende dispositivo nuovo
4. OOBE rileva Autopilot profile (via hardware hash)
5. Utente si autentica con credenziali aziendali
6. Dispositivo fa Entra ID join + enrollment Intune
7. ESP (Enrollment Status Page) mostra progresso
8. App, policy, certificati vengono installati
9. Desktop disponibile dopo completamento ESP
```

### Registrazione Hardware Hash

```powershell
# Raccolta hardware hash dal dispositivo (da eseguire localmente)
Install-Script -Name Get-WindowsAutoPilotInfo -Force
Get-WindowsAutoPilotInfo -OutputFile "C:\Temp\AutopilotHash.csv"

# Upload via Intune Admin Center:
# Devices → Windows enrollment → Devices → Import

# Oppure via Graph API
$hash = Get-Content "C:\Temp\AutopilotHash.csv" | ConvertFrom-Csv
$body = @{
    "@odata.type" = "#microsoft.graph.importedWindowsAutopilotDeviceIdentity"
    serialNumber = $hash.DeviceSerialNumber
    hardwareIdentifier = $hash.HardwareHash
    groupTag = "IT-Department"
} | ConvertTo-Json

Invoke-MgGraphRequest -Method POST `
    -Uri "https://graph.microsoft.com/v1.0/deviceManagement/importedWindowsAutopilotDeviceIdentities" `
    -Body $body -ContentType "application/json"
```

### Deployment Profiles

**User-Driven Mode:**

| Impostazione | Valore |
|---|---|
| Deployment mode | User-driven |
| Join to Entra ID | Entra ID joined |
| OOBE pages | Hide privacy, EULA, change account |
| Naming template | CORP-%SERIAL% |
| Apply device name template | Si |
| Language/Region | Operating system default |

**Self-Deploying Mode (kiosk/shared):**

| Impostazione | Valore |
|---|---|
| Deployment mode | Self-deploying |
| Join to Entra ID | Entra ID joined |
| OOBE pages | Hide all |
| Naming template | KIOSK-%RAND:4% |

**Pre-provisioning (White Glove):**

Permette al team IT di pre-configurare il dispositivo prima di consegnarlo all'utente:

1. Tecnico IT accende il dispositivo
2. Preme Windows key 5 volte → entra in modalità pre-provisioning
3. Viene applicato il profilo Autopilot (device context)
4. Dispositivo spento e consegnato all'utente
5. L'utente accende, si autentica, e riceve le configurazioni user-context

### Enrollment Status Page (ESP)

L'ESP mostra il progresso dell'enrollment e blocca l'accesso al desktop fino al completamento:

```
Intune → Devices → Windows enrollment → Enrollment Status Page
```

| Impostazione | Valore Raccomandato |
|---|---|
| Show app and profile configuration progress | Si |
| Show error when installation takes too long | Si |
| Show custom error message | "Contatta IT: helpdesk@contoso.com" |
| Turn on log collection | Si |
| Block device use until required apps installed | Si (solo per app critiche) |
| Installation time limit (minutes) | 60 |
| Allow retry when installation fails | Si |
| Allow reset when installation fails | Si |
| Allow device use despite error | No |

### Autopilot Reset

Ripristina il dispositivo allo stato post-Autopilot senza necessità di re-imaging:

```
Intune → Devices → [dispositivo] → Autopilot Reset
```

Oppure localmente:

```
Settings → System → Recovery → Reset this PC → Remove everything → Local reinstall
```

### Windows Autopilot Device Preparation

Evoluzione di Autopilot (disponibile da Windows 11 23H2+):

- Non richiede la registrazione preventiva degli hardware hash
- Configurazione just-in-time basata su gruppi Entra ID
- Supporta solo Entra ID join (no Hybrid)
- Tempo di deployment ridotto

---

## Co-Management con Configuration Manager

### Architettura Co-Management

Co-management permette di gestire dispositivi Windows simultaneamente con Intune e Configuration Manager (SCCM/MECM):

```
Configuration Manager ←→ Co-Management ←→ Intune
    (on-premises)         (workload split)    (cloud)
         ↕
    Dispositivo Windows
```

### Workload Slider

Ogni workload può essere spostato da Configuration Manager a Intune:

| Workload | Default | Migrazione |
|---|---|---|
| **Compliance policies** | ConfigMgr | Intune (priorità) |
| **Device configuration** | ConfigMgr | Intune |
| **Endpoint Protection** | ConfigMgr | Intune (Defender) |
| **Resource access policies** | ConfigMgr | Intune |
| **Client apps** | ConfigMgr | Intune |
| **Office Click-to-Run apps** | ConfigMgr | Intune |
| **Windows Update policies** | ConfigMgr | Intune (WUfB) |

> **Errore comune:** Con co-management attivo, se il workload "Compliance Policies" non è spostato su Intune, le compliance policy di Intune non vengono valutate e il Conditional Access non funziona correttamente. Verificare sempre che il workload sia spostato su Intune per ogni policy che dipende da Conditional Access.

### Abilitazione Co-Management

```powershell
# Prerequisiti:
# 1. ConfigMgr Current Branch (2111+)
# 2. Entra ID Connect configurato (Hybrid Entra ID Join)
# 3. Cloud Management Gateway (CMG) per gestione internet
# 4. Licenze Intune per tutti gli utenti

# In ConfigMgr Console:
# Administration → Cloud Services → Co-management → Configure Co-management
# 1. Automatic enrollment in Intune: All o Pilot
# 2. Pilot group: Collection specifica
# 3. Workloads: configurare slider per ogni workload
```

### Cloud Management Gateway (CMG)

Il CMG permette la gestione di dispositivi ConfigMgr via internet:

```powershell
# CMG si configura in ConfigMgr Console:
# Administration → Cloud Services → Cloud Management Gateway

# Requisiti:
# - Azure subscription
# - Server authentication certificate
# - Azure AD app registration
# - CMG connector point (site system role)
```

---

## Endpoint Analytics

### Panoramica

Endpoint Analytics fornisce insight sulle prestazioni e sull'esperienza utente dei dispositivi gestiti:

```
Intune → Reports → Endpoint Analytics
```

### Metriche Principali

| Metrica | Descrizione | Target |
|---|---|---|
| **Startup performance** | Tempo di boot + login | < 60 secondi |
| **Restart frequency** | Riavvii non pianificati | < 1/settimana |
| **Application reliability** | Crash e hang delle app | < 2 crash/app/giorno |
| **Proactive remediations** | Script correttivi automatici | > 90% successo |
| **Work from anywhere** | Score di readiness remoto | > 70/100 |

### Proactive Remediations

Script che rilevano e correggono automaticamente problemi comuni:

```powershell
# === DETECTION SCRIPT: Verifica servizio Spooler ===
# Se il servizio è fermo, lo script restituisce exit code 1 (problema rilevato)

$service = Get-Service -Name "Spooler" -ErrorAction SilentlyContinue
if ($service.Status -ne "Running") {
    Write-Output "Spooler service not running"
    exit 1   # Remediation necessaria
}
Write-Output "Spooler service is running"
exit 0   # Tutto ok


# === REMEDIATION SCRIPT: Avvia servizio Spooler ===
try {
    Start-Service -Name "Spooler" -ErrorAction Stop
    Set-Service -Name "Spooler" -StartupType Automatic
    Write-Output "Spooler service started and set to Automatic"
    exit 0
}
catch {
    Write-Output "Failed to start Spooler: $_"
    exit 1
}
```

```powershell
# === DETECTION SCRIPT: Verifica spazio disco ===
$drive = Get-PSDrive C
$freePercent = [math]::Round(($drive.Free / ($drive.Used + $drive.Free)) * 100, 1)

if ($freePercent -lt 10) {
    Write-Output "Low disk space: ${freePercent}% free"
    exit 1
}
Write-Output "Disk space OK: ${freePercent}% free"
exit 0


# === REMEDIATION SCRIPT: Pulizia disco ===
try {
    # Pulizia cartella Temp
    Remove-Item -Path "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
    # Pulizia Windows Temp
    Remove-Item -Path "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
    # Pulizia Recycle Bin
    Clear-RecycleBin -Force -ErrorAction SilentlyContinue
    # Pulizia Windows Update cache
    Stop-Service -Name wuauserv -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "C:\Windows\SoftwareDistribution\Download\*" -Recurse -Force -ErrorAction SilentlyContinue
    Start-Service -Name wuauserv
    
    Write-Output "Disk cleanup completed"
    exit 0
}
catch {
    Write-Output "Cleanup failed: $_"
    exit 1
}
```

---

## Remote Actions

### Azioni Disponibili

```
Intune → Devices → [dispositivo] → Azioni
```

| Azione | Effetto | Reversibile |
|---|---|---|
| **Sync** | Forza check-in immediato | - |
| **Restart** | Riavvia il dispositivo | - |
| **Rename** | Rinomina il dispositivo | Si |
| **Wipe** | Factory reset completo | No |
| **Retire** | Rimuove dati aziendali, mantiene personali | No |
| **Fresh Start** | Reset Windows preservando account utente | No |
| **Autopilot Reset** | Reset mantenendo Autopilot profile | No |
| **Remote Lock** | Blocca lo schermo | Si (con PIN) |
| **Reset Passcode** | Reset PIN/password | - |
| **Disable Activation Lock** | Rimuove iOS Activation Lock | - |
| **Locate Device** | Mostra posizione (iOS supervised) | - |
| **Rotate BitLocker Keys** | Ruota chiavi di recovery BitLocker | - |
| **Collect Diagnostics** | Raccoglie log diagnostici dal dispositivo | - |
| **Custom Notifications** | Invia notifica push all'utente | - |
| **Update Windows Defender** | Forza aggiornamento definizioni | - |
| **Quick Scan / Full Scan** | Avvia scansione Defender | - |

### Wipe vs Retire

| Caratteristica | Wipe | Retire |
|---|---|---|
| Dati aziendali | Rimossi | Rimossi |
| Dati personali | Rimossi | Preservati |
| Account utente | Rimossi | Preservati |
| App aziendali | Rimosse | Rimosse |
| App personali | Rimosse | Preservate |
| Enrollment | Rimosso | Rimosso |
| Factory reset | Si | No |
| Uso tipico | Dispositivo perso/rubato | BYOD, cambio utente |

```powershell
# Wipe via Graph API
$deviceId = "device-object-id"
Invoke-MgGraphRequest -Method POST `
    -Uri "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices/$deviceId/wipe"

# Retire via Graph API
Invoke-MgGraphRequest -Method POST `
    -Uri "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices/$deviceId/retire"

# Sync via Graph API
Invoke-MgGraphRequest -Method POST `
    -Uri "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices/$deviceId/syncDevice"

# Collect diagnostics
Invoke-MgGraphRequest -Method POST `
    -Uri "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices/$deviceId/createDeviceLogCollectionRequest"
```

---

## Custom Compliance Scripts

### Panoramica

Gli script di compliance personalizzati estendono le policy di compliance standard con controlli custom:

```
Intune → Devices → Compliance → Scripts → Add
```

### Struttura dello Script

Lo script deve restituire output JSON con la struttura definita:

```powershell
# === Custom Compliance Script: Verifica configurazioni sicurezza ===

$results = @()

# Check 1: Verifica che SMBv1 sia disabilitato
$smb1 = Get-SmbServerConfiguration | Select-Object -ExpandProperty EnableSMB1Protocol
$results += @{
    SettingName  = "SMBv1Disabled"
    Operator     = "IsEquals"
    DataType     = "Boolean"
    Operand      = $false
    MoreInfoUrl  = "https://aka.ms/smbv1"
    RemediationStrings = @(
        @{
            Language = "en_US"
            Title    = "SMBv1 must be disabled"
            Description = "SMBv1 is a legacy protocol with known vulnerabilities."
        }
    )
}

# Check 2: Verifica PowerShell execution policy
$execPolicy = Get-ExecutionPolicy -Scope LocalMachine
$results += @{
    SettingName  = "PSExecutionPolicy"
    Operator     = "IsEquals"
    DataType     = "String"
    Operand      = "RemoteSigned"
    MoreInfoUrl  = "https://aka.ms/psexecpolicy"
    RemediationStrings = @(
        @{
            Language = "en_US"
            Title    = "PowerShell Execution Policy"
            Description = "Must be RemoteSigned or more restrictive."
        }
    )
}

# Check 3: Verifica ultima data di reboot
$lastBoot = (Get-CimInstance -ClassName Win32_OperatingSystem).LastBootUpTime
$daysSinceBoot = (New-TimeSpan -Start $lastBoot -End (Get-Date)).Days
$results += @{
    SettingName  = "DaysSinceLastReboot"
    Operator     = "LessThan"
    DataType     = "Int64"
    Operand      = 14
    MoreInfoUrl  = "https://contoso.com/reboot-policy"
    RemediationStrings = @(
        @{
            Language = "en_US"
            Title    = "Device must reboot within 14 days"
            Description = "Regular reboots ensure patches are applied."
        }
    )
}

# Output JSON
$output = @{
    Values = $results
}
$output | ConvertTo-Json -Depth 5 -Compress
```

### Associazione a Compliance Policy

```
1. Upload script in Intune → Compliance → Scripts
2. Creare compliance policy → Custom Compliance
3. Selezionare lo script caricato
4. Configurare il JSON schema per i setting names
5. Assegnare la policy ai gruppi
```

---

## PowerShell Scripts Deployment

### Esecuzione Script via Intune

```
Intune → Devices → Scripts and remediations → Platform scripts → Add → Windows 10 and later
```

| Impostazione | Opzione |
|---|---|
| **Run this script using logged on credentials** | Si (user context) / No (system context) |
| **Enforce script signature check** | Si (solo script firmati) / No |
| **Run script in 64-bit PowerShell host** | Si (raccomandato) |
| **Run frequency** | Once / Every 1 hour / Every 8 hours / etc. |

### Esempio: Script di Configurazione Iniziale

```powershell
# === Script deployment: Configurazione iniziale workstation ===
# Contesto: SYSTEM
# Esecuzione: Una volta

$logFile = "C:\ProgramData\IntuneLogs\InitialConfig.log"
New-Item -Path (Split-Path $logFile) -ItemType Directory -Force | Out-Null

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp - $Message" | Out-File -FilePath $logFile -Append
}

try {
    Write-Log "=== Inizio configurazione iniziale ==="

    # 1. Disabilitare SMBv1
    Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force
    Write-Log "SMBv1 disabilitato"

    # 2. Configurare NTP
    w32tm /config /manualpeerlist:"time.windows.com" /syncfromflags:manual /reliable:YES /update
    Restart-Service w32time
    Write-Log "NTP configurato"

    # 3. Abilitare Remote Desktop (se richiesto)
    Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server" `
        -Name "fDenyTSConnections" -Value 0
    Enable-NetFirewallRule -DisplayGroup "Remote Desktop"
    Write-Log "Remote Desktop abilitato"

    # 4. Configurare power plan
    powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c  # High Performance
    Write-Log "Power plan: High Performance"

    # 5. Disabilitare consumer features
    $regPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\CloudContent"
    New-Item -Path $regPath -Force | Out-Null
    Set-ItemProperty -Path $regPath -Name "DisableWindowsConsumerFeatures" -Value 1
    Write-Log "Consumer features disabilitate"

    Write-Log "=== Configurazione completata con successo ==="
    exit 0
}
catch {
    Write-Log "ERRORE: $($_.Exception.Message)"
    exit 1
}
```

### Script con Output per Reporting

```powershell
# === Script che restituisce dati per Intune reporting ===
# Output su STDOUT viene catturato da Intune

$info = @{
    Hostname     = $env:COMPUTERNAME
    SerialNumber = (Get-CimInstance Win32_BIOS).SerialNumber
    TPMVersion   = (Get-CimInstance -Namespace "root/cimv2/Security/MicrosoftTpm" -ClassName Win32_Tpm).SpecVersion
    BitLocker    = (Get-BitLockerVolume -MountPoint C:).ProtectionStatus
    LastBoot     = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
    FreeSpace_GB = [math]::Round((Get-PSDrive C).Free / 1GB, 2)
}

$info | ConvertTo-Json
```

---

## Endpoint Privilege Management

### Panoramica EPM

Endpoint Privilege Management (EPM), parte della Intune Suite, permette agli utenti standard di eseguire attività che normalmente richiedono privilegi di amministratore, senza assegnare admin permanente.

### Elevation Rules

```
Intune → Endpoint Security → Endpoint Privilege Management → Policies → Create
```

| Tipo di Regola | Descrizione |
|---|---|
| **Automatic** | Elevazione automatica senza prompt |
| **User confirmed** | Richiede conferma utente (business justification) |
| **Support approved** | Richiede approvazione del team IT |

### Configurazione Elevation Policy

```
Elevation Settings Policy:
- Default elevation response: Deny all requests
- Send elevation data to Microsoft: Yes (per reporting)
- Report scope: Diagnostic data and managed elevations
```

```
Elevation Rules Policy:
- Rule name: "Installa stampanti"
- Elevation type: User confirmed
- File information:
  - File name: printui.exe
  - File path: C:\Windows\System32\
  - File hash: (calcolato automaticamente)
  - Certificate: Microsoft Windows
- Child process behavior: Allow managed elevation
- Business justification required: Yes
```

> **Errore comune:** Assegnare regole EPM troppo permissive (es. elevazione automatica per `cmd.exe` o `powershell.exe`) annulla il valore di EPM. Ogni regola deve specificare un'applicazione con hash o certificato publisher. Non elevare mai shell generiche in modo automatico.

---

## Windows Update for Business

### Panoramica WUfB

Windows Update for Business (WUfB) è il meccanismo cloud-native per gestire gli aggiornamenti Windows senza infrastruttura WSUS on-premises. Intune lo espone tramite tre tipi di policy:

| Policy | Funzione | Granularità |
|---|---|---|
| **Update Rings** | Deferral e comportamento degli aggiornamenti | Feature + Quality + Driver |
| **Feature Update Policies** | Fissare la versione di feature update target | Versione specifica (es. 24H2) |
| **Quality Update Policies** | Accelerare (expedite) aggiornamenti di sicurezza critici | Aggiornamento specifico |
| **Driver Update Policies** | Approvazione driver via WUfB | Per driver/dispositivo |

### Update Rings — Configurazione

```
Intune → Devices → Windows → Update Rings for Windows 10 and later → Create
```

| Impostazione | Ring 0 — IT Pilot | Ring 1 — Early Adopters | Ring 2 — Produzione |
|---|---|---|---|
| **Quality update deferral** | 0 giorni | 3 giorni | 7 giorni |
| **Feature update deferral** | 0 giorni | 14 giorni | 30 giorni |
| **Quality update pause** | No | No | Disponibile |
| **Feature update pause** | No | No | Disponibile |
| **Automatic update behavior** | Auto install + restart at scheduled time | Auto install + restart at scheduled time | Auto install + restart at scheduled time |
| **Active hours start** | 8:00 | 8:00 | 7:00 |
| **Active hours end** | 17:00 | 18:00 | 19:00 |
| **Restart grace period** | 2 giorni | 3 giorni | 5 giorni |
| **Deadline for quality updates** | 2 giorni | 5 giorni | 7 giorni |
| **Deadline for feature updates** | 5 giorni | 7 giorni | 14 giorni |
| **Uninstall period (feature)** | 10 giorni | 10 giorni | 30 giorni |

```powershell
# Creazione Update Ring via Graph API
$body = @{
    "@odata.type" = "#microsoft.graph.windowsUpdateForBusinessConfiguration"
    displayName = "Ring 2 - Produzione"
    description = "Ring di produzione con deferral di sicurezza"
    qualityUpdatesDeferralPeriodInDays = 7
    featureUpdatesDeferralPeriodInDays = 30
    qualityUpdatesPaused = $false
    featureUpdatesPaused = $false
    businessReadyUpdatesOnly = "userDefined"
    automaticUpdateMode = "autoInstallAndRebootAtScheduledTime"
    scheduledInstallDay = "everyDay"
    scheduledInstallTime = "03:00:00"
    engagedRestartDeadlineInDays = 5
    activeHoursStart = 7
    activeHoursEnd = 19
    deadlineForQualityUpdatesInDays = 7
    deadlineForFeatureUpdatesInDays = 14
    deadlineGracePeriodInDays = 2
    driversExcluded = $false
} | ConvertTo-Json

Invoke-MgGraphRequest -Method POST `
    -Uri "https://graph.microsoft.com/v1.0/deviceManagement/deviceConfigurations" `
    -Body $body -ContentType "application/json"
```

### Feature Update Policies

Le Feature Update Policies fissano la versione di feature update target, impedendo che i dispositivi avanzino oltre una versione specifica:

```
Intune → Devices → Windows → Feature updates for Windows 10 and later → Create
```

| Scenario | Versione Target | Motivo |
|---|---|---|
| Stabilizzazione dopo rilascio | Windows 11 24H2 | Testare compatibilità app |
| Blocco versione per compliance | Windows 11 23H2 | Certificazione settoriale |
| Rollout graduale nuova versione | Windows 11 24H2 | Migrazione progressiva |

> **Approfondimento:** Le Feature Update Policies utilizzano il servizio Windows Update for Business deployment service (WUfBDS), che gestisce l'offerta di aggiornamenti a livello di Microsoft cloud. A differenza dei deferral negli Update Rings (che ritardano ma non bloccano), le Feature Update Policies controllano esattamente quale versione viene offerta al dispositivo (fonte: https://learn.microsoft.com/en-us/mem/intune/protect/windows-10-feature-updates — consultato: 2026-05-23).

### Quality Update Policies (Expedited Updates)

Quando un aggiornamento di sicurezza critico richiede deployment immediato (es. zero-day attivamente sfruttato):

```
Intune → Devices → Windows → Quality updates for Windows 10 and later → Create
```

| Impostazione | Valore |
|---|---|
| Update to install | Expedited latest quality update |
| Days before forced reboot | 2 |
| Restart grace period | 1 giorno |

L'expedited update bypassa i deferral configurati negli Update Rings, forzando l'installazione dell'ultimo aggiornamento qualità entro 24-48 ore.

### Driver Update Policies

```
Intune → Devices → Windows → Driver updates for Windows 10 and later → Create
```

| Modalità | Comportamento |
|---|---|
| **Automatic** | Tutti i driver approvati automaticamente |
| **Manual approval** | Admin approva ogni driver prima del deployment |

```powershell
# Query driver disponibili per approvazione via Graph API
$drivers = Invoke-MgGraphRequest -Method GET `
    -Uri "https://graph.microsoft.com/beta/admin/windows/updates/catalog/entries?`$filter=isof('microsoft.graph.windowsUpdates.driverUpdateCatalogEntry')"

$drivers.value | ForEach-Object {
    [PSCustomObject]@{
        Name            = $_.displayName
        Version         = $_.version
        ReleaseDate     = $_.releaseDateTime
        DeployableUntil = $_.deployableUntilDateTime
    }
} | Format-Table -AutoSize
```

> **Errore comune:** Abilitare driver automatici in produzione senza un ring pilota. Un driver GPU difettoso distribuito automaticamente a migliaia di dispositivi può causare BSOD di massa. Best practice: usare manual approval per il ring di produzione e automatic solo per il ring pilota.

---

## Windows LAPS via Intune

### Panoramica

Windows LAPS (Local Administrator Password Solution) gestisce automaticamente la password dell'account amministratore locale, ruotandola periodicamente e salvandola in modo sicuro in Entra ID o Active Directory on-premises.

Windows LAPS è integrato nativamente in Windows 10 (21H2+) e Windows 11 — non richiede agent aggiuntivo, a differenza del legacy Microsoft LAPS (che usava un CSE Group Policy).

### Configurazione via Intune

```
Intune → Endpoint Security → Account Protection → Create → Local Admin Password Solution (Windows LAPS)
```

| Impostazione | Valore Raccomandato | Note |
|---|---|---|
| **Backup directory** | Azure AD | Oppure Active Directory per hybrid |
| **Password age (days)** | 30 | Rotazione mensile |
| **Administrator account name** | (default) | Usa account admin built-in |
| **Password complexity** | Large + small + numbers + special | Massima entropia |
| **Password length** | 20 | Minimo raccomandato 14 |
| **Post-authentication actions** | Reset password and logoff | Invalida dopo uso |
| **Post-authentication reset delay (hours)** | 2 | Finestra di utilizzo |

### Recupero Password LAPS

```
Intune → Devices → [dispositivo] → Local admin password
```

```powershell
# Recupero password LAPS via Graph API
$deviceId = "device-entra-id"
$laps = Invoke-MgGraphRequest -Method GET `
    -Uri "https://graph.microsoft.com/v1.0/directory/deviceLocalCredentials/$deviceId"

Write-Output "Account: $($laps.credentials[0].accountName)"
Write-Output "Password: $($laps.credentials[0].passwordBase64)"
Write-Output "Backup Time: $($laps.credentials[0].backUpDateTime)"
Write-Output "Rotation Due: $($laps.refreshDateTime)"
```

### Audit e Compliance LAPS

```powershell
# Verifica che LAPS sia attivo su tutti i dispositivi gestiti
$devices = Invoke-MgGraphRequest -Method GET `
    -Uri "https://graph.microsoft.com/v1.0/directory/deviceLocalCredentials"

$devices.value | ForEach-Object {
    [PSCustomObject]@{
        DeviceName   = $_.deviceName
        Account      = $_.credentials[0].accountName
        LastBackup   = $_.credentials[0].backUpDateTime
        NextRotation = $_.refreshDateTime
    }
} | Format-Table -AutoSize
```

> **Approfondimento:** Windows LAPS in modalità Entra ID salva la password crittografata nel cloud. L'accesso richiede il permesso RBAC `microsoft.directory/deviceLocalCredentials/password/read` in Entra ID. Tutti gli accessi alle password sono registrati nei sign-in logs di Entra ID, fornendo completa tracciabilità di chi ha letto quale password e quando (fonte: https://learn.microsoft.com/en-us/mem/intune/protect/windows-laps-overview — consultato: 2026-05-23).

---

## Device Categories, Scope Tags e Filters

### Device Categories

Le categorie dispositivo permettono la classificazione automatica per tipo/reparto:

```
Intune → Devices → Device categories → Create
```

Esempi: `IT-Department`, `Executive`, `Kiosk`, `Shared-Device`, `BYOD-Personal`.

Dopo la creazione, le categorie possono essere assegnate automaticamente tramite regole di mapping o selezionate dall'utente durante l'enrollment. Servono come criterio per **gruppi dinamici Entra ID**:

```
(device.deviceCategory -eq "IT-Department")
```

### Scope Tags — RBAC per Oggetti

Gli Scope Tags controllano la visibilità degli oggetti Intune per gli amministratori:

```
Intune → Tenant administration → Roles → Scope tags → Create
```

| Elemento | Scope Tag applicabile |
|---|---|
| Policy di compliance | Si |
| Configuration Profile | Si |
| App | Si |
| Script PowerShell | Si |
| Autopilot Profile | Si |
| Update Ring | Si |
| Enrollment Restriction | Si |

**Workflow operativo:**

```
1. Creare Scope Tags: "Milano", "Roma", "Torino"
2. Assegnare scope tags alle policy e ai profili pertinenti
3. Creare ruoli custom con scope tag specifici
4. Assegnare ruoli agli admin delegati
→ L'admin "Milano" vede e gestisce solo oggetti taggati "Milano"
```

### Filters — Targeting Granulare

I Filters permettono di raffinare il targeting delle assignment senza creare gruppi aggiuntivi:

```
Intune → Tenant administration → Filters → Create
```

```
# Esempi di regole filtro
(device.operatingSystemVersion -startsWith "10.0.22631")    # Solo Windows 11 23H2
(device.manufacturer -eq "Lenovo")                           # Solo hardware Lenovo
(device.model -startsWith "ThinkPad")                        # Solo ThinkPad
(device.enrollmentProfileName -eq "Autopilot-Standard")     # Solo profilo specifico
(device.deviceOwnership -eq "Corporate")                     # Solo dispositivi aziendali
```

| Modalità Filter | Comportamento |
|---|---|
| **Include** | La policy si applica solo ai dispositivi che matchano il filtro |
| **Exclude** | La policy si applica a tutti tranne i dispositivi che matchano |

> **Errore comune:** Confondere Scope Tags e Filters. **Scope Tags** = RBAC per admin (chi vede cosa nel portale). **Filters** = targeting per assignment (a quali dispositivi si applica la policy). Sono ortogonali e si usano insieme.

---

## DFCI — Device Firmware Configuration Interface

### Panoramica

Device Firmware Configuration Interface (DFCI) consente la gestione del firmware UEFI da Intune, senza accesso fisico al dispositivo. Supportato su hardware selezionato (Surface, Lenovo, Dell, HP con firmware DFCI-compatible).

### Configurazione

```
Intune → Devices → Configuration → Create → Templates →
  Device Firmware Configuration Interface
```

| Impostazione | Opzioni | Sicurezza |
|---|---|---|
| **Boot from USB** | Disable | Previene boot da media USB |
| **Cameras** | Disable | Privacy in ambienti sensibili |
| **Microphones** | Disable | Privacy in ambienti classificati |
| **Bluetooth** | Disable | Riduce superficie di attacco wireless |
| **Wi-Fi** | Disable | Per dispositivi solo Ethernet |
| **Boot from network (PXE)** | Disable | Previene boot da rete non autorizzato |
| **UEFI password** | Managed by Intune | Protegge impostazioni BIOS |

### Prerequisiti DFCI

1. Hardware con firmware DFCI-compatible (Surface Pro 9+, Surface Laptop 5+, Lenovo ThinkPad selezionati)
2. Dispositivo registrato via Windows Autopilot
3. Autopilot profile con DFCI abilitato
4. Windows 10/11 con UEFI che supporta il protocollo DFCI

> **Approfondimento:** DFCI usa certificati per autenticare le richieste di configurazione firmware. Intune invia policy firmate al dispositivo, che il firmware UEFI verifica prima di applicare. Questo impedisce che un attaccante con accesso fisico possa modificare le impostazioni BIOS/UEFI anche se ha la password del firmware (fonte: https://learn.microsoft.com/en-us/mem/intune/configuration/device-firmware-configuration-interface-windows — consultato: 2026-05-23).

---

## Intune Reporting e Automazione Graph API

### Report Operativi

Intune offre diversi livelli di reporting:

| Report | Posizione | Dati |
|---|---|---|
| **Device compliance** | Reports → Device compliance | Stato compliance per policy/OS |
| **Configuration profiles** | Reports → Device configuration | Successo/errore per profilo |
| **App install status** | Apps → Monitor | Stato installazione per app |
| **Update compliance** | Reports → Windows updates | Stato aggiornamenti per ring |
| **Endpoint Analytics** | Reports → Endpoint Analytics | Performance, startup, reliability |
| **Security baselines** | Endpoint Security → Overview | Aderenza alle baseline |

### Export API per Report Massivi

Per report con oltre 200.000 record, Intune usa un'API di export asincrona:

```powershell
# Avviare export report
$exportBody = @{
    reportName = "Devices"
    filter     = ""
    select     = @(
        "DeviceName", "UPN", "OSVersion",
        "ComplianceState", "LastContact"
    )
    format     = "csv"
} | ConvertTo-Json

$exportJob = Invoke-MgGraphRequest -Method POST `
    -Uri "https://graph.microsoft.com/v1.0/deviceManagement/reports/exportJobs" `
    -Body $exportBody -ContentType "application/json"

# Attendere completamento (polling)
do {
    Start-Sleep -Seconds 10
    $status = Invoke-MgGraphRequest -Method GET `
        -Uri "https://graph.microsoft.com/v1.0/deviceManagement/reports/exportJobs('$($exportJob.id)')"
} while ($status.status -ne "completed")

# Download CSV
Invoke-WebRequest -Uri $status.url -OutFile "C:\Reports\DeviceReport.csv"
Write-Output "Report scaricato: $($status.url)"
```

### Integrazione con Log Analytics

Per analisi avanzate e alerting, Intune può inviare dati diagnostici a un workspace Log Analytics:

```
Intune → Tenant administration → Diagnostic settings → Add diagnostic setting
```

| Categoria Log | Dati |
|---|---|
| **AuditLogs** | Azioni admin (creazione/modifica policy, wipe) |
| **OperationalLogs** | Enrollment, compliance evaluation, app install |
| **DeviceComplianceOrg** | Stato compliance aggregato |
| **Devices** | Inventario dispositivi |

```kusto
// KQL: Dispositivi non conformi da più di 7 giorni
IntuneDeviceComplianceOrg
| where ComplianceState == "NonCompliant"
| where TimeGenerated > ago(7d)
| summarize LastSeen=max(TimeGenerated) by DeviceName, OS, UPN
| order by LastSeen asc
```

```kusto
// KQL: Enrollment falliti nelle ultime 24 ore
IntuneOperationalLogs
| where TimeGenerated > ago(24h)
| where OperationName contains "Enrollment"
| where Result == "Fail"
| project TimeGenerated, UPN, DeviceName, ResultDescription
| order by TimeGenerated desc
```

### Backup Completo della Configurazione

```powershell
# === Backup completo Intune via Graph API ===
$backupRoot = "C:\IntuneBackup\$(Get-Date -Format 'yyyy-MM-dd')"
$endpoints = @{
    "CompliancePolicies"        = "deviceManagement/deviceCompliancePolicies"
    "ConfigurationProfiles"     = "deviceManagement/deviceConfigurations"
    "AppProtectionPolicies"     = "deviceAppManagement/managedAppPolicies"
    "ConditionalAccessPolicies" = "identity/conditionalAccess/policies"
    "EnrollmentRestrictions"    = "deviceManagement/deviceEnrollmentConfigurations"
    "SecurityBaselines"         = "deviceManagement/templates"
    "Scripts"                   = "deviceManagement/deviceManagementScripts"
}

foreach ($name in $endpoints.Keys) {
    $path = "$backupRoot\$name"
    New-Item -Path $path -ItemType Directory -Force | Out-Null
    
    $data = Invoke-MgGraphRequest -Method GET `
        -Uri "https://graph.microsoft.com/v1.0/$($endpoints[$name])"
    
    foreach ($item in $data.value) {
        $fileName = "$($item.displayName -replace '[^\w\-]','_').json"
        $item | ConvertTo-Json -Depth 15 |
            Out-File "$path\$fileName" -Encoding utf8
    }
    Write-Output "$name : $($data.value.Count) oggetti esportati"
}
Write-Output "Backup completato in $backupRoot"
```

---

## Sicurezza e Best Practices

### Checklist Sicurezza Intune

- [ ] MFA abilitata per tutti gli admin Intune
- [ ] Break-glass accounts esclusi da Conditional Access
- [ ] Security baselines applicate a tutti i dispositivi Windows
- [ ] App Protection Policies per tutte le app aziendali
- [ ] Compliance policies con azioni di non-compliance
- [ ] Conditional Access che richiede dispositivi conformi
- [ ] Enrollment restrictions configurate (piattaforme, versioni OS)
- [ ] BitLocker enforcement via compliance e configuration profile
- [ ] Defender for Endpoint integration abilitata
- [ ] RBAC configurato con principio del minimo privilegio
- [ ] Audit log monitorati
- [ ] Certificati SCEP/PKCS con chiavi >= 2048 bit
- [ ] Script PowerShell firmati in produzione
- [ ] Review trimestrale delle policy e delle esclusioni

### Best Practices per il Deployment

1. **Gruppi dinamici Entra ID** per assignment automatico basato su attributi dispositivo
2. **Scope tags** per delegare la gestione per reparto/sede
3. **Filters** per targetizzare assignment senza creare gruppi aggiuntivi
4. **Staging progressivo**: pilot → early adopters → produzione
5. **Naming convention** consistente per policy, profili e app
6. **Documentazione** di tutte le policy con owner e data di review
7. **Backup delle configurazioni** via Graph API export

```powershell
# Esempio: Backup di tutte le compliance policies via Graph API
$policies = Invoke-MgGraphRequest -Method GET `
    -Uri "https://graph.microsoft.com/v1.0/deviceManagement/deviceCompliancePolicies"

$backupPath = "C:\IntuneBackup\CompliancePolicies"
New-Item -Path $backupPath -ItemType Directory -Force | Out-Null

foreach ($policy in $policies.value) {
    $fileName = "$($policy.displayName -replace '[^\w]','_').json"
    $policy | ConvertTo-Json -Depth 10 | Out-File -FilePath "$backupPath\$fileName"
}

Write-Output "Backup completato: $($policies.value.Count) policy esportate"
```

---

## Troubleshooting

### Problema 1: Enrollment fallisce con errore 0x80180026

**Causa:** L'utente ha raggiunto il limite massimo di dispositivi registrabili.

**Soluzione:**
```
1. Intune → Devices → Enrollment → Device limit restrictions
2. Aumentare il limite o rimuovere dispositivi obsoleti
3. Controllare: Get-MgDeviceManagementManagedDevice -Filter "userPrincipalName eq 'user@contoso.com'"
```

### Problema 2: Auto-enrollment non funziona (Hybrid Entra ID Join)

**Causa:** GPO non applicata, DNS CNAME mancante, o Entra ID Connect non sincronizza.

**Soluzione:**
```powershell
# 1. Verificare GPO
gpresult /r /scope:computer | findstr "MDM"

# 2. Verificare Entra ID registration
dsregcmd /status
# Cercare: AzureAdJoined: YES, DomainJoined: YES

# 3. Verificare scheduled task
Get-ScheduledTask -TaskPath "\Microsoft\Windows\EnterpriseMgmt\*"

# 4. Controllare Event Log
Get-WinEvent -LogName "Microsoft-Windows-DeviceManagement-Enterprise-Diagnostics-Provider/Admin" `
    -MaxEvents 20 | Format-List TimeCreated, Message

# 5. Verificare DNS CNAME
Resolve-DnsName -Name "EnterpriseEnrollment.contoso.com" -Type CNAME
```

### Problema 3: App Win32 non si installa — errore 0x87D1041C

**Causa:** Detection rule non configurata correttamente o installer silenzioso fallisce.

**Soluzione:**
```powershell
# 1. Controllare log IME
Get-Content "C:\ProgramData\Microsoft\IntuneManagementExtension\Logs\IntuneManagementExtension.log" `
    -Tail 200 | Select-String "error|fail|0x87"

# 2. Testare l'installer manualmente con lo stesso comando
Start-Process -FilePath "installer.exe" -ArgumentList "/S" -Wait -PassThru

# 3. Verificare detection rule manualmente
# Eseguire la stessa logica dello script di detection

# 4. Controllare che il file .intunewin sia stato creato correttamente
# Re-package se necessario
```

### Problema 4: Compliance Policy mostra "Not evaluated"

**Causa:** Il dispositivo non ha ancora effettuato check-in, oppure la policy non è assegnata.

**Soluzione:**
```powershell
# 1. Forzare sync dal dispositivo
Invoke-MgGraphRequest -Method POST `
    -Uri "https://graph.microsoft.com/v1.0/deviceManagement/managedDevices/$deviceId/syncDevice"

# 2. Verificare assignment
# Intune → Devices → [dispositivo] → Device compliance → Per-setting status

# 3. Verificare che l'utente abbia licenza Intune
Get-MgUserLicenseDetail -UserId "user@contoso.com" | Where-Object {
    $_.ServicePlans.ServicePlanName -like "*INTUNE*"
}
```

### Problema 5: Conditional Access blocca utenti legittimi

**Causa:** Dispositivo non conforme, enrollment incompleto, o policy troppo restrittiva.

**Soluzione:**
```
1. Entra ID → Sign-in logs → Filtrare per utente → Conditional Access tab
2. Identificare quale policy ha bloccato e quale condizione è fallita
3. Verificare stato compliance dispositivo in Intune
4. Se il dispositivo è nuovo, attendere completamento enrollment + compliance evaluation
5. Usare "What If" tool in Conditional Access per simulare
```

### Problema 6: Configuration Profile in stato "Error" o "Conflict"

**Causa:** Conflitto tra profili multipli che configurano la stessa impostazione, o impostazione non supportata sulla versione OS del dispositivo.

**Soluzione:**
```
1. Intune → Devices → [dispositivo] → Device configuration → Per-setting status
2. Identificare le impostazioni in errore/conflitto
3. Verificare che non ci siano profili duplicati assegnati allo stesso gruppo
4. Controllare che la versione OS supporti l'impostazione
5. Usare "Monitoring → Assignment Failures" per overview
```

### Problema 7: SCEP Certificate enrollment fallisce

**Causa:** NDES non raggiungibile, certificate template non configurato, o Certificate Connector offline.

**Soluzione:**
```powershell
# 1. Verificare Certificate Connector status
# Intune → Tenant administration → Connectors and tokens → Certificate connectors

# 2. Verificare NDES URL
Test-NetConnection -ComputerName "ndes.contoso.com" -Port 443

# 3. Controllare NDES event log sul server
Get-WinEvent -LogName "Application" -FilterXPath "*[System[Provider[@Name='NDES']]]" -MaxEvents 20

# 4. Verificare template certificate permissions
# La registration authority (NDES service account) deve avere Read + Enroll sul template

# 5. Controllare CRL validity e accessibility
certutil -verify -urlfetch "certificato.cer"
```

### Problema 8: Autopilot OOBE bloccato o molto lento

**Causa:** Connettività internet lenta, ESP timeout, o dipendenze app non soddisfatte.

**Soluzione:**
```
1. Verificare connettività: il dispositivo deve raggiungere *.manage.microsoft.com
2. Controllare ESP timeout settings (aumentare se necessario)
3. Ridurre il numero di app "Required during ESP" al minimo essenziale
4. Controllare se ci sono app Win32 con dependency chain lunghe
5. Verificare che il profilo Autopilot sia assegnato al device group corretto
6. Press Shift+F10 durante OOBE per aprire CMD e diagnosticare rete
```

### Problema 9: PowerShell script non viene eseguito

**Causa:** IME non installato, script non assegnato, o errore nello script.

**Soluzione:**
```powershell
# 1. Verificare che IME sia installato e in esecuzione
Get-Service -Name "IntuneManagementExtension"

# 2. Controllare log IME per esecuzione script
$imePath = "C:\ProgramData\Microsoft\IntuneManagementExtension\Logs"
Select-String -Path "$imePath\IntuneManagementExtension.log" -Pattern "PowerShell" -Context 3

# 3. Verificare che lo script sia assegnato
# Intune → Devices → Scripts → [script] → Device status

# 4. Testare lo script localmente
# Eseguire con lo stesso contesto (System o User) configurato
```

### Problema 10: Dispositivo non riceve policy aggiornate

**Causa:** Check-in non avvenuto, cache locale corrotta, o canale di comunicazione bloccato.

**Soluzione:**
```powershell
# 1. Forzare sync da Company Portal
# Oppure: Settings → Accounts → Access work or school → [account] → Info → Sync

# 2. Verificare ultima sincronizzazione
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Enrollments\*" | Select-Object UPN, LastSuccessfulSync

# 3. Riavviare IME
Restart-Service -Name "IntuneManagementExtension" -Force

# 4. Verificare firewall/proxy
Test-NetConnection -ComputerName "manage.microsoft.com" -Port 443

# 5. Re-enrollment se persistente
# Settings → Accounts → Access work or school → Disconnect → Reconnect
```

### Problema 11: BitLocker recovery key non salvata in Entra ID / Intune

**Causa:** Policy BitLocker non configurata per escrow, o dispositivo non ancora conforme.

**Soluzione:**
```powershell
# 1. Verificare che BitLocker sia attivo
Get-BitLockerVolume -MountPoint C: | Select-Object VolumeStatus, EncryptionPercentage, KeyProtector

# 2. Forzare backup della recovery key in Entra ID
$bitlocker = Get-BitLockerVolume -MountPoint C:
$recoveryProtector = $bitlocker.KeyProtector | Where-Object { $_.KeyProtectorType -eq "RecoveryPassword" }
BackupToAAD-BitLockerKeyProtector -MountPoint C: -KeyProtectorId $recoveryProtector.KeyProtectorId

# 3. Verificare in Intune
# Intune → Devices → [dispositivo] → Recovery keys
```

### Problema 12: App Protection Policy non applicata su BYOD

**Causa:** App non supporta MAM SDK, utente non loggato con account aziendale nell'app, o policy non assegnata.

**Soluzione:**
```
1. Verificare che l'app supporti Intune MAM SDK
2. Verificare che l'utente sia loggato nell'app con l'account aziendale
3. Verificare assignment della policy (utente nel gruppo target)
4. Controllare: Intune → Apps → Monitor → App protection status
5. L'utente deve uscire e rientrare dall'app dopo l'assegnazione della policy
```

### Problema 13: Device non appare in Intune dopo enrollment

**Causa:** Latenza di sincronizzazione, enrollment parzialmente completato, o device limit raggiunto.

**Soluzione:**
```powershell
# 1. Verificare enrollment locale
dsregcmd /status | Select-String "MDM|Enroll"

# 2. Controllare Event Log enrollment
Get-WinEvent -LogName "Microsoft-Windows-DeviceManagement-Enterprise-Diagnostics-Provider/Admin" `
    -MaxEvents 10 | Format-List

# 3. Attendere fino a 15 minuti per la prima sincronizzazione

# 4. Se persistente, ri-eseguire enrollment
# Settings → Accounts → Access work or school → Disconnect → Connect
```

### Problema 14: Proactive Remediation script fallisce

**Causa:** Errore nello script, contesto di esecuzione errato, o timeout.

**Soluzione:**
```powershell
# 1. Testare detection script localmente (come SYSTEM)
PsExec.exe -s powershell.exe -File "detection.ps1"

# 2. Controllare che l'output sia solo exit code (0 = ok, 1 = remediation needed)

# 3. Verificare timeout: default 30 secondi per detection, 60 per remediation

# 4. Controllare log IME per errori specifici
Select-String -Path "$imePath\IntuneManagementExtension.log" `
    -Pattern "HealthScript|Remediation" -Context 5
```

### Problema 15: Company Portal non mostra le app disponibili

**Causa:** Assignment non configurato come "Available", Company Portal non aggiornato, o account non nel gruppo target.

**Soluzione:**
```
1. Verificare assignment tipo = Available (non Required)
2. Verificare che l'utente sia nel gruppo target
3. Aggiornare Company Portal da Microsoft Store
4. Sync manuale: Company Portal → Impostazioni → Sync
5. Attendere fino a 24h per la prima popolazione del catalogo
```

### Problema 16: Errore 0x800705B4 durante enrollment Windows

**Causa:** Timeout durante la comunicazione con il servizio Intune.

**Soluzione:**
```powershell
# 1. Verificare connettività
$endpoints = @(
    "login.microsoftonline.com",
    "graph.windows.net",
    "manage.microsoft.com",
    "enrollment.manage.microsoft.com"
)
$endpoints | ForEach-Object {
    $result = Test-NetConnection -ComputerName $_ -Port 443
    [PSCustomObject]@{
        Endpoint = $_
        Connected = $result.TcpTestSucceeded
    }
}

# 2. Verificare proxy settings
netsh winhttp show proxy

# 3. Se dietro proxy, configurare proxy per enrollment
netsh winhttp set proxy "proxy.contoso.com:8080" "*.contoso.com;*.microsoft.com"
```

### Problema 17: Windows Update for Business ring non funzionano

**Causa:** Conflitto con GPO WSUS on-premises, o Windows Update policy non assegnata.

**Soluzione:**
```powershell
# 1. Verificare che non ci siano GPO WSUS attive
Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" -ErrorAction SilentlyContinue

# 2. Se co-management, verificare che il workload Windows Update sia su Intune

# 3. Controllare WU logs
Get-WindowsUpdateLog  # Genera WindowsUpdate.log dal file ETL

# 4. Verificare che il dispositivo sia nel ring corretto
# Intune → Devices → Windows → Update rings
```

### Problema 18: Defender for Endpoint integration non mostra risk score

**Causa:** Connettore Defender non configurato, o dispositivo non onboarded in Defender.

**Soluzione:**
```
1. Intune → Endpoint Security → Microsoft Defender for Endpoint → Connection status
2. Verificare che il connettore sia "Enabled" e "Connected"
3. Verificare onboarding: Intune → Endpoint Security → Endpoint detection and response
4. Controllare che il dispositivo appaia nel portale Defender (security.microsoft.com)
5. Se mancante, creare una configuration profile per Defender onboarding
```

### Problema 19: Enrollment Apple DEP/ADE fallisce

**Causa:** Certificato push MDM Apple scaduto, o serial number non assegnato.

**Soluzione:**
```
1. Verificare Apple MDM Push Certificate:
   Intune → Tenant administration → Connectors → Apple MDM Push Certificate
   Controllare data di scadenza (rinnovo annuale obbligatorio)
2. Verificare token DEP in Intune → Apple enrollment → Enrollment program tokens
3. Verificare che il serial number sia assegnato al profilo corretto
4. In Apple Business Manager, verificare che il server MDM sia impostato su Intune
```

### Problema 20: Multiple configuration profiles in conflitto

**Causa:** Più profili configurano la stessa impostazione con valori diversi.

**Soluzione:**
```
1. Intune → Devices → [dispositivo] → Device configuration
2. Controllare "Conflict" nella colonna stato per ogni profilo
3. Cliccare sul conflitto per vedere quale impostazione è in conflitto
4. Regola: il profilo con "winning" priority si applica
5. Best practice: consolidare impostazioni in meno profili possibili
6. Usare Settings Catalog per visibilità completa su ogni setting
```

### Strumenti di Diagnostica

```powershell
# === Tool diagnostico completo Intune ===

# 1. MDMDiagnosticsTool (built-in)
MDMDiagnosticsTool.exe -out C:\Temp\IntuneDiag

# 2. Contenuto del report diagnostico
# - MDMDiagReport.html (report leggibile)
# - Registry export delle policy MDM
# - Event logs
# - Enrollment info
# - Certificate info

# 3. Intune Diagnostic Log Collection (remoto)
# Intune → Devices → [dispositivo] → Collect diagnostics
# Raccoglie: Event logs, registry, IME logs, Autopilot logs

# 4. Graph Explorer per query avanzate
# https://developer.microsoft.com/en-us/graph/graph-explorer
```

---

## Microsoft Intune Suite — Funzionalità Avanzate

La **Intune Suite** è un bundle di add-on premium rilasciato nel 2023 e progressivamente arricchito nel 2024-2025, che estende le capacità native di Intune Plan 1 e Plan 2 con funzionalità enterprise di nuova generazione. Il bundle è disponibile come licenza aggiuntiva stand-alone oppure incluso in Microsoft 365 E5 con Intune (a seconda della data di attivazione del tenant).

### Componenti della Suite

| Componente | Funzione principale | Disponibilità stand-alone |
|---|---|---|
| **Remote Help** | Assistenza remota integrata direttamente nel portale Intune — niente più TeamViewer o Quick Assist separati. Supporta Windows, macOS e Android con controllo basato su RBAC e audit trail completo. | Sì |
| **Endpoint Privilege Management (EPM)** | Elevazione just-in-time dei privilegi senza concedere admin permanente. Consente di definire regole basate su hash del file, path, certificato publisher o attributi specifici. Registra ogni elevazione con giustificazione dell'utente. | Sì |
| **Microsoft Cloud PKI** | Infrastruttura PKI completamente cloud-managed che elimina la necessità di NDES, server SCEP on-prem e template di certificati Active Directory. | Sì |
| **Enterprise App Management** | Catalogo curato da Microsoft con app enterprise pre-pacchettizzate, aggiornamenti automatici e packaging senza necessità di `.intunewin` manuale. Include app come Adobe Acrobat, Zoom, 7-Zip e centinaia di altre. | Sì |
| **Advanced Analytics** | Analisi avanzata con anomaly detection, battery health, device query in tempo reale (KQL) e correlazione cross-dataset. Estende Endpoint Analytics con capacità proattive e predittive. | Sì |
| **Firmware-over-the-Air (FOTA)** | Gestione aggiornamenti firmware per dispositivi Android OEM (Samsung, Zebra). Consente di controllare versioni firmware, pianificare rollout graduali e bloccare downgrade non autorizzati. | No (solo suite) |

### Differenze tra Plan 1, Plan 2 e Suite

```
Plan 1 (incluso in M365 E3/E5/F1/F3):
├── MDM/MAM completo
├── Compliance policies + Conditional Access
├── App deployment (LOB, Win32, Store)
├── Configuration profiles + Settings Catalog
├── Windows Autopilot
├── Update Rings + Feature Updates
└── LAPS + Remote Actions base

Plan 2 (add-on o incluso in M365 E5 Security):
├── Tutto Plan 1 +
├── Proactive Remediations (Endpoint Analytics)
├── Tunnel for MAM (VPN per app non enrolled)
├── Specialty devices management
└── Firmware management (DFCI)

Suite (add-on separato):
├── Tutto Plan 2 +
├── Remote Help
├── EPM (Endpoint Privilege Management)
├── Cloud PKI
├── Enterprise App Management
├── Advanced Analytics + Device Query
└── FOTA (Android firmware)
```

### Attivazione e Licensing

L'attivazione della Suite richiede almeno Intune Plan 1 come prerequisito. Il licensing è **per-utente**, non per dispositivo, e copre tutti i dispositivi enrollati dall'utente. Per ambienti con molti dispositivi shared/kiosk, è disponibile una licenza dispositivo separata che include un sottoinsieme delle funzionalità Suite.

### Remote Help — Architettura

Remote Help utilizza un relay cloud Microsoft (non peer-to-peer diretto) che garantisce il funzionamento anche attraverso firewall restrittivi. L'helper deve avere un ruolo RBAC appropriato (`Remote Help Operator` o custom), e la sessione viene registrata con timestamp, durata, azioni eseguite e identità di entrambe le parti. Il consent dell'utente finale è obbligatorio prima di ogni sessione.

```powershell
# Verificare lo stato di Remote Help su un dispositivo Windows
Get-Service -Name "intune_remotehelp" | Select-Object Name, Status, StartType

# Verificare la policy Remote Help assegnata
Get-IntuneDeviceConfigurationPolicy | Where-Object {
    $_.displayName -like "*Remote Help*"
} | Select-Object displayName, assignments
```

### Enterprise App Management — Workflow

1. Accedere a **Apps → Enterprise App Catalog** nel portale Intune
2. Cercare l'app desiderata nel catalogo curato
3. Selezionare la versione — Microsoft mantiene le versioni aggiornate automaticamente
4. Definire assignment (required/available) e gruppi target
5. L'app viene distribuita come Win32 app con detection rule pre-configurata
6. Gli aggiornamenti successivi vengono applicati automaticamente secondo la policy di aggiornamento scelta (auto, manual, scheduled)

Il vantaggio principale è l'eliminazione del ciclo manuale di download → packaging → upload → test → deploy per le app di uso comune.

---

## Microsoft Cloud PKI

**Cloud PKI** è una delle componenti più impattanti della Intune Suite: sostituisce l'intera infrastruttura PKI on-premises (NDES, server SCEP, CA subordinate, template AD CS) con un servizio cloud-native completamente gestito da Microsoft.

### Architettura Cloud PKI

```
┌─────────────────────────────────────────────────────┐
│                   Microsoft Cloud                    │
│                                                     │
│  ┌──────────────┐     ┌──────────────────────────┐ │
│  │  Cloud Root   │────▶│  Cloud Issuing CA         │ │
│  │  CA (offline) │     │  (auto-managed)           │ │
│  └──────────────┘     └────────┬─────────────────┘ │
│                                │                     │
│                    ┌───────────▼────────────┐       │
│                    │  Intune Certificate     │       │
│                    │  Connector (non serve!) │       │
│                    │  → eliminato           │       │
│                    └───────────┬────────────┘       │
└────────────────────────────────┼─────────────────────┘
                                 │ SCEP profile push
                    ┌────────────▼────────────┐
                    │  Dispositivi Managed     │
                    │  (Windows/iOS/Android/   │
                    │   macOS)                 │
                    └─────────────────────────┘
```

### Confronto: PKI Tradizionale vs Cloud PKI

| Aspetto | PKI On-Prem (NDES/SCEP) | Cloud PKI |
|---|---|---|
| **Infrastruttura server** | 2-3 server (Root CA, Issuing CA, NDES) | Nessun server — tutto cloud |
| **Connector** | Intune Certificate Connector obbligatorio | Non necessario |
| **Template certificati** | AD CS template complessi | Profili SCEP semplificati nel portale |
| **Rinnovo certificati** | Manuale o script custom | Automatico, gestito dal servizio |
| **Alta disponibilità** | Load balancer + cluster CA | Built-in (SLA Microsoft) |
| **Costo operativo** | Alto (patching, monitoring, backup CA) | Incluso nella licenza Suite |
| **Revoca** | CRL/OCSP on-prem | CRL cloud-hosted, OCSP integrato |
| **Tempo di setup** | Giorni/settimane | Ore |

### Configurazione Cloud PKI

1. **Creare la Root CA cloud** — navigare a Tenant Admin → Cloud PKI → Create root CA. Definire il subject name, la validità (tipicamente 10-20 anni) e l'algoritmo (RSA 4096 o ECDSA P-256/P-384).

2. **Creare la Issuing CA** — subordinata alla Root CA. Validità tipica 5-10 anni. La Issuing CA è quella che emette i certificati verso i dispositivi.

3. **Creare un profilo SCEP** — in Devices → Configuration → Create → Certificate → SCEP certificate. Selezionare la Cloud PKI Issuing CA come autorità di emissione.

4. **Assegnare il profilo** — targetizzare gruppi di dispositivi o utenti. Il certificato viene distribuito automaticamente al prossimo check-in del dispositivo.

### Scenari di utilizzo

- **Wi-Fi EAP-TLS** — autenticazione certificato per reti corporate senza password
- **VPN always-on** — certificati per autenticazione VPN IKEv2 o SSTP
- **S/MIME email** — firma e crittografia email con certificati utente
- **Autenticazione Conditional Access** — il certificato come fattore di autenticazione forte
- **Mutual TLS per applicazioni interne** — certificati client per app LOB che richiedono mTLS

### Migrazione da NDES a Cloud PKI

La migrazione consigliata è **parallela**: si deployan nuovi profili SCEP Cloud PKI accanto a quelli esistenti NDES, si verifica che i dispositivi ricevano i nuovi certificati, e poi si ritirano gradualmente i profili NDES. Non serve mai un cutover "big bang" — i certificati NDES esistenti restano validi fino alla scadenza naturale.

```powershell
# Verificare i certificati distribuiti via Cloud PKI su un dispositivo
Get-ChildItem -Path "Cert:\CurrentUser\My" | Where-Object {
    $_.Issuer -like "*Cloud PKI*"
} | Select-Object Subject, Issuer, NotAfter, Thumbprint | Format-Table -AutoSize

# Elencare le CA cloud configurate nel tenant via Graph API
$uri = "https://graph.microsoft.com/beta/deviceManagement/cloudCertificationAuthority"
Invoke-MgGraphRequest -Method GET -Uri $uri | Select-Object -ExpandProperty value |
    Select-Object displayName, status, validityPeriodInYears
```

---

## Intune e Defender for Endpoint — Integrazione Avanzata

L'integrazione tra Microsoft Intune e Microsoft Defender for Endpoint (MDE) crea un ciclo di sicurezza chiuso: Defender rileva le minacce e valuta il rischio, Intune applica le policy di remediation e blocca l'accesso alle risorse aziendali per i dispositivi compromessi. Questa integrazione bidirezionale è il cuore della strategia **Zero Trust** di Microsoft per gli endpoint.

### Attivazione del Connettore

1. In **Endpoint Security → Microsoft Defender for Endpoint** nel portale Intune, attivare il connettore
2. In **Microsoft Defender Security Center → Settings → Advanced Features**, abilitare "Microsoft Intune connection"
3. Selezionare le piattaforme da collegare: Windows, Android, iOS/iPadOS, macOS
4. Attendere la sincronizzazione iniziale (fino a 24 ore per il primo onboarding completo)

### Flusso di Risk-Based Compliance

```
Dispositivo con malware rilevato
        │
        ▼
Defender assegna risk level "HIGH"
        │
        ▼
Intune Compliance Policy verifica:
  "Require device to be at or under machine risk score = Low"
        │
        ▼
Dispositivo marcato NON COMPLIANT
        │
        ▼
Conditional Access blocca accesso a:
  - Exchange Online
  - SharePoint/OneDrive
  - Teams
  - App LOB aziendali
        │
        ▼
Utente riceve notifica con istruzioni di remediation
        │
        ▼
Defender risolve la minaccia (auto-remediation o manuale)
        │
        ▼
Risk level torna a "Low"
        │
        ▼
Compliance restaurata → accesso ripristinato automaticamente
```

### TVM — Threat and Vulnerability Management

Le **security recommendations** di TVM possono generare **security tasks** visibili nel portale Intune. Questo consente al team IT di ricevere indicazioni mirate su:

- Software vulnerabile da aggiornare (con CVE e severity score)
- Configurazioni deboli da correggere (es. SMBv1 abilitato, firewall disabilitato)
- Credenziali esposte o deboli
- Certificati in scadenza

Il flusso è: Defender → TVM Recommendation → Security Task in Intune → Admin corregge → Task chiusa automaticamente quando Defender verifica la remediation.

### EDR — Endpoint Detection and Response Policies

Intune può distribuire policy EDR direttamente ai dispositivi senza bisogno di GPO o script:

- **Endpoint Detection and Response** — configurazione del sensore EDR, sample submission, telemetry frequency
- **Attack Surface Reduction (ASR)** — regole per bloccare macro Office malevole, processi sospetti da email, credential stealing da LSASS
- **Account Protection** — Credential Guard, LAPS enforcement
- **Device Control** — blocco/audit di USB, stampanti, dispositivi Bluetooth

```powershell
# Verificare lo stato del sensore Defender su un dispositivo
Get-MpComputerStatus | Select-Object AMRunningMode, RealTimeProtectionEnabled,
    AntivirusSignatureLastUpdated, TamperProtectionSource

# Verificare le ASR rules attive
Get-MpPreference | Select-Object -ExpandProperty AttackSurfaceReductionRules_Ids
Get-MpPreference | Select-Object -ExpandProperty AttackSurfaceReductionRules_Actions
# 0=Disabled, 1=Block, 2=Audit, 6=Warn

# Elencare i security tasks da TVM via Graph API
$uri = "https://graph.microsoft.com/beta/deviceManagement/deviceConfigurationDeviceStateSummaries"
Invoke-MgGraphRequest -Method GET -Uri $uri
```

### Intune + Defender: Anti-Tampering

La **Tamper Protection** impedisce la disabilitazione dell'antivirus da parte di malware o utenti. Quando gestita tramite Intune, la Tamper Protection è controllata centralmente dal portale e non può essere modificata localmente nemmeno da un amministratore del dispositivo. Questa configurazione si attiva in **Endpoint Security → Antivirus → Windows Security Experience → Tamper Protection = Enabled**.

---

## Windows Autopatch

**Windows Autopatch** è il servizio Microsoft che automatizza completamente la gestione degli aggiornamenti Windows, sostituendo la necessità di configurare manualmente Update Rings, feature update policies e expedited updates. Lanciato nel 2022 e rinominato/ristrutturato nell'aprile 2025, Autopatch è ora parte integrante dell'offerta Intune per le organizzazioni che vogliono un approccio "hands-off" agli aggiornamenti.

### Cosa sostituisce Autopatch

| Gestione manuale | Autopatch automatizza |
|---|---|
| Creazione manuale di Update Rings per ogni gruppo | Deployment rings predefiniti con distribuzione automatica |
| Definizione manuale dei deferral days | Deferral calcolati automaticamente in base ai dati di qualità |
| Monitoraggio manuale dei rollout failure | Rollback automatico se il tasso di errore supera la soglia |
| Feature update policies manuali | Feature updates schedulati con protezione safeguard holds |
| Expedited updates caso per caso | Hotpatch e expedited push automatici per vulnerabilità critiche |

### Deployment Rings di Autopatch

Autopatch organizza i dispositivi in **quattro ring** con progressione temporale automatica:

| Ring | Popolazione | Timing | Scopo |
|---|---|---|---|
| **Test** | ~1% dei dispositivi (scelti da admin o auto) | Giorno 0 | Validazione iniziale dell'aggiornamento in ambiente reale |
| **First** | ~5% dei dispositivi | Giorno 1-2 | Early adopter — rilevamento problemi su scala ridotta |
| **Fast** | ~15% dei dispositivi | Giorno 3-6 | Validazione su scala media prima del rollout completo |
| **Broad** | ~79% dei dispositivi | Giorno 7-14 | Rollout di massa dopo conferma stabilità nei ring precedenti |

Se un aggiornamento causa un tasso di errore anomalo (crash, BSOD, rollback) nei ring iniziali, Autopatch **pausa automaticamente** il rollout ai ring successivi e genera un alert.

### Hotpatch

Il **hotpatching** è una funzionalità esclusiva di Autopatch per Windows 11 Enterprise 24H2+ e Windows 365 che applica patch di sicurezza **senza richiedere il riavvio del dispositivo**. Il ciclo è:

- **Mesi 1, 2** → Hotpatch (no reboot)
- **Mese 3** → Aggiornamento cumulativo standard (richiede reboot)
- Ciclo si ripete

Questo riduce drasticamente i riavvii forzati da 12/anno a 4/anno, migliorando la produttività degli utenti.

### Prerequisiti Autopatch

- Licenza **Microsoft 365 E3** o superiore (Autopatch base incluso)
- Dispositivi **Windows 10/11 Enterprise** o **Education**
- Dispositivi **Entra ID joined** o **Hybrid Entra ID joined**
- **Intune** come autorità MDM
- Connettività a **Windows Update for Business deployment service** endpoints

### Configurazione

```powershell
# Verificare lo stato Autopatch di un dispositivo
$uri = "https://graph.microsoft.com/beta/admin/windows/updates/deployments"
Invoke-MgGraphRequest -Method GET -Uri $uri | Select-Object -ExpandProperty value |
    Select-Object id, state, content | Format-Table

# Elencare i deployment rings configurati
$uri = "https://graph.microsoft.com/beta/admin/windows/updates/updatableAssets"
Invoke-MgGraphRequest -Method GET -Uri $uri | Select-Object -ExpandProperty value |
    Where-Object { $_.'@odata.type' -eq '#microsoft.graph.windowsUpdates.azureADDevice' } |
    Select-Object id, enrollments | Format-Table
```

---

## Tenant Attach — Approfondimento

**Tenant Attach** è una funzionalità di Configuration Manager (ConfigMgr/SCCM) che "proietta" i dispositivi on-premises nel portale Intune, offrendo visibilità cloud e alcune azioni remote senza richiedere la migrazione completa delle workload. È il primo passo nel percorso da ConfigMgr puro verso la co-management completa.

### Tenant Attach vs Co-Management

| Aspetto | Tenant Attach | Co-Management |
|---|---|---|
| **Autorità di gestione** | ConfigMgr rimane l'unica autorità | Doppia autorità: ConfigMgr + Intune |
| **Workload migration** | Nessuna — visibilità cloud senza spostamento workload | Slider per workload: compliance, app, update ring, EPP, device config |
| **Enrollment Intune** | Non richiesto | Richiesto (auto-enrollment via Entra ID) |
| **Azioni remote dal cloud** | Limitate: sync policy, restart, CMPivot, script, timeline | Complete: wipe, retire, fresh start, compliance check, tutte le azioni |
| **Conditional Access** | Non supportato direttamente | Sì — compliance policies Intune alimentano Conditional Access |
| **Endpoint Security policies** | Sì — Antivirus, Firewall, EDR dal portale Intune | Sì — se workload EPP è spostato a Intune |
| **Requisiti infrastruttura** | ConfigMgr 2006+ con CMG opzionale | ConfigMgr 2111+ con Entra ID hybrid join |
| **Complessità setup** | Bassa (checkbox in ConfigMgr console) | Media (configurazione workload slider, enrollment, testing) |

### Funzionalità disponibili con Tenant Attach

Anche senza co-management, un dispositivo tenant-attached può:

1. **Apparire nel portale Intune** — visibilità dello stato, dell'hardware e del software installato
2. **Ricevere Endpoint Security policies** — Antivirus, Firewall, Endpoint Detection and Response direttamente dal portale cloud
3. **Eseguire CMPivot dal cloud** — query WQL/KQL in tempo reale sui dispositivi on-prem
4. **Eseguire script PowerShell dal cloud** — senza VPN o accesso diretto alla rete on-prem
5. **Visualizzare la Timeline** — log cronologico di eventi, installazioni, errori
6. **Sincronizzare le policy** — forzare un policy refresh dal portale cloud
7. **Riavviare il dispositivo** — restart remoto dal cloud

### Percorso di migrazione consigliato

```
Fase 1: Tenant Attach (settimane 1-4)
├── Abilitare upload dispositivi nel portale Intune
├── Configurare Cloud Management Gateway (CMG)
├── Verificare visibilità e azioni remote
└── Familiarizzare il team IT con il portale Intune

Fase 2: Co-Management Pilot (settimane 5-12)
├── Abilitare co-management su un gruppo pilota
├── Spostare workload "Compliance policies" a Intune
├── Spostare workload "Endpoint Protection" a Intune
├── Testare Conditional Access con compliance Intune
└── Verificare che nessuna policy ConfigMgr venga persa

Fase 3: Co-Management Broad (settimane 13-24)
├── Estendere a tutti i dispositivi Windows
├── Spostare workload rimanenti gradualmente
├── Configurare Windows Autopilot per nuovi dispositivi
└── Ridurre dipendenza da ConfigMgr

Fase 4: Cloud-Native (mesi 6-18)
├── Nuovi dispositivi → Autopilot + Intune only
├── Dispositivi esistenti → re-provision come cloud-native
├── Decommissioning graduale ConfigMgr
└── Obiettivo: zero infrastruttura on-prem per endpoint
```

### Configurazione Tenant Attach

```powershell
# In ConfigMgr PowerShell (server site):
# Verificare stato tenant attach
Get-CMTenantAttachStatus

# Verificare i dispositivi caricati nel cloud
$uri = "https://graph.microsoft.com/beta/deviceManagement/managedDevices"
Invoke-MgGraphRequest -Method GET -Uri $uri | Select-Object -ExpandProperty value |
    Where-Object { $_.managementAgent -eq "configurationManagerClientMdm" } |
    Select-Object deviceName, managementAgent, complianceState | Format-Table
```

---

## Strumenti di Troubleshooting Avanzati

Oltre ai 20 problemi comuni già documentati nella sezione Troubleshooting, questa sezione approfondisce gli strumenti diagnostici a disposizione dell'amministratore Intune per indagini complesse.

### MDMDiagnosticsTool — Utilizzo Avanzato

`MDMDiagnosticsTool.exe` è lo strumento nativo Windows per raccogliere log MDM completi dal dispositivo. Si trova in `C:\Windows\System32\` ed è disponibile su ogni dispositivo Windows 10/11.

```powershell
# Raccolta standard — crea una cartella con tutti i log MDM
MDMDiagnosticsTool.exe -out "C:\temp\MDMDiag"

# Raccolta completa con registry dump e event logs
MDMDiagnosticsTool.exe -area DeviceEnrollment;DeviceProvisioning;Autopilot -cab "C:\temp\MDMDiag.cab"

# Solo log di enrollment
MDMDiagnosticsTool.exe -area DeviceEnrollment -cab "C:\temp\enrollment.cab"

# Esportazione completa come file CAB per invio al supporto
MDMDiagnosticsTool.exe -cab "C:\temp\FullDiag.cab"
```

Il file CAB risultante contiene:
- Registry export di `HKLM\SOFTWARE\Microsoft\Enrollments`
- Event log `Microsoft-Windows-DeviceManagement-Enterprise-Diagnostics-Provider`
- Stato delle policy MDM applicate
- Certificati MDM enrollment
- Log Autopilot (se applicabile)

### Collect Diagnostics — Azione Remota

Dal portale Intune, gli amministratori possono raccogliere diagnostiche da un dispositivo senza accesso fisico:

1. Navigare a **Devices → All devices → [dispositivo] → Collect diagnostics**
2. Il dispositivo riceve il comando al prossimo check-in
3. I log vengono caricati nel portale e sono scaricabili come ZIP
4. Il file ZIP contiene: event logs, registry keys, file di configurazione MDM, output di comandi diagnostici

I log raccolti includono automaticamente: `dsregcmd /status`, `ipconfig /all`, `gpresult /H`, certificati MDM, log dell'Intune Management Extension, e molto altro.

### Event Viewer — Event ID critici

| Event ID | Source | Significato |
|---|---|---|
| **75** | DeviceManagement-Enterprise-Diagnostics-Provider | Enrollment completato con successo |
| **76** | DeviceManagement-Enterprise-Diagnostics-Provider | Enrollment fallito — il messaggio contiene il codice di errore specifico |
| **100** | DeviceManagement-Enterprise-Diagnostics-Provider | Policy sync iniziata |
| **101** | DeviceManagement-Enterprise-Diagnostics-Provider | Policy sync completata |
| **102** | DeviceManagement-Enterprise-Diagnostics-Provider | Policy sync fallita |
| **36** | DeviceManagement-Enterprise-Diagnostics-Provider | Scheduled task per MDM check-in creata |
| **208** | DeviceManagement-Enterprise-Diagnostics-Provider | CSP (Configuration Service Provider) eseguito |

```powershell
# Query eventi di enrollment nell'Event Viewer
Get-WinEvent -LogName "Microsoft-Windows-DeviceManagement-Enterprise-Diagnostics-Provider/Admin" |
    Where-Object { $_.Id -in 75,76 } |
    Select-Object TimeCreated, Id, Message | Format-Table -Wrap

# Query fallimenti di sync
Get-WinEvent -LogName "Microsoft-Windows-DeviceManagement-Enterprise-Diagnostics-Provider/Admin" |
    Where-Object { $_.Id -eq 102 } |
    Sort-Object TimeCreated -Descending | Select-Object -First 10 |
    Format-Table TimeCreated, Message -Wrap
```

### Intune Troubleshooting Blade

Il portale Intune offre una sezione dedicata in **Troubleshooting + support → Troubleshoot** dove un amministratore può:

- Cercare un utente e visualizzare **tutti** i dispositivi, le policy assegnate, lo stato di compliance, le app installate e gli errori di enrollment
- Verificare lo stato di ogni singola configurazione: Applied, Pending, Error, Conflict
- Identificare **conflitti di policy** quando due profili configurano lo stesso setting con valori diversi
- Visualizzare la **timeline degli eventi** di un dispositivo specifico
- Esportare report dettagliati in CSV

### Log dell'Intune Management Extension (IME)

L'IME è l'agent che gestisce script PowerShell, Win32 app, proactive remediations e custom compliance scripts. I log si trovano in:

```
C:\ProgramData\Microsoft\IntuneManagementExtension\Logs\
├── IntuneManagementExtension.log        ← Log principale
├── AgentExecutor.log                    ← Esecuzione script
├── ClientHealth.log                     ← Health check dell'agent
├── Sensor.log                           ← Endpoint Analytics sensor data
└── *.intunewin extraction logs          ← Estrazione app Win32
```

```powershell
# Visualizzare gli ultimi errori nel log IME
Get-Content "C:\ProgramData\Microsoft\IntuneManagementExtension\Logs\IntuneManagementExtension.log" -Tail 200 |
    Select-String -Pattern "(Error|Exception|Failed)" | Select-Object -First 20

# Verificare lo stato del servizio IME
Get-Service -Name "IntuneManagementExtension" | Select-Object Name, Status, StartType

# Forzare un restart dell'IME (riavvia il check-in)
Restart-Service -Name "IntuneManagementExtension" -Force
```

### Enrollment Failure Report

In **Devices → Monitor → Enrollment failures** è disponibile un report dettagliato che mostra:

- Utente e dispositivo coinvolto
- Data e ora del tentativo
- **Failure category**: Authentication, Authorization, Device limit, Misconfigured, Server error
- **Error code** specifico con link alla documentazione Microsoft
- OS e versione del dispositivo

Questo report è il primo punto di analisi quando si ricevono segnalazioni di enrollment falliti su larga scala.

### dsregcmd — Diagnostica Entra ID Join

```powershell
# Stato completo della registrazione Entra ID
dsregcmd /status

# Sezioni chiave da verificare:
# - AzureAdJoined: YES (per dispositivi Entra ID joined)
# - DomainJoined: YES (per hybrid join)
# - WorkplaceJoined: YES (per registered/BYOD)
# - MDMUrl: contiene l'URL di enrollment Intune
# - TenantId: deve corrispondere al tenant corretto

# Debug specifico per enrollment MDM
dsregcmd /status | Select-String -Pattern "MDM|Intune|Enrollment|Tenant"
```

### Checklist di Troubleshooting Sistematica

Per un troubleshooting strutturato, seguire questo ordine:

1. **dsregcmd /status** — verificare che il join Entra ID sia corretto
2. **Event Viewer ID 75/76** — controllare se l'enrollment è riuscito
3. **Intune Troubleshooting blade** — cercare l'utente e verificare policy/app
4. **MDMDiagnosticsTool** — raccogliere log completi dal dispositivo
5. **IME logs** — se il problema riguarda script o app Win32
6. **Collect Diagnostics** — se non si ha accesso fisico al dispositivo
7. **Graph API query** — per troubleshooting programmatico avanzato

```powershell
# Script di troubleshooting rapido — esegue tutti i check principali
$results = @{}
$results['EntraJoin'] = (dsregcmd /status | Select-String "AzureAdJoined").ToString().Trim()
$results['MDMAuthority'] = (dsregcmd /status | Select-String "MdmUrl").ToString().Trim()
$results['IMEService'] = (Get-Service IntuneManagementExtension -ErrorAction SilentlyContinue).Status
$results['LastSync'] = (Get-WinEvent -LogName "Microsoft-Windows-DeviceManagement-Enterprise-Diagnostics-Provider/Admin" -MaxEvents 1 |
    Where-Object { $_.Id -eq 101 }).TimeCreated
$results['EnrollmentCerts'] = (Get-ChildItem Cert:\LocalMachine\My | Where-Object { $_.Issuer -like "*Microsoft Intune*" }).Count

$results | Format-Table -AutoSize
```

---

## FAQ

### 1. Qual è la differenza tra MDM e MAM?

**MDM** gestisce l'intero dispositivo: può applicare policy di sicurezza (BitLocker, firewall, antivirus), distribuire app, configurare Wi-Fi/VPN, e fare wipe remoto. Richiede l'enrollment del dispositivo in Intune. **MAM** gestisce solo le app aziendali: può limitare copia/incolla, richiedere PIN per l'app, crittografare i dati dell'app, e fare selective wipe dei soli dati aziendali. Non richiede enrollment del dispositivo, ideale per BYOD.

### 2. Posso usare Intune senza Azure AD Premium?

Intune richiede almeno un tenant Entra ID (ex Azure AD). Entra ID Free è incluso con Intune e supporta enrollment base. Tuttavia, per Conditional Access, gruppi dinamici, e funzionalità avanzate è necessario **Entra ID P1** (incluso in M365 E3) o **P2** (incluso in M365 E5). Senza P1, il Conditional Access non è disponibile, riducendo significativamente il valore di Intune.

### 3. Quanti dispositivi può registrare un utente?

Il default è 15 dispositivi per utente. Questo limite è configurabile in Intune → Devices → Enrollment → Device limit restrictions. Si consiglia di ridurlo a 5 per la maggior parte delle organizzazioni per limitare la superficie di attacco.

### 4. Come funziona la compliance con il Conditional Access?

Il Conditional Access in Entra ID può richiedere che il dispositivo sia "marcato come conforme" in Intune. Quando l'utente accede a una risorsa protetta, Entra ID interroga Intune per lo stato di compliance. Se il dispositivo non è conforme, l'accesso viene bloccato. Il grace period nella compliance policy determina il tempo tra la violazione e il blocco effettivo.

### 5. Cosa succede se il dispositivo è offline?

Il dispositivo mantiene le policy in cache locale. Le app e le policy già distribuite continuano a funzionare. Tuttavia, il dispositivo non riceverà aggiornamenti alle policy fino al prossimo check-in. Se il dispositivo resta offline oltre il periodo configurato nella compliance policy (es. "offline grace period"), può essere marcato come non-conforme.

### 6. Come gestisco app LOB (Line of Business) proprietarie?

Per app LOB Windows, le opzioni sono: (1) Pacchettizzare come Win32 `.intunewin` (raccomandato per la massima flessibilità); (2) Upload diretto di `.msi`; (3) Pacchettizzare come MSIX. Per app LOB iOS/Android, upload diretto di `.ipa`/`.apk` o integrazione con store aziendale. Per MAM su app custom, integrare l'Intune App SDK o usare l'App Wrapping Tool.

### 7. Autopilot funziona senza connessione internet durante OOBE?

No. Autopilot richiede connessione internet durante OOBE per contattare il servizio Intune, scaricare il profilo, e completare l'enrollment. Per scenari senza connettività, considerare provisioning package o immagine custom con Configuration Manager.

### 8. Posso usare GPO e Intune contemporaneamente?

Si, con co-management o Hybrid Entra ID Join. Tuttavia, le GPO e le policy Intune possono entrare in conflitto. In caso di conflitto, la policy MDM (Intune) ha la precedenza per le impostazioni gestite via MDM channel. Best practice: migrare le GPO a Intune progressivamente e rimuovere le GPO conflittuali.

### 9. Come migro da SCCM a Intune?

La migrazione raccomandata è graduale tramite co-management: (1) Abilitare co-management; (2) Spostare un workload alla volta (compliance, poi device config, poi apps, ecc.); (3) Testare ogni workload con un gruppo pilota; (4) Una volta tutti i workload su Intune, valutare la rimozione del client ConfigMgr.

### 10. Come gestisco gli aggiornamenti Windows con Intune?

Intune supporta Windows Update for Business (WUfB) con: (1) **Update rings** per definire i canali di aggiornamento e i deferral; (2) **Feature update policies** per fissare la versione di feature update; (3) **Quality update policies** per accelerare gli aggiornamenti di sicurezza; (4) **Driver update policies** per gestire i driver via WUfB. Non è possibile approvare singoli aggiornamenti come in WSUS.

### 11. Come funziona la crittografia BitLocker via Intune?

Intune può: (1) Richiedere BitLocker via compliance policy; (2) Configurare BitLocker via endpoint protection profile (metodo crittografia, recovery options); (3) Eseguire il backup delle recovery key in Entra ID automaticamente; (4) Ruotare le recovery key da remoto. L'utente non deve fare nulla se la silent encryption è configurata (richiede TPM 2.0 e Secure Boot).

### 12. Posso limitare quali app gli utenti possono installare?

Su dispositivi fully managed: si, tramite Windows Defender Application Control (WDAC) o AppLocker policy distribuite via Intune. Su dispositivi BYOD con solo MAM: no, non è possibile controllare le app personali. Le App Protection Policies controllano solo i dati aziendali all'interno delle app gestite.

### 13. Come configuro il kiosk mode con Intune?

Intune supporta kiosk mode per Windows: (1) **Single-app kiosk** — il dispositivo esegue una sola app UWP a schermo intero; (2) **Multi-app kiosk** — desktop limitato con app selezionate. Configurazione: Intune → Devices → Configuration → Kiosk profile. Combinare con Autopilot Self-Deploying mode per provisioning zero-touch.

### 14. Come monitoro la conformità dell'intera flotta?

Dashboard principali: (1) Intune → Overview → Compliance status; (2) Intune → Reports → Device compliance → Noncompliant devices; (3) Intune → Reports → Organizational reports; (4) Microsoft 365 admin center → Health → Device compliance. Per reporting personalizzato, usare Graph API o Log Analytics con Intune data connector.

### 15. Qual è la differenza tra Wipe, Retire e Fresh Start?

**Wipe** = factory reset completo, rimuove tutto. Usare per dispositivi persi/rubati o cambio ownership. **Retire** = rimuove solo dati e configurazioni aziendali, preserva dati personali. Usare per BYOD o dispositivi che escono dalla gestione. **Fresh Start** = reinstalla Windows preservando l'account utente e alcune impostazioni, rimuove le app pre-installate. Usare per risolvere problemi persistenti senza perdere l'identità del dispositivo.

---

## Esercizi

1. **Lab — Compliance Policy + Conditional Access.** Creare una compliance policy che richiede BitLocker e Defender attivo. Creare una Conditional Access policy che blocca l'accesso a Exchange Online per dispositivi non conformi. Testare con un dispositivo che viola la compliance.

2. **Lab — App Protection Policy BYOD.** Configurare una APP per Outlook e Teams che: blocca copia/incolla verso app personali, richiede PIN 6 cifre, e fa wipe dopo 5 tentativi PIN falliti. Testare su dispositivo non gestito.

3. **Lab — Win32 App Deployment.** Pacchettizzare un'applicazione (es. 7-Zip o Notepad++) in formato `.intunewin`. Configurare detection rule, requirement rule, e assignment. Verificare installazione su dispositivo target.

4. **Lab — Autopilot Deployment.** Registrare un hardware hash in Intune. Creare un deployment profile user-driven con ESP. Eseguire un fresh Windows install e verificare il flusso Autopilot completo.

5. **Lab — Custom Compliance Script.** Scrivere uno script che verifica: SMBv1 disabilitato, ultimo reboot < 14 giorni, spazio disco > 10%. Associare a una compliance policy e testare.

6. **Stretch — Co-Management Setup.** In lab con Configuration Manager, abilitare co-management e spostare il workload compliance su Intune. Verificare che le policy vengano valutate da Intune.

7. **Lab — Windows Update Rings.** Configurare tre Update Rings (Pilot, Early Adopters, Produzione) con deferral crescenti. Assegnare a gruppi Entra ID separati. Creare una Feature Update Policy che blocca la versione a Windows 11 23H2 per il ring di produzione. Verificare con `Get-WindowsUpdateLog` che i deferral siano applicati.

8. **Lab — Windows LAPS.** Configurare Windows LAPS via Intune per salvare le password admin locali in Entra ID. Verificare che la password sia recuperabile dal portale Intune. Testare la rotazione post-authentication: leggere la password, usarla per un login locale, verificare che venga ruotata entro il delay configurato.

9. **Lab — DFCI + Autopilot.** Su un dispositivo Surface (o simulato): configurare un profilo DFCI che disabilita boot da USB e fotocamera. Assegnare via Autopilot. Verificare che le impostazioni UEFI siano applicate e non modificabili localmente.

10. **Lab — Reporting e Backup.** Scrivere uno script PowerShell che esporta tutte le compliance policy, configuration profile e app protection policy di un tenant Intune in file JSON. Schedulare l'esecuzione giornaliera via Azure Automation o task scheduler locale.

11. **Lab — Scope Tags e Filters.** Creare uno scenario multi-sede: definire scope tags per tre sedi (Milano, Roma, Torino). Creare ruoli delegati per ogni sede. Configurare filters per differenziare le policy per manufacturer (Lenovo vs Dell). Verificare che ogni admin veda solo gli oggetti della propria sede.

---

## Letture

- Microsoft Intune documentation — https://learn.microsoft.com/en-us/mem/intune/ (consultato: 2026-05-23)
- Intune Training modules — https://learn.microsoft.com/en-us/training/browse/?products=mem-intune (consultato: 2026-05-23)
- Windows Autopilot documentation — https://learn.microsoft.com/en-us/autopilot/ (consultato: 2026-05-23)
- Microsoft Graph API for Intune — https://learn.microsoft.com/en-us/graph/api/resources/intune-graph-overview (consultato: 2026-05-23)
- Intune community blog — https://techcommunity.microsoft.com/t5/intune-customer-success/bg-p/IntuneCustomerSuccess (consultato: 2026-05-23)
- Windows LAPS documentation — https://learn.microsoft.com/en-us/mem/intune/protect/windows-laps-overview (consultato: 2026-05-23)
- Windows Update for Business — https://learn.microsoft.com/en-us/mem/intune/protect/windows-update-for-business-configure (consultato: 2026-05-23)
- DFCI management — https://learn.microsoft.com/en-us/mem/intune/configuration/device-firmware-configuration-interface-windows (consultato: 2026-05-23)
- Endpoint Privilege Management — https://learn.microsoft.com/en-us/mem/intune/protect/epm-overview (consultato: 2026-05-23)
- Intune Reporting via Graph API — https://learn.microsoft.com/en-us/mem/intune/fundamentals/reports (consultato: 2026-05-23)

---

## Glossario

| Termine | Definizione |
|---|---|
| **MDM** | Mobile Device Management — gestione dell'intero dispositivo. |
| **MAM** | Mobile App Management — gestione delle sole app aziendali. |
| **BYOD** | Bring Your Own Device — dispositivo personale dell'utente. |
| **`.intunewin`** | Formato di pacchetto per app Win32 in Intune. |
| **APP** | App Protection Policy — policy MAM per protezione dati in-app. |
| **EPM** | Endpoint Privilege Management — elevazione JIT senza admin permanente. |
| **IME** | Intune Management Extension — agent Windows per script e Win32 app. |
| **ESP** | Enrollment Status Page — pagina di progresso durante setup Autopilot. |
| **SCEP** | Simple Certificate Enrollment Protocol — protocollo per distribuzione certificati. |
| **PKCS** | Public Key Cryptography Standards — formato certificati, alternativa a SCEP. |
| **NDES** | Network Device Enrollment Service — servizio per enrollment SCEP. |
| **WUfB** | Windows Update for Business — gestione aggiornamenti cloud-native. |
| **CMG** | Cloud Management Gateway — proxy cloud per gestione ConfigMgr via internet. |
| **OMA-URI** | Open Mobile Alliance Uniform Resource Identifier — formato per custom settings MDM. |
| **ADMX** | Administrative Template XML — formato GPO importabile in Intune. |
| **UEM** | Unified Endpoint Management — gestione unificata di tutti gli endpoint. |
| **DEP/ADE** | Device Enrollment Program / Automated Device Enrollment — enrollment automatico Apple. |
| **SWR** | Stale-While-Revalidate — pattern di caching per dati. |
| **Conditional Access** | Meccanismo Entra ID per accesso condizionale basato su stato dispositivo/utente. |
| **Compliance Policy** | Policy che definisce i requisiti minimi di sicurezza per un dispositivo. |
| **Configuration Profile** | Profilo che applica impostazioni/configurazioni al dispositivo. |
| **LAPS** | Local Administrator Password Solution — rotazione automatica della password admin locale. |
| **DFCI** | Device Firmware Configuration Interface — gestione UEFI/BIOS da remoto via Intune. |
| **Update Ring** | Gruppo di configurazione WUfB che definisce deferral e comportamento aggiornamenti. |
| **Tenant Attach** | Funzionalità ConfigMgr che carica i dati dispositivo nel cloud Intune senza co-management completo. |
| **GDAP** | Granular Delegated Admin Privileges — modello di delega per MSP/partner che gestiscono più tenant. |
| **Settings Catalog** | Interfaccia Intune con migliaia di impostazioni ricercabili per nome, alternativa ai template. |
| **Scope Tags** | Etichette RBAC che controllano la visibilità degli oggetti Intune per gli amministratori. |
| **Filters** | Regole per raffinare il targeting delle assignment basate su proprietà del dispositivo. |
| **WDAC** | Windows Defender Application Control — controllo app a livello kernel, successore di AppLocker. |
| **Expedited Update** | Aggiornamento qualità forzato che bypassa i deferral degli Update Rings. |
| **Security Baseline** | Set pre-configurato di impostazioni di sicurezza raccomandate da Microsoft. |
| **Graph API** | API RESTful di Microsoft per automazione e integrazione con servizi cloud. |
| **Scope Tags** | Etichette per delegare l'accesso a oggetti Intune per reparto/sede. |
| **Filters** | Filtri per targetizzare assignment basati su proprietà del dispositivo. |
| **Autopilot Reset** | Reset del dispositivo che preserva il profilo Autopilot e l'enrollment. |
| **Proactive Remediations** | Script automatici che rilevano e correggono problemi sui dispositivi. |
| **Cloud PKI** | Servizio PKI cloud-native della Intune Suite che elimina la necessità di NDES e CA on-premises. |
| **Autopatch** | Servizio Microsoft che automatizza il deployment degli aggiornamenti Windows con deployment rings predefiniti. |
| **Remote Help** | Strumento di assistenza remota integrato in Intune con RBAC e audit trail. |
| **TVM** | Threat and Vulnerability Management — modulo di Defender che genera security tasks per Intune. |
| **Enterprise App Management** | Catalogo curato di app pre-pacchettizzate nella Intune Suite con aggiornamenti automatici. |
| **Hotpatch** | Aggiornamento di sicurezza applicabile senza riavvio, disponibile con Autopatch su Windows 11 24H2+. |
| **EDR** | Endpoint Detection and Response — capacità avanzata di rilevamento e risposta alle minacce di Defender. |
| **ASR** | Attack Surface Reduction — regole che bloccano comportamenti tipici del malware (macro, credential stealing). |
| **CMPivot** | Strumento ConfigMgr per query WQL/KQL in tempo reale sui dispositivi, disponibile anche da cloud con tenant attach. |
| **FOTA** | Firmware-Over-The-Air — gestione aggiornamenti firmware per dispositivi Android OEM via Intune Suite. |

---

## Auto-valutazione

<details>
<summary>1. Quando un'organizzazione dovrebbe scegliere MDM completo rispetto a MAM-only?</summary>

MDM completo si usa per dispositivi corporate dove l'organizzazione necessita di controllo totale: wipe remoto, enforcement BitLocker, restrizioni hardware, distribuzione app obbligatorie. MAM-only è la scelta per BYOD: l'utente mantiene il controllo del proprio dispositivo, ma l'organizzazione protegge i dati aziendali nelle app gestite (blocco copia/incolla, PIN, selective wipe dei soli dati aziendali).
</details>

<details>
<summary>2. Come funziona una App Protection Policy e quali dati protegge?</summary>

Una APP definisce regole di protezione dati a livello di app: richiede PIN per accesso, blocca copia/incolla verso app non gestite, impedisce salvataggio su cloud personali, impone encryption dei dati app. Protegge solo i dati aziendali all'interno dell'app (es. email in Outlook, file in OneDrive), senza toccare i dati personali dell'utente. Funziona anche su dispositivi non enrolled (MAM without enrollment).
</details>

<details>
<summary>3. Qual è la differenza tra SCEP e PKCS per la distribuzione certificati?</summary>

SCEP usa un protocollo challenge-based con NDES on-premises per generare certificati individuali per ogni dispositivo — richiede infrastruttura PKI. PKCS importa certificati pre-generati o usa un connettore per emettere certificati da una CA enterprise. SCEP è più flessibile per scenari di larga scala, PKCS è più semplice quando si hanno certificati già pronti o si usa una CA cloud.
</details>

<details>
<summary>4. Come funziona Endpoint Privilege Management (EPM) e perché è preferibile all'admin permanente?</summary>

EPM consente agli utenti standard di elevare specifiche applicazioni o processi tramite approvazione JIT (just-in-time), senza assegnare diritti admin permanenti. L'utente richiede l'elevazione, il sistema verifica regole pre-configurate (hash file, certificato publisher, approvazione manager), e concede i privilegi temporaneamente. Elimina il rischio di admin locali permanenti che rappresentano un vettore di attacco per lateral movement.
</details>

<details>
<summary>5. Cosa sono i Scope Tags e i Filters in Intune e come si differenziano?</summary>

I Scope Tags controllano la visibilità amministrativa: un admin con scope tag "Milano" vede solo le policy e i dispositivi taggati "Milano". I Filters controllano il targeting delle assignment: una policy assegnata a un gruppo può essere filtrata per proprietà del dispositivo (OS version, manufacturer, enrollment profile). Scope Tags = RBAC per admin. Filters = targeting granulare per assignment.
</details>

<details>
<summary>6. Qual è il ruolo dell'Intune Management Extension (IME) e quando interviene?</summary>

L'IME è un agent installato automaticamente sui dispositivi Windows quando si assegnano script PowerShell, app Win32 o Proactive Remediations. Gestisce il download, l'installazione e il reporting di questi contenuti. Non è necessario per MDM policies native (compliance, configuration profiles), che sono gestite direttamente dal client MDM integrato in Windows.
</details>

---

## Collegamenti incrociati

- [26-intune-gestione-moderna.md](26-intune-gestione-moderna.md) — Panoramica Intune, enrollment, compliance, distribuzione app
- [13-azure-ad-identita-ibrida.md](13-azure-ad-identita-ibrida.md) — Entra ID, identità ibrida, Conditional Access
- [24-windows-defender-endpoint-security.md](24-windows-defender-endpoint-security.md) — Defender for Endpoint, integrazione compliance Intune
- [12-endpoint-management.md](12-endpoint-management.md) — Confronto strumenti endpoint management (SCCM, Intune, ibrido)
- [05-sicurezza-windows.md](05-sicurezza-windows.md) — Sicurezza OS, firewall, auditing, baseline
