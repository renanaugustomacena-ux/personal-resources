# Sicurezza Windows — Guida Completa

> **Modulo 05** · **Aggiornamento:** 2026-05-22

> **Modulo del corso:** Amministrazione Windows enterprise
> **Prerequisiti:** [01-active-directory.md](01-active-directory.md), [08-permessi-e-accesso.md](08-permessi-e-accesso.md), [06-rete-windows.md](06-rete-windows.md)
> **Obiettivi di apprendimento:**
> 1. Comprendere l'architettura di sicurezza Windows: SRM, LSA, SAM, token e ACL
> 2. Configurare e gestire BitLocker con TPM e recovery key
> 3. Implementare Credential Guard, LSA Protection e Windows Hello
> 4. Applicare Microsoft Defender ASR rules ed Exploit Protection
> 5. Progettare una checklist di hardening per ruoli server specifici
> **Tempo stimato:** lettura 40 min · lab 60 min
> **Livello:** proficient
> **Ultimo aggiornamento:** 2026-05-23

## Idee guida
1. **BitLocker recovery: TPM failure scenario procedure.**
2. **Credential Guard: requires nested virt; Secured-core PC.**
3. **Defender ASR rules + Exploit Protection.**
4. **LSA Protection + Credential Manager.**


## Indice

- [Panoramica](#panoramica)
- [Architettura di Sicurezza Windows](#architettura-di-sicurezza-windows)
  - [Security Reference Monitor (SRM)](#security-reference-monitor-srm)
  - [Local Security Authority (LSA)](#local-security-authority-lsa)
  - [Security Account Manager (SAM)](#security-account-manager-sam)
  - [Token di accesso e SID](#token-di-accesso-e-sid)
  - [Access Control List (ACL)](#access-control-list-acl)
  - [Livelli di integrità (Mandatory Integrity Control)](#livelli-di-integrità-mandatory-integrity-control)
- [Autenticazione Windows](#autenticazione-windows)
  - [Kerberos](#kerberos)
  - [NTLM — perché evitarlo](#ntlm--perché-evitarlo)
  - [Windows Hello e FIDO2](#windows-hello-e-fido2)
- [Autorizzazione e controllo accessi](#autorizzazione-e-controllo-accessi)
  - [DACL e SACL](#dacl-e-sacl)
  - [Algoritmo di Access Check](#algoritmo-di-access-check)
  - [Permessi effettivi](#permessi-effettivi)
  - [Accesso basato su token](#accesso-basato-su-token)
- [User Account Control (UAC)](#user-account-control-uac)
- [Windows Defender](#windows-defender)
  - [Protezione in tempo reale e cloud](#protezione-in-tempo-reale-e-cloud)
  - [Attack Surface Reduction (ASR) — Regole complete](#attack-surface-reduction-asr--regole-complete)
  - [Accesso controllato alle cartelle](#accesso-controllato-alle-cartelle)
  - [Protezione di rete (Network Protection)](#protezione-di-rete-network-protection)
  - [Exploit Protection](#exploit-protection)
- [BitLocker](#bitlocker)
  - [BitLocker To Go](#bitlocker-to-go)
  - [Network Unlock](#network-unlock)
  - [Gestione con MBAM](#gestione-con-mbam)
- [Credential Guard](#credential-guard)
- [Windows Firewall Avanzato](#windows-firewall-avanzato)
  - [Profili e regole](#profili-e-regole)
  - [Connection Security Rules (IPsec)](#connection-security-rules-ipsec)
  - [Deploy centralizzato via GPO](#deploy-centralizzato-via-gpo)
- [Audit Policy e Logging](#audit-policy-e-logging)
  - [Sysmon](#sysmon)
  - [Windows Event Forwarding (WEF)](#windows-event-forwarding-wef)
  - [Event ID critici da monitorare](#event-id-critici-da-monitorare)
- [AppLocker e WDAC](#applocker-e-wdac)
- [LAPS — Local Admin Password Solution](#laps--local-admin-password-solution)
- [Protezione credenziali avanzata](#protezione-credenziali-avanzata)
  - [Protected Users](#protected-users)
  - [Authentication Policies e Silos](#authentication-policies-e-silos)
- [Windows Security Baseline](#windows-security-baseline)
  - [CIS Benchmarks](#cis-benchmarks)
  - [DISA STIG](#disa-stig)
- [Local Security Policy e Security Compliance Toolkit](#local-security-policy-e-security-compliance-toolkit)
- [Riduzione della superficie di attacco](#riduzione-della-superficie-di-attacco)
  - [Hardening servizi](#hardening-servizi)
  - [SMB Signing](#smb-signing)
  - [LDAP Signing e Channel Binding](#ldap-signing-e-channel-binding)
  - [Disabilitazione protocolli legacy](#disabilitazione-protocolli-legacy)
- [Windows Sandbox e Application Guard](#windows-sandbox-e-application-guard)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Checklist di Hardening](#checklist-di-hardening)

---

## Panoramica

La sicurezza Windows si basa su un approccio defense-in-depth: crittografia disco (BitLocker), protezione credenziali (Credential Guard, LAPS), controllo applicazioni (AppLocker/WDAC), antimalware (Defender), firewall, auditing e baseline di sicurezza. Ogni layer riduce la superficie di attacco.

Il modello di sicurezza Windows è costruito su componenti kernel-mode e user-mode che collaborano per garantire:

- **Identificazione**: ogni principal (utente, servizio, computer) riceve un Security Identifier (SID) univoco.
- **Autenticazione**: verifica dell'identità tramite Kerberos (dominio) o NTLM (fallback legacy).
- **Autorizzazione**: il Security Reference Monitor confronta il token dell'utente con la DACL dell'oggetto.
- **Auditing**: registrazione granulare di successi e fallimenti su ogni categoria di accesso.
- **Protezione dati**: crittografia a riposo (BitLocker, EFS) e in transito (TLS, IPsec).

Ogni richiesta di accesso a un oggetto (file, chiave di registro, named pipe, processo) transita per lo stesso algoritmo di access check nel kernel, rendendo il modello uniforme e prevedibile.

---

## Architettura di Sicurezza Windows

### Security Reference Monitor (SRM)

Il Security Reference Monitor è un componente **kernel-mode** (`ntoskrnl.exe`) responsabile di tutte le decisioni di accesso. Quando un thread tenta di aprire un handle a un oggetto protetto, il gestore oggetti (Object Manager) invoca SRM passandogli:

1. Il **token di accesso** del thread (o del processo se il thread non ne ha uno proprio).
2. Il **security descriptor** dell'oggetto, contenente owner SID, DACL e SACL.
3. La **maschera di accesso richiesta** (READ_CONTROL, WRITE_DAC, FILE_READ_DATA, ecc.).

SRM esegue l'algoritmo di access check e restituisce ACCESS_GRANTED o ACCESS_DENIED. Inoltre genera gli eventi di audit (success/failure) se la SACL dell'oggetto lo richiede.

```
Richiesta di accesso
       │
       ▼
┌──────────────┐     ┌──────────────────┐     ┌──────────────┐
│  Thread con  │────▶│  Object Manager  │────▶│     SRM      │
│    Token     │     │  (kernel-mode)   │     │ Access Check │
└──────────────┘     └──────────────────┘     └──────┬───────┘
                                                      │
                                              ┌───────┴───────┐
                                              │               │
                                        ACCESS_GRANTED  ACCESS_DENIED
                                              │               │
                                         Handle creato   STATUS_ACCESS
                                                          _DENIED
```

Caratteristiche chiave:
- Opera interamente in kernel-mode — non bypassabile da codice user-mode.
- Il codice SRM non è patchabile a runtime su sistemi con Secure Boot e HVCI attivi.
- Genera Event ID 4656 (handle richiesto), 4663 (accesso oggetto), 560/567 (legacy) quando il SACL è configurato.

```powershell
# Verificare se HVCI (Hypervisor-enforced Code Integrity) è attivo
# Protegge l'integrità del kernel, incluso SRM
Get-CimInstance -ClassName Win32_DeviceGuard `
    -Namespace root\Microsoft\Windows\DeviceGuard |
    Select-Object VirtualizationBasedSecurityStatus,
        SecurityServicesRunning,
        SecurityServicesConfigured
# SecurityServicesRunning contiene 2 se HVCI è attivo
```

### Local Security Authority (LSA)

LSA (`lsass.exe`) è il processo user-mode responsabile di:

- Autenticazione degli utenti (delegando a Kerberos SSP, NTLM SSP, Negotiate, ecc.).
- Creazione dei token di accesso dopo un logon riuscito.
- Gestione delle policy di sicurezza locali (password policy, audit policy, user rights).
- Gestione dei segreti LSA (password di servizio, chiavi di crittografia, segreti privati).

```
                    ┌─────────────────────┐
                    │   Winlogon / LogonUI │
                    └──────────┬──────────┘
                               │ credenziali
                               ▼
                    ┌──────────────────────┐
                    │    LSA (lsass.exe)   │
                    │  ┌────────────────┐  │
                    │  │ Kerberos SSP   │  │  ←── Dominio AD
                    │  │ NTLM SSP      │  │  ←── Legacy/fallback
                    │  │ Negotiate      │  │  ←── Sceglie automaticamente
                    │  │ Schannel       │  │  ←── TLS
                    │  │ CredSSP        │  │  ←── RDP/WinRM
                    │  └────────────────┘  │
                    │                      │
                    │  Policy Database     │
                    │  Secrets Store       │
                    │  Token Factory       │
                    └──────────┬───────────┘
                               │ token
                               ▼
                    ┌──────────────────────┐
                    │  Sessione utente     │
                    │  (explorer.exe, ecc) │
                    └──────────────────────┘
```

#### Protezione LSA

A partire da Windows 8.1/Server 2012 R2, è possibile attivare LSA Protection (PPL — Protected Process Light) per impedire a processi non firmati Microsoft di iniettare codice o leggere la memoria di lsass.exe:

```powershell
# Abilitare LSA Protection (PPL)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "RunAsPPL" -Value 1 -Type DWord

# Verificare che LSA Protection sia attiva dopo il riavvio
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "RunAsPPL"

# Abilitare via GPO:
# Computer → Administrative Templates → System → Local Security Authority
# → Configure LSASS to run as a protected process: Enabled with UEFI Lock

# Verificare con Event Log (dopo riavvio)
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-Wininit/Operational'; Id=12} |
    Select-Object TimeCreated, Message
# Event ID 12 = "LSASS.exe was started as a protected process"
```

**LSA Protection blocca**:
- Dumping credenziali con mimikatz (fallisce con `ERROR kuhl_m_sekurlsa_acquireLSA`)
- Injection di DLL non firmate in lsass
- Apertura di handle a lsass con PROCESS_VM_READ

### Security Account Manager (SAM)

Il SAM è il database locale delle credenziali su sistemi standalone o member server. Memorizza gli hash delle password degli account locali ed è archiviato nel file `%SystemRoot%\System32\config\SAM`.

Caratteristiche:
- Protetto da ACL restrittive (solo SYSTEM può accedere direttamente).
- Crittografato con la SYSKEY (boot key) derivata dal file SYSTEM.
- Su domain controller, le credenziali sono nel database Active Directory (`ntds.dit`), non nel SAM.
- A partire da Windows 10 1607, la crittografia SAM usa AES-128 in modalità CBC.

```powershell
# Il file SAM è bloccato dal sistema in esecuzione
# Percorso: C:\Windows\System32\config\SAM
# Un backup (shadow copy) è in C:\Windows\System32\config\RegBack\SAM

# Verificare gli account locali (senza leggere hash)
Get-LocalUser | Select-Object Name, Enabled, LastLogon, PasswordLastSet, SID

# Verificare la policy password locale
net accounts
# Mostra: min/max password age, min length, lockout threshold/duration

# Configurare policy password locale
net accounts /minpwlen:14 /maxpwage:90 /minpwage:1 /uniquepw:24 /lockoutthreshold:10

# Su domain controller, le policy sono in AD:
# gpmc.msc → Default Domain Policy → Computer → Windows Settings →
#   Security Settings → Account Policies → Password Policy
```

**Attacchi noti al SAM**:
- **SAM dump offline**: avvio da USB/WinPE, copia di SAM + SYSTEM, estrazione hash.
- **Shadow copy abuse**: `vssadmin create shadow /for=C:` → accesso a SAM dalla shadow.
- **Mitigazione**: BitLocker (impedisce accesso offline), LSA Protection, Credential Guard.

### Token di accesso e SID

Ogni processo e thread in Windows possiede un **token di accesso** creato da LSA al momento del logon. Il token contiene:

| Campo | Descrizione |
|-------|-------------|
| User SID | SID dell'utente (es. S-1-5-21-xxx-1001) |
| Group SIDs | SID di tutti i gruppi di appartenenza |
| Privileges | Elenco dei privilegi (SeBackupPrivilege, SeDebugPrivilege, ecc.) |
| Integrity Level | Livello di integrità: Low, Medium, High, System |
| Logon SID | SID univoco della sessione di logon |
| Token Type | Primary (processo) o Impersonation (thread) |
| Restricted SIDs | SID con accesso limitato (token filtrato) |
| Default DACL | DACL applicata agli oggetti creati dal processo |

#### SID — Struttura

Un SID ha il formato: `S-R-IA-SA-SA-...-RID`

```
S-1-5-21-3623811015-3361044348-30300820-1013
│ │ │  └──────────────────────────────────────── SubAuthority values
│ │ └─── Identifier Authority (5 = NT Authority)
│ └───── Revision (sempre 1)
└─────── Prefix "S" (Security Identifier)
```

SID noti (well-known):

| SID | Significato |
|-----|-------------|
| S-1-0-0 | Nobody (Null SID) |
| S-1-1-0 | Everyone |
| S-1-5-7 | Anonymous Logon |
| S-1-5-11 | Authenticated Users |
| S-1-5-18 | SYSTEM (Local System) |
| S-1-5-19 | LOCAL SERVICE |
| S-1-5-20 | NETWORK SERVICE |
| S-1-5-32-544 | BUILTIN\Administrators |
| S-1-5-32-545 | BUILTIN\Users |
| S-1-5-21-*-500 | Administrator (domain/local RID 500) |
| S-1-5-21-*-501 | Guest |
| S-1-5-21-*-512 | Domain Admins |
| S-1-5-21-*-513 | Domain Users |
| S-1-5-21-*-519 | Enterprise Admins |
| S-1-16-0 | Untrusted Integrity Level |
| S-1-16-4096 | Low Integrity Level |
| S-1-16-8192 | Medium Integrity Level |
| S-1-16-12288 | High Integrity Level |
| S-1-16-16384 | System Integrity Level |

```powershell
# Visualizzare il token del processo corrente
whoami /all
# Mostra: SID utente, gruppi, privilegi, livello di integrità

# SID di un utente specifico
(New-Object System.Security.Principal.NTAccount("CORP\mario.rossi")).Translate(
    [System.Security.Principal.SecurityIdentifier]).Value

# Utente da SID
(New-Object System.Security.Principal.SecurityIdentifier("S-1-5-21-xxx-1001")).Translate(
    [System.Security.Principal.NTAccount]).Value

# Token del processo corrente (dettagliato)
[System.Security.Principal.WindowsIdentity]::GetCurrent() |
    Select-Object Name, User, AuthenticationType, ImpersonationLevel, IsSystem

# Gruppi nel token corrente
[System.Security.Principal.WindowsIdentity]::GetCurrent().Groups |
    ForEach-Object {
        $sid = $_
        try {
            $name = $sid.Translate([System.Security.Principal.NTAccount]).Value
        } catch { $name = "(non risolvibile)" }
        [PSCustomObject]@{ SID = $sid.Value; Name = $name }
    }

# Privilegi del token corrente
whoami /priv
# Esempio output:
# SeShutdownPrivilege          Disabled
# SeChangeNotifyPrivilege      Enabled
# SeIncreaseWorkingSetPrivilege Disabled
```

### Access Control List (ACL)

Ogni oggetto protetto (file, cartella, chiave di registro, servizio, named pipe, oggetto AD) possiede un **Security Descriptor** con:

```
Security Descriptor
├── Owner SID          ─ chi possiede l'oggetto
├── Group SID          ─ gruppo primario (rilevante per POSIX compatibility)
├── DACL               ─ Discretionary ACL (chi può accedere)
│   ├── ACE 1: Allow   CORP\IT-Admins   FullControl
│   ├── ACE 2: Deny    CORP\Contractors  Write
│   └── ACE 3: Allow   BUILTIN\Users    Read
└── SACL               ─ System ACL (auditing)
    └── ACE 1: Audit   Everyone          Write (Success+Failure)
```

Ogni ACE (Access Control Entry) nella DACL specifica:

| Campo | Descrizione |
|-------|-------------|
| Type | Allow o Deny |
| SID | Principal a cui si applica |
| Access Mask | Bit mask dei permessi concessi/negati |
| Flags | Ereditarietà (CI, OI, NP, IO) |

```powershell
# Visualizzare ACL di un file/cartella
Get-Acl -Path "C:\Dati\Finanza" | Format-List

# ACL dettagliata con tutte le ACE
(Get-Acl -Path "C:\Dati\Finanza").Access |
    Select-Object IdentityReference, FileSystemRights, AccessControlType,
        IsInherited, InheritanceFlags, PropagationFlags

# SDDL (Security Descriptor Definition Language) — forma compatta
(Get-Acl -Path "C:\Dati\Finanza").Sddl
# Esempio: O:BAG:BAD:P(A;OICI;FA;;;BA)(A;OICI;0x1200a9;;;BU)
# O:BA = Owner:BUILTIN\Administrators
# D:P  = DACL Protected (no ereditarietà dal parent)
# (A;OICI;FA;;;BA) = Allow, ObjInherit+ContInherit, FullAccess, BUILTIN\Admins

# Impostare ACL
$acl = Get-Acl -Path "C:\Dati\Finanza"
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "CORP\GG-Finanza", "Modify", "ContainerInherit, ObjectInherit", "None", "Allow"
)
$acl.AddAccessRule($rule)
Set-Acl -Path "C:\Dati\Finanza" -AclObject $acl

# Rimuovere ereditarietà e copiare ACE esistenti
$acl = Get-Acl -Path "C:\Dati\Confidenziale"
$acl.SetAccessRuleProtection($true, $true)  # Protected=true, PreserveInheritance=true
Set-Acl -Path "C:\Dati\Confidenziale" -AclObject $acl

# ACL su chiave di registro
Get-Acl -Path "HKLM:\SOFTWARE\MiaApp" | Format-List

# ACL su un servizio
sc.exe sdshow wuauserv
# Restituisce SDDL del servizio Windows Update
```

#### Flag di ereditarietà

| Flag | Sigla | Significato |
|------|-------|-------------|
| ContainerInherit | CI | L'ACE si eredita nelle sottocartelle |
| ObjectInherit | OI | L'ACE si eredita nei file |
| NoPropagateInherit | NP | Ereditarietà si ferma al primo livello |
| InheritOnly | IO | L'ACE si applica solo agli oggetti figli, non al container stesso |

### Livelli di integrità (Mandatory Integrity Control)

Windows implementa il Mandatory Integrity Control (MIC) come layer aggiuntivo sopra la DACL. Ogni processo e oggetto ha un **livello di integrità** (IL):

| Livello | Valore | Esempio |
|---------|--------|---------|
| Untrusted | 0 | Processi sandboxed estremi |
| Low | 4096 | Internet Explorer Protected Mode, Edge sandbox |
| Medium | 8192 | Utenti standard, processi normali |
| High | 12288 | Processi elevati (Run as Administrator) |
| System | 16384 | Servizi di sistema, SYSTEM |

Regola fondamentale: **No Write Up, No Read Up** (opzionale).

Un processo con IL Medium **non può scrivere** su un oggetto con IL High, anche se la DACL lo permetterebbe. L'access check del SRM verifica prima il livello di integrità, poi la DACL.

```powershell
# Verificare il livello di integrità del processo corrente
whoami /groups | findstr "Label"
# Output esempio: Mandatory Label\Medium Mandatory Level

# Creare un processo a bassa integrità
# icacls imposta il livello sull'eseguibile, non sul processo
icacls "C:\Test\app.exe" /setintegritylevel low

# Verificare il livello di integrità di un file
icacls "C:\Test\app.exe" | findstr /i "integrity"

# Avviare un processo a bassa integrità con runas
# (richiede tool di terze parti come psexec o CreateProcess con TokenIntegrityLevel)

# Visualizzare IL di tutti i processi in esecuzione
Get-Process | ForEach-Object {
    $p = $_
    try {
        $handle = $p.Handle
        # Il livello di integrità è nel token — visibile con strumenti come Process Explorer
    } catch {}
}
# Per analisi dettagliata: usare Process Explorer (Sysinternals) → colonna "Integrity Level"
```

---

## Autenticazione Windows

### Kerberos

Kerberos v5 (RFC 4120) è il protocollo di autenticazione predefinito in ambienti Active Directory. Utilizza un modello a tre parti: client, server e Key Distribution Center (KDC, ospitato sul domain controller).

#### Flusso di autenticazione Kerberos

```
Client                          KDC (Domain Controller)              Server
  │                                    │                                │
  │  1. AS-REQ (username, timestamp)   │                                │
  │  ──────────────────────────────▶  │                                │
  │                                    │  (verifica password hash       │
  │                                    │   dal database AD)             │
  │  2. AS-REP (TGT + session key)    │                                │
  │  ◀──────────────────────────────  │                                │
  │                                    │                                │
  │  3. TGS-REQ (TGT + SPN target)    │                                │
  │  ──────────────────────────────▶  │                                │
  │                                    │  (verifica TGT, crea          │
  │                                    │   Service Ticket)             │
  │  4. TGS-REP (Service Ticket)      │                                │
  │  ◀──────────────────────────────  │                                │
  │                                    │                                │
  │  5. AP-REQ (Service Ticket)        │                                │
  │  ──────────────────────────────────────────────────────────────▶  │
  │                                    │                                │
  │  6. AP-REP (mutual auth, opzionale)│                                │
  │  ◀──────────────────────────────────────────────────────────────  │
```

Passaggi dettagliati:

1. **AS-REQ (Authentication Service Request)**: il client invia username e un timestamp crittografato con l'hash della password dell'utente (pre-authentication).
2. **AS-REP (Authentication Service Reply)**: il KDC verifica l'hash, e se valido restituisce un TGT (Ticket Granting Ticket) crittografato con la chiave del servizio krbtgt, più una session key.
3. **TGS-REQ (Ticket Granting Service Request)**: il client presenta il TGT e il Service Principal Name (SPN) del servizio target.
4. **TGS-REP**: il KDC verifica il TGT e restituisce un Service Ticket crittografato con la chiave del servizio target.
5. **AP-REQ (Application Request)**: il client presenta il Service Ticket al server target.
6. **AP-REP**: il server verifica il ticket e (opzionalmente) autentica se stesso al client.

```powershell
# Visualizzare i ticket Kerberos nella cache
klist

# Visualizzare il TGT
klist tgt

# Purge di tutti i ticket (utile per troubleshooting)
klist purge

# Visualizzare SPN registrati per un servizio
setspn -L nomeserver

# Registrare un SPN per un servizio
setspn -S HTTP/webapp.corp.contoso.com CORP\svc-webapp

# Verificare duplicati SPN (causa errore Kerberos)
setspn -X

# Verificare che Kerberos sia in uso per una connessione
klist | findstr /i "server"
# Se vedi ticket per il server target → Kerberos è in uso

# Diagnostica Kerberos
nltest /dsgetdc:corp.contoso.com /kdc
# Mostra quale DC sta fungendo da KDC
```

#### Tipi di crittografia Kerberos

| etype | Algoritmo | Sicurezza | Note |
|-------|-----------|-----------|------|
| 23 | RC4-HMAC | Debole | Basato su NTLM hash, vulnerabile a Kerberoasting |
| 17 | AES128-CTS-HMAC-SHA1 | Buona | Accettabile |
| 18 | AES256-CTS-HMAC-SHA1 | Ottima | Raccomandata |

```powershell
# Forzare AES per Kerberos (disabilitare RC4)
# GPO: Computer → Windows Settings → Security Settings → Local Policies →
#   Security Options → Network security: Configure encryption types
#   allowed for Kerberos
# Abilitare solo AES128 e AES256

# Su un account di servizio AD, abilitare AES:
Set-ADUser -Identity svc-webapp -KerberosEncryptionType AES128, AES256

# Verificare etype in uso
klist | findstr "Etype"
```

#### Attacchi Kerberos comuni

| Attacco | Descrizione | Mitigazione |
|---------|-------------|-------------|
| Kerberoasting | Richiesta TGS per account di servizio con SPN, crack offline dell'hash RC4 | Usare AES, password lunghe (>25 char), gMSA |
| AS-REP Roasting | Sfrutta account senza pre-auth, crack AS-REP offline | Abilitare pre-auth su tutti gli account |
| Golden Ticket | Forging TGT con hash krbtgt | Rotazione password krbtgt 2x, monitorare Event 4769 |
| Silver Ticket | Forging Service Ticket con hash servizio | gMSA, PAC validation, monitorare Event 4769 |
| Pass-the-Ticket | Riutilizzo ticket rubato dalla memoria | Credential Guard, LSA Protection |

### NTLM — perché evitarlo

NTLM (NT LAN Manager) è il protocollo di autenticazione legacy. Ancora presente per compatibilità ma da evitare.

**Problemi di NTLM**:

1. **Challenge/Response senza mutual authentication**: il server non si autentica al client → vulnerabile a relay.
2. **Hash NTLM come equivalente della password**: chi possiede l'hash può autenticarsi (Pass-the-Hash).
3. **Nessun supporto per delega vincolata**: NTLM non supporta constrained delegation nativa.
4. **Crittografia debole**: NTLMv1 usa DES; NTLMv2 usa HMAC-MD5 — entrambi inferiori a AES Kerberos.
5. **NTLM Relay**: l'attaccante intercetta e rilancia l'autenticazione verso un altro server.

```powershell
# Audit dell'uso di NTLM (prima di disabilitarlo)
# GPO: Computer → Windows Settings → Security Settings → Local Policies →
#   Security Options → Network security: Restrict NTLM

# 1. Abilitare auditing NTLM in ingresso
# "Audit incoming NTLM traffic" → "Enable auditing for all accounts"

# 2. Abilitare auditing NTLM in uscita
# "Audit NTLM authentication in this domain" → "Enable all"

# 3. Monitorare gli eventi
Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-NTLM/Operational'
} -MaxEvents 50 | Select-Object TimeCreated, Id, Message

# Forzare NTLMv2 (minimo)
# GPO: Network security: LAN Manager authentication level
# → "Send NTLMv2 response only. Refuse LM & NTLM"

# Bloccare NTLM completamente (dopo audit)
# "Restrict NTLM: Incoming NTLM traffic" → "Deny all accounts"
# "Restrict NTLM: Outgoing NTLM traffic" → "Deny all"
# ATTENZIONE: molte applicazioni legacy dipendono da NTLM. Testare prima.

# Eccezioni per server che richiedono NTLM
# "Restrict NTLM: Add server exceptions" → "server1.corp.contoso.com"
```

### Windows Hello e FIDO2

Windows Hello sostituisce le password con autenticazione forte basata su:
- **PIN locale**: legato al dispositivo, protetto da TPM.
- **Biometria**: impronta digitale, riconoscimento facciale (IR camera).
- **Chiave di sicurezza FIDO2**: autenticazione passwordless con standard WebAuthn.

```powershell
# Verificare stato Windows Hello
dsregcmd /status
# Sezione "User State" mostra: NgcSet, NgcKeyId, WorkplaceJoined, ecc.

# Configurare Windows Hello for Business via GPO
# Computer → Administrative Templates → Windows Components → Windows Hello for Business
# → Use Windows Hello for Business: Enabled
# → Use a hardware security device: Enabled (richiede TPM)
# → Use biometrics: Enabled

# Registrare chiave FIDO2 per un utente
# Settings → Accounts → Sign-in options → Security Key → Manage

# Verificare provider di credenziali registrati
Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Authentication\Credential Providers\*" |
    Select-Object PSChildName, "(default)"

# Policy per richiedere MFA al logon
# Computer → Administrative Templates → System → Logon
# → Assign a default credential provider
```

**FIDO2 in ambiente enterprise**:
- Supportato da Azure AD / Entra ID.
- Le chiavi FIDO2 supportano attestation (verifica del modello hardware).
- Compatibile con Conditional Access policy.
- Elimina completamente hash e ticket dalla rete.

---

## Autorizzazione e controllo accessi

### DACL e SACL

La **DACL** (Discretionary Access Control List) definisce chi può accedere all'oggetto e con quali permessi. La **SACL** (System Access Control List) definisce quali accessi vengono registrati nel log di sicurezza.

**Regole della DACL**:
- Se non esiste DACL (null DACL) → tutti hanno accesso completo.
- Se la DACL è vuota (0 ACE) → nessuno ha accesso.
- Le ACE Deny vengono valutate prima delle ACE Allow.
- Le ACE esplicite hanno priorità su quelle ereditate.

**Ordine canonico delle ACE**:
1. Deny espliciti
2. Allow espliciti
3. Deny ereditati (dal parent più vicino)
4. Allow ereditati (dal parent più vicino)
5. Deny ereditati (dal parent più lontano)
6. Allow ereditati (dal parent più lontano)

```powershell
# Configurare SACL (auditing) su una cartella
$acl = Get-Acl -Path "C:\Dati\Sensibili"
$auditRule = New-Object System.Security.AccessControl.FileSystemAuditRule(
    "Everyone",
    "Delete, Write",
    "ContainerInherit, ObjectInherit",
    "None",
    "Failure"
)
$acl.AddAuditRule($auditRule)
Set-Acl -Path "C:\Dati\Sensibili" -AclObject $acl

# Verificare SACL
(Get-Acl -Path "C:\Dati\Sensibili" -Audit).Audit |
    Select-Object IdentityReference, FileSystemRights, AuditFlags

# Impostare SACL via GPO (per policy centrale):
# Computer → Windows Settings → Security Settings → Advanced Audit Policy
# → Object Access → Audit File System: Success, Failure
```

### Algoritmo di Access Check

L'algoritmo eseguito da SRM per ogni richiesta di accesso:

```
1. Se l'utente è il proprietario dell'oggetto E richiede READ_CONTROL o WRITE_DAC
   → ACCESS_GRANTED (il proprietario può sempre leggere/modificare permessi)

2. Verifica Mandatory Integrity Control:
   - Se IL del processo < IL dell'oggetto E l'accesso è in scrittura
     → ACCESS_DENIED

3. Se la DACL è NULL
   → ACCESS_GRANTED (tutti hanno accesso)

4. Se la DACL è vuota (0 ACE)
   → ACCESS_DENIED (nessuno ha accesso)

5. Scorrere le ACE in ordine:
   a. Per ogni ACE Deny:
      - Se il SID nell'ACE corrisponde a un SID nel token
        E la maschera di accesso dell'ACE si sovrappone alla maschera richiesta
        → Rimuovere quei bit dalla maschera richiesta
        → Se rimanente = 0 → ACCESS_DENIED
   b. Per ogni ACE Allow:
      - Se il SID nell'ACE corrisponde a un SID nel token
        E la maschera di accesso dell'ACE si sovrappone alla maschera richiesta
        → Accumulare i bit concessi
   c. Se tutti i bit richiesti sono stati concessi
      → ACCESS_GRANTED
   d. Se si raggiunge la fine della DACL senza concedere tutti i bit
      → ACCESS_DENIED
```

### Permessi effettivi

I permessi effettivi di un utente su un oggetto dipendono dall'interazione tra:
- DACL dell'oggetto (ACE espliciti + ereditati)
- Gruppi nel token dell'utente
- Livello di integrità
- Privilegi del token (SeBackupPrivilege bypassa DACL per lettura, ecc.)
- Token type (filtered token di UAC riduce i gruppi)

```powershell
# Calcolare permessi effettivi (GUI)
# Proprietà file/cartella → Sicurezza → Avanzate → Accesso effettivo
# Selezionare utente → "Visualizza accesso effettivo"

# Calcolare permessi effettivi (PowerShell)
# Richiede modulo NTFSSecurity o analisi manuale del token vs DACL

# Con icacls (visualizzazione diretta)
icacls "C:\Dati\Finanza"
# Output:
# CORP\GG-Finanza:(OI)(CI)(M)    ← Modify, inherited to objects and containers
# BUILTIN\Administrators:(OI)(CI)(F)  ← Full Control
# BUILTIN\Users:(OI)(CI)(RX)          ← Read & Execute

# Significato flag icacls:
# (OI) = Object Inherit
# (CI) = Container Inherit
# (F)  = Full Control
# (M)  = Modify
# (RX) = Read & Execute
# (R)  = Read
# (W)  = Write
# (D)  = Delete
```

### Accesso basato su token

Ogni accesso a un oggetto è mediato dal token del thread/processo chiamante. Il concetto fondamentale è che **il token è l'unica rappresentazione dell'identità** all'interno del kernel.

```powershell
# Token filtrato UAC — un admin ha due token:
# 1. Token elevato (High IL, tutti i gruppi e privilegi)
# 2. Token filtrato (Medium IL, Administrators SID deny-only, privilegi rimossi)

# Verificare se il processo corrente è elevato
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object System.Security.Principal.WindowsPrincipal($identity)
$principal.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)
# True = processo elevato, False = token filtrato

# Impersonation: un thread può usare il token di un altro utente
# Livelli di impersonation:
# Anonymous        — nessuna informazione sull'identità
# Identification   — il server può identificare il client ma non agire per suo conto
# Impersonation    — il server può agire per conto del client localmente
# Delegation       — il server può agire per conto del client anche verso altri server

# Visualizzare token di un processo (richiede SeDebugPrivilege)
# Usare Process Explorer → Properties → Security → Groups/Privileges
```

---

## User Account Control (UAC)

UAC è il meccanismo che separa le attività amministrative da quelle standard, anche per utenti membri del gruppo Administrators.

### Come funziona UAC

1. Al logon, LSA crea due token per gli admin: elevato e filtrato.
2. I processi normali ricevono il token filtrato (Medium IL).
3. Quando un'operazione richiede privilegi admin, UAC mostra il prompt di elevazione.
4. Se l'utente conferma, il nuovo processo riceve il token elevato (High IL).

### Livelli di UAC

| Livello | Comportamento |
|---------|---------------|
| Always Notify | Prompt per ogni modifica al sistema e apertura app (massima sicurezza) |
| Notify on app changes (default) | Prompt solo per app, non per impostazioni Windows |
| Notify (no dimming) | Come sopra ma senza Secure Desktop |
| Never Notify | UAC disattivato (altamente sconsigliato) |

### Secure Desktop

Il prompt UAC viene visualizzato su un desktop separato (Secure Desktop) che non è accessibile ai processi user-mode. Questo impedisce a malware di:
- Simulare il prompt UAC con una finestra falsa.
- Cliccare automaticamente "Sì" sul prompt.
- Catturare screenshot del prompt.

```powershell
# Configurazione UAC via Registry
# Percorso: HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System

# EnableLUA = 1 → UAC abilitato (DEVE essere 1)
Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -Name "EnableLUA"

# ConsentPromptBehaviorAdmin:
# 0 = Elevate without prompting (pericoloso)
# 1 = Prompt for credentials on Secure Desktop
# 2 = Prompt for consent on Secure Desktop (consigliato)
# 3 = Prompt for credentials
# 4 = Prompt for consent
# 5 = Prompt for consent for non-Windows binaries (default)

# PromptOnSecureDesktop = 1 → Secure Desktop attivo
Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -Name "PromptOnSecureDesktop"

# EnableInstallerDetection = 1 → Rilevamento automatico installer
# FilterAdministratorToken = 1 → Filtra anche il built-in Administrator (RID 500)

# Configurazione via GPO (consigliata):
# Computer → Windows Settings → Security Settings → Local Policies → Security Options
# → User Account Control: *

# Verificare stato UAC
Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" |
    Select-Object EnableLUA, ConsentPromptBehaviorAdmin, ConsentPromptBehaviorUser,
        PromptOnSecureDesktop, EnableInstallerDetection, FilterAdministratorToken
```

### Auto-elevazione

Alcuni eseguibili Microsoft firmati hanno un manifest che dichiara `autoElevate=true`. Questi bypassano il prompt UAC per l'utente admin. Esempi: `mmc.exe`, `taskmgr.exe`, `perfmon.exe`.

```xml
<!-- Manifest di un eseguibile con auto-elevazione -->
<trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
  <security>
    <requestedPrivileges>
      <requestedExecutionLevel level="highestAvailable" uiAccess="false"/>
    </requestedPrivileges>
  </security>
</trustInfo>
```

```powershell
# Verificare se un eseguibile ha auto-elevazione
# (richiede sigcheck di Sysinternals)
sigcheck.exe -m "C:\Windows\System32\mmc.exe" | findstr "autoElevate"

# Best practice: impostare FilterAdministratorToken = 1
# per filtrare anche l'account Administrator built-in (RID 500)
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -Name "FilterAdministratorToken" -Value 1 -Type DWord
```

---

## Windows Defender

### Configurazione

```powershell
# Stato
Get-MpComputerStatus | Select-Object AntivirusEnabled, RealTimeProtectionEnabled,
    AntivirusSignatureLastUpdated, FullScanAge, QuickScanAge

# Aggiornare definizioni
Update-MpSignature

# Scansioni
Start-MpScan -ScanType QuickScan
Start-MpScan -ScanType FullScan
Start-MpScan -ScanType CustomScan -ScanPath "D:\Downloads"

# Esclusioni
Add-MpPreference -ExclusionPath "D:\Database"
Add-MpPreference -ExclusionExtension ".bak", ".log"
Add-MpPreference -ExclusionProcess "sqlservr.exe"
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath

# Configurazione avanzata
Set-MpPreference -DisableRealtimeMonitoring $false
Set-MpPreference -MAPSReporting Advanced          # Cloud Protection
Set-MpPreference -SubmitSamplesConsent SendAllSamples
Set-MpPreference -PUAProtection Enabled            # Blocca PUA
Set-MpPreference -EnableNetworkProtection Enabled  # Network Protection

# Attack Surface Reduction (ASR) rules
# Bloccare macro Office che creano processi child
Add-MpPreference -AttackSurfaceReductionRules_Ids D4F940AB-401B-4EFC-AADC-AD5F3C50688A `
    -AttackSurfaceReductionRules_Actions Enabled

# Bloccare processi non firmati da USB
Add-MpPreference -AttackSurfaceReductionRules_Ids B2B3F03D-6A65-4F7B-A9C7-1C7EF74A9BA4 `
    -AttackSurfaceReductionRules_Actions Enabled

# Visualizzare threat rilevate
Get-MpThreatDetection | Select-Object ThreatID, DomainUser, ProcessName, ActionSuccess
Get-MpThreat | Select-Object ThreatName, SeverityID, IsActive
```

### Deploy via GPO

```
Computer → Administrative Templates → Windows Components → Microsoft Defender Antivirus
├── Real-time Protection → Turn on behavior monitoring: Enabled
├── MAPS → Join Microsoft MAPS: Enabled (Advanced)
├── Scan → Schedule scan day: 0 (every day)
├── Security Intelligence Updates → Define the number of days: 1
└── Windows Defender Exploit Guard → Attack Surface Reduction
```

### Protezione in tempo reale e cloud

La protezione in tempo reale di Windows Defender opera su tre livelli:

1. **On-access scanning**: ogni file aperto, creato o modificato viene analizzato.
2. **Behavior monitoring**: analisi del comportamento dei processi in esecuzione (iniezione codice, modifica registro, connessioni sospette).
3. **Cloud-delivered protection (MAPS)**: file sconosciuti vengono inviati al cloud Microsoft per analisi rapida (< 10 secondi) con machine learning.

```powershell
# Configurazione completa protezione real-time
Set-MpPreference -DisableRealtimeMonitoring $false
Set-MpPreference -DisableBehaviorMonitoring $false
Set-MpPreference -DisableIOAVProtection $false         # Scansione download IE/Edge
Set-MpPreference -DisableOnAccessProtection $false
Set-MpPreference -DisableScriptScanning $false          # Scansione script (JS, VBS, PS1)

# Cloud Protection — livelli
Set-MpPreference -MAPSReporting Advanced
# Basic   = Invia metadati di base
# Advanced = Invia metadati + campioni per analisi cloud

# Cloud blocking timeout (tempo di attesa per verdetto cloud)
Set-MpPreference -CloudBlockLevel High
# Default    = livello standard
# High       = blocco aggressivo con possibili falsi positivi
# HighPlus   = protezione massima
# ZeroTolerance = blocca tutto ciò che non è noto come sicuro

# Timeout esteso per analisi cloud (secondi)
Set-MpPreference -CloudExtendedTimeout 50   # max 50 secondi

# Verificare stato protezione cloud
Get-MpComputerStatus | Select-Object AMServiceEnabled,
    AntispywareEnabled,
    BehaviorMonitorEnabled,
    IoavProtectionEnabled,
    NISEnabled,
    OnAccessProtectionEnabled,
    RealTimeProtectionEnabled

# Testare la connettività cloud con EICAR (file di test innocuo)
# Scaricare il file di test EICAR — se Defender lo blocca, cloud protection funziona
```

### Attack Surface Reduction (ASR) — Regole complete

Le regole ASR bloccano comportamenti comunemente usati dal malware. Ogni regola ha un GUID e può essere impostata su: Disabled (0), Block (1), Audit (2), Warn (6).

| GUID | Regola | Descrizione |
|------|--------|-------------|
| D4F940AB-401B-4EFC-AADC-AD5F3C50688A | Block Office macros from creating child processes | Blocca macro che avviano processi |
| 3B576869-A4EC-4529-8536-B80A7769E899 | Block Office apps from creating executable content | Blocca creazione EXE/DLL da Office |
| 75668C1F-73B5-4CF0-BB93-3ECF5CB7CC84 | Block Office apps from injecting code into other processes | Blocca injection da Office |
| D3E037E1-3EB8-44C8-A917-57927947596D | Block JavaScript or VBScript from launching downloaded executable content | Blocca script che avviano download |
| 5BEB7EFE-FD9A-4556-801D-275E5FFC04CC | Block execution of potentially obfuscated scripts | Blocca script offuscati |
| BE9BA2D9-53EA-4CDC-84E5-9B1EEEE46550 | Block executable content from email client and webmail | Blocca EXE da email |
| 92E97FA1-2EDF-4476-BDD6-9DD0B4DDDC7B | Block Win32 API calls from Office macros | Blocca API Win32 da macro |
| B2B3F03D-6A65-4F7B-A9C7-1C7EF74A9BA4 | Block untrusted and unsigned processes that run from USB | Blocca processi non firmati da USB |
| 26190899-1602-49E8-8B27-EB1D0A1CE869 | Block Office communication application from creating child processes | Blocca Outlook che crea processi |
| 7674BA52-37EB-4A4F-A9A1-F0F9A1619A2C | Block Adobe Reader from creating child processes | Blocca Adobe Reader child process |
| E6DB77E5-3DF2-4CF1-B95A-636979351E5B | Block persistence through WMI event subscription | Blocca persistenza via WMI |
| D1E49AAC-8F56-4280-B9BA-993A6D77406C | Block process creations originating from PSExec and WMI commands | Blocca PSExec/WMI |
| 01443614-CD74-433A-B99E-2ECDC07BFC25 | Block executable files from running unless they meet prevalence, age, or trusted list criteria | Blocca EXE sconosciuti |
| C1DB55AB-C21A-4637-BB3F-A12568109D35 | Use advanced protection against ransomware | Protezione ransomware avanzata |
| 9E6C4E1F-7D60-472F-BA1A-A39EF669E4B2 | Block credential stealing from LSASS | Blocca dumping LSASS |
| 56A863A9-875E-4185-98A7-B882C64B5CE5 | Block abuse of exploited vulnerable signed drivers | Blocca driver vulnerabili |

```powershell
# Abilitare tutte le regole ASR in Audit Mode (consigliato prima di Block)
$asrRuleIds = @(
    "D4F940AB-401B-4EFC-AADC-AD5F3C50688A",
    "3B576869-A4EC-4529-8536-B80A7769E899",
    "75668C1F-73B5-4CF0-BB93-3ECF5CB7CC84",
    "D3E037E1-3EB8-44C8-A917-57927947596D",
    "5BEB7EFE-FD9A-4556-801D-275E5FFC04CC",
    "BE9BA2D9-53EA-4CDC-84E5-9B1EEEE46550",
    "92E97FA1-2EDF-4476-BDD6-9DD0B4DDDC7B",
    "B2B3F03D-6A65-4F7B-A9C7-1C7EF74A9BA4",
    "26190899-1602-49E8-8B27-EB1D0A1CE869",
    "7674BA52-37EB-4A4F-A9A1-F0F9A1619A2C",
    "E6DB77E5-3DF2-4CF1-B95A-636979351E5B",
    "D1E49AAC-8F56-4280-B9BA-993A6D77406C",
    "C1DB55AB-C21A-4637-BB3F-A12568109D35",
    "9E6C4E1F-7D60-472F-BA1A-A39EF669E4B2",
    "56A863A9-875E-4185-98A7-B882C64B5CE5"
)
$auditActions = @("AuditMode") * $asrRuleIds.Count

Add-MpPreference -AttackSurfaceReductionRules_Ids $asrRuleIds `
    -AttackSurfaceReductionRules_Actions $auditActions

# Verificare regole attive
Get-MpPreference | Select-Object -ExpandProperty AttackSurfaceReductionRules_Ids
Get-MpPreference | Select-Object -ExpandProperty AttackSurfaceReductionRules_Actions

# Log ASR
Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-Windows Defender/Operational'
    Id = 1121, 1122  # 1121=Block, 1122=Audit
} -MaxEvents 20 | Select-Object TimeCreated, Id, Message

# Esclusioni ASR (per file/cartella)
Add-MpPreference -AttackSurfaceReductionOnlyExclusions "C:\DevTools\*"
```

### Accesso controllato alle cartelle

Controlled Folder Access protegge i file nelle cartelle monitorate da modifiche non autorizzate (anti-ransomware).

```powershell
# Abilitare Controlled Folder Access
Set-MpPreference -EnableControlledFolderAccess Enabled
# Valori: Disabled, Enabled, AuditMode, BlockDiskModificationOnly, AuditDiskModificationOnly

# Cartelle protette di default:
# Documents, Pictures, Videos, Music, Desktop, Favorites
# PLUS cartelle di sistema: Windows, Program Files, Program Files (x86)

# Aggiungere cartelle protette personalizzate
Add-MpPreference -ControlledFolderAccessProtectedFolders "D:\Progetti", "E:\Dati-Clienti"

# Consentire app specifiche (che devono poter scrivere nelle cartelle protette)
Add-MpPreference -ControlledFolderAccessAllowedApplications `
    "C:\Program Files\Notepad++\notepad++.exe",
    "C:\Program Files\7-Zip\7z.exe"

# Verificare configurazione
Get-MpPreference | Select-Object EnableControlledFolderAccess,
    ControlledFolderAccessProtectedFolders,
    ControlledFolderAccessAllowedApplications

# Log Controlled Folder Access
Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-Windows Defender/Operational'
    Id = 1123, 1124  # 1123=Blocked, 1124=Audit
} -MaxEvents 20
```

### Protezione di rete (Network Protection)

Network Protection estende Microsoft Defender SmartScreen a tutto il traffico HTTP/HTTPS in uscita, bloccando connessioni a domini malevoli, phishing e C2.

```powershell
# Abilitare Network Protection
Set-MpPreference -EnableNetworkProtection Enabled
# Valori: Disabled, Enabled, AuditMode

# Verificare
Get-MpPreference | Select-Object EnableNetworkProtection

# Log Network Protection
Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-Windows Defender/Operational'
    Id = 1125, 1126  # 1125=Block, 1126=Audit
} -MaxEvents 20

# GPO deployment:
# Computer → Administrative Templates → Windows Components →
#   Microsoft Defender Antivirus → Microsoft Defender Exploit Guard →
#   Network Protection → Prevent users and apps from accessing dangerous websites
#   → Enabled (Block)
```

### Exploit Protection

Exploit Protection sostituisce EMET (Enhanced Mitigation Experience Toolkit) e fornisce mitigazioni a livello di sistema e processo.

```powershell
# Visualizzare configurazione Exploit Protection
Get-ProcessMitigation -System
# Mostra: DEP, ASLR, CFG, SEHOP, Heap integrity, ecc.

# Configurare mitigazioni di sistema
Set-ProcessMitigation -System -Enable DEP, SEHOP, ForceRelocateImages

# Configurare mitigazioni per processo specifico
Set-ProcessMitigation -Name "chrome.exe" -Enable DEP, CFG, StrictHandle
Set-ProcessMitigation -Name "java.exe" -Enable DEP, BottomUp, SEHOP

# Esportare configurazione (per deploy via GPO)
Get-ProcessMitigation -RegistryConfigFilePath "C:\ExploitProtection-Export.xml"

# Importare configurazione
Set-ProcessMitigation -PolicyFilePath "C:\ExploitProtection-Export.xml"

# GPO:
# Computer → Administrative Templates → Windows Components →
#   Windows Defender Exploit Guard → Exploit Protection →
#   Use a common set of exploit protection settings
#   → Percorso del file XML di configurazione

# Mitigazioni principali:
# DEP    — Data Execution Prevention (blocca esecuzione dati come codice)
# ASLR   — Address Space Layout Randomization (randomizza indirizzi memoria)
# CFG    — Control Flow Guard (protegge i flussi di controllo)
# SEHOP  — Structured Exception Handler Overwrite Protection
# ACG    — Arbitrary Code Guard (blocca allocazione pagine eseguibili)
# EAF    — Export Address Table Filtering
```

---

## BitLocker

### Prerequisiti e Attivazione

```powershell
# Verificare TPM
Get-Tpm | Select-Object TpmPresent, TpmReady, TpmEnabled, TpmActivated

# Abilitare BitLocker su OS drive (con TPM)
Enable-BitLocker -MountPoint "C:" -EncryptionMethod XtsAes256 `
    -RecoveryPasswordProtector -UsedSpaceOnly

# Con TPM + PIN
$pin = ConvertTo-SecureString "123456" -AsPlainText -Force
Enable-BitLocker -MountPoint "C:" -EncryptionMethod XtsAes256 `
    -TpmAndPinProtector -Pin $pin

# Data drive (con password)
Enable-BitLocker -MountPoint "D:" -EncryptionMethod XtsAes256 `
    -PasswordProtector -Password (ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force)

# Auto-unlock data drive quando OS è sbloccato
Enable-BitLockerAutoUnlock -MountPoint "D:"

# Stato
Get-BitLockerVolume | Select-Object MountPoint, ProtectionStatus, EncryptionPercentage, VolumeStatus

# Recovery key
(Get-BitLockerVolume -MountPoint "C:").KeyProtector |
    Where-Object KeyProtectorType -eq "RecoveryPassword" |
    Select-Object -ExpandProperty RecoveryPassword

# Backup recovery key in AD
Backup-BitLockerKeyProtector -MountPoint "C:" -KeyProtectorId $keyProtectorId
```

### BitLocker via GPO (Deploy enterprise)

```
Computer → Administrative Templates → Windows Components → BitLocker Drive Encryption
├── Operating System Drives
│   ├── Require additional authentication at startup: Enabled
│   │   → Allow BitLocker without a compatible TPM: Unchecked (richiedere TPM)
│   ├── Choose how BitLocker-protected drives can be recovered: Enabled
│   │   → Save BitLocker recovery information to AD DS: Checked
│   │   → Do not enable BitLocker until recovery info stored in AD: Checked
│   └── Choose drive encryption method: XTS-AES 256
├── Fixed Data Drives
│   └── Choose drive encryption method: XTS-AES 256
└── Store BitLocker recovery information in AD DS: Enabled
```

### Gestione BitLocker

```powershell
# Sospendere (per aggiornamenti BIOS/firmware)
Suspend-BitLocker -MountPoint "C:" -RebootCount 1

# Sbloccare con recovery key
Unlock-BitLocker -MountPoint "D:" -RecoveryPassword "123456-789012-345678-901234-567890-123456-789012-345678"

# Disabilitare (decriptare)
Disable-BitLocker -MountPoint "D:"

# Cercare recovery key in AD (da DC)
Get-ADObject -Filter 'objectClass -eq "msFVE-RecoveryInformation"' `
    -SearchBase "CN=WKS-IT-001,OU=Computer,DC=corp,DC=contoso,DC=com" `
    -Properties msFVE-RecoveryPassword | Select-Object -ExpandProperty msFVE-RecoveryPassword
```

### Modalità di crittografia

| Modalità | Uso | Note |
|----------|-----|------|
| XTS-AES 128 | Drive fissi | Buon compromesso prestazioni/sicurezza |
| XTS-AES 256 | Drive fissi | Massima sicurezza, impatto prestazionale minimo su hardware moderno |
| AES-CBC 128 | Drive rimovibili | Compatibilità con Windows precedenti |
| AES-CBC 256 | Drive rimovibili | Massima sicurezza per drive rimovibili |

**XTS** (XEX-based Tweaked-codebook mode with ciphertext Stealing) è raccomandato per drive fissi perché offre protezione aggiuntiva contro attacchi di manipolazione dei dati cifrati. **CBC** è necessario per drive rimovibili che devono essere letti su sistemi Windows 7/8.

### Requisiti TPM

| Componente | Requisito |
|------------|-----------|
| TPM 1.2 | Supportato (minimo) |
| TPM 2.0 | Raccomandata — supporta SHA-256, crittografia più forte |
| UEFI | Richiesto per Secure Boot integration |
| Secure Boot | Consigliato — verifica integrità boot chain |
| PCR | TPM sigla i registri PCR 0, 2, 4, 7, 11 (UEFI) |

### BitLocker To Go

BitLocker To Go crittografa drive USB rimovibili. Utilizza AES-CBC per compatibilità.

```powershell
# Abilitare BitLocker To Go su chiavetta USB
Enable-BitLocker -MountPoint "E:" -EncryptionMethod Aes256 `
    -PasswordProtector -Password (ConvertTo-SecureString "ComplexP@ss!" -AsPlainText -Force) `
    -UsedSpaceOnly

# Aggiungere recovery password
Add-BitLockerKeyProtector -MountPoint "E:" -RecoveryPasswordProtector

# GPO per richiedere BitLocker su drive rimovibili
# Computer → Administrative Templates → Windows Components →
#   BitLocker Drive Encryption → Removable Data Drives
#   → Deny write access to removable drives not protected by BitLocker: Enabled
#   → Do not allow write access to devices configured in another organization: Checked

# Sbloccare da un altro computer
Unlock-BitLocker -MountPoint "E:" -Password (ConvertTo-SecureString "ComplexP@ss!" `
    -AsPlainText -Force)

# Verificare stato drive rimovibili
Get-BitLockerVolume -MountPoint "E:" |
    Select-Object MountPoint, VolumeType, ProtectionStatus, LockStatus, EncryptionMethod
```

### Network Unlock

Network Unlock permette lo sblocco automatico di BitLocker quando il computer è connesso alla rete aziendale via cavo (Ethernet). Utile per server e desktop in data center.

Prerequisiti:
- UEFI con firmware che supporta DHCP.
- Server WDS (Windows Deployment Services) con il certificato Network Unlock.
- Computer collegato via Ethernet alla rete aziendale.
- GPO che abilita Network Unlock.

```powershell
# 1. Installare feature WDS e BitLocker Network Unlock sul server
Install-WindowsFeature WDS-Deployment, BitLocker-NetworkUnlock

# 2. Creare certificato per Network Unlock
# Usare un template di certificato con EKU "BitLocker Drive Encryption Network Unlock"
# OID: 1.3.6.1.4.1.311.67.1.1

# 3. Distribuire il certificato al TPM dei client via GPO
# Computer → Administrative Templates → Windows Components →
#   BitLocker → Operating System Drives →
#   Allow network unlock at startup: Enabled

# 4. Aggiungere il protettore Network Unlock
Add-BitLockerKeyProtector -MountPoint "C:" -TpmAndNetworkUnlockProtector

# Verificare protettori attivi
(Get-BitLockerVolume -MountPoint "C:").KeyProtector |
    Select-Object KeyProtectorType, KeyProtectorId
```

### Gestione con MBAM

Microsoft BitLocker Administration and Monitoring (MBAM) fornisce una console centralizzata per gestire BitLocker in ambienti enterprise. Sostituito in parte da Microsoft Intune/Endpoint Manager.

Funzionalità MBAM:
- **Self-service portal**: utenti possono recuperare la recovery key autonomamente.
- **Helpdesk portal**: IT può recuperare recovery key per utenti.
- **Compliance reporting**: report sullo stato di crittografia di tutti i dispositivi.
- **Policy enforcement**: verifica che i computer rispettino le policy di crittografia.
- **Recovery key escrow**: backup centralizzato di tutte le recovery key.

```powershell
# Con Microsoft Intune (sostituto cloud di MBAM):
# Endpoint Manager → Devices → Configuration profiles →
#   Create profile → Windows 10 → Endpoint protection → BitLocker

# Report compliance:
# Endpoint Manager → Reports → Device configuration → BitLocker

# Recovery key da Intune:
# Endpoint Manager → Devices → [device] → Recovery keys

# Recovery key da Azure AD / Entra ID:
# Azure AD → Devices → [device] → BitLocker keys
```

---

## Credential Guard

```powershell
# Credential Guard usa la Virtualization Based Security (VBS) per isolare
# le credenziali (hash NTLM, ticket Kerberos) in un container protetto.
# Previene attacchi Pass-the-Hash e Pass-the-Ticket.

# Prerequisiti:
# - UEFI con Secure Boot
# - TPM 2.0 (consigliato)
# - Hyper-V (VBS)
# - Windows 10/11 Enterprise o Windows Server 2016+

# Abilitare via GPO (consigliato)
# Computer → Administrative Templates → System → Device Guard
# → Turn on Virtualization Based Security: Enabled
#   → Credential Guard Configuration: Enabled with UEFI lock

# Abilitare via PowerShell/Registry
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard" `
    -Name "EnableVirtualizationBasedSecurity" -Value 1
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "LsaCfgFlags" -Value 1  # 1=UEFI lock, 2=senza lock

# Verificare stato
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
    Select-Object VirtualizationBasedSecurityStatus,
        SecurityServicesRunning,
        SecurityServicesConfigured

# Output: SecurityServicesRunning = {1, 2}
# 1 = Credential Guard, 2 = Hypervisor enforced Code Integrity
```

### Architettura Credential Guard

```
┌─────────────────────────────────────────────────────────┐
│                    VTL 0 (Normal World)                 │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ lsass.exe│  │ App.exe  │  │ Driver.sys           │  │
│  │ (proxy)  │  │          │  │                      │  │
│  └────┬─────┘  └──────────┘  └──────────────────────┘  │
│       │                                                 │
│       │ chiamata sicura                                 │
│───────┼─────────────────────────────────────────────────│
│       ▼                                                 │
│  ┌─────────────────────────────────────────────────┐    │
│  │               VTL 1 (Secure World)              │    │
│  │                                                  │    │
│  │  ┌──────────────────────────┐                   │    │
│  │  │ LSA Isolated (lsaiso.exe)│                   │    │
│  │  │ - NTLM hash             │                   │    │
│  │  │ - Kerberos TGT          │                   │    │
│  │  │ - Derived credentials   │                   │    │
│  │  └──────────────────────────┘                   │    │
│  │                                                  │    │
│  │  Secure Kernel (SK)                             │    │
│  └──────────────────────────────────────────────────┘    │
│                                                         │
│  Hypervisor (Hyper-V)                                   │
└─────────────────────────────────────────────────────────┘
```

Credential Guard isola le credenziali in VTL 1 (Virtual Trust Level 1), inaccessibile dal sistema operativo normale (VTL 0). Anche un kernel compromesso o un admin con SeDebugPrivilege non può leggere le credenziali protette.

**Cosa protegge Credential Guard**:
- Hash NTLM
- Ticket Kerberos TGT
- Credenziali derivate (derived domain credentials)

**Cosa NON protegge**:
- Password in chiaro (se digitate e ancora in memoria prima di hashing)
- Credenziali di account locali (solo dominio)
- Credenziali di servizi (gMSA non interessate)
- Credenziali di applicazioni terze (browser, password manager)

```powershell
# Verificare con msinfo32
# System Information → Virtualization-based security Services Running
# Deve mostrare "Credential Guard"

# Verificare da PowerShell
$dg = Get-CimInstance -ClassName Win32_DeviceGuard `
    -Namespace root\Microsoft\Windows\DeviceGuard
if ($dg.SecurityServicesRunning -contains 1) {
    Write-Output "Credential Guard attivo"
} else {
    Write-Output "Credential Guard NON attivo"
}

# Disabilitare Credential Guard (se necessario per compatibilità)
# ATTENZIONE: rimuovere con UEFI lock richiede accesso fisico al BIOS
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "LsaCfgFlags" -Value 0
# Se abilitato con UEFI lock: richiede tool mountvol + bcdedit dal BIOS
```

---

## Windows Firewall Avanzato

### Profili e regole

```powershell
# PROFILI: Domain, Private, Public

# Stato
Get-NetFirewallProfile | Select-Object Name, Enabled, DefaultInboundAction, DefaultOutboundAction

# Configurare profili
Set-NetFirewallProfile -Profile Domain -Enabled True -DefaultInboundAction Block `
    -DefaultOutboundAction Allow -LogAllowed False -LogBlocked True `
    -LogFileName "%SystemRoot%\System32\LogFiles\Firewall\pfirewall.log" `
    -LogMaxSizeKilobytes 16384

# REGOLE

# Creare regola in ingresso
New-NetFirewallRule -DisplayName "Allow-WebServer" -Direction Inbound `
    -Protocol TCP -LocalPort 80, 443 -Action Allow -Profile Domain `
    -Description "Permettere traffico web"

# Creare regola per applicazione specifica
New-NetFirewallRule -DisplayName "Allow-SQL" -Direction Inbound `
    -Program "C:\Program Files\Microsoft SQL Server\MSSQL16.MSSQLSERVER\MSSQL\Binn\sqlservr.exe" `
    -Action Allow -Profile Domain

# Regola con IP sorgente
New-NetFirewallRule -DisplayName "Allow-RDP-Admin" -Direction Inbound `
    -Protocol TCP -LocalPort 3389 -RemoteAddress 192.168.10.0/24 `
    -Action Allow -Profile Domain

# Bloccare specifico
New-NetFirewallRule -DisplayName "Block-Telnet" -Direction Outbound `
    -Protocol TCP -RemotePort 23 -Action Block -Profile Any

# Elencare regole attive
Get-NetFirewallRule -Enabled True -Direction Inbound |
    Select-Object DisplayName, Profile, Action | Sort-Object DisplayName

# Regole per porta specifica
Get-NetFirewallPortFilter -Protocol TCP | Where-Object LocalPort -eq 3389 |
    Get-NetFirewallRule | Select-Object DisplayName, Enabled, Action

# Disabilitare/rimuovere regola
Disable-NetFirewallRule -DisplayName "Allow-WebServer"
Remove-NetFirewallRule -DisplayName "Allow-WebServer"

# IPsec Connection Security Rules
New-NetIPsecRule -DisplayName "Server-to-Server" -InboundSecurity Require `
    -OutboundSecurity Request -Phase1AuthSet (
        New-NetIPsecAuthProposal -Machine -Cert `
            -Authority "DC=com, DC=contoso, DC=corp, CN=Corp-CA" -AuthorityType Root
    )
```

#### Dettaglio profili

| Profilo | Quando si applica | Best Practice |
|---------|-------------------|---------------|
| Domain | Computer connesso alla rete con domain controller raggiungibile | Inbound Block, Outbound Allow, regole specifiche per servizi |
| Private | Rete fidata non di dominio (home) | Inbound Block, Outbound Allow |
| Public | Reti non fidate (hotel, aeroporto, caffè) | Inbound Block, Outbound Block (o Allow con restrizioni) |

```powershell
# Configurazione completa dei tre profili
Set-NetFirewallProfile -Profile Domain `
    -Enabled True -DefaultInboundAction Block -DefaultOutboundAction Allow `
    -LogBlocked True -LogMaxSizeKilobytes 32768 -NotifyOnListen True

Set-NetFirewallProfile -Profile Private `
    -Enabled True -DefaultInboundAction Block -DefaultOutboundAction Allow `
    -LogBlocked True -LogMaxSizeKilobytes 16384

Set-NetFirewallProfile -Profile Public `
    -Enabled True -DefaultInboundAction Block -DefaultOutboundAction Block `
    -LogBlocked True -LogMaxSizeKilobytes 16384 -AllowUnicastResponseToMulticast False

# Regole per servizi comuni — Domain Profile
New-NetFirewallRule -DisplayName "Allow-DNS-Out" -Direction Outbound `
    -Protocol UDP -RemotePort 53 -Action Allow -Profile Domain
New-NetFirewallRule -DisplayName "Allow-LDAP-Out" -Direction Outbound `
    -Protocol TCP -RemotePort 389, 636 -Action Allow -Profile Domain
New-NetFirewallRule -DisplayName "Allow-Kerberos-Out" -Direction Outbound `
    -Protocol TCP -RemotePort 88 -Action Allow -Profile Domain
New-NetFirewallRule -DisplayName "Allow-SMB-Out" -Direction Outbound `
    -Protocol TCP -RemotePort 445 -Action Allow -Profile Domain
```

### Connection Security Rules (IPsec)

Le Connection Security Rules stabiliscono connessioni autenticate e crittografate tra computer usando IPsec.

```powershell
# Creare regola di isolamento dominio
# Tutti i computer del dominio devono autenticarsi reciprocamente
New-NetIPsecRule -DisplayName "Domain-Isolation" `
    -InboundSecurity Require -OutboundSecurity Request `
    -Phase1AuthSet (New-NetIPsecAuthProposal -Machine -Kerberos) `
    -Profile Domain

# Regola server-to-server con certificato
$certProposal = New-NetIPsecAuthProposal -Machine -Cert `
    -Authority "CN=Corp-CA, DC=corp, DC=contoso, DC=com" `
    -AuthorityType Root
$authSet = New-NetIPsecPhase1AuthSet -DisplayName "CertAuth" `
    -Proposal $certProposal
New-NetIPsecRule -DisplayName "SQL-to-App-Encrypted" `
    -InboundSecurity Require -OutboundSecurity Require `
    -Phase1AuthSet $authSet.Name `
    -Protocol TCP -LocalPort 1433 `
    -Profile Domain

# Creare regola con crittografia obbligatoria
New-NetIPsecRule -DisplayName "Encrypted-Connection" `
    -InboundSecurity Require -OutboundSecurity Require `
    -Phase1AuthSet $authSet.Name `
    -EncryptedTunnelBypass $false `
    -RequireAuthorization $true

# Visualizzare connection security rules attive
Get-NetIPsecRule | Where-Object Enabled -eq True |
    Select-Object DisplayName, InboundSecurity, OutboundSecurity, Profile

# Main mode (Phase 1) security associations
Get-NetIPsecMainModeSA | Select-Object LocalEndpoint, RemoteEndpoint

# Quick mode (Phase 2) security associations
Get-NetIPsecQuickModeSA | Select-Object LocalEndpoint, RemoteEndpoint, EncryptionAlgorithm
```

### Deploy centralizzato via GPO

```
Computer → Windows Settings → Security Settings → Windows Defender Firewall
→ Inbound Rules / Outbound Rules
# Creare regole centralizzate che si applicano a tutti i server/workstation
```

```powershell
# Esportare le regole firewall correnti per backup/distribuzione
netsh advfirewall export "C:\Backup\firewall-rules.wfw"

# Importare regole
netsh advfirewall import "C:\Backup\firewall-rules.wfw"

# Export in formato leggibile (PowerShell)
Get-NetFirewallRule -Enabled True |
    Select-Object DisplayName, Direction, Action, Profile, Enabled |
    Export-Csv "C:\Backup\firewall-rules.csv" -NoTypeInformation

# Best practice per deploy GPO:
# 1. Creare GPO dedicata per firewall ("SEC-Firewall-Servers", "SEC-Firewall-Workstations")
# 2. Definire regole nel nodo "Windows Defender Firewall with Advanced Security"
# 3. Impostare "Apply local firewall rules" = No (per override regole locali)
# 4. Impostare "Apply local connection security rules" = No
# 5. Testare su OU di test prima del rollout
```

---

## Audit Policy e Logging

### Configurazione Audit

```powershell
# Audit Policy avanzata (consigliata su Security Baseline)
# Computer → Windows Settings → Security Settings → Advanced Audit Policy Configuration

# Abilitare via auditpol (command line)
auditpol /set /subcategory:"Logon" /success:enable /failure:enable
auditpol /set /subcategory:"Logoff" /success:enable
auditpol /set /subcategory:"Account Lockout" /success:enable /failure:enable
auditpol /set /subcategory:"Special Logon" /success:enable
auditpol /set /subcategory:"Other Logon/Logoff Events" /success:enable /failure:enable
auditpol /set /subcategory:"Security Group Management" /success:enable
auditpol /set /subcategory:"User Account Management" /success:enable /failure:enable
auditpol /set /subcategory:"Computer Account Management" /success:enable
auditpol /set /subcategory:"Process Creation" /success:enable
auditpol /set /subcategory:"Audit Policy Change" /success:enable
auditpol /set /subcategory:"Authentication Policy Change" /success:enable

# Verificare
auditpol /get /category:*
```

### Event ID Importanti

| Event ID | Log | Significato |
|----------|-----|-------------|
| 4624 | Security | Logon riuscito |
| 4625 | Security | Logon fallito |
| 4634 | Security | Logoff |
| 4648 | Security | Logon con credenziali esplicite (runas) |
| 4720 | Security | Account utente creato |
| 4722 | Security | Account utente abilitato |
| 4725 | Security | Account utente disabilitato |
| 4726 | Security | Account utente eliminato |
| 4728 | Security | Membro aggiunto a gruppo security global |
| 4732 | Security | Membro aggiunto a gruppo security local |
| 4740 | Security | Account locked out |
| 4756 | Security | Membro aggiunto a gruppo universal |
| 4767 | Security | Account unlocked |
| 4688 | Security | Nuovo processo creato |
| 1102 | Security | Audit log cancellato |
| 7045 | System | Nuovo servizio installato |

### Query Event Log con PowerShell

```powershell
# Logon falliti nelle ultime 24 ore
Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    Id = 4625
    StartTime = (Get-Date).AddDays(-1)
} | Select-Object TimeCreated,
    @{N='User';E={$_.Properties[5].Value}},
    @{N='Source';E={$_.Properties[19].Value}},
    @{N='Status';E={$_.Properties[7].Value}}

# Account lockout
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4740} -MaxEvents 50 |
    Select-Object TimeCreated,
        @{N='User';E={$_.Properties[0].Value}},
        @{N='CallerComputer';E={$_.Properties[1].Value}}

# Servizi installati (potenziale malware)
Get-WinEvent -FilterHashtable @{LogName='System'; Id=7045} -MaxEvents 20 |
    Select-Object TimeCreated,
        @{N='ServiceName';E={$_.Properties[0].Value}},
        @{N='ServicePath';E={$_.Properties[1].Value}},
        @{N='ServiceAccount';E={$_.Properties[4].Value}}

# Configurare dimensione log
wevtutil sl Security /ms:1073741824   # 1 GB
wevtutil sl System /ms:268435456      # 256 MB

# Forwarding eventi (Windows Event Forwarding - WEF)
# Collector: wecutil qc
# Source: winrm quickconfig
# Subscription: wecutil cs subscription.xml
```

### Event ID critici da monitorare

Elenco esteso di Event ID critici per un SOC/SIEM:

| Event ID | Log | Categoria | Priorità | Significato |
|----------|-----|-----------|----------|-------------|
| 1102 | Security | Audit | CRITICA | Log di sicurezza cancellato — possibile cover-up |
| 4616 | Security | System | ALTA | Ora di sistema modificata |
| 4624 tipo 10 | Security | Logon | MEDIA | Logon RDP riuscito |
| 4625 | Security | Logon | ALTA | Logon fallito (brute force se ripetuto) |
| 4648 | Security | Logon | ALTA | Logon con credenziali esplicite (lateral movement) |
| 4657 | Security | Registry | MEDIA | Valore di registro modificato |
| 4672 | Security | Logon | ALTA | Privilegi speciali assegnati a un logon |
| 4688 | Security | Process | MEDIA | Nuovo processo creato (con command line se abilitato) |
| 4697 | Security | Service | ALTA | Servizio installato nel sistema |
| 4698 | Security | Task | ALTA | Task schedulato creato |
| 4719 | Security | Policy | CRITICA | System audit policy modificata |
| 4720 | Security | Account | ALTA | Account utente creato |
| 4724 | Security | Account | ALTA | Tentativo di reset password |
| 4728 | Security | Group | ALTA | Membro aggiunto a gruppo privilegiato |
| 4732 | Security | Group | ALTA | Membro aggiunto a Administrators locale |
| 4740 | Security | Account | ALTA | Account locked out |
| 4756 | Security | Group | ALTA | Membro aggiunto a gruppo universal |
| 4768 | Security | Kerberos | MEDIA | TGT richiesto (AS-REQ) |
| 4769 | Security | Kerberos | MEDIA | Service Ticket richiesto (Kerberoasting se etype 23) |
| 4771 | Security | Kerberos | ALTA | Pre-auth fallita (password sbagliata) |
| 4776 | Security | NTLM | ALTA | Credential validation (NTLM auth) |
| 5140 | Security | Share | MEDIA | Accesso a share di rete |
| 5145 | Security | Share | MEDIA | Accesso a oggetto su share |
| 7045 | System | Service | ALTA | Nuovo servizio installato |
| 4104 | PowerShell | Script | ALTA | Script block logging (contenuto script) |
| 4103 | PowerShell | Module | MEDIA | Module logging |

```powershell
# Abilitare command line nel Event ID 4688
# GPO: Computer → Administrative Templates → System → Audit Process Creation
# → Include command line in process creation events: Enabled
# Questo è FONDAMENTALE per threat hunting

# Abilitare PowerShell Script Block Logging
# GPO: Computer → Administrative Templates → Windows Components →
#   Windows PowerShell → Turn on PowerShell Script Block Logging: Enabled
# Registra il contenuto completo degli script PowerShell eseguiti

# Abilitare PowerShell Transcription
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\Transcription" `
    -Name "EnableTranscripting" -Value 1
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\Transcription" `
    -Name "OutputDirectory" -Value "C:\PSTranscripts"

# Query multi-evento per correlazione (esempio: account lockout chain)
$lockoutEvents = Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4740} -MaxEvents 10
foreach ($evt in $lockoutEvents) {
    $user = $evt.Properties[0].Value
    $source = $evt.Properties[1].Value
    Write-Output "$($evt.TimeCreated) | User: $user | Source: $source"

    # Cercare i logon falliti correlati
    Get-WinEvent -FilterHashtable @{
        LogName='Security'; Id=4625
        StartTime = $evt.TimeCreated.AddMinutes(-30)
        EndTime = $evt.TimeCreated
    } -MaxEvents 20 | Where-Object { $_.Properties[5].Value -eq $user } |
        ForEach-Object {
            Write-Output "  ← Failed logon at $($_.TimeCreated) from $($_.Properties[19].Value)"
        }
}
```

### Sysmon

Sysmon (System Monitor) è uno strumento Sysinternals che fornisce logging avanzato degli eventi di sistema. Complementa il Security Log con dettagli che Windows non registra nativamente.

Event ID Sysmon principali:

| Event ID | Significato |
|----------|-------------|
| 1 | Process Create (con hash, parent process, command line) |
| 2 | File creation time changed (timestomping) |
| 3 | Network connection |
| 5 | Process terminated |
| 6 | Driver loaded |
| 7 | Image loaded (DLL loading) |
| 8 | CreateRemoteThread (injection) |
| 10 | Process Access (es. LSASS access) |
| 11 | File created |
| 12-14 | Registry events (create, delete, set value) |
| 15 | FileCreateStreamHash (Alternate Data Streams) |
| 17-18 | Pipe created/connected (lateral movement) |
| 22 | DNS query |
| 23 | File delete (con archiviazione) |
| 25 | Process tampering |

```powershell
# Installare Sysmon con configurazione SwiftOnSecurity
# 1. Scaricare Sysmon da Sysinternals
# 2. Scaricare config: github.com/SwiftOnSecurity/sysmon-config

# Installare
sysmon64.exe -accepteula -i sysmonconfig-export.xml

# Aggiornare configurazione
sysmon64.exe -c sysmonconfig-export.xml

# Verificare stato
sysmon64.exe -c

# Query Sysmon Log
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" -MaxEvents 20 |
    Select-Object TimeCreated, Id, Message

# Process creation con command line (Event ID 1)
Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-Sysmon/Operational'
    Id = 1
} -MaxEvents 20 | ForEach-Object {
    [PSCustomObject]@{
        Time = $_.TimeCreated
        Image = $_.Properties[4].Value
        CommandLine = $_.Properties[10].Value
        ParentImage = $_.Properties[20].Value
        User = $_.Properties[12].Value
    }
}

# Network connections (Event ID 3)
Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-Sysmon/Operational'
    Id = 3
} -MaxEvents 20 | ForEach-Object {
    [PSCustomObject]@{
        Time = $_.TimeCreated
        Image = $_.Properties[4].Value
        DestIP = $_.Properties[14].Value
        DestPort = $_.Properties[16].Value
        User = $_.Properties[12].Value
    }
}

# LSASS access (Event ID 10 — potenziale credential dumping)
Get-WinEvent -FilterHashtable @{
    LogName = 'Microsoft-Windows-Sysmon/Operational'
    Id = 10
} -MaxEvents 50 | Where-Object { $_.Properties[8].Value -like "*lsass*" } |
    Select-Object TimeCreated, @{N='SourceImage'; E={$_.Properties[4].Value}},
        @{N='TargetImage'; E={$_.Properties[8].Value}},
        @{N='GrantedAccess'; E={$_.Properties[18].Value}}
```

### Windows Event Forwarding (WEF)

WEF permette la raccolta centralizzata degli eventi di sicurezza da tutti i computer del dominio verso un collector centrale.

```powershell
# === COLLECTOR (server che raccoglie gli eventi) ===

# 1. Abilitare il servizio di raccolta
wecutil qc /q

# 2. Creare subscription XML
# Esempio subscription per eventi critici di sicurezza:
```

```xml
<!-- subscription-security.xml -->
<Subscription xmlns="http://schemas.microsoft.com/2006/03/windows/events/subscription">
    <SubscriptionId>SecurityEvents</SubscriptionId>
    <SubscriptionType>SourceInitiated</SubscriptionType>
    <Description>Raccolta eventi sicurezza critici</Description>
    <Enabled>true</Enabled>
    <Uri>http://schemas.microsoft.com/wbem/wsman/1/windows/EventLog</Uri>
    <ConfigurationMode>Custom</ConfigurationMode>
    <Delivery Mode="Push">
        <Batching>
            <MaxLatencyTime>900000</MaxLatencyTime>
        </Batching>
    </Delivery>
    <Query>
        <![CDATA[
        <QueryList>
            <Query Id="0">
                <Select Path="Security">
                    *[System[(EventID=4624 or EventID=4625 or EventID=4648 or
                              EventID=4672 or EventID=4688 or EventID=4720 or
                              EventID=4728 or EventID=4732 or EventID=4740 or
                              EventID=1102)]]
                </Select>
                <Select Path="System">
                    *[System[(EventID=7045)]]
                </Select>
                <Select Path="Microsoft-Windows-Sysmon/Operational">
                    *[System[(EventID=1 or EventID=3 or EventID=8 or EventID=10)]]
                </Select>
            </Query>
        </QueryList>
        ]]>
    </Query>
    <ReadExistingEvents>false</ReadExistingEvents>
    <TransportName>HTTP</TransportName>
    <AllowedSourceNonDomainComputers></AllowedSourceNonDomainComputers>
    <AllowedSourceDomainComputers>
        O:NSG:NSD:(A;;GA;;;DC)(A;;GA;;;NS)
    </AllowedSourceDomainComputers>
</Subscription>
```

```powershell
# 3. Creare la subscription
wecutil cs subscription-security.xml

# 4. Verificare subscription
wecutil gs SecurityEvents
wecutil gr SecurityEvents    # runtime status (quanti source connessi)

# === SOURCE (computer che inviano eventi) ===

# 1. Configurare WinRM
winrm quickconfig /q

# 2. Aggiungere il computer account del collector al gruppo
#    "Event Log Readers" locale (via GPO consigliato)
# GPO: Computer → Preferences → Control Panel → Local Users and Groups
#   → Event Log Readers → Add → CORP\COLLECTOR-SRV$

# 3. Configurare la subscription manager via GPO:
# Computer → Administrative Templates → Windows Components →
#   Event Forwarding → Configure target Subscription Manager
# → Enabled → Server=http://collector.corp.contoso.com:5985/wsman/SubscriptionManager/WEC

# Verificare dal source
wevtutil gl ForwardedEvents

# Query eventi raccolti sul collector
Get-WinEvent -LogName "ForwardedEvents" -MaxEvents 20 |
    Select-Object TimeCreated, Id, MachineName, Message
```

---

## AppLocker e WDAC

### AppLocker

```powershell
# AppLocker controlla quali applicazioni possono essere eseguite
# Tipi di regole: Executable, Windows Installer, Script, Packaged App, DLL

# Prerequisiti: Windows Enterprise/Education, servizio AppIDSvc attivo
Set-Service AppIDSvc -StartupType Automatic
Start-Service AppIDSvc

# Creare policy di default (allow tutto per admin, allow Windows per tutti)
# Via GPO: Computer → Windows Settings → Security Settings → Application Control Policies → AppLocker

# Esempio: bloccare esecuzione da cartelle utente
# Tipo: Executable Rules
# Azione: Deny
# Path: %USERPROFILE%\*
# Eccezione: nessuna
# Applicato a: Everyone (escluso BUILTIN\Administrators)

# Generare policy da PowerShell
Get-AppLockerPolicy -Effective -Xml | Out-File "C:\AppLocker-Current.xml"

# Testare policy
Test-AppLockerPolicy -XmlPolicy "C:\AppLocker-Policy.xml" `
    -Path "C:\Users\Public\Downloads\setup.exe" -User "Everyone"

# Event Log AppLocker
Get-WinEvent -LogName "Microsoft-Windows-AppLocker/EXE and DLL" -MaxEvents 20
# Mode Audit: Event ID 8003 (would be blocked)
# Mode Enforce: Event ID 8004 (blocked)
```

#### Tipi di regole AppLocker

| Tipo | Criteri disponibili | Uso |
|------|---------------------|-----|
| Publisher | Firma digitale + nome prodotto + versione | Più flessibile, consigliato |
| Path | Percorso file/cartella | Semplice ma aggirabile (copia file altrove) |
| File Hash | Hash SHA256 del file | Più sicuro ma richiede aggiornamento a ogni update |

```powershell
# Creare regola Publisher via PowerShell
$ruleInfo = New-Object Microsoft.Security.ApplicationId.PolicyManagement.PolicyModel.RuleInfo
# In pratica, le regole si gestiscono più facilmente via GPO o XML

# Generare regole automatiche da scansione del sistema
Get-AppLockerFileInformation -Directory "C:\Program Files" -Recurse `
    -FileType Exe | New-AppLockerPolicy -RuleType Publisher, Hash `
    -User "Everyone" -Optimize | Out-File "C:\AppLocker-ProgramFiles.xml"

# Unire policy
$policy1 = Get-Content "C:\AppLocker-Current.xml"
$policy2 = Get-Content "C:\AppLocker-ProgramFiles.xml"
# Merge via Set-AppLockerPolicy

# Modalità di enforcement
# Audit Only — registra nei log senza bloccare (Event ID 8003)
# Enforce    — blocca e registra (Event ID 8004)
# CONSIGLIO: SEMPRE Audit prima di Enforce, per almeno 2 settimane
```

#### AppLocker Event ID

| Event ID | Log | Significato |
|----------|-----|-------------|
| 8001 | AppLocker/EXE and DLL | Policy applicata con successo |
| 8002 | AppLocker/EXE and DLL | File consentito dalla regola |
| 8003 | AppLocker/EXE and DLL | File che SAREBBE stato bloccato (Audit Mode) |
| 8004 | AppLocker/EXE and DLL | File bloccato |
| 8005 | AppLocker/MSI and Script | File consentito |
| 8006 | AppLocker/MSI and Script | File che sarebbe stato bloccato (Audit) |
| 8007 | AppLocker/MSI and Script | File bloccato |

### WDAC (Windows Defender Application Control)

```powershell
# WDAC è il successore moderno di AppLocker
# Più sicuro (kernel-level), più complesso, più potente

# Creare policy base da audit di un sistema di riferimento
New-CIPolicy -FilePath "C:\WDAC\BasePolicy.xml" -Level Publisher `
    -Fallback Hash -UserPEs -ScanPath "C:\"

# Convertire in policy binaria
ConvertFrom-CIPolicy -XmlFilePath "C:\WDAC\BasePolicy.xml" `
    -BinaryFilePath "C:\WDAC\BasePolicy.p7b"

# Attivare in Audit Mode prima
Set-RuleOption -FilePath "C:\WDAC\BasePolicy.xml" -Option 3  # Audit Mode

# Deploy con GPO:
# Computer → Administrative Templates → System → Device Guard
# → Deploy Windows Defender Application Control: Enabled
# → Policy path: \\share\WDAC\BasePolicy.p7b
```

#### AppLocker vs WDAC — Confronto

| Caratteristica | AppLocker | WDAC |
|----------------|-----------|------|
| Livello di protezione | User-mode | Kernel-mode (più sicuro) |
| Bypass possibili | Sì (multiple tecniche note) | Molto più difficile |
| Edizioni Windows supportate | Enterprise/Education | Tutte (da Win10 1903) |
| Gestione | GPO, semplice | GPO/MDM/ConfigMgr, complesso |
| DLL enforcement | Opzionale (impatto prestazioni) | Integrato |
| Managed Installer | No | Sì (consente app da SCCM/Intune) |
| Intelligent Security Graph | No | Sì (ISG — consente app note come sicure) |

```powershell
# WDAC — Livelli di fiducia per le regole
# Publisher    — firma + nome editore
# FilePublisher — firma + nome file + versione
# FileName     — nome file (senza firma)
# SignedVersion — firmato + versione minima
# Hash         — SHA256 hash
# WHQLFilePublisher — specifico per driver WHQL

# Creare policy supplementare (per aggiungere regole a una base policy)
New-CIPolicy -FilePath "C:\WDAC\SupplementalPolicy.xml" -Level Publisher `
    -Fallback Hash -ScanPath "C:\CustomApps"
Set-CIPolicyIdInfo -FilePath "C:\WDAC\SupplementalPolicy.xml" `
    -BasePolicyToSupplementPath "C:\WDAC\BasePolicy.xml"

# Permettere Managed Installer (SCCM/Intune/MECM)
Set-RuleOption -FilePath "C:\WDAC\BasePolicy.xml" -Option 13  # Managed Installer

# Abilitare Intelligent Security Graph
Set-RuleOption -FilePath "C:\WDAC\BasePolicy.xml" -Option 14  # ISG

# Convertire e deployare
ConvertFrom-CIPolicy -XmlFilePath "C:\WDAC\SupplementalPolicy.xml" `
    -BinaryFilePath "C:\WDAC\SupplementalPolicy.p7b"

# Log WDAC (CodeIntegrity)
Get-WinEvent -LogName "Microsoft-Windows-CodeIntegrity/Operational" -MaxEvents 20 |
    Select-Object TimeCreated, Id, Message
# Event ID 3076 = Audit (sarebbe stato bloccato)
# Event ID 3077 = Block (file bloccato)
```

---

## LAPS — Local Admin Password Solution

```powershell
# LAPS gestisce automaticamente la password dell'admin locale di ogni computer,
# memorizzandola in AD con accesso controllato.

# Windows LAPS (integrato in Windows Server 2022+ e Windows 11 22H2+)

# 1. Configurare schema AD (una volta)
Update-LapsADSchema

# 2. Configurare permessi OU
Set-LapsADComputerSelfPermission -Identity "OU=Computer,DC=corp,DC=contoso,DC=com"

# 3. Configurare chi può leggere le password
Set-LapsADReadPasswordPermission -Identity "OU=Computer,DC=corp,DC=contoso,DC=com" `
    -AllowedPrincipals "CORP\GG-IT-Admins"

# 4. Deploy via GPO
# Computer → Administrative Templates → System → LAPS
# - Configure password backup directory: Active Directory
# - Password Settings:
#   - Complexity: Large letters + small letters + numbers + specials
#   - Length: 20
#   - Age: 30 days
# - Name of administrator account to manage: (lasciare vuoto per default admin)
# - Enable password encryption: Enabled

# Leggere password
Get-LapsADPassword -Identity "WKS-IT-001" -AsPlainText
# Output: Account, Password, PasswordUpdateTime, ExpirationTimestamp

# Reset password (forza rotazione)
Reset-LapsPassword -Identity "WKS-IT-001"

# Audit: chi ha letto le password
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4662} |
    Where-Object { $_.Message -like "*ms-Mcs-AdmPwd*" }
```

### LAPS — Legacy vs Windows LAPS

| Caratteristica | Legacy LAPS | Windows LAPS |
|----------------|-------------|--------------|
| Storage | Attributo AD in chiaro (ms-Mcs-AdmPwd) | Attributo AD crittografato |
| Crittografia password | No | Sì (DPAPI-NG) |
| Backup in Azure AD | No | Sì |
| Cronologia password | No | Sì |
| Account gestiti | Solo 1 admin locale | Multipli account |
| Rotazione automatica | Sì | Sì |
| Componente | Add-on da installare | Integrato nell'OS |

---

## Protezione credenziali avanzata

### Protected Users

Il gruppo **Protected Users** (introdotto in Windows Server 2012 R2) applica protezioni aggiuntive ai suoi membri:

- **Niente caching credenziali**: le credenziali non vengono memorizzate localmente (né NTLM hash, né testo in chiaro, né ticket a lungo termine).
- **Niente NTLM**: l'autenticazione NTLM è bloccata. Solo Kerberos.
- **Niente DES o RC4 per Kerberos**: solo AES.
- **TGT con durata ridotta**: 4 ore invece di 10 (non rinnovabile).
- **Niente delegation**: constrained e unconstrained delegation bloccate.

```powershell
# Aggiungere utenti al gruppo Protected Users
Add-ADGroupMember -Identity "Protected Users" -Members "admin-tier0", "svc-critical"

# Verificare membri
Get-ADGroupMember -Identity "Protected Users" | Select-Object Name, SamAccountName

# ATTENZIONE: testare prima! Account in Protected Users:
# - Non possono usare CredSSP → impatta RDP con NLA in alcuni scenari
# - Non possono usare Windows Digest → impatta applicazioni legacy
# - Non possono usare NTLM → impatta sistemi che non supportano Kerberos
# - Niente caching offline → non possono loggarsi se DC non raggiungibile

# Verificare se un utente è in Protected Users
$user = Get-ADUser -Identity "admin-tier0" -Properties MemberOf
$user.MemberOf | Where-Object { $_ -like "*Protected Users*" }

# Monitorare errori di autenticazione per Protected Users
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625} -MaxEvents 100 |
    Where-Object { $_.Properties[5].Value -in @("admin-tier0", "svc-critical") } |
    Select-Object TimeCreated, @{N='User';E={$_.Properties[5].Value}},
        @{N='FailureReason';E={$_.Properties[8].Value}}
```

### Authentication Policies e Silos

Le **Authentication Policies** (Windows Server 2012 R2+) permettono di vincolare dove gli account privilegiati possono autenticarsi, implementando il modello **tier**.

```powershell
# Creare un Authentication Policy per account Tier 0
New-ADAuthenticationPolicy -Name "Tier0-Policy" `
    -Description "Policy per account Tier 0 - solo DC" `
    -UserTGTLifetimeMins 240 `
    -Enforce

# Condizione: il TGT viene emesso solo se il computer è un DC
Set-ADAuthenticationPolicy -Identity "Tier0-Policy" `
    -UserAllowedToAuthenticateFrom (
        New-ADAuthenticationPolicySilo -Name "Tier0-Silo" | Out-Null
        "O:SYG:SYD:(XA;OICI;CR;;;WD;(@USER.ad://ext/AuthenticationSilo == `"Tier0-Silo`"))"
    )

# Creare Authentication Silo
New-ADAuthenticationPolicySilo -Name "Tier0-Silo" `
    -Description "Silo Tier 0: DC e account admin Tier 0" `
    -UserAuthenticationPolicy "Tier0-Policy" `
    -ComputerAuthenticationPolicy "Tier0-Policy" `
    -Enforce

# Assegnare account al silo
Grant-ADAuthenticationPolicySiloAccess -Identity "Tier0-Silo" `
    -Account "admin-tier0"
Set-ADUser -Identity "admin-tier0" `
    -AuthenticationPolicySilo "Tier0-Silo" `
    -AuthenticationPolicy "Tier0-Policy"

# Assegnare computer al silo
Grant-ADAuthenticationPolicySiloAccess -Identity "Tier0-Silo" `
    -Account "DC01$"
Set-ADComputer -Identity "DC01" `
    -AuthenticationPolicySilo "Tier0-Silo"

# Verificare assegnamenti
Get-ADAuthenticationPolicySilo -Identity "Tier0-Silo" -Properties Members |
    Select-Object -ExpandProperty Members
```

**Modello Tier**:

| Tier | Asset | Account | Silo |
|------|-------|---------|------|
| 0 | Domain Controller, PKI, ADFS | Domain Admins, Enterprise Admins | Tier0-Silo |
| 1 | Server applicativi, database | Server Admins | Tier1-Silo |
| 2 | Workstation, laptop | Helpdesk, Desktop Admins | Tier2-Silo |

---

## Windows Security Baseline

### Microsoft Security Compliance Toolkit

```powershell
# Scaricare da Microsoft:
# Security Compliance Toolkit + LGPO.exe

# Applicare baseline con LGPO
# LGPO.exe /g "C:\Baselines\Windows Server 2022\GPOs\{GUID}"

# Confrontare con baseline corrente
# PolicyAnalyzer.exe (incluso nel toolkit)

# Baseline principali (impostazioni chiave):

# Account Policy:
# - Min password length: 14
# - Password complexity: Enabled
# - Account lockout threshold: 10
# - Account lockout duration: 15 min

# Local Policies → User Rights:
# - Deny log on locally: Guests
# - Deny access from network: Guests, Local account (non-admin)

# Security Options:
# - Interactive logon: Don't display last signed-in: Enabled
# - Network access: Do not allow anonymous enum of SAM accounts: Enabled
# - Network security: LAN Manager authentication level: Send NTLMv2 only

# Audit:
# - Tutte le categorie elencate nella sezione Audit sopra

# Windows Firewall:
# - Tutti i profili: Enabled, Inbound: Block, Outbound: Allow
```

### CIS Benchmarks

I CIS (Center for Internet Security) Benchmarks forniscono linee guida di hardening indipendenti dal vendor, suddivise in due livelli:

- **Level 1 (L1)**: impostazioni che possono essere applicate senza impatto significativo sulla funzionalità.
- **Level 2 (L2)**: impostazioni più restrittive che possono impattare la funzionalità.

```powershell
# CIS Benchmark — Impostazioni chiave per Windows 10/11 Enterprise

# L1 — Account Policies
# Password minimum length: 14
# Account lockout threshold: 5
# Account lockout duration: 15 min
# Reset account lockout counter after: 15 min

# L1 — Audit Policy
auditpol /set /subcategory:"Credential Validation" /success:enable /failure:enable
auditpol /set /subcategory:"Application Group Management" /success:enable /failure:enable
auditpol /set /subcategory:"Security Group Management" /success:enable
auditpol /set /subcategory:"User Account Management" /success:enable /failure:enable
auditpol /set /subcategory:"Plug and Play Events" /success:enable
auditpol /set /subcategory:"Process Creation" /success:enable
auditpol /set /subcategory:"Account Lockout" /failure:enable
auditpol /set /subcategory:"Group Membership" /success:enable
auditpol /set /subcategory:"Logon" /success:enable /failure:enable
auditpol /set /subcategory:"Other Logon/Logoff Events" /success:enable /failure:enable
auditpol /set /subcategory:"Special Logon" /success:enable
auditpol /set /subcategory:"Removable Storage" /success:enable /failure:enable

# L1 — Security Options
# Accounts: Block Microsoft accounts: Users can't add or log on with Microsoft accounts
# Interactive logon: Machine inactivity limit: 900 seconds
# Network access: Do not allow anonymous enumeration of SAM accounts and shares: Enabled
# Network security: Allow Local System to use computer identity for NTLM: Enabled
# Network security: Do not store LAN Manager hash value on next password change: Enabled

# L2 — Impostazioni aggiuntive
# Network access: Restrict anonymous access to Named Pipes and Shares: Enabled
# Network security: Allow LocalSystem NULL session fallback: Disabled
# System objects: Strengthen default permissions of internal system objects: Enabled

# Verificare conformità con CIS-CAT (tool ufficiale CIS)
# O con script PowerShell di audit
```

### DISA STIG

I DISA (Defense Information Systems Agency) STIG (Security Technical Implementation Guides) sono gli standard di sicurezza del Dipartimento della Difesa USA. Più restrittivi dei CIS Benchmarks.

```powershell
# STIG — Impostazioni chiave per Windows Server

# V-254239: Password minimum length must be 14 characters
net accounts /minpwlen:14

# V-254240: Account lockout threshold must be 3 or fewer invalid logon attempts
net accounts /lockoutthreshold:3

# V-254269: Unencrypted passwords must not be sent to third-party SMB servers
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanWorkstation\Parameters" `
    -Name "EnablePlainTextPassword" -Value 0 -Type DWord

# V-254272: Outgoing secure channel traffic must be encrypted or signed
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Netlogon\Parameters" `
    -Name "RequireSignOrSeal" -Value 1 -Type DWord

# V-254273: Strong session key must be required for secure channel
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Netlogon\Parameters" `
    -Name "RequireStrongKey" -Value 1 -Type DWord

# V-254282: WDigest Authentication must be disabled
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\WDigest" `
    -Name "UseLogonCredential" -Value 0 -Type DWord

# Applicare STIG con SCAP Compliance Checker (SCC)
# Scaricare da public.cyber.mil
# SCC analizza il sistema e genera report XCCDF/ARF
```

---

## Local Security Policy e Security Compliance Toolkit

La Local Security Policy (`secpol.msc`) è l'interfaccia per le policy di sicurezza locali su sistemi non in dominio o come override locale.

```powershell
# Sezioni principali di secpol.msc:

# Account Policies
# ├── Password Policy
# │   ├── Enforce password history: 24
# │   ├── Maximum password age: 90 days
# │   ├── Minimum password age: 1 day
# │   ├── Minimum password length: 14
# │   └── Password must meet complexity requirements: Enabled
# └── Account Lockout Policy
#     ├── Account lockout threshold: 10
#     ├── Account lockout duration: 15 min
#     └── Reset account lockout counter after: 15 min

# Local Policies
# ├── Audit Policy (legacy — usare Advanced Audit Policy)
# ├── User Rights Assignment
# │   ├── Access this computer from the network
# │   ├── Deny log on locally
# │   ├── Deny access to this computer from the network
# │   ├── Log on as a service
# │   ├── Log on as a batch job
# │   └── Shut down the system
# └── Security Options
#     ├── Accounts: *
#     ├── Interactive logon: *
#     ├── Network access: *
#     ├── Network security: *
#     └── User Account Control: *

# Esportare policy locale
secedit /export /cfg "C:\Backup\secpol.cfg" /log "C:\Backup\secpol.log"

# Importare policy
secedit /configure /db "C:\Temp\secedit.sdb" /cfg "C:\Backup\secpol.cfg" /log "C:\Backup\import.log"

# Analizzare conformità rispetto a un template
secedit /analyze /db "C:\Temp\analysis.sdb" /cfg "C:\Baselines\baseline.inf" /log "C:\Temp\analysis.log"

# Security Compliance Toolkit — Workflow
# 1. Scaricare da microsoft.com/download
# 2. Estrarre le baseline GPO
# 3. Usare PolicyAnalyzer.exe per confrontare le impostazioni correnti
# 4. Usare LGPO.exe per applicare le baseline
# 5. Ri-analizzare per verificare conformità

# LGPO — applicare una baseline
# LGPO.exe /g "C:\Baselines\Win11-23H2-Security-Baseline\GPOs\{GUID}"
# /g = apply Group Policy from backup folder

# LGPO — esportare policy corrente per confronto
# LGPO.exe /b "C:\Backup\CurrentGPO"
```

---

## Riduzione della superficie di attacco

### Hardening servizi

```powershell
# Disabilitare servizi non necessari
$servicesDisable = @(
    "RemoteRegistry",    # Accesso remoto al registro
    "XblAuthManager",    # Xbox Live Auth
    "XboxNetApiSvc",     # Xbox Live Networking
    "DiagTrack",         # Connected User Experiences and Telemetry
    "dmwappushservice",  # WAP Push Message Routing
    "MapsBroker",        # Downloaded Maps Manager
    "lfsvc",             # Geolocation
    "SharedAccess",      # Internet Connection Sharing (ICS)
    "WMPNetworkSvc",     # Windows Media Player Network Sharing
    "FDResPub",          # Function Discovery Resource Publication
    "SSDPSRV"            # SSDP Discovery
)

foreach ($svc in $servicesDisable) {
    Set-Service -Name $svc -StartupType Disabled -ErrorAction SilentlyContinue
    Stop-Service -Name $svc -Force -ErrorAction SilentlyContinue
}

# Verificare servizi con credenziali non standard
Get-WmiObject Win32_Service | Where-Object {
    $_.StartName -notin @("LocalSystem", "NT AUTHORITY\LocalService",
        "NT AUTHORITY\NetworkService", "NT Authority\LocalService",
        "NT Authority\NetworkService", $null, "")
} | Select-Object Name, StartName, StartMode, State

# Usare gMSA (Group Managed Service Accounts) per servizi
# 1. Creare KDS root key (una volta per foresta)
Add-KdsRootKey -EffectiveImmediately
# In produzione: Add-KdsRootKey -EffectiveTime ((Get-Date).AddHours(-10))

# 2. Creare gMSA
New-ADServiceAccount -Name "gmsa-SqlSvc" `
    -DNSHostName "gmsa-sqlsvc.corp.contoso.com" `
    -PrincipalsAllowedToRetrieveManagedPassword "SqlServers$" `
    -KerberosEncryptionType AES256

# 3. Installare gMSA sul server
Install-ADServiceAccount -Identity "gmsa-SqlSvc"

# 4. Testare
Test-ADServiceAccount -Identity "gmsa-SqlSvc"
# True = funzionante

# 5. Configurare il servizio per usare il gMSA
# services.msc → Proprietà servizio → Log On → This account → CORP\gmsa-SqlSvc$
# La password viene gestita automaticamente da AD
```

### SMB Signing

SMB Signing previene attacchi man-in-the-middle e NTLM relay sulle connessioni SMB.

```powershell
# Verificare stato corrente
Get-SmbServerConfiguration | Select-Object EnableSecuritySignature, RequireSecuritySignature
Get-SmbClientConfiguration | Select-Object EnableSecuritySignature, RequireSecuritySignature

# EnableSecuritySignature = firma negoziata (se entrambi supportano)
# RequireSecuritySignature = firma obbligatoria (connessioni rifiutate senza firma)

# Abilitare firma obbligatoria (server)
Set-SmbServerConfiguration -RequireSecuritySignature $true -Force

# Abilitare firma obbligatoria (client)
Set-SmbClientConfiguration -RequireSecuritySignature $true -Force

# Via GPO (consigliato):
# Computer → Windows Settings → Security Settings → Local Policies → Security Options
# → Microsoft network server: Digitally sign communications (always): Enabled
# → Microsoft network client: Digitally sign communications (always): Enabled

# SMB Encryption (più sicuro di signing, ma maggiore overhead)
Set-SmbServerConfiguration -EncryptData $true -Force
# Nota: richiede client SMB 3.0+ (Windows 8+, Server 2012+)

# Verificare connessioni SMB attive e il loro stato di firma/crittografia
Get-SmbSession | Select-Object ClientComputerName, ClientUserName,
    SigningRequired, EncryptData

# Disabilitare SMBv1 (CRITICO — vulnerabile a EternalBlue/WannaCry)
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force
Disable-WindowsOptionalFeature -Online -FeatureName "SMB1Protocol" -NoRestart
```

### LDAP Signing e Channel Binding

LDAP Signing previene attacchi man-in-the-middle sulle connessioni LDAP, mentre Channel Binding lega la connessione LDAP al canale TLS sottostante.

```powershell
# === LDAP Signing ===

# Verificare stato corrente del DC
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" `
    -Name "LDAPServerIntegrity" -ErrorAction SilentlyContinue
# 0 = None, 1 = Require signing (consigliato), 2 = Require signing (più restrittivo)

# Abilitare LDAP Signing sul DC (via Registry)
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" `
    -Name "LDAPServerIntegrity" -Value 2 -Type DWord

# Via GPO (consigliato):
# Computer → Windows Settings → Security Settings → Local Policies → Security Options
# → Domain controller: LDAP server signing requirements: Require signing

# Client LDAP signing
# Computer → Windows Settings → Security Settings → Local Policies → Security Options
# → Network security: LDAP client signing requirements: Require signing

# === LDAP Channel Binding ===

# Abilitare Channel Binding sul DC
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" `
    -Name "LdapEnforceChannelBinding" -Value 2 -Type DWord
# 0 = Never, 1 = When supported, 2 = Always (consigliato)

# ATTENZIONE: prima di forzare, monitorare Event ID 3039 nel log Directory Service
# Questi eventi indicano client che non supportano Channel Binding
Get-WinEvent -FilterHashtable @{
    LogName = 'Directory Service'
    Id = 3039
} -MaxEvents 50 | Select-Object TimeCreated, Message

# Audit LDAP non firmato (Event ID 2889 — attivare PRIMA di forzare)
# Monitorare per 2-4 settimane prima di impostare "Require"
Get-WinEvent -FilterHashtable @{
    LogName = 'Directory Service'
    Id = 2889
} -MaxEvents 100 | Select-Object TimeCreated, Message
```

### Disabilitazione protocolli legacy

```powershell
# === SMBv1 ===
# Già trattato sopra — DISABILITARE SEMPRE
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force

# === LLMNR (Link-Local Multicast Name Resolution) ===
# Vulnerabile a poisoning/relay. Disabilitare.
# GPO: Computer → Administrative Templates → Network → DNS Client
# → Turn off multicast name resolution: Enabled
# Registry:
New-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" `
    -Name "EnableMulticast" -Value 0 -Type DWord -Force

# === NetBIOS over TCP/IP ===
# Vulnerabile a poisoning. Disabilitare su tutte le interfacce.
# Per interfaccia specifica:
$adapters = Get-WmiObject Win32_NetworkAdapterConfiguration -Filter "IPEnabled=true"
foreach ($adapter in $adapters) {
    $adapter.SetTcpipNetbios(2)  # 0=Default, 1=Enable, 2=Disable
}

# === WPAD (Web Proxy Auto-Discovery) ===
# Vulnerabile ad attacchi di rogue proxy. Disabilitare.
# GPO: Computer → Administrative Templates → Windows Components →
#   Internet Explorer → Disable caching of Auto-Proxy scripts: Enabled
# Registry:
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\WinHttpAutoProxySvc" `
    -Name "Start" -Value 4 -Type DWord  # Disabled

# === NTLMv1 ===
# Già trattato nella sezione autenticazione. Forzare NTLMv2:
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" `
    -Name "LmCompatibilityLevel" -Value 5 -Type DWord
# 5 = Send NTLMv2 response only. Refuse LM & NTLM

# === WDigest ===
# WDigest memorizza password in chiaro in memoria. Disabilitare.
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\WDigest" `
    -Name "UseLogonCredential" -Value 0 -Type DWord

# === Remote Desktop (se non necessario) ===
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server" `
    -Name "fDenyTSConnections" -Value 1 -Type DWord
# Se necessario, limitare con NLA:
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp" `
    -Name "UserAuthentication" -Value 1 -Type DWord  # NLA Required

# === Print Spooler (se non necessario, specialmente su DC) ===
Stop-Service Spooler -Force
Set-Service Spooler -StartupType Disabled
# PrintNightmare (CVE-2021-34527) sfrutta il servizio Spooler
```

---

## Windows Sandbox e Application Guard

### Windows Sandbox

Windows Sandbox fornisce un ambiente desktop leggero ed effimero per eseguire applicazioni non fidate. Al chiuso, tutto viene eliminato.

```powershell
# Prerequisiti:
# - Windows 10/11 Pro o Enterprise
# - Virtualizzazione hardware abilitata (BIOS/UEFI)
# - Almeno 4 GB RAM (8 consigliati)
# - 1 GB spazio disco libero

# Installare
Enable-WindowsOptionalFeature -Online -FeatureName "Containers-DisposableClientVM" -NoRestart

# Avviare: Start Menu → Windows Sandbox

# Configurazione avanzata con file .wsb (XML)
```

```xml
<!-- sandbox-config.wsb -->
<Configuration>
    <!-- Rete: Enable o Disable -->
    <Networking>Enable</Networking>

    <!-- GPU virtualizzata -->
    <vGPU>Enable</vGPU>

    <!-- Cartelle condivise con l'host (sola lettura consigliata) -->
    <MappedFolders>
        <MappedFolder>
            <HostFolder>C:\Users\utente\Downloads\DaTestare</HostFolder>
            <SandboxFolder>C:\Test</SandboxFolder>
            <ReadOnly>true</ReadOnly>
        </MappedFolder>
    </MappedFolders>

    <!-- Script di avvio automatico -->
    <LogonCommand>
        <Command>explorer.exe C:\Test</Command>
    </LogonCommand>

    <!-- Memoria (MB) -->
    <MemoryInMB>4096</MemoryInMB>

    <!-- Appunti: Enable o Disable -->
    <ClipboardRedirection>Disable</ClipboardRedirection>

    <!-- Stampante: Enable o Disable -->
    <PrinterRedirection>Disable</PrinterRedirection>

    <!-- Audio: Enable o Disable -->
    <AudioInput>Disable</AudioInput>
    <VideoInput>Disable</VideoInput>

    <!-- Protezione da manomissione della sandbox -->
    <ProtectedClient>Enable</ProtectedClient>
</Configuration>
```

### Microsoft Defender Application Guard (MDAG)

Application Guard isola la navigazione web in un container Hyper-V separato, proteggendo il sistema da exploit browser e download malevoli.

```powershell
# Installare Application Guard
Enable-WindowsOptionalFeature -Online -FeatureName "Windows-Defender-ApplicationGuard" -NoRestart

# Configurare via GPO:
# Computer → Administrative Templates → Windows Components →
#   Microsoft Defender Application Guard

# Impostazioni chiave:
# - Turn on Microsoft Defender Application Guard in Managed Mode: Enabled
#   → 1 = Enable for Edge only
#   → 2 = Enable for isolated Windows environments only
#   → 3 = Enable for Edge AND isolated Windows environments
#
# - Allow data persistence for MDAG: Disabled (massima sicurezza)
# - Allow camera and microphone access: Disabled
# - Allow hardware-accelerated rendering: Enabled
# - Configure clipboard settings: Disabled (o solo text-to-host)
# - Configure print settings: Disabled (o solo Print to PDF)
# - Block enterprise websites to load non-enterprise content in IE/Edge: Enabled

# Configurare siti trusted (enterprise) vs non-trusted
# Le network boundaries definiscono quali siti sono "enterprise":
# Computer → Administrative Templates → Network → Network Isolation
# → Enterprise resource domains hosted in the cloud
# → Domains categorized as both work and personal

# Verificare stato
Get-WindowsOptionalFeature -Online -FeatureName "Windows-Defender-ApplicationGuard"

# Application Guard supporta anche:
# - Office files: Word, Excel, PowerPoint aperti in container isolato
# - PDF files: visualizzazione in container
# Richiede Microsoft 365 Apps for Enterprise
```

---

## Best Practices

1. **Defense in depth**: non affidarsi a un singolo layer. BitLocker + Credential Guard + LAPS + AppLocker + Firewall + Audit
2. **Least privilege**: utenti standard, admin separati, gMSA per servizi
3. **Patch regolarmente**: WSUS o WUfB con finestre di manutenzione definite
4. **Baseline di sicurezza**: applicare e verificare periodicamente le Microsoft Security Baselines
5. **Monitorare i log**: Event Forwarding centralizzato, alert su Event ID critici (4625, 4740, 4720, 7045, 1102)
6. **Disabilitare protocolli legacy**: SMBv1, LLMNR, NetBIOS, WPAD, NTLMv1
7. **BitLocker ovunque**: su tutti i dispositivi, recovery key in AD, TPM + PIN per laptop
8. **Tiered administration model**: account separati per Tier 0/1/2, Authentication Policies e Silos
9. **Protected Users**: aggiungere tutti gli account privilegiati al gruppo Protected Users
10. **LSA Protection**: attivare RunAsPPL su tutti i sistemi
11. **Credential Guard**: abilitare su tutti i sistemi che supportano VBS
12. **Sysmon**: distribuire con configurazione SwiftOnSecurity su tutti gli endpoint
13. **LAPS**: implementare su tutti i computer per gestire le password admin locali
14. **ASR rules**: abilitare tutte le regole in Audit, poi passare a Block dopo 2 settimane
15. **WEF**: centralizzare la raccolta eventi verso un collector/SIEM

---

## Troubleshooting

**"BitLocker chiede recovery key dopo aggiornamento BIOS"** → Sospendere BitLocker PRIMA di aggiornare BIOS/firmware (`Suspend-BitLocker -RebootCount 1`). Se bloccato: usare recovery key salvata in AD.

**"AppLocker blocca applicazioni legittime"** → Impostare in Audit Mode prima di Enforce. Verificare i log: `Get-WinEvent -LogName "Microsoft-Windows-AppLocker/EXE and DLL"`. Creare eccezione per l'applicazione.

**"Credential Guard non si attiva"** → Verificare: UEFI con Secure Boot abilitato, TPM 2.0 presente, Hyper-V installato, edizione Enterprise/Education. Controllare `msinfo32` → Virtualization Based Security.

**"Account lockout senza causa apparente"** → Verificare PDC Emulator Event ID 4740 per identificare il computer sorgente. Cause comuni: sessioni RDP dimenticate, servizi con password vecchia, dispositivi mobili, task schedulati.

**"Kerberos fallisce e il sistema usa NTLM"** → Verificare SPN con `setspn -X` (duplicati). Verificare che il nome usato sia un FQDN (Kerberos richiede nomi risolvibili). Controllare che le porte TCP 88 (Kerberos) e UDP 88 siano aperte verso il DC. Verificare sincronizzazione oraria (tolleranza default: 5 minuti).

**"LSA Protection blocca applicazioni legitimate"** → Alcune applicazioni iniettano DLL in lsass.exe. Verificare Event ID 3033/3034 nel log CodeIntegrity. Se necessario, aggiungere il driver/DLL alla whitelist tramite HVCI policy, oppure disabilitare temporaneamente RunAsPPL (non consigliato in produzione).

**"BitLocker non si attiva: TPM non pronto"** → Eseguire `Initialize-Tpm`. Se TPM è ownership sconosciuta, eseguire `Clear-Tpm` (ATTENZIONE: cancella tutte le chiavi TPM). Verificare che TPM sia abilitato nel BIOS/UEFI. Su sistemi senza TPM: abilitare via GPO "Allow BitLocker without a compatible TPM" e usare chiave USB come protettore.

**"WDAC blocca applicazioni dopo deploy"** → Verificare Event ID 3076 (audit) o 3077 (block) nel log CodeIntegrity. Creare una policy supplementare con le eccezioni necessarie. Usare il Wizard WDAC per generare regole. SEMPRE testare in Audit Mode prima.

**"Windows Defender real-time protection si disattiva da solo"** → Possibile conflitto con altro antivirus. Verificare `Get-MpComputerStatus`. Se antivirus terzo è installato, Defender si disattiva. Se non c'è altro antivirus: verificare che il servizio `WinDefend` sia in esecuzione e `StartupType` sia Automatic. Controllare GPO che potrebbe disabilitarlo.

**"Firewall blocca connessioni dopo join al dominio"** → Verificare che il profilo corretto sia attivo: `Get-NetConnectionProfile`. Il profilo "Domain" si attiva solo quando il DC è raggiungibile. Se il profilo è "Public", le regole Domain non si applicano. Eseguire `nltest /dsgetdc:dominio.com` per diagnostica.

**"SMB Signing causa rallentamento significativo"** → Overhead di ~10-15% è normale. Se l'impatto è maggiore: verificare hardware di rete, driver NIC aggiornati, offload capabilities. Considerare SMB Encryption (SMB 3.0+) che include signing e ha overhead simile con maggiore sicurezza.

**"Event Log Security pieno e non registra nuovi eventi"** → Aumentare dimensione: `wevtutil sl Security /ms:4294967296` (4 GB). Configurare retention policy: `wevtutil sl Security /rt:false` (overwrite oldest events). Implementare WEF per centralizzare e archivare gli eventi.

**"Sysmon non registra eventi"** → Verificare che il servizio sia in esecuzione: `Get-Service Sysmon64`. Verificare la configurazione: `sysmon64.exe -c`. Ricontrollare il file XML di configurazione per errori di sintassi. Reinstallare: `sysmon64.exe -u force` poi `sysmon64.exe -i config.xml`.

**"Protected Users causa errori di autenticazione"** → L'account non può usare NTLM, DES, RC4. Verificare che tutti i sistemi target supportino Kerberos con AES. Applicazioni legacy che richiedono NTLM non funzioneranno. Il caching offline è disabilitato: l'utente non può loggarsi se il DC non è raggiungibile (problema per laptop).

**"LAPS non aggiorna la password"** → Verificare che il computer abbia i permessi di self-write sull'attributo ms-LAPS-Password: `Set-LapsADComputerSelfPermission`. Verificare la GPO LAPS. Controllare Event Log: `Get-WinEvent -LogName "Microsoft-Windows-LAPS/Operational"`. Verificare che il servizio LAPS Agent sia in esecuzione.

**"BitLocker recovery key non trovata in AD"** → Verificare che la GPO "Do not enable BitLocker until recovery information is stored in AD DS" sia attivata. Se il backup non è avvenuto: eseguire `Backup-BitLockerKeyProtector` manualmente. Verificare la replica AD: la recovery key potrebbe essere su un altro DC.

**"UAC prompt non appare ma l'applicazione fallisce"** → Verificare `ConsentPromptBehaviorAdmin` nel registro. Se impostato su 0 (elevate without prompting) E l'utente non è admin, l'app fallisce silenziosamente. Reimpostare a 5 (default). Verificare anche `EnableLUA = 1`.

**"NTLM audit mostra migliaia di eventi"** → Normale in ambienti con applicazioni legacy. Identificare le sorgenti: filtrare per IP/hostname. Creare eccezioni per i server necessari. Pianificare la migrazione delle applicazioni a Kerberos prima di bloccare NTLM.

**"ASR rule blocca un'applicazione interna"** → Aggiungere l'applicazione alle esclusioni ASR: `Add-MpPreference -AttackSurfaceReductionOnlyExclusions "C:\App\*"`. Verificare quale regola specifica blocca (Event ID 1121 mostra il GUID della regola). Impostare quella regola in Audit per l'applicazione.

**"Network Protection blocca siti legittimi"** → Verificare Event ID 1125 per il dominio bloccato. Aggiungere ai Custom Indicators in Microsoft Defender for Endpoint (se disponibile). In alternativa, impostare Network Protection in AuditMode temporaneamente. Segnalare falso positivo a Microsoft.

**"Controlled Folder Access blocca applicazioni fidate"** → Aggiungere l'applicazione alla lista consentita: `Add-MpPreference -ControlledFolderAccessAllowedApplications "C:\App\app.exe"`. Verificare che l'app firmi con un certificato valido. Event ID 1123 mostra l'app bloccata.

---

## FAQ

**D: Qual è la differenza tra AppLocker e WDAC? Quale scegliere?**
R: AppLocker opera in user-mode ed è più semplice da gestire tramite GPO, ma è aggirabile con tecniche note (es. DLL injection, LOLBAS). WDAC opera a livello kernel, è molto più difficile da bypassare ed è disponibile su tutte le edizioni di Windows 10/11 (da 1903). Per ambienti con requisiti di sicurezza elevati, scegliere WDAC. Per ambienti dove la semplicità di gestione è prioritaria, AppLocker è accettabile come controllo addizionale.

**D: Credential Guard protegge da tutti gli attacchi di credential theft?**
R: No. Credential Guard protegge hash NTLM, ticket Kerberos TGT e credenziali derivate dal dominio. NON protegge da: keylogger (la password viene digitata), password in chiaro memorizzate da applicazioni terze, credenziali locali (SAM), credenziali di applicazioni (browser, RDP client). Per una protezione completa, combinare con Windows Hello/FIDO2, LSA Protection e Protected Users.

**D: Devo disabilitare NTLM completamente?**
R: L'obiettivo è sì, ma il percorso richiede pianificazione. Fase 1: attivare NTLM auditing per 4-8 settimane. Fase 2: identificare e migrare applicazioni che usano NTLM. Fase 3: forzare NTLMv2 e rifiutare LM/NTLMv1. Fase 4: creare eccezioni per i sistemi residui. Fase 5: bloccare NTLM con eccezioni. Molte applicazioni legacy, scanner di rete, NAS e stampanti richiedono NTLM. Non bloccare senza audit preventivo.

**D: Come posso verificare se il mio sistema è conforme alla baseline CIS/STIG?**
R: Per CIS: usare CIS-CAT Lite/Pro (tool ufficiale che scansiona il sistema). Per STIG: usare SCAP Compliance Checker (SCC) di DISA. Per Microsoft: usare PolicyAnalyzer del Security Compliance Toolkit. In alternativa, script PowerShell di audit come quelli di HardeningKitty o Ping Castle (per AD).

**D: BitLocker con solo TPM è sicuro o serve anche il PIN?**
R: Solo TPM protegge da furto fisico del disco (estrazione e montaggio su altro computer), ma è vulnerabile a attacchi cold boot, DMA attacks (se porte Thunderbolt/FireWire sono accessibili) e TPM sniffing (su TPM discreti con bus LPC esposto). TPM + PIN aggiunge un secondo fattore che rende questi attacchi inefficaci. Per laptop, TPM + PIN è fortemente consigliato. Per server in data center con sicurezza fisica, solo TPM è accettabile.

**D: Cosa succede se il TPM si guasta e BitLocker è attivo?**
R: Il sistema chiede la recovery key al boot. Procedura: 1) Inserire la recovery key (48 cifre). 2) Una volta avviato, sospendere BitLocker: `Suspend-BitLocker`. 3) Sostituire il TPM o la scheda madre. 4) Riattivare BitLocker con il nuovo TPM: `Resume-BitLocker`. Se la recovery key non è disponibile: i dati sono persi. Per questo è mandatorio salvare le recovery key in AD/Azure AD/Intune.

**D: LAPS è necessario se uso Credential Guard?**
R: Sì. Credential Guard protegge le credenziali di dominio, non le password degli account locali. Se ogni computer ha la stessa password admin locale, un attaccante che la ottiene (da un singolo computer compromesso) può usarla per il lateral movement verso tutti gli altri computer. LAPS randomizza la password admin locale su ogni computer, eliminando questo vettore.

**D: Come implemento il modello Tiered Administration?**
R: Fase 1: creare account separati per ogni tier (admin-t0@corp, admin-t1@corp, admin-t2@corp). Fase 2: configurare Authentication Policies e Silos per vincolare ogni tier. Fase 3: implementare PAW (Privileged Access Workstations) per il Tier 0. Fase 4: configurare GPO per impedire logon cross-tier (es. Domain Admin non può loggarsi su workstation). Fase 5: monitorare violazioni con auditing.

**D: Windows Sandbox vs Application Guard: quale usare?**
R: Windows Sandbox è un desktop completo ed effimero per testare qualsiasi applicazione. Tutto viene cancellato alla chiusura. Application Guard è specifico per la navigazione web (Edge) e i file Office: isola il browser in un container Hyper-V con policy aziendali. Usare Sandbox per test di applicazioni sospette. Usare Application Guard per la navigazione quotidiana su siti non fidati.

**D: Quali sono gli Event ID minimi da monitorare per un SOC?**
R: Priorità assoluta (CRITICA): 1102 (log cancellato), 4720 (account creato), 4728/4732 (aggiunta a gruppi privilegiati), 4740 (lockout massivo), 7045 (servizio installato). Priorità alta: 4624 tipo 10 (RDP logon), 4625 (logon falliti), 4648 (credenziali esplicite), 4672 (privilegi speciali), 4688 (process creation con command line), 4697 (servizio installato via Security log). Se disponibile Sysmon: Event ID 1 (process create), 3 (network), 8 (CreateRemoteThread), 10 (LSASS access).

**D: Come proteggo i Domain Controller?**
R: 1) Tier 0 isolation con Authentication Policies. 2) Credential Guard e LSA Protection. 3) Nessun software non necessario installato. 4) Firewall restrittivo (solo porte AD necessarie). 5) Disabilitare Print Spooler (PrintNightmare). 6) BitLocker. 7) Sysmon con config dettagliata. 8) LAPS non serve su DC (non hanno account admin locale nel senso tradizionale). 9) Monitorare Event ID 4769 con etype 23 (Kerberoasting). 10) Rotazione password krbtgt ogni 6 mesi.

**D: Perché devo disabilitare LLMNR e NetBIOS?**
R: LLMNR (porta UDP 5355) e NetBIOS Name Service (porta UDP 137) sono protocolli di risoluzione nomi multicast/broadcast. Un attaccante nella stessa rete può rispondere a queste query fingendosi il server richiesto (poisoning), catturando gli hash NTLMv2 dell'utente. Strumenti come Responder automatizzano questo attacco. Disabilitare entrambi ed usare solo DNS.

**D: SMB Signing rallenta le prestazioni. Posso disabilitarlo?**
R: No, a meno che il rischio di NTLM relay sia accettabile nel vostro ambiente. L'overhead è tipicamente 10-15%. Su reti moderne con hardware adeguato, l'impatto è trascurabile. SMB Signing è l'unica protezione contro NTLM relay su SMB, un attacco che permette di ottenere accesso a qualsiasi share di rete. In ambienti ad alte prestazioni (es. cluster Hyper-V con storage SMB), considerare SMB Encryption che include signing.

**D: Come funziona la pre-authentication Kerberos e perché è importante?**
R: Senza pre-authentication, chiunque può richiedere un TGT al KDC per qualsiasi utente — il KDC risponde con dati crittografati con l'hash della password dell'utente. L'attaccante può poi fare brute force offline (AS-REP Roasting). Con pre-authentication abilitata, il client deve dimostrare di conoscere la password (inviando un timestamp crittografato) PRIMA che il KDC emetta il TGT. Verificare: `Get-ADUser -Filter {DoesNotRequirePreAuth -eq $true}` — ogni account restituito è vulnerabile.

**D: Come aggiorno la configurazione Sysmon senza reinstallarlo?**
R: Eseguire `sysmon64.exe -c nuova-config.xml`. L'aggiornamento è immediato, senza riavvio e senza perdita di eventi. Per verificare la configurazione attiva: `sysmon64.exe -c` (senza argomenti). Per monitorare modifiche alla config: Sysmon Event ID 16 registra ogni cambio di configurazione.

**D: Posso usare Credential Guard su macchine virtuali?**
R: Sì, con nested virtualization. L'hypervisor host deve supportare nested virt (Hyper-V lo supporta da Windows Server 2016). Su VMware, abilitare "Expose hardware assisted virtualization to the guest OS". Su cloud (Azure): usare VM di generazione 2 con Trusted Launch. Performance: l'overhead è maggiore rispetto a bare metal, ma accettabile nella maggior parte dei casi.

---

## Checklist di Hardening

### Windows 10/11 Enterprise — Workstation

```
IDENTITÀ E AUTENTICAZIONE
[ ] Password minima 14 caratteri con complessità
[ ] Account lockout: 5 tentativi, 15 minuti
[ ] Windows Hello for Business abilitato
[ ] UAC al massimo livello con Secure Desktop
[ ] FilterAdministratorToken = 1
[ ] Account admin locali separati (no uso quotidiano)
[ ] LAPS implementato per admin locale

PROTEZIONE CREDENZIALI
[ ] Credential Guard abilitato (VBS + UEFI lock)
[ ] LSA Protection (RunAsPPL) abilitato
[ ] WDigest disabilitato (UseLogonCredential = 0)
[ ] Caching credenziali ridotto (CachedLogonsCount = 2)
[ ] Protected Users per account privilegiati

CRITTOGRAFIA
[ ] BitLocker attivo su tutti i volumi
[ ] XTS-AES 256 per drive fissi
[ ] TPM + PIN per laptop
[ ] Recovery key salvata in AD/Azure AD
[ ] BitLocker To Go per drive rimovibili

ANTIMALWARE E EXPLOIT PROTECTION
[ ] Windows Defender real-time protection attivo
[ ] Cloud-delivered protection (MAPS) Advanced
[ ] ASR rules tutte attive (Block, non solo Audit)
[ ] Controlled Folder Access abilitato
[ ] Network Protection abilitato
[ ] Exploit Protection configurato (DEP, ASLR, CFG, SEHOP)
[ ] PUA Protection abilitato

CONTROLLO APPLICAZIONI
[ ] AppLocker o WDAC in enforcement mode
[ ] Blocco esecuzione da %USERPROFILE% e %TEMP%
[ ] PowerShell Constrained Language Mode (via WDAC)

RETE
[ ] Firewall abilitato su tutti e tre i profili
[ ] Profilo Public: Inbound Block, Outbound Block
[ ] SMBv1 disabilitato
[ ] LLMNR disabilitato
[ ] NetBIOS su TCP/IP disabilitato
[ ] WPAD disabilitato
[ ] NTLMv1 bloccato (LmCompatibilityLevel = 5)
[ ] SMB Signing obbligatorio
[ ] RDP con NLA obbligatorio (o disabilitato)

LOGGING E MONITORAGGIO
[ ] Advanced Audit Policy configurata
[ ] Sysmon installato con configurazione adeguata
[ ] PowerShell Script Block Logging abilitato
[ ] Command line in Event 4688 abilitato
[ ] Log Security dimensionato a 1+ GB
[ ] WEF configurato verso collector centrale

SISTEMA
[ ] Secure Boot abilitato
[ ] UEFI firmware aggiornato
[ ] Windows Update automatico o WSUS
[ ] Servizi non necessari disabilitati
[ ] Account Guest disabilitato
[ ] Shares amministrativi (C$, ADMIN$) monitorati
[ ] Print Spooler disabilitato se non necessario
```

### Windows Server 2022 — Server

```
IDENTITÀ E AUTENTICAZIONE
[ ] Password minima 14 caratteri (STIG: 15+)
[ ] Account lockout: 3 tentativi (STIG), 15 minuti
[ ] gMSA per tutti i servizi applicativi
[ ] Nessun accesso interattivo con account di servizio
[ ] Tiered administration model implementato
[ ] Authentication Policies e Silos configurati (per DC)

PROTEZIONE CREDENZIALI
[ ] Credential Guard abilitato (dove supportato)
[ ] LSA Protection (RunAsPPL) abilitato
[ ] Protected Users per Domain Admins e Enterprise Admins
[ ] WDigest disabilitato
[ ] Logon remoto limitato per account privilegiati

CRITTOGRAFIA
[ ] BitLocker attivo su tutti i volumi
[ ] XTS-AES 256
[ ] Network Unlock per server in data center
[ ] Recovery key in AD
[ ] TLS 1.2 minimo (disabilitare TLS 1.0/1.1)

ANTIMALWARE
[ ] Windows Defender attivo (se non c'è AV enterprise)
[ ] Esclusioni configurate per ruoli server (SQL, Exchange, ecc.)
[ ] ASR rules compatibili con il ruolo del server

RETE
[ ] Firewall abilitato con regole minime per il ruolo
[ ] Solo porte necessarie aperte
[ ] SMBv1 disabilitato
[ ] SMB Signing obbligatorio
[ ] SMB Encryption (dove possibile)
[ ] LDAP Signing obbligatorio
[ ] LDAP Channel Binding abilitato
[ ] LLMNR disabilitato
[ ] NetBIOS disabilitato
[ ] IPsec per comunicazioni server-to-server sensibili

HARDENING SPECIFICO PER RUOLO
[ ] Domain Controller: Print Spooler disabilitato
[ ] Domain Controller: Nessun software aggiuntivo
[ ] Domain Controller: Solo Tier 0 admin possono loggarsi
[ ] File Server: ABE (Access Based Enumeration) abilitato
[ ] SQL Server: gMSA per il servizio
[ ] Web Server: Application Pool con identità dedicata
[ ] Tutti: Remote Desktop limitato a jump server/PAW

LOGGING E MONITORAGGIO
[ ] Advanced Audit Policy configurata (tutte le categorie critiche)
[ ] Sysmon installato
[ ] WEF configurato verso SIEM
[ ] Log Security dimensionato a 4+ GB
[ ] PowerShell logging abilitato
[ ] Alerting su Event ID critici

PATCH E MANUTENZIONE
[ ] WSUS o WUfB configurato
[ ] Finestra di manutenzione definita
[ ] Patch critiche entro 14 giorni
[ ] Patch zero-day entro 72 ore
[ ] Baseline di sicurezza verificata periodicamente (trimestrale)

BACKUP E RECOVERY
[ ] Recovery key BitLocker verificata
[ ] System State backup per DC
[ ] Procedura di disaster recovery documentata e testata
[ ] Password krbtgt ruotata ogni 180 giorni (2 rotazioni consecutive)
```

## Esercizi

1. Spiegare il flusso di autenticazione Kerberos in AD: descrivere ogni passaggio dal logon dell'utente all'accesso a una risorsa di rete, indicando i componenti coinvolti (KDC, TGT, TGS, service ticket).
2. Configurare BitLocker su un volume dati in un lab, simulare la perdita del TPM (clear TPM dal BIOS), e recuperare il volume con la recovery key salvata in AD.
3. Un'azienda subisce un attacco Pass-the-Hash sui workstation del reparto contabilità. Descrivere l'attacco, spiegare perché Credential Guard lo previene, e proporre un piano di remediation immediato.
4. Progettare una checklist di hardening per un nuovo file server in una rete con Tier Model implementato. Includere: configurazione ASR rules, audit policy, logging, e restrizioni di accesso.

## Auto-valutazione

<details><summary>1. Qual è la differenza tra DACL e SACL?</summary>
DACL (Discretionary ACL) controlla chi può accedere a un oggetto e con quali permessi. SACL (System ACL) definisce quali operazioni vengono registrate nel Security Event Log (auditing). Riferimento: sezione «DACL e SACL».
</details>

<details><summary>2. Perché NTLM è da evitare e come si disabilita?</summary>
NTLM è vulnerabile a relay attack, pass-the-hash e non supporta mutual authentication. Si disabilita tramite GPO "Network security: Restrict NTLM" e monitorando gli Event ID 4624 con logon type NTLM prima di bloccare. Riferimento: sezione «NTLM — perché evitarlo».
</details>

<details><summary>3. Come funziona Credential Guard?</summary>
Credential Guard usa Virtualization Based Security (VBS) per isolare il processo LSASS in un contenitore protetto dall'hypervisor. Le credenziali derivate (hash NTLM, TGT Kerberos) non sono accessibili nemmeno con privilegi SYSTEM. Richiede UEFI Secure Boot, TPM 2.0, e virtualizzazione hardware. Riferimento: sezione «Credential Guard».
</details>

<details><summary>4. Cosa sono le ASR rules di Microsoft Defender?</summary>
Attack Surface Reduction rules sono regole che bloccano comportamenti comuni di malware: macro Office che lanciano processi, script offuscati, credential stealing da LSASS, esecuzione da cartelle email/USB. Si configurano via GPO o Intune. Riferimento: sezione «Defender ASR rules».
</details>

<details><summary>5. Qual è il ruolo del Mandatory Integrity Control (MIC)?</summary>
MIC assegna livelli di integrità (Untrusted, Low, Medium, High, System) a processi e oggetti. Un processo non può scrivere su oggetti con livello di integrità superiore (no write-up). Questo previene l'elevazione di privilegi da processi a bassa integrità (es. browser). Riferimento: sezione «Livelli di integrità».
</details>

<details><summary>6. Come si protegge la password krbtgt e perché servono 2 rotazioni consecutive?</summary>
L'account krbtgt firma tutti i TGT Kerberos. AD mantiene la password corrente e quella precedente per garantire continuità. Per invalidare tutti i TGT esistenti (es. dopo compromissione) servono 2 rotazioni consecutive, attendendo il tempo di replica tra le due. Riferimento: sezione «Kerberos» e checklist hardening.
</details>

<details><summary>7. Cosa deve contenere una Advanced Audit Policy efficace?</summary>
Deve coprire: Logon/Logoff (4624/4625), Account Management (4720/4726), Privilege Use (4672/4673), Object Access (4663), Policy Change (4719), e Process Creation (4688 con command line). I log devono essere dimensionati a 4+ GB e inoltrati a un SIEM. Riferimento: sezione «Logging e Monitoraggio».
</details>

## Letture primarie consigliate

- Microsoft Learn — Windows Security Documentation: <https://learn.microsoft.com/en-us/windows/security/> (consultato: 2026-05-23)
- Microsoft Learn — BitLocker Overview: <https://learn.microsoft.com/en-us/windows/security/operating-system-security/data-protection/bitlocker/> (consultato: 2026-05-23)
- Microsoft Learn — Credential Guard: <https://learn.microsoft.com/en-us/windows/security/identity-protection/credential-guard/> (consultato: 2026-05-23)
- Microsoft Learn — Attack Surface Reduction Rules: <https://learn.microsoft.com/en-us/defender-endpoint/attack-surface-reduction-rules-reference> (consultato: 2026-05-23)
- MITRE ATT&CK — Windows Techniques: <https://attack.mitre.org/matrices/enterprise/windows/> (consultato: 2026-05-23)

## Collegamenti incrociati

- [01-active-directory.md](01-active-directory.md) — Kerberos, NTLM e sicurezza AD
- [08-permessi-e-accesso.md](08-permessi-e-accesso.md) — NTFS permissions e ACL in dettaglio
- [24-windows-defender-endpoint-security.md](24-windows-defender-endpoint-security.md) — Defender for Endpoint
- [29-windows-server-hardening.md](29-windows-server-hardening.md) — Hardening server avanzato
- [28-pki-certificati-guida-completa.md](28-pki-certificati-guida-completa.md) — PKI e certificati per autenticazione

## Glossario locale

| Termine | Definizione |
|---------|-------------|
| SRM | Security Reference Monitor — componente kernel che verifica i permessi di accesso |
| LSA | Local Security Authority — processo che gestisce autenticazione e policy di sicurezza locali |
| SAM | Security Account Manager — database locale degli account (non-domain) |
| SID | Security Identifier — identificatore univoco per ogni principal di sicurezza (utente, gruppo, computer) |
| ACE | Access Control Entry — singola voce in una ACL che specifica permessi per un principal |
| VBS | Virtualization Based Security — isolamento hardware di processi critici tramite hypervisor |
| TPM | Trusted Platform Module — chip hardware per operazioni crittografiche e attestazione |
| ASR | Attack Surface Reduction — regole Defender che bloccano comportamenti tipici di malware |
| MIC | Mandatory Integrity Control — meccanismo di livelli di integrità che previene write-up |
| Sysmon | System Monitor — tool Sysinternals per logging avanzato di eventi di sistema e processo |
