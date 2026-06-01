# Multi-Forest AD Trust — Architettura e Gestione

> **Modulo 33** · **Aggiornamento:** 2026-05-23

| Campo | Valore |
|---|---|
| **Corso** | Windows per ingegneri di sistema |
| **Fase** | 3 — Infrastruttura enterprise |
| **Modulo** | 33 — Multi-Forest AD Trust |
| **Versione** | Windows Server 2025, Windows Server 2022, Windows Server 2019, Active Directory Domain Services |
| **Livello** | Proficient (avanzato) |
| **Prerequisiti** | Padronanza di Active Directory (→ `01-active-directory.md`), progettazione AD avanzata (→ `25-active-directory-design-avanzato.md`), conoscenza DNS e Kerberos, familiarità con PowerShell e Group Policy |
| **Obiettivi di apprendimento** | 1) Classificare i sei tipi di trust AD (parent-child, tree-root, shortcut, external, forest, realm) indicando transitività, direzione e caso d'uso · 2) Configurare un forest trust end-to-end con DNS conditional forwarder, porte firewall e validazione · 3) Applicare SID filtering e selective authentication per proteggere l'accesso cross-forest · 4) Pianificare ed eseguire migrazioni inter-forest con ADMT, SID History e security translation · 5) Diagnosticare errori di trust con nltest, netdom, Event ID e Kerberos referral tracing · 6) Implementare architetture PAM trust con shadow principal e MIM per l'amministrazione multi-forest · 7) Gestire il Name Suffix Routing e risolvere conflitti di suffisso tra forest trust multipli |
| **Tag** | `active-directory`, `trust`, `forest-trust`, `multi-forest`, `kerberos`, `sid-filtering`, `selective-authentication`, `admt`, `migrazione`, `pam-trust`, `cross-forest`, `dns`, `name-suffix-routing` |
| **Tempo stimato** | 20-28 ore (studio + esercizi + laboratorio) |
| **Ultimo aggiornamento** | 2026-05-23 |

## Idee guida

1. **External trust: relazione non transitiva tra domini specifici.**
2. **Forest trust: relazione transitiva tra tutti i domini di due forest.**
3. **Selective authentication > Forest-wide authentication per sicurezza granulare.**
4. **SID filtering attivo di default: protezione contro SID History injection.**
5. **Kerberos è il protocollo primario; NTLM solo come fallback — disabilitare se non serve.**

### Mappa Concettuale — Tipi di Trust e Direzione

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                         TRUST ACTIVE DIRECTORY — TASSONOMIA                         │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│                          ┌────────────────────┐                                      │
│                          │  TRUST AUTOMATICI   │                                      │
│                          │   (intra-forest)    │                                      │
│                          └────────┬───────────┘                                      │
│                     ┌─────────────┴──────────────┐                                   │
│                     │                            │                                    │
│          ┌──────────▼──────────┐     ┌───────────▼──────────┐                        │
│          │   Parent-Child      │     │    Tree-Root          │                        │
│          │                     │     │                       │                        │
│          │ Direzione: ↔ bidi   │     │ Direzione: ↔ bidi    │                        │
│          │ Transitivo: SI      │     │ Transitivo: SI        │                        │
│          │ Creazione: AUTO     │     │ Creazione: AUTO       │                        │
│          │ Uso: gerarchia      │     │ Uso: alberi diversi   │                        │
│          │     domini nel      │     │     nello stesso      │                        │
│          │     forest          │     │     forest            │                        │
│          └─────────────────────┘     └──────────────────────┘                        │
│                                                                                      │
│                          ┌────────────────────┐                                      │
│                          │  TRUST MANUALI      │                                      │
│                          │   (configurabili)   │                                      │
│                          └────────┬───────────┘                                      │
│          ┌────────────┬───────────┼───────────┬────────────┐                         │
│          │            │           │           │            │                          │
│  ┌───────▼───────┐ ┌──▼──────────▼──┐ ┌──────▼──────┐ ┌──▼─────────────┐            │
│  │   External    │ │    Forest      │ │  Shortcut   │ │    Realm       │            │
│  │               │ │                │ │             │ │                │            │
│  │ Dir: → o ↔    │ │ Dir: → o ↔     │ │ Dir: → o ↔  │ │ Dir: → o ↔     │            │
│  │ Trans: NO     │ │ Trans: SI      │ │ Trans: SI   │ │ Trans: CONF.   │            │
│  │ Creaz: MAN    │ │ Creaz: MAN     │ │ Creaz: MAN  │ │ Creaz: MAN     │            │
│  │               │ │                │ │             │ │                │            │
│  │ domain ↔      │ │ forest root ↔  │ │ dominio ↔   │ │ AD ↔ MIT       │            │
│  │ domain        │ │ forest root    │ │ dominio     │ │ Kerberos       │            │
│  │ (cross-forest)│ │ (cross-forest) │ │ (intra-for.)│ │ (cross-realm)  │            │
│  └───────────────┘ └────────────────┘ └─────────────┘ └────────────────┘            │
│                                                                                      │
├──────────────────────────────────────────────────────────────────────────────────────┤
│  DIREZIONE DEL TRUST vs ACCESSO RISORSE                                              │
│                                                                                      │
│   Dominio A ──trust──→ Dominio B     (A si fida di B)                                │
│   Utenti B  ──accesso──→ Risorse A   (accesso in direzione opposta)                  │
│                                                                                      │
│  SICUREZZA TRUST                                                                     │
│  ┌──────────────────┐  ┌────────────────────────┐  ┌───────────────────────┐         │
│  │  SID Filtering   │  │ Selective Authent.      │  │  Name Suffix Routing │         │
│  │  Rimuove SID     │  │ Richiede "Allowed to   │  │  Controlla quali     │         │
│  │  non appartenenti│  │ Authenticate" esplicito │  │  suffix UPN/DNS sono │         │
│  │  al trusted dom. │  │ su ogni computer target │  │  routati via trust   │         │
│  └──────────────────┘  └────────────────────────┘  └───────────────────────┘         │
│                                                                                      │
│  AUTENTICAZIONE CROSS-FOREST (Kerberos Referral)                                     │
│                                                                                      │
│  Client → DC locale (TGT) → Referral → DC forest remoto (TGS) → Risorsa             │
│                    inter-realm key                                                    │
│                                                                                      │
│  MIGRAZIONE MULTI-FOREST                                                             │
│  ┌──────────┐    ┌───────────┐    ┌───────────────┐    ┌──────────────┐              │
│  │Assessment │ →  │ADMT Setup │ →  │Migraz. pilota │ →  │Consolidament│              │
│  │DNS, Trust │    │SID Hist.  │    │Utenti, Gruppi │    │Decommission │              │
│  └──────────┘    └───────────┘    └───────────────┘    └──────────────┘              │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

## Indice

- [Architettura dei Trust in Active Directory](#architettura-dei-trust-in-active-directory)
- [Tipi di Trust](#tipi-di-trust)
- [Trust Types — Deep Dive](#trust-types--deep-dive)
- [Progettazione dell'Architettura Trust](#progettazione-dellarchitettura-trust)
- [Autenticazione Cross-Forest](#autenticazione-cross-forest)
- [Kerberos Cross-Realm — Deep Dive](#kerberos-cross-realm--deep-dive)
- [Selective Authentication](#selective-authentication)
- [SID Filtering](#sid-filtering)
- [Attacchi SID History e Contromisure](#attacchi-sid-history-e-contromisure)
- [Name Suffix Routing](#name-suffix-routing)
- [Name Suffix Routing — Configurazione Avanzata](#name-suffix-routing--configurazione-avanzata)
- [Configurazione DNS per Trust](#configurazione-dns-per-trust)
- [DNS per Multi-Forest — Scelta dell'Approccio](#dns-per-multi-forest--scelta-dellapproccio)
- [Requisiti Firewall Completi](#requisiti-firewall-completi)
- [Creazione Forest Trust Step-by-Step](#creazione-forest-trust-step-by-step)
- [Accesso Risorse Cross-Forest](#accesso-risorse-cross-forest)
- [Cross-Forest AGDLP in Pratica](#cross-forest-agdlp-in-pratica)
- [Migrazione Multi-Forest](#migrazione-multi-forest)
- [ADMT — Active Directory Migration Tool](#admt--active-directory-migration-tool)
- [ADMT — Deep Dive Operativo](#admt--deep-dive-operativo)
- [Consolidamento Domini](#consolidamento-domini)
- [Ristrutturazione Domini](#ristrutturazione-domini)
- [Cross-Forest PowerShell](#cross-forest-powershell)
- [Multi-Forest Administration — PAM Trust](#multi-forest-administration--pam-trust)
- [Global Catalog e Universal Group Membership Caching](#global-catalog-e-universal-group-membership-caching)
- [Forest Functional Levels](#forest-functional-levels)
- [Group Policy Cross-Forest](#group-policy-cross-forest)
- [Azure AD Connect con Multiple Forest](#azure-ad-connect-con-multiple-forest)
- [Monitoraggio Trust Health](#monitoraggio-trust-health)
- [Troubleshooting](#troubleshooting)
- [Troubleshooting Avanzato — Scenari Aggiuntivi](#troubleshooting-avanzato--scenari-aggiuntivi)
- [FAQ](#faq)
- [Esercizi](#esercizi)
- [Domande a Risposta Aperta](#domande-a-risposta-aperta)
- [Vero o Falso](#vero-o-falso)
- [Esercizi Scenario-Based](#esercizi-scenario-based)
- [Letture](#letture)
- [Collegamenti Incrociati](#collegamenti-incrociati)
- [Glossario](#glossario)

---

## Architettura dei Trust in Active Directory

### Concetti Fondamentali

Un **trust** (relazione di trust) in Active Directory è un collegamento logico tra due domini o forest che permette agli utenti di un dominio di autenticarsi e accedere a risorse nell'altro dominio. Il trust definisce la **direzione** dell'autenticazione e della concessione delle risorse.

Terminologia essenziale:

| Termine | Descrizione |
|---|---|
| **Trusting domain** | Il dominio che "si fida": concede accesso alle proprie risorse |
| **Trusted domain** | Il dominio "di cui ci si fida": contiene gli utenti che accedono |
| **Trust direction** | Direzione in cui fluiscono le richieste di autenticazione |
| **Resource access direction** | Direzione opposta al trust: le risorse sono nel trusting domain |

### Direzione del Trust

La direzione del trust e la direzione dell'accesso sono **opposte**:

```
Dominio A  ------trust-----→  Dominio B
(trusting)                      (trusted)

Utenti di B possono accedere a risorse di A
La "freccia" del trust punta verso il dominio di cui ci si fida
L'accesso alle risorse fluisce nella direzione opposta
```

Esempio pratico:

```
contoso.com  ------trust-----→  fabrikam.com
(trusting)                       (trusted)

Risultato: gli utenti fabrikam.com possono accedere a share/app in contoso.com
           gli utenti contoso.com NON possono accedere a risorse fabrikam.com
           (a meno di un trust bidirezionale)
```

### Trust Interni (Automatici)

All'interno di un singolo forest, AD crea automaticamente trust transitivi bidirezionali:

```
Forest contoso.com
├── contoso.com (root)
│   ├── parent-child trust (automatico, transitivo, bidirezionale)
│   ├── europe.contoso.com
│   │   ├── parent-child trust
│   │   └── italy.europe.contoso.com
│   └── asia.contoso.com
└── Tree-root trust (automatico, transitivo, bidirezionale)
    └── subsidiary.local (dominio tree aggiuntivo)
```

- **Parent-child trust**: creato automaticamente quando si aggiunge un child domain
- **Tree-root trust**: creato automaticamente quando si aggiunge un nuovo albero nel forest

Entrambi sono **transitivi** e **bidirezionali**: ogni dominio nel forest può autenticare utenti di qualsiasi altro dominio nel forest.

---

## Tipi di Trust

### Tabella Riepilogativa

| Tipo | Transitività | Direzione | Creazione | Uso |
|---|---|---|---|---|
| **Parent-child** | Transitivo | Bidirezionale | Automatica | Interno al forest |
| **Tree-root** | Transitivo | Bidirezionale | Automatica | Interno al forest |
| **External** | Non transitivo | Uno/bidirezionale | Manuale | Domain-to-domain tra forest |
| **Forest** | Transitivo | Uno/bidirezionale | Manuale | Forest-to-forest |
| **Shortcut** | Transitivo | Uno/bidirezionale | Manuale | Ottimizzazione intra-forest |
| **Realm** | Transitivo o non | Uno/bidirezionale | Manuale | AD ↔ Kerberos non-Windows |

### External Trust

Un external trust collega un dominio specifico di un forest a un dominio specifico di un altro forest. È **non transitivo**: l'accesso è limitato ai soli due domini coinvolti.

```
Forest A                    Forest B
├── a.com                   ├── b.com
│   └── child.a.com ←→ external trust ←→ child.b.com
│                           └── other.b.com (NO accesso)
└── other.a.com (NO accesso)
```

**Quando usare:**
- Accesso limitato tra due domini specifici
- Non si vuole esporre l'intero forest
- Compatibilità con domini Windows NT 4.0
- Scenari con vendor esterni che necessitano accesso a un solo dominio

**Creazione via GUI:**

```
Active Directory Domains and Trusts → Dominio → Properties → Trusts tab
→ New Trust → External Trust → selezionare dominio specifico
```

**Creazione via PowerShell (dal DC del dominio trusting):**

```powershell
# External trust unidirezionale (incoming — utenti remoti accedono a risorse locali)
netdom trust child.contoso.com /d:partner.fabrikam.com `
    /add /realm /passwordt:"TrustP@ss!2026" `
    /oneside:INCOMING
```

### Forest Trust

Un forest trust collega i root domain di due forest. È **transitivo** attraverso tutti i domini di entrambi i forest. Richiede forest functional level Windows Server 2003 o superiore.

```
Forest contoso.com              Forest fabrikam.com
├── contoso.com      ←→ forest trust ←→   fabrikam.com
├── europe.contoso.com    (transitivo)     ├── us.fabrikam.com
└── asia.contoso.com                       └── eu.fabrikam.com

Risultato: ogni dominio di un forest può autenticare utenti di ogni dominio dell'altro forest
```

**Quando usare:**
- Acquisizioni/fusioni dove serve accesso completo tra organizzazioni
- Separazione admin tra ambienti (Dev/Prod) con necessità di collaborazione
- Scenario multiorganizzazione con collaborazione estesa

**Creazione via PowerShell:**

```powershell
# Forest trust bidirezionale
# Eseguire su un DC nel forest root domain di ciascun forest

# Lato contoso.com
netdom trust contoso.com /d:fabrikam.com `
    /add /twoway /passwordt:"F0restTrust!2026" /foresthttps:yes

# Verifica
netdom trust contoso.com /d:fabrikam.com /verify

# Oppure via Active Directory Domains and Trusts GUI:
# Root domain → Properties → Trusts → New Trust → Forest Trust
```

### Shortcut Trust

Un shortcut trust riduce il percorso di autenticazione tra domini distanti nello stesso forest, eliminando la necessità di attraversare tutta la catena di trust parent-child.

```
contoso.com (root)
├── europe.contoso.com
│   └── italy.europe.contoso.com
└── asia.contoso.com
    └── japan.asia.contoso.com

Senza shortcut: italy.europe.contoso.com → europe.contoso.com → contoso.com
               → asia.contoso.com → japan.asia.contoso.com (4 hop)

Con shortcut trust diretto:
italy.europe.contoso.com ←→ shortcut ←→ japan.asia.contoso.com (1 hop)
```

**Quando usare:**
- Autenticazione cross-domain lenta a causa di molti hop
- Frequente accesso tra domini specifici in un forest grande
- Riduzione della latenza di autenticazione

**Creazione:**

```powershell
# Shortcut trust bidirezionale
netdom trust italy.europe.contoso.com /d:japan.asia.contoso.com `
    /add /twoway /passwordt:"ShortcutP@ss!" /shortcut
```

### Realm Trust

Un realm trust collega Active Directory a un realm Kerberos non-Windows (es. MIT Kerberos su Linux, macOS).

```
Active Directory              MIT Kerberos Realm
contoso.com ←→ realm trust ←→ LINUX.CONTOSO.COM

Utenti nel realm MIT possono autenticarsi a risorse AD (e viceversa)
```

**Quando usare:**
- Integrazione con sistemi Unix/Linux che usano MIT Kerberos
- Ambienti misti AD + Kerberos
- Interoperabilità con HPC cluster o sistemi legacy

**Creazione:**

```powershell
# Realm trust unidirezionale (utenti MIT accedono a risorse AD)
netdom trust contoso.com /d:LINUX.CONTOSO.COM `
    /add /realm /passwordt:"RealmTrust!2026" `
    /oneside:INCOMING

# Configurazione lato MIT KDC (krb5.conf)
# [realms]
#   CONTOSO.COM = {
#     kdc = dc01.contoso.com
#   }
# [domain_realm]
#   .contoso.com = CONTOSO.COM
```

### Confronto Dettagliato

| Caratteristica | External | Forest | Shortcut | Realm |
|---|---|---|---|---|
| **Transitività** | No | Si | Si | Configurabile |
| **Scope** | Domain-to-domain | Forest-to-forest | Domain-to-domain (intra) | AD ↔ Kerberos |
| **SID Filtering** | Si (default) | Si (default) | No (interno) | N/A |
| **Selective Auth** | Si | Si | No | No |
| **Kerberos** | Si | Si | Si | Si |
| **NTLM** | Si (fallback) | Si (fallback) | Si | No |
| **Min FFL** | Nessuno | 2003 | Nessuno | Nessuno |

---

## Trust Types — Deep Dive

### Parent-Child Trust — Dettagli Interni

Il parent-child trust viene creato automaticamente da `dcpromo` (o dalla promozione tramite Server Manager / `Install-ADDSDomain`) nel momento in cui si aggiunge un child domain a un dominio esistente. L'operazione stabilisce:

1. **Inter-realm key** AES-256 tra i DC dei due domini.
2. **Oggetto TDO (Trusted Domain Object)** in `CN=System` di ciascun dominio, con attributi `trustDirection`, `trustType`, `trustAttributes` e `flatName`.
3. **Record SRV DNS** per il child domain sotto la zona del parent (`_msdcs` e la zona del dominio stesso).

```powershell
# Visualizzare il TDO di un trust parent-child
Get-ADObject -SearchBase "CN=System,DC=europe,DC=contoso,DC=com" `
    -Filter { ObjectClass -eq "trustedDomain" } -Properties *

# Attributi chiave nel TDO:
# trustDirection   = 3 (bidirezionale)
# trustType        = 2 (AD trust, uplevel)
# trustAttributes  = 32 (WITHIN_FOREST)
# securityIdentifier = SID del dominio trusted
```

**Implicazioni operative:** Il parent-child trust non può essere eliminato manualmente. Per rimuoverlo occorre rimuovere il child domain dal forest (depromozione di tutti i DC del child domain). Tentare un `netdom trust /remove` su un trust parent-child restituisce errore perché il trust è intrinseco alla struttura del forest.

### Tree-Root Trust — Dettagli Interni

Il tree-root trust si crea quando si aggiunge un nuovo albero DNS al forest (ad esempio `subsidiary.local` nel forest `contoso.com`). Il trust collega direttamente il nuovo tree root al forest root domain, saltando qualsiasi gerarchia intermedia.

```
contoso.com (forest root)
│
├── europe.contoso.com (child)
│
└── tree-root trust (automatico, transitivo, bidi)
    │
    subsidiary.local (nuovo albero)
    └── dev.subsidiary.local (child del nuovo albero)
```

Il trust è transitivo: un utente di `dev.subsidiary.local` può accedere a risorse in `europe.contoso.com` senza trust aggiuntivi, perché il percorso di referral Kerberos attraversa `subsidiary.local` → `contoso.com` → `europe.contoso.com`.

### Shortcut Trust — Analisi delle Prestazioni

Il beneficio del shortcut trust è misurabile in termini di **hop di referral Kerberos eliminati**. In un forest con N livelli di profondità, un referral da un child domain a un child domain distante richiede fino a 2N - 2 hop senza shortcut.

**Esempio quantificato:**

```
Senza shortcut (forest profondo 4 livelli):
italy.europe.contoso.com → europe.contoso.com → contoso.com
→ asia.contoso.com → japan.asia.contoso.com
= 4 hop × ~15-50ms cadauno (dipende da latenza rete)
= 60-200ms di latenza aggiuntiva per ogni ticket request

Con shortcut trust diretto:
italy.europe.contoso.com → japan.asia.contoso.com
= 1 hop × ~15-50ms
= 15-50ms di latenza
```

**Quando creare un shortcut trust:** Quando il monitoraggio mostra che l'autenticazione cross-domain tra due domini specifici avviene frequentemente (>100 autenticazioni/giorno) e la latenza complessiva del referral chain supera la soglia accettabile per l'applicazione.

### External Trust — Considerazioni di Sicurezza

L'external trust è l'opzione più restrittiva per l'accesso cross-forest. Poiché non è transitivo, anche se `child.a.com` ha un external trust con `child.b.com`, gli utenti di `other.b.com` non possono usare questo trust per accedere a risorse in `child.a.com`.

**Limitazioni importanti:**

1. L'external trust **non supporta Kerberos AES** nelle versioni precedenti a Windows Server 2012 R2: il protocollo di autenticazione usa RC4-HMAC. Da Windows Server 2012 R2+ il supporto AES è disponibile se entrambi i lati lo supportano.
2. Il **name suffix routing** non è disponibile per external trust — è una funzionalità esclusiva del forest trust.
3. L'external trust non supporta **claims-based authentication** cross-trust (disponibile solo con forest trust FFL 2012+).

### Realm Trust — Configurazione Completa

La configurazione di un realm trust richiede interventi su entrambi i lati: Active Directory e MIT KDC.

**Lato Active Directory:**

```powershell
# Realm trust transitivo bidirezionale con MIT Kerberos
netdom trust contoso.com /d:LINUX.CONTOSO.COM `
    /add /realm /twoway /passwordt:"RealmXP@ss!2026" /transitive:YES

# Verificare il trust
netdom trust contoso.com /d:LINUX.CONTOSO.COM /verify
```

**Lato MIT KDC (krb5.conf):**

```ini
[libdefaults]
    default_realm = LINUX.CONTOSO.COM

[realms]
    LINUX.CONTOSO.COM = {
        kdc = kdc01.linux.contoso.com
        admin_server = kdc01.linux.contoso.com
    }
    CONTOSO.COM = {
        kdc = dc01.contoso.com
        kdc = dc02.contoso.com
    }

[domain_realm]
    .linux.contoso.com = LINUX.CONTOSO.COM
    .contoso.com = CONTOSO.COM

[capaths]
    LINUX.CONTOSO.COM = {
        CONTOSO.COM = .
    }
    CONTOSO.COM = {
        LINUX.CONTOSO.COM = .
    }
```

**Lato MIT KDC (kadmin):**

```bash
# Creare il principal cross-realm (entrambe le direzioni)
kadmin.local -q "addprinc -pw 'RealmXP@ss!2026' krbtgt/CONTOSO.COM@LINUX.CONTOSO.COM"
kadmin.local -q "addprinc -pw 'RealmXP@ss!2026' krbtgt/LINUX.CONTOSO.COM@CONTOSO.COM"

# Verificare
kadmin.local -q "listprincs krbtgt/*"
```

**Mappatura utenti:** Per consentire agli utenti MIT di accedere a risorse AD, è necessario creare account proxy o usare il name mapping:

```powershell
# Name mapping per utente MIT in AD
# User Properties → Account → Name Mappings → Kerberos Names
# Aggiungere: user@LINUX.CONTOSO.COM → account AD corrispondente

# Oppure via ktpass (per mapping SPN)
ktpass /princ user@LINUX.CONTOSO.COM /mapuser CONTOSO\linuxuser `
    /pass * /crypto AES256-SHA1
```

---

## Progettazione dell'Architettura Trust

### Modelli di Design Multi-Forest

**Modello 1 — Organizational Forest:**

```
Azienda principale        Azienda acquisita
contoso.com ←→ forest ←→ fabrikam.com
              trust

Uso: acquisizioni, fusioni, partnership long-term
Pro: separazione admin completa, controllo granulare
Contro: complessità gestionale, duplicazione risorse
```

**Modello 2 — Resource Forest:**

```
Account Forest            Resource Forest
contoso.com ←→ forest ←→ resource.contoso.com
(utenti)       trust     (server, app, database)

Uso: separazione utenti da risorse per sicurezza
Pro: admin delle risorse non hanno accesso agli account utente
Contro: gestione shadow account o selective auth
```

**Modello 3 — Restricted Access Forest:**

```
Produzione               Tier 0 (Admin)
contoso.com ←→ forest ←→ admin.contoso.com
              trust      (solo admin privilegiati)
              (selettivo)

Uso: ESAE / Red Forest per admin tier 0
Pro: isolamento totale degli admin privilegiati
Contro: complessità elevata, costi operativi
```

### Decision Matrix per Tipo di Trust

| Scenario | Trust Raccomandato | Note |
|---|---|---|
| Acquisizione completa | Forest trust bidirezionale | Selective auth in fase iniziale |
| Partner esterno | External trust unidirezionale | Solo dominio necessario |
| Dev/Prod separation | Forest trust (o nessun trust) | Dipende da necessità accesso |
| Vendor con accesso limitato | External trust + selective auth | Accesso minimo |
| Consolidamento pre-migrazione | Forest trust + ADMT | Transitorio |
| Admin privilegiati isolati | Forest trust + selective auth | Modello ESAE |
| Integrazione Linux | Realm trust | MIT Kerberos |

### Principi di Design

1. **Minimo privilegio**: preferire trust unidirezionali e selective authentication
2. **Ridurre la superficie**: evitare trust bidirezionali con entity esterne
3. **DNS affidabile**: il trust dipende dalla risoluzione DNS corretta tra forest
4. **Monitoraggio**: loggare tutti gli eventi di autenticazione cross-trust
5. **Review periodica**: verificare trimestralmente che i trust siano ancora necessari
6. **SID filtering**: mai disabilitare su trust esterni senza giustificazione documentata

---

## Autenticazione Cross-Forest

### Kerberos Cross-Forest

Quando un utente di Forest A accede a una risorsa in Forest B, il flusso Kerberos è:

```
1. Utente (user@contoso.com) richiede accesso a \\server.fabrikam.com\share

2. Client contatta DC di contoso.com
   → Riceve TGT per contoso.com

3. Client richiede referral per fabrikam.com
   → DC contoso.com genera referral ticket con inter-realm key

4. Client presenta referral a DC fabrikam.com
   → DC fabrikam.com genera TGS per la risorsa

5. Client accede a \\server.fabrikam.com\share con il TGS

Catena completa (se ci sono child domains coinvolti):
user@child.contoso.com → DC child.contoso.com
→ referral a contoso.com (parent)
→ referral a fabrikam.com (cross-forest)
→ referral a child.fabrikam.com (se la risorsa è in un child)
→ TGS per la risorsa
```

### Inter-Realm Keys

Quando si crea un trust, i DC dei due domini/forest scambiano chiavi crittografiche simmetriche (inter-realm keys) usate per firmare e validare i referral ticket:

```powershell
# Verifica trust e inter-realm keys
nltest /sc_query:fabrikam.com

# Output atteso:
# Flags: 0x... (trust type flags)
# Trusted DC Name: \\dc01.fabrikam.com
# Trusted DC Connection Status: Status = 0 0x0 NERR_Success
# The command completed successfully

# Verifica canale sicuro trust
nltest /sc_verify:fabrikam.com

# Reset trust password (se necessario)
netdom trust contoso.com /d:fabrikam.com /reset /passwordt:"NewP@ss!"
```

### NTLM Cross-Trust (Fallback)

NTLM viene usato come fallback quando Kerberos non è disponibile (es. accesso tramite IP, applicazioni legacy):

```
1. Client invia credenziali NTLM al server di fabrikam.com
2. Server fabrikam.com passa l'hash al DC di fabrikam.com
3. DC fabrikam.com non riconosce l'utente (dominio diverso)
4. DC fabrikam.com inoltra la richiesta al DC di contoso.com via trust
5. DC contoso.com valida le credenziali
6. Risposta torna al server di fabrikam.com → accesso consentito/negato
```

**Raccomandazione:** Disabilitare NTLM dove possibile per motivi di sicurezza. NTLM è vulnerabile a relay attack, pass-the-hash e brute force.

```powershell
# Audit NTLM usage prima di disabilitarlo
# GPO: Computer Configuration → Windows Settings → Security Settings
#      → Local Policies → Security Options
# "Network security: Restrict NTLM: Audit NTLM authentication in this domain" = Enable all

# Controllare event log per NTLM events
Get-WinEvent -LogName "Microsoft-Windows-NTLM/Operational" -MaxEvents 50 |
    Select-Object TimeCreated, @{N='Target';E={$_.Properties[0].Value}},
    @{N='Source';E={$_.Properties[1].Value}} | Format-Table -AutoSize
```

### Kerberos Constrained Delegation Cross-Forest

La delega Kerberos cross-forest ha limitazioni specifiche:

| Tipo Delegazione | Intra-Forest | Cross-Forest |
|---|---|---|
| **Unconstrained** | Si | No (bloccata per sicurezza) |
| **Constrained (KCD)** | Si | No (non supportata nativamente) |
| **Resource-Based Constrained (RBCD)** | Si | Si (con configurazione) |

```powershell
# Resource-Based Constrained Delegation cross-forest
# Sul server di destinazione nel forest remoto:

$trustedAccount = Get-ADComputer -Identity "webapp01" -Server "contoso.com"

Set-ADComputer -Identity "sqlserver01" `
    -PrincipalsAllowedToDelegateToAccount $trustedAccount
```

---

## Kerberos Cross-Realm — Deep Dive

### Trust Ticket Lifetime

I ticket Kerberos emessi durante un'autenticazione cross-realm hanno lifetime specifici controllati da policy indipendenti:

| Parametro | Default | Posizione GPO |
|---|---|---|
| **Maximum lifetime for service ticket** | 600 minuti (10 ore) | Computer Config → Windows Settings → Security Settings → Account Policies → Kerberos Policy |
| **Maximum lifetime for user ticket (TGT)** | 600 minuti (10 ore) | Stessa posizione |
| **Maximum lifetime for user ticket renewal** | 7 giorni | Stessa posizione |
| **Maximum tolerance for clock synchronization** | 5 minuti | Stessa posizione |

Per i **referral ticket cross-realm**, il lifetime è determinato dal dominio che emette il referral (il dominio source). Il DC del dominio di destinazione poi emette un TGS con il lifetime della propria policy.

```powershell
# Verificare le policy Kerberos correnti nel dominio
Get-ADDefaultDomainPasswordPolicy | Select-Object `
    MaxServiceAge, MaxTicketAge, MaxRenewAge, MaxClockSkew

# Visualizzare ticket Kerberos correnti (inclusi referral cross-realm)
klist

# Output tipico per accesso cross-forest:
# #0> Client: user@CONTOSO.COM
#     Server: krbtgt/FABRIKAM.COM@CONTOSO.COM   ← referral ticket
#     KerbTicket Encryption Type: AES-256-CTS
#     Ticket Flags: 0x40a10000 (forwardable renewable pre_authent)
#     Start Time: ...
#     End Time: ...
#
# #1> Client: user@CONTOSO.COM
#     Server: cifs/fileserver.fabrikam.com@FABRIKAM.COM   ← service ticket
#     KerbTicket Encryption Type: AES-256-CTS
```

### Referral Chain — Percorso Completo

Il referral chain è il percorso completo che un ticket Kerberos segue per attraversare trust multipli. In scenari complessi con child domain in entrambi i forest, il percorso può essere lungo:

```
Scenario: user@dev.europe.contoso.com accede a \\app.asia.fabrikam.com\share

Referral chain senza shortcut trust:
1. Client → DC dev.europe.contoso.com
   "Ho bisogno di un ticket per asia.fabrikam.com"
   DC: "Non conosco asia.fabrikam.com, ecco un referral per europe.contoso.com"
   
2. Client → DC europe.contoso.com
   DC: "Non conosco asia.fabrikam.com, ecco un referral per contoso.com"
   
3. Client → DC contoso.com (forest root)
   DC: "Ho un forest trust con fabrikam.com, ecco un referral cross-forest"
   
4. Client → DC fabrikam.com (forest root remoto)
   DC: "asia.fabrikam.com è un mio child, ecco un referral"
   
5. Client → DC asia.fabrikam.com
   DC: "Ecco il TGS per app.asia.fabrikam.com"

Totale: 5 hop di referral
```

### Impatto sulle Prestazioni

Ogni hop di referral richiede un roundtrip di rete al DC di quel dominio. L'impatto sulle prestazioni dipende da:

1. **Latenza di rete** tra i siti dei DC coinvolti
2. **Carico del DC** al momento della richiesta
3. **Numero di hop** nella referral chain
4. **Caching dei ticket** — i referral ticket vengono memorizzati nella cache del client e riutilizzati

```powershell
# Misurare il tempo di autenticazione cross-forest
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

# Forzare un'autenticazione cross-forest
$result = Test-Path "\\fileserver.fabrikam.com\share" -ErrorAction SilentlyContinue

$stopwatch.Stop()
Write-Output "Autenticazione cross-forest: $($stopwatch.ElapsedMilliseconds) ms"

# Confrontare con autenticazione locale
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$result = Test-Path "\\fileserver.contoso.com\share" -ErrorAction SilentlyContinue
$stopwatch.Stop()
Write-Output "Autenticazione locale: $($stopwatch.ElapsedMilliseconds) ms"
```

### Encryption Types nei Trust

L'encryption type usato per i ticket cross-realm dipende dalla negoziazione tra i DC dei due domini:

| Encryption Type | Supporto | Sicurezza | Note |
|---|---|---|---|
| **AES-256-CTS-HMAC-SHA1** | FFL 2008+ | Alta | Raccomandato |
| **AES-128-CTS-HMAC-SHA1** | FFL 2008+ | Media | Accettabile |
| **RC4-HMAC (ARCFOUR)** | Tutti | Bassa | Legacy, evitare se possibile |
| **DES** | Deprecato | Molto bassa | Disabilitato di default da 2008+ |

```powershell
# Verificare gli encryption types supportati dal trust
Get-ADTrust -Filter { Name -eq "fabrikam.com" } -Properties * |
    Select-Object Name, Direction, TrustType, `
    @{N='SupportedEncTypes';E={
        $enc = $_.msDS-SupportedEncryptionTypes
        $result = @()
        if ($enc -band 0x1)  { $result += "DES-CBC-CRC" }
        if ($enc -band 0x2)  { $result += "DES-CBC-MD5" }
        if ($enc -band 0x4)  { $result += "RC4-HMAC" }
        if ($enc -band 0x8)  { $result += "AES128" }
        if ($enc -band 0x10) { $result += "AES256" }
        $result -join ", "
    }}

# Forzare solo AES per il trust (disabilitare RC4)
# ATTENZIONE: verificare che entrambi i lati supportino AES
Set-ADObject -Identity (Get-ADTrust "fabrikam.com").DistinguishedName `
    -Replace @{'msDS-SupportedEncryptionTypes' = 24}  # 0x8 + 0x10 = AES128 + AES256
```

---

## Selective Authentication

### Panoramica

Con la selective authentication, l'accesso cross-trust non è automatico per tutti gli utenti. Ogni utente/gruppo deve essere esplicitamente autorizzato ad accedere a risorse specifiche nel dominio trusting tramite il permesso **Allowed to Authenticate**.

### Forest-Wide vs Selective Authentication

| Modalità | Comportamento | Sicurezza | Gestione |
|---|---|---|---|
| **Forest-wide** | Tutti gli utenti trusted possono tentare l'autenticazione a qualsiasi risorsa | Bassa | Semplice |
| **Selective** | Solo utenti/gruppi con permesso "Allowed to Authenticate" | Alta | Più complessa |

### Abilitazione Selective Authentication

```powershell
# Abilitare selective authentication su un trust esistente
# Da Active Directory Domains and Trusts:
# Trust properties → Authentication tab → Selective Authentication

# Via netdom
netdom trust contoso.com /d:fabrikam.com /SelectiveAuth:YES

# Verifica
netdom trust contoso.com /d:fabrikam.com /verify
```

### Configurazione del Permesso "Allowed to Authenticate"

Dopo aver abilitato la selective authentication, è necessario concedere il permesso sui computer target:

```powershell
# 1. Aprire Active Directory Users and Computers (ADUC)
# 2. Selezionare il computer object (es. fileserver01)
# 3. Properties → Security → Advanced → Add
# 4. Principal: utente o gruppo del trusted forest
# 5. Permesso: "Allowed to Authenticate" = Allow
# 6. Apply

# Via PowerShell (ADSI)
$computerDN = "CN=FileServer01,OU=Servers,DC=contoso,DC=com"
$trustedGroupSID = "S-1-5-21-XXXXXXXXX-XXXXXXXXX-XXXXXXXXX-1234"

$acl = Get-Acl "AD:\$computerDN"

# GUID per "Allowed to Authenticate" extended right
$allowedToAuthGuid = [guid]"68B1D179-0D15-4D4F-AB71-46152E79A7BC"

$ace = New-Object System.DirectoryServices.ActiveDirectoryAccessRule(
    [System.Security.Principal.SecurityIdentifier]$trustedGroupSID,
    "ExtendedRight",
    "Allow",
    $allowedToAuthGuid
)

$acl.AddAccessRule($ace)
Set-Acl "AD:\$computerDN" $acl
```

### Best Practices Selective Authentication

1. Creare gruppi dedicati nel trusted forest (es. "Cross-Forest Access - FileServer")
2. Documentare ogni permesso "Allowed to Authenticate" con owner e scadenza
3. Usare sempre selective authentication per trust con entity esterne
4. Review trimestrale dei permessi concessi
5. Monitorare eventi di autenticazione negata (Event ID 4625 con failure code per selective auth)

---

## SID Filtering

### Cosa Fa il SID Filtering

Il SID filtering (quarantine) rimuove dal token di autenticazione tutti i SID che non appartengono al dominio trusted. Questo protegge contro attacchi di SID History injection.

### Il Rischio Senza SID Filtering

```
Scenario di attacco:
1. Admin malevolo nel trusted forest (fabrikam.com)
2. Aggiunge SID di Enterprise Admin di contoso.com nella SID History di un utente fabrikam.com
3. L'utente si autentica via trust verso contoso.com
4. SENZA filtering: il token contiene il SID Enterprise Admin → accesso admin completo
5. CON filtering: il SID estraneo viene rimosso → l'utente ha solo i permessi legittimi
```

### Come Funziona

```
Token utente fabrikam.com:
- SID primario: S-1-5-21-FABRIKAM-1234 (utente)
- SID gruppo: S-1-5-21-FABRIKAM-5678 (Domain Users)
- SID History: S-1-5-21-CONTOSO-512 (Domain Admins contoso.com) ← INJECTION

Con SID Filtering attivo:
- S-1-5-21-FABRIKAM-1234 → PASSA (appartiene a fabrikam.com)
- S-1-5-21-FABRIKAM-5678 → PASSA (appartiene a fabrikam.com)
- S-1-5-21-CONTOSO-512 → RIMOSSO (non appartiene a fabrikam.com)
```

### Configurazione SID Filtering

```powershell
# SID filtering è ATTIVO di default su external e forest trust

# Verificare stato SID filtering
netdom trust contoso.com /d:fabrikam.com /FilterSids

# Disabilitare SID filtering (NON raccomandato — solo durante migrazioni)
netdom trust contoso.com /d:fabrikam.com /FilterSids:NO

# Riabilitare SID filtering
netdom trust contoso.com /d:fabrikam.com /FilterSids:YES

# Per forest trust: disabilitare SID filtering per un dominio specifico
# (TLN exclusion anziché disabilitare completamente)
netdom trust contoso.com /d:fabrikam.com `
    /EnableSIDHistory:YES    # Permette SID History durante migrazione
```

### SID Filtering e Migrazioni

Durante le migrazioni con ADMT, il SID History viene usato per mantenere l'accesso alle risorse originarie. Il SID filtering blocca questo flusso. Opzioni:

| Approccio | Sicurezza | Praticità |
|---|---|---|
| Disabilitare SID filtering temporaneamente | Bassa (rischio) | Alta |
| Usare TLN exclusion per domini specifici | Media | Media |
| Re-ACL le risorse post-migrazione | Alta | Bassa (lavoro) |
| Usare token groups con SID filtering attivo | Alta | Media |

**Raccomandazione:** Disabilitare il SID filtering solo durante la finestra di migrazione attiva, con monitoraggio intensivo, e riabilitarlo immediatamente dopo.

---

## Attacchi SID History e Contromisure

### Anatomia dell'Attacco SID History Injection

L'attacco SID History è una delle minacce più gravi negli scenari multi-forest. Un amministratore di dominio compromesso nel trusted forest può eseguire privilege escalation nel trusting forest.

**Fasi dell'attacco:**

```
Fase 1 — Ricognizione:
L'attaccante con privilegi Domain Admin in fabrikam.com enumera i SID del 
forest contoso.com (es. via LDAP query al GC):
- Enterprise Admins contoso.com: S-1-5-21-CONTOSO-519
- Domain Admins contoso.com:     S-1-5-21-CONTOSO-512
- Schema Admins contoso.com:     S-1-5-21-CONTOSO-518

Fase 2 — Injection:
L'attaccante usa strumenti come mimikatz (o API di basso livello) per 
iniettare il SID di Enterprise Admins nella sIDHistory di un utente 
controllato in fabrikam.com:

# mimikatz (esempio — solo per comprensione difensiva):
# misc::addsid user_compromesso S-1-5-21-CONTOSO-519

Fase 3 — Sfruttamento:
L'utente compromesso si autentica verso contoso.com via trust.
Se il SID filtering è disabilitato, il token include il SID injected.
L'utente ottiene privilegi Enterprise Admin in contoso.com.

Fase 4 — Persistenza:
L'attaccante crea account backdoor, golden ticket, o modifica GPO
nel forest contoso.com.
```

### Contromisure — Enforcement del SID Filtering

**1. Verificare che il SID filtering sia attivo su tutti i trust esterni e forest trust:**

```powershell
# Script di audit SID filtering su tutti i trust
Get-ADTrust -Filter * | ForEach-Object {
    $trustName = $_.Name
    $result = netdom trust (Get-ADDomain).DNSRoot /d:$trustName /FilterSids 2>&1
    [PSCustomObject]@{
        Trust           = $trustName
        Direction       = $_.Direction
        TrustType       = $_.TrustType
        SIDFiltering    = if ($result -match "enabled") { "ATTIVO" } else { "DISATTIVATO - RISCHIO" }
    }
} | Format-Table -AutoSize
```

**2. Quarantine policy su forest trust:**

Il quarantine (SID filtering per forest trust) filtra i SID in base al dominio di appartenenza. Solo i SID il cui RID authority corrisponde a uno dei domini del trusted forest vengono accettati.

```powershell
# Abilitare quarantine esplicita (normalmente attiva di default)
netdom trust contoso.com /d:fabrikam.com /Quarantine:YES

# Verificare con Get-ADTrust
Get-ADTrust -Identity "fabrikam.com" -Properties * | 
    Select-Object Name, SIDFilteringQuarantined, SIDFilteringForestAware
```

**3. Monitoraggio eventi di SID filtering:**

| Event ID | Log | Significato |
|---|---|---|
| **4675** | Security | Token costruito con SID filtrati — indica che il filtering ha rimosso SID sospetti |
| **4768** | Security | TGT request — controllare il campo `TargetDomainName` per autenticazioni cross-trust |
| **4769** | Security | TGS request — analizzare i referral cross-realm |

```powershell
# Monitorare eventi di SID filtering (Event ID 4675)
Get-WinEvent -LogName Security -FilterXPath `
    "*[System[EventID=4675]]" -MaxEvents 50 |
    Select-Object TimeCreated, Message | Format-List

# Alert automatico per SID filtering triggered
$query = @"
<QueryList>
  <Query Id="0" Path="Security">
    <Select Path="Security">*[System[EventID=4675]]</Select>
  </Query>
</QueryList>
"@

Register-WmiEvent -Query "SELECT * FROM __InstanceCreationEvent WHERE TargetInstance ISA 'Win32_NTLogEvent' AND TargetInstance.EventCode = '4675'" `
    -Action { Write-Warning "SID Filtering ha rimosso SID sospetti! Investigare." }
```

---

## Name Suffix Routing

### Panoramica

Il Name Suffix Routing (NSR) controlla quali name suffix (UPN suffix, DNS domain name) sono "routati" attraverso un forest trust. Determina se un utente con un certo UPN suffix può autenticarsi tramite il trust.

### Funzionamento

```
Forest contoso.com (trust → fabrikam.com):

Name suffixes di fabrikam.com routati:
- fabrikam.com → Enabled (utenti @fabrikam.com possono autenticarsi)
- us.fabrikam.com → Enabled (child domain routato)
- partner.net (UPN suffix aggiunto) → Disabled (bloccato da admin)

Se un utente user@partner.net tenta l'autenticazione via trust,
il DC di contoso.com rifiuta perché il suffix non è routato.
```

### Gestione Name Suffix Routing

```powershell
# Visualizzare name suffix routing per un trust
# Active Directory Domains and Trusts → Trust properties → Name Suffix Routing tab

# Via netdom
netdom trust contoso.com /d:fabrikam.com /NameSuffixes

# Disabilitare routing per un suffix specifico
netdom trust contoso.com /d:fabrikam.com `
    /ToggleSuffix:partner.net /disable

# Abilitare routing per un suffix
netdom trust contoso.com /d:fabrikam.com `
    /ToggleSuffix:partner.net /enable
```

### Conflitti Name Suffix

Se due trust forest hanno lo stesso name suffix, si crea un conflitto. Solo uno può essere routato:

```powershell
# Scenario: Forest A ha trust con Forest B e Forest C
# Sia B che C hanno il suffix "contoso.net"
# Solo uno dei due trust può routare contoso.net

# Verifica conflitti
netdom trust contoso.com /d:fabrikam.com /NameSuffixes
# Output mostra "Conflicting" accanto al suffix in conflitto

# Risoluzione: disabilitare il routing nel trust meno prioritario
```

---

## Name Suffix Routing — Configurazione Avanzata

### Tipi di Name Suffix

Il Name Suffix Routing gestisce due categorie di name suffix:

**1. Top-Level Names (TLN):** I nomi DNS dei domini nel forest. Per `fabrikam.com` con child domain `us.fabrikam.com` e `eu.fabrikam.com`, il TLN è `fabrikam.com`.

**2. UPN Suffixes non corrispondenti al DNS:** Se `fabrikam.com` ha aggiunto un UPN suffix come `@partner.net` (configurabile in Active Directory Domains and Trusts → Properties → UPN Suffixes), questo suffix appare nella lista NSR come suffix aggiuntivo.

```powershell
# Elencare tutti i UPN suffixes configurati nel forest remoto
# (visibili nella scheda Name Suffix Routing del trust)
Get-ADForest -Server "fabrikam.com" | Select-Object -ExpandProperty UPNSuffixes

# Elencare tutti i suffixes (inclusi i DNS domain names)
$forestInfo = Get-ADForest -Server "fabrikam.com"
$allSuffixes = @()
$allSuffixes += $forestInfo.Name               # forest root
$allSuffixes += $forestInfo.Domains            # tutti i domini
$allSuffixes += $forestInfo.UPNSuffixes        # UPN suffixes aggiuntivi
$allSuffixes | ForEach-Object { Write-Output "Suffix: $_" }
```

### Esclusioni TLN (Top-Level Name Exclusion)

Le TLN exclusion permettono di bloccare selettivamente il routing di specifici sottoinsiemi di un TLN, senza disabilitare l'intero suffix:

```powershell
# Scenario: fabrikam.com ha un child domain "restricted.fabrikam.com"
# che contiene dati riservati. Si vuole permettere il trust per fabrikam.com
# ma bloccare restricted.fabrikam.com.

# Aggiungere una TLN exclusion
netdom trust contoso.com /d:fabrikam.com `
    /AddTLNEx:restricted.fabrikam.com

# Verificare le exclusion
netdom trust contoso.com /d:fabrikam.com /NameSuffixes
# Output: restricted.fabrikam.com → Excluded

# Rimuovere una TLN exclusion
netdom trust contoso.com /d:fabrikam.com `
    /RemoveTLNEx:restricted.fabrikam.com
```

### Risoluzione Conflitti tra Forest Trust Multipli

Quando un'organizzazione ha trust con tre o più forest, i conflitti di name suffix sono frequenti. La regola di precedenza è:

```
Regola: il primo forest trust che dichiara un suffix lo "possiede".
Se un secondo trust dichiara lo stesso suffix, viene marcato come "Conflicting"
e NON viene routato tramite il secondo trust.

Esempio:
Forest A (contoso.com) ha trust con:
- Forest B (fabrikam.com): dichiara suffix "shared.net" → Enabled
- Forest C (tailspin.com): dichiara anche "shared.net" → Conflicting (disabilitato)

Per risolvere:
1. Determinare quale forest dovrebbe "possedere" shared.net
2. Disabilitare il suffix nel trust meno prioritario
3. Se necessario, creare un external trust separato verso il dominio specifico
   nel forest che non possiede il suffix
```

---

## Configurazione DNS per Trust

### Prerequisiti DNS

La risoluzione DNS tra forest è **critica** per il funzionamento dei trust. Ogni forest deve poter risolvere i nomi dell'altro forest.

### Metodi di Risoluzione DNS Cross-Forest

**Metodo 1 — Conditional Forwarder (raccomandato):**

```powershell
# Su DNS server di contoso.com: forward per fabrikam.com
Add-DnsServerConditionalForwarderZone -Name "fabrikam.com" `
    -MasterServers "10.20.1.10","10.20.1.11" `
    -ReplicationScope "Forest"

# Su DNS server di fabrikam.com: forward per contoso.com
Add-DnsServerConditionalForwarderZone -Name "contoso.com" `
    -MasterServers "10.10.1.10","10.10.1.11" `
    -ReplicationScope "Forest"

# Verifica
Resolve-DnsName -Name "dc01.fabrikam.com" -Server "10.10.1.10"
nslookup _ldap._tcp.fabrikam.com
```

**Metodo 2 — Stub Zone:**

```powershell
# Stub zone su DNS di contoso.com per fabrikam.com
Add-DnsServerStubZone -Name "fabrikam.com" `
    -MasterServers "10.20.1.10" `
    -ReplicationScope "Forest"

# La stub zone mantiene automaticamente i record NS aggiornati
```

**Metodo 3 — Secondary Zone (meno comune):**

```powershell
# Zone transfer: copia completa della zona
# Richiede che la zona primaria permetta il transfer
Add-DnsServerSecondaryZone -Name "fabrikam.com" `
    -ZoneFile "fabrikam.com.dns" `
    -MasterServers "10.20.1.10"
```

### Record DNS Critici per i Trust

| Record | Tipo | Scopo |
|---|---|---|
| `_ldap._tcp.dc._msdcs.fabrikam.com` | SRV | Localizzazione DC |
| `_kerberos._tcp.dc._msdcs.fabrikam.com` | SRV | Localizzazione KDC |
| `_gc._tcp.fabrikam.com` | SRV | Global Catalog |
| `_kpasswd._tcp.fabrikam.com` | SRV | Kerberos password change |
| `dc01.fabrikam.com` | A | DC host record |

```powershell
# Verifica completa dei record SRV necessari per il trust
$targetDomain = "fabrikam.com"
$srvRecords = @(
    "_ldap._tcp.dc._msdcs.$targetDomain",
    "_kerberos._tcp.dc._msdcs.$targetDomain",
    "_ldap._tcp.$targetDomain",
    "_gc._tcp.$targetDomain"
)

foreach ($record in $srvRecords) {
    $result = Resolve-DnsName -Name $record -Type SRV -ErrorAction SilentlyContinue
    if ($result) {
        Write-Output "[OK] $record → $($result.NameTarget):$($result.Port)"
    } else {
        Write-Warning "[FAIL] $record non risolvibile"
    }
}
```

### DNS e Firewall Ports

| Porta | Protocollo | Servizio | Necessità |
|---|---|---|---|
| 53 | TCP/UDP | DNS | Obbligatoria |
| 88 | TCP/UDP | Kerberos | Obbligatoria |
| 135 | TCP | RPC Endpoint Mapper | Obbligatoria |
| 389 | TCP/UDP | LDAP | Obbligatoria |
| 445 | TCP | SMB | Trust management |
| 464 | TCP/UDP | Kerberos password change | Cambio password |
| 636 | TCP | LDAPS | Se crittografia richiesta |
| 3268 | TCP | Global Catalog | Query cross-forest |
| 3269 | TCP | Global Catalog SSL | GC sicuro |
| 49152-65535 | TCP | RPC dinamiche | Obbligatorio (range restringibile) |

```powershell
# Test connettività porte trust
$dc = "dc01.fabrikam.com"
$ports = @(53, 88, 135, 389, 445, 636, 3268)

foreach ($port in $ports) {
    $result = Test-NetConnection -ComputerName $dc -Port $port -WarningAction SilentlyContinue
    [PSCustomObject]@{
        Porta     = $port
        Connesso  = $result.TcpTestSucceeded
    }
}
```

---

## DNS per Multi-Forest — Scelta dell'Approccio

### Confronto Conditional Forwarder vs Stub Zone vs Secondary Zone

| Caratteristica | Conditional Forwarder | Stub Zone | Secondary Zone |
|---|---|---|---|
| **Tipo di dato** | Inoltra le query ai DNS del forest remoto | Copia solo i record NS e SOA | Copia integrale della zona |
| **Aggiornamento** | Nessuno (punta a IP statici) | Automatico (polling del SOA) | Zone transfer automatico (AXFR/IXFR) |
| **Replica AD-integrata** | Si (Forest/Domain scope) | Si (Forest/Domain scope) | No (file-based) |
| **Visibilità dati** | Nessun dato locale | Solo NS records | Tutti i record — espone la struttura interna |
| **Failover** | Lista di IP, provati in ordine | Segue i NS records | N/A (read-only locale) |
| **Sicurezza** | Non espone dati interni | Espone solo i NS | Espone tutta la zona — rischio se il trust è con un partner esterno |
| **Caso d'uso ideale** | Forest trust standard | Grandi forest con molti DC | Scenari legacy, alta disponibilità DNS |

**Raccomandazione:** Per la maggior parte degli scenari multi-forest, il **conditional forwarder con replication scope Forest** è la scelta migliore. Offre il miglior bilanciamento tra funzionalità, sicurezza e semplicità di gestione.

```powershell
# Conditional forwarder con replica AD (forest-wide) — produzione
Add-DnsServerConditionalForwarderZone -Name "fabrikam.com" `
    -MasterServers "10.20.1.10","10.20.1.11","10.20.2.10" `
    -ReplicationScope "Forest"

# Stub zone — quando i DNS del forest remoto cambiano frequentemente
Add-DnsServerStubZone -Name "fabrikam.com" `
    -MasterServers "10.20.1.10" `
    -ReplicationScope "Forest"

# Verificare quale metodo è configurato
Get-DnsServerZone | Where-Object {
    $_.ZoneName -eq "fabrikam.com"
} | Select-Object ZoneName, ZoneType, IsAutoCreated, IsDsIntegrated
```

### DNS Split-Brain per Forest Interni ed Esterni

In scenari dove un forest interno deve risolvere nomi di un forest partner senza esporre la propria infrastruttura DNS:

```powershell
# Architettura DNS split-brain per multi-forest con partner esterno:
#
# Rete interna:
#   DC/DNS contoso.com → conditional forwarder → DNS fabrikam.com (via VPN)
#
# DMZ:
#   DNS pubblico contoso.com → nessun forwarding a fabrikam.com
#
# Risultato: solo i client interni possono risolvere fabrikam.com
# I DNS pubblici non conoscono l'esistenza del partner

# Verificare che il conditional forwarder sia solo su DNS interni
Get-DnsServerConditionalForwarderZone -Name "fabrikam.com" -ErrorAction SilentlyContinue
```

---

## Requisiti Firewall Completi

### Tabella Porte — Riferimento Completo

Per un forest trust funzionante, le seguenti porte devono essere aperte bidirezionalmente tra i DC dei due forest (fonte: Microsoft Learn, "Active Directory and Active Directory Domain Services Port Requirements" — consultato: 2026-05-23):

| Porta | Proto | Servizio | Direzione | Note |
|---|---|---|---|---|
| 53 | TCP/UDP | DNS | Bidi | Risoluzione nomi, fondamentale per DC locator |
| 88 | TCP/UDP | Kerberos | Bidi | Autenticazione Kerberos, referral cross-realm |
| 123 | UDP | NTP/W32Time | Bidi | Sincronizzazione orario (Kerberos richiede <5min skew) |
| 135 | TCP | RPC Endpoint Mapper | Bidi | Mapping delle porte RPC dinamiche |
| 137 | UDP | NetBIOS Name Service | Bidi | Risoluzione nomi NetBIOS (legacy) |
| 138 | UDP | NetBIOS Datagram | Bidi | Browsing, DFS (legacy) |
| 139 | TCP | NetBIOS Session | Bidi | Risorsa condivise SMBv1 (legacy) |
| 389 | TCP/UDP | LDAP | Bidi | Query directory, replication |
| 445 | TCP | SMB | Bidi | Trust management, SYSVOL, netlogon |
| 464 | TCP/UDP | Kerberos kpasswd | Bidi | Cambio password Kerberos |
| 636 | TCP | LDAPS | Bidi | LDAP sicuro (opzionale ma raccomandato) |
| 3268 | TCP | GC (LDAP) | Bidi | Query Global Catalog |
| 3269 | TCP | GC (LDAPS) | Bidi | Global Catalog sicuro |
| 9389 | TCP | AD Web Services | Bidi | PowerShell AD cmdlets (ADWS) |
| 49152-65535 | TCP | RPC dinamiche | Bidi | Usate da vari servizi AD |

### Restringere il Range RPC Dinamico

In ambienti con firewall restrittivo, è possibile limitare il range delle porte RPC dinamiche:

```powershell
# Limitare il range RPC a 10 porte (esempio: 50000-50010)
# Su ogni DC coinvolto nel trust:

# 1. Configurare NTDS per usare una porta statica
# Registry: HKLM\SYSTEM\CurrentControlSet\Services\NTDS\Parameters
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" `
    -Name "TCP/IP Port" -Value 50001 -Type DWord

# 2. Configurare Netlogon per usare una porta statica
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Netlogon\Parameters" `
    -Name "DCTcpipPort" -Value 50002 -Type DWord

# 3. Configurare FRS (se usato) per porta statica
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\NtFrs\Parameters" `
    -Name "RPC TCP/IP Port Assignment" -Value 50003 -Type DWord

# 4. Riavviare i servizi
Restart-Service NTDS, Netlogon -Force

# 5. Aprire sul firewall solo le porte specifiche anziché l'intero range
```

### Script di Validazione Porte

```powershell
# Validazione completa delle porte necessarie per il trust
function Test-TrustPorts {
    param(
        [Parameter(Mandatory)]
        [string]$RemoteDC
    )
    
    $ports = @(
        @{Port=53;   Proto="TCP/UDP"; Service="DNS"},
        @{Port=88;   Proto="TCP/UDP"; Service="Kerberos"},
        @{Port=135;  Proto="TCP";     Service="RPC Mapper"},
        @{Port=389;  Proto="TCP";     Service="LDAP"},
        @{Port=445;  Proto="TCP";     Service="SMB"},
        @{Port=464;  Proto="TCP";     Service="Kerberos PW"},
        @{Port=636;  Proto="TCP";     Service="LDAPS"},
        @{Port=3268; Proto="TCP";     Service="GC"},
        @{Port=3269; Proto="TCP";     Service="GC SSL"},
        @{Port=9389; Proto="TCP";     Service="ADWS"}
    )
    
    $results = foreach ($p in $ports) {
        $test = Test-NetConnection -ComputerName $RemoteDC -Port $p.Port `
            -WarningAction SilentlyContinue -InformationLevel Quiet
        [PSCustomObject]@{
            Porta    = $p.Port
            Servizio = $p.Service
            Stato    = if ($test) { "APERTA" } else { "BLOCCATA" }
        }
    }
    
    $results | Format-Table -AutoSize
    
    $blocked = ($results | Where-Object { $_.Stato -eq "BLOCCATA" }).Count
    if ($blocked -gt 0) {
        Write-Warning "$blocked porte bloccate — il trust potrebbe non funzionare correttamente"
    } else {
        Write-Output "Tutte le porte necessarie sono aperte"
    }
}

# Esempio di utilizzo:
# Test-TrustPorts -RemoteDC "dc01.fabrikam.com"
```

---

## Creazione Forest Trust Step-by-Step

### Prerequisiti

Prima di creare un forest trust, verificare tutti i seguenti requisiti:

```
Checklist pre-creazione forest trust:
[ ] 1. Entrambi i forest al FFL 2003 o superiore
[ ] 2. DNS cross-forest funzionante (conditional forwarder o stub zone)
[ ] 3. Porte firewall aperte (DNS, Kerberos, LDAP, SMB, RPC)
[ ] 4. Account Domain Admin o Enterprise Admin in entrambi i forest
[ ] 5. Sincronizzazione orario tra i forest (<5 minuti di skew)
[ ] 6. Nessun conflitto di name suffix con trust esistenti
[ ] 7. Decisione su selective authentication vs forest-wide
[ ] 8. Backup dei DC root domain di entrambi i forest
```

### Procedura Completa

**Fase 1 — Configurare DNS:**

```powershell
# Su un DC DNS di contoso.com:
Add-DnsServerConditionalForwarderZone -Name "fabrikam.com" `
    -MasterServers "10.20.1.10","10.20.1.11" `
    -ReplicationScope "Forest"

# Su un DC DNS di fabrikam.com:
Add-DnsServerConditionalForwarderZone -Name "contoso.com" `
    -MasterServers "10.10.1.10","10.10.1.11" `
    -ReplicationScope "Forest"

# Attendere la replica AD (o forzarla)
repadmin /syncall /APed

# Verificare la risoluzione in entrambe le direzioni
Resolve-DnsName "_ldap._tcp.dc._msdcs.fabrikam.com" -Type SRV
Resolve-DnsName "_ldap._tcp.dc._msdcs.contoso.com" -Type SRV
```

**Fase 2 — Verificare connettività di rete:**

```powershell
# Da un DC di contoso.com verso un DC di fabrikam.com
Test-TrustPorts -RemoteDC "dc01.fabrikam.com"

# Verificare la sincronizzazione orario
w32tm /stripchart /computer:dc01.fabrikam.com /samples:3 /dataonly
```

**Fase 3 — Creare il trust (GUI):**

```
1. Su un DC root domain di contoso.com:
   Active Directory Domains and Trusts → contoso.com → Properties → Trusts
   
2. New Trust → Trust Name: fabrikam.com → Next
   
3. Trust Type: Forest trust → Next
   
4. Direction of Trust: Two-way (o One-way: incoming/outgoing) → Next
   
5. Sides of Trust: "Both this domain and the specified domain"
   (se si ha accesso admin a entrambi i forest) → Next
   
6. Authentication Level: 
   - Forest-wide authentication (tutti possono autenticarsi)
   - Selective authentication (serve "Allowed to Authenticate" esplicito)
   
7. Trust Password: inserire una password complessa condivisa
   
8. Confirmation → Create → Validate trust (confermare su entrambi i lati)
```

**Fase 3 alternativa — Creare il trust (CLI):**

```powershell
# Trust bidirezionale con selective authentication
# Eseguire sul DC root di contoso.com:
netdom trust contoso.com /d:fabrikam.com `
    /add /twoway `
    /passwordt:"F0rest!Trust#2026!Secure" `
    /SelectiveAuth:YES

# Verificare immediatamente
netdom trust contoso.com /d:fabrikam.com /verify
nltest /sc_verify:fabrikam.com
```

**Fase 4 — Validare il trust:**

```powershell
# Validazione completa post-creazione
# 1. Verifica del trust object
Get-ADTrust -Filter { Name -eq "fabrikam.com" } | 
    Select-Object Name, Direction, TrustType, SelectiveAuthentication, `
    SIDFilteringQuarantined, SIDFilteringForestAware

# 2. Verifica del secure channel
nltest /sc_verify:fabrikam.com

# 3. Test DNS bidirezionale
Resolve-DnsName "dc01.fabrikam.com"
# (dal lato fabrikam.com)
# Resolve-DnsName "dc01.contoso.com"

# 4. Test accesso reale (se selective auth è off)
dir "\\dc01.fabrikam.com\NETLOGON"

# 5. Verifica Kerberos ticket
klist purge
dir "\\server.fabrikam.com\share"
klist  # Dovrebbe mostrare krbtgt/FABRIKAM.COM@CONTOSO.COM
```

---

## Accesso Risorse Cross-Forest

### Assegnazione Permessi

Per concedere accesso a risorse in un dominio trusting a utenti del dominio trusted:

```powershell
# 1. Nella ACL della risorsa (share, cartella, app), aggiungere l'utente/gruppo del trusted domain

# Esempio: aggiungere gruppo fabrikam.com a una share locale
$sharePath = "\\fileserver01.contoso.com\SharedDocs"
$acl = Get-Acl $sharePath

$rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    "FABRIKAM\ProjectTeam",       # Account dal trusted domain
    "ReadAndExecute",              # Permessi
    "ContainerInherit,ObjectInherit",
    "None",
    "Allow"
)
$acl.AddAccessRule($rule)
Set-Acl $sharePath $acl
```

### Gruppi Cross-Forest

Best practice per gestire accesso cross-forest:

```
Strategia A-G-DL-P (Account-Global-Domain Local-Permissions):

1. Nel TRUSTED forest (fabrikam.com):
   - Utenti → Global Group "GG-Project-Members"

2. Nel TRUSTING forest (contoso.com):
   - Domain Local Group "DL-SharedDocs-Read"
   - Aggiungere "FABRIKAM\GG-Project-Members" a "DL-SharedDocs-Read"

3. Sulla risorsa:
   - Assegnare permessi a "DL-SharedDocs-Read"

Vantaggi:
- L'admin di fabrikam.com gestisce la membership (chi accede)
- L'admin di contoso.com gestisce i permessi (a cosa accedono)
```

### Foreign Security Principals

Quando si aggiunge un utente/gruppo di un trusted forest a un gruppo locale, AD crea un **Foreign Security Principal (FSP)** nel container "ForeignSecurityPrincipals":

```powershell
# Visualizzare FSP nel dominio
Get-ADObject -SearchBase "CN=ForeignSecurityPrincipals,DC=contoso,DC=com" `
    -Filter * -Properties * | Select-Object Name, ObjectClass

# Tradurre SID in nome leggibile
$sid = New-Object System.Security.Principal.SecurityIdentifier("S-1-5-21-FABRIKAM-1234")
$account = $sid.Translate([System.Security.Principal.NTAccount])
Write-Output "Account: $account"
```

### Universal Groups e Cross-Forest

Gli Universal Groups sono memorizzati nel Global Catalog e visibili cross-forest:

| Tipo Gruppo | Visibilità | Cross-Forest |
|---|---|---|
| **Domain Local** | Solo nel dominio | No (non in GC) |
| **Global** | Solo nel forest | Si (via GC) |
| **Universal** | GC di tutto il forest | Si (via GC) |

---

## Cross-Forest AGDLP in Pratica

### Universal Group Membership e Multi-Forest

In un ambiente multi-forest, la strategia AGDLP (Account → Global → Domain Local → Permission) si estende con l'aggiunta di Universal Groups per aggregare Global Groups cross-domain all'interno dello stesso forest.

```
Scenario: Contoso (3 domini) + Fabrikam (2 domini) — Forest Trust bidirezionale

Forest contoso.com:
├── contoso.com
│   ├── GG-Engineering (Global — ingegneri sede centrale)
│   └── UG-AllEngineers (Universal — aggrega tutti gli ingegneri contoso)
├── europe.contoso.com
│   └── GG-EU-Engineering (Global — ingegneri EU)
└── asia.contoso.com
    └── GG-Asia-Engineering (Global — ingegneri Asia)

UG-AllEngineers contiene:
  - GG-Engineering
  - GG-EU-Engineering
  - GG-Asia-Engineering

Forest fabrikam.com:
├── fabrikam.com
│   └── GG-Fab-Engineering (Global — ingegneri fabrikam)

Nel trusting forest (contoso.com), sulla risorsa:
DL-ProjectDocs-RW (Domain Local) contiene:
  - UG-AllEngineers (Universal — tutti gli ingegneri contoso)
  - FABRIKAM\GG-Fab-Engineering (Global — ingegneri fabrikam, via FSP)

Share \\fileserver.contoso.com\ProjectDocs
  → ACL: DL-ProjectDocs-RW = Read/Write
```

**Perché non usare un Universal Group cross-forest:** Gli Universal Groups possono contenere membri solo dal proprio forest. Non è possibile aggiungere un Global Group di fabrikam.com a un Universal Group di contoso.com. Per l'accesso cross-forest, si aggiungono i Global Groups del forest trusted direttamente al Domain Local Group nel trusting forest.

### Pulizia FSP Orfani

Quando un trust viene rimosso o un oggetto nel trusted forest viene eliminato, i Foreign Security Principals corrispondenti diventano orfani. Questi FSP orfani appaiono come SID non risolti nelle ACL:

```powershell
# Trovare FSP orfani (SID non risolvibili)
$fspContainer = "CN=ForeignSecurityPrincipals,DC=contoso,DC=com"
Get-ADObject -SearchBase $fspContainer -Filter * -Properties * | ForEach-Object {
    $sid = $_.Name
    try {
        $resolved = (New-Object System.Security.Principal.SecurityIdentifier($sid)).Translate(
            [System.Security.Principal.NTAccount]
        )
        # SID risolvibile — OK
    } catch {
        [PSCustomObject]@{
            SID        = $sid
            DN         = $_.DistinguishedName
            Stato      = "ORFANO — non risolvibile"
        }
    }
}

# Rimuovere FSP orfani (dopo verifica)
# Remove-ADObject -Identity "CN=$orphanSID,$fspContainer" -Confirm
```

---

## Migrazione Multi-Forest

### Strategie di Migrazione

| Strategia | Descrizione | Complessità | Downtime |
|---|---|---|---|
| **Consolidamento** | Unire N forest in 1 | Alta | Variabile |
| **Ristrutturazione** | Riorganizzare domini tra forest | Alta | Variabile |
| **Upgrade in-place** | Aggiornare forest functional level | Bassa | Minimo |
| **In-place + ristrutturazione** | Combinazione | Media | Medio |

### Piano di Migrazione Multi-Forest

```
Fase 1 — Assessment (2-4 settimane)
├── Inventory di tutti i forest (domini, DC, oggetti)
├── Mappatura trust esistenti
├── Identificazione applicazioni con dipendenze AD
├── Analisi GPO e permessi
└── Assessment DNS

Fase 2 — Preparazione (2-4 settimane)
├── Creare forest trust bidirezionale
├── Configurare DNS cross-forest
├── Installare ADMT nel target forest
├── Creare gruppi di migrazione
└── Testare connettività cross-forest

Fase 3 — Migrazione pilota (1-2 settimane)
├── Migrare un OU pilota con ADMT
├── Verificare accesso a risorse con SID History
├── Testare applicazioni
├── Documentare problemi
└── Risolvere issues

Fase 4 — Migrazione produzione (4-12 settimane)
├── Migrare utenti a batch (per OU/dipartimento)
├── Migrare computer (re-join al nuovo dominio)
├── Migrare gruppi
├── Re-ACL risorse (progressivo)
└── Migrare service account

Fase 5 — Decommissioning (2-4 settimane)
├── Verificare che tutti gli utenti migrati funzionino
├── Riabilitare SID filtering
├── Rimuovere trust con source forest
├── Decommissionare DC del source forest
└── Pulizia DNS
```

### SID History nella Migrazione

```
Pre-migrazione:
Utente: FABRIKAM\john (SID: S-1-5-21-FABRIKAM-1234)
Accesso a: \\fileserver.fabrikam.com\share (ACL: S-1-5-21-FABRIKAM-1234 = Read)

Post-migrazione (con SID History):
Utente: CONTOSO\john (SID: S-1-5-21-CONTOSO-5678)
SID History: S-1-5-21-FABRIKAM-1234
Accesso a: \\fileserver.fabrikam.com\share → token contiene entrambi i SID → accesso funziona

Post-cleanup (SID History rimosso, ACL aggiornate):
Utente: CONTOSO\john (SID: S-1-5-21-CONTOSO-5678)
Accesso a: \\fileserver.contoso.com\share (ACL: S-1-5-21-CONTOSO-5678 = Read)
```

---

## ADMT — Active Directory Migration Tool

### Panoramica

ADMT (Active Directory Migration Tool) è lo strumento Microsoft per la migrazione di oggetti tra domini/forest AD. Supporta migrazione di utenti, gruppi, computer, e service account con preservazione del SID History.

### Prerequisiti ADMT

1. Forest trust bidirezionale tra source e target forest
2. ADMT installato su un member server nel target domain
3. SQL Server (anche Express) per il database ADMT
4. Account con privilegi di Domain Admin in entrambi i domain
5. Auditing abilitato nel source domain (audit account management)
6. SID filtering disabilitato temporaneamente (per SID History)

### Installazione ADMT

```powershell
# 1. Installare SQL Server Express (o Standard) sul server ADMT
# 2. Download ADMT v3.2 da Microsoft Download Center
# 3. Installare ADMT

# Prerequisiti source domain per SID History:
# 1. Creare un local group nel source domain: {source_domain}$$$
#    (es. FABRIKAM$$$) — necessario per SID History migration
New-ADGroup -Name "FABRIKAM$$$" -GroupScope DomainLocal -Path "CN=Users,DC=fabrikam,DC=com"

# 2. Abilitare audit account management nel source domain (GPO)
# Default Domain Controllers Policy → Computer Configuration → Policies
# → Windows Settings → Security Settings → Advanced Audit Policy
# → Account Management → Audit User Account Management: Success, Failure

# 3. Abilitare accesso remoto al registry del source domain
# Necessario per password migration agent
```

### Migrazione Utenti con ADMT

```powershell
# Via GUI: ADMT Console → User Account Migration Wizard
# Via command line:

# Migrazione utenti con SID History e password
ADMT USER /N "User1" "User2" /SD:"fabrikam.com" /TD:"contoso.com" `
    /TO:"OU=MigratedUsers,DC=contoso,DC=com" `
    /MSS:YES `        # Migrate SID History
    /MPS:YES `         # Migrate passwords (richiede Password Export Server)
    /TRP:YES `         # Translate roaming profiles
    /UUR:YES `         # Update user rights
    /FSD:YES           # Fix source domain permissions

# Migrazione batch da file
ADMT USER /IF:"C:\Migration\users.csv" /SD:"fabrikam.com" /TD:"contoso.com" `
    /TO:"OU=MigratedUsers,DC=contoso,DC=com" /MSS:YES /MPS:YES
```

### Migrazione Gruppi

```powershell
# Migrare gruppi con membership
ADMT GROUP /N "Group1" "Group2" /SD:"fabrikam.com" /TD:"contoso.com" `
    /TO:"OU=MigratedGroups,DC=contoso,DC=com" `
    /MSS:YES `         # SID History
    /MGM:YES `         # Migrate group membership
    /FIXM:YES          # Fix membership
```

### Migrazione Computer

```powershell
# Migrare computer al nuovo dominio
ADMT COMPUTER /N "PC001" "PC002" /SD:"fabrikam.com" /TD:"contoso.com" `
    /TO:"OU=Workstations,DC=contoso,DC=com" `
    /TRP:YES `         # Translate roaming profiles
    /TLF:YES `         # Translate local profiles
    /RN:30             # Riavvio in 30 secondi

# Il computer viene rimosso dal source domain e aggiunto al target domain
# Un reboot è necessario per completare il join
```

### Security Translation

Dopo la migrazione degli oggetti, le ACL sulle risorse devono essere aggiornate:

```powershell
# Traduzione sicurezza su file server
ADMT SECURITY /SD:"fabrikam.com" /TD:"contoso.com" `
    /TO:"OU=MigratedUsers,DC=contoso,DC=com" `
    /TST:REPLACE `     # Translate security: Replace old SID with new SID
    /TFC:YES `         # Translate files and folders
    /TSR:YES `         # Translate shares
    /TLG:YES `         # Translate local groups
    /TRP:YES           # Translate registry
```

---

## ADMT — Deep Dive Operativo

### Password Migration con Password Export Server (PES)

La migrazione delle password richiede l'installazione del **Password Export Server** su un DC nel source domain. Questo componente esporta le password in modo sicuro verso il server ADMT nel target domain.

```powershell
# Installazione PES sul DC source:
# 1. Scaricare PES dalla stessa pagina di download ADMT
# 2. Installare PES sul DC (richiede riavvio)
# 3. Il PES genera una chiave di crittografia (.pes file)
# 4. Copiare la chiave sul server ADMT nel target domain

# Verifica servizio PES
Get-Service -Name "Password Export Server Service" -ComputerName "dc01.fabrikam.com"

# Avviare il servizio PES (deve essere avviato manualmente per ogni sessione)
# Il servizio si arresta automaticamente dopo 5 minuti di inattività
Invoke-Command -ComputerName "dc01.fabrikam.com" -ScriptBlock {
    Start-Service "Password Export Server Service"
    Get-Service "Password Export Server Service" | Select-Object Status, Name
}

# Migrazione con password:
ADMT USER /N "User1" /SD:"fabrikam.com" /TD:"contoso.com" `
    /TO:"OU=MigratedUsers,DC=contoso,DC=com" `
    /MSS:YES /MPS:YES `
    /PESPATH:"C:\ADMT\Keys\fabrikam.pes"
```

### Migrazione Service Account

I service account richiedono attenzione speciale: un cambio di credenziali può interrompere servizi critici.

```powershell
# 1. Inventory dei service account nel source domain
ADMT SERVICE /N "svc-*" /SD:"fabrikam.com"

# 2. Il wizard identifica quali servizi usano l'account su quali computer
# Output: lista di computer e servizi associati a ciascun service account

# 3. Migrare il service account con aggiornamento automatico dei servizi
ADMT USER /N "svc-sql" /SD:"fabrikam.com" /TD:"contoso.com" `
    /TO:"OU=ServiceAccounts,DC=contoso,DC=com" `
    /MSS:YES /MPS:YES `
    /TranslateLocalGroups:YES `
    /UpdateServiceAccount:YES

# 4. Dopo la migrazione, verificare che i servizi si avviino correttamente
# sui computer target con le nuove credenziali
```

### Rollback della Migrazione

Se la migrazione di un batch di utenti causa problemi, è possibile un rollback parziale:

```powershell
# Opzione 1: Disabilitare gli account migrati nel target e riabilitare nel source
# Gli utenti useranno gli account originali via trust

# Opzione 2: ADMT Undo wizard (limitato)
# ADMT Console → Action → Undo Last Migration

# Opzione 3: Rollback manuale
# 1. Riabilitare l'account nel source domain
Get-ADUser -Identity "john" -Server "fabrikam.com" | Enable-ADAccount

# 2. Disabilitare l'account nel target domain
Get-ADUser -Identity "john" -Server "contoso.com" | Disable-ADAccount

# 3. Verificare che il SID History sia ancora valido
Get-ADUser -Identity "john" -Server "contoso.com" -Properties sIDHistory
```

---

## Consolidamento Domini

### Scenario: Unire Più Domini in un Singolo Forest

Il consolidamento domini riduce la complessità operativa eliminando domini non più necessari. Casi tipici:

- Domini child creati per motivi organizzativi ormai superati
- Domini acquisiti che devono essere integrati
- Riduzione del numero di DC per taglio costi

### Piano di Consolidamento Intra-Forest

```
Scenario: contoso.com ha 3 child domain da consolidare nel root

contoso.com (root)
├── europe.contoso.com → consolidare in contoso.com
├── asia.contoso.com → consolidare in contoso.com
└── africa.contoso.com → consolidare in contoso.com

Piano:
Fase 1 — Creare struttura OU nel root domain per ospitare gli oggetti migrati
Fase 2 — Migrare utenti/gruppi/computer con ADMT (intra-forest = più semplice)
Fase 3 — Aggiornare GPO e permessi
Fase 4 — Rimuovere i child domain (demote DC)
Fase 5 — Rimuovere le delegazioni DNS e i record orfani
```

### Depromozione DC e Rimozione Dominio

```powershell
# 1. Migrare tutti gli oggetti dal child domain al root domain
#    (usando ADMT o Move-ADObject per intra-forest)

# Move-ADObject per spostamenti intra-forest (alternativa ad ADMT):
# NOTA: Move-ADObject funziona cross-domain nello stesso forest
$usersToMove = Get-ADUser -Filter * -SearchBase "OU=Users,DC=europe,DC=contoso,DC=com" `
    -Server "europe.contoso.com"

foreach ($user in $usersToMove) {
    Move-ADObject -Identity $user.DistinguishedName `
        -TargetPath "OU=Europe-Migrated,DC=contoso,DC=com" `
        -TargetServer "contoso.com"
}

# 2. Trasferire i ruoli FSMO del child domain (se presenti)
Move-ADDirectoryServerOperationMasterRole -Identity "dc-root01" `
    -OperationMasterRole RIDMaster, InfrastructureMaster, PDCEmulator

# 3. Depromovere tutti i DC del child domain (ultimo DC = rimozione dominio)
# Su ogni DC tranne l'ultimo:
Uninstall-ADDSDomainController -DemoteOperationMasterRole `
    -Credential (Get-Credential) -Force

# Sull'ultimo DC del child domain (rimuove il dominio dal forest):
Uninstall-ADDSDomainController -LastDomainControllerInDomain `
    -RemoveApplicationPartitions -DemoteOperationMasterRole `
    -Credential (Get-Credential) -Force

# 4. Pulizia metadata (se la depromozione non è pulita)
# Su un DC del root domain:
ntdsutil
# metadata cleanup → connections → connect to server dc-root01
# select operation target → list domains → select domain <n>
# list servers in domain → select server <n> → quit
# remove selected server

# 5. Pulizia DNS
Get-DnsServerZone | Where-Object { $_.ZoneName -like "*europe.contoso.com*" } |
    Remove-DnsServerZone -Force
```

### Rimozione di un Trust

Quando un forest trust non è più necessario (dopo migrazione completa o fine partnership):

```powershell
# 1. Verificare che nessun utente dipenda dal trust
# Controllare event log per autenticazioni cross-trust recenti
Get-WinEvent -LogName Security -FilterXPath `
    "*[System[EventID=4624] and EventData[Data[@Name='TargetDomainName']='FABRIKAM']]" `
    -MaxEvents 100

# 2. Rimuovere il trust da entrambi i lati
# Lato contoso.com:
netdom trust contoso.com /d:fabrikam.com /remove /force

# Lato fabrikam.com:
netdom trust fabrikam.com /d:contoso.com /remove /force

# 3. Rimuovere i conditional forwarder DNS
Remove-DnsServerConditionalForwarderZone -Name "fabrikam.com" -Force

# 4. Rimuovere FSP orfani
Get-ADObject -SearchBase "CN=ForeignSecurityPrincipals,DC=contoso,DC=com" `
    -Filter * | Where-Object { $_.Name -match "S-1-5-21-FABRIKAM" } |
    Remove-ADObject -Confirm

# 5. Audit delle ACL che referenziano il dominio rimosso
# Cercare SID non risolti nelle ACL di file server, share, GPO
```

---

## Ristrutturazione Domini

### Inter-Forest vs Intra-Forest Migration

| Criterio | Intra-Forest (stesso forest) | Inter-Forest (forest diversi) |
|---|---|---|
| **Strumento** | Move-ADObject (nativo) o ADMT | ADMT (obbligatorio) |
| **SID** | Preservato (oggetto spostato) | Nuovo SID + SID History |
| **Password** | Preservata | Richiede PES o reset |
| **Membership gruppi** | Preservata | Deve essere ricreata/tradotta |
| **GPO** | Non seguono l'oggetto | Non applicabili cross-forest |
| **Complessità** | Bassa | Alta |
| **Downtime utente** | Minimo | Significativo (relogon) |

### Migrazione Intra-Forest con Move-ADObject

```powershell
# Move-ADObject sposta un oggetto tra domini nello stesso forest
# L'oggetto mantiene il proprio SID e tutti i riferimenti

# Spostare un utente da europe.contoso.com a contoso.com
$user = Get-ADUser -Identity "john.smith" -Server "europe.contoso.com"
Move-ADObject -Identity $user.DistinguishedName `
    -TargetPath "OU=Users,DC=contoso,DC=com" `
    -TargetServer "contoso.com"

# Spostare un intero OU (con tutti i contenuti)
$ou = Get-ADOrganizationalUnit -Identity "OU=Finance,DC=europe,DC=contoso,DC=com" `
    -Server "europe.contoso.com"
Move-ADObject -Identity $ou.DistinguishedName `
    -TargetPath "OU=Europe,DC=contoso,DC=com" `
    -TargetServer "contoso.com"

# Spostamento batch con logging
$users = Get-ADUser -Filter * -SearchBase "OU=Sales,DC=europe,DC=contoso,DC=com" `
    -Server "europe.contoso.com"

$log = foreach ($u in $users) {
    try {
        Move-ADObject -Identity $u.DistinguishedName `
            -TargetPath "OU=Sales-Migrated,DC=contoso,DC=com" `
            -TargetServer "contoso.com" -ErrorAction Stop
        [PSCustomObject]@{ User = $u.SamAccountName; Stato = "OK" }
    } catch {
        [PSCustomObject]@{ User = $u.SamAccountName; Stato = "ERRORE: $_" }
    }
}
$log | Export-Csv -Path "C:\Migration\move-log.csv" -NoTypeInformation
```

### Migrazione Inter-Forest — Checklist Operativa

```
Checklist migrazione inter-forest (ADMT):

Pre-migrazione:
[ ] Forest trust bidirezionale attivo e validato
[ ] SID filtering disabilitato temporaneamente
[ ] PES installato su DC source (per password migration)
[ ] Gruppo {SOURCE}$$$ creato nel source domain
[ ] Audit account management abilitato nel source
[ ] Mapping OU definito (source OU → target OU)
[ ] Comunicazione agli utenti pianificata

Migrazione:
[ ] Gruppi migrati PRIMA degli utenti (per preservare membership)
[ ] Utenti migrati con SID History e password
[ ] Computer migrati con security translation
[ ] Service account migrati con aggiornamento servizi
[ ] Profile roaming tradotti

Post-migrazione:
[ ] Security translation eseguita su file server, share, stampanti
[ ] GPO nel target domain applicate/create
[ ] Test accesso risorse con account migrati
[ ] SID filtering riabilitato
[ ] Cleanup SID History (dopo periodo di transizione)
[ ] Trust rimosso (quando non più necessario)
```

---

## Cross-Forest PowerShell

### Get-ADTrust — Query Trust Esistenti

```powershell
# Elencare tutti i trust del dominio corrente
Get-ADTrust -Filter *

# Trust con dettagli completi
Get-ADTrust -Filter * -Properties * | Select-Object `
    Name, Direction, TrustType, DisallowTransivity, `
    SelectiveAuthentication, SIDFilteringQuarantined, `
    SIDFilteringForestAware, ForestTransitive, `
    IntraForest, IsTreeParent, IsTreeRoot, `
    TGTDelegation, FlatName, Target

# Filtrare per tipo di trust
Get-ADTrust -Filter { TrustType -eq "Forest" }
Get-ADTrust -Filter { ForestTransitive -eq $true }
Get-ADTrust -Filter { IntraForest -eq $true }    # Trust interni (parent-child, tree-root)

# Trust verso un dominio specifico
Get-ADTrust -Identity "fabrikam.com" -Properties *
```

### New-ADTrust — Creazione Trust (Windows Server 2025)

A partire da Windows Server 2025, il cmdlet `New-ADTrust` (modulo ActiveDirectory aggiornato) permette la creazione di trust interamente via PowerShell, senza dipendere da `netdom`:

```powershell
# Creazione forest trust bidirezionale (Windows Server 2025+)
# Documentazione: https://learn.microsoft.com/en-us/powershell/module/activedirectory/
# (consultato: 2026-05-23)

# Forest trust con selective authentication
$trustPassword = ConvertTo-SecureString "F0rest!Trust#2026" -AsPlainText -Force

# Lato contoso.com:
New-ADTrust -Name "fabrikam.com" `
    -TrustType Forest `
    -Direction Bidirectional `
    -TrustPassword $trustPassword `
    -SelectiveAuthentication $true

# Verifica
Get-ADTrust -Identity "fabrikam.com" | Format-List *
```

### Gestione Trust Ticket con PowerShell

```powershell
# Configurare il TGT delegation per un trust
# (per scenari dove la delegation cross-forest è necessaria)
Set-ADTrust -Identity "fabrikam.com" -TGTDelegation $true

# Verificare la configurazione corrente
Get-ADTrust -Identity "fabrikam.com" -Properties TGTDelegation |
    Select-Object Name, TGTDelegation

# Modificare selective authentication su trust esistente
Set-ADTrust -Identity "fabrikam.com" -SelectiveAuthentication $true

# Aggiornare la password del trust
Set-ADTrust -Identity "fabrikam.com" -TrustPassword (
    ConvertTo-SecureString "NewP@ss!2026#Secure" -AsPlainText -Force
)
```

### Query Cross-Forest con PowerShell

```powershell
# Cercare utenti nel forest remoto (via trust)
Get-ADUser -Filter "Department -eq 'Engineering'" -Server "fabrikam.com" `
    -Properties Department, Mail | Select-Object Name, Department, Mail

# Cercare via Global Catalog (più veloce per query ampie)
Get-ADUser -Filter "Name -like 'John*'" -Server "gc.fabrikam.com:3268" `
    -Properties DisplayName, Mail

# Verificare membership di gruppi cross-forest
Get-ADGroupMember -Identity "GG-ProjectTeam" -Server "fabrikam.com" -Recursive |
    Select-Object Name, SamAccountName, DistinguishedName

# Confrontare oggetti tra forest (esempio: audit utenti duplicati)
$localUsers = Get-ADUser -Filter * -Properties Mail | Where-Object { $_.Mail }
$remoteUsers = Get-ADUser -Filter * -Server "fabrikam.com" -Properties Mail |
    Where-Object { $_.Mail }

$duplicates = Compare-Object $localUsers $remoteUsers -Property Mail -IncludeEqual |
    Where-Object { $_.SideIndicator -eq "==" }
Write-Output "Utenti con email duplicata cross-forest: $($duplicates.Count)"
```

---

## Multi-Forest Administration — PAM Trust

### Privileged Access Management (PAM) Trust

Il PAM trust è un tipo speciale di forest trust introdotto con Windows Server 2016 FFL. È progettato per il modello **Privileged Access Management** con Microsoft Identity Manager (MIM). Il PAM trust crea un trust unidirezionale dal forest di produzione verso un forest di amministrazione dedicato (bastion forest).

```
Forest di produzione           Bastion Forest (PAM)
contoso.com ──── PAM trust ──→ priv.contoso.com
(trusting)                     (trusted)

Caratteristiche del PAM trust:
- Trust unidirezionale (solo dal production al bastion)
- SID filtering disabilitato per design (necessario per shadow principals)
- Forest isolation completa per gli admin
- Supporta Time-Based Group Membership (appartenenza temporanea a gruppi)
```

### Shadow Principals

I **shadow principal** sono oggetti nel bastion forest che "proiettano" l'appartenenza a gruppi privilegiati del forest di produzione. Un admin nel bastion forest ottiene temporaneamente l'appartenenza a un gruppo del production forest, senza che il gruppo nel production forest venga modificato.

```powershell
# Creare un shadow principal nel bastion forest
# (richiede MIM PAM installato e configurato)

# Esempio concettuale via PowerShell:
# Nel bastion forest (priv.contoso.com):

# 1. Creare il shadow principal group
New-ADGroup -Name "Shadow-DomainAdmins-Contoso" `
    -GroupScope Global `
    -Path "OU=ShadowPrincipals,DC=priv,DC=contoso,DC=com" `
    -OtherAttributes @{
        'msDS-ShadowPrincipalSid' = 'S-1-5-21-CONTOSO-512'  # SID di Domain Admins in contoso.com
    }

# 2. Quando un admin necessita accesso privilegiato:
# MIM riceve la richiesta (via portale self-service o approvazione)
# MIM aggiunge l'admin al shadow group con Time-Based Membership
# L'admin ottiene temporaneamente i privilegi di Domain Admins in contoso.com

# Verificare shadow principals
Get-ADGroup -SearchBase "OU=ShadowPrincipals,DC=priv,DC=contoso,DC=com" `
    -Filter * -Properties msDS-ShadowPrincipalSid | 
    Select-Object Name, @{N='ShadowedSID';E={$_.'msDS-ShadowPrincipalSid'}}
```

### Time-Based Group Membership

Con FFL 2016+ e PAM trust, è possibile assegnare l'appartenenza a un gruppo con una scadenza temporale (TTL). Questo è fondamentale per il principio di accesso Just-In-Time (JIT):

```powershell
# Aggiungere un membro a un gruppo con scadenza temporale
# (Richiede FFL 2016+ e PAM abilitato)

# Aggiungere per 4 ore (14400 secondi)
Add-ADGroupMember -Identity "Shadow-DomainAdmins-Contoso" `
    -Members "admin-john" `
    -MemberTimeToLive (New-TimeSpan -Hours 4)

# Verificare la membership con TTL
Get-ADGroupMember -Identity "Shadow-DomainAdmins-Contoso" | ForEach-Object {
    $member = Get-ADObject -Identity $_.DistinguishedName -Properties memberOf, msDS-MemberTimeToLive
    [PSCustomObject]@{
        Member = $_.Name
        TTL    = $_.'msDS-MemberTimeToLive'
    }
}
```

### Requisiti per PAM Trust

| Requisito | Dettaglio |
|---|---|
| **Bastion forest FFL** | Windows Server 2016 |
| **Production forest FFL** | Windows Server 2012 R2 (minimo) |
| **MIM** | Microsoft Identity Manager 2016+ con componente PAM |
| **Trust type** | Forest trust con flag PAM (`/EnablePAMTrust:YES`) |
| **SID filtering** | Disabilitato sul PAM trust (per design) |
| **DC bastion** | Windows Server 2016+ (consigliato 2022/2025) |

```powershell
# Creare un PAM trust (dal forest di produzione verso il bastion)
netdom trust contoso.com /d:priv.contoso.com `
    /add /twoway:no /passwordt:"P@mTrust!2026" `
    /foresthttps:yes /EnablePAMTrust:YES
```

---

## Global Catalog e Universal Group Membership Caching

### Ruolo del Global Catalog nei Trust

Il Global Catalog (GC) contiene una replica parziale di tutti gli oggetti in tutti i domini del forest. È essenziale per:

1. **Autenticazione cross-domain**: risolve universal group membership
2. **UPN logon**: mappa UPN all'account corretto
3. **Cross-forest query**: ricerca oggetti in altri domini

```powershell
# Verificare DC che sono Global Catalog
Get-ADDomainController -Filter {IsGlobalCatalog -eq $true} | 
    Select-Object Name, IPv4Address, Site, IsGlobalCatalog

# Verificare GC raggiungibilità
nltest /dsgetdc:fabrikam.com /GC

# Query al Global Catalog (porta 3268)
Get-ADUser -Filter "Name -like 'John*'" -Server "gc01.fabrikam.com:3268" `
    -Properties DisplayName, Mail
```

### Universal Group Membership Caching (UGMC)

In siti con connettività lenta verso un GC, UGMC memorizza in cache la membership dei gruppi universali:

```powershell
# Abilitare UGMC su un sito
# Active Directory Sites and Services → Sites → [SiteName] → NTDS Site Settings
# → Properties → Enable Universal Group Membership Caching

# Via PowerShell
$siteDN = "CN=NTDS Site Settings,CN=BranchOffice,CN=Sites,CN=Configuration,DC=contoso,DC=com"
Set-ADObject -Identity $siteDN -Replace @{options = 32}  # 0x20 = UGMC enabled

# Verifica
Get-ADObject -Identity $siteDN -Properties options | Select-Object options
# options = 32 → UGMC attivo
```

### Impatto sui Trust

| Scenario | Senza GC nel sito | Con GC nel sito | Con UGMC |
|---|---|---|---|
| **Autenticazione locale** | Lenta (query GC remoto) | Veloce | Veloce (cache) |
| **Gruppi universali** | Query GC remoto | Locale | Cache (refresh ogni 8h) |
| **UPN logon** | Necessita GC | Locale | N/A (serve GC) |
| **Cross-forest query** | GC remoto | Locale | N/A |

---

## Forest Functional Levels

### Livelli Funzionali

| Forest Functional Level | Trust Supportati | Caratteristiche Chiave |
|---|---|---|
| **Windows 2000** | Parent-child, tree-root, external | Base |
| **Windows Server 2003** | + Forest trust | Forest trust, name suffix routing |
| **Windows Server 2008** | Tutti sopra | Fine-grained password policy |
| **Windows Server 2008 R2** | Tutti sopra | AD Recycle Bin |
| **Windows Server 2012** | Tutti sopra | Claims-based auth, compound auth |
| **Windows Server 2012 R2** | Tutti sopra | Authentication policies/silos |
| **Windows Server 2016** | Tutti sopra | Privileged Access Management |
| **Windows Server 2025** | Tutti sopra | Miglioramenti sicurezza |

### Impatto del Functional Level sui Trust

```powershell
# Verificare forest functional level
(Get-ADForest).ForestMode

# Verificare domain functional level
(Get-ADDomain).DomainMode

# Per creare un forest trust: entrambi i forest devono essere almeno 2003

# Per usare claims-based auth cross-forest: entrambi 2012+

# Per usare authentication policies/silos cross-forest: entrambi 2012 R2+
```

### Alzare il Functional Level

```powershell
# ATTENZIONE: operazione irreversibile

# Alzare domain functional level
Set-ADDomainMode -DomainMode Windows2016Domain -Identity "contoso.com"

# Alzare forest functional level (richiede tutti i domain al livello target)
Set-ADForestMode -ForestMode Windows2016Forest -Identity "contoso.com"

# Prerequisiti:
# 1. Tutti i DC nel forest devono eseguire almeno la versione richiesta
# 2. Tutti i domain nel forest devono essere al domain functional level richiesto
# 3. Backup completo prima dell'operazione
```

---

## Group Policy Cross-Forest

### Limitazioni GPO Cross-Forest

Le Group Policy Objects (GPO) **non si applicano cross-forest**. Le GPO sono limitate al forest in cui sono create. Tuttavia, ci sono scenari in cui la configurazione cross-forest è rilevante:

| Scenario | Soluzione |
|---|---|
| Utente forest A accede a RDS in forest B | GPO Loopback in forest B si applica |
| Software distribution cross-forest | Usare Intune/SCCM anziché GPO |
| Security settings cross-forest | Distribuire via Intune o script |
| Printer/share mapping cross-forest | GPO con logon script nel forest locale |

### GPO Loopback Processing Cross-Trust

Quando un utente di un trusted forest accede a un computer nel trusting forest (es. RDS server):

```
Utente: FABRIKAM\john → logon su rds.contoso.com

Senza Loopback:
- Computer GPO di contoso.com si applica (computer settings)
- User GPO di fabrikam.com TENTANO di applicarsi (possono fallire cross-forest)

Con Loopback (Replace mode):
- Computer GPO di contoso.com si applica
- User settings dalle GPO di contoso.com (legate all'OU del computer) si applicano
- Le GPO di fabrikam.com vengono ignorate

Raccomandazione: SEMPRE usare Loopback Replace per server acceduti cross-forest
```

```powershell
# Configurare Loopback Processing via GPO
# Computer Configuration → Policies → Administrative Templates
# → System → Group Policy → Configure user Group Policy loopback processing mode
# → Enabled → Mode: Replace
```

---

## Azure AD Connect con Multiple Forest

### Topologie Multi-Forest Supportate

**Topologia 1 — Single Azure AD Connect, Multiple Forest:**

```
Forest A (contoso.com)   Forest B (fabrikam.com)
       \                    /
        → Azure AD Connect ←
              |
         Entra ID (tenant unico)

Requisiti:
- Azure AD Connect installato in un forest con connettività a tutti gli altri
- Ogni forest deve avere trust o AD connector configurato
- Utenti univoci cross-forest (matching rule: mail, UPN, o objectSID)
```

**Topologia 2 — Multiple Azure AD Connect (per forest):**

```
NON SUPPORTATA per un singolo tenant Entra ID
(Solo un Azure AD Connect sync server attivo per tenant)

Eccezione: Azure AD Connect Cloud Sync (agent-based) supporta multi-forest
```

**Topologia 3 — Cloud Sync con Multiple Forest:**

```
Forest A → Cloud Sync Agent A → Entra ID
Forest B → Cloud Sync Agent B → Entra ID

Vantaggi: non richiede trust tra forest
Ogni forest ha il proprio lightweight agent
```

### Configurazione Azure AD Connect Multi-Forest

```powershell
# Durante l'installazione di Azure AD Connect:
# 1. Selezionare "Customize" → "Connect your directories"
# 2. Aggiungere ogni forest:
#    - Directory type: Active Directory
#    - Forest: contoso.com → Create new AD account o usare account esistente
#    - Forest: fabrikam.com → Account con Enterprise Admin (o delegato)
# 3. Configurare "Uniquely identifying your users":
#    - Users are represented only once across all directories (default)
#    - OPPURE: User identities exist across multiple directories (matching by mail/UPN)
# 4. Configurare "Filtering":
#    - Tutti i domini, oppure domini/OU specifiche per forest
# 5. Configurare "Optional Features":
#    - Password Hash Sync, Pass-through Auth, Federation

# Verifica post-configurazione
Start-ADSyncSyncCycle -PolicyType Delta
Get-ADSyncConnector | Select-Object Name, Type, Partitions
```

### Matching Rules

| Metodo | Attributo | Scenario |
|---|---|---|
| **Mail matching** | mail | Utenti con mailbox in Exchange |
| **UPN matching** | userPrincipalName | UPN uguali tra forest |
| **ObjectSID + msExchMasterAccountSID** | SID | Resource forest con account forest |
| **Source anchor (ms-DS-ConsistencyGuid)** | GUID | Default mapping |

### Problemi Comuni Multi-Forest Sync

```powershell
# Verificare errori di sync
Get-ADSyncScheduler
Get-ADSyncCSObject -ConnectorName "contoso.com" -DistinguishedName "CN=John,OU=Users,DC=contoso,DC=com"

# Verificare oggetti non sincronizzati
$errors = Get-ADSyncRunStepResult | Where-Object { $_.StepResult -ne "success" }
$errors | Format-List ConnectorName, StepType, StepResult

# Verifica matching
Get-ADSyncCSObject -ConnectorName "contoso.com" | Where-Object {
    $_.HasJoinError -or $_.HasSyncError
} | Select-Object DistinguishedName, HasJoinError, HasSyncError
```

---

## Monitoraggio Trust Health

### Strumenti di Monitoraggio

#### nltest — Verifica Canale Sicuro

```powershell
# Verifica stato del secure channel verso il trusted domain
nltest /sc_verify:fabrikam.com
# Output atteso:
# Flags: 80 HAS_IP HAS_TIMESERV
# Trusted DC Name \\dc01.fabrikam.com
# Trusted DC Connection Status Status = 0 0x0 NERR_Success
# Trust Verification Status = 0 0x0 NERR_Success

# Se Status != 0, il trust ha problemi
# Codici comuni:
# 0x00000005 = Access Denied (credenziali trust scadute)
# 0x0000054B = The specified domain does not exist (DNS failure)
# 0x00000702 = The trust relationship failed (trust rotto)

# Query tutti i DC del trusted domain
nltest /sc_query:fabrikam.com

# Forzare la riscoperta del DC trusted
nltest /dsgetdc:fabrikam.com /force
```

#### netdom — Verifica e Gestione Trust

```powershell
# Verifica completa del trust
netdom trust contoso.com /d:fabrikam.com /verify

# Verificare le proprietà del trust
netdom trust contoso.com /d:fabrikam.com /verify /verbose

# Reset della password del trust (se il secure channel è rotto)
netdom trust contoso.com /d:fabrikam.com /reset /passwordt:"NewTrustP@ss!2026"

# Verificare stato SID filtering
netdom trust contoso.com /d:fabrikam.com /FilterSids

# Verificare selective authentication
netdom trust contoso.com /d:fabrikam.com /SelectiveAuth
```

### Event ID Chiave per Trust Monitoring

| Event ID | Log | Significato | Azione |
|---|---|---|---|
| **4768** | Security | TGT request (include cross-realm) | Monitorare per autenticazioni cross-trust anomale |
| **4769** | Security | TGS request | Tracciare accesso a risorse cross-forest |
| **4770** | Security | TGT renewal | Normalmente informativo |
| **4771** | Security | Kerberos pre-authentication failed | Possibile brute force cross-trust |
| **4625** | Security | Logon failed | Cercare failure reason per selective auth blocks |
| **4675** | Security | SID filtering applied | SID History injection tentata e bloccata |
| **5827-5831** | System | NTLM authentication | Monitorare NTLM fallback cross-trust |

```powershell
# Script di monitoraggio trust health complessivo
function Get-TrustHealthReport {
    $trusts = Get-ADTrust -Filter *
    
    foreach ($trust in $trusts) {
        $trustName = $trust.Name
        
        # Verifica secure channel
        $scVerify = nltest /sc_verify:$trustName 2>&1
        $scStatus = if ($scVerify -match "NERR_Success") { "OK" } else { "ERRORE" }
        
        # Verifica DNS
        $dnsOK = $null -ne (Resolve-DnsName "_ldap._tcp.dc._msdcs.$trustName" `
            -Type SRV -ErrorAction SilentlyContinue)
        
        # Conteggio errori di autenticazione cross-trust nelle ultime 24 ore
        $authErrors = (Get-WinEvent -LogName Security -FilterXPath `
            "*[System[EventID=4625 and TimeCreated[timediff(@SystemTime) <= 86400000]] and EventData[Data[@Name='TargetDomainName']='$($trust.FlatName)']]" `
            -ErrorAction SilentlyContinue).Count
        
        [PSCustomObject]@{
            Trust              = $trustName
            Direction          = $trust.Direction
            TrustType          = $trust.TrustType
            SecureChannel      = $scStatus
            DNS                = if ($dnsOK) { "OK" } else { "ERRORE" }
            SelectiveAuth      = $trust.SelectiveAuthentication
            SIDFiltering       = $trust.SIDFilteringQuarantined
            AuthErrors24h      = $authErrors
        }
    }
}

# Eseguire il report
Get-TrustHealthReport | Format-Table -AutoSize

# Schedulare l'esecuzione giornaliera
# (Creare un Scheduled Task che esegue lo script e invia i risultati via email)
```

### Monitoraggio Continuo con Performance Counter

```powershell
# Performance counter rilevanti per trust health
# Su ogni DC coinvolto nel trust:

# 1. Kerberos Authentication — Ticket requests cross-realm
Get-Counter "\Security System-Wide Statistics\Kerberos Authentications" -SampleInterval 60 -MaxSamples 5

# 2. NTLM Authentication — per identificare fallback
Get-Counter "\Security System-Wide Statistics\NTLM Authentications" -SampleInterval 60 -MaxSamples 5

# 3. LDAP Client Sessions — connessioni al DC
Get-Counter "\NTDS\LDAP Client Sessions" -SampleInterval 10 -MaxSamples 5

# 4. External Referrals/sec — referral Kerberos cross-realm
Get-Counter "\DirectoryServices(NTDS)\External Referrals/sec" -SampleInterval 10 -MaxSamples 5
```

---

## Troubleshooting

### Problema 1: Creazione trust fallisce con errore "The specified domain either does not exist or could not be contacted"

**Causa:** Risoluzione DNS verso il forest remoto non funzionante.

**Soluzione:**
```powershell
# 1. Verificare risoluzione DNS
nslookup fabrikam.com
Resolve-DnsName -Name "_ldap._tcp.dc._msdcs.fabrikam.com" -Type SRV

# 2. Se non risolve, creare conditional forwarder
Add-DnsServerConditionalForwarderZone -Name "fabrikam.com" `
    -MasterServers "10.20.1.10" -ReplicationScope "Forest"

# 3. Verificare connettività rete (porte 53, 88, 135, 389, 445)
Test-NetConnection -ComputerName "dc01.fabrikam.com" -Port 389

# 4. Verificare firewall tra i due forest
```

### Problema 2: Trust validation fallisce — "The trust relationship failed"

**Causa:** Password del trust scaduta o non sincronizzata tra i DC dei due forest.

**Soluzione:**
```powershell
# 1. Verificare lo stato del trust
netdom trust contoso.com /d:fabrikam.com /verify

# 2. Reset della password del trust (eseguire su entrambi i lati)
netdom trust contoso.com /d:fabrikam.com /reset /passwordt:"NewTrustP@ss!2026"

# 3. Se il reset non funziona, eliminare e ricreare il trust
# AD Domains and Trusts → Trust properties → Remove
# Poi ricreare da entrambi i lati

# 4. Verificare che i DC possano comunicare
nltest /sc_verify:fabrikam.com
```

### Problema 3: Autenticazione cross-forest lenta

**Causa:** Percorso di autenticazione troppo lungo (molti hop), GC non raggiungibile, o NTLM fallback.

**Soluzione:**
```powershell
# 1. Creare shortcut trust tra i domini specifici
# Se child1.contoso.com → contoso.com → fabrikam.com → child1.fabrikam.com è lento
netdom trust child1.contoso.com /d:child1.fabrikam.com /add /twoway /shortcut

# 2. Verificare che Kerberos funzioni (non NTLM fallback)
klist  # Verificare ticket Kerberos per la risorsa cross-forest

# 3. Verificare GC raggiungibilità dal sito dell'utente
nltest /dsgetdc:fabrikam.com /GC /site:BranchOffice

# 4. Considerare aggiunta GC nel sito locale o abilitare UGMC
```

### Problema 4: Utenti del trusted domain non riescono ad accedere alle risorse

**Causa:** Selective authentication attiva senza permesso "Allowed to Authenticate", SID filtering che rimuove SID necessari, o permessi ACL non configurati.

**Soluzione:**
```powershell
# 1. Verificare se selective authentication è attiva
netdom trust contoso.com /d:fabrikam.com /verify
# Controllare output per "Selective Authentication"

# 2. Se selective auth è attiva, verificare permesso "Allowed to Authenticate"
# Sul computer target: Properties → Security → "Allowed to Authenticate" per l'utente/gruppo

# 3. Verificare SID filtering
netdom trust contoso.com /d:fabrikam.com /FilterSids
# Se SID filtering è attivo e l'utente dipende da SID History → problema

# 4. Verificare ACL sulla risorsa
icacls "\\fileserver01\share" /t | findstr "FABRIKAM"

# 5. Controllare event log di sicurezza
Get-WinEvent -LogName Security -FilterXPath `
    "*[System[EventID=4625]]" -MaxEvents 20 | Format-List
```

### Problema 5: SID History non funziona cross-forest

**Causa:** SID filtering rimuove i SID History (comportamento di default).

**Soluzione:**
```powershell
# Opzione 1: Disabilitare temporaneamente SID filtering (durante migrazione)
netdom trust contoso.com /d:fabrikam.com /EnableSIDHistory:YES

# Opzione 2: Re-ACL le risorse con i nuovi SID
# Usare ADMT Security Translation

# Opzione 3: TLN exclusion per permettere SID specifici
# Active Directory Domains and Trusts → Trust properties → Name Suffix Routing
# Disabilitare il filtering per il name suffix specifico

# DOPO la migrazione: riabilitare SID filtering
netdom trust contoso.com /d:fabrikam.com /EnableSIDHistory:NO
```

### Problema 6: Name Suffix Routing in conflitto

**Causa:** Due forest trust dichiarano lo stesso UPN suffix o DNS name.

**Soluzione:**
```powershell
# 1. Identificare il conflitto
netdom trust contoso.com /d:fabrikam.com /NameSuffixes
netdom trust contoso.com /d:othercorp.com /NameSuffixes

# 2. Disabilitare il routing nel trust meno prioritario
netdom trust contoso.com /d:othercorp.com /ToggleSuffix:conflicting.com /disable

# 3. Oppure creare UPN suffix alternativo nel forest conflittuante
# AD Domains and Trusts → Properties → UPN Suffixes → aggiungere suffix unico
```

### Problema 7: Conditional forwarder non funziona

**Causa:** DNS server non raggiungibile, firewall blocca porta 53, o forwarder mal configurato.

**Soluzione:**
```powershell
# 1. Testare il DNS server target direttamente
nslookup fabrikam.com 10.20.1.10

# 2. Verificare che porta 53 sia aperta
Test-NetConnection -ComputerName "10.20.1.10" -Port 53

# 3. Verificare configurazione conditional forwarder
Get-DnsServerForwarder
Get-DnsServerZone | Where-Object { $_.ZoneType -eq "Forwarder" }

# 4. Ricrearlo se corrotto
Remove-DnsServerConditionalForwarderZone -Name "fabrikam.com"
Add-DnsServerConditionalForwarderZone -Name "fabrikam.com" `
    -MasterServers "10.20.1.10","10.20.1.11" -ReplicationScope "Forest"
```

### Problema 8: ADMT migrazione fallisce — "Access Denied"

**Causa:** Permessi insufficienti, trust non configurato correttamente, o auditing non abilitato.

**Soluzione:**
```powershell
# 1. Verificare account: deve essere Domain Admin in entrambi i domini
whoami /groups | findstr "Domain Admins"

# 2. Verificare trust
netdom trust contoso.com /d:fabrikam.com /verify

# 3. Verificare auditing nel source domain
auditpol /get /category:"Account Management"
# Deve essere: Success and Failure

# 4. Verificare gruppo $$$ nel source domain
Get-ADGroup -Identity "FABRIKAM$$$" -ErrorAction SilentlyContinue

# 5. Controllare ADMT log
# %systemroot%\ADMT\Logs\Migration.log
```

### Problema 9: Kerberos delegation non funziona cross-forest

**Causa:** Constrained delegation non è supportata nativamente cross-forest; unconstrained delegation è bloccata.

**Soluzione:**
```powershell
# Usare Resource-Based Constrained Delegation (RBCD)
# RBCD è l'unica forma di delegation supportata cross-forest

# Sul server target nel forest remoto:
$frontEndServer = Get-ADComputer -Identity "webapp01" -Server "contoso.com"

Set-ADComputer -Identity "sqlserver01" `
    -PrincipalsAllowedToDelegateToAccount $frontEndServer

# Verificare configurazione RBCD
Get-ADComputer -Identity "sqlserver01" `
    -Properties msDS-AllowedToActOnBehalfOfOtherIdentity | 
    Select-Object -ExpandProperty msDS-AllowedToActOnBehalfOfOtherIdentity
```

### Problema 10: Azure AD Connect non sincronizza oggetti dal secondo forest

**Causa:** Connector non configurato, credenziali errate, o filtering troppo restrittivo.

**Soluzione:**
```powershell
# 1. Verificare connettori configurati
Get-ADSyncConnector | Select-Object Name, Type, Partitions

# 2. Se manca un forest, aggiungere tramite Azure AD Connect wizard
# Start → Azure AD Connect → Configure → Customize sync options

# 3. Verificare che il connector account abbia i permessi necessari
# Account deve avere: Replicate Directory Changes, Replicate Directory Changes All

# 4. Forzare full sync
Start-ADSyncSyncCycle -PolicyType Initial

# 5. Controllare errori
Get-ADSyncRunStepResult | Where-Object { $_.StepResult -ne "success" }
```

### Problema 11: Errore LDAP referral durante query cross-forest

**Causa:** Il client segue referral LDAP a un DC del forest remoto, ma il DC non è raggiungibile.

**Soluzione:**
```powershell
# 1. Query esplicita al Global Catalog (porta 3268) anziché LDAP (389)
Get-ADUser -Filter "mail -eq 'john@fabrikam.com'" -Server "gc01.fabrikam.com:3268"

# 2. Oppure specificare la partition di ricerca
Get-ADUser -Filter * -SearchBase "DC=fabrikam,DC=com" -Server "dc01.fabrikam.com"

# 3. Verificare che i GC siano raggiungibili
Test-NetConnection -ComputerName "gc01.fabrikam.com" -Port 3268
```

### Problema 12: Trust creato ma nltest restituisce errore

**Causa:** Secure channel non stabilito, DC replication delay, o configurazione incompleta.

**Soluzione:**
```powershell
# 1. Verificare secure channel
nltest /sc_query:fabrikam.com

# 2. Se fallisce, scoprire un DC nel trusted domain
nltest /dsgetdc:fabrikam.com

# 3. Forzare la ridiscovery del DC
nltest /dsgetdc:fabrikam.com /force

# 4. Reset del secure channel
netdom trust contoso.com /d:fabrikam.com /reset

# 5. Attendere replication (o forzarla)
repadmin /syncall /APed
```

### Problema 13: Cross-forest mail flow non funziona

**Causa:** Exchange non è configurato per la risoluzione cross-forest, o il Global Address List non include utenti remoti.

**Soluzione:**
```
1. Configurare Availability Service (Free/Busy) cross-forest:
   - Organization relationship in Exchange o Exchange Online
   
2. Per GAL sync: usare Azure AD Connect o GALSync tool
   - Creare mail-enabled contacts nel forest locale per utenti remoti

3. Verificare Autodiscover cross-forest:
   - SCP record o DNS record per _autodiscover del forest remoto
```

### Problema 14: Group Policy Loopback non funziona per utenti cross-forest

**Causa:** GPO non configurata per loopback processing, o l'utente cross-forest non ha permesso di lettura sulla GPO.

**Soluzione:**
```powershell
# 1. Verificare che Loopback Processing sia abilitato (Replace mode)
gpresult /r /scope:computer | findstr "Loopback"

# 2. Verificare che "Authenticated Users" o "Domain Users" includa gli utenti cross-forest
# La GPO deve avere permesso "Read" + "Apply group policy" per il gruppo corretto

# 3. Se necessario, aggiungere il gruppo cross-forest alla delegazione della GPO
# GPMC → GPO → Delegation → Add → selezionare gruppo dal trusted forest
```

### Problema 15: Impossibile aggiungere utenti trusted forest a gruppi locali

**Causa:** Trust non validato, GC non raggiungibile per cercare l'utente, o tipi di gruppo incompatibili.

**Soluzione:**
```powershell
# 1. Verificare trust
nltest /sc_verify:fabrikam.com

# 2. Verificare che il GC del trusted forest sia raggiungibile
nltest /dsgetdc:fabrikam.com /GC

# 3. Provare ad aggiungere via SID (se la risoluzione nomi fallisce)
$sid = "S-1-5-21-FABRIKAM-1234"
Add-ADGroupMember -Identity "LocalGroup" -Members $sid

# 4. Verificare che il tipo di gruppo sia compatibile:
#    - Global groups possono contenere solo membri del proprio dominio
#    - Universal groups possono contenere membri di qualsiasi dominio nel forest
#    - Domain Local groups possono contenere membri di qualsiasi dominio fidato
```

---

## Troubleshooting Avanzato — Scenari Aggiuntivi

### Problema 16: Trust funziona in una direzione ma non nell'altra

**Causa:** Trust configurato come unidirezionale anziché bidirezionale, oppure il trust è stato creato da un solo lato.

**Soluzione:**
```powershell
# 1. Verificare la direzione del trust
Get-ADTrust -Identity "fabrikam.com" | Select-Object Name, Direction
# Direction = "BiDirectional" | "Inbound" | "Outbound"

# 2. Se il trust è unidirezionale e serve bidirezionale:
# Verificare su entrambi i lati — il trust deve essere stato creato da entrambi
# Lato contoso.com:
netdom trust contoso.com /d:fabrikam.com /verify
# Lato fabrikam.com:
# netdom trust fabrikam.com /d:contoso.com /verify

# 3. Se manca un lato, creare il trust mancante:
netdom trust contoso.com /d:fabrikam.com /add /twoway /passwordt:"P@ss!2026"
# Oppure aggiungere solo la direzione mancante dal lato incompleto
```

### Problema 17: Clock skew — Kerberos authentication fails con errore "KRB_AP_ERR_SKEW"

**Causa:** La differenza oraria tra i DC dei due forest supera i 5 minuti (tolleranza default Kerberos).

**Soluzione:**
```powershell
# 1. Verificare la differenza oraria tra i DC
w32tm /stripchart /computer:dc01.fabrikam.com /samples:5 /dataonly

# 2. Se lo skew è > 5 minuti, sincronizzare gli orari
# Ciascun forest root PDC emulator deve puntare a una source NTP affidabile

# Forest A — PDC emulator:
w32tm /config /manualpeerlist:"time.windows.com" /syncfromflags:manual /update
w32tm /resync

# Forest B — PDC emulator (deve usare la stessa source o una compatibile):
# w32tm /config /manualpeerlist:"time.windows.com" /syncfromflags:manual /update

# 3. Verificare dopo la sincronizzazione
w32tm /stripchart /computer:dc01.fabrikam.com /samples:3 /dataonly
# Lo skew deve essere < 5 minuti (idealmente < 2 secondi)
```

### Problema 18: Account bloccato dopo autenticazione cross-trust fallita

**Causa:** La lockout policy del source domain conta i tentativi falliti via trust. Se un'applicazione nel trusting forest tenta ripetutamente credenziali sbagliate, l'account nel trusted domain si blocca.

**Soluzione:**
```powershell
# 1. Identificare l'account bloccato e la sorgente del blocco
Get-ADUser -Identity "john" -Server "fabrikam.com" -Properties LockedOut, `
    lockoutTime, badPwdCount, badPasswordTime

# 2. Trovare il DC che ha registrato il lockout
Get-ADDomainController -Filter * -Server "fabrikam.com" | ForEach-Object {
    $user = Get-ADUser -Identity "john" -Server $_.HostName `
        -Properties badPwdCount, lockoutTime
    [PSCustomObject]@{
        DC           = $_.HostName
        BadPwdCount  = $user.badPwdCount
        LockoutTime  = $user.lockoutTime
    }
}

# 3. Sbloccare l'account
Unlock-ADAccount -Identity "john" -Server "fabrikam.com"

# 4. Identificare l'applicazione/server nel trusting forest che causa i lockout
# Analizzare Event ID 4740 (Account Lockout) sui DC del trusted domain
```

---

## FAQ

### 1. Qual è la differenza tra un external trust e un forest trust?

Un **external trust** è una relazione non transitiva tra due domini specifici di forest diversi. Solo gli utenti di quel dominio possono accedere alle risorse dell'altro dominio. Un **forest trust** è una relazione transitiva tra i root domain di due forest: tutti i domini di entrambi i forest possono potenzialmente accedere alle risorse dell'altro forest. Il forest trust richiede almeno forest functional level 2003.

### 2. Posso creare un trust tra un dominio AD e un dominio Azure AD?

No, non esiste un trust diretto tra AD on-premises e Entra ID (Azure AD). L'integrazione avviene tramite **Azure AD Connect** che sincronizza gli oggetti, e tramite **Seamless SSO** o **Pass-through Authentication** per l'esperienza di single sign-on. Per scenari ibridi, il dispositivo fa sia il join AD (on-premises) che la registrazione in Entra ID.

### 3. Il SID filtering può causare problemi dopo una migrazione?

Si. Se dopo una migrazione con ADMT gli utenti mantengono l'accesso alle risorse originarie tramite SID History, il SID filtering rimuoverà quei SID dal token, bloccando l'accesso. Soluzioni: (1) Disabilitare temporaneamente il SID filtering durante la fase di transizione; (2) Re-ACL tutte le risorse con i nuovi SID; (3) Usare security translation con ADMT.

### 4. Quanti forest trust posso creare?

Non c'è un limite hardcoded. Tuttavia, ogni trust aggiunge complessità, latenza (referral chain), e superficie di attacco. Best practice: minimizzare il numero di trust e consolidare dove possibile. Per organizzazioni con 5+ forest, considerare il consolidamento.

### 5. Come verifico che un trust funzioni correttamente?

```powershell
# Test completo
netdom trust contoso.com /d:fabrikam.com /verify
nltest /sc_verify:fabrikam.com
# Test autenticazione: accedere a una risorsa nel trusted forest con credenziali cross-forest
# Verificare Kerberos ticket: klist
```

### 6. Posso avere un trust tra forest con domini interni (.local)?

Si, i trust funzionano indipendentemente dal suffisso DNS. Tuttavia, domini .local non sono instradabili su internet e possono creare problemi con servizi cloud. Raccomandazione: usare suffissi DNS registrati per nuovi forest, anche se sono puramente interni.

### 7. Cosa succede se un DC del trusted forest è offline?

Se tutti i DC del trusted forest sono irraggiungibili, l'autenticazione cross-trust fallisce. Se solo alcuni sono offline, il client proverà altri DC (discovery automatica). Per scenari critici, assicurarsi di avere più DC raggiungibili dal forest trusting, idealmente in siti vicini.

### 8. Come funziona il trust con Azure AD Domain Services?

Azure AD Domain Services (gestito) può creare **forest trust unidirezionali in uscita** verso un forest on-premises. Questo permette agli utenti on-premises di accedere a risorse nel dominio gestito Azure AD DS. Non supporta trust in entrambe le direzioni.

### 9. È possibile filtrare quali utenti possono autenticarsi cross-trust?

Si, tramite **selective authentication**. Dopo averla abilitata, solo gli utenti/gruppi con il permesso "Allowed to Authenticate" sul computer target possono completare l'autenticazione. Questo è il metodo più granulare per controllare l'accesso cross-trust.

### 10. Come gestisco i trust quando un'azienda acquisita viene integrata?

Piano tipico: (1) Creare forest trust con selective authentication; (2) Concedere accesso incrementale alle risorse necessarie; (3) Pianificare la migrazione con ADMT; (4) Migrare utenti e risorse; (5) Consolidare nel forest principale; (6) Rimuovere il trust e decommissionare il forest acquisito.

### 11. Qual è l'impatto di alzare il forest functional level sui trust esistenti?

Alzare il functional level non rompe i trust esistenti. Tuttavia, se un forest è a FFL 2003 e l'altro a FFL 2016, il trust funziona ma non è possibile usare le feature che richiedono il livello più alto su entrambi i lati (es. claims-based auth richiede 2012+ su entrambi).

### 12. Come configuro un trust con un dominio in una rete completamente isolata?

Opzioni: (1) Collegare le reti via VPN site-to-site; (2) Usare VPN con routing tra le subnet dei DC; (3) Considerare Azure AD come punto di convergenza (senza trust diretto ma con sync separati). Il trust richiede connettività di rete diretta tra i DC.

### 13. Il trust è crittografato?

Kerberos cross-realm ticket sono crittografati con le inter-realm keys (AES 256 se disponibile). Il canale di autenticazione è protetto. Tuttavia, il traffico LDAP tra DC non è crittografato di default: per crittografarlo, usare LDAPS (porta 636) o LDAP channel binding + signing.

### 14. Posso usare trust per single sign-on tra forest?

Si. Con un forest trust bidirezionale e Kerberos configurato correttamente, gli utenti ottengono SSO trasparente quando accedono a risorse nell'altro forest, senza dover reinserire le credenziali. Requisito: risoluzione DNS funzionante e Kerberos (non NTLM fallback).

### 15. Come monitoro l'uso dei trust nel tempo?

```powershell
# 1. Event log Security: eventi 4768 (TGT), 4769 (TGS), 4624 (logon)
# Filtrare per autenticazioni cross-domain

# 2. Replication monitoring
repadmin /replsummary

# 3. Audit policy: loggare tutti gli accessi cross-trust
# GPO → Advanced Audit Policy → Logon/Logoff → Audit Other Logon/Logoff Events

# 4. Performance counter: "Kerberos Authentication" per DC
# Counter: KDC referral requests
```

---

## Esercizi

1. **Lab — Creare un forest trust tra due lab forest.** Configurare DNS conditional forwarder, creare forest trust bidirezionale, verificare con `nltest /sc_verify`. Testare accesso a una share dal trusted forest.

2. **Lab — Selective authentication.** Convertire il trust in selective authentication. Verificare che gli utenti non possano più accedere alle risorse. Concedere "Allowed to Authenticate" su un server specifico. Verificare che l'accesso funzioni solo su quel server.

3. **Lab — SID filtering test.** Creare un utente nel trusted forest con SID History di un admin del trusting forest. Verificare che con SID filtering attivo il SID History viene rimosso. Disabilitare il filtering e verificare la differenza.

4. **Lab — ADMT migration pilot.** Installare ADMT nel target forest. Migrare 5 utenti e 2 gruppi con SID History. Verificare accesso alle risorse originarie. Eseguire security translation.

5. **Stretch — Multi-forest Azure AD Connect.** Configurare Azure AD Connect per sincronizzare due forest in un unico tenant Entra ID. Configurare matching by UPN. Verificare che gli utenti di entrambi i forest appaiano in Entra ID.

---

## Domande a Risposta Aperta

1. **Spiega il flusso completo di autenticazione Kerberos cross-forest** quando un utente di `child.contoso.com` accede a una risorsa in `child.fabrikam.com`, indicando tutti gli hop di referral, i DC coinvolti e le chiavi crittografiche utilizzate. Come cambierebbe il flusso con un shortcut trust?

2. **Un'organizzazione ha disabilitato il SID filtering su un forest trust per facilitare una migrazione sei mesi fa.** La migrazione è stata completata, ma nessuno ha riabilitato il filtering. Descrivi i rischi di sicurezza specifici che questa configurazione introduce, i vettori di attacco possibili e il piano di remediation step-by-step.

3. **Confronta la selective authentication con il SID filtering come meccanismi di protezione cross-trust.** In quali scenari usi l'una, l'altra, o entrambe? Fornisci un esempio concreto per ciascun caso.

4. **Un'azienda con 5 forest acquisiti vuole consolidare tutto in un singolo forest.** Descrivi la strategia di migrazione completa: dalla fase di assessment alla decommissione dei forest sorgente, indicando strumenti, rischi, prerequisiti e ordine delle operazioni.

5. **Spiega l'architettura PAM trust con MIM.** Come funzionano gli shadow principal? Perché il SID filtering è disabilitato per design su un PAM trust? Quali sono i vantaggi rispetto a una configurazione ESAE tradizionale senza PAM?

---

## Vero o Falso

1. **Un forest trust è transitivo: se Forest A ha un forest trust con Forest B, e Forest B ha un forest trust con Forest C, allora gli utenti di Forest A possono accedere direttamente a risorse in Forest C.**

   > **FALSO.** La transitività del forest trust si applica *all'interno* dei domini di ciascun forest. I forest trust non sono transitivi *tra* forest trust diversi. Forest A non ha alcuna relazione con Forest C a meno che non venga creato un trust separato tra A e C. (Rif.: Microsoft Learn — "How Domain and Forest Trusts Work", consultato: 2026-05-23)

2. **Il SID filtering è disabilitato di default sui forest trust e deve essere abilitato manualmente.**

   > **FALSO.** Il SID filtering (quarantine) è **attivo di default** su external trust e forest trust. Deve essere *disabilitato* manualmente (e temporaneamente) durante le migrazioni con ADMT quando si necessita del SID History. (Rif.: Microsoft Learn — "Security Considerations for Trusts", consultato: 2026-05-23)

3. **Un parent-child trust può essere rimosso manualmente dall'amministratore senza rimuovere il child domain dal forest.**

   > **FALSO.** Il parent-child trust è intrinseco alla struttura del forest e non può essere eliminato manualmente. Per rimuoverlo, occorre depromovere tutti i DC del child domain, rimuovendo così il dominio dal forest.

4. **La Kerberos Constrained Delegation (KCD) tradizionale funziona cross-forest tra domini di due forest diversi.**

   > **FALSO.** La KCD tradizionale (non resource-based) **non funziona cross-forest**. Solo la **Resource-Based Constrained Delegation (RBCD)** è supportata per scenari cross-forest. La Unconstrained Delegation è esplicitamente bloccata cross-forest per motivi di sicurezza.

5. **Con Azure AD Connect, è possibile sincronizzare più forest Active Directory on-premises in un singolo tenant Entra ID senza che i forest abbiano trust tra loro.**

   > **VERO.** Azure AD Connect può connettersi a più forest indipendenti e sincronizzarli in un unico tenant Entra ID. Non è necessario un trust tra i forest — è sufficiente che il server Azure AD Connect abbia connettività di rete verso i DC di ciascun forest e un account con i permessi adeguati. In alternativa, Azure AD Cloud Sync offre lo stesso risultato con agent leggeri per-forest.

---

## Esercizi Scenario-Based

### Scenario 1 — Acquisizione con Accesso Immediato

La tua azienda (contoso.com, FFL 2016, 3 child domain) ha acquisito fabrikam.com (FFL 2012 R2, singolo dominio). Il management richiede che entro 48 ore gli ingegneri di fabrikam.com possano accedere al file server `\\eng.contoso.com\projects` in sola lettura, senza concedere accesso a nessun'altra risorsa.

**Domanda:** Descrivi la configurazione completa step-by-step: tipo di trust, authentication mode, DNS, firewall, permessi, e il test di validazione. Motiva ogni scelta di sicurezza.

### Scenario 2 — Migrazione con Downtime Zero per gli Utenti

L'organizzazione ha completato la migrazione ADMT di 500 utenti da fabrikam.com a contoso.com. Gli utenti migrati usano ancora i file server nel vecchio forest tramite SID History. Il CISO chiede di riabilitare il SID filtering, ma il team infrastruttura dice che 200 share server non sono ancora stati re-ACL.

**Domanda:** Proponi un piano che bilanci sicurezza e continuità operativa. Come procedi con la security translation senza interrompere l'accesso? Quali metriche usi per decidere quando riabilitare il SID filtering?

### Scenario 3 — Incident Response: SID History Injection Sospetta

Il SOC rileva un Event ID 4675 ripetuto su un DC del forest contoso.com. L'analisi preliminare mostra che un account del trusted forest fabrikam.com ha SID History contenenti il SID di Enterprise Admins di contoso.com. Il SID filtering ha bloccato l'accesso, ma l'attacco è in corso.

**Domanda:** Descrivi il playbook di incident response: containment immediato, investigazione nel trusted forest, remediation, e misure preventive per evitare il ripetersi dell'incidente. Includi i comandi specifici per ogni fase.

### Scenario 4 — Multi-Forest con Requisiti di Compliance

Un'azienda in ambito finanziario ha 3 forest: `prod.bank.com` (dati clienti, PCI-DSS), `dev.bank.com` (sviluppo), `partner.bank.com` (vendor esterni). Devi progettare l'architettura trust che permetta: (a) agli sviluppatori di accedere a una copia sanitizzata dei dati in prod, (b) ai vendor di accedere solo a un portale web in prod, (c) nessun accesso di prod verso gli altri forest.

**Domanda:** Disegna l'architettura trust completa con direzione, tipo, authentication mode, e giustifica ogni scelta rispetto ai requisiti PCI-DSS. Quali trust NON creeresti e perché?

### Scenario 5 — PAM Trust per Privileged Access

L'organizzazione vuole implementare il modello PAM con bastion forest per eliminare le credenziali admin persistenti nel forest di produzione. Attualmente, 15 Domain Admin hanno credenziali permanenti in `contoso.com`.

**Domanda:** Progetta l'architettura completa: creazione del bastion forest, configurazione del PAM trust, installazione MIM, definizione delle policy di accesso Just-In-Time, e il piano di migrazione degli admin dal modello corrente al modello PAM. Quali sono le limitazioni e i rischi residui?

---

## Letture

- Microsoft Learn — Understanding Trust Types — https://learn.microsoft.com/en-us/entra/identity/domain-services/concepts-forest-trust (consultato: 2026-05-23)
- Microsoft Learn — Forest Trust Step-by-Step — https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/forest-recovery-guide/ (consultato: 2026-05-23)
- ADMT Guide — https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/deploy/admt-guide (consultato: 2026-05-23)
- Azure AD Connect Multi-Forest — https://learn.microsoft.com/en-us/entra/identity/hybrid/connect/plan-connect-topologies (consultato: 2026-05-23)
- Microsoft Learn — How Domain and Forest Trusts Work — https://learn.microsoft.com/en-us/entra/identity/domain-services/concepts-forest-trust (consultato: 2026-05-23)
- Microsoft Learn — SID Filtering and Quarantine — https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/component-updates/sid-filtering-quarantine (consultato: 2026-05-23)
- Microsoft Learn — Kerberos Authentication Overview — https://learn.microsoft.com/en-us/windows-server/security/kerberos/kerberos-authentication-overview (consultato: 2026-05-23)
- Microsoft Learn — Active Directory Firewall Ports — https://learn.microsoft.com/en-us/troubleshoot/windows-server/active-directory/config-firewall-for-ad-domains-and-trusts (consultato: 2026-05-23)
- Microsoft Learn — Privileged Access Management for AD DS — https://learn.microsoft.com/en-us/microsoft-identity-manager/pam/privileged-identity-management-for-active-directory-domain-services (consultato: 2026-05-23)
- Microsoft Learn — Selective Authentication — https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/forest-recovery-guide/ (consultato: 2026-05-23)
- Microsoft Learn — Azure AD Connect Cloud Sync — https://learn.microsoft.com/en-us/entra/identity/hybrid/cloud-sync/what-is-cloud-sync (consultato: 2026-05-23)
- Microsoft Learn — Name Suffix Routing — https://learn.microsoft.com/en-us/windows-server/identity/ad-ds/manage/component-updates/name-suffix-routing (consultato: 2026-05-23)

---

## Collegamenti Incrociati

| Modulo | Titolo | Relazione |
|---|---|---|
| `01-active-directory.md` | Active Directory — Fondamenti | Prerequisito: concetti base di domini, forest, DC, gruppi, GPO. Questo modulo estende i concetti trust introdotti nel modulo 01 con un approfondimento su scenari multi-forest, migrazione e sicurezza cross-trust. |
| `25-active-directory-design-avanzato.md` | Active Directory Design Avanzato | Complementare: progettazione di topologie multi-dominio e multi-forest, siti e repliche, FSMO, schema. Il modulo 25 tratta il design dell'infrastruttura AD; il modulo 33 si concentra sull'interconnessione tra forest e le relative implicazioni operative e di sicurezza. |
| `34-disaster-recovery-ad-pki.md` | Disaster Recovery AD e PKI | Complementare: il modulo 34 copre il backup/restore dei DC e della PKI. In scenari multi-forest, il disaster recovery deve considerare i trust, le inter-realm key, e la sincronizzazione con forest remoti. Un restore del forest root domain impatta tutti i trust in uscita. |

---

## Glossario

| Termine | Definizione |
|---|---|
| **Forest trust** | Trust transitivo bidirezionale tra due forest AD (richiede FFL 2003+). |
| **External trust** | Trust non transitivo tra due domini specifici di forest diversi. |
| **Shortcut trust** | Trust che riduce gli hop di autenticazione tra domini distanti nello stesso forest. |
| **Realm trust** | Trust tra AD e un realm Kerberos non-Windows (MIT). |
| **Selective authentication** | Modalità trust che richiede permesso esplicito "Allowed to Authenticate" per ogni risorsa. |
| **SID filtering** | Rimozione dal token di autenticazione dei SID non appartenenti al dominio trusted. |
| **SID History** | Attributo che preserva il SID originale di un oggetto migrato. |
| **SID History injection** | Attacco in cui un admin del trusted forest inietta SID privilegiati del trusting forest nella SID History di un utente. |
| **Name Suffix Routing** | Controllo di quali UPN/DNS suffix sono routati attraverso un forest trust. |
| **TLN (Top-Level Name)** | Nome DNS di primo livello routato via name suffix routing. |
| **TLN Exclusion** | Blocco selettivo del routing di un sottodominio specifico all'interno di un TLN routato. |
| **Inter-realm key** | Chiave simmetrica condivisa tra i DC di due domini trust per i referral ticket. |
| **Referral ticket** | Ticket Kerberos che reindirizza il client al KDC del dominio/forest corretto. |
| **Referral chain** | Percorso completo dei referral Kerberos attraverso trust multipli. |
| **Trusting domain** | Il dominio che concede accesso alle proprie risorse. |
| **Trusted domain** | Il dominio i cui utenti accedono alle risorse del trusting domain. |
| **GC (Global Catalog)** | Replica parziale di tutti gli oggetti del forest, usata per query cross-domain. |
| **UGMC** | Universal Group Membership Caching — cache locale della membership dei gruppi universali. |
| **FSP** | Foreign Security Principal — oggetto placeholder per SID di domini trusted. |
| **ADMT** | Active Directory Migration Tool — strumento per migrazione oggetti tra domini/forest. |
| **PES** | Password Export Server — componente ADMT installato su DC source per migrazione password. |
| **A-G-DL-P** | Account-Global-Domain Local-Permissions — strategia di nesting gruppi best practice. |
| **FFL** | Forest Functional Level — livello di funzionalità del forest AD. |
| **DFL** | Domain Functional Level — livello di funzionalità del dominio AD. |
| **RBCD** | Resource-Based Constrained Delegation — delegation cross-forest supportata. |
| **ESAE** | Enhanced Security Admin Environment — architettura per isolamento admin (Red Forest). |
| **PAM trust** | Trust speciale per Privileged Access Management con MIM, unidirezionale dal production al bastion forest. |
| **Shadow principal** | Oggetto nel bastion forest che proietta l'appartenenza a gruppi privilegiati del production forest. |
| **MIM** | Microsoft Identity Manager — piattaforma di identity governance usata per PAM. |
| **Time-Based Group Membership** | Appartenenza a un gruppo con scadenza temporale (TTL), disponibile con FFL 2016+ e PAM. |
| **JIT (Just-In-Time)** | Modello di accesso privilegiato in cui le credenziali admin sono assegnate temporaneamente su richiesta. |
| **Cloud Sync** | Azure AD Cloud Sync — agent leggero per sync multi-forest senza trust richiesto. |
| **TDO** | Trusted Domain Object — oggetto AD in CN=System che rappresenta il trust. |
| **Quarantine** | SID filtering specifico per forest trust, filtra SID in base al dominio di appartenenza. |
| **Domain consolidation** | Processo di unificazione di più domini in un singolo dominio all'interno di un forest. |
| **Intra-forest migration** | Migrazione di oggetti tra domini nello stesso forest (usa Move-ADObject). |
| **Inter-forest migration** | Migrazione di oggetti tra forest diversi (richiede ADMT). |
