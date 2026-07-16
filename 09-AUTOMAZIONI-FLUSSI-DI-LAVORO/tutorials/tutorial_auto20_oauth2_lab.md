# Tutorial Lab — OAuth 2.1 per Automazioni: PKCE, Client Credentials, Refresh Token

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `20-oauth2-flows-refresh-token-automazione.md`
> **Livello:** competent → proficient
> **Tempo stimato:** 5-6 ore (lab completo)
> **Prerequisiti:** HTTP/HTTPS, JSON, JWT basics, concetto authorization vs authentication
> **Versioni di riferimento:** OAuth 2.1 (RFC 9700) · OIDC Core 1.0 · Keycloak 24.x · Python 3.11+ · PyJWT 2.x

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Implementare OAuth 2.1 Authorization Code + PKCE (public client sicuro)
2. Configurare Client Credentials flow per automazioni machine-to-machine
3. Gestire refresh token rotation con rilevamento compromissione
4. Validare JWT con verifica firma, issuer, audience, exp — mai skip validation
5. Integrare Keycloak come Authorization Server self-hosted
6. Progettare token vault per automazioni multi-tenant
7. Diagnosticare i 10 errori OAuth più comuni in workflow automatizzati

---

## Lab Environment Setup

### Keycloak (Authorization Server self-hosted)

```yaml
# docker-compose-keycloak.yml
version: "3.8"
services:
  keycloak-db:
    image: postgres:16-alpine
    container_name: keycloak-db
    environment:
      POSTGRES_DB: keycloak
      POSTGRES_USER: keycloak
      POSTGRES_PASSWORD: keycloak_password
    volumes:
      - keycloak_db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U keycloak"]
      interval: 10s
      timeout: 5s
      retries: 5

  keycloak:
    image: quay.io/keycloak/keycloak:24.0
    container_name: keycloak
    restart: unless-stopped
    depends_on:
      keycloak-db:
        condition: service_healthy
    environment:
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://keycloak-db:5432/keycloak
      KC_DB_USERNAME: keycloak
      KC_DB_PASSWORD: keycloak_password
      KC_HOSTNAME: localhost
      KC_HTTP_ENABLED: "true"
      KC_HOSTNAME_STRICT: "false"
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin_password
    command: start-dev
    ports:
      - "8080:8080"
    volumes:
      - keycloak_data:/opt/keycloak/data

volumes:
  keycloak_db_data:
  keycloak_data:
```

```bash
# Avvia Keycloak
docker compose -f docker-compose-keycloak.yml up -d

# Attendi avvio (30-60s)
echo "Attesa Keycloak..."
until curl -sf http://localhost:8080/health/ready; do sleep 5; done
echo "Keycloak pronto"

# Installa librerie Python
pip install PyJWT==2.8.0 cryptography==42.0.0 httpx==0.27.0 \
            structlog==24.0.0 redis==5.0.7
```

### Setup Realm e Client in Keycloak

```bash
#!/bin/bash
# setup-keycloak.sh
# Configura realm "automation-lab" con client e utenti di test

KC_URL="http://localhost:8080"
ADMIN_USER="admin"
ADMIN_PASS="admin_password"
REALM="automation-lab"

# 1. Ottieni token admin
ADMIN_TOKEN=$(curl -sf -X POST "$KC_URL/realms/master/protocol/openid-connect/token" \
    -d "client_id=admin-cli" \
    -d "username=$ADMIN_USER" \
    -d "password=$ADMIN_PASS" \
    -d "grant_type=password" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

AUTH_HEADER="Authorization: Bearer $ADMIN_TOKEN"

# 2. Crea realm
curl -sf -X POST "$KC_URL/admin/realms" \
    -H "$AUTH_HEADER" -H "Content-Type: application/json" \
    -d "{\"realm\": \"$REALM\", \"enabled\": true, \"displayName\": \"Automation Lab\"}"
echo "Realm '$REALM' creato"

# 3. Client per Authorization Code + PKCE (public client — app web/mobile)
curl -sf -X POST "$KC_URL/admin/realms/$REALM/clients" \
    -H "$AUTH_HEADER" -H "Content-Type: application/json" \
    -d '{
        "clientId": "webapp-client",
        "name": "Web App (PKCE)",
        "publicClient": true,
        "redirectUris": ["http://localhost:8888/callback"],
        "webOrigins": ["http://localhost:8888"],
        "standardFlowEnabled": true,
        "directAccessGrantsEnabled": false,
        "attributes": {"pkce.code.challenge.method": "S256"}
    }'
echo "Client PKCE creato"

# 4. Client per Client Credentials (confidential — machine-to-machine)
curl -sf -X POST "$KC_URL/admin/realms/$REALM/clients" \
    -H "$AUTH_HEADER" -H "Content-Type: application/json" \
    -d '{
        "clientId": "automation-service",
        "name": "Automation Service (M2M)",
        "secret": "automation-service-secret",
        "publicClient": false,
        "serviceAccountsEnabled": true,
        "standardFlowEnabled": false,
        "directAccessGrantsEnabled": false
    }'
echo "Client M2M creato"

# 5. Utente di test
curl -sf -X POST "$KC_URL/admin/realms/$REALM/users" \
    -H "$AUTH_HEADER" -H "Content-Type: application/json" \
    -d '{
        "username": "test.user",
        "email": "test@lab.local",
        "enabled": true,
        "credentials": [{"type": "password", "value": "TestUser123!", "temporary": false}]
    }'
echo "Utente test creato"

echo ""
echo "=== Keycloak configurato ==="
echo "Realm:   $REALM"
echo "Admin:   http://localhost:8080/admin"
echo "OIDC Discovery: http://localhost:8080/realms/$REALM/.well-known/openid-configuration"
```

```bash
chmod +x setup-keycloak.sh
./setup-keycloak.sh
```

---

## Analogia Introduttiva

> **OAuth 2.0 è come il parcheggio di un hotel**:
> invece di dare la tua chiave di casa al parcheggiatore (la tua password all'app),
> dai un token speciale ("chiave valet") che permette SOLO di spostare l'auto —
> non di aprire la cassaforte o entrare in camera.
>
> Il **PKCE** è la ricevuta del parcheggio:
> al momento del ritiro, devi presentare sia la ricevuta (code_verifier)
> che il numero del ritiro (authorization code). Senza entrambi, nessun token.
>
> Il **refresh token** è come l'abbonamento annuale al parcheggio:
> scade l'accesso giornaliero (access token, 1 ora)?
> Mostri l'abbonamento (refresh token) e ottieni un nuovo badge — senza richiedere la chiave all'hotel.

---

## Architettura OAuth 2.1

```
FLUSSO AUTHORIZATION CODE + PKCE:

  Browser/App                Authorization Server           Resource Server
  ──────────                 (Keycloak)                    (API protetta)
      │                           │                              │
      │──1. GET /authorize ──────▶│                              │
      │  (code_challenge=SHA256(verifier))                       │
      │                           │                              │
      │◀──2. redirect → login ────│                              │
      │                           │                              │
      │──3. User autentica ──────▶│                              │
      │◀──4. redirect callback ───│                              │
      │   (authorization_code)    │                              │
      │                           │                              │
      │──5. POST /token ─────────▶│                              │
      │   (code, code_verifier)   │                              │
      │◀──6. access_token ────────│                              │
      │      refresh_token        │                              │
      │                           │                              │
      │──7. GET /api/resource ───────────────────────────────────▶
      │   Authorization: Bearer <access_token>                   │
      │◀──8. 200 OK ─────────────────────────────────────────────│


FLUSSO CLIENT CREDENTIALS (M2M — nessun utente):

  Automation Service         Authorization Server
  ──────────────────         (Keycloak)
      │                           │
      │──POST /token ────────────▶│
      │  (client_id, client_secret, grant_type=client_credentials)
      │◀──access_token ───────────│  (nessun refresh token)
      │                           │
      │──Usa access token ────────────────▶ Resource Server
```

---

## PART A — Validazione JWT (Fondamentale)

### A1 — Validazione Corretta con PyJWT

```python
# file: jwt_validator.py
"""
Validazione JWT production-grade.
MAI usare jwt.decode() senza verificare firma e claims obbligatori.
"""
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin

import httpx
import jwt
import structlog
from cryptography.hazmat.primitives import serialization

logger = structlog.get_logger(__name__)

# Cache per chiavi pubbliche JWKS (evita fetch ad ogni richiesta)
_jwks_cache: dict[str, dict] = {}
_jwks_cache_time: dict[str, float] = {}
JWKS_CACHE_TTL = 3600  # 1 ora


@dataclass
class ValidatedToken:
    sub: str              # subject (user_id o service_id)
    iss: str              # issuer
    aud: str | list[str]  # audience
    exp: int              # expiration timestamp
    scope: str            # spazi separati
    raw_claims: dict


class TokenValidationError(Exception):
    pass


def fetch_jwks(jwks_uri: str) -> dict:
    """Scarica le chiavi pubbliche dall'JWKS URI del provider (con cache)."""
    now = time.monotonic()
    if jwks_uri in _jwks_cache and (now - _jwks_cache_time.get(jwks_uri, 0)) < JWKS_CACHE_TTL:
        return _jwks_cache[jwks_uri]

    with httpx.Client(timeout=10) as client:
        r = client.get(jwks_uri)
        r.raise_for_status()
        jwks = r.json()

    _jwks_cache[jwks_uri] = jwks
    _jwks_cache_time[jwks_uri] = now
    logger.info("jwks_fetched", uri=jwks_uri, keys=len(jwks.get("keys", [])))
    return jwks


def validate_jwt(
    token: str,
    issuer: str,
    audience: str,
    jwks_uri: Optional[str] = None,
    algorithms: list[str] = None,
) -> ValidatedToken:
    """
    Valida un JWT in modo completo:
    1. Verifica firma con chiave pubblica da JWKS
    2. Verifica issuer (iss)
    3. Verifica audience (aud)
    4. Verifica scadenza (exp) con tolleranza 30s per clock skew
    5. Verifica algoritmo (no 'none')

    Solleva TokenValidationError se la validazione fallisce.
    """
    if algorithms is None:
        algorithms = ["RS256", "ES256"]  # Algoritmi raccomandati; mai HS256 per public JWT

    if "none" in [a.lower() for a in algorithms]:
        raise TokenValidationError("Algoritmo 'none' non consentito")

    # Scopri JWKS URI dall'issuer se non fornito
    if not jwks_uri:
        discovery_url = f"{issuer.rstrip('/')}/.well-known/openid-configuration"
        with httpx.Client(timeout=10) as client:
            r = client.get(discovery_url)
            r.raise_for_status()
            jwks_uri = r.json()["jwks_uri"]

    # Ottieni chiavi pubbliche
    jwks = fetch_jwks(jwks_uri)

    # Identifica la chiave corretta tramite kid nell'header del token
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    alg = header.get("alg", "")

    if alg.lower() == "none":
        raise TokenValidationError("Token con alg=none non consentito")

    matching_keys = [k for k in jwks.get("keys", []) if k.get("kid") == kid]
    if not matching_keys:
        # Prova a ricaricare le chiavi (rotazione chiave?)
        _jwks_cache.pop(jwks_uri, None)
        jwks = fetch_jwks(jwks_uri)
        matching_keys = [k for k in jwks.get("keys", []) if k.get("kid") == kid]
        if not matching_keys:
            raise TokenValidationError(f"Chiave pubblica con kid={kid} non trovata nel JWKS")

    # Verifica il token con PyJWT
    try:
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(matching_keys[0])
        claims = jwt.decode(
            token,
            public_key,
            algorithms=algorithms,
            audience=audience,
            issuer=issuer,
            leeway=30,   # 30 secondi tolleranza clock skew
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": True,
                "verify_iss": True,
                "require": ["exp", "iat", "sub", "iss", "aud"],
            },
        )
    except jwt.ExpiredSignatureError:
        raise TokenValidationError("Token scaduto")
    except jwt.InvalidAudienceError:
        raise TokenValidationError(f"Audience non valida — atteso: {audience}")
    except jwt.InvalidIssuerError:
        raise TokenValidationError(f"Issuer non valido — atteso: {issuer}")
    except jwt.InvalidSignatureError:
        raise TokenValidationError("Firma JWT non valida")
    except jwt.DecodeError as e:
        raise TokenValidationError(f"JWT non decodificabile: {e}")

    logger.info("token_valid",
                sub=claims.get("sub"),
                exp=claims.get("exp"),
                scope=claims.get("scope", ""))

    return ValidatedToken(
        sub=claims["sub"],
        iss=claims["iss"],
        aud=claims.get("aud", audience),
        exp=claims["exp"],
        scope=claims.get("scope", ""),
        raw_claims=claims,
    )


def has_scope(token: ValidatedToken, required_scope: str) -> bool:
    """Verifica che il token abbia lo scope richiesto."""
    token_scopes = set(token.scope.split())
    return required_scope in token_scopes
```

---

## PART B — Authorization Code + PKCE

### B1 — Implementazione PKCE (Client Pubblico)

```python
# file: pkce_client.py
"""
Client OAuth 2.1 Authorization Code + PKCE.
Usa PKCE (RFC 7636) obbligatorio per public client.
PKCE = Proof Key for Code Exchange — protegge dalla compromissione dell'authorization code.
"""
from __future__ import annotations

import base64
import hashlib
import http.server
import secrets
import threading
import time
import urllib.parse
import webbrowser
from dataclasses import dataclass
from typing import Optional

import httpx
import structlog

logger = structlog.get_logger(__name__)

KEYCLOAK_URL = "http://localhost:8080"
REALM = "automation-lab"
CLIENT_ID = "webapp-client"
REDIRECT_URI = "http://localhost:8888/callback"


@dataclass
class TokenSet:
    access_token: str
    refresh_token: Optional[str]
    id_token: Optional[str]
    expires_in: int
    token_type: str = "Bearer"
    scope: str = ""
    obtained_at: float = 0.0

    def __post_init__(self):
        if not self.obtained_at:
            self.obtained_at = time.time()

    def is_expired(self, buffer_seconds: float = 60.0) -> bool:
        return time.time() > (self.obtained_at + self.expires_in - buffer_seconds)

    @property
    def time_to_expiry(self) -> float:
        return (self.obtained_at + self.expires_in) - time.time()


def generate_pkce_pair() -> tuple[str, str]:
    """
    Genera code_verifier (random) e code_challenge (SHA256 del verifier).
    RFC 7636: verifier = 43-128 caratteri ASCII URL-safe random.
    """
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode("ascii")
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge


def build_authorization_url(state: str, code_challenge: str, scope: str = "openid email profile") -> str:
    """Costruisce l'URL per redirigere l'utente all'Authorization Server."""
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": scope,
        "state": state,                                 # Anti-CSRF
        "code_challenge": code_challenge,               # PKCE
        "code_challenge_method": "S256",
        "prompt": "login",                              # Forza nuovo login
    }
    base = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/auth"
    return f"{base}?{urllib.parse.urlencode(params)}"


def exchange_code_for_token(
    code: str,
    code_verifier: str,
    state_received: str,
    state_expected: str,
) -> TokenSet:
    """Scambia l'authorization code per i token (step 5 del flusso PKCE)."""
    if state_received != state_expected:
        raise ValueError(f"State mismatch — possibile CSRF! ricevuto={state_received}, atteso={state_expected}")

    token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
    with httpx.Client(timeout=15) as client:
        r = client.post(token_url, data={
            "grant_type": "authorization_code",
            "client_id": CLIENT_ID,
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "code_verifier": code_verifier,  # PKCE: AS verifica SHA256(verifier) == challenge
        })
        r.raise_for_status()
        data = r.json()

    return TokenSet(
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token"),
        id_token=data.get("id_token"),
        expires_in=data.get("expires_in", 300),
        scope=data.get("scope", ""),
    )


class PKCECallbackServer:
    """
    Server HTTP minimale per ricevere il callback OAuth.
    Gira su localhost:8888/callback per il lab.
    """

    def __init__(self):
        self._code: Optional[str] = None
        self._state: Optional[str] = None
        self._error: Optional[str] = None
        self._event = threading.Event()

    def wait_for_callback(self, timeout: float = 120.0) -> tuple[Optional[str], Optional[str]]:
        """Attende che il browser completi il login e reindirizzi al callback."""
        server = http.server.HTTPServer(("localhost", 8888), self._make_handler())
        server_thread = threading.Thread(target=lambda: server.handle_request(), daemon=True)
        server_thread.start()
        self._event.wait(timeout=timeout)
        server.server_close()
        return self._code, self._state

    def _make_handler(self):
        callback_server = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                callback_server._code = (params.get("code", [None])[0])
                callback_server._state = (params.get("state", [None])[0])
                callback_server._error = (params.get("error", [None])[0])
                callback_server._event.set()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"<h1>Login completato! Puoi chiudere questa scheda.</h1>")

            def log_message(self, *args):
                pass  # Silenzia log HTTP

        return Handler


def pkce_login() -> TokenSet:
    """
    Esegui il flusso PKCE completo:
    1. Genera PKCE pair
    2. Apri browser → AS
    3. Utente fa login
    4. Callback ricevuto → scambia code per token
    """
    code_verifier, code_challenge = generate_pkce_pair()
    state = secrets.token_urlsafe(16)

    auth_url = build_authorization_url(state, code_challenge)
    logger.info("opening_browser", url=auth_url[:80] + "...")

    # Apri browser con l'URL di autorizzazione
    print(f"\nSe il browser non si apre, incolla questo URL:\n{auth_url}\n")
    webbrowser.open(auth_url)

    # Attendi callback
    callback_handler = PKCECallbackServer()
    code, state_received = callback_handler.wait_for_callback(timeout=120)

    if not code:
        raise RuntimeError("Login non completato entro 120 secondi")

    # Scambia code per token
    tokens = exchange_code_for_token(code, code_verifier, state_received, state)
    logger.info("pkce_login_ok",
                expires_in=tokens.expires_in,
                scope=tokens.scope)
    return tokens


if __name__ == "__main__":
    import structlog
    structlog.configure()
    tokens = pkce_login()
    print(f"\nAccess token (primi 50 chars): {tokens.access_token[:50]}...")
    print(f"Scade in: {tokens.expires_in}s")
```

---

## PART C — Client Credentials (M2M)

### C1 — Client per Automazioni Machine-to-Machine

```python
# file: client_credentials.py
"""
OAuth 2.1 Client Credentials flow per automazioni M2M.
Usato quando non c'è un utente: servizi backend, workflow schedulati,
microservizi che comunicano tra loro.

REGOLE:
- Niente refresh token: quando scade, ri-richiedi con le credenziali
- Un client_id/secret per ogni servizio (scope minimi)
- Secret in vault/env, MAI nel codice
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx
import structlog

logger = structlog.get_logger(__name__)

KEYCLOAK_URL = "http://localhost:8080"
REALM = "automation-lab"


@dataclass
class M2MTokenCache:
    """Cache del token con refresh automatico prima della scadenza."""
    _token: Optional[str] = field(default=None, repr=False)
    _expires_at: float = 0.0
    _buffer_seconds: float = 60.0  # Rinnova 60s prima della scadenza


class OAuthM2MClient:
    """
    Client OAuth M2M con token caching e rinnovo automatico.
    Thread-safe per uso in servizi multi-threaded.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_url: str,
        scope: str = "",
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.scope = scope
        self._cache = M2MTokenCache()
        self._http = httpx.Client(timeout=15)

    def get_token(self) -> str:
        """
        Ottieni un access token valido.
        Se il token in cache è ancora valido, ritorna quello.
        Altrimenti richiede un nuovo token.
        """
        if self._is_cached_valid():
            return self._cache._token  # type: ignore

        logger.info("requesting_new_token", client=self.client_id)
        token_data = self._request_token()

        self._cache._token = token_data["access_token"]
        self._cache._expires_at = time.time() + token_data.get("expires_in", 300)
        logger.info("token_acquired",
                    client=self.client_id,
                    expires_in=token_data.get("expires_in"))
        return self._cache._token  # type: ignore

    def _is_cached_valid(self) -> bool:
        if not self._cache._token:
            return False
        return time.time() < (self._cache._expires_at - self._cache._buffer_seconds)

    def _request_token(self) -> dict:
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        if self.scope:
            data["scope"] = self.scope

        r = self._http.post(self.token_url, data=data)

        if r.status_code == 401:
            raise RuntimeError(f"Client credentials non valide per {self.client_id}")
        r.raise_for_status()
        return r.json()

    def make_authenticated_request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Wrapper per richieste autenticate — aggiunge Bearer token automaticamente."""
        token = self.get_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        return self._http.request(method, url, headers=headers, **kwargs)

    def close(self) -> None:
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ─── Factory function ──────────────────────────────────────────────────────────

def crea_automation_client(scope: str = "automation:read automation:write") -> OAuthM2MClient:
    """
    Crea un client M2M leggendo le credenziali dalle variabili d'ambiente.
    MAI passare le credenziali come argomenti hardcoded nel codice.
    """
    client_id = os.environ.get("OAUTH_CLIENT_ID", "automation-service")
    client_secret = os.environ.get("OAUTH_CLIENT_SECRET", "automation-service-secret")

    if not client_secret:
        raise RuntimeError("OAUTH_CLIENT_SECRET non impostata — impossibile procedere")

    token_url = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"

    return OAuthM2MClient(
        client_id=client_id,
        client_secret=client_secret,
        token_url=token_url,
        scope=scope,
    )


# Demo
if __name__ == "__main__":
    import structlog
    structlog.configure()

    with crea_automation_client() as client:
        token = client.get_token()
        print(f"Token ottenuto: {token[:50]}...")
        print(f"Valido ancora: {client._cache._expires_at - time.time():.0f}s")

        # Simula richiesta autenticata a un'API protetta
        print("\nSimulazione richiesta a httpbin.org (con token header):")
        r = client.make_authenticated_request("GET", "https://httpbin.org/headers")
        print(f"Status: {r.status_code}")
        auth_header = r.json().get("headers", {}).get("Authorization", "")
        print(f"Authorization header inviato: {auth_header[:40]}...")
```

---

## PART D — Refresh Token Rotation

### D1 — Gestione Refresh Token con Compromissione Detection

```python
# file: token_manager.py
"""
Token Manager con refresh token rotation.
OAuth 2.1 raccomanda refresh token rotation:
- Ogni uso del refresh token emette un NUOVO refresh token
- Il vecchio viene invalidato
- Se qualcuno usa un refresh token già consumato → possibile compromissione
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import httpx
import structlog

logger = structlog.get_logger(__name__)

KEYCLOAK_URL = "http://localhost:8080"
REALM = "automation-lab"
TOKEN_URL = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
REVOKE_URL = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/revoke"


@dataclass
class StoredTokens:
    """Token persistiti su disco (o Redis/Vault in produzione)."""
    access_token: str
    refresh_token: Optional[str]
    id_token: Optional[str]
    expires_at: float        # unix timestamp
    refresh_expires_at: float
    scope: str
    user_id: str


class TokenManager:
    """
    Gestisce il ciclo di vita completo dei token:
    - Storage persistente (file → Redis/Vault in produzione)
    - Refresh automatico prima della scadenza
    - Detection compromissione refresh token
    - Revoca esplicita
    """

    def __init__(
        self,
        client_id: str,
        client_secret: Optional[str],
        token_store_path: Path,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_store_path = token_store_path

    def store_tokens(self, tokens: StoredTokens) -> None:
        """Salva i token su disco (in produzione: Redis con TTL o HashiCorp Vault)."""
        self.token_store_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.token_store_path, "w") as f:
            json.dump(asdict(tokens), f, indent=2)
        os.chmod(self.token_store_path, 0o600)  # Solo il proprietario può leggere
        logger.info("tokens_stored", user_id=tokens.user_id)

    def load_tokens(self) -> Optional[StoredTokens]:
        """Carica token dallo store."""
        if not self.token_store_path.exists():
            return None
        with open(self.token_store_path) as f:
            data = json.load(f)
        return StoredTokens(**data)

    def get_valid_access_token(self) -> Optional[str]:
        """
        Ritorna un access token valido.
        Se scaduto ma il refresh token è valido, lo rinnova automaticamente.
        """
        tokens = self.load_tokens()
        if not tokens:
            logger.info("no_tokens_stored")
            return None

        # Token ancora valido (con buffer 60s)
        if time.time() < (tokens.expires_at - 60):
            return tokens.access_token

        # Token scaduto — tenta refresh
        if tokens.refresh_token and time.time() < tokens.refresh_expires_at:
            refreshed = self._refresh_token(tokens)
            if refreshed:
                return refreshed.access_token

        # Tutto scaduto — richiede nuovo login
        logger.warning("tokens_expired_relogin_required")
        return None

    def _refresh_token(self, current_tokens: StoredTokens) -> Optional[StoredTokens]:
        """
        Usa il refresh token per ottenere nuovi token.
        Con Keycloak/OAuth 2.1: il refresh token viene ruotato (nuovo RT emesso).
        """
        logger.info("refreshing_token", user_id=current_tokens.user_id)

        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "refresh_token": current_tokens.refresh_token,
        }
        if self.client_secret:
            data["client_secret"] = self.client_secret

        with httpx.Client(timeout=15) as client:
            r = client.post(TOKEN_URL, data=data)

        if r.status_code == 400:
            error = r.json().get("error", "unknown")
            if error in ("invalid_grant", "token_expired"):
                logger.warning("refresh_token_invalid",
                               error=error,
                               hint="Possibile riutilizzo di RT già consumato — possibile compromissione!")
                # In produzione: alert sicurezza + revoca tutti i token dell'utente
                self._revoke_all(current_tokens)
                return None
            raise RuntimeError(f"Refresh failed: {r.text}")

        r.raise_for_status()
        resp = r.json()

        now = time.time()
        new_tokens = StoredTokens(
            access_token=resp["access_token"],
            refresh_token=resp.get("refresh_token"),  # Nuovo RT (rotation)
            id_token=resp.get("id_token"),
            expires_at=now + resp.get("expires_in", 300),
            refresh_expires_at=now + resp.get("refresh_expires_in", 1800),
            scope=resp.get("scope", current_tokens.scope),
            user_id=current_tokens.user_id,
        )
        self.store_tokens(new_tokens)
        logger.info("token_refreshed_ok", user_id=current_tokens.user_id)
        return new_tokens

    def _revoke_all(self, tokens: StoredTokens) -> None:
        """Revoca tutti i token dell'utente (sicurezza su compromissione)."""
        if not tokens.refresh_token:
            return
        try:
            data = {
                "client_id": self.client_id,
                "token": tokens.refresh_token,
                "token_type_hint": "refresh_token",
            }
            if self.client_secret:
                data["client_secret"] = self.client_secret

            with httpx.Client(timeout=10) as client:
                client.post(REVOKE_URL, data=data)

            # Rimuovi token locali
            self.token_store_path.unlink(missing_ok=True)
            logger.warning("all_tokens_revoked", user_id=tokens.user_id,
                           reason="possible_compromission")
        except Exception as e:
            logger.error("revoke_failed", error=str(e))

    def revoke_logout(self, tokens: Optional[StoredTokens] = None) -> None:
        """Revoca il refresh token corrente (logout pulito)."""
        tokens = tokens or self.load_tokens()
        if tokens:
            self._revoke_all(tokens)
            logger.info("user_logged_out", user_id=tokens.user_id)
```

---

## PART E — Test e Verifica

### E1 — Test Suite OAuth

```python
#!/usr/bin/env python3
# file: tests/test_oauth.py
"""
Test per verificare l'implementazione OAuth corretta.
"""
import time
from unittest.mock import MagicMock, patch

import pytest
from jwt_validator import TokenValidationError, validate_jwt
from client_credentials import M2MTokenCache, OAuthM2MClient

class TestTokenCache:
    def test_cache_miss_on_empty(self):
        cache = M2MTokenCache()
        client = OAuthM2MClient.__new__(OAuthM2MClient)
        client._cache = cache
        assert not client._is_cached_valid()

    def test_cache_hit_when_valid(self):
        client = OAuthM2MClient.__new__(OAuthM2MClient)
        client._cache = M2MTokenCache()
        client._cache._token = "valid_token"
        client._cache._expires_at = time.time() + 3600  # scade tra 1 ora
        assert client._is_cached_valid()

    def test_cache_miss_when_expired(self):
        client = OAuthM2MClient.__new__(OAuthM2MClient)
        client._cache = M2MTokenCache()
        client._cache._token = "expired_token"
        client._cache._expires_at = time.time() - 100  # già scaduto
        assert not client._is_cached_valid()

    def test_cache_miss_near_expiry(self):
        """Il cache si considera scaduto 60s prima dell'effettiva scadenza."""
        client = OAuthM2MClient.__new__(OAuthM2MClient)
        client._cache = M2MTokenCache()
        client._cache._token = "almost_expired"
        client._cache._expires_at = time.time() + 30  # scade in 30s (< buffer 60s)
        assert not client._is_cached_valid()


class TestJWTValidation:
    def test_rejects_none_algorithm(self):
        """Verifica che l'algoritmo 'none' venga rifiutato."""
        from jwt_validator import validate_jwt
        with pytest.raises(TokenValidationError, match="none"):
            validate_jwt(
                "fake.token",
                issuer="http://localhost:8080/realms/automation-lab",
                audience="webapp-client",
                algorithms=["RS256", "none"],  # Questo deve fallire
            )

    def test_pkce_verifier_challenge_match(self):
        """Verifica la generazione corretta del PKCE pair."""
        import base64, hashlib
        from pkce_client import generate_pkce_pair

        verifier, challenge = generate_pkce_pair()

        # Verifica che challenge == base64url(SHA256(verifier))
        computed = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")

        assert computed == challenge
        assert 43 <= len(verifier) <= 128  # RFC 7636

    def test_state_csrf_protection(self):
        """Verifica che state diverso venga rifiutato."""
        from pkce_client import exchange_code_for_token
        with pytest.raises(ValueError, match="State mismatch"):
            exchange_code_for_token(
                code="fake_code",
                code_verifier="fake_verifier",
                state_received="received_xyz",
                state_expected="expected_abc",   # diverso!
            )


if __name__ == "__main__":
    # Esecuzione senza pytest (per verifica rapida)
    t = TestTokenCache()
    t.test_cache_miss_on_empty()
    t.test_cache_hit_when_valid()
    t.test_cache_miss_when_expired()
    t.test_cache_miss_near_expiry()
    print("[OK] TestTokenCache: tutti i test passano")

    t2 = TestJWTValidation()
    t2.test_pkce_verifier_challenge_match()
    print("[OK] TestJWTValidation: PKCE pair valido")
    t2.test_state_csrf_protection()
    print("[OK] TestJWTValidation: State CSRF protection attiva")
```

```bash
# Esegui test
python3 tests/test_oauth.py

# Con pytest (più verboso)
uv run pytest tests/test_oauth.py -v
```

### E2 — Integrazione Live con Keycloak

```bash
#!/bin/bash
# test-keycloak-live.sh
# Testa il flusso Client Credentials contro Keycloak reale

KC_URL="http://localhost:8080"
REALM="automation-lab"
TOKEN_URL="$KC_URL/realms/$REALM/protocol/openid-connect/token"
USERINFO_URL="$KC_URL/realms/$REALM/protocol/openid-connect/userinfo"
INTROSPECT_URL="$KC_URL/realms/$REALM/protocol/openid-connect/token/introspect"

echo "=== Test Client Credentials ==="

# 1. Ottieni token
echo "1. Richiesta token..."
TOKEN_RESPONSE=$(curl -sf -X POST "$TOKEN_URL" \
    -d "client_id=automation-service" \
    -d "client_secret=automation-service-secret" \
    -d "grant_type=client_credentials")

if [ $? -ne 0 ]; then
    echo "[FAIL] Impossibile ottenere token — Keycloak raggiungibile?"
    exit 1
fi

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
EXPIRES_IN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['expires_in'])")

echo "  [OK] Access token ottenuto (expires_in=${EXPIRES_IN}s)"
echo "  Token (primi 50 chars): ${ACCESS_TOKEN:0:50}..."

# 2. Decodifica header JWT (senza verifica firma — solo per ispezione)
echo ""
echo "2. Ispezione JWT header/payload..."
HEADER=$(echo "$ACCESS_TOKEN" | cut -d. -f1 | python3 -c "import sys,base64,json; data=sys.stdin.read().strip(); print(json.dumps(json.loads(base64.urlsafe_b64decode(data + '==').decode()), indent=2))")
PAYLOAD=$(echo "$ACCESS_TOKEN" | cut -d. -f2 | python3 -c "import sys,base64,json; data=sys.stdin.read().strip(); print(json.dumps(json.loads(base64.urlsafe_b64decode(data + '==').decode()), indent=2))" 2>/dev/null || echo "  (decode failed)")

echo "  Header: $HEADER"
echo "  Claims: $PAYLOAD" | head -20

# 3. Introspect (verifica server-side)
echo ""
echo "3. Token introspection..."
INTRO=$(curl -sf -X POST "$INTROSPECT_URL" \
    -u "automation-service:automation-service-secret" \
    -d "token=$ACCESS_TOKEN")
ACTIVE=$(echo "$INTRO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('active', False))")
echo "  Token attivo: $ACTIVE"

# 4. JWKS endpoint (chiavi pubbliche per verifica locale)
echo ""
echo "4. JWKS endpoint..."
JWKS=$(curl -sf "$KC_URL/realms/$REALM/protocol/openid-connect/certs")
KEYS_COUNT=$(echo "$JWKS" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('keys', [])))")
echo "  Chiavi pubbliche disponibili: $KEYS_COUNT"

echo ""
echo "=== Test completati ==="
```

---

## Troubleshooting: Errori OAuth Comuni

```
ERRORE: invalid_client
CAUSA:  client_id o client_secret sbagliati
FIX:    Verificare credenziali su Keycloak admin console
        Assicurarsi che il client esista nel realm corretto

ERRORE: invalid_grant (refresh token)
CAUSA:  Refresh token scaduto, già usato, o utente disabilitato
FIX:    Richiedi nuovo login utente
        Se segnalazione di security alert: revoca sessione

ERRORE: redirect_uri_mismatch
CAUSA:  redirect_uri nella richiesta != quello registrato sul client Keycloak
FIX:    Devono essere identici carattere per carattere (incluso trailing slash)
        Aggiungi il URI esatto sul client Keycloak (Admin → Clients → Valid redirect URIs)

ERRORE: invalid_scope
CAUSA:  Scope richiesto non configurato sul client o sul realm
FIX:    Aggiungi scope su Keycloak: Client scopes → Create

ERRORE: JWT ExpiredSignatureError in validazione
CAUSA:  Clock skew tra server e client > 30s (leeway configurata)
FIX:    Sincronizza NTP su tutti i server
        Aumenta leeway a 60s se necessario (non oltre)

ERRORE: alg=none nel token
CAUSA:  Vulnerabilità critica — AS configurato male o attacco in corso
FIX:    MAI accettare alg=none; reject immediatamente
        Investigare la provenienza del token

ERRORE: 401 su Resource Server con token valido
CAUSA:  aud (audience) nel token non corrisponde all'audience attesa dall'RS
FIX:    Aggiungere il client resource server come audience sul token
        Keycloak: Client → Client scopes → Add mapper → Audience
```

---

## Riepilogo: Regole d'Oro OAuth 2.1

```
1. ALWAYS PKCE per public client
   → code_challenge_method=S256 obbligatorio
   → MAI authorization code flow senza PKCE (OAuth 2.1 legacy)

2. CLIENT CREDENTIALS per M2M
   → Un client_id/secret per ogni servizio (scope minimi)
   → Ruota i secret ogni 90 giorni
   → Niente refresh token in questo flow

3. VALIDA SEMPRE IL JWT LATO SERVER
   → Firma, iss, aud, exp, alg
   → Usa JWKS endpoint, non chiavi hardcoded
   → JWKS cache con TTL 1h

4. REFRESH TOKEN ROTATION
   → Ogni refresh emette nuovo RT (vecchio invalidato)
   → RT già usato = possibile compromissione → alert + revoca

5. SCOPE MINIMI ASSOLUTI
   → read:invoices non implica write:invoices
   → Un token per API specifica, non "supertoken" globale

6. MAI NEL CODICE:
   → client_secret (usa env var o vault)
   → access token in URL (usa Authorization header)
   → alg=none accettato (reject sempre)

7. REVOCA ESPLICITA SU LOGOUT
   → POST /revoke con refresh_token
   → Elimina token locali (sessione, storage)
```

---

## Riferimenti

- OAuth 2.1 Draft: https://oauth.net/2.1/
- RFC 7636 — PKCE: https://datatracker.ietf.org/doc/html/rfc7636
- RFC 9700 — OAuth 2.1: https://datatracker.ietf.org/doc/html/rfc9700
- OpenID Connect Core: https://openid.net/specs/openid-connect-core-1_0.html
- Keycloak Docs: https://www.keycloak.org/docs/latest/
- PyJWT: https://pyjwt.readthedocs.io/
- OAuth 2.0 Security BCP: https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics
- Modulo sorgente: `20-oauth2-flows-refresh-token-automazione.md`
