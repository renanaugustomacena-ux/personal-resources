# Group Policy Objects (GPO) — Guida Approfondita

> **Modulo 21** · **Aggiornamento:** 2026-05-23

| Campo | Valore |
|---|---|
| **Modulo del corso** | Windows per ingegneri di sistema |
| **Fase** | Gestione centralizzata e hardening |
| **Modulo** | 21 — Group Policy Objects |
| **Versioni di riferimento** | Windows Server 2022 (21H2), Windows Server 2025, Windows 11 24H2, GPMC 6.3+, RSAT 1.0+, Intune 2405+ |
| **Livello** | Proficient (avanzato) |
| **Prerequisiti** | Active Directory (→ `01-active-directory.md`), registro di sistema (→ `04-registro-sistema.md`), PowerShell base (→ `02-powershell.md`), networking TCP/IP e DNS |
| **Obiettivi di apprendimento** | 1) Descrivere l'architettura GPC/GPT e il ciclo di elaborazione LSDOU con enforcement e block inheritance · 2) Configurare Security Filtering post-MS16-072 garantendo il permesso Read per gli account computer · 3) Progettare e pubblicare template ADMX personalizzati nel Central Store, gestendo conflitti di namespace tra versioni 2019/2022/Intune · 4) Leggere un report `gpresult /h` identificando il GPO vincente, i GPO negati e i tempi di elaborazione per CSE · 5) Implementare Loopback Processing (Replace e Merge) per scenari kiosk e RDS · 6) Configurare Advanced Audit Policy con subcategorie, SACL e `auditpol.exe` · 7) Eseguire backup, import cross-dominio e migrazione di GPO con migration tables · 8) Mappare policy ADMX su Intune tramite ADMX ingestion e OMA-URI |
| **Tempo stimato** | 18–26 ore (studio + esercizi + laboratorio) |
| **Ultimo aggiornamento** | 2026-05-23 |

## Idee guida
1. **ADMX 2019/2022/Intune mapping: feature parity tracking.**
2. **MS16-072 user-policy impact: BG settings break dopo patch.**
3. **`gpresult /h <file.html>` triage applicato.**
4. **Loopback processing per terminal server scenarios.**

### Mappa Concettuale

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                   GROUP POLICY OBJECTS — ARCHITETTURA E FLUSSO                  │
├──────────────────┬──────────────────┬───────────────────┬──────────────────────┤
│  COMPONENTI      │ ELABORAZIONE     │  FILTERING        │  STRUMENTI           │
│                  │                  │                   │                      │
│ ┌──────────────┐ │ ┌──────────────┐ │ ┌───────────────┐ │ ┌────────────────┐   │
│ │ GPC (LDAP)   │ │ │ LSDOU Order  │ │ │ Security      │ │ │ GPMC           │   │
│ │ GPT (SYSVOL) │ │ │ L→S→D→OU    │ │ │ Filtering     │ │ │ gpresult /h    │   │
│ └──────────────┘ │ ├──────────────┤ │ │ (MS16-072)    │ │ ├────────────────┤   │
│ ┌──────────────┐ │ │ Link Order   │ │ ├───────────────┤ │ │ RSoP           │   │
│ │ CSE (DLL)    │ │ │ Enforced     │ │ │ WMI Filters   │ │ │ Planning Mode  │   │
│ │ - Registry   │ │ │ Block Inh.   │ │ │ (WQL queries) │ │ ├────────────────┤   │
│ │ - Security   │ │ ├──────────────┤ │ ├───────────────┤ │ │ PowerShell     │   │
│ │ - Scripts    │ │ │ Loopback     │ │ │ Item-Level    │ │ │ GroupPolicy    │   │
│ │ - GP Prefs   │ │ │ Replace/Merge│ │ │ Targeting     │ │ │ Module         │   │
│ │ - Folder Red.│ │ │              │ │ │ (Preferences) │ │ │                │   │
│ └──────────────┘ │ └──────────────┘ │ └───────────────┘ │ └────────────────┘   │
├──────────────────┴──────────────────┴───────────────────┴──────────────────────┤
│  ADMX/ADML: Central Store │ Local Store │ Versioning 2019/2022/W11 │ Custom    │
├───────────────────────────────────────────────────────────────────────────────┤
│  INTUNE: Group Policy Analytics │ ADMX Ingestion │ OMA-URI │ MDM wins over GP │
├───────────────────────────────────────────────────────────────────────────────┤
│  SECURITY: CIS Benchmarks │ MS SCT Baselines │ Advanced Audit Policy │ SACL   │
├───────────────────────────────────────────────────────────────────────────────┤
│  BACKUP: Backup-GPO │ Import-GPO │ Migration Tables │ AGPM │ Starter GPOs    │
└───────────────────────────────────────────────────────────────────────────────┘
```


## Indice
- [Panoramica](#panoramica)
- [Architettura delle Group Policy](#architettura-delle-group-policy)
- [Client-Side Extensions (CSE) — Deep Dive](#client-side-extensions-cse--deep-dive)
- [Ordine di Elaborazione: LSDO](#ordine-di-elaborazione-lsdo)
- [Ereditarietà, Blocco e Imposizione](#ereditarietà-blocco-e-imposizione)
- [Security Filtering e WMI Filters](#security-filtering-e-wmi-filters)
- [MS16-072 — Analisi di Impatto Completa](#ms16-072--analisi-di-impatto-completa)
- [WMI Filters — Deep Dive](#wmi-filters--deep-dive)
- [Loopback Processing](#loopback-processing)
- [Preference Items vs Policy Settings](#preference-items-vs-policy-settings)
- [Central Store e File ADMX/ADML](#central-store-e-file-admxadml)
- [ADMX/ADML Deep Dive — Versioning e Intune](#admxadml-deep-dive--versioning-e-intune)
- [ADMX Templates Avanzati e Applicazioni di Terze Parti](#admx-templates-avanzati-e-applicazioni-di-terze-parti)
- [Administrative Templates vs Security Settings vs Software Restriction](#administrative-templates-vs-security-settings-vs-software-restriction)
- [Security Baselines e CIS Benchmarks](#security-baselines-e-cis-benchmarks)
- [Advanced Audit Policy Configuration](#advanced-audit-policy-configuration)
- [Resultant Set of Policy (RSoP) — Analisi Avanzata](#resultant-set-of-policy-rsop--analisi-avanzata)
- [gpresult /h — Ricetta di Triage](#gpresult-h--ricetta-di-triage)
- [GPO e Microsoft Intune — Gestione Ibrida](#gpo-e-microsoft-intune--gestione-ibrida)
- [Intune ADMX Ingestion](#intune-admx-ingestion)
- [Ricette GPO Comuni](#ricette-gpo-comuni)
- [Gestione GPO con PowerShell](#gestione-gpo-con-powershell)
- [GPO Backup, Migrazione e Import Cross-Dominio](#gpo-backup-migrazione-e-import-cross-dominio)
- [Starter GPOs](#starter-gpos)
- [GPO Performance — Ottimizzazione dell'Elaborazione](#gpo-performance--ottimizzazione-dellelaborazione)
- [Slow Link Detection](#slow-link-detection)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)
- [Riferimenti](#riferimenti)
- [Esercizi](#esercizi)
- [Auto-valutazione](#auto-valutazione)
- [Letture Primarie Consigliate](#letture-primarie-consigliate)
- [Collegamenti Incrociati](#collegamenti-incrociati)
- [Glossario Locale](#glossario-locale)

---

## Panoramica

Le Group Policy rappresentano uno dei meccanismi più potenti e granulari offerti da Microsoft per la gestione centralizzata di configurazioni, sicurezza e comportamento di utenti e computer all'interno di un dominio Active Directory. Attraverso i Group Policy Objects (GPO), un amministratore può definire centinaia di impostazioni che vengono applicate automaticamente ai target designati, eliminando la necessità di configurazioni manuali su ogni singola macchina.

Il sistema delle Group Policy si basa su un'architettura client-server in cui il domain controller memorizza i GPO nel database di Active Directory (componente GPC — Group Policy Container) e nella cartella SYSVOL (componente GPT — Group Policy Template), mentre il client-side extension (CSE) presente su ogni macchina Windows interpreta e applica le impostazioni. Questo meccanismo garantisce che le policy vengano applicate in modo coerente e prevedibile, seguendo un ordine di precedenza ben definito.

Comprendere a fondo il funzionamento delle Group Policy è essenziale per qualsiasi amministratore Windows, poiché errori nella configurazione possono avere impatti significativi sulla sicurezza, sulla produttività degli utenti e sulla stabilità dell'infrastruttura. Questa guida analizza ogni aspetto delle GPO, dall'architettura interna alle tecniche avanzate di filtering e troubleshooting, fornendo esempi pratici e ricette pronte per l'uso in ambiente di produzione.

---

## Architettura delle Group Policy

### Componenti Fondamentali

Ogni GPO è composto da due elementi distinti che lavorano in sinergia:

**Group Policy Container (GPC):** Oggetto memorizzato nel database di Active Directory, accessibile via LDAP al percorso `CN=Policies,CN=System,DC=dominio,DC=com`. Il GPC contiene metadati come il GUID del GPO, il numero di versione, lo stato (abilitato/disabilitato) e i link alle Organizational Unit. Il GPC è replicato attraverso la normale replica di Active Directory.

**Group Policy Template (GPT):** Struttura di cartelle memorizzata nella share SYSVOL di ogni domain controller, al percorso `\\dominio.com\SYSVOL\dominio.com\Policies\{GUID}`. Il GPT contiene i file effettivi delle policy: file .pol per le impostazioni del registry, script di logon/logoff e startup/shutdown, template di sicurezza e altri file di configurazione. Il GPT è replicato tramite DFS-R (o FRS nei domini legacy).

```
\\dominio.com\SYSVOL\dominio.com\Policies\{GUID}\
├── Machine\
│   ├── Registry.pol          # Impostazioni registry Computer
│   ├── Scripts\
│   │   ├── Startup\          # Script di avvio
│   │   └── Shutdown\         # Script di arresto
│   ├── Microsoft\
│   │   └── Windows NT\
│   │       └── SecEdit\
│   │           └── GptTmpl.inf  # Template di sicurezza
│   └── Preferences\          # Preference items Computer
│       ├── Drives\
│       ├── Printers\
│       └── ScheduledTasks\
├── User\
│   ├── Registry.pol          # Impostazioni registry Utente
│   ├── Scripts\
│   │   ├── Logon\            # Script di logon
│   │   └── Logoff\           # Script di logoff
│   └── Preferences\          # Preference items Utente
│       ├── Drives\
│       └── Shortcuts\
├── GPT.INI                   # Versione e stato del GPT
└── comment.cmtx              # Commenti del GPO
```

### Client-Side Extensions (CSE)

Le CSE sono DLL registrate sul client che interpretano specifiche categorie di impostazioni. Ogni CSE ha un GUID univoco e viene invocata dal Group Policy Client Service (`gpsvc`) durante l'elaborazione delle policy. Le CSE principali includono:

| CSE | GUID | Funzione |
|-----|------|----------|
| Registry | {35378EAC-683F-11D2-A89A-00C04FBBCFA2} | Impostazioni Administrative Template |
| Security | {827D319E-6EAC-11D2-A4EA-00C04F79F83A} | Policy di sicurezza |
| Scripts | {42B5FAAE-6536-11D2-AE5A-0000F87571E3} | Script startup/shutdown/logon/logoff |
| Software Installation | {C6DC5466-785A-11D2-84D0-00C04FB169F7} | Distribuzione software |
| Folder Redirection | {25537BA6-77A8-11D2-9B6C-0000F8080861} | Reindirizzamento cartelle |
| Group Policy Preferences | {BC75B1ED-5833-4858-9BB8-CBF0B166DF9D} | Preference items |

### Ciclo di Elaborazione

L'elaborazione delle Group Policy avviene in momenti specifici:

1. **All'avvio del computer** — Le policy Computer Configuration vengono applicate prima che appaia la schermata di logon. Il servizio `gpsvc` enumera i GPO applicabili, scarica le impostazioni aggiornate e invoca le CSE appropriate.

2. **Al logon dell'utente** — Le policy User Configuration vengono applicate dopo l'autenticazione ma prima che l'utente veda il desktop (per le policy sincrone) o in background (per le policy asincrone, default da Windows Vista in poi).

3. **Aggiornamento periodico in background** — Ogni 90 minuti (con un offset casuale di 0-30 minuti) per workstation e server, ogni 5 minuti per i domain controller. L'intervallo è configurabile tramite GPO stessa.

4. **Su richiesta manuale** — Tramite il comando `gpupdate /force` o `Invoke-GPUpdate` in PowerShell.

```powershell
# Forzare aggiornamento policy sul computer locale
gpupdate /force

# Forzare aggiornamento su un computer remoto
Invoke-GPUpdate -Computer "WORKSTATION01" -Force -RandomDelayInMinutes 0

# Forzare aggiornamento su tutte le macchine di una OU
Get-ADComputer -Filter * -SearchBase "OU=Workstations,DC=contoso,DC=com" |
    ForEach-Object { Invoke-GPUpdate -Computer $_.Name -Force }
```

---

## Client-Side Extensions (CSE) — Deep Dive

Le Client-Side Extensions sono il motore esecutivo delle Group Policy sul lato client. Ogni CSE è una DLL registrata nel registry di Windows e viene invocata dal servizio Group Policy Client (`gpsvc.dll`) in base al tipo di impostazioni contenute nel GPO. Comprendere il comportamento di ogni CSE è fondamentale per diagnosticare problemi di applicazione e ottimizzare le prestazioni.

### Registro delle CSE

Le CSE sono registrate sotto la chiave di registro:

```
HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\GPExtensions\{CSE-GUID}
```

Ogni voce contiene:

| Valore | Tipo | Descrizione |
|--------|------|-------------|
| `(Default)` | REG_SZ | Nome della CSE |
| `DllName` | REG_EXPAND_SZ | Percorso della DLL (es. `userenv.dll`) |
| `ProcessGroupPolicy` | REG_SZ | Funzione entry-point nella DLL |
| `NoMachinePolicy` | REG_DWORD | 1 = non elabora Computer Configuration |
| `NoUserPolicy` | REG_DWORD | 1 = non elabora User Configuration |
| `NoSlowLink` | REG_DWORD | 1 = non elabora su slow link |
| `NoBackgroundPolicy` | REG_DWORD | 1 = non elabora in background refresh |
| `NoGPOListChanges` | REG_DWORD | 1 = non rielabora se la lista GPO non è cambiata |

```powershell
# Enumerare tutte le CSE registrate sul sistema con il loro comportamento
Get-ChildItem "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\GPExtensions" |
    ForEach-Object {
        $props = Get-ItemProperty $_.PSPath
        [PSCustomObject]@{
            GUID            = $_.PSChildName
            Name            = $props.'(default)'
            DLL             = $props.DllName
            NoSlowLink      = [bool]$props.NoSlowLink
            NoBackground    = [bool]$props.NoBackgroundPolicy
            NoGPOListChange = [bool]$props.NoGPOListChanges
        }
    } | Sort-Object Name | Format-Table -AutoSize
```

### Comportamento delle CSE Principali

**Registry CSE** (`{35378EAC-683F-11D2-A89A-00C04FBBCFA2}`): Elabora i file `Registry.pol` e applica le impostazioni degli Administrative Templates. E' la CSE più veloce poiché si limita a scrivere chiavi di registro. Opera sia su slow link sia in background. Non rielabora se la lista GPO non è cambiata (ottimizzazione di default).

**Security CSE** (`{827D319E-6EAC-11D2-A4EA-00C04F79F83A}`): Elabora il file `GptTmpl.inf` e applica le security settings (password policy, user rights assignment, security options, audit policy). Viene rielaborata automaticamente ogni 16 ore anche se il GPO non è cambiato — garantendo la correzione di eventuali drift manuali.

**Scripts CSE** (`{42B5FAAE-6536-11D2-AE5A-0000F87571E3}`): Esegue gli script di startup/shutdown (Computer) e logon/logoff (User). Per default non opera su slow link (`NoSlowLink=1`). Ha un timeout configurabile tramite GPO (default: 600 secondi).

**Group Policy Preferences CSE** (`{BC75B1ED-5833-4858-9BB8-CBF0B166DF9D}`): Elabora le Preference items (drive maps, printers, registry, scheduled tasks, ecc.). Opera su slow link. L'Item-Level Targeting viene valutato dalla CSE stessa, non dal motore GPO principale.

> **Errore comune:** Molti amministratori confondono il fatto che una CSE non rielabori in background con il fatto che il GPO non sia applicato. La Registry CSE per default salta il background refresh se nulla è cambiato — ciò non significa che le impostazioni non siano attive. Forzare la rielaborazione con `gpupdate /force` o configurando "Process even if the Group Policy objects have not changed" sulla CSE specifica.

### Diagnostica Errori CSE

Quando una CSE fallisce, il servizio `gpsvc` registra eventi nel log operativo. Gli Event ID rilevanti:

| Event ID | Significato |
|----------|-------------|
| 4016 | Inizio elaborazione CSE |
| 5016 | Completamento elaborazione CSE (include durata in ms) |
| 6016 | Elaborazione CSE fallita |
| 7016 | Timeout elaborazione CSE |
| 4017 | Il servizio gpsvc non ha potuto elaborare la CSE |

```powershell
# Diagnosticare i tempi di elaborazione per ogni CSE
Get-WinEvent -LogName "Microsoft-Windows-GroupPolicy/Operational" |
    Where-Object { $_.Id -eq 5016 } |
    ForEach-Object {
        $msg = $_.Message
        $cseName = if ($msg -match 'extension (.+?) completed') { $Matches[1] } else { 'N/A' }
        $duration = if ($msg -match '(\d+) milliseconds') { [int]$Matches[1] } else { 0 }
        [PSCustomObject]@{
            TimeCreated = $_.TimeCreated
            CSE         = $cseName
            DurationMs  = $duration
        }
    } | Sort-Object DurationMs -Descending | Select-Object -First 20 | Format-Table -AutoSize
```

---

## Ordine di Elaborazione: LSDO

L'acronimo LSDO (Local, Site, Domain, OU) descrive l'ordine in cui i GPO vengono elaborati. Questo ordine è determinante perché, in caso di conflitto tra impostazioni, **l'ultimo GPO elaborato prevale** (vince chi viene dopo):

```
+----------------------------------+
|  1. LOCAL GPO (gpedit.msc)       |  <- Elaborato per primo
+----------------------------------+         (priorità più bassa)
           |
           v
+----------------------------------+
|  2. SITE GPO                     |
+----------------------------------+
           |
           v
+----------------------------------+
|  3. DOMAIN GPO                   |
+----------------------------------+
           |
           v
+----------------------------------+
|  4. OU GPO (genitore)            |
+----------------------------------+
           |
           v
+----------------------------------+
|  5. OU GPO (figlio)              |  <- Elaborato per ultimo
+----------------------------------+         (priorità più alta)
```

### Local Group Policy

La Local GPO è memorizzata direttamente sul computer locale in `%SystemRoot%\System32\GroupPolicy\`. Da Windows Vista, esistono anche Multiple Local GPO (MLGPO) che permettono di definire policy diverse per amministratori, non-amministratori e utenti specifici:

- `%SystemRoot%\System32\GroupPolicy` — Policy locale standard
- `%SystemRoot%\System32\GroupPolicyUsers\S-1-5-...` — Policy per utente specifico
- `%SystemRoot%\System32\GroupPolicyUsers\Non-Administrators` — Policy per non-admin

Le Local GPO hanno la priorità più bassa e vengono sovrascritte da qualsiasi GPO di dominio in caso di conflitto.

### Site GPO

I GPO collegati ai siti di Active Directory vengono elaborati dopo la Local GPO. I siti sono definiti in `Active Directory Sites and Services` e rappresentano tipicamente raggruppamenti geografici. L'uso di GPO a livello di sito è relativamente raro perché i siti attraversano i confini dei domini e possono avere effetti imprevisti.

### Domain GPO

I GPO collegati al dominio vengono elaborati dopo quelli del sito. Il GPO più importante a livello di dominio è la **Default Domain Policy** (GUID: `{31B2F340-016D-11D2-945F-00C04FB984F9}`), che definisce le policy di password e account lockout per l'intero dominio. Microsoft raccomanda di non modificare la Default Domain Policy se non per queste specifiche impostazioni.

### OU GPO

I GPO collegati alle Organizational Unit vengono elaborati per ultimi, partendo dalla OU più alta nella gerarchia fino alla OU che contiene direttamente l'oggetto. Questo significa che una OU figlia può sovrascrivere le impostazioni definite dalla OU genitore.

### Ordine di Collegamento (Link Order)

Quando più GPO sono collegati allo stesso contenitore (sito, dominio o OU), il **Link Order** determina la precedenza. Il GPO con Link Order 1 ha la priorità più alta tra i GPO collegati a quel contenitore (viene elaborato per ultimo tra i GPO di quel livello).

```powershell
# Visualizzare il link order dei GPO su una OU
Get-GPInheritance -Target "OU=Workstations,DC=contoso,DC=com"

# Modificare il link order
Set-GPLink -Name "GPO Restrizioni Desktop" `
    -Target "OU=Workstations,DC=contoso,DC=com" `
    -Order 1
```

---

## Ereditarietà, Blocco e Imposizione

### Ereditarietà

Per impostazione predefinita, i GPO vengono ereditati lungo la gerarchia di Active Directory. Un GPO collegato al dominio si applica a tutti gli oggetti in tutte le OU del dominio. Un GPO collegato a una OU genitore si applica anche a tutte le OU figlie. Questo meccanismo di ereditarietà riduce la duplicazione: le impostazioni comuni possono essere definite a un livello alto e automaticamente propagate.

L'ereditarietà riguarda solo i GPO collegati ai contenitori superiori nella gerarchia. Le impostazioni non configurate ("Not Configured") non interferiscono: solo le impostazioni esplicitamente configurate (Enabled o Disabled) hanno effetto.

### Block Inheritance

Un amministratore può interrompere l'ereditarietà su una specifica OU attivando **Block Inheritance**. Quando questa opzione è attiva, nessun GPO ereditato dai livelli superiori (dominio e OU genitore) viene applicato agli oggetti in quella OU — solo i GPO collegati direttamente alla OU stessa avranno effetto.

```powershell
# Abilitare Block Inheritance su una OU
Set-GPInheritance -Target "OU=ServerFarm,DC=contoso,DC=com" -IsBlocked Yes

# Verificare lo stato di Block Inheritance
(Get-GPInheritance -Target "OU=ServerFarm,DC=contoso,DC=com").GpoInheritanceBlocked
```

Nel Group Policy Management Console (GPMC), le OU con Block Inheritance sono indicate da un'icona blu con un punto esclamativo.

### Enforced (No Override)

L'opzione **Enforced** (precedentemente nota come "No Override") è l'arma più potente nella gerarchia delle GPO. Quando un collegamento GPO è marcato come Enforced:

1. Le sue impostazioni prevalgono su qualsiasi GPO elaborato successivamente
2. **Non può essere bloccato da Block Inheritance** — il GPO Enforced viene sempre applicato

Questo meccanismo è fondamentale per garantire che policy di sicurezza critiche definite a livello di dominio non possano essere aggirate da amministratori di OU che impostano Block Inheritance.

```powershell
# Impostare un collegamento GPO come Enforced
Set-GPLink -Name "Security Baseline - Obbligatorio" `
    -Target "DC=contoso,DC=com" `
    -Enforced Yes

# Rimuovere l'imposizione
Set-GPLink -Name "Security Baseline - Obbligatorio" `
    -Target "DC=contoso,DC=com" `
    -Enforced No
```

### Matrice di Precedenza

```
                    Block Inheritance    Enforced
                    sulla OU figlia?     sul link GPO genitore?     Risultato
                    ─────────────────    ──────────────────────     ──────────
Scenario 1:        No                   No                         GPO ereditato normalmente
Scenario 2:        Sì                   No                         GPO bloccato
Scenario 3:        No                   Sì                         GPO applicato con priorità alta
Scenario 4:        Sì                   Sì                         GPO applicato (Enforced vince)
```

---

## Security Filtering e WMI Filters

### Security Filtering

Per impostazione predefinita, un GPO si applica a tutti gli utenti e computer autenticati nel contenitore a cui è collegato. Il **Security Filtering** permette di restringere l'applicazione a specifici utenti, computer o gruppi di sicurezza, modificando le autorizzazioni sull'oggetto GPO stesso.

Il principio è semplice: un GPO viene applicato a un oggetto solo se quell'oggetto ha le autorizzazioni **Read** e **Apply Group Policy** sull'oggetto GPO. Rimuovendo "Authenticated Users" dal security filtering e aggiungendo un gruppo specifico, si limita l'applicazione.

**Attenzione critica (post-MS16-072):** A partire dalla patch di sicurezza MS16-072 (giugno 2016), il computer deve avere l'autorizzazione **Read** sul GPO affinché le policy utente vengano elaborate. Questo significa che se si rimuove "Authenticated Users" dal security filtering, è necessario aggiungere "Domain Computers" con almeno il permesso di **Read**, altrimenti il GPO non verrà applicato nemmeno agli utenti target.

```powershell
# Configurare security filtering: rimuovere Authenticated Users
Set-GPPermission -Name "GPO Desktop Restrizioni" `
    -TargetName "Authenticated Users" `
    -TargetType Group `
    -PermissionLevel None

# Aggiungere il gruppo target con Apply
Set-GPPermission -Name "GPO Desktop Restrizioni" `
    -TargetName "GRP-Desktop-Limitati" `
    -TargetType Group `
    -PermissionLevel GpoApply

# Aggiungere Domain Computers con Read (necessario post-MS16-072)
Set-GPPermission -Name "GPO Desktop Restrizioni" `
    -TargetName "Domain Computers" `
    -TargetType Group `
    -PermissionLevel GpoRead
```

### Deny Apply Group Policy

Un'alternativa al security filtering positivo è l'uso del **Deny** sull'autorizzazione "Apply Group Policy". Poiché Deny ha sempre la precedenza su Allow, questo metodo permette di escludere specifici utenti o gruppi dall'applicazione di un GPO senza modificare il filtering principale.

Caso d'uso tipico: un GPO che blocca l'accesso al Pannello di Controllo è collegato alla OU degli utenti, ma gli amministratori IT — che sono nella stessa OU — devono essere esclusi. Si aggiunge un Deny Apply al gruppo "IT-Admins".

### WMI Filters

I **WMI Filters** permettono di condizionare l'applicazione di un GPO in base a query WQL (WMI Query Language) eseguite sul client al momento dell'elaborazione. Se la query restituisce risultati, il GPO viene applicato; altrimenti viene ignorato.

I WMI Filters sono estremamente potenti ma hanno un impatto sulle prestazioni: ogni query viene eseguita localmente sul client durante il ciclo di elaborazione delle policy, aggiungendo latenza. Vanno usati con moderazione.

```powershell
# Creare un WMI Filter per selezionare solo Windows 11
$wmiFilter = @"
SELECT * FROM Win32_OperatingSystem WHERE Version LIKE "10.0.2%" AND ProductType = "1"
"@

# Esempi di query WMI comuni per GPO filtering:

# Solo laptop (batteria presente)
# SELECT * FROM Win32_Battery

# Solo macchine con più di 8 GB di RAM
# SELECT * FROM Win32_ComputerSystem WHERE TotalPhysicalMemory >= 8589934592

# Solo macchine in una specifica subnet
# SELECT * FROM Win32_NetworkAdapterConfiguration WHERE IPEnabled = TRUE AND IPAddress LIKE "10.0.1.%"

# Solo macchine con un software specifico installato
# SELECT * FROM Win32_Product WHERE Name LIKE "%Office%"
```

Per creare un WMI Filter tramite GPMC: tasto destro su "WMI Filters" → "New" → specificare nome, descrizione e query WQL. Poi, nelle proprietà del GPO, tab "General" → selezionare il WMI Filter dal menu a tendina.

---

## MS16-072 — Analisi di Impatto Completa

### Contesto della Vulnerabilità

Il Microsoft Security Bulletin MS16-072 (CVE-2016-3223), rilasciato il 14 giugno 2016, ha corretto una vulnerabilità di elevazione dei privilegi nel meccanismo di elaborazione delle Group Policy. La vulnerabilità consentiva a un attaccante in posizione man-in-the-middle (MITM) di iniettare GPO malevoli durante la fase di download, poiché il client autenticava la connessione utilizzando le credenziali dell'utente anziché quelle del computer.

Riferimento: https://learn.microsoft.com/en-us/security-updates/securitybulletins/2016/ms16-072 (consultato: 2026-05-23)

### Comportamento Pre-Patch

Prima di MS16-072, il flusso di elaborazione delle policy utente era:

```
1. Utente fa logon
2. Il servizio gpsvc usa il token dell'UTENTE per:
   a. Enumerare i GPO applicabili via LDAP
   b. Verificare i permessi (Read + Apply Group Policy) sull'oggetto GPO
   c. Scaricare il contenuto del GPT da SYSVOL
3. Se l'utente ha Read + Apply → GPO applicato
4. Se l'utente non ha Read → GPO ignorato
```

Questo significava che il Security Filtering per le policy utente poteva basarsi esclusivamente sui permessi dell'utente. Un GPO con solo "GRP-Finance" nel Security Filtering funzionava correttamente perché il token dell'utente conteneva la membership del gruppo.

### Comportamento Post-Patch

Dopo MS16-072, il servizio `gpsvc` utilizza il **token del computer** per enumerare e scaricare i GPO utente:

```
1. Utente fa logon
2. Il servizio gpsvc usa il token del COMPUTER per:
   a. Enumerare i GPO applicabili via LDAP (richiede Read)
   b. Scaricare il contenuto del GPT da SYSVOL (richiede Read)
3. Poi valuta i permessi Apply Group Policy con il token dell'UTENTE
4. Se il computer ha Read E l'utente ha Apply → GPO applicato
5. Se il computer NON ha Read → GPO invisibile, non scaricato
```

### Impatto Operativo

L'impatto è stato significativo e ha colpito molte organizzazioni che utilizzavano Security Filtering granulare sulle policy utente:

| Scenario | Pre-MS16-072 | Post-MS16-072 |
|----------|-------------|---------------|
| Security Filtering: Authenticated Users | Funziona | Funziona (Auth. Users include computer) |
| Security Filtering: solo gruppo utenti, Authenticated Users rimosso | Funziona | **NON funziona** — computer non ha Read |
| Security Filtering: gruppo utenti + Domain Computers (Read) | Funziona | Funziona |
| Deny Apply su gruppo utenti | Funziona | Funziona (Read computer OK, Apply negato) |

### Configurazione Corretta Post-MS16-072

Per ogni GPO che utilizza Security Filtering con un gruppo specifico di utenti:

```powershell
# Pattern corretto post-MS16-072 per GPO con user policy filtrate

$gpoName = "USR - Desktop Restrictions - Finance"

# 1. Rimuovere Authenticated Users dal filtering (se necessario)
Set-GPPermission -Name $gpoName `
    -TargetName "Authenticated Users" `
    -TargetType Group `
    -PermissionLevel None

# 2. Aggiungere il gruppo utenti target con Apply
Set-GPPermission -Name $gpoName `
    -TargetName "GRP-Finance-Users" `
    -TargetType Group `
    -PermissionLevel GpoApply

# 3. CRITICO: Aggiungere Domain Computers con SOLO Read
#    (non GpoApply — altrimenti il GPO si applicherebbe anche ai computer)
Set-GPPermission -Name $gpoName `
    -TargetName "Domain Computers" `
    -TargetType Group `
    -PermissionLevel GpoRead

# 4. Verificare la configurazione risultante
Get-GPPermission -Name $gpoName -All | Format-Table Trustee, Permission, Inherited -AutoSize
```

### Script di Audit per Conformità MS16-072

```powershell
# Identificare tutti i GPO vulnerabili al problema MS16-072
# (GPO con user policy dove manca Read per i computer)
function Find-MS16072VulnerableGPOs {
    $vulnerable = @()
    Get-GPO -All | ForEach-Object {
        $gpo = $_
        # Saltare GPO con solo Computer Configuration
        if ($gpo.User.DSVersion -eq 0 -and $gpo.User.SysvolVersion -eq 0) { return }

        $perms = Get-GPPermission -Guid $gpo.Id -All
        $hasAuthUsers = $perms | Where-Object {
            $_.Trustee.Name -eq "Authenticated Users" -and
            $_.Permission -in @("GpoApply", "GpoRead")
        }
        $hasDomainComputers = $perms | Where-Object {
            $_.Trustee.Name -eq "Domain Computers" -and
            $_.Permission -in @("GpoApply", "GpoRead")
        }

        if (-not $hasAuthUsers -and -not $hasDomainComputers) {
            $vulnerable += [PSCustomObject]@{
                GPOName     = $gpo.DisplayName
                GPOId       = $gpo.Id
                UserVersion = $gpo.User.DSVersion
                Issue       = "Nessun Read per computer — user policy non verranno applicate"
            }
        }
    }

    if ($vulnerable.Count -gt 0) {
        Write-Warning "Trovati $($vulnerable.Count) GPO vulnerabili al problema MS16-072:"
        $vulnerable | Format-Table -AutoSize
    } else {
        Write-Output "Tutti i GPO con user policy hanno permessi Read per i computer."
    }
    return $vulnerable
}

Find-MS16072VulnerableGPOs
```

> **Caso reale:** Dopo il Patch Tuesday di giugno 2016, numerose organizzazioni hanno riportato interruzioni nelle mappature drive, configurazioni stampanti e restrizioni desktop distribuite via GPO. La causa era che i GPO con Security Filtering granulare (senza Authenticated Users) avevano perso la visibilità per i computer. Microsoft ha pubblicato KB3163622 con le linee guida per la riconfigurazione.

---

## WMI Filters — Deep Dive

### Architettura e Impatto sulle Prestazioni

I WMI Filters sono oggetti memorizzati in Active Directory nella classe `msWMI-Som` sotto `CN=SOM,CN=WMIPolicy,CN=System,DC=dominio,DC=com`. Ogni WMI Filter contiene una o più query WQL che vengono eseguite localmente sul client durante l'elaborazione dei GPO. Il risultato della query determina se il GPO associato viene applicato o ignorato.

L'impatto sulle prestazioni è proporzionale alla complessità della query e alla classe WMI interrogata:

| Classe WMI | Tempo Tipico | Note |
|------------|-------------|------|
| `Win32_OperatingSystem` | < 50 ms | Rapida, dati sempre in cache |
| `Win32_ComputerSystem` | < 50 ms | Rapida |
| `Win32_Battery` | < 100 ms | Rapida |
| `Win32_NetworkAdapterConfiguration` | 100–500 ms | Dipende dal numero di adapter |
| `Win32_LogicalDisk` | 100–300 ms | Dipende dal numero di volumi |
| `Win32_Product` | 5–60 secondi | **Evitare** — enumera MSI, molto lenta |
| `Win32_QuickFixEngineering` | 1–10 secondi | Lenta su sistemi con molte patch |

> **Errore comune:** Usare `Win32_Product` per verificare la presenza di software installato. Questa classe attiva una validazione di ogni pacchetto MSI installato, causando tempi di elaborazione di decine di secondi. Usare `Win32Reg_AddRemovePrograms` (se disponibile via SCCM) oppure una query sul registro: `SELECT * FROM __InstanceModificationEvent WHERE TargetInstance ISA 'Win32_OperatingSystem'` non è la soluzione — meglio una query diretta sul registry key corrispondente via Item-Level Targeting con Registry Match nelle Preferences.

### Query WQL Ottimizzate di Uso Comune

```sql
-- Solo Windows 11 (build 22000+)
SELECT * FROM Win32_OperatingSystem
WHERE Version LIKE "10.0.2%" AND ProductType = "1"

-- Solo Windows Server 2022
SELECT * FROM Win32_OperatingSystem
WHERE Version LIKE "10.0.20348%" AND ProductType <> "1"

-- Solo Windows Server 2025
SELECT * FROM Win32_OperatingSystem
WHERE Version LIKE "10.0.26100%" AND ProductType <> "1"

-- Solo laptop (presenza batteria)
SELECT * FROM Win32_Battery

-- Solo desktop (assenza batteria)
SELECT * FROM Win32_ComputerSystem
WHERE PCSystemType = "1"

-- Macchine con almeno 16 GB di RAM
SELECT * FROM Win32_ComputerSystem
WHERE TotalPhysicalMemory >= 17179869184

-- Macchine con disco C: con meno di 20 GB liberi
SELECT * FROM Win32_LogicalDisk
WHERE DeviceID = "C:" AND FreeSpace < 21474836480

-- Macchine con architettura 64-bit
SELECT * FROM Win32_Processor WHERE AddressWidth = "64"

-- Solo macchine virtuali Hyper-V
SELECT * FROM Win32_ComputerSystem
WHERE Model = "Virtual Machine"

-- Solo macchine virtuali VMware
SELECT * FROM Win32_ComputerSystem
WHERE Model LIKE "VMware%"
```

### Creazione WMI Filters via PowerShell

```powershell
# Funzione per creare WMI Filters programmaticamente
function New-GPOWmiFilter {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$Description,
        [Parameter(Mandatory)][string[]]$Queries,
        [string]$Domain = $env:USERDNSDOMAIN
    )

    $defaultNamingContext = (Get-ADRootDSE).defaultNamingContext
    $wmiPath = "CN=SOM,CN=WMIPolicy,CN=System,$defaultNamingContext"
    $guid = "{$([System.Guid]::NewGuid())}"
    $creationDate = (Get-Date).ToUniversalTime().ToString("yyyyMMddHHmmss.ffffff-000")
    $author = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name

    # Formattare le query nel formato msWMI-Parm2
    $queryStrings = $Queries | ForEach-Object {
        "1;3;10;$($_.Length);WQL;root\CIMv2;$_;"
    }
    $parm2 = "$($Queries.Count);" + ($queryStrings -join "")

    $attributes = @{
        "msWMI-Name"             = $Name
        "msWMI-Parm1"            = $Description
        "msWMI-Parm2"            = $parm2
        "msWMI-Author"           = $author
        "msWMI-ID"               = $guid
        "msWMI-ChangeDate"       = $creationDate
        "msWMI-CreationDate"     = $creationDate
    }

    New-ADObject -Name $guid -Type "msWMI-Som" -Path $wmiPath -OtherAttributes $attributes
    Write-Output "WMI Filter '$Name' creato con GUID $guid"
}

# Esempio: creare un WMI Filter per soli laptop
New-GPOWmiFilter -Name "WMI - Solo Laptop" `
    -Description "Filtra per macchine con batteria (laptop)" `
    -Queries @("SELECT * FROM Win32_Battery")
```

---

## Loopback Processing

Il **Loopback Processing** è una funzionalità avanzata che modifica il comportamento standard dell'applicazione delle policy utente. Normalmente, le policy utente sono determinate dalla posizione dell'oggetto utente in Active Directory, indipendentemente dal computer su cui l'utente effettua il logon. Con il Loopback Processing, le policy utente vengono influenzate dalla posizione dell'oggetto computer.

Questa funzionalità è fondamentale in scenari come:
- **Kiosk e computer condivisi** — Dove è necessario che tutti gli utenti abbiano la stessa esperienza, indipendentemente dal loro profilo
- **Terminal Server / Remote Desktop Services** — Dove le policy utente devono essere uniformi per il server
- **Sale riunioni e laboratori** — Dove i computer devono applicare restrizioni specifiche a chiunque si colleghi

### Modalità Replace

In modalità **Replace**, le policy utente normali (basate sulla posizione dell'utente in AD) vengono completamente ignorate. Al loro posto, vengono applicate solo le policy utente definite nei GPO collegati alla OU del computer.

```
Flusso Replace:
1. Computer si avvia → applica Computer Configuration normalmente
2. Utente fa logon → le User Configuration dalla OU dell'utente vengono IGNORATE
3. Vengono applicate SOLO le User Configuration dei GPO della OU del computer
```

### Modalità Merge

In modalità **Merge**, le policy utente normali vengono applicate per prime, poi le policy utente dei GPO della OU del computer vengono applicate in aggiunta. In caso di conflitto, le impostazioni della OU del computer prevalgono.

```
Flusso Merge:
1. Computer si avvia → applica Computer Configuration normalmente
2. Utente fa logon → applica User Configuration dalla OU dell'utente
3. SOVRAPPONE le User Configuration dei GPO della OU del computer
4. In caso di conflitto → vince la configurazione del computer
```

### Configurazione

Il Loopback Processing si configura tramite:
`Computer Configuration → Policies → Administrative Templates → System → Group Policy → Configure user Group Policy loopback processing mode`

```powershell
# Verificare se il loopback processing è attivo su un computer
Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\System" -Name "UserPolicyMode" -ErrorAction SilentlyContinue
# 0 o assente = disabilitato, 1 = Replace, 2 = Merge
```

> **Approfondimento:** Il Loopback Processing è particolarmente rilevante in ambienti Azure Virtual Desktop (AVD) e Citrix Virtual Apps, dove i session host sono posizionati in OU dedicate. In modalità Replace, si garantisce che ogni utente che si collega al session host riceva una configurazione desktop uniforme — eliminando la variabilità delle policy utente personali che potrebbero introdurre conflitti o falle di sicurezza. Microsoft raccomanda Replace per scenari kiosk e Merge per scenari RDS dove si vuole mantenere parte della personalizzazione dell'utente.

---

## Preference Items vs Policy Settings

### Differenze Fondamentali

Le **Policy Settings** (impostazioni di policy tradizionali, sotto la sezione "Policies") sono gestite dal registry tattooing controllato: quando un GPO viene rimosso o non si applica più, le impostazioni vengono automaticamente ripristinate al valore predefinito. Le chiavi di registro vengono scritte in aree "managed" del registry (`HKLM\SOFTWARE\Policies\` e `HKCU\SOFTWARE\Policies\`).

Le **Preference Items** (sotto la sezione "Preferences") sono più flessibili: configurano impostazioni "reali" del sistema operativo nelle aree "non-managed" del registry e del filesystem. Quando un GPO con preference viene rimosso, le impostazioni rimangono (a meno che non sia configurata l'opzione "Remove this item when it is no longer applied").

| Caratteristica | Policy Settings | Preference Items |
|---------------|-----------------|------------------|
| Tattooing | No (rimosso con il GPO) | Sì (persiste, salvo configurazione) |
| Area Registry | Managed (Policies\) | Non-managed (area nativa) |
| Interfaccia utente | Disabilita le opzioni (greyed out) | Configura senza bloccare l'UI |
| Item-Level Targeting | No | Sì |
| Azioni disponibili | Enable/Disable | Create/Replace/Update/Delete |

### Item-Level Targeting

Una delle funzionalità più potenti delle Preference Items è l'**Item-Level Targeting**, che permette di condizionare l'applicazione di una singola preference in base a molteplici criteri, combinabili con operatori AND/OR:

- **Computer Name** — Applicare solo a specifiche macchine
- **Operating System** — Filtrare per versione OS
- **Security Group** — Membership in gruppi
- **IP Address Range** — Range di indirizzi IP
- **Registry Match** — Esistenza o valore di chiavi di registro
- **File Match** — Esistenza di file o cartelle
- **Environment Variable** — Valore di variabili d'ambiente
- **Battery Present** — Laptop vs desktop
- **Processing Mode** — Distinguere tra foreground e background processing
- **LDAP Query** — Query LDAP personalizzate

```
Esempio di Item-Level Targeting per mappatura drive:
┌─────────────────────────────────────────────┐
│ Item-Level Targeting                         │
│                                              │
│ [AND] Security Group: GRP-Finance            │
│ [AND] IP Address Range: 10.0.5.0/24          │
│ [OR]  Computer Name: FINANCE-*               │
│                                              │
│ Risultato: Drive H: → \\fileserver\finance$  │
└─────────────────────────────────────────────┘
```

### Preference Items — Tipologie Dettagliate

Le Preference Items coprono un ampio spettro di configurazioni. Le più utilizzate in ambiente enterprise:

**Drive Maps** (`User Configuration → Preferences → Windows Settings → Drive Maps`):
Mappatura di unità di rete con lettera drive. Supporta le azioni Create, Replace, Update, Delete. L'azione **Replace** è la più comune: rimuove la mappatura esistente e la ricrea, garantendo lo stato desiderato.

**Printers** (`Computer/User Configuration → Preferences → Control Panel Settings → Printers`):
Installazione di stampanti di rete con opzione di impostazione come predefinita. Supporta TCP/IP printers, shared printers e local printers.

**Registry** (`Computer/User Configuration → Preferences → Windows Settings → Registry`):
Creazione, modifica o eliminazione di chiavi e valori di registro in qualsiasi area (non solo Policies\). Utile per configurare applicazioni che non hanno template ADMX.

**Scheduled Tasks** (`Computer Configuration → Preferences → Control Panel Settings → Scheduled Tasks`):
Creazione e gestione di attività pianificate distribuite. Supporta sia Scheduled Tasks legacy sia Immediate Tasks (eseguite una sola volta, immediatamente).

**Shortcuts** (`User Configuration → Preferences → Windows Settings → Shortcuts`):
Creazione di collegamenti sul desktop, nel menu Start o in posizioni personalizzate.

> **Errore comune:** Usare l'azione "Create" anziché "Replace" per le Preference Items. L'azione Create applica la preference solo se l'elemento non esiste già — se un utente modifica manualmente la mappatura drive, la preference non la sovrascriverà. L'azione Replace rimuove e ricrea l'elemento a ogni ciclo di refresh, garantendo lo stato desiderato.

---

## Central Store e File ADMX/ADML

### Administrative Templates

Le impostazioni visibili sotto "Administrative Templates" in Group Policy Editor sono definite da file template:

- **File ADMX** — File XML che definiscono le impostazioni (chiavi di registro, valori, opzioni). Sono language-neutral.
- **File ADML** — File XML di localizzazione che contengono le stringhe tradotte nelle varie lingue. Sono language-specific.

Da Windows Vista in poi, i template ADMX hanno sostituito i vecchi file ADM. I file ADMX possono essere memorizzati localmente su ogni macchina amministrativa (`%SystemRoot%\PolicyDefinitions\`) oppure nel Central Store.

### Central Store

Il **Central Store** è una cartella nella share SYSVOL che centralizza tutti i file ADMX/ADML. Quando esiste il Central Store, GPMC e Group Policy Editor lo utilizzano automaticamente al posto dei file locali, garantendo che tutti gli amministratori vedano gli stessi template.

```powershell
# Creare il Central Store
$sysvolPath = "\\contoso.com\SYSVOL\contoso.com\Policies\PolicyDefinitions"

# Copiare i file ADMX dal computer locale
Copy-Item "C:\Windows\PolicyDefinitions\*.admx" $sysvolPath -Force
Copy-Item "C:\Windows\PolicyDefinitions\it-IT\*" "$sysvolPath\it-IT\" -Force
Copy-Item "C:\Windows\PolicyDefinitions\en-US\*" "$sysvolPath\en-US\" -Force

# Verificare il Central Store
Test-Path $sysvolPath
Get-ChildItem $sysvolPath -Filter "*.admx" | Measure-Object
```

### Aggiungere Template Personalizzati

Molte applicazioni (Chrome, Firefox, Office, Adobe) forniscono i propri file ADMX per gestire le configurazioni via GPO. Per aggiungere un template personalizzato:

1. Scaricare i file ADMX/ADML dal produttore
2. Copiare il file `.admx` nella root del Central Store
3. Copiare il file `.adml` nella sottocartella della lingua appropriata
4. Riaprire GPMC — il template apparirà automaticamente

```powershell
# Esempio: aggiungere i template di Google Chrome
$chromeAdmx = "C:\Temp\ChromeTemplates\policy_templates\windows\admx"
Copy-Item "$chromeAdmx\chrome.admx" $sysvolPath
Copy-Item "$chromeAdmx\google.admx" $sysvolPath
Copy-Item "$chromeAdmx\it-IT\chrome.adml" "$sysvolPath\it-IT\"
Copy-Item "$chromeAdmx\it-IT\google.adml" "$sysvolPath\it-IT\"
Copy-Item "$chromeAdmx\en-US\chrome.adml" "$sysvolPath\en-US\"
Copy-Item "$chromeAdmx\en-US\google.adml" "$sysvolPath\en-US\"
```

---

## ADMX/ADML Deep Dive — Versioning e Intune

### Central Store vs Local Store

Quando una macchina amministrativa apre GPMC, il sistema cerca i template ADMX in quest'ordine:

1. **Central Store** — `\\dominio\SYSVOL\dominio\Policies\PolicyDefinitions\`
2. **Local Store** — `C:\Windows\PolicyDefinitions\` (usato solo se il Central Store non esiste)

Il Central Store viene attivato automaticamente dalla sola presenza della cartella `PolicyDefinitions` nel percorso SYSVOL. Non esiste un'impostazione da abilitare. Se la cartella viene rimossa, GPMC ricade sul Local Store.

### Matrice di Versioning ADMX per Release Windows

Ogni versione di Windows include una versione aggiornata dei template ADMX con nuove policy. La regola operativa è: **il Central Store deve contenere i template della versione Windows più recente presente nell'ambiente**, altrimenti le policy specifiche delle versioni più recenti non saranno visibili in GPMC.

| Release Windows | Template ADMX | Nuove policy notevoli |
|----------------|---------------|-----------------------|
| Windows Server 2016 / W10 1607 | ADMX v1607 | Credential Guard, Windows Hello for Business |
| Windows Server 2019 / W10 1809 | ADMX v1809 | Windows Sandbox policy, Exploit Protection, WDAC |
| Windows 10 21H2 | ADMX 21H2 | Cloud Clipboard, Focus Assist, WSL policy |
| Windows Server 2022 | ADMX v21H2 Server | Azure Arc, SMB compression, Storage Replica |
| Windows 11 22H2 | ADMX 22H2 | Smart App Control, Microsoft Pluton, Passkeys |
| Windows 11 23H2 | ADMX 23H2 | Copilot, Windows Backup, Dev Home |
| Windows 11 24H2 / Server 2025 | ADMX 24H2 | Recall policy, Sudo for Windows, Wi-Fi 7 |

Riferimento: https://learn.microsoft.com/en-us/troubleshoot/windows-client/group-policy/create-and-manage-central-store (consultato: 2026-05-23)

### Procedura di Aggiornamento Sicura del Central Store

```powershell
# Procedura step-by-step per aggiornare il Central Store
# senza causare interruzioni

# 1. Backup dell'attuale Central Store
$centralStore = "\\$env:USERDNSDOMAIN\SYSVOL\$env:USERDNSDOMAIN\Policies\PolicyDefinitions"
$backupDir = "C:\GPOBackups\CentralStore-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
New-Item $backupDir -ItemType Directory -Force | Out-Null
Copy-Item "$centralStore\*" $backupDir -Recurse -Force
Write-Output "Backup Central Store completato in: $backupDir"

# 2. Scaricare i nuovi template ADMX dalla macchina con la versione Windows più recente
#    oppure dal download ufficiale Microsoft
$sourceAdmx = "C:\Windows\PolicyDefinitions"  # dalla macchina W11 24H2 o Server 2025

# 3. Confrontare prima dell'aggiornamento
$currentCount = (Get-ChildItem $centralStore -Filter "*.admx" -ErrorAction SilentlyContinue).Count
$newCount = (Get-ChildItem $sourceAdmx -Filter "*.admx").Count
Write-Output "Central Store attuale: $currentCount ADMX | Nuova versione: $newCount ADMX"

# 4. Copiare i nuovi template (sovrascrive i file esistenti)
Copy-Item "$sourceAdmx\*.admx" $centralStore -Force
# Copiare le localizzazioni
Get-ChildItem $sourceAdmx -Directory | Where-Object { $_.Name -match "^[a-z]{2}-[A-Z]{2}$" } |
    ForEach-Object {
        $destLang = Join-Path $centralStore $_.Name
        if (-not (Test-Path $destLang)) {
            New-Item $destLang -ItemType Directory -Force | Out-Null
        }
        Copy-Item "$($_.FullName)\*.adml" $destLang -Force
    }

# 5. Verificare integrità post-aggiornamento
$finalCount = (Get-ChildItem $centralStore -Filter "*.admx").Count
Write-Output "Central Store aggiornato: $finalCount ADMX"

# 6. Controllare conflitti di namespace
$namespaces = @{}
Get-ChildItem $centralStore -Filter "*.admx" | ForEach-Object {
    [xml]$xml = Get-Content $_.FullName
    $ns = $xml.policyDefinitions.policyNamespaces.target.namespace
    if ($ns -and $namespaces.ContainsKey($ns)) {
        Write-Warning "CONFLITTO: '$ns' in '$($_.Name)' e '$($namespaces[$ns])'"
    }
    if ($ns) { $namespaces[$ns] = $_.Name }
}
```

### Mapping ADMX → Intune

Microsoft Intune supporta l'importazione di policy ADMX-backed attraverso il catalog di Settings (Intune Settings Catalog). Non tutte le impostazioni ADMX hanno un equivalente diretto. La mappatura segue questo schema:

```
GPO ADMX Setting
    │
    ├─ Se presente in Intune Settings Catalog → Configurazione nativa
    │   (impostazioni "ADMX-backed" contrassegnate nel catalog)
    │
    ├─ Se presente in CSP (Configuration Service Provider) → OMA-URI custom
    │   Formato: ./Device/Vendor/MSFT/Policy/Config/{AreaName}/{PolicyName}
    │
    └─ Se non presente in CSP → Non gestibile via Intune
        (richiede script Proactive Remediations o packaged app)
```

---

## ADMX Templates Avanzati e Applicazioni di Terze Parti

### Struttura dei File ADMX

I file ADMX utilizzano uno schema XML standardizzato che definisce le impostazioni di policy attraverso elementi strutturati. La comprensione di questo schema è fondamentale per creare template personalizzati o per diagnosticare problemi con template di terze parti.

```xml
<?xml version="1.0" encoding="utf-8"?>
<policyDefinitions
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    revision="1.0"
    schemaVersion="1.0"
    xmlns="http://schemas.microsoft.com/GroupPolicy/2006/07/PolicyDefinitions">

  <!-- Namespace e super-category per il template -->
  <policyNamespaces>
    <target prefix="customApp" namespace="CustomApp.Policies.CustomApp" />
    <using prefix="windows" namespace="Microsoft.Policies.Windows" />
  </policyNamespaces>

  <resources minRequiredRevision="1.0" />

  <!-- Categorie visibili nel Group Policy Editor -->
  <categories>
    <category name="CustomAppCategory" displayName="$(string.CustomAppCategory)">
      <parentCategory ref="windows:System" />
    </category>
    <category name="SecuritySettings" displayName="$(string.SecuritySettings)">
      <parentCategory ref="CustomAppCategory" />
    </category>
  </categories>

  <!-- Definizione delle policy -->
  <policies>
    <policy name="EnableFeatureX"
            class="Machine"
            displayName="$(string.EnableFeatureX)"
            explainText="$(string.EnableFeatureX_Help)"
            presentation="$(presentation.EnableFeatureX)"
            key="SOFTWARE\Policies\CustomApp"
            valueName="EnableFeatureX">
      <parentCategory ref="SecuritySettings" />
      <supportedOn ref="windows:SUPPORTED_Windows10" />
      <enabledValue>
        <decimal value="1" />
      </enabledValue>
      <disabledValue>
        <decimal value="0" />
      </disabledValue>
      <elements>
        <decimal id="TimeoutValue" valueName="FeatureXTimeout"
                 required="true" minValue="10" maxValue="3600" />
        <enum id="LogLevel" valueName="FeatureXLogLevel" required="false">
          <item displayName="$(string.LogLevel_None)">
            <value><decimal value="0" /></value>
          </item>
          <item displayName="$(string.LogLevel_Verbose)">
            <value><decimal value="3" /></value>
          </item>
        </enum>
      </elements>
    </policy>
  </policies>
</policyDefinitions>
```

Il file ADML corrispondente contiene le stringhe localizzate:

```xml
<?xml version="1.0" encoding="utf-8"?>
<policyDefinitionResources
    xmlns:xsd="http://www.w3.org/2001/XMLSchema"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    revision="1.0"
    schemaVersion="1.0"
    xmlns="http://schemas.microsoft.com/GroupPolicy/2006/07/PolicyDefinitions">
  <displayName>Custom Application Policies</displayName>
  <description>Template ADMX personalizzato per Custom Application</description>
  <resources>
    <stringTable>
      <string id="CustomAppCategory">Custom Application</string>
      <string id="SecuritySettings">Security Settings</string>
      <string id="EnableFeatureX">Enable Feature X</string>
      <string id="EnableFeatureX_Help">Abilita la funzionalità X con timeout configurabile.
Quando abilitata, il sistema applica le impostazioni specificate.</string>
      <string id="LogLevel_None">Nessun logging</string>
      <string id="LogLevel_Verbose">Logging dettagliato</string>
    </stringTable>
    <presentationTable>
      <presentation id="EnableFeatureX">
        <decimalTextBox refId="TimeoutValue" defaultValue="300">Timeout (secondi):</decimalTextBox>
        <dropdownList refId="LogLevel" defaultItem="0">Livello di logging:</dropdownList>
      </presentation>
    </presentationTable>
  </resources>
</policyDefinitionResources>
```

### Template ADMX per Applicazioni Comuni

I produttori software forniscono template ADMX per gestire la configurazione delle proprie applicazioni via GPO. La tabella seguente elenca le fonti ufficiali:

| Applicazione | Sorgente ADMX | Percorso nel Central Store |
|-------------|---------------|---------------------------|
| Google Chrome | https://chromeenterprise.google/browser/download/ | `chrome.admx`, `google.admx` |
| Mozilla Firefox | https://github.com/mozilla/policy-templates/releases | `mozilla.admx`, `firefox.admx` |
| Microsoft Edge | Incluso nei Windows Administrative Templates | `msedge.admx` |
| Microsoft Office 365/2021 | Office Deployment Tool / Admin Template download | `office16.admx`, `outlk16.admx` |
| Adobe Acrobat Reader | https://www.adobe.com/devnet-docs/acrobatetk/tools/AdminGuide/ | `AcrobatReader.admx` |
| Zoom | https://support.zoom.us/hc/en-us/articles/360039100051 | `ZoomPolicies.admx` |
| Citrix Workspace | Citrix download center | `receiver.admx` |
| VMware Horizon | VMware download center | `vdm_agent.admx`, `vdm_client.admx` |

```powershell
# Script per aggiornare i template ADMX nel Central Store
function Update-CentralStoreTemplates {
    param(
        [string]$CentralStorePath = "\\$env:USERDNSDOMAIN\SYSVOL\$env:USERDNSDOMAIN\Policies\PolicyDefinitions",
        [string]$SourcePath
    )

    # Backup prima dell'aggiornamento
    $backupPath = "C:\GPOBackups\ADMX-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    New-Item -Path $backupPath -ItemType Directory -Force
    Copy-Item "$CentralStorePath\*" $backupPath -Recurse -Force

    # Copiare i nuovi template
    $admxFiles = Get-ChildItem $SourcePath -Filter "*.admx"
    $admxFiles | ForEach-Object {
        Copy-Item $_.FullName $CentralStorePath -Force
        Write-Output "Copiato: $($_.Name)"
    }

    # Copiare le localizzazioni
    $langFolders = Get-ChildItem $SourcePath -Directory | Where-Object { $_.Name -match "^[a-z]{2}-[A-Z]{2}$" }
    foreach ($lang in $langFolders) {
        $destLang = Join-Path $CentralStorePath $lang.Name
        if (-not (Test-Path $destLang)) {
            New-Item -Path $destLang -ItemType Directory -Force
        }
        Copy-Item "$($lang.FullName)\*.adml" $destLang -Force
        Write-Output "Localizzazione $($lang.Name): $(($lang | Get-ChildItem -Filter '*.adml').Count) file"
    }

    # Verifica integrità
    $totalAdmx = (Get-ChildItem $CentralStorePath -Filter "*.admx").Count
    $totalAdml_enUS = (Get-ChildItem "$CentralStorePath\en-US" -Filter "*.adml" -ErrorAction SilentlyContinue).Count
    Write-Output "`nCentral Store aggiornato:"
    Write-Output "  ADMX totali: $totalAdmx"
    Write-Output "  ADML en-US:  $totalAdml_enUS"
    Write-Output "  Backup:      $backupPath"
}
```

### Versioning dei Template ADMX tra Versioni Windows

Un problema critico è la compatibilità tra versioni dei template ADMX. I template di Windows Server 2022 contengono impostazioni non presenti nei template di Windows Server 2019 o Windows 10. La regola d'oro è: **il Central Store deve contenere i template della versione Windows più recente presente nell'ambiente**.

```powershell
# Verificare la versione dei template ADMX nel Central Store
$centralStore = "\\$env:USERDNSDOMAIN\SYSVOL\$env:USERDNSDOMAIN\Policies\PolicyDefinitions"
$admxFiles = Get-ChildItem $centralStore -Filter "*.admx"

$admxFiles | ForEach-Object {
    [xml]$xml = Get-Content $_.FullName
    $revision = $xml.policyDefinitions.revision
    [PSCustomObject]@{
        FileName   = $_.Name
        Revision   = $revision
        LastWrite  = $_.LastWriteTime
        SizeKB     = [math]::Round($_.Length / 1KB, 1)
    }
} | Sort-Object FileName | Format-Table -AutoSize

# Confrontare il numero di impostazioni tra versioni
$localCount = (Get-ChildItem "C:\Windows\PolicyDefinitions" -Filter "*.admx").Count
$centralCount = (Get-ChildItem $centralStore -Filter "*.admx").Count
Write-Output "Template locali: $localCount  |  Central Store: $centralCount"
if ($centralCount -lt $localCount) {
    Write-Warning "Il Central Store potrebbe essere obsoleto — meno template della macchina locale."
}
```

### Conflitti e Problemi Comuni con ADMX di Terze Parti

Quando si aggiungono template ADMX di terze parti al Central Store, possono verificarsi conflitti di namespace. I sintomi tipici sono errori in GPMC del tipo: "Namespace ... is already defined" oppure "Resource ... was not found".

```powershell
# Diagnosticare conflitti di namespace ADMX
$centralStore = "\\$env:USERDNSDOMAIN\SYSVOL\$env:USERDNSDOMAIN\Policies\PolicyDefinitions"
$namespaces = @{}

Get-ChildItem $centralStore -Filter "*.admx" | ForEach-Object {
    [xml]$xml = Get-Content $_.FullName
    $ns = $xml.policyDefinitions.policyNamespaces.target.namespace
    if ($ns) {
        if ($namespaces.ContainsKey($ns)) {
            Write-Warning "CONFLITTO: Namespace '$ns' definito in '$($_.Name)' e '$($namespaces[$ns])'"
        } else {
            $namespaces[$ns] = $_.Name
        }
    }
}

# Verificare che ogni ADMX abbia il corrispondente ADML
Get-ChildItem $centralStore -Filter "*.admx" | ForEach-Object {
    $admlName = $_.BaseName + ".adml"
    $admlPath = Join-Path "$centralStore\en-US" $admlName
    if (-not (Test-Path $admlPath)) {
        Write-Warning "ADMX senza ADML: $($_.Name) — manca $admlPath"
    }
}
```

### Creazione ADMX Personalizzati — Procedura Completa

Per applicazioni interne che non forniscono template ADMX, è possibile creare template personalizzati:

```powershell
# Generare uno scheletro ADMX/ADML per un'applicazione interna
function New-CustomADMXTemplate {
    param(
        [Parameter(Mandatory)][string]$AppName,
        [Parameter(Mandatory)][string]$RegistryKeyBase,
        [string]$OutputPath = "C:\Temp\CustomADMX"
    )

    $prefix = $AppName -replace '[^a-zA-Z0-9]', ''
    $namespace = "$prefix.Policies.$prefix"

    New-Item $OutputPath -ItemType Directory -Force | Out-Null
    New-Item "$OutputPath\en-US" -ItemType Directory -Force | Out-Null

    # Generare ADMX
    $admxContent = @"
<?xml version="1.0" encoding="utf-8"?>
<policyDefinitions revision="1.0" schemaVersion="1.0"
    xmlns="http://schemas.microsoft.com/GroupPolicy/2006/07/PolicyDefinitions">
  <policyNamespaces>
    <target prefix="$prefix" namespace="$namespace" />
    <using prefix="windows" namespace="Microsoft.Policies.Windows" />
  </policyNamespaces>
  <resources minRequiredRevision="1.0" />
  <categories>
    <category name="${prefix}Category" displayName="`$(string.${prefix}Category)">
      <parentCategory ref="windows:System" />
    </category>
  </categories>
  <policies>
    <!-- Aggiungere le policy qui -->
    <policy name="EnableApp" class="Machine"
            displayName="`$(string.EnableApp)"
            explainText="`$(string.EnableApp_Help)"
            key="$RegistryKeyBase" valueName="Enabled">
      <parentCategory ref="${prefix}Category" />
      <supportedOn ref="windows:SUPPORTED_Windows10" />
      <enabledValue><decimal value="1" /></enabledValue>
      <disabledValue><decimal value="0" /></disabledValue>
    </policy>
  </policies>
</policyDefinitions>
"@

    # Generare ADML
    $admlContent = @"
<?xml version="1.0" encoding="utf-8"?>
<policyDefinitionResources revision="1.0" schemaVersion="1.0"
    xmlns="http://schemas.microsoft.com/GroupPolicy/2006/07/PolicyDefinitions">
  <displayName>$AppName Policies</displayName>
  <description>Administrative Template for $AppName</description>
  <resources>
    <stringTable>
      <string id="${prefix}Category">$AppName</string>
      <string id="EnableApp">Enable $AppName</string>
      <string id="EnableApp_Help">Controls whether $AppName is enabled.</string>
    </stringTable>
  </resources>
</policyDefinitionResources>
"@

    Set-Content "$OutputPath\$prefix.admx" $admxContent -Encoding UTF8
    Set-Content "$OutputPath\en-US\$prefix.adml" $admlContent -Encoding UTF8
    Write-Output "Template ADMX generato in: $OutputPath"
    Write-Output "  ADMX: $prefix.admx"
    Write-Output "  ADML: en-US\$prefix.adml"
    Write-Output "Copiare nel Central Store per rendere disponibile in GPMC."
}

# Esempio
New-CustomADMXTemplate -AppName "InternalCRM" -RegistryKeyBase "SOFTWARE\Policies\InternalCRM"
```

---

## Administrative Templates vs Security Settings vs Software Restriction

Le Group Policy comprendono tre macro-aree di configurazione spesso confuse tra loro. Ciascuna ha un motore di elaborazione, un formato di storage e un comportamento distinti.

### Confronto Strutturale

| Aspetto | Administrative Templates | Security Settings | Software Restriction / AppLocker |
|---------|-------------------------|-------------------|----------------------------------|
| **Storage** | `Registry.pol` (file binario) | `GptTmpl.inf` (testo INI) | `Registry.pol` + oggetti LDAP |
| **CSE** | Registry CSE | Security CSE | Software Installation CSE / AppLocker CSE |
| **Area Registry** | `HKLM\SOFTWARE\Policies\` `HKCU\SOFTWARE\Policies\` | Varia (SAM, LSA, Security) | `HKLM\SOFTWARE\Policies\Microsoft\Windows\SrpV2` |
| **Tattooing** | No (anti-tattoo) | Dipende dall'impostazione | No (anti-tattoo) |
| **Rielaborazione** | Solo se GPO cambiato | Ogni 16 ore anche se invariato | Solo se GPO cambiato |
| **Slow link** | Elaborato | Elaborato | Elaborato |
| **File ADMX** | Sì (definiscono le impostazioni) | No (schema fisso) | No (schema fisso) |

### Administrative Templates

Le Administrative Templates controllano chiavi di registro sotto `HKLM\SOFTWARE\Policies\` e `HKCU\SOFTWARE\Policies\`. Ogni impostazione corrisponde a un valore di registro. Quando il GPO viene rimosso, il valore viene cancellato (anti-tattoo). Le impostazioni sono definite dai file ADMX e sono estensibili — qualsiasi applicazione che legge le proprie configurazioni dal registro può essere gestita tramite un template ADMX personalizzato.

### Security Settings

Le Security Settings includono: Account Policies (password, lockout, Kerberos), Local Policies (audit, user rights, security options), Event Log, Restricted Groups, System Services, Registry ACLs, File System ACLs, Windows Firewall. Queste impostazioni sono elaborate dalla Security CSE e scritte in aree "native" del sistema (non solo nel registro). La Security CSE ha un comportamento unico: rielabora le impostazioni ogni 16 ore anche se il GPO non è cambiato, correggendo automaticamente drift manuali.

### Software Restriction Policies (SRP) e AppLocker

Le SRP (legacy) e AppLocker (Windows 7+) controllano quali eseguibili, script, installer e DLL possono essere eseguiti. AppLocker è il successore delle SRP e offre regole basate su publisher, path e file hash con condizioni più granulari. Da Windows 10 1903+, Microsoft raccomanda Windows Defender Application Control (WDAC) come evoluzione di AppLocker per nuovi deployment.

> **Approfondimento:** La distinzione è operativamente importante perché le Security Settings e le Administrative Templates hanno cicli di rielaborazione diversi. Un drift nelle Security Settings (es. qualcuno modifica manualmente i User Rights Assignment) viene autocorretto entro 16 ore. Un drift nelle Administrative Templates (es. modifica manuale di una chiave di registro sotto `Policies\`) viene corretto solo al prossimo background refresh se il GPO risulta modificato — altrimenti la Registry CSE salta l'elaborazione per ottimizzazione.

---

## Security Baselines e CIS Benchmarks

### Microsoft Security Compliance Toolkit (SCT)

Microsoft fornisce il Security Compliance Toolkit (SCT), un set gratuito di strumenti e GPO preconfigurati con le impostazioni di sicurezza raccomandate per ogni versione di Windows e Windows Server. Le baseline includono GPO importabili, file di documentazione e script di analisi.

```powershell
# Scaricare e applicare una Security Baseline Microsoft
# 1. Download da https://www.microsoft.com/en-us/download/details.aspx?id=55319
# 2. Estrarre l'archivio, navigare nella cartella della baseline

# Importare la baseline come GPO nel dominio
$baselinePath = "C:\SecurityBaseline\Windows11-v24H2"
$gpoBackups = Get-ChildItem "$baselinePath\GPOs" -Directory

foreach ($gpoDir in $gpoBackups) {
    $gpoName = "SCT - " + $gpoDir.Name
    Import-GPO -BackupGpoName $gpoDir.Name -Path "$baselinePath\GPOs" -TargetName $gpoName -CreateIfNeeded
    Write-Output "Importata baseline GPO: $gpoName"
}

# Collegare le GPO importate alla OU di test
$testOU = "OU=SecurityTest,DC=contoso,DC=com"
Get-GPO -All | Where-Object { $_.DisplayName -like "SCT -*" } | ForEach-Object {
    New-GPLink -Name $_.DisplayName -Target $testOU -LinkEnabled Yes -ErrorAction SilentlyContinue
    Write-Output "Collegata '$($_.DisplayName)' a $testOU"
}
```

### Policy Analyzer

Il Policy Analyzer (incluso nell'SCT) permette di confrontare GPO esistenti con le baseline raccomandate, identificando le differenze:

```powershell
# Esportare la configurazione corrente per il confronto
# Policy Analyzer utilizza file .PolicyRules per le baseline
# e supporta il confronto tra:
# - GPO di dominio vs. baseline Microsoft
# - GPO di dominio vs. CIS Benchmark
# - Due GPO diverse tra loro
# - Registry locale vs. baseline

# Esportare un GPO come XML per analisi offline
Get-GPO -All | Where-Object { $_.DisplayName -like "SEC -*" } | ForEach-Object {
    $reportPath = "C:\Reports\GPO-Export\$($_.DisplayName -replace '[^\w]', '_').xml"
    Get-GPOReport -Guid $_.Id -ReportType XML -Path $reportPath
}
```

### CIS Benchmarks

I CIS (Center for Internet Security) Benchmarks forniscono raccomandazioni di sicurezza dettagliate per Windows, suddivise in due livelli:

- **Level 1 (L1)**: Impostazioni di sicurezza essenziali che possono essere applicate nella maggior parte degli ambienti senza impatto significativo sulla funzionalità. Raccomandate per tutte le organizzazioni.
- **Level 2 (L2)**: Impostazioni più restrittive adatte ad ambienti ad alta sicurezza. Possono limitare alcune funzionalità — richiedono testing approfondito.

```
Impostazioni CIS L1 critiche per Windows 11 Enterprise (estratto):

Account Policies:
├── Password Policy:
│   ├── Enforce password history: 24 passwords
│   ├── Maximum password age: 365 days
│   ├── Minimum password age: 1 day
│   ├── Minimum password length: 14 characters
│   └── Password must meet complexity: Enabled
├── Account Lockout:
│   ├── Account lockout threshold: 5 attempts (o meno)
│   ├── Account lockout duration: 15 minutes (o più)
│   └── Reset lockout counter: 15 minutes (o più)

Local Policies → Security Options:
├── Accounts: Administrator account status: Disabled
├── Accounts: Guest account status: Disabled
├── Accounts: Rename administrator account: (nome personalizzato)
├── Accounts: Rename guest account: (nome personalizzato)
├── Interactive logon: Don't display last username: Enabled
├── Interactive logon: Machine inactivity limit: 900 seconds (o meno)
├── Network access: Do not allow anonymous enum of SAM accounts: Enabled
├── Network access: Do not allow anonymous enum of SAM accounts and shares: Enabled
├── Network access: Restrict anonymous access to Named Pipes and Shares: Enabled
├── Network security: LAN Manager authentication level: NTLMv2 only
├── Network security: LDAP client signing requirements: Negotiate signing
└── User Account Control: Behavior of elevation prompt for admins: Prompt for consent

Advanced Audit Policy:
├── Account Logon: Audit Credential Validation: Success and Failure
├── Account Management: Audit Security Group Management: Success
├── Account Management: Audit User Account Management: Success and Failure
├── Logon/Logoff: Audit Logon: Success and Failure
├── Logon/Logoff: Audit Other Logon/Logoff Events: Success and Failure
├── Object Access: Audit Removable Storage: Success and Failure
├── Policy Change: Audit Policy Change: Success and Failure
├── Privilege Use: Audit Sensitive Privilege Use: Success and Failure
└── System: Audit Security System Extension: Success
```

```powershell
# Script per verificare la conformità di un computer con CIS L1
function Test-CISComplianceL1 {
    $results = @()

    # Verifica: Interactive logon - Machine inactivity limit
    $inactivity = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name "InactivityTimeoutSecs" -ErrorAction SilentlyContinue).InactivityTimeoutSecs
    $results += [PSCustomObject]@{
        Check      = "Machine inactivity limit <= 900s"
        Current    = $inactivity
        Expected   = "<=900"
        Compliant  = ($null -ne $inactivity -and $inactivity -le 900)
    }

    # Verifica: LAN Manager authentication level
    $lmLevel = (Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name "LmCompatibilityLevel" -ErrorAction SilentlyContinue).LmCompatibilityLevel
    $results += [PSCustomObject]@{
        Check      = "NTLMv2 only (LmCompatibilityLevel = 5)"
        Current    = $lmLevel
        Expected   = 5
        Compliant  = ($lmLevel -eq 5)
    }

    # Verifica: SMBv1 disabilitato
    $smb1 = (Get-SmbServerConfiguration).EnableSMB1Protocol
    $results += [PSCustomObject]@{
        Check      = "SMBv1 disabled"
        Current    = $smb1
        Expected   = $false
        Compliant  = ($smb1 -eq $false)
    }

    # Verifica: Windows Firewall abilitato per tutti i profili
    $fwProfiles = Get-NetFirewallProfile
    foreach ($profile in $fwProfiles) {
        $results += [PSCustomObject]@{
            Check      = "Firewall $($profile.Name) profile enabled"
            Current    = $profile.Enabled
            Expected   = $true
            Compliant  = ($profile.Enabled -eq $true)
        }
    }

    # Verifica: Audit policy per Logon Events
    $auditLogon = auditpol /get /subcategory:"Logon" /r 2>$null | ConvertFrom-Csv
    $results += [PSCustomObject]@{
        Check      = "Audit Logon: Success and Failure"
        Current    = $auditLogon.'Inclusion Setting'
        Expected   = "Success and Failure"
        Compliant  = ($auditLogon.'Inclusion Setting' -eq "Success and Failure")
    }

    # Verifica: UAC abilitato
    $enableLUA = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name "EnableLUA" -ErrorAction SilentlyContinue).EnableLUA
    $results += [PSCustomObject]@{
        Check      = "UAC enabled (EnableLUA = 1)"
        Current    = $enableLUA
        Expected   = 1
        Compliant  = ($enableLUA -eq 1)
    }

    # Verifica: Remote Desktop NLA
    $nla = (Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" -Name "UserAuthentication" -ErrorAction SilentlyContinue).UserAuthentication
    $results += [PSCustomObject]@{
        Check      = "RDP Network Level Authentication"
        Current    = $nla
        Expected   = 1
        Compliant  = ($nla -eq 1)
    }

    $totalChecks = $results.Count
    $compliant = ($results | Where-Object { $_.Compliant }).Count
    Write-Output "`n=== CIS L1 Compliance Report ==="
    Write-Output "Computer: $env:COMPUTERNAME"
    Write-Output "Conformi: $compliant / $totalChecks ($([math]::Round($compliant/$totalChecks*100,1))%)`n"
    $results | Format-Table -AutoSize
}

Test-CISComplianceL1
```

---

## Advanced Audit Policy Configuration

### Panoramica

Le Advanced Audit Policy (introdotte in Windows Vista / Server 2008) sostituiscono le legacy Basic Audit Policies con un sistema di subcategorie granulari. Mentre le Basic Audit Policies offrono solo 9 categorie (Account Logon, Account Management, DS Access, Logon/Logoff, Object Access, Policy Change, Privilege Use, System, Detailed Tracking), le Advanced Audit Policies suddividono queste in oltre 50 subcategorie, permettendo un controllo fine su cosa viene registrato nel Security Event Log.

Riferimento: https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/advanced-security-audit-policy-settings (consultato: 2026-05-23)

### Configurazione via GPO

```
Computer Configuration → Policies → Windows Settings → Security Settings
    → Advanced Audit Policy Configuration → Audit Policies:

    Account Logon:
    ├── Audit Credential Validation: Success, Failure
    ├── Audit Kerberos Authentication Service: Success, Failure
    ├── Audit Kerberos Service Ticket Operations: Success, Failure
    └── Audit Other Account Logon Events: Success, Failure

    Account Management:
    ├── Audit Application Group Management: Success, Failure
    ├── Audit Computer Account Management: Success
    ├── Audit Distribution Group Management: Success
    ├── Audit Other Account Management Events: Success
    ├── Audit Security Group Management: Success, Failure
    └── Audit User Account Management: Success, Failure

    DS Access (Domain Controllers):
    ├── Audit Detailed Directory Service Replication: Failure
    ├── Audit Directory Service Access: Success, Failure
    ├── Audit Directory Service Changes: Success, Failure
    └── Audit Directory Service Replication: Failure

    Logon/Logoff:
    ├── Audit Account Lockout: Failure
    ├── Audit Group Membership: Success
    ├── Audit Logoff: Success
    ├── Audit Logon: Success, Failure
    ├── Audit Other Logon/Logoff Events: Success, Failure
    └── Audit Special Logon: Success

    Object Access:
    ├── Audit File Share: Success, Failure
    ├── Audit File System: Success, Failure (richiede SACL)
    ├── Audit Registry: Success, Failure (richiede SACL)
    └── Audit Removable Storage: Success, Failure

    Policy Change:
    ├── Audit Audit Policy Change: Success, Failure
    ├── Audit Authentication Policy Change: Success
    └── Audit MPSSVC Rule-Level Policy Change: Success, Failure

    Privilege Use:
    └── Audit Sensitive Privilege Use: Success, Failure

    System:
    ├── Audit IPsec Driver: Success, Failure
    ├── Audit Other System Events: Success, Failure
    ├── Audit Security State Change: Success, Failure
    ├── Audit Security System Extension: Success, Failure
    └── Audit System Integrity: Success, Failure
```

### SACL (System Access Control List)

Per le subcategorie di Object Access (File System, Registry), l'abilitazione dell'audit policy non è sufficiente. E' necessario configurare anche una **SACL** sull'oggetto da monitorare (file, cartella, chiave di registro). La SACL specifica quali operazioni (lettura, scrittura, eliminazione) e per quali utenti/gruppi generare eventi di audit.

```powershell
# Configurare una SACL su una cartella per auditare l'accesso
$folderPath = "C:\SensitiveData"
$acl = Get-Acl $folderPath

# Creare una regola di audit: Everyone, Write/Delete, Success and Failure
$auditRule = New-Object System.Security.AccessControl.FileSystemAuditRule(
    "Everyone",
    "Write,Delete,ChangePermissions",
    "ContainerInherit,ObjectInherit",
    "None",
    "Success,Failure"
)
$acl.AddAuditRule($auditRule)
Set-Acl $folderPath $acl

# Verificare la SACL configurata
(Get-Acl $folderPath -Audit).Audit | Format-Table IdentityReference, FileSystemRights, AuditFlags
```

### Auditpol.exe — Gestione da Riga di Comando

`Auditpol.exe` è lo strumento nativo per leggere e configurare le Advanced Audit Policies localmente. E' particolarmente utile per diagnosticare se la policy effettiva corrisponde a quanto configurato nel GPO.

```powershell
# Visualizzare tutte le subcategorie di audit e il loro stato
auditpol /get /category:*

# Visualizzare solo una categoria specifica
auditpol /get /category:"Logon/Logoff"

# Formato CSV per analisi programmatica
auditpol /get /category:* /r | ConvertFrom-Csv |
    Where-Object { $_.'Inclusion Setting' -ne 'No Auditing' } |
    Format-Table 'Subcategory', 'Inclusion Setting' -AutoSize

# Confrontare la policy effettiva con la policy GPO
# La policy effettiva è in: auditpol /get
# La policy GPO è nel file: GptTmpl.inf del GPO → sezione [Event Audit]
# Se divergono, verificare che "Audit: Force audit policy subcategory settings"
# sia abilitato (Computer Config → Security Options)

# Esportare la configurazione audit corrente (per backup/confronto)
auditpol /backup /file:C:\Temp\audit-backup.csv

# Ripristinare da backup
auditpol /restore /file:C:\Temp\audit-backup.csv
```

> **Errore comune:** Le Basic Audit Policies (legacy, 9 categorie) e le Advanced Audit Policies (50+ subcategorie) possono entrare in conflitto. Se entrambe sono configurate, le Basic Audit Policies prevalgono e sovrascrivono le Advanced. Per garantire che le Advanced Audit Policies funzionino, abilitare: `Computer Configuration → Security Options → Audit: Force audit policy subcategory settings (Windows Vista or later) to override audit policy category settings: Enabled`.

---

## Resultant Set of Policy (RSoP) — Analisi Avanzata

### Panoramica RSoP

Il Resultant Set of Policy (RSoP) è lo strumento diagnostico fondamentale per determinare l'effettivo set di policy applicato a un utente o computer specifico. RSoP analizza tutti i GPO applicabili, risolve conflitti, applica il filtraggio e produce un report finale che mostra esattamente quale impostazione è attiva e da quale GPO proviene.

### Modalità di RSoP

RSoP opera in due modalità:

1. **Logging Mode** — Analizza le policy già applicate su un computer/utente esistente. Usa dati reali dal client. Strumenti: `gpresult`, `Get-GPResultantSetOfPolicy`.

2. **Planning Mode** — Simula l'applicazione delle policy per un computer/utente in uno scenario ipotetico (es. "cosa succederebbe se spostassi l'utente Mario nella OU Finance?"). Strumenti: `rsop.msc` in planning mode, `Get-GPResultantSetOfPolicy -ReportType Planning`.

### gpresult — Uso Avanzato

```powershell
# Report completo in HTML (metodo più informativo)
gpresult /H C:\Temp\gpresult-completo.html /F

# Report per solo computer (senza user policies)
gpresult /H C:\Temp\gpresult-computer.html /SCOPE COMPUTER

# Report per solo utente (senza computer policies)
gpresult /H C:\Temp\gpresult-user.html /SCOPE USER

# Report su macchina remota per un utente specifico
gpresult /S SERVER01 /USER contoso\admin.rossi /H C:\Temp\gpresult-remote.html

# Report testuale con verbose
gpresult /R /V

# Visualizzare solo i GPO applicati (output rapido)
gpresult /R /SCOPE COMPUTER 2>$null | Select-String "Applied Group Policy|Gruppo"

# Report XML per analisi programmatica
gpresult /X C:\Temp\gpresult.xml /F
```

### Analisi Programmatica del RSoP

```powershell
# Estrarre informazioni specifiche dal report XML di gpresult
function Get-GPResultAnalysis {
    param([string]$ComputerName = $env:COMPUTERNAME)

    $xmlPath = "C:\Temp\gpresult-$ComputerName.xml"
    gpresult /S $ComputerName /X $xmlPath /F 2>$null

    [xml]$xml = Get-Content $xmlPath
    $ns = @{rsop = "http://www.microsoft.com/GroupPolicy/Rsop"}

    # GPO applicati al computer
    $computerGPOs = $xml.Rsop.ComputerResults.GPO | ForEach-Object {
        [PSCustomObject]@{
            Name          = $_.Name
            Enabled       = $_.Enabled
            AccessDenied  = $_.AccessDenied
            FilterAllowed = $_.FilterAllowed
            Version       = "$($_.VersionDirectory)/$($_.VersionSysvol)"
            Link          = $_.Link.SOMPath
            LinkOrder     = $_.Link.SOMOrder
        }
    }

    # GPO applicati all'utente
    $userGPOs = $xml.Rsop.UserResults.GPO | ForEach-Object {
        [PSCustomObject]@{
            Name          = $_.Name
            Enabled       = $_.Enabled
            AccessDenied  = $_.AccessDenied
            FilterAllowed = $_.FilterAllowed
            Version       = "$($_.VersionDirectory)/$($_.VersionSysvol)"
            Link          = $_.Link.SOMPath
            LinkOrder     = $_.Link.SOMOrder
        }
    }

    Write-Output "=== GPO Computer ==="
    $computerGPOs | Format-Table -AutoSize
    Write-Output "`n=== GPO Utente ==="
    $userGPOs | Format-Table -AutoSize

    # Identificare GPO con version mismatch (AD vs SYSVOL)
    $allGPOs = @($computerGPOs) + @($userGPOs)
    $mismatched = $allGPOs | Where-Object {
        $v = $_.Version -split "/"
        $v[0] -ne $v[1]
    }
    if ($mismatched) {
        Write-Warning "GPO con version mismatch (possibile problema replica SYSVOL):"
        $mismatched | Format-Table Name, Version -AutoSize
    }
}

Get-GPResultAnalysis -ComputerName "WORKSTATION01"
```

### RSoP in Planning Mode

```powershell
# Simulare l'applicazione delle policy per uno scenario ipotetico
# "Cosa succede se l'utente admin.rossi si sposta nella OU Finance?"

Get-GPResultantSetOfPolicy `
    -User "contoso\admin.rossi" `
    -Computer "contoso\WORKSTATION01" `
    -TargetOU "OU=Finance,DC=contoso,DC=com" `
    -ReportType HTML `
    -Path "C:\Temp\rsop-planning.html"

# Simulazione via GPMC:
# GPMC → Group Policy Modeling (Planning) → tasto destro → "Group Policy Modeling Wizard"
# Permette di specificare:
# - Computer/OU del computer
# - Utente/OU dell'utente
# - Sito
# - WMI Filters simulati
# - Slow link detection
# - Loopback processing mode
```

### Group Policy Results vs Group Policy Modeling

| Aspetto | Group Policy Results | Group Policy Modeling |
|---------|---------------------|----------------------|
| Dati | Reali (dal client) | Simulati (dal DC) |
| Requisiti | Computer acceso e raggiungibile | Solo accesso al DC |
| Scenari ipotici | No | Sì |
| Accuratezza | Massima (dati reali) | Approssimata |
| WMI Filters | Valutati sul client | Simulati |
| Preference Items | Visibili | Non visibili |

---

## gpresult /h — Ricetta di Triage

### Struttura del Report HTML

Il report HTML generato da `gpresult /h` è lo strumento diagnostico più completo per l'analisi delle Group Policy. Sapere leggere questo report è una competenza operativa fondamentale. Il report è strutturato in sezioni ben definite:

```
Report gpresult /h — Sezioni principali:

1. COMPUTER CONFIGURATION SUMMARY
   ├── General: Last time GP was applied, DC contattato, link speed
   ├── Applied GPOs: Lista ordinata per precedenza
   ├── Denied GPOs: GPO non applicati (con motivo)
   └── Component Status: Tempo di elaborazione per ogni CSE

2. USER CONFIGURATION SUMMARY
   ├── General: Utente, dominio, DC contattato, profilo
   ├── Applied GPOs: Lista ordinata per precedenza
   ├── Denied GPOs: GPO non applicati (con motivo)
   └── Component Status: Tempo di elaborazione per ogni CSE

3. COMPUTER DETAILS
   ├── Policies → Administrative Templates (impostazioni attive)
   ├── Policies → Windows Settings → Security Settings
   ├── Preferences → (se presenti)
   └── Per ogni impostazione: "Winning GPO" indicato

4. USER DETAILS
   ├── Policies → Administrative Templates
   ├── Policies → Windows Settings
   ├── Preferences →
   └── Per ogni impostazione: "Winning GPO" indicato
```

### Procedura di Triage Step-by-Step

**Step 1 — Generare il report**

```powershell
# Generare il report sulla macchina target
gpresult /H C:\Temp\triage-$(hostname).html /F

# Per macchina remota con utente specifico
gpresult /S WORKSTATION01 /USER contoso\mario.rossi /H C:\Temp\triage-WS01.html /F
```

**Step 2 — Verificare i GPO applicati vs negati**

Aprire il report HTML nel browser. Nella sezione "Group Policy Objects" (sia Computer sia User), verificare:

- **Applied GPOs**: GPO effettivamente applicati, elencati in ordine di precedenza. Il GPO con il numero di Link Order più basso e posizione gerarchica più profonda ha la priorità effettiva più alta.
- **Denied GPOs**: GPO non applicati. Per ogni GPO negato, il report specifica il motivo:
  - `Denied (Security)` → Il target non ha i permessi Read + Apply. Causa frequente: problema MS16-072.
  - `Denied (WMI Filter)` → La query WMI ha restituito risultati vuoti.
  - `Denied (Empty)` → Il GPO non contiene impostazioni nella sezione rilevante (Computer o User).
  - `Denied (Disabled)` → La sezione Computer o User del GPO è disabilitata.
  - `Denied (Unknown Reason)` → Problema di connettività o errore CSE.

**Step 3 — Controllare il Component Status**

La sezione "Component Status" mostra il tempo di elaborazione di ogni CSE in millisecondi. Valori normali:

| CSE | Tempo Normale | Allarme |
|-----|--------------|---------|
| Registry (Administrative Templates) | < 500 ms | > 2000 ms |
| Security | < 1000 ms | > 5000 ms |
| Scripts | < 2000 ms | > 10000 ms |
| Group Policy Preferences | < 1000 ms | > 5000 ms |
| Folder Redirection | < 2000 ms | > 10000 ms |

**Step 4 — Identificare il Winning GPO per un'impostazione specifica**

Nella sezione "Details" del report, espandere l'albero delle impostazioni. Ogni policy configurata mostra il "Winning GPO" — il GPO che ha effettivamente determinato il valore dell'impostazione. Se un'impostazione ha un valore inatteso, verificare quale GPO ha "vinto" e controllare il Link Order e la posizione gerarchica di quel GPO.

**Step 5 — Verificare version mismatch AD vs SYSVOL**

Nel report, ogni GPO applicato mostra due numeri di versione: `Versione AD` e `Versione SYSVOL`. Se questi differiscono, c'è un problema di replica DFS-R — il contenuto del GPO nel database AD non corrisponde ai file in SYSVOL.

```powershell
# Script automatizzato per estrarre gli elementi chiave dal report XML
function Invoke-GPResultTriage {
    param(
        [string]$ComputerName = $env:COMPUTERNAME,
        [string]$UserName
    )

    $xmlPath = [System.IO.Path]::GetTempFileName() -replace '\.tmp$', '.xml'
    $gpArgs = "/S $ComputerName /X `"$xmlPath`" /F"
    if ($UserName) { $gpArgs += " /USER $UserName" }
    Start-Process gpresult -ArgumentList $gpArgs -Wait -NoNewWindow 2>$null

    [xml]$xml = Get-Content $xmlPath

    Write-Output "=== TRIAGE GPO — $ComputerName ==="
    Write-Output "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss UTC' -AsUTC)"

    # Computer GPOs
    Write-Output "`n--- COMPUTER: GPO Applicati ---"
    $xml.Rsop.ComputerResults.GPO |
        Where-Object { $_.IsValid -eq 'true' -and $_.FilterAllowed -ne 'false' } |
        ForEach-Object { Write-Output "  [OK] $($_.Name) (Link: $($_.Link.SOMPath))" }

    Write-Output "`n--- COMPUTER: GPO Negati ---"
    $xml.Rsop.ComputerResults.GPO |
        Where-Object { $_.FilterAllowed -eq 'false' -or $_.AccessDenied -eq 'true' } |
        ForEach-Object {
            $reason = if ($_.AccessDenied -eq 'true') { "Security" }
                      elseif ($_.FilterAllowed -eq 'false') { "WMI/Filter" }
                      else { "Unknown" }
            Write-Output "  [DENIED:$reason] $($_.Name)"
        }

    # Version mismatch
    Write-Output "`n--- VERSION MISMATCH ---"
    $mismatch = $xml.Rsop.ComputerResults.GPO + $xml.Rsop.UserResults.GPO |
        Where-Object { $_.VersionDirectory -ne $_.VersionSysvol }
    if ($mismatch) {
        $mismatch | ForEach-Object {
            Write-Warning "  $($_.Name): AD=$($_.VersionDirectory) SYSVOL=$($_.VersionSysvol)"
        }
    } else {
        Write-Output "  Nessun mismatch rilevato."
    }

    Remove-Item $xmlPath -ErrorAction SilentlyContinue
}

Invoke-GPResultTriage -ComputerName "WORKSTATION01" -UserName "contoso\mario.rossi"
```

---

## GPO e Microsoft Intune — Gestione Ibrida

### Coesistenza GPO e Intune

Negli ambienti moderni, molte organizzazioni gestiscono gli endpoint sia tramite GPO tradizionali (per dispositivi domain-joined on-premises) sia tramite Microsoft Intune (per dispositivi cloud-managed o hybrid Azure AD joined). La coesistenza richiede attenzione per evitare conflitti tra le due fonti di configurazione.

### Ordine di Prevalenza

Quando un dispositivo riceve configurazioni sia da GPO sia da Intune, il comportamento dipende dalla configurazione di **MDM wins over GP**:

```
Computer Configuration → Administrative Templates → System → Group Policy
    → Configure Group Policy and MDM policy processing:
        - MDM policy wins: Le impostazioni di Intune prevalgono sulle GPO
        - Group Policy wins: Le GPO prevalgono su Intune (default)
```

```powershell
# Verificare se MDM wins over GP è configurato
$mdmWins = Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\CurrentVersion\MDM" `
    -Name "EnableMDMAutoenrollment" -ErrorAction SilentlyContinue

# Verificare lo stato di enrollment MDM
$enrollmentInfo = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Enrollments\*" `
    -Name "ProviderId" -ErrorAction SilentlyContinue
$enrollmentInfo | Where-Object { $_.ProviderId -eq "MS DM Server" }
```

### Group Policy Analytics in Intune

Microsoft Intune include **Group Policy Analytics**, uno strumento che analizza le GPO esistenti e indica quali impostazioni hanno un equivalente in Intune:

```
Flusso di migrazione GPO → Intune:
1. Esportare il GPO come report XML (Get-GPOReport)
2. Caricare l'XML nel portale Intune → Devices → Group Policy analytics
3. Intune analizza e categorizza ogni impostazione:
   - Supportata in MDM (mappatura diretta)
   - Parzialmente supportata (funzionalità simile via OMA-URI)
   - Non supportata in MDM
   - Deprecata
4. Creare un profilo di configurazione Intune dalle impostazioni supportate
```

```powershell
# Esportare le GPO per l'analisi in Intune
$exportPath = "C:\GPOExport-Intune"
New-Item -Path $exportPath -ItemType Directory -Force

Get-GPO -All | ForEach-Object {
    $safeDisplayName = $_.DisplayName -replace '[\\/:*?"<>|]', '_'
    Get-GPOReport -Guid $_.Id -ReportType XML -Path "$exportPath\$safeDisplayName.xml"
}

Write-Output "Esportati $(Get-ChildItem $exportPath -Filter '*.xml' | Measure-Object | Select-Object -ExpandProperty Count) GPO"
Write-Output "Caricare i file XML su Endpoint Manager → Group Policy analytics"
```

### OMA-URI Custom per Impostazioni GPO Senza Equivalente Intune

Per le impostazioni GPO che non hanno un equivalente nativo in Intune, è possibile utilizzare profili OMA-URI custom che scrivono direttamente le stesse chiavi di registro delle GPO:

```
Endpoint Manager → Devices → Configuration profiles → Create profile:
    Platform: Windows 10 and later
    Profile type: Templates → Custom

OMA-URI Setting esempio (equivalente di una GPO registry policy):
    Name: Disable USB Storage
    OMA-URI: ./Device/Vendor/MSFT/Policy/Config/Storage/RemovableDiskDenyWriteAccess
    Data type: Integer
    Value: 1

Per impostazioni registry arbitrarie:
    OMA-URI: ./Device/Vendor/MSFT/Policy/Config/
             AdmPolicies~Policy~System/DisableRegistryTools
```

---

## Intune ADMX Ingestion

### ADMX-Backed Policies nel Settings Catalog

A partire da Intune 2305+, Microsoft ha introdotto il supporto per le **ADMX-backed policies** direttamente nel Settings Catalog di Intune. Questo meccanismo permette di configurare le stesse impostazioni degli Administrative Templates GPO senza bisogno di OMA-URI custom.

Riferimento: https://learn.microsoft.com/en-us/mem/intune/configuration/administrative-templates-import-custom (consultato: 2026-05-23)

### Importazione di ADMX Personalizzati in Intune

Per le applicazioni che non sono nel catalogo predefinito di Intune (es. Chrome, Firefox, applicazioni interne), è possibile importare file ADMX personalizzati:

```
Intune Admin Center → Devices → Configuration → Import ADMX:

1. Caricare il file .admx
2. Caricare il file .adml corrispondente (en-US obbligatorio)
3. Intune analizza il file e crea le impostazioni nel Settings Catalog
4. Le impostazioni appaiono sotto "Administrative Templates (imported)"
```

### Mapping OMA-URI per Policy ADMX

Le policy ADMX-backed in Intune utilizzano il CSP `Policy` con il seguente formato OMA-URI:

```
./Device/Vendor/MSFT/Policy/Config/{AreaName}/{PolicyName}

Dove:
- AreaName = nome della categoria ADMX (es. "Chrome~Policy~googlechrome~Startup")
- PolicyName = nome della policy ADMX (es. "RestoreOnStartup")
```

Per policy di tipo stringa, il valore deve essere wrappato in XML ADMX-compatibile:

```xml
<!-- Esempio: configurare la homepage di Chrome via OMA-URI -->
<enabled/>
<data id="RestoreOnStartupURLs" value="https://intranet.contoso.com"/>
```

```powershell
# Generare la mappatura OMA-URI per tutte le policy in un file ADMX
function Get-ADMXToOMAURIMapping {
    param([Parameter(Mandatory)][string]$AdmxFilePath)

    [xml]$admx = Get-Content $AdmxFilePath
    $ns = $admx.policyDefinitions.policyNamespaces.target
    $prefix = $ns.prefix
    $namespace = $ns.namespace

    $admx.policyDefinitions.policies.policy | ForEach-Object {
        $policy = $_
        $class = $policy.class  # Machine o User
        $scope = if ($class -eq 'Machine') { './Device' } else { './User' }
        $category = ($policy.parentCategory.ref -replace ':', '~')

        [PSCustomObject]@{
            PolicyName  = $policy.name
            Class       = $class
            RegistryKey = $policy.key
            ValueName   = $policy.valueName
            OMA_URI     = "$scope/Vendor/MSFT/Policy/Config/$namespace~$category/$($policy.name)"
        }
    } | Format-Table -AutoSize
}

# Esempio: generare mappatura per i template Chrome
Get-ADMXToOMAURIMapping -AdmxFilePath "C:\Temp\chrome.admx"
```

> **Approfondimento:** L'ADMX ingestion in Intune non supporta tutte le funzionalità dei template ADMX on-premises. Le limitazioni includono: nessun supporto per le policy di tipo `list` con elementi multipli in alcune build, nessun supporto per le `supportedOn` conditions, e le policy importate non sono visibili nel report di conformità fino a quando il device non sincronizza. Verificare la documentazione Microsoft per le limitazioni specifiche della versione Intune in uso.

---

## Ricette GPO Comuni

### Ricetta 1: Password Policy e Account Lockout

La password policy a livello di dominio si configura esclusivamente nella Default Domain Policy (o in un GPO collegato al dominio con precedenza superiore):

```
Computer Configuration → Policies → Windows Settings → Security Settings
    → Account Policies → Password Policy:
        - Enforce password history: 24 passwords
        - Maximum password age: 90 days
        - Minimum password age: 1 day
        - Minimum password length: 14 characters
        - Password must meet complexity requirements: Enabled
        - Store passwords using reversible encryption: Disabled

    → Account Policies → Account Lockout Policy:
        - Account lockout duration: 30 minutes
        - Account lockout threshold: 5 invalid logon attempts
        - Reset account lockout counter after: 30 minutes
```

### Ricetta 2: Mappatura Drive di Rete

Usando Group Policy Preferences con Item-Level Targeting:

```
User Configuration → Preferences → Windows Settings → Drive Maps:
    - Action: Replace
    - Location: \\fileserver.contoso.com\condivisione$
    - Reconnect: Checked
    - Label as: "Drive Condiviso"
    - Drive Letter: Use H:
    - Item-Level Targeting:
        └── Security Group: GRP-Users-DriveH
```

### Ricetta 3: Distribuzione Stampanti

```
Computer Configuration → Preferences → Control Panel Settings → Printers:
    - Action: Replace
    - Shared Path: \\printserver.contoso.com\HP-LaserJet-Piano2
    - Set this printer as default: Yes
    - Item-Level Targeting:
        └── IP Address Range: 10.0.2.0/24
```

### Ricetta 4: Software Restriction Policies (AppLocker)

```
Computer Configuration → Policies → Windows Settings → Security Settings
    → Application Control Policies → AppLocker:

    Executable Rules:
    - Default Rule: Allow Everyone to run all files in Windows folder
    - Default Rule: Allow Everyone to run all files in Program Files folder
    - Default Rule: Allow BUILTIN\Administrators to run all files
    - Custom Rule: Deny Everyone to run *.exe from %UserProfile%\Downloads

    Script Rules:
    - Default Rule: Allow scripts in Windows and Program Files
    - Custom Rule: Deny *.ps1 from removable media
```

```powershell
# Creare regole AppLocker via PowerShell
$rule = New-AppLockerPolicy -RuleType Publisher -User Everyone `
    -RuleNamePrefix "Blocco" -Deny `
    -FileInformation (Get-AppLockerFileInformation -Path "C:\Temp\malware.exe")

Set-AppLockerPolicy -PolicyObject $rule -Merge
```

### Ricetta 5: Restrizioni Desktop e Start Menu

```
User Configuration → Policies → Administrative Templates:
    → Desktop:
        - Remove Recycle Bin icon from desktop: Enabled
        - Hide and disable all items on the desktop: Enabled (per kiosk)

    → Start Menu and Taskbar:
        - Remove Run menu from Start Menu: Enabled
        - Remove access to the context menus for the taskbar: Enabled
        - Pin Apps to Taskbar: (configurare layout XML)

    → Control Panel:
        - Prohibit access to Control Panel and PC Settings: Enabled
        - Show only specified Control Panel items: (lista whitelist)
```

### Ricetta 6: Windows Update tramite GPO

```
Computer Configuration → Policies → Administrative Templates
    → Windows Components → Windows Update → Manage updates offered from WSUS:
        - Specify intranet Microsoft update service location:
            Set the intranet update service: https://wsus.contoso.com:8531
            Set the intranet statistics server: https://wsus.contoso.com:8531
        - Automatic Updates detection frequency: 4 hours

    → Windows Components → Windows Update → Manage end user experience:
        - Configure Automatic Updates: 4 - Auto download and schedule
        - Scheduled install day: 0 - Every day
        - Scheduled install time: 03:00
```

### Ricetta 7: Blocco USB Storage

```
Computer Configuration → Policies → Administrative Templates
    → System → Removable Storage Access:
        - All Removable Storage classes: Deny all access: Enabled
        - CD and DVD: Deny write access: Enabled
        - Removable Disks: Deny write access: Enabled
        - Removable Disks: Deny read access: Enabled
        - WPD Devices: Deny write access: Enabled
```

Per un approccio più granulare con eccezioni per dispositivi autorizzati:

```powershell
# Identificare il device ID di un USB autorizzato
Get-PnpDevice -Class "DiskDrive" -Status OK |
    Where-Object { $_.FriendlyName -like "*USB*" } |
    Get-PnpDeviceProperty -KeyName DEVPKEY_Device_HardwareIds |
    Select-Object -ExpandProperty Data
```

### Ricetta 8: Configurazione Firewall tramite GPO

```
Computer Configuration → Policies → Windows Settings → Security Settings
    → Windows Defender Firewall with Advanced Security:

    Inbound Rules:
    - Allow Remote Desktop (TCP 3389) solo da subnet interna
    - Allow ICMP Echo Request (solo subnet 10.0.0.0/8)
    - Block all other inbound by default

    Outbound Rules:
    - Allow HTTP/HTTPS (TCP 80, 443)
    - Allow DNS (UDP/TCP 53) solo verso DC
    - Allow Kerberos, LDAP verso DC
    - Block all other outbound by default (per ambienti ad alta sicurezza)
```

### Ricetta 9: Configurazione Power Management per Risparmio Energetico

```
Computer Configuration → Preferences → Windows Settings → Registry:
    Action: Replace
    Hive: HKEY_LOCAL_MACHINE
    Key: SOFTWARE\Policies\Microsoft\Power\PowerSettings
    Item-Level Targeting: Computer Name matches "LAB-*"

User Configuration → Policies → Administrative Templates
    → System → Power Management → Sleep Settings:
        - Specify the system sleep timeout (plugged in): 1800 seconds
        - Specify the system hibernate timeout (plugged in): 3600 seconds
        - Turn off the display (plugged in): 600 seconds
```

### Ricetta 10: Scheduled Task Distribuita via Preference

```
Computer Configuration → Preferences → Control Panel Settings → Scheduled Tasks:
    Action: Replace
    Name: Cleanup-TempFiles
    Trigger: Daily at 23:00
    Action: Start a program
        Program: powershell.exe
        Arguments: -ExecutionPolicy Bypass -File \\server\scripts$\cleanup-temp.ps1
    Run whether user is logged on or not: Yes
    Run with highest privileges: Yes
    Item-Level Targeting:
        └── Operating System: Windows 11
        └── Security Group: GRP-Workstations-Managed
```

---

## Gestione GPO con PowerShell

Il modulo `GroupPolicy` fornisce cmdlet completi per la gestione dei GPO:

```powershell
# Importare il modulo
Import-Module GroupPolicy

# Elencare tutti i GPO nel dominio
Get-GPO -All | Select-Object DisplayName, GpoStatus, CreationTime, ModificationTime |
    Sort-Object DisplayName | Format-Table -AutoSize

# Creare un nuovo GPO
$newGpo = New-GPO -Name "SEC - Baseline Workstation" -Comment "Security baseline per workstation"

# Collegare il GPO a una OU
New-GPLink -Name "SEC - Baseline Workstation" `
    -Target "OU=Workstations,DC=contoso,DC=com" `
    -LinkEnabled Yes

# Configurare un'impostazione di registry tramite GPO
Set-GPRegistryValue -Name "SEC - Baseline Workstation" `
    -Key "HKLM\SOFTWARE\Policies\Microsoft\Windows\System" `
    -ValueName "EnableSmartScreen" `
    -Type DWord -Value 1

# Esportare un GPO come report HTML
Get-GPOReport -Name "SEC - Baseline Workstation" -ReportType HTML -Path "C:\Reports\baseline.html"

# Esportare un GPO come report XML (per analisi programmatica)
Get-GPOReport -Name "SEC - Baseline Workstation" -ReportType XML -Path "C:\Reports\baseline.xml"

# Backup di tutti i GPO
$backupPath = "C:\GPOBackups\$(Get-Date -Format 'yyyy-MM-dd')"
New-Item -Path $backupPath -ItemType Directory -Force
Get-GPO -All | ForEach-Object {
    Backup-GPO -Guid $_.Id -Path $backupPath
}

# Ripristinare un GPO dal backup
Restore-GPO -Name "SEC - Baseline Workstation" -Path "C:\GPOBackups\2026-04-01"

# Copiare un GPO (per creare varianti)
Copy-GPO -SourceName "SEC - Baseline Workstation" -TargetName "SEC - Baseline Server"

# Trovare tutti i GPO orfani (non collegati a nessun contenitore)
$allGpos = Get-GPO -All
$linkedGpos = @()
$domains = (Get-ADDomain).DistinguishedName
$ous = Get-ADOrganizationalUnit -Filter * | Select-Object -ExpandProperty DistinguishedName
$containers = @($domains) + $ous

foreach ($container in $containers) {
    $inheritance = Get-GPInheritance -Target $container
    $linkedGpos += $inheritance.GpoLinks | Select-Object -ExpandProperty GpoId
}

$orphanGpos = $allGpos | Where-Object { $_.Id -notin $linkedGpos }
$orphanGpos | Select-Object DisplayName, CreationTime, ModificationTime

# Resultant Set of Policy (RSoP) per un utente su un computer
Get-GPResultantSetOfPolicy -Computer "WORKSTATION01" -User "contoso\mario.rossi" `
    -ReportType HTML -Path "C:\Reports\rsop-mario.html"
```

### Script di Audit GPO Completo

```powershell
# Generare un report completo di tutti i GPO con link e stato
$report = @()
Get-GPO -All | ForEach-Object {
    $gpo = $_
    $xml = [xml](Get-GPOReport -Guid $gpo.Id -ReportType XML)

    $links = $xml.GPO.LinksTo | ForEach-Object {
        "$($_.SOMPath) [Enabled: $($_.Enabled)]"
    }

    $report += [PSCustomObject]@{
        Name           = $gpo.DisplayName
        Status         = $gpo.GpoStatus
        Created        = $gpo.CreationTime
        Modified       = $gpo.ModificationTime
        ComputerVer    = $gpo.Computer.DSVersion
        UserVer        = $gpo.User.DSVersion
        Links          = ($links -join "; ")
        WmiFilter      = $gpo.WmiFilter.Name
    }
}

$report | Export-Csv "C:\Reports\GPO-Audit.csv" -NoTypeInformation -Encoding UTF8
```

### Cmdlet Avanzati del Modulo GroupPolicy

```powershell
# New-GPO — Creare GPO con stato specifico
New-GPO -Name "TEST - Nuova Policy" -Comment "Test policy per validazione" -GpoStatus AllSettingsEnabled

# Set-GPRegistryValue — Configurare valori di registro multipli
Set-GPRegistryValue -Name "SEC - Browser Lockdown" `
    -Key "HKLM\SOFTWARE\Policies\Microsoft\Edge" `
    -ValueName "HomepageLocation" `
    -Type String -Value "https://intranet.contoso.com"

Set-GPRegistryValue -Name "SEC - Browser Lockdown" `
    -Key "HKLM\SOFTWARE\Policies\Microsoft\Edge" `
    -ValueName "HomepageIsNewTabPage" `
    -Type DWord -Value 0

# Remove-GPRegistryValue — Rimuovere un valore configurato
Remove-GPRegistryValue -Name "SEC - Browser Lockdown" `
    -Key "HKLM\SOFTWARE\Policies\Microsoft\Edge" `
    -ValueName "HomepageLocation"

# Get-GPResultantSetOfPolicy — RSoP con output XML per parsing
Get-GPResultantSetOfPolicy -Computer "SRV01" -User "contoso\admin" `
    -ReportType XML -Path "C:\Temp\rsop.xml"

# New-GPLink — Collegare con parametri avanzati
New-GPLink -Name "SEC - Baseline" `
    -Target "OU=Servers,DC=contoso,DC=com" `
    -LinkEnabled Yes -Enforced Yes -Order 1
```

---

## GPO Backup, Migrazione e Import Cross-Dominio

### Backup Schedulato di Tutti i GPO

```powershell
# Script per backup automatizzato con retention
function Backup-AllGPOs {
    param(
        [string]$BackupRoot = "C:\GPOBackups",
        [int]$RetentionDays = 90
    )

    $timestamp = Get-Date -Format 'yyyy-MM-dd_HHmmss'
    $backupPath = Join-Path $BackupRoot $timestamp
    New-Item $backupPath -ItemType Directory -Force | Out-Null

    $gpos = Get-GPO -All
    $results = @()
    foreach ($gpo in $gpos) {
        $backup = Backup-GPO -Guid $gpo.Id -Path $backupPath
        $results += [PSCustomObject]@{
            Name     = $gpo.DisplayName
            BackupId = $backup.Id
            Status   = "OK"
        }
    }

    # Report del backup
    $results | Export-Csv "$backupPath\_backup-manifest.csv" -NoTypeInformation -Encoding UTF8
    Write-Output "Backup completato: $($results.Count) GPO in $backupPath"

    # Pulizia backup vecchi
    Get-ChildItem $BackupRoot -Directory |
        Where-Object { $_.CreationTime -lt (Get-Date).AddDays(-$RetentionDays) } |
        ForEach-Object {
            Remove-Item $_.FullName -Recurse -Force
            Write-Output "Rimosso backup obsoleto: $($_.Name)"
        }
}

Backup-AllGPOs -BackupRoot "C:\GPOBackups" -RetentionDays 90
```

### Import Cross-Dominio con Migration Tables

Quando si importa un GPO da un dominio a un altro, i riferimenti a oggetti specifici del dominio sorgente (nomi UNC, utenti, gruppi, percorsi LDAP) devono essere tradotti. Le **Migration Tables** (.migtable) definiscono queste mappature.

```powershell
# Creare una Migration Table per import cross-dominio
# La migration table è un file XML con il mapping source → destination

$migTableContent = @"
<?xml version="1.0" encoding="utf-16"?>
<MigrationTable xmlns="http://www.microsoft.com/GroupPolicy/Migrate/2005">
  <Mapping>
    <Type>UNCPath</Type>
    <Source>\\fileserver-old.domainA.com\share$</Source>
    <Destination>\\fileserver.domainB.com\share$</Destination>
  </Mapping>
  <Mapping>
    <Type>GlobalGroup</Type>
    <Source>DOMAINA\GRP-IT-Admins</Source>
    <Destination>DOMAINB\GRP-IT-Admins</Destination>
  </Mapping>
  <Mapping>
    <Type>User</Type>
    <Source>DOMAINA\admin.service</Source>
    <Destination>DOMAINB\admin.service</Destination>
  </Mapping>
  <Mapping>
    <Type>DomainLocalGroup</Type>
    <Source>DOMAINA\DL-FileShare-RW</Source>
    <Destination>DOMAINB\DL-FileShare-RW</Destination>
  </Mapping>
</MigrationTable>
"@

$migTablePath = "C:\GPOMigration\cross-domain.migtable"
New-Item (Split-Path $migTablePath) -ItemType Directory -Force | Out-Null
Set-Content $migTablePath $migTableContent -Encoding Unicode

# Importare il GPO usando la migration table
Import-GPO -BackupGpoName "SEC - Baseline Workstation" `
    -Path "C:\GPOBackups\2026-05-01" `
    -TargetName "SEC - Baseline Workstation" `
    -MigrationTable $migTablePath `
    -CreateIfNeeded

# Generare una migration table automaticamente da GPMC:
# GPMC → Group Policy Objects → tasto destro su un GPO → "Copy"
# Poi "Paste" in un altro dominio → wizard propone la migration table
```

### Import-GPO — Parametri Avanzati

```powershell
# Importare un GPO mantenendo i riferimenti GUID originali
Import-GPO -BackupId "B3F34E45-1234-5678-ABCD-EF0123456789" `
    -Path "C:\GPOBackups\2026-05-01" `
    -TargetName "Imported - Security Policy" `
    -CreateIfNeeded

# Importare sovrascrivendo un GPO esistente (per aggiornamento)
$existingGpo = Get-GPO -Name "SEC - Baseline Workstation"
Import-GPO -BackupGpoName "SEC - Baseline Workstation" `
    -Path "C:\GPOBackups\2026-05-01" `
    -TargetGuid $existingGpo.Id
```

---

## Starter GPOs

### Concetto e Utilizzo

Le **Starter GPOs** sono template riutilizzabili che contengono solo impostazioni degli Administrative Templates. Quando si crea un nuovo GPO basato su una Starter GPO, le impostazioni della Starter vengono copiate nel nuovo GPO come punto di partenza. Le Starter GPOs non vengono mai collegate direttamente a OU o domini.

Le Starter GPOs sono memorizzate nella cartella `StarterGPOs` all'interno di SYSVOL:
`\\dominio\SYSVOL\dominio\StarterGPOs\`

### Creazione e Gestione

```powershell
# Creare una Starter GPO
New-GPStarterGPO -Name "Starter - Desktop Standard" `
    -Comment "Template base per configurazione desktop standard"

# Configurare impostazioni nella Starter GPO
# (si usa GPMC: tasto destro → Edit, poi configurare le Administrative Templates)

# Creare un nuovo GPO basato su una Starter GPO
New-GPO -Name "CFG - Desktop Sede Milano" `
    -StarterGPOName "Starter - Desktop Standard" `
    -Comment "Configurazione desktop per sede di Milano"

# Elencare tutte le Starter GPOs
Get-GPStarterGPO -All | Select-Object DisplayName, Id, CreationTime | Format-Table

# Backup di una Starter GPO
# Le Starter GPOs sono supportate da Backup-GPStarterGPO (se disponibile)
# Altrimenti, fare backup manuale della cartella StarterGPOs in SYSVOL
```

### Best Practices per le Starter GPOs

- Creare Starter GPOs separate per i diversi ruoli: "Starter - Workstation", "Starter - Server", "Starter - Kiosk"
- Non sovraccaricare le Starter GPOs: includere solo le impostazioni base comuni
- Documentare nel campo Comment quali impostazioni contiene ogni Starter GPO
- Le Starter GPOs contengono solo Administrative Templates — Security Settings, Scripts e Preferences non sono supportati
- Dopo aver creato un GPO da una Starter, le modifiche alla Starter non si propagano ai GPO derivati — sono copie indipendenti

---

## GPO Performance — Ottimizzazione dell'Elaborazione

### Fattori che Influenzano le Prestazioni

L'elaborazione delle GPO aggiunge latenza al boot e al logon. I fattori principali:

| Fattore | Impatto | Mitigazione |
|---------|---------|-------------|
| Numero totale di GPO applicati | Lineare, ~50-100ms per GPO | Consolidare GPO ridondanti |
| WMI Filters | Alto per query su classi lente | Evitare `Win32_Product`, usare classi veloci |
| Script di Startup/Logon | Variabile, potenzialmente molto alto | Usare async, spostare a Scheduled Tasks |
| Software Installation (MSI) | Alto, richiede foreground sincrono | Preferire SCCM/Intune per deployment SW |
| Folder Redirection (primo logon) | Alto, trasferimento dati | Pre-provisioning con script |
| Slow link | Causa skip di alcune CSE | Configurare soglia appropriata |
| Replica SYSVOL interrotta | Causa retry e timeout | Monitorare DFS-R |

### Elaborazione Sincrona vs Asincrona

Da Windows Vista, l'elaborazione di default è **asincrona** per il foreground processing (boot e logon). Ciò significa che l'utente vede il desktop prima che tutte le CSE abbiano completato l'elaborazione. Alcune CSE richiedono però l'elaborazione **sincrona**:

- **Software Installation** — Sempre sincrona (l'MSI deve completare prima del desktop)
- **Folder Redirection** — Sincrona al primo logon, asincrona ai successivi
- **Scripts** — Configurabile via GPO

```powershell
# Forzare l'elaborazione sincrona (aumenta il tempo di logon ma garantisce completezza)
# Computer Configuration → Administrative Templates → System → Logon:
#   "Always wait for the network at computer startup and logon": Enabled

# Verificare se l'elaborazione sincrona è forzata
$syncWait = Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\CurrentVersion\Winlogon" `
    -Name "SyncForegroundPolicy" -ErrorAction SilentlyContinue
Write-Output "SyncForegroundPolicy: $($syncWait.SyncForegroundPolicy) (1=sincrono, 0/assente=asincrono)"
```

### Ottimizzare il Numero di GPO per OU

Linee guida Microsoft per le prestazioni:

- **< 30 GPO** applicati a un oggetto: prestazioni normali
- **30-50 GPO**: rallentamento percepibile, consolidamento consigliato
- **> 50 GPO**: impatto significativo, ristrutturazione necessaria

```powershell
# Contare i GPO effettivamente applicati a un computer e utente
function Measure-GPOCount {
    param([string]$ComputerName = $env:COMPUTERNAME)

    $xmlPath = [System.IO.Path]::GetTempFileName() -replace '\.tmp$', '.xml'
    gpresult /S $ComputerName /X $xmlPath /F 2>$null
    [xml]$xml = Get-Content $xmlPath

    $computerGPOs = ($xml.Rsop.ComputerResults.GPO | Where-Object { $_.FilterAllowed -ne 'false' -and $_.AccessDenied -ne 'true' }).Count
    $userGPOs = ($xml.Rsop.UserResults.GPO | Where-Object { $_.FilterAllowed -ne 'false' -and $_.AccessDenied -ne 'true' }).Count

    Write-Output "Computer: $ComputerName"
    Write-Output "  GPO Computer applicati: $computerGPOs"
    Write-Output "  GPO Utente applicati:   $userGPOs"
    Write-Output "  Totale:                 $($computerGPOs + $userGPOs)"

    if (($computerGPOs + $userGPOs) -gt 30) {
        Write-Warning "Superata la soglia raccomandata di 30 GPO. Considerare il consolidamento."
    }

    Remove-Item $xmlPath -ErrorAction SilentlyContinue
}

Measure-GPOCount -ComputerName "WORKSTATION01"
```

### Disabilitare Sezioni GPO Non Utilizzate

Se un GPO contiene solo Computer Configuration senza User Configuration (o viceversa), disabilitare la sezione non utilizzata evita che il client la elabori inutilmente:

```powershell
# Disabilitare User Configuration su un GPO che ha solo impostazioni Computer
$gpo = Get-GPO -Name "SEC - Firewall Rules"
$gpo.GpoStatus = "UserSettingsDisabled"

# Disabilitare Computer Configuration su un GPO che ha solo impostazioni User
$gpo = Get-GPO -Name "USR - Desktop Wallpaper"
$gpo.GpoStatus = "ComputerSettingsDisabled"

# Audit: trovare GPO con sezioni vuote non disabilitate
Get-GPO -All | ForEach-Object {
    $gpo = $_
    $status = $gpo.GpoStatus
    $hasComputer = $gpo.Computer.DSVersion -gt 0
    $hasUser = $gpo.User.DSVersion -gt 0
    if (-not $hasComputer -and $status -notin @("ComputerSettingsDisabled", "AllSettingsDisabled")) {
        Write-Output "[OPT] $($gpo.DisplayName): Computer Configuration vuota ma non disabilitata"
    }
    if (-not $hasUser -and $status -notin @("UserSettingsDisabled", "AllSettingsDisabled")) {
        Write-Output "[OPT] $($gpo.DisplayName): User Configuration vuota ma non disabilitata"
    }
}
```

---

## Slow Link Detection

### Meccanismo

Windows utilizza la **Slow Link Detection** per determinare se la connessione al domain controller è sufficientemente veloce per elaborare tutte le CSE. Il meccanismo invia pacchetti ICMP e misura la latenza. Se il link è classificato come "lento", alcune CSE vengono saltate per ridurre l'impatto.

La soglia predefinita è cambiata nel tempo:
- Windows XP/2003: **500 Kbps** (bandwidth-based)
- Windows Vista+: **0 ms di latenza** (time-based, di fatto disabilitato)
- Policy configurabile: `Computer Configuration → Administrative Templates → System → Group Policy → Group Policy slow link detection`

### CSE e Slow Link

| CSE | Elabora su Slow Link? |
|-----|----------------------|
| Registry (Administrative Templates) | Si |
| Security | Si |
| IP Security | Si |
| EFS Recovery | Si |
| Group Policy Preferences | Si |
| Scripts | **No** |
| Software Installation | **No** |
| Folder Redirection | **No** |
| Disk Quota | **No** |

```powershell
# Verificare la soglia slow link attuale
$threshold = Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\System" `
    -Name "GroupPolicyMinTransferRate" -ErrorAction SilentlyContinue
if ($threshold) {
    Write-Output "Soglia slow link: $($threshold.GroupPolicyMinTransferRate) Kbps"
    if ($threshold.GroupPolicyMinTransferRate -eq 0) {
        Write-Output "(Slow link detection DISABILITATO)"
    }
} else {
    Write-Output "Soglia slow link: default di sistema"
}

# Forzare l'elaborazione di una CSE su slow link:
# Computer Configuration → Administrative Templates → System → Group Policy
#   → Configure <CSE name> policy processing:
#     "Allow processing across a slow network connection": Enabled
```

---

## Best Practices

**Denominazione coerente:** Adottare una convenzione di naming rigorosa per i GPO. Un approccio efficace è: `[TIPO] - [SCOPE] - [DESCRIZIONE]`, ad esempio `SEC - Workstation - Disable USB Storage`, `CFG - Server - NTP Configuration`, `USR - Finance - Drive Mapping`. Questo facilita l'identificazione rapida dello scopo di ogni GPO.

**Principio di separazione:** Creare GPO focalizzati su un singolo scopo piuttosto che GPO monolitici con centinaia di impostazioni. Un GPO per la password policy, uno per le restrizioni desktop, uno per le mappature drive. Questo facilita la manutenzione, il troubleshooting e il riutilizzo.

**Non modificare i GPO predefiniti:** Microsoft raccomanda di non alterare la Default Domain Policy e la Default Domain Controllers Policy, se non per le impostazioni specifiche che richiedono quel livello (password policy, Kerberos policy). Creare nuovi GPO per tutte le altre configurazioni.

**Documentare ogni GPO:** Utilizzare il campo "Comment" disponibile nelle proprietà del GPO per descrivere lo scopo, il ticket di change management associato e la data di creazione. Per documentazione dettagliata, mantenere un registro esterno.

**Testare prima di applicare:** Utilizzare una OU di test con un campione di computer e utenti per validare i GPO prima di collegarli alle OU di produzione. Combinare con Security Filtering per roll-out graduali.

**Backup regolare:** Implementare backup schedulati dei GPO. La perdita di un GPO può essere estremamente difficile da ricostruire se non si ha un backup.

**Monitorare la replica SYSVOL:** Verificare regolarmente che il contenuto di SYSVOL sia coerente tra tutti i domain controller. Discrepanze nella replica causano applicazione inconsistente delle policy.

**Evitare WMI Filters quando possibile:** I WMI Filters aggiungono latenza all'elaborazione. Preferire Security Filtering o strutture OU appropriate quando il filtering può essere ottenuto con questi metodi.

**Minimizzare l'uso di Enforced e Block Inheritance:** Queste opzioni complicano la comprensione del flusso di applicazione. Usarle solo quando strettamente necessario per requisiti di sicurezza.

---

## Troubleshooting

### Problema: GPO Non Si Applica al Computer o Utente Target

**Sintomi**: Le impostazioni configurate nel GPO non hanno effetto sulla macchina o sull'utente target, nonostante il GPO sia collegato alla OU corretta e il link sia abilitato.

**Causa**: Le cause più comuni sono: il GPO è disabilitato (tutto o la sezione Computer/User), il Security Filtering esclude il target, un WMI Filter blocca l'applicazione, il computer non ha il permesso Read sul GPO (post-MS16-072), o la replica SYSVOL è inconsistente.

**Soluzione**: Procedere con diagnostica sistematica:

```powershell
# 1. Verificare lo stato del GPO
Get-GPO -Name "Nome GPO" | Select-Object DisplayName, GpoStatus

# 2. Verificare il collegamento e l'ordine
Get-GPInheritance -Target "OU=Target,DC=contoso,DC=com"

# 3. Generare RSoP per il target specifico
gpresult /S WORKSTATION01 /USER contoso\utente /H C:\Temp\gpresult.html

# 4. Verificare i permessi sul GPO
Get-GPPermission -Name "Nome GPO" -All

# 5. Verificare connettività SYSVOL
Test-Path "\\contoso.com\SYSVOL\contoso.com\Policies"

# 6. Controllare l'event log per errori GPO
Get-WinEvent -LogName "Microsoft-Windows-GroupPolicy/Operational" -MaxEvents 50 |
    Where-Object { $_.LevelDisplayName -eq "Error" -or $_.LevelDisplayName -eq "Warning" } |
    Format-Table TimeCreated, Id, Message -Wrap
```

### Problema: Conflitto tra GPO — Impostazione Inattesa

**Sintomi**: Un'impostazione ha un valore diverso da quello configurato nel GPO, oppure un'impostazione che dovrebbe essere attiva risulta disabilitata.

**Causa**: Un GPO con precedenza superiore sovrascrive l'impostazione. Ricordare l'ordine LSDO e il Link Order.

**Soluzione**: Utilizzare `gpresult /H` per identificare il "Winning GPO" per ogni impostazione. Il report HTML mostra chiaramente quale GPO ha "vinto" per ogni policy.

```powershell
# Eseguire gpresult con dettaglio verbose
gpresult /H C:\Temp\gpresult-dettaglio.html /F

# Oppure usare RSoP da remoto
Get-GPResultantSetOfPolicy -Computer "WORKSTATION01" -User "contoso\mario.rossi" `
    -ReportType HTML -Path "C:\Temp\rsop.html"
```

### Problema: Elaborazione GPO Lenta al Logon

**Sintomi**: Il logon degli utenti richiede diversi minuti. Gli utenti vedono il messaggio "Applying Group Policy" per un tempo eccessivo.

**Causa**: Le cause tipiche includono: troppi GPO collegati (>30 è un segnale di allarme), WMI Filters complessi, script di logon pesanti, Software Installation via GPO, problemi di connettività al domain controller o alla share SYSVOL.

**Soluzione**:

```powershell
# Abilitare il logging dettagliato per diagnosticare i tempi
# Creare il valore DWORD GroupPolicyMinTransferRate = 0
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\System" `
    -Name "GroupPolicyMinTransferRate" -Value 0 -Type DWord

# Analizzare i tempi nel log operativo
Get-WinEvent -LogName "Microsoft-Windows-GroupPolicy/Operational" |
    Where-Object { $_.Id -eq 4016 -or $_.Id -eq 5016 } |
    Select-Object TimeCreated, Message | Format-Table -Wrap

# Verificare quanti GPO si applicano
(gpresult /R /Scope Computer | Select-String "Applied Group Policy Objects").Count
```

### Problema: Preference Items Non Funzionano

**Sintomi**: Le Group Policy Preferences (mappatura drive, stampanti, scheduled task) non vengono applicate nonostante il GPO sia attivo.

**Causa**: Le Preference Items richiedono le Client-Side Extensions (CSE) specifiche, che potrebbero non essere installate su sistemi operativi precedenti. Inoltre, l'Item-Level Targeting potrebbe filtrare il target. Infine, le credenziali memorizzate nelle Preferences (deprecate per motivi di sicurezza — MS14-025) non funzionano più.

**Soluzione**: Verificare che le CSE siano installate, controllare l'Item-Level Targeting e non utilizzare l'opzione "Run in logged-on user's security context" per operazioni che richiedono privilegi elevati.

### Problema: Central Store Non Riconosciuto da GPMC

**Sintomi**: Dopo aver creato il Central Store in SYSVOL, GPMC continua a caricare i template locali dalla macchina amministrativa. I nuovi template aggiunti al Central Store non compaiono.

**Causa**: Il Central Store è attivato automaticamente quando GPMC rileva la cartella `PolicyDefinitions` al percorso corretto in SYSVOL. Se il percorso è errato, i permessi sono insufficienti o la replica DFS-R non ha completato la sincronizzazione, GPMC ricade sui file locali.

**Soluzione**:

```powershell
# Verificare il percorso corretto del Central Store
$correctPath = "\\$env:USERDNSDOMAIN\SYSVOL\$env:USERDNSDOMAIN\Policies\PolicyDefinitions"
Test-Path $correctPath

# Deve essere accessibile anche via FQDN del dominio, non del singolo DC
# Verificare i permessi
Get-Acl $correctPath | Format-List

# Verificare che il Central Store esista su tutti i DC
$dcs = Get-ADDomainController -Filter *
foreach ($dc in $dcs) {
    $dcPath = "\\$($dc.HostName)\SYSVOL\$env:USERDNSDOMAIN\Policies\PolicyDefinitions"
    $exists = Test-Path $dcPath
    $count = if ($exists) { (Get-ChildItem $dcPath -Filter "*.admx").Count } else { 0 }
    Write-Output "$($dc.HostName): Exists=$exists ADMX=$count"
}
```

### Problema: WMI Filter Blocca GPO Su Computer Sbagliati

**Sintomi**: Un GPO con WMI Filter non si applica a computer che dovrebbero soddisfare i criteri, oppure si applica a computer che non dovrebbero essere inclusi.

**Causa**: La query WQL contiene errori logici, le classi WMI non sono disponibili su tutti i client, oppure la query ha un impatto prestazionale che causa timeout.

**Soluzione**:

```powershell
# Testare una query WMI direttamente sul client target
$query = "SELECT * FROM Win32_OperatingSystem WHERE Version LIKE '10.0.2%' AND ProductType = '1'"
Get-CimInstance -Query $query

# Verificare tutte le classi WMI disponibili
Get-CimClass -Namespace root\cimv2 | Where-Object { $_.CimClassName -like "Win32_*" } |
    Select-Object CimClassName | Sort-Object CimClassName

# Misurare il tempo di esecuzione della query
Measure-Command {
    Get-CimInstance -Query "SELECT * FROM Win32_Product WHERE Name LIKE '%Office%'"
} | Select-Object TotalSeconds
# ATTENZIONE: Win32_Product è notoriamente lento (>30s), preferire Win32Reg_AddRemovePrograms

# Verificare i WMI Filters nel dominio
Get-ADObject -Filter { objectClass -eq "msWMI-Som" } -Properties "msWMI-Name","msWMI-Parm2" |
    Select-Object @{N='Name';E={$_."msWMI-Name"}}, @{N='Query';E={$_."msWMI-Parm2"}}
```

### Problema: GPO Replication Failure tra Domain Controller

**Sintomi**: Un GPO aggiornato su un DC non ha effetto sui client che si autenticano su un altro DC. Il numero di versione del GPO differisce tra DC. `gpresult` mostra versioni diverse a seconda del DC contattato.

**Causa**: La replica DFS-R di SYSVOL è interrotta o in ritardo. La replica AD del GPC può essere funzionante mentre la replica GPT in SYSVOL è rotta, causando un version mismatch.

**Soluzione**:

```powershell
# Verificare lo stato della replica DFS-R
dfsrmig /getglobalstate
dfsrmig /getmigrationstate

# Verificare la coerenza SYSVOL tra DC
$dcs = Get-ADDomainController -Filter *
$gpoGuid = (Get-GPO -Name "Nome GPO").Id

foreach ($dc in $dcs) {
    $gptPath = "\\$($dc.HostName)\SYSVOL\$env:USERDNSDOMAIN\Policies\{$gpoGuid}\GPT.INI"
    if (Test-Path $gptPath) {
        $gptIni = Get-Content $gptPath
        Write-Output "$($dc.HostName): $gptIni"
    } else {
        Write-Warning "$($dc.HostName): GPT.INI NON TROVATO"
    }
}

# Forzare la replica DFS-R
repadmin /syncall /AeD
```

### Problema: Loopback Processing Non Funziona su RDS/Terminal Server

**Sintomi**: Il Loopback Processing è configurato sulla OU del terminal server, ma le policy utente della OU del computer non vengono applicate. L'utente continua a ricevere le proprie policy utente normali.

**Causa**: Il GPO che abilita il Loopback Processing deve essere collegato alla OU che contiene l'oggetto computer del terminal server, e la sezione Computer Configuration del GPO deve essere abilitata. Inoltre, se si usa Replace mode, le User Configuration dei GPO nella OU del computer devono contenere effettivamente le impostazioni desiderate.

**Soluzione**:

```powershell
# Verificare che il loopback processing sia effettivamente attivo sul server
Invoke-Command -ComputerName "RDSERVER01" -ScriptBlock {
    $lpMode = (Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\System" `
        -Name "UserPolicyMode" -ErrorAction SilentlyContinue).UserPolicyMode
    switch ($lpMode) {
        1 { "Loopback: REPLACE mode" }
        2 { "Loopback: MERGE mode" }
        default { "Loopback: NON CONFIGURATO ($lpMode)" }
    }

    # Verificare quale OU contiene il computer
    $computerDN = (Get-ADComputer $env:COMPUTERNAME).DistinguishedName
    Write-Output "Computer DN: $computerDN"

    # Verificare i GPO collegati alla OU del computer che hanno User Configuration
    gpresult /R /SCOPE USER
}
```

### Problema: Script di Logon/Startup Non Si Eseguono

**Sintomi**: Gli script configurati nella sezione Scripts del GPO non vengono eseguiti. Non compaiono nei log di Event Viewer e non producono i risultati attesi.

**Causa**: Gli script non sono raggiungibili dal client (percorso di rete inaccessibile), il tipo di script non è supportato (es. PowerShell .ps1 richiede configurazione specifica), oppure la Execution Policy di PowerShell blocca l'esecuzione.

**Soluzione**:

```powershell
# Verificare gli script configurati via GPO
$gpoName = "CFG - Logon Script"
Get-GPO -Name $gpoName | Get-GPRegistryValue -Key "HKCU\Software\Microsoft\Windows\CurrentVersion\Group Policy\Scripts" -ErrorAction SilentlyContinue

# Per script PowerShell, verificare che la GPO li abiliti
# Computer Configuration → Policies → Administrative Templates → System → Scripts:
#   "Run Windows PowerShell scripts first" = Enabled
#   "Allow scripts to run regardless of execution policy settings" = Enabled (se necessario)

# Verificare l'accessibilità dello script dalla macchina client
Invoke-Command -ComputerName "CLIENT01" -ScriptBlock {
    $sysvolScripts = "\\$env:USERDNSDOMAIN\SYSVOL\$env:USERDNSDOMAIN\Policies"
    Test-Path $sysvolScripts
    # Verificare il percorso specifico dello script
}

# Controllare i log degli script GPO
Get-WinEvent -LogName "Microsoft-Windows-GroupPolicy/Operational" |
    Where-Object { $_.Id -in 4018, 5018 } |
    Select-Object TimeCreated, Id, Message | Format-Table -Wrap
```

### Problema: GPO Security Filtering Post-MS16-072 — Policy Utente Non Applicate

**Sintomi**: Dopo aver configurato il Security Filtering per applicare un GPO solo a un gruppo specifico di utenti, le policy utente nel GPO non vengono applicate a nessuno. Il report gpresult mostra il GPO come "Denied (Security)" o non lo elenca.

**Causa**: Dopo la patch MS16-072, il computer deve avere almeno il permesso **Read** sul GPO affinché le policy utente vengano elaborate. Se "Authenticated Users" è stato rimosso dal Security Filtering senza aggiungere "Domain Computers" con Read, il computer non riesce a leggere il GPO e le policy utente non vengono scaricate.

**Soluzione**:

```powershell
# Verificare i permessi attuali sul GPO
$gpoName = "USR - Policy Che Non Funziona"
Get-GPPermission -Name $gpoName -All | Format-Table Trustee, Permission, Inherited -AutoSize

# Fix: aggiungere Domain Computers con Read
Set-GPPermission -Name $gpoName `
    -TargetName "Domain Computers" `
    -TargetType Group `
    -PermissionLevel GpoRead

# Verificare che il gruppo target abbia GpoApply
Set-GPPermission -Name $gpoName `
    -TargetName "GRP-Target-Utenti" `
    -TargetType Group `
    -PermissionLevel GpoApply

# Dopo la modifica, forzare l'aggiornamento sul client
Invoke-GPUpdate -Computer "CLIENT01" -Force
```

### Problema: Impostazioni GPO "Tattooed" — Persistenti Dopo Rimozione GPO

**Sintomi**: Dopo aver rimosso o scollegato un GPO, alcune impostazioni persistono sui client e non tornano al valore predefinito.

**Causa**: Le **Preference Items** non rispettano il meccanismo anti-tattooing delle Policy Settings. Quando un GPO con Preference Items viene rimosso, le impostazioni configurate (chiavi di registro, mappature drive, scheduled task) rimangono in essere, perché scrivono nelle aree "non-managed" del sistema.

**Soluzione**:

```powershell
# Per Preference Items: verificare e abilitare "Remove this item when it is no longer applied"
# Nelle proprietà di ogni preference item → tab Common → spuntare:
# "Remove this item when it is no longer applied"

# Per Policy Settings (tradizionali) che persistono: forzare la rielaborazione
gpupdate /force

# Se il tattooing riguarda chiavi di registro, rimuoverle manualmente
# Identificare le chiavi tramite il report GPO
$gpoPath = "\\$env:USERDNSDOMAIN\SYSVOL\$env:USERDNSDOMAIN\Policies\{GPO-GUID}\User\Preferences\Registry\Registry.xml"
[xml]$regPrefs = Get-Content $gpoPath
$regPrefs.RegistrySettings.Registry | ForEach-Object {
    Write-Output "Hive: $($_.Properties.hive), Key: $($_.Properties.key), Value: $($_.Properties.name)"
}

# Rimuovere manualmente le chiavi persistenti su un client
Remove-ItemProperty "HKCU:\SOFTWARE\CustomApp" -Name "TattooedSetting" -ErrorAction SilentlyContinue
```

### Problema: Slow Link Detection Impedisce l'Applicazione delle GPO

**Sintomi**: I client connessi via VPN o WAN lenta non ricevono gli aggiornamenti GPO. Le policy di Folder Redirection e Software Installation non si applicano.

**Causa**: Windows rileva un collegamento lento (sotto 500 Kbps per default) e salta l'elaborazione di alcune CSE per evitare impatti sulle prestazioni. Le CSE che vengono saltate in caso di slow link includono: Software Installation, Folder Redirection, Scripts e Disk Quota.

**Soluzione**:

```powershell
# Configurare la soglia di slow link detection
# Computer Configuration → Administrative Templates → System → Group Policy:
#   "Group Policy slow link detection" = 0 (disabilita detection) o un valore in Kbps

# Verificare le impostazioni di slow link attuali
$slowLink = Get-ItemProperty "HKLM:\SOFTWARE\Policies\Microsoft\Windows\System" `
    -Name "GroupPolicyMinTransferRate" -ErrorAction SilentlyContinue
Write-Output "Slow link threshold: $($slowLink.GroupPolicyMinTransferRate) Kbps (0 = disabilitato)"

# Forzare l'elaborazione di CSE specifiche anche su slow link
# Computer Configuration → Administrative Templates → System → Group Policy:
#   "Configure <CSE name> policy processing":
#     - "Do not apply during periodic background processing": Disabled
#     - "Process even if the Group Policy objects have not changed": Enabled
#     - "Allow processing across a slow network connection": Enabled
```

### Problema: ADMX di Terze Parti Causa Errore "Namespace Already Defined" in GPMC

**Sintomi**: Dopo l'aggiunta di un template ADMX di terze parti nel Central Store, GPMC mostra l'errore "Namespace 'xxx' is already defined as the target namespace" quando si tenta di aprire un GPO.

**Causa**: Due file ADMX nel Central Store definiscono lo stesso namespace nel campo `<target>` del blocco `<policyNamespaces>`. Questo accade frequentemente quando si aggiornano i template di un prodotto senza rimuovere la versione precedente, o quando due prodotti condividono un namespace comune (es. template Google Chrome e Google Update).

**Soluzione**:

```powershell
# Identificare il conflitto di namespace
$centralStore = "\\$env:USERDNSDOMAIN\SYSVOL\$env:USERDNSDOMAIN\Policies\PolicyDefinitions"
$namespaces = @{}

Get-ChildItem $centralStore -Filter "*.admx" | ForEach-Object {
    [xml]$xml = Get-Content $_.FullName
    $ns = $xml.policyDefinitions.policyNamespaces.target.namespace
    if ($ns) {
        if ($namespaces.ContainsKey($ns)) {
            Write-Warning "CONFLITTO: '$ns' definito in '$($_.Name)' e '$($namespaces[$ns])'"
        }
        $namespaces[$ns] = $_.Name
    }
}

# Risolvere: rimuovere il file ADMX duplicato/obsoleto dal Central Store
# Fare SEMPRE un backup prima di eliminare
```

### Problema: Startup Scripts Ritardano l'Avvio del Computer

**Sintomi**: L'avvio del computer richiede diversi minuti prima di mostrare la schermata di logon. Il messaggio "Applying Group Policy" resta visibile a lungo.

**Causa**: Gli startup scripts configurati via GPO richiedono connettività di rete (es. accesso a share SYSVOL) che potrebbe non essere disponibile immediatamente all'avvio. Script pesanti, dipendenze da servizi non ancora avviati o timeout di rete amplificano il ritardo.

**Soluzione**:

```powershell
# Configurare l'elaborazione asincrona degli script di startup
# Computer Configuration → Administrative Templates → System → Scripts:
#   "Run startup scripts asynchronously": Enabled
#   "Maximum wait time for Group Policy scripts": 600 (secondi, default)

# Verificare la durata degli script nel log
Get-WinEvent -LogName "Microsoft-Windows-GroupPolicy/Operational" |
    Where-Object { $_.Id -in 4018, 5018 } |
    Select-Object TimeCreated, @{N='Duration';E={
        if ($_.Message -match '(\d+) milliseconds') { "$($Matches[1])ms" }
    }}, Message | Format-Table -Wrap

# Ottimizzare: spostare logiche pesanti in scheduled task anziché startup script
```

### Problema: Errore "The specified domain either does not exist or could not be contacted" in GPMC

**Sintomi**: GPMC non riesce a contattare il dominio. Non è possibile visualizzare, creare o modificare GPO. L'errore appare all'apertura della console o durante operazioni specifiche.

**Causa**: Problemi di risoluzione DNS, il DC contattato non è raggiungibile, oppure le credenziali dell'amministratore non hanno i permessi necessari.

**Soluzione**:

```powershell
# Diagnostica rapida
nltest /dsgetdc:$env:USERDNSDOMAIN
nslookup $env:USERDNSDOMAIN

# Verificare la connettività al DC
$dc = (Get-ADDomainController -Discover).HostName
Test-Connection $dc -Count 2
Test-NetConnection $dc -Port 389  # LDAP
Test-NetConnection $dc -Port 445  # SMB (SYSVOL)

# Forzare GPMC a contattare un DC specifico
# In GPMC: tasto destro sul dominio → "Change Domain Controller..."
# Oppure specificare il DC nel comando:
gpresult /S CLIENT01 /H report.html /D DC01.contoso.com
```

---

## FAQ — Domande Frequenti

### 1. Quanti GPO posso collegare a una singola OU?

Non esiste un limite tecnico rigido al numero di GPO collegabili a una OU. Tuttavia, ogni GPO aggiunto aumenta il tempo di elaborazione al logon e all'avvio. Microsoft consiglia come linea guida di mantenere il numero totale di GPO applicabili (sommando tutti i livelli LSDO) sotto i 30 per utente/computer. Oltre i 50 GPO, il tempo di elaborazione può diventare percepibile (>10 secondi).

### 2. Posso applicare un GPO a un utente specifico senza spostarlo in una OU diversa?

Sì, tramite **Security Filtering**. Rimuovere "Authenticated Users" dal security filtering del GPO e aggiungere l'utente o un gruppo che contiene l'utente. Ricordare di aggiungere "Domain Computers" con permesso Read (requisito post-MS16-072) se il GPO contiene policy utente.

### 3. Qual è la differenza tra "Disabled" e "Not Configured" in una policy?

- **Not Configured**: La policy non è gestita dal GPO. Non ha effetto e non sovrascrive impostazioni di altri GPO. È il valore predefinito.
- **Enabled**: La policy è attivamente abilitata. Sovrascrive GPO con priorità inferiore.
- **Disabled**: La policy è attivamente disabilitata. Sovrascrive GPO con priorità inferiore che la abilitano. Utile per annullare esplicitamente una policy ereditata.

### 4. Come posso impedire a un amministratore di OU di modificare i GPO di sicurezza?

Utilizzare il flag **Enforced** sui collegamenti GPO a livello di dominio per le policy di sicurezza. Anche se l'amministratore della OU abilita Block Inheritance, i GPO Enforced verranno comunque applicati. Inoltre, delegare i permessi GPMC con granularità: l'amministratore di OU può creare e collegare GPO alla propria OU, ma non modificare i GPO di dominio.

### 5. Le GPO funzionano su macchine non domain-joined?

Le GPO di Active Directory no — richiedono che il computer sia membro del dominio. Tuttavia, le **Local GPO** (`gpedit.msc`) funzionano su qualsiasi macchina Windows Pro/Enterprise/Education senza domain join. Per macchine Azure AD joined (senza AD on-premises), utilizzare Microsoft Intune per la gestione delle policy.

### 6. Come faccio a sapere quale GPO ha impostato una specifica chiave di registro?

Utilizzare `gpresult /H report.html` e consultare il report HTML. Per ogni impostazione, il report mostra il "Winning GPO". In alternativa, con PowerShell:

```powershell
# Cerca quale GPO configura una specifica chiave di registro
$keyToFind = "SOFTWARE\Policies\Microsoft\Windows\System\EnableSmartScreen"
Get-GPO -All | ForEach-Object {
    $xml = [xml](Get-GPOReport -Guid $_.Id -ReportType XML)
    $settings = $xml.GPO.Computer.ExtensionData.Extension.Policy
    $match = $settings | Where-Object { $_.Name -like "*SmartScreen*" }
    if ($match) {
        Write-Output "GPO: $($_.DisplayName) → $($match.Name): $($match.State)"
    }
}
```

### 7. Quanto spesso vengono aggiornate le GPO in background?

Per **workstation e server**: ogni 90 minuti con un offset casuale di 0-30 minuti (totale: 90-120 minuti). Per **domain controller**: ogni 5 minuti. La Security Policy CSE viene rielaborata ogni 16 ore indipendentemente dalle modifiche. L'intervallo è configurabile via GPO (`Computer Configuration → Administrative Templates → System → Group Policy → Set Group Policy refresh interval`).

### 8. È possibile applicare GPO diverse allo stesso utente a seconda del computer su cui fa logon?

Sì, tramite **Loopback Processing**. In modalità Merge, le policy utente dalla OU del computer vengono sovrapposte a quelle dalla OU dell'utente. In modalità Replace, solo le policy utente dalla OU del computer vengono applicate. Questo è lo scenario tipico per terminal server e kiosk.

### 9. Cosa succede se SYSVOL non è raggiungibile al momento del logon?

Se il client non riesce ad accedere a SYSVOL, viene utilizzata la cache locale delle policy (precedentemente scaricate e memorizzate in `C:\Windows\System32\GroupPolicy\DataStore`). Le policy verranno aggiornate al prossimo ciclo di refresh in background quando SYSVOL diventa accessibile. Se è il primo logon in assoluto del computer nel dominio e SYSVOL non è raggiungibile, nessuna GPO di dominio verrà applicata.

### 10. Come posso testare un GPO prima di applicarlo in produzione?

Metodi consigliati:
1. **OU di test**: Creare una OU dedicata con computer e utenti di test, collegare il GPO solo a quella OU.
2. **Security Filtering**: Collegare il GPO alla OU di produzione ma filtrarlo per un gruppo ristretto di utenti pilota.
3. **Enforcement mode evaluate**: Con i rulesets di GitHub (per l'analogia), o con GPO impostando prima solo Audit Mode.
4. **Group Policy Modeling**: Simulare l'applicazione nel GPMC senza applicare nulla realmente.

### 11. Posso versionare e fare rollback dei GPO come con il codice sorgente?

Non nativamente. I GPO non hanno un sistema di versioning integrato. Le best practices sono:
- **Backup regolari** con `Backup-GPO` prima di ogni modifica.
- **Export XML** con `Get-GPOReport -ReportType XML` per avere un record leggibile delle impostazioni.
- **AGPM (Advanced Group Policy Management)**: Componente di Microsoft Desktop Optimization Pack (MDOP) che aggiunge check-in/check-out, versioning, workflow di approvazione e audit dettagliato per i GPO.

### 12. Il campo "Comment" del GPO è replicato tra i DC?

Sì. Il commento del GPO è memorizzato nel file `comment.cmtx` nella directory GPT all'interno di SYSVOL e viene replicato tramite DFS-R insieme al resto del GPO. È un ottimo posto per documentare lo scopo del GPO, il ticket di change management e la data dell'ultima modifica.

### 13. Come posso delegare la creazione di GPO senza dare il permesso di collegarli?

In GPMC, la delega dei permessi è granulare:
- **Creare GPO**: Delegare in GPMC → "Group Policy Objects" → tab Delegation → aggiungere l'utente/gruppo.
- **Collegare GPO**: Delegare sulla OU specifica → tab Delegation → aggiungere permesso "Link GPOs".
- **Modificare GPO**: Nei permessi del singolo GPO → Delegation tab.

Un utente con permesso di creare GPO può crearli, ma non potrà collegarli a nessuna OU a meno che non abbia anche il permesso "Link GPOs" su quella OU.

### 14. Come funziona la priorità quando ho più WMI Filter e Security Filtering sullo stesso GPO?

I due meccanismi operano in sequenza:
1. Prima viene valutato il **Security Filtering**: il target deve avere i permessi Read + Apply Group Policy.
2. Poi viene valutato il **WMI Filter**: la query WQL deve restituire risultati.
3. Solo se entrambe le condizioni sono soddisfatte, il GPO viene applicato.

Un GPO può avere un solo WMI Filter assegnato, ma il WMI Filter può contenere più query WQL combinate con AND logico.

### 15. Come gestisco i GPO per i Fine-Grained Password Policies (FGPP)?

Le Fine-Grained Password Policies (introdotte in Windows Server 2008) non usano GPO. Sono oggetti Password Settings Object (PSO) memorizzati nel contenitore `CN=Password Settings Container,CN=System,DC=dominio,DC=com` e si gestiscono con:

```powershell
# Creare un PSO per gli account admin con requisiti più stringenti
New-ADFineGrainedPasswordPolicy -Name "PSO-Admin-Accounts" `
    -Precedence 10 `
    -MinPasswordLength 20 `
    -MaxPasswordAge "30.00:00:00" `
    -MinPasswordAge "1.00:00:00" `
    -PasswordHistoryCount 48 `
    -ComplexityEnabled $true `
    -ReversibleEncryptionEnabled $false `
    -LockoutThreshold 3 `
    -LockoutDuration "00:30:00" `
    -LockoutObservationWindow "00:30:00"

# Applicare il PSO a un gruppo
Add-ADFineGrainedPasswordPolicySubject -Identity "PSO-Admin-Accounts" `
    -Subjects "GRP-Domain-Admins"

# Verificare quale PSO si applica a un utente
Get-ADUserResultantPasswordPolicy -Identity "admin.rossi"
```

### 16. Come implemento l'audit delle modifiche ai GPO?

Abilitare l'auditing avanzato sulle Organizational Unit che contengono i GPO:

```powershell
# Monitorare le modifiche ai GPO nel Security Event Log
# Abilitare via GPO su tutti i DC:
# Computer Configuration → Advanced Audit Policy Configuration
#   → DS Access → Audit Directory Service Changes: Success

# Query per le modifiche ai GPO nell'Event Log
Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    ID = 5136, 5137, 5141  # Modify, Create, Delete directory object
} -MaxEvents 100 | Where-Object {
    $_.Message -like "*groupPolicyContainer*" -or
    $_.Message -like "*CN=Policies*"
} | Select-Object TimeCreated,
    @{N='Operation';E={
        switch ($_.Id) { 5136 { 'Modified' } 5137 { 'Created' } 5141 { 'Deleted' } }
    }},
    @{N='Details';E={$_.Message}} | Format-Table -Wrap
```

---

## Riferimenti

- Microsoft Docs: Group Policy Overview — https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-overview (consultato: 2026-05-23)
- Microsoft Docs: Group Policy Processing — https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2012-r2-and-2012/dn581922(v=ws.11) (consultato: 2026-05-23)
- Microsoft Security Bulletin MS16-072 — https://learn.microsoft.com/en-us/security-updates/securitybulletins/2016/ms16-072 (consultato: 2026-05-23)
- Group Policy Administrative Templates Catalog — https://admx.help (consultato: 2026-05-23)
- Microsoft Docs: AppLocker — https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/applocker/applocker-overview (consultato: 2026-05-23)
- CIS Benchmarks per Group Policy — https://www.cisecurity.org/benchmark/microsoft_windows_desktop (consultato: 2026-05-23)

---

## Esercizi

### Domande a Risposta Aperta

**1.** Descrivere la differenza tra il Group Policy Container (GPC) e il Group Policy Template (GPT). Spiegare come vengono replicati e quali problemi possono emergere se la replica di uno dei due componenti è interrotta mentre l'altro funziona normalmente.

**2.** Un'organizzazione ha configurato un GPO con Security Filtering impostato sul gruppo "GRP-Marketing" per distribuire mappature drive specifiche. Dopo l'installazione della patch MS16-072, le mappature non funzionano più. Spiegare la causa tecnica del problema e descrivere la soluzione, inclusi i comandi PowerShell necessari.

**3.** Confrontare le modalità Replace e Merge del Loopback Processing. Per ciascuna modalità, descrivere un caso d'uso appropriato in un ambiente enterprise, spiegando perché l'altra modalità non sarebbe adatta allo scenario proposto.

**4.** Spiegare la differenza tra le Advanced Audit Policies e le Basic Audit Policies. Descrivere cosa succede se entrambe sono configurate contemporaneamente e come risolvere il conflitto. Includere il ruolo di `auditpol.exe` nella diagnostica.

**5.** Un'organizzazione sta migrando la gestione degli endpoint da GPO on-premises a Microsoft Intune. Descrivere il flusso di lavoro per analizzare i GPO esistenti con Group Policy Analytics, le limitazioni dell'ADMX ingestion in Intune, e come gestire le impostazioni GPO che non hanno equivalente in Intune.

### Vero o Falso

**1.** Un GPO con il flag Enforced viene sempre applicato, anche se la OU figlia ha Block Inheritance abilitato.
<details><summary>Risposta</summary>VERO. L'opzione Enforced prevale su Block Inheritance — è per design il meccanismo che garantisce l'applicazione obbligatoria di policy di sicurezza a livello di dominio.</details>

**2.** Le Preference Items vengono automaticamente rimosse quando il GPO viene scollegato dalla OU.
<details><summary>Risposta</summary>FALSO. Le Preference Items scrivono in aree "non-managed" del sistema e persistono dopo la rimozione del GPO (tattooing), a meno che non sia abilitata l'opzione "Remove this item when it is no longer applied" nella tab Common della preference.</details>

**3.** Dopo la patch MS16-072, un GPO con policy utente filtrato per un gruppo specifico richiede che anche "Domain Computers" (o "Authenticated Users") abbia il permesso Read sul GPO.
<details><summary>Risposta</summary>VERO. Dopo MS16-072, il servizio gpsvc usa il token del computer per enumerare e scaricare i GPO utente. Senza Read per l'account computer, il GPO risulta invisibile e le policy utente non vengono elaborate.</details>

**4.** La Security CSE rielabora le impostazioni ogni 16 ore anche se il GPO non è stato modificato.
<details><summary>Risposta</summary>VERO. Questo comportamento è per design e serve a correggere automaticamente eventuali drift manuali nelle Security Settings.</details>

**5.** Le Starter GPOs possono contenere Security Settings, Scripts e Preference Items oltre agli Administrative Templates.
<details><summary>Risposta</summary>FALSO. Le Starter GPOs supportano esclusivamente le impostazioni degli Administrative Templates (registry-based). Security Settings, Scripts e Preferences non sono incluse.</details>

### Esercizi Basati su Scenario

**Scenario 1 — Kiosk per Biblioteca Pubblica:**
Una biblioteca pubblica ha 20 computer kiosk nella OU `OU=Kiosk,OU=Biblioteca,DC=comune,DC=it`. Gli utenti sono cittadini che accedono con account generici dalla OU `OU=Utenti,OU=Biblioteca,DC=comune,DC=it`. I kiosk devono avere: desktop bloccato (nessun accesso a Esplora File, cmd, PowerShell, Pannello di Controllo), singolo browser in modalità kiosk, timeout di sessione a 30 minuti, nessuna possibilità di installare software. Progettare la configurazione GPO completa, specificando: quanti GPO creare, dove collegarli, se usare Loopback Processing (e quale modalità), e le impostazioni chiave di ogni GPO.

**Scenario 2 — Migrazione ADMX Cross-Version:**
Un'organizzazione ha un dominio con DC Windows Server 2019 e sta aggiungendo nuovi server Windows Server 2025. Il Central Store contiene i template ADMX di Server 2019. Dopo l'aggiornamento del Central Store con i template di Server 2025, GPMC mostra errori "Namespace already defined" per tre file ADMX. Descrivere la procedura di troubleshooting, i comandi per identificare i conflitti, e la strategia per risolvere senza perdere la possibilità di gestire le policy di entrambe le versioni.

**Scenario 3 — Diagnosi con gpresult /h:**
Un utente del dipartimento Finance segnala che la mappatura del drive H: verso `\\fileserver\finance$` non compare dopo il logon. L'utente è membro del gruppo `GRP-Finance` e il suo account è nella OU `OU=Finance,OU=Users,DC=contoso,DC=com`. Il GPO "USR - Drive Map Finance" è collegato alla OU Finance ed è configurato con Security Filtering solo per `GRP-Finance` (Authenticated Users è stato rimosso). Descrivere i passi esatti per diagnosticare il problema usando `gpresult /h`, incluso: dove cercare nel report HTML, quali sezioni controllare per prima, e la soluzione più probabile.

**Scenario 4 — Audit e Compliance:**
Un auditor richiede la prova che tutti i server nella OU `OU=Servers,DC=contoso,DC=com` abbiano le Advanced Audit Policies configurate per registrare "Logon Success and Failure" e "Security Group Management Success". Descrivere come verificare la conformità su tutti i server, incluso: il GPO da configurare, come validare l'applicazione effettiva con `auditpol.exe`, e come generare un report automatizzato da presentare all'auditor.

**Scenario 5 — Intune Coesistenza:**
Un'organizzazione ha 500 workstation domain-joined gestite via GPO e sta iniziando il rollout di Intune per i nuovi laptop Hybrid Azure AD Joined. I 50 nuovi laptop devono ricevere le stesse configurazioni di sicurezza dei GPO esistenti (firewall, BitLocker, USB block, password policy), ma gestite da Intune. Descrivere: come analizzare i GPO esistenti per la migrazione, come configurare la coesistenza GPO/Intune durante la transizione, come gestire i conflitti tra le due fonti di configurazione, e quale impostazione attivare per definire la precedenza.

---

## Auto-valutazione

Rispondire alle seguenti domande per verificare la comprensione degli argomenti trattati. Le risposte corrette sono in blocchi collassabili.

**1.** Qual è l'ordine di elaborazione dei GPO e quale livello ha la precedenza più alta in caso di conflitto?
<details><summary>Risposta</summary>L'ordine è LSDOU: Local → Site → Domain → OU. La OU più vicina all'oggetto (la più "profonda") ha la precedenza più alta, perché viene elaborata per ultima. All'interno dello stesso livello, il GPO con Link Order 1 ha la precedenza più alta.</details>

**2.** Cosa cambia nel meccanismo di elaborazione delle policy utente dopo la patch MS16-072?
<details><summary>Risposta</summary>Dopo MS16-072, il servizio gpsvc usa il token del computer (non più dell'utente) per enumerare e scaricare i GPO utente via LDAP e SYSVOL. Se il computer non ha il permesso Read sul GPO, il GPO viene ignorato. La valutazione del permesso Apply Group Policy continua a usare il token dell'utente.</details>

**3.** Quale comando genera il report diagnostico più completo per le Group Policy?
<details><summary>Risposta</summary><code>gpresult /H percorso.html /F</code> genera un report HTML completo con: GPO applicati e negati, motivo del diniego, Winning GPO per ogni impostazione, version mismatch AD/SYSVOL, e tempi di elaborazione per ogni CSE.</details>

**4.** Quando la Security CSE rielabora le impostazioni anche senza modifiche al GPO?
<details><summary>Risposta</summary>Ogni 16 ore, indipendentemente dalle modifiche. Questo serve a correggere automaticamente eventuali drift manuali nelle Security Settings (password policy, user rights, security options, audit policy).</details>

**5.** Come si crea il Central Store per i template ADMX?
<details><summary>Risposta</summary>Creare la cartella <code>PolicyDefinitions</code> nel percorso SYSVOL: <code>\\dominio\SYSVOL\dominio\Policies\PolicyDefinitions\</code>. Copiare i file .admx nella root e i file .adml nelle sottocartelle delle lingue (es. <code>en-US\</code>, <code>it-IT\</code>). GPMC rileva automaticamente il Central Store alla prossima apertura.</details>

**6.** Qual è la differenza tra Administrative Templates e Security Settings in termini di rielaborazione?
<details><summary>Risposta</summary>La Registry CSE (Administrative Templates) per default non rielabora se la lista GPO non è cambiata — ottimizzazione di performance. La Security CSE rielabora ogni 16 ore anche se nulla è cambiato, correggendo drift. Questa differenza significa che un drift nelle Administrative Templates persiste fino alla prossima modifica GPO o a un <code>gpupdate /force</code>, mentre un drift nelle Security Settings si autocorregge.</details>

**7.** Cosa sono le Starter GPOs e quali limitazioni hanno?
<details><summary>Risposta</summary>Le Starter GPOs sono template riutilizzabili per creare nuovi GPO con impostazioni predefinite. Limitazioni: supportano solo Administrative Templates (no Security Settings, Scripts, Preferences); le modifiche alla Starter non si propagano ai GPO derivati; non possono essere collegate direttamente a OU.</details>

**8.** Come si verifica la conformità MS16-072 di tutti i GPO nel dominio?
<details><summary>Risposta</summary>Per ogni GPO con User Configuration (DSVersion > 0), verificare che Authenticated Users o Domain Computers abbia il permesso GpoRead. Usare <code>Get-GPPermission -All</code> su ogni GPO e controllare la presenza di almeno un principal che includa gli account computer con permesso Read.</details>

---

## Letture Primarie Consigliate

### Documentazione Microsoft (primaria)

- **Group Policy Overview** — https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/group-policy/group-policy-overview (consultato: 2026-05-23). Panoramica ufficiale dell'architettura GPO, componenti e ciclo di elaborazione.
- **Group Policy Processing and Precedence** — https://learn.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2012-r2-and-2012/dn581922(v=ws.11) (consultato: 2026-05-23). Dettaglio dell'ordine LSDOU, enforcement, block inheritance.
- **MS16-072 Security Bulletin** — https://learn.microsoft.com/en-us/security-updates/securitybulletins/2016/ms16-072 (consultato: 2026-05-23). Descrizione della vulnerabilità e del cambio di comportamento nel Security Filtering.
- **Central Store for Administrative Templates** — https://learn.microsoft.com/en-us/troubleshoot/windows-client/group-policy/create-and-manage-central-store (consultato: 2026-05-23). Guida alla creazione e gestione del Central Store ADMX.
- **Advanced Security Audit Policy Settings** — https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/advanced-security-audit-policy-settings (consultato: 2026-05-23). Riferimento completo per tutte le subcategorie di audit.
- **Administrative Templates import in Intune** — https://learn.microsoft.com/en-us/mem/intune/configuration/administrative-templates-import-custom (consultato: 2026-05-23). Guida all'ADMX ingestion nel Settings Catalog di Intune.
- **Loopback Processing** — https://learn.microsoft.com/en-us/troubleshoot/windows-server/group-policy/loopback-processing-of-group-policy (consultato: 2026-05-23). Spiegazione delle modalità Replace e Merge.

### Risorse Comunitarie

- **ADMX.help** — https://admx.help (consultato: 2026-05-23). Catalogo searchable di tutte le Administrative Templates con riferimenti alle chiavi di registro corrispondenti.
- **CIS Benchmarks for Windows** — https://www.cisecurity.org/benchmark/microsoft_windows_desktop (consultato: 2026-05-23). Benchmark di sicurezza Level 1 e Level 2 con mappatura a GPO.

### Libri

- *Moskowitz, J. — Group Policy: Fundamentals, Security, and the Managed Desktop, 4th Edition* — Wiley, 2022. Riferimento completo sulla gestione GPO in ambiente enterprise, include sezioni su AGPM e migrazione a Intune.

---

## Collegamenti Incrociati

### Moduli nella stessa cartella (03-WINDOWS-POWERUSER)

- `01-active-directory.md` — Struttura AD (domini, OU, siti) su cui le GPO si applicano; delega dei permessi; replica AD che trasporta il GPC
- `02-powershell.md` — Fondamenti PowerShell necessari per il modulo `GroupPolicy`; cmdlet base
- `04-registro-sistema.md` — Le Administrative Templates scrivono in `HKLM\SOFTWARE\Policies\` e `HKCU\SOFTWARE\Policies\`; comprensione degli hive, tipi di dato, navigazione
- `05-sicurezza-windows.md` — Security Settings delle GPO; UAC, BitLocker, Windows Firewall
- `22-powershell-scripting-avanzato.md` — PSRemoting per `Invoke-GPUpdate` remoto; moduli avanzati; Pester per testing di compliance GPO
- `24-microsoft-defender.md` — Configurazione Defender via GPO e Intune; ASR rules, Exploit Protection
- `29-hardening-windows.md` — Security baselines (SCT, CIS) implementate via GPO; hardening checklist

### Moduli in altre cartelle

- `15-SECURITY/` — Threat modeling, incident response, audit trail: le Advanced Audit Policies GPO alimentano i log di sicurezza analizzati nei moduli di cybersecurity

---

## Glossario Locale

| Termine | Definizione |
|---------|-------------|
| **ADMX** | Administrative Template XML — file che definisce le policy degli Administrative Templates. Language-neutral. |
| **ADML** | Administrative Template Markup Language — file di localizzazione per un ADMX. Language-specific. |
| **Central Store** | Cartella `PolicyDefinitions` in SYSVOL che centralizza i template ADMX/ADML per tutti gli amministratori. |
| **CSE** | Client-Side Extension — DLL sul client che interpreta e applica una categoria specifica di impostazioni GPO. |
| **Enforced** | Flag su un link GPO che garantisce l'applicazione anche in presenza di Block Inheritance e prevale su GPO successivi. |
| **FGPP** | Fine-Grained Password Policy — oggetto PSO che definisce policy password per gruppi specifici, indipendente dalle GPO. |
| **GPC** | Group Policy Container — oggetto LDAP in Active Directory che memorizza i metadati del GPO. |
| **GPO** | Group Policy Object — oggetto che contiene un set di impostazioni di configurazione applicabili a utenti e computer. |
| **GPT** | Group Policy Template — struttura di cartelle in SYSVOL che contiene i file effettivi delle policy. |
| **LSDOU** | Local, Site, Domain, OU — ordine di elaborazione delle GPO, dove l'ultimo elaborato prevale. |
| **Loopback Processing** | Funzionalità che fa sì che le policy utente siano determinate dalla posizione del computer anziché dell'utente. |
| **MS16-072** | Patch di sicurezza (giugno 2016) che ha modificato il comportamento del Security Filtering richiedendo Read per l'account computer. |
| **OMA-URI** | Open Mobile Alliance Uniform Resource Identifier — formato usato da Intune/MDM per indirizzare CSP di configurazione. |
| **RSoP** | Resultant Set of Policy — il set effettivo di policy risultante dall'elaborazione di tutti i GPO applicabili. |
| **SACL** | System Access Control List — ACL che definisce quali operazioni su un oggetto generano eventi di audit. |
| **SCT** | Security Compliance Toolkit — set di strumenti e baseline di sicurezza Microsoft per GPO. |
| **Security Filtering** | Meccanismo che limita l'applicazione di un GPO a specifici utenti, computer o gruppi basandosi sulle ACL del GPO. |
| **Starter GPO** | Template GPO riutilizzabile contenente solo Administrative Templates, usato come base per creare nuovi GPO. |
| **Tattooing** | Persistenza di impostazioni dopo la rimozione del GPO. Le Policy Settings sono anti-tattoo; le Preference Items no. |
| **WMI Filter** | Filtro basato su query WQL che condiziona l'applicazione di un GPO in base alle caratteristiche del client. |
| **WQL** | WMI Query Language — linguaggio di query per interrogare le classi WMI, usato nei WMI Filters. |
