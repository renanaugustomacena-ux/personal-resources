# Windows Registry — Guida Completa

> **Modulo 04** · **Aggiornamento:** 2026-05-23

| Campo | Valore |
|---|---|
| **Corso** | Windows per ingegneri di sistema |
| **Fase** | Fondamenti del sistema operativo |
| **Modulo del corso** | 04 — Windows Registry |
| **Versioni di riferimento** | Windows 11 24H2, Windows Server 2025, PowerShell 7.x |
| **Livello** | Competent |
| **Prerequisiti** | Architettura Windows base (→ `16-profili-e-servizi.md`), PowerShell operativo (→ `02-powershell.md`), sicurezza Windows (→ `05-sicurezza-windows.md`) |
| **Obiettivi di apprendimento** | 1) Comprendere l'architettura gerarchica del Registry (5 root key, file hive, transaction log) · 2) Utilizzare regedit, reg.exe e PowerShell per leggere, modificare e monitorare il Registry · 3) Mappare le Group Policy alle chiavi di Registry corrispondenti e comprendere la precedenza · 4) Configurare ACL, auditing e virtualizzazione del Registry per la difesa in profondità · 5) Estrarre artefatti forensi dal Registry (UserAssist, RecentDocs, USB, BAM) |
| **Tempo stimato** | lettura 70 min · lab 90 min |
| **Ultimo aggiornamento** | 2026-05-23 |

## Idee guida
1. **HKLM, HKCU, HKCR, HKU, HKCC: 5 hives.**
2. **Registry editing: `regedit` UI, `reg.exe` CLI, `Set-ItemProperty` PS.**
3. **Backup before modify: `reg export`.**
4. **Group Policy modifies registry; preferred over manual edit.**
5. **Il Registry è un database gerarchico con file fisici su disco — la corruzione di un singolo hive può impedire il boot.**
6. **La sicurezza del Registry (ACL, auditing, virtualizzazione) è un pilastro della difesa in profondità di Windows.**
7. **La forensica del Registry rivela cronologia utente, dispositivi USB, programmi eseguiti e timestamp di ultima scrittura.**


## Indice

- [Panoramica](#panoramica)
- [Architettura Registry](#architettura-registry)
  - [Struttura gerarchica](#struttura-gerarchica)
  - [Tipi di valori — approfondimento](#tipi-di-valori--approfondimento)
  - [File hive su disco](#file-hive-su-disco)
  - [Transaction logs e dirty hives](#transaction-logs-e-dirty-hives)
  - [Internals dei transaction log — sequence number e dirty pages](#internals-dei-transaction-log--sequence-number-e-dirty-pages)
- [Hive in dettaglio](#hive-in-dettaglio)
  - [HKEY_LOCAL_MACHINE (HKLM)](#hkey_local_machine-hklm)
  - [HKEY_CURRENT_USER (HKCU)](#hkey_current_user-hkcu)
  - [HKEY_USERS (HKU)](#hkey_users-hku)
  - [HKEY_CLASSES_ROOT (HKCR)](#hkey_classes_root-hkcr)
  - [HKEY_CURRENT_CONFIG (HKCC)](#hkey_current_config-hkcc)
- [Strumenti di modifica](#strumenti-di-modifica)
  - [regedit — interfaccia grafica](#regedit--interfaccia-grafica)
  - [reg.exe — riga di comando](#regexe--riga-di-comando)
  - [PowerShell — gestione avanzata](#powershell--gestione-avanzata)
- [Modifiche Registry comuni](#modifiche-registry-comuni)
  - [Performance e comportamento](#performance-e-comportamento)
  - [Sicurezza — hardening](#sicurezza--hardening)
  - [Attack Surface Reduction e difesa IFEO via Registry](#attack-surface-reduction-e-difesa-ifeo-via-registry)
  - [Rete](#rete)
  - [Desktop e interfaccia utente](#desktop-e-interfaccia-utente)
  - [Windows Update](#windows-update)
  - [Startup e avvio](#startup-e-avvio)
- [Registry per GPO e Deploy](#registry-per-gpo-e-deploy)
  - [Come le GPO scrivono nel Registry](#come-le-gpo-scrivono-nel-registry)
  - [Administrative Templates — ADMX/ADML](#administrative-templates--admxadml)
  - [Tattoo effect](#tattoo-effect)
  - [Preference Items](#preference-items)
  - [File .reg per deploy](#file-reg-per-deploy)
  - [Gestione Registry via Intune e MDM](#gestione-registry-via-intune-e-mdm)
- [Sicurezza del Registry](#sicurezza-del-registry)
  - [Permessi (ACL)](#permessi-acl)
  - [Auditing del Registry](#auditing-del-registry)
  - [Monitoraggio avanzato con Sysmon e Windows Event Forwarding](#monitoraggio-avanzato-con-sysmon-e-windows-event-forwarding)
  - [Registry Virtualization (UAC)](#registry-virtualization-uac)
  - [WOW6432Node — deep dive sulla redirezione 32/64 bit](#wow6432node--deep-dive-sulla-redirezione-3264-bit)
- [Registry Remoto](#registry-remoto)
- [Backup e Ripristino](#backup-e-ripristino)
  - [Backup](#backup)
  - [Ripristino](#ripristino)
  - [RegBack — backup automatico](#regback--backup-automatico)
  - [Automazione backup Registry con rotazione](#automazione-backup-registry-con-rotazione)
  - [System Restore e Registry](#system-restore-e-registry)
- [Registry Defragmentation e Cleanup](#registry-defragmentation-e-cleanup)
- [Software Deployment via Registry](#software-deployment-via-registry)
- [Registry Forensics](#registry-forensics)
  - [Last write time](#last-write-time)
  - [Tracce attività utente](#tracce-attività-utente)
  - [Cronologia USB](#cronologia-usb)
  - [Esecuzione programmi](#esecuzione-programmi)
  - [Strumenti forensi](#strumenti-forensi)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [FAQ](#faq)
- [Tabella di riferimento — 50+ chiavi utili per sysadmin](#tabella-di-riferimento--50-chiavi-utili-per-sysadmin)

---

## Panoramica

Il Windows Registry è un database gerarchico centralizzato che memorizza impostazioni di configurazione per il sistema operativo, driver, servizi e applicazioni. È critico per il funzionamento di Windows: una modifica errata può rendere il sistema non avviabile. Ogni modifica va pianificata, documentata e preceduta da un backup.

Il Registry è apparso per la prima volta in Windows 3.1 con uno scopo limitato (associazioni file OLE). A partire da Windows 95 e Windows NT 3.5, è diventato il repository centrale di configurazione, sostituendo progressivamente i file `.INI`. Oggi il Registry di un'installazione Windows 10/11 contiene tipicamente centinaia di migliaia di chiavi e milioni di valori.

### Perché il Registry esiste

- **Centralizzazione:** un unico punto per tutte le configurazioni, anziché migliaia di file `.INI` sparsi.
- **Struttura gerarchica:** organizzazione logica per macchina, utente, classe, profilo hardware.
- **Sicurezza granulare:** ACL su ogni chiave, auditing, ereditarietà dei permessi.
- **Supporto multi-utente:** ogni utente ha il proprio hive (`NTUSER.DAT`), caricato al login.
- **Accesso API unificato:** le applicazioni usano le stesse API (`RegOpenKeyEx`, `RegSetValueEx`, ecc.) indipendentemente dall'hive.

### Limiti e rischi

- **Singolo punto di fallimento:** un hive corrotto può impedire il boot.
- **Complessità:** la dimensione e la profondità del Registry rendono difficile individuare impostazioni specifiche.
- **Registry bloat:** le applicazioni spesso non ripuliscono le proprie chiavi alla disinstallazione.
- **Nessun versioning nativo:** non esiste un meccanismo integrato di rollback per singoli valori (solo backup manuali o System Restore).

---

## Architettura Registry

### Struttura Gerarchica

```
Registry
├── HKEY_LOCAL_MACHINE (HKLM)     → Configurazione sistema (hardware, software, sicurezza)
│   ├── HARDWARE                   → Rilevamento hardware (volatile, generato al boot)
│   ├── SAM                        → Security Account Manager (protetto)
│   ├── SECURITY                   → Policy sicurezza (protetto)
│   ├── SOFTWARE                   → Software installato e impostazioni
│   │   ├── Microsoft\Windows\CurrentVersion
│   │   ├── Microsoft\Windows NT\CurrentVersion
│   │   └── Policies               → Impostazioni da GPO (Computer)
│   └── SYSTEM                     → Configurazione servizi, driver, boot
│       ├── CurrentControlSet       → Control set attivo
│       ├── ControlSet001           → Backup control set
│       └── Select                  → Quale control set è attivo
│
├── HKEY_CURRENT_USER (HKCU)       → Profilo utente corrente
│   ├── SOFTWARE                   → Impostazioni app per utente
│   │   └── Policies               → Impostazioni da GPO (User)
│   ├── Control Panel              → Impostazioni pannello controllo
│   └── Environment                → Variabili ambiente utente
│
├── HKEY_USERS (HKU)               → Tutti i profili utente caricati
│   ├── .DEFAULT                   → Profilo default
│   └── S-1-5-21-...              → Profili per SID utente
│
├── HKEY_CLASSES_ROOT (HKCR)        → Merge di HKLM\SOFTWARE\Classes + HKCU\SOFTWARE\Classes
│   └── Associazioni file, COM, CLSID
│
└── HKEY_CURRENT_CONFIG (HKCC)      → Profilo hardware corrente (link a HKLM\SYSTEM)
```

### Concetti fondamentali

- **Hive (alveare):** un raggruppamento logico di chiavi e valori, mappato a un file su disco. Ogni hive è un albero indipendente.
- **Chiave (Key):** equivalente a una cartella nel filesystem. Può contenere sotto-chiavi e valori. Ogni chiave ha un timestamp di ultima scrittura (last write time).
- **Valore (Value):** equivalente a un file. Ha un nome, un tipo e dei dati. Una chiave può contenere zero o più valori.
- **Valore predefinito (Default):** ogni chiave ha un valore senza nome, mostrato come `(Default)` in regedit. Spesso vuoto.
- **Volatile key:** chiave che esiste solo in memoria e non viene scritta su disco. Esempio: `HKLM\HARDWARE`.

### Tipi di Valori — approfondimento

| Tipo | Nome | Descrizione | Esempio |
|------|------|-------------|---------|
| REG_SZ | String | Stringa di testo null-terminated | `"C:\Program Files\App"` |
| REG_EXPAND_SZ | Expandable String | Stringa con variabili d'ambiente, espansa a runtime | `"%USERPROFILE%\Desktop"` |
| REG_MULTI_SZ | Multi-String | Array di stringhe, separate da null, terminato da doppio null | `"val1\0val2\0val3\0\0"` |
| REG_DWORD | DWORD (32-bit) | Numero intero 32 bit, little-endian | `0x00000001` (1) |
| REG_QWORD | QWORD (64-bit) | Numero intero 64 bit, little-endian | `0x0000000100000000` |
| REG_BINARY | Binary | Dati binari raw, qualsiasi lunghezza | `01 00 14 80...` |
| REG_NONE | None | Nessun tipo definito | — |
| REG_LINK | Symbolic Link | Link simbolico a un'altra chiave (usato internamente) | percorso a un'altra chiave |
| REG_RESOURCE_LIST | Resource List | Lista risorse hardware (usato da HARDWARE hive) | dati strutturati |
| REG_FULL_RESOURCE_DESCRIPTOR | Full Resource Descriptor | Descrittore completo di risorsa hardware | dati strutturati |
| REG_RESOURCE_REQUIREMENTS_LIST | Resource Requirements List | Requisiti risorse hardware | dati strutturati |

#### REG_SZ vs REG_EXPAND_SZ

La differenza è critica: `REG_SZ` viene letto letteralmente, `REG_EXPAND_SZ` espande le variabili d'ambiente al momento della lettura.

```
REG_SZ:        "%SystemRoot%\system32"  → letto come "%SystemRoot%\system32" (stringa letterale)
REG_EXPAND_SZ: "%SystemRoot%\system32"  → letto come "C:\Windows\system32" (espansa)
```

Se si scrive un percorso con variabili d'ambiente e si usa `REG_SZ` anziché `REG_EXPAND_SZ`, la variabile non verrà espansa e il percorso non funzionerà.

#### REG_MULTI_SZ — struttura

```
Byte:  76 00 61 00 6C 00 31 00 00 00 76 00 61 00 6C 00 32 00 00 00 00 00
       |-- "val1" (UTF-16LE) --| NULL |-- "val2" (UTF-16LE) --| NULL NULL
```

Ogni stringa è in UTF-16LE, terminata da un null (due byte `00 00`). L'intera sequenza è terminata da un doppio null.

#### REG_DWORD e REG_QWORD — endianness

Entrambi sono memorizzati in little-endian. Un REG_DWORD con valore `0x12345678` è scritto su disco come `78 56 34 12`. Questo è trasparente quando si usano le API Windows, ma rilevante nell'analisi forense di hive raw.

#### REG_BINARY — uso comune

Usato per dati strutturati proprietari. Esempi:
- Security descriptors (permessi ACL)
- Configurazioni di stampanti
- Chiavi di licenza codificate
- Dati di configurazione hardware

L'interpretazione richiede la conoscenza del formato specifico usato dall'applicazione.

### File Hive su Disco

```
C:\Windows\System32\config\
├── SAM            → HKLM\SAM
├── SECURITY       → HKLM\SECURITY
├── SOFTWARE       → HKLM\SOFTWARE       (tipicamente 50-200 MB)
├── SYSTEM         → HKLM\SYSTEM         (tipicamente 10-40 MB)
├── DEFAULT        → HKU\.DEFAULT
├── DRIVERS        → HKLM\SYSTEM mappatura driver (in alcune versioni)
├── BBI            → Branch Prediction Buffer Information
└── NTUSER.DAT     → HKCU (nel profilo utente: C:\Users\<user>\NTUSER.DAT)

C:\Users\<user>\
├── NTUSER.DAT           → HKCU dell'utente (caricato al login)
├── ntuser.dat.LOG1      → Transaction log 1
├── ntuser.dat.LOG2      → Transaction log 2
└── AppData\Local\Microsoft\Windows\
    └── UsrClass.dat     → HKCU\SOFTWARE\Classes (componenti COM per utente)
```

Ogni hive ha file associati:
- `<HIVE>` — file principale
- `<HIVE>.LOG1`, `<HIVE>.LOG2` — transaction logs (per crash recovery)
- `<HIVE>.blf` — base log file (per le transazioni)
- `<HIVE>.regtrans-ms` — transaction registrations

### Transaction Logs e Dirty Hives

Il Configuration Manager di Windows implementa un sistema transazionale per proteggere gli hive dalla corruzione in caso di crash o power failure.

**Meccanismo di write-ahead logging:**

1. Le modifiche vengono prima scritte nel transaction log (`.LOG1` o `.LOG2`).
2. Un flag "dirty" viene impostato nell'header dell'hive.
3. Le modifiche vengono applicate all'hive principale.
4. Il flag "dirty" viene rimosso.

Se il sistema crolla tra i passi 2 e 4, al successivo boot il Configuration Manager rileva il flag "dirty" e ripristina l'hive usando il transaction log. Questo meccanismo garantisce la consistenza dell'hive.

**Dual-logging (Windows 8.1+):** Windows alterna tra `.LOG1` e `.LOG2`. Se un log è corrotto, l'altro è disponibile come fallback.

```powershell
# Verificare lo stato degli hive (requires admin)
# Se un hive è "dirty", i log non sono stati processati completamente
Get-ChildItem "C:\Windows\System32\config" -File |
    Where-Object { $_.Extension -notin '.LOG1','.LOG2','.blf','.regtrans-ms' } |
    Select-Object Name, Length, LastWriteTime
```

### Internals dei transaction log — sequence number e dirty pages

Il Configuration Manager del kernel gestisce la persistenza degli hive tramite un meccanismo di **write-ahead logging** derivato dalle tecniche dei database transazionali. Comprendere gli internals è essenziale sia per la forensics sia per diagnosticare hive corrotti.

**Struttura del file LOG:**

Ogni file `.LOG1` / `.LOG2` inizia con una firma `HvLE` (Hive Log Entry) seguita da un header che contiene:

| Campo | Dimensione | Funzione |
|-------|-----------|----------|
| Signature | 4 byte | `HvLE` — identifica il log come valido |
| Sequence number | 4 byte | Contatore monotonicamente crescente per ordinare le transazioni |
| Hive flags | 4 byte | Stato dell'hive (dirty, in-recovery, frozen) |
| Dirty pages vector | variabile | Bitmap che indica quali pagine da 4 KB dell'hive sono state modificate |
| Page data | variabile | Contenuto aggiornato delle pagine sporche |

**Ciclo di vita di una transazione:**

1. **Modifica in memoria**: il Configuration Manager aggiorna la cella dell'hive nel pool paginato del kernel.
2. **Marcatura dirty**: la pagina da 4 KB contenente la cella viene marcata nel dirty pages vector.
3. **Flush al log**: durante il lazy flush (ogni ~5 secondi di default) o al checkpoint esplicito, le pagine dirty vengono scritte nel file LOG attivo con un nuovo sequence number.
4. **Commit nell'hive primario**: solo dopo che il log è stato scritto con successo, il Configuration Manager applica le modifiche al file hive principale.
5. **Reset del dirty vector**: il vettore viene azzerato e il sequence number nell'header dell'hive primario viene aggiornato per corrispondere al log.

**Dual-logging e crash recovery:**

Il sistema alterna tra `.LOG1` e `.LOG2` ad ogni ciclo di flush. Se il sistema si arresta durante la scrittura nel file hive primario:

- Al riavvio, il kernel confronta il sequence number nell'header dell'hive con quelli nei due file LOG.
- Se un LOG ha un sequence number superiore a quello dell'hive → contiene modifiche non committate.
- Il Configuration Manager applica le dirty pages dal LOG all'hive primario, completando la transazione interrotta (recovery automatico).
- Se entrambi i LOG sono corrotti, Windows tenta il rollback all'ultimo stato consistente.

```powershell
# Analizzare sequence number di un hive offline con PowerShell
# Richiede il modulo di parsing binario — esempio con byte raw
$hivePath = "C:\Windows\System32\config\SOFTWARE"
$bytes = [System.IO.File]::ReadAllBytes($hivePath)
# Sequence number primario: offset 0x04 (4 byte, little-endian)
$seq1 = [BitConverter]::ToUInt32($bytes, 0x04)
# Sequence number secondario: offset 0x08
$seq2 = [BitConverter]::ToUInt32($bytes, 0x08)
Write-Host "Primary seq: $seq1 — Secondary seq: $seq2"
# Se $seq1 ≠ $seq2, l'hive è dirty (transazione non completata)
```

**Implicazioni forensi:**

- Un hive con sequence number primario ≠ secondario era in stato **dirty** al momento dell'acquisizione — le modifiche più recenti potrebbero trovarsi solo nei file LOG.
- I transaction log non riconciliati rappresentano artefatti forensi preziosi: contengono le ultime modifiche effettuate prima di un crash o arresto improvviso.
- Strumenti forensi come **Registry Explorer** (Eric Zimmerman) possono ricostruire l'hive applicando i dirty pages dai LOG, mostrando lo stato completo che Windows avrebbe ripristinato.
- La dimensione del dirty vector indica la quantità di modifiche pendenti: un vettore molto grande suggerisce un'attività intensa prima dell'arresto.

---

## Hive in Dettaglio

### HKEY_LOCAL_MACHINE (HKLM)

L'hive HKLM contiene la configurazione dell'intera macchina, indipendente dall'utente. È il più grande e importante hive del Registry.

#### HKLM\SAM

- **Contiene:** il database Security Account Manager — hash delle password locali, membership dei gruppi, policy degli account.
- **File su disco:** `C:\Windows\System32\config\SAM`
- **Accesso:** protetto. Solo `SYSTEM` ha accesso completo. Nemmeno Administrators può leggere direttamente. Per accedere: usare `PsExec -s regedit` oppure montare l'hive offline.
- **Struttura interna:**
  ```
  SAM\SAM\Domains\Account\Users\
  ├── 000001F4     → Administrator (RID 500)
  ├── 000001F5     → Guest (RID 501)
  └── 000003E8     → Primo utente creato (RID 1000)
  ```
- **Non modificare direttamente.** Usare: `net user`, `lusrmgr.msc`, PowerShell `Get-LocalUser`, o Active Directory per account di dominio.

#### HKLM\SECURITY

- **Contiene:** policy di sicurezza locali (LSA Policy), cached logon credentials, segreti LSA (Service account passwords, VPN passwords, ecc.).
- **File su disco:** `C:\Windows\System32\config\SECURITY`
- **Accesso:** protetto come SAM. Solo `SYSTEM`.
- **Struttura interna:**
  ```
  SECURITY\Policy\
  ├── PolAdtEv     → Audit policy
  ├── PolPrDmN     → Primary domain name
  ├── PolPrDmS     → Primary domain SID
  ├── PolAcDmN     → Account domain name
  └── Secrets\     → LSA secrets (password servizi, ecc.)
  ```
- **Rilevanza forense:** contiene le cached domain credentials (`SECURITY\Cache`), tipicamente 10-25 set di credenziali cached.

#### HKLM\SOFTWARE

- **Contiene:** configurazione di tutto il software installato a livello macchina, impostazioni Windows, policy GPO computer.
- **File su disco:** `C:\Windows\System32\config\SOFTWARE` (il file hive più grande, tipicamente 50-200 MB).
- **Sotto-chiavi principali:**
  ```
  SOFTWARE\
  ├── Classes\                    → Associazioni file e registrazioni COM (sistema)
  ├── Microsoft\
  │   ├── Windows\CurrentVersion\
  │   │   ├── Run\               → Programmi auto-start per tutti gli utenti
  │   │   ├── Uninstall\         → Lista programmi installati
  │   │   ├── Explorer\          → Configurazione Explorer
  │   │   ├── Policies\          → Policy system-wide
  │   │   └── App Paths\         → Percorsi applicazioni
  │   ├── Windows NT\CurrentVersion\
  │   │   ├── ProfileList\       → Profili utente (SID → path profilo)
  │   │   ├── Winlogon\          → Configurazione logon
  │   │   ├── NetworkList\       → Reti connesse storiche
  │   │   └── Schedule\          → Task schedulati
  │   └── Windows Defender\      → Configurazione antivirus
  ├── Policies\                  → GPO Computer Configuration
  ├── WOW6432Node\               → Vista 32-bit del registro su Windows 64-bit
  └── <Vendor>\                  → Chiavi specifiche per vendor terzi
  ```

#### HKLM\SYSTEM

- **Contiene:** configurazione di servizi, driver, boot, profili hardware.
- **File su disco:** `C:\Windows\System32\config\SYSTEM`
- **Sotto-chiavi principali:**
  ```
  SYSTEM\
  ├── CurrentControlSet\         → Alias al ControlSet attivo
  │   ├── Control\               → Configurazione sistema (ComputerName, TimeZone, etc.)
  │   │   ├── ComputerName\
  │   │   ├── FileSystem\
  │   │   ├── Lsa\               → Local Security Authority config
  │   │   ├── Session Manager\   → Boot configuration
  │   │   ├── Terminal Server\
  │   │   └── TimeZoneInformation\
  │   ├── Enum\                  → Dispositivi hardware enumerati (PnP)
  │   ├── Hardware Profiles\     → Profili hardware
  │   └── Services\              → Tutti i servizi e driver
  │       ├── Tcpip\Parameters\  → Configurazione TCP/IP
  │       ├── LanmanServer\      → Configurazione SMB server
  │       └── <ServiceName>\     → Start type, ImagePath, Dependencies
  ├── ControlSet001\             → Control set 1
  ├── ControlSet002\             → Control set 2 (backup)
  ├── Select\                    → Quale control set è Current, Default, Failed, LastKnownGood
  ├── Setup\                     → Informazioni setup Windows
  └── MountedDevices\            → Lettere di unità e GUID volumi montati
  ```

**ControlSet e boot process:** la chiave `SYSTEM\Select` contiene quattro valori DWORD:
- `Current` — il control set attualmente in uso (es. `1`)
- `Default` — il control set da usare al prossimo boot (es. `1`)
- `Failed` — il control set che ha fallito l'ultimo boot (es. `0` = nessuno)
- `LastKnownGood` — l'ultimo control set con cui il boot ha avuto successo (es. `2`)

`CurrentControlSet` è un link simbolico (`REG_LINK`) al `ControlSet00X` indicato da `Select\Current`.

#### HKLM\HARDWARE

- **Volatile:** generato interamente al boot, non ha file su disco.
- **Contiene:** hardware detection, ACPI tables, device map, resource allocation.
- **Non modificabile:** viene rigenerato a ogni avvio.

### HKEY_CURRENT_USER (HKCU)

- **File su disco:** `C:\Users\<username>\NTUSER.DAT`
- **Rappresenta:** il profilo dell'utente attualmente loggato. È un alias (link) all'appropriato sotto-hive di `HKU\<SID>`.
- **Sotto-chiavi principali:**
  ```
  HKCU\
  ├── SOFTWARE\
  │   ├── Microsoft\
  │   │   ├── Windows\CurrentVersion\
  │   │   │   ├── Run\                → Auto-start per questo utente
  │   │   │   ├── Explorer\
  │   │   │   │   ├── RecentDocs\     → File recenti
  │   │   │   │   ├── ComDlg32\       → Dialog box MRU (Most Recently Used)
  │   │   │   │   ├── UserAssist\     → Programmi eseguiti (ROT13 encoded)
  │   │   │   │   ├── RunMRU\         → Comandi dalla finestra Esegui
  │   │   │   │   └── TypedPaths\     → Percorsi digitati in Explorer
  │   │   │   ├── Internet Settings\  → Configurazione proxy, TLS
  │   │   │   └── Policies\           → GPO User Configuration
  │   │   ├── Office\                 → Impostazioni Microsoft Office
  │   │   └── Terminal Server Client\ → Connessioni RDP salvate
  │   └── <Vendor>\                   → Impostazioni per vendor terzi
  ├── Control Panel\
  │   ├── Desktop\                    → Wallpaper, screensaver, impostazioni DPI
  │   ├── International\              → Locale, formati data/ora
  │   └── Mouse\                      → Sensibilità mouse
  ├── Environment\                    → Variabili d'ambiente per l'utente
  ├── Console\                        → Impostazioni console cmd/PowerShell
  ├── Keyboard Layout\                → Layout tastiera
  ├── Network\                        → Drive di rete mappati
  └── Printers\                       → Stampanti per l'utente
  ```

### HKEY_USERS (HKU)

- **Contiene:** tutti i profili utente attualmente caricati in memoria.
- **Sotto-chiavi:**
  ```
  HKU\
  ├── .DEFAULT                        → Profilo default (usato da LocalSystem e schermata di login)
  ├── S-1-5-18                        → LocalSystem
  ├── S-1-5-19                        → LocalService
  ├── S-1-5-20                        → NetworkService
  ├── S-1-5-21-<domain>-<RID>         → Utente di dominio o locale
  └── S-1-5-21-<domain>-<RID>_Classes → Classes dell'utente (UsrClass.dat)
  ```
- I profili degli utenti non loggati non sono caricati in HKU. Per accedervi, caricare manualmente il loro `NTUSER.DAT`:
  ```powershell
  reg load HKU\TempUser "C:\Users\mario.rossi\NTUSER.DAT"
  # Operazioni...
  reg unload HKU\TempUser
  ```

### HKEY_CLASSES_ROOT (HKCR)

- **Vista merged:** unione di `HKLM\SOFTWARE\Classes` e `HKCU\SOFTWARE\Classes`.
- **Priorità:** le impostazioni in `HKCU\SOFTWARE\Classes` (per utente) hanno precedenza su quelle in `HKLM\SOFTWARE\Classes` (per macchina).
- **Contiene:**
  - Associazioni file (`.txt`, `.docx`, `.pdf`, ecc.)
  - Registrazioni COM/DCOM (`CLSID\{GUID}`)
  - ProgIDs (`Word.Document.12`)
  - Protocolli URL (`http`, `mailto`, `ms-settings`)
  - Interfacce COM (`Interface\{GUID}`)
  - TypeLibs (`TypeLib\{GUID}`)

```
HKCR\
├── .txt                           → punta a "txtfile" (ProgID)
├── .docx                          → punta a "Word.Document.12"
├── txtfile\
│   ├── DefaultIcon                → icona predefinita
│   └── shell\
│       ├── open\command           → comando per aprire
│       └── edit\command           → comando per modificare
├── CLSID\
│   └── {GUID}\
│       ├── InprocServer32         → DLL per COM in-process
│       ├── LocalServer32          → EXE per COM out-of-process
│       └── ProgID                 → ProgID associato
└── Installer\Products\            → Prodotti MSI registrati
```

### HKEY_CURRENT_CONFIG (HKCC)

- **Vista:** link simbolico a `HKLM\SYSTEM\CurrentControlSet\Hardware Profiles\Current`.
- **Contiene:** configurazione minima del profilo hardware corrente (display, stampanti).
- **Uso pratico:** molto limitato. Storicamente usato per i profili hardware docking/undocking dei laptop. In Windows moderno, quasi inutilizzato.

---

## Strumenti di Modifica

### regedit — Interfaccia Grafica

`regedit.exe` è l'editor grafico del Registry incluso in ogni installazione Windows.

**Avvio:**

```
Win+R → regedit → Invio
```

Richiede privilegi di amministratore per modificare chiavi in HKLM.

**Funzionalità principali:**

| Operazione | Come fare |
|------------|-----------|
| Navigare | Espandere l'albero a sinistra, oppure barra indirizzi (Win10+): `Computer\HKEY_LOCAL_MACHINE\SOFTWARE` |
| Cercare | `Ctrl+F` — cerca in chiavi, valori, dati. `F3` per il risultato successivo |
| Creare chiave | Tasto destro → Nuovo → Chiave |
| Creare valore | Tasto destro nel pannello destro → Nuovo → tipo valore |
| Modificare valore | Doppio clic sul valore |
| Rinominare | `F2` o tasto destro → Rinomina |
| Eliminare | `Canc` o tasto destro → Elimina |
| Esportare | Tasto destro sulla chiave → Esporta (formato `.reg`) |
| Importare | File → Importa, oppure doppio clic su un file `.reg` |
| Preferiti | Preferiti → Aggiungi ai Preferiti (per chiavi usate spesso) |
| Permessi | Tasto destro sulla chiave → Autorizzazioni |
| Caricare hive | File → Carica hive (per montare hive offline) |
| Scaricare hive | File → Scarica hive (per smontare hive caricato) |

**Limitazioni di regedit:**

- Ricerca lenta (sequenziale, non indicizzata).
- Non supporta operazioni in batch.
- Non supporta espressioni regolari nella ricerca.
- Non mostra il timestamp di ultima scrittura delle chiavi.
- Non supporta connessioni remote a registri multipli simultanei (solo uno alla volta).

**Connessione a registry remoto:**

File → Connetti a Registro di rete → inserire nome computer. Richiede che il servizio Remote Registry sia attivo sulla macchina remota.

### reg.exe — Riga di Comando

`reg.exe` è lo strumento CLI nativo per operazioni sul Registry. Supporta scripting e batch operations.

**Sintassi generale:**

```
reg <operazione> <percorso_chiave> [/v <valore>] [/t <tipo>] [/d <dati>] [/f]
```

**Operazioni disponibili:**

| Comando | Descrizione |
|---------|-------------|
| `reg query` | Leggere chiavi e valori |
| `reg add` | Creare/modificare chiavi e valori |
| `reg delete` | Eliminare chiavi e valori |
| `reg copy` | Copiare chiavi tra posizioni |
| `reg save` | Salvare hive in formato binario (.hiv) |
| `reg restore` | Ripristinare hive da file binario |
| `reg load` | Caricare hive offline |
| `reg unload` | Scaricare hive caricato |
| `reg compare` | Confrontare due chiavi o hive |
| `reg export` | Esportare in formato .reg (testo) |
| `reg import` | Importare da file .reg |
| `reg flags` | Gestire flag sulle chiavi (solo 64-bit) |

**Esempi pratici:**

```cmd
:: Leggere un valore specifico
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v ProductName

:: Leggere tutti i valori di una chiave
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion"

:: Leggere ricorsivamente (tutte le sotto-chiavi)
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /s

:: Creare/Modificare un valore stringa
reg add "HKLM\SOFTWARE\MyCompany" /v AppVersion /t REG_SZ /d "2.0" /f

:: Creare un DWORD
reg add "HKLM\SOFTWARE\MyCompany" /v Enabled /t REG_DWORD /d 1 /f

:: Creare un REG_EXPAND_SZ
reg add "HKLM\SOFTWARE\MyCompany" /v LogPath /t REG_EXPAND_SZ /d "%%TEMP%%\app.log" /f

:: Creare un REG_MULTI_SZ
reg add "HKLM\SOFTWARE\MyCompany" /v Features /t REG_MULTI_SZ /d "feat1\0feat2\0feat3" /f

:: Eliminare un valore
reg delete "HKLM\SOFTWARE\MyCompany" /v AppVersion /f

:: Eliminare un'intera chiave con sotto-chiavi
reg delete "HKLM\SOFTWARE\MyCompany" /f

:: Esportare in formato .reg
reg export "HKLM\SOFTWARE\MyCompany" C:\Backup\mycompany.reg

:: Importare da file .reg
reg import C:\Backup\mycompany.reg

:: Salvare un hive in formato binario
reg save HKLM\SYSTEM C:\Backup\system.hiv

:: Ripristinare un hive
reg restore HKLM\SYSTEM C:\Backup\system.hiv

:: Caricare un hive offline
reg load HKLM\OfflineSystem C:\Mounted\Windows\System32\config\SYSTEM

:: Scaricare un hive caricato
reg unload HKLM\OfflineSystem

:: Confrontare due chiavi
reg compare "HKLM\SOFTWARE\MyCompany" "HKLM\SOFTWARE\MyCompanyBackup" /s

:: Copiare una chiave
reg copy "HKLM\SOFTWARE\MyCompany" "HKLM\SOFTWARE\MyCompanyBackup" /s /f

:: Query su registry remoto
reg query "\\SERVER01\HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v ProductName
```

**Flag importanti:**

| Flag | Significato |
|------|-------------|
| `/f` | Force — non chiedere conferma |
| `/s` | Ricorsivo (sotto-chiavi) |
| `/v` | Nome del valore |
| `/ve` | Valore predefinito (senza nome) |
| `/t` | Tipo (REG_SZ, REG_DWORD, ecc.) |
| `/d` | Dati del valore |
| `/reg:32` | Forza vista 32-bit del registro |
| `/reg:64` | Forza vista 64-bit del registro |

### PowerShell — Gestione Avanzata

PowerShell tratta il Registry come un filesystem tramite PSDrive.

#### PSDrive Registry

```powershell
# PSDrive disponibili per il Registry
Get-PSDrive -PSProvider Registry
# HKLM → HKEY_LOCAL_MACHINE
# HKCU → HKEY_CURRENT_USER

# Per accedere ad altri hive, creare PSDrive personalizzati
New-PSDrive -Name HKU -PSProvider Registry -Root HKEY_USERS
New-PSDrive -Name HKCR -PSProvider Registry -Root HKEY_CLASSES_ROOT
New-PSDrive -Name HKCC -PSProvider Registry -Root HKEY_CURRENT_CONFIG
```

#### Navigazione e lettura

```powershell
# Il Registry è montato come PSDrive
Get-PSDrive -PSProvider Registry
# HKLM → HKEY_LOCAL_MACHINE
# HKCU → HKEY_CURRENT_USER

# Navigare
Set-Location HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion
Get-ChildItem                    # Sotto-chiavi
Get-ItemProperty .               # Valori nella chiave corrente

# Leggere un valore specifico
Get-ItemPropertyValue -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion" `
    -Name ProductName
# Output: Windows Server 2022 Datacenter

# Elencare tutti i valori di una chiave
Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion" |
    Select-Object ProductName, CurrentBuild, EditionID, InstallDate

# Cercare nel registry (ricorsivo)
Get-ChildItem -Path HKLM:\SOFTWARE -Recurse -ErrorAction SilentlyContinue |
    Where-Object { $_.GetValue("DisplayName") -like "*Office*" }

# Cercare un valore specifico in tutte le sotto-chiavi
Get-ChildItem -Path HKLM:\SOFTWARE\Microsoft -Recurse -ErrorAction SilentlyContinue |
    ForEach-Object {
        $key = $_
        $key.GetValueNames() | Where-Object { $_ -eq "DisplayName" } |
            ForEach-Object {
                [PSCustomObject]@{
                    Path  = $key.PSPath
                    Name  = $_
                    Value = $key.GetValue($_)
                }
            }
    }
```

#### Creazione e modifica

```powershell
# Creare chiave
New-Item -Path "HKLM:\SOFTWARE\MyCompany" -Force

# Creare/modificare valore stringa
New-ItemProperty -Path "HKLM:\SOFTWARE\MyCompany" -Name "AppVersion" `
    -Value "1.0" -PropertyType String
Set-ItemProperty -Path "HKLM:\SOFTWARE\MyCompany" -Name "AppVersion" -Value "2.0"

# Creare DWORD
New-ItemProperty -Path "HKLM:\SOFTWARE\MyCompany" -Name "Enabled" `
    -Value 1 -PropertyType DWord

# Creare QWORD
New-ItemProperty -Path "HKLM:\SOFTWARE\MyCompany" -Name "MaxSize" `
    -Value 4294967296 -PropertyType QWord

# Creare REG_EXPAND_SZ
New-ItemProperty -Path "HKLM:\SOFTWARE\MyCompany" -Name "LogDir" `
    -Value "%TEMP%\MyApp" -PropertyType ExpandString

# Creare REG_MULTI_SZ
New-ItemProperty -Path "HKLM:\SOFTWARE\MyCompany" -Name "Servers" `
    -Value @("srv01.contoso.com","srv02.contoso.com","srv03.contoso.com") `
    -PropertyType MultiString

# Creare REG_BINARY
$bytes = [byte[]](0x01, 0x02, 0x03, 0x04)
New-ItemProperty -Path "HKLM:\SOFTWARE\MyCompany" -Name "BinaryData" `
    -Value $bytes -PropertyType Binary

# Rimuovere valore
Remove-ItemProperty -Path "HKLM:\SOFTWARE\MyCompany" -Name "AppVersion"

# Rimuovere chiave (e tutti i sotto-valori)
Remove-Item -Path "HKLM:\SOFTWARE\MyCompany" -Recurse -Force

# Verificare esistenza chiave
Test-Path "HKLM:\SOFTWARE\MyCompany"

# Verificare esistenza valore
(Get-ItemProperty "HKLM:\SOFTWARE\MyCompany" -Name "Enabled" -ErrorAction SilentlyContinue).Enabled

# Rinominare un valore
Rename-ItemProperty -Path "HKLM:\SOFTWARE\MyCompany" -Name "OldName" -NewName "NewName"

# Copiare un'intera chiave
Copy-Item -Path "HKLM:\SOFTWARE\MyCompany" -Destination "HKLM:\SOFTWARE\MyCompanyBackup" -Recurse
```

#### Operazioni avanzate con .NET

```powershell
# Accesso diretto tramite API .NET per operazioni non supportate dai cmdlet

# Leggere il timestamp di ultima scrittura (last write time) di una chiave
$key = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey("SOFTWARE\Microsoft\Windows\CurrentVersion")
# Il timestamp è disponibile solo tramite P/Invoke o strumenti esterni

# Leggere un valore REG_EXPAND_SZ senza espansione
$key = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey("SYSTEM\CurrentControlSet\Control\Session Manager\Environment")
$rawValue = $key.GetValue("Path", $null, [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)

# Enumerare le sotto-chiavi con conteggio
$root = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey("SOFTWARE")
$root.GetSubKeyNames() | ForEach-Object {
    $subkey = $root.OpenSubKey($_)
    [PSCustomObject]@{
        Name         = $_
        SubKeyCount  = $subkey.SubKeyCount
        ValueCount   = $subkey.ValueCount
    }
} | Sort-Object SubKeyCount -Descending | Select-Object -First 20
```

#### Operazioni batch con script

```powershell
# Applicare un set di modifiche Registry da un CSV
# File CSV formato: Path,Name,Type,Value
$changes = Import-Csv "C:\Deploy\registry-changes.csv"
foreach ($change in $changes) {
    $params = @{
        Path         = $change.Path
        Name         = $change.Name
        Value        = $change.Value
        PropertyType = $change.Type
        Force        = $true
    }
    # Assicurarsi che la chiave esista
    if (-not (Test-Path $change.Path)) {
        New-Item -Path $change.Path -Force | Out-Null
    }
    New-ItemProperty @params -ErrorAction SilentlyContinue
    if ($?) {
        Write-Host "[OK] $($change.Path)\$($change.Name)" -ForegroundColor Green
    } else {
        Set-ItemProperty -Path $change.Path -Name $change.Name -Value $change.Value
        Write-Host "[UPD] $($change.Path)\$($change.Name)" -ForegroundColor Yellow
    }
}
```

---

## Modifiche Registry Comuni

### Performance e Comportamento

```powershell
# Disabilitare Last Access Time su NTFS (performance)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
    -Name "NtfsDisableLastAccessUpdate" -Value 0x80000003

# Aumentare dimensione cache DNS client
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Dnscache\Parameters" `
    -Name "CacheHashTableBucketSize" -Value 1 -Type DWord
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Dnscache\Parameters" `
    -Name "CacheHashTableSize" -Value 384 -Type DWord

# Disabilitare Cortana
New-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Windows Search" `
    -Name "AllowCortana" -Value 0 -PropertyType DWord -Force

# Disabilitare telemetria
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection" `
    -Name "AllowTelemetry" -Value 0

# Configurare shutdown timeout (millisecondi)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control" `
    -Name "WaitToKillServiceTimeout" -Value "5000"

# Disabilitare animazioni menu (più reattivo)
Set-ItemProperty -Path "HKCU:\Control Panel\Desktop" -Name "MenuShowDelay" -Value "0"

# Ottimizzare pagefile — disabilitare clearing al shutdown
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management" `
    -Name "ClearPageFileAtShutdown" -Value 0

# Aumentare la priorità dei processi in foreground
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\PriorityControl" `
    -Name "Win32PrioritySeparation" -Value 38

# Disabilitare Prefetch/Superfetch (su SSD, dove non serve)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters" `
    -Name "EnablePrefetcher" -Value 0
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters" `
    -Name "EnableSuperfetch" -Value 0

# Ridurre timeout per applicazioni non responsive (millisecondi)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control" `
    -Name "HungAppTimeout" -Value "2000"
Set-ItemProperty -Path "HKCU:\Control Panel\Desktop" -Name "HungAppTimeout" -Value "2000"

# Disabilitare error reporting (meno overhead)
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\Windows Error Reporting" `
    -Name "Disabled" -Value 1

# Ottimizzare IRPStackSize per reti complesse
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" `
    -Name "IRPStackSize" -Value 20 -Type DWord
```

### Sicurezza — Hardening

```powershell
# Disabilitare SMBv1
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" `
    -Name "SMB1" -Value 0 -Type DWord

# Disabilitare LLMNR (Link-Local Multicast Name Resolution)
New-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" `
    -Name "EnableMulticast" -Value 0 -PropertyType DWord -Force

# Disabilitare NetBIOS over TCP/IP (per adattatore)
# Valore 2 = Disabilitato
$adapters = Get-ChildItem "HKLM:\SYSTEM\CurrentControlSet\Services\NetBT\Parameters\Interfaces"
foreach ($adapter in $adapters) {
    Set-ItemProperty -Path $adapter.PSPath -Name "NetbiosOptions" -Value 2
}

# Disabilitare WPAD (Web Proxy Auto-Discovery)
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\WinHttpAutoProxySvc" `
    -Name "Start" -Value 4 -PropertyType DWord -Force

# Abilitare audit command line in Process Creation events
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\Audit" `
    -Name "ProcessCreationIncludeCmdLine_Enabled" -Value 1

# NLA: richiedere autenticazione prima del desktop remoto
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" `
    -Name "UserAuthentication" -Value 1

# ---- HARDENING AVANZATO ----

# Disabilitare LM Hash storage (impedisce hash deboli)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "NoLMHash" -Value 1

# Forzare NTLMv2 (disabilitare LM e NTLMv1)
# Valore 5 = Invia solo NTLMv2, rifiuta LM e NTLM
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "LmCompatibilityLevel" -Value 5

# Limitare cached credentials (ridurre da default 10-25 a 1 o 0)
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" `
    -Name "CachedLogonsCount" -Value "1"

# Disabilitare WDigest (impedisce password in chiaro in memoria)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\WDigest" `
    -Name "UseLogonCredential" -Value 0

# Abilitare LSA Protection (RunAsPPL)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "RunAsPPL" -Value 1

# Disabilitare esecuzione di autorun su tutti i drive
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer" `
    -Name "NoDriveTypeAutoRun" -Value 0xFF

# Disabilitare Remote Assistance
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Remote Assistance" `
    -Name "fAllowToGetHelp" -Value 0

# Disabilitare WinRM non criptato
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WinRM\Client" `
    -Name "AllowUnencryptedTraffic" -Value 0

# Abilitare Credential Guard (richiede Secure Boot + UEFI)
# Attenzione: non abilitare su VM senza nested virtualization
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard" `
    -Name "EnableVirtualizationBasedSecurity" -Value 1
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "LsaCfgFlags" -Value 1

# Disabilitare Windows Script Host (blocca .vbs, .js, .wsf)
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows Script Host\Settings" `
    -Name "Enabled" -Value 0

# Impedire l'uso di PowerShell v2 (engine obsoleto senza logging)
# Rimuovere la feature: Disable-WindowsOptionalFeature -Online -FeatureName MicrosoftWindowsPowerShellV2
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell" `
    -Name "EnableScripts" -Value 1
# Preferire la rimozione della feature piuttosto che il registry per PowerShell v2

# Forzare SMB signing
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" `
    -Name "RequireSecuritySignature" -Value 1
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" `
    -Name "RequireSecuritySignature" -Value 1
```

### Attack Surface Reduction e difesa IFEO via Registry

Le regole ASR (Attack Surface Reduction) di Microsoft Defender sono configurabili direttamente via Registry, consentendo hardening granulare anche senza GPO o Intune. Ogni regola è identificata da un GUID e può operare in modalità **Block** (1), **Audit** (2), **Warn** (6) o **Disabled** (0).

**Posizione nel Registry:**

```
HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Policy Manager\ASRRules
HKLM\SOFTWARE\Policies\Microsoft\Windows Defender\Windows Defender Exploit Guard\ASR\Rules
```

```powershell
# Abilitare regole ASR critiche via Registry (modalità Block = 1)
$asrPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows Defender\Policy Manager"
New-Item -Path $asrPath -Force | Out-Null

# Bloccare contenuto eseguibile da email client e webmail
Set-ItemProperty -Path $asrPath -Name "ASRRules" -Value @(
    "BE9BA2D9-53EA-4CDC-84E5-9B1EEEE46550=1"  # Block executable content from email
    "D4F940AB-401B-4EFC-AADC-AD5F3C50688A=1"  # Block Office from creating child processes
    "3B576869-A4EC-4529-8536-B80A7769E899=1"  # Block Office from creating executable content
    "75668C1F-73B5-4CF0-BB93-3ECF5CB7CC84=1"  # Block Office from injecting into processes
    "D3E037E1-3EB8-44C8-A917-57927947596D=1"  # Block JavaScript/VBScript launching downloads
    "5BEB7EFE-FD9A-4556-801D-275E5FFC04CC=1"  # Block execution of obfuscated scripts
    "92E97FA1-2EDF-4476-BDD6-9DD0B4DDDC7B=1"  # Block Win32 API calls from Office macros
    "01443614-CD74-433A-B99E-2ECDC07BFC25=1"  # Block executable files unless they meet criteria
)

# Verificare regole ASR attive
Get-MpPreference | Select-Object -ExpandProperty AttackSurfaceReductionRules_Ids
Get-MpPreference | Select-Object -ExpandProperty AttackSurfaceReductionRules_Actions
```

**Modalità Audit consigliata per il deployment iniziale:**

Prima di attivare il blocco, impostare tutte le regole con valore `2` (Audit) e monitorare gli eventi in `Microsoft-Windows-Windows Defender/Operational` con Event ID 1121 (block) e 1122 (audit). Questo evita falsi positivi che interrompono la produttività.

**Difesa da persistence IFEO (Image File Execution Options):**

La chiave `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options` è uno dei vettori di persistenza più abusati dagli attaccanti (MITRE ATT&CK T1546.012). Un attaccante può impostare il valore `Debugger` su un eseguibile malevolo, che verrà lanciato ogni volta che il processo legittimo viene avviato.

```powershell
# Esempio di persistence IFEO malevola (a scopo difensivo — capire per proteggere)
# L'attaccante crea:
# HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\notepad.exe
#   Debugger = "C:\malware\payload.exe"
# Ogni volta che notepad.exe viene avviato, Windows esegue payload.exe al suo posto

# Monitorare chiavi IFEO sospette
$ifeoPath = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options"
Get-ChildItem $ifeoPath | ForEach-Object {
    $debugger = (Get-ItemProperty $_.PSPath -Name "Debugger" -ErrorAction SilentlyContinue).Debugger
    $silentExit = (Get-ItemProperty $_.PSPath -Name "MonitorProcess" -ErrorAction SilentlyContinue).MonitorProcess
    if ($debugger -or $silentExit) {
        [PSCustomObject]@{
            Process        = $_.PSChildName
            Debugger       = $debugger
            MonitorProcess = $silentExit
        }
    }
}
```

**SilentProcessExit** — un secondo vettore IFEO meno noto: l'attaccante può registrare un `MonitorProcess` in `HKLM\...\SilentProcessExit\<processo>` che viene eseguito quando il processo target termina. Hardening raccomandato:

```powershell
# ACL restrittiva su IFEO — solo SYSTEM e Administrators possono scrivere
$acl = Get-Acl $ifeoPath
$acl.SetAccessRuleProtection($true, $false)  # Disabilita ereditarietà
$ruleSystem = New-Object System.Security.AccessControl.RegistryAccessRule(
    "NT AUTHORITY\SYSTEM", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow"
)
$ruleAdmin = New-Object System.Security.AccessControl.RegistryAccessRule(
    "BUILTIN\Administrators", "ReadKey", "ContainerInherit,ObjectInherit", "None", "Allow"
)
$acl.AddAccessRule($ruleSystem)
$acl.AddAccessRule($ruleAdmin)
Set-Acl $ifeoPath $acl
# ATTENZIONE: testare in ambiente non-produttivo — alcune applicazioni legittime usano IFEO
```

**SACL su IFEO per auditing:** configurare una SACL (System Access Control List) sulla chiave IFEO per generare Event ID 4657 ogni volta che un processo tenta di creare o modificare un valore `Debugger`. Questo fornisce un allarme precoce di tentativi di persistenza.

### Rete

```powershell
# Disabilitare IPv6 (se non necessario)
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters" `
    -Name "DisabledComponents" -Value 0xFF -PropertyType DWord -Force

# Configurare DNS suffix search order
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" `
    -Name "SearchList" -Value "corp.contoso.com,contoso.com"

# Aumentare il numero massimo di connessioni TCP simultanee
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" `
    -Name "TcpNumConnections" -Value 0x00FFFFFE -Type DWord

# Abilitare TCP Window Scaling (RFC 1323)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" `
    -Name "Tcp1323Opts" -Value 3 -Type DWord

# Configurare ARP cache timeout (secondi)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" `
    -Name "ArpCacheMinReferencedLife" -Value 600 -Type DWord

# Disabilitare Nagle algorithm per bassa latenza
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters" `
    -Name "TcpNoDelay" -Value 1 -Type DWord

# Configurare DNS client per usare DNS over HTTPS (Win11)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Dnscache\Parameters" `
    -Name "EnableAutoDoh" -Value 2 -Type DWord

# Disabilitare mDNS (Multicast DNS, espone hostname in rete)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Dnscache\Parameters" `
    -Name "EnableMDNS" -Value 0 -Type DWord
```

### Desktop e Interfaccia Utente

```powershell
# Mostrare estensioni file in Explorer
Set-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced" `
    -Name "HideFileExt" -Value 0

# Mostrare file nascosti
Set-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced" `
    -Name "Hidden" -Value 1

# Mostrare file di sistema protetti
Set-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced" `
    -Name "ShowSuperHidden" -Value 1

# Disabilitare raggruppamento nella barra delle applicazioni (Win10)
Set-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced" `
    -Name "TaskbarGlomLevel" -Value 2

# Aprire Explorer su "Questo PC" anziché "Accesso rapido"
Set-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced" `
    -Name "LaunchTo" -Value 1

# Abilitare percorso completo nella barra del titolo di Explorer
Set-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\CabinetState" `
    -Name "FullPath" -Value 1

# Disabilitare Snap Assist
Set-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced" `
    -Name "SnapAssist" -Value 0

# Disabilitare notifiche (Focus Assist permanente)
New-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings" `
    -Name "NOC_GLOBAL_SETTING_TOASTS_ENABLED" -Value 0 -PropertyType DWord -Force

# Ripristinare menu contestuale classico in Windows 11
New-Item -Path "HKCU:\SOFTWARE\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32" -Force
Set-ItemProperty -Path "HKCU:\SOFTWARE\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\InprocServer32" `
    -Name "(Default)" -Value ""

# Impostare tema scuro per le applicazioni
Set-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize" `
    -Name "AppsUseLightTheme" -Value 0
# Impostare tema scuro per il sistema
Set-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize" `
    -Name "SystemUsesLightTheme" -Value 0
```

### Windows Update

```powershell
# Disabilitare aggiornamenti automatici (solo in ambienti gestiti — non raccomandato per endpoint)
# Valore 1 = Non controllare mai
# Valore 2 = Notifica download
# Valore 3 = Scarica automaticamente, notifica installazione
# Valore 4 = Scarica e installa automaticamente
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" `
    -Name "AUOptions" -Value 3

# Configurare server WSUS
$wuPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate"
New-Item -Path $wuPath -Force | Out-Null
Set-ItemProperty -Path $wuPath -Name "WUServer" -Value "https://wsus.contoso.com:8531"
Set-ItemProperty -Path $wuPath -Name "WUStatusServer" -Value "https://wsus.contoso.com:8531"
Set-ItemProperty -Path "$wuPath\AU" -Name "UseWUServer" -Value 1

# Disabilitare driver updates tramite Windows Update
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" `
    -Name "ExcludeWUDriversInQualityUpdate" -Value 1

# Configurare ore attive (orario in cui non riavviare)
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings" `
    -Name "ActiveHoursStart" -Value 8
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings" `
    -Name "ActiveHoursEnd" -Value 20

# Differire feature updates (giorni, max 365)
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" `
    -Name "DeferFeatureUpdates" -Value 1
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" `
    -Name "DeferFeatureUpdatesPeriodInDays" -Value 90

# Differire quality updates (giorni, max 30)
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" `
    -Name "DeferQualityUpdates" -Value 1
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" `
    -Name "DeferQualityUpdatesPeriodInDays" -Value 7
```

### Startup e Avvio

```powershell
# Programmi che si avviano automaticamente — posizioni nel Registry:

# Per tutti gli utenti (richiede admin):
# HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
# HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce

# Per l'utente corrente:
# HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
# HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce

# Per servizi 32-bit su Windows 64-bit:
# HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run

# Elencare tutti i programmi autostart
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
Get-ItemProperty "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
Get-ItemProperty "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run" `
    -ErrorAction SilentlyContinue

# Aggiungere un programma all'autostart (utente corrente)
Set-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" `
    -Name "MyApp" -Value "C:\Program Files\MyApp\myapp.exe"

# Rimuovere un programma dall'autostart
Remove-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" -Name "MyApp"

# RunOnce — eseguire un comando al prossimo avvio e poi rimuovere
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce" `
    -Name "CleanupScript" -Value "C:\Scripts\cleanup.bat"

# Abilitare Last Known Good boot option (verbose)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Configuration Manager" `
    -Name "BackupCount" -Value 2

# Ridurre timeout di selezione OS nel boot loader (secondi)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager" `
    -Name "BootTimeout" -Value 5
# (Nota: normalmente si configura con bcdedit /timeout 5)

# Disabilitare boot logo per boot più veloce
# bcdedit /set quietboot on (più appropriato via bcdedit)

# Disabilitare startup delay (Windows 10+)
New-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Serialize" `
    -Name "StartupDelayInMSec" -Value 0 -PropertyType DWord -Force
```

---

## Registry per GPO e Deploy

### Come le GPO Scrivono nel Registry

```
Le GPO applicano impostazioni scrivendo valori nel Registry:
- Computer Configuration → HKLM\SOFTWARE\Policies\...
- User Configuration → HKCU\SOFTWARE\Policies\...

Queste chiavi vengono rimosse quando la GPO non si applica più (tattooing solo per Preferences).

# Preferences (User/Computer → Preferences → Windows Settings → Registry)
# Possono scrivere OVUNQUE nel registry
# Non vengono rimosse automaticamente
```

Le GPO vengono processate in questo ordine:
1. **Local GPO** (`C:\Windows\System32\GroupPolicy`)
2. **Site GPO** (livello AD site)
3. **Domain GPO**
4. **OU GPO** (dal livello più alto a quello più basso)

L'ultimo GPO processato "vince" in caso di conflitto (a meno che non ci sia un Enforced/No Override).

### Administrative Templates — ADMX/ADML

I template amministrativi sono file XML che definiscono le impostazioni delle GPO:

- **ADMX:** file XML con la definizione delle impostazioni (chiave registry, tipo, valori possibili).
- **ADML:** file di localizzazione (traduzione in varie lingue).

**Posizione dei file:**

```
# Local Policy Definitions
C:\Windows\PolicyDefinitions\
├── *.admx                    → Template definitions
└── it-IT\                    → Traduzioni italiane
    └── *.adml

# Central Store (dominio — preferito)
\\contoso.com\SYSVOL\contoso.com\Policies\PolicyDefinitions\
├── *.admx
└── it-IT\
    └── *.adml
```

**Come un ADMX definisce un'impostazione:**

```xml
<!-- Esempio semplificato di definizione ADMX -->
<policy name="AllowCortana"
        class="Machine"
        displayName="$(string.AllowCortana)"
        key="SOFTWARE\Policies\Microsoft\Windows\Windows Search"
        valueName="AllowCortana">
  <parentCategory ref="SearchCategory" />
  <supportedOn ref="SUPPORTED_Windows10" />
  <enabledValue>
    <decimal value="1" />
  </enabledValue>
  <disabledValue>
    <decimal value="0" />
  </disabledValue>
</policy>
```

Questo template indica che:
- La chiave è `HKLM\SOFTWARE\Policies\Microsoft\Windows\Windows Search`
- Il valore è `AllowCortana` di tipo DWORD
- Abilitato = 1, Disabilitato = 0

**Creare ADMX personalizzati:** utile per distribuire configurazioni applicative via GPO. Strumenti: ADMX Migrator, editor di testo con schema ADMX.

### Tattoo Effect

Il **tattoo effect** si verifica quando un'impostazione di policy viene rimossa ma il valore rimane nel Registry.

**Policy tradizionali (Administrative Templates):** scrivono in `SOFTWARE\Policies\...`. Quando la GPO viene rimossa o de-linkata, il valore viene eliminato. **Nessun tattoo effect.**

**Preferences:** scrivono in qualsiasi posizione del Registry. Quando la GPO viene rimossa, il valore **rimane** (tattoo effect). Per rimuoverlo:
- Creare una Preference con azione "Delete"
- Rimuovere manualmente i valori
- Usare uno script di cleanup

**Vecchie policy (pre-Windows 2000):** scrivevano direttamente in `SOFTWARE\Microsoft\...` anziché in `SOFTWARE\Policies\...`. Queste causano tattoo effect perché il policy engine non sa che deve rimuoverle.

### Preference Items

Le GPO Preferences permettono di manipolare il Registry con maggiore flessibilità rispetto alle Administrative Templates.

```
# In Group Policy Management:
# Computer Configuration → Preferences → Windows Settings → Registry

# Azioni disponibili:
# Create  → Crea se non esiste
# Replace → Crea o sovrascrive
# Update  → Aggiorna se esiste, crea se non esiste
# Delete  → Elimina

# Item-Level Targeting:
# Applicare la modifica solo a specifici computer/utenti/condizioni
```

**Differenze chiave Policies vs Preferences:**

| Caratteristica | Administrative Templates (Policy) | Preferences |
|----------------|-----------------------------------|-------------|
| Posizione registry | `SOFTWARE\Policies\...` | Qualsiasi |
| Rimossa con GPO | Sì | No (tattoo) |
| UI grayed out | Sì (utente non può modificare) | No |
| Item-level targeting | No | Sì |
| Azioni | Enable/Disable | Create/Replace/Update/Delete |
| Filtro condizionale | WMI filter (a livello GPO) | Per singolo item |

### File .reg per Deploy

```reg
Windows Registry Editor Version 5.00

; Commento: disabilitare SMBv1
[HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters]
"SMB1"=dword:00000000

; Creare chiave e valori
[HKEY_LOCAL_MACHINE\SOFTWARE\MyCompany\Settings]
"ServerURL"="https://app.contoso.com"
"Timeout"=dword:0000001e
"Features"=hex(7):66,00,65,00,61,00,74,00,31,00,00,00,66,00,65,00,61,00,74,00,32,00,00,00,00,00

; Eliminare un valore (trattino davanti al nome)
[HKEY_LOCAL_MACHINE\SOFTWARE\MyCompany\Settings]
"OldValue"=-

; Eliminare una chiave intera (trattino davanti al path)
[-HKEY_LOCAL_MACHINE\SOFTWARE\MyCompany\OldKey]
```

**Formato file .reg — dettaglio:**

```reg
Windows Registry Editor Version 5.00
; Questa riga è OBBLIGATORIA come prima riga del file

; Commenti iniziano con punto e virgola
; Righe vuote sono ignorate

; === TIPI DI DATI ===

; Stringa (REG_SZ)
[HKEY_LOCAL_MACHINE\SOFTWARE\Example]
"StringValue"="Hello World"

; Stringa con caratteri speciali (backslash va raddoppiato)
"PathValue"="C:\\Program Files\\MyApp"

; Stringa espandibile (REG_EXPAND_SZ) — hex(2)
"ExpandValue"=hex(2):25,00,54,00,45,00,4d,00,50,00,25,00,00,00

; Multi-stringa (REG_MULTI_SZ) — hex(7)
"MultiValue"=hex(7):41,00,00,00,42,00,00,00,00,00

; DWORD (REG_DWORD) — dword:XXXXXXXX (8 cifre hex)
"DwordValue"=dword:0000002a

; QWORD (REG_QWORD) — hex(b)
"QwordValue"=hex(b):00,00,00,01,00,00,00,00

; Binario (REG_BINARY) — hex:
"BinaryValue"=hex:01,02,03,04,05

; Valori lunghi possono andare a capo con backslash
"LongBinary"=hex:01,02,03,04,05,06,07,08,09,0a,0b,0c,0d,0e,0f,10,\
  11,12,13,14,15,16,17,18,19,1a,1b,1c,1d,1e,1f,20

; Valore predefinito (senza nome)
@="DefaultValue"

; Eliminare un valore
"DeleteMe"=-

; Eliminare una chiave intera (trattino prima del path)
[-HKEY_LOCAL_MACHINE\SOFTWARE\Example\SubkeyToDelete]
```

**Deploy automatizzato con file .reg:**

```cmd
:: Importare silenziosamente (senza conferma utente)
regedit /s C:\Deploy\settings.reg

:: Via GPO startup script
:: Computer Configuration → Windows Settings → Scripts → Startup
:: Aggiungere: regedit.exe /s \\server\share\settings.reg

:: Via Scheduled Task
schtasks /create /tn "ApplyRegistrySettings" /tr "regedit.exe /s C:\Deploy\settings.reg" ^
    /sc onlogon /ru SYSTEM /rl HIGHEST
```

### Gestione Registry via Intune e MDM

In ambienti cloud-first o ibridi, Intune consente di gestire chiavi di Registry senza infrastruttura Active Directory on-premises, utilizzando il protocollo OMA-DM e i Configuration Service Provider (CSP) di Windows.

**Tre approcci per gestire il Registry via Intune:**

| Metodo | Caso d'uso | Complessità |
|--------|-----------|-------------|
| **Settings Catalog** | Policy documentate con UI grafica | Bassa |
| **ADMX ingestion** | Policy enterprise con template ADMX personalizzati | Media |
| **Custom OMA-URI** | Qualsiasi valore Registry arbitrario | Alta |

**Settings Catalog (raccomandato):**

Dal portale Intune → Devices → Configuration profiles → Create → Settings Catalog. Questo metodo espone migliaia di policy con descrizione e validazione integrata. Internamente, ogni setting mappa a uno o più valori Registry tramite il Policy CSP.

**ADMX ingestion (Win10 1703+):**

Per policy enterprise non disponibili nel Settings Catalog, è possibile "ingestionare" file ADMX personalizzati:

1. Convertire il file ADMX in formato OMA-URI usando il path: `./Device/Vendor/MSFT/Policy/ConfigOperations/ADMXInstall/{AppName}/Policy/{SettingName}`
2. Il payload è l'intero contenuto XML del file ADMX codificato come stringa
3. Dopo l'ingestion, le policy diventano configurabili tramite OMA-URI standard

```xml
<!-- Esempio di configurazione OMA-URI per policy ADMX -->
<!-- URI: ./Device/Vendor/MSFT/Policy/Config/Chrome~Policy~googlechrome/HomepageLocation -->
<enabled/>
<data id="HomepageLocation" value="https://intranet.company.com"/>
```

**Custom OMA-URI per valori Registry arbitrari:**

Per scrivere direttamente nel Registry senza passare da un CSP specifico, utilizzare il **Registry CSP** (disponibile da Windows 10):

```
OMA-URI: ./Device/Vendor/MSFT/Registry/{RegistryHive}/{KeyPath}/{ValueName}
```

Dove `{RegistryHive}` è uno tra `HKLM`, `HKCU`, `HKCR`. Il tipo di dato OMA-DM corrisponde ai tipi Registry:

| Tipo Registry | Tipo OMA-DM |
|--------------|-------------|
| REG_SZ | chr (string) |
| REG_DWORD | int |
| REG_BINARY | bin (base64) |
| REG_MULTI_SZ | chr con separatore `&#xF000;` |

**SyncML sottostante:**

Ogni configurazione OMA-URI viene tradotta in un messaggio SyncML che il client MDM di Windows elabora:

```xml
<SyncBody>
  <Replace>
    <CmdID>1</CmdID>
    <Item>
      <Target>
        <LocURI>./Device/Vendor/MSFT/Policy/Config/WindowsDefender/AllowRealtimeMonitoring</LocURI>
      </Target>
      <Meta>
        <Format xmlns="syncml:metinf">int</Format>
      </Meta>
      <Data>1</Data>
    </Item>
  </Replace>
</SyncBody>
```

**Troubleshooting Intune + Registry:**

```powershell
# Verificare che le policy Intune siano state applicate localmente
# Le policy MDM vengono scritte in:
# HKLM\SOFTWARE\Microsoft\PolicyManager\current\device
# HKLM\SOFTWARE\Microsoft\PolicyManager\Providers\{ProviderGUID}\default\Device
Get-ChildItem "HKLM:\SOFTWARE\Microsoft\PolicyManager\current\device" -Recurse |
    Where-Object { $_.ValueCount -gt 0 } |
    ForEach-Object {
        $props = Get-ItemProperty $_.PSPath
        [PSCustomObject]@{
            Path   = $_.PSPath -replace 'Microsoft.PowerShell.Core\\Registry::', ''
            Values = ($props.PSObject.Properties |
                Where-Object { $_.Name -notlike 'PS*' } |
                ForEach-Object { "$($_.Name)=$($_.Value)" }) -join '; '
        }
    } | Format-Table -AutoSize

# Forzare sincronizzazione MDM
Start-Process "ms-settings:workplace"
# Oppure via riga di comando:
& "$env:windir\system32\deviceenroller.exe" /c /AutoEnrollMDM
```

**Conflitti GPO vs MDM:** quando un dispositivo è gestito sia da Active Directory GPO sia da Intune, il Policy CSP di Windows segue la regola "MDM wins over GP" se configurato con `ControlPolicyConflict/MDMWinsOverGP = 1` in `HKLM\SOFTWARE\Policies\Microsoft\Windows\CurrentVersion\MDM`. In caso contrario, la GPO ha precedenza. Pianificare attentamente la coesistenza durante la migrazione a cloud-only management.

---

## Sicurezza del Registry

### Permessi (ACL)

Ogni chiave del Registry ha un Security Descriptor che definisce chi può leggere, scrivere ed eliminare la chiave e i suoi valori.

**Permessi disponibili:**

| Permesso | Descrizione |
|----------|-------------|
| Query Value | Leggere valori |
| Set Value | Creare/modificare valori |
| Create Subkey | Creare sotto-chiavi |
| Enumerate Subkeys | Elencare sotto-chiavi |
| Notify | Ricevere notifiche di modifica |
| Create Link | Creare link simbolici |
| Delete | Eliminare la chiave |
| Write DAC | Modificare i permessi (DACL) |
| Write Owner | Cambiare il proprietario |
| Read Control | Leggere il security descriptor |
| Full Control | Tutti i permessi sopra |

**Gestire permessi via PowerShell:**

```powershell
# Leggere permessi di una chiave
$acl = Get-Acl "HKLM:\SOFTWARE\MyCompany"
$acl.Access | Format-Table IdentityReference, RegistryRights, AccessControlType

# Aggiungere permesso di lettura per un gruppo
$rule = New-Object System.Security.AccessControl.RegistryAccessRule(
    "CONTOSO\AppUsers",
    "ReadKey",
    "ContainerInherit,ObjectInherit",
    "None",
    "Allow"
)
$acl.AddAccessRule($rule)
Set-Acl "HKLM:\SOFTWARE\MyCompany" $acl

# Rimuovere un permesso
$acl = Get-Acl "HKLM:\SOFTWARE\MyCompany"
$ruleToRemove = $acl.Access | Where-Object { $_.IdentityReference -eq "CONTOSO\AppUsers" }
$acl.RemoveAccessRule($ruleToRemove)
Set-Acl "HKLM:\SOFTWARE\MyCompany" $acl

# Cambiare proprietario (Take Ownership)
$acl = Get-Acl "HKLM:\SOFTWARE\ProtectedKey"
$owner = New-Object System.Security.Principal.NTAccount("BUILTIN\Administrators")
$acl.SetOwner($owner)
Set-Acl "HKLM:\SOFTWARE\ProtectedKey" $acl

# Disabilitare ereditarietà e copiare permessi esistenti
$acl = Get-Acl "HKLM:\SOFTWARE\MyCompany"
$acl.SetAccessRuleProtection($true, $true)  # (proteggi, copia regole ereditate)
Set-Acl "HKLM:\SOFTWARE\MyCompany" $acl
```

**Gestire permessi via regedit:**

1. Tasto destro sulla chiave → Autorizzazioni
2. Per opzioni avanzate: pulsante "Avanzate"
3. Cambiare proprietario: Avanzate → Proprietario → Cambia
4. Modificare ereditarietà: Avanzate → togliere "Includi autorizzazioni ereditabili"

**Gestire permessi via reg.exe e SubInACL:**

```cmd
:: SubInACL (strumento Microsoft separato)
subinacl /keyreg "HKEY_LOCAL_MACHINE\SOFTWARE\MyCompany" /grant=CONTOSO\AppUsers=R
subinacl /keyreg "HKEY_LOCAL_MACHINE\SOFTWARE\MyCompany" /owner=BUILTIN\Administrators
```

### Auditing del Registry

L'auditing permette di registrare nel Security Event Log chi accede o modifica specifiche chiavi del Registry.

**Configurazione:**

1. Abilitare l'audit policy (via GPO o secpol.msc):
   - Computer Configuration → Windows Settings → Security Settings → Advanced Audit Policy Configuration → Object Access → Audit Registry
   - Oppure:
   ```powershell
   auditpol /set /subcategory:"Registry" /success:enable /failure:enable
   ```

2. Configurare il SACL (System Access Control List) sulla chiave:
   ```powershell
   $acl = Get-Acl "HKLM:\SOFTWARE\CriticalApp"
   $auditRule = New-Object System.Security.AccessControl.RegistryAuditRule(
       "Everyone",
       "SetValue,Delete",
       "ContainerInherit,ObjectInherit",
       "None",
       "Success,Failure"
   )
   $acl.AddAuditRule($auditRule)
   Set-Acl "HKLM:\SOFTWARE\CriticalApp" $acl
   ```

3. Gli eventi vengono registrati nell'Event Log come **Event ID 4657** (Security log):
   - Object Name: la chiave modificata
   - Object Value Name: il valore modificato
   - Process Name: il processo che ha effettuato la modifica
   - Account Name: l'utente

**Query eventi audit:**

```powershell
# Cercare eventi di modifica Registry nelle ultime 24 ore
Get-WinEvent -FilterHashtable @{
    LogName   = 'Security'
    Id        = 4657
    StartTime = (Get-Date).AddHours(-24)
} | Select-Object TimeCreated,
    @{N='Account';E={$_.Properties[1].Value}},
    @{N='Key';E={$_.Properties[4].Value}},
    @{N='Value';E={$_.Properties[5].Value}},
    @{N='NewValue';E={$_.Properties[10].Value}}
```

### Monitoraggio avanzato con Sysmon e Windows Event Forwarding

L'Event ID 4657 nativo di Windows richiede la configurazione di SACL su ogni chiave da monitorare. **Sysmon** (System Monitor, parte di Sysinternals) offre un approccio più flessibile e scalabile per il monitoraggio del Registry, generando eventi dedicati senza richiedere modifiche alle ACL.

**Event ID Sysmon per il Registry:**

| Event ID | Operazione | Descrizione |
|----------|-----------|-------------|
| 12 | CreateKey / DeleteKey | Creazione o eliminazione di una chiave |
| 13 | SetValue | Impostazione di un valore (include il dato scritto) |
| 14 | RenameKey | Rinomina di una chiave |

**Configurazione Sysmon mirata al Registry:**

La configurazione di Sysmon va progettata con un approccio **inclusion-first** per le operazioni Registry: monitorare solo le chiavi ad alto valore evita il rumore e l'impatto sulle performance.

```xml
<!-- Estratto di configurazione Sysmon per monitoraggio Registry -->
<!-- Basato su SwiftOnSecurity/sysmon-config e Olaf Hartong/sysmon-modular -->
<Sysmon schemaversion="4.90">
  <EventFiltering>
    <!-- Event ID 13: SetValue — monitorare persistence e tampering -->
    <RegistryEvent onmatch="include">
      <!-- Run keys — persistence classica -->
      <TargetObject condition="contains">\CurrentVersion\Run</TargetObject>
      <!-- Services — nuovi servizi o modifica path -->
      <TargetObject condition="contains">\Services\</TargetObject>
      <TargetObject condition="end with">\ImagePath</TargetObject>
      <TargetObject condition="end with">\ServiceDll</TargetObject>
      <!-- IFEO — debugger hijacking -->
      <TargetObject condition="contains">\Image File Execution Options\</TargetObject>
      <TargetObject condition="end with">\Debugger</TargetObject>
      <!-- AppInit_DLLs — DLL injection legacy -->
      <TargetObject condition="contains">\Windows\CurrentVersion\Windows</TargetObject>
      <TargetObject condition="end with">\AppInit_DLLs</TargetObject>
      <!-- WinLogon — persistence via Userinit/Shell -->
      <TargetObject condition="contains">\Microsoft\Windows NT\CurrentVersion\Winlogon</TargetObject>
      <!-- Security policy tampering -->
      <TargetObject condition="contains">\Policies\Microsoft\Windows Defender</TargetObject>
      <TargetObject condition="contains">\Policies\Microsoft\Windows\PowerShell</TargetObject>
      <!-- LSA — credential dumping e security packages -->
      <TargetObject condition="contains">\Control\Lsa</TargetObject>
      <TargetObject condition="end with">\Security Packages</TargetObject>
      <!-- COM hijacking -->
      <TargetObject condition="contains">\Classes\CLSID\</TargetObject>
      <TargetObject condition="end with">\InprocServer32</TargetObject>
      <!-- Scheduled Tasks persistence via Registry -->
      <TargetObject condition="contains">\Schedule\TaskCache</TargetObject>
    </RegistryEvent>

    <!-- Event ID 12: CreateKey / DeleteKey — chiavi critiche -->
    <RegistryEvent onmatch="include">
      <EventType condition="is">CreateKey</EventType>
      <TargetObject condition="contains">\Image File Execution Options\</TargetObject>
      <TargetObject condition="contains">\SilentProcessExit\</TargetObject>
      <TargetObject condition="contains">\CurrentVersion\Run</TargetObject>
    </RegistryEvent>
  </EventFiltering>
</Sysmon>
```

```powershell
# Installare e configurare Sysmon con la config di monitoraggio
# Scaricare Sysmon da: https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon
sysmon64.exe -accepteula -i sysmon-registry-config.xml

# Aggiornare una configurazione esistente
sysmon64.exe -c sysmon-registry-config.xml

# Verificare che Sysmon stia generando eventi Registry
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" -FilterXPath "*[System[EventID=13]]" -MaxEvents 5 |
    Select-Object TimeCreated,
        @{N='Process';E={$_.Properties[3].Value}},
        @{N='TargetObject';E={$_.Properties[5].Value}},
        @{N='Details';E={$_.Properties[6].Value}}
```

**Windows Event Forwarding (WEF) per centralizzare gli eventi Registry:**

In ambienti enterprise, gli eventi Sysmon vanno inoltrati a un collector centralizzato tramite WEF, che utilizza il protocollo WinRM.

```powershell
# Sul collector — creare una subscription per eventi Sysmon Registry
# Prerequisito: il servizio Windows Event Collector deve essere attivo
wecutil cs /c:SysmonRegistrySubscription.xml

# Contenuto della subscription XML:
# - QueryList con EventID 12, 13, 14 dal log Sysmon/Operational
# - DeliveryMode: Push (i client inviano eventi al collector)
# - ContentFormat: RenderedText

# Sul client — abilitare WinRM e configurare il collector
winrm quickconfig -q
# Aggiungere il collector alla policy:
# Computer Configuration → Admin Templates → Windows Components →
# Event Forwarding → Configure target Subscription Manager
# Valore: Server=http://collector.domain.local:5985/wsman/SubscriptionManager/WEC
```

**Pipeline completo di rilevamento:**

```
Modifica Registry → Sysmon Event 12/13/14 → WEF → SIEM/Splunk/Sentinel
                                                   ↓
                                              Regola di correlazione
                                                   ↓
                                              Alert + risposta automatica
```

**Basi di configurazione consigliate:**

- **SwiftOnSecurity/sysmon-config**: configurazione community ampiamente testata, buon punto di partenza.
- **Olaf Hartong/sysmon-modular**: approccio modulare che consente di assemblare la configurazione per componenti (Registry, processo, rete).
- **ZZZCMS/sysmon-config (Microsoft)**: template ufficiale Microsoft per ambienti enterprise.

**Performance considerations:** Sysmon Event 13 (SetValue) può generare un volume elevato di eventi se configurato con filtri troppo ampi. Monitorare il log size di Sysmon/Operational e impostare una dimensione massima adeguata (`wevtutil sl Microsoft-Windows-Sysmon/Operational /ms:268435456` per 256 MB). In ambienti con forte I/O sul Registry, valutare l'uso di `condition="begin with"` invece di `condition="contains"` per ridurre l'overhead di pattern matching.

### Registry Virtualization (UAC)

La virtualizzazione del Registry è un meccanismo di compatibilità introdotto con Windows Vista/UAC per le applicazioni legacy che tentano di scrivere in `HKLM\SOFTWARE` senza privilegi di amministratore.

**Come funziona:**

1. Un'applicazione non elevata tenta di scrivere in `HKLM\SOFTWARE\AppName\Setting`.
2. Windows intercetta la scrittura e la reindirizza a `HKCU\SOFTWARE\Classes\VirtualStore\MACHINE\SOFTWARE\AppName\Setting`.
3. Le letture successive dalla stessa app restituiscono il valore virtualizzato.
4. L'utente non se ne accorge — l'applicazione funziona come se avesse scritto in HKLM.

**Quando si applica:**

- Solo a processi 32-bit che non hanno un manifest con `requestedExecutionLevel`.
- Non si applica a processi 64-bit.
- Non si applica a processi con manifest UAC (asInvoker, requireAdministrator, highestAvailable).
- Non si applica a servizi, driver, o processi COM.
- Non si applica alle chiavi sotto `HKLM\SOFTWARE\Classes`.

**Verificare la virtualizzazione:**

```powershell
# Vedere i dati virtualizzati di un utente
Get-ChildItem "HKCU:\SOFTWARE\Classes\VirtualStore\MACHINE\SOFTWARE" -ErrorAction SilentlyContinue

# Disabilitare la virtualizzazione (sconsigliato, rompe la compatibilità)
# Via GPO: Computer Configuration → Windows Settings → Security Settings
#   → Local Policies → Security Options
#   → "User Account Control: Virtualize file and registry write failures to per-user locations" = Disabled
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -Name "EnableVirtualization" -Value 0
```

**WOW6432Node — Registry Redirection (32-bit vs 64-bit):**

Su Windows 64-bit, le applicazioni 32-bit vedono una vista diversa del Registry:

| Applicazione | Chiave richiesta | Chiave effettiva |
|-------------|------------------|------------------|
| 64-bit | `HKLM\SOFTWARE\MyApp` | `HKLM\SOFTWARE\MyApp` |
| 32-bit | `HKLM\SOFTWARE\MyApp` | `HKLM\SOFTWARE\WOW6432Node\MyApp` |

```powershell
# Forzare la vista 32-bit o 64-bit con reg.exe
reg query "HKLM\SOFTWARE\MyApp" /reg:32    # vista 32-bit
reg query "HKLM\SOFTWARE\MyApp" /reg:64    # vista 64-bit

# In PowerShell, usare le API .NET per scegliere la vista
$reg32 = [Microsoft.Win32.RegistryKey]::OpenBaseKey(
    [Microsoft.Win32.RegistryHive]::LocalMachine,
    [Microsoft.Win32.RegistryView]::Registry32
)
$key32 = $reg32.OpenSubKey("SOFTWARE\MyApp")

$reg64 = [Microsoft.Win32.RegistryKey]::OpenBaseKey(
    [Microsoft.Win32.RegistryHive]::LocalMachine,
    [Microsoft.Win32.RegistryView]::Registry64
)
$key64 = $reg64.OpenSubKey("SOFTWARE\MyApp")
```

### WOW6432Node — deep dive sulla redirezione 32/64 bit

Il meccanismo WOW64 (Windows on Windows 64-bit) gestisce la coesistenza tra applicazioni a 32 e 64 bit mantenendo viste separate del Registry. La comprensione dettagliata di questo sistema è fondamentale per evitare errori di configurazione e per l'analisi forense.

**Architettura della redirezione:**

Quando un'applicazione a 32 bit accede a `HKLM\SOFTWARE`, Windows la reindirizza silenziosamente a `HKLM\SOFTWARE\WOW6432Node`. Questo avviene a livello di kernel tramite il Registry Redirector, trasparente per l'applicazione.

```
Applicazione 64-bit → HKLM\SOFTWARE\RealApp\     (percorso reale)
Applicazione 32-bit → HKLM\SOFTWARE\RealApp\     (vista dall'app)
                       ↓ redirezione kernel
                       HKLM\SOFTWARE\WOW6432Node\RealApp\ (percorso fisico)
```

**Chiavi soggette a redirezione vs chiavi condivise:**

Non tutte le sottochiavi di `HKLM\SOFTWARE` vengono reindirizzate. Alcune sono **condivise** tra le viste 32-bit e 64-bit:

| Chiave | Comportamento | Motivo |
|--------|--------------|--------|
| `SOFTWARE\Classes\CLSID` | **Redirect** | COM registration separata per bitness |
| `SOFTWARE\Classes\AppID` | **Shared** | Identità applicazione indipendente dal bitness |
| `SOFTWARE\Classes\.ext` | **Shared** | Associazioni file comuni |
| `SOFTWARE\Classes\Interface` | **Shared** | Interfacce COM condivise (marshaling cross-bitness) |
| `SOFTWARE\Classes\TypeLib` | **Redirect** | Type libraries specifiche per architettura |
| `SOFTWARE\Microsoft\COM3` | **Redirect** | Configurazione COM separata |
| `SOFTWARE\Microsoft\EventSystem` | **Shared** | Event system unificato |
| `SOFTWARE\Microsoft\Cryptography` | **Shared** | Provider crittografici condivisi |
| `SOFTWARE\Microsoft\Windows\CurrentVersion\Run` | **Redirect** | Autostart separato per bitness |
| `SOFTWARE\Microsoft\Windows NT` | **Shared** (parziale) | Configurazione OS core |

**Registry Reflection (rimossa):**

Fino a Windows 7 / Server 2008 R2, il sistema utilizzava un meccanismo chiamato **Registry Reflection** che copiava automaticamente determinate chiavi tra la vista nativa e la vista WOW6432Node per mantenere la coerenza. Dalla rimozione della reflection, le due viste sono completamente indipendenti per le chiavi soggette a redirezione.

**Flag di accesso per controllare la vista:**

```powershell
# Accedere esplicitamente alla vista 64-bit da un processo 32-bit
# (utile in script PowerShell x86 o applicazioni .NET compilate per x86)

# KEY_WOW64_64KEY (0x0100) — forza accesso alla vista nativa 64-bit
$reg = [Microsoft.Win32.RegistryKey]::OpenBaseKey(
    [Microsoft.Win32.RegistryHive]::LocalMachine,
    [Microsoft.Win32.RegistryView]::Registry64  # equivale a KEY_WOW64_64KEY
)

# KEY_WOW64_32KEY (0x0200) — forza accesso alla vista WOW6432Node
$reg32 = [Microsoft.Win32.RegistryKey]::OpenBaseKey(
    [Microsoft.Win32.RegistryHive]::LocalMachine,
    [Microsoft.Win32.RegistryView]::Registry32  # equivale a KEY_WOW64_32KEY
)

# Esempio pratico: confrontare un valore tra le due viste
$path = "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
$native = $reg.OpenSubKey($path)
$wow = $reg32.OpenSubKey($path)
Write-Host "Programmi nella vista 64-bit: $($native.SubKeyCount)"
Write-Host "Programmi nella vista 32-bit: $($wow.SubKeyCount)"
```

**Implicazioni pratiche:**

- **Installazione software**: un installer a 32 bit che scrive in `HKLM\SOFTWARE` vedrà i propri valori solo in WOW6432Node. Se un servizio a 64 bit cerca quei valori nel percorso nativo, non li troverà.
- **Script di automazione**: specificare sempre il flag di vista corretto quando si accede al Registry da script che potrebbero essere eseguiti sotto architetture diverse.
- **Forensics**: durante l'analisi di un hive offline, verificare sempre sia `SOFTWARE` che `SOFTWARE\WOW6432Node` per ottenere un inventario completo delle applicazioni installate e delle configurazioni.
- **reg.exe**: il comando `reg query` da un prompt a 32 bit (es. `%windir%\SysWOW64\cmd.exe`) accede automaticamente alla vista WOW6432Node. Usare `/reg:64` per forzare la vista nativa: `reg query HKLM\SOFTWARE\MyApp /reg:64`.

---

## Registry Remoto

Il servizio Remote Registry consente di leggere e modificare il Registry di un computer remoto.

### Abilitare il servizio

```powershell
# Verificare stato del servizio Remote Registry
Get-Service RemoteRegistry -ComputerName SERVER01

# Avviare e impostare avvio automatico
Set-Service -Name RemoteRegistry -StartupType Automatic -ComputerName SERVER01
Start-Service -Name RemoteRegistry -ComputerName SERVER01

# Abilitare il firewall per il traffico Remote Registry
# Sul computer remoto:
New-NetFirewallRule -DisplayName "Remote Registry" `
    -Direction Inbound -Protocol TCP -LocalPort 445 -Action Allow
```

### Accesso remoto con reg.exe

```cmd
:: Query su registry remoto
reg query "\\SERVER01\HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v ProductName

:: Modificare registry remoto
reg add "\\SERVER01\HKLM\SOFTWARE\MyCompany" /v Setting /t REG_SZ /d "value" /f

:: Esportare da registry remoto
reg export "\\SERVER01\HKLM\SOFTWARE\MyCompany" C:\Backup\server01-mycompany.reg
```

### Accesso remoto con PowerShell

```powershell
# Metodo 1: Invoke-Command (preferito — usa WinRM, non Remote Registry)
Invoke-Command -ComputerName SERVER01 -ScriptBlock {
    Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion" |
        Select-Object ProductName, CurrentBuild
}

# Metodo 2: API .NET (usa il servizio Remote Registry)
$remoteReg = [Microsoft.Win32.RegistryKey]::OpenRemoteBaseKey(
    [Microsoft.Win32.RegistryHive]::LocalMachine,
    "SERVER01"
)
$key = $remoteReg.OpenSubKey("SOFTWARE\Microsoft\Windows NT\CurrentVersion")
$key.GetValue("ProductName")
$key.Close()
$remoteReg.Close()

# Metodo 3: WMI/CIM
$regProv = Get-CimInstance -Namespace root\default -ClassName StdRegProv -ComputerName SERVER01
# Leggere valore stringa (HKLM = 2147483650)
Invoke-CimMethod -InputObject $regProv -MethodName GetStringValue -Arguments @{
    hDefKey     = [UInt32]2147483650
    sSubKeyName = "SOFTWARE\Microsoft\Windows NT\CurrentVersion"
    sValueName  = "ProductName"
}

# Metodo 4: PSDrive remoto (via sessione PS)
$session = New-PSSession -ComputerName SERVER01
Invoke-Command -Session $session -ScriptBlock {
    Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion" |
        Select-Object ProductName, CurrentBuild
}
Remove-PSSession $session
```

### Sicurezza del Registry Remoto

- **Principio del minimo privilegio:** limitare chi può accedere al Remote Registry.
- **Disabilitare se non necessario:** `Set-Service RemoteRegistry -StartupType Disabled`
- **Firewall:** limitare l'accesso alla porta 445 (SMB) solo alle subnet di gestione.
- **Chiave di restrizione:** `HKLM\SYSTEM\CurrentControlSet\Control\SecurePipeServers\winreg` — la DACL su questa chiave determina chi può connettersi al Remote Registry.
- **Preferire WinRM (Invoke-Command):** più sicuro, usa HTTPS (porta 5986), supporta Kerberos, non richiede il servizio Remote Registry.

```powershell
# Verificare chi ha accesso al Remote Registry
$acl = Get-Acl "HKLM:\SYSTEM\CurrentControlSet\Control\SecurePipeServers\winreg"
$acl.Access | Format-Table IdentityReference, RegistryRights, AccessControlType
```

---

## Backup e Ripristino

### Backup

```powershell
# Esportare chiave specifica in formato .reg (testo, importabile)
reg export "HKLM\SOFTWARE\MyCompany" C:\Backup\mycompany.reg

# Salvare hive in formato binario (più completo, include permessi e timestamp)
reg save HKLM\SYSTEM C:\Backup\system.hiv
reg save HKLM\SOFTWARE C:\Backup\software.hiv
reg save HKLM\SAM C:\Backup\sam.hiv
reg save HKLM\SECURITY C:\Backup\security.hiv
reg save HKU\.DEFAULT C:\Backup\default.hiv

# Backup completo di una chiave con PowerShell (XML serialization)
$path = "HKLM:\SYSTEM\CurrentControlSet\Services"
$backup = Get-ChildItem $path -Recurse
$backup | Export-Clixml "C:\Backup\services-registry.xml"

# Backup System State (include registry completo + Active Directory + boot files)
wbadmin start systemstatebackup -backupTarget:D:

# Backup hive manuale — copia file su disco (richiede privilegi SYSTEM o offline)
# Non è possibile copiare i file hive mentre Windows è in esecuzione (file locked)
# Opzioni: usare Volume Shadow Copy, backup da WinRE, o reg save

# Backup tramite Volume Shadow Copy (VSS)
$shadow = (Get-WmiObject Win32_ShadowCopy -List).Create("C:\","ClientAccessible")
$shadowPath = (Get-WmiObject Win32_ShadowCopy | Sort-Object InstallDate -Descending | Select-Object -First 1).DeviceObject
cmd /c "mklink /d C:\ShadowCopy ${shadowPath}\"
Copy-Item "C:\ShadowCopy\Windows\System32\config\*" "C:\Backup\Hives\" -Force
cmd /c "rmdir C:\ShadowCopy"
```

### Ripristino

```powershell
# Importare file .reg
reg import C:\Backup\mycompany.reg

# Ripristinare hive da file binario (la chiave deve essere chiudibile)
reg restore HKLM\SYSTEM C:\Backup\system.hiv

# In caso di sistema non avviabile:
# 1. Boot da WinRE o WinPE
# 2. Accedere a C:\Windows\System32\config\
# 3. Rinominare hive corrotto (es. SYSTEM → SYSTEM.bad)
# 4. Copiare hive dal backup o da RegBack (se disponibile)
# 5. copy C:\Windows\System32\config\RegBack\SYSTEM C:\Windows\System32\config\SYSTEM

# Caricare hive offline (per modifiche su sistema non avviabile)
reg load HKLM\OfflineSystem C:\Mounted\Windows\System32\config\SYSTEM
# Fare modifiche...
reg unload HKLM\OfflineSystem
```

### RegBack — Backup Automatico

Windows storicamente mantiene copie di backup degli hive in `C:\Windows\System32\config\RegBack\`.

**Importante (Windows 10 1803+):** Microsoft ha disabilitato il backup automatico degli hive in RegBack. La cartella esiste ma i file sono a 0 byte.

**Riabilitare RegBack (se necessario):**

```powershell
# Creare la chiave per riabilitare il backup automatico degli hive
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Configuration Manager" `
    -Name "EnablePeriodicBackup" -Value 1 -PropertyType DWord -Force
# Richiede riavvio. Il Task Scheduler eseguirà il task "RegIdleBackup"
# per copiare periodicamente gli hive in RegBack.
```

**Backup manuale degli hive in RegBack (script schedulato):**

```powershell
# Script da schedulare con Task Scheduler (es. settimanale)
$source = "C:\Windows\System32\config"
$dest   = "C:\Windows\System32\config\RegBack"

$hives = @("SAM", "SECURITY", "SOFTWARE", "SYSTEM", "DEFAULT")
foreach ($hive in $hives) {
    reg save "HKLM\$hive" "$dest\$hive" /y 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Impossibile eseguire backup di $hive (in uso)"
    }
}
# Nota: DEFAULT va caricato da HKU\.DEFAULT
reg save "HKU\.DEFAULT" "$dest\DEFAULT" /y 2>$null
```

### Automazione backup Registry con rotazione

Lo script manuale precedente funziona per backup occasionali, ma in ambienti di produzione è necessaria un'automazione con rotazione dei backup per evitare di esaurire lo spazio disco e garantire la disponibilità di punti di ripristino recenti.

```powershell
# Script di backup Registry automatizzato con rotazione a 7 giorni
# Salvare come: C:\Scripts\Backup-Registry.ps1

[CmdletBinding()]
param(
    [string]$BackupRoot = "D:\Backups\Registry",
    [int]$RetentionDays = 7,
    [string[]]$Hives = @("SAM", "SECURITY", "SOFTWARE", "SYSTEM")
)

$ErrorActionPreference = 'Stop'
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$backupDir = Join-Path $BackupRoot $timestamp

try {
    # Creare directory di backup
    New-Item -Path $backupDir -ItemType Directory -Force | Out-Null

    # Eseguire backup di ogni hive
    $results = foreach ($hive in $Hives) {
        $destFile = Join-Path $backupDir "$hive.hiv"
        $regResult = reg save "HKLM\$hive" $destFile /y 2>&1
        [PSCustomObject]@{
            Hive    = $hive
            File    = $destFile
            Size    = if (Test-Path $destFile) { (Get-Item $destFile).Length } else { 0 }
            Status  = if ($LASTEXITCODE -eq 0) { 'OK' } else { 'ERRORE' }
            Message = $regResult
        }
    }

    # Backup del profilo DEFAULT
    $defaultDest = Join-Path $backupDir "DEFAULT.hiv"
    reg save "HKU\.DEFAULT" $defaultDest /y 2>&1 | Out-Null

    # Log dei risultati
    $results | Format-Table -AutoSize | Out-String | Write-Host

    # Rotazione — eliminare backup più vecchi di $RetentionDays
    $cutoff = (Get-Date).AddDays(-$RetentionDays)
    Get-ChildItem $BackupRoot -Directory |
        Where-Object { $_.CreationTime -lt $cutoff } |
        ForEach-Object {
            Write-Host "Rotazione: eliminazione $($_.FullName)"
            Remove-Item $_.FullName -Recurse -Force
        }

    # Generare hash SHA256 per integrità
    Get-ChildItem $backupDir -Filter "*.hiv" | ForEach-Object {
        $hash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
        "$hash  $($_.Name)" | Out-File (Join-Path $backupDir "checksums.sha256") -Append
    }

    Write-Host "`nBackup completato: $backupDir"
    Write-Host "File di checksum: $backupDir\checksums.sha256"
}
catch {
    Write-Error "Backup fallito: $_"
    exit 1
}
```

```powershell
# Registrare come Scheduled Task per esecuzione giornaliera alle 02:00
$action  = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File C:\Scripts\Backup-Registry.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At "02:00"
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -RunLevel Highest
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
    -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries

Register-ScheduledTask -TaskName "RegistryBackup-Daily" `
    -Action $action -Trigger $trigger -Principal $principal `
    -Settings $settings -Description "Backup automatico hive Registry con rotazione 7 giorni"

# Verificare la task registrata
Get-ScheduledTask -TaskName "RegistryBackup-Daily" | Format-List TaskName, State, LastRunTime
```

**Verifica integrità e ripristino dal backup:**

```powershell
# Verificare checksum prima del ripristino
$checksumFile = "D:\Backups\Registry\2024-01-15_020000\checksums.sha256"
Get-Content $checksumFile | ForEach-Object {
    $parts = $_ -split '  '
    $expectedHash = $parts[0]
    $fileName = $parts[1]
    $filePath = Join-Path (Split-Path $checksumFile) $fileName
    $actualHash = (Get-FileHash $filePath -Algorithm SHA256).Hash
    [PSCustomObject]@{
        File   = $fileName
        Match  = $expectedHash -eq $actualHash
        Status = if ($expectedHash -eq $actualHash) { 'INTEGRO' } else { 'CORROTTO' }
    }
}

# Ripristinare un hive dal backup (richiede boot da WinRE o offline)
# reg restore HKLM\SOFTWARE "D:\Backups\Registry\2024-01-15_020000\SOFTWARE.hiv"
```

### System Restore e Registry

System Restore crea snapshot (punti di ripristino) che includono gli hive del Registry.

```powershell
# Creare un punto di ripristino prima di modifiche Registry
Checkpoint-Computer -Description "Prima di modifiche Registry" -RestorePointType MODIFY_SETTINGS

# Elencare punti di ripristino
Get-ComputerRestorePoint | Select-Object SequenceNumber, Description, CreationTime

# Il ripristino avviene solo dall'interfaccia di System Restore:
# Pannello di Controllo → Sistema → Protezione Sistema → Ripristino configurazione di sistema
# Oppure da WinRE → Risoluzione dei problemi → Opzioni avanzate → Ripristino configurazione di sistema
```

---

## Registry Defragmentation e Cleanup

### Registry bloat

Nel tempo, il Registry accumula dati residui:
- Chiavi orfane di software disinstallato
- Riferimenti a file e percorsi che non esistono più
- COM/CLSID registrazioni di oggetti COM non più presenti
- MRU (Most Recently Used) lists obsolete
- Cache di dati temporanei

### Compattazione degli Hive

Windows compatta automaticamente gli hive durante il boot (idle time), ma la compattazione non è sempre efficiente.

**Non esistono strumenti Microsoft ufficiali per la defragmentazione del Registry.** Gli strumenti di terze parti "registry cleaner" hanno storicamente causato più problemi di quanti ne risolvano. Microsoft sconsiglia il loro uso.

**Approccio raccomandato:**

```powershell
# 1. Pulizia manuale delle chiavi note come inutili

# Rimuovere voci di uninstall orfane
$uninstall = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
Get-ChildItem $uninstall | ForEach-Object {
    $props = Get-ItemProperty $_.PSPath
    if ($props.DisplayName -and $props.InstallLocation) {
        if (-not (Test-Path $props.InstallLocation)) {
            Write-Host "Orfano: $($props.DisplayName) → $($props.InstallLocation)"
            # Remove-Item $_.PSPath -Recurse  # Decommentare per rimuovere
        }
    }
}

# 2. Pulizia cache SharedDLLs (riferimenti a DLL inesistenti)
$sharedDlls = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\SharedDLLs"
$sharedDlls.PSObject.Properties | Where-Object { $_.Name -ne "PSPath" -and $_.Name -ne "PSParentPath" -and $_.Name -ne "PSChildName" -and $_.Name -ne "PSDrive" -and $_.Name -ne "PSProvider" } | ForEach-Object {
    if (-not (Test-Path $_.Name)) {
        Write-Host "DLL inesistente: $($_.Name)"
        # Remove-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\SharedDLLs" -Name $_.Name
    }
}

# 3. Pulizia profili utente orfani (utenti eliminati con profilo rimasto)
$profileList = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList"
Get-ChildItem $profileList | ForEach-Object {
    $props = Get-ItemProperty $_.PSPath
    if ($props.ProfileImagePath -and -not (Test-Path $props.ProfileImagePath)) {
        Write-Host "Profilo orfano: $($_.PSChildName) → $($props.ProfileImagePath)"
    }
}

# 4. Pulizia COM/DCOM registrazioni orfane
# (Operazione rischiosa — solo in ambiente lab o dopo backup completo)
```

### Riduzione dimensione hive

L'unico modo affidabile per compattare un hive è:

1. Esportare l'hive in formato `.reg` (`reg export`)
2. Eliminare il file hive (offline)
3. Reimportare il file `.reg`

Questo crea un file hive nuovo, senza frammentazione interna. In pratica, è raramente necessario perché la dimensione degli hive moderni (anche 200+ MB per SOFTWARE) non impatta significativamente le performance.

---

## Software Deployment via Registry

### Rilevamento installazione software

```powershell
# Le applicazioni registrate (MSI e molte non-MSI) appaiono in:
# HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\     → 64-bit
# HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\ → 32-bit
# HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\     → per utente

# Elencare tutto il software installato
$paths = @(
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*",
    "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*"
)
Get-ItemProperty $paths -ErrorAction SilentlyContinue |
    Where-Object { $_.DisplayName } |
    Select-Object DisplayName, DisplayVersion, Publisher, InstallDate, UninstallString |
    Sort-Object DisplayName
```

### Stringhe di disinstallazione

```powershell
# Trovare la stringa di disinstallazione di un programma
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*" |
    Where-Object { $_.DisplayName -like "*Chrome*" } |
    Select-Object DisplayName, UninstallString, QuietUninstallString

# Disinstallazione silenziosa — flag comuni:
# MSI:      msiexec /x {GUID} /qn /norestart
# NSIS:     "uninstall.exe" /S
# InnoSetup: "unins000.exe" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
# InstallShield: "setup.exe" -s -f1"response.iss"

# Esempio: disinstallare silenziosamente via MSI GUID dal Registry
$app = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*" |
    Where-Object { $_.DisplayName -like "*7-Zip*" }
if ($app.UninstallString -match '\{[A-F0-9\-]+\}') {
    $guid = $Matches[0]
    Start-Process msiexec.exe -ArgumentList "/x $guid /qn /norestart" -Wait
}
```

### Configurazione applicazioni via Registry

Molte applicazioni leggono configurazioni dal Registry. Distribuire impostazioni via GPO Preferences o script:

```powershell
# Esempio: configurare Chrome Enterprise via Registry
$chromePolicies = "HKLM:\SOFTWARE\Policies\Google\Chrome"
New-Item -Path $chromePolicies -Force | Out-Null

# Homepage
Set-ItemProperty -Path $chromePolicies -Name "HomepageLocation" -Value "https://intranet.contoso.com"
Set-ItemProperty -Path $chromePolicies -Name "HomepageIsNewTabPage" -Value 0

# Bloccare estensioni non approvate
New-ItemProperty -Path "$chromePolicies\ExtensionInstallBlocklist" -Name "1" -Value "*" -Force
# Permettere solo estensioni specifiche
New-ItemProperty -Path "$chromePolicies\ExtensionInstallAllowlist" -Name "1" `
    -Value "cjpalhdlnbpafiamejdnhcphjbkeiagm" -Force  # uBlock Origin

# Esempio: configurare Microsoft Edge
$edgePolicies = "HKLM:\SOFTWARE\Policies\Microsoft\Edge"
New-Item -Path $edgePolicies -Force | Out-Null
Set-ItemProperty -Path $edgePolicies -Name "DefaultSearchProviderEnabled" -Value 1
Set-ItemProperty -Path $edgePolicies -Name "PasswordManagerEnabled" -Value 0
```

---

## Registry Forensics

L'analisi forense del Registry è fondamentale nelle indagini di incident response, malware analysis e digital forensics. Il Registry contiene una quantità enorme di artefatti relativi all'attività dell'utente e del sistema.

### Last Write Time

Ogni chiave del Registry ha un timestamp "Last Write Time" con precisione di 100 nanosecondi (FILETIME), aggiornato a ogni modifica della chiave (non dei singoli valori). Questo è l'equivalente del timestamp `mtime` per i file.

```powershell
# Leggere il Last Write Time di una chiave (richiede P/Invoke o strumenti esterni)
# PowerShell nativo non espone questa informazione

# Metodo con .NET e reflection (funziona su Windows)
function Get-RegistryKeyLastWriteTime {
    param([string]$Path)

    $key = Get-Item $Path
    $timestamp = $key.GetType().GetMethod("get_LastWriteTime",
        [System.Reflection.BindingFlags]::NonPublic -bor
        [System.Reflection.BindingFlags]::Instance
    )
    if ($timestamp) {
        return $timestamp.Invoke($key, $null)
    }
    Write-Warning "LastWriteTime non disponibile tramite reflection in questa versione"
}

# Alternativa: usare reg.exe /v per vedere i timestamp
# (reg.exe non mostra i timestamp delle chiavi direttamente)

# Strumenti dedicati: RegRipper, Registry Explorer (Eric Zimmerman), RECmd
```

### Tracce Attività Utente

```
# Posizioni chiave per la forensica utente (tutte in HKCU / NTUSER.DAT):

# File recenti aperti
HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs\
# Sotto-chiavi per estensione: .docx, .pdf, .xlsx, ecc.
# Valori: binari con nome file e percorso (MRU encoded)

# Comandi dalla finestra "Esegui" (Win+R)
HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\RunMRU\
# MRUList indica l'ordine di utilizzo

# Percorsi digitati nella barra indirizzi di Explorer
HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths\
# url1, url2, url3, ... = percorsi digitati

# Dialoghi Apri/Salva — ultimo percorso usato
HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\ComDlg32\
├── LastVisitedPidlMRU\     → Ultima app e cartella usata
└── OpenSavePidlMRU\        → Ultimo percorso per tipo file

# Programmi eseguiti (UserAssist) — ROT13 encoded
HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\UserAssist\
├── {CEBFF5CD-...}\Count\   → Programmi GUI eseguiti
└── {F4E57C4B-...}\Count\   → Shortcut usati
# I nomi dei valori sono path ROT13. Decodificare con:
# "Cebterz Svyrf" → "Program Files" (ROT13)
# I dati contengono contatore esecuzioni e timestamp

# Connessioni RDP effettuate
HKCU\SOFTWARE\Microsoft\Terminal Server Client\
├── Default\               → MRU server RDP
└── Servers\<hostname>\    → Hint username per server

# Reti WiFi a cui l'utente si è connesso
HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\NetworkList\Profiles\
# GUID → nome rete, data prima e ultima connessione, tipo (privata/pubblica)

# Ricerche effettuate in Explorer
HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\WordWheelQuery\
# MRUListEx + valori numerici = ricerche in ordine cronologico

# Shellbags — cartelle visitate e preferenze visualizzazione
HKCU\SOFTWARE\Microsoft\Windows\Shell\BagMRU\
HKCU\SOFTWARE\Microsoft\Windows\Shell\Bags\
# Rivelano cartelle visitate anche se i file sono stati eliminati
```

### Cronologia USB

```
# Dispositivi USB collegati — traccia COMPLETA nel Registry

# 1. Tutti i dispositivi USB mai collegati
HKLM\SYSTEM\CurrentControlSet\Enum\USB\
# VID_xxxx&PID_yyyy → Vendor e Product ID
# Sotto-chiave con serial number del dispositivo

# 2. Storage USB (chiavette, dischi esterni)
HKLM\SYSTEM\CurrentControlSet\Enum\USBSTOR\
# Disk&Ven_<vendor>&Prod_<product>&Rev_<revision>\<serial>
# Proprietà includono: FriendlyName, prima installazione

# 3. Lettera di unità assegnata al dispositivo
HKLM\SYSTEM\MountedDevices\
# \DosDevices\E: → dati binari che contengono il serial number del dispositivo

# 4. Volume GUID assegnato
HKLM\SOFTWARE\Microsoft\Windows Portable Devices\Devices\
# Mappa device → friendly name

# 5. Timestamp di prima e ultima connessione
HKLM\SYSTEM\CurrentControlSet\Enum\USBSTOR\<device>\<serial>\Properties\
# {83da6326-97a6-4088-9453-a1923f573b29}\0064  → prima installazione
# {83da6326-97a6-4088-9453-a1923f573b29}\0066  → ultima connessione
# {83da6326-97a6-4088-9453-a1923f573b29}\0067  → ultima disconnessione

# 6. Ultimo utente a collegare il dispositivo
HKLM\SYSTEM\CurrentControlSet\Enum\USBSTOR\<device>\<serial>\Properties\
# {83da6326-97a6-4088-9453-a1923f573b29}\0006  → SID dell'utente
```

```powershell
# Script: elencare tutti i dispositivi USB Storage
Get-ChildItem "HKLM:\SYSTEM\CurrentControlSet\Enum\USBSTOR" -ErrorAction SilentlyContinue |
    ForEach-Object {
        $device = $_
        Get-ChildItem $device.PSPath | ForEach-Object {
            $serial = $_
            $props = Get-ItemProperty $serial.PSPath -ErrorAction SilentlyContinue
            [PSCustomObject]@{
                Device       = $device.PSChildName
                SerialNumber = $serial.PSChildName
                FriendlyName = $props.FriendlyName
            }
        }
    }
```

### Esecuzione Programmi

```
# Artefatti che provano l'esecuzione di un programma:

# 1. UserAssist (NTUSER.DAT) — programmi GUI con contatore e timestamp
HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\UserAssist\

# 2. MUICache — nomi di programmi eseguiti
HKCU\SOFTWARE\Classes\Local Settings\Software\Microsoft\Windows\Shell\MUICache\

# 3. AppCompatCache (ShimCache) — programmi che il sistema ha valutato per compatibilità
HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\AppCompatCache\
# Il valore "AppCompatCache" contiene dati binari: path, dimensione file, timestamp
# Attenzione: la presenza in ShimCache NON prova l'esecuzione, solo l'analisi di compatibilità

# 4. BAM/DAM (Background Activity Moderator) — Windows 10 1709+
HKLM\SYSTEM\CurrentControlSet\Services\bam\State\UserSettings\<SID>\
HKLM\SYSTEM\CurrentControlSet\Services\dam\State\UserSettings\<SID>\
# Path completo del programma → timestamp di ultima esecuzione

# 5. Prefetch è su filesystem (C:\Windows\Prefetch\) ma il Registry contiene:
HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters\
# EnablePrefetcher: 0=disabilitato, 1=app, 2=boot, 3=entrambi

# 6. AmCache — database dettagliato delle applicazioni
# File: C:\Windows\AppCompat\Programs\Amcache.hve (formato hive Registry)
# Contiene: hash SHA1, path, publisher, versione, timestamp prima esecuzione
```

```powershell
# Script: leggere BAM (Background Activity Moderator) per tracce di esecuzione
$bamPath = "HKLM:\SYSTEM\CurrentControlSet\Services\bam\State\UserSettings"
Get-ChildItem $bamPath -ErrorAction SilentlyContinue | ForEach-Object {
    $sid = $_.PSChildName
    $props = Get-ItemProperty $_.PSPath
    $props.PSObject.Properties |
        Where-Object { $_.Name -notlike "PS*" -and $_.Name -ne "Version" -and $_.Name -ne "SequenceNumber" } |
        ForEach-Object {
            # I dati contengono un FILETIME (8 byte) nei primi 8 byte
            $data = $_.Value
            if ($data -is [byte[]] -and $data.Length -ge 8) {
                $filetime = [BitConverter]::ToInt64($data, 0)
                $datetime = [DateTime]::FromFileTime($filetime)
                [PSCustomObject]@{
                    SID       = $sid
                    Program   = $_.Name
                    Timestamp = $datetime
                }
            }
        }
} | Sort-Object Timestamp -Descending | Select-Object -First 30
```

### Strumenti Forensi

| Strumento | Tipo | Descrizione |
|-----------|------|-------------|
| **Registry Explorer** (Eric Zimmerman) | GUI | Analisi forense completa con timestamp, bookmarks, ricerca avanzata |
| **RECmd** (Eric Zimmerman) | CLI | Batch processing di hive con plugin per artefatti specifici |
| **RegRipper** | CLI/GUI | Plugin-based, estrae artefatti automaticamente |
| **KAPE** (Kroll) | CLI | Raccolta e analisi automatizzata (include moduli Registry) |
| **Autopsy** | GUI | Suite forense completa con parser Registry |
| **FTK Imager** | GUI | Acquisizione forense, può estrarre file hive da immagini disco |
| **regedit** | GUI | Per analisi live (limitato, nessun timestamp) |

**Workflow forense tipico:**

1. Acquisire i file hive (da immagine disco o copia live via reg save)
2. Caricare in Registry Explorer o RegRipper
3. Analizzare per artefatti rilevanti (UserAssist, USBSTOR, RecentDocs, BAM, ShimCache)
4. Correlare timestamp tra artefatti diversi
5. Documentare le evidenze con timestamp UTC ISO 8601

---

## Troubleshooting

**"Accesso negato modificando una chiave"** → La chiave ha permessi restrittivi. Usare regedit → tasto destro → Permessi → avanzate → Cambia proprietario → aggiungere permessi. Attenzione: modificare permessi su chiavi di sistema può destabilizzare il sistema.

**"Modifica registry non ha effetto"** → Alcune modifiche richiedono riavvio del servizio o del sistema. Verificare che la chiave sia scritta nel punto corretto (32-bit vs 64-bit: `HKLM\SOFTWARE` vs `HKLM\SOFTWARE\WOW6432Node`). Verificare che una GPO non stia sovrascrivendo la modifica.

**"Sistema non si avvia dopo modifica registry"** → Boot in Safe Mode (F8 o Shift+Restart), ripristinare il backup .reg, oppure usare System Restore. Se non funziona: WinRE → Command Prompt → `reg restore` o copia da `RegBack`.

**"Registry corrotto (Event 10, WMI errors)"** → `winmgmt /verifyrepository`. Se corrotto: `winmgmt /salvagerepository` o `winmgmt /resetrepository` (ultimo resort, perso WMI custom).

**"Errore di permesso su chiave di sistema critica (es. HKLM\SAM)"** → Non modificare direttamente SAM o SECURITY. Usare gli strumenti appropriati: `lusrmgr.msc`, `secpol.msc`, `gpedit.msc`, o i cmdlet PowerShell (`Set-LocalUser`, `Set-LocalGroup`). Se assolutamente necessario l'accesso raw: `PsExec -s -i regedit` per eseguire regedit come SYSTEM.

**"GPO non applicata, registry non aggiornato"** → Diagnostica:

```powershell
# Forzare aggiornamento GPO
gpupdate /force

# Verificare risultato GPO
gpresult /r              # Riepilogo
gpresult /h gpreport.html  # Report HTML dettagliato

# Verificare che il valore sia nel path corretto
# Computer: HKLM\SOFTWARE\Policies\...
# User:     HKCU\SOFTWARE\Policies\...
reg query "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate"

# Verificare evento GPO nel log
Get-WinEvent -LogName "Microsoft-Windows-GroupPolicy/Operational" -MaxEvents 20

# Verificare che il computer sia nell'OU corretta
# Verificare WMI filter se presente
# Verificare Security Filtering (GPO applicata al gruppo corretto)
```

**"Hive corrotto — sistema non si avvia, anche Safe Mode fallisce"** →

```
1. Boot da Windows Recovery Environment (WinRE) o USB di installazione
2. Selezionare "Risoluzione dei problemi" → "Prompt dei comandi"
3. Identificare la lettera del disco Windows:
   > diskpart
   > list volume
   > exit
4. Verificare quale hive è corrotto:
   > dir C:\Windows\System32\config\
5. Rinominare l'hive corrotto:
   > ren C:\Windows\System32\config\SYSTEM C:\Windows\System32\config\SYSTEM.bad
6. Copiare il backup (se RegBack è stato abilitato):
   > copy C:\Windows\System32\config\RegBack\SYSTEM C:\Windows\System32\config\SYSTEM
7. Se RegBack non è disponibile, provare System Restore da WinRE
8. Se tutto fallisce: reinstallare Windows con opzione "Mantieni i miei file"
```

**"Conflitto tra policy locale e GPO di dominio"** → Le GPO di dominio hanno sempre precedenza sulla policy locale. Ordine di elaborazione: Locale → Sito → Dominio → OU. Per la diagnostica:

```powershell
# Vedere quale GPO sta impostando un valore specifico
gpresult /h gpreport.html
# Cercare nel report HTML la chiave specifica

# Vedere la Resultant Set of Policy (RSoP)
rsop.msc    # GUI

# Verificare se la modifica locale viene sovrascritta
# al prossimo ciclo di aggiornamento GPO (ogni 90-120 minuti)
```

**"Il servizio non si avvia dopo modifica registry"** → Se è stato modificato `HKLM\SYSTEM\CurrentControlSet\Services\<ServiceName>`:

```powershell
# Verificare i valori critici del servizio
Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\<ServiceName>" |
    Select-Object Start, Type, ImagePath, ObjectName, ErrorControl, DependOnService

# Start type: 0=Boot, 1=System, 2=Automatic, 3=Manual, 4=Disabled
# Type: 1=Kernel driver, 2=File system driver, 16=Win32OwnProcess, 32=Win32ShareProcess
# ErrorControl: 0=Ignore, 1=Normal, 2=Severe, 3=Critical

# Se il servizio è un driver e Start è stato cambiato a 4 (Disabled)
# per un driver critico, il sistema potrebbe non avviarsi.
# Boot in Safe Mode e ripristinare il valore Start.
```

**"File .reg non viene importato correttamente"** → Verificare:
- Prima riga: `Windows Registry Editor Version 5.00` (con riga vuota dopo)
- Encoding: UTF-16LE con BOM (se esportato da regedit) o ANSI
- Percorsi: nessuna abbreviazione (usare `HKEY_LOCAL_MACHINE` completo)
- Backslash: raddoppiati nei valori stringa (`C:\\Path\\File`)
- Permessi: eseguire come amministratore se si scrive in HKLM

**"Valore Registry torna al default dopo riavvio"** → Cause possibili:
- Una GPO sovrascrive il valore a ogni refresh (ogni 90-120 min)
- Un servizio o applicazione riscrive il valore all'avvio
- Il valore è in un hive volatile (HKLM\HARDWARE)
- Windows Defender o altro AV ripristina impostazioni di sicurezza

```powershell
# Identificare chi modifica il valore: abilitare auditing sulla chiave
# e controllare Event ID 4657 nel Security Log
```

**"Chiave registry non trovata, ma esiste in regedit"** → Potrebbe essere un problema 32-bit/64-bit. Applicazioni 32-bit su Windows 64-bit vedono `WOW6432Node` come `SOFTWARE`. Usare `/reg:64` o `/reg:32` con `reg.exe`.

**"Cannot load hive: Access denied durante reg load"** → Verificare che il processo sia elevato (admin). Verificare che il file hive non sia in uso (locked). Se è un NTUSER.DAT di un utente loggato, è locked — l'utente deve fare logout.

**"Errore 0x00000035 — reg query su computer remoto"** → Il servizio Remote Registry non è attivo, il firewall blocca la porta 445, o non ci sono permessi. Verificare:

```cmd
sc \\SERVER01 query RemoteRegistry
net use \\SERVER01\IPC$ /user:DOMAIN\admin
reg query "\\SERVER01\HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v ProductName
```

**"Dimensione hive SOFTWARE eccessiva (>300 MB)"** → Cause: molti profili di installazione residui, cache WMI compilate, assemblies .NET, registrazioni COM/DCOM orfane. Pulizia: disinstallare software inutilizzato, eseguire `Dism /Online /Cleanup-Image /StartComponentCleanup`, considerare la ricompattazione manuale dell'hive.

**"Errore 0xC0000218 — STATUS_CANNOT_LOAD_REGISTRY_FILE"** → Il sistema non riesce a caricare un hive critico al boot. Indica corruzione grave. Procedura: boot da WinRE, ripristinare da RegBack o System Restore. Se non disponibile: repair install.

**"REG_EXPAND_SZ non espande le variabili d'ambiente"** → Verificare che il tipo sia effettivamente `REG_EXPAND_SZ` e non `REG_SZ`. In PowerShell:

```powershell
# Verificare il tipo di un valore
$key = Get-Item "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
$key.GetValueKind("Path")   # dovrebbe restituire "ExpandString"
```

**"MUI Error — UI corrotta dopo modifica Registry"** → Ripristinare la chiave modificata dal backup. Se non disponibile: `sfc /scannow` da prompt amministrativo, oppure `DISM /Online /Cleanup-Image /RestoreHealth`.

**"Task Scheduler non funziona dopo modifica ai servizi"** → Verificare che il servizio `Schedule` sia impostato su Start=2 (Automatic) e che le sue dipendenze siano intatte:

```powershell
Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\Schedule" |
    Select-Object Start, DependOnService, ImagePath
```

**"Performance degradate dopo modifica Registry networking"** → Ripristinare i valori TCP/IP ai default:

```cmd
netsh int ip reset
netsh int tcp reset
netsh winsock reset
:: Riavvio richiesto
```

---

## Best Practices

1. **Backup SEMPRE prima di modificare**: `reg export` della chiave specifica prima di ogni modifica. Salvare il file con timestamp nel nome: `reg export "HKLM\SOFTWARE\MyCompany" C:\Backup\mycompany_2026-05-22.reg`
2. **Documentare ogni modifica**: cosa è stato cambiato, perché, da chi, quando, come ripristinare. Mantenere un registro delle modifiche.
3. **Preferire GPO**: se una modifica può essere fatta via GPO, usare GPO anziché modifiche registry dirette. Le GPO sono documentate, reversibili e centralizzate.
4. **Non modificare SAM e SECURITY direttamente**: usare gli strumenti appropriati (Local Security Policy, GPO).
5. **Testare in ambiente lab**: ogni modifica registry su macchine di test prima della produzione.
6. **Usare paths completi**: evitare abbreviazioni, specificare sempre il path registry completo.
7. **Attenzione ai permessi**: alcune chiavi richiedono ownership change prima di poter essere modificate.
8. **Creare un punto di ripristino**: `Checkpoint-Computer -Description "Motivo"` prima di modifiche significative.
9. **Verificare 32-bit vs 64-bit**: su Windows 64-bit, le app 32-bit leggono da `WOW6432Node`. Specificare `/reg:64` o `/reg:32` quando necessario.
10. **Non usare registry cleaner di terze parti**: Microsoft sconsiglia il loro uso. Causano più problemi di quanti ne risolvano.
11. **Monitorare le modifiche critiche**: abilitare auditing sulle chiavi sensibili (sicurezza, servizi, startup).
12. **Automatizzare con script versionati**: tenere gli script di modifica Registry in un repository Git, con commenti che spieghino ogni modifica.
13. **Verificare dopo la modifica**: rileggere il valore dopo averlo scritto per confermare che la modifica è andata a buon fine.
14. **Attenzione al tipo di dato**: `REG_SZ` vs `REG_EXPAND_SZ`, `REG_DWORD` vs `REG_QWORD`. Il tipo sbagliato può causare comportamenti imprevisti.

---

## FAQ

**Q1: Qual è la differenza tra `reg export` e `reg save`?**
`reg export` crea un file `.reg` in formato testo (leggibile, importabile con `reg import` o doppio clic). `reg save` crea una copia binaria dell'hive (include permessi e timestamp, ripristinabile con `reg restore`). Per backup completo di un hive intero, usare `reg save`. Per backup di una singola chiave, `reg export`.

**Q2: Posso modificare il Registry di un altro utente senza che sia loggato?**
Sì. Caricare il suo NTUSER.DAT con `reg load HKU\TempUser "C:\Users\<user>\NTUSER.DAT"`, fare le modifiche, poi `reg unload HKU\TempUser`. L'utente non deve essere loggato (altrimenti il file è locked).

**Q3: Come trovo quale GPO sta sovrascrivendo la mia modifica Registry?**
`gpresult /h report.html` genera un report completo. Cercare la chiave specifica nel report. In alternativa: `rsop.msc` per una vista interattiva. Controllare anche i log: `Get-WinEvent -LogName "Microsoft-Windows-GroupPolicy/Operational"`.

**Q4: È sicuro eliminare chiavi in HKCR?**
HKCR è una vista merged di HKLM\SOFTWARE\Classes e HKCU\SOFTWARE\Classes. Eliminare in HKCR potrebbe eliminare l'associazione file per tutti gli utenti (se la chiave è in HKLM). Modificare preferibilmente HKCU\SOFTWARE\Classes per cambiamenti per utente.

**Q5: Come disabilitare un servizio Windows tramite Registry?**
Impostare `Start` a `4` (Disabled) in `HKLM\SYSTEM\CurrentControlSet\Services\<ServiceName>`. Attenzione: disabilitare servizi critici (RpcSs, Winmgmt, EventLog) può rendere il sistema instabile o non avviabile. Preferire `Set-Service -Name <name> -StartupType Disabled`.

**Q6: Perché alcune chiavi mostrano "(Valore non impostato)" come valore predefinito?**
Ogni chiave ha un valore predefinito (senza nome, mostrato come `(Default)`). Se nessun dato è stato assegnato, appare come "(Valore non impostato)". Questo è normale e non indica un problema.

**Q7: Come ripristinare le associazioni file predefinite?**
In Impostazioni → App → App predefinite → Ripristina. Via Registry: eliminare la chiave specifica in `HKCU\SOFTWARE\Classes\<.estensione>` per ripristinare il default di sistema (HKLM).

**Q8: Il Registry è thread-safe?**
Sì. Le API del Registry Windows sono thread-safe. Il Configuration Manager usa lock interni per garantire la coerenza. Tuttavia, se due processi scrivono lo stesso valore contemporaneamente, il risultato dipende dall'ordine di esecuzione (race condition logica, non corruzione).

**Q9: Quanto può essere grande un hive?**
Il limite teorico è 2 GB per hive (4 GB su sistemi molto recenti). In pratica, un hive SOFTWARE oltre i 300-500 MB indica bloat significativo. L'hive SAM è tipicamente pochi MB. L'hive SYSTEM è tipicamente 10-40 MB.

**Q10: Come eseguire regedit come SYSTEM per accedere a SAM/SECURITY?**
`PsExec -s -i regedit` (richiede PsExec di Sysinternals). Questo esegue regedit nel contesto dell'account SYSTEM, che ha accesso completo a SAM e SECURITY.

**Q11: Posso versionare il Registry con Git?**
Non direttamente. Si possono esportare chiavi in formato `.reg` (testo) e versionare i file `.reg`. Approccio consigliato: mantenere un repository di file `.reg` con le configurazioni standard dell'organizzazione.

**Q12: Come trovare quale processo sta scrivendo in una chiave specifica?**
Abilitare l'auditing sulla chiave (SACL) e controllare Event ID 4657 nel Security Log. In alternativa, Process Monitor (Sysinternals) con filtro "Operation is RegSetValue" e "Path contains <chiave>".

**Q13: Qual è la differenza tra CurrentControlSet e ControlSet001?**
`CurrentControlSet` è un link simbolico al ControlSet attivo (indicato da `HKLM\SYSTEM\Select\Current`). `ControlSet001` e `ControlSet002` sono i control set reali. Windows ne usa uno e tiene l'altro come backup (Last Known Good). Non modificare mai ControlSet001/002 direttamente — usare sempre CurrentControlSet.

**Q14: Come impedire agli utenti di eseguire regedit?**
Via GPO: User Configuration → Administrative Templates → System → "Prevent access to registry editing tools" = Enabled. Questo imposta `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\DisableRegistryTools` a 1. Non blocca `reg.exe` o PowerShell — solo l'interfaccia grafica di regedit.

**Q15: Il Registry viene incluso nei backup di Windows Server Backup?**
Sì, se si esegue un backup System State (`wbadmin start systemstatebackup`). Un backup bare-metal o un backup del volume di sistema include anch'esso il Registry. I backup solo di cartelle/file NON includono il Registry.

**Q16: Come monitorare le modifiche al Registry in tempo reale?**
Process Monitor (Sysinternals) con filtro sulle operazioni Registry (`RegSetValue`, `RegCreateKey`, `RegDeleteKey`). Per monitoring continuo: usare l'API `RegNotifyChangeKeyValue` o uno script PowerShell con FileSystemWatcher sull'evento WMI `RegistryValueChangeEvent`.

**Q17: NTUSER.DAT vs UsrClass.dat — qual è la differenza?**
`NTUSER.DAT` contiene la maggior parte delle impostazioni utente (HKCU). `UsrClass.dat` (in `AppData\Local\Microsoft\Windows\`) contiene `HKCU\SOFTWARE\Classes` — registrazioni COM e associazioni file per l'utente. Sono due hive separati, entrambi caricati al login dell'utente.

---

## Tabella di Riferimento — 50+ Chiavi Utili per Sysadmin

### Informazioni sistema

| # | Chiave | Valore | Descrizione |
|---|--------|--------|-------------|
| 1 | `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion` | `ProductName` | Nome del sistema operativo |
| 2 | `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion` | `CurrentBuild` | Numero build corrente |
| 3 | `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion` | `EditionID` | Edizione (Pro, Enterprise, ecc.) |
| 4 | `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion` | `InstallDate` | Data di installazione (Unix epoch) |
| 5 | `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion` | `RegisteredOrganization` | Organizzazione registrata |
| 6 | `HKLM\SYSTEM\CurrentControlSet\Control\ComputerName\ComputerName` | `ComputerName` | Nome del computer |
| 7 | `HKLM\SYSTEM\CurrentControlSet\Control\TimeZoneInformation` | `TimeZoneKeyName` | Fuso orario configurato |

### Startup e servizi

| # | Chiave | Valore | Descrizione |
|---|--------|--------|-------------|
| 8 | `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run` | (vari) | Programmi autostart (tutti gli utenti) |
| 9 | `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run` | (vari) | Programmi autostart (utente corrente) |
| 10 | `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce` | (vari) | Esecuzione singola al prossimo boot |
| 11 | `HKLM\SYSTEM\CurrentControlSet\Services\<name>` | `Start` | Tipo avvio servizio (0-4) |
| 12 | `HKLM\SYSTEM\CurrentControlSet\Services\<name>` | `ImagePath` | Percorso eseguibile del servizio |
| 13 | `HKLM\SYSTEM\CurrentControlSet\Control\SafeBoot\Minimal` | (sotto-chiavi) | Servizi avviati in Safe Mode Minimal |
| 14 | `HKLM\SYSTEM\CurrentControlSet\Control\SafeBoot\Network` | (sotto-chiavi) | Servizi avviati in Safe Mode with Networking |

### Software installato

| # | Chiave | Valore | Descrizione |
|---|--------|--------|-------------|
| 15 | `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*` | `DisplayName` | Nome software installato |
| 16 | `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*` | `DisplayVersion` | Versione installata |
| 17 | `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*` | `UninstallString` | Comando di disinstallazione |
| 18 | `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*` | `InstallDate` | Data di installazione (YYYYMMDD) |
| 19 | `HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*` | `DisplayName` | Software 32-bit su Windows 64-bit |
| 20 | `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\*` | `(Default)` | Percorso applicazioni (per Run dialog) |

### Rete

| # | Chiave | Valore | Descrizione |
|---|--------|--------|-------------|
| 21 | `HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters` | `Hostname` | Nome host TCP/IP |
| 22 | `HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters` | `Domain` | Suffisso DNS primario |
| 23 | `HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters` | `SearchList` | Lista suffissi DNS |
| 24 | `HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\<GUID>` | `DhcpIPAddress` | Indirizzo IP DHCP |
| 25 | `HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\<GUID>` | `DhcpNameServer` | DNS server DHCP |
| 26 | `HKLM\SYSTEM\CurrentControlSet\Services\Tcpip6\Parameters` | `DisabledComponents` | Componenti IPv6 disabilitati |
| 27 | `HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters` | `SMB1` | SMBv1 abilitato (0=no, 1=sì) |
| 28 | `HKLM\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient` | `EnableMulticast` | LLMNR abilitato (0=no) |

### Sicurezza

| # | Chiave | Valore | Descrizione |
|---|--------|--------|-------------|
| 29 | `HKLM\SYSTEM\CurrentControlSet\Control\Lsa` | `NoLMHash` | Disabilita LM hash (1=sì) |
| 30 | `HKLM\SYSTEM\CurrentControlSet\Control\Lsa` | `LmCompatibilityLevel` | Livello NTLMv2 (0-5) |
| 31 | `HKLM\SYSTEM\CurrentControlSet\Control\Lsa` | `RunAsPPL` | LSA Protection (1=abilitata) |
| 32 | `HKLM\SYSTEM\CurrentControlSet\Control\SecurityProviders\WDigest` | `UseLogonCredential` | WDigest cleartext (0=disabilitato) |
| 33 | `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon` | `CachedLogonsCount` | Credenziali cached (0-50) |
| 34 | `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System` | `EnableLUA` | UAC abilitato (1=sì) |
| 35 | `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System` | `ConsentPromptBehaviorAdmin` | Comportamento UAC admin (0-5) |
| 36 | `HKLM\SOFTWARE\Policies\Microsoft\Windows\PowerShell` | `EnableScripts` | Esecuzione script PS abilitata |
| 37 | `HKLM\SOFTWARE\Microsoft\Windows Script Host\Settings` | `Enabled` | WSH abilitato (0=disabilitato) |

### Desktop e Explorer

| # | Chiave | Valore | Descrizione |
|---|--------|--------|-------------|
| 38 | `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced` | `HideFileExt` | Nascondere estensioni (0=mostra) |
| 39 | `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced` | `Hidden` | Mostra file nascosti (1=sì) |
| 40 | `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced` | `LaunchTo` | Aprire Explorer su: 1=Questo PC, 2=Accesso rapido |
| 41 | `HKCU\Control Panel\Desktop` | `MenuShowDelay` | Ritardo menu (ms, 0=istantaneo) |
| 42 | `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize` | `AppsUseLightTheme` | Tema chiaro per app (0=scuro) |
| 43 | `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Themes\Personalize` | `SystemUsesLightTheme` | Tema chiaro per sistema (0=scuro) |

### Windows Update

| # | Chiave | Valore | Descrizione |
|---|--------|--------|-------------|
| 44 | `HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU` | `AUOptions` | Modalità aggiornamento (1-4) |
| 45 | `HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate` | `WUServer` | URL server WSUS |
| 46 | `HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate` | `DeferFeatureUpdatesPeriodInDays` | Giorni differimento feature updates |
| 47 | `HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate` | `DeferQualityUpdatesPeriodInDays` | Giorni differimento quality updates |

### Remote Desktop

| # | Chiave | Valore | Descrizione |
|---|--------|--------|-------------|
| 48 | `HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server` | `fDenyTSConnections` | RDP disabilitato (0=abilitato) |
| 49 | `HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp` | `PortNumber` | Porta RDP (default 3389) |
| 50 | `HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp` | `UserAuthentication` | NLA richiesto (1=sì) |

### Profili utente e logon

| # | Chiave | Valore | Descrizione |
|---|--------|--------|-------------|
| 51 | `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\<SID>` | `ProfileImagePath` | Percorso profilo utente |
| 52 | `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon` | `DefaultUserName` | Ultimo utente che ha fatto login |
| 53 | `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon` | `AutoAdminLogon` | Login automatico (1=abilitato) |
| 54 | `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon` | `Shell` | Shell predefinita (default: explorer.exe) |

### Performance e filesystem

| # | Chiave | Valore | Descrizione |
|---|--------|--------|-------------|
| 55 | `HKLM\SYSTEM\CurrentControlSet\Control\FileSystem` | `NtfsDisableLastAccessUpdate` | Disabilita LAT NTFS |
| 56 | `HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management` | `ClearPageFileAtShutdown` | Pulisci pagefile allo shutdown |
| 57 | `HKLM\SYSTEM\CurrentControlSet\Control\PriorityControl` | `Win32PrioritySeparation` | Priorità processi foreground |
| 58 | `HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management\PrefetchParameters` | `EnablePrefetcher` | Prefetcher (0-3) |
| 59 | `HKLM\SYSTEM\CurrentControlSet\Control` | `WaitToKillServiceTimeout` | Timeout kill servizi allo shutdown (ms) |

### Forensics

| # | Chiave | Valore | Descrizione |
|---|--------|--------|-------------|
| 60 | `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\UserAssist` | (sotto-chiavi) | Programmi eseguiti (ROT13) |
| 61 | `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\RecentDocs` | (sotto-chiavi) | File recenti |
| 62 | `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\RunMRU` | (sotto-chiavi) | Comandi Run (Win+R) |
| 63 | `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\TypedPaths` | (sotto-chiavi) | Percorsi digitati in Explorer |
| 64 | `HKLM\SYSTEM\CurrentControlSet\Enum\USBSTOR` | (sotto-chiavi) | Dispositivi USB Storage collegati |
| 65 | `HKLM\SYSTEM\CurrentControlSet\Services\bam\State\UserSettings\<SID>` | (sotto-chiavi) | Programmi eseguiti (BAM, Win10 1709+) |
| 66 | `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\NetworkList\Profiles` | (sotto-chiavi) | Reti connesse storiche |
| 67 | `HKCU\SOFTWARE\Microsoft\Terminal Server Client\Default` | (sotto-chiavi) | Server RDP recenti |

---

## Esercizi

### Esercizio 1 — Concettuale: Architettura hive e file fisici

Descrivi la relazione tra le 5 root key del Registry e i file hive su disco. Spiega il ruolo dei transaction log (`.LOG1`, `.LOG2`) nella protezione contro la corruzione. Cosa accade durante il boot se un hive è "dirty"?

### Esercizio 2 — Lab: Backup, modifica e rollback del Registry

1. Esportare il ramo `HKLM\SOFTWARE\Policies` con `reg export`.
2. Creare una chiave di test con `New-Item` e un valore DWORD con `Set-ItemProperty`.
3. Verificare la modifica con `Get-ItemProperty`.
4. Ripristinare il backup con `reg import`.
5. Verificare che la chiave di test sia stata rimossa.

### Esercizio 3 — Scenario: GPO non si riflette nel Registry

Un amministratore ha configurato una GPO per disabilitare la webcam su tutte le workstation, ma la policy non ha effetto. Usando la mappatura GPO → Registry, identifica la chiave attesa, verifica con `gpresult /h` se la policy è applicata, controlla il valore nel Registry con `reg query`, e diagnostica la discrepanza (conflitto di precedenza, security filtering, WMI filter).

### Esercizio 4 — Design: Strategia di auditing Registry per un SOC

Progetta una strategia di monitoraggio del Registry per un Security Operations Center. Identifica le chiavi critiche da monitorare (Run, RunOnce, Services, Winlogon, Image File Execution Options), configura le SACL appropriate, definisci gli Event ID da raccogliere (4657, 4663) e specifica le regole di alerting per modifiche sospette indicative di persistenza malware.

---

## Auto-valutazione

<details>
<summary>1. Quali sono le 5 root key del Registry e cosa contiene ciascuna?</summary>

**HKLM (HKEY_LOCAL_MACHINE):** configurazione hardware e software per tutto il sistema. **HKCU (HKEY_CURRENT_USER):** impostazioni dell'utente corrente. **HKU (HKEY_USERS):** profili di tutti gli utenti caricati (HKCU è un alias del SID corrente in HKU). **HKCR (HKEY_CLASSES_ROOT):** associazioni file e registrazioni COM — merge di HKLM\SOFTWARE\Classes e HKCU\SOFTWARE\Classes. **HKCC (HKEY_CURRENT_CONFIG):** profilo hardware corrente (alias di HKLM\SYSTEM\CurrentControlSet\Hardware Profiles\Current).
</details>

<details>
<summary>2. Dove si trovano fisicamente i file hive su disco?</summary>

I file hive principali sono in `C:\Windows\System32\config\`: SAM, SECURITY, SOFTWARE, SYSTEM, DEFAULT. L'hive NTUSER.DAT di ciascun utente è in `C:\Users\<utente>\NTUSER.DAT`. Ogni hive ha transaction log associati (`.LOG1`, `.LOG2`) per la protezione contro la corruzione e recovery atomico.
</details>

<details>
<summary>3. Qual è la differenza tra reg.exe, regedit e PowerShell per la modifica del Registry?</summary>

**regedit:** GUI interattiva, utile per esplorazione e modifica manuale. **reg.exe:** CLI nativa, utilizzabile in script batch e CMD, supporta `query`, `add`, `delete`, `export`, `import`. **PowerShell:** provider `Registry::` con cmdlet `Get-Item`, `Set-ItemProperty`, `New-Item` — più potente per automazione, scripting e integrazione con pipeline.
</details>

<details>
<summary>4. Come funziona la virtualizzazione del Registry in Windows?</summary>

La virtualizzazione del Registry reindirizza le scritture di applicazioni legacy (non UAC-aware) da `HKLM\SOFTWARE` a `HKCU\Software\Classes\VirtualStore\Machine\SOFTWARE`. Questo permette alle applicazioni che non hanno privilegi di amministratore di funzionare senza errori di accesso. È un meccanismo di compatibilità, non di sicurezza.
</details>

<details>
<summary>5. Come si configura l'auditing sulle chiavi di Registry?</summary>

1. Abilitare la policy "Audit Object Access" (o la subcategory "Audit Registry") in GPO. 2. Applicare una SACL sulla chiave specifica: regedit → tasto destro → Permissions → Advanced → Auditing → aggiungere entry per gli utenti/gruppi e le operazioni da monitorare (Set Value, Create Subkey, Delete). 3. Gli eventi vengono registrati nel Security log con Event ID 4657 (modifica valore) e 4663 (accesso a oggetto).
</details>

<details>
<summary>6. Quali chiavi di Registry sono critiche per la forensica di un sistema compromesso?</summary>

**Persistenza:** `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run`, `RunOnce`, `HKCU` equivalenti, `Winlogon\Shell`, `Image File Execution Options`. **Attività utente:** `UserAssist` (programmi eseguiti, ROT13), `RecentDocs`, `TypedPaths`, `RunMRU`. **Dispositivi:** `HKLM\SYSTEM\CurrentControlSet\Enum\USBSTOR`. **Rete:** `NetworkList\Profiles` (reti connesse). **Servizi:** `HKLM\SYSTEM\CurrentControlSet\Services` (servizi installati, inclusi potenziali backdoor).
</details>

<details>
<summary>7. Come le Group Policy modificano il Registry e qual è la precedenza?</summary>

Le GPO scrivono valori nel Registry sotto `HKLM\SOFTWARE\Policies\` (computer) e `HKCU\SOFTWARE\Policies\` (utente). Queste chiavi hanno precedenza sulle impostazioni equivalenti in `HKLM\SOFTWARE\` e `HKCU\SOFTWARE\`. La precedenza GPO segue LSDOU (Local → Site → Domain → OU). Le policy "Preferences" scrivono nelle chiavi native (non sotto `\Policies\`) e possono essere sovrascritte dall'utente.
</details>

---

## Letture primarie consigliate

- Microsoft Learn — Windows Registry. https://learn.microsoft.com/en-us/windows/win32/sysinfo/registry (consultato: 2026-05-23)
- Microsoft Learn — Registry Hives. https://learn.microsoft.com/en-us/windows/win32/sysinfo/registry-hives (consultato: 2026-05-23)
- Microsoft Learn — reg.exe Reference. https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/reg (consultato: 2026-05-23)
- Microsoft Learn — PowerShell Registry Provider. https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_registry_provider (consultato: 2026-05-23)
- SANS DFIR — Windows Registry Forensics. https://www.sans.org/blog/registry-analysis/ (consultato: 2026-05-23)

---

## Collegamenti incrociati

| Modulo | Relazione con questo capitolo |
|---|---|
| [02-powershell.md](02-powershell.md) | PowerShell — provider Registry, cmdlet per automazione query e modifica |
| [05-sicurezza-windows.md](05-sicurezza-windows.md) | Sicurezza — ACL, auditing, hardening delle chiavi di Registry |
| [21-group-policy-guida-completa.md](21-group-policy-guida-completa.md) | GPO — mappatura policy → chiavi Registry, precedenza LSDOU |
| [16-profili-e-servizi.md](16-profili-e-servizi.md) | Profili utente — NTUSER.DAT, caricamento hive, profili temporanei |
| [19-troubleshooting.md](19-troubleshooting.md) | Troubleshooting — diagnosi problemi Registry, profili corrotti, boot failure |

---

## Glossario locale

| Termine | Definizione |
|---|---|
| **Hive** | File fisico su disco che contiene un albero di chiavi e valori del Registry. I principali: SAM, SECURITY, SOFTWARE, SYSTEM, NTUSER.DAT. |
| **Root Key** | Le 5 chiavi radice del Registry: HKLM, HKCU, HKU, HKCR, HKCC. HKCR e HKCC sono alias (viste composite) di sotto-chiavi di HKLM. |
| **DWORD** | Tipo di valore Registry a 32 bit (4 byte). Usato per flag booleani (0/1), contatori e configurazioni numeriche. |
| **REG_SZ** | Tipo di valore Registry per stringhe di testo a terminazione nulla. Variante espandibile: `REG_EXPAND_SZ` (supporta variabili d'ambiente come `%SystemRoot%`). |
| **REG_MULTI_SZ** | Tipo di valore Registry per array di stringhe, separate da null e terminate da doppio null. Usato per elenchi (es. dipendenze servizi). |
| **Transaction Log** | File `.LOG1` e `.LOG2` associati a ogni hive, che registrano le operazioni di scrittura prima del commit. Permettono il recovery atomico in caso di crash. |
| **NTUSER.DAT** | File hive che contiene il ramo HKCU di un utente specifico. Ubicazione: `C:\Users\<utente>\NTUSER.DAT`. Caricato al logon, scaricato al logoff. |
| **Registry Virtualization** | Meccanismo UAC che reindirizza le scritture di app legacy da HKLM a HKCU\VirtualStore, permettendo il funzionamento senza privilegi admin. |
| **SACL** | System Access Control List. Lista di controllo che definisce quali operazioni su un oggetto (chiave Registry) generano eventi di audit nel Security log. |
| **CurrentControlSet** | Alias che punta al ControlSet attualmente in uso dal sistema (tipicamente ControlSet001). Contiene configurazioni di servizi, driver, hardware e rete. |
