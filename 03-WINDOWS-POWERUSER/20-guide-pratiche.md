# Guide Pratiche Windows — Deployment, Migrazione, Hardening

> **Modulo 20** · **Aggiornamento:** 2026-05-24

> **Modulo del corso:** Amministrazione Windows enterprise
> **Prerequisiti:** [01-active-directory.md](01-active-directory.md), [05-sicurezza-windows.md](05-sicurezza-windows.md), [02-powershell.md](02-powershell.md)
> **Obiettivi di apprendimento:**
> 1. Pianificare e condurre un deployment dominio da zero con MDT, WDS e Autopilot
> 2. Eseguire migrazioni Active Directory tra domini e foreste con ADMT
> 3. Applicare hardening CIS Benchmark e STIG su server e client Windows
> 4. Progettare e testare procedure di disaster recovery enterprise
> 5. Automatizzare la manutenzione periodica con PowerShell scheduled tasks
> **Tempo stimato:** lettura 90 min · lab 180 min
> **Livello:** proficient
> **Ultimo aggiornamento:** 2026-05-24

## Idee guida
1. **MDT + WDS legacy deployment; replaced by Autopilot + Intune.**
2. **DISM per offline image servicing.**
3. **In-place upgrade vs swing migration.**
4. **CIS Benchmark Windows + STIGs per government.**
5. **Hardening = riduzione superficie d'attacco, non solo patching.**
6. **DR testato trimestrale. Un piano mai testato è un piano fallimentare.**
7. **Automazione manutenzione con PowerShell scheduled tasks.**


## Indice

- [Deployment Dominio da Zero](#deployment-dominio-da-zero)
- [Deployment Client — MDT, WDS, Autopilot](#deployment-client--mdt-wds-autopilot)
- [Migrazione Active Directory](#migrazione-active-directory)
- [Migrazione Active Directory — Scenari Avanzati](#migrazione-active-directory--scenari-avanzati)
- [Hardening Windows Server](#hardening-windows-server)
- [Hardening Windows Server — CIS Benchmark](#hardening-windows-server--cis-benchmark)
- [Hardening Windows Client](#hardening-windows-client)
- [Hardening Windows Client — Guida Approfondita](#hardening-windows-client--guida-approfondita)
- [Checklist Installazione Server](#checklist-installazione-server)
- [Disaster Recovery Procedures](#disaster-recovery-procedures)
- [Disaster Recovery — Scenari Aggiuntivi](#disaster-recovery--scenari-aggiuntivi)
- [Manutenzione Periodica](#manutenzione-periodica)
- [Automazione Manutenzione](#automazione-manutenzione)
- [Scenari Reali Enterprise](#scenari-reali-enterprise)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [WPR/WPA — Tracciamento Performance Avanzato](#wprwpa--tracciamento-performance-avanzato)
- [Sysinternals — Analisi Approfondita](#sysinternals--analisi-approfondita)
- [DISM — Operazioni Avanzate e Component Store](#dism--operazioni-avanzate-e-component-store)
- [WinRE — Ambiente di Ripristino Avanzato](#winre--ambiente-di-ripristino-avanzato)
- [Event Log — Analisi Forense Avanzata](#event-log--analisi-forense-avanzata)

---

## Deployment Dominio da Zero

### Procedura Completa

```powershell
# =====================================================
# FASE 1: PREPARAZIONE INFRASTRUTTURA
# =====================================================

# 1.1 Naming Convention (definire PRIMA di tutto)
# Dominio: corp.contoso.com
# Server: <ruolo><sede><num> → DC01-MI, SRV01-MI, CA01-MI
# Workstation: WKS-<reparto>-<num> → WKS-IT-001
# Gruppi Security: GG-<nome> (Global), DL-<risorsa>-<permesso> (Domain Local)
# GPO: <tipo>-<target>-<funzione> → SEC-Workstation-BitLocker

# 1.2 Configurare primo server (DC01)
# - Installare Windows Server 2022
# - Configurare IP statico: 192.168.10.10/24
# - Gateway: 192.168.10.1
# - DNS: 127.0.0.1 (punterà a se stesso dopo l'installazione DNS)
# - Rinominare: Rename-Computer -NewName "DC01" -Restart

# =====================================================
# FASE 2: INSTALLAZIONE ACTIVE DIRECTORY
# =====================================================

# 2.1 Installare ruoli
Install-WindowsFeature AD-Domain-Services, DNS, DHCP -IncludeManagementTools

# 2.2 Promuovere a Domain Controller (nuova foresta)
$password = ConvertTo-SecureString "DSRMpassw0rd!" -AsPlainText -Force
Install-ADDSForest -DomainName "corp.contoso.com" `
    -DomainNetbiosName "CORP" `
    -ForestMode "WinThreshold" `
    -DomainMode "WinThreshold" `
    -InstallDns:$true `
    -SafeModeAdministratorPassword $password `
    -Force:$true
# Riavvio automatico

# 2.3 Post-installazione DC
# Configurare DNS: reverse zone
Add-DnsServerPrimaryZone -NetworkID "192.168.10.0/24" -ReplicationScope Domain

# Configurare DHCP
Add-DhcpServerInDC -DnsName "DC01.corp.contoso.com" -IPAddress 192.168.10.10
Add-DhcpServerv4Scope -Name "LAN" -StartRange 192.168.10.100 `
    -EndRange 192.168.10.250 -SubnetMask 255.255.255.0 -State Active
Set-DhcpServerv4OptionValue -ScopeId 192.168.10.0 `
    -Router 192.168.10.1 -DnsServer 192.168.10.10 -DnsDomain "corp.contoso.com"

# =====================================================
# FASE 3: SECONDO DC (RIDONDANZA)
# =====================================================

# 3.1 Su DC02 (IP: 192.168.10.11, DNS: 192.168.10.10)
Install-WindowsFeature AD-Domain-Services, DNS -IncludeManagementTools

$cred = Get-Credential  # CORP\Administrator
Install-ADDSDomainController -DomainName "corp.contoso.com" `
    -Credential $cred `
    -InstallDns:$true `
    -SafeModeAdministratorPassword $password `
    -Force:$true

# 3.2 Aggiornare DNS sui client per usare entrambi i DC
# DC01 DNS primario: 192.168.10.11 (punta all'altro), secondario: 127.0.0.1
# DC02 DNS primario: 192.168.10.10 (punta all'altro), secondario: 127.0.0.1

# 3.3 DHCP failover
Add-DhcpServerv4Failover -ComputerName DC01 -PartnerServer DC02 `
    -Name "DHCP-Failover" -ScopeId 192.168.10.0 `
    -SharedSecret "F@il0verSecret!" -Mode HotStandby -AutoStateTransition $true

# =====================================================
# FASE 4: STRUTTURA AD
# =====================================================

# 4.1 Creare OU
$base = "DC=corp,DC=contoso,DC=com"
$topOUs = @("Admin", "Utenti", "Computer", "Server", "Gruppi", "ServiceAccounts")
foreach ($ou in $topOUs) {
    New-ADOrganizationalUnit -Name $ou -Path $base -ProtectedFromAccidentalDeletion $true
}
# Sub-OU per utenti per sede
New-ADOrganizationalUnit -Name "Milano" -Path "OU=Utenti,$base"
New-ADOrganizationalUnit -Name "Roma" -Path "OU=Utenti,$base"

# 4.2 Creare gruppi base
New-ADGroup -Name "GG-IT-Staff" -GroupScope Global -GroupCategory Security `
    -Path "OU=Gruppi,$base"
New-ADGroup -Name "GG-All-Users" -GroupScope Global -GroupCategory Security `
    -Path "OU=Gruppi,$base"
New-ADGroup -Name "DL-FileShare-ReadWrite" -GroupScope DomainLocal -GroupCategory Security `
    -Path "OU=Gruppi,$base"

# 4.3 Abilitare AD Recycle Bin
Enable-ADOptionalFeature "Recycle Bin Feature" -Scope ForestOrConfigurationSet `
    -Target "corp.contoso.com" -Confirm:$false

# =====================================================
# FASE 5: GPO BASE
# =====================================================

# 5.1 Password Policy (sul Default Domain Policy)
Set-ADDefaultDomainPasswordPolicy -Identity "corp.contoso.com" `
    -MinPasswordLength 12 -ComplexityEnabled $true `
    -MaxPasswordAge "90.00:00:00" -MinPasswordAge "1.00:00:00" `
    -LockoutThreshold 5 -LockoutDuration "00:30:00" `
    -LockoutObservationWindow "00:30:00" -PasswordHistoryCount 24

# 5.2 Creare GPO principali
# SEC-Workstation-BaseConfig, SEC-Server-BaseConfig, SEC-AllUsers-BaseConfig
# Configurare via GPMC (gpmc.msc)
```

---

## Deployment Client — MDT, WDS, Autopilot

### MDT + WDS (Legacy ma ancora diffuso)

```powershell
# ============================================================
# MDT (Microsoft Deployment Toolkit) — SETUP COMPLETO
# ============================================================

# Prerequisiti:
# - Windows Server 2022 con WDS role
# - Windows ADK + WinPE add-on
# - MDT installato (download gratuito Microsoft)

# 1. Creare Deployment Share
New-Item "D:\DeploymentShare" -ItemType Directory
# MDT Deployment Workbench → New Deployment Share
# Path: D:\DeploymentShare
# Share Name: DeploymentShare$
# Description: "Deployment Windows Enterprise"

# 2. Importare OS
# Deployment Workbench → Operating Systems → Import
# Source: ISO Windows 11 Enterprise montata

# 3. Importare Application
# Deployment Workbench → Applications → New Application
# Tipo: Application with source files
# Source: \\SRV01\Software\Office365
# Command: setup.exe /configure configuration.xml

# 4. Creare Task Sequence
# Deployment Workbench → Task Sequences → New
# Template: Standard Client Task Sequence
# Nome: "Win11-Enterprise-Standard"
# OS: Windows 11 Enterprise selezionato al passo 2

# 5. Configurare CustomSettings.ini
# D:\DeploymentShare\Control\CustomSettings.ini
$customSettings = @'
[Settings]
Priority=TaskSequenceID, Make, Default

[Default]
OSInstall=Y
SkipBDDWelcome=YES
SkipTaskSequence=NO
SkipComputerName=NO
SkipDomainMembership=NO
SkipUserData=YES
SkipLocaleSelection=YES
SkipTimeZone=YES
SkipApplications=NO
SkipBitLocker=YES
SkipSummary=YES
SkipCapture=YES
SkipFinalSummary=NO

TimeZoneName=W. Europe Standard Time
UILanguage=it-IT
UserLocale=it-IT
KeyboardLocale=0410:00000410

JoinDomain=corp.contoso.com
DomainAdmin=CORP\svc-mdt-join
DomainAdminPassword=<password>
MachineObjectOU=OU=Computer,DC=corp,DC=contoso,DC=com

WSUSServer=http://wsus.corp.contoso.com:8530

SLShare=\\SRV01\Logs$\%ComputerName%
EventService=http://SRV01:9800
'@

# 6. Configurare Bootstrap.ini
$bootstrap = @'
[Settings]
Priority=Default

[Default]
DeployRoot=\\SRV01\DeploymentShare$
UserDomain=CORP
UserID=svc-mdt-deploy
UserPassword=<password>
SkipBDDWelcome=YES
'@

# 7. Update Deployment Share (genera boot image WinPE)
# Deployment Workbench → Tasto destro su share → Update
# Genera LiteTouchPE_x64.wim e .iso

# 8. Importare boot image in WDS
# WDS Console → Boot Images → Add Boot Image
# File: D:\DeploymentShare\Boot\LiteTouchPE_x64.wim
```

### Windows Autopilot (Moderno)

```powershell
# Autopilot è il sostituto moderno di MDT per il provisioning
# Il PC viene configurato "out of the box" senza imaging

# ============================================================
# AUTOPILOT WORKFLOW
# ============================================================
#
# ┌────────────────────────────────────────────────────┐
# │  1. OEM / Vendor registra il device in Autopilot   │
# │     (Hardware Hash → Intune → Autopilot Devices)   │
# ├────────────────────────────────────────────────────┤
# │  2. Admin configura Autopilot Profile in Intune     │
# │     - Deployment mode: User-Driven / Self-Deploy   │
# │     - Join type: Azure AD / Hybrid Azure AD         │
# │     - OOBE settings: skip privacy, EULA, etc.      │
# ├────────────────────────────────────────────────────┤
# │  3. Utente accende il PC e si connette a Internet   │
# │     - OOBE mostra branding aziendale               │
# │     - Utente inserisce credenziali Azure AD         │
# ├────────────────────────────────────────────────────┤
# │  4. Intune applica configurazioni e app             │
# │     - Compliance policies                          │
# │     - Configuration profiles                       │
# │     - App deployment (Win32, LOB, Store)            │
# │     - Security baselines                           │
# ├────────────────────────────────────────────────────┤
# │  5. PC pronto all'uso (30-60 minuti tipici)         │
# └────────────────────────────────────────────────────┘

# Registrare device manualmente (se non registrato dall'OEM)
# 1. Raccogliere Hardware Hash:
Install-Script -Name Get-WindowsAutoPilotInfo -Force
Get-WindowsAutoPilotInfo -OutputFile "C:\Temp\autopilot.csv"

# 2. Importare in Intune:
# Endpoint Manager → Devices → Windows → Enrollment → Devices
# Import → CSV con Serial Number, Hardware Hash, Group Tag

# Autopilot Profile — PowerShell Graph API
# Connect-MgGraph -Scopes "DeviceManagementServiceConfig.ReadWrite.All"
# Oppure configurare via Intune portal:
# Devices → Windows → Enrollment → Deployment Profiles → Create

# Autopilot Deployment Modes:
# User-Driven:   L'utente si autentica all'OOBE. Più comune.
# Self-Deploying: Zero-touch, il device si configura da solo (chioschi, sale riunioni).
# Pre-provisioned: Il tecnico IT prepara il device, l'utente completa in 5 minuti.
```

---

## Migrazione Active Directory

### Migrazione Domain Controller (in-place upgrade)

```powershell
# Scenario: Windows Server 2016 → Windows Server 2022

# 1. PREPARAZIONE
# - Backup System State di tutti i DC
# - Verificare salute AD: dcdiag /v /c /e
# - Verificare replica: repadmin /replsummary
# - Documentare FSMO roles: netdom query fsmo

# 2. AGGIUNGERE NUOVO DC (Windows Server 2022)
# Installare WS2022, join al dominio, promuovere a DC
Install-ADDSDomainController -DomainName "corp.contoso.com" `
    -InstallDns:$true -Credential (Get-Credential) -Force

# 3. TRASFERIRE FSMO ROLES al nuovo DC
Move-ADDirectoryServerOperationMasterRole -Identity "DC-NEW" `
    -OperationMasterRole SchemaMaster, DomainNamingMaster, `
        PDCEmulator, RIDMaster, InfrastructureMaster

# 4. VERIFICARE
netdom query fsmo
dcdiag /v /s:DC-NEW
repadmin /replsummary

# 5. DEMOTARE VECCHIO DC
Uninstall-ADDSDomainController -DemoteOperationMasterRole -Force

# 6. ALZARE LIVELLO FUNZIONALE (dopo che TUTTI i DC sono WS2022)
Set-ADDomainMode -Identity "corp.contoso.com" -DomainMode Windows2016Domain
Set-ADForestMode -Identity "corp.contoso.com" -ForestMode Windows2016Forest

# 7. CLEANUP
# - Rimuovere vecchi DC da AD Sites and Services
# - Pulire DNS records dei vecchi DC
# - Aggiornare DHCP options per puntare ai nuovi DC
```

---

## Migrazione Active Directory — Scenari Avanzati

### Migrazione Cross-Forest (ADMT)

```powershell
# ============================================================
# MIGRAZIONE CROSS-FOREST CON ADMT
# (Active Directory Migration Tool)
# ============================================================
#
# Scenario: Acquisizione aziendale
# Source forest: alpha.com
# Target forest: corp.contoso.com
# Obiettivo: migrare utenti, gruppi, computer da alpha a corp

# PREREQUISITI:
# 1. Forest trust bidirezionale tra alpha.com e corp.contoso.com
# 2. SID Filtering disabilitato sul trust (per SID History)
#    netdom trust alpha.com /domain:corp.contoso.com /quarantine:no
# 3. Auditing abilitato su entrambi i domini:
#    auditpol /set /subcategory:"Account Management" /success:enable /failure:enable
# 4. ADMT installato su un server nel dominio target
# 5. SQL Server (Express o Standard) per il database ADMT

# FASI MIGRAZIONE:

# FASE 1: Migrazione gruppi (prima degli utenti!)
# ADMT → Group Account Migration
# - Source domain: alpha.com
# - Target domain: corp.contoso.com
# - Target OU: OU=Migrated,OU=Gruppi,DC=corp,DC=contoso,DC=com
# - Migrate group SIDs to target domain: Yes (SID History)
# - Fix group membership: Yes
# - Copy group members: No (saranno migrati dopo)

# FASE 2: Migrazione utenti
# ADMT → User Account Migration
# - Source domain: alpha.com
# - Target OU: OU=Migrated,OU=Utenti,DC=corp,DC=contoso,DC=com
# - Migrate user SIDs: Yes (SID History)
# - Transition to target: Disable source account
# - Password migration: require DES
# - Generate complex passwords: Yes (se non si usa password migration)
# - Update previously migrated objects: Yes

# FASE 3: Migrazione computer
# ADMT → Computer Migration
# - Target OU: OU=Migrated,OU=Computer,DC=corp,DC=contoso,DC=com
# - Translate roaming profiles: Yes
# - Restart computer after migration: 5 minutes delay

# FASE 4: Security Translation
# ADMT → Security Translation Wizard
# - Tradurre ACL su file server, stampanti, share
# - Add mode: aggiunge ACE per nuovo SID mantenendo il vecchio
# - Replace mode: sostituisce vecchio SID con nuovo (fase finale)

# POST-MIGRAZIONE:
# 1. Verificare accessi utenti: possono accedere a risorse in entrambi i domini?
# 2. SID History: gli utenti migrati hanno accesso via SID History
# 3. Dopo 90 giorni: cleanup SID History (opzionale, per sicurezza)
# 4. Rimuovere forest trust quando la migrazione è completa
```

### Consolidamento Domini (Multi-Domain → Single Domain)

```powershell
# Scenario: 3 domini figlio da consolidare nel root domain
# child1.corp.contoso.com → corp.contoso.com
# child2.corp.contoso.com → corp.contoso.com

# PIANO:
# 1. Inventario completo di utenti, gruppi, GPO, risorse per ogni dominio
# 2. Creare OU structure nel target per ogni dominio sorgente
# 3. Migrare con ADMT (ordine: gruppi → utenti → computer)
# 4. Tradurre security su file server e risorse
# 5. Migrare GPO: backup da sorgente → import nel target con ADMT
# 6. Aggiornare DNS, DHCP, applicazioni che puntano al vecchio dominio
# 7. Decommissionare DC dei domini figlio
# 8. Rimuovere i domini figlio dalla foresta

# Migrazione GPO cross-domain:
# Export GPO dal dominio sorgente
Backup-GPO -Name "SEC-Workstation-BitLocker" -Path "C:\GPO-Backup" -Domain "child1.corp.contoso.com"

# Import nel dominio target (con migration table per SID/path)
Import-GPO -BackupGPOName "SEC-Workstation-BitLocker" -Path "C:\GPO-Backup" `
    -TargetName "SEC-Workstation-BitLocker-Migrated" `
    -MigrationTable "C:\GPO-Backup\migration.migtable" `
    -CreateIfNeeded
```

---

## Hardening Windows Server

```powershell
# =====================================================
# CHECKLIST HARDENING SERVER
# =====================================================

# 1. AGGIORNAMENTI
# - Installare tutte le patch correnti
# - Configurare WSUS o WUfB per aggiornamenti automatici

# 2. SERVIZI — Disabilitare non necessari
$servicesToDisable = @(
    "Spooler",         # Se non si stampa
    "RemoteRegistry",  # Se non serve
    "XboxGipSvc",      # Xbox (irrilevante su server)
    "XblAuthManager",
    "XblGameSave"
)
foreach ($svc in $servicesToDisable) {
    Set-Service -Name $svc -StartupType Disabled -ErrorAction SilentlyContinue
    Stop-Service -Name $svc -Force -ErrorAction SilentlyContinue
}

# 3. PROTOCOLLI LEGACY — Disabilitare
# SMBv1
Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart
# LLMNR
New-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" `
    -Name "EnableMulticast" -Value 0 -PropertyType DWord -Force
# NetBIOS (per ogni adattatore)
$adapters = Get-ChildItem "HKLM:\SYSTEM\CurrentControlSet\Services\NetBT\Parameters\Interfaces"
foreach ($a in $adapters) { Set-ItemProperty $a.PSPath -Name "NetbiosOptions" -Value 2 }

# 4. FIREWALL
Set-NetFirewallProfile -Profile Domain, Private, Public -Enabled True `
    -DefaultInboundAction Block -DefaultOutboundAction Allow
# Aprire SOLO le porte necessarie per il ruolo del server

# 5. AUDIT
auditpol /set /subcategory:"Logon" /success:enable /failure:enable
auditpol /set /subcategory:"Account Lockout" /failure:enable
auditpol /set /subcategory:"User Account Management" /success:enable /failure:enable
auditpol /set /subcategory:"Process Creation" /success:enable

# 6. REGISTRY HARDENING
# Disabilitare autologon
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" `
    -Name "AutoAdminLogon" -Value "0"
# Non mostrare ultimo utente
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -Name "DontDisplayLastUserName" -Value 1
# Richiedere Ctrl+Alt+Del
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -Name "DisableCAD" -Value 0

# 7. RDP HARDENING
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" `
    -Name "UserAuthentication" -Value 1  # NLA obbligatorio
# Limitare accesso RDP a gruppi specifici via GPO

# 8. LAPS — Installare e configurare per admin locale
# Windows LAPS (nuova versione integrata in Windows 11/Server 2022+)
# Gestisce automaticamente la password dell'admin locale
# Salva la password in AD o Azure AD (Entra ID)

# Abilitare Windows LAPS via GPO:
# Computer → Administrative Templates → System → LAPS
# → Configure password backup directory: Active Directory
# → Password Settings:
#   Password Complexity: Large letters + small letters + numbers + specials
#   Password Length: 20
#   Password Age (Days): 30

# Leggere la password LAPS di un computer
Get-LapsADPassword -Identity "WKS-IT-001" -AsPlainText

# 9. BITLOCKER — Su tutti i volumi dati
Enable-BitLocker -MountPoint "C:" -EncryptionMethod XtsAes256 `
    -RecoveryPasswordProtector -SkipHardwareTest
# Salvare recovery key in AD:
# GPO → Computer → Administrative Templates → Windows Components →
#   BitLocker Drive Encryption → Store BitLocker recovery info in AD DS: Enabled

# 10. BASELINE — Applicare Microsoft Security Baseline
# Scaricare: Microsoft Security Compliance Toolkit
# Contiene GPO preconfigurate per Windows Server e Client
# Import-GPO da baseline:
# LGPO.exe /g "C:\SecurityBaseline\GPOs\{GUID}"

# ============================================================
# HARDENING AGGIUNTIVO — SPESSO TRASCURATO
# ============================================================

# 11. CONFIGURARE SYSMON (monitoring avanzato)
# Sysmon registra: process creation, network connections,
# file creation, registry changes, driver loads
# Installare: sysmon64.exe -accepteula -i sysmonconfig.xml
# Config consigliata: SwiftOnSecurity/sysmon-config (GitHub)

# 12. CREDENTIAL GUARD (protezione credenziali)
# Isola LSASS in un container virtualizzato (VTL 1)
# Previene pass-the-hash e credential theft
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "LsaCfgFlags" -Value 1 -Type DWord
# 1 = Enabled with UEFI lock (consigliato)
# 2 = Enabled without UEFI lock

# 13. ATTACK SURFACE REDUCTION (ASR)
# Blocca tecniche comuni di attacco:
# - Macro Office che lanciano processi figlio
# - Script offuscati
# - Creazione processi da app Office
# - Credential stealing da LSASS
# Configurare via Intune o GPO: Windows Defender → ASR Rules

# 14. PROTECTED USERS GROUP
# Aggiungere account admin sensibili al gruppo "Protected Users"
# Effetti: no NTLM auth, no delegation, Kerberos TGT 4h max, no DES/RC4
Add-ADGroupMember -Identity "Protected Users" -Members "admin.mrossi"

# 15. TIERED ACCESS MODEL
# Tier 0: Domain Controllers, PKI, AD management
# Tier 1: Server applicativi, database, file server
# Tier 2: Workstation e dispositivi utente
# Un admin Tier 0 non logga MAI su un Tier 2 e viceversa
# Implementare con GPO: "Deny log on locally" e "Deny log on through RDP"
```

---

## Hardening Windows Server — CIS Benchmark

```powershell
# ============================================================
# CIS (Center for Internet Security) BENCHMARK
# Standard de-facto per hardening Windows
# ============================================================

# Livelli CIS:
# Level 1 (L1): Sicurezza base, minimo impatto operativo
# Level 2 (L2): Sicurezza avanzata, possibile impatto performance/funzionalità

# ============================================================
# CIS L1 — POLICY ACCOUNT
# ============================================================

# Password Policy (via GPO Default Domain Policy)
# Minimum password length: 14 characters (CIS) o 12 (Microsoft baseline)
# Password history: 24 passwords remembered
# Maximum password age: 365 days (CIS 2024+, prima era 60-90)
# Minimum password age: 1 day
# Complexity requirements: Enabled
# Store passwords using reversible encryption: Disabled

# Account Lockout Policy
# Account lockout threshold: 5 invalid attempts
# Account lockout duration: 15 minutes (o più)
# Reset account lockout counter: 15 minutes

# ============================================================
# CIS L1 — AUDIT POLICY (AVANZATA)
# ============================================================

# Usare Advanced Audit Policy Configuration (più granulare)
# Computer → Windows Settings → Security Settings →
#   Advanced Audit Policy Configuration

# Account Logon
auditpol /set /subcategory:"Credential Validation" /success:enable /failure:enable

# Account Management
auditpol /set /subcategory:"Computer Account Management" /success:enable
auditpol /set /subcategory:"Security Group Management" /success:enable
auditpol /set /subcategory:"User Account Management" /success:enable /failure:enable

# Logon/Logoff
auditpol /set /subcategory:"Account Lockout" /failure:enable
auditpol /set /subcategory:"Logoff" /success:enable
auditpol /set /subcategory:"Logon" /success:enable /failure:enable
auditpol /set /subcategory:"Special Logon" /success:enable

# Object Access
auditpol /set /subcategory:"Removable Storage" /success:enable /failure:enable

# Policy Change
auditpol /set /subcategory:"Audit Policy Change" /success:enable
auditpol /set /subcategory:"Authentication Policy Change" /success:enable
auditpol /set /subcategory:"Authorization Policy Change" /success:enable

# Privilege Use
auditpol /set /subcategory:"Sensitive Privilege Use" /success:enable /failure:enable

# System
auditpol /set /subcategory:"Security State Change" /success:enable
auditpol /set /subcategory:"Security System Extension" /success:enable
auditpol /set /subcategory:"System Integrity" /success:enable /failure:enable

# ============================================================
# CIS L1 — USER RIGHTS ASSIGNMENT
# ============================================================

# GPO → Computer → Windows Settings → Security Settings →
#   Local Policies → User Rights Assignment

# Access this computer from the network: Administrators, Authenticated Users
# Deny access to this computer from the network: Guests, Local account
# Deny log on locally: Guests
# Deny log on through RDS: Guests, Local account
# Allow log on locally: Administrators (solo)
# Debug programs: Administrators (o NESSUNO su server di produzione)
# Manage auditing and security log: Administrators
# Take ownership of files: Administrators

# ============================================================
# CIS L1 — SECURITY OPTIONS
# ============================================================

# GPO → Computer → Windows Settings → Security Settings →
#   Local Policies → Security Options

# Interactive logon: Do not display last user name: Enabled
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -Name "DontDisplayLastUserName" -Value 1

# Interactive logon: Do not require Ctrl+Alt+Del: Disabled
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -Name "DisableCAD" -Value 0

# Network access: Do not allow anonymous enumeration of SAM accounts: Enabled
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "RestrictAnonymousSAM" -Value 1

# Network security: LAN Manager authentication level: NTLMv2 response only, refuse LM & NTLM
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "LmCompatibilityLevel" -Value 5

# Network security: Minimum session security for NTLM: Require NTLMv2, 128-bit
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa\MSV1_0" `
    -Name "NtlmMinClientSec" -Value 537395200
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa\MSV1_0" `
    -Name "NtlmMinServerSec" -Value 537395200

# Verificare compliance CIS con script:
# Scaricare CIS-CAT Pro o CIS-CAT Lite (gratuito per assessment)
# Esegue scan automatizzato e genera report HTML con pass/fail per ogni controllo
```

---

## Hardening Windows Client

```powershell
# GPO per workstation:

# 1. BitLocker obbligatorio (con recovery key in AD)
# 2. Windows Firewall attivo su tutti i profili
# 3. Windows Defender con Real-Time Protection
# 4. AppLocker o WDAC (bloccare esecuzione da %USERPROFILE%)
# 5. USB restrizioni (block o read-only)
# 6. Screen lock dopo 10 minuti di inattività
# 7. Account lockout: 5 tentativi, 30 minuti
# 8. Disabilitare: Cortana, telemetria, Windows Store (se enterprise)
# 9. LAPS per admin locale
# 10. Windows Hello for Business o MFA

# Credential Guard (Windows Enterprise/Education):
# GPO → Device Guard → VBS → Credential Guard: Enabled with UEFI lock

# Conditional Access + Compliance (se Intune):
# Device must be compliant per accedere a risorse aziendali
```

---

## Hardening Windows Client — Guida Approfondita

### GPO Hardening Client — Configurazione Completa

```powershell
# ============================================================
# GPO: SEC-Client-Hardening-L1 (CIS Level 1 Client)
# ============================================================

# --- BITLOCKER ---
# Computer → Administrative Templates → Windows Components →
#   BitLocker Drive Encryption → Operating System Drives
# → Require additional authentication at startup: Enabled
#   → Allow BitLocker without a compatible TPM: Unchecked
#   → Configure TPM startup: Allow TPM
#   → Configure TPM startup PIN: Allow startup PIN with TPM
# → Choose how BitLocker-protected operating system drives can be recovered: Enabled
#   → Save BitLocker recovery information to AD DS: Enabled
#   → Do not enable BitLocker until recovery information is stored: Enabled

# Abilitare BitLocker via PowerShell:
$BLV = Get-BitLockerVolume -MountPoint "C:"
if ($BLV.ProtectionStatus -eq "Off") {
    Enable-BitLocker -MountPoint "C:" -EncryptionMethod XtsAes256 `
        -RecoveryPasswordProtector -SkipHardwareTest
    # Salvare recovery key in AD
    $key = (Get-BitLockerVolume -MountPoint "C:").KeyProtector |
        Where-Object KeyProtectorType -eq "RecoveryPassword"
    Backup-BitLockerKeyProtector -MountPoint "C:" -KeyProtectorId $key.KeyProtectorId
}

# --- WINDOWS FIREWALL ---
# Forzare firewall attivo su tutti i profili
Set-NetFirewallProfile -Profile Domain,Private,Public -Enabled True `
    -DefaultInboundAction Block -DefaultOutboundAction Allow `
    -LogAllowed False -LogBlocked True `
    -LogFileName "%SystemRoot%\System32\LogFiles\Firewall\pfirewall.log" `
    -LogMaxSizeKilobytes 16384

# Bloccare porte pericolose in inbound (anche nel profilo Domain)
New-NetFirewallRule -DisplayName "Block SMB Inbound" -Direction Inbound `
    -LocalPort 445 -Protocol TCP -Action Block -Profile Domain,Private,Public

# --- WINDOWS DEFENDER ---
# Computer → Administrative Templates → Windows Components →
#   Microsoft Defender Antivirus
# → Turn off Microsoft Defender Antivirus: DISABLED (deve restare attivo)
# → Real-time protection → Turn on behavior monitoring: Enabled
# → Real-time protection → Scan all downloaded files and attachments: Enabled
# → MAPS → Join Microsoft MAPS: Advanced MAPS
# → Scan → Scan removable drives: Enabled

# ASR Rules (Attack Surface Reduction) via PowerShell:
# Bloccare processi non firmati da USB
Add-MpPreference -AttackSurfaceReductionRules_Ids d4f940ab-401b-4efc-aadc-ad5f3c50688a `
    -AttackSurfaceReductionRules_Actions Enabled

# Bloccare app Office da creare processi figlio
Add-MpPreference -AttackSurfaceReductionRules_Ids d4f940ab-401b-4efc-aadc-ad5f3c50688a `
    -AttackSurfaceReductionRules_Actions Enabled

# Bloccare credential stealing da LSASS
Add-MpPreference -AttackSurfaceReductionRules_Ids 9e6c4e1f-7d60-472f-ba1a-a39ef669e4b2 `
    -AttackSurfaceReductionRules_Actions Enabled

# --- USB RESTRIZIONI ---
# Computer → Administrative Templates → System → Device Installation →
#   Device Installation Restrictions
# → Prevent installation of removable devices: Enabled
# → Allow installation of devices using drivers matching these device setup classes:
#   {745a17a0-74d3-11d0-b6fe-00a0c90f57da}  # HID (mouse/tastiera)

# --- SCREEN LOCK ---
# User → Administrative Templates → Control Panel → Personalization
# → Screen saver timeout: 600 (10 minuti)
# → Password protect the screen saver: Enabled
# → Force specific screen saver: scrnsave.scr (blank)

# --- TELEMETRIA ---
# Computer → Administrative Templates → Windows Components →
#   Data Collection and Preview Builds
# → Allow Diagnostic Data: 0 (Security/Off) o 1 (Required)
# Non inviare dati telemetrici opzionali

# --- POWERSHELL LOGGING ---
# Fondamentale per forensic e detection
# Computer → Administrative Templates → Windows Components →
#   Windows PowerShell
# → Turn on Module Logging: Enabled (log tutti i moduli: *)
# → Turn on Script Block Logging: Enabled
# → Turn on PowerShell Transcription: Enabled
#   Path: \\SRV01\PSLogs$\%COMPUTERNAME%\

# --- CONTROLLED FOLDER ACCESS ---
# Protegge cartelle utente da ransomware
Set-MpPreference -EnableControlledFolderAccess Enabled
# Aggiungere cartelle protette:
Add-MpPreference -ControlledFolderAccessProtectedFolders "D:\Dati"
# Aggiungere app autorizzate:
Add-MpPreference -ControlledFolderAccessAllowedApplications "C:\Program Files\CustomApp\app.exe"
```

### Intune Compliance Policy — Template

```powershell
# Per ambienti gestiti da Intune, definire compliance policy:
# Endpoint Manager → Devices → Compliance Policies → Create

# Settings consigliati:
# Device Health:
# - BitLocker: Require
# - Secure Boot: Require
# - Code Integrity: Require
#
# Device Properties:
# - Minimum OS version: 10.0.22621 (Win11 22H2)
#
# System Security:
# - Password required: Yes
# - Minimum password length: 8
# - Maximum minutes of inactivity: 10
# - Firewall: Require
# - Antivirus: Require
# - Antispyware: Require
# - Real-time protection: Require
# - Microsoft Defender Antimalware minimum version: current
#
# Actions for noncompliance:
# - Mark device noncompliant: Immediately
# - Send email to end user: After 1 day
# - Retire the noncompliant device: After 30 days
```

---

## Checklist Installazione Server

```
□ 1. Installare Windows Server 2022 (Standard o Datacenter)
□ 2. Configurare IP statico, DNS, hostname
□ 3. Attivare licenza Windows
□ 4. Join al dominio
□ 5. Installare aggiornamenti (tutto fino a data corrente)
□ 6. Installare ruoli necessari
□ 7. Configurare Windows Firewall (solo porte necessarie)
□ 8. Configurare backup (Windows Server Backup o soluzione enterprise)
□ 9. Configurare monitoring (Performance Monitor, Event Forwarding)
□ 10. Hardening:
    □ Disabilitare servizi non necessari
    □ Disabilitare SMBv1, LLMNR, NetBIOS
    □ Configurare audit policy
    □ Configurare NLA per RDP
    □ Installare LAPS
    □ BitLocker sui volumi dati
□ 11. Spostare in OU corretta in AD
□ 12. Applicare GPO del ruolo
□ 13. Documentare: IP, ruolo, dipendenze, responsabile, data installazione
□ 14. Verificare backup funzionante (test restore)
□ 15. Comunicare al team: nuovo server operativo
```

---

## Disaster Recovery Procedures

### Procedura: DC Guasto (1 solo DC down, altri OK)

```
TEMPO STIMATO: 2-4 ore

1. Verificare che gli altri DC funzionino: dcdiag /s:DC02
2. Se il DC guasto ha ruoli FSMO → seize sul DC funzionante:
   Move-ADDirectoryServerOperationMasterRole -Identity DC02 `
       -OperationMasterRole PDCEmulator,RIDMaster,InfrastructureMaster -Force
3. Aggiornare DNS: rimuovere record del DC guasto
4. Opzione A: riparare il DC guasto e re-promuovere
   Opzione B: installare nuovo DC, promuovere, trasferire ruoli
5. Cleanup AD: rimuovere il vecchio DC da AD Sites and Services
6. Verificare: dcdiag /v /c /e, repadmin /replsummary
```

### Procedura: Tutti i DC Down (disaster completo)

```
TEMPO STIMATO: 8-24 ore

1. Installare nuovo Windows Server (da ISO)
2. Configurare IP e hostname come il primo DC
3. Restore System State dal backup più recente:
   - Boot in DSRM
   - wbadmin start systemstaterecovery -version:...
4. Riavviare → verificare AD funzionante
5. Aggiungere secondo DC per ridondanza
6. Verificare tutti i servizi: DNS, DHCP, GPO, replica
7. Aggiornare DNS su tutti i client (se IP cambiate)
8. Verificare join dominio di client e server
```

---

## Disaster Recovery — Scenari Aggiuntivi

### Procedura: File Server Guasto

```powershell
# TEMPO STIMATO: 2-6 ore
#
# 1. ASSESSMENT
#    - Determinare entità del guasto (disco, controller, OS, hardware totale)
#    - Verificare ultimo backup disponibile e RPO (Recovery Point Objective)
#
# 2. SE GUASTO DISCO (RAID degradato)
#    a. Sostituire disco guasto (hot-swap se supportato)
#    b. RAID rebuild automatico (monitorare con vendor tool)
#    c. Verificare integrità dati dopo rebuild
#
# 3. SE GUASTO OS O HARDWARE TOTALE
#    a. Preparare nuovo server (o VM)
#    b. Installare Windows Server con stesso hostname
#    c. Join al dominio
#    d. Installare ruolo File Server
#    e. Restore dati da backup:

# Restore con Windows Server Backup
wbadmin start recovery -version:<backup-version> `
    -itemType:File -items:D:\Shares `
    -recoveryTarget:D:\Shares -overwrite:Overwrite

# Restore con Veeam (esempio)
# Veeam Console → Restore → Windows File Restore
# Selezionare backup point → Browse → selezionare cartelle → Restore

#    f. Ricreare share:
# Importare configurazione share da backup o script
# $shares = Import-Csv "C:\Backup\shares-config.csv"
# foreach ($s in $shares) {
#     New-SmbShare -Name $s.Name -Path $s.Path `
#         -FullAccess $s.FullAccess -ChangeAccess $s.ChangeAccess
# }

#    g. Verificare permessi NTFS (restore dovrebbe preservarli)
#    h. Aggiornare DFS target (se DFS in uso)
#    i. Verificare accesso utenti
```

### Procedura: Ransomware Recovery

```powershell
# ============================================================
# RANSOMWARE RESPONSE — PROCEDURA AZIENDALE
# ============================================================
# TEMPO STIMATO: 24-72 ore (dipende dall'estensione)

# FASE 1: CONTENIMENTO IMMEDIATO (prime 2 ore)
# ──────────────────────────────────────────────
# 1. ISOLARE i sistemi infetti dalla rete
#    - Disconnettere fisicamente il cavo di rete
#    - NON spegnere i sistemi (preservare memoria per forensic)
#    - Disabilitare switch port se possibile

# 2. Bloccare la propagazione:
#    - Bloccare SMB (445/TCP) tra subnet sul firewall
#    - Disabilitare account compromessi
#    - Revocare sessioni VPN

# 3. Notificare:
#    - CISO / Security team
#    - Management
#    - Legal (per obblighi normativi GDPR: 72h notification)

# FASE 2: ASSESSMENT (ore 2-8)
# ──────────────────────────────
# 1. Determinare il vettore di attacco:
#    - Email phishing? RDP esposto? Vulnerability exploit?
#    - Analizzare log: Security, PowerShell, Sysmon

# 2. Identificare l'estensione:
#    - Quali sistemi sono infetti?
#    - Quali dati sono cifrati?
#    - I backup sono integri? (verificare che non siano cifrati!)

# 3. Identificare la variante ransomware:
#    - Nota di riscatto → ID su nomoreransom.org
#    - Hash dei file cifrati → VirusTotal
#    - Potrebbe esistere un decryptor gratuito

# FASE 3: ERADICAZIONE (ore 8-24)
# ─────────────────────────────────
# 1. Rimuovere il malware da tutti i sistemi infetti
# 2. Resettare TUTTE le password (domain admin, service accounts, utenti)
# 3. Revocare tutti i Kerberos tickets: due volte il reset della password krbtgt
$newPass = ConvertTo-SecureString "NuovaP@ssw0rdKrbtgt!" -AsPlainText -Force
Set-ADAccountPassword -Identity krbtgt -NewPassword $newPass -Reset
# ATTENDERE che la replica AD propaghi (almeno 12 ore)
# poi resettare ANCORA krbtgt
Set-ADAccountPassword -Identity krbtgt -NewPassword $newPass -Reset

# 4. Patchare la vulnerabilità usata per l'ingresso

# FASE 4: RECOVERY (ore 24-72)
# ──────────────────────────────
# 1. Restore sistemi da backup puliti (PRE-infezione)
# 2. Restore dati da backup (verificare integrità)
# 3. Ricostruire sistemi che non hanno backup
# 4. Test completo prima di rimettere online
# 5. Monitoraggio intensivo per 30 giorni post-recovery

# FASE 5: POST-INCIDENT (settimane successive)
# ──────────────────────────────────────────────
# 1. Incident report completo (timeline, root cause, impact)
# 2. Lessons learned → miglioramenti infrastruttura
# 3. Aggiornare piano DR con le lezioni apprese
# 4. Formazione anti-phishing per gli utenti
# 5. Verificare copertura backup (air-gapped backup!)
```

### Procedura: Restore Backup Singolo Oggetto AD

```powershell
# Recuperare un singolo utente o OU cancellato per errore

# METODO 1: AD Recycle Bin (se abilitato — dovrebbe esserlo!)
# Recuperare utente cancellato nelle ultime 180 giorni (default tombstone)
Get-ADObject -Filter 'isDeleted -eq $true -and Name -like "*mrossi*"' `
    -IncludeDeletedObjects -Properties * |
    Restore-ADObject

# Recuperare OU cancellata
Get-ADObject -Filter 'isDeleted -eq $true -and ObjectClass -eq "organizationalUnit"' `
    -IncludeDeletedObjects |
    Restore-ADObject

# METODO 2: Authoritative Restore (se AD Recycle Bin non abilitato)
# 1. Boot DC in DSRM (Directory Services Restore Mode)
# 2. Restore System State: wbadmin start systemstaterecovery
# 3. Prima del reboot, marcare l'oggetto come authoritative:
#    ntdsutil → authoritative restore → restore object "CN=Mario Rossi,OU=Utenti,DC=corp,DC=contoso,DC=com"
# 4. Reboot → l'oggetto viene replicato a tutti i DC

# METODO 3: Snapshots AD (se configurati)
# 1. Montare snapshot: ntdsutil → snapshot → mount {GUID}
# 2. Esaminare il contenuto con dsamain.exe
# 3. Esportare l'oggetto con ldifde
# 4. Importare con ldifde nel AD corrente
```

---

## Manutenzione Periodica

### Giornaliera
- Verificare backup completati con successo
- Controllare Event Viewer per errori critici
- Verificare spazio disco sui server

### Settimanale
- `dcdiag /v /c` su tutti i DC
- `repadmin /replsummary`
- Report compliance aggiornamenti (WSUS)
- Verificare certificati in scadenza

### Mensile
- Patch Tuesday: testare e deployare aggiornamenti
- Review account utente: disabilitare inattivi, verificare gruppi admin
- WSUS cleanup: `Invoke-WsusServerCleanup`
- Verificare dimensione Event Log e archivio

### Trimestrale
- Test restore da backup (verifica reale)
- Review GPO: rimuovere obsolete, documentare modifiche
- Aggiornare documentazione infrastruttura
- Review firewall rules: rimuovere regole obsolete

### Annuale
- Review architettura AD: OU, gruppi, naming convention
- DR drill: simulare disaster e recovery completo
- Review licenze e contratti supporto
- Pianificazione capacità: storage, compute, rete per anno successivo
- Aggiornare piano DR con le modifiche dell'anno

---

## Automazione Manutenzione

### Script: Health Check Giornaliero AD

```powershell
# Script di health check da eseguire ogni giorno via Task Scheduler
# Output: report HTML inviato via email

function Invoke-ADHealthCheck {
    param(
        [string]$OutputPath = "C:\Reports",
        [string]$SmtpServer = "mail.corp.contoso.com",
        [string]$EmailTo = "it-team@corp.contoso.com"
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
    $results = @()

    # 1. DCDIAG
    Write-Host "Eseguendo dcdiag..."
    $dcdiag = dcdiag /v /c 2>&1
    $dcdiagFailed = $dcdiag | Select-String "failed test"
    $results += [PSCustomObject]@{
        Check  = "DCDiag"
        Status = if ($dcdiagFailed) { "FAILED" } else { "PASSED" }
        Detail = if ($dcdiagFailed) { ($dcdiagFailed -join "; ") } else { "All tests passed" }
    }

    # 2. Replica AD
    Write-Host "Verificando replica..."
    $replSummary = repadmin /replsummary 2>&1
    $replErrors = $replSummary | Select-String "fail|error" -CaseSensitive:$false
    $results += [PSCustomObject]@{
        Check  = "AD Replication"
        Status = if ($replErrors) { "WARNING" } else { "PASSED" }
        Detail = if ($replErrors) { ($replErrors -join "; ") } else { "Replication healthy" }
    }

    # 3. Spazio disco DC
    Write-Host "Verificando spazio disco..."
    $dcs = Get-ADDomainController -Filter *
    foreach ($dc in $dcs) {
        $disk = Get-CimInstance Win32_LogicalDisk -ComputerName $dc.HostName `
            -Filter "DeviceID='C:'" -ErrorAction SilentlyContinue
        if ($disk) {
            $freePercent = [math]::Round(($disk.FreeSpace / $disk.Size) * 100, 1)
            $results += [PSCustomObject]@{
                Check  = "Disk Space ($($dc.HostName))"
                Status = if ($freePercent -lt 10) { "CRITICAL" }
                         elseif ($freePercent -lt 20) { "WARNING" }
                         else { "PASSED" }
                Detail = "$freePercent% free ($([math]::Round($disk.FreeSpace/1GB, 1)) GB)"
            }
        }
    }

    # 4. Servizi critici
    Write-Host "Verificando servizi..."
    $criticalSvcs = @("DNS", "NTDS", "Netlogon", "W32Time", "DFSR")
    foreach ($dc in $dcs) {
        foreach ($svcName in $criticalSvcs) {
            $svc = Get-Service -Name $svcName -ComputerName $dc.HostName -ErrorAction SilentlyContinue
            if ($svc -and $svc.Status -ne "Running") {
                $results += [PSCustomObject]@{
                    Check  = "Service $svcName ($($dc.HostName))"
                    Status = "CRITICAL"
                    Detail = "Status: $($svc.Status)"
                }
            }
        }
    }

    # 5. Account lockout recenti
    $lockedAccounts = Search-ADAccount -LockedOut
    if ($lockedAccounts) {
        $results += [PSCustomObject]@{
            Check  = "Locked Accounts"
            Status = "WARNING"
            Detail = "$($lockedAccounts.Count) accounts: $(($lockedAccounts.SamAccountName -join ', '))"
        }
    }

    # 6. Certificati in scadenza (prossimi 30 giorni)
    $expiring = Get-ChildItem Cert:\LocalMachine\My |
        Where-Object { $_.NotAfter -lt (Get-Date).AddDays(30) -and $_.NotAfter -gt (Get-Date) }
    if ($expiring) {
        $results += [PSCustomObject]@{
            Check  = "Expiring Certificates"
            Status = "WARNING"
            Detail = "$($expiring.Count) certificates expiring within 30 days"
        }
    }

    # Generare report
    $criticalCount = ($results | Where-Object Status -eq "CRITICAL").Count
    $warningCount = ($results | Where-Object Status -eq "WARNING").Count

    $report = $results | Format-Table -AutoSize | Out-String
    Write-Host $report

    # Export CSV
    $csvPath = "$OutputPath\ADHealthCheck-$(Get-Date -Format 'yyyyMMdd').csv"
    $results | Export-Csv $csvPath -NoTypeInformation

    Write-Host "`n=== RIEPILOGO: $criticalCount CRITICAL, $warningCount WARNING ==="

    return $results
}

# Registrare come task schedulato:
# $action = New-ScheduledTaskAction -Execute "powershell.exe" `
#     -Argument "-ExecutionPolicy Bypass -File C:\Scripts\AD-HealthCheck.ps1"
# $trigger = New-ScheduledTaskTrigger -Daily -At "06:00"
# $principal = New-ScheduledTaskPrincipal -UserId "CORP\gMSA-Monitoring$" `
#     -LogonType Password -RunLevel Highest
# Register-ScheduledTask -TaskName "AD Daily Health Check" `
#     -Action $action -Trigger $trigger -Principal $principal
```

### Script: Pulizia Account Inattivi

```powershell
# Identificare e gestire account AD inattivi
function Find-InactiveADAccounts {
    param(
        [int]$InactiveDays = 90,
        [switch]$DisableAccounts,
        [switch]$WhatIf
    )

    $threshold = (Get-Date).AddDays(-$InactiveDays)

    # Utenti inattivi
    $inactiveUsers = Get-ADUser -Filter {
        Enabled -eq $true -and
        LastLogonDate -lt $threshold
    } -Properties LastLogonDate, Department, Manager, WhenCreated |
        Where-Object { $_.SamAccountName -notlike "svc-*" -and
                       $_.SamAccountName -notlike "gMSA-*" } |
        Select-Object SamAccountName, Name, Department,
            LastLogonDate, WhenCreated, DistinguishedName

    Write-Host "Account utente inattivi (> $InactiveDays giorni): $($inactiveUsers.Count)"
    $inactiveUsers | Format-Table -AutoSize

    # Computer inattivi
    $inactiveComputers = Get-ADComputer -Filter {
        Enabled -eq $true -and
        LastLogonDate -lt $threshold
    } -Properties LastLogonDate, OperatingSystem |
        Select-Object Name, OperatingSystem, LastLogonDate, DistinguishedName

    Write-Host "Computer inattivi (> $InactiveDays giorni): $($inactiveComputers.Count)"

    if ($DisableAccounts) {
        foreach ($user in $inactiveUsers) {
            if ($WhatIf) {
                Write-Host "[WhatIf] Disabiliterei: $($user.SamAccountName)"
            } else {
                Disable-ADAccount -Identity $user.SamAccountName
                Set-ADUser -Identity $user.SamAccountName `
                    -Description "DISABLED $(Get-Date -Format 'yyyy-MM-dd') - Inattivo > ${InactiveDays}gg"
                # Spostare in OU "Disabled"
                Move-ADObject -Identity $user.DistinguishedName `
                    -TargetPath "OU=Disabled,DC=corp,DC=contoso,DC=com"
            }
        }
    }

    return @{
        Users     = $inactiveUsers
        Computers = $inactiveComputers
    }
}

# Uso:
# Find-InactiveADAccounts -InactiveDays 90 -WhatIf
# Find-InactiveADAccounts -InactiveDays 90 -DisableAccounts
```

### Script: Report Compliance Patching

```powershell
# Verificare stato patching su tutti i server
function Get-PatchComplianceReport {
    param(
        [string]$OUPath = "OU=Server,DC=corp,DC=contoso,DC=com",
        [int]$MaxDaysOld = 45
    )

    $servers = Get-ADComputer -SearchBase $OUPath -Filter 'OperatingSystem -like "*Server*"' |
        Select-Object -ExpandProperty Name

    $results = foreach ($srv in $servers) {
        try {
            $hotfix = Invoke-Command -ComputerName $srv -ScriptBlock {
                Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 1
            } -ErrorAction Stop

            $daysSinceUpdate = ((Get-Date) - $hotfix.InstalledOn).Days

            [PSCustomObject]@{
                Server          = $srv
                LastHotfix      = $hotfix.HotFixID
                InstalledOn     = $hotfix.InstalledOn
                DaysSinceUpdate = $daysSinceUpdate
                Compliant       = $daysSinceUpdate -le $MaxDaysOld
                Status          = if ($daysSinceUpdate -le $MaxDaysOld) { "OK" }
                                  elseif ($daysSinceUpdate -le 60) { "WARNING" }
                                  else { "CRITICAL" }
            }
        }
        catch {
            [PSCustomObject]@{
                Server          = $srv
                LastHotfix      = "UNREACHABLE"
                InstalledOn     = $null
                DaysSinceUpdate = -1
                Compliant       = $false
                Status          = "ERROR"
            }
        }
    }

    $results | Sort-Object DaysSinceUpdate -Descending | Format-Table -AutoSize

    # Statistiche
    $total = $results.Count
    $compliant = ($results | Where-Object Compliant).Count
    Write-Host "`nCompliance: $compliant / $total ($([math]::Round($compliant/$total*100))%)"

    return $results
}
```

---

## Scenari Reali Enterprise

### Scenario 1: Deployment da Zero di una Nuova Sede

```
CONTESTO: Nuova sede con 50 postazioni, collegata via VPN site-to-site
TEMPO: 2 settimane dalla consegna hardware al go-live

SETTIMANA 1: INFRASTRUTTURA
─────────────────────────────
Giorno 1-2: Rack & Stack
- Installare switch, firewall, access point
- Configurare VLAN: Management, Server, Client, Guest
- Configurare VPN site-to-site verso sede principale
- Testare connettività

Giorno 3: Domain Controller
- Installare Windows Server 2022 (VM su Hyper-V host)
- Promuovere come DC aggiuntivo del dominio esistente
- Configurare come DNS server locale
- Creare AD Site per la nuova sede
- Configurare subnet e site link

Giorno 4: DHCP e servizi locali
- DHCP scope per la nuova sede
- DHCP failover con DC sede principale
- DFS Replication per share condivise
- Stampanti di rete

Giorno 5: Test
- Verificare AD replication: repadmin /replsummary
- Verificare DNS resolution locale
- Verificare GPO application
- Test login utente

SETTIMANA 2: CLIENT DEPLOYMENT
─────────────────────────────
Giorno 6-8: Imaging
- MDT Task Sequence con driver pack per il modello specifico
- WDS per PXE boot
- Deploy 50 workstation (batch da 10-15 alla volta)
- Join automatico al dominio nella OU corretta

Giorno 9: Configurazione
- Verificare GPO applicate su ogni workstation
- Installare applicazioni specifiche della sede
- Configurare stampanti
- Configurare Folder Redirection

Giorno 10: Go-Live
- Utenti accedono e verificano accesso a risorse
- Supporto on-site per problemi
- Documentare: IP plan, cablaggio, asset inventory
```

### Scenario 2: Hardening Post-Breach

```
CONTESTO: Dopo un incidente ransomware, hardening completo dell'infrastruttura
TEMPO: 4-6 settimane

SETTIMANA 1: ASSESSMENT E QUICK WINS
─────────────────────────────────────
- Audit completo: account admin, GPO, firewall rules, servizi esposti
- Disabilitare SMBv1 su TUTTI i sistemi
- Disabilitare LLMNR e NetBIOS su TUTTI i sistemi
- Reset password krbtgt (2x con intervallo 12h)
- Reset TUTTE le password admin
- Abilitare MFA per tutti gli admin

SETTIMANA 2: HARDENING AD
──────────────────────────
- Implementare Tiered Access Model (Tier 0/1/2)
- Aggiungere admin critici al gruppo Protected Users
- Configurare LAPS su tutte le workstation
- Abilitare AD Recycle Bin (se non attivo)
- Configurare audit policy avanzata (CIS Benchmark)
- Installare Sysmon su tutti i DC

SETTIMANA 3: HARDENING NETWORK E CLIENT
────────────────────────────────────────
- Segmentare la rete: VLAN separate per client, server, management
- Firewall rules: default deny tra VLAN
- Abilitare Windows Firewall su tutti i sistemi
- BitLocker su tutti i client
- Credential Guard su workstation Enterprise
- WDAC in Audit Mode

SETTIMANA 4: MONITORING E DETECTION
────────────────────────────────────
- Windows Event Forwarding: centralizzare log Security e Sysmon
- Alert per: account lockout, admin logon, service creation, scheduled task
- Baseline: documentare stato "normale" per detection anomalie
- Test penetration per verificare l'hardening

SETTIMANA 5-6: BACKUP E DR
───────────────────────────
- Implementare backup 3-2-1: 3 copie, 2 media, 1 offsite
- Backup air-gapped (non raggiungibile dalla rete — anti-ransomware)
- Test restore completo di DC, file server, database
- Documentare piano DR aggiornato
- DR drill con il team IT
```

---

## Troubleshooting

**1. "dcdiag fallisce con errore 'failed test Replications'"** → `repadmin /showrepl` per dettagli. Cause comuni: DNS non risolve l'altro DC (verificare `nslookup DC02.corp.contoso.com`), porta bloccata dal firewall (135/TCP, 389/TCP, 636/TCP, 3268/TCP, 49152-65535/TCP), time skew > 5 minuti (`w32tm /query /status`). Fix: correggere DNS, aprire porte, sincronizzare tempo.

**2. "GPO non si applica su alcune workstation"** → `gpresult /R` sulla workstation per vedere quali GPO sono applicate e quali filtrate. Cause: Security Filtering errato (l'account computer o utente non ha "Apply Group Policy"), WMI filter che esclude la macchina, link GPO sulla OU sbagliata, GPO disabilitato. Fix: verificare con `gpresult /H report.html` per report dettagliato.

**3. "Join dominio fallisce con errore 'The specified domain either does not exist or could not be contacted'"** → Il client non raggiunge un DC. Verificare: DNS punta al DC (`nslookup corp.contoso.com`), il DC è raggiungibile (ping), il firewall non blocca porte AD. Fix: configurare DNS primario = IP del DC, verificare rete.

**4. "DHCP: nessun IP assegnato ai client"** → Verificare: servizio DHCP attivo (`Get-Service DHCPServer`), scope attivo con indirizzi disponibili, DHCP relay configurato se client e server su subnet diverse. Se DHCP failover: verificare stato (`Get-DhcpServerv4Failover`). Fix: riattivare scope, aggiungere indirizzi, configurare relay agent.

**5. "BitLocker: recovery key richiesta dopo aggiornamento BIOS"** → L'aggiornamento BIOS ha modificato i PCR (Platform Configuration Registers) misurati dal TPM. Inserire la recovery key (da AD: `Get-BitLockerVolume` o portale Intune). Dopo il recovery: sospendere BitLocker prima di aggiornamenti BIOS futuri (`Suspend-BitLocker -MountPoint "C:" -RebootCount 1`).

**6. "Windows Update: errore 0x80070422 (service not running)"** → Il servizio Windows Update (wuauserv) è disabilitato o non si avvia. `Set-Service wuauserv -StartupType Manual; Start-Service wuauserv`. Verificare che i servizi dipendenti siano attivi: Background Intelligent Transfer Service (BITS), Cryptographic Services.

**7. "Hardening: dopo l'applicazione della baseline CIS, alcune applicazioni non funzionano"** → Troppo restrittivo in un colpo. Approccio corretto: applicare CIS in Audit Mode prima (solo logging senza blocco). Verificare le applicazioni per 2 settimane. Creare eccezioni per le app legittime. Poi passare a Enforce. Le impostazioni più problematiche: LAN Manager authentication level, User Rights Assignment, AppLocker/WDAC.

**8. "ADMT: migrazione fallisce con 'Access Denied'"** → L'account che esegue ADMT non ha i permessi necessari. Requisiti: Domain Admin nel target, almeno Domain Admin o delegated permissions nel source, SID Filtering disabilitato sul trust. Verificare il trust: `netdom trust source.com /domain:target.com /verify`.

**9. "Autopilot: il device non mostra il branding aziendale all'OOBE"** → Il device non è registrato in Autopilot, o il profilo non è assegnato. Verificare: Intune → Devices → Windows Enrollment → Autopilot Devices → cercare il serial number. Se presente ma senza profilo: assegnare il profilo manualmente. Se non presente: raccogliere l'hardware hash e importarlo.

**10. "MDT: Task Sequence fallisce allo step 'Apply Operating System'"** → Cause comuni: immagine WIM corrotta (verificare con DISM /CheckImage), spazio disco insufficiente, driver WinPE mancanti (storage controller). Verificare il log: `X:\MININT\SMSOSD\OSDLOGS\BDD.log` (durante WinPE) o `C:\MININT\SMSOSD\OSDLOGS\BDD.log` (dopo apply).

**11. "Disaster Recovery: System State restore fallisce con 'version mismatch'"** → Il backup è di una versione diversa di Windows Server. System State restore funziona solo se la versione OS corrisponde esattamente (es. Server 2019 backup → Server 2019 restore). Non è possibile fare cross-version restore. Soluzione: usare la stessa versione OS per il restore.

**12. "LAPS: Get-LapsADPassword restituisce errore 'Access Denied'"** → L'account non ha i permessi per leggere la password LAPS. I permessi LAPS sono granulari: solo specifici gruppi possono leggere le password. Verificare con `Get-LapsADPassword -Identity "WKS-001" -AsPlainText` come membro del gruppo autorizzato. Concedere: `Set-LapsADReadPasswordPermission -Identity "OU=Computer,DC=corp,DC=contoso,DC=com" -AllowedPrincipals "CORP\IT-HelpDesk"`.

**13. "Dopo hardening server, RDP non funziona più"** → NLA (Network Level Authentication) abilitato ma il client non lo supporta, o il certificato RDP non è trusted. Verificare: la GPO ha impostato "Require use of specific security layer: SSL" o NLA obbligatorio. Fix temporaneo: consentire connessioni senza NLA. Fix permanente: distribuire certificato RDP trusted via GPO.

**14. "Credential Guard abilitato, ma alcune app non funzionano"** → Credential Guard impedisce l'uso di NTLM e credenziali delegate. App che usano NTLM diretto o CredSSP senza Kerberos falliscono. Esempio: SQL Server Management Studio con autenticazione Windows verso server non nel dominio. Fix: configurare Kerberos dove possibile, aggiungere eccezioni per app specifiche.

**15. "Manutenzione: WSUS database cresce senza controllo (> 30 GB)"** → Il database WSUS (SUSDB) non viene pulito regolarmente. Fix: `Invoke-WsusServerCleanup -CleanupObsoleteUpdates -CleanupUnneededContentFiles -CompressUpdates -DeclineExpiredUpdates -DeclineSupersededUpdates`. Schedulare mensilmente. Se il database è già troppo grande: reindex con script SQL (SUSDB-Maintenance.sql).

---

## FAQ

**Q1: MDT o Autopilot? Quando usare quale?**
MDT: per ambienti on-premise, reimaging completo, customizzazione avanzata dell'immagine, driver injection complessa, deployment di massa con WDS/PXE. Autopilot: per ambienti cloud-first, provisioning zero-touch, dispositivi acquistati direttamente dall'OEM, gestione con Intune. In molte organizzazioni coesistono: MDT per server e casi speciali, Autopilot per workstation standard.

**Q2: Qual è la differenza tra CIS Benchmark e Microsoft Security Baseline?**
CIS Benchmark è uno standard indipendente con due livelli (L1/L2) e copre più aspetti. Microsoft Security Baseline è specifico per prodotti Microsoft ed è ottimizzato per compatibilità. In pratica: applicare la Microsoft Security Baseline come punto di partenza, poi integrare con le raccomandazioni CIS L1 che non sono coperte. Per ambienti governativi/militari: usare i DISA STIGs (ancora più restrittivi).

**Q3: Ogni quanto devo testare il Disaster Recovery?**
Trimestrale per test di restore parziale (singolo server, singolo database). Annuale per un DR drill completo (simulazione disaster totale). Dopo ogni cambio infrastrutturale significativo (nuovo DC, nuova SAN, migrazione cloud). Il test di restore è l'UNICO modo per verificare che il backup funzioni davvero. Un backup non testato equivale a nessun backup.

**Q4: Come gestire il patching di 200+ server senza downtime?**
Usare un approccio ring-based: Ring 0 (lab, 1 settimana dopo Patch Tuesday), Ring 1 (non-critical servers, settimana 2), Ring 2 (server di produzione non-critici, settimana 3), Ring 3 (server critici con maintenance window, settimana 4). Per ogni ring: WSUS approval → patch → reboot → verification script. Per zero-downtime: cluster failover, live migration, rolling upgrade.

**Q5: Come implementare il Tiered Access Model senza bloccare tutto?**
Fase 1: Creare account admin separati per Tier 0 (admin.mrossi) — non usare l'account personale per admin DC. Fase 2: GPO "Deny logon" per impedire a Tier 0 di accedere a workstation (Tier 2). Fase 3: PAW (Privileged Access Workstation) dedicata per amministrazione Tier 0. Il tutto richiede 2-3 mesi per implementazione graduale. Non bloccare tutto in un giorno — rischio lockout.

**Q6: Quanto tempo richiede un deploy da zero di un dominio AD per 100 utenti?**
Con MDT/WDS preparato: 3-5 giorni lavorativi. Giorno 1: DC + AD + DNS + DHCP. Giorno 2: struttura OU + GPO base + DHCP failover. Giorno 3: file server + share + permessi. Giorno 4-5: imaging 100 workstation (batch da 20). Pre-requisito: naming convention e IP plan già definiti, hardware rack & stack completato.

**Q7: È sicuro usare In-Place Upgrade per i Domain Controller?**
Microsoft lo supporta ufficialmente da Windows Server 2012 R2+. Ma la best practice enterprise è: aggiungere un NUOVO DC con il nuovo OS → trasferire FSMO → demotare il vecchio DC → rimuovere. Motivo: se l'upgrade va male, il rollback di un DC in-place è quasi impossibile senza restore da backup. Con il metodo nuovo DC, il vecchio DC resta funzionante come fallback.

**Q8: Come gestire il hardening su server legacy (2012 R2) che non possono essere aggiornati?**
Applicare il massimo hardening possibile: disabilitare SMBv1, LLMNR, NetBIOS. Segmentare la rete: VLAN dedicata con firewall rules restrittive. Monitoring intensivo: Sysmon, log centralizzati. Pianificare la migrazione: il server 2012 R2 è fuori supporto — ogni mese senza patch è un rischio. Se non migrabile: valutare Azure Extended Security Updates (ESU) per patch critiche.

**Q9: Come automatizzare il deploy di GPO su un nuovo dominio?**
Esportare le GPO dal dominio template con `Backup-GPO -All`. Creare uno script che importa tutte le GPO con `Import-GPO` e le linka alle OU corrette con `New-GPLink`. Usare una Migration Table per tradurre SID e path tra domini. Versionare le GPO in un repository git come file XML. Testare sempre in un lab prima di applicare in produzione.

**Q10: Qual è il RTO e RPO ragionevole per un'infrastruttura PMI con 200 utenti?**
RPO (quanto dati posso perdere): 4-8 ore con backup notturni, 15-30 minuti con replica real-time. RTO (quanto tempo per ripristinare): 4 ore per DC (da backup), 2 ore per file server (restore dati), 8 ore per full recovery (tutti i servizi). Per PMI il target ragionevole è RPO 4h + RTO 8h. Investire in: backup testati, DC ridondante, documentazione procedure. Il costo del downtime guida l'investimento nel DR.

**Q11: Come posso verificare velocemente lo stato di hardening di un server?**
Usare CIS-CAT Lite (gratuito) per assessment automatizzato. Oppure uno script PowerShell che verifica: SMBv1 disabilitato, firewall attivo, servizi non necessari disabilitati, NLA abilitato per RDP, audit policy configurata, LAPS installato, BitLocker attivo. Confrontare con la baseline CIS L1 e generare un report pass/fail. Eseguire trimestralmente su tutti i server.

**Q12: Come gestire la manutenzione periodica con un team IT di 2-3 persone?**
Automazione è la chiave. Script schedulati per: health check giornaliero AD (dcdiag, replica, spazio disco), report settimanale patching compliance, pulizia mensile account inattivi, alert automatico per certificati in scadenza. Usare gMSA per gli script schedulati. Documentare ogni procedura manuale in runbook condiviso. Dedicare 1 giorno al mese per manutenzione proattiva.

**Q13: Come posso rendere il hardening client trasparente per gli utenti?**
(1) Comunicare PRIMA: email che spiega le modifiche e perché. (2) Roll-out graduale: ring-based, IT team prima. (3) Test approfondito: verificare che le app LOB funzionino con le nuove restrizioni. (4) Help desk preparato: FAQ pronte per le domande più comuni. (5) Eccezioni documentate: se un reparto ha bisogno di USB, creare GPO specifica per quel reparto.

**Q14: Backup: Windows Server Backup o soluzione enterprise (Veeam)?**
Windows Server Backup è gratuito e sufficiente per PMI piccole (< 5 server, RPO 24h). Limitazioni: no deduplica, no replica offsite, scheduling base, restore granulare limitato. Veeam/Commvault: per ambienti con 10+ server, SLA stringenti (RPO < 1h), necessità di replica offsite, restore granulare (singolo file/email/DB row), reporting compliance. Costo vs rischio: il costo di Veeam è irrisorio rispetto al costo del downtime.

**Q15: Come documentare l'infrastruttura in modo che sia aggiornata?**
Automazione anche per la documentazione. Script che genera: (1) Inventario server con ruoli e IP. (2) Topology AD con OU e GPO. (3) Mapping rete con VLAN e firewall rules. (4) Lista share con permessi. Eseguire mensilmente e salvare in una wiki (Confluence, SharePoint). Regola: ogni modifica infrastrutturale include l'aggiornamento della documentazione come step obbligatorio nel change management.

---

## Troubleshooting Avanzato — BSOD e Analisi Crash Dump

### Architettura dei Crash Dump Windows

Quando Windows incontra un errore irrecuperabile nel kernel-mode, genera un BSOD (Blue Screen of Death) e scrive un crash dump su disco.

**Tipi di dump:**

| Tipo | Dimensione | Contenuto | Uso |
|------|-----------|-----------|-----|
| Small Memory Dump (minidump) | 256 KB - 1 MB | Stack del thread, bugcheck code, driver caricati | Triage rapido |
| Kernel Memory Dump | ~1/3 RAM | Memoria kernel, driver, strutture | Analisi standard |
| Complete Memory Dump | = RAM | Tutto: kernel + user-mode | Debug avanzato, raro in produzione |
| Automatic Memory Dump | Come kernel, gestione dinamica pagefile | Memoria kernel | Default da Windows 8+ |
| Active Memory Dump | < Complete | Pagine attive, esclude free e zeroed | Hyper-V host |

**Configurazione dump:**
```powershell
# Verificare configurazione attuale
Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\CrashControl"
# CrashDumpEnabled:
#   0 = None
#   1 = Complete Memory Dump
#   2 = Kernel Memory Dump
#   3 = Small Memory Dump (minidump)
#   7 = Automatic Memory Dump (default)

# Impostare Kernel Memory Dump (raccomandato per server)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\CrashControl" `
    -Name "CrashDumpEnabled" -Value 2

# Abilitare scrittura automatica su file
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\CrashControl" `
    -Name "AutoReboot" -Value 1

# Percorso dump file
# Default: %SystemRoot%\MEMORY.DMP (kernel/complete)
# Minidump: %SystemRoot%\Minidump\MMDDYY-NNNNN.dmp

# Verificare che il pagefile sia sufficiente
Get-CimInstance Win32_PageFileUsage | Select-Object Name, AllocatedBaseSize, CurrentUsage
# Il pagefile deve essere >= RAM per Complete Dump
# Per Kernel Dump: pagefile >= ~1/3 RAM (o gestione automatica)
```

### Analisi con WinDbg — Guida Passo-Passo

```
# === INSTALLAZIONE ===
# Scaricare WinDbg da Microsoft Store o Windows SDK
# Oppure: WinDbg Preview (versione moderna, consigliata)
# winget install Microsoft.WinDbg

# === CONFIGURARE I SYMBOL ===
# File → Settings → Debugging Settings → Symbol Path:
# srv*C:\Symbols*https://msdl.microsoft.com/download/symbols
#
# Oppure via variabile d'ambiente:
# _NT_SYMBOL_PATH=srv*C:\Symbols*https://msdl.microsoft.com/download/symbols

# === APRIRE IL DUMP ===
# File → Open Crash Dump → selezionare MEMORY.DMP o minidump

# === COMANDI FONDAMENTALI WinDbg ===

# Analisi automatica (PRIMO COMANDO da eseguire sempre)
!analyze -v

# Output chiave da leggere:
# BUGCHECK_CODE:       0x0000001A  → codice errore esadecimale
# BUGCHECK_P1-P4:      parametri specifici del bugcheck
# PROCESS_NAME:        processo colpevole
# MODULE_NAME:         driver/modulo responsabile
# FAILURE_BUCKET_ID:   identificatore univoco del crash
# STACK_TEXT:           stack trace al momento del crash

# Elencare i driver caricati
lm                    # lista moduli
lm v m <driver>       # dettagli versione di un driver specifico

# Stack trace del thread che ha causato il BSOD
kv                    # stack con parametri
kb                    # stack con primi 3 parametri

# Informazioni sul processo
!process 0 0          # lista tutti i processi
!process <addr> 7     # dettagli completi di un processo

# Informazioni sul thread corrente
!thread

# Pool memory analysis (per POOL_CORRUPTION/IRQL)
!poolused 2           # ordinato per utilizzo pool paged
!poolused 4           # ordinato per utilizzo pool nonpaged

# Verificare integrità del driver
!verifier             # stato del Driver Verifier

# Controllare l'IRQ level
!irql

# Cercare un pattern nello stack
!for_each_thread "!thread @#Thread; .if(@@(@#Thread->Tcb.State) != 5) {kv}"
```

### Bugcheck Code Comuni e Soluzioni

| Bugcheck | Nome | Causa Tipica | Azione |
|----------|------|-------------|--------|
| 0x0A | IRQL_NOT_LESS_OR_EQUAL | Driver accede memoria a IRQL errato | Aggiornare/rimuovere driver recente |
| 0x1A | MEMORY_MANAGEMENT | RAM difettosa o driver corrotto | `mdsched.exe` per test RAM, poi driver |
| 0x1E | KMODE_EXCEPTION_NOT_HANDLED | Eccezione non gestita in kernel-mode | !analyze -v per identificare il driver |
| 0x24 | NTFS_FILE_SYSTEM | Corruzione NTFS o controller disco | `chkdsk /f`, verificare SMART |
| 0x3B | SYSTEM_SERVICE_EXCEPTION | Eccezione in system call | Stack trace indica il modulo colpevole |
| 0x50 | PAGE_FAULT_IN_NONPAGED_AREA | Accesso a memoria non valida | RAM difettosa o driver con bug |
| 0x7E | SYSTEM_THREAD_EXCEPTION_NOT_HANDLED | Thread kernel con eccezione non gestita | Aggiornare driver nel MODULE_NAME |
| 0x9F | DRIVER_POWER_STATE_FAILURE | Driver non gestisce transizione power | Aggiornare driver, disabilitare risparmio |
| 0xC2 | BAD_POOL_CALLER | Allocazione pool invalida | Driver con bug: aggiornare o rimuovere |
| 0xD1 | DRIVER_IRQL_NOT_LESS_OR_EQUAL | Come 0x0A ma con info driver | Driver indicato nel crash dump |
| 0x133 | DPC_WATCHDOG_VIOLATION | DPC impiega troppo tempo | Storage driver lento, firmware, SSD |
| 0x139 | KERNEL_SECURITY_CHECK_FAILURE | Buffer overflow nel kernel | Aggiornare driver/OS, verificare integrità |

```powershell
# === Script: Raccogliere info BSOD recenti ===
# Leggere gli eventi di crash dal System Event Log
Get-WinEvent -FilterHashtable @{
    LogName = 'System'
    Id = 1001   # BugCheck event
} -MaxEvents 10 | ForEach-Object {
    [PSCustomObject]@{
        TimeCreated  = $_.TimeCreated
        BugcheckCode = $_.Properties[0].Value
        Parameter1   = $_.Properties[1].Value
        Parameter2   = $_.Properties[2].Value
        DumpFile     = $_.Properties[4].Value
    }
} | Format-Table -AutoSize

# Controllare le minidump disponibili
Get-ChildItem "$env:SystemRoot\Minidump" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object Name, LastWriteTime, @{N='SizeKB';E={[math]::Round($_.Length/1KB)}}
```

---

## Troubleshooting Avanzato — Performance Bottleneck

### Diagnosi Sistematica con Performance Monitor

```powershell
# === I 4 PILASTRI: CPU, RAM, Disco, Rete ===

# --- CPU ---
# Verificare utilizzo CPU
Get-Counter '\Processor(_Total)\% Processor Time' -SampleInterval 2 -MaxSamples 5

# Identificare il processo che consuma più CPU
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 Name, CPU, Id, WorkingSet64

# Verificare la coda del processore (> 2 per core = collo di bottiglia)
Get-Counter '\System\Processor Queue Length' -SampleInterval 2 -MaxSamples 5

# --- MEMORIA ---
# Disponibilità memoria (< 200 MB = critico)
Get-Counter '\Memory\Available MBytes' -SampleInterval 2 -MaxSamples 5

# Pages/sec (> 1000 = paging eccessivo, probabile bottleneck RAM)
Get-Counter '\Memory\Pages/sec' -SampleInterval 2 -MaxSamples 5

# Processi ordinati per consumo memoria
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 10 `
    Name, Id, @{N='WorkingSetMB';E={[math]::Round($_.WorkingSet64/1MB)}},
    @{N='PrivateMB';E={[math]::Round($_.PrivateMemorySize64/1MB)}}

# Pool memory (kernel)
Get-Counter '\Memory\Pool Paged Bytes','\Memory\Pool Nonpaged Bytes'

# --- DISCO ---
# Latenza disco (> 20ms = lento, > 50ms = critico)
Get-Counter '\PhysicalDisk(*)\Avg. Disk sec/Read','\PhysicalDisk(*)\Avg. Disk sec/Write' `
    -SampleInterval 2 -MaxSamples 5

# Coda disco (> 2 per spindle = saturazione)
Get-Counter '\PhysicalDisk(*)\Avg. Disk Queue Length' -SampleInterval 2 -MaxSamples 5

# IOPS
Get-Counter '\PhysicalDisk(*)\Disk Reads/sec','\PhysicalDisk(*)\Disk Writes/sec'

# Spazio disco
Get-CimInstance Win32_LogicalDisk | Where-Object { $_.DriveType -eq 3 } |
    Select-Object DeviceID, 
    @{N='SizeGB';E={[math]::Round($_.Size/1GB,1)}},
    @{N='FreeGB';E={[math]::Round($_.FreeSpace/1GB,1)}},
    @{N='Free%';E={[math]::Round(($_.FreeSpace/$_.Size)*100,1)}}

# --- RETE ---
# Throughput interfacce
Get-Counter '\Network Interface(*)\Bytes Total/sec' -SampleInterval 2 -MaxSamples 3

# Errori di rete
Get-Counter '\Network Interface(*)\Packets Received Errors',
            '\Network Interface(*)\Packets Outbound Errors'

# Connessioni TCP attive
Get-Counter '\TCPv4\Connections Active'
```

### Data Collector Set — Monitoraggio Automatico

```powershell
# Creare un Data Collector Set per monitoraggio 24h
$counters = @(
    '\Processor(_Total)\% Processor Time'
    '\Memory\Available MBytes'
    '\Memory\Pages/sec'
    '\PhysicalDisk(_Total)\Avg. Disk Queue Length'
    '\PhysicalDisk(_Total)\Avg. Disk sec/Read'
    '\PhysicalDisk(_Total)\Avg. Disk sec/Write'
    '\Network Interface(*)\Bytes Total/sec'
    '\System\Processor Queue Length'
    '\Process(*)\% Processor Time'
    '\Process(*)\Working Set'
)

# Logman per creare il collector (via cmd/logman, PowerShell non ha cmdlet nativo)
logman create counter "Perf-24h-Baseline" `
    -c $counters `
    -si 15 `
    -f csv `
    -o "C:\PerfLogs\Baseline" `
    -max 500 `
    --v

# Avviare la raccolta
logman start "Perf-24h-Baseline"

# Dopo 24h, fermare e analizzare
logman stop "Perf-24h-Baseline"
# Aprire il CSV in Excel o con PAL (Performance Analysis of Logs)
```

### Soglie di Allarme — Reference Card

| Contatore | Verde | Giallo | Rosso |
|-----------|-------|--------|-------|
| CPU % Total | < 70% | 70-85% | > 85% sostenuto |
| Processor Queue | < 2×core | 2-3×core | > 3×core |
| Available MB | > 1 GB | 200 MB - 1 GB | < 200 MB |
| Pages/sec | < 500 | 500-1000 | > 1000 |
| Disk sec/Read | < 10 ms | 10-20 ms | > 20 ms |
| Disk Queue | < 2 | 2-4 | > 4 |
| Net Errors | 0 | < 1% pacchetti | > 1% pacchetti |

---

## WPR/WPA — Tracciamento Performance Avanzato

### Architettura ETW e Windows Performance Toolkit

Windows Performance Toolkit (WPT) è il framework Microsoft per il profiling avanzato del sistema operativo. Si compone di due strumenti complementari: **Windows Performance Recorder (WPR)** per la registrazione delle tracce ETW (Event Tracing for Windows), e **Windows Performance Analyzer (WPA)** per l'analisi grafica dei dati raccolti. A differenza dei contatori Performance Monitor, WPR/WPA catturano eventi a livello kernel con overhead minimo, permettendo di diagnosticare problemi impossibili da individuare con i soli perfmon counters.

**Installazione:**
```powershell
# WPT è incluso nel Windows ADK (Assessment and Deployment Kit)
# Scaricare Windows ADK per Windows 11 dal sito Microsoft
# Durante l'installazione selezionare "Windows Performance Toolkit"

# Alternativa: installare WPA dal Microsoft Store
# winget install "Microsoft.WPA"

# Verificare installazione
wpr.exe -profiles   # lista profili disponibili
# Output: profili built-in come CPU, DiskIO, FileIO, GPU, Heap, VirtualAlloc, etc.
```

### Registrazione con WPR — Profili e Scenari

```powershell
# ============================================================
# SCENARIO 1: CPU Bottleneck — Identificare chi consuma CPU
# ============================================================

# Avviare registrazione con profilo CPU (sampling + context switch)
wpr -start CPU -start DiskIO -start FileIO

# ... riprodurre il problema (es. applicazione lenta per 30-60 secondi) ...

# Fermare e salvare la traccia
wpr -stop C:\PerfTraces\cpu-analysis.etl "Analisi CPU bottleneck su SRV-APP-01"

# ============================================================
# SCENARIO 2: Boot Lento — Analisi Tempi di Avvio
# ============================================================

# Il profilo GeneralProfile cattura tutto durante il boot
# Abilitare il boot tracing (persiste al reboot)
wpr -boottrace -addboot GeneralProfile

# Riavviare il sistema
# Al login, WPR ferma automaticamente la traccia
# Oppure fermare manualmente:
wpr -boottrace -stopboot C:\PerfTraces\boot-trace.etl

# Cancellare boot trace se non serve più
wpr -boottrace -cancelboot

# ============================================================
# SCENARIO 3: Disk I/O — Latenza Disco Elevata
# ============================================================

# Catturare attività disco dettagliata
wpr -start DiskIO -start FileIO -filemode

# Il flag -filemode scrive direttamente su file anziché buffer circolare
# Utile per sessioni di registrazione lunghe (> 5 minuti)

# Fermare
wpr -stop C:\PerfTraces\disk-analysis.etl "Analisi latenza disco"

# ============================================================
# SCENARIO 4: Profilo Personalizzato (XML)
# ============================================================

# I profili custom .wprp permettono di selezionare provider ETW specifici
# Esempio: catturare solo eventi di rete e DNS
# File: C:\PerfTraces\network-profile.wprp
# Struttura XML con <Profile>, <Collector>, <EventProvider>
# Provider utili:
#   Microsoft-Windows-TCPIP           {2F07E2EE-15DB-40F1-90EF-9D7BA282188A}
#   Microsoft-Windows-DNS-Client      {1C95126E-7EEA-49A9-A3FE-A378B03DDB4D}
#   Microsoft-Windows-Winsock-AFD     {E53C6823-7BB8-44BB-90DC-3F86090D3F42}

wpr -start C:\PerfTraces\network-profile.wprp
# ... riprodurre il problema di rete ...
wpr -stop C:\PerfTraces\net-analysis.etl
```

### Analisi con WPA — Metodologia Passo-Passo

```
# ============================================================
# APERTURA E NAVIGAZIONE IN WPA
# ============================================================

# 1. Aprire WPA e caricare il file .etl
#    File → Open → selezionare il file .etl

# 2. Pannello Graph Explorer (sinistra)
#    Organizzato per categorie: Computation, Storage, Memory, Network, etc.
#    Trascinare i grafici nella Analysis Area (centro) per visualizzarli

# === ANALISI CPU ===

# Grafico chiave: Computation → CPU Usage (Sampled)
# Colonne da aggiungere (tasto destro sulla tabella → Open View Editor):
#   Process, Thread ID, Stack, Weight (ms), % Weight
#
# Tecnica "drill-down":
# 1. Selezionare l'intervallo temporale con il problema (zoom con mouse)
# 2. Ordinare per "% Weight" discendente → il processo più pesante è in cima
# 3. Espandere lo stack del processo → seguire il call stack fino alla
#    funzione specifica che consuma CPU
# 4. Se il modulo è un driver (.sys) → aggiornare o sostituire
# 5. Se è codice applicativo → ottimizzare la funzione identificata

# Grafico: Computation → CPU Usage (Precise) — per context switch
# Mostra esattamente QUANDO un thread viene sospeso e da CHI
# Utile per: attese I/O, lock contention, priority inversion
# Colonne: NewProcess, ReadyingProcess, SwitchInTime, TimeSinceLast(us)

# === ANALISI DISCO ===

# Grafico: Storage → Disk Usage
# Colonne: Process, IO Type (Read/Write/Flush), Path, Size, Duration(ms)
# Ordinare per Duration → identifica le operazioni I/O più lente
# Pattern comuni:
#   - Molte piccole letture random → frammentazione o accesso non ottimizzato
#   - Flush frequenti → journaling eccessivo o applicazione che forza sync
#   - Latenza > 50ms → disco saturo o controller problematico

# === ANALISI BOOT ===

# Grafico: Other → Boot Phases
# Mostra le fasi del boot: PreSession, WinLogon, Explorer, PostBoot
# Identificare quale fase è lenta:
#   - PreSession lento → driver o servizio che blocca il boot
#   - WinLogon lento → GPO processing, autenticazione
#   - Explorer lento → shell extensions, startup programs
#   - PostBoot lento → applicazioni in avvio automatico

# === ANALISI MEMORIA ===

# Grafico: Memory → Virtual Memory Snapshots
# Mostra: Commit Charge, Working Set, Shared/Private per processo
# Pattern: Working Set che cresce senza mai scendere = memory leak
# Confrontare snapshot a inizio e fine registrazione

# === ESPORTAZIONE RISULTATI ===
# File → Export → CSV o HTML per condividere con il team
# Profile → Save Startup Profile → salvare layout personalizzato
```

### WPR/WPA — Reference Card Scenari

| Problema | Profilo WPR | Grafico WPA | Cosa Cercare |
|----------|-------------|-------------|--------------|
| App lenta | CPU + DiskIO | CPU Usage (Sampled) | Stack con % Weight elevato |
| Boot lento | GeneralProfile (boot) | Boot Phases | Fase più lunga, driver/servizi lenti |
| Freeze/hang | CPU (Precise) | CPU Usage (Precise) | Thread in attesa, ReadyingProcess |
| Disco saturo | DiskIO + FileIO | Disk Usage | IO con Duration > 50ms, processo |
| Memory leak | Heap + VirtualAlloc | Virtual Memory | Commit crescente senza rilascio |
| Rete lenta | Network (custom) | Generic Events | Latenza DNS, retransmit TCP |

---

## Sysinternals — Analisi Approfondita

### Process Monitor — Filtri Avanzati e Ricette

Process Monitor (ProcMon) cattura in tempo reale attività di file system, registro e rete per ogni processo. La chiave per un uso efficace è la strategia di filtraggio: senza filtri, ProcMon genera milioni di eventi in pochi minuti, rendendo impossibile l'analisi.

```powershell
# ============================================================
# INSTALLAZIONE E AVVIO
# ============================================================

# Scaricare da: https://learn.microsoft.com/sysinternals/downloads/procmon
# Oppure: winget install sysinternals (suite completa)
# Eseguire come amministratore: Procmon64.exe

# ============================================================
# FILTRI ESSENZIALI — CONFIGURAZIONE BASE
# ============================================================
# Menu: Filter → Filter... (Ctrl+L)
# Struttura filtro: [Column] [Relation] [Value] [Action]

# --- RICETTA 1: Diagnosi "Applicazione non si avvia" ---
# Filtrare per nome processo e risultati di errore
# Process Name  is   myapp.exe        Include
# Result        is not  SUCCESS       Include
# Questo mostra SOLO le operazioni fallite dell'applicazione
# Cercare: NAME NOT FOUND (DLL mancante), ACCESS DENIED (permessi),
#          PATH NOT FOUND (percorso errato)

# --- RICETTA 2: Trovare quale processo blocca un file ---
# Path    contains   NomeFile.docx     Include
# Operation  is      CreateFile        Include
# Controllare la colonna "Detail" per: Sharing Violation, Access Denied
# Il processo che ha il lock è quello con l'handle aperto

# --- RICETTA 3: Monitoraggio modifiche registro ---
# Diagnosticare problemi di GPO o installazione software
# Operation  begins with  Reg          Include
# Path       contains     SOFTWARE\Policies   Include
# Cattura: RegSetValue, RegCreateKey, RegDeleteValue su chiavi policy
# Utile per verificare se una GPO scrive effettivamente nel registro

# --- RICETTA 4: Diagnosi "Servizio non si avvia" ---
# Process Name  is   svchost.exe     Include
# Result        is not  SUCCESS      Include
# Category      is   File System     Include
# Cercare: DLL mancanti, file di configurazione non trovati

# --- RICETTA 5: Escludere rumore di sistema ---
# Aggiungere filtri EXCLUDE per ridurre il rumore:
# Process Name  is  System           Exclude
# Process Name  is  Procmon64.exe    Exclude
# Process Name  is  svchost.exe      Exclude   (se non è il target)
# Operation     is  RegQueryValue    Exclude   (molto frequente, poco utile)
# Path     begins with  HKLM\SYSTEM\CurrentControlSet\Services\Tcpip  Exclude
# Path     begins with  C:\Windows\Prefetch  Exclude

# ============================================================
# FUNZIONALITÀ AVANZATE
# ============================================================

# --- Process Tree ---
# Menu: Tools → Process Tree (Ctrl+T)
# Mostra la gerarchia padre-figlio dei processi
# Fondamentale per: identificare processi figli sospetti
# Esempio: powershell.exe → cmd.exe → certutil.exe = possibile download malevolo

# --- Stack Trace ---
# Doppio click su qualsiasi evento → tab "Stack"
# Mostra il call stack completo al momento dell'operazione
# Con i symbol configurati (Options → Configure Symbols → percorso symbol server)
# si vedono i nomi delle funzioni esatte

# --- Boot Logging ---
# Options → Enable Boot Logging
# ProcMon inizia a registrare dal boot (prima del login)
# Al successivo avvio di ProcMon, chiede se caricare il boot log
# Utile per: servizi che falliscono all'avvio, driver che causano lentezza

# --- Colonna "Process Start Time" (v4.0+, aggiornamento giugno 2024) ---
# Nuova colonna che mostra il timestamp di avvio del processo
# Permette di filtrare per processi avviati in un intervallo specifico
# Utile per: identificare processi creati durante un incidente

# --- Salvataggio e condivisione ---
# File → Save (PML nativo, richiede ProcMon per riaprire)
# File → Export → CSV / XML (per analisi con script o SIEM)
```

### Autoruns — Caccia alla Persistenza

Autoruns è lo strumento definitivo per l'analisi degli Auto-Start Extensibility Points (ASEP) di Windows. Mostra TUTTI i meccanismi che un programma (o malware) può usare per avviarsi automaticamente.

```powershell
# ============================================================
# AUTORUNS — CATEGORIE DI PERSISTENZA (14+ ASEP)
# ============================================================

# Eseguire come amministratore: Autoruns64.exe
# O versione CLI: autorunsc64.exe -a * -c > autoruns-baseline.csv

# === TAB PRINCIPALI ===

# LOGON
# Chiavi Run/RunOnce nel registro (HKLM e HKCU)
# Cartella Startup: %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
# Shell: explorer.exe (se sostituito → rootkit)
# Userinit: userinit.exe (se modificato → persistenza malevola)

# SCHEDULED TASKS
# Task Scheduler: tutte le attività pianificate
# Malware crea spesso task con nomi simili a quelli di sistema
# Controllare: task con azioni che puntano a temp, appdata, percorsi insoliti
# Task con trigger "At system startup" o "At user logon" sono i più sospetti

# SERVICES
# Tutti i servizi Windows registrati
# Servizi sospetti: nome generico, percorso in cartella temp, senza firma digitale
# Colonna "Publisher": se non verificato o sconosciuto → investigare

# DRIVERS
# Driver kernel-mode e filter driver
# Driver non firmati (evidenziati in rosso/rosa) → rischio elevato
# Driver firmati da publisher sconosciuti → verificare

# WINLOGON
# Notifiche Winlogon, Credential Providers, shell overrides
# Alterazioni = persistenza avanzata o credential theft

# WINSOCK PROVIDERS (LSP)
# Layered Service Providers: intercettano il traffico di rete
# LSP sospetti possono sniffare credenziali o redirigere traffico

# PRINT MONITORS
# DLL caricate dal servizio Print Spooler
# Tecnica di persistenza nota: PrintNightmare e varianti

# APPINIT DLLS
# DLL caricate in OGNI processo che importa user32.dll
# Usato storicamente per injection: se presente → sospetto

# OFFICE ADD-INS
# Plugin Office che si caricano all'avvio di Word, Excel, Outlook
# Add-in sconosciuti possono essere macro-persistenza

# BOOT EXECUTE
# Programmi eseguiti durante il boot di Windows (Session Manager)
# Default: autocheck autochk * — qualsiasi altra voce → investigare

# IMAGE HIJACKS (IFEO)
# Image File Execution Options: permette di sostituire un eseguibile
# Tecnica: aggiungere Debugger a calc.exe che lancia malware.exe
# Anche: SilentProcessExit può essere abusato per persistenza

# KNOWN DLLS
# DLL conosciute dal sistema e pre-caricate
# Se modificate → DLL hijacking

# PACKAGED APPS (Autoruns v14.2+, aggiornamento 2024-2025)
# Nuova categoria per le app UWP/MSIX con meccanismi di auto-start
# Le app pacchettizzate usano manifest XML per registrare startup tasks
# Autoruns v14.2 ispeziona questi manifest rivelando persistenze nascoste

# ============================================================
# WORKFLOW: CACCIA ALLA PERSISTENZA
# ============================================================

# 1. BASELINE: catturare lo stato "pulito" del sistema
autorunsc64.exe -accepteula -a * -c -h -s -v -vt > C:\Baseline\autoruns-clean.csv
# -c = CSV, -h = include hash, -s = verify signatures,
# -v = verify code signatures (online), -vt = check VirusTotal

# 2. CONFRONTO: dopo un incidente o periodicamente
autorunsc64.exe -accepteula -a * -c -h -s -v -vt > C:\Baseline\autoruns-current.csv

# 3. Comparare con PowerShell:
$baseline = Import-Csv C:\Baseline\autoruns-clean.csv
$current = Import-Csv C:\Baseline\autoruns-current.csv
$new = Compare-Object $baseline $current -Property "Image Path","Entry" -PassThru |
    Where-Object SideIndicator -eq "=>"
$new | Format-Table "Entry Location", "Entry", "Image Path", "Publisher" -AutoSize
# Le voci presenti in current ma non in baseline sono NUOVE → investigare

# 4. INDICATORI DI COMPROMISSIONE:
# - Entry senza firma digitale (Publisher vuoto o "Not Verified")
# - Image Path in cartelle temp: %TEMP%, %APPDATA%, C:\ProgramData
# - Entry con nomi che imitano processi legittimi (es. "svchost" in posizione errata)
# - Hash sconosciuto su VirusTotal (VT detection > 0)
# - Entry aggiunte dopo la data dell'ultimo baseline
```

### ProcDump — Dump di Processi per Diagnosi Live

```powershell
# ProcDump genera dump di memoria di processi in esecuzione
# senza terminare il processo (non invasivo)

# Dump quando un processo supera il 90% CPU per 10 secondi
procdump64.exe -ma -c 90 -s 10 -n 3 myapp.exe C:\Dumps\
# -ma = full dump, -c = soglia CPU, -s = secondi sostenuti, -n = numero dump

# Dump quando il processo consuma > 1 GB di memoria (memory leak)
procdump64.exe -ma -m 1024 myapp.exe C:\Dumps\

# Dump su eccezione non gestita (crash)
procdump64.exe -ma -e 1 myapp.exe C:\Dumps\

# Dump di un processo e di tutto il suo albero di processi (ProcDump v12.0+)
procdump64.exe -ma -pt myapp.exe C:\Dumps\
# Il flag -pt cattura il dump di ogni processo figlio ricorsivamente
# Utile per: servizi con worker processes, app con processi helper

# Installare come debugger JIT (post-mortem) per catturare tutti i crash
procdump64.exe -ma -i C:\Dumps\
# Ora ogni crash di qualsiasi applicazione genera un dump in C:\Dumps\
# Disinstallare: procdump64.exe -u
```

---

## DISM — Operazioni Avanzate e Component Store

### Anatomia del Component Store (WinSxS)

La cartella `C:\Windows\WinSxS` è il Component Store di Windows: contiene tutte le versioni di ogni componente del sistema (DLL, driver, file di manifesto). La sua dimensione apparente è spesso fuorviante a causa degli hard link: molti file in WinSxS sono hard link a file nelle directory di sistema e non occupano spazio aggiuntivo.

```powershell
# ============================================================
# ANALISI DEL COMPONENT STORE
# ============================================================

# Verificare la dimensione reale del Component Store
Dism /Online /Cleanup-Image /AnalyzeComponentStore

# Output chiave:
# Component Store (WinSxS) Size:                   8.42 GB
# Shared with Windows:                              6.31 GB  (hard link, non occupano spazio extra)
# Backups and Disabled Features:                    1.28 GB
# Cache and Temporary Data:                         0.83 GB
# Component Store Cleanup Recommended:              Yes / No
#
# "Shared with Windows" = spazio che NON si recupera eliminando WinSxS
# "Backups and Disabled Features" = spazio recuperabile con cleanup

# ============================================================
# OPERAZIONI DI PULIZIA — DAL MENO AL PIÙ AGGRESSIVO
# ============================================================

# LIVELLO 1: Pulizia standard
# Rimuove versioni precedenti di componenti aggiornati (grace period 30gg)
Dism /Online /Cleanup-Image /StartComponentCleanup

# Equivalente a: Task Scheduler → Microsoft → Windows → Servicing → StartComponentCleanup
# Differenza: il comando DISM ignora il grace period di 30 giorni

# LIVELLO 2: Reset base (IRREVERSIBILE)
# Rimuove TUTTE le versioni superseded, elimina il delta di rollback
Dism /Online /Cleanup-Image /StartComponentCleanup /ResetBase

# ATTENZIONE CRITICA: dopo /ResetBase NON è più possibile disinstallare
# gli aggiornamenti precedentemente installati
# Usare SOLO su immagini master per deployment, o dopo aver confermato
# che gli update correnti sono stabili
# Microsoft sconsiglia /ResetBase su macchine di produzione in alcuni scenari

# LIVELLO 3: Rimuovere feature disabilitate
# Le feature Windows disabilitate mantengono i payload su disco (Feature on Demand)
Dism /Online /Cleanup-Image /StartComponentCleanup /ResetBase
# Per feature specifiche:
Dism /Online /Disable-Feature /FeatureName:WindowsMediaPlayer /Remove
# /Remove elimina il payload dal disco; se necessario in futuro,
# Windows lo scarica da Windows Update

# ============================================================
# PIPELINE DI REPAIR: CheckHealth → ScanHealth → RestoreHealth
# ============================================================

# STEP 1: CheckHealth — verifica rapida (secondi)
# Controlla se il flag "repairable" è impostato da una scansione precedente
Dism /Online /Cleanup-Image /CheckHealth
# Output: "The component store is repairable" oppure "No component store corruption detected"
# NON esegue una scansione: legge solo il flag

# STEP 2: ScanHealth — scansione approfondita (5-15 minuti)
# Verifica l'integrità di ogni componente nel Component Store
Dism /Online /Cleanup-Image /ScanHealth
# Analizza i manifesti, verifica hash, controlla riferimenti incrociati
# Se trova corruzione → imposta il flag che CheckHealth legge

# STEP 3: RestoreHealth — riparazione (15-60 minuti)
# Scarica i componenti corrotti da Windows Update e li sostituisce
Dism /Online /Cleanup-Image /RestoreHealth
# Richiede connessione Internet (download da Windows Update)

# Se la macchina non ha accesso a Internet, specificare una sorgente locale:
# Montare una ISO di Windows e usare install.wim come sorgente
Dism /Online /Cleanup-Image /RestoreHealth /Source:WIM:D:\sources\install.wim:1
# :1 = indice dell'edizione nell'immagine WIM (1 = prima edizione)

# Sorgente alternativa: una cartella Windows montata
Dism /Online /Cleanup-Image /RestoreHealth /Source:D:\MountedWindows\Windows

# Limitare la ricerca alla sola sorgente locale (non contattare WU)
Dism /Online /Cleanup-Image /RestoreHealth /Source:WIM:D:\sources\install.wim:1 /LimitAccess

# ============================================================
# ORDINE CORRETTO: DISM prima, poi SFC
# ============================================================
# DISM ripara il Component Store (la "fonte" di file puliti)
# SFC ripara i file di sistema usando il Component Store come sorgente
# Se si esegue SFC prima di DISM e il Component Store è corrotto,
# SFC non riesce a riparare perché la sua sorgente è compromessa

# Pipeline completa di repair:
Dism /Online /Cleanup-Image /RestoreHealth
# Attendere completamento...
sfc /scannow
# Verificare risultato nel CBS log:
findstr /c:"[SR]" %SystemRoot%\Logs\CBS\CBS.log > %USERPROFILE%\Desktop\sfcdetails.txt
# Cercare: "[SR] Cannot repair member file" = file non riparabili

# ============================================================
# GESTIONE FEATURE WINDOWS
# ============================================================

# Elencare tutte le feature e il loro stato
Dism /Online /Get-Features /Format:Table
# Output: FeatureName | State (Enabled / Disabled / Enable Pending)

# PowerShell equivalente:
Get-WindowsOptionalFeature -Online | Sort-Object State -Descending |
    Select-Object FeatureName, State | Format-Table -AutoSize

# Abilitare una feature (es. Hyper-V)
Dism /Online /Enable-Feature /FeatureName:Microsoft-Hyper-V-All /All
# /All = abilita anche le feature dipendenti

# PowerShell:
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All -All

# Disabilitare una feature
Dism /Online /Disable-Feature /FeatureName:SMB1Protocol
# Senza /Remove: il payload resta su disco (riabilitazione offline possibile)
# Con /Remove: payload rimosso, richiede download da WU per riabilitare

# ============================================================
# OFFLINE SERVICING — Aggiornare immagini senza avviare l'OS
# ============================================================

# Montare immagine WIM per servicing offline
$mountDir = "C:\Mount\Offline"
New-Item $mountDir -ItemType Directory -Force
Dism /Mount-Image /ImageFile:D:\images\install.wim /Index:1 /MountDir:$mountDir

# Aggiungere un aggiornamento cumulativo all'immagine offline
Dism /Image:$mountDir /Add-Package /PackagePath:C:\Updates\windows11-kb5044567.msu

# Aggiungere driver all'immagine offline
Dism /Image:$mountDir /Add-Driver /Driver:C:\Drivers\NIC /Recurse

# Abilitare feature nell'immagine offline
Dism /Image:$mountDir /Enable-Feature /FeatureName:NetFx3 /Source:D:\sources\sxs

# Pulizia dell'immagine offline prima del commit
Dism /Image:$mountDir /Cleanup-Image /StartComponentCleanup /ResetBase

# Commit e smontaggio
Dism /Unmount-Image /MountDir:$mountDir /Commit
# /Discard per annullare le modifiche
```

### DISM e CBS Log — Analisi Errori

```powershell
# Il log DISM è in: C:\Windows\Logs\DISM\dism.log
# Il log CBS (Component Based Servicing): C:\Windows\Logs\CBS\CBS.log
# CBS è la fonte primaria per errori di aggiornamento e servicing

# Filtrare errori DISM
Select-String -Path "$env:SystemRoot\Logs\DISM\dism.log" -Pattern "Error|HRESULT|Failed" |
    Select-Object -Last 30 | Format-Table LineNumber, Line -AutoSize

# Errori CBS comuni:
# 0x800F081F — Source files non trovati → specificare /Source con WIM/ISO
# 0x80073712 — Component store corrotto → eseguire RestoreHealth con sorgente esterna
# 0x800F0922 — Spazio insufficiente nella partizione System Reserved
# 0x80070003 — Path non trovato → verificare /Source path e indice WIM
# 0x800F0906 — Download fallito → verificare proxy, DNS, firewall per WU

# Analisi CBS per SFC:
# Le entry SFC nel CBS.log sono marcate con [SR]
# "[SR] Repairing corrupted file" = file corrotto riparato con successo
# "[SR] Cannot repair member file" = riparazione fallita → DISM first
# "[SR] Verify complete" = nessuna corruzione trovata
```

---

## Troubleshooting Avanzato — Rete

### Diagnostica Completa di Rete

```powershell
# === LIVELLO 1: Connettività Base ===
# Ping e tracert (con timestamp)
Test-NetConnection -ComputerName "DC01.corp.contoso.com" -Port 389 -InformationLevel Detailed
Test-NetConnection -ComputerName "8.8.8.8" -TraceRoute

# === LIVELLO 2: Risoluzione DNS ===
# Verificare risoluzione DNS
Resolve-DnsName "DC01.corp.contoso.com" -Type A
Resolve-DnsName "_ldap._tcp.dc._msdcs.corp.contoso.com" -Type SRV  # SRV record DC
Resolve-DnsName "_kerberos._tcp.corp.contoso.com" -Type SRV         # Kerberos SRV

# Flush e verifica cache DNS
Clear-DnsClientCache
Get-DnsClientCache | Format-Table -AutoSize

# DNS server configurati
Get-DnsClientServerAddress | Where-Object { $_.AddressFamily -eq 2 } |
    Select-Object InterfaceAlias, ServerAddresses

# === LIVELLO 3: Porte e Servizi ===
# Verificare porte AD critiche
$adPorts = @(53,88,135,139,389,445,464,636,3268,3269)
$dc = "DC01.corp.contoso.com"
foreach ($port in $adPorts) {
    $result = Test-NetConnection -ComputerName $dc -Port $port -WarningAction SilentlyContinue
    $status = if ($result.TcpTestSucceeded) { "OPEN" } else { "BLOCKED" }
    Write-Output "Port $port : $status"
}

# === LIVELLO 4: Netsh Trace (cattura pacchetti nativa) ===
# Avviare cattura (non richiede tool aggiuntivi)
netsh trace start capture=yes tracefile=C:\Temp\nettrace.etl maxsize=512 overwrite=yes

# ... riprodurre il problema ...

# Fermare la cattura
netsh trace stop

# Convertire in formato leggibile (Wireshark può aprire .etl con plugin)
# Oppure usare Network Monitor / Message Analyzer

# === LIVELLO 5: Firewall ===
# Regole firewall attive
Get-NetFirewallRule -Enabled True -Direction Inbound |
    Select-Object Name, DisplayName, Action, Profile |
    Sort-Object DisplayName | Format-Table -AutoSize

# Verificare se il firewall blocca qualcosa
Get-NetFirewallRule -Action Block -Enabled True

# Log del firewall (se abilitato)
# Abilitare: Set-NetFirewallProfile -Profile Domain -LogAllowed True -LogBlocked True
Get-Content "$env:SystemRoot\System32\LogFiles\Firewall\pfirewall.log" -Tail 50

# === LIVELLO 6: NIC Teaming e Configurazione Avanzata ===
Get-NetAdapter | Select-Object Name, Status, LinkSpeed, MediaType
Get-NetIPConfiguration | Select-Object InterfaceAlias, IPv4Address, IPv4DefaultGateway
Get-NetAdapterBinding | Where-Object { $_.Enabled -eq $true } |
    Select-Object Name, ComponentID, DisplayName
```

---

## Troubleshooting Avanzato — Disco e File System

### Diagnosi Problemi Disco

```powershell
# === SMART Status (salute disco) ===
Get-PhysicalDisk | Select-Object FriendlyName, MediaType, OperationalStatus,
    HealthStatus, Size, @{N='SizeGB';E={[math]::Round($_.Size/1GB)}}

# Dettagli SMART (richiede admin)
Get-PhysicalDisk | Get-StorageReliabilityCounter |
    Select-Object DeviceId, Temperature, Wear, ReadErrorsTotal,
    WriteErrorsTotal, PowerOnHours

# === CHKDSK ===
# Verifica solo lettura (non corregge)
chkdsk C: /scan

# Correzione online (Windows 8+, non richiede reboot per NTFS)
chkdsk C: /spotfix

# Correzione classica (richiede reboot per volume di sistema)
# chkdsk C: /f /r   ← ATTENZIONE: richiede tempo, pianificare manutenzione

# Verificare se chkdsk è schedulato al prossimo reboot
fsutil dirty query C:

# === ReFS Health ===
Get-PhysicalDisk | Where-Object { $_.OperationalStatus -ne "OK" }
Get-VirtualDisk | Select-Object FriendlyName, OperationalStatus, HealthStatus

# === Spazio occupato — analisi rapida ===
# Top 20 cartelle più grandi sotto C:\
$root = "C:\"
Get-ChildItem $root -Directory -ErrorAction SilentlyContinue |
    ForEach-Object {
        $size = (Get-ChildItem $_.FullName -Recurse -File -Force -ErrorAction SilentlyContinue |
            Measure-Object -Property Length -Sum).Sum
        [PSCustomObject]@{
            Path = $_.FullName
            SizeGB = [math]::Round($size / 1GB, 2)
        }
    } | Sort-Object SizeGB -Descending | Select-Object -First 20 | Format-Table -AutoSize

# File più grandi sul volume
Get-ChildItem C:\ -Recurse -File -Force -ErrorAction SilentlyContinue |
    Sort-Object Length -Descending | Select-Object -First 20 `
    FullName, @{N='SizeMB';E={[math]::Round($_.Length/1MB,1)}}, LastWriteTime

# Pulizia: Windows Component Store (WinSxS)
Dism.exe /Online /Cleanup-Image /StartComponentCleanup /ResetBase
# ATTENZIONE: dopo /ResetBase non si possono disinstallare update precedenti
```

---

## Troubleshooting Avanzato — Windows Update Failures

### Analisi CBS Log

```powershell
# Il log CBS (Component Based Servicing) è la fonte primaria per errori Windows Update
# Percorso: C:\Windows\Logs\CBS\CBS.log

# Filtrare gli errori nel CBS log (file grande, usare select-string)
Select-String -Path "$env:SystemRoot\Logs\CBS\CBS.log" `
    -Pattern "Error|HRESULT|Failed" -Context 2,2 | Select-Object -Last 30

# Errori Windows Update specifici
Get-WindowsUpdateLog   # Converte ETL in formato leggibile (Win10+)
# Output: $env:USERPROFILE\Desktop\WindowsUpdate.log

# === Codici Errore Comuni ===
# 0x80073712 — Component store corrotto
#   Fix: DISM /Online /Cleanup-Image /RestoreHealth

# 0x800F081F — Source files non trovati (DISM non riesce a scaricare)
#   Fix: specificare source: DISM /Online /Cleanup-Image /RestoreHealth /Source:WIM:D:\sources\install.wim:1

# 0x80070002 — File not found durante update
#   Fix: rinominare SoftwareDistribution e riavviare servizio
#   Stop-Service wuauserv; Rename-Item "$env:SystemRoot\SoftwareDistribution" "SoftwareDistribution.old"
#   Start-Service wuauserv

# 0x80240031 — Policy blocca gli update
#   Fix: verificare GPO Windows Update (WSUS URL, approvals)

# 0x8024402F — Errore di connessione al server WU/WSUS
#   Fix: verificare proxy, DNS, connettività al WSUS server

# === Procedura di Repair Completa ===
# Step 1: Verificare integrità immagine
DISM /Online /Cleanup-Image /CheckHealth

# Step 2: Se corrotto, ripristinare
DISM /Online /Cleanup-Image /RestoreHealth

# Step 3: Verificare file di sistema
sfc /scannow

# Step 4: Se SFC trova errori non riparabili, verificare il log
Select-String -Path "$env:SystemRoot\Logs\CBS\CBS.log" -Pattern "\[SR\].*Cannot repair"

# Step 5: Reset completo componenti WU (ultima risorsa)
Stop-Service wuauserv, cryptSvc, bits, msiserver
Rename-Item "$env:SystemRoot\SoftwareDistribution" "SoftwareDistribution.bak" -ErrorAction SilentlyContinue
Rename-Item "$env:SystemRoot\System32\catroot2" "catroot2.bak" -ErrorAction SilentlyContinue
Start-Service wuauserv, cryptSvc, bits, msiserver
```

---

## Troubleshooting Avanzato — Group Policy

### GPResult Deep Dive

```powershell
# === Report HTML completo (il più leggibile) ===
gpresult /H "$env:USERPROFILE\Desktop\GPReport.html"
# Aprire in browser: mostra TUTTE le GPO applicate, filtrate, e denied

# === Report testuale rapido ===
gpresult /R                     # sommario: GPO applicate per user e computer
gpresult /R /SCOPE:COMPUTER     # solo computer policies
gpresult /R /SCOPE:USER         # solo user policies

# === Verbose: include registry values ===
gpresult /Z > "$env:USERPROFILE\Desktop\GPResult_verbose.txt"

# === RSoP (Resultant Set of Policy) ===
# GUI: rsop.msc  — mostra graficamente il risultato delle GPO
# Limitation: RSoP non mostra GPO deny o WMI filter failures

# === GPO Precedence Debugging ===
# Le GPO si applicano in ordine LSDOU:
# Local → Site → Domain → OU (l'ultima vince in caso di conflitto)
# Eccezione: "Enforced" GPO vince sempre (scende nella gerarchia)
# Eccezione: "Block Inheritance" sulla OU blocca GPO superiori (ma non Enforced)

# Verificare se una GPO specifica si applica
gpresult /R | Select-String "NomeGPO"

# === Group Policy Update Forzato ===
gpupdate /force                  # aggiorna tutte le policy
gpupdate /force /target:computer # solo computer policy
gpupdate /force /target:user     # solo user policy

# === Diagnostica GP con Event Log ===
# Log: Applications and Services Logs → Microsoft → Windows → GroupPolicy → Operational
Get-WinEvent -LogName "Microsoft-Windows-GroupPolicy/Operational" -MaxEvents 20 |
    Select-Object TimeCreated, Id, LevelDisplayName, Message |
    Format-Table -Wrap

# Event ID chiave:
# 4016 — Inizio processing GP
# 5016 — Fine processing GP (successo)
# 5017 — Fine processing GP con errori
# 7016 — Processing di una singola estensione GP
# 7017 — Errore processing estensione GP
# 8000-8007 — Dettagli per ciascuna GP processata

# === Simulazione: cosa succederebbe SE... ===
# (richiede RSAT Group Policy Management)
# GPMC → Group Policy Modeling → simulare spostamento utente/computer in altra OU

# === Verificare GPO in conflitto ===
# Due GPO impostano la stessa setting? La LAST applied vince (ordine di link nella OU)
Get-GPInheritance -Target "OU=Workstations,DC=corp,DC=contoso,DC=com"
```

---

## Troubleshooting Avanzato — Event Log Analysis

### Pattern di Analisi Event Log

```powershell
# === Strategia: cercare pattern, non singoli eventi ===

# Login falliti ripetuti (possibile brute force)
Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    Id = 4625         # Logon failure
} -MaxEvents 100 | Group-Object {
    $_.Properties[5].Value  # TargetUserName
} | Sort-Object Count -Descending | Select-Object Count, Name

# Account lockout
Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    Id = 4740         # Account locked out
} -MaxEvents 50 | ForEach-Object {
    [PSCustomObject]@{
        Time    = $_.TimeCreated
        Account = $_.Properties[0].Value
        Source  = $_.Properties[1].Value   # computer dove è avvenuto il lockout
    }
}

# Servizi che crashano
Get-WinEvent -FilterHashtable @{
    LogName = 'System'
    Id = 7031, 7034   # Service crash/unexpected termination
} -MaxEvents 20 | Select-Object TimeCreated,
    @{N='Service';E={$_.Properties[0].Value}},
    @{N='Action';E={$_.Properties[1].Value}} |
    Format-Table -AutoSize

# Installazione software (tracking cambiamenti)
Get-WinEvent -FilterHashtable @{
    LogName = 'Application'
    Id = 11707, 11724  # Install/Uninstall success
} -MaxEvents 20 | Select-Object TimeCreated, Message

# Reboot inattesi
Get-WinEvent -FilterHashtable @{
    LogName = 'System'
    Id = 6008          # Unexpected shutdown (precedente avvio dopo crash)
} -MaxEvents 10 | Select-Object TimeCreated, Message

# Errori disco
Get-WinEvent -FilterHashtable @{
    LogName = 'System'
    ProviderName = 'Disk','ntfs','volmgr'
    Level = 2,3        # Error, Warning
} -MaxEvents 20 | Select-Object TimeCreated, Id, ProviderName, Message

# === Event Log Forwarding — Setup ===
# Collector (server centrale):
wecutil qc    # quick config: abilita il servizio Windows Event Collector

# Subscription da GPO:
# Computer Configuration → Administrative Templates → 
# Windows Components → Event Forwarding
# → Configure target Subscription Manager:
# Server=http://LogCollector.corp.contoso.com:5985/wsman/SubscriptionManager/WEC

# === Correlazione: Timeline di un Incidente ===
# Raccogliere eventi da TUTTI i log in un intervallo temporale
$start = (Get-Date).AddHours(-4)
$end = Get-Date

$allEvents = foreach ($log in @('System','Security','Application')) {
    Get-WinEvent -FilterHashtable @{
        LogName   = $log
        StartTime = $start
        EndTime   = $end
        Level     = 1,2,3  # Critical, Error, Warning
    } -ErrorAction SilentlyContinue
}

$allEvents | Sort-Object TimeCreated |
    Select-Object TimeCreated, LogName, Id, LevelDisplayName, Message |
    Export-Csv "C:\Temp\IncidentTimeline.csv" -NoTypeInformation
```

### Event ID Reference Card — Windows Server

| Event ID | Log | Significato |
|----------|-----|------------|
| 4624 | Security | Logon riuscito |
| 4625 | Security | Logon fallito |
| 4648 | Security | Logon con credenziali esplicite (runas) |
| 4720 | Security | Account utente creato |
| 4726 | Security | Account utente eliminato |
| 4732 | Security | Membro aggiunto a gruppo locale |
| 4740 | Security | Account bloccato |
| 4756 | Security | Membro aggiunto a Universal Group |
| 1074 | System | Shutdown/restart iniziato da processo |
| 6005 | System | Event Log service avviato (= system boot) |
| 6006 | System | Event Log service fermato (= clean shutdown) |
| 6008 | System | Unexpected shutdown (crash/power loss) |
| 7036 | System | Servizio avviato o fermato |
| 7031 | System | Servizio terminato inaspettatamente |
| 7034 | System | Servizio terminato senza azione di recovery |

---

## WinRE — Ambiente di Ripristino Avanzato

### Architettura e Metodi di Accesso

Windows Recovery Environment (WinRE) è un ambiente di ripristino basato su Windows PE, progettato per diagnosticare e riparare problemi che impediscono l'avvio del sistema operativo. WinRE è installato in una partizione dedicata nascosta (tipicamente 450-750 MB) separata dalla partizione del sistema operativo.

```powershell
# ============================================================
# GESTIONE WinRE — reagentc.exe
# ============================================================

# Verificare stato corrente di WinRE
reagentc /info
# Output chiave:
# Windows RE status:     Enabled / Disabled
# Windows RE location:   \\?\GLOBALROOT\device\harddisk0\partition4\Recovery\WindowsRE
# BCD Identifier:        {GUID}
# Recovery Image:        (vuoto se non configurata un'immagine custom)

# Disabilitare WinRE (prima di modificare la partizione di recovery)
reagentc /disable

# Riabilitare WinRE
reagentc /enable

# Impostare percorso personalizzato per l'immagine WinRE
reagentc /setreimage /path C:\Recovery\WindowsRE /target C:\Windows

# Verificare integrità dell'immagine WinRE
Dism /Get-ImageInfo /ImageFile:C:\Recovery\WindowsRE\Winre.wim

# ============================================================
# METODI DI ACCESSO A WinRE
# ============================================================

# METODO 1: Da Windows funzionante
# Impostazioni → Sistema → Ripristino → Riavvio avanzato → Riavvia ora
# Oppure: shutdown /r /o /t 0

# METODO 2: Boot fallito
# Windows entra automaticamente in WinRE dopo 2 avvii consecutivi falliti
# (Automatic Failover) — il sistema rileva che il boot precedente non è
# arrivato fino al desktop e propone WinRE

# METODO 3: Supporto di installazione USB/DVD
# Boot da USB → "Ripristina il computer" (angolo in basso a sinistra)

# METODO 4: Forzato via Shift+Riavvia
# Dalla schermata di login: Shift + click su "Riavvia"
# Porta direttamente al menu di opzioni avanzate
```

### Operazioni di Riparazione dal Prompt dei Comandi WinRE

```powershell
# ============================================================
# Dal menu WinRE: Risoluzione problemi → Opzioni avanzate → Prompt dei comandi
# ============================================================

# ATTENZIONE: in WinRE il sistema operativo NON è su C:
# La partizione di sistema è tipicamente su D: o E: in WinRE
# Verificare: dir C:\ e dir D:\ per trovare la cartella Windows

# === RIPARAZIONE BOOT (bootrec) ===

# Riparare il Master Boot Record (sistemi BIOS/MBR)
bootrec /fixmbr

# Riscrivere il settore di avvio della partizione di sistema
bootrec /fixboot
# Se restituisce "Access denied" su sistemi UEFI:
# bootsect /nt60 sys /mbr

# Ricostruire il BCD (Boot Configuration Data) da zero
# PRIMA: rinominare il BCD corrente come backup
ren D:\EFI\Microsoft\Boot\BCD BCD.bak
# POI: ricostruire
bootrec /rebuildbcd
# Scansiona i dischi e chiede se aggiungere le installazioni trovate → "Y"

# Ricostruire BCD manualmente (se /rebuildbcd non trova l'installazione)
bcdedit /createstore D:\EFI\Microsoft\Boot\BCD
bcdedit /store D:\EFI\Microsoft\Boot\BCD /create {bootmgr} /d "Windows Boot Manager"
bcdedit /store D:\EFI\Microsoft\Boot\BCD /create /d "Windows 11" /application osloader
# Configurare i percorsi device e osdevice per la partizione corretta

# === SFC E DISM OFFLINE (da WinRE) ===

# SFC offline: specificare il percorso della partizione Windows
sfc /scannow /offbootdir=D:\ /offwindir=D:\Windows
# /offbootdir = partizione di boot (dove c'è il bootloader)
# /offwindir = cartella Windows del sistema da riparare

# DISM offline: riparare il Component Store da WinRE
Dism /Image:D:\ /Cleanup-Image /RestoreHealth /Source:WIM:E:\sources\install.wim:1
# E: = unità USB/DVD con l'ISO di installazione montata
# Se non si dispone dell'ISO:
Dism /Image:D:\ /Cleanup-Image /RestoreHealth
# Tenta il download da Windows Update (richiede rete in WinRE — non sempre disponibile)

# === CHKDSK OFFLINE ===
chkdsk D: /f /r
# /f = corregge errori, /r = cerca settori danneggiati e recupera dati leggibili
# Più efficace da WinRE perché il volume non è montato dal sistema operativo

# === REGISTRO OFFLINE — Modifica Manuale ===

# Caricare un hive del registro offline per modificare configurazioni
# senza avviare Windows (utile per: disabilitare driver problematici,
# resettare password, correggere impostazioni che impediscono il boot)

reg load HKLM\OFFLINE_SYSTEM D:\Windows\System32\config\SYSTEM
# Ora le chiavi sono accessibili sotto HKLM\OFFLINE_SYSTEM

# Esempio: disabilitare un driver che causa BSOD
# Trovare il servizio del driver:
reg query "HKLM\OFFLINE_SYSTEM\ControlSet001\Services\problematic_driver"
# Impostare Start = 4 (Disabled)
reg add "HKLM\OFFLINE_SYSTEM\ControlSet001\Services\problematic_driver" /v Start /t REG_DWORD /d 4 /f

# Esempio: resettare la password dell'admin locale
# (richiede tool esterno come chntpw, non incluso in WinRE standard)

# Scaricare hive dopo le modifiche
reg unload HKLM\OFFLINE_SYSTEM

# === BITLOCKER RECOVERY IN WinRE ===

# Se il disco è protetto da BitLocker, sbloccarlo PRIMA di qualsiasi operazione
manage-bde -unlock D: -RecoveryPassword 123456-789012-345678-901234-567890-123456-789012-345678
# La recovery key è quella salvata in AD, Entra ID o su file

# Verificare stato BitLocker da WinRE
manage-bde -status D:
# Lock Stato: Bloccato / Sbloccato
# Metodo di protezione: TPM, PIN, RecoveryPassword

# === RIPRISTINO CONFIGURAZIONE DI SISTEMA (System Restore) ===
# Da WinRE GUI: Risoluzione problemi → Opzioni avanzate → Ripristino configurazione di sistema
# Da CLI: rstrui.exe (se l'ambiente WinRE lo supporta)
# Ripristina il registro, i driver e i file di sistema a un punto precedente
# NON tocca i file utente (documenti, foto, etc.)
```

### Personalizzazione Immagine WinRE

```powershell
# Aggiungere driver o tool personalizzati all'immagine WinRE
# (utile per: driver storage/NIC mancanti, tool diagnostici custom)

# 1. Disabilitare WinRE e copiare l'immagine
reagentc /disable
Copy-Item "C:\Windows\System32\Recovery\Winre.wim" "C:\Temp\Winre.wim"

# 2. Montare l'immagine
$mountDir = "C:\Temp\WinRE-Mount"
New-Item $mountDir -ItemType Directory -Force
Dism /Mount-Image /ImageFile:C:\Temp\Winre.wim /Index:1 /MountDir:$mountDir

# 3. Aggiungere driver (es. controller storage per accedere al disco)
Dism /Image:$mountDir /Add-Driver /Driver:C:\Drivers\StorageController /Recurse

# 4. Aggiungere tool diagnostici (opzionale)
Copy-Item "C:\Tools\Autoruns64.exe" "$mountDir\Windows\System32\"

# 5. Commit e smontaggio
Dism /Unmount-Image /MountDir:$mountDir /Commit

# 6. Sostituire l'immagine originale e riabilitare WinRE
Copy-Item "C:\Temp\Winre.wim" "C:\Windows\System32\Recovery\Winre.wim" -Force
reagentc /enable
reagentc /info  # verificare che sia abilitato
```

---

## Event Log — Analisi Forense Avanzata

### Rilevamento Movimento Laterale

Il movimento laterale è la fase in cui un attaccante si sposta dalla macchina inizialmente compromessa verso altri sistemi nella rete. La correlazione tra event log di macchine diverse è fondamentale per ricostruire questa attività.

```powershell
# ============================================================
# RILEVAMENTO LATERAL MOVEMENT — PATTERN DI CORRELAZIONE
# ============================================================

# --- Pattern 1: Logon esplicito con credenziali rubate ---
# Event 4648 sulla macchina sorgente (credenziali esplicite usate)
# + Event 4624 Type 3 sulla macchina target (logon di rete)
# Se lo stesso utente ha 4648 da una macchina e 4624 Type 3 su un'altra
# nello stesso intervallo temporale → possibile lateral movement

Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    Id = 4648
} -MaxEvents 50 | ForEach-Object {
    [PSCustomObject]@{
        Time       = $_.TimeCreated
        Account    = $_.Properties[1].Value   # SubjectUserName
        TargetUser = $_.Properties[5].Value   # TargetUserName
        TargetHost = $_.Properties[8].Value   # TargetServerName
        Process    = $_.Properties[11].Value  # ProcessName
    }
} | Where-Object { $_.Process -notmatch "lsass|svchost" } |
    Format-Table -AutoSize

# --- Pattern 2: Logon Type anomali ---
# Type 3 (Network) da IP interni insoliti → possibile pass-the-hash/ticket
# Type 10 (RemoteInteractive/RDP) da host non amministrativi → sospetto
# Type 7 (Unlock) in orari non lavorativi → possibile accesso fisico non autorizzato

Get-WinEvent -FilterHashtable @{
    LogName = 'Security'; Id = 4624
} -MaxEvents 200 | ForEach-Object {
    [PSCustomObject]@{
        Time      = $_.TimeCreated
        Account   = $_.Properties[5].Value   # TargetUserName
        LogonType = $_.Properties[8].Value   # LogonType
        SourceIP  = $_.Properties[18].Value  # IpAddress
        Workstation = $_.Properties[11].Value # WorkstationName
    }
} | Where-Object { $_.LogonType -in @(3, 10) -and $_.Account -ne "ANONYMOUS LOGON" } |
    Group-Object SourceIP | Sort-Object Count -Descending |
    Select-Object Count, Name, @{N='Accounts';E={($_.Group.Account | Select-Object -Unique) -join ", "}}

# --- Pattern 3: Kerberoasting Detection ---
# Event 4769 (Kerberos Service Ticket Request) con encryption type 0x17 (RC4)
# L'uso di RC4 per richieste di service ticket è anomalo nei domini moderni
# e indica possibile Kerberoasting (estrazione hash per crack offline)

Get-WinEvent -FilterHashtable @{
    LogName = 'Security'; Id = 4769
} -MaxEvents 500 | ForEach-Object {
    $encType = $_.Properties[5].Value  # TicketEncryptionType
    if ($encType -eq "0x17") {
        [PSCustomObject]@{
            Time       = $_.TimeCreated
            Account    = $_.Properties[0].Value  # TargetUserName
            Service    = $_.Properties[2].Value  # ServiceName
            EncType    = $encType
            ClientAddr = $_.Properties[6].Value  # IpAddress
        }
    }
} | Format-Table -AutoSize
# Se ci sono molte richieste 0x17 in breve tempo dallo stesso IP → Kerberoasting

# ============================================================
# RILEVAMENTO MANOMISSIONE LOG
# ============================================================

# Event 1102 — Security Log cancellato
# Questo evento è registrato SEMPRE, anche quando il log viene svuotato
# Se presente → investigare immediatamente chi ha cancellato il log
Get-WinEvent -FilterHashtable @{
    LogName = 'Security'; Id = 1102
} -MaxEvents 10 | ForEach-Object {
    [PSCustomObject]@{
        Time    = $_.TimeCreated
        Account = $_.Properties[1].Value  # chi ha cancellato il log
        Domain  = $_.Properties[2].Value
    }
}

# Event 104 — Qualsiasi Event Log cancellato (System log)
Get-WinEvent -FilterHashtable @{
    LogName = 'System'; Id = 104
} -MaxEvents 10 | Select-Object TimeCreated, Message

# Verificare dimensione e retention del Security log
wevtutil gl Security
# maxSize = dimensione massima in byte
# retention = true/false (se false, gli eventi più vecchi vengono sovrascritti)
# Raccomandazione: almeno 1 GB per il Security log in produzione
wevtutil sl Security /ms:1073741824   # 1 GB

# ============================================================
# RILEVAMENTO PERSISTENZA
# ============================================================

# --- Scheduled Task creata (Event 4698) ---
# Malware e attaccanti creano task pianificate per persistenza
Get-WinEvent -FilterHashtable @{
    LogName = 'Security'; Id = 4698
} -MaxEvents 20 | ForEach-Object {
    [PSCustomObject]@{
        Time     = $_.TimeCreated
        Creator  = $_.Properties[1].Value   # SubjectUserName
        TaskName = $_.Properties[4].Value   # TaskName
        TaskXML  = $_.Properties[5].Value   # TaskContent (XML del task)
    }
} | Format-List
# Sospetti: task creati da account non-admin, task con azioni verso %TEMP%, %APPDATA%,
# o che eseguono powershell.exe con argomenti encoded (-enc, -EncodedCommand)

# --- Nuovo servizio installato (Event 7045) ---
# I servizi Windows sono un meccanismo di persistenza classico
Get-WinEvent -FilterHashtable @{
    LogName = 'System'; Id = 7045
} -MaxEvents 20 | ForEach-Object {
    [PSCustomObject]@{
        Time        = $_.TimeCreated
        ServiceName = $_.Properties[0].Value
        ImagePath   = $_.Properties[1].Value  # percorso dell'eseguibile
        ServiceType = $_.Properties[2].Value
        StartType   = $_.Properties[3].Value
        AccountName = $_.Properties[4].Value
    }
} | Format-Table -AutoSize
# Sospetti: servizi con ImagePath in temp/appdata, nome generico,
# account LocalSystem (massimi privilegi), avviati da utente non admin

# ============================================================
# EVENTI POWERSHELL SOSPETTI
# ============================================================

# Event 4104 (Script Block Logging) — cattura il contenuto degli script eseguiti
# Richiede: GPO → PowerShell → Turn on Script Block Logging: Enabled
Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-PowerShell/Operational'; Id = 4104
} -MaxEvents 100 | Where-Object {
    $_.Message -match "EncodedCommand|Invoke-Expression|iex|Net\.WebClient|DownloadString|DownloadFile|Invoke-Mimikatz|Invoke-Shellcode|-enc "
} | Select-Object TimeCreated, @{N='ScriptBlock';E={$_.Properties[2].Value}} |
    Format-List
# Pattern sospetti:
# - Base64 encoded commands (-enc, [Convert]::FromBase64String)
# - Download da URL (Net.WebClient, Invoke-WebRequest verso IP esterni)
# - Tool offensivi noti (Mimikatz, PowerSploit, Empire)
# - AMSI bypass attempts (AmsiInitFailed, AmsiUtils)

# ============================================================
# WINDOWS 11 24H2 / SERVER 2025 — NUOVE DIAGNOSTICHE GPP
# ============================================================

# A partire dall'aggiornamento gennaio 2026, Group Policy Preferences
# (GPP) registra un nuovo Event ID 4117 con informazioni diagnostiche
# dettagliate. In precedenza, l'unico evento disponibile era il 4098
# che riportava solo un codice di errore senza indicare il percorso
# o l'oggetto che aveva causato il fallimento.

# Il nuovo Event 4117 include:
# - Il percorso completo del file/oggetto non trovato
# - Il contesto della GPP preference item che ha generato l'errore
# - Informazioni sufficienti per il troubleshooting diretto

Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-GroupPolicy/Operational'
    Id = 4117
} -MaxEvents 20 -ErrorAction SilentlyContinue |
    Select-Object TimeCreated, Message | Format-List
# Se non presente → il sistema non ha ancora l'aggiornamento gennaio 2026+
```

### Correlazione Multi-Log con Sysmon

```powershell
# ============================================================
# SYSMON + EVENT LOG — CORRELAZIONE AVANZATA
# ============================================================

# Sysmon (System Monitor) è il complemento essenziale agli Event Log nativi
# Fornisce: hash dei processi, connessioni di rete per processo,
# creazione file con timestamp preciso, modifiche registro granulari

# Prerequisito: Sysmon installato con configurazione SwiftOnSecurity o equivalent
# sysmon64.exe -accepteula -i sysmonconfig-export.xml

# === Correlazione: Process Creation + Network Connection ===
# Sysmon Event 1 (Process Create) → chi ha lanciato il processo
# Sysmon Event 3 (Network Connection) → dove si è connesso

# Cercare processi che si connettono a IP esterni sospetti
Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-Sysmon/Operational'; Id = 3
} -MaxEvents 200 | Where-Object {
    $destIP = $_.Properties[14].Value  # DestinationIp
    # Escludere IP privati e loopback
    $destIP -notmatch "^(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|127\.|::1)"
} | ForEach-Object {
    [PSCustomObject]@{
        Time        = $_.TimeCreated
        Process     = $_.Properties[4].Value   # Image
        User        = $_.Properties[12].Value  # User
        DestIP      = $_.Properties[14].Value  # DestinationIp
        DestPort    = $_.Properties[16].Value  # DestinationPort
        DestHost    = $_.Properties[15].Value  # DestinationHostname
    }
} | Sort-Object DestIP | Format-Table -AutoSize

# === File Creation in cartelle sospette (Sysmon Event 11) ===
Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-Sysmon/Operational'; Id = 11
} -MaxEvents 200 | Where-Object {
    $target = $_.Properties[5].Value  # TargetFilename
    $target -match "\\Temp\\|\\AppData\\Local\\Temp\\|\\ProgramData\\" -and
    $target -match "\.(exe|dll|ps1|bat|cmd|vbs|js|hta|scr)$"
} | ForEach-Object {
    [PSCustomObject]@{
        Time     = $_.TimeCreated
        Process  = $_.Properties[4].Value  # Image (chi ha creato il file)
        Target   = $_.Properties[5].Value  # TargetFilename
        Hash     = $_.Properties[6].Value  # Hashes
    }
} | Format-Table -AutoSize
# File eseguibili creati in cartelle temp → possibile dropper

# === Timeline completa di un incidente (multi-source) ===
# Combinare Security + System + Sysmon in una timeline unificata
$startTime = (Get-Date "2026-05-24 08:00")
$endTime   = (Get-Date "2026-05-24 12:00")

$timeline = @()
foreach ($log in @('Security','System','Microsoft-Windows-Sysmon/Operational')) {
    $events = Get-WinEvent -FilterHashtable @{
        LogName   = $log
        StartTime = $startTime
        EndTime   = $endTime
        Level     = 1,2,3,4  # Critical, Error, Warning, Information
    } -MaxEvents 500 -ErrorAction SilentlyContinue

    foreach ($ev in $events) {
        $timeline += [PSCustomObject]@{
            Time     = $ev.TimeCreated
            Source   = $log.Split('/')[-1]  # nome log abbreviato
            EventID  = $ev.Id
            Level    = $ev.LevelDisplayName
            Message  = ($ev.Message -split "`n")[0]  # prima riga del messaggio
        }
    }
}

$timeline | Sort-Object Time |
    Export-Csv "C:\Forensic\timeline-$(Get-Date -Format 'yyyyMMdd').csv" -NoTypeInformation
# La timeline CSV è importabile in Excel, Splunk o qualsiasi SIEM
# Ordinata cronologicamente permette di ricostruire la sequenza dell'attacco
```

### Event ID Forensi — Reference Card Estesa

| Event ID | Log | Rilevanza Forense |
|----------|-----|-------------------|
| 1102 | Security | Log Security cancellato — possibile anti-forensics |
| 4624 Type 3 | Security | Logon di rete — correlazione per lateral movement |
| 4648 | Security | Logon con credenziali esplicite — possibile pass-the-hash |
| 4672 | Security | Privilegi speciali assegnati — escalation detection |
| 4698 | Security | Scheduled task creata — persistenza |
| 4769 (0x17) | Security | Kerberos ticket con RC4 — possibile Kerberoasting |
| 7045 | System | Nuovo servizio installato — persistenza |
| 4104 | PowerShell/Operational | Script block eseguito — detection encoded commands |
| 4117 | GroupPolicy/Operational | GPP diagnostic dettagliata (Win11 24H2+) |
| Sysmon 1 | Sysmon/Operational | Processo creato con hash e parent process |
| Sysmon 3 | Sysmon/Operational | Connessione di rete con processo sorgente |
| Sysmon 11 | Sysmon/Operational | File creato — dropper detection |
| Sysmon 13 | Sysmon/Operational | Valore registro modificato — persistenza |

---

## Glossario

| Termine | Definizione |
|---------|------------|
| **ADMT** | Active Directory Migration Tool — strumento per migrazione oggetti AD tra domini/foreste |
| **ASR** | Attack Surface Reduction — regole Defender per ridurre la superficie d'attacco |
| **Autopilot** | Servizio cloud Microsoft per provisioning zero-touch di dispositivi Windows |
| **BSOD** | Blue Screen of Death — schermata errore fatale kernel Windows |
| **CBS** | Component Based Servicing — engine che gestisce installazione e aggiornamento componenti Windows |
| **CIS Benchmark** | Center for Internet Security — standard di hardening con checklist dettagliate per OS e applicazioni |
| **Crash Dump** | File che contiene lo stato della memoria al momento di un crash kernel |
| **DISM** | Deployment Image Servicing and Management — tool per servicing immagini Windows offline/online |
| **DPC** | Deferred Procedure Call — funzione kernel eseguita a IRQL elevato, usata dai driver |
| **FSMO** | Flexible Single Master Operations — ruoli AD che richiedono un singolo DC master |
| **GPO** | Group Policy Object — oggetto che contiene impostazioni di policy per utenti e computer |
| **IRQL** | Interrupt Request Level — livello di priorità di interrupt nel kernel Windows |
| **LAPS** | Local Administrator Password Solution — gestione automatica password admin locali |
| **MDT** | Microsoft Deployment Toolkit — framework per deployment automatizzato OS/applicazioni |
| **NLA** | Network Level Authentication — autenticazione pre-sessione RDP |
| **PAW** | Privileged Access Workstation — workstation dedicata per amministrazione sicura |
| **RSoP** | Resultant Set of Policy — vista aggregata delle GPO risultanti per utente/computer |
| **STIG** | Security Technical Implementation Guide — standard di hardening DoD/DISA |
| **WDS** | Windows Deployment Services — ruolo server per deployment via PXE/rete |
| **WEF** | Windows Event Forwarding — raccolta centralizzata event log senza agent terzi |
| **WinDbg** | Windows Debugger — debugger Microsoft per analisi crash dump e kernel debugging |
| **WinRE** | Windows Recovery Environment — ambiente di ripristino basato su Windows PE per riparazione sistemi non avviabili |
| **WPA** | Windows Performance Analyzer — tool grafico per analisi tracce ETW generate da WPR |
| **WPR** | Windows Performance Recorder — tool per registrazione tracce ETW ad alta risoluzione per profiling OS |
| **ETW** | Event Tracing for Windows — infrastruttura kernel per logging eventi ad alte prestazioni e basso overhead |
| **ETL** | Event Trace Log — formato file binario contenente eventi ETW catturati da WPR o altri provider |
| **ASEP** | Auto-Start Extensibility Point — qualsiasi meccanismo di Windows che consente a programmi di avviarsi automaticamente |
| **ProcMon** | Process Monitor — tool Sysinternals per monitoraggio real-time di file system, registro e attività di rete per processo |

## Riferimenti

- Microsoft Docs — [Windows Debugging (WinDbg)](https://learn.microsoft.com/windows-hardware/drivers/debugger/)
- Microsoft Docs — [Performance Monitor Counters](https://learn.microsoft.com/windows-server/administration/performance-tuning/)
- Microsoft Docs — [Group Policy troubleshooting](https://learn.microsoft.com/troubleshoot/windows-server/group-policy/)
- Microsoft Docs — [Windows Update troubleshooting](https://learn.microsoft.com/troubleshoot/windows-client/installing-updates-features-roles/)
- Microsoft Docs — [DISM Command-Line Options](https://learn.microsoft.com/windows-hardware/manufacture/desktop/dism-command-line-options)
- CIS Benchmarks — [Microsoft Windows Server](https://www.cisecurity.org/benchmark/microsoft_windows_server)
- DISA STIGs — [Windows Server and Client](https://public.cyber.mil/stigs/)
- Microsoft Docs — [MDT documentation](https://learn.microsoft.com/mem/configmgr/mdt/)
- Microsoft Docs — [Windows Autopilot](https://learn.microsoft.com/autopilot/)
- Microsoft Docs — [Windows Performance Recorder](https://learn.microsoft.com/windows-hardware/test/wpt/windows-performance-recorder)
- Microsoft Docs — [Windows Performance Analyzer](https://learn.microsoft.com/windows-hardware/test/wpt/windows-performance-analyzer)
- Microsoft Docs — [Sysinternals Suite](https://learn.microsoft.com/sysinternals/)
- Microsoft Docs — [Windows Recovery Environment](https://learn.microsoft.com/windows-hardware/manufacture/desktop/windows-recovery-environment--windows-re--technical-reference)
- Microsoft Docs — [netsh trace commands](https://learn.microsoft.com/windows-server/administration/windows-commands/netsh-trace)
- Microsoft TechCommunity — [GPP Diagnostics in Windows Server 2025 and Windows 11 24H2](https://techcommunity.microsoft.com/blog/askds/from-guesswork-to-clarity-gpp-diagnostics-improve-in-windows-server-2025-and-win/4499474)

---

## Esercizi

1. **Lab — Deployment dominio greenfield.** Installare Windows Server, promuovere a DC, configurare DNS/DHCP, creare una struttura OU e joinare un client. Documentare ogni fase con screenshot e comandi PowerShell usati.

2. **Lab — Hardening CIS Benchmark.** Scaricare il CIS Benchmark per Windows Server 2022. Applicare le prime 20 raccomandazioni L1 via GPO. Eseguire un audit con `Invoke-CISBenchmark` o tool equivalente e confrontare il punteggio prima/dopo.

3. **Lab — Disaster Recovery test.** Simulare la perdita del PDC emulator: seize il ruolo FSMO su un DC secondario, verificare la replica, ripristinare il DC originale da System State backup, e documentare RTO/RPO effettivi.

4. **Lab — Automazione manutenzione.** Creare uno script PowerShell che: pulisce file temporanei, verifica lo spazio disco, controlla i log eventi critici delle ultime 24 ore, ed esporta un report HTML. Schedularlo con un Scheduled Task e verificare l'esecuzione automatica.

---

## Auto-valutazione

<details>
<summary>1. Qual è la differenza tra in-place upgrade e swing migration, e quando scegliere l'uno o l'altro?</summary>

L'in-place upgrade aggiorna il sistema operativo sul posto mantenendo applicazioni e configurazioni — è più rapido ma rischia incompatibilità. La swing migration prevede un nuovo server parallelo con migrazione graduale dei ruoli — è più sicura, consente rollback immediato e viene preferita per server critici di produzione.
</details>

<details>
<summary>2. Quali sono i 5 ruoli FSMO di Active Directory e cosa accade se il PDC Emulator diventa indisponibile?</summary>

I 5 ruoli FSMO sono: Schema Master, Domain Naming Master (forest-level), PDC Emulator, RID Master, Infrastructure Master (domain-level). Se il PDC Emulator va offline, si perdono la sincronizzazione orario, la gestione prioritaria dei cambio password e la compatibilità con client pre-Windows 2000. Si può eseguire il seize del ruolo su un altro DC.
</details>

<details>
<summary>3. Cosa prevede il livello L1 del CIS Benchmark rispetto al livello L2?</summary>

L1 contiene raccomandazioni di base applicabili a qualsiasi organizzazione con impatto minimo sulla funzionalità. L2 aggiunge controlli più restrittivi destinati ad ambienti ad alta sicurezza, che possono impattare usabilità o compatibilità applicativa. In genere si parte da L1 e si aggiungono progressivamente controlli L2 dove il rischio lo giustifica.
</details>

<details>
<summary>4. Perché un piano di disaster recovery non testato equivale a un piano inesistente?</summary>

Senza test periodici non si possono verificare: la reale recuperabilità dei backup, i tempi effettivi di RTO/RPO, la correttezza delle procedure documentate, le dipendenze non considerate. Un test trimestrale rivela gap nelle procedure, backup corrotti, e tempi di ripristino irrealistici prima che si verifichi un disastro reale.
</details>

<details>
<summary>5. Qual è il ruolo di DISM nell'offline servicing delle immagini Windows?</summary>

DISM (Deployment Image Servicing and Management) permette di montare un'immagine WIM/VHDX, applicare aggiornamenti, driver, feature pack e language pack senza avviare il sistema operativo. Questo consente di mantenere immagini di deployment aggiornate e pre-configurate, riducendo i tempi di post-deployment.
</details>

<details>
<summary>6. In che modo ASR (Attack Surface Reduction) rules complementano l'hardening tradizionale?</summary>

Le ASR rules di Microsoft Defender bloccano comportamenti specifici sfruttati dal malware: esecuzione di script offuscati, creazione di processi child da applicazioni Office, credenziali stealing da LSASS. Complementano l'hardening tradizionale (disabilitare servizi, chiudere porte) aggiungendo protezione runtime basata su pattern comportamentali.
</details>

---

## Letture primarie consigliate

- CIS Benchmarks — Microsoft Windows Server 2022 — https://www.cisecurity.org/benchmark/microsoft_windows_server
- Microsoft Docs — Windows Autopilot Overview — https://learn.microsoft.com/autopilot/
- Microsoft Docs — DISM Image Management — https://learn.microsoft.com/windows-hardware/manufacture/desktop/dism-image-management-command-line-options-s14
- DISA STIGs — Windows Server and Client — https://public.cyber.mil/stigs/
- Microsoft Docs — Active Directory Disaster Recovery — https://learn.microsoft.com/windows-server/identity/ad-ds/manage/ad-forest-recovery-guide

---

## Collegamenti incrociati

- [01-active-directory.md](01-active-directory.md) — Fondamenti AD: domini, foreste, OU, replica, FSMO
- [05-sicurezza-windows.md](05-sicurezza-windows.md) — Sicurezza OS, Defender, firewall, auditing
- [15-backup-ripristino.md](15-backup-ripristino.md) — Strategie backup, Windows Server Backup, bare-metal recovery
- [26-intune-gestione-moderna.md](26-intune-gestione-moderna.md) — Gestione moderna endpoint con Intune e Autopilot
- [29-windows-server-hardening.md](29-windows-server-hardening.md) — Hardening avanzato server: JEA, WDAC, credential guard
