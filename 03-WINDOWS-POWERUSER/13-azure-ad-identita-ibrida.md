# Azure AD e Identità Ibrida — Guida Completa

> **Modulo 13** · **Aggiornamento:** 2026-05-23

| Campo | Valore |
|---|---|
| **Corso** | Windows per ingegneri di sistema |
| **Fase** | 3 — Identità e autenticazione cloud |
| **Modulo** | 13 — Azure AD e Identità Ibrida |
| **Versione** | 2.0 |
| **Livello** | Advanced (avanzato) |
| **Prerequisiti** | Padronanza di Active Directory DS (→ `01-active-directory.md`), familiarità con PowerShell (→ `02-powershell.md`), concetti base di rete Windows (→ `06-rete-windows.md`), conoscenza dei protocolli di autenticazione (Kerberos, LDAP) |
| **Obiettivi di apprendimento** | 1) Descrivere l'architettura di Microsoft Entra ID e le differenze rispetto ad AD DS on-premise · 2) Pianificare e configurare Microsoft Entra Connect con PHS, PTA o Federation · 3) Implementare Conditional Access policies per scenari Zero Trust · 4) Configurare MFA con metodi resistenti al phishing (FIDO2, Windows Hello) · 5) Gestire device identity (registered, joined, hybrid joined) e le relative policy · 6) Utilizzare PIM per l'accesso privilegiato just-in-time e configurare Access Reviews · 7) Registrare applicazioni in Entra ID e gestire flussi OAuth 2.0 e permessi API · 8) Pianificare e monitorare una migrazione da AD FS ad autenticazione gestita |
| **Tempo stimato** | 20–28 ore (studio + esercizi + laboratorio) |
| **Ultimo aggiornamento** | 2026-05-23 |
| **Versioni di riferimento** | Microsoft Entra ID (2026), Entra Connect 2.3.x, Entra Connect Cloud Sync, PowerShell 7.5.x, Microsoft.Graph 2.x, Intune 2406+ |
| **Tag** | `entra-id`, `azure-ad`, `hybrid-identity`, `conditional-access`, `mfa`, `pim`, `sso`, `fido2`, `entra-connect`, `zero-trust`, `b2b`, `oauth2`, `app-registration` |

## Idee guida
1. **Azure AD Connect (legacy) → Microsoft Entra Connect (modern name).**
2. **Password hash sync vs Pass-through auth vs ADFS.**
3. **Conditional Access: rule-based MFA enforcement.**
4. **Microsoft 365 license = Azure AD identity.**
5. **Zero Trust: verifica ogni accesso, ogni volta, da ogni dispositivo.**
6. **Break-glass accounts: 2 account emergenza esclusi da tutte le policy.**
7. **Identity Protection: risk-based conditional access per detection automatica.**


## Indice

- [Panoramica](#panoramica)
- [Mappa Concettuale](#mappa-concettuale)
- [Architettura Entra ID](#architettura-entra-id)
- [Entra ID vs AD DS — Differenze Chiave](#entra-id-vs-ad-ds--differenze-chiave)
- [Edizioni Entra ID — Confronto Funzionalità](#edizioni-entra-id--confronto-funzionalità)
- [Microsoft Entra ID (Azure AD)](#microsoft-entra-id-azure-ad)
- [Entra ID — Gestione Avanzata Utenti e Gruppi](#entra-id--gestione-avanzata-utenti-e-gruppi)
- [Azure AD Connect](#azure-ad-connect)
- [Azure AD Connect — Prerequisiti di Installazione](#azure-ad-connect--prerequisiti-di-installazione)
- [Azure AD Connect — Filtering Avanzato](#azure-ad-connect--filtering-avanzato)
- [Azure AD Connect — Sync Rules e Trasformazioni](#azure-ad-connect--sync-rules-e-trasformazioni)
- [Azure AD Connect — Troubleshooting Sync](#azure-ad-connect--troubleshooting-sync)
- [Metodi di Autenticazione — Confronto Dettagliato](#metodi-di-autenticazione--confronto-dettagliato)
- [Hybrid Identity](#hybrid-identity)
- [Seamless SSO — Deep Dive](#seamless-sso--deep-dive)
- [Hybrid Identity — Device Management](#hybrid-identity--device-management)
- [Device Identity — Scenari e Configurazione](#device-identity--scenari-e-configurazione)
- [Conditional Access](#conditional-access)
- [Conditional Access — Componenti delle Policy](#conditional-access--componenti-delle-policy)
- [Conditional Access — Policy Comuni Essenziali](#conditional-access--policy-comuni-essenziali)
- [Conditional Access — Scenari Enterprise Avanzati](#conditional-access--scenari-enterprise-avanzati)
- [Multi-Factor Authentication](#multi-factor-authentication)
- [Metodi MFA — Dettaglio e Confronto](#metodi-mfa--dettaglio-e-confronto)
- [MFA — Deployment e Rollout Enterprise](#mfa--deployment-e-rollout-enterprise)
- [Identity Protection e Risk Policies](#identity-protection-e-risk-policies)
- [Identity Protection — Approfondimento](#identity-protection--approfondimento)
- [Azure AD Application Proxy](#azure-ad-application-proxy)
- [Privileged Identity Management (PIM)](#privileged-identity-management-pim)
- [PIM — Approfondimento Operativo](#pim--approfondimento-operativo)
- [Registrazione Applicazioni e OAuth 2.0](#registrazione-applicazioni-e-oauth-20)
- [B2B Collaboration e Cross-Tenant Access](#b2b-collaboration-e-cross-tenant-access)
- [Gestione con PowerShell — Microsoft.Graph](#gestione-con-powershell--microsoftgraph)
- [Monitoraggio Entra ID](#monitoraggio-entra-id)
- [Migrazione da AD FS ad Autenticazione Gestita](#migrazione-da-ad-fs-ad-autenticazione-gestita)
- [Automazione e Script Enterprise](#automazione-e-script-enterprise)
- [Scenari Reali Enterprise](#scenari-reali-enterprise)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Troubleshooting Avanzato — Guida Strutturata](#troubleshooting-avanzato--guida-strutturata)
- [FAQ](#faq)
- [Esercizi](#esercizi)
- [Auto-valutazione](#auto-valutazione)
- [Letture Primarie Consigliate](#letture-primarie-consigliate)
- [Collegamenti Incrociati](#collegamenti-incrociati)
- [Glossario Locale](#glossario-locale)

---

## Panoramica

Microsoft Entra ID (precedentemente Azure Active Directory) è il servizio di identità cloud di Microsoft. L'identità ibrida collega AD DS on-premise con Entra ID per consentire Single Sign-On su risorse cloud e on-premise. È il pilastro dell'infrastruttura moderna Microsoft: M365, Azure, e migliaia di app SaaS si autenticano tramite Entra ID.

---

## Mappa Concettuale

```
┌─────────────────────────────────────────────────────────────────────────────┐
│             RELAZIONE AD DS ON-PREM ↔ ENTRA CONNECT ↔ ENTRA ID            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────┐                                            │
│  │       AD DS ON-PREMISE       │                                            │
│  │                             │                                            │
│  │  Struttura gerarchica:      │                                            │
│  │    Forest                   │                                            │
│  │     └── Domain              │                                            │
│  │          ├── OU (Utenti)    │                                            │
│  │          ├── OU (Computer)  │                                            │
│  │          ├── OU (Gruppi)    │                                            │
│  │          └── OU (Servizi)   │                                            │
│  │                             │                                            │
│  │  Protocolli:                │                                            │
│  │    Kerberos, NTLM, LDAP    │                                            │
│  │                             │                                            │
│  │  Gestione:                  │                                            │
│  │    Group Policy (GPO)       │                                            │
│  │    SCCM / MECM              │                                            │
│  └──────────────┬──────────────┘                                            │
│                 │                                                           │
│                 │  ← Connessione outbound (HTTPS 443)                       │
│                 │  ← Ogni 30 min (delta sync) o su richiesta                │
│                 │                                                           │
│  ┌──────────────▼──────────────┐                                            │
│  │     MICROSOFT ENTRA CONNECT  │                                            │
│  │                             │                                            │
│  │  Motore di sync:            │                                            │
│  │    Import → Sync → Export   │                                            │
│  │                             │                                            │
│  │  Metodo autenticazione:     │                                            │
│  │    ┌─────────────────────┐  │                                            │
│  │    │ PHS  (hash sync)    │  │  ← Consigliato: resiliente, semplice      │
│  │    │ PTA  (pass-through) │  │  ← Nessun hash nel cloud                  │
│  │    │ FED  (AD FS)        │  │  ← Legacy, deprecato per nuovi deploy     │
│  │    └─────────────────────┘  │                                            │
│  │                             │                                            │
│  │  Filtering:                 │                                            │
│  │    OU / Domain / Attributo  │                                            │
│  │                             │                                            │
│  │  Features:                  │                                            │
│  │    Seamless SSO             │                                            │
│  │    Password Writeback       │                                            │
│  │    Device Writeback         │                                            │
│  │    Group Writeback          │                                            │
│  └──────────────┬──────────────┘                                            │
│                 │                                                           │
│                 │  ← Sync oggetti: Users, Groups, Contacts, Devices         │
│                 │  ← Hash password (se PHS abilitato)                       │
│                 │                                                           │
│  ┌──────────────▼──────────────┐                                            │
│  │      MICROSOFT ENTRA ID     │                                            │
│  │                             │                                            │
│  │  Struttura piatta:          │                                            │
│  │    Tenant                   │                                            │
│  │     ├── Users               │                                            │
│  │     ├── Groups              │                                            │
│  │     ├── Devices             │                                            │
│  │     ├── Applications        │                                            │
│  │     └── Admin Units (deleghe)│                                           │
│  │                             │                                            │
│  │  Protocolli:                │                                            │
│  │    OAuth 2.0, OIDC, SAML   │                                            │
│  │                             │                                            │
│  │  Gestione:                  │                                            │
│  │    Conditional Access       │                                            │
│  │    Intune (MDM/MAM)         │                                            │
│  │    Identity Protection      │                                            │
│  │    PIM (Just-In-Time)       │                                            │
│  │                             │                                            │
│  │  Risorse protette:          │                                            │
│  │    M365, Azure, SaaS, B2B   │                                            │
│  └─────────────────────────────┘                                            │
│                                                                             │
│  FLUSSO AUTENTICAZIONE (PHS):                                               │
│    Utente → Entra ID → verifica hash → token OAuth/OIDC → risorsa          │
│                                                                             │
│  FLUSSO AUTENTICAZIONE (PTA):                                               │
│    Utente → Entra ID → PTA Agent → AD DS → validazione → token → risorsa   │
│                                                                             │
│  FLUSSO AUTENTICAZIONE (Federation):                                        │
│    Utente → Entra ID → redirect AD FS → Kerberos/NTLM → token → risorsa   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Architettura Entra ID

```
┌──────────────────────────────────────────────────────────────┐
│                  ARCHITETTURA IDENTITÀ IBRIDA            │
├──────────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────┐     ┌─────────────────────┐    │
│  │   ON-PREMISE         │     │   CLOUD              │    │
│  │                     │     │                      │    │
│  │  Active Directory   │     │  Microsoft Entra ID  │    │
│  │  Domain Services    │     │  (Azure AD)          │    │
│  │                     │     │                      │    │
│  │  ┌──────────────┐   │     │  ┌──────────────┐    │    │
│  │  │ Users        │   │     │  │ Users (cloud) │    │    │
│  │  │ Groups       │───┼──→──│  │ Groups        │    │    │
│  │  │ Computers    │   │     │  │ Devices       │    │    │
│  │  └──────────────┘   │     │  └──────────────┘    │    │
│  │                     │     │                      │    │
│  │  ┌──────────────┐   │     │  ┌──────────────┐    │    │
│  │  │ Kerberos     │   │     │  │ OAuth 2.0     │    │    │
│  │  │ NTLM         │   │     │  │ OIDC          │    │    │
│  │  │ LDAP         │   │     │  │ SAML 2.0      │    │    │
│  │  └──────────────┘   │     │  └──────────────┘    │    │
│  │                     │     │                      │    │
│  │  GPO               │     │  Intune / CA         │    │
│  │  SCCM              │     │  Conditional Access  │    │
│  └──────────┬──────────┘     └──────────┬───────────┘    │
│             │                           │                │
│             │    ┌──────────────────┐    │                │
│             └────│  Entra Connect   │────┘                │
│                  │  (Sync Engine)   │                     │
│                  │  PHS / PTA / Fed │                     │
│                  └──────────────────┘                     │
│                                                          │
│  RISORSE PROTETTE:                                       │
│  ├── Microsoft 365 (Exchange, SharePoint, Teams)         │
│  ├── Azure Resources (VM, Storage, SQL, etc.)            │
│  ├── App SaaS (Salesforce, ServiceNow, Workday, etc.)    │
│  ├── App on-premise (via App Proxy)                      │
│  └── Custom apps (B2C / B2B)                             │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## Entra ID vs AD DS — Differenze Chiave

Active Directory Domain Services (AD DS) e Microsoft Entra ID sono servizi di identità fondamentalmente diversi. Non si tratta di "AD nel cloud": Entra ID è progettato per il paradigma cloud con protocolli moderni, mentre AD DS resta il pilastro della gestione on-premise. Comprendere le differenze è cruciale per progettare architetture ibride corrette.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     ENTRA ID vs AD DS — CONFRONTO APPROFONDITO          │
├───────────────────────┬────────────────────────┬─────────────────────────┤
│ Dimensione            │ AD DS (on-premise)     │ Entra ID (cloud)        │
├───────────────────────┼────────────────────────┼─────────────────────────┤
│ Struttura directory   │ Gerarchica (Forest →   │ Piatta (Tenant →        │
│                       │ Domain → OU → Oggetti) │ Oggetti diretti)        │
│                       │                        │                         │
│ Unità organizzative   │ OU (Organizational     │ Administrative Units    │
│                       │ Units) con GPO linkate │ (AU) — solo deleghe     │
│                       │                        │ admin, no policy linkate│
│                       │                        │                         │
│ Protocolli authn      │ Kerberos v5            │ OAuth 2.0               │
│                       │ NTLM (legacy)          │ OpenID Connect (OIDC)   │
│                       │ LDAP (bind)            │ SAML 2.0                │
│                       │                        │ WS-Federation           │
│                       │                        │                         │
│ Protocollo directory  │ LDAP (389/636)         │ Microsoft Graph API     │
│                       │                        │ (REST over HTTPS)       │
│                       │                        │                         │
│ Gestione policy       │ Group Policy (GPO)     │ Conditional Access      │
│                       │ SCCM / MECM            │ Intune (MDM/MAM)        │
│                       │                        │ Compliance Policies     │
│                       │                        │                         │
│ Trust model           │ Forest Trust, External │ B2B Collaboration       │
│                       │ Trust, Shortcut Trust  │ Cross-tenant access     │
│                       │ Realm Trust (Kerberos) │ settings                │
│                       │                        │                         │
│ Topologia             │ Sites e Subnet per     │ Distribuzione globale   │
│                       │ replica traffico       │ automatica (Microsoft   │
│                       │ Domain Controllers     │ gestisce infrastruttura)│
│                       │                        │                         │
│ Schema                │ Estensibile (attribute │ Extension attributes    │
│                       │ schema AD)             │ (15 standard + custom   │
│                       │                        │ via Graph)              │
│                       │                        │                         │
│ Ruoli infrastruttura  │ FSMO Roles (5):        │ N/A — servizio gestito  │
│                       │ PDC, RID, Schema,      │ (SLA 99.99%)            │
│                       │ Domain Naming,         │                         │
│                       │ Infrastructure         │                         │
│                       │                        │                         │
│ Autenticazione device │ Domain Join (Kerberos  │ Entra Join (PRT +       │
│                       │ computer account)      │ certificato device)     │
│                       │                        │                         │
│ MFA nativo            │ No (richiede ADFS +    │ Sì (integrato,          │
│                       │ MFA adapter esterno)   │ Conditional Access)     │
│                       │                        │                         │
│ Accesso condizionale  │ Network Location       │ Conditional Access:     │
│                       │ Awareness (NLA),       │ user, device, location, │
│                       │ IPsec, claim rules     │ risk, app, client app   │
│                       │ ADFS                   │                         │
│                       │                        │                         │
│ API management        │ ADSI, LDAP queries,    │ Microsoft Graph REST    │
│                       │ PowerShell AD module   │ PowerShell Microsoft.   │
│                       │                        │ Graph module            │
└───────────────────────┴────────────────────────┴─────────────────────────┘
```

Le Administrative Units (AU) in Entra ID sono spesso confuse con le OU di AD DS, ma hanno scopi diversi. Le OU servono a due funzioni: (1) organizzare oggetti e (2) applicare Group Policy tramite GPO link. Le AU in Entra ID servono esclusivamente per la delega amministrativa — cioè definire un perimetro entro cui un amministratore con ruolo scoped può operare. Non esiste un meccanismo di policy linkato alle AU. Le policy di gestione dei dispositivi sono gestite da Intune, e l'accesso è governato da Conditional Access, che opera a livello di tenant e non di AU.

Riferimento: https://learn.microsoft.com/entra/fundamentals/compare-with-active-directory (consultato: 2026-05-23)

---

## Edizioni Entra ID — Confronto Funzionalità

L'edizione di Entra ID determina quali funzionalità di sicurezza e gestione sono disponibili. La scelta dell'edizione influenza direttamente la postura di sicurezza del tenant.

### Licenze Entra ID — Confronto Dettagliato

```
┌──────────────────────┬───────────┬───────────┬───────────┬─────────────────┐
│ Feature              │ Free      │ P1        │ P2        │ Governance      │
├──────────────────────┼───────────┼───────────┼───────────┼─────────────────┤
│ User management      │ ✓         │ ✓         │ ✓         │ ✓               │
│ SSO (illimitato)     │ ✓         │ ✓         │ ✓         │ ✓               │
│ B2B collab           │ ✓         │ ✓         │ ✓         │ ✓               │
│ MFA (Security Def.)  │ ✓         │ ✓         │ ✓         │ ✓               │
│ Self-service pwd     │ cloud     │ writeback │ writeback │ writeback       │
│ Conditional Access   │ base      │ ✓ full    │ ✓ full    │ ✓ full          │
│ Dynamic Groups       │ ✗         │ ✓         │ ✓         │ ✓               │
│ App Proxy            │ ✗         │ ✓         │ ✓         │ ✓               │
│ Group naming policy  │ ✗         │ ✓         │ ✓         │ ✓               │
│ Password Protection  │ ✗         │ ✓         │ ✓         │ ✓               │
│ Sign-in risk CA      │ ✗         │ ✗         │ ✓         │ ✓               │
│ User risk CA         │ ✗         │ ✗         │ ✓         │ ✓               │
│ Identity Protection  │ ✗         │ ✗         │ ✓         │ ✓               │
│ PIM                  │ ✗         │ ✗         │ ✓         │ ✓               │
│ Access Reviews       │ ✗         │ ✗         │ ✓         │ ✓               │
│ Entitlement Mgmt     │ ✗         │ ✗         │ ✗         │ ✓               │
│ Lifecycle Workflows  │ ✗         │ ✗         │ ✗         │ ✓               │
│ Terms of Use         │ ✗         │ ✓         │ ✓         │ ✓               │
│ Risk-based CA        │ ✗         │ ✗         │ ✓         │ ✓               │
│ Verified ID          │ ✗         │ ✗         │ ✗         │ ✓               │
│ Workload Identities  │ ✗         │ P (add-on)│ P (add-on)│ P (add-on)      │
├──────────────────────┼───────────┼───────────┼───────────┼─────────────────┤
│ Incluso in:          │ M365 Free │ M365 E3   │ M365 E5   │ Entra ID        │
│                      │           │ EMS E3    │ EMS E5    │ Governance       │
│                      │           │           │           │ (add-on P2)     │
└──────────────────────┴───────────┴───────────┴───────────┴─────────────────┘
```

**Decisione pratica**: per un'organizzazione che vuole implementare Zero Trust, P1 è il minimo indispensabile (Conditional Access, gruppi dinamici, App Proxy). P2 aggiunge la dimensione risk-based (Identity Protection, PIM, Access Reviews) ed è necessario per qualsiasi organizzazione con dati regolamentati. Entra ID Governance aggiunge il lifecycle management e l'entitlement management per organizzazioni con processi HR complessi.

Riferimento: https://learn.microsoft.com/entra/fundamentals/whatis#licenses (consultato: 2026-05-23)

---

## Microsoft Entra ID (Azure AD)

### Concetti Fondamentali

```
Entra ID vs Active Directory DS:

AD DS (on-premise)              │  Entra ID (cloud)
────────────────────────────────│──────────────────────────────
LDAP                            │  REST API (Microsoft Graph)
Kerberos / NTLM                 │  OAuth 2.0 / OpenID Connect / SAML
Organizational Units            │  Flat structure (no OU)
Group Policy                    │  Intune / Conditional Access
Domains / Forests / Trust       │  Tenants
Sites / Replica                 │  Globally distributed
Schema extensible               │  Extension attributes
FSMO Roles                      │  N/A (managed service)
```

### Tipi di Join

```
1. Azure AD Registered (BYOD)
   → Device personale registrato per accesso risorse aziendali
   → L'utente aggiunge account aziendale in Settings
   → Device rimane personale, profilo di lavoro separato

2. Azure AD Joined (Cloud-only)
   → Device aziendale gestito interamente dal cloud
   → No dominio AD on-premise
   → Login con credenziali Azure AD
   → Gestito da Intune
   → Consigliato per nuovi device

3. Hybrid Azure AD Joined
   → Device nel dominio AD on-premise E registrato in Azure AD
   → Login con credenziali AD (sincronizzate)
   → SSO sia per risorse on-premise che cloud
   → Gestito da SCCM e/o Intune (co-management)
   → Per transizione graduale da AD a cloud
```

```powershell
# Verificare stato join
dsregcmd /status

# Output chiave:
# AzureAdJoined: YES/NO
# EnterpriseJoined: YES/NO (Hybrid)
# DomainJoined: YES/NO (AD on-premise)
# TenantId: GUID del tenant

# Licenze Entra ID:
# Free          → Gestione utenti base, SSO illimitato per app integrate
# P1            → Conditional Access, gruppi dinamici, self-service password reset, App Proxy
# P2            → Identity Protection, PIM (Privileged Identity Management), Access Reviews
```

---

## Entra ID — Gestione Avanzata Utenti e Gruppi

### Gruppi Dinamici

```powershell
# I gruppi dinamici aggiungono/rimuovono membri automaticamente
# basandosi su attributi dell'utente o del dispositivo
# Richiedono Entra ID P1

# Esempi di regole per gruppi dinamici:

# Tutti gli utenti del reparto IT
# (user.department -eq "IT")

# Tutti gli utenti con licenza E3
# (user.assignedPlans -any (assignedPlan.servicePlanId -eq "GUID-E3"))

# Tutti gli utenti con JobTitle che contiene "Manager"
# (user.jobTitle -contains "Manager")

# Tutti gli utenti della sede di Milano
# (user.city -eq "Milano") -and (user.accountEnabled -eq true)

# Tutti i dispositivi Windows (dynamic device group)
# (device.deviceOSType -eq "Windows") -and (device.accountEnabled -eq true)

# Tutti i dispositivi Windows 11
# (device.deviceOSType -eq "Windows") -and (device.deviceOSVersion -startsWith "10.0.22")

# ATTENZIONE: i gruppi dinamici possono impiegare 5-30 minuti
# per aggiornare la membership dopo una modifica di attributo

# Verificare lo stato di processing di un gruppo dinamico:
# Entra ID → Groups → [gruppo] → Dynamic membership rules
# → Processing status: mostra se la regola è in fase di valutazione

# Via Microsoft Graph PowerShell:
Connect-MgGraph -Scopes "Group.Read.All"
Get-MgGroup -Filter "displayName eq 'DYN-IT-Staff'" |
    Select-Object DisplayName, MembershipRule, MembershipRuleProcessingState
```

### Administrative Units

```powershell
# Le Administrative Units (AU) permettono di delegare la gestione
# a sottoinsiemi di utenti senza dare accesso globale

# Scenario: delegare la gestione degli utenti di Milano
# al team IT di Milano, senza che possano gestire utenti di Roma

# Creare Administrative Unit
Connect-MgGraph -Scopes "AdministrativeUnit.ReadWrite.All"
New-MgDirectoryAdministrativeUnit -DisplayName "AU-Milano" `
    -Description "Utenti e dispositivi sede Milano"

# Aggiungere membri all'AU
# (utenti, gruppi, dispositivi)
$au = Get-MgDirectoryAdministrativeUnit -Filter "displayName eq 'AU-Milano'"
New-MgDirectoryAdministrativeUnitMember -AdministrativeUnitId $au.Id `
    -DirectoryObjectId "<user-object-id>"

# Assegnare un ruolo amministrativo nell'AU
# Esempio: User Administrator scoped all'AU di Milano
New-MgRoleManagementDirectoryRoleAssignment `
    -DirectoryScopeId "/administrativeUnits/$($au.Id)" `
    -RoleDefinitionId "<user-admin-role-id>" `
    -PrincipalId "<admin-user-object-id>"

# Risultato: l'admin può gestire SOLO gli utenti nell'AU di Milano
```

---

## Azure AD Connect

### Installazione e Configurazione

```powershell
# Azure AD Connect sincronizza AD DS on-premise → Entra ID
# Installare su un server member del dominio (NON sul DC)

# Prerequisiti:
# - Windows Server 2016+ (consigliato 2022)
# - .NET Framework 4.7.2+
# - SQL Express (incluso) o SQL Server per > 100.000 oggetti
# - Account Global Administrator in Entra ID
# - Account Enterprise Administrator in AD DS
# - Connettività HTTPS verso *.microsoftonline.com, *.windows.net

# Metodi di sincronizzazione:
# 1. Password Hash Sync (PHS) — CONSIGLIATO
#    → Hash della password sincronizzato nel cloud
#    → L'utente usa la stessa password on-premise e cloud
#    → Funziona anche se AD on-premise è down
#    → Più semplice e resiliente

# 2. Pass-through Authentication (PTA)
#    → Password validata in tempo reale contro AD on-premise
#    → Nessun hash nel cloud
#    → Richiede agenti PTA installati on-premise
#    → Se AD è down, login cloud fallisce

# 3. Federation (AD FS)
#    → Autenticazione delegata a AD FS on-premise
#    → Più complesso, richiede infrastruttura AD FS
#    → Per scenari con autenticazione custom o smart card
#    → Sconsigliato per nuovi deploy (preferire PHS + Seamless SSO)
```

---

## Azure AD Connect — Prerequisiti di Installazione

L'installazione di Entra Connect richiede una preparazione accurata. Errori nella fase di prerequisiti sono la causa principale di problemi di sync nelle prime settimane.

```
┌────────────────────────────────────────────────────────────────────────────┐
│              PREREQUISITI INSTALLAZIONE — CHECKLIST COMPLETA              │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  SERVER:                                                                   │
│  ├── Windows Server 2016 o successivo (2022 consigliato)                   │
│  ├── Domain member, NON Domain Controller                                  │
│  ├── .NET Framework 4.7.2+ (4.8 consigliato)                              │
│  ├── TLS 1.2 abilitato (obbligatorio dal 2023)                            │
│  ├── PowerShell 5.1 (incluso in Server 2016+)                             │
│  ├── NO server con ruolo Web Application Proxy                             │
│  └── Minimo 4 GB RAM, 70 GB disco, 1.6 GHz CPU                           │
│                                                                            │
│  DATABASE:                                                                 │
│  ├── < 100.000 oggetti: SQL Express LocalDB (incluso, automatico)         │
│  ├── ≥ 100.000 oggetti: SQL Server full (2016+)                           │
│  └── SQL collation: Latin1_General_CI_AS                                   │
│                                                                            │
│  ACCOUNT:                                                                  │
│  ├── Entra ID: account Global Administrator (dedicato, non personale)      │
│  ├── AD DS: account Enterprise Administrator (per setup iniziale)          │
│  ├── AD Connector account: creato dal wizard o pre-creato con              │
│  │   permessi specifici per OU sincronizzate                               │
│  └── Service account: ADSync (creato automaticamente, GMSA consigliato)   │
│                                                                            │
│  RETE:                                                                     │
│  ├── Outbound HTTPS (443) verso:                                           │
│  │   ├── *.microsoftonline.com                                             │
│  │   ├── *.windows.net                                                     │
│  │   ├── *.msftconnecttest.com                                             │
│  │   ├── *.msappproxy.net                                                  │
│  │   └── *.servicebus.windows.net                                          │
│  ├── DNS: risoluzione pubblica funzionante                                 │
│  ├── NO proxy con SSL inspection sul traffico verso endpoints Microsoft    │
│  └── NO firewall stateful che interrompa long-lived connections            │
│                                                                            │
│  ACTIVE DIRECTORY:                                                         │
│  ├── UPN suffix routable (es. contoso.com, NON corp.local)                │
│  ├── Tutti gli utenti da sincronizzare devono avere UPN routable           │
│  ├── IdFix tool eseguito per correggere attributi problematici             │
│  ├── Schema AD aggiornato (verificare con ADPrep se necessario)            │
│  └── Recycle Bin AD abilitato (consigliato)                                │
│                                                                            │
│  ENTRA ID:                                                                 │
│  ├── Dominio custom verificato (es. contoso.com)                           │
│  ├── Licenza P1 minima per funzionalità complete                           │
│  └── Nessuna directory sync preesistente attiva (DirSync, AADSync)        │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

```powershell
# Verificare TLS 1.2 abilitato sul server:
[Net.ServicePointManager]::SecurityProtocol
# Deve includere Tls12

# Abilitare TLS 1.2 se mancante:
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\.NETFramework\v4.0.30319" `
    -Name "SchUseStrongCrypto" -Value 1 -Type DWord
Set-ItemProperty -Path "HKLM:\SOFTWARE\Wow6432Node\Microsoft\.NETFramework\v4.0.30319" `
    -Name "SchUseStrongCrypto" -Value 1 -Type DWord

# Verificare UPN suffix in AD:
Get-ADForest | Select-Object -ExpandProperty UPNSuffixes
# Se mancano suffix routable, aggiungerli:
# Active Directory Domains and Trusts → Properties → UPN Suffixes

# Verificare utenti con UPN non routable:
Get-ADUser -Filter {UserPrincipalName -like "*@corp.local"} |
    Select-Object Name, UserPrincipalName |
    Export-Csv "C:\Temp\users-non-routable-upn.csv" -NoTypeInformation

# Eseguire IdFix prima dell'installazione:
# Download: https://microsoft.github.io/idfix/
# Eseguire su un PC domain-joined, correggere tutti gli errori
```

Riferimento: https://learn.microsoft.com/entra/identity/hybrid/connect/how-to-connect-install-prerequisites (consultato: 2026-05-23)

---

## Azure AD Connect — Filtering Avanzato

Il filtering controlla quali oggetti AD DS vengono sincronizzati in Entra ID. Un filtering errato può causare la sincronizzazione di account di servizio, test accounts, o oggetti non necessari, aumentando il rischio e il rumore nei log.

```powershell
# ============================================================
# TIPI DI FILTERING
# ============================================================

# 1. DOMAIN FILTERING
# Selezionare quali domini di un multi-domain forest sincronizzare.
# Wizard → Customize synchronization options → Domain/OU filtering
# Es: in un forest con corp.contoso.com e test.contoso.com,
# sincronizzare solo corp.contoso.com

# 2. OU FILTERING (più comune)
# Selezionare quali OU sincronizzare.
# Wizard → Customize synchronization options → Domain/OU filtering
# Espandere il dominio → selezionare/deselezionare OU
#
# Regola pratica:
# ✓ Sincronizzare: OU con utenti, gruppi operativi, contatti
# ✗ NON sincronizzare: OU di test, OU di service accounts interni,
#   OU di computer (a meno che non serva Hybrid Join),
#   OU di default "Users" e "Computers" (se usati come catch-all)

# 3. GROUP-BASED FILTERING (pilota)
# Sincronizzare solo i membri di un gruppo AD specifico.
# Utile per pilot deployment — sincronizzare 50-100 utenti per test.
# Wizard → Express Settings → Group-based filtering
# Limitazione: solo per pilot, non per produzione permanente.

# 4. ATTRIBUTE-BASED FILTERING
# Regole personalizzate basate su attributi AD.
# Configurare nel Synchronization Rules Editor.

# ============================================================
# ATTRIBUTE-BASED FILTERING — ESEMPI
# ============================================================

# Aprire Synchronization Rules Editor:
# Start → Synchronization Rules Editor

# Creare una regola "Inbound" per escludere oggetti:
# Direction: Inbound
# Precedence: (numero basso = priorità alta)
# Connected System: il connector AD
# Scoping Filter:
#   Attribute: department
#   Operator: EQUAL
#   Value: "Test"
# → Transformation: cloudFiltered = True (esclude l'oggetto dal sync)

# Esempio in PowerShell (post-configurazione, verifica):
Get-ADSyncRule | Where-Object {
    $_.Name -like "*Custom*" -and $_.Direction -eq "Inbound"
} | Select-Object Name, Precedence, Description

# ============================================================
# FILTERING PER ATTRIBUTO extensionAttribute
# ============================================================

# Pattern comune: usare extensionAttribute15 come flag di sync.
# In AD, impostare extensionAttribute15 = "SyncToCloud" sugli utenti
# da sincronizzare. Nel Sync Rules Editor, creare una regola:
#   Scoping: extensionAttribute15 NOT EQUAL "SyncToCloud"
#   → cloudFiltered = True (esclude chi non ha il flag)

# Impostare il flag in AD:
Set-ADUser -Identity "mrossi" -Replace @{extensionAttribute15 = "SyncToCloud"}

# Verificare utenti con il flag:
Get-ADUser -Filter {extensionAttribute15 -eq "SyncToCloud"} -Properties extensionAttribute15 |
    Select-Object Name, UserPrincipalName, extensionAttribute15
```

Riferimento: https://learn.microsoft.com/entra/identity/hybrid/connect/how-to-connect-sync-configure-filtering (consultato: 2026-05-23)

---

## Azure AD Connect — Sync Rules e Trasformazioni

Le Synchronization Rules governano come gli attributi vengono trasformati durante il flusso dallo spazio connettore AD verso il Metaverse e poi verso lo spazio connettore Entra ID.

```powershell
# ============================================================
# ARCHITETTURA DEL SYNC ENGINE
# ============================================================
#
# Il flusso di sync avviene in tre fasi:
#
# AD DS Connector Space → Metaverse → Entra ID Connector Space
#       (Import)              (Sync)           (Export)
#
# Connector Space: rappresentazione locale degli oggetti dal sistema connesso
# Metaverse: rappresentazione unificata degli oggetti da tutti i connettori
# Sync Rules: definiscono come gli attributi fluiscono tra le fasi

# ============================================================
# TIPI DI SYNC RULES
# ============================================================
#
# INBOUND: dal Connector Space AD verso il Metaverse
#   → Mappano attributi AD a attributi Metaverse
#   → Applicano trasformazioni (es. uppercase, concatenazione)
#
# OUTBOUND: dal Metaverse verso il Connector Space Entra ID
#   → Mappano attributi Metaverse a attributi Entra ID
#   → Definiscono quali attributi vengono esportati

# Visualizzare tutte le sync rules:
Get-ADSyncRule | Select-Object Name, Direction, Precedence, Disabled |
    Sort-Object Precedence | Format-Table -AutoSize

# ============================================================
# TRASFORMAZIONI COMUNI
# ============================================================

# 1. Generare userPrincipalName da attributi AD
# Expression: IIF(IsPresent([mail]), [mail], 
#             IIF(IsPresent([userPrincipalName]), [userPrincipalName],
#             Error("No UPN or mail")))

# 2. Concatenare firstName + lastName per displayName
# Expression: Join(" ", Trim([givenName]), Trim([sn]))

# 3. Generare proxyAddress da mail
# Expression: IIF(IsPresent([mail]), 
#             Join("", "SMTP:", [mail]), Null)

# 4. Mapping da estensionAttribute a Custom Security Attribute
# Usare regole outbound per mappare extensionAttribute1-15
# a attributi custom in Entra ID

# ============================================================
# TROUBLESHOOTING SYNC RULES
# ============================================================

# Verifica Preview di un oggetto (dry-run della sync):
# Synchronization Service Manager → Operations → selezionare un run
# → Connectors → cercare l'oggetto → Preview
# Il Preview mostra COSA succederebbe durante la sync, senza applicare

# Export errori specifici:
$errors = Get-ADSyncRunStepResult | Where-Object { $_.StepResult -ne "success" }
$errors | ForEach-Object {
    Write-Host "Connector: $($_.ConnectorName) | Step: $($_.RunProfileName) | Result: $($_.StepResult)"
}
```

Riferimento: https://learn.microsoft.com/entra/identity/hybrid/connect/concept-azure-ad-connect-sync-default-rules (consultato: 2026-05-23)

---

### Configurazione Sync

```powershell
# Dopo installazione wizard, il servizio ADSync gira come servizio Windows

# Verificare stato sync
Get-ADSyncScheduler
# Output: SyncCycleEnabled, NextSyncCycleStartTimeInUTC (default ogni 30 min)

# Forzare sync manuale
Start-ADSyncSyncCycle -PolicyType Delta    # Solo modifiche
Start-ADSyncSyncCycle -PolicyType Initial  # Sync completo (usare con cautela)

# Verificare errori sync
Get-ADSyncRunStepResult

# Filtering — sincronizzare solo OU specifiche:
# Wizard → Customize synchronization options → Domain/OU filtering
# Es: sincronizzare solo OU=Utenti e OU=Gruppi, escludere OU=Test

# Filtering per attributo:
# Sync Rules Editor → Creare regola con condizione
# Es: sincronizzare solo utenti con attribute department != "Test"

# Attribute mapping:
# Entra ID Connect gestisce il mapping automatico:
# sAMAccountName → onPremisesSamAccountName
# userPrincipalName → userPrincipalName
# mail → mail
# displayName → displayName

# UPN Suffix: assicurarsi che il dominio UPN sia un dominio verificato in Entra ID
# Se AD usa "corp.contoso.com" ma Entra ID ha "contoso.com":
# Aggiungere "contoso.com" come UPN suffix in AD e assegnare agli utenti
```

### Azure AD Connect Cloud Sync

```powershell
# Alternativa moderna ad Azure AD Connect (agent-based)
# Più leggero, gestito interamente dal cloud, multi-forest
# Installare agent su server member:
# AzureADConnectProvisioningAgentSetup.exe

# Configurazione interamente da portale Azure:
# Entra ID → Azure AD Connect → Cloud Sync
# Vantaggi: no server dedicato, failover automatico, gestione cloud
# Limitazioni: meno opzioni di filtering e transformazione rispetto al classico
```

### Confronto: Azure AD Connect vs Cloud Sync

```
┌──────────────────────┬───────────────────┬───────────────────┐
│ Feature              │ Azure AD Connect  │ Cloud Sync        │
├──────────────────────┼───────────────────┼───────────────────┤
│ Installazione        │ Server dedicato   │ Agent leggero     │
│ Multi-forest         │ Sì (complesso)    │ Sì (semplice)     │
│ Filtering (OU)       │ ✓ avanzato        │ ✓ base            │
│ Filtering (attributo)│ ✓ regole custom   │ ✓ limitato        │
│ Writeback password   │ ✓                 │ ✓                 │
│ Writeback gruppi     │ ✓                 │ ✗                 │
│ Writeback dispositivi│ ✓                 │ ✗                 │
│ Exchange Hybrid      │ ✓ completo        │ ✓ base            │
│ PHS                  │ ✓                 │ ✓                 │
│ PTA                  │ ✓                 │ ✗                 │
│ Federation (ADFS)    │ ✓                 │ ✗                 │
│ > 150.000 oggetti    │ ✓ (SQL Server)    │ ✓                 │
│ HA / Failover        │ Staging server    │ Multi-agent       │
│ Gestione             │ Wizard locale     │ Portale Azure     │
│ Consigliato per:     │ Scenari complessi │ Nuovi deploy      │
└──────────────────────┴───────────────────┴───────────────────┘
```

---

## Azure AD Connect — Troubleshooting Sync

```powershell
# ============================================================
# DIAGNOSTICA SYNC — GUIDA PASSO PASSO
# ============================================================

# 1. Verificare stato del servizio
Get-Service ADSync | Select-Object Name, Status, StartType
# Se non è Running: Start-Service ADSync

# 2. Verificare scheduler
Get-ADSyncScheduler
# AllowedSyncCycleInterval: 00:30:00 (default)
# SyncCycleEnabled: True
# NextSyncCycleStartTimeInUTC: prossimo sync

# 3. Verificare ultimo sync
Get-ADSyncConnectorRunStatus
# Mostra lo stato dell'ultimo run

# 4. Esportare errori di sync
$errors = Get-ADSyncRunProfileResult | Where-Object Result -ne "success" |
    Select-Object -First 20
$errors | Format-Table ConnectorName, RunProfileName, Result, StartDate

# 5. Verificare errori specifici su un oggetto
$userDN = "CN=Mario Rossi,OU=Utenti,DC=corp,DC=contoso,DC=com"
Get-ADSyncCSObject -DistinguishedName $userDN -ConnectorName "corp.contoso.com"

# ============================================================
# ERRORI COMUNI E SOLUZIONI
# ============================================================

# Errore: "InvalidSoftMatch"
# → L'oggetto cloud non corrisponde all'oggetto on-premise
# → Fix: verificare proxyAddresses e UPN corrispondano
#   Set-ADUser mrossi -UserPrincipalName "mrossi@contoso.com"

# Errore: "AttributeValueMustBeUnique"
# → Due utenti hanno lo stesso proxyAddress o UPN
# → Fix: trovare il duplicato:
Get-ADUser -Filter * -Properties ProxyAddresses |
    Where-Object { $_.ProxyAddresses -contains "SMTP:duplicate@contoso.com" }

# Errore: "LargeObject"
# → Un attributo supera il limite di dimensione (es. photo > 100KB)
# → Fix: ridurre la dimensione dell'attributo

# Errore: "DataValidationFailed"
# → Caratteri non validi in attributi (es. mail con spazi)
# → Fix: pulire gli attributi con IdFix tool

# ============================================================
# IDFIX — CORREZIONE ATTRIBUTI PRIMA DEL SYNC
# ============================================================

# IdFix è un tool Microsoft per trovare e correggere errori negli attributi AD
# prima di sincronizzare con Entra ID

# Download: microsoft.com/download/details.aspx?id=36832
# Eseguire su un PC domain-joined

# Errori comuni trovati da IdFix:
# - UPN non routable (user@corp.local invece di user@contoso.com)
# - Caratteri non validi in displayName
# - ProxyAddresses duplicate
# - Mail format non valido
# - Spazi trailing in attributi
```

---

## Metodi di Autenticazione — Confronto Dettagliato

La scelta del metodo di autenticazione è la decisione architetturale più importante nella progettazione dell'identità ibrida. Ogni metodo ha implicazioni su resilienza, sicurezza e complessità operativa.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│           CONFRONTO METODI DI AUTENTICAZIONE IBRIDA                         │
├──────────────┬──────────────────┬──────────────────┬────────────────────────┤
│              │ PHS              │ PTA              │ Federation (AD FS)     │
│              │ Password Hash    │ Pass-through     │                        │
│              │ Sync             │ Authentication   │                        │
├──────────────┼──────────────────┼──────────────────┼────────────────────────┤
│ Funzionamento│ Hash della pwd   │ Pwd validata in  │ Autenticazione         │
│              │ sincronizzato    │ real-time contro │ delegata a AD FS       │
│              │ ogni 2 minuti    │ AD on-prem via   │ on-premise             │
│              │ nel cloud        │ agent leggero    │                        │
│              │                  │                  │                        │
│ Hash nel     │ Sì (hash di      │ No               │ No                     │
│ cloud?       │ hash, non pwd    │                  │                        │
│              │ in chiaro)       │                  │                        │
│              │                  │                  │                        │
│ Resilienza   │ Alta: funziona   │ Media: dipende   │ Bassa: dipende da      │
│              │ anche se AD      │ da almeno 1      │ infrastruttura ADFS    │
│              │ on-prem è down   │ agent PTA        │ (2+ server + WAP)      │
│              │                  │ raggiungibile    │                        │
│              │                  │                  │                        │
│ Infrastruttura│ Solo Entra      │ Entra Connect +  │ Entra Connect + ADFS   │
│ richiesta    │ Connect          │ 3+ PTA agents    │ farm (2 ADFS + 2 WAP)  │
│              │                  │ (su server AD)   │                        │
│              │                  │                  │                        │
│ Complessità  │ Bassa            │ Media            │ Alta                   │
│ operativa    │                  │                  │                        │
│              │                  │                  │                        │
│ Latenza      │ Nessuna (hash    │ Dipendente da    │ Dipendente da ADFS     │
│ autenticaz.  │ verificato in    │ latenza rete     │ e rete                 │
│              │ cloud)           │ verso agent      │                        │
│              │                  │                  │                        │
│ Policy pwd   │ Entra ID pwd     │ AD DS password   │ AD DS password policy  │
│ applicate    │ policy (cloud)   │ policy (on-prem) │ + claim rules ADFS     │
│              │ + AD DS (on-prem)│                  │                        │
│              │                  │                  │                        │
│ Account      │ Bloccato sia in  │ Bloccato solo se │ Bloccato solo se AD    │
│ lockout      │ AD che in Entra  │ AD lo blocca     │ lo blocca              │
│              │ (Smart Lockout)  │                  │                        │
│              │                  │                  │                        │
│ Leaked creds │ Sì (Identity     │ No               │ No                     │
│ detection    │ Protection)      │                  │                        │
│              │                  │                  │                        │
│ Smart card / │ No nativo (serve │ No               │ Sì (caso d'uso         │
│ certificate  │ Windows Hello)   │                  │ principale di ADFS)    │
│              │                  │                  │                        │
│ Seamless SSO │ Sì (configurare  │ Sì (configurare  │ Non necessario (ADFS   │
│              │ in Entra Connect)│ in Entra Connect)│ gestisce SSO)          │
│              │                  │                  │                        │
│ CONSIGLIATO  │ Sì — default per │ Solo se vincolo  │ Solo per smart card,   │
│              │ nuovi deploy     │ normativo vieta  │ certificati, claim     │
│              │                  │ hash nel cloud   │ rules complesse        │
├──────────────┼──────────────────┼──────────────────┼────────────────────────┤
│ Microsoft    │ CONSIGLIATO      │ Alternativa      │ DEPRECATO per nuovi    │
│ raccomanda   │                  │ accettabile      │ deploy                 │
└──────────────┴──────────────────┴──────────────────┴────────────────────────┘
```

**Nota su PHS e sicurezza**: l'hash sincronizzato nel cloud non è la password in chiaro e non è nemmeno l'hash NTLM diretto. Entra Connect calcola un hash dell'hash MD4 della password usando SHA-256 + salt, trasmesso su canale TLS. Questo hash non può essere usato per autenticarsi direttamente su sistemi on-premise. Identity Protection utilizza questo hash per confrontarlo con database di credenziali compromesse note (es. data breach pubblici), fornendo una funzionalità di sicurezza aggiuntiva non disponibile con PTA o Federation.

Riferimento: https://learn.microsoft.com/entra/identity/hybrid/connect/how-to-connect-password-hash-synchronization (consultato: 2026-05-23)

---

## Hybrid Identity

### Seamless SSO

```powershell
# Seamless SSO permette login automatico alle risorse cloud
# da dispositivi domain-joined nella rete aziendale (senza prompt password)

# Requisiti: Azure AD Connect con PHS o PTA + Seamless SSO abilitato
# Funziona con: Kerberos ticket del computer → Azure AD token

# Abilitare nel wizard Azure AD Connect:
# → User sign-in → Enable single sign-on

# GPO necessaria sui client:
# User → Administrative Templates → Windows Components → Internet Explorer
#   → Internet Control Panel → Security Page → Intranet Zone
#     → Site to Zone Assignment: https://autologon.microsoftonline.com → Zone 1
# User → Administrative Templates → Windows Components → Internet Explorer
#   → Internet Control Panel → Security Page → Intranet Zone
#     → Allow updates to status bar via script: Enabled

# Oppure via registry:
Set-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings\ZoneMap\Domains\microsoftonline.com\autologon" `
    -Name "https" -Value 1 -Type DWord
```

---

## Seamless SSO — Deep Dive

Seamless SSO è il meccanismo che consente agli utenti di accedere alle risorse cloud senza inserire credenziali, sfruttando il ticket Kerberos ottenuto al login Windows. Comprendere il flusso interno è essenziale per il troubleshooting.

### Come Funziona — Flusso Kerberos

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  FLUSSO SEAMLESS SSO — PASSO PER PASSO                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. L'utente apre il browser e accede a una risorsa M365               │
│     (es. https://outlook.office365.com)                                │
│                                                                         │
│  2. Entra ID rileva il dominio federated/managed e reindirizza          │
│     a https://autologon.microsoftonline.com                             │
│                                                                         │
│  3. Il browser (nella Intranet Zone) invia un Kerberos service ticket  │
│     per il SPN "AZUREADSSOACC" automaticamente, senza prompt            │
│                                                                         │
│  4. Il ticket è crittato con la chiave dell'account computer            │
│     AZUREADSSOACC$ creato in AD durante la configurazione               │
│     di Seamless SSO nel wizard Entra Connect                            │
│                                                                         │
│  5. Entra ID decrittografa il ticket con la stessa chiave condivisa    │
│     (sincronizzata durante il setup), verifica l'identità dell'utente   │
│                                                                         │
│  6. Entra ID emette un token OAuth 2.0 / OIDC per l'utente             │
│     senza che l'utente abbia inserito username o password               │
│                                                                         │
│  Risultato: SSO trasparente per l'utente nella rete aziendale          │
│                                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────────┐    ┌────────────┐    │
│  │ Client   │───>│ Browser  │───>│ autologon.   │───>│ Entra ID   │    │
│  │ domain-  │    │ Intranet │    │ microsofton  │    │ verifica   │    │
│  │ joined   │    │ Zone     │    │ line.com     │    │ Kerberos   │    │
│  │          │    │ Kerberos │    │ (SPN:        │    │ ticket →   │    │
│  │          │    │ ticket   │    │ AZUREADSSOACC│    │ OAuth token│    │
│  └──────────┘    └──────────┘    └──────────────┘    └────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Configurazione Completa Seamless SSO

```powershell
# ============================================================
# PREREQUISITI
# ============================================================
# - PHS o PTA come metodo di autenticazione
# - Client Windows domain-joined
# - Browser: IE, Edge (legacy), Edge Chromium, Chrome, Firefox
# - Client nella rete aziendale (raggiunge il DC per Kerberos)

# ============================================================
# STEP 1: Abilitare nel wizard Entra Connect
# ============================================================
# Eseguire il wizard Entra Connect → Change user sign-in
# → Selezionare "Enable single sign-on"
# Inserire credenziali Domain Admin
# Il wizard crea l'account computer AZUREADSSOACC$ in AD

# ============================================================
# STEP 2: Configurare GPO per i browser
# ============================================================

# Per Internet Explorer e Edge Legacy:
# GPO: User → Administrative Templates → Windows Components →
#   Internet Explorer → Internet Control Panel → Security Page
#   → Site to Zone Assignment List: Enabled
#   → Aggiungere: https://autologon.microsoftonline.com = 1 (Intranet)
#   → Aggiungere: https://aadg.windows.net.nsatc.net = 1 (Intranet)

# Per Chrome (via registry o GPO):
# HKCU\Software\Policies\Google\Chrome\AuthServerAllowlist
# Valore: https://autologon.microsoftonline.com

# Per Firefox:
# about:config → network.negotiate-auth.trusted-uris
# Valore: https://autologon.microsoftonline.com

# ============================================================
# STEP 3: Verificare funzionamento
# ============================================================

# Sul client domain-joined, verificare il ticket Kerberos:
klist
# Deve mostrare un ticket per: HTTP/autologon.microsoftonline.com

# Verificare l'account AZUREADSSOACC$ in AD:
Get-ADComputer -Identity "AZUREADSSOACC" -Properties PasswordLastSet
# PasswordLastSet: deve essere recente (chiave Kerberos va ruotata ogni 30 giorni)

# ============================================================
# KEY ROLLOVER (IMPORTANTE)
# ============================================================
# La chiave Kerberos dell'account AZUREADSSOACC$ dovrebbe essere
# ruotata ogni 30 giorni per sicurezza.
# Entra Connect non lo fa automaticamente.

# Ruotare manualmente:
Update-AzureADSSOForest -OnPremCredentials $creds -PreserveCustomPermissionsOnDesktopSsoAccount

# ============================================================
# TROUBLESHOOTING SEAMLESS SSO
# ============================================================

# Problema: SSO non funziona da Edge Chromium
# → Edge Chromium usa PRT (Primary Refresh Token) per SSO, non Kerberos
# → Se il device è Azure AD Joined o Hybrid Joined, il PRT fornisce SSO
# → Seamless SSO Kerberos è fallback per device solo domain-joined

# Problema: SSO funziona per alcuni utenti, non per altri
# → Verificare GPO applicata: gpresult /r
# → Verificare Intranet Zone: reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Internet Settings\ZoneMap\Domains\microsoftonline.com\autologon"
# → Verificare ticket: klist (deve mostrare ticket per autologon.microsoftonline.com)

# Problema: prompt password su VPN
# → VPN split-tunnel: il traffico verso autologon.microsoftonline.com
#   deve passare attraverso il tunnel per raggiungere il DC
# → Alternativa: se il device è Hybrid Joined, usare PRT (non dipende da Kerberos)
```

Riferimento: https://learn.microsoft.com/entra/identity/hybrid/connect/how-to-connect-sso-how-it-works (consultato: 2026-05-23)

---

### Password Writeback

```powershell
# Permette agli utenti di cambiare o resettare la password nel cloud
# e la modifica viene scritta nell'AD on-premise

# Abilitare nel wizard Azure AD Connect:
# → Optional features → Password writeback

# Prerequisiti:
# - Azure AD Premium P1 o P2
# - Account AD Connect con permessi: Reset Password, Change Password
#   sulle OU sincronizzate

# Self-Service Password Reset (SSPR):
# Entra ID → Password reset → Properties
# - Enabled: All users
# - Authentication methods: 2 methods required
#   (Phone, Email, Security Questions, Microsoft Authenticator)
# - Registration: Require users to register at sign-in

# L'utente accede a https://aka.ms/sspr per resettare autonomamente
```

---

## Hybrid Identity — Device Management

### Hybrid Azure AD Join — Configurazione Completa

```powershell
# Hybrid Azure AD Join registra i dispositivi domain-joined
# sia in AD on-premise che in Entra ID

# ============================================================
# PREREQUISITI
# ============================================================
# - Azure AD Connect configurato con Device writeback
# - SCP (Service Connection Point) configurato in AD
# - DNS: i client devono risolvere enterpriseregistration.windows.net
# - Proxy: i client devono raggiungere *.microsoftonline.com

# Verificare SCP in AD:
$scp = Get-ADObject -Filter 'Name -eq "62a0ff2e-97b9-4513-943f-0d221bd30080"' `
    -SearchBase "CN=Configuration,DC=corp,DC=contoso,DC=com" -Properties keywords
$scp.keywords
# Deve contenere: azureADName:<tenant>.onmicrosoft.com
#                 azureADId:<tenant-id>

# ============================================================
# CONFIGURAZIONE IN AZURE AD CONNECT
# ============================================================
# Wizard → Configure device options → Configure Hybrid Azure AD join
# Selezionare: Windows 10+ devices
# Verificare SCP configuration
# Completare il wizard

# ============================================================
# GPO PER I CLIENT
# ============================================================

# Computer → Administrative Templates → Windows Components →
#   Device Registration
# → Register domain joined computers as devices: Enabled

# Il processo Hybrid Join avviene automaticamente:
# 1. Il client legge il SCP da AD
# 2. Il client contatta Entra ID
# 3. Il client riceve un certificato device
# 4. Il device appare in Entra ID → Devices
# 5. Il Primary Refresh Token (PRT) viene emesso

# Verificare stato join sul client:
dsregcmd /status
# AzureAdJoined: YES
# DomainJoined: YES
# → Hybrid Azure AD Joined confermato

# Diagnosticare problemi join:
dsregcmd /status /debug
# Verificare: TenantId, DeviceId, SSO State, PRT

# Verificare PRT (Primary Refresh Token):
dsregcmd /status | findstr "PRT"
# AzureAdPrt: YES → il token SSO è attivo
# AzureAdPrtUpdateTime: timestamp dell'ultimo rinnovo
```

### Co-Management SCCM + Intune

```powershell
# Co-Management permette di gestire i dispositivi con SCCM E Intune
# Graduale: spostare workload da SCCM a Intune uno alla volta

# Workload che possono essere gestiti da Intune:
# - Compliance Policies
# - Device Configuration
# - Windows Update Policies
# - Endpoint Protection
# - Resource Access Policies (Wi-Fi, VPN, Email, Certificates)
# - Client Apps
# - Office Click-to-Run Apps

# Configurazione:
# SCCM Console → Administration → Cloud Services → Co-management
# → Enable co-management
# → Automatic enrollment in Intune: Pilot (gruppo) o All

# Per ogni workload, scegliere:
# - SCCM: gestito on-premise
# - Pilot Intune: gestito da Intune solo per il gruppo pilota
# - Intune: gestito da Intune per tutti

# Monitorare:
# SCCM Console → Monitoring → Co-management
# → Dashboard con stato enrollment e workload per dispositivo
```

---

## Device Identity — Scenari e Configurazione

La scelta del tipo di device identity dipende dallo scenario organizzativo. Ogni tipo ha implicazioni diverse su gestione, SSO e sicurezza.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│              DEVICE IDENTITY — QUANDO USARE COSA                            │
├──────────────────┬──────────────────┬──────────────────┬─────────────────────┤
│                  │ Entra Registered │ Entra Joined     │ Hybrid Entra Joined │
├──────────────────┼──────────────────┼──────────────────┼─────────────────────┤
│ Scenario         │ BYOD, device     │ Cloud-first,     │ Transizione da AD   │
│                  │ personali        │ nuovi dispositivi│ on-prem a cloud     │
│                  │                  │ senza AD on-prem │                     │
│                  │                  │                  │                     │
│ Ownership        │ Personale        │ Aziendale        │ Aziendale           │
│                  │                  │                  │                     │
│ AD DS on-prem    │ Non richiesto    │ Non richiesto    │ Richiesto (domain   │
│                  │                  │                  │ join)               │
│                  │                  │                  │                     │
│ Entra ID join    │ Registrazione    │ Join diretto     │ Domain join AD +    │
│                  │ account lavoro   │ a Entra ID       │ registrazione Entra │
│                  │                  │                  │                     │
│ Login Windows    │ Account locale   │ Credenziali      │ Credenziali AD      │
│                  │ o Microsoft      │ Entra ID         │ (sincronizzate)     │
│                  │                  │                  │                     │
│ Gestione         │ Intune MAM       │ Intune MDM       │ SCCM e/o Intune    │
│                  │ (app-level)      │ (device-level)   │ (co-management)     │
│                  │                  │                  │                     │
│ SSO cloud        │ Limitato (per    │ PRT (completo)   │ PRT + Kerberos      │
│                  │ app configurate) │                  │ (on-prem e cloud)   │
│                  │                  │                  │                     │
│ SSO on-prem      │ No               │ No (solo con     │ Sì (Kerberos nativo)│
│                  │                  │ Windows Hello    │                     │
│                  │                  │ cloud trust)     │                     │
│                  │                  │                  │                     │
│ GPO              │ No               │ No (Intune)      │ Sì (AD GPO)         │
│                  │                  │                  │                     │
│ BitLocker key    │ Non gestita      │ Auto-backup in   │ AD DS e/o Entra ID  │
│ backup           │                  │ Entra ID         │                     │
│                  │                  │                  │                     │
│ Conditional      │ Limitato (device │ Completo         │ Completo            │
│ Access device    │ non compliance)  │ (compliant,      │ (compliant, hybrid  │
│ grant            │                  │ Entra joined)    │ joined required)    │
│                  │                  │                  │                     │
│ Consigliato per  │ Dipendenti con   │ Startup, PMI     │ Enterprise con AD   │
│                  │ device personali,│ cloud-native,    │ esistente,          │
│                  │ contractor,      │ remote workers   │ transizione         │
│                  │ studenti         │ senza AD on-prem │ graduale al cloud   │
├──────────────────┼──────────────────┼──────────────────┼─────────────────────┤
│ CONFIGURAZIONE   │ Settings →       │ Settings →       │ GPO + Entra Connect │
│                  │ Accounts →       │ Accounts →       │ + SCP in AD         │
│                  │ Access work/     │ Access work/     │ (automatico dopo    │
│                  │ school → Connect │ school → Join    │ domain join)        │
│                  │                  │ this device to   │                     │
│                  │                  │ Azure AD         │                     │
└──────────────────┴──────────────────┴──────────────────┴─────────────────────┘
```

```powershell
# ============================================================
# CONFIGURAZIONE ENTRA JOINED (CLOUD-ONLY)
# ============================================================

# Durante OOBE (Out-of-Box Experience) di Windows:
# → "How would you like to set up?" → "Set up for work or school"
# → Inserire credenziali Entra ID → il device si registra automaticamente
# → Intune enrollment avviene contemporaneamente (se configurato)

# Dopo il setup iniziale:
# Settings → Accounts → Access work or school → Connect
# → Selezionare "Join this device to Azure Active Directory"
# → Inserire credenziali → Confermare

# Verificare su Entra ID (portale):
# Entra ID → Devices → All devices
# Join Type: Azure AD joined
# MDM: Microsoft Intune (se enrollment automatico)

# ============================================================
# STALE DEVICE CLEANUP
# ============================================================

# I device che non si connettono da molto tempo (90+ giorni)
# dovrebbero essere disabilitati o rimossi per pulizia.

Connect-MgGraph -Scopes "Device.ReadWrite.All"
$staleDate = (Get-Date).AddDays(-90).ToString("yyyy-MM-ddTHH:mm:ssZ")
$staleDevices = Get-MgDevice -Filter "approximateLastSignInDateTime le $staleDate" -All
$staleDevices | Select-Object DisplayName, OperatingSystem, ApproximateLastSignInDateTime |
    Export-Csv "C:\Temp\stale-devices.csv" -NoTypeInformation
Write-Host "Dispositivi non attivi da 90+ giorni: $($staleDevices.Count)"
```

Riferimento: https://learn.microsoft.com/entra/identity/devices/concept-device-registration (consultato: 2026-05-23)

---

## Conditional Access

```powershell
# Conditional Access è il motore Zero Trust di Entra ID:
# IF (condizioni) THEN (grant/block con controlli)

# Componenti di una policy:
# ASSIGNMENTS (chi e cosa):
#   → Users/Groups: tutti, gruppi specifici, guest
#   → Cloud apps: Office 365, app specifiche, tutte
#   → Conditions:
#       → Sign-in risk (richiede Entra ID P2)
#       → Device platform (Windows, iOS, Android)
#       → Location (IP range, named locations)
#       → Client app (browser, mobile, desktop, legacy auth)

# ACCESS CONTROLS (cosa fare):
#   → Grant: MFA required, compliant device required, hybrid joined required
#   → Block: blocca accesso
#   → Session: limited access, sign-in frequency, app enforced restrictions

# POLICY COMUNI:

# 1. Richiedere MFA per tutti gli utenti su tutte le app
# Assignments: All users (escludere break-glass accounts!)
# Cloud apps: All cloud apps
# Grant: Require MFA

# 2. Bloccare legacy authentication
# Assignments: All users
# Conditions: Client apps → Other clients (Exchange ActiveSync, other)
# Grant: Block

# 3. Richiedere device compliant per accesso a Office 365
# Assignments: All users
# Cloud apps: Office 365
# Grant: Require device to be marked as compliant

# 4. Richiedere MFA da reti non aziendali
# Assignments: All users
# Conditions: Locations → Exclude trusted locations
# Grant: Require MFA

# 5. Bloccare accesso da paesi non autorizzati
# Conditions: Locations → Include selected → "Blocked Countries"
# Grant: Block

# BREAK-GLASS ACCOUNTS:
# Account di emergenza (2) esclusi da TUTTE le policy CA
# - Solo Global Admin
# - Password lunga e complessa, scritta e conservata in cassaforte
# - Monitorare accessi con alert
```

---

## Conditional Access — Componenti delle Policy

Ogni policy di Conditional Access è composta da quattro blocchi fondamentali. La comprensione dettagliata di ciascuno è necessaria per progettare policy efficaci senza creare conflitti o gap di sicurezza.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                ANATOMIA DI UNA CONDITIONAL ACCESS POLICY                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. ASSIGNMENTS (CHI + COSA)                                             │
│  ├── Users and Groups:                                                   │
│  │   ├── Include: All users / Specific groups / Directory roles          │
│  │   ├── Exclude: Break-glass accounts / Service accounts / Groups       │
│  │   └── Guest or external users (selezionabile specificamente)          │
│  │                                                                       │
│  ├── Target Resources:                                                   │
│  │   ├── Cloud apps: All / Specific apps (Office 365, Azure Portal...)  │
│  │   ├── User actions: Register security info / Register or join devices │
│  │   └── Authentication context: per proteggere azioni specifiche        │
│  │       (es. "richiedi MFA quando l'utente accede a un sito            │
│  │       SharePoint classificato come Confidential")                     │
│  │                                                                       │
│  2. CONDITIONS (QUANDO)                                                  │
│  ├── User risk level: None / Low / Medium / High (richiede P2)          │
│  ├── Sign-in risk level: None / Low / Medium / High (richiede P2)       │
│  ├── Insider risk level: Elevated / Minor / Moderate (Purview)          │
│  ├── Device platforms: Android / iOS / Windows / macOS / Linux / All     │
│  ├── Locations:                                                          │
│  │   ├── Named locations (IP ranges, countries)                          │
│  │   ├── Trusted locations (MFA trusted IPs)                             │
│  │   └── Include / Exclude combinations                                  │
│  ├── Client apps:                                                        │
│  │   ├── Browser                                                         │
│  │   ├── Mobile apps and desktop clients                                 │
│  │   └── Other clients (Exchange ActiveSync, other legacy)               │
│  ├── Filter for devices:                                                 │
│  │   ├── Device.isCompliant / Device.isManaged                           │
│  │   ├── Device.operatingSystem / Device.model                           │
│  │   └── Custom expressions per proprietà del device                     │
│  └── Authentication flows: Device code flow / Authentication transfer    │
│                                                                          │
│  3. GRANT CONTROLS (COSA FARE — ALLOW)                                   │
│  ├── Block access                                                        │
│  ├── Grant access with:                                                  │
│  │   ├── Require multifactor authentication                              │
│  │   ├── Require authentication strength                                 │
│  │   │   (custom: es. solo FIDO2, solo passwordless)                     │
│  │   ├── Require device to be marked as compliant                        │
│  │   ├── Require Hybrid Azure AD joined device                           │
│  │   ├── Require approved client app                                     │
│  │   ├── Require app protection policy                                   │
│  │   ├── Require password change                                         │
│  │   └── Require terms of use accepted                                   │
│  └── Multiple controls: Require ALL / Require ONE of selected            │
│                                                                          │
│  4. SESSION CONTROLS (LIMITI SULLA SESSIONE)                             │
│  ├── Use app enforced restrictions                                       │
│  │   (SharePoint: limited access, Exchange: view-only attachments)       │
│  ├── Use Conditional Access App Control                                  │
│  │   (proxy tramite Defender for Cloud Apps per DLP in real-time)        │
│  ├── Sign-in frequency: quanto spesso l'utente deve ri-autenticarsi     │
│  │   (es. ogni 12 ore, ogni 7 giorni)                                    │
│  ├── Persistent browser session: Allow / Never persist                   │
│  │   (controlla "Keep me signed in")                                     │
│  ├── Customize continuous access evaluation: Strict / Standard           │
│  │   (strict = revoca token immediata su cambio policy)                  │
│  └── Disable resilience defaults: se abilitato, non usa token cached     │
│      durante interruzioni di Entra ID                                    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

Riferimento: https://learn.microsoft.com/entra/identity/conditional-access/concept-conditional-access-policies (consultato: 2026-05-23)

---

## Conditional Access — Policy Comuni Essenziali

Queste sono le policy che ogni tenant enterprise dovrebbe implementare come baseline di sicurezza. L'ordine di implementazione segue una progressione di rischio.

```powershell
# ============================================================
# POLICY BASELINE — PRIORITÀ DI IMPLEMENTAZIONE
# ============================================================

# PRIORITÀ 1: Bloccare legacy authentication
# Perché: protocolli legacy (POP3, IMAP, SMTP basic) non supportano MFA
# e sono il vettore d'attacco #1 per password spray
#
# Nome: "CA001 — Block legacy authentication"
# Users: All users
# Cloud apps: All cloud apps
# Conditions → Client apps: Exchange ActiveSync clients, Other clients
# Grant: Block access
# Exclude: break-glass accounts
# Stato: On (non serve Report-Only, impatto prevedibile)

# PRIORITÀ 2: Richiedere MFA per tutti gli utenti
# Nome: "CA002 — Require MFA for all users"
# Users: All users
# Cloud apps: All cloud apps
# Grant: Require multifactor authentication
# Exclude: break-glass accounts, service accounts (con compensating control)
# Stato: prima Report-Only per 7 giorni, poi On

# PRIORITÀ 3: Richiedere MFA per azioni amministrative
# Nome: "CA003 — Require phishing-resistant MFA for admins"
# Users: Directory roles → Global Admin, Exchange Admin, SharePoint Admin,
#   Security Admin, Conditional Access Admin, Privileged Role Admin
# Cloud apps: All cloud apps
# Grant: Require authentication strength → Phishing-resistant MFA
# Exclude: break-glass accounts
# Stato: On

# PRIORITÀ 4: Richiedere dispositivo conforme per M365
# Nome: "CA004 — Require compliant device for M365"
# Users: All users
# Cloud apps: Office 365
# Grant: Require device to be marked as compliant
# Exclude: break-glass accounts, guest users (non gestiti)
# Stato: Report-Only → test con pilot → On

# PRIORITÀ 5: Bloccare accesso da paesi non autorizzati
# Nome: "CA005 — Block access from unauthorized countries"
# Users: All users
# Conditions → Locations: Include → "Blocked Countries" named location
# Grant: Block access
# Exclude: break-glass accounts
# Stato: On

# PRIORITÀ 6: Richiedere MFA per registrazione MFA
# Nome: "CA006 — Require MFA for security info registration"
# Users: All users
# User actions: Register security information
# Conditions → Locations: Exclude → Trusted locations (rete aziendale)
# Grant: Require MFA
# Nota: evita che un attaccante registri un proprio metodo MFA
# da una rete non fidata

# PRIORITÀ 7: Frequenza sign-in per sessioni non persistenti
# Nome: "CA007 — Sign-in frequency for unmanaged devices"
# Users: All users
# Cloud apps: All cloud apps
# Conditions → Filter for devices: device.isCompliant -ne True
# Session: Sign-in frequency → 12 hours
# Session: Persistent browser session → Never persistent
# Nota: utenti su device non gestiti devono ri-autenticarsi ogni 12 ore
```

---

## Conditional Access — Scenari Enterprise Avanzati

### Named Locations

```powershell
# Le Named Locations definiscono reti/paesi per le policy CA

# Creare named location per IP aziendali:
# Entra ID → Security → Conditional Access → Named locations → New location
# Nome: "Corporate Network"
# Tipo: IP ranges
# IP: 203.0.113.0/24, 198.51.100.0/24
# Mark as trusted location: Yes

# Creare named location per paesi bloccati:
# Nome: "Blocked Countries"
# Tipo: Countries/Regions
# Selezionare: Russia, North Korea, Iran, etc.

# Usare nelle policy CA:
# Conditions → Locations → Include: "Blocked Countries" → Grant: Block
```

### Continuous Access Evaluation (CAE)

```powershell
# CAE permette la revoca in tempo reale dei token di accesso
# Senza CAE: i token OAuth durano 1 ora (default)
# Con CAE: il token viene invalidato immediatamente quando:
# - L'utente viene disabilitato
# - La password viene cambiata
# - L'MFA viene revocato
# - L'admin revoca le sessioni
# - La policy CA cambia (es. nuova location policy)

# CAE è abilitato di default per Microsoft 365 apps
# Le app devono supportare CAE (SDK aggiornato)

# Verificare lo stato CAE:
# Sign-in logs → selezionare un evento → "Continuous Access Evaluation"
# → Is Satisfactory: True/False

# Forzare la revoca immediata di tutte le sessioni di un utente:
Connect-MgGraph -Scopes "User.ReadWrite.All"
Revoke-MgUserSignInSession -UserId "<user-object-id>"
# Con CAE, le sessioni M365 vengono terminate in 1-3 minuti
# Senza CAE, il token resta valido fino alla scadenza (1 ora)
```

### Token Protection (Token Binding)

```powershell
# Token Protection lega il token al dispositivo che lo ha richiesto
# Impedisce il token theft (rubare un token e usarlo da un altro dispositivo)

# Configurare in Conditional Access:
# Session Controls → "Require token protection for sign-in sessions (Preview)"
# Grant: Require token protection

# Prerequisiti:
# - Windows 10/11 con TPM 2.0
# - Device Azure AD Joined o Hybrid Joined
# - App che supportano token protection (Edge, Office, etc.)

# Se un token viene rubato e usato da un dispositivo diverso,
# Entra ID rifiuta l'accesso perché il token è legato al TPM del device originale
```

### Authentication Strengths

```powershell
# Authentication Strengths definiscono QUALI metodi MFA sono accettabili
# Esempio: per admin richiedere FIDO2, non SMS

# Strengths predefinite:
# - Multifactor authentication: qualsiasi metodo MFA
# - Passwordless MFA: FIDO2, Windows Hello, Authenticator passwordless
# - Phishing-resistant MFA: solo FIDO2 e Windows Hello (NO SMS, NO push)

# Creare strength personalizzata:
# Entra ID → Security → Authentication methods → Authentication strengths
# Nome: "Admin-PhishingResistant"
# Metodi consentiti: FIDO2 security key, Windows Hello for Business

# Usare nella policy CA:
# Grant → "Require authentication strength" → selezionare la strength
# Risultato: gli admin DEVONO usare FIDO2 o Windows Hello, SMS non accettato
```

---

## Multi-Factor Authentication

```powershell
# MFA aggiunge un secondo fattore oltre alla password:
# - Microsoft Authenticator (push notification o TOTP) — CONSIGLIATO
# - SMS/Phone call (meno sicuro, evitare se possibile)
# - FIDO2 Security Key (hardware, es. YubiKey) — più sicuro
# - Windows Hello for Business (biometrico/PIN legato al device)

# Configurazione MFA:
# Entra ID → Security → MFA → Additional cloud-based MFA settings
# Oppure: gestito interamente via Conditional Access (consigliato)

# Per-user MFA (legacy, sconsigliato):
# Entra ID → Users → Per-user MFA
# Stato: Disabled → Enabled → Enforced

# MFA via Conditional Access (consigliato):
# Creare policy CA con Grant: Require MFA
# Più granulare: MFA solo da reti non fidate, solo per app sensibili

# Number Matching (anti-MFA fatigue):
# Entra ID → Security → Authentication methods → Microsoft Authenticator
# → Enable number matching: Enabled
# L'utente deve inserire il numero mostrato sullo schermo nell'app
# Previene attacchi di MFA bombing/prompt fatigue

# FIDO2 Security Key:
# Entra ID → Security → Authentication methods → FIDO2 security key
# → Enable: Yes, Target: All users o gruppi specifici
# L'utente registra la chiave in myaccount.microsoft.com

# Registrazione: https://aka.ms/mfasetup
```

---

## Metodi MFA — Dettaglio e Confronto

Ogni metodo MFA ha un profilo di sicurezza diverso. La scelta va guidata dal profilo di rischio dell'utente e dal contesto d'uso.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│               METODI MFA — CONFRONTO SICUREZZA E USABILITÀ                 │
├───────────────────┬─────────────┬──────────────┬───────────┬────────────────┤
│ Metodo            │ Phishing-   │ MFA Fatigue  │ Usabilità │ Prerequisiti   │
│                   │ resistant?  │ resistant?   │           │                │
├───────────────────┼─────────────┼──────────────┼───────────┼────────────────┤
│ Microsoft         │ No (push    │ Sì (con      │ Alta      │ Smartphone     │
│ Authenticator     │ notification│ number       │           │ con app        │
│ (push + number    │ intercett.) │ matching)    │           │ installata     │
│ matching)         │             │              │           │                │
│                   │             │              │           │                │
│ Microsoft         │ Sì (se      │ Sì           │ Alta      │ Smartphone con │
│ Authenticator     │ passwordless│              │           │ app, Entra ID  │
│ (passwordless)    │ + device    │              │           │ P1, device     │
│                   │ binding)    │              │           │ registrato     │
│                   │             │              │           │                │
│ FIDO2 Security    │ Sì          │ Sì           │ Media     │ Chiave HW      │
│ Key (YubiKey,     │ (standard   │              │ (serve    │ (25-60 EUR),   │
│ Feitian, etc.)    │ WebAuthn)   │              │ portare   │ browser con    │
│                   │             │              │ la chiave)│ WebAuthn       │
│                   │             │              │           │                │
│ Windows Hello     │ Sì          │ Sì           │ Alta      │ TPM 2.0,       │
│ for Business      │ (chiave     │              │ (biometr.)│ Windows 10/11, │
│                   │ legata a    │              │           │ fotocamera IR  │
│                   │ device)     │              │           │ o lettore impr.│
│                   │             │              │           │                │
│ Certificate-based │ Sì          │ Sì           │ Media     │ Smart card o   │
│ Authentication    │ (certificato│              │           │ certificato    │
│ (CBA)             │ X.509)      │              │           │ utente, PKI    │
│                   │             │              │           │                │
│ TOTP (Authenticat.│ No (codice  │ Sì           │ Media     │ App TOTP       │
│ o app terze)      │ intercett.) │              │           │ qualsiasi      │
│                   │             │              │           │                │
│ SMS               │ No (SIM     │ No (prompt   │ Alta      │ Telefono       │
│                   │ swap, SS7   │ bombing)     │           │ cellulare      │
│                   │ intercept)  │              │           │                │
│                   │             │              │           │                │
│ Phone call        │ No          │ No           │ Alta      │ Telefono       │
│                   │             │              │           │                │
│ Email OTP         │ No (email   │ No           │ Alta      │ Indirizzo      │
│                   │ compromesso)│              │           │ email          │
├───────────────────┼─────────────┼──────────────┼───────────┼────────────────┤
│ RACCOMANDAZIONE:                                                            │
│ ├── Admin / privilegiati: FIDO2 o Windows Hello (phishing-resistant)        │
│ ├── Utenti standard: Authenticator con number matching                      │
│ ├── Frontline / kiosk: FIDO2 o Temporary Access Pass                       │
│ └── EVITARE: SMS e phone call per nuovi deployment                          │
└──────────────────────────────────────────────────────────────────────────────┘
```

```powershell
# ============================================================
# CONFIGURAZIONE METODI MFA — AUTHENTICATION METHODS POLICY
# ============================================================

# La gestione moderna dei metodi MFA avviene tramite la
# Authentication Methods Policy (non più tramite legacy MFA settings)

# Entra ID → Security → Authentication methods → Policies

# Abilitare Microsoft Authenticator (passwordless + push):
# → Microsoft Authenticator → Enable → All users
# → Configure → Authentication mode: Any (push + passwordless)
# → Number matching: Enabled
# → Show additional context: Enabled (app name + location in notifica)

# Abilitare FIDO2:
# → FIDO2 security key → Enable → Specific group (es. GRP-Admins)
# → Allow self-service setup: Yes
# → Enforce attestation: No (a meno che non serva filtrare per vendor)
# → Key restrictions: opzionalmente limitare a specifici AAGUID
#   (es. solo YubiKey 5 Series)

# Abilitare Certificate-based Authentication (CBA):
# → Certificate-based authentication → Enable
# → Configurare: Certificate authorities (caricare CA root e intermediate)
# → Authentication binding: certificate field → Entra ID attribute mapping
# → Protection level: Single-factor o Multi-factor certificate auth
# Richiede PKI interna configurata (→ 28-pki-certificati-guida-completa.md)

# Disabilitare SMS (consigliato per nuovi deploy):
# → SMS → Enable → Specific group (solo utenti che NECESSITANO SMS)
# O → Disable
```

Riferimento: https://learn.microsoft.com/entra/identity/authentication/concept-authentication-methods (consultato: 2026-05-23)

---

## MFA — Deployment e Rollout Enterprise

### Piano di Rollout MFA per 500+ Utenti

```powershell
# ============================================================
# PIANO DI ROLLOUT MFA — 4 SETTIMANE
# ============================================================

# SETTIMANA 1: PREPARAZIONE
# ─────────────────────────
# 1. Verificare licenze (P1 minimo per MFA via Conditional Access)
# 2. Creare Break-Glass accounts (2x) ESCLUSI da tutte le policy
# 3. Abilitare Combined Registration:
#    Entra ID → User settings → Manage user feature settings
#    → Users can use combined security information registration: All

# 4. Scegliere i metodi MFA consentiti:
#    Entra ID → Security → Authentication methods → Policies
#    → Microsoft Authenticator: Enabled (All users)
#    → FIDO2 security keys: Enabled (Admin group)
#    → SMS: Enabled (All users) — come fallback
#    → Email: Disabled (non sicuro per MFA)

# 5. Configurare Number Matching (anti-MFA fatigue):
#    Microsoft Authenticator → Configure → Number matching: Enabled
#    → Show additional context: Enabled (mostra app name e location)

# 6. Creare Registration Campaign:
#    Entra ID → Security → Authentication methods → Registration campaign
#    → State: Enabled
#    → Days allowed to snooze: 3
#    → Target: All users

# SETTIMANA 2: PILOT — IT TEAM (Report-Only)
# ────────────────────────────────────────────
# Creare policy CA in Report-Only mode per il gruppo IT:
# Nome: "CA-MFA-Pilot-IT"
# Users: GRP-IT-Staff
# Cloud Apps: All cloud apps
# Grant: Require MFA
# Enable policy: Report-only

# Monitorare per 5 giorni:
# Sign-in logs → filter by policy name
# Verificare quanti login sarebbero stati bloccati
# Quanti utenti non hanno ancora registrato MFA

# SETTIMANA 3: ENFORCE — IT TEAM + EARLY ADOPTERS
# ──────────────────────────────────────────────────
# Passare la policy CA a "On" per IT
# Aggiungere gruppo Early Adopters (50-100 utenti volontari)
# Monitorare problemi e supportare utenti

# SETTIMANA 4: ENFORCE — TUTTI GLI UTENTI
# ─────────────────────────────────────────
# Creare policy definitiva:
# Nome: "CA-MFA-All-Users"
# Users: All users
# Exclude: Break-glass accounts, service accounts
# Cloud Apps: All cloud apps
# Grant: Require MFA
# Enable policy: On

# ============================================================
# MONITORAGGIO POST-ROLLOUT
# ============================================================

# Report MFA adoption:
# Entra ID → Security → Authentication methods → Activity
# → Registration → quanti utenti hanno registrato MFA
# → Usage → quanti login usano MFA

# Script: trovare utenti senza MFA registrato
Connect-MgGraph -Scopes "UserAuthenticationMethod.Read.All"
$users = Get-MgUser -All -Property DisplayName, UserPrincipalName, Id
foreach ($u in $users) {
    $methods = Get-MgUserAuthenticationMethod -UserId $u.Id
    if ($methods.Count -le 1) {  # Solo password, nessun secondo fattore
        Write-Host "NO MFA: $($u.UserPrincipalName)"
    }
}
```

---

## Identity Protection e Risk Policies

```powershell
# Entra ID Identity Protection (richiede P2) usa ML per detectare
# comportamenti anomali e automatizzare la risposta

# ============================================================
# TIPI DI RISCHIO
# ============================================================

# USER RISK (rischio sull'account — persistente fino a remediation)
# - Leaked credentials: password trovata in data breach
# - Threat intelligence: Microsoft intelligence indica compromissione
# - Anomalous user activity: pattern anomalo sull'account

# SIGN-IN RISK (rischio sulla sessione — per singolo login)
# - Anonymous IP: login da rete anonimizzata (Tor, VPN anonima)
# - Atypical travel: login da location impossibile (es. Roma e Tokyo in 1h)
# - Malware-linked IP: IP associato a malware
# - Unfamiliar sign-in properties: browser/OS/location mai usati
# - Password spray: pattern di password spray rilevato
# - Token anomaly: proprietà anomale nel token

# ============================================================
# CONFIGURARE RISK POLICIES
# ============================================================

# Entra ID → Security → Identity Protection → Policies

# USER RISK POLICY:
# Users: All users (exclude break-glass)
# User risk level: High
# Access: Allow access → Require password change
# → L'utente con rischio alto DEVE cambiare password

# SIGN-IN RISK POLICY:
# Users: All users (exclude break-glass)
# Sign-in risk: Medium and above
# Access: Allow access → Require MFA
# → Login sospetto richiede MFA aggiuntivo

# OPPURE via Conditional Access (più flessibile):
# Conditions → Sign-in risk level → Medium, High
# Grant → Require MFA + Require password change

# ============================================================
# MONITORARE I RISCHI
# ============================================================

# Entra ID → Security → Identity Protection
# → Risky users: lista utenti con rischio attivo
# → Risky sign-ins: login con rischio rilevato
# → Risk detections: tutti gli eventi di rischio

# API Graph per automatizzare:
Connect-MgGraph -Scopes "IdentityRiskyUser.Read.All"
Get-MgRiskyUser -Filter "riskLevel eq 'high'" |
    Select-Object UserDisplayName, UserPrincipalName, RiskLevel, RiskState

# Confermare o dismissare un rischio:
# Confirm-MgRiskyUserCompromised -UserId "<user-id>"
# Invoke-MgDismissRiskyUser -UserId "<user-id>"
```

---

## Identity Protection — Approfondimento

### Risk Detection Engine — Come Funziona

Identity Protection analizza miliardi di segnali per ogni autenticazione. I segnali provengono da:

1. **Microsoft Threat Intelligence**: dati da Windows, Xbox, Microsoft 365 su botnet, malware, phishing
2. **Credential Intelligence**: monitoraggio continuo del dark web e paste sites per credenziali compromesse (funziona solo con PHS abilitato)
3. **Behavioral Analytics**: baseline ML per ogni utente (location, device, orari, app)
4. **Microsoft Defender for Cloud Apps**: segnali da app SaaS monitorate

```powershell
# ============================================================
# RISK-BASED CONDITIONAL ACCESS — BEST PRACTICES
# ============================================================

# La raccomandazione Microsoft è gestire le risk policies tramite
# Conditional Access (non tramite la UI legacy di Identity Protection).

# Policy per SIGN-IN RISK:
# Nome: "CA-SignInRisk-MFA"
# Users: All users (exclude break-glass)
# Cloud apps: All cloud apps
# Conditions → Sign-in risk: Medium + High
# Grant: Require MFA (l'utente MFA-verificato risolve il rischio automaticamente)

# Policy per USER RISK:
# Nome: "CA-UserRisk-PasswordChange"
# Users: All users (exclude break-glass)
# Cloud apps: All cloud apps
# Conditions → User risk: High
# Grant: Require password change + Require MFA
# Nota: richiede SSPR + Password Writeback per utenti sincronizzati

# ============================================================
# INVESTIGAZIONE RISCHI
# ============================================================

# Workflow di investigazione per un utente a rischio alto:
#
# 1. Entra ID → Identity Protection → Risky users → selezionare utente
# 2. Verificare le Risk Detections associate:
#    - Tipo di rischio (leaked creds, atypical travel, etc.)
#    - Timestamp e location
#    - IP address
# 3. Correlare con i Sign-in logs (stesso timestamp, stesso IP)
# 4. Decidere:
#    - Rischio confermato → Confirm compromised (forza password change + MFA re-registration)
#    - Falso positivo → Dismiss risk
# 5. Se confermato:
#    - Revocare tutte le sessioni
#    - Forzare password change
#    - Verificare le app consent dell'utente (possibile OAuth app grant attack)
#    - Verificare i mail forwarding rules (possibile BEC)

# Script: report rischi delle ultime 24 ore
Connect-MgGraph -Scopes "IdentityRiskEvent.Read.All"
$yesterday = (Get-Date).AddDays(-1).ToString("yyyy-MM-ddTHH:mm:ssZ")
$detections = Get-MgRiskDetection -Filter "detectedDateTime ge $yesterday" |
    Select-Object UserDisplayName, RiskEventType, RiskLevel, DetectedDateTime,
        IpAddress, Location, Activity
$detections | Format-Table -AutoSize
```

Riferimento: https://learn.microsoft.com/entra/id-protection/concept-identity-protection-risks (consultato: 2026-05-23)

---

## Azure AD Application Proxy

```powershell
# App Proxy pubblica applicazioni web on-premise verso Internet
# attraverso Entra ID, SENZA VPN e senza aprire porte firewall

# Architettura:
# [Utente esterno] → [Entra ID] → [App Proxy Cloud Service]
#                                         ↓ (outbound HTTPS)
#                                  [App Proxy Connector on-premise]
#                                         ↓
#                                  [App web interna]

# Vantaggi:
# - Nessuna porta inbound sul firewall
# - SSO con Entra ID (Kerberos, header, SAML)
# - Conditional Access + MFA sulle app on-premise
# - Pre-autenticazione: l'utente si autentica in Entra ID PRIMA di raggiungere l'app

# Installazione Connector:
# 1. Scaricare App Proxy Connector dal portale Entra ID
# 2. Installare su un server Windows nella stessa rete dell'app
# 3. Il connector stabilisce connessione outbound (443) verso il cloud

# Configurare App Proxy:
# Entra ID → Enterprise applications → New application → On-premises application
# - Internal URL: https://intranet.corp.contoso.com
# - External URL: https://intranet-contoso.msappproxy.net (o dominio custom)
# - Pre Authentication: Azure Active Directory
# - SSO: Integrated Windows Authentication (per app Kerberos)

# Requisiti per SSO Kerberos:
# - Connector server nel dominio AD
# - SPN configurato per l'account del servizio app
# - Kerberos Constrained Delegation (KCD) configurato
```

---

---

## Privileged Identity Management (PIM)

```powershell
# PIM (richiede Entra ID P2) gestisce l'accesso privilegiato
# con il principio "Just-In-Time" e "Just-Enough-Access"

# ============================================================
# CONCETTI PIM
# ============================================================
#
# ELIGIBLE: l'utente PUÒ attivare il ruolo quando serve
# ACTIVE: il ruolo è attivo (permanente o time-limited)
#
# Workflow:
# 1. Admin configura il ruolo come "Eligible" per l'utente
# 2. L'utente richiede l'attivazione quando necessario
# 3. L'attivazione richiede: giustificazione + MFA + (opzionale) approvazione
# 4. Il ruolo è attivo per una durata limitata (es. 4 ore)
# 5. Alla scadenza, il ruolo viene automaticamente disattivato

# ============================================================
# CONFIGURAZIONE PIM
# ============================================================

# Entra ID → Identity Governance → Privileged Identity Management

# Per ogni ruolo:
# → Settings → Edit
# - Maximum activation duration: 4 hours (default 8)
# - Require MFA on activation: Yes
# - Require justification: Yes
# - Require approval: Yes (per ruoli critici come Global Admin)
# - Approvers: gruppo di approvatori
# - Require ticket information: Yes (numero ticket ITSM)

# Assegnare ruolo eligible:
# PIM → Entra ID roles → Roles → Global Administrator
# → Add assignments → Select member → Assignment type: Eligible
# → Duration: 1 year (poi rinnovo con review)

# L'utente attiva il ruolo quando serve:
# myaccount.microsoft.com → PIM → My roles → Activate
# Inserire: giustificazione, durata, ticket number
# Se l'approvazione è richiesta: l'approvatore riceve una notifica

# ============================================================
# ACCESS REVIEWS (revisioni periodiche)
# ============================================================

# Le Access Reviews verificano periodicamente che gli assegnamenti
# siano ancora necessari

# Entra ID → Identity Governance → Access Reviews → New

# Configurazione:
# - Scope: PIM role assignments
# - Frequency: Quarterly (ogni 3 mesi)
# - Reviewers: Manager of the user (o self-review)
# - Auto-apply results: Yes
# - If reviewer doesn't respond: Remove access
# - Duration: 14 days per completare la review

# Risultato: ogni trimestre, i manager confermano o revocano
# l'accesso privilegiato dei propri team member
```

---

## PIM — Approfondimento Operativo

### Workflow di Approvazione e Alert

```powershell
# ============================================================
# CONFIGURAZIONE AVANZATA PIM PER RUOLO
# ============================================================

# Per il ruolo Global Administrator (il più critico):
# PIM → Entra ID roles → Global Administrator → Settings → Edit

# Activation:
# - Maximum duration: 2 hours (non 8 — interventi emergenziali sono brevi)
# - On activation, require: Azure MFA
# - Require justification: Yes
# - Require ticket information: Yes
# - Require approval to activate: Yes
# - Select approvers: GRP-PIM-Approvers (almeno 3 persone)

# Assignment:
# - Allow permanent eligible assignment: No
# - Expire eligible assignments after: 365 days
# - Allow permanent active assignment: No (mai permanente per GA)
# - Expire active assignments after: N/A (non usare active per GA)

# Notification:
# - Send notifications when members are assigned as eligible: Admin + Assignee
# - Send notifications when members are activated: Admin + Assignee + Approver
# - Send notifications when eligible assignments are about to expire: 14 days

# ============================================================
# PIM PER AZURE RESOURCES (non solo Entra ID roles)
# ============================================================

# PIM gestisce anche i ruoli RBAC sulle risorse Azure:
# PIM → Azure resources → selezionare subscription → Roles
# Es: Owner, Contributor, Reader su una subscription
# Stesso workflow: Eligible → Activate → Just-In-Time

# Questo è fondamentale per non avere assegnamenti Owner permanenti
# sulle subscription Azure di produzione.

# ============================================================
# ACCESS REVIEWS — CONFIGURAZIONE DETTAGLIATA
# ============================================================

# Access Review per ruoli PIM:
# Scope: Users assigned to a privileged role
# Review: Global Administrator, Exchange Administrator
# Reviewers: Self (l'utente conferma se ha ancora bisogno)
#   + Manager (il manager conferma)
# Frequency: Quarterly
# Duration per review round: 14 days
# Auto-apply: Yes
# If reviewer doesn't respond: Remove access
# Fallback reviewers: GRP-IT-Security

# Access Review per gruppi con accesso a risorse sensibili:
# Scope: Members of group "GRP-Finance-Data-Access"
# Reviewers: Group owner
# Frequency: Monthly (per dati finanziari, più frequente)
# Duration: 7 days
# Auto-apply: Yes

# Monitorare Access Reviews:
Connect-MgGraph -Scopes "AccessReview.Read.All"
Get-MgIdentityGovernanceAccessReviewDefinition |
    Select-Object DisplayName, Status, @{N='StartDate';E={$_.Schedule.StartDateTime}} |
    Format-Table -AutoSize
```

Riferimento: https://learn.microsoft.com/entra/id-governance/privileged-identity-management/pim-configure (consultato: 2026-05-23)

---

## Registrazione Applicazioni e OAuth 2.0

La registrazione delle applicazioni in Entra ID è il meccanismo con cui le applicazioni ottengono un'identità nel tenant e possono autenticare utenti o accedere a API protette.

### App Registration vs Enterprise Application

```
┌──────────────────────────────────────────────────────────────────────────┐
│            APP REGISTRATION vs ENTERPRISE APPLICATION                    │
├──────────────────────────┬───────────────────────────────────────────────┤
│ App Registration          │ Enterprise Application (Service Principal)  │
├──────────────────────────┼───────────────────────────────────────────────┤
│ Definizione globale       │ Istanza locale nel tenant                    │
│ dell'applicazione         │ dell'applicazione                            │
│                          │                                               │
│ Contiene:                │ Contiene:                                     │
│ - Client ID (App ID)     │ - Object ID (istanza tenant)                 │
│ - Redirect URIs          │ - Assegnamenti utenti/gruppi                 │
│ - Certificati/Secrets    │ - Conditional Access policies                 │
│ - API Permissions        │ - SSO configuration                           │
│ - Token configuration    │ - Provisioning (SCIM)                         │
│                          │ - Properties (logo, notes)                    │
│                          │                                               │
│ Creata da: sviluppatore  │ Creata automaticamente quando:               │
│ o admin dell'app         │ - Un'app registration viene creata            │
│                          │ - Un'app gallery viene aggiunta               │
│                          │ - Un utente consente un'app (consent)         │
│                          │                                               │
│ Scope: multi-tenant      │ Scope: singolo tenant                         │
│ (se configurata)         │                                               │
├──────────────────────────┴───────────────────────────────────────────────┤
│ REGOLA: l'App Registration è il "blueprint",                             │
│ l'Enterprise Application è l'"istanza" nel tenant                        │
└──────────────────────────────────────────────────────────────────────────┘
```

### Flussi OAuth 2.0 in Entra ID

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    FLUSSI OAuth 2.0 — QUANDO USARE QUALE                │
├───────────────────────┬──────────────────────────────────────────────────┤
│ Flusso                │ Scenario                                        │
├───────────────────────┼──────────────────────────────────────────────────┤
│ Authorization Code    │ Web app con backend (es. ASP.NET, Node.js)      │
│ + PKCE                │ L'utente si autentica, l'app riceve un          │
│                       │ authorization code, lo scambia per token        │
│                       │ PKCE obbligatorio (anche per web app)           │
│                       │ CONSIGLIATO per la maggior parte dei casi       │
│                       │                                                  │
│ Client Credentials    │ Servizio-a-servizio (daemon, batch, API-to-API) │
│                       │ Nessun utente coinvolto                          │
│                       │ L'app si autentica con secret o certificato     │
│                       │ Usa permessi Application (non Delegated)        │
│                       │                                                  │
│ On-behalf-of (OBO)    │ API che chiama un'altra API per conto           │
│                       │ dell'utente autenticato                          │
│                       │ L'API intermedia scambia il token dell'utente   │
│                       │ per un token verso l'API downstream             │
│                       │                                                  │
│ Device Code           │ Dispositivi senza browser (IoT, CLI, smart TV)  │
│                       │ L'utente si autentica su un altro dispositivo   │
│                       │ inserendo un codice monouso                      │
│                       │ ATTENZIONE: vettore di phishing (device code    │
│                       │ phishing) — valutare blocco via CA              │
│                       │                                                  │
│ Implicit (DEPRECATO)  │ Non usare — sostituito da Auth Code + PKCE     │
│                       │ Era per SPA, ma espone token nell'URL            │
│                       │                                                  │
│ ROPC (DEPRECATO)      │ Non usare — invia username/password nel body    │
│                       │ Non supporta MFA, non supporta CA               │
└───────────────────────┴──────────────────────────────────────────────────┘
```

### Permessi API — Delegated vs Application

```powershell
# ============================================================
# TIPI DI PERMESSI
# ============================================================

# DELEGATED (delegati):
# - L'app agisce PER CONTO dell'utente
# - Richiede un utente autenticato
# - Il permesso effettivo è l'INTERSEZIONE tra il permesso dell'app
#   e i permessi dell'utente
# - Esempio: User.Read → l'app può leggere il profilo dell'utente loggato
# - Consenso: può essere dato dall'utente (user consent)
#   o dall'admin (admin consent) a seconda del permesso

# APPLICATION:
# - L'app agisce COME SE STESSA (senza utente)
# - Per daemon, servizi, batch jobs
# - Il permesso effettivo è il permesso completo (nessun utente che limita)
# - Esempio: User.Read.All → l'app può leggere TUTTI gli utenti
# - Consenso: SEMPRE admin consent (un admin deve approvare)

# ============================================================
# REGISTRARE UN'APPLICAZIONE — STEP BY STEP
# ============================================================

# 1. Entra ID → App registrations → New registration
#    Nome: "MyApp-Production"
#    Supported account types: Accounts in this organizational directory only
#    Redirect URI: https://myapp.contoso.com/auth/callback (per web app)

# 2. Annotare:
#    Application (client) ID: usato dall'app per identificarsi
#    Directory (tenant) ID: usato per costruire gli endpoint di autenticazione

# 3. Creare il segreto o il certificato:
#    Certificates & secrets → New client secret
#    NOTA: i client secret scadono (max 24 mesi). Preferire certificati.
#    Per produzione: usare certificati (più sicuri, nessun secret in chiaro)

# 4. Configurare i permessi API:
#    API permissions → Add a permission → Microsoft Graph
#    → Delegated permissions: User.Read (minimo per login)
#    → Application permissions: User.Read.All (solo se daemon)
#    → Grant admin consent (per permessi che lo richiedono)

# 5. Configurare i token:
#    Token configuration → Add optional claim
#    Es: aggiungere "email", "upn", "groups" nel token ID

# ============================================================
# SICUREZZA REGISTRAZIONE APP
# ============================================================

# Limitare chi può registrare app:
# Entra ID → User settings → App registrations
# → Users can register applications: No (solo admin possono registrare)

# Limitare il user consent:
# Entra ID → Enterprise applications → Consent and permissions
# → User consent settings:
#   Opzione raccomandata: "Allow user consent for apps from verified publishers,
#   for selected permissions"
# → Configure admin consent workflow: Enabled
#   (gli utenti possono richiedere consent, un admin approva)

# Verificare app con permessi eccessivi:
Connect-MgGraph -Scopes "Application.Read.All"
Get-MgServicePrincipal -All |
    ForEach-Object {
        $sp = $_
        $appRoles = Get-MgServicePrincipalAppRoleAssignment -ServicePrincipalId $sp.Id
        if ($appRoles) {
            [PSCustomObject]@{
                App = $sp.DisplayName
                Permissions = ($appRoles | ForEach-Object { $_.ResourceDisplayName + ": " + $_.Id }) -join "; "
            }
        }
    } | Where-Object Permissions | Format-Table -Wrap
```

Riferimento: https://learn.microsoft.com/entra/identity-platform/v2-overview (consultato: 2026-05-23)

---

## B2B Collaboration e Cross-Tenant Access

La collaborazione B2B consente di invitare utenti esterni (guest) nel tenant per accedere a risorse condivise senza creare account separati. L'utente guest si autentica nel proprio tenant di origine (home tenant) e accede alle risorse nel tenant host.

### Guest Users — Funzionamento

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      B2B COLLABORATION — FLUSSO                         │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  TENANT A (Host — la tua org)          TENANT B (Home — org esterna)    │
│  ┌──────────────────────────┐          ┌───────────────────────────┐    │
│  │                          │          │                           │    │
│  │  Guest User:             │  ◄──────  │  User:                    │    │
│  │  mrossi_partner.com      │  authn   │  mrossi@partner.com       │    │
│  │  #EXT#@contoso.           │  nel     │  Autenticazione nel       │    │
│  │  onmicrosoft.com         │  home    │  proprio tenant           │    │
│  │                          │  tenant  │                           │    │
│  │  Accesso a:              │          │  MFA gestita dal          │    │
│  │  - SharePoint specifico  │          │  tenant partner           │    │
│  │  - Teams specifico       │          │  (se trust configurato)   │    │
│  │  - App enterprise        │          │                           │    │
│  │                          │          │                           │    │
│  │  Conditional Access:     │          │                           │    │
│  │  - Applicato dal host    │          │                           │    │
│  │  - MFA: host o home      │          │                           │    │
│  │    (trust settings)      │          │                           │    │
│  │                          │          │                           │    │
│  └──────────────────────────┘          └───────────────────────────┘    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Cross-Tenant Access Settings

```powershell
# ============================================================
# CROSS-TENANT ACCESS SETTINGS
# ============================================================

# Entra ID → External Identities → Cross-tenant access settings

# DEFAULT SETTINGS (applicati a tutti i tenant esterni):
# - Inbound access (utenti esterni che accedono al nostro tenant):
#   → B2B collaboration: Allow (default)
#   → Trust settings: Block (default — non fidarsi del MFA esterno)
#
# - Outbound access (nostri utenti che accedono a tenant esterni):
#   → B2B collaboration: Allow (default)

# PER-TENANT SETTINGS (configurazioni specifiche per partner):
# Aggiungere un'organizzazione partner:
# → Add organization → inserire Tenant ID o dominio del partner

# Esempio: fidarsi del MFA del partner "partner.com":
# → Inbound access → Trust settings → Customize
# → Trust multifactor authentication from Azure AD tenant: Yes
# → Trust compliant devices: Yes (opzionale)
# → Trust hybrid Azure AD joined devices: Yes (opzionale)

# Risultato: quando mrossi@partner.com accede al nostro tenant,
# se ha già fatto MFA nel suo tenant, non gli viene chiesto di nuovo.

# ============================================================
# INVITARE GUEST USERS
# ============================================================

# Via portale:
# Entra ID → Users → New user → Invite external user
# Inserire email, messaggio di invito personalizzato
# Assegnare a gruppi e app

# Via PowerShell:
Connect-MgGraph -Scopes "User.Invite.All"
New-MgInvitation `
    -InvitedUserEmailAddress "mrossi@partner.com" `
    -InvitedUserDisplayName "Mario Rossi (Partner)" `
    -InviteRedirectUrl "https://myapps.microsoft.com" `
    -SendInvitationMessage:$true `
    -InvitedUserMessageInfo @{
        CustomizedMessageBody = "Benvenuto nel nostro tenant. Accedi per collaborare."
    }

# ============================================================
# GUEST USER LIFECYCLE
# ============================================================

# Problema: i guest users tendono ad accumularsi senza controllo.
# Soluzione: Access Reviews per guest users.

# Creare Access Review per guest:
# Identity Governance → Access Reviews → New
# Scope: Guest users only
# Review: All Microsoft 365 groups with guest users
# Reviewers: Group owners
# Frequency: Quarterly
# If reviewer doesn't respond: Remove access
# Auto-apply: Yes

# Script: trovare guest users inattivi
Connect-MgGraph -Scopes "User.Read.All", "AuditLog.Read.All"
$staleDate = (Get-Date).AddDays(-90).ToString("yyyy-MM-ddTHH:mm:ssZ")
$staleGuests = Get-MgUser -Filter "userType eq 'Guest'" -All -Property DisplayName, UserPrincipalName, SignInActivity |
    Where-Object { $_.SignInActivity.LastSignInDateTime -lt $staleDate -or $null -eq $_.SignInActivity.LastSignInDateTime }
$staleGuests | Select-Object DisplayName, UserPrincipalName,
    @{N='LastSignIn';E={$_.SignInActivity.LastSignInDateTime}} |
    Format-Table -AutoSize
Write-Host "Guest inattivi da 90+ giorni: $($staleGuests.Count)"
```

Riferimento: https://learn.microsoft.com/entra/external-id/what-is-b2b (consultato: 2026-05-23)

---

## Gestione con PowerShell — Microsoft.Graph

Il modulo Microsoft.Graph è il successore dei moduli AzureAD e MSOnline (deprecati). Tutta la gestione programmatica di Entra ID dovrebbe passare da Microsoft.Graph.

```powershell
# ============================================================
# SETUP E CONNESSIONE
# ============================================================

# Installare il modulo (una volta):
Install-Module Microsoft.Graph -Scope CurrentUser

# Il modulo è modulare — installare solo i sotto-moduli necessari:
Install-Module Microsoft.Graph.Users -Scope CurrentUser
Install-Module Microsoft.Graph.Groups -Scope CurrentUser
Install-Module Microsoft.Graph.Identity.DirectoryManagement -Scope CurrentUser
Install-Module Microsoft.Graph.Identity.SignIns -Scope CurrentUser

# Connessione interattiva (per admin):
Connect-MgGraph -Scopes "User.Read.All", "Group.ReadWrite.All", "AuditLog.Read.All"
# Apre il browser per l'autenticazione OAuth2

# Connessione con certificato (per automazione):
Connect-MgGraph -ClientId "<app-id>" -TenantId "<tenant-id>" `
    -CertificateThumbprint "<thumbprint>"

# Connessione con Managed Identity (da Azure VM/Function):
Connect-MgGraph -Identity

# Verificare connessione:
Get-MgContext | Select-Object Account, TenantId, Scopes

# ============================================================
# OPERAZIONI COMUNI — UTENTI
# ============================================================

# Elencare tutti gli utenti:
Get-MgUser -All -Property DisplayName, UserPrincipalName, AccountEnabled, UserType |
    Format-Table

# Cercare un utente specifico:
Get-MgUser -UserId "mrossi@contoso.com"

# Creare un nuovo utente cloud-only:
$passwordProfile = @{
    Password = "P@ssw0rd!ChangeMe"
    ForceChangePasswordNextSignIn = $true
}
New-MgUser -DisplayName "Luca Bianchi" `
    -UserPrincipalName "lbianchi@contoso.com" `
    -MailNickname "lbianchi" `
    -AccountEnabled:$true `
    -PasswordProfile $passwordProfile

# Disabilitare un utente:
Update-MgUser -UserId "mrossi@contoso.com" -AccountEnabled:$false

# ============================================================
# OPERAZIONI COMUNI — GRUPPI
# ============================================================

# Creare un gruppo di sicurezza:
New-MgGroup -DisplayName "GRP-Finance" `
    -MailEnabled:$false -SecurityEnabled:$true `
    -MailNickname "grp-finance" `
    -Description "Gruppo sicurezza per il team Finance"

# Aggiungere membro:
$user = Get-MgUser -UserId "mrossi@contoso.com"
$group = Get-MgGroup -Filter "displayName eq 'GRP-Finance'"
New-MgGroupMember -GroupId $group.Id -DirectoryObjectId $user.Id

# Elencare membri di un gruppo:
Get-MgGroupMember -GroupId $group.Id -All | ForEach-Object {
    Get-MgDirectoryObject -DirectoryObjectId $_.Id |
        Select-Object @{N='Name';E={$_.AdditionalProperties.displayName}}
}

# ============================================================
# OPERAZIONI — RUOLI E POLICY
# ============================================================

# Elencare assegnamenti di ruoli di directory:
Get-MgRoleManagementDirectoryRoleAssignment -All |
    Select-Object PrincipalId, RoleDefinitionId, DirectoryScopeId |
    Format-Table

# Elencare le Conditional Access policies:
Get-MgIdentityConditionalAccessPolicy |
    Select-Object DisplayName, State, CreatedDateTime |
    Format-Table -AutoSize
```

Riferimento: https://learn.microsoft.com/powershell/microsoftgraph/overview (consultato: 2026-05-23)

---

## Monitoraggio Entra ID

Il monitoraggio è la base della postura di sicurezza. Entra ID produce log dettagliati su ogni autenticazione e ogni modifica amministrativa. Senza monitoraggio attivo, le compromissioni passano inosservate.

### Sign-in Logs

```powershell
# I sign-in logs registrano ogni tentativo di autenticazione.
# Disponibili nel portale: Entra ID → Monitoring → Sign-in logs
# Retention: 30 giorni (P1/P2), 7 giorni (Free)

# Tipi di sign-in logs:
# 1. Interactive sign-ins: login utente (browser, app)
# 2. Non-interactive sign-ins: refresh token, SSO automatico
# 3. Service principal sign-ins: app-to-app (Client Credentials)
# 4. Managed identity sign-ins: Azure managed identity

# Filtri utili nel portale:
# - Status: Success / Failure / Interrupted
# - Conditional Access: Success / Failure / Not Applied
# - IP Address: per cercare IP sospetti
# - Application: per monitorare app specifiche

# Accesso via API:
Connect-MgGraph -Scopes "AuditLog.Read.All"
$signIns = Get-MgAuditLogSignIn -Top 50 -Filter "status/errorCode ne 0" |
    Select-Object UserDisplayName, AppDisplayName, IpAddress,
        @{N='City';E={$_.Location.City}},
        @{N='Error';E={$_.Status.ErrorCode}},
        @{N='Reason';E={$_.Status.FailureReason}},
        CreatedDateTime
$signIns | Format-Table -AutoSize
```

### Audit Logs

```powershell
# Gli audit logs registrano ogni modifica amministrativa nel tenant.
# Chi ha fatto cosa, quando, su quale oggetto.

# Esempi di eventi registrati:
# - Creazione/modifica/eliminazione utenti
# - Modifica membership gruppi
# - Modifica Conditional Access policies
# - Consent a un'applicazione
# - Assegnamento/rimozione ruoli
# - Modifica impostazioni del tenant

# Accesso via portale: Entra ID → Monitoring → Audit logs
# Filtri: Activity, Category, Target, Initiated by, Date range

# Accesso via API:
$audits = Get-MgAuditLogDirectoryAudit -Top 50 -Filter "activityDisplayName eq 'Add member to role'" |
    Select-Object ActivityDisplayName,
        @{N='Actor';E={$_.InitiatedBy.User.UserPrincipalName}},
        @{N='Target';E={$_.TargetResources[0].DisplayName}},
        ActivityDateTime
$audits | Format-Table -AutoSize
```

### Diagnostic Settings — Long-term Retention

```powershell
# Per retention oltre 30 giorni, configurare Diagnostic Settings
# per inviare i log a:
# 1. Log Analytics workspace (per query KQL avanzate)
# 2. Storage Account (per archiviazione a lungo termine, compliance)
# 3. Event Hub (per SIEM esterno: Splunk, Sentinel, QRadar)

# Configurazione:
# Entra ID → Monitoring → Diagnostic settings → Add diagnostic setting
# Nome: "EntraID-to-LogAnalytics"
# Logs da inviare:
# ✓ AuditLogs
# ✓ SignInLogs
# ✓ NonInteractiveUserSignInLogs
# ✓ ServicePrincipalSignInLogs
# ✓ ManagedIdentitySignInLogs
# ✓ RiskyUsers
# ✓ UserRiskEvents
# ✓ RiskyServicePrincipals
# Destinazione: Log Analytics workspace (nella subscription Azure)

# ============================================================
# QUERY KQL IN LOG ANALYTICS
# ============================================================

# Dopo l'invio a Log Analytics, usare KQL per analisi avanzate:

# Login falliti nelle ultime 24h raggruppati per IP:
# SigninLogs
# | where TimeGenerated > ago(24h)
# | where ResultType != "0"
# | summarize FailedAttempts = count() by IPAddress, UserDisplayName
# | where FailedAttempts > 5
# | order by FailedAttempts desc

# Modifiche a Conditional Access policy:
# AuditLogs
# | where Category == "Policy"
# | where ActivityDisplayName has "conditional access"
# | project TimeGenerated, InitiatedBy.user.userPrincipalName,
#           ActivityDisplayName, TargetResources

# Nuovi Global Admin aggiunti:
# AuditLogs
# | where ActivityDisplayName == "Add member to role"
# | extend RoleName = tostring(TargetResources[0].displayName)
# | where RoleName == "Global Administrator"
# | project TimeGenerated, InitiatedBy.user.userPrincipalName, RoleName
```

### Workbooks

```powershell
# I Workbooks sono dashboard interattive pre-costruite per
# visualizzare i dati di Entra ID.

# Entra ID → Monitoring → Workbooks
# Workbooks utili preinstallati:
# - Sign-in Analysis: panoramica dei login per status, app, location
# - Conditional Access Insights: efficacia delle policy CA
# - Authentication Methods Activity: adozione MFA e metodi usati
# - Risky Sign-ins: sign-in ad alto rischio con dettagli
# - Sensitive Operations: operazioni admin critiche

# Per workbook personalizzati:
# Entra ID → Monitoring → Workbooks → New
# Usare query KQL per creare visualizzazioni custom

# ALERT RULES (notifiche proattive):
# Azure Monitor → Alerts → New alert rule
# Scope: Log Analytics workspace con log Entra ID
# Condition: Custom log search (query KQL)
# Action: Email, SMS, webhook, Logic App

# Esempio alert: notifica quando un Global Admin viene aggiunto
# Query:
# AuditLogs
# | where ActivityDisplayName == "Add member to role"
# | extend RoleName = tostring(TargetResources[0].displayName)
# | where RoleName == "Global Administrator"
# Frequency: Every 5 minutes
# Threshold: Greater than 0
# Action: email a security-team@contoso.com
```

Riferimento: https://learn.microsoft.com/entra/identity/monitoring-health/concept-sign-ins (consultato: 2026-05-23)

---

## Migrazione da AD FS ad Autenticazione Gestita

La migrazione da AD FS a PHS + Seamless SSO è un progetto critico che elimina l'infrastruttura on-premise più complessa e costosa dell'identità ibrida. Microsoft raccomanda attivamente questa migrazione per tutti i clienti che non hanno requisiti di autenticazione custom.

### Perché Migrare

```
COSTI AD FS (infrastruttura tipica):
├── 2x server ADFS (Windows Server license, hardware/VM, manutenzione)
├── 2x server WAP (Web Application Proxy) in DMZ
├── Certificati SSL pubblici (rinnovo annuale)
├── Monitoring, patching, DR, backup
├── Competenze specialistiche per troubleshooting
└── TOTALE: 15.000-40.000 EUR/anno (escludendo tempo staff)

COSTI PHS + Seamless SSO:
├── Azure AD Connect (già presente per sync)
├── Nessun server aggiuntivo
├── Nessun certificato aggiuntivo
└── TOTALE: 0 EUR aggiuntivi (incluso nelle licenze Entra ID)
```

### Piano di Migrazione Dettagliato

```powershell
# ============================================================
# FASE 1: ASSESSMENT (1-2 settimane)
# ============================================================

# Inventario di tutte le applicazioni che usano AD FS:
# AD FS Management Console → Relying Party Trusts
# Elencare ogni app con:
# - Nome
# - Protocollo (SAML, WS-Fed, OAuth)
# - Claim rules
# - Utenti/gruppi che accedono

# Verificare quali app possono essere migrate direttamente:
# - App che supportano OAuth 2.0 / OIDC → migrazione diretta a Entra ID
# - App SAML standard → aggiungere in Enterprise Applications
# - App con claim rules custom complesse → valutare riscrittura o App Proxy

# Usare AD FS Application Activity Report:
# Entra ID → Usage & Insights → AD FS application activity
# Mostra quali app ADFS possono essere migrate e quali hanno limitazioni

# ============================================================
# FASE 2: PREPARAZIONE (1-2 settimane)
# ============================================================

# 1. Abilitare PHS nel wizard Entra Connect (coesiste con Federation)
#    Wizard → Change user sign-in → Enable Password Hash Synchronization
#    Il sync degli hash inizia in background (non cambia il metodo di autenticazione)

# 2. Configurare Seamless SSO nel wizard Entra Connect
#    → Enable single sign-on → inserire credenziali Domain Admin

# 3. Deployare GPO per Seamless SSO sui client
#    (come descritto nella sezione Seamless SSO)

# 4. Configurare SSPR + Password Writeback (se non già attivo)

# 5. Migrare le applicazioni:
#    Per ogni Relying Party Trust in ADFS:
#    a. Aggiungere l'app come Enterprise Application in Entra ID
#    b. Configurare SSO (SAML, OIDC, header-based)
#    c. Configurare claim/attributi
#    d. Assegnare utenti/gruppi
#    e. Testare con un utente pilota

# ============================================================
# FASE 3: STAGED ROLLOUT (1-2 settimane)
# ============================================================

# La Staged Rollout permette di migrare GRUPPI di utenti
# da Federation a Managed auth senza cambiare il dominio per tutti.

# Entra ID → Hybrid identity → Staged rollout
# Abilitare:
# - Password Hash Sync: ON
# - Seamless Single Sign-On: ON
# Aggiungere gruppi pilota:
# - GRP-StagedRollout-IT (team IT, 20 utenti)
# - Poi GRP-StagedRollout-EarlyAdopters (100 utenti)
# - Poi GRP-StagedRollout-Finance, HR, etc.

# Gli utenti nei gruppi staged rollout:
# - Si autenticano via PHS (non più via ADFS)
# - SSO via Seamless SSO nella rete aziendale
# - Tutte le policy CA si applicano normalmente

# Monitorare:
# - Sign-in logs: verificare login success/failure per gli utenti migrati
# - Controllare che nessuna app fallisca

# ============================================================
# FASE 4: CUTOVER COMPLETO
# ============================================================

# Quando tutti i gruppi sono stati migrati con successo:
# Convertire il dominio da Federated a Managed:

# PowerShell (MSOnline module o Graph):
# Set-MsolDomainAuthentication -DomainName "contoso.com" -Authentication Managed

# Oppure nel wizard Entra Connect:
# → Change user sign-in → Password Hash Synchronization

# Verificare:
# - TUTTI gli utenti possono autenticarsi
# - SSO funziona (rete aziendale)
# - SSPR funziona
# - MFA funziona (via CA, non più via ADFS MFA adapter)

# ============================================================
# FASE 5: DECOMMISSIONING ADFS (dopo 2-4 settimane di stabilità)
# ============================================================

# 1. Verificare che nessun utente usi più ADFS (sign-in logs ADFS = 0)
# 2. Rimuovere Staged Rollout (non più necessario)
# 3. Rimuovere i record DNS che puntano a ADFS/WAP
# 4. Spegnere i server WAP
# 5. Spegnere i server ADFS
# 6. Rimuovere le VM o il hardware
# 7. Aggiornare la documentazione
```

Riferimento: https://learn.microsoft.com/entra/identity/hybrid/connect/migrate-from-federation-to-cloud-authentication (consultato: 2026-05-23)

---

## Automazione e Script Enterprise

### Script: Audit Configurazione Entra ID

```powershell
# Script di audit completo della configurazione Entra ID
# Eseguire periodicamente per verificare compliance

function Invoke-EntraIDAudit {
    Connect-MgGraph -Scopes @(
        "User.Read.All",
        "Group.Read.All",
        "Policy.Read.All",
        "AuditLog.Read.All",
        "Directory.Read.All"
    )

    $report = @()

    # 1. Verificare Global Administrators
    $gaRole = Get-MgDirectoryRole -Filter "displayName eq 'Global Administrator'"
    $gaMembers = Get-MgDirectoryRoleMember -DirectoryRoleId $gaRole.Id
    $report += [PSCustomObject]@{
        Check   = "Global Admins Count"
        Value   = $gaMembers.Count
        Status  = if ($gaMembers.Count -le 5) { "OK" }
                  elseif ($gaMembers.Count -le 8) { "WARNING" }
                  else { "CRITICAL" }
        Detail  = "Raccomandato: max 5 Global Admin (2 break-glass + 3 operativi)"
    }

    # 2. Verificare Break-Glass accounts
    $bgAccounts = Get-MgUser -Filter "startsWith(displayName,'BreakGlass')" -ErrorAction SilentlyContinue
    $report += [PSCustomObject]@{
        Check   = "Break-Glass Accounts"
        Value   = ($bgAccounts | Measure-Object).Count
        Status  = if (($bgAccounts | Measure-Object).Count -ge 2) { "OK" } else { "CRITICAL" }
        Detail  = "Devono esistere almeno 2 break-glass accounts"
    }

    # 3. Verificare MFA registration
    $allUsers = Get-MgUser -All -Property DisplayName, UserPrincipalName, Id |
        Where-Object UserPrincipalName -notlike "*#EXT#*"
    $noMfa = 0
    foreach ($u in $allUsers | Select-Object -First 50) {
        $methods = Get-MgUserAuthenticationMethod -UserId $u.Id -ErrorAction SilentlyContinue
        if ($methods.Count -le 1) { $noMfa++ }
    }
    $report += [PSCustomObject]@{
        Check   = "Users without MFA (sample)"
        Value   = $noMfa
        Status  = if ($noMfa -eq 0) { "OK" } else { "WARNING" }
        Detail  = "Utenti nel campione senza MFA registrato"
    }

    # 4. Verificare Conditional Access policies
    $caPolicies = Get-MgIdentityConditionalAccessPolicy
    $report += [PSCustomObject]@{
        Check   = "CA Policies Active"
        Value   = ($caPolicies | Where-Object State -eq "enabled").Count
        Status  = if (($caPolicies | Where-Object State -eq "enabled").Count -ge 3) { "OK" }
                  else { "WARNING" }
        Detail  = "Minimo raccomandato: MFA all users, Block legacy auth, Block risky locations"
    }

    # 5. Verificare legacy auth block
    $legacyBlock = $caPolicies | Where-Object {
        $_.Conditions.ClientAppTypes -contains "other" -and
        $_.GrantControls.BuiltInControls -contains "block"
    }
    $report += [PSCustomObject]@{
        Check   = "Legacy Auth Blocked"
        Value   = if ($legacyBlock) { "Yes" } else { "No" }
        Status  = if ($legacyBlock) { "OK" } else { "CRITICAL" }
        Detail  = "Legacy auth (IMAP, POP3, SMTP) deve essere bloccata"
    }

    Write-Host "`n=== AUDIT ENTRA ID ===" -ForegroundColor Cyan
    $report | Format-Table Check, Value, Status, Detail -AutoSize

    return $report
}
```

### Script: Report Sign-In Activity

```powershell
# Report login falliti e sospetti nelle ultime 24 ore
function Get-SuspiciousSignIns {
    param([int]$Hours = 24)

    Connect-MgGraph -Scopes "AuditLog.Read.All"

    $startTime = (Get-Date).AddHours(-$Hours).ToString("yyyy-MM-ddTHH:mm:ssZ")

    # Login falliti
    $failedSignIns = Get-MgAuditLogSignIn -Filter `
        "status/errorCode ne 0 and createdDateTime ge $startTime" `
        -Top 100 |
        Select-Object UserDisplayName, UserPrincipalName, AppDisplayName,
            @{N='IP';E={$_.IPAddress}},
            @{N='Location';E={"$($_.Location.City), $($_.Location.CountryOrRegion)"}},
            @{N='Error';E={$_.Status.ErrorCode}},
            @{N='Reason';E={$_.Status.FailureReason}},
            CreatedDateTime

    Write-Host "Login falliti nelle ultime $Hours ore: $($failedSignIns.Count)"
    $failedSignIns | Format-Table -AutoSize

    # Raggruppare per IP (potenziale attacco brute force)
    $bruteForce = $failedSignIns | Group-Object IP |
        Where-Object Count -gt 5 |
        Sort-Object Count -Descending
    if ($bruteForce) {
        Write-Host "`n!!! POTENZIALE BRUTE FORCE !!!" -ForegroundColor Red
        $bruteForce | Format-Table Count, Name
    }

    # Raggruppare per utente (potenziale account compromesso)
    $targeted = $failedSignIns | Group-Object UserPrincipalName |
        Where-Object Count -gt 3 |
        Sort-Object Count -Descending
    if ($targeted) {
        Write-Host "`n!!! UTENTI BERSAGLIO !!!" -ForegroundColor Yellow
        $targeted | Format-Table Count, Name
    }

    return $failedSignIns
}
```

---

## Scenari Reali Enterprise

### Scenario 1: Migrazione da ADFS a PHS + Seamless SSO

```
CONTESTO: Azienda con 3000 utenti, ADFS farm (2 server + WAP)
PROBLEMA: Infrastruttura ADFS costosa da mantenere, single point of failure
OBIETTIVO: Migrare a PHS + Seamless SSO (cloud-managed, resiliente)

PIANO DI MIGRAZIONE (3 settimane):

SETTIMANA 1: PREPARAZIONE
- Abilitare PHS nel wizard Azure AD Connect (può coesistere con ADFS)
- Il sync delle password hash inizia in background
- Verificare che tutti gli utenti hanno UPN routable
- Configurare Seamless SSO nell'Azure AD Connect wizard
- Deployare GPO per Intranet Zone (Seamless SSO)

SETTIMANA 2: TEST E STAGED ROLLOVER
- Azure AD Connect: cambiare sign-in method da Federation a PHS
  (Staged Rollover: gruppo pilota prima, poi tutti)
- Testare con gruppo IT:
  - Login M365 funziona? → PHS
  - SSO dalla rete aziendale funziona? → Seamless SSO
  - SSPR funziona? → Password Writeback
- Testare con 100 utenti early adopters

SETTIMANA 3: CUTOVER COMPLETO
- Convertire il dominio da Federated a Managed:
  Set-MsolDomainAuthentication -DomainName "contoso.com" `
      -Authentication Managed
- Verificare che TUTTI gli utenti possono autenticarsi
- Monitorare sign-in logs per errori
- Dopo 2 settimane senza problemi: decommissionare ADFS

RISULTATO:
- Costo infrastruttura: da 2 server ADFS + 2 WAP → 0 server
- Resilienza: PHS funziona anche se AD on-premise è down
- MFA: gestito via Conditional Access (non più ADFS MFA adapter)
- SSO: Seamless SSO nella rete aziendale, trasparente per l'utente
```

### Scenario 2: Implementazione Zero Trust con Conditional Access

```
CONTESTO: Azienda con 500 utenti, M365 E5, lavoro ibrido
OBIETTIVO: Implementare Zero Trust progressivamente

FASE 1: IDENTITÀ (Mese 1)
- MFA per tutti gli utenti (Conditional Access)
- Blocco legacy authentication
- SSPR + Password Writeback
- Number Matching abilitato su Authenticator
- Break-glass accounts configurati e testati

FASE 2: DISPOSITIVI (Mese 2)
- Hybrid Azure AD Join per tutti i PC corporate
- Intune enrollment + compliance policy
- CA policy: "Require compliant device" per Office 365
- BitLocker enforced via Intune

FASE 3: ACCESSO CONDIZIONALE AVANZATO (Mese 3)
- Named locations: rete aziendale trusted
- CA: MFA obbligatoria da reti non trusted
- CA: Block access da paesi non autorizzati
- CA: Require managed device per accesso a SharePoint
- Session control: sign-in frequency 12h

FASE 4: IDENTITÀ PRIVILEGIATA (Mese 4)
- PIM per tutti i ruoli admin
- Authentication Strength: phishing-resistant per admin
- Access Reviews trimestrali
- Identity Protection: risk-based policies

FASE 5: MONITORING (Continuo)
- Alert per risky sign-ins
- Alert per risky users
- Sign-in analytics dashboard
- Monthly compliance report
```

---

## Best Practices

1. **Password Hash Sync + Seamless SSO**: la combinazione più resiliente per hybrid identity. Funziona anche se AD on-premise è down
2. **Conditional Access come pilastro Zero Trust**: ogni accesso è valutato. MFA + device compliance + location
3. **Bloccare legacy auth**: protocolli legacy (IMAP, POP3, SMTP basic auth) non supportano MFA e sono vettore di attacco principale
4. **Break-glass accounts**: 2 account di emergenza esclusi da TUTTE le policy CA, monitorati con alert, password in cassaforte fisica
5. **SSPR + Password Writeback**: riduce il carico dell'helpdesk e migliora la user experience, ROI immediato
6. **Monitorare sync**: alert se Azure AD Connect non sincronizza da > 3 ore; configurare Health Agent per monitoring nel portale
7. **UPN routable**: assicurarsi che l'UPN degli utenti sia un dominio pubblico verificato (es. user@contoso.com, non user@corp.local)
8. **Number Matching su Authenticator**: abilitare sempre per prevenire MFA fatigue attacks (MFA bombing)
9. **PIM per ruoli privilegiati**: mai assegnare ruoli admin come permanenti; usare Eligible con attivazione just-in-time
10. **Report-Only prima di Enforce**: ogni policy CA va testata in Report-Only per almeno 1 settimana prima dell'enforcement
11. **Authentication Strengths per admin**: richiedere FIDO2 o Windows Hello (phishing-resistant) per tutti gli admin
12. **Access Reviews trimestrali**: verificare che gli assegnamenti privilegiati siano ancora necessari
13. **IdFix prima del primo sync**: correggere errori attributi in AD prima di avviare Azure AD Connect
14. **Azure AD Connect su server dedicato**: non installare su un DC; il server deve essere domain member, non DC
15. **CAE (Continuous Access Evaluation)**: verificare che le app supportino CAE per revoca token real-time

---

## Troubleshooting

**1. "Azure AD Connect non sincronizza"** → Verificare servizio ADSync (`Get-Service ADSync`), controllare `Get-ADSyncScheduler`. Event Viewer → Application → ADSync. Errori comuni: password account scaduta, connettività HTTPS bloccata, conflitti di attributi (duplicate UPN/ProxyAddress). Eseguire `Start-ADSyncSyncCycle -PolicyType Delta` per forzare sync.

**2. "Seamless SSO non funziona"** → Verificare: GPO per Intranet Zone applicata, computer domain-joined, ticket Kerberos valido (`klist`), Azure AD Connect SSO abilitato. Funziona solo con browser (non app native mobile). Verificare che `autologon.microsoftonline.com` sia nella Intranet Zone. Edge basato su Chromium: non usa le zone IE — Seamless SSO funziona comunque via PRT.

**3. "Conditional Access blocca utenti legittimi"** → Sign-in logs in Entra ID → filtrare per utente → tab "Conditional Access" → vedere quale policy ha bloccato e perché. Usare "Report-only" mode per testare policy prima di applicarle. Verificare che l'utente non stia usando legacy auth client.

**4. "Utente non può fare MFA registration"** → Verificare: licenza P1 o security defaults, metodo MFA consentito (Authentication Methods policy), Combined Registration abilitata. URL registrazione: https://aka.ms/mfasetup. Se la CA policy richiede MFA per registrare MFA (chicken-and-egg): creare una location trust o temporary exclusion.

**5. "dsregcmd /status mostra AzureAdJoined: NO su un device Hybrid"** → Il Hybrid Join non è completato. Verificare: SCP configurato in AD, il device raggiunge `enterpriseregistration.windows.net`, il device è sincronizzato in Entra ID (verificare in Azure Portal → Devices). Log: Event Viewer → Applications and Services → Microsoft → Windows → User Device Registration → Admin.

**6. "Errore sync: 'LargeObject' su un utente"** → Un attributo supera il limite di dimensione Entra ID. Comune: `thumbnailPhoto` > 100KB. Fix: ridurre la dimensione della foto in AD (`Set-ADUser -Clear thumbnailPhoto`). Alternativa: configurare Azure AD Connect per non sincronizzare l'attributo (Sync Rules Editor).

**7. "MFA fatigue: utenti ricevono prompt MFA ripetuti non richiesti"** → Potenziale attacco MFA bombing. Abilitare Number Matching su Authenticator (l'attaccante non conosce il numero). Abilitare "Show additional context" (mostra app e location). Verificare sign-in logs per tentativi sospetti. Revocare sessioni utente: `Revoke-MgUserSignInSession`.

**8. "App Proxy: errore 'This corporate app can't be accessed'"** → Verificare: Connector attivo e connesso (Entra ID → Application Proxy → Connectors), URL interna raggiungibile dal server del Connector, certificato SSL valido sull'app interna. Se SSO Kerberos: verificare SPN configurato e KCD nel Connector.

**9. "Password Writeback: errore 33004 (insufficient permissions)"** → L'account del servizio Azure AD Connect non ha i permessi per resettare le password nell'OU dell'utente. Fix: assegnare "Reset Password" e "Change Password" sull'OU interessata all'account del connettore AD. Usare il wizard Azure AD Connect → "Review required permissions".

**10. "Conditional Access: MFA richiesta in loop infinito"** → L'app non supporta MFA claim handshake correttamente. Comune con app legacy on-premise. Fix: usare App Proxy con pre-authentication Entra ID (gestisce MFA prima di raggiungere l'app). Alternativa: escludere l'app dalla policy CA e proteggerla diversamente (IP restriction).

**11. "PHS: password change on-premise non si riflette nel cloud"** → Il sync della password avviene ogni 2 minuti (separato dal delta sync ogni 30 min). Verificare: Azure AD Connect Health → Sync → Password Hash Synchronization. Se l'errore persiste: verificare che il Password Hash Sync sia abilitato nel wizard, e che la porta 443 verso Azure sia aperta.

**12. "Identity Protection: troppi falsi positivi su 'unfamiliar sign-in properties'"** → Comune nelle prime settimane — il modello ML ha bisogno di 14 giorni per costruire il baseline. Dismissare i falsi positivi: `Invoke-MgDismissRiskyUser`. Configurare la risk policy con threshold "High" invece di "Medium" per ridurre i falsi positivi.

**13. "Break-glass account: come verificare che funzioni?"** → Test trimestrale: (1) Da un browser in incognito, (2) Accedere con le credenziali break-glass, (3) Verificare che NESSUNA CA policy blocchi, (4) Verificare accesso completo al portale Azure. Dopo il test: cambiare la password. Verificare alert: sign-in del break-glass dovrebbe generare una notifica immediata.

**14. "Azure AD Connect Cloud Sync vs Classic: quale scegliere per nuova installazione?"** → Cloud Sync se: nuovo deploy, scenario semplice (PHS, no PTA/Federation), multi-forest, vuoi gestione cloud-first. Classic se: servono PTA o Federation, device writeback, Exchange hybrid complesso, filtering attributi avanzato, > 150.000 oggetti con SQL custom. Per la maggior parte dei nuovi deploy, Cloud Sync è sufficiente.

**15. "Errore tenant: 'AADSTS50011 - reply URL does not match'"** → L'URL di risposta configurata nell'app registration non corrisponde a quella usata dall'applicazione. Entra ID → App registrations → [app] → Authentication → redirect URIs. Aggiungere l'URL esatta dell'app (incluso trailing slash se presente). Errore comune dopo cambio dominio o migrazione app.

---

## Troubleshooting Avanzato — Guida Strutturata

### Errori di Sync — Albero Decisionale

```
PROBLEMA: oggetti non sincronizzati da AD a Entra ID

├── L'oggetto è nella OU sincronizzata?
│   ├── NO → Spostare l'oggetto nella OU corretta o aggiungere l'OU al filtering
│   └── SÌ → continua ↓
│
├── L'oggetto ha attributi validi (IdFix)?
│   ├── NO → Correggere con IdFix (UPN non routable, caratteri speciali, duplicati)
│   └── SÌ → continua ↓
│
├── L'oggetto è filtrato da una Sync Rule custom?
│   ├── SÌ → Sync Rules Editor → verificare la regola → cloudFiltered
│   └── NO → continua ↓
│
├── L'oggetto ha un conflitto di attributi?
│   ├── "AttributeValueMustBeUnique" → cercare duplicati UPN/ProxyAddress
│   ├── "InvalidSoftMatch" → verificare che proxyAddresses e UPN corrispondano
│   └── Nessun errore → continua ↓
│
├── Il servizio ADSync è in esecuzione?
│   ├── NO → Start-Service ADSync → verificare Event Viewer per errori
│   └── SÌ → continua ↓
│
├── L'ultimo sync ha avuto successo?
│   ├── NO → Get-ADSyncRunStepResult → analizzare errori specifici
│   └── SÌ → L'oggetto potrebbe essere in uno stato di pending
│       → Forzare: Start-ADSyncSyncCycle -PolicyType Delta
│       → Se persiste: Start-ADSyncSyncCycle -PolicyType Initial (con cautela)
│
└── Controllare Azure AD Connect Health nel portale per alert e raccomandazioni
```

### SSO Failures — Diagnostica

```
PROBLEMA: l'utente riceve prompt di credenziali nella rete aziendale

├── Il device è domain-joined?
│   ├── NO → Seamless SSO richiede domain join. Usare PRT se Azure AD Joined.
│   └── SÌ → continua ↓
│
├── L'utente usa un browser supportato?
│   ├── Edge Chromium → SSO via PRT (non Kerberos). Verificare dsregcmd /status → AzureAdPrt: YES
│   ├── IE / Edge Legacy → Verificare Intranet Zone
│   ├── Chrome → Verificare AuthServerAllowlist policy
│   ├── Firefox → Verificare network.negotiate-auth.trusted-uris
│   └── Altro → potrebbe non supportare Seamless SSO
│
├── La GPO Intranet Zone è applicata?
│   ├── Verificare: gpresult /r → cercare "Site to Zone Assignment"
│   └── Se mancante → applicare GPO e fare gpupdate /force
│
├── Il ticket Kerberos è presente?
│   ├── Verificare: klist → cercare ticket per autologon.microsoftonline.com
│   ├── NO → Il client non raggiunge il DC o l'account AZUREADSSOACC$ non esiste
│   └── SÌ → Il ticket potrebbe essere scaduto o la chiave non corrisponde
│       → Verificare: Get-ADComputer AZUREADSSOACC -Properties PasswordLastSet
│       → Se > 30 giorni: ruotare la chiave con Update-AzureADSSOForest
│
└── Se il device è Hybrid Joined e Edge Chromium:
    → SSO avviene via PRT, non Kerberos
    → Verificare dsregcmd /status → AzureAdPrt: YES, AzureAdPrtUpdateTime: recente
    → Se AzureAdPrt: NO → problema di device registration, non di Seamless SSO
```

### Conflitti tra Policy CA — Diagnostica

```powershell
# Quando più policy CA si applicano contemporaneamente,
# Entra ID le valuta TUTTE e applica i controlli più restrittivi.

# Esempio di conflitto:
# Policy A: "Require MFA from untrusted locations"
# Policy B: "Require compliant device for Office 365"
# Risultato: l'utente da rete non trusted su device non compliant
# deve soddisfare ENTRAMBE: MFA + compliant device

# Per diagnosticare quale policy sta causando problemi:
# 1. Sign-in logs → selezionare l'evento → tab "Conditional Access"
#    → Lista di TUTTE le policy valutate con risultato per ciascuna
#    → "Not Applied", "Success", "Failure"

# 2. What If tool (simulatore CA):
# Entra ID → Security → Conditional Access → What If
# Inserire: utente, app, location, device platform, client app
# → Mostra quali policy si applicherebbero e con quale risultato

# 3. Report-Only mode:
# Tutte le nuove policy dovrebbero iniziare in Report-Only
# per almeno 7 giorni prima dell'enforcement
# I risultati Report-Only appaiono nei sign-in logs
# senza impatto sull'utente

# Script: verificare CA policy in conflitto potenziale
Connect-MgGraph -Scopes "Policy.Read.All"
$policies = Get-MgIdentityConditionalAccessPolicy -Filter "state eq 'enabled'"
foreach ($p in $policies) {
    [PSCustomObject]@{
        Name = $p.DisplayName
        Users = ($p.Conditions.Users.IncludeUsers -join ", ")
        Apps = ($p.Conditions.Applications.IncludeApplications -join ", ")
        Grant = ($p.GrantControls.BuiltInControls -join ", ")
        State = $p.State
    }
} | Format-Table -AutoSize
```

### Device Registration Issues — Diagnostica

```powershell
# Problemi comuni di device registration e relative soluzioni:

# 1. Hybrid Join fallisce silenziosamente
# Log: Event Viewer → Applications and Services → Microsoft →
#   Windows → User Device Registration → Admin
# Errori comuni:
# - Event 204: "Discovery failed" → il device non trova il SCP in AD
# - Event 304: "Device join not completed" → problema di connettività
# - Event 360: "Server is busy" → troppi device che tentano contemporaneamente

# 2. Device appare come "Pending" in Entra ID
# → La registrazione è iniziata ma non completata
# → Cause: sync delay (aspettare il prossimo ciclo Azure AD Connect)
# → Fix: Start-ADSyncSyncCycle -PolicyType Delta poi attendere 5 minuti

# 3. PRT non emesso dopo Hybrid Join
dsregcmd /status
# Verificare:
# AzureAdJoined: YES (deve essere YES)
# AzureAdPrt: NO → il PRT non è stato emesso
# → Causa più comune: l'utente deve fare logout/login dopo il join
# → Oppure: il device non raggiunge login.microsoftonline.com
# → Oppure: l'orologio del device è sfasato (> 5 minuti di differenza)

# 4. "Something went wrong" durante Azure AD Join
# → Verificare che l'utente abbia il permesso di fare join:
# Entra ID → Devices → Device settings
# → "Users may join devices to Azure AD": All / Selected / None
# → "Maximum number of devices per user": verificare non sia raggiunto (default 50)
```

---

## FAQ

**Q1: Qual è la differenza tra Security Defaults e Conditional Access?**
Security Defaults è un set di policy MFA predefinite, gratuite, non personalizzabili. Abilita MFA per tutti, blocca legacy auth, protegge gli admin. Conditional Access (richiede P1) è completamente personalizzabile: definisci le condizioni esatte (utente, app, location, device, rischio) e le azioni. Quando attivi Conditional Access, devi disabilitare Security Defaults. Per PMI senza P1: Security Defaults è un ottimo punto di partenza.

**Q2: Posso usare PHS e PTA contemporaneamente?**
No, sono mutuamente esclusivi come metodo di sign-in primario. Ma PHS può funzionare come fallback per PTA: se gli agent PTA sono tutti offline, PHS prende il sopravvento (richiede abilitazione nel wizard). La raccomandazione è usare PHS come metodo primario — è più resiliente, più semplice, e supporta Identity Protection (leak detection).

**Q3: Quanti agent PTA devo installare?**
Minimo 3 agent per alta disponibilità (su server diversi). Ogni agent gestisce circa 400 autenticazioni al secondo. Per 1000 utenti: 3 agent sono più che sufficienti. Gli agent non richiedono server dedicati — possono coesistere con altri ruoli. Installare sempre su server nel dominio AD, mai su DC.

**Q4: Come gestire gli account di servizio (service accounts) con Conditional Access?**
Gli account di servizio (non interattivi) non possono fare MFA. Opzioni: (1) Escluderli dalla policy CA con una Named Location (IP del server). (2) Usare Managed Identities in Azure (nessuna password). (3) Usare Workload Identities con Conditional Access for Workload Identities (anteprima). (4) Come minimo: escluderli dalla policy CA ma monitorare gli accessi con alert.

**Q5: Qual è il modo migliore per bloccare l'accesso da paesi specifici?**
Conditional Access → Named Locations → creare "Blocked Countries" con i paesi da bloccare → CA policy: Include all users, Include all cloud apps, Conditions → Locations → Include "Blocked Countries" → Grant: Block. ATTENZIONE: i VPN e i proxy possono bypassare i country block. Non fare affidamento solo sul GeoIP per la sicurezza.

**Q6: Come migrare da per-user MFA a Conditional Access MFA?**
(1) Creare la policy CA con MFA in Report-Only mode. (2) Verificare per 1 settimana che copra tutti gli utenti. (3) Abilitare la policy CA (On). (4) Disabilitare il per-user MFA per tutti gli utenti (Entra ID → Users → Per-user MFA → stato: Disabled). (5) Verificare che il MFA funzioni tramite CA. L'utente non nota differenze — i metodi MFA registrati restano gli stessi.

**Q7: Come funzionano i break-glass accounts in pratica?**
Creazione: 2 account cloud-only (non sincronizzati da AD on-premise), Global Admin, password 30+ caratteri, MFA con hardware FIDO2 key conservata in cassaforte. Configurazione: esclusi da TUTTE le policy CA (per nome, non per gruppo). Monitoraggio: alert automatico su ogni sign-in (Log Analytics o alert rule in Azure Monitor). Test: login trimestrale per verificare funzionamento. Uso: solo quando tutti gli admin normali sono bloccati.

**Q8: Come gestire Conditional Access per utenti guest (B2B)?**
Creare policy CA specifica per guest: Conditions → Users → Include "Guest or external users". Consigliato: MFA obbligatoria, device compliance non applicabile (non gestito da noi), limiterare le app accessibili (solo quelle necessarie per la collaborazione). MFA trust: se il tenant del guest ha già MFA, Entra ID può accettare il claim MFA del tenant home (cross-tenant access settings).

**Q9: PIM: quanto tempo dare per l'attivazione di un ruolo?**
Dipende dal ruolo e dal contesto. Global Admin: max 2 ore (per interventi di emergenza). Exchange Admin: 4 ore (per manutenzione pianificata). Helpdesk Admin: 8 ore (per turno lavorativo). Regola: dare il tempo minimo necessario per completare il task. Se servono attivazioni più lunghe: valutare se il ruolo è troppo ampio e dovrebbe essere diviso.

**Q10: Come proteggere Entra ID dal compromesso di AD on-premise?**
(1) Non sincronizzare account Tier 0 (Domain Admins) con Azure AD Connect — gestire admin cloud separatamente. (2) Usare PHS (non PTA/Federation) — se AD on-premise è compromesso, l'attaccante non può autenticarsi nel cloud tramite PTA/ADFS. (3) Abilitare Identity Protection per detection di credenziali compromesse. (4) Conditional Access: richiedere device compliant per accesso admin al portale Azure. (5) Monitorare sync: alert se vengono sincronizzati oggetti in OU non previste.

**Q11: Azure AD Application Proxy vs VPN: quando usare quale?**
App Proxy: per applicazioni web singole, accesso da device non gestiti, pre-authentication con MFA. Nessuna installazione client. VPN: per accesso a rete completa, applicazioni non-web (RDP, file share, thick client), quando servono molte risorse on-premise. Always-On VPN: per device managed che devono essere sempre nella rete aziendale. Trend: sostituire VPN con App Proxy + Azure Virtual Desktop dove possibile.

**Q12: Come garantire che Entra ID Connect sia sempre aggiornato?**
Azure AD Connect ha auto-update abilitato di default. Verificare: `Get-ADSyncAutoUpgrade`. Se l'auto-update fallisce (versione troppo vecchia, customizzazioni): aggiornare manualmente scaricando l'ultima versione. Azure AD Connect Health (nel portale) mostra alert se la versione è obsoleta. Pianificare aggiornamento manuale se la versione ha più di 6 mesi.

**Q13: Come gestire la transizione da Windows Hello for Business PIN a FIDO2?**
Le due soluzioni coesistono. Windows Hello PIN è legato al dispositivo (funziona solo su quel PC). FIDO2 è portabile (funziona su qualsiasi dispositivo). Per admin: migrare a FIDO2 (phishing-resistant, portabile). Per utenti standard: Windows Hello PIN è sufficiente e più comodo. Non servono entrambi — scegliere in base al profilo di rischio.

**Q14: Cosa succede se Azure AD Connect va offline per un giorno?**
Con PHS: nulla di critico. Le password hash sincronizzate permettono il login cloud. Le modifiche fatte in AD on-premise (nuovi utenti, gruppi, password change) non si riflettono nel cloud fino al ripristino del sync. Con PTA: il login cloud continua a funzionare (gli agent PTA sono separati dal sync). Con Federation (ADFS): nessun impatto (ADFS non dipende da Azure AD Connect per l'autenticazione). Allarme: configurare alert se sync > 3 ore di ritardo.

**Q15: Come implementare il passwordless authentication?**
Tre approcci, implementabili gradualmente: (1) Windows Hello for Business: biometrico + PIN legato al device, per workstation corporate. (2) Microsoft Authenticator passwordless: notifica push con number matching, senza digitare password. (3) FIDO2 Security Key: chiave hardware, massima sicurezza, portabile. Piano: iniziare con Authenticator passwordless (più semplice), poi FIDO2 per admin. La password non viene rimossa — viene nascosta dal login (l'utente non la usa mai).

---

## Esercizi

### Domande a Risposta Aperta

**1.** Descrivi il flusso completo di autenticazione Seamless SSO dall'apertura del browser da parte dell'utente fino all'emissione del token OAuth 2.0 da parte di Entra ID. Specifica il ruolo di Kerberos, dell'account AZUREADSSOACC$ e della Intranet Zone nel processo.

**2.** Un'azienda con 2000 utenti deve scegliere tra PHS, PTA e Federation per la propria identità ibrida. L'azienda non ha requisiti di smart card o claim rules custom e vuole massimizzare la resilienza. Argomenta la raccomandazione motivando ogni aspetto: resilienza, sicurezza (leaked credential detection), complessità operativa e costo infrastrutturale.

**3.** Progetta un set di almeno 5 Conditional Access policies per un'azienda che sta adottando Zero Trust. Per ciascuna policy, specifica: nome, assignments (utenti, app, condizioni), grant controls, session controls, ordine di deployment (Report-Only → On) e giustificazione di sicurezza.

**4.** Spiega la differenza tra permessi Delegated e Application in una registrazione app Entra ID. Fornisci un esempio concreto di quando useresti ciascun tipo, descrivendo il flusso OAuth 2.0 appropriato e le implicazioni di sicurezza del consent model.

**5.** Un utente segnala che non riesce ad accedere a Microsoft 365 dal proprio PC aziendale nella rete interna. Il PC è Hybrid Azure AD Joined e Conditional Access richiede un dispositivo conforme. Descrivi il processo di troubleshooting passo per passo, indicando i comandi diagnostici (`dsregcmd`, `klist`, sign-in logs) e le possibili cause di fallimento.

### Vero o Falso (motivare la risposta)

**6.** Entra ID utilizza Organizational Units (OU) come Active Directory DS per organizzare gli oggetti e applicare policy di sicurezza.

**7.** Con Password Hash Sync abilitato, se l'Active Directory on-premise subisce un'interruzione completa, gli utenti possono ancora autenticarsi alle risorse cloud Microsoft 365.

**8.** Un'applicazione registrata in Entra ID con permessi Application (es. User.Read.All) richiede sempre un utente autenticato per funzionare.

**9.** Il flusso Device Code di OAuth 2.0 è considerato sicuro e non necessita di restrizioni particolari tramite Conditional Access.

**10.** PIM (Privileged Identity Management) permette di assegnare ruoli amministrativi come "Eligible", richiedendo all'utente di attivare il ruolo on-demand con giustificazione e MFA.

### Scenari Pratici

**11.** La tua azienda ha appena scoperto che 15 utenti hanno ricevuto un'email di phishing e 3 di loro hanno inserito le proprie credenziali in un sito fraudolento. Descrivi la procedura di incident response utilizzando gli strumenti di Entra ID: Identity Protection, Conditional Access, sign-in logs, revoca sessioni e SSPR. Elenca le azioni in ordine di priorità.

**12.** Un'azienda con sede in Italia e filiale in Germania deve configurare B2B Collaboration con un partner esterno (partner.com). Il partner ha un proprio tenant Entra ID con MFA configurato. Configura: (a) Cross-tenant access settings per fidarsi del MFA del partner, (b) un processo per invitare 50 utenti guest, (c) una Conditional Access policy specifica per gli utenti guest, (d) un processo di Access Review trimestrale per i guest.

**13.** Stai pianificando la migrazione da AD FS a PHS + Seamless SSO per un'azienda con 5000 utenti e 12 Relying Party Trust configurati in AD FS (6 applicazioni SAML, 4 WS-Federation, 2 con claim rules custom complesse). Descrivi il piano di migrazione fase per fase, specificando come gestire le applicazioni con claim rules custom e come usare la Staged Rollout per minimizzare il rischio.

**14.** Il tuo Azure AD Connect mostra l'errore "AttributeValueMustBeUnique" per l'attributo proxyAddresses su 23 utenti. Descrivi: (a) come identificare gli utenti coinvolti e i valori duplicati, (b) come risolvere il conflitto senza impattare la posta esistente, (c) come prevenire il problema in futuro con strumenti come IdFix e convenzioni di naming.

**15.** Un amministratore ha configurato una Conditional Access policy "Require MFA for all users on all cloud apps" ma non ha escluso i break-glass accounts. L'unico Global Administrator è bloccato perché non riesce a completare l'MFA (ha perso il telefono). Descrivi: (a) come accedere al tenant usando i break-glass accounts (se esistono), (b) come accedere se i break-glass accounts non esistono o sono anch'essi bloccati, (c) quali azioni preventive avrebbero evitato questa situazione.

---

## Auto-valutazione

Rispondi mentalmente o per iscritto per verificare la comprensione:

1. Sai spiegare perché PHS è più resiliente di PTA senza consultare le note?
2. Riesci a elencare almeno 5 componenti di una Conditional Access policy?
3. Conosci la differenza tra Entra Registered, Entra Joined e Hybrid Entra Joined?
4. Sai descrivere il workflow PIM per l'attivazione di un ruolo privilegiato?
5. Riesci a diagnosticare un problema di Seamless SSO partendo da `dsregcmd /status` e `klist`?
6. Sai la differenza tra permessi Delegated e Application in un'app registration?
7. Conosci almeno 3 metodi MFA phishing-resistant?
8. Sai configurare un diagnostic setting per inviare i log Entra ID a Log Analytics?

Se hai risposto "no" a 3 o più domande, rileggi le sezioni corrispondenti prima di procedere al modulo successivo.

---

## Letture Primarie Consigliate

1. **What is Microsoft Entra ID?** — https://learn.microsoft.com/entra/fundamentals/whatis (consultato: 2026-05-23)
2. **Compare Active Directory to Entra ID** — https://learn.microsoft.com/entra/fundamentals/compare-with-active-directory (consultato: 2026-05-23)
3. **What is Microsoft Entra Connect?** — https://learn.microsoft.com/entra/identity/hybrid/connect/whatis-azure-ad-connect (consultato: 2026-05-23)
4. **Choose the right authentication method** — https://learn.microsoft.com/entra/identity/hybrid/connect/choose-ad-authn (consultato: 2026-05-23)
5. **What is Conditional Access?** — https://learn.microsoft.com/entra/identity/conditional-access/overview (consultato: 2026-05-23)
6. **Common Conditional Access policies** — https://learn.microsoft.com/entra/identity/conditional-access/concept-conditional-access-policy-common (consultato: 2026-05-23)
7. **Authentication methods in Entra ID** — https://learn.microsoft.com/entra/identity/authentication/concept-authentication-methods (consultato: 2026-05-23)
8. **What is Identity Protection?** — https://learn.microsoft.com/entra/id-protection/overview-identity-protection (consultato: 2026-05-23)
9. **What is PIM?** — https://learn.microsoft.com/entra/id-governance/privileged-identity-management/pim-configure (consultato: 2026-05-23)
10. **Microsoft identity platform and OAuth 2.0** — https://learn.microsoft.com/entra/identity-platform/v2-oauth2-auth-code-flow (consultato: 2026-05-23)
11. **What is B2B collaboration?** — https://learn.microsoft.com/entra/external-id/what-is-b2b (consultato: 2026-05-23)
12. **Microsoft Entra seamless SSO** — https://learn.microsoft.com/entra/identity/hybrid/connect/how-to-connect-sso-how-it-works (consultato: 2026-05-23)
13. **Migrate from federation to cloud authentication** — https://learn.microsoft.com/entra/identity/hybrid/connect/migrate-from-federation-to-cloud-authentication (consultato: 2026-05-23)
14. **Microsoft Graph PowerShell overview** — https://learn.microsoft.com/powershell/microsoftgraph/overview (consultato: 2026-05-23)
15. **Entra ID sign-in logs** — https://learn.microsoft.com/entra/identity/monitoring-health/concept-sign-ins (consultato: 2026-05-23)
16. **Manage emergency access accounts** — https://learn.microsoft.com/entra/identity/role-based-access-control/security-emergency-access (consultato: 2026-05-23)

---

## Collegamenti Incrociati

| Modulo | Collegamento | Rilevanza |
|--------|-------------|-----------|
| `01-active-directory.md` | Fondamenti AD DS, OU, GPO, Kerberos, LDAP — prerequisiti per comprendere l'identità ibrida | Prerequisito diretto |
| `26-intune-gestione-moderna.md` | MDM/MAM, compliance policies, co-management — complemento per device management | Device identity e compliance |
| `30-identita-ibrida-azure-ad-dettaglio.md` | Approfondimento tecnico su scenari avanzati di identità ibrida | Estensione diretta di questo modulo |
| `32-intune-mdm-mam.md` | Dettagli su Mobile Device Management e Mobile Application Management | Complemento per Conditional Access device grant |
| `25-active-directory-design-avanzato.md` | Multi-domain, multi-forest, trust design — impatta sync e filtering | Architettura AD pre-sync |
| `33-multi-forest-ad-trust.md` | Trust cross-forest, multi-forest sync con Entra Connect | Scenari sync complessi |
| `28-pki-certificati-guida-completa.md` | PKI interna, smart card, certificate-based auth in Entra ID | CBA e certificati MFA |
| `05-sicurezza-windows.md` | Sicurezza Windows, BitLocker, WDAC — complemento per device compliance | Compliance e hardening device |
| `22-powershell-scripting-avanzato.md` | PowerShell avanzato per automazione Entra ID con Microsoft.Graph | Strumento operativo |
| `34-disaster-recovery-ad-pki.md` | DR per AD e PKI — impatto su identità ibrida in caso di disastro | Resilienza e continuità |

---

## Glossario Locale

| Termine | Definizione |
|---------|------------|
| **Entra ID** | Servizio di identità cloud di Microsoft, precedentemente Azure Active Directory (Azure AD). Gestisce autenticazione e autorizzazione per M365, Azure e app SaaS. |
| **Tenant** | Istanza dedicata di Entra ID per un'organizzazione. Ogni tenant ha un ID univoco e un dominio `*.onmicrosoft.com`. |
| **PHS (Password Hash Sync)** | Metodo di autenticazione ibrida in cui l'hash della password AD viene sincronizzato in Entra ID. Il login cloud non dipende dall'infrastruttura on-premise. |
| **PTA (Pass-through Authentication)** | Metodo di autenticazione ibrida in cui la password viene validata in real-time contro AD on-premise tramite agent leggeri. |
| **Federation** | Metodo di autenticazione in cui l'autenticazione è delegata a un Identity Provider esterno (es. AD FS). Deprecato per nuovi deploy. |
| **Entra Connect** | Tool di sincronizzazione che replica utenti, gruppi e attributi da AD DS on-premise a Entra ID. Precedentemente Azure AD Connect. |
| **Seamless SSO** | Funzionalità che consente login automatico alle risorse cloud da device domain-joined nella rete aziendale, sfruttando ticket Kerberos. |
| **PRT (Primary Refresh Token)** | Token emesso dopo l'autenticazione su un device Azure AD Joined o Hybrid Joined. Fornisce SSO a tutte le risorse cloud senza re-autenticazione. |
| **Conditional Access (CA)** | Motore di policy di Entra ID che valuta condizioni (utente, device, location, rischio) per decidere se concedere, bloccare o richiedere controlli aggiuntivi per l'accesso. |
| **Break-glass account** | Account di emergenza cloud-only con ruolo Global Administrator, escluso da tutte le policy CA, usato solo quando tutti gli admin normali sono bloccati. |
| **PIM (Privileged Identity Management)** | Servizio Entra ID P2 che gestisce l'accesso privilegiato con attivazione just-in-time, MFA, giustificazione e approvazione. |
| **Identity Protection** | Servizio Entra ID P2 che usa ML per rilevare rischi su utenti e sign-in (credenziali compromesse, travel impossibile, ecc.) e automatizzare la risposta. |
| **FIDO2** | Standard di autenticazione passwordless basato su chiavi hardware (es. YubiKey). Resistente al phishing perché la chiave crittografica è legata al dominio. |
| **App Registration** | Definizione globale di un'applicazione in Entra ID: client ID, redirect URI, permessi API, certificati/secret. |
| **Enterprise Application** | Istanza locale (service principal) di un'applicazione nel tenant, con assegnamenti utenti, SSO config e policy CA applicate. |
| **B2B Collaboration** | Funzionalità che consente di invitare utenti esterni (guest) nel tenant per accedere a risorse condivise. L'utente guest si autentica nel proprio tenant di origine. |
| **Cross-tenant access settings** | Configurazioni che controllano come utenti e app di altri tenant Entra ID possono accedere al proprio tenant (inbound) e come i propri utenti possono accedere ad altri tenant (outbound). |
| **CAE (Continuous Access Evaluation)** | Meccanismo che consente la revoca in near-real-time dei token di accesso quando cambiano le condizioni (utente disabilitato, password cambiata, policy CA modificata). |
| **Authentication Strength** | Funzionalità CA che consente di specificare QUALI metodi MFA sono accettabili per una policy (es. solo FIDO2, solo phishing-resistant). |
| **SCP (Service Connection Point)** | Oggetto in AD DS (nella partition di Configuration) che indica ai client domain-joined quale tenant Entra ID usare per Hybrid Join e Seamless SSO. |
| **KQL (Kusto Query Language)** | Linguaggio di query usato in Azure Log Analytics e Microsoft Sentinel per analizzare log di Entra ID, sign-in, audit e altri dati di sicurezza. |
| **SSPR (Self-Service Password Reset)** | Funzionalità che consente agli utenti di resettare la propria password senza contattare l'helpdesk. Con Password Writeback, la nuova password viene scritta in AD on-premise. |
| **Administrative Unit (AU)** | Container logico in Entra ID per la delega amministrativa. Consente di limitare lo scope di un ruolo admin a un sottoinsieme di utenti, gruppi o dispositivi. |
| **Staged Rollout** | Funzionalità che consente di migrare gradualmente gruppi di utenti da Federation a Managed authentication (PHS o PTA) senza convertire l'intero dominio. |
| **IdFix** | Tool Microsoft che analizza gli attributi degli oggetti AD DS e identifica errori (UPN non routable, caratteri non validi, duplicati) che causerebbero problemi di sync. |
