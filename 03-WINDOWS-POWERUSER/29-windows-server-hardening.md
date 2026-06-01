# Windows Server Hardening — Guida Approfondita

> **Modulo 29** · **Aggiornamento:** 2026-05-23

| | |
|---|---|
| **Obiettivi di apprendimento** | 1. Applicare i CIS Benchmark (Level 1 e Level 2) e i DISA STIG a Windows Server 2022/2025 con documentazione delle eccezioni · 2. Implementare una strategia completa di protezione delle credenziali: Credential Guard, LAPS, gMSA, Protected Users, restrizione NTLM e Kerberos armoring · 3. Configurare WDAC e AppLocker per il controllo delle applicazioni con policy in modalità audit e poi enforcement · 4. Progettare una configurazione di audit avanzata con Sysmon, WEF/WEC e integrazione SIEM per la detection delle minacce · 5. Eseguire l'hardening di rete end-to-end: firewall avanzato, IPsec, SMB signing/encryption, disabilitazione protocolli legacy, TLS 1.3 · 6. Automatizzare la verifica di conformità con DSC e script di compliance, generando report periodici |
| **Prerequisiti** | [01 — Active Directory](01-active-directory.md) · [02 — PowerShell](02-powershell.md) · [05 — Sicurezza Windows](05-sicurezza-windows.md) · [06 — Rete Windows](06-rete-windows.md) · [08 — Permessi e Accesso](08-permessi-e-accesso.md) · [10 — Gestione Aggiornamenti](10-gestione-aggiornamenti.md) · [11 — Servizi Certificati](11-servizi-certificati.md) |
| **Tempo stimato** | 16 – 20 ore (studio + laboratorio) |
| **Livello** | Proficient |

## Idee guida
1. **CIS Benchmark Windows Server.**
2. **Disable SMBv1; enforce SMBv3 + signing + encryption.**
3. **Block legacy auth (NTLM v1; LM hashes).**
4. **AppLocker / WDAC application control.**
5. **Defense in depth: nessun singolo controllo è sufficiente — stratificare firewall + credential protection + audit + application control + patching.**
6. **Credential Guard + LSA Protection = linea di difesa primaria contro credential theft.**
7. **Audit everything, alert on the right things: volume senza qualità è rumore.**
8. **Ogni eccezione alla baseline deve essere documentata, approvata e riesaminata periodicamente.**
9. **Server Core è la configurazione predefinita; Desktop Experience è l'eccezione che richiede giustificazione.**
10. **L'hardening non è un evento — è un processo continuo di verifica, drift detection e remediation.**


## Indice

- [Panoramica](#panoramica)
- [CIS Benchmarks e Security Baselines](#cis-benchmarks-e-security-baselines)
  - [Microsoft Security Compliance Toolkit (SCT)](#microsoft-security-compliance-toolkit-sct)
  - [CIS Benchmarks](#cis-benchmarks)
- [CIS Benchmark — Approfondimento Level 1 e Level 2](#cis-benchmark--approfondimento-level-1-e-level-2)
  - [Level 1 — Controlli Fondamentali](#level-1--controlli-fondamentali)
  - [Level 2 — Controlli Avanzati](#level-2--controlli-avanzati)
  - [Documentazione delle Eccezioni](#documentazione-delle-eccezioni)
- [DISA STIG per Windows Server](#disa-stig-per-windows-server)
  - [Panoramica STIG](#panoramica-stig)
  - [SCAP Scanning](#scap-scanning)
  - [Remediation Workflow](#remediation-workflow)
- [Disabilitazione Servizi Non Necessari](#disabilitazione-servizi-non-necessari)
- [Service Hardening Avanzato](#service-hardening-avanzato)
  - [Sicurezza degli Account di Servizio](#sicurezza-degli-account-di-servizio)
  - [Per-Service SID Isolation](#per-service-sid-isolation)
  - [Servizi e Permessi del File System](#servizi-e-permessi-del-file-system)
- [Rimozione SMBv1 e Protocolli Legacy](#rimozione-smbv1-e-protocolli-legacy)
- [Disabilitazione LLMNR e NBT-NS](#disabilitazione-llmnr-e-nbt-ns)
- [Sicurezza di Rete Avanzata](#sicurezza-di-rete-avanzata)
  - [IPsec Policies](#ipsec-policies)
  - [SMB Signing e Encryption](#smb-signing-e-encryption)
  - [Disabilitazione Protocolli Legacy di Rete](#disabilitazione-protocolli-legacy-di-rete)
- [Credential Protection](#credential-protection)
- [Account Security Avanzata](#account-security-avanzata)
  - [Protected Users Group](#protected-users-group)
  - [Fine-Grained Password Policies (PSO)](#fine-grained-password-policies-pso)
  - [AdminSDHolder e SDProp](#adminsdholder-e-sdprop)
  - [Privileged Access Tiers (Tier Model)](#privileged-access-tiers-tier-model)
  - [Group Managed Service Accounts (gMSA)](#group-managed-service-accounts-gmsa)
- [Credential Guard e Prevenzione del Furto di Credenziali Remote](#credential-guard-e-prevenzione-del-furto-di-credenziali-remote)
  - [Remote Credential Guard](#remote-credential-guard)
  - [Restrizioni NTLM](#restrizioni-ntlm)
  - [Kerberos Armoring (FAST)](#kerberos-armoring-fast)
- [Configurazione Event Log e Audit Policy](#configurazione-event-log-e-audit-policy)
- [Audit Avanzato e Integrazione SIEM](#audit-avanzato-e-integrazione-siem)
  - [Windows Event Forwarding (WEF/WEC)](#windows-event-forwarding-wefwec)
  - [Integrazione SIEM](#integrazione-siem)
  - [Event ID Critici — Tabella Estesa](#event-id-critici--tabella-estesa)
- [Windows Firewall Advanced Rules](#windows-firewall-advanced-rules)
- [LAPS Deployment](#laps-deployment)
- [JEA — Just Enough Administration](#jea--just-enough-administration)
- [Windows Defender — Funzionalità di Protezione Avanzata](#windows-defender--funzionalità-di-protezione-avanzata)
  - [WDAC — Windows Defender Application Control](#wdac--windows-defender-application-control)
  - [AppLocker — Confronto e Coesistenza con WDAC](#applocker--confronto-e-coesistenza-con-wdac)
  - [ASR — Attack Surface Reduction Rules](#asr--attack-surface-reduction-rules)
  - [Controlled Folder Access](#controlled-folder-access)
  - [Exploit Protection](#exploit-protection)
- [AppLocker e WDAC — Application Whitelisting](#applocker-e-wdac--application-whitelisting)
- [TLS Hardening — Configurazione Schannel](#tls-hardening--configurazione-schannel)
  - [Cipher Suite Ordering](#cipher-suite-ordering)
  - [Registry Keys Critiche per TLS](#registry-keys-critiche-per-tls)
  - [Verifica della Configurazione TLS](#verifica-della-configurazione-tls)
- [Registry Hardening](#registry-hardening)
  - [Chiavi di Registro Critiche per la Sicurezza](#chiavi-di-registro-critiche-per-la-sicurezza)
  - [ACL sul Registry](#acl-sul-registry)
  - [NtfsDisable8dot3NameCreation e Altre Ottimizzazioni](#ntfsdisable8dot3namecreation-e-altre-ottimizzazioni)
- [Server Core e Nano Server](#server-core-e-nano-server)
  - [Vantaggi di Sicurezza di Server Core](#vantaggi-di-sicurezza-di-server-core)
  - [Gestione di Server Core](#gestione-di-server-core)
  - [Nano Server — Uso e Limitazioni](#nano-server--uso-e-limitazioni)
- [Patch Management Hardening](#patch-management-hardening)
  - [Sicurezza WSUS](#sicurezza-wsus)
  - [Windows Update for Business (WUfB)](#windows-update-for-business-wufb)
  - [Update Ring Strategy](#update-ring-strategy)
  - [Procedura di Rollback](#procedura-di-rollback)
- [PowerShell Security](#powershell-security)
  - [Constrained Language Mode](#constrained-language-mode)
  - [Script Block Logging e Module Logging](#script-block-logging-e-module-logging)
  - [Transcription](#transcription)
  - [JEA — Integrazione con PowerShell Security](#jea--integrazione-con-powershell-security)
- [Sicurezza Fisica e di Avvio](#sicurezza-fisica-e-di-avvio)
  - [BitLocker per Server](#bitlocker-per-server)
  - [Secure Boot e UEFI](#secure-boot-e-uefi)
  - [Measured Boot e Device Guard](#measured-boot-e-device-guard)
- [Compliance Scanning e Automazione](#compliance-scanning-e-automazione)
  - [Security Compliance Toolkit (SCT)](#security-compliance-toolkit-sct)
  - [DSC per Compliance Continua](#dsc-per-compliance-continua)
  - [Azure Policy e Microsoft Defender for Cloud](#azure-policy-e-microsoft-defender-for-cloud)
- [Desired State Configuration (DSC) per Hardening Automatizzato](#desired-state-configuration-dsc-per-hardening-automatizzato)
- [Sysmon — Monitoraggio Avanzato dei Processi](#sysmon--monitoraggio-avanzato-dei-processi)
- [Hardening Checklist Completa](#hardening-checklist-completa)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Esercizi](#esercizi)
- [Autovalutazione](#autovalutazione)
- [Letture](#letture)
- [Cross-link ai Moduli Correlati](#cross-link-ai-moduli-correlati)
- [Glossario](#glossario)
- [Riferimenti](#riferimenti)

---

## Panoramica

L'hardening di un sistema Windows Server è il processo sistematico di riduzione della superficie di attacco attraverso la disabilitazione di funzionalità non necessarie, la configurazione di controlli di sicurezza avanzati e l'implementazione del principio del minimo privilegio. Un server Windows nella configurazione predefinita espone numerosi servizi, protocolli e funzionalità che, se non necessari per il ruolo specifico del server, rappresentano potenziali vettori di attacco.

In un panorama di minacce dove gli attacchi laterali (lateral movement) attraverso la rete interna sono la norma piuttosto che l'eccezione, l'hardening non è un'opzione ma un requisito fondamentale. Tecniche come Pass-the-Hash, Kerberoasting, LLMNR/NBT-NS poisoning e relay attacks sfruttano configurazioni di default di Windows che possono essere facilmente mitigate con le configurazioni descritte in questa guida.

Questa guida segue un approccio strutturato basato su framework riconosciuti (CIS Benchmarks, Microsoft Security Baselines, NIST SP 800-123) e copre ogni aspetto dell'hardening: dalla rimozione dei protocolli legacy alla protezione delle credenziali, dall'audit avanzato alla gestione dei privilegi amministrativi con LAPS e JEA.

```
MAPPA CONCETTUALE — WINDOWS SERVER HARDENING LAYERS
====================================================

                    ┌────────────────────────────────┐
                    │     COMPLIANCE & FRAMEWORK     │
                    │  CIS Benchmark │ DISA STIG     │
                    │  SCT Baselines │ NIST 800-123  │
                    └───────────────┬────────────────┘
                                    │
          ┌─────────────────────────┼─────────────────────────┐
          │                         │                         │
          ▼                         ▼                         ▼
┌─────────────────┐   ┌──────────────────────┐   ┌──────────────────┐
│  IDENTITY &     │   │   NETWORK SECURITY   │   │   APPLICATION    │
│  CREDENTIALS    │   │                      │   │   CONTROL        │
│                 │   │  Firewall avanzato   │   │                  │
│ Credential Guard│   │  IPsec policies      │   │  WDAC policies   │
│ LAPS / gMSA     │   │  SMB sign+encrypt    │   │  AppLocker rules │
│ Protected Users │   │  TLS 1.2/1.3 only    │   │  ASR rules       │
│ LSA Protection  │   │  No LLMNR/NBT-NS     │   │  Exploit Protect │
│ Fine-Grain PSO  │   │  No SMBv1/WPAD       │   │  Controlled FAcc │
│ Tier Model      │   │  Cipher hardening    │   │  Script control  │
└────────┬────────┘   └──────────┬───────────┘   └────────┬─────────┘
         │                       │                        │
         └───────────┬───────────┴───────────┬────────────┘
                     │                       │
                     ▼                       ▼
          ┌────────────────────┐   ┌─────────────────────┐
          │  AUDIT & DETECTION │   │   OS HARDENING      │
          │                    │   │                      │
          │ Advanced Audit Pol │   │  Server Core         │
          │ Sysmon             │   │  Service hardening   │
          │ PS Script Logging  │   │  Registry hardening  │
          │ WEF/WEC forwarding │   │  Patch management    │
          │ SIEM integration   │   │  BitLocker/SecureBoot│
          │ Event ID alerting  │   │  DSC compliance      │
          └────────────────────┘   └─────────────────────┘
                     │                       │
                     └───────────┬───────────┘
                                 │
                     ┌───────────▼───────────┐
                     │   CONTINUOUS          │
                     │   COMPLIANCE          │
                     │                       │
                     │  SCT scanning         │
                     │  DSC drift detection  │
                     │  Automated reporting  │
                     │  Exception mgmt       │
                     │  Periodic review      │
                     └───────────────────────┘
```

---

## CIS Benchmarks e Security Baselines

### Microsoft Security Compliance Toolkit (SCT)

Microsoft fornisce gratuitamente le security baselines attraverso il Security Compliance Toolkit, che include GPO preconfigurate per ogni versione di Windows e ogni ruolo server.

```powershell
# Scaricare il Security Compliance Toolkit
# https://www.microsoft.com/en-us/download/details.aspx?id=55319

# Il pacchetto contiene:
# - GPO backup per ogni baseline
# - Script di applicazione
# - Documentazione delle impostazioni
# - LGPO.exe per applicazione locale

# Applicare una baseline su un server standalone (non in dominio)
# Usando LGPO.exe (incluso nel SCT)
.\LGPO.exe /g ".\Windows Server 2022 Security Baseline\GPOs\{GUID}"

# Verificare le impostazioni applicate
.\LGPO.exe /parse /m "C:\Windows\System32\GroupPolicy\Machine\Registry.pol"
```

### CIS Benchmarks

I CIS (Center for Internet Security) Benchmarks forniscono raccomandazioni dettagliate classificate in due livelli:

- **Level 1**: Impostazioni di base che non impattano significativamente la funzionalità. Raccomandate per tutti i server.
- **Level 2**: Impostazioni più restrittive che potrebbero impattare la funzionalità. Raccomandate per server ad alta sicurezza.

```powershell
# Esempio: verificare conformità a CIS benchmark per password policy
$passwordPolicy = @{
    "Enforce password history"                      = 24
    "Maximum password age"                          = 365  # CIS: 365 o meno
    "Minimum password age"                          = 1
    "Minimum password length"                       = 14
    "Password must meet complexity requirements"    = $true
    "Store passwords using reversible encryption"   = $false
}

# Verificare la policy corrente
net accounts | Select-String "password|lockout"

# Verificare tramite secedit
secedit /export /cfg "C:\Temp\secpolicy.cfg"
Get-Content "C:\Temp\secpolicy.cfg" | Select-String "Password|Lockout"
```

---

## CIS Benchmark — Approfondimento Level 1 e Level 2

### Level 1 — Controlli Fondamentali

Il Level 1 dei CIS Benchmark rappresenta le impostazioni di sicurezza minime che ogni server in produzione dovrebbe avere. Queste configurazioni non impattano significativamente la funzionalità e sono applicabili alla grande maggioranza degli ambienti.

```powershell
# ═══════════════════════════════════════════════════════════
# CIS Level 1 — Controlli chiave (Windows Server 2022)
# ═══════════════════════════════════════════════════════════

# 1.1 — Account Policies
# Password minima 14 caratteri (CIS 1.1.4)
net accounts /minpwlen:14

# History delle password: 24 (CIS 1.1.1)
net accounts /uniquepw:24

# Lockout threshold: 5 tentativi (CIS 1.2.2)
net accounts /lockoutthreshold:5

# Lockout duration: 15 minuti (CIS 1.2.1)
net accounts /lockoutduration:15

# Reset lockout counter: 15 minuti (CIS 1.2.3)
net accounts /lockoutwindow:15

# 2.2 — User Rights Assignment
# Deny access to this computer from the network: Guest (CIS 2.2.21)
# Deny log on locally: Guest (CIS 2.2.22)
# Configurare via GPO o secedit

# 2.3 — Security Options
# Interactive logon: Do not display last user name (CIS 2.3.7.1)
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -Name "DontDisplayLastUserName" -Value 1 -Type DWord

# Interactive logon: Machine inactivity limit = 900 seconds (CIS 2.3.7.3)
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -Name "InactivityTimeoutSecs" -Value 900 -Type DWord

# Network access: Do not allow anonymous enumeration of SAM accounts (CIS 2.3.10.2)
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "RestrictAnonymousSAM" -Value 1 -Type DWord

# Network security: LAN Manager authentication level = NTLMv2 only (CIS 2.3.11.7)
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "LmCompatibilityLevel" -Value 5 -Type DWord

# 9.1 — Windows Firewall Domain Profile
# Firewall state: On (CIS 9.1.1)
Set-NetFirewallProfile -Profile Domain -Enabled True -DefaultInboundAction Block

# 17 — Advanced Audit Policy Configuration
# Audit Credential Validation: Success and Failure (CIS 17.1.1)
auditpol /set /subcategory:"Credential Validation" /success:enable /failure:enable

# 18.4 — MSS Settings
# Enable Safe DLL search mode (CIS 18.4.8)
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager" `
    -Name "SafeDllSearchMode" -Value 1 -Type DWord

# Enable Screen Saver Grace Period (CIS 18.4.9)
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" `
    -Name "ScreenSaverGracePeriod" -Value "5" -Type String
```

### Level 2 — Controlli Avanzati

Il Level 2 include configurazioni più restrittive che possono impattare la funzionalità di alcune applicazioni. Ogni controllo Level 2 deve essere testato nell'ambiente specifico prima del deployment.

```powershell
# ═══════════════════════════════════════════════════════════
# CIS Level 2 — Controlli avanzati (Windows Server 2022)
# ═══════════════════════════════════════════════════════════

# 2.2 — User Rights Assignment (Level 2 additions)
# Deny log on through Remote Desktop Services: Guest, Local account (CIS 2.2.26)
# Configurare via GPO: "Deny log on through Remote Desktop Services"

# 2.3 — Security Options
# Network security: Do not store LAN Manager hash value (CIS 2.3.11.5)
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "NoLMHash" -Value 1 -Type DWord

# Network security: Force logoff when logon hours expire (CIS 2.3.11.6)
net accounts /forcelogoff:yes

# 5.x — System Services (Level 2)
# Disabilitare Xbox Accessory Management, Xbox Game Monitoring, ecc.
$level2Services = @(
    "XboxGipSvc", "XblGameSave", "XblAuthManager",
    "WpnService",   # Windows Push Notifications System Service
    "PushToInstall"  # Windows PushToInstall Service
)
foreach ($svc in $level2Services) {
    Set-Service -Name $svc -StartupType Disabled -ErrorAction SilentlyContinue
}

# 18.1 — Control Panel (Level 2)
# Personalization: Enable screen saver (CIS 18.1.1.1)
Set-ItemProperty "HKCU:\Control Panel\Desktop" -Name "ScreenSaveActive" -Value "1"

# Personalization: Screen saver timeout = 900 (CIS 18.1.1.2)
Set-ItemProperty "HKCU:\Control Panel\Desktop" -Name "ScreenSaveTimeOut" -Value "900"

# 18.6 — Network (Level 2)
# Prohibit installation and configuration of Network Bridge (CIS 18.6.1)
New-Item "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Network Connections" -Force | Out-Null
Set-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Network Connections" `
    -Name "NC_AllowNetBridge_NLA" -Value 0 -Type DWord

# 18.9 — Windows Components (Level 2)
# Disable Autoplay for all drives (CIS 18.9.8.1)
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer" `
    -Name "NoDriveTypeAutoRun" -Value 255 -Type DWord

# Turn off Windows Error Reporting (CIS 18.9.20.1.1)
Set-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Windows Error Reporting" `
    -Name "Disabled" -Value 1 -Type DWord

# Disabilitare Windows Ink Workspace (CIS 18.9.46.1)
New-Item "HKLM:\SOFTWARE\Policies\Microsoft\WindowsInkWorkspace" -Force | Out-Null
Set-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\WindowsInkWorkspace" `
    -Name "AllowWindowsInkWorkspace" -Value 0 -Type DWord
```

### Documentazione delle Eccezioni

Ogni deviazione dalla baseline CIS deve essere documentata formalmente. Il registro delle eccezioni è un requisito di audit e compliance.

```
REGISTRO ECCEZIONI CIS BENCHMARK
=================================

┌──────────┬────────────┬────────────────────────┬───────────────────────┬──────────────┬────────────┐
│ CIS ID   │ Livello    │ Descrizione Controllo  │ Motivo Eccezione      │ Approvato da │ Scadenza   │
├──────────┼────────────┼────────────────────────┼───────────────────────┼──────────────┼────────────┤
│ 2.3.11.7 │ L1         │ NTLMv2 only            │ App legacy ERP-SAP    │ CISO         │ 2026-12-31 │
│ 9.3.1    │ L1         │ FW Public profile on   │ DMZ server specifico  │ NetSec Lead  │ 2026-09-30 │
│ 18.4.8   │ L1         │ Safe DLL search mode   │ Incomp. driver HW     │ SysAdmin     │ 2026-06-30 │
│ ...      │ ...        │ ...                    │ ...                   │ ...          │ ...        │
└──────────┴────────────┴────────────────────────┴───────────────────────┴──────────────┴────────────┘

Regole:
- Ogni eccezione ha una data di scadenza (max 12 mesi)
- Alla scadenza, l'eccezione deve essere rivalutata o eliminata
- Il risk owner è responsabile della mitigazione compensativa
- Le eccezioni sono soggette ad audit interno trimestrale
```

---

## DISA STIG per Windows Server

### Panoramica STIG

I DISA STIG (Security Technical Implementation Guides) sono standard di hardening pubblicati dalla Defense Information Systems Agency del Dipartimento della Difesa USA. Mentre i CIS Benchmark sono consenso dell'industria, i DISA STIG sono requisiti obbligatori per i sistemi governativi e militari, e rappresentano un riferimento di alto livello anche per il settore privato.

Ogni finding STIG è classificato con una severità CAT I (critica), CAT II (alta) o CAT III (media):

| Categoria | Severità | Impatto se non mitigato |
|-----------|----------|-------------------------|
| CAT I | Critica | Compromissione diretta del sistema, perdita di dati classificati |
| CAT II | Alta | Significativa riduzione della postura di sicurezza |
| CAT III | Media | Rischio minore, best practice non rispettata |

### SCAP Scanning

SCAP (Security Content Automation Protocol) permette la scansione automatizzata della conformità STIG.

```powershell
# DISA fornisce lo SCAP Compliance Checker (SCC)
# Download: https://public.cyber.mil/stigs/scap/

# Installazione SCC (da prompt elevato)
# msiexec /i "SCC_5.10_Windows_X64.msi" /qn

# Esecuzione di uno scan STIG per Windows Server 2022
# Dalla GUI: SCC → Content → selezionare il benchmark → Scan

# Esportazione risultati in formato STIG Viewer (CKL)
# SCC genera automaticamente file .ckl per ogni scan

# Alternativa open-source: OpenSCAP (su Linux o cross-platform)
# Per Windows, usare il PowerShell DSC STIG module:
Install-Module -Name PowerSTIG -Scope AllUsers
# Generare una configurazione DSC basata sullo STIG:
$stigConfig = @{
    OsVersion   = "2022"
    OsRole      = "MS"  # Member Server (DC = "DC")
    StigVersion = "2.2"
    Exception   = @{
        "V-254243" = @{ ValueData = "1" }  # Eccezione documentata
    }
}
# Import-Module PowerSTIG
# WindowsServer -OsVersion $stigConfig.OsVersion ...
```

### Remediation Workflow

```
WORKFLOW DISA STIG REMEDIATION
==============================

1. SCAN INIZIALE
   └─→ SCC scan completo → report baseline (CKL)

2. TRIAGE
   └─→ Classificare findings per CAT I → CAT II → CAT III
   └─→ CAT I: remediation immediata (entro 30 giorni)
   └─→ CAT II: remediation pianificata (entro 90 giorni)
   └─→ CAT III: valutare e pianificare

3. REMEDIATION
   └─→ Per ogni finding:
        a. Leggere il fix text dello STIG
        b. Testare in ambiente di laboratorio
        c. Applicare in produzione (change management)
        d. Documentare l'eccezione se non applicabile

4. VALIDAZIONE
   └─→ Re-scan dopo remediation
   └─→ Confrontare con scan precedente
   └─→ Verificare che nessun finding risolto sia regredito

5. REPORTING
   └─→ Generare POA&M (Plan of Action and Milestones)
   └─→ Report alla governance per CAT I aperti
   └─→ Ciclo trimestrale di re-scan
```

---

## Disabilitazione Servizi Non Necessari

Ogni servizio in esecuzione è un potenziale vettore di attacco. L'approccio corretto è disabilitare tutti i servizi non richiesti dal ruolo specifico del server.

```powershell
# Servizi comunemente disabilitati sui server (valutare per ogni ruolo)
$servicesToDisable = @(
    "XblGameSave"              # Xbox Live Game Save
    "XblAuthManager"           # Xbox Live Auth Manager
    "MapsBroker"               # Downloaded Maps Manager
    "lfsvc"                    # Geolocation Service
    "SharedAccess"             # Internet Connection Sharing
    "Browser"                  # Computer Browser (legacy)
    "SSDPSRV"                  # SSDP Discovery
    "upnphost"                 # UPnP Device Host
    "WMPNetworkSvc"            # Windows Media Player Sharing
    "icssvc"                   # Windows Mobile Hotspot Service
    "WerSvc"                   # Windows Error Reporting (valutare)
    "DiagTrack"                # Connected User Experiences and Telemetry
    "dmwappushservice"         # Device Management WAP Push
    "RetailDemo"               # Retail Demo Service
    "RemoteRegistry"           # Remote Registry (rischio sicurezza!)
    "Fax"                      # Fax
    "TapiSrv"                  # Telephony
)

foreach ($svc in $servicesToDisable) {
    $service = Get-Service -Name $svc -ErrorAction SilentlyContinue
    if ($service) {
        if ($service.Status -eq 'Running') { Stop-Service $svc -Force }
        Set-Service $svc -StartupType Disabled
        Write-Output "Disabilitato: $svc ($($service.DisplayName))"
    }
}

# Verificare i servizi in esecuzione con account privilegiati
Get-WmiObject Win32_Service |
    Where-Object { $_.StartName -eq "LocalSystem" -and $_.State -eq "Running" } |
    Select-Object Name, DisplayName, StartName, PathName |
    Sort-Object Name | Format-Table -AutoSize

# Servizi CRITICI che NON devono essere disabilitati
# - CryptSvc (Cryptographic Services)
# - EventLog (Windows Event Log)
# - gpsvc (Group Policy Client)
# - MpsSvc (Windows Firewall)
# - WinDefend (Windows Defender)
# - W32Time (Windows Time)
# - Netlogon (per server in dominio)
# - NTDS (per Domain Controller)
```

---

## Service Hardening Avanzato

### Sicurezza degli Account di Servizio

I servizi Windows che girano come LocalSystem hanno accesso completo al sistema operativo. Ridurre i privilegi degli account di servizio è una misura critica di hardening.

```powershell
# Audit: elencare tutti i servizi che girano come LocalSystem
Get-WmiObject Win32_Service |
    Where-Object { $_.StartName -eq "LocalSystem" -and $_.State -eq "Running" } |
    Select-Object Name, DisplayName, PathName |
    Sort-Object Name | Format-Table -AutoSize

# Audit: servizi con path non quotato (vulnerabilità unquoted service path)
Get-WmiObject Win32_Service | Where-Object {
    $_.PathName -notmatch '^"' -and
    $_.PathName -match '\s' -and
    $_.PathName -notmatch '^C:\\Windows\\system32'
} | Select-Object Name, DisplayName, PathName

# Per servizi custom: creare gMSA (Group Managed Service Account)
# Vedere sezione dedicata più avanti

# Per servizi che non necessitano di privilegi elevati:
# cambiare l'account a Local Service o Network Service
# Local Service = minimo privilegio, no accesso rete
# Network Service = minimo privilegio, accesso rete come account computer
```

### Per-Service SID Isolation

Windows supporta l'isolamento dei servizi tramite Service SID, che permette di assegnare permessi specifici a un servizio senza utilizzare un account dedicato.

```powershell
# Verificare il tipo di SID di un servizio
sc.exe qsidtype <nome_servizio>

# Tipi di Service SID:
# NONE        = nessun SID del servizio (legacy)
# UNRESTRICTED = SID aggiunto al token, usato per ACL
# RESTRICTED   = SID aggiunto + token restricted (più sicuro)

# Impostare il Service SID type su Restricted
sc.exe sidtype <nome_servizio> restricted

# Esempio: isolare il servizio Windows Time
sc.exe sidtype W32Time restricted

# Verificare i permessi del file system per un servizio specifico
$serviceName = "W32Time"
$serviceInfo = Get-WmiObject Win32_Service -Filter "Name='$serviceName'"
$servicePath = ($serviceInfo.PathName -replace '"','').Split(' ')[0]
$parentDir = Split-Path $servicePath
Get-Acl $parentDir | Format-List
```

### Servizi e Permessi del File System

```powershell
# Verificare che le directory dei servizi non siano scrivibili da utenti non privilegiati
$services = Get-WmiObject Win32_Service | Where-Object {
    $_.PathName -and $_.PathName -notmatch '^C:\\Windows\\system32'
}
foreach ($svc in $services) {
    $path = ($svc.PathName -replace '"','').Split(' ')[0]
    if (Test-Path $path) {
        $dir = Split-Path $path
        $acl = Get-Acl $dir -ErrorAction SilentlyContinue
        $writableByUsers = $acl.Access | Where-Object {
            $_.IdentityReference -match "Users|Everyone|Authenticated Users" -and
            $_.FileSystemRights -match "Write|Modify|FullControl"
        }
        if ($writableByUsers) {
            Write-Warning "ATTENZIONE: $($svc.Name) - directory scrivibile: $dir"
        }
    }
}
```

---

## Rimozione SMBv1 e Protocolli Legacy

### SMBv1

SMBv1 è un protocollo degli anni '90 con vulnerabilità note (EternalBlue/WannaCry). Deve essere rimosso da tutti i sistemi moderni.

```powershell
# Verificare se SMBv1 è installato/abilitato
Get-WindowsFeature FS-SMB1
Get-SmbServerConfiguration | Select-Object EnableSMB1Protocol

# Rimuovere SMBv1 completamente
Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -Remove -NoRestart
# oppure
Remove-WindowsFeature FS-SMB1

# Disabilitare SMBv1 sul server SMB (se la feature non può essere rimossa)
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force

# Disabilitare SMBv1 sul client SMB
Set-SmbClientConfiguration -EnableSMB1Protocol $false -Force
Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol-Client

# Verificare che solo SMBv2/v3 sia attivo
Get-SmbServerConfiguration | Select-Object EnableSMB1Protocol, EnableSMB2Protocol
```

### Hardening SMBv2/v3

```powershell
# Richiedere la firma SMB (previene relay attacks)
Set-SmbServerConfiguration -RequireSecuritySignature $true -Force
Set-SmbClientConfiguration -RequireSecuritySignature $true -Force

# Abilitare la cifratura SMB (SMB 3.0+)
Set-SmbServerConfiguration -EncryptData $true -Force

# Disabilitare l'accesso guest a SMB (previene accesso anonimo)
Set-SmbServerConfiguration -EnableAuthenticateUserSharing $true -Force

# Disabilitare le null session
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\LanManServer\Parameters" `
    -Name "RestrictNullSessAccess" -Value 1 -Type DWord

# Restringere l'enumerazione anonima delle share
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "RestrictAnonymous" -Value 1 -Type DWord
```

### Disabilitazione di Protocolli Obsoleti

```powershell
# Disabilitare TLS 1.0 e 1.1
$protocols = @("TLS 1.0", "TLS 1.1", "SSL 2.0", "SSL 3.0")
foreach ($protocol in $protocols) {
    $serverPath = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\$protocol\Server"
    $clientPath = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\$protocol\Client"

    New-Item -Path $serverPath -Force | Out-Null
    New-ItemProperty -Path $serverPath -Name "Enabled" -Value 0 -PropertyType DWord -Force
    New-ItemProperty -Path $serverPath -Name "DisabledByDefault" -Value 1 -PropertyType DWord -Force

    New-Item -Path $clientPath -Force | Out-Null
    New-ItemProperty -Path $clientPath -Name "Enabled" -Value 0 -PropertyType DWord -Force
    New-ItemProperty -Path $clientPath -Name "DisabledByDefault" -Value 1 -PropertyType DWord -Force
}

# Abilitare esplicitamente solo TLS 1.2 e 1.3
$enableProtocols = @("TLS 1.2", "TLS 1.3")
foreach ($protocol in $enableProtocols) {
    $serverPath = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\$protocol\Server"
    $clientPath = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\$protocol\Client"

    New-Item -Path $serverPath -Force | Out-Null
    New-ItemProperty -Path $serverPath -Name "Enabled" -Value 1 -PropertyType DWord -Force

    New-Item -Path $clientPath -Force | Out-Null
    New-ItemProperty -Path $clientPath -Name "Enabled" -Value 1 -PropertyType DWord -Force
}

# Disabilitare cipher suite deboli
$weakCiphers = @(
    "DES 56/56", "RC2 40/128", "RC2 56/128", "RC2 128/128",
    "RC4 40/128", "RC4 56/128", "RC4 64/128", "RC4 128/128",
    "Triple DES 168"
)
foreach ($cipher in $weakCiphers) {
    $path = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Ciphers\$cipher"
    New-Item -Path $path -Force | Out-Null
    New-ItemProperty -Path $path -Name "Enabled" -Value 0 -PropertyType DWord -Force
}

# Disabilitare WPAD (rischio MITM)
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\WinHttpAutoProxySvc" `
    -Name "Start" -Value 4 -Type DWord
```

---

## Disabilitazione LLMNR e NBT-NS

LLMNR (Link-Local Multicast Name Resolution) e NBT-NS (NetBIOS Name Service) sono protocolli di risoluzione nomi locali che possono essere sfruttati per intercettare credenziali tramite attacchi di poisoning (es. Responder, Inveigh).

```powershell
# Disabilitare LLMNR tramite GPO (metodo raccomandato)
# Computer Configuration → Administrative Templates → Network → DNS Client
#   → Turn off multicast name resolution: Enabled

# Disabilitare LLMNR tramite registry
New-Item "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" -Force | Out-Null
Set-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" `
    -Name "EnableMulticast" -Value 0 -Type DWord

# Disabilitare NBT-NS su tutte le interfacce di rete
$adapters = Get-WmiObject Win32_NetworkAdapterConfiguration | Where-Object { $_.IPEnabled -eq $true }
foreach ($adapter in $adapters) {
    $adapter.SetTcpipNetbios(2)  # 0=Default, 1=Enable, 2=Disable
}

# Verificare lo stato NBT-NS
Get-WmiObject Win32_NetworkAdapterConfiguration |
    Where-Object IPEnabled |
    Select-Object Description, TcpipNetbiosOptions
# TcpipNetbiosOptions: 0=Default, 1=Enabled, 2=Disabled

# Disabilitare mDNS (Multicast DNS, Windows 10+)
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\Dnscache\Parameters" `
    -Name "EnableMDNS" -Value 0 -Type DWord

# Disabilitare WPAD
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\WinHttpAutoProxySvc" `
    -Name "Start" -Value 4 -Type DWord
```

---

## Sicurezza di Rete Avanzata

### IPsec Policies

IPsec permette di cifrare e autenticare il traffico di rete tra server, creando un ulteriore livello di protezione per il traffico interno che non utilizza TLS applicativo.

```powershell
# Creare una regola IPsec per proteggere il traffico tra server applicativi
# Fase 1: Connection Security Rule (autenticazione)
New-NetIPsecRule -DisplayName "Server-to-Server IPsec" `
    -InboundSecurity Require `
    -OutboundSecurity Request `
    -Phase1AuthSet "ComputerKerb" `
    -Profile Domain `
    -InterfaceType Any `
    -Enabled True

# Creare un'autenticazione basata su certificati (per server non in dominio)
$certProp = New-NetIPsecAuthProposal -Machine -Cert `
    -Authority "DC=com,DC=contoso,CN=Contoso Root CA" `
    -AuthorityType Root
$authSet = New-NetIPsecPhase1AuthSet -DisplayName "CertAuth" `
    -Proposal $certProp

# Applicare IPsec tra due subnet specifiche
New-NetIPsecRule -DisplayName "App-to-DB IPsec" `
    -InboundSecurity Require `
    -OutboundSecurity Require `
    -LocalAddress "10.0.10.0/24" `
    -RemoteAddress "10.0.20.0/24" `
    -Phase1AuthSet $authSet.Name `
    -Protocol TCP `
    -LocalPort 1433 `
    -Profile Domain

# Verificare le regole IPsec attive
Get-NetIPsecRule | Where-Object Enabled -eq True |
    Select-Object DisplayName, InboundSecurity, OutboundSecurity | Format-Table

# Monitorare le Security Associations (SA) attive
Get-NetIPsecMainModeSA
Get-NetIPsecQuickModeSA
```

### SMB Signing e Encryption

```powershell
# Configurazione completa di SMB signing e encryption

# Server-side: richiedere signing su tutte le connessioni
Set-SmbServerConfiguration -RequireSecuritySignature $true -Force

# Server-side: richiedere encryption (SMB 3.0+)
Set-SmbServerConfiguration -EncryptData $true -Force

# Server-side: rifiutare connessioni da client che non supportano encryption
Set-SmbServerConfiguration -RejectUnencryptedAccess $true -Force

# Client-side: richiedere signing
Set-SmbClientConfiguration -RequireSecuritySignature $true -Force

# Per-share: abilitare encryption su share specifiche
Set-SmbShare -Name "SensitiveData" -EncryptData $true -Force

# Verificare la configurazione completa
Get-SmbServerConfiguration | Select-Object `
    RequireSecuritySignature, EncryptData, RejectUnencryptedAccess,
    EnableSMB1Protocol, EnableSMB2Protocol

# Monitorare connessioni SMB attive e il loro livello di cifratura
Get-SmbSession | Select-Object ClientComputerName, ClientUserName,
    Dialect, SigningRequired, EncryptionRequired | Format-Table
```

### Disabilitazione Protocolli Legacy di Rete

```powershell
# Disabilitare IPv6 se non utilizzato (valutare attentamente)
# NOTA: Microsoft non raccomanda la disabilitazione di IPv6 in modo generico
# Farlo SOLO se IPv6 non è utilizzato e causa problemi di sicurezza
# Disabilitare via registry (binding rimane, ma stack disabilitato):
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters" `
    -Name "DisabledComponents" -Value 0xFF -Type DWord

# Disabilitare NetBIOS over TCP/IP (se non necessario per app legacy)
# Già coperto nella sezione LLMNR/NBT-NS

# Disabilitare il Link-Layer Topology Discovery (LLTD)
# Previene la mappatura automatica della rete
Set-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\LLTD" `
    -Name "EnableLLTDIO" -Value 0 -Type DWord
Set-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\LLTD" `
    -Name "EnableRspndr" -Value 0 -Type DWord

# Disabilitare il servizio SNMP se non necessario
Set-Service SNMP -StartupType Disabled -ErrorAction SilentlyContinue
Stop-Service SNMP -ErrorAction SilentlyContinue

# Disabilitare Telnet Client (se installato)
Disable-WindowsOptionalFeature -Online -FeatureName TelnetClient -NoRestart -ErrorAction SilentlyContinue

# Verificare le porte in ascolto e i processi associati
Get-NetTCPConnection -State Listen |
    Select-Object LocalAddress, LocalPort, OwningProcess,
        @{N='ProcessName';E={(Get-Process -Id $_.OwningProcess).ProcessName}} |
    Sort-Object LocalPort | Format-Table -AutoSize
```

---

## Credential Protection

### LSA Protection

LSA Protection impedisce l'accesso non autorizzato al processo LSASS (Local Security Authority Subsystem Service), che memorizza le credenziali in memoria. Strumenti come Mimikatz sfruttano l'accesso a LSASS per estrarre password e hash.

```powershell
# Abilitare LSA Protection (RunAsPPL)
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "RunAsPPL" -Value 1 -Type DWord

# Verificare lo stato
Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "RunAsPPL"

# Nota: LSA Protection richiede riavvio e potrebbe bloccare driver
# di autenticazione di terze parti non firmati come PPL
```

### Credential Guard

Credential Guard utilizza la sicurezza basata sulla virtualizzazione (VBS) per isolare le credenziali in un ambiente protetto dall'hypervisor, rendendole inaccessibili anche al kernel del sistema operativo.

```powershell
# Prerequisiti:
# - UEFI Secure Boot
# - TPM 2.0 (raccomandato)
# - Hyper-V (installato automaticamente)
# - 64-bit OS

# Abilitare Credential Guard tramite GPO
# Computer Configuration → Administrative Templates → System → Device Guard
#   → Turn On Virtualization Based Security: Enabled
#     - Platform Security Level: Secure Boot and DMA Protection
#     - Credential Guard Configuration: Enabled with UEFI lock

# Abilitare tramite registry
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard" `
    -Name "EnableVirtualizationBasedSecurity" -Value 1 -Type DWord
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard" `
    -Name "RequirePlatformSecurityFeatures" -Value 3 -Type DWord
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "LsaCfgFlags" -Value 1 -Type DWord

# Verificare lo stato di Credential Guard
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
    Select-Object SecurityServicesRunning, VirtualizationBasedSecurityStatus
# SecurityServicesRunning: 1 = Credential Guard attivo
```

### Protezione Aggiuntiva delle Credenziali

```powershell
# Disabilitare WDigest (memorizzazione password in chiaro in LSASS)
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\WDigest" `
    -Name "UseLogonCredential" -Value 0 -Type DWord

# Disabilitare la cache delle credenziali (o ridurla)
# Default: 10 logon cached, ridurre a 2-4 per server, 0 per DC
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" `
    -Name "CachedLogonsCount" -Value 2 -Type String

# Prevenire l'esecuzione di Mimikatz e tool simili
# (via ASR rules o AppLocker — vedere guida dedicata)

# Disabilitare la delega non vincolata su tutti i computer (tranne DC)
# Verificare computer con delega non vincolata
Get-ADComputer -Filter 'TrustedForDelegation -eq $true' -Properties TrustedForDelegation |
    Where-Object Name -notlike "*DC*" |
    Select-Object Name, TrustedForDelegation

# Rimuovere la delega non vincolata
Set-ADComputer "SERVER01" -TrustedForDelegation $false
```

---

## Account Security Avanzata

### Protected Users Group

Il gruppo Protected Users è un gruppo di sicurezza globale introdotto in Windows Server 2012 R2 che applica automaticamente restrizioni di sicurezza non configurabili agli account membri. È lo strumento principale per proteggere gli account amministrativi.

```powershell
# Restrizioni applicate automaticamente ai membri di Protected Users:
# - NTLM non disponibile (solo Kerberos)
# - DES e RC4 non usati per Kerberos pre-authentication
# - Nessuna delega Kerberos (unconstrained e constrained)
# - Nessun rinnovo del TGT oltre le 4 ore (default)
# - Nessuna cache delle credenziali offline
# - WDigest non memorizza credenziali in chiaro

# Aggiungere account amministrativi al gruppo Protected Users
Add-ADGroupMember -Identity "Protected Users" -Members "admin-tier0", "admin-tier1"

# Verificare i membri
Get-ADGroupMember -Identity "Protected Users" | Select-Object Name, SamAccountName

# ATTENZIONE: NON aggiungere account di servizio o gMSA!
# Protected Users blocca NTLM e delega, causando failure per i servizi

# Verificare che gli account aggiunti funzionino correttamente
# Testare l'autenticazione Kerberos dopo l'aggiunta:
klist purge
# Effettuare logon e verificare che il TGT sia emesso
klist tickets

# Monitorare eventi correlati a Protected Users
# Event ID 100 (ProtectedUser) nel log di sicurezza
Get-WinEvent -FilterHashtable @{LogName='Security'; ID=100} -MaxEvents 10 -ErrorAction SilentlyContinue
```

### Fine-Grained Password Policies (PSO)

Le Fine-Grained Password Policies (FGPP) permettono di definire policy di password diverse per gruppi diversi di utenti all'interno dello stesso dominio, superando il limite storico di una sola password policy per dominio.

```powershell
# Prerequisito: livello funzionale dominio >= Windows Server 2008

# Creare una PSO per gli account amministrativi (più restrittiva)
New-ADFineGrainedPasswordPolicy -Name "PSO-Admins-Tier0" `
    -Precedence 10 `
    -ComplexityEnabled $true `
    -LockoutDuration "00:30:00" `
    -LockoutObservationWindow "00:30:00" `
    -LockoutThreshold 3 `
    -MaxPasswordAge "90.00:00:00" `
    -MinPasswordAge "1.00:00:00" `
    -MinPasswordLength 20 `
    -PasswordHistoryCount 24 `
    -ReversibleEncryptionEnabled $false

# Creare una PSO per gli utenti standard (meno restrittiva)
New-ADFineGrainedPasswordPolicy -Name "PSO-Users-Standard" `
    -Precedence 50 `
    -ComplexityEnabled $true `
    -LockoutDuration "00:15:00" `
    -LockoutObservationWindow "00:15:00" `
    -LockoutThreshold 5 `
    -MaxPasswordAge "365.00:00:00" `
    -MinPasswordAge "1.00:00:00" `
    -MinPasswordLength 14 `
    -PasswordHistoryCount 24 `
    -ReversibleEncryptionEnabled $false

# Applicare la PSO a un gruppo
Add-ADFineGrainedPasswordPolicySubject -Identity "PSO-Admins-Tier0" `
    -Subjects "Domain Admins", "Enterprise Admins"

Add-ADFineGrainedPasswordPolicySubject -Identity "PSO-Users-Standard" `
    -Subjects "Domain Users"

# Verificare quale PSO si applica a un utente specifico
Get-ADUserResultantPasswordPolicy -Identity "admin-tier0"

# Elencare tutte le PSO con i relativi soggetti
Get-ADFineGrainedPasswordPolicy -Filter * |
    Select-Object Name, Precedence, MinPasswordLength, MaxPasswordAge,
    @{N='AppliedTo';E={(Get-ADFineGrainedPasswordPolicySubject -Identity $_.Name).Name -join ", "}} |
    Format-Table -AutoSize
```

### AdminSDHolder e SDProp

AdminSDHolder è un container speciale in Active Directory che definisce le ACL applicate automaticamente a tutti gli account e gruppi protetti (Domain Admins, Enterprise Admins, ecc.) tramite il processo SDProp, che viene eseguito ogni 60 minuti dal PDC Emulator.

```powershell
# Verificare le ACL correnti su AdminSDHolder
$adminSDHolder = "AD:\CN=AdminSDHolder,CN=System,DC=contoso,DC=com"
(Get-Acl $adminSDHolder).Access |
    Select-Object IdentityReference, AccessControlType, ActiveDirectoryRights |
    Format-Table -AutoSize

# Elencare gli account con il flag adminCount = 1
# (account protetti da AdminSDHolder/SDProp)
Get-ADUser -Filter 'adminCount -eq 1' -Properties adminCount, MemberOf |
    Select-Object Name, SamAccountName, Enabled,
        @{N='Groups';E={($_.MemberOf | ForEach-Object { ($_ -split ',')[0] -replace 'CN=' }) -join ", "}}

# RISCHIO: account "orfani" con adminCount=1 che non sono più in gruppi protetti
# Questi account mantengono le ACL restrittive di AdminSDHolder anche dopo la rimozione
# dal gruppo, impedendo la corretta ereditarietà delle ACL
Get-ADUser -Filter 'adminCount -eq 1' -Properties MemberOf | Where-Object {
    $protectedGroups = @("Domain Admins","Enterprise Admins","Schema Admins",
                         "Administrators","Account Operators","Server Operators",
                         "Print Operators","Backup Operators")
    $memberGroups = $_.MemberOf | ForEach-Object { ($_ -split ',')[0] -replace 'CN=' }
    -not ($memberGroups | Where-Object { $_ -in $protectedGroups })
} | Select-Object Name, SamAccountName

# Per correggere gli account orfani: resettare adminCount e ripristinare ereditarietà ACL
# Set-ADUser "utente-orfano" -Clear adminCount
# dsacls "CN=utente-orfano,OU=Users,DC=contoso,DC=com" /resetDefaultDACL
```

### Privileged Access Tiers (Tier Model)

Il modello a livelli (Tier Model) di Microsoft separa gli asset e gli account amministrativi in tre livelli per prevenire il lateral movement e l'escalation dei privilegi.

```
TIER MODEL — PRIVILEGED ACCESS
═══════════════════════════════════════════════════════════════

TIER 0 — IDENTITA' (Forest/Domain Control)
├── Domain Controllers, AD Federation Services
├── Certificate Authority (Enterprise CA)
├── Azure AD Connect, PKI infrastructure
├── Account: Domain Admins, Enterprise Admins, Schema Admins
└── Regola: MAI fare logon da workstation Tier 1 o Tier 2

TIER 1 — APPLICAZIONI (Server e Servizi)
├── Application servers, database servers, file servers
├── Exchange, SharePoint, SQL Server, SCCM
├── Account: Server Admins, Application Admins
└── Regola: MAI fare logon da workstation Tier 2 o Tier 0

TIER 2 — ENDPOINT (Workstation e Dispositivi)
├── Workstation, laptop, stampanti, dispositivi utente
├── Help desk, supporto locale
├── Account: Workstation Admins, Help Desk
└── Regola: MAI fare logon a server Tier 0 o Tier 1

REGOLA FONDAMENTALE:
  Le credenziali di un tier NON devono MAI essere esposte
  su un dispositivo di un tier inferiore.
  (Tier 0 > Tier 1 > Tier 2)
```

```powershell
# Implementazione del Tier Model con GPO
# Creare OU separate per ogni tier
New-ADOrganizationalUnit -Name "Tier0-Assets" -Path "DC=contoso,DC=com"
New-ADOrganizationalUnit -Name "Tier1-Assets" -Path "DC=contoso,DC=com"
New-ADOrganizationalUnit -Name "Tier2-Assets" -Path "DC=contoso,DC=com"

# Creare gruppi per ogni tier
New-ADGroup -Name "Tier0-Admins" -GroupScope Global -Path "OU=Tier0-Assets,DC=contoso,DC=com"
New-ADGroup -Name "Tier1-Admins" -GroupScope Global -Path "OU=Tier1-Assets,DC=contoso,DC=com"
New-ADGroup -Name "Tier2-Admins" -GroupScope Global -Path "OU=Tier2-Assets,DC=contoso,DC=com"

# GPO: Deny logon dei Tier0-Admins su workstation e server applicativi
# Computer Configuration → Policies → Windows Settings → Security Settings
#   → Local Policies → User Rights Assignment
#   → "Deny log on locally": Tier0-Admins (applicata su Tier1 e Tier2 OU)
#   → "Deny log on through RDP": Tier0-Admins (applicata su Tier1 e Tier2 OU)

# Verifica: controllare dove un account Tier0 può effettuare logon
# Event ID 4624 con tipo 2 (Interactive) o 10 (RDP) sui server non-Tier0
Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624} -MaxEvents 1000 |
    Where-Object { $_.Properties[5].Value -in @("admin-t0") -and $_.Properties[8].Value -in @(2,10) }
```

### Group Managed Service Accounts (gMSA)

I gMSA sono account di servizio il cui password è gestita automaticamente da Active Directory (rotazione ogni 30 giorni, 240 caratteri). Eliminano la necessità di gestire manualmente le password dei service account.

```powershell
# Prerequisito: creare la KDS root key (una volta per forest)
# In produzione, la chiave è disponibile dopo 10 ore (per la replica)
Add-KdsRootKey -EffectiveImmediately  # Solo per lab!
# In produzione:
# Add-KdsRootKey -EffectiveTime ((Get-Date).AddHours(-10))

# Creare un gMSA
New-ADServiceAccount -Name "gMSA-SQLEngine" `
    -DNSHostName "gmsa-sqlengine.contoso.com" `
    -PrincipalsAllowedToRetrieveManagedPassword "SQL-Servers" `
    -KerberosEncryptionType AES128,AES256

# Installare il gMSA sul server che lo utilizzerà
Install-ADServiceAccount -Identity "gMSA-SQLEngine"

# Testare il gMSA
Test-ADServiceAccount -Identity "gMSA-SQLEngine"
# Risultato atteso: True

# Configurare un servizio Windows per usare il gMSA
# Nel campo "Log On As" del servizio: CONTOSO\gMSA-SQLEngine$
# La password è vuota (gestita da AD)

# Elencare tutti i gMSA nel dominio
Get-ADServiceAccount -Filter * -Properties PrincipalsAllowedToRetrieveManagedPassword |
    Select-Object Name, DNSHostName, Created,
        @{N='AllowedHosts';E={$_.PrincipalsAllowedToRetrieveManagedPassword}} |
    Format-Table -AutoSize
```

---

## Credential Guard e Prevenzione del Furto di Credenziali Remote

### Remote Credential Guard

Remote Credential Guard protegge le credenziali durante le sessioni Remote Desktop, impedendo che vengano esposte sul server remoto. A differenza di Restricted Admin Mode, permette il single sign-on verso risorse di rete dalla sessione remota.

```powershell
# Abilitare Remote Credential Guard via GPO
# Computer Configuration → Administrative Templates → System → Credentials Delegation
#   → "Restrict delegation of credentials to remote servers": Enabled
#   → Mode: "Require Remote Credential Guard"

# Abilitare via registry
Set-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\CredentialsDelegation" `
    -Name "RestrictedRemoteAdministration" -Value 2 -Type DWord
# 0 = Disabled, 1 = Require Restricted Admin, 2 = Require Remote Credential Guard

# Connettersi con Remote Credential Guard
mstsc.exe /remoteGuard /v:SERVER01

# Via PowerShell (WinRM):
Enter-PSSession -ComputerName SERVER01 -Credential (Get-Credential) -Authentication CredSSP
# NOTA: CredSSP è un'alternativa ma meno sicura. Preferire Remote Credential Guard.

# Verificare che Remote Credential Guard sia attivo nella sessione
# Sul server remoto, verificare che non ci siano credenziali in LSASS
# Non ci sono hash dell'utente nel processo lsass.exe del server remoto
```

### Restrizioni NTLM

NTLM è un protocollo di autenticazione legacy vulnerabile a relay attacks, pass-the-hash e brute force. La strategia è restringere NTLM progressivamente fino alla completa eliminazione.

```powershell
# Fase 1: AUDIT — monitorare l'uso di NTLM prima di bloccarlo
# GPO: Network security: Restrict NTLM: Audit NTLM authentication in this domain
# = "Enable all"

# GPO: Network security: Restrict NTLM: Audit Incoming NTLM Traffic
# = "Enable auditing for all accounts"

# Verificare il log di audit NTLM (dopo aver abilitato l'audit)
Get-WinEvent -LogName "Microsoft-Windows-NTLM/Operational" -MaxEvents 100 |
    Select-Object TimeCreated, Message | Format-Table -Wrap

# Fase 2: ECCEZIONI — creare una lista di eccezioni per le app legacy
# GPO: Network security: Restrict NTLM: Add server exceptions in this domain
# Valore: lista di server che necessitano ancora di NTLM

# Fase 3: ENFORCEMENT
# GPO: Network security: Restrict NTLM: NTLM authentication in this domain
# = "Deny all domain accounts to domain servers"

# Registry: LAN Manager authentication level
# Valore 5 = Invia solo risposte NTLMv2, rifiuta LM e NTLM
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "LmCompatibilityLevel" -Value 5 -Type DWord

# Disabilitare la memorizzazione di hash LM
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "NoLMHash" -Value 1 -Type DWord

# Verificare l'uso di NTLM nel dominio (dopo enforcement)
Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4776} -MaxEvents 50 |
    Select-Object TimeCreated,
        @{N='User';E={$_.Properties[1].Value}},
        @{N='Workstation';E={$_.Properties[2].Value}},
        @{N='Status';E={$_.Properties[3].Value}}
```

### Kerberos Armoring (FAST)

Kerberos FAST (Flexible Authentication Secure Tunneling) protegge lo scambio di pre-autenticazione Kerberos da attacchi offline come AS-REP Roasting, wrapping il messaggio KDC in un tunnel TGT esistente.

```powershell
# Prerequisiti:
# - Domain Functional Level >= Windows Server 2012
# - Tutti i DC devono supportare FAST
# - Client Windows 8+ o Server 2012+

# Abilitare Kerberos Armoring (FAST) tramite GPO
# Computer Configuration → Policies → Administrative Templates
#   → System → KDC
#   → "KDC support for claims, compound authentication and Kerberos armoring"
#   = "Supported" (inizialmente) poi "Always provide claims" (dopo test)

# Computer Configuration → Policies → Administrative Templates
#   → System → Kerberos
#   → "Kerberos client support for claims, compound authentication and Kerberos armoring"
#   = "Enabled"

# Verificare che FAST sia attivo per un utente
klist tickets
# I ticket mostreranno il flag "FAST" se armoring è attivo

# Protezione aggiuntiva: richiedere pre-autenticazione per tutti gli account
# Cercare account senza pre-autenticazione (vulnerabili a AS-REP Roasting)
Get-ADUser -Filter 'DoesNotRequirePreAuth -eq $true' -Properties DoesNotRequirePreAuth |
    Select-Object Name, SamAccountName, DoesNotRequirePreAuth

# Correggere: abilitare la pre-autenticazione
Get-ADUser -Filter 'DoesNotRequirePreAuth -eq $true' |
    Set-ADAccountControl -DoesNotRequirePreAuth $false
```

---

## Configurazione Event Log e Audit Policy

### Dimensionamento dei Log

```powershell
# Aumentare la dimensione dei log di sicurezza
$logs = @{
    "Security"    = 1024MB  # 1 GB per security log
    "System"      = 256MB
    "Application" = 256MB
    "Microsoft-Windows-PowerShell/Operational" = 256MB
    "Microsoft-Windows-Sysmon/Operational"      = 512MB
}

foreach ($log in $logs.GetEnumerator()) {
    $logName = $log.Key
    $maxSize = $log.Value
    wevtutil sl $logName /ms:$maxSize
    Write-Output "Configurato $logName: $($maxSize / 1MB) MB"
}

# Verificare le dimensioni correnti
Get-WinEvent -ListLog Security,System,Application |
    Select-Object LogName, MaximumSizeInBytes,
        @{N='MaxSizeMB';E={$_.MaximumSizeInBytes / 1MB}},
        RecordCount, IsEnabled | Format-Table -AutoSize
```

### Advanced Audit Policy

```powershell
# Configurare l'Advanced Audit Policy (GPO o auditpol)
# Queste sono le impostazioni raccomandate per la detection delle minacce

# Account Logon
auditpol /set /subcategory:"Credential Validation" /success:enable /failure:enable
auditpol /set /subcategory:"Kerberos Authentication Service" /success:enable /failure:enable
auditpol /set /subcategory:"Kerberos Service Ticket Operations" /success:enable /failure:enable

# Account Management
auditpol /set /subcategory:"Computer Account Management" /success:enable /failure:enable
auditpol /set /subcategory:"Security Group Management" /success:enable /failure:enable
auditpol /set /subcategory:"User Account Management" /success:enable /failure:enable

# Logon/Logoff
auditpol /set /subcategory:"Logon" /success:enable /failure:enable
auditpol /set /subcategory:"Logoff" /success:enable
auditpol /set /subcategory:"Special Logon" /success:enable
auditpol /set /subcategory:"Other Logon/Logoff Events" /success:enable /failure:enable

# Object Access (selettivo, può generare molto volume)
auditpol /set /subcategory:"File System" /success:enable /failure:enable
auditpol /set /subcategory:"Registry" /success:enable /failure:enable
auditpol /set /subcategory:"SAM" /success:enable /failure:enable
auditpol /set /subcategory:"Removable Storage" /success:enable /failure:enable

# Policy Change
auditpol /set /subcategory:"Audit Policy Change" /success:enable /failure:enable
auditpol /set /subcategory:"Authentication Policy Change" /success:enable
auditpol /set /subcategory:"Authorization Policy Change" /success:enable

# Privilege Use
auditpol /set /subcategory:"Sensitive Privilege Use" /success:enable /failure:enable

# Process Tracking (critico per threat detection)
auditpol /set /subcategory:"Process Creation" /success:enable /failure:enable
auditpol /set /subcategory:"Process Termination" /success:enable

# System
auditpol /set /subcategory:"Security State Change" /success:enable /failure:enable
auditpol /set /subcategory:"Security System Extension" /success:enable /failure:enable
auditpol /set /subcategory:"System Integrity" /success:enable /failure:enable

# Abilitare il logging della command line nei processi (Event ID 4688)
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\Audit" `
    -Name "ProcessCreationIncludeCmdLine_Enabled" -Value 1 -Type DWord

# Abilitare il PowerShell Script Block Logging
Set-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" `
    -Name "EnableScriptBlockLogging" -Value 1 -Type DWord

# Abilitare il PowerShell Module Logging
Set-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ModuleLogging" `
    -Name "EnableModuleLogging" -Value 1 -Type DWord

# Verificare la configurazione audit
auditpol /get /category:*
```

### Event ID Critici per il Monitoring

| Event ID | Log | Descrizione |
|----------|-----|-------------|
| 4624 | Security | Logon riuscito |
| 4625 | Security | Logon fallito |
| 4648 | Security | Logon con credenziali esplicite |
| 4672 | Security | Privilegi speciali assegnati |
| 4688 | Security | Nuovo processo creato |
| 4698 | Security | Scheduled task creato |
| 4720 | Security | Account utente creato |
| 4728 | Security | Membro aggiunto a gruppo privilegiato |
| 4732 | Security | Membro aggiunto ad Administrators locali |
| 4768 | Security | Kerberos TGT richiesto |
| 4769 | Security | Kerberos service ticket richiesto |
| 4776 | Security | NTLM authentication |
| 7045 | System | Nuovo servizio installato |

---

## Audit Avanzato e Integrazione SIEM

### Windows Event Forwarding (WEF/WEC)

Windows Event Forwarding permette di centralizzare i log di sicurezza da tutti i server verso un collector, senza installare agenti aggiuntivi. È la soluzione Microsoft nativa per il log forwarding.

```powershell
# ═══════════════════════════════════════════════════════════
# CONFIGURAZIONE WEF — Windows Event Collector (WEC)
# ═══════════════════════════════════════════════════════════

# Sul server COLLECTOR (WEC):
# Abilitare il servizio Windows Event Collector
wecutil qc /q
# Oppure:
winrm quickconfig -q

# Creare una subscription per raccogliere eventi di sicurezza
wecutil cs SecurityEvents.xml

# Esempio di file SecurityEvents.xml per subscription:
# <Subscription xmlns="http://schemas.microsoft.com/2006/03/windows/events/subscription">
#   <SubscriptionId>SecurityForwarding</SubscriptionId>
#   <SubscriptionType>SourceInitiated</SubscriptionType>
#   <Description>Security events from all servers</Description>
#   <Enabled>true</Enabled>
#   <Uri>http://schemas.microsoft.com/wbem/wsman/1/windows/EventLog</Uri>
#   <ConfigurationMode>Custom</ConfigurationMode>
#   <Delivery Mode="Push">
#     <Batching>
#       <MaxLatencyTime>900000</MaxLatencyTime>
#     </Batching>
#   </Delivery>
#   <Query>
#     <![CDATA[
#       <QueryList>
#         <Query Id="0">
#           <Select Path="Security">
#             *[System[(EventID=4624 or EventID=4625 or EventID=4648 or
#               EventID=4672 or EventID=4688 or EventID=4698 or
#               EventID=4720 or EventID=4728 or EventID=4732 or
#               EventID=4768 or EventID=4769 or EventID=4776 or EventID=7045)]]
#           </Select>
#           <Select Path="Microsoft-Windows-Sysmon/Operational">*</Select>
#           <Select Path="Microsoft-Windows-PowerShell/Operational">
#             *[System[(EventID=4103 or EventID=4104)]]
#           </Select>
#         </Query>
#       </QueryList>
#     ]]>
#   </Query>
#   <ReadExistingEvents>false</ReadExistingEvents>
#   <TransportName>HTTP</TransportName>
#   <AllowedSourceNonDomainComputers></AllowedSourceNonDomainComputers>
#   <AllowedSourceDomainComputers>
#     O:NSG:NSD:(A;;GA;;;DC)(A;;GA;;;NS)
#   </AllowedSourceDomainComputers>
# </Subscription>

# ═══════════════════════════════════════════════════════════
# CONFIGURAZIONE WEF — Sui server SOURCE (via GPO)
# ═══════════════════════════════════════════════════════════

# GPO: Computer Configuration → Policies → Administrative Templates
#   → Windows Components → Event Forwarding
#   → "Configure target Subscription Manager"
# Valore: Server=http://WEC-SERVER.contoso.com:5985/wsman/SubscriptionManager/WEC

# Verificare la subscription
wecutil gs SecurityForwarding
wecutil gr SecurityForwarding  # Runtime status con lista dei source

# Verificare sul source che il forwarding funziona
wevtutil qe ForwardedEvents /c:5 /f:text
```

### Integrazione SIEM

```powershell
# Per l'invio dei log a un SIEM esterno (Splunk, Elastic, Sentinel),
# le opzioni principali sono:

# 1. WEF → SIEM Agent sul WEC (consigliato)
#    Il WEC centralizza i log, il SIEM agent raccoglie dal WEC
#    Riduce il numero di agenti da gestire

# 2. Syslog forwarding (per SIEM che accettano syslog)
#    Usare NXLog (open source) o Snare come forwarder
#    NXLog converte EVTX → syslog/CEF/JSON

# 3. Microsoft Sentinel (cloud-native)
#    Installare Azure Monitor Agent (AMA) sui server
#    Configurare Data Collection Rules (DCR) per gli eventi desiderati

# Esempio: configurare NXLog per forwarding syslog
# nxlog.conf (percorso: C:\Program Files\nxlog\conf\nxlog.conf)
# <Input eventlog>
#     Module im_msvistalog
#     Query <QueryList>\
#         <Query Id="0">\
#             <Select Path="Security">*[System[(EventID=4624 or EventID=4625)]]</Select>\
#         </Query>\
#     </QueryList>
# </Input>
# <Output syslog_out>
#     Module om_tcp
#     Host 10.0.50.10
#     Port 514
#     Exec to_syslog_ietf();
# </Output>
# <Route eventlog_to_syslog>
#     Path eventlog => syslog_out
# </Route>
```

### Event ID Critici — Tabella Estesa

| Event ID | Log | Descrizione | Rilevanza Security |
|----------|-----|-------------|-------------------|
| 1102 | Security | Security log cleared | Critico — possibile anti-forensics |
| 4616 | Security | System time changed | Alto — possibile manipolazione timestamp |
| 4624 (Type 3) | Security | Network logon | Medio — lateral movement tracking |
| 4624 (Type 10) | Security | RDP logon | Alto — accesso remoto interattivo |
| 4625 | Security | Failed logon | Alto — brute force detection |
| 4634 | Security | Logoff | Basso — correlazione sessioni |
| 4648 | Security | Logon con credenziali esplicite (runas) | Alto — privilege escalation |
| 4657 | Security | Registry value modified | Medio — persistence detection |
| 4663 | Security | Object access attempt | Medio — data exfiltration |
| 4672 | Security | Special privileges (admin logon) | Alto — privileged access |
| 4688 | Security | Process created (con command line) | Critico — execution tracking |
| 4697 | Security | Service installed | Critico — persistence mechanism |
| 4698 | Security | Scheduled task created | Critico — persistence mechanism |
| 4719 | Security | System audit policy changed | Critico — defense evasion |
| 4720 | Security | User account created | Alto — account creation |
| 4724 | Security | Password reset attempt | Alto — account takeover |
| 4728 | Security | Member added to security-enabled global group | Alto — privilege escalation |
| 4732 | Security | Member added to local Administrators | Critico — privilege escalation |
| 4738 | Security | User account changed | Medio — account modification |
| 4768 | Security | Kerberos TGT request | Medio — authentication tracking |
| 4769 | Security | Kerberos service ticket request | Medio — Kerberoasting detection |
| 4771 | Security | Kerberos pre-authentication failed | Alto — brute force |
| 4776 | Security | NTLM authentication attempt | Alto — NTLM usage tracking |
| 5140 | Security | Network share accessed | Medio — lateral movement |
| 5156 | Security | Windows Firewall allowed connection | Basso — network tracking |
| 5157 | Security | Windows Firewall blocked connection | Medio — blocked attempts |
| 7045 | System | New service installed | Critico — persistence mechanism |
| Sysmon 1 | Sysmon | Process create (hash, parent, cmdline) | Critico — execution chain |
| Sysmon 3 | Sysmon | Network connection | Alto — C2 detection |
| Sysmon 8 | Sysmon | CreateRemoteThread | Critico — injection detection |
| Sysmon 10 | Sysmon | Process access (LSASS) | Critico — credential theft |
| Sysmon 11 | Sysmon | File create | Medio — dropper detection |
| Sysmon 22 | Sysmon | DNS query | Alto — DNS tunneling/DGA |
| Sysmon 25 | Sysmon | Process tampering | Critico — hollowing/herpaderping |

---

## Windows Firewall Advanced Rules

```powershell
# Verificare lo stato del firewall per tutti i profili
Get-NetFirewallProfile | Select-Object Name, Enabled, DefaultInboundAction, DefaultOutboundAction

# Abilitare il firewall su tutti i profili con default deny inbound
Set-NetFirewallProfile -Profile Domain,Private,Public `
    -Enabled True `
    -DefaultInboundAction Block `
    -DefaultOutboundAction Allow `
    -LogAllowed True `
    -LogBlocked True `
    -LogFileName "C:\Windows\System32\LogFiles\Firewall\pfirewall.log" `
    -LogMaxSizeKilobytes 16384

# Regole essenziali per un server (esempio: Domain Controller)
# Nota: aprire SOLO le porte necessarie per il ruolo specifico

# Remote Desktop (solo da subnet di management)
New-NetFirewallRule -DisplayName "RDP - Management Only" `
    -Direction Inbound -Protocol TCP -LocalPort 3389 `
    -RemoteAddress "10.0.100.0/24" `
    -Action Allow -Profile Domain

# WinRM (PowerShell Remoting - solo da management)
New-NetFirewallRule -DisplayName "WinRM - Management Only" `
    -Direction Inbound -Protocol TCP -LocalPort 5985,5986 `
    -RemoteAddress "10.0.100.0/24" `
    -Action Allow -Profile Domain

# ICMP Echo (ping) - opzionale
New-NetFirewallRule -DisplayName "ICMP Echo" `
    -Direction Inbound -Protocol ICMPv4 -IcmpType 8 `
    -Action Allow -Profile Domain

# Bloccare porte notoriamente pericolose in uscita
$dangerousPorts = @(4444, 5555, 6666, 8888, 9001, 1234)  # Porte comuni per C2
New-NetFirewallRule -DisplayName "Block C2 Outbound Ports" `
    -Direction Outbound -Protocol TCP -RemotePort $dangerousPorts `
    -Action Block -Profile Domain,Private,Public

# Bloccare SMB in uscita (prevenire lateral movement)
# ATTENZIONE: solo per workstation, non per server che necessitano SMB
New-NetFirewallRule -DisplayName "Block Outbound SMB" `
    -Direction Outbound -Protocol TCP -RemotePort 445 `
    -Action Block -Profile Domain `
    -RemoteAddress "!10.0.1.0/24"  # Permettere solo verso il file server

# Elencare le regole attive
Get-NetFirewallRule | Where-Object Enabled -eq True |
    Select-Object DisplayName, Direction, Action, Profile |
    Sort-Object Direction, DisplayName | Format-Table -AutoSize

# Esportare le regole per documentazione
Get-NetFirewallRule | Where-Object Enabled -eq True | ForEach-Object {
    $portFilter = Get-NetFirewallPortFilter -AssociatedNetFirewallRule $_
    $addrFilter = Get-NetFirewallAddressFilter -AssociatedNetFirewallRule $_
    [PSCustomObject]@{
        Name        = $_.DisplayName
        Direction   = $_.Direction
        Action      = $_.Action
        Protocol    = $portFilter.Protocol
        LocalPort   = $portFilter.LocalPort
        RemotePort  = $portFilter.RemotePort
        RemoteAddr  = $addrFilter.RemoteAddress
        Profile     = $_.Profile
    }
} | Export-Csv "C:\Reports\FirewallRules.csv" -NoTypeInformation
```

---

## LAPS Deployment

LAPS (Local Administrator Password Solution) gestisce automaticamente le password degli account amministratore locale sui computer del dominio, assicurando che ogni computer abbia una password unica, complessa e ruotata regolarmente. Questo previene il lateral movement attraverso password di admin locale identiche.

### Windows LAPS (Integrato da Windows Server 2022 e Windows 11)

```powershell
# Verificare il supporto LAPS nativo
Get-Command Get-LapsAADPassword, Get-LapsDiagnostics -ErrorAction SilentlyContinue

# Configurare LAPS tramite GPO
# Computer Configuration → Administrative Templates → System → LAPS:
#   - Configure password backup directory: Active Directory
#   - Password Settings:
#     - Password Complexity: Large + small + numbers + specials
#     - Password Length: 20
#     - Password Age: 30 days
#   - Name of administrator account to manage: (vuoto = default Administrator)

# Estendere lo schema AD per LAPS (se necessario per legacy LAPS)
Update-LapsADSchema

# Configurare i permessi sulle OU per LAPS
Set-LapsADComputerSelfPermission -Identity "OU=Workstations,DC=contoso,DC=com"

# Concedere il permesso di leggere le password LAPS
Set-LapsADReadPasswordPermission -Identity "OU=Workstations,DC=contoso,DC=com" `
    -AllowedPrincipals "CONTOSO\GRP-IT-Helpdesk"

# Recuperare la password LAPS di un computer
Get-LapsADPassword -Identity "WORKSTATION01" -AsPlainText

# Forzare la rotazione immediata della password
Reset-LapsPassword -Identity "WORKSTATION01"

# Audit: verificare chi ha letto le password LAPS
Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    ID = 4662
} -MaxEvents 100 | Where-Object {
    $_.Properties[8].Value -like "*ms-Mcs-AdmPwd*"
} | Select-Object TimeCreated,
    @{N='User';E={$_.Properties[1].Value}},
    @{N='Computer';E={$_.Properties[6].Value}}
```

---

## JEA — Just Enough Administration

JEA (Just Enough Administration) è un framework PowerShell che implementa il principio del minimo privilegio per l'amministrazione remota. Con JEA, gli utenti possono eseguire solo comandi specifici con privilegi elevati, senza ricevere l'accesso amministrativo completo al server.

```powershell
# Creare la struttura delle cartelle per JEA
$modulePath = "C:\Program Files\WindowsPowerShell\Modules\ContosoJEA"
New-Item -Path "$modulePath\RoleCapabilities" -ItemType Directory -Force

# Creare un Role Capability file (.psrc) — definisce cosa l'utente può fare
$roleCapParams = @{
    Path                = "$modulePath\RoleCapabilities\DNSAdmin.psrc"
    VisibleCmdlets      = @(
        "Get-DnsServer*"
        "Add-DnsServerResourceRecordA"
        "Add-DnsServerResourceRecordCName"
        "Remove-DnsServerResourceRecord"
        "Get-DnsServerZone"
        "Restart-Service -Name DNS"
    )
    VisibleFunctions    = @("Get-Date", "Write-Output")
    VisibleExternalCommands = @("nslookup.exe", "ipconfig.exe")
    VisibleProviders    = @("FileSystem")
    FunctionDefinitions = @(
        @{
            Name = "Get-DNSHealth"
            ScriptBlock = {
                $zones = Get-DnsServerZone
                foreach ($zone in $zones) {
                    [PSCustomObject]@{
                        Zone    = $zone.ZoneName
                        Type    = $zone.ZoneType
                        Records = (Get-DnsServerResourceRecord -ZoneName $zone.ZoneName).Count
                    }
                }
            }
        }
    )
}
New-PSRoleCapabilityFile @roleCapParams

# Creare un Session Configuration file (.pssc) — definisce chi può fare cosa
$sessConfigParams = @{
    Path                    = "$modulePath\ContosoJEA.pssc"
    SessionType             = "RestrictedRemoteServer"
    RunAsVirtualAccount     = $true  # Esegue come account virtuale con privilegi admin
    TranscriptDirectory     = "C:\JEATranscripts"
    RoleDefinitions         = @{
        "CONTOSO\GRP-DNS-Operators" = @{ RoleCapabilities = "DNSAdmin" }
    }
    LanguageMode            = "ConstrainedLanguage"
}
New-PSSessionConfigurationFile @sessConfigParams

# Registrare l'endpoint JEA
Register-PSSessionConfiguration -Name "ContosoJEA.DNSAdmin" `
    -Path "$modulePath\ContosoJEA.pssc" -Force

# Testare l'endpoint JEA
Enter-PSSession -ComputerName "DNS-SERVER01" -ConfigurationName "ContosoJEA.DNSAdmin"

# All'interno della sessione JEA:
# L'utente può eseguire solo i comandi definiti nel Role Capability
Get-DnsServerZone                                          # OK
Add-DnsServerResourceRecordA -Name "web" -ZoneName "contoso.com" -IPv4Address "10.0.1.50"  # OK
Restart-Computer                                            # BLOCCATO
Get-Process                                                 # BLOCCATO

# Verificare le trascrizioni JEA (audit completo)
Get-ChildItem "C:\JEATranscripts" -Recurse | Select-Object Name, LastWriteTime
```

---

## TLS Hardening — Configurazione Schannel

### Cipher Suite Ordering

L'ordine delle cipher suite determina quale algoritmo viene negoziato per primo. Prioritizzare le suite più sicure e moderne.

```powershell
# Visualizzare le cipher suite attualmente configurate
Get-TlsCipherSuite | Select-Object Name, CipherBlockLength,
    CipherLength, KeyExchangeAlgorithm, HashAlgorithm |
    Format-Table -AutoSize

# Configurare l'ordine delle cipher suite (TLS 1.2 e 1.3)
# Suite raccomandate in ordine di priorità:
$cipherSuites = @(
    # TLS 1.3 (preferite)
    "TLS_AES_256_GCM_SHA384"
    "TLS_AES_128_GCM_SHA256"
    "TLS_CHACHA20_POLY1305_SHA256"
    # TLS 1.2 (fallback)
    "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384"
    "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256"
    "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384"
    "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256"
    "TLS_DHE_RSA_WITH_AES_256_GCM_SHA384"
    "TLS_DHE_RSA_WITH_AES_128_GCM_SHA256"
)

# Disabilitare le suite non nella lista
Get-TlsCipherSuite | ForEach-Object {
    if ($_.Name -notin $cipherSuites) {
        Disable-TlsCipherSuite -Name $_.Name -ErrorAction SilentlyContinue
    }
}

# Abilitare e ordinare le suite desiderate
$priority = 0
foreach ($suite in $cipherSuites) {
    Enable-TlsCipherSuite -Name $suite -Position $priority -ErrorAction SilentlyContinue
    $priority++
}

# Configurare le curve ellittiche preferite
# Prioritizzare curve forti
$curves = @("NistP384", "NistP256", "curve25519")
Set-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Cryptography\Configuration\SSL\00010003" `
    -Name "EccCurves" -Value $curves -Type MultiString -ErrorAction SilentlyContinue
```

### Registry Keys Critiche per TLS

```powershell
# ═══════════════════════════════════════════════════════════
# CONFIGURAZIONE COMPLETA TLS VIA REGISTRY (Schannel)
# ═══════════════════════════════════════════════════════════

# Disabilitare protocolli obsoleti (SSL 2.0, SSL 3.0, TLS 1.0, TLS 1.1)
$disableProtocols = @("SSL 2.0", "SSL 3.0", "TLS 1.0", "TLS 1.1")
foreach ($proto in $disableProtocols) {
    foreach ($side in @("Server", "Client")) {
        $regPath = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\$proto\$side"
        New-Item -Path $regPath -Force | Out-Null
        New-ItemProperty -Path $regPath -Name "Enabled" -Value 0 -PropertyType DWord -Force
        New-ItemProperty -Path $regPath -Name "DisabledByDefault" -Value 1 -PropertyType DWord -Force
    }
}

# Abilitare esplicitamente TLS 1.2 e TLS 1.3
$enableProtocols = @("TLS 1.2", "TLS 1.3")
foreach ($proto in $enableProtocols) {
    foreach ($side in @("Server", "Client")) {
        $regPath = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\$proto\$side"
        New-Item -Path $regPath -Force | Out-Null
        New-ItemProperty -Path $regPath -Name "Enabled" -Value 1 -PropertyType DWord -Force
        New-ItemProperty -Path $regPath -Name "DisabledByDefault" -Value 0 -PropertyType DWord -Force
    }
}

# Disabilitare hash deboli
$disableHashes = @("MD5", "SHA")  # SHA = SHA-1
foreach ($hash in $disableHashes) {
    $regPath = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Hashes\$hash"
    New-Item -Path $regPath -Force | Out-Null
    New-ItemProperty -Path $regPath -Name "Enabled" -Value 0 -PropertyType DWord -Force
}

# Disabilitare key exchange deboli
$regPath = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\KeyExchangeAlgorithms\Diffie-Hellman"
New-Item -Path $regPath -Force | Out-Null
# Imporre DH key length minimo 2048 bit
New-ItemProperty -Path $regPath -Name "ServerMinKeyBitLength" -Value 2048 -PropertyType DWord -Force
New-ItemProperty -Path $regPath -Name "ClientMinKeyBitLength" -Value 2048 -PropertyType DWord -Force

# Disabilitare la rinegoziazione TLS non sicura
$regPath = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL"
New-ItemProperty -Path $regPath -Name "AllowInsecureRenegoClients" -Value 0 -PropertyType DWord -Force
New-ItemProperty -Path $regPath -Name "AllowInsecureRenegoServers" -Value 0 -PropertyType DWord -Force
```

### Verifica della Configurazione TLS

```powershell
# Verificare la configurazione TLS corrente
# Usare il cmdlet Test-NetConnection per una verifica rapida
Test-NetConnection -ComputerName "server.contoso.com" -Port 443

# Verificare le cipher suite supportate dal server (richiede openssl o nmap)
# Da un client Linux: nmap --script ssl-enum-ciphers -p 443 server.contoso.com

# Verificare via PowerShell quali protocolli sono abilitati
$regBase = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols"
Get-ChildItem $regBase -Recurse | ForEach-Object {
    $enabled = Get-ItemProperty $_.PSPath -Name "Enabled" -ErrorAction SilentlyContinue
    $disabled = Get-ItemProperty $_.PSPath -Name "DisabledByDefault" -ErrorAction SilentlyContinue
    if ($enabled -or $disabled) {
        [PSCustomObject]@{
            Path    = $_.PSPath -replace '.*Protocols\\',''
            Enabled = $enabled.Enabled
            DisabledByDefault = $disabled.DisabledByDefault
        }
    }
} | Format-Table -AutoSize

# Tool consigliato per audit TLS: IISCrypto (GUI)
# https://www.nartac.com/Products/IISCrypto
# Permette di configurare Schannel graficamente e genera un report
```

---

## Registry Hardening

### Chiavi di Registro Critiche per la Sicurezza

```powershell
# ═══════════════════════════════════════════════════════════
# REGISTRY HARDENING — Chiavi di sicurezza critiche
# ═══════════════════════════════════════════════════════════

# 1. Prevenire enumerazione anonima di account SAM e share
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "RestrictAnonymous" -Value 1 -Type DWord
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "RestrictAnonymousSAM" -Value 1 -Type DWord

# 2. Disabilitare autorun su tutti i drive
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer" `
    -Name "NoDriveTypeAutoRun" -Value 255 -Type DWord

# 3. Abilitare Safe DLL search mode
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager" `
    -Name "SafeDllSearchMode" -Value 1 -Type DWord

# 4. Disabilitare il caching delle credenziali (ridurre a 0-2 per server)
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" `
    -Name "CachedLogonsCount" -Value "2" -Type String

# 5. Prevenire il dump della memoria (crash dump disabilitato o limitato)
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\CrashControl" `
    -Name "CrashDumpEnabled" -Value 0 -Type DWord  # 0=None, 1=Complete, 2=Kernel, 3=Small

# 6. Configurare il banner legale pre-logon
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -Name "LegalNoticeCaption" -Value "AVVISO DI SICUREZZA" -Type String
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -Name "LegalNoticeText" -Value "Accesso autorizzato solo per personale autorizzato. Ogni attivita' e' monitorata e registrata." -Type String

# 7. Disabilitare la memorizzazione delle credenziali per RDP
Set-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\CredentialsDelegation" `
    -Name "AllowSavedCredentials" -Value 0 -Type DWord -Force
Set-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\CredentialsDelegation" `
    -Name "AllowSavedCredentialsWhenNTLMOnly" -Value 0 -Type DWord -Force

# 8. Prevenire elevazione automatica dei built-in Administrator
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -Name "FilterAdministratorToken" -Value 1 -Type DWord

# 9. UAC: richiedere sempre il consent prompt per gli admin
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -Name "ConsentPromptBehaviorAdmin" -Value 1 -Type DWord  # 1 = Prompt for credentials
Set-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -Name "EnableLUA" -Value 1 -Type DWord

# 10. Prevenire l'esecuzione di macro in Office (se installato)
New-Item "HKLM:\SOFTWARE\Policies\Microsoft\Office\16.0\Common\Security" -Force | Out-Null
Set-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Office\16.0\Common\Security" `
    -Name "DisableAllActiveX" -Value 1 -Type DWord
```

### ACL sul Registry

```powershell
# Verificare le ACL su chiavi di registro critiche
$criticalKeys = @(
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"
    "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
    "HKLM:\SYSTEM\CurrentControlSet\Services"
    "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa"
)

foreach ($key in $criticalKeys) {
    $acl = Get-Acl $key -ErrorAction SilentlyContinue
    $suspicious = $acl.Access | Where-Object {
        $_.IdentityReference -match "Everyone|Users|Authenticated Users" -and
        $_.RegistryRights -match "SetValue|CreateSubKey|FullControl"
    }
    if ($suspicious) {
        Write-Warning "ACL sospetta su: $key"
        $suspicious | Format-Table IdentityReference, RegistryRights, AccessControlType
    }
}

# Restringere le ACL sulle chiavi Run (prevenire persistence non autorizzata)
$runKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
$acl = Get-Acl $runKey
# Rimuovere permessi di scrittura per Users
$usersRule = $acl.Access | Where-Object {
    $_.IdentityReference -match "BUILTIN\\Users" -and
    $_.RegistryRights -match "SetValue"
}
if ($usersRule) {
    $acl.RemoveAccessRule($usersRule)
    Set-Acl $runKey $acl
}
```

### NtfsDisable8dot3NameCreation e Altre Ottimizzazioni

```powershell
# Disabilitare i nomi 8.3 (riduce dimensione MFT e previene enumerazione)
# 1 = disabilitare su tutti i volumi (2 = per-volume)
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
    -Name "NtfsDisable8dot3NameCreation" -Value 1 -Type DWord

# Disabilitare il timestamp di ultimo accesso (performance e riduzione I/O)
# Default su Server 2022: già disabilitato per volumi di sistema
fsutil behavior set disablelastaccess 1

# Abilitare long path support (se necessario per applicazioni)
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
    -Name "LongPathsEnabled" -Value 1 -Type DWord

# Prevenire l'accesso anonimo alla named pipe e share
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" `
    -Name "NullSessionPipes" -Value @() -Type MultiString
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" `
    -Name "NullSessionShares" -Value @() -Type MultiString
```

---

## Server Core e Nano Server

### Vantaggi di Sicurezza di Server Core

Server Core è l'installazione di Windows Server senza interfaccia grafica (GUI). Offre una superficie di attacco significativamente ridotta.

```
CONFRONTO SUPERFICIE DI ATTACCO
================================

Server Core           vs    Desktop Experience
─────────────────────────────────────────────────
~6 GB spazio disco          ~10+ GB spazio disco
~250 MB RAM in meno         GUI + framework
~50% meno aggiornamenti     Tutti gli aggiornamenti
No Internet Explorer        Internet Explorer
No Explorer.exe shell       Full shell
No .NET Framework GUI       WinForms, WPF
Meno servizi attivi         Più servizi attivi
Meno file binari            Più file binari
Meno CVE applicabili        Più CVE applicabili

Ruoli supportati su Server Core:
  AD DS, AD CS, DHCP, DNS, File Server, Hyper-V,
  IIS (senza GUI mgmt), Print Server, WSUS
```

### Gestione di Server Core

```powershell
# Gestione di Server Core — strumenti disponibili

# 1. PowerShell remoting (metodo principale)
Enter-PSSession -ComputerName SERVER-CORE01 -Credential (Get-Credential)

# 2. Windows Admin Center (WAC) — browser-based
# Installare WAC su un server di gestione con GUI
# Connettere al Server Core via browser

# 3. RSAT (Remote Server Administration Tools)
# Installare su workstation di management con GUI
Install-WindowsFeature RSAT-AD-Tools, RSAT-DNS-Server, RSAT-File-Services

# 4. sconfig.cmd — menu testuale di configurazione base
# Disponibile direttamente sulla console del Server Core
# Permette: nome computer, dominio, aggiornamenti, rete, RDP

# 5. Server Manager remoto
# Da un server Desktop Experience, aggiungere il Server Core come server gestito

# Verificare se l'installazione è Server Core
$installType = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion").InstallationType
if ($installType -eq "Server Core") {
    Write-Output "Installazione: Server Core"
} elseif ($installType -eq "Server") {
    Write-Output "Installazione: Desktop Experience"
}

# Convertire Desktop Experience → Server Core (Windows Server 2022)
# ATTENZIONE: operazione non facilmente reversibile
# Uninstall-WindowsFeature Server-Gui-Shell -Restart
```

### Nano Server — Uso e Limitazioni

Nano Server è disponibile solo come container base image a partire da Windows Server 2019. Non è più installabile come OS standalone.

```powershell
# Nano Server come container image (unico uso supportato)
# Pull dell'immagine
# docker pull mcr.microsoft.com/windows/nanoserver:ltsc2022

# Vantaggi come container base image:
# - Immagine ~260 MB (vs ~4 GB per Server Core container)
# - Superficie di attacco minimale
# - Avvio rapido
# - Ideale per microservizi .NET

# Limitazioni:
# - No PowerShell completo (solo PowerShell Core)
# - No MSI installer
# - No supporto 32-bit
# - No Active Directory roles
# - Non installabile come OS standalone
```

---

## Patch Management Hardening

### Sicurezza WSUS

WSUS (Windows Server Update Services) richiede hardening specifico poiché è un target di alto valore per gli attaccanti — un WSUS compromesso può distribuire aggiornamenti malevoli a tutti i client.

```powershell
# Hardening WSUS — Checklist critica

# 1. Usare HTTPS per la comunicazione client-WSUS
# Configurare SSL sul sito IIS di WSUS
# Forzare HTTPS via GPO:
# "Specify intranet Microsoft update service location"
# URL: https://wsus.contoso.com:8531

# 2. Limitare l'accesso alla console WSUS
# Solo gli admin WSUS devono poter accedere
# Verificare i membri del gruppo locale "WSUS Administrators"
Get-LocalGroupMember -Group "WSUS Administrators" -ErrorAction SilentlyContinue

# 3. Proteggere il database WSUS
# Se SQL Server esterno: connessione cifrata, account dedicato
# Se WID (Windows Internal Database): limitare l'accesso al file
$widPath = "C:\Windows\WID\Data"
if (Test-Path $widPath) {
    Get-Acl $widPath | Format-List
}

# 4. Firma digitale degli aggiornamenti
# WSUS firma automaticamente gli aggiornamenti Microsoft
# Per aggiornamenti di terze parti: configurare un certificato di firma
# GPO: "Allow signed updates from an intranet Microsoft update service location"

# 5. Proteggere la cartella dei contenuti WSUS
$wsusContentPath = "C:\WSUS\WsusContent"
if (Test-Path $wsusContentPath) {
    # Verificare che solo SYSTEM e WSUS admin abbiano accesso
    Get-Acl $wsusContentPath | Format-List
}

# 6. Monitorare l'integrità WSUS
# Controllare lo stato di sincronizzazione
Get-WsusServer | Get-WsusServerSynchronization | Select-Object LastSynchronizationTime, Result
```

### Windows Update for Business (WUfB)

```powershell
# WUfB permette di gestire gli aggiornamenti via cloud senza WSUS
# Configurazione via GPO o Intune

# GPO: Computer Configuration → Administrative Templates
#   → Windows Components → Windows Update → Windows Update for Business

# Deferral dei quality updates (security patches): max 30 giorni
# Deferral dei feature updates: max 365 giorni

# Configurazione ring-based via registry
# Ring 0 — Pilota (0 giorni di deferral)
Set-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" `
    -Name "DeferQualityUpdates" -Value 1 -Type DWord
Set-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" `
    -Name "DeferQualityUpdatesPeriodInDays" -Value 0 -Type DWord

# Ring 1 — Early Adopter (7 giorni)
# Ring 2 — Broad (14 giorni)
# Ring 3 — Critical Systems (21 giorni)
```

### Update Ring Strategy

```
STRATEGIA RING-BASED PER PATCH MANAGEMENT
==========================================

Ring 0 — PILOTA (5% dei server)
├── Server di test/staging non critici
├── Deferral: 0 giorni
├── Monitoraggio: 48-72 ore post-patch
└── Criterio avanzamento: nessun impatto funzionale

Ring 1 — EARLY ADOPTER (15% dei server)
├── Server di sviluppo, file server secondari
├── Deferral: 3-7 giorni
├── Monitoraggio: 72 ore post-patch
└── Criterio avanzamento: nessun incident P1/P2

Ring 2 — BROAD DEPLOYMENT (60% dei server)
├── Server applicativi, database non-critici
├── Deferral: 7-14 giorni
├── Monitoraggio: standard
└── Criterio avanzamento: compliance > 95%

Ring 3 — CRITICAL SYSTEMS (20% dei server)
├── Domain Controller, Exchange, SQL critici, CA
├── Deferral: 14-21 giorni
├── Maintenance window: fuori orario lavorativo
└── Criterio: rollback procedure testata

ECCEZIONE — ZERO-DAY
├── Skip ring → deployment immediato su tutti i ring
├── Rollback pronto prima del deployment
├── Comunicazione al management entro 1 ora
└── Post-mortem entro 24 ore
```

### Procedura di Rollback

```powershell
# Procedura di rollback aggiornamenti Windows

# 1. Identificare l'aggiornamento problematico
Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 10

# 2. Rimuovere un aggiornamento specifico
wusa /uninstall /kb:5025230 /quiet /norestart

# Alternativa PowerShell (Windows Server 2022+):
Remove-WindowsPackage -Online -PackageName "Package_for_KB5025230~..."

# 3. Bloccare la reinstallazione dell'aggiornamento
# Usare WSUS: declinare l'aggiornamento
# Usare WUfB: "Pause quality updates" via GPO

# 4. Verificare il rollback
Get-HotFix -Id KB5025230  # Non dovrebbe restituire risultati

# 5. Documentare l'incident
# - KB number
# - Sintomi osservati
# - Server impattati
# - Timestamp del rollback
# - Ticket di supporto Microsoft (se aperto)
```

---

## PowerShell Security

### Constrained Language Mode

Il Constrained Language Mode limita le funzionalità di PowerShell disponibili, impedendo l'uso di .NET arbitrario, COM objects e script block non firmati. È uno strumento critico per prevenire l'uso di PowerShell come attack tool.

```powershell
# Verificare il language mode corrente
$ExecutionContext.SessionState.LanguageMode

# Language modes disponibili:
# FullLanguage       = tutte le funzionalità (default)
# ConstrainedLanguage = solo cmdlet approvati, no .NET/COM arbitrario
# RestrictedLanguage = no script block, no variabili custom
# NoLanguage         = nessun codice PowerShell eseguibile

# WDAC abilita automaticamente Constrained Language Mode
# quando una policy CI è in enforcement mode
# Questa è la modalità raccomandata per abilitare CLM

# Alternativa: forzare CLM via variabile d'ambiente (meno sicuro, bypassabile)
# Solo per testing:
# [Environment]::SetEnvironmentVariable('__PSLockdownPolicy', '4', 'Machine')

# In Constrained Language Mode, questi comandi sono bloccati:
# [System.Net.WebClient]::new()        — download arbitrario
# Add-Type -TypeDefinition ...          — compilazione C# in-memory
# New-Object -ComObject ...             — accesso COM
# [Reflection.Assembly]::Load(...)      — caricamento assembly arbitrario

# Verificare il comportamento in CLM
if ($ExecutionContext.SessionState.LanguageMode -eq "ConstrainedLanguage") {
    Write-Output "CLM attivo — .NET arbitrario bloccato"
}
```

### Script Block Logging e Module Logging

```powershell
# Script Block Logging registra il contenuto completo di ogni script block
# eseguito da PowerShell, incluso il codice deoffuscato

# Abilitare Script Block Logging
$regPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging"
New-Item -Path $regPath -Force | Out-Null
Set-ItemProperty $regPath -Name "EnableScriptBlockLogging" -Value 1 -Type DWord
# Opzionale: loggare anche l'invocazione (molto verboso)
Set-ItemProperty $regPath -Name "EnableScriptBlockInvocationLogging" -Value 1 -Type DWord

# Module Logging registra l'input/output di cmdlet specifici
$regPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ModuleLogging"
New-Item -Path $regPath -Force | Out-Null
Set-ItemProperty $regPath -Name "EnableModuleLogging" -Value 1 -Type DWord

# Specificare i moduli da loggare (* = tutti)
$modulePath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ModuleLogging\ModuleNames"
New-Item -Path $modulePath -Force | Out-Null
Set-ItemProperty $modulePath -Name "*" -Value "*" -Type String

# Event ID correlati:
# 4103 = Module logging (input/output dei cmdlet)
# 4104 = Script Block Logging (contenuto dello script)

# Query degli eventi di Script Block Logging
Get-WinEvent -LogName "Microsoft-Windows-PowerShell/Operational" -MaxEvents 50 |
    Where-Object { $_.Id -eq 4104 } |
    Select-Object TimeCreated, @{N='ScriptBlock';E={$_.Properties[2].Value}} |
    Format-List
```

### Transcription

La trascrizione PowerShell registra tutto l'input e output di ogni sessione PowerShell in file di testo.

```powershell
# Abilitare la trascrizione PowerShell
$regPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\Transcription"
New-Item -Path $regPath -Force | Out-Null
Set-ItemProperty $regPath -Name "EnableTranscripting" -Value 1 -Type DWord
Set-ItemProperty $regPath -Name "OutputDirectory" -Value "C:\PSTranscripts" -Type String
Set-ItemProperty $regPath -Name "EnableInvocationHeader" -Value 1 -Type DWord

# Creare la directory per le trascrizioni
New-Item -Path "C:\PSTranscripts" -ItemType Directory -Force

# Limitare l'accesso alla directory delle trascrizioni
$acl = Get-Acl "C:\PSTranscripts"
$acl.SetAccessRuleProtection($true, $false)  # Disabilitare ereditarietà
$adminRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "BUILTIN\Administrators", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
$systemRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "NT AUTHORITY\SYSTEM", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
$acl.AddAccessRule($adminRule)
$acl.AddAccessRule($systemRule)
Set-Acl "C:\PSTranscripts" $acl

# Le trascrizioni catturano TUTTO: comandi digitati, output, errori
# Utili per: audit, forensics, compliance, formazione
# ATTENZIONE: possono contenere credenziali se inserite in chiaro
```

### JEA — Integrazione con PowerShell Security

JEA (Just Enough Administration) è il componente che completa la strategia di sicurezza PowerShell limitando i comandi disponibili per ogni ruolo. Vedere la sezione JEA dedicata per i dettagli implementativi.

```powershell
# Riepilogo della sicurezza PowerShell stratificata:
# Layer 1: Execution Policy (firma degli script)
# Layer 2: Constrained Language Mode via WDAC (blocco .NET/COM)
# Layer 3: Script Block Logging (audit di tutto il codice eseguito)
# Layer 4: Module Logging (audit input/output dei cmdlet)
# Layer 5: Transcription (registrazione completa delle sessioni)
# Layer 6: JEA (limitazione dei comandi per ruolo)

# Verificare la configurazione complessiva della sicurezza PowerShell
function Get-PSSecurityStatus {
    $status = [PSCustomObject]@{
        ExecutionPolicy = Get-ExecutionPolicy
        LanguageMode = $ExecutionContext.SessionState.LanguageMode
        ScriptBlockLogging = (Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" -Name EnableScriptBlockLogging -ErrorAction SilentlyContinue).EnableScriptBlockLogging
        ModuleLogging = (Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ModuleLogging" -Name EnableModuleLogging -ErrorAction SilentlyContinue).EnableModuleLogging
        Transcription = (Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\Transcription" -Name EnableTranscripting -ErrorAction SilentlyContinue).EnableTranscripting
        PSRemoting = (Test-WSMan -ErrorAction SilentlyContinue) -ne $null
    }
    $status
}
Get-PSSecurityStatus
```

---

## Sicurezza Fisica e di Avvio

### BitLocker per Server

BitLocker protegge i dati a riposo cifrando l'intero volume del disco. Su server, protegge dal furto fisico dei dischi e dall'accesso offline al file system.

```powershell
# Prerequisiti per BitLocker su server:
# - TPM 2.0 (raccomandato) o chiave USB per l'avvio
# - Feature BitLocker installata
Install-WindowsFeature BitLocker -IncludeManagementTools -Restart

# Verificare lo stato del TPM
Get-Tpm | Select-Object TpmPresent, TpmReady, TpmEnabled, TpmActivated, TpmOwned

# Abilitare BitLocker sul volume di sistema con TPM
Enable-BitLocker -MountPoint "C:" -EncryptionMethod XtsAes256 `
    -TpmProtector -UsedSpaceOnly

# Aggiungere un recovery password (OBBLIGATORIO — salvare in AD o archivio sicuro)
Add-BitLockerKeyProtector -MountPoint "C:" -RecoveryPasswordProtector

# Per volumi dati:
Enable-BitLocker -MountPoint "D:" -EncryptionMethod XtsAes256 `
    -RecoveryPasswordProtector -UsedSpaceOnly

# Salvare le chiavi di recovery in Active Directory
Backup-BitLockerKeyProtector -MountPoint "C:" `
    -KeyProtectorId (Get-BitLockerVolume -MountPoint "C:").KeyProtector[1].KeyProtectorId

# Verificare lo stato di BitLocker
Get-BitLockerVolume | Select-Object MountPoint, VolumeStatus,
    EncryptionMethod, EncryptionPercentage, ProtectionStatus,
    LockStatus | Format-Table

# GPO per BitLocker:
# Computer Configuration → Administrative Templates
#   → Windows Components → BitLocker Drive Encryption
# - "Store BitLocker recovery information in Active Directory": Enabled
# - "Choose drive encryption method and cipher strength": XTS-AES 256-bit
```

### Secure Boot e UEFI

```powershell
# Verificare che Secure Boot sia attivo
Confirm-SecureBootUEFI
# True = Secure Boot attivo

# Verificare la modalità di avvio (UEFI vs Legacy BIOS)
$env:firmware_type  # UEFI oppure BIOS
# Oppure:
bcdedit | Select-String "path"
# Se il path è \EFI\... → UEFI
# Se il path è \Windows\... → Legacy BIOS

# Secure Boot protegge contro:
# - Bootkit (malware che si installa nel bootloader)
# - Rootkit che si caricano prima del kernel
# - Modifica non autorizzata del bootloader
# - Avvio da supporti non autorizzati

# Configurazione UEFI (da BIOS setup):
# - Secure Boot: Enabled
# - Boot Mode: UEFI Only (disabilitare CSM/Legacy)
# - Set UEFI password (prevenire modifiche non autorizzate)
# - Disabilitare boot da USB/CD se non necessario
# - Disabilitare boot via rete (PXE) se non gestito
```

### Measured Boot e Device Guard

```powershell
# Measured Boot registra ogni componente di avvio nel TPM (PCR registers)
# permettendo la verifica remota dell'integrità del boot (attestation)

# Verificare lo stato di Virtualization Based Security (VBS)
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
    Select-Object AvailableSecurityProperties,
                  RequiredSecurityProperties,
                  SecurityServicesConfigured,
                  SecurityServicesRunning,
                  VirtualizationBasedSecurityStatus

# VirtualizationBasedSecurityStatus:
# 0 = Not configured
# 1 = Configured but not running
# 2 = Running

# SecurityServicesRunning:
# 1 = Credential Guard
# 2 = HVCI (Hypervisor-Protected Code Integrity)

# Abilitare HVCI (Hypervisor-Protected Code Integrity)
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity" `
    -Name "Enabled" -Value 1 -Type DWord

# Verificare la compatibilità hardware per Device Guard
# Usare il tool Device Guard and Credential Guard hardware readiness
# https://www.microsoft.com/en-us/download/details.aspx?id=53337
```

---

## Compliance Scanning e Automazione

### Security Compliance Toolkit (SCT)

Il Security Compliance Toolkit di Microsoft include GPO preconfigurate, script di analisi e strumenti per verificare la conformità alle baseline di sicurezza.

```powershell
# Download SCT:
# https://www.microsoft.com/en-us/download/details.aspx?id=55319

# Il pacchetto include:
# 1. GPO Backup per Windows Server 2022
# 2. LGPO.exe — applicazione locale delle policy
# 3. PolicyAnalyzer.exe — confronto tra policy
# 4. Documentazione delle impostazioni in Excel

# Usare Policy Analyzer per confrontare la configurazione corrente
# con la baseline Microsoft:
# 1. Avviare PolicyAnalyzer.exe
# 2. Importare la baseline GPO di Windows Server 2022
# 3. Importare la GPO corrente (esportata con gpresult o LGPO)
# 4. Confrontare e identificare le deviazioni

# Esportare la GPO corrente per confronto
gpresult /H "C:\Reports\GPOReport.html" /F
# Oppure in formato XML:
gpresult /X "C:\Reports\GPOReport.xml" /F

# Usare LGPO per applicare la baseline su un server standalone
.\LGPO.exe /g ".\Windows Server 2022 Security Baseline\GPOs"
```

### DSC per Compliance Continua

```powershell
# DSC può essere usato non solo per applicare configurazioni,
# ma per il monitoraggio continuo della conformità (compliance drift detection)

# Configurare il Local Configuration Manager (LCM) in modalità ApplyAndMonitor
[DSCLocalConfigurationManager()]
Configuration LCMConfig {
    Node "localhost" {
        Settings {
            ConfigurationMode = "ApplyAndMonitor"  # Applica e monitora drift
            # Alternative: ApplyOnly, ApplyAndAutoCorrect
            ConfigurationModeFrequencyMins = 30     # Verifica ogni 30 minuti
            RebootNodeIfNeeded = $false
            RefreshMode = "Push"
            StatusRetentionTimeInDays = 30
        }
    }
}

# ApplyAndAutoCorrect = auto-remediation del drift (più aggressivo)
# ApplyAndMonitor = segnala il drift senza correggere (consigliato in produzione)

# Verificare la conformità DSC
Test-DscConfiguration -Detailed |
    Select-Object ResourcesInDesiredState, ResourcesNotInDesiredState

# Report di compliance DSC dettagliato
Get-DscConfigurationStatus | Select-Object Status, StartDate,
    Type, RebootRequested, NumberOfResources
```

### Azure Policy e Microsoft Defender for Cloud

```powershell
# Per server hybrid (on-premises con connettività Azure):

# Azure Arc permette di gestire server on-premises da Azure
# Installare Azure Connected Machine Agent per:
# - Azure Policy compliance
# - Microsoft Defender for Cloud
# - Azure Monitor (log e metriche)
# - Azure Update Management

# Verificare lo stato di Azure Arc
azcmagent show

# Azure Policy per server include:
# - Audit di configurazioni non conformi
# - Remediation automatica
# - Compliance dashboard centralizzato
# - Integrazione con CIS Benchmark e NIST framework

# Microsoft Defender for Cloud fornisce:
# - Secure Score (postura di sicurezza)
# - Vulnerability assessment
# - Raccomandazioni di hardening
# - Rilevamento minacce (Defender for Servers)
```

---

## Hardening Checklist Completa

```
HARDENING CHECKLIST — Windows Server 2022
==========================================

[ ] Installazione e Configurazione Base
    [ ] Installazione Server Core (quando possibile)
    [ ] Aggiornamenti di sicurezza installati (patch mensili)
    [ ] Antivirus/EDR attivo e aggiornato
    [ ] Dischi cifrati con BitLocker (se supportato)

[ ] Account e Autenticazione
    [ ] Account Administrator rinominato
    [ ] Account Guest disabilitato
    [ ] Password policy conforme (>14 char, complessità)
    [ ] Account lockout configurato (5 tentativi, 30 min)
    [ ] LAPS deployato per admin locale
    [ ] Service account con gMSA dove possibile
    [ ] Credential Guard abilitato (se supportato)
    [ ] LSA Protection (RunAsPPL) abilitato
    [ ] WDigest disabilitato

[ ] Rete e Protocolli
    [ ] SMBv1 rimosso
    [ ] SMB signing richiesto
    [ ] LLMNR disabilitato
    [ ] NBT-NS disabilitato
    [ ] mDNS disabilitato
    [ ] WPAD disabilitato
    [ ] TLS 1.0/1.1 disabilitati
    [ ] Cipher suite deboli rimosse
    [ ] Windows Firewall attivo su tutti i profili
    [ ] Regole firewall minime (default deny inbound)

[ ] Servizi e Funzionalità
    [ ] Servizi non necessari disabilitati
    [ ] Ruoli non necessari rimossi
    [ ] Remote Desktop limitato a subnet di management
    [ ] PowerShell remoting limitato (JEA dove possibile)
    [ ] Accesso anonimo/null session bloccato

[ ] Audit e Monitoraggio
    [ ] Advanced Audit Policy configurato
    [ ] Process creation audit con command line
    [ ] PowerShell Script Block Logging abilitato
    [ ] Log dimensionati adeguatamente
    [ ] Event forwarding a SIEM configurato
    [ ] Sysmon installato e configurato

[ ] Gestione Aggiornamenti
    [ ] WSUS o WUfB configurato
    [ ] Aggiornamenti automatici per patch critiche
    [ ] Finestra di manutenzione definita
```

---

## Best Practices

**Adottare Server Core dove possibile:** Server Core ha una superficie di attacco significativamente ridotta rispetto a Desktop Experience. Meno file binari, meno servizi, meno vettori di attacco. Gestire con PowerShell remoting, Windows Admin Center e RSAT.

**Applicare il principio del minimo privilegio ovunque:** Nessun utente dovrebbe avere più permessi di quelli strettamente necessari per il proprio ruolo. Utilizzare JEA per l'amministrazione remota, LAPS per l'admin locale, gMSA per i service account.

**Hardening in layers (defense in depth):** Non affidarsi a un singolo controllo di sicurezza. Combinare firewall + audit + credential protection + network segmentation + endpoint protection per creare difese in profondità.

**Testare ogni modifica in un ambiente non-produzione:** Le configurazioni di hardening possono interrompere applicazioni e servizi. Validare sempre in laboratorio prima del deployment in produzione.

**Documentare tutte le eccezioni:** Ogni deviazione dalla baseline di sicurezza deve essere documentata con una giustificazione tecnica, approvata dal responsabile della sicurezza e sottoposta a revisione periodica.

**Automatizzare l'hardening:** Utilizzare script PowerShell, GPO e Desired State Configuration (DSC) per applicare e verificare le configurazioni di hardening in modo consistente e ripetibile su tutti i server.

---

## Troubleshooting

### Problema: Servizio o Applicazione Non Funziona Dopo l'Hardening

**Sintomi**: Un'applicazione aziendale smette di funzionare dopo l'applicazione delle policy di hardening. L'applicazione potrebbe non avviarsi, non riuscire ad autenticarsi o perdere la connettività.

**Causa**: L'hardening ha disabilitato un protocollo, un servizio o una porta di rete utilizzata dall'applicazione. Esempi comuni: applicazioni legacy che richiedono SMBv1, TLS 1.0 o NTLM.

**Soluzione**:

```powershell
# 1. Identificare cosa è cambiato (comparare con la baseline pre-hardening)
# 2. Controllare i log dell'applicazione
# 3. Monitorare le connessioni di rete bloccate
Get-WinEvent -LogName "Microsoft-Windows-Windows Firewall With Advanced Security/Firewall" `
    -MaxEvents 100 | Where-Object { $_.Id -eq 5157 } |
    Select-Object TimeCreated, Message

# 4. Verificare se l'applicazione utilizza protocolli disabilitati
# Per TLS: abilitare il logging SChannel
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL" `
    -Name "EventLogging" -Value 7 -Type DWord
# Controllare: Event Viewer → System → Source: SChannel

# 5. Creare un'eccezione documentata se necessario
# (non revocare l'intero hardening per una singola applicazione)
```

### Problema: Lockout Frequenti degli Account Dopo Audit Policy

**Sintomi**: Dopo l'abilitazione dell'advanced audit policy, gli utenti vengono bloccati frequentemente nonostante inseriscano la password corretta.

**Causa**: Le applicazioni o i servizi che utilizzano credenziali cached o stored credentials tentano autenticazioni con password obsolete, generando failure che raggiungono il lockout threshold.

**Soluzione**:

```powershell
# Identificare la sorgente dei lockout
Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4740} -MaxEvents 20 |
    Select-Object TimeCreated,
        @{N='Account';E={$_.Properties[0].Value}},
        @{N='CallerComputer';E={$_.Properties[1].Value}} |
    Format-Table

# Utilizzare Account Lockout Tools di Microsoft
# https://www.microsoft.com/en-us/download/details.aspx?id=18465
# LockoutStatus.exe mostra lo stato lockout su tutti i DC

# Trovare le credenziali cached sul computer sorgente
cmdkey /list  # Sul computer dell'utente
# Rimuovere credenziali obsolete
cmdkey /delete:target_name
```

### Tabella Problemi Comuni — Riferimento Rapido

| # | Problema | Causa | Soluzione |
|---|----------|-------|-----------|
| 1 | Applicazione non funziona dopo hardening | L'hardening ha disabilitato un protocollo/servizio/porta necessari (SMBv1, TLS 1.0, NTLM) | Abilitare SChannel logging (`EventLogging=7`), verificare firewall log (Event ID 5157), creare eccezione documentata per il singolo protocollo necessario — non revocare l'intero hardening |
| 2 | Lockout frequenti dopo audit policy | Credenziali cached/stored obsolete nei servizi e applicazioni raggiungono il lockout threshold | `Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4740}` per trovare la sorgente; `cmdkey /list` e `/delete` sul computer sorgente; verificare scheduled task e servizi con credenziali hard-coded |
| 3 | Credential Guard blocca applicazioni | App legacy usano NTLM, CredSSP o delega non vincolata incompatibili con Credential Guard | Verificare `Win32_DeviceGuard` per stato CG; testare l'app senza CG in lab; se necessario usare Remote Credential Guard come alternativa; documentare eccezione |
| 4 | WDAC blocca software legittimo in enforcement mode | La policy non include il publisher o hash del software | Analizzare Event ID 3077 (blocked) nel log CodeIntegrity; creare supplementary policy con `New-CIPolicy -ScanPath`; testare in audit (Event ID 3076) prima di ri-applicare enforcement |
| 5 | AppLocker non blocca nulla nonostante le regole | Il servizio AppIDSvc non è in esecuzione o le regole sono in Audit mode | `Get-Service AppIDSvc` → deve essere Running e StartupType Automatic; verificare enforcement mode nelle proprietà di ogni rule collection |
| 6 | SMB signing causa rallentamenti significativi | L'overhead della firma SMB su hardware datato o rete ad alta latenza | SMB signing aggiunge ~10-15% overhead; verificare che la NIC supporti offloading; considerare SMB encryption (che include signing) su hardware moderno; non disabilitare signing — è una mitigazione critica contro relay |
| 7 | TLS 1.0/1.1 disabilitati rompono applicazione legacy | L'applicazione non supporta TLS 1.2+ | Verificare con SChannel log quale protocollo richiede; aggiornare l'applicazione; se impossibile, riabilitare TLS 1.0/1.1 SOLO per quella porta/applicazione via registry, documentare eccezione con scadenza |
| 8 | Sysmon genera troppo volume di log | Configurazione Sysmon troppo verbosa, Event ID 7 (Image Loaded) non filtrato | Usare la configurazione SwiftOnSecurity come base (filtra noise); escludere processi noti dal logging; aumentare dimensione log; verificare che WEF non forwardi eventi non necessari |
| 9 | WEF non riceve eventi dai server source | Firewall blocca WinRM (5985/5986) o permessi insufficienti | `winrm quickconfig` sul source; verificare firewall tra source e collector; account del source deve essere nel gruppo "Event Log Readers" del collector; `wecutil gr <subscription>` per diagnostica |
| 10 | PowerShell Constrained Language Mode blocca script di gestione | Script di automazione usa .NET o COM non consentiti in CLM | Firmare gli script con un certificato trusted dalla policy WDAC; usare cmdlet nativi invece di chiamate .NET; creare un JEA endpoint con FullLanguage per gli admin autorizzati |
| 11 | Protected Users: account non riesce ad autenticarsi | NTLM necessario per risorsa specifica, ma Protected Users blocca NTLM | Verificare quale risorsa richiede NTLM con `Get-WinEvent` (Event ID 4776); configurare la risorsa per Kerberos; se impossibile, rimuovere l'account da Protected Users e applicare mitigazioni alternative |
| 12 | BitLocker: server non si avvia dopo aggiornamento firmware | L'aggiornamento firmware ha cambiato i valori PCR nel TPM | Usare la recovery key per sbloccare; dopo l'avvio, sospendere BitLocker (`Suspend-BitLocker`), aggiornare il firmware, riprendere BitLocker (`Resume-BitLocker`); salvare sempre la recovery key in AD |
| 13 | GPO di hardening non si applica su alcuni server | WMI filter esclude il server, security filtering non include il computer account, link order errato | `gpresult /H report.html` sul server; verificare WMI filter con `gwmi -Query`; verificare che il computer account sia nel security filtering della GPO; verificare link order e block inheritance |
| 14 | ASR rule blocca operazione legittima di Office | La regola ASR è troppo aggressiva per il workflow aziendale | Identificare il GUID della regola ASR dal log Defender (Event ID 1121); impostare la regola in modalità Audit (`Actions = 2`) invece di Block; creare un'esclusione per il processo specifico se necessario |
| 15 | Compliance scan mostra drift dopo poche ore | Un processo o script sovrascrive le impostazioni di hardening | Identificare il processo che modifica il registry con Sysmon (Event ID 13); verificare GPO conflittuali con `gpresult /z`; usare DSC in modalità `ApplyAndAutoCorrect` per auto-remediation; indagare se malware sta disabilitando le protezioni |
| 16 | LSA Protection (RunAsPPL) blocca driver di autenticazione | Driver di terze parti (smart card, biometrico) non firmato come PPL | Verificare il log LSA per driver bloccati; il driver deve essere firmato con certificato WHQL per funzionare con PPL; contattare il vendor per un driver aggiornato; in extremis, disabilitare RunAsPPL e documentare eccezione |
| 17 | Server Core: impossibile installare ruolo necessario | Il ruolo richiede la GUI (feature `Server-Gui-Shell`) | Verificare ruoli supportati su Server Core (`Get-WindowsFeature`); per ruoli che richiedono GUI, usare Desktop Experience su quel server specifico e documentare l'eccezione; gestire con RSAT/WAC da remoto |
| 18 | NTLM audit mostra migliaia di eventi, impossibile eliminare NTLM | Troppe applicazioni e servizi usano NTLM nel dominio | Approccio progressivo: categorizzare per server, eliminare NTLM un server alla volta; usare le eccezioni GPO per server che necessitano ancora NTLM; obiettivo: riduzione incrementale, non eliminazione totale in una volta |

---

## AppLocker e WDAC — Application Whitelisting

### AppLocker

AppLocker è la tecnologia di application whitelisting integrata in Windows che permette di controllare quali eseguibili, script, installer e DLL possono essere eseguiti nel sistema. A differenza del vecchio Software Restriction Policies (SRP), AppLocker supporta regole basate su publisher (firma digitale), path e hash del file, con la possibilità di applicare regole diverse per gruppi di utenti.

```powershell
# Verificare lo stato del servizio AppIDSvc (necessario per AppLocker)
Get-Service AppIDSvc | Select-Object Name, Status, StartType
# Il servizio deve essere in esecuzione e impostato su Automatic
Set-Service AppIDSvc -StartupType Automatic
Start-Service AppIDSvc

# Creare le regole di default tramite PowerShell
# Le regole di default permettono tutto il software nelle cartelle Windows e Program Files
# e permettono agli admin di eseguire qualsiasi cosa
Get-AppLockerPolicy -Effective | Select-Object -ExpandProperty RuleCollections

# Generare regole di default per gli eseguibili
$defaultRules = Get-AppLockerPolicy -Local
Set-AppLockerPolicy -PolicyObject $defaultRules -Merge

# Creare una regola publisher per permettere solo software firmato da Microsoft
$condition = New-AppLockerPolicyCondition -Publisher `
    -ProductName "*" -BinaryName "*" `
    -PublisherName "O=MICROSOFT CORPORATION, L=REDMOND, S=WASHINGTON, C=US" `
    -LowSection "*" -HighSection "*"

# Esportare la policy AppLocker corrente per analisi
Get-AppLockerPolicy -Effective -Xml | Out-File "C:\Reports\AppLockerPolicy.xml"

# Modalità Audit: registra le violazioni senza bloccare
# Computer Configuration → Windows Settings → Security Settings
#   → Application Control Policies → AppLocker
#   → Configure rule enforcement → Executable rules: Audit only

# Analizzare i log di AppLocker (Event ID 8003 = blocked, 8004 = allowed audit)
Get-WinEvent -LogName "Microsoft-Windows-AppLocker/EXE and DLL" -MaxEvents 100 |
    Where-Object { $_.Id -eq 8004 } |
    Select-Object TimeCreated, Message | Format-Table -Wrap

# Regole per bloccare l'esecuzione da cartelle utente (prevenire ransomware)
# Bloccare esecuzione da %USERPROFILE%, %APPDATA%, %TEMP%
$blockPaths = @(
    "%OSDRIVE%\Users\*\AppData\*"
    "%OSDRIVE%\Users\*\Downloads\*"
    "%WINDIR%\Temp\*"
    "%TEMP%\*"
)
foreach ($path in $blockPaths) {
    Write-Output "Regola da creare: Deny all users - Path: $path"
}
```

### Windows Defender Application Control (WDAC)

WDAC (precedentemente Device Guard Code Integrity) è la tecnologia di nuova generazione per il controllo delle applicazioni, più robusta di AppLocker perché opera a livello di kernel tramite Virtualization Based Security (VBS). WDAC non può essere bypassato nemmeno da processi con privilegi SYSTEM, rendendolo significativamente più sicuro di AppLocker.

```powershell
# Creare una policy WDAC di base (scan del sistema corrente come reference)
New-CIPolicy -Level Publisher -Fallback Hash `
    -FilePath "C:\Policies\BasePolicy.xml" `
    -UserPEs -MultiplePolicyFormat

# Creare una policy supplementare per software aggiuntivo
$scanPath = "C:\Program Files\CustomApp"
New-CIPolicy -Level Publisher -Fallback Hash `
    -ScanPath $scanPath `
    -FilePath "C:\Policies\CustomApp-Supplement.xml" `
    -UserPEs -MultiplePolicyFormat

# Convertire la policy XML in formato binario
ConvertFrom-CIPolicy -XmlFilePath "C:\Policies\BasePolicy.xml" `
    -BinaryFilePath "C:\Policies\BasePolicy.cip"

# Deployare la policy in modalità audit (prima di enforcement)
# Nella policy XML, assicurarsi che sia presente:
# <Rule><Option>Enabled:Audit Mode</Option></Rule>

# Copiare la policy nella posizione di enforcement
Copy-Item "C:\Policies\BasePolicy.cip" `
    "C:\Windows\System32\CodeIntegrity\CiPolicies\Active\"

# Verificare lo stato WDAC
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
    Select-Object UsermodeCodeIntegrityPolicyEnforcementStatus,
                  CodeIntegrityPolicyEnforcementStatus
# 0 = Off, 1 = Audit, 2 = Enforced

# Analizzare gli eventi WDAC (Event ID 3076 = audit block, 3077 = enforced block)
Get-WinEvent -LogName "Microsoft-Windows-CodeIntegrity/Operational" -MaxEvents 50 |
    Where-Object { $_.Id -in @(3076, 3077) } |
    Select-Object TimeCreated, Id, Message
```

---

## Windows Defender — Funzionalità di Protezione Avanzata

### WDAC — Windows Defender Application Control

WDAC è la tecnologia di application control più robusta di Windows, operando a livello kernel tramite VBS. A differenza di AppLocker, WDAC non può essere bypassato da processi SYSTEM.

```powershell
# Strategia di deployment WDAC raccomandata:
# 1. Creare policy da un sistema di riferimento (golden image)
# 2. Deployare in audit mode
# 3. Analizzare gli eventi di blocco
# 4. Raffinare la policy con supplementary policies
# 5. Passare a enforcement mode

# Step 1: scan del sistema di riferimento
New-CIPolicy -Level Publisher -Fallback Hash `
    -FilePath "C:\Policies\GoldenImage.xml" `
    -UserPEs -MultiplePolicyFormat

# Step 2: abilitare audit mode (già default nella policy generata)
# Verificare che <Rule> contenga <Option>Enabled:Audit Mode</Option>

# Step 3: dopo il deployment, analizzare gli eventi
Get-WinEvent -LogName "Microsoft-Windows-CodeIntegrity/Operational" -MaxEvents 200 |
    Where-Object { $_.Id -in @(3076, 3077) } |
    Select-Object TimeCreated, Id,
        @{N='File';E={($_.Message -split "`n" | Select-String "file name").ToString().Trim()}} |
    Format-Table -AutoSize

# Step 4: creare supplementary policy per il software non coperto
New-CIPolicy -Level Publisher -Fallback Hash `
    -ScanPath "C:\Program Files\CustomApp" `
    -FilePath "C:\Policies\CustomApp-Supplement.xml" `
    -UserPEs -MultiplePolicyFormat

# Impostare come supplementary (non standalone)
Set-CIPolicyIdInfo -FilePath "C:\Policies\CustomApp-Supplement.xml" `
    -BasePolicyToSupplementPath "C:\Policies\GoldenImage.xml"

# Step 5: rimuovere audit mode e passare a enforcement
Set-RuleOption -FilePath "C:\Policies\GoldenImage.xml" -Option 3 -Delete
# Option 3 = "Enabled:Audit Mode" → rimuoverlo = enforcement

# Convertire e deployare
ConvertFrom-CIPolicy -XmlFilePath "C:\Policies\GoldenImage.xml" `
    -BinaryFilePath "C:\Policies\GoldenImage.cip"
Copy-Item "C:\Policies\GoldenImage.cip" `
    "C:\Windows\System32\CodeIntegrity\CiPolicies\Active\"
```

### AppLocker — Confronto e Coesistenza con WDAC

| Caratteristica | AppLocker | WDAC |
|---|---|---|
| Livello di enforcement | User mode | Kernel mode (VBS) |
| Bypassabile da SYSTEM | Sì | No |
| Granularità per utente/gruppo | Sì | No (per-machine) |
| Supporto Server Core | Sì | Sì |
| Facilità di gestione | Media (GPO) | Complessa (XML/PowerShell) |
| Supplementary policies | No | Sì (multi-policy) |
| Managed Installer | No | Sì |
| Raccomandazione | Ambienti misti, regole per-utente | Massima sicurezza, server dedicati |

La coesistenza è possibile: AppLocker per regole per-utente, WDAC per enforcement a livello di sistema.

### ASR — Attack Surface Reduction Rules

Le ASR rules sono regole comportamentali integrate in Microsoft Defender che bloccano tecniche di attacco specifiche (macro Office malicious, process injection, credential stealing).

```powershell
# Elencare tutte le ASR rules disponibili
Get-MpPreference | Select-Object -ExpandProperty AttackSurfaceReductionRules_Ids

# ASR Rules critiche per server (GUID → descrizione):
$asrRules = @{
    "56a863a9-875e-4185-98a7-b882c64b5ce5" = "Block abuse of exploited vulnerable signed drivers"
    "7674ba52-37eb-4a4f-a9a1-f0f9a1619a2c" = "Block Adobe Reader from creating child processes"
    "d4f940ab-401b-4efc-aadc-ad5f3c50688a" = "Block all Office applications from creating child processes"
    "9e6c4e1f-7d60-472f-ba1a-a39ef669e4b2" = "Block credential stealing from LSASS"
    "be9ba2d9-53ea-4cdc-84e5-9b1eeee46550" = "Block executable content from email client and webmail"
    "01443614-cd74-433a-b99e-2ecdc07bfc25" = "Block executable files from running unless they meet criteria"
    "d3e037e1-3eb8-44c8-a917-57927947596d" = "Block JavaScript or VBScript from launching downloaded content"
    "75668c1f-73b5-4cf0-bb93-3ecf5cb7cc84" = "Block Office applications from injecting code into processes"
    "26190899-1602-49e8-8b27-eb1d0a1ce869" = "Block Office communication application from creating child processes"
    "e6db77e5-3df2-4cf1-b95a-636979351e5b" = "Block persistence through WMI event subscription"
    "b2b3f03d-6a65-4f7b-a9c7-1c7ef74a9ba4" = "Block untrusted and unsigned processes that run from USB"
    "92e97fa1-2edf-4476-bdd6-9dd0b4dddc7b" = "Block Win32 API calls from Office macros"
    "c1db55ab-c21a-4637-bb3f-a12568109d35" = "Use advanced protection against ransomware"
}

# Abilitare le ASR rules in modalità audit (2 = Audit, 1 = Block, 0 = Off)
foreach ($ruleId in $asrRules.Keys) {
    Add-MpPreference -AttackSurfaceReductionRules_Ids $ruleId `
        -AttackSurfaceReductionRules_Actions 2  # Audit first
}

# Dopo il periodo di audit, passare a Block
foreach ($ruleId in $asrRules.Keys) {
    Add-MpPreference -AttackSurfaceReductionRules_Ids $ruleId `
        -AttackSurfaceReductionRules_Actions 1  # Block
}

# Verificare lo stato delle ASR rules
Get-MpPreference | Select-Object `
    AttackSurfaceReductionRules_Ids,
    AttackSurfaceReductionRules_Actions

# Monitorare eventi ASR (Event ID 1121 = blocked, 1122 = audit)
Get-WinEvent -LogName "Microsoft-Windows-Windows Defender/Operational" -MaxEvents 100 |
    Where-Object { $_.Id -in @(1121, 1122) } |
    Select-Object TimeCreated, Id, Message
```

### Controlled Folder Access

Controlled Folder Access protegge le cartelle critiche da modifiche non autorizzate (ransomware protection).

```powershell
# Abilitare Controlled Folder Access
Set-MpPreference -EnableControlledFolderAccess Enabled
# Modalità: Enabled, Disabled, AuditMode

# Cartelle protette di default: Documenti, Desktop, Immagini, Video, Musica, Preferiti
# Aggiungere cartelle personalizzate
Add-MpPreference -ControlledFolderAccessProtectedFolders "D:\CriticalData"
Add-MpPreference -ControlledFolderAccessProtectedFolders "E:\Shares\Finance"

# Aggiungere applicazioni autorizzate (whitelist)
Add-MpPreference -ControlledFolderAccessAllowedApplications "C:\Program Files\CustomApp\app.exe"

# Verificare la configurazione
Get-MpPreference | Select-Object `
    EnableControlledFolderAccess,
    ControlledFolderAccessProtectedFolders,
    ControlledFolderAccessAllowedApplications
```

### Exploit Protection

Exploit Protection è il successore di EMET (Enhanced Mitigation Experience Toolkit) e fornisce mitigazioni a livello di sistema e per-applicazione contro tecniche di exploit comuni.

```powershell
# Configurazioni di sistema (process-level mitigations)
# Abilitare DEP (Data Execution Prevention) per tutti i processi
Set-ProcessMitigation -System -Enable DEP

# Abilitare ASLR (Address Space Layout Randomization) forzato
Set-ProcessMitigation -System -Enable ForceRelocateImages

# Abilitare CFG (Control Flow Guard) di sistema
Set-ProcessMitigation -System -Enable CFG

# Per-process mitigations (esempio: proteggere PowerShell)
Set-ProcessMitigation -Name "powershell.exe" `
    -Enable DEP, EmulateAtlThunks, BottomUp, HighEntropy, StrictHandle

# Esportare la configurazione corrente per documentazione
Get-ProcessMitigation -System | Format-List
Get-ProcessMitigation -Name "powershell.exe" | Format-List

# Esportare in XML per deployment via GPO
Get-ProcessMitigation -RegistryConfigFilePath "C:\Policies\ExploitProtection.xml"
# Importare su altri server:
# Set-ProcessMitigation -PolicyFilePath "C:\Policies\ExploitProtection.xml"
```

---

## Desired State Configuration (DSC) per Hardening Automatizzato

DSC (Desired State Configuration) è il framework dichiarativo di PowerShell per automatizzare la configurazione e il mantenimento dello stato desiderato dei server. Applicato all'hardening, DSC garantisce che le configurazioni di sicurezza rimangano consistenti nel tempo e siano automaticamente ripristinate in caso di drift.

```powershell
# Esempio di configurazione DSC per hardening di base
Configuration ServerHardening {
    param (
        [string[]]$ComputerName = "localhost"
    )

    Import-DscResource -ModuleName PSDesiredStateConfiguration
    Import-DscResource -ModuleName SecurityPolicyDsc
    Import-DscResource -ModuleName AuditPolicyDsc

    Node $ComputerName {
        # Disabilitare servizi non necessari
        Service DisableRemoteRegistry {
            Name        = "RemoteRegistry"
            State       = "Stopped"
            StartupType = "Disabled"
        }

        Service DisableFax {
            Name        = "Fax"
            State       = "Stopped"
            StartupType = "Disabled"
        }

        Service DisableBrowser {
            Name        = "Browser"
            State       = "Stopped"
            StartupType = "Disabled"
        }

        # Configurare la password policy
        AccountPolicy PasswordPolicy {
            Name                                        = "PasswordPolicy"
            Enforce_password_history                     = 24
            Maximum_Password_Age                         = 365
            Minimum_Password_Age                         = 1
            Minimum_Password_Length                       = 14
            Password_must_meet_complexity_requirements    = "Enabled"
            Store_passwords_using_reversible_encryption   = "Disabled"
        }

        # Configurare l'account lockout
        AccountPolicy LockoutPolicy {
            Name                                  = "LockoutPolicy"
            Account_lockout_duration               = 30
            Account_lockout_threshold              = 5
            Reset_account_lockout_counter_after     = 30
        }

        # Registry key per disabilitare SMBv1
        Registry DisableSMBv1 {
            Ensure    = "Present"
            Key       = "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters"
            ValueName = "SMB1"
            ValueData = "0"
            ValueType = "DWord"
        }

        # Registry key per disabilitare LLMNR
        Registry DisableLLMNR {
            Ensure    = "Present"
            Key       = "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient"
            ValueName = "EnableMulticast"
            ValueData = "0"
            ValueType = "DWord"
        }

        # Registry key per LSA Protection
        Registry EnableLSAProtection {
            Ensure    = "Present"
            Key       = "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Lsa"
            ValueName = "RunAsPPL"
            ValueData = "1"
            ValueType = "DWord"
        }

        # Registry key per disabilitare WDigest
        Registry DisableWDigest {
            Ensure    = "Present"
            Key       = "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\SecurityProviders\WDigest"
            ValueName = "UseLogonCredential"
            ValueData = "0"
            ValueType = "DWord"
        }

        # Abilitare il PowerShell Script Block Logging
        Registry EnableScriptBlockLogging {
            Ensure    = "Present"
            Key       = "HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging"
            ValueName = "EnableScriptBlockLogging"
            ValueData = "1"
            ValueType = "DWord"
        }

        # Audit Policy per Process Creation
        AuditPolicySubcategory ProcessCreation {
            Name      = "Process Creation"
            AuditFlag = "Success"
            Ensure    = "Present"
        }

        # Audit Policy per Logon
        AuditPolicySubcategory Logon {
            Name      = "Logon"
            AuditFlag = "SuccessAndFailure"
            Ensure    = "Present"
        }

        # Verificare che il firewall sia attivo su tutti i profili
        Script EnableFirewall {
            GetScript  = { @{ Result = (Get-NetFirewallProfile).Enabled -join "," } }
            SetScript  = { Set-NetFirewallProfile -Profile Domain,Private,Public -Enabled True }
            TestScript = {
                $profiles = Get-NetFirewallProfile
                ($profiles | Where-Object { $_.Enabled -eq $false }).Count -eq 0
            }
        }
    }
}

# Compilare la configurazione
ServerHardening -OutputPath "C:\DSC\ServerHardening"

# Applicare la configurazione
Start-DscConfiguration -Path "C:\DSC\ServerHardening" -Wait -Verbose -Force

# Verificare la conformità
Test-DscConfiguration -Detailed | Format-List ResourcesInDesiredState, ResourcesNotInDesiredState

# Configurare il DSC Pull Server o Azure Automation DSC
# per il monitoraggio centralizzato della conformità
```

### Script di Compliance Check Automatizzato

```powershell
function Test-ServerHardening {
    <#
    .SYNOPSIS
        Verifica la conformità di un server alle baseline di hardening.
    .DESCRIPTION
        Esegue una serie di controlli automatizzati e genera un report
        con lo stato di conformità per ogni controllo.
    #>
    param (
        [string]$ComputerName = $env:COMPUTERNAME,
        [string]$ReportPath = "C:\Reports\HardeningReport-$(Get-Date -Format 'yyyyMMdd').html"
    )

    $results = @()

    # Check SMBv1
    $smb1 = Get-SmbServerConfiguration | Select-Object -ExpandProperty EnableSMB1Protocol
    $results += [PSCustomObject]@{
        Check  = "SMBv1 Disabilitato"
        Status = if (-not $smb1) { "PASS" } else { "FAIL" }
        Detail = "EnableSMB1Protocol = $smb1"
    }

    # Check SMB Signing
    $smbSign = Get-SmbServerConfiguration | Select-Object -ExpandProperty RequireSecuritySignature
    $results += [PSCustomObject]@{
        Check  = "SMB Signing Richiesto"
        Status = if ($smbSign) { "PASS" } else { "FAIL" }
        Detail = "RequireSecuritySignature = $smbSign"
    }

    # Check LLMNR
    $llmnr = Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" -Name EnableMulticast -ErrorAction SilentlyContinue
    $results += [PSCustomObject]@{
        Check  = "LLMNR Disabilitato"
        Status = if ($llmnr.EnableMulticast -eq 0) { "PASS" } else { "FAIL" }
        Detail = "EnableMulticast = $($llmnr.EnableMulticast)"
    }

    # Check LSA Protection
    $lsaPPL = Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name RunAsPPL -ErrorAction SilentlyContinue
    $results += [PSCustomObject]@{
        Check  = "LSA Protection (RunAsPPL)"
        Status = if ($lsaPPL.RunAsPPL -eq 1) { "PASS" } else { "FAIL" }
        Detail = "RunAsPPL = $($lsaPPL.RunAsPPL)"
    }

    # Check WDigest
    $wdigest = Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\WDigest" -Name UseLogonCredential -ErrorAction SilentlyContinue
    $results += [PSCustomObject]@{
        Check  = "WDigest Disabilitato"
        Status = if ($wdigest.UseLogonCredential -eq 0) { "PASS" } else { "FAIL" }
        Detail = "UseLogonCredential = $($wdigest.UseLogonCredential)"
    }

    # Check Firewall
    $fwProfiles = Get-NetFirewallProfile
    $fwAllEnabled = ($fwProfiles | Where-Object { $_.Enabled -eq $false }).Count -eq 0
    $results += [PSCustomObject]@{
        Check  = "Firewall Attivo (tutti i profili)"
        Status = if ($fwAllEnabled) { "PASS" } else { "FAIL" }
        Detail = ($fwProfiles | ForEach-Object { "$($_.Name)=$($_.Enabled)" }) -join ", "
    }

    # Check PowerShell Script Block Logging
    $psLogging = Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" -Name EnableScriptBlockLogging -ErrorAction SilentlyContinue
    $results += [PSCustomObject]@{
        Check  = "PowerShell Script Block Logging"
        Status = if ($psLogging.EnableScriptBlockLogging -eq 1) { "PASS" } else { "FAIL" }
        Detail = "EnableScriptBlockLogging = $($psLogging.EnableScriptBlockLogging)"
    }

    # Check Credential Guard
    $credGuard = Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard -ErrorAction SilentlyContinue
    $cgRunning = $credGuard.SecurityServicesRunning -contains 1
    $results += [PSCustomObject]@{
        Check  = "Credential Guard Attivo"
        Status = if ($cgRunning) { "PASS" } else { "WARN" }
        Detail = "SecurityServicesRunning = $($credGuard.SecurityServicesRunning -join ',')"
    }

    # Check Remote Registry
    $remReg = Get-Service RemoteRegistry -ErrorAction SilentlyContinue
    $results += [PSCustomObject]@{
        Check  = "Remote Registry Disabilitato"
        Status = if ($remReg.StartType -eq 'Disabled') { "PASS" } else { "FAIL" }
        Detail = "StartType = $($remReg.StartType), Status = $($remReg.Status)"
    }

    # Report
    $passCount = ($results | Where-Object Status -eq "PASS").Count
    $failCount = ($results | Where-Object Status -eq "FAIL").Count
    $warnCount = ($results | Where-Object Status -eq "WARN").Count
    $total     = $results.Count

    Write-Output "`n====== HARDENING COMPLIANCE REPORT ======"
    Write-Output "Server: $ComputerName"
    Write-Output "Data:   $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Output "=========================================="
    Write-Output "PASS: $passCount / $total"
    Write-Output "FAIL: $failCount / $total"
    Write-Output "WARN: $warnCount / $total"
    Write-Output "Score: $([math]::Round($passCount/$total*100))%"
    Write-Output "==========================================`n"

    $results | Format-Table Check, Status, Detail -AutoSize

    return $results
}

# Eseguire il compliance check
$report = Test-ServerHardening
```

---

## Sysmon — Monitoraggio Avanzato dei Processi

Sysmon (System Monitor) è un tool di Sysinternals che estende enormemente le capacità di logging di Windows, registrando eventi come la creazione di processi con hash, connessioni di rete, modifiche al registro, caricamento di driver e DLL, e molto altro. È un componente essenziale per qualsiasi strategia di detection avanzata.

```powershell
# Installare Sysmon con una configurazione ottimizzata per la detection
# Scaricare da: https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon
# Usare la configurazione di SwiftOnSecurity come base:
# https://github.com/SwiftOnSecurity/sysmon-config

# Installazione con file di configurazione
sysmon64.exe -accepteula -i sysmonconfig-export.xml

# Aggiornare la configurazione senza reinstallare
sysmon64.exe -c sysmonconfig-export.xml

# Verificare la configurazione corrente
sysmon64.exe -c

# Event ID critici di Sysmon:
# 1  = Process Create (con hash, parent process, command line)
# 3  = Network Connection (processo che apre connessioni)
# 7  = Image Loaded (DLL loading - alto volume, filtrare!)
# 8  = CreateRemoteThread (injection detection)
# 10 = Process Access (es. accesso a LSASS)
# 11 = File Create (creazione file)
# 12 = Registry key/value create/delete
# 13 = Registry value set
# 22 = DNS Query (logging DNS per processo)
# 23 = File Delete (con archiviazione del file eliminato)
# 25 = Process Tampering (process hollowing, herpaderping)

# Query eventi Sysmon con PowerShell
# Processi sospetti che accedono a LSASS (potenziale credential dumping)
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" -MaxEvents 1000 |
    Where-Object { $_.Id -eq 10 -and $_.Message -match "lsass.exe" } |
    Select-Object TimeCreated,
        @{N='SourceProcess';E={($_.Message -split "`n" | Select-String "SourceImage:").ToString().Trim()}},
        @{N='TargetProcess';E={($_.Message -split "`n" | Select-String "TargetImage:").ToString().Trim()}}

# Connessioni di rete verso IP esterni (potenziale C2)
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" -MaxEvents 500 |
    Where-Object { $_.Id -eq 3 } |
    Select-Object TimeCreated,
        @{N='Process';E={($_.Message -split "`n" | Select-String "Image:").ToString().Trim()}},
        @{N='DestIP';E={($_.Message -split "`n" | Select-String "DestinationIp:").ToString().Trim()}},
        @{N='DestPort';E={($_.Message -split "`n" | Select-String "DestinationPort:").ToString().Trim()}}

# Query DNS sospette (potenziale DNS tunneling o DGA)
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" -MaxEvents 500 |
    Where-Object { $_.Id -eq 22 } |
    Select-Object TimeCreated,
        @{N='Process';E={($_.Message -split "`n" | Select-String "Image:").ToString().Trim()}},
        @{N='Query';E={($_.Message -split "`n" | Select-String "QueryName:").ToString().Trim()}}
```

---

---

## Esercizi

1. **Lab — Compliance Scan Baseline.** Installare una VM Windows Server 2022 con configurazione di default. Eseguire lo script `Test-ServerHardening` (dalla sezione DSC), documentare tutti i FAIL. Applicare le correzioni una per una, ri-eseguendo lo script dopo ogni modifica. Obiettivo: 100% PASS.

2. **Lab — LAPS + gMSA Deployment.** In un dominio lab con almeno 2 server: (a) deployare Windows LAPS su una OU di workstation, verificare la rotazione della password, testare il recupero; (b) creare un gMSA per un servizio SQL Server, configurare il servizio per usare il gMSA, verificare con `Test-ADServiceAccount`.

3. **Lab — WDAC Audit-to-Enforcement.** Su un server di test: (a) creare una policy WDAC dalla golden image con `New-CIPolicy`; (b) deployare in audit mode; (c) installare un'applicazione di terze parti, verificare gli eventi 3076; (d) creare una supplementary policy; (e) passare a enforcement mode; (f) verificare che il software non autorizzato sia bloccato.

4. **Lab — Hardening di Rete End-to-End.** Su un server lab: (a) rimuovere SMBv1 e abilitare SMB signing+encryption; (b) disabilitare LLMNR, NBT-NS, mDNS, WPAD; (c) disabilitare TLS 1.0/1.1 e configurare solo cipher suite sicure; (d) configurare il firewall con default deny inbound; (e) testare la connettività di tutte le applicazioni dopo ogni modifica.

5. **Stretch — WEF/WEC con Detection Rules.** Configurare un server WEC collector e 2+ server source. Creare una subscription per gli Event ID critici (4625, 4688, 4698, 7045). Simulare un attacco (creazione di scheduled task sospetta, installazione di un servizio) e verificare che gli eventi siano raccolti centralmente. Creare uno script PowerShell che analizza gli eventi raccolti e genera alert.

6. **Lab — PowerShell Security Stack.** Su un server di test: (a) abilitare Script Block Logging, Module Logging e Transcription; (b) configurare WDAC per forzare Constrained Language Mode; (c) creare un endpoint JEA per gli operatori DNS; (d) testare che un operatore DNS possa solo eseguire i comandi autorizzati; (e) verificare che tutti i comandi siano registrati nei log e nelle trascrizioni.

---

## Autovalutazione

<details>
<summary>1. Qual è la differenza fondamentale tra CIS Benchmark Level 1 e Level 2, e come si decide quale applicare?</summary>

Level 1 include impostazioni di sicurezza di base che non impattano significativamente la funzionalità del sistema e sono raccomandate per tutti i server in produzione. Level 2 include impostazioni più restrittive che possono impattare la funzionalità di alcune applicazioni e sono raccomandate per server ad alta sicurezza (es. DMZ, server che gestiscono dati classificati). La decisione dipende dalla classificazione del dato e dal risk assessment: server che gestiscono dati sensibili (PII, dati finanziari, dati sanitari) dovrebbero adottare Level 2 con test approfonditi in ambiente di staging. Ogni controllo Level 2 non applicabile deve essere documentato nel registro eccezioni con giustificazione tecnica e data di scadenza.
</details>

<details>
<summary>2. Perché Credential Guard è più sicuro di LSA Protection (RunAsPPL) e quali sono i prerequisiti hardware?</summary>

LSA Protection (RunAsPPL) impedisce l'accesso al processo LSASS da parte di processi non firmati come PPL, ma un attaccante con privilegi kernel può potenzialmente bypassare questa protezione. Credential Guard utilizza la Virtualization Based Security (VBS) per isolare le credenziali in un container protetto dall'hypervisor (Isolated LSA). Anche il kernel del sistema operativo non può accedere a questo container, rendendo gli attacchi di credential theft (Mimikatz) inefficaci anche con privilegi SYSTEM. Prerequisiti hardware: CPU con supporto virtualizzazione (Intel VT-x/AMD-V), TPM 2.0 (raccomandato), UEFI Secure Boot, 64-bit OS. Non disponibile su VM nested senza supporto hypervisor specifico.
</details>

<details>
<summary>3. Qual è la strategia raccomandata per eliminare NTLM da un dominio Active Directory?</summary>

L'eliminazione di NTLM è un processo graduale in 4 fasi: (1) Audit — abilitare il logging NTLM tramite GPO per identificare tutti gli utilizzi nel dominio (Event log "Microsoft-Windows-NTLM/Operational"); (2) Analisi — categorizzare le applicazioni che usano NTLM, identificare quelle che possono essere migrate a Kerberos e quelle che necessitano eccezioni temporanee; (3) Eccezioni — creare la lista di server/applicazioni che necessitano ancora NTLM nella GPO "Add server exceptions"; (4) Enforcement — applicare gradualmente la restrizione "Deny all domain accounts to domain servers" per-OU, monitorando l'impatto. Non tentare mai di disabilitare NTLM in una sola operazione su tutto il dominio.
</details>

<details>
<summary>4. Come funziona il Protected Users group e perché NON si devono aggiungere gli account di servizio?</summary>

Il gruppo Protected Users applica automaticamente restrizioni non configurabili: blocca NTLM (solo Kerberos), disabilita DES e RC4 per Kerberos, impedisce la delega (constrained e unconstrained), limita il TGT a 4 ore, impedisce la cache delle credenziali offline, e disabilita WDigest. Gli account di servizio NON devono essere aggiunti perché: (a) molti servizi necessitano NTLM per compatibilità; (b) la delega Kerberos è spesso necessaria per i servizi multi-tier; (c) la limitazione del TGT a 4 ore causa rinnovi frequenti che possono interrompere processi di lunga durata; (d) l'assenza di cache offline impedisce l'avvio dei servizi se il DC non è raggiungibile. Per i service account, usare gMSA con restrizioni specifiche.
</details>

<details>
<summary>5. Qual è la differenza tra WDAC e AppLocker, e quando usare ciascuno?</summary>

WDAC (Windows Defender Application Control) opera a livello kernel tramite VBS e non può essere bypassato nemmeno da processi SYSTEM — è la soluzione più robusta. AppLocker opera a livello user mode ed è bypassabile con privilegi elevati. WDAC supporta supplementary policies (multi-policy) e managed installer, ma non ha granularità per-utente. AppLocker supporta regole per-utente/per-gruppo. Usare WDAC per: server dedicati a ruoli specifici dove la massima sicurezza è prioritaria. Usare AppLocker per: ambienti misti dove servono regole diverse per gruppi diversi di utenti. Possono coesistere: WDAC per l'enforcement di sistema, AppLocker per regole per-utente aggiuntive.
</details>

<details>
<summary>6. Descrivere la strategia di audit a tre livelli (Native Windows + Sysmon + WEF) e il ruolo di ciascun componente.</summary>

Livello 1 — Advanced Audit Policy (nativo Windows): configura cosa viene registrato nel Security log (logon, process creation, privilege use, policy change). Event ID 4624/4625 (logon), 4688 (process create con command line), 4672 (special privileges), 4698 (scheduled task). Livello 2 — Sysmon: estende enormemente il logging con eventi non disponibili nativamente: hash dei processi, parent process tree, connessioni di rete per processo (Event ID 3), accesso a LSASS (Event ID 10), DNS query per processo (Event ID 22), process tampering (Event ID 25). Livello 3 — WEF/WEC: centralizza gli eventi di tutti i server su un collector, eliminando la necessità di accedere a ogni server per l'analisi. Il collector è il punto di integrazione con il SIEM. Insieme, i tre livelli forniscono visibilità completa: cosa è successo (Audit Policy), come è successo (Sysmon), dove è visibile (WEF).
</details>

<details>
<summary>7. Quali sono i rischi di disabilitare TLS 1.0/1.1 e come si mitigano?</summary>

Il rischio principale è rompere applicazioni legacy che non supportano TLS 1.2+. Questo include: applicazioni Java con JRE < 8u161 (TLS 1.2 non abilitato per default), applicazioni .NET Framework < 4.6 (senza registry override), client con OS molto vecchi (Windows XP, Windows Server 2003), dispositivi IoT/SCADA con firmware non aggiornabile, e librerie di terze parti che hard-codano TLS 1.0. Mitigazione: (1) abilitare SChannel logging (`EventLogging=7`) prima della disabilitazione per identificare connessioni TLS 1.0/1.1; (2) mantenere TLS 1.0/1.1 abilitato per un periodo di audit; (3) creare eccezioni per-porta se necessario (IIS può avere binding diversi); (4) aggiornare le applicazioni e le librerie. Non mantenere TLS 1.0/1.1 abilitato indefinitamente — è una debolezza documentata.
</details>

<details>
<summary>8. Perché Server Core è preferibile a Desktop Experience per l'hardening e quali sono le limitazioni operative?</summary>

Server Core riduce la superficie di attacco in modo significativo: ~50% meno aggiornamenti necessari, nessun Internet Explorer (vettore di attacco comune), meno file binari eseguibili (meno target per exploitation), meno servizi in esecuzione, meno CVE applicabili. Limitazioni operative: nessuna interfaccia grafica (gestione solo via PowerShell, WinRM, RSAT remoto, Windows Admin Center); non tutti i ruoli sono supportati (es. alcuni ruoli che richiedono GUI); la curva di apprendimento per gli amministratori abituati alla GUI è significativa; il troubleshooting sul server locale è limitato a PowerShell. Mitigazione: formazione del team su PowerShell, adozione di Windows Admin Center come console centralizzata, mantenere Desktop Experience solo sui server che lo richiedono con documentazione dell'eccezione.
</details>

<details>
<summary>9. Come si implementa una strategia di patch management ring-based e come si gestisce un zero-day?</summary>

Ring-based: Ring 0 (5% server, pilota, 0 giorni deferral, 48-72h monitoraggio), Ring 1 (15%, early adopter, 3-7 giorni), Ring 2 (60%, broad, 7-14 giorni), Ring 3 (20%, critical systems, 14-21 giorni con maintenance window dedicata). Ogni ring avanza solo se il precedente non ha mostrato impatti. Per zero-day con exploit attivo: skip dell'intero processo ring, deployment immediato su tutti i server con rollback procedure pronta prima dell'applicazione. Comunicazione al management entro 1 ora. Post-mortem entro 24 ore per documentare l'impatto e le decisioni prese. La procedura di rollback (`wusa /uninstall /kb:XXXXXX`) deve essere testata in anticipo per garantire che funzioni rapidamente.
</details>

<details>
<summary>10. Spiegare il modello Tier (Tier 0/1/2) di Microsoft e come si implementa tecnicamente con GPO.</summary>

Il Tier Model separa gli asset in tre livelli: Tier 0 (identity — DC, CA, AADConnect), Tier 1 (application — server applicativi, DB, Exchange), Tier 2 (endpoint — workstation, laptop). La regola fondamentale: le credenziali di un tier superiore non devono mai essere esposte su un dispositivo di un tier inferiore. Implementazione tecnica: (1) creare OU separate per ogni tier; (2) creare gruppi di admin per ogni tier (Tier0-Admins, Tier1-Admins, Tier2-Admins); (3) applicare GPO con "Deny log on locally" e "Deny log on through RDP" per impedire il cross-tier logon (es. Tier0-Admins denied su OU Tier1 e Tier2); (4) utilizzare Privileged Access Workstation (PAW) dedicate per ogni tier; (5) monitorare con Event ID 4624 (Type 2 e 10) per detectare violazioni del modello.
</details>

---

## Letture

- CIS Benchmarks per Windows Server 2022 — https://www.cisecurity.org/benchmark/microsoft_windows_server · Consultato: 2026-05-23
- Microsoft Security Compliance Toolkit (SCT) — https://www.microsoft.com/en-us/download/details.aspx?id=55319 · Consultato: 2026-05-23
- Microsoft Learn — Credential Guard Overview — https://learn.microsoft.com/en-us/windows/security/identity-protection/credential-guard/ · Consultato: 2026-05-23
- Microsoft Learn — Windows LAPS — https://learn.microsoft.com/en-us/windows-server/identity/laps/laps-overview · Consultato: 2026-05-23
- Microsoft Learn — JEA (Just Enough Administration) — https://learn.microsoft.com/en-us/powershell/scripting/learn/remoting/jea/overview · Consultato: 2026-05-23
- Microsoft Learn — WDAC (Windows Defender Application Control) — https://learn.microsoft.com/en-us/windows/security/application-security/application-control/windows-defender-application-control/ · Consultato: 2026-05-23
- Microsoft Learn — Attack Surface Reduction Rules — https://learn.microsoft.com/en-us/defender-endpoint/attack-surface-reduction-rules-reference · Consultato: 2026-05-23
- DISA STIG per Windows Server 2022 — https://public.cyber.mil/stigs/ · Consultato: 2026-05-23
- NIST SP 800-123: Guide to General Server Security — https://csrc.nist.gov/publications/detail/sp/800-123/final · Consultato: 2026-05-23
- Microsoft Learn — Protected Users Security Group — https://learn.microsoft.com/en-us/windows-server/security/credentials-protection-and-management/protected-users-security-group · Consultato: 2026-05-23
- Microsoft Learn — Windows Event Forwarding — https://learn.microsoft.com/en-us/windows/security/operating-system-security/device-management/windows-event-forwarding/ · Consultato: 2026-05-23
- MITRE ATT&CK Framework — Windows Techniques — https://attack.mitre.org/matrices/enterprise/windows/ · Consultato: 2026-05-23
- SwiftOnSecurity — Sysmon Configuration — https://github.com/SwiftOnSecurity/sysmon-config · Consultato: 2026-05-23
- AD Security by Sean Metcalf — https://adsecurity.org/ · Consultato: 2026-05-23
- Microsoft Learn — Kerberos Armoring (FAST) — https://learn.microsoft.com/en-us/windows-server/security/kerberos/kerberos-authentication-overview · Consultato: 2026-05-23

---

## Cross-link ai Moduli Correlati

| Modulo | Relazione con questo capitolo |
|--------|-------------------------------|
| [01 — Active Directory](01-active-directory.md) | Tier Model, Protected Users, AdminSDHolder, Fine-Grained Password Policies, Kerberos armoring — tutti dipendono dalla comprensione di AD |
| [02 — PowerShell](02-powershell.md) | Script Block Logging, Module Logging, Transcription, Constrained Language Mode, JEA, DSC — fondamenta della sicurezza PowerShell |
| [05 — Sicurezza Windows](05-sicurezza-windows.md) | Fondamenti di sicurezza, principio del minimo privilegio, defense in depth — prerequisiti concettuali dell'hardening |
| [06 — Rete Windows](06-rete-windows.md) | Windows Firewall, IPsec, SMB, protocolli di rete — dettagli implementativi dell'hardening di rete |
| [08 — Permessi e Accesso](08-permessi-e-accesso.md) | NTFS ACL, share permissions, delega — complemento alla gestione dei permessi nell'hardening |
| [09 — Monitoraggio e Performance](09-monitoraggio-performance.md) | Performance Monitor, contatori — il monitoraggio è l'occhio dell'hardening |
| [10 — Gestione Aggiornamenti](10-gestione-aggiornamenti.md) | WSUS, WUfB, ring-based patching — il patching è la prima linea di difesa |
| [11 — Servizi Certificati](11-servizi-certificati.md) | PKI, TLS, certificati — l'infrastruttura che sostiene TLS hardening, Kerberos armoring, code signing |
| [12 — Endpoint Management](12-endpoint-management.md) | Intune, GPO, compliance — strumenti di deployment e verifica delle policy di hardening |
| [13 — Azure AD / Identità Ibrida](13-azure-ad-identita-ibrida.md) | Azure AD Connect, Conditional Access — estensione dell'hardening all'identità cloud |
| [30 — Identità Ibrida Dettaglio](30-identita-ibrida-azure-ad-dettaglio.md) | Approfondimento su Azure AD Connect, Passthrough Auth — sicurezza dell'identità ibrida |
| [34 — Disaster Recovery AD+PKI](34-disaster-recovery-ad-pki.md) | Backup e recovery delle configurazioni di hardening, forest recovery dopo compromissione |

---

## Glossario

| Termine | Definizione |
|---|---|
| **CIS Benchmark** | Standard di configurazione di sicurezza pubblicati dal Center for Internet Security, basati sul consenso dell'industria. Organizzati in Level 1 (base) e Level 2 (avanzato). |
| **DISA STIG** | Security Technical Implementation Guide, standard di hardening del Dipartimento della Difesa USA. Finding classificati in CAT I (critica), CAT II (alta), CAT III (media). |
| **SCAP** | Security Content Automation Protocol. Framework di protocolli per la scansione automatizzata della conformità a standard di sicurezza (CIS, STIG). |
| **Credential Guard** | Tecnologia Microsoft che utilizza Virtualization Based Security (VBS) per isolare le credenziali in un container protetto dall'hypervisor, inaccessibile anche al kernel del sistema operativo. |
| **LSA Protection (RunAsPPL)** | Configurazione che impedisce a processi non firmati come Protected Process Light di accedere al processo LSASS. Meno robusto di Credential Guard ma senza requisiti hardware VBS. |
| **Protected Users** | Gruppo di sicurezza globale AD che applica automaticamente restrizioni non configurabili: solo Kerberos, no cache offline, no delega, TGT limitato a 4 ore. |
| **gMSA** | Group Managed Service Account. Account di servizio con password gestita automaticamente da AD (rotazione ogni 30 giorni, 240 caratteri). Elimina la gestione manuale delle password dei service account. |
| **AdminSDHolder** | Container speciale in AD che definisce le ACL applicate automaticamente ogni 60 minuti (via SDProp) a tutti gli account e gruppi protetti (Domain Admins, Enterprise Admins, ecc.). |
| **WDAC** | Windows Defender Application Control. Tecnologia di application control a livello kernel (via VBS) che controlla quali eseguibili, script e driver possono essere caricati. Non bypassabile da SYSTEM. |
| **AppLocker** | Tecnologia di application whitelisting a livello user-mode che supporta regole per publisher, path e hash, con granularità per utente/gruppo. Bypassabile con privilegi elevati. |
| **ASR Rules** | Attack Surface Reduction Rules. Regole comportamentali integrate in Microsoft Defender che bloccano tecniche di attacco specifiche (macro malicious, injection, credential theft da LSASS). |
| **FAST (Kerberos Armoring)** | Flexible Authentication Secure Tunneling. Estensione Kerberos che protegge lo scambio di pre-autenticazione wrappandolo in un tunnel TGT, prevenendo AS-REP Roasting e offline attacks. |
| **WEF/WEC** | Windows Event Forwarding / Windows Event Collector. Tecnologia nativa Windows per la centralizzazione dei log di sicurezza da server source a un collector senza agenti aggiuntivi. |
| **Schannel** | Provider di sicurezza di Windows che implementa i protocolli SSL/TLS. Configurabile via registry per abilitare/disabilitare protocolli, cipher suite e algoritmi di hash. |
| **VBS** | Virtualization Based Security. Tecnologia Microsoft che usa l'hypervisor per creare regioni di memoria isolate dal kernel del sistema operativo. Fondamento di Credential Guard, HVCI e WDAC. |
| **HVCI** | Hypervisor-Protected Code Integrity. Componente VBS che verifica l'integrità del codice in kernel mode, impedendo il caricamento di driver non firmati o modificati. |
| **DSC** | Desired State Configuration. Framework PowerShell dichiarativo per definire e mantenere lo stato desiderato dei server. Usato per compliance-as-code e drift detection. |
| **PSO** | Password Settings Object. Oggetto AD che implementa le Fine-Grained Password Policies, permettendo policy di password diverse per gruppi diversi nello stesso dominio. |
| **Tier Model** | Modello di accesso privilegiato Microsoft che separa asset e account amministrativi in tre livelli (Tier 0 identity, Tier 1 application, Tier 2 endpoint) per prevenire lateral movement. |
| **Service SID** | Security Identifier assegnato a un servizio Windows per permessi granulari senza account dedicato. Tipi: None, Unrestricted, Restricted. |
| **CLM** | Constrained Language Mode. Modalità PowerShell che blocca .NET arbitrario, COM objects e script non firmati. Abilitato automaticamente da WDAC in enforcement mode. |

---

## Riferimenti

- CIS Benchmarks per Windows Server — https://www.cisecurity.org/benchmark/microsoft_windows_server
- Microsoft Security Compliance Toolkit — https://www.microsoft.com/en-us/download/details.aspx?id=55319
- Microsoft Docs: Windows LAPS — https://learn.microsoft.com/en-us/windows-server/identity/laps/laps-overview
- Microsoft Docs: JEA — https://learn.microsoft.com/en-us/powershell/scripting/learn/remoting/jea/overview
- Microsoft Docs: Credential Guard — https://learn.microsoft.com/en-us/windows/security/identity-protection/credential-guard/
- NIST SP 800-123: Guide to General Server Security — https://csrc.nist.gov/publications/detail/sp/800-123/final
- MITRE ATT&CK Framework — https://attack.mitre.org/
- AD Security by Sean Metcalf — https://adsecurity.org/
