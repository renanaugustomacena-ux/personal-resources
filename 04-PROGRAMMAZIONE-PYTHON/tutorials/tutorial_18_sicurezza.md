# Tutorial 18 — Sicurezza in Python: Crittografia, JWT, OWASP

> **Companion a:** `18-sicurezza.md`
> **Scope:** hashlib, hmac, secrets, cryptography, JWT, SQL injection, XSS, OWASP Top 10
> **Prerequisiti:** `tutorial_11_web_framework.md`, `tutorial_12_database.md`
> **Durata stimata:** 16-20 ore
> **Stack:** Python 3.12+, cryptography 42+, PyJWT 2.x, passlib

---

## Mappa concettuale

```
Sicurezza in Python
│
├── Hash e HMAC
│   ├── hashlib — SHA-256, SHA-3, BLAKE2
│   ├── hmac — autenticazione messaggi
│   └── secrets — generazione sicura
│
├── Crittografia (libreria `cryptography`)
│   ├── Simmetrica
│   │   ├── AES-GCM — cifratura autenticata
│   │   ├── ChaCha20-Poly1305
│   │   └── Fernet — wrapper sicuro e facile
│   └── Asimmetrica
│       ├── RSA — cifratura, firma
│       └── Ed25519 / ECDSA — firma digitale
│
├── Password
│   ├── bcrypt / argon2 — hashing password
│   ├── passlib — wrapper multi-algoritmo
│   └── MAI MD5/SHA1 per password
│
├── JWT (JSON Web Token)
│   ├── Header.Payload.Signature
│   ├── HS256 (HMAC) / RS256 (RSA)
│   ├── Scadenza (exp), emittente (iss)
│   └── Refresh token pattern
│
├── OWASP Top 10 in Python
│   ├── SQL Injection → ORM/parametrizzazione
│   ├── XSS → escape output, CSP
│   ├── CSRF → token, SameSite cookie
│   ├── IDOR → autorizzazione per risorsa
│   └── Secrets → variabili ambiente, vault
│
└── Input validation
    ├── Pydantic — schema validation
    ├── Sanitizzazione — strip, encode
    └── Rate limiting — brute force protection
```

---

# Parte A — Hash, HMAC e secrets

---

## A1. Hashing sicuro

```python
import hashlib
import hmac as hmac_module
import secrets

# Hash di file o dati
def hash_sha256(dati: bytes) -> str:
    return hashlib.sha256(dati).hexdigest()

def hash_file(percorso: str) -> str:
    h = hashlib.sha256()
    with open(percorso, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

# BLAKE2b — più veloce di SHA-256, sicuro
def hash_blake2(dati: bytes, chiave: bytes | None = None) -> str:
    return hashlib.blake2b(dati, key=chiave, digest_size=32).hexdigest()

# HMAC — autenticazione messaggio (verifica integrità E autenticità)
def firma_hmac(chiave: bytes, messaggio: bytes) -> str:
    return hmac_module.new(chiave, messaggio, hashlib.sha256).hexdigest()

def verifica_hmac(chiave: bytes, messaggio: bytes, firma_attesa: str) -> bool:
    firma_calcolata = firma_hmac(chiave, messaggio)
    # compare_digest: resistente a timing attack
    return hmac_module.compare_digest(firma_calcolata, firma_attesa)

# Generazione valori sicuri
token = secrets.token_hex(32)          # 32 byte = 64 char esadecimali
token_url = secrets.token_urlsafe(32)  # safe per URL
api_key = secrets.token_hex(24)
codice_otp = secrets.randbelow(1_000_000)   # 6 cifre
```

> **Analogia:** Un hash è come un'impronta digitale — univoca per ogni input, impossibile invertire. HMAC è come un hash firmato con una chiave segreta: chiunque abbia la chiave può verificare che il messaggio non sia stato alterato. È ciò che usa Stripe per firmare i webhook: tu ricevi il payload + la firma HMAC, calcoli la tua firma con il secret condiviso, e le confronti.

---

## A2. Hashing password (bcrypt/Argon2)

```python
from passlib.context import CryptContext
from passlib.hash import argon2, bcrypt

# Argon2 — vincitore del Password Hashing Competition 2015
# Raccomandato per nuovi sistemi
argon2_hasher = argon2.using(
    time_cost=3,        # iterazioni
    memory_cost=65536,  # 64 MB
    parallelism=4,
    hash_len=32,
    salt_len=16,
)

def hash_password_argon2(password: str) -> str:
    return argon2_hasher.hash(password)

def verifica_password_argon2(password: str, hash_salvato: str) -> bool:
    try:
        return argon2_hasher.verify(hash_salvato, password)
    except Exception:
        return False

# bcrypt — alternativa consolidata
def hash_password_bcrypt(password: str, rounds: int = 12) -> str:
    return bcrypt.using(rounds=rounds).hash(password)

def verifica_password_bcrypt(password: str, hash_salvato: str) -> bool:
    try:
        return bcrypt.verify(password, hash_salvato)
    except Exception:
        return False

# passlib CryptContext — gestione multi-algoritmo e upgrade automatico
pwd_context = CryptContext(
    schemes=["argon2", "bcrypt"],
    deprecated="auto",   # upgrade automatico algoritmi vecchi
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verifica_password(password: str, hash_salvato: str) -> bool:
    return pwd_context.verify(password, hash_salvato)

def necessita_upgrade(hash_salvato: str) -> bool:
    return pwd_context.needs_update(hash_salvato)
```

---

# Parte B — Crittografia simmetrica e asimmetrica

---

## B1. AES-GCM: cifratura autenticata

```python
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64

def cifra_aes_gcm(chiave: bytes, testo_in_chiaro: bytes, dati_associati: bytes | None = None) -> bytes:
    """Cifra con AES-256-GCM (autenticato)."""
    nonce = os.urandom(12)   # 96 bit — OBBLIGATORIO unico per ogni cifratura
    aesgcm = AESGCM(chiave)
    ciphertext = aesgcm.encrypt(nonce, testo_in_chiaro, dati_associati)
    return nonce + ciphertext   # prependi nonce al ciphertext

def decifra_aes_gcm(chiave: bytes, dati_cifrati: bytes, dati_associati: bytes | None = None) -> bytes:
    """Decifra e verifica autenticità."""
    nonce, ciphertext = dati_cifrati[:12], dati_cifrati[12:]
    aesgcm = AESGCM(chiave)
    try:
        return aesgcm.decrypt(nonce, ciphertext, dati_associati)
    except Exception:
        raise ValueError("Decifratura fallita: dati corrotti o chiave errata")

# Fernet: wrapper sicuro per uso quotidiano
from cryptography.fernet import Fernet

def genera_chiave_fernet() -> bytes:
    return Fernet.generate_key()   # 32 byte base64url

def cifra_fernet(chiave: bytes, messaggio: str) -> str:
    f = Fernet(chiave)
    return f.encrypt(messaggio.encode()).decode()

def decifra_fernet(chiave: bytes, token: str) -> str:
    f = Fernet(chiave)
    return f.decrypt(token.encode()).decode()

# Esempio: cifrare dati sensibili a riposo
chiave = AESGCM.generate_key(bit_length=256)
dati_sensibili = b"Numero carta: 4111 1111 1111 1111"
cifrati = cifra_aes_gcm(chiave, dati_sensibili)
decifrati = decifra_aes_gcm(chiave, cifrati)
assert decifrati == dati_sensibili
```

---

## B2. RSA e Ed25519: firma digitale

```python
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

def genera_coppia_ed25519() -> tuple[bytes, bytes]:
    """Genera chiave privata/pubblica Ed25519."""
    privata = Ed25519PrivateKey.generate()
    pubblica = privata.public_key()

    privata_pem = privata.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(b"passphrase"),
    )
    pubblica_pem = pubblica.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return privata_pem, pubblica_pem

def firma_ed25519(chiave_privata_pem: bytes, messaggio: bytes, passphrase: bytes) -> bytes:
    from cryptography.hazmat.primitives.serialization import load_pem_private_key
    privata = load_pem_private_key(chiave_privata_pem, password=passphrase)
    return privata.sign(messaggio)

def verifica_ed25519(chiave_pubblica_pem: bytes, messaggio: bytes, firma: bytes) -> bool:
    from cryptography.hazmat.primitives.serialization import load_pem_public_key
    from cryptography.exceptions import InvalidSignature
    pubblica = load_pem_public_key(chiave_pubblica_pem)
    try:
        pubblica.verify(firma, messaggio)
        return True
    except InvalidSignature:
        return False
```

---

# Parte C — JWT e autenticazione

---

## C1. JWT con PyJWT

```python
import jwt
import time
from datetime import datetime, timedelta, timezone

SECRET_KEY = "chiave-segreta-molto-lunga-cambia-in-produzione"
ALGORITHM = "HS256"

def crea_access_token(
    utente_id: int,
    email: str,
    ruoli: list[str],
    scadenza_minuti: int = 60,
) -> str:
    """Crea JWT access token."""
    ora = datetime.now(timezone.utc)
    payload = {
        "sub": str(utente_id),
        "email": email,
        "roles": ruoli,
        "iat": ora,
        "exp": ora + timedelta(minutes=scadenza_minuti),
        "jti": __import__("secrets").token_hex(16),   # JWT ID univoco
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verifica_access_token(token: str) -> dict:
    """Verifica e decodifica JWT, lancia eccezione se non valido."""
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"require": ["exp", "iat", "sub"]},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token scaduto")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Token non valido: {e}")

def crea_refresh_token(utente_id: int) -> str:
    """Refresh token — scadenza lunga, un solo scopo: rinnovo access token."""
    ora = datetime.now(timezone.utc)
    payload = {
        "sub": str(utente_id),
        "type": "refresh",
        "iat": ora,
        "exp": ora + timedelta(days=30),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# Pattern refresh token rotation
_token_revocati: set[str] = set()

def rinnova_access_token(refresh_token: str) -> tuple[str, str]:
    """Rinnova access token, invalida il refresh token usato."""
    payload = verifica_access_token(refresh_token)
    if payload.get("type") != "refresh":
        raise ValueError("Non è un refresh token")
    jti = payload.get("jti", "")
    if jti in _token_revocati:
        raise ValueError("Refresh token già usato (possibile furto)")
    if jti:
        _token_revocati.add(jti)   # invalida il vecchio
    utente_id = int(payload["sub"])
    nuovo_access = crea_access_token(utente_id, "", [])
    nuovo_refresh = crea_refresh_token(utente_id)
    return nuovo_access, nuovo_refresh
```

---

# Parte D — OWASP Top 10 in pratica

---

## D1. SQL Injection — prevenzione

```python
# SBAGLIATO: SQL injection!
def login_vulnerabile(conn, username: str, password: str) -> bool:
    query = f"SELECT * FROM utenti WHERE username='{username}' AND password='{password}'"
    # Input: username = "admin'--"  → autentica senza password!
    cursor = conn.execute(query)
    return cursor.fetchone() is not None

# CORRETTO: parametrizzazione
def login_sicuro(conn, username: str, password_hash: str) -> bool:
    cursor = conn.execute(
        "SELECT password_hash FROM utenti WHERE username = ?",
        (username,),   # parametro separato
    )
    row = cursor.fetchone()
    if row is None:
        return False
    import hmac
    return hmac.compare_digest(row[0], password_hash)

# SQLAlchemy — ORM protegge automaticamente
from sqlalchemy import text
def query_orm_sicura(session, username: str) -> object:
    # Parametrizzato automaticamente dall'ORM
    from app.models import Utente
    from sqlalchemy import select
    stmt = select(Utente).where(Utente.username == username)
    return session.execute(stmt).scalar_one_or_none()

# Per SQL raw — usa :param
def query_raw_sicura(session, min_eta: int) -> list:
    result = session.execute(
        text("SELECT * FROM utenti WHERE eta >= :min_eta"),
        {"min_eta": min_eta},
    )
    return list(result)
```

---

## D2. XSS, CSRF, validazione input

```python
import html
from pydantic import BaseModel, Field, field_validator
import re

# XSS — escape sempre l'output HTML
def escape_html(testo: str) -> str:
    return html.escape(testo, quote=True)

# NON fare: f"<p>{commento_utente}</p>"
# FARE:
def render_commento(commento: str) -> str:
    return f"<p>{escape_html(commento)}</p>"

# Validazione input rigorosa con Pydantic
class RegistrazioneUtente(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_\-]+$")
    email: str = Field(max_length=200)
    password: str = Field(min_length=8, max_length=100)

    @field_validator("email")
    @classmethod
    def valida_email(cls, v: str) -> str:
        pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError("Email non valida")
        return v.lower()

    @field_validator("password")
    @classmethod
    def valida_password(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password deve contenere almeno una maiuscola")
        if not re.search(r"\d", v):
            raise ValueError("Password deve contenere almeno un numero")
        if not re.search(r"[!@#$%^&*]", v):
            raise ValueError("Password deve contenere almeno un carattere speciale")
        return v

# CSRF Token con FastAPI
import secrets
from fastapi import FastAPI, Request, HTTPException, Cookie

app = FastAPI()

def genera_csrf_token() -> str:
    return secrets.token_urlsafe(32)

@app.get("/form")
async def mostra_form(request: Request) -> dict:
    token = genera_csrf_token()
    # In produzione: salvare in session store
    return {"csrf_token": token}

@app.post("/form/submit")
async def processa_form(
    request: Request,
    csrf_token: str | None = None,
) -> dict:
    # Verifica token CSRF
    body = await request.json()
    token_inviato = body.get("csrf_token", "")
    token_atteso = csrf_token or ""   # da cookie/session
    if not secrets.compare_digest(token_inviato, token_atteso):
        raise HTTPException(403, "CSRF token non valido")
    return {"ok": True}
```

---

## D3. Rate limiting e brute force protection

```python
import time
from collections import defaultdict
from fastapi import FastAPI, Request, HTTPException

app = FastAPI()

class RateLimiterMemoria:
    def __init__(self, max_tentativi: int = 5, finestra_sec: float = 300.0) -> None:
        self._tentativi: dict[str, list[float]] = defaultdict(list)
        self._max = max_tentativi
        self._finestra = finestra_sec

    def controlla(self, chiave: str) -> None:
        ora = time.monotonic()
        self._tentativi[chiave] = [
            t for t in self._tentativi[chiave]
            if ora - t < self._finestra
        ]
        if len(self._tentativi[chiave]) >= self._max:
            raise HTTPException(
                status_code=429,
                detail=f"Troppi tentativi. Riprova tra {self._finestra / 60:.0f} minuti.",
                headers={"Retry-After": str(int(self._finestra))},
            )
        self._tentativi[chiave].append(ora)

rate_limiter = RateLimiterMemoria(max_tentativi=5, finestra_sec=300)

@app.post("/login")
async def login(request: Request, dati: dict) -> dict:
    ip = request.client.host if request.client else "unknown"
    rate_limiter.controlla(f"login:{ip}")

    username = dati.get("username", "")
    rate_limiter.controlla(f"login:user:{username}")

    # ... logica autenticazione
    return {"token": "..."}
```

---

# Parte E — Riepilogo

## Regole d'oro sicurezza Python

| Regola | Come applicarla |
|---|---|
| Mai MD5/SHA1 per password | Usare bcrypt o Argon2 |
| Mai concatenare SQL | ORM o parametri `?` / `:nome` |
| Mai secrets nel codice | `os.environ` o secrets manager |
| Sempre escape output HTML | `html.escape()` o template engine |
| Sempre HTTPS in produzione | TLS 1.2+ obbligatorio |
| Timing-safe compare | `hmac.compare_digest()` sempre |
| Token casuali sicuri | `secrets.token_hex()` mai `random` |
| JWT con scadenza breve | Access: 15-60 min, Refresh: 7-30 gg |
| Rate limiting su auth | Max 5 tentativi per 5 minuti |
| Log senza PII | Mai password, carte, token in log |

## Prossimi passi

- `tutorial_22_clean_code.md` — principi di qualità del codice
- `tutorial_27_ci_cd.md` — security scanning in CI/CD pipeline
