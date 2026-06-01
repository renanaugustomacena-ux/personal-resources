# Driver e Compatibilità Windows — Guida Completa

> **Modulo 18** · **Aggiornamento:** 2026-05-23

| Campo | Valore |
|---|---|
| **Corso** | Windows per Ingegneri di Sistema |
| **Fase** | Fase 3 — Infrastruttura e compatibilità |
| **Modulo** | 18 — Driver e Compatibilità |
| **Versione di riferimento** | Windows 11 24H2, Windows Server 2025, WDK 10.0.26100, DISM 10.0.x, PnPUtil 10.0.x |
| **Livello** | Proficient (avanzato) |
| **Prerequisiti** | Architettura Windows kernel/user mode (→ `05-sicurezza-windows.md`), PowerShell intermedio (→ `02-powershell.md`), familiarità con Device Manager e DISM, nozioni di crittografia e firme digitali |
| **Obiettivi di apprendimento** | 1) Comprendere l'architettura WDM / WDF e scegliere tra KMDF e UMDF in base al tipo di dispositivo · 2) Gestire il ciclo di vita dei driver: staging, deploy, rollback, ritiro · 3) Applicare le policy di firma driver (WHQL, attestation, KMCS) e configurare Secure Boot · 4) Diagnosticare problemi driver tramite Driver Verifier, Device Manager status codes e crash dump · 5) Iniettare driver in immagini WIM con DISM e gestire il deploy enterprise via MDT/SCCM/Intune · 6) Configurare HVCI e verificare la compatibilità dei driver con Virtualization-Based Security · 7) Risolvere problemi di compatibilità applicativa con shim, SxS assemblies, API sets e manifest · 8) Amministrare driver di stampa (v3/v4, Universal Print), GPU (WDDM), storage (Storport/NVMe), rete (NDIS/NetAdapterCx) e USB |
| **Tempo stimato** | 20–28 ore (studio + esercizi + laboratorio) |
| **Ultimo aggiornamento** | 2026-05-23 |
| **Tag** | driver, WDM, WDF, KMDF, UMDF, WHQL, driver-signing, HVCI, VBS, Driver-Verifier, PnPUtil, DISM, Device-Manager, WDAC, compatibility, shim, SxS, NDIS, SR-IOV, WDDM, GPU-P, Storport, NVMe, USB-Type-C, Universal-Print, PrintNightmare |

## Idee guida
1. **Driver signing mandatory; WHQL preferred.**
2. **Driver Verifier per debug driver issue.**
3. **DISM + sfc per system file repair.**
4. **Compatibility Mode per legacy app.**
5. **Driver lifecycle: test → stage → deploy → monitor → retire.**
6. **HVCI e VBS impongono requisiti driver più stringenti.**
7. **Automazione PnPUtil + DISM per imaging e provisioning.**

### Mappa Concettuale

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                     DRIVER E COMPATIBILITÀ WINDOWS                            │
├──────────────────┬──────────────────┬───────────────────┬─────────────────────┤
│  ARCHITETTURA    │  FIRMA & TRUST   │  CLASSI DRIVER    │  COMPATIBILITÀ      │
│                  │                  │                   │                     │
│ ┌──────────────┐ │ ┌──────────────┐ │ ┌───────────────┐ │ ┌─────────────────┐ │
│ │ WDM (legacy) │ │ │ WHQL / HLK   │ │ │ Print v3/v4   │ │ │ Compat. Mode    │ │
│ │ WDF: KMDF    │ │ │ Attestation  │ │ │ Universal Prt │ │ │ Shim (SDB)      │ │
│ │ WDF: UMDF    │ │ │ EV / Auth.   │ │ ├───────────────┤ │ │ ACT / ADK       │ │
│ └──────────────┘ │ ├──────────────┤ │ │ GPU / WDDM    │ │ ├─────────────────┤ │
│ ┌──────────────┐ │ │ Secure Boot  │ │ │ GPU-P / GPU-PV│ │ │ API Sets        │ │
│ │ Port/Miniport│ │ │ UEFI + db/dbx│ │ ├───────────────┤ │ │ SxS Assemblies  │ │
│ │ Miniclass    │ │ ├──────────────┤ │ │ Storage:      │ │ │ Manifest (.man) │ │
│ └──────────────┘ │ │ KMCS         │ │ │ Storport/NVMe │ │ │ DLL Search Ord. │ │
│ ┌──────────────┐ │ │ HVCI / VBS   │ │ ├───────────────┤ │ ├─────────────────┤ │
│ │ INF + CAT    │ │ │ Code Integr. │ │ │ Rete: NDIS    │ │ │ MSIX / App-V    │ │
│ │ SYS + DLL    │ │ └──────────────┘ │ │ NetAdapterCx  │ │ │ WDAC            │ │
│ └──────────────┘ │                  │ │ SR-IOV / VMQ  │ │ │ AppLocker       │ │
│                  │                  │ ├───────────────┤ │ └─────────────────┘ │
│                  │                  │ │ USB: USBX     │ │                     │
│                  │                  │ │ Type-C / UAC  │ │                     │
│                  │                  │ └───────────────┘ │                     │
├──────────────────┴──────────────────┴───────────────────┴─────────────────────┤
│  DEPLOY: Driver Store │ PnPUtil │ DISM │ MDT │ SCCM/MECM │ Intune │ WUfB    │
├──────────────────────────────────────────────────────────────────────────────┤
│  DIAG: Driver Verifier │ Device Manager Codes │ setupapi.dev.log │ WinDbg   │
├──────────────────────────────────────────────────────────────────────────────┤
│  PS: Get-PnpDevice │ Get-WindowsDriver │ Add-WindowsDriver │ Export-WinDrv  │
└──────────────────────────────────────────────────────────────────────────────┘
```


## Indice

- [Panoramica](#panoramica)
- [Architettura Driver Windows](#architettura-driver-windows)
- [WDM vs WDF — Confronto Approfondito](#wdm-vs-wdf--confronto-approfondito)
- [Device Manager](#device-manager)
- [Gestione Driver](#gestione-driver)
- [Driver Store — Architettura Interna](#driver-store--architettura-interna)
- [Driver Signing e Integrità](#driver-signing-e-integrità)
- [KMCS — Kernel-Mode Code Signing](#kmcs--kernel-mode-code-signing)
- [HVCI e Virtualization-Based Security](#hvci-e-virtualization-based-security)
- [Driver Verifier — Guida Approfondita](#driver-verifier--guida-approfondita)
- [Driver di Stampa — v3, v4 e Universal Print](#driver-di-stampa--v3-v4-e-universal-print)
- [Driver GPU e Display — WDDM e GPU Partitioning](#driver-gpu-e-display--wddm-e-gpu-partitioning)
- [Driver Storage — Storport, SCSI Port e NVMe](#driver-storage--storport-scsi-port-e-nvme)
- [Driver di Rete — NDIS, NetAdapterCx e SR-IOV](#driver-di-rete--ndis-netadaptercx-e-sr-iov)
- [Driver USB — Stack, USBX, Type-C e Audio Class](#driver-usb--stack-usbx-type-c-e-audio-class)
- [Compatibilità Applicazioni](#compatibilità-applicazioni)
- [API Sets, SxS Assemblies e DLL Search Order](#api-sets-sxs-assemblies-e-dll-search-order)
- [Application Compatibility Toolkit — Scenari Avanzati](#application-compatibility-toolkit--scenari-avanzati)
- [Impostazioni di Compatibilità Windows](#impostazioni-di-compatibilità-windows)
- [Virtualizzazione Applicazioni](#virtualizzazione-applicazioni)
- [WDAC — Application Control](#wdac--application-control)
- [WDAC — Scenari Enterprise Avanzati](#wdac--scenari-enterprise-avanzati)
- [Deploy Driver Enterprise — MDT, SCCM, Intune](#deploy-driver-enterprise--mdt-sccm-intune)
- [Windows Update for Business — Driver Management](#windows-update-for-business--driver-management)
- [Automazione e Script di Gestione Driver](#automazione-e-script-di-gestione-driver)
- [GPO per Driver e Compatibilità](#gpo-per-driver-e-compatibilità)
- [Scenari Reali Enterprise](#scenari-reali-enterprise)
- [Best Practices](#best-practices)
- [Alberi Decisionali di Troubleshooting](#alberi-decisionali-di-troubleshooting)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Esercizi](#esercizi)
- [Auto-valutazione](#auto-valutazione)
- [Letture Primarie Consigliate](#letture-primarie-consigliate)
- [Collegamenti Incrociati](#collegamenti-incrociati)
- [Glossario Locale](#glossario-locale)

---

## Panoramica

I driver sono il ponte tra hardware e sistema operativo. La gestione driver in ambiente enterprise richiede: inventario hardware, driver catalog approvato, deploy automatizzato, e testing di compatibilità. Windows fornisce strumenti integrati (Device Manager, DISM, PnPUtil) e policy (driver signing, WDAC) per mantenere un ambiente stabile e sicuro.

Il lifecycle completo di un driver in ambiente enterprise segue queste fasi:

```
┌─────────────────────────────────────────────────────────┐
│               DRIVER LIFECYCLE ENTERPRISE               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. DISCOVERY    → Identificare hardware e driver       │
│         ↓           necessari                           │
│  2. ACQUISITION  → Scaricare da OEM/vendor              │
│         ↓           (WHQL certified preferred)          │
│  3. TESTING      → Validare su lab/pilot                │
│         ↓           (Driver Verifier, HVCI compat)      │
│  4. STAGING      → Inserire nel Driver Store /          │
│         ↓           repository aziendale                │
│  5. DEPLOYMENT   → Distribuire via MDT/SCCM/Intune/    │
│         ↓           Windows Update for Business         │
│  6. MONITORING   → Event log, performance counters,     │
│         ↓           crash dump analysis                 │
│  7. MAINTENANCE  → Aggiornare, rollback se necessario   │
│         ↓                                               │
│  8. RETIREMENT   → Rimuovere driver obsoleti dal        │
│                     Driver Store e dall'imaging          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Architettura Driver Windows

### Modello Driver Windows (WDM, WDF, KMDF, UMDF)

```
┌──────────────────────────────────────────────────────────┐
│                    APPLICAZIONE UTENTE                    │
├──────────────────────────────────────────────────────────┤
│                    USER MODE (Ring 3)                     │
│  ┌──────────────────────────────────────────────────┐    │
│  │  UMDF Driver (User Mode Driver Framework)        │    │
│  │  → Stampanti, sensori, USB semplici              │    │
│  │  → Crash non causa BSOD                          │    │
│  │  → Accesso limitato all'hardware                 │    │
│  └──────────────────────────────────────────────────┘    │
├──────────────────────────────────────────────────────────┤
│                   KERNEL MODE (Ring 0)                    │
│  ┌──────────────────────────────────────────────────┐    │
│  │  KMDF Driver (Kernel Mode Driver Framework)      │    │
│  │  → Storage, rete, GPU, chipset                   │    │
│  │  → Crash causa BSOD                              │    │
│  │  → Accesso completo all'hardware                 │    │
│  └──────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────┐    │
│  │  WDM Driver (Windows Driver Model) — Legacy      │    │
│  │  → Modello precedente, più complesso              │    │
│  │  → Ancora usato da driver vecchi                  │    │
│  └──────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────┐    │
│  │  Miniport / Miniclass Driver                      │    │
│  │  → Modello port/miniport per storage e rete       │    │
│  │  → Il port driver è fornito da Microsoft          │    │
│  │  → Il vendor fornisce solo il miniport            │    │
│  └──────────────────────────────────────────────────┘    │
├──────────────────────────────────────────────────────────┤
│                       HARDWARE                           │
└──────────────────────────────────────────────────────────┘
```

### File che compongono un driver

```powershell
# Un driver Windows è composto da:
#
# *.inf     → File setup/installazione. Descrive l'hardware supportato,
#             i file da copiare, le chiavi registry da creare.
#             PnPUtil e Device Manager leggono questo file.
#
# *.sys     → Il driver vero e proprio (kernel-mode binary).
#             Caricato in memoria kernel. Un bug qui = BSOD.
#
# *.dll     → Componenti user-mode (UI, servizi di supporto).
#
# *.cat     → Catalogo firma digitale. Contiene gli hash firmati
#             di tutti i file del pacchetto driver.
#             Windows verifica il .cat prima di caricare il driver.
#
# *.cer     → Certificato del publisher (opzionale, per trust).

# Esempio struttura pacchetto driver Intel Ethernet:
# e1d65x64.inf    → Setup file
# e1d65x64.sys    → Driver kernel
# e1d65x64.cat    → Catalogo firma
# e1d65x64.din    → Dati configurazione
# NicCo36.dll     → Componente user-mode
# PROSetCL.exe    → Utility configurazione
```

### INF File — Struttura e Sezioni Chiave

```ini
; Esempio di file .inf annotato

[Version]
Signature   = "$WINDOWS NT$"          ; Sempre questo valore
Class       = Net                      ; Classe dispositivo (Net, Display, etc.)
ClassGuid   = {4d36e972-e325-11ce-bfc1-08002be10318}  ; GUID classe
Provider    = %ManufacturerName%       ; Variabile definita in [Strings]
CatalogFile = driver.cat               ; File catalogo firma
DriverVer   = 05/15/2025, 12.19.2.48  ; Data e versione
PnpLockdown = 1                        ; Protegge i file driver dalla modifica

[Manufacturer]
%ManufacturerName% = DeviceList, NTamd64.10.0...22000  ; Target OS build

[DeviceList.NTamd64.10.0...22000]
%DeviceName% = Install_Section, PCI\VEN_8086&DEV_15F3  ; Hardware ID

[Install_Section]
CopyFiles = DriverFiles
AddReg    = DriverReg

[DriverFiles]
mydriver.sys

[DriverReg]
HKR, , DriverSetting1, 0x00010001, 1  ; REG_DWORD = 1

[Strings]
ManufacturerName = "Contoso Corp"
DeviceName       = "Contoso Network Adapter"
```

```powershell
# Analizzare un INF file per estrarre hardware ID supportati
Select-String -Path "C:\Drivers\*.inf" -Pattern "PCI\\VEN_" |
    ForEach-Object { $_.Line.Trim() }

# Trovare l'INF corretto per un dispositivo specifico
$hwId = (Get-PnpDevice -FriendlyName "*Intel*Ethernet*").HardwareID[0]
Write-Host "Hardware ID: $hwId"
# Cercare questo ID nei file .inf dei driver scaricati
Select-String -Path "C:\Drivers\**\*.inf" -Pattern ($hwId -replace '\\','\\')
```

---

## WDM vs WDF — Confronto Approfondito

### Evoluzione dei modelli driver

```
┌─────────────────────────────────────────────────────────────┐
│               EVOLUZIONE MODELLI DRIVER WINDOWS             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1993  VxD (Windows 3.1 / 9x)                              │
│    ↓     → Modello 16/32-bit, nessuna protezione            │
│  1998  WDM (Windows 98 / 2000)                              │
│    ↓     → Primo modello kernel-mode strutturato            │
│    ↓     → IRP-based, complesso, error-prone                │
│  2006  WDF 1.0 (Windows Vista)                              │
│    ↓     → Framework object-oriented su WDM                 │
│    ↓     → KMDF per kernel, UMDF per user-mode              │
│  2015  UMDF 2.0 (Windows 10)                                │
│    ↓     → API quasi identica a KMDF                        │
│    ↓     → Migrazione semplificata UMDF ↔ KMDF              │
│  2023  WDF 1.33+ / UMDF 2.33+                              │
│         → Supporto ARM64, HVCI, VBS                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### WDM (Windows Driver Model) — Dettagli

```powershell
# WDM è il modello driver legacy, diretto predecessore di WDF.
# Richiede al driver di gestire manualmente:
#
# - IRP (I/O Request Packets): ogni richiesta I/O è un IRP
#   Il driver deve implementare dispatch routines per ogni tipo di IRP
#   (IRP_MJ_CREATE, IRP_MJ_READ, IRP_MJ_WRITE, IRP_MJ_DEVICE_CONTROL, ecc.)
#
# - PnP e Power Management: il driver deve gestire
#   IRP_MN_START_DEVICE, IRP_MN_STOP_DEVICE, IRP_MN_REMOVE_DEVICE
#   IRP_MN_SET_POWER, IRP_MN_QUERY_POWER
#
# - Concorrenza: il driver deve gestire spinlock, IRQL,
#   DPC (Deferred Procedure Call), ISR (Interrupt Service Routine)
#
# - Cleanup: il driver deve rilasciare tutte le risorse manualmente
#   Errori in questa fase causano memory leak e resource leak
#
# PROBLEMI WDM:
# - Codice boilerplate enorme (migliaia di linee per un driver semplice)
# - Facile introdurre bug: BSOD per IRQL errato, deadlock, memory leak
# - Nessun supporto integrato per power management moderno
# - Nessuna protezione tra driver e kernel
#
# QUANDO SI INCONTRA ANCORA WDM:
# - Driver legacy per hardware industriale
# - Filter driver per storage/rete
# - Driver di nicchia mai migrati a WDF
```

### WDF: KMDF vs UMDF — Quando usare quale

```powershell
# ┌───────────────────┬─────────────────────┬─────────────────────┐
# │ CARATTERISTICA    │ KMDF                │ UMDF (v2)           │
# ├───────────────────┼─────────────────────┼─────────────────────┤
# │ Esecuzione        │ Kernel mode (Ring 0) │ User mode (Ring 3)  │
# │ Crash impatto     │ BSOD intero sistema │ Solo il driver       │
# │                   │                     │ (auto-restart)       │
# │ Accesso hardware  │ Diretto (MMIO, DMA, │ Tramite framework    │
# │                   │ interrupt)          │ (I/O mediato)        │
# │ Performance       │ Massima (nessun     │ Overhead context     │
# │                   │ context switch)     │ switch user↔kernel   │
# │ Debugging         │ Kernel debugger     │ User-mode debugger   │
# │                   │ (WinDbg)            │ (Visual Studio)      │
# │ Sicurezza         │ Nessuna sandbox     │ Sandbox UMDF host    │
# │ HVCI compat.      │ Deve essere HVCI-   │ Intrinsecamente      │
# │                   │ compatible          │ compatibile          │
# │ Firma richiesta   │ WHQL / Attestation  │ Authenticode suff.   │
# │ Casi d'uso        │ Storage, NIC, GPU,  │ Stampanti, sensori,  │
# │                   │ chipset, audio      │ USB periferiche,     │
# │                   │                     │ NFC, biometrici      │
# └───────────────────┴─────────────────────┴─────────────────────┘
#
# REGOLA DECISIONALE:
# 1. Il dispositivo richiede DMA, interrupt, o accesso hardware diretto?
#    → KMDF
# 2. Il dispositivo è una periferica USB senza requisiti di latenza critici?
#    → UMDF
# 3. Il driver deve funzionare con HVCI senza modifiche?
#    → UMDF (se il dispositivo lo permette)
# 4. Il driver deve supportare Windows Server Core senza GUI?
#    → KMDF (UMDF richiede il UMDF Host process)
# 5. In dubbio?
#    → Iniziare con UMDF, migrare a KMDF solo se necessario

# Identificare il tipo di framework usato da un driver installato
Get-CimInstance Win32_PnPSignedDriver |
    Where-Object DeviceName -like "*Intel*" |
    Select-Object DeviceName, DriverVersion, InfName,
        @{N='IsSigned';E={$_.IsSigned}},
        @{N='DriverType';E={
            $infPath = "C:\Windows\INF\$($_.InfName)"
            if (Test-Path $infPath) {
                $content = Get-Content $infPath -Raw
                if ($content -match 'UmdfService') { 'UMDF' }
                elseif ($content -match 'KmdfService') { 'KMDF' }
                else { 'WDM/Other' }
            } else { 'Unknown' }
        }} | Format-Table -AutoSize
```

Rif.: *Windows Driver Frameworks*, https://learn.microsoft.com/en-us/windows-hardware/drivers/wdf/ (consultato: 2026-05-23)

---

## Device Manager

```powershell
# Device Manager (devmgmt.msc) — interfaccia GUI per gestione dispositivi

# PowerShell: elencare dispositivi
Get-PnpDevice | Select-Object Class, FriendlyName, Status, InstanceId |
    Sort-Object Class | Format-Table -AutoSize

# Dispositivi con problemi
Get-PnpDevice | Where-Object Status -ne "OK" |
    Select-Object Class, FriendlyName, Status, Problem

# Dispositivi per classe
Get-PnpDevice -Class Display         # Schede video
Get-PnpDevice -Class Net             # Schede di rete
Get-PnpDevice -Class DiskDrive       # Dischi
Get-PnpDevice -Class HIDClass        # Human Interface Devices
Get-PnpDevice -Class USB             # Controller USB
Get-PnpDevice -Class AudioEndpoint   # Dispositivi audio
Get-PnpDevice -Class Bluetooth       # Bluetooth
Get-PnpDevice -Class PrintQueue      # Stampanti
Get-PnpDevice -Class Camera          # Webcam

# Proprietà driver di un dispositivo
Get-PnpDeviceProperty -InstanceId "PCI\VEN_8086&DEV_..." |
    Where-Object KeyName -like "*Driver*"

# Ottenere versione driver di un dispositivo specifico
Get-PnpDevice -Class Net | ForEach-Object {
    $props = Get-PnpDeviceProperty -InstanceId $_.InstanceId
    [PSCustomObject]@{
        Device        = $_.FriendlyName
        DriverVersion = ($props | Where-Object KeyName -eq 'DEVPKEY_Device_DriverVersion').Data
        DriverDate    = ($props | Where-Object KeyName -eq 'DEVPKEY_Device_DriverDate').Data
        DriverProvider= ($props | Where-Object KeyName -eq 'DEVPKEY_Device_DriverProvider').Data
        INFName       = ($props | Where-Object KeyName -eq 'DEVPKEY_Device_DriverInfPath').Data
    }
} | Format-Table -AutoSize

# Disabilitare/Abilitare dispositivo
Disable-PnpDevice -InstanceId "USB\VID_..." -Confirm:$false
Enable-PnpDevice -InstanceId "USB\VID_..." -Confirm:$false

# Inventario completo hardware — Export CSV per CMDB
Get-PnpDevice | Where-Object Status -eq "OK" | ForEach-Object {
    $props = Get-PnpDeviceProperty -InstanceId $_.InstanceId -ErrorAction SilentlyContinue
    [PSCustomObject]@{
        Class          = $_.Class
        FriendlyName   = $_.FriendlyName
        InstanceId     = $_.InstanceId
        HardwareIds    = ($_.HardwareID -join "; ")
        DriverVersion  = ($props | Where-Object KeyName -eq 'DEVPKEY_Device_DriverVersion').Data
        Manufacturer   = ($props | Where-Object KeyName -eq 'DEVPKEY_Device_Manufacturer').Data
    }
} | Export-Csv "C:\Temp\HW-Inventory-$(hostname).csv" -NoTypeInformation -Encoding UTF8

# Device codes di errore comuni:
# Code 1:  Device not configured correctly
# Code 3:  Driver for this device might be corrupted
# Code 10: Device cannot start
# Code 12: Not enough resources (IRQ/memory conflict)
# Code 14: Device requires restart to work properly
# Code 16: Windows cannot identify all resources
# Code 18: Reinstall the drivers for this device
# Code 19: Registry info for this device is incomplete/damaged
# Code 21: Windows is removing this device
# Code 22: Device is disabled
# Code 24: Device is not present / not working / not all drivers installed
# Code 28: Drivers not installed
# Code 29: Device disabled because firmware did not give required resources
# Code 31: Device not working properly (driver load failed)
# Code 32: Driver for this device has been disabled (registry)
# Code 33: Windows cannot determine which resources are required
# Code 34: Windows cannot determine settings for this device
# Code 37: Windows cannot initialize the device driver
# Code 39: Windows cannot load the device driver — corrupted or missing
# Code 41: Windows loaded the driver but cannot find the device
# Code 43: Device has been stopped — driver reported a problem
# Code 44: An application or service has shut down this device
# Code 45: Currently, this device is not connected to the computer
# Code 46: Cannot gain access (OS is shutting down)
# Code 47: Hot unplug preparation — cannot be used
# Code 48: Software for this device has been blocked (compatibility)
# Code 49: Windows cannot start new hardware (system hive too large)
# Code 50: Windows cannot apply all properties for this device
# Code 51: This device is waiting on another device
# Code 52: Windows cannot verify the digital signature of the driver
# Code 53: Device reserved for Windows debugger
# Code 54: Device has failed and is being reset (ACPI)
# Code 56: Windows is still setting up the class configuration
```

### Device Manager — Operazioni Avanzate

```powershell
# Forzare re-detect hardware (equivale a "Scan for hardware changes")
$devcon = "C:\Tools\devcon.exe"  # Scaricare da Windows SDK
# Oppure via PowerShell: richiamare Device Installation scan
# Nota: non c'è un cmdlet nativo; usare CIM o WMI
$searcher = [System.Management.ManagementObjectSearcher]::new(
    "SELECT * FROM Win32_PnPEntity WHERE Status='Error'"
)
$searcher.Get() | ForEach-Object {
    Write-Host "Dispositivo in errore: $($_.Caption) — Status: $($_.Status)"
}

# Ottenere device tree gerarchico
function Get-DeviceTree {
    param([string]$ParentId = "")
    $devices = Get-PnpDevice | Where-Object { $_.InstanceId -like "*$ParentId*" }
    foreach ($dev in $devices) {
        [PSCustomObject]@{
            Name       = $dev.FriendlyName
            Class      = $dev.Class
            Status     = $dev.Status
            InstanceId = $dev.InstanceId
        }
    }
}

# Dispositivi nascosti (hidden devices) — spesso causa di conflitti
# In Device Manager: View → Show hidden devices
# Via PowerShell — mostrare dispositivi non presenti:
$env:DEVMGR_SHOW_NONPRESENT_DEVICES = 1
Get-PnpDevice -Status Unknown | Select-Object Class, FriendlyName, InstanceId

# Conteggio dispositivi per classe (panoramica fleet)
Get-PnpDevice | Where-Object Status -eq "OK" |
    Group-Object Class |
    Sort-Object Count -Descending |
    Select-Object Count, Name | Format-Table -AutoSize
```

### Device Path e Instance ID — Anatomia

```powershell
# L'Instance ID è l'identificativo univoco di un dispositivo nell'albero PnP.
# Formato: <BusType>\<DeviceID>\<InstanceID>
#
# Esempio NIC Intel:
#   PCI\VEN_8086&DEV_15F3&SUBSYS_00008086&REV_03\3&11583659&0&FE
#   │     │         │         │              │      └─ Instance specifico
#   │     │         │         │              └─ Revisione silicon
#   │     │         │         └─ Subsystem (vendor + device board)
#   │     │         └─ Device ID Intel I225-V
#   │     └─ Vendor ID Intel Corporation
#   └─ Bus PCI
#
# Esempio USB:
#   USB\VID_046D&PID_C52B\5&2F5D1C1&0&2
#   │    │         │       └─ Instance specifico (porta + hub)
#   │    │         └─ Product ID (Logitech Unifying Receiver)
#   │    └─ Vendor ID (Logitech)
#   └─ Bus USB
#
# Il Device Path (utilizzato da applicazioni Win32) usa il formato:
#   \\?\PCI#VEN_8086&DEV_15F3#3&11583659&0&FE#{GUID-interfaccia}
# Nota: backslash → #, GUID identifica l'interfaccia del dispositivo

# Ottenere il device path completo
Get-PnpDeviceProperty -InstanceId "PCI\VEN_8086&DEV_15F3*" |
    Where-Object KeyName -eq 'DEVPKEY_Device_PDOName' |
    Select-Object InstanceId, Data
```

---

## Gestione Driver

### Driver Store

```powershell
# Windows Driver Store: C:\Windows\System32\DriverStore\FileRepository\
# Contiene tutti i driver installati e disponibili

# Elencare driver nel Driver Store
pnputil /enum-drivers
# O filtrato:
pnputil /enum-drivers | findstr "Published Name"

# Aggiungere driver al Driver Store
pnputil /add-driver C:\Drivers\network\*.inf /subdirs /install
# /subdirs = include sottodirectory
# /install = installa immediatamente se hardware presente

# Rimuovere driver dal Driver Store
pnputil /delete-driver oem42.inf /force
# /force = anche se in uso (richiede reboot)

# Esportare driver installati (per backup o imaging)
Export-WindowsDriver -Online -Destination "C:\Backup\Drivers"
# Esporta TUTTI i driver third-party in cartelle con .inf

# DISM per gestione offline (immagini WIM)
DISM /Image:C:\Mount /Add-Driver /Driver:C:\Drivers /Recurse
DISM /Image:C:\Mount /Get-Drivers
DISM /Image:C:\Mount /Remove-Driver /Driver:oem42.inf

# Driver rollback (tornare alla versione precedente)
# Device Manager → Dispositivo → Properties → Driver → Roll Back Driver
# Disponibile solo se esiste un driver precedente

# Windows Update per driver
# I driver vengono distribuiti anche via Windows Update (optional)
# GPO per controllare: Computer → Administrative Templates →
#   Windows Components → Windows Update → Do not include drivers with Windows Updates
```

### Driver per Deploy (MDT/SCCM)

```powershell
# Per imaging enterprise, i driver vengono iniettati durante il deployment

# Struttura cartella driver consigliata:
# D:\Drivers\
# ├── Dell\
# │   ├── Latitude-5540\
# │   │   ├── Network\
# │   │   ├── Chipset\
# │   │   └── Video\
# │   └── OptiPlex-7090\
# ├── HP\
# │   └── EliteDesk-800-G9\
# └── Lenovo\
#     └── ThinkPad-T14s\

# MDT: Deployment Workbench → Out-of-Box Drivers → Import
# SCCM: Software Library → Operating Systems → Driver Packages

# Per SCCM Task Sequence:
# Step "Auto Apply Drivers" — seleziona automaticamente in base all'hardware
# O: "Apply Driver Package" — applica un pacchetto specifico per modello
```

---

## Driver Store — Architettura Interna

### Come funziona il Driver Store

```
┌────────────────────────────────────────────────────────────┐
│                  DRIVER STORE WORKFLOW                      │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  STAGING (pnputil /add-driver)                             │
│  ┌──────────────────────────────────────────────────┐      │
│  │ 1. Windows verifica la firma del catalogo (.cat) │      │
│  │ 2. Copia i file in DriverStore\FileRepository\   │      │
│  │ 3. Assegna nome oem<N>.inf                       │      │
│  │ 4. Il driver è ora "disponibile" ma NON attivo   │      │
│  └──────────────────────────────────────────────────┘      │
│           ↓                                                │
│  INSTALLAZIONE (Plug & Play)                               │
│  ┌──────────────────────────────────────────────────┐      │
│  │ 1. Nuovo hardware rilevato (PnP Event)           │      │
│  │ 2. PnP Manager cerca nel Driver Store            │      │
│  │ 3. Confronta Hardware ID con .inf disponibili    │      │
│  │ 4. Seleziona il driver con ranking migliore      │      │
│  │    (HW ID match > compat ID, data più recente)   │      │
│  │ 5. Copia i file in System32\drivers\             │      │
│  │ 6. Crea chiavi registry per il dispositivo       │      │
│  │ 7. Driver caricato in memoria                    │      │
│  └──────────────────────────────────────────────────┘      │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Driver Ranking — Come Windows sceglie il driver

```powershell
# Quando più driver corrispondono a un dispositivo, Windows usa un ranking:
#
# PRIORITÀ (dalla più alta):
#
# 1. Hardware ID match (esatto) > Compatible ID match
#    Hardware ID: PCI\VEN_8086&DEV_15F3&SUBSYS_00008086&REV_03
#    Compatible ID: PCI\VEN_8086&DEV_15F3 (meno specifico)
#
# 2. Firma del driver:
#    - Inbox (incluso nel Windows image) = ranking più alto
#    - WHQL signed (Windows Hardware Quality Labs)
#    - Authenticode signed (certificato commerciale)
#    - Unsigned = bloccato su 64-bit
#
# 3. Feature Score (DriverVer + match specificity)
#    - DriverVer più recente vince a parità di match
#
# 4. Data del driver (DriverVer nel .inf)
#    - Data più recente vince

# Visualizzare il ranking per un dispositivo:
# setupapi.dev.log contiene tutti i dettagli del processo di selezione
Get-Content "C:\Windows\INF\setupapi.dev.log" -Tail 200 |
    Select-String "Rank|Selected|Searching"

# Forzare l'installazione di un driver specifico ignorando il ranking
pnputil /add-driver "C:\Drivers\specific\driver.inf" /install /force

# Impedire che Windows Update sovrascriva un driver staging
# GPO: Computer → Administrative Templates → System → Device Installation
#   → Prevent device metadata retrieval from the Internet: Enabled
```

### PnPUtil — Riferimento Completo

```powershell
# PnPUtil è lo strumento command-line principale per la gestione Driver Store

# Elencare tutti i driver OEM nel Driver Store
pnputil /enum-drivers

# Elencare driver con informazioni dettagliate
pnputil /enum-drivers /class "Net"      # Solo driver di rete
pnputil /enum-drivers /class "Display"  # Solo driver video

# Elencare dispositivi
pnputil /enum-devices                           # Tutti i dispositivi
pnputil /enum-devices /connected                # Solo connessi
pnputil /enum-devices /disconnected             # Solo disconnessi
pnputil /enum-devices /class Net                # Solo classe Net
pnputil /enum-devices /problem                  # Dispositivi con problemi
pnputil /enum-devices /deviceids                # Mostra Hardware ID

# Aggiungere driver
pnputil /add-driver "C:\Drivers\*.inf"                        # Singola cartella
pnputil /add-driver "C:\Drivers\*.inf" /subdirs               # Ricorsivo
pnputil /add-driver "C:\Drivers\*.inf" /subdirs /install      # Stage + install
pnputil /add-driver "C:\Drivers\*.inf" /subdirs /install /reboot  # + reboot se serve

# Rimuovere driver
pnputil /delete-driver oem42.inf             # Rimuove se non in uso
pnputil /delete-driver oem42.inf /uninstall  # Disinstalla anche dal dispositivo
pnputil /delete-driver oem42.inf /force      # Forza rimozione anche se in uso

# Esportare driver
pnputil /export-driver oem42.inf C:\Backup\  # Esporta un driver specifico
pnputil /export-driver * C:\Backup\          # Esporta tutti i driver OEM

# Disabilitare / Abilitare / Riavviare dispositivo
pnputil /disable-device "USB\VID_0781&PID_5581\..."
pnputil /enable-device "USB\VID_0781&PID_5581\..."
pnputil /restart-device "USB\VID_0781&PID_5581\..."

# Scansione hardware changes
pnputil /scan-devices
```

### DISM per Driver — Gestione Offline e Online

```powershell
# DISM (Deployment Image Servicing and Management) gestisce driver in immagini WIM
# e nel sistema operativo corrente (online)

# === OPERAZIONI ONLINE ===

# Elencare driver third-party installati
DISM /Online /Get-Drivers /Format:Table

# Elencare con dettagli (include inbox drivers)
DISM /Online /Get-Drivers /All /Format:Table

# Dettagli su un driver specifico
DISM /Online /Get-DriverInfo /Driver:oem42.inf

# Aggiungere driver al sistema online
DISM /Online /Add-Driver /Driver:C:\Drivers\mydriver.inf

# Aggiungere driver ricorsivamente
DISM /Online /Add-Driver /Driver:C:\Drivers\ /Recurse

# Rimuovere driver
DISM /Online /Remove-Driver /Driver:oem42.inf

# === OPERAZIONI OFFLINE (su immagine WIM) ===

# Montare immagine
DISM /Mount-Wim /WimFile:D:\Images\install.wim /Index:1 /MountDir:C:\Mount

# Aggiungere driver all'immagine
DISM /Image:C:\Mount /Add-Driver /Driver:C:\Drivers\ /Recurse
# Con /ForceUnsigned per driver non firmati (solo per test!)

# Elencare driver nell'immagine
DISM /Image:C:\Mount /Get-Drivers /Format:Table

# Rimuovere driver dall'immagine
DISM /Image:C:\Mount /Remove-Driver /Driver:oem42.inf

# Smontare e salvare
DISM /Unmount-Wim /MountDir:C:\Mount /Commit

# === POWERSHELL EQUIVALENTS ===

# Add driver online
Add-WindowsDriver -Online -Driver "C:\Drivers\" -Recurse

# Export drivers
Export-WindowsDriver -Online -Destination "C:\Backup\Drivers"

# Add driver to offline image
Add-WindowsDriver -Path "C:\Mount" -Driver "C:\Drivers\" -Recurse

# Get drivers
Get-WindowsDriver -Online
Get-WindowsDriver -Path "C:\Mount"
Get-WindowsDriver -Online -Driver "oem42.inf" -All
```

---

## Driver Signing e Integrità

```powershell
# Windows richiede driver firmati digitalmente (Kernel Mode Code Signing)
# I driver non firmati non possono essere caricati su Windows 64-bit

# ============================================================
# CATENA DI TRUST DEI DRIVER
# ============================================================
#
# Livello 1: WHQL (Windows Hardware Quality Labs)
#   → Microsoft testa e firma il driver
#   → Massima affidabilità e ranking
#   → Richiesto per distribuire via Windows Update
#   → Il vendor invia il driver a Microsoft HLK (Hardware Lab Kit)
#
# Livello 2: Attestation Signing
#   → Microsoft firma senza test HLK completo
#   → Per driver kernel-mode che non richiedono HLK
#   → Il vendor carica il pacchetto su Partner Center
#
# Livello 3: EV Certificate (Extended Validation)
#   → Il vendor firma con certificato EV
#   → Richiesto come prerequisito per l'attestation signing
#   → Non sufficiente da solo per kernel-mode su Win 10 1607+
#
# Livello 4: Standard Authenticode
#   → Firma con certificato code signing standard
#   → Accettato per UMDF (User Mode) driver
#   → NON accettato per KMDF su Windows 10 1607+

# Verificare firma driver
sigcheck -v C:\Windows\System32\drivers\driver.sys
# O con PowerShell:
Get-AuthenticodeSignature C:\Windows\System32\drivers\driver.sys

# Verificare tutte le firme dei driver caricati
Get-CimInstance Win32_SystemDriver | ForEach-Object {
    $path = $_.PathName -replace '\\SystemRoot','C:\Windows' -replace '\\\?\?\\',''
    if (Test-Path $path) {
        $sig = Get-AuthenticodeSignature $path
        [PSCustomObject]@{
            Driver  = $_.Name
            Status  = $sig.Status
            Signer  = $sig.SignerCertificate.Subject
            Expires = $sig.SignerCertificate.NotAfter
        }
    }
} | Where-Object Status -ne "Valid" | Format-Table -AutoSize

# Verificare integrità di tutti i driver
sfc /verifyonly    # Verifica senza riparare
sfc /scannow       # Verifica e ripara

# Verificare integrità componenti Windows
DISM /Online /Cleanup-Image /CheckHealth     # Check rapido
DISM /Online /Cleanup-Image /ScanHealth      # Scan approfondito
DISM /Online /Cleanup-Image /RestoreHealth   # Ripara componenti corrotti

# Secure Boot
# Verifica che il firmware e il boot loader siano firmati
# Impedisce il caricamento di bootkit e driver non firmati al boot
# Verificare: msinfo32 → Secure Boot State: On
Confirm-SecureBootUEFI   # $true = Secure Boot attivo

# Verificare stato Secure Boot e dettagli
$sb = Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\SecureBoot\State"
Write-Host "Secure Boot: $(if($sb.UEFISecureBootEnabled){'ON'}else{'OFF'})"

# Secure Boot policy — database chiavi
Get-SecureBootUEFI -Name PK    # Platform Key (una sola, del vendor HW)
Get-SecureBootUEFI -Name KEK   # Key Exchange Key
Get-SecureBootUEFI -Name db    # Authorized signature database
Get-SecureBootUEFI -Name dbx   # Forbidden signature database

# Impostare Secure Boot policy personalizzata (UEFI avanzato):
# Format-SecureBootUEFI / Set-SecureBootUEFI — usare con estrema cautela
```

### Catena di Integrità al Boot

```
┌─────────────────────────────────────────────────────────┐
│                SECURE BOOT CHAIN                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  UEFI Firmware                                           │
│  ├── Verifica Platform Key (PK)                          │
│  ├── Verifica bootloader (bootmgfw.efi)                  │
│  │   └── Firmato con chiave nel db                       │
│  ├── Verifica Windows Boot Manager                       │
│  │   └── Firmato Microsoft                               │
│  ├── Verifica winload.efi (OS loader)                    │
│  │   └── Firmato Microsoft                               │
│  ├── Verifica kernel (ntoskrnl.exe)                      │
│  │   └── Firmato Microsoft                               │
│  └── KERNEL MODE CODE INTEGRITY (CI)                     │
│      ├── Verifica ogni driver .sys al caricamento        │
│      ├── Verifica catalogo firma (.cat)                  │
│      ├── Se HVCI attivo → la verifica avviene in VTL1   │
│      └── Driver non firmato → BLOCCATO                   │
│                                                          │
│  Risultato: boot chain integra dal firmware al driver    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Cross-Signing — Deprecazione e Impatto

```powershell
# Il cross-signing permetteva ai vendor di firmare driver kernel-mode
# con un certificato rilasciato da una CA presente nella lista Microsoft
# di CA autorizzate per il cross-signing.
#
# TIMELINE DEPRECAZIONE:
#
# Pre-2015:   Cross-signing con qualsiasi CA nella lista Microsoft
#             (VeriSign, DigiCert, GlobalSign, Symantec, ecc.)
#
# 2015-2016:  Microsoft restringe le CA autorizzate
#
# 2016-07:    Windows 10 1607 (Anniversary Update)
#             → Nuovi driver kernel-mode DEVONO essere firmati
#               tramite Partner Center (WHQL o Attestation)
#             → I driver cross-signed precedenti continuano a funzionare
#             → Eccezione: driver per Windows Vista/7/8/8.1
#
# 2021:       Attori malevoli abusano di certificati cross-signed
#             scaduti/revocati per firmare rootkit
#
# 2023+:      Microsoft revoca certificati cross-signed compromessi
#             tramite aggiornamenti della lista dbx e klist.exe
#
# STATO ATTUALE:
# - I driver cross-signed esistenti continuano a caricarsi
#   (per backward compatibility)
# - Nessun NUOVO driver può essere cross-signed
# - Per nuovi driver kernel-mode: solo WHQL o Attestation via Partner Center
# - HVCI può bloccare anche driver cross-signed se non conformi
#
# IMPATTO PRATICO:
# Se un vendor hardware ha SOLO un driver cross-signed vecchio:
# 1. Verificare se funziona ancora (quasi sempre sì, a meno che il cert
#    non sia nella lista dbx)
# 2. Chiedere al vendor un driver firmato via Partner Center
# 3. Se il vendor non esiste più: valutare hardware alternativo

# Verificare se un driver usa un certificato cross-signed
$sig = Get-AuthenticodeSignature "C:\Windows\System32\drivers\legacy.sys"
$sig.SignerCertificate | Format-List Subject, Issuer, NotAfter, Thumbprint
# Se Issuer contiene "VeriSign", "Symantec", "DigiCert" e NotAfter < 2021
# → probabilmente cross-signed legacy
```

Rif.: *Windows Hardware Compatibility Program*, https://learn.microsoft.com/en-us/windows-hardware/drivers/dashboard/ (consultato: 2026-05-23)

---

## KMCS — Kernel-Mode Code Signing

```powershell
# KMCS (Kernel-Mode Code Signing) è la policy di Windows che impone
# la firma digitale per tutti i driver caricati nel kernel.
#
# ============================================================
# ENFORCEMENT RULES (Windows 10/11 64-bit)
# ============================================================
#
# 1. TUTTI i driver kernel-mode devono essere firmati
# 2. Secure Boot ON → enforcement rigoroso (solo firma nel db/dbx)
# 3. Secure Boot OFF → fallback ad Authenticode standard
# 4. HVCI ON → enforcement tramite hypervisor (VTL1)
#    impossibile bypassare anche con exploit kernel
# 5. Test Signing Mode → consente driver firmati con certificato di test
#    (SOLO per sviluppo, MAI in produzione)

# ============================================================
# BCDEDIT — OPZIONI PER FIRMA DRIVER
# ============================================================

# Visualizzare configurazione corrente
bcdedit /enum {current}

# Test Signing Mode (SOLO LAB / SVILUPPO)
bcdedit /set testsigning on
# → Mostra watermark "Test Mode" sul desktop
# → Accetta driver firmati con certificati di test
# → MAI usare in produzione: espone il kernel a driver arbitrari

# Disabilitare Test Signing (tornare alla normalità)
bcdedit /set testsigning off

# Disable Integrity Checks (ESTREMAMENTE PERICOLOSO)
bcdedit /set nointegritychecks on
# → Disabilita COMPLETAMENTE la verifica firma driver
# → Equivale a disattivare KMCS
# → Il sistema è vulnerabile a rootkit e driver malevoli
# → NON USARE MAI, nemmeno in lab (usare test signing invece)

# Verificare che i check siano attivi (stato normale)
bcdedit | Select-String "testsigning|nointegritychecks"
# Output atteso: entrambi non presenti o impostati a "No"

# ============================================================
# AUDIT: IDENTIFICARE DRIVER NON CONFORMI
# ============================================================

# Elencare tutti i driver kernel caricati e verificarne la firma
Get-CimInstance Win32_SystemDriver | Where-Object State -eq "Running" |
    ForEach-Object {
        $path = $_.PathName -replace '\\SystemRoot','C:\Windows' -replace '\\\?\?\\',''
        $sig = if (Test-Path $path) {
            Get-AuthenticodeSignature $path
        } else { $null }
        [PSCustomObject]@{
            Name        = $_.Name
            DisplayName = $_.DisplayName
            Path        = $path
            SignStatus  = if ($sig) { $sig.Status } else { 'FileNotFound' }
            SignType    = if ($sig -and $sig.SignerCertificate) {
                            if ($sig.SignerCertificate.Subject -match 'Microsoft') { 'Microsoft' }
                            elseif ($sig.IsOSBinary) { 'OS-Binary' }
                            else { 'Third-Party' }
                          } else { 'Unknown' }
        }
    } | Where-Object SignStatus -ne 'Valid' |
    Sort-Object SignStatus |
    Format-Table -AutoSize

# Event log per errori di firma
Get-WinEvent -LogName "Microsoft-Windows-CodeIntegrity/Operational" -MaxEvents 50 |
    Where-Object Id -in @(3033, 3034, 3035, 3089, 3090) |
    Select-Object TimeCreated, Id,
        @{N='Type';E={
            switch ($_.Id) {
                3033 { 'Unsigned driver blocked' }
                3034 { 'Unsigned driver audit' }
                3035 { 'Signing level not met' }
                3089 { 'HVCI incompatible (audit)' }
                3090 { 'HVCI incompatible (blocked)' }
            }
        }}, Message | Format-Table -Wrap
```

Rif.: *Kernel-Mode Code Signing Requirements*, https://learn.microsoft.com/en-us/windows-hardware/drivers/install/kernel-mode-code-signing-policy--windows-vista-and-later- (consultato: 2026-05-23)

---

## HVCI e Virtualization-Based Security

```powershell
# HVCI (Hypervisor-protected Code Integrity)
# Usa la virtualizzazione per proteggere il kernel
# I driver incompatibili con HVCI non possono essere caricati

# ============================================================
# VBS (Virtualization-Based Security) ARCHITECTURE
# ============================================================
#
# ┌──────────────────────────────────────────────────┐
# │              VTL 0 (Normal World)                 │
# │   Windows Kernel + Driver (ntoskrnl.exe)          │
# │   → Esegue codice kernel-mode                    │
# │   → Soggetto a exploit se compromesso             │
# ├──────────────────────────────────────────────────┤
# │              VTL 1 (Secure World)                 │
# │   Secure Kernel (securekernel.exe)                │
# │   HVCI Engine — verifica firma driver             │
# │   Credential Guard — protegge LSASS              │
# │   → Isolato dall'hypervisor                       │
# │   → VTL 0 non può accedere a VTL 1               │
# ├──────────────────────────────────────────────────┤
# │              HYPERVISOR (Hyper-V)                 │
# │   Gestisce VTL 0 e VTL 1                         │
# │   Impone isolamento memoria                      │
# └──────────────────────────────────────────────────┘

# Verificare stato VBS e HVCI
# msinfo32 → Virtualization-based security → Running
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
    Select-Object -Property AvailableSecurityProperties,
        CodeIntegrityPolicyEnforcementStatus,
        RequiredSecurityProperties,
        SecurityServicesConfigured,
        SecurityServicesRunning,
        VirtualizationBasedSecurityStatus

# Abilitare HVCI via PowerShell
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity" `
    -Name "Enabled" -Value 1 -Type DWord

# Abilitare HVCI via GPO:
# Computer → Administrative Templates → System → Device Guard
#   → Turn On Virtualization Based Security: Enabled
#   → Virtualization Based Protection of Code Integrity: Enabled with UEFI lock

# Requisiti hardware per VBS/HVCI:
# - CPU con virtualizzazione (Intel VT-x / AMD-V)
# - SLAT (Second Level Address Translation) — Intel EPT / AMD RVI
# - UEFI firmware con Secure Boot
# - TPM 2.0 (consigliato)
# - RAM: almeno 4 GB (8+ consigliati)

# Verificare compatibilità hardware per VBS
$info = Get-ComputerInfo
Write-Host "Hyper-V Requirements:"
Write-Host "  VM Monitor Extensions: $($info.HyperVisorPresent)"
Write-Host "  Firmware Type: $($info.BiosFirmwareType)"

# Verificare compatibilità driver con HVCI
# Microsoft fornisce la lista driver incompatibili:
# https://learn.microsoft.com/en-us/windows/security/hardware-security/...
#
# Driver incompatibili:
# - Usano esecuzione di codice non protetto (W+X pages)
# - Allocano memoria kernel eseguibile a runtime
# - Modificano code pages dopo il caricamento
# - Usano pool allocations non sicure

# Test di compatibilità HVCI di un driver:
# 1. Usare HLK (Hardware Lab Kit) con Code Integrity test
# 2. Usare Driver Verifier con HVCI checks
# 3. Verificare nell'Event Log dopo abilitazione HVCI
Get-WinEvent -LogName "Microsoft-Windows-CodeIntegrity/Operational" |
    Where-Object Id -in @(3089, 3090) |
    Select-Object TimeCreated, Message -First 20
# Event 3089: driver incompatibile con HVCI (audit)
# Event 3090: driver bloccato da HVCI (enforce)
```

---

## Driver Verifier — Guida Approfondita

```powershell
# Driver Verifier è lo strumento di Microsoft per trovare bug nei driver
# ATTENZIONE: può causare BSOD intenzionali quando rileva violazioni!
# Usare SOLO in ambienti di test o per diagnosticare BSOD ricorrenti

# ============================================================
# MODALITÀ OPERATIVE
# ============================================================

# Standard checks — set base di verifiche
verifier /standard /all                 # Tutti i driver
verifier /standard /driver mydriver.sys # Driver specifico

# Le verifiche standard includono:
# - Special Pool: rileva buffer overflow/underflow
# - Force IRQL Checking: rileva accesso a memoria paged a IRQL elevato
# - Pool Tracking: rileva memory leak
# - I/O Verification: verifica uso corretto delle IRP
# - Deadlock Detection: rileva potential deadlock
# - DMA Checking: verifica uso corretto DMA
# - Security Checks: verifica vulnerabilità
# - Miscellaneous Checks: altre verifiche

# Verifiche aggiuntive (abilitare selettivamente):
verifier /flags 0x209BB /driver mydriver.sys
# 0x00001 = Special Pool
# 0x00002 = Force IRQL Checking
# 0x00008 = Pool Tracking
# 0x00010 = I/O Verification
# 0x00020 = Deadlock Detection
# 0x00100 = DMA Verification
# 0x00800 = Miscellaneous Checks
# 0x20000 = DDI compliance checking (KMDF rules)
# Combinare con OR: 0x209BB = tutti i flag sopra

# Verifiche avanzate per HVCI compliance:
verifier /flags 0x02000000 /driver mydriver.sys
# 0x02000000 = Code Integrity Checks

# Impostazioni correnti
verifier /querysettings

# Statistiche runtime (senza reboot)
verifier /query

# Disabilitare Driver Verifier (richiede reboot)
verifier /reset

# GUI interattiva
verifier     # Senza parametri apre il wizard GUI

# ============================================================
# SCENARIO: DIAGNOSTICARE BSOD RICORRENTE
# ============================================================

# 1. Identificare il driver sospetto dal crash dump
# Analizzare il minidump con WinDbg:
# .sympath srv*C:\Symbols*https://msdl.microsoft.com/download/symbols
# .reload
# !analyze -v
# → Output indica il driver colpevole

# 2. Abilitare Driver Verifier sul driver sospetto
verifier /standard /driver sospetto.sys

# 3. Riavviare e aspettare il crash
# Se il driver ha un bug, il BSOD sarà IMMEDIATO e con informazioni dettagliate

# 4. Analizzare il nuovo crash dump
# Il bug check code sarà specifico del tipo di violazione

# 5. Dopo la diagnosi, DISABILITARE Driver Verifier
verifier /reset
# Se il sistema non si avvia:
# Boot in Safe Mode → verifier /reset → reboot

# ============================================================
# DRIVER VERIFIER IN SAFE MODE
# ============================================================
# Se Driver Verifier causa BSOD al boot:
# 1. Premere F8 o Shift+click su Restart → Advanced Options
# 2. Avviare in Safe Mode
# 3. Aprire cmd come admin: verifier /reset
# 4. Riavviare normalmente
```

### Configurazione Driver Verifier via GPO

```powershell
# Per abilitare Driver Verifier su macchine di test via policy:
# Non esiste una GPO nativa, ma si può usare uno script startup

# Script startup GPO per abilitare Driver Verifier:
# Computer → Windows Settings → Scripts → Startup
$script = @'
@echo off
verifier /standard /driver thirdparty1.sys thirdparty2.sys
'@
# Nota: il reboot successivo attiverà le verifiche

# Monitorare i risultati centralmente:
# Event Log → System → Source: "Verifier"
# Inoltrare via Windows Event Forwarding (WEF)
```

---

## Driver di Stampa — v3, v4 e Universal Print

### Evoluzione dei driver di stampa

```
┌──────────────────────────────────────────────────────────────┐
│              EVOLUZIONE DRIVER DI STAMPA WINDOWS             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  v2 (Legacy)     Windows 2000/XP                             │
│    ↓               → Kernel-mode, spesso causa di BSOD      │
│    ↓               → Ogni stampante = driver diverso         │
│                                                              │
│  v3 (Tradizionale) Windows Vista+                            │
│    ↓               → User-mode, più stabile                  │
│    ↓               → Ancora modello un-driver-per-stampante  │
│    ↓               → Supporto XPS e GDI rendering           │
│                                                              │
│  v4 (Moderno)    Windows 8+                                  │
│    ↓               → Modello universale (un driver, molte    │
│    ↓                 stampanti)                               │
│    ↓               → Print Class Driver + GPD/PPD            │
│    ↓               → Nessun setup richiesto dall'utente      │
│                                                              │
│  Universal Print  Windows 10 2004+                           │
│                   → Servizio cloud (Azure AD)                │
│                   → Zero driver sul client                   │
│                   → Gestione centralizzata da Intune/Portal  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### v3 vs v4 — Confronto tecnico

```powershell
# ┌────────────────────┬───────────────────────┬───────────────────────┐
# │ ASPETTO            │ v3                    │ v4                    │
# ├────────────────────┼───────────────────────┼───────────────────────┤
# │ Esecuzione         │ User-mode (spoolsv)   │ User-mode (isolato)   │
# │ Isolamento         │ Condivide processo     │ Processo separato per │
# │                    │ spooler                │ ogni driver           │
# │ Rendering          │ GDI o XPS             │ Solo XPS (XPSDrv)     │
# │ File richiesti     │ DLL + INF + PPD/GPD   │ INF + GPD/PPD + JS    │
# │ Setup utente       │ Richiesto (wizard)     │ Automatico (PnP)      │
# │ Point and Print    │ Scarica driver dal     │ Driver classe locale  │
# │                    │ server (rischio sec.)  │ (nessun download)     │
# │ ARM64              │ Non supportato         │ Supportato            │
# │ Enhanced P&P sec.  │ N/A                    │ Default sicuro        │
# │ Manutenzione       │ Un driver per modello  │ Un driver per classe  │
# └────────────────────┴───────────────────────┴───────────────────────┘

# Elencare driver stampante installati e la loro versione
Get-PrinterDriver | Select-Object Name, MajorVersion,
    @{N='DriverVersion';E={
        switch ($_.MajorVersion) {
            3 { 'v3 (legacy)' }
            4 { 'v4 (modern)' }
            default { "v$($_.MajorVersion)" }
        }
    }}, Manufacturer, PrinterEnvironment |
    Format-Table -AutoSize

# Elencare stampanti con dettagli driver
Get-Printer | ForEach-Object {
    $drv = Get-PrinterDriver -Name $_.DriverName -ErrorAction SilentlyContinue
    [PSCustomObject]@{
        PrinterName = $_.Name
        DriverName  = $_.DriverName
        DriverVer   = if ($drv) { "v$($drv.MajorVersion)" } else { 'N/A' }
        PortName    = $_.PortName
        Shared      = $_.Shared
    }
} | Format-Table -AutoSize
```

### PrintNightmare e sicurezza Point and Print

```powershell
# CVE-2021-34527 (PrintNightmare) — vulnerabilità critica nei driver v3
# Un utente non privilegiato poteva caricare un driver stampante malevolo
# tramite Point and Print e ottenere esecuzione codice SYSTEM.
#
# IMPATTO: Remote Code Execution + Local Privilege Escalation
# CVSS: 8.8 (High)
# CWE: CWE-269 (Improper Privilege Management)
#
# MITIGAZIONI (tutte da applicare):
#
# 1. Patch KB5005010+ (installare aggiornamenti cumulativi recenti)
#
# 2. GPO: Restrict Point and Print
#    Computer → Administrative Templates → Printers →
#    Package Point and print - Approved servers:
#    → Enabled, con lista server di stampa approvati
#
# 3. GPO: Impedire installazione driver stampante non approvati
#    Point and Print Restrictions:
#    → "When installing drivers for a new connection":
#       Show warning and elevation prompt
#    → "When updating drivers for an existing connection":
#       Show warning and elevation prompt
#
# 4. Registry hardening (post-patch):
Set-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Printers\PointAndPrint" `
    -Name "RestrictDriverInstallationToAdministrators" -Value 1 -Type DWord
# → Solo admin possono installare driver stampante via Point and Print

# 5. Printer Isolation (v3 driver)
# Isola ogni driver stampante in un processo separato
# Impedisce che un driver compromesso acceda allo spooler
# GPO: Computer → Printers → Execute print drivers in isolated processes: Enabled

# Verificare se PrintNightmare è mitigato
$regPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Printers\PointAndPrint"
if (Test-Path $regPath) {
    $val = (Get-ItemProperty $regPath -ErrorAction SilentlyContinue).RestrictDriverInstallationToAdministrators
    Write-Host "RestrictDriverInstallation: $(if($val -eq 1){'MITIGATO'}else{'VULNERABILE'})"
} else {
    Write-Host "Chiave non presente — verificare patch e GPO"
}
```

### Universal Print

```powershell
# Universal Print è un servizio cloud Microsoft 365 che elimina
# la necessità di driver di stampa e print server on-premises.
#
# ARCHITETTURA:
# Client → Azure AD auth → Universal Print cloud → Connector → Stampante
#
# VANTAGGI:
# - Zero driver sul client (usa il rendering IPP nativo di Windows)
# - Nessun print server on-premises (il connector è leggero)
# - Gestione centralizzata da Microsoft Entra admin center
# - Integrazione con Intune per assegnazione stampanti
# - Supporto Conditional Access (stampa solo da dispositivi compliant)
#
# REQUISITI:
# - Licenza Microsoft 365 E3/E5 o Universal Print standalone
# - Windows 10 1903+ o Windows 11
# - Azure AD Join o Hybrid Azure AD Join
# - Universal Print Connector su un server on-prem (per stampanti non-cloud)
#
# LIMITAZIONI:
# - Nessun supporto per stampanti con driver proprietari obbligatori
# - Latenza dipende dalla connessione cloud
# - Non sostituisce completamente i print server per workflow di stampa
#   complessi (pull printing, accounting avanzato)

# Verificare stampanti Universal Print assegnate
Get-Printer | Where-Object { $_.PortName -like "*universalprint*" }
```

Rif.: *Universal Print documentation*, https://learn.microsoft.com/en-us/universal-print/ (consultato: 2026-05-23)

Rif.: *CVE-2021-34527 — PrintNightmare*, https://msrc.microsoft.com/update-guide/vulnerability/CVE-2021-34527 (consultato: 2026-05-23)

---

## Driver GPU e Display — WDDM e GPU Partitioning

### WDDM (Windows Display Driver Model) — Versioni

```
┌──────────────────────────────────────────────────────────────┐
│                    VERSIONI WDDM                             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  WDDM 1.0   Windows Vista         DirectX 9/10              │
│  WDDM 1.1   Windows 7             DirectX 11, DXGI 1.1      │
│  WDDM 1.2   Windows 8             DirectX 11.1, preemption  │
│  WDDM 1.3   Windows 8.1           DirectX 11.2, tiled res.  │
│  WDDM 2.0   Windows 10 (1507)     DirectX 12, virtual mem   │
│  WDDM 2.1   Windows 10 (1607)     Shader Model 6.0          │
│  WDDM 2.2   Windows 10 (1703)     Shader Model 6.1          │
│  WDDM 2.3   Windows 10 (1709)     Shader Model 6.2          │
│  WDDM 2.4   Windows 10 (1803)     Shader Model 6.3, raytr.  │
│  WDDM 2.5   Windows 10 (1903)     Shader Model 6.4          │
│  WDDM 2.6   Windows 10 (1909)     Shader Model 6.5, VRS     │
│  WDDM 2.7   Windows 10 (2004)     Shader Model 6.6, meshsh. │
│  WDDM 2.9   Windows 10 (21H1)     Shader Model 6.6          │
│  WDDM 3.0   Windows 11 (21H2)     Shader Model 6.7          │
│  WDDM 3.1   Windows 11 (22H2)     Shader Model 6.8          │
│  WDDM 3.2   Windows 11 (24H2)     Shader Model 6.9          │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

```powershell
# Verificare versione WDDM del driver GPU
# Metodo 1: dxdiag
# Start → dxdiag → tab Display → Driver Model

# Metodo 2: Registry
$displayKey = Get-ChildItem "HKLM:\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}" -ErrorAction SilentlyContinue
foreach ($key in $displayKey) {
    $props = Get-ItemProperty $key.PSPath -ErrorAction SilentlyContinue
    if ($props.DriverDesc) {
        Write-Host "GPU: $($props.DriverDesc)"
        Write-Host "  Driver Version: $($props.DriverVersion)"
        Write-Host "  WDDM: verificare via dxdiag o DxCapsViewer"
    }
}

# Metodo 3: PowerShell — dettagli GPU
Get-CimInstance Win32_VideoController |
    Select-Object Name, DriverVersion, DriverDate,
        AdapterRAM, VideoModeDescription, Status |
    Format-List
```

### GPU Partitioning (GPU-P e GPU-PV) per Hyper-V

```powershell
# GPU-P (GPU Partitioning) — divide la GPU fisica tra VM
# GPU-PV (GPU Paravirtualization) — accesso GPU virtualizzato
#
# ┌─────────────────────────────────────────────────────────┐
# │ HOST                                                     │
# │ ┌───────────────────────────────────────────────────┐    │
# │ │ GPU FISICA (es. NVIDIA A100, Intel Xe)            │    │
# │ │                                                    │    │
# │ │ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │    │
# │ │ │ Partiz. │ │ Partiz. │ │ Partiz. │ │ Partiz. │ │    │
# │ │ │  Host   │ │  VM 1   │ │  VM 2   │ │  VM 3   │ │    │
# │ │ └─────────┘ └─────────┘ └─────────┘ └─────────┘ │    │
# │ └───────────────────────────────────────────────────┘    │
# │                                                          │
# │ Ogni VM vede una GPU virtuale con VRAM dedicata          │
# │ Windows Sandbox e WSL2 usano GPU-PV internamente         │
# └──────────────────────────────────────────────────────────┘
#
# REQUISITI GPU-P:
# - Windows 10 2004+ / Windows 11 come host
# - GPU compatibile con GPU-P (Intel Gen 9.5+, NVIDIA con GRID/vGPU)
# - Driver GPU host con supporto WDDM 2.5+
# - Hyper-V abilitato
#
# CASI D'USO:
# - Desktop virtuali con accelerazione GPU (VDI)
# - Machine learning / inferenza AI in VM
# - CAD / rendering in VM

# Verificare supporto GPU-P sulla GPU del host
$gpu = Get-CimInstance Win32_VideoController
Write-Host "GPU: $($gpu.Name)"
# Il supporto GPU-P dipende dal driver — verificare nella documentazione
# del vendor GPU (NVIDIA GRID vGPU Manager, Intel GPU-P support matrix)

# Assegnare una partizione GPU a una VM Hyper-V
$vmName = "VM-GPU-Test"
$gpuPath = (Get-VMHostPartitionableGpu).Name
Set-VMGpuPartitionAdapter -VMName $vmName
Add-VMGpuPartitionAdapter -VMName $vmName -MinPartitionVRAM 1073741824  # 1 GB min
# Nota: richiede copia dei driver GPU nella VM (non installati automaticamente)
```

Rif.: *WDDM architecture*, https://learn.microsoft.com/en-us/windows-hardware/drivers/display/windows-vista-display-driver-model-design-guide (consultato: 2026-05-23)

Rif.: *GPU Partitioning*, https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/gpu-partitioning (consultato: 2026-05-23)

---

## Driver Storage — Storport, SCSI Port e NVMe

### Architettura Storage Driver Stack

```
┌──────────────────────────────────────────────────────────────┐
│                  STORAGE DRIVER STACK                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  APPLICAZIONE                                                │
│       ↓ (I/O Request)                                        │
│  FILE SYSTEM DRIVER (NTFS, ReFS)                             │
│       ↓                                                      │
│  VOLUME MANAGER (volmgr.sys, volsnap.sys)                    │
│       ↓                                                      │
│  DISK CLASS DRIVER (disk.sys)                                │
│       ↓                                                      │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  PORT DRIVER (fornito da Microsoft)                  │     │
│  │                                                      │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │     │
│  │  │  Storport.sys │  │ SCSIport.sys │  │ stornvme   │ │     │
│  │  │  (moderno)    │  │  (legacy)    │  │  (NVMe)    │ │     │
│  │  └──────────────┘  └──────────────┘  └────────────┘ │     │
│  └─────────────────────────────────────────────────────┘     │
│       ↓                                                      │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  MINIPORT DRIVER (fornito dal vendor HW)             │     │
│  │  → Comunica direttamente con il controller HBA       │     │
│  │  → Intel RST, LSI MegaRAID, Broadcom, Marvell        │     │
│  └─────────────────────────────────────────────────────┘     │
│       ↓                                                      │
│  HARDWARE (HBA, RAID controller, NVMe SSD, SATA)            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Storport vs SCSI Port

```powershell
# ┌───────────────────┬─────────────────────┬─────────────────────┐
# │ CARATTERISTICA    │ Storport            │ SCSI Port (legacy)  │
# ├───────────────────┼─────────────────────┼─────────────────────┤
# │ Introdotto in     │ Windows Server 2003 │ Windows NT 4.0      │
# │ I/O Model         │ Full-duplex, async  │ Half-duplex, sync   │
# │ Queue depth       │ 254 per LUN         │ 1 per LUN           │
# │ MSI/MSI-X         │ Supportato          │ Non supportato      │
# │ DMA              │ 64-bit scatter/gath. │ Limitato            │
# │ Performance       │ Ottimizzato per SSD │ Progettato per HDD  │
# │ Hot-plug          │ Supportato nativo   │ Limitato            │
# │ NVMe             │ Supportato (stornvme)│ Non supportato      │
# │ Stato             │ Attivo, consigliato │ Deprecato           │
# └───────────────────┴─────────────────────┴─────────────────────┘

# Identificare quale port driver usa un disco
Get-Disk | ForEach-Object {
    $disk = $_
    $pnp = Get-PnpDevice | Where-Object {
        $_.InstanceId -like "*DISK*" -and $_.FriendlyName -eq $disk.FriendlyName
    }
    [PSCustomObject]@{
        DiskNumber = $disk.Number
        Model      = $disk.Model
        BusType    = $disk.BusType
        MediaType  = $disk.MediaType
        Size_GB    = [math]::Round($disk.Size / 1GB, 2)
        PartStyle  = $disk.PartitionStyle
    }
} | Format-Table -AutoSize

# NVMe driver stack — verificare il driver in uso
Get-PnpDevice -Class SCSIAdapter |
    Select-Object FriendlyName, InstanceId,
        @{N='Driver';E={
            (Get-PnpDeviceProperty -InstanceId $_.InstanceId |
             Where-Object KeyName -eq 'DEVPKEY_Device_DriverInfPath').Data
        }} | Format-Table -AutoSize
# Il driver NVMe inbox di Windows (stornvme.sys) è sufficiente per la
# maggior parte degli SSD NVMe. I driver vendor (Samsung NVMe, Intel RST)
# possono offrire performance aggiuntive o funzionalità specifiche.
```

Rif.: *Storport driver*, https://learn.microsoft.com/en-us/windows-hardware/drivers/storage/storport-driver (consultato: 2026-05-23)

---

## Driver di Rete — NDIS, NetAdapterCx e SR-IOV

### NDIS — Evoluzione

```powershell
# NDIS (Network Driver Interface Specification) è il framework per
# i driver di rete su Windows. Ogni versione aggiunge funzionalità:
#
# NDIS 5.x   Windows XP / Server 2003
#             → Modello monolitico
# NDIS 6.0   Windows Vista / Server 2008
#             → Filter drivers, send/receive scaling
# NDIS 6.20  Windows 7 / Server 2008 R2
#             → RSS (Receive Side Scaling), VMQ
# NDIS 6.30  Windows 8 / Server 2012
#             → SR-IOV, QoS, PacketDirect
# NDIS 6.40  Windows 8.1 / Server 2012 R2
#             → GFT (Generic Flow Tables)
# NDIS 6.50  Windows 10 (1507)
#             → NetAdapterCx preview
# NDIS 6.80  Windows 10 (1709) / Server 2019
#             → RSS v2, NetAdapterCx GA
# NDIS 6.83  Windows 10 (1903)
#             → Miglioramenti prestazioni
# NDIS 6.84  Windows 10 (2004) / Server 2022
#             → Miglioramenti RSS, timestamping
# NDIS 6.86  Windows 11 / Server 2025
#             → Ulteriori ottimizzazioni

# Verificare versione NDIS di un driver di rete
Get-NetAdapter | ForEach-Object {
    $name = $_.Name
    $driver = Get-NetAdapterAdvancedProperty -Name $name -ErrorAction SilentlyContinue
    [PSCustomObject]@{
        Name          = $name
        InterfaceDesc = $_.InterfaceDescription
        LinkSpeed     = $_.LinkSpeed
        Status        = $_.Status
        DriverVersion = $_.DriverVersion
        NdisVersion   = $_.NdisVersion
    }
} | Format-Table -AutoSize
```

### NetAdapterCx — Il futuro dei driver di rete

```powershell
# NetAdapterCx è il nuovo framework WDF per driver di rete.
# Sostituisce il modello NDIS miniport tradizionale con un modello
# basato su WDF (KMDF), semplificando notevolmente lo sviluppo.
#
# VANTAGGI:
# - Basato su KMDF → meno boilerplate, meno bug
# - Power management automatico
# - Buffer management semplificato (net rings)
# - Integrazione con Driver Verifier
# - Compatibilità futura garantita
#
# STRUTTURA:
# ┌────────────────────────────────────────┐
# │ NetAdapterCx Framework                 │
# │ ├── Gestione ciclo di vita adapter     │
# │ ├── Net ring buffer per Tx/Rx          │
# │ ├── OID handling semplificato          │
# │ └── Power management integrato         │
# │          ↓                             │
# │ NetAdapter Client Driver (vendor)      │
# │          ↓                             │
# │ WDF / KMDF Framework                   │
# └────────────────────────────────────────┘
```

### RSS, VMQ e SR-IOV — Offloading per Virtualizzazione

```powershell
# RSS (Receive Side Scaling)
# Distribuisce il processing dei pacchetti in ingresso su più CPU
# Essenziale per NIC 10/25/100 Gbps
Get-NetAdapterRss | Select-Object Name, Enabled, NumberOfReceiveQueues,
    Profile, BaseProcessorNumber

# VMQ (Virtual Machine Queue)
# Assegna code hardware dedicate alle VM Hyper-V
# Ogni VM riceve i pacchetti sulla propria coda, bypassando il host
Get-NetAdapterVmq | Select-Object Name, Enabled, MaxProcessors,
    NumberOfReceiveQueues

# SR-IOV (Single Root I/O Virtualization)
# La NIC espone Virtual Functions (VF) direttamente alle VM
# Le VM accedono alla NIC senza passare dal virtual switch Hyper-V
# Performance quasi native, riduzione carico CPU host
#
# REQUISITI SR-IOV:
# - NIC con supporto SR-IOV (Intel X710, Mellanox ConnectX-5, ecc.)
# - CPU con IOMMU (Intel VT-d / AMD-Vi)
# - BIOS/UEFI: SR-IOV e VT-d abilitati
# - Hyper-V virtual switch con SR-IOV abilitato
# - Driver NIC compatibile SR-IOV nel host E nella VM

Get-NetAdapterSriov | Select-Object Name, Enabled,
    NumVFs, SriovSupport

# Abilitare SR-IOV su un virtual switch Hyper-V
# New-VMSwitch -Name "SriovSwitch" -NetAdapterName "Ethernet" -EnableIov $true

# Verificare che SR-IOV sia attivo per una VM
# Get-VMNetworkAdapter -VMName "VM01" | Select-Object Name, IovWeight, SriovSupport
```

Rif.: *NDIS drivers*, https://learn.microsoft.com/en-us/windows-hardware/drivers/network/ndis-drivers (consultato: 2026-05-23)

Rif.: *SR-IOV*, https://learn.microsoft.com/en-us/windows-hardware/drivers/network/single-root-i-o-virtualization--sr-iov- (consultato: 2026-05-23)

---

## Driver USB — Stack, USBX, Type-C e Audio Class

### USB Driver Stack — Architettura

```
┌──────────────────────────────────────────────────────────────┐
│                   USB DRIVER STACK                            │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  APPLICAZIONE / CLASS DRIVER                                 │
│       ↓                                                      │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  USB Function Drivers (per classe)                    │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐  │    │
│  │  │ HID      │ │ Storage  │ │ Audio    │ │ Video  │  │    │
│  │  │(hidusb)  │ │(USBSTOR) │ │(usbaudio)│ │(usbvid)│  │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────┘  │    │
│  └──────────────────────────────────────────────────────┘    │
│       ↓                                                      │
│  USB CORE STACK                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │  URB Layer (USB Request Block)                        │    │
│  │       ↓                                              │    │
│  │  USB Hub Driver (usbhub.sys / usbhub3.sys)           │    │
│  │       ↓                                              │    │
│  │  Host Controller Driver:                              │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐             │    │
│  │  │ XHCI     │ │ EHCI     │ │ UHCI/OHCI│             │    │
│  │  │(usbxhci) │ │(usbehci) │ │(legacy)  │             │    │
│  │  │USB 3.x   │ │USB 2.0   │ │USB 1.x   │             │    │
│  │  └──────────┘ └──────────┘ └──────────┘             │    │
│  └──────────────────────────────────────────────────────┘    │
│       ↓                                                      │
│  HARDWARE (USB Host Controller)                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### USB Type-C e UCM (USB Connector Manager)

```powershell
# USB Type-C introduce complessità aggiuntiva rispetto a USB-A/B:
# - Reversibilità connettore (orientation detection)
# - Power Delivery (PD) fino a 240W
# - Alternate Mode (DisplayPort, Thunderbolt, HDMI via Type-C)
# - USB4 (basato su Thunderbolt 3)
#
# Il driver stack per Type-C include:
# - UCM (USB Connector Manager): gestisce il connettore fisico
# - UcmTcpciCx: driver per controller PD (TCPC)
# - UcmCx: client driver per la policy di ruolo (DFP/UFP/DRP)
# - UcmUcsiCx: UCSI (USB Type-C Connector System Interface)
#   protocollo standard per il firmware del connettore
#
# Il driver UCSI viene fornito dal vendor della piattaforma (Intel, AMD)
# e gestisce la negoziazione PD e la selezione dell'alternate mode.

# Verificare controller USB presenti
Get-PnpDevice -Class USB | Select-Object FriendlyName, Status,
    @{N='Type';E={
        if ($_.FriendlyName -match 'xHCI|USB 3') { 'USB 3.x (xHCI)' }
        elseif ($_.FriendlyName -match 'EHCI|USB 2') { 'USB 2.0 (EHCI)' }
        elseif ($_.FriendlyName -match 'Type-C|UCSI') { 'Type-C Controller' }
        else { 'Other' }
    }} | Sort-Object Type | Format-Table -AutoSize

# Elencare dispositivi USB connessi con dettagli
Get-PnpDevice -Class USB -Status OK |
    Select-Object FriendlyName, InstanceId,
        @{N='VID_PID';E={
            if ($_.InstanceId -match 'VID_([0-9A-F]{4})&PID_([0-9A-F]{4})') {
                "VID=$($Matches[1]) PID=$($Matches[2])"
            } else { 'N/A' }
        }} | Format-Table -AutoSize
```

### USB Audio Class Driver

```powershell
# Windows include un driver USB Audio Class (UAC) inbox:
# - UAC 1.0: usbaudio.sys (supporto base, 16/24-bit, fino a 96 kHz)
# - UAC 2.0: usbaudio2.sys (Windows 10 1703+, supporto high-res,
#             fino a 32-bit/384 kHz, feedback endpoints)
# - UAC 3.0: supporto parziale in Windows 11
#
# La maggior parte delle interfacce audio USB professionali
# (Focusrite, RME, MOTU, ecc.) usa il driver UAC class di Windows
# o un driver ASIO proprietario per latenza ridotta.
#
# PROBLEMI COMUNI:
# - Glitch audio (buffer underrun): aumentare buffer size nel DAW
# - Dispositivo non riconosciuto: verificare UAC version supportata
# - Latenza elevata: usare driver ASIO del vendor (non WDM/MME)

# Verificare dispositivi audio USB
Get-PnpDevice -Class AudioEndpoint |
    Where-Object { $_.InstanceId -like "*USB*" } |
    Select-Object FriendlyName, Status, InstanceId
```

Rif.: *USB driver stack*, https://learn.microsoft.com/en-us/windows-hardware/drivers/usbcon/ (consultato: 2026-05-23)

Rif.: *USB Type-C connector driver*, https://learn.microsoft.com/en-us/windows-hardware/drivers/usbcon/developing-windows-drivers-for-usb-type-c-connectors (consultato: 2026-05-23)

---

## Compatibilità Applicazioni

### Application Compatibility Toolkit

```powershell
# Problemi di compatibilità comuni:
# - App richiede versione OS precedente
# - App richiede permessi admin non necessari
# - App scrive in directory protette (Program Files, Windows)
# - App usa API deprecate

# Compatibility Mode (per singola app)
# Tasto destro → Properties → Compatibility
# - Run in compatibility mode for: Windows 7/8/10
# - Run as administrator
# - Disable display scaling on high DPI
# - Reduced color mode

# Compatibility Mode via Registry
Set-ItemProperty "HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" `
    -Name "C:\Program Files\OldApp\app.exe" -Value "WINXPSP3 RUNASADMIN"

# Valori comuni:
# WINXPSP3, WIN7RTM, WIN8RTM, WIN10RTM — Compatibility mode
# RUNASADMIN — Esegui come admin
# HIGHDPIAWARE — DPI awareness
# DISABLEDXMAXIMIZEDWINDOWEDMODE — Disable fullscreen optimization

# Application Compatibility Toolkit (ACT)
# Parte di Windows ADK
# Permette di creare fix personalizzati (shim) per applicazioni incompatibili
# Database di compatibilità: sdb file distribuibili via GPO
```

---

## API Sets, SxS Assemblies e DLL Search Order

### API Sets — Astrazione delle DLL di sistema

```powershell
# Gli API Sets sono un meccanismo di virtualizzazione delle DLL introdotto
# in Windows 7 e ampliato significativamente da Windows 10.
#
# Invece di chiamare direttamente kernel32.dll o user32.dll,
# le applicazioni moderne usano "api-ms-win-*" contract DLL.
# Il loader di Windows risolve questi contratti alla DLL reale al runtime.
#
# ESEMPIO:
# api-ms-win-core-file-l1-1-0.dll → risolve a kernelbase.dll
# api-ms-win-core-memory-l1-1-0.dll → risolve a kernelbase.dll
# api-ms-win-core-synch-l1-1-0.dll → risolve a kernelbase.dll
#
# VANTAGGI:
# - Microsoft può ristrutturare le DLL interne senza rompere le app
# - Le app che usano API sets sono portabili tra edizioni Windows
#   (Desktop, Server Core, IoT, HoloLens)
# - Facilita il supporto di piattaforme diverse (x64, ARM64)
#
# SCHEMA DI MAPPING:
# L'elenco completo è in: C:\Windows\System32\apisetschema.dll
# (embedded come risorsa, leggibile con strumenti come ApiSetView)

# Elencare gli API set resolution di un processo
# (richiede tool esterno come ApiSetView o Dependencies)
# Oppure verificare se una DLL è un API set:
$dll = "api-ms-win-core-file-l1-1-0.dll"
$path = [System.IO.Path]::Combine($env:SystemRoot, "System32", $dll)
if (Test-Path $path) {
    Write-Host "$dll esiste come file fisico (forward DLL)"
} else {
    Write-Host "$dll è un API set virtuale (risolto dal loader)"
}
```

### SxS — Side-by-Side Assemblies

```powershell
# Il sistema SxS (Side-by-Side, WinSxS) permette a più versioni
# della stessa DLL di coesistere sullo stesso sistema.
#
# DIRECTORY: C:\Windows\WinSxS\
# Contiene TUTTE le versioni di componenti Windows e shared assemblies.
# Può occupare diversi GB — NON eliminare manualmente i file!
#
# COME FUNZIONA:
# 1. Un'applicazione dichiara le dipendenze nel suo MANIFEST (.manifest o
#    embedded nel PE come risorsa RT_MANIFEST)
# 2. Il loader SxS cerca la versione esatta nel WinSxS store
# 3. L'applicazione ottiene la versione specifica richiesta
# 4. Altre applicazioni possono usare versioni diverse dello stesso assembly
#
# ESEMPIO MANIFEST applicazione:
# <dependency>
#   <dependentAssembly>
#     <assemblyIdentity type="win32" name="Microsoft.VC90.CRT"
#       version="9.0.21022.8" processorArchitecture="amd64"
#       publicKeyToken="1fc8b3b9a1e18e3b" />
#   </dependentAssembly>
# </dependency>
#
# Questo manifest richiede ESATTAMENTE la versione 9.0.21022.8 del
# Visual C++ 2008 Runtime. Se non presente → errore side-by-side.

# Verificare manifest di un eseguibile
# (il manifest è embedded come risorsa o come file .exe.manifest esterno)
# Tool: mt.exe (dal Windows SDK)
# mt.exe -inputresource:app.exe -out:manifest.xml

# Elencare assembly nel WinSxS store
Get-ChildItem "C:\Windows\WinSxS" -Directory |
    Where-Object Name -like "*vc*crt*" |
    Select-Object Name | Sort-Object Name

# Dimensione WinSxS (dimensione reale vs. apparente — molti hardlink!)
$winsxs = "C:\Windows\WinSxS"
$apparent = (Get-ChildItem $winsxs -Recurse -File -ErrorAction SilentlyContinue |
    Measure-Object Length -Sum).Sum / 1GB
Write-Host "WinSxS dimensione apparente: $([math]::Round($apparent, 2)) GB"
Write-Host "Nota: la dimensione reale è molto inferiore grazie agli hardlink"

# Pulizia WinSxS (sicura, tramite DISM)
# DISM /Online /Cleanup-Image /StartComponentCleanup
# DISM /Online /Cleanup-Image /StartComponentCleanup /ResetBase
# /ResetBase rimuove tutte le versioni superate dei componenti
# (impedisce il rollback degli aggiornamenti installati)
```

### DLL Search Order

```powershell
# L'ordine di ricerca delle DLL è CRITICO per la sicurezza.
# Un ordine errato può portare a DLL hijacking / DLL preloading attacks.
#
# ORDINE DI RICERCA STANDARD (SafeDllSearchMode ON — default):
#
# 1. Directory dell'applicazione (dove risiede l'EXE)
# 2. C:\Windows\System32 (o SysWOW64 per processi 32-bit)
# 3. C:\Windows\System (16-bit legacy)
# 4. C:\Windows
# 5. Directory di lavoro corrente (CWD)
# 6. Directories nella variabile PATH
#
# ORDINE CON SafeDllSearchMode OFF (insicuro):
# 1. Directory dell'applicazione
# 2. Directory di lavoro corrente (CWD) ← PERICOLOSO
# 3. System32
# 4. Windows
# 5. PATH
#
# MITIGAZIONI DLL HIJACKING:
# 1. SafeDllSearchMode: ON (default, non disabilitare)
# 2. SetDllDirectory(""): rimuove CWD dall'ordine di ricerca
# 3. LoadLibraryEx con LOAD_LIBRARY_SEARCH_SYSTEM32:
#    forza il caricamento solo da System32
# 4. Manifest con <file> element per DLL dependencies
# 5. App Manifest: requestedExecutionLevel per prevenire
#    il caricamento da directory writable dall'utente

# Verificare SafeDllSearchMode
$val = (Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager" `
    -Name "SafeDllSearchMode" -ErrorAction SilentlyContinue).SafeDllSearchMode
Write-Host "SafeDllSearchMode: $(if($val -eq 0){'OFF (insicuro!)'}else{'ON (default)'})"

# Verificare la variabile PATH per directory sospette
$env:PATH -split ';' | ForEach-Object {
    $dir = $_
    $acl = Get-Acl $dir -ErrorAction SilentlyContinue
    $writable = $acl.Access | Where-Object {
        $_.IdentityReference -match 'Users|Everyone|Authenticated' -and
        $_.FileSystemRights -match 'Write|FullControl|Modify'
    }
    if ($writable) {
        Write-Warning "PATH directory scrivibile da utenti: $dir"
    }
} 2>$null
```

### Manifest Files — Struttura e Uso

```powershell
# I file manifest (.manifest o embedded) dichiarano:
# - Identità dell'assembly (nome, versione, architettura)
# - Dipendenze da altri assembly (SxS)
# - Livello di esecuzione richiesto (UAC)
# - Compatibilità con versioni Windows
# - DPI awareness
#
# ESEMPIO MANIFEST COMPLETO:
#
# <?xml version="1.0" encoding="UTF-8"?>
# <assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
#   <assemblyIdentity version="1.0.0.0" name="MyApp" type="win32"/>
#
#   <!-- UAC Execution Level -->
#   <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
#     <security>
#       <requestedPrivileges>
#         <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
#       </requestedPrivileges>
#     </security>
#   </trustInfo>
#
#   <!-- OS Compatibility -->
#   <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
#     <application>
#       <supportedOS Id="{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}"/> <!-- Win 10/11 -->
#       <supportedOS Id="{1f676c76-80e1-4239-95bb-83d0f6d0da78}"/> <!-- Win 8.1 -->
#       <supportedOS Id="{4a2f28e3-53b9-4441-ba9c-d69d4a4a6e38}"/> <!-- Win 8 -->
#       <supportedOS Id="{35138b9a-5d96-4fbd-8e2d-a2440225f93a}"/> <!-- Win 7 -->
#     </application>
#   </compatibility>
#
#   <!-- DPI Awareness -->
#   <application xmlns="urn:schemas-microsoft-com:asm.v3">
#     <windowsSettings>
#       <dpiAware>true/pm</dpiAware>
#       <dpiAwareness>PerMonitorV2</dpiAwareness>
#     </windowsSettings>
#   </application>
# </assembly>
#
# Se un'app NON include il <compatibility> block per Windows 10/11,
# Windows applica automaticamente le compatibility shim come se l'app
# fosse progettata per Windows Vista. Questo può causare problemi
# (es. GetVersionEx restituisce 6.2 invece di 10.0).
```

Rif.: *DLL search order*, https://learn.microsoft.com/en-us/windows/win32/dlls/dynamic-link-library-search-order (consultato: 2026-05-23)

Rif.: *Side-by-side assemblies*, https://learn.microsoft.com/en-us/windows/win32/sbscs/about-side-by-side-assemblies- (consultato: 2026-05-23)

---

## Application Compatibility Toolkit — Scenari Avanzati

### Shim Database (SDB) — Fix personalizzati

```powershell
# Gli Shim intercettano le chiamate API dell'applicazione e le redirigono
# Permettono di far funzionare app legacy senza modificare il binario

# ============================================================
# TIPI DI SHIM PRINCIPALI
# ============================================================
#
# CorrectFilePaths
#   → Reindirizza percorsi hardcoded (es. C:\Windows\System → SysWOW64)
#
# ForceAdminAccess
#   → L'app crede di essere admin (virtualizza controlli UAC)
#
# VirtualizeDeleteFile
#   → Virtualizza le eliminazioni di file in directory protette
#
# RedirectShortcut
#   → Reindirizza shortcut a percorsi corretti
#
# WinXPVersionLie / Win7VersionLie / Win8VersionLie
#   → L'app riceve la versione OS che si aspetta
#
# EmulateSortingWindows61
#   → Emula il sorting order di Windows 7
#
# HandleBadPtr
#   → Gestisce puntatori non validi (app buggata)
#
# IgnoreException
#   → Ignora eccezioni specifiche (crash non critici)

# Creare un SDB con Compatibility Administrator:
# 1. Installare Windows ADK
# 2. Aprire Compatibility Administrator (32 o 64-bit)
# 3. New Database → nome: "CorpCompat"
# 4. New Application Fix:
#    - Nome app
#    - Path eseguibile
#    - Selezionare fix (shim) dal catalogo
#    - Testare
# 5. Save database → CorpCompat.sdb

# Installare SDB via command line
sdbinst "C:\Deploy\CorpCompat.sdb"

# Disinstallare SDB
sdbinst -u "C:\Deploy\CorpCompat.sdb"

# Installare SDB silenziosamente (per deploy via SCCM/GPO)
sdbinst -q "C:\Deploy\CorpCompat.sdb"

# Deploy SDB via GPO:
# Computer → Administrative Templates → Windows Components
#   → Application Compatibility → Turn off Application Compatibility Engine: DISABLED
#   → Install Application Compatibility Databases via script

# Elencare SDB installati
Get-ChildItem "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\InstalledSDB" |
    ForEach-Object {
        [PSCustomObject]@{
            Name = (Get-ItemProperty $_.PSPath).DatabaseDescription
            Path = (Get-ItemProperty $_.PSPath).DatabasePath
            Type = (Get-ItemProperty $_.PSPath).DatabaseType
        }
    }
```

### Compatibility Testing — Processo Strutturato

```powershell
# ============================================================
# PROCESSO DI TEST COMPATIBILITÀ PER MAJOR UPGRADE
# (es. Windows 10 → Windows 11, o feature update)
# ============================================================
#
# FASE 1: INVENTARIO APPLICAZIONI
# ─────────────────────────────────
# Censire tutte le applicazioni aziendali e categorizzarle

# Inventario app installate su tutti i PC del dominio (via SCCM o script)
$computers = Get-ADComputer -Filter 'OperatingSystem -like "*Windows 10*"' |
    Select-Object -ExpandProperty Name

$results = foreach ($pc in $computers) {
    Invoke-Command -ComputerName $pc -ScriptBlock {
        Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*" |
            Where-Object DisplayName |
            Select-Object DisplayName, DisplayVersion, Publisher, InstallDate
    } -ErrorAction SilentlyContinue | Select-Object PSComputerName, DisplayName,
        DisplayVersion, Publisher
}
$results | Export-Csv "C:\Reports\AppInventory.csv" -NoTypeInformation

# FASE 2: CATEGORIZZAZIONE
# ─────────────────────────
# Categoria A: Mission-critical (ERP, CRM, LOB)       → Test completo
# Categoria B: Standard (Office, browser, utility)     → Test rapido
# Categoria C: Opzionale (tool personali)              → Test se risorse
# Categoria D: Da dismettere                           → Skip

# FASE 3: TEST IN LAB
# ─────────────────────
# - VM con Windows 11 pulito
# - Installare ogni app Categoria A
# - Eseguire test funzionali critici
# - Verificare interazione con GPO e WDAC
# - Documentare risultati

# FASE 4: PILOT RING
# ────────────────────
# - 5-10% dei PC con utenti volontari
# - Monitorare per 2-4 settimane
# - Raccogliere feedback
# - Risolvere problemi emersi

# FASE 5: DEPLOY GRADUALE
# ─────────────────────────
# Ring 1: IT staff (1 settimana)
# Ring 2: Early adopters (2 settimane)
# Ring 3: Business units non-critiche (2 settimane)
# Ring 4: Tutta l'organizzazione
```

---

## Impostazioni di Compatibilità Windows

### Configurazione per applicazione — GUI e Registry

```powershell
# ============================================================
# COMPATIBILITY MODE — CONFIGURAZIONE DETTAGLIATA
# ============================================================
#
# Le impostazioni di compatibilità sono memorizzate nel registry
# in due posizioni:
#
# Per-utente:
#   HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers
#
# Per-macchina (richiede admin):
#   HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers
#
# Il valore è il percorso completo dell'eseguibile (come nome della proprietà)
# e il dato è una stringa con i flag separati da spazio.

# FLAG DISPONIBILI:
#
# Versione OS emulata:
#   WINXPSP3     → Windows XP SP3
#   VISTASP2     → Windows Vista SP2
#   WIN7RTM      → Windows 7
#   WIN8RTM      → Windows 8
#   WIN81RTM     → Windows 8.1
#   WIN10RTM     → Windows 10 (prima versione)
#
# Opzioni aggiuntive:
#   RUNASADMIN           → Esegui come amministratore
#   640X480              → Risoluzione 640x480
#   256COLOR             → Modalità 256 colori
#   16BITCOLOR           → Modalità 16-bit colore
#   DISABLETHEMES        → Disabilita temi visuali
#   DISABLEDWM           → Disabilita composizione desktop
#   HIGHDPIAWARE         → Segnala come DPI-aware
#   DPIUNAWARE           → Forza DPI-unaware (scaling sistema)
#   GDIDPISCALING        → Usa GDI DPI scaling
#   PERPROCESSSYSTEMDPIFORCEOFF  → Disabilita per-process system DPI
#   PERPROCESSSYSTEMDPIFORCEON   → Forza per-process system DPI
#   DISABLEDXMAXIMIZEDWINDOWEDMODE → Disabilita ottimizzazione fullscreen

# Esempio: impostare compatibilità Windows 7 + DPI awareness
Set-ItemProperty "HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" `
    -Name "C:\Program Files\Legacy\app.exe" `
    -Value "~ WIN7RTM HIGHDPIAWARE" -Type String
# Il carattere ~ indica di non ereditare impostazioni dalla macchina

# Elencare tutte le app con compatibility mode impostato
$userLayers = Get-ItemProperty `
    "HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" `
    -ErrorAction SilentlyContinue
if ($userLayers) {
    $userLayers.PSObject.Properties |
        Where-Object Name -notlike 'PS*' |
        ForEach-Object {
            [PSCustomObject]@{
                Scope = 'User'
                Path  = $_.Name
                Flags = $_.Value
            }
        }
}

# Rimuovere compatibility mode da un'app
Remove-ItemProperty "HKCU:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers" `
    -Name "C:\Program Files\Legacy\app.exe" -ErrorAction SilentlyContinue
```

### AppCompat Database — Shim database di sistema

```powershell
# Windows include un database di compatibilità preinstallato (sysmain.sdb)
# che contiene fix automatici per migliaia di applicazioni note.
#
# Posizione: C:\Windows\AppPatch\
# - sysmain.sdb        → Database principale (app note)
# - drvmain.sdb        → Database driver
# - msimain.sdb        → Database MSI
# - pcamain.sdb        → Program Compatibility Assistant
# - frxmain.sdb        → App-V (se installato)
#
# Il Program Compatibility Assistant (PCA) monitora le app
# e suggerisce automaticamente fix di compatibilità se rileva
# un crash o un comportamento anomalo.
#
# GPO per controllare PCA:
# Computer → Administrative Templates → Windows Components →
#   Application Compatibility →
#   Turn off Program Compatibility Assistant: Enabled/Disabled

# Verificare se l'Application Compatibility Engine è attivo
$aceEnabled = (Get-ItemProperty `
    "HKLM:\SOFTWARE\Policies\Microsoft\Windows\AppCompat" `
    -Name "DisableEngine" -ErrorAction SilentlyContinue).DisableEngine
Write-Host "AppCompat Engine: $(if($aceEnabled -eq 1){'DISABILITATO'}else{'ATTIVO'})"
```

---

### Virtualizzazione Applicazioni

```powershell
# App-V (Application Virtualization)
# Esegue applicazioni in un ambiente virtuale isolato
# Risolve conflitti DLL, permessi, registry tra applicazioni
# Integrato in SCCM/MECM e Intune

# MSIX (formato moderno)
# Container per applicazioni Windows
# Installazione pulita, disinstallazione completa
# Supporto per app Win32, .NET, UWP
# MSIX Packaging Tool per convertire installer tradizionali

# MSIX — Creare un pacchetto da installer MSI/EXE
# 1. Installare MSIX Packaging Tool dal Microsoft Store
# 2. Avviare su VM pulita (consigliato)
# 3. Wizard: selezionare installer originale
# 4. L'installer viene monitorato: file copiati, registry, servizi
# 5. Output: file .msix firmato
#
# Conversione da command-line con MsixPackagingTool.exe:
# MsixPackagingTool.exe create-package --template "C:\Templates\template.xml"

# MSIX — Deploy via Intune
# 1. Caricare .msix su Intune → Apps → Windows → Add
# 2. Tipo: Windows app (Win32) o Line-of-business app
# 3. Assegnare a gruppi utente/device

# MSIX — Deploy via SCCM
# Software Library → Application Management → Applications
# → Create Application → .msix file

# App-V — Sequencing (creazione pacchetto virtualizzato)
# 1. VM pulita con App-V Sequencer installato
# 2. Avviare Sequencer, selezionare installer
# 3. Installare normalmente nella VM
# 4. Configurare shortcuts e FTA (File Type Associations)
# 5. Output: pacchetto .appv

# App-V — Pubblicazione via SCCM
# Software Library → Application Management → Virtual Environments
# Pubblicare il pacchetto .appv e assegnare a collection

# Windows Sandbox
# VM leggera usa-e-getta per testare applicazioni sospette
# Abilitare:
Enable-WindowsOptionalFeature -FeatureName "Containers-DisposableClientVM" -Online

# Avviare: Start → Windows Sandbox
# Tutto ciò che viene fatto nella Sandbox viene cancellato alla chiusura

# Windows Sandbox — Configurazione avanzata (.wsb file)
# Creare file test-app.wsb:
$wsb = @'
<Configuration>
  <MappedFolders>
    <MappedFolder>
      <HostFolder>C:\Installers</HostFolder>
      <SandboxFolder>C:\Installers</SandboxFolder>
      <ReadOnly>true</ReadOnly>
    </MappedFolder>
  </MappedFolders>
  <LogonCommand>
    <Command>C:\Installers\setup.exe /silent</Command>
  </LogonCommand>
  <Networking>Enable</Networking>
  <vGPU>Enable</vGPU>
  <MemoryInMB>4096</MemoryInMB>
</Configuration>
'@
$wsb | Out-File "C:\Temp\test-app.wsb" -Encoding UTF8
# Doppio click sul .wsb per avviare la Sandbox configurata
```

---

## WDAC — Application Control

```powershell
# WDAC controlla quali binari possono essere eseguiti a livello kernel
# Più sicuro di AppLocker (che opera a livello utente)

# Policy modes:
# - Audit: registra violazioni senza bloccare (per test)
# - Enforce: blocca binari non autorizzati

# Creare policy da sistema di riferimento ("gold image")
New-CIPolicy -FilePath "C:\WDAC\Policy.xml" -Level Publisher `
    -Fallback Hash -UserPEs -ScanPath "C:\"

# Livelli di trust:
# Hash         → Identifica il file esatto (fragile con aggiornamenti)
# FileName     → Nome file eseguibile
# Publisher    → Firmato da un publisher specifico (consigliato)
# FilePublisher → Publisher + nome file + versione minima
# PCACertificate → Root CA del certificato di firma

# Aggiungere regole per app specifiche
Add-SignerRule -FilePath "C:\WDAC\Policy.xml" `
    -CertificatePath "C:\Certs\publisher.cer" -Kernel -User

# Aggiungere app per hash (per app non firmate)
$files = Get-SystemDriver -ScanPath "C:\Program Files\CustomApp" -UserPEs
New-CIPolicy -FilePath "C:\WDAC\CustomApp.xml" -DriverFiles $files -Level Hash

# Merge policy
Merge-CIPolicy -PolicyPaths "C:\WDAC\Policy.xml", "C:\WDAC\CustomApp.xml" `
    -OutputFilePath "C:\WDAC\MergedPolicy.xml"

# Impostare in Audit Mode
Set-RuleOption -FilePath "C:\WDAC\MergedPolicy.xml" -Option 3  # Audit Mode

# Convertire e deployare
ConvertFrom-CIPolicy -XmlFilePath "C:\WDAC\MergedPolicy.xml" `
    -BinaryFilePath "C:\WDAC\Policy.p7b"

# Deploy via GPO:
# Computer → Administrative Templates → System → Device Guard
# → Deploy WDAC: path del .p7b

# Event Log WDAC:
# Microsoft-Windows-CodeIntegrity/Operational
Get-WinEvent -LogName "Microsoft-Windows-CodeIntegrity/Operational" -MaxEvents 20
# Event ID 3076: Audit (sarebbe bloccato)
# Event ID 3077: Enforce (bloccato)
```

---

---

## WDAC — Scenari Enterprise Avanzati

### WDAC con Managed Installer

```powershell
# Managed Installer permette a SCCM/Intune di autorizzare automaticamente
# le applicazioni che distribuisce, senza creare regole WDAC manuali

# Abilitare Managed Installer in WDAC:
# 1. Creare policy WDAC con opzione Managed Installer
Set-RuleOption -FilePath "C:\WDAC\Policy.xml" -Option 13  # Managed Installer

# 2. Definire SCCM come Managed Installer
# Il client SCCM (CcmExec.exe) viene registrato come installer fidato
# Tutto ciò che SCCM installa viene automaticamente autorizzato da WDAC

# 3. Configurare via Intune:
# Endpoint Security → App Control → Create Policy
# Template: Default Windows mode + Managed Installer
```

### WDAC Supplemental Policies (Multiple Policy)

```powershell
# Windows 10 1903+ supporta multiple policy WDAC
# Base policy + supplemental policies per aggiungere eccezioni

# Creare base policy (restrittiva)
New-CIPolicy -FilePath "C:\WDAC\BasePolicy.xml" -Level Publisher `
    -Fallback Hash -UserPEs -MultiplePolicyFormat

# Impostare come base policy
Set-CIPolicyIdInfo -FilePath "C:\WDAC\BasePolicy.xml" `
    -BasePolicyToSupplementPath "C:\WDAC\BasePolicy.xml"

# Creare supplemental policy per app specifiche
New-CIPolicy -FilePath "C:\WDAC\Supplement-CustomApp.xml" `
    -Level FilePublisher -Fallback Hash -UserPEs `
    -ScanPath "C:\Program Files\CustomApp" `
    -MultiplePolicyFormat

# Collegare la supplemental alla base
Set-CIPolicyIdInfo -FilePath "C:\WDAC\Supplement-CustomApp.xml" `
    -BasePolicyToSupplementPath "C:\WDAC\BasePolicy.xml" `
    -SupplementsBasePolicyID "{GUID-della-base-policy}"

# Vantaggio: aggiornare le eccezioni senza toccare la base policy
```

### WDAC Monitoring e Auditing

```powershell
# Script di monitoraggio WDAC — generare report violazioni
function Get-WDACViolations {
    param(
        [int]$Hours = 24,
        [string]$ComputerName = $env:COMPUTERNAME
    )
    $startTime = (Get-Date).AddHours(-$Hours)

    Get-WinEvent -ComputerName $ComputerName `
        -LogName "Microsoft-Windows-CodeIntegrity/Operational" `
        -FilterXPath "*[System[TimeCreated[@SystemTime>='$($startTime.ToUniversalTime().ToString('o'))']]]" `
        -ErrorAction SilentlyContinue |
        Where-Object Id -in @(3076, 3077, 3089, 3090) |
        ForEach-Object {
            [PSCustomObject]@{
                Time      = $_.TimeCreated
                EventId   = $_.Id
                Mode      = if ($_.Id -in 3076, 3089) { "Audit" } else { "Blocked" }
                Message   = $_.Message.Substring(0, [Math]::Min(200, $_.Message.Length))
                Computer  = $ComputerName
            }
        }
}

# Report settimanale WDAC
$allViolations = Get-WDACViolations -Hours 168
$allViolations | Group-Object Mode | ForEach-Object {
    Write-Host "$($_.Name): $($_.Count) eventi"
}
$allViolations | Export-Csv "C:\Reports\WDAC-Violations-$(Get-Date -Format 'yyyyMMdd').csv" -NoTypeInformation
```

---

## Deploy Driver Enterprise — MDT, SCCM, Intune

### MDT (Microsoft Deployment Toolkit)

```powershell
# MDT gestisce i driver tramite il Deployment Workbench

# Struttura organizzata per modello:
# Deployment Share → Out-of-Box Drivers
# ├── Windows 11\
# │   ├── Dell Latitude 5540\
# │   │   ├── A01-Chipset\
# │   │   ├── A02-Network\
# │   │   ├── A03-Audio\
# │   │   └── A04-Video\
# │   ├── HP EliteBook 840 G10\
# │   └── Lenovo ThinkPad T14s Gen 4\
# └── WinPE Drivers\
#     ├── Network\
#     └── Storage\

# Importare driver in MDT via PowerShell
Import-Module "C:\Program Files\Microsoft Deployment Toolkit\bin\MicrosoftDeploymentToolkit.psd1"
New-PSDrive -Name "DS001" -PSProvider MDTProvider -Root "D:\DeploymentShare"

# Creare cartella modello
New-Item -Path "DS001:\Out-of-Box Drivers\Windows 11\Dell Latitude 5540" -ItemType Directory

# Importare driver
Import-MDTDriver -Path "DS001:\Out-of-Box Drivers\Windows 11\Dell Latitude 5540" `
    -SourcePath "C:\Drivers\Dell\Latitude-5540"

# Selection Profile per Task Sequence
# Deployment Workbench → Advanced Configuration → Selection Profiles
# Creare un profilo che include solo i driver del modello target

# Task Sequence — Inject Drivers
# Step "Inject Drivers" → Selection Profile: "Dell Latitude 5540 Drivers"
# Oppure: "Install all drivers from the selection profile"

# Automatic Model Detection (CustomSettings.ini)
# [Settings]
# Priority=Default
# [Default]
# DriverSelectionProfile=Nothing
# DriverGroup001=%Make%\%Model%
#
# I driver vengono selezionati automaticamente in base a Make e Model WMI
```

### SCCM / MECM

```powershell
# SCCM gestisce i driver tramite Driver Packages e Auto Apply

# ============================================================
# METODO 1: DRIVER PACKAGE (consigliato per modelli specifici)
# ============================================================

# 1. Importare driver
# Software Library → Operating Systems → Drivers → Import Driver
# Selezionare cartella con .inf files

# 2. Creare Driver Package
# Software Library → Operating Systems → Driver Packages → Create
# Nome: "Dell Latitude 5540 - Win11"
# Source: \\SCCM-SRV\Sources\Drivers\Dell\Latitude-5540

# 3. Aggiungere driver al package
# Selezionare i driver importati → Add to Driver Package

# 4. Distribuire sui Distribution Points
# Tasto destro → Distribute Content

# 5. Task Sequence step: "Apply Driver Package"
# WMI Query per selezionare il modello:
# SELECT * FROM Win32_ComputerSystem WHERE Model LIKE '%Latitude 5540%'

# ============================================================
# METODO 2: AUTO APPLY DRIVERS (per fleet eterogeneo)
# ============================================================

# Task Sequence step: "Auto Apply Drivers"
# SCCM cerca nel catalogo driver il match migliore per ogni dispositivo
# Pro: automatico, gestisce molti modelli
# Contro: più lento, può selezionare driver non testati

# ============================================================
# AUTOMAZIONE: DOWNLOAD DRIVER DA OEM
# ============================================================

# Dell Command | Update — scarica driver per modello
# HP Client Management Script Library
# Lenovo System Update

# Esempio: Dell Command | Update CLI
# dcu-cli.exe /applyUpdates -autoSuspendBitLocker=enable
```

### Intune (Endpoint Manager)

```powershell
# Intune gestisce i driver tramite Windows Update for Business
# e driver update policy (preview/GA)

# ============================================================
# METODO 1: WINDOWS UPDATE FOR BUSINESS — DRIVER UPDATES
# ============================================================

# Intune → Devices → Windows → Update Rings
# "Driver updates" tab:
# - Automatically approve all drivers: NO (consigliato)
# - Approve drivers individually: YES

# Intune → Devices → Windows → Driver updates
# Lista di driver disponibili per i dispositivi gestiti
# Approvare/rifiutare singolarmente

# ============================================================
# METODO 2: DRIVER PACKAGE VIA WIN32 APP
# ============================================================

# Per driver specifici che non passano da Windows Update:
# 1. Creare pacchetto Win32 (.intunewin) con il driver
# 2. Detection rule: registry key o file version del driver
# 3. Install command: pnputil /add-driver driver.inf /install
# 4. Uninstall command: pnputil /delete-driver oemXX.inf /uninstall

# IntuneWinAppUtil.exe per creare il pacchetto:
# IntuneWinAppUtil.exe -c C:\Drivers\NetDriver\ -s install.cmd -o C:\Packages\

# install.cmd:
# pnputil /add-driver "%~dp0driver.inf" /install

# Detection rule:
# Registry: HKLM\SYSTEM\CurrentControlSet\Services\<DriverName>
# Chiave: Version → valore >= versione attesa
```

---

## Windows Update for Business — Driver Management

```powershell
# WUfB permette di controllare come i driver vengono distribuiti via Windows Update

# ============================================================
# GPO PER CONTROLLO DRIVER VIA WINDOWS UPDATE
# ============================================================

# Computer → Administrative Templates → Windows Components → Windows Update

# Escludere driver da Windows Update (tutto o niente)
# → Do not include drivers with Windows Updates: Enabled
# Nota: sconsigliato in generale, meglio usare il controllo granulare

# Manage Updates offered from WUfB:
# → Manage preview builds: (Semi-Annual Channel per driver)
# → Select when Quality Updates are received: (ritardo in giorni)

# ============================================================
# INTUNE — WINDOWS UPDATE FOR BUSINESS POLICY
# ============================================================

# Devices → Windows → Update Rings → Create Profile
# Settings:
# - Feature update deferral: 30 days (tipico)
# - Quality update deferral: 7 days (tipico)
# - Driver deferral: 14 days (consigliato)
# - Microsoft product updates: Allow
# - Windows drivers: Allow (con approval manuale)

# ============================================================
# WSUS — DRIVER APPROVAL WORKFLOW
# ============================================================

# WSUS → Updates → Driver Updates
# Approvare i driver per gruppo di computer:
# $wsus = Get-WsusServer
# $updates = $wsus.GetUpdates() | Where-Object {
#     $_.UpdateClassificationTitle -eq "Drivers" -and
#     $_.IsApproved -eq $false
# }
# foreach ($u in $updates) {
#     Write-Host "Driver: $($u.Title) — KB: $($u.KnowledgebaseArticles)"
# }
# Approvare: $u.Approve("Install", $targetGroup)
```

---

## Automazione e Script di Gestione Driver

### Script: Inventario Driver Fleet

```powershell
# Script completo per inventario driver su tutti i PC del dominio
# Utile per: audit, preparazione upgrade, identificazione driver obsoleti

function Get-FleetDriverInventory {
    param(
        [string]$OUPath = "OU=Computer,DC=corp,DC=contoso,DC=com",
        [string]$OutputPath = "C:\Reports"
    )

    $computers = Get-ADComputer -SearchBase $OUPath -Filter * |
        Select-Object -ExpandProperty Name

    $inventory = foreach ($pc in $computers) {
        try {
            Invoke-Command -ComputerName $pc -ScriptBlock {
                Get-WindowsDriver -Online | ForEach-Object {
                    [PSCustomObject]@{
                        Computer      = $env:COMPUTERNAME
                        DriverName    = $_.Driver
                        OriginalName  = $_.OriginalFileName
                        ProviderName  = $_.ProviderName
                        Date          = $_.Date
                        Version       = $_.Version
                        ClassName     = $_.ClassName
                        BootCritical  = $_.BootCritical
                    }
                }
            } -ErrorAction Stop
        }
        catch {
            [PSCustomObject]@{
                Computer = $pc; DriverName = "ERRORE CONNESSIONE"
                OriginalName = $_.Exception.Message
                ProviderName = ""; Date = ""; Version = ""
                ClassName = ""; BootCritical = ""
            }
        }
    }

    $timestamp = Get-Date -Format "yyyyMMdd-HHmm"
    $inventory | Export-Csv "$OutputPath\DriverInventory-$timestamp.csv" -NoTypeInformation

    # Report riepilogativo
    Write-Host "`n=== RIEPILOGO DRIVER FLEET ==="
    Write-Host "Computer scansionati: $($computers.Count)"
    Write-Host "Driver totali trovati: $(($inventory | Where-Object DriverName -ne 'ERRORE CONNESSIONE').Count)"

    # Driver unici per provider
    $inventory | Where-Object DriverName -ne "ERRORE CONNESSIONE" |
        Group-Object ProviderName |
        Sort-Object Count -Descending |
        Select-Object Count, Name -First 15 |
        Format-Table -AutoSize

    return $inventory
}

# Uso:
# $inv = Get-FleetDriverInventory -OUPath "OU=Workstations,DC=corp,DC=contoso,DC=com"
```

### Script: Pulizia Driver Store

```powershell
# Rimuovere driver orfani dal Driver Store per liberare spazio disco
# Il Driver Store può crescere a diversi GB con driver obsoleti

function Clear-OldDrivers {
    param(
        [switch]$WhatIf
    )

    # Ottenere tutti i driver staged
    $staged = pnputil /enum-drivers | Out-String
    $drivers = [regex]::Matches($staged, 'Published Name\s*:\s*(oem\d+\.inf)')

    $removed = 0
    foreach ($match in $drivers) {
        $infName = $match.Groups[1].Value

        # Verificare se il driver è attualmente in uso
        $inUse = Get-PnpDevice | Where-Object {
            try {
                $props = Get-PnpDeviceProperty -InstanceId $_.InstanceId -ErrorAction SilentlyContinue
                ($props | Where-Object KeyName -eq 'DEVPKEY_Device_DriverInfPath').Data -eq $infName
            } catch { $false }
        }

        if (-not $inUse) {
            if ($WhatIf) {
                Write-Host "[WhatIf] Rimuoverei: $infName"
            }
            else {
                Write-Host "Rimuovendo driver non in uso: $infName"
                pnputil /delete-driver $infName
            }
            $removed++
        }
    }

    Write-Host "`nDriver non in uso trovati: $removed"

    # Dimensione attuale Driver Store
    $size = (Get-ChildItem "C:\Windows\System32\DriverStore\FileRepository" -Recurse -File |
        Measure-Object Length -Sum).Sum / 1GB
    Write-Host "Dimensione Driver Store: $([math]::Round($size, 2)) GB"
}

# Uso:
# Clear-OldDrivers -WhatIf    # Anteprima (non elimina nulla)
# Clear-OldDrivers            # Esecuzione reale
```

### Script: Backup e Restore Driver

```powershell
# Backup completo dei driver third-party — pre-reinstallazione OS

function Backup-Drivers {
    param(
        [string]$Destination = "D:\Backup\Drivers\$(hostname)-$(Get-Date -Format 'yyyyMMdd')"
    )

    New-Item $Destination -ItemType Directory -Force | Out-Null

    # Export via DISM (metodo consigliato)
    Export-WindowsDriver -Online -Destination $Destination

    # Salvare anche il manifest
    $manifest = Get-WindowsDriver -Online | Select-Object Driver, OriginalFileName,
        ProviderName, Date, Version, ClassName, BootCritical

    $manifest | Export-Csv "$Destination\_manifest.csv" -NoTypeInformation
    $manifest | ConvertTo-Json | Out-File "$Destination\_manifest.json" -Encoding UTF8

    $count = ($manifest | Measure-Object).Count
    $size = (Get-ChildItem $Destination -Recurse -File | Measure-Object Length -Sum).Sum / 1MB

    Write-Host "Backup completato:"
    Write-Host "  Driver esportati: $count"
    Write-Host "  Dimensione: $([math]::Round($size, 2)) MB"
    Write-Host "  Percorso: $Destination"
}

function Restore-Drivers {
    param(
        [string]$Source
    )

    if (-not (Test-Path $Source)) {
        Write-Error "Percorso non trovato: $Source"
        return
    }

    # Installare tutti i driver dalla cartella di backup
    $infFiles = Get-ChildItem $Source -Recurse -Filter "*.inf"
    $total = $infFiles.Count
    $current = 0
    $errors = @()

    foreach ($inf in $infFiles) {
        $current++
        Write-Progress -Activity "Installando driver" -Status "$current / $total" `
            -PercentComplete (($current / $total) * 100)

        $result = pnputil /add-driver $inf.FullName /install 2>&1
        if ($LASTEXITCODE -ne 0) {
            $errors += [PSCustomObject]@{
                INF   = $inf.Name
                Error = $result -join " "
            }
        }
    }

    Write-Host "`nRestore completato: $($total - $errors.Count) / $total driver installati"
    if ($errors.Count -gt 0) {
        Write-Host "Driver con errori:"
        $errors | Format-Table -AutoSize
    }
}
```

---

## GPO per Driver e Compatibilità

```powershell
# ============================================================
# GPO — CONTROLLO INSTALLAZIONE DRIVER
# ============================================================

# Computer → Administrative Templates → System → Device Installation

# Impedire installazione di dispositivi specifici (per tipo):
# → Prevent installation of devices using drivers that match
#   these device setup classes:
#   {745a17a0-74d3-11d0-b6fe-00a0c90f57da}  # Human Interface (USB HID)
#   {36fc9e60-c465-11cf-8056-444553540000}  # USB controllers
#   → Apply to matching devices already installed: Yes

# Impedire installazione di dispositivi specifici (per ID):
# → Prevent installation of devices that match any of these device IDs:
#   USB\VID_0781*   # Blocca tutti i device SanDisk
#   → Apply to all matching: Yes

# Consentire solo dispositivi approvati:
# → Prevent installation of devices not described by other policy settings: Enabled
# → Allow installation of devices that match:
#   (lista specifica di Hardware ID approvati)

# ============================================================
# GPO — COMPATIBILITÀ APPLICAZIONI
# ============================================================

# Computer → Administrative Templates → Windows Components →
#   Application Compatibility

# Turn off Application Compatibility Engine: DISABLED
#   → Deve restare attivo per gli shim

# Turn off Program Compatibility Assistant: Enabled
#   → Disabilita il popup PCA (Program Compatibility Assistant)
#   → In enterprise è spesso disabilitato

# Turn off Steps Recorder: Enabled
#   → Disabilita il recorder di passi (privacy)

# ============================================================
# GPO — WINDOWS UPDATE DRIVER POLICY
# ============================================================

# Computer → Administrative Templates → Windows Components →
#   Windows Update → Manage updates offered from WUfB

# Do not include drivers with Windows Updates: Enabled
#   → I driver NON vengono distribuiti via Windows Update
#   → Usare se i driver vengono gestiti separatamente (SCCM/MDT)

# Specify deadline for automatic updates:
# → Quality updates: 7 days
# → Feature updates: 14 days
# → Grace period: 2 days
```

---

## Scenari Reali Enterprise

### Scenario 1: Migrazione Fleet da Windows 10 a Windows 11

```
CONTESTO: 500 workstation, 15 modelli diversi (Dell, HP, Lenovo)
OBIETTIVO: Upgrade a Windows 11 con zero downtime driver

PASSO 1: Inventario
- Eseguire Get-FleetDriverInventory su tutte le workstation
- Identificare modelli e driver attuali
- Verificare compatibilità hardware Win11 (TPM 2.0, Secure Boot, CPU)

PASSO 2: Download Driver
- Scaricare driver Win11 per ogni modello dagli OEM:
  Dell: dell.com/support/kbdoc → Enterprise Driver Packs
  HP: ftp.hp.com/pub/softpaq/sp → Client Management Solutions
  Lenovo: support.lenovo.com → SCCM Driver Packs
- Organizzare nella struttura \Drivers\<Vendor>\<Model>\

PASSO 3: Test Lab
- Creare Task Sequence Win11 in MDT/SCCM
- Testare su almeno 1 unità per modello
- Abilitare Driver Verifier standard per 48h di test
- Verificare HVCI compatibility

PASSO 4: Pilot
- Ring 1: 10 PC IT (1 settimana)
- Ring 2: 50 PC early adopters (2 settimane)
- Monitorare Event Log per errori driver (Code 10, 28, 43)

PASSO 5: Deploy
- Ring 3: 200 PC (2 settimane)
- Ring 4: 240 PC rimanenti (2 settimane)
- Rollback plan: immagine di backup pre-upgrade
```

### Scenario 2: BSOD Ricorrente su Modello Specifico

```
SINTOMI: 20 Dell Latitude 5540 con BSOD "DRIVER_IRQL_NOT_LESS_OR_EQUAL"
FREQUENZA: 2-3 volte al giorno, random

DIAGNOSI:
1. Analizzare minidump con WinDbg:
   - !analyze -v → identifica driver: igdkmd64.sys (Intel Graphics)
   - lmvm igdkmd64 → versione: 31.0.101.4502

2. Verificare se esiste versione più recente:
   - Intel Driver Support Assistant: 31.0.101.5186 disponibile

3. Confermare con Driver Verifier su una macchina:
   - verifier /standard /driver igdkmd64.sys
   - Crash immediato confermato con Special Pool violation

SOLUZIONE:
1. Scaricare driver Intel DCH 31.0.101.5186
2. Testare su 2 macchine per 48h
3. Zero BSOD → distribuire a tutte le 20 macchine via SCCM
4. Monitorare per 1 settimana

PREVENZIONE:
- Aggiungere controllo versione driver Intel Graphics alla compliance baseline
- Alert automatico se versione < 31.0.101.5186
```

### Scenario 3: Blocco USB per Security Compliance

```
CONTESTO: Compliance PCI-DSS richiede blocco USB storage
OBIETTIVO: Bloccare chiavette USB ma permettere mouse/tastiera/stampanti

GPO Configuration:
Computer → Administrative Templates → System → Device Installation

1. Prevent installation of removable devices: Enabled
   → Blocca tutti i removable storage

2. Eccezioni per dispositivi approvati:
   Allow installation of devices that match these device IDs:
   → USB\Class_03 (HID — mouse, tastiera)
   → USB\Class_07 (Stampanti)
   → USB\Class_0E (Video — webcam)
   → USB\VID_xxxx&PID_yyyy (dispositivi specifici approvati)

3. Per applicare anche a dispositivi già installati:
   → Apply layered order: Already installed matching devices = Prevent

4. Verifica:
   Get-PnpDevice -Class USB | Select-Object FriendlyName, Status, InstanceId
   → Le chiavette USB risultano disabilitate
   → Mouse e tastiere funzionano normalmente
```

---

## Best Practices

1. **Catalog driver approvato**: mantenere un repository di driver testati per ogni modello hardware, organizzato `\Vendor\Model\DriverType\`
2. **Export driver prima di reinstallare**: `Export-WindowsDriver` salva tutti i driver third-party; includere il manifest CSV
3. **WDAC in produzione**: partire da Audit Mode, analizzare per settimane, poi passare a Enforce; usare supplemental policies per eccezioni
4. **Test driver su ambiente lab**: ogni nuovo driver va testato prima del deploy in produzione con Driver Verifier standard per almeno 48h
5. **Secure Boot + HVCI**: abilitare su tutti i dispositivi supportati per protezione kernel; verificare compatibilità driver prima
6. **Compatibility Testing**: testare le applicazioni critiche su ogni major update di Windows prima del rollout con processo Ring-based
7. **Naming convention driver packages**: `<Vendor>-<Model>-<OS>-<Date>` (es. `Dell-Lat5540-Win11-20260115`)
8. **Pulizia periodica Driver Store**: eseguire audit trimestrale; il Driver Store può crescere oltre 5 GB con versioni obsolete
9. **Driver firmati WHQL**: in produzione accettare solo driver WHQL o Attestation Signed; mai disabilitare la verifica firma
10. **Automazione inventario**: eseguire inventario driver mensile; confrontare con il catalogo approvato; segnalare deviazioni
11. **WinPE driver separati**: mantenere un set di driver storage e network specifici per WinPE, separati dai driver OS
12. **Backup pre-upgrade**: prima di ogni major update driver (GPU, chipset, NIC), eseguire snapshot o backup del sistema
13. **Event forwarding centralizzato**: inoltrare eventi CodeIntegrity e PnP da tutte le workstation a un collector centrale (WEF)
14. **WDAC + Managed Installer**: in ambienti SCCM/Intune, usare Managed Installer per autorizzare automaticamente le app distribuite
15. **SDB per legacy app**: creare e distribuire SDB personalizzati via GPO per app legacy incompatibili con Windows 11

---

## Alberi Decisionali di Troubleshooting

### Albero 1: BSOD causato da driver

```
BSOD (Blue Screen of Death)
│
├─ Il BSOD è ricorrente?
│  ├─ NO → Probabilmente evento singolo (cosmic ray, surriscaldamento)
│  │       Monitorare. Se non si ripete → nessuna azione.
│  │
│  └─ SÌ → Raccogliere minidump: C:\Windows\Minidump\*.dmp
│          │
│          ├─ Analizzare con WinDbg: !analyze -v
│          │  │
│          │  ├─ Il driver colpevole è identificato?
│          │  │  ├─ SÌ → Il driver è third-party?
│          │  │  │       ├─ SÌ → Esiste versione più recente dal vendor?
│          │  │  │       │       ├─ SÌ → Aggiornare. Testare 48h.
│          │  │  │       │       │       ├─ BSOD risolto → Deploy fleet
│          │  │  │       │       │       └─ BSOD persiste → Driver Verifier
│          │  │  │       │       │           su driver sospetto. Contattare vendor.
│          │  │  │       │       └─ NO → Rollback alla versione precedente.
│          │  │  │       │              Contattare vendor per fix.
│          │  │  │       └─ NO (inbox Microsoft) → Verificare Windows Update.
│          │  │  │              sfc /scannow + DISM /RestoreHealth.
│          │  │  │              Se persiste: reinstallare OS in-place.
│          │  │  │
│          │  │  └─ NO → Bug check code indica la categoria:
│          │  │         ├─ IRQL_NOT_LESS_OR_EQUAL → Accesso memoria a IRQL errato
│          │  │         ├─ PAGE_FAULT_IN_NONPAGED_AREA → Memory corruption
│          │  │         ├─ SYSTEM_SERVICE_EXCEPTION → Eccezione in syscall
│          │  │         ├─ KERNEL_DATA_INPAGE_ERROR → Errore I/O disco (HW?)
│          │  │         └─ DRIVER_POWER_STATE_FAILURE → Problema power mgmt
│          │  │           → Abilitare Driver Verifier /standard /all
│          │  │             (in ambiente di test!)
│          │  │
│          │  └─ Il minidump è corrotto o assente?
│          │     → Verificare: pagefile sufficiente su C:
│          │       Reg: CrashDumpEnabled = 7 (Automatic)
│          │       Riavviare e attendere il prossimo crash.
```

### Albero 2: Dispositivo non riconosciuto

```
Dispositivo non riconosciuto (punto esclamativo giallo / Unknown device)
│
├─ Device Manager → Properties → Status Code
│  │
│  ├─ Code 28: Driver non installato
│  │  ├─ Ottenere Hardware ID: Get-PnpDevice | Where Status -ne OK
│  │  ├─ Cercare driver sul sito del vendor con Hardware ID
│  │  ├─ Alternativa: pnputil /add-driver <path> /install
│  │  └─ Se nessun driver trovato: verificare che il dispositivo
│  │     sia supportato sul sistema operativo corrente.
│  │
│  ├─ Code 10: Impossibile avviare il dispositivo
│  │  ├─ Driver installato ma non funzionante
│  │  ├─ Provare: disinstallare dispositivo + riavviare (PnP reinstalla)
│  │  ├─ Se persiste: aggiornare driver
│  │  └─ Se ancora persiste: possibile guasto hardware → testare su altro PC
│  │
│  ├─ Code 43: Dispositivo arrestato (problema segnalato dal driver)
│  │  ├─ Comune con GPU, USB e Bluetooth
│  │  ├─ Provare: disinstallare driver + riavviare
│  │  ├─ Se USB: provare porta diversa, altro cavo
│  │  └─ Se GPU: DDU (Display Driver Uninstaller) + reinstallare
│  │
│  ├─ Code 52: Firma digitale non verificabile
│  │  ├─ Il driver non è firmato o la firma è scaduta/corrotta
│  │  ├─ Verificare: Get-AuthenticodeSignature <driver.sys>
│  │  ├─ Scaricare versione firmata dal vendor
│  │  └─ Se non disponibile: → vedi albero "Errore firma driver"
│  │
│  └─ Code 12: Risorse insufficienti (IRQ/memoria)
│     ├─ Conflitto risorse tra dispositivi
│     ├─ BIOS/UEFI: verificare impostazioni IRQ
│     ├─ Provare: slot PCI diverso (se possibile)
│     └─ Se persiste: disabilitare dispositivo in conflitto
```

### Albero 3: Errore firma driver

```
Driver non caricato per errore di firma
│
├─ Il sistema ha Secure Boot attivo?
│  ├─ SÌ → Il driver è WHQL o Attestation signed?
│  │       ├─ SÌ → Verificare integrità catalogo .cat
│  │       │       sigcheck -v driver.sys
│  │       │       Se corrotto: riscaricare dal vendor
│  │       └─ NO → Il driver deve essere firmato via Partner Center
│  │              Contattare il vendor. Nessun workaround sicuro.
│  │
│  └─ NO → KMCS comunque attivo su Windows 64-bit
│          ├─ Il driver è Authenticode signed?
│          │  ├─ SÌ (UMDF) → Dovrebbe caricarsi. Verificare integrità.
│          │  └─ SÌ (KMDF) → Su Windows 10 1607+, Authenticode non basta
│          │                  per kernel-mode. Serve WHQL/Attestation.
│          └─ Il driver non è firmato?
│             ├─ È un ambiente di SVILUPPO/LAB?
│             │  ├─ SÌ → bcdedit /set testsigning on
│             │  │       Firmare con certificato di test
│             │  │       (watermark "Test Mode" sul desktop)
│             │  └─ NO → NON abilitare test signing in produzione.
│             │          Contattare il vendor per driver firmato.
│             │          Se il vendor non esiste più:
│             │          valutare hardware alternativo.
│             └─ È un driver legacy cross-signed?
│                ├─ Il certificato è nella lista dbx (revocato)?
│                │  ├─ SÌ → Driver bloccato permanentemente.
│                │  │       Cercare driver più recente.
│                │  └─ NO → Dovrebbe ancora caricarsi.
│                │          Verificare Event Log CodeIntegrity.
│                └─ Verificare data scadenza certificato:
│                   Get-AuthenticodeSignature driver.sys
```

### Albero 4: Problema di compatibilità applicazione

```
Applicazione non funziona correttamente su Windows 11
│
├─ L'applicazione si avvia?
│  ├─ NO → Errore specifico visualizzato?
│  │       ├─ "Side-by-side configuration incorrect"
│  │       │  → Installare il Visual C++ Redistributable richiesto
│  │       │    Verificare manifest con mt.exe
│  │       ├─ "This app can't run on your PC"
│  │       │  → App 16-bit o architettura incompatibile
│  │       │    Soluzione: VM con Windows XP/7 a 32-bit
│  │       ├─ "Blocked by administrator" / WDAC
│  │       │  → Verificare Event ID 3077 in CodeIntegrity log
│  │       │    Creare regola WDAC supplementare
│  │       └─ Crash silenzioso o errore generico
│  │          → Controllare Event Viewer → Application log
│  │            Provare Compatibility Mode (Win 10 / Win 7)
│  │
│  └─ SÌ, ma con problemi → Che tipo di problema?
│     ├─ Problemi grafici / DPI scaling errato
│     │  → Properties → Compatibility → Change high DPI settings
│     │    Override: scaling performed by Application
│     │    Se non basta: DPIUNAWARE nel registry AppCompatFlags
│     │
│     ├─ Errori di permesso / accesso negato
│     │  → L'app scrive in C:\Program Files o C:\Windows?
│     │    Soluzione 1: Compatibility → Run as administrator
│     │    Soluzione 2: Shim ForceAdminAccess (virtualizza UAC)
│     │    Soluzione 3: Ridirezione con shim CorrectFilePaths
│     │
│     ├─ L'app mostra la versione OS sbagliata
│     │  → L'app usa GetVersionEx (deprecata)?
│     │    Senza manifest <compatibility>, riceve 6.2 (Win 8)
│     │    Soluzione: aggiungere manifest con supportedOS Win10/11
│     │    Alternativa: shim Win10RTM / Win7VersionLie
│     │
│     └─ Funzionalità mancante o comportamento diverso
│        → API deprecata rimossa in Windows 11?
│          Verificare documentazione Microsoft per breaking changes
│          Se l'API è stata rimossa: contattare il vendor per update
│          Se il vendor non supporta Win11: MSIX / App-V / VM
```

---

## Troubleshooting

**1. "Dispositivo con punto esclamativo giallo in Device Manager"** → Tasto destro → Properties → vedi error code. Code 28: driver non installato (`pnputil /add-driver`). Code 10/43: driver corrotto o hardware guasto. Code 12: conflitto risorse. Verificare anche `setupapi.dev.log` per dettagli sul fallimento dell'installazione.

**2. "BSOD dopo installazione driver"** → Boot in Safe Mode, disinstallare il driver (`pnputil /delete-driver`), rollback dal Device Manager. Se non si avvia nemmeno in Safe Mode: WinRE → Disable Driver Signature Enforcement → disinstallare. Usare Driver Verifier per identificare driver instabili. Analizzare `C:\Windows\Minidump\*.dmp` con WinDbg.

**3. "App non funziona su Windows 11 ma funzionava su Windows 10"** → Provare Compatibility Mode (Win10). Verificare se l'app scrive in directory protette. Controllare se WDAC/AppLocker la blocca. Verificare Event ID 3076/3077 in CodeIntegrity log. Come ultimo resort: virtualizzazione App-V, MSIX, o VM con Windows 10.

**4. "WDAC blocca applicazione legittima"** → Verificare Event ID 3077 per identificare il file bloccato. Creare regola supplementare (preferibilmente a livello Publisher) e merge nella policy. Testare in Audit Mode prima di re-enforcing. Usare `ConvertFrom-CIPolicy` e ridistribuire.

**5. "Driver Store occupa troppo spazio disco"** → Eseguire `pnputil /enum-drivers` per elencare i driver staged. Identificare versioni multiple dello stesso driver (es. oem15.inf, oem16.inf, oem17.inf tutti Intel Graphics). Rimuovere le versioni vecchie con `pnputil /delete-driver oemXX.inf`. Alternativa: usare DISM `Dism /Online /Cleanup-Image /StartComponentCleanup`.

**6. "HVCI impedisce il caricamento di un driver necessario"** → Verificare Event ID 3089/3090 nel log CodeIntegrity. Se il driver è di un vendor noto, verificare se esiste una versione HVCI-compatible. Se non esiste: contattare il vendor. Se il driver è indispensabile e nessuna alternativa esiste, valutare di disabilitare HVCI solo sulla macchina specifica (non consigliato).

**7. "Windows Update installa un driver sbagliato che causa problemi"** → Disinstallare il driver dal Device Manager (Roll Back Driver). Bloccare il driver specifico: scaricare "Show or hide updates troubleshooter" (wushowhide.diagcab) o usare GPO per bloccare driver da Windows Update. In alternativa: usare la policy GPO "Prevent installation of devices that match".

**8. "PnPUtil /add-driver fallisce con errore 259 (no more data)"** → Il file .inf non contiene Hardware ID corrispondenti all'hardware presente. Verificare che il driver sia per l'architettura corretta (x64 vs ARM64). Verificare che la sezione `[Manufacturer]` nel .inf includa il target OS corretto.

**9. "Driver non firmato necessario per hardware legacy"** → Su Windows 64-bit, i driver non firmati sono bloccati. Opzioni: (a) contattare il vendor per driver firmato, (b) usare test signing mode (`bcdedit /set testsigning on` — SOLO per lab!), (c) disabilitare secure boot + driver signature enforcement all'avvio (temporaneo). Mai usare test signing in produzione.

**10. "Compatibilità app: DPI scaling errato su monitor 4K"** → Properties → Compatibility → "Change high DPI settings" → "Override high DPI scaling behavior" → Scaling performed by: Application. Per GPO: impostare il flag `HIGHDPIAWARE` nel registry `AppCompatFlags\Layers`. Se l'app non supporta DPI scaling, considerare l'esecuzione in VM con risoluzione fissa.

**11. "SDB personalizzato non viene applicato"** → Verificare che il file .sdb sia installato: `sdbinst -l` elenca i database installati. Verificare che Application Compatibility Engine sia abilitato (GPO non deve avere "Turn off Application Compatibility Engine: Enabled"). Verificare che il percorso dell'eseguibile nel SDB corrisponda esattamente al percorso reale.

**12. "Secure Boot impedisce il boot dopo aggiornamento firmware"** → Il firmware potrebbe aver aggiornato le chiavi Secure Boot. Accedere al BIOS/UEFI: verificare che Secure Boot sia abilitato. Se le chiavi sono state resettate: ripristinare le chiavi di default dal BIOS. Se il bootloader è stato compromesso: usare il supporto di installazione Windows per riparare il boot (`bootrec /rebuildbcd`).

**13. "Export-WindowsDriver non esporta tutti i driver"** → `Export-WindowsDriver -Online` esporta solo driver third-party (non inbox). Per ottenere anche i driver inbox: usare `Get-WindowsDriver -Online -All` e copiare manualmente dal FileRepository. I driver inbox sono già inclusi nel media di installazione Windows.

**14. "Auto Apply Drivers in SCCM seleziona il driver sbagliato"** → Verificare il ranking: il driver con Hardware ID match più specifico e data più recente vince. Soluzione: usare "Apply Driver Package" con WMI query per il modello invece di "Auto Apply Drivers". Verificare che non ci siano driver duplicati nel catalogo SCCM.

**15. "Windows Sandbox non si avvia"** → Verificare: virtualizzazione abilitata nel BIOS, Hyper-V installato, feature "Containers-DisposableClientVM" abilitata, RAM sufficiente (almeno 4 GB liberi). Errore comune: conflitto con altri hypervisor (VirtualBox, VMware). Su Windows Home: feature non disponibile.

**16. "App-V pacchetto non si avvia con errore 0xC0000135"** → DLL mancante nel pacchetto virtuale. Ri-sequenziare includendo le dipendenze. Verificare che il App-V client sia attivo: `Get-Service AppVClient`. Verificare la versione del client App-V corrisponda a quella del sequencer.

**17. "MSIX installazione fallisce con firma non attendibile"** → Il certificato usato per firmare il pacchetto MSIX non è trusted sulla macchina. Installare il certificato nel Trusted People store: `Import-Certificate -FilePath cert.cer -CertStoreLocation Cert:\LocalMachine\TrustedPeople`. In enterprise: distribuire il certificato via GPO.

---

## FAQ

**Q1: Qual è la differenza tra KMDF e UMDF? Quando usare quale?**
KMDF (Kernel Mode Driver Framework) gira in kernel mode (Ring 0) ed è usato per driver che richiedono accesso diretto all'hardware: storage, rete, GPU, chipset. Un crash nel KMDF causa BSOD. UMDF (User Mode Driver Framework) gira in user mode (Ring 3) ed è usato per dispositivi più semplici: stampanti, sensori, USB semplici. Un crash in UMDF non causa BSOD. Quando possibile, i vendor dovrebbero usare UMDF per maggiore stabilità.

**Q2: Come forzare l'installazione di un driver specifico quando Windows sceglie quello sbagliato?**
Device Manager → tasto destro → Update Driver → Browse my computer → Let me pick → Have Disk → selezionare il .inf desiderato. Via PowerShell: `pnputil /add-driver driver.inf /install /force`. Per impedire che Windows Update sovrascriva: usare la GPO "Prevent installation of devices that match these device IDs" con il device ID, poi installare manualmente il driver desiderato.

**Q3: Che differenza c'è tra WDAC e AppLocker?**
WDAC opera a livello kernel (più sicuro, più difficile da bypassare) e controlla quali binari possono essere caricati. AppLocker opera a livello user-mode e controlla quali applicazioni l'utente può eseguire. WDAC è consigliato per scenari di alta sicurezza. AppLocker è più semplice da gestire e sufficiente per molti scenari. Possono essere usati insieme: WDAC per il kernel, AppLocker per il controllo utente.

**Q4: Come verificare se un driver è compatibile con HVCI prima di distribuirlo?**
Tre metodi: (1) Consultare la lista Microsoft di driver incompatibili. (2) Abilitare HVCI in Audit Mode e verificare Event ID 3089 nel log CodeIntegrity. (3) Usare il Windows Hardware Lab Kit (HLK) con il test "Code Integrity". Il vendor dovrebbe certificare la compatibilità HVCI.

**Q5: Quando usare MSIX vs App-V vs Compatibility Shim?**
MSIX: per app moderne che devono essere containerizzate con installazione/disinstallazione pulita; supporta Win32, .NET, UWP. App-V: per app legacy che hanno conflitti DLL/registry con altre app; esecuzione completamente virtualizzata. Shim (SDB): per app che hanno problemi specifici di compatibilità OS ma non conflitti tra app; fix leggero senza virtualizzazione.

**Q6: Come gestire i driver su dispositivi ARM64 Windows?**
I driver ARM64 sono diversi dai driver x64 — non sono intercambiabili. I driver x86/x64 non funzionano su Windows ARM64 (nemmeno con emulazione). Ogni driver deve essere compilato specificamente per ARM64. Verificare con il vendor la disponibilità. I driver Windows inbox coprono la maggior parte dell'hardware supportato.

**Q7: Posso disabilitare la verifica firma driver in produzione?**
Fortemente sconsigliato. La firma driver è un pilastro della sicurezza kernel di Windows. Disabilitarla espone il sistema a rootkit e driver malevoli. In produzione: mai usare `bcdedit /set testsigning on` o `bcdedit /set nointegritychecks on`. Se un driver legacy non firmato è indispensabile, isolarlo in una VM.

**Q8: Come funziona il rollback driver e quando è disponibile?**
Windows mantiene la versione precedente di un driver nel Driver Store. Il rollback è disponibile SOLO se esiste una versione precedente (Device Manager → Properties → Driver → Roll Back Driver). Non è disponibile dopo una reinstallazione pulita del OS. Per garantire il rollback: prima di aggiornare un driver, verificare che la versione corrente sia nel Driver Store con `pnputil /enum-drivers`.

**Q9: Qual è il modo migliore per distribuire driver in un ambiente con 50+ modelli hardware?**
Usare la struttura `\Vendor\Model\` e il metodo "Apply Driver Package" in SCCM con WMI query per ogni modello. Scaricare i driver pack dagli OEM (Dell Command Update, HP Client Management, Lenovo System Update). Per ambienti Intune: Windows Update for Business con approvazione manuale dei driver. Evitare "Auto Apply Drivers" in fleet eterogenei — troppo imprevedibile.

**Q10: Come gestire le shim di compatibilità in un ambiente WDAC?**
Le shim (SDB) devono essere firmate e distribuite prima dell'attivazione WDAC. I binari coinvolti nello shim devono essere autorizzati nella policy WDAC. Se l'Application Compatibility Engine è bloccato da WDAC, le shim non funzioneranno. Best practice: includere i SDB nella policy WDAC come file autorizzati tramite hash o publisher.

**Q11: Quanti driver possono essere staged nel Driver Store prima di avere problemi?**
Non c'è un limite rigido, ma il Driver Store può crescere oltre 10 GB con centinaia di driver staged. Il problema è lo spazio disco, non la funzionalità. Best practice: pulizia trimestrale dei driver obsoleti con `pnputil /delete-driver`. Monitorare la dimensione di `C:\Windows\System32\DriverStore\FileRepository\`.

**Q12: Come bloccare specifiche classi di dispositivi USB (solo storage) permettendo tutto il resto?**
Usare la GPO "Prevent installation of devices using drivers that match these device setup classes". La classe USB Mass Storage è `{36FC9E60-C465-11CF-8056-444553540000}`. Le classi HID (mouse/tastiera), Audio, e Video non vengono bloccate. Verificare con `Get-PnpDevice -Class USB | Select-Object Class, FriendlyName`.

**Q13: Che impatto ha HVCI sulle performance del sistema?**
L'impatto è generalmente minimo (1-5% su workload tipici). L'impatto maggiore si nota su carichi I/O intensivi e calcolo kernel-mode. Se un driver non è HVCI-compatible e viene bloccato, la funzionalità del dispositivo è persa. Misurare l'impatto con Performance Monitor prima e dopo l'abilitazione.

**Q14: Come migrare da Roaming Profiles + AppCompat shim a un ambiente moderno?**
(1) Migrare i profili a FSLogix (VHD container). (2) Convertire le app con shim in pacchetti MSIX dove possibile. (3) Per app che resistono alla conversione, mantenere gli SDB ma testarli con WDAC. (4) Per app irrecuperabili, virtualizzare con App-V o VM dedicata. Piano tipico: 6-12 mesi per un'organizzazione media.

**Q15: Windows Sandbox può sostituire una VM per il testing applicazioni?**
Solo parzialmente. Windows Sandbox è ideale per test rapidi usa-e-getta: verificare un installer, testare un'app sospetta, provare una configurazione. Non persiste tra le sessioni (tutto cancellato alla chiusura). Non supporta GPU passthrough, configurazioni di rete avanzate, o multi-monitor. Per test di compatibilità strutturati (settimane di test, multiple configurazioni): usare VM tradizionali (Hyper-V).

---

## Esercizi

### Domande a risposta aperta

**E1.** Un'azienda con 300 workstation distribuite su 12 modelli hardware diversi (Dell, HP, Lenovo) sta pianificando la migrazione da Windows 10 22H2 a Windows 11 24H2. Descrivere il processo completo di gestione driver per questa migrazione, includendo: inventario, acquisizione, test, staging e deploy. Specificare gli strumenti da utilizzare e le strategie per minimizzare il rischio di incompatibilità.

**E2.** Un sistema Windows 11 con HVCI abilitato segnala nell'Event Log (Event ID 3090) che un driver legacy di un dispositivo di acquisizione dati industriale è stato bloccato. Il dispositivo è critico per la produzione e il vendor originale non esiste più. Analizzare tutte le opzioni disponibili (da quella più sicura alla meno sicura) e motivare la scelta consigliata.

**E3.** Dopo aver abilitato una policy WDAC in modalità Enforce, diverse applicazioni LOB (Line of Business) smettono di funzionare. Descrivere il processo di diagnosi, la creazione di policy supplementari, e la strategia per passare da Audit a Enforce in modo graduale senza impattare la produttività.

**E4.** Un'organizzazione deve implementare il blocco dei dispositivi USB storage per conformità PCI-DSS, mantenendo il funzionamento di mouse, tastiere, webcam e stampanti USB. Progettare la configurazione GPO completa, includendo le eccezioni, e descrivere come testare la policy prima del rollout.

**E5.** Un team di sviluppo interno utilizza un'applicazione ERP legacy (sviluppata nel 2012 per Windows 7) che presenta i seguenti problemi su Windows 11: DPI scaling errato, errori di permesso nella scrittura in `C:\Program Files`, e crash quando interroga la versione del sistema operativo. Per ciascun problema, descrivere la causa tecnica e la soluzione appropriata (shim, manifest, compatibility mode, o altro).

### Vero / Falso

**V1.** I driver UMDF (User Mode Driver Framework) possono causare BSOD in caso di crash.
**Risposta:** Falso. I driver UMDF girano in user mode (Ring 3) e un loro crash non causa BSOD. Il processo UMDF host viene riavviato automaticamente.

**V2.** Su Windows 11 64-bit, un driver kernel-mode firmato solo con Authenticode standard (non WHQL/Attestation) può essere caricato normalmente.
**Risposta:** Falso. A partire da Windows 10 1607, i nuovi driver kernel-mode richiedono firma WHQL o Attestation tramite il Microsoft Partner Center. L'Authenticode standard è sufficiente solo per driver UMDF.

**V3.** Il comando `pnputil /export-driver * C:\Backup\` esporta sia i driver third-party che i driver inbox di Windows.
**Risposta:** Falso. `pnputil /export-driver *` esporta solo i driver OEM (third-party) presenti nel Driver Store. I driver inbox sono inclusi nel media di installazione Windows.

**V4.** La directory WinSxS (C:\Windows\WinSxS) può essere pulita manualmente eliminando le sottocartelle più vecchie per liberare spazio disco.
**Risposta:** Falso. La pulizia manuale di WinSxS può rendere il sistema instabile. La pulizia deve essere eseguita esclusivamente tramite DISM (`/StartComponentCleanup`) o Disk Cleanup, che gestiscono correttamente gli hardlink e le dipendenze.

**V5.** SR-IOV (Single Root I/O Virtualization) permette alle VM Hyper-V di accedere direttamente alla scheda di rete fisica, bypassando il virtual switch per prestazioni quasi native.
**Risposta:** Vero. SR-IOV espone Virtual Functions (VF) della NIC direttamente alle VM, eliminando l'overhead del virtual switch e del processamento nel host.

### Scenari pratici

**S1.** Un amministratore riceve un ticket: su 15 notebook HP EliteBook 840 G10, la webcam integrata non viene riconosciuta dopo un aggiornamento cumulativo di Windows 11. Device Manager mostra il dispositivo con Code 43. Descrivere passo per passo la diagnosi e la risoluzione, includendo i comandi PowerShell da eseguire.

**S2.** Un'azienda sta valutando l'adozione di Universal Print per eliminare i print server on-premises. Attualmente ha 50 stampanti di rete gestite da 3 print server Windows Server con driver v3. Analizzare: requisiti per la migrazione, vantaggi e limitazioni, e un piano di transizione graduale.

**S3.** Un driver di un controller RAID legacy (LSI MegaRAID, driver cross-signed 2018) funziona su Windows 10 ma non si carica su Windows 11 con Secure Boot e HVCI attivi. L'hardware è un server di produzione che non può essere sostituito a breve termine. Proporre una strategia di mitigazione che bilanci sicurezza e operatività.

**S4.** Durante il testing di un nuovo driver GPU NVIDIA su un PC di sviluppo, il sistema va in BSOD ripetutamente con il bug check `VIDEO_TDR_FAILURE (nvlddmkm.sys)`. Il PC non riesce ad avviarsi nemmeno in modalità normale. Descrivere l'intera procedura di recovery e diagnosi.

**S5.** Un'applicazione legacy a 32-bit richiede una specifica versione di Visual C++ 2008 Runtime (9.0.21022.8) che entra in conflitto con una versione più recente richiesta da un'altra applicazione sullo stesso sistema. Spiegare come il sistema SxS (Side-by-Side) dovrebbe gestire questa situazione e diagnosticare il caso in cui non funzioni correttamente.

---

## Auto-valutazione

| Competenza | Livello |
|---|---|
| Comprendere l'architettura WDM/WDF e scegliere KMDF vs UMDF | Base / Intermedio / Avanzato |
| Gestire il Driver Store con PnPUtil e DISM | Base / Intermedio / Avanzato |
| Configurare e verificare driver signing (WHQL, Attestation, KMCS) | Base / Intermedio / Avanzato |
| Diagnosticare BSOD da driver con Driver Verifier e WinDbg | Base / Intermedio / Avanzato |
| Configurare HVCI e verificare compatibilità driver | Base / Intermedio / Avanzato |
| Iniettare driver in immagini WIM e gestire deploy enterprise | Base / Intermedio / Avanzato |
| Creare e distribuire shim di compatibilità (SDB) | Base / Intermedio / Avanzato |
| Configurare GPO per controllo installazione driver | Base / Intermedio / Avanzato |
| Gestire WDAC con supplemental policies e managed installer | Base / Intermedio / Avanzato |
| Amministrare driver per classi specifiche (stampa, GPU, storage, rete, USB) | Base / Intermedio / Avanzato |
| Troubleshooting di compatibilità applicativa (SxS, API sets, DLL, manifest) | Base / Intermedio / Avanzato |

---

## Letture Primarie Consigliate

1. **Windows Driver Frameworks (WDF) documentation** — architettura KMDF/UMDF, ciclo di vita driver, best practice per lo sviluppo
   https://learn.microsoft.com/en-us/windows-hardware/drivers/wdf/ (consultato: 2026-05-23)

2. **Driver signing requirements** — requisiti firma per Windows 10/11, WHQL, Attestation, Partner Center
   https://learn.microsoft.com/en-us/windows-hardware/drivers/install/kernel-mode-code-signing-policy--windows-vista-and-later- (consultato: 2026-05-23)

3. **WDAC (Windows Defender Application Control)** — creazione policy, deployment, supplemental policies, managed installer
   https://learn.microsoft.com/en-us/windows/security/application-security/application-control/windows-defender-application-control/wdac (consultato: 2026-05-23)

4. **Driver Verifier** — opzioni, scenari di utilizzo, bug check codes
   https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/driver-verifier (consultato: 2026-05-23)

5. **Virtualization-Based Security (VBS) and HVCI** — architettura VTL, requisiti hardware, compatibilità driver
   https://learn.microsoft.com/en-us/windows/security/hardware-security/enable-virtualization-based-protection-of-code-integrity (consultato: 2026-05-23)

6. **PnPUtil command syntax** — riferimento completo per la gestione Driver Store da linea di comando
   https://learn.microsoft.com/en-us/windows-hardware/drivers/devtest/pnputil (consultato: 2026-05-23)

7. **DISM driver servicing** — aggiunta, rimozione ed elenco driver in immagini offline e online
   https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/add-and-remove-drivers-to-an-offline-windows-image (consultato: 2026-05-23)

8. **Application Compatibility Toolkit (ACT)** — shim database, Compatibility Administrator, process di test
   https://learn.microsoft.com/en-us/windows/deployment/planning/compatibility-administrator-users-guide (consultato: 2026-05-23)

9. **DLL search order and security** — ordine di ricerca, SafeDllSearchMode, mitigazioni DLL hijacking
   https://learn.microsoft.com/en-us/windows/win32/dlls/dynamic-link-library-search-order (consultato: 2026-05-23)

10. **Universal Print** — architettura cloud, requisiti, configurazione connector, integrazione Intune
    https://learn.microsoft.com/en-us/universal-print/ (consultato: 2026-05-23)

11. **NDIS drivers and network driver development** — versioni NDIS, NetAdapterCx, SR-IOV, RSS
    https://learn.microsoft.com/en-us/windows-hardware/drivers/network/ (consultato: 2026-05-23)

12. **USB driver development** — USB driver stack, Type-C, class drivers, USBX
    https://learn.microsoft.com/en-us/windows-hardware/drivers/usbcon/ (consultato: 2026-05-23)

---

## Collegamenti Incrociati

| Modulo | Relazione con questo modulo |
|---|---|
| `12-endpoint-management.md` | Deploy driver enterprise tramite MDT, SCCM, Intune; driver update policies; compliance baselines per versioni driver |
| `19-troubleshooting.md` | Diagnosi BSOD e crash dump analysis; WinDbg per analisi driver; Event Log per errori PnP e CodeIntegrity |
| `23-hyper-v-guida-completa.md` | GPU-P e GPU-PV per VM; SR-IOV per NIC virtuali; driver storage per VHD/VHDX; HVCI e VBS come dipendenze Hyper-V |

---

## Glossario Locale

| Termine | Definizione |
|---|---|
| **ACT** | Application Compatibility Toolkit — set di strumenti per creare fix di compatibilità (shim) per app legacy |
| **API Set** | Contratto DLL virtuale (`api-ms-win-*`) che il loader Windows risolve alla DLL reale al runtime, consentendo ristrutturazioni interne trasparenti |
| **Attestation Signing** | Processo per cui Microsoft firma un driver kernel-mode caricato su Partner Center senza eseguire test HLK completi |
| **CAT (Catalog file)** | File `.cat` che contiene gli hash firmati di tutti i file in un pacchetto driver; Windows verifica la firma del catalogo prima di caricare il driver |
| **Cross-signing** | Meccanismo legacy (deprecato) che permetteva ai vendor di firmare driver kernel-mode tramite CA autorizzate da Microsoft |
| **DLL Hijacking** | Attacco in cui un attaccante posiziona una DLL malevola in una directory ad alta priorità nell'ordine di ricerca DLL, facendola caricare al posto della DLL legittima |
| **GPU-P / GPU-PV** | GPU Partitioning / GPU Paravirtualization — tecnologie per condividere una GPU fisica tra host Hyper-V e VM |
| **HVCI** | Hypervisor-protected Code Integrity — verifica firma driver eseguita in VTL 1 (Secure World), impossibile da bypassare anche con exploit kernel |
| **INF** | File di setup driver (`.inf`) che descrive l'hardware supportato, i file da copiare e le chiavi registry da creare |
| **KMCS** | Kernel-Mode Code Signing — policy Windows che impone la firma digitale per tutti i driver caricati in kernel mode |
| **KMDF** | Kernel Mode Driver Framework — framework WDF per driver kernel-mode (accesso diretto hardware, crash = BSOD) |
| **Miniport** | Driver che implementa funzionalità specifiche dell'hardware, operando insieme a un port driver fornito da Microsoft |
| **NDIS** | Network Driver Interface Specification — framework per i driver di rete su Windows |
| **NetAdapterCx** | Nuovo framework WDF per driver di rete, sostituto del modello NDIS miniport tradizionale |
| **PnPUtil** | Utilità command-line per la gestione del Driver Store Windows (staging, installazione, rimozione, export driver) |
| **PrintNightmare** | CVE-2021-34527 — vulnerabilità critica nel servizio Print Spooler che permetteva RCE e privilege escalation tramite Point and Print |
| **RSS** | Receive Side Scaling — distribuzione del processing dei pacchetti di rete in ingresso su più core CPU |
| **SDB** | Shim Database — file compilato contenente fix di compatibilità (shim) per applicazioni legacy, installabile con `sdbinst` |
| **Shim** | Intercettore di chiamate API che modifica il comportamento di un'applicazione senza alterarne il binario |
| **SR-IOV** | Single Root I/O Virtualization — tecnologia che espone Virtual Functions della NIC direttamente alle VM per performance quasi native |
| **Storport** | Port driver moderno per storage Windows, ottimizzato per SSD e NVMe, sostituto di SCSI Port |
| **SxS** | Side-by-Side — meccanismo che permette la coesistenza di versioni multiple della stessa DLL (WinSxS store) |
| **UAC (USB Audio Class)** | Specifica USB per dispositivi audio; Windows include driver class inbox per UAC 1.0 e 2.0 |
| **UCM** | USB Connector Manager — driver per la gestione dei connettori USB Type-C (orientamento, PD, alternate mode) |
| **UMDF** | User Mode Driver Framework — framework WDF per driver user-mode (crash non causa BSOD, sandbox) |
| **VBS** | Virtualization-Based Security — uso dell'hypervisor Hyper-V per creare ambienti isolati (VTL 0/1) per la protezione del kernel |
| **VMQ** | Virtual Machine Queue — assegnazione di code hardware NIC dedicate alle VM Hyper-V |
| **WDAC** | Windows Defender Application Control — controllo a livello kernel su quali binari possono essere eseguiti |
| **WDDM** | Windows Display Driver Model — modello driver per GPU/display; la versione corrente determina il supporto DirectX e Shader Model |
| **WDF** | Windows Driver Frameworks — framework moderno (KMDF + UMDF) che sostituisce WDM per lo sviluppo di driver Windows |
| **WDM** | Windows Driver Model — modello driver legacy IRP-based, ancora usato da driver vecchi ma sostituito da WDF per nuovi sviluppi |
| **WHQL** | Windows Hardware Quality Labs — programma di certificazione Microsoft in cui il driver viene testato e firmato |
| **WinSxS** | Windows Side-by-Side store (`C:\Windows\WinSxS`) — repository di tutte le versioni dei componenti Windows e shared assemblies |
