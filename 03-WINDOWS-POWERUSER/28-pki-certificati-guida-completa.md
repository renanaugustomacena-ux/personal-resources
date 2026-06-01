# PKI e Certificati Digitali — Guida Approfondita

> **Modulo 28** · **Aggiornamento:** 2026-05-23

> **Modulo del corso:** Windows Poweruser
> **Posizione nel percorso:** [Syllabus](00-SYLLABUS.md) · Fase 5 — Servizi Avanzati
> **Prerequisiti:** [01 — Active Directory](01-active-directory.md), [02 — PowerShell](02-powershell.md), [05 — Sicurezza Windows](05-sicurezza-windows.md), [11 — Servizi Certificati](11-servizi-certificati.md), [29 — Windows Server Hardening](29-windows-server-hardening.md)
> **Obiettivi di apprendimento:**
> 1. Progettare una gerarchia CA a due o tre livelli con Root CA offline e Issuing CA enterprise
> 2. Configurare certificate templates personalizzati con autoenrollment, key archival e security permissions
> 3. Implementare e gestire CRL Distribution Points, AIA e OCSP Responder per la validazione dei certificati
> 4. Identificare e mitigare le vulnerabilità AD CS (ESC1-ESC8) utilizzando strumenti come Certipy e Certify
> 5. Automatizzare la gestione del ciclo di vita dei certificati tramite PowerShell e certutil
> 6. Pianificare e eseguire backup, migrazione e disaster recovery della CA
> 7. Integrare Let's Encrypt / ACME per scenari hybrid-PKI con certificati pubblici
> 8. Monitorare la salute della PKI con script diagnostici e audit degli eventi
> **Tempo stimato:** lettura 120 min · lab 180 min
> **Livello:** proficient
> **Versioni di riferimento:** Windows Server 2022/2025, PowerShell 5.1/7.x, Certipy 4.x, certutil 10.x


## Mappa concettuale

```
                    ┌──────────────────────────────────────────────────────────────┐
                    │                   PKI ENTERPRISE — ARCHITETTURA              │
                    └──────────────────────────┬───────────────────────────────────┘
                                               │
              ┌────────────────────────────────┼────────────────────────────────┐
              │                                │                                │
    ┌─────────▼──────────┐         ┌───────────▼──────────┐        ┌───────────▼──────────┐
    │    ROOT CA          │         │   POLICY CA           │        │   REGISTRATION       │
    │  (offline, vault)   │         │  (opzionale,          │        │   AUTHORITY (RA)      │
    │  RSA 4096 / ECC     │         │   three-tier)         │        │                      │
    │  Validità: 20 anni  │         │                      │        │  NDES / CEP / CES    │
    └─────────┬──────────┘         └───────────┬──────────┘        └──────────────────────┘
              │ firma                          │ firma
              ▼                                ▼
    ┌────────────────────────────────────────────────────┐
    │              ISSUING CA (Enterprise, Online)        │
    │  Integrata con AD · Auto-enrollment via GPO         │
    │  RSA 4096 · Validità: 10 anni                       │
    │  Emette certificati per utenti, computer, servizi   │
    └──────┬───────────┬──────────┬──────────┬───────────┘
           │           │          │          │
           ▼           ▼          ▼          ▼
    ┌──────────┐ ┌──────────┐ ┌────────┐ ┌───────────┐
    │ User     │ │ Computer │ │ Server │ │ Code      │
    │ Cert     │ │ Cert     │ │ TLS    │ │ Signing   │
    │ (S/MIME, │ │ (802.1X, │ │ (IIS,  │ │ (Scripts, │
    │  Smart   │ │  IPsec)  │ │  ADFS) │ │  Driver)  │
    │  Card)   │ │          │ │        │ │           │
    └──────────┘ └──────────┘ └────────┘ └───────────┘

    ┌──────────────────────── VALIDAZIONE ────────────────────────┐
    │                                                              │
    │  Client ──► CDP (LDAP/HTTP) ──► Base CRL + Delta CRL        │
    │  Client ──► AIA (HTTP)     ──► OCSP Responder (real-time)   │
    │  Client ──► AIA (HTTP)     ──► Certificato CA (chain build) │
    │                                                              │
    └──────────────────────────────────────────────────────────────┘

    ┌──────────────────── ENROLLMENT PATHS ───────────────────────┐
    │                                                              │
    │  1. Auto-enrollment (GPO) ──► Enterprise CA                  │
    │  2. Manual (certsrv web / certreq / MMC)                     │
    │  3. NDES (SCEP) ──► Network devices, MDM/Intune              │
    │  4. CEP/CES (HTTPS) ──► Non-domain-joined, DMZ              │
    │  5. CMC/CMP ──► Interop con CA non-Microsoft                 │
    │  6. ACME (Let's Encrypt) ──► Certificati pubblici            │
    │                                                              │
    └──────────────────────────────────────────────────────────────┘
```


## Idee guida
1. **Cert renewal timing: 60-90 giorni prima scadenza.**
2. **Duplicate SAN issue: avoid; use single cert.**
3. **CRL DP failover.** OCSP stapling per perf.
4. **Two-tier offline root + online issuing.**


## Indice
- [Panoramica](#panoramica)
- [Concetti Fondamentali della Crittografia a Chiave Pubblica](#concetti-fondamentali-della-crittografia-a-chiave-pubblica)
- [Struttura del Certificato X.509](#struttura-del-certificato-x509)
- [Architettura della PKI](#architettura-della-pki)
- [Confronto Gerarchie CA: One-Tier, Two-Tier, Three-Tier](#confronto-gerarchie-ca-one-tier-two-tier-three-tier)
- [Cross-Certification e Bridge CA](#cross-certification-e-bridge-ca)
- [Installazione di AD Certificate Services](#installazione-di-ad-certificate-services)
- [Certificate Templates](#certificate-templates)
- [Auto-Enrollment tramite GPO](#auto-enrollment-tramite-gpo)
- [Web Enrollment e NDES](#web-enrollment-e-ndes)
- [CEP e CES — Certificate Enrollment Policy e Service](#cep-e-ces--certificate-enrollment-policy-e-service)
- [OCSP Responder](#ocsp-responder)
- [Gestione CRL](#gestione-crl)
- [CRL Distribution Points e AIA — Progettazione](#crl-distribution-points-e-aia--progettazione)
- [Ciclo di Vita dei Certificati](#ciclo-di-vita-dei-certificati)
- [Gestione con PowerShell](#gestione-con-powershell)
- [Interoperabilità OpenSSL e PKCS#12](#interoperabilità-openssl-e-pkcs12)
- [Certificati TLS/SSL — Gestione Avanzata](#certificati-tlsssl--gestione-avanzata)
- [Scenari Avanzati di Certificati](#scenari-avanzati-di-certificati)
- [AD CS Abuse e Hardening — ESC1-ESC8](#ad-cs-abuse-e-hardening--esc1-esc8)
- [Let's Encrypt e ACME su Windows](#lets-encrypt-e-acme-su-windows)
- [Migrazione della CA tra Server](#migrazione-della-ca-tra-server)
- [Monitoring e Compliance PKI](#monitoring-e-compliance-pki)
- [Securing the CA — Hardening e Key Ceremony](#securing-the-ca--hardening-e-key-ceremony)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Esercizi](#esercizi)
- [Auto-valutazione](#auto-valutazione)
- [Letture](#letture)
- [Collegamenti incrociati](#collegamenti-incrociati)
- [Glossario locale](#glossario-locale)
- [Riferimenti](#riferimenti)

---

## Panoramica

La Public Key Infrastructure (PKI) è il framework tecnologico che gestisce la creazione, distribuzione, utilizzo, archiviazione e revoca dei certificati digitali. In un'infrastruttura Microsoft enterprise, la PKI è implementata tramite Active Directory Certificate Services (AD CS), che fornisce una Certification Authority (CA) integrata con Active Directory per l'emissione automatizzata di certificati per utenti, computer, servizi e dispositivi.

Una PKI ben progettata è il fondamento di numerose tecnologie di sicurezza: SSL/TLS per la cifratura delle comunicazioni web, S/MIME per la firma e cifratura delle email, IPsec per la protezione del traffico di rete, 802.1X per l'autenticazione di rete, smart card per l'autenticazione forte, BitLocker per la cifratura dei dischi con TPM e Network Unlock, e code signing per la firma del software.

Questa guida copre i principi teorici della crittografia a chiave pubblica, la progettazione di una gerarchia CA enterprise, la configurazione dei certificate templates, l'auto-enrollment, i meccanismi di validazione (CRL e OCSP) e la gestione completa del ciclo di vita dei certificati tramite PowerShell, fornendo le competenze necessarie per implementare e gestire una PKI enterprise robusta e conforme alle best practices.

---

## Concetti Fondamentali della Crittografia a Chiave Pubblica

### Coppia di Chiavi: Pubblica e Privata

La crittografia asimmetrica si basa su una coppia di chiavi matematicamente correlate:

- **Chiave Pubblica**: distribuita liberamente, utilizzata per cifrare i dati e verificare le firme digitali
- **Chiave Privata**: mantenuta segreta dal proprietario, utilizzata per decifrare i dati e creare le firme digitali

```
Cifratura:
Mittente (Alice) ──[chiave pubblica di Bob]──> Messaggio Cifrato ──> Bob ──[chiave privata di Bob]──> Messaggio in Chiaro

Firma Digitale:
Alice ──[chiave privata di Alice]──> Firma ──> Bob ──[chiave pubblica di Alice]──> Verifica OK
```

### Algoritmi Crittografici e Lunghezza delle Chiavi

La scelta dell'algoritmo crittografico e della lunghezza della chiave determina il livello di sicurezza e le performance della PKI. Le raccomandazioni attuali (NIST SP 800-57 Part 1, Rev. 5) sono:

| Algoritmo | Lunghezza chiave | Sicurezza equivalente (bit) | Uso raccomandato | Scadenza NIST |
|-----------|-----------------|---------------------------|------------------|---------------|
| RSA | 2048 | 112 | End-entity certificates | Accettabile fino al 2030 |
| RSA | 3072 | 128 | CA intermedia | Raccomandato post-2030 |
| RSA | 4096 | ~140 | Root CA | Lungo termine |
| ECDSA P-256 | 256 | 128 | End-entity, performance | Raccomandato |
| ECDSA P-384 | 384 | 192 | Root CA, CA intermedia | Suite B, NATO |
| ECDSA P-521 | 521 | 256 | Massima sicurezza | Raramente necessario |
| Ed25519 | 256 | 128 | Firma (non in AD CS) | Supporto limitato |

> **Errore comune:** Molti ambienti enterprise usano ancora RSA 1024-bit per certificati end-entity. Questa lunghezza è considerata deprecata dal 2013 (NIST) e vulnerabile a fattorizzazione con hardware moderno. La migrazione a RSA 2048+ o ECC è obbligatoria.

### Hash Algorithm e Sicurezza

| Algoritmo | Dimensione output | Stato | Note |
|-----------|------------------|-------|------|
| MD5 | 128 bit | **Deprecato** | Collisioni dimostrate (2004), non usare mai |
| SHA-1 | 160 bit | **Deprecato** | Collisioni pratiche (SHAttered, 2017), rifiutato dai browser dal 2017 |
| SHA-256 | 256 bit | **Raccomandato** | Standard corrente per certificati |
| SHA-384 | 384 bit | Raccomandato | Suite B, ambienti ad alta sicurezza |
| SHA-512 | 512 bit | Valido | Overhead maggiore, raramente necessario |

### Certificate Signing Request (CSR)

Il CSR è una richiesta formale di emissione di un certificato, inviata dal richiedente alla CA. Contiene:

1. **Subject**: identità del richiedente (Common Name, Organization, ecc.)
2. **Public Key**: la chiave pubblica del richiedente
3. **Signature**: il CSR è firmato con la chiave privata del richiedente, provando il possesso

```powershell
# Generare un CSR manualmente con certreq
$inf = @"
[NewRequest]
Subject = "CN=webserver.contoso.com,O=Contoso,L=Roma,S=Lazio,C=IT"
KeyLength = 2048
KeySpec = 1
KeyUsage = 0xa0
MachineKeySet = TRUE
ProviderName = "Microsoft RSA SChannel Cryptographic Provider"
RequestType = PKCS10
HashAlgorithm = SHA256

[EnhancedKeyUsageExtension]
OID=1.3.6.1.5.5.7.3.1 ; Server Authentication

[Extensions]
2.5.29.17 = "{text}"
_continue_ = "dns=webserver.contoso.com&"
_continue_ = "dns=www.contoso.com&"
_continue_ = "dns=contoso.com"
"@
$inf | Out-File "C:\Certs\webserver.inf" -Encoding ASCII
certreq -new "C:\Certs\webserver.inf" "C:\Certs\webserver.csr"
```

### Catena di Certificati (Certificate Chain)

La fiducia in un certificato si basa su una catena di fiducia:

```
┌─────────────────────────────┐
│  Root CA Certificate         │  ← Self-signed, fiducia esplicita
│  (Validity: 20 years)        │     (nel Trust Store del client)
│  CN=Contoso Root CA          │
└──────────────┬──────────────┘
               │ firma
               v
┌─────────────────────────────┐
│  Subordinate/Issuing CA      │  ← Firmato dalla Root CA
│  Certificate                 │     (fiducia transitiva)
│  (Validity: 10 years)        │
│  CN=Contoso Enterprise CA    │
└──────────────┬──────────────┘
               │ firma
               v
┌─────────────────────────────┐
│  End-Entity Certificate      │  ← Firmato dalla Issuing CA
│  (Validity: 1-2 years)       │     (certificato dell'utente/server)
│  CN=webserver.contoso.com    │
└─────────────────────────────┘
```

---

## Struttura del Certificato X.509

Un certificato X.509v3 (RFC 5280) è una struttura ASN.1 firmata dalla CA. Comprendere i campi è essenziale per il troubleshooting e la configurazione dei template.

### Campi Obbligatori (TBS Certificate)

| Campo | OID / Posizione | Descrizione | Esempio |
|-------|----------------|-------------|---------|
| **Version** | — | Versione del formato (v1=0, v2=1, v3=2) | v3 (2) |
| **Serial Number** | — | Identificativo unico assegnato dalla CA | `4a:3b:2c:1d:...` |
| **Signature Algorithm** | — | Algoritmo usato dalla CA per firmare | `sha256WithRSAEncryption` |
| **Issuer** | — | Distinguished Name della CA emittente | `CN=Contoso Enterprise CA, O=Contoso, C=IT` |
| **Validity** | — | Periodo di validità (NotBefore, NotAfter) | `2026-05-23T00:00:00Z` / `2027-05-23T23:59:59Z` |
| **Subject** | — | Distinguished Name del titolare | `CN=webserver.contoso.com` |
| **Subject Public Key Info** | — | Algoritmo + chiave pubblica | RSA 2048-bit |

### Estensioni X.509v3 Principali

| Estensione | OID | Critica? | Descrizione |
|------------|-----|----------|-------------|
| **Key Usage** | 2.5.29.15 | Sì | Scopo della chiave: digitalSignature, keyEncipherment, keyCertSign, crlSign |
| **Extended Key Usage (EKU)** | 2.5.29.37 | No | Scopo applicativo: Server Auth (1.3.6.1.5.5.7.3.1), Client Auth (.2), Code Signing (.3), Email Protection (.4) |
| **Subject Alternative Name (SAN)** | 2.5.29.17 | Sì (se Subject vuoto) | Nomi alternativi: DNS, IP, email, URI |
| **Authority Key Identifier (AKI)** | 2.5.29.35 | No | Identificativo della chiave della CA emittente |
| **Subject Key Identifier (SKI)** | 2.5.29.14 | No | Hash della chiave pubblica del soggetto |
| **CRL Distribution Points (CDP)** | 2.5.29.31 | No | URL dove scaricare la CRL |
| **Authority Information Access (AIA)** | 1.3.6.1.5.5.7.1.1 | No | URL per OCSP e certificato CA |
| **Basic Constraints** | 2.5.29.19 | Sì | Indica se è un certificato CA (cA=TRUE) + pathLenConstraint |
| **Certificate Policies** | 2.5.29.32 | No | OID delle policy di emissione |
| **Name Constraints** | 2.5.29.30 | Sì | Limita i namespace per cui la CA può emettere |
| **Certificate Template Name** | 1.3.6.1.4.1.311.21.7 | No | Nome del template AD CS (estensione Microsoft) |

```powershell
# Visualizzare la struttura completa di un certificato X.509
$cert = Get-ChildItem Cert:\LocalMachine\My | Select-Object -First 1

# Campi principali
Write-Output "=== CERTIFICATE FIELDS ==="
Write-Output "Version:    $($cert.Version)"
Write-Output "Serial:     $($cert.SerialNumber)"
Write-Output "Subject:    $($cert.Subject)"
Write-Output "Issuer:     $($cert.Issuer)"
Write-Output "NotBefore:  $($cert.NotBefore)"
Write-Output "NotAfter:   $($cert.NotAfter)"
Write-Output "Thumbprint: $($cert.Thumbprint)"
Write-Output "Algo:       $($cert.SignatureAlgorithm.FriendlyName)"
Write-Output "Key Size:   $($cert.PublicKey.Key.KeySize)"

# Estensioni
Write-Output "`n=== EXTENSIONS ==="
$cert.Extensions | ForEach-Object {
    [PSCustomObject]@{
        OID       = $_.Oid.Value
        Name      = $_.Oid.FriendlyName
        Critical  = $_.Critical
        Value     = $_.Format(1)
    }
} | Format-Table -Wrap

# Decodifica con certutil (output più dettagliato)
certutil -dump "C:\Certs\server.cer"
```

> **Approfondimento:** Il campo Name Constraints (OID 2.5.29.30) è una delle estensioni più potenti ma meno utilizzate. Permette a una Root CA di limitare i domini per cui le Subordinate CA possono emettere certificati, ad esempio `permittedSubtrees: .contoso.com, .fabrikam.com`. Questa restrizione previene l'emissione non autorizzata di certificati per domini esterni, riducendo drasticamente l'impatto di un compromesso della CA subordinata.

---

## Architettura della PKI

### Gerarchia a Due Livelli (Raccomandato)

La best practice per ambienti enterprise è una gerarchia a due livelli:

**Root CA (offline):** La CA radice firma solo il certificato della Subordinate CA. Viene mantenuta offline (spenta, o su una macchina air-gapped) per proteggere la chiave privata. Un compromesso della Root CA invalida l'intera PKI.

**Subordinate/Issuing CA (online):** La CA che emette effettivamente i certificati per utenti, computer e servizi. È integrata con Active Directory per l'auto-enrollment. Può essere ridondante (2 Issuing CA per alta disponibilità).

```
┌──────────────────────────────┐
│        Root CA (Standalone)    │
│     ┌──────────────────┐      │
│     │ OFFLINE / Vault   │      │  ← Accesa solo per rinnovare
│     │ Standalone CA     │      │     i certificati delle Sub CA
│     │ (no dominio)      │      │     o pubblicare CRL
│     └──────────────────┘      │
└────────────┬─────────────────┘
             │ firma certificato
             v
┌──────────────────────────────┐
│     Issuing CA (Enterprise)    │
│  ┌──────────────────────────┐ │
│  │ Online, integrata con AD │ │  ← Emette certificati per
│  │ Enterprise CA             │ │     utenti, computer, servizi
│  │ Auto-enrollment via GPO   │ │
│  └──────────────────────────┘ │
└──────────────────────────────┘
```

---

## Confronto Gerarchie CA: One-Tier, Two-Tier, Three-Tier

La scelta della topologia CA è una decisione architetturale con impatto a lungo termine sulla sicurezza, la gestibilità e la scalabilità della PKI.

### One-Tier (Singola CA)

```
┌─────────────────────────────┐
│   Root + Issuing CA          │   ← Self-signed, sempre online
│   (Enterprise, domain-joined)│      Emette certificati direttamente
│   Unico punto di fiducia    │
└─────────────────────────────┘
```

| Aspetto | Dettaglio |
|---------|-----------|
| **Uso** | Lab, test, PMI < 50 utenti, PoC |
| **Pro** | Semplicissima da installare, costo zero |
| **Contro** | La chiave Root è online e vulnerabile, nessuna separazione dei ruoli, compromesso = rebuild completo |
| **Validità tipica** | 5 anni (Root + emissione) |

> **Caso reale:** Una PMI italiana con ~30 dipendenti ha implementato una CA one-tier per l'autenticazione 802.1X. Dopo 3 anni, il server CA ha subito un attacco ransomware. La chiave Root è stata compromessa, invalidando l'intera PKI e richiedendo la sostituzione di tutti i certificati su ogni dispositivo: 2 settimane di downtime parziale.

### Two-Tier (Raccomandato)

```
┌─────────────────────────────┐
│   Root CA (Standalone)       │   ← Offline, air-gapped, vault
│   RSA 4096 / ECC P-384      │
│   Validità: 20 anni         │
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│   Issuing CA (Enterprise)    │   ← Online, AD-integrated
│   RSA 4096, Validità: 10y   │      Auto-enrollment, templates
└─────────────────────────────┘
```

| Aspetto | Dettaglio |
|---------|-----------|
| **Uso** | Produzione enterprise (95% degli scenari) |
| **Pro** | Root protetta offline, Issuing CA sostituibile senza invalidare la trust chain, separazione dei ruoli |
| **Contro** | Complessità moderata, la Root CA deve essere accesa periodicamente per CRL e rinnovi Sub CA |
| **Validità tipica** | Root 20y, Issuing 10y, End-entity 1-2y |

### Three-Tier (Alta sicurezza)

```
┌─────────────────────────────┐
│   Root CA (Standalone)       │   ← Offline, HSM, vault
│   ECC P-384                  │
│   Validità: 25 anni         │
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│   Policy CA (Standalone)     │   ← Online o semi-offline
│   Applica policy di emissione│      Definisce le issuance policies
│   Validità: 15 anni         │      per ogni branch
└──────────────┬──────────────┘
               │
┌──────────────▼──────────────┐
│   Issuing CA (Enterprise)    │   ← Online, AD-integrated
│   Validità: 5-10 anni       │      Emette end-entity certificates
└─────────────────────────────┘
```

| Aspetto | Dettaglio |
|---------|-----------|
| **Uso** | Governo, militare, finanza regolamentata, PKI multi-organizzazione |
| **Pro** | Policy CA permette policy diverse per divisione/partner, massima granularità, conforme a Common Criteria |
| **Contro** | Complessità elevata, più certificati CA da gestire, overkill per il 95% degli ambienti |
| **Validità tipica** | Root 25y, Policy 15y, Issuing 5-10y, End-entity 1y |

### Matrice Decisionale

| Criterio | One-Tier | Two-Tier | Three-Tier |
|----------|----------|----------|------------|
| Sicurezza Root | Bassa | Alta | Massima |
| Complessità | Minima | Moderata | Elevata |
| Costo | Zero | Basso | Significativo (HSM) |
| Scalabilità | Nessuna | Buona | Eccellente |
| Conformità | Nessuna | CIS, NIST | Common Criteria, NATO |
| Recovery | Rebuild totale | Rebuild Issuing CA | Rebuild singolo livello |
| Raccomandato per | Lab/PoC | Enterprise | Governo/Difesa |

---

## Cross-Certification e Bridge CA

### Cross-Certification

La cross-certification permette a due organizzazioni con PKI indipendenti di stabilire una fiducia reciproca senza condividere una Root CA comune. Ogni organizzazione emette un certificato di cross-certification per la CA dell'altra.

```
┌───────────────────────┐                ┌───────────────────────┐
│  Contoso Root CA       │                │  Fabrikam Root CA      │
│                       │                │                       │
│  Emette cross-cert    │───────────────>│                       │
│  per Fabrikam Root    │<───────────────│  Emette cross-cert    │
│                       │                │  per Contoso Root     │
└───────────┬───────────┘                └───────────┬───────────┘
            │                                        │
            ▼                                        ▼
    Contoso Issuing CA                       Fabrikam Issuing CA
            │                                        │
            ▼                                        ▼
    Utenti Contoso possono                   Utenti Fabrikam possono
    fidarsi dei cert Fabrikam                fidarsi dei cert Contoso
```

```powershell
# Creare un certificato di cross-certification
# 1. Fabrikam invia il certificato della sua Root CA a Contoso
# 2. Sulla Root CA di Contoso, creare un cross-certificate:
certreq -policy "FabrikamRootCA.cer" "FabrikamCrossCert.cer"

# 3. Pubblicare il cross-certificate in AD di Contoso
certutil -dspublish -f "FabrikamCrossCert.cer" CrossCA

# 4. Verificare la cross-certification
certutil -verify -urlfetch "FabrikamUserCert.cer"
```

### Bridge CA

Una Bridge CA è un modello più complesso usato principalmente in ambito governativo (es. Federal Bridge CA negli USA). Invece di creare cross-certification N-to-N tra ogni coppia di organizzazioni, tutte le organizzazioni si cross-certificano con una singola Bridge CA centrale.

```
                    ┌───────────────────┐
                    │   BRIDGE CA        │
                    │   (Peer-to-Peer)   │
                    └───┬───┬───┬───┬───┘
                        │   │   │   │
              cross-cert│   │   │   │cross-cert
                        │   │   │   │
    ┌───────────────┐   │   │   │   │   ┌───────────────┐
    │ Org A Root CA  │◄──┘   │   │   └──►│ Org D Root CA  │
    └───────────────┘       │   │       └───────────────┘
                            │   │
    ┌───────────────┐       │   │       ┌───────────────┐
    │ Org B Root CA  │◄──────┘   └──────►│ Org C Root CA  │
    └───────────────┘                   └───────────────┘
```

> **Approfondimento:** Il modello Bridge CA risolve il problema di scalabilità della cross-certification: con N organizzazioni, la cross-certification diretta richiede N*(N-1)/2 relazioni. Con una Bridge CA, servono solo N relazioni. La Federal Bridge CA (FBCA) gestita da GSA collega oltre 40 agenzie federali statunitensi con una singola infrastruttura di fiducia.

---

## Installazione di AD Certificate Services

### Root CA (Standalone, Offline)

```powershell
# SULLA MACCHINA ROOT CA (non unita al dominio)

# Installare il ruolo CA
Install-WindowsFeature -Name ADCS-Cert-Authority -IncludeManagementTools

# Configurare come Root CA Standalone
Install-AdcsCertificationAuthority -CAType StandaloneRootCA `
    -CryptoProviderName "RSA#Microsoft Software Key Storage Provider" `
    -KeyLength 4096 `
    -HashAlgorithmName SHA256 `
    -ValidityPeriod Years `
    -ValidityPeriodUnits 20 `
    -CACommonName "Contoso Root CA" `
    -CADistinguishedNameSuffix "O=Contoso,L=Roma,C=IT" `
    -Force

# Configurare la CRL (Certificate Revocation List)
# La Root CA deve pubblicare la CRL periodicamente
certutil -setreg CA\CRLPeriodUnits 1
certutil -setreg CA\CRLPeriod "Years"
certutil -setreg CA\CRLOverlapPeriodUnits 3
certutil -setreg CA\CRLOverlapPeriod "Months"

# Pubblicare la CRL
certutil -CRL

# Esportare il certificato Root e la CRL per distribuzione
certutil -ca.cert "C:\RootCA\ContosoRootCA.cer"
certutil -CRL
Copy-Item "C:\Windows\System32\CertSrv\CertEnroll\*.crl" "C:\RootCA\"

# Copiare il certificato Root e la CRL su un media rimovibile
# per trasferirli alla Issuing CA e pubblicarli in AD
```

### Issuing CA (Enterprise, Online)

```powershell
# SULLA MACCHINA ISSUING CA (unita al dominio)

# Prima: pubblicare il certificato Root CA in Active Directory
certutil -dspublish -f "C:\Temp\ContosoRootCA.cer" RootCA
certutil -addstore -f Root "C:\Temp\ContosoRootCA.cer"
certutil -addstore -f Root "C:\Temp\ContosoRootCA.crl"

# Installare il ruolo CA
Install-WindowsFeature -Name ADCS-Cert-Authority, ADCS-Web-Enrollment -IncludeManagementTools

# Configurare come Enterprise Subordinate CA
Install-AdcsCertificationAuthority -CAType EnterpriseSubordinateCA `
    -CryptoProviderName "RSA#Microsoft Software Key Storage Provider" `
    -KeyLength 2048 `
    -HashAlgorithmName SHA256 `
    -CACommonName "Contoso Enterprise CA" `
    -CADistinguishedNameSuffix "O=Contoso,L=Roma,C=IT" `
    -Force

# Il processo genererà un CSR (.req) che deve essere firmato dalla Root CA
# 1. Copiare il .req sulla Root CA
# 2. Sulla Root CA: certreq -submit "C:\Temp\IssuingCA.req"
# 3. Emettere il certificato: certsrv.msc → Pending Requests → Issue
# 4. Esportare il certificato firmato
# 5. Copiare il certificato firmato sulla Issuing CA
# 6. Installare: certutil -installcert "C:\Temp\IssuingCA.cer"

# Configurare CRL Distribution Points
certutil -setreg CA\CRLPeriodUnits 7
certutil -setreg CA\CRLPeriod "Days"
certutil -setreg CA\CRLDeltaPeriodUnits 1
certutil -setreg CA\CRLDeltaPeriod "Days"

# Configurare AIA (Authority Information Access)
# HTTP location per la CRL e il certificato CA (per client non-AD)
certutil -setreg CA\CACertPublicationURLs "1:C:\Windows\system32\CertSrv\CertEnroll\%3%8.crt\n2:ldap:///CN=%7,CN=AIA,CN=Public Key Services,CN=Services,%6%11\n2:http://pki.contoso.com/CertEnroll/%3%8.crt"

certutil -setreg CA\CRLPublicationURLs "65:C:\Windows\system32\CertSrv\CertEnroll\%3%8%9.crl\n79:ldap:///CN=%7%8,CN=%2,CN=CDP,CN=Public Key Services,CN=Services,%6%10\n6:http://pki.contoso.com/CertEnroll/%3%8%9.crl"

# Riavviare il servizio CA
Restart-Service certsvc

# Installare Web Enrollment
Install-AdcsWebEnrollment -Force
```

### Ruoli di Servizio AD CS

AD CS è composto da diversi role services, ciascuno con una funzione specifica:

| Role Service | Descrizione | Quando installarlo |
|--------------|-------------|-------------------|
| **Certification Authority** | Servizio principale che emette e gestisce i certificati | Sempre (obbligatorio) |
| **CA Web Enrollment** | Pagina web (certsrv) per la richiesta di certificati via browser | Client non-domain, richieste manuali |
| **Online Responder (OCSP)** | Fornisce risposte OCSP per la verifica di revoca in tempo reale | Ambienti con molti client, VPN, 802.1X |
| **NDES** | Implementa SCEP per dispositivi di rete e MDM | Switch, router, Intune/MDM |
| **CEP** | Certificate Enrollment Policy via HTTPS | Client non-domain, DMZ, Workplace Join |
| **CES** | Certificate Enrollment Service via HTTPS | Complementare a CEP |

```powershell
# Installare tutti i role services in una volta
Install-WindowsFeature -Name ADCS-Cert-Authority, `
    ADCS-Web-Enrollment, `
    ADCS-Online-Cert, `
    ADCS-Device-Enrollment, `
    ADCS-Enroll-Web-Pol, `
    ADCS-Enroll-Web-Svc `
    -IncludeManagementTools
```

---

## Certificate Templates

I certificate templates definiscono le proprietà dei certificati emessi: scopo (EKU), durata, lunghezza della chiave, permessi di enrollment e comportamento di auto-enrollment.

### Versioni dei Template

| Versione | Disponibile da | Caratteristiche |
|----------|---------------|-----------------|
| V1 | Windows 2000 | Template predefiniti, non modificabili |
| V2 | Windows 2003 | Duplicabili e personalizzabili, autoenrollment |
| V3 | Windows 2008 | Supporto CNG, SHA-256+, Suite B |
| V4 | Windows 2012 | Supporto key attestation, rinnovamento con nuova chiave |

### Creare un Template Personalizzato

```
Procedura GUI (certsrv.msc → Certificate Templates → Manage):
1. Trovare il template da cui duplicare (es. "Web Server")
2. Tasto destro → Duplicate Template
3. Configurare:

Tab Compatibility:
  - Certification Authority: Windows Server 2016
  - Certificate recipient: Windows 10 / Windows Server 2016

Tab General:
  - Template display name: "Contoso Web Server"
  - Validity period: 1 year
  - Renewal period: 6 weeks
  - Publish certificate in Active Directory: Yes

Tab Request Handling:
  - Purpose: Signature and encryption
  - Allow private key to be exported: No (sicurezza)

Tab Cryptography:
  - Provider Category: Key Storage Provider
  - Algorithm name: RSA
  - Minimum key size: 2048
  - Hash: SHA256

Tab Subject Name:
  - Supply in the request (per i server, l'admin specifica il CN)
  -- oppure --
  - Build from AD information (per utenti, auto-popola dal profilo AD)

Tab Extensions:
  - Application Policies (EKU):
    - Server Authentication (1.3.6.1.5.5.7.3.1)
    - Client Authentication (1.3.6.1.5.5.7.3.2) [opzionale]
  - Key Usage:
    - Digital Signature
    - Key Encipherment

Tab Security:
  - Authenticated Users: Read, Enroll
  - Domain Computers: Read, Enroll, Autoenroll (se auto-enrollment)
  - CA Admins: Full Control

Tab Issuance Requirements:
  - CA certificate manager approval: No (per auto-enrollment)
  - Number of authorized signatures: 0
```

```powershell
# Pubblicare un template sulla CA (renderlo disponibile per l'enrollment)
Add-CATemplate -Name "ContosoWebServer" -Force

# Verificare i template pubblicati
Get-CATemplate | Select-Object Name

# Elencare tutti i template disponibili in AD
Get-ADObject -SearchBase "CN=Certificate Templates,CN=Public Key Services,CN=Services,$((Get-ADRootDSE).configurationNamingContext)" `
    -Filter * -Properties displayName, msPKI-Cert-Template-OID |
    Select-Object Name, displayName
```

### Template: Supersede e Issuance Policies

Il meccanismo di **supersede** permette a un nuovo template di sostituire uno o più template obsoleti. Quando un template v2 viene configurato per fare il supersede di un template v1, i certificati esistenti emessi dal vecchio template vengono automaticamente rinnovati con il nuovo template al prossimo ciclo di auto-enrollment.

```
Tab Superseded Templates (nel nuovo template):
  - Aggiungere il/i template da sostituire
  - I certificati esistenti verranno rinnovati con il nuovo template
  - Il vecchio template può essere rimosso dalla CA dopo il rollover

Tab Issuance Requirements — Issuance Policies:
  - Le issuance policies (OID) definiscono sotto quali condizioni la CA emette il certificato
  - Usate per differenziare livelli di assurance (Low / Medium / High)
  - Mappabili a Certificate Policies nell'estensione 2.5.29.32
  - Esempio: una policy "High Assurance" richiede smart card + approvazione manuale
```

```powershell
# Elencare tutti i template con le relative issuance policies
$templateDN = "CN=Certificate Templates,CN=Public Key Services,CN=Services,$((Get-ADRootDSE).configurationNamingContext)"
Get-ADObject -SearchBase $templateDN -Filter * `
    -Properties displayName, 'msPKI-Certificate-Policy', 'msPKI-RA-Application-Policies', 'msPKI-Supersede-Templates' |
    Where-Object { $_.displayName } |
    Select-Object Name, displayName,
        @{N='IssuancePolicies';E={$_.'msPKI-Certificate-Policy' -join ', '}},
        @{N='SupersededTemplates';E={$_.'msPKI-Supersede-Templates' -join ', '}} |
    Format-Table -Wrap
```

---

## Auto-Enrollment tramite GPO

L'auto-enrollment permette ai computer e agli utenti di richiedere automaticamente certificati senza intervento manuale. È il metodo più efficiente per distribuire certificati su larga scala.

### Configurazione

```
Passo 1: Configurare i permessi sul template
- Template Security → Aggiungere il gruppo target con permessi:
  Read, Enroll, Autoenroll

Passo 2: Configurare la GPO
Computer Configuration → Policies → Windows Settings → Security Settings
  → Public Key Policies → Certificate Services Client - Auto-Enrollment:
    - Configuration Model: Enabled
    - Renew expired certificates: Checked
    - Update certificates that use certificate templates: Checked

User Configuration → Policies → Windows Settings → Security Settings
  → Public Key Policies → Certificate Services Client - Auto-Enrollment:
    (stesse impostazioni per certificati utente)
```

```powershell
# Verificare i certificati auto-enrolled su un computer
Get-ChildItem Cert:\LocalMachine\My | Select-Object Subject, Issuer,
    NotBefore, NotAfter, HasPrivateKey,
    @{N='Template';E={($_.Extensions | Where-Object Oid.Value -eq "1.3.6.1.4.1.311.21.7").Format(0)}}

# Forzare un ciclo di auto-enrollment
certutil -pulse

# Equivalente PowerShell
Start-Process "certutil" -ArgumentList "-pulse" -NoNewWindow -Wait
```

### Come Funziona l'Auto-Enrollment Internamente

```
Ciclo di auto-enrollment (eseguito ogni ~8 ore o al login):

1. Il client contatta il DC e legge le policy di auto-enrollment dalla GPO
2. Il client enumera le CA enterprise disponibili in AD
   (CN=Enrollment Services,CN=Public Key Services,CN=Services,...)
3. Per ogni CA, il client legge i template pubblicati
4. Per ogni template, il client verifica:
   a. Ha i permessi Read + Enroll + Autoenroll?
   b. Ha già un certificato valido per questo template?
   c. Il certificato esistente è in fase di rinnovo (renewal period)?
5. Se i criteri sono soddisfatti, il client genera una coppia di chiavi,
   crea un CSR e lo invia alla CA tramite DCOM/RPC
6. La CA valida la richiesta, verifica i permessi e emette il certificato
7. Il client installa il certificato nel cert store appropriato
```

### Auto-Enrollment: Troubleshooting Avanzato

| Evento | Event ID | Significato |
|--------|----------|-------------|
| Enrollment riuscito | 64 (AutoEnrollment) | Certificato emesso e installato con successo |
| Enrollment fallito | 13 (AutoEnrollment) | Errore durante il processo — verificare il messaggio |
| Template non trovato | 15 (AutoEnrollment) | Il template non è pubblicato sulla CA o il client non ha permessi |
| CA non raggiungibile | 6 (AutoEnrollment) | Problemi di rete, firewall o servizio CA fermo |
| Rinnovo schedulato | 16 (AutoEnrollment) | Il certificato è nel periodo di rinnovo, rinnovo avviato |

```powershell
# Event log dedicato per l'auto-enrollment
Get-WinEvent -LogName "Microsoft-Windows-CertificateServicesClient-AutoEnrollment/Operational" -MaxEvents 20 |
    Select-Object TimeCreated, Id, LevelDisplayName, Message | Format-Table -Wrap

# Abilitare il verbose logging per il debug
# HKLM\SOFTWARE\Microsoft\Cryptography\AutoEnrollment
# AEEventLogLevel = 0 (verbose)
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Cryptography\AutoEnrollment" `
    -Name "AEEventLogLevel" -Value 0 -Type DWord
```

---

## Web Enrollment e NDES

### Web Enrollment

Il Web Enrollment (certsrv web page) permette di richiedere certificati tramite browser, utile per dispositivi non uniti al dominio o per utenti che necessitano di tipi specifici di certificati.

URL: `https://ca-server.contoso.com/certsrv`

### NDES (Network Device Enrollment Service)

NDES implementa il protocollo SCEP (Simple Certificate Enrollment Protocol) per permettere ai dispositivi di rete (router, switch, access point) e ai dispositivi mobili gestiti da MDM di richiedere certificati automaticamente.

```powershell
# Installare NDES
Install-WindowsFeature -Name ADCS-Device-Enrollment -IncludeManagementTools

# Configurare NDES
Install-AdcsNetworkDeviceEnrollmentService -ServiceAccountName "CONTOSO\svc-ndes" `
    -ServiceAccountPassword (ConvertTo-SecureString "P@ssw0rd" -AsPlainText -Force) `
    -RAName "Contoso NDES RA" `
    -RACountry "IT" `
    -SigningProviderName "Microsoft Strong Cryptographic Provider" `
    -SigningKeyLength 2048 `
    -EncryptionProviderName "Microsoft Strong Cryptographic Provider" `
    -EncryptionKeyLength 2048 `
    -Force
```

### Integrazione con Intune

Intune può utilizzare NDES+SCEP per distribuire certificati ai dispositivi gestiti:

```
Flusso Intune → NDES → CA:
1. Intune invia il profilo SCEP al dispositivo
2. Il dispositivo genera una coppia di chiavi e un CSR
3. Il dispositivo invia il CSR a NDES via HTTPS
4. NDES inoltra la richiesta alla CA
5. La CA emette il certificato
6. NDES restituisce il certificato al dispositivo
7. Il dispositivo installa il certificato
```

---

## CEP e CES — Certificate Enrollment Policy e Service

Il Certificate Enrollment Policy (CEP) e il Certificate Enrollment Service (CES) permettono l'enrollment di certificati tramite HTTPS per dispositivi non uniti al dominio, in DMZ o connessi tramite VPN. A differenza di NDES/SCEP (progettato per dispositivi di rete), CEP/CES sono progettati per workstation e server Windows che non hanno accesso diretto ad Active Directory.

### Architettura CEP/CES

```
┌──────────────────────┐     HTTPS      ┌──────────────────────┐     DCOM/RPC     ┌─────────────┐
│  Client Windows       │──────────────►│  CEP + CES Server    │───────────────►│  Issuing CA  │
│  (non domain-joined)  │               │  (DMZ o perimetro)   │                │  (Enterprise) │
│                       │◄──────────────│                      │◄───────────────│              │
│  Riceve policy +      │  cert emesso  │  Proxy enrollment    │  cert emesso   │              │
│  template disponibili │               │  requests            │                │              │
└──────────────────────┘               └──────────────────────┘                └─────────────┘
```

### Modalità di Autenticazione CEP/CES

| Modalità | Descrizione | Caso d'uso |
|----------|-------------|------------|
| **Username/Password** | Autenticazione con credenziali AD | Client non-domain con accesso alla rete |
| **Client Certificate** | Autenticazione con certificato esistente (renewal) | Rinnovo automatico di certificati esistenti |
| **Key-Based Renewal** | Rinnovo basato sulla chiave del certificato corrente | Rinnovo senza credenziali utente |

```powershell
# Installare CEP e CES
Install-WindowsFeature -Name ADCS-Enroll-Web-Pol, ADCS-Enroll-Web-Svc -IncludeManagementTools

# Configurare CEP (Certificate Enrollment Policy)
Install-AdcsEnrollmentPolicyWebService -AuthenticationType UserName `
    -SSLCertThumbprint (Get-ChildItem Cert:\LocalMachine\My |
        Where-Object Subject -like "*cep.contoso.com*").Thumbprint `
    -Force

# Configurare CES (Certificate Enrollment Service)
Install-AdcsEnrollmentWebService -AuthenticationType UserName `
    -SSLCertThumbprint (Get-ChildItem Cert:\LocalMachine\My |
        Where-Object Subject -like "*ces.contoso.com*").Thumbprint `
    -CAConfig "CA01.contoso.com\Contoso Enterprise CA" `
    -Force

# Sul client: configurare la policy URL
# Tramite GPO o manualmente:
# certutil -enrollmentServerURL -setup https://cep.contoso.com/ADPolicyProvider_CEP_UsernamePassword/service.svc/CEP

# Richiedere un certificato via CEP/CES
certreq -enroll -username "contoso\user" -machine "ContosoWebServer"
```

---

## OCSP Responder

L'OCSP (Online Certificate Status Protocol) fornisce un'alternativa più efficiente alle CRL per la verifica dello stato di revoca dei certificati. Invece di scaricare l'intera lista di revoca, il client invia una query per un singolo certificato e riceve una risposta immediata.

```powershell
# Installare l'OCSP Responder
Install-WindowsFeature -Name ADCS-Online-Cert -IncludeManagementTools

# Configurare l'OCSP Responder
Install-AdcsOnlineResponder -Force

# Configurare la Revocation Configuration
# (tramite GUI: Online Responder Management Console → Revocation Configuration → Add)
# 1. Specificare il certificato della CA che serve l'OCSP
# 2. Configurare la signing certificate dell'OCSP
# 3. Configurare i CRL distribution points

# Aggiungere l'URL OCSP all'AIA dei certificati emessi dalla CA
certutil -setreg CA\CACertPublicationURLs "1:C:\Windows\system32\CertSrv\CertEnroll\%3%8.crt\n2:ldap:///CN=%7,CN=AIA,CN=Public Key Services,CN=Services,%6%11\n32:http://ocsp.contoso.com/ocsp"

# Verificare lo stato OCSP di un certificato
certutil -verify -urlfetch "C:\Certs\server.cer"
```

### OCSP Stapling

L'OCSP Stapling è un'ottimizzazione in cui il web server stesso interroga periodicamente il responder OCSP e include (staples) la risposta firmata nel TLS handshake. Questo elimina la necessità per il client di contattare direttamente il responder OCSP, migliorando privacy e performance.

```powershell
# OCSP Stapling in IIS (Windows Server 2012+)
# È abilitato per default su IIS 8.0+ — non richiede configurazione manuale
# Verificare lo stato:
netsh http show sslcert

# Se necessario, configurare manualmente:
# 1. Verificare che l'AIA del certificato contenga un URL OCSP valido
certutil -dump "C:\Certs\server.cer" | Select-String "OCSP"

# 2. Verificare che il server possa raggiungere il responder OCSP
$ocspUrl = "http://ocsp.contoso.com/ocsp"
Invoke-WebRequest -Uri $ocspUrl -Method HEAD

# 3. In Nginx su Windows (se usato):
# ssl_stapling on;
# ssl_stapling_verify on;
# resolver 8.8.8.8;
```

> **Caso reale:** Un'organizzazione con 5000 client che verificano certificati TLS simultaneamente generava ~150 richieste/secondo al responder OCSP, causando latenza e occasionali timeout. L'abilitazione di OCSP Stapling su tutti i web server ha ridotto il traffico verso il responder OCSP del 98%, eliminando completamente i timeout.

### OCSP vs CRL — Quando Usare Quale

| Criterio | CRL | OCSP |
|----------|-----|------|
| **Latenza** | Dipende dalla dimensione della CRL (può essere multi-MB) | Risposta immediata (~100ms) |
| **Aggiornamento** | Periodico (base CRL ogni 7 giorni, delta CRL ogni giorno) | Real-time (basato sull'ultima CRL caricata) |
| **Carico rete** | Alto per CRL grandi, basso per delta CRL | Basso per query, ma alto per OCSP server |
| **Offline support** | Client può usare CRL cachata | Richiede connettività all'OCSP server |
| **Privacy** | Nessun leak: client scarica la lista completa | OCSP server vede quale certificato il client sta verificando |
| **Raccomandato per** | Ambienti con molte revoche, client offline | VPN, 802.1X, smart card, web server (stapling) |
| **Standard** | RFC 5280 (X.509 CRL) | RFC 6960 (OCSP) |

---

## Gestione CRL

La CRL (Certificate Revocation List) è la lista dei certificati revocati dalla CA. I client scaricano periodicamente la CRL per verificare che i certificati presentati non siano stati revocati.

### Tipi di CRL

**Base CRL:** Lista completa di tutti i certificati revocati. Può diventare molto grande in ambienti con molte revoche.

**Delta CRL:** Lista incrementale che contiene solo le revoche avvenute dall'ultima pubblicazione della Base CRL. Riduce il traffico di rete e il tempo di download.

```powershell
# Verificare la configurazione CRL della CA
certutil -getreg CA\CRLPeriodUnits
certutil -getreg CA\CRLPeriod
certutil -getreg CA\CRLDeltaPeriodUnits
certutil -getreg CA\CRLDeltaPeriod

# Pubblicare manualmente una nuova CRL
certutil -CRL

# Verificare la CRL corrente
certutil -URL "http://pki.contoso.com/CertEnroll/ContosoCA.crl"

# Verificare la validità di un certificato (include check CRL e OCSP)
certutil -verify -urlfetch "C:\Certs\server.cer"

# Revocare un certificato
$cert = Get-ChildItem Cert:\LocalMachine\My | Where-Object Subject -like "*webserver*"
certutil -revoke $cert.SerialNumber 1  # 1 = Key Compromise

# Codici di revoca:
# 0 = Unspecified
# 1 = Key Compromise
# 2 = CA Compromise
# 3 = Affiliation Changed
# 4 = Superseded
# 5 = Cessation of Operation
# 6 = Certificate Hold (temporaneo, revocabile)
```

---

## CRL Distribution Points e AIA — Progettazione

La progettazione dei CDP (CRL Distribution Points) e dell'AIA (Authority Information Access) è uno degli aspetti più critici e spesso sottovalutati della PKI. Un CDP irraggiungibile causa il fallimento della validazione dei certificati in tutto l'ambiente.

### Tipi di CDP e Priorità

| Protocollo | Pro | Contro | Priorità |
|------------|-----|--------|----------|
| **LDAP** | Sempre disponibile per client domain-joined, nessun server aggiuntivo | Non funziona per client non-domain o esterni, richiede AD access | 1 (primario per client interni) |
| **HTTP** | Funziona per tutti i client (interni ed esterni), cachable, load-balanceable | Richiede un web server dedicato, deve essere raggiungibile | 2 (primario per client esterni) |
| **File** | Semplice per pubblicazione locale | Non distribuibile, solo per la CA stessa | Solo per pubblicazione locale |
| **FTP** | Compatibilità legacy | Insicuro (cleartext), deprecato | Non raccomandato |

### Regole di Progettazione CDP/AIA

1. **Almeno due CDP**: uno LDAP (per client AD) e uno HTTP (per client esterni)
2. **CRL Overlap Period**: la nuova CRL deve essere pubblicata prima che la vecchia scada. Formula: `CRL Validity = CRL Period + CRL Overlap Period`
3. **HTTP CDP raggiungibile dall'esterno**: se i certificati vengono usati da client esterni (VPN, web server), l'URL HTTP deve essere raggiungibile da Internet
4. **Naming convention stabile**: non usare hostname del server CA nel CDP URL — usare un alias DNS (es. `pki.contoso.com`) che può essere reindirizzato in caso di migrazione
5. **Ordine dei CDP**: LDAP prima di HTTP nei certificati per client interni, HTTP prima di LDAP per certificati usati esternamente

### Calcolo CRL Overlap

```
Scenario: CRL Period = 7 giorni, CRL Overlap = 3 giorni

Giorno 0: CRL v1 pubblicata (valida fino al giorno 7+3=10)
Giorno 7: CRL v2 pubblicata (valida fino al giorno 14+3=17)
Giorno 10: CRL v1 scade, ma CRL v2 è già disponibile da 3 giorni
           I client hanno avuto 3 giorni per scaricare la nuova CRL

Se la CA è offline o irraggiungibile il giorno 7:
  - I client hanno comunque 3 giorni di overlap (fino al giorno 10)
  - ALERT: entro 3 giorni la CA deve pubblicare una nuova CRL
```

```powershell
# Configurazione completa CDP e AIA per una Issuing CA
# NOTA: i numeri nel certutil -setreg hanno significati specifici:
# 1 = Pubblicazione locale (file system)
# 2 = Includi nell'estensione CDP/AIA del certificato
# 4 = Includi nelle CRL per trovare la delta CRL
# 8 = Includi nell'estensione AIA del certificato
# 64 = Pubblica CRL in questa posizione
# 128 = Pubblica delta CRL in questa posizione

# CRL Distribution Points
$cdpConfig = @(
    "65:C:\Windows\system32\CertSrv\CertEnroll\%3%8%9.crl"           # File locale (pubblica)
    "79:ldap:///CN=%7%8,CN=%2,CN=CDP,CN=Public Key Services,CN=Services,%6%10"  # LDAP (pubblica + includi)
    "6:http://pki.contoso.com/CertEnroll/%3%8%9.crl"                 # HTTP (includi nel cert)
)
certutil -setreg CA\CRLPublicationURLs ($cdpConfig -join "\n")

# Authority Information Access
$aiaConfig = @(
    "1:C:\Windows\system32\CertSrv\CertEnroll\%3%8.crt"             # File locale
    "2:ldap:///CN=%7,CN=AIA,CN=Public Key Services,CN=Services,%6%11"  # LDAP (includi)
    "2:http://pki.contoso.com/CertEnroll/%3%8.crt"                   # HTTP (includi)
    "32:http://ocsp.contoso.com/ocsp"                                # OCSP (includi)
)
certutil -setreg CA\CACertPublicationURLs ($aiaConfig -join "\n")

# Riavviare il servizio CA per applicare le modifiche
Restart-Service certsvc

# Pubblicare una nuova CRL con le nuove configurazioni
certutil -CRL

# Verificare che i CDP siano raggiungibili
certutil -URL "http://pki.contoso.com/CertEnroll/ContosoEnterpriseCA.crl"
certutil -URL "ldap:///CN=Contoso Enterprise CA,CN=CA01,CN=CDP,CN=Public Key Services,CN=Services,CN=Configuration,DC=contoso,DC=com"
```

---

## Ciclo di Vita dei Certificati

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Richiesta│───>│ Emissione│───>│  Utilizzo│───>│ Rinnovo/ │
│  (CSR)   │    │(CA firma)│    │  (valido)│    │ Revoca   │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     │                │               │               │
     │                │               │               │
     v                v               v               v
 - Generazione    - Validazione   - Autenticazione - Auto-renewal
   coppia chiavi    richiesta     - Cifratura      - Revoca manuale
 - Creazione CSR  - Firma CA      - Firma digitale - Scadenza
 - Invio a CA     - Distribuzione - Verifica chain - Archiviazione
```

### Rinnovo: Chiave Esistente vs Nuova Chiave

Il rinnovo del certificato può avvenire in due modi:

| Modalità | Descrizione | Quando usarla |
|----------|-------------|---------------|
| **Rekey (nuova chiave)** | Genera una nuova coppia di chiavi e un nuovo certificato | Raccomandato: rotazione periodica delle chiavi, dopo sospetto compromesso |
| **Renew (stessa chiave)** | Mantiene la stessa chiave privata, emette un nuovo certificato | Accettabile per il rinnovo di routine se la chiave non è compromessa |

```powershell
# Rinnovo con nuova chiave (raccomandato)
certreq -enroll -machine -q "ContosoWebServer"

# Rinnovo con la stessa chiave
certreq -enroll -machine -q -cert THUMBPRINT "ContosoWebServer"
```

### Tempistiche di Rinnovo Raccomandate

| Tipo di certificato | Validità | Inizio rinnovo | Urgenza |
|---------------------|----------|----------------|---------|
| Root CA | 20 anni | 2 anni prima | Bassa, ma critica |
| Issuing CA | 10 anni | 1 anno prima | Media |
| Web server TLS | 1 anno | 60 giorni prima | Alta |
| User S/MIME | 1 anno | 30 giorni prima | Media |
| Smart card | 1-2 anni | 60 giorni prima | Alta |
| Code signing | 1-3 anni | 90 giorni prima | Alta |
| 802.1X computer | 1 anno | Auto-enrollment | Automatico |

```powershell
# Monitorare i certificati in scadenza
$daysThreshold = 30
Get-ChildItem Cert:\LocalMachine\My | Where-Object {
    $_.NotAfter -lt (Get-Date).AddDays($daysThreshold) -and
    $_.NotAfter -gt (Get-Date)
} | Select-Object Subject, Issuer, NotAfter,
    @{N='DaysLeft';E={($_.NotAfter - (Get-Date)).Days}},
    Thumbprint | Sort-Object NotAfter

# Script di monitoring per tutti i server
$servers = Get-ADComputer -Filter 'OperatingSystem -like "*Server*"' | Select-Object -ExpandProperty Name

$expiringCerts = $servers | ForEach-Object {
    $server = $_
    try {
        Invoke-Command -ComputerName $server -ScriptBlock {
            Get-ChildItem Cert:\LocalMachine\My | Where-Object {
                $_.NotAfter -lt (Get-Date).AddDays(30) -and $_.NotAfter -gt (Get-Date)
            } | Select-Object Subject, NotAfter, Thumbprint
        } -ErrorAction Stop | ForEach-Object {
            [PSCustomObject]@{
                Server     = $server
                Subject    = $_.Subject
                ExpiryDate = $_.NotAfter
                DaysLeft   = ($_.NotAfter - (Get-Date)).Days
                Thumbprint = $_.Thumbprint
            }
        }
    } catch {
        Write-Warning "Impossibile contattare $server"
    }
}

$expiringCerts | Sort-Object DaysLeft | Format-Table -AutoSize
```

---

## Gestione con PowerShell

```powershell
# Elencare i certificati nello store locale
Get-ChildItem Cert:\LocalMachine\My | Format-Table Subject, Issuer, NotAfter, Thumbprint
Get-ChildItem Cert:\CurrentUser\My | Format-Table Subject, Issuer, NotAfter, Thumbprint

# Ottenere i dettagli di un certificato specifico
$cert = Get-ChildItem Cert:\LocalMachine\My\THUMBPRINT
$cert | Format-List *
$cert.Extensions | ForEach-Object {
    [PSCustomObject]@{
        Oid       = $_.Oid.FriendlyName
        Critical  = $_.Critical
        Value     = $_.Format(1)
    }
}

# Esportare un certificato (senza chiave privata)
Export-Certificate -Cert $cert -FilePath "C:\Certs\export.cer" -Type CERT

# Esportare con chiave privata (PFX)
$password = ConvertTo-SecureString "ExportP@ss!" -AsPlainText -Force
Export-PfxCertificate -Cert $cert -FilePath "C:\Certs\export.pfx" -Password $password

# Importare un certificato
Import-Certificate -FilePath "C:\Certs\rootca.cer" -CertStoreLocation Cert:\LocalMachine\Root

# Importare un PFX
Import-PfxCertificate -FilePath "C:\Certs\server.pfx" -CertStoreLocation Cert:\LocalMachine\My `
    -Password (ConvertTo-SecureString "P@ssw0rd" -AsPlainText -Force)

# Creare un certificato self-signed (per test/sviluppo)
$selfSigned = New-SelfSignedCertificate -DnsName "test.contoso.com" `
    -CertStoreLocation Cert:\LocalMachine\My `
    -NotAfter (Get-Date).AddYears(2) `
    -KeyAlgorithm RSA -KeyLength 2048 `
    -HashAlgorithm SHA256 `
    -KeyExportPolicy Exportable

# Richiedere un certificato da una CA enterprise
$template = "ContosoWebServer"
$enrollment = New-Object -ComObject X509Enrollment.CX509Enrollment
$request = New-Object -ComObject X509Enrollment.CX509CertificateRequestPkcs10
$request.InitializeFromTemplateName(0x1, $template)  # 0x1 = Machine context
$enrollment.InitializeFromRequest($request)
$enrollment.Enroll()

# Oppure con certreq
certreq -enroll -machine "ContosoWebServer"

# Verificare un certificato remoto (es. HTTPS)
$uri = "https://www.contoso.com"
$request = [System.Net.HttpWebRequest]::Create($uri)
$request.Timeout = 10000
try { $request.GetResponse() | Out-Null } catch {}
$cert = $request.ServicePoint.Certificate
[PSCustomObject]@{
    Subject   = $cert.Subject
    Issuer    = $cert.Issuer
    ValidFrom = $cert.GetEffectiveDateString()
    ValidTo   = $cert.GetExpirationDateString()
    Serial    = $cert.GetSerialNumberString()
}
```

### Modulo PKI di PowerShell (PSPKI)

Il modulo PSPKI (PowerShell PKI Module) estende significativamente le capacità native di PowerShell per la gestione di AD CS.

```powershell
# Installare il modulo PSPKI
Install-Module -Name PSPKI -Scope CurrentUser

# Ottenere informazioni sulla CA
Import-Module PSPKI
Get-CertificationAuthority | Format-List *

# Elencare i certificati emessi dalla CA
Get-IssuedRequest -CertificationAuthority "CA01.contoso.com\Contoso Enterprise CA" `
    -Property CommonName, NotAfter, CertificateTemplate |
    Sort-Object NotAfter |
    Format-Table

# Elencare i certificati in scadenza nei prossimi 30 giorni
Get-IssuedRequest -CertificationAuthority "CA01.contoso.com\Contoso Enterprise CA" `
    -Filter "NotAfter -le $(Get-Date).AddDays(30)" `
    -Property CommonName, NotAfter, CertificateTemplate |
    Format-Table

# Revocare un certificato tramite PSPKI
Get-IssuedRequest -CertificationAuthority "CA01.contoso.com\Contoso Enterprise CA" `
    -Filter "CommonName -eq 'webserver.contoso.com'" |
    Revoke-Certificate -Reason "KeyCompromise"

# Elencare i template disponibili con dettagli
Get-CertificateTemplate | Select-Object Name, DisplayName,
    @{N='EKU';E={($_.Settings.EnhancedKeyUsage | ForEach-Object { $_.FriendlyName }) -join ', '}},
    @{N='KeySize';E={$_.Settings.MinimumKeySize}} |
    Format-Table -Wrap
```

---

## Interoperabilità OpenSSL e PKCS#12

In ambienti eterogenei (Linux, appliance, container), è frequente la necessità di convertire certificati tra formati diversi. OpenSSL è lo strumento standard per queste operazioni.

### Formati dei Certificati

| Formato | Estensione | Contenuto | Encoding | Uso tipico |
|---------|-----------|-----------|----------|------------|
| **DER** | .cer, .der | Certificato singolo | Binario | Windows, Java |
| **PEM** | .pem, .crt | Certificato singolo o catena | Base64 (ASCII) | Linux, Apache, Nginx |
| **PFX/PKCS#12** | .pfx, .p12 | Certificato + chiave privata + catena | Binario | Windows (import/export), IIS |
| **PKCS#7** | .p7b, .p7c | Certificato/i senza chiave privata | Base64 o binario | Distribuzione della catena |
| **PKCS#10** | .csr, .req | Certificate Signing Request | Base64 | Richiesta a CA |

### Conversioni Comuni

```powershell
# === CONVERSIONI CON certutil (nativo Windows) ===

# PEM → DER
certutil -decode "cert.pem" "cert.der"

# DER → PEM
certutil -encode "cert.der" "cert.pem"

# Visualizzare un certificato PEM/DER
certutil -dump "cert.pem"

# === CONVERSIONI CON OpenSSL (richiede OpenSSL installato) ===

# PFX → PEM (certificato + chiave separati)
openssl pkcs12 -in server.pfx -out server.pem -nodes
openssl pkcs12 -in server.pfx -out cert.pem -nokeys
openssl pkcs12 -in server.pfx -out key.pem -nocerts -nodes

# PEM → PFX
openssl pkcs12 -export -out server.pfx -inkey key.pem -in cert.pem -certfile chain.pem

# PEM → DER
openssl x509 -in cert.pem -outform DER -out cert.der

# DER → PEM
openssl x509 -in cert.der -inform DER -outform PEM -out cert.pem

# Visualizzare un certificato
openssl x509 -in cert.pem -text -noout

# Verificare corrispondenza chiave-certificato (i moduli devono coincidere)
openssl x509 -noout -modulus -in cert.pem | openssl md5
openssl rsa -noout -modulus -in key.pem | openssl md5

# Generare CSR con OpenSSL e inviare a CA Windows
openssl req -new -newkey rsa:2048 -nodes -keyout server.key \
    -out server.csr -subj "/CN=webserver.contoso.com/O=Contoso/L=Roma/C=IT"

# Inviare il CSR alla CA Windows
certreq -submit -attrib "CertificateTemplate:ContosoWebServer" server.csr server.cer

# Creare il PFX con il certificato emesso dalla CA Windows
openssl pkcs12 -export -out server.pfx -inkey server.key -in server.cer -certfile chain.pem
```

---

## Certificati TLS/SSL — Gestione Avanzata

### Certificati SAN (Subject Alternative Name)

I certificati SAN permettono di proteggere più nomi DNS con un singolo certificato. Sono lo standard per i certificati TLS moderni (il campo Subject/CN è deprecato per la validazione del nome host dai browser moderni — RFC 6125).

```powershell
# Creare un certificato SAN con più nomi DNS
New-SelfSignedCertificate -DnsName "www.contoso.com", "contoso.com", `
    "mail.contoso.com", "portal.contoso.com" `
    -CertStoreLocation Cert:\LocalMachine\My `
    -KeyAlgorithm RSA -KeyLength 2048 `
    -HashAlgorithm SHA256 `
    -NotAfter (Get-Date).AddYears(1) `
    -FriendlyName "Contoso Multi-SAN Certificate"

# Richiedere un certificato SAN dalla CA enterprise (con file INF)
$inf = @"
[NewRequest]
Subject = "CN=www.contoso.com,O=Contoso,C=IT"
KeyLength = 2048
MachineKeySet = TRUE
RequestType = PKCS10
HashAlgorithm = SHA256

[Extensions]
2.5.29.17 = "{text}"
_continue_ = "dns=www.contoso.com&"
_continue_ = "dns=contoso.com&"
_continue_ = "dns=mail.contoso.com&"
_continue_ = "dns=portal.contoso.com"

[RequestAttributes]
CertificateTemplate = ContosoWebServer
"@
$inf | Out-File "C:\Certs\san.inf" -Encoding ASCII
certreq -new "C:\Certs\san.inf" "C:\Certs\san.csr"
certreq -submit "C:\Certs\san.csr" "C:\Certs\san.cer"
certreq -accept "C:\Certs\san.cer"
```

### Certificati Wildcard

I certificati wildcard (`*.contoso.com`) proteggono tutti i sottodomini di primo livello di un dominio. Sono convenienti ma hanno implicazioni di sicurezza.

| Aspetto | Dettaglio |
|---------|-----------|
| **Copertura** | `*.contoso.com` copre `www.contoso.com`, `mail.contoso.com`, ecc. |
| **Limitazione** | NON copre `contoso.com` (naked domain) e NON copre `sub.sub.contoso.com` |
| **Rischio** | Se la chiave viene compromessa, TUTTI i servizi sono esposti |
| **Raccomandazione** | Preferire certificati SAN specifici per servizi critici |
| **AD CS** | I template devono avere "Supply in the request" per il Subject Name |

### Certificate Transparency (CT) Logs

Certificate Transparency è un framework (RFC 6962) che richiede alle CA pubbliche di registrare ogni certificato emesso in log pubblici e verificabili. Questo permette di rilevare certificati erroneamente emessi o malevoli.

```powershell
# Monitorare i CT logs per il proprio dominio usando crt.sh
# (richiede accesso Internet)
$domain = "contoso.com"
$ctResults = Invoke-RestMethod "https://crt.sh/?q=%25.$domain&output=json"
$ctResults | Select-Object id, issuer_name, common_name, not_before, not_after |
    Sort-Object not_before -Descending |
    Format-Table -AutoSize

# Verificare che un certificato sia presente nei CT logs
# I browser moderni (Chrome, Edge) richiedono Signed Certificate Timestamps (SCT)
# nei certificati per fidarsi di essi. Le CA pubbliche aggiungono SCT automaticamente.
```

### HSTS (HTTP Strict Transport Security) e HSTS Preload

HSTS è un header HTTP che istruisce il browser a connettersi sempre via HTTPS, prevenendo downgrade attacks e SSL stripping.

```powershell
# Configurare HSTS in IIS tramite web.config
# <system.webServer>
#   <httpProtocol>
#     <customHeaders>
#       <add name="Strict-Transport-Security" value="max-age=31536000; includeSubDomains; preload" />
#     </customHeaders>
#   </httpProtocol>
# </system.webServer>

# Configurare HSTS tramite PowerShell (IIS 10.0 / Windows Server 2019+)
Import-Module IISAdministration
$siteName = "Default Web Site"
$manager = Get-IISServerManager
$config = $manager.GetWebConfiguration($siteName)
$section = $config.GetSection("system.webServer/httpProtocol")
$headers = $section.GetCollection("customHeaders")
$header = $headers.CreateElement("add")
$header["name"] = "Strict-Transport-Security"
$header["value"] = "max-age=31536000; includeSubDomains; preload"
$headers.Add($header)
$manager.CommitChanges()

# Prerequisiti per HSTS Preload (hstspreload.org):
# 1. Certificato TLS valido (non self-signed)
# 2. Redirect HTTP → HTTPS su tutti i sottodomini
# 3. Header HSTS con max-age >= 31536000 (1 anno)
# 4. includeSubDomains e preload presenti
```

---

## Scenari Avanzati di Certificati

### Certificate-Based Authentication per Wi-Fi (802.1X)

Uno degli scenari più comuni per una PKI enterprise è l'autenticazione 802.1X basata su certificati per le reti wireless aziendali. I dispositivi aziendali ricevono un certificato computer tramite auto-enrollment e lo presentano al RADIUS server (NPS) durante la connessione Wi-Fi.

```powershell
# Flusso 802.1X con certificati:
# 1. Il computer riceve un certificato via auto-enrollment (template "Workstation Authentication")
# 2. L'utente si connette alla rete Wi-Fi aziendale
# 3. Il Wireless Access Point inoltra la richiesta al NPS (RADIUS)
# 4. NPS verifica il certificato del client:
#    - Chain validation (catena fino alla Root CA trust)
#    - CRL/OCSP check (non revocato)
#    - EKU check (Client Authentication)
#    - Template check (template autorizzato nella NPS policy)
# 5. NPS approva e il client ottiene accesso alla VLAN aziendale

# Configurare NPS per certificate-based authentication
# Network Policy Server → Policies → Network Policies:
# Conditions:
#   - Windows Groups: Domain Computers
#   - NAS Port Type: Wireless IEEE 802.11
# Constraints:
#   - Authentication Methods: Microsoft Smart Card or other certificate
#   - EAP Types: EAP-TLS
# Settings:
#   - RADIUS Attributes: Tunnel-Type = VLAN, Tunnel-Pvt-Group-ID = 100

# Verificare il certificato usato per 802.1X sul client
Get-ChildItem Cert:\LocalMachine\My | Where-Object {
    $_.EnhancedKeyUsageList.FriendlyName -contains "Client Authentication"
} | Select-Object Subject, Issuer, NotAfter, Thumbprint,
    @{N='Template';E={
        ($_.Extensions | Where-Object { $_.Oid.Value -eq "1.3.6.1.4.1.311.21.7" }).Format(0)
    }}

# Distribuire il profilo Wi-Fi via GPO con certificato
# Computer Configuration → Policies → Windows Settings → Security Settings
#   → Wireless Network (802.11) Policies → New Policy
#   → Add SSID → Authentication: WPA2-Enterprise → EAP Type: Smart Card or Certificate
```

### TLS Mutual Authentication (mTLS)

La mutual TLS authentication richiede che sia il server che il client presentino un certificato durante il TLS handshake. Questo è più sicuro della TLS standard (dove solo il server si autentica) ed è usato per API interne, microservizi e comunicazioni M2M.

```powershell
# Configurare IIS per richiedere il certificato client (mTLS)
# IIS Manager → Sites → Default Web Site → SSL Settings:
#   → Require SSL
#   → Client Certificates: Require

# Configurare via PowerShell
Import-Module WebAdministration
Set-WebConfigurationProperty -Filter "system.webServer/security/access" `
    -PSPath "IIS:\Sites\Default Web Site" `
    -Name sslFlags -Value "Ssl, SslRequireCert"

# Configurare il mapping certificato-utente (one-to-one)
# IIS Manager → Sites → Default Web Site → Authentication
# → IIS Client Certificate Mapping Authentication → Enable

# Verificare il certificato client presentato in una richiesta HTTPS
$listener = [System.Net.HttpListener]::new()
$listener.Prefixes.Add("https://+:8443/")
$listener.Start()
# Il certificato client è in: $context.Request.GetClientCertificate()
```

### IPsec con Certificati

IPsec usa certificati per l'autenticazione dei peer in scenari site-to-site o transport mode.

```powershell
# Creare una Connection Security Rule con autenticazione via certificato
New-NetIPsecRule -DisplayName "Server-to-Server IPsec" `
    -InboundSecurity Require -OutboundSecurity Require `
    -Phase1AuthSet (New-NetIPsecAuthProposal -Machine -Cert `
        -Authority "CN=Contoso Enterprise CA" `
        -AuthorityType Root) `
    -Protocol TCP -LocalPort 445

# Verificare le regole IPsec attive
Get-NetIPsecRule | Format-Table DisplayName, InboundSecurity, OutboundSecurity
```

### Smart Card Logon e PKINIT

L'autenticazione con smart card utilizza il protocollo PKINIT (RFC 4556) per estendere Kerberos con certificati X.509. Il certificato sulla smart card sostituisce la password nel processo di autenticazione.

```powershell
# Requisiti per Smart Card Logon:
# 1. Template "Smartcard Logon" o "Smartcard User" pubblicato sulla CA
# 2. EKU: Smart Card Logon (1.3.6.1.4.1.311.20.2.2) + Client Authentication
# 3. Subject contiene UPN dell'utente nel SAN (userPrincipalName)
# 4. NTAuthCertificates in AD contiene il certificato della CA emittente

# Verificare NTAuthCertificates
certutil -viewstore -enterprise NTAuth

# Aggiungere un certificato CA a NTAuthCertificates
certutil -dspublish -f "IssuingCA.cer" NTAuth

# Verificare i certificati sulla smart card
certutil -scinfo

# Testare il logon con smart card
# Inserire la smart card → Windows presenta la schermata di logon con PIN

# Forzare l'autenticazione solo via smart card per un utente
Set-ADUser -Identity "admin.sicurezza" -SmartcardLogonRequired $true
```

### VPN con Certificati (IKEv2 / SSTP)

```powershell
# Template per certificati VPN server (NPS/RRAS):
# - EKU: Server Authentication + IP Security IKE Intermediate (1.3.6.1.5.5.8.2.2)
# - SAN: DNS name del VPN server (vpn.contoso.com)

# Template per certificati VPN client:
# - EKU: Client Authentication
# - Auto-enrollment per i computer del dominio

# Configurazione VPN IKEv2 con certificato (sul client)
Add-VpnConnection -Name "Contoso VPN" `
    -ServerAddress "vpn.contoso.com" `
    -TunnelType IKEv2 `
    -AuthenticationMethod MachineCertificate `
    -EncryptionLevel Maximum

# Verificare la connessione VPN
Get-VpnConnection -Name "Contoso VPN" | Format-List *
```

### Code Signing Certificates

I certificati di code signing vengono utilizzati per firmare script PowerShell, applicazioni, driver e macro, garantendo l'integrità e l'autenticità del codice.

```powershell
# Creare un template per code signing
# Duplicare il template "Code Signing" esistente
# Configurazioni importanti:
# - Subject Name: Supply in the request
# - EKU: Code Signing (1.3.6.1.5.5.7.3.3)
# - Private Key: Not exportable
# - Security: Solo il gruppo degli sviluppatori autorizzati

# Richiedere un certificato code signing
$cert = Get-Certificate -Template "ContosoCodeSigning" -CertStoreLocation Cert:\CurrentUser\My

# Firmare uno script PowerShell
$signingCert = Get-ChildItem Cert:\CurrentUser\My -CodeSigningCert |
    Where-Object Subject -like "*Developer*"

Set-AuthenticodeSignature -FilePath "C:\Scripts\Deploy.ps1" -Certificate $signingCert `
    -TimestampServer "http://timestamp.digicert.com" -HashAlgorithm SHA256

# Verificare la firma di uno script
Get-AuthenticodeSignature "C:\Scripts\Deploy.ps1" | Select-Object Status, SignerCertificate, TimeStamperCertificate

# Configurare PowerShell per richiedere la firma degli script
Set-ExecutionPolicy AllSigned -Scope LocalMachine

# Firmare tutti gli script in una cartella
Get-ChildItem "C:\Scripts\*.ps1" | ForEach-Object {
    Set-AuthenticodeSignature -FilePath $_.FullName -Certificate $signingCert `
        -TimestampServer "http://timestamp.digicert.com" -HashAlgorithm SHA256
    Write-Output "Firmato: $($_.Name)"
}
```

### Driver Signing e SHA-256 Migration

A partire da Windows 10 1607, Microsoft richiede certificati di cross-signing per i driver in kernel mode. I driver devono essere firmati con SHA-256 (SHA-1 non è più accettato per i nuovi driver).

```powershell
# Firmare un driver con signtool (parte del Windows SDK)
# signtool sign /fd SHA256 /a /tr http://timestamp.digicert.com /td SHA256 mydriver.sys

# Verificare la firma di un driver
# signtool verify /pa /v mydriver.sys

# Per i driver kernel-mode distribuiti tramite Windows Update:
# 1. Registrare un account nel Windows Hardware Dev Center
# 2. Inviare il driver per la certificazione Microsoft
# 3. Microsoft firma il driver con il proprio certificato

# Timestamp server: SEMPRE usare un timestamp server!
# Se il certificato scade, la firma rimane valida grazie al timestamp.
# Senza timestamp, la firma diventa non valida alla scadenza del certificato.
```

### Key Archival e Recovery

Il Key Archival permette alla CA di archiviare una copia della chiave privata dell'utente, consentendo il recovery in caso di perdita (ad esempio, se un utente cifra file con S/MIME e poi perde il profilo).

```powershell
# Abilitare Key Archival sulla CA
# certsrv.msc → Properties della CA → Recovery Agents tab
# Aggiungere i certificati degli agenti di recovery (KRA - Key Recovery Agent)

# Configurare il template per Key Archival
# Template Properties → Request Handling:
#   Archive subject's encryption private key: Yes

# Recuperare una chiave archiviata
# 1. Trovare il numero di serie del certificato
certutil -getkey "UserSearchString" "C:\Recovery\outputblob.dat"

# 2. Recuperare la chiave con il KRA certificate
certutil -recoverkey "C:\Recovery\outputblob.dat" "C:\Recovery\recovered.pfx"

# 3. Importare il PFX recuperato nel profilo dell'utente
Import-PfxCertificate -FilePath "C:\Recovery\recovered.pfx" `
    -CertStoreLocation Cert:\CurrentUser\My `
    -Password (ConvertTo-SecureString "RecoveryP@ss" -AsPlainText -Force)

# Audit: elencare tutte le chiavi archiviate
certutil -view -restrict "RequestDisposition=20" -out "RequestID,CommonName,NotBefore,NotAfter"
```

### Disaster Recovery della PKI

La perdita della CA è un evento catastrofico che può paralizzare l'intera infrastruttura. Un piano di DR per la PKI deve includere:

```powershell
# BACKUP DELLA CA (eseguire regolarmente)

# 1. Backup del database della CA e della chiave privata
$backupPath = "D:\CABackups\$(Get-Date -Format 'yyyy-MM-dd')"
New-Item $backupPath -ItemType Directory -Force

# Backup database
Backup-CARoleService -Path $backupPath

# Backup della chiave privata (separatamente, con password forte)
certutil -backupkey "$backupPath\PrivateKey"

# Backup della configurazione del registry
reg export "HKLM\SYSTEM\CurrentControlSet\Services\CertSvc" "$backupPath\CertSvc-Registry.reg"

# 2. Backup dei template (esportare da AD)
$templateDN = "CN=Certificate Templates,CN=Public Key Services,CN=Services,$((Get-ADRootDSE).configurationNamingContext)"
Get-ADObject -SearchBase $templateDN -Filter * -Properties * |
    Export-Clixml "$backupPath\CertTemplates.xml"

# RESTORE DELLA CA (procedura di disaster recovery)
# 1. Installare Windows Server con lo stesso hostname
# 2. Installare il ruolo AD CS
# 3. Ripristinare il backup:
Restore-CARoleService -Path $backupPath -Force
# 4. Verificare i certificati emessi:
certutil -view -restrict "Disposition=20" | Select-Object -First 10
```

---

## AD CS Abuse e Hardening — ESC1-ESC8

AD CS è uno dei vettori di attacco più sottovalutati in Active Directory. La ricerca "Certified Pre-Owned" (Will Schroeder e Lee Christensen, 2021) ha documentato otto classi di vulnerabilità (ESC1-ESC8) che permettono l'escalation di privilegi fino a Domain Admin o Enterprise Admin. Ogni sysadmin che gestisce una PKI deve conoscere questi vettori e applicare le mitigazioni.

### Strumenti di Audit

| Strumento | Linguaggio | Descrizione |
|-----------|-----------|-------------|
| **Certipy** | Python | Audit completo AD CS, enumeration, abuse, ESC1-ESC8 |
| **Certify** | C# (.NET) | Enumeration e abuse template, Golden Certificate |
| **PSPKIAudit** | PowerShell | Audit dei template e delle configurazioni CA |
| **ADCSKiller** | Python | Automazione dell'exploitation di template vulnerabili |

```powershell
# Enumerazione con Certipy (eseguire da Kali o con Python su Windows)
# certipy find -u user@contoso.com -p 'Password' -dc-ip 10.0.0.1 -vulnerable
# certipy find -u user@contoso.com -p 'Password' -dc-ip 10.0.0.1 -json

# Enumerazione con Certify (da un host domain-joined)
# Certify.exe find /vulnerable
# Certify.exe find /vulnerable /currentuser
```

### ESC1 — Template con SAN Controllabile dall'Utente

**Vettore:** Il template ha "Supply in the request" per il Subject Name E un utente a basso privilegio ha permesso di Enroll.

**Impatto:** L'attaccante può richiedere un certificato con il SAN di qualsiasi utente (es. `administrator@contoso.com`) e autenticarsi come Domain Admin.

**Condizioni:**
- Template ha CT_FLAG_ENROLLEE_SUPPLIES_SUBJECT
- EKU include Client Authentication o PKINIT
- Utente a basso privilegio ha Enroll permission

**Mitigazione:**
```
1. Rimuovere "Supply in the request" → usare "Build from AD information"
2. Se "Supply in the request" è necessario: abilitare "CA certificate manager approval"
3. Limitare i permessi di Enroll ai soli gruppi necessari
4. Abilitare l'audit: certsrv.msc → Properties → Auditing tab
```

### ESC2 — Template con Any Purpose EKU o Nessun EKU

**Vettore:** Template con EKU "Any Purpose" (2.5.29.37.0) o senza EKU (SubCA certificate in pratica).

**Impatto:** Il certificato può essere usato per qualsiasi scopo, inclusa l'autenticazione come qualsiasi utente.

**Mitigazione:**
```
1. Non usare mai "Any Purpose" per template utente/computer
2. Specificare sempre EKU restrittivi (solo Server Auth, solo Client Auth, ecc.)
3. Template senza EKU: rimuoverli o aggiungere EKU specifici
```

### ESC3 — Enrollment Agent Abuse

**Vettore:** Template "Enrollment Agent" con permessi troppo permissivi. Un Enrollment Agent può richiedere certificati per conto di altri utenti.

**Impatto:** Qualsiasi utente con certificato Enrollment Agent può ottenere certificati per Domain Admin.

**Mitigazione:**
```
1. Limitare il template Enrollment Agent ai soli agenti autorizzati
2. Configurare "Restrict enrollment agents" sulla CA:
   certsrv.msc → CA Properties → Enrollment Agents tab
   → Restrict enrollment agents → specificare chi può fare enrollment per chi
3. Evitare di pubblicare template Enrollment Agent su CA enterprise
```

### ESC4 — ACL Vulnerabili sui Template

**Vettore:** Un utente a basso privilegio ha permessi di scrittura (Write / FullControl) sull'oggetto AD del template.

**Impatto:** L'attaccante modifica il template per aggiungere "Supply in the request" e/o "Any Purpose" EKU, trasformandolo in ESC1 o ESC2.

**Mitigazione:**
```powershell
# Audit dei permessi su tutti i template
$templateDN = "CN=Certificate Templates,CN=Public Key Services,CN=Services,$((Get-ADRootDSE).configurationNamingContext)"
Get-ADObject -SearchBase $templateDN -Filter * -Properties nTSecurityDescriptor | ForEach-Object {
    $template = $_.Name
    $_.nTSecurityDescriptor.Access | Where-Object {
        $_.ActiveDirectoryRights -match 'WriteProperty|WriteDacl|WriteOwner|GenericAll|GenericWrite' -and
        $_.IdentityReference -notmatch 'Enterprise Admins|Domain Admins|SYSTEM|Cert Publishers'
    } | ForEach-Object {
        [PSCustomObject]@{
            Template   = $template
            Identity   = $_.IdentityReference
            Rights     = $_.ActiveDirectoryRights
            AccessType = $_.AccessControlType
        }
    }
} | Format-Table -Wrap

# Rimuovere permessi eccessivi
# Se "Authenticated Users" ha GenericWrite su un template:
# → Rimuovere e limitare a gruppi specifici
```

### ESC5 — ACL Vulnerabili sulla CA Object

**Vettore:** Permessi eccessivi sull'oggetto CA in AD o sul server CA stesso.

**Impatto:** L'attaccante modifica la configurazione della CA per abilitare template vulnerabili, modificare CDP/AIA o estrarre la chiave privata.

**Mitigazione:**
```
1. Verificare ACL sull'oggetto CA in AD:
   CN=<CA Name>,CN=Enrollment Services,CN=Public Key Services,CN=Services,...
2. Solo Enterprise Admins e Domain Admins devono avere FullControl
3. Hardening del server CA: limitare accesso RDP, logon locale solo a PKI admins
4. Non installare altri ruoli sul server CA
```

### ESC6 — EDITF_ATTRIBUTESUBJECTALTNAME2

**Vettore:** La CA ha il flag `EDITF_ATTRIBUTESUBJECTALTNAME2` abilitato, che permette al richiedente di specificare SAN arbitrari in qualsiasi richiesta, indipendentemente dalla configurazione del template.

**Impatto:** Qualsiasi utente che può fare enrollment su qualsiasi template con Client Auth EKU può ottenere un certificato per qualsiasi identità.

**Verifica e mitigazione:**
```powershell
# Verificare se il flag è abilitato
certutil -getreg policy\EditFlags
# Se il valore contiene EDITF_ATTRIBUTESUBJECTALTNAME2 (0x00040000):

# RIMUOVERE IL FLAG (mitigazione critica)
certutil -setreg policy\EditFlags -EDITF_ATTRIBUTESUBJECTALTNAME2
Restart-Service certsvc

# Verificare la rimozione
certutil -getreg policy\EditFlags
```

> **Errore comune:** Molti tutorial online suggeriscono di abilitare `EDITF_ATTRIBUTESUBJECTALTNAME2` per semplificare la creazione di certificati SAN. Questo apre ESC6 — non farlo mai in produzione. Usare invece template con "Supply in the request" e approvazione del manager.

### ESC7 — Permessi di CA Officer o Manager sulla CA

**Vettore:** Un utente a basso privilegio ha il permesso "Manage CA" o "Manage Certificates" sulla CA.

**Impatto:** "Manage CA" permette di aggiungere template (inclusi quelli vulnerabili). "Manage Certificates" permette di approvare richieste pending, incluse richieste per certificati di escalation.

**Mitigazione:**
```
1. Limitare "Manage CA" a un gruppo dedicato (PKI Admins)
2. Limitare "Manage Certificates" a un gruppo dedicato (Certificate Managers)
3. Audit: certsrv.msc → Properties → Security tab → verificare i permessi
4. Non assegnare MAI questi permessi a Domain Users o Authenticated Users
```

### ESC8 — NTLM Relay alla Web Enrollment

**Vettore:** Il servizio Web Enrollment (certsrv) accetta autenticazione NTLM senza Extended Protection for Authentication (EPA). Un attaccante può fare relay dell'autenticazione NTLM di un Domain Controller al servizio certsrv e ottenere un certificato per il DC.

**Impatto:** Compromissione del Domain Controller tramite relay NTLM → certificato DC → DCSync.

**Mitigazione:**
```powershell
# 1. Abilitare EPA (Extended Protection for Authentication) su IIS/certsrv
# IIS Manager → Sites → Default Web Site → CertSrv → Authentication
# → Windows Authentication → Advanced Settings → Extended Protection: Required

# 2. Disabilitare HTTP e richiedere HTTPS per certsrv
# IIS Manager → Sites → Default Web Site → CertSrv → SSL Settings
# → Require SSL → Require 128-bit encryption

# 3. Alternativa: disabilitare completamente Web Enrollment se non necessario
# È preferibile usare auto-enrollment o CEP/CES

# 4. Disabilitare NTLM dove possibile → forzare Kerberos
# GPO: Computer Configuration → Windows Settings → Security Settings
# → Local Policies → Security Options
# → Network security: Restrict NTLM: NTLM authentication in this domain
```

### Checklist Hardening AD CS

```
┌──────────────────────────────────────────────────────────────────────┐
│                     AD CS HARDENING CHECKLIST                        │
├──────────────────────────────────────────────────────────────────────┤
│ [ ] EDITF_ATTRIBUTESUBJECTALTNAME2 disabilitato su tutte le CA      │
│ [ ] Nessun template con "Any Purpose" EKU pubblicato                │
│ [ ] Template con "Supply in the request" → approvazione obbligatoria│
│ [ ] Permessi Enroll limitati ai gruppi necessari per ogni template   │
│ [ ] Nessun utente non-admin ha Write su oggetti template in AD      │
│ [ ] "Manage CA" e "Manage Certificates" solo per PKI admins          │
│ [ ] Web Enrollment (certsrv) → EPA abilitato o servizio disabilitato│
│ [ ] Audit abilitato sulla CA per enrollment/revocation/key access    │
│ [ ] Enrollment Agent con restrizioni configurate                     │
│ [ ] CA server hardened (no altri ruoli, accesso limitato)            │
│ [ ] Root CA offline e in vault                                       │
│ [ ] Backup della chiave privata CA protetto e testato               │
│ [ ] Scan periodico con Certipy/Certify per template vulnerabili      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Let's Encrypt e ACME su Windows

### Protocollo ACME

ACME (Automatic Certificate Management Environment, RFC 8555) è il protocollo usato da Let's Encrypt per l'emissione automatizzata di certificati DV (Domain Validation) gratuiti. L'integrazione con Windows permette di avere certificati TLS pubblici rinnovati automaticamente, complementari alla PKI interna.

### Client ACME per Windows

| Client | Tipo | Descrizione |
|--------|------|-------------|
| **win-acme** (wacs) | CLI / Scheduled Task | Il più popolare per IIS, supporta DNS challenge |
| **Certbot** | CLI (Python) | Client ufficiale Let's Encrypt, supporto Windows |
| **Posh-ACME** | PowerShell module | Nativo PowerShell, integrabile in script |
| **Caddy** | Reverse proxy | ACME built-in, auto-renewal |

### win-acme (wacs) — Configurazione per IIS

```powershell
# 1. Scaricare win-acme da https://www.win-acme.com/
# 2. Estrarre in C:\Tools\win-acme\

# Ottenere un certificato per un sito IIS
# wacs.exe --target iis --siteid 1 --installation iis --webroot C:\inetpub\wwwroot

# Ottenere un certificato con DNS challenge (wildcard)
# wacs.exe --target manual --host "*.contoso.com" --validation dns-01 --validationmode dns-01.manual

# Rinnovo automatico: wacs crea un Scheduled Task che rinnova ogni giorno
# Il rinnovo avviene solo quando il certificato è a < 30 giorni dalla scadenza
```

### Posh-ACME — Gestione Certificati Let's Encrypt con PowerShell

```powershell
# Installare il modulo
Install-Module -Name Posh-ACME -Scope CurrentUser

# Configurare l'ACME server (Let's Encrypt production)
Set-PAServer -DirectoryUrl 'https://acme-v02.api.letsencrypt.org/directory'

# Creare un account ACME
New-PAAccount -AcceptTOS -Contact 'admin@contoso.com'

# Ottenere un certificato con HTTP-01 challenge
New-PACertificate -Domain 'www.contoso.com' -Plugin WebSelfHost

# Ottenere un certificato con DNS-01 challenge (supporta wildcard)
# Richiede un plugin DNS per il proprio provider (Azure DNS, Cloudflare, ecc.)
New-PACertificate -Domain '*.contoso.com' -Plugin AzureDns `
    -PluginArgs @{
        AZSubscriptionId = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
        AZTenantId       = 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'
        AZAppCred        = (Get-Credential)
    }

# Importare il certificato in IIS
$cert = Get-PACertificate
Import-PfxCertificate -FilePath $cert.PfxFile `
    -CertStoreLocation Cert:\LocalMachine\My `
    -Password (ConvertTo-SecureString $cert.PfxPass -AsPlainText -Force)

# Script di rinnovo automatico (da schedulare)
Submit-Renewal | ForEach-Object {
    if ($_) {
        Import-PfxCertificate -FilePath $_.PfxFile `
            -CertStoreLocation Cert:\LocalMachine\My `
            -Password (ConvertTo-SecureString $_.PfxPass -AsPlainText -Force)
        Write-Output "Certificato rinnovato: $($_.AllSANs -join ', ')"
    }
}
```

### Hybrid PKI: CA Interna + Let's Encrypt

| Certificato | CA | Motivo |
|------------|-----|--------|
| 802.1X, Smart Card, S/MIME | CA interna | Richiede trust chain interna, non DV |
| Web server interni (intranet) | CA interna | Non raggiungibili dall'esterno |
| Web server pubblici | Let's Encrypt | Gratuito, auto-renewal, trusted da tutti i browser |
| API gateway DMZ | Let's Encrypt | DV sufficiente, auto-renewal |
| Code signing | CA interna o CA commerciale | Richiede EV o OV, non DV |

---

## Migrazione della CA tra Server

La migrazione di una CA da un server Windows a un altro (es. per aggiornamento del sistema operativo, sostituzione hardware o cambio hostname) è un'operazione delicata che richiede pianificazione.

### Pre-requisiti

- Il nuovo server deve avere lo stesso nome del server originale (o si deve aggiornare il CDP/AIA)
- Il nuovo server deve essere unito al dominio (per Enterprise CA)
- Tutti i backup devono essere verificati prima di iniziare

### Procedura di Migrazione Step-by-Step

```powershell
# === FASE 1: BACKUP SUL SERVER ORIGINALE ===

# 1.1 Backup del database CA e della chiave privata
$backupPath = "D:\CAMigration\Backup"
New-Item $backupPath -ItemType Directory -Force
Backup-CARoleService -Path $backupPath

# 1.2 Backup della chiave privata (con password)
certutil -backupkey "$backupPath\CAKey"
# Inserire la password quando richiesto — conservarla in modo sicuro!

# 1.3 Esportare la configurazione del registry
reg export "HKLM\SYSTEM\CurrentControlSet\Services\CertSvc" "$backupPath\CertSvc.reg"

# 1.4 Esportare le configurazioni CA specifiche
certutil -getreg > "$backupPath\CA-Registry-Dump.txt"

# 1.5 Elencare i template pubblicati
certutil -catemplates > "$backupPath\PublishedTemplates.txt"

# 1.6 Backup dei file CRL e AIA
Copy-Item "C:\Windows\System32\CertSrv\CertEnroll\*" "$backupPath\CertEnroll\" -Recurse

# === FASE 2: DISINSTALLARE LA CA DAL SERVER ORIGINALE ===
# NOTA: NON disinstallare il ruolo AD CS. Rimuovere solo la configurazione.
# Questo preserva gli oggetti in AD.

# === FASE 3: INSTALLARE AD CS SUL NUOVO SERVER ===

# 3.1 Installare il ruolo (senza configurare)
Install-WindowsFeature -Name ADCS-Cert-Authority -IncludeManagementTools

# 3.2 Ripristinare il database e la chiave
Restore-CARoleService -Path $backupPath -Force

# 3.3 Importare la configurazione del registry
reg import "$backupPath\CertSvc.reg"

# 3.4 Avviare il servizio CA
Start-Service certsvc

# === FASE 4: VALIDAZIONE POST-MIGRAZIONE ===

# 4.1 Verificare che la CA sia funzionante
certutil -ping

# 4.2 Verificare i certificati emessi
certutil -view -restrict "Disposition=20" -out "RequestID,CommonName,NotAfter" | Select-Object -First 20

# 4.3 Verificare i template pubblicati
certutil -catemplates

# 4.4 Pubblicare una nuova CRL
certutil -CRL

# 4.5 Verificare i CDP
certutil -URL "http://pki.contoso.com/CertEnroll/ContosoCA.crl"

# 4.6 Testare l'enrollment
certreq -enroll -machine "ContosoWebServer"

# 4.7 Aggiornare i DNS record se l'IP è cambiato
# Il CDP HTTP deve puntare al nuovo server (o meglio, a un alias DNS stabile)
```

### Migrazione con Cambio Hostname

Se il nuovo server ha un hostname diverso, è necessario aggiornare tutti i CDP e AIA:

```powershell
# Aggiornare i CDP (se l'hostname del CA server appare nel CDP URL)
# NOTA: è per questo che si raccomanda di usare un alias DNS (pki.contoso.com)
#       e non l'hostname del server (ca01.contoso.com) nei CDP/AIA

# Se i CDP/AIA contengono il vecchio hostname:
certutil -setreg CA\CRLPublicationURLs "..."  # nuovi URL con nuovo hostname
certutil -setreg CA\CACertPublicationURLs "..."  # nuovi URL
Restart-Service certsvc
certutil -CRL  # Pubblicare CRL con i nuovi CDP

# I certificati già emessi conterranno i vecchi CDP/AIA
# Opzioni: 
# 1. Creare un alias DNS che punta dal vecchio hostname al nuovo
# 2. Attendere il rinnovo naturale dei certificati (otterranno i nuovi CDP)
# 3. Forzare il rinnovo con certutil -pulse su tutti i client
```

---

## Monitoring e Compliance PKI

### Event ID Critici per il Monitoring della CA

| Event ID | Fonte | Descrizione | Severità |
|----------|-------|-------------|----------|
| **4886** | Security | Richiesta di certificato ricevuta | Informativo |
| **4887** | Security | Certificato emesso | Informativo |
| **4888** | Security | Richiesta di certificato rifiutata | Warning |
| **4889** | Security | Estensione del certificato (pendente → emesso) | Informativo |
| **4890** | Security | Impostazioni del template modificate | Critico |
| **4891** | Security | Template aggiunto alla CA | Critico |
| **4892** | Security | Template rimosso dalla CA | Warning |
| **4893** | Security | CA avviata | Informativo |
| **4894** | Security | CA fermata | Warning |
| **4895** | Security | CRL pubblicata | Informativo |
| **4896** | Security | Row(s) eliminato/i dal database della CA | Critico |
| **4899** | Security | Template di certificato aggiornato | Critico |
| **4900** | Security | Security del template modificata | Critico |

### Abilitare l'Audit sulla CA

```powershell
# Abilitare l'audit per tutti gli eventi della CA
certutil -setreg CA\AuditFilter 127
# Bit mask:
# 1  = Start/Stop del servizio CA
# 2  = Backup/Restore del database CA
# 4  = Emissione/rifiuto certificato
# 8  = Revoca certificato
# 16 = Modifica security settings della CA
# 32 = Recupero chiavi archiviate
# 64 = Configurazione CA modificata
# 127 = TUTTO (raccomandato)

Restart-Service certsvc

# Abilitare l'audit policy via GPO sul CA server
# Computer Configuration → Windows Settings → Security Settings
# → Advanced Audit Policy Configuration → Object Access
# → Audit Certification Services: Success, Failure
```

### Script di Health Check PKI

```powershell
# === PKI Health Check Script ===
# Eseguire periodicamente (scheduled task giornaliero)

$results = @()

# 1. Verificare il servizio CA
$caService = Get-Service certsvc -ErrorAction SilentlyContinue
$results += [PSCustomObject]@{
    Check  = "Servizio CA (certsvc)"
    Status = if ($caService.Status -eq 'Running') { "OK" } else { "CRITICAL" }
    Detail = $caService.Status
}

# 2. Verificare la validità del certificato CA
$caCert = Get-ChildItem Cert:\LocalMachine\My |
    Where-Object { $_.Extensions | Where-Object { $_.Oid.Value -eq "2.5.29.19" -and $_.Format(0) -match "Subject Type=CA" } } |
    Select-Object -First 1
$caDaysLeft = ($caCert.NotAfter - (Get-Date)).Days
$results += [PSCustomObject]@{
    Check  = "Certificato CA"
    Status = if ($caDaysLeft -gt 365) { "OK" } elseif ($caDaysLeft -gt 90) { "WARNING" } else { "CRITICAL" }
    Detail = "Scade tra $caDaysLeft giorni ($($caCert.NotAfter.ToString('yyyy-MM-dd')))"
}

# 3. Verificare la CRL corrente
try {
    $crl = certutil -URL "http://pki.contoso.com/CertEnroll/ContosoEnterpriseCA.crl" 2>&1
    $crlOK = $crl -match "Verified"
    $results += [PSCustomObject]@{
        Check  = "CRL HTTP raggiungibile"
        Status = if ($crlOK) { "OK" } else { "CRITICAL" }
        Detail = if ($crlOK) { "CRL valida e raggiungibile" } else { "CRL NON raggiungibile!" }
    }
} catch {
    $results += [PSCustomObject]@{ Check = "CRL HTTP"; Status = "CRITICAL"; Detail = $_.Exception.Message }
}

# 4. Certificati in scadenza nei prossimi 30 giorni
$expiringCount = (Get-ChildItem Cert:\LocalMachine\My | Where-Object {
    $_.NotAfter -lt (Get-Date).AddDays(30) -and $_.NotAfter -gt (Get-Date)
}).Count
$results += [PSCustomObject]@{
    Check  = "Certificati in scadenza (30gg)"
    Status = if ($expiringCount -eq 0) { "OK" } else { "WARNING" }
    Detail = "$expiringCount certificato/i in scadenza"
}

# 5. Spazio disco per il database CA
$dbDisk = Get-WmiObject Win32_LogicalDisk -Filter "DeviceID='C:'"
$freeGB = [math]::Round($dbDisk.FreeSpace / 1GB, 1)
$results += [PSCustomObject]@{
    Check  = "Spazio disco CA"
    Status = if ($freeGB -gt 10) { "OK" } elseif ($freeGB -gt 2) { "WARNING" } else { "CRITICAL" }
    Detail = "$freeGB GB liberi"
}

# Report
Write-Output "`n=== PKI HEALTH CHECK — $(Get-Date -Format 'yyyy-MM-dd HH:mm') ==="
$results | Format-Table Check, Status, Detail -AutoSize

# Alert via email se qualcosa è CRITICAL
$criticals = $results | Where-Object Status -eq "CRITICAL"
if ($criticals) {
    $body = ($criticals | Format-Table | Out-String)
    # Send-MailMessage -To "pki-team@contoso.com" -From "pki-monitor@contoso.com" `
    #     -Subject "ALERT: PKI Health Check - CRITICAL" -Body $body -SmtpServer "smtp.contoso.com"
}
```

### Script di Inventario Certificati del Dominio

```powershell
# === INVENTARIO COMPLETO CERTIFICATI DEL DOMINIO ===
# Esegue una scansione di tutti i server e raccoglie informazioni sui certificati

$outputFile = "C:\Reports\CertInventory-$(Get-Date -Format 'yyyyMMdd').csv"

$servers = Get-ADComputer -Filter 'OperatingSystem -like "*Server*"' -Properties OperatingSystem |
    Select-Object Name, OperatingSystem

$allCerts = $servers | ForEach-Object -Parallel {
    $server = $_.Name
    $os = $_.OperatingSystem
    try {
        Invoke-Command -ComputerName $server -ScriptBlock {
            Get-ChildItem Cert:\LocalMachine\My -ErrorAction SilentlyContinue | ForEach-Object {
                [PSCustomObject]@{
                    Subject      = $_.Subject
                    Issuer       = $_.Issuer
                    NotBefore    = $_.NotBefore
                    NotAfter     = $_.NotAfter
                    DaysLeft     = [math]::Max(0, ($_.NotAfter - (Get-Date)).Days)
                    Thumbprint   = $_.Thumbprint
                    HasPrivateKey = $_.HasPrivateKey
                    KeySize      = $_.PublicKey.Key.KeySize
                    SignAlgo     = $_.SignatureAlgorithm.FriendlyName
                    Template     = ($_.Extensions | Where-Object { $_.Oid.Value -eq "1.3.6.1.4.1.311.21.7" } |
                                   ForEach-Object { $_.Format(0) })
                    SAN          = ($_.Extensions | Where-Object { $_.Oid.Value -eq "2.5.29.17" } |
                                   ForEach-Object { $_.Format(0) })
                }
            }
        } -ErrorAction Stop | ForEach-Object {
            $_ | Add-Member -NotePropertyName Server -NotePropertyValue $server -PassThru |
                 Add-Member -NotePropertyName OS -NotePropertyValue $os -PassThru
        }
    } catch {
        [PSCustomObject]@{
            Server = $server; OS = $os; Subject = "ERRORE: $($_.Exception.Message)"
            Issuer = ""; NotBefore = $null; NotAfter = $null; DaysLeft = -1
            Thumbprint = ""; HasPrivateKey = $false; KeySize = 0
            SignAlgo = ""; Template = ""; SAN = ""
        }
    }
} -ThrottleLimit 20

$allCerts | Export-Csv $outputFile -NoTypeInformation -Encoding UTF8
Write-Output "Inventario completato: $($allCerts.Count) certificati su $($servers.Count) server"
Write-Output "Report salvato in: $outputFile"

# Report riassuntivo
Write-Output "`n=== RIEPILOGO ==="
Write-Output "Certificati scaduti:       $($allCerts | Where-Object { $_.DaysLeft -eq 0 -and $_.NotAfter -ne $null } | Measure-Object).Count"
Write-Output "Scadono entro 30 giorni:   $($allCerts | Where-Object { $_.DaysLeft -gt 0 -and $_.DaysLeft -le 30 } | Measure-Object).Count"
Write-Output "Scadono entro 90 giorni:   $($allCerts | Where-Object { $_.DaysLeft -gt 30 -and $_.DaysLeft -le 90 } | Measure-Object).Count"
Write-Output "SHA-1 ancora in uso:       $($allCerts | Where-Object { $_.SignAlgo -match 'sha1' } | Measure-Object).Count"
Write-Output "RSA < 2048 bit:            $($allCerts | Where-Object { $_.KeySize -gt 0 -and $_.KeySize -lt 2048 } | Measure-Object).Count"
Write-Output "Server non raggiungibili:  $($allCerts | Where-Object { $_.DaysLeft -eq -1 } | Measure-Object).Count"
```

### Monitoring con Enterprise Tools

| Strumento | Integrazione PKI | Cosa monitorare |
|-----------|-----------------|-----------------|
| **SCOM** | Management Pack for AD CS | CA service health, CRL expiry, certificate expiry |
| **Splunk / Sentinel** | Event forwarding | Event ID 4886-4900 dalla CA |
| **Nagios / Zabbix** | Custom check | CRL HTTP reachability, OCSP response time |
| **PKIView (pkiview.msc)** | Built-in Windows | CA hierarchy health, CDP/AIA raggiungibilità |
| **certutil -verify** | Nativo | Chain validation end-to-end |

```powershell
# Usare PKIView (Enterprise PKI snap-in) per una vista d'insieme
# pkiview.msc → mostra lo stato di salute dell'intera gerarchia PKI
# Controlla automaticamente: certificati CA, CRL, delta CRL, AIA, OCSP

# Verificare la salute PKI da riga di comando
certutil -ping  # Verifica che il servizio CA risponda
certutil -CAInfo  # Informazioni sulla CA (certificato, CRL, template)
```

---

## Securing the CA — Hardening e Key Ceremony

### Hardening del Server CA

Il server che ospita la CA è uno degli asset più critici dell'infrastruttura. La sua compromissione equivale alla compromissione dell'intera PKI.

```
┌──────────────────────────────────────────────────────────────────────┐
│                     CA SERVER HARDENING CHECKLIST                     │
├──────────────────────────────────────────────────────────────────────┤
│ [ ] Server dedicato: nessun altro ruolo installato                   │
│ [ ] OS aggiornato: patch mensili applicate entro 72h                 │
│ [ ] Accesso fisico: server in rack protetto o VM con accesso limitato│
│ [ ] Login locale: limitato al gruppo "PKI Administrators"            │
│ [ ] RDP: disabilitato o limitato a jump server con MFA              │
│ [ ] PowerShell remoting: limitato a PKI admins con JEA               │
│ [ ] Firewall: solo porte necessarie (RPC, LDAP, HTTP per CDP)       │
│ [ ] Antivirus: esclusioni per database CA e CertEnroll               │
│ [ ] Audit: AuditFilter=127, Advanced Audit Policy configurata       │
│ [ ] Backup: giornaliero, testato trimestralmente                     │
│ [ ] SMBv1: disabilitato                                              │
│ [ ] LLMNR/NBT-NS: disabilitato                                      │
│ [ ] NTLM: limitato (preferire Kerberos)                              │
│ [ ] BitLocker: abilitato con TPM + PIN                               │
│ [ ] Windows Defender Credential Guard: abilitato                     │
└──────────────────────────────────────────────────────────────────────┘
```

```powershell
# Hardening del server CA — script di configurazione

# 1. Limitare chi può effettuare logon locale
# GPO: Computer Configuration → Windows Settings → Security Settings
# → Local Policies → User Rights Assignment
# → Allow log on locally: solo "PKI Administrators", "Local Administrator"

# 2. Disabilitare servizi non necessari sul CA server
$unnecessaryServices = @(
    "RemoteRegistry", "Browser", "SSDPSRV", "upnphost",
    "MapsBroker", "lfsvc", "XblGameSave", "DiagTrack"
)
$unnecessaryServices | ForEach-Object {
    $svc = Get-Service -Name $_ -ErrorAction SilentlyContinue
    if ($svc) {
        Stop-Service $_ -Force -ErrorAction SilentlyContinue
        Set-Service $_ -StartupType Disabled
        Write-Output "Disabilitato: $_"
    }
}

# 3. Configurare Windows Firewall per il CA server
# Permettere solo il traffico necessario
New-NetFirewallRule -DisplayName "CA - RPC Endpoint Mapper" `
    -Direction Inbound -Protocol TCP -LocalPort 135 -Action Allow
New-NetFirewallRule -DisplayName "CA - DCOM" `
    -Direction Inbound -Protocol TCP -LocalPort 49152-65535 -Action Allow
New-NetFirewallRule -DisplayName "CA - HTTP CDP" `
    -Direction Inbound -Protocol TCP -LocalPort 80 -Action Allow
New-NetFirewallRule -DisplayName "CA - HTTPS CES/CEP" `
    -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow

# 4. Abilitare audit avanzato
auditpol /set /subcategory:"Certification Services" /success:enable /failure:enable
auditpol /set /subcategory:"Other Object Access Events" /success:enable /failure:enable
```

### HSM (Hardware Security Module)

Per ambienti ad alta sicurezza, la chiave privata della CA viene protetta da un HSM.

| Soluzione HSM | Tipo | Certificazione | Uso tipico |
|--------------|------|---------------|------------|
| **Thales Luna Network HSM** | Network-attached | FIPS 140-2/3 Level 3 | Enterprise, governo |
| **Entrust nShield** | Network/PCIe | FIPS 140-2 Level 3, Common Criteria | Enterprise, finanza |
| **YubiHSM 2** | USB | FIPS 140-2 Level 3 | PMI, dev, Root CA offline |
| **Azure Dedicated HSM** | Cloud | FIPS 140-2 Level 3 | Hybrid cloud |
| **Azure Managed HSM** | Cloud-managed | FIPS 140-2 Level 3 | Cloud-native |
| **AWS CloudHSM** | Cloud | FIPS 140-2 Level 3 | AWS workloads |

```powershell
# Configurare AD CS per usare un HSM
# Il provider CSP/KSP dell'HSM deve essere installato prima di configurare la CA
# Esempio con provider generico:
Install-AdcsCertificationAuthority -CAType EnterpriseSubordinateCA `
    -CryptoProviderName "HSM Vendor CSP v1.0" `
    -KeyLength 4096 `
    -HashAlgorithmName SHA256 `
    -CACommonName "Contoso Enterprise CA" `
    -Force

# Verificare il provider CSP/KSP in uso dalla CA
certutil -store My "Contoso Enterprise CA"
# Cercare la riga "Provider = ..." per confermare che usa l'HSM
```

### Key Ceremony per la Root CA

La key ceremony è la procedura formalizzata per la generazione della coppia di chiavi della Root CA. È un requisito per conformità a standard come WebTrust, ETSI e per le CA pubblicamente trusted.

```
┌──────────────────────────────────────────────────────────────────┐
│               KEY CEREMONY — PROCEDURA SEMPLIFICATA              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. PREPARAZIONE                                                 │
│     • Sala sicura con accesso controllato (badge + registro)     │
│     • 2+ testimoni indipendenti presenti                         │
│     • Videocamera attiva (opzionale ma raccomandato)              │
│     • Hardware air-gapped (no NIC, no Wi-Fi, no USB non auth)    │
│     • HSM inizializzato e verificato                              │
│                                                                  │
│  2. GENERAZIONE CHIAVI                                           │
│     • Generare la coppia RSA 4096 / ECC P-384 sull'HSM           │
│     • Verificare l'entropia del generatore random dell'HSM       │
│     • Esportare SOLO la chiave pubblica (mai la privata)          │
│                                                                  │
│  3. CREAZIONE CERTIFICATO ROOT                                   │
│     • Self-sign del certificato Root CA                           │
│     • Validità: 20-25 anni                                       │
│     • Verificare il thumbprint e le estensioni                    │
│                                                                  │
│  4. BACKUP                                                       │
│     • Backup della chiave privata su N smart card/USB sicuri     │
│     • Distribuire i backup a M custodi (M-of-N threshold)        │
│     • Ciascun custode conserva il backup in cassaforte separata  │
│                                                                  │
│  5. DOCUMENTAZIONE                                               │
│     • Firmare il verbale con data, ora, partecipanti             │
│     • Registrare serial number, thumbprint, hash del certificato │
│     • Archiviare il verbale in modo sicuro e accessibile         │
│                                                                  │
│  6. SPEGNIMENTO                                                  │
│     • Spegnere la macchina Root CA                                │
│     • Riporla nel vault fisico                                   │
│     • Registrare lo spegnimento nel log                           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Separazione dei Ruoli (Role Separation)

Per conformità e sicurezza, i ruoli PKI devono essere separati:

| Ruolo | Responsabilità | Permessi |
|-------|---------------|----------|
| **CA Administrator** | Configurazione della CA, template, CDP/AIA | Manage CA |
| **Certificate Manager** | Approvazione/rifiuto richieste, revoca certificati | Manage Certificates |
| **Auditor** | Revisione dei log, compliance | Auditor (read-only su audit log) |
| **Backup Operator** | Backup del database CA e della chiave | Backup/Restore della CA |
| **Key Recovery Agent** | Recupero delle chiavi private archiviate | KRA certificate |

```powershell
# Abilitare la separazione dei ruoli sulla CA
certutil -setreg CA\RoleSeparationEnabled 1
Restart-Service certsvc

# Con role separation abilitata, un utente non può avere sia
# "Manage CA" che "Manage Certificates" sulla stessa CA.
# Questo implementa il principio della separazione dei compiti (SoD).

# Verificare lo stato
certutil -getreg CA\RoleSeparationEnabled
```

---

## Best Practices

**Automatizzare il monitoring dei certificati:** Implementare uno script schedulato che verifichi quotidianamente la scadenza di tutti i certificati attivi nel dominio, inclusi i certificati installati sui server (web server, Exchange, AD FS), i certificati CA della gerarchia e le CRL. Lo script deve generare alert automatici quando un certificato è a 30, 14 e 7 giorni dalla scadenza, con escalation progressiva e tempestiva al team di sicurezza. Integrare il monitoring con il sistema di ticketing aziendale per creare automaticamente ticket di rinnovo con priorità appropriata.

**Root CA offline:** La Root CA deve essere mantenuta offline e accesa solo per operazioni specifiche (rinnovamento certificato Subordinate CA, pubblicazione CRL). La chiave privata della Root CA è il singolo punto di fiducia dell'intera PKI.

**Gerarchia a due livelli:** Non usare una singola CA per tutto. La separazione Root/Issuing protegge la Root CA e permette di revocare e sostituire una Issuing CA senza invalidare l'intera PKI.

**Chiavi forti:** Root CA: RSA 4096-bit (o ECC P-384), validità 20 anni. Issuing CA: RSA 4096-bit, validità 10 anni. End-entity: RSA 2048-bit minimo (4096 raccomandato), validità 1-2 anni. SHA-256 come hash algorithm minimo.

**CRL e OCSP sempre raggiungibili:** I CDP (CRL Distribution Points) e l'OCSP devono essere raggiungibili da tutti i client, inclusi quelli esterni alla rete aziendale. Utilizzare URL HTTP pubblici oltre ai percorsi LDAP interni.

**Non esportare le chiavi private:** Configurare i template con "private key not exportable" per i certificati di autenticazione. Solo i certificati che necessitano di backup/migrazione (es. web server in cluster) dovrebbero permettere l'esportazione.

**Monitorare la scadenza:** Implementare monitoring automatizzato per i certificati in scadenza su tutti i server e servizi. Un certificato scaduto su un web server o un servizio critico causa downtime immediato.

**Backup della CA:** Eseguire backup regolari del database della CA, della chiave privata della CA e della configurazione. Senza il backup della chiave privata della CA, è impossibile ricostruire la PKI.

**Documentare tutto:** Mantenere una documentazione aggiornata della gerarchia PKI, dei template, delle CRL distribution points, dei permessi di enrollment e delle procedure operative (rinnovo CA, disaster recovery).

**Pianificare il rinnovo della CA con largo anticipo:** Il certificato della Issuing CA ha una validità tipica di 5-10 anni, ma il rinnovo deve essere pianificato mesi prima della scadenza. Un certificato CA scaduto impedisce l'emissione di nuovi certificati e invalida gradualmente tutti i certificati emessi man mano che vengono rinnovati. Creare reminder nel sistema di ticketing almeno 6 mesi prima della scadenza di ogni certificato CA.

**Implementare Certificate Transparency (CT) dove applicabile:** Per i certificati pubblici, Certificate Transparency fornisce un meccanismo di audit aperto che permette di rilevare certificati erroneamente emessi o malevoli. Monitorare i CT log per il proprio dominio utilizzando servizi come crt.sh o Google CT Search per identificare tempestivamente certificati non autorizzati.

**Configurare OCSP Stapling sui web server:** Invece di richiedere ai client di contattare direttamente il responder OCSP per verificare la revoca, il web server può includere (staple) la risposta OCSP nella propria risposta TLS. Questo migliora significativamente le prestazioni del TLS handshake e riduce il carico sul responder OCSP. In IIS, OCSP stapling è supportato nativamente da Windows Server 2012 e successivi, configurabile tramite il binding HTTPS del sito.

**Utilizzare Hardware Security Module (HSM) per le chiavi CA:** Per ambienti ad alta sicurezza, la chiave privata della CA deve essere protetta da un HSM (Hardware Security Module) certificato FIPS 140-2 Level 3 o superiore. L'HSM garantisce che la chiave privata non possa mai essere estratta dal dispositivo, proteggendola anche in caso di compromissione completa del sistema operativo della CA. Le soluzioni HSM più diffuse in ambito enterprise includono Thales Luna, nCipher nShield e Azure Dedicated HSM per ambienti hybrid cloud.

**Separare i ruoli della CA dall'infrastruttura applicativa:** La Issuing CA non dovrebbe mai ospitare altri ruoli o applicazioni. Dedicare un server dedicato (fisico o virtuale protetto) alla CA enterprise, con hardening specifico e rigoroso: disabilitare l'accesso RDP per gli utenti non autorizzati, limitare il login locale al gruppo dei PKI Administrator, abilitare l'audit completo di tutti gli accessi e le operazioni di emissione certificati.

---

## Troubleshooting

### Problema: Auto-Enrollment Non Funziona

**Sintomi**: I computer o gli utenti non ricevono automaticamente i certificati dal template configurato per l'auto-enrollment.

**Causa**: Permessi mancanti sul template (Read + Enroll + Autoenroll), GPO non applicata, template non pubblicato sulla CA, o il servizio Certificate Propagation non è in esecuzione.

**Soluzione**:

```powershell
# Verificare che il template sia pubblicato sulla CA
certutil -catemplates | Select-String "TemplateName"

# Verificare i permessi sul template
# certtmpl.msc → Template → Properties → Security
# Il gruppo target deve avere: Read, Enroll, Autoenroll

# Verificare la GPO
gpresult /H "C:\Temp\gpresult.html"
# Cercare: "Certificate Services Client - Auto-Enrollment" → Enabled

# Forzare un ciclo di auto-enrollment
certutil -pulse

# Verificare gli eventi di enrollment
Get-WinEvent -LogName "Application" -MaxEvents 50 |
    Where-Object { $_.ProviderName -eq "Microsoft-Windows-CertificateServicesClient-AutoEnrollment" } |
    Select-Object TimeCreated, Id, LevelDisplayName, Message | Format-Table -Wrap
```

### Problema: Errore "Certificate Chain Is Not Trusted"

**Sintomi**: Un client non si fida di un certificato emesso dalla CA enterprise. Browser mostra "NET::ERR_CERT_AUTHORITY_INVALID".

**Causa**: Il certificato della Root CA non è nel Trusted Root Certification Authorities store del client. Questo accade per client non uniti al dominio o quando la propagazione tramite GPO non ha funzionato.

**Soluzione**:

```powershell
# Verificare se il certificato Root è presente nello store
Get-ChildItem Cert:\LocalMachine\Root | Where-Object Subject -like "*Contoso Root*"

# Se mancante, importare manualmente
Import-Certificate -FilePath "C:\Certs\ContosoRootCA.cer" -CertStoreLocation Cert:\LocalMachine\Root

# Per client uniti al dominio, la distribuzione avviene via GPO:
# Computer Configuration → Policies → Windows Settings → Security Settings
#   → Public Key Policies → Trusted Root Certification Authorities
#   → Import → [certificato Root CA]

# Verificare la catena completa di un certificato
certutil -verify -urlfetch "C:\Certs\server.cer"
```

### Problema: CRL Scaduta — Certificati Rifiutati

**Sintomi**: I certificati validi vengono rifiutati perché la CRL è scaduta. Errore: "The revocation function was unable to check revocation because the revocation server was offline."

**Causa**: La CA non ha pubblicato una nuova CRL prima della scadenza della precedente. La Root CA offline potrebbe non essere stata accesa in tempo per pubblicare la CRL.

**Soluzione**:

```powershell
# Verificare la data di scadenza della CRL
certutil -URL "http://pki.contoso.com/CertEnroll/ContosoRootCA.crl"

# Sulla CA: pubblicare immediatamente una nuova CRL
certutil -CRL

# Per la Root CA offline:
# 1. Accendere la macchina Root CA
# 2. certutil -CRL
# 3. Copiare la CRL sui CDP configurati (web server, LDAP)
# 4. Verificare che la nuova CRL sia accessibile

# Pubblicare la CRL in AD (se il CDP include LDAP)
certutil -dspublish -f "C:\CRL\ContosoRootCA.crl" "Contoso Root CA"
```

### Tabella Troubleshooting Rapida — 15+ Problemi Comuni

| # | Problema | Causa probabile | Soluzione rapida |
|---|---------|----------------|------------------|
| 1 | Auto-enrollment non funziona | Permessi template mancanti (Read+Enroll+Autoenroll) | Verificare permessi template + `certutil -pulse` |
| 2 | "Certificate chain not trusted" | Root CA non nel Trusted Root store del client | Importare Root CA via GPO o manualmente |
| 3 | CRL scaduta — certificati rifiutati | CA non ha pubblicato CRL in tempo | `certutil -CRL` sulla CA, copiare CRL su CDP |
| 4 | "The RPC server is unavailable" durante enrollment | Servizio CA non raggiungibile (firewall, DNS, servizio fermo) | Verificare `certsvc` è running, firewall TCP 135 + porte dinamiche |
| 5 | Certificato emesso ma senza SAN | Template non configurato per SAN o EDITF flag mancante | Usare template con SAN configurato, NON abilitare EDITF_ATTRIBUTESUBJECTALTNAME2 |
| 6 | Errore "Template not found" durante enrollment | Template non pubblicato sulla CA o nome errato | `Add-CATemplate -Name "NomeTemplate"` |
| 7 | Certificato non appare dopo enrollment | Certificato emesso ma non installato nel cert store | `certreq -accept file.cer`, verificare pending requests |
| 8 | OCSP restituisce "Unauthorized" | Certificato di firma OCSP scaduto o permessi errati | Rinnovare il signing certificate dell'OCSP Responder |
| 9 | Smart card logon fallisce con "No valid certificates found" | NTAuthCertificates non contiene il cert della CA emittente | `certutil -dspublish -f IssuingCA.cer NTAuth` |
| 10 | Web Enrollment (certsrv) mostra errore 500 | AppPool identity non ha permessi o .NET non configurato | Riconfigurare AppPool, verificare `Install-AdcsWebEnrollment -Force` |
| 11 | Delta CRL non viene pubblicata | `CRLDeltaPeriod` impostato a 0 o problema di pubblicazione | Verificare `certutil -getreg CA\CRLDeltaPeriod`, configurare `Days` |
| 12 | Certificato con SHA-1 rifiutato dal browser | Template o CA usa SHA-1 (deprecato) | Aggiornare il template a SHA-256, ri-emettere |
| 13 | "Key not valid for use in specified state" all'esportazione | Chiave privata marcata come non esportabile | Ri-emettere con template che permette l'esportazione (se appropriato) |
| 14 | NDES restituisce "The SCEP request is invalid" | Challenge password scaduta o configurazione NDES errata | Verificare NDES config nel registry, rinnovare RA certificates |
| 15 | Errore "The revocation function was unable to check revocation for the certificate" | CDP irraggiungibile o CRL corrotta | Verificare raggiungibilità HTTP dei CDP: `certutil -URL <url>` |
| 16 | Certificato CA in scadenza: enrollment di nuovi certificati fallisce | Validità del cert CA < validità richiesta dal template | Rinnovare il certificato della CA PRIMA che scada |
| 17 | "Access denied" durante enrollment di un template | Utente/computer non ha Enroll permission sul template | Aggiungere il gruppo corretto con Enroll permission |
| 18 | Duplicate serial number nella CA database | Corruzione del database CA o restore errato | `certutil -verifykeys`, restore dal backup e verificare integrità |
| 19 | Certificato valido ma IIS mostra "This site is not secure" | Mismatch tra hostname e CN/SAN del certificato | Verificare che il SAN contenga il FQDN esatto del sito |
| 20 | CEP/CES enrollment fallisce con errore 403 | Autenticazione non configurata correttamente su IIS | Verificare auth mode (Username vs Certificate) su CEP/CES virtual directories |

---

## Esercizi

### Esercizio 1 — Progettazione PKI Two-Tier

**Obiettivo:** Progettare e documentare una gerarchia CA two-tier per un'organizzazione di 500 utenti con requisiti di 802.1X, S/MIME e web server TLS.

**Consegna:**
1. Diagramma della gerarchia (Root CA + Issuing CA) con specifiche crittografiche (algoritmo, lunghezza chiave, validità)
2. Elenco dei certificate templates necessari (almeno 5) con EKU, permessi e configurazione auto-enrollment
3. Schema dei CDP e AIA (LDAP + HTTP) con calcolo dell'overlap period
4. Piano di backup e rinnovo della CA (frequenze, procedure, responsabilità)

**Criteri di successo:** La documentazione deve essere sufficientemente dettagliata per implementare la PKI senza informazioni aggiuntive.

### Esercizio 2 — Audit AD CS con Certipy

**Obiettivo:** Eseguire un audit completo della configurazione AD CS in un ambiente lab e identificare i template vulnerabili (ESC1-ESC8).

**Procedura:**
1. Installare Certipy in un ambiente lab (Kali Linux o Python su Windows)
2. Eseguire `certipy find -vulnerable` contro il domain controller
3. Analizzare il report JSON e identificare ogni vulnerabilità trovata
4. Per ogni vulnerabilità: documentare il vettore di attacco, l'impatto e la mitigazione specifica
5. Applicare le mitigazioni e ri-eseguire lo scan per verificare la remediation

**Criteri di successo:** Zero vulnerabilità ESC1-ESC8 nello scan post-remediation.

### Esercizio 3 — Script di Monitoring Certificati

**Obiettivo:** Scrivere uno script PowerShell che monitora tutti i certificati in scadenza in un dominio AD e genera un report HTML.

**Requisiti:**
1. Lo script deve interrogare tutti i server Windows nel dominio (via `Get-ADComputer` + `Invoke-Command`)
2. Elencare i certificati in scadenza nei prossimi 60 giorni con: server, subject, issuer, data scadenza, giorni rimanenti, thumbprint
3. Generare un report HTML con colori (verde > 30gg, giallo 14-30gg, rosso < 14gg)
4. Opzionale: inviare il report via email al team PKI

**Criteri di successo:** Report HTML corretto con codifica colore e dati accurati.

### Esercizio 4 — Integrazione Let's Encrypt con IIS

**Obiettivo:** Configurare il rinnovo automatico di un certificato Let's Encrypt per un web server IIS pubblico usando Posh-ACME.

**Procedura:**
1. Installare il modulo Posh-ACME
2. Configurare l'account ACME con Let's Encrypt (staging per test)
3. Ottenere un certificato con HTTP-01 challenge
4. Importare il certificato nello store di IIS e configurare il binding HTTPS
5. Creare uno Scheduled Task che rinnova automaticamente il certificato ogni giorno (il rinnovo effettivo avviene solo quando necessario)
6. Configurare HSTS header sul sito

**Criteri di successo:** Il certificato viene rinnovato automaticamente senza intervento manuale, HSTS è configurato.

### Esercizio 5 — Key Ceremony Simulata

**Obiettivo:** Simulare una key ceremony per la Root CA in un ambiente lab, documentando ogni passaggio.

**Procedura:**
1. Preparare una VM air-gapped (nessuna NIC) con Windows Server
2. Documentare la procedura: data, ora, "testimoni" (simulati), hash dell'ambiente
3. Generare la coppia di chiavi RSA 4096 e il certificato Root CA self-signed
4. Esportare il certificato Root (senza chiave privata) su chiavetta USB
5. Esportare la chiave privata con password su una seconda chiavetta USB
6. Redigere un verbale della ceremony con: serial number, thumbprint, SHA-256 hash del certificato, validità
7. Spegnere la VM e annotare lo spegnimento

**Criteri di successo:** Verbale completo con tutte le informazioni richieste, chiave privata e certificato su media separati.

### Esercizio 6 — Migrazione CA con Cambio di OS

**Obiettivo:** Migrare una CA da Windows Server 2019 a Windows Server 2025 con validazione completa post-migrazione.

**Procedura:**
1. Installare una CA di test su una VM Windows Server 2019
2. Emettere almeno 5 certificati di test (web server, user, code signing)
3. Eseguire il backup completo (database, chiave privata, registry, template)
4. Installare Windows Server 2025 su una seconda VM con lo stesso hostname
5. Eseguire il restore del backup sulla nuova VM
6. Validare: servizio CA funzionante, tutti i certificati emessi visibili, enrollment di un nuovo certificato, CRL pubblicata, CDP raggiungibili

**Criteri di successo:** Zero certificati persi, enrollment funzionante, CRL valida post-migrazione.

---

## Auto-valutazione

<details>
<summary>1. Perché la Root CA deve essere mantenuta offline e quali rischi comporta se viene compromessa?</summary>

La Root CA è il singolo punto di fiducia (trust anchor) dell'intera PKI. Se la chiave privata della Root CA viene compromessa, un attaccante può:
- Emettere certificati per qualsiasi identità (inclusi certificati CA)
- Invalidare l'intera catena di fiducia — tutti i certificati emessi diventano potenzialmente non fidati
- La remediation richiede la sostituzione della Root CA e la ri-emissione di TUTTI i certificati nell'organizzazione

Mantenerla offline (air-gapped, in vault fisico) riduce drasticamente la superficie di attacco. Viene accesa solo per: (1) firmare/rinnovare certificati delle Subordinate CA, (2) pubblicare la CRL della Root CA. Tutte le altre operazioni avvengono tramite la Issuing CA.
</details>

<details>
<summary>2. Qual è la differenza tra CRL base, delta CRL e OCSP? Quando usare ciascuno?</summary>

- **Base CRL:** Lista completa di tutti i certificati revocati dalla CA. Scaricata integralmente dal client. Vantaggi: funziona offline (cachable), supporto universale. Svantaggi: può diventare grande (MB), aggiornamento non real-time.
- **Delta CRL:** Lista incrementale con le sole revoche dall'ultima base CRL. Riduce traffico e latenza. Vantaggi: download più piccolo, aggiornamento più frequente. Svantaggi: richiede comunque la base CRL.
- **OCSP:** Protocollo real-time: il client chiede lo stato di un singolo certificato e riceve risposta immediata. Vantaggi: risposta puntuale, bassa latenza. Svantaggi: richiede connettività, il server OCSP vede quali certificati vengono verificati (privacy).

Raccomandazione: usare OCSP per scenari real-time (802.1X, VPN, smart card) e CRL + delta CRL come fallback e per client che operano offline.
</details>

<details>
<summary>3. Cosa sono le vulnerabilità ESC1-ESC8 e quale è la più critica in ambienti enterprise?</summary>

Le vulnerabilità ESC1-ESC8 sono classi di misconfiguration in AD CS documentate nella ricerca "Certified Pre-Owned" (2021). Permettono l'escalation dei privilegi fino a Domain Admin.

**ESC1** (template con SAN controllabile + Enroll per low-priv user) è spesso considerata la più critica perché è estremamente comune, facilmente sfruttabile e permette di impersonare qualsiasi utente, incluso Domain Admin, con un singolo enrollment.

**ESC6** (EDITF_ATTRIBUTESUBJECTALTNAME2) è altrettanto pericolosa perché trasforma QUALSIASI template con Client Auth in un ESC1, indipendentemente dalla configurazione del template.

La mitigazione minima: disabilitare ESC6 (`certutil -setreg policy\EditFlags -EDITF_ATTRIBUTESUBJECTALTNAME2`), rimuovere "Supply in the request" o aggiungere approvazione del manager, limitare Enroll permissions.
</details>

<details>
<summary>4. Come si calcola il CRL Overlap Period e perché è importante?</summary>

Il CRL Overlap Period è il tempo durante il quale la vecchia CRL e la nuova CRL sono entrambe valide. Formula:

`Validità CRL = CRL Period + CRL Overlap Period`

Esempio: CRL Period = 7 giorni, Overlap = 3 giorni → la CRL è valida per 10 giorni totali. La CA pubblica una nuova CRL ogni 7 giorni, ma la vecchia rimane valida per altri 3 giorni. Questo dà ai client il tempo di scaricare la nuova CRL prima che la vecchia scada.

Se l'overlap è troppo corto e la CA ha un'interruzione temporanea, i client non riescono a scaricare la nuova CRL prima della scadenza della vecchia, causando il rifiuto di tutti i certificati. Raccomandazione: CRL Overlap >= 1/3 del CRL Period, minimo 1 giorno.
</details>

<details>
<summary>5. Qual è la differenza tra un certificato SAN e un certificato wildcard? Quale è più sicuro?</summary>

- **Certificato SAN:** Contiene una lista esplicita di nomi DNS nel campo Subject Alternative Name (es. `www.contoso.com`, `mail.contoso.com`, `portal.contoso.com`). Ogni nome è specificato individualmente.
- **Certificato Wildcard:** Usa un pattern `*.contoso.com` che copre tutti i sottodomini di primo livello. Non copre il naked domain (`contoso.com`) e non copre sotto-sottodomini (`sub.sub.contoso.com`).

**SAN è più sicuro:** se la chiave viene compromessa, solo i servizi elencati sono esposti. Con un wildcard, TUTTI i sottodomini sono esposti. Inoltre, un certificato wildcard condiviso tra molti servizi aumenta la superficie di distribuzione della chiave privata. Raccomandazione: usare SAN per servizi critici, wildcard solo per ambienti non critici o dev/staging.
</details>

<details>
<summary>6. Descrivere la procedura per migrare una CA su un nuovo server mantenendo la continuità del servizio.</summary>

1. **Backup completo** sul server originale: database CA (`Backup-CARoleService`), chiave privata (`certutil -backupkey`), configurazione registry (`reg export`), template pubblicati, file CRL/AIA.
2. **Verificare i backup** prima di procedere — un backup non testato non è un backup.
3. **Installare il ruolo AD CS** sul nuovo server (stesso hostname raccomandato). Non configurare — solo installare il ruolo.
4. **Ripristinare** database e chiave privata (`Restore-CARoleService`), importare il registry.
5. **Avviare il servizio** `certsvc` e verificare: `certutil -ping`, `certutil -catemplates`, `certutil -view`.
6. **Pubblicare una nuova CRL** (`certutil -CRL`) e verificare la raggiungibilità dei CDP.
7. **Testare l'enrollment** di un nuovo certificato.
8. Se l'hostname è diverso: aggiornare CDP/AIA o creare alias DNS dal vecchio hostname al nuovo.
</details>

<details>
<summary>7. Quale protocollo usa Let's Encrypt e perché non può sostituire una PKI interna?</summary>

Let's Encrypt usa il protocollo **ACME** (RFC 8555) per l'emissione automatizzata di certificati DV (Domain Validation). La validazione avviene tramite challenge HTTP-01 (file su web server) o DNS-01 (record TXT nel DNS).

**Non può sostituire una PKI interna perché:**
1. Emette solo certificati **DV** (Domain Validation) — non verifica l'identità dell'organizzazione
2. Non supporta EKU specifici come Smart Card Logon, Code Signing, S/MIME
3. Non supporta certificati per risorse interne (hostname non pubblici, IP privati)
4. Validità massima 90 giorni (progettata per il rinnovo automatico, non per tutti gli scenari)
5. Nessuna integrazione con AD per auto-enrollment, key archival, template management

L'approccio corretto è **hybrid PKI**: CA interna per autenticazione, S/MIME, code signing e risorse interne; Let's Encrypt per i certificati TLS dei servizi pubblici.
</details>

<details>
<summary>8. Quali Event ID monitorare sulla CA per rilevare attività sospette e possibili attacchi ESC?</summary>

Event ID critici per la sicurezza della CA:

- **4886** — Richiesta di certificato ricevuta: monitorare per volumi anomali o richieste da utenti insoliti
- **4887** — Certificato emesso: correlare con le richieste per identificare emissioni non autorizzate
- **4888** — Richiesta rifiutata: picchi di rifiuti possono indicare tentativi di abuse
- **4890** — Impostazioni template modificate: CRITICO — potrebbe indicare ESC4 (modifica template per renderlo vulnerabile)
- **4891** — Template aggiunto alla CA: CRITICO — un attaccante con ESC7 (Manage CA) può aggiungere un template vulnerabile
- **4899** — Template aggiornato: CRITICO — modifica non autorizzata del template
- **4900** — Security del template modificata: CRITICO — modifica ACL per ottenere Enroll permission

Alert immediato per: 4890, 4891, 4899, 4900 al di fuori delle finestre di manutenzione pianificate. Correlare 4886+4887 per identificare enrollment anomali (utente richiede certificato con SAN di un altro utente → possibile ESC1/ESC6).
</details>

<details>
<summary>9. Perché è importante usare un alias DNS (es. pki.contoso.com) nei CDP invece dell'hostname del server CA?</summary>

Se il CDP contiene l'hostname del server CA (es. `http://ca01.contoso.com/CertEnroll/CA.crl`), una migrazione della CA su un server con hostname diverso causerà l'invalidazione di tutti i certificati già emessi, perché i client non troveranno la CRL al vecchio URL.

Usando un alias DNS stabile (es. `pki.contoso.com`), in caso di migrazione basta aggiornare il record DNS per puntare al nuovo server. Tutti i certificati già emessi continueranno a trovare la CRL al solito URL. Questo vale anche per l'AIA (URL del certificato CA e dell'OCSP Responder).

Regola pratica: i CDP/AIA non devono mai contenere hostname legati a un server specifico, ma sempre alias funzionali che possono essere reindirizzati.
</details>

<details>
<summary>10. Qual è la differenza tra role separation e least privilege nella gestione della CA?</summary>

**Least privilege** significa che ogni account ha solo i permessi minimi necessari per svolgere il proprio compito. Ad esempio, un Certificate Manager ha solo "Manage Certificates" e non "Manage CA".

**Role separation** va oltre: impone che un singolo account non possa avere ruoli che creerebbero conflitti di interesse. Con `RoleSeparationEnabled=1` sulla CA, un utente non può avere contemporaneamente "Manage CA" (configurare la CA, aggiungere template) e "Manage Certificates" (approvare/rifiutare richieste). Questo impedisce che un singolo attore possa sia creare un template vulnerabile sia approvare una richiesta malevola su quel template.

Role separation implementa il principio di Separation of Duties (SoD), fondamentale per la compliance con standard come ISO 27001, SOC 2 e PCI DSS.
</details>

---

## Letture

- Microsoft Learn — AD CS Overview. https://learn.microsoft.com/en-us/windows-server/identity/ad-cs/active-directory-certificate-services-overview (consultato: 2026-05-23)
- Microsoft Learn — Certificate Template Concepts. https://learn.microsoft.com/en-us/windows-server/identity/ad-cs/certificate-template-concepts (consultato: 2026-05-23)
- Microsoft Learn — OCSP Installation and Configuration. https://learn.microsoft.com/en-us/windows-server/identity/ad-cs/online-responder-installation-configuration (consultato: 2026-05-23)
- Will Schroeder, Lee Christensen — Certified Pre-Owned: Abusing Active Directory Certificate Services. SpecterOps Whitepaper, giugno 2021. https://specterops.io/wp-content/uploads/sites/3/2022/06/Certified_Pre-Owned.pdf (consultato: 2026-05-23)
- RFC 5280 — Internet X.509 PKI Certificate and CRL Profile. https://tools.ietf.org/html/rfc5280 (consultato: 2026-05-23)
- RFC 6960 — Online Certificate Status Protocol (OCSP). https://tools.ietf.org/html/rfc6960 (consultato: 2026-05-23)
- RFC 8555 — Automatic Certificate Management Environment (ACME). https://tools.ietf.org/html/rfc8555 (consultato: 2026-05-23)
- RFC 4556 — PKINIT: Public Key Cryptography for Initial Authentication in Kerberos. https://tools.ietf.org/html/rfc4556 (consultato: 2026-05-23)
- NIST SP 800-57 Part 1 Rev. 5 — Recommendation for Key Management. https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final (consultato: 2026-05-23)
- Microsoft PKI Blog — Core Infrastructure and Security. https://techcommunity.microsoft.com/t5/core-infrastructure-and-security/bd-p/CoreInfrastructureandSecurity (consultato: 2026-05-23)
- Microsoft Learn — Key Archival and Recovery. https://learn.microsoft.com/en-us/windows-server/identity/ad-cs/key-archival-and-management (consultato: 2026-05-23)
- Microsoft Learn — CEP and CES Deployment Guide. https://learn.microsoft.com/en-us/windows-server/identity/ad-cs/certificate-enrollment-policy-web-service (consultato: 2026-05-23)
- Certipy — GitHub Repository. https://github.com/ly4k/Certipy (consultato: 2026-05-23)
- Posh-ACME — PowerShell ACME Client. https://github.com/rmbolger/Posh-ACME (consultato: 2026-05-23)
- RFC 6962 — Certificate Transparency. https://tools.ietf.org/html/rfc6962 (consultato: 2026-05-23)

---

## Collegamenti incrociati

| Modulo | Relazione |
|--------|-----------|
| [01 — Active Directory](01-active-directory.md) | AD è il fondamento della PKI enterprise: template in AD, NTAuthCertificates, GPO auto-enrollment |
| [02 — PowerShell](02-powershell.md) | Tutti gli script di gestione PKI utilizzano PowerShell; modulo PSPKI |
| [05 — Sicurezza Windows](05-sicurezza-windows.md) | PKI è il pilastro dell'autenticazione forte: smart card, 802.1X, BitLocker |
| [06 — Rete Windows](06-rete-windows.md) | 802.1X, VPN IKEv2, IPsec — tutti basati su certificati |
| [11 — Servizi Certificati](11-servizi-certificati.md) | Introduzione ai servizi certificati — questo modulo ne è l'approfondimento |
| [21 — Group Policy](21-group-policy-guida-completa.md) | Auto-enrollment configurato via GPO, distribuzione Root CA |
| [26 — Intune](26-intune-gestione-moderna.md) | Distribuzione certificati via SCEP/NDES per dispositivi gestiti |
| [29 — Windows Server Hardening](29-windows-server-hardening.md) | Hardening del server CA, disabilitazione protocolli legacy |
| [34 — Disaster Recovery AD + PKI](34-disaster-recovery-ad-pki.md) | Backup/restore della CA, recovery dopo compromissione |

---

## Glossario locale

| Termine | Definizione |
|---------|-------------|
| **PKI** | Public Key Infrastructure. Framework per la gestione dei certificati digitali: creazione, distribuzione, utilizzo, archiviazione e revoca. |
| **CA (Certification Authority)** | Entità che emette e firma certificati digitali. In ambiente Microsoft, implementata tramite AD CS. |
| **Root CA** | CA radice della gerarchia. Self-signed, trust anchor. Deve essere mantenuta offline per proteggere la chiave privata. |
| **Issuing CA** | CA subordinata che emette certificati per end-entity (utenti, computer, servizi). Online e integrata con AD. |
| **CSR (Certificate Signing Request)** | Richiesta formale di emissione certificato contenente Subject, chiave pubblica e firma del richiedente. Standard PKCS#10. |
| **CRL (Certificate Revocation List)** | Lista firmata dalla CA dei certificati revocati. I client la consultano per verificare lo stato di revoca. |
| **Delta CRL** | CRL incrementale con le sole revoche dall'ultima base CRL. Riduce il traffico di rete. |
| **CDP (CRL Distribution Point)** | URL (LDAP, HTTP, file) dove la CA pubblica le CRL. Incluso nei certificati come estensione X.509. |
| **AIA (Authority Information Access)** | Estensione X.509 che indica dove trovare il certificato della CA emittente e l'URL dell'OCSP Responder. |
| **OCSP** | Online Certificate Status Protocol (RFC 6960). Verifica real-time dello stato di revoca di un singolo certificato. |
| **EKU (Extended Key Usage)** | Estensione X.509 che specifica gli scopi per cui il certificato può essere usato (Server Auth, Client Auth, Code Signing, ecc.). |
| **SAN (Subject Alternative Name)** | Estensione X.509 che elenca nomi alternativi per il soggetto: DNS, IP, email, URI. Standard per la validazione del nome host. |
| **ACME** | Automatic Certificate Management Environment (RFC 8555). Protocollo per l'emissione automatizzata di certificati, usato da Let's Encrypt. |
| **PKINIT** | Public Key Cryptography for Initial Authentication in Kerberos (RFC 4556). Protocollo che estende Kerberos per supportare l'autenticazione con certificati X.509. |
| **HSM (Hardware Security Module)** | Dispositivo hardware certificato per la protezione delle chiavi crittografiche. Garantisce che la chiave privata non possa essere estratta. |
| **NDES** | Network Device Enrollment Service. Implementazione Microsoft del protocollo SCEP per l'enrollment di certificati da dispositivi di rete. |
| **CEP/CES** | Certificate Enrollment Policy / Service. Servizi HTTPS per l'enrollment di certificati da client non-domain-joined. |
| **NTAuthCertificates** | Oggetto AD nella partizione Configuration contenente i certificati delle CA autorizzate per autenticazione (smart card, EAP-TLS). |
| **ESC1-ESC8** | Otto classi di vulnerabilità AD CS documentate nella ricerca "Certified Pre-Owned" che permettono escalation di privilegi. |
| **Certificate Transparency (CT)** | Framework (RFC 6962) che richiede la registrazione di certificati pubblici in log verificabili per rilevare emissioni non autorizzate. |
| **HSTS** | HTTP Strict Transport Security. Header HTTP che forza i browser a connettersi sempre via HTTPS. |
| **Key Archival** | Funzionalità AD CS che archivia una copia della chiave privata dell'utente nella CA, permettendo il recovery in caso di perdita. |
| **Cross-Certification** | Meccanismo che permette a due PKI indipendenti di stabilire fiducia reciproca senza condividere una Root CA. |
| **Bridge CA** | CA che funge da hub di cross-certification tra multiple organizzazioni, riducendo la complessità delle relazioni di fiducia. |

---

## Riferimenti

- Microsoft Docs: AD CS Overview — https://learn.microsoft.com/en-us/windows-server/identity/ad-cs/active-directory-certificate-services-overview
- Microsoft Docs: Certificate Templates — https://learn.microsoft.com/en-us/windows-server/identity/ad-cs/certificate-template-concepts
- Microsoft Docs: OCSP — https://learn.microsoft.com/en-us/windows-server/identity/ad-cs/online-responder-installation-configuration
- RFC 5280: Internet X.509 PKI Certificate and CRL Profile — https://tools.ietf.org/html/rfc5280
- RFC 6960: OCSP — https://tools.ietf.org/html/rfc6960
- Microsoft PKI Blog — https://techcommunity.microsoft.com/t5/core-infrastructure-and-security/bd-p/CoreInfrastructureandSecurity
- NIST SP 800-57: Recommendation for Key Management — https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final
- Microsoft Docs: Key Archival and Recovery — https://learn.microsoft.com/en-us/windows-server/identity/ad-cs/key-archival-and-management
