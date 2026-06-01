# Permessi e Accesso Windows — Guida Completa

> **Modulo 08** · **Aggiornamento:** 2026-05-24

| Campo | Valore |
|---|---|
| **Modulo del corso** | Amministrazione Windows enterprise |
| **Prerequisiti** | Conoscenza di Active Directory e gruppi (→ `01-active-directory.md`), padronanza di PowerShell base (→ `02-powershell.md`), familiarità con la sicurezza Windows (→ `05-sicurezza-windows.md`) |
| **Obiettivi di apprendimento** | 1) Padroneggiare il modello di controllo accessi Windows (SID, Security Descriptor, DACL, SACL, token) · 2) Configurare permessi NTFS e share secondo la best practice AGDLP · 3) Implementare audit dell'accesso agli oggetti tramite SACL e `auditpol` · 4) Gestire accessi privilegiati con UAC, Tiered Administration, LAPS e PAW · 5) Configurare Dynamic Access Control (DAC) basato su claims |
| **Tempo stimato** | lettura 80 min · lab 100 min |
| **Livello** | Proficient |
| **Ultimo aggiornamento** | 2026-05-24 |

## Idee guida
1. **NTFS permissions vs Share permissions: most-restrictive wins.**
2. **AGDLP best practice: Account → Global → Domain Local → Permissions.**
3. **`icacls` + `Get-Acl/Set-Acl` PS cmdlet.**
4. **UAC + LUA + Mandatory Integrity Levels (MIL).**
5. **Security Descriptor = Owner + Group + DACL + SACL — ogni oggetto ne ha uno.**
6. **Tiered Administration Model: separare privilegi T0 (DC), T1 (server), T2 (workstation).**
7. **Dynamic Access Control (DAC): accesso basato su claims e proprietà delle risorse.**
8. **Audit SACL + auditpol: tracciare chi accede a cosa, quando e come.**
9. **LAPS / PAW / Conditional Access: difesa in profondità per accessi privilegiati.**
10. **JEA (Just Enough Administration): delega granulare di comandi PowerShell senza concedere admin completo.**
11. **PAM Bastion Forest: membership temporanea nei gruppi privilegiati con TGT a tempo limitato.**


## Indice

- [Panoramica](#panoramica)
- [Modello di Controllo Accessi Windows](#modello-di-controllo-accessi-windows)
  - [Security Identifiers (SID)](#security-identifiers-sid)
  - [Security Descriptor](#security-descriptor)
  - [Access Control List (ACL)](#access-control-list-acl)
  - [Access Control Entry (ACE)](#access-control-entry-ace)
  - [Token di Accesso](#token-di-accesso)
  - [Mandatory Integrity Control (MIC)](#mandatory-integrity-control-mic)
  - [SDDL — Security Descriptor Definition Language](#sddl--security-descriptor-definition-language)
- [Permessi NTFS Fondamenti](#permessi-ntfs-fondamenti)
  - [Permessi Standard](#permessi-standard)
  - [Permessi Avanzati (Granulari)](#permessi-avanzati-granulari)
  - [Dettaglio dei 13 Permessi Avanzati](#dettaglio-dei-13-permessi-avanzati)
  - [Gestione con PowerShell](#gestione-con-powershell)
- [Ereditarietà Permessi](#ereditarietà-permessi)
  - [Come Funziona](#come-funziona)
  - [Flag di Ereditarietà in Dettaglio](#flag-di-ereditarietà-in-dettaglio)
  - [Gestione Ereditarietà](#gestione-ereditarietà)
  - [Blocco Ereditarietà — Scenari Reali](#blocco-ereditarietà--scenari-reali)
  - [Sostituzione Permessi sui Figli](#sostituzione-permessi-sui-figli)
  - [Troubleshooting Ereditarietà — Diagnosi Avanzata](#troubleshooting-ereditarietà--diagnosi-avanzata)
- [Permessi Effettivi](#permessi-effettivi)
  - [Calcolo dei Permessi Effettivi](#calcolo-dei-permessi-effettivi)
  - [Ordine di Valutazione ACE](#ordine-di-valutazione-ace)
  - [Strumenti di Verifica](#strumenti-di-verifica)
- [Share Permission vs NTFS](#share-permission-vs-ntfs)
  - [Matrice di Interazione](#matrice-di-interazione)
  - [Gestione Share](#gestione-share)
- [Ownership — Proprietà degli Oggetti](#ownership--proprietà-degli-oggetti)
  - [Prendere Possesso (Take Ownership)](#prendere-possesso-take-ownership)
  - [SeBackupPrivilege e SeRestorePrivilege](#sebackupprivilege-e-serestoreprivilege)
- [icacls — Gestione CLI](#icacls--gestione-cli)
- [Permessi Registry](#permessi-registry)
- [Permessi Servizi](#permessi-servizi)
- [Dynamic Access Control](#dynamic-access-control)
  - [Componenti DAC](#componenti-dac)
  - [Implementazione DAC](#implementazione-dac)
  - [Classificazione Automatica con FSRM](#classificazione-automatica-con-fsrm)
  - [Espressioni Condizionali e Compound Identity](#espressioni-condizionali-e-compound-identity)
- [Group Policy e Permessi](#group-policy-e-permessi)
  - [Restricted Groups](#restricted-groups)
  - [Permessi File System via GPO](#permessi-file-system-via-gpo)
  - [Audit Policy via GPO](#audit-policy-via-gpo)
  - [User Rights Assignment](#user-rights-assignment)
- [Delega in Active Directory](#delega-in-active-directory)
  - [Delega a Livello di OU](#delega-a-livello-di-ou)
  - [Permessi Personalizzati con dsacls](#permessi-personalizzati-con-dsacls)
- [Privileged Access Management](#privileged-access-management)
  - [Tiered Administration Model](#tiered-administration-model)
  - [Privileged Access Workstations (PAW)](#privileged-access-workstations-paw)
  - [PAM — Bastion Forest e Membership Temporanea](#pam--bastion-forest-e-membership-temporanea)
  - [LAPS — Local Administrator Password Solution](#laps--local-administrator-password-solution)
  - [Windows LAPS vs Legacy LAPS — Confronto Dettagliato](#windows-laps-vs-legacy-laps--confronto-dettagliato)
  - [Just Enough Administration (JEA)](#just-enough-administration-jea)
- [Conditional Access con Azure AD / Entra ID](#conditional-access-con-azure-ad--entra-id)
  - [Entra Private Access per Active Directory On-Premises](#entra-private-access-per-active-directory-on-premises)
- [Configurazione Audit](#configurazione-audit)
  - [SACL — System Access Control List](#sacl--system-access-control-list)
  - [auditpol — Gestione Policy di Audit](#auditpol--gestione-policy-di-audit)
  - [Event ID Chiave](#event-id-chiave)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)

---

## Panoramica

Il modello di accesso Windows si basa su Security Identifiers (SID), Access Control Lists (ACL) e token di sicurezza. Ogni oggetto (file, cartella, chiave registry, servizio) ha una Security Descriptor che contiene DACL (chi può accedere) e SACL (cosa viene auditato). La corretta configurazione dei permessi è fondamentale per la sicurezza e l'operatività.

Il modello è **discretionary** (DAC): il proprietario dell'oggetto decide chi può accedere. Windows aggiunge anche il **Mandatory Integrity Control (MIC)** che impone livelli di integrità obbligatori — un meccanismo che funziona *prima* della valutazione delle ACL e rappresenta il livello MAC (Mandatory Access Control) del sistema.

Ogni volta che un processo tenta di accedere a un oggetto, il Security Reference Monitor (SRM) nel kernel confronta il token di accesso del processo con la security descriptor dell'oggetto. Questa decisione avviene in tempo reale, per ogni singola operazione I/O.

```
Flusso decisionale di accesso:

 Processo (token)                    Oggetto (security descriptor)
 ┌──────────────┐                    ┌──────────────────────────┐
 │ User SID     │                    │ Owner SID                │
 │ Group SIDs   │                    │ Group SID                │
 │ Privileges   │──── SRM check ────│ DACL (Access Control)    │
 │ Integrity Lv │                    │ SACL (Audit)             │
 │ Claims       │                    │ Integrity Label          │
 └──────────────┘                    └──────────────────────────┘
                       │
              ┌────────┴────────┐
              │ 1. MIC check    │
              │ 2. Owner check  │
              │ 3. DACL eval    │
              │    → Deny ACE   │
              │    → Allow ACE  │
              │ 4. Implicit deny│
              └─────────────────┘
```

---

## Modello di Controllo Accessi Windows

### Security Identifiers (SID)

Ogni principal (utente, gruppo, computer, servizio) è identificato da un SID univoco. Il SID è un valore binario con una rappresentazione stringa leggibile.

```
Formato SID:
S-R-X-Y₁-Y₂-...-Yₙ-RID

Dove:
S   = Prefisso fisso "S"
R   = Revision (sempre 1)
X   = Identifier Authority (es. 5 = NT Authority)
Y   = Sub-authority values
RID = Relative Identifier (univoco nel dominio)

Esempio:
S-1-5-21-3623811015-3361044348-30300820-1013
│ │ │  │                                │
│ │ │  └── Sub-authorities (dominio)    └── RID (utente specifico)
│ │ └── NT Authority
│ └── Revision 1
└── SID prefix
```

#### SID Well-Known (predefiniti)

```
SID                          Nome                              Descrizione
────────────────────────────────────────────────────────────────────────────
S-1-0-0                      Nobody                            Nessuna identità
S-1-1-0                      Everyone                          Tutti gli utenti
S-1-2-0                      Local                             Utenti locali
S-1-3-0                      Creator Owner                     Proprietario futuro
S-1-3-1                      Creator Group                     Gruppo del creatore
S-1-5-2                      Network                           Accesso via rete
S-1-5-4                      Interactive                       Login interattivo
S-1-5-6                      Service                           Account di servizio
S-1-5-7                      Anonymous                         Login anonimo
S-1-5-9                      Enterprise Domain Controllers     Tutti i DC
S-1-5-11                     Authenticated Users               Utenti autenticati
S-1-5-18                     SYSTEM (LocalSystem)              Account di sistema
S-1-5-19                     LOCAL SERVICE                     Servizio locale
S-1-5-20                     NETWORK SERVICE                   Servizio di rete
S-1-5-32-544                 Administrators                    Gruppo admin locali
S-1-5-32-545                 Users                             Gruppo utenti locali
S-1-5-32-547                 Power Users                       Power Users locali
S-1-5-32-551                 Backup Operators                  Operatori backup
S-1-5-domainID-500           Administrator                     Admin dominio built-in
S-1-5-domainID-512           Domain Admins                     Gruppo Domain Admins
S-1-5-domainID-513           Domain Users                      Gruppo Domain Users
S-1-5-domainID-519           Enterprise Admins                 Gruppo Enterprise Admins
S-1-16-0                     Untrusted Integrity               Livello integrità minimo
S-1-16-4096                  Low Integrity                     Bassa integrità
S-1-16-8192                  Medium Integrity                  Media integrità
S-1-16-12288                 High Integrity                    Alta integrità (admin)
S-1-16-16384                 System Integrity                  Integrità di sistema
```

```powershell
# Ottenere SID di un utente
$user = New-Object System.Security.Principal.NTAccount("CORP\mrossi")
$user.Translate([System.Security.Principal.SecurityIdentifier]).Value

# SID → nome utente
$sid = New-Object System.Security.Principal.SecurityIdentifier("S-1-5-21-xxx-1013")
$sid.Translate([System.Security.Principal.NTAccount]).Value

# SID dell'utente corrente
[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value

# Tutti i SID nel token corrente (utente + gruppi)
whoami /all
```

### Security Descriptor

Ogni oggetto securizzabile possiede una Security Descriptor (SD). La SD è una struttura dati che contiene tutte le informazioni di sicurezza dell'oggetto.

```
Security Descriptor
┌──────────────────────────────────────────────┐
│ Header                                        │
│   ├── Revision                                │
│   ├── Control Flags                           │
│   │     SE_DACL_PRESENT                       │
│   │     SE_SACL_PRESENT                       │
│   │     SE_DACL_PROTECTED (ereditarietà off)  │
│   │     SE_DACL_AUTO_INHERITED                │
│   │     SE_SELF_RELATIVE                      │
│   │                                           │
│ Owner SID   → chi possiede l'oggetto          │
│ Group SID   → gruppo primario (compat POSIX)  │
│ DACL        → chi PUÒ/NON PUÒ accedere       │
│ SACL        → cosa viene registrato (audit)   │
└──────────────────────────────────────────────┘

DACL assente (null DACL) → TUTTI hanno accesso completo (PERICOLOSO)
DACL vuota (0 ACE)       → NESSUNO ha accesso (tranne Owner con READ_CONTROL e WRITE_DAC)
```

### Access Control List (ACL)

Una ACL è una lista ordinata di ACE (Access Control Entry). Esistono due tipi:

```
DACL (Discretionary ACL):
├── Determina chi può o non può accedere all'oggetto
├── Valutata dal SRM per ogni richiesta di accesso
├── Contiene ACE di tipo Allow e Deny
└── L'ordine degli ACE è CRITICO

SACL (System ACL):
├── Determina quali operazioni vengono auditate
├── Richiede SeSecurityPrivilege per essere letta/modificata
├── Contiene ACE di tipo System Audit
└── Genera eventi nel Security Event Log
```

### Access Control Entry (ACE)

Ogni ACE ha una struttura definita che specifica un permesso per un principal.

```
Struttura ACE:
┌──────────────────────────────────┐
│ ACE Header                       │
│   ├── ACE Type                   │
│   │    ACCESS_ALLOWED_ACE        │
│   │    ACCESS_DENIED_ACE         │
│   │    SYSTEM_AUDIT_ACE          │
│   │    ACCESS_ALLOWED_CALLBACK   │
│   ├── ACE Flags (ereditarietà)   │
│   │    CONTAINER_INHERIT_ACE     │
│   │    OBJECT_INHERIT_ACE        │
│   │    INHERIT_ONLY_ACE          │
│   │    NO_PROPAGATE_INHERIT_ACE  │
│   │    INHERITED_ACE             │
│   └── ACE Size                   │
│                                  │
│ Access Mask (32 bit)             │
│   ├── Bit 0-15: Object-specific  │
│   │   (es. FILE_READ_DATA)       │
│   ├── Bit 16-23: Standard        │
│   │   (DELETE, READ_CONTROL,     │
│   │    WRITE_DAC, WRITE_OWNER,   │
│   │    SYNCHRONIZE)              │
│   └── Bit 24-31: Generic         │
│       (GENERIC_READ/WRITE/       │
│        EXECUTE/ALL)              │
│                                  │
│ SID del principal                │
└──────────────────────────────────┘
```

#### Access Mask — Bit Map per File/Cartelle

```
Bit    Costante                           Hex          Descrizione
────────────────────────────────────────────────────────────────────────
0      FILE_READ_DATA / LIST_DIRECTORY    0x0001       Leggere dati / elencare contenuto
1      FILE_WRITE_DATA / ADD_FILE         0x0002       Scrivere dati / aggiungere file
2      FILE_APPEND_DATA / ADD_SUBDIRECTORY 0x0004      Appendere dati / aggiungere sottocartelle
3      FILE_READ_EA                       0x0008       Leggere attributi estesi
4      FILE_WRITE_EA                      0x0010       Scrivere attributi estesi
5      FILE_EXECUTE / TRAVERSE            0x0020       Eseguire / attraversare cartella
6      FILE_DELETE_CHILD                  0x0040       Cancellare figli (solo cartelle)
7      FILE_READ_ATTRIBUTES              0x0080       Leggere attributi
8      FILE_WRITE_ATTRIBUTES             0x0100       Scrivere attributi
16     DELETE                             0x010000     Cancellare l'oggetto
17     READ_CONTROL                       0x020000     Leggere la SD (permessi)
18     WRITE_DAC                          0x040000     Modificare la DACL
19     WRITE_OWNER                        0x080000     Cambiare proprietario
20     SYNCHRONIZE                        0x100000     Sincronizzare

GENERIC_READ    = 0x80000000 → FILE_READ_DATA | FILE_READ_ATTRIBUTES | FILE_READ_EA | READ_CONTROL | SYNCHRONIZE
GENERIC_WRITE   = 0x40000000 → FILE_WRITE_DATA | FILE_APPEND_DATA | FILE_WRITE_ATTRIBUTES | FILE_WRITE_EA | READ_CONTROL | SYNCHRONIZE
GENERIC_EXECUTE = 0x20000000 → FILE_EXECUTE | FILE_READ_ATTRIBUTES | READ_CONTROL | SYNCHRONIZE
GENERIC_ALL     = 0x10000000 → tutti i bit
```

### Token di Accesso

Il token di accesso viene creato al login e accompagna il processo per tutta la sua vita. Contiene l'identità completa del principal.

```
Token di Accesso
┌────────────────────────────────────────┐
│ User SID                               │ → identità dell'utente
│ Group SIDs                             │ → tutti i gruppi di appartenenza
│ Privileges                             │ → privilegi assegnati (es. SeDebugPrivilege)
│ Logon SID                              │ → SID univoco per questa sessione
│ Default Owner                          │ → proprietario default per nuovi oggetti
│ Default DACL                           │ → DACL default per nuovi oggetti
│ Integrity Level                        │ → livello MIC
│ Claims (opzionale, DAC)                │ → attributi da AD per accesso basato su claim
│ Token Type                             │ → Primary o Impersonation
│ Impersonation Level                    │ → Anonymous, Identification, Impersonation, Delegation
└────────────────────────────────────────┘

# Visualizzare il token corrente
whoami /all
whoami /priv
whoami /groups

# Il token NON si aggiorna automaticamente dopo cambio gruppi AD.
# L'utente DEVE fare logoff/logon (o klist purge + nuovo ticket) per ricevere
# un token aggiornato con la nuova membership.
```

### Mandatory Integrity Control (MIC)

MIC aggiunge un livello di controllo *prima* della DACL. Un processo con integrità inferiore non può scrivere su un oggetto con integrità superiore, anche se la DACL lo consente.

```
Livelli di Integrità:
──────────────────────────────────────────────
System (S-1-16-16384)   → Servizi di sistema, kernel
High   (S-1-16-12288)   → Processi elevati (Run as Administrator)
Medium (S-1-16-8192)    → Processi utente standard (default)
Low    (S-1-16-4096)    → Browser sandboxed, Protected Mode IE/Edge
Untrusted (S-1-16-0)    → Processi non attendibili

Policy MIC:
- No Write Up    → processo basso non può scrivere su oggetto alto (DEFAULT)
- No Read Up     → processo basso non può leggere oggetto alto (raro)
- No Execute Up  → processo basso non può eseguire oggetto alto (raro)
```

```powershell
# Verificare il livello di integrità di un processo
whoami /groups | findstr "Label"

# Impostare integrità Low su un file
icacls "C:\Temp\sandbox.txt" /setintegritylevel low

# Verificare integrità di un file
icacls "C:\Temp\sandbox.txt" | findstr /i "integrity"

# Creare un processo a bassa integrità
# (richiede che l'eseguibile abbia livello low impostato)
icacls "C:\Tools\sandbox.exe" /setintegritylevel low
```

### SDDL — Security Descriptor Definition Language

SDDL è una rappresentazione testuale delle security descriptor. Usata nei comandi CLI, GPO, registry e API.

```
Formato SDDL:
O:owner_sid G:group_sid D:dacl_flags(ace_string)(ace_string)... S:sacl_flags(ace_string)...

Formato ACE string:
(ace_type;ace_flags;rights;object_guid;inherit_object_guid;account_sid)

Tipi ACE (ace_type):
A  = Access Allowed
D  = Access Denied
AU = System Audit
AL = System Alarm

Flag ACE (ace_flags):
CI = Container Inherit
OI = Object Inherit
IO = Inherit Only
NP = No Propagate Inherit
ID = Inherited
SA = Successful Access Audit
FA = Failed Access Audit

Diritti (rights):
GA = Generic All           GR = Generic Read
GW = Generic Write         GX = Generic Execute
FA = File All Access       FR = File Generic Read
FW = File Generic Write    FX = File Generic Execute
KA = Key All Access        KR = Key Read
KW = Key Write             KX = Key Execute
RC = Read Control          WD = Write DAC
WO = Write Owner           DE = Delete
SD = Standard Delete

SID abbreviati:
BA = BUILTIN\Administrators     BU = BUILTIN\Users
SY = NT AUTHORITY\SYSTEM        AU = Authenticated Users
WD = Everyone                   CO = Creator Owner
DA = Domain Admins              DU = Domain Users
EA = Enterprise Admins          LA = Local Administrator
```

```
Esempio SDDL reale per una cartella:
O:DA
G:DU
D:PAI(A;OICIIO;FA;;;CO)(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;0x1301bf;;;AU)
S:AI(AU;SAFAOISAFA;FA;;;WD)

Decodifica:
O:DA         → Owner: Domain Admins
G:DU         → Group: Domain Users
D:PAI        → DACL: Protetta (P), Auto-Inherited (AI)
  (A;OICIIO;FA;;;CO) → Allow, OI+CI+IO, Full Access, Creator Owner (solo figli)
  (A;OICI;FA;;;SY)   → Allow, OI+CI, Full Access, SYSTEM
  (A;OICI;FA;;;BA)    → Allow, OI+CI, Full Access, Builtin Admins
  (A;OICI;0x1301bf;;;AU) → Allow, OI+CI, diritti specifici, Authenticated Users
S:AI         → SACL: Auto-Inherited
  (AU;SAFAOISAFA;FA;;;WD) → Audit success+failure, Full Access, Everyone
```

```powershell
# Ottenere SDDL di un file
(Get-Acl "D:\Shares\Documents").Sddl

# Impostare SD da SDDL
$acl = Get-Acl "D:\Shares\Documents"
$acl.SetSecurityDescriptorSddlForm("D:PAI(A;OICI;FA;;;BA)(A;OICI;FA;;;SY)")
Set-Acl "D:\Shares\Documents" $acl

# icacls mostra SDDL con /save
icacls "D:\Shares\Documents" /save "C:\Backup\acl.txt" /t
# Il file salvato contiene SDDL
```

---

## Permessi NTFS Fondamenti

### Permessi Standard

```
Permessi FILE:
├── Full Control        → Tutto: leggere, scrivere, modificare, cancellare, cambiare permessi
├── Modify              → Leggere, scrivere, modificare, cancellare (no cambio permessi)
├── Read & Execute      → Leggere ed eseguire
├── Read                → Solo leggere
└── Write               → Creare/modificare (no cancellare, no leggere)

Permessi CARTELLA:
├── Full Control        → Tutto, incluso cambio permessi e ownership
├── Modify              → Tutto tranne cambio permessi/ownership
├── Read & Execute      → Navigare, leggere, eseguire
├── List Folder Contents→ Solo elencare contenuto (non leggere file)
├── Read                → Leggere contenuto
└── Write               → Creare file/sottocartelle
```

#### Mappatura Standard → Avanzati

```
                      Traverse  List   Read   Read   Create  Create  Write  Write  Delete  Delete  Read   Change  Take
                      Folder/   Folder Attr   Ext    Files/  Folder/ Attr   Ext    Sub &   Self    Perm   Perm    Owner
                      Execute   /Read         Attr   Write   Append         Attr   Files
                                Data                 Data    Data
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
Full Control            ✓        ✓      ✓      ✓      ✓       ✓       ✓      ✓      ✓       ✓       ✓      ✓       ✓
Modify                  ✓        ✓      ✓      ✓      ✓       ✓       ✓      ✓      ✗       ✓       ✓      ✗       ✗
Read & Execute          ✓        ✓      ✓      ✓      ✗       ✗       ✗      ✗      ✗       ✗       ✓      ✗       ✗
List Folder Contents    ✓        ✓      ✓      ✓      ✗       ✗       ✗      ✗      ✗       ✗       ✓      ✗       ✗
Read                    ✗        ✓      ✓      ✓      ✗       ✗       ✗      ✗      ✗       ✗       ✓      ✗       ✗
Write                   ✗        ✗      ✗      ✗      ✓       ✓       ✓      ✓      ✗       ✗       ✓      ✗       ✗
```

Nota: "List Folder Contents" e "Read & Execute" differiscono solo nell'ereditarietà. "List Folder Contents" eredita solo alle cartelle (CI), "Read & Execute" eredita a cartelle e file (CI+OI).

### Permessi Avanzati (Granulari)

```
I permessi Standard sono combinazioni di permessi avanzati:

Traverse Folder / Execute File
List Folder / Read Data
Read Attributes
Read Extended Attributes
Create Files / Write Data
Create Folders / Append Data
Write Attributes
Write Extended Attributes
Delete Subfolders and Files
Delete
Read Permissions
Change Permissions
Take Ownership

Esempio: "Read" = List Folder + Read Data + Read Attributes + Read Extended Attributes + Read Permissions
```

### Dettaglio dei 13 Permessi Avanzati

Ogni permesso avanzato controlla un'operazione specifica. Comprendere la granularità è essenziale per scenari complessi.

```
1. Traverse Folder / Execute File
   ├── Cartella: permette di attraversare la cartella per raggiungere
   │            file/sottocartelle, anche senza permesso di elencare il contenuto
   └── File: permette di eseguire il file come programma
   Nota: "Bypass traverse checking" è un privilegio utente (SeChangeNotifyPrivilege)
         abilitato di default per tutti. Questo rende il permesso Traverse quasi
         sempre irrilevante — ma può essere rimosso per ambienti alta sicurezza.

2. List Folder / Read Data
   ├── Cartella: permette di elencare i nomi di file e sottocartelle
   └── File: permette di leggere il contenuto del file
   È il permesso base per qualsiasi operazione di lettura.

3. Read Attributes
   Permette di leggere gli attributi base del file/cartella:
   ├── Read-only, Hidden, System, Archive
   ├── Date di creazione, ultimo accesso, ultima modifica
   └── Dimensione del file
   NON include gli attributi estesi (ADS, EA).

4. Read Extended Attributes
   Permette di leggere gli attributi estesi (Extended Attributes - EA):
   ├── Alternate Data Streams (ADS) metadata
   ├── Attributi EFS (Encrypting File System)
   └── Attributi personalizzati delle applicazioni

5. Create Files / Write Data
   ├── Cartella: permette di creare nuovi file nella cartella
   └── File: permette di sovrascrivere il contenuto del file (anche troncarlo a 0)
   Attenzione: su un file, questo permesso permette di CANCELLARE il contenuto
   sovrascrivendolo con dati vuoti, anche senza il permesso Delete.

6. Create Folders / Append Data
   ├── Cartella: permette di creare sottocartelle
   └── File: permette di aggiungere dati alla fine del file (append-only)
   Uso tipico: file di log dove gli utenti possono scrivere ma non modificare
   il contenuto esistente.

7. Write Attributes
   Permette di modificare gli attributi base:
   ├── Cambiare Read-only, Hidden, System, Archive
   └── Modificare i timestamp (date di creazione/modifica)
   Nota: un utente con Write Attributes può "falsificare" le date di un file.

8. Write Extended Attributes
   Permette di modificare gli attributi estesi:
   ├── Creare/modificare Alternate Data Streams
   └── Modificare attributi EA delle applicazioni

9. Delete Subfolders and Files
   Solo per cartelle. Permette di cancellare qualsiasi figlio (file o sottocartella)
   ANCHE SE quel figlio non ha il permesso Delete per l'utente.
   Questo è il "parent override" — il permesso sulla cartella padre sovrascrive
   il permesso Delete sul singolo oggetto figlio.

10. Delete
    Permette di cancellare L'OGGETTO STESSO.
    Per cancellare un file servono: Delete sul file OPPURE Delete Subfolders and Files
    sulla cartella padre. Uno dei due è sufficiente.

11. Read Permissions
    Permette di leggere la DACL (vedere chi ha quali permessi).
    Sempre incluso in qualsiasi permesso standard — se puoi leggere un file,
    puoi vedere i suoi permessi.

12. Change Permissions
    Permette di modificare la DACL (aggiungere/rimuovere ACE).
    Presente solo in Full Control. CRITICO: chi ha Change Permissions può
    darsi qualsiasi altro permesso, rendendolo equivalente a Full Control
    dal punto di vista pratico.

13. Take Ownership
    Permette di impostare se stessi (o il proprio gruppo) come proprietario.
    NON permette di impostare un terzo come proprietario (serve WRITE_OWNER +
    SE_RESTORE_NAME). Il proprietario ha sempre READ_CONTROL e WRITE_DAC
    impliciti — quindi prendere possesso significa poter modificare la DACL.
```

### Gestione con PowerShell

```powershell
# Leggere ACL
Get-Acl "D:\Shares\Documents" | Format-List

# Leggere ACL in dettaglio
(Get-Acl "D:\Shares\Documents").Access |
    Select-Object IdentityReference, FileSystemRights, AccessControlType, IsInherited

# Impostare proprietario
$acl = Get-Acl "D:\Shares\Documents"
$owner = New-Object System.Security.Principal.NTAccount("CORP\Admin")
$acl.SetOwner($owner)
Set-Acl "D:\Shares\Documents" $acl

# Aggiungere permesso
$acl = Get-Acl "D:\Shares\Documents"
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "CORP\GG-Marketing",           # Identità
    "Modify",                       # Permesso
    "ContainerInherit,ObjectInherit",  # Ereditarietà (cartelle + file)
    "None",                         # Propagazione
    "Allow"                         # Tipo
)
$acl.AddAccessRule($rule)
Set-Acl "D:\Shares\Documents" $acl

# Rimuovere permesso specifico
$acl = Get-Acl "D:\Shares\Documents"
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "CORP\GG-Marketing", "Modify", "Allow")
$acl.RemoveAccessRule($rule)
Set-Acl "D:\Shares\Documents" $acl

# Rimuovere TUTTI i permessi di un utente/gruppo
$acl = Get-Acl "D:\Shares\Documents"
$acl.PurgeAccessRules((New-Object System.Security.Principal.NTAccount("CORP\GG-Marketing")))
Set-Acl "D:\Shares\Documents" $acl

# Aggiungere permesso avanzato (granulare)
$acl = Get-Acl "D:\Shares\Logs"
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "CORP\GG-Auditors",
    [System.Security.AccessControl.FileSystemRights]::ReadData -bor
    [System.Security.AccessControl.FileSystemRights]::ReadAttributes -bor
    [System.Security.AccessControl.FileSystemRights]::ReadPermissions,
    "ContainerInherit,ObjectInherit",
    "None",
    "Allow"
)
$acl.AddAccessRule($rule)
Set-Acl "D:\Shares\Logs" $acl

# Creare ACE di tipo Deny
$acl = Get-Acl "D:\Shares\HR"
$denyRule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "CORP\GG-Contractors",
    "Delete,DeleteSubdirectoriesAndFiles",
    "ContainerInherit,ObjectInherit",
    "None",
    "Deny"
)
$acl.AddAccessRule($denyRule)
Set-Acl "D:\Shares\HR" $acl

# Copiare ACL da una cartella a un'altra
$sourceAcl = Get-Acl "D:\Shares\Template"
Set-Acl "D:\Shares\NewProject" $sourceAcl

# Esportare ACL in CSV per documentazione
Get-ChildItem "D:\Shares\Documents" -Recurse -Directory |
    ForEach-Object {
        $path = $_.FullName
        (Get-Acl $path).Access | Select-Object @{N='Path';E={$path}},
            IdentityReference, FileSystemRights, AccessControlType, IsInherited
    } | Export-Csv "C:\Reports\acl-report.csv" -NoTypeInformation
```

---

## Ereditarietà Permessi

### Come Funziona

```
L'ereditarietà propaga i permessi dalla cartella padre ai figli.

Cartella Padre (Permesso: GG-Staff → Read)
├── Sottocartella 1    → Eredita: GG-Staff → Read (automatico)
│   └── File A         → Eredita: GG-Staff → Read (automatico)
└── Sottocartella 2    → Eredita: GG-Staff → Read (automatico)
    └── File B         → Eredita: GG-Staff → Read (automatico)
```

### Flag di Ereditarietà in Dettaglio

```
Flag di ereditarietà:
- ContainerInherit (CI) → Sottocartelle ereditano
- ObjectInherit (OI)    → File ereditano
- InheritOnly (IO)      → Permesso si applica solo ai figli, NON all'oggetto stesso
- NoPropagateInherit (NP) → Eredita solo al primo livello (non ricorsivo)

Combinazioni e significato:

Flag              Questa cartella   Sottocartelle   File   Sotto-sottocartelle
──────────────────────────────────────────────────────────────────────────────
(nessuno)              ✓                ✗            ✗          ✗
(CI)                   ✓                ✓            ✗          ✓
(OI)                   ✓                ✗            ✓          ✗ (file in sotto: ✓)
(CI)(OI)               ✓                ✓            ✓          ✓
(IO)                   ✗                ✗            ✗          ✗ (inutile da solo)
(CI)(IO)               ✗                ✓            ✗          ✓
(OI)(IO)               ✗                ✗            ✓          ✗ (file in sotto: ✓)
(CI)(OI)(IO)           ✗                ✓            ✓          ✓
(CI)(NP)               ✓                ✓            ✗          ✗ (solo 1° livello)
(OI)(NP)               ✓                ✗            ✓          ✗ (solo 1° livello)
(CI)(OI)(NP)           ✓                ✓            ✓          ✗ (solo 1° livello)
(CI)(OI)(IO)(NP)       ✗                ✓            ✓          ✗ (solo 1° livello)
```

```
Esempio pratico NoPropagateInherit:

Scenario: Dare accesso di lettura a un consulente esterno SOLO sulla cartella
principale e le sue sottocartelle dirette, ma NON nelle sotto-sottocartelle.

D:\Projects\ClientA (CI)(NP)(RX) → CORP\Consulente
├── Docs           → Eredita (RX) ✓
│   ├── Internal   → NON eredita ✗ (NP blocca propagazione)
│   └── Draft      → NON eredita ✗
├── Reports        → Eredita (RX) ✓
│   └── Q1         → NON eredita ✗
└── file.txt       → NON eredita ✗ (manca OI)
```

### Gestione Ereditarietà

```powershell
# Disabilitare ereditarietà (copiando permessi esistenti)
$acl = Get-Acl "D:\Shares\Restricted"
$acl.SetAccessRuleProtection($true, $true)   # (protetto, copia permessi ereditati)
Set-Acl "D:\Shares\Restricted" $acl

# Disabilitare ereditarietà (rimuovendo permessi ereditati)
$acl = Get-Acl "D:\Shares\Restricted"
$acl.SetAccessRuleProtection($true, $false)  # (protetto, NON copiare)
Set-Acl "D:\Shares\Restricted" $acl

# Riabilitare ereditarietà
$acl = Get-Acl "D:\Shares\Restricted"
$acl.SetAccessRuleProtection($false, $false)
Set-Acl "D:\Shares\Restricted" $acl

# Forzare reset ereditarietà ricorsivo
icacls "D:\Shares\Documents" /reset /t /c
# Resetta tutti i permessi al valore ereditato dal padre

# Verificare se l'ereditarietà è disabilitata
$acl = Get-Acl "D:\Shares\Restricted"
$acl.AreAccessRulesProtected   # True = ereditarietà disabilitata
```

### Blocco Ereditarietà — Scenari Reali

```
Scenario 1: Cartella HR con dati sensibili dentro una share generale

D:\Shares (Everyone → Read, IT → Full Control)
├── General       → Eredita: Everyone Read ✓
├── IT            → Eredita: Everyone Read ✓ (ok, contenuto non sensibile)
└── HR            → BLOCCA EREDITARIETÀ → Solo HR-Staff → Modify, Admins → Full Control
    ├── Payroll   → Eredita da HR (HR-Staff → Modify)
    └── Contracts → Eredita da HR (HR-Staff → Modify)

Azione:
1. Disabilitare ereditarietà su D:\Shares\HR (copiando)
2. Rimuovere ACE "Everyone → Read"
3. Aggiungere ACE "CORP\GG-HR-Staff → Modify"

Scenario 2: Cartelle utente in share dipartimentale

D:\Shares\Marketing (GG-Marketing → Modify)
├── Progetti       → Eredita (GG-Marketing → Modify) ✓ collaborazione
├── Campagne       → Eredita (GG-Marketing → Modify) ✓ collaborazione
└── Personale      → BLOCCA EREDITARIETÀ
    ├── mrossi     → Solo mrossi → Modify, Admins → Full Control
    ├── gverdi     → Solo gverdi → Modify, Admins → Full Control
    └── abianchi   → Solo abianchi → Modify, Admins → Full Control
```

### Sostituzione Permessi sui Figli

```powershell
# Forzare la sostituzione di tutti i permessi figli con quelli del padre
# (GUI: Sicurezza → Avanzate → "Sostituisci tutte le autorizzazioni degli oggetti
#  figlio con autorizzazioni ereditabili da questo oggetto")

# Con icacls — reset ricorsivo
icacls "D:\Shares\Documents" /reset /t /c /q
# /t = ricorsivo, /c = continua con errori, /q = quiet

# Con PowerShell — riabilitare ereditarietà ricorsivamente
Get-ChildItem "D:\Shares\Documents" -Recurse |
    ForEach-Object {
        $acl = Get-Acl $_.FullName
        $acl.SetAccessRuleProtection($false, $false)
        Set-Acl $_.FullName $acl
    }

# Attenzione: "Replace all child permissions" nella GUI esegue DUE operazioni:
# 1. Riabilita l'ereditarietà su tutti i figli
# 2. Rimuove tutti gli ACE espliciti dai figli
# L'effetto netto: tutti i figli hanno SOLO i permessi ereditati dal padre.
```

### Troubleshooting Ereditarietà — Diagnosi Avanzata

L'ereditarietà dei permessi è il punto in cui la maggior parte dei problemi di accesso ha origine. Un blocco accidentale, una propagazione interrotta da un aggiornamento di sistema, o una migrazione di dati mal gestita possono creare situazioni in cui l'albero delle ACL diventa inconsistente. La diagnosi sistematica è fondamentale per risolvere questi scenari senza ricorrere a reset distruttivi.

```
Matrice di diagnosi ereditarietà:

Sintomo                                  Causa probabile                     Azione
────────────────────────────────────────────────────────────────────────────────────────────────
Sottocartelle non ereditano              SE_DACL_PROTECTED impostato         Verificare AreAccessRulesProtected
Permessi ereditati ma non visibili       ACE con flag IO senza CI/OI         Controllare flag con Get-Acl .Access
Nuovi file non ricevono permessi padre   OI mancante nel permesso padre      Aggiungere ObjectInherit al padre
Ereditarietà funziona a 1 livello       NP (NoPropagateInherit) attivo      Rimuovere NP flag dall'ACE
ACL "corrotte" dopo restore backup       Backup non ha preservato SD         Ripristinare da icacls /save backup
Permessi diversi tra file fratelli       Alcuni file hanno ACE espliciti     Cercare ACE con IsInherited=$false
```

```powershell
# 1. Trovare TUTTE le cartelle dove l'ereditarietà è disabilitata
# Questo è il primo passo in qualsiasi diagnosi di problemi ereditarietà

function Find-BrokenInheritance {
    param(
        [string]$RootPath,
        [switch]$IncludeFiles
    )
    $items = if ($IncludeFiles) {
        Get-ChildItem $RootPath -Recurse -ErrorAction SilentlyContinue
    } else {
        Get-ChildItem $RootPath -Recurse -Directory -ErrorAction SilentlyContinue
    }

    $items | ForEach-Object {
        $acl = Get-Acl $_.FullName -ErrorAction SilentlyContinue
        if ($acl -and $acl.AreAccessRulesProtected) {
            [PSCustomObject]@{
                Path             = $_.FullName
                Owner            = $acl.Owner
                ExplicitACECount = ($acl.Access | Where-Object { -not $_.IsInherited }).Count
                InheritedACECount = ($acl.Access | Where-Object { $_.IsInherited }).Count
            }
        }
    }
}

# Uso — scansione di una share
Find-BrokenInheritance -RootPath "D:\Shares\Documents" |
    Export-Csv "C:\Reports\broken-inheritance.csv" -NoTypeInformation

# 2. Verificare l'integrità delle ACL in un albero
# icacls /verify segnala ACL malformate, SID irrisolvibili, ordine ACE non canonico
icacls "D:\Shares\Documents" /verify /t /c /q 2>"C:\Reports\acl-errors.log"

# 3. Confrontare le ACL attese con quelle effettive
# Utile dopo migrazioni o restore da backup
function Compare-InheritedACL {
    param(
        [string]$ParentPath,
        [string]$ChildPath
    )
    $parentAcl = Get-Acl $ParentPath
    $childAcl = Get-Acl $ChildPath

    # ACE del padre che DOVREBBERO essere ereditati (con CI o OI)
    $inheritable = $parentAcl.Access | Where-Object {
        $_.InheritanceFlags -match 'ContainerInherit|ObjectInherit'
    }

    # ACE ereditati effettivamente presenti sul figlio
    $inherited = $childAcl.Access | Where-Object { $_.IsInherited }

    Write-Host "=== ACE ereditabili dal padre: $($inheritable.Count) ==="
    Write-Host "=== ACE ereditati sul figlio:  $($inherited.Count) ==="

    if ($inheritable.Count -ne $inherited.Count) {
        Write-Warning "MISMATCH: il figlio non ha ricevuto tutti gli ACE ereditabili"
        Write-Warning "Possibile ereditarietà interrotta. Verificare AreAccessRulesProtected."
    }
}

# 4. Ricostruzione sicura dell'ereditarietà su un albero corrotto
# ATTENZIONE: salvare SEMPRE un backup PRIMA di qualsiasi operazione correttiva
icacls "D:\Shares\Documents" /save "C:\Backup\acl-pre-fix.txt" /t /c

# Riabilitare ereditarietà preservando gli ACE espliciti validi
Get-ChildItem "D:\Shares\Documents" -Recurse -Directory | ForEach-Object {
    $acl = Get-Acl $_.FullName
    if ($acl.AreAccessRulesProtected) {
        Write-Host "Riabilitando ereditarietà su: $($_.FullName)"
        # $true = protetto, $true = preserva ereditati → NO
        # $false = non protetto (riabilita ereditarietà), $false = irrilevante
        $acl.SetAccessRuleProtection($false, $false)
        Set-Acl $_.FullName $acl
    }
}

# 5. Forzare la ri-propagazione dal padre senza toccare ACE espliciti
# Questo è meno distruttivo di icacls /reset /t che rimuove anche gli ACE espliciti
$parentAcl = Get-Acl "D:\Shares\Documents"
Set-Acl "D:\Shares\Documents" $parentAcl
# Il Set-Acl ri-propaga gli ACE ereditabili a tutti i figli
# dove l'ereditarietà non è esplicitamente bloccata

# 6. Trovare ACE con flag di ereditarietà anomali
(Get-Acl "D:\Shares\Documents").Access | Where-Object {
    # ACE con InheritOnly ma senza ContainerInherit né ObjectInherit
    # → ACE inutile, non si applica a nulla
    $_.PropagationFlags -match 'InheritOnly' -and
    $_.InheritanceFlags -eq 'None'
} | Select-Object IdentityReference, FileSystemRights, InheritanceFlags, PropagationFlags
```

```
Procedura di recovery per ACL corrotte dopo crash o restore:

1. BACKUP  → icacls "path" /save "backup.txt" /t /c
2. VERIFY  → icacls "path" /verify /t /c — identifica ACL corrotte
3. OWNER   → takeown /F "path" /A /R /D Y — assicura che admin abbia possesso
4. RESET   → icacls "path" /reset /t /c — reset a ereditarietà dal padre
5. APPLY   → Riapplicare gli ACE espliciti necessari da documentazione
6. VERIFY  → icacls "path" /verify /t /c — conferma integrità
7. TEST    → Testare accesso con un account non privilegiato

Se la corruzione è limitata a pochi oggetti:
- icacls "file_corrotto" /reset — reset singolo oggetto
- Se icacls fallisce: takeown + icacls /grant + icacls /reset

Se la corruzione è estesa (migliaia di oggetti):
- Ripristinare da backup che include le ACL (Windows Server Backup,
  robocopy /SEC, ntbackup)
- NON usare restore di solo dati (senza metadata) — perderebbe le ACL
```

---

## Permessi Effettivi

### Calcolo dei Permessi Effettivi

```
I permessi EFFETTIVI sono il risultato della combinazione di:
1. Permessi NTFS diretti sull'oggetto (espliciti)
2. Permessi NTFS ereditati
3. Appartenenza a gruppi (cumulativi: se in gruppo A e B, ha permessi di A + B)
4. Regole Allow e Deny (Deny vince SEMPRE su Allow)
5. Permessi Share (se accesso via rete → most-restrictive wins)
6. Mandatory Integrity Control (MIC check prima di tutto)

Regole fondamentali:
- I permessi sono CUMULATIVI per gruppo membership
- DENY esplicito vince SEMPRE su ALLOW (esplicito o ereditato)
- DENY ereditato vince su ALLOW ereditato
- DENY esplicito vince su ALLOW esplicito
- Nessun permesso = accesso negato (deny implicito)
- Owner ha sempre READ_CONTROL e WRITE_DAC impliciti
```

### Ordine di Valutazione ACE

```
Il SRM valuta gli ACE in questo ordine (CRITICO per la corretta applicazione):

1. Explicit Deny          → Deny applicati direttamente all'oggetto
2. Explicit Allow         → Allow applicati direttamente all'oggetto
3. Inherited Deny         → Deny ereditati dal padre più vicino
4. Inherited Allow        → Allow ereditati dal padre più vicino
5. (ripete 3-4 per padri più lontani nella gerarchia)

L'ordine canonico è fondamentale:
- Windows riordina automaticamente gli ACE quando usi la GUI
- icacls e API Win32 NON riordinano automaticamente
- ACE fuori ordine (es. Allow prima di Deny) causa comportamenti imprevisti

Esempio pratico:

Utente: mrossi
Gruppi: GG-Staff, GG-Marketing

ACE sulla cartella D:\Shares\Reports:
1. (Deny)  GG-Staff     → Delete                 [Explicit Deny]
2. (Allow) GG-Marketing → Modify                 [Explicit Allow]
3. (Allow) GG-Staff     → Read (ereditato)        [Inherited Allow]

Permessi effettivi di mrossi:
- Read & Execute: ✓ (da GG-Marketing Modify + GG-Staff Read ereditato)
- Write:          ✓ (da GG-Marketing Modify)
- Delete:         ✗ (Deny esplicito su GG-Staff vince su Allow di Modify)
- Change Perm:    ✗ (Modify non include Change Permissions)
```

### Strumenti di Verifica

```powershell
# Calcolare permessi effettivi (GUI)
# Proprietà → Sicurezza → Avanzate → Accesso effettivo → Seleziona utente

# Con PowerShell — analisi ACL completa
$path = "D:\Shares\Documents\Report.xlsx"
$user = "CORP\mrossi"
$acl = Get-Acl $path
$identity = New-Object System.Security.Principal.NTAccount($user)

$acl.Access | Where-Object {
    $_.IdentityReference -eq $user -or
    (Get-ADPrincipalGroupMembership $user.Split("\")[1] |
        Where-Object Name -eq $_.IdentityReference.Value.Split("\")[1])
} | Select-Object IdentityReference, FileSystemRights, AccessControlType

# Metodo rapido: verificare accesso con test .NET
function Test-FileAccess {
    param(
        [string]$Path,
        [System.Security.AccessControl.FileSystemRights]$Rights
    )
    try {
        $acl = Get-Acl $Path
        $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
        $principal = New-Object System.Security.Principal.WindowsPrincipal($identity)

        # Valuta le regole
        $allowed = $false
        $denied = $false
        foreach ($rule in $acl.Access) {
            $isMatch = $false
            if ($rule.IdentityReference.Value -eq $identity.Name) {
                $isMatch = $true
            }
            # Controlla anche i gruppi
            foreach ($group in $identity.Groups) {
                $groupName = $group.Translate([System.Security.Principal.NTAccount]).Value
                if ($rule.IdentityReference.Value -eq $groupName) {
                    $isMatch = $true
                }
            }
            if ($isMatch) {
                if ($rule.AccessControlType -eq 'Deny' -and ($rule.FileSystemRights -band $Rights)) {
                    $denied = $true
                }
                if ($rule.AccessControlType -eq 'Allow' -and ($rule.FileSystemRights -band $Rights)) {
                    $allowed = $true
                }
            }
        }
        if ($denied) { return $false }
        return $allowed
    } catch {
        return $false
    }
}

# Uso
Test-FileAccess -Path "D:\Shares\Documents\Report.xlsx" -Rights "Modify"

# accesschk (Sysinternals) — il metodo più affidabile
# Download: https://learn.microsoft.com/sysinternals/downloads/accesschk
accesschk.exe -u "CORP\mrossi" "D:\Shares\Documents" -v
accesschk.exe -u "CORP\mrossi" "D:\Shares\Documents" -d   # solo la cartella
```

---

## Share Permission vs NTFS

```
PERCORSO DI ACCESSO:

Accesso LOCALE (console, RDP):
→ Solo permessi NTFS si applicano

Accesso via RETE (\\server\share):
→ Share Permission + NTFS Permission
→ Il permesso PIÙ RESTRITTIVO tra i due vince

BEST PRACTICE:
- Share Permission: Everyone → Full Control (o Change)
- Controllare l'accesso SOLO con NTFS
- Questo semplifica la gestione: un solo punto di controllo

Eccezione: usare share permission per limitare l'accesso di massa
quando serve una "prima barriera" rapida.
```

### Matrice di Interazione

```
Permesso Share    Permesso NTFS      Accesso Effettivo (rete)
───────────────────────────────────────────────────────────────
Full Control      Full Control       Full Control
Full Control      Modify             Modify
Full Control      Read               Read
Change            Full Control       Change (più restrittivo)
Change            Modify             Modify (identico a Change)
Change            Read               Read
Read              Full Control       Read (più restrittivo)
Read              Modify             Read
Read              Read               Read
Nessuno           Full Control       Nessun accesso
Full Control      Nessuno            Nessun accesso

Nota: il confronto avviene a livello di singola operazione (read, write, delete...)
non a livello di etichetta. "Change" e "Modify" non sono identici nella composizione
esatta dei bit, ma nella pratica si comportano in modo equivalente.
```

```
Permessi Share disponibili (solo 3):

Full Control  → Leggere, scrivere, cancellare, modificare permessi share
Change        → Leggere, scrivere, cancellare (no modifica permessi share)
Read          → Solo leggere

A differenza di NTFS, i permessi share NON hanno:
- Ereditarietà granulare (si applicano a tutta la share)
- Permessi avanzati (solo 3 livelli)
- Deny (si possono negare ma è raro e sconsigliato)
```

### Gestione Share

```powershell
# Creare condivisione
New-SmbShare -Name "Documents" -Path "D:\Shares\Documents" `
    -FullAccess "Domain Admins" `
    -ChangeAccess "Authenticated Users" `
    -ReadAccess "Domain Users" `
    -Description "Documentazione aziendale"

# Modificare permessi share
Grant-SmbShareAccess -Name "Documents" -AccountName "CORP\GG-Marketing" `
    -AccessRight Change -Force

Revoke-SmbShareAccess -Name "Documents" -AccountName "Everyone" -Force

# Elencare condivisioni
Get-SmbShare | Select-Object Name, Path, Description
Get-SmbShareAccess -Name "Documents"

# ABE (Access Based Enumeration) — nascondere cartelle senza permessi
Set-SmbShare -Name "Documents" -FolderEnumerationMode AccessBased

# Sessioni attive e file aperti
Get-SmbSession | Select-Object ClientComputerName, ClientUserName, NumOpens
Get-SmbOpenFile | Select-Object ClientComputerName, ClientUserName, Path
Close-SmbSession -ClientComputerName "WKS-IT-001" -Force

# Creare share nascosta ($ alla fine)
New-SmbShare -Name "AdminData$" -Path "D:\Admin" `
    -FullAccess "Domain Admins" `
    -Description "Share amministrativa nascosta"
# Accessibile solo digitando \\server\AdminData$ — non appare in Esplora risorse

# Condivisioni amministrative predefinite
# C$, D$, ... — root di ogni volume (solo admin)
# ADMIN$ — %SYSTEMROOT% (solo admin)
# IPC$ — named pipes (connessioni inter-processo)
# PRINT$ — driver stampanti
```

---

## Ownership — Proprietà degli Oggetti

Il proprietario (Owner) di un oggetto ha diritti speciali impliciti che non possono essere revocati dalla DACL:

```
Diritti impliciti del proprietario:
├── READ_CONTROL  → può sempre leggere la DACL (vedere i permessi)
├── WRITE_DAC     → può sempre modificare la DACL (cambiare i permessi)
└── Conseguenza   → il proprietario può SEMPRE riottenere Full Control
                     anche se qualcuno ha rimosso tutti i suoi permessi

Questo è un meccanismo di sicurezza fondamentale:
- Impedisce il "lockout" permanente di un oggetto
- Il proprietario è l'ultima risorsa per recuperare l'accesso
- Solo un amministratore può cambiare il proprietario senza il suo consenso
```

### Prendere Possesso (Take Ownership)

```powershell
# Prerequisiti per prendere possesso:
# 1. Avere il permesso "Take Ownership" sull'oggetto (incluso in Full Control)
# 2. OPPURE avere il privilegio SeTakeOwnershipPrivilege (Administrators di default)
# 3. OPPURE avere SeRestorePrivilege (Backup Operators)

# Via icacls
icacls "D:\Shares\LockedFolder" /setowner "CORP\Admin" /t /c
# /t = ricorsivo, /c = continua con errori

# Via PowerShell
$acl = Get-Acl "D:\Shares\LockedFolder"
$owner = New-Object System.Security.Principal.NTAccount("CORP\Admin")
$acl.SetOwner($owner)
Set-Acl "D:\Shares\LockedFolder" $acl

# Prendere possesso quando NON si hanno permessi
# (richiede SeTakeOwnershipPrivilege, tipicamente eseguito come admin)
# Bisogna prima abilitare il privilegio nel token:

# Script completo per prendere possesso forzato
function Take-Ownership {
    param([string]$Path)

    # takeown.exe è il modo più semplice
    takeown /F $Path /A /R /D Y
    # /F = file/cartella
    # /A = assegna al gruppo Administrators
    # /R = ricorsivo
    # /D Y = risposta automatica "Sì"

    # Dopo aver preso possesso, aggiungi permessi
    icacls $Path /grant "Administrators:(OI)(CI)(F)" /t /c
}

Take-Ownership -Path "D:\Shares\LockedFolder"

# Verificare il proprietario
(Get-Acl "D:\Shares\Documents").Owner
# Output: CORP\Admin

# Elencare proprietari ricorsivamente
Get-ChildItem "D:\Shares\Documents" -Recurse |
    ForEach-Object {
        [PSCustomObject]@{
            Path = $_.FullName
            Owner = (Get-Acl $_.FullName).Owner
        }
    } | Where-Object Owner -ne "BUILTIN\Administrators"
```

### SeBackupPrivilege e SeRestorePrivilege

```
SeBackupPrivilege:
├── Consente di LEGGERE qualsiasi file, ignorando la DACL
├── Assegnato di default a: Administrators, Backup Operators
├── Usato dai software di backup per leggere file protetti
├── RISCHIO SICUREZZA: un attaccante con questo privilegio può leggere
│   qualsiasi file nel sistema (SAM, NTDS.dit, etc.)
└── Non bypassa la cifratura EFS (serve la chiave EFS separata)

SeRestorePrivilege:
├── Consente di SCRIVERE qualsiasi file, ignorando la DACL
├── Consente di cambiare il proprietario a QUALSIASI principal
│   (a differenza di SeTakeOwnershipPrivilege che permette solo "sé stesso")
├── Assegnato di default a: Administrators, Backup Operators
├── Usato dai software di backup per ripristinare file
└── RISCHIO SICUREZZA: permette di sovrascrivere file di sistema,
    DLL hijacking, modifica di qualsiasi ACL

Entrambi i privilegi:
- Devono essere ABILITATI nel token (non solo assegnati)
- L'uso richiede il flag FILE_FLAG_BACKUP_SEMANTICS nelle API
- Vengono auditati con Event ID 4674 se l'audit dei privilegi è attivo
```

```powershell
# Verificare chi ha SeBackupPrivilege
secedit /export /cfg C:\Temp\secpol.cfg
Select-String "SeBackupPrivilege" C:\Temp\secpol.cfg

# Verificare privilegi del token corrente
whoami /priv | findstr /i "backup restore"

# Rimuovere SeBackupPrivilege da un gruppo (via GPO o secpol.msc)
# Computer Configuration → Windows Settings → Security Settings →
# Local Policies → User Rights Assignment → Back up files and directories
```

---

## icacls — Gestione CLI

```powershell
# icacls è lo strumento CLI nativo per gestire permessi NTFS

# Visualizzare permessi
icacls "D:\Shares\Documents"

# Output esempio:
# D:\Shares\Documents CORP\GG-Staff:(OI)(CI)(M)
#                     BUILTIN\Administrators:(OI)(CI)(F)
#                     NT AUTHORITY\SYSTEM:(OI)(CI)(F)

# Abbreviazioni:
# F  = Full Control
# M  = Modify
# RX = Read & Execute
# R  = Read
# W  = Write
# D  = Delete

# CI = Container Inherit (sottocartelle)
# OI = Object Inherit (file)
# IO = Inherit Only

# AGGIUNGERE permesso
icacls "D:\Shares\Documents" /grant "CORP\GG-Sales:(OI)(CI)(M)"

# Con propagazione solo ai figli
icacls "D:\Shares\Documents" /grant "CORP\GG-Sales:(OI)(CI)(IO)(M)"

# RIMUOVERE permesso
icacls "D:\Shares\Documents" /remove "CORP\GG-Sales"

# NEGARE (Deny)
icacls "D:\Shares\Documents" /deny "CORP\ExternalUsers:(OI)(CI)(W)"

# APPLICARE RICORSIVAMENTE
icacls "D:\Shares\Documents" /grant "CORP\GG-Staff:(OI)(CI)(M)" /t

# RESET (ripristina ereditarietà)
icacls "D:\Shares\Documents" /reset /t /c
# /t = ricorsivo, /c = continua anche con errori

# SALVARE e RIPRISTINARE ACL (backup)
icacls "D:\Shares\Documents" /save "C:\Backup\acl-documents.txt" /t
icacls "D:\Shares" /restore "C:\Backup\acl-documents.txt"

# CAMBIARE PROPRIETARIO
icacls "D:\Shares\Documents" /setowner "CORP\Admin" /t /c

# DISABILITARE ereditarietà
icacls "D:\Shares\Restricted" /inheritance:d   # Disabilita (copia ereditati come espliciti)
icacls "D:\Shares\Restricted" /inheritance:r   # Disabilita (rimuove ereditati)
icacls "D:\Shares\Restricted" /inheritance:e   # Riabilita ereditarietà

# PERMESSI GRANULARI con icacls
# Quando serve più controllo dei permessi standard:

# Solo lettura dati e attributi (senza esecuzione)
icacls "D:\Shares\ReadOnly" /grant "CORP\GG-Viewers:(OI)(CI)(R)"

# Append-only (creare file, non modificare/cancellare)
icacls "D:\Shares\DropBox" /grant "CORP\GG-Submitters:(OI)(CI)(W)" /deny "CORP\GG-Submitters:(OI)(CI)(DE,DC)"
# DE = Delete, DC = Delete Child

# Permessi specifici con notazione estesa
icacls "D:\Shares\Custom" /grant "CORP\GG-Auditors:(OI)(CI)(RD,RA,REA,RC)"
# RD = Read Data, RA = Read Attributes, REA = Read Extended Attributes, RC = Read Control

# Verificare permessi ricorsivamente e trovare anomalie
icacls "D:\Shares\Documents" /verify /t /c
# Segnala ACL corrotte o inconsistenti

# Trovare file con permessi non ereditati (espliciti)
icacls "D:\Shares\Documents\*" /findsid "CORP\mrossi" /t
# Trova tutti gli oggetti dove CORP\mrossi ha un ACE
```

---

## Permessi Registry

Le chiavi del registro Windows hanno ACL analoghe a quelle del file system. La gestione dei permessi sul registry è fondamentale per la sicurezza del sistema.

```
Gerarchia Registry:
HKEY_LOCAL_MACHINE (HKLM)  → Configurazione macchina (richiede admin per modifiche)
HKEY_CURRENT_USER (HKCU)   → Configurazione utente corrente
HKEY_USERS (HKU)           → Tutti i profili utente caricati
HKEY_CLASSES_ROOT (HKCR)   → Merge di HKLM\SOFTWARE\Classes + HKCU\SOFTWARE\Classes
HKEY_CURRENT_CONFIG (HKCC) → Profilo hardware corrente

Permessi Registry:
├── Full Control        → Tutti i permessi
├── Read                → Query Value, Enumerate SubKeys, Notify, Read Control
├── Special Permissions → Combinazioni granulari
│
│ Permessi granulari:
├── Query Value          → Leggere valori
├── Set Value            → Scrivere/modificare valori
├── Create Subkey        → Creare sottochiavi
├── Enumerate Subkeys    → Elencare sottochiavi
├── Notify               → Ricevere notifiche di modifica
├── Create Link          → Creare link simbolici (riservato al sistema)
├── Delete               → Cancellare la chiave
├── Write DAC            → Modificare i permessi
├── Write Owner          → Cambiare il proprietario
└── Read Control         → Leggere i permessi
```

```powershell
# Leggere ACL di una chiave registry
Get-Acl "HKLM:\SOFTWARE\MyApp" | Format-List

# Dettaglio ACE
(Get-Acl "HKLM:\SOFTWARE\MyApp").Access |
    Select-Object IdentityReference, RegistryRights, AccessControlType, IsInherited

# Aggiungere permesso a una chiave registry
$acl = Get-Acl "HKLM:\SOFTWARE\MyApp"
$rule = New-Object System.Security.AccessControl.RegistryAccessRule(
    "CORP\GG-AppUsers",
    "ReadKey",
    "ContainerInherit",
    "None",
    "Allow"
)
$acl.AddAccessRule($rule)
Set-Acl "HKLM:\SOFTWARE\MyApp" $acl

# Dare accesso in scrittura a una chiave specifica
$acl = Get-Acl "HKLM:\SOFTWARE\MyApp\Config"
$rule = New-Object System.Security.AccessControl.RegistryAccessRule(
    "CORP\GG-AppAdmins",
    "FullControl",
    "ContainerInherit",
    "None",
    "Allow"
)
$acl.AddAccessRule($rule)
Set-Acl "HKLM:\SOFTWARE\MyApp\Config" $acl

# Rimuovere permesso
$acl = Get-Acl "HKLM:\SOFTWARE\MyApp"
$rule = New-Object System.Security.AccessControl.RegistryAccessRule(
    "BUILTIN\Users", "FullControl", "Allow")
$acl.RemoveAccessRule($rule)
Set-Acl "HKLM:\SOFTWARE\MyApp" $acl

# Prendere possesso di una chiave registry (come admin)
$key = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey(
    "SOFTWARE\LockedKey",
    [Microsoft.Win32.RegistryKeyPermissionCheck]::ReadWriteSubTree,
    [System.Security.AccessControl.RegistryRights]::TakeOwnership
)
$acl = $key.GetAccessControl()
$acl.SetOwner([System.Security.Principal.NTAccount]"BUILTIN\Administrators")
$key.SetAccessControl($acl)
$key.Close()

# Backup/Restore permessi registry con reg.exe
reg save HKLM\SOFTWARE\MyApp C:\Backup\myapp-reg.hiv
reg restore HKLM\SOFTWARE\MyApp C:\Backup\myapp-reg.hiv

# Audit: trovare chiavi con permessi larghi
Get-ChildItem "HKLM:\SOFTWARE" -Recurse -ErrorAction SilentlyContinue |
    ForEach-Object {
        $acl = Get-Acl $_.PSPath
        $acl.Access | Where-Object {
            $_.IdentityReference -eq "BUILTIN\Users" -and
            $_.RegistryRights -match "FullControl|SetValue"
        } | ForEach-Object {
            [PSCustomObject]@{
                Key = $_.PSPath
                Identity = $_.IdentityReference
                Rights = $_.RegistryRights
            }
        }
    }
```

---

## Permessi Servizi

Ogni servizio Windows ha una security descriptor che controlla chi può avviare, fermare, interrogare o modificare la configurazione del servizio.

```
Permessi servizio (Access Mask):
├── SERVICE_QUERY_CONFIG        (0x0001) → Leggere la configurazione
├── SERVICE_CHANGE_CONFIG       (0x0002) → Modificare la configurazione
├── SERVICE_QUERY_STATUS        (0x0004) → Leggere lo stato
├── SERVICE_ENUMERATE_DEPENDENTS(0x0008) → Elencare servizi dipendenti
├── SERVICE_START               (0x0010) → Avviare il servizio
├── SERVICE_STOP                (0x0020) → Fermare il servizio
├── SERVICE_PAUSE_CONTINUE      (0x0040) → Mettere in pausa / riprendere
├── SERVICE_INTERROGATE         (0x0080) → Interrogare il servizio
├── SERVICE_USER_DEFINED_CONTROL(0x0100) → Inviare comandi personalizzati
├── DELETE                      (0x10000)→ Cancellare il servizio
├── READ_CONTROL                (0x20000)→ Leggere la SD
├── WRITE_DAC                   (0x40000)→ Modificare la DACL
└── WRITE_OWNER                 (0x80000)→ Cambiare il proprietario

RISCHIO SICUREZZA:
SERVICE_CHANGE_CONFIG = l'attaccante può modificare il binPath del servizio,
puntandolo a un eseguibile malevolo. Al prossimo riavvio del servizio,
il codice dell'attaccante verrà eseguito con i privilegi del servizio
(spesso SYSTEM). Questa è una tecnica di privilege escalation comune.
```

```powershell
# Visualizzare la security descriptor di un servizio (SDDL)
sc.exe sdshow "Spooler"
# Output esempio:
# D:(A;;CCLCSWLOCRRC;;;AU)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)(A;;CCLCSWRPWPDTLOCRRC;;;SY)

# Decodifica SDDL servizio:
# CC = SERVICE_QUERY_CONFIG         LC = SERVICE_QUERY_STATUS
# SW = SERVICE_ENUMERATE_DEPENDENTS LO = SERVICE_INTERROGATE
# CR = SERVICE_USER_DEFINED_CONTROL RC = READ_CONTROL
# RP = SERVICE_START                WP = SERVICE_STOP
# DT = SERVICE_PAUSE_CONTINUE      SD = DELETE
# WD = WRITE_DAC                   WO = WRITE_OWNER
# DC = SERVICE_CHANGE_CONFIG

# Modificare la security descriptor di un servizio
# Attenzione: errori nella SDDL possono rendere il servizio inaccessibile!

# Dare permesso di start/stop a un gruppo specifico
$sddl = (sc.exe sdshow "MyService")[1]
# Aggiungere ACE: (A;;RPWP;;;S-1-5-21-xxx-1234) = Allow Start+Stop per il SID
$newSddl = $sddl.Replace("D:", "D:(A;;RPWP;;;S-1-5-21-xxx-1234)")
sc.exe sdset "MyService" $newSddl

# Metodo più sicuro con PowerShell e SubInACL (Sysinternals)
# SubInACL non è più distribuito; alternativa con sc.exe:

# Leggere permessi di TUTTI i servizi e trovare quelli con permessi larghi
Get-Service | ForEach-Object {
    $name = $_.Name
    $sd = sc.exe sdshow $name 2>$null
    if ($sd) {
        [PSCustomObject]@{
            Service = $name
            SDDL = ($sd | Where-Object { $_ -match '^D:' }) -join ''
        }
    }
} | Where-Object { $_.SDDL -match 'WD.*BU|DC.*BU|DC.*AU' }
# Cerca servizi dove BUILTIN\Users (BU) o Authenticated Users (AU)
# hanno WRITE_DAC o SERVICE_CHANGE_CONFIG

# Esempio: dare a HelpDesk il permesso di riavviare un servizio
# 1. Ottenere SID del gruppo
$helpDeskSid = (New-Object System.Security.Principal.NTAccount("CORP\GG-HelpDesk")).Translate(
    [System.Security.Principal.SecurityIdentifier]).Value

# 2. Ottenere SDDL corrente
$currentSddl = (sc.exe sdshow "AppService" | Where-Object { $_ -match '^D:' }) -join ''

# 3. Costruire nuovo ACE
# RPWPDTLORC = Start, Stop, Pause/Continue, Interrogate, Read Control
$newAce = "(A;;RPWPDTLORC;;;$helpDeskSid)"

# 4. Inserire prima della chiusura della DACL
$newSddl = $currentSddl -replace '^(D:.*?)$', "`$1$newAce"

# 5. Applicare
sc.exe sdset "AppService" $newSddl
```

---

## Dynamic Access Control

### Componenti DAC

```
Dynamic Access Control (DAC) è un modello di accesso avanzato introdotto in
Windows Server 2012 che estende le ACL tradizionali con:

1. Claims (Attestazioni)
   ├── User Claims: attributi dell'utente da Active Directory
   │   (Department, Country, Clearance, etc.)
   ├── Device Claims: attributi del computer da AD
   │   (Department, Location, IsManaged, etc.)
   └── Trasportati nel ticket Kerberos (richiede armoring)

2. Resource Properties (Proprietà delle Risorse)
   ├── Classificazione dei file/cartelle
   │   (Confidentiality: Public/Confidential/Secret)
   ├── Definite centralmente in AD
   └── Applicate tramite File Classification Infrastructure (FCI)
       o manualmente

3. Central Access Rules (Regole di Accesso Centrali)
   ├── Espressioni condizionali che combinano claims e resource properties
   ├── Esempio: IF user.Department == "Finance" AND
   │            resource.Confidentiality == "Confidential"
   │            THEN Allow Read
   └── Definite in AD, distribuite via GPO

4. Central Access Policies (Criteri di Accesso Centrali)
   ├── Raggruppano una o più Central Access Rules
   ├── Distribuite ai file server via GPO
   └── Applicate a cartelle/volumi specifici
```

### Implementazione DAC

```powershell
# DAC richiede:
# - Windows Server 2012+ Domain Controller
# - Functional level dominio >= Windows Server 2012
# - Kerberos armoring (claims trasportati nel ticket)
# - File Classification Infrastructure (FCI) per classificare i file

# 1. Abilitare il supporto Claims nei DC
# GPO: Computer → Administrative Templates → System → KDC →
# KDC support for claims, compound authentication and Kerberos armoring → Enabled

# 2. Abilitare il supporto Claims sui client
# GPO: Computer → Administrative Templates → System → Kerberos →
# Kerberos client support for claims, compound authentication and Kerberos armoring → Enabled

# 3. Creare Claim Type
New-ADClaimType -DisplayName "Department" -SourceAttribute "department" `
    -SuggestedValues @(
        New-Object Microsoft.ActiveDirectory.Management.ADSuggestedValueEntry("IT", "IT"),
        New-Object Microsoft.ActiveDirectory.Management.ADSuggestedValueEntry("Finance", "Finance"),
        New-Object Microsoft.ActiveDirectory.Management.ADSuggestedValueEntry("HR", "HR")
    )

# 4. Creare Resource Property
New-ADResourceProperty -DisplayName "Confidentiality" -IsSecured $true `
    -ResourcePropertyValueType "MS-DS-MultivaluedChoice" `
    -SuggestedValues @(
        New-Object Microsoft.ActiveDirectory.Management.ADSuggestedValueEntry("Public", "Public"),
        New-Object Microsoft.ActiveDirectory.Management.ADSuggestedValueEntry("Confidential", "Confidential"),
        New-Object Microsoft.ActiveDirectory.Management.ADSuggestedValueEntry("Secret", "Secret")
    )

# Aggiungere la Resource Property alla Resource Property List globale
Add-ADResourcePropertyListMember -Identity "Global Resource Property List" `
    -Members "Confidentiality"

# 5. Creare Central Access Rule
# Condizione: user.Department == "Finance" AND resource.Confidentiality == "Confidential"
# Permesso: Read
# (Configurazione da Active Directory Administrative Center → Dynamic Access Control)

# 6. Creare Central Access Policy (raggruppa regole)
# Active Directory Administrative Center → Dynamic Access Control → Central Access Policies

# 7. Distribuire via GPO:
# Computer → Windows Settings → Security Settings → File System → Central Access Policy

# 8. Applicare la policy a una cartella
# Proprietà → Sicurezza → Avanzate → Central Policy → selezionare la policy

# Classificare file con FCI (File Server Resource Manager)
# Install-WindowsFeature FS-Resource-Manager
# Configurare regole di classificazione automatica basate su contenuto o posizione

# Verificare claims nel token corrente
whoami /claims

# Verificare resource properties di un file
Get-Item "D:\Shares\Finance\Report.xlsx" |
    Select-Object -ExpandProperty Attributes
```

### Classificazione Automatica con FSRM

La classificazione manuale dei file non scala in ambienti enterprise. File Server Resource Manager (FSRM) fornisce un'infrastruttura di classificazione automatica (FCI — File Classification Infrastructure) che tagga i file in base al contenuto, alla posizione o a pattern regex.

```
Tipi di regole di classificazione FSRM:

1. Content Classifier
   ├── Scansiona il contenuto dei file alla ricerca di pattern
   ├── Supporta regex, stringhe esatte, liste di parole
   ├── Esempio: file che contengono "CONFIDENZIALE" o "NDA" → Confidentiality: Confidential
   └── Funziona su: .docx, .xlsx, .pdf, .txt, .csv e altri formati indicizzabili

2. Folder Classifier
   ├── Classifica in base alla posizione nel file system
   ├── Esempio: tutti i file in D:\Shares\Finance → Department: Finance
   └── Il metodo più affidabile e con meno overhead di CPU

3. Custom Classifier (Windows PowerShell)
   ├── Pipeline personalizzata per logica di classificazione complessa
   ├── Esempio: classificare in base ai metadati del documento
   └── Richiede sviluppo di un classification module custom
```

```powershell
# Prerequisito: installare il ruolo FSRM
Install-WindowsFeature FS-Resource-Manager -IncludeManagementTools

# Creare una proprietà di classificazione locale (se non si usa DAC centralizzato)
New-FsrmClassificationPropertyDefinition -Name "Confidentiality" `
    -Type "SingleChoice" `
    -PossibleValue @(
        (New-FsrmClassificationPropertyValue -Name "Public"),
        (New-FsrmClassificationPropertyValue -Name "Internal"),
        (New-FsrmClassificationPropertyValue -Name "Confidential"),
        (New-FsrmClassificationPropertyValue -Name "Secret")
    )

# Creare una regola di classificazione basata sul contenuto
New-FsrmClassificationRule -Name "Detect-Confidential-Content" `
    -Namespace "D:\Shares\Documents" `
    -Property "Confidentiality" `
    -PropertyValue "Confidential" `
    -ClassificationMechanism "Content Classifier" `
    -ContentRegularExpression @(
        "CONFIDENTIAL|RISERVATO|NDA|NON DIVULGARE"
    ) `
    -ReevaluateProperty Overwrite

# Creare una regola di classificazione basata sulla cartella
New-FsrmClassificationRule -Name "Finance-Folder-Classification" `
    -Namespace "D:\Shares\Finance" `
    -Property "Department" `
    -PropertyValue "Finance" `
    -ClassificationMechanism "Folder Classifier" `
    -ReevaluateProperty Overwrite

# Eseguire la classificazione manualmente (test)
Start-FsrmClassification -RunDuration 0 -Confirm:$false

# Schedulare la classificazione automatica (ogni notte alle 02:00)
Set-FsrmClassification -Schedule (New-FsrmScheduledTask -Time "02:00" `
    -Weekly @("Monday","Wednesday","Friday"))

# Verificare i risultati della classificazione
Get-FsrmClassification | Select-Object LastReportPathWithoutExtension
# Il report XML mostra quali file sono stati classificati e come

# Verificare la classificazione di un file specifico
Get-FsrmFileManagementJob | Get-FsrmStorageReport
```

```
Staging vs Enforcement nelle Central Access Policies:

STAGING (Proposed Permissions):
├── La policy viene valutata ma NON applicata
├── Genera Event ID 4818 nel Security Log
│   "Proposed Central Access Policy does not grant the same access
│    permissions as the current Central Access Policy"
├── Permette di analizzare l'impatto PRIMA di andare in produzione
└── Configurazione: nella Central Access Rule, impostare "Proposed Permissions"
    accanto ai "Current Permissions"

ENFORCEMENT:
├── La policy viene valutata E applicata
├── Gli accessi vengono concessi/negati in base alle regole DAC
├── Genera eventi standard di accesso (4663, 4656)
└── Passare da staging a enforcement SOLO dopo aver analizzato i log di staging

Best practice per il rollout DAC:
1. Definire claims e resource properties in AD
2. Creare Central Access Rules con SOLO "Proposed Permissions"
3. Distribuire via GPO ai file server di test
4. Classificare i file (FSRM o manualmente)
5. Analizzare Event ID 4818 per almeno 2 settimane
6. Se nessun impatto negativo → copiare Proposed in Current Permissions
7. Estendere a tutti i file server
```

### Espressioni Condizionali e Compound Identity

DAC supporta espressioni condizionali avanzate negli ACE, permettendo di combinare claims dell'utente, claims del dispositivo e proprietà delle risorse in una singola regola di accesso. Quando claims utente e claims dispositivo vengono valutati insieme, si parla di **Compound Identity** — una funzionalità che richiede Kerberos armoring (FAST) e Windows Server 2012+ come livello funzionale del dominio.

```
Sintassi delle espressioni condizionali negli ACE:

Formato ACE condizionale in SDDL:
(XA;;rights;;;SID;(condition))     → Conditional Allow
(XD;;rights;;;SID;(condition))     → Conditional Deny

Operatori supportati:
==    Uguale                    !=    Diverso
<     Minore                    <=    Minore o uguale
>     Maggiore                  >=    Maggiore o uguale
Contains    Contiene valore     Any_of      Almeno uno dei valori
Member_of   Membro del SID      Not_Member_of   Non membro

Riferimenti a claims e proprietà:
@User.department          → claim utente "department"
@Device.department        → claim dispositivo "department"
@Resource.Confidentiality → resource property "Confidentiality"

Esempi di espressioni condizionali:

1. Accesso solo se utente è del dipartimento Finance:
   (XA;;FR;;;AU;(@User.department == "Finance"))

2. Accesso solo da dispositivo managed del dipartimento corretto:
   (XA;;FR;;;AU;(@User.department == @Resource.Department &&
                  @Device.isManaged == true))

3. Accesso a file Confidential solo per utente con clearance:
   (XA;;FR;;;AU;(@Resource.Confidentiality == "Confidential" &&
                  @User.securityClearance >= 2))

4. Compound Identity — utente Finance da dispositivo Finance:
   (XA;;FR;;;AU;(@User.department == "Finance" &&
                  @Device.department == "Finance"))
   Questo impedisce l'accesso da dispositivi non autorizzati
   anche se l'utente è corretto (es. PC del dipartimento Marketing).
```

```powershell
# Abilitare Compound Identity (Kerberos armoring richiesto)
# GPO sui DC:
# Computer → Administrative Templates → System → KDC →
#   KDC support for claims, compound authentication
#   and Kerberos armoring → Enabled → Always provide claims

# GPO sui client:
# Computer → Administrative Templates → System → Kerberos →
#   Kerberos client support for claims, compound authentication
#   and Kerberos armoring → Enabled

# Creare Device Claim Type (esempio: isManaged)
New-ADClaimType -DisplayName "IsManaged" `
    -SourceAttribute "msDS-isManaged" `
    -SuggestedValues @(
        New-Object Microsoft.ActiveDirectory.Management.ADSuggestedValueEntry("true", "true"),
        New-Object Microsoft.ActiveDirectory.Management.ADSuggestedValueEntry("false", "false")
    ) `
    -AppliesToClasses @("computer")

# Verificare i claims del dispositivo corrente
whoami /claims
# Output include sia User Claims che Device Claims

# Verificare che il Kerberos armoring sia attivo
klist
# I ticket dovrebbero mostrare "Flags: ... PA-DATA ..." indicando armoring

# Testare una Central Access Rule con espressione condizionale
# (via Active Directory Administrative Center → DAC → Central Access Rules)
# Nella condizione: @User.department == @Resource.Department
# Questo abilita l'accesso SOLO quando il dipartimento utente
# corrisponde al dipartimento del file/cartella
```

---

## Group Policy e Permessi

### Restricted Groups

Restricted Groups controlla l'appartenenza a gruppi locali su computer di dominio. Garantisce che solo i gruppi/utenti specificati siano membri dei gruppi target.

```
Uso tipico:
- Assicurare che solo Domain Admins e IT-Support siano Administrators locali
- Impedire che utenti si aggiungano a gruppi privilegiati
- Standardizzare la membership dei gruppi su tutti i computer

Configurazione:
Computer Configuration → Windows Settings → Security Settings → Restricted Groups

Due modalità:
1. "Members of this group" → SOSTITUISCE la membership attuale
   Se specifichi solo "Domain Admins" e "GG-IT-Support", QUALSIASI altro
   membro del gruppo locale Administrators verrà RIMOSSO ad ogni refresh GPO.

2. "This group is a member of" → AGGIUNGE il gruppo come membro
   Aggiunge il gruppo specificato ai gruppi locali elencati, senza rimuovere
   i membri esistenti.
```

```powershell
# Alternativa moderna: Preferenze GP → Local Users and Groups
# Computer Configuration → Preferences → Control Panel Settings →
# Local Users and Groups

# Vantaggi rispetto a Restricted Groups:
# - Più flessibile (Add/Remove/Replace)
# - Targeting granulare (per OU, per gruppo, per filtro WMI)
# - Non sovrascrive necessariamente la membership esistente

# Verificare l'appartenenza al gruppo Administrators locale
Get-LocalGroupMember -Group "Administrators"

# Verificare le GPO applicate che gestiscono gruppi
gpresult /r /scope:computer | Select-String -Pattern "Restricted|Group"
```

### Permessi File System via GPO

```
Impostare permessi NTFS su cartelle/file in modo centralizzato tramite Group Policy.

Configurazione:
Computer Configuration → Windows Settings → Security Settings → File System

1. Tasto destro → Add File
2. Specificare il percorso (deve esistere sul computer target)
3. Configurare le ACL desiderate
4. Scegliere la modalità:
   - "Configure this file or folder then" →
     a) Propagate inheritable permissions: applica e propaga ai figli
     b) Replace existing permissions: SOVRASCRIVE tutti i permessi esistenti

Limitazioni:
- Si applica al prossimo refresh GPO (o gpupdate /force)
- Funziona solo su percorsi locali
- Non gestisce permessi share (solo NTFS)
- Se il percorso non esiste, l'impostazione viene ignorata silenziosamente
```

### Audit Policy via GPO

```
Configurazione audit centralizzata per tracciare accessi e modifiche.

Configurazione base (9 categorie):
Computer Configuration → Windows Settings → Security Settings →
Local Policies → Audit Policy

Configurazione avanzata (58 sotto-categorie):
Computer Configuration → Windows Settings → Security Settings →
Advanced Audit Policy Configuration → System Audit Policies

Categorie principali per permessi e accesso:
├── Object Access
│   ├── Audit File System          → accessi a file/cartelle
│   ├── Audit Registry             → accessi al registry
│   ├── Audit SAM                  → accessi al Security Account Manager
│   ├── Audit Handle Manipulation  → operazioni sugli handle
│   └── Audit File Share           → accessi alle share
├── Logon/Logoff
│   ├── Audit Logon                → login riusciti/falliti
│   └── Audit Account Lockout     → blocchi account
├── Privilege Use
│   ├── Audit Sensitive Privilege Use → uso di privilegi sensibili
│   └── Audit Non-Sensitive Privilege Use
├── Account Management
│   ├── Audit User Account Management
│   └── Audit Security Group Management
└── DS Access (Active Directory)
    ├── Audit Directory Service Access
    └── Audit Directory Service Changes
```

### User Rights Assignment

```
Permessi a livello di sistema operativo (non a livello di oggetto).

Computer Configuration → Windows Settings → Security Settings →
Local Policies → User Rights Assignment

Privilegi critici per la sicurezza:
──────────────────────────────────────────────────────────────────────
Privilegio                             Default              Rischio
──────────────────────────────────────────────────────────────────────
SeBackupPrivilege                      Admin, BackupOp      ALTO
  Back up files and directories        → Legge qualsiasi file
SeRestorePrivilege                     Admin, BackupOp      ALTO
  Restore files and directories        → Scrive qualsiasi file
SeTakeOwnershipPrivilege               Administrators       ALTO
  Take ownership of files              → Prende possesso di tutto
SeDebugPrivilege                       Administrators       CRITICO
  Debug programs                       → Accede alla memoria di qualsiasi processo
SeLoadDriverPrivilege                  Administrators       CRITICO
  Load and unload device drivers       → Carica driver kernel
SeImpersonatePrivilege                 Admin, Service       ALTO
  Impersonate a client                 → Si spaccia per altri utenti
SeAssignPrimaryTokenPrivilege          Service              ALTO
  Replace a process-level token        → Crea processi con altri token
SeTcbPrivilege                         Nessuno (default)    CRITICO
  Act as part of the operating system  → Potere illimitato
SeRemoteInteractiveLogonRight          Admin, RDP Users     MEDIO
  Allow log on through RDP
SeDenyNetworkLogonRight                (vuoto)              -
  Deny access from network             → Blocca login via rete
SeDenyInteractiveLogonRight            (vuoto)              -
  Deny log on locally                  → Blocca login locale
SeSecurityPrivilege                    Administrators       ALTO
  Manage auditing and security log     → Può cancellare il security log
```

---

## Delega in Active Directory

### Delega a Livello di OU

La delega AD permette di assegnare permessi amministrativi granulari su Organizational Unit specifiche, senza dare Domain Admin.

```
Scenari comuni di delega:
├── HelpDesk resetta password nella OU "Employees"
├── HR crea/modifica account nella OU "HR-Users"
├── IT-Regional gestisce computer nella OU della propria sede
└── Application Team gestisce gruppi nella OU "App-Groups"

Procedura (GUI):
1. Active Directory Users and Computers
2. Tasto destro sulla OU → "Delegate Control..."
3. Selezionare utente/gruppo delegato
4. Scegliere task predefiniti o permessi personalizzati
5. Completare il wizard

Task predefiniti nel wizard:
- Create, delete, and manage user accounts
- Reset user passwords and force password change at next logon
- Read all user information
- Create, delete, and manage groups
- Modify the membership of a group
- Manage Group Policy links
- Generate Resultant Set of Policy (Planning/Logging)
- Create, delete, and manage inetOrgPerson accounts
- Join a computer to the domain
```

### Permessi Personalizzati con dsacls

```powershell
# dsacls è il tool CLI per gestire permessi AD sugli oggetti directory

# Visualizzare permessi su una OU
dsacls "OU=Employees,DC=corp,DC=local"

# Delegare il reset password a GG-HelpDesk sulla OU Employees
dsacls "OU=Employees,DC=corp,DC=local" /G "CORP\GG-HelpDesk:CA;Reset Password;user"
# /G = Grant
# CA = Control Access (extended right)
# Reset Password = nome dell'extended right
# user = classe di oggetti target

# Delegare la creazione di utenti
dsacls "OU=Employees,DC=corp,DC=local" /G "CORP\GG-HR:CC;user"
# CC = Create Child
# user = classe di oggetti che possono essere creati

# Delegare la modifica di attributi specifici
dsacls "OU=Employees,DC=corp,DC=local" /G "CORP\GG-HR:WP;telephoneNumber;user"
dsacls "OU=Employees,DC=corp,DC=local" /G "CORP\GG-HR:WP;department;user"
dsacls "OU=Employees,DC=corp,DC=local" /G "CORP\GG-HR:WP;title;user"
# WP = Write Property

# Delegare la gestione gruppi
dsacls "OU=Groups,DC=corp,DC=local" /G "CORP\GG-AppTeam:WP;member;group"
# Permette di modificare la membership dei gruppi nella OU

# Rimuovere una delega
dsacls "OU=Employees,DC=corp,DC=local" /R "CORP\GG-HR"
# /R = Remove all ACE per quel principal

# Con PowerShell (alternativa a dsacls)
Import-Module ActiveDirectory

# Ottenere ACL di una OU
$ouPath = "AD:\OU=Employees,DC=corp,DC=local"
$acl = Get-Acl $ouPath

# Delegare reset password
$resetPwdGuid = [guid]"00299570-246d-11d0-a768-00aa006e0529"  # GUID dell'extended right "Reset Password"
$userClassGuid = [guid]"bf967aba-0de6-11d0-a285-00aa003049e2" # GUID della classe "user"

$rule = New-Object System.DirectoryServices.ActiveDirectoryAccessRule(
    (New-Object System.Security.Principal.NTAccount("CORP\GG-HelpDesk")),
    [System.DirectoryServices.ActiveDirectoryRights]::ExtendedRight,
    [System.Security.AccessControl.AccessControlType]::Allow,
    $resetPwdGuid,
    [System.DirectoryServices.ActiveDirectorySecurityInheritance]::Descendents,
    $userClassGuid
)
$acl.AddAccessRule($rule)
Set-Acl $ouPath $acl

# Audit: verificare tutte le deleghe su una OU
(Get-Acl "AD:\OU=Employees,DC=corp,DC=local").Access |
    Where-Object { -not $_.IsInherited } |
    Select-Object IdentityReference, ActiveDirectoryRights,
                  AccessControlType, ObjectType, InheritedObjectType |
    Format-Table -AutoSize
```

---

## Privileged Access Management

### Tiered Administration Model

```
Il modello a livelli (Tiered Administration) di Microsoft separa i privilegi
in tre livelli (Tier) per limitare l'impatto di una compromissione.

Principio fondamentale: le credenziali di un livello NON devono MAI
essere esposte a un livello inferiore.

Tier 0 — Controllo del Dominio (identità)
├── Domain Controllers
├── Domain Admins, Enterprise Admins, Schema Admins
├── PKI (Certificate Authority servers)
├── Account AD privilegiati
├── Strumenti: solo da PAW T0 con accesso diretto ai DC
└── REGOLA: credenziali T0 MAI su server T1 o workstation T2

Tier 1 — Server e Applicazioni
├── Member servers (file server, SQL, Exchange, etc.)
├── Server Admins (non Domain Admins)
├── Service accounts delle applicazioni
├── Strumenti: solo da PAW T1 o jump server T1
└── REGOLA: credenziali T1 MAI su workstation T2

Tier 2 — Workstation e Utenti
├── Workstation, laptop, dispositivi utente
├── HelpDesk, supporto locale
├── Account utente standard
├── Strumenti: workstation standard con UAC
└── REGOLA: il livello più esposto agli attacchi (phishing, malware)

Implementazione pratica:
1. Creare OU separate per ogni Tier
2. GPO che limita il login interattivo per livello:
   - DC: solo T0 admin
   - Server: solo T1 admin (negare T0 e T2)
   - Workstation: solo T2 admin (negare T0 e T1)
3. Creare account admin separati per ogni livello:
   - mrossi-T0 → solo per DC
   - mrossi-T1 → solo per server
   - mrossi    → uso quotidiano su workstation
4. Authentication Policies (Windows Server 2012 R2+) per
   limitare i TGT a dispositivi specifici
```

### Privileged Access Workstations (PAW)

```
Una PAW è una workstation dedicata e hardened per l'esecuzione
di attività amministrative sensibili.

Caratteristiche PAW:
├── Hardware dedicato (non VM su hypervisor non attendibile)
├── OS hardened (Windows 11 Enterprise con Device Guard)
├── Nessun accesso Internet diretto
├── Nessun software non essenziale
├── Full disk encryption (BitLocker + TPM)
├── Credential Guard abilitato (isola LSASS in VM)
├── Application Control (AppLocker o WDAC)
├── USB disabilitati (tranne tastiera/mouse)
├── Network segmentation (VLAN dedicata)
└── Monitoraggio avanzato (EDR, SIEM forwarding)

Livelli PAW:
PAW Tier 0 → Gestione DC, AD, PKI
PAW Tier 1 → Gestione server, applicazioni
PAW Tier 2 → HelpDesk, gestione workstation (opzionale, spesso jump server)

Alternative in ambienti più piccoli:
- Privileged Access Secure Environment (PASE): VM dedicata su workstation
  con Hyper-V isolation
- Sessioni RDP con Remote Credential Guard (non espone credenziali)
- Azure AD Privileged Identity Management (PIM) per JIT access

# Verificare se Credential Guard è attivo
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
    Select-Object SecurityServicesRunning
# SecurityServicesRunning: {1} = Credential Guard attivo
```

### PAM — Bastion Forest e Membership Temporanea

Privileged Access Management (PAM) per Active Directory Domain Services è una soluzione che utilizza una **foresta bastion** (bastione) dedicata per isolare i privilegi amministrativi dalla foresta di produzione. Il principio cardine è che le credenziali privilegiate non risiedono mai nella foresta esposta agli attacchi, ma vengono concesse temporaneamente attraverso un meccanismo di trust e membership a tempo limitato.

```
Architettura PAM con Bastion Forest:

┌──────────────────────────┐          ┌──────────────────────────┐
│   FORESTA PRODUZIONE     │          │   FORESTA BASTION        │
│   (corp.local)           │   TRUST  │   (bastion.local)        │
│                          │◄─────────│                          │
│ ┌──────────────────────┐ │          │ ┌──────────────────────┐ │
│ │ Domain Admins        │ │          │ │ Shadow Principals    │ │
│ │ (gruppo protetto)    │ │          │ │ (foreign principal   │ │
│ │                      │ │          │ │  groups)             │ │
│ └──────────────────────┘ │          │ ├──────────────────────┤ │
│                          │          │ │ MIM PAM Service      │ │
│ Risorse (DC, server,    │          │ │ Portale approvazione │ │
│ applicazioni)            │          │ │ Workflow Just-In-Time│ │
│                          │          │ └──────────────────────┘ │
└──────────────────────────┘          └──────────────────────────┘

Flusso di una richiesta PAM:
1. Admin richiede accesso privilegiato tramite portale MIM
2. Workflow di approvazione (automatico o manuale)
3. MIM aggiunge l'admin a un shadow security principal nel bastion
4. Il membership ha un TTL (es. 30 minuti, 4 ore)
5. Kerberos emette TGT con TTL corrispondente alla membership
6. L'admin può operare sulla foresta di produzione
7. Allo scadere del TTL, la membership viene rimossa automaticamente
8. Il TGT scade — nessun accesso residuo
```

```powershell
# ─── CONFIGURAZIONE PAM (richiede Microsoft Identity Manager) ───

# 1. Stabilire il trust PAM tra foresta produzione e bastion
# Eseguire sulla foresta bastion:
New-PAMTrust -SourceForest "corp.local" -Credentials (Get-Credential)

# Verificare il trust
Test-PAMTrust -SourceForest "corp.local"

# 2. Creare shadow security principals nel bastion
# Questi gruppi "ombra" corrispondono ai gruppi privilegiati in produzione
New-PAMGroup -SourceGroupName "Domain Admins" `
    -SourceDomain "corp.local" `
    -SourceDomainController "dc01.corp.local" `
    -Credentials (Get-Credential)

# 3. Configurare un ruolo PAM con TTL
New-PAMRole -DisplayName "Emergency Domain Admin" `
    -Privileges (Get-PAMGroup -SourceGroupName "Domain Admins") `
    -TTL (New-TimeSpan -Hours 4) `
    -MFAEnabled $true `
    -ApprovalEnabled $true `
    -AvailableFrom "08:00" `
    -AvailableTo "20:00"

# 4. Richiedere elevazione temporanea
New-PAMRequest -Role (Get-PAMRole -DisplayName "Emergency Domain Admin") `
    -Justification "Manutenzione schema AD - ticket INC-2024-001"

# 5. Verificare le richieste attive
Get-PAMRequest -Status Active |
    Select-Object Requestor, Role, TTL, ExpirationDate

# ─── MEMBERSHIP TEMPORANEA NATIVA (senza MIM) ───
# Windows Server 2016+ con PAM Feature abilitata nel dominio

# Abilitare la PAM feature opzionale nel dominio
# (richiede Forest Functional Level Windows Server 2016)
Enable-ADOptionalFeature "Privileged Access Management Feature" `
    -Scope ForestOrConfigurationSet `
    -Target "corp.local" -Confirm:$false

# Aggiungere un utente a un gruppo con TTL (membership temporanea)
Add-ADGroupMember -Identity "Domain Admins" `
    -Members "mrossi-T0" `
    -MemberTimeToLive (New-TimeSpan -Hours 2)

# Verificare la membership temporanea
Get-ADGroup "Domain Admins" -Properties member |
    Select-Object -ExpandProperty member

# Vedere il TTL residuo
Get-ADGroupMember "Domain Admins" | ForEach-Object {
    $ttl = Get-ADObject $_.DistinguishedName -Properties "msDS-MembershipExpirationTime"
    [PSCustomObject]@{
        Name = $_.Name
        ExpirationUTC = $ttl."msDS-MembershipExpirationTime"
    }
}

# La membership scade automaticamente — il TGT Kerberos associato
# diventa invalido, e l'utente perde i privilegi senza intervento manuale.
# Non richiede logoff/logon: il DC rifiuterà i ticket alla scadenza.
```

```
Vantaggi della membership temporanea rispetto all'accesso permanente:

1. Superficie d'attacco ridotta
   └── Credenziali privilegiate attive solo per la durata necessaria
2. Audit completo
   └── Ogni elevazione è tracciata con giustificazione, durata, approvatore
3. Eliminazione dello standing access
   └── "Zero Standing Privileges" — nessun admin permanente
4. Protezione da credential theft
   └── TGT rubati scadono con la membership (ore, non giorni)
5. Compliance
   └── Dimostrabile per SOX, PCI-DSS, ISO 27001: chi ha avuto quali
       privilegi, quando, per quanto tempo, e con quale giustificazione
```

### LAPS — Local Administrator Password Solution

```
LAPS (ora Windows LAPS in Windows Server 2025 / Windows 11) gestisce
automaticamente la password dell'account Administrator locale, generando
password univoche per ogni computer e salvandole in AD.

Problema che risolve:
Senza LAPS, la password dell'admin locale è spesso:
- Identica su tutti i computer (immagine deployment)
- Nota a tutti gli IT
- Mai cambiata
- Usabile per lateral movement (Pass-the-Hash)

Come funziona:
1. Client-side Extension (CSE) sul computer
2. Ad ogni refresh GPO, genera una nuova password casuale
3. Salva la password in un attributo AD del computer object
4. Solo gli utenti/gruppi con il permesso di leggere quell'attributo
   possono visualizzare la password

Implementazione LAPS legacy:
─────────────────────────────
# 1. Estendere lo schema AD (una volta, richiede Schema Admin)
Import-Module AdmPwd.PS
Update-AdmPwdADSchema

# 2. Configurare i permessi di lettura
# Solo GG-IT-Support può leggere le password nella OU "Workstations"
Set-AdmPwdReadPasswordPermission -OrgUnit "Workstations" `
    -AllowedPrincipals "CORP\GG-IT-Support"

# 3. Dare ai computer il permesso di aggiornare la propria password
Set-AdmPwdComputerSelfPermission -OrgUnit "Workstations"

# 4. Configurare GPO
# Computer → Administrative Templates → LAPS →
#   Enable local admin password management: Enabled
#   Password Settings: lunghezza, complessità, età massima

# 5. Leggere la password di un computer
Get-AdmPwdPassword -ComputerName "WKS-IT-001" | Select-Object Password, ExpirationTimestamp

Windows LAPS (nativo da Windows 11 / Server 2025):
─────────────────────────────────────────────
# Nativo nell'OS, non richiede installazione separata
# Supporta backup su Azure AD oltre che AD on-prem
# Supporta cifratura della password in AD (DPAPI-NG)
# Supporta gestione DSRM password sui DC

# Configurazione via GPO o Intune
# Computer → Administrative Templates → Windows LAPS

# Leggere la password
Get-LapsADPassword -Identity "WKS-IT-001" -AsPlainText
```

### Windows LAPS vs Legacy LAPS — Confronto Dettagliato

Con il rilascio di Windows LAPS nativo nell'OS (da Windows 11 22H2 / Server 2019 con aggiornamento di aprile 2023), il legacy LAPS basato su MSI è stato deprecato. La migrazione è fortemente consigliata. Le due soluzioni usano attributi AD diversi e possono coesistere durante il periodo di transizione, ma non dovrebbero gestire lo stesso account sullo stesso computer contemporaneamente.

```
Confronto Windows LAPS vs Legacy LAPS:

Caratteristica                 Legacy LAPS (MSI)          Windows LAPS (nativo)
─────────────────────────────────────────────────────────────────────────────────
Distribuzione                  MSI su ogni client         Integrato nell'OS
Attributi AD                   ms-Mcs-AdmPwd              msLAPS-Password
                               ms-Mcs-AdmPwdExpirationTime msLAPS-PasswordExpirationTime
                                                          msLAPS-EncryptedPassword
                                                          msLAPS-EncryptedPasswordHistory
                                                          msLAPS-EncryptedDSRMPassword
                                                          msLAPS-EncryptedDSRMPasswordHistory
Cifratura password in AD       NO (plaintext)             SÌ (DPAPI-NG, opzionale)
Cronologia password            NO                         SÌ (cronologia cifrata)
Backup su Azure AD/Entra ID   NO                         SÌ
Gestione DSRM password (DC)   NO                         SÌ
Account gestiti                Solo admin locale           Admin locale + account custom
Emulation mode                 -                          SÌ (compatibilità legacy)
Policy configurazione          GPO (AdmPwd.admx)          GPO (LAPS.admx) + Intune
Deprecazione                   Deprecato (Win 11 23H2+)  Attivo, supportato
Schema AD richiesto            Update-AdmPwdADSchema      Update-LapsADSchema
Cmdlet lettura password        Get-AdmPwdPassword         Get-LapsADPassword
Permessi self-update           Set-AdmPwdComputerSelf     Set-LapsADComputerSelfPermission
                               Permission
```

```powershell
# ─── MIGRAZIONE DA LEGACY LAPS A WINDOWS LAPS ───

# 1. Aggiornare lo schema AD per Windows LAPS
# (richiede Schema Admin — eseguire UNA VOLTA su un DC)
Update-LapsADSchema

# 2. Concedere ai computer il permesso di aggiornare i propri attributi LAPS
Set-LapsADComputerSelfPermission -Identity "OU=Workstations,DC=corp,DC=local"

# 3. Configurare i permessi di lettura per il team IT
Set-LapsADReadPasswordPermission -Identity "OU=Workstations,DC=corp,DC=local" `
    -AllowedPrincipals "CORP\GG-IT-Support"

# Permesso per leggere la cronologia password (opzionale)
Set-LapsADPasswordExpirationPermission -Identity "OU=Workstations,DC=corp,DC=local" `
    -AllowedPrincipals "CORP\GG-IT-Support"

# 4. Abilitare la cifratura (richiede Domain Functional Level 2016+)
# GPO: Computer → Administrative Templates → Windows LAPS →
#   Configure password backup directory: Active Directory
#   Enable password encryption in Active Directory: Enabled
#   Configure size of encrypted password history: 12

# 5. Abilitare emulation mode durante la transizione
# GPO: Computer → Administrative Templates → Windows LAPS →
#   Enable legacy LAPS emulation: Enabled
# In emulation mode, Windows LAPS scrive ANCHE negli attributi legacy
# permettendo agli strumenti legacy di continuare a funzionare

# 6. Leggere la password con Windows LAPS (supporta cifratura)
Get-LapsADPassword -Identity "WKS-IT-001" -AsPlainText
# Output:
#   ComputerName     : WKS-IT-001
#   Account          : Administrator
#   Password         : {H7$kL9!mN2@pQ4}
#   PasswordUpdateTime: 2026-05-20T14:30:00Z
#   ExpirationTimestamp: 2026-06-19T14:30:00Z

# 7. Gestione DSRM password sui Domain Controller
# (Directory Services Restore Mode — password di recovery del DC)
# GPO sui DC: Computer → Administrative Templates → Windows LAPS →
#   Enable password backup for DSRM accounts: Enabled
# Questo elimina il rischio di password DSRM dimenticate o mai cambiate
Get-LapsADPassword -Identity "DC01" -AsPlainText -IncludeDSRM

# 8. Dopo aver verificato che Windows LAPS funziona:
# - Disabilitare emulation mode
# - Rimuovere il GPO legacy LAPS
# - Disinstallare il client MSI legacy (se presente)
# - Rimuovere gli attributi legacy dallo schema NON è necessario né consigliato
```

### Just Enough Administration (JEA)

JEA (Just Enough Administration) è una tecnologia di sicurezza PowerShell che implementa il controllo d'accesso basato sui ruoli per l'amministrazione remota. Consente agli utenti autorizzati di eseguire comandi specifici in un contesto elevato su macchine remote, senza concedere l'accesso amministrativo completo. Ogni sessione viene registrata con trascrizioni complete, garantendo accountability e tracciabilità.

```
Architettura JEA:

┌─────────────────────────────────────────────────────────────┐
│                     JEA Endpoint                             │
│                                                              │
│  ┌──────────────────┐    ┌──────────────────────────────┐   │
│  │ Session Config   │    │ Role Capability              │   │
│  │ (.pssc)          │    │ (.psrc)                      │   │
│  │                  │    │                              │   │
│  │ Chi può connettersi│    │ Quali comandi sono permessi │   │
│  │ Quale ruolo assegnare│  │ Quali parametri sono esposti│   │
│  │ Virtual Account   │    │ Quali funzioni custom       │   │
│  │ Transcription path│    │ Quali script possono girare  │   │
│  └──────────────────┘    └──────────────────────────────┘   │
│                                                              │
│  L'utente si connette → PSSession → Virtual Account locale   │
│  Il Virtual Account è membro di Administrators               │
│  MA può eseguire SOLO i comandi definiti nel role capability  │
└─────────────────────────────────────────────────────────────┘
```

```powershell
# ─── ESEMPIO COMPLETO: JEA ENDPOINT PER HELPDESK ───
# Permettere all'HelpDesk di riavviare servizi specifici
# e resettare password AD, senza dare admin completo

# 1. Creare la directory del modulo JEA
$modulePath = "$env:ProgramFiles\WindowsPowerShell\Modules\JEA-HelpDesk"
New-Item -Path $modulePath -ItemType Directory -Force
New-Item -Path "$modulePath\RoleCapabilities" -ItemType Directory -Force

# 2. Creare il Role Capability file (.psrc)
# Definisce COSA l'utente può fare
New-PSRoleCapabilityFile -Path "$modulePath\RoleCapabilities\HelpDeskRole.psrc" `
    -VisibleCmdlets @(
        # Gestione servizi — SOLO specifici servizi
        @{
            Name       = 'Restart-Service'
            Parameters = @{ Name = 'Name'; ValidateSet = 'Spooler','W32Time','DNS','DHCP' }
        },
        @{
            Name       = 'Get-Service'
            Parameters = @{ Name = 'Name'; ValidateSet = 'Spooler','W32Time','DNS','DHCP' }
        },
        # Gestione AD — solo reset password e unlock
        'Unlock-ADAccount',
        @{
            Name       = 'Set-ADAccountPassword'
            Parameters = @{ Name = 'Identity' }
        },
        'Search-ADAccount',
        'Get-ADUser'
    ) `
    -VisibleFunctions @(
        # Funzione custom per resettare password con log
        'Reset-UserPassword'
    ) `
    -FunctionDefinitions @(
        @{
            Name = 'Reset-UserPassword'
            ScriptBlock = {
                param([string]$Username)
                $newPwd = ConvertTo-SecureString "TempP@ss$(Get-Random -Max 9999)!" -AsPlainText -Force
                Set-ADAccountPassword -Identity $Username -Reset -NewPassword $newPwd
                Set-ADUser -Identity $Username -ChangePasswordAtLogon $true
                Unlock-ADAccount -Identity $Username
                Write-Output "Password resettata per $Username. L'utente dovrà cambiarla al prossimo login."
            }
        }
    ) `
    -VisibleExternalCommands @(
        'C:\Windows\System32\ipconfig.exe',
        'C:\Windows\System32\nslookup.exe'
    )

# 3. Creare il Session Configuration file (.pssc)
# Definisce CHI può connettersi e con quale ruolo
New-PSSessionConfigurationFile -Path "$modulePath\JEA-HelpDesk.pssc" `
    -SessionType RestrictedRemoteServer `
    -RunAsVirtualAccount `
    -TranscriptDirectory "C:\JEA-Transcripts\HelpDesk" `
    -RoleDefinitions @{
        'CORP\GG-HelpDesk' = @{ RoleCapabilities = 'HelpDeskRole' }
    } `
    -LanguageMode NoLanguage `
    -ExecutionPolicy RemoteSigned

# 4. Registrare l'endpoint JEA
Register-PSSessionConfiguration -Name "JEA-HelpDesk" `
    -Path "$modulePath\JEA-HelpDesk.pssc" `
    -Force

# 5. Testare la connessione (come utente HelpDesk)
Enter-PSSession -ComputerName "SRV01" `
    -ConfigurationName "JEA-HelpDesk" `
    -Credential (Get-Credential "CORP\helpdesk-user")

# Una volta connessi, l'utente può SOLO:
# Get-Command                     → vede solo i comandi autorizzati
# Restart-Service Spooler         → ✓ consentito
# Restart-Service wuauserv        → ✗ negato (non nella ValidateSet)
# Reset-UserPassword "mrossi"     → ✓ consentito
# Get-Process                     → ✗ negato (non nel role capability)

# 6. Verificare le trascrizioni (come admin)
Get-ChildItem "C:\JEA-Transcripts\HelpDesk" -Recurse |
    Sort-Object LastWriteTime -Descending | Select-Object -First 5
# Ogni file contiene: chi si è connesso, da dove, quali comandi ha eseguito,
# output dei comandi, timestamp di ogni operazione

# 7. Audit: verificare gli endpoint JEA registrati
Get-PSSessionConfiguration | Where-Object { $_.RunAsVirtualAccount -eq $true } |
    Select-Object Name, Permission, RunAsVirtualAccount
```

```
Scenari JEA comuni in ambiente enterprise:

Scenario                  Role Capability                      Destinatari
────────────────────────────────────────────────────────────────────────────
DNS Admin delegato        Get/Add/Remove-DnsServerResourceRecord GG-DNS-Ops
                          Restart-Service DNS
Gestione servizi app      Start/Stop/Restart-Service AppService  GG-App-Team
                          Get-EventLog -LogName Application
File Server audit         Get-SmbShare, Get-SmbSession           GG-Audit
                          Get-SmbOpenFile, Get-Acl
SQL monitoring            Invoke-Sqlcmd (solo SELECT)             GG-DBA-Readonly
                          Get-Service MSSQLSERVER
Hyper-V operatore         Get/Start/Stop/Restart-VM               GG-HyperV-Ops
                          Get-VMSnapshot, Restore-VMSnapshot

Vantaggi rispetto alla delega AD tradizionale:
- Granularità a livello di parametro (non solo "può eseguire il cmdlet"
  ma "può eseguire il cmdlet solo con questi valori")
- Virtual Account: l'utente non conosce mai la password admin
- Trascrizione: ogni comando è registrato
- LanguageMode NoLanguage: impedisce l'esecuzione di codice arbitrario
- Non richiede l'utente nel gruppo Administrators locale
```

---

## Conditional Access con Azure AD / Entra ID

```
Conditional Access è il motore decisionale di Microsoft Entra ID
(ex Azure AD) per l'accesso alle risorse cloud e ibride.

Modello: IF (condizioni) THEN (azione) — applicato ad ogni autenticazione.

Segnali (Conditions):
├── Utente / Gruppo
├── Applicazione cloud target
├── Posizione (IP, paese, named location)
├── Piattaforma dispositivo (Windows, iOS, Android, macOS)
├── Stato del dispositivo (compliant, hybrid joined, managed)
├── Rischio di login (Azure AD Identity Protection)
│   ├── Rischio utente: credenziali compromesse (data breach, dark web)
│   └── Rischio sessione: IP anonimizzato, viaggio impossibile, attività anomala
├── App client (browser, app desktop, legacy auth)
└── Filtri per dispositivo (regole custom su attributi del device)

Azioni (Grant Controls):
├── Block access (nega l'accesso)
├── Grant access con requisiti:
│   ├── Require MFA
│   ├── Require compliant device
│   ├── Require Hybrid Azure AD joined device
│   ├── Require approved client app
│   ├── Require app protection policy
│   ├── Require password change
│   └── Require all / any of the above
└── Session Controls:
    ├── App-enforced restrictions (SharePoint/Exchange conditional)
    ├── Conditional Access App Control (proxy MCAS/Defender for Cloud Apps)
    ├── Sign-in frequency (richiedi re-auth ogni X ore)
    ├── Persistent browser session (ricorda/non ricordare)
    └── Disable resilience defaults

Esempio di policy comuni:
─────────────────────────
1. "Require MFA for all admins"
   IF: user in "Global Admins" / "Privileged Role Admins"
   THEN: Require MFA

2. "Block legacy authentication"
   IF: client app = "Other clients" / "Exchange ActiveSync"
   THEN: Block access

3. "Require compliant device for internal apps"
   IF: app = "SharePoint Online" / "Exchange Online"
   AND: device state != compliant
   THEN: Block access (or require MFA)

4. "Block high-risk sign-ins"
   IF: sign-in risk = High
   THEN: Block access

5. "Require MFA from untrusted locations"
   IF: location NOT IN "Corporate Network"
   THEN: Require MFA

6. "Restrict unmanaged devices"
   IF: device state != managed
   THEN: Session → App-enforced restrictions (read-only SharePoint)

Deployment:
- Usare sempre "Report-only" mode prima di abilitare
- Escludere almeno 2 break-glass accounts da TUTTE le policy
- Testare con "What If" tool nel portale
- Monitorare sign-in logs per impatto
```

### Entra Private Access per Active Directory On-Premises

A partire dal 2025, Microsoft ha introdotto **Entra Private Access** per estendere le policy di Conditional Access alle risorse on-premises, inclusi i Domain Controller Active Directory. Questa tecnologia utilizza un framework ZTNA (Zero Trust Network Access) identity-centric che funge da proxy tra il client e le risorse private, applicando le stesse policy MFA, device compliance e risk-based access che tradizionalmente erano disponibili solo per le risorse cloud.

```
Architettura Entra Private Access per AD DC:

Client (Hybrid Joined)     →    Global Secure Access Client
        │                                    │
        │ Kerberos/LDAP/RPC                  │ HTTPS tunnel
        │                                    │
        ▼                                    ▼
┌────────────────┐              ┌─────────────────────────┐
│ Domain          │   Inbound   │ Private Access Connector │
│ Controller      │◄────────────│ (installato sulla rete   │
│                 │   TCP 1337  │  interna, vicino ai DC)  │
│ SPN protetti    │              │                         │
│ via policy      │              │ Valuta Conditional      │
└────────────────┘              │ Access PRIMA di          │
                                 │ inoltrare il traffico   │
                                 └─────────────────────────┘

Requisiti:
- Client: Windows 10+ Entra Joined o Hybrid Joined
- Global Secure Access Client installato sui client
- Private Access Connector sulla rete interna
- Firewall: TCP 1337 inbound sul DC
- SPN delle applicazioni AD registrati nella policy Private Access
```

```
Scenari di protezione abilitati:

1. MFA per accesso ai DC
   IF: accesso Kerberos/LDAP al Domain Controller
   AND: utente in gruppo "Domain Admins"
   THEN: Require MFA + Compliant Device

2. Blocco accesso da dispositivi non gestiti
   IF: accesso a risorse AD on-prem
   AND: dispositivo non compliant in Intune
   THEN: Block access

3. Risk-based access per on-prem
   IF: sign-in risk = High (viaggio impossibile, IP anonimizzato)
   AND: accesso a qualsiasi risorsa privata
   THEN: Block access + alert al team security

4. Geo-restriction per admin
   IF: utente in "Enterprise Admins"
   AND: posizione NON in "Sedi Aziendali"
   THEN: Block access

Aggiornamenti enforcement 2026:
─────────────────────────────────
Microsoft ha annunciato (rollout marzo-giugno 2026) un miglioramento
dell'enforcement delle policy che eliminava un bypass noto:
- Le policy con "All cloud apps" e specifiche esclusioni potevano essere
  aggirate in scenari di autenticazione OIDC-only
- Il nuovo enforcement applica la policy anche a richieste che
  precedentemente sfuggivano alla valutazione
- Azione richiesta: verificare le policy con esclusioni e testare
  con "What If" prima della data di enforcement
```

```powershell
# Verificare la configurazione Entra Private Access
# (richiede il modulo Microsoft.Graph)
Connect-MgGraph -Scopes "NetworkAccess.ReadWrite.All"

# Elencare i connettori Private Access configurati
Get-MgServicePrincipalById -ServicePrincipalId (
    Get-MgServicePrincipal -Filter "displayName eq 'Microsoft Entra Private Access'"
).Id

# Verificare lo stato del Global Secure Access Client (lato client)
# Il client gestisce l'instradamento del traffico verso i connettori
Get-Service "Global Secure Access Client" | Select-Object Status, StartType

# Verificare la connettività al connettore
Test-NetConnection -ComputerName "connector.corp.local" -Port 443

# Configurazione Authentication Strength personalizzata
# Per richiedere metodi MFA specifici (es. FIDO2, non SMS)
# Entra Admin Center → Protection → Authentication methods →
# Authentication strengths → New authentication strength
# Usare nella policy Conditional Access come Grant control
```

---

## Configurazione Audit

### SACL — System Access Control List

La SACL definisce quali operazioni su un oggetto vengono registrate nel Security Event Log.

```
Tipi di audit:
├── Success Audit → registra quando l'operazione RIESCE
├── Failure Audit → registra quando l'operazione VIENE NEGATA
└── Entrambi possono essere configurati contemporaneamente

Prerequisiti:
1. La policy "Audit object access" deve essere abilitata (GPO o auditpol)
2. L'oggetto deve avere SACL configurata
3. Senza ENTRAMBI, nessun evento viene generato
```

```powershell
# Aggiungere SACL a una cartella (audit tutti gli accessi in scrittura)
$acl = Get-Acl "D:\Shares\Finance"
$auditRule = New-Object System.Security.AccessControl.FileSystemAuditRule(
    "Everyone",                          # Chi auditare
    "Write,Delete,ChangePermissions",    # Operazioni da auditare
    "ContainerInherit,ObjectInherit",    # Ereditarietà
    "None",                              # Propagazione
    "Success,Failure"                    # Tipo di audit
)
$acl.AddAuditRule($auditRule)
Set-Acl "D:\Shares\Finance" $acl

# Verificare la SACL
(Get-Acl "D:\Shares\Finance").Audit |
    Select-Object IdentityReference, FileSystemRights, AuditFlags

# Rimuovere una regola di audit
$acl = Get-Acl "D:\Shares\Finance"
$acl.RemoveAuditRule($auditRule)
Set-Acl "D:\Shares\Finance" $acl

# SACL con icacls
# icacls non gestisce direttamente la SACL — usare PowerShell o la GUI.
# La SACL è modificabile solo con SeSecurityPrivilege (Administrators di default).

# Audit su chiave registry
$acl = Get-Acl "HKLM:\SOFTWARE\Sensitive"
$auditRule = New-Object System.Security.AccessControl.RegistryAuditRule(
    "Everyone",
    "SetValue,Delete",
    "ContainerInherit",
    "None",
    "Success,Failure"
)
$acl.AddAuditRule($auditRule)
Set-Acl "HKLM:\SOFTWARE\Sensitive" $acl
```

### auditpol — Gestione Policy di Audit

```powershell
# auditpol è lo strumento CLI per configurare le Advanced Audit Policies

# Visualizzare tutte le policy di audit
auditpol /get /category:*

# Visualizzare una sotto-categoria specifica
auditpol /get /subcategory:"File System"
auditpol /get /subcategory:"Registry"
auditpol /get /subcategory:"Logon"

# Abilitare audit su file system (success + failure)
auditpol /set /subcategory:"File System" /success:enable /failure:enable

# Abilitare audit su registry
auditpol /set /subcategory:"Registry" /success:enable /failure:enable

# Abilitare audit su handle manipulation (per tracciare accessi dettagliati)
auditpol /set /subcategory:"Handle Manipulation" /success:enable /failure:enable

# Abilitare audit accesso file share
auditpol /set /subcategory:"File Share" /success:enable /failure:enable

# Abilitare audit logon dettagliato
auditpol /set /subcategory:"Logon" /success:enable /failure:enable
auditpol /set /subcategory:"Account Lockout" /success:enable /failure:enable

# Abilitare audit uso privilegi sensibili
auditpol /set /subcategory:"Sensitive Privilege Use" /success:enable /failure:enable

# Backup e restore delle policy di audit
auditpol /backup /file:C:\Backup\audit-policy.csv
auditpol /restore /file:C:\Backup\audit-policy.csv

# Resettare tutte le policy al default
auditpol /clear /y

# Attenzione: GPO Advanced Audit Policy sovrascrive le impostazioni locali.
# Se si usa GPO, configurare SEMPRE via GPO e non con auditpol locale.
# GPO: Computer → Windows Settings → Security Settings →
#      Advanced Audit Policy Configuration
```

### Event ID Chiave

```
Event ID     Categoria              Descrizione
────────────────────────────────────────────────────────────────────────
4624         Logon                  Login riuscito
4625         Logon                  Login fallito
4634         Logon                  Logoff
4648         Logon                  Login con credenziali esplicite (runas)
4656         Object Access          Handle richiesto su un oggetto
4660         Object Access          Oggetto cancellato
4663         Object Access          Tentativo di accesso a un oggetto
4670         Object Access          Permessi cambiati su un oggetto
4672         Logon                  Login con privilegi speciali (admin)
4674         Privilege Use          Operazione su oggetto privilegiato
4688         Process                Nuovo processo creato
4689         Process                Processo terminato
4698         Task Scheduler         Task schedulato creato
4720         Account Mgmt           Account utente creato
4722         Account Mgmt           Account utente abilitato
4724         Account Mgmt           Reset password
4728         Account Mgmt           Membro aggiunto a gruppo globale
4732         Account Mgmt           Membro aggiunto a gruppo locale
4740         Account Mgmt           Account bloccato (lockout)
4756         Account Mgmt           Membro aggiunto a gruppo universale
4768         Kerberos               TGT richiesto (AS-REQ)
4769         Kerberos               Service Ticket richiesto (TGS-REQ)
4771         Kerberos               Pre-autenticazione Kerberos fallita
4776         NTLM                   Autenticazione NTLM
5140         File Share             Accesso a share di rete
5145         File Share             Accesso a oggetto in share (dettagliato)
```

```powershell
# Consultare eventi di sicurezza recenti
Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    Id = 4663
    StartTime = (Get-Date).AddHours(-24)
} -MaxEvents 50 | Select-Object TimeCreated, Message

# Cercare tentativi di accesso negati a una cartella specifica
Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    Id = 4663
    StartTime = (Get-Date).AddDays(-7)
} | Where-Object { $_.Message -match "D:\\Shares\\Finance" -and $_.Message -match "Failure" } |
    Select-Object TimeCreated, @{N='User';E={$_.Properties[1].Value}},
                  @{N='Object';E={$_.Properties[6].Value}}

# Cercare modifiche ai permessi
Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    Id = 4670
    StartTime = (Get-Date).AddDays(-7)
} -MaxEvents 20 | ForEach-Object {
    [PSCustomObject]@{
        Time = $_.TimeCreated
        User = $_.Properties[1].Value
        Object = $_.Properties[6].Value
    }
}
```

---

## Best Practices

1. **AGDLP**: Account → Global Group → Domain Local Group → Permission. Non assegnare MAI permessi a singoli utenti.

2. **Deny con cautela**: Deny è potente ma difficile da debuggare. Preferire "non dare il permesso" piuttosto che negarlo esplicitamente.

3. **Share Permission minima**: impostare Everyone → Change sulle share, controllare tutto con NTFS.

4. **ABE sempre**: Access Based Enumeration su tutte le share — gli utenti non devono vedere cartelle a cui non hanno accesso.

5. **Non rompere l'ereditarietà senza necessità**: ogni interruzione di ereditarietà crea un punto di gestione separato. Documentare ogni interruzione.

6. **Documentare la struttura permessi**: matrice ruoli/cartelle/permessi. Rivisitare almeno semestralmente.

7. **Audit accessi**: abilitare SACL sulle cartelle sensibili per tracciare chi accede a cosa.

8. **Principio del privilegio minimo**: assegnare il permesso minimo necessario per svolgere il compito. Non dare Modify quando basta Read.

9. **Separazione dei ruoli**: usare il Tiered Administration Model. Account admin separati per DC (T0), server (T1), workstation (T2).

10. **LAPS obbligatorio**: implementare LAPS su tutte le workstation e member server. La password admin locale unica per ogni macchina impedisce il lateral movement.

11. **Credential Guard**: abilitare Credential Guard su tutte le macchine Windows 10/11 Enterprise per proteggere credenziali in memoria.

12. **Eliminare NTLM dove possibile**: NTLM è vulnerabile a relay e pass-the-hash. Forzare Kerberos dove supportato. Monitorare l'uso NTLM con Event ID 4776.

13. **Review periodica degli ACL**: creare un processo trimestrale di revisione dei permessi su share, OU AD e GPO. Cercare ACE per utenti/gruppi inesistenti.

14. **Backup regolare delle ACL**: usare `icacls /save` per documentare e poter ripristinare le ACL critiche.

15. **Non usare Domain Admins per l'amministrazione quotidiana**: usare account separati con permessi delegati appropriati.

16. **Proteggere i gruppi privilegiati**: monitorare le modifiche a Domain Admins, Enterprise Admins, Schema Admins, Backup Operators con alert in tempo reale.

17. **Disabilitare l'autenticazione legacy**: bloccare NTLM v1, LM hash storage, null sessions. Conditional Access per bloccare legacy auth in Azure AD.

18. **Just-In-Time (JIT) Access**: usare Azure AD PIM o soluzioni PAM per concedere privilegi temporanei anziché permanenti.

19. **Classificazione dei dati**: implementare DAC o almeno una classificazione manuale (Public, Internal, Confidential, Restricted) per applicare permessi coerenti.

20. **Test delle modifiche**: usare "What-If" / "Accesso effettivo" prima di applicare modifiche ai permessi. Testare con un account non privilegiato.

---

## Troubleshooting

**"Accesso negato nonostante i permessi sembrino corretti"** → Verificare: permessi effettivi (tab Accesso effettivo), Deny esplicito o ereditato, permessi share (se accesso via rete), ABE attivo, proprietario del file, token utente (logoff/logon per aggiornare gruppi).

**"Permessi non si propagano ai sottocartelle"** → Verificare ereditarietà: `icacls path` → se non ci sono (CI)(OI) il permesso non si eredita. Verificare che l'ereditarietà non sia disabilitata sulla sottocartella.

**"Utente vede cartelle che non dovrebbe vedere"** → ABE non è attivo (`Set-SmbShare -FolderEnumerationMode AccessBased`). ABE funziona solo per accessi via rete (share), non per accessi locali.

**"Cambio permessi ricorsivo è lentissimo"** → Su milioni di file, `icacls /t` può impiegare ore. Considerare: disabilitare ereditarietà e riabilitarla (propaga istantaneamente), usare `robocopy /SEC` per copiare ACL in modo efficiente, o schedulare in ore notturne.

**"L'utente ha appena cambiato gruppo ma non vede le cartelle"** → Il token Kerberos non viene aggiornato automaticamente. L'utente deve fare logoff/logon. In dominio, anche `klist purge` e riapertura della sessione. Per RDP: disconnettere completamente (non solo bloccare).

**"Deny non funziona come previsto"** → Verificare che il Deny sia applicato al SID corretto. Se il Deny è su un gruppo ma l'utente accede tramite un altro gruppo con Allow, il Deny vince comunque. Ma se il Deny è ereditato e l'Allow è esplicito, l'Allow vince? NO — in Windows il Deny esplicito vince sempre. Verificare l'ordine ACE con `(Get-Acl path).Access`.

**"Proprietario cambiato e ora nessuno può accedere"** → Il proprietario ha sempre READ_CONTROL e WRITE_DAC impliciti. Contattare il proprietario per riaggiungere le ACE, oppure un admin con SeTakeOwnershipPrivilege può prendere possesso e ripristinare la DACL.

**"icacls restituisce errore 'Access is denied' durante /setowner"** → Eseguire il comando come Administrator con SeTakeOwnershipPrivilege abilitato. Se il file è su un volume remoto, i privilegi locali non si applicano — serve un account con privilegi sul server remoto.

**"ACL corrotte dopo un crash / restore da backup"** → Verificare con `icacls path /verify`. Se corrotte, `icacls path /reset /t /c` ripristina le ACL ereditando dal padre. Se serve una ACL specifica, ripristinare dal backup salvato con `icacls /save`.

**"Permesso Read & Execute non permette di eseguire un .exe"** → Verificare: 1) SRP/AppLocker/WDAC potrebbe bloccare l'esecuzione indipendentemente dai permessi NTFS. 2) L'eseguibile potrebbe essere bloccato dal flag "Zone.Identifier" (downloaded from Internet): `Unblock-File file.exe` o tasto destro → Sblocca.

**"Set-Acl fallisce con 'The security identifier is not allowed'"** → Si sta cercando di impostare un SID non valido come proprietario (es. un SID di un dominio non trusted o un SID inesistente). Verificare la risoluzione del nome con `New-Object System.Security.Principal.NTAccount("DOMAIN\user")`.

**"L'utente non riesce a cancellare un file nonostante abbia Modify"** → Se il file ha il flag ReadOnly impostato, la cancellazione fallisce anche con permessi Modify. Rimuovere il flag: `attrib -r file.txt`. Altra causa: il file è aperto da un altro processo — verificare con `Get-SmbOpenFile` o Process Explorer.

**"Permessi share funzionano da un PC ma non da un altro"** → Verificare: 1) Lo stesso utente sta usando credenziali cached diverse. 2) Il computer potrebbe avere GPO diverse (Restricted Groups, User Rights). 3) Il firewall potrebbe bloccare SMB (TCP 445). 4) Kerberos potrebbe fallire su un PC e usare NTLM sull'altro (SPN issues).

**"GPO Restricted Groups rimuove gli admin locali"** → Questo è il comportamento atteso di "Members of this group". Per aggiungere membri SENZA rimuovere quelli esistenti, usare Preferences → Local Users and Groups con azione "Update" invece di Restricted Groups.

**"SACL configurata ma nessun evento nel Security Log"** → Verificare: 1) `auditpol /get /subcategory:"File System"` — deve mostrare Success/Failure. 2) La GPO potrebbe sovrascrivere le impostazioni locali. 3) Il Security Log potrebbe essere pieno — verificare dimensione e retention. 4) Se si usa Advanced Audit Policy via GPO, la Basic Audit Policy viene ignorata.

**"L'utente ha Full Control ma non riesce a cambiare il proprietario"** → Full Control include Take Ownership, ma Take Ownership permette solo di impostare SE STESSI come proprietario. Per impostare un TERZO come proprietario serve SeRestorePrivilege. Anche con WRITE_OWNER, Windows valida che il nuovo owner sia il caller o un gruppo di cui è membro.

**"Dopo aver disabilitato l'ereditarietà, i permessi dei file dentro sono spariti"** → Si è usato `SetAccessRuleProtection($true, $false)` che disabilita l'ereditarietà e RIMUOVE tutti i permessi ereditati. Se non c'erano ACE espliciti, il risultato è una DACL vuota = nessun accesso (tranne per l'Owner). Soluzione: prendere possesso come admin, riabilitare l'ereditarietà o aggiungere ACE espliciti.

**"Il servizio non si avvia dopo aver modificato la DACL del servizio"** → La SDDL impostata con `sc sdset` potrebbe essere malformata o non includere SYSTEM (SY). SYSTEM deve sempre avere accesso ai servizi. Ripristinare: `sc sdset ServiceName "D:(A;;CCLCSWRPWPDTLOCRRC;;;SY)(A;;CCDCLCSWRPWPDTLOCRSDRCWDWO;;;BA)"`.

**"Lateral movement tramite admin locale con stessa password"** → Implementare LAPS immediatamente. Fino a LAPS, cambiare le password admin locali e renderle uniche per macchina. Disabilitare WDigest (`HKLM\SYSTEM\CurrentControlSet\Control\SecurityProviders\WDigest` → `UseLogonCredential = 0`).

**"L'utente non riesce ad accedere a una sottocartella nonostante abbia permessi sulla share"** → La sottocartella potrebbe avere l'ereditarietà disabilitata con permessi restrittivi. Verificare: `icacls "percorso\sottocartella"`. Se l'ereditarietà è disabilitata, i permessi del padre non si propagano — servono ACE espliciti sulla sottocartella.

**"Accesso negato a chiavi registry dopo aggiornamento Windows"** → Windows Update può reimpostare le ACL su chiavi di sistema. Verificare e ripristinare con `Get-Acl/Set-Acl`. Per chiavi personalizzate dell'applicazione, mantenere un backup SDDL e un task schedulato che verifichi periodicamente.

**"Token bloat — autenticazione lenta o fallisce per troppi gruppi"** → Il token Kerberos ha un limite di dimensione (default 12 KB per HTTP, 48 KB per altri). Se un utente è membro di troppi gruppi (>1000), il ticket è troppo grande. Soluzioni: ridurre la group membership, aumentare `MaxTokenSize` via GPO, o passare a claims-based access (DAC) che non soffre di questo limite.

---

## FAQ — Domande Frequenti

**D1: Qual è la differenza tra permessi NTFS e permessi Share?**
I permessi NTFS sono salvati nel file system e si applicano SEMPRE (accesso locale e rete). I permessi Share si applicano SOLO per accessi via rete (\\server\share). Quando si accede via rete, si applica il risultato più restrittivo tra i due. Best practice: usare permessi Share larghi (Everyone → Change) e controllare tutto con NTFS.

**D2: Se un utente è in due gruppi con permessi diversi, quale prevale?**
I permessi sono cumulativi. Se il Gruppo A ha Read e il Gruppo B ha Write, l'utente ha Read + Write. L'unica eccezione è Deny, che vince SEMPRE su Allow indipendentemente dalla fonte.

**D3: Un Deny ereditato perde contro un Allow esplicito?**
NO. In Windows, Deny vince SEMPRE su Allow. L'ordine di valutazione (esplicito prima di ereditato) non cambia questa regola — il SRM raccoglie tutti i Deny e tutti gli Allow, e se c'è un Deny per un'operazione specifica, quell'operazione è negata.

**D4: Come faccio a sapere rapidamente i permessi effettivi di un utente su un file?**
GUI: tasto destro → Proprietà → Sicurezza → Avanzate → Accesso effettivo → selezionare l'utente. CLI: `accesschk.exe -u "DOMAIN\user" "percorso" -v` (Sysinternals). L'unico metodo 100% affidabile è accedere effettivamente al file con quell'account.

**D5: Quando devo usare "List Folder Contents" anziché "Read & Execute"?**
Quasi mai come scelta esplicita. La differenza è nell'ereditarietà: List Folder Contents eredita solo alle sottocartelle (CI), Read & Execute eredita a sottocartelle e file (CI+OI). In pratica, Read & Execute è quasi sempre quello che si vuole.

**D6: Posso recuperare l'accesso a un file se la DACL è vuota?**
Sì. Il proprietario (Owner) ha sempre READ_CONTROL e WRITE_DAC impliciti, quindi può riaprire i permessi. Se anche il proprietario è inaccessibile, un amministratore con SeTakeOwnershipPrivilege può prendere possesso e poi modificare la DACL.

**D7: Come funziona l'ereditarietà con NoPropagateInherit?**
NoPropagateInherit (NP) fa sì che il permesso venga ereditato SOLO dai figli diretti (primo livello), non dai nipoti. Utile quando si vuole dare accesso a una cartella e alle sue sottocartelle immediate, ma non alle sotto-sottocartelle.

**D8: Perché i permessi non cambiano dopo aver modificato la membership di un gruppo?**
Il token di accesso dell'utente viene creato al login e non si aggiorna dinamicamente. L'utente deve fare logoff/logon per ottenere un nuovo token con la membership aggiornata. Per Kerberos, `klist purge` forza il rinnovo dei ticket.

**D9: Cos'è AGDLP e perché è importante?**
AGDLP = Account → Global Group → Domain Local Group → Permission. L'account utente va in un Global Group (per ruolo funzionale, es. GG-Marketing), il Global Group va in un Domain Local Group (per accesso specifico, es. DL-Share-Marketing-RW), e il Domain Local Group riceve il permesso sulla risorsa. Questo modello scala in ambienti multi-dominio e separa il "chi" dal "cosa può fare".

**D10: Come proteggo i file server dal lateral movement?**
1) LAPS per password admin locali uniche. 2) Credential Guard per proteggere credenziali in memoria. 3) Tiered Administration — non usare account T0 su file server (T1). 4) Disabilitare WDigest. 5) Remote Credential Guard per sessioni RDP. 6) Monitorare Event ID 4624 tipo 3 (network logon) e 4648 (explicit credentials).

**D11: Qual è la differenza tra SeTakeOwnershipPrivilege e SeRestorePrivilege per cambiare il proprietario?**
SeTakeOwnershipPrivilege permette di impostare come proprietario SOLO se stessi (o un gruppo di cui si è membri). SeRestorePrivilege permette di impostare come proprietario QUALSIASI principal, anche un terzo. Ecco perché SeRestorePrivilege è considerato più pericoloso.

**D12: Come implemento un "drop box" dove gli utenti possono depositare file ma non modificarli/leggerli dopo?**
Creare una cartella con: Write (per creare file) ma senza Read e senza Modify. L'utente può copiare file nella cartella ma non può vedere cosa c'è dentro né modificare i file dopo averli creati. icacls: `/grant "Users:(CI)(W)" /deny "Users:(CI)(OI)(RD,DE,DC)"`. Solo gli admin potranno leggere/gestire i file depositati.

**D13: Come monitoro le modifiche ai permessi in tempo reale?**
1) Abilitare audit "Object Access → File System" (success). 2) Configurare SACL sulla cartella per "Change Permissions" e "Take Ownership". 3) Event ID 4670 registra ogni modifica ai permessi. 4) Inoltrare gli eventi a un SIEM o usare Windows Event Forwarding (WEF) per centralizzare. 5) Creare alert per modifiche su cartelle critiche.

**D14: Qual è il rischio di una "null DACL" (DACL assente)?**
Una DACL assente (non vuota, ma proprio assente nella SD) significa che TUTTI hanno FULL ACCESS all'oggetto. È diverso da una DACL vuota (nessun ACE) che nega l'accesso a tutti tranne il proprietario. La null DACL è pericolosa e non dovrebbe mai esistere in produzione. Verificare: `(Get-Acl path).AreAccessRulesCanonical` e controllare il conteggio ACE.

**D15: Come gestisco i permessi in un ambiente ibrido (on-prem + Azure AD)?**
Usare Azure AD Connect per sincronizzare le identità. I permessi NTFS on-prem continuano a funzionare con SID AD. Per risorse cloud, usare Conditional Access + Azure RBAC. Per file share ibride, Azure Files supporta autenticazione AD DS per mantenere le ACL NTFS nel cloud. Per la gestione centralizzata, considerare Microsoft Entra Permissions Management.

**D16: Come verifico che non ci siano ACE orfani (riferiti a SID cancellati)?**
Gli ACE orfani appaiono come SID numerici (S-1-5-21-...) anziché come nomi. Script di verifica:
```powershell
Get-ChildItem "D:\Shares" -Recurse -Directory | ForEach-Object {
    (Get-Acl $_.FullName).Access |
        Where-Object { $_.IdentityReference.Value -match '^S-1-5-21-' } |
        ForEach-Object {
            [PSCustomObject]@{
                Path = $_.FullName
                OrphanSID = $_.IdentityReference.Value
                Rights = $_.FileSystemRights
            }
        }
}
```
Questi ACE dovrebbero essere rimossi per pulizia e per evitare che un SID riciclato ottenga accesso non intenzionale.

**D17: In che modo UAC interagisce con i permessi NTFS?**
UAC crea un token "filtered" per gli admin, con i privilegi amministrativi rimossi. Quando l'admin accede a un file che richiede privilegi elevati, il token filtrato viene usato e l'accesso potrebbe essere negato. "Run as Administrator" usa il token completo (unfilitered). Questo è il motivo per cui un admin può vedere "Accesso negato" su un cmd non elevato ma non su uno elevato, anche se la DACL concede Full Control a Administrators.

---

## Esercizi

### Esercizio 1: Analisi ACL e Best Practice AGDLP

Su un file server di lab, implementare la struttura AGDLP completa:

1. Creare una struttura cartelle `D:\Shares\Progetti\{Alpha,Beta,Gamma}`.
2. Creare gruppi AD: Global Groups (`GG-Progetto-Alpha-RW`, `GG-Progetto-Alpha-RO`) e Domain Local Groups (`DL-Share-Alpha-Modify`, `DL-Share-Alpha-Read`).
3. Assegnare permessi NTFS ai gruppi Domain Local con `icacls` o `Set-Acl`.
4. Disabilitare l'ereditarietà sulla cartella root e configurare permessi espliciti.
5. Verificare i permessi effettivi con `Get-Acl` e `icacls /verify`.

**Criteri di validazione**: un utente membro di `GG-Progetto-Alpha-RW` deve poter creare e modificare file in Alpha, ma non in Beta/Gamma. Un utente senza appartenenza a nessun gruppo deve ricevere "Accesso negato".

### Esercizio 2: Audit SACL e Monitoraggio Accessi

Configurare l'audit completo dell'accesso ai file:

1. Abilitare la policy di audit con `auditpol /set /subcategory:"File System" /success:enable /failure:enable`.
2. Configurare una SACL su `D:\Shares\Riservato` per tracciare accessi in lettura e scrittura del gruppo "Everyone".
3. Generare eventi di accesso (accedere a file, tentare accesso negato).
4. Analizzare Event ID 4663 (Object Access) con `Get-WinEvent` e filtrare per ObjectName.
5. Creare un report con i 10 utenti che hanno acceduto più frequentemente.

**Criteri di validazione**: gli eventi 4663 devono mostrare chi ha acceduto, a quale file, con quale operazione e l'orario UTC.

### Esercizio 3: Rilevamento ACE Orfani e Pulizia

Creare uno script PowerShell per identificare e gestire ACE orfani:

1. Scansionare ricorsivamente `D:\Shares` e raccogliere tutte le ACE il cui `IdentityReference` corrisponde a un SID numerico (S-1-5-21-...).
2. Per ogni ACE orfano, documentare: percorso, SID, diritti assegnati.
3. Generare un report CSV e un conteggio per cartella.
4. Implementare un parametro `-RemoveOrphans` con conferma (`-Confirm`) per la rimozione.

**Criteri di validazione**: lo script deve identificare correttamente SID orfani senza toccare SID well-known (S-1-5-18, S-1-5-32-*, ecc.).

### Esercizio 4: Configurazione Dynamic Access Control

In un ambiente AD di lab, configurare DAC:

1. Definire un claim type basato sul dipartimento dell'utente (`department`).
2. Creare una resource property "Classificazione" con valori "Pubblico", "Interno", "Riservato".
3. Configurare una Central Access Rule: i file classificati "Riservato" sono accessibili solo a utenti del dipartimento "Sicurezza".
4. Applicare la Central Access Policy via GPO al file server.
5. Verificare che un utente del dipartimento "Marketing" non possa accedere ai file "Riservato".

**Criteri di validazione**: `Get-Acl` deve mostrare la Central Access Policy applicata. L'accesso deve essere correttamente concesso/negato in base ai claims.

---

## Auto-valutazione

### Domanda 1

Qual è la differenza tra una DACL vuota e una DACL assente (null DACL)?

<details>
<summary>Risposta</summary>

Una DACL vuota (zero ACE) nega l'accesso a tutti tranne al proprietario dell'oggetto. Una DACL assente (null DACL) significa che non esiste alcun controllo di accesso e TUTTI hanno FULL ACCESS all'oggetto. La null DACL è estremamente pericolosa e non dovrebbe mai esistere in produzione. Verificare con `(Get-Acl path).AreAccessRulesCanonical` e controllare il conteggio ACE.

Riferimento: Microsoft Learn, Access Control Lists. Consultato: 2026-05-23.
</details>

### Domanda 2

Spiegare il modello AGDLP e perché è la best practice raccomandata.

<details>
<summary>Risposta</summary>

AGDLP = Account → Global Group → Domain Local Group → Permissions. Gli account utente sono membri di Global Groups (raggruppamento logico per ruolo/progetto). I Global Groups sono membri di Domain Local Groups (che rappresentano i permessi su una risorsa specifica). I permessi NTFS/share sono assegnati solo ai Domain Local Groups. Questo modello separa "chi sono" (Global) da "cosa possono fare" (Domain Local), semplifica la gestione multi-dominio, e rende i permessi auditabili.

Riferimento: Microsoft Learn, Best practices for assigning permissions. Consultato: 2026-05-23.
</details>

### Domanda 3

Come funziona il Mandatory Integrity Control (MIC) e quale relazione ha con UAC?

<details>
<summary>Risposta</summary>

MIC assegna un livello di integrità (Low, Medium, High, System) a processi e oggetti. Un processo non può scrivere su un oggetto con livello di integrità superiore ("no write up"). UAC crea token filtrati per gli admin con livello Medium; l'elevazione ("Run as Administrator") usa il token completo con livello High. Questo impedisce a processi non elevati di modificare risorse di sistema, anche se la DACL lo permetterebbe.

Riferimento: Microsoft Learn, Mandatory Integrity Control. Consultato: 2026-05-23.
</details>

### Domanda 4

Qual è la differenza tra permessi NTFS e permessi share? Quale prevale?

<details>
<summary>Risposta</summary>

I permessi NTFS sono granulari, si applicano sia all'accesso locale che remoto, e viaggiano con il file se copiato su un altro volume NTFS. I permessi share si applicano solo all'accesso via rete e sono meno granulari (Read, Change, Full Control). Quando un utente accede a un file via share, si applicano entrambi e il risultato è il più restrittivo dei due (most-restrictive wins). Best practice: impostare share permissions a "Everyone: Full Control" e gestire l'accesso solo tramite NTFS.

Riferimento: Microsoft Learn, Share and NTFS Permissions. Consultato: 2026-05-23.
</details>

### Domanda 5

Come si configura LAPS per la gestione delle password degli admin locali?

<details>
<summary>Risposta</summary>

LAPS (Local Administrator Password Solution) genera password casuali e univoche per l'account admin locale di ogni computer, le memorizza in un attributo AD protetto da ACL, e le ruota automaticamente. Configurazione: estendere lo schema AD con `Update-AdmPwdADSchema`, configurare i permessi con `Set-AdmPwdComputerSelfPermission`, distribuire il CSE via GPO. Windows LAPS (integrato da Windows 11 22H2 e Server 2019+) sostituisce il LAPS legacy con supporto Azure AD e backup in Azure.

Riferimento: Microsoft Learn, Windows LAPS. Consultato: 2026-05-23.
</details>

### Domanda 6

Cosa rappresenta SDDL e quando è utile?

<details>
<summary>Risposta</summary>

SDDL (Security Descriptor Definition Language) è una rappresentazione testuale compatta del Security Descriptor di un oggetto. Formato: `O:owner-SID G:group-SID D:dacl-flags(ace-list) S:sacl-flags(ace-list)`. Ogni ACE ha il formato `(type;flags;rights;object-guid;inherit-guid;account-SID)`. È utile per: automazione con script, backup/restore di permessi, documentazione, confronto tra configurazioni, e troubleshooting. `ConvertFrom-SddlString` in PowerShell converte SDDL in formato leggibile.

Riferimento: Microsoft Learn, Security Descriptor String Format. Consultato: 2026-05-23.
</details>

---

## Letture Primarie Consigliate

1. **Microsoft Learn: Access Control Overview** — Modello di controllo accessi Windows, SID, token, DACL, SACL.
   https://learn.microsoft.com/en-us/windows/security/identity-protection/access-control/
   Consultato: 2026-05-23.

2. **Microsoft Learn: NTFS Permissions Reference** — Permessi standard e avanzati NTFS, ereditarietà, best practice.
   https://learn.microsoft.com/en-us/windows-server/storage/file-server/ntfs-overview
   Consultato: 2026-05-23.

3. **Microsoft Learn: Windows LAPS** — Guida completa a Local Administrator Password Solution.
   https://learn.microsoft.com/en-us/windows-server/identity/laps/laps-overview
   Consultato: 2026-05-23.

4. **Microsoft Learn: Dynamic Access Control** — Configurazione DAC con claims, resource properties, e Central Access Policies.
   https://learn.microsoft.com/en-us/windows-server/identity/solution-guides/dynamic-access-control-overview
   Consultato: 2026-05-23.

5. **Microsoft Learn: Auditing File System** — Configurazione SACL, auditpol, e analisi eventi di accesso.
   https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/audit-file-system
   Consultato: 2026-05-23.

---

## Collegamenti Incrociati

| File | Relazione con questo modulo |
|---|---|
| [01-active-directory.md](01-active-directory.md) | Prerequisito: gruppi AD, SID, struttura OU per il modello AGDLP |
| [05-sicurezza-windows.md](05-sicurezza-windows.md) | Approfondimento: Tiered Administration, Privileged Access Workstation |
| [07-storage-windows.md](07-storage-windows.md) | Contesto: NTFS come filesystem di base, share SMB, quota disco |
| [16-profili-e-servizi.md](16-profili-e-servizi.md) | Contesto: permessi su profili utente e servizi Windows |
| [21-group-policy-guida-completa.md](21-group-policy-guida-completa.md) | Configurazione GPO per audit, LAPS deployment, Folder Redirection |

---

## Glossario Locale

| Termine | Definizione |
|---|---|
| **ACE** | Access Control Entry. Singola voce in una ACL che specifica permessi concessi o negati a un SID. |
| **ACL** | Access Control List. Lista ordinata di ACE che definisce chi può accedere a un oggetto e come. |
| **AGDLP** | Account → Global Group → Domain Local Group → Permissions. Best practice per l'assegnazione permessi in AD. |
| **DAC** | Dynamic Access Control. Controllo accessi basato su claims dell'utente e proprietà delle risorse. |
| **DACL** | Discretionary Access Control List. Lista ACE che controlla l'accesso a un oggetto. |
| **FCI** | File Classification Infrastructure. Componente FSRM per la classificazione automatica dei file basata su contenuto, posizione o regex. |
| **JEA** | Just Enough Administration. Tecnologia PowerShell per delega granulare di comandi specifici senza concedere admin completo. |
| **LAPS** | Local Administrator Password Solution. Gestione centralizzata delle password admin locali. |
| **MIC** | Mandatory Integrity Control. Livelli di integrità (Low/Medium/High/System) che limitano la scrittura verso l'alto. |
| **PAM** | Privileged Access Management. Gestione degli accessi privilegiati con membership temporanea e foresta bastion. |
| **SACL** | System Access Control List. Lista ACE per l'audit degli accessi a un oggetto. |
| **SDDL** | Security Descriptor Definition Language. Formato testuale per rappresentare i Security Descriptor. |
| **SID** | Security Identifier. Identificatore univoco per utenti, gruppi e computer in AD (es. S-1-5-21-...). |
