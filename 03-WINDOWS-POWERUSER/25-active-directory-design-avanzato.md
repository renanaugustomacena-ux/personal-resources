# Active Directory Design Avanzato — Guida Approfondita

> **Modulo del corso:** Windows per ingegneri di sistema
> **Posizione nel percorso:** [00-SYLLABUS.md](00-SYLLABUS.md) → Modulo 25
> **Prerequisiti:** [01-active-directory.md](01-active-directory.md) (fondamenti AD, LDAP, Kerberos), [05-sicurezza-windows.md](05-sicurezza-windows.md) (hardening, audit), [21-group-policy-guida-completa.md](21-group-policy-guida-completa.md) (GPO design), [06-rete-windows.md](06-rete-windows.md) (DNS, networking)
> **Obiettivi di apprendimento:**
> 1. Progettare una topologia AD forest/domain scalabile scegliendo tra modelli single-forest, multi-domain e multi-forest in base ai requisiti di isolamento e compliance
> 2. Implementare il modello di tiering amministrativo (Tier 0/1/2) con OU structure, delega granulare e GPO inheritance
> 3. Ottimizzare la topologia di replica AD tramite site link, site link bridge, bridgehead server e scheduling della replica inter-site
> 4. Gestire i ruoli FSMO con consapevolezza del placement ottimale, delle procedure di trasferimento e seizure, e dell'impatto operativo della perdita di ciascun ruolo
> 5. Hardening di Active Directory con Protected Users, LAPS/Windows LAPS, gMSA, fine-grained password policies, Kerberos constrained delegation e RBCD
> 6. Identificare e mitigare le principali superfici di attacco AD: Kerberoasting, AS-REP Roasting, DCSync, DCShadow, Golden/Silver Ticket, Pass-the-Hash e AD CS abuse
> 7. Configurare Azure AD Connect (Entra Connect) con sync rules, filtering, PHS/PTA/Federation e staging mode
> 8. Pianificare capacity e monitorare la salute AD con dcdiag, repadmin, Event ID critici e performance counter
> **Tempo stimato:** lettura 90 min · lab 180 min
> **Livello:** proficient
> **Ultimo aggiornamento:** 2026-05-23
> **Versioni di riferimento:** Windows Server 2025, Active Directory functional level 2025, Entra Connect 2.x

## Mappa concettuale

```
                        ┌───────────────────────┐
                        │      FOREST           │
                        │  (security boundary)  │
                        └──────────┬────────────┘
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
      ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
      │  Root Domain │   │ Child Domain │   │ Child Domain │
      │  (empty root)│   │  corp.x.com  │   │  dev.x.com   │
      └──────┬───────┘   └──────┬───────┘   └──────────────┘
             │                  │
    ┌────────┴────────┐  ┌──────┴──────────────────┐
    ▼                 ▼  ▼                         ▼
┌────────┐    ┌────────┐ ┌────────────┐    ┌────────────┐
│ Schema │    │Domain  │ │    OU      │    │   Sites    │
│ Master │    │Naming  │ │  Hierarchy │    │ & Subnets  │
└────────┘    │ Master │ └─────┬──────┘    └─────┬──────┘
              └────────┘       │                 │
                    ┌──────────┼──────────┐      │
                    ▼          ▼          ▼      ▼
              ┌─────────┐┌─────────┐┌─────────┐┌──────────┐
              │ Tier 0  ││ Tier 1  ││ Tier 2  ││Replication│
              │ DC/AD   ││ Server  ││Workstat.││ Topology │
              └─────────┘└─────────┘└─────────┘└──────────┘
                    │          │          │          │
                    └──────────┼──────────┘          │
                               ▼                    ▼
                    ┌─────────────────┐   ┌──────────────┐
                    │   GPO / Delega  │   │  KCC / ISTG  │
                    │  AGDLP / FGPP   │   │ Bridgehead   │
                    └─────────────────┘   └──────────────┘
                               │
                    ┌──────────┼──────────┐
                    ▼          ▼          ▼
              ┌──────────┐┌─────────┐┌──────────┐
              │ Security ││  gMSA   ││  LAPS    │
              │Hardening ││ RBCD    ││Protected │
              │ FSMO     ││AdminSD  ││ Users    │
              └──────────┘└─────────┘└──────────┘
```

> **Modulo 25** · **Aggiornamento:** 2026-05-23

## Idee guida
1. **Forest/Domain/OU/Site planning prima di deploy.**
2. **Tier 0/1/2 admin model: separation of duties.**
3. **Read-only DC (RODC) per branch office.**
4. **Empty root forest per maximum isolation.**


## Indice
- [Panoramica](#panoramica)
- [Progettazione di Forest e Domini](#progettazione-di-forest-e-domini)
  - [Livelli Funzionali Forest e Domain](#livelli-funzionali-forest-e-domain)
  - [Schema Extensions — Best Practices e Versioning](#schema-extensions--best-practices-e-versioning)
- [Organizational Unit e Delega Amministrativa](#organizational-unit-e-delega-amministrativa)
  - [Read-Only Domain Controller (RODC)](#read-only-domain-controller-rodc)
- [Strategia di Gruppi: AGDLP e AGUDLP](#strategia-di-gruppi-agdlp-e-agudlp)
- [Fine-Grained Password Policies](#fine-grained-password-policies)
- [Siti AD e Topologia di Replica](#siti-ad-e-topologia-di-replica)
  - [Knowledge Consistency Checker (KCC)](#knowledge-consistency-checker-kcc)
  - [ISTG e Bridgehead Server](#istg-e-bridgehead-server)
  - [Site Link Bridge e Transitività](#site-link-bridge-e-transitività)
  - [Replica Urgente (Urgent Replication)](#replica-urgente-urgent-replication)
  - [Trasporti Inter-Site: IP vs SMTP](#trasporti-inter-site-ip-vs-smtp)
  - [Confronto: Replica Intra-Site vs Inter-Site](#confronto-replica-intra-site-vs-inter-site)
- [DFSR e Replica SYSVOL](#dfsr-e-replica-sysvol)
- [Schema Extensions](#schema-extensions)
  - [Deferred Index e searchFlags](#deferred-index-e-searchflags)
- [Tombstone Lifetime e AD Recycle Bin](#tombstone-lifetime-e-ad-recycle-bin)
- [Query LDAP Avanzate](#query-ldap-avanzate)
- [Trust Relationships — Approfondimento](#trust-relationships--approfondimento)
  - [Tipi di Trust](#tipi-di-trust)
  - [SID Filtering e Selective Authentication](#sid-filtering-e-selective-authentication)
  - [Gestione Trust con PowerShell](#gestione-trust-con-powershell)
- [FSMO Roles — Deep Dive](#fsmo-roles--deep-dive)
  - [Matrice di Placement Ottimale](#matrice-di-placement-ottimale)
  - [Trasferimento e Seizure dei Ruoli](#trasferimento-e-seizure-dei-ruoli)
  - [Impatto Operativo della Perdita di un Ruolo FSMO](#impatto-operativo-della-perdita-di-un-ruolo-fsmo)
- [AD Security Hardening](#ad-security-hardening)
  - [Protected Users Group](#protected-users-group)
  - [LAPS e Windows LAPS](#laps-e-windows-laps)
  - [Kerberos Constrained Delegation e RBCD](#kerberos-constrained-delegation-e-rbcd)
  - [Authentication Policies e Silos](#authentication-policies-e-silos)
  - [Credential Guard](#credential-guard)
- [Superficie di Attacco AD](#superficie-di-attacco-ad)
  - [Kerberoasting](#kerberoasting)
  - [AS-REP Roasting](#as-rep-roasting)
  - [DCSync e DCShadow](#dcsync-e-dcshadow)
  - [Golden Ticket e Silver Ticket](#golden-ticket-e-silver-ticket)
  - [Pass-the-Hash e Pass-the-Ticket](#pass-the-hash-e-pass-the-ticket)
  - [AD Certificate Services Abuse (ESC1-ESC8)](#ad-certificate-services-abuse-esc1-esc8)
- [Red Forest / ESAE Architecture](#red-forest--esae-architecture)
  - [Tier 0 Isolation](#tier-0-isolation)
  - [Privileged Access Workstations (PAW)](#privileged-access-workstations-paw)
  - [Jump Server e Credential Isolation](#jump-server-e-credential-isolation)
- [Monitoring e Health AD](#monitoring-e-health-ad)
  - [dcdiag — Deep Dive](#dcdiag--deep-dive)
  - [repadmin — Comandi Avanzati](#repadmin--comandi-avanzati)
  - [Event ID Critici](#event-id-critici)
  - [Performance Counter AD](#performance-counter-ad)
- [Azure AD Connect / Entra Connect](#azure-ad-connect--entra-connect)
  - [Architettura e Sync Rules](#architettura-e-sync-rules)
  - [Filtering e Scoping](#filtering-e-scoping)
  - [PHS vs PTA vs Federation](#phs-vs-pta-vs-federation)
  - [Seamless SSO e Staging Mode](#seamless-sso-e-staging-mode)
- [AD Migration](#ad-migration)
  - [ADMT e Cross-Forest Migration](#admt-e-cross-forest-migration)
  - [SID History e Trust Setup per Migrazione](#sid-history-e-trust-setup-per-migrazione)
  - [Domain Rename (rendom)](#domain-rename-rendom)
  - [Domain Consolidation](#domain-consolidation)
- [AD Backup e Recovery](#ad-backup-e-recovery)
  - [Manutenzione del Database AD (NTDS.DIT)](#manutenzione-del-database-ad-ntdsdit)
- [Capacity Planning e Ottimizzazione](#capacity-planning-e-ottimizzazione)
  - [Dimensionamento DC](#dimensionamento-dc)
  - [Ottimizzazione Query LDAP](#ottimizzazione-query-ldap)
  - [Placement del Global Catalog](#placement-del-global-catalog)
  - [Integrazione DNS](#integrazione-dns)
  - [Zone DNS AD-Integrated](#zone-dns-ad-integrated)
  - [Conditional Forwarders e Stub Zones](#conditional-forwarders-e-stub-zones)
  - [Split-Brain DNS](#split-brain-dns-split-horizon-dns)
  - [DNSSEC per Zone AD-Integrated](#dnssec-per-zone-ad-integrated)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Group Managed Service Accounts (gMSA)](#group-managed-service-accounts-gmsa)
- [AdminSDHolder e Protected Groups](#adminsdholder-e-protected-groups)
- [Esercizi](#esercizi)
- [Autovalutazione](#autovalutazione)
- [Letture](#letture)
- [Collegamento ad altri moduli](#collegamento-ad-altri-moduli)
- [Glossario](#glossario)

---

## Panoramica

Active Directory Domain Services (AD DS) è il servizio di directory fondamentale nelle infrastrutture Microsoft enterprise, responsabile dell'autenticazione, dell'autorizzazione e della gestione centralizzata di identità e risorse. Mentre la configurazione base di un dominio AD è relativamente accessibile, la progettazione di un'architettura AD scalabile, sicura e resiliente richiede una comprensione approfondita dei concetti avanzati: forest e domain design, topologia di replica, delega granulare, strategie di gruppo e meccanismi di recovery.

Una progettazione AD inadeguata può generare problemi di sicurezza (escalation di privilegi, lateral movement), problemi di prestazioni (replica inefficiente, query LDAP lente) e problemi operativi (impossibilità di delegare, complessità di gestione). Correggere errori di design dopo il deployment è costoso e spesso richiede migrazioni complesse.

Questa guida analizza i principi di progettazione avanzata di Active Directory, dalla struttura logica (forest, domini, OU) alla struttura fisica (siti, subnet, replica), dalle strategie di gestione delle identità (AGDLP, fine-grained password policies) ai meccanismi di protezione e recovery (tombstone, Recycle Bin), fornendo le competenze necessarie per architettare e mantenere infrastrutture AD enterprise-grade.

---

## Progettazione di Forest e Domini

### Il Forest come Confine di Sicurezza

Il forest è il confine di sicurezza assoluto in Active Directory. Tutti i domini all'interno di un forest condividono:
- Lo **schema** — Definizione di tutte le classi di oggetti e attributi
- Il **Global Catalog** — Replica parziale di tutti gli oggetti del forest
- La **Configuration partition** — Topologia di siti e servizi
- Un **trust transitivo bidirezionale** automatico tra tutti i domini

Il principio fondamentale è: **se non ti fidi completamente di un'entità, quella entità deve stare in un forest separato**. I domain admin di un qualsiasi dominio figlio possono potenzialmente compromettere l'intero forest attraverso tecniche come SID History injection o compromissione del trust.

```
Forest contoso.com
├── contoso.com (forest root domain)
│   ├── Schema Master, Domain Naming Master
│   ├── Enterprise Admins, Schema Admins
│   └── Domain Admins (root)
├── corp.contoso.com (child domain)
│   ├── PDC Emulator, RID Master, Infrastructure Master
│   └── Domain Admins (corp)
└── dev.contoso.com (child domain)
    └── Domain Admins (dev)

Trust automatico transitivo tra tutti i domini ←→
```

### Modelli di Design del Forest

**Single Forest, Single Domain (consigliato per la maggior parte delle organizzazioni):** L'approccio più semplice. Un forest con un unico dominio. La segmentazione viene gestita tramite OU e delega. Vantaggi: semplicità, costo ridotto, Global Catalog unico. Svantaggi: nessun isolamento tra unità organizzative.

**Single Forest, Multiple Domains:** Un forest root domain dedicato (spesso "vuoto") con domini figli regionali o funzionali. Utile quando servono namespace DNS separati o policy di password diverse a livello di dominio (prima dell'introduzione delle Fine-Grained Password Policies). L'uso di questo modello è diminuito significativamente con le FGPP.

**Multiple Forests:** Forest separati collegati da trust espliciti. Necessario quando servono schemi diversi, isolamento di sicurezza completo o compliance con normative che richiedono separazione dei dati (es. forest dedicato per l'ambiente SCADA/OT).

```powershell
# Verificare la struttura del forest
Get-ADForest | Select-Object Name, ForestMode, RootDomain, Domains, Sites,
    GlobalCatalogs, SchemaMaster, DomainNamingMaster

# Verificare il livello funzionale del dominio
Get-ADDomain | Select-Object Name, DomainMode, PDCEmulator, RIDMaster,
    InfrastructureMaster, DNSRoot, Forest

# Elencare tutti i trust
Get-ADTrust -Filter * | Select-Object Name, Direction, TrustType,
    IsTreeParent, IsTreeRoot, IntraForest
```

### Forest Root Domain Dedicato

In architetture multi-dominio, un approccio consigliato è creare un forest root domain "vuoto" che contiene solo gli account Enterprise Admin e Schema Admin, i domain controller del root domain e nessun altro oggetto. Questo riduce la superficie di attacco del forest root e semplifica la gestione della sicurezza.

### Livelli Funzionali Forest e Domain

I livelli funzionali determinano le feature AD disponibili. L'innalzamento è **irreversibile**.

| Livello Funzionale | Novità Principali |
|---|---|
| **Windows Server 2008** | Fine-Grained Password Policies, DFS-R per SYSVOL, AES Kerberos |
| **Windows Server 2008 R2** | AD Recycle Bin, Authentication Mechanism Assurance, gMSA |
| **Windows Server 2012** | KDC supporta compound authentication e claims |
| **Windows Server 2012 R2** | Protected Users, Authentication Policies/Silos, Domain Controller: Refuse machine account password changes |
| **Windows Server 2016** | Privileged Access Management (PAM), Windows Hello for Business |
| **Windows Server 2025** | Windows LAPS integrato, TLS 1.3 per LDAP, schema 90+ |

```powershell
# Verificare il livello funzionale corrente
Get-ADForest | Select-Object Name, ForestMode
Get-ADDomain | Select-Object Name, DomainMode

# Innalzare il livello funzionale del dominio (IRREVERSIBILE)
# Prerequisito: TUTTI i DC del dominio devono essere al livello richiesto o superiore
Set-ADDomainMode -Identity "contoso.com" -DomainMode Windows2016Domain -Confirm:$false

# Innalzare il livello funzionale del forest (IRREVERSIBILE)
# Prerequisito: TUTTI i domini del forest devono essere al livello richiesto o superiore
Set-ADForestMode -Identity "contoso.com" -ForestMode Windows2016Forest -Confirm:$false

# Verificare che tutti i DC siano pronti per l'innalzamento
Get-ADDomainController -Filter * |
    Select-Object Name, OperatingSystem, OperatingSystemVersion |
    Format-Table -AutoSize
```

### Schema Extensions — Best Practices e Versioning

Lo schema AD è condiviso da tutti i domini nel forest. Le modifiche sono **irreversibili** (attributi e classi possono essere disattivati ma non eliminati). Ogni estensione si propaga a tutti i DC.

```powershell
# Verificare la versione corrente dello schema
Get-ADObject (Get-ADRootDSE).schemaNamingContext -Property objectVersion |
    Select-Object objectVersion

# Versioni schema note:
# 87 = Windows Server 2016/2019
# 88 = Windows Server 2022
# 90 = Windows Server 2025
# 15332 = Exchange 2016/2019 CU
# 17003 = Exchange 2019 CU14+

# Best practice prima di estendere lo schema:
# 1. Testare in un ambiente di lab isolato
# 2. Avere un backup System State recente di tutti i DC
# 3. Documentare gli OID e i nomi degli attributi custom
# 4. Usare un prefix OID registrato (non inventare OID random)
# 5. Eseguire adprep come Schema Admin da un DC con il ruolo Schema Master
# 6. Verificare la replica dello schema su tutti i DC dopo l'estensione

# Dopo l'estensione, verificare la propagazione
Get-ADDomainController -Filter * | ForEach-Object {
    $version = Get-ADObject (Get-ADRootDSE -Server $_.HostName).schemaNamingContext `
        -Property objectVersion -Server $_.HostName
    [PSCustomObject]@{
        DC = $_.Name
        SchemaVersion = $version.objectVersion
    }
} | Format-Table -AutoSize
```

---

## Organizational Unit e Delega Amministrativa

### Principi di Design delle OU

Le OU servono a due scopi principali: **applicazione di Group Policy** e **delega amministrativa**. La struttura delle OU dovrebbe riflettere il modello di delega dell'organizzazione, non necessariamente l'organigramma aziendale.

```
DC=contoso,DC=com
├── OU=Admin              # Account e gruppi amministrativi
│   ├── OU=Tier0          # Domain Admins, DC admins
│   ├── OU=Tier1          # Server admins
│   └── OU=Tier2          # Workstation admins, helpdesk
├── OU=Utenti
│   ├── OU=Sede-Roma
│   ├── OU=Sede-Milano
│   └── OU=Sede-Napoli
├── OU=Computer
│   ├── OU=Workstations
│   │   ├── OU=Sede-Roma
│   │   ├── OU=Sede-Milano
│   │   └── OU=Sede-Napoli
│   ├── OU=Server
│   │   ├── OU=FileServer
│   │   ├── OU=AppServer
│   │   └── OU=Database
│   └── OU=Kiosk
├── OU=Gruppi
│   ├── OU=Security
│   ├── OU=Distribution
│   └── OU=RoleGroups
├── OU=ServiceAccounts
│   ├── OU=ManagedSA      # gMSA
│   └── OU=StandardSA
└── OU=Disabled            # Account disabilitati (retention)
```

### Delega con Precisione

```powershell
# Delegare la gestione degli utenti in una OU specifica
$ou = "OU=Sede-Roma,OU=Utenti,DC=contoso,DC=com"
$group = "GRP-IT-Roma-UserAdmin"
$groupSid = (Get-ADGroup $group).SID

# Importare il modulo per la gestione degli ACL AD
Import-Module ActiveDirectory

# Ottenere l'ACL corrente
$acl = Get-Acl "AD:\$ou"

# Aggiungere il permesso di creare/eliminare utenti
$identity = [System.Security.Principal.IdentityReference]$groupSid
$adRights = [System.DirectoryServices.ActiveDirectoryRights]"CreateChild,DeleteChild"
$type = [System.Security.AccessControl.AccessControlType]"Allow"
$userGuid = [guid]"bf967aba-0de6-11d0-a285-00aa003049e2"  # GUID della classe User

$rule = New-Object System.DirectoryServices.ActiveDirectoryAccessRule(
    $identity, $adRights, $type, $userGuid
)
$acl.AddAccessRule($rule)

# Aggiungere il permesso di modificare proprietà degli utenti
$adRights = [System.DirectoryServices.ActiveDirectoryRights]"WriteProperty"
$rule = New-Object System.DirectoryServices.ActiveDirectoryAccessRule(
    $identity, $adRights, $type, [guid]::Empty, "Descendents", $userGuid
)
$acl.AddAccessRule($rule)

# Applicare l'ACL
Set-Acl "AD:\$ou" $acl

# Delegare il reset password
$resetPwdGuid = [guid]"00299570-246d-11d0-a768-00aa006e0529"  # Reset Password
$rule = New-Object System.DirectoryServices.ActiveDirectoryAccessRule(
    $identity,
    [System.DirectoryServices.ActiveDirectoryRights]"ExtendedRight",
    $type,
    $resetPwdGuid,
    "Descendents",
    $userGuid
)
$acl.AddAccessRule($rule)
Set-Acl "AD:\$ou" $acl

# Verificare le deleghe su una OU
(Get-Acl "AD:\$ou").Access |
    Where-Object { $_.IdentityReference -notlike "NT AUTHORITY\*" -and
                   $_.IdentityReference -notlike "BUILTIN\*" -and
                   $_.IdentityReference -notlike "S-1-5-*" } |
    Select-Object IdentityReference, ActiveDirectoryRights, ObjectType, AccessControlType |
    Format-Table -AutoSize
```

### Protezione degli Oggetti dall'Eliminazione Accidentale

```powershell
# Abilitare la protezione su tutte le OU esistenti
Get-ADOrganizationalUnit -Filter * |
    Set-ADObject -ProtectedFromAccidentalDeletion $true

# Verificare quali OU NON sono protette
Get-ADOrganizationalUnit -Filter * -Properties ProtectedFromAccidentalDeletion |
    Where-Object { -not $_.ProtectedFromAccidentalDeletion } |
    Select-Object Name, DistinguishedName

# Proteggere anche i gruppi critici
"Domain Admins","Enterprise Admins","Schema Admins","Protected Users" |
    ForEach-Object {
        Set-ADObject (Get-ADGroup $_) -ProtectedFromAccidentalDeletion $true
    }
```

### Read-Only Domain Controller (RODC)

I RODC sono domain controller che mantengono una copia in sola lettura del database AD. Sono progettati per siti remoti con scarsa sicurezza fisica o limitata connettività di rete.

**Caratteristiche RODC:**
- Database AD in sola lettura (nessun oggetto creato/modificato localmente)
- Password caching selettivo: solo gli account configurati nella Password Replication Policy (PRP)
- Separazione dei ruoli: un admin locale può gestire il server senza avere accesso a tutto il dominio
- Replica unidirezionale: il RODC riceve le modifiche ma non le invia mai

```powershell
# Verificare i RODC nel dominio
Get-ADDomainController -Filter 'IsReadOnly -eq $true' |
    Select-Object Name, Site, IPv4Address, IsReadOnly

# Configurare la Password Replication Policy (PRP) di un RODC
# Aggiungere un gruppo i cui membri avranno le password cached
Add-ADDomainControllerPasswordReplicationPolicy -Identity "RODC-NAPOLI" `
    -AllowedList "GG-Utenti-Napoli"

# Verificare la PRP corrente
Get-ADDomainControllerPasswordReplicationPolicy -Identity "RODC-NAPOLI" -Allowed |
    Select-Object Name, ObjectClass
Get-ADDomainControllerPasswordReplicationPolicy -Identity "RODC-NAPOLI" -Denied |
    Select-Object Name, ObjectClass

# Verificare quali password sono effettivamente cached
Get-ADDomainControllerPasswordReplicationPolicyUsage -Identity "RODC-NAPOLI" `
    -RevealedAccounts | Select-Object Name, ObjectClass

# Pre-popolare la cache password (es. prima di un maintenance del link WAN)
Get-ADGroupMember "GG-Utenti-Napoli" |
    ForEach-Object { Sync-ADObject -Object $_.DistinguishedName -Source "DC01" -Destination "RODC-NAPOLI" }
```

**Regole di design RODC:**
- Non assegnare mai ruoli FSMO a un RODC
- Non installare CA o Exchange su un RODC
- Includere nella PRP (Allowed) solo gli utenti del sito locale
- Escludere dalla PRP (Denied) tutti gli account privilegiati (Tier 0, service account critici)
- Configurare un admin locale (RODC Admin) per la gestione del server senza Domain Admin

#### Filtered Attribute Set (FAS)

Il Filtered Attribute Set è l'elenco degli attributi che **non vengono mai replicati** su un RODC, indipendentemente dal contenuto del database. Serve a impedire che dati sensibili (credenziali applicative, attributi custom con segreti) raggiungano siti fisicamente insicuri.

Per default il FAS include gli attributi marcati come `confidential` (bit 128 di `searchFlags`) e quelli specificamente marcati come `RODC filtered`. Attributi custom possono essere aggiunti al FAS, ma gli attributi di sistema critici (`objectSid`, `sAMAccountName`, `userAccountControl`, attributi della classe `top`) non possono essere filtrati.

```powershell
# Elencare gli attributi nel Filtered Attribute Set
Get-ADObject -SearchBase (Get-ADRootDSE).schemaNamingContext `
    -Filter 'searchFlags -band 512' -Properties lDAPDisplayName, searchFlags |
    Select-Object lDAPDisplayName, searchFlags |
    Format-Table -AutoSize
# searchFlags bit 9 (valore 512) = attributo nel FAS

# Aggiungere un attributo custom al FAS (richiede Schema Admin)
Set-ADObject "CN=contoso-SecretToken,$(
    (Get-ADRootDSE).schemaNamingContext)" `
    -Replace @{searchFlags = 513}  # 1 (indexed) + 512 (RODC filtered)
```

#### RODC Staging (Installazione Staged)

Il deployment staged di un RODC consente di pre-creare l'account computer del RODC in AD e di delegarne l'installazione a personale IT locale senza concedere permessi di Domain Admin.

```powershell
# Fase 1 — Amministratore di dominio pre-crea l'account RODC
Add-ADDSReadOnlyDomainControllerAccount `
    -DomainControllerAccountName "RODC-PALERMO" `
    -DomainName "contoso.com" `
    -SiteName "Palermo-Branch" `
    -DelegatedAdministratorAccountName "CONTOSO\admin-palermo" `
    -AllowPasswordReplicationAccountName "GG-Utenti-Palermo" `
    -DenyPasswordReplicationAccountName "GG-Tier0-Admins","GG-Service-Accounts-Critical"

# Fase 2 — L'admin locale esegue l'installazione sul server remoto
# (non servono credenziali Domain Admin — solo l'account delegato)
# Install-ADDSDomainController -DomainName "contoso.com" `
#     -UseExistingAccount -SafeModeAdministratorPassword (Read-Host -AsSecureString) `
#     -Credential (Get-Credential CONTOSO\admin-palermo)

# Verificare lo stato dell'account RODC pre-creato
Get-ADComputer "RODC-PALERMO" -Properties managedBy, msDS-RevealedDSAs |
    Select-Object Name, Enabled, managedBy
```

#### Risposta alla Compromissione di un RODC

Se un RODC viene compromesso (furto fisico, accesso non autorizzato), la procedura di risposta è meno critica rispetto a un DC scrivibile grazie al caching selettivo e alla replica unidirezionale.

**Procedura di risposta:**

1. **Identificare le password cached:** Verificare quali account avevano le credenziali replicate sul RODC compromesso. Solo quelle password devono essere considerate compromesse.
2. **Reset delle password:** Resettare le password di tutti gli account nella Revealed list.
3. **Reset della password krbtgt del RODC:** Ogni RODC ha il proprio account `krbtgt_XXXXX` separato dal `krbtgt` del dominio. Resettare solo quello.
4. **Rimuovere l'account computer del RODC** dal dominio tramite metadata cleanup.
5. **Non riportare mai online** il RODC compromesso senza reinstallazione completa.

```powershell
# 1. Identificare gli account con password cached sul RODC compromesso
Get-ADDomainControllerPasswordReplicationPolicyUsage -Identity "RODC-PALERMO" `
    -RevealedAccounts |
    Select-Object Name, SamAccountName, ObjectClass |
    Format-Table -AutoSize

# 2. Resettare le password degli account compromessi
Get-ADDomainControllerPasswordReplicationPolicyUsage -Identity "RODC-PALERMO" `
    -RevealedAccounts |
    Where-Object { $_.ObjectClass -eq 'user' } |
    ForEach-Object {
        Set-ADAccountPassword -Identity $_.SamAccountName `
            -Reset -NewPassword (ConvertTo-SecureString "TempP@ss$(Get-Random)" -AsPlainText -Force)
        Write-Output "Reset password: $($_.SamAccountName)"
    }

# 3. Identificare e resettare il krbtgt del RODC (ogni RODC ha il proprio)
Get-ADUser -Filter 'Name -like "krbtgt_*"' -Properties Description |
    Where-Object { $_.Description -like "*RODC-PALERMO*" } |
    Select-Object Name, Description

# 4. Rimuovere l'account computer del RODC dal dominio
# ntdsutil > metadata cleanup > remove selected server

# 5. Rimuovere i record DNS del RODC
Get-DnsServerResourceRecord -ZoneName "contoso.com" -Name "RODC-PALERMO" |
    Remove-DnsServerResourceRecord -ZoneName "contoso.com" -Force
```

---

## Strategia di Gruppi: AGDLP e AGUDLP

### AGDLP

AGDLP è la best practice Microsoft per la gestione delle autorizzazioni:

- **A**ccount → membro di
- **G**lobal Group → membro di
- **D**omain **L**ocal Group → assegnato a
- **P**ermission (sulla risorsa)

```
Utente: Mario Rossi (Account)
    ↓ è membro di
GG-Finance (Global Group - raggruppa utenti per ruolo)
    ↓ è membro di
DL-Share-Finance-ReadWrite (Domain Local Group - definisce il permesso)
    ↓ ha il permesso
NTFS Read/Write su \\fileserver\finance$
```

### AGUDLP

AGUDLP estende il modello per ambienti multi-dominio:

- **A**ccount → membro di
- **G**lobal Group (nel dominio dell'utente) → membro di
- **U**niversal Group (nel forest) → membro di
- **D**omain **L**ocal Group (nel dominio della risorsa) → assegnato a
- **P**ermission

```powershell
# Implementare AGDLP per una share finanziaria

# 1. Creare il Global Group (raggruppa utenti per ruolo/reparto)
New-ADGroup -Name "GG-Finance-Team" -GroupScope Global `
    -GroupCategory Security -Path "OU=Security,OU=Gruppi,DC=contoso,DC=com" `
    -Description "Team del dipartimento Finance"

# 2. Aggiungere gli utenti al Global Group
Add-ADGroupMember -Identity "GG-Finance-Team" -Members "mario.rossi","laura.bianchi"

# 3. Creare i Domain Local Group (uno per livello di accesso)
New-ADGroup -Name "DL-Share-Finance-Read" -GroupScope DomainLocal `
    -GroupCategory Security -Path "OU=Security,OU=Gruppi,DC=contoso,DC=com" `
    -Description "Accesso in lettura alla share Finance"

New-ADGroup -Name "DL-Share-Finance-ReadWrite" -GroupScope DomainLocal `
    -GroupCategory Security -Path "OU=Security,OU=Gruppi,DC=contoso,DC=com" `
    -Description "Accesso in lettura/scrittura alla share Finance"

# 4. Annidare il Global Group nel Domain Local Group
Add-ADGroupMember -Identity "DL-Share-Finance-ReadWrite" -Members "GG-Finance-Team"

# 5. Assegnare il permesso NTFS al Domain Local Group
$acl = Get-Acl "D:\Shares\Finance"
$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "CONTOSO\DL-Share-Finance-ReadWrite",
    "Modify",
    "ContainerInherit,ObjectInherit",
    "None",
    "Allow"
)
$acl.AddAccessRule($rule)
Set-Acl "D:\Shares\Finance" $acl
```

Vantaggi di AGDLP:
- **Separazione dei concetti**: chi sono gli utenti (GG) vs cosa possono fare (DL)
- **Scalabilità**: aggiungere un nuovo utente richiede solo l'aggiunta al GG
- **Audit semplificato**: i DL group mostrano immediatamente chi ha accesso a cosa
- **Multi-dominio**: i GG possono essere annidati in DL di domini diversi

---

## Fine-Grained Password Policies

Le Fine-Grained Password Policies (FGPP), introdotte in Windows Server 2008 (livello funzionale dominio 2008+), permettono di definire policy di password diverse per gruppi specifici all'interno dello stesso dominio, superando il limite della singola password policy per dominio.

### Password Settings Object (PSO)

```powershell
# Creare una FGPP per gli amministratori (più restrittiva)
New-ADFineGrainedPasswordPolicy -Name "PSO-Admins-Strict" `
    -Precedence 10 `
    -ComplexityEnabled $true `
    -LockoutDuration "00:30:00" `
    -LockoutObservationWindow "00:30:00" `
    -LockoutThreshold 3 `
    -MaxPasswordAge "30.00:00:00" `
    -MinPasswordAge "1.00:00:00" `
    -MinPasswordLength 16 `
    -PasswordHistoryCount 24 `
    -ReversibleEncryptionEnabled $false `
    -Description "Password policy rigorosa per account amministrativi"

# Creare una FGPP per gli utenti standard
New-ADFineGrainedPasswordPolicy -Name "PSO-Users-Standard" `
    -Precedence 20 `
    -ComplexityEnabled $true `
    -LockoutDuration "00:15:00" `
    -LockoutObservationWindow "00:15:00" `
    -LockoutThreshold 5 `
    -MaxPasswordAge "90.00:00:00" `
    -MinPasswordAge "1.00:00:00" `
    -MinPasswordLength 12 `
    -PasswordHistoryCount 12 `
    -ReversibleEncryptionEnabled $false

# Creare una FGPP per i service account (password molto lunghe, nessuna scadenza)
New-ADFineGrainedPasswordPolicy -Name "PSO-ServiceAccounts" `
    -Precedence 15 `
    -ComplexityEnabled $true `
    -LockoutThreshold 0 `
    -MaxPasswordAge "0.00:00:00" `
    -MinPasswordLength 30 `
    -PasswordHistoryCount 24 `
    -ReversibleEncryptionEnabled $false

# Applicare le FGPP ai gruppi
Add-ADFineGrainedPasswordPolicySubject -Identity "PSO-Admins-Strict" `
    -Subjects "GG-Domain-Admins", "GG-Enterprise-Admins"
Add-ADFineGrainedPasswordPolicySubject -Identity "PSO-Users-Standard" `
    -Subjects "GG-All-Users"
Add-ADFineGrainedPasswordPolicySubject -Identity "PSO-ServiceAccounts" `
    -Subjects "GG-Service-Accounts"

# Verificare quale FGPP si applica a un utente specifico
Get-ADUserResultantPasswordPolicy -Identity "mario.rossi"

# Elencare tutte le FGPP
Get-ADFineGrainedPasswordPolicy -Filter * | Select-Object Name, Precedence,
    MinPasswordLength, MaxPasswordAge, LockoutThreshold,
    @{N='AppliedTo';E={(Get-ADFineGrainedPasswordPolicySubject -Identity $_.Name).Name -join ", "}} |
    Format-Table -AutoSize
```

### Regole di Precedenza

Quando un utente è soggetto a più FGPP (tramite membership in più gruppi), viene applicata la FGPP con il **valore di Precedence più basso** (1 = massima priorità). Se la precedenza è uguale, vince il PSO con il GUID più basso (comportamento deterministico ma non intuitivo — evitare duplicati di precedenza).

---

## Siti AD e Topologia di Replica

### Concetti

I siti in Active Directory rappresentano raggruppamenti fisici di computer collegati da connessioni di rete ad alta velocità. I siti controllano:

1. **Replica tra domain controller** — Replica intra-site (immediata, notifica-based) vs inter-site (schedulata, compressa)
2. **Localizzazione dei servizi** — I client preferiscono autenticarsi con DC nello stesso sito
3. **DFS target selection** — I client accedono al target DFS più vicino nel loro sito

```powershell
# Creare un sito
New-ADReplicationSite -Name "Roma-DC1" -Description "Datacenter primario Roma"

# Creare una subnet e associarla al sito
New-ADReplicationSubnet -Name "10.0.1.0/24" -Site "Roma-DC1" -Description "VLAN Server Roma"
New-ADReplicationSubnet -Name "10.0.2.0/24" -Site "Roma-DC1" -Description "VLAN Client Roma"

# Creare un site link (connessione logica tra siti)
New-ADReplicationSiteLink -Name "Roma-Milano" `
    -SitesIncluded "Roma-DC1","Milano-DC1" `
    -Cost 100 `
    -ReplicationFrequencyInMinutes 15 `
    -InterSiteTransportProtocol IP

# Configurare la schedule di replica su un site link
Set-ADReplicationSiteLink -Identity "Roma-Milano" `
    -ReplicationFrequencyInMinutes 15 `
    -Description "Link WAN Roma-Milano 100Mbps"

# Verificare la topologia di replica
Get-ADReplicationSite -Filter * | Select-Object Name, Description
Get-ADReplicationSubnet -Filter * | Select-Object Name, Site, Description
Get-ADReplicationSiteLink -Filter * | Select-Object Name, Cost,
    ReplicationFrequencyInMinutes, SitesIncluded

# Verificare lo stato della replica
Get-ADReplicationPartnerMetadata -Target "DC01" | Select-Object Server, Partner,
    PartnerType, LastReplicationSuccess, LastReplicationResult,
    ConsecutiveReplicationFailures | Format-Table -AutoSize

# Repadmin per diagnostica dettagliata
repadmin /replsummary
repadmin /showrepl DC01
repadmin /queue DC01
```

### Knowledge Consistency Checker (KCC)

Il KCC è il processo automatico che genera la topologia di replica tra i domain controller. Per la replica intra-site, il KCC crea una topologia ad anello bidirezionale con massimo 3 hop tra qualsiasi coppia di DC. Per la replica inter-site, il KCC utilizza i site link per determinare il percorso ottimale.

```
Sito Roma (3 DC):                  Sito Milano (2 DC):
DC01 ←→ DC02 ←→ DC03              DC04 ←→ DC05
  └──────────→ DC03                  │
           (ring topology)           │
                                     │
        Site Link Roma-Milano        │
        DC03 ←──────────────────→ DC04
        (bridgehead servers)
```

### ISTG e Bridgehead Server

L'**ISTG (Inter-Site Topology Generator)** è il DC in ciascun sito designato a calcolare la topologia di replica inter-site. L'ISTG seleziona automaticamente i **bridgehead server** — i DC che gestiscono la replica tra siti.

```powershell
# Identificare l'ISTG di ogni sito
Get-ADReplicationSite -Filter * -Properties InterSiteTopologyGenerator |
    Select-Object Name,
    @{N='ISTG';E={($_.InterSiteTopologyGenerator -split ',')[1] -replace 'CN='}}

# Identificare i bridgehead server preferiti (se configurati manualmente)
Get-ADObject -Filter 'objectClass -eq "server"' `
    -SearchBase "CN=Sites,$(Get-ADRootDSE | Select-Object -ExpandProperty configurationNamingContext)" `
    -Properties bridgeheadTransportList |
    Where-Object { $_.bridgeheadTransportList } |
    Select-Object Name, @{N='Transport';E={$_.bridgeheadTransportList}}

# Configurare un bridgehead server preferito (manuale)
# ATTENZIONE: se il bridgehead server preferito va offline,
# la replica inter-site per quel sito si ferma completamente
# (a differenza della selezione automatica, che failover su un altro DC)
Set-ADObject "CN=DC01,CN=Servers,CN=Roma-DC1,CN=Sites,$(
    (Get-ADRootDSE).configurationNamingContext)" `
    -Add @{bridgeheadTransportList = "CN=IP,CN=Inter-Site Transports,CN=Sites,$(
    (Get-ADRootDSE).configurationNamingContext)"}
```

### Site Link Bridge e Transitività

Per default, tutti i site link sono **transitivi**: se il Sito A è collegato al Sito B tramite un site link, e il Sito B al Sito C tramite un altro, il KCC può instradare la replica da A a C attraverso B.

**Site Link Bridge:** Raggruppa esplicitamente i site link per controllare la transitività. Necessario solo quando la transitività automatica è disabilitata (raro, usato in topologie hub-and-spoke strette).

```powershell
# Verificare se la transitività dei site link è abilitata (default)
Get-ADReplicationSiteLink -Filter * -Properties options |
    Select-Object Name, Cost, ReplicationFrequencyInMinutes,
    @{N='Transitivity';E={if ($_.options -band 1) {'Disabled'} else {'Enabled'}}}

# Creare un site link bridge (solo se transitività disabilitata)
New-ADReplicationSiteLinkBridge -Name "Bridge-Roma-Milano-Napoli" `
    -SiteLinksIncluded "Roma-Milano","Milano-Napoli"
```

### Replica Urgente (Urgent Replication)

Alcune modifiche AD vengono replicate immediatamente (intra-site), senza attendere il ciclo normale. Le modifiche che triggerano la replica urgente:

- Cambio password utente
- Account lockout
- Modifica del secret LSA
- Modifica del RID Manager

```powershell
# La replica urgente è automatica per queste operazioni.
# Per la replica inter-site, la "notifica urgente" può essere abilitata:
Set-ADReplicationSiteLink "Roma-Milano" `
    -Replace @{options = 1}  # bit 0 = URGENT_REPLICATION_NOTIFICATION_ENABLED

# Verificare se la notifica urgente è abilitata sui site link
Get-ADReplicationSiteLink -Filter * -Properties options |
    Select-Object Name,
    @{N='UrgentNotification';E={if ($_.options -band 1) {'Yes'} else {'No'}}}
```

### Trasporti Inter-Site: IP vs SMTP

La replica inter-site può utilizzare due protocolli di trasporto. **IP (RPC over IP)** è il default e il più utilizzato; **SMTP** è un'alternativa legacy per scenari con connettività intermittente o non affidabile, ma presenta limitazioni significative.

| Caratteristica | IP (RPC over IP) | SMTP |
|---|---|---|
| **Partizioni supportate** | Tutte (Domain, Schema, Configuration, Application) | Solo Schema, Configuration, Application — **NON supporta la partizione Domain** |
| **Compressione** | Sì (automatica per replica inter-site) | Sì |
| **Scheduling** | Configurabile tramite site link schedule | Configurabile |
| **Requisiti infrastrutturali** | Connettività TCP/IP tra i DC | Enterprise CA per firmare i messaggi SMTP |
| **Firewall** | Porte RPC dinamiche (o port mapping statico) | Porta 25 (SMTP) |
| **Caso d'uso tipico** | Praticamente tutti gli scenari moderni | Storicamente usato per link WAN molto lenti o instabili |
| **Stato attuale** | Standard e raccomandato | **Deprecato** — sconsigliato per nuove implementazioni |

> **Nota operativa:** Poiché il trasporto SMTP non supporta la partizione Domain, non può essere usato per la replica tra DC dello stesso dominio in siti diversi. È utilizzabile solo per partizioni Configuration, Schema e Application in scenari multi-dominio. In pratica, il trasporto IP è l'unica scelta in quasi tutti gli ambienti moderni.
>
> Riferimento: [Active Directory Replication Concepts](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/replication/active-directory-replication-concepts) — consultato: 2026-05-23

### Confronto: Replica Intra-Site vs Inter-Site

| Aspetto | Intra-Site | Inter-Site |
|---|---|---|
| **Trigger** | Change notification (entro ~15 secondi dalla modifica) | Schedulata in base alla frequenza del site link (default 180 min) |
| **Compressione** | No (si assume banda locale abbondante) | Sì (~85-90% di compressione, risparmia banda WAN) |
| **Change notification** | Attivo per default | Disattivo per default (abilitabile tramite bit 1 su site link `options`) |
| **Topologia** | Anello bidirezionale (ring) con shortcut se >7 DC | Albero minimo tra siti tramite bridgehead server |
| **Protocollo** | RPC over IP | RPC over IP (o SMTP per partizioni non-Domain) |
| **Latenza tipica** | Secondi | Minuti-ore (dipende da schedule e frequenza) |
| **Generatore topologia** | KCC locale per ogni DC | ISTG del sito seleziona i bridgehead e genera la topologia inter-site |

```powershell
# Abilitare change notification su un site link inter-site
# (riduce la latenza di replica, ma aumenta il traffico WAN)
# bit 1 = USE_NOTIFY (abilita change notification)
# bit 0 = URGENT_REPLICATION per inter-site
$siteLink = Get-ADReplicationSiteLink "Roma-Milano" -Properties options
$currentOptions = if ($siteLink.options) { $siteLink.options } else { 0 }
$newOptions = $currentOptions -bor 0x2   # bit 1 = USE_NOTIFY
Set-ADReplicationSiteLink "Roma-Milano" -Replace @{options = $newOptions}
Write-Output "Opzioni aggiornate: $newOptions (Change notification abilitato)"

# Verificare la configurazione corrente di tutti i site link
Get-ADReplicationSiteLink -Filter * -Properties options |
    Select-Object Name, Cost, ReplicationFrequencyInMinutes,
    @{N='ChangeNotification';E={if ($_.options -band 2) {'Enabled'} else {'Disabled'}}},
    @{N='UrgentReplication';E={if ($_.options -band 1) {'Enabled'} else {'Disabled'}}},
    @{N='Transport';E={'IP'}} | Format-Table -AutoSize

# Verificare il trasporto disponibile per ciascun sito
Get-ADObject -Filter 'objectClass -eq "interSiteTransport"' `
    -SearchBase "CN=Inter-Site Transports,CN=Sites,$((Get-ADRootDSE).configurationNamingContext)" |
    Select-Object Name, DistinguishedName
```

---

## DFSR e Replica SYSVOL

### DFSR (Distributed File System Replication)

DFSR è il motore di replica utilizzato per SYSVOL (e per le cartelle DFS Namespace). Ha sostituito FRS (File Replication Service) a partire da Windows Server 2008.

```powershell
# Verificare il tipo di replica SYSVOL
dfsrmig /getglobalstate
# State 0 = Start (FRS), State 1 = Prepared, State 2 = Redirected, State 3 = Eliminated (DFSR)

# Migrare da FRS a DFSR (se ancora su FRS)
dfsrmig /setglobalstate 1  # Prepared
# Attendere la replica e verificare
dfsrmig /getmigrationstate
dfsrmig /setglobalstate 2  # Redirected
dfsrmig /setglobalstate 3  # Eliminated

# Monitorare lo stato DFSR
Get-DfsReplicationGroup | Select-Object GroupName, Description
Get-DfsrMember | Select-Object GroupName, ComputerName, DomainName

# Report diagnostico DFSR
$report = Get-DfsrBacklog -SourceComputerName "DC01" -DestinationComputerName "DC02" `
    -GroupName "Domain System Volume"
Write-Output "File in backlog: $($report.Count)"

# Report di salute DFSR
Write-DfsrHealthReport -GroupName "Domain System Volume" `
    -ReferenceComputerName "DC01" -Path "C:\Reports"
```

### Risoluzione Conflitti SYSVOL

DFSR utilizza un algoritmo "last writer wins" per risolvere i conflitti. I file in conflitto vengono spostati nella cartella `ConflictAndDeleted` con un limite di dimensione configurabile.

```powershell
# Verificare la dimensione della cartella ConflictAndDeleted
$conflictPath = "C:\System Volume Information\DFSR\Private\ConflictAndDeletedManifest.xml"
# Analizzare via DFSR Management Console o:
Get-DfsrState -ComputerName "DC01" | Select-Object FileName, UpdateState, Inbound

# Forzare una replica autoritativa di SYSVOL (EMERGENZA)
# 1. Sul DC autoritativo: impostare il flag D4 nel registry
# HKLM\System\CurrentControlSet\Services\DFSR\Parameters\Sysvols\Migrating Sysvols\Local Settings\DomainName\domainDN
# Valore: "Enabled" = 1 (autoritativo)

# 2. Sugli altri DC: impostare D2
# Valore: "Enabled" = 0 (non autoritativo)
```

---

## Schema Extensions

Lo schema di Active Directory definisce le classi di oggetti (User, Computer, Group) e i loro attributi (sAMAccountName, mail, telephoneNumber). Lo schema è globale per l'intero forest e le modifiche sono irreversibili (gli attributi possono essere disattivati ma non eliminati).

```powershell
# Verificare la versione dello schema
Get-ADObject (Get-ADRootDSE).schemaNamingContext -Property objectVersion |
    Select-Object objectVersion

# Versioni schema comuni:
# 87 = Windows Server 2016/2019
# 88 = Windows Server 2022
# 47 = Exchange 2010
# 15332 = Exchange 2016/2019

# Elencare le estensioni schema recenti
Get-ADObject -SearchBase (Get-ADRootDSE).schemaNamingContext `
    -Filter * -Properties whenCreated, name |
    Sort-Object whenCreated -Descending | Select-Object -First 20 Name, whenCreated

# Verificare il Schema Master
Get-ADForest | Select-Object SchemaMaster

# Registrare lo schema snap-in per MMC
regsvr32 schmmgmt.dll
# Poi aprire MMC → aggiungi snap-in → Active Directory Schema
```

### Estensione Schema Personalizzata

```powershell
# ATTENZIONE: le modifiche allo schema sono irreversibili e si propagano a tutto il forest

# Generare un OID univoco per i nuovi attributi
$prefix = "1.2.840.113556.1.8000.2554"  # Prefix Microsoft per OID custom
$guid = [System.Guid]::NewGuid()
$oidSuffix = $guid.ToString().Replace("-","").Substring(0,10)
$newOid = "$prefix.$oidSuffix"

# Creare un nuovo attributo (esempio: employee badge number)
$schemaPath = (Get-ADRootDSE).schemaNamingContext
New-ADObject -Name "contoso-BadgeNumber" -Type "attributeSchema" `
    -Path $schemaPath `
    -OtherAttributes @{
        attributeId = $newOid
        attributeSyntax = "2.5.5.12"  # Unicode String
        isSingleValued = $true
        oMSyntax = 64
        searchFlags = 1  # Indicizzato
        lDAPDisplayName = "contosoBadgeNumber"
    }

# Aggiornare lo schema (richiede Schema Admin)
$rootDSE = New-Object System.DirectoryServices.DirectoryEntry("LDAP://RootDSE")
$rootDSE.Put("schemaUpdateNow", 1)
$rootDSE.SetInfo()
```

### Deferred Index e searchFlags

L'attributo `searchFlags` controlla il comportamento di indicizzazione e replicazione di un attributo nello schema. I bit principali:

| Bit | Valore | Significato |
|-----|--------|-------------|
| 0 | 1 | **Indexed** — Accelera le query LDAP con filtri su questo attributo |
| 1 | 2 | **Index in container** — Indicizzato per ricerche limitate a un singolo container |
| 2 | 4 | **ANR (Ambiguous Name Resolution)** — Partecipa alla risoluzione dei nomi ambigui |
| 3 | 8 | **Preserve on delete** — Preservato quando l'oggetto diventa tombstone |
| 5 | 32 | **Tuple index** — Indice su sottostringhe, utile per query wildcard mediana (`*value*`) |
| 7 | 128 | **Confidential** — Richiede `RIGHT_DS_READ_PROPERTY_EXTENDED` per la lettura |
| 9 | 512 | **RODC Filtered** — Non replicato sui RODC |

**Deferred Index:** Quando si aggiunge un indice su un attributo esistente in un database con milioni di oggetti, la costruzione avviene in background senza impatto immediato sulle prestazioni del DC. Durante la costruzione l'indice non è disponibile per le query. Per database grandi, la costruzione può richiedere ore.

```powershell
# Verificare i searchFlags di un attributo
Get-ADObject -SearchBase (Get-ADRootDSE).schemaNamingContext `
    -Filter 'lDAPDisplayName -eq "department"' -Properties searchFlags, isMemberOfPartialAttributeSet |
    Select-Object lDAPDisplayName, searchFlags, isMemberOfPartialAttributeSet

# Aggiungere un indice a un attributo non indicizzato (richiede Schema Admin)
$attrDN = (Get-ADObject -SearchBase (Get-ADRootDSE).schemaNamingContext `
    -Filter 'lDAPDisplayName -eq "extensionAttribute1"' -Properties searchFlags).DistinguishedName
Set-ADObject $attrDN -Replace @{searchFlags = 1}

# Marcare un attributo come confidenziale (bit 7)
Set-ADObject $attrDN -Replace @{searchFlags = 128}

# Aggiungere un attributo al Partial Attribute Set (replicato sui GC)
Set-ADObject $attrDN -Replace @{isMemberOfPartialAttributeSet = $true}
# ATTENZIONE: aggiungere attributi al PAS triggera un full sync del GC su tutti i DC

# Monitorare la costruzione degli indici — Event ID 1137
Get-WinEvent -LogName "Directory Service" -MaxEvents 200 |
    Where-Object { $_.Id -eq 1137 } |
    Select-Object TimeCreated, Message
```

---

## Tombstone Lifetime e AD Recycle Bin

### Tombstone

Quando un oggetto viene eliminato in AD, non viene rimosso immediatamente dal database. Viene convertito in un **tombstone**: la maggior parte degli attributi viene rimossa, l'attributo `isDeleted` viene impostato a `TRUE` e l'oggetto viene spostato nel container `Deleted Objects`. Il tombstone viene replicato a tutti i DC per informarli dell'eliminazione.

Il **Tombstone Lifetime (TSL)** definisce per quanti giorni il tombstone persiste prima di essere eliminato definitivamente dal garbage collection. Il default è **180 giorni** (60 giorni per forest creati con Windows 2000/2003).

```powershell
# Verificare il Tombstone Lifetime
Get-ADObject "CN=Directory Service,CN=Windows NT,CN=Services,$(
    (Get-ADRootDSE).configurationNamingContext)" -Properties tombstoneLifetime |
    Select-Object tombstoneLifetime

# Modificare il Tombstone Lifetime (raccomandato: 180 giorni)
Set-ADObject "CN=Directory Service,CN=Windows NT,CN=Services,$(
    (Get-ADRootDSE).configurationNamingContext)" `
    -Replace @{tombstoneLifetime = 180}
```

### AD Recycle Bin

L'AD Recycle Bin, introdotto in Windows Server 2008 R2, preserva tutti gli attributi degli oggetti eliminati (inclusi quelli linked come group membership) per un periodo configurabile, rendendo il recovery completo e senza perdita di dati.

```powershell
# Abilitare il Recycle Bin (IRREVERSIBILE — richiede Forest Level 2008 R2+)
Enable-ADOptionalFeature -Identity "Recycle Bin Feature" `
    -Scope ForestOrConfigurationSet `
    -Target "contoso.com" `
    -Confirm:$false

# Verificare lo stato
Get-ADOptionalFeature -Filter * | Select-Object Name, EnabledScopes

# Elencare gli oggetti eliminati
Get-ADObject -Filter * -IncludeDeletedObjects |
    Where-Object { $_.Deleted -eq $true -and $_.ObjectClass -ne "container" } |
    Select-Object Name, ObjectClass, whenChanged, DistinguishedName |
    Sort-Object whenChanged -Descending

# Ripristinare un utente eliminato
Get-ADObject -Filter 'sAMAccountName -eq "mario.rossi"' -IncludeDeletedObjects |
    Restore-ADObject

# Ripristinare tutti gli oggetti eliminati da una OU specifica
Get-ADObject -Filter * -IncludeDeletedObjects -SearchBase "OU=Utenti,DC=contoso,DC=com" |
    Where-Object { $_.Deleted -eq $true } | Restore-ADObject

# Ripristinare un'intera OU con il suo contenuto
# Prima ripristinare la OU, poi gli oggetti al suo interno
$deletedOU = Get-ADObject -Filter 'Name -eq "Sede-Roma" -and ObjectClass -eq "organizationalUnit"' -IncludeDeletedObjects
$deletedOU | Restore-ADObject

# Poi ripristinare gli oggetti dentro la OU
Get-ADObject -Filter * -IncludeDeletedObjects |
    Where-Object { $_.LastKnownParent -like "*Sede-Roma*" -and $_.Deleted } |
    Restore-ADObject
```

### Deleted Object Lifetime vs Tombstone Lifetime

Con il Recycle Bin abilitato:
- **Deleted Object Lifetime** = Periodo in cui l'oggetto è nel Recycle Bin con tutti gli attributi preservati (default = tombstoneLifetime)
- **Tombstone Lifetime** = Dopo il Deleted Object Lifetime, l'oggetto diventa un tombstone "classico" (attributi rimossi) per un ulteriore periodo uguale al TSL

Totale: un oggetto eliminato è recuperabile (completamente) per `Deleted Object Lifetime` giorni, poi parzialmente per altri `Tombstone Lifetime` giorni.

---

## Query LDAP Avanzate

### dsquery e PowerShell

```powershell
# Trovare utenti con password che non scade mai
Get-ADUser -Filter 'PasswordNeverExpires -eq $true' -Properties PasswordNeverExpires |
    Select-Object Name, SamAccountName, Enabled, PasswordNeverExpires

# Utenti che non hanno fatto logon negli ultimi 90 giorni
$threshold = (Get-Date).AddDays(-90)
Get-ADUser -Filter 'LastLogonDate -lt $threshold' -Properties LastLogonDate |
    Select-Object Name, SamAccountName, LastLogonDate, Enabled |
    Sort-Object LastLogonDate

# Computer con OS obsoleto
Get-ADComputer -Filter 'OperatingSystem -like "*Windows 7*" -or OperatingSystem -like "*2012*"' `
    -Properties OperatingSystem, LastLogonDate |
    Select-Object Name, OperatingSystem, LastLogonDate

# Gruppi vuoti
Get-ADGroup -Filter * -Properties Members |
    Where-Object { $_.Members.Count -eq 0 } |
    Select-Object Name, GroupScope, GroupCategory

# Utenti con delega non vincolata (rischio sicurezza!)
Get-ADUser -Filter 'TrustedForDelegation -eq $true' -Properties TrustedForDelegation |
    Select-Object Name, SamAccountName, TrustedForDelegation

# Computer con delega non vincolata
Get-ADComputer -Filter 'TrustedForDelegation -eq $true' -Properties TrustedForDelegation |
    Where-Object { $_.Name -notlike "*DC*" } |
    Select-Object Name, TrustedForDelegation

# Utenti con SPN configurato (potenziali target di Kerberoasting)
Get-ADUser -Filter 'ServicePrincipalName -like "*"' -Properties ServicePrincipalName |
    Select-Object Name, SamAccountName, ServicePrincipalName

# dsquery equivalenti
dsquery user -inactive 12  # Utenti inattivi per 12 settimane
dsquery computer -inactive 8  # Computer inattivi per 8 settimane
dsquery user -stalepwd 90  # Password non cambiata da 90 giorni

# Query LDAP raw con DirectorySearcher
$searcher = New-Object System.DirectoryServices.DirectorySearcher
$searcher.Filter = "(&(objectClass=user)(objectCategory=person)(adminCount=1))"
$searcher.PropertiesToLoad.AddRange(@("samAccountName","distinguishedName","whenChanged"))
$searcher.FindAll() | ForEach-Object {
    [PSCustomObject]@{
        Name = $_.Properties.samaccountname[0]
        DN   = $_.Properties.distinguishedname[0]
    }
}
```

### Query LDAP per Audit di Sicurezza

```powershell
# Trovare account con adminCount=1 (protetti da AdminSDHolder)
Get-ADObject -Filter 'adminCount -eq 1' -Properties adminCount, objectClass, whenChanged |
    Select-Object Name, ObjectClass, whenChanged

# Account con password vuota consentita
Get-ADUser -Filter 'PasswordNotRequired -eq $true' -Properties PasswordNotRequired |
    Select-Object Name, Enabled, PasswordNotRequired

# Account con Pre-Authentication Kerberos disabilitata (AS-REP Roastable)
Get-ADUser -Filter 'DoesNotRequirePreAuth -eq $true' -Properties DoesNotRequirePreAuth |
    Select-Object Name, DoesNotRequirePreAuth

# Ultimi oggetti creati (monitoraggio cambiamenti)
Get-ADObject -Filter * -Properties whenCreated |
    Where-Object { $_.whenCreated -gt (Get-Date).AddDays(-7) } |
    Sort-Object whenCreated -Descending |
    Select-Object Name, ObjectClass, whenCreated
```

---

## Trust Relationships — Approfondimento

### Tipi di Trust

Active Directory supporta diversi tipi di trust relationship, ciascuno con caratteristiche e casi d'uso specifici.

| Tipo di Trust | Direzione | Transitività | Creazione | Caso d'uso |
|---|---|---|---|---|
| **Parent-Child** | Bidirezionale | Transitivo | Automatica (join dominio figlio) | Struttura gerarchica all'interno di un forest |
| **Tree-Root** | Bidirezionale | Transitivo | Automatica (nuovo albero nel forest) | Namespace DNS diversi nello stesso forest |
| **Forest** | Bidirezionale o unidirezionale | Transitivo (tra forest) | Manuale | Collaborazione tra organizzazioni separate |
| **External** | Unidirezionale | Non transitivo | Manuale | Trust con singolo dominio NT4 o dominio AD esterno |
| **Shortcut** | Bidirezionale o unidirezionale | Transitivo | Manuale | Ottimizzazione autenticazione tra domini distanti nel forest |
| **Realm** | Bidirezionale o unidirezionale | Transitivo o non transitivo | Manuale | Trust con realm Kerberos non-Windows (MIT, Linux) |

```
Forest A (contoso.com)              Forest B (partner.com)
┌──────────────────────┐            ┌──────────────────────┐
│  contoso.com (root)  │            │  partner.com (root)  │
│  ├─ corp.contoso.com │◄══════════►│  ├─ eu.partner.com   │
│  └─ dev.contoso.com  │  Forest    │  └─ us.partner.com   │
│                      │  Trust     │                      │
└──────────────────────┘            └──────────────────────┘

Shortcut Trust (ottimizzazione):
  dev.contoso.com ◄─── shortcut ───► corp.contoso.com
  (evita di salire a contoso.com per la referral chain)
```

### SID Filtering e Selective Authentication

**SID Filtering (Quarantine):** Meccanismo di sicurezza che rimuove i SID estranei (non appartenenti al dominio trusted) dai token di autenticazione che attraversano un trust. Attivo per default sui forest trust, previene attacchi di SID History injection.

```powershell
# Verificare lo stato del SID Filtering su un trust
Get-ADTrust -Identity "partner.com" -Properties SIDFilteringForestAware,
    SIDFilteringQuarantined

# SID Filtering è abilitato per default sui forest trust
# Per disabilitare (SOLO se necessario per migrazione con SID History):
netdom trust contoso.com /domain:partner.com /quarantine:No
# ATTENZIONE: disabilitare SID Filtering espone a SID injection attacks

# Riabilitare SID Filtering dopo la migrazione:
netdom trust contoso.com /domain:partner.com /quarantine:Yes
```

**Selective Authentication:** Limita quali utenti del forest trusted possono autenticarsi su quali risorse nel forest trusting. Invece di concedere accesso a tutto il forest (forest-wide authentication), richiede il permesso esplicito "Allowed to Authenticate" sui singoli computer.

```powershell
# Abilitare Selective Authentication su un forest trust
Set-ADObject "CN=partner.com,CN=System,DC=contoso,DC=com" `
    -Replace @{trustAttributes = 64}  # TRUST_ATTRIBUTE_CROSS_ORGANIZATION

# Concedere "Allowed to Authenticate" a un gruppo del forest trusted
# su un server specifico del forest locale
$server = Get-ADComputer "FILESERVER01"
$acl = Get-Acl "AD:\$($server.DistinguishedName)"
$trustedGroup = New-Object System.Security.Principal.SecurityIdentifier(
    "S-1-5-21-XXXXXXXXX-XXXXXXXXX-XXXXXXXXX-1234")  # SID del gruppo nel forest trusted
$rule = New-Object System.DirectoryServices.ActiveDirectoryAccessRule(
    $trustedGroup,
    [System.DirectoryServices.ActiveDirectoryRights]"ExtendedRight",
    [System.Security.AccessControl.AccessControlType]"Allow",
    [guid]"68b1d179-0d15-4d4f-ab71-46152e79a7bc"  # Allowed-To-Authenticate
)
$acl.AddAccessRule($rule)
Set-Acl "AD:\$($server.DistinguishedName)" $acl
```

### Gestione Trust con PowerShell

```powershell
# Creare un forest trust bidirezionale
$localForest = [System.DirectoryServices.ActiveDirectory.Forest]::GetCurrentForest()
$remoteForest = [System.DirectoryServices.ActiveDirectory.Forest]::GetForest(
    (New-Object System.DirectoryServices.ActiveDirectory.DirectoryContext(
        "Forest", "partner.com", "admin@partner.com", "P@ssw0rd")))
$localForest.CreateTrustRelationship($remoteForest, "Bidirectional")

# Verificare lo stato di un trust
$trust = Get-ADTrust -Filter 'Target -eq "partner.com"'
$trust | Select-Object Name, Direction, TrustType, DisallowTransivity,
    SelectiveAuthentication, IntraForest, IsTreeParent

# Validare il trust
Test-ComputerSecureChannel  # Per trust con il proprio dominio
nltest /sc_verify:partner.com  # Per trust specifico

# Reset del trust (se la relazione è rotta)
netdom trust contoso.com /domain:partner.com /reset /passwordT:NewTrustPwd!

# Elencare tutti i trust con dettagli
Get-ADTrust -Filter * | Format-Table Name, Direction, TrustType,
    SelectiveAuthentication, IntraForest -AutoSize
```

---

## FSMO Roles — Deep Dive

I cinque ruoli FSMO (Flexible Single Master Operations) sono operazioni che devono essere gestite da un singolo domain controller alla volta per prevenire conflitti. Due ruoli sono forest-wide, tre sono domain-wide.

### Matrice di Placement Ottimale

| Ruolo | Scope | DC Consigliato | Giustificazione |
|---|---|---|---|
| **Schema Master** | Forest | Root domain DC, stesso DC del Domain Naming Master | Usato raramente (solo estensioni schema). Collocarlo con DN Master riduce la complessità. |
| **Domain Naming Master** | Forest | Root domain DC, stesso DC dello Schema Master | Usato raramente (aggiunta/rimozione domini). Deve avere il Global Catalog. |
| **RID Master** | Dominio | DC principale del dominio, non RODC | Emette pool di RID per la creazione di oggetti. Deve essere raggiungibile da tutti i DC che creano oggetti. |
| **PDC Emulator** | Dominio | DC con migliore connettività e hardware, nel sito hub | Gestisce: cambio password urgenti, time sync, lockout, GPO editor default. È il DC più sollecitato. |
| **Infrastructure Master** | Dominio | DC senza Global Catalog (in ambienti multi-dominio) | Aggiorna riferimenti cross-dominio. Se tutti i DC sono GC, il posizionamento è irrilevante. |

```
Forest contoso.com — Placement FSMO consigliato:

Root domain DC01 (contoso.com):
  ├── Schema Master ★
  ├── Domain Naming Master ★
  ├── RID Master
  ├── PDC Emulator
  └── Infrastructure Master (o su DC02 se non tutti sono GC)

Child domain DC03 (corp.contoso.com):
  ├── RID Master
  ├── PDC Emulator
  └── Infrastructure Master

Child domain DC05 (dev.contoso.com):
  ├── RID Master
  ├── PDC Emulator
  └── Infrastructure Master

★ = forest-wide (una sola istanza per forest)
```

### Trasferimento e Seizure dei Ruoli

**Trasferimento (cooperativo):** Usato quando entrambi i DC (sorgente e destinazione) sono online e funzionanti.

```powershell
# Trasferire tutti i ruoli a un singolo DC
Move-ADDirectoryServerOperationMasterRole -Identity "DC02" `
    -OperationMasterRole SchemaMaster, DomainNamingMaster, RIDMaster,
    PDCEmulator, InfrastructureMaster -Confirm:$false

# Trasferire un singolo ruolo
Move-ADDirectoryServerOperationMasterRole -Identity "DC02" `
    -OperationMasterRole PDCEmulator

# Verificare i ruoli attuali (forest-wide)
Get-ADForest | Select-Object SchemaMaster, DomainNamingMaster

# Verificare i ruoli attuali (domain-wide)
Get-ADDomain | Select-Object RIDMaster, PDCEmulator, InfrastructureMaster

# Verifica complessiva con netdom
netdom query fsmo
```

**Seizure (forzata):** Usato quando il DC che detiene il ruolo è permanentemente offline. L'operazione è irreversibile: il vecchio DC non deve MAI essere riconnesso alla rete.

```powershell
# Seizure via PowerShell (aggiungere -Force)
Move-ADDirectoryServerOperationMasterRole -Identity "DC02" `
    -OperationMasterRole RIDMaster -Force

# Seizure via ntdsutil (metodo classico)
ntdsutil
  roles
  connections
  connect to server DC02
  quit
  seize RID Master
  quit
  quit

# CRITICO: dopo il seize, il vecchio DC non deve MAI tornare online
# Se il vecchio DC è raggiungibile, fare metadata cleanup:
ntdsutil
  metadata cleanup
  connections
  connect to server DC02
  quit
  select operation target
  list domains
  select domain 0
  list sites
  select site 0
  list servers in site
  select server <numero del vecchio DC>
  quit
  remove selected server
  quit
  quit
```

### Impatto Operativo della Perdita di un Ruolo FSMO

| Ruolo Perso | Impatto Immediato | Impatto a Medio Termine | Azione |
|---|---|---|---|
| **Schema Master** | Nessuno | Impossibile estendere lo schema (installazione Exchange, Lync, etc.) | Seize solo se necessaria estensione schema |
| **Domain Naming Master** | Nessuno | Impossibile aggiungere/rimuovere domini dal forest | Seize solo se necessario aggiungere domini |
| **RID Master** | Nessuno (i DC hanno pool di RID in cache) | Quando i pool RID si esauriscono, impossibile creare nuovi oggetti | Seize con urgenza media (pool ~500 RID per DC) |
| **PDC Emulator** | Cambio password non propagati urgentemente, time sync alterato, lockout policy rallentata | GPO editor default non raggiungibile, autenticazione NTLMv1 fallisce per password recenti | **Seize immediato** — impatto operativo più alto |
| **Infrastructure Master** | Nessuno in ambienti single-domain o se tutti i DC sono GC | In ambienti multi-dominio con DC non-GC: riferimenti cross-dominio non aggiornati (phantom objects) | Seize con urgenza bassa |

---

## AD Security Hardening

### Protected Users Group

Il gruppo Protected Users (Windows Server 2012 R2+) applica automaticamente protezioni non configurabili ai suoi membri.

**Protezioni applicate:**
- Nessun caching delle credenziali (no NTLM hash memorizzato su workstation)
- Nessun utilizzo di NTLM, digest authentication o CredSSP
- Kerberos non usa DES o RC4 (solo AES)
- Il TGT Kerberos non è rinnovabile (lifetime 4 ore, non 10 ore)
- Nessuna delegazione Kerberos (unconstrained o constrained)

```powershell
# Aggiungere account al gruppo Protected Users
Add-ADGroupMember -Identity "Protected Users" -Members "admin-tier0", "admin-dc01"

# Verificare i membri
Get-ADGroupMember -Identity "Protected Users" | Select-Object Name, objectClass

# ATTENZIONE: non aggiungere service account a Protected Users
# La restrizione su NTLM e delegazione può rompere applicazioni legacy
# Non aggiungere account computer — causa malfunzionamenti

# Verificare quali account sono protetti e il loro ultimo logon
Get-ADGroupMember "Protected Users" -Recursive |
    Get-ADUser -Properties LastLogonDate, PasswordLastSet |
    Select-Object Name, SamAccountName, LastLogonDate, PasswordLastSet |
    Format-Table -AutoSize
```

### LAPS e Windows LAPS

**LAPS legacy (2015-2023):** Gestisce la password dell'account Administrator locale, memorizzandola in un attributo confidenziale di AD (`ms-Mcs-AdmPwd`). Richiede schema extension e GPO client-side extension.

**Windows LAPS (Windows Server 2025, Windows 11 23H2+):** Integrato nel sistema operativo, non richiede client-side extension. Supporta: backup su AD e/o Entra ID, password encryption, password history, account DSRM dei DC.

```powershell
# --- Windows LAPS (moderno, integrato in Windows Server 2025) ---

# Verificare se Windows LAPS schema è presente
Get-ADObject -SearchBase (Get-ADRootDSE).schemaNamingContext `
    -Filter 'name -eq "ms-LAPS-Password"' -Properties name

# Aggiornare lo schema per Windows LAPS (se necessario)
Update-LapsADSchema

# Configurare Windows LAPS via GPO o PowerShell
# Computer Configuration > Administrative Templates > System > LAPS
# Oppure:
Set-LapsADPasswordExpirationPolicy -Identity "OU=Workstations,OU=Computer,DC=contoso,DC=com" `
    -PasswordLength 20 -PasswordAgeDays 30

# Leggere la password LAPS di un computer
Get-LapsADPassword -Identity "WS001" -AsPlainText

# Elencare tutte le password LAPS scadute
Get-ADComputer -Filter * -SearchBase "OU=Workstations,OU=Computer,DC=contoso,DC=com" `
    -Properties msLAPS-PasswordExpirationTime |
    Where-Object { $_.'msLAPS-PasswordExpirationTime' -lt (Get-Date) } |
    Select-Object Name, @{N='Scadenza';E={$_.'msLAPS-PasswordExpirationTime'}}

# --- LAPS legacy (per ambienti pre-2025) ---

# Verificare schema extension LAPS legacy
Get-ADObject -SearchBase (Get-ADRootDSE).schemaNamingContext `
    -Filter 'name -eq "ms-Mcs-AdmPwd"' -Properties name

# Leggere password LAPS legacy
Get-ADComputer "WS001" -Properties ms-Mcs-AdmPwd, ms-Mcs-AdmPwdExpirationTime |
    Select-Object Name, @{N='Password';E={$_.'ms-Mcs-AdmPwd'}},
    @{N='Expiration';E={[datetime]::FromFileTime($_.'ms-Mcs-AdmPwdExpirationTime')}}
```

### Kerberos Constrained Delegation e RBCD

**Unconstrained Delegation (PERICOLOSA):** Il server può impersonare l'utente verso qualsiasi servizio. Un attaccante che compromette il server ottiene i TGT di tutti gli utenti che si autenticano.

**Constrained Delegation (KCD):** Il server può impersonare l'utente solo verso servizi specifici elencati in `msDS-AllowedToDelegateTo`. Richiede configurazione sul DC. Limitazione: richiede accesso in scrittura all'attributo del server, che tipicamente richiede Domain Admin.

**Resource-Based Constrained Delegation (RBCD):** La configurazione avviene sulla risorsa target tramite `msDS-AllowedToActOnBehalfOfOtherIdentity`. Il proprietario della risorsa decide chi può delegare verso di essa, senza richiedere Domain Admin.

```powershell
# Verificare computer con unconstrained delegation (RISCHIO)
Get-ADComputer -Filter 'TrustedForDelegation -eq $true' `
    -Properties TrustedForDelegation |
    Where-Object { $_.Name -notlike "*DC*" } |
    Select-Object Name, TrustedForDelegation

# Configurare Constrained Delegation (classica)
Set-ADComputer "WEBSERVER01" -TrustedForDelegation $false
Set-ADComputer "WEBSERVER01" `
    -Add @{'msDS-AllowedToDelegateTo' = @(
        'MSSQLSvc/SQL01.contoso.com:1433',
        'HTTP/API01.contoso.com'
    )}

# Configurare Resource-Based Constrained Delegation (RBCD)
# Il proprietario di SQL01 configura: "WEBSERVER01 può delegare verso di me"
$webServer = Get-ADComputer "WEBSERVER01"
Set-ADComputer "SQL01" `
    -PrincipalsAllowedToDelegateToAccount $webServer

# Verificare RBCD configurata su un server
Get-ADComputer "SQL01" -Properties PrincipalsAllowedToDelegateToAccount |
    Select-Object -ExpandProperty PrincipalsAllowedToDelegateToAccount

# Rimuovere RBCD
Set-ADComputer "SQL01" -PrincipalsAllowedToDelegateToAccount $null
```

### Authentication Policies e Silos

Le Authentication Policies (Windows Server 2012 R2+) permettono di limitare dove un account può autenticarsi e con quale TGT lifetime. I Silos raggruppano utenti, computer e service account sotto una policy comune.

```powershell
# Creare una Authentication Policy per Tier 0
New-ADAuthenticationPolicy -Name "Policy-Tier0" `
    -UserTGTLifetimeMins 240 `
    -Enforce `
    -Description "Policy per account Tier 0 — TGT 4 ore"

# Creare una condizione di accesso: solo da DC e PAW
# Il computer deve essere nel gruppo "GG-Tier0-Computers"
$condition = "O:SYG:SYD:(XA;OICI;CR;;;WD;(@USER.ad://ext/AuthenticationSilo == `"Silo-Tier0`"))"

# Creare un Authentication Silo
New-ADAuthenticationPolicySilo -Name "Silo-Tier0" `
    -UserAuthenticationPolicy "Policy-Tier0" `
    -ComputerAuthenticationPolicy "Policy-Tier0" `
    -ServiceAuthenticationPolicy "Policy-Tier0" `
    -Enforce `
    -Description "Silo per isolamento credenziali Tier 0"

# Assegnare utenti e computer al silo
Set-ADUser "admin-tier0" -AuthenticationPolicySilo "Silo-Tier0"
Set-ADComputer "DC01" -AuthenticationPolicySilo "Silo-Tier0"
Set-ADComputer "PAW01" -AuthenticationPolicySilo "Silo-Tier0"

# Verificare le assegnazioni
Get-ADUser "admin-tier0" -Properties AuthenticationPolicy, AuthenticationPolicySilo |
    Select-Object Name, AuthenticationPolicy, AuthenticationPolicySilo
```

### Credential Guard

Credential Guard utilizza la virtualizzazione hardware (VBS — Virtualization-Based Security) per isolare i secret NTLM e i TGT Kerberos in un processo protetto (`lsaIso.exe`), inaccessibile anche al kernel compromesso.

```powershell
# Verificare se Credential Guard è attivo
Get-CimInstance -ClassName Win32_DeviceGuard `
    -Namespace root\Microsoft\Windows\DeviceGuard |
    Select-Object -ExpandProperty SecurityServicesRunning
# 1 = Credential Guard attivo

# Abilitare Credential Guard via GPO
# Computer Configuration > Administrative Templates > System > Device Guard
# → Turn On Virtualization Based Security
# → Credential Guard Configuration: Enabled with UEFI lock

# Verificare via registry
Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name LsaCfgFlags
# 1 = abilitato con UEFI lock, 2 = abilitato senza lock

# Verificare che VBS sia supportato
systeminfo | Select-String "Virtualization-based security"
```

---

## Superficie di Attacco AD

### Kerberoasting

**Tecnica:** Richiesta di Service Ticket (TGS) per qualsiasi SPN associato a un account utente (non computer). Il ticket è cifrato con l'hash NTLM della password del service account. L'attaccante estrae il ticket e lo cracka offline.

**Prerequisiti attaccante:** Qualsiasi account di dominio autenticato.

```powershell
# DETECTION: trovare account utente con SPN (target di Kerberoasting)
Get-ADUser -Filter 'ServicePrincipalName -like "*"' `
    -Properties ServicePrincipalName, PasswordLastSet, Enabled |
    Select-Object Name, SamAccountName, ServicePrincipalName,
    PasswordLastSet, Enabled | Format-Table -AutoSize

# MITIGAZIONE:
# 1. Usare gMSA al posto di account utente con SPN
# 2. Password lunghe (25+ caratteri) per account con SPN obbligatorio
# 3. Monitorare Event ID 4769 (TGS request) con anomalie
# 4. Usare AES encryption (disabilitare RC4 dove possibile)

# Disabilitare RC4 per un account (forzare AES)
Set-ADUser "svc-sqlserver" `
    -KerberosEncryptionType AES128,AES256 `
    -Replace @{'msDS-SupportedEncryptionTypes' = 24}  # 24 = AES128+AES256

# Monitorare richieste TGS anomale
Get-WinEvent -LogName Security -FilterXPath `
    "*[System[EventID=4769] and EventData[Data[@Name='TicketEncryptionType']='0x17']]" `
    -MaxEvents 50 |
    Select-Object TimeCreated,
    @{N='Account';E={$_.Properties[0].Value}},
    @{N='Service';E={$_.Properties[2].Value}}
```

### AS-REP Roasting

**Tecnica:** Richiesta di TGT (AS-REQ) per account con Kerberos pre-authentication disabilitata. La risposta AS-REP contiene dati cifrati con l'hash della password dell'utente, crackabili offline.

```powershell
# DETECTION: trovare account senza pre-authentication
Get-ADUser -Filter 'DoesNotRequirePreAuth -eq $true' `
    -Properties DoesNotRequirePreAuth |
    Select-Object Name, SamAccountName, DoesNotRequirePreAuth

# MITIGAZIONE: riabilitare la pre-authentication (non dovrebbe mai essere disabilitata)
Get-ADUser -Filter 'DoesNotRequirePreAuth -eq $true' |
    Set-ADUser -DoesNotRequirePreAuth $false

# Monitorare Event ID 4768 con pre-auth failure (tipo 0x0)
```

### DCSync e DCShadow

**DCSync:** Simulazione del protocollo di replica AD (MS-DRSR) per estrarre hash delle password da qualsiasi DC. Richiede i permessi "Replicating Directory Changes" e "Replicating Directory Changes All" sul domain naming context.

**DCShadow:** Registra un DC fittizio nello schema AD e inietta modifiche direttamente nel database AD, bypassando logging e monitoring. Richiede Domain Admin + Schema Admin.

```powershell
# DETECTION DCSync: verificare chi ha i permessi di replica
$domainDN = (Get-ADDomain).DistinguishedName
$acl = Get-Acl "AD:\$domainDN"
$acl.Access |
    Where-Object {
        $_.ObjectType -eq "1131f6ad-9c07-11d1-f79f-00c04fc2dcd2" -or  # Replicating Dir Changes All
        $_.ObjectType -eq "1131f6aa-9c07-11d1-f79f-00c04fc2dcd2"      # Replicating Dir Changes
    } |
    Where-Object { $_.IdentityReference -notlike "NT AUTHORITY\*" } |
    Select-Object IdentityReference, ActiveDirectoryRights, ObjectType |
    Format-Table -AutoSize

# MITIGAZIONE DCSync:
# 1. Solo Domain Controllers e account di replica autorizzati devono avere questi permessi
# 2. Monitorare Event ID 4662 con le GUID di replica specifiche
# 3. Usare Microsoft Defender for Identity / ATA per detection in tempo reale

# DETECTION DCShadow: verificare registrazioni di DC inattese
Get-ADDomainController -Filter * | Select-Object Name, Site, OperatingSystem |
    Format-Table -AutoSize
# Confrontare con la lista nota dei DC autorizzati
```

### Golden Ticket e Silver Ticket

**Golden Ticket:** TGT Kerberos forgiato con l'hash di `krbtgt`. Permette di impersonare qualsiasi utente per la durata del ticket (anche 10 anni). Sopravvive al reset password dell'utente.

**Silver Ticket:** TGS Kerberos forgiato con l'hash dell'account computer/servizio target. Permette l'accesso a un singolo servizio senza contattare il KDC. Non appare nei log del DC.

```powershell
# MITIGAZIONE Golden Ticket:
# 1. Reset password krbtgt DUE VOLTE (con 10+ ore di intervallo)
# PRIMO RESET:
Set-ADAccountPassword -Identity "krbtgt" `
    -Reset -NewPassword (ConvertTo-SecureString -AsPlainText `
    ([char[]]([char]33..[char]122) | Get-Random -Count 32 | ForEach-Object {[string]$_}) `
    -Force)
# ATTENDERE ALMENO 10 ORE (replica + TGT lifetime)
# SECONDO RESET:
Set-ADAccountPassword -Identity "krbtgt" `
    -Reset -NewPassword (ConvertTo-SecureString -AsPlainText `
    ([char[]]([char]33..[char]122) | Get-Random -Count 32 | ForEach-Object {[string]$_}) `
    -Force)

# 2. Verificare l'ultimo reset di krbtgt
Get-ADUser "krbtgt" -Properties PasswordLastSet |
    Select-Object Name, PasswordLastSet

# MITIGAZIONE Silver Ticket:
# 1. Usare gMSA (rotazione password automatica ogni 30 giorni)
# 2. Abilitare PAC Validation sui servizi
# 3. Monitorare accessi ai servizi senza corrispondente TGS request al DC
```

### Pass-the-Hash e Pass-the-Ticket

**Pass-the-Hash (PtH):** Utilizzo dell'hash NTLM (senza conoscere la password in chiaro) per autenticarsi via NTLM. Efficace contro servizi che accettano NTLM.

**Pass-the-Ticket (PtT):** Utilizzo di un TGT o TGS Kerberos rubato dalla memoria per autenticarsi su servizi Kerberos.

```powershell
# MITIGAZIONE PtH:
# 1. Disabilitare NTLM dove possibile
# GPO: Computer Configuration > Windows Settings > Security Settings >
#       Local Policies > Security Options >
#       Network security: Restrict NTLM: Incoming/Outgoing NTLM traffic

# 2. Audit dell'uso NTLM prima di bloccarlo
# GPO: Network security: Restrict NTLM: Audit NTLM authentication in this domain
# Monitorare Event ID 8001-8004 nel log Microsoft-Windows-NTLM/Operational

# 3. Implementare Credential Guard (vedi sezione sopra)

# 4. Abilitare Protected Users per account privilegiati

# MITIGAZIONE PtT:
# 1. Ridurre TGT lifetime per account privilegiati (Authentication Policies)
# 2. Credential Guard per proteggere i ticket in memoria
# 3. Implementare il tiering model per limitare dove le credenziali privilegiate
#    vengono esposte
```

### AD Certificate Services Abuse (ESC1-ESC8)

Le vulnerabilità di AD CS (Active Directory Certificate Services) sono state catalogate da SpecterOps (whitepaper "Certified Pre-Owned", 2021). Le principali:

| ID | Vulnerabilità | Impatto | Mitigazione |
|---|---|---|---|
| **ESC1** | Template con Enrollee Supplies Subject + Client Authentication + Enrollment open | Qualsiasi utente può richiedere un certificato per qualsiasi altro utente (incluso Domain Admin) | Rimuovere "Enrollee Supplies Subject" o limitare enrollment a gruppi specifici |
| **ESC2** | Template con Any Purpose o SubCA EKU | Come ESC1, ma con EKU generici | Limitare EKU e enrollment |
| **ESC3** | Enrollment Agent template con enrollment aperto | L'enrollment agent può richiedere certificati per conto di chiunque | Limitare enrollment agent a gruppi specifici |
| **ESC4** | ACL vulnerabili sui template (WriteDACL, WriteOwner, WriteProperty) | Modifica del template per abilitare ESC1/ESC2 | Audit ACL sui template, rimuovere permessi eccessivi |
| **ESC6** | CA con flag EDITF_ATTRIBUTESUBJECTALTNAME2 | Qualsiasi template diventa vulnerabile come ESC1 | Rimuovere il flag: `certutil -config "CA01\Contoso-CA" -setreg policy\EditFlags -EDITF_ATTRIBUTESUBJECTALTNAME2` |
| **ESC7** | ACL vulnerabili sulla CA (ManageCA, ManageCertificates) | Approvazione arbitraria di richieste, modifica config CA | Audit ACL sulla CA, rimuovere permessi eccessivi |
| **ESC8** | NTLM relay verso il web enrollment della CA (HTTP) | Relay dell'autenticazione NTLM di un DC per ottenere un certificato DC | Disabilitare HTTP enrollment, usare solo HTTPS con EPA |

```powershell
# Audit dei template vulnerabili (ESC1)
# Cercare template con CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT e Client Authentication EKU
$templates = Get-ADObject -SearchBase "CN=Certificate Templates,CN=Public Key Services,CN=Services,$(
    (Get-ADRootDSE).configurationNamingContext)" -Filter * `
    -Properties msPKI-Certificate-Name-Flag, pKIExtendedKeyUsage, name,
    'nTSecurityDescriptor' |
    Where-Object {
        ($_.'msPKI-Certificate-Name-Flag' -band 1) -and  # ENROLLEE_SUPPLIES_SUBJECT
        ($_.pKIExtendedKeyUsage -contains "1.3.6.1.5.5.7.3.2")  # Client Authentication
    }

$templates | Select-Object Name,
    @{N='SuppliesSubject';E={$_.'msPKI-Certificate-Name-Flag' -band 1}},
    @{N='EKU';E={$_.pKIExtendedKeyUsage -join ', '}} |
    Format-Table -AutoSize

# Verificare il flag EDITF_ATTRIBUTESUBJECTALTNAME2 sulla CA (ESC6)
certutil -config "CA01\Contoso-CA" -getreg policy\EditFlags
# Se il flag è presente, rimuoverlo:
# certutil -config "CA01\Contoso-CA" -setreg policy\EditFlags -EDITF_ATTRIBUTESUBJECTALTNAME2
# net stop certsvc && net start certsvc
```

---

## Red Forest / ESAE Architecture

> **Nota:** Microsoft ha deprecato il modello ESAE (Enhanced Security Admin Environment) / Red Forest nel 2021, sostituendolo con una strategia di privileged access cloud-first basata su Entra ID, Conditional Access e PIM. Tuttavia, i concetti fondamentali di isolamento delle credenziali e tiering rimangono validi e sono alla base delle architetture di sicurezza AD moderne.

### Tier 0 Isolation

Il Tier Model suddivide l'infrastruttura in livelli di criticità. Il principio cardine è: **le credenziali di un tier non devono mai essere esposte su sistemi di un tier inferiore**.

```
┌─────────────────────────────────────────────┐
│                  TIER 0                      │
│  Domain Controllers, AD FS, PKI CA,         │
│  Azure AD Connect, SIEM collector           │
│  Account: admin-tier0, svc-adfs             │
│  Logon permesso SOLO su: DC, PAW Tier 0     │
├─────────────────────────────────────────────┤
│                  TIER 1                      │
│  Application servers, file servers,          │
│  database servers, Exchange, SCCM            │
│  Account: admin-tier1                        │
│  Logon permesso su: Server, PAW Tier 1      │
├─────────────────────────────────────────────┤
│                  TIER 2                      │
│  Workstations, laptops, thin clients         │
│  Account: admin-tier2, helpdesk              │
│  Logon permesso su: Workstation, PAW Tier 2 │
└─────────────────────────────────────────────┘

REGOLA D'ORO: le credenziali scendono solo, mai salgono.
  Tier 0 → NON fa logon su Tier 1 o Tier 2
  Tier 1 → NON fa logon su Tier 2
  Un account Tier 2 NON deve MAI avere accesso a Tier 0 o Tier 1
```

```powershell
# Implementare il tiering con GPO — Deny logon
# GPO: "Tier0-Deny-Logon-Tier1-Tier2"
# Applicata a: OU=Server, OU=Workstations
# Computer Configuration > Windows Settings > Security Settings >
#   Local Policies > User Rights Assignment >
#   Deny log on locally: GG-Tier0-Admins
#   Deny log on through Remote Desktop Services: GG-Tier0-Admins
#   Deny access to this computer from the network: GG-Tier0-Admins

# Verificare dove un account privilegiato ha fatto logon (audit)
Get-WinEvent -LogName Security -FilterXPath `
    "*[System[EventID=4624] and EventData[Data[@Name='TargetUserName']='admin-tier0']]" `
    -MaxEvents 100 |
    Select-Object TimeCreated,
    @{N='Logon';E={$_.Properties[5].Value}},
    @{N='Computer';E={$_.Properties[11].Value}},
    @{N='LogonType';E={$_.Properties[8].Value}}
```

### Privileged Access Workstations (PAW)

Le PAW sono workstation dedicate esclusivamente all'amministrazione, hardened e isolate dalla rete utente. Non hanno accesso a Internet, email o applicazioni generiche.

**Requisiti PAW:**
- Hardware dedicato (non VM su hypervisor condiviso)
- Windows con Credential Guard, BitLocker, Secure Boot
- Nessun accesso Internet diretto
- Nessun software non essenziale (browser, Office, etc.)
- Patch management separato
- Monitoraggio rafforzato

```powershell
# GPO per PAW — configurazione base
# Computer Configuration > Administrative Templates >
# 1. Bloccare accesso Internet
#    Windows Components > Internet Explorer > Disable Internet Connection Wizard = Enabled
#    + Windows Firewall: bloccare traffico outbound tranne verso DC e jump server

# 2. Bloccare USB (eccetto tastiera/mouse)
#    System > Removable Storage Access > All Removable Storage classes: Deny all access

# 3. Abilitare AppLocker con whitelist restrittiva
#    Solo eseguibili firmati Microsoft + strumenti di amministrazione approvati

# Verificare la configurazione PAW
Get-ComputerInfo | Select-Object CsName, WindowsProductName,
    OsArchitecture, BiosFirmwareType
Get-BitLockerVolume C: | Select-Object VolumeStatus, EncryptionMethod, ProtectionStatus
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
    Select-Object SecurityServicesRunning, SecurityServicesConfigured
```

### Jump Server e Credential Isolation

I jump server (o bastion host) sono punti di accesso intermediari per l'amministrazione dei server, evitando la connessione diretta dalla workstation utente al server da amministrare.

```powershell
# Architettura di accesso:
# Utente → PAW → Jump Server (RDP Gateway) → Server Target
# Le credenziali Tier 1 vengono inserite SOLO sul jump server, mai sulla PAW

# Configurare RD Gateway come jump server
# Server Manager > Add Roles > Remote Desktop Services > RD Gateway
# Configurare Connection Authorization Policies (CAP) per limitare:
# - Chi può connettersi (solo admin autorizzati)
# - Da dove (solo da PAW)
# - Verso dove (solo server del tier autorizzato)

# Verificare le sessioni attive sul jump server
Get-RDUserSession -ConnectionBroker "JUMP01.contoso.com" |
    Select-Object UserName, HostServer, SessionState, CreateTime
```

---

## Monitoring e Health AD

### dcdiag — Deep Dive

`dcdiag` è lo strumento diagnostico primario per la salute dei domain controller. Ogni test verifica un aspetto specifico.

```powershell
# Diagnostica completa su tutti i DC del dominio
dcdiag /v /e /c

# Test specifici critici
dcdiag /test:DNS /DnsAll /e          # DNS completo su tutti i DC
dcdiag /test:Replications /v         # Stato replica
dcdiag /test:Services /v             # Servizi AD (NTDS, KDC, DNS, etc.)
dcdiag /test:Advertising /v          # Il DC si pubblicizza correttamente?
dcdiag /test:FsmoCheck /v            # Raggiungibilità dei FSMO role holders
dcdiag /test:RidManager /v           # Stato del RID pool
dcdiag /test:Topology /v             # Topologia di replica KCC
dcdiag /test:NCSecDesc /v            # Permessi sulle naming context
dcdiag /test:KnowsOfRoleHolders /v   # Il DC conosce i FSMO holders?
dcdiag /test:MachineAccount /v       # Account computer del DC nel dominio

# Salvare il report completo
dcdiag /v /e /c > C:\Reports\dcdiag_$(Get-Date -Format 'yyyyMMdd').txt
```

| Test dcdiag | Cosa Verifica | Failure Indica |
|---|---|---|
| `Connectivity` | Connessione LDAP/RPC al DC | Problemi rete/firewall/DNS |
| `Replications` | Stato delle repliche in/out | Replica rotta, errore KCC |
| `Services` | Servizi NTDS, KDC, DNS, DFS, IsmServ, W32Time | Servizio fermo o malfunzionante |
| `Advertising` | Il DC risponde alle query di localizzazione | DC non raggiungibile dai client |
| `FsmoCheck` | I FSMO role holders rispondono | FSMO holder offline |
| `RidManager` | Pool RID disponibile | Pool RID in esaurimento o RID Master irraggiungibile |
| `KccEvent` | Errori del Knowledge Consistency Checker | Problemi generazione topologia replica |
| `SysVolCheck` | SYSVOL è condiviso e raggiungibile | DFSR/FRS non funzionante, SYSVOL non pronto |
| `DFSREvent` | Errori DFSR nel log eventi | Problemi replica SYSVOL o DFS |
| `DNS` | Record DNS necessari per AD | Record SRV mancanti, zone danneggiate |
| `NCSecDesc` | Permessi sulle naming context | ACL corrotte, permessi di replica mancanti |

### repadmin — Comandi Avanzati

```powershell
# Report sintetico di tutte le repliche
repadmin /replsummary

# Stato dettagliato delle repliche di un DC specifico
repadmin /showrepl DC01 /verbose /all

# Visualizzare la coda di replica
repadmin /queue DC01

# Forzare replica immediata di tutte le partizioni
repadmin /syncall DC01 /APed
# A = tutte le partizioni, P = push (notifica ai partner),
# e = cross-site, d = identifica i server per DN

# Mostrare i metadata di replica per un oggetto specifico
repadmin /showobjmeta DC01 "CN=Mario Rossi,OU=Utenti,DC=contoso,DC=com"

# Confrontare gli oggetti tra due DC (detect inconsistenze)
repadmin /showchanges DC01 DC02 "DC=contoso,DC=com" /statistics

# Monitorare il vettore UTD (Up-To-Dateness)
repadmin /showutdvec DC01 "DC=contoso,DC=com"

# Verificare i connection object
repadmin /showconn DC01

# Report di tutte le failure di replica nelle ultime 24 ore
repadmin /showrepl * /csv > C:\Reports\repl_$(Get-Date -Format 'yyyyMMdd').csv
```

### Event ID Critici

| Event ID | Log | Significato | Azione |
|---|---|---|---|
| **1311** | Directory Service | KCC non riesce a generare la topologia di replica | Verificare connettività tra DC e site link |
| **1388** | Directory Service | Oggetto lingering rilevato (replica stale) | Eseguire `repadmin /removelingeringobjects` |
| **1864** | Directory Service | DC non ha replicato per più di tombstone lifetime | Rimuovere il DC e ripromoverlo |
| **2042** | Directory Service | Tombstone lifetime superato, replica disabilitata | Il DC deve essere rimosso dal dominio |
| **2095** | Directory Service | USN rollback rilevato | Il DC deve essere rimosso e ripromosso |
| **4740** | Security | Account lockout | Verificare se è attacco brute force o misconfiguration |
| **4625** | Security | Logon fallito | Analizzare pattern: brute force, credenziali scadute |
| **4769** | Security | TGS request (Kerberoasting detection con RC4) | Verificare se RC4 è usato per account con SPN |
| **4768** | Security | TGT request (AS-REP roasting se pre-auth disabilitata) | Verificare account senza pre-authentication |
| **4662** | Security | Operazione su oggetto AD (DCSync detection) | Verificare GUID di replica nel campo ObjectType |
| **5136** | Security | Modifica di un oggetto AD | Audit delle modifiche su oggetti critici |
| **5141** | Security | Eliminazione di un oggetto AD | Audit delle eliminazioni |
| **1644** | Directory Service | Query LDAP costosa (se diagnostics abilitato) | Ottimizzare la query o indicizzare l'attributo |

### Performance Counter AD

```powershell
# Counter critici per il monitoring dei DC
$counters = @(
    "\NTDS\LDAP Searches/sec"
    "\NTDS\LDAP Successful Binds/sec"
    "\NTDS\LDAP Client Sessions"
    "\NTDS\DRA Inbound Bytes Total/sec"
    "\NTDS\DRA Outbound Bytes Total/sec"
    "\NTDS\DRA Pending Replication Synchronizations"
    "\NTDS\DS Threads in Use"
    "\NTDS\ATQ Estimated Queue Delay"
    "\NTDS\Kerberos Authentications"
    "\NTDS\NTLM Authentications"
    "\Database ==> Instances(NTDSA)\Database Cache % Hit"
    "\Database ==> Instances(NTDSA)\Database Cache Size (MB)"
    "\Database ==> Instances(NTDSA)\I/O Database Reads/sec"
    "\Netlogon\Semaphore Acquires"
    "\Netlogon\Semaphore Waiters"
    "\DNS\Total Query Received/sec"
    "\DNS\Recursive Query Failure/sec"
)

# Raccogliere dati per 5 minuti
$timestamp = Get-Date -Format 'yyyyMMdd_HHmm'
Get-Counter -Counter $counters -SampleInterval 10 -MaxSamples 30 |
    Export-Counter -Path "C:\Reports\AD_Perf_$timestamp.blg" -FileFormat BLG

# Soglie di allarme
# LDAP Searches/sec > 10000: possibile query storm
# ATQ Estimated Queue Delay > 50ms: DC sovraccarico
# DRA Pending Replication Synchronizations > 0 per prolungato: replica in ritardo
# Database Cache % Hit < 90%: RAM insufficiente per la cache ESE
# NTLM Authentications alto: NTLM non disabilitato, target di PtH
# Semaphore Waiters > 0: Netlogon congestionato
```

### AD Replication Status Tool e Script di Monitoraggio

```powershell
# Script di monitoraggio completo — genera un report HTML dello stato AD
$reportPath = "C:\Reports\AD_Health_$(Get-Date -Format 'yyyyMMdd').html"

$html = "<html><head><title>AD Health Report</title></head><body>"
$html += "<h1>AD Health Report — $(Get-Date -Format 'yyyy-MM-dd HH:mm')</h1>"

# 1. Stato DC
$html += "<h2>Domain Controllers</h2>"
$dcs = Get-ADDomainController -Filter * |
    Select-Object Name, Site, IPv4Address, OperatingSystem,
    IsGlobalCatalog, IsReadOnly, Enabled
$html += ($dcs | ConvertTo-Html -Fragment)

# 2. FSMO Roles
$html += "<h2>FSMO Roles</h2>"
$forest = Get-ADForest
$domain = Get-ADDomain
$fsmo = [PSCustomObject]@{
    SchemaMaster        = $forest.SchemaMaster
    DomainNamingMaster  = $forest.DomainNamingMaster
    RIDMaster           = $domain.RIDMaster
    PDCEmulator         = $domain.PDCEmulator
    InfrastructureMaster = $domain.InfrastructureMaster
}
$html += ($fsmo | ConvertTo-Html -Fragment)

# 3. Replica Status
$html += "<h2>Replication Status</h2>"
$replStatus = Get-ADReplicationPartnerMetadata -Target * |
    Select-Object Server, Partner, LastReplicationSuccess,
    ConsecutiveReplicationFailures, LastReplicationResult
$html += ($replStatus | ConvertTo-Html -Fragment)

# 4. RID Pool
$html += "<h2>RID Pool Availability</h2>"
$ridInfo = Get-ADDomainController -Filter * | ForEach-Object {
    $dc = $_.HostName
    $rid = Get-ADObject "CN=RID Set,CN=$($_.Name),OU=Domain Controllers,$(
        (Get-ADDomain).DistinguishedName)" `
        -Properties rIDAllocationPool, rIDPreviousAllocationPool -Server $dc
    [PSCustomObject]@{
        DC = $_.Name
        Pool = $rid.rIDAllocationPool
    }
}
$html += ($ridInfo | ConvertTo-Html -Fragment)

$html += "</body></html>"
$html | Out-File $reportPath -Encoding UTF8

# Pianificare il report giornaliero
# schtasks /create /tn "AD-Health-Report" /sc daily /st 07:00 `
#     /tr "powershell -File C:\Scripts\AD-Health-Report.ps1" /ru SYSTEM
```

---

## Azure AD Connect / Entra Connect

Azure AD Connect (rinominato Entra Connect in Entra ID) è il tool di sincronizzazione tra Active Directory on-premises e Microsoft Entra ID (ex Azure AD).

### Architettura e Sync Rules

```
┌────────────────┐          ┌──────────────────┐          ┌────────────────┐
│   AD DS        │          │  Entra Connect   │          │  Microsoft     │
│   on-premises  │◄────────►│  Sync Engine     │◄────────►│  Entra ID      │
│                │  LDAP    │                  │  HTTPS   │  (Azure AD)    │
│  Forest A      │          │  ┌────────────┐  │          │                │
│  Forest B      │          │  │ Metaverse  │  │          │  Users         │
│  (optional)    │          │  │            │  │          │  Groups        │
└────────────────┘          │  └────────────┘  │          │  Devices       │
                            │  Connectors:     │          │                │
                            │  - AD Connector  │          └────────────────┘
                            │  - AAD Connector │
                            └──────────────────┘
```

```powershell
# Verificare la versione di Entra Connect
Get-ADSyncGlobalSettings | Select-Object @{N='Version';E={
    (Get-Item "C:\Program Files\Microsoft Azure AD Sync\Bin\miiserver.exe").VersionInfo.FileVersion
}}

# Verificare lo stato del sync
Get-ADSyncScheduler | Select-Object AllowedSyncCycleInterval,
    CurrentlyEffectiveSyncCycleInterval, SyncCycleEnabled,
    NextSyncCycleStartTimeInUTC, NextSyncCyclePolicyType

# Forzare un sync cycle
Start-ADSyncSyncCycle -PolicyType Delta  # o Initial per full sync

# Visualizzare le sync rules
Get-ADSyncRule | Select-Object Name, Direction, Connector,
    LinkType, Precedence | Sort-Object Precedence |
    Format-Table -AutoSize

# Verificare gli errori di sync
Get-ADSyncCSObject -ConnectorName "contoso.com" |
    Where-Object { $_.HasSyncError } |
    Select-Object ObjectType, DN, SyncError
```

### Filtering e Scoping

**Filtering basato su OU:** Selezionare specifiche OU da sincronizzare.

**Filtering basato su dominio:** In ambienti multi-dominio, sincronizzare solo domini specifici.

**Filtering basato su attributo:** Sync rules con clausole di scoping (`department -eq "IT"`, `extensionAttribute1 -eq "Sync"`).

**Filtering basato su gruppo:** Sync solo i membri di un gruppo specifico (utile per pilot).

```powershell
# Verificare il filtering OU configurato
Get-ADSyncConnector | ForEach-Object {
    $connector = $_
    Get-ADSyncConnectorPartitionHierarchy -ConnectorName $connector.Name |
        Where-Object { $_.Selected } |
        Select-Object @{N='Connector';E={$connector.Name}},
        Name, Selected, DN
}

# Creare una sync rule personalizzata con scoping filter
# Esempio: sincronizzare solo utenti con extensionAttribute1 = "CloudSync"
# Questo si fa tramite Synchronization Rules Editor (GUI) o:
$rule = New-ADSyncRule `
    -Name "In from AD - User filter by extAttr1" `
    -Direction Inbound `
    -Precedence 50 `
    -SourceObjectType user `
    -TargetObjectType person `
    -Connector (Get-ADSyncConnector -Name "contoso.com").Identifier `
    -LinkType Join `
    -ScopingFilter @(
        New-ADSyncScopingCondition -Attribute extensionAttribute1 -Operator EQUAL -Value "CloudSync"
    )
```

### PHS vs PTA vs Federation

| Metodo | Dove avviene l'autenticazione | Hash in cloud? | Dipendenza on-prem | Complessità |
|---|---|---|---|---|
| **Password Hash Sync (PHS)** | Cloud (Entra ID) | Sì (hash dell'hash) | Nessuna (funziona anche se AD on-prem è offline) | Bassa |
| **Pass-Through Auth (PTA)** | On-premises (agent) | No | Sì (agent deve essere raggiungibile) | Media |
| **Federation (AD FS)** | On-premises (AD FS farm) | No | Sì (AD FS + WAP devono essere online) | Alta |

**Raccomandazione Microsoft 2025:** PHS come metodo primario. PHS offre resilienza, supporta Identity Protection (leaked credentials detection), non richiede infrastruttura aggiuntiva. AD FS è considerato legacy e viene dismesso in favore di PHS + Seamless SSO.

```powershell
# Verificare il metodo di autenticazione configurato
Get-ADSyncGlobalSettings | Select-Object @{N='AuthMethod';E={
    if ($_.Parameters['Microsoft.Synchronize.PasswordSync'].Value -eq 'True') { 'PHS' }
    elseif ($_.Parameters['Microsoft.OptionalFeature.PassThroughAuthentication'].Value -eq 'True') { 'PTA' }
    else { 'Federation / Unknown' }
}}

# Verificare lo stato degli agent PTA
Get-ADSyncPassThroughAuthenticationAgent |
    Select-Object MachineName, Status, LastHeartbeat

# Verificare lo stato del Password Hash Sync
Get-ADSyncAADPasswordSyncConfiguration -SourceConnector "contoso.com"
```

### Seamless SSO e Staging Mode

**Seamless SSO:** Permette agli utenti su dispositivi corporate di autenticarsi automaticamente su servizi cloud senza inserire la password. Utilizza Kerberos: il client ottiene un TGS per il SPN `AZUREADSSOACC$` e lo presenta a Entra ID.

**Staging Mode:** Un secondo server Entra Connect in modalità read-only che esegue import e sync ma non scrive su Entra ID. Usato come standby per il disaster recovery.

```powershell
# Abilitare Seamless SSO
# Tramite wizard di Entra Connect, oppure:
Set-ADSyncDomainJoinedComputerSync -Enable $true

# Verificare che l'account computer AZUREADSSOACC$ esista in AD
Get-ADComputer "AZUREADSSOACC" -Properties ServicePrincipalName,
    PasswordLastSet, whenCreated |
    Select-Object Name, ServicePrincipalName, PasswordLastSet

# IMPORTANTE: la password di AZUREADSSOACC$ deve essere ruotata ogni 30 giorni
# La rotazione automatica non esiste — va scripted
# Riferimento: Microsoft Learn "Seamless SSO - password rollover"

# Staging Mode — configurare un secondo server
# 1. Installare Entra Connect con le stesse impostazioni del server primario
# 2. Nella configurazione, selezionare "Enable staging mode"
# 3. Il server importa e sincronizza, ma non esporta

# Verificare se il server è in staging mode
Get-ADSyncGlobalSettings |
    Select-Object @{N='StagingMode';E={$_.Parameters['Microsoft.Synchronize.StagingMode'].Value}}

# Per fare failover: disabilitare staging mode sul server standby
Set-ADSyncScheduler -StagingModeEnabled $false
# E abilitare staging mode sul vecchio primario (se ancora online)
```

---

## AD Migration

### ADMT e Cross-Forest Migration

Active Directory Migration Tool (ADMT) è lo strumento Microsoft per la migrazione di oggetti (utenti, gruppi, computer) tra domini e forest. Supporta la migrazione con preservazione di SID History per mantenere l'accesso alle risorse durante il periodo di transizione.

```
Forest Sorgente                    Forest Destinazione
┌──────────────────┐               ┌──────────────────┐
│  old.corp.com    │    trust      │  new.contoso.com  │
│  ├─ Users        │◄────────────►│  ├─ Users          │
│  ├─ Groups       │    ADMT      │  ├─ Groups         │
│  └─ Computers    │─────────────►│  └─ Computers      │
└──────────────────┘               └──────────────────┘

Fasi della migrazione:
1. Stabilire trust bidirezionale tra i forest
2. Migrare gruppi (Global → Universal durante migrazione → Global)
3. Migrare utenti con SID History
4. Migrare computer (re-join al nuovo dominio)
5. Migrare permessi NTFS e share (ADMT security translation)
6. Periodo di coesistenza (entrambi i forest attivi)
7. Decommissioning del forest sorgente
```

```powershell
# Pre-requisiti ADMT:
# 1. Trust bidirezionale tra i forest
# 2. Auditing abilitato su entrambi i domini
# 3. SID Filtering disabilitato sul trust (temporaneamente)
# 4. SQL Server per il database ADMT

# Abilitare audit policy per supporto SID History (sul dominio sorgente)
# GPO: Default Domain Controllers Policy
# Computer Configuration > Windows Settings > Security Settings >
#   Local Policies > Audit Policy >
#   Audit account management: Success
#   Audit directory service access: Success

# Verificare che il trust sia configurato per SID History
netdom trust new.contoso.com /domain:old.corp.com /quarantine:No
# NOTA: re-abilitare il quarantine dopo la migrazione!

# Migrazione utenti con ADMT (riga di comando)
admt user /N "mario.rossi" "laura.bianchi" `
    /SD:"old.corp.com" /TD:"new.contoso.com" `
    /TO:"OU=Migrated,OU=Utenti,DC=new,DC=contoso,DC=com" `
    /MSS:YES `            # Migrate SID History
    /TRP:YES `            # Translate Roaming Profile
    /UUR:REPLACE           # Update User Rights

# Migrazione gruppi
admt group /N "GG-Finance-Team" `
    /SD:"old.corp.com" /TD:"new.contoso.com" `
    /TO:"OU=Security,OU=Gruppi,DC=new,DC=contoso,DC=com" `
    /MSS:YES /MGS:YES     # Migrate SID e Group membership

# Security translation (aggiornare ACL su file server, share, registry)
admt security /N "FILESERVER01" `
    /SD:"old.corp.com" /TD:"new.contoso.com" `
    /TOT:Replace `         # Translation Option Type
    /TFS:YES               # Translate File Security
```

### SID History e Trust Setup per Migrazione

SID History preserva i SID del dominio sorgente nell'attributo `sIDHistory` dell'oggetto migrato nel dominio destinazione. Quando l'utente accede a una risorsa con ACL che referenzia il vecchio SID, il token di sicurezza include entrambi i SID (nuovo e storico), garantendo l'accesso senza modificare le ACL.

```powershell
# Verificare SID History di un utente migrato
Get-ADUser "mario.rossi" -Properties SIDHistory |
    Select-Object Name, SID, SIDHistory

# Elencare tutti gli utenti con SID History (post-migrazione)
Get-ADUser -Filter 'SIDHistory -like "*"' -Properties SIDHistory |
    Select-Object Name, SamAccountName,
    @{N='SIDHistory';E={$_.SIDHistory -join '; '}} |
    Format-Table -AutoSize

# Pulizia SID History dopo completamento migrazione (quando non più necessaria)
# ATTENZIONE: rimuovere SID History solo dopo aver aggiornato tutte le ACL
Get-ADUser "mario.rossi" | Set-ADUser -Remove @{SIDHistory = "S-1-5-21-OLD-DOMAIN-SID"}

# Verifica post-migrazione
Get-ADUser "mario.rossi" -Properties SIDHistory, memberOf |
    Select-Object Name, SID, SIDHistory,
    @{N='Groups';E={($_.memberOf | ForEach-Object {
        (Get-ADGroup $_).Name }) -join ', '}}
```

### Domain Rename (rendom)

Il tool `rendom` permette di rinominare un dominio AD esistente. È un'operazione complessa e ad alto rischio che richiede una pianificazione rigorosa.

**Vincoli e prerequisiti:**

| Vincolo | Dettaglio |
|---|---|
| Exchange | **NON supportato** se Exchange Server è presente nel forest — Exchange non supporta il domain rename |
| Forest functional level | Minimo Windows Server 2003 |
| Disponibilità servizi | Tutti i DC devono essere riavviati; tutti i computer membro devono essere riavviati (fino a 2 volte) |
| DFS Namespace | I namespace domain-based devono essere ricreati |
| Certificate Authority | I certificati emessi con il vecchio nome devono essere ri-emessi |
| Cluster | I cluster devono essere distrutti e ricreati |
| Applicazioni | Qualsiasi applicazione con hardcoded domain name richiede riconfigurazione |

```
# Procedura domain rename (schema semplificato)
# 1. Generare il file di stato corrente
rendom /list        # genera domainlist.xml

# 2. Modificare domainlist.xml con i nuovi nomi DNS e NetBIOS

# 3. Caricare le istruzioni di rename
rendom /upload      # carica le istruzioni su tutti i DC

# 4. Preparare i DC
rendom /prepare     # verifica che tutti i DC siano pronti

# 5. Eseguire il rename
rendom /execute     # rinomina il dominio (richiede riavvio di tutti i DC)

# 6. Dopo il riavvio di tutti i DC:
gpfixup /olddns:old.domain.com /newdns:new.domain.com
gpfixup /oldnb:OLDDOMAIN /newnb:NEWDOMAIN

# 7. Riavviare tutti i computer membro (fino a 2 volte)
# 8. Pulizia finale
rendom /clean       # rimuove i riferimenti al vecchio nome
rendom /end         # termina la procedura di rename
```

> **Raccomandazione:** Nella maggior parte degli scenari, la **migrazione cross-forest con ADMT** (descritta sopra) è preferibile al domain rename. La migrazione permette un rollback più semplice, un periodo di coesistenza e non ha le stesse restrizioni legate ad Exchange. Considerare il domain rename solo quando la migrazione non è praticabile (ad esempio, per mantenere i SID invariati).
>
> Riferimento: [Domain Rename](https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/deploy/ad-ds-domain-rename) — consultato: 2026-05-23

### Domain Consolidation

La domain consolidation è il processo di riduzione del numero di domini all'interno di un forest, tipicamente migrando gli oggetti dai domini figlio al dominio root o a un singolo dominio operativo. Le motivazioni principali sono:

- **Riduzione della complessità:** Meno domini = meno trust impliciti, meno FSMO, meno DC da gestire
- **Costo operativo:** Ogni dominio aggiuntivo richiede almeno 2 DC, DNS dedicato, GPO separate
- **Compliance:** Unificare le policy di password e sicurezza è più semplice in un singolo dominio

**Approccio tipico:**

1. Valutare se le ragioni per i domini multipli sono ancora valide (i motivi storici spesso includevano limiti di replica FRS o confini amministrativi che oggi si gestiscono con OU e delega)
2. Creare la struttura OU nel dominio di destinazione
3. Migrare con ADMT preservando SID History
4. Aggiornare ACL e risorse con ADMT Security Translation
5. Decommissionare i DC del dominio consolidato
6. Eseguire metadata cleanup con `ntdsutil` per rimuovere i riferimenti al dominio eliminato

---

## AD Backup e Recovery

> Per la trattazione completa delle procedure di backup e recovery, inclusa la forest recovery, il restore autoritativo/non-autoritativo, il DSRM e il bare metal recovery, vedere → [34-disaster-recovery-ad-pki.md](34-disaster-recovery-ad-pki.md).

Questa sezione offre un riepilogo dei concetti fondamentali.

**System State Backup:** Include il database AD (NTDS.DIT), SYSVOL, registro di sistema, boot files e COM+ registration. È il tipo di backup essenziale per i DC.

```powershell
# Backup System State con wbadmin
wbadmin start systemstatebackup -backupTarget:E: -quiet

# Verificare i backup disponibili
wbadmin get versions -backupTarget:E:

# Scheduling automatico (task schedulato giornaliero)
schtasks /create /tn "AD-SystemState-Backup" /sc daily /st 02:00 `
    /tr "wbadmin start systemstatebackup -backupTarget:E: -quiet" `
    /ru SYSTEM
```

**Authoritative vs Non-Authoritative Restore:**
- **Non-Authoritative:** Ripristina il DC a uno stato precedente, poi la replica aggiorna con le modifiche recenti. Usato per DC corrotto.
- **Authoritative:** Marca gli oggetti ripristinati con version number elevato, forzando la replica verso gli altri DC. Usato per recuperare oggetti eliminati.

**AD Recycle Bin:** Già trattato in dettaglio in [Tombstone Lifetime e AD Recycle Bin](#tombstone-lifetime-e-ad-recycle-bin).

**Forest Recovery:** Procedura strutturata per il ripristino completo di un forest AD dopo un disastro catastrofico. Richiede isolamento di rete, restore del primo DC, metadata cleanup, seize FSMO, e ricostruzione degli altri DC. → Procedura completa in [34-disaster-recovery-ad-pki.md](34-disaster-recovery-ad-pki.md).

### Manutenzione del Database AD (NTDS.DIT)

Il database AD utilizza il motore ESE (Extensible Storage Engine), lo stesso usato da Exchange. Nel tempo, il file `NTDS.DIT` può crescere a causa di frammentazione interna: quando gli oggetti vengono eliminati, lo spazio nel file viene marcato come libero ma il file non si riduce automaticamente. La deframmentazione online avviene automaticamente ogni 12 ore (garbage collection), ma recupera spazio solo all'interno del file. La deframmentazione offline crea una copia compattata del database.

```powershell
# Verificare la dimensione corrente del database
Get-Item "C:\Windows\NTDS\ntds.dit" |
    Select-Object FullName, @{N='SizeMB';E={[math]::Round($_.Length / 1MB, 2)}}
Get-Item "C:\Windows\NTDS\edb.log" |
    Select-Object FullName, @{N='SizeMB';E={[math]::Round($_.Length / 1MB, 2)}}

# Verificare lo spazio libero nel database (senza fermare il servizio)
# Evento 1646 nel log Directory Service dopo il garbage collection
# mostra lo spazio libero recuperato
Get-WinEvent -LogName "Directory Service" -MaxEvents 100 |
    Where-Object { $_.Id -eq 1646 } |
    Select-Object TimeCreated, Message | Format-List
```

**Deframmentazione offline con ntdsutil (RICHIEDE DSRM):**

La deframmentazione offline richiede di avviare il DC in Directory Services Restore Mode (DSRM). Questo rende il DC temporaneamente non disponibile per l'autenticazione. Eseguire questa operazione durante una finestra di manutenzione e solo quando il database mostra una frammentazione significativa (>30% di spazio libero interno).

```
# 1. Riavviare il DC in DSRM (Directory Services Restore Mode)
# bcdedit /set safeboot dsrepair
# shutdown /r /t 0

# 2. Accedere con la password DSRM e aprire ntdsutil
ntdsutil
  activate instance ntds
  files
  info
  # Mostra: dimensione database, spazio libero, percorso log
  compact to C:\Temp\NTDS
  # Crea una copia compattata in C:\Temp\NTDS
  quit
  quit

# 3. Se la compattazione ha successo:
# - Copiare il nuovo ntds.dit sopra il vecchio
# - Eliminare i vecchi log (edb*.log) dalla cartella NTDS
# copy "C:\Temp\NTDS\ntds.dit" "C:\Windows\NTDS\ntds.dit"
# del "C:\Windows\NTDS\edb*.log"

# 4. Verificare l'integrità del database compattato
ntdsutil
  activate instance ntds
  files
  integrity
  # Esegue esentutl /g per verificare le pagine del database
  quit
  quit

# 5. Riavviare in modalità normale
# bcdedit /deletevalue safeboot
# shutdown /r /t 0
```

**Verifica integrità semantica del database:**

```powershell
# Semantic Database Analysis (verifica la coerenza logica degli oggetti AD)
# Richiede DSRM
ntdsutil
  activate instance ntds
  semantic database analysis
  verbose on
  go fixup
  # Corregge automaticamente le inconsistenze trovate
  quit
  quit

# Verifica dell'integrità delle pagine ESE (può essere eseguita online)
# esentutl /g "C:\Windows\NTDS\ntds.dit" /8 /o
# ATTENZIONE: su database grandi può richiedere ore
```

> **Best practice:** La deframmentazione offline è raramente necessaria nei deployment moderni. Lo spazio libero nel database viene riutilizzato automaticamente dal garbage collection. Eseguire la deframmentazione offline solo se: (1) il database è cresciuto significativamente dopo una massiccia eliminazione di oggetti, (2) lo spazio su disco è critico e il file NTDS.DIT occupa significativamente più di quanto necessario, o (3) come parte di una procedura di disaster recovery. (Rif.: https://learn.microsoft.com/en-us/troubleshoot/windows-server/active-directory/compact-directory-database-utility — consultato: 2026-05-23)

---

## Capacity Planning e Ottimizzazione

### Dimensionamento DC

| Parametro | Guideline | Note |
|---|---|---|
| **CPU** | 1 core per 5.000 utenti (approssimativo) | PDC Emulator richiede più CPU |
| **RAM** | Sufficiente per contenere l'intero NTDS.DIT in cache | Controllare `Database Cache % Hit` (target: >95%) |
| **Disco NTDS** | SSD/NVMe dedicato per `C:\Windows\NTDS\` | Separare NTDS.DIT dai log di transazione |
| **Disco SYSVOL** | Separato da NTDS | Volume dedicato per le GPO |
| **Rete** | 1 Gbps minimum tra DC nello stesso sito | Dedicare una NIC per la replica dove possibile |
| **DC per sito** | Minimo 2 (ridondanza) | Siti con >5.000 utenti: considerare un terzo DC |
| **RODC** | Siti remoti con <500 utenti e scarsa sicurezza fisica | Cache solo gli account necessari |

```powershell
# Verificare la dimensione del database AD
Get-Item "C:\Windows\NTDS\ntds.dit" | Select-Object FullName,
    @{N='SizeMB';E={[math]::Round($_.Length / 1MB, 2)}}

# Conteggio oggetti per stima dimensionamento
$domain = (Get-ADDomain).DistinguishedName
$counts = @{
    Users      = (Get-ADUser -Filter * -SearchBase $domain).Count
    Computers  = (Get-ADComputer -Filter * -SearchBase $domain).Count
    Groups     = (Get-ADGroup -Filter * -SearchBase $domain).Count
    GPOs       = (Get-GPO -All).Count
}
$counts | Format-Table -AutoSize

# Verificare Database Cache % Hit
Get-Counter "\Database ==> Instances(NTDSA)\Database Cache % Hit" |
    ForEach-Object { $_.CounterSamples[0].CookedValue }
# < 90% = aggiungere RAM

# Verificare il RID pool disponibile
$ridPool = Get-ADObject "CN=RID Manager$,CN=System,$domain" `
    -Properties rIDAvailablePool
$rIDissued = [int64]($ridPool.rIDAvailablePool -band 0xFFFFFFFF)
$rIDtotal = [int64]($ridPool.rIDAvailablePool -shr 32)
Write-Output "RID issued: $rIDissued / $rIDtotal (remaining: $($rIDtotal - $rIDissued))"
```

### Ottimizzazione Query LDAP

```powershell
# Abilitare query logging (Event ID 1644)
# HKLM\SYSTEM\CurrentControlSet\Services\NTDS\Diagnostics
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Diagnostics" `
    -Name "15 Field Engineering" -Value 5
# Soglia di tempo (millisecondi) per loggare query lente
New-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" `
    -Name "Expensive Search Results Threshold" -Value 1000 -PropertyType DWORD
New-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" `
    -Name "Inefficient Search Results Threshold" -Value 1000 -PropertyType DWORD
New-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" `
    -Name "Search Time Threshold (msecs)" -Value 100 -PropertyType DWORD

# Best practice per query LDAP efficienti:
# 1. Usare attributi indicizzati nei filtri (sAMAccountName, objectClass, objectCategory)
# 2. Evitare filtri con wildcard iniziale (*value) — non usano l'indice
# 3. Specificare objectCategory invece di objectClass (objectCategory è indicizzato,
#    objectClass lo è solo in alcune configurazioni)
# 4. Limitare gli attributi restituiti (Properties / PropertiesToLoad)
# 5. Usare paging per result set grandi

# Esempio: query inefficiente vs efficiente
# INEFFICIENTE: scansione full
# Get-ADUser -Filter 'Description -like "*finance*"'
# EFFICIENTE: attributo indicizzato + scope limitato
# Get-ADUser -Filter 'Department -eq "Finance"' -SearchBase "OU=Utenti,DC=contoso,DC=com"
```

### Placement del Global Catalog

Il Global Catalog (GC) contiene una replica parziale (attributi PAS — Partial Attribute Set) di tutti gli oggetti del forest. È necessario per: Universal Group membership resolution, Exchange GAL lookup, forest-wide searches, logon in ambienti multi-dominio.

**Regole di placement:**
1. Ogni sito con utenti deve avere almeno un GC
2. In ambienti single-domain, tutti i DC dovrebbero essere GC
3. In ambienti multi-dominio, bilanciare il carico di replica (ogni GC replica dati da tutti i domini)
4. L'Infrastructure Master non deve essere GC (in ambienti multi-dominio con DC non-GC)

```powershell
# Elencare tutti i Global Catalog nel forest
Get-ADForest | Select-Object -ExpandProperty GlobalCatalogs

# Verificare se un DC è Global Catalog
Get-ADDomainController -Identity "DC01" | Select-Object Name, IsGlobalCatalog, Site

# Promuovere un DC a Global Catalog
Set-ADObject "CN=NTDS Settings,CN=DC01,CN=Servers,CN=Roma-DC1,CN=Sites,CN=Configuration,$(
    (Get-ADRootDSE).rootDomainNamingContext)" `
    -Replace @{options = 1}  # bit 0 = GC
# Oppure via Server Manager > AD Sites and Services > DC01 > NTDS Settings > Properties > Global Catalog

# Verificare la dimensione del GC vs database locale
# Il GC aggiunge ~50% alla dimensione del NTDS.DIT in ambienti multi-dominio
```

### Integrazione DNS

Active Directory richiede DNS per funzionare. I record SRV sono essenziali per la localizzazione dei DC, dei servizi Kerberos e del Global Catalog.

```powershell
# Verificare i record SRV critici
Resolve-DnsName -Name "_ldap._tcp.dc._msdcs.contoso.com" -Type SRV
Resolve-DnsName -Name "_kerberos._tcp.dc._msdcs.contoso.com" -Type SRV
Resolve-DnsName -Name "_gc._tcp.contoso.com" -Type SRV
Resolve-DnsName -Name "_ldap._tcp.Roma-DC1._sites.dc._msdcs.contoso.com" -Type SRV

# Verificare che tutti i DC abbiano i record DNS registrati
$dcs = Get-ADDomainController -Filter *
foreach ($dc in $dcs) {
    $dns = Resolve-DnsName -Name $dc.HostName -Type A -ErrorAction SilentlyContinue
    [PSCustomObject]@{
        DC   = $dc.Name
        Site = $dc.Site
        IP   = $dns.IPAddress
        DNS  = if ($dns) { 'OK' } else { 'MISSING' }
    }
} | Format-Table -AutoSize

# Forzare la re-registrazione dei record DNS di un DC
nltest /dsregdns
ipconfig /registerdns

# Verificare l'aging/scavenging delle zone DNS
Get-DnsServerZoneAging -Name "contoso.com" |
    Select-Object ZoneName, AgingEnabled, ScavengeServers, NoRefreshInterval, RefreshInterval
```

### Zone DNS AD-Integrated

Le zone DNS integrate in Active Directory (AD-integrated) memorizzano i record DNS direttamente nel database AD invece che in file di zona. Questo offre vantaggi significativi rispetto alle zone file-based.

| Caratteristica | Zone File-Based | Zone AD-Integrated |
|---|---|---|
| **Replica** | Trasferimento di zona DNS (AXFR/IXFR) | Replica AD (multi-master, automatica) |
| **Sicurezza** | Qualsiasi client può aggiornare (se non TSIG) | Solo autenticazione Kerberos (Secure Dynamic Updates) |
| **Fault tolerance** | Master singolo | Multi-master (tutti i DC con DNS scrivono) |
| **Granularità replica** | Intera zona | Per-record (solo le modifiche si replicano) |
| **Partizione di replica** | N/A | ForestDnsZones, DomainDnsZones o custom Application Partition |

```powershell
# Verificare il tipo di zona e la partizione di replica
Get-DnsServerZone | Select-Object ZoneName, ZoneType, IsDsIntegrated,
    ReplicationScope, DirectoryPartitionName | Format-Table -AutoSize

# Convertire una zona file-based in AD-integrated
# ConvertTo-DnsServerPrimaryZone -Name "contoso.com" -ReplicationScope Domain

# Abilitare Secure Dynamic Updates (solo per zone AD-integrated)
Set-DnsServerPrimaryZone -Name "contoso.com" -DynamicUpdate Secure
# Secure = solo client autenticati con Kerberos possono aggiornare i record

# Verificare le Application Directory Partition DNS
Get-ADObject -SearchBase (Get-ADRootDSE).configurationNamingContext `
    -Filter 'objectClass -eq "crossRef" -and systemFlags -band 5' `
    -Properties dnsRoot, nCName |
    Select-Object dnsRoot, nCName
```

### Conditional Forwarders e Stub Zones

**Conditional Forwarders:** Inoltrano le query DNS per un dominio specifico a server DNS designati. Usati per risolvere nomi in forest o domini esterni senza un trust DNS completo.

**Stub Zones:** Copie parziali di una zona che contengono solo i record NS e gli indirizzi glue dei nameserver autoritativi. Si aggiornano automaticamente dal server master e servono come meccanismo di referral.

```powershell
# Creare un conditional forwarder per un forest partner
Add-DnsServerConditionalForwarderZone -Name "partner.com" `
    -MasterServers 10.20.1.10, 10.20.1.11 `
    -ReplicationScope Forest `
    -PassThru

# Elencare i conditional forwarder configurati
Get-DnsServerZone | Where-Object { $_.ZoneType -eq 'Forwarder' } |
    Select-Object ZoneName, MasterServers, IsDsIntegrated

# Creare una stub zone (referral automatico)
Add-DnsServerStubZone -Name "subsidiary.com" `
    -MasterServers 10.30.1.10 `
    -ReplicationScope Domain

# Verificare i forwarder globali (non condizionali)
Get-DnsServerForwarder | Select-Object IPAddress, EnableReordering, Timeout
```

### Split-Brain DNS (Split-Horizon DNS)

Lo split-brain DNS è una configurazione in cui lo stesso nome di dominio viene risolto con indirizzi diversi a seconda che la query provenga dalla rete interna o da Internet. È comune in ambienti dove servizi pubblicati esternamente (webmail, VPN, portali) devono essere raggiungibili sia internamente (IP privato) sia esternamente (IP pubblico).

**Implementazione in AD:** Creare una zona DNS interna AD-integrated con lo stesso nome del dominio pubblico. I client interni risolvono tramite i DC/DNS interni; i client esterni risolvono tramite i DNS pubblici.

```powershell
# Esempio: mail.contoso.com deve risolvere a 10.0.1.50 internamente
# e a 203.0.113.50 esternamente

# Zona interna AD-integrated (già esistente o da creare)
Add-DnsServerResourceRecordA -ZoneName "contoso.com" `
    -Name "mail" -IPv4Address "10.0.1.50"

# La zona pubblica (gestita dal provider DNS esterno) ha:
# mail.contoso.com → 203.0.113.50

# Rischi dello split-brain:
# 1. Drift: i record interni ed esterni possono divergere
# 2. Complessità di troubleshooting (quale DNS sta risolvendo?)
# 3. Certificati TLS: devono essere validi per entrambi gli indirizzi (SAN)

# Verificare la risoluzione dal punto di vista del client interno
Resolve-DnsName "mail.contoso.com" -Server 10.0.1.1  # DC/DNS interno
Resolve-DnsName "mail.contoso.com" -Server 8.8.8.8   # DNS pubblico (confronto)
```

### DNSSEC per Zone AD-Integrated

DNSSEC (Domain Name System Security Extensions) aggiunge firme crittografiche ai record DNS per prevenire il DNS spoofing e il cache poisoning. Windows Server supporta DNSSEC per le zone AD-integrated con distribuzione delle chiavi tramite AD e GPO.

```powershell
# Firmare una zona con DNSSEC (richiede DNS Server su Windows Server 2012+)
# Invoke-DnsServerZoneSign -ZoneName "contoso.com" `
#     -SignWithDefault -PassThru

# Verificare lo stato DNSSEC di una zona
Get-DnsServerDnsSecZoneSetting -ZoneName "contoso.com" |
    Select-Object ZoneName, IsSigned, DenialOfExistence,
    NSec3HashAlgorithm, IsKeyMasterServer

# Verificare le chiavi DNSSEC
Get-DnsServerSigningKey -ZoneName "contoso.com" |
    Select-Object KeyType, CryptoAlgorithm, KeyLength, ActiveKey, NextKey

# Configurare i client per validare DNSSEC tramite GPO
# Computer Configuration > Policies > Windows Settings >
#   Name Resolution Policy Table (NRPT) >
#   Aggiungere regola: .contoso.com → Enable DNSSEC, Require validation

# Verificare la NRPT configurata
Get-DnsClientNrptPolicy | Select-Object Namespace, DnssecValidationRequired
```

> **Nota operativa:** DNSSEC aggiunge complessità significativa alla gestione DNS. Prima di implementarlo, valutare se il threat model dell'organizzazione giustifica il costo operativo. In ambienti puramente interni dove tutto il traffico DNS transita su rete controllata, il beneficio può essere marginale rispetto al rischio di rotture causate da chiavi scadute o misconfigurazioni DNSSEC. DNSSEC è più critico per zone esposte a Internet. (Rif.: https://learn.microsoft.com/en-us/windows-server/networking/dns/deploy/dnssec — consultato: 2026-05-23)

---

## Best Practices

**Mantenere il forest root domain pulito:** In architetture multi-dominio, il forest root domain dovrebbe contenere solo gli account Enterprise Admin e Schema Admin. Nessun utente regolare, nessun server applicativo. Questo riduce la superficie di attacco sul livello più privilegiato del forest.

**Implementare il tiering model:** Separare gli account amministrativi in tier (Tier 0 = Domain Controllers e AD, Tier 1 = Server, Tier 2 = Workstation). Un account Tier 1 non deve mai fare logon su un sistema Tier 2 e viceversa, per prevenire il credential theft e il lateral movement.

**Usare AGDLP per tutti i permessi:** Anche se inizialmente sembra più complesso, il modello AGDLP semplifica enormemente la gestione a lungo termine. Non assegnare mai permessi direttamente agli utenti.

**Abilitare il Recycle Bin immediatamente:** Non c'è ragione per non abilitare il Recycle Bin in qualsiasi ambiente con livello funzionale forest 2008 R2 o superiore. Il costo è minimo e il beneficio in caso di eliminazione accidentale è enorme.

**Documentare la topologia di siti:** Mantenere una mappa aggiornata dei siti, delle subnet associate e dei site link. Subnet mancanti significano che i client non troveranno il DC più vicino, causando autenticazione lenta e traffico di replica non ottimale.

**Monitorare la replica continuamente:** Implementare monitoring automatizzato dello stato di replica con alert per failure. Una replica rotta per più tempo del Tombstone Lifetime può causare la necessità di rimuovere e ricostruire un DC.

**Proteggere gli oggetti critici dall'eliminazione accidentale:** Abilitare il flag "Protect object from accidental deletion" su tutte le OU, i gruppi critici e gli account di servizio.

**Utilizzare gMSA per i service account:** I Group Managed Service Accounts eliminano la necessità di gestire manualmente le password dei service account, riducendo il rischio di credenziali compromesse.

**Implementare audit regolari delle ACL:** Le Access Control List sugli oggetti AD tendono ad accumulare permessi non necessari nel tempo (permission creep). Eseguire audit trimestrali delle ACL sulle OU critiche e sugli oggetti protetti, verificando che i permessi riflettano il principio del minimo privilegio e rimuovendo le deleghe non più necessarie.

**Testare il disaster recovery di AD regolarmente:** Mantenere una procedura testata per il ripristino di Active Directory in caso di forest corruption o compromissione totale. Questo include: backup dello System State di almeno due DC per dominio, procedura di forest recovery documentata (Microsoft KB articolo "Active Directory Forest Recovery"), e un ambiente di test isolato dove eseguire periodicamente simulazioni di recovery per validare i backup e la procedura operativa.

---

## Troubleshooting

### Tabella di Riferimento Rapido

| # | Problema | Sintomo | Causa Probabile | Soluzione |
|---|---|---|---|---|
| 1 | Replica AD fallisce | `repadmin /replsummary` mostra failure | DNS, firewall, USN rollback | Vedi sotto |
| 2 | Trust relationship failed | "Trust relationship between this workstation and the primary domain has failed" | Password account computer scaduta | `Reset-ComputerMachinePassword` |
| 3 | Query LDAP lente | Alto CPU su DC, operazioni AD lente | Filtri non indicizzati, mancanza indici | Event ID 1644, indicizzare attributi |
| 4 | Account lockout ripetuti | Event ID 4740 frequente per lo stesso utente | Credenziali cached, servizio con password vecchia, attacco brute force | Identificare sorgente con Event ID 4740 + `lockoutstatus.exe` |
| 5 | SYSVOL non condiviso | `NETLOGON` e `SYSVOL` share mancanti, GPO non applicate | DFSR non funzionante, Journal Wrap | `dfsrmig /getglobalstate`, Event ID 4012/2213 |
| 6 | FSMO role holder irraggiungibile | `dcdiag /test:FsmoCheck` fallisce | DC con ruolo FSMO offline | Transfer (se online) o Seize (se permanentemente offline) |
| 7 | Global Catalog non disponibile | Logon lento, Universal Group membership non risolta | DC con GC offline, nessun GC nel sito | Verificare GC nel sito, promuovere un DC a GC |
| 8 | Delegation non funziona | Admin delegato non riesce a gestire oggetti nella OU | ACL configurate erroneamente, AdminSDHolder sovrascrive le ACL | Verificare ACL con `Get-Acl`, controllare `adminCount` |
| 9 | GPO non applicata | `gpresult /r` non mostra la GPO attesa | Link GPO mancante, security filtering errato, WMI filter che fallisce | `gpresult /h report.html`, verificare link e filtering |
| 10 | Kerberos authentication failure | Event ID 4771, "KDC_ERR_PREAUTH_FAILED" | Password errata, skew temporale >5 min, SPN duplicato | Verificare time sync (`w32tm /query /status`), SPN (`setspn -X`) |
| 11 | RID pool esaurito | Impossibile creare nuovi oggetti, Event ID 16645 | RID Master irraggiungibile o pool globale esaurito | Contattare RID Master, `dcdiag /test:RidManager` |
| 12 | Oggetti lingering | Event ID 1388/1988, inconsistenze tra DC | DC riconnesso dopo lunga assenza, replica non aggiornata | `repadmin /removelingeringobjects` |
| 13 | Schema extension fallisce | `adprep /forestprep` errore | Schema Master irraggiungibile, permessi insufficienti, conflitto OID | Verificare Schema Master, eseguire come Schema Admin |
| 14 | Subnet mancante in Sites & Services | Client autenticati da DC in sito remoto, traffico WAN eccessivo | Subnet IP non associata a nessun sito AD | Creare la subnet e associarla al sito corretto |
| 15 | Password LAPS non leggibile | `Get-LapsADPassword` restituisce errore | Permessi ACL mancanti, schema LAPS non esteso, GPO non applicata | Verificare schema extension, ACL, `gpresult` sul client |
| 16 | Entra Connect sync in errore | Oggetti non sincronizzati, errori nel Synchronization Service Manager | Attributo duplicato (UPN, proxyAddress), filtering errato | Verificare errori export, correggere duplicati |
| 17 | Protected Users non funziona | Utente nel gruppo ma usa ancora NTLM | DC non è 2012 R2+, client non è 8.1+/2012 R2+ | Verificare functional level, OS del client |

### Problema: Replica AD Fallisce tra Due Domain Controller

**Sintomi**: `repadmin /replsummary` mostra failure su uno o più DC. Gli oggetti creati su un DC non appaiono su un altro.

**Causa**: Problemi di rete (firewall, DNS), USN rollback, database AD corrotto, Tombstone Lifetime scaduto su un DC disconnesso troppo a lungo.

**Soluzione**:

```powershell
# Diagnostica completa della replica
repadmin /replsummary
repadmin /showrepl DC01 /verbose

# Verificare DNS (causa più comune)
dcdiag /test:DNS /DnsAll /e

# Verificare la connettività RPC
dcdiag /test:Connectivity /s:DC01

# Forzare una replica
repadmin /syncall DC01 /APed

# Se USN rollback (Event ID 2095 nel log Directory Service)
# Il DC deve essere RIMOSSO dal dominio e ripromosso

# Verificare il database AD
ntdsutil
  activate instance ntds
  semantic database analysis
  go fixup
```

### Problema: Utente Non Riesce ad Autenticarsi — "Trust Relationship Failed"

**Sintomi**: L'utente riceve "The trust relationship between this workstation and the primary domain has failed" al logon.

**Causa**: La password dell'account computer nel dominio non corrisponde alla password memorizzata localmente sulla macchina. Questo accade quando la macchina è stata offline per più di 30 giorni (default per il rinnovo della password computer) o dopo un ripristino da backup.

**Soluzione**:

```powershell
# Metodo 1: Reset della password computer (richiede credenziali di dominio)
Reset-ComputerMachinePassword -Credential (Get-Credential) -Server "DC01"

# Metodo 2: Rimuovere e riaggiungere al dominio (dalla macchina con admin locale)
Remove-Computer -UnjoinDomainCredential (Get-Credential) -PassThru -Verbose -Restart
# Dopo il riavvio:
Add-Computer -DomainName "contoso.com" -Credential (Get-Credential) -Restart

# Metodo 3: Via netdom (dalla macchina problematica)
netdom resetpwd /Server:DC01 /UserD:contoso\admin /PasswordD:*
```

### Problema: Query LDAP Lente

**Sintomi**: Le operazioni di ricerca in AD (login, query PowerShell, applicazioni) sono lente. Il DC mostra alto utilizzo CPU.

**Causa**: Query LDAP non ottimizzate che scansionano l'intero database senza filtri indicizzati, oppure numero eccessivo di oggetti, oppure indici mancanti per attributi personalizzati.

**Soluzione**:

```powershell
# Abilitare il logging delle query costose
Set-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Diagnostics" `
    -Name "15 Field Engineering" -Value 5

# Verificare gli eventi nel log Directory Service
Get-WinEvent -LogName "Directory Service" -MaxEvents 100 |
    Where-Object { $_.Id -eq 1644 } |
    Select-Object TimeCreated, Message

# Verificare se un attributo è indicizzato
Get-ADObject -SearchBase (Get-ADRootDSE).schemaNamingContext `
    -Filter 'lDAPDisplayName -eq "department"' -Properties searchFlags |
    Select-Object lDAPDisplayName, searchFlags
# searchFlags bit 1 (valore 1) = indicizzato

# Indicizzare un attributo (richiede Schema Admin)
Set-ADObject -Identity "CN=Department,$(
    (Get-ADRootDSE).schemaNamingContext)" -Replace @{searchFlags = 1}
```

### Problema: Account Lockout Ripetuti e Inspiegabili

**Sintomi**: Un utente viene bloccato ripetutamente anche dopo aver cambiato la password. Event ID 4740 frequente.

**Causa**: Credenziali cached su dispositivi (telefono, mappature drive, servizi Windows, RDP salvato), processi o servizi che usano la vecchia password.

**Soluzione**:

```powershell
# Identificare la sorgente del lockout (il DC che ha eseguito il lockout)
Get-WinEvent -LogName Security -FilterXPath `
    "*[System[EventID=4740] and EventData[Data[@Name='TargetUserName']='mario.rossi']]" `
    -MaxEvents 10 |
    Select-Object TimeCreated,
    @{N='LockedUser';E={$_.Properties[0].Value}},
    @{N='CallerComputer';E={$_.Properties[1].Value}}

# Verificare su quale DC è avvenuto il lockout
Get-ADUser "mario.rossi" -Properties LockedOut, AccountLockoutTime,
    LastBadPasswordAttempt, BadLogonCount, BadPwdCount |
    Select-Object Name, LockedOut, AccountLockoutTime,
    LastBadPasswordAttempt, BadLogonCount

# Sbloccare l'account
Unlock-ADAccount -Identity "mario.rossi"

# Tool Microsoft: LockoutStatus.exe e EventCombMT per analisi multi-DC
```

### Problema: SYSVOL Non Condiviso — GPO Non Applicate

**Sintomi**: Le share `NETLOGON` e `SYSVOL` non sono visibili su un DC. Le GPO non vengono applicate ai client.

**Causa**: DFSR non funzionante, Journal Wrap (Event ID 2213), DC appena promosso che non ha completato la replica iniziale.

**Soluzione**:

```powershell
# Verificare lo stato delle share
net share | Select-String "NETLOGON|SYSVOL"

# Verificare lo stato DFSR
Get-DfsReplicationGroup -GroupName "Domain System Volume" |
    Get-DfsrMember | Select-Object ComputerName, DomainName

# Verificare il backlog DFSR
Get-DfsrBacklog -SourceComputerName "DC01" -DestinationComputerName "DC02" `
    -GroupName "Domain System Volume" -Verbose

# Se Journal Wrap (Event ID 2213):
# 1. Fermare DFSR
Stop-Service DFSR
# 2. Rimuovere il database DFSR
Remove-Item "C:\System Volume Information\DFSR\*" -Recurse -Force
# 3. Riavviare DFSR (ricostruirà il database)
Start-Service DFSR
# 4. Monitorare il log DFSR per la re-sincronizzazione
```

### Problema: Subnet IP Non Associata a un Sito AD

**Sintomi**: I client vengono autenticati da DC in siti remoti. Il traffico di autenticazione attraversa link WAN lenti. Event ID 5807 nel System log del DC.

**Causa**: La subnet IP dei client non è associata a nessun sito in AD Sites and Services.

**Soluzione**:

```powershell
# Verificare le subnet configurate
Get-ADReplicationSubnet -Filter * | Select-Object Name, Site | Format-Table -AutoSize

# Identificare subnet mancanti dal log
Get-WinEvent -LogName System -FilterXPath `
    "*[System[EventID=5807]]" -MaxEvents 20 |
    Select-Object TimeCreated, Message

# Aggiungere la subnet mancante
New-ADReplicationSubnet -Name "10.0.5.0/24" -Site "Roma-DC1" `
    -Description "VLAN Client Roma piano 3"

# Verificare che un client trovi il DC corretto
nltest /dsgetsite   # Mostra il sito AD del client corrente
nltest /dsgetdc:contoso.com /site:Roma-DC1  # Verifica quale DC serve il sito
```

### Problema: SPN Duplicato — Autenticazione Kerberos Fallisce

**Sintomi**: Autenticazione Kerberos fallisce per un servizio specifico. Event ID 4771 con codice errore `0x7` (KDC_ERR_S_PRINCIPAL_UNKNOWN) o errori intermittenti.

**Causa**: Più account hanno lo stesso SPN registrato. Kerberos non può determinare quale account usare.

**Soluzione**:

```powershell
# Cercare SPN duplicati nel forest
setspn -X

# Cercare un SPN specifico
setspn -Q MSSQLSvc/SQL01.contoso.com:1433

# Rimuovere l'SPN dall'account errato
setspn -D MSSQLSvc/SQL01.contoso.com:1433 CONTOSO\vecchio-account

# Aggiungere l'SPN all'account corretto (o usare gMSA)
setspn -A MSSQLSvc/SQL01.contoso.com:1433 CONTOSO\gMSA-SQLService$

# Verificare gli SPN di un account
setspn -L CONTOSO\gMSA-SQLService$
```

### Problema: Time Skew Kerberos — Clock Deviation > 5 Minuti

**Sintomi**: Autenticazione Kerberos fallisce. Event ID 4771 con codice `0x18` (KRB_AP_ERR_SKEW). Messaggi "The security database on the server does not have a computer account for this workstation trust relationship".

**Causa**: La differenza di orario tra il client e il DC supera la tolleranza Kerberos (default: 5 minuti).

**Soluzione**:

```powershell
# Verificare la sincronizzazione NTP
w32tm /query /status
w32tm /query /peers

# Forzare la re-sincronizzazione
w32tm /resync /force

# Verificare la gerarchia NTP (il PDC Emulator del root domain è la time source)
w32tm /monitor

# Configurare il PDC Emulator come NTP client esterno
w32tm /config /manualpeerlist:"time.windows.com,0x9" /syncfromflags:MANUAL /update
Restart-Service w32time
```

### Problema: Entra Connect — Oggetti Non Sincronizzati

**Sintomi**: Utenti o gruppi creati in AD on-premises non appaiono in Entra ID dopo il ciclo di sync.

**Causa**: Oggetto fuori scope (OU non selezionata, filtering attributo), attributo duplicato (UPN, proxyAddress), errore nella sync rule.

**Soluzione**:

```powershell
# Verificare errori nel Synchronization Service Manager
# Start > Azure AD Connect > Synchronization Service

# Verificare via PowerShell
Get-ADSyncCSObject -ConnectorName "contoso.com" |
    Where-Object { $_.HasSyncError } |
    Select-Object ObjectType, DN, SyncError | Format-List

# Cercare UPN duplicati (causa comune di errore)
Get-ADUser -Filter * -Properties UserPrincipalName |
    Group-Object UserPrincipalName |
    Where-Object { $_.Count -gt 1 } |
    Select-Object Count, Name

# Forzare un full sync dopo la correzione
Start-ADSyncSyncCycle -PolicyType Initial
```

---

## Group Managed Service Accounts (gMSA)

I Group Managed Service Accounts eliminano la gestione manuale delle password per i service account. Active Directory gestisce automaticamente la rotazione della password (ogni 30 giorni di default), e la password — lunga 240 caratteri random — non è mai conosciuta da nessun amministratore.

```powershell
# Prerequisiti: creare la KDS Root Key (una volta per forest)
# La chiave è disponibile dopo 10 ore dalla creazione (replica AD)
Add-KdsRootKey -EffectiveImmediately
# Per ambienti di test (NON usare in produzione):
Add-KdsRootKey -EffectiveTime ((Get-Date).AddHours(-10))

# Creare un gMSA
New-ADServiceAccount -Name "gMSA-SQLService" `
    -DNSHostName "gMSA-SQLService.contoso.com" `
    -PrincipalsAllowedToRetrieveManagedPassword "GRP-SQL-Servers" `
    -KerberosEncryptionType AES128,AES256 `
    -ServicePrincipalNames "MSSQLSvc/SQL01.contoso.com:1433","MSSQLSvc/SQL01.contoso.com" `
    -Description "Service account gestito per SQL Server"

# Verificare il gMSA
Get-ADServiceAccount -Identity "gMSA-SQLService" -Properties * |
    Select-Object Name, DNSHostName, Enabled, Created,
    PrincipalsAllowedToRetrieveManagedPassword, ServicePrincipalNames

# Installare il gMSA sul server target (eseguire sul server che userà l'account)
Install-ADServiceAccount -Identity "gMSA-SQLService"

# Testare che il server possa recuperare la password
Test-ADServiceAccount -Identity "gMSA-SQLService"
# Output: True = OK, False = il server non è autorizzato

# Configurare un servizio Windows per usare il gMSA
# Nome account: CONTOSO\gMSA-SQLService$ (nota il $ finale)
# Password: lasciare vuota (gestita da AD)

# Elencare tutti i gMSA nel dominio
Get-ADServiceAccount -Filter * -Properties PrincipalsAllowedToRetrieveManagedPassword |
    Select-Object Name, Enabled,
    @{N='AllowedHosts';E={$_.PrincipalsAllowedToRetrieveManagedPassword}} |
    Format-Table -AutoSize
```

### Confronto Service Account Tradizionali vs gMSA

| Aspetto | Account Tradizionale | gMSA |
|---------|---------------------|------|
| Password Management | Manuale, rischio di password statica | Automatica, rotazione ogni 30 giorni |
| Password Strength | Dipende dall'admin | 240 caratteri random |
| SPN Management | Manuale | Automatico |
| Kerberos Delegation | Configurazione manuale | Supporto nativo |
| Multi-server | Password condivisa (rischio) | Password sincronizzata via AD |
| Audit | Difficile tracciare chi conosce la password | Nessun umano conosce la password |
| Recovery | Richiede reset manuale se compromesso | Automatico |

## AdminSDHolder e Protected Groups

AdminSDHolder è un meccanismo di protezione che applica forzatamente un set di autorizzazioni agli account e ai gruppi privilegiati. Ogni 60 minuti, il processo SDProp (Security Descriptor Propagator) confronta le ACL degli oggetti protetti con quelle del container AdminSDHolder e sovrascrive qualsiasi modifica non autorizzata.

```powershell
# Oggetti protetti da AdminSDHolder (adminCount=1)
$protectedObjects = Get-ADObject -Filter 'adminCount -eq 1' -Properties adminCount, objectClass, memberOf |
    Select-Object Name, ObjectClass, adminCount

# Gruppi protetti per default in un dominio:
# - Account Operators
# - Administrators
# - Backup Operators
# - Domain Admins
# - Domain Controllers
# - Enterprise Admins (solo nel root domain)
# - Print Operators
# - Replicator
# - Schema Admins (solo nel root domain)
# - Server Operators

# Problema comune: utenti rimossi da gruppi privilegiati mantengono adminCount=1
# Le ACL restano quelle restrittive di AdminSDHolder, bloccando la delega
# Soluzione: reset manuale di adminCount e re-ereditarietà ACL

# Trovare utenti con adminCount=1 che NON sono più in gruppi privilegiati
$privilegedGroups = @("Domain Admins","Enterprise Admins","Schema Admins","Administrators",
    "Account Operators","Backup Operators","Server Operators","Print Operators")

$allPrivMembers = $privilegedGroups | ForEach-Object {
    Get-ADGroupMember $_ -Recursive -ErrorAction SilentlyContinue
} | Select-Object -ExpandProperty distinguishedName -Unique

$orphanedAdminCount = Get-ADUser -Filter 'adminCount -eq 1' |
    Where-Object { $_.DistinguishedName -notin $allPrivMembers }

$orphanedAdminCount | ForEach-Object {
    Write-Output "Orfano: $($_.Name) ($($_.SamAccountName))"
    # Per correggere (valutare caso per caso):
    # Set-ADUser $_ -Replace @{adminCount=0}
    # Poi re-abilitare l'ereditarietà ACL manualmente
}
```

---

## Esercizi

### Esercizio 1 — Progettazione OU e Delega Tier Model

**Scenario:** Un'azienda con 3 sedi (Roma, Milano, Napoli) e 3 tier amministrativi necessita di una struttura OU completa.

**Compiti:**
1. Progettare la struttura OU su carta, includendo OU separate per Tier 0/1/2, utenti per sede, computer (workstation vs server), gruppi e service account.
2. Implementare la struttura in un lab AD con PowerShell (`New-ADOrganizationalUnit`).
3. Creare i gruppi Global e Domain Local secondo il modello AGDLP per una share finanziaria.
4. Delegare la gestione degli utenti nella OU di Roma a un gruppo IT locale, limitando i permessi a: creazione/eliminazione utenti, reset password, modifica proprietà base.
5. Verificare la delega con `Get-Acl "AD:\OU=..."` e testare con un account non-admin.

**Risultato atteso:** Struttura OU funzionante con delega verificata, nessun utente IT Roma con permessi al di fuori della propria OU.

### Esercizio 2 — Hardening AD e Detection Attacchi

**Scenario:** Eseguire un hardening di base e configurare la detection delle principali tecniche di attacco.

**Compiti:**
1. Identificare tutti gli account utente con SPN (target Kerberoasting): `Get-ADUser -Filter 'ServicePrincipalName -like "*"'`.
2. Identificare account senza Kerberos pre-authentication (AS-REP Roastable): `Get-ADUser -Filter 'DoesNotRequirePreAuth -eq $true'`.
3. Riabilitare la pre-authentication su tutti gli account trovati.
4. Identificare computer con unconstrained delegation (esclusi i DC).
5. Creare una FGPP restrittiva per gli account con SPN obbligatorio (minimo 25 caratteri, rotazione 30 giorni).
6. Aggiungere gli account Tier 0 al gruppo Protected Users.
7. Verificare l'ultimo reset della password `krbtgt` e documentare la procedura di doppio reset.

**Risultato atteso:** Report degli account vulnerabili, FGPP applicata, Protected Users configurato.

### Esercizio 3 — Topologia di Replica Multi-Sito

**Scenario:** Configurare una topologia di replica AD per 4 siti: Roma (hub), Milano, Napoli, Palermo. Roma è connessa direttamente a Milano (100 Mbps) e Napoli (50 Mbps). Napoli è connessa a Palermo (10 Mbps). Milano non ha connessione diretta con Napoli o Palermo.

**Compiti:**
1. Creare i 4 siti e le subnet associate.
2. Creare i site link con costi proporzionali alla banda (costo = 1024/banda in Mbps).
3. Configurare la frequenza di replica appropriata per ciascun site link.
4. Verificare che il KCC generi la topologia corretta con `repadmin /showconn`.
5. Forzare una replica e verificare il risultato con `repadmin /replsummary`.
6. Simulare un failure del site link Roma-Milano e verificare che la replica usa il percorso alternativo Roma→Napoli→Palermo.

**Risultato atteso:** Topologia funzionante con tutti i siti, replica verificata, failover del percorso validato.

### Esercizio 4 — Configurazione Entra Connect con Staging Server

**Scenario:** Configurare Entra Connect con PHS, Seamless SSO e un server in staging mode.

**Compiti:**
1. Installare Entra Connect sul server primario con PHS e Seamless SSO.
2. Configurare il filtering per sincronizzare solo le OU `Utenti` e `Gruppi` (escludere `Admin`, `ServiceAccounts`, `Disabled`).
3. Verificare la sincronizzazione con `Start-ADSyncSyncCycle -PolicyType Delta`.
4. Installare un secondo server Entra Connect in staging mode con la stessa configurazione.
5. Verificare che il server in staging importa e sincronizza ma non esporta.
6. Simulare un failover: disabilitare staging mode sul server secondario.
7. Verificare che la sincronizzazione continua correttamente.

**Risultato atteso:** Due server Entra Connect configurati, failover testato e documentato.

### Esercizio 5 — RODC Deployment e Risposta a Compromissione

**Scenario:** Un'azienda deve installare un RODC in una filiale remota con 80 utenti, connessione WAN a 10 Mbps e nessun personale IT in sede. Il server è in un locale senza controllo accessi fisico.

**Compiti:**
1. Pre-creare l'account RODC con staging (delega a un admin locale remoto).
2. Configurare la Password Replication Policy: consentire solo gli utenti della filiale, negare esplicitamente tutti gli account Tier 0 e i service account critici.
3. Aggiungere un attributo custom contenente dati sensibili al Filtered Attribute Set per impedirne la replica sul RODC.
4. Pre-popolare la cache password degli utenti della filiale prima di una manutenzione WAN programmata.
5. Simulare la compromissione del RODC: identificare le password cached, resettarle, rimuovere il RODC dal dominio.

**Risultato atteso:** RODC funzionante con PRP restrittiva, FAS configurato, procedura di compromissione testata e documentata.

### Domande a Risposta Aperta

1. **Spiega la differenza tra site link bridge e la transitività automatica dei site link.** In quale scenario disabiliteresti la transitività automatica e useresti site link bridge manuali? Fornisci un esempio con topologia hub-and-spoke.

2. **Descrivi il processo completo di estensione dello schema AD**, includendo: chi deve eseguirlo, quali prerequisiti verificare, come testare in ambiente di lab, come monitorare la propagazione e cosa succede se la replica dello schema fallisce su uno dei DC.

3. **Confronta i tre metodi di autenticazione di Entra Connect (PHS, PTA, Federation).** Per ciascuno indica: dove avviene l'autenticazione, requisiti di infrastruttura, comportamento in caso di failure dell'AD on-premises, e in quale scenario è preferibile.

4. **Un attaccante ha ottenuto un Golden Ticket nel tuo ambiente.** Descrivi la procedura completa di risposta all'incidente: come confermi la compromissione, quali azioni immediate prendi, perché il reset di krbtgt deve essere doppio con intervallo di 10+ ore, e quali controlli implementi per prevenire una ricorrenza.

5. **Progetta una strategia DNS completa per un ambiente AD con 3 forest** (produzione, sviluppo, partner esterno) che devono risolversi reciprocamente. Specifica: tipo di zone, conditional forwarder vs stub zone vs delegation, gestione dello split-brain DNS per i servizi pubblicati, e considerazioni su DNSSEC.

### Vero o Falso

1. **V/F:** In un ambiente single-domain dove tutti i DC sono Global Catalog, il posizionamento dell'Infrastructure Master è irrilevante.

<details>
<summary>Risposta</summary>

**VERO.** L'Infrastructure Master aggiorna i riferimenti cross-dominio (phantom objects). Se tutti i DC sono GC, ogni DC ha già una copia parziale di tutti gli oggetti del forest, quindi non ci sono phantom objects da aggiornare. In ambienti single-domain, tutti i DC dovrebbero essere GC e il posizionamento dell'Infrastructure Master non ha impatto operativo.
</details>

2. **V/F:** Le modifiche allo schema AD possono essere annullate eliminando gli attributi o le classi aggiunte per errore.

<details>
<summary>Risposta</summary>

**FALSO.** Le modifiche allo schema sono **irreversibili**. Gli attributi e le classi aggiunti possono essere **disattivati** (impostando `isDefunct = TRUE`) ma non eliminati dal database. L'OID utilizzato non può essere riutilizzato. Per questo motivo, le estensioni dello schema devono essere testate in ambiente di lab prima del deployment in produzione.
</details>

3. **V/F:** Un RODC può essere promosso a detentore di un ruolo FSMO se il DC che lo deteneva va permanentemente offline.

<details>
<summary>Risposta</summary>

**FALSO.** I ruoli FSMO non possono mai essere assegnati a un RODC. I RODC non possono scrivere nel database AD e i ruoli FSMO richiedono la capacità di modificare oggetti (emettere RID, aggiornare lo schema, gestire i cambi password urgenti). Il seize di un ruolo FSMO deve essere eseguito su un DC scrivibile.
</details>

4. **V/F:** Se il SID Filtering è attivo su un forest trust, un utente nel forest trusted con SID History contenente il SID di Enterprise Admins del forest locale otterrà comunque i privilegi di Enterprise Admin.

<details>
<summary>Risposta</summary>

**FALSO.** Il SID Filtering (quarantine) rimuove dal token di autenticazione tutti i SID che non appartengono al dominio di origine dell'utente. Il SID di Enterprise Admins del forest locale verrebbe filtrato dal token, impedendo l'escalation di privilegi. Questa è esattamente la protezione per cui il SID Filtering esiste ed è attivo per default sui forest trust.
</details>

5. **V/F:** La replica inter-site usa la compressione per default, mentre la replica intra-site no.

<details>
<summary>Risposta</summary>

**VERO.** La replica intra-site assume connessioni LAN ad alta velocità e non comprime i dati di replica, privilegiando la bassa latenza. La replica inter-site comprime i dati (tipicamente 40-60% di riduzione) per ottimizzare l'uso della banda WAN. La compressione inter-site si attiva per payload superiori a 50 KB.
</details>

---

## Autovalutazione

<details>
<summary>1. Qual è il confine di sicurezza assoluto in Active Directory: il dominio o il forest?</summary>

Il **forest** è il confine di sicurezza assoluto. Tutti i domini all'interno di un forest condividono lo schema, la Configuration partition, il Global Catalog e hanno trust transitivi bidirezionali automatici. Un Domain Admin di un dominio figlio può potenzialmente compromettere l'intero forest tramite tecniche come SID History injection. Se non si ha fiducia completa in un'entità, deve stare in un forest separato.
</details>

<details>
<summary>2. In un ambiente multi-dominio, dove deve essere posizionato l'Infrastructure Master e perché?</summary>

L'Infrastructure Master deve essere posizionato su un DC che **non è Global Catalog**, in ambienti multi-dominio dove non tutti i DC sono GC. Il motivo: l'Infrastructure Master aggiorna i riferimenti cross-dominio (phantom objects). Se è su un GC, non rileva le differenze perché il GC ha già una copia parziale di tutti gli oggetti. **Eccezione:** se tutti i DC del dominio sono GC (configurazione consigliata in molti ambienti), il posizionamento è irrilevante perché non ci sono phantom objects da aggiornare.
</details>

<details>
<summary>3. Qual è la differenza tra Constrained Delegation (KCD) e Resource-Based Constrained Delegation (RBCD)?</summary>

**Constrained Delegation (KCD):** La configurazione avviene sull'account del server che delega, tramite l'attributo `msDS-AllowedToDelegateTo`. Richiede permessi di Domain Admin per configurare. Il server può impersonare gli utenti solo verso i servizi specificati nella lista.

**RBCD:** La configurazione avviene sulla **risorsa target**, tramite l'attributo `msDS-AllowedToActOnBehalfOfOtherIdentity`. Il proprietario della risorsa decide chi può delegare verso di essa, **senza richiedere Domain Admin**. È il modello moderno e preferito, specialmente per scenari cross-dominio e ambienti cloud-hybrid.
</details>

<details>
<summary>4. Cosa succede se il PDC Emulator va offline e non viene eseguito un seize?</summary>

Impatto immediato e progressivo:
- **Cambio password:** Le password cambiate su altri DC non vengono propagate urgentemente. Un utente che cambia password potrebbe fallire il logon se il DC di autenticazione non ha ancora replicato.
- **Time sync:** La gerarchia NTP è interrotta. I client iniziano a derivare. Dopo 5+ minuti di skew, l'autenticazione Kerberos fallisce.
- **Account lockout:** La policy di lockout non viene applicata centralmente. Un attaccante potrebbe fare brute force su DC diversi senza triggerare il lockout.
- **GPO Editor:** La modifica delle GPO fallisce (il PDC Emulator è il default per la modifica GPO).
- **Compatibilità NTLMv1:** Il fallback NTLM per client legacy fallisce.

**Azione:** Il PDC Emulator è il ruolo FSMO con l'impatto operativo più alto — eseguire il seize immediatamente.
</details>

<details>
<summary>5. Come si previene il Kerberoasting e perché i gMSA sono la mitigazione migliore?</summary>

**Kerberoasting** sfrutta il fatto che qualsiasi utente autenticato può richiedere un TGS per qualsiasi SPN, e il ticket è cifrato con l'hash della password dell'account del servizio. L'attaccante cracka offline l'hash.

**Mitigazioni:**
1. **gMSA (migliore):** Password di 240 caratteri random, ruotata automaticamente ogni 30 giorni. Incrackabile con brute force.
2. Password lunghe (25+ caratteri) per account con SPN che non possono usare gMSA.
3. Forzare AES e disabilitare RC4 (`msDS-SupportedEncryptionTypes = 24`).
4. Monitorare Event ID 4769 con encryption type RC4 (0x17).
5. Ridurre il numero di account utente con SPN — usare account computer dove possibile.

I gMSA sono la mitigazione migliore perché eliminano il problema alla radice: la password non è crackabile.
</details>

<details>
<summary>6. Perché Microsoft ha deprecato il modello ESAE/Red Forest e quali concetti rimangono validi?</summary>

Microsoft ha deprecato il modello ESAE (Enhanced Security Admin Environment) / Red Forest nel 2021 perché:
- **Complessità operativa:** Mantenere un forest separato per l'amministrazione è costoso e complesso.
- **Strategia cloud-first:** Microsoft promuove l'uso di Entra ID Privileged Identity Management (PIM), Conditional Access e cloud-native PAM come alternativa.
- **Drift di sicurezza:** Il forest ESAE tende a essere trascurato nel tempo, diventando esso stesso un vettore di attacco.

**Concetti che rimangono validi:**
- **Tiering model (Tier 0/1/2):** Separazione delle credenziali per livello di criticità.
- **Privileged Access Workstations (PAW):** Workstation dedicate per l'amministrazione.
- **Credential isolation:** Le credenziali di un tier non devono essere esposte su sistemi di un tier inferiore.
- **Deny logon policies:** Bloccare il logon di account privilegiati su sistemi di tier inferiore.

L'approccio moderno combina questi principi con Entra ID PIM, Conditional Access e Defender for Identity.
</details>

<details>
<summary>7. Qual è la differenza tra SID Filtering e Selective Authentication sui forest trust?</summary>

**SID Filtering (Quarantine):** Filtra i SID estranei dal token di autenticazione quando attraversa un trust. Rimuove qualsiasi SID che non appartiene al dominio trusted. Previene attacchi di SID History injection (un utente nel forest trusted con SID History contenente il SID di Enterprise Admins nel forest locale). Attivo per default sui forest trust.

**Selective Authentication:** Limita **quali utenti** del forest trusted possono autenticarsi su **quali risorse** nel forest locale. Invece di permettere l'accesso a tutti i computer (forest-wide authentication), richiede il permesso esplicito "Allowed to Authenticate" su ogni singolo computer. È un controllo più granulare ma richiede più gestione.

In sintesi: SID Filtering protegge dall'injection di SID falsi. Selective Authentication controlla chi può accedere a cosa.
</details>

<details>
<summary>8. Come si configura il monitoring per rilevare un attacco DCSync?</summary>

DCSync simula il protocollo di replica AD (MS-DRSR) usando i permessi "Replicating Directory Changes" e "Replicating Directory Changes All" per estrarre hash di password da qualsiasi DC.

**Detection:**
1. **Audit ACL:** Verificare regolarmente chi ha i permessi di replica sul domain naming context. Solo i Domain Controllers e account di replica autorizzati dovrebbero averli.
2. **Event ID 4662:** Monitorare gli accessi a oggetti AD con le GUID specifiche dei permessi di replica:
   - `1131f6ad-9c07-11d1-f79f-00c04fc2dcd2` — Replicating Directory Changes All
   - `1131f6aa-9c07-11d1-f79f-00c04fc2dcd2` — Replicating Directory Changes
3. **Correlazione:** Se Event ID 4662 viene generato da un account non-DC con queste GUID, è un forte indicatore di DCSync.
4. **Microsoft Defender for Identity** (ex ATA): Detection nativa di DCSync con alert in tempo reale.
5. **repadmin /showrepl:** Verificare che solo i DC noti appaiano come partner di replica.

Il monitoring delle ACL di replica è una delle attività di audit AD più critiche.
</details>

<details>
<summary>9. Quali sono le vulnerabilità AD CS più critiche (ESC1-ESC8) e come si audita?</summary>

Le vulnerabilità AD CS più critiche (catalogate da SpecterOps nel whitepaper "Certified Pre-Owned"):

- **ESC1 (più pericolosa):** Template con flag "Enrollee Supplies Subject" + EKU Client Authentication + enrollment aperto a utenti non privilegiati. Permette a chiunque di richiedere un certificato per qualsiasi utente, incluso Domain Admin.
- **ESC4:** ACL vulnerabili sui template (WriteDACL, WriteOwner) che permettono di modificare un template per abilitare ESC1.
- **ESC6:** Flag `EDITF_ATTRIBUTESUBJECTALTNAME2` sulla CA, che rende qualsiasi template vulnerabile come ESC1.
- **ESC8:** NTLM relay verso il web enrollment HTTP della CA per ottenere certificati Domain Controller.

**Audit con PowerShell:** Cercare template con `msPKI-Certificate-Name-Flag` contenente il bit `CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT` (valore 1) e EKU `1.3.6.1.5.5.7.3.2` (Client Authentication). Verificare il flag `EDITF_ATTRIBUTESUBJECTALTNAME2` con `certutil -config "CA\Name" -getreg policy\EditFlags`. Tool dedicato: **Certify** (GhostPack) per audit automatizzato.
</details>

<details>
<summary>10. In un ambiente con 50.000 utenti e 5 siti, quanti DC servono e come si dimensionano?</summary>

**Guideline di dimensionamento:**

- **Numero DC:** Minimo 2 per sito (ridondanza). Il sito hub con il maggior numero di utenti potrebbe richiedere 3-4 DC. Totale stimato: 10-15 DC.
- **CPU:** ~1 core per 5.000 utenti. Il PDC Emulator richiede più risorse (2-3x). DC nel sito hub: 4-8 core. DC in siti remoti: 2-4 core.
- **RAM:** Sufficiente per la cache ESE (il database NTDS.DIT). Per 50.000 utenti, il database è tipicamente 1-4 GB. Allocare almeno 8-16 GB di RAM per DC per garantire >95% cache hit.
- **Disco:** SSD/NVMe per il volume NTDS. Separare NTDS.DIT dai log di transazione.
- **GC:** Tutti i DC dovrebbero essere Global Catalog se single-domain. In multi-domain, almeno 1 GC per sito.
- **RODC:** Per siti remoti con <500 utenti e scarsa sicurezza fisica.

Monitorare `Database Cache % Hit` (target >95%), `LDAP Searches/sec`, `ATQ Estimated Queue Delay` per validare il dimensionamento.
</details>

---

## Letture

- Microsoft Learn — AD DS Design Guide. https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/plan/ad-ds-design-guide — consultato 2026-05-23
- Microsoft Learn — Active Directory Domain Services Overview. https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/virtual-dc/active-directory-domain-services-overview — consultato 2026-05-23
- Microsoft Learn — Fine-Grained Password Policies. https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/adac/introduction-to-active-directory-administrative-center-enhancements--level-100-#fine_grained_pswd_policy_mgmt — consultato 2026-05-23
- Microsoft Learn — AD Recycle Bin. https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/adac/introduction-to-active-directory-administrative-center-enhancements--level-100-#ad_recycle_bin_mgmt — consultato 2026-05-23
- Microsoft Learn — Active Directory Replication Concepts. https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/replication/active-directory-replication-concepts — consultato 2026-05-23
- Microsoft Learn — Privileged Access Strategy. https://learn.microsoft.com/en-us/security/privileged-access-workstations/privileged-access-strategy — consultato 2026-05-23
- Microsoft Learn — Windows LAPS Overview. https://learn.microsoft.com/en-us/windows-server/identity/laps/laps-overview — consultato 2026-05-23
- Microsoft Learn — Entra Connect (Azure AD Connect) Sync. https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/how-to-connect-sync-whatis — consultato 2026-05-23
- Microsoft Learn — Authentication Policies and Silos. https://learn.microsoft.com/en-us/windows-server/security/credentials-protection-and-management/authentication-policies-and-authentication-policy-silos — consultato 2026-05-23
- Microsoft Learn — AD Forest Recovery Guide. https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/ad-forest-recovery-guide — consultato 2026-05-23
- SpecterOps — Certified Pre-Owned (AD CS abuse). https://posts.specterops.io/certified-pre-owned-d95910965cd2 — consultato 2026-05-23
- AD Security (Sean Metcalf). https://adsecurity.org/ — consultato 2026-05-23
- SANS — Securing Active Directory. https://www.sans.org/white-papers/ — consultato 2026-05-23
- Microsoft Learn — RODC Deployment and Password Replication Policy. https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/deploy/rodc/read-only-domain-controller-updates — consultato: 2026-05-23
- Microsoft Learn — AD Sites and Replication. https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/replication/active-directory-replication-concepts — consultato: 2026-05-23
- Microsoft Learn — DNSSEC Overview. https://learn.microsoft.com/en-us/windows-server/networking/dns/deploy/dnssec — consultato: 2026-05-23
- Microsoft Learn — AD DS Database Compaction. https://learn.microsoft.com/en-us/troubleshoot/windows-server/active-directory/compact-directory-database-utility — consultato: 2026-05-23
- Microsoft Learn — AD Schema Extensions. https://learn.microsoft.com/en-us/windows/win32/ad/extending-the-schema — consultato: 2026-05-23
- Microsoft Learn — ADMT Guide. https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/deploy/upgrade-domain-controllers — consultato: 2026-05-23

---

## Collegamento ad altri moduli

| Modulo | Relazione con questo capitolo |
|---|---|
| [01-active-directory.md](01-active-directory.md) | Fondamenti AD: LDAP, Kerberos, FSMO base, OU, GPO — prerequisito di questo modulo |
| [05-sicurezza-windows.md](05-sicurezza-windows.md) | Hardening, audit policy, Event ID — complementare alla sezione sicurezza |
| [06-rete-windows.md](06-rete-windows.md) | DNS, networking — prerequisito per siti e replica |
| [11-servizi-certificati.md](11-servizi-certificati.md) | PKI e AD CS — complementare alla sezione AD CS abuse |
| [13-azure-ad-identita-ibrida.md](13-azure-ad-identita-ibrida.md) | Identità ibrida, Entra ID — complementare alla sezione Entra Connect |
| [21-group-policy-guida-completa.md](21-group-policy-guida-completa.md) | GPO design e troubleshooting — complementare alla sezione OU e delega |
| [22-powershell-scripting-avanzato.md](22-powershell-scripting-avanzato.md) | Scripting per automazione AD |
| [24-windows-defender-endpoint-security.md](24-windows-defender-endpoint-security.md) | Defender for Identity, endpoint protection |
| [33-multi-forest-ad-trust.md](33-multi-forest-ad-trust.md) | Multi-forest trust, cross-forest authentication — complementare alla sezione Trust Relationships |
| [34-disaster-recovery-ad-pki.md](34-disaster-recovery-ad-pki.md) | Backup, restore, forest recovery — trattazione completa del DR AD |

---

## Glossario

| Termine | Definizione |
|---|---|
| **Forest** | Confine di sicurezza assoluto in AD. Tutti i domini di un forest condividono schema, Configuration partition, Global Catalog e trust transitivi bidirezionali. |
| **FSMO** | Flexible Single Master Operations. 5 ruoli AD (Schema Master, Domain Naming Master, RID Master, PDC Emulator, Infrastructure Master) che devono essere gestiti da un singolo DC alla volta. |
| **Tiering Model** | Modello di sicurezza che suddivide l'infrastruttura in Tier 0 (DC/AD), Tier 1 (Server), Tier 2 (Workstation). Le credenziali di un tier non devono essere esposte su sistemi di un tier inferiore. |
| **AGDLP** | Account → Global Group → Domain Local Group → Permission. Best practice Microsoft per la gestione delle autorizzazioni tramite nesting di gruppi. |
| **FGPP** | Fine-Grained Password Policy. Permette policy di password diverse per gruppi specifici all'interno dello stesso dominio, tramite Password Settings Objects (PSO). |
| **gMSA** | Group Managed Service Account. Account di servizio con password di 240 caratteri gestita automaticamente da AD, rotazione ogni 30 giorni. |
| **AdminSDHolder** | Meccanismo di protezione che applica forzatamente un set di ACL agli account e gruppi privilegiati ogni 60 minuti (processo SDProp). |
| **Kerberoasting** | Tecnica di attacco che sfrutta la possibilità di richiedere TGS per SPN associati a account utente, per crackare offline l'hash della password del servizio. |
| **DCSync** | Tecnica di attacco che simula il protocollo di replica AD per estrarre hash di password da qualsiasi DC. Richiede permessi di replica. |
| **Golden Ticket** | TGT Kerberos forgiato con l'hash di krbtgt. Permette di impersonare qualsiasi utente. Mitigazione: doppio reset della password krbtgt. |
| **RBCD** | Resource-Based Constrained Delegation. Modello di delega Kerberos configurato sulla risorsa target tramite `msDS-AllowedToActOnBehalfOfOtherIdentity`. |
| **SID Filtering** | Meccanismo di sicurezza sui trust che rimuove i SID estranei dai token di autenticazione, prevenendo attacchi di SID History injection. |
| **KCC** | Knowledge Consistency Checker. Processo automatico che genera la topologia di replica tra i DC, creando connection objects ottimali. |
| **ISTG** | Inter-Site Topology Generator. Il DC in ogni sito designato a generare la topologia di replica inter-site per conto del KCC. |
| **Bridgehead Server** | DC designato come punto di contatto per la replica inter-site. Riceve le modifiche dal sito remoto e le distribuisce ai DC locali. |
| **PAW** | Privileged Access Workstation. Workstation dedicata e hardenizzata per l'amministrazione, isolata dalla rete utente, senza accesso Internet. |
| **ESAE** | Enhanced Security Admin Environment (Red Forest). Architettura deprecata da Microsoft (2021) per l'isolamento delle credenziali privilegiate in un forest separato. I concetti di tiering rimangono validi. |
| **Tombstone** | Stato di un oggetto AD eliminato. L'oggetto perde la maggior parte degli attributi ma il GUID persiste per il Tombstone Lifetime (default 180 giorni) prima della purge definitiva. |
| **Entra Connect** | Nuovo nome di Azure AD Connect. Tool di sincronizzazione tra AD on-premises e Microsoft Entra ID (ex Azure AD). Supporta PHS, PTA e Federation. |
| **PHS** | Password Hash Sync. Metodo di autenticazione Entra Connect che sincronizza un hash dell'hash NTLM delle password in cloud. Raccomandato da Microsoft come metodo primario. |
| **AD CS** | Active Directory Certificate Services. Ruolo Windows Server per l'implementazione di una PKI enterprise integrata con AD. Le vulnerabilità ESC1-ESC8 sono una superficie di attacco critica. |
| **RODC** | Read-Only Domain Controller. DC con database AD in sola lettura, progettato per siti remoti con scarsa sicurezza fisica. Supporta Password Replication Policy per il caching selettivo delle credenziali. |
| **Site Link** | Oggetto AD che rappresenta la connessione logica tra due o più siti AD. Definisce il costo, la frequenza di replica e la schedule per la replica inter-site. |
| **USN** | Update Sequence Number. Contatore univoco per DC che traccia ogni modifica al database AD. Usato dal protocollo di replica per determinare quali modifiche devono essere replicate. Un USN rollback causa quarantena del DC. |
| **Credential Guard** | Tecnologia VBS (Virtualization-Based Security) che isola gli hash NTLM e i TGT Kerberos in un processo protetto (lsaIso.exe), inaccessibile anche da codice kernel compromesso. |
| **FAS** | Filtered Attribute Set. Elenco degli attributi AD che non vengono mai replicati su un RODC, controllato tramite il bit 512 di `searchFlags`. Impedisce che dati sensibili raggiungano siti fisicamente insicuri. |
| **DNSSEC** | Domain Name System Security Extensions. Aggiunge firme crittografiche ai record DNS per prevenire spoofing e cache poisoning. Supportato su Windows Server per zone AD-integrated. |
| **Split-Brain DNS** | Configurazione in cui lo stesso nome di dominio risolve in indirizzi diversi a seconda che la query provenga dalla rete interna (IP privato) o da Internet (IP pubblico). |
| **Site Link Bridge** | Oggetto AD che raggruppa esplicitamente site link per controllare la transitività della replica. Necessario solo quando la transitività automatica dei site link è disabilitata. |
| **ESE** | Extensible Storage Engine. Motore di database utilizzato da Active Directory (NTDS.DIT) e Exchange. Supporta transazioni ACID, caching, e deframmentazione online/offline. |
| **DSRM** | Directory Services Restore Mode. Modalità di avvio speciale dei DC che ferma i servizi AD e permette la manutenzione offline del database (deframmentazione, restore autoritativo). Richiede una password DSRM dedicata. |
| **Deferred Index** | Meccanismo per cui la costruzione di un nuovo indice su un attributo AD avviene in background senza bloccare il servizio. L'indice non è disponibile per le query fino al completamento della costruzione. |
| **SDProp** | Security Descriptor Propagator. Processo che ogni 60 minuti confronta le ACL degli oggetti protetti (adminCount=1) con quelle del container AdminSDHolder e sovrascrive le modifiche non autorizzate. |
| **Conditional Forwarder** | Configurazione DNS che inoltra le query per un dominio specifico a server DNS designati, usata per la risoluzione cross-forest senza configurare zone secondarie o delegation complete. |
