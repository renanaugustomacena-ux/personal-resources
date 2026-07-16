# Tutorial 11 — Web Framework in Python: FastAPI dalla A alla Z

> **Companion a:** `11-web-framework.md`
> **Scope:** FastAPI, Pydantic v2, routing, dependency injection, middleware, background tasks, WebSocket, testing
> **Prerequisiti:** `tutorial_09_type_hints_mypy.md`, `tutorial_10_programmazione_asincrona.md`
> **Durata stimata:** 18-22 ore
> **Stack:** Python 3.12+, FastAPI 0.115+, Pydantic v2, Uvicorn/Gunicorn

---

## Mappa concettuale

```
FastAPI — Web Framework Asincrono
│
├── Routing
│   ├── @app.get/post/put/delete/patch
│   ├── Path parameters — /items/{item_id}
│   ├── Query parameters — /items?limit=10&skip=0
│   ├── Request body — Pydantic BaseModel
│   └── APIRouter — modularizzazione endpoint
│
├── Pydantic v2 — Validazione e serializzazione
│   ├── BaseModel — schema + validazione
│   ├── Field() — metadati, constraints
│   ├── @model_validator — validazione cross-field
│   ├── @field_validator — validazione singolo campo
│   └── model_config — configurazione (from_attributes, strict)
│
├── Dependency Injection
│   ├── Depends() — iniezione dipendenze
│   ├── Security — OAuth2, API key, JWT
│   ├── Database session — scoped a request
│   └── Cache, settings, config
│
├── Middleware
│   ├── CORS — CORSMiddleware
│   ├── Auth — custom middleware
│   ├── Logging — request/response
│   └── Timing — latenza endpoint
│
├── Background Tasks
│   ├── BackgroundTasks — dopo risposta
│   └── asyncio.create_task — concorrenza
│
├── WebSocket
│   ├── @app.websocket() — endpoint WS
│   ├── websocket.accept/send/receive
│   └── ConnectionManager — multi-client
│
└── Testing
    ├── TestClient (sincrono, httpx)
    ├── AsyncClient — test asincroni
    ├── override_dependencies — mock DI
    └── pytest fixtures per app/client
```

---

# Parte A — Fondamenti di FastAPI

---

## A1. Installazione e struttura minima

```python
# Installa: pip install fastapi uvicorn[standard] pydantic
# Esegui: uvicorn main:app --reload

from fastapi import FastAPI

app = FastAPI(
    title="API di esempio",
    description="Tutorial FastAPI completo",
    version="0.1.0",
    docs_url="/docs",        # Swagger UI
    redoc_url="/redoc",      # ReDoc
    openapi_url="/openapi.json",
)

@app.get("/")
async def radice() -> dict[str, str]:
    return {"messaggio": "Benvenuto nell'API!"}

@app.get("/salute")
async def salute() -> dict[str, str]:
    return {"stato": "ok"}
```

> **Analogia:** FastAPI è come un ufficio postale ultra-moderno. Ogni endpoint (`@app.get`) è uno sportello specializzato. Il visitatore arriva con una richiesta HTTP, viene guidato allo sportello giusto grazie al routing, il suo documento (body JSON) viene validato automaticamente, e riceve la risposta. Pydantic è l'impiegato che controlla che il documento sia compilato correttamente prima ancora che arrivi allo sportello.

---

## A2. Path e Query parameters

```python
from fastapi import FastAPI, Path, Query

app = FastAPI()

# Path parameter — parte dell'URL
@app.get("/articoli/{articolo_id}")
async def leggi_articolo(
    articolo_id: int = Path(
        gt=0,
        description="ID dell'articolo (deve essere positivo)"
    )
) -> dict:
    return {"articolo_id": articolo_id}

# Query parameters — dopo il ?
@app.get("/articoli")
async def lista_articoli(
    skip: int = Query(default=0, ge=0, description="Elementi da saltare"),
    limit: int = Query(default=10, ge=1, le=100, description="Max elementi"),
    categoria: str | None = Query(default=None, description="Filtra per categoria"),
    ordina_per: str = Query(default="data", regex="^(data|nome|prezzo)$"),
) -> dict:
    return {
        "skip": skip,
        "limit": limit,
        "categoria": categoria,
        "ordina_per": ordina_per,
    }

# Path + Query combinati
@app.get("/utenti/{utente_id}/ordini")
async def ordini_utente(
    utente_id: int = Path(gt=0),
    completati: bool = Query(default=False),
) -> dict:
    return {"utente_id": utente_id, "solo_completati": completati}
```

---

## A3. Request body con Pydantic v2

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field, EmailStr, model_validator
from datetime import datetime
from decimal import Decimal

app = FastAPI()

class IndirizzoSpedizione(BaseModel):
    via: str = Field(min_length=3, max_length=200)
    citta: str = Field(min_length=2, max_length=100)
    cap: str = Field(pattern=r"^\d{5}$")
    paese: str = Field(default="IT")

class CreaOrdine(BaseModel):
    prodotti: list[int] = Field(min_length=1, description="Lista ID prodotti")
    quantita: dict[int, int] = Field(description="ID prodotto -> quantità")
    indirizzo: IndirizzoSpedizione
    note: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def valida_quantita_prodotti(self) -> "CreaOrdine":
        for pid in self.prodotti:
            if pid not in self.quantita:
                raise ValueError(f"Manca la quantità per il prodotto {pid}")
            if self.quantita[pid] < 1:
                raise ValueError(f"Quantità per {pid} deve essere >= 1")
        return self

class RispostaOrdine(BaseModel):
    id: int
    stato: str
    totale: Decimal
    creato_il: datetime

@app.post("/ordini", response_model=RispostaOrdine, status_code=201)
async def crea_ordine(ordine: CreaOrdine) -> RispostaOrdine:
    return RispostaOrdine(
        id=1,
        stato="in_attesa",
        totale=Decimal("49.99"),
        creato_il=datetime.now(),
    )
```

---

## A4. Response model e status codes

```python
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI()

class Utente(BaseModel):
    id: int
    nome: str
    email: str

class UtenteConPassword(Utente):
    password_hash: str   # campo interno — NON deve uscire

# response_model esclude campi non dichiarati nel modello di risposta
@app.get("/utenti/{id}", response_model=Utente)
async def leggi_utente(id: int) -> UtenteConPassword:
    if id != 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Utente {id} non trovato",
        )
    return UtenteConPassword(
        id=1,
        nome="Mario",
        email="mario@example.com",
        password_hash="$2b$12$...",   # escluso dal response_model
    )

# response_model_exclude — escludere campi specifici
@app.get("/utenti/{id}/pubblico", response_model=Utente, response_model_exclude={"email"})
async def profilo_pubblico(id: int) -> Utente:
    return Utente(id=id, nome="Mario", email="mario@example.com")

# Risposta personalizzata
from fastapi.responses import JSONResponse, Response

@app.delete("/utenti/{id}", status_code=204)
async def elimina_utente(id: int) -> Response:
    # 204 No Content
    return Response(status_code=204)
```

---

# Parte B — Funzionalità avanzate

---

## B1. Dependency Injection

```python
from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel

app = FastAPI()

# Dipendenza semplice — funzione
def get_db():
    db = {"connessione": "simulata"}
    try:
        yield db
    finally:
        pass  # chiudi connessione

# Dipendenza parametrizzata — callable class
class Paginazione:
    def __init__(
        self,
        skip: int = 0,
        limit: int = 10,
        max_limit: int = 100,
    ) -> None:
        self.skip = skip
        self.limit = min(limit, max_limit)

def get_paginazione(skip: int = 0, limit: int = 10) -> Paginazione:
    return Paginazione(skip=skip, limit=limit)

# Dipendenza autenticazione
async def verifica_api_key(
    x_api_key: str = Header(description="Chiave API")
) -> str:
    # In produzione: verifica contro DB/cache
    if x_api_key != "secret-key":
        raise HTTPException(status_code=401, detail="API key non valida")
    return x_api_key

# Catena di dipendenze
async def get_utente_corrente(
    api_key: str = Depends(verifica_api_key),
    db: dict = Depends(get_db),
) -> dict:
    return {"utente": "mario", "ruolo": "admin"}

@app.get("/profilo")
async def leggi_profilo(
    utente: dict = Depends(get_utente_corrente),
    pagina: Paginazione = Depends(get_paginazione),
) -> dict:
    return {"utente": utente, "pagina": {"skip": pagina.skip, "limit": pagina.limit}}
```

---

## B2. APIRouter — modularizzazione

```python
# routers/utenti.py
from fastapi import APIRouter, Depends

router = APIRouter(
    prefix="/utenti",
    tags=["utenti"],
    dependencies=[Depends(verifica_api_key)],
    responses={404: {"description": "Non trovato"}},
)

@router.get("/")
async def lista_utenti() -> list:
    return []

@router.get("/{id}")
async def leggi_utente(id: int) -> dict:
    return {"id": id}

@router.post("/", status_code=201)
async def crea_utente(dati: dict) -> dict:
    return dati

# routers/prodotti.py
from fastapi import APIRouter

router_prodotti = APIRouter(prefix="/prodotti", tags=["prodotti"])

@router_prodotti.get("/")
async def lista_prodotti() -> list:
    return []

# main.py
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
app.include_router(router_prodotti)
```

---

## B3. Middleware

```python
import time
import uuid
import logging
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://myapp.com", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware personalizzato — logging e timing
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = str(uuid.uuid4())
        request.state.correlation_id = correlation_id

        inizio = time.perf_counter()
        logger.info(
            "Richiesta",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "url": str(request.url),
            }
        )

        try:
            response = await call_next(request)
        except Exception as e:
            logger.exception("Errore non gestito", extra={"correlation_id": correlation_id})
            raise

        durata_ms = (time.perf_counter() - inizio) * 1000
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Response-Time"] = f"{durata_ms:.1f}ms"

        logger.info(
            "Risposta",
            extra={
                "correlation_id": correlation_id,
                "status": response.status_code,
                "durata_ms": round(durata_ms, 1),
            }
        )
        return response

app.add_middleware(LoggingMiddleware)

# Middleware come decoratore @app.middleware
@app.middleware("http")
async def aggiungi_headers_sicurezza(request: Request, call_next) -> Response:
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response
```

---

## B4. Background Tasks

```python
from fastapi import FastAPI, BackgroundTasks
import asyncio
import logging

logger = logging.getLogger(__name__)
app = FastAPI()

async def invia_email(destinatario: str, soggetto: str, corpo: str) -> None:
    """Simula invio email asincrono."""
    logger.info(f"Invio email a {destinatario}: {soggetto}")
    await asyncio.sleep(2)   # simulazione SMTP
    logger.info(f"Email inviata a {destinatario}")

def aggiorna_statistiche(utente_id: int, azione: str) -> None:
    """Funzione sincrona — gira in un thread."""
    logger.info(f"Statistiche aggiornate: utente={utente_id}, azione={azione}")

@app.post("/registrazione")
async def registra_utente(
    dati: dict,
    background_tasks: BackgroundTasks,
) -> dict:
    # Risposta immediata al client
    utente_id = 42

    # Task eseguito DOPO l'invio della risposta
    background_tasks.add_task(
        invia_email,
        dati.get("email", ""),
        "Benvenuto!",
        "Il tuo account è stato creato."
    )
    background_tasks.add_task(aggiorna_statistiche, utente_id, "registrazione")

    return {"id": utente_id, "stato": "creato"}
```

---

## B5. WebSocket

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import json

app = FastAPI()

class GestoreConnessioni:
    def __init__(self) -> None:
        self.attive: dict[str, WebSocket] = {}

    async def connetti(self, ws: WebSocket, client_id: str) -> None:
        await ws.accept()
        self.attive[client_id] = ws

    def disconnetti(self, client_id: str) -> None:
        self.attive.pop(client_id, None)

    async def invia_a(self, client_id: str, messaggio: dict) -> None:
        if ws := self.attive.get(client_id):
            await ws.send_json(messaggio)

    async def broadcast(self, messaggio: dict, escludi: str | None = None) -> None:
        per_disconnettere = []
        for cid, ws in self.attive.items():
            if cid == escludi:
                continue
            try:
                await ws.send_json(messaggio)
            except Exception:
                per_disconnettere.append(cid)
        for cid in per_disconnettere:
            self.disconnetti(cid)

gestore = GestoreConnessioni()

@app.websocket("/ws/{client_id}")
async def endpoint_ws(websocket: WebSocket, client_id: str) -> None:
    await gestore.connetti(websocket, client_id)
    try:
        while True:
            dati = await websocket.receive_json()
            tipo = dati.get("tipo", "messaggio")

            if tipo == "messaggio":
                await gestore.broadcast(
                    {"mittente": client_id, "testo": dati.get("testo", "")},
                    escludi=client_id,
                )
            elif tipo == "privato":
                dest = dati.get("destinatario")
                await gestore.invia_a(dest, {"mittente": client_id, "testo": dati.get("testo", "")})

    except WebSocketDisconnect:
        gestore.disconnetti(client_id)
        await gestore.broadcast({"sistema": f"{client_id} ha lasciato la chat"})
```

---

# Parte C — Esercizi guidati

---

## C1. API CRUD completa con validazione

```python
from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime

app = FastAPI()

# Database simulato in memoria
_db: dict[int, dict] = {}
_counter = 0

class CreaUtente(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    email: str = Field(description="Email valida")
    eta: int = Field(ge=0, le=150)
    bio: str | None = Field(default=None, max_length=500)

class AggiornaParziale(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=100)
    bio: str | None = Field(default=None, max_length=500)

class UtenteDB(BaseModel):
    id: int
    nome: str
    email: str
    eta: int
    bio: str | None
    creato_il: datetime
    aggiornato_il: datetime

def _get_o_404(id: int) -> dict:
    if id not in _db:
        raise HTTPException(status_code=404, detail=f"Utente {id} non trovato")
    return _db[id]

@app.post("/utenti", response_model=UtenteDB, status_code=201)
async def crea(dati: CreaUtente) -> UtenteDB:
    global _counter
    _counter += 1
    ora = datetime.now()
    record = {"id": _counter, **dati.model_dump(), "creato_il": ora, "aggiornato_il": ora}
    _db[_counter] = record
    return UtenteDB(**record)

@app.get("/utenti/{id}", response_model=UtenteDB)
async def leggi(id: int) -> UtenteDB:
    return UtenteDB(**_get_o_404(id))

@app.put("/utenti/{id}", response_model=UtenteDB)
async def aggiorna(id: int, dati: CreaUtente) -> UtenteDB:
    record = _get_o_404(id)
    record.update(**dati.model_dump(), aggiornato_il=datetime.now())
    return UtenteDB(**record)

@app.patch("/utenti/{id}", response_model=UtenteDB)
async def aggiorna_parziale(id: int, dati: AggiornaParziale) -> UtenteDB:
    record = _get_o_404(id)
    aggiornamenti = dati.model_dump(exclude_none=True)
    record.update(**aggiornamenti, aggiornato_il=datetime.now())
    return UtenteDB(**record)

@app.delete("/utenti/{id}", status_code=204)
async def elimina(id: int) -> None:
    _get_o_404(id)
    del _db[id]
```

---

## C2. Autenticazione JWT

```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import hashlib
import hmac
import json
import base64
import time

app = FastAPI()

# Semplificazione: JWT manuale per capire la meccanica
# In produzione: usare python-jose o PyJWT
SECRET = "chiave-segreta-molto-lunga-e-casuale"

def crea_jwt(payload: dict, scadenza_sec: int = 3600) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {**payload, "exp": int(time.time()) + scadenza_sec}

    def b64url(data: dict) -> str:
        return base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()

    h = b64url(header)
    p = b64url(payload)
    firma = hmac.new(SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).hexdigest()
    return f"{h}.{p}.{firma}"

def verifica_jwt(token: str) -> dict:
    try:
        h, p, firma = token.split(".")
        attesa = hmac.new(SECRET.encode(), f"{h}.{p}".encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(firma, attesa):
            raise ValueError("Firma non valida")
        payload = json.loads(base64.urlsafe_b64decode(p + "=="))
        if payload.get("exp", 0) < time.time():
            raise ValueError("Token scaduto")
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

# Utenti simulati
UTENTI_DB = {"mario": {"password_hash": hashlib.sha256("password123".encode()).hexdigest()}}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

@app.post("/token", response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends()) -> Token:
    utente = UTENTI_DB.get(form.username)
    if not utente:
        raise HTTPException(status_code=401, detail="Credenziali non valide")
    pwd_hash = hashlib.sha256(form.password.encode()).hexdigest()
    if not hmac.compare_digest(utente["password_hash"], pwd_hash):
        raise HTTPException(status_code=401, detail="Credenziali non valide")
    token = crea_jwt({"sub": form.username})
    return Token(access_token=token)

async def get_utente_corrente(token: str = Depends(oauth2_scheme)) -> str:
    payload = verifica_jwt(token)
    return payload["sub"]

@app.get("/me")
async def leggi_profilo(utente: str = Depends(get_utente_corrente)) -> dict:
    return {"utente": utente}
```

---

# Parte D — Testing

---

## D1. Test con TestClient

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI, Depends

app = FastAPI()

# Dipendenza reale
def get_db_reale():
    return {"connessione": "reale"}

@app.get("/dati")
def leggi_dati(db=Depends(get_db_reale)) -> dict:
    return {"fonte": "db", "valore": 42}

# Test sincrono con TestClient
client = TestClient(app)

def test_root():
    r = client.get("/")
    assert r.status_code == 404  # nessun endpoint /

def test_dati():
    r = client.get("/dati")
    assert r.status_code == 200
    assert r.json() == {"fonte": "db", "valore": 42}

# Override dipendenze per test
def get_db_mock():
    return {"connessione": "mock"}

def test_dati_con_mock():
    app.dependency_overrides[get_db_reale] = get_db_mock
    r = client.get("/dati")
    assert r.status_code == 200
    app.dependency_overrides.clear()
```

---

## D2. Test asincroni con pytest-anyio

```python
# pip install pytest-anyio httpx
import pytest
from httpx import AsyncClient, ASGITransport
from fastapi import FastAPI

app = FastAPI()

@app.get("/async-endpoint")
async def endpoint_async() -> dict:
    return {"asincrono": True}

@pytest.mark.anyio
async def test_endpoint_async():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        r = await client.get("/async-endpoint")
        assert r.status_code == 200
        assert r.json() == {"asincrono": True}

# Fixture pytest per client condiviso
@pytest.fixture
async def client_async():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c

@pytest.mark.anyio
async def test_con_fixture(client_async):
    r = await client_async.get("/async-endpoint")
    assert r.status_code == 200
```

---

# Parte E — Riepilogo e prossimi passi

## Cheatsheet FastAPI

```
Endpoint:       @app.get/post/put/delete/patch("/percorso")
Path param:     def fn(id: int = Path(gt=0))
Query param:    def fn(q: str | None = Query(None))
Body:           def fn(dati: MioModello)
Risposta:       response_model=MioModello, status_code=201
Errori:         raise HTTPException(status_code=404, detail="msg")
DI:             def fn(db=Depends(get_db))
Router:         router = APIRouter(prefix="/x"); app.include_router(router)
Middleware:     app.add_middleware(MioMiddleware)
BG task:        def fn(bg: BackgroundTasks): bg.add_task(fn, arg)
WebSocket:      @app.websocket("/ws"); await ws.accept(); ws.receive_json()
Test sync:      client = TestClient(app); client.get("/")
Test async:     AsyncClient(transport=ASGITransport(app), base_url="http://test")
Override DI:    app.dependency_overrides[dep] = mock; clear()
```

## Anti-pattern da evitare

- **Logica nel controller** — endpoint devono solo coordinare, non contenere business logic
- **Usare `dict` come tipo di ritorno** — sempre definire modelli Pydantic espliciti
- **Non gestire HTTPException** — errori non gestiti ritornano 500 invece di messaggi utili
- **Bloccare l'event loop** — non chiamare codice sincrono bloccante direttamente; usare `run_in_executor`
- **Secrets in codice** — usare `pydantic-settings` con `.env` file

## Prossimi passi

- `tutorial_12_database.md` — SQLAlchemy 2.0 async con FastAPI
- `tutorial_27_ci_cd.md` — Docker, CI/CD pipeline per FastAPI
- `tutorial_31_otel.md` — Observability con OpenTelemetry per FastAPI
