# Troubleshooting Windows — Guida Completa

> **Modulo 19** · **Aggiornamento:** 2026-05-23

| Campo | Valore |
|---|---|
| **Corso** | Windows per ingegneri di sistema |
| **Fase** | Diagnosi e risoluzione dei problemi |
| **Modulo del corso** | 19 — Troubleshooting Windows |
| **Versioni di riferimento** | Windows 11 24H2, Windows Server 2025, Sysinternals Suite 2024+, WinDbg Preview |
| **Livello** | Proficient |
| **Prerequisiti** | Amministrazione Active Directory (→ `01-active-directory.md`), PowerShell operativo (→ `02-powershell.md`), networking Windows (→ `06-rete-windows.md`) |
| **Obiettivi di apprendimento** | 1) Applicare una metodologia di troubleshooting strutturata con alberi decisionali · 2) Analizzare Event Viewer (Application, Security, System) e Reliability Monitor per identificare cause root · 3) Utilizzare Sysinternals (Procmon, Procdump, Autoruns) per la diagnosi avanzata di processi, servizi e boot · 4) Diagnosticare BSOD tramite analisi di minidump con WinDbg · 5) Risolvere problemi di GPO, DNS, rete, performance e certificati in ambienti enterprise |
| **Tempo stimato** | lettura 120 min · lab 150 min |
| **Ultimo aggiornamento** | 2026-05-23 |

## Idee guida
1. **Event Viewer first stop.** Application/Security/System.**
2. **Reliability Monitor for OS health timeline.**
3. **`gpresult /h` triage GPO precedence.**
4. **Sysinternals tools (Procmon, Procdump, Autoruns) essential.**


## Indice

- [Panoramica](#panoramica)
- [Metodologia di Troubleshooting](#metodologia-di-troubleshooting)
- [BSOD — Blue Screen of Death](#bsod--blue-screen-of-death)
- [Problemi di Boot](#problemi-di-boot)
- [Windows Update — Diagnosi e Riparazione](#windows-update--diagnosi-e-riparazione)
- [Troubleshooting Active Directory](#troubleshooting-active-directory)
- [Troubleshooting Group Policy (GPO)](#troubleshooting-group-policy-gpo)
- [Troubleshooting DNS](#troubleshooting-dns)
- [Troubleshooting Rete](#troubleshooting-rete)
- [Troubleshooting Performance](#troubleshooting-performance)
- [Troubleshooting Servizi e Applicazioni](#troubleshooting-servizi-e-applicazioni)
- [Problemi di Stampa](#problemi-di-stampa)
- [Problemi Profili Utente](#problemi-profili-utente)
- [Problemi Certificati](#problemi-certificati)
- [Troubleshooting Hyper-V](#troubleshooting-hyper-v)
- [Troubleshooting Cluster](#troubleshooting-cluster)
- [WinRE e Recovery Environment](#winre-e-recovery-environment)
- [Troubleshooting Remoto](#troubleshooting-remoto)
- [Strumenti Sysinternals](#strumenti-sysinternals)
- [Script PowerShell Diagnostici](#script-powershell-diagnostici)
- [Scenari Avanzati — 30+ Casi](#scenari-avanzati--30-casi)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)
- [Quick Reference — Comandi Diagnostici](#quick-reference--comandi-diagnostici)

---

## Panoramica

Il troubleshooting efficace segue un metodo sistematico: identificare il sintomo, raccogliere dati, isolare la causa, applicare la soluzione, verificare e documentare. Gli strumenti principali sono: Event Viewer, Performance Monitor, Sysinternals Suite, PowerShell e WinDbg.

Questo modulo copre la diagnosi e la risoluzione dei problemi su Windows Client e Server in ambienti enterprise. Ogni sezione fornisce: contesto teorico, comandi diagnostici, cause comuni, procedure di risoluzione e script di automazione.

### Principi fondamentali del troubleshooting

```
┌─────────────────────────────────────────────────────┐
│              TROUBLESHOOTING MINDSET                │
├─────────────────────────────────────────────────────┤
│  1. NON CAMBIARE PIÙ DI UNA COSA ALLA VOLTA        │
│  2. DOCUMENTARE OGNI PASSO (log, screenshot, note)  │
│  3. RACCOGLIERE DATI PRIMA DI AGIRE                 │
│  4. IL PROBLEMA PIÙ SEMPLICE È QUASI SEMPRE GIUSTO  │
│  5. VERIFICARE CHE LA FIX FUNZIONI + NO SIDE-EFFECT │
│  6. ROLLBACK PLAN PRIMA DI OGNI MODIFICA             │
└─────────────────────────────────────────────────────┘
```

### Strumenti diagnostici essenziali

| Strumento | Uso primario | Accesso |
|-----------|-------------|---------|
| Event Viewer | Log di sistema, applicazione, security | `eventvwr.msc` |
| Performance Monitor | Contatori CPU, RAM, disco, rete | `perfmon.msc` |
| Reliability Monitor | Timeline stabilità OS | `perfmon /rel` |
| Resource Monitor | Uso risorse real-time per processo | `resmon.exe` |
| WinDbg | Analisi crash dump, kernel debugging | Microsoft Store / WDK |
| Sysinternals Suite | Diagnostica avanzata processi, rete, I/O | `\\live.sysinternals.com\tools\` |
| PowerShell | Automazione, query, diagnostica scriptabile | Built-in |
| Task Manager | Quick overview risorse e processi | `Ctrl+Shift+Esc` |
| `msconfig` | Boot configuration, servizi, startup | `msconfig.exe` |
| `msinfo32` | Riepilogo completo hardware e software | `msinfo32.exe` |

---

## Metodologia di Troubleshooting

```
1. IDENTIFICARE IL PROBLEMA
   → Cosa non funziona? Da quando? Per chi? Sempre o intermittente?
   → Cosa è cambiato? (aggiornamenti, configurazioni, hardware)
   → Qual è l'impatto? (un utente, tutti, un servizio)

2. RACCOGLIERE DATI
   → Event Viewer (System, Application, Security)
   → Performance Monitor
   → Log applicazione specifici
   → Screenshot dell'errore
   → Output comandi diagnostici

3. FORMULARE IPOTESI
   → Basandosi sui dati, qual è la causa più probabile?
   → Elencare le possibilità in ordine di probabilità

4. TESTARE
   → Verificare l'ipotesi con un test mirato
   → Un cambiamento alla volta
   → Se non risolve, tornare al punto 3

5. RISOLVERE
   → Applicare la soluzione
   → Verificare che il problema sia risolto
   → Verificare che non ci siano effetti collaterali

6. DOCUMENTARE
   → Problema, causa, soluzione, tempo impiegato
   → Knowledge base per il futuro
```

### Tecniche di isolamento avanzate

#### Binary Search (Ricerca Binaria)

La tecnica binary search è efficace quando il problema potrebbe risiedere in uno di molti componenti. Invece di testarli uno ad uno (O(n)), si dimezza l'insieme ad ogni passo (O(log n)).

```
ESEMPIO: 20 servizi attivi, uno causa crash periodici

Passo 1: Disabilitare metà dei servizi (11-20) → Problema persiste?
  SÌ → Il problema è nei servizi 1-10
  NO → Il problema è nei servizi 11-20

Passo 2: Dimezzare ancora il sottoinsieme
  Se 1-10: disabilitare 6-10 → Problema persiste?
  SÌ → Servizi 1-5
  NO → Servizi 6-10

Passo 3: Continuare finché non si isola il singolo servizio
  3-4 iterazioni bastano per 20 elementi
```

```powershell
# Esempio pratico: identificare un driver che causa instabilità
# 1. Avviare in Safe Mode (carica set minimo di driver)
# Se in Safe Mode funziona → il problema è un driver terze parti

# 2. Elencare driver non-Microsoft
Get-WindowsDriver -Online | Where-Object {
    $_.ProviderName -ne "Microsoft" -and
    $_.BootCritical -eq $false
} | Select-Object ClassName, ProviderName, Driver, Date |
    Sort-Object ClassName

# 3. Disabilitare gruppi di driver con Device Manager
#    Dimezzare: prima metà dei dispositivi → test → seconda metà → test
```

#### Last Known Good Configuration

```powershell
# Windows memorizza l'ultimo ControlSet che ha completato il boot con successo
# Registry: HKLM\SYSTEM\Select
# CurrentControlSet → quello attuale
# LastKnownGood → l'ultimo che ha funzionato

# Verificare quale ControlSet è attivo
Get-ItemProperty "HKLM:\SYSTEM\Select"
# Current: 1 → usa ControlSet001
# LastKnownGood: 2 → ControlSet002 era l'ultimo boot riuscito

# In WinRE: bcdedit per forzare LastKnownGood
bcdedit /set {default} lastknowngood Yes
```

#### Tecnica di isolamento per ambienti

```
ISOLAMENTO UTENTE
→ Il problema si verifica con un altro utente sullo stesso PC?
  SÌ → Problema del sistema/hardware
  NO → Problema del profilo utente o delle sue policy

ISOLAMENTO PC
→ Il problema si verifica sullo stesso utente su un altro PC?
  SÌ → Problema dell'account (AD, GPO, roaming profile)
  NO → Problema specifico di quel PC

ISOLAMENTO RETE
→ Il problema si verifica con connessione diretta (no switch/VPN)?
  SÌ → Problema non è la rete
  NO → Problema di rete (firewall, switch, routing)

ISOLAMENTO SOFTWARE
→ Il problema si verifica in Safe Mode?
  SÌ → Problema di OS/hardware
  NO → Problema di driver o software terze parti

ISOLAMENTO TEMPORALE
→ Il problema si verifica a orari specifici?
  SÌ → Scheduled task, backup, scansione antivirus, manutenzione
  NO → Problema costante → cercare nei log l'evento trigger
```

#### Raccolta strutturata dei dati

```powershell
# Script di raccolta dati iniziale — da eseguire all'inizio del troubleshooting
$LogPath = "C:\TroubleshootLogs\$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -Path $LogPath -ItemType Directory -Force

# 1. Info sistema
msinfo32 /report "$LogPath\systeminfo.txt"
systeminfo > "$LogPath\systeminfo_cmd.txt"

# 2. Event Log recenti (ultime 24 ore)
$Yesterday = (Get-Date).AddHours(-24)
Get-WinEvent -LogName System -MaxEvents 500 |
    Where-Object { $_.TimeCreated -gt $Yesterday -and $_.Level -le 2 } |
    Export-Csv "$LogPath\EventLog_System_Errors.csv" -NoTypeInformation

Get-WinEvent -LogName Application -MaxEvents 500 |
    Where-Object { $_.TimeCreated -gt $Yesterday -and $_.Level -le 2 } |
    Export-Csv "$LogPath\EventLog_App_Errors.csv" -NoTypeInformation

# 3. Servizi in stato anomalo
Get-Service | Where-Object {
    $_.StartType -eq 'Automatic' -and $_.Status -ne 'Running'
} | Export-Csv "$LogPath\Services_NotRunning.csv" -NoTypeInformation

# 4. Stato disco
Get-Volume | Export-Csv "$LogPath\Volumes.csv" -NoTypeInformation
Get-PhysicalDisk | Export-Csv "$LogPath\PhysicalDisks.csv" -NoTypeInformation

# 5. Rete
Get-NetIPConfiguration | Out-File "$LogPath\NetConfig.txt"
Get-NetAdapter | Out-File "$LogPath\NetAdapters.txt"

# 6. Processi e risorse
Get-Process | Sort-Object CPU -Descending |
    Select-Object -First 20 Name, Id, CPU,
    @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB)}} |
    Export-Csv "$LogPath\TopProcesses.csv" -NoTypeInformation

Write-Host "Dati raccolti in: $LogPath" -ForegroundColor Green
```

### Reliability Monitor

```powershell
# Reliability Monitor: timeline grafica di stabilità del sistema
# Accessibile da: perfmon /rel
# Mostra:
#   - Crash applicazioni
#   - Crash Windows (BSOD)
#   - Installazioni/disinstallazioni software
#   - Aggiornamenti Windows
#   - Cambiamenti driver
#   - Indice di stabilità (1-10)

# Consultare Reliability Monitor via PowerShell
Get-CimInstance Win32_ReliabilityStabilityMetrics |
    Select-Object TimeGenerated, SystemStabilityIndex |
    Sort-Object TimeGenerated -Descending |
    Select-Object -First 14

# Recuperare eventi di instabilità recenti
Get-CimInstance Win32_ReliabilityRecords |
    Where-Object { $_.EventIdentifier -ne $null } |
    Select-Object -First 20 TimeGenerated, SourceName, EventIdentifier, Message
```

---

## BSOD — Blue Screen of Death

### Analisi BSOD

```powershell
# I BSOD generano un crash dump in: C:\Windows\MEMORY.DMP (o Minidump)

# Verificare configurazione dump
Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\CrashControl" |
    Select-Object CrashDumpEnabled, DumpFile, MinidumpDir
# CrashDumpEnabled: 1=Complete, 2=Kernel, 3=Small (minidump), 7=Automatic

# BSOD comuni e cause:

# IRQL_NOT_LESS_OR_EQUAL (0x0A)
# → Driver buggy accede a memoria a IRQL elevato
# → Soluzione: identificare il driver (WinDbg), aggiornare/rimuovere

# SYSTEM_SERVICE_EXCEPTION (0x3B)
# → Eccezione non gestita in un servizio di sistema
# → Causa comune: driver GPU, antivirus, virtualizzazione

# KERNEL_DATA_INPAGE_ERROR (0x7A)
# → Errore lettura pagina dal disco/paging file
# → Causa: disco guasto, settori danneggiati, cavo SATA difettoso
# → Controllare: chkdsk /r, SMART status del disco

# PAGE_FAULT_IN_NONPAGED_AREA (0x50)
# → Accesso a memoria non paginata non valida
# → Causa: RAM difettosa, driver corrotto
# → Test: Windows Memory Diagnostic (mdsched.exe)

# CRITICAL_PROCESS_DIED (0xEF)
# → Un processo di sistema critico si è fermato
# → Causa: file di sistema corrotti, disco, malware
# → Soluzione: sfc /scannow, DISM /RestoreHealth

# Analisi con WinDbg:
# 1. Installare WinDbg (dal Microsoft Store o Windows SDK)
# 2. File → Open Crash Dump → C:\Windows\MEMORY.DMP
# 3. Configurare symbol path: srv*C:\Symbols*https://msdl.microsoft.com/download/symbols
# 4. Eseguire: !analyze -v
# Output mostra: il modulo responsabile, lo stack trace, l'istruzione che ha causato il crash

# Analisi rapida con PowerShell
Get-WinEvent -LogName System | Where-Object {
    $_.ProviderName -eq "Microsoft-Windows-WER-SystemErrorReporting"
} | Select-Object -First 5 TimeCreated, Message

# BlueScreenView (NirSoft) — tool gratuito per analisi rapida minidump
```

### Analisi dettagliata con WinDbg

```powershell
# === GUIDA APPROFONDITA WinDbg ===

# INSTALLAZIONE
# Opzione 1: Microsoft Store → "WinDbg Preview" (consigliato)
# Opzione 2: Windows SDK → selezionare solo "Debugging Tools for Windows"

# CONFIGURAZIONE SYMBOL PATH
# Menu: File → Settings → Debugging Settings → Default Symbol Path
# Valore: srv*C:\Symbols*https://msdl.microsoft.com/download/symbols
# Oppure da command line WinDbg:
# .sympath srv*C:\Symbols*https://msdl.microsoft.com/download/symbols
# .reload

# APERTURA CRASH DUMP
# File → Open Dump File → C:\Windows\MEMORY.DMP
# Oppure Minidump: C:\Windows\Minidump\MMDDYY-NNNNN.dmp

# COMANDI WinDbg ESSENZIALI
#
# !analyze -v
#   Analisi automatica completa del crash
#   Output chiave:
#     BUGCHECK_CODE: il codice di stop (es. 0x3B)
#     BUGCHECK_P1-P4: parametri dello stop code
#     IMAGE_NAME: modulo sospettato (es. ntfs.sys, nvlddmkm.sys)
#     MODULE_NAME: nome del driver/modulo
#     FAILURE_BUCKET_ID: bucket per raggruppare crash simili
#     STACK_TEXT: call stack al momento del crash
#
# !process 0 0
#   Elenco di tutti i processi al momento del crash
#
# !thread
#   Dettagli del thread che ha causato il crash
#
# !pool
#   Analisi pool memory (per POOL_CORRUPTION)
#
# lm t n
#   Lista moduli caricati con timestamp (utile per driver datati)
#
# .logopen C:\debug_output.txt
#   Salva l'output su file per analisi successiva
#
# k
#   Stack trace corrente
#
# !irp
#   Analisi I/O Request Packet (per problemi storage/filesystem)

# INTERPRETAZIONE DELLO STACK TRACE
#
# Esempio di output !analyze -v:
# STACK_TEXT:
# fffff800`12345678 nt!KeBugCheckEx
# fffff800`12345680 nt!KiBugCheckDispatch+0x69
# fffff800`12345690 driver_terze_parti!DriverEntry+0x1a3
# fffff800`123456a0 nt!IopLoadDriver+0x4c2
#
# Interpretazione:
# - nt! = componente kernel Windows (normalmente NON è la causa)
# - driver_terze_parti! = IL COLPEVOLE: modulo terze parti
# - DriverEntry = la funzione del driver che ha causato il crash
# - Cercare il nome del modulo (es: nvlddmkm.sys = NVIDIA GPU driver)
```

### Catalogo Stop Code completo

```
STOP CODE                          HEX     CAUSA TIPICA                          AZIONE
─────────────────────────────────────────────────────────────────────────────────────
IRQL_NOT_LESS_OR_EQUAL             0x0A    Driver accede a memoria invalida      WinDbg → identifica driver → aggiorna
KMODE_EXCEPTION_NOT_HANDLED        0x1E    Eccezione kernel non gestita          WinDbg → stack trace → identifica modulo
NTFS_FILE_SYSTEM                   0x24    Corruzione filesystem NTFS            chkdsk /r → verifica disco SMART
FAT_FILE_SYSTEM                    0x23    Corruzione filesystem FAT             chkdsk /r su volume FAT
KERNEL_MODE_EXCEPTION_NOT_HANDLED  0x8E    Eccezione trap in kernel mode         WinDbg → driver terze parti?
SYSTEM_SERVICE_EXCEPTION           0x3B    Eccezione in servizio sistema         Driver GPU/AV/VT → aggiorna
SYSTEM_THREAD_EXCEPTION            0x7E    Eccezione thread di sistema           WinDbg → modulo nel backtrace
PAGE_FAULT_IN_NONPAGED_AREA        0x50    Accesso memoria non paginata          RAM test → driver corrotto
KERNEL_DATA_INPAGE_ERROR           0x7A    Errore lettura da disco/paging        Disco SMART → cavo SATA → chkdsk
CRITICAL_PROCESS_DIED              0xEF    Processo critico terminato            sfc → DISM → malware scan
UNEXPECTED_KERNEL_MODE_TRAP        0x7F    Trap inatteso kernel mode             Hardware (RAM/CPU overheating)
DRIVER_IRQL_NOT_LESS_OR_EQUAL      0xD1    Driver specifico + IRQL              Identifica driver → rimuovi/aggiorna
UNMOUNTABLE_BOOT_VOLUME            0xED    Volume di boot non montabile          chkdsk /r → ricostruisci BCD
INACCESSIBLE_BOOT_DEVICE           0x7B    Device di boot non accessibile        Controller BIOS → driver storage
WHEA_UNCORRECTABLE_ERROR           0x124   Errore hardware non correggibile      RAM/CPU/GPU/PSU → diagnostica HW
CLOCK_WATCHDOG_TIMEOUT             0x101   CPU core non risponde in tempo        Firmware → driver chipset → BIOS
DPC_WATCHDOG_VIOLATION             0x133   DPC routine troppo lunga              Driver storage/rete → firmware SSD
VIDEO_TDR_FAILURE                  0x116   Timeout Detection Recovery GPU        Driver GPU → PSU → surriscaldamento
MEMORY_MANAGEMENT                  0x1A    Errore gestione memoria               RAM test → pagefile → driver
BAD_POOL_HEADER                    0x19    Corruzione pool header                RAM → driver → malware
POOL_CORRUPTION_IN_FILE_AREA       0xDE    Corruzione pool in area file          Driver filesystem → filter driver
DRIVER_VERIFIER_DETECTED_VIOLATION 0xC4    Driver Verifier ha trovato bug        Il driver sotto test è buggy
KERNEL_SECURITY_CHECK_FAILURE      0x139   Stack buffer overflow rilevato        Driver/componente con buffer overflow
PFN_LIST_CORRUPT                   0x4E    Page Frame Number corrotto            RAM difettosa → driver
UNEXPECTED_STORE_EXCEPTION         0x154   Eccezione store inattesa              Disco/SSD → driver storage
HYPERVISOR_ERROR                   0x20001 Errore hypervisor                     Hyper-V config → firmware CPU
```

### Prevenire BSOD

```powershell
# 1. Aggiornare driver (specialmente GPU, storage, NIC)
# 2. Test RAM: mdsched.exe → Restart and check
# 3. Verificare disco: chkdsk C: /r (da WinRE o al reboot)
# 4. Verificare file sistema: sfc /scannow
# 5. Driver Verifier in ambiente test per identificare driver instabili
# 6. Monitorare temperature hardware

# === DRIVER VERIFIER — USO AVANZATO ===

# Abilitare Driver Verifier per driver specifici (NON usare su tutti!)
verifier /standard /driver driver1.sys driver2.sys

# Verificare stato Driver Verifier
verifier /query

# Disabilitare (DOPO il test — richiede reboot)
verifier /reset

# ATTENZIONE: Driver Verifier CAUSA BSOD di proposito se trova un bug
# Usare SOLO in ambiente test/lab, MAI in produzione senza piano di rollback

# === WINDOWS MEMORY DIAGNOSTIC (mdsched.exe) ===
# Due passaggi disponibili:
# Standard: test base (rapido)
# Extended: test approfondito (può richiedere ore)

# Avviare:
mdsched.exe
# → Restart now and check for problems
# → Check for problems the next time I start my computer

# Risultati: Event Viewer → System → Source: MemoryDiagnostics-Results

# Alternativa più approfondita: MemTest86 (boot da USB, più accurato)

# === MONITORAGGIO PROATTIVO BSOD ===

# Contare BSOD negli ultimi 30 giorni
$Start = (Get-Date).AddDays(-30)
Get-WinEvent -FilterHashtable @{
    LogName = 'System'
    ProviderName = 'Microsoft-Windows-WER-SystemErrorReporting'
    StartTime = $Start
} -ErrorAction SilentlyContinue | Measure-Object | Select-Object Count

# Elencare tutti i minidump disponibili
Get-ChildItem "C:\Windows\Minidump" -ErrorAction SilentlyContinue |
    Select-Object Name, CreationTime, Length |
    Sort-Object CreationTime -Descending

# Configurare dump completo (per analisi più dettagliata)
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\CrashControl" `
    -Name "CrashDumpEnabled" -Value 1 -Type DWord
# 1=Complete dump — richiede pagefile >= RAM fisica su C:
```

---

## Problemi di Boot

### Diagnosi Boot

```powershell
# Boot process Windows:
# 1. UEFI/BIOS → POST → Boot device
# 2. Boot Manager (bootmgr) → BCD (Boot Configuration Data)
# 3. Windows Loader (winload.efi) → Kernel (ntoskrnl.exe)
# 4. Session Manager (smss.exe) → Winlogon → Desktop

# Accedere a WinRE:
# - Tenere Shift durante click su Restart
# - Boot da media di installazione → Repair your computer
# - Dopo 3 boot falliti consecutivi, WinRE si avvia automaticamente

# Riparare Boot Manager
# Da WinRE → Command Prompt:
bootrec /fixmbr          # Ripara MBR (legacy BIOS)
bootrec /fixboot         # Ripara boot sector
bootrec /rebuildbcd      # Ricostruisce BCD

# Per UEFI:
bcdboot C:\Windows /s S: /f UEFI
# Dove S: è la partizione EFI (System)

# Verificare BCD
bcdedit /enum all        # Elencare tutte le entry
bcdedit /set {default} recoveryenabled Yes

# Boot in Safe Mode (da WinRE)
bcdedit /set {default} safeboot minimal       # Safe Mode
bcdedit /set {default} safeboot network       # Safe Mode with Networking
bcdedit /deletevalue {default} safeboot       # Tornare a boot normale

# Startup Repair (automatico)
# WinRE → Troubleshoot → Advanced → Startup Repair
```

### Problemi Specifici

```powershell
# "BOOTMGR is missing"
# → Partizione System corrotta o mancante
# → Da WinRE: bootrec /fixmbr && bootrec /fixboot && bootrec /rebuildbcd

# "Inaccessible Boot Device" (0x7B)
# → Driver storage controller mancante o corrotto
# → Controller mode cambiato in BIOS (AHCI ↔ RAID)
# → Da WinRE: DISM /Image:C:\ /Add-Driver /Driver:path

# "Your PC ran into a problem" loop
# → WinRE → Troubleshoot → Advanced:
#   1. Startup Repair (primo tentativo)
#   2. Safe Mode (disinstallare ultimo aggiornamento/driver)
#   3. System Restore (se disponibile)
#   4. Reset this PC (mantieni i file)
#   5. BMR da backup (ultimo resort)

# Disinstallare ultimo aggiornamento da WinRE
# Troubleshoot → Advanced → Uninstall Updates
# → Uninstall latest quality update
# → Uninstall latest feature update
```

### Boot diagnostico avanzato

```powershell
# === BOOT LOG ===
# Abilitare il boot log per registrare tutti i driver caricati
bcdedit /set {default} bootlog Yes
# Dopo il riavvio: C:\Windows\ntbtlog.txt
# Contiene: "Loaded driver" e "Did not load driver" per ogni modulo
# Utile per identificare driver che falliscono il caricamento

# Disabilitare dopo l'analisi:
bcdedit /deletevalue {default} bootlog

# === BOOT TIMING ===
# Analizzare tempi di boot con Event Viewer
# Log: Microsoft-Windows-Diagnostics-Performance/Operational
# Event ID 100: Windows Boot Performance → durata totale boot
# Event ID 101: Applicazione che rallenta il boot → nome, durata

Get-WinEvent -LogName "Microsoft-Windows-Diagnostics-Performance/Operational" `
    -MaxEvents 20 | Where-Object { $_.Id -in 100, 101, 102 } |
    Select-Object TimeCreated, Id, Message

# === PARTIZIONE EFI — RICOSTRUZIONE MANUALE ===

# Da WinRE Command Prompt:
diskpart
list disk
select disk 0
list partition
# Identificare la partizione EFI (Type: System, ~100-500MB, FAT32)
# Se mancante o corrotta:
select partition 1          # partizione EFI
assign letter=S
exit

# Ricostruire EFI boot files:
bcdboot C:\Windows /s S: /f UEFI /l it-IT

# Se la partizione EFI è completamente distrutta:
diskpart
select disk 0
create partition efi size=260
format fs=fat32 quick label="System"
assign letter=S
exit
bcdboot C:\Windows /s S: /f UEFI

# === BCD CORROTTO — RICOSTRUZIONE COMPLETA ===

# Da WinRE:
# 1. Rinominare il BCD corrotto
ren C:\Boot\BCD BCD.bak
# oppure (UEFI):
ren S:\EFI\Microsoft\Boot\BCD BCD.bak

# 2. Ricostruire
bootrec /rebuildbcd
# Se chiede di aggiungere installazioni trovate → premere Y

# 3. Se bootrec non trova installazioni:
bcdboot C:\Windows /s S: /f UEFI

# === SECURE BOOT — PROBLEMI ===
# Secure Boot impedisce il boot se i binari non sono firmati
# Errore: "Secure Boot violation" o boot loop

# Da UEFI/BIOS:
# 1. Verificare che Secure Boot sia abilitato
# 2. Se driver non firmato necessario → disabilitare temporaneamente Secure Boot
# 3. Da WinRE: bcdedit /set {default} nointegritychecks On (SOLO per debug)
# 4. Dopo risoluzione: bcdedit /set {default} nointegritychecks Off

# === STUCK AT "PREPARING AUTOMATIC REPAIR" ===
# 1. Forzare spegnimento (tenere power 10s) durante il loop
# 2. Al terzo tentativo WinRE si avvia
# 3. Se non si avvia → boot da USB di installazione
# 4. Da WinRE:
bcdedit /set {default} recoveryenabled No
# 5. Boot manuale → se funziona, il problema era Automatic Repair stesso
# 6. Riabilitare dopo fix: bcdedit /set {default} recoveryenabled Yes
```

---

## Windows Update — Diagnosi e Riparazione

### Analisi errori Windows Update

```powershell
# === CBS LOG (Component-Based Servicing) ===
# Il log primario di Windows Update
# Posizione: C:\Windows\Logs\CBS\CBS.log

# Ottenere il log WindowsUpdate consolidato (Win10/11):
Get-WindowsUpdateLog
# Genera: C:\Users\<user>\Desktop\WindowsUpdate.log
# Combina file ETL da C:\Windows\Logs\WindowsUpdate\ in formato leggibile

# Cercare errori nel CBS log:
Select-String -Path "C:\Windows\Logs\CBS\CBS.log" -Pattern "Error|FAIL|0x8" |
    Select-Object -Last 50

# === CODICI ERRORE COMUNI ===

# 0x80073712 — File manifesto CBS corrotto
# → DISM /Online /Cleanup-Image /RestoreHealth
# → sfc /scannow

# 0x800F0922 — Spazio insufficiente nella partizione System Reserved
# → Espandere la partizione o pulire file temporanei
# → Anche: VPN attiva durante update (disconnettere VPN)

# 0x80070002 — File mancante
# → net stop wuauserv && ren C:\Windows\SoftwareDistribution SoftwareDistribution.old
# → net start wuauserv

# 0x80240034 — WU non può risolvere il WSUS
# → Verificare configurazione WSUS in GPO
# → Verificare raggiungibilità del server WSUS

# 0x800F081F — Source file mancante per DISM
# → Specificare sorgente: DISM /Online /Cleanup-Image /RestoreHealth /Source:D:\sources\install.wim

# 0x80070005 — Accesso negato
# → Servizio BITS o WU non in esecuzione come SYSTEM
# → Permessi cartelle WU corrotti

# 0x8024402C — Connessione al server WU fallita
# → Proxy, firewall, o WSUS non raggiungibile

# === PROCEDURA DI RIPARAZIONE WINDOWS UPDATE ===

# LIVELLO 1: Reset soft
net stop wuauserv
net stop cryptSvc
net stop bits
net stop msiserver
ren C:\Windows\SoftwareDistribution SoftwareDistribution.old
ren C:\Windows\System32\catroot2 catroot2.old
net start wuauserv
net start cryptSvc
net start bits
net start msiserver

# LIVELLO 2: SFC + DISM
# Prima DISM (ripara il component store)
DISM /Online /Cleanup-Image /CheckHealth
DISM /Online /Cleanup-Image /ScanHealth
DISM /Online /Cleanup-Image /RestoreHealth

# Poi SFC (ripara file di sistema usando il component store riparato)
sfc /scannow
# Output: C:\Windows\Logs\CBS\CBS.log

# LIVELLO 3: Riregistrare DLL di Windows Update
$dlls = @(
    "atl.dll", "urlmon.dll", "mshtml.dll", "shdocvw.dll",
    "browseui.dll", "jscript.dll", "vbscript.dll", "scrrun.dll",
    "msxml.dll", "msxml3.dll", "msxml6.dll", "actxprxy.dll",
    "softpub.dll", "wintrust.dll", "dssenh.dll", "rsaenh.dll",
    "gpkcsp.dll", "sccbase.dll", "slbcsp.dll", "cryptdlg.dll",
    "oleaut32.dll", "ole32.dll", "shell32.dll",
    "wuaueng.dll", "wuaueng1.dll", "wucltui.dll",
    "wups.dll", "wups2.dll", "wuweb.dll", "qmgr.dll", "qmgrprxy.dll"
)
foreach ($dll in $dlls) {
    regsvr32 /s $dll
}

# LIVELLO 4: Installazione manuale
# Scaricare l'aggiornamento da Microsoft Update Catalog:
# https://www.catalog.update.microsoft.com
# Cercare il KB number → scaricare .msu → installare manualmente
wusa.exe C:\Temp\KB5012345.msu /quiet /norestart

# LIVELLO 5: In-Place Upgrade (ultimo resort prima di reinstallazione)
# Scaricare ISO di Windows → montare → setup.exe → "Keep everything"
# Ripara il component store completamente preservando dati e applicazioni
```

### Component Store e manutenzione

```powershell
# Analizzare dimensione component store (WinSxS)
DISM /Online /Cleanup-Image /AnalyzeComponentStore

# Pulire componenti sostituiti (non reversibile)
DISM /Online /Cleanup-Image /StartComponentCleanup
# Aggressivo (rimuove anche versioni precedenti non più necessarie):
DISM /Online /Cleanup-Image /StartComponentCleanup /ResetBase

# Verificare integrità componenti installati
DISM /Online /Cleanup-Image /CheckHealth    # rapido
DISM /Online /Cleanup-Image /ScanHealth     # approfondito (può richiedere minuti)

# Specificare sorgente alternativa per RestoreHealth
# Da ISO montata:
DISM /Online /Cleanup-Image /RestoreHealth /Source:D:\sources\install.wim
# Da WSUS (se configurato):
DISM /Online /Cleanup-Image /RestoreHealth /Source:wim:D:\sources\install.wim:1 /LimitAccess

# Elencare aggiornamenti installati
Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 20

# Elencare aggiornamenti in pending
Get-WindowsPackage -Online |
    Where-Object { $_.PackageState -eq "InstallPending" } |
    Select-Object PackageName, PackageState

# Verificare stato BITS (Background Intelligent Transfer Service)
Get-BitsTransfer -AllUsers | Select-Object DisplayName, JobState, BytesTransferred
```

---

## Troubleshooting Active Directory

```powershell
# DIAGNOSTICA COMPLETA
dcdiag /v /c /e > C:\Logs\dcdiag.txt       # Tutti i test, verbose, tutti i DC
dcdiag /test:replications /s:DC01            # Solo replica
dcdiag /test:dns /v /s:DC01                  # Solo DNS
dcdiag /test:services /s:DC01                # Servizi AD necessari

# REPLICA
repadmin /replsummary                        # Sommario replica
repadmin /showrepl DC01                      # Dettaglio replica per DC
repadmin /queue DC01                         # Operazioni in coda
repadmin /syncall DC01 /APed                 # Forza sincronizzazione completa

# PROBLEMI COMUNI AD

# "Cannot contact domain controller"
# 1. DNS: il client risolve il dominio? nslookup domain.com
# 2. Rete: ping al DC, Test-NetConnection DC01 -Port 389
# 3. Servizi DC: Get-Service NTDS, DNS, Netlogon sul DC
# 4. Firewall: porte AD aperte? (53, 88, 135, 389, 445, 636, 3268, 49152-65535)

# "Account lockout"
# Trovare la sorgente del lockout:
Get-WinEvent -ComputerName (Get-ADDomain).PDCEmulator -FilterHashtable @{
    LogName='Security'; Id=4740
} -MaxEvents 10 | ForEach-Object {
    [PSCustomObject]@{
        Time = $_.TimeCreated
        User = $_.Properties[0].Value
        SourceComputer = $_.Properties[1].Value
    }
}

# "SYSVOL non replicato"
# Verificare stato DFS-R:
Get-DfsrState -ComputerName DC01, DC02
dfsrdiag pollad

# Netlogon share test
net view \\DC01 /all
dir \\DC01\NETLOGON
dir \\DC01\SYSVOL

# Time sync (critico per Kerberos — max 5 min di differenza)
w32tm /query /status
w32tm /query /source
w32tm /resync /force
```

### Replication — Diagnostica approfondita

```powershell
# === REPADMIN — COMANDI AVANZATI ===

# Sommario globale errori di replica (tutti i DC)
repadmin /replsummary /bysrc /bydest /sort:delta

# Dettaglio replica per naming context specifico
repadmin /showrepl DC01 DC=domain,DC=com

# Mostrare metadata di un oggetto (per conflitti di replica)
repadmin /showobjmeta DC01 "CN=User1,OU=Users,DC=domain,DC=com"

# Mostrare la topologia KCC (Knowledge Consistency Checker)
repadmin /showconn DC01

# Verificare USN (Update Sequence Number) tra partner di replica
repadmin /showutdvec DC01 DC=domain,DC=com

# Forzare replica tra due DC specifici
repadmin /replicate DC02 DC01 DC=domain,DC=com

# Forzare replica di tutto verso tutti (emergenza)
repadmin /syncall DC01 /APed
# /A = All naming contexts
# /P = Push (notifica i partner)
# /e = Enterprise (tutti i siti)
# /d = Identifica i server per DN

# === ERRORI DI REPLICA COMUNI ===

# Errore 8606: Insufficient Attributes to Create Object
# → Oggetto lingering (fantasma) presente su un DC ma cancellato sugli altri
# → Soluzione: rimuovere lingering objects
repadmin /removelingeringobjects DC02 DC01_GUID DC=domain,DC=com /advisory_mode
# Prima in advisory_mode (solo report), poi senza (rimuove)
repadmin /removelingeringobjects DC02 DC01_GUID DC=domain,DC=com

# Errore 8524: The DSA operation is unable to proceed because of a DNS lookup failure
# → DC non riesce a risolvere il partner via DNS
# → Verificare: nslookup DC01.domain.com
# → Verificare: record CNAME dell'NTDS Settings GUID in DNS

# Errore 8453: Replication access was denied
# → Permessi AD rotti sul naming context
# → Verificare: ACL su domainDNS object
# → Reset con: dsacls "DC=domain,DC=com" /G "Enterprise Domain Controllers":GR

# Errore 1256: The remote system is not available
# → DC partner offline o non raggiungibile
# → Verificare: rete, firewall, servizio NTDS sul partner

# Errore 8614: The Active Directory cannot replicate with this server
#   because the time since the last replication exceeded the tombstone lifetime
# → CRITICO: dati potenzialmente persi
# → Il DC è stato offline più del Tombstone Lifetime (default: 180 giorni)
# → Soluzione: demote il DC e promuoverlo nuovamente
```

### Kerberos — Problemi e soluzioni

```powershell
# === ERRORI KERBEROS COMUNI ===

# KRB_AP_ERR_SKEW — Clock skew troppo grande (>5 min)
# Diagnostica:
w32tm /query /status                         # Stato sincronizzazione locale
w32tm /stripchart /computer:DC01.domain.com  # Differenza con il DC
w32tm /resync /force                         # Forza risincronizzazione

# Configurare gerarchia NTP corretta:
# PDC Emulator → sincronizza con sorgente esterna (NTP pool)
# Altri DC → sincronizzano con PDC Emulator
# Client → sincronizzano con DC nel proprio sito

# Sul PDC Emulator:
w32tm /config /manualpeerlist:"0.pool.ntp.org,0x8 1.pool.ntp.org,0x8" /syncfromflags:MANUAL /update
net stop w32time && net start w32time
w32tm /resync

# KRB_ERR_PREAUTH_FAILED — Pre-authentication fallita
# → Password errata
# → Account lockout
# → Encryption type non supportato
# Verificare:
Get-ADUser username -Properties msDS-SupportedEncryptionTypes

# KRB_AP_ERR_MODIFIED — Messaggio alterato in transito
# → SPN duplicato
# → Account computer corrotto
# Verificare SPN:
setspn -X    # Trovare SPN duplicati nel forest
setspn -L computername    # Elencare SPN di un account

# Ticket Kerberos — Diagnostica
klist                     # Ticket del contesto utente corrente
klist -li 0x3e7          # Ticket del contesto SYSTEM (sessione 0)
klist purge              # Svuotare cache ticket (forza rinnovo)

# Registrare un SPN mancante
setspn -S HTTP/webapp.domain.com svc_webapp
# -S = aggiunge solo se non esiste già (safe)

# NTLM Fallback — Quando Kerberos fallisce, Windows usa NTLM
# Identificare connessioni che usano NTLM invece di Kerberos:
# Event Viewer → Security → Event ID 4624 → AuthenticationPackageName
# Se "NTLM" invece di "Kerberos" → Kerberos non funziona per quel servizio
# Cause: SPN mancante, DNS non risolve, clock skew
```

### FSMO Roles — Troubleshooting

```powershell
# Verificare chi detiene i ruoli FSMO
netdom query fsmo

# Alternativa PowerShell:
Get-ADDomain | Select-Object InfrastructureMaster, RIDMaster, PDCEmulator
Get-ADForest | Select-Object SchemaMaster, DomainNamingMaster

# Se un DC che detiene un ruolo FSMO va offline permanentemente:
# → SEIZE (cattura forzata) del ruolo su un altro DC
# ATTENZIONE: il vecchio DC NON deve MAI essere rimesso online dopo un seize
# (tranne per RID Master, PDC Emulator e Infrastructure Master che sono safe da seize)

# Seize con PowerShell (esempio: PDC Emulator)
Move-ADDirectoryServerOperationMasterRole -Identity DC02 `
    -OperationMasterRole PDCEmulator -Force
# -Force = seize invece di transfer

# Transfer ordinato (DC sorgente online)
Move-ADDirectoryServerOperationMasterRole -Identity DC02 `
    -OperationMasterRole PDCEmulator
# Senza -Force = transfer negoziato (il vecchio DC rilascia il ruolo)
```

---

## Troubleshooting Group Policy (GPO)

### Diagnostica GPO

```powershell
# === GPRESULT — STRUMENTO PRINCIPALE ===

# Report HTML completo (consigliato)
gpresult /h C:\Temp\gpo_report.html /f
# Apre in browser: mostra tutte le GPO applicate e denied

# Report per utente specifico
gpresult /h C:\Temp\gpo_report.html /user domain\username /f

# Risultato in console (rapido)
gpresult /r                    # Sommario
gpresult /z                    # Dettagliato (verbose)

# === RSoP (Resultant Set of Policy) ===
# GUI: rsop.msc → mostra il risultato finale delle policy applicate
# Limitazione: non mostra GPO denied (usare gpresult per quello)

# === GPO PROCESSING ORDER ===
# Le GPO si applicano in quest'ordine (LSDOU):
# 1. Local GPO (gpedit.msc)
# 2. Site GPO
# 3. Domain GPO
# 4. OU GPO (dalla OU più alta alla più specifica)
# Ultima applicata vince (a meno di "Enforced")

# Eccezioni:
# "Enforced" (No Override): la GPO forzata vince sempre
# "Block Inheritance": la OU non eredita GPO dal parent
#   Ma Enforced batte Block Inheritance

# === ORDINE DI PROCESSING DETTAGLIATO ===
# 1. Computer startup scripts → Computer GPO
# 2. Network identification (NLA determina Domain/Private/Public)
# 3. User logon → User GPO
# 4. User logon scripts
# Background refresh: ogni 90 min (+/- 30 min random)
# DC background refresh: ogni 5 min

# Forzare refresh GPO
gpupdate /force                        # Refresh sia Computer che User
gpupdate /force /target:computer       # Solo Computer
gpupdate /force /target:user           # Solo User

# === EVENT LOG PER GPO ===

# Log principale: Microsoft-Windows-GroupPolicy/Operational
Get-WinEvent -LogName "Microsoft-Windows-GroupPolicy/Operational" -MaxEvents 50 |
    Format-Table TimeCreated, Id, Message -Wrap

# Event ID importanti:
# 4016: Starting computer policy processing
# 4017: Starting user policy processing
# 5016: Computer policy processing completed successfully
# 5017: User policy processing completed successfully
# 7016: Computer policy processing completed with errors
# 7017: User policy processing completed with errors
# 5312: List of GPO applied
# 5313: GPO denied (filtered out) — CRITICO per troubleshooting

# Filtrare solo errori GPO
Get-WinEvent -LogName "Microsoft-Windows-GroupPolicy/Operational" |
    Where-Object { $_.Level -le 2 } |  # 1=Critical, 2=Error
    Select-Object -First 20 TimeCreated, Id, Message

# === MOTIVI COMUNI GPO NON APPLICATA ===

# 1. WMI Filter — la GPO ha un WMI filter che non corrisponde al PC
# Verificare: GPMC → GPO → WMI Filtering
# Testare il WMI filter manualmente:
Get-CimInstance -Namespace root\CIMv2 -Query "SELECT * FROM Win32_OperatingSystem WHERE Version LIKE '10.%'"
# Se restituisce risultato → il filter corrisponde

# 2. Security Filtering — utente/computer non nel gruppo di sicurezza
# Default: "Authenticated Users" ha Read+Apply
# Se cambiato: verificare che il computer/utente abbia entrambi i permessi

# 3. Link disabilitato — la GPO esiste ma il link alla OU è disabilitato
# GPMC → OU → verificare che il link sia enabled

# 4. Loopback Processing — in modalità Replace o Merge
# Replace: le GPO utente della OU del computer sostituiscono quelle dell'utente
# Merge: le GPO utente della OU del computer si aggiungono (e vincono in conflitto)
# Verificare: Computer Configuration → Administrative Templates → System → Group Policy
#   → Configure user Group Policy loopback processing mode

# 5. Slow Link Detection — GPO non processata perché il link è lento
# Default threshold: < 500 kbps → slow link → alcune GPO non si applicano
# Verificare:
#   Computer Configuration → Administrative Templates → System → Group Policy
#     → Configure Group Policy Slow Link Detection

# === WMI FILTER DEBUGGING ===

# Testare un WMI filter offline
$Query = "SELECT * FROM Win32_OperatingSystem WHERE ProductType = 1"
$Result = Get-CimInstance -Namespace root\CIMv2 -Query $Query
if ($Result) { "MATCH — la GPO si applicherebbe" } else { "NO MATCH — GPO filtrata" }

# Elencare tutti i WMI Filter nel dominio
Get-ADObject -SearchBase "CN=SOM,CN=WMIPolicy,CN=System,$(([ADSI]'').distinguishedName)" `
    -Filter * -Properties msWMI-Name, msWMI-Parm2 |
    Select-Object @{N='Name';E={$_.'msWMI-Name'}}, @{N='Query';E={$_.'msWMI-Parm2'}}

# === GPO PREFERENCES vs POLICY ===
# Policy: lock down (l'utente non può cambiare)
#   → Scritta in HKLM\Software\Policies o HKCU\Software\Policies
#   → Rimossa quando la GPO non si applica più (tatuaggio: NO)
# Preference: default (l'utente può modificare)
#   → Scritta nelle stesse chiavi dell'applicazione
#   → NON rimossa quando la GPO non si applica più (tatuaggio: SÌ, salvo F5/Apply Once)
# Se il setting è "tattooed" e la GPO è stata rimossa → il setting rimane
# Pulire: eliminare manualmente la chiave registry o usare Remove preference item
```

---

## Troubleshooting DNS

```powershell
# WORKFLOW DIAGNOSTICO DNS

# 1. Il client risolve?
Resolve-DnsName "hostname.domain.com"                     # Generico
Resolve-DnsName "_ldap._tcp.dc._msdcs.domain.com" -Type SRV  # SRV record AD

# 2. Da quale DNS server?
Get-DnsClientServerAddress -AddressFamily IPv4

# 3. Flush cache e riprova
Clear-DnsClientCache
Resolve-DnsName "hostname.domain.com"

# 4. Query diretta al DNS server
Resolve-DnsName "hostname.domain.com" -Server 192.168.10.10

# 5. Il record esiste sul server DNS?
Get-DnsServerResourceRecord -ZoneName "domain.com" -Name "hostname" -ComputerName DC01

# 6. Diagnostica DNS server
dcdiag /test:dns /v /s:DC01

# 7. Registrazione DNS
ipconfig /registerdns    # Client
# Sul DNS server: verificare Dynamic Updates abilitati sulla zona

# PROBLEMI COMUNI

# "DNS non risolve nomi interni"
# → Verificare che il client punti ai DNS interni (non 8.8.8.8!)
# → Verificare DNS suffix search list
# → Verificare che la zona sia attiva: Get-DnsServerZone

# "SRV records mancanti per AD"
# → Il DC non ha registrato i record: restart Netlogon (net stop netlogon && net start netlogon)
# → Verificare: zona _msdcs esiste e accetta dynamic updates

# "DNS scavenging ha cancellato record validi"
# → Record statici devono avere timestamp 0 (non soggetti a scavenging)
# → Verificare No-Refresh e Refresh interval
```

### DNS — Problemi avanzati

```powershell
# === CONDITIONAL FORWARDER NON FUNZIONA ===
# Sintomo: client non riesce a risolvere nomi di un dominio esterno
# 1. Verificare che il conditional forwarder esista:
Get-DnsServerZone -ComputerName DC01 | Where-Object ZoneType -eq "Forwarder"

# 2. Testare connettività al DNS target:
Test-NetConnection -ComputerName 10.0.0.1 -Port 53

# 3. Testare risoluzione diretta tramite il forwarder:
Resolve-DnsName "host.external.com" -Server 10.0.0.1

# 4. Se funziona direttamente ma non tramite il DC → ricreare il forwarder:
Remove-DnsServerZone -Name "external.com" -ComputerName DC01 -Force
Add-DnsServerConditionalForwarderZone -Name "external.com" `
    -MasterServers 10.0.0.1,10.0.0.2 -ComputerName DC01

# === STUB ZONE OUTDATED ===
# La stub zone contiene solo NS e SOA record → punta al DNS autoritativo
# Se i record NS sono obsoleti → risoluzione fallisce
Get-DnsServerZone -Name "partner.com" -ComputerName DC01
# Verificare MasterServers → sono ancora corretti?
# Forzare transfer: dnscmd DC01 /zonerefresh partner.com

# === DNS CACHE POISONING / RECORD STALE ===
# Verificare cache DNS del server:
Get-DnsServerCache -ComputerName DC01 | Where-Object HostName -like "*target*"
# Pulire cache del server DNS:
Clear-DnsServerCache -ComputerName DC01 -Force
# Pulire cache del client:
Clear-DnsClientCache

# === RECORD DUPLICATI O STALE ===
# Causa comune: scavenging disabilitato + DHCP → record accumulati
# Abilitare scavenging sulla zona:
Set-DnsServerZoneAging -Name "domain.com" -Aging $true `
    -NoRefreshInterval 7.00:00:00 -RefreshInterval 7.00:00:00 `
    -ComputerName DC01

# Abilitare scavenging sul server (necessario per entrambi):
Set-DnsServerScavenging -ScavengingState $true `
    -ScavengingInterval 7.00:00:00 -ComputerName DC01

# Trovare record stale (non aggiornati da 30+ giorni):
$Threshold = (Get-Date).AddDays(-30)
Get-DnsServerResourceRecord -ZoneName "domain.com" -ComputerName DC01 |
    Where-Object { $_.Timestamp -ne $null -and $_.Timestamp -lt $Threshold } |
    Select-Object HostName, RecordType, Timestamp
```

---

## Troubleshooting Rete

```powershell
# APPROCCIO LAYER-BY-LAYER

# LAYER 1 — FISICO
Get-NetAdapter | Select-Object Name, Status, LinkSpeed, MediaConnectionState
# Status: Up? LinkSpeed: corretto? MediaConnectionState: Connected?

# LAYER 2 — DATA LINK
Get-NetAdapterStatistics | Select-Object Name, ReceivedBytes, SentBytes,
    ReceivedUnicastPackets, OutboundDiscardedPackets

# LAYER 3 — NETWORK
Get-NetIPConfiguration
Test-Connection 192.168.10.1           # Gateway
Test-Connection 8.8.8.8               # Internet
tracert 8.8.8.8                        # Dove si ferma?

# LAYER 4 — TRANSPORT
Test-NetConnection -ComputerName SRV01 -Port 443
Test-NetConnection -ComputerName SRV01 -Port 3389

# Porte in ascolto
Get-NetTCPConnection -State Listen | Select-Object LocalPort,
    @{N='Process';E={(Get-Process -Id $_.OwningProcess).Name}} |
    Sort-Object LocalPort

# LAYER 7 — APPLICATION
# Testare l'applicazione specifica (HTTP, SMB, RDP, etc.)
Invoke-WebRequest -Uri "http://webapp:8080/health" -UseBasicParsing
net use \\SRV01\share
mstsc /v:SRV01

# FIREWALL
Get-NetFirewallRule -Enabled True -Direction Inbound |
    Where-Object Action -eq Block |
    Select-Object DisplayName, Profile

# Profilo rete (Domain/Private/Public)
Get-NetConnectionProfile
# Se "Public" invece di "Domain" → il DC non è raggiungibile al boot
Set-NetConnectionProfile -InterfaceAlias "Ethernet" -NetworkCategory DomainAuthenticated

# PACKET CAPTURE (se necessario)
pktmon filter add -t TCP -p 443
pktmon start --capture --file-name C:\Temp\capture.etl
# ...riprodurre il problema...
pktmon stop
pktmon etl2pcap C:\Temp\capture.etl --out C:\Temp\capture.pcapng
```

### DHCP — Troubleshooting

```powershell
# === CLIENT NON OTTIENE IP ===

# Verificare stato DHCP sul client
ipconfig /all    # Cercare: DHCP Enabled, DHCP Server, Lease Obtained

# Se il client ha un indirizzo 169.254.x.x (APIPA)
# → DHCP non raggiungibile
# → Verificare: cavo, switch, VLAN, DHCP server attivo

# Rilasciare e rinnovare
ipconfig /release
ipconfig /renew

# Verificare DHCP server
Get-DhcpServerv4Scope -ComputerName DHCP01
Get-DhcpServerv4ScopeStatistics -ComputerName DHCP01
# Cercare: Free addresses > 0, Percentageinuse < 90%

# Se scope esaurito (0 free addresses):
# → Espandere range
# → Ridurre lease duration
# → Trovare e pulire lease orfani
Get-DhcpServerv4Lease -ComputerName DHCP01 -ScopeId 192.168.10.0 |
    Where-Object { $_.AddressState -eq "InactiveReservation" -or
                   $_.HostName -eq "" }

# === DHCP RELAY / IP HELPER ===
# Se client e DHCP server sono in subnet diverse → serve IP helper sull'interfaccia del router
# Verificare: configurazione switch L3 / router per ip helper-address

# === CONFLITTO IP ===
# Event Viewer → System → Source: DHCP-Client o Tcpip → Event ID 4199
# Trovare chi ha l'IP duplicato:
arp -a 192.168.10.50       # Mostra MAC address
# Confrontare con: Get-DhcpServerv4Lease per identificare il device
```

### SMB — Problemi di accesso condivisioni

```powershell
# === "ACCESS DENIED" su condivisione ===

# 1. Verificare share permissions (chi può accedere alla condivisione)
Get-SmbShareAccess -Name "ShareName" -CimSession SRV01

# 2. Verificare NTFS permissions (chi può accedere ai file)
Get-Acl "\\SRV01\ShareName" | Format-List

# 3. Il permesso EFFETTIVO è l'INTERSEZIONE dei due:
#    Share: Everyone = Full Control
#    NTFS: Domain Users = Read
#    → Risultato: Domain Users ha solo Read

# === SMB NON RAGGIUNGIBILE ===

# Test di base
Test-NetConnection -ComputerName SRV01 -Port 445

# Verificare versione SMB in uso
Get-SmbConnection

# Se SMBv1 richiesto ma disabilitato (corretto — non riabilitare SMBv1):
Get-SmbServerConfiguration | Select-Object EnableSMB1Protocol, EnableSMB2Protocol
# SMBv1 è insicuro. Non riabilitarlo. Aggiornare il client/server.

# === PERFORMANCE SMB LENTA ===
# Verificare SMB Signing (impatto 10-15% su performance):
Get-SmbServerConfiguration | Select-Object RequireSecuritySignature
# Se il server è DC → signing è obbligatorio (by design)
# Per file server non-DC → valutare se necessario

# Verificare SMB Multichannel (usa più NIC per performance):
Get-SmbMultichannelConnection
# Se non attivo con NIC multiple → verificare RSS, RDMA

# === CANNOT BROWSE NETWORK ===
# "Network discovery" dipende da:
# - Function Discovery Resource Publication (FDResPub)
# - SSDP Discovery (SSDPSRV)
# - UPnP Device Host (upnphost)
Get-Service FDResPub, SSDPSRV, upnphost | Select-Object Name, Status, StartType
```

### VPN — Troubleshooting

```powershell
# === VPN NON SI CONNETTE ===

# Event Log VPN:
Get-WinEvent -LogName "Application" -MaxEvents 30 |
    Where-Object { $_.ProviderName -like "*RasClient*" -or
                   $_.ProviderName -like "*Ras*" }

# Errori comuni:
# Error 691: username/password errati, o account lockout
# Error 800: VPN server non raggiungibile (firewall, DNS, routing)
# Error 809: IPSEC ports bloccati (UDP 500, 4500)
# Error 812: RADIUS policy nega l'accesso
# Error 720: errore negoziazione PPP → reinstallare miniport WAN

# Diagnostica SSTP VPN
Test-NetConnection -ComputerName vpn.company.com -Port 443
# SSTP usa porta 443 — se bloccata, SSTP non funziona

# Diagnostica IKEv2 VPN
Test-NetConnection -ComputerName vpn.company.com -Port 500 -InformationLevel Detailed
# IKEv2 usa UDP 500 e 4500

# Always-On VPN — diagnostica
Get-VpnConnection                    # Configurazione VPN
Get-VpnConnection -AllUserConnection # VPN machine tunnel

# Verificare profilo VPN ProfileXML
Get-VpnConnection -Name "VPN_Name" | Select-Object -ExpandProperty ServerAddress

# === SPLIT TUNNEL vs FORCE TUNNEL ===
# Split tunnel: solo traffico per rete aziendale passa per VPN
# Force tunnel: TUTTO il traffico passa per VPN (più sicuro, più lento)
Get-VpnConnection | Select-Object Name, SplitTunneling
# Problemi con force tunnel:
# - Internet lento → tutto passa per il gateway aziendale
# - Applicazioni cloud non funzionano → routing subottimale
```

### Firewall — Diagnostica regole

```powershell
# === REGOLE FIREWALL — ANALISI ===

# Trovare quale regola blocca un traffico specifico
# Abilitare logging:
Set-NetFirewallProfile -Profile Domain -LogBlocked True `
    -LogFileName "C:\Windows\System32\LogFiles\Firewall\pfirewall.log" `
    -LogMaxSizeKilobytes 32767

# Leggere il log (dopo aver riprodotto il problema):
Get-Content "C:\Windows\System32\LogFiles\Firewall\pfirewall.log" -Tail 50

# Cercare regole per porta
Get-NetFirewallPortFilter | Where-Object LocalPort -eq 8080 |
    Get-NetFirewallRule | Select-Object DisplayName, Enabled, Action, Direction

# Cercare regole per programma
Get-NetFirewallApplicationFilter | Where-Object Program -like "*app.exe*" |
    Get-NetFirewallRule | Select-Object DisplayName, Enabled, Action

# Creare regola temporanea di test (da rimuovere dopo)
New-NetFirewallRule -DisplayName "TEST_Allow_8080" `
    -Direction Inbound -Protocol TCP -LocalPort 8080 `
    -Action Allow -Profile Domain

# Rimuovere dopo il test:
Remove-NetFirewallRule -DisplayName "TEST_Allow_8080"

# Verificare profilo attivo
Get-NetFirewallProfile | Select-Object Name, Enabled, DefaultInboundAction
# Se DefaultInboundAction è Block → tutto ciò che non ha una Allow rule è bloccato
```

---

## Troubleshooting Performance

```powershell
# CHECKLIST RAPIDA (1 minuto)
# 1. Task Manager → Performance tab → CPU, Memory, Disk, Network overview
# 2. Resource Monitor → identifica il processo che consuma risorse

# CPU ALTA
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10 Name, CPU, Id
# Cause comuni: aggiornamenti, antivirus scan, backup, query DB, crypto mining

# Se un processo consuma 100% CPU:
Get-CimInstance Win32_Process -Filter "ProcessId=1234" | Select-Object CommandLine
# Decidere: è legittimo? Va terminato? Va ottimizzato?

# MEMORIA PIENA
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 10 Name,
    @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB)}}

# Memory leak: il processo cresce continuamente senza rilasciare
# Monitorare: Performance Monitor → Process → Working Set
# Se leak confermato: restart del servizio/processo

# Commit charge vs Physical RAM:
$os = Get-CimInstance Win32_OperatingSystem
[PSCustomObject]@{
    TotalRAM_GB = [math]::Round($os.TotalVisibleMemorySize/1MB, 2)
    FreeRAM_GB = [math]::Round($os.FreePhysicalMemory/1MB, 2)
    CommitLimit_GB = [math]::Round(($os.TotalVirtualMemorySize)/1MB, 2)
}

# DISCO LENTO
# Resource Monitor → Disk → per-process I/O
# Performance Monitor → PhysicalDisk → Avg. Disk Queue Length (> 2 = collo di bottiglia)

# Verificare salute disco
Get-PhysicalDisk | Select-Object FriendlyName, HealthStatus, OperationalStatus
# Se HealthStatus ≠ Healthy → sostituire il disco ASAP
```

### Performance avanzata — CPU

```powershell
# === IDENTIFICARE PROCESSI CPU-INTENSIVE ===

# Top 10 processi per CPU time con dettagli
Get-Process | Where-Object { $_.CPU -gt 0 } |
    Sort-Object CPU -Descending |
    Select-Object -First 10 Name, Id, CPU,
    @{N='Threads';E={$_.Threads.Count}},
    @{N='Handles';E={$_.HandleCount}},
    @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB)}},
    @{N='StartTime';E={$_.StartTime}} |
    Format-Table -AutoSize

# CPU per core (importante per processi single-threaded)
Get-Counter '\Processor(*)\% Processor Time' -MaxSamples 3 -SampleInterval 2

# Se un singolo core è al 100% e gli altri sono idle
# → processo single-threaded che satura un core
# → ottimizzare o parallelizzare il processo

# === INTERRUPT E DPC (kernel mode CPU usage) ===
# Se "System Interrupts" consuma CPU in Task Manager:
# → Driver hardware che genera troppe interrupt
# → Controllare: latencymon.exe (LatencyMon) identifica il driver

# Performance counter DPC time:
Get-Counter '\Processor(_Total)\% DPC Time' -MaxSamples 5 -SampleInterval 1
# DPC Time > 5% → problema driver

# === PROCESS DUMP PER ANALISI ===
# Se un processo consuma CPU e va analizzato:
# Procdump (Sysinternals) — cattura dump quando CPU > 90% per 10 secondi
# procdump -c 90 -s 10 -ma <PID> C:\Dumps\
# Il dump può essere analizzato con WinDbg o Visual Studio
```

### Performance avanzata — Memoria

```powershell
# === MEMORY LEAK DETECTION ===

# Monitorare Working Set di un processo nel tempo
$ProcessName = "w3wp"   # esempio: IIS worker process
$Samples = 10
$Interval = 60          # secondi

1..$Samples | ForEach-Object {
    $proc = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue |
        Select-Object Name, Id, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB)}},
        @{N='PrivateMB';E={[math]::Round($_.PrivateMemorySize64/1MB)}},
        @{N='Handles';E={$_.HandleCount}}
    [PSCustomObject]@{
        Time = Get-Date -Format "HH:mm:ss"
        Process = $proc.Name
        PID = $proc.Id
        WorkingSetMB = $proc.MemMB
        PrivateMB = $proc.PrivateMB
        Handles = $proc.Handles
    }
    Start-Sleep -Seconds $Interval
} | Format-Table -AutoSize

# Se WorkingSetMB o PrivateMB crescono costantemente → memory leak

# === HANDLE LEAK ===
# I processi con handle leak accumulano handle senza rilasciarli
# Sintomo: HandleCount cresce nel tempo → eventualmente il sistema rallenta

# Monitorare handle count
Get-Process | Where-Object HandleCount -gt 5000 |
    Select-Object Name, Id, HandleCount |
    Sort-Object HandleCount -Descending

# Handle > 10000 su un processo → probabile handle leak
# Handle > 50000 → impatto sistema → riavviare il processo

# Usare handle.exe (Sysinternals) per dettagli:
# handle.exe -p <PID> -s    → sommario per tipo di handle
# Tipi: File, Key (registry), Thread, Event, Section, Mutant

# === NONPAGED POOL EXHAUSTION ===
# Pool memoria kernel non paginabile (sempre in RAM)
# Se esaurito → BSOD

# Verificare:
Get-Counter '\Memory\Pool Nonpaged Bytes' -MaxSamples 1
# Valore tipico: 100-500 MB
# Se > 1 GB → driver con leak nel pool

# poolmon.exe (Windows SDK) identifica il pool tag che consuma memoria
# poolmon -b → ordina per bytes totali → identifica il tag
# Cercare il tag: findstr /s "<tag>" C:\Windows\System32\drivers\*.sys

# === PAGEFILE DIAGNOSTICA ===
# Verificare configurazione pagefile
Get-CimInstance Win32_PageFileUsage | Select-Object Name, AllocatedBaseSize, CurrentUsage, PeakUsage

# Se PeakUsage si avvicina ad AllocatedBaseSize → pagefile troppo piccolo
# Regola generale: pagefile = 1.5x RAM per server standard
# Per analisi crash dump: pagefile >= RAM (necessario per complete dump)

# Configurare pagefile via PowerShell:
# (Richiede reboot)
$sys = Get-CimInstance Win32_ComputerSystem
$sys | Set-CimInstance -Property @{AutomaticManagedPagefile=$false}
# Impostare pagefile personalizzato:
# wmic pagefileset where name="C:\\pagefile.sys" set InitialSize=8192,MaximumSize=16384
```

### Performance avanzata — Disco I/O

```powershell
# === DISK QUEUE LENGTH ===
# Numero medio di richieste I/O in coda
# Valore sano: < 2 per disco fisico
# > 2: collo di bottiglia
# > 5: problema serio

Get-Counter '\PhysicalDisk(*)\Avg. Disk Queue Length' -MaxSamples 5 -SampleInterval 2
Get-Counter '\PhysicalDisk(*)\Avg. Disk sec/Read' -MaxSamples 5 -SampleInterval 2
Get-Counter '\PhysicalDisk(*)\Avg. Disk sec/Write' -MaxSamples 5 -SampleInterval 2

# Latenza disco:
# < 10ms = buono (SSD tipico)
# 10-20ms = accettabile (HDD)
# > 20ms = problematico
# > 50ms = critico

# === IDENTIFICARE PROCESSO CHE GENERA I/O ===
# Resource Monitor → Disk tab → ordinare per Total (B/sec)
# Oppure:
Get-Counter '\Process(*)\IO Read Bytes/sec' -MaxSamples 1 |
    Select-Object -ExpandProperty CounterSamples |
    Where-Object CookedValue -gt 0 |
    Sort-Object CookedValue -Descending |
    Select-Object -First 10 InstanceName,
    @{N='ReadMB_s';E={[math]::Round($_.CookedValue/1MB, 2)}}

# === STORAGE SPACES / STORAGE POOL HEALTH ===
Get-StoragePool | Select-Object FriendlyName, HealthStatus, OperationalStatus
Get-VirtualDisk | Select-Object FriendlyName, HealthStatus, OperationalStatus
Get-PhysicalDisk | Select-Object FriendlyName, HealthStatus, MediaType, BusType, Size

# Se un disco in un pool è degradato:
Get-PhysicalDisk | Where-Object HealthStatus -ne "Healthy"
# Verificare: Event Viewer → System → Source: disk, ntfs, storagespaces

# === TRIM / OPTIMIZE SSD ===
# Verificare stato TRIM:
fsutil behavior query DisableDeleteNotify
# 0 = TRIM abilitato (corretto per SSD)
# 1 = TRIM disabilitato (abilitare con: fsutil behavior set DisableDeleteNotify 0)

# Ottimizzare manualmente:
Optimize-Volume -DriveLetter C -ReTrim -Verbose
# Per HDD: Optimize-Volume -DriveLetter D -Defrag
```

### Performance avanzata — Rete

```powershell
# === NETWORK BOTTLENECK DETECTION ===

# Bandwidth in uso per interfaccia
Get-Counter '\Network Interface(*)\Bytes Total/sec' -MaxSamples 5 -SampleInterval 2 |
    Select-Object -ExpandProperty CounterSamples |
    Where-Object CookedValue -gt 0 |
    Select-Object InstanceName,
    @{N='Mbps';E={[math]::Round($_.CookedValue * 8 / 1MB, 2)}}

# Se Mbps si avvicina alla link speed → saturazione

# Errori di rete
Get-NetAdapterStatistics | Select-Object Name,
    ReceivedErrors, OutboundErrors,
    ReceivedDiscards, OutboundDiscards

# Errori > 0.1% dei pacchetti → problema fisico (cavo, switch, NIC)

# === TCP CONNECTION ANALYSIS ===

# Connessioni per stato
Get-NetTCPConnection | Group-Object State |
    Select-Object Name, Count | Sort-Object Count -Descending

# Troppe connessioni TIME_WAIT → applicazione non chiude correttamente le connessioni
# Troppe connessioni ESTABLISHED → verificare se legittimo

# Connessioni per processo
Get-NetTCPConnection -State Established |
    Select-Object LocalPort, RemoteAddress, RemotePort,
    @{N='Process';E={(Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue).Name}} |
    Sort-Object Process | Format-Table -AutoSize

# === NIC TEAMING / RSS / VMQ ===
# Verificare NIC teaming:
Get-NetLbfoTeam
Get-NetLbfoTeamMember

# Receive Side Scaling:
Get-NetAdapterRss
# Se performance rete bassa con CPU multi-core → abilitare RSS

# VMQ (Virtual Machine Queue) — Hyper-V host:
Get-NetAdapterVmq
```

---

## Troubleshooting Servizi e Applicazioni

```powershell
# Servizio non si avvia
Get-Service -Name "ServiceName" | Format-List *
Get-WinEvent -LogName System -MaxEvents 20 |
    Where-Object { $_.Message -like "*ServiceName*" }

# Errori comuni servizio:
# Error 1053: Service did not respond in time → aumentare timeout o debug
# Error 1067: Process terminated unexpectedly → crash, verificare Event Log
# Error 1069: Logon failure → password account servizio cambiata
# Error 5: Access denied → permessi insufficienti

# Dipendenze servizio
Get-Service -Name "ServiceName" -RequiredServices
# Se una dipendenza è ferma, il servizio non può partire

# Application crash
# Event Viewer → Application → Source: Application Error
# Cercare: Faulting module, exception code
Get-WinEvent -FilterHashtable @{LogName='Application'; ProviderName='Application Error'} -MaxEvents 10

# .NET crash
# Event Viewer → Application → Source: .NET Runtime
# Stack trace nell'evento per identificare il punto di crash

# IIS
# Log: C:\inetpub\logs\LogFiles\
# Event Viewer → Application → Source: IIS-W3SVC-WP
Get-WebAppPoolState *
# Se Application Pool si ferma (503 error):
# → Verificare Event Log per crash
# → Verificare memoria (Rapid Fail Protection ferma il pool dopo N crash)
```

### Servizi — Diagnostica avanzata

```powershell
# === SERVIZIO CHE CRASHA RIPETUTAMENTE ===

# Configurare recovery options (cosa fare al crash)
sc.exe failure "ServiceName" reset=86400 actions=restart/60000/restart/60000/run/120000
# Dopo primo crash: restart dopo 60 secondi
# Dopo secondo crash: restart dopo 60 secondi
# Dopo ulteriori crash: esegui un comando dopo 120 secondi
# Reset counter dopo 86400 secondi (24h)

# Verificare recovery options attuali
sc.exe qfailure "ServiceName"

# === SERVIZIO CON DIPENDENZE CIRCOLARI ===
# Identificare tutte le dipendenze di un servizio
Get-Service -Name "ServiceName" | Select-Object -ExpandProperty RequiredServices
Get-Service -Name "ServiceName" | Select-Object -ExpandProperty DependentServices

# Mappa completa delle dipendenze
Get-Service | ForEach-Object {
    [PSCustomObject]@{
        Service = $_.Name
        DependsOn = ($_.RequiredServices | ForEach-Object Name) -join ", "
        RequiredBy = ($_.DependentServices | ForEach-Object Name) -join ", "
    }
} | Where-Object { $_.DependsOn -ne "" -or $_.RequiredBy -ne "" }

# === DELAYED START ===
# Per servizi che falliscono perché le dipendenze non sono pronte
# Configurare Delayed Auto Start:
Set-Service -Name "ServiceName" -StartupType AutomaticDelayedStart
# Il servizio parte ~2 minuti dopo gli altri Automatic services

# === SERVICE ACCOUNT — PROBLEMI ===
# Error 1069 (Logon failure):
# → La password del service account è cambiata in AD
# → L'account è bloccato
# → L'account è scaduto
# → L'account non ha "Log on as a service" right

# Verificare chi ha "Log on as a service":
secedit /export /cfg C:\Temp\secpol.cfg
Select-String "SeServiceLogonRight" C:\Temp\secpol.cfg

# Verificare account servizio
Get-CimInstance Win32_Service | Where-Object Name -eq "ServiceName" |
    Select-Object Name, StartName, State

# Resettare la password del service account:
$svc = Get-CimInstance Win32_Service -Filter "Name='ServiceName'"
$svc | Invoke-CimMethod -MethodName Change -Arguments @{StartPassword="NuovaPassword"}
# Oppure via services.msc → Properties → Log On tab

# === PROCDUMP — CATTURARE DUMP DI UN SERVIZIO CHE CRASHA ===
# procdump.exe -ma -e -w <nome_processo> C:\Dumps\
# -ma = full dump
# -e = trigger sull'eccezione
# -w = attende che il processo parta (utile per servizi)
# Il dump risultante si analizza con WinDbg
```

### Application Crash — Analisi approfondita

```powershell
# === EVENT LOG PER APPLICATION CRASHES ===

# Application Error (crash non gestiti)
Get-WinEvent -FilterHashtable @{
    LogName = 'Application'
    ProviderName = 'Application Error'
} -MaxEvents 10 | ForEach-Object {
    [PSCustomObject]@{
        Time = $_.TimeCreated
        App = $_.Properties[0].Value        # Faulting application name
        Version = $_.Properties[1].Value     # Faulting application version
        Module = $_.Properties[3].Value      # Faulting module name
        ExCode = '0x{0:X}' -f $_.Properties[6].Value  # Exception code
    }
}

# Application Hang (applicazione non risponde)
Get-WinEvent -FilterHashtable @{
    LogName = 'Application'
    ProviderName = 'Application Hang'
} -MaxEvents 10

# Windows Error Reporting (WER) — crash report dettagliati
Get-ChildItem "$env:LocalAppData\CrashDumps" -ErrorAction SilentlyContinue
# WER store:
Get-ChildItem "$env:ProgramData\Microsoft\Windows\WER\ReportArchive" -ErrorAction SilentlyContinue

# === APPLICATION COMPATIBILITY TOOLKIT (ACT) ===
# Per applicazioni legacy che non funzionano su Windows recente:
# 1. Compatibility mode (tasto destro → Properties → Compatibility)
# 2. Compatibility Administrator (parte di Windows ADK)
#    → Crea fix personalizzati (shim) per applicazioni
# 3. Application Compatibility Toolkit → analisi log

# === EXCEPTION CODES COMUNI ===
# 0xC0000005: Access Violation — accesso a memoria non valida
# 0xC00000FD: Stack Overflow — ricorsione infinita o stack troppo piccolo
# 0xC0000374: Heap Corruption — corruzione della heap
# 0xE0434352: .NET CLR Exception — eccezione .NET non gestita
# 0xC0000409: Stack Buffer Overrun — possibile exploit o bug
# 0x40000015: Fatal Application Exit — applicazione ha chiamato abort()

# === .NET CRASH — DIAGNOSTICA ===
# Abilitare First Chance Exception logging:
# Event Viewer → Application → .NET Runtime
# Cercare: "Application: app.exe Framework Version: ..."
# Lo stack trace nel messaggio indica il punto di crash

# Fuslogvw.exe (Assembly Binding Log Viewer)
# Per problemi di assembly loading (DLL mancanti, versione errata)
# Abilitare logging:
# HKLM\SOFTWARE\Microsoft\Fusion\ForceLog = 1 (DWORD)
# HKLM\SOFTWARE\Microsoft\Fusion\LogPath = C:\FusionLog\
# ATTENZIONE: disabilitare dopo il debug (impatto performance)
```

---

## Problemi di Stampa

```powershell
# === PRINT SPOOLER CRASH ===

# Il Print Spooler (spoolsv.exe) crasha e non riparte
# 1. Pulire la coda di stampa
Stop-Service Spooler -Force
Remove-Item "C:\Windows\System32\spool\PRINTERS\*" -Force
Start-Service Spooler

# 2. Se il crash è causato da un driver corrotto
# Identificare il driver:
Get-PrinterDriver | Select-Object Name, PrinterEnvironment, DriverVersion

# Rimuovere driver problematico:
Remove-PrinterDriver -Name "Driver Problematico"
# Poi reinstallare la versione corretta

# 3. Event Viewer per diagnostica crash spooler
Get-WinEvent -FilterHashtable @{
    LogName = 'System'
    ProviderName = 'Service Control Manager'
} -MaxEvents 20 | Where-Object { $_.Message -like "*Spooler*" }

# === DRIVER CONFLICTS ===

# Usare Type 4 (v4) driver quando possibile (meno crash):
# V4 driver sono isolati → un driver che crasha non blocca tutti gli altri
# V3 driver: tutti nello stesso processo spooler → uno crasha, tutti crashano

# Verificare tipo driver:
Get-PrinterDriver | Select-Object Name, MajorVersion
# MajorVersion 4 = v4 driver (raccomandato)
# MajorVersion 3 = v3 driver (legacy)

# Isolare driver V3 in un processo separato:
# printui.exe → driver properties → Advanced → Print processor
# Spuntare "Enable advanced printing features"
# Se il driver crasha, solo la sua istanza viene colpita

# === STAMPANTE DI RETE NON RAGGIUNGIBILE ===

# Test base
Test-NetConnection -ComputerName PRINTER01 -Port 9100   # RAW printing
Test-NetConnection -ComputerName PRINTER01 -Port 631     # IPP/CUPS
ping PRINTER01

# Verifica che la porta sia configurata correttamente
Get-PrinterPort | Select-Object Name, PrinterHostAddress, PortNumber

# === GPO DEPLOYMENT STAMPANTI ===

# Verificare stampanti distribuite via GPO:
Get-WinEvent -LogName "Microsoft-Windows-PrintService/Operational" -MaxEvents 20

# Se la stampante GPO non appare:
# 1. gpresult /r → la GPO è applicata?
# 2. Il driver è disponibile nel Print Server? (point-and-print)
# 3. Point-and-print restrictions: GPO blocca l'installazione automatica driver?
# Computer Configuration → Administrative Templates → Printers
#   → Point and Print Restrictions

# === SPOOLER SUBSYSTEM APP CRASH LOOP ===
# Se Spooler crasha immediatamente al restart:
# 1. Avviare in Safe Mode
# 2. Pulire: C:\Windows\System32\spool\PRINTERS\*
# 3. Rimuovere driver sospetti:
#    HKLM\SYSTEM\CurrentControlSet\Control\Print\Environments\
#    → Windows x64\Print Processors → rimuovere entry non-default
# 4. Riavviare in modalità normale
```

---

## Problemi Profili Utente

```powershell
# === TEMPORARY PROFILE ===
# Sintomo: l'utente fa login e ottiene un profilo temporaneo
# Il desktop è vuoto, i file non vengono salvati
# Messaggio: "You've been signed in with a temporary profile"

# Causa: il profilo esistente è corrotto e Windows non riesce a caricarlo
# → Windows crea un profilo temp in C:\Users\TEMP

# Soluzione:
# 1. Verificare quale profilo è corrotto:
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\*" |
    Select-Object PSChildName, ProfileImagePath, State
# State: 0 = ok, 1 = temporary, 8192 = backup

# 2. Trovare il SID dell'utente:
$User = Get-ADUser -Identity "username"
$User.SID.Value

# 3. Nel registry: HKLM\...\ProfileList
# Se ci sono due entry per lo stesso SID (es. S-1-5-21-xxx e S-1-5-21-xxx.bak):
# a. Rinominare S-1-5-21-xxx → S-1-5-21-xxx.old
# b. Rinominare S-1-5-21-xxx.bak → S-1-5-21-xxx
# c. Nella entry corretta: impostare RefCount=0, State=0
# d. Riavviare

# === PROFILO CORROTTO (senza temporary profile) ===
# Sintomo: desktop lento, applicazioni non partono, start menu non funziona

# Reset profilo preservando i dati:
# 1. Rinominare C:\Users\username → C:\Users\username.bak
# 2. Nel registry: rinominare la chiave del profilo → .bak
# 3. L'utente fa login → nuovo profilo creato
# 4. Copiare i dati: Desktop, Documents, Downloads, AppData (selettivamente)
#    NON copiare: NTUSER.DAT (è il profilo corrotto)

# === ROAMING PROFILE — SYNC PROBLEMS ===

# Verificare configurazione roaming profile:
Get-ADUser username -Properties ProfilePath | Select-Object ProfilePath
# ProfilePath dovrebbe essere: \\server\profiles$\username

# Verificare che il server del profilo sia raggiungibile:
Test-Path "\\FILESRV\profiles$\username"

# Verificare permessi:
Get-Acl "\\FILESRV\profiles$\username" | Format-List

# Problemi comuni:
# 1. Profilo troppo grande → sincronizzazione lenta / fallisce
#    Verificare dimensione:
(Get-ChildItem "\\FILESRV\profiles$\username" -Recurse -Force -ErrorAction SilentlyContinue |
    Measure-Object Length -Sum).Sum / 1GB
#    Se > 1 GB → troppo grande → configurare folder redirection per Desktop/Documents

# 2. File bloccati impediscono la sincronizzazione
#    Event Viewer → Application → Source: User Profile Service
#    → Cercare "was not unloaded" o "file in use"

# 3. NTUSER.DAT bloccato da un processo
#    handle.exe NTUSER.DAT → mostra quale processo lo tiene aperto

# === USER PROFILE SERVICE EVENTS ===
Get-WinEvent -LogName "Microsoft-Windows-User Profile Service/Operational" -MaxEvents 20 |
    Select-Object TimeCreated, Id, LevelDisplayName, Message

# Event ID importanti:
# 1509: file non copiato durante caricamento profilo
# 1511: profilo temporaneo creato
# 1530: file/directory bloccati durante scaricamento profilo
# 1533: impossibile cancellare directory profilo

# === FOLDER REDIRECTION — PROBLEMI ===
# Se folder redirection è configurata via GPO ma non funziona:
# 1. Verificare GPO: User Config → Policies → Windows Settings → Folder Redirection
# 2. Verificare permessi sulla share di destinazione:
#    Owner: Creator Owner / Full Control
#    Domain Users: Read/Write
#    Share: Full Control (NTFS gestisce i permessi)
# 3. Verificare Offline Files (se abilitato):
Get-WmiObject -Class Win32_OfflineFilesItem |
    Where-Object { $_.ItemPath -like "*username*" } |
    Select-Object ItemPath, ItemType, PinState
```

---

## Problemi Certificati

```powershell
# === CHAIN VALIDATION — CERTIFICATO NON TRUSTED ===

# Sintomo: "Certificate is not trusted" o "Certificate chain is incomplete"

# Verificare la catena di un certificato:
certutil -verify -urlfetch C:\Temp\certificate.cer

# Verificare CRL (Certificate Revocation List):
certutil -URL C:\Temp\certificate.cer
# Apre GUI con test di revoca OCSP e CRL

# Verificare certificati nel local store:
Get-ChildItem Cert:\LocalMachine\Root       # Trusted Root CA
Get-ChildItem Cert:\LocalMachine\CA         # Intermediate CA
Get-ChildItem Cert:\LocalMachine\My         # Personal certificates

# Trovare certificati in scadenza (30 giorni):
$Threshold = (Get-Date).AddDays(30)
Get-ChildItem Cert:\LocalMachine\My |
    Where-Object { $_.NotAfter -lt $Threshold -and $_.NotAfter -gt (Get-Date) } |
    Select-Object Subject, Thumbprint, NotAfter

# Trovare certificati GIÀ scaduti:
Get-ChildItem Cert:\LocalMachine\My |
    Where-Object { $_.NotAfter -lt (Get-Date) } |
    Select-Object Subject, Thumbprint, NotAfter

# === ENROLLMENT FAILURES (AD CS) ===

# Certificato non si rinnova automaticamente:
# 1. Il template permette auto-enrollment?
certutil -template <TemplateName>
# Verificare: "Allow Enroll" e "Allow Autoenroll" per il gruppo giusto

# 2. La GPO di autoenrollment è applicata?
# Computer Config → Windows Settings → Security Settings → Public Key Policies
#   → Certificate Services Client – Auto-Enrollment → Enabled
# User Config → stessa posizione per certificati utente

# 3. Il client raggiunge la CA?
certutil -ping -config "CA_Server\CA_Name"

# 4. Richiedere manualmente un certificato:
certreq -new request.inf request.req
certreq -submit request.req certificate.cer
certreq -accept certificate.cer

# === BINDING CERTIFICATO IIS / HTTPS ===

# Verificare binding:
Get-ChildItem IIS:\SslBindings
# oppure:
netsh http show sslcert

# Se il certificato è scaduto o errato:
# 1. Importare il nuovo certificato:
Import-PfxCertificate -FilePath C:\Temp\new_cert.pfx `
    -CertStoreLocation Cert:\LocalMachine\My -Password (ConvertTo-SecureString "pw" -AsPlainText -Force)

# 2. Aggiornare il binding IIS:
#    IIS Manager → Site → Bindings → Edit → selezionare nuovo certificato
# Oppure PowerShell:
# New-WebBinding -Name "Default Web Site" -Protocol https -Port 443
# (Get-WebBinding -Name "Default Web Site" -Protocol https).AddSslCertificate($thumbprint, "My")

# === CERTIFICATE TEMPLATE PROBLEMS ===
# Errore: "The requested certificate template is not supported by this CA"
# → Il template non è pubblicato sulla CA
# → Verificare: certsrv.msc → Certificate Templates → tasto destro → New → Certificate Template to Issue

# Errore: "The permissions on the certificate template do not allow the current user to enroll"
# → L'utente/computer non ha permessi Enroll sul template
# → Verificare: certtmpl.msc → template → Security → Enroll permission

# === SCEP / NDES TROUBLESHOOTING ===
# Per enrollment da dispositivi mobili/MDM via NDES:
# Log: Event Viewer → Application → Source: NetworkDeviceEnrollmentService
# IIS log per NDES: C:\inetpub\logs → cercare /CertSrv/mscep
# Errore 500 su NDES → verificare account NDES e permessi sul template
```

---

## Troubleshooting Hyper-V

```powershell
# === VM NON SI AVVIA ===

# Verificare stato VM:
Get-VM | Select-Object Name, State, CPUUsage, MemoryAssigned, Status

# Verificare eventi Hyper-V:
Get-WinEvent -LogName "Microsoft-Windows-Hyper-V-Worker-Admin" -MaxEvents 20

# Cause comuni VM non si avvia:
# 1. Risorse insufficienti sull'host:
Get-VMHost | Select-Object MemoryCapacity, LogicalProcessorCount
# Confrontare con le VM che richiedono risorse

# 2. VHD/VHDX non trovato o corrotto:
Get-VMHardDiskDrive -VMName "VMName" | Select-Object Path
Test-Path "D:\VMs\VMName\disk.vhdx"

# 3. Conflitto MAC address:
Get-VMNetworkAdapter -VMName * | Group-Object MacAddress |
    Where-Object Count -gt 1 | Select-Object Name, Count, Group

# 4. Checkpoint corrotto:
Get-VMSnapshot -VMName "VMName" | Select-Object Name, CreationTime, ParentSnapshotName
# Rimuovere checkpoint problematico:
# Remove-VMSnapshot -VMName "VMName" -Name "SnapshotName"
# ATTENZIONE: l'eliminazione mergia il differencing disk — può richiedere tempo

# === NETWORKING VM ===

# VM non ha connettività di rete:
# 1. Verificare virtual switch:
Get-VMSwitch | Select-Object Name, SwitchType, NetAdapterInterfaceDescription
# SwitchType: External (connesso alla NIC fisica), Internal, Private

# 2. Verificare che la VM sia connessa allo switch corretto:
Get-VMNetworkAdapter -VMName "VMName" | Select-Object SwitchName, MacAddress, IPAddresses

# 3. Se VLAN configurato:
Get-VMNetworkAdapterVlan -VMName "VMName"
# Verificare che la VLAN ID corrisponda alla rete corretta

# 4. MAC Address Spoofing (necessario per NLB, nested virtualization):
Get-VMNetworkAdapter -VMName "VMName" | Select-Object MacAddressSpoofing

# === INTEGRATION SERVICES ===

# Verificare versione Integration Services:
Get-VMIntegrationService -VMName "VMName" | Select-Object Name, Enabled, PrimaryStatusDescription

# Se Integration Services non aggiornati:
# → Windows: aggiornamento tramite Windows Update
# → Linux: installare linux-tools (hyperv-daemons)

# Abilitare servizi integrazione specifici:
Enable-VMIntegrationService -VMName "VMName" -Name "Guest Service Interface"
# Guest Service Interface: necessario per Copy-VMFile
# Time Synchronization: sincronizzazione orologio
# Heartbeat: verifica che la VM sia responsiva
# Key-Value Pair Exchange: scambio dati host-guest

# === CHECKPOINT (SNAPSHOT) PROBLEMS ===

# Checkpoint chain corrotta:
Get-VHD "D:\VMs\VMName\disk.vhdx" | Select-Object VhdType, ParentPath
# Se ParentPath punta a un file che non esiste → la catena è rotta
# → La VM non può partire

# Soluzione per catena checkpoint rotta:
# 1. Identificare tutti i file AVHDX nella cartella VM
# 2. Verificare la catena: Get-VHD per ogni file
# 3. Se un parent manca → la VM è potenzialmente irrecuperabile
# 4. Se possibile, merge manuale: Merge-VHD

# === PERFORMANCE HYPER-V ===

# CPU overcommit: troppe vCPU assegnate rispetto ai pCPU
# Regola: vCPU totali ≤ 8× pCPU per carichi leggeri
$TotalVCPU = (Get-VM | Where-Object State -eq Running | Measure-Object -Property ProcessorCount -Sum).Sum
$PhysicalCPU = (Get-CimInstance Win32_Processor | Measure-Object NumberOfLogicalProcessors -Sum).Sum
"vCPU ratio: $TotalVCPU vCPU / $PhysicalCPU pCPU = $([math]::Round($TotalVCPU/$PhysicalCPU, 1)):1"

# Dynamic Memory problems:
Get-VM | Where-Object State -eq Running |
    Select-Object Name,
    @{N='AssignedMB';E={$_.MemoryAssigned/1MB}},
    @{N='DemandMB';E={$_.MemoryDemand/1MB}},
    MemoryStatus
# MemoryStatus "Warning" o "Low" → la VM non ha abbastanza memoria

# === LIVE MIGRATION FAILURES ===
# Errore: "Virtual machine migration failed"
# Cause comuni:
# 1. La destinazione non ha CPU compatibile → configurare CPU compatibility
# 2. Il virtual switch non esiste sulla destinazione → creare switch con stesso nome
# 3. Storage non raggiungibile dalla destinazione → shared storage o SMB
# 4. Delega Kerberos non configurata → configurare constrained delegation
# 5. Rete Live Migration non configurata → Hyper-V Settings → Live Migrations
```

---

## Troubleshooting Cluster

```powershell
# === FAILOVER CLUSTER — DIAGNOSTICA ===

# Stato generale cluster:
Get-Cluster | Select-Object Name, Domain
Get-ClusterNode | Select-Object Name, State, DrainStatus
Get-ClusterGroup | Select-Object Name, State, OwnerNode

# Validare cluster (test completo):
Test-Cluster -Node Node1, Node2 -ReportName C:\Temp\ClusterValidation

# === QUORUM — PROBLEMI ===

# Verificare configurazione quorum:
Get-ClusterQuorum | Select-Object Cluster, QuorumResource, QuorumType

# Tipi di quorum:
# NodeMajority: maggioranza nodi (dispari)
# NodeAndDiskMajority: nodi + disco witness
# NodeAndFileShareMajority: nodi + file share witness (raccomandato per Azure/multi-site)
# CloudWitness: nodi + Azure blob storage witness

# Se quorum perso (cluster offline):
# → Meno della metà dei nodi + witness è online
# → Forzare quorum su un nodo:
# net start clussvc /fq   ← EMERGENZA: forza quorum con un solo nodo
# ATTENZIONE: rischio split-brain se l'altra partizione è ancora attiva

# === CLUSTER SHARED VOLUMES (CSV) ===

# Stato CSV:
Get-ClusterSharedVolume | Select-Object Name, State,
    @{N='Node';E={$_.OwnerNode.Name}},
    @{N='FriendlyName';E={$_.SharedVolumeInfo.FriendlyVolumeName}}

# CSV in stato "Redirected" → I/O va attraverso la rete (lento)
# Cause:
# 1. Disco fisico degradato
# 2. Rete cluster CSV non funziona
# 3. Filtro I/O incompatibile (antivirus)

# Verificare rete CSV:
Get-ClusterNetwork | Select-Object Name, State, Role
# Role: 1 = Client access only, 3 = Client and Cluster

# === SPLIT-BRAIN ===
# Situazione in cui il cluster si divide in due partizioni
# che credono entrambe di avere il quorum → rischio di corruzione dati

# Prevenzione:
# 1. Configurare witness (disk, file share, o cloud)
# 2. Rete di heartbeat ridondante
# 3. Non forzare quorum senza verificare l'altra partizione

# Se split-brain si è verificato:
# 1. Identificare quale partizione ha i dati più recenti
# 2. Arrestare i servizi cluster sulla partizione "perdente"
# 3. Consolidare i dati manualmente
# 4. Ripristinare il cluster da una singola partizione

# === CLUSTER-AWARE UPDATING (CAU) ===
# Aggiornamento rolling senza downtime:
Get-CauRun -ClusterName Cluster01 | Select-Object Status, CurrentAction
# Se CAU si blocca:
Stop-CauRun -ClusterName Cluster01 -Force

# === EVENT LOG CLUSTER ===
Get-WinEvent -LogName "Microsoft-Windows-FailoverClustering/Operational" -MaxEvents 30 |
    Select-Object TimeCreated, Id, LevelDisplayName, Message

# Event ID critici:
# 1069: Risorsa cluster fallita
# 1146: Nodo rimosso dal cluster
# 1177: Quorum perso
# 1254: Rete cluster partitioned
```

---

## WinRE e Recovery Environment

```powershell
# WinRE (Windows Recovery Environment) fornisce:

# Troubleshoot → Advanced Options:
# ├── Startup Repair          → Ripara automaticamente problemi di boot
# ├── Startup Settings        → Safe Mode, Disable driver signing, etc.
# ├── Command Prompt          → Accesso CLI per riparazioni manuali
# ├── Uninstall Updates       → Rimuovere ultimo update
# ├── System Restore          → Ripristinare a punto precedente
# ├── System Image Recovery   → BMR da backup immagine
# └── UEFI Firmware Settings  → Accesso al BIOS/UEFI

# Da Command Prompt in WinRE:

# Riparare file di sistema
sfc /scannow /offbootdir=C:\ /offwindir=C:\Windows

# DISM offline
DISM /Image:C:\ /Cleanup-Image /RestoreHealth

# Riparare BCD
bootrec /rebuildbcd
bcdboot C:\Windows /s S: /f UEFI

# Accedere al registry offline
reg load HKLM\OfflineSystem C:\Windows\System32\config\SYSTEM
reg load HKLM\OfflineSoftware C:\Windows\System32\config\SOFTWARE
# Fare modifiche...
reg unload HKLM\OfflineSystem
reg unload HKLM\OfflineSoftware

# Reset password admin locale (da WinRE)
# 1. Rinominare utilman.exe → utilman.bak
# 2. Copiare cmd.exe → utilman.exe
# 3. Riavviare, sulla schermata di login click su Accessibility
# 4. net user Administrator NewPassword
# 5. Ripristinare utilman.exe originale
```

### WinRE — Procedure avanzate

```powershell
# === VERIFICARE E CONFIGURARE WINRE ===

# Verificare se WinRE è abilitato:
reagentc /info
# Output mostra: Windows RE status, Windows RE location, BCD identifier

# Se WinRE è disabilitato:
reagentc /enable

# Riconfigurare WinRE (se la partizione è stata spostata):
reagentc /setreimage /path C:\Recovery\WindowsRE

# === CREARE USB DI RIPRISTINO ===
# 1. Pannello di controllo → Recovery → Create a recovery drive
# 2. Spuntare "Back up system files to the recovery drive"
# 3. Selezionare USB (≥ 16 GB)
# Alternativa: scaricare Media Creation Tool per ISO completa

# === OFFLINE REGISTRY EDITING — CASI D'USO ===

# Caso 1: Disabilitare un driver che causa BSOD
reg load HKLM\OfflineSystem C:\Windows\System32\config\SYSTEM
# Navigare a: HKLM\OfflineSystem\ControlSet001\Services\<DriverName>
# Impostare Start = 4 (disabled)
reg add "HKLM\OfflineSystem\ControlSet001\Services\DriverName" /v Start /t REG_DWORD /d 4 /f
reg unload HKLM\OfflineSystem

# Caso 2: Ripristinare networking (se NLA bloccato)
reg load HKLM\OfflineSystem C:\Windows\System32\config\SYSTEM
# Verificare/modificare configurazione rete in ControlSet001\Services\Tcpip\Parameters
reg unload HKLM\OfflineSystem

# Caso 3: Abilitare Safe Mode (se bcdedit non funziona)
reg load HKLM\OfflineSystem C:\Windows\System32\config\SYSTEM
reg add "HKLM\OfflineSystem\ControlSet001\Control\SafeBoot\Minimal" /v SafeBootOption /t REG_SZ /d "Minimal" /f
reg unload HKLM\OfflineSystem

# === IN-PLACE UPGRADE (REPAIR INSTALL) ===
# Ultima risorsa prima della reinstallazione completa
# Preserva: applicazioni installate, dati utente, configurazioni
# Ricostruisce: file di sistema, component store, registry di sistema

# Procedura:
# 1. Scaricare ISO Windows della stessa versione/edizione
# 2. Montare la ISO (doppio click)
# 3. Eseguire setup.exe dalla ISO montata
# 4. Selezionare "Keep personal files and apps"
# 5. Attendere il completamento (30-90 minuti)
# 6. Verificare che tutto funzioni
# 7. Eseguire Windows Update per patch mancanti
```

---

## Troubleshooting Remoto

```powershell
# === WINRM (Windows Remote Management) ===

# Verificare se WinRM è configurato:
Test-WSMan -ComputerName SRV01

# Se WinRM non è configurato:
# Sul server remoto (come admin):
winrm quickconfig
# Oppure via PowerShell:
Enable-PSRemoting -Force

# Connessione remota interattiva:
Enter-PSSession -ComputerName SRV01

# Esecuzione comando remoto:
Invoke-Command -ComputerName SRV01 -ScriptBlock { Get-Service | Where-Object Status -eq Stopped }

# Esecuzione su più server:
Invoke-Command -ComputerName SRV01, SRV02, SRV03 -ScriptBlock {
    [PSCustomObject]@{
        Computer = $env:COMPUTERNAME
        Uptime = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
        FreeRAM = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB, 1)
    }
}

# === WINRM TROUBLESHOOTING ===

# Errore: "WinRM cannot process the request"
# 1. Verificare che il servizio WinRM sia attivo sul target:
Get-Service WinRM -ComputerName SRV01   # richiede accesso RPC
# Se non raggiungibile: sc.exe \\SRV01 query WinRM

# 2. Verificare firewall (porta 5985 HTTP, 5986 HTTPS):
Test-NetConnection -ComputerName SRV01 -Port 5985

# 3. Verificare Trusted Hosts (per workgroup, non-domain):
Get-Item WSMan:\localhost\Client\TrustedHosts
# Aggiungere server:
Set-Item WSMan:\localhost\Client\TrustedHosts -Value "SRV01,SRV02" -Force

# 4. Kerberos vs NTLM:
# In dominio: Kerberos (default, no config necessaria)
# Cross-domain o workgroup: serve TrustedHosts o HTTPS
# Forzare NTLM: -Authentication Negotiate

# 5. Credenziali specifiche:
$cred = Get-Credential
Enter-PSSession -ComputerName SRV01 -Credential $cred

# === REMOTE EVENT LOG ===

# Leggere event log da remoto
Get-WinEvent -ComputerName SRV01 -LogName System -MaxEvents 20 |
    Where-Object Level -le 2 |
    Select-Object TimeCreated, Id, LevelDisplayName, Message

# Cercare errori specifici su più server
$Servers = @("SRV01", "SRV02", "SRV03")
Invoke-Command -ComputerName $Servers -ScriptBlock {
    Get-WinEvent -FilterHashtable @{LogName='System'; Level=1,2; StartTime=(Get-Date).AddHours(-24)} `
        -MaxEvents 10 -ErrorAction SilentlyContinue |
        Select-Object @{N='Server';E={$env:COMPUTERNAME}}, TimeCreated, Id, Message
} | Sort-Object TimeCreated -Descending

# === RDP — PROBLEMI ===

# RDP non si connette:
# 1. RDP abilitato?
Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server" |
    Select-Object fDenyTSConnections
# fDenyTSConnections = 0 → abilitato, 1 → disabilitato

# Abilitare RDP da remoto (via WinRM/PsExec):
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server" `
    -Name fDenyTSConnections -Value 0
Enable-NetFirewallRule -DisplayGroup "Remote Desktop"

# 2. Porta RDP (default 3389):
Test-NetConnection -ComputerName SRV01 -Port 3389
# Se porta cambiata: verificare in registry
# HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp\PortNumber

# 3. NLA (Network Level Authentication):
Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" |
    Select-Object UserAuthentication
# UserAuthentication = 1 → NLA abilitato (richiede credenziali prima della sessione)
# Se il client non supporta NLA → disabilitare (meno sicuro)

# 4. Licenze RD (per Server con ruolo RDS):
# "Remote Desktop licensing mode is not configured"
# Verificare: Server Manager → RDS → Licensing

# 5. Sessioni RDP esaurite:
query session /server:SRV01
# Se tutte le sessioni sono in uso → disconnettere sessione inattiva:
logoff <ID> /server:SRV01

# 6. Certificato RDP non trusted:
# Il certificato self-signed predefinito genera warning
# → Configurare certificato firmato dalla CA interna via GPO:
#    Computer Config → Administrative Templates → Windows Components → Remote Desktop Services
#      → Security → Server authentication certificate template

# === PSEXEC (Alternativa a WinRM) ===
# psexec.exe \\SRV01 cmd.exe                    → CMD remoto
# psexec.exe \\SRV01 -s cmd.exe                 → CMD come SYSTEM
# psexec.exe \\SRV01 -u domain\admin -p pw cmd  → Con credenziali specifiche
# psexec.exe \\SRV01 -c C:\script.ps1           → Copia ed esegui script

# PSEXEC richiede: porta 445 (SMB) + Admin$ share accessibile
Test-NetConnection -ComputerName SRV01 -Port 445
Test-Path "\\SRV01\Admin$"
```

---

## Strumenti Sysinternals

```powershell
# Sysinternals Suite (download.sysinternals.com) o \\live.sysinternals.com\tools\

# PROCESS EXPLORER (procexp.exe)
# Task Manager avanzato: albero processi, DLL caricate, handle,
# performance per-process, GPU usage, VirusTotal integration

# PROCESS MONITOR (procmon.exe)
# Registra TUTTE le operazioni: file, registry, rete, processi
# Filtri potenti per isolare il problema
# Es: "Perché l'app non trova il file config?" → filtra per processo + result NOTFOUND

# AUTORUNS (autoruns.exe)
# TUTTO ciò che parte automaticamente: servizi, driver, scheduled task,
# logon scripts, shell extensions, BHO, codecs, etc.
# Disabilitare temporaneamente entry sospette per diagnostica

# TCPVIEW (tcpview.exe)
# Real-time: connessioni di rete per processo
# Sostituto visuale di netstat

# HANDLE (handle.exe)
# Chi sta usando un file/cartella? (file locked)
# handle.exe "C:\path\to\locked\file"

# PSEXEC (psexec.exe)
# Esecuzione remota (alternativa a Invoke-Command per ambienti senza WinRM)
# psexec \\SRV01 cmd.exe
# psexec \\SRV01 -s cmd.exe   → Come SYSTEM

# BGINFO (bginfo.exe)
# Mostra info sistema sul desktop (IP, hostname, OS, RAM)
# Utile per lab e server senza RDP bookmark

# DISKMON, RAMMAP, VMMAP — analisi dettagliata disk I/O, RAM, memoria per-processo
```

### Sysinternals — Uso avanzato

```powershell
# === PROCESS MONITOR (Procmon) — WORKFLOW DIAGNOSTICO ===

# 1. Avviare Procmon PRIMA di riprodurre il problema
# 2. Riprodurre il problema
# 3. Fermare la cattura (Ctrl+E)
# 4. Applicare filtri:

# Filtro per processo specifico:
# Filter → Filter → Process Name → is → "app.exe" → Add

# Filtro per risultato errore:
# Filter → Filter → Result → contains → "NOT FOUND" → Add
# Utile per: DLL mancanti, file config non trovati, registry key mancanti

# Filtro per operazioni specifiche:
# Filter → Filter → Operation → is → "CreateFile" → Add
# Utile per: capire quali file un'app tenta di aprire

# Combinazione potente: Process Name = app.exe AND Result = ACCESS DENIED
# → Mostra esattamente cosa l'app cerca ma non ha permessi di accedere

# 5. Esportare i risultati filtrati:
# File → Save → CSV o PML

# Trick avanzato: Boot Logging
# Options → Enable Boot Logging → Si
# Al reboot Procmon registra TUTTO dall'avvio (prima ancora del logon)
# Utile per diagnosticare problemi di boot o servizi che falliscono all'avvio

# === AUTORUNS — PULIZIA E DIAGNOSTICA ===

# Workflow:
# 1. Aprire autoruns.exe come Administrator
# 2. Options → Hide Microsoft Entries → Si (mostra solo terze parti)
# 3. Options → Scan Options → Check VirusTotal.com → Si
# 4. Tab per tab: analizzare entry sospette
#    - Logon: programmi che partono al login
#    - Services: servizi non-Microsoft
#    - Drivers: driver terze parti
#    - Scheduled Tasks: task pianificati
#    - Boot Execute: programmi eseguiti dal boot manager
# 5. Disabilitare (non eliminare!) entry sospette → uncheck checkbox
# 6. Riavviare → verificare se il problema è risolto
# 7. Se risolto → l'entry disabilitata era la causa

# === ACCESSCHK — VERIFICARE PERMESSI ===
# accesschk.exe -d "C:\ProgramData\App" → permessi directory
# accesschk.exe -k HKLM\SOFTWARE\App → permessi registry key
# accesschk.exe -c ServiceName → permessi servizio
# accesschk.exe -p ProcessName → permessi processo

# === LIVEKD — LIVE KERNEL DEBUGGING ===
# Analisi kernel senza attaccare un debugger remoto
# livekd.exe -w → apre WinDbg con accesso al kernel live
# Utile per analisi pool memory, handle kernel, driver issues
# SOLO per analisi (read-only), non per debug interattivo
```

---

## Script PowerShell Diagnostici

### Health Check completo

```powershell
# === HEALTH CHECK SERVER — SCRIPT COMPLETO ===

function Get-ServerHealthReport {
    param(
        [string]$ComputerName = $env:COMPUTERNAME
    )

    $Report = [ordered]@{}

    # 1. INFORMAZIONI SISTEMA
    $OS = Get-CimInstance Win32_OperatingSystem -ComputerName $ComputerName
    $CS = Get-CimInstance Win32_ComputerSystem -ComputerName $ComputerName
    $Report["Sistema"] = [PSCustomObject]@{
        Hostname = $CS.Name
        Domain = $CS.Domain
        OS = $OS.Caption
        Build = $OS.BuildNumber
        LastBoot = $OS.LastBootUpTime
        Uptime = ((Get-Date) - $OS.LastBootUpTime).ToString("dd\.hh\:mm\:ss")
    }

    # 2. CPU
    $CPU = Get-Counter '\Processor(_Total)\% Processor Time' -ComputerName $ComputerName -MaxSamples 3
    $AvgCPU = ($CPU.CounterSamples.CookedValue | Measure-Object -Average).Average
    $Report["CPU"] = [PSCustomObject]@{
        Utilizzo_Medio = "$([math]::Round($AvgCPU, 1))%"
        Stato = if ($AvgCPU -gt 90) { "CRITICO" } elseif ($AvgCPU -gt 70) { "ATTENZIONE" } else { "OK" }
    }

    # 3. MEMORIA
    $Report["Memoria"] = [PSCustomObject]@{
        TotalGB = [math]::Round($OS.TotalVisibleMemorySize / 1MB, 1)
        FreeGB = [math]::Round($OS.FreePhysicalMemory / 1MB, 1)
        UsedPercent = "$([math]::Round((1 - $OS.FreePhysicalMemory/$OS.TotalVisibleMemorySize)*100, 1))%"
        Stato = if ($OS.FreePhysicalMemory/$OS.TotalVisibleMemorySize -lt 0.1) { "CRITICO" }
                elseif ($OS.FreePhysicalMemory/$OS.TotalVisibleMemorySize -lt 0.2) { "ATTENZIONE" }
                else { "OK" }
    }

    # 4. DISCHI
    $Report["Dischi"] = Get-Volume -CimSession $ComputerName |
        Where-Object { $_.DriveLetter -ne $null -and $_.DriveType -eq "Fixed" } |
        Select-Object DriveLetter,
        @{N='TotalGB';E={[math]::Round($_.Size/1GB, 1)}},
        @{N='FreeGB';E={[math]::Round($_.SizeRemaining/1GB, 1)}},
        @{N='FreePercent';E={"$([math]::Round($_.SizeRemaining/$_.Size*100, 1))%"}},
        @{N='Stato';E={
            if ($_.SizeRemaining/$_.Size -lt 0.1) { "CRITICO" }
            elseif ($_.SizeRemaining/$_.Size -lt 0.2) { "ATTENZIONE" }
            else { "OK" }
        }}

    # 5. SERVIZI NON RUNNING (che dovrebbero esserlo)
    $Report["ServiziDown"] = Get-Service -ComputerName $ComputerName |
        Where-Object { $_.StartType -eq 'Automatic' -and $_.Status -ne 'Running' } |
        Select-Object Name, DisplayName, Status

    # 6. ERRORI EVENT LOG (ultime 24 ore)
    $Yesterday = (Get-Date).AddHours(-24)
    $Report["ErroriRecenti"] = Get-WinEvent -ComputerName $ComputerName -FilterHashtable @{
        LogName = 'System','Application'
        Level = 1,2
        StartTime = $Yesterday
    } -MaxEvents 20 -ErrorAction SilentlyContinue |
        Select-Object LogName, TimeCreated, ProviderName, Id, Message

    return $Report
}

# Uso:
# $report = Get-ServerHealthReport -ComputerName "SRV01"
# $report["Sistema"]
# $report["Dischi"]
# $report["ServiziDown"]
```

### One-liner diagnostici

```powershell
# === 30+ ONE-LINER DIAGNOSTICI ===

# 1. Uptime del server
(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime

# 2. Ultimo reboot
(Get-CimInstance Win32_OperatingSystem).LastBootUpTime

# 3. Chi è loggato (sessioni attive)
query user

# 4. Processi con CPU > 50%
Get-Counter '\Process(*)\% Processor Time' -MaxSamples 1 | Select-Object -ExpandProperty CounterSamples | Where-Object { $_.CookedValue -gt 50 -and $_.InstanceName -ne "_total" -and $_.InstanceName -ne "idle" } | Select-Object InstanceName, @{N='CPU%';E={[math]::Round($_.CookedValue, 1)}}

# 5. Spazio disco sotto 10%
Get-Volume | Where-Object { $_.DriveType -eq "Fixed" -and $_.SizeRemaining/$_.Size -lt 0.1 } | Select-Object DriveLetter, @{N='FreeGB';E={[math]::Round($_.SizeRemaining/1GB, 1)}}

# 6. Servizi che dovrebbero essere attivi ma non lo sono
Get-Service | Where-Object { $_.StartType -eq 'Automatic' -and $_.Status -ne 'Running' } | Select-Object Name, Status

# 7. Ultimi 10 errori critici (System log)
Get-WinEvent -FilterHashtable @{LogName='System'; Level=1} -MaxEvents 10 | Format-Table TimeCreated, ProviderName, Message -Wrap

# 8. Connessioni di rete attive per processo
Get-NetTCPConnection -State Established | Select-Object LocalPort, RemoteAddress, RemotePort, @{N='Process';E={(Get-Process -Id $_.OwningProcess -EA SilentlyContinue).Name}} | Sort-Object Process

# 9. File più grandi su C:
Get-ChildItem C:\ -Recurse -File -ErrorAction SilentlyContinue | Sort-Object Length -Descending | Select-Object -First 20 @{N='SizeMB';E={[math]::Round($_.Length/1MB)}}, FullName

# 10. Certificati in scadenza (30 giorni)
Get-ChildItem Cert:\LocalMachine\My | Where-Object { $_.NotAfter -lt (Get-Date).AddDays(30) -and $_.NotAfter -gt (Get-Date) } | Select-Object Subject, NotAfter

# 11. Ultimo Windows Update installato
Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 5

# 12. Controllare DNS resolution
Resolve-DnsName "dc01.domain.com" -ErrorAction SilentlyContinue | Select-Object Name, IPAddress

# 13. Gateway raggiungibile
Test-Connection (Get-NetRoute -DestinationPrefix 0.0.0.0/0).NextHop -Count 1 -Quiet

# 14. Scheduled tasks falliti
Get-ScheduledTask | Where-Object State -eq 'Ready' | Get-ScheduledTaskInfo | Where-Object LastTaskResult -ne 0 | Select-Object TaskName, LastTaskResult, LastRunTime

# 15. Processi senza finestra (potenziali servizi o malware)
Get-Process | Where-Object { $_.MainWindowHandle -eq 0 -and $_.SessionId -ne 0 } | Select-Object Name, Id, CPU, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB)}}

# 16. Firewall rules bloccanti
Get-NetFirewallRule -Enabled True -Direction Inbound | Where-Object Action -eq Block | Select-Object DisplayName | Measure-Object

# 17. RAM usage per processo (top 10)
Get-Process | Sort-Object WorkingSet64 -Descending | Select-Object -First 10 Name, @{N='MemMB';E={[math]::Round($_.WorkingSet64/1MB)}}

# 18. Controllare SMB shares
Get-SmbShare | Where-Object { $_.Name -notlike "*$" } | Select-Object Name, Path, CurrentUsers

# 19. Pending reboot check
Test-Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending"

# 20. BSOD count (ultimi 30 giorni)
Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='Microsoft-Windows-WER-SystemErrorReporting'; StartTime=(Get-Date).AddDays(-30)} -ErrorAction SilentlyContinue | Measure-Object

# 21. IP configuration rapida
Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" } | Select-Object InterfaceAlias, IPAddress, PrefixLength

# 22. Account AD bloccati
Search-ADAccount -LockedOut | Select-Object Name, SamAccountName, LockedOut

# 23. Password scadute (AD)
Search-ADAccount -PasswordExpired | Select-Object Name, SamAccountName, PasswordExpired

# 24. GPO applicate al computer locale
gpresult /r /scope:computer 2>$null | Select-String "Applied Group Policy"

# 25. Replica AD status rapido
repadmin /replsummary 2>$null | Select-String "error|fail"

# 26. Temperatura disco (se supportato)
Get-PhysicalDisk | Get-StorageReliabilityCounter | Select-Object DeviceId, Temperature, ReadErrorsTotal, WriteErrorsTotal

# 27. Handle count per processo (potenziali leak)
Get-Process | Where-Object HandleCount -gt 5000 | Select-Object Name, Id, HandleCount | Sort-Object HandleCount -Descending

# 28. Verifica NTP sync
w32tm /query /status 2>$null | Select-String "Source|Last Sync|Stratum"

# 29. Connessioni in stato TIME_WAIT (resource exhaustion)
(Get-NetTCPConnection -State TimeWait | Measure-Object).Count

# 30. Dimensione profili utente
Get-ChildItem C:\Users -Directory | ForEach-Object { [PSCustomObject]@{User=$_.Name; SizeMB=[math]::Round((Get-ChildItem $_.FullName -Recurse -Force -EA SilentlyContinue | Measure-Object Length -Sum).Sum/1MB)} } | Sort-Object SizeMB -Descending
```

---

## Scenari Avanzati — 30+ Casi

### Scenario 1: Server non risponde dopo aggiornamento

```
SINTOMO: Server Windows 2022 non raggiungibile dopo un patch Tuesday.
         RDP non funziona, ping OK.

DIAGNOSI:
1. ping SRV01 → OK (il server è online)
2. Test-NetConnection SRV01 -Port 3389 → FAIL (RDP non in ascolto)
3. Test-NetConnection SRV01 -Port 5985 → OK (WinRM funziona)
4. Enter-PSSession SRV01
5. Get-Service TermService → Status: Stopped
6. Get-WinEvent -LogName System -MaxEvents 10 → errore: TermService dipendenza fallita
7. Get-Service -Name TermService -RequiredServices → RpcSs (running), UmRdpService (stopped)
8. Start-Service UmRdpService → errore: file DLL mancante dopo update

SOLUZIONE:
1. sfc /scannow (via WinRM remoto)
2. DISM /Online /Cleanup-Image /RestoreHealth
3. Restart-Service TermService -Force
4. Verificare: Test-NetConnection SRV01 -Port 3389 → OK
```

### Scenario 2: Account lockout ripetuto

```
SINTOMO: Un utente si blocca ogni 15 minuti nonostante cambi la password.

DIAGNOSI:
1. Identificare la sorgente del lockout (Event ID 4740 sul PDC Emulator)
2. Il SourceComputer è un PC secondario dell'utente (portatile)
3. Sul portatile: credenziali cached in Credential Manager
4. Un mapped drive con vecchia password causa il lockout

SOLUZIONE:
1. Sul portatile: Credential Manager → rimuovere le credenziali stale
2. Disconnettere mapped drive: net use Z: /delete
3. Riconnettere con nuove credenziali
4. Verificare: nessun lockout nelle 2 ore successive
```

### Scenario 3: BSOD intermittente su cluster node

```
SINTOMO: Nodo cluster genera BSOD 1-2 volte a settimana (0xD1 DRIVER_IRQL_NOT_LESS_OR_EQUAL).

DIAGNOSI:
1. Analisi minidump con WinDbg → !analyze -v
2. IMAGE_NAME: nic_driver.sys (driver NIC Intel)
3. Verificare versione: la versione installata è 6 mesi vecchia
4. Controllare changelog driver Intel: bug fix per NIC teaming in versione recente

SOLUZIONE:
1. Scaricare driver aggiornato dal vendor
2. Drain il nodo cluster: Suspend-ClusterNode -Name Node01 -Drain
3. Installare driver aggiornato
4. Riavviare il nodo
5. Resume-ClusterNode -Name Node01
6. Monitorare: zero BSOD per 2 settimane → problema risolto
```

### Scenario 4: GPO non si applica a una OU

```
SINTOMO: La GPO "Desktop Lockdown" è linkata alla OU "Finance" ma non si applica.

DIAGNOSI:
1. gpresult /h report.html su un PC della OU Finance
2. La GPO appare in "Denied GPOs" con motivo "WMI Filter: FALSE"
3. Verificare il WMI filter della GPO:
   SELECT * FROM Win32_OperatingSystem WHERE Version LIKE '10.0.19041%'
4. I PC Finance hanno build 10.0.19045 → filter non corrisponde

SOLUZIONE:
1. Aggiornare il WMI filter: Version LIKE '10.0.%' (per tutte le versioni Win10/11)
2. gpupdate /force sui PC target
3. gpresult /h → GPO ora in "Applied GPOs"
```

### Scenario 5: DNS intermittente dopo migrazione DC

```
SINTOMO: Dopo la decommissione di un vecchio DC, alcuni client non risolvono nomi interni.

DIAGNOSI:
1. Get-DnsClientServerAddress → alcuni client puntano ancora all'IP del vecchio DC
2. Get-DhcpServerv4OptionValue -OptionId 6 → l'option DNS nel DHCP contiene ancora il vecchio IP
3. I client con lease lungo hanno ancora il vecchio DNS

SOLUZIONE:
1. Aggiornare DHCP option 6 con solo i nuovi DC
2. ipconfig /release && ipconfig /renew sui client critici
3. Attendere il refresh DHCP per gli altri
4. Verificare che nessun client punti al vecchio IP
```

### Scenario 6: Performance lenta dopo aggiornamento antivirus

```
SINTOMO: Tutti i server rallentano dopo l'aggiornamento dell'antivirus.
         CPU costantemente al 60-80%.

DIAGNOSI:
1. Get-Process | Sort-Object CPU -Descending → "MsMpEng.exe" (Windows Defender) in cima
2. Performance Monitor → Defender sta scansionando costantemente
3. Nuovo engine dell'AV esegue scansione completa su tutti i file ad ogni accesso
4. Esclusioni mancanti per database, log, file temporanei

SOLUZIONE:
1. Configurare esclusioni AV per path critici (DB, IIS logs, Exchange, SQL tempdb)
2. Configurare esclusioni per processo (sqlservr.exe, w3wp.exe)
3. Schedulare full scan fuori orario lavorativo
4. CPU torna a livelli normali (10-20%)
```

### Scenario 7: Stampa lenta da terminal server

```
SINTOMO: Stampare da RDS terminal server richiede 5+ minuti per pagina.

DIAGNOSI:
1. Verificare driver: V3 driver installato (caricato nello spooler principale)
2. La stampante è reindirizzata via RDP (printer redirection)
3. Il driver V3 genera spool file enormi (rendering lato server)
4. Il file spool viene inviato attraverso la connessione RDP (banda limitata)

SOLUZIONE:
1. Sostituire con driver V4 o Microsoft Universal Print Driver
2. Abilitare "Easy Print" (rendering lato client):
   GPO: Computer Config → Admin Templates → Windows Components → RDS → Printer Redirection
   → Use Remote Desktop Easy Print printer driver first
3. Tempo di stampa: da 5 minuti a 10 secondi
```

### Scenario 8: VM Hyper-V non migra

```
SINTOMO: Live Migration di una VM fallisce con errore di compatibilità processore.

DIAGNOSI:
1. Get-VM "VMName" | Select-Object * → ProcessorCompatibilityForMigrationEnabled = False
2. L'host di destinazione ha un processore diverso (Intel gen diversa)
3. Senza compatibility mode, le istruzioni CPU specifiche non sono mascherate

SOLUZIONE:
1. Spegnere la VM
2. Set-VMProcessor -VMName "VMName" -CompatibilityForMigrationEnabled $true
3. Avviare la VM
4. Ritentare Live Migration → successo
```

### Scenario 9: Certificate warning su sito intranet

```
SINTOMO: Tutti i browser mostrano "Certificate not trusted" per un sito intranet.

DIAGNOSI:
1. Esaminare il certificato: emesso dalla CA interna
2. Verificare catena: la Root CA è nel Trusted Root CA store?
3. Get-ChildItem Cert:\LocalMachine\Root | Where-Object Subject -like "*InternalCA*" → NON TROVATO
4. La Root CA non è stata distribuita ai client

SOLUZIONE:
1. GPO: Computer Config → Windows Settings → Security → Public Key Policies → Trusted Root CA
2. Importare il certificato della Root CA
3. gpupdate /force sui client
4. Verificare: certificato ora trusted senza warning
```

### Scenario 10: Cluster CSV in stato Redirected

```
SINTOMO: CSV di un cluster Hyper-V in stato "Redirected" → performance I/O degradata.

DIAGNOSI:
1. Get-ClusterSharedVolume → State: Online, FaultState: InRedirectedAccess
2. Controllare rete: Get-ClusterNetwork → la rete CSV è down
3. Il cavo di rete dedicato al CSV traffic è disconnesso
4. Con CSV redirected, l'I/O passa attraverso la rete cluster (lenta)

SOLUZIONE:
1. Riconnettere il cavo di rete CSV
2. Verificare: Get-ClusterNetwork → tutte le reti Up
3. Il CSV torna in "Direct" access
4. Performance I/O normalizzata
```

### Scenario 11: Windows Update fallisce con 0x80073712

```
SINTOMO: Windows Update fallisce ripetutamente con errore 0x80073712.

DIAGNOSI:
1. CBS.log mostra: "manifest hash mismatch" → component store corrotto
2. DISM /Online /Cleanup-Image /CheckHealth → "repairable"

SOLUZIONE:
1. DISM /Online /Cleanup-Image /RestoreHealth
2. sfc /scannow
3. Rieseguire Windows Update → successo
```

### Scenario 12: Utente con profilo da 15 GB

```
SINTOMO: Login di un utente richiede 8+ minuti con roaming profile.

DIAGNOSI:
1. Misurare dimensione profilo: 15 GB
2. Contenuto: cache browser (5 GB), PST Outlook (6 GB), file temporanei (4 GB)

SOLUZIONE:
1. Configurare folder redirection per Desktop, Documents, AppData\Roaming
2. Spostare PST su share di rete o migrare a Exchange Online
3. Configurare GPO per limitare dimensione cache browser
4. Pulire file temporanei
5. Profilo ridotto a 200 MB → login in 30 secondi
```

### Scenario 13: Kerberos double-hop failure

```
SINTOMO: Script PowerShell su Server A accede a Server B, ma Server B non riesce ad accedere 
         a Server C (es: IIS → SQL → File Server).

DIAGNOSI:
1. Il secondo hop fallisce perché Kerberos non inoltra il ticket
2. Kerberos delegation non configurata

SOLUZIONE:
1. Configurare Constrained Delegation sull'account del servizio intermedio
2. AD Users & Computers → Server B account → Delegation tab
3. "Trust this computer for delegation to specified services only"
4. Aggiungere il SPN del servizio target (es: CIFS/FileServer)
5. Riavviare il servizio su Server B
```

### Scenario 14: DHCP scope exhaustion

```
SINTOMO: Nuovi dispositivi non ottengono IP. APIPA (169.254.x.x) sui client.

DIAGNOSI:
1. Get-DhcpServerv4ScopeStatistics → Free: 0, InUse: 254
2. Tutti gli IP nel range sono assegnati
3. Molti lease appartengono a dispositivi non più presenti

SOLUZIONE:
1. Ridurre lease duration da 8 giorni a 4 ore (per rete con BYOD/guest)
2. Eliminare lease orfani manualmente
3. Espandere il range se necessario
4. Verificare: Free addresses > 20% dello scope
```

### Scenario 15: Service account password expired

```
SINTOMO: Servizio IIS non parte lunedì mattina. Error 1069.

DIAGNOSI:
1. Get-WinEvent → "The service did not start due to a logon failure"
2. Il service account usa un AD account con password expiry
3. La password è scaduta durante il weekend

SOLUZIONE:
1. Reset password in AD
2. Aggiornare la password nel servizio: services.msc → Log On tab
3. Start-Service W3SVC
4. PREVENZIONE: usare Group Managed Service Account (gMSA) — password gestita automaticamente da AD
```

### Scenario 16: Slow boot dopo aggiunta a dominio

```
SINTOMO: PC impiega 5+ minuti per fare boot dopo essere stato aggiunto al dominio.

DIAGNOSI:
1. Boot log: Event ID 100 → 320 secondi
2. Event ID 101 → "Group Policy Scripts" richiede 180 secondi
3. Il logon script assegnato via GPO tenta di mappare 10 drive
4. Tre server target non sono raggiungibili (spenti/migrati)

SOLUZIONE:
1. Aggiornare lo script di logon: rimuovere mapping a server inesistenti
2. Aggiungere timeout/test di raggiungibilità nello script
3. Boot time: da 320 a 45 secondi
```

### Scenario 17: Split-brain DNS

```
SINTOMO: webapp.company.com risolve in IP diversi a seconda del client.

DIAGNOSI:
1. Client interni → 10.0.1.50 (DNS interno)
2. Client esterni → 203.0.113.50 (DNS pubblico)
3. Un client interno punta al DNS 8.8.8.8 → ottiene l'IP pubblico → non raggiunge il sito

SOLUZIONE:
1. Verificare che TUTTI i client interni usino DNS interni (via DHCP)
2. Configurare split-brain DNS correttamente:
   - Zona interna: webapp.company.com → 10.0.1.50
   - Zona pubblica: webapp.company.com → 203.0.113.50
3. Rimuovere 8.8.8.8 dalle configurazioni DNS interne
```

### Scenario 18: Errore replication 8614 — tombstone lifetime exceeded

```
SINTOMO: DC in branch office offline per 200 giorni. Replica fallisce con errore 8614.

DIAGNOSI:
1. repadmin /showrepl BranchDC → Error 8614: "time since last replication exceeded tombstone lifetime"
2. Tombstone lifetime default: 180 giorni
3. Il DC ha dati inconsistenti (ha oggetti che dovrebbero essere cancellati)

SOLUZIONE:
1. NON forzare la replica (causerebbe lingering objects)
2. Demote il branch DC: Uninstall-ADDSDomainController -Force
3. Pulire metadata: ntdsutil → metadata cleanup
4. Ri-promuovere il DC da zero: Install-ADDSDomainController
5. PREVENZIONE: monitoring replica con alert su failure > 24h
```

### Scenario 19: Print Spooler crash loop su print server

```
SINTOMO: Print Spooler crasha ogni 30 secondi. Nessuna stampante funziona.

DIAGNOSI:
1. Event Viewer → Application Error → Faulting module: hpdriver.dll
2. Un driver HP V3 appena installato causa il crash
3. Il driver V3 gira nello stesso processo del Spooler → crash totale

SOLUZIONE:
1. Avviare in Safe Mode
2. Eliminare il driver HP: pnputil /delete-driver oem42.inf /force
3. Pulire coda: Remove-Item "C:\Windows\System32\spool\PRINTERS\*"
4. Riavviare → Spooler stabile
5. Installare driver HP V4 o Universal Print Driver
```

### Scenario 20: VPN Always-On non si connette

```
SINTOMO: Device tunnel VPN non si connette al boot. User tunnel funziona dopo il login.

DIAGNOSI:
1. Device tunnel richiede certificato computer → verificare certificato
2. Get-ChildItem Cert:\LocalMachine\My → certificato presente ma scaduto
3. Auto-enrollment non ha rinnovato perché il PC era offline durante il rinnovo

SOLUZIONE:
1. Connettere il PC alla rete aziendale (tramite user tunnel)
2. certutil -pulse → forza enrollment
3. Verificare: nuovo certificato emesso con validità corretta
4. Riavviare → device tunnel si connette al boot
```

### Scenario 21: Event log pieno — eventi persi

```
SINTOMO: Event log Security raggiunge la dimensione massima. Nuovi eventi persi.

DIAGNOSI:
1. Get-WinEvent -ListLog Security → MaximumSizeInBytes: 20MB (troppo piccolo per un DC)
2. LogMode: Circular (sovrascrive i vecchi — ma è pieno di eventi in 2 ore)

SOLUZIONE:
1. Aumentare la dimensione: wevtutil sl Security /ms:1073741824  (1 GB)
2. Configurare via GPO per tutti i DC:
   Computer Config → Administrative Templates → Windows Components → Event Log Service → Security
   → Maximum Log Size: 1048576 KB
3. Configurare export automatico (archiving) o SIEM forwarding
```

### Scenario 22: Scheduled task non si esegue

```
SINTOMO: Una scheduled task critica (backup) non viene eseguita da 3 giorni.

DIAGNOSI:
1. Get-ScheduledTaskInfo -TaskName "BackupDB" → LastTaskResult: 0x41301
2. 0x41301 = "The task is currently running" → la task precedente non è terminata
3. La task ha "Do not start a new instance" configurato
4. Il processo di backup è bloccato aspettando un lock sul database

SOLUZIONE:
1. Terminare il processo di backup bloccato
2. Configurare timeout: Settings → "Stop the task if it runs longer than" = 4 hours
3. Configurare: "If the task is already running" = Stop the existing instance
4. Eseguire il backup manualmente → successo
5. Verificare: la task funziona automaticamente la notte successiva
```

### Scenario 23: NIC teaming failover non funziona

```
SINTOMO: Server con NIC teaming perde connettività quando la NIC primaria si guasta.

DIAGNOSI:
1. Get-NetLbfoTeam → "Team1" con 2 NIC
2. Get-NetLbfoTeamMember → NIC1: Active, NIC2: Standby
3. Simulare guasto NIC1: Disable-NetAdapter NIC1
4. NIC2 non prende il ruolo di Active → timeout 30 secondi

SOLUZIONE:
1. Verificare che il NIC teaming mode sia corretto: Switch Independent / Active Standby
2. Il problema era la NIC2 che aveva un driver datato non compatibile con failover
3. Aggiornare driver NIC2
4. Test failover: Disable-NetAdapter NIC1 → NIC2 prende il ruolo in < 2 secondi
```

### Scenario 24: Hyper-V checkpoint merge bloccato

```
SINTOMO: VM Hyper-V mostra "Merging" nello stato da 12 ore. La VM è lenta.

DIAGNOSI:
1. La VM ha accumulato 15 checkpoint (snapshot) in 6 mesi
2. La cancellazione di un checkpoint ha avviato il merge
3. Il disco differencing è 200 GB → merge richiede tempo e I/O

SOLUZIONE:
1. NON interrompere il merge (corromperebbe il disco)
2. Attendere il completamento (può richiedere ore/giorni per dischi grandi)
3. Monitorare I/O: Get-Counter '\PhysicalDisk(*)\Disk Bytes/sec'
4. PREVENZIONE: limitare il numero di checkpoint (max 3-5)
5. Configurare backup software che non usa checkpoint Hyper-V
```

### Scenario 25: Windows Firewall blocca applicazione legittima

```
SINTOMO: Applicazione LOB (line of business) non comunica con il server.

DIAGNOSI:
1. Test-NetConnection -ComputerName AppServer -Port 8443 → TcpTestSucceeded: False
2. Temporaneamente disabilitare firewall → connessione funziona → è il firewall
3. Get-NetFirewallProfile → DefaultInboundAction: Block (corretto)
4. Non esiste una regola Allow per la porta 8443

SOLUZIONE:
1. Creare regola firewall specifica (NON disabilitare il firewall):
   New-NetFirewallRule -DisplayName "LOB App Port 8443" `
       -Direction Inbound -Protocol TCP -LocalPort 8443 `
       -Action Allow -Profile Domain -Program "C:\App\app.exe"
2. Distribuire via GPO per tutti i server interessati
3. Test-NetConnection → TcpTestSucceeded: True
```

### Scenario 26: SYSVOL replication failure (DFSR)

```
SINTOMO: GPO nuove non si propagano a tutti i DC. SYSVOL non sincronizzato.

DIAGNOSI:
1. dir \\DC01\SYSVOL\domain\Policies → 45 GPO
2. dir \\DC02\SYSVOL\domain\Policies → 42 GPO (3 mancanti)
3. Get-DfsrState → DC02: "Initial Sync" (bloccato in sync iniziale)
4. Event Viewer DC02 → DFSR → Event 4012: "DFS Replication stopped replication"

SOLUZIONE:
1. Sul DC autoritativo (DC01): impostare come primary
   (Get-DfsReplicationGroup | Get-DfsReplicatedFolder).Members dove DC01 → Primary = True
2. Sul DC non autoritativo (DC02): forzare re-inizializzazione non autoritativa
3. Attendere la sincronizzazione completa
4. Verificare: dir \\DC02\SYSVOL → 45 GPO (identico a DC01)
```

### Scenario 27: Memory leak in applicazione .NET

```
SINTOMO: Un'applicazione web .NET consuma tutta la RAM in 48 ore.

DIAGNOSI:
1. Get-Process w3wp → WorkingSet: 200 MB (cresciuto da 50 MB in 48h)
2. Performance Monitor → Process(w3wp) → Private Bytes → trend crescente
3. Procdump: procdump -ma -m 500 w3wp C:\Dumps\  (trigger a 500 MB)
4. WinDbg → !dumpheap -stat → tipo con più istanze: System.Data.SqlClient.SqlConnection
5. L'app non chiude le connessioni SQL (manca Dispose/using block)

SOLUZIONE:
1. Correggere il codice: wrappare SqlConnection in using statement
2. Come mitigazione temporanea: IIS → Application Pool → Recycling → ogni 6 ore
3. Configurare: Private Memory Limit = 1 GB (recycle automatico se supera)
```

### Scenario 28: BitLocker recovery mode inatteso

```
SINTOMO: PC entra in BitLocker Recovery Mode dopo aggiornamento BIOS.

DIAGNOSI:
1. L'aggiornamento BIOS ha modificato i PCR (Platform Configuration Registers)
2. BitLocker rileva il cambiamento come potenziale manomissione
3. Richiede la recovery key

SOLUZIONE:
1. Inserire la recovery key (da Azure AD, AD, o backup utente)
2. Dopo il boot: manage-bde -protectors -disable C: (sospendere BitLocker per 1 reboot)
3. PREVENZIONE prima di aggiornare BIOS: Suspend-BitLocker -MountPoint C: -RebootCount 1
```

### Scenario 29: RDP black screen

```
SINTOMO: Connessione RDP stabilita ma lo schermo rimane nero.

DIAGNOSI:
1. La sessione RDP si connette (credenziali accettate) ma desktop non appare
2. Cause possibili: driver GPU remoto, shell corrotta, profilo corrotto

SOLUZIONE:
1. Provare: Ctrl+Alt+End → Task Manager → File → Run → explorer.exe
2. Se funziona → Explorer/Shell non partiva automaticamente
3. Verificare registry: HKCU\Software\Microsoft\Windows NT\CurrentVersion\Winlogon → Shell = explorer.exe
4. Se profilo corrotto → rinominare profilo e fare logon con profilo nuovo
5. Se il problema è GPU: disabilitare hardware acceleration in RDP client settings
```

### Scenario 30: Cluster quorum witness fallisce

```
SINTOMO: File Share Witness non raggiungibile. Cluster in stato warning.

DIAGNOSI:
1. Get-ClusterQuorum → QuorumResource: "File Share Witness" → State: Failed
2. Test-Path "\\FILESRV\Witness$\cluster01" → False
3. Il file server witness è stato migrato senza aggiornare il cluster

SOLUZIONE:
1. Creare la share sul nuovo file server
2. Aggiornare il cluster:
   Set-ClusterQuorum -FileShareWitness "\\NEWSRV\Witness$"
3. Get-ClusterQuorum → State: Online
4. BEST PRACTICE: usare Cloud Witness (Azure Blob) per eliminare dipendenza da file server
```

### Scenario 31: Slow network copy (SMB)

```
SINTOMO: Copia file su rete locale a 10 MB/s su link da 1 Gbps.

DIAGNOSI:
1. Velocità attesa su 1 Gbps: ~110 MB/s
2. Get-SmbServerConfiguration → EncryptData: True
3. SMB Encryption causa overhead significativo su CPU deboli
4. Anche SMB Signing contribuisce al rallentamento

SOLUZIONE:
1. Se la rete è trusted (LAN interna): valutare se l'encryption è necessaria
2. Per file server non-DC: Set-SmbServerConfiguration -EncryptData $false
3. Abilitare SMB Multichannel se disponibili NIC multiple
4. Verificare RSS abilitato: Get-NetAdapterRss
5. Velocità dopo ottimizzazione: 95 MB/s
```

### Scenario 32: Errore "The trust relationship between this workstation and the primary domain has failed"

```
SINTOMO: L'utente non riesce a fare login al dominio. Messaggio di trust relationship.

DIAGNOSI:
1. Il computer account in AD ha una password che non corrisponde a quella locale
2. Causa: il PC è stato ripristinato da un backup vecchio, o è stato offline troppo a lungo

SOLUZIONE:
1. Login con account locale administrator
2. Reset-ComputerMachinePassword -Credential (Get-Credential domain\admin)
3. Riavviare il PC
4. Se non funziona: rimuovere dal dominio → riaggiungere
   Remove-Computer -Force -Restart
   Add-Computer -DomainName "domain.com" -Credential (Get-Credential) -Restart
```

---

## FAQ — Domande Frequenti

### FAQ 1: Come forzare un BSOD per test?

```
# Da un kernel debugger o con NotMyFault (Sysinternals):
# notmyfault.exe /crash → genera BSOD immediato
# SOLO in ambiente test/lab
# Utile per verificare che la configurazione dump funzioni
```

### FAQ 2: Come recuperare file da un disco che non fa boot?

```
# 1. Collegare il disco come secondario in un altro PC
# 2. Se il disco è leggibile → copiare i file
# 3. Se il disco è BitLocker → serve la recovery key
#    manage-bde -unlock D: -RecoveryPassword XXXXXX-XXXXXX-...
# 4. Se il disco ha errori → chkdsk D: /r (dal PC funzionante)
# 5. Se il disco non viene riconosciuto → problema hardware → recovery specializzato
```

### FAQ 3: sfc /scannow trova errori ma non li ripara. Cosa fare?

```
# 1. Eseguire prima DISM per riparare il component store:
DISM /Online /Cleanup-Image /RestoreHealth
# 2. Poi rieseguire sfc /scannow
# 3. Se DISM fallisce → specificare sorgente:
DISM /Online /Cleanup-Image /RestoreHealth /Source:D:\sources\install.wim
# 4. Se ancora fallisce → eseguire in WinRE (offline):
sfc /scannow /offbootdir=C:\ /offwindir=C:\Windows
# 5. Ultimo resort: in-place upgrade (preserva dati e app)
```

### FAQ 4: Come identificare quale processo sta usando un file (file locked)?

```powershell
# Con handle.exe (Sysinternals):
# handle.exe "C:\path\to\locked\file"
# Output: app.exe pid: 1234 type: File C5C: C:\path\to\locked\file

# Con Resource Monitor:
# CPU tab → Associated Handles → cercare il nome del file

# Con PowerShell (approssimativo):
Get-Process | ForEach-Object {
    try { $_.Modules | Where-Object FileName -like "*filename*" } catch {}
} | Select-Object FileName
```

### FAQ 5: Come monitorare la replica AD in modo proattivo?

```powershell
# Script di monitoraggio replica (da eseguire come scheduled task):
$Results = repadmin /replsummary /bysrc /bydest 2>&1
if ($Results -match "fail|error") {
    Send-MailMessage -To "admin@domain.com" -From "monitoring@domain.com" `
        -Subject "AD Replication Error Detected" `
        -Body ($Results | Out-String) -SmtpServer "smtp.domain.com"
}
```

### FAQ 6: Come pulire lo spazio disco su un server Windows?

```powershell
# 1. Pulire component store:
DISM /Online /Cleanup-Image /StartComponentCleanup /ResetBase

# 2. Pulire profili utente vecchi:
Get-CimInstance Win32_UserProfile | Where-Object {
    $_.Special -eq $false -and $_.LastUseTime -lt (Get-Date).AddDays(-90)
} | Select-Object LocalPath, LastUseTime
# Rimuovere: Remove-CimInstance (verificare prima!)

# 3. Pulire log IIS vecchi:
Get-ChildItem "C:\inetpub\logs" -Recurse -File |
    Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-30) } |
    Remove-Item -Force

# 4. Pulire Windows Update cache:
Stop-Service wuauserv
Remove-Item "C:\Windows\SoftwareDistribution\Download\*" -Recurse -Force
Start-Service wuauserv

# 5. Comprimere cartelle vecchie:
compact /c /s:"C:\Logs\Archive" /i
```

### FAQ 7: Come verificare se un server necessita di reboot?

```powershell
function Test-PendingReboot {
    $Pending = @()
    # Windows Update
    if (Test-Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired") {
        $Pending += "WindowsUpdate"
    }
    # Component Based Servicing
    if (Test-Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending") {
        $Pending += "CBS"
    }
    # Pending file rename operations
    $PFR = Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager" -Name PendingFileRenameOperations -ErrorAction SilentlyContinue
    if ($PFR.PendingFileRenameOperations) {
        $Pending += "FileRename"
    }
    # Computer name change
    $ActiveName = (Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\ComputerName\ActiveComputerName").ComputerName
    $PendingName = (Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\ComputerName\ComputerName").ComputerName
    if ($ActiveName -ne $PendingName) {
        $Pending += "ComputerRename"
    }

    [PSCustomObject]@{
        Computer = $env:COMPUTERNAME
        RebootPending = $Pending.Count -gt 0
        Reasons = $Pending -join ", "
    }
}
Test-PendingReboot
```

### FAQ 8: Come resettare tutte le policy di Windows Firewall?

```powershell
# Reset completo (ATTENZIONE: rimuove TUTTE le regole personalizzate)
netsh advfirewall reset

# Alternativa: reset solo un profilo
Set-NetFirewallProfile -Profile Domain -DefaultInboundAction Block -DefaultOutboundAction Allow
# Poi aggiungere le regole necessarie
```

### FAQ 9: Come esportare e importare un certificato con catena completa?

```powershell
# Esportare con chiave privata (PFX):
$Cert = Get-ChildItem Cert:\LocalMachine\My | Where-Object Subject -like "*webapp*"
$Password = ConvertTo-SecureString "P@ssw0rd" -AsPlainText -Force
Export-PfxCertificate -Cert $Cert -FilePath C:\Temp\webapp.pfx -Password $Password -ChainOption BuildChain
# -ChainOption BuildChain include tutta la catena

# Importare:
Import-PfxCertificate -FilePath C:\Temp\webapp.pfx `
    -CertStoreLocation Cert:\LocalMachine\My -Password $Password
```

### FAQ 10: Come abilitare il debug logging di Group Policy?

```powershell
# Abilitare GPO debug logging (verbose):
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Diagnostics" /v GPSvcDebugLevel /t REG_DWORD /d 0x30002 /f

# Riavviare o eseguire gpupdate /force
# Log generato in: C:\Windows\debug\usermode\gpsvc.log

# DISABILITARE dopo il debug (impatto performance):
reg delete "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Diagnostics" /v GPSvcDebugLevel /f
```

### FAQ 11: Come diagnosticare problemi WMI?

```powershell
# Verificare stato WMI
winmgmt /verifyrepository
# Output: "WMI repository is consistent" = OK
# "WMI repository is INCONSISTENT" = corrotto

# Ricostruire repository WMI (ultimo resort):
winmgmt /salvagerepository
# Se non funziona:
winmgmt /resetrepository
# ATTENZIONE: resetrepository cancella tutte le classi/istanze custom
```

### FAQ 12: Come trovare quale GPO ha impostato una specifica chiave di registro?

```powershell
# gpresult mostra le GPO applicate ma non mappa ogni singola chiave
# Usare rsop.msc per navigare graficamente le policy risultanti

# Per una chiave specifica: cercare nelle GPO
Get-GPO -All | ForEach-Object {
    $GPO = $_
    $Report = Get-GPOReport -Guid $GPO.Id -ReportType Xml
    if ($Report -like "*NomeChiaveRegistro*") {
        [PSCustomObject]@{
            GPOName = $GPO.DisplayName
            GPOId = $GPO.Id
        }
    }
}
```

### FAQ 13: Come diagnosticare lentezza del login?

```powershell
# Event Viewer → Applications and Services Logs →
#   Microsoft → Windows → GroupPolicy → Operational
# Cercare Event ID 4001 (inizio processing) e 8001 (fine processing)
# La differenza è il tempo totale di GPO processing

# Oppure:
Get-WinEvent -LogName "Microsoft-Windows-GroupPolicy/Operational" |
    Where-Object { $_.Id -in 4001, 8001 } |
    Select-Object -First 10 TimeCreated, Id, Message

# Altre cause di login lento:
# - Logon scripts che eseguono mapping a server non raggiungibili
# - Roaming profile grande
# - Folder redirection verso share lenta
# - Molte GPO (>50) applicate all'utente
# - Printer mapping via GPO a printer non raggiungibili
```

### FAQ 14: Come configurare un Group Managed Service Account (gMSA)?

```powershell
# Prerequisiti: schema AD ≥ Windows Server 2012, KDS root key creata

# 1. Creare KDS root key (una volta per forest, attesa 10h per replica):
Add-KdsRootKey -EffectiveTime (Get-Date).AddHours(-10)
# -10h solo in lab. In produzione: Add-KdsRootKey -EffectiveImmediately (attende replica)

# 2. Creare gMSA:
New-ADServiceAccount -Name "gMSA_IIS" `
    -DNSHostName "gmsa_iis.domain.com" `
    -PrincipalsAllowedToRetrieveManagedPassword "WebServers_Group"

# 3. Sul server target:
Install-ADServiceAccount -Identity "gMSA_IIS"
Test-ADServiceAccount -Identity "gMSA_IIS"  # True = OK

# 4. Configurare il servizio per usare il gMSA:
# Nome: domain\gMSA_IIS$ (nota il $ finale)
# Password: lasciare vuota (gestita da AD)
```

### FAQ 15: Come diagnosticare un errore "Access Denied" generico?

```powershell
# 1. Verificare chi sei:
whoami /all   # utente, gruppi, privilegi

# 2. Verificare permessi sulla risorsa:
icacls "C:\path\to\resource"
# Oppure:
Get-Acl "C:\path\to\resource" | Format-List

# 3. Verificare se UAC sta interferendo:
# L'utente è admin ma il processo non è elevato? → Run as Administrator

# 4. Verificare Event Log Security per audit failure:
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4656,4663} -MaxEvents 10

# 5. Se la risorsa è una share:
# Verificare SHARE permissions E NTFS permissions
# Il permesso effettivo è l'intersezione (il più restrittivo)

# 6. Se la risorsa è un servizio:
# sc.exe sdshow ServiceName → mostra il Security Descriptor in SDDL
```

### FAQ 16: Come svuotare la coda di stampa bloccata?

```powershell
Stop-Service Spooler -Force
Remove-Item "C:\Windows\System32\spool\PRINTERS\*" -Force
Start-Service Spooler
Get-PrintJob -PrinterName * | Remove-PrintJob
```

### FAQ 17: Come verificare la versione TLS supportata da un server?

```powershell
# Verificare protocolli TLS abilitati nel registry:
$Protocols = @("SSL 2.0", "SSL 3.0", "TLS 1.0", "TLS 1.1", "TLS 1.2", "TLS 1.3")
foreach ($Protocol in $Protocols) {
    $ServerPath = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\$Protocol\Server"
    $Enabled = (Get-ItemProperty $ServerPath -Name "Enabled" -ErrorAction SilentlyContinue).Enabled
    $DisabledByDefault = (Get-ItemProperty $ServerPath -Name "DisabledByDefault" -ErrorAction SilentlyContinue).DisabledByDefault
    [PSCustomObject]@{
        Protocol = $Protocol
        Enabled = if ($Enabled -eq 0) { "No" } elseif ($Enabled -eq 1) { "Yes" } else { "Default" }
        DisabledByDefault = $DisabledByDefault
    }
}
# Best practice: TLS 1.2 e 1.3 abilitati, tutto il resto disabilitato
```

### FAQ 18: Come convertire un file ETL (Event Trace Log) in formato leggibile?

```powershell
# Per log di Windows Update:
Get-WindowsUpdateLog   # Converte i .etl in WindowsUpdate.log leggibile

# Per capture di rete (pktmon):
pktmon etl2pcap C:\Temp\capture.etl --out C:\Temp\capture.pcapng
# Aprire con Wireshark

# Per Performance Trace:
# tracerpt C:\Temp\trace.etl -o C:\Temp\trace.csv -of CSV
```

### FAQ 19: Come fare rollback di un driver dopo BSOD?

```powershell
# Se riesci a fare boot:
# Device Manager → dispositivo → Properties → Driver → Roll Back Driver

# Se non riesci a fare boot:
# 1. WinRE → Command Prompt
# 2. Identificare il driver:
DISM /Image:C:\ /Get-Drivers | findstr /i "driver_problematico"
# 3. Rimuovere:
DISM /Image:C:\ /Remove-Driver /Driver:oem42.inf
# 4. Riavviare
```

### FAQ 20: Come configurare Windows per generare dump completi?

```powershell
# Impostare dump completo (necessita pagefile >= RAM su C:)
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\CrashControl" -Name "CrashDumpEnabled" -Value 1
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\CrashControl" -Name "AutoReboot" -Value 1

# Verificare pagefile (deve essere >= RAM fisica):
$RAM = (Get-CimInstance Win32_PhysicalMemory | Measure-Object Capacity -Sum).Sum / 1GB
$PF = Get-CimInstance Win32_PageFileUsage | Select-Object AllocatedBaseSize
Write-Host "RAM: $RAM GB — Pagefile: $($PF.AllocatedBaseSize / 1024) GB"

# Se pagefile è troppo piccolo → configurare:
# System Properties → Advanced → Performance → Advanced → Virtual Memory → Change
# Uncheck "Automatically manage" → Custom size → Initial = RAM GB, Maximum = RAM*1.5
```

### FAQ 21: Differenza tra Safe Mode, Safe Mode with Networking e Safe Mode with Command Prompt?

```
Safe Mode (Minimal):
  → Solo driver e servizi essenziali
  → Nessuna rete
  → GUI Explorer disponibile
  → Uso: rimuovere driver/software problematici

Safe Mode with Networking:
  → Come Minimal + driver e servizi di rete
  → Accesso a internet/LAN
  → Uso: scaricare driver/fix dalla rete, accesso a condivisioni

Safe Mode with Command Prompt:
  → Solo driver essenziali
  → Nessuna rete
  → Solo Command Prompt (niente Explorer)
  → Uso: quando Explorer stesso è il problema
```

### FAQ 22: Come disabilitare un servizio da WinRE se impedisce il boot?

```powershell
# Da WinRE → Command Prompt:
# 1. Caricare il registry offline:
reg load HKLM\OfflineSystem C:\Windows\System32\config\SYSTEM

# 2. Trovare il servizio:
reg query "HKLM\OfflineSystem\ControlSet001\Services\NomeServizio"

# 3. Disabilitare (Start = 4):
reg add "HKLM\OfflineSystem\ControlSet001\Services\NomeServizio" /v Start /t REG_DWORD /d 4 /f

# 4. Scaricare il registry:
reg unload HKLM\OfflineSystem

# 5. Riavviare → il servizio non partirà
# 6. Una volta nel sistema, diagnosticare e risolvere il problema del servizio
# 7. Riabilitare il servizio: Set-Service -Name "NomeServizio" -StartupType Automatic
```

---

## Quick Reference — Comandi Diagnostici

### Cheat Sheet — Comandi per categoria

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    QUICK REFERENCE — TROUBLESHOOTING                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ─── INFORMAZIONI SISTEMA ───                                              ║
║  systeminfo                                  Info completa OS + HW         ║
║  msinfo32                                    GUI info sistema dettagliata  ║
║  Get-ComputerInfo                            PowerShell system info        ║
║  hostname                                    Nome computer                 ║
║  whoami /all                                 Utente, gruppi, privilegi     ║
║                                                                            ║
║  ─── EVENT LOG ───                                                         ║
║  eventvwr.msc                                Event Viewer GUI              ║
║  Get-WinEvent -LogName System -Max 20        Ultimi 20 eventi System       ║
║  Get-WinEvent -FilterHashtable @{            Filtro per ID e source        ║
║      LogName='System'; Id=7034}                                            ║
║  wevtutil qe System /c:10 /f:text           Ultimi 10 eventi (CLI)        ║
║                                                                            ║
║  ─── RETE ───                                                              ║
║  ipconfig /all                               Configurazione IP completa   ║
║  Get-NetIPConfiguration                      PowerShell net config         ║
║  Test-Connection <host>                      Ping                          ║
║  Test-NetConnection <host> -Port <n>         Test porta TCP                ║
║  tracert <host>                              Traceroute                    ║
║  nslookup <host>                             Query DNS (classico)          ║
║  Resolve-DnsName <host>                      Query DNS (PowerShell)        ║
║  netstat -an                                 Connessioni e porte attive    ║
║  Get-NetTCPConnection                        Connessioni TCP (PowerShell)  ║
║  route print                                 Tabella routing               ║
║  Get-NetRoute                                Routing (PowerShell)          ║
║  arp -a                                      Tabella ARP                   ║
║  Get-NetNeighbor                             ARP (PowerShell)              ║
║  netsh wlan show profiles                    Profili WiFi salvati          ║
║                                                                            ║
║  ─── DNS ───                                                               ║
║  ipconfig /flushdns                          Svuota cache DNS client       ║
║  Clear-DnsClientCache                        Flush DNS (PowerShell)        ║
║  ipconfig /registerdns                       Registra record DNS           ║
║  Get-DnsClientCache                          Mostra cache DNS              ║
║  Get-DnsClientServerAddress                  DNS server configurati        ║
║  dcdiag /test:dns /v                         Diagnostica DNS AD            ║
║                                                                            ║
║  ─── ACTIVE DIRECTORY ───                                                  ║
║  dcdiag /v /c /e                             Diagnostica completa AD       ║
║  repadmin /replsummary                       Sommario replica              ║
║  repadmin /showrepl <DC>                     Dettaglio replica             ║
║  repadmin /syncall <DC> /APed                Forza sync completa           ║
║  nltest /dsgetdc:domain.com                  Trova DC per il dominio       ║
║  nltest /sc_query:domain.com                 Verifica secure channel       ║
║  netdom query fsmo                           Chi ha i ruoli FSMO           ║
║  w32tm /query /status                        Stato sync orologio           ║
║                                                                            ║
║  ─── GROUP POLICY ───                                                      ║
║  gpresult /h report.html                     Report GPO completo (HTML)    ║
║  gpresult /r                                 Report GPO sommario           ║
║  gpupdate /force                             Forza refresh GPO             ║
║  rsop.msc                                    Resultant Set of Policy       ║
║                                                                            ║
║  ─── SERVIZI ───                                                           ║
║  Get-Service | Where Status -ne Running      Servizi non attivi            ║
║  sc.exe query <service>                      Stato servizio (cmd)          ║
║  sc.exe qfailure <service>                   Recovery options              ║
║  Get-Service <name> -RequiredServices        Dipendenze servizio           ║
║                                                                            ║
║  ─── DISCHI E FILE SYSTEM ───                                              ║
║  Get-Volume                                  Stato volumi                  ║
║  Get-PhysicalDisk                            Stato dischi fisici           ║
║  chkdsk C: /r                                Verifica e ripara (reboot)    ║
║  fsutil fsinfo drives                        Elenco drive                  ║
║  Get-Partition                               Partizioni                    ║
║  Optimize-Volume -DriveLetter C              Ottimizza (defrag/TRIM)       ║
║                                                                            ║
║  ─── PERFORMANCE ───                                                       ║
║  Get-Process | Sort CPU -Desc | Select -F 10 Top 10 CPU                   ║
║  Get-Process | Sort WorkingSet64 -Desc       Top memoria                   ║
║  Get-Counter '\Processor(_Total)\% ...'      Contatore CPU                 ║
║  perfmon.msc                                 Performance Monitor           ║
║  resmon.exe                                  Resource Monitor              ║
║  perfmon /rel                                Reliability Monitor           ║
║                                                                            ║
║  ─── BOOT E RECOVERY ───                                                   ║
║  bcdedit /enum all                           BCD entries                   ║
║  bootrec /fixmbr                             Ripara MBR                    ║
║  bootrec /fixboot                            Ripara boot sector            ║
║  bootrec /rebuildbcd                         Ricostruisce BCD              ║
║  bcdboot C:\Windows /s S: /f UEFI           Ripara boot UEFI              ║
║  sfc /scannow                                Verifica file sistema         ║
║  DISM /Online /Cleanup-Image /RestoreHealth  Ripara component store        ║
║  reagentc /info                              Stato WinRE                   ║
║                                                                            ║
║  ─── WINDOWS UPDATE ───                                                    ║
║  Get-WindowsUpdateLog                        Genera log WU leggibile       ║
║  Get-HotFix | Sort InstalledOn -Desc         Aggiornamenti installati     ║
║  wuauclt /detectnow                          Forza check aggiornamenti     ║
║  usoclient StartInteractiveScan              Scan WU (Win10/11)            ║
║                                                                            ║
║  ─── CERTIFICATI ───                                                       ║
║  certlm.msc                                 Cert store computer           ║
║  certmgr.msc                                Cert store utente             ║
║  certutil -verify -urlfetch <cert>           Verifica catena               ║
║  Get-ChildItem Cert:\LocalMachine\My         Certificati personal          ║
║                                                                            ║
║  ─── HYPER-V ───                                                           ║
║  Get-VM                                      Stato VM                      ║
║  Get-VMSwitch                                Virtual switch                ║
║  Get-VMSnapshot -VMName <name>               Checkpoint/snapshot           ║
║  Get-VMNetworkAdapter -VMName <name>         NIC virtuali                  ║
║                                                                            ║
║  ─── CLUSTER ───                                                           ║
║  Get-ClusterNode                             Nodi cluster                  ║
║  Get-ClusterGroup                            Gruppi cluster                ║
║  Get-ClusterQuorum                           Stato quorum                  ║
║  Get-ClusterSharedVolume                     CSV stato                     ║
║  Test-Cluster                                Validazione cluster           ║
║                                                                            ║
║  ─── REMOTE ───                                                            ║
║  Enter-PSSession -ComputerName <host>        Sessione remota PS            ║
║  Invoke-Command -ComputerName <host> ...     Comando remoto                ║
║  Test-WSMan -ComputerName <host>             Verifica WinRM                ║
║  query user /server:<host>                   Sessioni utente remote        ║
║  mstsc /v:<host>                             RDP client                    ║
║                                                                            ║
║  ─── STAMPA ───                                                            ║
║  Get-Printer                                 Stampanti installate          ║
║  Get-PrintJob -PrinterName <name>            Lavori in coda                ║
║  Restart-Service Spooler                     Riavvio spooler               ║
║                                                                            ║
║  ─── SYSINTERNALS ───                                                      ║
║  procexp.exe                                 Process Explorer              ║
║  procmon.exe                                 Process Monitor               ║
║  autoruns.exe                                Startup items                 ║
║  tcpview.exe                                 Connessioni rete real-time    ║
║  handle.exe <path>                           Chi usa un file               ║
║  psexec \\<host> cmd                         Esecuzione remota             ║
║  accesschk.exe                               Verifica permessi             ║
║  livekd.exe                                  Live kernel debug             ║
║                                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Checklist Troubleshooting Rapida

| Problema | Primo Comando |
|----------|--------------|
| Server non risponde | `Test-Connection`, `Test-NetConnection -Port 3389` |
| Servizio down | `Get-Service Name`, Event Viewer System |
| Login fallisce | Event Viewer Security (4625), `dsregcmd /status` |
| DNS non risolve | `Resolve-DnsName`, `Clear-DnsClientCache` |
| AD replica fallisce | `repadmin /replsummary`, `dcdiag /test:replications` |
| Disco pieno | `Get-Volume`, `Get-ChildItem -Recurse \| Measure-Object Length -Sum` |
| Performance lenta | Task Manager → Performance, `Get-Process \| Sort CPU` |
| BSOD | `C:\Windows\Minidump\` → WinDbg → `!analyze -v` |
| GPO non applicata | `gpresult /h report.html`, `gpupdate /force` |
| Aggiornamento fallito | `Get-WindowsUpdateLog`, DISM + SFC |
| Certificato scaduto | `Get-ChildItem Cert:\LocalMachine\My \| Where NotAfter -lt (Get-Date)` |
| Stampante bloccata | `Stop-Service Spooler`, pulire spool, `Start-Service Spooler` |
| Profilo temporaneo | Registry `ProfileList` → rinominare entry `.bak` |
| Account bloccato | Event ID 4740 su PDC Emulator → sorgente lockout |
| Kerberos errore | `klist`, `w32tm /query /status`, `setspn -X` |
| VM non parte | `Get-VM`, Event Viewer Hyper-V, VHD exists? |
| Cluster degradato | `Get-ClusterNode`, `Get-ClusterGroup`, `Get-ClusterQuorum` |
| WinRM non funziona | `Test-WSMan`, `Test-NetConnection -Port 5985`, TrustedHosts |
| RDP non connette | `fDenyTSConnections`, firewall 3389, `query session` |
| VPN fallisce | Event Log RasClient, test porta 443/500, certificato |
| SMB accesso negato | Share permissions + NTFS permissions, `Test-NetConnection -Port 445` |
| Boot loop | WinRE → Startup Repair → Safe Mode → bootrec |
| DHCP no IP | `ipconfig /release /renew`, DHCP scope statistics |
| Trust relationship broken | `Reset-ComputerMachinePassword` |
| Scheduled task fallita | `Get-ScheduledTaskInfo`, `LastTaskResult` |
| Memory leak | `Get-Process \| Sort WorkingSet64`, monitorare nel tempo |
| Handle leak | `Get-Process \| Where HandleCount -gt 5000` |
| Disk I/O saturo | `Get-Counter '\PhysicalDisk(*)\Avg. Disk Queue Length'` |
| NIC teaming fail | `Get-NetLbfoTeam`, `Get-NetLbfoTeamMember` |
| SYSVOL non sincro | `Get-DfsrState`, `dfsrdiag pollad` |
| File locked | `handle.exe "path"`, Resource Monitor → CPU → Handles |

---

## Esercizi

### Esercizio 1 — Concettuale: Metodologia di troubleshooting strutturata

Descrivi le fasi di una metodologia di troubleshooting strutturata (identificazione, isolamento, diagnosi, risoluzione, documentazione). Per ciascuna fase, indica quale strumento Windows (Event Viewer, Reliability Monitor, Procmon, WinDbg, gpresult) è più appropriato e perché.

### Esercizio 2 — Lab: Analisi BSOD con WinDbg

1. Recuperare un file minidump da `C:\Windows\Minidump\` (o generare un crash controllato in una VM di test).
2. Aprire il dump in WinDbg Preview.
3. Eseguire `!analyze -v` e identificare: bugcheck code, driver colpevole, stack trace.
4. Documentare la root cause analysis e la remediation proposta.

### Esercizio 3 — Scenario: GPO non applicata dopo la migrazione di un server

Un server Windows è stato spostato nella OU "Servers-Prod" ma le GPO di hardening non si applicano. L'amministratore ha già eseguito `gpupdate /force`. Costruisci un albero decisionale di diagnosi: verifica ordine LSDOU, security filtering, WMI filter, link status, `gpresult /h`, Event ID 1085/1125, e verifica replica SYSVOL.

### Esercizio 4 — Design: Dashboard di monitoraggio proattivo

Progetta una dashboard di monitoraggio proattivo per un ambiente con 200 server Windows. Definisci: Event ID critici da raccogliere (4740, 1074, 6008, 7034, 36874, etc.), soglie performance counter (CPU, disco, memoria), alert automatici, e integrazione con un SIEM. Specifica la retention policy per i log.

---

## Auto-valutazione

<details>
<summary>1. Quali sono i tre log principali di Event Viewer e cosa contiene ciascuno?</summary>

**Application:** eventi generati da applicazioni e servizi (crash, errori .NET, errori SQL). **Security:** eventi di audit (logon/logoff, accesso a file, cambio policy, Event ID 4624/4625/4740). **System:** eventi del kernel, driver, servizi Windows (avvio/arresto servizi, errori disco, errori rete). Per il troubleshooting si parte sempre dal log più pertinente al sintomo.
</details>

<details>
<summary>2. Come si analizza un BSOD quando il server è già ripartito?</summary>

Recuperare il minidump da `C:\Windows\Minidump\` (o il full dump da `%SystemRoot%\MEMORY.DMP` se configurato). Aprirlo con WinDbg Preview, eseguire `!analyze -v` per ottenere il bugcheck code, il modulo colpevole e lo stack trace. Correlare con il driver o componente identificato. Verificare aggiornamenti driver/firmware.
</details>

<details>
<summary>3. Qual è la sequenza di precedenza delle GPO (LSDOU)?</summary>

Local → Site → Domain → OU (dalla OU più esterna alla più interna). Le policy applicate per ultime vincono (la OU più specifica prevale). Eccezioni: Enforced (No Override) sulla GPO la fa prevalere anche su OU più specifiche. Block Inheritance sulla OU blocca le policy dei livelli superiori (tranne le Enforced).
</details>

<details>
<summary>4. Un servizio critico si arresta ripetutamente. Come si diagnostica?</summary>

1. Event Viewer → System: cercare Event ID 7034 (crash) o 7031 (terminazione inaspettata). 2. Application log: cercare l'errore dell'applicazione stessa. 3. `sc qfailure <servizio>` per verificare le recovery action configurate. 4. Procmon con filtro sul processo del servizio per identificare file/registry access denied. 5. Procdump per generare un crash dump al prossimo crash (`procdump -ma -e -w <processo>`).
</details>

<details>
<summary>5. Come si verifica se un problema DNS è la causa di un malfunzionamento AD?</summary>

`nslookup` o `Resolve-DnsName` per verificare la risoluzione dei record SRV (`_ldap._tcp.dc._msdcs.<dominio>`). `dcdiag /test:DNS` per un test completo della configurazione DNS del DC. `nltest /dsgetdc:<dominio>` per verificare la localizzazione del DC. Controllare Event ID 4013 (DNS Server non riesce a caricare le zone integrate in AD).
</details>

<details>
<summary>6. Cosa fa Reliability Monitor e quando è preferibile a Event Viewer?</summary>

Reliability Monitor mostra una timeline grafica della stabilità del sistema con un indice di stabilità (1-10). Aggrega crash applicazioni, errori Windows, warning hardware e installazioni software in una vista cronologica. È preferibile a Event Viewer per avere una visione d'insieme rapida della salute del sistema nel tempo, identificare correlazioni tra eventi e installazioni.
</details>

<details>
<summary>7. Come si diagnostica un problema di performance disco su un server?</summary>

1. Task Manager → Performance → Disco per una vista immediata. 2. Resource Monitor → Disk per identificare i processi che generano più I/O. 3. Performance Monitor: `\PhysicalDisk(*)\Avg. Disk Queue Length` (>2 per spindle = collo di bottiglia), `\PhysicalDisk(*)\% Disk Time`, `\PhysicalDisk(*)\Avg. Disk sec/Read` (>20ms = lento). 4. `Get-Counter` in PowerShell per raccolta dati automatizzata. 5. `stordiag.exe` per diagnostica storage completa.
</details>

<details>
<summary>8. Qual è la differenza tra Procmon e Process Explorer e quando si usa ciascuno?</summary>

**Procmon** cattura in tempo reale tutte le operazioni di file system, registry e rete di ogni processo — ideale per diagnosticare "perché l'applicazione X fallisce" (access denied, file not found, registry key mancante). **Process Explorer** mostra lo stato corrente dei processi (DLL caricate, handle aperti, risorse consumate) — ideale per identificare cosa sta consumando risorse o quale processo detiene un file.
</details>

---

## Letture primarie consigliate

- Microsoft Learn — Windows Event Log. https://learn.microsoft.com/en-us/windows/win32/eventlog/event-logging (consultato: 2026-05-23)
- Microsoft Learn — Sysinternals Suite. https://learn.microsoft.com/en-us/sysinternals/ (consultato: 2026-05-23)
- Microsoft Learn — Troubleshoot Group Policy. https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/troubleshoot/troubleshoot-group-policy (consultato: 2026-05-23)
- Microsoft Learn — Blue Screen Troubleshooting. https://learn.microsoft.com/en-us/troubleshoot/windows-client/performance/stop-error-or-blue-screen-error-troubleshooting (consultato: 2026-05-23)
- Microsoft Learn — Windows Recovery Environment (WinRE). https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/windows-recovery-environment--windows-re--technical-reference (consultato: 2026-05-23)

---

## Collegamenti incrociati

| Modulo | Relazione con questo capitolo |
|---|---|
| [01-active-directory.md](01-active-directory.md) | Active Directory — troubleshooting replica, FSMO, trust |
| [02-powershell.md](02-powershell.md) | PowerShell — strumento primario per diagnostica e automazione troubleshooting |
| [06-rete-windows.md](06-rete-windows.md) | Networking — diagnosi DNS, DHCP, NIC teaming, firewall |
| [09-monitoraggio-performance.md](09-monitoraggio-performance.md) | Performance counter, baseline, soglie di allarme |
| [21-group-policy-guida-completa.md](21-group-policy-guida-completa.md) | GPO — troubleshooting precedenza, filtering, replica SYSVOL |

---

## Glossario locale

| Termine | Definizione |
|---|---|
| **Event Viewer** | Console MMC per la visualizzazione e l'analisi dei log di Windows (Application, Security, System, e log personalizzati). |
| **Reliability Monitor** | Strumento che mostra una timeline grafica con indice di stabilità del sistema (1-10), aggregando crash, errori e installazioni. |
| **Minidump** | File di dump ridotto (~256 KB) generato durante un BSOD, contenente il bugcheck code, lo stack del thread in errore e i driver caricati. Ubicazione: `C:\Windows\Minidump\`. |
| **Procmon (Process Monitor)** | Tool Sysinternals che cattura in tempo reale tutte le operazioni di file system, registry e rete di ogni processo, con filtri avanzati. |
| **Autoruns** | Tool Sysinternals che mostra tutti i programmi configurati per l'avvio automatico (registry, task scheduler, servizi, driver, WMI). |
| **Procdump** | Tool Sysinternals per la generazione controllata di crash dump di processi, attivabile su exception, CPU threshold o hang. |
| **WinDbg** | Debugger Microsoft per l'analisi di crash dump (kernel e user mode). Il comando `!analyze -v` identifica automaticamente la causa probabile di un BSOD. |
| **LSDOU** | Local → Site → Domain → OU. Ordine di applicazione delle Group Policy, dove l'OU più specifica prevale (last writer wins). |
| **SFC (System File Checker)** | Utility che verifica e ripristina i file di sistema protetti da Windows Resource Protection. Comando: `sfc /scannow`. |
| **DISM** | Deployment Image Servicing and Management. Tool per la manutenzione delle immagini Windows, usato per riparare il component store (`DISM /RestoreHealth`). |

---

*Fine del Modulo 19 — Troubleshooting Windows*
