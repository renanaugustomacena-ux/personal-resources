# Lab 03 — Compliance policy e Conditional Access con Intune

> **Modulo di riferimento:** [26-intune-gestione-moderna.md](../26-intune-gestione-moderna.md), [32-intune-mdm-mam.md](../32-intune-mdm-mam.md), [13-azure-ad-identita-ibrida.md](../13-azure-ad-identita-ibrida.md)
> **Tempo stimato:** 2-3 ore
> **Livello:** proficient
> **Prerequisiti:** foresta AD funzionante (Lab 01), tenant Microsoft 365 con licenze Intune Plan 1 + Entra ID P1, moduli 12, 13, 26, 32 completati
> **Ultimo aggiornamento:** 2026-05-23

---

## Obiettivo

Configurare Microsoft Intune per la gestione di dispositivi hybrid-joined: enrollment via Entra Connect, compliance policy, configuration profile, Conditional Access e App Protection Policy. Il lab copre sia le operazioni da portale Intune sia i comandi Microsoft Graph PowerShell equivalenti.

---

## Ambiente

| Componente | Dettaglio |
|------------|----------|
| DC on-premises | DC-MI (da Lab 01), dominio `corp.labexample.it` |
| Server Entra Connect | SRV-AAD-01 (Windows Server 2022, dominio-joined) |
| Tenant Entra ID | `corplab.onmicrosoft.com` |
| Dominio personalizzato | `corp.labexample.it` (verificato nel tenant) |
| Client test | WS-MI-01 (Windows 11 23H2, dominio-joined) |
| Licenze | Microsoft 365 E3/E5 o Intune Plan 1 + Entra ID P1 |

> **Prerequisito critico:** il dominio UPN `corp.labexample.it` deve essere registrato e verificato nel tenant Entra ID prima di avviare il lab.

---

## Parte 1 — Setup Entra Connect (PHS + Seamless SSO) (30 min)

### 1.1 Preparare l'ambiente on-premises

```powershell
# Su DC-MI: verificare UPN suffix
# Il dominio radice (corp.labexample.it) è già un UPN suffix valido di default.
# Aggiungere suffissi SOLO se si usa un UPN diverso dal dominio radice (es. azienda.it)
Get-ADForest | Select-Object -ExpandProperty UPNSuffixes

# Esempio: aggiungere un suffisso personalizzato (solo se necessario)
# Set-ADForest -Identity "corp.labexample.it" `
#     -UPNSuffixes @{Add="azienda.it"}

# Aggiornare gli UPN degli utenti esistenti
Get-ADUser -Filter * -SearchBase "OU=Accounts,OU=Tier2-Workstations,OU=CORP,DC=corp,DC=labexample,DC=it" |
    ForEach-Object {
        $newUPN = $_.SamAccountName + "@corp.labexample.it"
        Set-ADUser -Identity $_ -UserPrincipalName $newUPN
    }

# Verificare
Get-ADUser -Filter * -Properties UserPrincipalName |
    Select-Object Name, UserPrincipalName | Format-Table
```

### 1.2 Installare e configurare Entra Connect

Su SRV-AAD-01:

1. Scaricare Entra Connect da <https://learn.microsoft.com/entra/identity/hybrid/connect/how-to-connect-install-roadmap>
2. Eseguire `AzureADConnect.msi`
3. Selezionare **Customize** (non Express)

Configurazione guidata:

| Passaggio | Impostazione |
|-----------|-------------|
| Sign-in method | **Password Hash Synchronization (PHS)** |
| Seamless SSO | **Enable** |
| Connect to Entra ID | Credenziali Global Administrator del tenant |
| Connect directories | `corp.labexample.it` (credenziali Enterprise Admin) |
| Domain/OU filtering | **Sync selected domains and OUs** |
| OU selezionate | `OU=Accounts,OU=Tier2-Workstations,OU=CORP,...` |
| | `OU=Groups,OU=Tier2-Workstations,OU=CORP,...` |
| | Non sincronizzare Tier 0 (Domain Admins) |
| Uniquely identifying | objectGUID (default) |
| Filtering | None |
| Optional features | **Password hash synchronization**, **Password writeback** |

### 1.3 Verificare la sincronizzazione

```powershell
# Sul server Entra Connect
Import-Module ADSync

# Stato del connettore
Get-ADSyncConnectorRunStatus

# Forzare una sincronizzazione delta
Start-ADSyncSyncCycle -PolicyType Delta

# Verificare l'ultimo ciclo
Get-ADSyncScheduler

# Output atteso:
# AllowedSyncCycleInterval : 00:30:00
# CurrentlyEffectiveSyncCycleInterval : 00:30:00
# NextSyncCyclePolicyType : Delta
# NextSyncCycleStartTimeInUTC : 2026-05-23T15:30:00Z
# SyncCycleEnabled : True
```

### 1.4 Verificare Seamless SSO

```powershell
# Verificare che l'account computer AZUREADSSOACC$ esista in AD
Get-ADComputer -Filter "Name -eq 'AZUREADSSOACC'"

# Output atteso:
# DistinguishedName : CN=AZUREADSSOACC,CN=Computers,DC=corp,DC=labexample,DC=it
# Name              : AZUREADSSOACC
# Enabled           : True
```

Configurare la Intranet zone via GPO per abilitare SSO nel browser:

```powershell
$gpoName = "CFG-SSO-SeamlessSSO"
New-GPO -Name $gpoName
$tier2WsDN = "OU=Workstations,OU=Tier2-Workstations,OU=CORP," + (Get-ADDomain).DistinguishedName
New-GPLink -Name $gpoName -Target $tier2WsDN

# Aggiungere autologon.microsoftazuread-sso.com alla Intranet zone
Set-GPRegistryValue -Name $gpoName `
    -Key "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings\ZoneMap\Domains\microsoftazuread-sso.com\autologon" `
    -ValueName "https" -Type DWord -Value 1  # 1 = Intranet Zone
```

> **Fonte:** <https://learn.microsoft.com/entra/identity/hybrid/connect/how-to-connect-sso-quick-start>

---

## Parte 2 — Registrazione dispositivi Hybrid Join (20 min)

### 2.1 Configurare Hybrid Entra Join in Entra Connect

1. Rieseguire il wizard Entra Connect: `C:\Program Files\Microsoft Azure Active Directory Connect\AzureADConnect.exe`
2. Selezionare **Configure device options**
3. Selezionare **Configure Hybrid Azure AD join**
4. Selezionare il dominio `corp.labexample.it`
5. Selezionare **Windows 10+ devices**
6. SCP (Service Connection Point) viene configurato automaticamente in AD

### 2.2 Verificare il SCP in AD

```powershell
# Il SCP è registrato nel configuration container
$configDN = (Get-ADRootDSE).configurationNamingContext
Get-ADObject -Filter "objectClass -eq 'serviceConnectionPoint'" `
    -SearchBase "CN=Device Registration Configuration,CN=Services,$configDN" `
    -Properties keywords |
    Select-Object DistinguishedName, keywords

# Output atteso: keyword contenente il tenant ID
# azureADId:<tenant-guid>
# azureADName:corplab.onmicrosoft.com
```

### 2.3 Verificare l'hybrid join sul client

Sul client WS-MI-01 (dopo il riavvio e la sincronizzazione):

```powershell
# Stato del join del dispositivo
dsregcmd /status

# Cercare nella sezione "Device State":
# AzureAdJoined: YES
# DomainJoined: YES
# DeviceId: <guid>

# Tramite Microsoft Graph PowerShell (dal server di gestione)
Install-Module Microsoft.Graph.Identity.DirectoryManagement -Scope CurrentUser -Force
Connect-MgGraph -Scopes "Device.Read.All"

Get-MgDevice -Filter "displayName eq 'WS-MI-01'" |
    Select-Object DisplayName, DeviceId, TrustType, IsCompliant, IsManaged

# TrustType atteso: ServerAd (indica hybrid join)
```

> **Fonte:** <https://learn.microsoft.com/entra/identity/devices/how-to-hybrid-join>

---

## Parte 3 — Compliance Policy (30 min)

### 3.1 Creare la compliance policy dal portale Intune

Percorso: **Intune admin center** > **Devices** > **Compliance** > **Create policy**

| Piattaforma | Windows 10 and later |
|-------------|---------------------|

Impostazioni della policy:

| Sezione | Impostazione | Valore |
|---------|-------------|--------|
| Device Health | BitLocker | **Require** |
| Device Health | Secure Boot | **Require** |
| Device Health | Code integrity | **Require** |
| Device Properties | Minimum OS version | **10.0.22631** (Win 11 23H2) |
| System Security | Require a password | **Yes** |
| System Security | Minimum password length | **8** |
| System Security | Firewall | **Require** |
| System Security | Antivirus | **Require** |
| System Security | Antispyware | **Require** |
| System Security | Microsoft Defender Antimalware | **Require** |
| System Security | Real-time protection | **Require** |

### 3.2 Creare la compliance policy via Microsoft Graph PowerShell

```powershell
Install-Module Microsoft.Graph.DeviceManagement -Scope CurrentUser -Force
Connect-MgGraph -Scopes "DeviceManagementConfiguration.ReadWrite.All"

# Definire il corpo della policy
$compliancePolicyBody = @{
    "@odata.type" = "#microsoft.graph.windows10CompliancePolicy"
    displayName = "WIN-COMPLIANCE-Baseline"
    description = "Compliance baseline per dispositivi Windows hybrid-joined"
    bitLockerEnabled = $true
    secureBootEnabled = $true
    codeIntegrityEnabled = $true
    osMinimumVersion = "10.0.22631"
    passwordRequired = $true
    passwordMinimumLength = 8
    firewallEnabled = $true
    antivirusRequired = $true
    antiSpywareRequired = $true
    defenderEnabled = $true
    rtpEnabled = $true
    scheduledActionsForRule = @(
        @{
            ruleName = "PasswordRequired"
            scheduledActionConfigurations = @(
                @{
                    actionType = "block"
                    gracePeriodHours = 72  # 3 giorni di grazia
                    notificationTemplateId = ""
                }
            )
        }
    )
}

# Creare la policy
$policy = New-MgDeviceManagementDeviceCompliancePolicy -BodyParameter $compliancePolicyBody

# Verificare la creazione
Get-MgDeviceManagementDeviceCompliancePolicy |
    Select-Object DisplayName, Id, CreatedDateTime |
    Format-Table
```

### 3.3 Assegnare la policy a un gruppo

```powershell
# Creare un gruppo Entra ID per i dispositivi target
$group = New-MgGroup -DisplayName "Intune-Windows-Devices" `
    -MailEnabled:$false `
    -SecurityEnabled:$true `
    -MailNickname "intune-win-devices" `
    -GroupTypes @()

# Assegnare la compliance policy al gruppo
$assignment = @{
    target = @{
        "@odata.type" = "#microsoft.graph.groupAssignmentTarget"
        groupId = $group.Id
    }
}

New-MgDeviceManagementDeviceCompliancePolicyAssignment `
    -DeviceCompliancePolicyId $policy.Id `
    -BodyParameter $assignment
```

> **Fonte:** <https://learn.microsoft.com/mem/intune/protect/compliance-policy-create-windows>

---

## Parte 4 — Configuration Profile (30 min)

### 4.1 Profilo Wi-Fi enterprise

Percorso portale: **Intune admin center** > **Devices** > **Configuration** > **Create** > **New policy**

| Impostazione | Valore |
|-------------|--------|
| Platform | Windows 10 and later |
| Profile type | Templates > Wi-Fi |
| Wi-Fi type | Enterprise |
| SSID | `CORP-WIFI` |
| Connect automatically | Yes |
| Security type | WPA2-Enterprise |
| EAP type | EAP-TLS |
| Certificate server names | `radius.corp.labexample.it` |
| Root certificate for server validation | Certificato CA root aziendale |

### 4.2 Profilo VPN

```powershell
# Via Microsoft Graph PowerShell
$vpnProfile = @{
    "@odata.type" = "#microsoft.graph.windows10VpnConfiguration"
    displayName = "CFG-VPN-CorpAccess"
    description = "VPN Always On per accesso alla rete aziendale"
    connectionName = "CORP VPN"
    connectionType = "ikEv2"
    serverCollection = @(
        @{
            address = "vpn.corp.labexample.it"
            description = "VPN Gateway principale"
            isDefaultServer = $true
        }
    )
    authenticationMethod = "usernameAndPassword"
    enableSplitTunneling = $true
    enableAlwaysOn = $true
    dnsSuffixes = @("corp.labexample.it")
}

New-MgDeviceManagementDeviceConfiguration -BodyParameter $vpnProfile
```

### 4.3 Profilo certificato SCEP

Percorso portale: **Intune admin center** > **Devices** > **Configuration** > **Create** > **SCEP certificate**

| Impostazione | Valore |
|-------------|--------|
| Certificate type | User |
| Subject name format | `CN={{UserName}},E={{EmailAddress}}` |
| SAN | UPN = `{{UserPrincipalName}}` |
| Certificate validity period | 1 year |
| Key storage provider | Software KSP |
| Key usage | Digital signature, Key encipherment |
| Key size | 2048 |
| Hash algorithm | SHA-256 |
| Root certificate | Profilo trusted root pubblicato separatamente |
| SCEP server URLs | `https://ndes.corp.labexample.it/certsrv/mscep/mscep.dll` |

> **Prerequisito:** un'infrastruttura PKI con NDES (Network Device Enrollment Service) configurato. Vedi modulo [28-pki-certificati-guida-completa.md](../28-pki-certificati-guida-completa.md).

### 4.4 Verificare i profili assegnati

```powershell
# Elencare tutti i configuration profile
Get-MgDeviceManagementDeviceConfiguration |
    Select-Object DisplayName, "@odata.type", CreatedDateTime |
    Format-Table

# Controllare lo stato di deployment di un profilo specifico
$profileId = (Get-MgDeviceManagementDeviceConfiguration -Filter "displayName eq 'CFG-VPN-CorpAccess'").Id

Get-MgDeviceManagementDeviceConfigurationDeviceStatus -DeviceConfigurationId $profileId |
    Select-Object DeviceDisplayName, Status, LastReportedDateTime |
    Format-Table
```

> **Fonte:** <https://learn.microsoft.com/mem/intune/configuration/device-profile-create>

---

## Parte 5 — Conditional Access Policy (20 min)

### 5.1 Creare la policy "Richiedi dispositivo conforme per M365"

Percorso portale: **Entra admin center** > **Protection** > **Conditional Access** > **Create new policy**

| Sezione | Impostazione |
|---------|-------------|
| Name | `CA-001-RequireCompliantDevice-M365` |
| Users | Include: All users / Exclude: break-glass account |
| Target resources | Cloud apps > Select: Office 365 |
| Conditions | Device platforms: Windows |
| | Client apps: Browser, Mobile apps and desktop clients |
| Grant | Require device to be marked as compliant |
| Session | Sign-in frequency: 12 hours |
| Enable policy | **Report-only** (inizialmente) |

> **IMPORTANTE:** abilitare sempre in modalità **Report-only** prima del passaggio a **On**. Verificare l'impatto nei sign-in log prima di applicare.

### 5.2 Creare la policy via Microsoft Graph PowerShell

```powershell
Install-Module Microsoft.Graph.Identity.SignIns -Scope CurrentUser -Force
Connect-MgGraph -Scopes "Policy.ReadWrite.ConditionalAccess","Policy.Read.All","Application.Read.All"

# Trovare l'ID dell'app Office 365
# Office 365 Exchange Online: 00000002-0000-0ff1-ce00-000000000000
# Oppure usare l'ID aggregato "Office365"

$caPolicy = @{
    displayName = "CA-001-RequireCompliantDevice-M365"
    state = "enabledForReportingButNotEnforced"  # Report-only
    conditions = @{
        users = @{
            includeUsers = @("All")
            excludeUsers = @("<break-glass-account-object-id>")  # Sostituire con l'ID reale
        }
        applications = @{
            includeApplications = @("Office365")
        }
        platforms = @{
            includePlatforms = @("windows")
        }
        clientAppTypes = @("browser", "mobileAppsAndDesktopClients")
    }
    grantControls = @{
        operator = "OR"
        builtInControls = @("compliantDevice")
    }
    sessionControls = @{
        signInFrequency = @{
            value = 12
            type = "hours"
            isEnabled = $true
        }
    }
}

New-MgIdentityConditionalAccessPolicy -BodyParameter $caPolicy
```

### 5.3 Creare la policy per MFA fallback (dispositivi non gestiti)

```powershell
$caPolicyMFA = @{
    displayName = "CA-002-RequireMFA-UnmanagedDevices"
    state = "enabledForReportingButNotEnforced"
    conditions = @{
        users = @{
            includeUsers = @("All")
            excludeUsers = @("<break-glass-account-object-id>")
        }
        applications = @{
            includeApplications = @("All")
        }
        clientAppTypes = @("browser", "mobileAppsAndDesktopClients")
    }
    grantControls = @{
        operator = "AND"
        builtInControls = @("mfa")
    }
}

New-MgIdentityConditionalAccessPolicy -BodyParameter $caPolicyMFA
```

> **Fonte:** <https://learn.microsoft.com/entra/identity/conditional-access/howto-conditional-access-policy-compliant-device>

---

## Parte 6 — App Protection Policy (MAM) (20 min)

### 6.1 Creare la policy MAM per dispositivi non gestiti

Percorso portale: **Intune admin center** > **Apps** > **App protection policies** > **Create policy** > **Windows**

Questa policy protegge i dati aziendali nelle app M365 anche su dispositivi personali (BYOD) non registrati in Intune.

| Sezione | Impostazione | Valore |
|---------|-------------|--------|
| Name | `MAM-WIN-M365-Protection` | |
| Apps | Protected apps | Microsoft Edge, Office apps |
| Data protection | Data transfer | Allow copy/paste only to policy managed apps |
| Data protection | Receive data | Only from policy managed apps |
| Data protection | Print | Block |
| Data protection | Save copies of org data | Block (except OneDrive for Business) |
| Data protection | Encrypt org data | Require |
| Health checks | Min OS version | 10.0.22631 |
| Health checks | Max allowed device threat level | Secured |

### 6.2 Configurare la policy via Graph (parziale)

```powershell
Install-Module Microsoft.Graph.Devices.CorporateManagement -Scope CurrentUser -Force
Connect-MgGraph -Scopes "DeviceManagementApps.ReadWrite.All"

# Le app protection policy per Windows hanno struttura complessa.
# Usare il portale per la creazione iniziale, poi esportare la configurazione:
Get-MgDeviceAppManagementMdmWindowsInformationProtectionPolicy |
    Select-Object DisplayName, Id, EnforcementLevel |
    Format-Table
```

> **Nota:** la configurazione completa della MAM policy per Windows via Graph richiede una struttura JSON articolata. Il portale Intune è il metodo raccomandato per la prima configurazione. Per ambienti IaC, esportare la policy creata via portale e replicarla con Graph.

> **Fonte:** <https://learn.microsoft.com/mem/intune/apps/app-protection-policies>

---

## Parte 7 — Verifica completa (30 min)

### 7.1 Verificare lo stato di compliance del dispositivo

Dal portale Intune:
1. **Devices** > **All devices** > selezionare `WS-MI-01`
2. Verificare nella tab **Compliance** che lo stato sia **Compliant**

```powershell
Connect-MgGraph -Scopes "DeviceManagementManagedDevices.Read.All"

# Trovare il dispositivo
$device = Get-MgDeviceManagementManagedDevice -Filter "deviceName eq 'WS-MI-01'"

# Stato compliance
$device | Select-Object DeviceName, ComplianceState, LastSyncDateTime,
    OperatingSystem, OsVersion, IsEncrypted

# Output atteso:
# DeviceName      : WS-MI-01
# ComplianceState : compliant
# IsEncrypted     : True
# OsVersion       : 10.0.22631.xxxx

# Dettaglio compliance per policy
Get-MgDeviceManagementManagedDeviceCompliancePolicyState `
    -ManagedDeviceId $device.Id |
    Select-Object DisplayName, State, SettingCount |
    Format-Table
```

### 7.2 Verificare i sign-in log di Conditional Access

Dal portale Entra:
1. **Monitoring** > **Sign-in logs**
2. Filtrare per utente test
3. Cliccare su un sign-in > tab **Conditional Access**
4. Verificare che la policy `CA-001` sia elencata e che il risultato sia **Success** (per dispositivi conformi) o **Failure** (per dispositivi non conformi)

```powershell
Install-Module Microsoft.Graph.Reports -Scope CurrentUser -Force
Connect-MgGraph -Scopes "AuditLog.Read.All"

# Ultimi sign-in con risultato CA
Get-MgAuditLogSignIn -Filter "userPrincipalName eq 'mario.rossi@corp.labexample.it'" `
    -Top 10 |
    Select-Object UserDisplayName, AppDisplayName, Status,
        ConditionalAccessStatus, CreatedDateTime |
    Format-Table

# Output atteso per dispositivo conforme:
# ConditionalAccessStatus : success

# Per dispositivo non conforme:
# ConditionalAccessStatus : failure
```

### 7.3 Utilizzare il tool "What If" di Conditional Access

Percorso portale: **Entra admin center** > **Protection** > **Conditional Access** > **What If**

| Campo | Valore |
|-------|--------|
| User | `mario.rossi@corp.labexample.it` |
| Cloud app | Office 365 |
| Device platform | Windows |
| Device state | Device is Hybrid Azure AD joined, Device is compliant |
| Client app | Browser |

Risultato atteso:
- `CA-001-RequireCompliantDevice-M365` → **Will apply** (Grant: require compliant device)
- `CA-002-RequireMFA-UnmanagedDevices` → **Will not apply** (dispositivo conforme soddisfa la prima policy)

```powershell
# Il "What If" non ha un equivalente diretto in PowerShell Graph SDK.
# Usare l'API REST direttamente:
$whatIfBody = @{
    conditionalAccessWhatIfSubject = @{
        "@odata.type" = "#microsoft.graph.conditionalAccessWhatIfSubject"
        userId = "<user-object-id>"
    }
    conditionalAccessContext = @{
        "@odata.type" = "#microsoft.graph.conditionalAccessContext"
        includeApplications = @("Office365")
    }
} | ConvertTo-Json -Depth 5

# Nota: questa è una API in beta. Verificare la documentazione aggiornata.
# Invoke-MgGraphRequest -Method POST `
#     -Uri "https://graph.microsoft.com/beta/identity/conditionalAccess/evaluate" `
#     -Body $whatIfBody
```

### 7.4 Verificare sul dispositivo client

```powershell
# Stato MDM enrollment
dsregcmd /status

# Cercare nella sezione "MDM":
# MdmUrl: https://enrollment.manage.microsoft.com/enrollmentserver/discovery.svc
# MdmTouUrl: https://portal.manage.microsoft.com/TermsofUse.aspx
# MdmComplianceUrl: https://portal.manage.microsoft.com/?portalAction=Compliance

# Stato della sincronizzazione Intune
Get-ScheduledTask -TaskPath "\Microsoft\Windows\EnterpriseMgmt\*" |
    Select-Object TaskName, State, LastRunTime |
    Format-Table

# Certificati deployati via SCEP
Get-ChildItem Cert:\CurrentUser\My |
    Where-Object { $_.Issuer -match "corp.labexample" } |
    Select-Object Subject, Issuer, NotAfter, Thumbprint |
    Format-Table

# Profili Wi-Fi installati
netsh wlan show profiles
```

### 7.5 Troubleshooting

```powershell
# Event log MDM
Get-WinEvent -LogName "Microsoft-Windows-DeviceManagement-Enterprise-Diagnostics-Provider/Admin" `
    -MaxEvents 20 |
    Format-Table TimeCreated, Id, LevelDisplayName, Message -Wrap

# Forzare la sincronizzazione Intune
# Impostazioni > Account > Accesso azienda o dell'istituto di istruzione > Info > Sincronizza

# Da PowerShell (trigger sync via scheduled task)
Get-ScheduledTask -TaskPath "\Microsoft\Windows\EnterpriseMgmt\*" |
    Where-Object { $_.TaskName -match "Schedule.*created.*" } |
    Start-ScheduledTask

# Raccogliere i log diagnostici Intune
MdmDiagnosticsTool.exe -out C:\Temp\IntuneDiag
# I log vengono salvati in C:\Temp\IntuneDiag come file CAB
```

---

## Checklist finale

- [ ] Entra Connect installato con PHS + Seamless SSO
- [ ] OU filtering configurato (escluso Tier 0)
- [ ] Utenti sincronizzati con UPN corretto nel tenant Entra ID
- [ ] Account AZUREADSSOACC$ presente in AD
- [ ] SCP configurato nel configuration container AD
- [ ] Dispositivo WS-MI-01 risulta Hybrid Entra Joined (`dsregcmd /status`)
- [ ] Compliance policy creata: BitLocker, firewall, antivirus, OS version minima
- [ ] Compliance policy assegnata al gruppo dispositivi
- [ ] Configuration profile Wi-Fi enterprise creato
- [ ] Configuration profile VPN Always On creato
- [ ] Profilo certificato SCEP configurato (con NDES funzionante)
- [ ] CA policy `CA-001` in modalità Report-only: dispositivo conforme richiesto per M365
- [ ] CA policy `CA-002` in modalità Report-only: MFA per dispositivi non gestiti
- [ ] App Protection Policy per dispositivi BYOD configurata
- [ ] Sign-in log mostrano `ConditionalAccessStatus: success` per dispositivi conformi
- [ ] What If tool conferma le policy attese
- [ ] `dsregcmd /status` conferma MDM enrollment attivo

---

## Riferimenti

- <https://learn.microsoft.com/entra/identity/hybrid/connect/how-to-connect-install-roadmap>
- <https://learn.microsoft.com/entra/identity/hybrid/connect/how-to-connect-sso-quick-start>
- <https://learn.microsoft.com/entra/identity/devices/how-to-hybrid-join>
- <https://learn.microsoft.com/mem/intune/protect/compliance-policy-create-windows>
- <https://learn.microsoft.com/mem/intune/configuration/device-profile-create>
- <https://learn.microsoft.com/entra/identity/conditional-access/howto-conditional-access-policy-compliant-device>
- <https://learn.microsoft.com/mem/intune/apps/app-protection-policies>
- <https://learn.microsoft.com/graph/api/resources/intune-deviceconfig-windows10compliancepolicy>
