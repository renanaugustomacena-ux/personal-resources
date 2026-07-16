# Tutorial Lab — Integrazione API: Client HTTP, Pagination e Rate Limiting

> **Campo di studio:** 09-AUTOMAZIONI-FLUSSI-DI-LAVORO
> **Modulo sorgente:** `04-integrazione-api.md`
> **Livello:** beginner → intermediate
> **Tempo stimato:** 2-3 ore (lab completo)
> **Prerequisiti:** HTTP/REST base, Python async/await, JSON
> **Versioni di riferimento:** Python 3.11+ · httpx 0.27.x · respx 0.21.x (test)

---

## Obiettivi del Lab

Al termine di questo tutorial saprai:

1. Costruire un client HTTP asincrono robusto con httpx
2. Implementare pagination cursor-based e page-based
3. Gestire rate limiting (429 Too Many Requests) con backoff automatico
4. Autenticare richieste: API Key, OAuth 2.0 Bearer, Basic Auth
5. Testare client HTTP con mock server (respx) senza dipendenze esterne
6. Gestire timeout, retry e error handling in modo production-grade

---

## Lab Environment Setup

```bash
# Prerequisiti
python3 --version   # 3.11+

# Python deps
pip install \
  httpx==0.27.0 \
  respx==0.21.1 \
  tenacity==9.0.0 \
  pydantic==2.7.0 \
  pytest==8.2.0 \
  pytest-asyncio==0.23.7

# Struttura progetto
mkdir -p api-lab/{client,auth,pagination,tests,mock_server}
cd api-lab
```

---

## Analogia Introduttiva

> **Un client HTTP è come un fattorino che consegna e ritira pacchi**:
> va all'indirizzo giusto (URL), suona il campanello (richiesta HTTP),
> aspetta la risposta (timeout), e torna con il pacco (response body).
>
> Senza gestione errori: se il citofono è guasto,
> il fattorino aspetta all'infinito (hang) o torna a casa subito (errore).
>
> Con retry + backoff: torna dopo 1 minuto, poi 2, poi 4 —
> come un buon fattorino che non si arrende al primo tentativo.
>
> Il **Rate Limiting** è il portiere del palazzo:
> "un fattorino ogni 10 secondi, non di più".
> Se ne arrivano 10 in un secondo (burst), il portiere dice
> `429 Too Many Requests` — aspetta il tuo turno.
> Un client robusto legge l'header `Retry-After` e aspetta esattamente
> quel numero di secondi prima di riprovare.

---

## Architettura del Lab

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CLIENT HTTP STACK                                  │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    ApiClient                                  │    │
│  │                                                               │    │
│  │  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │    │
│  │  │  Auth   │  │ RateLimit│  │  Retry   │  │ Pagination │  │    │
│  │  │ Middleware│  │Middleware│  │Middleware│  │  Iterator  │  │    │
│  │  └────┬────┘  └────┬─────┘  └────┬─────┘  └─────┬──────┘  │    │
│  └───────┼────────────┼─────────────┼───────────────┼──────────┘    │
│          │            │             │               │                 │
│          ▼            ▼             ▼               ▼                 │
│       httpx.AsyncClient (pool HTTP/1.1 + HTTP/2)                     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTPS
                    ┌──────────▼──────────┐
                    │   EXTERNAL API      │
                    │  GET /v1/ordini     │
                    │  POST /v1/pagamenti │
                    │  → 200 / 429 / 503  │
                    └─────────────────────┘
```

---

## PART A — Client HTTP Base

### A1 — Client Strutturato con httpx

```python
#!/usr/bin/env python3
# file: client/api_client.py
"""
Client HTTP production-grade con:
- Connection pool riutilizzabile
- Timeout configurabili (connect + read + write)
- Auth middleware
- Retry automatico su errori transitori
- Logging strutturato delle richieste
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional, AsyncIterator
from contextlib import asynccontextmanager

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
    before_sleep_log,
)

logger = logging.getLogger(__name__)


# ─── Configurazione ───────────────────────────────────────────────────────────

@dataclass
class ApiClientConfig:
    """Configurazione del client API."""
    base_url: str
    timeout_connect_s: float = 5.0
    timeout_read_s: float = 30.0
    timeout_write_s: float = 10.0
    max_retries: int = 3
    retry_backoff_initial: float = 1.0
    retry_backoff_max: float = 30.0
    max_connections: int = 10
    http2: bool = True  # HTTP/2 per multiplexing su stessa connessione


# ─── Errori classificati ─────────────────────────────────────────────────────

class ApiError(Exception):
    """Errore base per chiamate API."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class RetriableApiError(ApiError):
    """Errore transitorio — può essere ritentato."""


class NonRetriableApiError(ApiError):
    """Errore permanente — non ritentare."""


class RateLimitError(RetriableApiError):
    """429 Too Many Requests."""
    def __init__(self, retry_after_s: float = 60.0):
        super().__init__(f"Rate limit: riprova tra {retry_after_s}s")
        self.retry_after_s = retry_after_s


def classifica_errore(response: httpx.Response) -> None:
    """Solleva l'eccezione appropriata in base allo status code."""
    status = response.status_code
    
    if status == 429:
        retry_after = float(response.headers.get("Retry-After", 60))
        raise RateLimitError(retry_after_s=retry_after)
    
    if status in {500, 502, 503, 504}:
        raise RetriableApiError(
            f"Server error: {status} {response.text[:100]}",
            status_code=status
        )
    
    if 400 <= status < 500:
        raise NonRetriableApiError(
            f"Client error: {status} {response.text[:200]}",
            status_code=status
        )
    
    # 2xx: nessuna eccezione


# ─── Rate Limiter (Token Bucket) ─────────────────────────────────────────────

@dataclass
class TokenBucketLimiter:
    """
    Token Bucket rate limiter.
    Garantisce max `rate` richieste per `period_s` secondi.
    """
    rate: float          # Richieste per secondo (es. 10.0)
    burst: float = 1.0   # Max burst (default: no burst)
    
    _tokens: float = field(init=False, default=0.0)
    _last_refill: float = field(init=False, default=0.0)
    _lock: asyncio.Lock = field(init=False, default_factory=asyncio.Lock)

    def __post_init__(self):
        self._tokens = self.burst
        self._last_refill = time.monotonic()

    async def acquire(self) -> None:
        """Aspetta finché non c'è un token disponibile."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(self.burst, self._tokens + elapsed * self.rate)
            self._last_refill = now
            
            if self._tokens >= 1.0:
                self._tokens -= 1.0
            else:
                wait_time = (1.0 - self._tokens) / self.rate
                await asyncio.sleep(wait_time)
                self._tokens = 0.0


# ─── Client principale ───────────────────────────────────────────────────────

class ApiClient:
    """
    Client HTTP asincrono production-grade.
    
    Uso:
        async with ApiClient(config) as client:
            response = await client.get("/v1/ordini")
    """

    def __init__(
        self,
        config: ApiClientConfig,
        auth_header: Optional[dict[str, str]] = None,
        rate_limiter: Optional[TokenBucketLimiter] = None,
    ):
        self.config = config
        self._default_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **(auth_header or {}),
        }
        self._rate_limiter = rate_limiter
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "ApiClient":
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url,
            headers=self._default_headers,
            timeout=httpx.Timeout(
                connect=self.config.timeout_connect_s,
                read=self.config.timeout_read_s,
                write=self.config.timeout_write_s,
            ),
            limits=httpx.Limits(
                max_connections=self.config.max_connections,
                max_keepalive_connections=self.config.max_connections,
            ),
            http2=self.config.http2,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        """
        Esegue una richiesta con rate limiting e retry automatico.
        """
        if self._rate_limiter:
            await self._rate_limiter.acquire()
        
        start = time.monotonic()
        
        try:
            async for attempt in AsyncRetrying(
                retry=retry_if_exception_type(RetriableApiError),
                stop=stop_after_attempt(self.config.max_retries),
                wait=wait_exponential_jitter(
                    initial=self.config.retry_backoff_initial,
                    max=self.config.retry_backoff_max,
                ),
                before_sleep=before_sleep_log(logger, logging.WARNING),
                reraise=True,
            ):
                with attempt:
                    response = await self._client.request(method, path, **kwargs)
                    
                    logger.debug(
                        "HTTP %s %s → %d (%.0fms)",
                        method, path, response.status_code,
                        (time.monotonic() - start) * 1000
                    )
                    
                    classifica_errore(response)  # Solleva se errore
                    return response
        
        except RateLimitError as e:
            # Per rate limit: aspetta esattamente Retry-After prima di ritentare
            logger.warning("Rate limit hit — aspetto %.1fs", e.retry_after_s)
            await asyncio.sleep(e.retry_after_s)
            return await self._request(method, path, **kwargs)
        
        except httpx.TimeoutException as e:
            raise RetriableApiError(f"Timeout: {e}") from e
        
        except httpx.ConnectError as e:
            raise RetriableApiError(f"Connection error: {e}") from e

    async def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self._request("GET", path, **kwargs)

    async def post(self, path: str, json: Optional[dict] = None, **kwargs: Any) -> httpx.Response:
        return await self._request("POST", path, json=json, **kwargs)

    async def put(self, path: str, json: Optional[dict] = None, **kwargs: Any) -> httpx.Response:
        return await self._request("PUT", path, json=json, **kwargs)

    async def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        return await self._request("DELETE", path, **kwargs)
```

---

## PART B — Pagination

### B1 — Pagination Cursor-Based e Page-Based

```python
#!/usr/bin/env python3
# file: pagination/paginator.py
"""
Pagination iterator per API che usano cursor o page/offset.

Cursor-based (GitHub, Stripe, Cursor DB):
  GET /v1/ordini?limit=100&cursor=eyJpZCI6MTAwfQ==
  Response: {"data": [...], "next_cursor": "eyJpZCI6MjAwfQ==", "has_more": true}
  Vantaggio: stabile su dataset che cambiano

Page-based (classico, REST semplice):
  GET /v1/ordini?page=1&per_page=50
  Response: {"data": [...], "total_pages": 5, "current_page": 1}
  Svantaggio: instabile se il dataset cambia durante la paginazione
"""
from __future__ import annotations

import asyncio
import logging
from typing import AsyncIterator, Optional, Any

from client.api_client import ApiClient

logger = logging.getLogger(__name__)


async def pagina_cursor(
    client: ApiClient,
    path: str,
    params: Optional[dict] = None,
    page_size: int = 100,
    cursor_field: str = "next_cursor",
    data_field: str = "data",
    has_more_field: str = "has_more",
    max_pages: Optional[int] = None,
) -> AsyncIterator[dict]:
    """
    Itera su tutte le pagine di una API cursor-based.
    
    Yield singoli oggetti (non pagine intere).
    
    Example:
        async for ordine in pagina_cursor(client, "/v1/ordini"):
            processa(ordine)
    """
    cursor: Optional[str] = None
    pagine_recuperate = 0
    oggetti_totali = 0
    
    while True:
        # Costruisci parametri
        request_params = {**(params or {}), "limit": page_size}
        if cursor:
            request_params["cursor"] = cursor
        
        response = await client.get(path, params=request_params)
        data = response.json()
        
        items = data.get(data_field, [])
        pagine_recuperate += 1
        oggetti_totali += len(items)
        
        logger.debug(
            "Pagina %d: %d oggetti (cursor=%s)",
            pagine_recuperate, len(items), cursor
        )
        
        for item in items:
            yield item
        
        # Controlla se ci sono altre pagine
        has_more = data.get(has_more_field, False)
        cursor = data.get(cursor_field)
        
        if not has_more or not cursor:
            logger.info(
                "Paginazione completata: %d pagine, %d oggetti totali",
                pagine_recuperate, oggetti_totali
            )
            break
        
        if max_pages and pagine_recuperate >= max_pages:
            logger.warning("Raggiunto limite max_pages=%d", max_pages)
            break


async def pagina_offset(
    client: ApiClient,
    path: str,
    params: Optional[dict] = None,
    page_size: int = 50,
    page_field: str = "page",
    data_field: str = "data",
    total_field: str = "total",
    max_pages: Optional[int] = None,
) -> AsyncIterator[dict]:
    """
    Itera su tutte le pagine di una API page/offset-based.
    """
    page = 1
    totale: Optional[int] = None
    oggetti_visti = 0
    
    while True:
        request_params = {**(params or {}), page_field: page, "per_page": page_size}
        
        response = await client.get(path, params=request_params)
        data = response.json()
        
        items = data.get(data_field, [])
        if totale is None:
            totale = data.get(total_field, 0)
        
        for item in items:
            yield item
        
        oggetti_visti += len(items)
        logger.debug("Pagina %d/%d: %d oggetti", page, 
                     (totale // page_size + 1) if totale else "?", len(items))
        
        if not items or oggetti_visti >= (totale or 0):
            break
        if max_pages and page >= max_pages:
            break
        
        page += 1


async def raccoglie_tutto(iterator: AsyncIterator[dict]) -> list[dict]:
    """Raccoglie tutti gli oggetti da un async iterator in una lista."""
    return [item async for item in iterator]


# ─── Demo ─────────────────────────────────────────────────────────────────────

async def demo_paginazione():
    """Demo con mock dell'API (usa respx per il test reale)."""
    print("\n=== DEMO PAGINAZIONE ===")
    print("Per testare con un'API reale, usa ApiClient con base_url vera")
    print("Per test unitari: usa respx per mockare le risposte HTTP")
    
    # Simula struttura risposta cursor-based
    pagine_mock = [
        {"data": [{"id": i} for i in range(1, 101)], "next_cursor": "cursor_101", "has_more": True},
        {"data": [{"id": i} for i in range(101, 201)], "next_cursor": "cursor_201", "has_more": True},
        {"data": [{"id": i} for i in range(201, 251)], "next_cursor": None, "has_more": False},
    ]
    
    print("\nSimulazione paginazione cursor-based:")
    print(f"  Pagina 1: {len(pagine_mock[0]['data'])} oggetti + cursor")
    print(f"  Pagina 2: {len(pagine_mock[1]['data'])} oggetti + cursor")
    print(f"  Pagina 3: {len(pagine_mock[2]['data'])} oggetti + nessun cursor (fine)")
    print(f"  Totale: {sum(len(p['data']) for p in pagine_mock)} oggetti")


if __name__ == "__main__":
    asyncio.run(demo_paginazione())
```

---

## PART C — Autenticazione

### C1 — Strategie di Autenticazione

```python
#!/usr/bin/env python3
# file: auth/auth_strategies.py
"""
Strategie di autenticazione per API esterne.
Ogni strategia ritorna un dict di header da aggiungere alle richieste.
"""
from __future__ import annotations

import base64
import os
import time
import logging
from dataclasses import dataclass, field
from typing import Optional
import threading

import httpx

logger = logging.getLogger(__name__)


# ─── 1. API Key ───────────────────────────────────────────────────────────────

def auth_api_key(
    api_key: str,
    header_name: str = "X-API-Key",
) -> dict[str, str]:
    """
    Autenticazione con API Key nell'header.
    Usato da: Stripe, SendGrid, molte API SaaS italiane.
    """
    return {header_name: api_key}


def auth_api_key_bearer(api_key: str) -> dict[str, str]:
    """
    API Key come Bearer token.
    Usato da: OpenAI, Anthropic, molte AI API.
    """
    return {"Authorization": f"Bearer {api_key}"}


# ─── 2. Basic Auth ────────────────────────────────────────────────────────────

def auth_basic(username: str, password: str) -> dict[str, str]:
    """
    HTTP Basic Authentication.
    Usato da: API legacy, Jenkins, alcune API REST banking italiane.
    SEMPRE over HTTPS — mai in chiaro.
    """
    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


# ─── 3. OAuth 2.0 Bearer ─────────────────────────────────────────────────────

@dataclass
class OAuthToken:
    """Token OAuth 2.0 con gestione scadenza."""
    access_token: str
    expires_at: float  # Unix timestamp
    token_type: str = "Bearer"
    
    def is_valid(self, buffer_s: float = 60.0) -> bool:
        """True se il token è valido per almeno buffer_s secondi."""
        return time.time() < (self.expires_at - buffer_s)


class ClientCredentialsAuth:
    """
    OAuth 2.0 Client Credentials flow con cache e refresh automatico.
    Usato per: M2M (machine-to-machine), API senza utente.
    """

    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        scope: str = "",
    ):
        self._token_url = token_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._scope = scope
        self._token: Optional[OAuthToken] = None
        self._lock = threading.Lock()

    def _ottieni_nuovo_token(self) -> OAuthToken:
        """Chiama il token endpoint per ottenere un nuovo access token."""
        with httpx.Client() as client:
            r = client.post(
                self._token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    **({"scope": self._scope} if self._scope else {}),
                },
                timeout=10.0,
            )
            r.raise_for_status()
            data = r.json()
            
            return OAuthToken(
                access_token=data["access_token"],
                expires_at=time.time() + data.get("expires_in", 3600),
                token_type=data.get("token_type", "Bearer"),
            )

    def get_header(self) -> dict[str, str]:
        """
        Ritorna header Authorization con token valido.
        Refresh automatico se il token è scaduto o in scadenza.
        Thread-safe.
        """
        with self._lock:
            if self._token is None or not self._token.is_valid():
                logger.debug("Token OAuth scaduto/mancante — refresh")
                self._token = self._ottieni_nuovo_token()
                logger.debug("Token OAuth rinnovato (scade in %ds)",
                             int(self._token.expires_at - time.time()))
        
        return {"Authorization": f"{self._token.token_type} {self._token.access_token}"}


# ─── Demo ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test: mostra header generati (senza chiamate reali)
    print("=== STRATEGIE DI AUTENTICAZIONE ===\n")
    
    print("1. API Key:")
    headers = auth_api_key("sk-myapikey123", header_name="X-API-Key")
    print(f"   Headers: {headers}\n")
    
    print("2. Bearer Token:")
    headers = auth_api_key_bearer("sk-myapikey123")
    print(f"   Headers: {headers}\n")
    
    print("3. Basic Auth:")
    headers = auth_basic("admin", "mypassword")
    print(f"   Headers: {headers}\n")
    
    print("4. OAuth Client Credentials:")
    print("   (richiede token URL reale — vedi tutorial OAuth 2.1)")
    print("   auth = ClientCredentialsAuth(token_url, client_id, client_secret)")
    print("   headers = auth.get_header()  # Auto-refresh!")
```

---

## PART D — Test con Mock HTTP

### D1 — Unit Test con respx

```python
#!/usr/bin/env python3
# file: tests/test_api_client.py
"""
Test del client API con respx — mock HTTP senza server reale.
respx intercetta le chiamate httpx a livello di transport.
"""
from __future__ import annotations

import json
import pytest
import pytest_asyncio
import respx
import httpx

from client.api_client import ApiClient, ApiClientConfig, RateLimitError, NonRetriableApiError


# ─── Fixture ─────────────────────────────────────────────────────────────────

@pytest.fixture
def config():
    return ApiClientConfig(
        base_url="https://api.test.example.com",
        max_retries=2,
        retry_backoff_initial=0.01,  # Veloce nei test
    )


# ─── Test GET ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_get_successo(config):
    """GET con risposta 200 ritorna il JSON."""
    ordine = {"id": "ORD-001", "importo": 49.99}
    respx.get("https://api.test.example.com/v1/ordini/ORD-001").mock(
        return_value=httpx.Response(200, json=ordine)
    )
    
    async with ApiClient(config) as client:
        response = await client.get("/v1/ordini/ORD-001")
        assert response.status_code == 200
        assert response.json() == ordine


@pytest.mark.asyncio
@respx.mock
async def test_get_non_trovato(config):
    """GET con 404 solleva NonRetriableApiError."""
    respx.get("https://api.test.example.com/v1/ordini/INESISTENTE").mock(
        return_value=httpx.Response(404, json={"error": "not found"})
    )
    
    async with ApiClient(config) as client:
        with pytest.raises(NonRetriableApiError) as exc_info:
            await client.get("/v1/ordini/INESISTENTE")
        assert exc_info.value.status_code == 404


# ─── Test Rate Limiting ───────────────────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_rate_limit_retry(config):
    """429 viene ritentato dopo Retry-After."""
    call_count = [0]
    ordine = {"id": "ORD-001", "importo": 49.99}
    
    def handler(request):
        call_count[0] += 1
        if call_count[0] == 1:
            return httpx.Response(429, headers={"Retry-After": "0"})
        return httpx.Response(200, json=ordine)
    
    respx.get("https://api.test.example.com/v1/ordini/ORD-001").mock(side_effect=handler)
    
    async with ApiClient(config) as client:
        response = await client.get("/v1/ordini/ORD-001")
        assert response.status_code == 200
        assert call_count[0] == 2  # Prima richiesta + retry dopo rate limit


# ─── Test Retry su Errore Server ──────────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_retry_su_500(config):
    """503 viene ritentato — successo al secondo tentativo."""
    call_count = [0]
    ordine = {"id": "ORD-001"}
    
    def handler(request):
        call_count[0] += 1
        if call_count[0] < 2:
            return httpx.Response(503, json={"error": "service unavailable"})
        return httpx.Response(200, json=ordine)
    
    respx.get("https://api.test.example.com/v1/ordini/ORD-001").mock(side_effect=handler)
    
    async with ApiClient(config) as client:
        response = await client.get("/v1/ordini/ORD-001")
        assert response.status_code == 200
        assert call_count[0] == 2


# ─── Test Pagination ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
@respx.mock
async def test_paginazione_cursor(config):
    """Itera su 3 pagine cursor-based e raccoglie tutti gli oggetti."""
    from pagination.paginator import pagina_cursor, raccoglie_tutto
    
    pagine = [
        {"data": [{"id": i} for i in range(1, 4)], "next_cursor": "c2", "has_more": True},
        {"data": [{"id": i} for i in range(4, 7)], "next_cursor": "c3", "has_more": True},
        {"data": [{"id": i} for i in range(7, 9)], "next_cursor": None, "has_more": False},
    ]
    
    call_count = [0]
    
    def handler(request):
        page = pagine[call_count[0]]
        call_count[0] += 1
        return httpx.Response(200, json=page)
    
    respx.get("https://api.test.example.com/v1/items").mock(side_effect=handler)
    
    async with ApiClient(config) as client:
        tutti = await raccoglie_tutto(pagina_cursor(client, "/v1/items", page_size=3))
    
    assert len(tutti) == 8
    assert call_count[0] == 3
    assert tutti[0]["id"] == 1
    assert tutti[-1]["id"] == 8


# ─── Test Token Bucket Rate Limiter ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_token_bucket_limiter():
    """Verifica che il rate limiter non superi il rate configurato."""
    from client.api_client import TokenBucketLimiter
    import time
    
    limiter = TokenBucketLimiter(rate=10.0, burst=1.0)  # 10 req/s
    
    start = time.monotonic()
    for _ in range(3):
        await limiter.acquire()
    elapsed = time.monotonic() - start
    
    # Con rate=10/s e burst=1, 3 richieste devono richiedere almeno ~0.2s
    assert elapsed >= 0.15  # 2 pause × 0.1s = 0.2s (con tolleranza)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])
```

---

## PART E — Mock Server Locale (Sviluppo)

### E1 — Server Flask Minimale per Test Manuali

```python
#!/usr/bin/env python3
# file: mock_server/server.py
"""
Server HTTP mock per testare il client localmente senza API esterna.
Simula rate limiting, errori, e paginazione.

Avvio: python mock_server/server.py
Test: curl http://localhost:8080/v1/ordini
"""
from __future__ import annotations

import json
import time
import random
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

ORDINI = [{"id": f"ORD-{i:03d}", "importo": i * 9.99} for i in range(1, 51)]
RICHIESTE_PER_IP: dict[str, list[float]] = {}
RATE_LIMIT = 10  # req/s
PAGE_SIZE = 10


class MockApiHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)
        
        # Rate limiting semplice
        ip = self.client_address[0]
        now = time.time()
        history = [t for t in RICHIESTE_PER_IP.get(ip, []) if now - t < 1.0]
        RICHIESTE_PER_IP[ip] = history + [now]
        
        if len(history) >= RATE_LIMIT:
            self._risposta(429, {"error": "too many requests"}, 
                          headers={"Retry-After": "1"})
            return
        
        if path == "/v1/ordini":
            page = int(params.get("page", ["1"])[0])
            per_page = int(params.get("per_page", [str(PAGE_SIZE)])[0])
            cursor = params.get("cursor", [None])[0]
            
            # Simula errore casuale (5%)
            if random.random() < 0.05:
                self._risposta(503, {"error": "service unavailable"})
                return
            
            start = (page - 1) * per_page
            items = ORDINI[start:start + per_page]
            
            self._risposta(200, {
                "data": items,
                "total": len(ORDINI),
                "page": page,
                "per_page": per_page,
                "has_more": (start + per_page) < len(ORDINI),
            })
        
        elif path.startswith("/v1/ordini/"):
            ordine_id = path.split("/")[-1]
            ordine = next((o for o in ORDINI if o["id"] == ordine_id), None)
            if ordine:
                self._risposta(200, ordine)
            else:
                self._risposta(404, {"error": f"Ordine {ordine_id} non trovato"})
        
        elif path == "/health":
            self._risposta(200, {"status": "ok"})
        
        else:
            self._risposta(404, {"error": "endpoint non trovato"})

    def _risposta(self, status: int, body: dict, headers: dict = None):
        body_bytes = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body_bytes)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body_bytes)

    def log_message(self, format, *args):
        print(f"[MockAPI] {args[0]} {args[1]} {args[2]}")


if __name__ == "__main__":
    server = HTTPServer(("localhost", 8080), MockApiHandler)
    print("Mock API Server su http://localhost:8080")
    print("Endpoints: GET /v1/ordini, GET /v1/ordini/:id, GET /health")
    print(f"Rate limit: {RATE_LIMIT} req/s")
    server.serve_forever()
```

---

## Esercizi

### Esercizio 1 — Sincronizza Ordini da API Esterna (30 min)

```python
# Usa ApiClient + pagina_cursor per scaricare tutti gli ordini
# e salvarli in un file JSONL locale

async def scarica_tutti_ordini(api_url: str, api_key: str, output_path: str) -> int:
    """
    Scarica tutti gli ordini via pagination e salva in JSONL.
    Restituisce il numero totale di ordini scaricati.
    """
    config = ApiClientConfig(base_url=api_url)
    auth = auth_api_key_bearer(api_key)
    
    async with ApiClient(config, auth_header=auth) as client:
        count = 0
        with open(output_path, "w") as f:
            async for ordine in pagina_cursor(client, "/v1/ordini"):
                f.write(json.dumps(ordine) + "\n")
                count += 1
        return count
```

### Esercizio 2 — Parallel Requests con semaforo (20 min)

```python
# Scarica N ordini in parallelo con un limite di concorrenza
import asyncio

async def scarica_dettagli_parallelo(
    client: ApiClient,
    ordine_ids: list[str],
    max_concorrenza: int = 5,
) -> list[dict]:
    """Scarica dettagli di N ordini in parallelo."""
    semaforo = asyncio.Semaphore(max_concorrenza)
    
    async def get_uno(ordine_id: str) -> dict:
        async with semaforo:
            r = await client.get(f"/v1/ordini/{ordine_id}")
            return r.json()
    
    return await asyncio.gather(*[get_uno(oid) for oid in ordine_ids])
```

### Esercizio 3 — Aggiunta Test Pagination (20 min)

Aggiungi a `test_api_client.py` un test per `pagina_offset`:
- Mock 3 pagine da 10 ordini ciascuna (total=30)
- Verifica che tutti i 30 oggetti vengano raccolti
- Verifica che ci siano esattamente 3 chiamate HTTP

---

## Script di Verifica Prerequisiti

```python
#!/usr/bin/env python3
# file: verifica_prerequisiti.py
def check_import(modulo):
    try:
        __import__(modulo)
        print(f"  [OK] {modulo}")
        return True
    except ImportError:
        print(f"  [FAIL] {modulo} — pip install {modulo}")
        return False

print("Verifica prerequisiti API Lab...")
results = [
    check_import("httpx"),
    check_import("tenacity"),
    check_import("respx"),
    check_import("pydantic"),
    check_import("pytest"),
    check_import("pytest_asyncio"),
]
print(f"\n{'Tutti OK!' if all(results) else 'Alcune dipendenze mancanti'}")
```

---

## Riferimenti

- httpx docs: https://www.python-httpx.org/
- respx (HTTP mocking): https://lundberg.github.io/respx/
- tenacity retry: https://tenacity.readthedocs.io/
- Token Bucket algorithm: https://en.wikipedia.org/wiki/Token_bucket
- Modulo sorgente: `04-integrazione-api.md`
