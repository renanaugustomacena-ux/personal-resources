# Lab 02 — Catalogo GPO enterprise e CIS Baseline

> **Modulo di riferimento:** [21-group-policy-guida-completa.md](../21-group-policy-guida-completa.md), [05-sicurezza-windows.md](../05-sicurezza-windows.md)
> **Tempo stimato:** 3-4 ore
> **Livello:** proficient
> **Prerequisiti:** foresta AD funzionante (Lab 01 completato), almeno 1 client Windows 10/11 in dominio, moduli 02, 05, 21 completati
> **Ultimo aggiornamento:** 2026-05-23

---

## Obiettivo

Implementare un catalogo di oltre 30 GPO che copra: security baseline (CIS), gestione desktop, AppLocker/WDAC, LAPS, hardening SMB e audit avanzato. Ogni GPO segue una convenzione di naming strutturata e viene verificata con `gpresult`, RSOP e log eventi.

---

## Ambiente

- DC con foresta `corp.labexample.it` (da Lab 01)
- 1+ client Windows 10/11 Pro/Enterprise in dominio (hostname: `WS-MI-01`)
- 1 server membro per testare GPO server (hostname: `SRV-APP-01`)
- RSAT installati sul DC o su una workstation di gestione
- Group Policy Management Console (GPMC) disponibile

---

## Parte 1 — Convenzione di naming e strategia di linkaggio (20 min)

### 1.1 Definire la convenzione di naming

Formato: `{SCOPE}-{CATEGORIA}-{DESCRIZIONE}`

| Prefisso | Significato | Esempio |
|----------|-------------|---------|
| `SEC` | Security baseline | `SEC-PWD-PasswordPolicy` |
| `DSK` | Desktop management | `DSK-MAP-DriveMapping` |
| `APP` | Application control | `APP-AL-ExecutableRules` |
| `SRV` | Server settings | `SRV-SMB-HardeningSMB` |
| `AUD` | Audit policy | `AUD-ADV-AdvancedAuditPolicy` |
| `CFG` | Configuration | `CFG-LAPS-Deployment` |

### 1.2 Documentare la matrice di linkaggio OU

| GPO | Linkata a OU |
|-----|-------------|
| `SEC-PWD-PasswordPolicy` | Dominio (root) |
| `SEC-LOCK-AccountLockout` | Dominio (root) |
| `SEC-FW-WindowsFirewall` | OU=CORP |
| `DSK-MAP-DriveMapping` | OU=Workstations (Tier 2) |
| `APP-AL-ExecutableRules` | OU=Workstations (Tier 2) |
| `CFG-LAPS-Deployment` | OU=Workstations + OU=Servers |
| `SRV-SMB-HardeningSMB` | OU=CORP |
| `AUD-ADV-AdvancedAuditPolicy` | Dominio (root) |

### 1.3 Creare le GPO con PowerShell

```powershell
# Array con tutte le GPO da creare
$GPOs = @(
    "SEC-PWD-PasswordPolicy",
    "SEC-LOCK-AccountLockout",
    "SEC-FW-WindowsFirewall",
    "SEC-UA-UserAccountControl",
    "SEC-CRED-CredentialGuard",
    "SEC-LSA-LsaProtection",
    "SEC-RDP-RemoteDesktopHardening",
    "SEC-NET-NetworkAccess",
    "DSK-MAP-DriveMapping",
    "DSK-WALL-Wallpaper",
    "DSK-START-StartMenuLayout",
    "DSK-PWR-PowerSettings",
    "DSK-IE-EdgeDefaults",
    "DSK-PRNT-PrinterMapping",
    "APP-AL-ExecutableRules",
    "APP-AL-ScriptRules",
    "APP-AL-DLLRules",
    "APP-AL-MSIRules",
    "CFG-LAPS-Deployment",
    "CFG-WIN-WindowsUpdate",
    "CFG-DEF-DefenderSettings",
    "CFG-BIT-BitLockerPolicy",
    "CFG-TEL-TelemetrySettings",
    "SRV-SMB-HardeningSMB",
    "SRV-SMB-SigningEnforce",
    "SRV-RDP-ServerRDP",
    "SRV-WRM-WinRMConfig",
    "AUD-ADV-AdvancedAuditPolicy",
    "AUD-PS-PowerShellLogging",
    "AUD-LOG-EventLogSizing",
    "AUD-SYS-SysmonDeploy"
)

foreach ($gpoName in $GPOs) {
    New-GPO -Name $gpoName -Comment "GPO enterprise catalog - $gpoName"
}

# Verificare
Get-GPO -All | Where-Object { $_.DisplayName -match "^(SEC|DSK|APP|CFG|SRV|AUD)-" } |
    Sort-Object DisplayName |
    Format-Table DisplayName, Id, CreationTime
```

---

## Parte 2 — GPO Security Baseline (45 min)

### 2.1 Password Policy

Percorso GPO: `Computer Configuration > Policies > Windows Settings > Security Settings > Account Policies > Password Policy`

```powershell
# Linkare la GPO al dominio (la password policy si applica solo a livello dominio)
New-GPLink -Name "SEC-PWD-PasswordPolicy" -Target (Get-ADDomain).DistinguishedName
```

> **IMPORTANTE:** le impostazioni di password policy e account lockout risiedono nel nodo
> `Security Settings > Account Policies` della GPO e **non** sono configurabili tramite
> `Set-GPRegistryValue`. Devono essere impostate tramite la GPMC GUI:
>
> 1. Aprire `gpmc.msc`
> 2. Tasto destro su **SEC-PWD-PasswordPolicy** > **Edit**
> 3. Navigare a: `Computer Configuration > Policies > Windows Settings > Security Settings > Account Policies > Password Policy`
> 4. Configurare ogni impostazione secondo la tabella CIS seguente
>
> In alternativa, usare un security template `.inf` e importarlo nella GPO tramite
> la console Security Templates (`secpol.msc` > Import Policy). Il comando `secedit /configure`
> applica solo alla policy **locale** della macchina su cui viene eseguito, non alla GPO domain.

Template `.inf` per documentazione (importabile via GPMC > Import Policy):

```ini
[Unicode]
Unicode=yes
[System Access]
MinimumPasswordAge = 1
MaximumPasswordAge = 60
MinimumPasswordLength = 14
PasswordComplexity = 1
PasswordHistorySize = 24
ClearTextPassword = 0
LockoutBadCount = 5
ResetLockoutCount = 15
LockoutDuration = 15
```

**Impostazioni CIS raccomandate:**

| Impostazione | Valore CIS |
|-------------|-----------|
| Minimum password length | 14 caratteri |
| Password history | 24 password |
| Maximum password age | 365 giorni (o meno) |
| Minimum password age | 1 giorno |
| Complexity requirements | Abilitato |
| Account lockout threshold | 5 tentativi |
| Account lockout duration | 15 minuti |
| Reset lockout counter | 15 minuti |

> **Fonte:** <https://learn.microsoft.com/windows/security/threat-protection/security-policy-settings/password-policy>

### 2.2 Account Lockout

```powershell
New-GPLink -Name "SEC-LOCK-AccountLockout" -Target (Get-ADDomain).DistinguishedName

# Verificare la policy applicata
Get-ADDefaultDomainPasswordPolicy
```

Output atteso:

```
ComplexityEnabled           : True
LockoutDuration             : 00:15:00
LockoutObservationWindow    : 00:15:00
LockoutThreshold            : 5
MaxPasswordAge              : 60.00:00:00
MinPasswordAge              : 1.00:00:00
MinPasswordLength           : 14
PasswordHistoryCount        : 24
```

### 2.3 Windows Firewall via GPO

Percorso GPO: `Computer Configuration > Policies > Windows Settings > Security Settings > Windows Defender Firewall with Advanced Security`

```powershell
$gpoName = "SEC-FW-WindowsFirewall"
$corpDN = "OU=CORP," + (Get-ADDomain).DistinguishedName
New-GPLink -Name $gpoName -Target $corpDN

# Configurare il profilo Domain
Set-GPRegistryValue -Name $gpoName -Key "HKLM\SOFTWARE\Policies\Microsoft\WindowsFirewall\DomainProfile" `
    -ValueName "EnableFirewall" -Type DWord -Value 1
Set-GPRegistryValue -Name $gpoName -Key "HKLM\SOFTWARE\Policies\Microsoft\WindowsFirewall\DomainProfile" `
    -ValueName "DefaultInboundAction" -Type DWord -Value 1  # Block
Set-GPRegistryValue -Name $gpoName -Key "HKLM\SOFTWARE\Policies\Microsoft\WindowsFirewall\DomainProfile" `
    -ValueName "DefaultOutboundAction" -Type DWord -Value 0  # Allow

# Profilo Private
Set-GPRegistryValue -Name $gpoName -Key "HKLM\SOFTWARE\Policies\Microsoft\WindowsFirewall\PrivateProfile" `
    -ValueName "EnableFirewall" -Type DWord -Value 1
Set-GPRegistryValue -Name $gpoName -Key "HKLM\SOFTWARE\Policies\Microsoft\WindowsFirewall\PrivateProfile" `
    -ValueName "DefaultInboundAction" -Type DWord -Value 1

# Profilo Public
Set-GPRegistryValue -Name $gpoName -Key "HKLM\SOFTWARE\Policies\Microsoft\WindowsFirewall\PublicProfile" `
    -ValueName "EnableFirewall" -Type DWord -Value 1
Set-GPRegistryValue -Name $gpoName -Key "HKLM\SOFTWARE\Policies\Microsoft\WindowsFirewall\PublicProfile" `
    -ValueName "DefaultInboundAction" -Type DWord -Value 1
```

### 2.4 Audit Policy di base

Percorso GPO: `Computer Configuration > Policies > Windows Settings > Security Settings > Local Policies > Audit Policy`

```powershell
$gpoName = "AUD-ADV-AdvancedAuditPolicy"
New-GPLink -Name $gpoName -Target (Get-ADDomain).DistinguishedName

# Le audit policy avanzate si configurano meglio con auditpol o via GPMC.
# Impostare "Force audit policy subcategory settings" per sovrascrivere le legacy
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\System\CurrentControlSet\Control\Lsa" `
    -ValueName "SCENoApplyLegacyAuditPolicy" -Type DWord -Value 1
```

> Vedi Parte 7 per la configurazione completa dell'Advanced Audit Policy.

---

## Parte 3 — GPO Desktop Management (30 min)

### 3.1 Drive Mapping

Percorso GPO: `User Configuration > Preferences > Windows Settings > Drive Maps`

```powershell
$gpoName = "DSK-MAP-DriveMapping"
$tier2WsDN = "OU=Workstations,OU=Tier2-Workstations,OU=CORP," + (Get-ADDomain).DistinguishedName
New-GPLink -Name $gpoName -Target $tier2WsDN

# Il drive mapping via GPP richiede la GUI (GPMC > Preferences > Drive Maps)
# Esempio di configurazione:
# Azione: Update
# Location: \\SRV-APP-01\Shared$
# Drive Letter: S:
# Reconnect: Yes
# Label: "Condivisione Aziendale"
# Item-level targeting: Security Group "Domain Users"
```

> **Nota:** i drive mapping GPP non si configurano interamente via PowerShell. Usare GPMC per creare le voci GPP, poi verificare con `gpresult`.

### 3.2 Wallpaper aziendale

```powershell
$gpoName = "DSK-WALL-Wallpaper"
New-GPLink -Name $gpoName -Target $tier2WsDN

# Impostare il wallpaper via registry policy
Set-GPRegistryValue -Name $gpoName `
    -Key "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" `
    -ValueName "Wallpaper" -Type String -Value "\\DC-MI\NETLOGON\wallpaper\corporate.jpg"

Set-GPRegistryValue -Name $gpoName `
    -Key "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" `
    -ValueName "WallpaperStyle" -Type String -Value "10"  # 10 = Fill

# Impedire la modifica del wallpaper
Set-GPRegistryValue -Name $gpoName `
    -Key "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\ActiveDesktop" `
    -ValueName "NoChangingWallPaper" -Type DWord -Value 1
```

### 3.3 Power Settings

```powershell
$gpoName = "DSK-PWR-PowerSettings"
New-GPLink -Name $gpoName -Target $tier2WsDN

# Impedire standby quando collegato alla rete AC
# Percorso GPO: Computer Configuration > Admin Templates > System > Power Management > Sleep Settings
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SOFTWARE\Policies\Microsoft\Power\PowerSettings\29F6C1DB-86DA-48C5-9FDB-F2B67B1F44DA" `
    -ValueName "ACSettingIndex" -Type DWord -Value 0  # 0 = Never

# Spegnimento monitor dopo 15 minuti (AC)
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SOFTWARE\Policies\Microsoft\Power\PowerSettings\3C0BC021-C8A8-4E07-A973-6B14CBCB2B7E" `
    -ValueName "ACSettingIndex" -Type DWord -Value 900  # 900 secondi = 15 min
```

### 3.4 Start Menu Layout (Windows 10/11)

```powershell
$gpoName = "DSK-START-StartMenuLayout"
New-GPLink -Name $gpoName -Target $tier2WsDN

# Per Windows 11: usare il layout JSON
# Percorso GPO: User Configuration > Admin Templates > Start Menu and Taskbar
Set-GPRegistryValue -Name $gpoName `
    -Key "HKCU\Software\Policies\Microsoft\Windows\Explorer" `
    -ValueName "StartLayoutFile" -Type ExpandString `
    -Value "\\DC-MI\NETLOGON\layouts\StartMenuLayout.json"

# Nascondere app recenti
Set-GPRegistryValue -Name $gpoName `
    -Key "HKCU\Software\Policies\Microsoft\Windows\Explorer" `
    -ValueName "HideRecentlyAddedApps" -Type DWord -Value 1
```

---

## Parte 4 — AppLocker Policy (45 min)

### 4.1 Abilitare il servizio AppIDSvc

Prerequisito: il servizio Application Identity deve essere in esecuzione.

```powershell
$gpoName = "APP-AL-ExecutableRules"
$tier2WsDN = "OU=Workstations,OU=Tier2-Workstations,OU=CORP," + (Get-ADDomain).DistinguishedName
New-GPLink -Name $gpoName -Target $tier2WsDN

# Configurare il servizio AppIDSvc per l'avvio automatico via GPO
# Percorso: Computer Configuration > Windows Settings > Security Settings > System Services
# Servizio: Application Identity → Startup: Automatic
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SYSTEM\CurrentControlSet\Services\AppIDSvc" `
    -ValueName "Start" -Type DWord -Value 2  # 2 = Automatic
```

### 4.2 Creare le regole Executable

```powershell
# Generare le regole predefinite su una macchina di riferimento
Get-AppLockerPolicy -Effective -Xml | Out-File C:\Temp\current-applocker.xml

# Creare regole di default (allow per Windows e Program Files)
$defaultRules = @"
<AppLockerPolicy Version="1">
  <RuleCollection Type="Exe" EnforcementMode="AuditOnly">
    <FilePathRule Id="921cc481-6e17-4653-8f75-050b80acca20"
                  Name="(Default) All files in Windows folder"
                  Description="Allow members of Everyone to run all files in Windows."
                  UserOrGroupSid="S-1-1-0" Action="Allow">
      <Conditions>
        <FilePathCondition Path="%WINDIR%\*"/>
      </Conditions>
    </FilePathRule>
    <FilePathRule Id="a61c8b2c-a319-4cd0-9690-d2177cad7b51"
                  Name="(Default) All files in Program Files"
                  Description="Allow members of Everyone to run all files in Program Files."
                  UserOrGroupSid="S-1-1-0" Action="Allow">
      <Conditions>
        <FilePathCondition Path="%PROGRAMFILES%\*"/>
      </Conditions>
    </FilePathRule>
    <FilePublisherRule Id="b7af7102-efde-4369-8a89-7a6a392d1473"
                       Name="(Default) Microsoft signed"
                       Description="Allow Microsoft-signed executables."
                       UserOrGroupSid="S-1-1-0" Action="Allow">
      <Conditions>
        <FilePublisherCondition PublisherName="O=MICROSOFT CORPORATION*" ProductName="*" BinaryName="*">
          <BinaryVersionRange LowSection="*" HighSection="*"/>
        </FilePublisherCondition>
      </Conditions>
    </FilePublisherRule>
  </RuleCollection>
</AppLockerPolicy>
"@

$defaultRules | Out-File C:\Temp\applocker-exe.xml -Encoding UTF8
```

> **IMPORTANTE:** iniziare sempre in modalità `AuditOnly` prima di passare a `Enforce`. Monitorare l'Event Log `Microsoft-Windows-AppLocker/EXE and DLL` per verificare quali applicazioni verrebbero bloccate.

### 4.3 Regole Script

```powershell
# Percorso GPO: Computer Configuration > Windows Settings > Security Settings > Application Control Policies > AppLocker > Script Rules
# In modalità Audit:
# - Allow %WINDIR%\* per Everyone
# - Allow %PROGRAMFILES%\* per Everyone
# - Allow script firmati Microsoft per Everyone
# - Deny %USERPROFILE%\* per gruppi non amministrativi

$gpoName = "APP-AL-ScriptRules"
New-GPLink -Name $gpoName -Target $tier2WsDN
```

### 4.4 Regole DLL (opzionale, impatto prestazioni)

```powershell
$gpoName = "APP-AL-DLLRules"
New-GPLink -Name $gpoName -Target $tier2WsDN

# Le regole DLL possono impattare le prestazioni. Abilitare solo in AuditOnly inizialmente.
# Percorso GPO: Computer Configuration > Windows Settings > Security Settings >
#   Application Control Policies > AppLocker > DLL Rules
# Attivare via GPMC > AppLocker Properties > DLL Rules > Configure rule enforcement > Audit only
```

### 4.5 Verificare AppLocker

```powershell
# Sul client, dopo gpupdate
Get-AppLockerPolicy -Effective | Format-List

# Verificare gli eventi (sul client)
Get-WinEvent -LogName "Microsoft-Windows-AppLocker/EXE and DLL" -MaxEvents 20 |
    Format-Table TimeCreated, Id, Message -Wrap
```

> **Fonte:** <https://learn.microsoft.com/windows/security/application-security/application-control/app-control-for-business/applocker/applocker-overview>

---

## Parte 5 — LAPS Deployment (30 min)

### 5.1 Prerequisiti — Windows LAPS

Windows LAPS è integrato nativamente in Windows Server 2025 e Windows 11 23H2+. Per versioni precedenti, usare il client LAPS scaricabile.

```powershell
# Verificare la versione LAPS disponibile
Get-Command -Module LAPS -ErrorAction SilentlyContinue

# Aggiornare lo schema AD per Windows LAPS (richiede Schema Admin)
Update-LapsADSchema -Verbose

# Output atteso:
# VERBOSE: Adding ms-LAPS-Password attribute...
# VERBOSE: Adding ms-LAPS-PasswordExpirationTime attribute...
# VERBOSE: Adding ms-LAPS-EncryptedPassword attribute...
# VERBOSE: Modifying computer class schema...
```

### 5.2 Configurare le permission AD

```powershell
$tier2WsDN = "OU=Workstations,OU=Tier2-Workstations,OU=CORP," + (Get-ADDomain).DistinguishedName
$tier1SrvDN = "OU=Servers,OU=Tier1-Servers,OU=CORP," + (Get-ADDomain).DistinguishedName

# Permettere ai computer di aggiornare la propria password LAPS
Set-LapsADComputerSelfPermission -Identity $tier2WsDN
Set-LapsADComputerSelfPermission -Identity $tier1SrvDN

# Concedere al gruppo T2-UserAdmins la possibilità di leggere le password LAPS
Set-LapsADReadPasswordPermission -Identity $tier2WsDN `
    -AllowedPrincipals "CORP\T2-UserAdmins"

# Verificare le permission
Find-LapsADExtendedRights -Identity $tier2WsDN
```

### 5.3 Configurare la GPO LAPS

```powershell
$gpoName = "CFG-LAPS-Deployment"

# Linkare alle OU workstation e server
New-GPLink -Name $gpoName -Target $tier2WsDN
New-GPLink -Name $gpoName -Target $tier1SrvDN

# Percorso GPO: Computer Configuration > Admin Templates > System > LAPS

# Abilitare LAPS
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\LAPS" `
    -ValueName "BackupDirectory" -Type DWord -Value 2  # 2 = Active Directory

# Complessità password
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\LAPS" `
    -ValueName "PasswordComplexity" -Type DWord -Value 4  # Large+small+numbers+specials

# Lunghezza password
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\LAPS" `
    -ValueName "PasswordLength" -Type DWord -Value 20

# Età password (giorni)
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\LAPS" `
    -ValueName "PasswordAgeDays" -Type DWord -Value 30

# Nome account da gestire
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\LAPS" `
    -ValueName "AdministratorAccountName" -Type String -Value "Administrator"
```

### 5.4 Verificare LAPS

```powershell
# Sul client, dopo gpupdate /force
gpupdate /force

# Dal DC, leggere la password LAPS di un computer
Get-LapsADPassword -Identity "WS-MI-01" -AsPlainText

# Output atteso:
# ComputerName : WS-MI-01
# Password     : xK#9mP2!qR7vL5nW...
# ExpirationTimestamp : 2026-06-22 14:30:00
```

> **Fonte:** <https://learn.microsoft.com/windows-server/identity/laps/laps-overview>

---

## Parte 6 — SMB Hardening (30 min)

### 6.1 Disabilitare SMBv1

```powershell
$gpoName = "SRV-SMB-HardeningSMB"
$corpDN = "OU=CORP," + (Get-ADDomain).DistinguishedName
New-GPLink -Name $gpoName -Target $corpDN

# Disabilitare SMBv1 client
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SYSTEM\CurrentControlSet\Services\mrxsmb10" `
    -ValueName "Start" -Type DWord -Value 4  # 4 = Disabled

# Disabilitare SMBv1 server
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" `
    -ValueName "SMB1" -Type DWord -Value 0

# Verificare localmente
Get-SmbServerConfiguration | Select-Object EnableSMB1Protocol, EnableSMB2Protocol
```

### 6.2 Enforce SMB Signing

```powershell
$gpoName = "SRV-SMB-SigningEnforce"
New-GPLink -Name $gpoName -Target $corpDN

# Richiedere la firma digitale per il server SMB
# Percorso GPO: Computer Configuration > Policies > Windows Settings > Security Settings >
#   Local Policies > Security Options

# Microsoft network server: Digitally sign communications (always)
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" `
    -ValueName "RequireSecuritySignature" -Type DWord -Value 1

# Microsoft network server: Digitally sign communications (if client agrees)
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" `
    -ValueName "EnableSecuritySignature" -Type DWord -Value 1

# Microsoft network client: Digitally sign communications (always)
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" `
    -ValueName "RequireSecuritySignature" -Type DWord -Value 1

# Microsoft network client: Digitally sign communications (if server agrees)
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" `
    -ValueName "EnableSecuritySignature" -Type DWord -Value 1
```

### 6.3 Disabilitare SMB null session

```powershell
# Restringere l'accesso anonimo ai named pipe e share
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" `
    -ValueName "RestrictNullSessAccess" -Type DWord -Value 1

# Network access: Do not allow anonymous enumeration of SAM accounts
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" `
    -ValueName "RestrictAnonymousSAM" -Type DWord -Value 1

# Network access: Do not allow anonymous enumeration of SAM accounts and shares
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" `
    -ValueName "RestrictAnonymous" -Type DWord -Value 1
```

> **Fonte:** <https://learn.microsoft.com/windows-server/storage/file-server/troubleshoot/detect-enable-and-disable-smbv1-v2-v3>

---

## Parte 7 — Advanced Audit Policy Configuration (30 min)

### 7.1 Configurare le subcategory di audit

Percorso GPO: `Computer Configuration > Policies > Windows Settings > Security Settings > Advanced Audit Policy Configuration`

```powershell
$gpoName = "AUD-ADV-AdvancedAuditPolicy"

# Forzare l'uso delle subcategory (già fatto nella Parte 2)
# Configurare tramite auditpol (da applicare via GPO o script di avvio):

# Account Logon
auditpol /set /subcategory:"Credential Validation" /success:enable /failure:enable
auditpol /set /subcategory:"Kerberos Authentication Service" /success:enable /failure:enable
auditpol /set /subcategory:"Kerberos Service Ticket Operations" /success:enable /failure:enable

# Account Management
auditpol /set /subcategory:"Computer Account Management" /success:enable
auditpol /set /subcategory:"Security Group Management" /success:enable
auditpol /set /subcategory:"User Account Management" /success:enable /failure:enable

# Logon/Logoff
auditpol /set /subcategory:"Logon" /success:enable /failure:enable
auditpol /set /subcategory:"Logoff" /success:enable
auditpol /set /subcategory:"Account Lockout" /failure:enable
auditpol /set /subcategory:"Special Logon" /success:enable

# Object Access
auditpol /set /subcategory:"File System" /success:enable /failure:enable
auditpol /set /subcategory:"Registry" /success:enable /failure:enable
auditpol /set /subcategory:"SAM" /success:enable

# Policy Change
auditpol /set /subcategory:"Audit Policy Change" /success:enable /failure:enable
auditpol /set /subcategory:"Authentication Policy Change" /success:enable

# Privilege Use
auditpol /set /subcategory:"Sensitive Privilege Use" /success:enable /failure:enable

# System
auditpol /set /subcategory:"Security State Change" /success:enable
auditpol /set /subcategory:"Security System Extension" /success:enable /failure:enable
auditpol /set /subcategory:"System Integrity" /success:enable /failure:enable
```

> **Nota:** in produzione, configurare le subcategory tramite il nodo GPMC `Advanced Audit Policy Configuration`, non con `auditpol` diretto (che è locale al singolo host).

### 7.2 PowerShell Script Block Logging

```powershell
$gpoName = "AUD-PS-PowerShellLogging"
New-GPLink -Name $gpoName -Target (Get-ADDomain).DistinguishedName

# Abilitare Script Block Logging
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" `
    -ValueName "EnableScriptBlockLogging" -Type DWord -Value 1

# Abilitare Module Logging
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ModuleLogging" `
    -ValueName "EnableModuleLogging" -Type DWord -Value 1

# Loggare tutti i moduli
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ModuleLogging\ModuleNames" `
    -ValueName "*" -Type String -Value "*"

# Abilitare Transcription
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SOFTWARE\Policies\Microsoft\Windows\PowerShell\Transcription" `
    -ValueName "EnableTranscripting" -Type DWord -Value 1

Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SOFTWARE\Policies\Microsoft\Windows\PowerShell\Transcription" `
    -ValueName "OutputDirectory" -Type String -Value "\\DC-MI\PSLogs$\%COMPUTERNAME%"

Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SOFTWARE\Policies\Microsoft\Windows\PowerShell\Transcription" `
    -ValueName "EnableInvocationHeader" -Type DWord -Value 1
```

### 7.3 Event Log Sizing

```powershell
$gpoName = "AUD-LOG-EventLogSizing"
New-GPLink -Name $gpoName -Target (Get-ADDomain).DistinguishedName

# Security log: 1 GB (1048576 KB)
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SOFTWARE\Policies\Microsoft\Windows\EventLog\Security" `
    -ValueName "MaxSize" -Type DWord -Value 1048576

# System log: 256 MB
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SOFTWARE\Policies\Microsoft\Windows\EventLog\System" `
    -ValueName "MaxSize" -Type DWord -Value 262144

# Application log: 256 MB
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SOFTWARE\Policies\Microsoft\Windows\EventLog\Application" `
    -ValueName "MaxSize" -Type DWord -Value 262144

# Retention: overwrite as needed
Set-GPRegistryValue -Name $gpoName `
    -Key "HKLM\SOFTWARE\Policies\Microsoft\Windows\EventLog\Security" `
    -ValueName "Retention" -Type String -Value "0"
```

> **Fonte:** <https://learn.microsoft.com/windows/security/threat-protection/auditing/advanced-security-auditing>

---

## Parte 8 — Verifica completa (30 min)

### 8.1 Forzare l'applicazione delle GPO sul client

```powershell
# Sul client WS-MI-01
gpupdate /force

# Attendere il completamento
# Computer Policy update has completed successfully.
# User Policy update has completed successfully.
```

### 8.2 Generare report GPO con gpresult

```powershell
# Report HTML completo
gpresult /h C:\Temp\gpresult-report.html /f

# Aprire il report
Start-Process C:\Temp\gpresult-report.html

# Report testuale rapido
gpresult /r

# Report per uno specifico utente/computer
gpresult /scope:computer /v
gpresult /scope:user /v
```

### 8.3 Resultant Set of Policy (RSOP)

```powershell
# RSOP via PowerShell
Get-GPResultantSetOfPolicy -Computer "WS-MI-01" -User "CORP\mario.rossi" `
    -ReportType Html -Path "C:\Temp\rsop-report.html"

# In alternativa, per test rapido
rsop.msc  # GUI interattiva
```

### 8.4 Verificare GPO specifiche

```powershell
# Verificare la password policy effettiva
Get-ADDefaultDomainPasswordPolicy

# Verificare il firewall
Get-NetFirewallProfile | Format-Table Name, Enabled, DefaultInboundAction

# Verificare SMBv1 disabilitato
Get-SmbServerConfiguration | Select-Object EnableSMB1Protocol

# Verificare LAPS
Get-LapsADPassword -Identity "WS-MI-01" -AsPlainText

# Verificare AppLocker
Get-AppLockerPolicy -Effective | Select-Object -ExpandProperty RuleCollections

# Verificare PowerShell logging
Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" -ErrorAction SilentlyContinue

# Verificare SMB signing
Get-SmbServerConfiguration | Select-Object RequireSecuritySignature
```

### 8.5 Controllare Event Log per errori GPO

```powershell
# Errori GPO nel log System
Get-WinEvent -FilterHashtable @{
    LogName = 'System'
    ProviderName = 'Microsoft-Windows-GroupPolicy'
    Level = 2  # Error
} -MaxEvents 10 -ErrorAction SilentlyContinue |
    Format-Table TimeCreated, Id, Message -Wrap

# Eventi AppLocker
Get-WinEvent -LogName "Microsoft-Windows-AppLocker/EXE and DLL" -MaxEvents 10 -ErrorAction SilentlyContinue |
    Format-Table TimeCreated, Id, Message -Wrap

# Eventi PowerShell Script Block
Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-PowerShell/Operational'
    Id = 4104  # Script Block Logging
} -MaxEvents 5 -ErrorAction SilentlyContinue |
    Format-Table TimeCreated, Message -Wrap
```

---

## Checklist finale

- [ ] 30+ GPO create con naming convention coerente
- [ ] Password policy CIS: min 14 char, history 24, lockout 5 tentativi
- [ ] Account lockout configurato (5 tentativi, 15 min)
- [ ] Windows Firewall abilitato su tutti i profili (inbound block)
- [ ] Drive mapping, wallpaper e power settings per workstation
- [ ] AppLocker in modalità AuditOnly con regole EXE, Script, DLL
- [ ] Windows LAPS operativo: schema aggiornato, permission delegate, password leggibili
- [ ] SMBv1 disabilitato su client e server
- [ ] SMB signing obbligatorio
- [ ] Null session bloccate
- [ ] Advanced Audit Policy: logon, account mgmt, privilege use, policy change
- [ ] PowerShell Script Block Logging + Transcription abilitati
- [ ] Event log dimensionati (Security 1GB, System/App 256MB)
- [ ] `gpresult /h` senza errori di applicazione
- [ ] `rsop.msc` mostra le policy attese

---

## Riferimenti

- <https://learn.microsoft.com/windows/security/threat-protection/security-policy-settings/password-policy>
- <https://learn.microsoft.com/windows/security/application-security/application-control/app-control-for-business/applocker/applocker-overview>
- <https://learn.microsoft.com/windows-server/identity/laps/laps-overview>
- <https://learn.microsoft.com/windows-server/storage/file-server/troubleshoot/detect-enable-and-disable-smbv1-v2-v3>
- <https://learn.microsoft.com/windows/security/threat-protection/auditing/advanced-security-auditing>
- <https://learn.microsoft.com/powershell/module/grouppolicy/>
- CIS Microsoft Windows Server 2022 Benchmark v2.0 — <https://www.cisecurity.org/benchmark/microsoft_windows_server>
