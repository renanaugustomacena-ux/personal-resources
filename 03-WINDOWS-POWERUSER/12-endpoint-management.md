# Endpoint Management — Guida Completa

> **Modulo 12** · **Aggiornamento:** 2026-05-24

| Campo | Valore |
|---|---|
| **Modulo del corso** | Amministrazione Windows enterprise |
| **Prerequisiti** | Conoscenza di Active Directory e GPO (→ `01-active-directory.md`), familiarità con Azure AD e identità ibrida (→ `13-azure-ad-identita-ibrida.md`), padronanza di PowerShell base (→ `02-powershell.md`) |
| **Obiettivi di apprendimento** | 1) Confrontare SCCM/MECM on-prem con Intune cloud-first e implementare co-management · 2) Configurare Windows Autopilot per provisioning zero-touch · 3) Gestire MDM e MAM per dispositivi aziendali e BYOD · 4) Progettare update rings e Autopatch per il patch management · 5) Utilizzare Endpoint Analytics per visibilità proattiva sulla salute dei dispositivi |
| **Tempo stimato** | lettura 110 min · lab 120 min |
| **Livello** | Proficient |
| **Ultimo aggiornamento** | 2026-05-24 |

## Idee guida
1. **Configuration Manager (SCCM) on-prem; Intune cloud-first.**
2. **Co-management: SCCM + Intune insieme.**
3. **Autopilot classico + Device Preparation (v2) per zero-touch provisioning.**
4. **WSUS legacy; replaced da Update for Business.**
5. **MDM per dispositivi aziendali; MAM per BYOD senza enrollment.**
6. **Endpoint Analytics per visibilità proattiva sulla salute dei dispositivi.**
7. **Autopatch per automazione completa degli aggiornamenti Windows.**
8. **EPM per elevazione just-in-time senza admin locale permanente.**
9. **ASR rules via Intune per ridurre la superficie di attacco sugli endpoint.**
10. **Windows 365 Cloud PC gestiti come endpoint fisici in Intune.**


## Indice

- [Panoramica](#panoramica)
- [Evoluzione dell'Endpoint Management](#evoluzione-dellendpoint-management)
- [Microsoft Intune — Deep Dive](#microsoft-intune--deep-dive)
- [SCCM / MECM — Architettura e Funzionalità](#sccm--mecm--architettura-e-funzionalità)
- [Windows Autopilot](#windows-autopilot)
- [Co-Management](#co-management)
- [MDM vs MAM](#mdm-vs-mam)
- [Configuration Profiles — Approfondimento](#configuration-profiles--approfondimento)
- [Application Management](#application-management)
- [Compliance Policy e Conditional Access](#compliance-policy-e-conditional-access)
- [Patch Management e Update Rings](#patch-management-e-update-rings)
- [Windows Autopatch](#windows-autopatch)
- [Windows 365 Cloud PC — Gestione tramite Intune](#windows-365-cloud-pc--gestione-tramite-intune)
- [Endpoint Analytics](#endpoint-analytics)
- [Defender for Endpoint — Regole ASR via Intune](#defender-for-endpoint--regole-asr-via-intune)
- [Endpoint Privilege Management (EPM)](#endpoint-privilege-management-epm)
- [PowerShell Scripts e Remediation](#powershell-scripts-e-remediation)
- [Matrice Decisionale di Deployment](#matrice-decisionale-di-deployment)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## Panoramica

L'Endpoint Management gestisce il ciclo di vita dei dispositivi aziendali: provisioning, configurazione, distribuzione software, compliance, aggiornamenti e ritiro. Microsoft offre due piattaforme principali: **Intune** (cloud-native, MDM/MAM) e **SCCM/MECM** (on-premise, gestione completa). Il co-management le unisce per una transizione graduale al cloud.

### Obiettivi dell'Endpoint Management

```
Obiettivo                       │ Strumento primario
────────────────────────────────┼──────────────────────────────────
Provisioning zero-touch         │ Windows Autopilot + Intune
Distribuzione software          │ Intune (Win32), SCCM (Packages)
Compliance dispositivo          │ Intune Compliance + Conditional Access
Aggiornamenti OS                │ WUfB Update Rings / Autopatch
Sicurezza endpoint              │ Microsoft Defender for Endpoint
Inventario HW/SW                │ SCCM Inventory / Intune Reports
Assistenza remota               │ Remote Help (Intune) / SCCM Remote
OS Deployment (imaging)         │ SCCM Task Sequences / Autopilot
Gestione app BYOD               │ MAM (App Protection Policies)
Monitoraggio proattivo          │ Endpoint Analytics
```

### Componenti dell'Ecosistema Microsoft

```
Microsoft Intune Suite
├── Microsoft Intune (core MDM/MAM)
├── Intune Remote Help
├── Microsoft Tunnel (VPN gateway)
├── Endpoint Privilege Management
├── Advanced Endpoint Analytics
├── Intune Plan 2 (firmware management, specialty devices)
└── Copilot in Intune (AI-assisted troubleshooting)

Configuration Manager (MECM)
├── Site Server + Database (SQL)
├── Management Points
├── Distribution Points
├── Software Update Points (WSUS)
├── State Migration Points
├── Cloud Management Gateway (CMG)
└── Client Agent su ogni endpoint

Servizi Complementari
├── Azure AD / Entra ID (identità)
├── Conditional Access (accesso condizionale)
├── Microsoft Defender for Endpoint (EDR)
├── Windows Autopilot (provisioning)
├── Windows Autopatch (aggiornamenti automatici)
└── Endpoint Analytics (telemetria e proactive remediations)
```

---

## Evoluzione dell'Endpoint Management

### Timeline Storica

```
Anno │ Prodotto                        │ Paradigma
─────┼─────────────────────────────────┼─────────────────────────────────
1994 │ SMS 1.0                         │ Inventario e distribuzione SW
2003 │ SMS 2003                        │ Software metering, patch mgmt
2007 │ SCCM 2007                       │ Desired Configuration Mgmt,
     │                                 │ OSD, NAP integration
2012 │ SCCM 2012                       │ Application model, user-centric
     │                                 │ deployment, UDI
2014 │ Intune standalone (v1)          │ MDM cloud-only, mobile devices
2016 │ SCCM CB (Current Branch)        │ Servicing model, frequenti
     │                                 │ aggiornamenti
2019 │ MECM (rinominato)               │ Microsoft Endpoint Manager,
     │   + Co-management GA            │ Intune + SCCM unified console
2020 │ Intune + Autopilot maturo       │ Cloud-native device lifecycle
2022 │ Intune Suite + Autopatch GA     │ Premium add-ons, managed updates
2023 │ Intune cloud-native focus       │ Settings Catalog, Remediations
2024 │ Copilot in Intune               │ AI-assisted policy creation
2025 │ Intune Advanced                 │ Firmware, privilege mgmt,
     │                                 │ specialty device support
```

### Paradigmi a Confronto

```
On-Premises (SCCM)              │ Cloud-Native (Intune)
────────────────────────────────┼──────────────────────────────────
Richiede infrastruttura server  │ Nessun server da gestire
Active Directory domain join    │ Azure AD / Entra ID join
GPO per configurazione          │ Configuration Profiles / MDM
Imaging con Task Sequences      │ Autopilot zero-touch
WSUS per patch                  │ WUfB Update Rings
Distribution Points per SW      │ CDN cloud per distribuzione
LAN/VPN necessaria              │ Funziona ovunque con Internet
Costo infrastruttura alto       │ Costo per licenza/utente
Controllo granulare completo    │ Controllo tramite MDM CSP
Gestione solo Windows (core)    │ Multi-piattaforma (Win/iOS/Android/Mac)
```

### Percorso di Modernizzazione Consigliato

```
Fase 1: Assessment
├── Inventario dispositivi attuali (OS, modelli, età)
├── Mappatura applicazioni e dipendenze
├── Identificare dispositivi legacy non supportati
└── Valutare licenze disponibili (E3/E5, Intune add-on)

Fase 2: Co-Management
├── Installare CMG per SCCM (cloud management gateway)
├── Abilitare co-management SCCM + Intune
├── Spostare primi workload: Compliance + Endpoint Protection
├── Pilotare con gruppo ristretto (5-10% dei device)
└── Monitorare e validare per 30 giorni

Fase 3: Cloud Transition
├── Spostare Windows Update policies → Intune
├── Spostare Device Configuration → Intune
├── Migrare applicazioni critiche a Win32 .intunewin
├── Configurare Autopilot per nuovi device
└── Disabilitare imaging SCCM per nuovi device

Fase 4: Cloud-Native
├── Nuovi device: solo Azure AD Join + Autopilot
├── Rimanenti workload: Client Apps → Intune
├── Ritiro graduale infrastruttura SCCM
├── SCCM mantenuto solo per device legacy
└── Target: 90%+ device cloud-managed entro 18 mesi
```

---

## Microsoft Intune — Deep Dive

### Architettura

```
Microsoft Intune (cloud)
├── Device Management (MDM)
│   ├── Windows 10/11      → Enrollment automatico via Azure AD Join
│   ├── iOS/iPadOS         → Apple Push Notification + DEP
│   ├── Android            → Android Enterprise (Work Profile, Fully Managed)
│   └── macOS              → MDM enrollment
├── Application Management (MAM)
│   ├── App Protection Policies (senza enrollment)
│   ├── App Configuration Policies
│   └── Win32 App / MSI / Store deployment
├── Compliance Policies     → Verificano requisiti (BitLocker, PIN, versione OS)
├── Configuration Profiles  → Equivalente GPO cloud-based
├── Conditional Access      → Integrazione Azure AD per accesso condizionale
├── Endpoint Security
│   ├── Antivirus           → Microsoft Defender gestito
│   ├── Disk Encryption     → BitLocker gestito
│   ├── Firewall            → Windows Firewall gestito
│   └── Attack Surface Reduction
├── Endpoint Analytics      → Performance, proactive remediations
├── Scripts                 → PowerShell e Bash script deployment
├── Remediations           → Script di detection + remediation
└── Reports                → Compliance, app install, device status
```

### Prerequisiti e Licenze

```
Licenza Intune inclusa in:
├── Microsoft 365 E3/E5           → Intune Plan 1
├── Microsoft 365 F1/F3           → Intune Plan 1
├── Enterprise Mobility + Security E3/E5 → Intune Plan 1
├── Microsoft 365 Business Premium → Intune Plan 1
└── Intune standalone (acquisto separato)

Intune Suite (add-on premium):
├── Intune Plan 2           → Firmware-over-the-air, specialty devices
├── Remote Help              → Assistenza remota integrata
├── Endpoint Privilege Mgmt  → Elevazione just-in-time
├── Advanced Analytics       → Anomaly detection, device query
└── Microsoft Tunnel         → VPN gateway cloud-managed

Prerequisiti tecnici:
├── Tenant Azure AD / Entra ID
├── MDM Authority impostata su Intune
├── Licenza assegnata agli utenti
├── DNS: enterpriseregistration.windows.net → CNAME
├── Per iOS: Apple MDM Push Certificate
├── Per Android: Managed Google Play account
└── Per Autopilot: hash hardware registrati
```

### Enrollment — Metodi Dettagliati

```powershell
# ═══════════════════════════════════════════════════════════════
# METODO 1: Azure AD Join (consigliato per nuovi device)
# ═══════════════════════════════════════════════════════════════
# Settings → Accounts → Access work or school → Connect → Join Azure AD
# Enrollment automatico se MDM User Scope configurato in Intune
#
# Prerequisiti:
# - Intune → Devices → Enrollment → Automatic enrollment
# - MDM User Scope: All (o gruppi specifici)
# - MAM User Scope: None (o gruppi specifici per BYOD)
#
# Flow:
# 1. Utente clicca "Join this device to Azure AD"
# 2. Inserisce credenziali aziendali
# 3. Azure AD registra il device
# 4. MDM enrollment automatico in Intune
# 5. Compliance check + policy sync

# ═══════════════════════════════════════════════════════════════
# METODO 2: Autopilot (zero-touch provisioning) — vedi sezione dedicata
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
# METODO 3: Bulk enrollment con Provisioning Package
# ═══════════════════════════════════════════════════════════════
# Windows Configuration Designer → Advanced provisioning → Cloud Management
# Genera .ppkg da applicare ai dispositivi
#
# Utile per:
# - Dispositivi condivisi (kiosk, sala riunioni)
# - Enrollment di massa senza Autopilot
# - Device senza utente assegnato
#
# Creare il package:
# 1. Aprire Windows Configuration Designer
# 2. Advanced Provisioning → nome progetto
# 3. Runtime Settings → Workplace → Enrollments
# 4. Inserire UPN, AuthPolicy = OnPremise, DiscoveryServiceFullURL
# 5. Export → Provisioning Package (.ppkg)
# Applicare: Settings → Accounts → Access work or school → Add provisioning package

# ═══════════════════════════════════════════════════════════════
# METODO 4: Group Policy enrollment (hybrid Azure AD Join)
# ═══════════════════════════════════════════════════════════════
# Computer → Administrative Templates → Windows Components → MDM
# → Enable automatic MDM enrollment using default Azure AD credentials
#
# Prerequisiti:
# - Device hybrid Azure AD joined
# - Azure AD Connect configurato con device sync
# - MDM User Scope configurato in Intune
# - GPO applicata ai computer target

# ═══════════════════════════════════════════════════════════════
# METODO 5: Co-Management enrollment (da SCCM)
# ═══════════════════════════════════════════════════════════════
# SCCM → Administration → Cloud Services → Co-management
# Enrollment automatico in Intune per client SCCM esistenti
# Richiede: Azure AD hybrid join + co-management abilitato

# ═══════════════════════════════════════════════════════════════
# METODO 6: Enrollment per dispositivi personali (BYOD)
# ═══════════════════════════════════════════════════════════════
# L'utente installa Company Portal dal Microsoft Store
# Si autentica con credenziali aziendali
# Il dispositivo viene registrato (Azure AD Registered, non Joined)
# MAM policies applicate alle app aziendali
# Il dispositivo personale non è gestito completamente (MDM leggero)

# ═══════════════════════════════════════════════════════════════
# VERIFICA ENROLLMENT
# ═══════════════════════════════════════════════════════════════
dsregcmd /status
# Controllare:
# AzureAdJoined: YES (per AAD Join)
# DomainJoined: YES (per hybrid)
# MdmUrl: https://enrollment.manage.microsoft.com/...
# TenantId: <GUID del tenant>

# Forzare sync con Intune
# Settings → Accounts → Access work or school → Info → Sync
# O PowerShell:
$enrollmentID = Get-ScheduledTask | Where-Object {$_.TaskName -like "*PushLaunch*"} |
    Select-Object -ExpandProperty TaskPath | Split-Path -Leaf
Start-ScheduledTask -TaskPath "\Microsoft\Windows\EnterpriseMgmt\$enrollmentID\" `
    -TaskName "PushLaunch"
```

### Enrollment Restrictions

```
Le Enrollment Restrictions controllano QUALI dispositivi possono registrarsi.

Intune → Devices → Enrollment restrictions → Device type restrictions
├── Piattaforme consentite: Windows, iOS, Android, macOS
├── Versione OS minima/massima
├── Dispositivi personali: consentire o bloccare
├── Manufacturer restrictions (es. solo Dell, HP, Lenovo)
└── Limite numero dispositivi per utente (default: 15)

Intune → Devices → Enrollment restrictions → Device limit restrictions
├── Default: 5 dispositivi per utente
├── Personalizzabile per gruppi
└── Non si applica a device Autopilot o bulk enrollment

Best practice:
├── Bloccare enrollment di versioni OS obsolete
├── Limitare dispositivi personali se non necessario
├── Assegnare restrizioni diverse per gruppo
│   (es. IT admins: 15 device, utenti standard: 5)
└── Documentare le eccezioni
```

### Device Categories e Scope Tags

```
Device Categories (categorizzazione automatica):
├── L'utente sceglie la categoria durante l'enrollment
├── Categorie tipiche: Desktop, Laptop, Tablet, Kiosk, SharedDevice
├── Dynamic groups basati sulla categoria:
│   (device.deviceCategory -eq "Laptop")
├── Policy e app assegnate automaticamente per categoria
└── Configurazione: Intune → Devices → Device categories

Scope Tags (delega amministrativa):
├── Limitano la visibilità di oggetti Intune per ruolo/area
├── Esempio: tag "EuropeIT" vede solo device e policy europei
├── Assegnati a: configuration profiles, apps, compliance policies
├── Admin con scope tag "EuropeIT" non vede oggetti tag "AsiaIT"
├── Default scope tag: tutti gli admin lo vedono
└── Configurazione: Intune → Tenant admin → Roles → Scope tags
```

---

## SCCM / MECM — Architettura e Funzionalità

### Architettura Dettagliata

```
SCCM / MECM (on-premise o cloud-attached)
├── Site Server          → Central management point, database SQL
├── Management Point (MP)
│   ├── Comunicazione client-server (HTTP/HTTPS)
│   ├── Policy download
│   └── Inventory upload
├── Distribution Point (DP)
│   ├── Distribuzione contenuti (software, OS images, driver packages)
│   ├── Branch Distribution Point (server leggero per sedi piccole)
│   ├── Cloud Distribution Point (Azure blob per client remoti)
│   └── Pull Distribution Point (scarica da altri DP)
├── Software Update Point (SUP)
│   ├── Integrazione WSUS
│   ├── Synchronization schedule
│   └── Update groups e deployment packages
├── Reporting Point      → SQL Reporting Services (SSRS)
├── Fallback Status Point → Client che non comunicano col MP
├── State Migration Point → USMT data durante OSD
├── Enrollment Point     → MDM enrollment on-prem
├── Cloud Management Gateway (CMG)
│   ├── Servizio Azure che fa da proxy per client su Internet
│   ├── Permette gestione SCCM senza VPN
│   ├── Costo: Azure VM + traffico
│   └── Richiede certificati PKI o Azure AD token auth
└── SCCM Client Agent    → Installato su ogni endpoint

Gerarchia:
Central Administration Site (CAS) → per ambienti > 100.000 client
├── Primary Site (gestisce fino a 100.000 client)
│   ├── Distribution Points
│   ├── Management Points
│   └── Software Update Points
└── Secondary Site (per sedi remote con banda limitata)
    ├── Distribution Point locale
    └── Management Point locale (proxy)
```

### Boundary Groups

```
I Boundary Groups definiscono la topologia di rete per SCCM:

Boundary Types:
├── IP Subnet (es. 10.1.0.0/16)
├── Active Directory Site
├── IPv6 prefix
└── IP address range

Boundary Group → associa:
├── Distribution Points assegnati
├── Management Points assegnati
├── Software Update Points assegnati
├── State Migration Points assegnati
└── Fallback behavior (tempo prima di cercare in altro BG)

Esempio configurazione:
Boundary Group "MilanoHQ"
├── Subnet: 10.10.0.0/16
├── DP: DP-MILANO01.corp.contoso.com
├── MP: MP-MILANO01.corp.contoso.com
├── SUP: SUP-MILANO01.corp.contoso.com
└── Fallback to "Default": 120 minuti

Boundary Group "RomaOffice"
├── Subnet: 10.20.0.0/16
├── DP: DP-ROMA01.corp.contoso.com
├── MP: MP-ROMA01.corp.contoso.com
└── Fallback to "MilanoHQ": 60 minuti
```

### Metodi di Installazione Client SCCM

```powershell
# ═══════════════════════════════════════════════════════════════
# METODO 1: Client Push Installation (più comune)
# ═══════════════════════════════════════════════════════════════
# SCCM Console → Administration → Site Configuration → Client Push
# Richiede: admin locale sul target, porte 445/135/RPC
# Automatico: abilita per discovered resources
# Account: dedicato con local admin sui client
ccmsetup.exe /mp:sccm-server.corp.contoso.com SMSSITECODE=PS1

# ═══════════════════════════════════════════════════════════════
# METODO 2: Group Policy Installation
# ═══════════════════════════════════════════════════════════════
# Software Installation GPO che punta al ccmsetup.msi
# Computer Configuration → Policies → Software Settings →
#   Software Installation → New Package
# Slower ma non richiede admin push access

# ═══════════════════════════════════════════════════════════════
# METODO 3: Logon Script
# ═══════════════════════════════════════════════════════════════
# Script nel logon script che verifica e installa il client
# @echo off
# if not exist "%windir%\ccm\ccmexec.exe" (
#   \\sccm-server\SMS_PS1\Client\ccmsetup.exe /mp:sccm-server SMSSITECODE=PS1
# )

# ═══════════════════════════════════════════════════════════════
# METODO 4: Manual / Command Line
# ═══════════════════════════════════════════════════════════════
ccmsetup.exe /mp:sccm-server.corp.contoso.com `
    SMSSITECODE=PS1 `
    SMSMP=sccm-server.corp.contoso.com `
    FSP=fsp-server.corp.contoso.com `
    CCMHTTPPORT=80 `
    CCMHTTPSPORT=443

# ═══════════════════════════════════════════════════════════════
# METODO 5: Software Update Point (con WSUS)
# ═══════════════════════════════════════════════════════════════
# Pubblica ccmsetup come update in WSUS
# I client Windows Update scaricano e installano automaticamente

# Verificare installazione:
Get-Service CcmExec  # Deve essere Running
Get-WmiObject -Namespace root\ccm -Class SMS_Client  # Versione client
# Log installazione: C:\Windows\ccmsetup\Logs\ccmsetup.log
# Log client: C:\Windows\CCM\Logs\

# Azioni manuali del client:
# Control Panel → Configuration Manager → Actions tab
# - Machine Policy Retrieval & Evaluation Cycle
# - Software Inventory Cycle
# - Hardware Inventory Cycle
# - Software Updates Scan Cycle
# - Software Updates Deployment Evaluation Cycle
```

### Software Distribution

```powershell
# SCCM supporta due modelli di distribuzione:

# ════════════════════════════════════════════════════
# APPLICATIONS (modello moderno, consigliato)
# ════════════════════════════════════════════════════
# Software Library → Application Management → Applications → Create Application
#
# Deployment Type (può averne multipli per app):
# ├── MSI installer
# ├── Script installer (EXE con parametri)
# ├── App-V virtual application
# ├── MSIX
# ├── Mac OS X (.cmmac)
# └── Web application
#
# Detection Method (come verifica se l'app è installata):
# ├── MSI Product Code (automatico per MSI)
# ├── File system: path + nome file + versione
# ├── Registry: chiave + valore + confronto
# └── Custom script (PowerShell, VBScript, JScript)
#
# Requirements (condizioni per installare):
# ├── OS version
# ├── Disk space minimo
# ├── RAM minima
# ├── CPU architecture (x86/x64)
# └── Custom Global Conditions (WQL query, script, registry)
#
# Dependencies (installate prima dell'app):
# ├── .NET Framework
# ├── Visual C++ Runtime
# └── Altre applicazioni prerequisite
#
# Supersedence (sostituzione versioni):
# ├── La nuova versione sostituisce automaticamente la vecchia
# ├── Opzione: upgrade (mantiene dati) o uninstall+install
# └── Catena di supersedence per aggiornamenti multipli

# ════════════════════════════════════════════════════
# PACKAGES (modello legacy, più flessibile)
# ════════════════════════════════════════════════════
# Software Library → Packages → Create Package
#
# Meno intelligente: nessun detection, nessun requirement automatico
# Più flessibile: esegue qualsiasi command line
# Utile per: script complessi, sequenze multi-step, configurazioni
#
# Package + Program = unità di distribuzione
# Il Program definisce la command line da eseguire

# ════════════════════════════════════════════════════
# TASK SEQUENCES (per deploy complessi)
# ════════════════════════════════════════════════════
# Sequenze multi-step con logica condizionale
# Utile per: installazione OS, provisioning complesso, migrazione
```

### OS Deployment (OSD) — Approfondimento

```powershell
# SCCM OSD usa Task Sequences per deploy automatizzato dell'OS

# Componenti necessari:
# 1. Boot Image (WinPE personalizzato con driver)
# 2. OS Image (WIM dell'immagine Windows)
# 3. Driver Packages (driver per modelli hardware specifici)
# 4. Application Packages (software da installare post-OS)
# 5. USMT Package (per migrazione dati utente)

# Task Sequence tipica — Steps:
# ═══════════════════════════════════════════════════════════════
# 1. Restart in WinPE
#    └── Boot dal PXE, USB, o media
# 2. Partition Disk
#    ├── UEFI: EFI (500MB) + MSR (128MB) + OS + Recovery
#    └── BIOS: System (500MB) + OS
# 3. Apply Operating System Image
#    └── Applica il WIM all'unità OS
# 4. Apply Windows Settings
#    ├── Organization name
#    ├── Product key (KMS/MAK)
#    ├── Admin password
#    └── Time zone
# 5. Apply Network Settings
#    ├── Join domain: corp.contoso.com
#    ├── OU: OU=Workstations,DC=corp,DC=contoso,DC=com
#    └── Domain join account
# 6. Apply Device Drivers
#    ├── Auto-apply da driver catalog
#    └── O applica driver package specifico per modello
# 7. Setup Windows and ConfigMgr
#    └── Installa il client SCCM
# 8. Install Software Updates
#    └── Scarica e installa patch dal SUP
# 9. Install Applications
#    ├── Office 365 Apps
#    ├── Adobe Reader
#    ├── Chrome/Edge
#    └── Applicazioni LOB
# 10. Run Command Line / PowerShell
#     ├── Configurazioni custom
#     ├── Registry tweaks
#     └── Cleanup temporanei
# ═══════════════════════════════════════════════════════════════

# Metodi di avvio OSD:
# PXE Boot      → Richiede PXE-enabled DP
# Boot Media    → USB o CD con WinPE
# Prestaged     → WIM pre-applicato dal produttore
# Standalone    → Media completo offline
```

---

## Windows Autopilot

### Panoramica

```
Autopilot fornisce provisioning zero-touch per nuovi dispositivi Windows:
1. L'utente accende il PC nuovo
2. Si connette alla rete e vede la schermata di login aziendale
3. Inserisce credenziali Azure AD
4. Il dispositivo si configura automaticamente (app, policy, certificati)

Nessun imaging necessario — l'OEM installa Windows, Autopilot lo personalizza.

Vantaggi rispetto a OSD tradizionale:
├── Nessuna infrastruttura server necessaria
├── OEM spedisce direttamente all'utente
├── Funziona ovunque con connessione Internet
├── Nessun WIM customizzato da mantenere
├── Aggiornamento OS tramite WUfB, non re-imaging
└── Self-service: l'utente completa il setup
```

### Scenari di Deployment

```
═══════════════════════════════════════════════════════════════
SCENARIO 1: User-Driven (più comune)
═══════════════════════════════════════════════════════════════
Flow:
1. Utente accende il PC → OOBE personalizzato
2. Seleziona lingua e tastiera
3. Si connette alla rete (Wi-Fi o Ethernet)
4. Inserisce email aziendale → redirect a Azure AD login
5. MFA se configurato
6. Enrollment Setup Page (ESP):
   ├── Device preparation (AAD Join, MDM enrollment)
   ├── Device setup (compliance check, config profiles)
   └── Account setup (app installation, policy sync)
7. Desktop pronto

Configurazione:
├── Join type: Azure AD Join o Hybrid Azure AD Join
├── OOBE: skip privacy, EULA, registration
├── User account type: Standard (consigliato) o Administrator
└── Enrollment Status Page: abilitata con timeout

═══════════════════════════════════════════════════════════════
SCENARIO 2: Self-Deploying (per kiosk e shared device)
═══════════════════════════════════════════════════════════════
Flow:
1. Device acceso → nessun input utente necessario
2. Connessione rete automatica (Ethernet consigliato)
3. TPM 2.0 attestation (identifica il device)
4. Azure AD Join + MDM enrollment automatici
5. App e policy installate senza interazione

Requisiti:
├── TPM 2.0 obbligatorio
├── Ethernet o Wi-Fi pre-configurato
├── Nessun utente assegnato (device-centric)
└── Non supporta Hybrid Azure AD Join

Casi d'uso:
├── Kiosk (single-app o multi-app)
├── Digital signage
├── Dispositivi condivisi
└── Sale riunioni

═══════════════════════════════════════════════════════════════
SCENARIO 3: Pre-Provisioning (White Glove)
═══════════════════════════════════════════════════════════════
Flow — Fase IT:
1. IT riceve il device dal fornitore
2. Accende → OOBE → preme Windows key 5 volte
3. Seleziona "Provision this device"
4. Device si registra in Autopilot, applica config e app
5. IT verifica che tutto sia OK → Reseal

Flow — Fase Utente:
1. Utente riceve il device pre-configurato
2. Accende → OOBE rapido (solo credenziali)
3. Setup completato in pochi minuti (la maggior parte già fatto)

Vantaggi:
├── Riduce tempo utente da 30-60 min a 5-10 min
├── IT verifica prima della consegna
├── App pesanti già installate (Office, LOB)
└── Utile per VIP o dispositivi critici

═══════════════════════════════════════════════════════════════
SCENARIO 4: Autopilot Reset
═══════════════════════════════════════════════════════════════
Riporta il device allo stato post-Autopilot senza reinstallare Windows.
├── Rimuove: profili utente, app installate dall'utente, impostazioni
├── Mantiene: Azure AD Join, MDM enrollment, Wi-Fi, config Autopilot
├── Utile per: passaggio device tra utenti, problemi software
├── Trigger locale: Settings → Recovery → Reset this PC (con preserva)
└── Trigger remoto: Intune → Devices → Autopilot Reset
```

### Configurazione Autopilot

```powershell
# ═══════════════════════════════════════════════════════════════
# STEP 1: Registrare dispositivi (Hardware Hash)
# ═══════════════════════════════════════════════════════════════

# Sul dispositivo (durante OOBE o da Windows):
Install-Script Get-WindowsAutopilotInfo
Get-WindowsAutopilotInfo -OutputFile C:\autopilot.csv

# Contenuto CSV:
# Serial Number, Windows Product ID, Hardware Hash
# Il Hardware Hash è un blob di 4K+ caratteri che identifica il device

# Importare il CSV:
# Intune → Devices → Windows enrollment → Devices → Import

# Metodo OEM: il fornitore registra gli hash direttamente nel tenant
# (Dell, HP, Lenovo supportano la registrazione pre-vendita)

# ═══════════════════════════════════════════════════════════════
# STEP 2: Creare Deployment Profile
# ═══════════════════════════════════════════════════════════════
# Intune → Devices → Windows enrollment → Deployment Profiles → Create
#
# Impostazioni profilo:
# ├── Deployment mode: User-Driven / Self-Deploying
# ├── Join type: Azure AD Join / Hybrid Azure AD Join
# ├── OOBE settings:
# │   ├── Skip privacy settings: Yes
# │   ├── Skip EULA: Yes
# │   ├── Skip registration: Yes
# │   ├── Hide change account options: Yes
# │   └── User account type: Standard / Administrator
# ├── Naming template:
# │   ├── CORP-%SERIAL%     → CORP-5CG1234ABC
# │   ├── CORP-%RAND:4%     → CORP-A7F2
# │   └── Massimo 15 caratteri (limite NetBIOS)
# └── Apply device name template: Yes

# ═══════════════════════════════════════════════════════════════
# STEP 3: Configurare Enrollment Status Page (ESP)
# ═══════════════════════════════════════════════════════════════
# Intune → Devices → Windows enrollment → Enrollment Status Page
#
# ESP settings:
# ├── Show app and profile configuration progress: Yes
# ├── Show error when setup exceeds X minutes: 60 (consigliato)
# ├── Show custom error message: Yes
# ├── Allow users to reset device: Yes
# ├── Allow user to use device if setup fails: No (consigliato)
# ├── Block device use until required apps installed: Yes
# └── Track installation of selected apps:
#     ├── Office 365 Apps
#     ├── VPN client
#     └── App LOB critiche

# ═══════════════════════════════════════════════════════════════
# STEP 4: Assegnare profilo a gruppi di dispositivi
# ═══════════════════════════════════════════════════════════════
# Creare Dynamic Device Group in Azure AD:
# (device.devicePhysicalIds -any (_ -contains "[OrderID]:PurchaseOrder2024"))

# Oppure basato su Autopilot group tag:
# (device.devicePhysicalIds -any (_ -contains "[OrderID]:IT-Laptops"))

# ═══════════════════════════════════════════════════════════════
# STEP 5: Assegnare app e policy
# ═══════════════════════════════════════════════════════════════
# Le app e configuration profiles assegnati al gruppo
# verranno installati automaticamente durante l'enrollment
# App Required → installate durante ESP
# Configuration Profiles → applicati durante Device Setup
```

### Autopilot Device Preparation (v2)

```
Autopilot Device Preparation è la nuova generazione del provisioning
Windows, progettata per semplificare e velocizzare l'onboarding dei
dispositivi rispetto al classico Autopilot (v1).

Differenza fondamentale: NON richiede la registrazione dell'hardware hash.
Il dispositivo viene registrato dinamicamente durante il sign-in dell'utente.

Confronto Autopilot v1 (Classic) vs v2 (Device Preparation):

Aspetto                  │ Autopilot Classic (v1)    │ Device Preparation (v2)
─────────────────────────┼───────────────────────────┼──────────────────────────
Registrazione device     │ Hardware hash obbligatorio│ Dinamica al sign-in
                         │ (import CSV o OEM)        │ (nessun hash richiesto)
Modalità supportate      │ User-Driven, Self-Deploy, │ Solo User-Driven e
                         │ Pre-Provisioning, Existing│ Automatic (Windows 365)
Join type                │ Azure AD Join + Hybrid    │ Solo Entra ID Join
                         │ Azure AD Join             │ (no Hybrid)
Co-management            │ Supportato                │ NON supportato
Pre-provisioning (WG)    │ Supportato                │ NON supportato
Self-deploying mode      │ Supportato                │ NON supportato
Mix app LOB + Win32      │ Può causare failure       │ Supportato senza problemi
Reporting                │ ESP status + report std   │ Near real-time per ogni
                         │                           │ app e script + export diag
Velocità provisioning    │ 30-60 minuti tipico       │ Più rapido (meno overhead)
Complexity               │ Maggiore (hash, profili)  │ Minore (zero pre-registr.)

Quando usare v2 (Device Preparation):
├── Nuovi deployment cloud-native senza infrastruttura legacy
├── Organizzazioni che non vogliono gestire hardware hash
├── Scenario User-Driven con Entra ID Join puro
├── Windows 365 Cloud PC provisioning
├── Quando si distribuiscono app LOB e Win32 nella stessa policy
└── Quando serve reporting granulare in tempo reale

Quando restare su v1 (Classic Autopilot):
├── Self-Deploying mode necessario (kiosk, shared device)
├── Pre-Provisioning (White Glove) richiesto
├── Hybrid Azure AD Join obbligatorio
├── Co-management SCCM + Intune attivo
├── Ambienti con workflow OEM basati su hardware hash già consolidati
└── Device existing da riconvertire (Autopilot for existing devices)

Coesistenza:
├── v1 e v2 possono coesistere nello stesso tenant
├── Ogni device può usare solo UNA delle due soluzioni
├── Profili Autopilot classic hanno precedenza su Device Preparation
├── La migrazione da v1 a v2 non è automatica
│   (richiede rimozione del profilo classic e creazione policy v2)
└── Consiglio: usare v2 per nuovi device, mantenere v1 per device esistenti
```

### Configurazione Device Preparation

```
Intune → Devices → Device onboarding → Enrollment
→ Windows Autopilot Device Preparation → Create policy

Componenti della policy:
├── Device naming template: CORP-%RAND:4% (max 15 caratteri)
├── Timeout: tempo massimo per il provisioning (consigliato 90 min)
├── App assignment:
│   ├── Fino a 10 app per policy (LOB + Win32 mescolabili)
│   ├── Le app vengono installate in ordine definito
│   ├── Reporting mostra stato di ogni singola app in tempo reale
│   └── Failure di un'app non blocca necessariamente il provisioning
├── Script assignment:
│   ├── Script PowerShell eseguiti durante il provisioning
│   ├── Reporting per-script con output e exit code
│   └── Timeout per-script configurabile
└── Assegnazione: gruppi di device Entra ID

Flow dell'utente:
1. Accende il PC nuovo → OOBE
2. Seleziona lingua e rete
3. Inserisce email aziendale → redirect Entra ID login
4. MFA se configurato → autenticazione completata
5. Device registrato dinamicamente in Intune
6. Policy Device Preparation applicata
7. App e script installati con progresso visibile in tempo reale
8. Desktop pronto — l'utente può iniziare a lavorare

Diagnostica e troubleshooting:
├── Export diagnostics direttamente dalla console durante il provisioning
├── Log dettagliati per ogni step (device setup, app install, script)
├── Near real-time: aggiornamenti ogni pochi secondi nella console Intune
└── In caso di errore: possibilità di retry senza ricominciare da zero
```

---

## Co-Management

### Architettura e Prerequisiti

```
Co-Management connette SCCM con Intune per gestione ibrida.
Ogni workload può essere gestito da SCCM O da Intune.

Prerequisiti:
├── SCCM CB version 1710 o successiva
├── Azure AD hybrid join per i dispositivi
├── Azure AD Connect configurato
├── Licenza Intune per gli utenti
├── CMG consigliato (per client remoti)
├── MDM Authority = Intune
└── Co-management abilitato in SCCM console
```

### Workload Dettagliati

```
Workload gestibili — Slider SCCM ← → Intune:

├── Compliance Policies
│   ├── SCCM: Configuration Baselines, Compliance Settings
│   ├── Intune: Compliance Policies con Conditional Access
│   └── Consiglio: spostare a Intune per primo (Conditional Access)
│
├── Device Configuration
│   ├── SCCM: Configuration Items, Baselines
│   ├── Intune: Configuration Profiles, Settings Catalog
│   └── Consiglio: spostare dopo compliance (secondo workload)
│
├── Resource Access Policies
│   ├── SCCM: Wi-Fi, VPN, Email, Certificate profiles
│   ├── Intune: stessi profili ma cloud-managed
│   └── Consiglio: spostare con device configuration
│
├── Endpoint Protection
│   ├── SCCM: SCEP (System Center Endpoint Protection)
│   ├── Intune: Microsoft Defender for Endpoint policies
│   └── Consiglio: spostare a Intune per Defender integration
│
├── Windows Update Policies
│   ├── SCCM: SUP/WSUS con Software Update Groups
│   ├── Intune: Windows Update for Business rings
│   └── Consiglio: spostare a Intune (WUfB più efficiente)
│
├── Client Apps
│   ├── SCCM: Applications e Packages
│   ├── Intune: Win32 apps, Microsoft Store, LOB
│   └── Consiglio: ultimo workload da spostare (più complesso)
│
└── Office Click-to-Run Apps
    ├── SCCM: Office deployment con ODT
    ├── Intune: Microsoft 365 Apps deployment integrato
    └── Consiglio: spostare insieme a Client Apps
```

### Fasi di Transizione

```
Percorso di migrazione tipico:

Fase 1: Abilitazione (Settimana 1-2)
├── Configurare Azure AD Connect con device sync
├── Abilitare Hybrid Azure AD Join
├── Installare CMG se necessario
├── Abilitare co-management in SCCM console
├── Pilotare con collection ristretta (10-20 device IT)
└── Tutti i workload rimangono su SCCM

Fase 2: Primi Workload (Settimana 3-6)
├── Spostare Compliance policies → Intune (pilot)
├── Configurare Conditional Access policies
├── Spostare Endpoint Protection → Intune (pilot)
├── Verificare: compliance reporting, Defender policies funzionanti
└── Espandere pilot a 50-100 device

Fase 3: Configurazione (Mese 2-3)
├── Spostare Device Configuration → Intune
├── Spostare Resource Access → Intune
├── Spostare Windows Update → Intune (WUfB rings)
├── Creare Configuration Profiles equivalenti alle GPO SCCM
└── Espandere a tutti i device (tranne legacy)

Fase 4: Applicazioni (Mese 3-6)
├── Migrare le app critiche a formato .intunewin
├── Spostare Office Click-to-Run → Intune
├── Spostare Client Apps → Intune
├── Testare install/uninstall/detection per ogni app
└── Company Portal come self-service

Fase 5: Completamento (Mese 6-12)
├── Nuovi device: solo Autopilot + Intune (no SCCM client)
├── Verificare che tutti i workload funzionino da Intune
├── Discommissionare SCCM infrastructure gradualmente
├── Mantenere SCCM solo per device legacy (Windows 7/8.1)
└── Target: SCCM decommissioned entro 18 mesi
```

### Abilitazione e Monitoraggio

```powershell
# ═══════════════════════════════════════════════════════════════
# Abilitare co-management in SCCM
# ═══════════════════════════════════════════════════════════════
# SCCM Console → Administration → Cloud Services → Co-management
# Properties → Enable co-management
#
# Impostazioni:
# - Automatic enrollment in Intune: All o Pilot (collection)
# - Pilot collection: scegliere collection con device di test
# - Workloads: slider per ogni workload
#   Posizioni slider:
#   ├── Configuration Manager (tutto SCCM)
#   ├── Pilot Intune (solo pilot collection usa Intune)
#   └── Intune (tutti i device usano Intune)

# ═══════════════════════════════════════════════════════════════
# Verificare stato co-management sul client
# ═══════════════════════════════════════════════════════════════
Get-CimInstance -Namespace root\ccm\clientsdk -ClassName CCM_CoManagementState

# Output atteso:
# MachineId: <GUID>
# ComgmtPolicyPresent: True
# IsMachineCoManaged: True
# <WorkloadName>Authority: 1 (SCCM) o 2 (Intune) per ogni workload

# ═══════════════════════════════════════════════════════════════
# Monitoraggio in Intune
# ═══════════════════════════════════════════════════════════════
# Intune → Devices → Overview → Co-management eligibility
# Dashboard con:
# ├── Co-managed devices count
# ├── Workload distribution (per workload, SCCM vs Intune)
# ├── Enrollment errors
# └── Client health (attivi, inattivi, sconosciuti)

# SCCM → Monitoring → Co-management
# ├── Co-management Dashboard
# ├── Workload transition status
# └── Enrollment failure details

# ═══════════════════════════════════════════════════════════════
# Log utili per troubleshooting co-management
# ═══════════════════════════════════════════════════════════════
# Sul client:
# C:\Windows\CCM\Logs\CoManagementHandler.log  → stato co-management
# C:\Windows\CCM\Logs\ComplRelayAgent.log       → relay compliance
# C:\Windows\CCM\Logs\WUAHandler.log            → Windows Update
# C:\Windows\CCM\Logs\CIAgent.log               → Configuration Items
```

---

## MDM vs MAM

### Device Management (MDM) vs App Management (MAM)

```
MDM (Mobile Device Management)     │ MAM (Mobile Application Management)
────────────────────────────────────┼──────────────────────────────────────
Gestisce l'intero dispositivo       │ Gestisce solo le app aziendali
Enrollment obbligatorio             │ Enrollment NON necessario
Wipe totale possibile               │ Solo selective wipe (dati aziendali)
Full control: Wi-Fi, VPN, cert     │ Control limitato alle app managed
Ideale per device aziendali (COPE) │ Ideale per BYOD
Privacy utente limitata             │ Privacy utente preservata
BitLocker, Firewall gestiti         │ Nessun accesso a impostazioni OS
Tutti i profili di configurazione   │ Solo App Protection Policies
Report hardware/software completo   │ Report limitato alle app managed
```

### Scenari BYOD

```
BYOD (Bring Your Own Device) — Best Practice:

Scenario 1: MAM-Only (nessun enrollment)
├── L'utente installa Outlook, Teams, OneDrive dal public store
├── Al primo login aziendale → App Protection Policy applicata
├── Dati aziendali cifrati e isolati nelle app managed
├── Copy/paste tra app managed consentito
├── Copy/paste verso app personali BLOCCATO
├── IT può fare selective wipe delle sole app aziendali
├── Nessun accesso a: contatti personali, foto, GPS, app personali
└── Zero impatto sulla privacy dell'utente

Scenario 2: MAM + Enrollment leggero (Azure AD Registered)
├── Utente registra il device (non Join, solo Register)
├── MAM policies + alcune MDM policy leggere
├── Conditional Access con compliance basica
├── Company Portal per app self-service
└── Wipe limitato: solo dati aziendali

Scenario 3: Full MDM (device aziendale)
├── Azure AD Join completo
├── Tutte le policy MDM applicate
├── Intune controlla il dispositivo interamente
├── BitLocker, Firewall, Windows Update gestiti
└── Wipe completo possibile
```

### App Protection Policies (APP)

```
Le App Protection Policies proteggono i dati aziendali a livello app:

Intune → Apps → App protection policies → Create policy

Data Protection:
├── Backup org data to iTunes/iCloud: Block
├── Send org data to other apps: Policy managed apps only
├── Receive data from other apps: Policy managed apps only
├── Restrict cut, copy, paste between apps: Policy managed apps
├── Third party keyboards: Block
├── Encrypt org data: Require
├── Printing org data: Block
└── Screen capture: Block

Access Requirements:
├── PIN for access: Require
├── PIN type: Numeric (minimo 6 cifre)
├── Biometric instead of PIN: Allow
├── PIN reset after (days): 90
├── App PIN when device PIN set: Require
├── Work/school account credentials: Require
└── Recheck access requirements after (minutes): 30

Conditional Launch:
├── Max PIN attempts: 5 → Reset PIN
├── Offline grace period: 720 min → Block access
├── Jailbroken/rooted device: Block access
├── Min OS version: iOS 16.0 → Warn
├── Max threat level: Secured → Block access
├── Min app version: 2.0 → Block access
└── Disabled account: Block access

Assegnazione:
├── Assegnare a gruppi di utenti (non device)
├── Include: "Tutti gli utenti BYOD"
├── Exclude: "Utenti con device aziendali"
└── Platform: iOS/iPadOS, Android (policy separate per piattaforma)
```

---

## Configuration Profiles — Approfondimento

### Tipologie di Profili

```
Intune → Devices → Configuration profiles → Create profile

Tre approcci principali:

1. Templates (profili predefiniti)
├── Device restrictions
├── Wi-Fi
├── VPN
├── Email
├── Trusted certificate
├── SCEP certificate
├── PKCS certificate
├── Endpoint protection
├── Identity protection (Windows Hello)
├── Edition upgrade
├── Kiosk
├── Shared multi-user device
├── Domain Join (per hybrid)
├── Delivery Optimization
├── Device firmware configuration (DFCI)
├── Windows health monitoring
└── Custom (OMA-URI)

2. Settings Catalog (interfaccia moderna, consigliata)
├── Cerca qualsiasi impostazione Windows per nome
├── Tutte le Administrative Templates ADMX
├── Security baselines
├── Defender settings
├── Edge settings
├── Office settings
├── 5000+ impostazioni disponibili
└── Più granulare dei template

3. Custom Profiles (OMA-URI)
├── Per impostazioni non disponibili nei template/catalog
├── Richiede conoscenza del Configuration Service Provider (CSP)
├── Formato: ./Device/Vendor/MSFT/<CSP>/<setting>
├── Utile per impostazioni di nicchia o nuove
└── Documentazione: docs.microsoft.com/windows/client-management/mdm/
```

### Configuration Profiles Comuni — Dettaglio

```powershell
# ═══════════════════════════════════════════════════════════════
# DEVICE RESTRICTIONS
# ═══════════════════════════════════════════════════════════════
# Intune → Configuration Profiles → Create → Templates → Device restrictions
#
# General:
# ├── Block screen capture: Yes/No
# ├── Block camera: Yes/No
# ├── Block removable storage: Yes/No
# ├── Block Bluetooth: Yes/No
# ├── Block USB connection: Yes/No
# └── Block manual unenrollment: Yes
#
# Password:
# ├── Require password: Yes
# ├── Minimum length: 8
# ├── Required type: Alphanumeric
# ├── Password expiration (days): 90
# ├── Number of previous passwords to prevent: 5
# ├── Maximum minutes of inactivity before lock: 5
# └── Simple passwords: Block
#
# Windows Hello for Business:
# ├── Configure: Enable
# ├── Minimum PIN length: 6
# ├── Biometrics: Allow
# ├── Security key for sign-in: Enable
# └── Use certificates for on-premises resources: Enable
#
# Edge Browser:
# ├── Default search engine: configurabile
# ├── Block password manager: No
# ├── Block popups: Yes
# ├── Block developer tools: Yes (per utenti standard)
# └── Favorites: configurable via JSON

# ═══════════════════════════════════════════════════════════════
# WI-FI PROFILES
# ═══════════════════════════════════════════════════════════════
# Intune → Configuration Profiles → Create → Templates → Wi-Fi
#
# Settings:
# ├── Network name (SSID): CorpWiFi
# ├── Connect automatically: Yes
# ├── Hidden network: No
# ├── Security type: WPA2-Enterprise
# ├── EAP type: EAP-TLS (con certificato)
# ├── Certificate server names: radius.corp.contoso.com
# ├── Root certificate for server validation: Trusted CA cert profile
# ├── Authentication method: Certificate (SCEP o PKCS)
# └── Proxy: Automatic detection
#
# Il profilo Wi-Fi si associa a un profilo certificato (SCEP/PKCS)
# per autenticazione 802.1X automatica

# ═══════════════════════════════════════════════════════════════
# VPN PROFILES
# ═══════════════════════════════════════════════════════════════
# Intune → Configuration Profiles → Create → Templates → VPN
#
# Settings:
# ├── Connection name: CorpVPN
# ├── Connection type: IKEv2 / Always On VPN
# ├── Server: vpn.corp.contoso.com
# ├── Authentication: Certificate / EAP
# ├── Split tunneling: Enable
# │   ├── Include routes: 10.0.0.0/8, 172.16.0.0/12
# │   └── Exclude routes: Internet traffic
# ├── Always On: Enable
# ├── DNS suffix: corp.contoso.com
# ├── Trusted network detection: corp.contoso.com
# └── App-triggered VPN: app specifiche che attivano il tunnel

# ═══════════════════════════════════════════════════════════════
# CERTIFICATI (SCEP e PKCS)
# ═══════════════════════════════════════════════════════════════
# Chain tipica: Root CA → Intermediate CA → User/Device cert
#
# 1. Trusted Certificate Profile:
#    → Importa Root CA e Intermediate CA
#    → Distribuisce a tutti i device
#
# 2. SCEP Certificate Profile:
#    ├── Subject: CN={{UserPrincipalName}}
#    ├── SAN: UPN={{UserPrincipalName}}
#    ├── Key usage: Digital signature, Key encipherment
#    ├── Key size: 2048
#    ├── Validity: 1 year
#    ├── SCEP Server URL: https://ndes.corp.contoso.com/certsrv/mscep/
#    ├── Renewal threshold: 20%
#    └── Richiede: NDES server + Intune Certificate Connector
#
# 3. PKCS Certificate Profile:
#    ├── Alternativa a SCEP per ambienti semplificati
#    ├── Certification Authority: ca.corp.contoso.com
#    ├── Certificate template: IntunePKCS
#    └── Richiede: Intune Certificate Connector on-prem

# ═══════════════════════════════════════════════════════════════
# EMAIL PROFILES
# ═══════════════════════════════════════════════════════════════
# Intune → Configuration Profiles → Create → Templates → Email
#
# Settings:
# ├── Email server: outlook.office365.com
# ├── Account name: {{UserPrincipalName}}
# ├── Username: {{UserPrincipalName}}
# ├── Email address: {{mail}}
# ├── Authentication: Certificate / Username and password
# ├── SSL: Required
# ├── Sync email: last 7 days
# ├── Sync contacts: Yes
# ├── Sync calendar: Yes
# └── S/MIME signing certificate: PKCS profile reference
```

### Conflict Resolution

```
Quando più profili configurano la stessa impostazione → Conflitto.

Ordine di precedenza:
1. Platform-specific settings > Cross-platform
2. Settings Catalog > Templates > Custom OMA-URI
3. User-scope > Device-scope (per impostazioni user)
4. Ultimo profilo modificato vince (non garantito, evitare)

Identificare conflitti:
├── Intune → Devices → seleziona device → Device configuration
├── Status: Conflict / Error / Pending / Succeeded
├── Drill down per vedere quale profilo causa il conflitto
└── Intune → Reports → Device configuration → Assignment failures

Best practice per evitare conflitti:
├── Un profilo per categoria (non duplicare)
├── Usare gruppi esclusivi (non sovrapposti)
├── Documentare quale profilo gestisce quale impostazione
├── Settings Catalog preferito (mostra conflitti chiaramente)
└── Scope Tags per separare ambienti (prod, test, sviluppo)
```

### ADMX Ingestion

```
Importare template ADMX custom in Intune (per app di terze parti):

Intune → Devices → Configuration → Import ADMX

Passi:
1. Ottenere i file ADMX/ADML dell'applicazione
   (es. Chrome ADMX, Firefox ADMX, Adobe ADMX)
2. Importare in Intune → Import ADMX
3. Attendere processing (può richiedere minuti)
4. Le impostazioni appaiono nel Settings Catalog
   sotto "Imported Administrative Templates"
5. Creare Configuration Profile → Settings Catalog
6. Cercare le impostazioni importate per nome
7. Configurare e assegnare ai gruppi

Limitazioni:
├── Massimo 10 file ADMX custom importabili
├── File ADMX devono essere well-formed XML
├── ADML (localizzazione) opzionale ma consigliato
├── Aggiornamenti ADMX: reimportare il file aggiornato
└── Non tutti i CSP supportano tutte le impostazioni ADMX
```

---

## Application Management

### Intune — Tipi di App

```powershell
# ═══════════════════════════════════════════════════════════════
# TIPO 1: Win32 App (.intunewin) — PIÙ VERSATILE
# ═══════════════════════════════════════════════════════════════

# Preparare Win32 app:
# 1. Scaricare IntuneWinAppUtil.exe da GitHub Microsoft
# IntuneWinAppUtil.exe -c C:\Source\App -s setup.exe -o C:\Output
#
# Parametri:
# -c  Source folder con l'installer e file associati
# -s  Setup file (MSI o EXE da eseguire)
# -o  Output folder per il .intunewin risultante
# -q  Quiet mode

# 2. Caricare in Intune → Apps → Windows → Add → Win32 app
#
# App information:
# ├── Name: nome visualizzato
# ├── Description: descrizione per Company Portal
# ├── Publisher: produttore
# ├── App version: 2.0.1
# └── Category: Productivity / Business / etc.
#
# Program:
# ├── Install command: setup.exe /S /NORESTART
# ├── Uninstall command: uninstall.exe /S
# ├── Install behavior: System (installa come SYSTEM)
# ├── Device restart behavior: No specific action
# └── Return codes:
#     ├── 0 = Success
#     ├── 1707 = Success
#     ├── 3010 = Soft reboot required
#     ├── 1641 = Hard reboot required
#     └── 1618 = Retry (installer busy)

# Requirements:
# ├── OS architecture: 64-bit
# ├── Minimum OS version: Windows 10 21H2
# ├── Disk space: 500 MB
# ├── RAM: 4 GB
# └── Custom requirement scripts (PowerShell)

# Detection rules (CRITICO — determinano se l'app è installata):
# Opzione A - File:
#   Path: C:\Program Files\App
#   File: app.exe
#   Detection: File or folder exists (o version >= 2.0)
#
# Opzione B - Registry:
#   Key: HKLM\SOFTWARE\App
#   Value: Version
#   Detection: String comparison (= "2.0.1")
#
# Opzione C - Custom script (PowerShell):
#   Script che esce con 0 + scrive su STDOUT = rilevato
#   Script che esce con 0 senza output = NON rilevato
#   Script che esce con != 0 = errore di detection

# Dependencies (installate prima):
# ├── .NET Framework 4.8
# ├── Visual C++ Runtime 2015-2022
# └── Java Runtime (se necessario)
#
# Ordine: Intune installa le dependencies prima dell'app principale

# Supersedence (sostituzione versioni):
# ├── Update: aggiorna la versione precedente (mantiene dati)
# ├── Replace: disinstalla la vecchia, installa la nuova
# └── Catena: v1.0 → v1.5 → v2.0 (automatico)

# Assignment types:
# ├── Required → Installazione obbligatoria (push silenzioso)
# ├── Available for enrolled devices → Utente sceglie da Company Portal
# ├── Available with or without enrollment → per MAM
# └── Uninstall → Rimozione forzata

# ═══════════════════════════════════════════════════════════════
# TIPO 2: Microsoft Store App (nuova integrazione)
# ═══════════════════════════════════════════════════════════════
# Intune → Apps → Windows → Add → Microsoft Store app (new)
#
# Cerca app direttamente dal Microsoft Store
# Installazione automatica senza account Store
# Auto-update gestito dal Store
# Non richiede packaging .intunewin
# Esempi: Company Portal, Power BI, Whiteboard

# ═══════════════════════════════════════════════════════════════
# TIPO 3: Microsoft 365 Apps (Office)
# ═══════════════════════════════════════════════════════════════
# Intune → Apps → Windows → Add → Microsoft 365 Apps → Windows 10+
#
# Configuration:
# ├── Apps da includere: Word, Excel, PowerPoint, Outlook, Teams
# ├── Architecture: 64-bit (consigliato)
# ├── Update channel: Monthly Enterprise / Current
# ├── Version to install: Latest
# ├── Languages: it-IT, en-US
# ├── Shared Computer Activation: per VDI/shared
# └── Accept EULA: Yes

# ═══════════════════════════════════════════════════════════════
# TIPO 4: Line-of-Business (LOB) App
# ═══════════════════════════════════════════════════════════════
# Intune → Apps → Windows → Add → Line-of-business app
# Supporta: .msi, .appx, .appxbundle, .msix, .msixbundle
# Più semplice del Win32 ma meno flessibile
# Detection automatica per MSI (Product Code)

# ═══════════════════════════════════════════════════════════════
# TIPO 5: MSIX / MSIX App Attach
# ═══════════════════════════════════════════════════════════════
# MSIX: formato moderno di packaging Microsoft
# Vantaggi:
# ├── Clean install/uninstall (nessun residuo)
# ├── Auto-update tramite AppInstaller
# ├── Containerizzato (sicurezza migliorata)
# ├── Firma digitale obbligatoria
# └── Supporto Intune come LOB app
#
# MSIX App Attach (per Azure Virtual Desktop):
# ├── L'app è su VHD/VHDX/CimFS
# ├── Montata on-demand alla sessione utente
# ├── Non installata sul golden image
# └── Riduce dimensione e complessità immagine VDI

# ═══════════════════════════════════════════════════════════════
# MATRICE DECISIONALE: Win32 vs MSIX vs Store
# ═══════════════════════════════════════════════════════════════
#
# Criterio              │ Win32 (.intunewin)  │ MSIX            │ Store
# ──────────────────────┼─────────────────────┼─────────────────┼──────────────
# Formato installer     │ EXE, MSI, qualsiasi │ .msix/.msixbundle│ Automatico
# Packaging richiesto   │ Sì (IntuneWinAppUtil)│ Sì (MSIX Tool) │ No
# Firma digitale        │ Opzionale           │ OBBLIGATORIA    │ Microsoft
# Containerizzazione    │ No                  │ Sì (isolato)    │ Sì
# Clean uninstall       │ Dipende dall'app    │ Garantito       │ Garantito
# Dependencies          │ Supportate          │ Non supportate  │ N/A
# Supersedence          │ Supportata          │ Non supportata  │ N/A
# Detection rules       │ Manuali (obblig.)   │ Automatiche     │ Automatiche
# Dimensione max        │ 30 GB               │ 30 GB           │ N/A
# Auto-update           │ No (manuale)        │ Via AppInstaller │ Via Store
# App con driver/servizi│ Sì                  │ No              │ No
# Legacy installer      │ Sì                  │ Conversione req.│ No
# Ideale per            │ App enterprise,     │ App moderne,    │ App pubbliche,
#                       │ installer complessi │ clean lifecycle │ utility comuni
#
# Regola decisionale:
# 1. App disponibile nel Microsoft Store → Store (zero packaging)
# 2. App moderna senza driver/servizi → MSIX (clean lifecycle)
# 3. App legacy, installer complesso, driver → Win32 (massima flessibilità)

# ═══════════════════════════════════════════════════════════════
# MSIX — Pipeline di Packaging
# ═══════════════════════════════════════════════════════════════
#
# Workflow di conversione app esistente → MSIX:
#
# 1. Analisi compatibilità
#    ├── L'app usa servizi Windows? → MSIX non supporta (usare Win32)
#    ├── L'app installa driver? → MSIX non supporta (usare Win32)
#    ├── L'app scrive fuori dal proprio container? → Potrebbe non funzionare
#    └── MSIX Packaging Tool → test di conversione automatica
#
# 2. Conversione
#    ├── MSIX Packaging Tool (Microsoft Store, gratuito)
#    ├── Installare l'app in una VM pulita durante il capture
#    ├── Il tool cattura tutte le modifiche al filesystem e registry
#    └── Genera il pacchetto .msix con manifest
#
# 3. Firma digitale (OBBLIGATORIA)
#    ├── Azure Artifact Signing — certificato CA-trusted nel cloud
#    ├── Code Signing Certificate — acquistato da CA pubblica
#    ├── Self-signed — solo per test interni (non produzione)
#    ├── Comando: SignTool sign /fd SHA256 /a /f cert.pfx app.msix
#    └── Senza firma → Windows rifiuta l'installazione
#
# 4. Test e validazione
#    ├── Installare su device di test
#    ├── Verificare funzionalità complete
#    ├── Testare clean uninstall (nessun residuo)
#    └── Validare auto-update se configurato
#
# 5. Deployment via Intune
#    ├── Intune → Apps → Windows → Add → Line-of-business app
#    ├── Caricare il .msix firmato
#    ├── Metadata estratti automaticamente dal manifest
#    └── Assegnare come Required o Available

# ═══════════════════════════════════════════════════════════════
# TIPO 6: Web Link
# ═══════════════════════════════════════════════════════════════
# Intune → Apps → Windows → Add → Web link
# Crea shortcut a URL sul desktop/Start
# Nessuna installazione, solo collegamento
# Utile per: intranet, webapp aziendali, portali
```

### SCCM — Application Deployment

```powershell
# SCCM supporta modelli più maturi per ambienti on-prem:
# - Applications (modello moderno con detection e requirements)
# - Packages (legacy, meno intelligenti ma più flessibili)
# - Task Sequences (per deploy complessi multi-step)

# Application con deployment type:
# 1. Software Library → Applications → Create Application
# 2. Detection method: MSI product code, file, registry, o script
# 3. Requirements: OS, RAM, CPU, disk
# 4. Dependencies: other applications
# 5. Deploy: Collection target, Purpose (Required/Available), Schedule

# Supercedence: la nuova app sostituisce automaticamente la vecchia
# Global Conditions: condizioni riutilizzabili per requirements

# User Device Affinity (UDA):
# ├── Associa utente primario al device
# ├── App "Available" appare nel Software Center dell'utente
# ├── Basata su login frequency o assegnazione manuale
# └── Rilevante per deployment user-centric
```

---

## Compliance Policy e Conditional Access

### Compliance Policies — Configurazione

```powershell
# Le compliance policy verificano che i dispositivi soddisfino i requisiti

# Intune → Devices → Compliance policies → Create policy → Windows 10+

# ═══════════════════════════════════════════════════════════════
# DEVICE HEALTH
# ═══════════════════════════════════════════════════════════════
# ├── Require BitLocker: Yes
# ├── Require Secure Boot: Yes
# ├── Require code integrity: Yes
# ├── Require TPM: Yes (version 2.0)
# └── Require Device Encryption: Yes

# ═══════════════════════════════════════════════════════════════
# DEVICE PROPERTIES
# ═══════════════════════════════════════════════════════════════
# ├── Minimum OS version: 10.0.22621 (Win11 22H2)
# ├── Maximum OS version: (opzionale, per bloccare beta)
# ├── Minimum OS build: (per patch specifiche)
# └── Valid operating system builds: (range accettabile)

# ═══════════════════════════════════════════════════════════════
# SYSTEM SECURITY
# ═══════════════════════════════════════════════════════════════
# ├── Password required: Yes
# ├── Minimum password length: 8
# ├── Required password type: Alphanumeric
# ├── Max minutes of inactivity before lock: 5
# ├── Password expiration (days): 90
# ├── Number of previous passwords: 5
# ├── Firewall: Required
# ├── Antivirus: Required
# ├── Antispyware: Required
# └── Microsoft Defender Antimalware: Required

# ═══════════════════════════════════════════════════════════════
# MICROSOFT DEFENDER FOR ENDPOINT
# ═══════════════════════════════════════════════════════════════
# ├── Risk score: Clear (nessun rischio) / Low / Medium
# └── Integrazione con Defender for Endpoint risk level

# ═══════════════════════════════════════════════════════════════
# AZIONI PER NON-COMPLIANCE
# ═══════════════════════════════════════════════════════════════
# Le azioni sono sequenziali con grace period:
#
# Giorno 0: Mark device as non-compliant
# Giorno 1: Send email notification all'utente
#   "Il tuo dispositivo LAPTOP-ABC non soddisfa i requisiti aziendali.
#    Problemi: BitLocker disabilitato.
#    Hai 3 giorni per risolvere prima del blocco accessi."
# Giorno 3: Remotely lock the device (opzionale)
# Giorno 7: Retire the device (rimozione dati aziendali)
#
# Personalizzabili per severity e tipo di non-compliance
```

### Custom Compliance Scripts

```powershell
# Gli script custom estendono la compliance oltre le policy native

# Intune → Devices → Compliance → Scripts → Add

# Lo script di discovery restituisce JSON con i valori da verificare:

# Esempio: verificare che specifici servizi siano attivi
$result = @{}
$services = @("WinDefend", "mpssvc", "EventLog", "BFE")
foreach ($svc in $services) {
    $status = (Get-Service -Name $svc -ErrorAction SilentlyContinue).Status
    $result[$svc] = if ($status -eq "Running") { $true } else { $false }
}
# Verificare ultimo reboot (non oltre 30 giorni)
$lastBoot = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
$daysSinceBoot = (New-TimeSpan -Start $lastBoot -End (Get-Date)).Days
$result["RebootWithin30Days"] = ($daysSinceBoot -le 30)

# Output JSON (richiesto da Intune):
$result | ConvertTo-Json -Compress
# Output: {"WinDefend":true,"mpssvc":true,"EventLog":true,
#          "BFE":true,"RebootWithin30Days":true}

# In Intune, il JSON viene mappato a regole compliance:
# ├── Operand: WinDefend
# ├── Operator: IsEquals
# ├── Value: true
# ├── Remediation message: "Windows Defender service must be running"
# └── Severity: Error (non-compliant) o Warning (informational)
```

### Custom Compliance — Architettura Avanzata

```
L'architettura custom compliance si basa su due componenti:
un discovery script PowerShell e un file JSON di validazione.

Discovery Script (PowerShell):
├── Eseguito sul device nel contesto SYSTEM
├── Limite dimensione: 1 MB per script
├── Limite output: 1 MB
├── Timeout: 10 minuti (Windows)
├── Deve restituire JSON compresso su STDOUT
├── Exit code 0 = esecuzione riuscita (i valori JSON vengono valutati)
├── Exit code != 0 = errore di esecuzione (device non valutabile)
├── Run in 64-bit PowerShell: abilitare per accedere a registry 64-bit
└── Frequenza valutazione: ogni 8 ore (allineata al sync Intune)

JSON Validation File (caricato in Intune):
├── Definisce le regole di validazione per l'output dello script
├── Massimo 20 regole per policy (best practice per performance)
├── Ogni regola specifica:
│   ├── SettingName   — chiave nel JSON restituito dallo script
│   ├── Operator      — IsEquals, NotEquals, GreaterThan, LessThan, etc.
│   ├── DataType      — Boolean, Int64, Double, String, DateTime, Version
│   ├── Operand       — valore atteso
│   ├── MoreInfoUrl   — link alla documentazione per l'utente
│   └── RemediationStrings — messaggio localizzato per non-compliance
│       ├── Language: it_IT
│       ├── Title: "Servizio Defender non attivo"
│       └── Description: "Avviare il servizio Windows Defender..."
└── Formato file JSON:

{
  "Rules": [
    {
      "SettingName": "WinDefend",
      "Operator": "IsEquals",
      "DataType": "Boolean",
      "Operand": true,
      "MoreInfoUrl": "https://docs.contoso.com/defender",
      "RemediationStrings": [
        {
          "Language": "it_IT",
          "Title": "Windows Defender disabilitato",
          "Description": "Il servizio Windows Defender deve essere attivo."
        }
      ]
    },
    {
      "SettingName": "DaysSinceLastReboot",
      "Operator": "LessThan",
      "DataType": "Int64",
      "Operand": 30,
      "MoreInfoUrl": "https://docs.contoso.com/reboot-policy",
      "RemediationStrings": [
        {
          "Language": "it_IT",
          "Title": "Riavvio necessario",
          "Description": "Il dispositivo non viene riavviato da oltre 30 giorni."
        }
      ]
    }
  ]
}

Workflow completo:
1. Caricare il discovery script in Intune → Compliance → Scripts
2. Caricare il JSON validation file nella compliance policy
3. Intune esegue lo script sul device → riceve JSON output
4. Il JSON viene confrontato con le regole nel validation file
5. Se tutte le regole passano → device compliant
6. Se una regola fallisce → device non-compliant con messaggio specifico
7. L'utente vede il messaggio di remediation nel Company Portal
8. Dopo la correzione, il prossimo sync rivaluta la compliance

Limiti e best practice:
├── ≤ 20 regole per policy per evitare rallentamenti
├── Script leggeri: evitare query WMI pesanti o scan disco completi
├── Testare script localmente prima del deployment
├── Usare ErrorAction SilentlyContinue per robustezza
├── Non mischiare custom compliance con compliance nativa per la stessa verifica
└── Documentare ogni script con versione, autore, e data ultimo aggiornamento
```

### Conditional Access Integration

```
La combinazione Compliance + Conditional Access è il cuore della sicurezza:

Entra ID → Security → Conditional Access → Create new policy

Esempio policy "Require compliant device for Office 365":

Assignments:
├── Users: All users
│   └── Exclude: Break-glass admin accounts, Service accounts
├── Cloud apps: Office 365 (include Exchange, SharePoint, Teams)
├── Conditions:
│   ├── Device platforms: Windows, iOS, Android
│   ├── Locations: All locations
│   │   └── Exclude: Trusted locations (rete aziendale)
│   └── Client apps: Browser, Mobile apps and desktop clients
│
Access controls:
├── Grant: Require device to be marked as compliant
│   └── O: Require Hybrid Azure AD joined device
├── For multiple controls: Require one of the selected
└── Session: Sign-in frequency: 12 hours

Ciclo risultante:
Device non compliant
→ Utente tenta di accedere a Exchange Online
→ Conditional Access blocca l'accesso
→ Utente vede: "Il tuo dispositivo non soddisfa i requisiti"
→ Link a Company Portal per risolvere
→ Utente abilita BitLocker / aggiorna OS / etc.
→ Intune rivaluta compliance
→ Device diventa compliant
→ Accesso ripristinato automaticamente
```

---

## Patch Management e Update Rings

### Windows Update for Business (WUfB)

```
WUfB sostituisce WSUS per la gestione degli aggiornamenti in ambienti cloud:

Tipi di aggiornamenti gestiti:
├── Quality Updates (mensili, security + bug fix)
│   ├── Patch Tuesday (secondo martedì del mese)
│   ├── Out-of-band (OOB) per fix critici
│   └── .NET Framework updates
├── Feature Updates (annuali, nuova versione Windows)
│   ├── Windows 11 23H2, 24H2, etc.
│   ├── 36 mesi di supporto (Enterprise)
│   └── Richiede compatibility testing
├── Driver Updates (opzionale)
│   ├── Firmware, driver hardware
│   ├── Approvazione manuale consigliata
│   └── Gestibile con driver update profiles
└── Microsoft Product Updates (altri prodotti MS)
    └── Office, .NET, Defender definitions

Intune → Devices → Windows 10/11 updates → Update rings
```

### Configurazione Update Rings

```
Update Ring tipico per un'organizzazione:

Ring 1: "Preview" (IT + Early Adopters, ~5% device)
├── Quality update deferral: 0 giorni (subito)
├── Feature update deferral: 0 giorni
├── Deadline: 2 giorni (auto-install dopo 2gg)
├── Grace period: 0 giorni
├── Active hours: 8:00 - 18:00
└── Scopo: test rapido, trovare problemi

Ring 2: "Pilot" (dipartimenti non critici, ~15% device)
├── Quality update deferral: 3 giorni
├── Feature update deferral: 14 giorni
├── Deadline: 5 giorni
├── Grace period: 2 giorni
├── Active hours: 8:00 - 18:00
└── Scopo: validazione su campione più ampio

Ring 3: "Broad" (maggioranza dei device, ~70% device)
├── Quality update deferral: 7 giorni
├── Feature update deferral: 30 giorni
├── Deadline: 5 giorni
├── Grace period: 2 giorni
├── Active hours: 8:00 - 18:00
└── Scopo: rollout generale dopo validazione

Ring 4: "Critical" (device mission-critical, ~10% device)
├── Quality update deferral: 14 giorni
├── Feature update deferral: 60 giorni
├── Deadline: 7 giorni
├── Grace period: 3 giorni
├── Active hours: definite per reparto
└── Scopo: stabilità massima, ultimo a ricevere

Impostazioni aggiuntive per tutti i ring:
├── Automatic update behavior: Auto install and restart at scheduled time
├── Pause updates: disponibile per emergenze (max 35 giorni)
├── Uninstall window: 10 giorni (per rollback quality updates)
├── Feature update uninstall: 30 giorni
└── Delivery Optimization: Enabled (peer-to-peer per banda)
```

### Feature Update Policies

```
Le Feature Update Policies controllano QUALE versione installare:

Intune → Devices → Windows 10/11 updates → Feature updates

Configurazione:
├── Feature update to deploy: Windows 11, version 24H2
├── Rollout options:
│   ├── Start date: 2026-03-01
│   ├── Gradual rollout: Yes
│   ├── Groups per day: 1000 device/giorno
│   └── End date: 2026-06-01
└── Assegnazione: gruppi di device

Safeguard Holds:
├── Microsoft blocca automaticamente device con problemi noti
├── Il device non riceve la feature update finché il hold è attivo
├── Visibile in Reports → Windows updates → Safeguard holds
└── Non bypassare: i hold esistono per prevenire problemi
```

### Driver Management via Intune

```
Intune → Devices → Windows 10/11 updates → Driver updates

Windows Driver Update Management:
├── Richiede: Windows 10/11 con WUfB abilitato
├── Mostra driver disponibili da Windows Update catalog
├── Admin approva/rifiuta driver specifici
├── Approval policies per gruppo di device
└── Reporting su installazione driver

Approval workflow:
1. Intune mostra driver disponibili per i device gestiti
2. Admin esamina: produttore, versione, device interessati
3. Approva driver per ring specifico
4. Driver distribuito al ring approvato
5. Monitoraggio installazione e problemi

Best practice:
├── NON approvare driver automaticamente
├── Testare su ring Preview prima
├── Driver firmware: approvare solo dopo test OEM
├── Escludere driver GPU per workstation creative (gestire manualmente)
└── Mantenere log delle approvazioni con data e responsabile
```

### Expedited Updates

```
Per patch di emergenza (zero-day, CVE critici):

Intune → Devices → Windows 10/11 updates → Quality updates

Expedited Quality Update:
├── Ignora i deferral configurati nei ring
├── Installa entro 24-48 ore
├── Forza restart se necessario (con notifica utente)
├── Usare SOLO per CVE critici attivamente sfruttati
└── Esempio: patch per PrintNightmare, Exchange zero-day

Configurazione:
├── Update: selezionare il KB specifico
├── Expedite: Yes
├── Days until forced reboot: 1 (per emergenze) o 2
└── Assegnazione: All devices (per CVE critici)
```

---

## Windows Autopatch

### Panoramica

```
Windows Autopatch è un servizio gestito da Microsoft che automatizza
gli aggiornamenti Windows per device enterprise.

Cosa gestisce:
├── Windows Quality Updates (mensili)
├── Windows Feature Updates (annuali)
├── Microsoft 365 Apps updates
├── Microsoft Edge updates
└── Microsoft Teams updates

Prerequisiti:
├── Licenza: Microsoft 365 E3/E5 o Windows 10/11 Enterprise E3/E5
├── Intune enrollment per tutti i device
├── Azure AD Join o Hybrid Azure AD Join
├── Windows 10/11 Enterprise o Education
├── Connettività Internet per Windows Update
└── Autopatch readiness assessment superato
```

### Ring Structure Automatica

```
Autopatch crea automaticamente 4 ring:

Ring              │ % Device │ Deferral  │ Scopo
──────────────────┼──────────┼───────────┼────────────────────────
Test              │ ~1%      │ 0 giorni  │ Validazione iniziale
First             │ ~5%      │ 1 giorno  │ Early adopter monitoring
Fast              │ ~15%     │ 6 giorni  │ Campione rappresentativo
Broad             │ ~79%     │ 9 giorni  │ Rollout generale

L'assegnazione ai ring è automatica:
├── Basata su gruppi Azure AD gestiti da Autopatch
├── Device assegnati automaticamente al ring appropriato
├── Admin può spostare device specifici tra ring
├── Service Health Dashboard per monitorare rollout
└── Rollback automatico se KPI degradati
```

### Reporting e Monitoraggio

```
Intune → Reports → Windows Autopatch

Dashboard disponibili:
├── Quality Update Status
│   ├── % device up-to-date per ring
│   ├── Device con errori di installazione
│   ├── Pause attive
│   └── Trend storico di compliance
├── Feature Update Status
│   ├── Progresso migrazione per ring
│   ├── Safeguard holds attivi
│   ├── Device esclusi e motivi
│   └── Timeline prevista per completamento
├── Microsoft 365 Apps
│   ├── Versione corrente per device
│   ├── Update channel distribution
│   └── Errori di aggiornamento
├── Service Health
│   ├── Incident attivi
│   ├── Advisory e comunicazioni
│   ├── Maintenance windows
│   └── Release notes per ogni update
└── Devices
    ├── Registered devices count
    ├── Not ready devices (e motivi)
    ├── Ring distribution
    └── Device health score
```

---

## Windows 365 Cloud PC — Gestione tramite Intune

### Panoramica Cloud PC

```
Windows 365 fornisce PC virtuali (Cloud PC) ospitati nel cloud Microsoft,
accessibili da qualsiasi dispositivo con browser o client Remote Desktop.
I Cloud PC vengono gestiti in Intune esattamente come endpoint fisici.

Edizioni:
├── Windows 365 Business    → per PMI, setup semplificato, < 300 utenti
├── Windows 365 Enterprise  → per grandi organizzazioni, Intune required
├── Windows 365 Frontline   → per lavoratori a turni, condivisione licenze
└── Windows 365 Government  → per enti governativi US (GCC)

Vantaggi chiave:
├── Provisioning in minuti, non ore
├── Accesso da qualsiasi device (thin client, tablet, BYOD)
├── Gestione unificata con device fisici in Intune
├── Dati nel cloud, non sul dispositivo locale
├── Scalabilità: aggiungere/rimuovere Cloud PC on-demand
└── Sicurezza: VBS, HVCI, Credential Guard abilitati per default
    sui Cloud PC con immagine Windows 11 gallery (dal 2024)
```

### Provisioning Policy

```
La provisioning policy orchestra la creazione automatica dei Cloud PC:

Intune → Devices → Manage Windows 365 Cloud PCs → Provision Cloud PCs
→ Provisioning policies → Create policy

Componenti della policy:
├── Nome e descrizione
├── Tipo di join: Azure AD Join (consigliato) o Hybrid Azure AD Join
├── Rete:
│   ├── Microsoft Hosted Network — nessuna configurazione Azure richiesta
│   │   ├── Ideale per: organizzazioni senza infrastruttura Azure
│   │   ├── Microsoft gestisce VNet, subnet, DNS
│   │   └── Limitazione: nessun accesso a risorse on-premises
│   └── Azure Network Connection (ANC)
│       ├── Il Cloud PC si connette a una VNet Azure esistente
│       ├── Accesso a risorse on-premises via VPN/ExpressRoute
│       ├── Richiede: subscription Azure, VNet, subnet dedicata
│       └── Necessario per: app LOB on-prem, Active Directory, file server
├── Immagine:
│   ├── Gallery Image — immagini Microsoft preconfigurate
│   │   ├── Windows 11 Enterprise + Microsoft 365 Apps
│   │   ├── Windows 11 Enterprise (senza Office)
│   │   └── Windows 10 Enterprise (per compatibilità)
│   └── Custom Image
│       ├── Immagine personalizzata caricata dall'organizzazione
│       ├── Include: app preinstallate, configurazioni custom, driver
│       ├── Formato: managed image in Azure Compute Gallery
│       └── Best practice: mantenere l'immagine leggera, usare Intune per app
├── Configurazione:
│   ├── Lingua e regione: it-IT, en-US, etc.
│   ├── Windows Autopilot Device Preparation (opzionale, da 2025)
│   │   └── Integra il provisioning Cloud PC con Autopilot v2
│   └── Servizi aggiuntivi: Microsoft Managed Desktop, etc.
└── Assegnazione: gruppi di utenti Azure AD

Sizing (configurazione hardware Cloud PC):
├── 2 vCPU / 4 GB RAM / 64 GB storage   → task leggeri, web browsing
├── 2 vCPU / 8 GB RAM / 128 GB storage  → uso generico, Office
├── 4 vCPU / 16 GB RAM / 128 GB storage → sviluppo, app pesanti
├── 8 vCPU / 32 GB RAM / 256 GB storage → data analysis, ingegneria
└── 16 vCPU / 64 GB RAM / 512 GB storage → workstation virtuale premium

Regioni (supporto geografico):
├── Geography level (Level 1) — intera area geografica (es. Europa)
├── Region group level (Level 2) — sotto-gruppi specifici (es. Europa Occidentale)
└── Single region (Level 3) — regione Azure specifica (es. West Europe)
```

### Gestione Cloud PC in Intune

```
I Cloud PC appaiono nella console Intune come dispositivi standard
e supportano le stesse funzionalità di gestione:

Funzionalità supportate:
├── Configuration Profiles      → stesse policy dei device fisici
├── Compliance Policies         → stesse regole di compliance
├── Conditional Access          → accesso condizionale identico
├── Application Deployment      → Win32, Store, LOB, Microsoft 365 Apps
├── Windows Update Rings        → aggiornamenti gestiti via WUfB
├── Endpoint Security           → Defender, Firewall, BitLocker, ASR
├── Remediations                → script di detection e remediation
├── Remote Actions              → restart, reprovision, resize
└── Endpoint Analytics          → performance e reliability

Azioni specifiche Cloud PC:
├── Reprovision — ricrea il Cloud PC da zero (perde dati utente)
├── Resize — cambia configurazione hardware (vCPU, RAM, storage)
├── Restore — ripristina a uno snapshot precedente
│   ├── Snapshot automatici ogni 12 ore (configurabile)
│   ├── Retention: 10 punti di ripristino
│   └── Utile per: corruzione dati, problemi post-update
├── Place in grace period — sospende il Cloud PC (es. utente in congedo)
└── Bulk actions — azioni su multipli Cloud PC simultaneamente

Cloud PC Monitoring (preview dal 2025):
├── Dashboard integrato per salute e performance dei Cloud PC
├── Connection health trends e affidabilità
├── Insight a livello utente e dispositivo
├── Latenza di connessione e qualità della sessione
└── Alerting proattivo per problemi ricorrenti
```

---

## Endpoint Analytics

### Panoramica

```
Endpoint Analytics fornisce visibilità sulla performance e
l'esperienza utente dei dispositivi gestiti.

Intune → Reports → Endpoint analytics

Componenti principali:
├── Startup Performance
├── Application Reliability
├── Proactive Remediations
├── Device Scoping (per filtrare per reparto/sede)
└── Work From Anywhere (score di readiness)
```

### Startup Performance

```
Misura il tempo di avvio dei dispositivi e identifica i bottleneck:

Metriche:
├── Boot time (total)
│   ├── BIOS time (firmware → OS loader)
│   ├── Core boot time (OS loader → desktop)
│   ├── Core logon time (credenziali → desktop interattivo)
│   └── Group Policy processing time
├── Desktop responsive time
│   └── Tempo prima che il desktop sia utilizzabile
├── Restart frequency
│   └── Quante volte il device si riavvia al giorno
└── Startup processes impact
    ├── Lista processi che rallentano il boot
    ├── Impatto per processo (basso/medio/alto)
    └── Suggerimento: disabilitare o ottimizzare

Score:
├── 0-50: Poor → intervento necessario
├── 50-70: Needs improvement → ottimizzare
├── 70-100: Good → nella norma
└── Baseline: confronto con organizzazioni simili

Azioni comuni:
├── Disabilitare startup item non necessari
├── Aggiornare driver storage (NVMe/SSD)
├── Verificare BIOS version (aggiornare se lento)
├── Rimuovere software bloatware preinstallato
└── Valutare hardware replacement se > 5 anni
```

### Application Reliability

```
Monitora crash e hang delle applicazioni:

Dati raccolti:
├── App crash count (per app, per device, per OS version)
├── App hang count (not responding > 5 secondi)
├── Mean time to failure (MTTF)
├── Crash-free device percentage
├── Trend: miglioramento o peggioramento nel tempo
└── Correlazione: crash dopo aggiornamento specifico?

Drill down:
├── App name + version
├── Crash count (ultimi 14 giorni)
├── Devices affected
├── OS version correlation
├── Error module (DLL che causa il crash)
└── Exception code

Azioni:
├── Aggiornare l'app alla versione più recente
├── Contattare il vendor per fix noti
├── Creare proactive remediation per workaround
├── Valutare sostituzione dell'app se sistematicamente instabile
└── Correlare con Feature Update rollout per regression
```

### Proactive Remediations

```
Script che rilevano e correggono problemi automaticamente:

Intune → Devices → Remediations → Create script package

Struttura:
├── Detection script: verifica se il problema esiste
│   └── Exit code 1 = problema trovato, 0 = OK
├── Remediation script: corregge il problema
│   └── Exit code 0 = corretto con successo
├── Schedule: giornaliero, settimanale, orario
├── Scope: User context o System context
└── Assignment: gruppi di device

Esempio built-in Microsoft:
├── Clear stale certificates
├── Disable Office macros from the internet
├── Remove expired certificates
├── Update stale Group Policy
└── Restart stopped Windows Update service
```

---

## Defender for Endpoint — Regole ASR via Intune

### Panoramica ASR

```
Le regole Attack Surface Reduction (ASR) bloccano comportamenti comuni
sfruttati da malware e attacchi avanzati. Sono parte di Microsoft Defender
for Endpoint e vengono distribuite e gestite centralmente tramite Intune.

Intune → Endpoint security → Attack surface reduction → Create policy
Platform: Windows → Profile: Attack Surface Reduction Rules

Le regole ASR non sostituiscono l'antivirus: lavorano a livello di
comportamento, intercettando azioni sospette prima che il payload venga
eseguito. Ogni regola ha un GUID univoco e può essere impostata in
tre modalità:
├── Disabled (0)  — Regola disattivata
├── Block (1)     — Regola attiva, blocca l'azione
├── Audit (2)     — Registra l'evento senza bloccare (per test)
└── Warn (6)      — Mostra avviso all'utente, consente override
```

### Regole ASR Principali

```
Le regole più rilevanti per ambienti enterprise:

Categoria: Office e Macro
├── Block all Office applications from creating child processes
│   GUID: d4f940ab-401b-4efc-aadc-ad5f3c50688a
│   Blocca Word, Excel, PowerPoint dall'avviare processi figlio
│   (es. PowerShell lanciato da una macro VBA malevola)
├── Block Office applications from creating executable content
│   GUID: 3b576869-a4ec-4529-8536-b80a7769e899
│   Impedisce la scrittura di file .exe/.dll da applicazioni Office
├── Block Office applications from injecting code into other processes
│   GUID: 75668c1f-73b5-4cf0-bb93-3ecf5cb7cc84
│   Previene tecniche di code injection da processo Office
└── Block Win32 API calls from Office macros
    GUID: 92e97fa1-2edf-4476-bdd6-9dd0b4dddc7b
    Blocca chiamate API Win32 dirette da macro VBA

Categoria: Script e Processi
├── Block execution of potentially obfuscated scripts
│   GUID: 5beb7efe-fd9a-4556-801d-275e5ffc04cc
│   Rileva e blocca script PowerShell/VBScript/JavaScript offuscati
├── Block JavaScript or VBScript from launching downloaded executable
│   GUID: d3e037e1-3eb8-44c8-a917-57927947596d
│   Previene download-and-execute via script browser
├── Block process creations originating from PSExec and WMI commands
│   GUID: d1e49aac-8f56-4280-b9ba-993a6d77406c
│   Contrasta lateral movement via PSExec/WMI
└── Use advanced protection against ransomware
    GUID: c1db55ab-c21a-4637-bb3f-a12568109d35
    Euristica avanzata per bloccare pattern ransomware

Categoria: Credential e Persistence
├── Block credential stealing from Windows LSASS
│   GUID: 9e6c4e1f-7d60-472f-ba1a-a39ef669e4b2
│   Protegge il processo lsass.exe da dump delle credenziali
│   (equivalente a Credential Guard per device senza VBS)
├── Block persistence through WMI event subscription
│   GUID: e6db77e5-3df2-4cf1-b95a-636979351e5b
│   Blocca la creazione di eventi WMI permanenti per persistence
└── Block untrusted and unsigned processes that run from USB
    GUID: b2b3f03d-6a65-4f7b-a9c7-1c7ef74a9ba4
    Impedisce l'esecuzione di binari non firmati da dispositivi USB

Categoria: Email e Download
├── Block executable content from email client and webmail
│   GUID: be9ba2d9-53ea-4cdc-84e5-9b1eeee46550
│   Blocca esecuzione di allegati eseguibili direttamente da Outlook
└── Block executable files from running unless they meet criteria
    GUID: 01443614-cd74-433a-b99e-2ecdc07bfc25
    Blocca eseguibili che non soddisfano criteri di prevalenza/età/trust
```

### Deployment Strategy — Rollout Graduale

```
Strategia consigliata per il rollout delle regole ASR:

Fase 1: Inventory (Settimana 1-2)
├── Abilitare TUTTE le regole in modalità Audit
├── Assegnare a tutti i device gestiti
├── Raccogliere eventi in Defender portal → Reports → ASR
├── Identificare false positive per ogni regola
└── Documentare applicazioni legittime che triggerano regole

Fase 2: Esclusioni (Settimana 3-4)
├── Creare esclusioni per file path, processo, o certificato
│   Intune → Endpoint security → ASR → Exclusions
├── Esclusioni supportano wildcard solo via Intune (non SCCM)
├── Formato: C:\ProgramData\App\*.exe o per processo
├── Limitare le esclusioni al minimo necessario
└── Documentare ogni esclusione con giustificazione

Fase 3: Enforcement Progressivo (Mese 2-3)
├── Spostare regole a basso impatto in Block:
│   1. Block executable content from email
│   2. Block untrusted processes from USB
│   3. Block Office from creating child processes
├── Monitorare per 2 settimane prima di proseguire
├── Spostare regole a medio impatto in Block:
│   4. Block obfuscated scripts
│   5. Block credential stealing from LSASS
│   6. Block ransomware protection
└── Mantenere in Audit regole ad alto impatto fino a validazione

Fase 4: Full Enforcement (Mese 3+)
├── Tutte le regole in Block (o Warn per eccezioni)
├── Monitoraggio continuo nel Defender portal
├── Review trimestrale delle esclusioni
└── Allineamento con security baselines Microsoft

Merge behavior tra policy multiple:
├── Impostazioni non in conflitto vengono unite (superset)
├── Impostazioni in conflitto: la più restrittiva vince
├── Consiglio: una sola ASR policy per device per evitare ambiguità
└── Usare Scope Tags per separare ambienti
```

### Monitoraggio ASR nel Defender Portal

```
Microsoft Defender portal → Reports → Attack surface reduction

Dashboard ASR:
├── Detection count per regola (ultime 24h / 7gg / 30gg)
├── Top blocked rules con trend
├── Device con più detection
├── Audit vs Block event distribution
├── Esclusioni applicate e frequenza di match
└── Correlation con alert Defender for Endpoint

Advanced Hunting (KQL) per analisi dettagliata:
DeviceEvents
| where ActionType startswith "Asr"
| summarize count() by ActionType, FileName
| order by count_ desc

Integrazione con Intune:
├── Compliance policy può richiedere Defender risk score "Clear"
├── Device con ASR violation → risk score aumenta
├── Conditional Access blocca device ad alto rischio
└── Ciclo: ASR block → Defender alert → Risk score → CA block
```

---

## Endpoint Privilege Management (EPM)

### Panoramica EPM

```
Endpoint Privilege Management è un componente dell'Intune Suite che consente
agli utenti standard di eseguire attività che normalmente richiedono privilegi
di amministratore, senza concedere admin locale permanente.

Principio: utenti standard per default, elevazione controllata per eccezione.

Intune → Endpoint security → Endpoint Privilege Management

Prerequisiti:
├── Licenza: Intune Suite o Intune EPM add-on standalone
├── Windows 10/11 (22H2+)
├── Device registrato in Intune (Azure AD Join o Hybrid)
├── Intune Management Extension installata
└── Non compatibile con altri strumenti PAM di terze parti sul medesimo endpoint

Componenti:
├── Elevation Settings Policy    → Configurazione base del client EPM
├── Elevation Rules Policy       → Regole che definiscono quali file possono essere elevati
├── Support Approved Elevations  → Workflow di approvazione manuale
└── EPM Overview Dashboard       → Visibilità su elevazioni gestite e non gestite
```

### Tipi di Elevazione

```
EPM supporta diversi tipi di elevazione, ciascuno adatto a scenari differenti:

1. Automatic (Elevazione Automatica)
├── Il file viene elevato senza interazione utente
├── Basato su regole definite dall'admin (hash, certificato, path)
├── Ideale per: installer approvati, tool IT, aggiornamenti noti
├── Rischio: medio — richiede regole precise per evitare abusi
└── Nessuna conferma richiesta, trasparente per l'utente

2. User Confirmed (Conferma Utente)
├── L'utente vede un prompt che chiede conferma prima dell'elevazione
├── Può richiedere business justification (testo libero)
├── Ideale per: operazioni occasionali con consapevolezza dell'utente
├── Rischio: basso — l'utente deve attivamente confermare
└── L'admin vede la justification nei report

3. Support Approved (Approvazione Supporto)
├── L'utente richiede l'elevazione, che entra in coda di approvazione
├── Un admin Intune approva o rifiuta la richiesta
├── Il file può essere eseguito elevato solo dopo approvazione
├── Ideale per: software non previsto, installazioni eccezionali
├── Approvazione valida per un periodo limitato (configurabile)
├── Workflow: utente → richiesta → admin review → approve/deny → esecuzione
└── Copilot in Intune può assistere nella valutazione del rischio dell'app

4. Elevate as Current User (da ottobre 2025)
├── L'elevazione avviene nel contesto dell'utente connesso
├── Differenza dal default: normalmente EPM usa un account virtuale
├── Necessario per app che accedono a profilo utente, variabili
│   d'ambiente, percorsi personalizzati (es. %APPDATA%)
└── Utile per: installer che scrivono in HKCU o profilo utente
```

### Elevation Rules — Configurazione

```
Le elevation rules definiscono quali file possono essere elevati e come:

Intune → Endpoint security → EPM → Elevation Rules Policy → Create

Criteri di identificazione file:
├── File Hash (SHA-256)
│   ├── Identificazione più sicura e specifica
│   ├── Cambia ad ogni aggiornamento dell'app → manutenzione alta
│   └── Ideale per: installer specifici, file critici
├── Certificate (firma digitale)
│   ├── Tutti i file firmati da quel certificato sono coperti
│   ├── Persiste attraverso aggiornamenti dell'app
│   ├── Rischio: certificati rubati o troppo ampi
│   └── Ideale per: software vendor trusted (Microsoft, Adobe)
├── File Path
│   ├── Tutti i file in un percorso specifico
│   ├── Meno sicuro: un attaccante potrebbe inserire file nel path
│   ├── Combinare con Certificate o Hash per sicurezza
│   └── Ideale per: cartelle controllate da IT
└── File Name (nome file, con o senza versione)
    ├── Complementare ad altri criteri
    └── Non usare come unico criterio di match

Estensioni supportate:
├── .exe — Eseguibili standard
├── .msi — Installer Windows (aggiunto nel 2024)
├── .ps1 — Script PowerShell (aggiunto nel 2024)
└── Altre estensioni in fase di valutazione futura

Configurazione regola:
├── File identification: hash / cert / path / combinazione
├── Elevation type: Automatic / User Confirmed / Support Approved
├── Child process behavior: Allow / Deny / Allow by rule
│   (controllare se il processo elevato può avviare processi figlio)
├── Validation: verificare il file prima dell'elevazione
└── Assignment: gruppi di device o utenti
```

### EPM Dashboard e Reporting

```
EPM Overview Dashboard (disponibile da ottobre 2025):
├── Managed Elevations — elevazioni gestite da regole EPM
│   ├── Count per tipo (automatic, user confirmed, support approved)
│   ├── Top file elevati
│   └── Trend nel tempo
├── Unmanaged Elevations — elevazioni senza regola corrispondente
│   ├── File che gli utenti tentano di elevare senza match
│   ├── Utile per creare nuove regole basate su domanda reale
│   └── Priorità: analizzare i file più frequentemente richiesti
├── Devices with Local Admin — device con account admin locale attivo
│   ├── Target: ridurre progressivamente fino a zero
│   └── Monitorare variazioni (nuovi admin non autorizzati)
├── Pending Approvals — richieste support approved in attesa
│   ├── Tempo medio di approvazione
│   ├── Richieste scadute
│   └── Admin che approvano di più
└── Elevation Trends — grafico storico delle elevazioni

Integrazione con Copilot in Intune:
├── Copilot analizza le richieste di elevazione support approved
├── Valuta il rischio dell'applicazione (reputazione, firma, prevalenza)
├── Suggerisce approve/deny con motivazione
└── Riduce il carico sugli admin per decisioni ripetitive
```

---

## PowerShell Scripts e Remediation

### Script Deployment via Intune

```powershell
# Intune → Devices → Scripts → Platform scripts → Add (Windows 10+)

# Impostazioni script:
# ├── Run script in 64-bit PowerShell: Yes (consigliato)
# ├── Run script using logged-on credentials: No (usa SYSTEM)
# ├── Enforce script signature check: Yes (in produzione)
# ├── Run script in 64-bit PowerShell host: Yes
# └── Assignment: gruppi di device o utenti

# NOTA: gli script Intune vengono eseguiti UNA VOLTA per device
# (a meno che il content hash cambi, allora riesegue)
# Per esecuzioni ricorrenti → usare Proactive Remediations

# ═══════════════════════════════════════════════════════════════
# ESEMPIO 1: Configurare power settings
# ═══════════════════════════════════════════════════════════════
# Timeout schermo e sleep per device aziendali
powercfg /change standby-timeout-ac 30
powercfg /change standby-timeout-dc 15
powercfg /change monitor-timeout-ac 10
powercfg /change monitor-timeout-dc 5
powercfg /change hibernate-timeout-ac 0
powercfg /change hibernate-timeout-dc 60
Write-Output "Power settings configured successfully"
exit 0

# ═══════════════════════════════════════════════════════════════
# ESEMPIO 2: Registrare event log custom per audit
# ═══════════════════════════════════════════════════════════════
$logName = "CorpEndpointMgmt"
if (-not [System.Diagnostics.EventLog]::SourceExists($logName)) {
    New-EventLog -LogName "Application" -Source $logName
}
Write-EventLog -LogName "Application" -Source $logName `
    -EventId 1000 -EntryType Information `
    -Message "Intune script executed: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
exit 0

# ═══════════════════════════════════════════════════════════════
# ESEMPIO 3: Pulizia disco automatica
# ═══════════════════════════════════════════════════════════════
$freeSpaceGB = [math]::Round(
    (Get-PSDrive C).Free / 1GB, 2
)
if ($freeSpaceGB -lt 20) {
    # Pulizia temp files
    Remove-Item "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
    # Pulizia Windows Update cache
    Stop-Service wuauserv -Force
    Remove-Item "C:\Windows\SoftwareDistribution\Download\*" `
        -Recurse -Force -ErrorAction SilentlyContinue
    Start-Service wuauserv
    # Pulizia profili temp
    Get-ChildItem "C:\Users" -Directory |
        Where-Object { $_.Name -like "TEMP*" -or $_.Name -like "*.000" } |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Output "Disk cleanup completed. Previous free space: ${freeSpaceGB}GB"
}
exit 0
```

### Proactive Remediations — Esempi Avanzati

```powershell
# ═══════════════════════════════════════════════════════════════
# REMEDIATION 1: Verificare e riparare Windows Update
# ═══════════════════════════════════════════════════════════════

# --- Detection Script ---
$wuService = Get-Service wuauserv -ErrorAction SilentlyContinue
$bitsService = Get-Service bits -ErrorAction SilentlyContinue
$lastUpdate = (New-Object -ComObject Microsoft.Update.AutoUpdate).Results
$lastInstall = $lastUpdate.LastInstallationSuccessDate
$daysSinceUpdate = (New-TimeSpan -Start $lastInstall -End (Get-Date)).Days

if ($wuService.Status -ne "Running" -or
    $bitsService.Status -ne "Running" -or
    $daysSinceUpdate -gt 30) {
    Write-Output "WU issue detected: Service=$($wuService.Status), " +
                 "BITS=$($bitsService.Status), DaysSinceUpdate=$daysSinceUpdate"
    exit 1  # Problema trovato
}
Write-Output "Windows Update healthy"
exit 0  # OK

# --- Remediation Script ---
# Riavviare servizi WU
$services = @("wuauserv", "bits", "cryptsvc", "msiserver")
foreach ($svc in $services) {
    Stop-Service $svc -Force -ErrorAction SilentlyContinue
}
# Reset Windows Update components
Remove-Item "C:\Windows\SoftwareDistribution" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "C:\Windows\System32\catroot2" -Recurse -Force -ErrorAction SilentlyContinue
foreach ($svc in $services) {
    Start-Service $svc -ErrorAction SilentlyContinue
}
# Trigger scan
(New-Object -ComObject Microsoft.Update.AutoUpdate).DetectNow()
Write-Output "Windows Update components reset and scan triggered"
exit 0

# ═══════════════════════════════════════════════════════════════
# REMEDIATION 2: Verificare certificati scaduti
# ═══════════════════════════════════════════════════════════════

# --- Detection Script ---
$expiredCerts = Get-ChildItem Cert:\LocalMachine\My |
    Where-Object { $_.NotAfter -lt (Get-Date) }
if ($expiredCerts.Count -gt 0) {
    $list = ($expiredCerts | ForEach-Object {
        "$($_.Subject) expired $($_.NotAfter.ToString('yyyy-MM-dd'))"
    }) -join "; "
    Write-Output "Expired certs found: $list"
    exit 1
}
Write-Output "No expired certificates"
exit 0

# --- Remediation Script ---
$expired = Get-ChildItem Cert:\LocalMachine\My |
    Where-Object { $_.NotAfter -lt (Get-Date) }
$removed = 0
foreach ($cert in $expired) {
    try {
        Remove-Item $cert.PSPath -Force
        $removed++
    } catch {
        Write-Output "Failed to remove: $($cert.Subject) - $($_.Exception.Message)"
    }
}
Write-Output "Removed $removed expired certificates"
exit 0

# ═══════════════════════════════════════════════════════════════
# REMEDIATION 3: Verificare configurazione DNS
# ═══════════════════════════════════════════════════════════════

# --- Detection Script ---
$expectedDNS = @("10.10.1.1", "10.10.1.2")
$adapters = Get-DnsClientServerAddress -AddressFamily IPv4 |
    Where-Object { $_.InterfaceAlias -notlike "*Loopback*" -and
                   $_.InterfaceAlias -notlike "*VPN*" }
$issues = @()
foreach ($adapter in $adapters) {
    $currentDNS = $adapter.ServerAddresses
    if ($currentDNS -and ($currentDNS -notcontains $expectedDNS[0])) {
        $issues += "$($adapter.InterfaceAlias): $($currentDNS -join ',')"
    }
}
if ($issues.Count -gt 0) {
    Write-Output "DNS mismatch: $($issues -join '; ')"
    exit 1
}
Write-Output "DNS configuration correct"
exit 0

# --- Remediation Script ---
$primaryDNS = "10.10.1.1"
$secondaryDNS = "10.10.1.2"
$adapters = Get-NetAdapter | Where-Object { $_.Status -eq "Up" }
foreach ($adapter in $adapters) {
    Set-DnsClientServerAddress -InterfaceIndex $adapter.ifIndex `
        -ServerAddresses @($primaryDNS, $secondaryDNS)
}
Clear-DnsClientCache
Write-Output "DNS reconfigured to $primaryDNS, $secondaryDNS"
exit 0
```

### Custom Compliance Discovery Script

```powershell
# Custom compliance script per verifiche avanzate non disponibili nativamente

# Intune → Devices → Compliance → Scripts → Add

# Questo script verifica:
# 1. Servizi di sicurezza attivi
# 2. Ultime definizioni Defender aggiornate
# 3. Nessun software proibito installato
# 4. Crittografia disco attiva
# 5. Ultimo reboot entro 30 giorni

$compliance = @{}

# Check 1: Servizi critici
$requiredServices = @{
    "WinDefend" = "Windows Defender Antivirus"
    "mpssvc"    = "Windows Firewall"
    "EventLog"  = "Windows Event Log"
    "BFE"       = "Base Filtering Engine"
}
foreach ($svc in $requiredServices.GetEnumerator()) {
    $status = (Get-Service -Name $svc.Key -ErrorAction SilentlyContinue).Status
    $compliance["Service_$($svc.Key)"] = ($status -eq "Running")
}

# Check 2: Defender definitions freshness
$defenderStatus = Get-MpComputerStatus -ErrorAction SilentlyContinue
if ($defenderStatus) {
    $defAge = (New-TimeSpan -Start $defenderStatus.AntivirusSignatureLastUpdated `
        -End (Get-Date)).Days
    $compliance["DefenderDefinitionsUpToDate"] = ($defAge -le 3)
    $compliance["DefenderDefinitionAgeDays"] = $defAge
} else {
    $compliance["DefenderDefinitionsUpToDate"] = $false
}

# Check 3: Software proibito
$prohibited = @("BitTorrent", "TeamViewer", "AnyDesk")
$installed = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*" `
    -ErrorAction SilentlyContinue |
    Where-Object { $_.DisplayName -and
        ($prohibited | Where-Object { $_.DisplayName -like "*$_*" }) }
$compliance["NoProhibitedSoftware"] = ($null -eq $installed)

# Check 4: BitLocker
$bitlocker = Get-BitLockerVolume -MountPoint "C:" -ErrorAction SilentlyContinue
$compliance["BitLockerEnabled"] = (
    $bitlocker -and $bitlocker.ProtectionStatus -eq "On"
)

# Check 5: Ultimo reboot
$lastBoot = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
$daysSinceBoot = [math]::Round(
    (New-TimeSpan -Start $lastBoot -End (Get-Date)).TotalDays, 0
)
$compliance["RebootWithin30Days"] = ($daysSinceBoot -le 30)
$compliance["DaysSinceLastReboot"] = $daysSinceBoot

# Output JSON (formato richiesto da Intune)
return $compliance | ConvertTo-Json -Compress
```

---

## Matrice Decisionale di Deployment

### Quale Strumento Usare?

```
Scenario                              │ Strumento Consigliato
──────────────────────────────────────┼──────────────────────────────────────
Nuovo device, utente remoto           │ Autopilot User-Driven + Intune
Nuovo device, kiosk/shared            │ Autopilot Self-Deploying
Nuovo device, VIP/executive           │ Autopilot Pre-Provisioning
Device esistente, domain-joined       │ Co-management → migrazione a Intune
Device legacy (Win 7/8.1)            │ SCCM (no Intune support)
BYOD smartphone/tablet                │ MAM (App Protection Policies)
BYOD laptop personale                 │ MAM-only o Azure AD Register + MAM
Migrazione OS in massa                │ SCCM OSD Task Sequences
Patch management cloud                │ WUfB Update Rings via Intune
Patch management on-prem              │ SCCM SUP + WSUS
App deployment cloud                  │ Intune Win32 / Microsoft Store
App deployment on-prem complesso      │ SCCM Applications + Packages
Aggiornamenti automatici gestiti      │ Windows Autopatch
Compliance + accesso condizionale     │ Intune Compliance + Conditional Access
Monitoraggio proattivo                │ Endpoint Analytics + Remediations
VDI / Azure Virtual Desktop           │ MSIX App Attach + Intune
Driver management                     │ Intune Driver Updates o SCCM DP
```

### Matrice per Dimensione Organizzazione

```
Dimensione    │ Architettura Consigliata
──────────────┼─────────────────────────────────────────────
< 100 device  │ Intune standalone + Autopilot
              │ Nessun SCCM necessario
              │ MAM per BYOD
              │ WUfB per patch
──────────────┼─────────────────────────────────────────────
100-1000      │ Intune + Autopilot (cloud-first)
              │ SCCM solo se legacy significativo
              │ Co-management se SCCM esistente
              │ Autopatch per aggiornamenti
──────────────┼─────────────────────────────────────────────
1000-10000    │ Co-management (SCCM + Intune)
              │ Migrazione graduale a Intune
              │ CMG per client remoti
              │ Update Rings per patch
──────────────┼─────────────────────────────────────────────
> 10000       │ Co-management con CAS
              │ CMG + Cloud DP
              │ Intune per nuovi device
              │ SCCM per OS deployment legacy
              │ Autopatch per aggiornamenti automatici
```

---

## Best Practices

1. **Cloud-first per nuovi device**: Autopilot + Intune per ogni nuovo dispositivo. SCCM per device legacy
2. **Zero-touch deployment**: Autopilot elimina la necessità di imaging manuale. L'OEM spedisce direttamente all'utente
3. **Compliance + Conditional Access**: la combinazione è potente — solo dispositivi conformi accedono alle risorse
4. **Dynamic groups**: in Azure AD, usare gruppi dinamici per assegnare automaticamente policy basate su proprietà device (OS, modello, reparto)
5. **App packaging standardizzato**: creare un repository di .intunewin testati. Documentare install/uninstall/detection per ogni app
6. **Monitorare compliance**: dashboard Intune per percentuale compliance. Target: 95%+ compliant
7. **Layered security**: Compliance + Conditional Access + Defender for Endpoint + App Protection = difesa in profondità
8. **Naming convention**: standardizzare i nomi dei profili — es. `[Platform]-[Type]-[Scope]-[Description]` come `WIN-COMP-AllUsers-BaselineSecurity`
9. **Change management**: testare ogni nuova policy su ring Preview prima del rollout ampio. Mai applicare direttamente a "All Devices"
10. **Documentazione**: mantenere un registro di tutti i profili, policy, e app con owner, scopo, e gruppi target
11. **Proactive Remediations**: usare per fix automatici dei problemi ricorrenti, non come sostituto di configurazioni corrette
12. **Backup dei profili**: esportare periodicamente le configurazioni Intune via Graph API per disaster recovery
13. **Scope Tags**: usare per delegare l'amministrazione a team regionali senza accesso globale
14. **Audit regolare**: verificare mensilmente le policy orfane, i profili non assegnati, e i device stale (inattivi > 90 giorni)

---

## Troubleshooting

**"Autopilot non parte, mostra OOBE standard"** → Il dispositivo non è registrato in Autopilot, o il profilo non è assegnato. Verificare: hardware hash importato, profilo assegnato al gruppo corretto, dispositivo connesso a Internet durante OOBE. Controllare che il profilo sia sincronizzato: Intune → Devices → Windows enrollment → Devices → selezionare il device → Profile status.

**"App Intune non si installa"** → Verificare in Intune → Apps → Monitor → App install status. Sul device: `C:\ProgramData\Microsoft\IntuneManagementExtension\Logs\IntuneManagementExtension.log`. Cause comuni: detection rule errata, dipendenza mancante, install command sbagliato, return code non mappato.

**"Device non compliant ma tutto sembra OK"** → Forzare sync da Intune. Verificare: data ultimo check-in, quale policy fallisce (drill down nel report compliance). L'evaluation potrebbe essere in ritardo (fino a 8 ore). Controllare: Intune → Devices → selezionare device → Device compliance → per-policy status.

**"SCCM client non comunica"** → Verificare servizio CcmExec (`Get-Service CcmExec`). Log: `C:\Windows\CCM\Logs\`. Verificare connettività al Management Point. Reinstallare client se necessario: `ccmsetup.exe /remediate:client`. Controllare: `C:\Windows\CCM\Logs\ClientLocation.log` per problemi di boundary group.

**"Configuration Profile in stato Error"** → Intune → Devices → selezionare device → Device configuration → profilo in errore → Per-setting status. Cause comuni: conflitto con altro profilo, impostazione non supportata dalla versione OS, CSP non disponibile sul device.

**"Enrollment fallisce con errore 80180018"** → Limite dispositivi raggiunto per l'utente. Verificare: Intune → Devices → Enrollment restrictions → Device limit. Default: 5. Aumentare o rimuovere device vecchi dell'utente.

**"Enrollment fallisce con errore 800700032"** → MDM Terms of Use non accettati. L'utente deve accettare i termini durante l'enrollment. Verificare che i Terms of Use siano configurati correttamente in Intune.

**"Autopilot ESP bloccato su 'Identifying' per oltre 30 minuti"** → Problemi di connettività. Verificare: accesso a `*.manage.microsoft.com`, `enrollment.manage.microsoft.com`, `login.microsoftonline.com`. Firewall o proxy potrebbe bloccare il traffico. Controllare se il profilo Autopilot è assegnato.

**"Windows Update non funziona su device Intune"** → Verificare che il device sia nel ring corretto. Controllare: Settings → Windows Update → Update history. Log: `C:\Windows\Logs\WindowsUpdate\WindowsUpdate.log`. Se WUfB configurato, WSUS locale deve essere disabilitato (GPO potrebbe interferire).

**"Win32 app in stato 'Downloading' per ore"** → IME (Intune Management Extension) potrebbe essere bloccato. Riavviare il servizio: `Restart-Service IntuneManagementExtension`. Verificare spazio disco disponibile. Controllare proxy/firewall per accesso a `swda01-mscdn.manage.microsoft.com`.

**"Co-management non si attiva"** → Verificare: Azure AD hybrid join completato (`dsregcmd /status` → AzureAdJoined: YES + DomainJoined: YES). Controllare log: `C:\Windows\CCM\Logs\CoManagementHandler.log`. Verificare che l'utente abbia licenza Intune.

**"Conditional Access blocca utenti legittimi"** → Verificare: Entra ID → Sign-in logs → filtrare per utente → Conditional Access tab → quale policy blocca. Cause comuni: device non compliant (check compliance status), MFA non completato, location non trusted.

**"Profilo Wi-Fi non si connette"** → Il certificato associato potrebbe non essere deployato. Verificare: il profilo Trusted Root CA è installato, il profilo SCEP/PKCS ha generato il certificato (certlm.msc → Personal → Certificates). NDES/Connector deve essere raggiungibile.

**"BitLocker compliance fallisce ma BitLocker è attivo"** → Verificare il metodo di cifratura. La policy potrebbe richiedere XTS-AES-256, ma il device usa AES-128. Controllare: `manage-bde -status C:`. Per cambiare: decrypt e re-encrypt con metodo corretto.

**"Script Intune non viene eseguito"** → Gli script vengono eseguiti una sola volta per device. Se il contenuto non è cambiato, non riesegue. Per rieseguire: modificare lo script (anche un commento) per cambiare il content hash. Verificare: Intune → Devices → Scripts → selezionare script → Device status.

**"Proactive Remediation detection OK ma remediation fallisce"** → Lo script di remediation viene eseguito nel contesto sbagliato (User vs System). Verificare i permessi necessari. Controllare i log: `C:\ProgramData\Microsoft\IntuneManagementExtension\Logs\AgentExecutor.log`.

**"Device scompare da Intune dopo 30 giorni"** → Device stale cleanup attivo. Intune → Devices → Device cleanup rules. Default: rimuove device inattivi dopo 90 giorni (configurabile). Device spento per lungo periodo o senza connettività verrà rimosso.

**"Autopilot Reset fallisce"** → Richiede connettività Internet e WinRE funzionante. Verificare: `reagentc /info` → Windows RE status: Enabled. Se disabilitato: `reagentc /enable`. Verificare che il device sia ancora registrato in Autopilot.

**"SCCM Distribution Point lento"** → Verificare: bandwidth throttling configurato, BITS transfer in corso, spazio disco sul DP. Log: `C:\SMS_DP$\sms\Logs\smsdpprov.log`. Considerare Branch Cache o Peer Cache per sedi remote. Controllare la schedulazione dei deployment.

**"App Protection Policy non applicata su BYOD"** → L'app deve essere managed e l'utente deve aver effettuato il login con account aziendale nell'app. Verificare: l'app è nella lista delle protected apps, la policy è assegnata al gruppo utente corretto, l'utente ha licenza Intune.

**"Endpoint Analytics non mostra dati"** → I device devono avere Windows 10/11 Enterprise/Education. Verificare: data collection policy abilitata (Intune → Reports → Endpoint analytics → Settings). I dati possono richiedere 24-48 ore per apparire dopo l'enrollment.

---

## FAQ

**Q1: Intune o SCCM? Quale scegliere per un nuovo progetto?**
A: Per greenfield senza infrastruttura esistente → Intune + Autopilot. Per organizzazioni con SCCM già in produzione → co-management con migrazione graduale. SCCM rimane necessario per: OS imaging complesso, device legacy (Win 7/8.1), ambienti air-gapped senza Internet.

**Q2: È possibile gestire lo stesso device con SCCM e Intune contemporaneamente?**
A: Sì, è il co-management. Ogni workload (compliance, updates, apps, etc.) viene gestito da uno solo dei due tramite slider. Non si sovrappongono sullo stesso workload.

**Q3: Autopilot funziona senza connessione Internet?**
A: No. Autopilot richiede connessione Internet durante l'OOBE per contattare il servizio Microsoft e scaricare il profilo di deployment. Per deployment offline → SCCM OSD con Task Sequence su boot media.

**Q4: Posso usare GPO e Intune insieme sullo stesso device?**
A: Tecnicamente sì (hybrid Azure AD join), ma è sconsigliato. Le GPO e i Configuration Profiles Intune possono confliggere. La policy MDM ha priorità sulla GPO per impostazioni gestite. Usare la CSP `ControlPolicyConflict` per definire la priorità: `MDMWinsOverGP`.

**Q5: Quanto costa Intune?**
A: Intune Plan 1 è incluso in Microsoft 365 E3/E5, EMS E3/E5, e Microsoft 365 Business Premium. Come standalone: consultare il listino Microsoft aggiornato. Intune Suite (Plan 2 + add-ons) è un costo aggiuntivo per-user.

**Q6: Quanti device può gestire un singolo tenant Intune?**
A: Non c'è un limite ufficiale pubblicato. Tenant con 500.000+ device sono documentati. La scalabilità è gestita da Microsoft nel cloud. SCCM invece ha limiti architetturali: 100.000 per Primary Site, con CAS per andare oltre.

**Q7: Come gestisco gli aggiornamenti driver via Intune?**
A: Intune → Devices → Windows 10/11 updates → Driver updates. Richiede WUfB abilitato. I driver vengono proposti dal Windows Update catalog e l'admin approva/rifiuta per ring. Per driver custom non nel catalog → distribuire come Win32 app.

**Q8: Qual è la differenza tra Required e Available per le app?**
A: Required = installazione automatica obbligatoria (push silenzioso, l'utente non può rifiutare). Available = l'app appare nel Company Portal, l'utente decide se installarla. Per app critiche (Office, VPN, security) → Required. Per app opzionali (utility, tools) → Available.

**Q9: Come funziona Autopatch rispetto ai WUfB Update Rings manuali?**
A: Autopatch è un servizio gestito: Microsoft configura i ring, monitora il rollout, e interviene se ci sono problemi. WUfB Update Rings manuali richiedono che l'admin configuri deferral, deadline, e monitori i risultati. Autopatch = servizio gestito, WUfB Rings = self-service.

**Q10: Posso fare wipe remoto di un device BYOD senza cancellare i dati personali?**
A: Sì, con Selective Wipe (Retire). Rimuove solo i dati aziendali: profilo email, app managed, certificati, Wi-Fi aziendale. Non tocca: foto, app personali, impostazioni personali. Disponibile sia per device MDM enrolled che MAM-only.

**Q11: Come migro le GPO esistenti a Intune Configuration Profiles?**
A: Usare Group Policy Analytics in Intune: Devices → Group Policy analytics → Import GPO. Importare il backup GPO (LGPO export). Intune analizza ogni impostazione e indica: supportata in MDM (verde), non supportata (rosso), deprecata (giallo). Creare Settings Catalog profiles per le impostazioni supportate.

**Q12: Quanto tempo impiega un device Autopilot a essere pronto?**
A: User-Driven: 30-60 minuti tipico (dipende da app e policy). Pre-Provisioned: 5-10 minuti per l'utente (la fase IT richiede 20-40 minuti prima). Self-Deploying: 15-30 minuti senza interazione. Fattori: numero app Required, velocità rete, complessità policy.

**Q13: Come gestisco device condivisi (es. PC in sala riunioni, laboratorio)?**
A: Usare Autopilot Self-Deploying mode + Shared Device configuration profile. Configurare: account guest limitato, auto-logoff dopo inattività, pulizia sessione al logout, app installate a livello device (non utente). Per multi-user: Shared PC mode in Intune.

**Q14: È possibile rollback un Windows Feature Update?**
A: Sì, entro il periodo di disinstallazione configurato (default 10 giorni, configurabile fino a 60). Dopo il periodo → il rollback non è più possibile e richiede re-imaging. Intune → Devices → Windows 10/11 updates → Feature updates → Uninstall. Per quality updates: stesso principio, finestra più breve.

**Q15: Come verifico se un device è gestito correttamente da Intune?**
A: Sul device: `dsregcmd /status` → verificare AzureAdJoined, MdmUrl. Settings → Accounts → Access work or school → Info → mostra policy e app sincronizzate. Intune → Devices → selezionare device → Overview → verifica: Last check-in, Compliance, OS version, Primary user, Enrollment date, Management channel.

**Q16: Qual è la differenza tra Configuration Profiles Templates e Settings Catalog?**
A: Templates sono profili predefiniti con interfaccia guidata per scenari specifici (Wi-Fi, VPN, Email). Settings Catalog è un'interfaccia flat che espone 5000+ impostazioni individuali cercabili per nome, più granulare e flessibile. Per nuove configurazioni → preferire Settings Catalog. Templates rimangono utili per: Wi-Fi con certificati, VPN, e altri scenari che richiedono relazioni tra impostazioni.

**Q17: Come gestisco la transizione da WSUS a WUfB?**
A: Spostare il workload Windows Update da SCCM a Intune tramite co-management slider. Creare WUfB Update Rings in Intune prima dello spostamento. Rimuovere la GPO che punta a WSUS (HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate → WUServer). Verificare che il device riceva aggiornamenti da Windows Update e non da WSUS.

---

## Esercizi

### Esercizio 1: Autopilot Deployment Profile

Configurare un deployment Autopilot completo in un tenant di lab:

1. Registrare un dispositivo Autopilot tramite hardware hash (export con `Get-WindowsAutopilotInfo`).
2. Creare un Autopilot Deployment Profile (User-Driven, Azure AD Join).
3. Assegnare il profilo al dispositivo tramite un gruppo dinamico basato sull'Autopilot tag.
4. Configurare un Enrollment Status Page (ESP) con: app richieste visibili, timeout 60 minuti, blocco uso device fino al completamento.
5. Eseguire il reset del device e testare il flusso OOBE → Autopilot → ESP → Desktop.

**Criteri di validazione**: il device deve completare il provisioning senza errori. `dsregcmd /status` deve mostrare AzureAdJoined=YES e MdmUrl presente.

### Esercizio 2: Configuration Profiles e Compliance

Creare un set di policy di configurazione e compliance in Intune:

1. Creare un Configuration Profile (Settings Catalog) con: BitLocker encryption obbligatorio, Windows Hello for Business abilitato, telemetry livello Required.
2. Creare una Compliance Policy con: OS minimo Windows 11 23H2, BitLocker richiesto, firewall attivo, antivirus aggiornato.
3. Configurare un Conditional Access policy che blocchi l'accesso alle risorse aziendali per device non compliant.
4. Assegnare profile e policy a un gruppo pilota e verificare lo stato su un device di test.

**Criteri di validazione**: il device di test deve risultare "Compliant" in Intune. Un device non compliant deve essere bloccato dal Conditional Access.

### Esercizio 3: Application Deployment con Win32 App

Distribuire un'applicazione tramite Intune Win32 app:

1. Preparare il pacchetto con `IntuneWinAppUtil.exe` (input: installer MSI o EXE + setup folder).
2. Creare la Win32 app in Intune con: install command, uninstall command, detection rule (file/registry/script).
3. Configurare requirements: OS architecture, minimum OS version, disk space.
4. Assegnare come Required per un gruppo e Available per un altro.
5. Monitorare il deployment in Intune → Apps → Monitor → App install status.

**Criteri di validazione**: l'app deve risultare "Installed" per il gruppo Required. L'app deve apparire nel Company Portal per il gruppo Available.

### Esercizio 4: Co-Management SCCM + Intune

In un ambiente di lab con SCCM, configurare il co-management:

1. Verificare i prerequisiti: Azure AD Connect sincronizzato, Hybrid Azure AD Join configurato, CMG (Cloud Management Gateway) o VPN.
2. Abilitare co-management nella console SCCM (Administration → Cloud Services → Co-management).
3. Spostare un workload (es. Compliance Policies) da SCCM a Intune tramite lo slider.
4. Verificare lo stato di co-management su un device con `Get-WmiObject -Namespace root\ccm -Class SMS_Client`.
5. Confrontare il comportamento della Compliance Policy gestita da Intune vs SCCM.

**Criteri di validazione**: il device deve risultare co-managed in entrambe le console. Il workload spostato deve essere gestito da Intune.

---

## Auto-valutazione

### Domanda 1

Qual è la differenza tra MDM e MAM, e quando usare ciascuno?

<details>
<summary>Risposta</summary>

MDM (Mobile Device Management) gestisce l'intero dispositivo: configurazione, policy, compliance, wipe remoto. Richiede enrollment del device in Intune. Adatto a dispositivi aziendali. MAM (Mobile Application Management) gestisce solo le applicazioni e i dati aziendali al loro interno, senza controllare il device. Non richiede enrollment. Adatto a BYOD dove l'utente non vuole cedere il controllo del dispositivo personale. MAM-only protegge i dati aziendali (copy/paste restriction, encryption, wipe selettivo) senza toccare il resto.

Riferimento: Microsoft Learn, MAM vs MDM. Consultato: 2026-05-23.
</details>

### Domanda 2

Come funziona Windows Autopilot e quali sono i tre deployment mode?

<details>
<summary>Risposta</summary>

Autopilot permette il provisioning zero-touch: il device si registra con l'hardware hash, durante l'OOBE si connette ad Azure AD e riceve profilo, app e policy automaticamente. I tre mode: (1) User-Driven: l'utente si autentica e il device viene configurato per quell'utente (30-60 min). (2) Self-Deploying: nessuna interazione utente, per dispositivi condivisi o kiosk (15-30 min). (3) Pre-Provisioned (White Glove): il reparto IT completa la fase hardware-intensive in anticipo, l'utente ha un setup rapido (5-10 min).

Riferimento: Microsoft Learn, Windows Autopilot. Consultato: 2026-05-23.
</details>

### Domanda 3

Qual è la differenza tra Required e Available per le applicazioni in Intune?

<details>
<summary>Risposta</summary>

Required = installazione automatica obbligatoria (push silenzioso, l'utente non può rifiutare). Il deployment avviene nel background. Available = l'app appare nel Company Portal, l'utente decide se installarla. Per app critiche (Office, VPN, security agent) → Required. Per app opzionali (utility, tools) → Available. È possibile combinare: Required per un gruppo di base e Available per utenti aggiuntivi.

Riferimento: Microsoft Learn, Add apps to Intune. Consultato: 2026-05-23.
</details>

### Domanda 4

Come funziona Autopatch rispetto ai WUfB Update Rings manuali?

<details>
<summary>Risposta</summary>

Autopatch è un servizio gestito: Microsoft configura i ring (Test, First, Fast, Broad), monitora il rollout, e interviene automaticamente se vengono rilevati problemi (rollback). WUfB Update Rings manuali richiedono che l'admin configuri deferral, deadline, e monitori i risultati autonomamente. Autopatch = servizio gestito con SLA, WUfB Rings = self-service completo. Autopatch richiede licenza Windows Enterprise E3+ e Intune.

Riferimento: Microsoft Learn, Windows Autopatch. Consultato: 2026-05-23.
</details>

### Domanda 5

Qual è la differenza tra Configuration Profiles Templates e Settings Catalog?

<details>
<summary>Risposta</summary>

Templates sono profili predefiniti con interfaccia guidata per scenari specifici (Wi-Fi, VPN, Email, SCEP). Settings Catalog è un'interfaccia flat che espone 5000+ impostazioni individuali cercabili per nome, più granulare e flessibile. Per nuove configurazioni → preferire Settings Catalog perché copre più impostazioni e viene aggiornato più frequentemente. Templates rimangono utili per scenari che richiedono relazioni tra impostazioni (es. Wi-Fi con certificato SCEP).

Riferimento: Microsoft Learn, Configuration profiles in Intune. Consultato: 2026-05-23.
</details>

### Domanda 6

Come si esegue il selective wipe di un device BYOD?

<details>
<summary>Risposta</summary>

Selective Wipe (Retire in Intune) rimuove solo i dati aziendali: profilo email aziendale, app managed, certificati, configurazione Wi-Fi aziendale, VPN profile. Non tocca: foto, app personali, impostazioni personali. Disponibile sia per device MDM enrolled (Intune → Devices → selezionare device → Retire) che MAM-only (rimozione dei dati app tramite App Protection Policy). A differenza del Full Wipe, non ripristina il device alle impostazioni di fabbrica.

Riferimento: Microsoft Learn, Remove devices - retire. Consultato: 2026-05-23.
</details>

---

## Letture Primarie Consigliate

1. **Microsoft Learn: Microsoft Intune Documentation** — Guida completa alla gestione degli endpoint con Intune.
   https://learn.microsoft.com/en-us/mem/intune/
   Consultato: 2026-05-23.

2. **Microsoft Learn: Windows Autopilot** — Deployment guide per provisioning zero-touch.
   https://learn.microsoft.com/en-us/autopilot/
   Consultato: 2026-05-23.

3. **Microsoft Learn: Configuration Manager (SCCM/MECM)** — Documentazione ufficiale per endpoint management on-prem.
   https://learn.microsoft.com/en-us/mem/configmgr/
   Consultato: 2026-05-23.

4. **Microsoft Learn: Windows Autopatch** — Servizio gestito per aggiornamenti automatici Windows.
   https://learn.microsoft.com/en-us/windows/deployment/windows-autopatch/
   Consultato: 2026-05-23.

5. **Microsoft Learn: Co-Management** — Guida alla gestione ibrida SCCM + Intune.
   https://learn.microsoft.com/en-us/mem/configmgr/comanage/
   Consultato: 2026-05-23.

---

## Collegamenti Incrociati

| File | Relazione con questo modulo |
|---|---|
| [01-active-directory.md](01-active-directory.md) | Prerequisito: struttura AD, GPO, Hybrid Azure AD Join |
| [13-azure-ad-identita-ibrida.md](13-azure-ad-identita-ibrida.md) | Prerequisito: Azure AD, Azure AD Connect, Conditional Access |
| [10-gestione-aggiornamenti.md](10-gestione-aggiornamenti.md) | Contesto: WSUS legacy, Windows Update for Business, patch management |
| [21-group-policy-guida-completa.md](21-group-policy-guida-completa.md) | Confronto: GPO on-prem vs Intune Configuration Profiles |
| [24-windows-defender-endpoint-security.md](24-windows-defender-endpoint-security.md) | Integrazione: Defender for Endpoint enrollment tramite Intune |

---

## Glossario Locale

| Termine | Definizione |
|---|---|
| **Autopatch** | Servizio gestito Microsoft per l'automazione completa del patching Windows con ring predefiniti. |
| **Autopilot** | Tecnologia Microsoft per il provisioning zero-touch di dispositivi Windows tramite cloud. |
| **CMG** | Cloud Management Gateway. Ponte cloud per gestire device SCCM via Internet senza VPN. |
| **Co-management** | Gestione ibrida dove SCCM e Intune gestiscono lo stesso device con workload suddivisi. |
| **CSP** | Configuration Service Provider. Interfaccia MDM per configurare impostazioni Windows (equivalente cloud delle GPO). |
| **ESP** | Enrollment Status Page. Schermata che mostra il progresso del provisioning Autopilot. |
| **MAM** | Mobile Application Management. Gestione delle sole app aziendali senza controllo del device. |
| **MDM** | Mobile Device Management. Gestione completa del dispositivo tramite enrollment. |
| **OMA-URI** | Open Mobile Alliance Uniform Resource Identifier. Path per configurazioni MDM custom non esposte nel Settings Catalog. |
| **ASR** | Attack Surface Reduction. Regole di Microsoft Defender for Endpoint che bloccano comportamenti sfruttati da malware (macro Office, script offuscati, credential stealing). |
| **Cloud PC** | PC virtuale Windows 365 ospitato nel cloud Microsoft, gestito tramite Intune come un endpoint fisico. |
| **EPM** | Endpoint Privilege Management. Componente dell'Intune Suite che consente elevazione just-in-time senza concedere admin locale permanente. |
| **MSIX** | Formato moderno di packaging Microsoft con containerizzazione, firma obbligatoria, installazione/disinstallazione atomica e nessun residuo nel sistema. |
| **WUfB** | Windows Update for Business. Servizio cloud per la gestione degli aggiornamenti Windows senza WSUS. |
