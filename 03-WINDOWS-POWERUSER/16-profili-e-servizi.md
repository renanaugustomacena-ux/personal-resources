# Profili Utente e Servizi Windows — Guida Completa

> **Modulo 16** · **Aggiornamento:** 2026-05-22

| Campo | Valore |
|---|---|
| **Modulo del corso** | Amministrazione Windows enterprise |
| **Prerequisiti** | Conoscenza di Active Directory e GPO (→ `01-active-directory.md`), familiarità con i permessi NTFS (→ `08-permessi-e-accesso.md`), padronanza di PowerShell base (→ `02-powershell.md`) |
| **Obiettivi di apprendimento** | 1) Gestire l'architettura dei profili utente Windows (local, roaming, mandatory) e il versioning · 2) Configurare FSLogix Profile Container e Office Container per ambienti VDI/RDS · 3) Implementare Folder Redirection via GPO con gestione offline · 4) Amministrare servizi Windows con SCM, recovery options e dipendenze · 5) Configurare gMSA per service account sicuri con rotazione automatica delle password |
| **Tempo stimato** | lettura 80 min · lab 90 min |
| **Livello** | Competent |
| **Ultimo aggiornamento** | 2026-05-24 |

## Idee guida
1. **Roaming profiles legacy; FSLogix container moderno.**
2. **Profile redirection via GPO.**
3. **Service: `Get-Service`, `Set-Service`.**
4. **Service account: gMSA (group Managed Service Account) preferred.**
5. **NTUSER.DAT è il cuore del profilo — il registry hive HKCU.**
6. **Profile versioning: v2 (Win7), v4 (Win8.1), v5 (Win10), v6 (Win10 1607+).**
7. **Separare Office Container da Profile Container in FSLogix per flessibilità.**


## Indice

- [Panoramica](#panoramica)
- [Architettura Profilo Utente](#architettura-profilo-utente)
- [Profili Utente Windows](#profili-utente-windows)
- [Profili Speciali — Mandatory, Super Mandatory, Default](#profili-speciali--mandatory-super-mandatory-default)
- [Roaming Profiles](#roaming-profiles)
- [Folder Redirection](#folder-redirection)
- [Folder Redirection — Configurazione Avanzata](#folder-redirection--configurazione-avanzata)
- [FSLogix](#fslogix)
- [FSLogix — Configurazione Avanzata](#fslogix--configurazione-avanzata)
- [FSLogix — Configurazione Registry e VHDLocations](#fslogix--configurazione-registry-e-vhdlocations)
- [FSLogix — Cloud Cache e Multi-Site](#fslogix--cloud-cache-e-multi-site)
- [Servizi Windows](#servizi-windows)
- [Service Account — gMSA e MSA](#service-account--gmsa-e-msa)
- [dMSA — Delegated Managed Service Account (Server 2025)](#dmsa--delegated-managed-service-account-server-2025)
- [Servizi Windows — Gestione Avanzata](#servizi-windows--gestione-avanzata)
- [GPO per Profili e Servizi](#gpo-per-profili-e-servizi)
- [Automazione e Script Enterprise](#automazione-e-script-enterprise)
- [Diagnosi e Riparazione Profili Corrotti](#diagnosi-e-riparazione-profili-corrotti)
- [Service Hardening — SID, Restrizioni e Isolamento](#service-hardening--sid-restrizioni-e-isolamento)
- [Recovery Avanzato e Monitoraggio Automatico](#recovery-avanzato-e-monitoraggio-automatico)
- [Scenari Reali Enterprise](#scenari-reali-enterprise)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## Panoramica

I profili utente contengono le impostazioni personali, desktop, documenti e configurazioni applicazioni. In ambienti enterprise con utenti che accedono a più computer, servono soluzioni per rendere il profilo disponibile ovunque: Roaming Profiles (legacy), Folder Redirection (documenti su share), e FSLogix (VHD containers, moderno). La gestione dei servizi Windows è complementare per garantire stabilità del sistema.

```
┌──────────────────────────────────────────────────────────┐
│        EVOLUZIONE GESTIONE PROFILI (TIMELINE)            │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  2000-2010   ROAMING PROFILES                            │
│              → Copia profilo su share al login/logoff    │
│              → Lento, file lock, bloat                   │
│              → Ancora in uso in ambienti legacy          │
│                                                          │
│  2005-2020   FOLDER REDIRECTION                          │
│              → Reindirizza cartelle su share             │
│              → Più efficiente del roaming completo       │
│              → Offline Files per accesso senza rete      │
│              → Ancora valido per workstation fisiche     │
│                                                          │
│  2010-2020   UE-V (User Environment Virtualization)      │
│              → Sincronizza solo impostazioni app         │
│              → Leggero, flessibile                       │
│              → Rimosso in Windows 11 22H2+               │
│                                                          │
│  2018+       FSLOGIX PROFILE CONTAINER                   │
│              → VHD/VHDX montato al login                 │
│              → Standard per VDI/RDS/AVD                  │
│              → Nessun file lock, login veloce            │
│              → Soluzione consigliata da Microsoft        │
│                                                          │
│  2023+       WINDOWS 365 CLOUD PC                        │
│              → Profilo nel cloud, persistente            │
│              → FSLogix integrato                         │
│              → Soluzione completamente cloud             │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Architettura Profilo Utente

### Componenti del Profilo

```
┌─────────────────────────────────────────────────────────┐
│              ARCHITETTURA PROFILO UTENTE                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  REGISTRY HIVE (NTUSER.DAT)                             │
│  ├── Caricato come HKCU al login                        │
│  ├── Contiene tutte le impostazioni utente              │
│  ├── Desktop, Explorer, applicazioni                    │
│  ├── Variabili ambiente utente                          │
│  ├── Mappature stampanti, connessioni di rete           │
│  └── Dimensione tipica: 2-50 MB                        │
│                                                         │
│  FILESYSTEM (%USERPROFILE%)                             │
│  ├── Desktop\         — File e shortcut sul desktop     │
│  ├── Documents\       — Documenti utente                │
│  ├── Downloads\       — File scaricati                  │
│  ├── Pictures\        — Immagini                        │
│  ├── Music\           — Musica                          │
│  ├── Videos\          — Video                           │
│  ├── Favorites\       — Preferiti IE/Edge legacy        │
│  ├── Links\           — Link rapidi Explorer            │
│  ├── Contacts\        — Contatti                        │
│  └── Searches\        — Ricerche salvate                │
│                                                         │
│  APPDATA (il cuore delle configurazioni app)            │
│  ├── Roaming\    — Dati che seguono l'utente            │
│  │   ├── Microsoft\Office\  — Impostazioni Office       │
│  │   ├── Microsoft\Outlook\ — Firme, template           │
│  │   ├── Microsoft\Teams\   — Cache Teams (pre-v2)      │
│  │   ├── Chrome\            — Profilo browser            │
│  │   └── (app specifiche)                               │
│  ├── Local\      — Dati specifici per questa macchina   │
│  │   ├── Microsoft\Outlook\  — OST file (cache mail)   │
│  │   ├── Microsoft\Teams\    — Cache Teams              │
│  │   ├── Google\Chrome\      — Cache browser            │
│  │   ├── Packages\           — App UWP/Store            │
│  │   └── Temp\               — File temporanei          │
│  └── LocalLow\   — Dati a basso livello integrità      │
│      └── (app con sandboxing)                           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Profile Versioning

```powershell
# Windows usa versioni di profilo per evitare conflitti tra OS diversi
# Il suffisso viene aggiunto automaticamente alla cartella profilo

# Versioni profilo:
# Nessun suffisso  → Windows XP/2003
# .V2              → Windows Vista/7, Server 2008/2008R2
# .V4              → Windows 8.1, Server 2012R2
# .V5              → Windows 10 (build 1507-1511)
# .V6              → Windows 10 (build 1607+), Windows 11, Server 2016+

# Esempio su un file server:
# \\SRV01\Profiles$\mrossi         → profilo Windows XP
# \\SRV01\Profiles$\mrossi.V2      → profilo Windows 7
# \\SRV01\Profiles$\mrossi.V6      → profilo Windows 10/11

# Verificare la versione profilo del sistema corrente
$profileList = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList"
$version = (Get-ItemProperty $profileList).ProfilesVersion
Write-Host "Profile Version: $version"

# Questo impedisce che un profilo Win7 venga caricato su Win10
# Ogni OS carica solo il profilo della propria versione
```

---

## Profili Utente Windows

### Struttura Profilo

```
C:\Users\username\
├── Desktop\                → File sul desktop
├── Documents\              → Documenti utente
├── Downloads\              → File scaricati
├── AppData\
│   ├── Local\              → Dati app specifici per il computer
│   │   └── Temp\           → File temporanei
│   ├── LocalLow\           → Dati app a basso livello integrità
│   └── Roaming\            → Dati app che seguono l'utente (roaming)
│       ├── Microsoft\      → Impostazioni Office, Edge, etc.
│       └── ...
├── NTUSER.DAT              → Hive registry utente (HKCU)
├── NTUSER.DAT.LOG1/LOG2    → Transaction log del registry
└── ntuser.ini              → Lista esclusioni roaming
```

### Gestione Profili

```powershell
# Elencare profili
Get-CimInstance Win32_UserProfile | Select-Object LocalPath, SID, LastUseTime, Loaded

# Dimensione profili con dettaglio per cartella
Get-ChildItem C:\Users -Directory | ForEach-Object {
    [PSCustomObject]@{
        User = $_.Name
        SizeMB = [math]::Round((Get-ChildItem $_.FullName -Recurse -Force -ErrorAction SilentlyContinue |
            Measure-Object Length -Sum).Sum / 1MB, 2)
    }
} | Sort-Object SizeMB -Descending

# Dettaglio dimensione per sottocartella (diagnosticare profilo grande)
function Get-ProfileBreakdown {
    param([string]$UserProfile)
    $folders = @("Desktop", "Documents", "Downloads", "Pictures",
                 "AppData\Local", "AppData\Roaming", "AppData\LocalLow")
    foreach ($f in $folders) {
        $path = Join-Path $UserProfile $f
        if (Test-Path $path) {
            $size = (Get-ChildItem $path -Recurse -Force -ErrorAction SilentlyContinue |
                Measure-Object Length -Sum).Sum
            [PSCustomObject]@{
                Folder = $f
                SizeMB = [math]::Round($size / 1MB, 2)
            }
        }
    }
}
Get-ProfileBreakdown -UserProfile "C:\Users\mrossi" | Sort-Object SizeMB -Descending

# Eliminare profilo (corretto — non cancellare solo la cartella!)
Get-CimInstance Win32_UserProfile | Where-Object LocalPath -like "*vecchio.utente*" |
    Remove-CimInstance
# IMPORTANTE: Remove-CimInstance elimina sia la cartella che la voce nel registry
# MAI cancellare solo la cartella C:\Users\<user> manualmente!
# Ciò lascia voci orfane nel registry e causa problemi al prossimo login

# Eliminare profili inattivi da più di 90 giorni (pulizia automatizzata)
$threshold = (Get-Date).AddDays(-90)
Get-CimInstance Win32_UserProfile |
    Where-Object {
        -not $_.Special -and
        -not $_.Loaded -and
        $_.LastUseTime -lt $threshold -and
        $_.LocalPath -notlike "*Administrator*" -and
        $_.LocalPath -notlike "*Default*"
    } | ForEach-Object {
        Write-Host "Profilo inattivo: $($_.LocalPath) — Ultimo uso: $($_.LastUseTime)"
        # Decommentare per eliminare:
        # $_ | Remove-CimInstance
    }

# Profilo default (template per nuovi utenti)
# C:\Users\Default\
# Personalizzare: copiare impostazioni nel profilo Default, poi sysprep

# Personalizzare il profilo Default — procedura corretta
# 1. Accedere come utente temporaneo, configurare le impostazioni desiderate
# 2. Disconnettere l'utente temporaneo
# 3. Usare CopyProfile in unattend.xml durante sysprep:
#    <CopyProfile>true</CopyProfile>
# OPPURE:
# 4. Copiare manualmente i file necessari in C:\Users\Default\
# 5. Esportare il registry: reg export HKCU C:\Users\Default\NTUSER.DAT

# Registry hive del profilo
# Caricare l'hive di un profilo non attivo
reg load HKU\TempProfile "C:\Users\mrossi\NTUSER.DAT"
# Modificare impostazioni
reg add "HKU\TempProfile\Software\Microsoft\Windows\CurrentVersion\Explorer" `
    /v ShowRecent /t REG_DWORD /d 0 /f
# Scaricare l'hive
reg unload HKU\TempProfile
```

---

## Profili Speciali — Mandatory, Super Mandatory, Default

### Mandatory Profile (NTUSER.MAN)

```powershell
# Un profilo mandatory è un profilo che NON salva le modifiche al logoff
# L'utente lavora normalmente durante la sessione,
# ma al logoff tutto torna come prima

# ============================================================
# CREAZIONE PROFILO MANDATORY
# ============================================================

# 1. Creare un profilo "gold" (utente template)
# - Login come utente template
# - Configurare desktop, impostazioni, applicazioni
# - Logoff

# 2. Rinominare NTUSER.DAT → NTUSER.MAN
Rename-Item "\\SRV01\Profiles$\template\NTUSER.DAT" "NTUSER.MAN"

# 3. Assegnare il profilo mandatory all'utente
Set-ADUser -Identity mrossi -ProfilePath "\\SRV01\Profiles$\mandatory"
# Tutti gli utenti possono puntare allo STESSO profilo mandatory
# Poiché non scrivono, non c'è conflitto

# CASI D'USO:
# - Chioschi pubblici / postazioni condivise
# - Laboratori informatici / aule formazione
# - Postazioni di reception / call center
# - Ambienti dove la personalizzazione è vietata

# Vantaggi:
# - Ambiente consistente e prevedibile
# - Nessun bloat del profilo
# - Un solo profilo da mantenere per N utenti
# - Logoff veloce (nulla da scrivere)

# Svantaggi:
# - L'utente non può salvare preferenze
# - Wallpaper personalizzato, shortcut → persi al logoff
# - Impostazioni applicazioni non persistono
```

### Super Mandatory Profile

```powershell
# Un profilo Super Mandatory impedisce il login se il profilo
# non è raggiungibile (es. share offline)

# Differenza:
# Mandatory → se la share è offline, l'utente logga con profilo locale temporaneo
# Super Mandatory → se la share è offline, il login viene RIFIUTATO

# Creazione: aggiungere .MAN al nome della cartella del profilo
# \\SRV01\Profiles$\mandatory.MAN\
#                              ^^^^ estensione sulla CARTELLA

# Assegnare:
Set-ADUser -Identity mrossi -ProfilePath "\\SRV01\Profiles$\mandatory.MAN"

# Caso d'uso: ambienti ad alta sicurezza dove un profilo incontrollato
# (locale temporaneo) è inaccettabile
```

---

## Roaming Profiles

```powershell
# Il roaming profile copia il profilo da/verso una share di rete al login/logoff
# LEGACY: lento con profili grandi, problemi di blocco file, versioni incompatibili

# Configurazione:
# 1. Creare share
New-SmbShare -Name "Profiles$" -Path "D:\Profiles" `
    -FullAccess "Domain Admins" -ChangeAccess "Authenticated Users"

# NTFS permissions sulla cartella D:\Profiles:
# SYSTEM: Full Control
# Domain Admins: Full Control
# Creator Owner: Full Control (solo sottocartelle e file)
# Authenticated Users: List Folder / Read Data, Create Folders (solo questa cartella)

# 2. Impostare path profilo sull'utente
Set-ADUser -Identity mrossi -ProfilePath "\\SRV01\Profiles$\%username%"
# La cartella viene creata automaticamente al primo login

# 3. GPO per esclusioni (ridurre dimensione)
# User → Administrative Templates → System → User Profiles
#   → Exclude directories in roaming profile:
#     AppData\Local;AppData\LocalLow;Downloads

# Problemi comuni:
# - Slow login/logoff (copia profilo grande sulla rete)
# - File lock (Outlook OST, database locali bloccano il logoff)
# - Profile bloat (cache browser, file temporanei)
# - Version mismatch (Windows 10 v2 vs v6 profili)

# CONSIGLIO: NON usare Roaming Profiles su nuovi deploy.
# Usare Folder Redirection + FSLogix
```

---

## Folder Redirection

```powershell
# Folder Redirection reindirizza cartelle del profilo su una share di rete
# I file rimangono sulla rete, non vengono copiati localmente
# Molto più efficiente dei Roaming Profiles

# Cartelle redirect-abili:
# Desktop, Documents, Pictures, Music, Videos, Downloads,
# AppData\Roaming, Start Menu, Favorites

# Configurazione via GPO:
# User → Windows Settings → Folder Redirection

# Per ogni cartella:
# - Basic (tutti nella stessa root): \\SRV01\Redirect$\%USERNAME%\Documents
# - Advanced (per gruppo/utente)
# - Follow the Documents folder (per Pictures, Music, etc.)

# Impostazioni critiche:
# - Grant the user exclusive rights: Yes (solo l'utente accede alla propria cartella)
# - Move contents to new location: Yes (prima volta, migra dati esistenti)
# - Also apply to Windows 2000/XP: dipende dall'ambiente
# - Policy removal: Redirect back to local (o Leave in new location)

# Creare share per folder redirection
New-SmbShare -Name "Redirect$" -Path "D:\Redirect" `
    -FullAccess "Domain Admins" -ChangeAccess "Authenticated Users"

# NTFS:
# SYSTEM: Full Control
# Domain Admins: Full Control
# Creator Owner: Full Control (sottocartelle e file)
# Authenticated Users: Create Folders (solo questa cartella)

# Offline Files (cache locale per accesso offline)
# GPO: Computer → Administrative Templates → Network → Offline Files
# - Allow or Disallow use of Offline Files: Enabled
# - Synchronize all offline files before logoff: Enabled
# - Configure slow-link mode: 35000 (35ms latency threshold)

# Disabilitare Offline Files se non necessari (semplifica):
# - Configure Offline Files: Disabled
```

---

## Folder Redirection — Configurazione Avanzata

### Preparazione Share con Permessi Corretti

```powershell
# ============================================================
# SETUP COMPLETO SHARE PER FOLDER REDIRECTION
# ============================================================

# 1. Creare la struttura cartelle
$basePath = "D:\UserData\FolderRedirection"
New-Item $basePath -ItemType Directory -Force

# 2. Configurare permessi NTFS (critici per sicurezza)
# Rimuovere ereditarietà e impostare permessi minimi
$acl = Get-Acl $basePath
$acl.SetAccessRuleProtection($true, $false)  # Disabilita ereditarietà

# SYSTEM: Full Control
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "SYSTEM", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
$acl.AddAccessRule($rule)

# Domain Admins: Full Control
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "CORP\Domain Admins", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
$acl.AddAccessRule($rule)

# Creator Owner: Full Control (solo sottocartelle e file)
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "CREATOR OWNER", "FullControl", "ContainerInherit,ObjectInherit", "InheritOnly", "Allow")
$acl.AddAccessRule($rule)

# Authenticated Users: Create Folders (solo questa cartella)
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "Authenticated Users", "CreateDirectories", "None", "None", "Allow")
$acl.AddAccessRule($rule)

# List Folder (necessario per navigare alla propria cartella)
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "Authenticated Users", "ListDirectory", "None", "None", "Allow")
$acl.AddAccessRule($rule)

Set-Acl $basePath $acl

# 3. Creare share nascosta
New-SmbShare -Name "Redirect$" -Path $basePath `
    -FullAccess "CORP\Domain Admins" `
    -ChangeAccess "CORP\Authenticated Users" `
    -Description "Folder Redirection - Non modificare permessi"

# 4. Abilitare Access Based Enumeration
Set-SmbShare -Name "Redirect$" -FolderEnumerationMode AccessBased

# Con ABE, ogni utente vede solo la propria cartella nella share
```

### Offline Files — Gestione Approfondita

```powershell
# Gli Offline Files creano una cache locale delle cartelle redirected
# L'utente può lavorare anche senza connessione alla share

# Verificare stato cache Offline Files
Get-WmiObject Win32_OfflineFilesCache | Select-Object Active, Enabled, Location

# Visualizzare file in cache
Get-ChildItem "$env:SystemRoot\CSC\v2.0.6\namespace" -Recurse -ErrorAction SilentlyContinue

# Forzare sincronizzazione
$sync = New-Object -ComObject CscShell.SyncMgr
# Oppure: mobsync.exe (Sync Center)

# Dimensione cache Offline Files
$cscPath = "$env:SystemRoot\CSC"
if (Test-Path $cscPath) {
    $size = (Get-ChildItem $cscPath -Recurse -Force -ErrorAction SilentlyContinue |
        Measure-Object Length -Sum).Sum / 1MB
    Write-Host "Cache Offline Files: $([math]::Round($size, 2)) MB"
}

# GPO per gestione Offline Files:
# Computer → Administrative Templates → Network → Offline Files
#
# Configure Slow-link mode: 35000 (35ms)
#   → Se la latenza supera 35ms, passa in modalità slow-link
#   → In slow-link, i file vengono serviti dalla cache locale
#
# Limit disk space used by Offline Files: 20% dello spazio disco
#   → Impedisce che la cache occupi tutto il disco
#
# Configure Background Sync: 360 minuti (6 ore)
#   → Sincronizzazione automatica ogni 6 ore
#
# Enable Transparent Caching: Enabled
#   → Cache automatica dei file letti dalla rete
#   → Riduce il traffico di rete per file letti frequentemente
#
# Files Not Cached:
#   *.pst;*.ost;*.tmp;~*.*
#   → File Outlook e temporanei non vengono messi in cache
#   → Previene conflitti e corruzione

# Pulire la cache Offline Files (reset completo)
# ATTENZIONE: sincronizzare prima!
# CSCCmd.exe /disable  → disabilita
# Eliminare C:\Windows\CSC\  → rimuove cache
# CSCCmd.exe /enable   → riabilita
# Oppure via GPO con script
```

### Folder Redirection con DFS

```powershell
# DFS (Distributed File System) permette di usare un namespace unico
# per la Folder Redirection, indipendentemente dal server fisico

# Namespace DFS: \\corp.contoso.com\UserData
# Invece di: \\SRV01\Redirect$

# Vantaggi:
# - Se SRV01 diventa SRV02, basta aggiornare il target DFS
# - L'utente non deve cambiare nulla
# - DFS Replication per ridondanza multi-site
# - Trasparente per le GPO

# Installare DFS
Install-WindowsFeature FS-DFS-Namespace, FS-DFS-Replication -IncludeManagementTools

# Creare namespace
New-DfsnRoot -TargetPath "\\SRV01\Redirect$" -Path "\\corp.contoso.com\UserData" -Type DomainV2

# Aggiungere folder target
New-DfsnFolder -Path "\\corp.contoso.com\UserData\Documents" `
    -TargetPath "\\SRV01\Redirect$"

# GPO Folder Redirection punta al namespace DFS:
# \\corp.contoso.com\UserData\%USERNAME%\Documents
# Invece di: \\SRV01\Redirect$\%USERNAME%\Documents
```

---

## FSLogix

```powershell
# FSLogix è la soluzione moderna di Microsoft per la gestione profili
# Salva il profilo utente in un VHD/VHDX montato al login
# Ideale per: VDI, RDS, Azure Virtual Desktop, multi-session

# Vantaggi:
# - Login veloce (mount VHD, non copia file)
# - Supporta applicazioni problematiche (Outlook cache, Teams, OneDrive)
# - Nessun profile bloat o file lock
# - Compatibile con roaming e non-persistent desktops

# Installazione:
# Scaricare FSLogix da Microsoft (gratuito con licenze M365/RDS)
# Installare FSLogixAppsSetup.exe su ogni Session Host

# Configurazione via GPO (template ADMX inclusi):
# Computer → Administrative Templates → FSLogix → Profile Containers

# Impostazioni principali:
# - Enabled: Yes
# - VHD Locations: \\SRV01\FSLogix$ (share per i VHD)
# - Size in MBs: 30000 (30 GB per utente)
# - Dynamic VHD(X) allocation: Yes
# - Delete local profile when FSLogix loads: Yes
# - Locked retry count: 3
# - Locked retry interval: 15 (secondi)

# Creare share
New-SmbShare -Name "FSLogix$" -Path "D:\FSLogix" `
    -FullAccess "Domain Admins" -ChangeAccess "Authenticated Users"

# NTFS su D:\FSLogix:
# SYSTEM: Full Control
# Domain Admins: Full Control
# Creator Owner: Full Control (sottocartelle)
# Domain Users / Authenticated Users:
#   - Modify (questa cartella, sottocartelle, file)

# Struttura risultante:
# D:\FSLogix\
# ├── S-1-5-21-..._mrossi\
# │   └── Profile_mrossi.VHDX    → Profilo completo come VHD
# ├── S-1-5-21-..._gbianchi\
# │   └── Profile_gbianchi.VHDX
# └── ...

# Office Container (separato dal profilo, per Outlook/Teams/OneDrive cache)
# Computer → FSLogix → Office 365 Containers
# - Enabled: Yes
# - VHD Locations: \\SRV01\FSLogix-Office$
# - Include Office activation data: Yes
# - Include Outlook data: Yes
# - Include Teams data: Yes
# - Include OneDrive data: Yes

# Diagnostica
# Log: C:\ProgramData\FSLogix\Logs\
# Event Viewer: Applications and Services → FSLogix → Apps → Operational
# Strumento: frxtray (system tray) mostra stato mount
```

---

## FSLogix — Configurazione Avanzata

### Esclusioni e Inclusioni

```powershell
# FSLogix permette di definire cosa includere/escludere dal profile container
# Utile per ridurre la dimensione del VHD e velocizzare il login

# ============================================================
# REDIRECTIONS.XML — FILE DI CONFIGURAZIONE ESCLUSIONI
# ============================================================

# Posizione: C:\Program Files\FSLogix\Apps\Rules\
# O via GPO: path centralizzato

# Esempio redirections.xml completo:
$redirections = @'
<?xml version="1.0" encoding="UTF-8"?>
<FrxProfileFolderRedirection ExcludeCommonFolders="0">

  <!-- ESCLUSIONI: queste cartelle restano locali, NON nel VHD -->

  <!-- Cache browser (si ricrea automaticamente) -->
  <Exclude Copy="0">AppData\Local\Google\Chrome\User Data\Default\Cache</Exclude>
  <Exclude Copy="0">AppData\Local\Google\Chrome\User Data\Default\Code Cache</Exclude>
  <Exclude Copy="0">AppData\Local\Microsoft\Edge\User Data\Default\Cache</Exclude>

  <!-- Cache Windows -->
  <Exclude Copy="0">AppData\Local\Temp</Exclude>
  <Exclude Copy="0">AppData\Local\Microsoft\Windows\INetCache</Exclude>
  <Exclude Copy="0">AppData\Local\Microsoft\Windows\Explorer</Exclude>

  <!-- Teams cache (Teams v2 usa meno cache) -->
  <Exclude Copy="0">AppData\Local\Microsoft\Teams\Cache</Exclude>
  <Exclude Copy="0">AppData\Local\Microsoft\Teams\blob_storage</Exclude>
  <Exclude Copy="0">AppData\Local\Microsoft\Teams\databases</Exclude>
  <Exclude Copy="0">AppData\Local\Microsoft\Teams\GPUCache</Exclude>
  <Exclude Copy="0">AppData\Local\Microsoft\Teams\IndexedDB</Exclude>
  <Exclude Copy="0">AppData\Local\Microsoft\Teams\Local Storage</Exclude>
  <Exclude Copy="0">AppData\Local\Microsoft\Teams\tmp</Exclude>

  <!-- OneDrive cache (i file sono nel cloud) -->
  <Exclude Copy="0">AppData\Local\Microsoft\OneDrive\logs</Exclude>

  <!-- Windows Search index -->
  <Exclude Copy="0">AppData\Local\Packages\Microsoft.Windows.Search_cw5n1h2txyewy</Exclude>

  <!-- INCLUSIONI: forzare queste cartelle nel VHD anche se escluse da pattern -->
  <Include>AppData\Local\Microsoft\Outlook</Include>
  <Include>AppData\Local\Microsoft\Office</Include>

</FrxProfileFolderRedirection>
'@
$redirections | Out-File "C:\Program Files\FSLogix\Apps\Rules\redirections.xml" -Encoding UTF8
```

### Compattazione e Manutenzione VHD

```powershell
# I VHD FSLogix crescono nel tempo ma non si restringono automaticamente
# Serve compattazione periodica

# ============================================================
# COMPATTAZIONE MANUALE VHD
# ============================================================

# 1. Verificare che l'utente NON sia loggato
# 2. Compattare con diskpart o PowerShell

function Compact-FSLogixVHD {
    param(
        [string]$VHDPath,
        [switch]$WhatIf
    )

    # Verificare che non sia in uso
    try {
        $file = [System.IO.File]::Open($VHDPath, 'Open', 'Read', 'None')
        $file.Close()
    }
    catch {
        Write-Warning "VHD in uso, skip: $VHDPath"
        return
    }

    $sizeBefore = (Get-Item $VHDPath).Length / 1GB

    if (-not $WhatIf) {
        # Montare come readonly
        Mount-VHD -Path $VHDPath -ReadOnly
        $disk = Get-VHD $VHDPath

        # Smontare
        Dismount-VHD -Path $VHDPath

        # Compattare (Optimize-VHD richiede Hyper-V role)
        Optimize-VHD -Path $VHDPath -Mode Full
    }

    $sizeAfter = (Get-Item $VHDPath).Length / 1GB

    [PSCustomObject]@{
        File       = Split-Path $VHDPath -Leaf
        BeforeGB   = [math]::Round($sizeBefore, 2)
        AfterGB    = [math]::Round($sizeAfter, 2)
        SavedGB    = [math]::Round($sizeBefore - $sizeAfter, 2)
    }
}

# Compattare tutti i VHD nella share FSLogix
$vhds = Get-ChildItem "\\SRV01\FSLogix$" -Recurse -Filter "*.VHDX"
foreach ($vhd in $vhds) {
    Compact-FSLogixVHD -VHDPath $vhd.FullName
}

# ============================================================
# COMPATTAZIONE AUTOMATICA (Task Schedulato)
# ============================================================
# FSLogix dalla versione 2210+ include compattazione automatica
# Abilitare via GPO:
# Computer → FSLogix → Profile Containers
# → SizeInMBs: 30000
# → IsDynamic: 1
# → VHDCompactDisk: 1 (abilita compattazione al logoff)
```

### FSLogix con Antivirus — Esclusioni

```powershell
# Le esclusioni antivirus sono CRITICHE per performance FSLogix
# Senza esclusioni, l'antivirus scansiona ogni operazione nel VHD

# Esclusioni raccomandate da Microsoft per FSLogix:

# FILE da escludere dalla scansione:
# *.VHD
# *.VHDX
# *.CIM

# CARTELLE da escludere:
# C:\Program Files\FSLogix\Apps\frxdrv.sys
# C:\Program Files\FSLogix\Apps\frxdrvvt.sys
# C:\Program Files\FSLogix\Apps\frxccd.sys
# %TEMP%\*.VHD
# %TEMP%\*.VHDX
# %Windir%\TEMP\*.VHD
# %Windir%\TEMP\*.VHDX
# \\SRV01\FSLogix$\**\*.VHD    → Share FSLogix
# \\SRV01\FSLogix$\**\*.VHDX

# PROCESSI da escludere:
# C:\Program Files\FSLogix\Apps\frxccd.exe
# C:\Program Files\FSLogix\Apps\frxccds.exe
# C:\Program Files\FSLogix\Apps\frxsvc.exe

# Per Windows Defender (via GPO):
# Computer → Administrative Templates → Windows Components →
#   Microsoft Defender Antivirus → Exclusions
# → Path Exclusions: aggiungere i path sopra
# → Process Exclusions: aggiungere i processi sopra

# Per Windows Defender via PowerShell:
Add-MpPreference -ExclusionPath "C:\Program Files\FSLogix\Apps\frxdrv.sys"
Add-MpPreference -ExclusionProcess "C:\Program Files\FSLogix\Apps\frxsvc.exe"
Add-MpPreference -ExclusionExtension "VHD", "VHDX"
```

---

## FSLogix — Configurazione Registry e VHDLocations

### Chiavi di Registro FSLogix — Riferimento Completo

```powershell
# ============================================================
# TUTTE LE CHIAVI REGISTRY FSLogix PROFILE CONTAINER
# ============================================================
# Posizione: HKLM:\SOFTWARE\FSLogix\Profiles
# Queste chiavi possono essere impostate via GPO (ADMX) o direttamente nel registry

# --- CHIAVI FONDAMENTALI ---

# Abilitare FSLogix Profile Container
Set-ItemProperty -Path "HKLM:\SOFTWARE\FSLogix\Profiles" -Name "Enabled" -Value 1 -Type DWord

# VHDLocations: path della share dove vengono salvati i VHD
# Supporta fino a 4 path separati da punto e virgola
# Il primo disponibile viene usato (failover automatico)
Set-ItemProperty -Path "HKLM:\SOFTWARE\FSLogix\Profiles" `
    -Name "VHDLocations" -Value "\\SRV01\FSLogix$;\\SRV02\FSLogix$" -Type String

# Nota: NON combinare VHDLocations con CCDLocations (Cloud Cache)
# Se CCDLocations è configurato, VHDLocations viene IGNORATO
# CCDLocations usa una sintassi diversa (type=smb,connectionString=...)

# --- DIMENSIONE E TIPO VHD ---

# Dimensione massima del VHD in MB (default: 30000 = ~30 GB)
Set-ItemProperty -Path "HKLM:\SOFTWARE\FSLogix\Profiles" `
    -Name "SizeInMBs" -Value 30000 -Type DWord

# Tipo di volume: VHD o VHDX (VHDX consigliato: più robusto, meno corruzione)
# VHD = legacy, limite 2 TB
# VHDX = moderno, supporto per dischi più grandi, journaling, resilienza
Set-ItemProperty -Path "HKLM:\SOFTWARE\FSLogix\Profiles" `
    -Name "VolumeType" -Value "VHDX" -Type String

# Allocazione dinamica (il VHD cresce con i dati, non alloca tutto subito)
Set-ItemProperty -Path "HKLM:\SOFTWARE\FSLogix\Profiles" `
    -Name "IsDynamic" -Value 1 -Type DWord

# --- NAMING E DIRECTORY ---

# FlipFlopProfileDirectoryName: inverte l'ordine SID e username nella cartella
# 0 (default) = S-1-5-21-xxx_username (es. S-1-5-21-1234_mrossi)
# 1           = username_S-1-5-21-xxx (es. mrossi_S-1-5-21-1234)
# Consigliato 1: più leggibile per gli amministratori nella share
Set-ItemProperty -Path "HKLM:\SOFTWARE\FSLogix\Profiles" `
    -Name "FlipFlopProfileDirectoryName" -Value 1 -Type DWord

# --- GESTIONE LOCK E SESSIONI CONCORRENTI ---

# Tentativi di retry quando il VHD è bloccato (altra sessione)
Set-ItemProperty -Path "HKLM:\SOFTWARE\FSLogix\Profiles" `
    -Name "LockedRetryCount" -Value 3 -Type DWord

# Intervallo tra i tentativi in secondi
Set-ItemProperty -Path "HKLM:\SOFTWARE\FSLogix\Profiles" `
    -Name "LockedRetryInterval" -Value 15 -Type DWord

# Intervallo di ricollegamento automatico in secondi (utile per reconnect)
Set-ItemProperty -Path "HKLM:\SOFTWARE\FSLogix\Profiles" `
    -Name "ReAttachIntervalSeconds" -Value 15 -Type DWord

# Numero massimo di retry per il ricollegamento
Set-ItemProperty -Path "HKLM:\SOFTWARE\FSLogix\Profiles" `
    -Name "ReAttachRetryCount" -Value 3 -Type DWord

# --- PULIZIA E PERFORMANCE ---

# Eliminare il profilo locale quando FSLogix è attivo
# Previene conflitti tra profilo locale e container
Set-ItemProperty -Path "HKLM:\SOFTWARE\FSLogix\Profiles" `
    -Name "DeleteLocalProfileWhenVHDShouldApply" -Value 1 -Type DWord

# Compattazione disco al logoff (disponibile da FSLogix 2210+)
Set-ItemProperty -Path "HKLM:\SOFTWARE\FSLogix\Profiles" `
    -Name "VHDCompactDisk" -Value 1 -Type DWord

# --- LOGGING ---

# Livello di log (0 = nessuno, 1 = errori, 2 = warning, 3 = info)
Set-ItemProperty -Path "HKLM:\SOFTWARE\FSLogix\Logging" `
    -Name "LoggingLevel" -Value 3 -Type DWord

# Abilitare log per debugging dettagliato
Set-ItemProperty -Path "HKLM:\SOFTWARE\FSLogix\Logging" `
    -Name "LogFileKeepingPeriod" -Value 7 -Type DWord
```

### Script Completo: Configurazione FSLogix via Registry

```powershell
# ============================================================
# CONFIGURAZIONE COMPLETA FSLogix — DA ESEGUIRE SUI SESSION HOST
# ============================================================

function Set-FSLogixConfiguration {
    param(
        [Parameter(Mandatory)]
        [string]$VHDLocations,

        [int]$SizeInMBs = 30000,
        [switch]$EnableOfficeContainer,
        [string]$OfficeVHDLocations
    )

    $regPath = "HKLM:\SOFTWARE\FSLogix\Profiles"
    if (-not (Test-Path $regPath)) {
        New-Item -Path $regPath -Force | Out-Null
    }

    # Configurazione Profile Container
    $settings = @{
        Enabled                           = 1
        VHDLocations                      = $VHDLocations
        SizeInMBs                         = $SizeInMBs
        VolumeType                        = "VHDX"
        IsDynamic                         = 1
        FlipFlopProfileDirectoryName      = 1
        DeleteLocalProfileWhenVHDShouldApply = 1
        LockedRetryCount                  = 3
        LockedRetryInterval               = 15
        ReAttachIntervalSeconds           = 15
        ReAttachRetryCount                = 3
        VHDCompactDisk                    = 1
    }

    foreach ($key in $settings.Keys) {
        $type = if ($settings[$key] -is [int]) { "DWord" } else { "String" }
        Set-ItemProperty -Path $regPath -Name $key -Value $settings[$key] -Type $type
        Write-Host "  Impostato: $key = $($settings[$key])"
    }

    # Configurazione Office Container (se richiesta)
    if ($EnableOfficeContainer -and $OfficeVHDLocations) {
        $officeRegPath = "HKLM:\SOFTWARE\Policies\FSLogix\ODFC"
        if (-not (Test-Path $officeRegPath)) {
            New-Item -Path $officeRegPath -Force | Out-Null
        }

        $officeSettings = @{
            Enabled                      = 1
            VHDLocations                 = $OfficeVHDLocations
            VolumeType                   = "VHDX"
            IsDynamic                    = 1
            IncludeOfficeActivation      = 1
            IncludeOutlook               = 1
            IncludeOutlookPersonalization = 1
            IncludeTeams                 = 1
            IncludeOneDrive              = 1
            IncludeOneNote               = 1
            IncludeSharePoint            = 1
            FlipFlopProfileDirectoryName = 1
        }

        foreach ($key in $officeSettings.Keys) {
            $type = if ($officeSettings[$key] -is [int]) { "DWord" } else { "String" }
            Set-ItemProperty -Path $officeRegPath -Name $key -Value $officeSettings[$key] -Type $type
            Write-Host "  ODFC: $key = $($officeSettings[$key])"
        }
    }

    Write-Host "`nConfigurazione FSLogix completata." -ForegroundColor Green
    Write-Host "Riavviare il servizio: Restart-Service frxsvc" -ForegroundColor Yellow
}

# Esempio di utilizzo — solo Profile Container (raccomandato per nuovi deploy):
Set-FSLogixConfiguration -VHDLocations "\\SRV01\FSLogix$"

# Esempio con Office Container separato (solo se si usa Citrix UPM, VMware DEM, etc.):
# Set-FSLogixConfiguration -VHDLocations "\\SRV01\FSLogix$" `
#     -EnableOfficeContainer -OfficeVHDLocations "\\SRV01\FSLogix-Office$"
```

### Profile Container vs Office Container — Quando Separare

```
Nota importante (aggiornamento 2024+):
Nei deploy NUOVI, Microsoft consiglia di usare SOLO il Profile Container
senza separare l'Office Container, salvo ambienti con soluzioni profilo
pre-esistenti (Citrix UPM, VMware DEM, Liquidware ProfileUnity).

Il Profile Container cattura già TUTTI i dati Office (Outlook cache, Teams,
OneDrive sync state, attivazione licenza). Separare l'Office Container:
- Raddoppia il numero di file VHDX da gestire
- Aumenta i punti di fallimento
- Complica backup e disaster recovery
- Aggiunge complessità senza beneficio in ambienti greenfield

QUANDO ha senso separare:
┌──────────────────────────────────────────────────────────────┐
│  SCENARIO                          │  USARE SOLO PROFILE?   │
├────────────────────────────────────┼────────────────────────┤
│  Deploy nuovo (greenfield)         │  SÌ — solo Profile     │
│  Migrazione da Citrix UPM          │  NO — Profile + ODFC   │
│  Migrazione da VMware DEM          │  NO — Profile + ODFC   │
│  Azure Virtual Desktop nuovo       │  SÌ — solo Profile     │
│  RDS con profili già gestiti       │  DIPENDE — valutare    │
│  Requisito backup Office separato  │  VALUTARE — Profile +  │
│                                    │  Folder Redirect per   │
│                                    │  i documenti           │
└────────────────────────────────────┴────────────────────────┘
```

### Avviso Sicurezza: Hardening Kerberos AES-SHA1 (Aprile 2026)

```
ATTENZIONE — MODIFICA CRITICA
A partire dall'aggiornamento cumulativo di Windows Server di aprile 2026,
il tipo di crittografia Kerberos predefinito passa da RC4 a AES-SHA1.

Le file share che ospitano container FSLogix e che NON sono aggiornate
per supportare AES-SHA1 POTREBBERO avere problemi di accesso dopo
l'applicazione di questo aggiornamento.

AZIONE RICHIESTA prima dell'installazione dell'aggiornamento:
1. Verificare la configurazione Kerberos sui file server:
   Get-ADComputer -Filter * -Properties msDS-SupportedEncryptionTypes
2. Assicurarsi che i file server supportino AES128/AES256
3. Per Azure Files: verificare che l'account di storage sia configurato
   per autenticazione Kerberos con AES-256
4. Testare l'accesso ai container FSLogix in un ambiente di staging
   PRIMA di applicare l'aggiornamento in produzione

Riferimento: Microsoft Learn, FSLogix documentation, marzo 2026.
```

---

## FSLogix — Cloud Cache e Multi-Site

```powershell
# Cloud Cache permette a FSLogix di usare multiple storage locations
# con replica locale per resilienza e performance

# ============================================================
# CLOUD CACHE ARCHITECTURE
# ============================================================
#
# ┌─────────────────────────────────────────────────────┐
# │                   SESSION HOST                       │
# │   ┌───────────────────────────────────┐             │
# │   │    Cloud Cache Provider            │             │
# │   │    (cache locale in memoria)       │             │
# │   └───────────┬───────────────────────┘             │
# │               │                                      │
# │    ┌──────────┼──────────┐                          │
# │    ↓          ↓          ↓                          │
# │  SMB 1     SMB 2     Azure Blob                    │
# │  (Site A)  (Site B)  (Azure Storage)               │
# │                                                      │
# │  Scritte simultanee su tutte le location             │
# │  Lettura dalla cache locale (veloce)                 │
# │  Se una location è offline → le altre funzionano     │
# └─────────────────────────────────────────────────────┘

# Configurazione Cloud Cache:
# Computer → FSLogix → Profile Containers
# VHD Locations:
#   type=smb,connectionString=\\SRV01-MI\FSLogix$;
#   type=smb,connectionString=\\SRV01-RM\FSLogix$;
#   type=azure,connectionString=<azure-blob-connection-string>

# Nota: Cloud Cache sostituisce VHDLocations standard
# Non usare entrambi

# Requisiti:
# - Bandwidth sufficiente tra i siti
# - Latenza accettabile (< 80ms consigliato)
# - Azure Storage Account per la replica cloud (opzionale)

# Monitoraggio Cloud Cache:
# Event Viewer → FSLogix → CloudCache → Operational
# Log: C:\ProgramData\FSLogix\Logs\CloudCache*.log
```

---

## Servizi Windows

### Gestione Servizi

```powershell
# Elencare servizi
Get-Service | Where-Object Status -eq Running | Sort-Object DisplayName
Get-Service -Name "wuauserv" | Format-List *

# Avviare / Fermare / Riavviare
Start-Service -Name "wuauserv"
Stop-Service -Name "wuauserv" -Force
Restart-Service -Name "wuauserv"

# Tipo avvio
Set-Service -Name "wuauserv" -StartupType Automatic  # Automatic, Manual, Disabled
Set-Service -Name "wuauserv" -StartupType Disabled

# Delayed Start
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\wuauserv" `
    -Name "DelayedAutoStart" -Value 1

# Account servizio
# Preferire gMSA (Group Managed Service Accounts) o MSA
# EVITARE account utente normali per i servizi

# Verificare da cosa dipende un servizio
Get-Service -Name "DNS" -DependentServices  # Servizi che dipendono da DNS
Get-Service -Name "DNS" -RequiredServices   # Servizi da cui DNS dipende

# Servizi su computer remoto
Get-Service -ComputerName SRV01 | Where-Object Status -eq Stopped |
    Where-Object StartType -eq Automatic

# Recovery (azione quando il servizio crasha)
sc.exe failure wuauserv reset= 86400 actions= restart/60000/restart/120000/restart/300000
# Reset counter dopo 86400 sec (24h)
# 1° fallimento: restart dopo 60 sec
# 2° fallimento: restart dopo 120 sec
# 3° fallimento: restart dopo 300 sec
```

### Servizi Critici Windows

```
Servizi che NON devono essere disabilitati:
├── EventLog             → Logging eventi (sempre Automatic)
├── RPCSS                → RPC runtime (Automatic)
├── DcomLaunch           → DCOM Server Process Launcher
├── BFE                  → Base Filtering Engine (firewall)
├── MpsSvc               → Windows Defender Firewall
├── WinDefend            → Windows Defender Antivirus
├── CryptSvc             → Cryptographic Services
├── Winmgmt              → WMI (fondamentale per monitoring)
├── LanmanServer         → File/print sharing (SMB)
├── LanmanWorkstation    → Client SMB
├── Netlogon             → Autenticazione dominio
├── W32Time              → Sincronizzazione tempo
├── DNS (se DC)          → DNS Server
├── NTDS (se DC)         → Active Directory DS
└── CertSvc (se CA)      → Certificate Services

Servizi spesso disabilitabili (se non necessari):
├── Spooler              → Solo se non si stampa
├── RemoteRegistry       → Se non serve gestione remota registry
├── XboxGipSvc           → Servizi Xbox (su server)
├── WSearch              → Windows Search indexing (valutare)
└── Fax                  → Servizio fax
```

---

---

## Service Account — gMSA e MSA

### Group Managed Service Account (gMSA)

```powershell
# gMSA è la soluzione moderna per account di servizio in AD
# Password gestita automaticamente da AD (240 char, rotazione ogni 30 giorni)
# Nessun intervento manuale per cambio password

# ============================================================
# SETUP gMSA — PREREQUISITI
# ============================================================

# 1. Creare la KDS Root Key (una sola volta per foresta)
# La chiave KDS genera le password per tutti i gMSA
Add-KdsRootKey -EffectiveImmediately
# NOTA: in produzione, la chiave è disponibile dopo 10 ore (replica DC)
# Per lab/test, per renderla immediatamente disponibile:
Add-KdsRootKey -EffectiveTime ((Get-Date).AddHours(-10))

# 2. Verificare che la KDS Root Key esista
Get-KdsRootKey

# ============================================================
# CREAZIONE gMSA
# ============================================================

# 3. Creare un gruppo AD per i server autorizzati a usare il gMSA
New-ADGroup -Name "gMSA-SQLServers" -GroupScope Global `
    -GroupCategory Security -Path "OU=ServiceAccounts,DC=corp,DC=contoso,DC=com"

# 4. Aggiungere i computer al gruppo
Add-ADGroupMember -Identity "gMSA-SQLServers" -Members "SRV-SQL01$", "SRV-SQL02$"
# NOTA: il $ dopo il nome indica l'account computer

# 5. Creare il gMSA
New-ADServiceAccount -Name "gMSA-SQL" `
    -DNSHostName "gMSA-SQL.corp.contoso.com" `
    -PrincipalsAllowedToRetrieveManagedPassword "gMSA-SQLServers" `
    -Path "OU=ServiceAccounts,DC=corp,DC=contoso,DC=com" `
    -KerberosEncryptionType AES128, AES256

# 6. Installare il gMSA sul server che lo userà
# (eseguire su ogni server nel gruppo)
Install-ADServiceAccount -Identity "gMSA-SQL"

# 7. Testare
Test-ADServiceAccount -Identity "gMSA-SQL"
# Output: True = funziona

# 8. Configurare il servizio per usare il gMSA
# services.msc → Servizio → Properties → Log On → This account:
# CORP\gMSA-SQL$  (con il $ finale, password VUOTA)

# Via PowerShell:
sc.exe config "MSSQLSERVER" obj= "CORP\gMSA-SQL$" password= ""
# O per servizi che supportano gMSA nativamente:
# SQL Server Configuration Manager → SQL Server → Properties → Log On

# ============================================================
# gMSA — CASI D'USO COMUNI
# ============================================================
#
# - SQL Server service account
# - IIS Application Pool identity
# - Windows Task Scheduler (Run As)
# - SCCM Site System accounts
# - Servizi custom .NET / PowerShell
# - Backup agent service account

# Elencare tutti i gMSA nel dominio
Get-ADServiceAccount -Filter * -Properties PrincipalsAllowedToRetrieveManagedPassword |
    Select-Object Name, DNSHostName, Created,
        @{N='AuthorizedServers';E={$_.PrincipalsAllowedToRetrieveManagedPassword}}

# Verificare su quali server è installato un gMSA
$gmsa = Get-ADServiceAccount -Identity "gMSA-SQL" -Properties PrincipalsAllowedToRetrieveManagedPassword
$gmsa.PrincipalsAllowedToRetrieveManagedPassword | ForEach-Object {
    $group = Get-ADGroup $_ -Properties Members
    $group.Members | ForEach-Object { (Get-ADComputer $_).Name }
}
```

### Service Account — Best Practice e Audit

```powershell
# Audit: trovare servizi che usano account utente (da migrare a gMSA)
function Find-ServiceAccountsToMigrate {
    param([string[]]$Computers)

    foreach ($pc in $Computers) {
        try {
            $services = Get-CimInstance Win32_Service -ComputerName $pc -ErrorAction Stop |
                Where-Object {
                    $_.StartName -notin @(
                        "LocalSystem", "NT AUTHORITY\LocalService",
                        "NT AUTHORITY\NetworkService", "NT AUTHORITY\SYSTEM",
                        "Local System", "NT Authority\Local Service",
                        "NT Authority\Network Service"
                    ) -and $_.StartName -notlike "*`$"  # Escludi gMSA (terminano con $)
                }

            foreach ($svc in $services) {
                [PSCustomObject]@{
                    Computer    = $pc
                    ServiceName = $svc.Name
                    DisplayName = $svc.DisplayName
                    StartName   = $svc.StartName
                    StartMode   = $svc.StartMode
                    State       = $svc.State
                    Action      = "MIGRARE a gMSA"
                }
            }
        }
        catch {
            Write-Warning "Impossibile connettersi a: $pc"
        }
    }
}

# Esempio: scansionare tutti i server del dominio
$servers = (Get-ADComputer -Filter 'OperatingSystem -like "*Server*"').Name
$results = Find-ServiceAccountsToMigrate -Computers $servers
$results | Export-Csv "C:\Reports\ServiceAccounts-ToMigrate.csv" -NoTypeInformation
$results | Format-Table -AutoSize
```

### dMSA — Delegated Managed Service Account (Server 2025)

Windows Server 2025 introduce i **dMSA** (Delegated Managed Service Account), un nuovo tipo di account di servizio progettato per eliminare il rischio di Kerberoasting e furto di credenziali. A differenza dei gMSA, le credenziali del dMSA non lasciano mai il domain controller.

#### Differenze Architetturali rispetto a gMSA

```
┌──────────────────────────────────────────────────────────────────┐
│            FLUSSO AUTENTICAZIONE: gMSA vs dMSA                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  gMSA (Group Managed Service Account):                           │
│  ┌──────┐      Password hash       ┌───────┐                    │
│  │  DC  │ ──────────────────────▶  │ Server│  ← password        │
│  └──────┘   (recuperabile dal      └───────┘    presente         │
│              server autorizzato)       │        sul server       │
│                                        ▼                         │
│                                   [Servizio]                     │
│  Rischio: il password hash è sul server → attaccabile            │
│                                                                  │
│  dMSA (Delegated Managed Service Account):                       │
│  ┌──────┐   Ticket Kerberos legato  ┌───────┐                   │
│  │  DC  │ ────────alla macchina───▶ │ Server│  ← nessuna        │
│  └──────┘   (derivato dall'identità └───────┘    password        │
│              macchina, non estraibile)  │        presente         │
│                                        ▼                         │
│                                   [Servizio]                     │
│  Il secret esiste SOLO sul DC. Non è estraibile.                 │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

#### Tabella Comparativa — Tutti i Tipi di Account di Servizio

| Aspetto | Account Utente Tradizionale | MSA (sMSA) | gMSA | dMSA (Server 2025) |
|---------|----------------------------|------------|------|---------------------|
| Gestione password | Manuale | Automatica (AD) | Automatica (AD) | Automatica (AD) |
| Rotazione password | Manuale (rischio scadenza) | Ogni 30 gg | Ogni 30 gg | Periodica + machine-bound |
| Multi-server | Sì (stessa password ovunque) | NO (1 solo server) | SÌ (gruppo server) | NO (1 solo server) |
| Kerberoasting | VULNERABILE | Vulnerabile | Vulnerabile (hash estraibile) | IMMUNE (secret solo su DC) |
| Credential theft | VULNERABILE (password nota) | Ridotto | Ridotto (hash su server) | ELIMINATO (nessun hash locale) |
| Requisiti OS | Qualsiasi | Server 2008 R2+ | Server 2012+ | Server 2025+ (DC e client) |
| Credential Guard | Non applicabile | Compatibile | Compatibile | Integrato nativamente |
| Migrazione da SA tradizionale | N/A | Supportata | Supportata | Supportata (da SA tradizionale) |
| Migrazione da gMSA | N/A | N/A | N/A | NON supportata |

#### Creazione e Configurazione dMSA

```powershell
# ============================================================
# PREREQUISITI dMSA
# ============================================================

# 1. Almeno un Domain Controller con Windows Server 2025
# 2. Schema AD aggiornato a Windows Server 2025
# 3. Client/server che userà il dMSA: deve supportare dMSA (Win Server 2025)

# Verificare il livello funzionale del dominio
Get-ADDomain | Select-Object DomainMode
# Deve essere Windows2025Domain o superiore

# ============================================================
# ABILITARE dMSA SUL SERVER TARGET
# ============================================================

# Impostare la chiave di registro sul server che userà il dMSA
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\Kerberos\Parameters" `
    -Name "DelegatedMSAEnabled" -Value 1 -Type DWord

# Riavviare il servizio Kerberos o il server per applicare la modifica
Restart-Service "Kdc" -ErrorAction SilentlyContinue

# ============================================================
# CREARE IL dMSA
# ============================================================

# Creare il dMSA con AES256 (il tipo di crittografia più sicuro)
New-ADServiceAccount -Name "dMSA-WebApp" `
    -DNSHostName "dMSA-WebApp.corp.contoso.com" `
    -CreateDelegatedServiceAccount $true `
    -KerberosEncryptionType AES256 `
    -Path "OU=ServiceAccounts,DC=corp,DC=contoso,DC=com"

# ============================================================
# AUTORIZZARE IL SERVER A USARE IL dMSA
# ============================================================

# Concedere al server specifico il permesso di usare il dMSA
$serverDN = (Get-ADComputer "SRV-WEB01").DistinguishedName
Set-ADServiceAccount -Identity "dMSA-WebApp" `
    -PrincipalsAllowedToDelegateToAccount $serverDN

# ============================================================
# INSTALLARE E TESTARE
# ============================================================

# Sul server target:
Install-ADServiceAccount -Identity "dMSA-WebApp"
Test-ADServiceAccount -Identity "dMSA-WebApp"
# Output atteso: True

# Configurare il servizio
sc.exe config "W3SVC" obj= "CORP\dMSA-WebApp$" password= ""
```

#### Migrazione da Account Tradizionale a dMSA

```powershell
# La migrazione da account di servizio tradizionale a dMSA è supportata
# ATTENZIONE: la migrazione da gMSA a dMSA NON è supportata

# 1. Identificare il service account corrente
$currentSA = Get-CimInstance Win32_Service -Filter "Name='CustomService'" |
    Select-Object Name, StartName
Write-Host "Account corrente: $($currentSA.StartName)"

# 2. Creare il dMSA sostitutivo
New-ADServiceAccount -Name "dMSA-CustomSvc" `
    -DNSHostName "dMSA-CustomSvc.corp.contoso.com" `
    -CreateDelegatedServiceAccount $true `
    -KerberosEncryptionType AES256

# 3. Il dMSA supporta la migrazione: AD disabilita la password
#    dell'account tradizionale originale durante il processo
#    I ticket Kerberos esistenti continuano a funzionare fino alla scadenza

# 4. Dopo la migrazione, l'account tradizionale viene disabilitato
#    ma non eliminato, per consentire il rollback

# ============================================================
# CREDENTIAL GUARD CON dMSA
# ============================================================

# Credential Guard può essere usato per migliorare la sicurezza dei dMSA
# Quando abilitato:
# - Rotazione automatica delle password a ogni reboot
# - Tutti i ticket del service account sono vincolati alla macchina
# - Protezione hardware-backed (se TPM disponibile)

# Verificare se Credential Guard è abilitato
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
    Select-Object AvailableSecurityProperties, RequiredSecurityProperties,
        SecurityServicesConfigured, SecurityServicesRunning
```

#### Quando Usare dMSA vs gMSA

```
DECISIONE: dMSA o gMSA?

┌─────────────────────────────────────────────────────┐
│  Il servizio gira su PIÙ server contemporaneamente? │
│  (cluster, farm, load balancer)                     │
└─────────┬────────────────────────┬──────────────────┘
          │                        │
        SÌ                       NO
          │                        │
     Usare gMSA              ┌─────┴──────────────────┐
     (multi-server)           │  Hai Server 2025 come  │
                              │  DC e come target?     │
                              └─────┬──────────┬───────┘
                                    │          │
                                  SÌ          NO
                                    │          │
                               Usare dMSA    Usare gMSA
                               (protezione   (compatibilità)
                                massima)

Nota: dMSA è preferibile quando disponibile, perché elimina il rischio
di furto credenziali. Tuttavia, richiede Windows Server 2025 sia come DC
sia come server target — un requisito ancora restrittivo (2026).
```

---

## Servizi Windows — Gestione Avanzata

### Recovery Actions e Monitoring

```powershell
# ============================================================
# CONFIGURAZIONE RECOVERY ACTIONS — BEST PRACTICE
# ============================================================

# Recovery actions determinano cosa succede quando un servizio crasha

# Configurazione via sc.exe (più flessibile di PowerShell)
# Sintassi: sc failure <servizio> reset= <sec> actions= <azione1>/<delay1>/...

# Esempio: servizio critico con recovery progressivo
sc.exe failure "CustomService" reset= 86400 actions= restart/30000/restart/60000/run/120000
# reset= 86400    → resetta il contatore errori dopo 24 ore
# 1° fallimento:  restart dopo 30 secondi
# 2° fallimento:  restart dopo 60 secondi
# 3°+ fallimento: esegui un programma dopo 120 secondi

# Specificare il programma da eseguire al 3° fallimento
sc.exe failureflag "CustomService" 1
sc.exe failure "CustomService" command= "powershell.exe -File C:\Scripts\ServiceAlert.ps1"

# Verificare configurazione recovery
sc.exe qfailure "CustomService"

# ============================================================
# CONFIGURARE RECOVERY PER TUTTI I SERVIZI CRITICI
# ============================================================

$criticalServices = @(
    @{ Name = "W32Time";       Actions = "restart/30000/restart/60000/restart/120000" },
    @{ Name = "Netlogon";      Actions = "restart/30000/restart/60000/restart/120000" },
    @{ Name = "DNS";           Actions = "restart/30000/restart/60000/restart/120000" },
    @{ Name = "NTDS";          Actions = "restart/30000/restart/60000/restart/120000" },
    @{ Name = "LanmanServer";  Actions = "restart/30000/restart/60000/restart/120000" },
    @{ Name = "EventLog";      Actions = "restart/15000/restart/30000/restart/60000" },
    @{ Name = "CryptSvc";      Actions = "restart/30000/restart/60000/restart/120000" }
)

foreach ($svc in $criticalServices) {
    sc.exe failure $svc.Name reset= 86400 actions= $svc.Actions
    Write-Host "Recovery configurato per: $($svc.Name)"
}
```

### Dipendenze Servizi — Analisi e Gestione

```powershell
# Capire le dipendenze è fondamentale per troubleshooting

# Visualizzare albero dipendenze
function Get-ServiceDependencyTree {
    param([string]$ServiceName, [int]$Depth = 0)

    $prefix = "  " * $Depth
    $svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $svc) { return }

    Write-Host "$prefix├── $($svc.Name) ($($svc.DisplayName)) [$($svc.Status)]"

    $deps = Get-Service -Name $ServiceName -DependentServices -ErrorAction SilentlyContinue
    foreach ($dep in $deps) {
        Get-ServiceDependencyTree -ServiceName $dep.Name -Depth ($Depth + 1)
    }
}

# Esempio: albero dipendenze del DNS
Get-ServiceDependencyTree -ServiceName "DNS"

# Trovare servizi senza dipendenze (potenzialmente disabilitabili)
Get-Service | Where-Object {
    $req = $_ | Select-Object -ExpandProperty RequiredServices -ErrorAction SilentlyContinue
    $dep = $_ | Select-Object -ExpandProperty DependentServices -ErrorAction SilentlyContinue
    $req.Count -eq 0 -and $dep.Count -eq 0
} | Select-Object Name, DisplayName, Status, StartType |
    Sort-Object Status, DisplayName | Format-Table -AutoSize
```

### Servizi — Creazione e Gestione Custom

```powershell
# Creare un servizio Windows personalizzato
# Utile per script PowerShell che devono girare come servizio

# Metodo 1: sc.exe (nativo, per eseguibili .exe)
sc.exe create "MyCustomService" `
    binpath= "C:\Services\MyService.exe" `
    displayname= "My Custom Service" `
    start= auto `
    obj= "CORP\gMSA-CustomSvc$" `
    password= ""

# Aggiungere descrizione
sc.exe description "MyCustomService" "Servizio personalizzato per elaborazione dati"

# Metodo 2: New-Service (PowerShell)
New-Service -Name "MyCustomService" `
    -BinaryPathName "C:\Services\MyService.exe" `
    -DisplayName "My Custom Service" `
    -StartupType Automatic `
    -Description "Servizio personalizzato per elaborazione dati" `
    -Credential (New-Object PSCredential "CORP\gMSA-CustomSvc$", (New-Object SecureString))

# Per script PowerShell come servizio, usare NSSM (Non-Sucking Service Manager)
# nssm.exe install "PSService" powershell.exe "-ExecutionPolicy Bypass -File C:\Scripts\service.ps1"
# nssm.exe set "PSService" AppDirectory "C:\Scripts"
# nssm.exe set "PSService" DisplayName "PowerShell Background Service"
# nssm.exe set "PSService" Start SERVICE_AUTO_START

# Rimuovere un servizio
sc.exe delete "MyCustomService"
# O:
Remove-Service -Name "MyCustomService"  # PowerShell 6+
```

---

## GPO per Profili e Servizi

```powershell
# ============================================================
# GPO — PROFILI UTENTE
# ============================================================

# Computer → Administrative Templates → System → User Profiles

# Delete cached copies of roaming profiles: Enabled
#   → Rimuove la copia locale del roaming profile al logoff
#   → Risparmia spazio disco sulla workstation

# Do not check for user ownership of Roaming Profile Folders: Disabled
#   → DEVE restare disabilitato per sicurezza
#   → Impedisce hijacking del profilo

# Set roaming profile path for all users: \\SRV01\Profiles$\%USERNAME%
#   → Alternativa a impostare il path su ogni utente AD

# Limit profile size: 500 MB (opzionale)
#   → Avviso all'utente se il profilo supera la soglia
#   → Non impedisce il login (solo warning)

# Exclude directories in roaming profile:
#   AppData\Local;AppData\LocalLow;Downloads;Music;Videos
#   → Riduce drasticamente la dimensione del roaming profile
#   → Queste cartelle non vengono copiate sulla share

# Wait for remote user profile: Enabled
#   → Aspetta che il profilo remoto sia caricato
#   → Evita di caricare un profilo locale temporaneo

# Timeout for dialog boxes: 30 (secondi)
#   → Quanto aspettare prima di caricare profilo locale

# ============================================================
# GPO — SERVIZI
# ============================================================

# Computer → Windows Settings → Security Settings → System Services

# Per ogni servizio si può impostare:
# - Startup Mode: Automatic, Manual, Disabled
# - Security (chi può avviare/fermare)

# Esempio: disabilitare servizi non necessari via GPO
# Xbox Game Bar Service → Disabled
# Fax → Disabled
# Remote Registry → Disabled (se non necessario)
# Print Spooler → Disabled (su server non-print)

# ============================================================
# GPO — LOGON/LOGOFF SCRIPTS
# ============================================================

# User → Windows Settings → Scripts → Logon
# Utili per:
# - Mappare drive di rete
# - Configurare stampanti
# - Pulire file temporanei
# - Sincronizzare impostazioni

# Computer → Windows Settings → Scripts → Startup
# Utili per:
# - Configurazioni a livello macchina
# - Aggiornamenti agent
# - Configurazione servizi
```

---

## Automazione e Script Enterprise

### Script: Monitoraggio Dimensione Profili

```powershell
# Monitorare le dimensioni dei profili FSLogix su tutta la share
function Get-FSLogixProfileReport {
    param(
        [string]$SharePath = "\\SRV01\FSLogix$",
        [int]$WarningThresholdGB = 15,
        [int]$CriticalThresholdGB = 25
    )

    $profiles = Get-ChildItem $SharePath -Directory | ForEach-Object {
        $vhdFiles = Get-ChildItem $_.FullName -Filter "*.VHDX" -ErrorAction SilentlyContinue
        foreach ($vhd in $vhdFiles) {
            $sizeGB = [math]::Round($vhd.Length / 1GB, 2)
            $status = switch {
                ($sizeGB -ge $CriticalThresholdGB) { "CRITICAL" }
                ($sizeGB -ge $WarningThresholdGB)  { "WARNING" }
                default                            { "OK" }
            }

            [PSCustomObject]@{
                User       = $_.Name -replace 'S-1-5-21-[\d-]+_',''
                SID        = ($_.Name -split '_')[0]
                VHDFile    = $vhd.Name
                SizeGB     = $sizeGB
                LastWrite  = $vhd.LastWriteTime
                Status     = $status
            }
        }
    }

    # Riepilogo
    Write-Host "`n=== RIEPILOGO PROFILI FSLOGIX ==="
    Write-Host "Totale profili: $($profiles.Count)"
    Write-Host "OK:       $(($profiles | Where-Object Status -eq 'OK').Count)"
    Write-Host "WARNING:  $(($profiles | Where-Object Status -eq 'WARNING').Count)"
    Write-Host "CRITICAL: $(($profiles | Where-Object Status -eq 'CRITICAL').Count)"
    Write-Host "Spazio totale: $([math]::Round(($profiles | Measure-Object SizeGB -Sum).Sum, 2)) GB"

    # Mostrare profili critici
    $critical = $profiles | Where-Object Status -ne "OK" | Sort-Object SizeGB -Descending
    if ($critical) {
        Write-Host "`nProfili che richiedono attenzione:"
        $critical | Format-Table -AutoSize
    }

    return $profiles
}

# Uso:
# $report = Get-FSLogixProfileReport -SharePath "\\SRV01\FSLogix$"
# $report | Export-Csv "C:\Reports\FSLogix-Report.csv" -NoTypeInformation
```

### Script: Migrazione Roaming Profiles → FSLogix

```powershell
# Script per migrare da Roaming Profiles a FSLogix
# PIANIFICAZIONE: eseguire fuori orario lavorativo

function Migrate-RoamingToFSLogix {
    param(
        [string]$RoamingSharePath = "\\SRV01\Profiles$",
        [string]$FSLogixSharePath = "\\SRV01\FSLogix$",
        [int]$VHDSizeMB = 30000,
        [string[]]$Users
    )

    foreach ($user in $Users) {
        Write-Host "`n=== Migrazione profilo: $user ===" -ForegroundColor Cyan

        $roamingPath = Join-Path $RoamingSharePath "$user.V6"
        if (-not (Test-Path $roamingPath)) {
            Write-Warning "Profilo roaming non trovato: $roamingPath"
            continue
        }

        # Ottenere SID dell'utente
        $adUser = Get-ADUser -Identity $user
        $sid = $adUser.SID.Value

        # Creare cartella FSLogix
        $fslogixUserPath = Join-Path $FSLogixSharePath "${sid}_${user}"
        New-Item $fslogixUserPath -ItemType Directory -Force | Out-Null

        # Creare VHD
        $vhdPath = Join-Path $fslogixUserPath "Profile_${user}.VHDX"
        $diskpart = @"
create vdisk file="$vhdPath" maximum=$VHDSizeMB type=expandable
select vdisk file="$vhdPath"
attach vdisk
create partition primary
format fs=ntfs quick label="FSLogix-$user"
assign letter=Z
"@
        $diskpart | diskpart

        # Copiare contenuto profilo nel VHD
        robocopy $roamingPath "Z:\Profile" /E /COPYALL /R:1 /W:1 /XD "AppData\Local\Temp"

        # Smontare VHD
        $diskpartDetach = @"
select vdisk file="$vhdPath"
detach vdisk
"@
        $diskpartDetach | diskpart

        # Aggiornare utente AD (rimuovere roaming profile path)
        # Set-ADUser -Identity $user -ProfilePath $null
        # Decommentare quando pronti per il cutover

        Write-Host "Migrazione completata per: $user" -ForegroundColor Green
    }
}
```

### Script: Health Check Servizi Critici

```powershell
# Monitorare lo stato dei servizi critici su tutti i server
function Test-CriticalServices {
    param(
        [string[]]$Computers,
        [hashtable]$ServiceMap  # Computer → servizi attesi
    )

    $results = foreach ($pc in $Computers) {
        $expectedServices = if ($ServiceMap.ContainsKey($pc)) {
            $ServiceMap[$pc]
        } else {
            @("EventLog", "W32Time", "Winmgmt", "CryptSvc")  # Default
        }

        foreach ($svcName in $expectedServices) {
            try {
                $svc = Get-Service -Name $svcName -ComputerName $pc -ErrorAction Stop
                [PSCustomObject]@{
                    Computer    = $pc
                    Service     = $svcName
                    DisplayName = $svc.DisplayName
                    Status      = $svc.Status
                    StartType   = $svc.StartType
                    IsHealthy   = $svc.Status -eq "Running"
                }
            }
            catch {
                [PSCustomObject]@{
                    Computer    = $pc
                    Service     = $svcName
                    DisplayName = "N/A"
                    Status      = "UNREACHABLE"
                    StartType   = "N/A"
                    IsHealthy   = $false
                }
            }
        }
    }

    # Mostrare solo problemi
    $problems = $results | Where-Object { -not $_.IsHealthy }
    if ($problems) {
        Write-Host "`n!!! SERVIZI CON PROBLEMI !!!" -ForegroundColor Red
        $problems | Format-Table -AutoSize
    }
    else {
        Write-Host "`nTutti i servizi critici sono operativi." -ForegroundColor Green
    }

    return $results
}

# Uso:
# $map = @{
#     "DC01" = @("DNS","NTDS","Netlogon","W32Time","EventLog")
#     "DC02" = @("DNS","NTDS","Netlogon","W32Time","EventLog")
#     "SRV-SQL01" = @("MSSQLSERVER","SQLSERVERAGENT","EventLog")
#     "SRV-WEB01" = @("W3SVC","EventLog","CryptSvc")
# }
# Test-CriticalServices -Computers $map.Keys -ServiceMap $map
```

---

## Scenari Reali Enterprise

### Scenario 1: Deployment FSLogix per Azure Virtual Desktop

```
CONTESTO: 200 utenti, Azure Virtual Desktop multi-session, Office 365 E3
OBIETTIVO: Login < 15 secondi, nessun problema Outlook/Teams/OneDrive

ARCHITETTURA:
- Azure Storage Account (Premium File Share) per VHD FSLogix
- 2 Session Host Pool (40 VM Windows 11 Multi-session)
- FSLogix Profile + Office Container separati

CONFIGURAZIONE:
1. Azure Storage Account
   - Performance: Premium
   - Tipo: FileStorage
   - Share: fslogix-profiles (5 TB), fslogix-office (3 TB)
   - Autenticazione: Azure AD Kerberos

2. FSLogix GPO:
   - Profile Container: \\<storage>.file.core.windows.net\fslogix-profiles
   - Office Container: \\<storage>.file.core.windows.net\fslogix-office
   - Size: 30 GB profile, 20 GB office
   - Dynamic: Yes
   - DeleteLocalProfile: Yes
   - Redirections.xml: escludere cache browser e Teams

3. Risultati:
   - Login time: 8-12 secondi (da 45+ con roaming profiles)
   - Outlook: OST file persistente nel Office Container
   - Teams: dati nel Profile Container, cache esclusa
   - OneDrive: sync state nel Office Container
```

### Scenario 2: Migrazione da Roaming Profiles a Folder Redirection

```
CONTESTO: 150 workstation fisiche, 8 sedi, Roaming Profiles attivi
PROBLEMA: Login 3-5 minuti, logoff 2-3 minuti, utenti frustrati
OBIETTIVO: Login < 30 secondi, dati accessibili ovunque

PIANO DI MIGRAZIONE (4 settimane):

Settimana 1: PREPARAZIONE
- Audit dimensione profili (media 2.5 GB, max 12 GB)
- Creare share DFS: \\corp.contoso.com\UserData
- Configurare permessi NTFS corretti
- Creare GPO "Folder Redirection" in test

Settimana 2: PILOT
- 10 utenti volontari IT
- GPO Folder Redirection: Documents, Desktop, Pictures
- Offline Files: abilitati con cache 2 GB
- Monitorare: login time, feedback utenti, Event Log

Settimana 3: ROLLOUT GRADUALE
- Sede per sede (riduce impatto sulla WAN)
- Ogni sera: migrazione batch 20-30 utenti
- Script automatico: robocopy profili → share redirect
- Rimuovere ProfilePath dall'utente AD

Settimana 4: COMPLETAMENTO E CLEANUP
- Ultime sedi
- Verificare tutti gli utenti migrati
- Rimuovere share Roaming Profiles (dopo 30 gg backup)
- Documentare nuova architettura
```

### Scenario 3: gMSA per SQL Server Cluster

```
CONTESTO: SQL Server Always On AG, 3 nodi, account di servizio con password
PROBLEMA: Ogni 90 giorni, cambio password manuale → rischio downtime
OBIETTIVO: Zero maintenance su account servizio

IMPLEMENTAZIONE:
1. Creare KDS Root Key (se non esiste)
2. Creare gruppo AD: gMSA-SQLCluster (membri: SQL01$, SQL02$, SQL03$)
3. Creare gMSA: gMSA-SQL$ con PrincipalsAllowed = gMSA-SQLCluster
4. Su ogni nodo: Install-ADServiceAccount gMSA-SQL
5. SQL Server Configuration Manager → cambiare account servizio
6. Verificare: Test-ADServiceAccount gMSA-SQL → True su ogni nodo
7. Testare failover: l'AG funziona con il gMSA su tutti i nodi

RISULTATO:
- Zero interventi manuali per password
- Password 240 caratteri, rotazione automatica ogni 30 giorni
- Nessun rischio di lockout o scadenza password
- Audit trail in AD per l'uso dell'account
```

---

## Best Practices

1. **FSLogix per VDI/RDS/AVD**: sostituisce Roaming Profiles completamente. Login rapido, nessun file lock. Separare Profile Container da Office Container
2. **Folder Redirection per workstation fisiche**: Documents, Desktop redirect su share DFS, il resto locale. Abilitare Offline Files per lavoro offline
3. **Non usare Roaming Profiles**: legacy, lento, problematico. Se già in uso, pianificare migrazione a FSLogix o Folder Redirection in 4-6 settimane
4. **gMSA per servizi**: password gestite automaticamente da AD, rotazione automatica 30 giorni, nessun intervento manuale. Migrare tutti i servizi da account utente a gMSA
5. **Monitorare dimensione profili**: alert se un profilo FSLogix supera 20 GB (tipicamente indica cache accumulata). Script automatico settimanale
6. **Service recovery configurato**: ogni servizio critico deve avere azioni di recovery (restart automatico con delay progressivo)
7. **Esclusioni antivirus FSLogix**: configurare SEMPRE le esclusioni per VHD/VHDX, processi FSLogix e share. Senza esclusioni, performance degradano del 50%+
8. **Redirections.xml**: escludere cache browser, Teams cache, file temporanei dal Profile Container per ridurre dimensione VHD
9. **Compattazione VHD periodica**: i VHD FSLogix crescono ma non si restringono. Compattazione mensile o abilitare compattazione al logoff
10. **DFS per share profili**: usare namespace DFS per astrazione dal server fisico. Facilita failover e migrazione storage
11. **Audit account servizio trimestrale**: scansionare tutti i server per servizi con account utente. Pianificare migrazione a gMSA
12. **Profili mandatory per postazioni condivise**: chioschi, reception, laboratori → profilo mandatory con NTUSER.MAN
13. **Access Based Enumeration sulle share**: ogni utente vede solo la propria cartella. Abilitare ABE su tutte le share profili
14. **Backup VHD FSLogix**: includere la share FSLogix nel backup notturno. Testare restore trimestrale di un profilo VHD
15. **Documentare le dipendenze servizi**: mantenere una mappa delle dipendenze tra servizi per ogni ruolo server

---

## Troubleshooting

**1. "Login lento con Roaming Profile"** → Il profilo è troppo grande. Verificare dimensione (`dir /s C:\Users\username`), configurare esclusioni GPO (AppData\Local, Downloads), considerare migrazione a FSLogix o Folder Redirection. Profili > 500 MB causano login > 60 secondi su WAN.

**2. "FSLogix VHD non si monta"** → Controllare log `C:\ProgramData\FSLogix\Logs\Profile*.log`. Cause comuni: share non raggiungibile (Test-Path), permessi NTFS/share errati, VHD locked da un'altra sessione (verificare che l'utente non sia loggato altrove con `query user /server:<host>`), spazio insufficiente sulla share.

**3. "Folder Redirection: cartelle vuote dopo primo login"** → La migrazione potrebbe essere in corso (per profili grandi richiede tempo). Verificare: GPO applicata (`gpresult /R /User <user>`), share raggiungibile, permessi corretti. Controllare Event Viewer → Applications → Folder Redirection (Event ID 502 = successo, 510 = errore).

**4. "Servizio non si avvia: Error 1069 (logon failure)"** → L'account del servizio ha password scaduta o cambiata. Aggiornare la password nel servizio (`services.msc` → Properties → Log On) o migrare a gMSA. Se gMSA: verificare `Test-ADServiceAccount` e che il computer sia nel gruppo autorizzato.

**5. "FSLogix: profilo cresce continuamente, supera 30 GB"** → Verificare redirections.xml: cache browser, Teams, OneDrive devono essere esclusi. Controllare AppData\Local per file temporanei. Abilitare compattazione VHD. Verificare che l'utente non salvi file pesanti sul Desktop (redirectare Desktop su share separata).

**6. "Offline Files: conflitto alla sincronizzazione"** → Sync Center mostra conflitti. Cause: lo stesso file modificato localmente e sulla share. Risoluzione: scegliere quale versione mantenere. Prevenzione: GPO per sincronizzare i file prima del logoff, configurare slow-link mode per ridurre le occasioni di lavoro offline non intenzionale.

**7. "Login fallisce con profilo temporaneo (TEMP profile)"** → L'utente riceve un profilo temporaneo — modifiche perse al logoff. Cause: profilo corrotto (NTUSER.DAT danneggiato), SID duplicato, permessi errati sulla cartella profilo. Fix: eliminare il profilo corrotto (`Remove-CimInstance`), rimuovere la chiave SID da `HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\<SID>` con suffisso `.bak`, login dell'utente crea un nuovo profilo.

**8. "gMSA: Test-ADServiceAccount restituisce False"** → Il computer non è nel gruppo autorizzato (`PrincipalsAllowedToRetrieveManagedPassword`). Dopo aver aggiunto il computer al gruppo, RIAVVIARE il computer (il token Kerberos deve essere aggiornato). Verificare che la KDS Root Key sia replicata su tutti i DC.

**9. "Servizio Windows si avvia e si ferma immediatamente"** → Controllare Event Viewer → System e Application per errori del servizio. Cause comuni: dipendenza non avviata (verificare con `Get-Service -RequiredServices`), file eseguibile mancante o corrotto, account di servizio senza permessi "Log on as a service". Concedere: `secpol.msc → Local Policies → User Rights Assignment → Log on as a service`.

**10. "FSLogix su AVD: errore 'Profile in use' quando l'utente si riconnette"** → Il profilo VHD è ancora montato da una sessione precedente non chiusa correttamente. Verificare: `frx list-active-sessions`. Forzare disconnect della sessione orfana. Configurare FSLogix: "Locked retry count: 3", "Locked retry interval: 15". Abilitare "ReAttachIntervalSeconds" per ricollegamento automatico.

**11. "Folder Redirection: GPO non si applica"** → Verificare: `gpresult /R /User <user>` per vedere se la GPO è nel risultato. Se manca: verificare il Security Filtering (il gruppo utente deve avere "Apply Group Policy"). Verificare il link della GPO all'OU corretta. Se presente ma non funziona: verificare connettività alla share, permessi NTFS, e che `Folder Redirection` appaia nell'Event Viewer → Application.

**12. "Servizio: Error 1053 (service did not respond to start or control request in a timely fashion)"** → Il servizio impiega troppo tempo ad avviarsi. Cause: dipendenza lenta, disco lento, rete lenta. Aumentare il timeout: `HKLM:\SYSTEM\CurrentControlSet\Control\ServicesPipeTimeout` (default 30000 ms, impostare 60000 o 120000). Se gMSA: la prima risoluzione della password può essere lenta — attendere e riprovare.

**13. "Profilo FSLogix: applicazione non trova i dati dopo migrazione"** → L'applicazione salvava dati in AppData\Local (che era locale). Con FSLogix, AppData\Local è nel VHD. Verificare che redirections.xml non escluda la cartella dell'app. Verificare che i dati siano stati migrati nel VHD durante la migrazione.

**14. "Roaming Profile: il profilo non si scarica al logoff (logoff lento)"** → File lock: un'applicazione tiene aperto un file (comune con Outlook OST, database Access). Identificare: Process Explorer → Find Handle → cercare file in `C:\Users\<user>`. Soluzione: configurare esclusioni nel ntuser.ini, o forzare la chiusura delle app al logoff via GPO script.

**15. "Servizio di terze parti non funziona con gMSA"** → Non tutte le applicazioni supportano gMSA nativamente. Il servizio deve supportare account che terminano con `$` e password vuota. Workaround: creare un wrapper service con NSSM che usa il gMSA, poi avvia l'applicazione come child process. Alternativa: usare un MSA standard (non group) se il servizio gira su un solo server.

---

## FAQ

**Q1: Qual è la differenza tra Roaming Profiles e Folder Redirection?**
Roaming Profiles copia l'INTERO profilo (NTUSER.DAT + AppData\Roaming + cartelle utente) da/verso una share ad ogni login/logoff. È lento con profili grandi. Folder Redirection reindirizza cartelle SPECIFICHE (Documents, Desktop) su una share di rete — i file restano sulla share e non vengono copiati. Folder Redirection è più efficiente e può essere combinato con Offline Files.

**Q2: FSLogix è gratuito?**
FSLogix è incluso (senza costo aggiuntivo) con: Microsoft 365 E3/E5/A3/A5, Microsoft 365 Business Premium, Windows Enterprise E3/E5, Windows Education A3/A5, Windows VDA, RDS CAL. Non è disponibile standalone per acquisto separato. Verificare la licenza prima del deployment.

**Q3: Posso usare FSLogix su workstation fisiche (non VDI)?**
Tecnicamente sì, FSLogix funziona su workstation fisiche. Ma non è lo scenario ottimale. Per workstation fisiche, Folder Redirection è più semplice e diretto. FSLogix è progettato per ambienti dove l'utente accede a macchine diverse ogni sessione (VDI, RDS, AVD). Su workstation fisiche assegnate, il profilo locale funziona bene.

**Q4: Come funziona il profile container FSLogix internamente?**
Al login, FSLogix monta un file VHD/VHDX dalla share di rete come volume locale. Il contenuto del VHD DIVENTA `C:\Users\<username>`. Il sistema operativo vede il profilo come locale — ma i dati sono nel VHD sulla share. Al logoff, il VHD viene smontato. Il risultato: login veloce (mount, non copia), nessun file lock (il VHD è aperto solo da un host alla volta), supporto completo per tutte le applicazioni.

**Q5: Qual è la differenza tra MSA e gMSA?**
MSA (Managed Service Account): password gestita da AD, ma funziona solo su UN computer. gMSA (Group Managed Service Account): password gestita da AD, funziona su MULTIPLI computer (definiti in un gruppo). Per cluster, farm, e servizi distribuiti: usare gMSA. Per servizi su un solo server: entrambi funzionano, ma gMSA è preferibile per consistenza.

**Q6: Come posso monitorare la salute dei servizi centralmente senza tool terzi?**
Usare Windows Event Forwarding (WEF) per raccogliere eventi di servizio (Event ID 7036 = avvio/arresto, 7031 = crash, 7034 = terminazione inattesa) da tutti i server verso un collector. Combinare con PowerShell scheduled task per report. Alternativa: Performance Monitor con Data Collector Set centralizzato. Per monitoring avanzato: SCOM, Zabbix, o Prometheus con Windows Exporter.

**Q7: Come gestire il profilo quando un utente cambia cognome (e username)?**
(1) Creare il nuovo account AD. (2) Per FSLogix: rinominare la cartella del VHD con il nuovo SID o creare un link simbolico. (3) Per Folder Redirection: i file sono nella share con il vecchio nome — rinominare la cartella o configurare il nuovo utente per puntare alla stessa. (4) Per Roaming Profiles: copiare la cartella profilo con il nuovo nome.

**Q8: Quanto spazio storage devo prevedere per FSLogix?**
Regola empirica: 20-30 GB per utente (VHD dinamico). Con Office Container separato: 10-15 GB profilo + 10-15 GB Office. Per 200 utenti: 6-10 TB di storage con VHD dinamici. Prevedere 20% overhead per compattazione e snapshot backup. Usare storage performance tier (SSD/NVMe) per le share FSLogix — HDD è inaccettabile.

**Q9: Posso avere sia Folder Redirection che FSLogix?**
Sì, e in alcuni scenari è consigliato. Esempio: FSLogix per il profilo (AppData, desktop, registry) + Folder Redirection per Documents (su share separata con backup dedicato). Questo permette backup indipendente dei documenti e riduce la dimensione del VHD FSLogix. Configurare redirections.xml per escludere le cartelle redirectate dal VHD.

**Q10: Come diagnosticare un login lento su VDI con FSLogix?**
Abilitare il log dettagliato: `C:\ProgramData\FSLogix\Logs\Profile*.log`. Cercare i timestamp nel log per identificare la fase lenta. Fasi tipiche: (1) VHD mount, (2) profile load, (3) GPO processing, (4) logon scripts. Se il mount è lento: problema di rete o storage. Se il load è lento: profilo troppo grande. Se le GPO sono lente: troppe GPO o WMI filter complessi.

**Q11: Come impedire che un utente usi un profilo temporaneo?**
GPO: User → Administrative Templates → System → User Profiles → "Do not log users on with temporary profiles": Enabled. Con questa policy, se il profilo non può essere caricato (corrotto, share offline), il login viene RIFIUTATO invece di fornire un profilo temporaneo. Attenzione: può impedire il login se c'è un problema con la share profili.

**Q12: Qual è la best practice per il backup dei profili FSLogix?**
Backup la share FSLogix completa con il tool di backup enterprise (Veeam, Commvault, etc.). Non fare backup dei singoli VHD montati — il lock impedisce la copia. Programmare il backup nelle ore notturne quando gli utenti sono disconnessi. Per Azure: Azure Backup con snapshot dello Storage Account. Testare il restore di un singolo VHD ogni trimestre.

**Q13: Come gestire i servizi Windows durante il patching?**
Prima del patching: documentare lo stato dei servizi con `Get-Service | Export-Csv`. Dopo il reboot: confrontare lo stato con il backup. Script di validazione post-patching: verificare che tutti i servizi Automatic siano Running. Se un servizio non si riavvia: controllare Event Log, dipendenze, e account di servizio (la password potrebbe essere scaduta durante il reboot).

**Q14: Posso usare gMSA con Task Scheduler?**
Sì, da Windows Server 2012+. Creare il task con: `schtasks /create /tn "MyTask" /tr "powershell.exe -File script.ps1" /sc daily /st 02:00 /ru CORP\gMSA-Task$ /rp ""`. Il task gira con le credenziali del gMSA senza password salvata. Requisito: il computer deve essere nel gruppo `PrincipalsAllowedToRetrieveManagedPassword` del gMSA.

**Q15: Come gestire il profilo degli utenti guest / contractor?**
Opzioni: (1) Profilo mandatory: tutti i guest usano lo stesso profilo readonly, nessuna personalizzazione salvata. (2) FSLogix con VHD piccoli (5 GB) e cleanup automatico dopo 30 giorni di inattività. (3) Azure AD guest + Conditional Access: accesso solo a specifiche app cloud, nessun profilo locale. La scelta dipende dal livello di accesso: se accedono a workstation fisiche, mandatory profile; se solo cloud, Conditional Access.

---

## 12. User Environment Virtualization (UE-V) — Approfondimento

### 12.1 Architettura UE-V

UE-V (User Environment Virtualization) cattura e applica le impostazioni utente tra sessioni e dispositivi Windows senza richiedere profili roaming. A differenza dei roaming profiles che sincronizzano l'intero profilo, UE-V sincronizza solo le **impostazioni specifiche delle applicazioni**.

**Componenti architetturali:**

```
┌─────────────────────┐     ┌──────────────────────┐
│   UE-V Agent        │     │  Settings Storage     │
│   (client)          │────▶│  Location (SMB share) │
│                     │     │  \\server\UEV-Store   │
│  - Template Engine  │     └──────────────────────┘
│  - Sync Provider    │              │
│  - Settings Cache   │              ▼
│    (local backup)   │     ┌──────────────────────┐
└─────────────────────┘     │  Settings Templates   │
                            │  Catalog (GPO/SCCM)   │
                            └──────────────────────┘
```

**Flusso operativo:**
1. L'utente apre un'applicazione (es. Word)
2. L'agent UE-V rileva l'evento tramite il template registrato
3. Applica le impostazioni dalla Settings Storage Location
4. L'utente modifica impostazioni (font default, toolbar, macro)
5. Alla chiusura dell'applicazione, l'agent cattura le modifiche
6. Le impostazioni vengono scritte nella Settings Storage Location

### 12.2 Abilitazione e Configurazione UE-V

UE-V è integrato in Windows 10/11 Enterprise ed Education. Non richiede installazione separata.

```powershell
# Abilitare UE-V sul client
Enable-UEV

# Verificare stato
Get-UevStatus
# Output: UE-V is enabled

# Configurare la Settings Storage Location
Set-UevConfiguration -SettingsStoragePath "\\FileServer01\UEV-Store\%USERNAME%"

# Verificare la configurazione
Get-UevConfiguration | Select-Object SettingsStoragePath, SyncMethod, SyncEnabled

# Configurare il metodo di sincronizzazione
# SyncMethod: SyncProvider (default) o None
Set-UevConfiguration -SyncMethod SyncProvider

# Configurare intervallo di sync (minuti)
Set-UevConfiguration -SyncTimeoutInMilliseconds 2000
Set-UevConfiguration -MaxPackageSizeInBytes 524288000  # 500 MB max
```

**Configurazione via GPO (preferita in enterprise):**
```
Computer Configuration → Administrative Templates → Windows Components → 
Microsoft User Experience Virtualization

Impostazioni chiave:
- Settings storage path: \\server\UEV-Store\%USERNAME%
- Sync method: SyncProvider
- Enable UE-V: Enabled
- Use User Experience Virtualization (UE-V): Enabled
- First Use Notification: Disabled (nasconde il popup agli utenti)
- Settings template catalog path: \\server\UEV-Templates
- Tray Icon: Disabled (nessuna icona nell'area notifiche)
```

### 12.3 Template UE-V — Creazione e Gestione

I template definiscono QUALI impostazioni vengono catturate per ciascuna applicazione.

**Template built-in (Windows + Office):**
```powershell
# Elencare i template registrati
Get-UevTemplate

# Template predefiniti includono:
# - MicrosoftOffice2019Win32 / MicrosoftOffice2019Win64
# - MicrosoftWord2019
# - MicrosoftExcel2019
# - MicrosoftOutlook2019
# - MicrosoftPowerPoint2019
# - DesktopSettings (sfondo, colori, taskbar)
# - WindowsDesktopSettings

# Registrare tutti i template Office
Get-UevTemplate | Where-Object { $_.TemplateName -like "*Office*" } | Register-UevTemplate
```

**Creare un template personalizzato con UE-V Generator:**
```powershell
# Aprire il Generator (incluso in Windows ADK)
& "${env:ProgramFiles(x86)}\Windows Kits\10\Assessment and Deployment Kit\User State Migration Tool\amd64\UevTemplateGenerator.exe"

# Flusso di creazione:
# 1. "Discover" — l'app viene avviata e il generator monitora
#    quali file e chiavi di registro vengono modificati
# 2. Selezionare i percorsi rilevanti (escludere cache/temp)
# 3. Salvare il template XML
# 4. Testare su un client di sviluppo
# 5. Registrare con Register-UevTemplate

# Registrare un template personalizzato
Register-UevTemplate -Path "\\server\UEV-Templates\CustomApp.xml"

# Rimuovere un template
Unregister-UevTemplate -TemplateId "CustomApp"
```

**Esempio di template XML per applicazione LOB:**
```xml
<?xml version="1.0" encoding="utf-8"?>
<SettingsLocationTemplate xmlns="http://schemas.microsoft.com/UEV/v2.1">
  <Name>InternalCRM v3</Name>
  <ID>InternalCRM</ID>
  <Version>1</Version>
  <Author>IT Team</Author>
  <Processes>
    <Process>
      <Filename>InternalCRM.exe</Filename>
    </Process>
  </Processes>
  <Settings>
    <Registry>
      <Path>HKCU\Software\InternalCRM\Preferences</Path>
      <Recursive/>
    </Registry>
    <File>
      <Root>APPDATA</Root>
      <Path>InternalCRM\config</Path>
      <FileMask>*.xml</FileMask>
    </File>
  </Settings>
</SettingsLocationTemplate>
```

### 12.4 UE-V vs FSLogix vs Roaming — Confronto Prestazionale

| Aspetto | UE-V | FSLogix | Roaming Profile |
|---------|------|---------|-----------------|
| Cosa sincronizza | Solo impostazioni app | Intero profilo (VHD) | Intero profilo (copia) |
| Impatto logon | Minimo (pochi KB) | Basso (mount VHD, ~2s) | Alto (copia MB/GB) |
| Impatto logoff | Minimo | Basso (unmount) | Alto (copia indietro) |
| Storage per utente | 1-50 MB | 10-30 GB (VHD) | 500 MB - 5 GB |
| Complessità setup | Media (template) | Bassa (agent + share) | Bassa (GPO) |
| Offline support | Sì (cache locale) | No (serve la share) | Parziale |
| App compatibility | Richiede template | Trasparente | Trasparente |
| Uso ideale | Multi-device, app specifiche | VDI, desktop persistenti | Legacy, piccoli ambienti |

**Combinazione consigliata enterprise:**
- **VDI/AVD**: FSLogix per profilo completo + Office Container
- **Desktop fisici multi-device**: UE-V per impostazioni + Folder Redirection per documenti
- **Kiosk/shared workstation**: Mandatory profile + nessuna sincronizzazione

---

## 13. Profili Mandatory — Approfondimento

### 13.1 Creazione del Profilo Mandatory

Un profilo mandatory è un profilo pre-configurato che viene caricato ad ogni login e **scartato al logoff** — le modifiche dell'utente non persistono.

**Procedura completa:**

```powershell
# === FASE 1: Creare un account template ===
New-ADUser -Name "TemplateUser" -SamAccountName "template.mandatory" `
    -UserPrincipalName "template.mandatory@corp.local" `
    -Path "OU=Templates,DC=corp,DC=local" `
    -AccountPassword (ConvertTo-SecureString "P@ssw0rd!Temp" -AsPlainText -Force) `
    -Enabled $true

# === FASE 2: Login con l'account template ===
# Accedere a una workstation con l'account template
# Personalizzare: sfondo, layout Start, app pinnate, preferenze browser
# Rimuovere app inutili dal menu Start
# Configurare le impostazioni desiderate
# Logoff

# === FASE 3: Copiare il profilo ===
# Usare il metodo CopyProfile via Sysprep (più affidabile)
# oppure copiare manualmente la cartella profilo

# Percorso profilo template (dopo il logoff)
$sourceProfile = "C:\Users\template.mandatory"

# Percorso share per profilo mandatory
$mandatoryPath = "\\FileServer01\Profiles$\mandatory.V6"

# Copiare con robocopy preservando ACL e attributi
robocopy $sourceProfile $mandatoryPath /E /COPYALL /XD "AppData\Local\Temp" /XF "*.tmp" /XJ

# === FASE 4: Rinominare NTUSER.DAT in NTUSER.MAN ===
# Questo è il passo CRITICO che rende il profilo mandatory
Rename-Item "$mandatoryPath\NTUSER.DAT" "NTUSER.MAN"

# === FASE 5: Impostare i permessi ===
# Il profilo deve essere leggibile da tutti gli utenti che lo usano
$acl = Get-Acl $mandatoryPath
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "CORP\Domain Users", "ReadAndExecute", "ContainerInherit,ObjectInherit", "None", "Allow"
)
$acl.AddAccessRule($rule)
Set-Acl $mandatoryPath $acl

# === FASE 6: Assegnare il profilo via GPO o AD ===
# Per singoli utenti: proprietà AD User → Profile tab → Profile path
Set-ADUser -Identity "kiosk.user1" -ProfilePath "\\FileServer01\Profiles$\mandatory"

# Per gruppo tramite GPO:
# User Configuration → Administrative Templates → System → User Profiles
# → Set roaming profile path for all users logging onto this computer
# Valore: \\FileServer01\Profiles$\mandatory
```

### 13.2 Mandatory Profile per Windows 10/11 — Versioning

Windows usa suffissi di versione per i profili:

| OS | Suffisso | Esempio |
|----|----------|---------|
| Windows 10 (1607-) | .V5 | mandatory.V5 |
| Windows 10 (1607+) | .V6 | mandatory.V6 |
| Windows 11 | .V6 | mandatory.V6 |

```powershell
# Script per creare le cartelle per tutti i suffissi
$basePath = "\\FileServer01\Profiles$\mandatory"
$suffixes = @(".V5", ".V6")

foreach ($suffix in $suffixes) {
    $fullPath = "$basePath$suffix"
    if (-not (Test-Path $fullPath)) {
        New-Item -Path $fullPath -ItemType Directory
        # Copiare il profilo template specifico per ciascun OS
        robocopy "$basePath-source-$suffix" $fullPath /E /COPYALL /XJ
        Rename-Item "$fullPath\NTUSER.DAT" "NTUSER.MAN"
    }
}
```

### 13.3 Super Mandatory Profile

Il **super mandatory profile** impedisce il login se il profilo non è disponibile (a differenza del mandatory profile standard che fallback su profilo locale).

```powershell
# Creare un super mandatory profile:
# Invece di NTUSER.MAN → rinominare in NTUSER.MAN
# E aggiungere .MAN anche alla CARTELLA
# Esempio: \\server\Profiles$\mandatory.man.V6\NTUSER.MAN
$superMandatoryPath = "\\FileServer01\Profiles$\mandatory.man.V6"
New-Item -Path $superMandatoryPath -ItemType Directory
# ... copiare contenuti e rinominare NTUSER.DAT → NTUSER.MAN

# Con super mandatory:
# - Share offline → login RIFIUTATO (niente profilo temporaneo)
# - Utile per kiosk e ambienti ad alta sicurezza
# - ATTENZIONE: un outage dello storage = nessun utente può accedere
```

### 13.4 Troubleshooting Mandatory Profile

| Sintomo | Causa | Soluzione |
|---------|-------|-----------|
| Login lentissimo | NTUSER.DAT non rinominato in .MAN | Verificare che esista NTUSER.MAN |
| Modifiche che persistono | Il profilo non è veramente mandatory | Controllare il suffisso di versione .V6 |
| "We can't sign in" | Super mandatory + share offline | Verificare connettività alla share |
| Errore "Profile not loaded" | Permessi errati sulla cartella | ACL: Domain Users = ReadAndExecute |
| Profilo locali creati | Path nel profilo AD sbagliato | Verificare AD User → Profile tab |
| Layout Start non funziona | LayoutModification.xml mancante | Includere nel profilo template |

---

## Diagnosi e Riparazione Profili Corrotti

### Sintomi di Corruzione del Profilo

Un profilo corrotto si manifesta tipicamente in questi modi:

| Sintomo | Event ID | Descrizione |
|---------|----------|-------------|
| Profilo temporaneo caricato | 1511 | "Windows cannot find the local profile and is logging you on with a temporary profile" |
| Servizio profili fallito | 1515 | "Windows has backed up this user profile. Windows will automatically try to use the backed up profile the next time this user logs on" |
| Login bloccato | 1521 | "Windows cannot load the user's profile but has logged you on with the default profile" |
| Hive corrotto | 1542 | "The profile hive was not loaded successfully. This is caused by a corrupted or missing profile hive" |
| Profilo non scaricato | 1530 | "Windows detected your registry file is still in use by other applications. The file will be unloaded now" |

### Procedura Diagnostica Step-by-Step

```powershell
# ============================================================
# FASE 1: IDENTIFICAZIONE DEL PROBLEMA
# ============================================================

# Verificare se l'utente sta usando un profilo temporaneo
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$profilePath = (Get-CimInstance Win32_UserProfile |
    Where-Object { $_.SID -eq ([System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value) }).LocalPath
Write-Host "Profilo corrente: $profilePath"
# Se il path contiene "TEMP" → l'utente è su un profilo temporaneo

# Controllare il registry per voci .bak (profilo danneggiato)
$profileListPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList"
Get-ChildItem $profileListPath | ForEach-Object {
    $sid = $_.PSChildName
    $profileImagePath = (Get-ItemProperty $_.PSPath).ProfileImagePath
    $isBak = $sid -match '\.bak$'
    [PSCustomObject]@{
        SID              = $sid
        ProfilePath      = $profileImagePath
        IsBackupEntry    = $isBak
        State            = (Get-ItemProperty $_.PSPath -ErrorAction SilentlyContinue).State
    }
} | Where-Object { $_.IsBackupEntry -or $_.ProfilePath -like "*TEMP*" } |
    Format-Table -AutoSize

# Cercare eventi di errore nel log
Get-WinEvent -FilterHashtable @{
    LogName = 'Application'
    ProviderName = 'Microsoft-Windows-User Profiles Service'
    Level = 2  # Error
} -MaxEvents 20 | Select-Object TimeCreated, Id, Message | Format-Table -Wrap

# ============================================================
# FASE 2: RIPARAZIONE REGISTRY — PROFILO .BAK
# ============================================================

# Il problema più comune: esiste una chiave SID con suffisso .bak
# Questo accade quando il profilo crasha e Windows crea un backup

# Esempio: l'utente ha SID S-1-5-21-1234567890-1234567890-1234567890-1001
# Nel registry potrebbe esserci:
# S-1-5-21-...-1001       → punta a C:\Users\TEMP.corp (profilo temporaneo)
# S-1-5-21-...-1001.bak   → punta a C:\Users\mrossi (profilo VERO)

# Fix: rinominare le chiavi per ripristinare il profilo originale
function Repair-UserProfileRegistry {
    param(
        [Parameter(Mandatory)]
        [string]$UserSID
    )

    $basePath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList"
    $normalKey = Join-Path $basePath $UserSID
    $bakKey = Join-Path $basePath "$UserSID.bak"

    # Verificare che la chiave .bak esista
    if (-not (Test-Path $bakKey)) {
        Write-Warning "Nessuna chiave .bak trovata per SID: $UserSID"
        return
    }

    Write-Host "Chiave .bak trovata. Profilo path: $((Get-ItemProperty $bakKey).ProfileImagePath)"

    # Backup delle chiavi correnti prima di modificare
    reg export "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\$UserSID" `
        "C:\Backup\ProfileList-$UserSID-normal.reg" /y 2>$null
    reg export "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\$UserSID.bak" `
        "C:\Backup\ProfileList-$UserSID-bak.reg" /y

    # Rinominare: normale → .bad (temporaneo)
    Rename-Item -Path $normalKey -NewName "$UserSID.bad" -ErrorAction Stop

    # Rinominare: .bak → normale (ripristino)
    Rename-Item -Path $bakKey -NewName $UserSID -ErrorAction Stop

    # Impostare lo State a 0 (profilo non caricato, pronto per il login)
    Set-ItemProperty -Path $normalKey -Name "State" -Value 0 -Type DWord

    # Impostare RefCount a 0
    Set-ItemProperty -Path $normalKey -Name "RefCount" -Value 0 -Type DWord

    Write-Host "Profilo ripristinato. L'utente può effettuare il login." -ForegroundColor Green
    Write-Host "Eliminare la chiave .bad dopo aver verificato il funzionamento." -ForegroundColor Yellow
}

# Uso:
# Repair-UserProfileRegistry -UserSID "S-1-5-21-1234567890-1234567890-1234567890-1001"
```

### Riparazione NTUSER.DAT da Shadow Copy

```powershell
# Se il file NTUSER.DAT è corrotto, si può recuperare da una shadow copy
# o dal backup di sistema

# 1. Verificare la presenza di shadow copies
vssadmin list shadows

# 2. Trovare le shadow copies che contengono il profilo
$shadowCopies = Get-CimInstance Win32_ShadowCopy | Sort-Object InstallDate -Descending
foreach ($sc in $shadowCopies) {
    $shadowPath = $sc.DeviceObject + "\Users\mrossi\NTUSER.DAT"
    Write-Host "Shadow: $($sc.InstallDate) → $shadowPath"
}

# 3. Montare la shadow copy e copiare il file
# (accedere via \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopyN\)
# OPPURE: usare la tab "Versioni precedenti" in Explorer sulla cartella profilo

# 4. Riparare con System File Checker e DISM
# Eseguire da un account amministratore diverso dall'utente con profilo corrotto
sfc /scannow
# Se SFC trova errori ma non riesce a ripararli:
DISM /Online /Cleanup-Image /RestoreHealth
# Poi rieseguire:
sfc /scannow

# 5. Tentare il caricamento manuale dell'hive per verificare integrità
reg load HKU\TestHive "C:\Users\mrossi\NTUSER.DAT"
# Se il comando fallisce → l'hive è corrotto irrimediabilmente
# Se funziona → l'hive è integro, il problema è altrove
reg unload HKU\TestHive
```

### Pulizia Enterprise — Delprof2 e Profili Orfani

```powershell
# Delprof2 è lo strumento standard per la pulizia profili su RDS e VDI
# Scaricabile da: https://helgeklein.com/free-tools/delprof2-user-profile-deletion-tool/

# Eliminare profili inattivi da più di 30 giorni (preview — nessuna eliminazione)
# Delprof2.exe /d:30 /l
# /d:30 = profili inutilizzati da 30+ giorni
# /l    = list only (dry-run, nessuna eliminazione)

# Eliminare effettivamente
# Delprof2.exe /d:30 /u
# /u = unattended (nessuna conferma)

# Escludere account specifici
# Delprof2.exe /d:30 /u /ed:admin* /ed:svc-*

# Su computer remoto
# Delprof2.exe /c:\\SRV-RDS01 /d:30 /u

# ============================================================
# ALTERNATIVA POWERSHELL: Rilevare profili orfani
# ============================================================
# Un profilo orfano ha una voce nel registry ma la cartella non esiste,
# o viceversa la cartella esiste ma non ha una voce nel registry

function Find-OrphanedProfiles {
    $profileList = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList"
    $results = @()

    # Profili nel registry
    $regProfiles = Get-ChildItem $profileList | ForEach-Object {
        $path = (Get-ItemProperty $_.PSPath).ProfileImagePath
        [PSCustomObject]@{
            SID  = $_.PSChildName
            Path = $path
            RegistryExists = $true
            FolderExists   = Test-Path $path
        }
    }

    # Cartelle in C:\Users che non hanno voce nel registry
    $registeredPaths = $regProfiles.Path | ForEach-Object { Split-Path $_ -Leaf }
    $folderProfiles = Get-ChildItem "C:\Users" -Directory |
        Where-Object { $_.Name -notin @("Public","Default","Default User","All Users") } |
        Where-Object { $_.Name -notin $registeredPaths } |
        ForEach-Object {
            [PSCustomObject]@{
                SID  = "N/A (no registry entry)"
                Path = $_.FullName
                RegistryExists = $false
                FolderExists   = $true
            }
        }

    # Combinare e mostrare problemi
    $orphaned = @($regProfiles | Where-Object { -not $_.FolderExists }) +
                @($folderProfiles)

    if ($orphaned) {
        Write-Host "`n=== PROFILI ORFANI RILEVATI ===" -ForegroundColor Red
        $orphaned | Format-Table -AutoSize
        Write-Host "Azione: usare Remove-CimInstance per rimuovere le voci registry orfane"
        Write-Host "        o eliminare le cartelle senza voce registry (dopo backup)"
    }
    else {
        Write-Host "Nessun profilo orfano trovato." -ForegroundColor Green
    }

    return $orphaned
}

# Uso:
# $orphans = Find-OrphanedProfiles
```

### Prevenzione della Corruzione Profili

| Misura Preventiva | Implementazione | Priorità |
|-------------------|-----------------|----------|
| Shutdown pulito | GPO: forzare logoff prima dello shutdown | Alta |
| Shadow copies | Abilitare VSS sulla partizione C: con snapshot giornalieri | Alta |
| Backup NTUSER.DAT | Script pianificato per copiare NTUSER.DAT delle sessioni attive | Media |
| Monitoraggio Event Log | Alert su Event ID 1511, 1515, 1521 via WEF o SCOM | Alta |
| Antivirus esclusioni | Escludere NTUSER.DAT e i file .LOG dalla scansione in tempo reale | Alta |
| Profili temporanei GPO | "Do not log users on with temporary profiles": valutare in base all'ambiente | Media |
| Pulizia periodica | Delprof2 o script settimanale per profili > 90 giorni inattivi | Media |
| Monitoraggio disco | Alert quando lo spazio su C: scende sotto il 15% (causa comune di corruzione) | Alta |

---

## 14. Architettura dei Servizi Windows — Approfondimento

### 14.1 Service Control Manager (SCM)

Il SCM (`services.exe`) è il componente kernel-mode che gestisce il ciclo di vita di tutti i servizi Windows.

**Architettura SCM:**
```
┌─────────────────────────────────────────────┐
│  Service Control Manager (services.exe)     │
│                                             │
│  ┌──────────────┐  ┌──────────────────────┐ │
│  │ Service DB   │  │ Control Dispatcher   │ │
│  │ (Registry)   │  │ (RPC endpoint)       │ │
│  │ HKLM\SYSTEM\ │  └──────────────────────┘ │
│  │ CurrentCSS\  │           │               │
│  │ Services     │     ┌─────┴─────┐         │
│  └──────────────┘     │           │         │
│                    ┌──┴───┐  ┌────┴────┐    │
│                    │Win32 │  │Driver   │    │
│                    │Service│  │Service  │    │
│                    │(user) │  │(kernel) │    │
│                    └───────┘  └─────────┘    │
└─────────────────────────────────────────────┘
```

**Tipi di servizio:**
```powershell
# Enumerare i tipi di servizio
Get-Service | Group-Object ServiceType | Select-Object Name, Count

# Tipi principali:
# Win32OwnProcess    — processo dedicato (svchost.exe -k isolato)
# Win32ShareProcess  — condivide un processo svchost.exe
# KernelDriver       — driver kernel-mode
# FileSystemDriver   — driver del file system
# InteractiveProcess — può interagire con il desktop (deprecated)
```

### 14.2 Dipendenze dei Servizi — Mappatura Completa

```powershell
# === Visualizzare le dipendenze di un servizio ===
Get-Service -Name "Netlogon" -DependentServices   # chi dipende DA Netlogon
Get-Service -Name "Netlogon" -RequiredServices     # di chi Netlogon HA BISOGNO

# === Albero dipendenze completo (ricorsivo) ===
function Get-ServiceDependencyTree {
    param (
        [string]$ServiceName,
        [int]$Depth = 0
    )
    
    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if (-not $service) { return }
    
    $indent = "  " * $Depth
    $status = $service.Status
    Write-Output "$indent[$status] $($service.Name) — $($service.DisplayName)"
    
    $deps = Get-Service -Name $ServiceName -RequiredServices -ErrorAction SilentlyContinue
    foreach ($dep in $deps) {
        Get-ServiceDependencyTree -ServiceName $dep.Name -Depth ($Depth + 1)
    }
}

# Esempio: albero dipendenze di Active Directory Domain Services
Get-ServiceDependencyTree -ServiceName "NTDS"
# Output:
# [Running] NTDS — Active Directory Domain Services
#   [Running] Netlogon — Net Logon
#     [Running] LanmanWorkstation — Workstation
#       [Running] NSI — Network Store Interface Service
#       [Running] Bowser — Browser Support Driver
#   [Running] RpcSs — Remote Procedure Call (RPC)
#   [Running] SamSs — Security Accounts Manager
#     [Running] RpcSs — Remote Procedure Call (RPC)
#   [Running] NTFRS — File Replication Service  (o DFSR)
#   [Running] Kdc — Kerberos Key Distribution Center
```

### 14.3 Ordine di Avvio dei Servizi e Startup Type

```powershell
# Tipi di avvio
Get-Service | Group-Object StartType | Select-Object Name, Count
# Automatic       — avvio con il sistema
# AutomaticDelayedStart — avvio dopo 2 minuti dal boot
# Manual           — avvio on-demand
# Disabled         — non avviabile

# Servizi Automatic che non sono Running (problema potenziale)
Get-Service | Where-Object {
    $_.StartType -eq "Automatic" -and $_.Status -ne "Running"
} | Select-Object Name, DisplayName, Status | Format-Table -AutoSize

# === Impostare Delayed Start (riduce tempo di boot) ===
Set-Service -Name "SomeService" -StartupType AutomaticDelayedStart

# === Servizi critici che NON devono essere Disabled ===
$criticalServices = @(
    "EventLog",      # Windows Event Log
    "RpcSs",         # Remote Procedure Call
    "Winmgmt",       # WMI
    "CryptSvc",      # Cryptographic Services
    "BITS",          # Background Intelligent Transfer
    "wuauserv",      # Windows Update
    "W32Time",       # Windows Time
    "Netlogon",      # Net Logon (DC e domain members)
    "DNS",           # DNS Server (solo sui DC)
    "NTDS",          # AD DS (solo sui DC)
    "Kdc",           # Kerberos KDC (solo sui DC)
    "DFS",           # DFS Namespace
    "DFSR"           # DFS Replication
)

# Verifica stato servizi critici
foreach ($svc in $criticalServices) {
    $s = Get-Service -Name $svc -ErrorAction SilentlyContinue
    if ($s) {
        if ($s.Status -ne "Running") {
            Write-Warning "CRITICO: $($s.Name) ($($s.DisplayName)) è $($s.Status)"
        }
    }
}
```

### 14.4 Recovery Actions dei Servizi

```powershell
# Configurare azioni di recovery per un servizio
# sc.exe è necessario — Set-Service non supporta tutte le opzioni
sc.exe failure "MyService" reset= 86400 actions= restart/60000/restart/120000/run/180000 command= "powershell.exe -File C:\Scripts\ServiceAlert.ps1"

# Significato:
# reset= 86400    → resetta il contatore fallimenti dopo 24h
# Primo fallimento: restart dopo 60 secondi
# Secondo fallimento: restart dopo 120 secondi
# Fallimenti successivi: esegui uno script dopo 180 secondi

# Verificare la configurazione di recovery
sc.exe qfailure "MyService"

# Configurazione consigliata per servizi critici:
# Primo:    Restart the Service (30s)
# Secondo:  Restart the Service (60s)
# Terzo:    Run a Program (script di notifica + tentativo restart)
# Reset:    1 giorno

# Abilitare "Enable actions for stops with errors"
# Registry: HKLM\SYSTEM\CurrentControlSet\Services\<name>\FailureActionsOnNonCrashFailures = 1
```

---

## Service Hardening — SID, Restrizioni e Isolamento

### 14.5 Service SID — Identità per Servizio

Ogni servizio Windows può avere un **Service SID** (Security Identifier) dedicato, utilizzabile nelle ACL per proteggere risorse specifiche del servizio. Il Service SID elimina la necessità di creare account utente separati per servizi che devono accedere a risorse limitate.

```powershell
# ============================================================
# TIPI DI SERVICE SID
# ============================================================

# Visualizzare il tipo di SID di un servizio
sc.exe qsidtype "wuauserv"
# Output: SERVICE_SID_TYPE: UNRESTRICTED

# Tipi di SID disponibili:
# NONE         → nessun SID di servizio (legacy)
# UNRESTRICTED → il servizio ha un SID, usabile nelle ACL
# RESTRICTED   → SID write-restricted: il servizio può LEGGERE
#                con il token del processo, ma può SCRIVERE solo
#                su risorse dove il Service SID ha permesso esplicito

# Impostare un Service SID restricted (più sicuro)
sc.exe sidtype "CustomService" restricted

# Impostare un Service SID unrestricted
sc.exe sidtype "CustomService" unrestricted

# Rimuovere il Service SID
sc.exe sidtype "CustomService" none

# ============================================================
# ESEMPIO: PROTEGGERE UNA CARTELLA CON SERVICE SID
# ============================================================

# Il Service SID ha il formato: NT SERVICE\<NomeServizio>
# Esempio: NT SERVICE\wuauserv per Windows Update

# Concedere a un servizio l'accesso esclusivo a una cartella
$path = "C:\ServiceData\CustomService"
New-Item $path -ItemType Directory -Force

$acl = Get-Acl $path
$acl.SetAccessRuleProtection($true, $false)  # Disabilita ereditarietà

# SYSTEM: Full Control (necessario per il sistema)
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "SYSTEM", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
$acl.AddAccessRule($rule)

# Administrators: Full Control (necessario per gestione)
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "BUILTIN\Administrators", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow")
$acl.AddAccessRule($rule)

# Service SID: Modify (solo il servizio può scrivere qui)
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "NT SERVICE\CustomService", "Modify", "ContainerInherit,ObjectInherit", "None", "Allow")
$acl.AddAccessRule($rule)

Set-Acl $path $acl
# Risultato: solo CustomService, SYSTEM e Administrators accedono alla cartella
```

### 14.5.1 Session 0 Isolation

```powershell
# Da Windows Vista/Server 2008, i servizi girano in Session 0 (isolata)
# Le sessioni utente partono da Session 1 in poi
# I servizi NON possono interagire direttamente con il desktop utente

# Verificare in quale sessione gira un servizio
Get-CimInstance Win32_Service -Filter "Name='CustomService'" |
    Select-Object Name, ProcessId
# Poi controllare la sessione del processo:
Get-Process -Id <PID> | Select-Object Id, SessionId
# Session 0 = isolato (corretto per un servizio)

# Servizi che richiedono interazione con l'utente:
# - NON usare il flag "Interactive" (deprecato e bloccato)
# - Usare un'applicazione tray separata che comunica via pipe o socket
# - Esempio: il servizio FSLogix (frxsvc) usa frxtray.exe per il tray icon
```

### 14.5.2 Privilegi Minimi per Servizi (RequiredPrivileges)

```powershell
# Ogni servizio può dichiarare i privilegi MINIMI necessari
# Se un privilegio non è nella lista, il servizio non lo ottiene
# Questo limita i danni in caso di compromissione del servizio

# Visualizzare i privilegi richiesti da un servizio
sc.exe qprivs "wuauserv"
# Output: REQUIRED_PRIVILEGES:
#   SeAuditPrivilege
#   SeCreateGlobalPrivilege
#   SeCreatePageFilePrivilege
#   ...

# Impostare privilegi minimi per un servizio custom
sc.exe privs "CustomService" SeChangeNotifyPrivilege/SeImpersonatePrivilege
# Il servizio riceverà SOLO questi privilegi, nessun altro

# Privilegi comuni per servizi:
# SeChangeNotifyPrivilege   → traversare directory (quasi sempre necessario)
# SeImpersonatePrivilege    → impersonare client (necessario per servizi di rete)
# SeAuditPrivilege          → generare audit events
# SeAssignPrimaryTokenPrivilege → assegnare token a processi (servizi che lanciano processi)
# SeBackupPrivilege         → leggere file ignorando le ACL (servizi di backup)
# SeServiceLogonRight       → logon come servizio (necessario per tutti i service account)

# Verificare i privilegi effettivi di un processo di servizio in esecuzione
whoami /priv  # (eseguito nel contesto del servizio)
# Per un servizio remoto: usare Process Explorer → Properties → Security tab

# ============================================================
# RESTRIZIONE ACCESSO RETE PER SERVIZIO
# ============================================================

# Windows Firewall può usare il Service SID per limitare l'accesso di rete
# Solo il servizio specifico può comunicare sulla porta indicata

# Creare regola firewall specifica per un servizio
New-NetFirewallRule -DisplayName "CustomService - Allow HTTPS" `
    -Direction Outbound `
    -Service "CustomService" `
    -Protocol TCP `
    -RemotePort 443 `
    -Action Allow

# Bloccare tutto il traffico in uscita per un servizio specifico
New-NetFirewallRule -DisplayName "CustomService - Block All Outbound" `
    -Direction Outbound `
    -Service "CustomService" `
    -Action Block

# Questo impedisce che un servizio compromesso comunichi con un C2 server
# Il servizio può accedere SOLO alle porte esplicitamente autorizzate
```

### 14.5.3 Delayed Auto-Start — Sicurezza e Performance

```powershell
# Il Delayed Auto-Start avvia i servizi 1-2 minuti dopo il boot
# Benefici:
# 1. PERFORMANCE: riduce il tempo di boot distribuendo il carico
# 2. SICUREZZA: permette ai servizi di sicurezza (antivirus, EDR) di avviarsi
#    PRIMA dei servizi applicativi, riducendo la finestra di esposizione
# 3. STABILITÀ: le dipendenze di rete e storage hanno tempo di stabilizzarsi

# Impostare un servizio per Delayed Auto-Start
Set-Service -Name "CustomService" -StartupType AutomaticDelayedStart

# OPPURE via registry
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\CustomService" `
    -Name "DelayedAutostart" -Value 1 -Type DWord
# NOTA: StartType deve essere Automatic (2) per DelayedAutostart

# Quali servizi mettere in Delayed Auto-Start:
# SÌ: servizi applicativi, agent di monitoring, servizi di backup
# NO: servizi di sicurezza (antivirus, EDR, firewall)
# NO: servizi core di rete (DNS, DHCP su server)
# NO: servizi di autenticazione (Netlogon, KDC su DC)

# ATTENZIONE: non impostare MAI servizi di sicurezza in Delayed Auto-Start
# Un ritardo nell'avvio dell'antivirus crea una finestra di 2 minuti
# durante la quale il sistema è privo di protezione

# Audit: trovare servizi Automatic che beneficerebbero del Delayed Start
Get-Service | Where-Object {
    $_.StartType -eq "Automatic" -and
    $_.Status -eq "Running" -and
    $_.Name -notin @("EventLog","RpcSs","Winmgmt","CryptSvc","BFE","MpsSvc",
                      "WinDefend","Netlogon","DNS","NTDS","Kdc","W32Time")
} | Select-Object Name, DisplayName, StartType | Format-Table -AutoSize
```

---

## Recovery Avanzato e Monitoraggio Automatico

### 14.6 FailureActionsOnNonCrashFailures

```powershell
# Per default, le recovery actions si attivano SOLO quando il servizio
# crasha (termina inaspettatamente con codice di errore)
# Se il servizio si ferma "correttamente" con errore (es. errore di configurazione),
# le recovery actions NON si attivano

# Abilitare le recovery actions anche per stop con errore
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\CustomService" `
    -Name "FailureActionsOnNonCrashFailures" -Value 1 -Type DWord

# Questo è CRITICO per servizi che possono fallire senza crash:
# - Servizi che si fermano per errori di configurazione
# - Servizi che non riescono a connettersi a un database
# - Servizi che esauriscono le risorse e si fermano ordinatamente
# Senza questa chiave, il servizio si ferma e NESSUNO viene notificato

# Configurare per tutti i servizi custom
$customServices = Get-Service | Where-Object {
    $_.Name -like "Custom*" -or $_.Name -like "Corp*"
}
foreach ($svc in $customServices) {
    $regPath = "HKLM:\SYSTEM\CurrentControlSet\Services\$($svc.Name)"
    Set-ItemProperty -Path $regPath -Name "FailureActionsOnNonCrashFailures" `
        -Value 1 -Type DWord
    Write-Host "FailureActionsOnNonCrashFailures abilitato per: $($svc.Name)"
}
```

### 14.6.1 Monitoraggio Crash Servizi via Event Log

```powershell
# Event ID rilevanti per il monitoraggio servizi:
# 7036 — Servizio avviato o arrestato (informativo)
# 7031 — Servizio terminato inaspettatamente (CRASH)
# 7034 — Servizio terminato inaspettatamente per la N-esima volta
# 7040 — Tipo di avvio del servizio cambiato
# 7045 — Nuovo servizio installato (potenziale IOC di sicurezza)

# Cercare crash di servizi nelle ultime 24 ore
$since = (Get-Date).AddHours(-24)
Get-WinEvent -FilterHashtable @{
    LogName = 'System'
    Id = 7031, 7034
    StartTime = $since
} -ErrorAction SilentlyContinue | ForEach-Object {
    [PSCustomObject]@{
        Time    = $_.TimeCreated
        EventID = $_.Id
        Message = $_.Message.Split("`n")[0]  # Solo la prima riga
    }
} | Format-Table -Wrap

# ============================================================
# SCRIPT DI NOTIFICA AUTOMATICA SU CRASH SERVIZIO
# ============================================================

# Questo script viene invocato come recovery action (Run a Program)
# Salva in C:\Scripts\ServiceCrashAlert.ps1

$alertScript = @'
param(
    [string]$ServiceName = "UnknownService"
)

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss UTC" -AsUTC
$hostname  = $env:COMPUTERNAME
$fqdn      = [System.Net.Dns]::GetHostEntry($hostname).HostName

# Raccogliere informazioni diagnostiche
$recentEvents = Get-WinEvent -FilterHashtable @{
    LogName = 'System'
    Id = 7031, 7034
    StartTime = (Get-Date).AddMinutes(-10)
} -MaxEvents 5 -ErrorAction SilentlyContinue

$eventDetails = $recentEvents | ForEach-Object {
    "  [$($_.TimeCreated)] Event $($_.Id): $($_.Message.Split("`n")[0])"
} | Out-String

# Log locale
$logEntry = @"
==================================================
SERVICE CRASH ALERT
Timestamp: $timestamp
Server:    $fqdn
Service:   $ServiceName
Recent Events:
$eventDetails
==================================================
"@

$logEntry | Out-File "C:\Logs\ServiceCrash-$(Get-Date -Format 'yyyyMMdd').log" -Append

# Inviare email di notifica (configurare il relay SMTP)
$mailParams = @{
    From       = "alerts@corp.contoso.com"
    To         = "sysadmin-team@corp.contoso.com"
    Subject    = "[ALERT] Service crash: $ServiceName su $hostname"
    Body       = $logEntry
    SmtpServer = "smtp.corp.contoso.com"
    Priority   = "High"
}

try {
    Send-MailMessage @mailParams -ErrorAction Stop
    "Email inviata con successo" | Out-File "C:\Logs\ServiceCrash-$(Get-Date -Format 'yyyyMMdd').log" -Append
}
catch {
    "ERRORE invio email: $($_.Exception.Message)" |
        Out-File "C:\Logs\ServiceCrash-$(Get-Date -Format 'yyyyMMdd').log" -Append
}
'@

# Salvare lo script
$alertScript | Out-File "C:\Scripts\ServiceCrashAlert.ps1" -Encoding UTF8

# Configurare il servizio per invocare lo script al terzo fallimento
sc.exe failure "CustomService" reset= 86400 `
    actions= restart/30000/restart/60000/run/120000
sc.exe failure "CustomService" `
    command= "powershell.exe -ExecutionPolicy Bypass -File C:\Scripts\ServiceCrashAlert.ps1 -ServiceName CustomService"
```

### 14.6.2 Monitoraggio Centralizzato con Windows Event Forwarding

```powershell
# WEF (Windows Event Forwarding) raccoglie eventi da tutti i server
# verso un collector centralizzato — senza agent aggiuntivi

# Sul COLLECTOR (il server che riceve gli eventi):
wecutil qc /q  # Configura il servizio Windows Event Collector

# Creare una subscription per gli eventi di crash servizi
$subscriptionXml = @"
<Subscription xmlns="http://schemas.microsoft.com/2006/03/windows/events/subscription">
    <SubscriptionId>ServiceCrashes</SubscriptionId>
    <SubscriptionType>SourceInitiated</SubscriptionType>
    <Description>Raccolta crash servizi da tutti i server</Description>
    <Enabled>true</Enabled>
    <Uri>http://schemas.microsoft.com/wbem/wsman/1/windows/EventLog</Uri>
    <Query>
        <![CDATA[
        <QueryList>
            <Query Id="0" Path="System">
                <Select Path="System">
                    *[System[(EventID=7031 or EventID=7034 or EventID=7045)]]
                </Select>
            </Query>
        </QueryList>
        ]]>
    </Query>
    <ReadExistingEvents>false</ReadExistingEvents>
    <TransportName>HTTP</TransportName>
    <ContentFormat>RenderedText</ContentFormat>
    <Locale Language="en-US"/>
    <LogFile>ForwardedEvents</LogFile>
    <AllowedSourceNonDomainComputers/>
    <AllowedSourceDomainComputers>
        O:NSG:NSD:(A;;GA;;;DC)(A;;GA;;;NS)
    </AllowedSourceDomainComputers>
</Subscription>
"@

$subscriptionXml | Out-File "C:\Temp\ServiceCrashes.xml" -Encoding UTF8
wecutil cs "C:\Temp\ServiceCrashes.xml"

# Sui SOURCE (i server monitorati):
# GPO: Computer → Administrative Templates → Windows Components →
#   Event Forwarding → Configure target Subscription Manager
# Valore: Server=http://<collector>:5985/wsman/SubscriptionManager/WEC
```

---

## 15. Analisi Prestazionale delle Soluzioni di Profilo

### 15.1 Benchmark di Logon Time

| Soluzione | Profilo 500MB | Profilo 2GB | Profilo 5GB |
|-----------|--------------|------------|------------|
| Profilo Locale | 3-5s | 3-5s | 3-5s |
| Roaming Profile (LAN 1Gbps) | 8-15s | 30-60s | 2-5 min |
| Roaming Profile (WAN 100Mbps) | 20-40s | 2-5 min | 10+ min |
| FSLogix (SSD storage) | 3-6s | 3-6s | 3-6s |
| FSLogix (HDD storage) | 5-10s | 5-10s | 6-12s |
| Mandatory Profile | 3-5s | N/A (piccolo) | N/A |
| UE-V | 3-5s (+ 1-2s sync) | N/A | N/A |

**Nota:** FSLogix ha tempi quasi costanti perché monta un VHD, non copia i file.

### 15.2 Impatto su Storage e Rete

```powershell
# === Script di analisi dimensione profili ===
$users = Get-ChildItem "C:\Users" -Directory | Where-Object { $_.Name -notin @("Public","Default","Default User") }

$report = foreach ($user in $users) {
    $size = (Get-ChildItem $user.FullName -Recurse -Force -ErrorAction SilentlyContinue |
        Measure-Object -Property Length -Sum).Sum / 1GB
    
    $appDataSize = 0
    $appDataPath = Join-Path $user.FullName "AppData"
    if (Test-Path $appDataPath) {
        $appDataSize = (Get-ChildItem $appDataPath -Recurse -Force -ErrorAction SilentlyContinue |
            Measure-Object -Property Length -Sum).Sum / 1GB
    }
    
    [PSCustomObject]@{
        User = $user.Name
        TotalGB = [math]::Round($size, 2)
        AppDataGB = [math]::Round($appDataSize, 2)
        DocumentsGB = [math]::Round(($size - $appDataSize), 2)
    }
}

$report | Sort-Object TotalGB -Descending | Format-Table -AutoSize

# Output esempio:
# User          TotalGB  AppDataGB  DocumentsGB
# ----          -------  ---------  -----------
# m.rossi       4.52     2.31       2.21
# g.bianchi     3.18     1.89       1.29
# l.verdi       1.24     0.87       0.37
```

### 15.3 Matrice Decisionale — Quale Soluzione Scegliere

```
                    ┌─────────────────────────────────┐
                    │   Quanti dispositivi per utente? │
                    └────────┬──────────┬──────────────┘
                             │          │
                         1 device   2+ devices
                             │          │
                    ┌────────┘          └────────┐
                    │                            │
              Profilo Locale          ┌──────────┴────────────┐
              (nessuna sync           │  Tipo di ambiente?    │
               necessaria)           └────┬────────┬─────────┘
                                          │        │
                                       VDI/RDS   Desktop fisici
                                          │        │
                                     FSLogix     ┌──┴──────────┐
                                                 │  Cosa       │
                                                 │  sincronizzare?  │
                                                 └──┬──────────┘
                                                    │
                                          ┌─────────┴─────────┐
                                     Solo impostazioni    Tutto il profilo
                                          │                    │
                                        UE-V +            FSLogix o
                                   Folder Redirect     Folder Redirect
```

---

## Esercizi

### Esercizio 1: Configurazione FSLogix Profile Container

In un ambiente RDS/VDI di lab, configurare FSLogix:

1. Creare una share di rete `\\fileserver\Profiles$` con permessi NTFS corretti (Creator Owner: Full Control sulle sottocartelle; Users: solo Modify sulla root).
2. Installare l'agent FSLogix sui session host.
3. Configurare le chiavi registry: `VHDLocations`, `Enabled=1`, `SizeInMBs=30000`, `VolumeType=VHDX`.
4. Separare Office Container dal Profile Container configurando `OfficeContainerVHDLocations` su una share dedicata.
5. Testare il logon/logoff di un utente e verificare la creazione del VHDX con `Get-ChildItem \\fileserver\Profiles$`.

**Criteri di validazione**: il file VHDX deve essere creato al primo logon. Al logoff, il VHDX deve essere smontato. Al secondo logon, le impostazioni utente devono essere preservate.

### Esercizio 2: Folder Redirection via GPO

Configurare la Folder Redirection per un'unità organizzativa:

1. Creare la share `\\fileserver\Users$` con permessi ABE (Access-Based Enumeration) abilitati.
2. Creare una GPO e configurare la redirection per: Desktop, Documenti, Immagini, Download.
3. Abilitare "Grant the user exclusive rights to folder" e "Move the contents of the user folder to the new location".
4. Configurare Offline Files per le cartelle redirezionate.
5. Testare il comportamento offline: disconnettere la rete, verificare l'accesso ai file, riconnettere e verificare la sincronizzazione.

**Criteri di validazione**: `dir /al %USERPROFILE%\Documents` deve mostrare un junction point verso la share. I file devono essere accessibili offline.

### Esercizio 3: Configurazione gMSA

Creare e utilizzare un Group Managed Service Account:

1. Verificare che la KDS Root Key esista con `Get-KdsRootKey`; se assente, crearla con `Add-KdsRootKey`.
2. Creare un gMSA con `New-ADServiceAccount -DNSHostName svc-webapp.contoso.com -PrincipalsAllowedToRetrieveManagedPassword "WebServers"`.
3. Installare il gMSA sul server target con `Install-ADServiceAccount`.
4. Configurare un servizio Windows (es. IIS Application Pool) per eseguire come gMSA.
5. Verificare il funzionamento con `Test-ADServiceAccount` e controllare che il servizio si avvii correttamente.

**Criteri di validazione**: `Test-ADServiceAccount -Identity svc-webapp` deve restituire True. Il servizio deve avviarsi senza richiedere password.

### Esercizio 4: Troubleshooting Profili Corrotti

Simulare e risolvere un profilo utente corrotto:

1. Identificare la posizione del profilo nel registry: `HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList`.
2. Simulare un profilo temporaneo (rinominare la chiave del profilo appendendo `.bak`).
3. Diagnosticare con: Event Log (User Profile Service), `whoami /user`, `echo %USERPROFILE%`.
4. Risolvere: rimuovere la chiave `.bak`, ricreare il profilo locale, ripristinare da backup se disponibile.
5. Documentare la procedura di recovery completa.

**Criteri di validazione**: l'utente deve poter effettuare il logon con il profilo corretto (non temporaneo). Le impostazioni precedenti devono essere ripristinate.

---

## Auto-valutazione

### Domanda 1

Qual è la differenza tra Roaming Profiles e FSLogix Profile Container?

<details>
<summary>Risposta</summary>

I Roaming Profiles sincronizzano il profilo tra client e share di rete al logon/logoff. Problemi: tempi di logon lunghi con profili grandi, conflitti di sincronizzazione, limitazioni con applicazioni moderne (Outlook OST, Teams cache). FSLogix containerizza l'intero profilo in un VHD/VHDX montato al logon come disco locale. Vantaggi: logon quasi istantaneo (mount vs copia), compatibilità applicativa completa, supporto per Office 365 caching. FSLogix è la soluzione raccomandata per VDI/RDS e ha sostituito Roaming Profiles nella maggior parte degli scenari.

Riferimento: Microsoft Learn, FSLogix documentation. Consultato: 2026-05-23.
</details>

### Domanda 2

Cos'è un profilo Mandatory e quando si usa?

<details>
<summary>Risposta</summary>

Un profilo Mandatory è un profilo pre-configurato che viene scartato al logoff: le modifiche dell'utente non persistono. Si crea rinominando NTUSER.DAT in NTUSER.MAN. Uso tipico: kiosk, laboratori, postazioni condivise dove serve un'esperienza utente consistente. Il profilo Super Mandatory aggiunge un ulteriore vincolo: se la share non è raggiungibile, il logon viene bloccato (anziché creare un profilo locale temporaneo). Configurazione: impostare il profile path nel tab Profile dell'utente AD.

Riferimento: Microsoft Learn, Mandatory User Profiles. Consultato: 2026-05-23.
</details>

### Domanda 3

Cos'è un gMSA e perché è preferibile a un account utente per i servizi?

<details>
<summary>Risposta</summary>

Un gMSA (Group Managed Service Account) è un account AD specifico per servizi, con password di 240 caratteri gestita e ruotata automaticamente da AD (ogni 30 giorni di default). Vantaggi rispetto a un account utente: nessuna password da gestire/documentare/ruotare manualmente, nessun rischio di scadenza password che blocca il servizio, password non indovinabile, può essere usato su più server simultaneamente. Requisiti: schema AD Windows Server 2012+, KDS Root Key configurata.

Riferimento: Microsoft Learn, Group Managed Service Accounts. Consultato: 2026-05-23.
</details>

### Domanda 4

Come funziona il versioning dei profili Windows?

<details>
<summary>Risposta</summary>

Windows usa suffissi di versione nelle cartelle profilo per evitare conflitti tra versioni OS diverse: v2 (Windows 7/Server 2008 R2), v4 (Windows 8.1/Server 2012 R2), v5 (Windows 10 pre-1607), v6 (Windows 10 1607+/Server 2016+/Windows 11). Il suffisso viene aggiunto automaticamente al path del profilo roaming. Questo garantisce che un utente che accede da Windows 10 e Windows 7 abbia profili separati, evitando incompatibilità. FSLogix usa un meccanismo diverso basato su container VHD/VHDX senza versioning del path.

Riferimento: Microsoft Learn, Profile version mapping. Consultato: 2026-05-23.
</details>

### Domanda 5

Qual è la differenza tra i tipi di avvio dei servizi Windows (Automatic, Automatic Delayed, Manual, Disabled)?

<details>
<summary>Risposta</summary>

Automatic: il servizio si avvia durante il boot del sistema. Automatic (Delayed Start): si avvia 1-2 minuti dopo il boot, riducendo il carico iniziale (raccomandato per servizi non critici all'avvio). Manual: si avvia solo quando richiesto da un altro servizio o da un trigger. Disabled: non può essere avviato in alcun modo (usato per disabilitare servizi non necessari per sicurezza). Trigger Start (aggiunto in Windows 7+): il servizio si avvia automaticamente quando si verifica un evento specifico (es. connessione di rete, join al dominio).

Riferimento: Microsoft Learn, Service startup types. Consultato: 2026-05-23.
</details>

### Domanda 6

Come si configura il recovery di un servizio Windows in caso di crash?

<details>
<summary>Risposta</summary>

Nella tab Recovery del servizio (o via `sc failure`): First failure, Second failure, Subsequent failures — azioni possibili: Restart the Service, Run a Program, Restart the Computer, Take No Action. Configurare anche: Reset fail count after N giorni, Restart service after N minuti. Best practice: primo fallimento → restart dopo 60 secondi; secondo → restart dopo 120 secondi; terzo → eseguire uno script di notifica e restart. Per servizi critici, combinare con un monitoraggio esterno (SCOM, Zabbix) che rilevi i crash pattern.

Riferimento: Microsoft Learn, Service recovery actions. Consultato: 2026-05-23.
</details>

---

## Letture Primarie Consigliate

1. **Microsoft Learn: FSLogix Documentation** — Guida completa a Profile Container, Office Container, Cloud Cache.
   https://learn.microsoft.com/en-us/fslogix/
   Consultato: 2026-05-23.

2. **Microsoft Learn: Folder Redirection and Offline Files** — Configurazione, troubleshooting e best practice.
   https://learn.microsoft.com/en-us/windows-server/storage/folder-redirection/
   Consultato: 2026-05-23.

3. **Microsoft Learn: Group Managed Service Accounts** — Creazione, configurazione e troubleshooting gMSA.
   https://learn.microsoft.com/en-us/windows-server/security/group-managed-service-accounts/group-managed-service-accounts-overview
   Consultato: 2026-05-23.

4. **James Rankin Blog** — Approfondimenti tecnici su FSLogix, profili utente, e ottimizzazione VDI.
   https://james-rankin.com/
   Consultato: 2026-05-23.

5. **Microsoft Learn: Mandatory User Profiles** — Creazione e gestione di profili mandatory e super mandatory.
   https://learn.microsoft.com/en-us/windows/client-management/mandatory-user-profile
   Consultato: 2026-05-23.

---

## Collegamenti Incrociati

| File | Relazione con questo modulo |
|---|---|
| [01-active-directory.md](01-active-directory.md) | Prerequisito: struttura AD, GPO, account utente per profili e gMSA |
| [08-permessi-e-accesso.md](08-permessi-e-accesso.md) | Prerequisito: permessi NTFS sulle share dei profili e Folder Redirection |
| [07-storage-windows.md](07-storage-windows.md) | Contesto: SMB share per profili, VHD/VHDX per FSLogix |
| [21-group-policy-guida-completa.md](21-group-policy-guida-completa.md) | Configurazione: GPO per Folder Redirection, profili roaming, FSLogix settings |
| [15-backup-ripristino.md](15-backup-ripristino.md) | Contesto: backup dei profili e delle share di Folder Redirection |

---

## Glossario Locale

| Termine | Definizione |
|---|---|
| **AppData** | Cartella del profilo utente che contiene dati applicativi (%APPDATA% = Roaming, %LOCALAPPDATA% = Local). |
| **DFSR** | Distributed File System Replication. Replica automatica di cartelle tra server. |
| **ESE** | Extensible Storage Engine. Motore database usato per cache profili e Outlook OST. |
| **Folder Redirection** | GPO che reindirizza cartelle utente (Documenti, Desktop) a una share di rete. |
| **FSLogix** | Soluzione Microsoft (acquisita 2018) per la containerizzazione dei profili tramite VHD/VHDX. |
| **Delprof2** | Utility di pulizia profili utente per ambienti enterprise. Rimuove profili inattivi da RDS/VDI. |
| **dMSA** | Delegated Managed Service Account (Server 2025). Account di servizio con credenziali machine-bound che non lasciano mai il DC, immune a Kerberoasting. |
| **gMSA** | Group Managed Service Account. Account AD per servizi con password gestita automaticamente su più server. |
| **Kerberoasting** | Attacco che estrae e cracca offline i ticket Kerberos dei service account per ottenere le password. dMSA è immune. |
| **NTUSER.DAT** | File di registro che contiene l'hive HKEY_CURRENT_USER del profilo utente. |
| **NTUSER.MAN** | NTUSER.DAT rinominato per creare un profilo mandatory (read-only). |
| **SCM** | Service Control Manager. Componente Windows che gestisce il ciclo di vita dei servizi. |
| **Service SID** | Security Identifier per-servizio (NT SERVICE\NomeServizio). Usabile nelle ACL per proteggere risorse specifiche del servizio. |
| **UE-V** | User Environment Virtualization. Sincronizza impostazioni applicative tra dispositivi. |
| **WEF** | Windows Event Forwarding. Meccanismo nativo per raccogliere eventi da server remoti verso un collector centralizzato. |
