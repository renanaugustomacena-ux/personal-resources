# Identità Ibrida e Azure AD — Guida Approfondita

> **Modulo 30** · **Aggiornamento:** 2026-05-23

| Campo | Valore |
|---|---|
| **Corso** | Windows per ingegneri di sistema |
| **Fase** | Identità e governance cloud |
| **Modulo** | 30 — Identità ibrida e Azure AD |
| **Versione** | 2.1 |
| **Livello** | Proficient (avanzato) |
| **Prerequisiti** | Conoscenza di Active Directory (→ `01-active-directory.md`), basi di Azure AD (→ `07-azure-ad.md`), PowerShell intermedio (→ `02-powershell.md`), networking fondamentale (→ `04-networking-base.md`) |
| **Obiettivi di apprendimento** | 1) Progettare e gestire l'architettura Azure AD Connect (sync rules, filtering, staging mode, Cloud Sync) · 2) Implementare e confrontare PHS, PTA e Federation con AD FS, scegliendo il metodo adeguato allo scenario · 3) Configurare Conditional Access risk-based con Identity Protection (user risk, sign-in risk, risk investigation) · 4) Gestire MFA backup, Temporary Access Pass e la procedura di emergenza "All MFA lost" · 5) Implementare PIM per accesso just-in-time, Access Reviews e Entitlement Management · 6) Configurare Hybrid Azure AD Join, Device Writeback, Group Writeback e Password Writeback · 7) Pianificare e condurre la migrazione da AD FS a PHS/PTA con Staged Rollout · 8) Monitorare la salute della sincronizzazione con Azure AD Connect Health e risolvere errori comuni |
| **Tempo stimato** | 24–32 ore (studio + esercizi + laboratorio) |
| **Ultimo aggiornamento** | 2026-05-23 |
| **Versioni di riferimento** | Microsoft Entra Connect 2.3.x, Microsoft Entra ID (Azure AD), PowerShell 7.5.x, Microsoft Graph API v1.0 |
| **Tag** | `hybrid-identity`, `entra-connect`, `conditional-access`, `PIM`, `MFA`, `PHS`, `PTA`, `AD-FS`, `identity-protection`, `zero-trust` |

## Idee guida
1. **Risk-based CA: detect anomaly login + step-up auth.**
2. **MFA backup: SMS fallback, Authenticator app, FIDO2 key.**
3. **All MFA lost recovery: documented break-glass procedure.**
4. **Privileged Identity Management (PIM) per JIT admin.**

### Mappa Concettuale

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    IDENTITÀ IBRIDA E MICROSOFT ENTRA ID                     │
├──────────────────┬──────────────────┬──────────────────┬────────────────────┤
│  SINCRONIZZAZIONE│  AUTENTICAZIONE  │  GOVERNANCE      │  SICUREZZA         │
│                  │                  │                  │                    │
│ ┌──────────────┐ │ ┌──────────────┐ │ ┌──────────────┐ │ ┌────────────────┐ │
│ │Entra Connect │ │ │ PHS          │ │ │ PIM          │ │ │ Conditional    │ │
│ │Sync Engine   │ │ │ Hash Sync    │ │ │ Just-in-Time │ │ │ Access Engine  │ │
│ └──────────────┘ │ ├──────────────┤ │ ├──────────────┤ │ ├────────────────┤ │
│ ┌──────────────┐ │ │ PTA          │ │ │ Access       │ │ │ Identity       │ │
│ │Cloud Sync    │ │ │ Pass-through │ │ │ Reviews      │ │ │ Protection     │ │
│ │Lightweight   │ │ ├──────────────┤ │ ├──────────────┤ │ │ Risk Engine    │ │
│ └──────────────┘ │ │ AD FS        │ │ │ Entitlement  │ │ ├────────────────┤ │
│ ┌──────────────┐ │ │ Federation   │ │ │ Management   │ │ │ MFA / TAP      │ │
│ │Staging Mode  │ │ ├──────────────┤ │ └──────────────┘ │ │ Backup & Recov.│ │
│ │DR & Testing  │ │ │ Seamless SSO │ │                  │ ├────────────────┤ │
│ └──────────────┘ │ │ Kerberos PRT │ │                  │ │ Password       │ │
│                  │ ├──────────────┤ │                  │ │ Protection     │ │
│                  │ │ CBA / FIDO2  │ │                  │ │ SSPR+Writeback │ │
│                  │ └──────────────┘ │                  │ └────────────────┘ │
├──────────────────┴──────────────────┴──────────────────┴────────────────────┤
│  SYNC FLOW: AD DS ──► Connector Space ──► Metaverse ──► Connector Space    │
│             ──► Microsoft Entra ID   (delta ogni 30 min, full on demand)   │
├─────────────────────────────────────────────────────────────────────────────┤
│  DISPOSITIVI: Azure AD Join │ Hybrid Join │ Registered │ Device Writeback  │
├─────────────────────────────────────────────────────────────────────────────┤
│  WRITEBACK: Password │ Device │ Group │ vers. on-premises ◄── cloud        │
├─────────────────────────────────────────────────────────────────────────────┤
│  MIGRAZIONE: AD FS → Staged Rollout → PHS/PTA (Managed Domain)            │
└─────────────────────────────────────────────────────────────────────────────┘
```


## Indice
- [Panoramica](#panoramica)
- [Azure AD Connect: Architettura e Sync Rules](#azure-ad-connect-architettura-e-sync-rules)
- [Metodi di Autenticazione](#metodi-di-autenticazione)
- [Filtering e Personalizzazione della Sincronizzazione](#filtering-e-personalizzazione-della-sincronizzazione)
- [Seamless Single Sign-On](#seamless-single-sign-on)
- [Registrazione dei Dispositivi](#registrazione-dei-dispositivi)
- [Device Writeback](#device-writeback)
- [Conditional Access Policies](#conditional-access-policies)
- [Risk-Based Conditional Access — Deep Dive](#risk-based-conditional-access--deep-dive)
- [MFA Backup e Procedura di Emergenza](#mfa-backup-e-procedura-di-emergenza)
- [Privileged Identity Management (PIM)](#privileged-identity-management-pim)
- [Access Reviews](#access-reviews)
- [Entitlement Management](#entitlement-management)
- [Monitoraggio e Salute della Sincronizzazione](#monitoraggio-e-salute-della-sincronizzazione)
- [Password Protection e SSPR](#password-protection-e-self-service-password-reset)
- [AD FS Deep Dive](#ad-fs-deep-dive)
- [Certificate-Based Authentication (CBA)](#certificate-based-authentication-cba)
- [Migrazione da AD FS a PHS/PTA (Staged Rollout)](#migrazione-da-ad-fs-a-phspta-staged-rollout)
- [Microsoft Entra Connect Cloud Sync](#microsoft-entra-connect-cloud-sync)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Domande e Risposte (Q&A)](#domande-e-risposte-qa)
- [Esercizi Pratici](#esercizi-pratici)
- [Auto-valutazione](#auto-valutazione)
- [Glossario Locale](#glossario-locale)
- [Letture Primarie Consigliate](#letture-primarie-consigliate)
- [Riferimenti](#riferimenti)

---

## Panoramica

L'identità ibrida è il modello architetturale in cui le identità degli utenti esistono sia nell'Active Directory on-premises che in Azure Active Directory (ora Microsoft Entra ID), con sincronizzazione e autenticazione che operano attraverso entrambi i mondi. Questo modello permette alle organizzazioni di sfruttare l'investimento esistente in Active Directory estendendo le identità al cloud per accedere a Microsoft 365, Azure e migliaia di applicazioni SaaS.

La componente chiave di questa architettura è **Azure AD Connect** (ora Microsoft Entra Connect), il tool di sincronizzazione che mantiene allineate le identità tra l'ambiente on-premises e il cloud. Azure AD Connect supporta diversi metodi di autenticazione — Password Hash Synchronization (PHS), Pass-through Authentication (PTA) e Federation con AD FS — ciascuno con trade-off specifici in termini di sicurezza, complessità e requisiti infrastrutturali.

### Modello di Riferimento: Identità Ibrida Enterprise

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CLOUD (Microsoft Entra ID)                      │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │ Conditional   │  │ Identity     │  │ Microsoft 365 / Azure    │  │
│  │ Access Engine │  │ Protection   │  │ + SaaS Apps              │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────────┘  │
│         │                 │                      │                   │
│  ┌──────┴─────────────────┴──────────────────────┴──────────────┐   │
│  │              Azure AD / Microsoft Entra ID                    │   │
│  │  Users │ Groups │ Devices │ Apps │ Roles │ Policies           │   │
│  └───────────────────────────┬───────────────────────────────────┘   │
│                              │                                       │
│  ┌───────────────────────────┼───────────────────────────────────┐   │
│  │     Sync Layer            │                                    │   │
│  │  ┌──────────┐  ┌─────────┴──────┐  ┌──────────────────────┐  │   │
│  │  │ Cloud    │  │ Azure AD       │  │ PHS / PTA / ADFS     │  │   │
│  │  │ Sync     │  │ Connect        │  │ Authentication       │  │   │
│  │  │ Agent    │  │ Sync Engine    │  │ Pipeline             │  │   │
│  │  └──────────┘  └────────────────┘  └──────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              │                                       │
└──────────────────────────────┼───────────────────────────────────────┘
                               │  HTTPS 443 (outbound only)
┌──────────────────────────────┼───────────────────────────────────────┐
│                     ON-PREMISES                                       │
│                              │                                       │
│  ┌───────────────────────────┴───────────────────────────────────┐   │
│  │              Active Directory Domain Services                  │   │
│  │  Users │ Groups │ Computers │ GPOs │ DNS │ PKI                │   │
│  │                                                                │   │
│  │  ┌──────────┐  ┌──────────────┐  ┌──────────────────────┐    │   │
│  │  │ Domain   │  │ AD FS Farm   │  │ PTA Agents           │    │   │
│  │  │ Contrlrs │  │ + WAP Proxy  │  │ (2+ per HA)          │    │   │
│  │  └──────────┘  └──────────────┘  └──────────────────────┘    │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Requisiti di Licenza

| Funzionalità | Licenza Richiesta |
|---|---|
| Azure AD Connect (base) | Gratuita con qualsiasi tenant Azure AD |
| PHS, PTA, Seamless SSO | Azure AD Free |
| Conditional Access | Azure AD Premium P1 |
| Identity Protection (risk-based) | Azure AD Premium P2 |
| PIM | Azure AD Premium P2 |
| Access Reviews | Azure AD Premium P2 |
| Entitlement Management | Azure AD Premium P2 |
| Azure AD Connect Health | Azure AD Premium P1 |
| Device Writeback | Azure AD Premium P1 |
| Group Writeback | Azure AD Premium P1 |
| SSPR con Password Writeback | Azure AD Premium P1 |

---

## Azure AD Connect: Architettura e Sync Rules

### Architettura Interna

```
┌─────────────────────┐           ┌─────────────────────┐
│  Active Directory    │           │  Azure AD            │
│  On-Premises         │           │  (Entra ID)          │
│                      │           │                      │
│  ┌────────────────┐  │           │  ┌────────────────┐  │
│  │ Users           │  │  Azure   │  │ Users           │  │
│  │ Groups          │  │  AD      │  │ Groups          │  │
│  │ Contacts        │  │ Connect  │  │ Contacts        │  │
│  │ Devices         │  │ ◄──────► │  │ Devices         │  │
│  └────────────────┘  │  (Sync)  │  └────────────────┘  │
│                      │           │                      │
│  Domain Controllers  │           │  Azure AD Services   │
│  AD DS               │           │  Microsoft 365       │
│  DNS                 │           │  Conditional Access  │
└─────────────────────┘           └─────────────────────┘
```

Azure AD Connect è composto da diversi componenti fondamentali:

**Synchronization Engine (Sync Engine):** Il cuore del sistema. Gestisce il flusso di attributi tra i connector spaces (rappresentazioni dello spazio dei nomi di AD on-premises e Azure AD) e il metaverse (database centrale unificato). Il sync engine è basato su FIM/MIM (Forefront Identity Manager / Microsoft Identity Manager) e utilizza un database SQL Server LocalDB o un'istanza SQL Server full per l'archiviazione.

**Connector Space:** Staging area che rappresenta gli oggetti nel sistema connesso. Ogni connector (AD DS e Azure AD) ha il proprio connector space. Gli oggetti nel connector space sono proiezioni degli oggetti reali: non sono gli oggetti AD o Azure AD stessi, ma copie temporanee utilizzate dal sync engine per calcolare le differenze.

**Metaverse:** Database centrale che contiene la vista unificata di tutti gli oggetti sincronizzati, con le regole di join e projection. Quando un oggetto da AD e uno da Azure AD si riferiscono alla stessa identità, vengono "uniti" nel metaverse tramite regole di join.

**Sync Rules:** Regole che definiscono come gli attributi fluiscono tra i connector spaces e il metaverse. Le regole hanno priorità (il numero più basso vince) e possono essere:
- **Inbound**: dal connector al metaverse (importazione)
- **Outbound**: dal metaverse al connector (esportazione)

**Rules Extension:** Codice C# custom che può essere utilizzato per logiche di trasformazione complesse non gestibili con le sync rules standard.

### Architettura del Database Interno

```
┌────────────────────────────────────────────────┐
│              Azure AD Connect Server             │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │           Sync Engine                     │   │
│  │                                            │   │
│  │  ┌────────────┐  ┌───────┐  ┌──────────┐ │   │
│  │  │ AD DS      │  │       │  │ Azure AD │ │   │
│  │  │ Connector  │←→│ Meta  │←→│ Connector│ │   │
│  │  │ Space      │  │ verse │  │ Space    │ │   │
│  │  │            │  │       │  │          │ │   │
│  │  │ Pending    │  │ Join  │  │ Pending  │ │   │
│  │  │ Import     │  │ Rules │  │ Export   │ │   │
│  │  │ Pending    │  │       │  │ Pending  │ │   │
│  │  │ Export     │  │       │  │ Import   │ │   │
│  │  └────────────┘  └───────┘  └──────────┘ │   │
│  │                                            │   │
│  │  ┌──────────────────────────────────────┐ │   │
│  │  │         Sync Rules Engine             │ │   │
│  │  │  Inbound Rules (AD → Metaverse)       │ │   │
│  │  │  Outbound Rules (Metaverse → Azure)   │ │   │
│  │  │  Precedence: lower number = higher    │ │   │
│  │  └──────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────┘   │
│                                                  │
│  ┌──────────────────────────────────────────┐   │
│  │  SQL Server LocalDB (o SQL Full)          │   │
│  │  ADSync database                           │   │
│  └──────────────────────────────────────────┘   │
└────────────────────────────────────────────────┘
```

### Ciclo di Sincronizzazione

```
Delta Sync (ogni 30 minuti di default):
1. Import dal connector AD → legge le modifiche da AD (USN tracking)
2. Synchronization → applica le sync rules inbound, aggiorna il metaverse
3. Import dal connector Azure AD → legge le modifiche da Azure AD (delta link)
4. Synchronization → applica le sync rules inbound dal connector Azure AD
5. Export verso Azure AD → scrive le modifiche pendenti in Azure AD
6. Export verso AD → scrive le modifiche pendenti in AD (writeback)

Full Sync (solo quando necessario):
- Riesegue tutte le sync rules su tutti gli oggetti
- Necessario dopo modifica di sync rules
- Necessario dopo aggiornamento di Azure AD Connect
- Può richiedere ore in ambienti grandi (>100k oggetti)
```

```powershell
# Verificare lo stato della sincronizzazione (sul server Azure AD Connect)
Get-ADSyncScheduler | Select-Object AllowedSyncCycleInterval,
    CurrentlyEffectiveSyncCycleInterval, NextSyncCyclePolicyType,
    NextSyncCycleStartTimeInUTC, SyncCycleEnabled

# Forzare una sincronizzazione delta
Start-ADSyncSyncCycle -PolicyType Delta

# Forzare una sincronizzazione completa (usare con cautela in produzione!)
Start-ADSyncSyncCycle -PolicyType Initial

# Verificare l'ultimo ciclo di sync
Get-ADSyncRunStepResult | Select-Object -First 5 StepNumber, StepType,
    ConnectorName, StartDate, EndDate, StepResult

# Verificare gli errori di sincronizzazione
Get-ADSyncCSObject -ConnectorName "contoso.com - AAD" |
    Where-Object { $_.HasExportError -eq $true } |
    Select-Object DistinguishedName, ObjectType, ExportErrorMessage

# Contare gli oggetti per tipo nel connector space
Get-ADSyncCSObject -ConnectorName "contoso.com" |
    Group-Object ObjectType | Select-Object Name, Count

# Verificare la versione di Azure AD Connect
Get-ADSyncGlobalSettings | Select-Object -ExpandProperty Parameters |
    Where-Object Name -eq "Microsoft.Synchronize.ServerConfigurationVersion"
```

### Sync Rules Personalizzate

Le sync rules sono il cuore della personalizzazione di Azure AD Connect. Ogni regola ha:
- **Name**: nome descrittivo
- **Direction**: Inbound o Outbound
- **Priority (Precedence)**: numero più basso = priorità più alta
- **Connected System**: il connector a cui si applica
- **CS Object Type**: tipo di oggetto nel connector space (user, group, contact)
- **MV Object Type**: tipo di oggetto nel metaverse (person, group)
- **Link Type**: Join (associa), Provision (crea), StickyJoin
- **Scoping Filter**: condizioni per applicare la regola
- **Join Rules**: come associare oggetti CS e MV
- **Transformations**: come trasformare gli attributi

```powershell
# Elencare le sync rules esistenti
Get-ADSyncRule | Select-Object Name, Direction, Priority, Connector,
    SourceObjectType, TargetObjectType, LinkType |
    Sort-Object Priority | Format-Table -AutoSize

# Elencare solo le regole personalizzate (non out-of-box)
Get-ADSyncRule | Where-Object { $_.ImmutableTag -eq $null } |
    Select-Object Name, Direction, Priority | Sort-Object Priority

# Dettaglio di una sync rule specifica
Get-ADSyncRule -Identifier "abc12345-1234-1234-1234-abc123456789" |
    Select-Object Name, Direction, Priority, Connector, SourceObjectType,
    TargetObjectType, LinkType, ScopingFilter, AttributeFlowMappings

# Esempio: creare una sync rule per sincronizzare un attributo personalizzato
# (es. extensionAttribute1 → extension_appid_customField)

# Usare il Synchronization Rules Editor (GUI) per creare regole:
# 1. Aprire Synchronization Rules Editor (Start → Synchronization Rules Editor)
# 2. Add new rule:
#    - Name: "In from AD - Custom - ExtensionAttribute1"
#    - Direction: Inbound
#    - Connected System: contoso.com (AD connector)
#    - CS Object Type: user
#    - MV Object Type: person
#    - Link Type: Join
#    - Precedence: 50 (più basso = priorità più alta)
# 3. Scoping filter: (opzionale) filtrare gli utenti
#    Esempio: department EQUAL "IT"
# 4. Transformations:
#    - FlowType: Direct
#    - Target Attribute: extensionAttribute1
#    - Source: extensionAttribute1
```

### Sync Rule per Filtrare Utenti Esterni

```powershell
# Creare una sync rule che impedisce la sincronizzazione di utenti esterni
# usando l'attributo cloudFiltered

# Sync Rule via PowerShell (alternativa alla GUI)
$rule = New-ADSyncRule `
    -Name "In from AD - Filter External Users" `
    -Direction Inbound `
    -Priority 49 `
    -SourceObjectType user `
    -TargetObjectType person `
    -Connector (Get-ADSyncConnector -Name "contoso.com").Identifier `
    -LinkType Join `
    -ScopingFilter @(
        New-Object Microsoft.IdentityManagement.PowerShell.ObjectModel.ScopeCondition `
            -Property @{
                Attribute = "department"
                Operator = "EQUAL"
                Value = "External"
            }
    ) `
    -Transformations @(
        New-Object Microsoft.IdentityManagement.PowerShell.ObjectModel.FlowMapping `
            -Property @{
                FlowType = "Constant"
                TargetAttribute = "cloudFiltered"
                Source = "True"
            }
    )

Add-ADSyncRule -SynchronizationRule $rule

# Dopo aver aggiunto la regola, eseguire un Full Sync
Start-ADSyncSyncCycle -PolicyType Initial
```

### Gestione Multi-Forest

In ambienti con foreste multiple (es. dopo fusioni e acquisizioni), Azure AD Connect può sincronizzare da più foreste verso un singolo tenant Azure AD.

```
Topologie Multi-Forest Supportate:

1. Multiple forests, single Azure AD tenant (più comune)
   Forest A ──┐
   Forest B ──┼── Azure AD Connect ── Azure AD Tenant
   Forest C ──┘

2. Multiple forests, single Azure AD Connect (con trust)
   Forest A ←trust→ Forest B
         └────────── Azure AD Connect ── Azure AD Tenant

3. Multiple forests, multiple Azure AD Connect (staging)
   Forest A ── AADConnect (active) ──┐
   Forest B ── AADConnect (active) ──┼── Azure AD Tenant
   (ogni forest ha il proprio server AADConnect)

   NON SUPPORTATO: più di un server AADConnect attivo per la stessa forest
   verso lo stesso tenant (causa duplicati)
```

```powershell
# Verificare i connectors configurati (uno per forest)
Get-ADSyncConnector | Select-Object Name, Type, SubType |
    Format-Table -AutoSize

# Verificare le partizioni sincronizzate per ogni connector
foreach ($connector in Get-ADSyncConnector | Where-Object Type -eq "AD") {
    Write-Output "=== $($connector.Name) ==="
    Get-ADSyncConnectorPartition -Connector $connector |
        Select-Object Name, Selected
}

# Gestire i conflitti di soft-match tra foreste
# Quando lo stesso utente esiste in più foreste, AADConnect usa:
# 1. sourceAnchor (ImmutableId) per hard-match
# 2. ProxyAddresses / UPN per soft-match
# Se nessun match: crea oggetti duplicati → errore

# Verificare duplicati
$aadUsers = Get-AzureADUser -All $true
$duplicateUPNs = $aadUsers | Group-Object UserPrincipalName |
    Where-Object Count -gt 1
if ($duplicateUPNs) {
    Write-Warning "Trovati UPN duplicati:"
    $duplicateUPNs | ForEach-Object { Write-Output $_.Name }
}
```

### Source Anchor (ImmutableId)

Il **sourceAnchor** è l'attributo che collega in modo permanente un oggetto AD on-premises al suo corrispondente in Azure AD. Una volta stabilito, non deve mai cambiare.

```powershell
# Verificare quale attributo è usato come sourceAnchor
Get-ADSyncGlobalSettings | Select-Object -ExpandProperty Parameters |
    Where-Object Name -eq "Microsoft.OptionalFeature.AnchorAttribute"

# Default: ms-DS-ConsistencyGuid (raccomandato)
# Legacy: ObjectGUID (non raccomandato per migrazioni tra foreste)

# Verificare il sourceAnchor per un utente specifico
$user = Get-ADUser "mario.rossi" -Properties "ms-DS-ConsistencyGuid"
$immutableId = [System.Convert]::ToBase64String($user."ms-DS-ConsistencyGuid")
Write-Output "ImmutableId: $immutableId"

# Confrontare con Azure AD
$aadUser = Get-AzureADUser -SearchString "mario.rossi"
Write-Output "Azure AD ImmutableId: $($aadUser.ImmutableId)"

# Hard-match manuale (quando un utente non si sincronizza)
# Attenzione: operazione delicata, fare backup prima
$adGuid = (Get-ADUser "mario.rossi" -Properties ObjectGUID).ObjectGUID
$immutableId = [System.Convert]::ToBase64String($adGuid.ToByteArray())
Set-AzureADUser -ObjectId "user@contoso.com" -ImmutableId $immutableId
```

---

## Metodi di Autenticazione

### Password Hash Synchronization (PHS) — Deep Dive

PHS sincronizza un hash derivato dell'hash della password da AD on-premises ad Azure AD. L'autenticazione avviene interamente nel cloud.

#### Processo di Derivazione dell'Hash (Internals)

```
Processo PHS — Come funziona internamente:

1. AD on-premises memorizza la password come NTLM hash (MD4)
   User password: "P@ssw0rd!"
   → MD4 hash: 0x4F2B3C... (16 bytes)

2. Azure AD Connect legge l'NTLM hash dal DC via MS-DRSR
   (Directory Replication Service Remote Protocol)
   Richiede il permesso "Replicating Directory Changes" e
   "Replicating Directory Changes All" sull'oggetto dominio

3. Il PHS agent applica una derivazione a più passaggi:
   a. NTLM hash (16 bytes) viene salato con un salt di 10 bytes
   b. Si applica PBKDF2-HMAC-SHA256 con 1000 iterazioni
   c. Il risultato è un hash di 32 bytes

   Input:  MD4(password)
   Salt:   random(10 bytes)
   Algo:   PBKDF2(HMAC-SHA256, input, salt, 1000 iterations)
   Output: 32 bytes hash + salt

4. L'hash derivato viene inviato ad Azure AD via HTTPS (TLS 1.2+)

5. Azure AD memorizza l'hash derivato nel suo database
   → NON è possibile risalire alla password originale dall'hash Azure AD
   → NON è possibile risalire nemmeno all'NTLM hash
   → L'hash derivato è utilizzabile SOLO per la verifica della password

6. Quando l'utente si autentica su Azure AD:
   Azure AD applica lo stesso processo di derivazione alla password inserita
   e confronta con l'hash memorizzato.

Implicazioni di Sicurezza:
- L'hash in Azure AD NON è l'NTLM hash → non può essere usato per pass-the-hash
- PBKDF2 con 1000 iterazioni rende il brute-force costoso
- Il salt unico per utente previene rainbow table attacks
- La trasmissione è end-to-end encrypted via TLS
```

```
Vantaggi PHS:
+ Nessuna infrastruttura aggiuntiva on-premises
+ Funziona anche se AD on-premises è offline (disaster recovery)
+ Abilita Azure AD Identity Protection:
  - Leaked credential detection (confronto con database di breach)
  - Password spray detection
  - Brute force detection
+ Semplicità operativa (meno componenti = meno failure points)
+ Prerequisito per Seamless SSO

Svantaggi PHS:
- Hash delle password nel cloud (rischio percepito, mitigato dalla derivazione)
- Non supporta smart card authentication nativa
- Non supporta third-party MFA on-premises (ma Azure MFA copre questo)
- La sincronizzazione degli hash ha una latenza di ~2 minuti
  (cambio password on-prem → disponibile in cloud dopo ~2 min)
```

```powershell
# Verificare se PHS è abilitato
Get-ADSyncAADPasswordSyncConfiguration -SourceConnector "contoso.com"

# Verificare lo stato dettagliato del PHS
$status = Get-ADSyncAADPasswordSyncConfiguration -SourceConnector "contoso.com"
$status | Format-List Enabled, TargetConnector, LastSuccessfulSync

# Testare la sincronizzazione password per un utente specifico
Invoke-ADSyncDiagnostics -PasswordSync -ADConnectorName "contoso.com" `
    -ADObjectDN "CN=Mario Rossi,OU=Utenti,DC=contoso,DC=com"

# Verificare gli eventi di sincronizzazione password
Get-WinEvent -LogName "Application" -FilterXPath "*[System[Provider[@Name='Directory Synchronization'] and (EventID=656 or EventID=657)]]" |
    Select-Object -First 20 TimeCreated, Id, Message

# EventID 656 = Password sync started
# EventID 657 = Password sync completed

# Abilitare PHS se disabilitato (richiede riconfigurazione del wizard)
# Azure AD Connect wizard → Change user sign-in → Password Hash Synchronization
# Oppure via PowerShell (solo se già configurato):
Set-ADSyncAADPasswordSyncConfiguration -SourceConnector "contoso.com" -TargetConnector "AADConnector" -Enable $true

# Monitorare la latenza della sincronizzazione password
$lastSync = Get-ADSyncAADPasswordSyncConfiguration -SourceConnector "contoso.com"
$latency = (Get-Date) - $lastSync.LastSuccessfulSync
Write-Output "Latenza ultima sync password: $($latency.TotalMinutes) minuti"
```

### Pass-through Authentication (PTA)

PTA non sincronizza password nel cloud. Quando un utente si autentica, Azure AD invia la richiesta a un agente PTA installato on-premises che valida le credenziali direttamente contro AD.

```
Flusso PTA Dettagliato:

1. Client accede a login.microsoftonline.com
2. Azure AD presenta la pagina di login
3. L'utente inserisce username e password
4. Azure AD cifra la password con la chiave pubblica dell'agente PTA
5. Azure AD inserisce la richiesta nella coda Azure Service Bus del tenant
6. L'agente PTA (sempre connesso via outbound HTTPS) preleva la richiesta
7. L'agente decifra la password con la propria chiave privata
8. L'agente valida le credenziali contro AD via Win32 LogonUser API
9. AD restituisce il risultato: successo, password scaduta, account bloccato, ecc.
10. L'agente invia il risultato ad Azure AD
11. Azure AD concede o nega l'accesso

Componenti:
- PTA Agent: servizio Windows installato su 1+ server on-premises
  (Microsoft AAD App Proxy Connector / Authentication Agent)
- Connessione outbound-only: l'agente inizia la connessione ad Azure
  Service Bus (porta 443 HTTPS) — NON servono porte inbound nel firewall
- Coda Service Bus: le richieste di autenticazione vengono inoltrate via Service Bus
- Chiavi asimmetriche: ogni agente genera una coppia di chiavi RSA
  durante la registrazione. La chiave privata resta sull'agente, la pubblica
  viene caricata su Azure AD.
```

```
Architettura Alta Disponibilità PTA:

        ┌──────────────────────┐
        │     Azure AD          │
        │  ┌────────────────┐  │
        │  │ Service Bus    │  │
        │  │ Queue          │  │
        │  └───┬────────┬───┘  │
        └──────┼────────┼──────┘
               │        │
    HTTPS 443  │        │  HTTPS 443
   (outbound)  │        │  (outbound)
               │        │
  ┌────────────┴──┐  ┌──┴────────────┐
  │ PTA Agent #1  │  │ PTA Agent #2  │
  │ Server A      │  │ Server B      │
  │ (Active)      │  │ (Active)      │
  └───────┬───────┘  └───────┬───────┘
          │                   │
          │   LDAP/Kerberos   │
          ├───────────────────┤
          │                   │
  ┌───────┴───────┐  ┌───────┴───────┐
  │ DC-01         │  │ DC-02         │
  │ (AD DS)       │  │ (AD DS)       │
  └───────────────┘  └───────────────┘

Raccomandazione: minimo 2 agenti PTA per alta disponibilità.
Gli agenti sono stateless — il load balancing è gestito dal Service Bus.
```

```powershell
# Verificare lo stato degli agenti PTA installati
# Via PowerShell (sul server Azure AD Connect)
Get-AzureADConnectAuthenticationAgentGroup

# Verificare la salute dell'agente localmente
Get-Service "AzureADConnectAuthenticationAgent" | Select-Object Status, StartType

# Verificare la connettività dell'agente agli endpoint
$endpoints = @(
    "https://login.microsoftonline.com",
    "https://login.windows.net",
    "https://autologon.microsoftazuread-sso.com",
    "https://sts.windows.net"
)
foreach ($ep in $endpoints) {
    try {
        $result = Invoke-WebRequest -Uri $ep -UseBasicParsing -TimeoutSec 10
        Write-Output "OK ($($result.StatusCode)): $ep"
    } catch {
        Write-Warning "FAIL: $ep - $($_.Exception.Message)"
    }
}

# Installare un agente PTA aggiuntivo (per alta disponibilità)
# 1. Scaricare AADConnectAuthAgentSetup.exe dal portale Azure AD
#    Azure AD → Azure AD Connect → Pass-through Authentication → Download agent
# 2. Eseguire l'installer su un server Windows membro del dominio
# 3. Inserire le credenziali Global Admin durante la registrazione
# 4. L'agente si registra automaticamente con Azure AD

# Diagnostica PTA
# Event logs: Applications and Services Logs → Microsoft → AzureADConnect → AuthenticationAgent
Get-WinEvent -LogName "Microsoft-AzureADConnect-AuthenticationAgent/Admin" -MaxEvents 20 |
    Select-Object TimeCreated, LevelDisplayName, Message
```

### Federation (AD FS) — Panoramica

La federation delega l'intero processo di autenticazione a un Identity Provider on-premises (tipicamente AD FS — Active Directory Federation Services).

```
Flusso Federation:
Client → Azure AD → redirect a AD FS → AD FS autentica contro AD → Token SAML → Azure AD → Client

Vantaggi:
+ Controllo completo sull'autenticazione
+ Supporta smart card e certificate-based auth
+ Supporta third-party MFA solutions (RSA, Duo on-prem)
+ Customizzazione completa della pagina di login
+ Claims rules per logiche di autorizzazione complesse

Svantaggi:
- Infrastruttura complessa (AD FS server, WAP proxy, certificati, load balancer)
- Costo operativo elevato (patching, certificati, monitoring)
- Single point of failure se non ridondato
- Microsoft sta attivamente migrando i clienti verso PHS/PTA
```

### Raccomandazione Microsoft e Matrice di Confronto

```
┌──────────────────────┬──────────┬──────────┬──────────────┐
│ Criterio             │   PHS    │   PTA    │ AD FS        │
├──────────────────────┼──────────┼──────────┼──────────────┤
│ Hash password cloud  │ Sì (der.)│ No       │ No           │
│ Infrastruttura on-p  │ Nessuna  │ Agenti   │ Farm + WAP   │
│ AD offline = auth?   │ Sì       │ No       │ No           │
│ Smart card auth      │ No       │ No       │ Sì           │
│ Identity Protection  │ Completa │ Parziale │ Parziale     │
│ Lockout policy on-p  │ No       │ Sì       │ Sì           │
│ Claims rules custom  │ No       │ No       │ Sì           │
│ Complessità          │ Bassa    │ Media    │ Alta         │
│ HA setup             │ PHS      │ 2+ agent │ Farm + NLB   │
│ Cert-based auth      │ Via CBA  │ No       │ Sì           │
│ 3rd party MFA on-p   │ No       │ No       │ Sì           │
│ Login page custom    │ Branding │ Branding │ Completa     │
│ Latenza auth         │ ~ms      │ ~100ms   │ ~200ms+      │
│ Costo TCO            │ Basso    │ Medio    │ Alto         │
└──────────────────────┴──────────┴──────────┴──────────────┘

Raccomandazione Microsoft: PHS come metodo primario o backup.
```

---

## Filtering e Personalizzazione della Sincronizzazione

### Domain Filtering

```powershell
# Sincronizzare solo specifici domini in un forest multi-dominio
# Configurazione durante il setup di Azure AD Connect:
# Customize synchronization options → Domain/OU filtering

# Verificare i domini configurati
Get-ADSyncConnector -Name "contoso.com" | Select-Object -ExpandProperty Partitions |
    Select-Object Name, Selected
```

### OU Filtering

La forma più comune di filtering: sincronizzare solo gli utenti/computer in specifiche OU.

```powershell
# L'OU filtering si configura nel wizard di Azure AD Connect
# o tramite modifica del connector:

# Verificare le OU incluse nella sincronizzazione
Get-ADSyncConnectorPartition -Connector (Get-ADSyncConnector -Name "contoso.com") |
    Get-ADSyncConnectorPartitionHierarchy

# OU tipicamente INCLUSE:
# OU=Utenti,DC=contoso,DC=com
# OU=Gruppi,DC=contoso,DC=com
# OU=ServiceAccounts,DC=contoso,DC=com

# OU tipicamente ESCLUSE:
# OU=AdminTier0 (account Tier 0 non devono MAI essere sincronizzati)
# OU=AdminTier1 (account Tier 1 valutare caso per caso)
# OU=Disabled
# OU=Test
# CN=Computers (default, solo se non serve Hybrid Azure AD Join)

# Aggiungere una nuova OU al filtro via wizard:
# 1. Aprire Azure AD Connect wizard
# 2. Customize synchronization options
# 3. Domain/OU filtering → espandere il tree → selezionare le OU
# 4. Finish → verrà eseguito un Full Sync
```

### Attribute-based Filtering

```powershell
# Filtrare in base a un attributo (es. department)
# Usare il Synchronization Rules Editor:
# 1. Creare una inbound sync rule con scoping filter
# 2. Condition: department NOT EQUAL "External"
# 3. Oppure: extensionAttribute15 EQUAL "SyncToCloud"

# Metodo raccomandato: usare cloudFiltered
# Creare una sync rule che imposta cloudFiltered = TRUE per gli utenti da escludere

# Esempio completo: escludere utenti con department = "Contractor"
# 1. Sync Rule: "In from AD - Filter Contractors"
#    Direction: Inbound
#    Priority: 48
#    Scoping: department EQUAL "Contractor"
#    Transformation: cloudFiltered = Constant "True"

# 2. Dopo la creazione, eseguire Full Sync
Start-ADSyncSyncCycle -PolicyType Initial

# Verificare che l'utente sia filtrato
$csObj = Get-ADSyncCSObject -ConnectorName "contoso.com" -DistinguishedName "CN=John Contractor,OU=Utenti,DC=contoso,DC=com"
$csObj | Select-Object DistinguishedName, IsConnector
# Se cloudFiltered = True, l'oggetto non sarà esportato verso Azure AD
```

### Group-based Filtering

```powershell
# Sincronizzare solo i membri di un gruppo specifico
# Configurazione nel wizard di Azure AD Connect:
# "Customize synchronization options" → "Sync filtering" → "Group"
# Specificare il gruppo: GRP-AzureAD-Sync

# IMPORTANTE: Limitazioni del Group-based filtering:
# 1. È supportato SOLO per il provisioning iniziale (primo setup)
# 2. Dopo il primo sync, è NECESSARIO passare a OU-based o attribute-based
# 3. Il group-based filtering non supporta gruppi nested
# 4. Supporta un solo gruppo
# 5. NON è una funzionalità di produzione — è pensata per piloting

# Strategia raccomandata per produzione:
# 1. Usare group-based filtering per il pilota iniziale (max 50k utenti nel gruppo)
# 2. Identificare le OU che contengono gli utenti del pilota
# 3. Convertire a OU-based filtering quando si espande
# 4. Aggiungere attribute-based filtering per eccezioni
```

---

## Seamless Single Sign-On

Seamless SSO permette agli utenti su computer uniti al dominio nella rete aziendale di accedere automaticamente ai servizi cloud Microsoft senza inserire le credenziali. Funziona con PHS e PTA.

### Funzionamento Interno

```
Flusso Seamless SSO Dettagliato:

1. Utente accede a portal.office.com dal PC unito al dominio
2. Azure AD richiede autenticazione → redirect a login.microsoftonline.com
3. Azure AD inserisce nell'URL il parametro domain_hint (o l'utente inserisce UPN)
4. Il browser (IE/Edge/Chrome) rileva che l'URL è nella zona Intranet
5. Il browser invia automaticamente un Kerberos ticket per il SPN:
   HTTP/autologon.microsoftazuread-sso.com
6. Il ticket è emesso dal KDC (Domain Controller) usando la chiave
   dell'account computer AZUREADSSOACC$ in Active Directory
7. Azure AD riceve il ticket Kerberos
8. Azure AD lo decifra usando la chiave di Kerberos sincronizzata
   durante il setup di Seamless SSO
9. Il ticket contiene l'identità dell'utente → Azure AD emette token
10. L'utente è autenticato senza inserire password

Requisiti:
- Computer unito al dominio AD on-premises
- Account computer AZUREADSSOACC$ creato in AD (automatico)
- Kerberos ticket valido → l'utente deve aver fatto logon al dominio
- URL nella zona Intranet del browser
- Browser supportato: IE, Edge (Chromium), Chrome (con estensione), Firefox (con about:config)
```

```powershell
# Abilitare Seamless SSO (durante la configurazione di Azure AD Connect)
# Azure AD Connect wizard → User sign-in → Enable single sign-on

# Verificare che l'account computer AZUREADSSOACC$ esista
Get-ADComputer "AZUREADSSOACC" -Properties * | Select-Object Name, SamAccountName,
    ServicePrincipalName, PasswordLastSet, whenCreated

# Verificare il SPN dell'account
Get-ADComputer "AZUREADSSOACC" -Properties ServicePrincipalName |
    Select-Object -ExpandProperty ServicePrincipalName
# Deve contenere: HTTP/autologon.microsoftazuread-sso.com

# Configurare i siti intranet via GPO per IE/Edge Legacy
# User Configuration → Administrative Templates → Windows Components
#   → Internet Explorer → Internet Control Panel → Security Page
#   → Site to Zone Assignment List:
#   Value: https://autologon.microsoftazuread-sso.com = 1 (Intranet zone)
#   Value: https://aadg.windows.net.nsatc.net = 1

# Per Chrome/Edge Chromium (GPO o reg key)
# HKLM\Software\Policies\Google\Chrome\AuthServerAllowlist
#   Value: "autologon.microsoftazuread-sso.com"
# HKLM\Software\Policies\Microsoft\Edge\AuthServerAllowlist
#   Value: "autologon.microsoftazuread-sso.com"

# Per Firefox:
# about:config → network.negotiate-auth.trusted-uris
#   Value: https://autologon.microsoftazuread-sso.com

# Rotazione della chiave Kerberos di AZUREADSSOACC$
# CRITICO: raccomandata ogni 30 giorni per sicurezza
# Se la chiave viene compromessa, un attaccante può creare ticket Kerberos
# per qualsiasi utente sincronizzato → accesso a tutte le risorse cloud

Update-AzureADSSOForest -OnPremCredentials (Get-Credential) -PreserveCustomPermissionsOnDesktopSsoAccount

# Verificare la data dell'ultima rotazione
Get-ADComputer "AZUREADSSOACC" -Properties PasswordLastSet |
    Select-Object PasswordLastSet
# Se > 30 giorni: eseguire immediatamente la rotazione

# Script per alert automatico sulla rotazione
$ssoAccount = Get-ADComputer "AZUREADSSOACC" -Properties PasswordLastSet
$daysSinceRotation = ((Get-Date) - $ssoAccount.PasswordLastSet).Days
if ($daysSinceRotation -gt 25) {
    Write-Warning "ALERT: AZUREADSSOACC$ password non ruotata da $daysSinceRotation giorni!"
    Write-Warning "Eseguire Update-AzureADSSOForest entro $(30 - $daysSinceRotation) giorni."
}
```

---

## Registrazione dei Dispositivi

### Azure AD Join

Il dispositivo è registrato solo in Azure AD, senza essere unito al dominio AD on-premises. Ideale per dispositivi cloud-only e nuovi deploy senza infrastruttura AD.

```
Flusso Azure AD Join:
Settings → Accounts → Access work or school → Connect → Join Azure AD
→ Inserire credenziali Azure AD → Dispositivo registrato

Il dispositivo riceve:
- Primary Refresh Token (PRT) per SSO a risorse cloud
- Certificato dispositivo (per Conditional Access basato su device)
- Policy da Intune (se configurato MDM auto-enrollment)
- BitLocker recovery keys escrowed in Azure AD
```

### Hybrid Azure AD Join

Il dispositivo è unito sia al dominio AD on-premises che ad Azure AD. Il miglior approccio per organizzazioni ibride che vogliono mantenere la compatibilità con GPO e risorse on-premises.

```powershell
# Prerequisiti per Hybrid Azure AD Join:
# 1. Azure AD Connect configurato con Device options
# 2. Service Connection Point (SCP) in AD configurato
# 3. I computer devono poter raggiungere gli endpoint Azure AD
# 4. Windows 10 1809+ (per domini federati) o Windows 10 1903+ (per managed)

# Verificare il Service Connection Point
$scp = Get-ADObject -SearchBase "CN=Configuration,$(
    (Get-ADRootDSE).rootDomainNamingContext)" `
    -Filter 'objectClass -eq "serviceConnectionPoint" -and Name -eq "62a0ff2e-97b9-4513-943f-0d221bd30080"' `
    -Properties keywords
$scp | Select-Object -ExpandProperty keywords
# Deve restituire:
# azureADId: <TenantID>
# azureADName: <TenantName>

# Configurare SCP tramite Azure AD Connect wizard:
# "Configure device options" → "Configure Hybrid Azure AD Join"

# Verificare lo stato di registrazione su un dispositivo
dsregcmd /status

# Output chiave:
# +----------------------------------------------------------------------+
# |                        Device State                                   |
# +----------------------------------------------------------------------+
# AzureAdJoined: YES
# EnterpriseJoined: NO
# DomainJoined: YES  ← Hybrid = AzureAdJoined YES + DomainJoined YES
# DeviceId: <GUID del dispositivo in Azure AD>
# Thumbprint: <Thumbprint del certificato dispositivo>
# TenantId: <GUID del tenant>

# Diagnostica dettagliata
dsregcmd /status /debug

# Verificare il Primary Refresh Token
dsregcmd /status | Select-String "AzureAdPrt"
# AzureAdPrt: YES = L'utente ha un PRT valido per SSO

# Verificare la connettività agli endpoint richiesti
$endpoints = @(
    "https://enterpriseregistration.windows.net"
    "https://login.microsoftonline.com"
    "https://device.login.microsoftonline.com"
    "https://autologon.microsoftazuread-sso.com"
)
foreach ($ep in $endpoints) {
    try { Invoke-WebRequest $ep -UseBasicParsing -TimeoutSec 10; Write-Output "OK: $ep" }
    catch { Write-Warning "FAIL: $ep" }
}

# Task scheduled per Hybrid Join (Windows 10/11)
# Il join avviene tramite un task schedulato:
# Task Scheduler → Microsoft → Windows → Workplace Join → Automatic-Device-Join
Get-ScheduledTask -TaskPath "\Microsoft\Windows\Workplace Join\" |
    Select-Object TaskName, State, LastRunTime, LastTaskResult
```

### Azure AD Registered (BYOD)

Il dispositivo personale è registrato in Azure AD senza essere unito. Permette l'accesso alle risorse aziendali con MAM (Mobile Application Management) senza gestione completa del dispositivo.

```
Confronto Modalità di Registrazione:

┌────────────────────┬──────────────┬──────────────────┬─────────────┐
│ Aspetto            │ Azure AD     │ Hybrid Azure     │ Azure AD    │
│                    │ Registered   │ AD Join          │ Join        │
├────────────────────┼──────────────┼──────────────────┼─────────────┤
│ Ownership          │ Personale    │ Aziendale        │ Aziendale   │
│ Domain Joined      │ No           │ Sì               │ No          │
│ Azure AD Joined    │ No           │ Sì               │ Sì          │
│ MDM enrollment     │ Opzionale    │ Opzionale        │ Auto        │
│ GPO                │ No           │ Sì               │ No          │
│ SSO cloud          │ App-level    │ PRT + Kerberos   │ PRT         │
│ SSO on-prem        │ No           │ Sì               │ Via VPN     │
│ Conditional Access │ Limitato     │ Completo         │ Completo    │
│ BitLocker escrow   │ No           │ Sì               │ Sì          │
│ Windows Hello      │ No           │ Sì               │ Sì          │
│ Caso d'uso         │ BYOD         │ Corp desktop     │ Cloud-first │
└────────────────────┴──────────────┴──────────────────┴─────────────┘
```

---

## Device Writeback

Il Device Writeback sincronizza gli oggetti dispositivo da Azure AD verso Active Directory on-premises. Questo è necessario per scenari specifici dove l'on-premises deve "conoscere" i dispositivi registrati nel cloud.

### Scenari che Richiedono Device Writeback

```
1. AD FS con Conditional Access basato su dispositivo
   - AD FS verifica se il dispositivo è registrato in Azure AD
   - Senza writeback, AD FS non ha visibilità sui dispositivi cloud

2. Windows Hello for Business Hybrid Certificate Trust
   - Richiede che il dispositivo sia presente in AD per il provisioning
     del certificato tramite NDES (Network Device Enrollment Service)

3. Conditional Access on-premises
   - Applicazioni on-premises protette da AD FS o WAP che richiedono
     device compliance check
```

```powershell
# Abilitare Device Writeback in Azure AD Connect
# 1. Azure AD Connect wizard → Optional features → Device writeback
# 2. Selezionare la forest e il container dove scrivere i dispositivi
#    Default: CN=RegisteredDevices,DC=contoso,DC=com

# Prerequisiti:
# - Azure AD Premium P1 o P2
# - L'account di servizio Azure AD Connect deve avere permessi di scrittura
#   sul container dei dispositivi
# - Schema AD esteso (il wizard lo fa automaticamente)

# Verificare che il container RegisteredDevices esista
Get-ADObject -SearchBase "DC=contoso,DC=com" -Filter 'Name -eq "RegisteredDevices"' |
    Select-Object Name, DistinguishedName, ObjectClass

# Verificare i dispositivi scritti nel container
Get-ADObject -SearchBase "CN=RegisteredDevices,DC=contoso,DC=com" -Filter * -Properties * |
    Select-Object Name, ObjectClass, @{N='DeviceId';E={$_.msDS-DeviceID}},
    @{N='Compliant';E={$_.msDS-IsCompliant}},
    @{N='OS';E={$_.msDS-DeviceOSType}},
    @{N='Enabled';E={$_.msDS-IsEnabled}}

# Verificare che il Device Writeback sia funzionante
$lastRun = Get-ADSyncRunProfileResult -ConnectorName "contoso.com - AAD" -NumberRequested 1
$lastRun | Select-Object RunNumber, StartDate, EndDate, Result,
    CountImportAdd, CountImportUpdate, CountImportDelete

# Troubleshoot: se i dispositivi non vengono scritti
# Verificare i permessi sull'OU RegisteredDevices
$connector = Get-ADSyncConnector -Name "contoso.com"
$serviceAccount = $connector.ConnectivityParameters |
    Where-Object Name -eq "forest-login-user" |
    Select-Object -ExpandProperty Value
Write-Output "Account di servizio: $serviceAccount"
Write-Output "Verificare che abbia: Create msDS-Device objects, Write all properties"
Write-Output "sul container CN=RegisteredDevices"
```

### Group Writeback

Il Group Writeback sincronizza gruppi creati in Microsoft Entra ID verso Active Directory on-premises, consentendo alle applicazioni on-premises di utilizzare gruppi gestiti nel cloud per il controllo degli accessi.

Riferimento: https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/how-to-connect-group-writeback-v2 (consultato: 2026-05-23)

```
┌──────────────────────────────┬──────────────┬──────────────────────────────┐
│ Tipo Gruppo Cloud            │ Writeback    │ Tipo Risultante in AD        │
├──────────────────────────────┼──────────────┼──────────────────────────────┤
│ Microsoft 365 Group          │ Sì           │ Universal Distribution Group │
│ Security Group (cloud-only)  │ Sì (v2)      │ Universal Security Group     │
│ Mail-enabled Security        │ Sì (v2)      │ Universal Security Group     │
│ Distribution Group           │ No           │ N/A                          │
│ Dynamic Membership Group     │ Sì (v2)      │ Universal Security Group     │
└──────────────────────────────┴──────────────┴──────────────────────────────┘

Group Writeback v2 (raccomandato):
- Supporta Security Groups e M365 Groups
- OU di destinazione configurabile (non solo CN=AADConnect di v1)
- Mapping del tipo di gruppo (es. M365 → Security in AD)
- Richiede Azure AD Connect 2.0+ con feature abilitata

Limitazioni:
- NO nested group writeback (membership non ricorsiva)
- Unidirezionale: cloud → on-premises (modifiche in AD non propagate)
- Latenza ~30 minuti (dipende dal ciclo di sync)
- Richiede Azure AD Premium P1
```

```powershell
# Abilitare Group Writeback v2 in Azure AD Connect
# 1. Azure AD Connect wizard → Optional Features → Group Writeback
# 2. Selezionare l'OU di destinazione per i gruppi
#    Raccomandazione: creare una OU dedicata, es. OU=CloudGroups,DC=contoso,DC=com

# Verificare che Group Writeback sia abilitato
Get-ADSyncGlobalSettings | Select-Object -ExpandProperty Parameters |
    Where-Object Name -eq "Microsoft.OptionalFeature.GroupWritebackV2"

# Verificare i gruppi scritti in AD
Get-ADGroup -SearchBase "OU=CloudGroups,DC=contoso,DC=com" -Filter * -Properties * |
    Select-Object Name, GroupCategory, GroupScope,
    @{N='CloudId';E={$_.'msDS-ExternalDirectoryObjectId'}},
    @{N='Source';E={'Cloud Writeback'}}

# Monitorare errori di writeback
Get-ADSyncCSObject -ConnectorName "contoso.com" -ObjectType group |
    Where-Object { $_.HasExportError } |
    Select-Object DistinguishedName, ExportErrorMessage

# Permessi richiesti sull'OU di destinazione per l'account di servizio:
# - Create Group Objects
# - Delete Group Objects
# - Write All Properties su Group Objects
# - Read All Properties su Group Objects
```

---

## Conditional Access Policies

Le Conditional Access policies sono il motore decisionale Zero Trust che valuta ogni richiesta di accesso basandosi su segnali multipli.

### Architettura Decisionale

```
Flusso Decisionale Conditional Access:

Richiesta di accesso
        │
        ▼
┌───────────────────┐
│ Raccolta Segnali  │
│ - User identity   │
│ - Device state    │
│ - Location (IP)   │
│ - Application     │
│ - Sign-in risk    │
│ - User risk       │
│ - Client app      │
│ - Device platform │
└───────┬───────────┘
        │
        ▼
┌───────────────────┐
│ Valutazione       │    ┌──────────────────────────────┐
│ Policy            │───►│ Tutte le policy vengono      │
│ (AND tra policy)  │    │ valutate. Se QUALSIASI       │
│                   │    │ policy blocca → BLOCCO.      │
│                   │    │ Le policy sono cumulative     │
│                   │    │ (non si escludono a vicenda)  │
└───────┬───────────┘    └──────────────────────────────┘
        │
        ▼
┌───────────────────┐
│ Enforcement       │
│ - Block access    │
│ - Grant access    │
│   with controls:  │
│   - MFA           │
│   - Compliant     │
│   - Hybrid Join   │
│   - App protection│
│   - ToU           │
│ - Session ctrl:   │
│   - Sign-in freq  │
│   - Persistent    │
│   - MCAS proxy    │
└───────────────────┘
```

### Policy Risk-Based

```
Policy: "CA001 - Block High-Risk Sign-Ins"
┌───────────────────────────────────────────────┐
│ Assignments:                                   │
│   Users: All users                             │
│   Exclude: Break-glass accounts (2 accounts)   │
│   Cloud apps: All cloud apps                   │
│                                                │
│ Conditions:                                    │
│   Sign-in risk: High                           │
│     (Rilevato da Azure AD Identity Protection:  │
│      - Atypical travel                          │
│      - Anonymous IP (Tor, VPN)                  │
│      - Malware-linked IP                        │
│      - Leaked credentials (PHS required)        │
│      - Password spray                           │
│      - Unfamiliar sign-in properties            │
│      - Token issuer anomaly)                    │
│                                                │
│ Grant: Block access                            │
└───────────────────────────────────────────────┘

Policy: "CA002 - Require MFA for Medium Risk"
┌───────────────────────────────────────────────┐
│ Conditions:                                    │
│   Sign-in risk: Medium                         │
│                                                │
│ Grant: Require MFA                             │
│ Session: Sign-in frequency = 1 hour            │
└───────────────────────────────────────────────┘

Policy: "CA003 - Require Compliant Device for Sensitive Apps"
┌───────────────────────────────────────────────┐
│ Cloud apps: SharePoint, Exchange, Teams        │
│ Conditions:                                    │
│   Device platforms: Windows, iOS, Android      │
│                                                │
│ Grant:                                         │
│   Require device compliant (Intune)            │
│   OR Require Hybrid Azure AD joined device     │
│   AND Require MFA                              │
│                                                │
│ Session: Persistent browser = Never            │
└───────────────────────────────────────────────┘

Policy: "CA004 - Block Legacy Authentication"
┌───────────────────────────────────────────────┐
│ Users: All users                               │
│ Cloud apps: All cloud apps                     │
│ Conditions:                                    │
│   Client apps: Exchange ActiveSync, Other       │
│                clients                          │
│                                                │
│ Grant: Block access                            │
│                                                │
│ NOTA: I protocolli legacy (IMAP, POP3, SMTP    │
│ Auth, legacy EAS) NON supportano MFA e sono    │
│ il vettore #1 per password spray attacks.      │
│ Bloccarli è la prima policy da implementare.   │
└───────────────────────────────────────────────┘

Policy: "CA005 - Require MFA per Amministratori"
┌───────────────────────────────────────────────┐
│ Users: Directory roles:                        │
│   Global Admin, Privileged Role Admin,         │
│   Exchange Admin, SharePoint Admin,            │
│   Security Admin, User Admin,                  │
│   Authentication Admin, Conditional Access     │
│   Admin, Password Admin                        │
│                                                │
│ Cloud apps: All cloud apps                     │
│                                                │
│ Grant: Require MFA                             │
│ AND: Require compliant device OR Hybrid Join   │
└───────────────────────────────────────────────┘

Policy: "CA006 - Geo-Blocking"
┌───────────────────────────────────────────────┐
│ Users: All users                               │
│ Cloud apps: All cloud apps                     │
│ Conditions:                                    │
│   Locations: All locations                     │
│   Exclude: Named locations (Trusted:           │
│     Italia, USA, Germania)                     │
│                                                │
│ Grant: Block access                            │
│                                                │
│ NOTA: Aggiungere paesi dove l'azienda opera.   │
│ Utenti in viaggio possono usare VPN aziendale  │
│ oppure richiedere eccezione temporanea.        │
└───────────────────────────────────────────────┘
```

### Named Locations

```powershell
# Creare named locations via Graph API
$headers = @{
    Authorization  = "Bearer $accessToken"
    "Content-Type" = "application/json"
}

# Named location basata su IP (ufficio)
$ipLocation = @{
    "@odata.type"  = "#microsoft.graph.ipNamedLocation"
    displayName    = "Sede Milano"
    isTrusted      = $true
    ipRanges       = @(
        @{ "@odata.type" = "#microsoft.graph.iPv4CidrRange"; cidrAddress = "203.0.113.0/24" },
        @{ "@odata.type" = "#microsoft.graph.iPv4CidrRange"; cidrAddress = "198.51.100.0/24" }
    )
} | ConvertTo-Json -Depth 4

Invoke-RestMethod -Uri "https://graph.microsoft.com/v1.0/identity/conditionalAccess/namedLocations" `
    -Method POST -Headers $headers -Body $ipLocation

# Named location basata su paese
$countryLocation = @{
    "@odata.type"              = "#microsoft.graph.countryNamedLocation"
    displayName                = "Paesi Autorizzati"
    countriesAndRegions        = @("IT", "US", "DE", "FR", "GB")
    includeUnknownCountriesAndRegions = $false
} | ConvertTo-Json -Depth 4

Invoke-RestMethod -Uri "https://graph.microsoft.com/v1.0/identity/conditionalAccess/namedLocations" `
    -Method POST -Headers $headers -Body $countryLocation
```

### Implementazione Graduale con Report-Only

```powershell
# Creare una CA policy via Graph API in report-only mode
$body = @{
    displayName = "CA001 - Require MFA for All Users"
    state       = "enabledForReportingButNotEnforced"  # Report-only mode
    conditions  = @{
        users = @{
            includeUsers  = @("All")
            excludeGroups = @("grp-breakglass-accounts-id")
        }
        applications = @{
            includeApplications = @("All")
        }
        clientAppTypes = @("browser", "mobileAppsAndDesktopClients")
    }
    grantControls = @{
        operator        = "OR"
        builtInControls = @("mfa")
    }
} | ConvertTo-Json -Depth 5

$headers = @{ Authorization = "Bearer $accessToken"; "Content-Type" = "application/json" }
Invoke-RestMethod -Uri "https://graph.microsoft.com/v1.0/identity/conditionalAccess/policies" `
    -Method POST -Headers $headers -Body $body

# WORKFLOW DI IMPLEMENTAZIONE:
# Settimana 1-2: Policy in Report-Only → analizzare Sign-in logs
# Settimana 3:   Restringere a un gruppo pilota → abilitare enforcement
# Settimana 4:   Espandere gradualmente → monitorare ticket help desk
# Settimana 6:   Enforcement completo → includere "All users"

# Analizzare l'impatto di una policy in Report-Only
# Azure AD → Sign-in logs → Conditional Access tab
# Filtrare per: Report-only: Success / Report-only: Failure
# Le "Failure" indicano utenti che sarebbero stati bloccati
```

---

## Risk-Based Conditional Access — Deep Dive

Identity Protection analizza ogni autenticazione con modelli di machine learning e assegna due tipi distinti di rischio. La distinzione è fondamentale per configurare policy efficaci.

Riferimento: https://learn.microsoft.com/en-us/entra/id-protection/concept-identity-protection-risks (consultato: 2026-05-23)

### User Risk vs Sign-in Risk

```
┌───────────────────────────────────────────────────────────────────────────┐
│                        MODELLO DI RISCHIO                                │
│                                                                          │
│  SIGN-IN RISK                          USER RISK                         │
│  ─────────────                         ─────────                         │
│  Valutato per OGNI tentativo           Valutato sull'IDENTITÀ complessiva│
│  di accesso, in tempo reale.           dell'utente, cumulativo.          │
│                                                                          │
│  Domanda: "Questo specifico           Domanda: "Questo account           │
│  tentativo di login è sospetto?"      è stato compromesso?"              │
│                                                                          │
│  Esempi:                               Esempi:                           │
│  - Login da IP anonimo (Tor)           - Credenziali trovate in un       │
│  - Viaggio atipico (impossibile)         breach database (leaked creds)  │
│  - IP collegato a malware              - Attività anomala persistente    │
│  - Password spray rilevato             - Conferma admin di compromiss.   │
│  - Token anomaly                       - Azure Threat Intelligence       │
│                                                                          │
│  Risposta tipica:                      Risposta tipica:                   │
│  → Richiedere MFA step-up             → Forzare cambio password          │
│  → Bloccare se rischio alto           → Bloccare fino a remediation      │
│                                                                          │
│  Livelli: Low │ Medium │ High         Livelli: Low │ Medium │ High       │
└───────────────────────────────────────────────────────────────────────────┘
```

### Tipi di Rilevamento del Rischio

```
SIGN-IN RISK — Rilevamenti in tempo reale e offline:

┌────────────────────────────────┬──────────┬──────────────────────────────────┐
│ Tipo di Rilevamento            │ Tempo    │ Descrizione                      │
├────────────────────────────────┼──────────┼──────────────────────────────────┤
│ Anonymous IP address           │ Realtime │ Login da IP anonimizzato (Tor,   │
│                                │          │ VPN anonima, proxy aperto)       │
├────────────────────────────────┼──────────┼──────────────────────────────────┤
│ Atypical travel                │ Offline  │ Due login da posizioni           │
│                                │          │ geograficamente distanti in      │
│                                │          │ un tempo fisicamente impossibile │
├────────────────────────────────┼──────────┼──────────────────────────────────┤
│ Malware linked IP              │ Offline  │ IP noto per comunicare con       │
│                                │          │ server C2 di botnet              │
├────────────────────────────────┼──────────┼──────────────────────────────────┤
│ Unfamiliar sign-in properties  │ Realtime │ Combinazione insolita di         │
│                                │          │ dispositivo, browser, ASN, IP    │
├────────────────────────────────┼──────────┼──────────────────────────────────┤
│ Password spray                 │ Offline  │ Stesso pattern di password       │
│                                │          │ testato su molti account         │
├────────────────────────────────┼──────────┼──────────────────────────────────┤
│ Token issuer anomaly           │ Realtime │ Il token SAML è stato emesso     │
│                                │          │ da un issuer sospetto            │
├────────────────────────────────┼──────────┼──────────────────────────────────┤
│ Anomalous token                │ Realtime │ Token con lifetime o claim       │
│                                │          │ anomali (possibile token replay) │
├────────────────────────────────┼──────────┼──────────────────────────────────┤
│ Suspicious browser             │ Offline  │ Browser automation o attività    │
│                                │          │ scripted durante il login        │
├────────────────────────────────┼──────────┼──────────────────────────────────┤
│ Impossible travel              │ Offline  │ Variante più restrittiva di      │
│                                │          │ atypical travel, alta confidenza │
└────────────────────────────────┴──────────┴──────────────────────────────────┘

USER RISK — Rilevamenti cumulativi:

┌────────────────────────────────┬──────────┬──────────────────────────────────┐
│ Leaked credentials             │ Offline  │ Le credenziali dell'utente sono  │
│                                │          │ state trovate in un breach       │
│                                │          │ (richiede PHS abilitato)         │
├────────────────────────────────┼──────────┼──────────────────────────────────┤
│ Azure AD Threat Intelligence   │ Offline  │ Attività coerente con pattern    │
│                                │          │ di attacco noti da Microsoft TI  │
├────────────────────────────────┼──────────┼──────────────────────────────────┤
│ Anomalous user activity        │ Offline  │ Pattern di accesso anomalo       │
│                                │          │ rispetto allo storico utente     │
├────────────────────────────────┼──────────┼──────────────────────────────────┤
│ Possible attempt to access PRT │ Offline  │ Tentativo di accedere al Primary │
│                                │          │ Refresh Token del dispositivo    │
├────────────────────────────────┼──────────┼──────────────────────────────────┤
│ Verified threat actor IP       │ Realtime │ IP associato a threat actor noto │
│                                │          │ confermato da Microsoft MSTIC    │
└────────────────────────────────┴──────────┴──────────────────────────────────┘
```

### Configurazione delle Policy Risk-Based

```
POLICY RACCOMANDATE PER LIVELLO DI RISCHIO:

Sign-in Risk:                              User Risk:
  High   → BLOCCO accesso                   High   → BLOCCO + cambio password
  Medium → MFA + sessione 1h                Medium → Cambio password (dopo MFA)
  Low    → MFA step-up                      Low    → Monitorare, MFA al prossimo

Configurazione: Entra ID → Protection → Identity Protection → Policies

  Sign-in risk policy:
    Users: All users (exclude break-glass)
    Sign-in risk: Medium and above
    Access: Allow — Require MFA | Enforce: On

  User risk policy:
    Users: All users (exclude break-glass)
    User risk: High
    Access: Allow — Require password change | Enforce: On
```

### Workflow di Investigazione del Rischio

```
Quando Identity Protection genera un alert:

1. TRIAGE — Entra ID → Protection → Identity Protection → Risk detections
   Filtrare per livello (High priority), verificare tipo e conteggio utenti

2. INVESTIGAZIONE — Per ogni utente a rischio:
   a) Entra ID → Risky users → cliccare utente → tutti i rilevamenti
      Esaminare: IP, geolocalizzazione, user agent, timestamp
   b) Confrontare con Sign-in log: dispositivo/IP noto? Orario coerente?
   c) Contattare l'utente su canale separato (telefono, Teams, non email)

3. DECISIONE — Tre azioni possibili:
   ┌─────────────────┬───────────────────────────────────────────────────┐
   │ Confirm comprom. │ Forza cambio password, revoca sessioni, IR.     │
   │ Dismiss risk     │ Falso positivo confermato (viaggio, VPN, ecc.). │
   │ Remediate        │ Self-remediation completata (password + MFA).   │
   └─────────────────┴───────────────────────────────────────────────────┘

4. POST-INCIDENT — Documentare nel ticketing, avviare IR se confermato,
   aggiornare policy CA se necessario (es. bloccare range IP)
```

```powershell
# Interrogare utenti a rischio via Microsoft Graph
$headers = @{ Authorization = "Bearer $accessToken"; "Content-Type" = "application/json" }

# Elencare tutti gli utenti a rischio elevato
$riskyUsers = Invoke-RestMethod `
    -Uri "https://graph.microsoft.com/v1.0/identityProtection/riskyUsers?`$filter=riskLevel eq 'high'" `
    -Headers $headers
$riskyUsers.value | Select-Object userDisplayName, userPrincipalName,
    riskLevel, riskState, riskLastUpdatedDateTime

# Dettaglio dei rilevamenti per un utente specifico
$userId = "<user-object-id>"
$detections = Invoke-RestMethod `
    -Uri "https://graph.microsoft.com/v1.0/identityProtection/riskDetections?`$filter=userId eq '$userId'" `
    -Headers $headers
$detections.value | Select-Object riskEventType, riskLevel, riskState,
    detectedDateTime, ipAddress, location, activity

# Elencare sign-in a rischio
$riskySignIns = Invoke-RestMethod `
    -Uri "https://graph.microsoft.com/v1.0/identityProtection/riskyUsers?`$filter=riskState eq 'atRisk'" `
    -Headers $headers

# Confermare la compromissione di un utente (POST)
$body = @{ userIds = @($userId) } | ConvertTo-Json
Invoke-RestMethod `
    -Uri "https://graph.microsoft.com/v1.0/identityProtection/riskyUsers/confirmCompromised" `
    -Method POST -Headers $headers -Body $body

# Dismissare il rischio (falso positivo)
Invoke-RestMethod `
    -Uri "https://graph.microsoft.com/v1.0/identityProtection/riskyUsers/dismiss" `
    -Method POST -Headers $headers -Body $body

# Report mensile: conteggio rilevamenti per tipo
$allDetections = Invoke-RestMethod `
    -Uri "https://graph.microsoft.com/v1.0/identityProtection/riskDetections?`$filter=detectedDateTime ge $(
        (Get-Date).AddDays(-30).ToString('yyyy-MM-ddT00:00:00Z'))" `
    -Headers $headers
$allDetections.value | Group-Object riskEventType |
    Select-Object Name, Count | Sort-Object Count -Descending
```

---

## MFA Backup e Procedura di Emergenza

Questa sezione documenta la gerarchia dei metodi di autenticazione di backup, la configurazione del Temporary Access Pass (TAP) e la procedura operativa per lo scenario critico in cui un utente perde tutti i metodi MFA.

### Gerarchia dei Metodi di Backup MFA

Riferimento: https://learn.microsoft.com/en-us/entra/identity/authentication/concept-authentication-methods (consultato: 2026-05-23)

```
METODI MFA — Ordinati per sicurezza e resistenza al phishing:

┌───┬──────────────────────────────┬──────────────┬───────────────────────────┐
│ # │ Metodo                       │ Phishing-    │ Scenario di Backup        │
│   │                              │ Resistant    │                           │
├───┼──────────────────────────────┼──────────────┼───────────────────────────┤
│ 1 │ FIDO2 Security Key           │ SÌ           │ Chiave primaria +         │
│   │ (hardware, es. YubiKey)      │              │ chiave secondaria in safe │
├───┼──────────────────────────────┼──────────────┼───────────────────────────┤
│ 2 │ Windows Hello for Business   │ SÌ           │ Biometrico + PIN,         │
│   │ (biometria + TPM)            │              │ legato al dispositivo     │
├───┼──────────────────────────────┼──────────────┼───────────────────────────┤
│ 3 │ Microsoft Authenticator      │ Parziale     │ Installare su 2           │
│   │ (push + number matching)     │ (numberMatch)│ dispositivi (phone + tab) │
├───┼──────────────────────────────┼──────────────┼───────────────────────────┤
│ 4 │ Authenticator OATH TOTP      │ No           │ Salvare i seed codes in   │
│   │ (software token)             │              │ password manager offline  │
├───┼──────────────────────────────┼──────────────┼───────────────────────────┤
│ 5 │ OATH hardware token          │ No           │ Token fisico di backup    │
│   │                              │              │ in cassaforte             │
├───┼──────────────────────────────┼──────────────┼───────────────────────────┤
│ 6 │ SMS / Voice call             │ No           │ Solo come ultimo fallback │
│   │ (NON raccomandato come       │              │ — vulnerabile a SIM swap  │
│   │ metodo primario)             │              │                           │
└───┴──────────────────────────────┴──────────────┴───────────────────────────┘

RACCOMANDAZIONE: ogni utente ALMENO 2 metodi MFA; privilegiati ALMENO 3 (1 phishing-resistant).
```

### Temporary Access Pass (TAP)

Il TAP è un codice temporaneo a uso limitato che un amministratore può emettere per consentire a un utente di accedere senza MFA, tipicamente per registrare nuovi metodi di autenticazione o recuperare l'accesso.

Riferimento: https://learn.microsoft.com/en-us/entra/identity/authentication/howto-authentication-temporary-access-pass (consultato: 2026-05-23)

```
Configurazione TAP Policy:
Entra ID → Protection → Authentication methods → Policies → Temporary Access Pass

  - Enabled: Yes
  - Target: All users (o gruppo specifico)
  - Minimum lifetime: 10 minutes (default: 1 hour)
  - Maximum lifetime: 8 hours (massimo configurabile: 30 giorni)
  - Default lifetime: 1 hour
  - One-time use: Yes (raccomandato per sicurezza)
  - Length: 8-48 characters (default: 8)

Proprietà del TAP:
  - Soddisfa il requisito MFA (conta come "something you have")
  - Funziona con Conditional Access (soddisfa "Require MFA")
  - Configurabile come one-time o multi-use; scadenza temporale
  - NON può essere usato per cambiare la password
  - Tracciato nel sign-in log come "Temporary Access Pass"
```

```powershell
# Emettere un TAP per un utente via Microsoft Graph
$headers = @{ Authorization = "Bearer $accessToken"; "Content-Type" = "application/json" }

$tapBody = @{
    isUsableOnce   = $true      # Uso singolo (raccomandato)
    lifetimeInMinutes = 60      # Validità: 1 ora
} | ConvertTo-Json

$userId = "<user-object-id>"
$tap = Invoke-RestMethod `
    -Uri "https://graph.microsoft.com/v1.0/users/$userId/authentication/temporaryAccessPassMethods" `
    -Method POST -Headers $headers -Body $tapBody

Write-Output "TAP emesso per l'utente:"
Write-Output "Codice: $($tap.temporaryAccessPass)"
Write-Output "Scadenza: $($tap.lifetimeInMinutes) minuti"
Write-Output "Uso singolo: $($tap.isUsableOnce)"
Write-Output "Valido da: $($tap.startDateTime)"

# IMPORTANTE: comunicare il TAP su un canale sicuro (telefono, di persona)
# NON via email — il TAP è equivalente a una password temporanea + MFA

# Verificare i TAP attivi per un utente
$activeTaps = Invoke-RestMethod `
    -Uri "https://graph.microsoft.com/v1.0/users/$userId/authentication/temporaryAccessPassMethods" `
    -Headers $headers
$activeTaps.value | Select-Object id, isUsableOnce, lifetimeInMinutes,
    startDateTime, isUsable

# Revocare un TAP specifico
$tapId = $activeTaps.value[0].id
Invoke-RestMethod `
    -Uri "https://graph.microsoft.com/v1.0/users/$userId/authentication/temporaryAccessPassMethods/$tapId" `
    -Method DELETE -Headers $headers
```

### Procedura di Emergenza: "All MFA Lost"

Questa procedura si applica quando un utente ha perso accesso a TUTTI i metodi MFA registrati (telefono smarrito/rubato, FIDO2 key perduta, cambio dispositivo senza migrazione Authenticator). L'utente non può autenticarsi in alcun modo.

```
╔══════════════════════════════════════════════════════════════════════════╗
║           RUNBOOK: RECUPERO COMPLETO MFA — "ALL MFA LOST"              ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  FASE 1: VERIFICA IDENTITÀ (fuori banda — NON via email/Teams)         ║
║  a) L'utente contatta l'help desk via TELEFONO o DI PERSONA            ║
║  b) Operatore verifica identità con almeno 2 di:                       ║
║     - Badge aziendale (di persona)                                     ║
║     - Matricola + data di nascita                                      ║
║     - Domanda di sicurezza HR (ultimo stipendio, data assunzione)      ║
║     - Conferma dal manager diretto (telefonata separata)               ║
║  c) Utenti privilegiati: verifica obbligatoria da CISO + manager       ║
║  d) Documentare: ID operatore, metodo verifica, timestamp ISO 8601     ║
║                                                                        ║
║  FASE 2: RESET DEI METODI MFA (admin)                                  ║
║  a) Entra ID → Users → [utente] → Authentication methods              ║
║     → Require re-register multifactor authentication                  ║
║  b) Eliminare TUTTI i metodi registrati: telefono, Authenticator,      ║
║     FIDO2 keys, Windows Hello for Business                             ║
║  c) Revocare TUTTE le sessioni attive:                                 ║
║     Entra ID → Users → [utente] → Revoke sessions                    ║
║                                                                        ║
║  FASE 3: EMISSIONE TAP (admin)                                         ║
║  a) Emettere TAP one-time, lifetime 60 minuti                          ║
║  b) Comunicare SOLO via canale verificato (di persona o telefono)      ║
║  c) MAI via email, MAI via chat non verificata                         ║
║                                                                        ║
║  FASE 4: RE-ENROLLMENT MFA (utente)                                    ║
║  a) Accedere a https://aka.ms/mysecurityinfo con il TAP                ║
║  b) Registrare ALMENO 2 metodi MFA (Authenticator + secondario)        ║
║  c) Utenti privilegiati: ALMENO 3 metodi, incluso 1 FIDO2 key         ║
║  d) Testare ogni metodo registrato                                     ║
║                                                                        ║
║  FASE 5: VERIFICA E CHIUSURA (admin)                                   ║
║  a) Verificare nel portale che i nuovi metodi MFA sono attivi          ║
║  b) Verificare nel sign-in log l'accesso con i nuovi metodi           ║
║  c) Revocare il TAP se non già scaduto                                 ║
║  d) Chiudere il ticket: metodi registrati, timestamp, esito            ║
║  e) Se utente privilegiato: notificare Security team                   ║
║                                                                        ║
╚══════════════════════════════════════════════════════════════════════════╝
```

```powershell
# Script admin per la procedura All MFA Lost
# Eseguire come Authentication Administrator o Privileged Authentication Administrator

param(
    [Parameter(Mandatory)] [string]$UserUPN,
    [string]$TicketNumber = "N/A"
)

$userId = (Get-MgUser -UserId $UserUPN).Id
Write-Output "=== PROCEDURA ALL MFA LOST ==="
Write-Output "Utente: $UserUPN"
Write-Output "Ticket: $TicketNumber"
Write-Output "Timestamp: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ' -AsUtc)"

# Step 1: Elencare i metodi MFA attuali (prima di rimuoverli)
Write-Output "`n--- Metodi MFA attuali (pre-reset) ---"
$methods = Get-MgUserAuthenticationMethod -UserId $userId
$methods | Select-Object AdditionalProperties | ForEach-Object {
    Write-Output $_.AdditionalProperties
}

# Step 2: Revocare tutte le sessioni
Write-Output "`n--- Revoca sessioni ---"
Revoke-MgUserSignInSession -UserId $userId
Write-Output "Sessioni revocate."

# Step 3: Richiedere re-registrazione MFA
# (Tramite portale: Users → Authentication methods → Require re-register)
# Via Graph: non c'è un singolo endpoint — si rimuovono i metodi singolarmente

# Step 4: Emettere TAP
Write-Output "`n--- Emissione Temporary Access Pass ---"
$tapParams = @{
    IsUsableOnce      = $true
    LifetimeInMinutes = 60
}
$tap = New-MgUserAuthenticationTemporaryAccessPassMethod -UserId $userId `
    -BodyParameter $tapParams

Write-Output "TAP generato:"
Write-Output "Codice: $($tap.TemporaryAccessPass)"
Write-Output "Scadenza: $($tap.LifetimeInMinutes) minuti"
Write-Output "Monouso: $($tap.IsUsableOnce)"
Write-Output ""
Write-Output ">>> COMUNICARE IL TAP ALL'UTENTE SOLO VIA CANALE VERIFICATO <<<"
Write-Output ">>> L'utente deve accedere a https://aka.ms/mysecurityinfo <<<"
```

### Recupero FIDO2 Key Smarrita

```
Procedura per chiave FIDO2 persa o danneggiata:

1. L'utente accede con un metodo MFA alternativo (Authenticator, SMS)
   - Se nessun altro metodo disponibile → procedura "All MFA Lost"

2. L'utente accede a https://aka.ms/mysecurityinfo
   - Rimuove la FIDO2 key smarrita dalla lista dei metodi
   - Registra la FIDO2 key sostitutiva

3. L'admin conferma nel portale:
   - Entra ID → Users → [utente] → Authentication methods
   - Verificare che la vecchia key è rimossa e la nuova registrata

4. Se la FIDO2 key persa era l'UNICA chiave di un utente privilegiato:
   - Trattare come potenziale compromissione — revocare tutte le sessioni
   - Monitorare sign-in log per accessi sospetti con la vecchia key

Best practice preventiva:
- Ogni utente con FIDO2: ALMENO 2 chiavi registrate
- Chiave secondaria in cassaforte; per privilegiati, in cassaforte aziendale
```

---

## Privileged Identity Management (PIM)

PIM fornisce accesso just-in-time ai ruoli privilegiati in Azure AD e Azure. Invece di assegnare ruoli permanentemente, gli utenti devono "attivare" il ruolo quando ne hanno bisogno, con giustificazione, approvazione opzionale e durata limitata.

### Concetti Fondamentali

**Eligible Assignment:** L'utente è idoneo per un ruolo ma non lo ha attivo. Deve richiedere l'attivazione. Non ha alcun privilegio finché non attiva.

**Active Assignment:** L'utente ha il ruolo attivo (permanente o temporaneo dopo l'attivazione). Ha tutti i privilegi del ruolo.

**Activation:** Il processo di passaggio da Eligible ad Active, che può richiedere:
- MFA (sempre raccomandato)
- Giustificazione testuale
- Approvazione da parte di un reviewer
- Ticket number (per tracciabilità)
- Durata limitata (1-24 ore)

### Flusso PIM

```
Flusso PIM:
1. Admin configura: "Mario Rossi è Eligible per Global Administrator"
2. Mario ha bisogno di fare un'operazione privilegiata
3. Mario va in PIM → Attiva il ruolo "Global Administrator"
4. Mario inserisce la giustificazione: "Ticket INC-1234: modifica DNS tenant"
5. PIM richiede MFA (Authenticator / FIDO2)
6. (Opzionale) L'approvatore riceve notifica email/Teams e approva
7. Mario ha il ruolo attivo per 1-8 ore (configurabile)
8. Mario esegue l'operazione privilegiata
9. Dopo la scadenza, il ruolo torna a Eligible automaticamente
10. L'evento è registrato nell'audit log con tutti i dettagli:
    - Chi ha attivato
    - Quale ruolo
    - Quando (inizio/fine)
    - Giustificazione fornita
    - Chi ha approvato (se applicabile)
    - IP di attivazione
```

### Configurazione Dettagliata

```
Azure AD → Identity Governance → Privileged Identity Management → Azure AD roles

Configurare ruolo "Global Administrator":

  Role settings → Edit:

    Activation tab:
      - Activation maximum duration: 2 hours (non più di 4h per Global Admin)
      - Require MFA on activation: Yes (SEMPRE per ruoli critici)
      - Require justification: Yes
      - Require approval: Yes (per Global Admin, Privileged Role Admin)
      - Approvers: Security team group
      - Require ticket information: Yes (link al change management)
      - Require Azure MFA (not on-prem MFA): Yes

    Assignment tab:
      - Allow permanent eligible assignment: No
      - Expire eligible assignment after: 180 days (forza rinnovo periodico)
      - Allow permanent active assignment: No (MAI per ruoli critici)
      - Expire active assignment after: max 2 hours
      - Require MFA on active assignment: Yes
      - Require justification on active assignment: Yes

    Notification tab:
      - Send email when members are assigned as eligible: Yes → Security team
      - Send email when members are assigned as active: Yes → Security team + CISO
      - Send email when eligible members activate: Yes → Security team
      - Send email on role activation approval request: Yes → Approvers
```

### Ruoli da Proteggere con PIM

| Ruolo | Rischio | Durata Max | Approvazione | MFA |
|-------|---------|------------|-------------|-----|
| Global Administrator | Critico | 1h | Sì | Sì |
| Privileged Role Administrator | Critico | 1h | Sì | Sì |
| Security Administrator | Critico | 2h | Sì | Sì |
| Conditional Access Administrator | Alto | 2h | Sì | Sì |
| Exchange Administrator | Alto | 2h | Opzionale | Sì |
| SharePoint Administrator | Alto | 2h | Opzionale | Sì |
| User Administrator | Medio | 4h | No | Sì |
| Application Administrator | Medio | 4h | No | Sì |
| Intune Administrator | Medio | 4h | No | Sì |
| Groups Administrator | Basso | 8h | No | Sì |
| Helpdesk Administrator | Basso | 8h | No | Sì |

### PIM per Azure Resources

PIM non si limita ai ruoli Azure AD — copre anche i ruoli Azure RBAC per subscription, resource groups e risorse specifiche.

```powershell
# Configurare PIM per un ruolo Azure RBAC via Graph API
# Esempio: Owner su una subscription

$roleAssignment = @{
    properties = @{
        roleDefinitionId = "/subscriptions/<sub-id>/providers/Microsoft.Authorization/roleDefinitions/8e3af657-a8ff-443c-a75c-2fe8c4bcb635"  # Owner
        principalId      = "<user-object-id>"
        requestType      = "AdminAssign"
        scheduleInfo     = @{
            startDateTime = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
            expiration    = @{
                type     = "AfterDuration"
                duration = "P180D"  # 180 giorni eligible
            }
        }
    }
} | ConvertTo-Json -Depth 6

# Assegnare come Eligible
Invoke-RestMethod -Uri "https://management.azure.com/subscriptions/<sub-id>/providers/Microsoft.Authorization/roleEligibilityScheduleRequests/<guid>?api-version=2022-04-01" `
    -Method PUT -Headers $headers -Body $roleAssignment
```

---

## Access Reviews

Le Access Reviews automatizzano la verifica periodica degli accessi, assicurando che utenti e gruppi mantengano solo le autorizzazioni necessarie (principio del minimo privilegio).

### Configurazione

```
Azure AD → Identity Governance → Access Reviews → New access review

Configurazione:
  Review name: "Revisione trimestrale - Global Admins"
  Frequency: Quarterly
  Duration: 14 days
  End: After 4 occurrences (1 anno)

  Scope:
    - Review type: Azure AD roles
    - Role: Global Administrator
    - Scope: All users with eligible or active assignments

  Reviewers:
    - Self-review: No (gli admin non devono approvare il proprio accesso)
    - Specific reviewers: CISO, Security Manager
    - Fallback reviewers: IT Director

  Settings:
    - Auto apply results: Yes
    - If reviewer doesn't respond: Remove access
    - Action to apply on denied: Remove active/eligible assignment
    - Additional notifications: Remind reviewers 3 days before end
    - Justification required: Yes

  Advanced settings:
    - Show recommendations to reviewers: Yes (basate su ultimo sign-in)
    - Require reason for approval: Yes
```

### Access Reviews per Gruppi e Applicazioni

```
Scenari tipici per Access Reviews:

1. Revisione gruppi di sicurezza con accesso a dati sensibili
   - Frequency: Mensile
   - Reviewer: Owner del gruppo
   - Auto-remove se non approvato

2. Revisione accesso ad applicazioni enterprise
   - Frequency: Trimestrale
   - Reviewer: Application owner
   - Raccomandazioni basate su ultimo utilizzo

3. Revisione guest users (B2B)
   - Frequency: Mensile
   - Reviewer: Sponsor dell'ospite
   - Auto-remove se guest non ha acceduto in 90 giorni

4. Revisione PIM role assignments
   - Frequency: Trimestrale
   - Reviewer: Security team
   - Se non approvato: rimuovi eligible assignment
```

```powershell
# Creare un Access Review via Graph API
$accessReview = @{
    displayName   = "Q1 2026 - Global Admin Review"
    descriptionForAdmins = "Revisione trimestrale degli assegnamenti Global Admin"
    descriptionForReviewers = "Verificare che ogni utente necessiti ancora del ruolo Global Administrator"
    scope         = @{
        query     = "/roleManagement/directory/roleAssignmentScheduleInstances?`$filter=roleDefinition/id eq '62e90394-69f5-4237-9190-012177145e10'"  # Global Admin role
        queryType = "MicrosoftGraph"
    }
    reviewers     = @(
        @{
            query     = "/users/<ciso-object-id>"
            queryType = "MicrosoftGraph"
        }
    )
    settings      = @{
        mailNotificationsEnabled       = $true
        reminderNotificationsEnabled   = $true
        justificationRequiredOnApproval = $true
        autoApplyDecisionsEnabled      = $true
        defaultDecision                = "Deny"
        defaultDecisionEnabled         = $true
        instanceDurationInDays         = 14
        recurrence                     = @{
            pattern = @{ type = "absoluteMonthly"; interval = 3 }
            range   = @{ type = "numbered"; numberOfOccurrences = 4; startDate = "2026-01-01" }
        }
        recommendationsEnabled         = $true
        recommendationLookBackDuration = "P30D"
    }
} | ConvertTo-Json -Depth 8

Invoke-RestMethod -Uri "https://graph.microsoft.com/v1.0/identityGovernance/accessReviews/definitions" `
    -Method POST -Headers $headers -Body $accessReview
```

---

## Entitlement Management

L'Entitlement Management è il sistema di governance degli accessi che gestisce il ciclo di vita completo dell'accesso alle risorse: dalla richiesta, all'approvazione, al provisioning, fino alla scadenza automatica.

### Concetti Chiave

```
Terminologia Entitlement Management:

Access Package:
  Un bundle di risorse (gruppi, app, siti SharePoint, ruoli Azure AD)
  che possono essere richieste come un'unica unità.
  Esempio: "Onboarding Marketing" include:
  - Gruppo "Marketing-All"
  - Applicazione "Marketing Dashboard"
  - Sito SharePoint "Marketing Resources"
  - Ruolo Azure AD "Reports Reader"

Catalog:
  Un container logico che raggruppa access packages correlati.
  Esempio: catalogo "Marketing" contiene tutti gli access package
  per il dipartimento Marketing.

Policy:
  Le regole che governano chi può richiedere un access package,
  chi lo approva, e quando scade.
  Un access package può avere più policy (es. una per interni,
  una per guest, una per auto-assignment).

Connected Organization:
  Un'organizzazione esterna (partner, fornitore) i cui utenti
  possono richiedere access package tramite B2B.

Assignment:
  L'accesso effettivo di un utente a un access package.
  Ha una data di inizio, una data di scadenza, e uno stato.
```

### Architettura

```
┌──────────────────────────────────────────────────────────────┐
│                    Entitlement Management                     │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Catalog:     │  │ Catalog:     │  │ Catalog:             │  │
│  │ "Marketing"  │  │ "IT"         │  │ "External Partners" │  │
│  │              │  │              │  │                       │  │
│  │ ┌─────────┐ │  │ ┌─────────┐ │  │ ┌─────────────────┐ │  │
│  │ │ Access  │ │  │ │ Access  │ │  │ │ Access Package: │ │  │
│  │ │ Package:│ │  │ │ Package:│ │  │ │ "Partner Portal │ │  │
│  │ │ "Mktg   │ │  │ │ "Dev    │ │  │ │  Access"        │ │  │
│  │ │ Onboard"│ │  │ │ Onboard"│ │  │ └─────────────────┘ │  │
│  │ └─────────┘ │  │ └─────────┘ │  │                       │  │
│  │              │  │              │  │ Policy: Connected    │  │
│  │ Policy:      │  │ Policy:      │  │ Org auto-approve     │  │
│  │ Manager      │  │ IT Manager   │  │ Expiry: 90 days      │  │
│  │ approval     │  │ approval     │  │                       │  │
│  │ Expiry: 365d │  │ Expiry: 365d │  │                       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Configurazione di un Access Package

```
Azure AD → Identity Governance → Entitlement Management → Catalogs

1. Creare un Catalog:
   Name: "Dipartimento Marketing"
   Description: "Risorse per il team Marketing"
   Enabled: Yes
   Enabled for external users: No (o Sì per partner)

2. Aggiungere risorse al Catalog:
   - Groups and Teams:
     - GRP-Marketing-All
     - GRP-Marketing-Managers
     - Team-Marketing (Microsoft Teams)
   - Applications:
     - Marketing Dashboard (Enterprise App)
     - Adobe Creative Cloud (Enterprise App)
   - SharePoint sites:
     - Marketing Resources

3. Creare un Access Package:
   Name: "Marketing - Onboarding Nuovo Dipendente"
   Description: "Accesso standard per nuovi dipendenti Marketing"
   Catalog: Dipartimento Marketing

   Resource roles:
   - GRP-Marketing-All → Member
   - Marketing Dashboard → User
   - Marketing Resources → Member

4. Creare Policy per l'Access Package:
   Name: "Policy per dipendenti interni"
   Users who can request:
     - For users in your directory
     - Specific users and groups: All employees
   
   Approval:
     - Require approval: Yes
     - First approver: Manager dell'utente
     - Second approver: Marketing Director (fallback)
     - Escalation: Auto-approve after 3 days if no response
   
   Lifecycle:
     - Expiration: 365 days from date approved
     - Access review: Every 180 days
     - Reviewer: Manager dell'utente
     - If reviewer doesn't respond: Remove access
```

```powershell
# Creare un access package via Graph API
$catalog = @{
    displayName = "Dipartimento Marketing"
    description = "Risorse per il team Marketing"
    isExternallyVisible = $false
} | ConvertTo-Json

$newCatalog = Invoke-RestMethod `
    -Uri "https://graph.microsoft.com/v1.0/identityGovernance/entitlementManagement/catalogs" `
    -Method POST -Headers $headers -Body $catalog

# Aggiungere una risorsa (gruppo) al catalogo
$resource = @{
    catalogId = $newCatalog.id
    requestType = "AdminAdd"
    accessPackageResource = @{
        displayName = "GRP-Marketing-All"
        resourceType = "AadGroup"
        originId = "<group-object-id>"
        originSystem = "AadGroup"
    }
} | ConvertTo-Json -Depth 4

Invoke-RestMethod `
    -Uri "https://graph.microsoft.com/v1.0/identityGovernance/entitlementManagement/resourceRequests" `
    -Method POST -Headers $headers -Body $resource

# Creare l'access package
$accessPackage = @{
    displayName = "Marketing - Onboarding"
    description = "Accesso standard per nuovi dipendenti Marketing"
    catalog     = @{ id = $newCatalog.id }
} | ConvertTo-Json -Depth 3

$newPackage = Invoke-RestMethod `
    -Uri "https://graph.microsoft.com/v1.0/identityGovernance/entitlementManagement/accessPackages" `
    -Method POST -Headers $headers -Body $accessPackage
```

### Scenari Avanzati di Entitlement Management

```
Scenario 1: Auto-Assignment basato su attributi
  - Quando department = "Marketing" → assegna automaticamente access package
  - Non richiede approvazione
  - Si rimuove automaticamente quando l'utente cambia dipartimento

Scenario 2: Separation of Duties (SoD)
  - L'access package "Finance Approver" è incompatibile con "Finance Requester"
  - Se un utente ha già uno dei due, non può richiedere l'altro
  - Previene conflitti di interesse (chi approva spese ≠ chi le richiede)

Scenario 3: Connected Organizations (B2B)
  - Partner esterni possono richiedere accesso al portale partner
  - Richiedono approvazione dello sponsor interno
  - L'accesso scade dopo 90 giorni
  - Access review automatico ogni 30 giorni
  - Se il partner non accede per 30 giorni → rimozione automatica

Scenario 4: Lifecycle Automation con Logic Apps
  - Trigger: utente assegnato a access package
  - Azione: crea ticket in ServiceNow, notifica Teams, provisiona risorse aggiuntive
  - Trigger: access package scaduto
  - Azione: chiudi ticket ServiceNow, archivia risorse, notifica manager
```

---

## Monitoraggio e Salute della Sincronizzazione

```powershell
# Azure AD Connect Health
# Richiede Azure AD Premium P1 o P2
# Installa un agente di monitoring sul server Azure AD Connect

# Monitorare localmente con PowerShell
Get-ADSyncScheduler | Format-List

# Verificare errori di sincronizzazione
Get-ADSyncConnectorRunStatus | Where-Object { $_.Result -ne "success" }

# Report degli errori per oggetto
Get-ADSyncCSObject -ConnectorName "contoso.com" -ObjectType user |
    Where-Object { $_.HasSyncError } |
    Select-Object DistinguishedName, ErrorMessage

# Monitorare il delta sync
$lastRun = Get-ADSyncRunProfileResult -ConnectorName "contoso.com" -NumberRequested 1
$lastRun | Select-Object RunNumber, StartDate, EndDate, Result,
    CountExportAdd, CountExportUpdate, CountExportDelete,
    CountImportAdd, CountImportUpdate, CountImportDelete |
    Format-List

# Script di monitoring automatico
$syncStatus = Get-ADSyncScheduler
$lastSync = (Get-ADSyncRunProfileResult -NumberRequested 1).EndDate

if ((New-TimeSpan -Start $lastSync -End (Get-Date)).TotalMinutes -gt 60) {
    Write-Warning "ALERT: Ultima sincronizzazione più vecchia di 60 minuti!"
    # Inviare alert via email o webhook
}

if (-not $syncStatus.SyncCycleEnabled) {
    Write-Error "CRITICAL: Il sync scheduler è disabilitato!"
}

# Script di monitoring completo
function Get-AADCSyncHealthReport {
    $report = @{
        Timestamp       = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        SchedulerStatus = (Get-ADSyncScheduler).SyncCycleEnabled
        Issues          = @()
    }

    # Controllare la latenza del sync
    $lastRun = Get-ADSyncRunProfileResult -NumberRequested 1
    $latencyMinutes = ((Get-Date) - $lastRun.EndDate).TotalMinutes
    if ($latencyMinutes -gt 60) {
        $report.Issues += "Sync latency: $([math]::Round($latencyMinutes,1)) minuti"
    }

    # Controllare errori di export
    $exportErrors = Get-ADSyncCSObject -ConnectorName "contoso.com - AAD" |
        Where-Object HasExportError | Measure-Object
    if ($exportErrors.Count -gt 0) {
        $report.Issues += "Export errors: $($exportErrors.Count)"
    }

    # Controllare errori di import
    $importErrors = Get-ADSyncCSObject -ConnectorName "contoso.com" |
        Where-Object HasSyncError | Measure-Object
    if ($importErrors.Count -gt 0) {
        $report.Issues += "Import/Sync errors: $($importErrors.Count)"
    }

    # Controllare spazio disco
    $drive = Get-PSDrive C
    $freeGB = [math]::Round($drive.Free / 1GB, 2)
    if ($freeGB -lt 10) {
        $report.Issues += "Low disk space: ${freeGB}GB free"
    }

    # Controllare la Kerberos key rotation (Seamless SSO)
    try {
        $ssoAccount = Get-ADComputer "AZUREADSSOACC" -Properties PasswordLastSet
        $daysSinceRotation = ((Get-Date) - $ssoAccount.PasswordLastSet).Days
        if ($daysSinceRotation -gt 25) {
            $report.Issues += "SSO Kerberos key: $daysSinceRotation days since rotation (limit: 30)"
        }
    } catch {
        # AZUREADSSOACC non esiste se SSO non è abilitato
    }

    if ($report.Issues.Count -eq 0) {
        $report.Status = "HEALTHY"
    } else {
        $report.Status = "DEGRADED"
    }

    return $report
}

# Eseguire il report
$healthReport = Get-AADCSyncHealthReport
$healthReport | ConvertTo-Json -Depth 3
```

### Azure AD Connect Health — Monitoraggio Centralizzato

Azure AD Connect Health fornisce monitoraggio proattivo dell'infrastruttura di identità ibrida direttamente dal portale Entra ID, con alert email, dashboard degli errori di sync e metriche di performance.

Riferimento: https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/how-to-connect-health-operations (consultato: 2026-05-23)

```
Tipi di Agente Health:

┌───────────────────────────────┬───────────────────────────────────────────┐
│ Agente                        │ Dove installarlo e cosa monitora          │
├───────────────────────────────┼───────────────────────────────────────────┤
│ Health Agent for Sync         │ Sul server Azure AD Connect.              │
│                               │ Monitora: stato sync, latenza,            │
│                               │ errori di import/export, oggetti in       │
│                               │ conflitto, connettività verso Azure AD.  │
├───────────────────────────────┼───────────────────────────────────────────┤
│ Health Agent for AD FS        │ Su ogni server AD FS e WAP.              │
│                               │ Monitora: latenza token, certificati in  │
│                               │ scadenza, extranet lockout, richieste/s, │
│                               │ disponibilità endpoint.                  │
├───────────────────────────────┼───────────────────────────────────────────┤
│ Health Agent for AD DS        │ Su ogni Domain Controller.               │
│                               │ Monitora: replica AD, DNS, LDAP bind     │
│                               │ performance, NTDS.dit size, Kerberos     │
│                               │ authentication failures.                 │
└───────────────────────────────┴───────────────────────────────────────────┘

Categorie di Alert:

  CRITICAL: Sync non funzionante da >2 ore, certificato AD FS scaduto,
            agente Health offline, replica AD fallita
  WARNING:  Latenza sync >60 min, certificato in scadenza (<30 giorni),
            errori di export >10 oggetti, extranet lockout elevato
  INFO:     Aggiornamento agente disponibile, cambio configurazione
            rilevato, rotazione chiave SSO necessaria

Dashboard errori di sync (nel portale):
  Entra ID → Connect Health → Sync errors
  - Raggruppa errori per tipo (InvalidSoftMatch, DataValidation, ecc.)
  - Mostra il conteggio di oggetti per ogni tipo di errore
  - Fornisce raccomandazioni per la risoluzione
  - Permette il drill-down fino all'oggetto specifico in errore

Notifiche email:
  - Configurabili per ruolo (Global Admin, Identity Admin)
  - Digest settimanale o alert in tempo reale
  - Personalizzabili per severity (solo Critical, oppure Warning+)
```

```powershell
# Installare Health Agent for Sync (sul server Azure AD Connect)
# L'agent for Sync è incluso in Azure AD Connect 2.x — verificare:
Get-Service "AzureADConnectHealthSyncInsights" | Select-Object Status, StartType

# Installare Health Agent for AD DS (su ogni DC)
# Scaricare: https://aka.ms/aaboragent
# Eseguire MicrosoftAzureADConnectHealthADDSAgentSetup.exe su ogni DC

# Verificare la connettività dell'agente Health
Test-AzureADConnectHealthConnectivity -Role Sync
# Role validi: Sync, ADFS, ADDS

# Verificare la registrazione dell'agente
Get-AzureADConnectHealthServiceConfiguration | Select-Object TenantId, ServiceInstance
```

### Staging Server (Disaster Recovery)

```powershell
# Configurare un server Azure AD Connect in Staging Mode
# Il server in staging esegue import e sync ma NON export
# Può essere promosso ad attivo in caso di failure del server principale

# Verificare se il server è in staging mode
Get-ADSyncGlobalSettings | Select-Object -ExpandProperty Parameters |
    Where-Object Name -eq "Microsoft.Synchronize.StagingModeEnabled"

# Promuovere il staging server ad attivo
# 1. Verificare che il server principale sia spento o disconnesso
# 2. Sul staging server: Azure AD Connect wizard
#    → Configure staging mode → Deselezionare "Enable staging mode"
# 3. Il server inizierà ad esportare le modifiche

# ATTENZIONE: MAI avere due server attivi (non-staging) contemporaneamente
# verso lo stesso tenant. Questo causa duplicazioni e corruzione dei dati.

# Script per monitoring del staging server
$stagingStatus = Get-ADSyncGlobalSettings | Select-Object -ExpandProperty Parameters |
    Where-Object Name -eq "Microsoft.Synchronize.StagingModeEnabled"
$isStaging = $stagingStatus.Value

if ($isStaging -eq "True") {
    Write-Output "Server in STAGING mode - solo import/sync, NO export"
    # Verificare che stia sincronizzando
    $lastRun = Get-ADSyncRunProfileResult -NumberRequested 1
    if ($lastRun.Result -eq "success") {
        Write-Output "Ultimo sync riuscito: $($lastRun.EndDate)"
    } else {
        Write-Warning "ALERT: Ultimo sync fallito: $($lastRun.Result)"
    }
}
```

#### Casi d'Uso dello Staging Mode

```
Oltre al disaster recovery, lo staging server è utile per:

1. TEST DI SYNC RULES
   - Creare/modificare sync rules sullo staging server
   - Eseguire Full Sync e verificare i risultati nel metaverse
   - Se il risultato è corretto → applicare le stesse regole sul server attivo
   - Se il risultato è sbagliato → rollback senza impatto in produzione

2. VALIDAZIONE PRE-UPGRADE
   - Aggiornare Azure AD Connect sullo staging server
   - Verificare che il sync funzioni con la nuova versione
   - Se OK → aggiornare il server attivo
   - Se problemi → mantenere la versione precedente sul server attivo

3. VERIFICA CONSISTENZA DATI
   - Confrontare i connector space tra staging e active
   - Identificare divergenze nella configurazione
   - Usare come baseline per audit di sync
```

#### Procedura di Failover: Staging → Active

```powershell
# PROCEDURA COMPLETA DI FAILOVER

# Step 1: Verificare che il server principale sia effettivamente irraggiungibile
Test-NetConnection -ComputerName "AADCONNECT-PRIMARY" -Port 443

# Step 2: Verificare la configurazione del staging server PRIMA del failover
$stagingParams = Get-ADSyncGlobalSettings | Select-Object -ExpandProperty Parameters
$stagingParams | Where-Object Name -in @(
    "Microsoft.Synchronize.StagingModeEnabled",
    "Microsoft.Synchronize.ServerConfigurationVersion",
    "Microsoft.OptionalFeature.AnchorAttribute"
) | Select-Object Name, Value

# Step 3: Verificare che l'ultimo sync sullo staging sia recente e riuscito
Get-ADSyncRunProfileResult -NumberRequested 5 |
    Select-Object RunNumber, StartDate, EndDate, Result, StepResult

# Step 4: Confrontare il numero di oggetti (deve essere coerente con il server attivo)
Get-ADSyncConnectorStatistics -ConnectorName "contoso.com" |
    Select-Object TotalConnectors, TotalDisconnectors

# Step 5: PROMUOVERE — Disabilitare staging mode
# Azure AD Connect wizard → Configure staging mode → DESELEZIONARE "Enable staging mode"
# → Finish → Il server inizia ad esportare

# Step 6: Verificare dopo la promozione
$newParams = Get-ADSyncGlobalSettings | Select-Object -ExpandProperty Parameters
$newParams | Where-Object Name -eq "Microsoft.Synchronize.StagingModeEnabled"
# Value deve essere False

# Step 7: Forzare un delta sync e verificare che le export funzionino
Start-ADSyncSyncCycle -PolicyType Delta
Start-Sleep -Seconds 120
Get-ADSyncRunProfileResult -NumberRequested 1 |
    Select-Object Result, CountExportAdd, CountExportUpdate
```

---

## Password Protection e Self-Service Password Reset

### Azure AD Password Protection

Azure AD Password Protection estende la protezione delle password al mondo on-premises, impedendo agli utenti di scegliere password presenti nelle liste di password compromesse di Microsoft e nelle liste personalizzate dell'organizzazione.

```powershell
# Componenti:
# 1. Azure AD Password Protection Proxy Service (1+ server, non su DC)
# 2. Azure AD Password Protection DC Agent (su ogni DC)

# Installare il proxy
Import-Module AzureADPasswordProtection
Register-AzureADPasswordProtectionProxy -AccountUpn admin@contoso.onmicrosoft.com

# Installare l'agent sui Domain Controller (richiede riavvio)
# Scaricare AzureADPasswordProtectionDCAgentSetup.exe ed eseguire su ogni DC

# Verificare il deployment
Get-AzureADPasswordProtectionDCAgent |
    Select-Object ServerFQDN, SoftwareVersion, IsHealthy, HeartbeatUTC
Get-AzureADPasswordProtectionProxy |
    Select-Object ServerFQDN, SoftwareVersion, IsHealthy

# Configurare nel portale:
# Azure AD → Security → Authentication Methods → Password Protection
#   - Enable on Windows Server AD: Yes
#   - Mode: Audit (test) → Enforced (produzione)
#   - Custom banned passwords: nomi aziendali, prodotti, città, stagioni
#   Esempio: "contoso", "Milano2024", "Summer", "Welcome", "Password"

# Monitorare password bloccate (Event ID 30002 = rejected)
Get-WinEvent -LogName "Microsoft-Windows-Azure AD Password Protection DC Agent/Admin" -MaxEvents 50 |
    Where-Object { $_.Id -eq 30002 } |
    Select-Object TimeCreated, Message
```

### Self-Service Password Reset (SSPR)

```
Configurazione SSPR:
Azure AD → Password reset → Properties
  - SSPR enabled: All (o gruppo pilota)

Authentication methods:
  - Methods required: 2
  - Methods available:
    - Mobile phone (SMS)
    - Email
    - Authenticator app notification
    - Security questions (NON raccomandato per privileged)

On-premises integration:
  - Write back passwords to on-premises: Yes
  - Allow unlock without reset: Yes
```

```powershell
# Prerequisiti per Password Writeback:
# 1. Azure AD Connect con Password Writeback abilitato
# 2. Azure AD Premium P1
# 3. Account di servizio con permessi Reset Password sulle OU

# Verificare che il Password Writeback sia abilitato
Get-ADSyncAADPasswordResetConfiguration -Connector "contoso.com"

# Verificare i permessi dell'account di servizio
$connector = Get-ADSyncConnector -Name "contoso.com"
$accountName = $connector.ConnectivityParameters |
    Where-Object Name -eq "forest-login-user" |
    Select-Object -ExpandProperty Value
Write-Output "Account di servizio: $accountName"
# Deve avere: Reset Password, Write lockoutTime, Write pwdLastSet
```

### Password Writeback — Come Funziona

Riferimento: https://learn.microsoft.com/en-us/entra/identity/authentication/concept-sspr-writeback (consultato: 2026-05-23)

```
Flusso Password Writeback:

1. L'utente resetta la password nel cloud (SSPR, admin reset, o cambio password)
2. Entra ID verifica che il Password Writeback è abilitato per il tenant
3. Entra ID cifra la nuova password con la chiave pubblica RSA del connettore
   (la chiave privata è SOLO sul server Azure AD Connect — mai nel cloud)
4. La richiesta cifrata viene inviata via Azure Service Bus (HTTPS 443)
   al connettore Azure AD Connect on-premises
5. Il connettore decifra la password con la chiave privata locale
6. Il connettore tenta di impostare la password in AD on-premises usando
   l'API Win32 SetPassword con le credenziali dell'account di servizio
7. AD applica la password policy locale (complessità, storia, lunghezza minima)
8. Se la password soddisfa la policy → successo → risultato inviato al cloud
9. Se la password NON soddisfa la policy → fallimento → l'utente riceve
   il messaggio "La password non soddisfa i requisiti dell'organizzazione"

Modello di Sicurezza:
- La password in chiaro NON transita mai in forma leggibile nel cloud
- La cifratura RSA usa chiavi generate durante il setup di Azure AD Connect
- La chiave privata NON lascia mai il server on-premises
- Il canale Service Bus è autenticato e cifrato (TLS 1.2+)
- L'account di servizio necessita SOLO del permesso Reset Password sulle OU
  (principio del minimo privilegio)
```

### Troubleshooting Password Writeback — Errori Comuni

```powershell
# Errore: "Password does not meet the on-premises Active Directory
#          password complexity requirements"
# Causa: la password scelta dall'utente non rispetta la policy AD (GPO)
# Fix: verificare la policy GPO e informare l'utente dei requisiti
Get-ADDefaultDomainPasswordPolicy | Select-Object ComplexityEnabled,
    MinPasswordLength, PasswordHistoryCount, MinPasswordAge, MaxPasswordAge

# Errore: "An error occurred during the password writeback operation"
# Causa: l'account di servizio non ha i permessi necessari
# Fix: verificare e assegnare i permessi sull'OU
$serviceAccountSID = (Get-ADUser $accountName).SID
$acl = Get-Acl "AD:OU=Utenti,DC=contoso,DC=com"
$acl.Access | Where-Object { $_.IdentityReference -match $accountName } |
    Select-Object ActiveDirectoryRights, AccessControlType, InheritanceType

# Permessi richiesti sull'OU degli utenti:
# - Reset Password (ExtendedRight)
# - Write lockoutTime (WriteProperty)
# - Write pwdLastSet (WriteProperty)

# Errore: "The on-premises password writeback service is not responding"
# Causa: il servizio ADSync è fermo o il Service Bus non è raggiungibile
# Fix:
Get-Service "ADSync" | Select-Object Status
Test-NetConnection -ComputerName "*.servicebus.windows.net" -Port 443

# Verificare gli eventi di writeback
Get-WinEvent -LogName "Application" -FilterXPath `
    "*[System[Provider[@Name='ADSync'] and (EventID=33004 or EventID=33008)]]" |
    Select-Object -First 10 TimeCreated, Id, Message
# EventID 33004 = Password writeback riuscito
# EventID 33008 = Password writeback fallito
```

---

## AD FS Deep Dive

### Architettura AD FS

```
                              ┌──────────────────┐
                              │    Internet       │
                              │    Users          │
                              └────────┬──────────┘
                                       │ HTTPS 443
                              ┌────────┴──────────┐
                              │   Load Balancer    │
                              │   (External VIP)   │
                              └────────┬──────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                    │
              ┌─────┴─────┐    ┌──────┴─────┐    ┌───────┴────┐
              │  WAP #1    │    │  WAP #2    │    │  WAP #3    │
              │ (DMZ)      │    │ (DMZ)      │    │ (DMZ)      │
              └─────┬──────┘    └──────┬─────┘    └───────┬────┘
                    │                  │                    │
              ──────┴──────────────────┴────────────────────┘
                              │ HTTPS 443
                              │ (Internal)
                    ┌─────────┴──────────┐
                    │   Load Balancer     │
                    │   (Internal VIP)    │
                    └─────────┬──────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
        ┌─────┴─────┐  ┌─────┴─────┐  ┌─────┴─────┐
        │ ADFS #1   │  │ ADFS #2   │  │ ADFS #3   │
        │ (Farm)    │  │ (Farm)    │  │ (Farm)    │
        └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
              │               │               │
              └───────────────┼───────────────┘
                              │ LDAP/Kerberos
                    ┌─────────┴──────────┐
                    │  Domain Controllers │
                    │  AD DS              │
                    └────────────────────┘

Componenti:
- AD FS Server Farm: 2+ server Windows con ruolo AD FS
  - Autentica gli utenti contro Active Directory
  - Emette token SAML/WS-Federation/OAuth
  - Gestisce le claims rules e i relying party trusts
  - Database: WID (Windows Internal Database, fino a 5 server)
    o SQL Server (per farm più grandi)

- WAP (Web Application Proxy): 2+ server nella DMZ
  - Proxy inverso per AD FS
  - Pubblica l'endpoint di autenticazione su Internet
  - NON richiede domain-join (best practice di sicurezza)
  - Pre-autentica le richieste prima di inoltrarle ad AD FS

- Certificati richiesti:
  1. Token Signing Certificate: firma i token SAML
  2. Token Decryption Certificate: decifra i token encrypted
  3. SSL Certificate: per il servizio AD FS (es. sts.contoso.com)
  4. Service Communication Certificate: per la comunicazione WAP ↔ AD FS
```

### Claims Rules — Esempi Pratici

Le Claims Rules sono il linguaggio di scripting di AD FS che controlla quali attributi vengono inclusi nei token SAML e come vengono trasformati.

```
# Sintassi Claims Rule Language:
# condition => action;

# Rule 1: Passthrough di un attributo LDAP
# Invia l'UPN dell'utente come NameIdentifier nel token SAML
c:[Type == "http://schemas.microsoft.com/ws/2008/06/identity/claims/windowsaccountname",
   Issuer == "AD AUTHORITY"]
=> issue(store = "Active Directory",
         types = ("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/upn",
                  "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
                  "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"),
         query = ";userPrincipalName,mail,displayName;{0}",
         param = c.Value);

# Rule 2: Trasformazione — Cambiare il tipo di claim
# Converte un UPN in NameIdentifier (richiesto da molte app SaaS)
c:[Type == "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/upn"]
=> issue(Type = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier",
         Issuer = c.Issuer,
         OriginalIssuer = c.OriginalIssuer,
         Value = c.Value,
         ValueType = c.ValueType,
         Properties["http://schemas.xmlsoap.org/ws/2005/05/identity/claimproperties/format"]
           = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress");

# Rule 3: Filtro — Emettere un claim solo se l'utente è in un gruppo
c1:[Type == "http://schemas.microsoft.com/ws/2008/06/identity/claims/groupsid",
    Value == "S-1-5-21-1234567890-1234567890-1234567890-1234"]
=> issue(Type = "http://schemas.microsoft.com/ws/2008/06/identity/claims/role",
         Value = "Admin");

# Rule 4: Custom — Bloccare utenti di specifiche OU
# (Access Control Policy)
EXISTS([Type == "http://schemas.microsoft.com/ws/2008/06/identity/claims/groupsid",
        Value == "S-1-5-21-....-BlockedGroup"])
=> issue(Type = "http://schemas.microsoft.com/authorization/claims/deny",
         Value = "true");

# Rule 5: Multi-value — Inviare tutti i gruppi dell'utente
c:[Type == "http://schemas.microsoft.com/ws/2008/06/identity/claims/groupsid",
   Issuer == "AD AUTHORITY"]
=> issue(store = "Active Directory",
         types = ("http://schemas.xmlsoap.org/claims/Group"),
         query = ";tokenGroups;{0}",
         param = c.Value);

# Rule 6: Regex — Trasformare il dominio dell'email
c:[Type == "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
   Value =~ "(?i)^.+@old-domain\.com$"]
=> issue(Type = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
         Value = RegExReplace(c.Value, "@old-domain\.com$", "@new-domain.com"));
```

```powershell
# Gestione Claims Rules via PowerShell

# Elencare tutti i Relying Party Trusts
Get-AdfsRelyingPartyTrust | Select-Object Name, Identifier, Enabled |
    Format-Table -AutoSize

# Visualizzare le claims rules di un Relying Party
$rp = Get-AdfsRelyingPartyTrust -Name "Microsoft Office 365 Identity Platform"
$rp.IssuanceTransformRules
$rp.IssuanceAuthorizationRules

# Aggiungere una claims rule
$newRule = '@RuleName = "Send Department as claim"
c:[Type == "http://schemas.microsoft.com/ws/2008/06/identity/claims/windowsaccountname",
   Issuer == "AD AUTHORITY"]
=> issue(store = "Active Directory",
         types = ("http://schemas.xmlsoap.org/claims/Department"),
         query = ";department;{0}",
         param = c.Value);'

$currentRules = (Get-AdfsRelyingPartyTrust -Name "MyApp").IssuanceTransformRules
$updatedRules = $currentRules + $newRule
Set-AdfsRelyingPartyTrust -TargetName "MyApp" -IssuanceTransformRules $updatedRules

# Testare le claims rules (AD FS 2019+)
# https://sts.contoso.com/adfs/ls/ClaimsXray.aspx
# Oppure: Test-AdfsClaimRules (non disponibile in tutte le versioni)
```

### Configurazione WAP (Web Application Proxy)

```powershell
# Prerequisiti WAP:
# - Windows Server con ruolo Remote Access installato
# - Server nella DMZ, NON unito al dominio (raccomandato)
# - Certificato SSL wildcard o per il servizio AD FS
# - Connettività verso AD FS server farm (TCP 443)

# Installare il ruolo WAP
Install-WindowsFeature Web-Application-Proxy -IncludeManagementTools

# Configurare WAP per connettersi ad AD FS
$cred = Get-Credential -Message "Credenziali admin AD FS"
Install-WebApplicationProxy `
    -FederationServiceName "sts.contoso.com" `
    -FederationServiceTrustCredential $cred `
    -CertificateThumbprint "ABCD1234..."

# Verificare la configurazione WAP
Get-WebApplicationProxyConfiguration | Format-List

# Pubblicare un'applicazione web tramite WAP
Add-WebApplicationProxyApplication `
    -BackendServerUrl "https://intranet.contoso.com" `
    -ExternalCertificateThumbprint "ABCD1234..." `
    -ExternalUrl "https://intranet.contoso.com" `
    -Name "Intranet Portal" `
    -ExternalPreAuthentication ADFS `
    -ADFSRelyingPartyName "Intranet Portal"

# Verificare le applicazioni pubblicate
Get-WebApplicationProxyApplication | Select-Object Name, ExternalUrl,
    BackendServerUrl, ExternalPreAuthentication | Format-Table -AutoSize

# Monitorare la salute del WAP
Get-WebApplicationProxyHealth | Select-Object HealthState, ComponentName,
    AdditionalInfo | Format-Table -AutoSize
```

### AD FS Extranet Lockout

```powershell
# Protezione contro brute force attacks sugli endpoint AD FS esposti

# AD FS 2016+: Extranet Smart Lockout
Set-AdfsProperties -EnableExtranetLockout $true
Set-AdfsProperties -ExtranetLockoutThreshold 15        # Max tentativi
Set-AdfsProperties -ExtranetObservationWindow (New-TimeSpan -Minutes 30)
Set-AdfsProperties -ExtranetLockoutRequirePDC $false   # Non richiedere PDC per lockout

# AD FS 2019+: Extranet Smart Lockout con location awareness
Set-AdfsProperties -EnableExtranetLockout $true
Set-AdfsProperties -ExtranetLockoutMode AdfsSmartLockoutLogOnly  # Modalità audit prima

# Dopo validazione, passare a enforcement
Set-AdfsProperties -ExtranetLockoutMode AdfsSmartLockoutEnforce

# Verificare gli account bloccati
Get-AdfsAccountActivity -UserPrincipalName "mario.rossi@contoso.com"

# Sbloccare un account
Reset-AdfsAccountLockout -UserPrincipalName "mario.rossi@contoso.com"
```

---

## Certificate-Based Authentication (CBA)

La Certificate-Based Authentication permette di autenticare gli utenti usando certificati X.509 (smart card, virtual smart card, certificati software) senza password.

### CBA con AD FS (Tradizionale)

```
Flusso CBA con AD FS:

1. Utente inserisce la smart card nel lettore
2. Il browser presenta il certificato client al WAP/AD FS
3. AD FS verifica:
   - Il certificato è emesso da una CA trusted (nella NTAuth store)
   - Il certificato non è revocato (CRL/OCSP check)
   - Il certificato è nel periodo di validità
   - Il SAN (Subject Alternative Name) contiene l'UPN dell'utente
4. AD FS mappa il certificato all'utente AD (UPN mapping o explicit mapping)
5. AD FS emette il token SAML
6. L'utente è autenticato

Configurazione AD FS per CBA:
- Certificate Authentication deve essere abilitata come metodo di autenticazione
- I certificati CA root e intermedi devono essere nel Trusted Root/Intermediate store
- L'endpoint certificato deve essere abilitato (TCP 49443 di default)
```

```powershell
# Configurare AD FS per Certificate Authentication
Set-AdfsGlobalAuthenticationPolicy -PrimaryExtranetAuthenticationProvider @(
    "CertificateAuthentication",
    "FormsAuthentication"
)

# Configurare l'endpoint per client certificate (porta 49443)
Set-AdfsProperties -TlsClientPort 49443

# Verificare la configurazione
Get-AdfsGlobalAuthenticationPolicy | Select-Object -ExpandProperty PrimaryExtranetAuthenticationProvider
Get-AdfsGlobalAuthenticationPolicy | Select-Object -ExpandProperty PrimaryIntranetAuthenticationProvider
```

### CBA con Microsoft Entra ID (Cloud-Native)

A partire dal 2023, Azure AD / Entra ID supporta CBA direttamente nel cloud, senza bisogno di AD FS.

```
Configurazione Entra CBA:

Azure AD → Security → Authentication Methods → Certificate-based authentication

1. Abilitare CBA:
   - Enable: Yes
   - Target: All users o gruppo specifico

2. Configurare le CA:
   - Caricare i certificati CA (root e intermedi) come Certification Authorities
   - Ogni CA ha un CRL Distribution Point (CDP) per la revocation check

3. Configurare le regole di autenticazione:
   - Certificate Issuer + Policy OID → Authentication strength
     - Single-factor: il certificato da solo
     - Multi-factor: il certificato conta come MFA (se la CA e il policy OID
       indicano che il certificato è stato emesso con verifica dell'identità forte)

4. Configurare il binding:
   - Come Entra ID mappa il certificato all'utente:
     - SAN PrincipalName → UPN (più comune)
     - SAN RFC822Name → Email
     - Subject → DisplayName (meno sicuro)
     - SKI (Subject Key Identifier) → certificateUserIds
     - SHA1 Public Key → certificateUserIds
   - Priorità: se più metodi sono configurati, quale ha precedenza

5. Username binding (affinity binding):
   - High affinity: SAN PrincipalName, SAN RFC822Name (unicità garantita)
   - Low affinity: Subject, SKI (possibilità di conflitti)

Note:
- Entra CBA elimina la dipendenza da AD FS per gli scenari smart card
- Supporta sia X.509 hardware (smart card) che software certificates
- Supporta FIDO2 + CBA per scenari phishing-resistant MFA
```

---

## Migrazione da AD FS a PHS/PTA (Staged Rollout)

Microsoft raccomanda attivamente la migrazione da AD FS a metodi di autenticazione più semplici (PHS o PTA). Lo Staged Rollout permette di migrare gradualmente gruppi di utenti senza un cut-over completo.

```
Flusso di Migrazione Staged:

Fase 1: Preparazione (2-4 settimane)
  - Abilitare PHS come backup (anche se si usa Federation)
  - Verificare che tutti gli utenti abbiano hash sincronizzati
  - Inventario completo delle applicazioni che dipendono da AD FS:
    * Claims rules personalizzate
    * Relying party trusts
    * Conditional Access basato su device (richiede Hybrid Join)
    * Third-party MFA integration
  - Documentare ogni claims rule personalizzata
  - Identificare equivalenti in Conditional Access + Azure AD
  - Piano di rollback documentato

Fase 2: Staged Rollout (Gruppi Pilota) — 2-4 settimane
  Azure AD → Azure AD Connect → Staged Rollout
    - Enable staged rollout for managed authentication: Yes
    - Password Hash Sync: aggiungi gruppo "GRP-Pilot-PHS"

  Gli utenti nel gruppo pilota:
  - Autenticano direttamente con Azure AD (PHS)
  - NON vengono più reindirizzati ad AD FS
  - Gli altri utenti continuano a usare Federation
  - Il cambio è trasparente per l'utente

Fase 3: Validazione — 2 settimane
  - Monitorare i sign-in logs per il gruppo pilota
  - Verificare che funzionino:
    * MFA (Azure MFA deve essere configurato)
    * Conditional Access policies
    * SSPR con password writeback
    * Seamless SSO (se abilitato)
    * Tutte le applicazioni critiche
  - Raccogliere feedback dagli utenti
  - Verificare che l'help desk non riceva più ticket del normale

Fase 4: Espansione Graduale — 4-8 settimane
  - Aggiungere altri gruppi allo staged rollout (es. per dipartimento)
  - Monitorare per 2-4 settimane per gruppo
  - Risolvere eventuali problemi prima di espandere

Fase 5: Cutover Completo
  - Quando tutti gli utenti sono nello staged rollout:
  Azure AD Connect wizard → Change user sign-in
    → Password Hash Synchronization (o PTA)
  - Questo converte il dominio da Federated a Managed
  - Disabilitare lo staged rollout

Fase 6: Decommissioning AD FS — 2-4 settimane
  - Mantenere AD FS spento (non decommissionato) per 2 settimane
  - Se nessun problema: procedere
  - Rimuovere i relying party trusts
  - Disabilitare i WAP (Web Application Proxy)
  - Rimuovere il ruolo AD FS dai server
  - Rimuovere i record DNS (sts.contoso.com)
  - Rimuovere i certificati dedicati
  - Decommissionare i server
```

```powershell
# Verificare lo stato del dominio (Federated vs Managed)
Get-MsolDomain -DomainName "contoso.com" | Select-Object Name, Authentication
# Authentication = Federated → AD FS
# Authentication = Managed → PHS o PTA

# Verificare tutti i relying party trusts prima della migrazione
Get-AdfsRelyingPartyTrust | Select-Object Name, Identifier, Enabled,
    IssuanceTransformRulesFile | Export-Csv "ADFS-RP-Inventory.csv" -NoTypeInformation

# Esportare le claims rules per documentazione
Get-AdfsRelyingPartyTrust | ForEach-Object {
    $rpName = $_.Name -replace '[^\w]', '_'
    $_.IssuanceTransformRules | Out-File "Claims-$rpName.txt"
    $_.IssuanceAuthorizationRules | Out-File "AuthZ-$rpName.txt"
}

# Convertire un dominio da Federated a Managed (cutover completo)
# ATTENZIONE: operazione con impatto immediato, testare prima con staged rollout!
Set-MsolDomainAuthentication -DomainName "contoso.com" -Authentication Managed

# Verificare dopo la conversione
Get-MsolDomainFederationSettings -DomainName "contoso.com"  # Dovrebbe dare errore
Get-MsolDomain -DomainName "contoso.com" | Select-Object Authentication  # = Managed
```

---

## Microsoft Entra Connect Cloud Sync

Microsoft Entra Connect Cloud Sync (precedentemente Azure AD Connect Cloud Provisioning) è l'alternativa leggera e cloud-managed ad Azure AD Connect.

```
Confronto Azure AD Connect vs Cloud Sync:

┌────────────────────────────┬───────────────────┬───────────────────┐
│ Aspetto                    │ Azure AD Connect  │ Cloud Sync        │
├────────────────────────────┼───────────────────┼───────────────────┤
│ Installazione              │ Server dedicato   │ Agente leggero    │
│ High Availability          │ Staging server    │ Multipli agenti   │
│ Sync rules personalizzate  │ Sì (complesso)    │ Limitato          │
│ Writeback (gruppi, device) │ Completo          │ Parziale          │
│ Multi-forest               │ Sì (singola ist.) │ Sì (multi-agente) │
│ Exchange Hybrid            │ Completo          │ Parziale          │
│ Gestione                   │ On-premises       │ Cloud (portale)   │
│ Aggiornamenti              │ Manuali           │ Automatici        │
│ PTA support                │ Sì                │ No                │
│ Password writeback         │ Sì                │ Sì (2023+)        │
│ Group writeback             │ Sì                │ No                │
│ Device writeback           │ Sì                │ No                │
│ Directory extensions       │ Sì                │ Sì (limitato)     │
│ Attribute mapping          │ Sync Rules Editor │ Portale Azure     │
│ SQL Server                 │ LocalDB o full    │ Non necessario    │
│ Filtering                  │ OU, domain, attr  │ OU, attr, scope   │
│ SCIM provisioning          │ No                │ Sì (tramite app)  │
└────────────────────────────┴───────────────────┴───────────────────┘

Quando usare Cloud Sync:
- Multi-forest con foreste disconnesse (acquisizioni, M&A)
- Necessità di alta disponibilità senza staging server
- Scenari semplici senza sync rules complesse
- Preferenza per gestione cloud-only
- Ambienti dove non si vuole un server Windows dedicato

Quando NON usare Cloud Sync:
- Exchange Hybrid completo richiesto
- Sync rules complesse necessarie
- Device writeback richiesto
- Group writeback richiesto
- Pass-through Authentication (non supportato)
- Large-scale attribute transformation necessaria
```

```powershell
# Installare l'agente Cloud Sync
# 1. Scaricare dal portale: Azure AD → Azure AD Connect → Cloud Sync → Download agent
# 2. Eseguire AADConnectProvisioningAgentSetup.exe
# 3. Configurare nel portale Azure: Azure AD → Cloud Sync

# Verificare lo stato dell'agente
Get-Service "AADConnectProvisioningAgent" | Select-Object Status, StartType

# Configurazione via portale Azure:
# Azure AD → Azure AD Connect → Cloud Sync → New configuration
# 1. Selezionare l'agente
# 2. Configurare scope (dominio, OU)
# 3. Configurare attribute mapping
# 4. Abilitare provisioning

# Monitorare via portale:
# Azure AD → Cloud Sync → Provisioning logs
# Mostra oggetti sincronizzati, errori, warning
```

---

## Best Practices

### Architettura

**PHS come metodo primario (o come backup):** Anche se si utilizza PTA o Federation per l'autenticazione primaria, abilitare PHS come backup. In caso di failure dell'infrastruttura on-premises, Azure AD può autenticare gli utenti con gli hash sincronizzati. PHS abilita anche la leaked credential detection di Identity Protection.

**Staging Mode per i test:** Azure AD Connect supporta una "staging mode" dove il server esegue import e sync ma non esporta. Usare un secondo server in staging mode come hot-standby e per testare modifiche alle sync rules.

**Non sincronizzare gli account admin:** Gli account Tier 0 (Domain Admins, Enterprise Admins, Schema Admins) non dovrebbero MAI essere sincronizzati in Azure AD. Creare account cloud-only dedicati per l'amministrazione di Azure AD. Questo segue il principio della separazione dei privilege path.

### Sicurezza

**Rotazione regolare della chiave Kerberos per Seamless SSO:** La chiave di decryption dell'account AZUREADSSOACC$ deve essere ruotata almeno ogni 30 giorni. Se la chiave viene compromessa, un attaccante può creare ticket Kerberos per qualsiasi utente — Silver Ticket attack contro Azure AD.

**Implementare Conditional Access gradualmente:** Iniziare con policy in Report-Only mode per almeno 2 settimane. Analizzare i sign-in logs per identificare impatti. Solo dopo la validazione, passare a enforcement.

**Mantenere break-glass accounts:** Almeno 2 account cloud-only con ruolo Global Administrator, esclusi da TUTTE le policy di Conditional Access, con:
- Password lunga (>24 caratteri) e complessa
- Conservata in cassaforte fisica (2 copie in 2 location)
- MFA con hardware token fisico dedicato
- Monitoraggio di ogni accesso (alert immediato)
- Test trimestrale di accesso funzionante

### Governance

**Usare PIM per tutti i ruoli privilegiati:** Nessun utente dovrebbe avere un'assegnazione permanente a ruoli privilegiati in Azure AD. Usare PIM per tutti i ruoli con rischio Medio o superiore.

**Implementare Access Reviews trimestrali:** Automatizzare la revisione degli accessi per gruppi privilegiati, applicazioni sensibili e ruoli Azure AD. Configurare auto-removal per accessi non confermati.

**Adottare Entitlement Management:** Usare access packages per gestire il ciclo di vita degli accessi. L'onboarding e l'offboarding diventano processi governati e automatizzati anziché richieste ad-hoc.

---

## Troubleshooting

### Problema: Utente Non Si Sincronizza in Azure AD

**Sintomi**: Un utente creato in AD on-premises non appare in Azure AD dopo diversi cicli di sync.

**Cause possibili**:
1. L'utente è fuori dall'OU scope di sincronizzazione
2. Ha un attributo filtrato (cloudFiltered = True)
3. Conflitto di UPN o proxyAddress con un altro oggetto
4. Manca di un attributo obbligatorio (UPN, sourceAnchor)
5. L'utente è un account di servizio senza UPN valido

**Soluzione**:

```powershell
# Step 1: Verificare se l'utente è nel connector space
$csObject = Get-ADSyncCSObject -ConnectorName "contoso.com" `
    -DistinguishedName "CN=Mario Rossi,OU=Utenti,DC=contoso,DC=com"
if ($csObject -eq $null) {
    Write-Warning "L'utente NON è nel connector space."
    Write-Warning "Verificare: OU filtering, domain filtering, scoping filter delle sync rules"
} else {
    Write-Output "L'utente è nel connector space. Verificare le sync rules applicate..."
}

# Step 2: Verificare le sync rules applicate
$csObject | Get-ADSyncCSObjectLog -NumberRequested 1

# Step 3: Verificare gli errori di esportazione
Get-ADSyncCSObject -ConnectorName "contoso.com - AAD" |
    Where-Object HasExportError | Select-Object DistinguishedName, ExportErrorMessage

# Step 4: Verificare i conflitti UPN e proxyAddress
Get-ADUser "mario.rossi" -Properties UserPrincipalName, ProxyAddresses, mail
# L'UPN deve essere unico in Azure AD
# Il proxyAddress SMTP: primario deve essere unico

# Step 5: Diagnostica automatica
Invoke-ADSyncDiagnostics -ObjectSync -ADConnectorName "contoso.com" `
    -ADObjectDN "CN=Mario Rossi,OU=Utenti,DC=contoso,DC=com"

# Step 6: Verificare nel metaverse
$mvObject = Get-ADSyncMVObject -Identifier (
    $csObject.ConnectedMVObjectId)
$mvObject | Select-Object ObjectId, ObjectType, Lineage
```

### Problema: Hybrid Azure AD Join Fallisce — dsregcmd Mostra "NO"

**Sintomi**: `dsregcmd /status` mostra `AzureAdJoined: NO` su un computer unito al dominio.

**Cause possibili**:
1. SCP non configurato o non raggiungibile
2. Il computer non raggiunge gli endpoint Azure AD
3. L'oggetto computer non è nell'OU sincronizzata
4. Conflitto con un dispositivo già registrato (stale device)
5. Clock skew > 5 minuti
6. Il task scheduled Automatic-Device-Join non è in esecuzione

```powershell
# Step 1: Verificare il SCP
nltest /dsgetsite  # Verificare il sito AD

# Step 2: dsregcmd diagnostica completa
dsregcmd /status   # Sezione "Diagnostic Data" mostra errori dettagliati

# Step 3: Verificare la connettività agli endpoint
$endpoints = @(
    "https://enterpriseregistration.windows.net"
    "https://login.microsoftonline.com"
    "https://device.login.microsoftonline.com"
    "https://autologon.microsoftazuread-sso.com"
)
foreach ($ep in $endpoints) {
    try { Invoke-WebRequest $ep -UseBasicParsing -TimeoutSec 10; Write-Output "OK: $ep" }
    catch { Write-Warning "FAIL: $ep - $($_.Exception.Message)" }
}

# Step 4: Verificare l'oggetto computer in AD
Get-ADComputer $env:COMPUTERNAME -Properties userCertificate, OperatingSystem |
    Select-Object Name, userCertificate, OperatingSystem

# Step 5: Verificare il task scheduled
Get-ScheduledTask -TaskPath "\Microsoft\Windows\Workplace Join\" |
    Select-Object TaskName, State, LastRunTime, LastTaskResult
# LastTaskResult 0 = success
# LastTaskResult non-zero = consultare errore

# Step 6: Forzare la registrazione
dsregcmd /join           # Tenta manualmente il join
dsregcmd /forcerecovery  # Se precedente join è corrotto

# Step 7: Verificare il clock
w32tm /query /status     # Verificare la sincronizzazione NTP
```

### Problema: Conditional Access Blocca Utenti Legittimi

**Sintomi**: Utenti legittimi vengono bloccati dall'accesso a risorse cloud. Errore: "Access has been blocked by Conditional Access policies."

```powershell
# Step 1: Identificare la policy responsabile
# Azure AD → Sign-in logs → Filtrare per utente
# La colonna "Conditional Access" mostra quale policy ha bloccato

# Step 2: Usare il "What If" tool per simulare
# Azure AD → Conditional Access → What If
# Inserire: User, Cloud app, Device platform, Location, Sign-in risk
# Risultato: mostra quali policy si applicano e il risultato atteso

# Step 3: Verificare lo stato del dispositivo
dsregcmd /status  # Sul dispositivo dell'utente
# AzureAdJoined, Compliant, MFA status

# Step 4: Se è un problema temporaneo, escludere l'utente
# Azure AD → Conditional Access → Policy → Exclude → Users/Groups
# IMPORTANTE: creare un ticket per tracciare e rimuovere l'esclusione

# Step 5: Verificare le named locations
# Se l'utente è in viaggio, il suo IP potrebbe non essere nella trusted location
# Soluzione: usare VPN aziendale o aggiungere temporaneamente il range IP
```

### Problema: Password Hash Sync Non Funziona

**Sintomi**: Le password cambiate on-premises non si sincronizzano con Azure AD. Gli utenti non riescono ad accedere con la nuova password.

```powershell
# Step 1: Verificare lo stato del PHS
Get-ADSyncAADPasswordSyncConfiguration -SourceConnector "contoso.com"

# Step 2: Verificare gli eventi
Get-WinEvent -LogName "Application" -FilterXPath @"
*[System[Provider[@Name='Directory Synchronization'] and (EventID=650 or EventID=651 or EventID=656 or EventID=657)]]
"@ | Select-Object -First 20 TimeCreated, Id, Message

# EventID 650 = Password sync heartbeat
# EventID 651 = Password sync error
# EventID 656 = Password sync started
# EventID 657 = Password sync completed

# Step 3: Diagnostica specifica per utente
Invoke-ADSyncDiagnostics -PasswordSync -ADConnectorName "contoso.com" `
    -ADObjectDN "CN=Mario Rossi,OU=Utenti,DC=contoso,DC=com"

# Step 4: Verificare i permessi dell'account di servizio
# L'account di servizio Azure AD Connect deve avere:
# "Replicating Directory Changes" sul dominio
# "Replicating Directory Changes All" sul dominio
$serviceAccount = "MSOL_<unique>"  # Formato tipico
Get-ACL "AD:DC=contoso,DC=com" | Select-Object -ExpandProperty Access |
    Where-Object { $_.IdentityReference -like "*$serviceAccount*" }

# Step 5: Riavviare il servizio di sincronizzazione
Restart-Service "ADSync"
Start-ADSyncSyncCycle -PolicyType Delta
```

### Problema: Errori di Esportazione verso Azure AD

**Sintomi**: Il sync log mostra errori di esportazione. Gli oggetti non vengono creati/aggiornati in Azure AD.

```powershell
# Errori comuni di esportazione:

# 1. InvalidSoftMatch — Conflitto di proxyAddress
# Soluzione: verificare unicità dell'indirizzo email
Get-ADUser -Filter * -Properties ProxyAddresses |
    Select-Object SamAccountName, @{N='SMTP';E={
        ($_.ProxyAddresses | Where-Object {$_ -clike "SMTP:*"}) -replace "SMTP:",""
    }} | Group-Object SMTP | Where-Object Count -gt 1

# 2. ObjectTypeMismatch — L'oggetto esiste in Azure AD come tipo diverso
# Es: un utente AD corrisponde a un contatto Azure AD
# Soluzione: eliminare l'oggetto conflittuale in Azure AD

# 3. DataValidationFailed — Attributo con formato non valido
# Es: UPN senza dominio verificato, phone number troppo lungo
Get-ADSyncCSObject -ConnectorName "contoso.com - AAD" |
    Where-Object HasExportError |
    Select-Object DistinguishedName, ExportErrorMessage |
    ForEach-Object {
        Write-Output "Object: $($_.DistinguishedName)"
        Write-Output "Error: $($_.ExportErrorMessage)"
        Write-Output "---"
    }

# 4. IdentityNotFound — L'oggetto referenziato non esiste
# Comune con gruppi che hanno membri fuori dallo scope di sync
# Soluzione: verificare che tutti i membri del gruppo siano sincronizzati
```

---

## Domande e Risposte (Q&A)

**D1: Posso usare PHS e PTA contemporaneamente?**
R: No, non sulla stessa configurazione. Puoi avere PHS abilitato come backup mentre usi PTA come metodo primario. In questo caso, PHS sincronizza gli hash per il fallback e per Identity Protection, ma l'autenticazione primaria passa attraverso gli agenti PTA. Se gli agenti PTA sono tutti offline, Azure AD NON fallback automaticamente a PHS — l'autenticazione fallisce. Per il failover automatico, devi usare Staged Rollout per spostare gli utenti manualmente su PHS.

**D2: Cosa succede se il server Azure AD Connect va offline?**
R: La sincronizzazione si ferma, ma l'autenticazione continua normalmente. Con PHS, gli utenti autenticano con gli hash già sincronizzati. Le modifiche fatte on-premises (nuovi utenti, cambio password, disabilitazione account) non si propagano al cloud fino al ripristino del server. Per questo è critico avere un staging server pronto per la promozione.

**D3: Quanti agenti PTA servono per un'organizzazione di 10.000 utenti?**
R: Minimo 3 agenti. Ogni agente può gestire circa 2000-3000 autenticazioni simultanee. Con 10k utenti, il carico di picco potrebbe essere 500-1000 autenticazioni/minuto (es. lunedì mattina). 3 agenti forniscono ridondanza n+1, quindi se uno va offline, i restanti 2 gestiscono il carico.

**D4: Come funziona il failover di Seamless SSO se l'account AZUREADSSOACC$ viene compromesso?**
R: Se sospetti la compromissione, ruota immediatamente la chiave Kerberos con `Update-AzureADSSOForest`. La vecchia chiave diventa immediatamente invalida, e tutti i ticket Kerberos emessi con la vecchia chiave vengono rifiutati. Gli utenti dovranno ri-autenticarsi con username/password (una volta), dopodiché Seamless SSO funzionerà nuovamente con la nuova chiave.

**D5: Qual è la differenza tra Azure AD Join e Hybrid Azure AD Join? Quale scegliere?**
R: Azure AD Join è per dispositivi cloud-only — nessuna dipendenza da AD on-premises. Hybrid Join è per dispositivi che devono accedere sia a risorse cloud che on-premises (file share, stampanti, applicazioni legacy). Se l'organizzazione sta migrando verso il cloud e non ha applicazioni legacy on-premises, Azure AD Join è preferibile. Se ci sono dipendenze on-premises (GPO, NTLM/Kerberos per risorse interne), Hybrid Join è necessario.

**D6: È sicuro sincronizzare gli hash delle password nel cloud?**
R: Sì, con le dovute precauzioni. Azure AD NON memorizza l'hash NTLM della password. Memorizza un hash derivato (PBKDF2-HMAC-SHA256 con 1000 iterazioni + salt) dell'hash NTLM. Questo hash derivato non è utilizzabile per pass-the-hash attacks e non può essere invertito per ottenere la password. La trasmissione è cifrata con TLS 1.2+. Il rischio di un breach di Azure AD è molto più basso di quello di un DC on-premises mal protetto.

**D7: Come gestisco gli account di servizio nella sincronizzazione ibrida?**
R: Gli account di servizio on-premises generalmente NON devono essere sincronizzati in Azure AD. Usare una OU dedicata per gli account di servizio ed escluderla dal filtering. Per servizi che richiedono identità cloud, creare account separati cloud-only o usare Managed Identities in Azure. Per service principal, usare App Registrations con certificati (non password).

**D8: Qual è la strategia raccomandata per i break-glass accounts?**
R: Creare esattamente 2 account cloud-only con ruolo Global Administrator permanente (eccezione a PIM). Non sincronizzarli da AD. Escluderli da TUTTE le Conditional Access policies. Usare password di 24+ caratteri casuali, memorizzate in 2 copie in cassaforti fisiche separate. MFA con FIDO2 key hardware dedicata (non Authenticator app, che dipende da un telefono). Testare l'accesso ogni 90 giorni. Configurare alert immediato su ogni sign-in di questi account.

**D9: Entitlement Management vs. self-service group management: quando usare quale?**
R: Self-service group management è adatto per gruppi semplici dove il owner approva le richieste one-off. Entitlement Management è per scenari strutturati: bundle di risorse (access packages), ciclo di vita automatizzato (scadenza, access review), approvazione multi-livello, audit trail completo, e supporto per utenti esterni (B2B). Se hai più di 5 applicazioni enterprise e 500+ utenti, Entitlement Management scala molto meglio.

**D10: Come migro da AD FS a PHS senza downtime?**
R: Usa Staged Rollout. Abilita PHS come metodo di sync (anche se il dominio è ancora federato). Crea un gruppo pilota (es. 50 utenti IT). Aggiungi il gruppo a Staged Rollout. Questi utenti autenticano via PHS, gli altri continuano con AD FS. Espandi gradualmente il gruppo. Quando tutti sono migrati, converti il dominio da Federated a Managed con `Set-MsolDomainAuthentication -Authentication Managed`. Mantieni AD FS spento (non decommissionato) per 2 settimane come rollback. Dopo la validazione, decommissiona AD FS.

---

## Esercizi Pratici

### Esercizio 1: Configurazione Completa di Azure AD Connect

**Obiettivo:** Configurare Azure AD Connect con PHS, Seamless SSO e OU filtering.

**Scenario:** Contoso ha un dominio AD `contoso.com` con le seguenti OU:
- `OU=Utenti` (da sincronizzare)
- `OU=Gruppi` (da sincronizzare)
- `OU=ServiceAccounts` (da escludere)
- `OU=AdminTier0` (da escludere)

**Passi:**
1. Installare Azure AD Connect su un server Windows dedicato
2. Configurare PHS come metodo di autenticazione
3. Abilitare Seamless SSO
4. Configurare OU filtering per sincronizzare solo `Utenti` e `Gruppi`
5. Verificare la sincronizzazione con `Get-ADSyncScheduler`
6. Verificare che AZUREADSSOACC$ sia stato creato
7. Configurare la GPO per i siti Intranet
8. Testare Seamless SSO da un PC unito al dominio

**Criteri di successo:**
- Delta sync funzionante ogni 30 minuti
- Gli utenti in `OU=Utenti` appaiono in Azure AD
- Gli utenti in `OU=AdminTier0` NON appaiono in Azure AD
- Seamless SSO funziona da un PC in rete aziendale


### Esercizio 2: Conditional Access — Implementazione Progressiva

**Obiettivo:** Implementare un set di policy Conditional Access seguendo il framework Zero Trust.

**Scenario:** Implementare le seguenti policy per Contoso:
1. Blocco legacy authentication
2. MFA per tutti gli utenti
3. Require compliant device per M365
4. Geo-blocking per paesi non autorizzati
5. Block high-risk sign-ins

**Passi:**
1. Creare i break-glass accounts (2 account cloud-only)
2. Implementare ogni policy in Report-Only mode
3. Analizzare i sign-in logs per 2 settimane
4. Identificare gli impatti (utenti che sarebbero bloccati)
5. Risolvere i problemi (es. utenti che usano client legacy)
6. Passare la prima policy (legacy auth block) a enforcement
7. Procedere con le altre policy una alla volta

**Criteri di successo:**
- Break-glass accounts funzionanti ed esclusi da tutte le policy
- Tutte le policy in enforcement dopo il periodo di test
- Zero ticket help desk non gestiti


### Esercizio 3: PIM e Access Reviews

**Obiettivo:** Configurare PIM per i ruoli privilegiati e implementare Access Reviews trimestrali.

**Scenario:**
- 5 Global Admins attuali con ruolo permanente
- Obiettivo: convertire tutti in eligible assignment con PIM
- Implementare access review trimestrale

**Passi:**
1. Verificare i current role assignments permanenti
2. Per ogni Global Admin, creare un eligible assignment con PIM
3. Configurare le impostazioni del ruolo: max 2h, MFA, approval
4. Rimuovere gli active assignment permanenti (dopo aver verificato PIM)
5. Creare un Access Review trimestrale per Global Admin
6. Testare l'attivazione PIM con un account
7. Verificare l'audit log

**Criteri di successo:**
- Zero permanent active assignments per Global Admin
- Tutti gli admin in eligible assignment
- Access Review configurata e funzionante
- Audit log registra tutte le attivazioni


### Esercizio 4: Entitlement Management per Onboarding

**Obiettivo:** Creare un sistema automatizzato di onboarding usando Entitlement Management.

**Scenario:** Il dipartimento Marketing necessita di un processo strutturato:
- Nuovi dipendenti richiedono accesso a: gruppo Marketing-All, app Marketing Dashboard, sito SharePoint
- L'approvazione deve passare dal manager
- L'accesso scade dopo 365 giorni con access review semestrale

**Passi:**
1. Creare un catalogo "Marketing"
2. Aggiungere le risorse al catalogo
3. Creare l'access package "Marketing Onboarding"
4. Configurare la policy di approvazione
5. Configurare la scadenza e l'access review
6. Testare la richiesta come utente
7. Approvare come manager
8. Verificare l'assegnazione delle risorse

**Criteri di successo:**
- L'utente può richiedere l'access package dal portale My Access
- Il manager riceve la notifica e approva
- Le risorse vengono assegnate automaticamente
- L'access review funziona dopo 180 giorni


### Esercizio 5: Migrazione da AD FS a PHS con Staged Rollout

**Obiettivo:** Pianificare e simulare la migrazione da AD FS a PHS.

**Scenario:** Contoso usa AD FS per l'autenticazione. L'obiettivo è migrare a PHS eliminando l'infrastruttura AD FS.

**Passi:**
1. Inventario dei Relying Party Trusts di AD FS
2. Esportare tutte le claims rules personalizzate
3. Identificare le applicazioni che dipendono da claims rules specifiche
4. Mappare le claims rules ad equivalenti Conditional Access + Azure AD
5. Abilitare PHS come sync method (senza cambiare il dominio)
6. Configurare Staged Rollout con un gruppo pilota IT
7. Testare tutte le applicazioni con il gruppo pilota
8. Espandere gradualmente
9. Convertire il dominio a Managed
10. Decommissionare AD FS (dopo 2 settimane di stabilità)

**Criteri di successo:**
- Inventario completo delle dipendenze AD FS
- Piano di mapping claims → CA/Azure AD
- Staged Rollout funzionante per il gruppo pilota
- Nessuna interruzione di servizio durante la migrazione


### Esercizio 6: Hardening della Configurazione Hybrid Identity

**Obiettivo:** Implementare tutte le best practice di sicurezza per l'identità ibrida.

**Checklist:**
- [ ] Separazione degli account admin: cloud-only per Azure AD, on-prem per AD
- [ ] PHS abilitato (anche se PTA/Federation è il metodo primario)
- [ ] Seamless SSO con rotazione chiave ogni 30 giorni
- [ ] Azure AD Connect su server dedicato (non su DC)
- [ ] Staging server configurato e testato
- [ ] Break-glass accounts creati, esclusi da CA, monitorati
- [ ] PIM configurato per tutti i ruoli critici
- [ ] Conditional Access: legacy auth bloccata, MFA per tutti, geo-blocking
- [ ] Access Reviews trimestrali per ruoli privilegiati
- [ ] Password Protection abilitata on-premises e nel cloud
- [ ] SSPR con password writeback abilitato
- [ ] Azure AD Connect Health configurato con alerting
- [ ] Monitoraggio AZUREADSSOACC$ password rotation
- [ ] Named Locations configurate per uffici e VPN

---

## Auto-valutazione

1. Qual è la differenza tra **user risk** e **sign-in risk** in Identity Protection? Fai un esempio concreto per ciascuno.
2. Spiega il flusso interno di **Password Hash Synchronization**: quanti passaggi di derivazione applica Azure AD Connect all'hash NTLM prima di inviarlo al cloud?
3. Un utente ha perso il telefono con Microsoft Authenticator e la FIDO2 key è rimasta a casa. Quali passi segui come admin per ripristinare l'accesso? (Procedura "All MFA Lost")
4. Perché è critico ruotare la chiave Kerberos dell'account AZUREADSSOACC$ ogni 30 giorni? Quale attacco diventa possibile in caso di compromissione?
5. Il server Azure AD Connect primario è andato offline. Descrivi la procedura step-by-step per promuovere lo staging server.
6. Qual è la differenza tra un **Eligible assignment** e un **Active assignment** in PIM? Perché si preferisce l'eligible?
7. Spiega come funziona il **Password Writeback**: la password in chiaro transita nel cloud? Quale meccanismo di cifratura protegge il flusso?
8. Un Conditional Access policy in Report-Only mode mostra 200 "Report-only: Failure" nella prima settimana. Cosa significa e come procedi?
9. Confronta **Azure AD Connect** e **Cloud Sync**: in quale scenario scegli l'uno piuttosto che l'altro? Cita almeno 3 criteri discriminanti.
10. Descrivi il flusso completo di Staged Rollout per migrare da AD FS a PHS. Quante fasi prevede e qual è il rollback plan?

---

## Glossario Locale

| Termine | Definizione |
|---|---|
| **Source Anchor (ImmutableId)** | Attributo che collega in modo permanente un oggetto AD on-premises al corrispondente in Entra ID. Default: `ms-DS-ConsistencyGuid`. Una volta stabilito, non deve mai cambiare. |
| **Connector Space** | Staging area nel sync engine che contiene proiezioni temporanee degli oggetti AD o Entra ID, usate per calcolare le differenze durante la sincronizzazione. |
| **Metaverse** | Database centrale unificato nel sync engine dove gli oggetti da AD e Entra ID vengono "uniti" tramite regole di join per creare una vista consolidata dell'identità. |
| **Primary Refresh Token (PRT)** | Token emesso da Entra ID ai dispositivi registrati (Azure AD Join / Hybrid Join) che abilita il Single Sign-On verso le risorse cloud senza re-autenticazione. |
| **Temporary Access Pass (TAP)** | Codice temporaneo monouso emesso da un admin per consentire a un utente di accedere e registrare nuovi metodi MFA quando tutti i metodi precedenti sono stati persi. |
| **PIM Eligible Assignment** | Assegnazione di ruolo dove l'utente è idoneo ma non ha il ruolo attivo. Deve richiedere l'attivazione con MFA, giustificazione e opzionalmente approvazione. |
| **PIM Active Assignment** | Assegnazione di ruolo dove l'utente ha il ruolo attivo (temporaneo dopo attivazione o permanente). Ha tutti i privilegi del ruolo per la durata configurata. |
| **Staged Rollout** | Funzionalità che permette di migrare gradualmente gruppi di utenti da autenticazione federata (AD FS) a managed (PHS/PTA) senza un cutover completo del dominio. |
| **Break-Glass Account** | Account di emergenza cloud-only con ruolo Global Administrator permanente, escluso da tutte le Conditional Access policy, per accedere al tenant quando tutti gli altri metodi falliscono. |
| **Sign-in Risk** | Livello di rischio calcolato da Identity Protection per ogni singolo tentativo di autenticazione, basato su segnali come IP anonimo, viaggio atipico, password spray. |
| **User Risk** | Livello di rischio cumulativo calcolato sull'identità complessiva dell'utente, basato su segnali come credenziali trovate in breach, attività anomala persistente. |
| **Password Writeback** | Meccanismo che consente il reset della password nel cloud (SSPR) con propagazione sicura verso AD on-premises tramite canale cifrato RSA su Azure Service Bus. |
| **Group Writeback v2** | Funzionalità che sincronizza gruppi creati in Entra ID (M365 Groups, Security Groups) verso AD on-premises per l'uso con applicazioni legacy. |
| **Phishing-resistant MFA** | Metodi di autenticazione che non possono essere intercettati tramite phishing: FIDO2 security keys e Windows Hello for Business (certificato bound al dispositivo). |
| **Access Package** | Bundle di risorse (gruppi, app, siti SharePoint, ruoli) gestito da Entitlement Management che può essere richiesto come unità, con policy di approvazione, scadenza e access review. |

---

## Letture Primarie Consigliate

1. **Microsoft Entra hybrid identity documentation** — https://learn.microsoft.com/en-us/entra/identity/hybrid/ — Hub principale per tutta la documentazione sull'identità ibrida, inclusi Connect, Cloud Sync, PHS, PTA, Federation (consultato: 2026-05-23)
2. **Identity Protection risk detections** — https://learn.microsoft.com/en-us/entra/id-protection/concept-identity-protection-risks — Catalogo completo dei tipi di rilevamento del rischio, con classificazione realtime/offline e azioni raccomandate (consultato: 2026-05-23)
3. **Conditional Access design guide** — https://learn.microsoft.com/en-us/entra/identity/conditional-access/plan-conditional-access — Guida alla pianificazione delle policy CA in ambienti enterprise, con framework di naming e deployment (consultato: 2026-05-23)
4. **Temporary Access Pass** — https://learn.microsoft.com/en-us/entra/identity/authentication/howto-authentication-temporary-access-pass — Configurazione, emissione e gestione del TAP per onboarding e recovery MFA (consultato: 2026-05-23)
5. **PIM for Azure AD roles** — https://learn.microsoft.com/en-us/entra/id-governance/privileged-identity-management/pim-configure — Configurazione completa di PIM con role settings, approval workflow, notifiche e audit (consultato: 2026-05-23)
6. **Emergency access accounts in Entra ID** — https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/security-emergency-access — Best practice per break-glass accounts: creazione, protezione, monitoraggio, test periodico (consultato: 2026-05-23)
7. **Migrate from AD FS to password hash synchronization** — https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/plan-migrate-adfs-password-hash-sync — Piano dettagliato di migrazione con staged rollout, inventario dipendenze, mapping claims → CA (consultato: 2026-05-23)
8. **Azure AD Connect Health** — https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/how-to-connect-health-operations — Installazione agenti, configurazione alert, dashboard errori, troubleshooting (consultato: 2026-05-23)

---

## Riferimenti

- Microsoft Docs: Azure AD Connect — https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/whatis-azure-ad-connect
- Microsoft Docs: PHS — https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/how-to-connect-password-hash-synchronization
- Microsoft Docs: PHS internals — https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/how-to-connect-password-hash-synchronization#detailed-description-of-how-password-hash-synchronization-works
- Microsoft Docs: PTA — https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/how-to-connect-pta
- Microsoft Docs: PTA deep dive — https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/how-to-connect-pta-how-it-works
- Microsoft Docs: Seamless SSO — https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/how-to-connect-sso
- Microsoft Docs: Conditional Access — https://learn.microsoft.com/en-us/entra/identity/conditional-access/
- Microsoft Docs: PIM — https://learn.microsoft.com/en-us/entra/id-governance/privileged-identity-management/
- Microsoft Docs: Access Reviews — https://learn.microsoft.com/en-us/entra/id-governance/access-reviews-overview
- Microsoft Docs: Entitlement Management — https://learn.microsoft.com/en-us/entra/id-governance/entitlement-management-overview
- Microsoft Docs: Hybrid Azure AD Join — https://learn.microsoft.com/en-us/entra/identity/devices/how-to-hybrid-join
- Microsoft Docs: AD FS — https://learn.microsoft.com/en-us/windows-server/identity/ad-fs/ad-fs-overview
- Microsoft Docs: Certificate-Based Authentication — https://learn.microsoft.com/en-us/entra/identity/authentication/concept-certificate-based-authentication
- Microsoft Docs: Cloud Sync — https://learn.microsoft.com/en-us/entra/identity/hybrid/cloud-sync/what-is-cloud-sync
- Microsoft Docs: Device Writeback — https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/how-to-connect-device-writeback
- Microsoft Docs: Staged Rollout — https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/how-to-connect-staged-rollout
- Microsoft Docs: Break-glass accounts — https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/security-emergency-access
