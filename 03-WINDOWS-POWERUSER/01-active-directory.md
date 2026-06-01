# Active Directory — Guida Completa

> **Modulo 01** · **Aggiornamento:** 2026-05-22

> **Modulo del corso:** Amministrazione Windows enterprise
> **Prerequisiti:** [06-rete-windows.md](06-rete-windows.md), [00-guida-allo-studio.md](00-guida-allo-studio.md), [08-permessi-e-accesso.md](08-permessi-e-accesso.md)
> **Obiettivi di apprendimento:**
> 1. Comprendere l'architettura di AD DS: foreste, domini, trust e ruoli FSMO
> 2. Progettare e gestire Sites & Subnets per ottimizzare la replica
> 3. Amministrare oggetti AD tramite GUI, PowerShell e LDAP
> 4. Diagnosticare problemi di replica e autenticazione con dcdiag e repadmin
> 5. Applicare il Tier Model e il principio del minimo privilegio in ambienti AD
> **Tempo stimato:** lettura 45 min · lab 60 min
> **Livello:** proficient
> **Ultimo aggiornamento:** 2026-05-23

## Idee guida
1. **Forest = security boundary; Domain = replication boundary.**
2. **5 ruoli FSMO: Schema, DomainNaming, RID, PDC, Infrastructure.**
3. **`dcdiag /v` + `repadmin /replsummary` mandatory.**
4. **Sites & Subnets per ottimizzare replication.**
5. **LDAP è il linguaggio nativo di AD — padroneggiarlo è obbligatorio.**
6. **DNS non funziona → AD non funziona. Senza eccezioni.**
7. **Kerberos è il protocollo primario; NTLM è il fallback da eliminare.**
8. **Least Privilege + Tier Model = difesa in profondità per AD.**


## Indice

- [Panoramica](#panoramica)
- [Architettura Active Directory](#architettura-active-directory)
  - [Componenti Fondamentali](#componenti-fondamentali)
  - [Database Active Directory (NTDS.DIT)](#database-active-directory-ntdsdit)
  - [Partizioni del Database](#partizioni-del-database)
  - [Global Catalog](#global-catalog)
- [Foreste, Domini, Alberi e Trust](#foreste-domini-alberi-e-trust)
  - [Gerarchia Logica](#gerarchia-logica)
  - [Alberi (Trees)](#alberi-trees)
  - [Relazioni di Trust](#relazioni-di-trust)
  - [Livelli Funzionali](#livelli-funzionali)
- [FSMO Roles — Approfondimento](#fsmo-roles--approfondimento)
  - [Dettaglio Ruoli](#dettaglio-ruoli)
  - [Trasferimento e Seize](#trasferimento-e-seize)
  - [Impatto della Perdita di un Ruolo FSMO](#impatto-della-perdita-di-un-ruolo-fsmo)
- [Struttura LDAP](#struttura-ldap)
  - [Distinguished Names](#distinguished-names)
  - [Schema AD — Classi e Attributi](#schema-ad--classi-e-attributi)
  - [OID e Schema Extension](#oid-e-schema-extension)
  - [Global Catalog e Partial Attribute Set](#global-catalog-e-partial-attribute-set)
- [Organizational Unit e Struttura](#organizational-unit-e-struttura)
  - [Design delle OU](#design-delle-ou)
  - [Gestione OU con PowerShell](#gestione-ou-con-powershell)
- [Utenti, Gruppi e Computer](#utenti-gruppi-e-computer)
  - [Gestione Utenti](#gestione-utenti)
  - [Gestione Gruppi](#gestione-gruppi)
  - [Group Managed Service Accounts (gMSA)](#group-managed-service-accounts-gmsa)
  - [Computer Objects](#computer-objects)
- [Group Policy — Fondamenti](#group-policy--fondamenti)
  - [Architettura GPO](#architettura-gpo)
  - [Ordine di Elaborazione (LSDOU)](#ordine-di-elaborazione-lsdou)
  - [Gestione GPO](#gestione-gpo)
  - [GPO Comuni](#gpo-comuni)
- [Group Policy — Avanzato](#group-policy--avanzato)
  - [Security Filtering e WMI Filtering](#security-filtering-e-wmi-filtering)
  - [WMI Filter](#wmi-filter)
  - [Loopback Processing](#loopback-processing)
  - [Group Policy Preferences](#group-policy-preferences)
  - [Central Store per ADMX](#central-store-per-admx)
  - [Starter GPO](#starter-gpo)
- [GPO Troubleshooting](#gpo-troubleshooting)
- [Sites e Replica](#sites-e-replica)
  - [Configurazione Sites](#configurazione-sites)
  - [Replica Intra-Site vs Inter-Site](#replica-intra-site-vs-inter-site)
  - [Knowledge Consistency Checker (KCC)](#knowledge-consistency-checker-kcc)
  - [Bridgehead Server](#bridgehead-server)
  - [Replica Urgente](#replica-urgente)
  - [Monitoraggio Replica — repadmin Deep Dive](#monitoraggio-replica--repadmin-deep-dive)
- [Kerberos e Autenticazione](#kerberos-e-autenticazione)
  - [Flusso Kerberos Dettagliato](#flusso-kerberos-dettagliato)
  - [Diagnostica Kerberos](#diagnostica-kerberos)
  - [NTLM — Il Fallback da Eliminare](#ntlm--il-fallback-da-eliminare)
- [Sicurezza Active Directory](#sicurezza-active-directory)
  - [Kerberoasting — Attacco e Difesa](#kerberoasting--attacco-e-difesa)
  - [NTLM Relay — Attacco e Mitigazione](#ntlm-relay--attacco-e-mitigazione)
  - [Protected Users Group](#protected-users-group)
  - [AdminSDHolder e SDProp](#adminsdholder-e-sdprop)
  - [LAPS — Local Administrator Password Solution](#laps--local-administrator-password-solution)
  - [Credential Caching e Protezione](#credential-caching-e-protezione)
- [Delega Amministrativa](#delega-amministrativa)
  - [Modello di Delega su OU](#modello-di-delega-su-ou)
  - [Delega con PowerShell](#delega-con-powershell)
  - [Least Privilege Design](#least-privilege-design)
- [AD Recycle Bin](#ad-recycle-bin)
  - [Abilitazione](#abilitazione)
  - [Ripristino Oggetti](#ripristino-oggetti)
  - [Tombstone e Ciclo di Vita degli Oggetti Eliminati](#tombstone-e-ciclo-di-vita-degli-oggetti-eliminati)
- [LDAP Query e Integrazione](#ldap-query-e-integrazione)
  - [Query LDAP con PowerShell](#query-ldap-con-powershell)
  - [Query LDAP Avanzate](#query-ldap-avanzate)
  - [Connessione da Sistemi Non-Windows](#connessione-da-sistemi-non-windows)
- [DNS Integrato con AD](#dns-integrato-con-ad)
  - [Architettura DNS in Active Directory](#architettura-dns-in-active-directory)
  - [Zona _msdcs e Record SRV](#zona-_msdcs-e-record-srv)
  - [Zone AD-Integrated — Scope di Replica](#zone-ad-integrated--scope-di-replica)
  - [Conditional Forwarder e Stub Zone](#conditional-forwarder-e-stub-zone)
  - [DNS Scavenging e Manutenzione](#dns-scavenging-e-manutenzione)
  - [Diagnostica DNS per AD](#diagnostica-dns-per-ad)
- [Azure AD Connect e Identita Ibrida](#azure-ad-connect-e-identita-ibrida)
  - [Topologie di Sincronizzazione](#topologie-di-sincronizzazione)
  - [Metodi di Autenticazione](#metodi-di-autenticazione)
  - [Staging Mode](#staging-mode)
- [AD Certificate Services — Integrazione](#ad-certificate-services--integrazione)
- [Cmdlet PowerShell AD — Riferimento](#cmdlet-powershell-ad--riferimento)
- [Best Practices e Design](#best-practices-e-design)
  - [Principi di Design](#principi-di-design)
  - [Checklist per Nuovi Deployment](#checklist-per-nuovi-deployment)
- [Troubleshooting — 25+ Problemi Comuni](#troubleshooting--25-problemi-comuni)
- [FAQ — Domande Frequenti](#faq--domande-frequenti)

---

## Panoramica

Active Directory Domain Services (AD DS) e il servizio di directory Microsoft che costituisce il pilastro di ogni infrastruttura enterprise Windows. Fornisce un repository centralizzato per identita, risorse di rete e policy di sicurezza. AD DS e un database distribuito LDAP-compliant che integra autenticazione Kerberos, replica multi-master, Group Policy e risoluzione DNS.

AD DS non e un singolo servizio: e un ecosistema composto da componenti interdipendenti. Ogni Domain Controller ospita una copia del database NTDS.DIT, agisce come KDC (Key Distribution Center) Kerberos, server DNS integrato e motore di applicazione delle Group Policy. La comprensione profonda di ciascun componente e delle interazioni tra essi e cio che distingue un amministratore competente da un operatore.

### Perche AD e Critico

- **Autenticazione centralizzata**: ogni logon Windows in un dominio passa attraverso AD.
- **Autorizzazione**: i gruppi di sicurezza AD determinano l'accesso a file, stampanti, applicazioni, database.
- **Policy Management**: le Group Policy permettono di gestire centralmente decine di migliaia di endpoint.
- **Service Discovery**: tramite DNS integrato, ogni client trova automaticamente i DC, i Global Catalog, i servizi Kerberos.
- **Base per tutto il resto**: Exchange, SharePoint, SCCM/MECM, PKI, RADIUS/NPS — tutti dipendono da AD.

### Prerequisiti per questo Modulo

- Conoscenza di networking (TCP/IP, DNS, subnetting).
- Familiarita con Windows Server (installazione, ruoli, servizi).
- Esperienza base con PowerShell.
- Comprensione dei concetti di autenticazione e autorizzazione.

---

## Architettura Active Directory

### Componenti Fondamentali

```
Active Directory Domain Services
├── Domain Controller (DC)
│   ├── Database AD (NTDS.DIT)          → C:\Windows\NTDS\
│   ├── SYSVOL                           → C:\Windows\SYSVOL\
│   ├── Kerberos KDC                     → Autenticazione
│   └── DNS Server (integrato)           → Risoluzione nomi
├── Schema
│   ├── Classi oggetto (user, computer, group...)
│   └── Attributi (sAMAccountName, mail, memberOf...)
├── Global Catalog (GC)
│   └── Subset attributi di TUTTI gli oggetti della foresta
└── FSMO Roles (5 ruoli)
    ├── Schema Master (1 per foresta)
    ├── Domain Naming Master (1 per foresta)
    ├── PDC Emulator (1 per dominio)
    ├── RID Master (1 per dominio)
    └── Infrastructure Master (1 per dominio)
```

Ogni Domain Controller e un peer in un sistema di replica multi-master: qualsiasi DC puo accettare modifiche (con l'eccezione delle operazioni FSMO). Le modifiche vengono propagate a tutti gli altri DC tramite il protocollo di replica AD basato su USN (Update Sequence Number) e timestamp.

### Database Active Directory (NTDS.DIT)

```
C:\Windows\NTDS\
├── ntds.dit              → Database ESE (Extensible Storage Engine)
├── edb.chk              → Checkpoint file
├── edb*.log             → Transaction log
├── edbres*.jrs          → Log di riserva (spazio garantito per shutdown pulito)
└── temp.edb             → File temporaneo per operazioni
```

Il database e basato su ESE (Jet Blue), lo stesso motore di Exchange. Ogni operazione di scrittura viene prima registrata nei transaction log, poi applicata al database (write-ahead logging). Questo garantisce consistenza anche in caso di crash.

```powershell
# Dimensione corrente del database
Get-Item "C:\Windows\NTDS\ntds.dit" | Select-Object Name, @{N='SizeMB';E={[math]::Round($_.Length/1MB,2)}}

# Deframmentazione offline (richiede Directory Services offline — DSRM)
# Arrestare il servizio AD DS, poi:
# ntdsutil → activate instance ntds → files → compact to C:\Temp\NTDS
# Copiare il file compattato al posto dell'originale
```

### Partizioni del Database

Il database NTDS.DIT contiene diverse partizioni, ciascuna con un diverso scope di replica:

| Partizione | Contenuto | Replica |
|------------|-----------|---------|
| **Schema** | Definizioni classi e attributi | Tutti i DC della foresta |
| **Configuration** | Topologia sites, servizi, collegamenti | Tutti i DC della foresta |
| **Domain** | Oggetti del dominio (utenti, gruppi, computer, OU) | Solo DC del dominio |
| **ForestDnsZones** | Zone DNS con scope foresta | Tutti i DC DNS della foresta |
| **DomainDnsZones** | Zone DNS con scope dominio | Tutti i DC DNS del dominio |
| **Application** | Partizioni custom (es. TAPI, custom apps) | DC designati |

```powershell
# Elencare le partizioni di replica
Get-ADReplicationPartnerMetadata -Target DC01 -Partition *

# Elencare le naming context
repadmin /showrepl DC01
# Mostra: DC=corp,DC=contoso,DC=com
#         CN=Configuration,DC=corp,DC=contoso,DC=com
#         CN=Schema,CN=Configuration,DC=corp,DC=contoso,DC=com
#         DC=ForestDnsZones,DC=corp,DC=contoso,DC=com
#         DC=DomainDnsZones,DC=corp,DC=contoso,DC=com
```

### Global Catalog

Il Global Catalog (GC) e un DC speciale che contiene una copia parziale (Partial Attribute Set) di TUTTI gli oggetti di TUTTI i domini della foresta. Serve per:

- **Ricerche cross-domain**: un utente in `eu.corp.contoso.com` cerca un contatto in `us.corp.contoso.com`.
- **Universal Group Membership**: durante il logon, il GC viene interrogato per risolvere i gruppi universali.
- **UPN resolution**: il GC risolve il UserPrincipalName per il logon.
- **Exchange Global Address List**: la GAL si basa sul GC.

```powershell
# Verificare quali DC sono Global Catalog
Get-ADDomainController -Filter {IsGlobalCatalog -eq $true} |
    Select-Object Name, Site, IsGlobalCatalog

# Promuovere un DC a Global Catalog
Set-ADObject -Identity (Get-ADDomainController DC02).NTDSSettingsObjectDN `
    -Replace @{options=1}

# Il GC opera sulla porta 3268 (LDAP) e 3269 (LDAPS)
# Test connettivita GC:
Test-NetConnection DC01 -Port 3268
```

**Raccomandazione**: in un ambiente single-domain, rendere TUTTI i DC anche Global Catalog. In un ambiente multi-domain, avere almeno un GC per site.

---

## Foreste, Domini, Alberi e Trust

### Gerarchia Logica

```
Foresta (corp.contoso.com)           → Confine di sicurezza MASSIMO
├── Dominio Root (corp.contoso.com)   → Schema + Enterprise Admins
│   ├── OU Amministrazione
│   └── OU Servizi
├── Dominio Child (eu.corp.contoso.com)
│   ├── OU Italia
│   └── OU Germania
└── Dominio Child (us.corp.contoso.com)
    ├── OU New York
    └── OU California

Foresta Partner (partner.com)
└── Trust con corp.contoso.com
```

**Foresta**: il confine di sicurezza massimo in AD. Tutti i domini in una foresta condividono lo stesso schema, la stessa partizione Configuration, e hanno trust transitivi automatici tra loro. Un compromesso di un Domain Admin in qualsiasi dominio della foresta puo potenzialmente compromettere l'intera foresta (via schema modification, configuration change, SID history abuse).

**Dominio**: il confine di replica per la partizione Domain. Ogni dominio ha i propri DC, la propria policy password (Default Domain Policy), i propri gruppi Domain Admins. E anche un confine di policy, ma NON un vero confine di sicurezza (quel ruolo spetta alla foresta).

### Alberi (Trees)

Un albero (tree) e una gerarchia di domini che condividono un namespace DNS contiguo:

```
Albero 1 (namespace contoso.com):
    corp.contoso.com
    ├── eu.corp.contoso.com
    └── us.corp.contoso.com

Albero 2 (namespace fabrikam.com) nella stessa foresta:
    fabrikam.com
    └── dev.fabrikam.com
```

I domini nello stesso albero sono collegati da trust parent-child automatici e transitivi. I root di alberi diversi nella stessa foresta sono collegati da trust tree-root automatici e transitivi.

### Relazioni di Trust

```powershell
# Visualizzare trust esistenti
Get-ADTrust -Filter *

# Dettaglio trust
Get-ADTrust -Identity "partner.com" | Select-Object *

# Creare trust foresta (bidirezionale)
# Da eseguire su entrambi i lati
netdom trust corp.contoso.com /domain:partner.com /twoway /transitive /add

# Verificare trust
Test-ComputerSecureChannel -Server DC01
nltest /sc_query:corp.contoso.com

# Verificare trust con dominio specifico
nltest /trusted_domains
nltest /sc_verify:partner.com

# Reset del secure channel (se trust rotta)
netdom resetpwd /s:DC01 /ud:corp\admin /pd:*
```

| Tipo Trust | Direzione | Transitivita | Creazione | Uso |
|-----------|-----------|-------------|-----------|-----|
| Parent-Child | Bidirezionale | Transitivo | Automatica | Tra parent e child domain |
| Tree-Root | Bidirezionale | Transitivo | Automatica | Tra tree root domains |
| Forest | Bidirezionale o Mono | Transitivo | Manuale | Tra foreste diverse |
| External | Bidirezionale o Mono | Non transitivo | Manuale | Con domini esterni/legacy NT4 |
| Shortcut | Bidirezionale o Mono | Transitivo | Manuale | Ottimizzazione percorso auth tra rami distanti |
| Realm | Bidirezionale o Mono | Transitivo o no | Manuale | Con Kerberos realm non-Windows (MIT, Linux) |

**SID Filtering**: per default, le forest trust filtrano i SID provenienti dall'altra foresta. Questo previene attacchi tramite SID History injection. Disabilitare il SID Filtering e un rischio di sicurezza significativo.

```powershell
# Verificare stato SID Filtering
netdom trust corp.contoso.com /domain:partner.com /quarantine

# Abilitare SID Filtering (raccomandato)
netdom trust corp.contoso.com /domain:partner.com /quarantine:yes

# Selective Authentication (limita quali utenti dell'altra foresta possono autenticarsi)
netdom trust corp.contoso.com /domain:partner.com /SelectiveAuth:yes
```

### Livelli Funzionali

I livelli funzionali determinano quali funzionalita AD sono disponibili. Alzare il livello funzionale e un'operazione **irreversibile**.

```powershell
# Verificare livello funzionale corrente
(Get-ADForest).ForestMode          # Es: Windows2016Forest
(Get-ADDomain).DomainMode          # Es: Windows2016Domain

# Alzare livello funzionale dominio
Set-ADDomainMode -Identity "corp.contoso.com" -DomainMode Windows2016Domain

# Alzare livello funzionale foresta
Set-ADForestMode -Identity "corp.contoso.com" -ForestMode Windows2016Forest
# ATTENZIONE: operazione irreversibile!
```

| Livello | Funzionalita Sbloccate | DC Minimo |
|---------|----------------------|-----------|
| Windows Server 2012 R2 | Authentication policies, silos, Protected Users group | WS 2012 R2 |
| Windows Server 2016 | Privileged Access Management (PAM), nuovi tipi criptografia Kerberos | WS 2016 |
| Windows Server 2019 | Nessuna nuova funzionalita significativa (allineamento) | WS 2019 |
| Windows Server 2022 | Nessuna nuova funzionalita significativa (allineamento) | WS 2022 |
| Windows Server 2025 | Supporto credenziali aggiornate, miglioramenti sicurezza | WS 2025 |

**Regola critica**: prima di alzare il livello funzionale:
1. Verificare che **tutti** i DC del dominio/foresta eseguano almeno la versione richiesta.
2. Verificare compatibilita applicativa (Exchange, SharePoint, SCCM richiedono livelli specifici).
3. Testare in ambiente lab/staging.
4. Avere un backup System State recente di tutti i DC.
5. Documentare il rollback plan (che nella pratica significa forest recovery da backup).

---

## FSMO Roles — Approfondimento

### Dettaglio Ruoli

I FSMO (Flexible Single Master Operations) sono 5 ruoli che possono essere detenuti da un solo DC alla volta, per operazioni che richiedono un singolo punto di autorita.

```powershell
# Visualizzare tutti i ruoli FSMO
netdom query fsmo

# Oppure PowerShell
Get-ADForest | Select-Object SchemaMaster, DomainNamingMaster
Get-ADDomain | Select-Object PDCEmulator, RIDMaster, InfrastructureMaster
```

#### Schema Master (1 per foresta)

L'unico DC autorizzato a modificare lo schema AD. Lo schema definisce tutte le classi di oggetti (user, computer, group) e i loro attributi.

- **Quando serve**: installazione Exchange, Lync/Skype, SCCM, qualsiasi applicazione che estende lo schema.
- **Se offline**: nessun impatto operativo immediato. Non si possono installare applicazioni che modificano lo schema.
- **Dove posizionarlo**: sul DC root del dominio radice della foresta, nello stesso site del team che gestisce lo schema.

#### Domain Naming Master (1 per foresta)

L'unico DC autorizzato ad aggiungere o rimuovere domini dalla foresta, e gestire i riferimenti cross-reference per i domini.

- **Quando serve**: aggiunta/rimozione domini, creazione application partitions.
- **Se offline**: non si possono aggiungere/rimuovere domini. Operazione rara.
- **Dove posizionarlo**: sullo stesso DC dello Schema Master (raccomandato).

#### PDC Emulator (1 per dominio)

Il ruolo FSMO piu critico per le operazioni quotidiane:

- **Time Source**: il PDC Emulator e la sorgente di tempo autorevole per il dominio. Tutti i client e member server sincronizzano da esso.
- **Password Change**: riceve le modifiche password con priorita. Quando un utente cambia password su DC-A, il DC-A replica immediatamente la modifica al PDC Emulator.
- **Account Lockout**: processa le richieste di lockout/unlock.
- **GPO Editor**: la console GPMC si connette al PDC Emulator per default.
- **Compatibilita legacy**: agisce come PDC per client pre-Windows 2000 (ormai irrilevante).

```powershell
# Il PDC Emulator gestisce la sincronizzazione tempo:
# PDC Emulator → fonte NTP esterna
# Tutti gli altri DC → PDC Emulator
# Client/Member Server → DC del site

# Configurare il PDC Emulator per sincronizzarsi con fonte esterna
w32tm /config /manualpeerlist:"time.windows.com,0x9 time.nist.gov,0x9" `
    /syncfromflags:manual /reliable:YES /update
Restart-Service w32time
w32tm /resync
```

- **Se offline**: impatto significativo. Le modifiche password possono non propagarsi immediatamente, il lockout potrebbe non funzionare correttamente, il tempo potrebbe desincronizzarsi.
- **Dove posizionarlo**: sul DC piu potente, nel site con il maggior numero di utenti.

#### RID Master (1 per dominio)

Assegna pool di RID (Relative Identifier) ai DC. Ogni oggetto creato in AD riceve un SID composto da: Domain SID + RID. Il RID deve essere unico nel dominio.

- **Quando serve**: continuamente — ogni volta che un DC crea un nuovo oggetto.
- **Se offline**: i DC possono continuare a creare oggetti finche il loro pool di RID non si esaurisce (tipicamente ~500 RID per pool).
- **Dove posizionarlo**: sullo stesso DC del PDC Emulator (raccomandato).

```powershell
# Verificare pool RID disponibili
dcdiag /test:ridmanager /v

# Verificare RID rimanenti per il dominio
$domain = Get-ADDomain
$ridInfo = Get-ADObject "CN=RID Manager$,CN=System,$($domain.DistinguishedName)" `
    -Properties rIDAvailablePool
$totalSIDs = $ridInfo.rIDAvailablePool
[int32]$totalSIDsIssued = $totalSIDs / ([math]::Pow(2,32))
[int64]$temp64val = $totalSIDs % ([math]::Pow(2,32))
[int32]$nextRID = $temp64val
Write-Output "RID successivo: $nextRID | RID totali emessi: $totalSIDsIssued"
```

#### Infrastructure Master (1 per dominio)

Aggiorna i riferimenti cross-domain (phantom records). Quando un oggetto di un altro dominio e referenziato nel dominio locale (es. membro di un gruppo), l'Infrastructure Master mantiene aggiornato il DN e il SID di quel riferimento.

- **Quando serve**: in ambienti multi-domain.
- **Se offline**: i riferimenti cross-domain diventano stale. In ambiente single-domain, nessun impatto.
- **Regola CRITICA**: in un ambiente multi-domain, l'Infrastructure Master NON deve risiedere su un Global Catalog (a meno che tutti i DC siano GC).
- **Dove posizionarlo**: su un DC che NON e Global Catalog (in multi-domain). In single-domain, ovunque.

### Trasferimento e Seize

```powershell
# TRASFERIMENTO PIANIFICATO (entrambi i DC online):
# Trasferire singolo ruolo
Move-ADDirectoryServerOperationMasterRole -Identity "DC02" `
    -OperationMasterRole PDCEmulator

# Trasferire piu ruoli contemporaneamente
Move-ADDirectoryServerOperationMasterRole -Identity "DC02" `
    -OperationMasterRole PDCEmulator, RIDMaster, InfrastructureMaster

# Trasferire TUTTI i 5 ruoli
Move-ADDirectoryServerOperationMasterRole -Identity "DC02" `
    -OperationMasterRole SchemaMaster, DomainNamingMaster, PDCEmulator, `
    RIDMaster, InfrastructureMaster

# SEIZE DI EMERGENZA (DC originale offline PERMANENTEMENTE):
Move-ADDirectoryServerOperationMasterRole -Identity "DC02" `
    -OperationMasterRole PDCEmulator -Force

# Via ntdsutil (metodo classico):
# ntdsutil → roles → connections → connect to server DC02 →
# quit → seize PDC → quit → quit
```

### Impatto della Perdita di un Ruolo FSMO

| Ruolo | Impatto se Offline | Seize Sicuro? | Note |
|-------|-------------------|---------------|------|
| Schema Master | Nessun impatto operativo | Si, sempre sicuro | Non fare seize a meno che non serva immediatamente modificare lo schema |
| Domain Naming Master | Non si aggiungono domini | Si, sempre sicuro | Raramente necessario |
| PDC Emulator | Password, lockout, tempo | Si, sempre sicuro | Fare seize il prima possibile |
| RID Master | Esaurimento pool RID | Si, ma il vecchio DC non deve MAI tornare online | Pool RID duplicati = disastro |
| Infrastructure Master | Riferimenti cross-domain stale | Si, sempre sicuro | In single-domain: nessun impatto |

**Regola d'oro del seize**: dopo un seize, il DC originale NON deve MAI essere riconnesso alla rete. Se tornasse online con il ruolo, si avrebbe un conflitto split-brain. L'unica eccezione e il PDC Emulator (il protocollo gestisce il conflitto), ma e comunque sconsigliato.

---

## Struttura LDAP

### Distinguished Names

Ogni oggetto in AD ha un Distinguished Name (DN) univoco che ne identifica la posizione nell'albero LDAP:

```
DN completo:
CN=Mario Rossi,OU=Italia,OU=Utenti,DC=corp,DC=contoso,DC=com

Componenti:
- DC (Domain Component)   → DC=corp,DC=contoso,DC=com (dominio)
- OU (Organizational Unit) → OU=Utenti (unita organizzativa)
- CN (Common Name)        → CN=Mario Rossi (nome oggetto)
- O  (Organization)       → Usato raramente in AD
```

Tipi di nome in AD:

| Tipo | Esempio | Uso |
|------|---------|-----|
| **DN** (Distinguished Name) | `CN=Mario Rossi,OU=Italia,OU=Utenti,DC=corp,DC=contoso,DC=com` | Identificatore LDAP univoco |
| **RDN** (Relative DN) | `CN=Mario Rossi` | Nome relativo nella OU corrente |
| **UPN** (User Principal Name) | `mrossi@corp.contoso.com` | Logon in formato email |
| **sAMAccountName** | `mrossi` | Logon pre-Windows 2000 (DOMAIN\user) |
| **SID** (Security Identifier) | `S-1-5-21-xxx-xxx-xxx-1234` | Identificatore di sicurezza immutabile |
| **GUID** (objectGUID) | `a1b2c3d4-e5f6-...` | Identificatore immutabile (anche se l'oggetto viene rinominato/spostato) |
| **Canonical Name** | `corp.contoso.com/Utenti/Italia/Mario Rossi` | Formato leggibile (DN al contrario con slash) |

```powershell
# Recuperare DN di un utente
(Get-ADUser mrossi).DistinguishedName

# Recuperare tutti i tipi di nome
Get-ADUser mrossi -Properties CanonicalName, ObjectGUID, SID |
    Select-Object Name, DistinguishedName, UserPrincipalName, `
    SamAccountName, SID, ObjectGUID, CanonicalName
```

### Schema AD — Classi e Attributi

Lo schema AD e il blueprint che definisce quali oggetti possono esistere nel database e quali attributi possono avere.

#### Classi

Una classe definisce un tipo di oggetto. Ogni classe ha:
- **Mandatory attributes**: attributi obbligatori (es. `cn` per la classe `user`).
- **Optional attributes**: attributi facoltativi (es. `mail`, `telephoneNumber`).
- **Superclass**: la classe da cui eredita (es. `user` eredita da `organizationalPerson` che eredita da `person` che eredita da `top`).

Classi fondamentali:

| Classe | objectClass | Uso |
|--------|------------|-----|
| `user` | `top;person;organizationalPerson;user` | Account utente |
| `computer` | `top;person;organizationalPerson;user;computer` | Account computer |
| `group` | `top;group` | Gruppi di sicurezza e distribuzione |
| `organizationalUnit` | `top;organizationalUnit` | Contenitori OU |
| `contact` | `top;person;organizationalPerson;contact` | Contatti (no logon) |
| `groupPolicyContainer` | `top;container;groupPolicyContainer` | Oggetti GPO |

#### Attributi

Ogni attributo ha un tipo di dati (stringa, intero, booleano, DN, octect string), un OID univoco, e regole di indicizzazione.

Attributi chiave per la classe `user`:

| Attributo | Tipo | Descrizione |
|-----------|------|-------------|
| `sAMAccountName` | Stringa | Nome logon pre-2000 |
| `userPrincipalName` | Stringa | Nome logon UPN |
| `distinguishedName` | DN | Percorso LDAP completo |
| `memberOf` | Multi-value DN | Gruppi di appartenenza |
| `userAccountControl` | Intero (bitmask) | Flag account (abilitato, locked, password expired...) |
| `pwdLastSet` | Large Integer | Timestamp ultimo cambio password |
| `lastLogonTimestamp` | Large Integer | Ultimo logon (replicato, con latenza ~14 giorni) |
| `lastLogon` | Large Integer | Ultimo logon (NON replicato, per-DC) |
| `whenCreated` | Datetime | Data creazione |
| `whenChanged` | Datetime | Ultima modifica |
| `objectSid` | SID | Security Identifier |
| `objectGUID` | GUID | Identificatore univoco immutabile |

```powershell
# Elencare TUTTI gli attributi di un utente
Get-ADUser mrossi -Properties * | Get-Member -MemberType Property | Select-Object Name

# Elencare le classi dello schema
Get-ADObject -SearchBase "CN=Schema,CN=Configuration,DC=corp,DC=contoso,DC=com" `
    -Filter {objectClass -eq "classSchema"} -Properties lDAPDisplayName |
    Select-Object lDAPDisplayName | Sort-Object lDAPDisplayName

# Elencare gli attributi dello schema
Get-ADObject -SearchBase "CN=Schema,CN=Configuration,DC=corp,DC=contoso,DC=com" `
    -Filter {objectClass -eq "attributeSchema"} -Properties lDAPDisplayName, attributeSyntax |
    Select-Object lDAPDisplayName, attributeSyntax | Sort-Object lDAPDisplayName
```

### OID e Schema Extension

Ogni classe e attributo nello schema ha un OID (Object Identifier) univoco. Microsoft utilizza il prefisso OID `1.2.840.113556.1.x.x`. Le estensioni di schema di terze parti devono usare i propri OID registrati.

```powershell
# Verificare un attributo dello schema per OID
Get-ADObject -SearchBase "CN=Schema,CN=Configuration,DC=corp,DC=contoso,DC=com" `
    -Filter {lDAPDisplayName -eq "mail"} -Properties attributeID, attributeSyntax, isSingleValued

# Estendere lo schema (ESTREMA CAUTELA — irreversibile):
# 1. Registrare un OID aziendale via Microsoft (o generare con script)
# 2. Testare SEMPRE in lab prima
# 3. Backup completo dello schema
# 4. L'operazione richiede membership in Schema Admins
# 5. Solo lo Schema Master puo accettare modifiche
# 6. Le modifiche allo schema sono replicate a TUTTI i DC della foresta
# 7. NON si possono rimuovere attributi/classi — solo disabilitarli
```

### Global Catalog e Partial Attribute Set

Il Global Catalog contiene un sottoinsieme di attributi (Partial Attribute Set — PAS) di tutti gli oggetti della foresta. Solo gli attributi marcati come `isMemberOfPartialAttributeSet = TRUE` nello schema vengono replicati al GC.

```powershell
# Elencare gli attributi inclusi nel Partial Attribute Set (GC)
Get-ADObject -SearchBase "CN=Schema,CN=Configuration,DC=corp,DC=contoso,DC=com" `
    -Filter {isMemberOfPartialAttributeSet -eq $true -and objectClass -eq "attributeSchema"} `
    -Properties lDAPDisplayName | Select-Object lDAPDisplayName | Sort-Object lDAPDisplayName

# Aggiungere un attributo al GC (attenzione: causa replica massiva):
# Set-ADObject -Identity "CN=myCustomAttribute,CN=Schema,CN=Configuration,DC=..." `
#     -Replace @{isMemberOfPartialAttributeSet=$true}
```

---

## Organizational Unit e Struttura

### Design delle OU

Le OU servono a due scopi: **delega amministrativa** e **applicazione GPO**. Il design deve riflettere il modello di delega, non necessariamente l'organigramma aziendale.

```
corp.contoso.com
├── OU=Admin           → Account amministrativi (protezione elevata)
│   ├── OU=T0-Admins   → Tier 0: Domain Admins, Enterprise Admins
│   ├── OU=T1-Admins   → Tier 1: Server admins
│   └── OU=T2-Admins   → Tier 2: Workstation admins
├── OU=Utenti          → Account utente standard
│   ├── OU=Italia
│   ├── OU=Germania
│   └── OU=Spagna
├── OU=Computer
│   ├── OU=Workstation
│   ├── OU=Laptop
│   └── OU=Kiosk
├── OU=Server
│   ├── OU=FileServer
│   ├── OU=WebServer
│   └── OU=DatabaseServer
├── OU=Gruppi
│   ├── OU=Security
│   ├── OU=Distribution
│   └── OU=Ruolo
├── OU=ServiceAccounts  → Account di servizio (gMSA)
└── OU=Disabled         → Account disabilitati (staging per eliminazione)
```

**Principi di design delle OU**:
1. **Delega prima, GPO dopo**: progettare le OU attorno a chi gestisce cosa, non attorno all'organigramma.
2. **Non troppo profonde**: massimo 5-6 livelli di nesting. Ogni livello aggiunge complessita di debug GPO.
3. **Non troppo piatte**: una singola OU con 10.000 oggetti rende la gestione difficile.
4. **Separare utenti da computer**: applicano GPO diverse e hanno deleghe diverse.
5. **OU dedicata per admin**: gli account privilegiati devono essere in OU separate con GPO restrittive.
6. **OU Disabled/Quarantine**: per gli account in fase di offboarding, prima di eliminarli.

### Gestione OU con PowerShell

```powershell
# Creare OU
New-ADOrganizationalUnit -Name "Italia" -Path "OU=Utenti,DC=corp,DC=contoso,DC=com" `
    -ProtectedFromAccidentalDeletion $true -Description "Utenti sede Italia"

# Creare struttura completa
$base = "DC=corp,DC=contoso,DC=com"
$topOUs = @("Admin", "Utenti", "Computer", "Server", "Gruppi", "ServiceAccounts", "Disabled")
foreach ($ou in $topOUs) {
    New-ADOrganizationalUnit -Name $ou -Path $base -ProtectedFromAccidentalDeletion $true
}

# Creare sotto-OU
$subOUs = @{
    "Admin"    = @("T0-Admins", "T1-Admins", "T2-Admins")
    "Computer" = @("Workstation", "Laptop", "Kiosk")
    "Server"   = @("FileServer", "WebServer", "DatabaseServer")
    "Gruppi"   = @("Security", "Distribution", "Ruolo")
}
foreach ($parent in $subOUs.Keys) {
    foreach ($child in $subOUs[$parent]) {
        New-ADOrganizationalUnit -Name $child `
            -Path "OU=$parent,$base" -ProtectedFromAccidentalDeletion $true
    }
}

# Spostare oggetto in un'altra OU
Move-ADObject -Identity "CN=Mario Rossi,OU=Italia,OU=Utenti,DC=corp,DC=contoso,DC=com" `
    -TargetPath "OU=Germania,OU=Utenti,DC=corp,DC=contoso,DC=com"

# Elencare OU con i loro oggetti figli
Get-ADOrganizationalUnit -Filter * | ForEach-Object {
    $count = (Get-ADObject -SearchBase $_.DistinguishedName -SearchScope OneLevel -Filter *).Count
    [PSCustomObject]@{
        OU = $_.Name
        DN = $_.DistinguishedName
        ObjectCount = $count
    }
}

# Rimuovere protezione da eliminazione accidentale (prima di eliminare una OU)
Set-ADOrganizationalUnit -Identity "OU=Obsoleta,DC=corp,DC=contoso,DC=com" `
    -ProtectedFromAccidentalDeletion $false
Remove-ADOrganizationalUnit -Identity "OU=Obsoleta,DC=corp,DC=contoso,DC=com" -Recursive
```

---

## Utenti, Gruppi e Computer

### Gestione Utenti

```powershell
# Creare utente
New-ADUser -Name "Mario Rossi" -GivenName "Mario" -Surname "Rossi" `
    -SamAccountName "mrossi" -UserPrincipalName "mrossi@corp.contoso.com" `
    -Path "OU=Italia,OU=Utenti,DC=corp,DC=contoso,DC=com" `
    -AccountPassword (ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force) `
    -Enabled $true -ChangePasswordAtLogon $true

# Creare utenti in bulk da CSV
Import-Csv "C:\Users\utenti.csv" | ForEach-Object {
    New-ADUser -Name "$($_.Nome) $($_.Cognome)" `
        -GivenName $_.Nome -Surname $_.Cognome `
        -SamAccountName $_.Username `
        -UserPrincipalName "$($_.Username)@corp.contoso.com" `
        -Path $_.OU `
        -AccountPassword (ConvertTo-SecureString $_.Password -AsPlainText -Force) `
        -Enabled $true
}

# Modificare utente
Set-ADUser -Identity "mrossi" -Title "System Administrator" -Department "IT" `
    -Office "Milano" -EmailAddress "mrossi@contoso.com"

# Disabilitare utente (offboarding)
Disable-ADAccount -Identity "mrossi"
Move-ADObject -Identity (Get-ADUser mrossi).DistinguishedName `
    -TargetPath "OU=Disabled,DC=corp,DC=contoso,DC=com"

# Cercare utenti
Get-ADUser -Filter 'Department -eq "IT"' -Properties Title, Department |
    Select-Object Name, SamAccountName, Title, Department

# Utenti inattivi da 90 giorni
$threshold = (Get-Date).AddDays(-90)
Get-ADUser -Filter {LastLogonDate -lt $threshold -and Enabled -eq $true} `
    -Properties LastLogonDate | Select-Object Name, LastLogonDate

# Utenti con password scaduta
Search-ADAccount -PasswordExpired | Select-Object Name, PasswordExpired

# Utenti con password che non scade mai
Get-ADUser -Filter {PasswordNeverExpires -eq $true -and Enabled -eq $true} `
    -Properties PasswordNeverExpires | Select-Object Name, SamAccountName

# Utenti bloccati
Search-ADAccount -LockedOut | Select-Object Name, LockedOut, LastLogonDate

# Reset password
Set-ADAccountPassword -Identity "mrossi" -Reset `
    -NewPassword (ConvertTo-SecureString "NewP@ss1!" -AsPlainText -Force)
Unlock-ADAccount -Identity "mrossi"

# Forzare cambio password al prossimo logon
Set-ADUser -Identity "mrossi" -ChangePasswordAtLogon $true

# Impostare scadenza account (per contrattisti temporanei)
Set-ADAccountExpiration -Identity "contractor01" -DateTime "2026-12-31"
```

### Gestione Gruppi

```powershell
# Tipi di gruppo:
# Security → per permessi su risorse (file share, NTFS, applicazioni)
# Distribution → per liste distribuzione email (no permessi di sicurezza)

# Scope gruppi:
# Domain Local  → permessi su risorse del dominio locale, membri da qualsiasi dominio
# Global        → membri SOLO del dominio, usabile ovunque nella foresta
# Universal     → membri da qualsiasi dominio, usabile ovunque (replicato in GC)
```

**Strategia di nesting AGDLP/AGUDLP**:

```
AGDLP (Account → Global → Domain Local → Permission):
    Account utente
    └── Global Group (raggruppa per ruolo/funzione)
        └── Domain Local Group (raggruppa per risorsa)
            └── Permission sulla risorsa (NTFS, share, app)

AGUDLP (con Universal — per ambienti multi-domain):
    Account utente
    └── Global Group (per dominio)
        └── Universal Group (cross-domain)
            └── Domain Local Group (risorsa)
                └── Permission
```

```powershell
# Creare gruppo globale (ruolo)
New-ADGroup -Name "GG-IT-Staff" -GroupScope Global -GroupCategory Security `
    -Path "OU=Security,OU=Gruppi,DC=corp,DC=contoso,DC=com" `
    -Description "Gruppo globale staff IT"

# Creare gruppo domain local (risorsa)
New-ADGroup -Name "DL-FileShare-Read" -GroupScope DomainLocal -GroupCategory Security `
    -Path "OU=Security,OU=Gruppi,DC=corp,DC=contoso,DC=com" `
    -Description "Accesso lettura file share"

# Creare gruppo universale (cross-domain)
New-ADGroup -Name "UG-AllIT" -GroupScope Universal -GroupCategory Security `
    -Path "OU=Security,OU=Gruppi,DC=corp,DC=contoso,DC=com" `
    -Description "Tutti gli IT cross-domain"

# Aggiungere membri
Add-ADGroupMember -Identity "GG-IT-Staff" -Members "mrossi", "gbianchi"

# Nesting AGDLP
Add-ADGroupMember -Identity "DL-FileShare-Read" -Members "GG-IT-Staff"

# Elencare membri (ricorsivo)
Get-ADGroupMember -Identity "GG-IT-Staff" -Recursive | Select-Object Name, ObjectClass

# Trovare gruppi di un utente
(Get-ADUser mrossi -Properties MemberOf).MemberOf

# Report completo gruppi con membri
Get-ADGroup -Filter {GroupCategory -eq "Security"} | ForEach-Object {
    $members = Get-ADGroupMember -Identity $_ -ErrorAction SilentlyContinue
    [PSCustomObject]@{
        Gruppo = $_.Name
        Scope = $_.GroupScope
        MembriCount = ($members | Measure-Object).Count
    }
}
```

### Group Managed Service Accounts (gMSA)

```powershell
# Creare KDS Root Key (una volta per foresta)
Add-KdsRootKey -EffectiveImmediately
# In produzione: Add-KdsRootKey -EffectiveTime ((Get-Date).AddHours(-10))

# Creare gMSA
New-ADServiceAccount -Name "gMSA-WebApp" -DNSHostName "gMSA-WebApp.corp.contoso.com" `
    -PrincipalsAllowedToRetrieveManagedPassword "SRV01$" `
    -ServicePrincipalNames "HTTP/webapp.corp.contoso.com"

# Permettere a piu server di usare il gMSA
Set-ADServiceAccount -Identity "gMSA-WebApp" `
    -PrincipalsAllowedToRetrieveManagedPassword "SRV01$","SRV02$","SRV03$"

# Installare gMSA sul server
Install-ADServiceAccount -Identity "gMSA-WebApp"
Test-ADServiceAccount -Identity "gMSA-WebApp"
# In servizio: usare corp\gMSA-WebApp$ come account, senza password

# Vantaggi gMSA:
# - Password gestita automaticamente (cambio ogni 30 giorni)
# - Password complessa (240 caratteri random)
# - Non puo essere usato per logon interattivo
# - Supportato da IIS, SQL Server, Task Scheduler, servizi Windows
```

### Computer Objects

```powershell
# Pre-stage computer account (per WDS/MDT)
New-ADComputer -Name "WKS-IT-001" -SamAccountName "WKS-IT-001$" `
    -Path "OU=Workstation,OU=Computer,DC=corp,DC=contoso,DC=com"

# Trovare computer inattivi (90 giorni)
$threshold = (Get-Date).AddDays(-90)
Get-ADComputer -Filter {LastLogonDate -lt $threshold} -Properties LastLogonDate, OperatingSystem |
    Select-Object Name, LastLogonDate, OperatingSystem

# Report computer per sistema operativo
Get-ADComputer -Filter * -Properties OperatingSystem, OperatingSystemVersion |
    Group-Object OperatingSystem | Select-Object Name, Count | Sort-Object Count -Descending

# Verificare secure channel di un computer
Test-ComputerSecureChannel -Verbose

# Reset secure channel (se rotto)
Test-ComputerSecureChannel -Repair -Credential (Get-Credential)
# Oppure:
Reset-ComputerMachinePassword -Server DC01 -Credential (Get-Credential)

# Rimuovere dal dominio (PowerShell remoto)
Remove-Computer -ComputerName "WKS-IT-001" -UnjoinDomainCredential (Get-Credential) -Force
```

---

## Group Policy — Fondamenti

### Architettura GPO

Una Group Policy Object (GPO) e composta da due parti:

```
GPO
├── Group Policy Container (GPC)     → Oggetto in AD (LDAP)
│   ├── Link alla OU/dominio/site
│   ├── Versione (AD side)
│   ├── Security filtering
│   └── WMI Filter link
└── Group Policy Template (GPT)      → Cartella in SYSVOL
    ├── Machine\                     → Computer Configuration
    │   ├── Registry.pol            → Registry-based policies
    │   ├── Scripts\                → Startup/Shutdown scripts
    │   ├── Security\               → Security settings
    │   └── comment.cmtx            → Commenti
    └── User\                       → User Configuration
        ├── Registry.pol
        ├── Scripts\                → Logon/Logoff scripts
        └── Documents & Settings\
```

### Ordine di Elaborazione (LSDOU)

```
Ordine di elaborazione GPO (LSDOU):
1. Local Policy                → gpedit.msc (su ogni macchina)
2. Site Policy                 → GPO collegate al Site AD
3. Domain Policy               → GPO collegate al dominio
4. OU Policy                   → GPO collegate alla OU (dalla piu esterna alla piu interna)
   └── Child OU Policy         → Piu specifica, sovrascrive le precedenti

Regola: l'ultima GPO applicata VINCE (sovrascrive le precedenti)
Eccezione: "Enforced" forza una GPO anche contro GPO piu specifiche
Eccezione: "Block Inheritance" sulla OU blocca GPO superiori (ma non Enforced)
```

**Ordine di precedenza dentro un livello**: se piu GPO sono linkate alla stessa OU, quella con Link Order 1 ha la precedenza piu alta (si applica per ultima, cioe vince).

**Conflitto Enforced vs Block Inheritance**: Enforced vince sempre. Se una GPO e marcata Enforced a livello di dominio, si applica anche se la OU ha Block Inheritance.

### Gestione GPO

```powershell
# Creare GPO
New-GPO -Name "SEC-PasswordPolicy" -Comment "Policy password per il dominio"

# Collegare GPO a una OU
New-GPLink -Name "SEC-PasswordPolicy" `
    -Target "OU=Utenti,DC=corp,DC=contoso,DC=com"

# Collegare GPO al dominio
New-GPLink -Name "SEC-PasswordPolicy" -Target "DC=corp,DC=contoso,DC=com"

# Impostare Enforced
Set-GPLink -Name "SEC-PasswordPolicy" -Target "DC=corp,DC=contoso,DC=com" -Enforced Yes

# Impostare Block Inheritance su una OU
Set-GPInheritance -Target "OU=Eccezioni,OU=Utenti,DC=corp,DC=contoso,DC=com" -IsBlocked Yes

# Report HTML di una GPO
Get-GPOReport -Name "SEC-PasswordPolicy" -ReportType Html -Path "C:\Reports\GPO-Password.html"

# Report di tutte le GPO
Get-GPO -All | ForEach-Object {
    Get-GPOReport -Guid $_.Id -ReportType Html -Path "C:\Reports\$($_.DisplayName).html"
}

# Elenco di tutte le GPO con stato link
Get-GPO -All | ForEach-Object {
    $links = (Get-GPOReport -Guid $_.Id -ReportType XML | Select-Xml -XPath "//q1:LinksTo" `
        -Namespace @{q1="http://www.microsoft.com/GroupPolicy/Settings/ReportExtension"}).Node
    [PSCustomObject]@{
        Nome = $_.DisplayName
        Stato = $_.GpoStatus
        LinksCount = ($links | Measure-Object).Count
    }
}

# Backup GPO
Backup-GPO -All -Path "C:\Backup\GPO"

# Ripristino GPO
Restore-GPO -Name "SEC-PasswordPolicy" -Path "C:\Backup\GPO"

# Copiare GPO (per template)
Copy-GPO -SourceName "SEC-PasswordPolicy" -TargetName "SEC-PasswordPolicy-Test"
```

### GPO Comuni

```powershell
# PASSWORD POLICY (solo su Default Domain Policy o PSO)
# Computer Configuration → Policies → Windows Settings → Security Settings → Account Policies
# - Minimum password length: 12
# - Password complexity: Enabled
# - Maximum password age: 90 days
# - Account lockout threshold: 5 attempts
# - Account lockout duration: 30 minutes

# FINE-GRAINED PASSWORD POLICY (PSO) — Livello funzionale 2008+
New-ADFineGrainedPasswordPolicy -Name "PSO-AdminAccounts" `
    -Precedence 10 -MinPasswordLength 16 -ComplexityEnabled $true `
    -MaxPasswordAge "60.00:00:00" -LockoutThreshold 3 -LockoutDuration "00:30:00" `
    -LockoutObservationWindow "00:30:00" -ReversibleEncryptionEnabled $false

Add-ADFineGrainedPasswordPolicySubject -Identity "PSO-AdminAccounts" -Subjects "Domain Admins"

# Verificare quale PSO si applica a un utente
Get-ADUserResultantPasswordPolicy -Identity "mrossi"

# WINDOWS UPDATE via GPO
# Computer → Administrative Templates → Windows Components → Windows Update
# - Configure Automatic Updates: 4 (Auto download and schedule install)
# - Specify intranet update service: http://wsus-server:8530

# RESTRICT USB
# Computer → Administrative Templates → System → Removable Storage Access
# - All Removable Storage: Deny All Access

# DISABLE COMMAND PROMPT
# User → Administrative Templates → System
# - Prevent access to the command prompt: Enabled

# MAP NETWORK DRIVE (Preferences)
# User → Preferences → Windows Settings → Drive Maps
# - Action: Update, Letter: S:, Location: \\SRV01\Shared

# DISABLE SMBv1
# Computer → Administrative Templates → Network → Lanman Workstation
# - Enable insecure guest logons: Disabled
# Computer → Administrative Templates → Network → Lanman Server
# - SMB 1.0/CIFS File Sharing Support: Disabled

# AUDIT POLICY
# Computer → Windows Settings → Security Settings → Advanced Audit Policy
# - Account Logon: Audit Kerberos Authentication Service: Success, Failure
# - Account Logon: Audit Credential Validation: Success, Failure
# - Logon/Logoff: Audit Logon: Success, Failure
# - Object Access: Audit File System: Success, Failure
```

---

## Group Policy — Avanzato

### Security Filtering e WMI Filtering

```powershell
# Security Filtering (applicare GPO solo a un gruppo)
# 1. Rimuovere "Authenticated Users" dalla GPO
Set-GPPermission -Name "GPO-Software-Office" -PermissionLevel None `
    -TargetName "Authenticated Users" -TargetType Group

# 2. Aggiungere il gruppo target con Apply
Set-GPPermission -Name "GPO-Software-Office" -PermissionLevel GpoApply `
    -TargetName "GG-Office-Users" -TargetType Group

# 3. IMPORTANTE: "Authenticated Users" deve avere almeno Read per funzionare
Set-GPPermission -Name "GPO-Software-Office" -PermissionLevel GpoRead `
    -TargetName "Authenticated Users" -TargetType Group

# NOTA CRITICA su Security Filtering e Kerberos:
# Il computer deve poter leggere la GPO (nel SYSVOL).
# Se la GPO ha SOLO user-side settings, il COMPUTER deve comunque avere Read.
# Altrimenti la GPO non viene scaricata.
```

### WMI Filter

```
# Filtrare GPO per tipo sistema operativo
# Solo Windows 11:
SELECT * FROM Win32_OperatingSystem WHERE Version LIKE "10.0.2%" AND ProductType = "1"

# Solo Windows Server 2022:
SELECT * FROM Win32_OperatingSystem WHERE Version LIKE "10.0.20348%" AND ProductType = "3"

# Solo laptop:
SELECT * FROM Win32_Battery WHERE BatteryStatus IS NOT NULL

# Solo macchine con almeno 8 GB RAM:
SELECT * FROM Win32_ComputerSystem WHERE TotalPhysicalMemory >= 8589934592

# Solo macchine con disco SSD:
SELECT * FROM Win32_DiskDrive WHERE MediaType = "Fixed hard disk media"

# ProductType values:
# 1 = Workstation
# 2 = Domain Controller
# 3 = Server (non DC)
```

```powershell
# Creare WMI Filter via PowerShell
$wmiFilterName = "WMI-Windows11-Only"
$wmiQuery = 'SELECT * FROM Win32_OperatingSystem WHERE Version LIKE "10.0.2%" AND ProductType = "1"'
$wmiNamespace = "root\CIMv2"

# L'oggetto WMI Filter risiede in AD come oggetto msWMI-Som
$wmiFilter = New-Object Microsoft.GroupPolicy.WmiFilter
# (Piu pratico creare via GPMC GUI)
```

### Loopback Processing

Il Loopback Processing e una funzionalita avanzata che permette di applicare le User Configuration settings di GPO collegate al **computer** (invece che all'utente). Fondamentale per ambienti come kiosk, sale conferenze, terminal server.

```
Scenario: sala conferenze con PC "KIOSK-01" in OU=Kiosk
Problema: gli utenti che fanno logon su KIOSK-01 ottengono le LORO GPO utente,
          non quelle specifiche per il kiosk.

Soluzione: Loopback Processing sulla GPO collegata a OU=Kiosk.

DUE MODALITA:

1. REPLACE Mode:
   - Le User Configuration settings delle GPO dell'utente vengono IGNORATE
   - Si applicano SOLO le User Configuration settings delle GPO del computer
   - Uso: kiosk, chioschi, laboratori — controllo totale sull'esperienza utente

2. MERGE Mode:
   - Le User Configuration settings delle GPO dell'utente si applicano PRIMA
   - Le User Configuration settings delle GPO del computer si applicano DOPO
   - In caso di conflitto, le settings del computer VINCONO
   - Uso: terminal server — personalizzazione utente + override specifici del server
```

```
# Configurare Loopback Processing via GPO:
# Computer Configuration → Administrative Templates → System → Group Policy
# → Configure user Group Policy loopback processing mode
# - Enabled
# - Mode: Replace (o Merge)
```

### Group Policy Preferences

```
# Preferences vs Policy:
# - Policy: impone un'impostazione, l'utente non puo cambiarla (icona con bordo rosso)
# - Preference: configura un default, l'utente puo modificarla (icona senza bordo)

# Azioni Preferences:
# - Create: crea se non esiste, non modifica se esiste
# - Replace: elimina e ricrea
# - Update: crea se non esiste, modifica se esiste (la piu comune)
# - Delete: rimuove

# Item-Level Targeting (Preferences):
# Condizioni per applicare una Preference solo se:
# - Computer in un certo gruppo/OU
# - Sistema operativo specifico
# - Indirizzo IP in un range
# - Variabile d'ambiente presente
# - Registry value match
# - Battery present (laptop)
# - RAM > N GB
# - Disk space > N GB
# - Time range specifico
# - Combinazioni AND/OR di condizioni multiple

# Esempio: creare shortcut desktop solo per utenti del gruppo Marketing
# User → Preferences → Windows Settings → Shortcuts
# + Item-Level Targeting: Security Group IS GG-Marketing
```

### Central Store per ADMX

```powershell
# Creare il Central Store per template ADMX (una volta per dominio)
# Copia i template da un client Windows recente
$source = "C:\Windows\PolicyDefinitions"
$dest = "\\corp.contoso.com\SYSVOL\corp.contoso.com\Policies\PolicyDefinitions"

Copy-Item -Path $source -Destination $dest -Recurse
# Ora tutti i DC vedranno gli stessi template ADMX

# Per aggiungere ADMX di terze parti (Chrome, Firefox, Office):
# Copiare i file .admx nella root del Central Store
# Copiare i file .adml nella sottocartella della lingua (es. it-IT, en-US)

# Verificare che il Central Store funzioni:
# Aprire GPMC → Edit una GPO → Administrative Templates
# Deve mostrare "Administrative Templates: Policy definitions (ADMX files)
#                retrieved from the central store."
```

### Starter GPO

```powershell
# Le Starter GPO sono template pre-configurati per accelerare la creazione di nuove GPO
# Contengono SOLO Administrative Templates (no Security Settings, no Preferences)

# Creare una Starter GPO
New-GPStarterGPO -Name "STARTER-Baseline-Security" `
    -Comment "Baseline sicurezza per tutte le workstation"

# Creare GPO da Starter GPO
New-GPO -Name "SEC-Workstation-Baseline" -StarterGPOName "STARTER-Baseline-Security"
```

---

## GPO Troubleshooting

```powershell
# VERIFICA APPLICAZIONE GPO

# Resultant Set of Policy (RSoP) — cosa viene applicato?
gpresult /r                        # Sommario
gpresult /h C:\gpresult.html       # Report HTML completo
gpresult /r /scope:computer        # Solo computer policies
gpresult /r /scope:user            # Solo user policies

# Su un computer remoto
gpresult /s WKS-IT-001 /r /user corp\mrossi

# Forzare aggiornamento GPO
gpupdate /force                    # Computer + User
gpupdate /target:computer          # Solo computer
gpupdate /target:user              # Solo user
Invoke-GPUpdate -Computer "WKS-IT-001" -Force  # PowerShell remoto

# CHECKLIST PROBLEMI GPO
#
# GPO non si applica — seguire questa sequenza diagnostica:
#
# 1. LINK: la GPO e linkata alla OU/dominio/site corretti?
Get-GPInheritance -Target "OU=Italia,OU=Utenti,DC=corp,DC=contoso,DC=com"

# 2. SECURITY FILTERING: il target (utente/computer) ha i permessi Read + Apply?
Get-GPPermission -Name "GPO-Software-Office" -All

# 3. WMI FILTER: il filtro WMI e soddisfatto sul target?
# Testare manualmente: wbemtest → connessione locale → query WMI

# 4. BLOCK INHERITANCE: la OU target ha Block Inheritance?
# Se si, la GPO deve essere Enforced per superarlo

# 5. ORDINE DI PRECEDENZA (LSDOU): un'altra GPO sovrascrive la setting?
# Controllare nel gpresult /h quale GPO ha vinto

# 6. STATO GPO: la sezione (User/Computer) e abilitata?
(Get-GPO "GPO-Software-Office").GpoStatus
# Valori: AllSettingsEnabled, AllSettingsDisabled, UserSettingsDisabled, ComputerSettingsDisabled

# 7. REPLICA SYSVOL: la GPO e presente su tutti i DC?
dcdiag /test:sysvolcheck /s:DC01
# Verificare DFS-R:
dfsrdiag pollad

# 8. VERSIONE: la versione AD e SYSVOL corrispondono?
Get-GPO -All | ForEach-Object {
    [PSCustomObject]@{
        Name = $_.DisplayName
        UserVersionAD = $_.User.DSVersion
        UserVersionSysvol = $_.User.SysvolVersion
        ComputerVersionAD = $_.Computer.DSVersion
        ComputerVersionSysvol = $_.Computer.SysvolVersion
        Match = ($_.User.DSVersion -eq $_.User.SysvolVersion -and
                 $_.Computer.DSVersion -eq $_.Computer.SysvolVersion)
    }
} | Where-Object { -not $_.Match }

# 9. LOOPBACK: se si tratta di User Configuration su un computer specifico,
#    e attivo il Loopback Processing?

# 10. SLOW LINK DETECTION: il client rileva un link lento?
# Per default, link < 500 kbps = slow link.
# Su slow link, alcune GPO non vengono applicate (es. Software Installation).
# Computer → Administrative Templates → System → Group Policy →
#   Group Policy slow link detection: impostare soglia o disabilitare.
```

---

## Sites e Replica

### Configurazione Sites

I Sites in AD rappresentano la topologia fisica della rete. Servono per:
- **Ottimizzare la replica**: replica intra-site veloce e non compressa; inter-site programmata e compressa.
- **Localizzare servizi**: un client trova il DC piu vicino basandosi sul site.
- **DFS**: namespace DFS usano i sites per il referral piu vicino.

```powershell
# Creare Site
New-ADReplicationSite -Name "Milano"
New-ADReplicationSite -Name "Roma"

# Creare Subnet e associare al Site
New-ADReplicationSubnet -Name "192.168.10.0/24" -Site "Milano" -Description "Rete LAN Milano"
New-ADReplicationSubnet -Name "192.168.20.0/24" -Site "Roma" -Description "Rete LAN Roma"
New-ADReplicationSubnet -Name "10.0.0.0/16" -Site "Milano" -Description "VPN Milano"

# Creare Site Link
New-ADReplicationSiteLink -Name "Milano-Roma" -SitesIncluded "Milano","Roma" `
    -Cost 100 -ReplicationFrequencyInMinutes 15 `
    -InterSiteTransportProtocol IP

# Modificare Site Link
Set-ADReplicationSiteLink -Identity "Milano-Roma" `
    -ReplicationFrequencyInMinutes 30 -Cost 200

# Creare Site Link Bridge (per topologie hub-spoke senza full mesh)
New-ADReplicationSiteLinkBridge -Name "Bridge-Hub" `
    -SiteLinksIncluded "Milano-Roma","Milano-Napoli"

# Spostare DC in un site
Move-ADDirectoryServer -Identity "DC02" -Site "Roma"

# Verificare site assignment di un computer
nltest /dsgetsite
# Oppure:
[System.DirectoryServices.ActiveDirectory.ActiveDirectorySite]::GetComputerSite().Name
```

### Replica Intra-Site vs Inter-Site

| Caratteristica | Intra-Site | Inter-Site |
|---------------|------------|------------|
| **Trigger** | Change notification (immediato) | Schedule (programmato) |
| **Latenza** | ~15 secondi dopo la modifica | In base al programma (default 180 min) |
| **Compressione** | No | Si (40-60% riduzione) |
| **Trasporto** | RPC over IP | RPC over IP o SMTP (solo config/schema) |
| **Topologia** | Ring (anello) generata dal KCC | Span tree tra bridgehead servers |
| **Bandwidth** | Assume LAN (alta banda, bassa latenza) | Assume WAN (banda limitata) |

```
Flusso replica intra-site (change notification):
1. DC-A modifica un oggetto
2. DC-A attende 15 secondi (replication dampening)
3. DC-A notifica i partner di replica
4. I partner richiedono le modifiche (pull model)
5. Totale: ~15-45 secondi per la propagazione nel site

Flusso replica inter-site (schedule-based):
1. DC-A modifica un oggetto (in Site Milano)
2. La modifica viene replicata intra-site ai DC di Milano
3. Al prossimo intervallo di replica inter-site, il bridgehead
   server di Milano invia le modifiche al bridgehead server di Roma
4. Le modifiche vengono replicate intra-site ai DC di Roma
5. Totale: dipende dallo schedule (default 180 min)
```

### Knowledge Consistency Checker (KCC)

Il KCC e un processo che gira su ogni DC e genera automaticamente la topologia di replica.

```
KCC genera:
- Intra-site: topologia ad anello bidirezionale
  (ogni DC ha almeno 2 partner, per ridondanza)
  Se i DC nel site sono > 7, il KCC crea shortcut per ridurre il numero di hop.

- Inter-site: la ISTG (Inter-Site Topology Generator) e un DC designato per site
  che genera le connection inter-site tra bridgehead servers.
```

```powershell
# Forzare il KCC a ricalcolare la topologia
repadmin /kcc DC01

# Verificare le connessioni di replica generate dal KCC
Get-ADReplicationConnection -Filter * | Select-Object Name, ReplicateFromDirectoryServer,
    ReplicateToDirectoryServer, AutoGenerated

# Verificare la ISTG (Inter-Site Topology Generator) per un site
Get-ADReplicationSite -Identity "Milano" | Select-Object InterSiteTopologyGenerator
```

### Bridgehead Server

Il bridgehead server e il DC designato in ogni site per gestire la replica inter-site. Il KCC/ISTG lo seleziona automaticamente, ma puo essere designato manualmente.

```powershell
# Verificare il bridgehead server corrente
repadmin /bridgeheads

# Designare manualmente un preferred bridgehead server
# (In AD Sites and Services: proprieta del DC → Transport → "Add to preferred bridgehead")
# Via PowerShell:
Set-ADObject -Identity (Get-ADDomainController DC01).NTDSSettingsObjectDN `
    -Add @{bridgeheadTransportList="CN=IP,CN=Inter-Site Transports,CN=Sites,CN=Configuration,DC=corp,DC=contoso,DC=com"}

# ATTENZIONE: se il preferred bridgehead server va offline, la replica inter-site
# si FERMA per quel site (il KCC non failover a un altro DC).
# Designare sempre ALMENO 2 preferred bridgehead.
```

### Replica Urgente

Alcune modifiche vengono replicate immediatamente, bypassando il delay di 15 secondi (intra-site) e lo schedule (inter-site su Windows Server 2003+):

- Cambio password utente
- Account lockout
- Cambio del segreto LSA
- Cambio del segreto della trust relationship
- Modifica del RID Manager

```powershell
# Forzare replica manuale di tutte le partizioni
repadmin /syncall DC01 /APed
# /A = tutte le partizioni
# /P = push (notifica i partner)
# /e = enterprise (tutti i site)
# /d = identifica i server per DN

# Forzare replica di una specifica partizione
repadmin /replicate DC02 DC01 "DC=corp,DC=contoso,DC=com"
```

### Monitoraggio Replica — repadmin Deep Dive

```powershell
# COMANDI REPADMIN ESSENZIALI

# Stato replica di tutti i DC (vista d'insieme)
repadmin /replsummary
# Mostra: Source DC, Destination DC, Number of Failures, Last Failure Time

# Stato replica dettagliato di un DC
repadmin /showrepl DC01
# Mostra: ogni naming context, partner, ultimo successo, ultimo fallimento

# Elenco oggetti in attesa di replica
repadmin /queue DC01

# Mostrare le modifiche pendenti
repadmin /showchanges DC01 DC02 "DC=corp,DC=contoso,DC=com"

# Verificare la convergenza (tutti i DC hanno lo stesso dato)
repadmin /showattr DC01 "CN=Mario Rossi,OU=Utenti,DC=corp,DC=contoso,DC=com" /atts:pwdLastSet

# Confrontare un attributo su tutti i DC
repadmin /showobjmeta DC01 "CN=Mario Rossi,OU=Utenti,DC=corp,DC=contoso,DC=com"
# Mostra: versione, origine, timestamp per ogni attributo

# Verificare USN (Update Sequence Number)
repadmin /showutdvec DC01 "DC=corp,DC=contoso,DC=com"

# Report errori di replica
repadmin /failcache

# DIAGNOSTICA AVANZATA

# Verificare lingering objects (oggetti che dovrebbero essere cancellati ma persistono)
repadmin /removelingeringobjects DC02 DC01 "DC=corp,DC=contoso,DC=com" /advisory_mode

# dcdiag — suite completa di test
dcdiag /v /c /e          # Tutti i test, tutti i DC, verbose
dcdiag /test:replications # Solo test replica
dcdiag /test:topology     # Verifica topologia KCC
dcdiag /test:intersite    # Verifica replica inter-site
dcdiag /test:kccevent     # Verifica eventi KCC
```

---

## Kerberos e Autenticazione

### Flusso Kerberos Dettagliato

```
FLUSSO COMPLETO KERBEROS IN AD:

┌─────────┐         ┌──────────────────┐         ┌──────────────┐
│  Client  │         │   KDC (DC)       │         │  Application │
│          │         │ AS + TGS Service │         │    Server    │
└────┬─────┘         └────────┬─────────┘         └──────┬───────┘
     │                        │                          │
     │  1. AS-REQ             │                          │
     │  (username + timestamp │                          │
     │   encrypted con hash   │                          │
     │   password utente)     │                          │
     │──────────────────────>│                          │
     │                        │                          │
     │  2. AS-REP             │                          │
     │  (TGT encrypted con   │                          │
     │   hash krbtgt account  │                          │
     │   + session key)       │                          │
     │<──────────────────────│                          │
     │                        │                          │
     │  3. TGS-REQ            │                          │
     │  (TGT + SPN target    │                          │
     │   es: HTTP/webapp)     │                          │
     │──────────────────────>│                          │
     │                        │                          │
     │  4. TGS-REP            │                          │
     │  (Service Ticket       │                          │
     │   encrypted con hash   │                          │
     │   dell'account         │                          │
     │   del servizio)        │                          │
     │<──────────────────────│                          │
     │                        │                          │
     │  5. AP-REQ (Service Ticket)                      │
     │─────────────────────────────────────────────────>│
     │                        │                          │
     │  6. AP-REP (mutual auth, opzionale)              │
     │<─────────────────────────────────────────────────│
```

Dettagli critici:
- Il **TGT** e valido per default 10 ore (rinnovabile per 7 giorni).
- Il **Service Ticket** e valido per default 10 ore.
- Il **clock skew** massimo tollerato e 5 minuti. Se il tempo del client differisce dal DC di oltre 5 minuti, l'autenticazione Kerberos fallisce.
- Il TGT e cifrato con l'hash della password dell'account **krbtgt**. Chiunque possieda l'hash krbtgt puo forgiare TGT (Golden Ticket attack).
- Il Service Ticket e cifrato con l'hash dell'account che possiede lo SPN. Se quell'account ha una password debole, il ticket puo essere craccato offline (Kerberoasting).

### Diagnostica Kerberos

```powershell
# Visualizzare ticket Kerberos correnti
klist                              # Ticket utente corrente
klist -li 0x3e7                    # Ticket computer (SYSTEM)

# Cancellare cache ticket
klist purge

# Verificare SPN (Service Principal Name)
setspn -L accountname              # Lista SPN di un account
setspn -Q HTTP/webapp.contoso.com  # Cerca chi ha questo SPN (verifica duplicati)

# Registrare SPN
setspn -S HTTP/webapp.contoso.com svc-webapp

# SPN duplicati — causa comune di fallimenti Kerberos
setspn -X                          # Trova TUTTI gli SPN duplicati nel dominio

# Verificare sincronizzazione tempo (clock skew)
w32tm /query /status
w32tm /stripchart /computer:DC01
w32tm /monitor /domain:corp.contoso.com

# Test autenticazione
# Se Kerberos fallisce e il client cade su NTLM:
# → Verificare SPN (duplicato o mancante)
# → Verificare DNS (il client deve risolvere il server per FQDN)
# → Verificare clock skew (< 5 minuti)
# → Verificare connettivita alla porta 88 (Kerberos) sul DC
```

### NTLM — Il Fallback da Eliminare

NTLM e il protocollo di autenticazione legacy che precede Kerberos. E ancora presente per compatibilita, ma deve essere progressivamente eliminato.

```
Perche NTLM e pericoloso:
1. Vulnerabile a relay attack (NTLM relay)
2. Vulnerabile a pass-the-hash
3. Non supporta mutual authentication
4. Hash NTLMv1 e debole (crackabile in ore)
5. Non supporta Kerberos delegation

Quando NTLM viene usato (invece di Kerberos):
- Accesso via IP (es. \\192.168.10.1\share) invece di FQDN
- SPN mancante o duplicato per il servizio
- Client non in dominio
- Clock skew > 5 minuti
- Applicazioni legacy che non supportano Kerberos
- Accesso a risorse in un workgroup
```

```powershell
# Audit dell'uso di NTLM (trovare chi lo usa ancora)
# GPO: Computer → Windows Settings → Security Settings → Local Policies → Security Options
# - Network security: Restrict NTLM: Audit NTLM authentication in this domain: Enable all
# - Network security: Restrict NTLM: Audit Incoming NTLM Traffic: Enable auditing for all accounts

# Dopo il periodo di audit, bloccare NTLM gradualmente:
# - Network security: Restrict NTLM: NTLM authentication in this domain: Deny all accounts
# - Aggiungere eccezioni dove necessario

# Verificare eventi NTLM nei log:
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4776} -MaxEvents 20 |
    Select-Object TimeCreated, Message
```

---

## Sicurezza Active Directory

### Kerberoasting — Attacco e Difesa

Il Kerberoasting sfrutta il fatto che il Service Ticket e cifrato con l'hash della password dell'account che possiede lo SPN. Se quell'account ha una password debole, un attaccante puo richiedere il ticket e craccarlo offline.

```
Flusso attacco Kerberoasting:
1. Attaccante ottiene accesso con un account di dominio qualsiasi (bassa privileges)
2. Enumera gli SPN associati ad account UTENTE (non computer)
3. Richiede Service Ticket per quegli SPN (operazione legittima, nessun alert)
4. Estrae i ticket dalla memoria
5. Cracca offline i ticket con hashcat/John the Ripper
6. Ottiene la password in chiaro dell'account servizio
7. Se l'account servizio e privilegiato → compromissione
```

```powershell
# DIFESA: Identificare account vulnerabili a Kerberoasting

# Trovare tutti gli account utente con SPN (potenziali target)
Get-ADUser -Filter {ServicePrincipalName -ne "$null"} `
    -Properties ServicePrincipalName, PasswordLastSet, MemberOf |
    Select-Object Name, SamAccountName, PasswordLastSet,
    @{N='SPNs';E={$_.ServicePrincipalName -join '; '}},
    @{N='Privileged';E={$_.MemberOf -match "Admin"}}

# MITIGAZIONI:
# 1. Password lunghe e complesse (>25 caratteri) per service accounts con SPN
# 2. Usare gMSA (Group Managed Service Accounts) — password 240 char, rotazione automatica
# 3. Monitorare richieste TGS anomale (Event ID 4769 con cifratura RC4)
# 4. Usare AES encryption per i service accounts (non RC4/DES)
# 5. Ridurre i privilegi degli account servizio al minimo necessario
# 6. Audit regolare degli SPN su account utente

# Forzare AES per un account servizio:
Set-ADUser -Identity "svc-webapp" -KerberosEncryptionType AES128,AES256

# Verificare tipo di cifratura
Get-ADUser -Identity "svc-webapp" -Properties msDS-SupportedEncryptionTypes
```

### NTLM Relay — Attacco e Mitigazione

```
Flusso attacco NTLM Relay:
1. Attaccante posiziona un listener su un host controllato
2. Induce una vittima a connettersi (via link, email, WPAD, LLMNR poisoning)
3. La vittima invia il challenge/response NTLM al listener dell'attaccante
4. L'attaccante re-inoltra (relay) il challenge/response al server target
5. Il server target autentica l'attaccante come se fosse la vittima
6. L'attaccante ottiene accesso alla risorsa con i privilegi della vittima
```

```powershell
# MITIGAZIONI NTLM Relay:

# 1. Disabilitare NTLM dove possibile (vedi sezione NTLM sopra)

# 2. Abilitare SMB Signing (impedisce relay su SMB)
# GPO: Computer → Windows Settings → Security Settings → Local Policies → Security Options
# - Microsoft network server: Digitally sign communications (always): Enabled
# - Microsoft network client: Digitally sign communications (always): Enabled

# 3. Abilitare LDAP Signing e Channel Binding
# GPO: Computer → Windows Settings → Security Settings → Local Policies → Security Options
# - Domain controller: LDAP server signing requirements: Require signing
# - Domain controller: LDAP server channel binding token requirements: Always

# 4. Abilitare EPA (Extended Protection for Authentication) su IIS/Exchange

# 5. Disabilitare LLMNR e NetBIOS (usati per poisoning)
# GPO: Computer → Administrative Templates → Network → DNS Client
# - Turn off multicast name resolution: Enabled
# NetBIOS: disabilitare via DHCP Option o interfaccia di rete

# 6. Abilitare Windows Defender Credential Guard (Windows 10/11 Enterprise)
```

### Protected Users Group

Il gruppo Protected Users (disponibile dal livello funzionale 2012 R2) applica restrizioni di sicurezza rigorose ai suoi membri:

```
Restrizioni applicate ai membri di Protected Users:
- NON possono autenticarsi con NTLM (solo Kerberos)
- NON possono usare DES o RC4 per Kerberos pre-authentication
- NON possono essere delegati (Kerberos delegation bloccata)
- TGT lifetime ridotto a 4 ore (non rinnovabile)
- Credenziali NON vengono cached su disco (no offline logon)
- Credential caching in memoria ridotto al minimo
- WDigest authentication disabilitata
```

```powershell
# Aggiungere account privilegiati al gruppo Protected Users
Add-ADGroupMember -Identity "Protected Users" -Members "admin-mrossi"

# Verificare membri
Get-ADGroupMember -Identity "Protected Users" | Select-Object Name, ObjectClass

# ATTENZIONE:
# - NON aggiungere service accounts → non potranno autenticarsi con NTLM
# - NON aggiungere account che necessitano di offline logon
# - NON aggiungere l'account krbtgt
# - Testare prima con un account di test
# - Ideale per: Domain Admins, Enterprise Admins, privileged admin accounts
```

### AdminSDHolder e SDProp

AdminSDHolder e un meccanismo di protezione automatica per gli account privilegiati. Ogni 60 minuti (per default), il processo SDProp sovrascrive le ACL di tutti i membri dei gruppi protetti con le ACL dell'oggetto AdminSDHolder.

```
Gruppi protetti da AdminSDHolder/SDProp:
- Domain Admins
- Enterprise Admins
- Schema Admins
- Administrators
- Account Operators
- Server Operators
- Print Operators
- Backup Operators
- Replicator
- Domain Controllers
- Read-only Domain Controllers
```

```powershell
# L'attributo adminCount = 1 indica che l'oggetto e (o e stato) protetto da SDProp
# NOTA: adminCount non viene resettato quando un utente viene rimosso dal gruppo protetto

# Trovare tutti gli utenti con adminCount = 1
Get-ADUser -Filter {adminCount -eq 1} -Properties adminCount, MemberOf |
    Select-Object Name, SamAccountName, adminCount

# Trovare utenti "orfani" (adminCount=1 ma non piu in gruppi protetti)
$protectedGroups = @("Domain Admins","Enterprise Admins","Schema Admins",
    "Administrators","Account Operators","Server Operators",
    "Print Operators","Backup Operators")
$protectedMembers = $protectedGroups | ForEach-Object {
    Get-ADGroupMember $_ -Recursive -ErrorAction SilentlyContinue
} | Select-Object -ExpandProperty SamAccountName -Unique

Get-ADUser -Filter {adminCount -eq 1 -and Enabled -eq $true} |
    Where-Object { $_.SamAccountName -notin $protectedMembers } |
    Select-Object Name, SamAccountName

# Modificare l'intervallo SDProp (default 60 minuti):
# HKLM\SYSTEM\CurrentControlSet\Services\NTDS\Parameters
# AdminSDProtectFrequency (DWORD) = secondi (min 60)

# Visualizzare ACL dell'AdminSDHolder container
(Get-ACL "AD:CN=AdminSDHolder,CN=System,DC=corp,DC=contoso,DC=com").Access |
    Select-Object IdentityReference, ActiveDirectoryRights, AccessControlType
```

### LAPS — Local Administrator Password Solution

LAPS gestisce automaticamente la password dell'account amministratore locale su ogni computer del dominio, memorizzandola in un attributo AD protetto.

```powershell
# Windows LAPS (integrato in Windows Server 2019+ e Windows 10/11 con update)

# Verificare se LAPS e configurato
Get-ADComputer "WKS-IT-001" -Properties ms-Mcs-AdmPwd, ms-Mcs-AdmPwdExpirationTime

# Per Windows LAPS (nuovo, nativo):
Get-LapsADPassword -Identity "WKS-IT-001" -AsPlainText

# Configurare LAPS via GPO:
# Computer → Administrative Templates → LAPS
# - Configure password backup directory: Active Directory
# - Password Settings: lunghezza, complessita, durata
# - Name of administrator account to manage: (lasciare vuoto per il built-in)
# - Post-authentication actions: Reset password and logoff

# LAPS e una mitigazione critica contro:
# - Pass-the-hash laterale (ogni PC ha una password locale diversa)
# - Credential reuse (le password ruotano automaticamente)
# - Accesso non autorizzato (la password e protetta con ACL AD)
```

### Credential Caching e Protezione

```powershell
# Per default, Windows crea cache delle credenziali per consentire
# l'offline logon. Il numero di logon cached e controllato da:
# GPO: Computer → Windows Settings → Security Settings → Local Policies → Security Options
# - Interactive logon: Number of previous logons to cache: 10 (default)
# Per workstation sicure: ridurre a 1 o 2
# Per DC: impostare a 0

# Credential Guard (Windows 10/11 Enterprise):
# Isola LSA in un container Hyper-V protetto.
# Le credenziali NTLM hash e Kerberos TGT non sono accessibili da malware.
# Requisiti: UEFI Secure Boot, TPM 2.0, Hyper-V

# Verificare se Credential Guard e attivo
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
    Select-Object SecurityServicesRunning
# 1 = Credential Guard running

# Remote Credential Guard (per RDP):
# Impedisce che le credenziali vengano inviate al server remoto durante RDP.
# mstsc /remoteGuard
```

---

## Delega Amministrativa

### Modello di Delega su OU

La delega amministrativa permette di assegnare permessi granulari su specifiche OU senza concedere privilegi a livello di dominio.

```
Modello di delega Tier:

Tier 0 (Domain Controllers, Schema, Forest)
│   → Solo Enterprise Admins e Domain Admins
│   → Nessuna delega — accesso diretto
│
Tier 1 (Server e Servizi)
│   → GG-T1-ServerAdmins → delega su OU=Server
│   → GG-T1-ServiceAdmins → delega su OU=ServiceAccounts
│   → Permessi: gestire server, servizi, gMSA
│
Tier 2 (Workstation e Utenti)
    → GG-T2-HelpdeskL1 → delega su OU=Utenti (reset password, unlock)
    → GG-T2-HelpdeskL2 → delega su OU=Computer (join/unjoin dominio)
    → GG-T2-GroupMgr → delega su OU=Gruppi (gestione membri gruppi)
```

### Delega con PowerShell

```powershell
# La delega in AD si realizza modificando le ACL (Access Control List)
# sul Distinguished Name della OU target.

# ESEMPIO 1: Delega reset password agli helpdesk
$ouDN = "OU=Utenti,DC=corp,DC=contoso,DC=com"
$groupSID = (Get-ADGroup "GG-Helpdesk").SID

# Ottenere il GUID dell'attributo "Reset Password"
$resetPwdGUID = [GUID]"00299570-246d-11d0-a768-00aa006e0529"
# GUID "User" class
$userClassGUID = [GUID]"bf967aba-0de6-11d0-a285-00aa003049e2"

$acl = Get-ACL "AD:$ouDN"
$ace = New-Object System.DirectoryServices.ActiveDirectoryAccessRule(
    $groupSID,
    "ExtendedRight",
    "Allow",
    $resetPwdGUID,
    "Descendents",
    $userClassGUID
)
$acl.AddAccessRule($ace)
Set-ACL "AD:$ouDN" $acl

# ESEMPIO 2: Delega lettura/scrittura attributi utente
$writePropertyGUID = [GUID]::Empty  # Tutti gli attributi
$ace = New-Object System.DirectoryServices.ActiveDirectoryAccessRule(
    $groupSID,
    "ReadProperty,WriteProperty",
    "Allow",
    $writePropertyGUID,
    "Descendents",
    $userClassGUID
)

# ESEMPIO 3: Delega creazione/eliminazione computer objects
$computerClassGUID = [GUID]"bf967a86-0de6-11d0-a285-00aa003049e2"
$ouDN = "OU=Computer,DC=corp,DC=contoso,DC=com"
$acl = Get-ACL "AD:$ouDN"
$ace = New-Object System.DirectoryServices.ActiveDirectoryAccessRule(
    (Get-ADGroup "GG-ComputerAdmins").SID,
    "CreateChild,DeleteChild",
    "Allow",
    $computerClassGUID,
    "All"
)
$acl.AddAccessRule($ace)
Set-ACL "AD:$ouDN" $acl

# VERIFICA: elencare le deleghe su una OU
(Get-ACL "AD:OU=Utenti,DC=corp,DC=contoso,DC=com").Access |
    Where-Object { $_.IdentityReference -notmatch "BUILTIN|NT AUTHORITY|S-1-5-" } |
    Select-Object IdentityReference, ActiveDirectoryRights, ObjectType, InheritedObjectType
```

### Least Privilege Design

```
Principi di delega least privilege:

1. MAI aggiungere utenti a Domain Admins per attivita che non lo richiedono.
   Il 90% delle attivita quotidiane (reset password, join computer, gestione gruppi)
   puo essere delegato senza Domain Admin.

2. Creare gruppi di delega separati per ogni permesso:
   - GG-Helpdesk-ResetPwd     (reset password)
   - GG-Helpdesk-UnlockAcct   (unlock account)
   - GG-Helpdesk-ModifyUser   (modifica attributi)
   - GG-Desktop-JoinDomain    (join computer al dominio)

3. Delegare sulla OU piu ristretta possibile.
   Non delegare su "DC=corp,DC=contoso,DC=com" quando basta OU=Utenti.

4. Documentare ogni delega:
   - Chi ha accesso
   - Quali permessi
   - Su quale OU
   - Data della delega
   - Approvazione
   - Ultima revisione

5. Audit regolare (quarterly):
   - Le deleghe sono ancora necessarie?
   - Ci sono utenti che hanno lasciato il team ma hanno ancora accesso?
   - Ci sono escalation di privilegio non documentate?
```

---

## AD Recycle Bin

### Abilitazione

L'AD Recycle Bin (disponibile dal livello funzionale 2008 R2) permette di ripristinare oggetti eliminati mantenendo TUTTI gli attributi (inclusi i link come memberOf). Senza Recycle Bin, il ripristino da tombstone perde la maggior parte degli attributi.

```powershell
# Verificare se AD Recycle Bin e abilitato
Get-ADOptionalFeature -Filter {Name -eq "Recycle Bin Feature"}

# Abilitare AD Recycle Bin (IRREVERSIBILE — non si puo disabilitare)
Enable-ADOptionalFeature -Identity "Recycle Bin Feature" `
    -Scope ForestOrConfigurationSet -Target "corp.contoso.com" -Confirm:$false

# Requisiti:
# - Livello funzionale foresta: Windows Server 2008 R2 o superiore
# - L'operazione e irreversibile
# - Replica a tutti i DC della foresta
```

### Ripristino Oggetti

```powershell
# Elencare oggetti nel Recycle Bin
Get-ADObject -Filter {isDeleted -eq $true -and name -ne "Deleted Objects"} `
    -IncludeDeletedObjects -Properties * |
    Select-Object Name, ObjectClass, whenChanged, LastKnownParent, msDS-LastKnownRDN

# Ripristinare un utente specifico
Get-ADObject -Filter {isDeleted -eq $true -and ObjectClass -eq "user" `
    -and msDS-LastKnownRDN -eq "Mario Rossi"} -IncludeDeletedObjects |
    Restore-ADObject

# Ripristinare nella OU originale (default) o specificare una diversa
Get-ADObject -Filter {isDeleted -eq $true -and ObjectClass -eq "user" `
    -and msDS-LastKnownRDN -eq "Mario Rossi"} -IncludeDeletedObjects |
    Restore-ADObject -TargetPath "OU=Italia,OU=Utenti,DC=corp,DC=contoso,DC=com"

# Ripristinare un'intera OU con tutti gli oggetti figli
# Prima ripristinare la OU:
Get-ADObject -Filter {isDeleted -eq $true -and ObjectClass -eq "organizationalUnit" `
    -and msDS-LastKnownRDN -eq "OU-Eliminata"} -IncludeDeletedObjects |
    Restore-ADObject
# Poi ripristinare gli oggetti figli:
Get-ADObject -Filter {isDeleted -eq $true -and LastKnownParent -eq `
    "OU=OU-Eliminata,DC=corp,DC=contoso,DC=com"} -IncludeDeletedObjects |
    Restore-ADObject
```

### Tombstone e Ciclo di Vita degli Oggetti Eliminati

```
Con AD Recycle Bin ABILITATO:

Oggetto attivo
    │ (Eliminazione)
    ▼
Stato "Deleted" (nel Recycle Bin)
    │ Tutti gli attributi mantenuti
    │ Durata: deleted object lifetime (default 180 giorni)
    │ Ripristino COMPLETO possibile
    ▼
Stato "Recycled" (tombstone)
    │ La maggior parte degli attributi rimossi
    │ Durata: tombstone lifetime (default 180 giorni)
    │ Ripristino NON possibile (dati persi)
    ▼
Oggetto rimosso fisicamente dal database (garbage collection)


Con AD Recycle Bin DISABILITATO:

Oggetto attivo
    │ (Eliminazione)
    ▼
Tombstone (stato unico)
    │ La maggior parte degli attributi IMMEDIATAMENTE rimossi
    │ Solo SID, GUID, DN, objectClass, last known parent mantenuti
    │ Durata: tombstone lifetime (default 180 giorni)
    │ Ripristino possibile ma con perdita dati massiva
    ▼
Oggetto rimosso fisicamente
```

```powershell
# Verificare e modificare tombstone lifetime
$configDN = (Get-ADRootDSE).configurationNamingContext
$tombstone = Get-ADObject "CN=Directory Service,CN=Windows NT,CN=Services,$configDN" `
    -Properties tombstoneLifetime
$tombstone.tombstoneLifetime  # Default: 180 giorni

# Modificare tombstone lifetime (minimo raccomandato: 180 giorni)
Set-ADObject "CN=Directory Service,CN=Windows NT,CN=Services,$configDN" `
    -Replace @{tombstoneLifetime=365}

# Verificare deleted object lifetime
# (uguale al tombstone lifetime per default)
Get-ADObject "CN=Directory Service,CN=Windows NT,CN=Services,$configDN" `
    -Properties 'msDS-deletedObjectLifetime'
```

---

## LDAP Query e Integrazione

### Query LDAP con PowerShell

```powershell
# Il modulo ActiveDirectory usa LDAP sotto il cofano.
# Per performance o da sistemi non-Windows, si possono fare query LDAP dirette.

# Query con DirectorySearcher (.NET)
$searcher = New-Object DirectoryServices.DirectorySearcher
$searcher.SearchRoot = "LDAP://OU=Utenti,DC=corp,DC=contoso,DC=com"
$searcher.Filter = "(&(objectClass=user)(department=IT)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))"
$searcher.PropertiesToLoad.AddRange(@("sAMAccountName","mail","title"))
$searcher.PageSize = 1000  # Fondamentale per risultati > 1000
$results = $searcher.FindAll()

foreach ($result in $results) {
    $result.Properties["samaccountname"]
}

# IMPORTANTE: PageSize
# Senza PageSize, LDAP restituisce massimo 1000 risultati (MaxPageSize default del DC).
# Con PageSize impostato, la query viene paginata automaticamente.
```

### Query LDAP Avanzate

```powershell
# FILTRI LDAP COMUNI

# Tutti gli utenti abilitati:
"(&(objectClass=user)(objectCategory=person)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))"

# Utenti con password scaduta:
"(&(objectClass=user)(objectCategory=person)(pwdLastSet=0))"

# Utenti con password che non scade mai (bit 65536 in userAccountControl):
"(&(objectClass=user)(userAccountControl:1.2.840.113556.1.4.803:=65536))"

# Computer con OS specifico:
"(&(objectClass=computer)(operatingSystem=*Server 2022*))"

# Membri di un gruppo (ricorsivo) — OID 1.2.840.113556.1.4.1941:
"(&(objectClass=user)(memberOf:1.2.840.113556.1.4.1941:=CN=GG-IT-Staff,OU=Gruppi,DC=corp,DC=contoso,DC=com))"

# Oggetti modificati nelle ultime 24 ore:
"(&(objectClass=user)(whenChanged>=20260521000000.0Z))"

# Utenti con account che scade entro 30 giorni:
# (Richiede calcolo del valore FILETIME per la data)

# Oggetti con un attributo specifico vuoto:
"(&(objectClass=user)(!(mail=*)))"

# Oggetti con un attributo che contiene un valore:
"(&(objectClass=user)(description=*VPN*))"

# MATCHING RULES (OID speciali):
# 1.2.840.113556.1.4.803  → Bitwise AND (usato per userAccountControl)
# 1.2.840.113556.1.4.804  → Bitwise OR
# 1.2.840.113556.1.4.1941 → LDAP_MATCHING_RULE_IN_CHAIN (membership ricorsiva)

# VALORI userAccountControl comuni:
# 2     = ACCOUNTDISABLE
# 16    = LOCKOUT
# 32    = PASSWD_NOTREQD
# 64    = PASSWD_CANT_CHANGE
# 512   = NORMAL_ACCOUNT
# 65536 = DONT_EXPIRE_PASSWD
# 8388608 = PASSWORD_EXPIRED
```

### Connessione da Sistemi Non-Windows

```bash
# Da Linux con ldapsearch:
ldapsearch -H ldap://dc01.corp.contoso.com \
    -D "mrossi@corp.contoso.com" -W \
    -b "DC=corp,DC=contoso,DC=com" \
    "(&(objectClass=user)(department=IT))" \
    sAMAccountName mail title

# LDAPS (porta 636, richiede certificato sul DC):
ldapsearch -H ldaps://dc01.corp.contoso.com:636 \
    -D "mrossi@corp.contoso.com" -W \
    -b "DC=corp,DC=contoso,DC=com" \
    "(objectClass=user)" sAMAccountName

# Query al Global Catalog (porta 3268/3269):
ldapsearch -H ldap://dc01.corp.contoso.com:3268 \
    -D "mrossi@corp.contoso.com" -W \
    -b "DC=corp,DC=contoso,DC=com" \
    "(objectClass=user)" sAMAccountName

# Con Python (ldap3):
# from ldap3 import Server, Connection, ALL
# server = Server('dc01.corp.contoso.com', port=636, use_ssl=True, get_info=ALL)
# conn = Connection(server, user='mrossi@corp.contoso.com', password='...', auto_bind=True)
# conn.search('DC=corp,DC=contoso,DC=com', '(objectClass=user)',
#             attributes=['sAMAccountName', 'mail'])
```

---

## DNS Integrato con AD

### Architettura DNS in Active Directory

```
DNS e CRITICO per AD — senza DNS, NIENTE funziona.
Non e opzionale. AD dipende da DNS per:
- Localizzazione Domain Controller (_ldap._tcp.dc._msdcs.domain)
- Localizzazione servizi (SRV records)
- Kerberos (localizzazione KDC)
- Replica tra DC
- Join al dominio
- Localizzazione Global Catalog
- Risoluzione site (site-aware service location)
```

### Zona _msdcs e Record SRV

La zona `_msdcs.<forest>` e una zona speciale che contiene i record di service location per tutti i servizi AD della foresta.

```
Struttura record SRV nella zona _msdcs:

_msdcs.corp.contoso.com
├── _ldap._tcp.dc                    → Tutti i DC del dominio
├── _ldap._tcp.<site>._sites.dc      → DC nel site specifico
├── _kerberos._tcp.dc                → Tutti i KDC
├── _kerberos._tcp.<site>._sites.dc  → KDC nel site specifico
├── _kpasswd._tcp                    → Servizio cambio password Kerberos
├── _gc._tcp                         → Tutti i Global Catalog della foresta
├── _gc._tcp.<site>._sites           → GC nel site specifico
├── _ldap._tcp.gc                    → Alias per GC
├── _ldap._tcp.pdc                   → PDC Emulator
├── _ldap._tcp.<domainGUID>.domains  → Lookup per GUID dominio
└── dc/
    └── _ldap._tcp                   → DC (duplicato per compatibilita)

Record nella zona del dominio (non _msdcs):
_ldap._tcp.corp.contoso.com          → DC che servono il dominio
_kerberos._tcp.corp.contoso.com      → KDC del dominio
_kerberos._udp.corp.contoso.com      → KDC via UDP
_kpasswd._tcp.corp.contoso.com       → Servizio cambio password
```

```powershell
# Verificare record SRV critici (DEVONO tutti esistere)
Resolve-DnsName -Name "_ldap._tcp.dc._msdcs.corp.contoso.com" -Type SRV
Resolve-DnsName -Name "_kerberos._tcp.dc._msdcs.corp.contoso.com" -Type SRV
Resolve-DnsName -Name "_gc._tcp.corp.contoso.com" -Type SRV
Resolve-DnsName -Name "_kpasswd._tcp.corp.contoso.com" -Type SRV
Resolve-DnsName -Name "_ldap._tcp.pdc._msdcs.corp.contoso.com" -Type SRV

# Verificare record SRV per un site specifico
Resolve-DnsName -Name "_ldap._tcp.Milano._sites.dc._msdcs.corp.contoso.com" -Type SRV

# Con nslookup
nslookup -type=SRV _ldap._tcp.dc._msdcs.corp.contoso.com

# Forzare la ri-registrazione dei record DNS da un DC
nltest /dsregdns
# Oppure:
ipconfig /registerdns
# Oppure riavviare il servizio Netlogon:
Restart-Service Netlogon
```

### Zone AD-Integrated — Scope di Replica

Le zone DNS AD-Integrated memorizzano i record DNS nel database AD invece che in file di zona. Questo offre replica multi-master, sicurezza integrata, e compressione.

```
Scope di replica per zone AD-Integrated:

1. ForestDnsZones (tutti i DC DNS della foresta):
   - Usato per la zona _msdcs della foresta
   - Partizione: DC=ForestDnsZones,DC=corp,DC=contoso,DC=com
   - Replica a TUTTI i DC con ruolo DNS nella foresta

2. DomainDnsZones (tutti i DC DNS del dominio):
   - Usato per la zona forward del dominio
   - Partizione: DC=DomainDnsZones,DC=corp,DC=contoso,DC=com
   - Replica solo ai DC con ruolo DNS nel dominio

3. Domain (tutti i DC del dominio):
   - Scope legacy (Windows 2000 compatibility)
   - Replica a tutti i DC del dominio, anche senza ruolo DNS
   - NON raccomandato per nuove zone

4. Custom application partition:
   - Per replicare solo a DC specifici designati
```

```powershell
# Verificare le zone e il loro scope di replica
Get-DnsServerZone | Select-Object ZoneName, ZoneType, ReplicationScope, DirectoryPartitionName

# Cambiare scope di replica di una zona
Set-DnsServerPrimaryZone -Name "corp.contoso.com" -ReplicationScope Forest

# Creare zona AD-Integrated con scope specifico
Add-DnsServerPrimaryZone -Name "newzone.corp.contoso.com" `
    -ReplicationScope Domain -DynamicUpdate Secure
```

### Conditional Forwarder e Stub Zone

```powershell
# Conditional Forwarder — risolvere un dominio specifico tramite DNS server specificati
Add-DnsServerConditionalForwarderZone -Name "partner.com" `
    -MasterServers 10.10.10.10,10.10.10.11 `
    -ReplicationScope Forest
# Tutti i DC DNS della foresta sapranno risolvere "partner.com"

# Stub Zone — mantiene automaticamente una copia dei record NS e SOA
# della zona target (piu dinamica del conditional forwarder)
Add-DnsServerStubZone -Name "subsidiary.com" `
    -MasterServers 172.16.0.10 `
    -ReplicationScope Domain

# Differenza:
# - Conditional Forwarder: statico, punto a IP fissi dei DNS target
# - Stub Zone: dinamica, scopre automaticamente i DNS server autoritativi
```

### DNS Scavenging e Manutenzione

```powershell
# DNS Scavenging (pulizia record obsoleti)
# Fondamentale per evitare record DNS stale

# Abilitare scavenging a livello server
Set-DnsServerScavenging -ScavengingState $true `
    -RefreshInterval 7.00:00:00 `
    -NoRefreshInterval 7.00:00:00 `
    -ScavengingInterval 7.00:00:00

# Abilitare aging sulla zona
Set-DnsServerZoneAging -Name "corp.contoso.com" -Aging $true `
    -RefreshInterval 7.00:00:00 -NoRefreshInterval 7.00:00:00

# Parametri:
# - NoRefreshInterval: periodo in cui i record NON possono essere refreshed (default 7gg)
# - RefreshInterval: periodo in cui i record POSSONO essere refreshed (default 7gg)
# - ScavengingInterval: ogni quanto il server esegue la pulizia (default 7gg)
# Un record puo essere eliminato dopo: NoRefreshInterval + RefreshInterval

# Verificare record stale
Get-DnsServerResourceRecord -ZoneName "corp.contoso.com" -RRType A |
    Where-Object { $_.Timestamp -ne $null -and $_.Timestamp -lt (Get-Date).AddDays(-30) } |
    Select-Object HostName, Timestamp, RecordData

# ATTENZIONE: non abilitare scavenging sui record statici critici
# (DC, server infrastrutturali). Marcarli come statici (timestamp = 0).
```

### Diagnostica DNS per AD

```powershell
# Suite completa di diagnostica DNS
dcdiag /test:dns /v /s:DC01 /DnsDynamicUpdate /DnsRecordRegistration

# Verificare risoluzione DNS dal client
nslookup corp.contoso.com
nslookup -type=SRV _ldap._tcp.dc._msdcs.corp.contoso.com

# Verificare che il client punti ai DNS server corretti
Get-DnsClientServerAddress -InterfaceAlias "Ethernet"

# Flush cache DNS
ipconfig /flushdns
Clear-DnsClientCache

# Registrare record DNS del client
ipconfig /registerdns

# Verificare la cache DNS locale del client
Get-DnsClientCache | Where-Object { $_.Entry -like "*corp.contoso*" }

# Gestione record
Add-DnsServerResourceRecordA -ZoneName "corp.contoso.com" `
    -Name "webapp" -IPv4Address "192.168.10.30"
Add-DnsServerResourceRecordCName -ZoneName "corp.contoso.com" `
    -Name "www" -HostNameAlias "webapp.corp.contoso.com"

# Rimuovere record
Remove-DnsServerResourceRecord -ZoneName "corp.contoso.com" `
    -Name "oldserver" -RRType A -Force
```

---

## Azure AD Connect e Identita Ibrida

### Topologie di Sincronizzazione

Azure AD Connect (ora Microsoft Entra Connect) sincronizza le identita da AD on-premises verso Microsoft Entra ID (ex Azure AD).

```
TOPOLOGIE SUPPORTATE:

1. Single Forest, Single Tenant (la piu comune):
   AD on-premises (1 foresta) → Azure AD Connect → Microsoft Entra ID (1 tenant)

2. Multiple Forests, Single Tenant:
   Foresta A ─┐
   Foresta B ─┤→ Azure AD Connect → Microsoft Entra ID (1 tenant)
   Foresta C ─┘
   (un singolo Azure AD Connect con connector multipli)

3. Multiple Forests, Multiple Connectors:
   Foresta A → Azure AD Connect 1 ─┐
   Foresta B → Azure AD Connect 2 ─┤→ Microsoft Entra ID (1 tenant)
   Foresta C → Azure AD Connect 3 ─┘
   (NON supportato — usare la topologia #2)

4. Multiple Forests, Staging Mode:
   Foresta A ─┐→ Azure AD Connect (attivo) ──→ Microsoft Entra ID
   Foresta A ─┘→ Azure AD Connect (staging) ──→ (pronto per failover)
```

### Metodi di Autenticazione

| Metodo | Descrizione | Pros | Cons |
|--------|-------------|------|------|
| **PHS** (Password Hash Sync) | Hash dell'hash della password sincronizzato nel cloud | Semplicita, SSO, no dipendenza on-prem per auth cloud | Hash nel cloud (rischio percepito) |
| **PTA** (Pass-Through Auth) | Autenticazione validata on-premises in tempo reale | Password MAI nel cloud, policy on-prem rispettate | Richiede agenti on-prem online, single point of failure se agenti offline |
| **Federation** (AD FS) | Token SAML/WS-Fed emesso da AD FS on-prem | Massima flessibilita, MFA custom, smart card | Infrastruttura complessa (AD FS + WAP), alta manutenzione |

```
RACCOMANDAZIONE:
- Per la maggior parte delle organizzazioni: PHS + Seamless SSO
- PHS come backup ANCHE con PTA o Federation (per disaster recovery)
- Federation solo se ci sono requisiti specifici non coperti da PHS/PTA
  (es. autenticazione certificato, terze parti identity provider)
```

### Staging Mode

```
Azure AD Connect in Staging Mode:
- Importa e sincronizza i dati (legge da AD e Azure AD)
- NON esporta le modifiche (non scrive in Azure AD)
- Utile per:
  1. DR: se il server primario fallisce, promuovere lo staging
  2. Test: verificare le regole di sincronizzazione prima di applicarle
  3. Migrazione: upgrade della versione di Azure AD Connect

Per promuovere lo staging server:
1. Disabilitare Azure AD Connect sul server attivo
2. Sul server staging: togliere la modalita staging
3. Verificare la sincronizzazione
```

Per approfondimenti sull'identita ibrida, vedere: [30-identita-ibrida-azure-ad-dettaglio.md](30-identita-ibrida-azure-ad-dettaglio.md).

---

## AD Certificate Services — Integrazione

AD Certificate Services (AD CS) fornisce una PKI (Public Key Infrastructure) integrata con Active Directory. Per la guida completa, vedere: [28-pki-certificati-guida-completa.md](28-pki-certificati-guida-completa.md).

```
Integrazione AD CS con Active Directory:

1. Auto-Enrollment: i template dei certificati vengono pubblicati in AD.
   I client ricevono automaticamente i certificati tramite GPO.
   Computer → Windows Settings → Security Settings → Public Key Policies
   → Certificate Services Client - Auto-Enrollment: Enabled

2. LDAPS: AD CS emette certificati per i DC, abilitando LDAPS (porta 636).
   Critico per: comunicazioni LDAP cifrate, Azure AD Connect, applicazioni.

3. Kerberos PKINIT: autenticazione smart card tramite certificati.
   Il DC verifica il certificato dell'utente e emette un TGT Kerberos.

4. 802.1X e RADIUS/NPS: i certificati AD CS vengono usati per
   l'autenticazione di rete wireless e wired.

5. Secure Email (S/MIME): certificati per la firma e cifratura email.

6. Code Signing: certificati per la firma del codice.
```

```powershell
# Verificare i certificati dei DC (fondamentali per LDAPS)
Get-ChildItem Cert:\LocalMachine\My | Where-Object {
    $_.EnhancedKeyUsageList.ObjectId -contains "1.3.6.1.5.5.7.3.1"
} | Select-Object Subject, Issuer, NotBefore, NotAfter, Thumbprint

# Verificare LDAPS (porta 636)
Test-NetConnection DC01.corp.contoso.com -Port 636

# Verificare i template pubblicati in AD
Get-ADObject -SearchBase "CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=corp,DC=contoso,DC=com" `
    -Filter {objectClass -eq "pKICertificateTemplate"} -Properties displayName |
    Select-Object displayName
```

---

## Cmdlet PowerShell AD — Riferimento

### Gestione Utenti

```powershell
# Cercare utenti
Get-ADUser -Identity "mrossi"                              # Per sAMAccountName
Get-ADUser -Filter 'Name -like "Mario*"'                   # Per filtro
Get-ADUser -LDAPFilter "(department=IT)"                   # Per filtro LDAP
Get-ADUser -Filter * -SearchBase "OU=Italia,OU=Utenti,DC=corp,DC=contoso,DC=com"  # Per OU

# Creare utente
New-ADUser -Name "Mario Rossi" -SamAccountName "mrossi" `
    -UserPrincipalName "mrossi@corp.contoso.com" `
    -Path "OU=Italia,OU=Utenti,DC=corp,DC=contoso,DC=com" `
    -AccountPassword (ConvertTo-SecureString "P@ssw0rd!" -AsPlainText -Force) `
    -Enabled $true

# Modificare utente
Set-ADUser -Identity "mrossi" -Title "Sysadmin" -Department "IT"

# Disabilitare/abilitare
Disable-ADAccount -Identity "mrossi"
Enable-ADAccount -Identity "mrossi"

# Account scaduti, bloccati, password scaduta
Search-ADAccount -AccountExpired
Search-ADAccount -LockedOut
Search-ADAccount -PasswordExpired
Search-ADAccount -AccountInactive -TimeSpan 90.00:00:00

# Password
Set-ADAccountPassword -Identity "mrossi" -Reset `
    -NewPassword (ConvertTo-SecureString "NewP@ss!" -AsPlainText -Force)
Unlock-ADAccount -Identity "mrossi"

# Eliminare utente
Remove-ADUser -Identity "mrossi" -Confirm:$false
```

### Gestione Gruppi

```powershell
Get-ADGroup -Identity "GG-IT-Staff"
Get-ADGroup -Filter 'GroupCategory -eq "Security"'
New-ADGroup -Name "GG-NewGroup" -GroupScope Global -GroupCategory Security `
    -Path "OU=Security,OU=Gruppi,DC=corp,DC=contoso,DC=com"
Add-ADGroupMember -Identity "GG-IT-Staff" -Members "mrossi"
Remove-ADGroupMember -Identity "GG-IT-Staff" -Members "mrossi" -Confirm:$false
Get-ADGroupMember -Identity "GG-IT-Staff" -Recursive
Get-ADPrincipalGroupMembership -Identity "mrossi"
```

### Gestione Computer

```powershell
Get-ADComputer -Identity "WKS-IT-001"
Get-ADComputer -Filter 'OperatingSystem -like "*Server*"' -Properties OperatingSystem
New-ADComputer -Name "WKS-NEW-001" -Path "OU=Workstation,OU=Computer,DC=corp,DC=contoso,DC=com"
Remove-ADComputer -Identity "WKS-OLD-001" -Confirm:$false
```

### Gestione OU

```powershell
Get-ADOrganizationalUnit -Filter * | Select-Object Name, DistinguishedName
New-ADOrganizationalUnit -Name "NuovaOU" -Path "DC=corp,DC=contoso,DC=com" `
    -ProtectedFromAccidentalDeletion $true
Set-ADOrganizationalUnit -Identity "OU=NuovaOU,DC=corp,DC=contoso,DC=com" `
    -Description "Descrizione aggiornata"
```

### Spostamento e Operazioni Generiche

```powershell
# Spostare qualsiasi oggetto AD
Move-ADObject -Identity "CN=Mario Rossi,OU=Italia,OU=Utenti,DC=corp,DC=contoso,DC=com" `
    -TargetPath "OU=Germania,OU=Utenti,DC=corp,DC=contoso,DC=com"

# Rinominare oggetto
Rename-ADObject -Identity "CN=VecchioNome,OU=Gruppi,DC=corp,DC=contoso,DC=com" `
    -NewName "NuovoNome"

# Query generiche su oggetti AD
Get-ADObject -Filter {objectClass -eq "contact"} -SearchBase "DC=corp,DC=contoso,DC=com"
Get-ADObject -Filter * -SearchBase "CN=Deleted Objects,DC=corp,DC=contoso,DC=com" `
    -IncludeDeletedObjects

# Recuperare info dominio e foresta
Get-ADDomain
Get-ADForest
Get-ADDomainController -Filter *
Get-ADRootDSE
```

### Domain Controller

```powershell
# Elencare tutti i DC
Get-ADDomainController -Filter * | Select-Object Name, IPv4Address, Site, IsGlobalCatalog, OperatingSystem

# Verificare salute DC
dcdiag /v /c /s:DC01

# Promuovere un server a DC
Install-ADDSDomainController -DomainName "corp.contoso.com" `
    -InstallDns:$true -SiteName "Milano" `
    -Credential (Get-Credential)

# Demote un DC
Uninstall-ADDSDomainController -DemoteOperationMasterRole:$true

# Read-Only Domain Controller (RODC)
Install-ADDSDomainController -DomainName "corp.contoso.com" `
    -ReadOnlyReplica:$true -SiteName "FilialePiccola" `
    -InstallDns:$true
```

---

## Best Practices e Design

### Principi di Design

1. **Minimo numero di domini**: un singolo dominio copre il 90% degli scenari. Usare domini multipli solo per requisiti reali (isolamento policy, compliance, fusioni aziendali).

2. **Schema Tier per l'amministrazione**:
   - **Tier 0**: Domain Controllers, admin accounts AD — massima protezione
   - **Tier 1**: Server e servizi enterprise — protezione alta
   - **Tier 2**: Workstation e utenti standard — protezione standard
   - Account Tier 0 NON devono MAI fare logon su macchine Tier 1 o 2

3. **Naming convention consistente**: definire e documentare standard per nomi utenti, gruppi, computer, GPO, OU.

4. **Backup regolare**: backup System State di almeno un DC per dominio, testare il restore periodicamente.

5. **Monitorare la salute AD**:
```powershell
# Script di health check quotidiano
dcdiag /v /c /e > C:\Logs\dcdiag-$(Get-Date -Format yyyyMMdd).txt
repadmin /replsummary > C:\Logs\repl-$(Get-Date -Format yyyyMMdd).txt
Get-ADDomainController -Filter * | ForEach-Object {
    [PSCustomObject]@{
        Name = $_.Name
        Raggiungibile = Test-Connection $_.HostName -Count 1 -Quiet
        IP = $_.IPv4Address
        Site = $_.Site
    }
}
```

6. **Proteggere gli account privilegiati**: MFA per admin, PAW (Privileged Access Workstations), gruppi admin vuoti di default, audit costante.

7. **Documentare tutto**: topologia, trust, GPO, delega, naming convention, piano DR.

8. **Minimo due DC per dominio**: mai un singolo DC. Idealmente, 2 DC per site principale, 1 RODC per site remoto piccolo.

9. **DNS integrato con AD**: non usare DNS stand-alone per la zona del dominio AD. Usare sempre zone AD-Integrated.

10. **SYSVOL su DFS-R**: verificare che la replica SYSVOL sia migrata da FRS a DFS-R (FRS e deprecato).

### Checklist per Nuovi Deployment

```
PRE-DEPLOYMENT:
[ ] Definire naming convention (dominio, OU, utenti, computer, gruppi, GPO)
[ ] Progettare topologia foresta/dominio/tree (single-domain nella maggior parte dei casi)
[ ] Definire schema IP e subnet per i sites AD
[ ] Definire schema di delega (chi gestisce cosa)
[ ] Definire modello Tier (T0/T1/T2) per gli account amministrativi
[ ] Pianificare il livello funzionale target
[ ] Verificare i prerequisiti hardware e rete
[ ] Definire il piano di backup e DR

DEPLOYMENT — DC:
[ ] Installare almeno 2 DC nel site primario
[ ] Installare DNS integrato con AD
[ ] Configurare il PDC Emulator per sincronizzarsi con NTP esterno
[ ] Rendere tutti i DC anche Global Catalog (in single-domain)
[ ] Verificare record SRV DNS
[ ] Verificare replica con repadmin /replsummary
[ ] Creare site e subnet per ogni sede
[ ] Configurare site link con costi e schedule appropriati

DEPLOYMENT — STRUTTURA:
[ ] Creare la struttura OU secondo il modello di delega
[ ] Proteggere tutte le OU da eliminazione accidentale
[ ] Abilitare AD Recycle Bin
[ ] Creare i gruppi di delega
[ ] Configurare le deleghe sulle OU
[ ] Creare la Default Domain Policy (password, lockout)
[ ] Creare GPO baseline per workstation e server
[ ] Configurare il Central Store per ADMX
[ ] Creare Fine-Grained Password Policy per admin

SICUREZZA:
[ ] Creare account admin separati (Tier 0/1/2)
[ ] Aggiungere admin critici a Protected Users
[ ] Configurare LAPS per le password locali
[ ] Audit policy (4624, 4625, 4740, 4768, 4769, 4776)
[ ] Disabilitare o limitare NTLM
[ ] Abilitare SMB Signing
[ ] Abilitare LDAP Signing
[ ] Configurare Credential Guard sulle workstation
[ ] Verificare SID Filtering sulle trust (se presenti)

POST-DEPLOYMENT:
[ ] Verificare salute con dcdiag /v /c /e
[ ] Verificare replica con repadmin /replsummary
[ ] Testare login da client
[ ] Testare applicazione GPO con gpresult /h
[ ] Documentare la topologia, le deleghe, le GPO
[ ] Configurare monitoring e alerting
[ ] Testare il restore da backup
[ ] Pianificare revisione quarterly delle deleghe e dei gruppi admin
```

---

## Troubleshooting — 25+ Problemi Comuni

### 1. Impossibile joinare al dominio

```powershell
# Cause comuni:
# - DNS errato: il client non risolve il dominio
# - Connettivita: porte bloccate (53, 88, 135, 139, 389, 445, 636, 3268, 49152-65535)
# - Account computer: limite di join raggiunto (default 10 per utente)
# - Credenziali: l'utente non ha permessi di join

# Diagnostica:
nslookup corp.contoso.com                    # Il client risolve il dominio?
nslookup -type=SRV _ldap._tcp.dc._msdcs.corp.contoso.com  # Trova i DC?
Test-NetConnection DC01 -Port 389           # LDAP raggiungibile?
Test-NetConnection DC01 -Port 88            # Kerberos raggiungibile?
nltest /dsgetdc:corp.contoso.com            # Trova un DC?

# Se il limite di join e raggiunto (ms-DS-MachineAccountQuota):
Get-ADObject -Identity (Get-ADDomain).DistinguishedName -Properties ms-DS-MachineAccountQuota
```

### 2. Account lockout continuo

```powershell
# Cercare l'origine del lockout:
# Event ID 4740 sul PDC Emulator → mostra il Caller Computer Name
Get-WinEvent -ComputerName (Get-ADDomain).PDCEmulator `
    -FilterHashtable @{LogName='Security'; Id=4740} -MaxEvents 50 |
    ForEach-Object {
        $xml = [xml]$_.ToXml()
        [PSCustomObject]@{
            Time = $_.TimeCreated
            User = $xml.Event.EventData.Data[0].'#text'
            CallerComputer = $xml.Event.EventData.Data[1].'#text'
        }
    }

# Cause comuni:
# - Sessioni RDP aperte con password vecchia
# - Servizi Windows con credenziali vecchie
# - Scheduled task con credenziali vecchie
# - Dispositivi mobili (email) con password cached
# - Drive mappati con password cached
# - Applicazioni con credenziali salvate
```

### 3. Replica AD fallisce

```powershell
# Diagnostica:
repadmin /showrepl DC01                     # Stato replica dettagliato
repadmin /replsummary                       # Vista d'insieme
repadmin /failcache                         # Errori recenti
dcdiag /test:replications /s:DC01           # Test diagnostico

# Errori comuni:
# - Error 8453: accesso replica negato → verificare permessi
# - Error 8524: DNS lookup failed → DC non risolvibili via DNS
# - Error 1256: connessione al partner fallita → firewall, rete
# - Error 8614: AD non replica a causa di USN rollback → ripristinare DC

# Riparare:
repadmin /syncall DC01 /APed               # Forzare replica completa
```

### 4. GPO non si applica

Vedere la sezione [GPO Troubleshooting](#gpo-troubleshooting) per la procedura diagnostica completa in 10 passi.

### 5. Autenticazione fallisce (Kerberos)

```powershell
# Diagnostica:
klist                                       # Ticket correnti?
klist purge                                 # Pulire cache
nltest /dsgetdc:corp.contoso.com            # Trova DC?
w32tm /stripchart /computer:DC01            # Clock skew?

# Cause comuni:
# - Clock skew > 5 minuti → sincronizzare tempo
# - SPN duplicato → setspn -X
# - SPN mancante → setspn -S
# - DNS non risolve il server per FQDN → verificare DNS
# - Account computer scaduto → Reset-ComputerMachinePassword
```

### 6. DNS non registra i record SRV

```powershell
# Verificare:
dcdiag /test:dns /DnsDynamicUpdate /DnsRecordRegistration /s:DC01
nltest /dsregdns                            # Forzare ri-registrazione
ipconfig /registerdns
Restart-Service Netlogon

# Cause comuni:
# - Zona DNS non permette dynamic update → Set-DnsServerPrimaryZone -DynamicUpdate Secure
# - Il DC non ha permessi di scrivere nella zona DNS
# - Il servizio DNS non e attivo sul DC
```

### 7. FSMO Role Holder non raggiungibile

```powershell
netdom query fsmo                           # Dove sono i ruoli?
# Se il DC con un ruolo FSMO e offline:
# Per PDC Emulator: seize immediatamente (critico)
# Per RID Master: seize se i pool RID si stanno esaurendo
# Per Schema/DomainNaming/Infrastructure: seize solo se necessario
```

### 8. SYSVOL vuoto o non replicato

```powershell
# Verificare stato DFS-R per SYSVOL
Get-DfsrState
dfsrdiag pollad
dcdiag /test:sysvolcheck /s:DC01

# Verificare che SYSVOL sia condiviso
net share | findstr SYSVOL

# Se SYSVOL e corrotto: authoritative restore dal DC con i dati corretti
# Seguire la procedura Microsoft KB per "authoritative DFS-R SYSVOL restore"
```

### 9. Trust relationship rotta tra workstation e dominio

```powershell
# Errore: "The trust relationship between this workstation and the primary domain failed"
# Causa: la password dell'account computer e desincronizzata

# Fix (da account locale admin sulla workstation):
Test-ComputerSecureChannel -Repair -Credential (Get-Credential CORP\admin)

# Alternativa:
Reset-ComputerMachinePassword -Server DC01 -Credential (Get-Credential CORP\admin)

# Ultima risorsa: unjoin e rejoin al dominio
```

### 10. Tempo desincronizzato

```powershell
# Verificare:
w32tm /query /status
w32tm /query /peers
w32tm /monitor /domain:corp.contoso.com

# Fix PDC Emulator (deve sincronizzarsi con fonte esterna):
w32tm /config /manualpeerlist:"time.windows.com,0x9" /syncfromflags:manual /reliable:YES /update
Restart-Service w32time
w32tm /resync

# Fix altri DC (devono sincronizzarsi con PDC Emulator):
w32tm /config /syncfromflags:domhier /update
Restart-Service w32time
```

### 11. Lingering Objects

```powershell
# Lingering objects: oggetti che sono stati eliminati su un DC ma persistono su altri
# perche la replica e stata interrotta per piu del tombstone lifetime.

# Diagnosi:
repadmin /removelingeringobjects DC02 DC01 "DC=corp,DC=contoso,DC=com" /advisory_mode

# Rimozione:
repadmin /removelingeringobjects DC02 DC01 "DC=corp,DC=contoso,DC=com"

# Abilitare strict replication consistency (impedisce lingering objects):
repadmin /regkey DC01 +strict
```

### 12. USN Rollback

```powershell
# USN Rollback: un DC e stato ripristinato da un backup/snapshot vecchio,
# causando USN incongruenti con gli altri DC.
# GRAVITA CRITICA: puo causare corruzione della replica.

# Sintomi:
# - Event ID 2095 nel log Directory Service
# - Il DC si mette in "quarantena" e smette di replicare

# Fix: l'unica soluzione e demote e re-promote il DC.
# NON ripristinare MAI un DC da snapshot VM senza usare gli
# strumenti di checkpoint supportati da AD (VM-GenerationID).
```

### 13. Global Catalog non disponibile

```powershell
# Sintomi:
# - Login lento o fallito (Universal Group Membership non risolvibile)
# - Exchange: GAL non disponibile

# Diagnostica:
Get-ADDomainController -Filter {IsGlobalCatalog -eq $true}
Test-NetConnection DC01 -Port 3268          # LDAP GC
nltest /dsgetdc:corp.contoso.com /gc        # Trova un GC?

# Fix: promuovere un DC a GC
# AD Sites and Services → DC → NTDS Settings → General → Global Catalog: checked
```

### 14. SPN duplicato

```powershell
# SPN duplicati causano fallimento Kerberos (il KDC non sa quale account usare)
setspn -X                                   # Trova tutti i duplicati

# Fix: rimuovere il duplicato
setspn -D HTTP/webapp.contoso.com old-account

# Registrare lo SPN sull'account corretto
setspn -S HTTP/webapp.contoso.com correct-account
```

### 15. Password dell'account krbtgt compromessa

```powershell
# Se l'hash krbtgt e compromesso, l'attaccante puo forgiare Golden Ticket.
# Reset della password krbtgt (DA FARE DUE VOLTE, con intervallo > replica):

# 1. Prima rotazione:
Set-ADAccountPassword -Identity krbtgt -Reset `
    -NewPassword (ConvertTo-SecureString ([System.Web.Security.Membership]::GeneratePassword(32,8)) `
    -AsPlainText -Force)

# 2. Verificare che la replica sia completata su TUTTI i DC:
repadmin /replsummary

# 3. Dopo almeno 10 ore (lifetime TGT), seconda rotazione:
Set-ADAccountPassword -Identity krbtgt -Reset `
    -NewPassword (ConvertTo-SecureString ([System.Web.Security.Membership]::GeneratePassword(32,8)) `
    -AsPlainText -Force)

# NOTA: il reset krbtgt invalida TUTTI i TGT esistenti.
# Tutti gli utenti/servizi dovranno ri-autenticarsi.
# Pianificare in una finestra di manutenzione.
```

### 16. AD Database corrotto

```powershell
# Controllare l'integrita del database:
# (Richiede DSRM — Directory Services Restore Mode)
# Avviare in DSRM → ntdsutil → activate instance ntds → files → integrity

# Riparazione semantica:
# ntdsutil → semantic database analysis → go

# Se il database e irrecuperabile:
# 1. Demote il DC corrotto
# 2. Pulire i metadati
# 3. Re-promote da un DC sano
```

### 17. Group membership non si aggiorna

```powershell
# Causa comune: il token Kerberos contiene i gruppi al momento dell'emissione.
# Modifiche ai gruppi richiedono un nuovo TGT.

# Fix rapido:
klist purge                                 # Pulire cache ticket
# L'utente deve fare logoff/logon per ottenere un nuovo TGT con i gruppi aggiornati

# Se il problema persiste:
# - Verificare replica: le modifiche sono su tutti i DC?
# - Verificare il GC: i gruppi universali sono aggiornati?
repadmin /showattr DC01 "CN=Mario Rossi,OU=Utenti,DC=corp,DC=contoso,DC=com" /atts:memberOf
```

### 18. Secure Channel rotto (tra DC)

```powershell
# Verificare:
nltest /sc_verify:corp.contoso.com

# Fix:
netdom resetpwd /s:DC01 /ud:corp\admin /pd:*

# Se non funziona: demote e re-promote il DC
```

### 19. AD non si avvia dopo restore

```powershell
# Avviare in DSRM (Directory Services Restore Mode):
# F8 durante il boot → Directory Services Restore Mode
# Usare la password DSRM impostata durante la promozione

# Verificare database:
# ntdsutil → activate instance ntds → files → integrity

# Se restore autoritativo necessario:
# ntdsutil → authoritative restore → restore subtree "OU=Utenti,DC=corp,DC=contoso,DC=com"
```

### 20. DNS Zone transfer fallisce

```powershell
# Per zone AD-Integrated: non usa zone transfer tradizionali (usa replica AD)
# Per zone secondarie standard:
Get-DnsServerZone "secondaria.com" | Select-Object ZoneType, MasterServers
nslookup -type=AXFR secondaria.com master-dns-server

# Verificare che il master consenta zone transfer al secondario
```

### 21. Troppi errori nei log Directory Service

```powershell
# Verificare eventi critici:
Get-WinEvent -LogName "Directory Service" -MaxEvents 100 |
    Where-Object { $_.Level -le 2 } |  # 1=Critical, 2=Error
    Select-Object TimeCreated, Id, Message

# Eventi comuni da investigare:
# 1084 — Replica fallita
# 1311 — KCC non riesce a generare la topologia
# 2042 — Tombstone lifetime superato (lingering objects probabile)
# 2095 — USN rollback rilevato
```

### 22. LDAPS non funziona

```powershell
# LDAPS richiede un certificato sul DC con:
# - Subject o SAN che corrisponda al FQDN del DC
# - EKU: Server Authentication
# - Emesso da una CA trusted dal client

# Verificare:
Test-NetConnection DC01.corp.contoso.com -Port 636
openssl s_client -connect DC01.corp.contoso.com:636 -showcerts

# Se il certificato non c'e:
# 1. Verificare che AD CS sia configurato
# 2. Creare un template per DC con Server Authentication EKU
# 3. Pubblicare il template
# 4. Forzare auto-enrollment: certutil -pulse
```

### 23. Fine-Grained Password Policy non si applica

```powershell
# Verificare quale PSO si applica:
Get-ADUserResultantPasswordPolicy -Identity "mrossi"

# Verificare le PSO e i loro soggetti:
Get-ADFineGrainedPasswordPolicy -Filter * | ForEach-Object {
    [PSCustomObject]@{
        Nome = $_.Name
        Precedenza = $_.Precedence
        MinLength = $_.MinPasswordLength
        Soggetti = (Get-ADFineGrainedPasswordPolicySubject -Identity $_.Name).Name -join ","
    }
}

# Ricordare: le PSO si applicano a UTENTI e GRUPPI, non a OU.
# La precedenza piu bassa (numero piu piccolo) vince.
```

### 24. RODC non sincronizza

```powershell
# Read-Only Domain Controller:
# - Non accetta scritture dirette
# - Deve replicare da un DC scrivibile

# Verificare:
repadmin /showrepl RODC01
Get-ADDomainController RODC01 -Properties IsReadOnly

# Se la PRP (Password Replication Policy) e troppo restrittiva:
Get-ADDomainControllerPasswordReplicationPolicy -Identity RODC01 -Allowed
Get-ADDomainControllerPasswordReplicationPolicy -Identity RODC01 -Denied
```

### 25. Demote DC fallisce

```powershell
# Se un DC non puo essere demote normalmente:
# 1. Tentare con -ForceRemoval
Uninstall-ADDSDomainController -ForceRemoval

# 2. Pulire i metadati manualmente:
# ntdsutil → metadata cleanup → connections → connect to server DC01 →
# quit → select operation target → list domains → select domain 0 →
# list sites → select site 0 → list servers in site → select server X →
# quit → remove selected server

# 3. Pulire i record DNS del DC rimosso
# 4. Pulire gli oggetti AD del DC rimosso
```

---

## FAQ — Domande Frequenti

**D1: Quanti DC devo avere per dominio?**
Minimo 2 per alta affidabilita. Per sedi remote con pochi utenti, considerare un RODC. Per sedi grandi, 2-3 DC scrivibili. Ogni site con utenti dovrebbe avere almeno 1 DC (altrimenti il logon e lento perche attraversa il WAN).

**D2: Posso tornare indietro dopo aver alzato il livello funzionale?**
No. L'innalzamento del livello funzionale e irreversibile. L'unico "rollback" e il ripristino dell'intera foresta da backup. Testare sempre in lab prima.

**D3: Quando devo usare un dominio separato invece di una OU?**
Quasi mai. Un dominio separato ha senso solo per: requisiti di isolamento delle policy password (pre-2008, ora le PSO risolvono), fusioni aziendali temporanee, compliance che richiede isolamento reale, organizzazioni con amministrazione IT completamente separata.

**D4: Global Catalog su tutti i DC o solo su alcuni?**
In ambiente single-domain: TUTTI i DC come GC (nessun overhead di replica aggiuntivo). In multi-domain: almeno 1 GC per site, ma attenzione alla regola dell'Infrastructure Master (non metterlo su un GC a meno che tutti i DC siano GC).

**D5: Quanto spesso devo cambiare la password di krbtgt?**
Microsoft raccomanda ogni 180 giorni come best practice. Dopo un incidente di sicurezza, immediatamente (due volte con intervallo). Il reset invalida tutti i TGT esistenti.

**D6: Come faccio a sapere se NTLM e ancora usato nel mio ambiente?**
Abilitare l'audit NTLM via GPO (Security Options → Restrict NTLM → Audit), poi analizzare gli Event ID 4776 (NTLM auth) e gli eventi nel log "Microsoft-Windows-NTLM/Operational". Solo dopo aver identificato tutto l'uso di NTLM si puo procedere al blocco progressivo.

**D7: Devo usare FRS o DFS-R per SYSVOL?**
DFS-R, senza discussione. FRS e deprecato dal 2008. Se il dominio usa ancora FRS, migrare a DFS-R con `dfsrmig /SetGlobalState`. Richiede livello funzionale 2008+.

**D8: Come proteggo gli account privilegiati da Kerberoasting?**
1. Usare gMSA per i service accounts (password 240 caratteri, rotazione automatica). 2. Per gli account utente con SPN, password > 25 caratteri. 3. Disabilitare RC4 e forzare AES per i service accounts. 4. Monitorare Event ID 4769 per richieste TGS anomale.

**D9: Cosa succede se tutti i DC di un site vanno offline?**
I client tentano di autenticarsi con i DC di un altro site (determinato dal costo del site link). Il logon sara piu lento a causa della latenza WAN. Se anche tutti i DC della foresta vanno offline, nessuna autenticazione di dominio e possibile (solo cached credentials per offline logon).

**D10: Posso usare Azure AD (Entra ID) senza AD on-premises?**
Si, e il modello "cloud-only". Non richiede Azure AD Connect. Gli utenti sono creati direttamente in Entra ID. Ma si perde: GPO, NTLM/Kerberos per app legacy, file share on-prem integrati con AD, stampa integrata con AD.

**D11: Come faccio backup e DR di Active Directory?**
Backup del System State di almeno un DC per dominio con Windows Server Backup o tool enterprise (Veeam, CommVault). Testare il restore in lab quarterly. Documentare la procedura di forest recovery (Microsoft ha un whitepaper dettagliato). Il backup VM snapshot e supportato solo con VM-GenerationID.

**D12: Quante GPO sono troppe?**
Non c'e un numero massimo assoluto, ma ogni GPO aggiunta aumenta il tempo di boot/logon. Con > 50 GPO per un oggetto, investigare il consolidamento. Usare `gpresult /h` per misurare il tempo di elaborazione. GPO vuote o disabilitate devono essere rimosse.

**D13: Come gestisco gli account di servizio?**
Preferire gMSA (Group Managed Service Accounts) per tutti i nuovi servizi. Per servizi che non supportano gMSA (applicazioni legacy), usare account di servizio dedicati con password lunghe (>25 caratteri), rotazione periodica, e principio del minimo privilegio. MAI usare Domain Admin come service account.

**D14: Cosa fare dopo un ransomware che ha cifrato i DC?**
1. Isolare la rete. 2. Ripristinare da backup offline (non connesso alla rete durante l'attacco). 3. Seguire la procedura Microsoft di "AD Forest Recovery". 4. Resettare la password krbtgt due volte. 5. Resettare tutte le password (inclusi tutti gli account admin e service). 6. Verificare che nessun malware persistente sia nei GPO o negli script di logon in SYSVOL. 7. Abilitare monitoring aggressivo per rilevare persistenza.

**D15: Qual e la differenza tra lastLogon e lastLogonTimestamp?**
`lastLogon` e aggiornato ad ogni logon ma NON e replicato tra DC (ogni DC ha il suo valore). Per trovare il vero ultimo logon, bisogna interrogare TUTTI i DC. `lastLogonTimestamp` e replicato ma con un ritardo di default di 14 giorni (per ridurre il traffico di replica). Per audit accurato, usare `lastLogon` su tutti i DC.

**D16: Come configuro AD per supportare Linux/macOS?**
Linux e macOS possono joinare AD usando: SSSD (Linux), PBIS, Centrify, o il built-in di macOS (Directory Utility). Richiedono: DNS funzionante, Kerberos raggiungibile (porta 88), LDAP raggiungibile (porta 389/636). Per macOS: apple-specific MDM profile puo configurare il binding AD. Per Linux con SSSD: configurare `/etc/sssd/sssd.conf` con il dominio AD.

**D17: Come funziona la replica di un cambio password?**
Quando un utente cambia password: 1. La modifica viene scritta sul DC locale. 2. Il DC locale invia immediatamente (urgent replication) la modifica al PDC Emulator. 3. Il PDC Emulator e il "giudice finale" per le password. 4. Se un utente prova a logon su un DC che non ha ancora la nuova password, quel DC contatta il PDC Emulator per una seconda verifica prima di rifiutare.

---

> **Riferimenti correlati nel modulo 03-WINDOWS-POWERUSER:**
> - [02-powershell.md](02-powershell.md) — PowerShell avanzato
> - [21-group-policy-guida-completa.md](21-group-policy-guida-completa.md) — Group Policy in dettaglio
> - [25-active-directory-design-avanzato.md](25-active-directory-design-avanzato.md) — Design AD avanzato
> - [28-pki-certificati-guida-completa.md](28-pki-certificati-guida-completa.md) — PKI e certificati
> - [30-identita-ibrida-azure-ad-dettaglio.md](30-identita-ibrida-azure-ad-dettaglio.md) — Azure AD Connect
> - [33-multi-forest-ad-trust.md](33-multi-forest-ad-trust.md) — Multi-forest e trust
> - [34-disaster-recovery-ad-pki.md](34-disaster-recovery-ad-pki.md) — DR per AD e PKI

## Esercizi

1. Descrivere la differenza tra security boundary e replication boundary in AD, e spiegare perché una forest rappresenta il confine di sicurezza.
2. Creare un lab con due DC in un dominio: promuovere il secondo DC, forzare il trasferimento di un ruolo FSMO e verificare con `netdom query fsmo`.
3. Un utente segnala che non riesce ad autenticarsi dopo un cambio password. Il PDC Emulator è offline. Spiegare cosa succede e come risolvere.
4. Progettare la topologia Sites & Subnets per un'organizzazione con 3 sedi (Roma, Milano, Napoli) connesse con link WAN a 10 Mbps, motivando le scelte di costo e frequenza di replica.

## Auto-valutazione

<details><summary>1. Quali sono i 5 ruoli FSMO e su quale scope operano?</summary>
Schema Master e Domain Naming Master operano a livello forest (uno per forest). RID Master, PDC Emulator e Infrastructure Master operano a livello domain (uno per dominio). Riferimento: sezione «FSMO Roles — Approfondimento».
</details>

<details><summary>2. Cosa succede se il RID Master è offline per un periodo prolungato?</summary>
I DC esauriscono il proprio pool RID e non possono creare nuovi oggetti (utenti, computer, gruppi). Il RID Master deve essere ripristinato o il ruolo trasferito con seize. Riferimento: sezione «RID Master».
</details>

<details><summary>3. Perché DNS è critico per il funzionamento di Active Directory?</summary>
AD usa DNS per localizzare i DC (record SRV in _msdcs), per la replica tra siti e per il processo di domain join. Senza DNS funzionante, nessuna operazione AD procede. Riferimento: sezione «DNS e Active Directory».
</details>

<details><summary>4. Qual è la differenza tra lastLogon e lastLogonTimestamp?</summary>
`lastLogon` è aggiornato ad ogni logon ma non replicato (locale al DC). `lastLogonTimestamp` è replicato ma con ritardo di ~14 giorni. Per audit accurato serve interrogare tutti i DC. Riferimento: sezione «FAQ — D15».
</details>

<details><summary>5. Come si diagnostica un problema di replica tra DC?</summary>
Usare `repadmin /replsummary` per una panoramica, `repadmin /showrepl` per i dettagli per DC, e `dcdiag /v` per una diagnostica completa. Controllare anche DNS, connettività di rete e porte firewall (RPC, LDAP, Kerberos). Riferimento: sezione «Replica e Sites & Subnets».
</details>

<details><summary>6. Cos'è il Tier Model e perché è fondamentale per la sicurezza AD?</summary>
Il Tier Model separa l'ambiente in 3 livelli: Tier 0 (DC e foresta), Tier 1 (server applicativi), Tier 2 (workstation). Le credenziali di un tier superiore non devono mai essere esposte a un tier inferiore, per prevenire lateral movement. Riferimento: sezione «Sicurezza AD».
</details>

## Letture primarie consigliate

- Microsoft Learn — Active Directory Domain Services Overview: <https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/virtual-dc/active-directory-domain-services-overview> (consultato: 2026-05-23)
- Microsoft Learn — AD DS Forest Recovery: <https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/ad-forest-recovery-guide> (consultato: 2026-05-23)
- Microsoft Learn — FSMO Roles: <https://learn.microsoft.com/en-us/troubleshoot/windows-server/active-directory/fsmo-roles> (consultato: 2026-05-23)
- Sean Metcalf — AD Security Best Practices: <https://adsecurity.org/> (consultato: 2026-05-23)

## Collegamenti incrociati

- [02-powershell.md](02-powershell.md) — Cmdlet AD e automazione
- [05-sicurezza-windows.md](05-sicurezza-windows.md) — Kerberos, Credential Guard, hardening
- [21-group-policy-guida-completa.md](21-group-policy-guida-completa.md) — Group Policy
- [25-active-directory-design-avanzato.md](25-active-directory-design-avanzato.md) — Design AD multi-dominio
- [33-multi-forest-ad-trust.md](33-multi-forest-ad-trust.md) — Multi-forest e trust

## Glossario locale

| Termine | Definizione |
|---------|-------------|
| FSMO | Flexible Single Master Operation — ruoli AD che richiedono un singolo DC master |
| Global Catalog | DC che contiene una replica parziale di tutti gli oggetti della forest |
| NTDS.DIT | Database Active Directory su ogni DC (Extensible Storage Engine) |
| Site | Raggruppamento logico di subnet con buona connettività, usato per ottimizzare la replica |
| Trust | Relazione di fiducia tra domini o forest che consente l'accesso cross-domain |
| krbtgt | Account di servizio Kerberos la cui chiave firma tutti i TGT del dominio |
| gMSA | Group Managed Service Account — account di servizio con password gestita automaticamente da AD |
| Tombstone | Oggetto AD eliminato, mantenuto per un periodo (180 gg default) per propagare la cancellazione |
| PDC Emulator | Ruolo FSMO che gestisce backward compatibility, cambio password e time sync |
| Urgent Replication | Replica immediata verso il PDC Emulator per eventi critici (cambio password, lockout) |
