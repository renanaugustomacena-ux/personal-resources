---
corso: "Programmazione Python"
fase: "6 — Sicurezza"
modulo: "18"
titolo: "Sicurezza in Python"
versione: "cryptography 44.x / bandit 1.8+ / pip-audit 2.x"
livello: "Intermedio-Avanzato"
prerequisiti:
  - "01-06 — Python Base"
  - "07 — Error Handling e Logging"
  - "11 — Web Framework"
obiettivi:
  - "Applicare crittografia simmetrica e asimmetrica con cryptography"
  - "Generare token e OTP sicuri con il modulo secrets"
  - "Generare e consumare SBOM in formato CycloneDX"
  - "Integrare bandit, pip-audit e detect-secrets nella CI/CD"
  - "Mappare OWASP Top 10 a pattern Python con mitigazioni concrete"
  - "Validare input con Pydantic, prevenire path traversal e injection"
  - "Comprendere PEP 458, Trusted Publishers e sigstore"
tag: [sicurezza, cryptography, bandit, OWASP, SBOM, supply-chain, secrets, pip-audit]
---

# Sicurezza in Python — Guida Completa

> **Modulo 18** · **Aggiornamento:** 2026-05-24 · **Versione:** cryptography 44.x / bandit 1.8+ / pip-audit 2.x

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Python Base](01-fondamenti-linguaggio.md), [Error Handling](07-error-handling-e-logging.md), [Web Framework](11-web-framework.md)
>
> Al termine di questo modulo saprai:
> 1. Applicare crittografia simmetrica e asimmetrica con la libreria `cryptography`
> 2. Utilizzare il modulo `secrets` per generazione crittograficamente sicura di token e OTP
> 3. Generare e consumare SBOM in formato CycloneDX per trasparenza della supply chain
> 4. Integrare `bandit`, `pip-audit`, `safety` e `detect-secrets` in pipeline CI/CD
> 5. Mappare la OWASP Top 10 a pattern Python concreti con mitigazioni testate
> 6. Validare input con Pydantic, prevenire path traversal e verificare upload di file
> 7. Comprendere PEP 458, Trusted Publishers e sigstore per distribuzione sicura
>
> **Tempo stimato:** 8-10 ore · **Livello:** Intermedio-Avanzato
8. Gestire segreti con env vars, python-dotenv, HashiCorp Vault e AWS Secrets Manager secondo il principio zero-trust.
9. Riconoscere e prevenire le insidie di `eval`/`exec`, `pickle`, `yaml.load` e template injection.
10. Effettuare dependency review (audit licenze, segnali di manutenzione, valutazione alternative) prima di adottare nuove dipendenze.


## Idee guida

1. **`secrets` > `random` per crypto-quality random.**
2. **`cryptography` library standard; mai roll-your-own.**
3. **`pip-audit` per CVE scan deps.**
4. **PEP 458/480: TUF for PyPI security.** Trusted Publishers.
5. **bandit static analyzer.** SAST per Python.
6. **SBOM con CycloneDX-py per trasparenza supply chain.**
7. **Dependency pinning con hash checking per build riproducibili.**
8. **Pydantic come security layer: validazione strutturale all'ingresso.**


## Mappa concettuale — Livelli di sicurezza Python

```
┌─────────────────────────────────────────────────────────────────┐
│                    LIVELLO APPLICAZIONE                         │
│  Input validation (Pydantic) · Output encoding · AuthN/AuthZ   │
│  CSRF/XSS/SQLi prevention · Secure deserialization             │
│  secrets module · cryptography lib · Argon2id hashing          │
├─────────────────────────────────────────────────────────────────┤
│                    LIVELLO DIPENDENZE                           │
│  pip-audit · safety · bandit (SAST) · detect-secrets           │
│  Dependency pinning (uv.lock / pip-compile --generate-hashes)  │
│  SBOM (CycloneDX) · License audit · Renovate/Dependabot       │
├─────────────────────────────────────────────────────────────────┤
│                    LIVELLO SUPPLY CHAIN                         │
│  PEP 458 (TUF per PyPI) · PEP 480 (key mgmt)                 │
│  Trusted Publishers (OIDC) · sigstore (Fulcio + Rekor)         │
│  --require-hashes · Mirror/proxy privati (Artifactory, Nexus)  │
├─────────────────────────────────────────────────────────────────┤
│                    LIVELLO RUNTIME                              │
│  TLS 1.2+ · Certificate verification · HSTS                   │
│  Least privilege (uid/gid drop) · Secure session config        │
│  Rate limiting · Security logging · Fail securely              │
├─────────────────────────────────────────────────────────────────┤
│                    LIVELLO OS / INFRASTRUTTURA                  │
│  File permissions (0o600) · Firewall / network segmentation    │
│  Secrets manager (Vault, AWS SM) · Container hardening         │
│  CI/CD security gates · Monitoring & alerting                  │
└─────────────────────────────────────────────────────────────────┘
```

Ogni livello difende indipendentemente; la compromissione di uno non deve compromettere gli altri (defense in depth).


## Indice

1. [Panoramica](#panoramica)
2. [Crittografia](#crittografia)
   - [hashlib — Hashing](#hashlib--hashing)
   - [secrets — Generazione Sicura](#secrets--generazione-sicura)
   - [cryptography library](#cryptography-library)
3. [Sicurezza Password](#sicurezza-password)
   - [bcrypt](#bcrypt)
   - [argon2-cffi](#argon2-cffi)
   - [Password Policy Enforcement](#password-policy-enforcement)
   - [Pattern Completo di Archiviazione Sicura](#pattern-completo-di-archiviazione-sicura)
4. [Sicurezza Web](#sicurezza-web)
   - [SQL Injection Prevention](#sql-injection-prevention)
   - [XSS Prevention](#xss-prevention)
   - [CSRF Protection](#csrf-protection)
   - [Input Validation e Sanitization](#input-validation-e-sanitization)
   - [Secure Headers](#secure-headers)
   - [CORS Configuration](#cors-configuration)
   - [Session Security](#session-security)
5. [Sicurezza Rete](#sicurezza-rete)
   - [TLS/SSL Configuration](#tlsssl-configuration)
   - [Certificate Verification](#certificate-verification)
   - [Certificate Pinning](#certificate-pinning)
   - [Secure HTTP Client Configuration](#secure-http-client-configuration)
   - [SSH Key Management](#ssh-key-management)
6. [Gestione Segreti](#gestione-segreti)
   - [Environment Variables](#environment-variables)
   - [Secret Management Systems](#secret-management-systems)
   - [keyring Library](#keyring-library)
   - [Non Committare Mai i Segreti](#non-committare-mai-i-segreti)
7. [Analisi Sicurezza Codice](#analisi-sicurezza-codice)
   - [Bandit](#bandit)
   - [Safety](#safety)
   - [pip-audit](#pip-audit)
8. [Dipendenze Sicure](#dipendenze-sicure)
   - [Pinning delle Versioni](#pinning-delle-versioni)
   - [Dependabot e Renovate](#dependabot-e-renovate)
   - [Vulnerability Scanning in CI/CD](#vulnerability-scanning-in-cicd)
   - [Supply Chain Security](#supply-chain-security)
9. [Secure Coding Patterns](#secure-coding-patterns)
   - [Input Validation](#input-validation)
   - [Output Encoding](#output-encoding)
   - [Principle of Least Privilege](#principle-of-least-privilege)
   - [Defense in Depth](#defense-in-depth)
   - [Fail Securely](#fail-securely)
   - [Logging Security Events](#logging-security-events)
   - [Secure Deserialization](#secure-deserialization)
10. [OWASP Top 10 per Python](#owasp-top-10-per-python)
11. [Best Practices](#best-practices)
12. [Cryptography Library — Approfondimento](#cryptography-library--approfondimento)
    - [Versioning e Policy EOL](#versioning-e-policy-eol)
    - [Fernet — Approfondimento](#fernet--approfondimento)
    - [Crittografia Asimmetrica — Curve Ellittiche](#crittografia-asimmetrica--curve-ellittiche)
    - [X.509 — Validazione Catena di Certificati](#x509--validazione-catena-di-certificati)
    - [Hazmat Layer — Regole di Ingaggio](#hazmat-layer--regole-di-ingaggio)
13. [Il Modulo secrets — Approfondimento](#il-modulo-secrets--approfondimento)
    - [secrets vs random — Quando Usare Quale](#secrets-vs-random--quando-usare-quale)
    - [Pattern Avanzati con secrets](#pattern-avanzati-con-secrets)
14. [SBOM — Software Bill of Materials](#sbom--software-bill-of-materials)
    - [CycloneDX-py](#cyclonedx-py)
    - [Formati SBOM: JSON e XML](#formati-sbom-json-e-xml)
    - [SBOM in CI/CD](#sbom-in-cicd)
15. [Supply Chain Security — Approfondimento](#supply-chain-security--approfondimento)
    - [PEP 458 — TUF per PyPI](#pep-458--tuf-per-pypi)
    - [PEP 480 — Gestione Chiavi per TUF](#pep-480--gestione-chiavi-per-tuf)
    - [Trusted Publishers (OIDC)](#trusted-publishers-oidc)
    - [Sigstore per Python](#sigstore-per-python)
16. [pip-audit — Approfondimento](#pip-audit--approfondimento)
    - [Strategie di Scansione Avanzata](#strategie-di-scansione-avanzata)
    - [Gestione Falsi Positivi](#gestione-falsi-positivi)
    - [pip-audit in CI/CD](#pip-audit-in-cicd)
17. [Dependency Pinning Avanzato](#dependency-pinning-avanzato)
    - [uv e uv.lock](#uv-e-uvlock)
    - [Hash Checking Mode](#hash-checking-mode)
    - [Build Riproducibili](#build-riproducibili)
18. [Bandit — Approfondimento](#bandit--approfondimento)
    - [Configurazione Avanzata](#configurazione-avanzata)
    - [Livelli di Severita e Confidenza](#livelli-di-severita-e-confidenza)
    - [Bandit in CI/CD con Quality Gate](#bandit-in-cicd-con-quality-gate)
    - [Gestione Falsi Positivi con nosec](#gestione-falsi-positivi-con-nosec)
19. [OWASP Top 10 — Mapping Python Dettagliato](#owasp-top-10--mapping-python-dettagliato)
20. [Validazione Input Avanzata](#validazione-input-avanzata)
    - [Pydantic come Security Layer](#pydantic-come-security-layer)
    - [Prevenzione Path Traversal](#prevenzione-path-traversal)
    - [Validazione File Upload](#validazione-file-upload)
21. [Gestione Segreti — Approfondimento](#gestione-segreti--approfondimento)
    - [Pattern con python-dotenv](#pattern-con-python-dotenv)
    - [HashiCorp Vault — Integrazione Completa](#hashicorp-vault--integrazione-completa)
    - [AWS Secrets Manager — Pattern di Rotazione](#aws-secrets-manager--pattern-di-rotazione)
22. [Secure Coding — Insidie Comuni](#secure-coding--insidie-comuni)
    - [eval e exec — Pericoli e Alternative](#eval-e-exec--pericoli-e-alternative)
    - [pickle — Deserializzazione Arbitraria](#pickle--deserializzazione-arbitraria)
    - [YAML safe_load vs load](#yaml-safe_load-vs-load)
    - [Template Injection (SSTI)](#template-injection-ssti)
23. [HTTP Security Headers — Middleware Completo](#http-security-headers--middleware-completo)
24. [Dependency Review](#dependency-review)
    - [Audit Licenze](#audit-licenze)
    - [Segnali di Manutenzione](#segnali-di-manutenzione)
    - [Valutazione Alternative](#valutazione-alternative)
25. [Troubleshooting](#troubleshooting)
26. [Esercizi](#esercizi)
27. [Letture e Riferimenti](#letture-e-riferimenti)
28. [Cross-link](#cross-link)
29. [Glossario](#glossario)

---

## Panoramica

La sicurezza e un pilastro fondamentale nello sviluppo software moderno. Ogni applicazione Python, sia essa un servizio web, uno script di automazione o un tool da riga di comando, deve essere progettata con la sicurezza come principio guida fin dall'inizio, non come un'aggiunta posteriore. Le conseguenze di una falla di sicurezza possono essere devastanti: perdita di dati sensibili, compromissione di sistemi, danni reputazionali e sanzioni legali.

Python offre un ecosistema ricco e maturo per implementare pratiche di sicurezza a ogni livello. La libreria standard include moduli come `hashlib`, `secrets`, `ssl` e `hmac`, mentre l'ecosistema di terze parti fornisce strumenti di livello professionale come `cryptography`, `bcrypt`, `argon2-cffi` e tool di analisi statica come `bandit`.

Questa guida copre l'intero spettro della sicurezza applicativa in Python: dalla crittografia e la gestione delle password, alla protezione delle applicazioni web, alla sicurezza di rete, alla gestione dei segreti, all'analisi del codice e alle best practice di secure coding. Ogni sezione include esempi pratici e completi, direttamente applicabili a progetti reali.

---

## Crittografia

La crittografia e la scienza che protegge le informazioni trasformandole in forme illeggibili per chi non possiede la chiave corretta. In Python possiamo operare a diversi livelli: hashing per l'integrita dei dati, generazione sicura di valori casuali, crittografia simmetrica e asimmetrica, e gestione dei certificati.

### hashlib — Hashing

Il modulo `hashlib` della libreria standard fornisce implementazioni di algoritmi di hashing crittografico. Un hash e una funzione unidirezionale: dato un input produce un output di lunghezza fissa (il digest), ma dall'output e computazionalmente impossibile risalire all'input originale.

```python
import hashlib

# --- Algoritmi di base ---

# MD5 (128 bit) — NON usare per sicurezza, solo per checksum rapidi
md5_hash = hashlib.md5(b"Dati da verificare").hexdigest()
print(f"MD5:     {md5_hash}")

# SHA-256 (256 bit) — standard raccomandato per uso generale
sha256_hash = hashlib.sha256(b"Dati da verificare").hexdigest()
print(f"SHA-256: {sha256_hash}")

# SHA-512 (512 bit) — per requisiti di sicurezza piu elevati
sha512_hash = hashlib.sha512(b"Dati da verificare").hexdigest()
print(f"SHA-512: {sha512_hash}")

# BLAKE2b (fino a 512 bit) — moderno, veloce, sicuro
blake2_hash = hashlib.blake2b(b"Dati da verificare").hexdigest()
print(f"BLAKE2b: {blake2_hash}")

# BLAKE2s (fino a 256 bit) — ottimizzato per piattaforme a 32 bit
blake2s_hash = hashlib.blake2s(b"Dati da verificare").hexdigest()
print(f"BLAKE2s: {blake2s_hash}")
```

**File hashing** — per verificare l'integrita di file di grandi dimensioni si legge il file a blocchi, evitando di caricarlo interamente in memoria:

```python
import hashlib
from pathlib import Path


def calcola_hash_file(percorso: str, algoritmo: str = "sha256",
                      dim_blocco: int = 8192) -> str:
    """Calcola l'hash di un file leggendolo a blocchi."""
    h = hashlib.new(algoritmo)
    with open(percorso, "rb") as f:
        while blocco := f.read(dim_blocco):
            h.update(blocco)
    return h.hexdigest()


# Uso
hash_file = calcola_hash_file("/percorso/al/file.zip")
print(f"SHA-256 del file: {hash_file}")

# Verifica integrita confrontando con hash atteso
hash_atteso = "a1b2c3d4e5f6..."
if hash_file == hash_atteso:
    print("File integro")
else:
    print("ATTENZIONE: il file potrebbe essere stato alterato!")
```

**Password hashing con PBKDF2 e scrypt** — per le password non si usa mai un hash semplice. Si utilizzano funzioni derivate appositamente progettate per essere lente e resistenti agli attacchi brute-force:

```python
import hashlib
import os


# --- PBKDF2 (Password-Based Key Derivation Function 2) ---
def hash_password_pbkdf2(password: str) -> tuple[bytes, bytes]:
    """Hash di una password con PBKDF2-HMAC-SHA256."""
    salt = os.urandom(32)  # 32 byte di sale casuale
    chiave = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations=600_000  # OWASP raccomanda >= 600.000 per SHA-256
    )
    return salt, chiave


def verifica_password_pbkdf2(password: str, salt: bytes,
                              chiave_attesa: bytes) -> bool:
    """Verifica una password contro hash PBKDF2 memorizzato."""
    chiave = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations=600_000
    )
    return hmac.compare_digest(chiave, chiave_attesa)


# --- scrypt ---
def hash_password_scrypt(password: str) -> tuple[bytes, bytes]:
    """Hash di una password con scrypt (memory-hard)."""
    salt = os.urandom(32)
    chiave = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**17,     # costo CPU/memoria (potenza di 2)
        r=8,         # dimensione blocco
        p=1,         # parallelismo
        dklen=64     # lunghezza chiave derivata
    )
    return salt, chiave


# Esempio d'uso
salt, chiave = hash_password_pbkdf2("MiaPasswordSegreta123!")
print(f"Salt:   {salt.hex()}")
print(f"Chiave: {chiave.hex()}")
```

### secrets — Generazione Sicura

Il modulo `secrets` (introdotto in Python 3.6) e progettato specificamente per generare valori casuali crittograficamente sicuri. A differenza del modulo `random` (che usa un PRNG deterministico e NON e sicuro), `secrets` utilizza il generatore di numeri casuali del sistema operativo.

```python
import secrets
import string


# --- Token generation ---
# Token esadecimale (32 byte = 64 caratteri hex)
token_hex = secrets.token_hex(32)
print(f"Token hex:   {token_hex}")

# Token in byte grezzi
token_bytes = secrets.token_bytes(32)
print(f"Token bytes: {token_bytes.hex()}")

# Token URL-safe (base64)
token_url = secrets.token_urlsafe(32)
print(f"Token URL:   {token_url}")


# --- Generazione di stringhe casuali ---
def genera_password_sicura(lunghezza: int = 16) -> str:
    """Genera una password casuale sicura con tutti i tipi di caratteri."""
    alfabeto = string.ascii_letters + string.digits + string.punctuation
    while True:
        password = "".join(secrets.choice(alfabeto) for _ in range(lunghezza))
        # Verifica che contenga almeno un carattere per tipo
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and any(c.isdigit() for c in password)
                and any(c in string.punctuation for c in password)):
            return password


password = genera_password_sicura(20)
print(f"Password generata: {password}")


# --- Generazione interi sicuri ---
# Intero casuale in un range (per OTP, codici di verifica)
codice_otp = secrets.randbelow(1_000_000)  # 0–999999
print(f"Codice OTP: {codice_otp:06d}")


# --- Confronto sicuro (timing-safe) ---
# MAI usare == per confrontare token/hash: e vulnerabile a timing attack
import hmac

token_ricevuto = "abc123"
token_memorizzato = "abc123"

# SBAGLIATO (vulnerabile a timing attack):
# if token_ricevuto == token_memorizzato:

# CORRETTO:
if hmac.compare_digest(token_ricevuto, token_memorizzato):
    print("Token valido")

# Oppure con secrets:
if secrets.compare_digest(token_ricevuto.encode(), token_memorizzato.encode()):
    print("Token valido (via secrets)")
```

### cryptography library

La libreria `cryptography` e lo standard de facto per la crittografia in Python. Fornisce sia primitive di alto livello (ricette sicure) sia accesso a operazioni di basso livello.

```bash
pip install cryptography
```

**Crittografia simmetrica con Fernet** — Fernet e una ricetta di alto livello che combina AES-128-CBC con HMAC-SHA256, gestendo automaticamente IV, padding e autenticazione:

```python
from cryptography.fernet import Fernet


# Generazione chiave (conservarla in modo sicuro!)
chiave = Fernet.generate_key()
print(f"Chiave Fernet: {chiave.decode()}")

# Crittografia
f = Fernet(chiave)
dati_originali = b"Dati sensibili da proteggere"
dati_cifrati = f.encrypt(dati_originali)
print(f"Cifrato: {dati_cifrati}")

# Decrittografia
dati_decifrati = f.decrypt(dati_cifrati)
print(f"Decifrato: {dati_decifrati.decode()}")
assert dati_decifrati == dati_originali

# Fernet con scadenza (token con TTL)
try:
    # Il token scade dopo 60 secondi
    dati = f.decrypt(dati_cifrati, ttl=60)
except Exception:
    print("Token scaduto o non valido")
```

**Crittografia simmetrica con AES (basso livello)** — per scenari che richiedono controllo diretto sull'algoritmo:

```python
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding


def aes_encrypt(chiave: bytes, dati: bytes) -> tuple[bytes, bytes]:
    """Cifra dati con AES-256-CBC."""
    iv = os.urandom(16)
    # Padding PKCS7
    padder = padding.PKCS7(128).padder()
    dati_padded = padder.update(dati) + padder.finalize()
    # Cifratura
    cipher = Cipher(algorithms.AES(chiave), modes.CBC(iv))
    encryptor = cipher.encryptor()
    cifrato = encryptor.update(dati_padded) + encryptor.finalize()
    return iv, cifrato


def aes_decrypt(chiave: bytes, iv: bytes, cifrato: bytes) -> bytes:
    """Decifra dati con AES-256-CBC."""
    cipher = Cipher(algorithms.AES(chiave), modes.CBC(iv))
    decryptor = cipher.decryptor()
    dati_padded = decryptor.update(cifrato) + decryptor.finalize()
    # Rimozione padding
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(dati_padded) + unpadder.finalize()


# Uso
chiave_aes = os.urandom(32)  # 256 bit
iv, cifrato = aes_encrypt(chiave_aes, b"Messaggio segreto AES-256")
decifrato = aes_decrypt(chiave_aes, iv, cifrato)
print(f"Decifrato: {decifrato.decode()}")
```

**Crittografia asimmetrica con RSA** — la crittografia a chiave pubblica permette di cifrare con una chiave pubblica e decifrare solo con la corrispondente chiave privata:

```python
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
from cryptography.hazmat.primitives import hashes, serialization


# --- Generazione coppia di chiavi RSA ---
chiave_privata = rsa.generate_private_key(
    public_exponent=65537,
    key_size=4096  # 2048 minimo, 4096 raccomandato
)
chiave_pubblica = chiave_privata.public_key()

# Serializzazione chiave privata (PEM, con password)
pem_privata = chiave_privata.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.BestAvailableEncryption(b"password-chiave")
)

# Serializzazione chiave pubblica
pem_pubblica = chiave_pubblica.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

print("Chiave pubblica generata con successo")


# --- Cifratura/Decifratura ---
messaggio = b"Messaggio cifrato con RSA"

cifrato = chiave_pubblica.encrypt(
    messaggio,
    asym_padding.OAEP(
        mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)

decifrato = chiave_privata.decrypt(
    cifrato,
    asym_padding.OAEP(
        mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)

print(f"Decifrato: {decifrato.decode()}")


# --- Firma digitale ---
from cryptography.hazmat.primitives.asymmetric import utils

dati_da_firmare = b"Documento da firmare digitalmente"

firma = chiave_privata.sign(
    dati_da_firmare,
    asym_padding.PSS(
        mgf=asym_padding.MGF1(hashes.SHA256()),
        salt_length=asym_padding.PSS.MAX_LENGTH
    ),
    hashes.SHA256()
)

# Verifica firma (chiunque puo farlo con la chiave pubblica)
try:
    chiave_pubblica.verify(
        firma,
        dati_da_firmare,
        asym_padding.PSS(
            mgf=asym_padding.MGF1(hashes.SHA256()),
            salt_length=asym_padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    print("Firma verificata con successo!")
except Exception:
    print("ATTENZIONE: firma non valida!")
```

**Certificati X.509** — i certificati digitali sono fondamentali per TLS/SSL. La libreria `cryptography` permette di caricarli, crearli e validarli:

```python
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
import datetime


# --- Caricamento di un certificato esistente ---
def carica_certificato(percorso: str) -> x509.Certificate:
    """Carica un certificato X.509 da file PEM."""
    with open(percorso, "rb") as f:
        return x509.load_pem_x509_certificate(f.read())


# --- Creazione di un certificato self-signed ---
def crea_certificato_selfsigned(
    nome_comune: str,
    organizzazione: str,
    giorni_validita: int = 365
) -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
    """Crea un certificato X.509 self-signed."""
    # Genera la chiave privata
    chiave = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096
    )

    # Costruisci il soggetto e l'emittente
    soggetto = emittente = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "IT"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Lombardia"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Milano"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, organizzazione),
        x509.NameAttribute(NameOID.COMMON_NAME, nome_comune),
    ])

    # Costruisci il certificato
    cert = (
        x509.CertificateBuilder()
        .subject_name(soggetto)
        .issuer_name(emittente)
        .public_key(chiave.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        .not_valid_after(
            datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(days=giorni_validita)
        )
        .add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(nome_comune),
                x509.DNSName(f"*.{nome_comune}"),
            ]),
            critical=False,
        )
        .sign(chiave, hashes.SHA256())
    )

    return chiave, cert


chiave, cert = crea_certificato_selfsigned("esempio.local", "MiaOrg Srl")
print(f"Soggetto: {cert.subject}")
print(f"Emittente: {cert.issuer}")
print(f"Valido dal: {cert.not_valid_before_utc}")
print(f"Valido fino al: {cert.not_valid_after_utc}")
print(f"Numero seriale: {cert.serial_number}")
```

**Key derivation** — le funzioni di derivazione chiave trasformano una password in una chiave crittografica adatta per la cifratura:

```python
import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives import hashes


# --- PBKDF2 ---
salt = os.urandom(16)
kdf_pbkdf2 = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=600_000
)
chiave_derivata = kdf_pbkdf2.derive(b"MiaPassword123!")
print(f"Chiave PBKDF2: {chiave_derivata.hex()}")

# Verifica (lancia eccezione se non corrisponde)
kdf_verifica = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,
    salt=salt,
    iterations=600_000
)
kdf_verifica.verify(b"MiaPassword123!", chiave_derivata)


# --- Scrypt ---
salt = os.urandom(16)
kdf_scrypt = Scrypt(
    salt=salt,
    length=32,
    n=2**17,
    r=8,
    p=1
)
chiave_scrypt = kdf_scrypt.derive(b"MiaPassword123!")
print(f"Chiave Scrypt: {chiave_scrypt.hex()}")
```

Per **Argon2**, attualmente il miglior algoritmo di key derivation disponibile, si utilizza la libreria dedicata `argon2-cffi`, trattata nella sezione successiva.

---

## Sicurezza Password

La gestione sicura delle password e uno degli aspetti piu critici di qualsiasi applicazione che gestisce autenticazione. Le password non devono mai essere memorizzate in chiaro: vanno sempre trasformate tramite funzioni di hashing appositamente progettate per essere lente e resistenti agli attacchi.

### bcrypt

`bcrypt` e una funzione di hashing per password progettata nel 1999, basata sull'algoritmo Blowfish. Include automaticamente il sale nel risultato e permette di regolare il fattore di costo (work factor) per aumentare la resistenza nel tempo.

```bash
pip install bcrypt
```

```python
import bcrypt


# --- Hashing di una password ---
password = "MiaPasswordSegreta123!"
password_bytes = password.encode("utf-8")

# Il sale viene generato automaticamente
# Il parametro rounds controlla la lentezza (default=12, raccomandato>=12)
hash_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=13))
print(f"Hash bcrypt: {hash_password.decode()}")
# Output: $2b$13$randomsalthere...hashedpasswordhere


# --- Verifica ---
if bcrypt.checkpw(password_bytes, hash_password):
    print("Password corretta")
else:
    print("Password errata")

# Tentativo con password sbagliata
if not bcrypt.checkpw(b"PasswordSbagliata", hash_password):
    print("Password errata (come atteso)")
```

### argon2-cffi

Argon2 e il vincitore della Password Hashing Competition (2015) ed e attualmente considerato il miglior algoritmo per l'hashing delle password. Offre tre varianti: Argon2d (resistente a GPU), Argon2i (resistente a side-channel), e Argon2id (ibrido, raccomandato).

```bash
pip install argon2-cffi
```

```python
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError


# --- Configurazione e hashing ---
ph = PasswordHasher(
    time_cost=3,       # numero di iterazioni
    memory_cost=65536,  # memoria in KiB (64 MB)
    parallelism=4,      # thread paralleli
    hash_len=32,        # lunghezza hash in byte
    salt_len=16,        # lunghezza sale in byte
    type=PasswordHasher.Type.ID  # Argon2id (raccomandato)
)

hash_argon2 = ph.hash("MiaPasswordSegreta123!")
print(f"Hash Argon2id: {hash_argon2}")
# Output: $argon2id$v=19$m=65536,t=3,p=4$salt$hash


# --- Verifica ---
try:
    ph.verify(hash_argon2, "MiaPasswordSegreta123!")
    print("Password corretta")

    # Controlla se l'hash necessita di rehash (parametri cambiati)
    if ph.check_needs_rehash(hash_argon2):
        print("L'hash va rigenerato con i nuovi parametri")
        nuovo_hash = ph.hash("MiaPasswordSegreta123!")
except VerifyMismatchError:
    print("Password errata")
```

### Password Policy Enforcement

Applicare politiche di complessita alle password e fondamentale per prevenire password deboli:

```python
import re
from dataclasses import dataclass


@dataclass
class RisultatoValidazione:
    valida: bool
    errori: list[str]


def valida_password(password: str) -> RisultatoValidazione:
    """Valida una password secondo le politiche di sicurezza."""
    errori = []

    if len(password) < 12:
        errori.append("La password deve avere almeno 12 caratteri")
    if len(password) > 128:
        errori.append("La password non puo superare 128 caratteri")
    if not re.search(r"[a-z]", password):
        errori.append("Deve contenere almeno una lettera minuscola")
    if not re.search(r"[A-Z]", password):
        errori.append("Deve contenere almeno una lettera maiuscola")
    if not re.search(r"\d", password):
        errori.append("Deve contenere almeno un numero")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errori.append("Deve contenere almeno un carattere speciale")

    # Controlla password comuni (in produzione usare un file completo)
    password_comuni = {
        "password123!", "admin123456", "qwerty123456",
        "letmein12345", "welcome12345"
    }
    if password.lower() in password_comuni:
        errori.append("Questa password e troppo comune")

    # Controlla sequenze ripetitive
    if re.search(r"(.)\1{3,}", password):
        errori.append("Non puo contenere piu di 3 caratteri consecutivi uguali")

    return RisultatoValidazione(valida=len(errori) == 0, errori=errori)


# Test
risultato = valida_password("Ab1!corta")
print(f"Valida: {risultato.valida}, Errori: {risultato.errori}")

risultato = valida_password("UnaPassword$icura2024!")
print(f"Valida: {risultato.valida}, Errori: {risultato.errori}")
```

### Pattern Completo di Archiviazione Sicura

Un pattern robusto e completo per la gestione delle password in un'applicazione:

```python
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, HashingError
import hmac
import secrets
import logging

logger = logging.getLogger(__name__)


class GestorePassword:
    """Gestore centralizzato per l'hashing e la verifica delle password."""

    def __init__(self):
        self._hasher = PasswordHasher(
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=32,
            salt_len=16
        )
        # Pepper: segreto globale dell'applicazione (da caricare da env/vault)
        self._pepper = self._carica_pepper()

    @staticmethod
    def _carica_pepper() -> bytes:
        """Carica il pepper da una fonte sicura."""
        import os
        pepper = os.environ.get("APP_PASSWORD_PEPPER", "")
        if not pepper:
            logger.warning("PASSWORD_PEPPER non configurato!")
            return b""
        return pepper.encode("utf-8")

    def _applica_pepper(self, password: str) -> str:
        """Applica il pepper alla password con HMAC."""
        if self._pepper:
            return hmac.new(
                self._pepper, password.encode("utf-8"), "sha256"
            ).hexdigest()
        return password

    def hash(self, password: str) -> str:
        """Genera l'hash sicuro di una password."""
        try:
            password_peppered = self._applica_pepper(password)
            return self._hasher.hash(password_peppered)
        except HashingError as e:
            logger.error(f"Errore durante l'hashing: {e}")
            raise

    def verifica(self, hash_memorizzato: str, password: str) -> bool:
        """Verifica una password contro il suo hash."""
        try:
            password_peppered = self._applica_pepper(password)
            return self._hasher.verify(hash_memorizzato, password_peppered)
        except VerifyMismatchError:
            return False
        except Exception as e:
            logger.error(f"Errore durante la verifica: {e}")
            return False

    def necessita_rehash(self, hash_memorizzato: str) -> bool:
        """Controlla se l'hash va rigenerato (parametri aggiornati)."""
        return self._hasher.check_needs_rehash(hash_memorizzato)


# Uso
gestore = GestorePassword()
hash_pwd = gestore.hash("LaMiaPassword$icura2024!")
print(f"Verifica: {gestore.verifica(hash_pwd, 'LaMiaPassword$icura2024!')}")
print(f"Rehash necessario: {gestore.necessita_rehash(hash_pwd)}")
```

---

## Sicurezza Web

Le applicazioni web sono il bersaglio principale degli attacchi informatici. Comprendere e mitigare le vulnerabilita web e essenziale per ogni sviluppatore Python che lavori con framework come Flask, Django o FastAPI.

### SQL Injection Prevention

La SQL injection e una delle vulnerabilita piu pericolose e diffuse. Si verifica quando input dell'utente viene concatenato direttamente nelle query SQL senza sanitizzazione.

```python
import sqlite3


# --- SBAGLIATO: vulnerabile a SQL injection ---
def cerca_utente_INSICURO(username: str):
    conn = sqlite3.connect("database.db")
    # MAI fare questo! L'input dell'utente e inserito direttamente nella query
    query = f"SELECT * FROM utenti WHERE username = '{username}'"
    return conn.execute(query).fetchall()
    # Input malevolo: ' OR '1'='1' --
    # Query risultante: SELECT * FROM utenti WHERE username = '' OR '1'='1' --'


# --- CORRETTO: query parametrizzate ---
def cerca_utente_SICURO(username: str):
    conn = sqlite3.connect("database.db")
    query = "SELECT * FROM utenti WHERE username = ?"
    return conn.execute(query, (username,)).fetchall()


# --- Con SQLAlchemy (ORM) ---
from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///database.db")

def cerca_utente_sqlalchemy(username: str):
    with engine.connect() as conn:
        # Parametri con bind sempre sicuri
        result = conn.execute(
            text("SELECT * FROM utenti WHERE username = :user"),
            {"user": username}
        )
        return result.fetchall()


# --- Con Django ORM (sempre sicuro per design) ---
# from myapp.models import Utente
# utente = Utente.objects.filter(username=username).first()
# Django parametrizza automaticamente tutte le query
```

### XSS Prevention

Il Cross-Site Scripting (XSS) permette a un attaccante di iniettare codice JavaScript malevolo nelle pagine web visualizzate da altri utenti.

```python
import html
from markupsafe import Markup, escape


# --- Escaping manuale ---
input_utente = '<script>alert("XSS!")</script>'
sicuro = html.escape(input_utente)
print(f"Escaped: {sicuro}")
# Output: &lt;script&gt;alert(&quot;XSS!&quot;)&lt;/script&gt;


# --- Con MarkupSafe (usato da Jinja2/Flask) ---
sicuro = escape(input_utente)
print(f"MarkupSafe: {sicuro}")


# --- Jinja2 auto-escaping (Flask lo abilita di default) ---
# In template Jinja2:
# {{ variabile }}         -> auto-escaped
# {{ variabile|safe }}    -> NON escaped (usare solo per HTML fidato!)


# --- Content-Security-Policy header ---
# Flask
from flask import Flask, make_response

app = Flask(__name__)

@app.after_request
def aggiungi_security_headers(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    return response
```

### CSRF Protection

Il Cross-Site Request Forgery forza un utente autenticato a eseguire azioni indesiderate su un'applicazione web.

```python
# --- Flask con Flask-WTF (protezione CSRF integrata) ---
from flask import Flask, render_template, request
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, SubmitField

app = Flask(__name__)
app.config["SECRET_KEY"] = "chiave-segreta-da-env"  # in produzione: da variabile ambiente
csrf = CSRFProtect(app)


class FormProfilo(FlaskForm):
    nome = StringField("Nome")
    submit = SubmitField("Aggiorna")


@app.route("/profilo", methods=["GET", "POST"])
def profilo():
    form = FormProfilo()
    if form.validate_on_submit():  # include verifica CSRF automatica
        # Aggiorna profilo...
        pass
    return render_template("profilo.html", form=form)


# Nel template HTML:
# <form method="POST">
#     {{ form.hidden_tag() }}  <!-- Include token CSRF -->
#     {{ form.nome.label }} {{ form.nome() }}
#     {{ form.submit() }}
# </form>


# --- Per API REST (token CSRF in header) ---
@app.route("/api/dati", methods=["POST"])
@csrf.exempt  # solo se l'API usa un altro meccanismo (es. JWT)
def api_dati():
    pass


# --- Django: CSRF abilitato di default ---
# In settings.py: MIDDLEWARE contiene 'django.middleware.csrf.CsrfViewMiddleware'
# Nel template: {% csrf_token %} dentro ogni <form>
```

### Input Validation e Sanitization

Ogni dato proveniente dall'utente deve essere considerato potenzialmente pericoloso e deve essere validato prima dell'uso:

```python
from pydantic import BaseModel, field_validator, EmailStr
import re
import bleach


# --- Validazione con Pydantic ---
class RegistrazioneUtente(BaseModel):
    username: str
    email: EmailStr
    eta: int

    @field_validator("username")
    @classmethod
    def valida_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]{3,30}$", v):
            raise ValueError(
                "Username: solo lettere, numeri e underscore, 3-30 caratteri"
            )
        return v.lower()

    @field_validator("eta")
    @classmethod
    def valida_eta(cls, v: int) -> int:
        if not 13 <= v <= 120:
            raise ValueError("Eta deve essere tra 13 e 120")
        return v


# Test
try:
    utente = RegistrazioneUtente(
        username="mario_rossi",
        email="mario@esempio.it",
        eta=30
    )
    print(f"Utente valido: {utente}")
except Exception as e:
    print(f"Validazione fallita: {e}")


# --- Sanitizzazione HTML con bleach ---
input_sporco = '<p>Testo ok</p><script>alert("XSS")</script><b>grassetto</b>'
pulito = bleach.clean(
    input_sporco,
    tags=["p", "b", "i", "em", "strong"],
    attributes={},
    strip=True
)
print(f"Sanitizzato: {pulito}")
# Output: <p>Testo ok</p>alert("XSS")<b>grassetto</b>
```

### Secure Headers

Gli header HTTP di sicurezza aggiungono livelli di protezione importanti contro diverse classi di attacchi:

```python
from flask import Flask

app = Flask(__name__)


@app.after_request
def security_headers(response):
    """Aggiunge header di sicurezza a ogni risposta."""
    # Forza HTTPS per tutti i futuri accessi (1 anno)
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains; preload"
    )
    # Impedisce il rendering in iframe (protezione clickjacking)
    response.headers["X-Frame-Options"] = "DENY"
    # Impedisce lo sniffing del MIME type
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Controlla il Referrer inviato nelle richieste
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Limita le funzionalita del browser
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), payment=()"
    )
    # Content Security Policy (gia visto sopra)
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    # Protezione XSS del browser (legacy, ma non fa male)
    response.headers["X-XSS-Protection"] = "1; mode=block"

    return response
```

### CORS Configuration

Il Cross-Origin Resource Sharing deve essere configurato attentamente per non esporre l'API a domini non autorizzati:

```python
# --- Flask-CORS ---
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)

# SBAGLIATO: permette qualsiasi origine
# CORS(app, origins="*")

# CORRETTO: solo origini specifiche
CORS(app, origins=[
    "https://www.miosito.it",
    "https://app.miosito.it"
], supports_credentials=True)


# --- FastAPI ---
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.miosito.it", "https://app.miosito.it"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=3600  # Cache preflight per 1 ora
)
```

### Session Security

La gestione sicura delle sessioni e critica per prevenire hijacking e fixation:

```python
from flask import Flask, session

app = Flask(__name__)

# Configurazione sicura delle sessioni
app.config.update(
    SECRET_KEY="chiave-generata-con-secrets-token-hex-64",
    SESSION_COOKIE_SECURE=True,       # solo HTTPS
    SESSION_COOKIE_HTTPONLY=True,      # non accessibile da JavaScript
    SESSION_COOKIE_SAMESITE="Lax",    # protezione CSRF parziale
    SESSION_COOKIE_NAME="__Host-session",  # prefisso __Host- per sicurezza extra
    PERMANENT_SESSION_LIFETIME=1800,  # 30 minuti
)


# --- Rigenerazione ID sessione dopo login ---
@app.route("/login", methods=["POST"])
def login():
    # Dopo autenticazione riuscita...
    session.clear()                    # elimina sessione precedente
    session.regenerate()               # nuovo ID sessione (Flask-Session)
    session["user_id"] = utente.id
    session["login_time"] = datetime.utcnow().isoformat()
    session.permanent = True
    return redirect("/dashboard")
```

---

## Sicurezza Rete

La sicurezza delle comunicazioni di rete e essenziale per proteggere i dati in transito. Python offre il modulo `ssl` nella libreria standard e diverse librerie di terze parti per configurazioni avanzate.

### TLS/SSL Configuration

```python
import ssl
import socket


# --- Creazione contesto SSL sicuro ---
def crea_contesto_ssl_client() -> ssl.SSLContext:
    """Crea un contesto SSL sicuro per connessioni client."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    # Versione minima TLS 1.2 (TLS 1.0 e 1.1 sono deprecati)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2

    # Cifrari sicuri (disabilita quelli deboli)
    ctx.set_ciphers(
        "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"
    )

    # Abilita verifica certificato e hostname
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED

    # Carica i certificati CA di sistema
    ctx.load_default_certs()

    return ctx


def crea_contesto_ssl_server(cert_file: str, key_file: str) -> ssl.SSLContext:
    """Crea un contesto SSL sicuro per un server."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(certfile=cert_file, keyfile=key_file)
    ctx.set_ciphers(
        "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"
    )
    return ctx


# Esempio: connessione sicura a un server
ctx = crea_contesto_ssl_client()
with socket.create_connection(("www.python.org", 443)) as sock:
    with ctx.wrap_socket(sock, server_hostname="www.python.org") as ssock:
        print(f"Protocollo: {ssock.version()}")
        print(f"Cifrario: {ssock.cipher()}")
        cert = ssock.getpeercert()
        print(f"Soggetto: {cert['subject']}")
```

### Certificate Verification

```python
import ssl
import socket
from datetime import datetime


def verifica_certificato(hostname: str, porta: int = 443) -> dict:
    """Verifica il certificato TLS di un server remoto."""
    ctx = ssl.create_default_context()

    with socket.create_connection((hostname, porta), timeout=10) as sock:
        with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
            cert = ssock.getpeercert()
            # Analisi dettagliata del certificato
            info = {
                "soggetto": dict(x[0] for x in cert["subject"]),
                "emittente": dict(x[0] for x in cert["issuer"]),
                "versione": cert["version"],
                "numero_seriale": cert["serialNumber"],
                "valido_da": cert["notBefore"],
                "valido_fino": cert["notAfter"],
                "san": [
                    entry[1]
                    for entry in cert.get("subjectAltName", [])
                ],
                "protocollo": ssock.version(),
                "cifrario": ssock.cipher()[0],
            }

            # Controlla se il certificato sta per scadere
            scadenza = datetime.strptime(
                cert["notAfter"], "%b %d %H:%M:%S %Y %Z"
            )
            giorni_rimasti = (scadenza - datetime.utcnow()).days
            info["giorni_alla_scadenza"] = giorni_rimasti

            if giorni_rimasti < 30:
                info["avviso"] = "ATTENZIONE: certificato in scadenza!"

            return info


info = verifica_certificato("www.python.org")
for chiave, valore in info.items():
    print(f"{chiave}: {valore}")
```

### Certificate Pinning

Il certificate pinning aggiunge un ulteriore livello di sicurezza verificando che il certificato del server corrisponda a un valore atteso:

```python
import hashlib
import ssl
import socket


def connetti_con_pinning(hostname: str, porta: int,
                          pin_sha256_atteso: str) -> bool:
    """Connette a un server verificando il pin del certificato."""
    ctx = ssl.create_default_context()

    with socket.create_connection((hostname, porta)) as sock:
        with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
            # Ottieni il certificato in formato DER
            cert_der = ssock.getpeercert(binary_form=True)
            # Calcola SHA-256 del certificato
            pin_effettivo = hashlib.sha256(cert_der).hexdigest()

            if pin_effettivo != pin_sha256_atteso:
                raise ssl.SSLError(
                    f"Certificate pinning fallito! "
                    f"Atteso: {pin_sha256_atteso}, "
                    f"Ricevuto: {pin_effettivo}"
                )
            print(f"Certificate pinning verificato per {hostname}")
            return True
```

### Secure HTTP Client Configuration

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context


class AdattatoreSSLSicuro(HTTPAdapter):
    """HTTP adapter con configurazione TLS sicura."""

    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.minimum_version = 0x0303  # TLS 1.2
        ctx.set_ciphers(
            "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:!aNULL:!MD5"
        )
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)


def crea_sessione_sicura() -> requests.Session:
    """Crea una sessione HTTP con configurazione sicura."""
    sessione = requests.Session()
    adattatore = AdattatoreSSLSicuro()
    sessione.mount("https://", adattatore)

    # Header di sicurezza predefiniti
    sessione.headers.update({
        "User-Agent": "MiaApp/1.0",
        "Accept": "application/json",
    })

    # Timeout globali (SEMPRE impostare i timeout!)
    sessione.timeout = (5, 30)  # (connect, read) in secondi

    return sessione


# Uso
sessione = crea_sessione_sicura()
risposta = sessione.get("https://api.esempio.it/dati", verify=True)
```

### SSH Key Management

```python
import paramiko
from pathlib import Path


def crea_coppia_chiavi_ssh(
    percorso: Path,
    tipo: str = "ed25519",
    passphrase: str | None = None
):
    """Genera una coppia di chiavi SSH."""
    if tipo == "ed25519":
        chiave = paramiko.Ed25519Key.generate()
    elif tipo == "rsa":
        chiave = paramiko.RSAKey.generate(4096)
    else:
        raise ValueError(f"Tipo chiave non supportato: {tipo}")

    # Salva chiave privata
    percorso_privata = percorso / f"id_{tipo}"
    chiave.write_private_key_file(
        str(percorso_privata),
        password=passphrase
    )
    percorso_privata.chmod(0o600)

    # Salva chiave pubblica
    percorso_pubblica = percorso / f"id_{tipo}.pub"
    with open(percorso_pubblica, "w") as f:
        f.write(f"{chiave.get_name()} {chiave.get_base64()}")
    percorso_pubblica.chmod(0o644)

    print(f"Chiavi generate in {percorso}")


def connessione_ssh_sicura(hostname: str, username: str,
                            chiave_privata: str):
    """Stabilisce una connessione SSH sicura."""
    client = paramiko.SSHClient()
    # In produzione: usare load_system_host_keys() o un file known_hosts
    # MAI usare AutoAddPolicy in produzione!
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.RejectPolicy())

    try:
        client.connect(
            hostname=hostname,
            username=username,
            key_filename=chiave_privata,
            timeout=10,
            allow_agent=False,
            look_for_keys=False
        )
        stdin, stdout, stderr = client.exec_command("whoami")
        print(f"Connesso come: {stdout.read().decode().strip()}")
    finally:
        client.close()
```

---

## Gestione Segreti

I segreti dell'applicazione (chiavi API, password database, token di accesso) devono essere gestiti con estrema cura. Non devono mai apparire nel codice sorgente o nei repository.

### Environment Variables

L'approccio piu semplice e usare variabili d'ambiente, gestite con `python-dotenv` per lo sviluppo locale:

```bash
pip install python-dotenv
```

```python
# --- File .env (MAI committare!) ---
# DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
# SECRET_KEY=abc123...
# API_KEY=sk-...

import os
from dotenv import load_dotenv
from pathlib import Path


# Carica le variabili dal file .env
load_dotenv(Path(__file__).parent / ".env")


class Configurazione:
    """Configurazione dell'applicazione da variabili d'ambiente."""

    def __init__(self):
        self.database_url = self._richiedi("DATABASE_URL")
        self.secret_key = self._richiedi("SECRET_KEY")
        self.api_key = self._richiedi("API_KEY")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.porta = int(os.getenv("PORT", "8000"))

    @staticmethod
    def _richiedi(nome: str) -> str:
        """Richiede una variabile d'ambiente obbligatoria."""
        valore = os.getenv(nome)
        if not valore:
            raise RuntimeError(
                f"Variabile d'ambiente obbligatoria mancante: {nome}"
            )
        return valore


config = Configurazione()
```

### Secret Management Systems

Per ambienti di produzione si utilizzano sistemi dedicati alla gestione dei segreti:

```python
# --- HashiCorp Vault ---
import hvac


def leggi_segreto_vault(percorso: str, chiave: str) -> str:
    """Legge un segreto da HashiCorp Vault."""
    client = hvac.Client(
        url=os.getenv("VAULT_ADDR", "https://vault.miosito.it:8200"),
        token=os.getenv("VAULT_TOKEN")
    )

    if not client.is_authenticated():
        raise RuntimeError("Autenticazione Vault fallita")

    segreto = client.secrets.kv.v2.read_secret_version(path=percorso)
    return segreto["data"]["data"][chiave]


# Uso
# db_password = leggi_segreto_vault("database/produzione", "password")


# --- AWS Secrets Manager ---
import boto3
import json


def leggi_segreto_aws(nome_segreto: str, regione: str = "eu-west-1") -> dict:
    """Legge un segreto da AWS Secrets Manager."""
    client = boto3.client("secretsmanager", region_name=regione)
    risposta = client.get_secret_value(SecretId=nome_segreto)

    if "SecretString" in risposta:
        return json.loads(risposta["SecretString"])
    raise ValueError(f"Segreto '{nome_segreto}' non trovato o non leggibile")


# Uso
# segreti_db = leggi_segreto_aws("produzione/database")
# connessione = crea_connessione(
#     host=segreti_db["host"],
#     password=segreti_db["password"]
# )
```

### keyring Library

La libreria `keyring` permette di memorizzare segreti nel portachiavi del sistema operativo (Keychain su macOS, Credential Manager su Windows, Secret Service su Linux):

```bash
pip install keyring
```

```python
import keyring


# Memorizza un segreto
keyring.set_password("mia-applicazione", "api_key", "sk-abc123xyz789")

# Recupera un segreto
api_key = keyring.get_password("mia-applicazione", "api_key")
print(f"API Key: {api_key}")

# Elimina un segreto
keyring.delete_password("mia-applicazione", "api_key")


# --- Wrapper per uso in applicazione ---
class SegretiLocali:
    """Gestione segreti tramite il portachiavi di sistema."""

    def __init__(self, nome_servizio: str):
        self._servizio = nome_servizio

    def leggi(self, chiave: str) -> str | None:
        return keyring.get_password(self._servizio, chiave)

    def scrivi(self, chiave: str, valore: str):
        keyring.set_password(self._servizio, chiave, valore)

    def elimina(self, chiave: str):
        try:
            keyring.delete_password(self._servizio, chiave)
        except keyring.errors.PasswordDeleteError:
            pass  # Chiave non esistente

    def richiedi(self, chiave: str) -> str:
        """Legge un segreto obbligatorio, solleva eccezione se mancante."""
        valore = self.leggi(chiave)
        if valore is None:
            raise KeyError(f"Segreto '{chiave}' non trovato nel portachiavi")
        return valore
```

### Non Committare Mai i Segreti

Prevenire che i segreti finiscano accidentalmente nel repository e fondamentale:

```gitignore
# --- .gitignore (sezione segreti) ---
.env
.env.*
*.pem
*.key
*.p12
*.pfx
credentials.json
service-account.json
secrets.yaml
secrets.yml
```

```yaml
# --- .pre-commit-config.yaml ---
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: package.lock.json
```

```bash
# Installazione e configurazione detect-secrets
pip install detect-secrets pre-commit

# Genera baseline (ignora i falsi positivi esistenti)
detect-secrets scan > .secrets.baseline

# Installa gli hook pre-commit
pre-commit install

# Scansione manuale
detect-secrets scan --all-files
detect-secrets audit .secrets.baseline
```

```python
# --- Script di verifica per CI/CD ---
import subprocess
import sys


def verifica_segreti_esposti():
    """Verifica che non ci siano segreti esposti nel repository."""
    risultato = subprocess.run(
        ["detect-secrets", "scan", "--all-files", "--force-use-all-plugins"],
        capture_output=True, text=True
    )

    import json
    report = json.loads(risultato.stdout)

    segreti_trovati = report.get("results", {})
    if segreti_trovati:
        print("ERRORE: Segreti potenziali trovati!")
        for file, dettagli in segreti_trovati.items():
            for segreto in dettagli:
                print(f"  {file}:{segreto['line_number']} - {segreto['type']}")
        sys.exit(1)
    else:
        print("Nessun segreto trovato.")


if __name__ == "__main__":
    verifica_segreti_esposti()
```

---

## Analisi Sicurezza Codice

L'analisi statica di sicurezza (SAST) permette di identificare vulnerabilita nel codice sorgente prima che raggiungano la produzione. Python offre diversi strumenti dedicati.

### Bandit

Bandit e lo strumento di analisi di sicurezza statica piu utilizzato per Python. Scansiona il codice alla ricerca di pattern noti che indicano vulnerabilita.

```bash
# Installazione
pip install bandit

# Scansione base
bandit -r percorso/al/progetto/

# Scansione con output dettagliato
bandit -r percorso/al/progetto/ -f json -o report_sicurezza.json

# Scansione con livello di confidenza minimo
bandit -r percorso/al/progetto/ -ll  # solo MEDIUM e HIGH

# Escludere test e venv
bandit -r percorso/al/progetto/ --exclude "*/test*,*/venv/*"

# Selezionare test specifici
bandit -r percorso/al/progetto/ -t B101,B102,B301
```

**Problemi comunemente rilevati da Bandit:**

```python
# B101: assert usato per logica (rimosso in ottimizzazione)
assert utente.e_admin  # Bandit avvisa: assert non e un controllo di sicurezza

# B301: uso di pickle (deserializzazione insicura)
import pickle
dati = pickle.loads(dati_non_fidati)  # Bandit avvisa: rischio esecuzione codice

# B303: uso di MD5/SHA1 per sicurezza
import hashlib
h = hashlib.md5(password.encode())  # Bandit avvisa: hash debole

# B602: subprocess con shell=True
import subprocess
subprocess.call(comando, shell=True)  # Bandit avvisa: shell injection

# B105: password hardcoded
password = "admin123"  # Bandit avvisa: possibile password nel codice

# B108: /tmp hardcoded (race condition)
with open("/tmp/dati.txt", "w") as f:  # Bandit avvisa: usare tempfile
    f.write(dati)
```

**File di configurazione Bandit** (`.bandit`):

```ini
[bandit]
exclude = tests,venv,.venv
skips = B101
targets = src
```

**Baseline file** — per gestire i falsi positivi in un progetto esistente:

```bash
# Genera baseline con i problemi attuali
bandit -r src/ -f json -o .bandit-baseline.json

# Scansione successiva: mostra solo nuovi problemi
bandit -r src/ -b .bandit-baseline.json
```

### Safety

Safety verifica le dipendenze Python installate contro un database di vulnerabilita note (CVE):

```bash
# Installazione
pip install safety

# Verifica delle dipendenze installate
safety check

# Verifica da un file requirements
safety check -r requirements.txt

# Output in formato JSON per CI/CD
safety check --json --output report_vulnerabilita.json

# Con chiave API per database completo (gratuito per open source)
safety check --key $SAFETY_API_KEY
```

**Integrazione in CI/CD (GitHub Actions):**

```yaml
# .github/workflows/security.yml
name: Security Check
on: [push, pull_request]

jobs:
  safety-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: pip install safety
      - run: safety check --full-report
```

### pip-audit

`pip-audit` e uno strumento di Google/PyPI che verifica le dipendenze installate contro il database di vulnerabilita di PyPI e l'OSV (Open Source Vulnerabilities):

```bash
# Installazione
pip install pip-audit

# Audit dell'ambiente corrente
pip-audit

# Audit da un file requirements
pip-audit -r requirements.txt

# Formato JSON per automazione
pip-audit -f json -o audit_results.json

# Fix automatico (aggiorna alla versione senza vulnerabilita)
pip-audit --fix

# Audit specifico per una fonte di dati
pip-audit --vulnerability-service osv
```

```python
# --- Script di audit automatizzato ---
import subprocess
import json
import sys


def esegui_audit_dipendenze() -> list[dict]:
    """Esegue pip-audit e restituisce le vulnerabilita trovate."""
    risultato = subprocess.run(
        ["pip-audit", "-f", "json", "--progress-spinner=off"],
        capture_output=True, text=True
    )

    vulnerabilita = json.loads(risultato.stdout)
    critiche = [
        v for v in vulnerabilita
        if v.get("fix_versions")  # ha una versione corretta disponibile
    ]

    if critiche:
        print(f"Trovate {len(critiche)} vulnerabilita con fix disponibile:")
        for v in critiche:
            print(f"  {v['name']} {v['version']}: {v['id']}")
            print(f"    Fix: {', '.join(v['fix_versions'])}")
        sys.exit(1)

    print("Nessuna vulnerabilita trovata.")
    return []


if __name__ == "__main__":
    esegui_audit_dipendenze()
```

---

## Dipendenze Sicure

La gestione sicura delle dipendenze e un aspetto critico della supply chain security. Una singola dipendenza compromessa puo mettere a rischio l'intera applicazione.

### Pinning delle Versioni

Fissare le versioni delle dipendenze garantisce build riproducibili e previene l'introduzione automatica di versioni compromesse:

```txt
# requirements.txt — versioni esatte (pin completo)
Flask==3.1.0
SQLAlchemy==2.0.36
requests==2.32.3
cryptography==44.0.0
```

```toml
# pyproject.toml con Poetry — lock file garantisce riproducibilita
[tool.poetry.dependencies]
python = "^3.11"
flask = "^3.1.0"
sqlalchemy = "^2.0.36"
requests = "^2.32.3"
```

```bash
# Genera requirements con hash per verifica integrita
pip install pip-tools
pip-compile --generate-hashes requirements.in > requirements.txt

# Il risultato include hash SHA-256:
# Flask==3.1.0 \
#     --hash=sha256:abc123... \
#     --hash=sha256:def456...
```

### Dependabot e Renovate

Strumenti automatici per mantenere le dipendenze aggiornate:

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: pip
    directory: "/"
    schedule:
      interval: weekly
      day: monday
    open-pull-requests-limit: 10
    reviewers:
      - "team-sicurezza"
    labels:
      - "dipendenze"
      - "sicurezza"
    # Raggruppa aggiornamenti minori
    groups:
      production-dependencies:
        patterns:
          - "*"
        update-types:
          - "minor"
          - "patch"
```

```json5
// renovate.json (alternativa a Dependabot)
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "config:recommended",
    "security:openssf-scorecard",
    ":pinAllExceptPeerDependencies"
  ],
  "packageRules": [
    {
      "matchUpdateTypes": ["patch"],
      "automerge": true,
      "automergeType": "branch"
    }
  ],
  "vulnerabilityAlerts": {
    "enabled": true,
    "labels": ["security"]
  }
}
```

### Vulnerability Scanning in CI/CD

```yaml
# .github/workflows/security-scan.yml
name: Security Scan

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: "0 8 * * 1"  # ogni lunedi alle 8:00

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Installa dipendenze
        run: pip install -r requirements.txt

      - name: pip-audit
        run: |
          pip install pip-audit
          pip-audit --strict

      - name: Bandit
        run: |
          pip install bandit
          bandit -r src/ -ll -f json -o bandit-report.json
        continue-on-error: false

      - name: Safety
        run: |
          pip install safety
          safety check --full-report

      - name: Carica report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: security-reports
          path: |
            bandit-report.json
```

### Supply Chain Security

La sicurezza della supply chain protegge contro dipendenze malevole o compromesse:

```python
# --- Verifica integrita dei pacchetti ---
# Installa solo da PyPI ufficiale con hash verificati
# pip install --require-hashes -r requirements.txt

# --- Analisi del pacchetto prima dell'installazione ---
import subprocess
import json


def analizza_pacchetto(nome: str) -> dict:
    """Raccoglie informazioni di sicurezza su un pacchetto PyPI."""
    # Informazioni dal registro PyPI
    import requests
    risposta = requests.get(f"https://pypi.org/pypi/{nome}/json", timeout=10)
    if risposta.status_code != 200:
        return {"errore": f"Pacchetto '{nome}' non trovato"}

    info = risposta.json()["info"]
    return {
        "nome": info["name"],
        "versione": info["version"],
        "autore": info["author"],
        "licenza": info["license"],
        "homepage": info["home_page"],
        "richiede_python": info["requires_python"],
        "data_rilascio": info.get("release_url", "N/D"),
    }


# Principi di supply chain security:
# 1. Usare sempre --require-hashes in produzione
# 2. Verificare l'autore e la reputazione prima di aggiungere dipendenze
# 3. Minimizzare il numero di dipendenze
# 4. Usare un mirror/proxy privato (es. Artifactory, Nexus)
# 5. Abilitare audit automatici in CI/CD
# 6. Monitorare CVE per le dipendenze in uso
```

---

## Secure Coding Patterns

I pattern di codifica sicura sono principi fondamentali che guidano lo sviluppo di software resistente agli attacchi. Applicarli sistematicamente riduce drasticamente la superficie di attacco.

### Input Validation

La regola d'oro: **mai fidarsi dell'input**. Ogni dato proveniente dall'esterno deve essere validato, sia esso da un utente, un'API esterna, un file o un database.

```python
from typing import Any
import re


def valida_email(email: str) -> str:
    """Valida un indirizzo email con regex rigorosa."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email) or len(email) > 254:
        raise ValueError(f"Email non valida: {email}")
    return email.lower()


def valida_intero_nel_range(valore: Any, minimo: int, massimo: int,
                             nome: str = "valore") -> int:
    """Valida che un valore sia un intero nel range specificato."""
    try:
        n = int(valore)
    except (TypeError, ValueError):
        raise ValueError(f"{nome} deve essere un intero")
    if not minimo <= n <= massimo:
        raise ValueError(f"{nome} deve essere tra {minimo} e {massimo}")
    return n


def valida_percorso_file(percorso: str, directory_base: str) -> str:
    """Valida un percorso file prevenendo path traversal."""
    from pathlib import Path
    percorso_risolto = Path(directory_base, percorso).resolve()
    base_risolta = Path(directory_base).resolve()
    if not str(percorso_risolto).startswith(str(base_risolta)):
        raise ValueError("Tentativo di path traversal rilevato")
    return str(percorso_risolto)
```

### Output Encoding

L'output deve essere codificato in base al contesto di destinazione per prevenire attacchi injection:

```python
import html
import json
import urllib.parse


def output_html(testo: str) -> str:
    """Codifica testo per inserimento in HTML."""
    return html.escape(testo, quote=True)


def output_url(parametro: str) -> str:
    """Codifica un parametro per inserimento in URL."""
    return urllib.parse.quote(parametro, safe="")


def output_json(dati: Any) -> str:
    """Serializza dati per inserimento in contesto JSON."""
    return json.dumps(dati, ensure_ascii=True)


# Esempio d'uso in un template
nome_utente = '<script>alert("XSS")</script>'
print(f"HTML: {output_html(nome_utente)}")
print(f"URL:  {output_url(nome_utente)}")
print(f"JSON: {output_json(nome_utente)}")
```

### Principle of Least Privilege

Ogni componente del sistema deve avere solo i permessi strettamente necessari per svolgere la propria funzione:

```python
import os
from pathlib import Path


# --- Permessi file minimi ---
def crea_file_segreto(percorso: str, contenuto: str):
    """Crea un file con permessi restrittivi (solo proprietario)."""
    path = Path(percorso)
    path.write_text(contenuto)
    path.chmod(0o600)  # rw------- (solo proprietario)


# --- Drop dei privilegi (per demoni/servizi) ---
def riduci_privilegi(uid: int, gid: int):
    """Riduce i privilegi del processo corrente (richiede root)."""
    if os.getuid() == 0:
        os.setgroups([])      # rimuove gruppi supplementari
        os.setgid(gid)        # imposta il gruppo
        os.setuid(uid)        # imposta l'utente (irreversibile!)
        os.umask(0o077)       # file creati: solo proprietario


# --- Connessione database con permessi minimi ---
# Utente database con permessi limitati per ogni servizio:
# CREATE USER app_reader WITH PASSWORD '...' LOGIN;
# GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_reader;
#
# CREATE USER app_writer WITH PASSWORD '...' LOGIN;
# GRANT SELECT, INSERT, UPDATE ON specific_table TO app_writer;
```

### Defense in Depth

La difesa in profondita applica molteplici livelli di sicurezza, in modo che il fallimento di un livello non comprometta l'intero sistema:

```python
from functools import wraps
from flask import Flask, request, abort, session
import time

app = Flask(__name__)


# Livello 1: Rate limiting
richieste_per_ip: dict[str, list[float]] = {}

def rate_limit(max_richieste: int = 100, finestra: int = 3600):
    """Limita il numero di richieste per IP."""
    def decoratore(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            ip = request.remote_addr
            ora = time.time()
            if ip not in richieste_per_ip:
                richieste_per_ip[ip] = []
            richieste_per_ip[ip] = [
                t for t in richieste_per_ip[ip] if ora - t < finestra
            ]
            if len(richieste_per_ip[ip]) >= max_richieste:
                abort(429, "Troppe richieste")
            richieste_per_ip[ip].append(ora)
            return f(*args, **kwargs)
        return wrapper
    return decoratore


# Livello 2: Autenticazione
def richiedi_autenticazione(f):
    """Verifica che l'utente sia autenticato."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            abort(401, "Autenticazione richiesta")
        return f(*args, **kwargs)
    return wrapper


# Livello 3: Autorizzazione
def richiedi_ruolo(ruolo: str):
    """Verifica che l'utente abbia il ruolo richiesto."""
    def decoratore(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if session.get("ruolo") != ruolo:
                abort(403, "Permesso negato")
            return f(*args, **kwargs)
        return wrapper
    return decoratore


# Applicazione di tutti i livelli
@app.route("/admin/utenti", methods=["DELETE"])
@rate_limit(max_richieste=10, finestra=60)
@richiedi_autenticazione
@richiedi_ruolo("admin")
def elimina_utente():
    # Livello 4: Validazione input
    user_id = request.json.get("user_id")
    if not isinstance(user_id, int) or user_id < 1:
        abort(400, "ID utente non valido")
    # Livello 5: Query parametrizzata (prevenzione SQL injection)
    # Livello 6: Audit logging
    return {"status": "ok"}
```

### Fail Securely

Quando un'operazione fallisce, il sistema deve rimanere in uno stato sicuro. Gli errori non devono mai rivelare informazioni sensibili:

```python
import logging
from flask import Flask, jsonify

app = Flask(__name__)
logger = logging.getLogger(__name__)


# --- SBAGLIATO: espone dettagli interni ---
@app.errorhandler(500)
def errore_INSICURO(e):
    return {"errore": str(e), "traceback": traceback.format_exc()}, 500


# --- CORRETTO: messaggio generico, dettagli nel log ---
@app.errorhandler(500)
def errore_SICURO(e):
    logger.exception("Errore interno del server")  # dettagli solo nel log
    return jsonify({
        "errore": "Si e verificato un errore interno",
        "codice": "ERRORE_INTERNO"
    }), 500


@app.errorhandler(404)
def non_trovato(e):
    return jsonify({"errore": "Risorsa non trovata"}), 404


@app.errorhandler(401)
def non_autorizzato(e):
    # NON rivelare se l'utente esiste o meno
    return jsonify({"errore": "Credenziali non valide"}), 401


# --- Pattern di login sicuro ---
def login(username: str, password: str) -> bool:
    """Login che non rivela informazioni sull'esistenza dell'utente."""
    utente = cerca_utente(username)

    if utente is None:
        # Esegui comunque l'hash per prevenire timing attack
        from argon2 import PasswordHasher
        ph = PasswordHasher()
        try:
            ph.verify("$argon2id$v=19$m=65536,t=3,p=4$fake$fake", password)
        except Exception:
            pass
        return False

    return gestore_password.verifica(utente.hash_password, password)
```

### Logging Security Events

Il logging degli eventi di sicurezza e fondamentale per il rilevamento e l'analisi degli incidenti, ma non deve mai includere dati sensibili:

```python
import logging
import json
from datetime import datetime


class SecurityLogger:
    """Logger specializzato per eventi di sicurezza."""

    def __init__(self, nome: str = "security"):
        self._logger = logging.getLogger(nome)
        handler = logging.FileHandler("security.log")
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s"
        ))
        self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)

    def _log(self, livello: str, evento: str, **dettagli):
        messaggio = json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "evento": evento,
            **dettagli
        })
        getattr(self._logger, livello)(messaggio)

    def login_riuscito(self, username: str, ip: str):
        self._log("info", "LOGIN_SUCCESS", username=username, ip=ip)

    def login_fallito(self, username: str, ip: str):
        # MAI loggare la password tentata!
        self._log("warning", "LOGIN_FAILED", username=username, ip=ip)

    def accesso_negato(self, username: str, risorsa: str, ip: str):
        self._log("warning", "ACCESS_DENIED",
                  username=username, risorsa=risorsa, ip=ip)

    def modifica_permessi(self, admin: str, utente_target: str,
                          vecchio_ruolo: str, nuovo_ruolo: str):
        self._log("info", "PERMISSION_CHANGE",
                  admin=admin, target=utente_target,
                  vecchio_ruolo=vecchio_ruolo, nuovo_ruolo=nuovo_ruolo)

    def sospetta_intrusione(self, ip: str, dettaglio: str):
        self._log("critical", "SUSPECTED_INTRUSION",
                  ip=ip, dettaglio=dettaglio)


sec_log = SecurityLogger()
sec_log.login_fallito("admin", "192.168.1.100")
sec_log.sospetta_intrusione("10.0.0.99", "5 tentativi di login falliti in 1 minuto")
```

### Secure Deserialization

La deserializzazione di dati da fonti non fidate e una delle vulnerabilita piu pericolose. Il modulo `pickle` di Python permette l'esecuzione di codice arbitrario durante la deserializzazione:

```python
import pickle
import json
import yaml


# === PERICOLO: pickle da fonte non fidata ===
# MAI fare questo con dati non fidati:
# dati = pickle.loads(dati_dalla_rete)
# Un payload malevolo puo eseguire comandi arbitrari sul sistema!


# === Alternative sicure ===

# 1. JSON (sicuro per design, nessuna esecuzione di codice)
dati_json = json.loads('{"nome": "Mario", "eta": 30}')

# 2. YAML sicuro (usare safe_load, MAI load!)
# SBAGLIATO: yaml.load(dati, Loader=yaml.FullLoader)  # esecuzione codice!
# CORRETTO:
dati_yaml = yaml.safe_load('nome: Mario\neta: 30')

# 3. Se pickle e necessario, usare un unpickler ristretto
import io


class UnpicklerSicuro(pickle.Unpickler):
    """Unpickler che permette solo tipi sicuri."""

    TIPI_CONSENTITI = {
        "builtins": {"dict", "list", "tuple", "set", "frozenset",
                     "str", "int", "float", "bool", "bytes", "complex"},
        "collections": {"OrderedDict", "defaultdict"},
        "datetime": {"datetime", "date", "time", "timedelta"},
    }

    def find_class(self, modulo: str, nome: str):
        if modulo in self.TIPI_CONSENTITI:
            if nome in self.TIPI_CONSENTITI[modulo]:
                return super().find_class(modulo, nome)
        raise pickle.UnpicklingError(
            f"Tipo non consentito: {modulo}.{nome}"
        )


def carica_pickle_sicuro(dati: bytes):
    """Deserializza pickle permettendo solo tipi sicuri."""
    return UnpicklerSicuro(io.BytesIO(dati)).load()
```

---

## OWASP Top 10 per Python

La OWASP Top 10 e la lista delle dieci vulnerabilita piu critiche nelle applicazioni web. Ecco come ogni voce si applica a Python, con le relative mitigazioni.

### A01:2021 — Broken Access Control

Controllo degli accessi mancante o difettoso che permette agli utenti di agire al di fuori dei propri permessi.

```python
# Mitigazione: controlli di autorizzazione espliciti su ogni endpoint
@app.route("/api/utenti/<int:user_id>/profilo")
@richiedi_autenticazione
def profilo_utente(user_id: int):
    # Verifica che l'utente possa accedere a QUESTO profilo
    if session["user_id"] != user_id and session["ruolo"] != "admin":
        abort(403)
    return ottieni_profilo(user_id)
```

### A02:2021 — Cryptographic Failures

Uso di crittografia debole o assente per proteggere dati sensibili.

**Mitigazioni:** usare algoritmi moderni (AES-256, SHA-256+, Argon2id), TLS 1.2+ per dati in transito, mai MD5/SHA1 per sicurezza, mai crittografia custom.

### A03:2021 — Injection

SQL injection, OS command injection, LDAP injection e simili.

**Mitigazioni:** query parametrizzate, ORM, mai `shell=True` con input utente, validazione rigorosa degli input.

### A04:2021 — Insecure Design

Difetti architetturali che non possono essere risolti con una semplice correzione del codice.

**Mitigazioni:** threat modeling, principi di secure design, revisione dell'architettura, pattern defense in depth.

### A05:2021 — Security Misconfiguration

Configurazioni di sicurezza assenti, incomplete o errate.

```python
# Mitigazione: configurazione sicura di default
# Flask
app.config.update(
    DEBUG=False,                       # MAI True in produzione
    TESTING=False,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
```

### A06:2021 — Vulnerable and Outdated Components

Dipendenze con vulnerabilita note o non piu mantenute.

**Mitigazioni:** pip-audit, safety, Dependabot/Renovate, aggiornamenti regolari, pinning con hash.

### A07:2021 — Identification and Authentication Failures

Debolezze nell'autenticazione che permettono la compromissione di identita.

**Mitigazioni:** Argon2id per le password, autenticazione multi-fattore, rate limiting sui login, blocco account dopo tentativi falliti.

### A08:2021 — Software and Data Integrity Failures

Codice e infrastruttura che non proteggono contro violazioni di integrita (es. deserializzazione insicura, aggiornamenti senza verifica).

**Mitigazioni:** verificare firme digitali, evitare pickle da fonti non fidate, usare `--require-hashes` con pip, CI/CD sicuro.

### A09:2021 — Security Logging and Monitoring Failures

Logging insufficiente che impedisce il rilevamento di attacchi.

**Mitigazioni:** loggare tutti gli eventi di sicurezza (login, accessi negati, modifiche permessi), centralizzare i log, configurare alerting, mai loggare dati sensibili.

### A10:2021 — Server-Side Request Forgery (SSRF)

L'applicazione effettua richieste HTTP a URL controllati dall'utente senza validazione.

```python
from urllib.parse import urlparse
import ipaddress


def valida_url_esterno(url: str) -> bool:
    """Valida un URL prevenendo SSRF verso risorse interne."""
    parsed = urlparse(url)

    # Solo HTTPS
    if parsed.scheme != "https":
        return False

    # Blocca IP privati e locali
    try:
        ip = ipaddress.ip_address(parsed.hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return False
    except ValueError:
        pass  # hostname non e un IP, procedera con DNS

    # Blocca hostname interni noti
    hostname_bloccati = {"localhost", "127.0.0.1", "0.0.0.0",
                          "metadata.google.internal", "169.254.169.254"}
    if parsed.hostname in hostname_bloccati:
        return False

    return True
```

---

## Best Practices

Dieci pratiche fondamentali per la sicurezza delle applicazioni Python, da applicare sistematicamente in ogni progetto.

**1. Mantenere Python e le dipendenze sempre aggiornate.**
Le vulnerabilita note vengono corrette nelle nuove versioni. Utilizzare `pip-audit` e `safety` regolarmente, configurare Dependabot o Renovate, e aggiornare Python stesso alle ultime release di sicurezza. Pianificare un ciclo di aggiornamento settimanale o bisettimanale.

**2. Non inventare la propria crittografia.**
Utilizzare sempre librerie consolidate e peer-reviewed come `cryptography`, `bcrypt` e `argon2-cffi`. Gli algoritmi crittografici custom contengono quasi sempre vulnerabilita sottili. Seguire le raccomandazioni di NIST e OWASP per la scelta degli algoritmi e dei parametri.

**3. Validare tutti gli input, codificare tutti gli output.**
Ogni dato proveniente dall'esterno e potenzialmente pericoloso. Validare tipo, formato, lunghezza e range di ogni input. Codificare l'output in base al contesto di destinazione (HTML, URL, SQL, JSON). Utilizzare framework come Pydantic per la validazione strutturata.

**4. Gestire i segreti con sistemi dedicati.**
Non inserire mai password, chiavi API o token nel codice sorgente. Utilizzare variabili d'ambiente per lo sviluppo locale (python-dotenv), sistemi di gestione segreti per la produzione (Vault, AWS Secrets Manager), e strumenti come detect-secrets per prevenire commit accidentali.

**5. Utilizzare query parametrizzate per ogni interazione con il database.**
Non concatenare mai stringhe per costruire query SQL. Utilizzare i parametri delle query forniti dal driver del database, oppure un ORM come SQLAlchemy o Django ORM, che parametrizzano automaticamente le query.

**6. Configurare TLS/SSL correttamente.**
Forzare TLS 1.2 come versione minima, verificare sempre i certificati (mai `verify=False` in produzione), configurare cifrari sicuri, e impostare HSTS per le applicazioni web. Monitorare la scadenza dei certificati.

**7. Applicare il principio del minimo privilegio.**
Ogni componente deve avere solo i permessi strettamente necessari. Utenti database con accesso limitato alle tabelle necessarie, file con permessi restrittivi, processi che rilasciano i privilegi di root dopo l'inizializzazione.

**8. Implementare logging di sicurezza completo.**
Registrare tutti gli eventi rilevanti per la sicurezza: tentativi di login (riusciti e falliti), modifiche ai permessi, accessi a risorse sensibili, errori di autorizzazione. Non includere mai dati sensibili nei log (password, token, numeri di carta di credito). Centralizzare i log e configurare alert per pattern sospetti.

**9. Integrare l'analisi di sicurezza nella CI/CD.**
Eseguire Bandit, pip-audit, Safety e detect-secrets automaticamente in ogni pipeline CI/CD. Bloccare il merge di pull request che introducono nuove vulnerabilita. Eseguire scansioni periodiche anche sull'intero codebase, non solo sui nuovi commit.

**10. Adottare la difesa in profondita.**
Non affidarsi mai a un singolo meccanismo di sicurezza. Combinare validazione input, autenticazione, autorizzazione, crittografia, rate limiting, logging e monitoraggio. Ogni livello riduce il rischio residuo, e la compromissione di un singolo livello non compromette l'intero sistema. Eseguire regolarmente penetration test e revisioni di sicurezza del codice.

---

## Cryptography Library — Approfondimento

La libreria `cryptography` e il pilastro crittografico dell'ecosistema Python. Mantenuta da Pyca (Python Cryptographic Authority), supportata da Mozilla e usata internamente da `pip`, `paramiko`, `pyOpenSSL` e decine di altri progetti critici. Comprenderne il modello di versioning, le policy di fine vita e le API avanzate e essenziale per chiunque sviluppi software che gestisce dati sensibili.

### Versioning e Policy EOL

La libreria segue un modello di rilascio basato su *feature releases* (es. 42.0, 43.0, 44.0) con patch di sicurezza per l'ultima major e, quando necessario, per la major precedente. Il progetto **non** mantiene branch di supporto a lungo termine (LTS): ogni nuova major sostituisce la precedente come branch supportato.

**Policy di supporto della libreria (da `cryptography` SECURITY.md):**

| Aspetto | Regola |
|---------|--------|
| Branch supportato | Solo l'ultima major release riceve patch di sicurezza |
| Finestra EOL | La major precedente riceve patch critiche per ~6 mesi dopo il rilascio della nuova major |
| OpenSSL supportato | Segue le versioni supportate da OpenSSL; quando OpenSSL 1.1.1 ha raggiunto EOL (2023-09-11), `cryptography` ha rimosso il supporto |
| Python supportato | Segue la policy EOL di CPython; versioni EOL di Python vengono rimosse entro 1-2 release |
| Backend Rust | Dal rilascio 35.0 (2022), la libreria richiede un compilatore Rust per la build; questo ha implicazioni per sistemi embedded o legacy |

**Verifica della versione installata:**

```python
import cryptography

print(f"cryptography version: {cryptography.__version__}")

# Verifica programmatica della versione minima
from packaging.version import Version

versione_minima = Version("42.0.0")
versione_installata = Version(cryptography.__version__)

if versione_installata < versione_minima:
    raise RuntimeError(
        f"cryptography {versione_installata} non supportata. "
        f"Aggiornare ad almeno {versione_minima}"
    )
```

**Strategia di aggiornamento consigliata:**

1. Monitorare i rilasci su GitHub (`pyca/cryptography/releases`)
2. Aggiornare entro 30 giorni dalla nuova major release
3. Applicare patch di sicurezza entro 48 ore dal rilascio
4. Testare con `pytest` prima di deployare in produzione
5. Verificare la compatibilita con la versione di OpenSSL in uso: `python -c "from cryptography.hazmat.backends.openssl import backend; print(backend.openssl_version_text())"`

### Fernet — Approfondimento

Fernet e la ricetta di alto livello raccomandata per la crittografia simmetrica. Internamente combina AES-128-CBC per la confidenzialita e HMAC-SHA256 per l'autenticita (encrypt-then-MAC). Il formato del token include versione, timestamp, IV, ciphertext e tag HMAC.

```python
from cryptography.fernet import Fernet, MultiFernet
import base64
import os


# --- Rotazione delle chiavi con MultiFernet ---
# MultiFernet permette di ruotare le chiavi senza re-cifrare tutti i dati
chiave_vecchia = Fernet.generate_key()
chiave_nuova = Fernet.generate_key()

# La prima chiave nella lista e usata per cifrare
# Tutte le chiavi vengono provate per decifrare
multi_fernet = MultiFernet([Fernet(chiave_nuova), Fernet(chiave_vecchia)])

# Cifratura (usa chiave_nuova)
token = multi_fernet.encrypt(b"Dati sensibili durante la rotazione chiavi")

# Decifratura (prova prima chiave_nuova, poi chiave_vecchia)
dati = multi_fernet.decrypt(token)

# Rotazione esplicita: re-cifra un token vecchio con la chiave nuova
token_ruotato = multi_fernet.rotate(token)


# --- Derivare una chiave Fernet da una password ---
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


def chiave_fernet_da_password(password: str, salt: bytes) -> bytes:
    """Deriva una chiave Fernet valida da una password umana."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,
    )
    chiave_grezza = kdf.derive(password.encode("utf-8"))
    return base64.urlsafe_b64encode(chiave_grezza)


salt = os.urandom(16)
chiave = chiave_fernet_da_password("LaMiaPassphrase!", salt)
f = Fernet(chiave)
cifrato = f.encrypt(b"Dati protetti con password")
print(f"Token: {cifrato[:40]}...")
```

### Crittografia Asimmetrica — Curve Ellittiche

Le curve ellittiche (ECC) offrono lo stesso livello di sicurezza di RSA con chiavi significativamente piu corte. Una chiave ECC a 256 bit equivale approssimativamente a una RSA a 3072 bit (NIST SP 800-57 Part 1, Rev. 5).

```python
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization


# --- ECDSA: firma e verifica ---
chiave_privata = ec.generate_private_key(ec.SECP256R1())  # P-256 (NIST)
messaggio = b"Documento da firmare con curva ellittica"

firma = chiave_privata.sign(messaggio, ec.ECDSA(hashes.SHA256()))

try:
    chiave_privata.public_key().verify(firma, messaggio, ec.ECDSA(hashes.SHA256()))
    print("Firma ECDSA valida")
except Exception:
    print("Firma ECDSA NON valida")


# --- ECDH: key exchange ---
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

chiave_alice = ec.generate_private_key(ec.SECP256R1())
chiave_bob = ec.generate_private_key(ec.SECP256R1())

segreto_alice = chiave_alice.exchange(ec.ECDH(), chiave_bob.public_key())
segreto_bob = chiave_bob.exchange(ec.ECDH(), chiave_alice.public_key())
assert segreto_alice == segreto_bob

# Derivazione chiave simmetrica dal segreto condiviso (HKDF, RFC 5869)
chiave_simmetrica = HKDF(
    algorithm=hashes.SHA256(), length=32, salt=None, info=b"chiave-sessione-v1",
).derive(segreto_alice)
```

### X.509 — Validazione Catena di Certificati

Oltre alla creazione di certificati self-signed (trattata nella sezione Crittografia), la validazione della catena e critica per mTLS e verifica certificati client.

```python
from cryptography import x509
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.primitives.asymmetric import padding
from datetime import datetime, timezone


def valida_catena_certificati(cert_pem: bytes, ca_pem: bytes) -> dict[str, object]:
    """Valida un certificato contro la sua CA emittente."""
    cert = load_pem_x509_certificate(cert_pem)
    ca = load_pem_x509_certificate(ca_pem)
    risultato: dict[str, object] = {
        "soggetto": cert.subject.rfc4514_string(),
        "emittente": cert.issuer.rfc4514_string(),
    }

    try:
        ca.public_key().verify(
            cert.signature, cert.tbs_certificate_bytes,
            padding.PKCS1v15(), cert.signature_hash_algorithm,
        )
        risultato["firma_valida"] = True
    except Exception:
        risultato["firma_valida"] = False

    ora = datetime.now(timezone.utc)
    risultato["scaduto"] = ora > cert.not_valid_after_utc
    risultato["giorni_alla_scadenza"] = (cert.not_valid_after_utc - ora).days
    return risultato
```

### Hazmat Layer — Regole di Ingaggio

Il modulo `cryptography.hazmat` (Hazardous Materials) espone primitive crittografiche di basso livello. Il nome stesso e un avviso: usare queste API richiede competenze crittografiche solide. Errori comuni portano a vulnerabilita critiche.

**Quando usare hazmat:**
- Quando le ricette di alto livello (Fernet, `sign`/`verify`) non coprono il caso d'uso
- Quando si implementa un protocollo specifico documentato in un RFC
- Quando si deve interoperare con sistemi che richiedono parametri specifici

**Quando NON usare hazmat:**
- Per cifratura generica (usare Fernet)
- Per hashing password (usare argon2-cffi o bcrypt)
- Per generare numeri casuali (usare `secrets`)

```python
# REGOLA: ogni uso di hazmat deve citare il riferimento (RFC, NIST SP, etc.)

# Esempio: AES-GCM (NIST SP 800-38D) — cifratura autenticata
# Preferito su AES-CBC+HMAC perche GCM gestisce autenticita e cifratura
# in un'unica operazione, riducendo il rischio di errori di composizione.
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def aes_gcm_encrypt(chiave: bytes, dati: bytes,
                     dati_associati: bytes | None = None) -> tuple[bytes, bytes]:
    """Cifra con AES-256-GCM (NIST SP 800-38D)."""
    nonce = os.urandom(12)  # 96 bit come raccomandato da NIST
    aesgcm = AESGCM(chiave)
    cifrato = aesgcm.encrypt(nonce, dati, dati_associati)
    return nonce, cifrato


def aes_gcm_decrypt(chiave: bytes, nonce: bytes, cifrato: bytes,
                     dati_associati: bytes | None = None) -> bytes:
    """Decifra con AES-256-GCM."""
    aesgcm = AESGCM(chiave)
    return aesgcm.decrypt(nonce, cifrato, dati_associati)


chiave = AESGCM.generate_key(bit_length=256)
nonce, cifrato = aes_gcm_encrypt(chiave, b"Messaggio riservato", b"header-pubblico")
originale = aes_gcm_decrypt(chiave, nonce, cifrato, b"header-pubblico")
print(f"Decifrato: {originale.decode()}")
```

---

## Il Modulo secrets — Approfondimento

Il modulo `secrets` (PEP 506, Python 3.6+) e il modo canonico per generare valori casuali crittograficamente sicuri. Utilizza `os.urandom()` come sorgente, che a sua volta usa `/dev/urandom` (Linux), `CryptGenRandom` (Windows) o `getentropy()` (macOS/BSD).

### secrets vs random — Quando Usare Quale

| Scenario | Modulo | Motivazione |
|----------|--------|-------------|
| Token di sessione, API key | `secrets` | Devono essere imprevedibili |
| Password, OTP | `secrets` | Devono resistere a brute-force |
| CSRF token | `secrets` | Devono essere non indovinabili |
| Sale per hashing | `secrets` / `os.urandom` | Devono essere unici e casuali |
| Simulazione Monte Carlo | `random` | Non servono garanzie crittografiche |
| Ordinamento casuale di una lista | `random` | Nessun requisito di sicurezza |
| Test unitari (seed riproducibile) | `random` | Serve determinismo con `random.seed()` |
| Generazione UUID | `uuid.uuid4()` | Usa `os.urandom` internamente |

**Errore critico da evitare:**

```python
import random

# SBAGLIATO: random usa Mersenne Twister (PRNG deterministico)
# Un attaccante che osserva 624 output consecutivi puo prevedere
# TUTTI i futuri output. Non usare MAI per sicurezza.
token_insicuro = "".join(random.choices("abcdefghijklmnop", k=32))

# CORRETTO:
import secrets
token_sicuro = secrets.token_urlsafe(32)
```

### Pattern Avanzati con secrets

```python
import secrets
import string
import hmac


# --- Generazione di codici di invito con formato leggibile ---
def genera_codice_invito(segmenti: int = 4, lunghezza_segmento: int = 4) -> str:
    """Genera un codice tipo 'ABCD-EF12-GH34-IJ56' crittograficamente sicuro."""
    caratteri = string.ascii_uppercase + string.digits
    # Rimuove caratteri ambigui (0/O, 1/I/L)
    caratteri = caratteri.translate(str.maketrans("", "", "0OIL1"))
    segmenti_generati = [
        "".join(secrets.choice(caratteri) for _ in range(lunghezza_segmento))
        for _ in range(segmenti)
    ]
    return "-".join(segmenti_generati)


print(f"Codice invito: {genera_codice_invito()}")


# --- Token con prefisso per identificazione rapida ---
def genera_api_key(prefisso: str = "sk") -> str:
    """Genera un'API key con prefisso identificativo (es. sk_live_abc123)."""
    token = secrets.token_urlsafe(32)
    return f"{prefisso}_live_{token}"


print(f"API Key: {genera_api_key()}")


# --- Confronto timing-safe per token ---
def verifica_token(token_ricevuto: str, token_atteso: str) -> bool:
    """Confronto costante nel tempo per prevenire timing attack."""
    # secrets.compare_digest accetta solo bytes
    return secrets.compare_digest(
        token_ricevuto.encode("utf-8"),
        token_atteso.encode("utf-8"),
    )


# Equivalente con hmac (funziona anche con stringhe):
def verifica_token_hmac(ricevuto: str, atteso: str) -> bool:
    """Alternativa con hmac.compare_digest (accetta str direttamente)."""
    return hmac.compare_digest(ricevuto, atteso)
```

---

## SBOM — Software Bill of Materials

Un SBOM (Software Bill of Materials) e un inventario formale di tutti i componenti software presenti in un'applicazione, incluse le dipendenze dirette e transitive, con le rispettive versioni e licenze. E il fondamento della trasparenza nella supply chain software.

Il concetto e analogo alla distinta dei materiali nell'industria manifatturiera: sapere esattamente cosa contiene il prodotto finale. L'Executive Order 14028 degli USA (2021) ha reso gli SBOM un requisito per il software venduto al governo federale, e l'UE con il Cyber Resilience Act (CRA) sta seguendo la stessa direzione.

### CycloneDX-py

CycloneDX e uno standard OWASP per gli SBOM, supportato nativamente dall'ecosistema Python tramite `cyclonedx-py`.

```bash
# Installazione
pip install cyclonedx-bom

# Generazione SBOM dall'ambiente corrente
cyclonedx-py environment -o sbom.json --format json

# Generazione SBOM da requirements.txt
cyclonedx-py requirements -i requirements.txt -o sbom.xml --format xml

# Generazione SBOM da Poetry
cyclonedx-py poetry -o sbom.json --format json

# Generazione SBOM da Pipenv
cyclonedx-py pipenv -o sbom.json --format json
```

### Formati SBOM: JSON e XML

CycloneDX supporta sia JSON sia XML. Il formato JSON e piu leggero e facile da processare programmaticamente; XML e usato in contesti enterprise e per la validazione con schema XSD.

```python
import json
from pathlib import Path


def analizza_sbom(percorso_sbom: str) -> dict:
    """Analizza un SBOM CycloneDX in formato JSON."""
    sbom = json.loads(Path(percorso_sbom).read_text())

    componenti = sbom.get("components", [])
    risultato = {
        "totale_componenti": len(componenti),
        "per_tipo": {},
        "licenze_uniche": set(),
        "senza_licenza": [],
    }

    for comp in componenti:
        tipo = comp.get("type", "unknown")
        risultato["per_tipo"][tipo] = risultato["per_tipo"].get(tipo, 0) + 1

        licenze = comp.get("licenses", [])
        if licenze:
            for lic in licenze:
                if "license" in lic:
                    lid = lic["license"].get("id", lic["license"].get("name", "N/D"))
                    risultato["licenze_uniche"].add(lid)
        else:
            risultato["senza_licenza"].append(
                f"{comp.get('name', '?')}@{comp.get('version', '?')}"
            )

    risultato["licenze_uniche"] = sorted(risultato["licenze_uniche"])
    return risultato


# Uso:
# info = analizza_sbom("sbom.json")
# print(f"Componenti totali: {info['totale_componenti']}")
# print(f"Licenze: {info['licenze_uniche']}")
# print(f"Senza licenza: {info['senza_licenza']}")
```

### SBOM in CI/CD

```yaml
# .github/workflows/sbom.yml — genera e pubblica SBOM ad ogni release
name: Generate SBOM
on:
  release:
    types: [published]

jobs:
  sbom:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - name: Genera SBOM CycloneDX
        run: |
          pip install cyclonedx-bom
          cyclonedx-py environment -o sbom.json --format json
      - uses: actions/upload-artifact@v4
        with:
          name: sbom
          path: sbom.json
      - run: gh release upload "${{ github.event.release.tag_name }}" sbom.json
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Supply Chain Security — Approfondimento

La supply chain del software Python si estende dal codice sorgente al pacchetto distribuito su PyPI, passando per il sistema di build, il registro, il trasporto e l'installazione locale. Ogni anello di questa catena puo essere compromesso.

### PEP 458 — TUF per PyPI

PEP 458 (accettato, in fase di implementazione progressiva) integra The Update Framework (TUF) in PyPI. TUF e un framework di sicurezza progettato specificamente per proteggere i sistemi di aggiornamento software contro attacchi come:

- **Freeze attack** — un attaccante serve versioni vecchie del pacchetto con vulnerabilita note
- **Rollback attack** — un attaccante fa apparire una versione vecchia come la piu recente
- **Mix-and-match attack** — un attaccante combina versioni di pacchetti diversi in modo inconsistente
- **Arbitrary package attack** — un attaccante sostituisce un pacchetto legittimo con uno malevolo

TUF usa un sistema di ruoli con firme crittografiche:

```
                  root
                   │
          ┌────────┼────────┐
          │        │        │
       targets  snapshot  timestamp
          │
     delegated targets
```

| Ruolo | Responsabilita |
|-------|----------------|
| `root` | Definisce le chiavi fidate per tutti gli altri ruoli |
| `targets` | Firma i metadati dei pacchetti (hash, dimensione) |
| `snapshot` | Firma un'istantanea coerente di tutti i metadati targets |
| `timestamp` | Firma un timestamp che indica la freschezza dei metadati (previene freeze attack) |

**Stato di implementazione su PyPI (2026):** i metadati TUF sono serviti da PyPI; `pip` sta integrando progressivamente la verifica TUF come default. E possibile verificare manualmente:

```bash
# Verifica dei metadati TUF di PyPI (sperimentale)
pip install python-tuf
python -c "
from tuf.ngclient import Updater
updater = Updater(
    metadata_dir='tuf_metadata',
    metadata_base_url='https://pypi.org/simple/',
)
# In futuro pip fara questo automaticamente
"
```

### PEP 480 — Gestione Chiavi per TUF

PEP 480 completa PEP 458 definendo come le chiavi crittografiche di TUF vengono gestite su PyPI. I punti chiave:

1. **Separazione delle chiavi:** le chiavi root sono conservate offline (hardware security module); le chiavi online (timestamp, snapshot) sono su infrastruttura PyPI
2. **Rotazione delle chiavi:** procedura definita per sostituire chiavi compromesse senza interrompere il servizio
3. **Soglia multi-firma:** il ruolo root richiede firme da piu parti indipendenti (quorum), prevenendo compromissione da un singolo punto

### Trusted Publishers (OIDC)

Trusted Publishers e il meccanismo di PyPI per pubblicare pacchetti senza token di lunga durata. Usa OpenID Connect (OIDC) per verificare l'identita del publisher direttamente dall'ambiente CI/CD.

```yaml
# .github/workflows/publish.yml — Trusted Publisher (nessun token!)
name: Publish to PyPI
on:
  release: { types: [published] }
permissions:
  id-token: write
jobs:
  publish:
    runs-on: ubuntu-latest
    environment: release
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install build && python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

**Vantaggi rispetto ai token API:** nessun segreto da gestire; token effimero (vive solo per la durata del workflow); identita verificabile crittograficamente; vincolato a repository/branch/ambiente specifici.

### Sigstore per Python

Sigstore e un'infrastruttura di firma digitale senza chiavi (keyless signing) sviluppata da Google e Linux Foundation. Per Python, il pacchetto `sigstore` permette di firmare e verificare artefatti senza gestire chiavi private.

```bash
# Installazione
pip install sigstore

# Firma di un artefatto (richiede autenticazione OIDC)
python -m sigstore sign mio_pacchetto-1.0.0.tar.gz

# Verifica della firma
python -m sigstore verify identity \
  --cert-identity ciupsciups@libero.it \
  --cert-oidc-issuer https://accounts.google.com \
  mio_pacchetto-1.0.0.tar.gz
```

Sigstore usa tre componenti:
- **Fulcio** — CA che emette certificati effimeri basati su identita OIDC
- **Rekor** — transparency log immutabile (simile a Certificate Transparency)
- **Cosign** — tool per firmare container images (non direttamente Python, ma parte dell'ecosistema)

---

## pip-audit — Approfondimento

`pip-audit` (mantenuto da Trail of Bits, sponsorizzato da Google) verifica le dipendenze Python installate contro l'OSV (Open Source Vulnerabilities) database e il database di vulnerabilita di PyPI.

### Strategie di Scansione Avanzata

```bash
# Scansione con sorgente dati specifica
pip-audit --vulnerability-service osv      # Open Source Vulnerabilities (default)
pip-audit --vulnerability-service pypi     # Database PyPI nativo

# Scansione di un virtual environment specifico
pip-audit --path /percorso/al/.venv

# Scansione con output machine-readable
pip-audit -f json -o risultati.json
pip-audit -f cyclonedx-json -o sbom-vuln.json  # output CycloneDX con vuln
pip-audit -f markdown -o report.md

# Scansione rigorosa (fallisce anche per avvisi)
pip-audit --strict

# Fix automatico: aggiorna le dipendenze vulnerabili
pip-audit --fix --dry-run   # mostra cosa farebbe
pip-audit --fix             # applica gli aggiornamenti
```

### Gestione Falsi Positivi

```bash
# Ignora vulnerabilita specifiche (per ID)
pip-audit --ignore-vuln PYSEC-2024-1234
pip-audit --ignore-vuln GHSA-xxxx-yyyy-zzzz

# Ignora multiple vulnerabilita da file
pip-audit --ignore-vuln-file .pip-audit-known-exploits

# File .pip-audit-known-exploits:
# PYSEC-2024-1234  # motivo: non applicabile al nostro uso di libreria X
# GHSA-xxxx-yyyy   # motivo: mitigato da configurazione firewall
```

### pip-audit in CI/CD

```yaml
# .github/workflows/pip-audit.yml
name: pip-audit
on: [push, pull_request]
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r requirements.txt
      - run: |
          pip install pip-audit
          pip-audit --strict --desc \
            --ignore-vuln-file .pip-audit-known-exploits \
            -f json -o pip-audit-results.json
```

---

## Dependency Pinning Avanzato

### uv e uv.lock

`uv` (di Astral, gli autori di Ruff) e un gestore di pacchetti Python ultra-veloce scritto in Rust. Il suo lockfile (`uv.lock`) e cross-platform e include hash per tutte le dipendenze, garantendo build riproducibili.

```bash
# Installazione uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Inizializzazione progetto
uv init mio-progetto
cd mio-progetto

# Aggiunta dipendenze (aggiorna automaticamente uv.lock)
uv add flask cryptography argon2-cffi

# Installazione da lockfile (deterministica)
uv sync

# Aggiornamento dipendenze rispettando i vincoli
uv lock --upgrade

# Esportazione in requirements.txt con hash
uv export --format requirements-txt > requirements.txt
```

**Struttura di `uv.lock`:** il lockfile include la versione esatta, la sorgente, gli hash SHA-256 di ogni wheel e sdist, e il grafo completo delle dipendenze transitive. Non e progettato per essere editato manualmente.

### Hash Checking Mode

```bash
# pip con verifica hash (requirements.txt generato da pip-compile o uv)
pip install --require-hashes -r requirements.txt

# Esempio di requirements.txt con hash:
# cryptography==44.0.0 \
#     --hash=sha256:354f2f... \
#     --hash=sha256:8b1a2e...

# pip-compile con generazione hash
pip-compile --generate-hashes requirements.in -o requirements.txt
```

**Perche gli hash sono importanti:**
- Prevengono la sostituzione di un pacchetto con uno malevolo (man-in-the-middle)
- Garantiscono che lo stesso identico artefatto venga installato in tutti gli ambienti
- Rilevano modifiche post-pubblicazione (un maintainer malevolo che modifica un release gia pubblicato)

### Build Riproducibili

```toml
# pyproject.toml — configurazione per build riproducibili
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "mio-progetto"
version = "1.0.0"
requires-python = ">=3.11"
dependencies = [
    "flask>=3.1.0,<4.0",
    "cryptography>=44.0.0,<45.0",
    "argon2-cffi>=23.1.0",
]

[tool.uv]
# Richiede che uv.lock sia committato e aggiornato
managed = true
```

---

## Bandit — Approfondimento

### Configurazione Avanzata

```toml
# pyproject.toml — configurazione Bandit
[tool.bandit]
exclude_dirs = ["tests", "venv", ".venv", "migrations"]
skips = ["B101"]  # skip assert_used nei test
targets = ["src"]

# Per progetto, si puo anche usare .bandit.yml
```

```yaml
# .bandit.yml — configurazione YAML (alternativa)
exclude_dirs:
  - tests
  - venv
  - .venv
  - migrations

skips:
  - B101  # assert_used (legittimo nei test)

# Profili personalizzati
profiles:
  strict:
    include:
      - any_other_function_with_shell_equals_true
      - assert_used
      - exec_used
      - hardcoded_password_string
      - hardcoded_tmp_directory
```

### Livelli di Severita e Confidenza

Bandit classifica ogni finding su due assi:

| Severita | Significato |
|----------|-------------|
| LOW | Rischio basso, potenziale code smell di sicurezza |
| MEDIUM | Rischio moderato, richiede revisione |
| HIGH | Rischio alto, probabile vulnerabilita |

| Confidenza | Significato |
|------------|-------------|
| LOW | Bandit non e sicuro che sia un problema reale |
| MEDIUM | Probabile problema |
| HIGH | Bandit e molto sicuro che sia un problema |

```bash
# Filtrare per severita e confidenza
bandit -r src/ -ll -ii     # solo MEDIUM+ severita, MEDIUM+ confidenza
bandit -r src/ -lll -iii   # solo HIGH severita, HIGH confidenza

# Output con contesto (mostra le righe di codice)
bandit -r src/ -n 5        # mostra 5 righe di contesto per finding

# Lista tutti i test disponibili
bandit --tests
```

### Bandit in CI/CD con Quality Gate

```yaml
# .github/workflows/bandit.yml — quality gate: zero HIGH findings
name: Bandit SAST
on: [push, pull_request]
jobs:
  bandit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: |
          pip install bandit[toml]
          bandit -r src/ -lll -iii -f json -o bandit-high.json
```

### Gestione Falsi Positivi con nosec

```python
# Sopprimere un singolo finding con commento nosec
import subprocess

# Questo e sicuro perche il comando e hardcoded, non viene da input utente
subprocess.run(["ls", "-la"], check=True)  # nosec B603

# Con specifica del test soppresso (piu preciso)
subprocess.run(["ls", "-la"], check=True)  # nosec B603 - comando hardcoded

# ATTENZIONE: non abusare di nosec. Ogni soppressione deve essere:
# 1. Giustificata con un commento
# 2. Rivista periodicamente
# 3. Il piu specifica possibile (citare il test ID)
```

---

## OWASP Top 10 — Mapping Python Dettagliato

Espansione della sezione precedente con mitigazioni operative per ogni voce della OWASP Top 10 (2021) nel contesto Python.

| # | Vulnerabilita | Moduli/Framework Python | Mitigazione primaria |
|---|---------------|------------------------|---------------------|
| A01 | Broken Access Control | Flask-Login, Django auth, FastAPI Depends | Decoratori di autorizzazione su ogni endpoint; RBAC/ABAC |
| A02 | Cryptographic Failures | `cryptography`, `hashlib`, `ssl` | AES-256-GCM, Argon2id, TLS 1.2+, mai MD5/SHA1 per sicurezza |
| A03 | Injection | SQLAlchemy, Django ORM, `shlex` | Query parametrizzate, ORM, `shlex.quote()` per comandi shell |
| A04 | Insecure Design | Threat modeling, ADR | Security by design, threat model prima del codice |
| A05 | Security Misconfiguration | Flask/Django settings, `python-dotenv` | `DEBUG=False` in produzione, header di sicurezza, CSP |
| A06 | Vulnerable Components | `pip-audit`, `safety`, CycloneDX | SBOM, scansione automatica, Dependabot/Renovate |
| A07 | Auth Failures | `argon2-cffi`, `PyJWT`, `python-jose` | Argon2id, MFA, rate limiting, blocco account |
| A08 | Data Integrity | `--require-hashes`, sigstore, TUF | Hash pinning, firma digitale, CI/CD sicuro |
| A09 | Logging Failures | `logging`, structlog, Sentry | Log strutturati con trace_id, mai loggare segreti |
| A10 | SSRF | `ipaddress`, `urllib.parse` | Validazione URL, blocco IP privati/loopback, allowlist |

```python
# A03 — Prevenzione OS Command Injection
import shlex
import subprocess


def esegui_comando_sicuro(nome_file: str) -> str:
    """Esegue un comando con input utente in modo sicuro."""
    # SBAGLIATO: shell=True con input utente
    # subprocess.run(f"cat {nome_file}", shell=True)

    # CORRETTO: lista di argomenti (nessuna shell)
    nome_sanitizzato = shlex.quote(nome_file)
    risultato = subprocess.run(
        ["cat", nome_file],  # lista, non stringa
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
    )
    return risultato.stdout
```

---

## Validazione Input Avanzata

### Pydantic come Security Layer

Pydantic non e solo un tool di serializzazione: usato sistematicamente, diventa un livello di sicurezza che blocca input malformati prima che raggiungano la logica applicativa.

```python
from pydantic import BaseModel, field_validator, model_validator, Field
from pydantic import EmailStr, HttpUrl
from typing import Annotated
import re


class RichiestaRicerca(BaseModel):
    """Modello di validazione per una richiesta di ricerca."""
    query: Annotated[str, Field(min_length=1, max_length=200)]
    pagina: Annotated[int, Field(ge=1, le=1000)] = 1
    per_pagina: Annotated[int, Field(ge=1, le=100)] = 20
    ordinamento: str = "rilevanza"

    @field_validator("query")
    @classmethod
    def sanitizza_query(cls, v: str) -> str:
        # Rimuove caratteri di controllo
        v = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", v)
        # Previene SQL injection basilare nei parametri di ricerca
        v = v.replace("'", "").replace('"', "").replace(";", "")
        return v.strip()

    @field_validator("ordinamento")
    @classmethod
    def valida_ordinamento(cls, v: str) -> str:
        validi = {"rilevanza", "data", "nome", "prezzo"}
        if v not in validi:
            raise ValueError(f"Ordinamento deve essere uno di: {validi}")
        return v


class UploadFile(BaseModel):
    """Validazione per upload di file."""
    nome_file: str
    dimensione_bytes: Annotated[int, Field(gt=0, le=10_485_760)]  # max 10 MB
    content_type: str

    @field_validator("nome_file")
    @classmethod
    def valida_nome_file(cls, v: str) -> str:
        # Previene path traversal
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError("Nome file contiene caratteri non consentiti")
        # Solo estensioni permesse
        estensioni_consentite = {".pdf", ".png", ".jpg", ".jpeg", ".csv"}
        ext = "." + v.rsplit(".", 1)[-1].lower() if "." in v else ""
        if ext not in estensioni_consentite:
            raise ValueError(f"Estensione non consentita. Permesse: {estensioni_consentite}")
        return v

    @field_validator("content_type")
    @classmethod
    def valida_content_type(cls, v: str) -> str:
        tipi_consentiti = {
            "application/pdf",
            "image/png",
            "image/jpeg",
            "text/csv",
        }
        if v not in tipi_consentiti:
            raise ValueError(f"Content-Type non consentito: {v}")
        return v
```

### Prevenzione Path Traversal

```python
from pathlib import Path
import os


class ValidatorePercorso:
    """Validatore di percorsi file con prevenzione path traversal."""

    def __init__(self, directory_base: str):
        self._base = Path(directory_base).resolve()
        if not self._base.is_dir():
            raise ValueError(f"Directory base non esiste: {directory_base}")

    def valida(self, percorso_relativo: str) -> Path:
        """Valida e risolve un percorso relativo alla directory base."""
        # Rimuove componenti pericolose
        pulito = percorso_relativo.replace("\x00", "")  # null byte injection

        # Risolve il percorso completo
        percorso_completo = (self._base / pulito).resolve()

        # Verifica che sia sotto la directory base
        try:
            percorso_completo.relative_to(self._base)
        except ValueError:
            raise PermissionError(
                f"Tentativo di path traversal: {percorso_relativo!r}"
            )

        return percorso_completo

    def leggi_sicuro(self, percorso_relativo: str) -> bytes:
        """Legge un file solo se dentro la directory base."""
        percorso = self.valida(percorso_relativo)
        if not percorso.is_file():
            raise FileNotFoundError(f"File non trovato: {percorso_relativo}")
        # Verifica anche i symlink
        if percorso.is_symlink():
            target = percorso.resolve()
            try:
                target.relative_to(self._base)
            except ValueError:
                raise PermissionError("Symlink punta fuori dalla directory base")
        return percorso.read_bytes()


# Uso
validatore = ValidatorePercorso("/app/uploads")
# validatore.valida("../../etc/passwd")  # -> PermissionError
# validatore.valida("documenti/report.pdf")  # -> Path("/app/uploads/documenti/report.pdf")
```

### Validazione File Upload

```python
import hashlib
import magic  # python-magic
from pathlib import Path


TIPI_CONSENTITI = {
    "application/pdf": {".pdf"},
    "image/png": {".png"},
    "image/jpeg": {".jpg", ".jpeg"},
    "text/csv": {".csv"},
}
DIMENSIONE_MAX = 10 * 1024 * 1024  # 10 MB


def valida_upload(nome_file: str, contenuto: bytes) -> dict:
    """Valida un file caricato: dimensione, estensione, magic bytes, path traversal."""
    errori = []
    if len(contenuto) > DIMENSIONE_MAX:
        errori.append(f"Troppo grande: {len(contenuto)} byte")
    ext = Path(nome_file).suffix.lower()
    estensioni = {e for exts in TIPI_CONSENTITI.values() for e in exts}
    if ext not in estensioni:
        errori.append(f"Estensione non consentita: {ext}")
    tipo_reale = magic.from_buffer(contenuto[:2048], mime=True)
    if tipo_reale not in TIPI_CONSENTITI:
        errori.append(f"Tipo reale non consentito: {tipo_reale}")
    if ".." in nome_file or "/" in nome_file or "\\" in nome_file:
        errori.append("Path traversal nel nome file")
    if errori:
        raise ValueError(f"Upload non valido: {'; '.join(errori)}")
    return {
        "nome_sicuro": Path(nome_file).name,
        "tipo": tipo_reale,
        "sha256": hashlib.sha256(contenuto).hexdigest(),
    }
```

---

## Gestione Segreti — Approfondimento

### Pattern con python-dotenv

```python
import os
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ConfigurazioneSicura:
    """Configurazione immutabile caricata da variabili d'ambiente."""
    database_url: str
    secret_key: str
    api_key: str
    debug: bool = False
    porta: int = 8000
    origini_cors: tuple[str, ...] = ()

    @classmethod
    def da_ambiente(cls, file_env: str = ".env") -> "ConfigurazioneSicura":
        """Carica la configurazione da file .env e variabili d'ambiente."""
        percorso_env = Path(file_env)
        if percorso_env.exists():
            load_dotenv(percorso_env)

        def richiedi(nome: str) -> str:
            valore = os.getenv(nome)
            if not valore:
                raise RuntimeError(f"Variabile obbligatoria mancante: {nome}")
            return valore

        origini = os.getenv("CORS_ORIGINS", "")
        return cls(
            database_url=richiedi("DATABASE_URL"),
            secret_key=richiedi("SECRET_KEY"),
            api_key=richiedi("API_KEY"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            porta=int(os.getenv("PORT", "8000")),
            origini_cors=tuple(o.strip() for o in origini.split(",") if o.strip()),
        )

    def __repr__(self) -> str:
        """Override repr per non esporre segreti nei log."""
        return (
            f"ConfigurazioneSicura(database_url='***', secret_key='***', "
            f"api_key='***', debug={self.debug}, porta={self.porta})"
        )
```

### HashiCorp Vault — Integrazione Completa

```python
import os
import hvac
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ClienteVault:
    """Client per HashiCorp Vault KV v2."""

    def __init__(self, url: str | None = None, token: str | None = None,
                 mount_point: str = "secret"):
        self._mount = mount_point
        self._client = hvac.Client(
            url=url or os.environ["VAULT_ADDR"],
            token=token or os.environ["VAULT_TOKEN"],
        )
        if not self._client.is_authenticated():
            raise RuntimeError("Autenticazione Vault fallita")

    def leggi(self, percorso: str) -> dict[str, Any]:
        """Legge un segreto da Vault KV v2."""
        try:
            resp = self._client.secrets.kv.v2.read_secret_version(
                path=percorso, mount_point=self._mount,
            )
            return resp["data"]["data"]
        except hvac.exceptions.InvalidPath:
            raise KeyError(f"Segreto non trovato: {percorso}")

    def leggi_chiave(self, percorso: str, chiave: str) -> str:
        dati = self.leggi(percorso)
        if chiave not in dati:
            raise KeyError(f"Chiave '{chiave}' non in {percorso}")
        return dati[chiave]

# vault = ClienteVault()
# db_password = vault.leggi_chiave("database/produzione", "password")
```

### AWS Secrets Manager — Pattern con Cache

```python
import boto3
import json
from datetime import datetime, timedelta


class GestitoreSegretiAWS:
    """Gestore di segreti da AWS Secrets Manager con cache TTL."""

    def __init__(self, regione: str = "eu-west-1", ttl_secondi: int = 300):
        self._client = boto3.client("secretsmanager", region_name=regione)
        self._cache: dict[str, tuple[dict, datetime]] = {}
        self._ttl = timedelta(seconds=ttl_secondi)

    def leggi(self, nome_segreto: str) -> dict:
        if nome_segreto in self._cache:
            valore, scadenza = self._cache[nome_segreto]
            if datetime.utcnow() < scadenza:
                return valore
        try:
            resp = self._client.get_secret_value(SecretId=nome_segreto)
            dati = json.loads(resp["SecretString"])
            self._cache[nome_segreto] = (dati, datetime.utcnow() + self._ttl)
            return dati
        except self._client.exceptions.ResourceNotFoundException:
            raise KeyError(f"Segreto non trovato: {nome_segreto}")

# aws = GestitoreSegretiAWS()
# cred = aws.leggi("produzione/database")
```

---

## Secure Coding — Insidie Comuni

### eval e exec — Pericoli e Alternative

`eval()` e `exec()` eseguono codice Python arbitrario. Con input utente, equivalgono a dare all'attaccante accesso completo al sistema.

```python
# === PERICOLO ASSOLUTO ===

# SBAGLIATO: eval con input utente
# espressione = input("Inserisci un'espressione: ")
# risultato = eval(espressione)
# Input malevolo: __import__('os').system('rm -rf /')

# SBAGLIATO: exec con input utente
# codice = request.form["codice"]
# exec(codice)  # esecuzione di codice arbitrario


# === ALTERNATIVE SICURE ===

# 1. Per espressioni matematiche: ast.literal_eval
import ast

def valuta_espressione_sicura(espressione: str) -> object:
    """Valuta solo letterali Python sicuri (stringhe, numeri, tuple, liste, dict)."""
    try:
        return ast.literal_eval(espressione)
    except (ValueError, SyntaxError) as e:
        raise ValueError(f"Espressione non valida: {e}")


# ast.literal_eval accetta: "42", "'hello'", "[1, 2, 3]", "{'a': 1}"
# ast.literal_eval rifiuta: "__import__('os')", "print('hello')"
print(valuta_espressione_sicura("[1, 2, 3]"))  # [1, 2, 3]


# 2. Per calcoli matematici complessi: librerie dedicate
# pip install simpleeval
from simpleeval import simple_eval

risultato = simple_eval("2 * (3 + 4)")  # 14
# simple_eval("__import__('os')") -> NameNotDefined exception


# 3. Per configurazione dinamica: dizionario di funzioni
def somma(a: float, b: float) -> float:
    return a + b

def prodotto(a: float, b: float) -> float:
    return a * b

operazioni = {"somma": somma, "prodotto": prodotto}

def esegui_operazione(nome: str, a: float, b: float) -> float:
    if nome not in operazioni:
        raise ValueError(f"Operazione sconosciuta: {nome}")
    return operazioni[nome](a, b)
```

### pickle — Deserializzazione Arbitraria

Il protocollo pickle include opcode che eseguono codice arbitrario durante la deserializzazione. Un attaccante puo costruire un payload che chiama `os.system()` o qualsiasi altra funzione. La sezione [Secure Deserialization](#secure-deserialization) mostra l'`UnpicklerSicuro` per i rari casi in cui pickle e necessario con dati interni.

**Alternative sicure:** `json` (nessuna esecuzione di codice), `msgpack` (binario veloce), Protocol Buffers (schema tipizzato). Usare queste per tutti i dati provenienti dalla rete o dagli utenti.

### YAML safe_load vs load

```python
import yaml

# === PERICOLO: yaml.load con FullLoader/UnsafeLoader ===
# yaml.load("!!python/object/apply:os.system ['id']", Loader=yaml.FullLoader)
# Questo ESEGUE il comando "id" durante il parsing!


# === SICURO: yaml.safe_load ===
dati = yaml.safe_load("""
nome: Mario Rossi
eta: 30
ruoli:
  - admin
  - utente
""")
print(dati)  # {'nome': 'Mario Rossi', 'eta': 30, 'ruoli': ['admin', 'utente']}

# safe_load rifiuta tag Python arbitrari:
try:
    yaml.safe_load("!!python/object/apply:os.system ['id']")
except yaml.YAMLError as e:
    print(f"Bloccato: {e}")


# === REGOLA: in ogni progetto, vietare yaml.load ===
# Usare SEMPRE yaml.safe_load o yaml.CSafeLoader
# Bandit rileva questo con il test B506 (yaml_load)
```

### Template Injection (SSTI)

Server-Side Template Injection si verifica quando input utente viene passato direttamente al motore di template come parte del template stesso, anziche come dato.

```python
from jinja2 import Environment, BaseLoader, select_autoescape, SandboxedEnvironment


# === SBAGLIATO: input utente nel template ===
# env = Environment(loader=BaseLoader())
# template_insicuro = env.from_string(input_utente)
# Input malevolo: {{ config.__class__.__init__.__globals__['os'].popen('id').read() }}


# === CORRETTO: input utente solo come dati ===
env = Environment(
    loader=BaseLoader(),
    autoescape=select_autoescape(default=True, default_for_string=True),
)

# Il template e fisso, i dati vengono dall'utente
template = env.from_string("Ciao, {{ nome }}! Hai {{ eta }} anni.")
risultato = template.render(nome="<script>alert(1)</script>", eta=30)
print(risultato)
# Output: Ciao, &lt;script&gt;alert(1)&lt;/script&gt;! Hai 30 anni.


# === Se serve esecuzione di template utente: SandboxedEnvironment ===
sandbox = SandboxedEnvironment()
try:
    t = sandbox.from_string("{{ range(10) }}")  # consentito
    t = sandbox.from_string("{{ ''.__class__.__mro__ }}")  # bloccato
except Exception as e:
    print(f"Sandbox ha bloccato: {e}")
```

---

## HTTP Security Headers — Middleware Completo

La sezione [Secure Headers](#secure-headers) mostra l'implementazione Flask. Qui un middleware equivalente per FastAPI con CSP nonce-based e Cross-Origin policies (OWASP Secure Headers Project).

```python
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import secrets


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Aggiunge header di sicurezza OWASP-compliant a ogni risposta."""

    async def dispatch(self, request: Request, call_next):
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce

        response: Response = await call_next(request)
        h = response.headers
        h["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        h["Content-Security-Policy"] = (
            f"default-src 'self'; script-src 'self' 'nonce-{nonce}'; "
            f"style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; "
            f"frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        )
        h["X-Frame-Options"] = "DENY"
        h["X-Content-Type-Options"] = "nosniff"
        h["Referrer-Policy"] = "strict-origin-when-cross-origin"
        h["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
        h["Cross-Origin-Opener-Policy"] = "same-origin"
        h["Cross-Origin-Resource-Policy"] = "same-origin"
        return response

app = FastAPI()
app.add_middleware(SecurityHeadersMiddleware)
```

**Django equivalente:** `SecurityMiddleware` + settings `SECURE_HSTS_SECONDS`, `X_FRAME_OPTIONS`, `SECURE_CONTENT_TYPE_NOSNIFF`, `django-csp` per Content-Security-Policy.

### Rate Limiting — Protezione Contro Abusi e DoS Applicativo

Il rate limiting e una difesa fondamentale contro attacchi di tipo brute-force, credential stuffing, scraping automatizzato e denial-of-service a livello applicativo. A differenza del rate limiting a livello infrastrutturale (nginx `limit_req`, cloud WAF), il rate limiting applicativo permette granularita per utente, endpoint e azione semantica.

**Pattern Token Bucket con Redis:**

```python
import time
import redis
from dataclasses import dataclass


@dataclass(frozen=True)
class RateLimitResult:
    consentito: bool
    rimanenti: int
    reset_tra_secondi: float


class TokenBucketLimiter:
    """Rate limiter con algoritmo token bucket su Redis.

    Ogni chiave ha un bucket con capacita massima.
    I token vengono rigenerati a un tasso costante.
    Ogni richiesta consuma un token; se il bucket e vuoto, la richiesta viene rifiutata.
    """

    def __init__(self, client: redis.Redis, capacita: int, tasso_per_secondo: float):
        self._r = client
        self._capacita = capacita
        self._tasso = tasso_per_secondo

    def controlla(self, chiave: str) -> RateLimitResult:
        ora = time.monotonic()
        pipe = self._r.pipeline()

        dati = self._r.hmget(chiave, "token", "ultimo_accesso")
        token_attuali = float(dati[0]) if dati[0] else float(self._capacita)
        ultimo = float(dati[1]) if dati[1] else ora

        trascorso = ora - ultimo
        token_rigenerati = trascorso * self._tasso
        token_attuali = min(self._capacita, token_attuali + token_rigenerati)

        if token_attuali >= 1.0:
            token_attuali -= 1.0
            consentito = True
        else:
            consentito = False

        ttl = int(self._capacita / self._tasso) + 1
        pipe.hset(chiave, mapping={"token": str(token_attuali), "ultimo_accesso": str(ora)})
        pipe.expire(chiave, ttl)
        pipe.execute()

        reset_tra = (1.0 - token_attuali) / self._tasso if not consentito else 0.0
        return RateLimitResult(
            consentito=consentito,
            rimanenti=int(token_attuali),
            reset_tra_secondi=round(reset_tra, 2),
        )
```

**Strategie di rate limiting per endpoint:**

| Endpoint | Strategia | Limite tipico | Motivazione |
|----------|-----------|---------------|-------------|
| `/login` | Per IP + username | 5 tentativi / 15 min | Anti brute-force |
| `/api/v1/*` | Per API key | 100 req / min | Protezione risorse |
| `/register` | Per IP | 3 registrazioni / ora | Anti bot |
| `/password-reset` | Per email | 3 richieste / ora | Anti enumeration |
| `/upload` | Per utente | 10 file / ora | Anti abuso storage |

**Header di risposta per rate limiting (RFC 6585 + draft IETF):**

```python
def aggiungi_header_rate_limit(response, risultato: RateLimitResult, limite: int):
    response.headers["X-RateLimit-Limit"] = str(limite)
    response.headers["X-RateLimit-Remaining"] = str(risultato.rimanenti)
    response.headers["X-RateLimit-Reset"] = str(int(time.time() + risultato.reset_tra_secondi))
    if not risultato.consentito:
        response.headers["Retry-After"] = str(int(risultato.reset_tra_secondi))
```

Il rate limiting applicativo deve essere combinato con il rate limiting infrastrutturale: il WAF o il reverse proxy bloccano attacchi volumetrici (migliaia di richieste al secondo), mentre il rate limiter applicativo gestisce abusi piu sottili che richiedono contesto semantico. La chiave del rate limiting deve includere informazioni sufficienti per evitare sia i falsi positivi (utenti legittimi bloccati dietro lo stesso NAT) sia i falsi negativi (attaccanti che ruotano IP). L'uso dell'API key o del token di sessione come chiave primaria, con fallback sull'IP per le richieste non autenticate, rappresenta un buon compromesso.

### Protezione API Authentication — JWT e Token Rotation

La gestione sicura dei token di autenticazione per le API richiede attenzione a diverse superfici di attacco: token theft, replay attack, token fixation e mancata revoca. Il pattern seguente implementa JWT con access token di breve durata e refresh token con rotazione automatica.

```python
import jwt
import secrets
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    access_scade: datetime
    refresh_scade: datetime


SECRET_KEY = "chiave-caricata-da-env-var"  # In produzione: os.environ["JWT_SECRET"]
ALGORITHM = "HS256"
ACCESS_TTL = timedelta(minutes=15)
REFRESH_TTL = timedelta(days=7)


def genera_token_pair(user_id: str, ruoli: list[str]) -> TokenPair:
    ora = datetime.now(timezone.utc)
    access_scade = ora + ACCESS_TTL
    refresh_scade = ora + REFRESH_TTL

    access_payload = {
        "sub": user_id,
        "roles": ruoli,
        "exp": access_scade,
        "iat": ora,
        "jti": secrets.token_hex(16),
        "type": "access",
    }
    refresh_payload = {
        "sub": user_id,
        "exp": refresh_scade,
        "iat": ora,
        "jti": secrets.token_hex(16),
        "type": "refresh",
    }

    return TokenPair(
        access_token=jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM),
        refresh_token=jwt.encode(refresh_payload, SECRET_KEY, algorithm=ALGORITHM),
        access_scade=access_scade,
        refresh_scade=refresh_scade,
    )
```

Il campo `jti` (JWT ID) e essenziale per la revoca: ogni token ha un identificativo unico che puo essere inserito in una blocklist Redis quando l'utente effettua il logout o quando viene rilevata un'attivita sospetta. La rotazione del refresh token a ogni utilizzo garantisce che un token rubato diventi inutilizzabile dopo il primo uso legittimo, riducendo la finestra di attacco.

---

## Dependency Review

Prima di aggiungere una nuova dipendenza al progetto, e necessario un processo di valutazione che consideri sicurezza, licenza, manutenzione e alternative.

### Audit Licenze

```bash
# pip-licenses genera report delle licenze di tutte le dipendenze
pip install pip-licenses
pip-licenses --format=json --output-file=licenze.json
pip-licenses --format=markdown --output-file=licenze.md
```

**Classificazione licenze:**

| Categoria | Licenze | Azione |
|-----------|---------|--------|
| Consentite | MIT, Apache-2.0, BSD-2/3-Clause, ISC, PSF-2.0, MPL-2.0 | Nessuna |
| Restrittive | GPL-3.0 (virale per linking) | Valutare impatto legale |
| Vietate | AGPL-3.0 (richiede rilascio codice), SSPL-1.0 (restrizioni SaaS) | Blocco |
| Sconosciute | UNKNOWN | Indagare manualmente |

### Segnali di Manutenzione

Indicatori da verificare prima di adottare una dipendenza:

| Segnale | Verde | Giallo | Rosso |
|---------|-------|--------|-------|
| Ultimo commit | < 3 mesi | 3-12 mesi | > 12 mesi |
| Issues aperte vs chiuse | Ratio sano | Accumulo | Solo aperte |
| Rilasci | Regolari | Sporadici | Nessuno da 1+ anno |
| Maintainer | Team/org | Singolo attivo | Singolo inattivo |
| Copertura test | > 80% | > 50% | Nessun test |
| Dipendenze transitive | Poche, note | Moderate | Molte, sconosciute |
| Security policy | SECURITY.md presente | Assente | Vulnerabilita ignorate |
| Downloads PyPI | Stabili/crescenti | Calanti | Quasi zero |

```bash
# Verifica rapida di un pacchetto con pip
pip show nome-pacchetto

# Informazioni da PyPI
curl -s https://pypi.org/pypi/nome-pacchetto/json | python -m json.tool | head -30

# Statistiche download (ultimi 30 giorni)
# pip install pypistats
# pypistats overall nome-pacchetto --last-month
```

### Valutazione Alternative

Checklist prima di adottare una nuova dipendenza:

- **Necessita:** la funzionalita e disponibile nella stdlib? Esiste gia una dipendenza nel progetto che la copre?
- **Sicurezza:** nessuna CVE critica aperta; ha SECURITY.md; rilasci di sicurezza tempestivi; licenza compatibile
- **Manutenzione:** ultimo rilascio < 6 mesi; maintainer multipli/org; CI/CD attiva; documentazione aggiornata
- **Impatto:** dipendenze transitive accettabili; dimensione ragionevole; compatibile con le versioni Python del progetto

---

## Troubleshooting

### Errori Comuni e Soluzioni

| Problema | Causa | Soluzione |
|----------|-------|-----------|
| `ssl.SSLCertVerificationError` | Certificato scaduto o CA non riconosciuta | Aggiornare `certifi`: `pip install --upgrade certifi`; verificare la data di sistema |
| `cryptography` non si installa | Manca il compilatore Rust o OpenSSL headers | `apt install build-essential libssl-dev libffi-dev`; aggiornare pip: `pip install --upgrade pip` |
| `bandit` segnala troppi falsi positivi | Configurazione troppo aggressiva | Creare `.bandit.yml` con `skips` per i test non applicabili; usare `# nosec` con giustificazione |
| `pip-audit` fallisce con timeout | Rete lenta o proxy aziendale | `pip-audit --timeout 60`; configurare `HTTP_PROXY`/`HTTPS_PROXY` |
| `Fernet.decrypt` lancia `InvalidToken` | Chiave sbagliata o token corrotto | Verificare che la chiave sia identica; controllare encoding (base64); verificare TTL se usato |
| `argon2.exceptions.HashingError` | Parametri di memoria troppo alti per il sistema | Ridurre `memory_cost`; verificare la RAM disponibile |
| `detect-secrets` blocca il commit | Falso positivo su stringa lunga | `detect-secrets audit .secrets.baseline` per marcare come falso positivo |
| `yaml.scanner.ScannerError` | YAML malformato | Validare con `yamllint`; usare `yaml.safe_load` (non `yaml.load`) |
| `secrets.compare_digest` TypeError | Tipi misti (str vs bytes) | Assicurarsi che entrambi gli argomenti siano `bytes` (usare `.encode()`) |
| Import error su `cryptography.hazmat` | Versione obsoleta della libreria | `pip install --upgrade cryptography`; verificare compatibilita OpenSSL |

### Debugging di Problemi TLS

```python
import ssl
import socket


def diagnostica_tls(hostname: str, porta: int = 443) -> dict:
    """Diagnostica problemi TLS con un server remoto."""
    risultato: dict = {}
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, porta), timeout=10) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                risultato["protocollo"] = ssock.version()
                risultato["cifrario"] = ssock.cipher()[0]
                risultato["scadenza"] = ssock.getpeercert()["notAfter"]
                risultato["tls_ok"] = True
    except ssl.SSLCertVerificationError as e:
        risultato["tls_ok"] = False
        risultato["errore"] = str(e)
    except ssl.SSLError as e:
        risultato["tls_ok"] = False
        risultato["errore"] = str(e)
    return risultato
```

---

## Esercizi

### Esercizio 1 — Token API con Rotazione (Livello: Intermedio)

Implementare un sistema di generazione e verifica di API token con supporto per la rotazione. Requisiti:
- Generare token con `secrets.token_urlsafe(32)` e prefisso identificativo
- Memorizzare l'hash SHA-256 del token (non il token in chiaro)
- Supportare token multipli attivi per utente
- Confronto timing-safe con `hmac.compare_digest`
- Scadenza configurabile per token

### Esercizio 2 — Scanner di Segreti Custom (Livello: Intermedio)

Scrivere uno scanner che cerca pattern di segreti nel codice sorgente. Requisiti:
- Regex per API key (pattern comuni: `sk-`, `pk_`, `ghp_`, `AKIA`)
- Regex per password hardcoded (`password = "..."`, `passwd`, `pwd`)
- Ignorare file in `.gitignore` e directory `venv`/`node_modules`
- Report con file, riga e tipo di segreto trovato
- Modalita baseline (ignora i finding gia noti)

### Esercizio 3 — Middleware di Sicurezza (Livello: Avanzato)

Creare un middleware FastAPI completo che implementi:
- Rate limiting per IP (usando un dizionario in-memory con cleanup periodico)
- Header di sicurezza completi (CSP con nonce, HSTS, X-Frame-Options)
- Logging strutturato degli eventi di sicurezza
- Blocco automatico di IP dopo N tentativi falliti

### Esercizio 4 — SBOM Analyzer (Livello: Avanzato)

Scrivere un tool che:
- Generi un SBOM CycloneDX dall'ambiente Python corrente
- Verifichi tutte le licenze contro una policy definita
- Identifichi dipendenze con piu di 12 mesi dall'ultimo rilascio
- Produca un report Markdown con le raccomandazioni
- Esca con codice di errore se ci sono violazioni critiche

### Esercizio 5 — Cifratura File con Key Derivation (Livello: Intermedio)

Implementare un tool CLI per cifrare/decifrare file con password. Requisiti:
- Derivazione chiave da password con PBKDF2 (600.000 iterazioni) o Argon2id
- Cifratura con AES-256-GCM (non CBC)
- Il file cifrato contiene: versione formato, salt, nonce, ciphertext, tag
- Verifica integrita alla decifratura
- Test unitari per cifratura, decifratura, password errata, file corrotto

---

## Letture e Riferimenti

### Standard e Specifiche

- **OWASP Top 10 (2021)** — [owasp.org/Top10](https://owasp.org/www-project-top-ten/) — lista delle 10 vulnerabilita web piu critiche
- **OWASP Cheat Sheet Series** — [cheatsheetseries.owasp.org](https://cheatsheetseries.owasp.org/) — guide pratiche per ogni categoria di vulnerabilita
- **OWASP Secure Headers Project** — header HTTP di sicurezza raccomandati
- **NIST SP 800-57** — raccomandazioni sulla gestione delle chiavi crittografiche
- **NIST SP 800-63B** — linee guida sulle password (digital identity)
- **NIST SP 800-38D** — specifiche AES-GCM
- **PEP 506** — Adding A Secrets Module To The Standard Library
- **PEP 458** — Secure PyPI downloads with signed repository metadata (TUF)
- **PEP 480** — Surviving a Compromise of PyPI: The Maximum Security Model
- **RFC 6749** — OAuth 2.0 Authorization Framework
- **RFC 7519** — JSON Web Token (JWT)

### Documentazione Librerie

- **cryptography** — [cryptography.io](https://cryptography.io/en/latest/) — documentazione ufficiale con tutorial e API reference
- **argon2-cffi** — [argon2-cffi.readthedocs.io](https://argon2-cffi.readthedocs.io/) — hashing password con Argon2
- **Bandit** — [bandit.readthedocs.io](https://bandit.readthedocs.io/) — analisi statica di sicurezza
- **pip-audit** — [github.com/pypa/pip-audit](https://github.com/pypa/pip-audit) — audit vulnerabilita dipendenze
- **CycloneDX Python** — [github.com/CycloneDX/cyclonedx-python](https://github.com/CycloneDX/cyclonedx-python) — generazione SBOM
- **sigstore-python** — [github.com/sigstore/sigstore-python](https://github.com/sigstore/sigstore-python) — firma keyless
- **detect-secrets** — [github.com/Yelp/detect-secrets](https://github.com/Yelp/detect-secrets) — prevenzione commit di segreti
- **Pydantic** — [docs.pydantic.dev](https://docs.pydantic.dev/) — validazione dati

### Libri

- Anderson, Ross — *Security Engineering* (3rd ed., 2020) — trattato completo sulla sicurezza dei sistemi
- Stuttard, Pinto — *The Web Application Hacker's Handbook* (2nd ed.) — reference per la sicurezza web
- McDonald, Malcolm — *Web Security for Developers* (No Starch Press) — introduzione pratica

---

## Cross-link

| Modulo | Collegamento |
|--------|-------------|
| 08 — Testing | Pattern di test per codice di sicurezza; mocking di `secrets` e `cryptography` |
| 09 — Type Hints e mypy | Typing rigoroso come livello di sicurezza; `Final`, `Literal` per costanti |
| 11 — Web Framework | Flask/FastAPI setup sicuro; middleware di sicurezza |
| 13 — REST API | Autenticazione JWT, OAuth 2.0, rate limiting su endpoint |
| 31 — Osservabilita | Logging strutturato di eventi di sicurezza; correlazione con trace_id |

---

## Glossario

| Termine | Definizione |
|---------|------------|
| **AES-GCM** | Advanced Encryption Standard in Galois/Counter Mode; cifratura autenticata che fornisce confidenzialita e integrita in un'unica operazione (NIST SP 800-38D) |
| **Argon2id** | Algoritmo di hashing password vincitore della Password Hashing Competition (2015); variante ibrida resistente a GPU e side-channel |
| **Bandit** | Strumento di analisi statica di sicurezza (SAST) per codice Python; identifica pattern di codice vulnerabile |
| **CSRF** | Cross-Site Request Forgery; attacco che forza un utente autenticato a eseguire azioni non intenzionali |
| **CSP** | Content Security Policy; header HTTP che controlla quali risorse il browser puo caricare |
| **CVE** | Common Vulnerabilities and Exposures; identificatore unico per vulnerabilita note |
| **CycloneDX** | Standard OWASP per Software Bill of Materials (SBOM) |
| **Fernet** | Ricetta di crittografia simmetrica della libreria `cryptography`; AES-128-CBC + HMAC-SHA256 |
| **HSTS** | HTTP Strict Transport Security; header che forza il browser a usare solo HTTPS |
| **KDF** | Key Derivation Function; funzione che trasforma una password in una chiave crittografica |
| **OIDC** | OpenID Connect; protocollo di autenticazione basato su OAuth 2.0 |
| **OSV** | Open Source Vulnerabilities; database di vulnerabilita open source gestito da Google |
| **OWASP** | Open Web Application Security Project; organizzazione che produce standard e strumenti per la sicurezza web |
| **PBKDF2** | Password-Based Key Derivation Function 2; KDF standardizzata in RFC 8018 |
| **PEP 458** | Python Enhancement Proposal per integrare TUF (The Update Framework) in PyPI |
| **PEP 480** | PEP complementare a 458 per la gestione delle chiavi crittografiche di TUF su PyPI |
| **pip-audit** | Strumento di audit delle dipendenze Python contro database di vulnerabilita |
| **SAST** | Static Application Security Testing; analisi di sicurezza del codice sorgente senza eseguirlo |
| **SBOM** | Software Bill of Materials; inventario formale dei componenti software |
| **Sigstore** | Infrastruttura di firma digitale keyless (Fulcio + Rekor) per artefatti software |
| **SSRF** | Server-Side Request Forgery; attacco in cui il server effettua richieste verso risorse interne |
| **SSTI** | Server-Side Template Injection; iniezione di codice nei template server-side |
| **Timing attack** | Attacco side-channel che sfrutta le differenze di tempo nella comparazione di stringhe |
| **Trusted Publishers** | Meccanismo PyPI basato su OIDC per pubblicare pacchetti senza token di lunga durata |
| **TUF** | The Update Framework; framework di sicurezza per sistemi di aggiornamento software |
| **XSS** | Cross-Site Scripting; iniezione di script malevoli nelle pagine web |

---

> **Nota finale:** la sicurezza non e uno stato da raggiungere ma un processo continuo. Le minacce evolvono costantemente, e con esse devono evolversi le difese. Investire nella formazione continua del team, seguire le pubblicazioni di OWASP, NIST e CERT, e mantenere una cultura della sicurezza in ogni fase del ciclo di sviluppo software.
