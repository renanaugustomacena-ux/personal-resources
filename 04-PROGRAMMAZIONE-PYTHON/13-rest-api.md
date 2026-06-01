---
corso: "Programmazione Python"
fase: "3 — Librerie e Framework"
modulo: "13"
titolo: "REST API con Python"
versione: "FastAPI 0.115+ / Pydantic v2.9+ / Strawberry 0.252+"
livello: "Intermedio-Avanzato"
prerequisiti:
  - "11 — Web Framework"
  - "12 — Database"
  - "09 — Type Hints e Mypy"
obiettivi:
  - "Progettare API RESTful con FastAPI seguendo le best practice"
  - "Implementare autenticazione JWT e OAuth2 con scopes"
  - "Validare request/response con Pydantic v2 e schemi OpenAPI"
  - "Costruire API GraphQL con Strawberry"
  - "Versionare, documentare e testare API professionali"
  - "Implementare rate limiting, caching e pagination"
tag: [REST-API, FastAPI, Pydantic, OpenAPI, GraphQL, Strawberry, JWT, OAuth2]
---

# REST API con Python — Guida Completa

> **Modulo 13** · **Aggiornamento:** 2026-05-24 · **Versione:** FastAPI 0.115+ / Pydantic v2.9+ / Strawberry 0.252+

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Web Framework](11-web-framework.md), [Database](12-database.md), [Type Hints](09-type-hints-e-mypy.md)
>
> Al termine di questo modulo saprai:
> 1. Progettare API RESTful con FastAPI seguendo le best practice
> 2. Implementare autenticazione JWT e OAuth2 con scopes
> 3. Validare request/response con Pydantic v2 e generare schemi OpenAPI
> 4. Costruire API GraphQL con Strawberry
> 5. Versionare, documentare e testare API professionali
> 6. Implementare rate limiting, caching e pagination
>
> **Tempo stimato:** 8-10 ore · **Livello:** Intermedio-Avanzato
> **Fase:** Modulo 13 di 33 — Integrazione e comunicazione tra sistemi
> **Livello:** Intermedio–Avanzato

## Obiettivi di apprendimento

1. Progettare REST API conformi ai vincoli architetturali REST e alle convenzioni di naming delle risorse.
2. Implementare CRUD completo con FastAPI, validazione Pydantic v2 e gestione strutturata degli errori (RFC 7807).
3. Applicare strategie di autenticazione (JWT con refresh token, OAuth2 scopes, API keys) e autorizzazione RBAC.
4. Padroneggiare paginazione offset e cursor-based, filtri dinamici, ordinamento e Link headers.
5. Integrare rate limiting (sliding window, token bucket), caching (ETag, Redis) e versioning (URL, header, content negotiation).
6. Costruire endpoint WebSocket con FastAPI per comunicazione bidirezionale in tempo reale.
7. Esporre un layer GraphQL con Strawberry, DataLoader per N+1 e persisted queries.
8. Scrivere test completi con httpx AsyncClient, fixture pattern e contract testing.
9. Applicare hardening di sicurezza: CORS, CSRF per cookie auth, sanitizzazione input, prevenzione SQL injection.


## Mappa concettuale — Architettura a strati di una REST API

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CLIENT (browser, mobile, altro servizio)      │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │  HTTP / WebSocket / GraphQL
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  REVERSE PROXY / API GATEWAY                                          │
│  TLS termination · Rate limiting globale · CORS · Logging accessi     │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  FRAMEWORK (FastAPI / Flask)                                          │
│  ┌────────────┐  ┌───────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Middleware  │  │   Routing +   │  │  Dependency  │  │ OpenAPI    │ │
│  │ (CORS,     │  │   Validazione │  │  Injection   │  │ auto-gen   │ │
│  │  Auth,     │  │   (Pydantic)  │  │  (DB, Auth)  │  │ Swagger UI │ │
│  │  Logging)  │  │               │  │              │  │ ReDoc      │ │
│  └────────────┘  └───────────────┘  └──────────────┘  └────────────┘ │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  SERVICE LAYER (Business Logic)                                       │
│  Orchestrazione · Regole di dominio · Transazioni · Event dispatch    │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  REPOSITORY / DATA ACCESS                                             │
│  SQLAlchemy async · Redis cache · S3 storage · External API clients   │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  INFRASTRUTTURA                                                       │
│  PostgreSQL · Redis · Object Storage · Message Broker                 │
└─────────────────────────────────────────────────────────────────────────┘
```


## Idee guida
1. **FastAPI auto-genera OpenAPI 3.1 schema.**
2. **Pydantic v2 (`model_validate`, `Field`, `ConfigDict`).**
3. **RFC 7807 Problem Details: `HTTPException` con custom handler.**
4. **OAuth2PasswordBearer + JWT per auth standard.**


## Indice

1. [Panoramica](#panoramica)
2. [Progettazione API](#progettazione-api)
3. [Implementazione con FastAPI](#implementazione-con-fastapi)
4. [Implementazione con Flask](#implementazione-con-flask)
5. [Client API (requests/httpx)](#client-api-requestshttpx)
6. [Testing API](#testing-api)
7. [Documentazione API](#documentazione-api)
8. [Versioning e Evoluzione](#versioning-e-evoluzione)
9. [Risposta agli errori — RFC 7807 Problem Details](#risposta-agli-errori--rfc-7807-problem-details)
10. [Autenticazione avanzata — JWT Refresh, OAuth2 Scopes](#autenticazione-avanzata--jwt-refresh-oauth2-scopes)
11. [Rate Limiting avanzato — Sliding Window e Token Bucket](#rate-limiting-avanzato--sliding-window-e-token-bucket)
12. [Paginazione avanzata — Cursor, Link Headers, Pydantic Models](#paginazione-avanzata--cursor-link-headers-pydantic-models)
13. [HATEOAS — Hypermedia nella pratica](#hateoas--hypermedia-nella-pratica)
14. [Validazione avanzata — Pydantic v2](#validazione-avanzata--pydantic-v2)
15. [Response Serialization](#response-serialization)
16. [File Upload e Download](#file-upload-e-download)
17. [WebSocket con FastAPI](#websocket-con-fastapi)
18. [GraphQL con Strawberry](#graphql-con-strawberry)
19. [Sicurezza API — CORS, CSRF, Sanitizzazione, SQL Injection](#sicurezza-api--cors-csrf-sanitizzazione-sql-injection)
20. [Testing avanzato — Contract Testing e Fixture Pattern](#testing-avanzato--contract-testing-e-fixture-pattern)
21. [Best Practices](#best-practices)
22. [Troubleshooting](#troubleshooting)
23. [Esercizi](#esercizi)
24. [Letture e riferimenti](#letture-e-riferimenti)
25. [Cross-link](#cross-link)
26. [Glossario](#glossario)

---

## Panoramica

Le REST API (Representational State Transfer Application Programming Interface) rappresentano il paradigma dominante per la comunicazione tra sistemi distribuiti nel web moderno. Comprendere come progettarle e implementarle in Python significa padroneggiare uno degli strumenti fondamentali dello sviluppo software contemporaneo.

### Principi REST

L'architettura REST, definita da Roy Fielding nella sua tesi di dottorato nel 2000, si fonda su vincoli architetturali precisi che garantiscono scalabilita, semplicita e interoperabilita.

**Stateless (Senza stato):** ogni richiesta dal client al server deve contenere tutte le informazioni necessarie per essere compresa e processata. Il server non mantiene alcuno stato della sessione client tra una richiesta e l'altra. Questo semplifica enormemente la scalabilita orizzontale: qualsiasi istanza del server puo gestire qualsiasi richiesta.

**Resource-Based (Basato su risorse):** tutto e una risorsa, identificata univocamente da un URI (Uniform Resource Identifier). Le risorse sono entita concettuali — un utente, un prodotto, un ordine — e non azioni. L'URI `/api/v1/utenti/42` identifica l'utente con ID 42, non un'azione sull'utente.

**Metodi HTTP:** le operazioni sulle risorse si esprimono attraverso i metodi HTTP standard: GET per leggere, POST per creare, PUT per sostituire, PATCH per aggiornare parzialmente, DELETE per eliminare. Ogni metodo ha una semantica ben definita che client e server condividono implicitamente.

**HATEOAS (Hypermedia As The Engine Of Application State):** le risposte del server dovrebbero includere link ipertestuali che guidano il client verso le azioni e le risorse correlate. Sebbene nella pratica questo principio venga spesso trascurato, la sua applicazione migliora significativamente la discoverability dell'API.

```json
{
  "id": 42,
  "nome": "Mario Rossi",
  "email": "mario@esempio.it",
  "_links": {
    "self": "/api/v1/utenti/42",
    "ordini": "/api/v1/utenti/42/ordini",
    "profilo": "/api/v1/utenti/42/profilo"
  }
}
```

### Principi di Design delle API

Una buona API e prevedibile, consistente e ben documentata. Il principio della minima sorpresa guida ogni decisione: uno sviluppatore che usa la tua API per la prima volta dovrebbe poter indovinare come funziona basandosi su cio che ha gia visto.

La **consistenza** e fondamentale: se una risorsa usa la paginazione con `?page=1&size=20`, tutte le risorse dovrebbero seguire la stessa convenzione. Se un endpoint restituisce errori con un certo formato, tutti gli endpoint dovrebbero fare lo stesso.

La **backward compatibility** e un altro principio guida: ogni modifica all'API dovrebbe, per quanto possibile, non rompere i client esistenti. Aggiungere campi a una risposta e sicuro; rimuoverli o rinominarli non lo e.

Il **principio di granularita** suggerisce di trovare il giusto equilibrio tra endpoint troppo generici (che restituiscono troppi dati) e troppo specifici (che richiedono troppe chiamate). Un endpoint `/api/v1/ordini/42` che include anche i dettagli degli articoli ordinati e spesso preferibile a richiedere due chiamate separate.

Infine, l'**idempotenza** e un concetto cruciale: ripetere la stessa richiesta deve produrre lo stesso risultato. GET, PUT e DELETE sono idempotenti per definizione; POST non lo e, ed e per questo che creare una risorsa due volte con gli stessi dati puo generare duplicati se non gestito correttamente.

### OpenAPI e Swagger

OpenAPI (precedentemente noto come Swagger) e lo standard de facto per descrivere le REST API. Un documento OpenAPI definisce endpoint, parametri, schemi di richiesta/risposta, autenticazione e molto altro in formato YAML o JSON.

```yaml
openapi: 3.1.0
info:
  title: API Prodotti
  version: 1.0.0
paths:
  /api/v1/prodotti:
    get:
      summary: Lista prodotti
      parameters:
        - name: categoria
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Lista dei prodotti
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Prodotto'
```

FastAPI genera automaticamente la specifica OpenAPI dal codice Python, eliminando la necessita di mantenere la documentazione separata.

---

## Progettazione API

### Naming Convention

La progettazione degli URI e un aspetto cruciale che determina l'usabilita e la chiarezza dell'API.

**Nomi plurali per le risorse:** le risorse si esprimono con nomi al plurale, mai con verbi. L'azione e implicita nel metodo HTTP.

```
# Corretto
GET    /api/v1/prodotti          # Lista prodotti
GET    /api/v1/prodotti/42       # Singolo prodotto
POST   /api/v1/prodotti          # Crea prodotto
PUT    /api/v1/prodotti/42       # Aggiorna prodotto
DELETE /api/v1/prodotti/42       # Elimina prodotto

# Errato
GET    /api/v1/getProdotti
POST   /api/v1/creaProdotto
DELETE /api/v1/eliminaProdotto/42
```

**kebab-case per URI multi-parola:** quando un nome di risorsa contiene piu parole, si usa il kebab-case (trattino basso o trattino medio). Lo standard piu diffuso e il trattino medio.

```
/api/v1/categorie-prodotti
/api/v1/ordini-acquisto
/api/v1/note-credito
```

**Risorse annidate per relazioni:** le relazioni tra risorse si esprimono attraverso l'annidamento degli URI, limitandosi pero a un massimo di due livelli di profondita.

```
/api/v1/utenti/42/ordini              # Ordini dell'utente 42
/api/v1/utenti/42/ordini/7            # Ordine 7 dell'utente 42
/api/v1/utenti/42/ordini/7/articoli   # Troppo profondo, meglio evitare
```

**Versioning:** esistono tre approcci principali per il versioning delle API.

```
# 1. URL Path (il piu comune e raccomandato)
/api/v1/prodotti
/api/v2/prodotti

# 2. Header personalizzato
GET /api/prodotti
Accept-Version: v1

# 3. Query parameter
GET /api/prodotti?version=1
```

Il versioning tramite URL path e il piu diffuso perche esplicito, facilmente testabile con un browser e semplice da implementare nel routing.

**Filtering, sorting e pagination tramite query parameters:**

```
# Filtro
GET /api/v1/prodotti?categoria=elettronica&prezzo_min=100

# Ordinamento
GET /api/v1/prodotti?sort=prezzo&order=desc

# Paginazione
GET /api/v1/prodotti?page=2&size=20

# Combinazione
GET /api/v1/prodotti?categoria=elettronica&sort=prezzo&order=asc&page=1&size=10
```

### HTTP Methods e Status Codes

Ogni metodo HTTP ha una semantica precisa che va rispettata rigorosamente.

| Metodo | Semantica | Idempotente | Corpo richiesta | Corpo risposta |
|--------|-----------|-------------|-----------------|----------------|
| GET | Leggere una risorsa | Si | No | Si |
| POST | Creare una risorsa | No | Si | Si |
| PUT | Sostituire interamente | Si | Si | Si |
| PATCH | Aggiornare parzialmente | No* | Si | Si |
| DELETE | Eliminare una risorsa | Si | No | Opzionale |

*PATCH puo essere reso idempotente, ma non lo e per definizione.

**Status codes essenziali:**

| Codice | Nome | Uso |
|--------|------|-----|
| 200 | OK | Richiesta riuscita (GET, PUT, PATCH) |
| 201 | Created | Risorsa creata con successo (POST) |
| 204 | No Content | Operazione riuscita senza corpo (DELETE) |
| 400 | Bad Request | Richiesta malformata o dati invalidi |
| 401 | Unauthorized | Autenticazione mancante o non valida |
| 403 | Forbidden | Autenticato ma non autorizzato |
| 404 | Not Found | Risorsa non trovata |
| 409 | Conflict | Conflitto con lo stato corrente (es. duplicato) |
| 422 | Unprocessable Entity | Dati sintatticamente corretti ma semanticamente invalidi |
| 429 | Too Many Requests | Rate limit superato |
| 500 | Internal Server Error | Errore generico del server |
| 503 | Service Unavailable | Servizio temporaneamente non disponibile |

**Formato errori RFC 7807 (Problem Details):**

```json
{
  "type": "https://api.esempio.it/errori/validazione",
  "title": "Errore di validazione",
  "status": 422,
  "detail": "Il campo 'email' non contiene un indirizzo email valido.",
  "instance": "/api/v1/utenti",
  "errors": [
    {
      "field": "email",
      "message": "Formato email non valido",
      "value": "non-una-email"
    }
  ]
}
```

Questo formato standardizzato permette ai client di gestire gli errori in modo programmatico e consistente.

---

## Implementazione con FastAPI

FastAPI e il framework Python moderno per eccellenza nella costruzione di REST API. Sfrutta i type hints di Python, la validazione automatica con Pydantic e genera documentazione OpenAPI senza configurazione aggiuntiva.

### CRUD Completo

Implementiamo un CRUD completo per una risorsa "prodotti" con tutti gli accorgimenti professionali.

```python
# app/schemas/prodotto.py
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from datetime import datetime


class ProdottoBase(BaseModel):
    """Schema base condiviso tra creazione e risposta."""
    nome: str = Field(
        ...,
        min_length=2,
        max_length=200,
        examples=["Laptop ProBook 450"]
    )
    descrizione: str | None = Field(
        None,
        max_length=2000,
        examples=["Laptop professionale con display 15.6 pollici"]
    )
    prezzo: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        examples=[999.99]
    )
    categoria: str = Field(
        ...,
        min_length=2,
        max_length=100,
        examples=["elettronica"]
    )
    disponibile: bool = Field(default=True)


class ProdottoCreate(ProdottoBase):
    """Schema per la creazione di un prodotto."""
    sku: str = Field(
        ...,
        pattern=r"^[A-Z]{2,4}-\d{4,8}$",
        examples=["EL-12345"]
    )


class ProdottoUpdate(BaseModel):
    """Schema per l'aggiornamento parziale (PATCH). Tutti i campi opzionali."""
    nome: str | None = Field(None, min_length=2, max_length=200)
    descrizione: str | None = Field(None, max_length=2000)
    prezzo: Decimal | None = Field(None, gt=0, decimal_places=2)
    categoria: str | None = Field(None, min_length=2, max_length=100)
    disponibile: bool | None = None


class ProdottoResponse(ProdottoBase):
    """Schema di risposta con campi generati dal server."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    creato_il: datetime
    aggiornato_il: datetime
```

```python
# app/dependencies.py
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

DATABASE_URL = "postgresql+asyncpg://utente:password@localhost/negozio"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection per la sessione database."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

```python
# app/routers/prodotti.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.dependencies import get_db
from app.models import Prodotto
from app.schemas.prodotto import (
    ProdottoCreate,
    ProdottoUpdate,
    ProdottoResponse,
)

router = APIRouter(prefix="/api/v1/prodotti", tags=["prodotti"])


@router.get(
    "/",
    response_model=dict,
    summary="Lista prodotti con paginazione",
)
async def lista_prodotti(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Numero pagina"),
    size: int = Query(20, ge=1, le=100, description="Elementi per pagina"),
    categoria: str | None = Query(None, description="Filtra per categoria"),
    sort: str = Query("id", description="Campo di ordinamento"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
):
    """Restituisce la lista paginata dei prodotti con filtri opzionali."""
    query = select(Prodotto)

    if categoria:
        query = query.where(Prodotto.categoria == categoria)

    # Conteggio totale
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    totale = result.scalar()

    # Ordinamento
    colonna = getattr(Prodotto, sort, Prodotto.id)
    if order == "desc":
        colonna = colonna.desc()
    query = query.order_by(colonna)

    # Paginazione
    offset = (page - 1) * size
    query = query.offset(offset).limit(size)

    result = await db.execute(query)
    prodotti = result.scalars().all()

    return {
        "data": [ProdottoResponse.model_validate(p) for p in prodotti],
        "meta": {
            "totale": totale,
            "pagina": page,
            "dimensione": size,
            "pagine_totali": (totale + size - 1) // size,
        },
        "links": {
            "self": f"/api/v1/prodotti?page={page}&size={size}",
            "next": f"/api/v1/prodotti?page={page + 1}&size={size}"
            if offset + size < totale
            else None,
            "prev": f"/api/v1/prodotti?page={page - 1}&size={size}"
            if page > 1
            else None,
        },
    }


@router.get(
    "/{prodotto_id}",
    response_model=ProdottoResponse,
    summary="Dettaglio prodotto",
)
async def dettaglio_prodotto(
    prodotto_id: int = Path(..., gt=0, description="ID del prodotto"),
    db: AsyncSession = Depends(get_db),
):
    """Restituisce i dettagli di un singolo prodotto."""
    result = await db.execute(
        select(Prodotto).where(Prodotto.id == prodotto_id)
    )
    prodotto = result.scalar_one_or_none()

    if not prodotto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prodotto con id {prodotto_id} non trovato",
        )

    return prodotto


@router.post(
    "/",
    response_model=ProdottoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crea un nuovo prodotto",
)
async def crea_prodotto(
    dati: ProdottoCreate,
    db: AsyncSession = Depends(get_db),
):
    """Crea un nuovo prodotto nel catalogo."""
    # Verifica SKU duplicato
    esistente = await db.execute(
        select(Prodotto).where(Prodotto.sku == dati.sku)
    )
    if esistente.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Un prodotto con SKU '{dati.sku}' esiste gia",
        )

    prodotto = Prodotto(**dati.model_dump())
    db.add(prodotto)
    await db.flush()
    await db.refresh(prodotto)

    return prodotto


@router.patch(
    "/{prodotto_id}",
    response_model=ProdottoResponse,
    summary="Aggiorna parzialmente un prodotto",
)
async def aggiorna_prodotto(
    dati: ProdottoUpdate,
    prodotto_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
):
    """Aggiorna solo i campi forniti del prodotto."""
    result = await db.execute(
        select(Prodotto).where(Prodotto.id == prodotto_id)
    )
    prodotto = result.scalar_one_or_none()

    if not prodotto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prodotto con id {prodotto_id} non trovato",
        )

    # Aggiorna solo i campi presenti (exclude_unset ignora i campi non forniti)
    dati_aggiornamento = dati.model_dump(exclude_unset=True)
    for campo, valore in dati_aggiornamento.items():
        setattr(prodotto, campo, valore)

    await db.flush()
    await db.refresh(prodotto)

    return prodotto


@router.delete(
    "/{prodotto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Elimina un prodotto",
)
async def elimina_prodotto(
    prodotto_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
):
    """Elimina definitivamente un prodotto dal catalogo."""
    result = await db.execute(
        select(Prodotto).where(Prodotto.id == prodotto_id)
    )
    prodotto = result.scalar_one_or_none()

    if not prodotto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prodotto con id {prodotto_id} non trovato",
        )

    await db.delete(prodotto)
```

### Validazione Input

La validazione e la prima linea di difesa dell'API. Pydantic permette validazioni sofisticate sia a livello di campo che di modello.

```python
from pydantic import BaseModel, Field, field_validator, model_validator
from decimal import Decimal
import re


class ProdottoCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=200)
    sku: str
    prezzo: Decimal = Field(..., gt=0)
    prezzo_scontato: Decimal | None = Field(None, ge=0)
    tags: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("sku")
    @classmethod
    def valida_sku(cls, v: str) -> str:
        """Valida il formato SKU: 2-4 lettere maiuscole, trattino, 4-8 cifre."""
        pattern = r"^[A-Z]{2,4}-\d{4,8}$"
        if not re.match(pattern, v):
            raise ValueError(
                "SKU deve seguire il formato: XX-1234 "
                "(2-4 lettere maiuscole, trattino, 4-8 cifre)"
            )
        return v

    @field_validator("tags")
    @classmethod
    def valida_tags(cls, v: list[str]) -> list[str]:
        """Normalizza i tags: lowercase e rimuovi duplicati."""
        tags_normalizzati = list({tag.lower().strip() for tag in v})
        return tags_normalizzati

    @model_validator(mode="after")
    def verifica_prezzo_scontato(self) -> "ProdottoCreate":
        """Il prezzo scontato deve essere inferiore al prezzo originale."""
        if self.prezzo_scontato is not None:
            if self.prezzo_scontato >= self.prezzo:
                raise ValueError(
                    "Il prezzo scontato deve essere inferiore al prezzo originale"
                )
        return self
```

**Validazione dei query parameters con FastAPI:**

```python
from fastapi import Query, Path


@router.get("/ricerca")
async def ricerca_prodotti(
    q: str = Query(
        ...,
        min_length=2,
        max_length=100,
        description="Termine di ricerca",
        examples=["laptop gaming"],
    ),
    prezzo_min: Decimal | None = Query(
        None, ge=0, description="Prezzo minimo"
    ),
    prezzo_max: Decimal | None = Query(
        None, ge=0, description="Prezzo massimo"
    ),
    categorie: list[str] | None = Query(
        None, description="Filtra per categorie multiple"
    ),
):
    """Ricerca prodotti con validazione completa dei parametri."""
    if prezzo_min and prezzo_max and prezzo_min > prezzo_max:
        raise HTTPException(
            status_code=422,
            detail="prezzo_min non puo essere maggiore di prezzo_max",
        )
    # ... logica di ricerca
```

### Paginazione

La paginazione e essenziale per gestire grandi quantita di dati in modo efficiente. Senza paginazione, una richiesta a una collezione con milioni di record tenterebbe di caricare tutto in memoria, causando timeout, consumo eccessivo di risorse e un'esperienza utente pessima.

Esistono due approcci principali, ciascuno con vantaggi e svantaggi specifici. La paginazione offset/limit e la piu intuitiva e semplice da implementare, ma soffre di problemi di prestazioni con offset molto grandi e di inconsistenza quando i dati cambiano tra una pagina e l'altra. La paginazione cursor-based risolve entrambi i problemi, ma e piu complessa da implementare e non supporta il salto diretto a una pagina specifica.

**Paginazione offset/limit (classica):**

```python
from pydantic import BaseModel


class PaginationMeta(BaseModel):
    totale: int
    pagina: int
    dimensione: int
    pagine_totali: int


class PaginatedResponse(BaseModel):
    data: list
    meta: PaginationMeta
    links: dict[str, str | None]


async def pagina_risultati(
    query,
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    base_url: str = "",
) -> PaginatedResponse:
    """Utility generica per la paginazione offset/limit."""
    # Conteggio totale
    count_q = select(func.count()).select_from(query.subquery())
    totale = (await db.execute(count_q)).scalar()

    # Applica paginazione
    offset = (page - 1) * size
    result = await db.execute(query.offset(offset).limit(size))
    items = result.scalars().all()

    pagine_totali = (totale + size - 1) // size

    return PaginatedResponse(
        data=items,
        meta=PaginationMeta(
            totale=totale,
            pagina=page,
            dimensione=size,
            pagine_totali=pagine_totali,
        ),
        links={
            "self": f"{base_url}?page={page}&size={size}",
            "first": f"{base_url}?page=1&size={size}",
            "last": f"{base_url}?page={pagine_totali}&size={size}",
            "next": f"{base_url}?page={page + 1}&size={size}"
            if page < pagine_totali
            else None,
            "prev": f"{base_url}?page={page - 1}&size={size}"
            if page > 1
            else None,
        },
    )
```

**Paginazione cursor-based (per dataset grandi):**

```python
import base64
import json
from datetime import datetime


def codifica_cursor(prodotto_id: int, creato_il: datetime) -> str:
    """Codifica un cursor in base64 per la paginazione."""
    payload = {"id": prodotto_id, "ts": creato_il.isoformat()}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def decodifica_cursor(cursor: str) -> dict:
    """Decodifica un cursor base64."""
    payload = json.loads(base64.urlsafe_b64decode(cursor.encode()))
    return payload


@router.get("/stream")
async def lista_prodotti_cursor(
    cursor: str | None = Query(None, description="Cursor per la pagina successiva"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Paginazione cursor-based, ideale per feed e liste in tempo reale."""
    query = select(Prodotto).order_by(Prodotto.creato_il.desc(), Prodotto.id.desc())

    if cursor:
        dati_cursor = decodifica_cursor(cursor)
        query = query.where(
            (Prodotto.creato_il < dati_cursor["ts"])
            | (
                (Prodotto.creato_il == dati_cursor["ts"])
                & (Prodotto.id < dati_cursor["id"])
            )
        )

    query = query.limit(limit + 1)  # +1 per sapere se c'e una pagina successiva
    result = await db.execute(query)
    prodotti = result.scalars().all()

    ha_prossima = len(prodotti) > limit
    if ha_prossima:
        prodotti = prodotti[:limit]

    prossimo_cursor = None
    if ha_prossima and prodotti:
        ultimo = prodotti[-1]
        prossimo_cursor = codifica_cursor(ultimo.id, ultimo.creato_il)

    return {
        "data": prodotti,
        "next_cursor": prossimo_cursor,
        "has_more": ha_prossima,
    }
```

### Filtri e Ordinamento

Un sistema di filtri flessibile permette ai client di richiedere esattamente i dati di cui hanno bisogno.

```python
from enum import Enum
from dataclasses import dataclass


class OrdinamentoProdotto(str, Enum):
    NOME = "nome"
    PREZZO = "prezzo"
    CREATO_IL = "creato_il"
    CATEGORIA = "categoria"


class DirezionOrdinamento(str, Enum):
    ASC = "asc"
    DESC = "desc"


@dataclass
class FiltriProdotto:
    """Raggruppa tutti i parametri di filtro per i prodotti."""
    categoria: str | None = None
    prezzo_min: Decimal | None = None
    prezzo_max: Decimal | None = None
    disponibile: bool | None = None
    q: str | None = None  # ricerca testuale


def applica_filtri(query, filtri: FiltriProdotto):
    """Applica filtri dinamicamente alla query."""
    if filtri.categoria:
        query = query.where(Prodotto.categoria == filtri.categoria)
    if filtri.prezzo_min is not None:
        query = query.where(Prodotto.prezzo >= filtri.prezzo_min)
    if filtri.prezzo_max is not None:
        query = query.where(Prodotto.prezzo <= filtri.prezzo_max)
    if filtri.disponibile is not None:
        query = query.where(Prodotto.disponibile == filtri.disponibile)
    if filtri.q:
        query = query.where(
            Prodotto.nome.ilike(f"%{filtri.q}%")
            | Prodotto.descrizione.ilike(f"%{filtri.q}%")
        )
    return query


@router.get("/")
async def lista_prodotti(
    categoria: str | None = Query(None),
    prezzo_min: Decimal | None = Query(None, ge=0),
    prezzo_max: Decimal | None = Query(None, ge=0),
    disponibile: bool | None = Query(None),
    q: str | None = Query(None, min_length=2),
    sort: OrdinamentoProdotto = Query(OrdinamentoProdotto.CREATO_IL),
    order: DirezionOrdinamento = Query(DirezionOrdinamento.DESC),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Lista prodotti con filtri dinamici, ordinamento e paginazione."""
    filtri = FiltriProdotto(
        categoria=categoria,
        prezzo_min=prezzo_min,
        prezzo_max=prezzo_max,
        disponibile=disponibile,
        q=q,
    )

    query = select(Prodotto)
    query = applica_filtri(query, filtri)

    # Ordinamento
    colonna_sort = getattr(Prodotto, sort.value)
    if order == DirezionOrdinamento.DESC:
        colonna_sort = colonna_sort.desc()
    query = query.order_by(colonna_sort)

    return await pagina_risultati(query, db, page, size, "/api/v1/prodotti")
```

### Autenticazione e Autorizzazione

L'autenticazione e l'autorizzazione sono due concetti distinti ma complementari. L'**autenticazione** risponde alla domanda "chi sei?" — verifica l'identita del chiamante tramite credenziali (token, API key, certificato). L'**autorizzazione** risponde alla domanda "cosa puoi fare?" — verifica che l'utente autenticato abbia i permessi necessari per l'operazione richiesta.

FastAPI integra entrambe attraverso il suo sistema di dependency injection, che permette di dichiarare requisiti di sicurezza come dipendenze degli endpoint. Questo approccio rende il codice di autenticazione riutilizzabile, testabile e componibile.

**Autenticazione JWT con OAuth2:**

```python
# app/auth/jwt.py
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

SECRET_KEY = "la-tua-chiave-segreta-molto-lunga-e-complessa"
ALGORITHM = "HS256"
ACCESS_TOKEN_SCADENZA_MINUTI = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    sub: str
    ruolo: str
    exp: datetime


def crea_access_token(dati: dict, scadenza: timedelta | None = None) -> str:
    """Genera un JWT token con scadenza configurabile."""
    da_codificare = dati.copy()
    scade = datetime.now(timezone.utc) + (
        scadenza or timedelta(minutes=ACCESS_TOKEN_SCADENZA_MINUTI)
    )
    da_codificare.update({"exp": scade})
    return jwt.encode(da_codificare, SECRET_KEY, algorithm=ALGORITHM)


def verifica_password(password_chiara: str, hash_password: str) -> bool:
    return pwd_context.verify(password_chiara, hash_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)
```

```python
# app/auth/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_utente_corrente(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Utente:
    """Estrae l'utente dal JWT token."""
    eccezione_credenziali = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenziali non valide",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise eccezione_credenziali
    except JWTError:
        raise eccezione_credenziali

    utente = await db.get(Utente, int(user_id))
    if utente is None:
        raise eccezione_credenziali

    return utente


def richiedi_ruolo(*ruoli_ammessi: str):
    """Dependency factory per il controllo dei ruoli (RBAC)."""
    async def verifica_ruolo(
        utente: Utente = Depends(get_utente_corrente),
    ) -> Utente:
        if utente.ruolo not in ruoli_ammessi:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Ruolo '{utente.ruolo}' non autorizzato. "
                       f"Ruoli richiesti: {', '.join(ruoli_ammessi)}",
            )
        return utente
    return verifica_ruolo


async def autenticazione_api_key(
    api_key: str | None = Depends(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> Utente:
    """Autenticazione alternativa tramite API Key."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key mancante nell'header X-API-Key",
        )

    result = await db.execute(
        select(APIKey).where(APIKey.chiave == api_key, APIKey.attiva == True)
    )
    chiave = result.scalar_one_or_none()

    if not chiave:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key non valida o disattivata",
        )

    return await db.get(Utente, chiave.utente_id)
```

```python
# Uso delle dependency di autenticazione nei router
@router.get("/profilo", response_model=UtenteResponse)
async def profilo_utente(
    utente: Utente = Depends(get_utente_corrente),
):
    """Endpoint accessibile a qualsiasi utente autenticato."""
    return utente


@router.delete(
    "/{utente_id}",
    dependencies=[Depends(richiedi_ruolo("admin"))],
)
async def elimina_utente(utente_id: int, db: AsyncSession = Depends(get_db)):
    """Endpoint accessibile solo agli amministratori."""
    # ... logica di eliminazione
```

### Rate Limiting

Il rate limiting e un meccanismo di protezione fondamentale per qualsiasi API in produzione. Protegge da abusi intenzionali (attacchi DDoS, scraping aggressivo), da errori dei client (loop infiniti, retry senza backoff) e garantisce un utilizzo equo delle risorse tra tutti i consumatori dell'API. Senza rate limiting, un singolo client mal configurato puo degradare le prestazioni per tutti gli altri utenti.

```python
# app/middleware/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request

limiter = Limiter(key_func=get_remote_address)


def configura_rate_limiting(app: FastAPI):
    """Configura il rate limiting globale e per-endpoint."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Uso negli endpoint
@router.get("/")
@limiter.limit("100/minute")
async def lista_prodotti(request: Request):
    """Massimo 100 richieste al minuto per IP."""
    ...


@router.post("/")
@limiter.limit("10/minute")
async def crea_prodotto(request: Request, dati: ProdottoCreate):
    """Limite piu restrittivo per operazioni di scrittura."""
    ...
```

**Rate limiting personalizzato per utente:**

```python
from slowapi import Limiter


def chiave_per_utente(request: Request) -> str:
    """Usa l'ID utente come chiave per il rate limiting."""
    token = request.headers.get("Authorization", "")
    if token.startswith("Bearer "):
        try:
            payload = jwt.decode(
                token[7:], SECRET_KEY, algorithms=[ALGORITHM]
            )
            return f"user:{payload.get('sub', 'anonymous')}"
        except JWTError:
            pass
    return get_remote_address(request)


limiter_per_utente = Limiter(key_func=chiave_per_utente)


@router.post("/ordini")
@limiter_per_utente.limit("5/minute")
async def crea_ordine(request: Request):
    """Massimo 5 ordini al minuto per utente autenticato."""
    ...
```

### Caching

Il caching e una delle strategie piu efficaci per migliorare le prestazioni di un'API. Riduce il carico sul server, diminuisce la latenza percepita dal client e puo abbattere significativamente i costi infrastrutturali. Tuttavia, il caching introduce anche complessita nella gestione della coerenza dei dati: un dato in cache potrebbe essere obsoleto, e il client potrebbe vedere informazioni non aggiornate.

Esistono diversi livelli di caching applicabili a una REST API: caching HTTP tramite headers standard (ETags, Cache-Control), caching applicativo con Redis o Memcached, e caching a livello di CDN per contenuti statici o semi-statici.

**ETags e Cache-Control:**

```python
import hashlib
from fastapi import Request
from fastapi.responses import JSONResponse


@router.get("/{prodotto_id}")
async def dettaglio_prodotto(
    prodotto_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Restituisce il prodotto con supporto ETag per il caching."""
    prodotto = await db.get(Prodotto, prodotto_id)
    if not prodotto:
        raise HTTPException(status_code=404)

    # Genera ETag basato sul contenuto
    dati = ProdottoResponse.model_validate(prodotto).model_dump_json()
    etag = hashlib.md5(dati.encode()).hexdigest()

    # Verifica If-None-Match
    if_none_match = request.headers.get("If-None-Match")
    if if_none_match == etag:
        return JSONResponse(status_code=304, content=None)

    return JSONResponse(
        content=json.loads(dati),
        headers={
            "ETag": etag,
            "Cache-Control": "private, max-age=60",
        },
    )
```

**Caching con Redis:**

```python
import redis.asyncio as redis
import json
from functools import wraps

redis_client = redis.from_url("redis://localhost:6379", decode_responses=True)


def cache_redis(ttl_secondi: int = 300, prefisso: str = "api"):
    """Decorator per il caching automatico con Redis."""
    def decoratore(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Costruisci la chiave cache
            chiave = f"{prefisso}:{func.__name__}:{hash(str(kwargs))}"

            # Prova a recuperare dalla cache
            dati_cache = await redis_client.get(chiave)
            if dati_cache:
                return json.loads(dati_cache)

            # Esegui la funzione e salva in cache
            risultato = await func(*args, **kwargs)
            await redis_client.setex(
                chiave,
                ttl_secondi,
                json.dumps(risultato, default=str),
            )

            return risultato
        return wrapper
    return decoratore


async def invalida_cache_prodotto(prodotto_id: int):
    """Invalida la cache quando un prodotto viene modificato."""
    pattern = f"api:*prodott*:{prodotto_id}*"
    async for chiave in redis_client.scan_iter(match=pattern):
        await redis_client.delete(chiave)

    # Invalida anche la lista prodotti
    async for chiave in redis_client.scan_iter(match="api:lista_prodotti:*"):
        await redis_client.delete(chiave)
```

### Lifespan Events — Inizializzazione e Shutdown

A partire da FastAPI 0.93+ (consolidato in 0.115+), il meccanismo raccomandato per gestire la logica di startup e shutdown e il parametro `lifespan`, che sostituisce i deprecati decoratori `@app.on_event("startup")` e `@app.on_event("shutdown")`. Il lifespan utilizza un async context manager: il codice prima di `yield` viene eseguito all'avvio dell'applicazione, quello dopo `yield` allo shutdown. Questo approccio e superiore perche permette di condividere risorse (pool di connessioni, client HTTP, cache) tra la fase di inizializzazione e quella di chiusura in modo type-safe tramite `app.state`.

```python
# app/main.py — lifespan con risorse condivise
from contextlib import asynccontextmanager
from fastapi import FastAPI
import httpx
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestisce il ciclo di vita dell'applicazione.

    Startup: crea pool di connessioni, client HTTP, connessione Redis.
    Shutdown: chiude tutte le risorse in modo ordinato.
    """
    # --- STARTUP ---
    engine = create_async_engine(settings.database_url, pool_size=20)
    app.state.db_sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    app.state.http_client = httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    )
    app.state.redis = redis.from_url(
        settings.redis_url, decode_responses=True
    )

    yield  # L'applicazione serve le richieste

    # --- SHUTDOWN ---
    await app.state.http_client.aclose()
    await app.state.redis.aclose()
    await engine.dispose()


app = FastAPI(
    title="API Catalogo",
    version="1.0.0",
    lifespan=lifespan,
)
```

Il vantaggio chiave rispetto ai vecchi `on_event` e duplice: primo, se si definisce `lifespan`, tutti i `@app.on_event()` vengono ignorati, eliminando ambiguita; secondo, le risorse condivise tramite `app.state` sono accessibili in qualsiasi dependency senza variabili globali.

### BackgroundTasks — Operazioni Asincrone Post-Risposta

`BackgroundTasks` permette di eseguire operazioni dopo l'invio della risposta al client, senza bloccare la richiesta. E ideale per attivita come l'invio di email, l'aggiornamento di indici di ricerca, la generazione di report o la notifica a servizi esterni. A differenza di un task queue come Celery, i BackgroundTasks vengono eseguiti nello stesso processo — sono quindi adatti a operazioni leggere e non critiche.

```python
from fastapi import BackgroundTasks, Depends
from datetime import datetime, timezone


async def invia_notifica_email(email: str, oggetto: str, corpo: str):
    """Task eseguito in background dopo la risposta HTTP."""
    # Simula l'invio email (in produzione usare un servizio SMTP)
    async with httpx.AsyncClient() as client:
        await client.post(
            "https://api.email-service.it/send",
            json={"to": email, "subject": oggetto, "body": corpo},
        )


async def aggiorna_log_attivita(
    utente_id: int,
    azione: str,
    db_session,
):
    """Registra l'attivita dell'utente in background."""
    async with db_session() as db:
        log = LogAttivita(
            utente_id=utente_id,
            azione=azione,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(log)
        await db.commit()


@router.post("/ordini", status_code=201)
async def crea_ordine(
    dati: OrdineCreate,
    background_tasks: BackgroundTasks,
    utente: Utente = Depends(get_utente_corrente),
    db: AsyncSession = Depends(get_db),
):
    """Crea un ordine e invia conferma email in background."""
    ordine = Ordine(**dati.model_dump(), utente_id=utente.id)
    db.add(ordine)
    await db.flush()
    await db.refresh(ordine)

    # Questi task vengono eseguiti DOPO l'invio della risposta
    background_tasks.add_task(
        invia_notifica_email,
        utente.email,
        f"Conferma ordine #{ordine.id}",
        f"Il tuo ordine e stato ricevuto. Totale: {ordine.totale}€",
    )
    background_tasks.add_task(
        aggiorna_log_attivita,
        utente.id,
        f"ordine_creato:{ordine.id}",
        db_session=app.state.db_sessionmaker,
    )

    return OrdineResponse.model_validate(ordine)
```

Per operazioni piu complesse o che richiedono garanzie di esecuzione (retry, persistenza), e preferibile utilizzare un task queue dedicato come Celery con Redis o RabbitMQ come broker. I BackgroundTasks non offrono garanzie di completamento in caso di crash del processo.

### Custom Middleware — Intercettare il Ciclo Request/Response

FastAPI, attraverso Starlette, offre due approcci per la creazione di middleware personalizzato: il decoratore `@app.middleware("http")` per middleware semplici e la classe `BaseHTTPMiddleware` per middleware piu strutturati. Il middleware intercetta ogni richiesta prima che raggiunga l'endpoint e ogni risposta prima che venga inviata al client, rendendolo ideale per logging, timing, header injection e validazioni trasversali.

```python
# app/middleware/request_id.py
import uuid
import time
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("api")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Aggiunge un ID univoco a ogni richiesta per la tracciabilita."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(
            "X-Request-ID", str(uuid.uuid4())
        )
        # Rende il request_id disponibile nel contesto della richiesta
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    """Misura e logga il tempo di elaborazione di ogni richiesta."""

    async def dispatch(self, request: Request, call_next):
        inizio = time.perf_counter()
        response = await call_next(request)
        durata_ms = (time.perf_counter() - inizio) * 1000

        response.headers["X-Process-Time-Ms"] = f"{durata_ms:.2f}"
        logger.info(
            "richiesta completata",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "durata_ms": round(durata_ms, 2),
                "request_id": getattr(request.state, "request_id", "N/A"),
            },
        )
        return response


# Registrazione middleware (ordine inverso di esecuzione)
# L'ultimo aggiunto e il primo eseguito
app.add_middleware(TimingMiddleware)
app.add_middleware(RequestIdMiddleware)
```

L'ordine di registrazione dei middleware e cruciale: Starlette li esegue nell'ordine inverso rispetto a come vengono aggiunti. Il middleware registrato per ultimo sara il primo a processare la richiesta. Per questo motivo, middleware come il RequestId (che genera un identificatore necessario agli altri) vanno registrati per ultimi, in modo che vengano eseguiti per primi.

---

## Implementazione con Flask

Flask rimane una scelta valida per API piu semplici o quando si lavora con codebase esistenti. Mentre FastAPI e costruito attorno al paradigma asincrono e alla generazione automatica della documentazione, Flask offre maggiore flessibilita e un ecosistema di estensioni maturo e collaudato.

La differenza principale nell'approccio e filosofica: FastAPI adotta il paradigma "batteries included" con validazione automatica, documentazione generata e dependency injection nativi; Flask segue il principio del "micro-framework" dove ogni funzionalita viene aggiunta esplicitamente tramite estensioni. Nessuno dei due approcci e intrinsecamente superiore — la scelta dipende dal contesto del progetto, dal team e dai requisiti.

### Flask-smorest con Marshmallow

flask-smorest e l'estensione moderna per costruire REST API con Flask, combinando la serializzazione di Marshmallow con la generazione automatica della documentazione OpenAPI. Rispetto al piu vecchio Flask-RESTful, flask-smorest offre un supporto migliore per OpenAPI 3.x e un'integrazione piu naturale con i Blueprint di Flask.

```python
# app/__init__.py
from flask import Flask
from flask_smorest import Api

def create_app():
    app = Flask(__name__)
    app.config["API_TITLE"] = "API Prodotti"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = (
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    )

    api = Api(app)

    from app.resources.prodotti import blp as prodotti_blp
    api.register_blueprint(prodotti_blp)

    return app
```

```python
# app/schemas.py
from marshmallow import Schema, fields, validate, validates, ValidationError


class ProdottoSchema(Schema):
    id = fields.Int(dump_only=True)
    nome = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    descrizione = fields.Str(validate=validate.Length(max=2000))
    prezzo = fields.Decimal(required=True, as_string=True)
    categoria = fields.Str(required=True, validate=validate.Length(min=2, max=100))
    sku = fields.Str(required=True, validate=validate.Regexp(r"^[A-Z]{2,4}-\d{4,8}$"))
    disponibile = fields.Bool(load_default=True)
    creato_il = fields.DateTime(dump_only=True)

    @validates("prezzo")
    def valida_prezzo(self, value):
        if value <= 0:
            raise ValidationError("Il prezzo deve essere maggiore di zero.")


class ProdottoUpdateSchema(Schema):
    nome = fields.Str(validate=validate.Length(min=2, max=200))
    descrizione = fields.Str(validate=validate.Length(max=2000))
    prezzo = fields.Decimal(as_string=True)
    categoria = fields.Str(validate=validate.Length(min=2, max=100))
    disponibile = fields.Bool()


class PaginazioneQuerySchema(Schema):
    page = fields.Int(load_default=1, validate=validate.Range(min=1))
    size = fields.Int(load_default=20, validate=validate.Range(min=1, max=100))
```

```python
# app/resources/prodotti.py
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from app.schemas import ProdottoSchema, ProdottoUpdateSchema, PaginazioneQuerySchema

blp = Blueprint(
    "prodotti",
    __name__,
    url_prefix="/api/v1/prodotti",
    description="Operazioni sui prodotti",
)


@blp.route("/")
class ProdottiList(MethodView):

    @blp.arguments(PaginazioneQuerySchema, location="query")
    @blp.response(200, ProdottoSchema(many=True))
    def get(self, args):
        """Lista prodotti con paginazione."""
        page = args["page"]
        size = args["size"]
        prodotti = Prodotto.query.paginate(
            page=page, per_page=size, error_out=False
        )
        return prodotti.items

    @blp.arguments(ProdottoSchema)
    @blp.response(201, ProdottoSchema)
    def post(self, dati_nuovo):
        """Crea un nuovo prodotto."""
        prodotto = Prodotto(**dati_nuovo)
        db.session.add(prodotto)
        db.session.commit()
        return prodotto


@blp.route("/<int:prodotto_id>")
class ProdottiDetail(MethodView):

    @blp.response(200, ProdottoSchema)
    def get(self, prodotto_id):
        """Dettaglio di un singolo prodotto."""
        prodotto = Prodotto.query.get_or_404(prodotto_id)
        return prodotto

    @blp.arguments(ProdottoUpdateSchema)
    @blp.response(200, ProdottoSchema)
    def patch(self, dati_aggiornamento, prodotto_id):
        """Aggiornamento parziale di un prodotto."""
        prodotto = Prodotto.query.get_or_404(prodotto_id)
        for campo, valore in dati_aggiornamento.items():
            setattr(prodotto, campo, valore)
        db.session.commit()
        return prodotto

    @blp.response(204)
    def delete(self, prodotto_id):
        """Elimina un prodotto."""
        prodotto = Prodotto.query.get_or_404(prodotto_id)
        db.session.delete(prodotto)
        db.session.commit()
```

---

## Client API (requests/httpx)

Costruire API e solo meta del lavoro: bisogna anche saperle consumare efficacemente. In un'architettura a microservizi, ogni servizio e sia produttore che consumatore di API, rendendo la padronanza delle librerie client altrettanto importante quanto quella dei framework server-side.

Python offre due librerie eccellenti per questo scopo: `requests`, lo standard storico con un'interfaccia intuitiva, e `httpx`, l'alternativa moderna con supporto nativo per async e HTTP/2.

### requests Library

La libreria requests e lo standard de facto per le chiamate HTTP sincrone in Python. La sua interfaccia elegante e il suo approccio "human-friendly" l'hanno resa la libreria piu scaricata dell'intero ecosistema Python. Per le API REST, requests offre tutto il necessario: gestione automatica del JSON, session con connection pooling, autenticazione pluggabile e gestione robusta dei timeout.

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# Configurazione con session per connection pooling e retry
session = requests.Session()

strategia_retry = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["GET", "PUT", "DELETE"],
)

adapter = HTTPAdapter(max_retries=strategia_retry)
session.mount("https://", adapter)
session.mount("http://", adapter)

# Headers comuni
session.headers.update({
    "Content-Type": "application/json",
    "Authorization": "Bearer il-tuo-token-jwt",
})

BASE_URL = "https://api.esempio.it/api/v1"


# GET — Lista risorse con paginazione
risposta = session.get(
    f"{BASE_URL}/prodotti",
    params={"page": 1, "size": 20, "categoria": "elettronica"},
    timeout=10,
)
risposta.raise_for_status()  # Solleva eccezione per errori HTTP
prodotti = risposta.json()
print(f"Trovati {prodotti['meta']['totale']} prodotti")


# POST — Crea risorsa
nuovo_prodotto = {
    "nome": "Monitor UltraWide 34 pollici",
    "prezzo": "599.99",
    "categoria": "elettronica",
    "sku": "EL-99001",
}
risposta = session.post(
    f"{BASE_URL}/prodotti",
    json=nuovo_prodotto,
    timeout=10,
)
if risposta.status_code == 201:
    prodotto_creato = risposta.json()
    print(f"Prodotto creato con ID: {prodotto_creato['id']}")


# PUT — Sostituzione completa
prodotto_aggiornato = {
    "nome": "Monitor UltraWide 34 pollici - Edizione 2025",
    "prezzo": "549.99",
    "categoria": "elettronica",
    "sku": "EL-99001",
    "disponibile": True,
}
risposta = session.put(
    f"{BASE_URL}/prodotti/42",
    json=prodotto_aggiornato,
    timeout=10,
)


# PATCH — Aggiornamento parziale
risposta = session.patch(
    f"{BASE_URL}/prodotti/42",
    json={"prezzo": "479.99"},
    timeout=10,
)


# DELETE — Eliminazione
risposta = session.delete(f"{BASE_URL}/prodotti/42", timeout=10)
if risposta.status_code == 204:
    print("Prodotto eliminato con successo")


# Upload file
with open("immagine_prodotto.jpg", "rb") as f:
    risposta = session.post(
        f"{BASE_URL}/prodotti/42/immagine",
        files={"file": ("foto.jpg", f, "image/jpeg")},
        timeout=30,
    )
```

### httpx Library

httpx e l'evoluzione moderna di requests, con supporto nativo per async e HTTP/2. Offre un'API quasi identica a requests per il client sincrono, rendendo la migrazione estremamente semplice, ma aggiunge funzionalita cruciali come il client asincrono, il supporto HTTP/2 per multiplexing delle connessioni, e lo streaming bidirezionale. In contesti ad alta concorrenza — come un servizio che deve aggregare dati da multiple API esterne — httpx asincrono offre prestazioni nettamente superiori rispetto a requests.

```python
import httpx
import asyncio


# Client sincrono (simile a requests)
with httpx.Client(
    base_url="https://api.esempio.it/api/v1",
    headers={"Authorization": "Bearer token"},
    timeout=10.0,
) as client:
    risposta = client.get("/prodotti", params={"page": 1})
    prodotti = risposta.json()


# Client asincrono (ideale per alta concorrenza)
async def operazioni_api():
    async with httpx.AsyncClient(
        base_url="https://api.esempio.it/api/v1",
        headers={"Authorization": "Bearer token"},
        timeout=10.0,
        http2=True,  # Abilita HTTP/2
    ) as client:
        # Richieste parallele con asyncio.gather
        risultati = await asyncio.gather(
            client.get("/prodotti", params={"categoria": "elettronica"}),
            client.get("/prodotti", params={"categoria": "abbigliamento"}),
            client.get("/categorie"),
        )

        elettronica, abbigliamento, categorie = [r.json() for r in risultati]

        # Streaming di risposte grandi
        async with client.stream("GET", "/export/prodotti") as risposta:
            async for chunk in risposta.aiter_bytes():
                # Processa chunk per chunk senza caricare tutto in memoria
                elabora_chunk(chunk)


asyncio.run(operazioni_api())
```

### httpx — Pattern Avanzati per la Produzione

In ambienti di produzione, l'uso base di httpx non e sufficiente. Servono configurazioni esplicite per il connection pooling, le strategie di retry, i timeout granulari e lo streaming di payload di grandi dimensioni. Questi pattern trasformano httpx da semplice libreria client a infrastruttura affidabile per la comunicazione inter-servizio.

**Connection pooling e limiti di connessione:**

Il connection pooling evita il costo di stabilire una nuova connessione TCP (e handshake TLS) per ogni richiesta. httpx gestisce automaticamente il pool quando si usa un'istanza `Client` o `AsyncClient`, ma i parametri di default vanno calibrati in base al carico previsto.

```python
import httpx

# Configurazione esplicita dei limiti di connessione
limiti = httpx.Limits(
    max_connections=100,         # Connessioni totali nel pool
    max_keepalive_connections=20, # Connessioni keep-alive mantenute
    keepalive_expiry=30,         # Secondi prima di chiudere connessioni idle
)

# Timeout granulari per fase della connessione
timeout = httpx.Timeout(
    connect=5.0,   # Timeout per stabilire la connessione TCP
    read=30.0,     # Timeout per ricevere la risposta
    write=10.0,    # Timeout per inviare il body della richiesta
    pool=5.0,      # Timeout per ottenere una connessione dal pool
)

async def crea_client_produzione() -> httpx.AsyncClient:
    """Crea un client httpx configurato per la produzione."""
    return httpx.AsyncClient(
        base_url="https://api.servizio-esterno.it",
        limits=limiti,
        timeout=timeout,
        http2=True,
        headers={"User-Agent": "MioServizio/1.0"},
    )
```

**Retry automatico con transport personalizzato:**

httpx supporta i retry configurando un transport dedicato. I retry vanno applicati solo a errori di connessione, non a errori applicativi (4xx), per evitare di ripetere operazioni non idempotenti.

```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


# Approccio 1: retry nativo di httpx (solo errori di connessione)
transport = httpx.AsyncHTTPTransport(retries=3)
client = httpx.AsyncClient(transport=transport)


# Approccio 2: retry con tenacity per controllo granulare
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.ConnectError, httpx.ReadTimeout)),
    reraise=True,
)
async def chiama_servizio_con_retry(
    client: httpx.AsyncClient,
    metodo: str,
    url: str,
    **kwargs,
) -> httpx.Response:
    """Chiama un servizio esterno con retry e backoff esponenziale."""
    risposta = await client.request(metodo, url, **kwargs)
    # Solleva eccezione per status 5xx (trigger retry)
    if risposta.status_code >= 500:
        raise httpx.HTTPStatusError(
            f"Server error: {risposta.status_code}",
            request=risposta.request,
            response=risposta,
        )
    return risposta
```

**Streaming di risposte di grandi dimensioni:**

Per risposte che non devono essere caricate interamente in memoria (export CSV, file binari, feed di dati), httpx offre lo streaming asincrono con `aiter_bytes()`, `aiter_text()` e `aiter_lines()`.

```python
async def scarica_export_grande(client: httpx.AsyncClient, url: str, destinazione: str):
    """Scarica un file grande in streaming senza caricarlo in memoria."""
    async with client.stream("GET", url) as risposta:
        risposta.raise_for_status()
        dimensione_totale = int(risposta.headers.get("content-length", 0))
        scaricati = 0

        async with aiofiles.open(destinazione, "wb") as f:
            async for chunk in risposta.aiter_bytes(chunk_size=8192):
                await f.write(chunk)
                scaricati += len(chunk)

        return {"scaricati_bytes": scaricati, "file": destinazione}


async def processa_stream_ndjson(client: httpx.AsyncClient, url: str):
    """Processa uno stream NDJSON (newline-delimited JSON) riga per riga."""
    risultati = []
    async with client.stream("GET", url) as risposta:
        async for riga in risposta.aiter_lines():
            if riga.strip():
                dato = json.loads(riga)
                risultati.append(dato)
    return risultati
```

La regola fondamentale per il client httpx in produzione: creare una singola istanza `AsyncClient` (o poche istanze condivise) e riutilizzarla per tutta la durata del servizio, tipicamente attraverso il lifespan di FastAPI. Istanziare un nuovo client per ogni richiesta vanifica completamente i benefici del connection pooling.

---

## Testing API

I test sono la garanzia che l'API funzioni correttamente e continui a funzionare dopo ogni modifica. Per le REST API, il testing assume un'importanza ancora maggiore rispetto ad altre tipologie di software: l'API e un contratto pubblico, e qualsiasi modifica involontaria al comportamento puo rompere decine di client che dipendono da quel contratto.

Una strategia di testing efficace per le API prevede diversi livelli: **unit test** per la logica di business isolata, **integration test** per verificare l'interazione tra componenti (routing, validazione, database), e **end-to-end test** per verificare flussi completi come il ciclo di autenticazione seguito da operazioni CRUD.

### pytest + TestClient di FastAPI

FastAPI rende il testing particolarmente semplice grazie all'integrazione con httpx e al suo sistema di dependency injection che permette di sostituire facilmente le dipendenze reali (come il database di produzione) con alternative di test.

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.dependencies import get_db
from app.models import Base
from app.auth.jwt import crea_access_token

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine_test = create_async_engine(TEST_DATABASE_URL, echo=False)
async_session_test = async_sessionmaker(
    engine_test, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(autouse=True)
async def setup_database():
    """Crea e distrugge il database per ogni test."""
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    """Fornisce una sessione database per i test."""
    async with async_session_test() as session:
        yield session


@pytest.fixture
async def client(db_session):
    """Client HTTP per i test con database di test iniettato."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def token_admin() -> str:
    """Genera un token JWT per un utente admin di test."""
    return crea_access_token({"sub": "1", "ruolo": "admin"})


@pytest.fixture
def token_utente() -> str:
    """Genera un token JWT per un utente normale di test."""
    return crea_access_token({"sub": "2", "ruolo": "utente"})


@pytest.fixture
def headers_admin(token_admin) -> dict:
    return {"Authorization": f"Bearer {token_admin}"}


@pytest.fixture
def prodotto_esempio() -> dict:
    """Dati di esempio per creare un prodotto."""
    return {
        "nome": "Laptop Test",
        "descrizione": "Un laptop per i test",
        "prezzo": "999.99",
        "categoria": "elettronica",
        "sku": "EL-10001",
        "disponibile": True,
    }
```

```python
# tests/test_prodotti.py
import pytest
from httpx import AsyncClient


class TestCreazioneProdotto:
    """Test per l'endpoint POST /api/v1/prodotti."""

    @pytest.mark.anyio
    async def test_crea_prodotto_successo(
        self, client: AsyncClient, headers_admin: dict, prodotto_esempio: dict
    ):
        risposta = await client.post(
            "/api/v1/prodotti",
            json=prodotto_esempio,
            headers=headers_admin,
        )

        assert risposta.status_code == 201
        dati = risposta.json()
        assert dati["nome"] == prodotto_esempio["nome"]
        assert dati["sku"] == prodotto_esempio["sku"]
        assert "id" in dati
        assert "creato_il" in dati

    @pytest.mark.anyio
    async def test_crea_prodotto_sku_duplicato(
        self, client: AsyncClient, headers_admin: dict, prodotto_esempio: dict
    ):
        # Crea il primo prodotto
        await client.post(
            "/api/v1/prodotti",
            json=prodotto_esempio,
            headers=headers_admin,
        )

        # Tenta di creare un duplicato
        risposta = await client.post(
            "/api/v1/prodotti",
            json=prodotto_esempio,
            headers=headers_admin,
        )

        assert risposta.status_code == 409
        assert "esiste gia" in risposta.json()["detail"].lower()

    @pytest.mark.anyio
    async def test_crea_prodotto_dati_invalidi(
        self, client: AsyncClient, headers_admin: dict
    ):
        dati_invalidi = {
            "nome": "X",  # Troppo corto (min 2 caratteri)
            "prezzo": "-10",  # Negativo
            "categoria": "elettronica",
            "sku": "formato-errato",  # Non valido
        }

        risposta = await client.post(
            "/api/v1/prodotti",
            json=dati_invalidi,
            headers=headers_admin,
        )

        assert risposta.status_code == 422

    @pytest.mark.anyio
    async def test_crea_prodotto_non_autenticato(
        self, client: AsyncClient, prodotto_esempio: dict
    ):
        risposta = await client.post(
            "/api/v1/prodotti",
            json=prodotto_esempio,
        )

        assert risposta.status_code == 401


class TestListaProdotti:
    """Test per l'endpoint GET /api/v1/prodotti."""

    @pytest.mark.anyio
    async def test_lista_vuota(self, client: AsyncClient):
        risposta = await client.get("/api/v1/prodotti")

        assert risposta.status_code == 200
        dati = risposta.json()
        assert dati["data"] == []
        assert dati["meta"]["totale"] == 0

    @pytest.mark.anyio
    async def test_paginazione(
        self, client: AsyncClient, headers_admin: dict
    ):
        # Crea 25 prodotti
        for i in range(25):
            await client.post(
                "/api/v1/prodotti",
                json={
                    "nome": f"Prodotto {i}",
                    "prezzo": "10.00",
                    "categoria": "test",
                    "sku": f"TS-{10000 + i}",
                },
                headers=headers_admin,
            )

        # Richiedi la prima pagina
        risposta = await client.get(
            "/api/v1/prodotti", params={"page": 1, "size": 10}
        )

        dati = risposta.json()
        assert len(dati["data"]) == 10
        assert dati["meta"]["totale"] == 25
        assert dati["meta"]["pagine_totali"] == 3
        assert dati["links"]["next"] is not None
        assert dati["links"]["prev"] is None

    @pytest.mark.anyio
    async def test_filtro_categoria(
        self, client: AsyncClient, headers_admin: dict
    ):
        # Crea prodotti in categorie diverse
        for cat in ["elettronica", "elettronica", "abbigliamento"]:
            await client.post(
                "/api/v1/prodotti",
                json={
                    "nome": f"Prodotto {cat}",
                    "prezzo": "10.00",
                    "categoria": cat,
                    "sku": f"TS-{hash(cat) % 99999:05d}",
                },
                headers=headers_admin,
            )

        risposta = await client.get(
            "/api/v1/prodotti",
            params={"categoria": "elettronica"},
        )

        dati = risposta.json()
        assert dati["meta"]["totale"] == 2
        assert all(
            p["categoria"] == "elettronica" for p in dati["data"]
        )


class TestDettaglioProdotto:
    """Test per l'endpoint GET /api/v1/prodotti/{id}."""

    @pytest.mark.anyio
    async def test_prodotto_esistente(
        self, client: AsyncClient, headers_admin: dict, prodotto_esempio: dict
    ):
        # Crea il prodotto
        creazione = await client.post(
            "/api/v1/prodotti",
            json=prodotto_esempio,
            headers=headers_admin,
        )
        prodotto_id = creazione.json()["id"]

        # Recupera il dettaglio
        risposta = await client.get(f"/api/v1/prodotti/{prodotto_id}")

        assert risposta.status_code == 200
        assert risposta.json()["id"] == prodotto_id

    @pytest.mark.anyio
    async def test_prodotto_non_esistente(self, client: AsyncClient):
        risposta = await client.get("/api/v1/prodotti/99999")

        assert risposta.status_code == 404


class TestEliminazioneProdotto:
    """Test per l'endpoint DELETE /api/v1/prodotti/{id}."""

    @pytest.mark.anyio
    async def test_elimina_prodotto(
        self, client: AsyncClient, headers_admin: dict, prodotto_esempio: dict
    ):
        creazione = await client.post(
            "/api/v1/prodotti",
            json=prodotto_esempio,
            headers=headers_admin,
        )
        prodotto_id = creazione.json()["id"]

        risposta = await client.delete(
            f"/api/v1/prodotti/{prodotto_id}",
            headers=headers_admin,
        )

        assert risposta.status_code == 204

        # Verifica che non esista piu
        verifica = await client.get(f"/api/v1/prodotti/{prodotto_id}")
        assert verifica.status_code == 404
```

### Postman e HTTPie

Oltre ai test automatici, strumenti come Postman e HTTPie sono preziosi per l'esplorazione e il testing manuale.

**HTTPie dalla riga di comando:**

```bash
# GET con parametri
http GET https://api.esempio.it/api/v1/prodotti \
    categoria==elettronica \
    page==1 \
    size==10 \
    Authorization:"Bearer token-jwt"

# POST con corpo JSON
http POST https://api.esempio.it/api/v1/prodotti \
    nome="Nuovo Prodotto" \
    prezzo:=29.99 \
    categoria="test" \
    sku="TS-00001" \
    Authorization:"Bearer token-jwt"

# PATCH
http PATCH https://api.esempio.it/api/v1/prodotti/42 \
    prezzo:=19.99 \
    Authorization:"Bearer token-jwt"

# DELETE
http DELETE https://api.esempio.it/api/v1/prodotti/42 \
    Authorization:"Bearer token-jwt"
```

**Postman — organizzazione delle collection:**

Le collection di Postman possono essere strutturate per rispecchiare la gerarchia dell'API. Si consiglia di creare cartelle per ogni risorsa, con richieste per ogni operazione CRUD. Le variabili d'ambiente (`{{base_url}}`, `{{token}}`) permettono di passare facilmente tra ambienti di sviluppo, staging e produzione.

Per i test automatizzati in Postman, si usano gli script nella scheda "Tests":

```javascript
// Test nella scheda "Tests" di Postman
pm.test("Status code e 200", function () {
    pm.response.to.have.status(200);
});

pm.test("La risposta contiene dati paginati", function () {
    const json = pm.response.json();
    pm.expect(json).to.have.property("data");
    pm.expect(json).to.have.property("meta");
    pm.expect(json.meta).to.have.property("totale");
});

// Salva un valore per le richieste successive
if (pm.response.code === 201) {
    const json = pm.response.json();
    pm.environment.set("prodotto_id", json.id);
}
```

---

## Documentazione API

Una buona documentazione e tanto importante quanto una buona implementazione. Un'API senza documentazione e essenzialmente inutilizzabile per sviluppatori esterni, e anche per il team interno dopo qualche mese senza toccare quel codice. La documentazione dell'API deve essere accurata, aggiornata e facilmente navigabile.

Il vantaggio principale di FastAPI in questo ambito e che la documentazione nasce dal codice stesso: i type hints diventano schemi, le docstring diventano descrizioni, i parametri con valori di default diventano esempi. Questo approccio "documentation as code" elimina il problema della documentazione disallineata dal comportamento reale dell'API.

### Generazione automatica con FastAPI

FastAPI genera automaticamente la specifica OpenAPI dal codice Python. Ogni type hint, ogni Field, ogni docstring contribuisce alla documentazione finale.

```python
from fastapi import FastAPI

app = FastAPI(
    title="API Catalogo Prodotti",
    description="""
    ## API per la gestione del catalogo prodotti

    Questa API permette di:
    * **Creare** nuovi prodotti nel catalogo
    * **Leggere** prodotti singoli o liste filtrate
    * **Aggiornare** prodotti esistenti (totalmente o parzialmente)
    * **Eliminare** prodotti dal catalogo

    ### Autenticazione
    L'API usa JWT Bearer token. Ottieni un token tramite `/api/v1/auth/login`.

    ### Rate Limiting
    - Lettura: 100 richieste/minuto
    - Scrittura: 10 richieste/minuto
    """,
    version="1.0.0",
    contact={
        "name": "Team API",
        "email": "api@esempio.it",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/docs",           # Swagger UI
    redoc_url="/redoc",         # ReDoc
    openapi_url="/openapi.json",
)
```

**Personalizzazione degli endpoint per la documentazione:**

```python
@router.post(
    "/",
    response_model=ProdottoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crea un nuovo prodotto",
    description="Inserisce un nuovo prodotto nel catalogo. "
                "Richiede autenticazione con ruolo admin.",
    responses={
        201: {
            "description": "Prodotto creato con successo",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "nome": "Laptop ProBook",
                        "prezzo": "999.99",
                        "categoria": "elettronica",
                        "sku": "EL-12345",
                        "disponibile": True,
                        "creato_il": "2025-01-15T10:30:00Z",
                        "aggiornato_il": "2025-01-15T10:30:00Z",
                    }
                }
            },
        },
        409: {"description": "Prodotto con lo stesso SKU gia esistente"},
        422: {"description": "Dati di input non validi"},
    },
    tags=["prodotti"],
)
async def crea_prodotto(dati: ProdottoCreate):
    ...
```

### Swagger UI e ReDoc

FastAPI espone due interfacce di documentazione interattive:

- **Swagger UI** (`/docs`): interfaccia interattiva che permette di provare gli endpoint direttamente dal browser, con supporto per l'autenticazione e la visualizzazione degli schemi.

- **ReDoc** (`/redoc`): documentazione in formato piu tradizionale, ideale per la consultazione e la stampa, con navigazione laterale e ricerca.

### Personalizzazione avanzata di Swagger UI

FastAPI consente di personalizzare l'aspetto e il comportamento di Swagger UI attraverso parametri specifici e configurazioni OpenAPI.

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


app = FastAPI(
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={
        "deepLinking": True,
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "filter": True,
        "syntaxHighlight.theme": "monokai",
        "tryItOutEnabled": True,
    },
)


def schema_openapi_personalizzato():
    """Genera uno schema OpenAPI personalizzato con server e security globali."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Aggiungi server per ambienti multipli
    openapi_schema["servers"] = [
        {"url": "https://api.esempio.it", "description": "Produzione"},
        {"url": "https://staging.api.esempio.it", "description": "Staging"},
        {"url": "http://localhost:8000", "description": "Sviluppo locale"},
    ]

    # Security scheme globale
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Token JWT ottenuto da /api/v1/auth/login",
        },
        "APIKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
        },
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = schema_openapi_personalizzato
```

### OpenAPI 3.1 — Allineamento a JSON Schema 2020-12 e Nuove Funzionalita

FastAPI genera nativamente schemi conformi a OpenAPI 3.1, che introduce cambiamenti significativi rispetto alla versione 3.0.

**JSON Schema 2020-12 completo** — OpenAPI 3.1 adotta integralmente JSON Schema 2020-12 senza sottoinsieme personalizzato. Questo significa supporto nativo per `type: ["string", "null"]` (al posto di `nullable: true`), `prefixItems` per tuple tipizzate, `$dynamicRef` per ricorsione generica, e `contentMediaType` / `contentEncoding` per campi binari.

```python
from pydantic import BaseModel

class Prodotto(BaseModel):
    nome: str
    descrizione: str | None = None  # genera type: ["string", "null"]
    tags: list[str] = []

# Lo schema OpenAPI 3.1 generato automaticamente da FastAPI:
# "descrizione": {
#     "anyOf": [{"type": "string"}, {"type": "null"}],
#     "default": null
# }
```

**Webhooks** — OpenAPI 3.1 introduce l'oggetto `webhooks` a livello root per documentare callback che l'API invia ai client. FastAPI (dalla versione 0.99.0) supporta questo meccanismo con `app.webhooks`, un APIRouter dedicato:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class EventoOrdine(BaseModel):
    evento: str
    ordine_id: int
    stato: str
    timestamp: str


@app.webhooks.post("ordine-aggiornato")
async def webhook_ordine_aggiornato(body: EventoOrdine):
    """
    Quando lo stato di un ordine cambia, il sistema invia
    un POST a questo webhook con i dettagli dell'evento.

    L'URL di destinazione viene configurato dal client
    tramite l'endpoint /webhooks/registra.
    """
    ...


@app.webhooks.post("pagamento-confermato")
async def webhook_pagamento(body: dict):
    """Notifica di conferma pagamento avvenuto."""
    ...
```

I webhook dichiarati appaiono nella documentazione OpenAPI sotto la sezione dedicata, con schema del body e descrizione. Non generano endpoint sull'applicazione — servono esclusivamente a documentare i callback in uscita verso i client registrati.

**pathItems in Components** — OpenAPI 3.1 permette di definire `pathItems` riutilizzabili dentro `components`, consentendo di condividere intere definizioni di path (operazioni, parametri, risposte) tra piu endpoint. Questo e utile quando la stessa logica CRUD si applica a risorse diverse con schema identico.

### Best Practices per la documentazione

- Descrivi ogni endpoint con un `summary` breve e una `description` dettagliata
- Fornisci `examples` nei Pydantic Field per ogni campo
- Documenta tutti i possibili codici di risposta con `responses`
- Usa i `tags` per raggruppare logicamente gli endpoint
- Mantieni aggiornate le descrizioni dei parametri di query
- Includi esempi di richieste e risposte per scenari comuni e per casi di errore

---

## Versioning e Evoluzione

Le API evolvono nel tempo, e gestire questa evoluzione senza rompere i client esistenti e una delle sfide piu importanti.

### Strategie di Versioning a confronto

Esistono tre strategie principali, ciascuna con trade-off specifici.

**1. URL Path versioning** — il piu diffuso, esplicito e facilmente testabile.

```python
# app/main.py — router separati per versione
from fastapi import FastAPI

app = FastAPI()

# Monta i router versionati
app.include_router(router_v1, prefix="/api/v1")
app.include_router(router_v2, prefix="/api/v2")
```

**2. Header versioning** — piu pulito dal punto di vista REST, ma meno visibile.

```python
from fastapi import Header, HTTPException


async def versione_da_header(
    accept_version: str = Header("v1", alias="Accept-Version"),
) -> str:
    """Estrae la versione dall'header Accept-Version."""
    versioni_supportate = {"v1", "v2"}
    if accept_version not in versioni_supportate:
        raise HTTPException(
            status_code=400,
            detail=f"Versione '{accept_version}' non supportata. "
                   f"Versioni disponibili: {versioni_supportate}",
        )
    return accept_version


@router.get("/prodotti")
async def lista_prodotti(
    versione: str = Depends(versione_da_header),
):
    if versione == "v2":
        return await lista_prodotti_v2()
    return await lista_prodotti_v1()
```

**3. Content negotiation** — usa il media type nell'header Accept (RFC 6838).

```python
from fastapi import Header


@router.get("/prodotti")
async def lista_prodotti(
    accept: str = Header("application/json"),
):
    """
    Content negotiation via Accept header:
    - application/vnd.api.v1+json → formato v1
    - application/vnd.api.v2+json → formato v2
    """
    if "vnd.api.v2" in accept:
        return await lista_prodotti_v2()
    return await lista_prodotti_v1()
```

| Strategia | Pro | Contro |
|-----------|-----|--------|
| URL path | Esplicito, cache-friendly, facile da testare | URL "inquinati" dalla versione |
| Header | URL puliti, piu RESTful | Non visibile nel browser, cache complessa |
| Content negotiation | Massima conformita REST | Complesso da implementare e debuggare |

### Approfondimento: Versioning con Router Composition in FastAPI

Nella pratica, la sfida del versioning non e scegliere la strategia (URL path vince nella maggioranza dei casi) ma gestire il codice condiviso tra versioni. Un approccio efficace e la composizione dei router: la logica comune viene estratta in un service layer, e ogni versione espone un router sottile che mappa i dati nel formato specifico della versione.

```python
# app/services/prodotto_service.py — logica condivisa tra versioni
from app.models import Prodotto
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class ProdottoService:
    """Service layer indipendente dalla versione dell'API."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, prodotto_id: int) -> Prodotto | None:
        result = await self.db.execute(
            select(Prodotto).where(Prodotto.id == prodotto_id)
        )
        return result.scalar_one_or_none()

    async def lista(self, **filtri) -> list[Prodotto]:
        query = select(Prodotto)
        if filtri.get("categoria"):
            query = query.where(Prodotto.categoria == filtri["categoria"])
        result = await self.db.execute(query)
        return list(result.scalars().all())
```

```python
# app/routers/v1/prodotti.py — formato risposta v1
from app.services.prodotto_service import ProdottoService

router_v1 = APIRouter(prefix="/api/v1/prodotti", tags=["prodotti-v1"])


@router_v1.get("/{prodotto_id}")
async def dettaglio_v1(prodotto_id: int, db: AsyncSession = Depends(get_db)):
    service = ProdottoService(db)
    prodotto = await service.get_by_id(prodotto_id)
    if not prodotto:
        raise HTTPException(status_code=404)
    # V1: formato flat, prezzo come stringa
    return {
        "id": prodotto.id,
        "nome": prodotto.nome,
        "prezzo": str(prodotto.prezzo),
        "categoria": prodotto.categoria,
    }


# app/routers/v2/prodotti.py — formato risposta v2 con metadati
router_v2 = APIRouter(prefix="/api/v2/prodotti", tags=["prodotti-v2"])


@router_v2.get("/{prodotto_id}")
async def dettaglio_v2(prodotto_id: int, db: AsyncSession = Depends(get_db)):
    service = ProdottoService(db)
    prodotto = await service.get_by_id(prodotto_id)
    if not prodotto:
        raise HTTPException(status_code=404)
    # V2: formato arricchito con metadati e link HATEOAS
    return {
        "data": {
            "id": prodotto.id,
            "nome": prodotto.nome,
            "prezzo": {"valore": float(prodotto.prezzo), "valuta": "EUR"},
            "categoria": prodotto.categoria,
        },
        "meta": {"versione": "v2", "deprecato": False},
        "_links": {"self": f"/api/v2/prodotti/{prodotto.id}"},
    }
```

Quando si supportano piu versioni simultanee, la best practice e mantenere al massimo due versioni attive (corrente e precedente). Le major tech company come Stripe e GitHub seguono questa regola, concedendo ai consumatori un periodo di migrazione di 6-12 mesi prima di ritirare la versione precedente. Il costo di mantenere piu di due versioni cresce esponenzialmente: ogni bugfix deve essere replicato, ogni test deve coprire tutte le varianti, e la documentazione diventa un labirinto.

Il versioning tramite header, sebbene meno comune, diventa vantaggioso quando le differenze tra versioni sono minime e si vuole evitare la duplicazione dei router. In questo caso, un middleware di negoziazione della versione puo iniettare la versione nel contesto della richiesta, e i singoli endpoint la usano per decidere il formato di risposta.

### Breaking vs Non-Breaking Changes

La distinzione tra cambiamenti retrocompatibili e non e il cuore della gestione dell'evoluzione di un'API. Un cambiamento breaking costringe tutti i client ad aggiornarsi simultaneamente — uno scenario che in sistemi distribuiti e spesso impossibile da coordinare. Per questo motivo, i cambiamenti breaking dovrebbero essere l'ultima risorsa, e quando necessari, gestiti con una strategia di versioning chiara e un periodo di transizione adeguato.

**Cambiamenti non-breaking (retrocompatibili):**
- Aggiungere nuovi endpoint
- Aggiungere campi opzionali alle risposte
- Aggiungere parametri opzionali alle richieste
- Aggiungere nuovi valori a un enum (con cautela)
- Rilassare una validazione (accettare piu input)

**Cambiamenti breaking (richiedono nuova versione):**
- Rimuovere un endpoint
- Rimuovere o rinominare un campo nella risposta
- Rendere obbligatorio un parametro precedentemente opzionale
- Cambiare il tipo di un campo
- Modificare la semantica di un campo esistente
- Restringere una validazione

### Strategia di Deprecation

```python
import warnings
from fastapi import Header
from datetime import date


def avviso_deprecazione(
    versione_rimossa: str,
    alternativa: str,
):
    """Middleware per segnalare endpoint deprecati."""
    def dependency(
        x_api_version: str | None = Header(None),
    ):
        # Aggiunge header di deprecazione nella risposta
        return {
            "Deprecation": "true",
            "Sunset": "2026-06-01",
            "Link": f'<{alternativa}>; rel="successor-version"',
        }
    return dependency


# Endpoint deprecato
@router_v1.get(
    "/prodotti",
    deprecated=True,  # Segnato come deprecato in Swagger
    summary="[DEPRECATO] Lista prodotti — Usa /api/v2/prodotti",
)
async def lista_prodotti_v1():
    """
    **DEPRECATO**: Questo endpoint sara rimosso il 2026-06-01.

    Usare `/api/v2/prodotti` che supporta filtri avanzati e
    paginazione cursor-based.
    """
    ...


# Nuovo endpoint nella v2
@router_v2.get("/prodotti", summary="Lista prodotti con filtri avanzati")
async def lista_prodotti_v2():
    ...
```

### Piano di migrazione

La gestione della migrazione tra versioni dell'API e tanto un problema tecnico quanto organizzativo. Un piano ben strutturato minimizza l'impatto sui client e riduce il rischio di interruzioni del servizio.

Un piano di migrazione ben strutturato prevede:

1. **Annuncio**: comunicare la deprecazione con almeno 6 mesi di anticipo
2. **Periodo di overlap**: mantenere entrambe le versioni attive
3. **Monitoraggio**: tracciare l'utilizzo della versione deprecata
4. **Comunicazione diretta**: contattare i consumatori che ancora usano la versione vecchia
5. **Sunset**: disattivare la versione deprecata, restituendo 410 Gone con indicazioni sulla migrazione

---

## Risposta agli errori — RFC 7807 Problem Details

RFC 7807 (successivamente aggiornato da RFC 9457, luglio 2023) definisce un formato standard per comunicare dettagli degli errori nelle risposte HTTP. Invece di inventare un formato proprietario per ogni API, RFC 7807 stabilisce membri obbligatori e opzionali che rendono gli errori machine-readable e consistenti tra servizi diversi.

### Struttura Problem Details

I membri definiti dalla specifica sono:

| Membro | Tipo | Obbligatorio | Descrizione |
|--------|------|--------------|-------------|
| `type` | URI | No (default `about:blank`) | URI che identifica il tipo di errore |
| `title` | string | No | Breve descrizione leggibile del tipo di errore |
| `status` | integer | No | Codice HTTP (ripetuto per comodita del client) |
| `detail` | string | No | Spiegazione specifica di questa occorrenza |
| `instance` | URI | No | URI che identifica questa specifica occorrenza |

La specifica consente di aggiungere membri estesi (extension members) per dettagli aggiuntivi specifici dell'applicazione.

### Implementazione completa in FastAPI

```python
# app/errors/problem_details.py
from pydantic import BaseModel, Field
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


class ProblemDetail(BaseModel):
    """Risposta errore conforme a RFC 7807 / RFC 9457."""
    type: str = Field(
        default="about:blank",
        description="URI che identifica il tipo di problema",
    )
    title: str = Field(
        ...,
        description="Breve descrizione leggibile del tipo di problema",
    )
    status: int = Field(
        ...,
        description="Codice di stato HTTP",
    )
    detail: str | None = Field(
        None,
        description="Spiegazione specifica dell'occorrenza",
    )
    instance: str | None = Field(
        None,
        description="URI dell'istanza specifica del problema",
    )


class ValidationProblemDetail(ProblemDetail):
    """Problem Details esteso per errori di validazione."""
    errors: list[dict] = Field(
        default_factory=list,
        description="Lista degli errori di validazione per campo",
    )


# --- Handler personalizzati ---

async def handler_http_exception(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Converte le HTTPException di FastAPI in formato RFC 7807."""
    problem = ProblemDetail(
        type=f"https://api.esempio.it/errori/{exc.status_code}",
        title=_titoli_http.get(exc.status_code, "Errore sconosciuto"),
        status=exc.status_code,
        detail=str(exc.detail) if exc.detail else None,
        instance=str(request.url.path),
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )


async def handler_validazione(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Converte gli errori di validazione Pydantic in formato RFC 7807."""
    errori_formattati = []
    for errore in exc.errors():
        campo = ".".join(str(loc) for loc in errore["loc"] if loc != "body")
        errori_formattati.append({
            "field": campo,
            "message": errore["msg"],
            "type": errore["type"],
        })

    problem = ValidationProblemDetail(
        type="https://api.esempio.it/errori/validazione",
        title="Errore di validazione",
        status=422,
        detail=f"La richiesta contiene {len(errori_formattati)} "
               f"error{'e' if len(errori_formattati) == 1 else 'i'} "
               f"di validazione.",
        instance=str(request.url.path),
        errors=errori_formattati,
    )
    return JSONResponse(
        status_code=422,
        content=problem.model_dump(exclude_none=True),
        media_type="application/problem+json",
    )


# Mappa codici HTTP → titoli leggibili
_titoli_http = {
    400: "Richiesta non valida",
    401: "Autenticazione richiesta",
    403: "Accesso negato",
    404: "Risorsa non trovata",
    409: "Conflitto",
    422: "Entita non processabile",
    429: "Troppe richieste",
    500: "Errore interno del server",
    503: "Servizio non disponibile",
}


# --- Registrazione degli handler ---

def registra_error_handlers(app):
    """Registra tutti gli handler RFC 7807 sull'applicazione FastAPI."""
    app.add_exception_handler(StarletteHTTPException, handler_http_exception)
    app.add_exception_handler(RequestValidationError, handler_validazione)
```

### Esempio di risposta

Un client che invia dati non validi riceve:

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/problem+json

{
  "type": "https://api.esempio.it/errori/validazione",
  "title": "Errore di validazione",
  "status": 422,
  "detail": "La richiesta contiene 2 errori di validazione.",
  "instance": "/api/v1/prodotti",
  "errors": [
    {
      "field": "prezzo",
      "message": "Input should be greater than 0",
      "type": "greater_than"
    },
    {
      "field": "sku",
      "message": "String should match pattern '^[A-Z]{2,4}-\\d{4,8}$'",
      "type": "string_pattern_mismatch"
    }
  ]
}
```

---

## Autenticazione avanzata — JWT Refresh, OAuth2 Scopes

L'autenticazione base con access token e descritta nella sezione FastAPI. Qui approfondiamo il flusso completo con refresh token e gli scopes OAuth2 per autorizzazione granulare.

### Flusso Access + Refresh Token

L'access token ha vita breve (15-30 minuti) per limitare la finestra di esposizione in caso di compromissione. Il refresh token ha vita lunga (giorni/settimane) e serve esclusivamente a ottenere nuovi access token senza richiedere le credenziali.

```python
# app/auth/tokens.py
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from jose import jwt
from pydantic import BaseModel


REFRESH_TOKEN_SCADENZA_GIORNI = 7


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # secondi


def crea_coppia_token(user_id: int, ruolo: str) -> TokenPair:
    """Genera una coppia access + refresh token."""
    access = crea_access_token(
        {"sub": str(user_id), "ruolo": ruolo, "type": "access"},
        scadenza=timedelta(minutes=ACCESS_TOKEN_SCADENZA_MINUTI),
    )
    refresh = crea_access_token(
        {
            "sub": str(user_id),
            "type": "refresh",
            "jti": str(uuid4()),  # ID univoco per revoca
        },
        scadenza=timedelta(days=REFRESH_TOKEN_SCADENZA_GIORNI),
    )
    return TokenPair(
        access_token=access,
        refresh_token=refresh,
        expires_in=ACCESS_TOKEN_SCADENZA_MINUTI * 60,
    )
```

```python
# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

router_auth = APIRouter(prefix="/api/v1/auth", tags=["autenticazione"])


@router_auth.post("/login", response_model=TokenPair)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Autenticazione con credenziali, restituisce access + refresh token."""
    utente = await autentica_utente(db, form.username, form.password)
    if not utente:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenziali non valide",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return crea_coppia_token(utente.id, utente.ruolo)


@router_auth.post("/refresh", response_model=TokenPair)
async def refresh_token(
    refresh: str,
    db: AsyncSession = Depends(get_db),
):
    """Rinnova l'access token usando il refresh token."""
    try:
        payload = jwt.decode(refresh, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token non valido")

        # Verifica che il refresh token non sia stato revocato
        jti = payload.get("jti")
        if await e_token_revocato(db, jti):
            raise HTTPException(status_code=401, detail="Token revocato")

        user_id = int(payload["sub"])
        utente = await db.get(Utente, user_id)
        if not utente:
            raise HTTPException(status_code=401, detail="Utente non trovato")

        # Revoca il vecchio refresh token (rotation)
        await revoca_token(db, jti)

        return crea_coppia_token(utente.id, utente.ruolo)
    except JWTError:
        raise HTTPException(status_code=401, detail="Token scaduto o corrotto")
```

### OAuth2 Scopes

Gli scopes permettono di definire permessi granulari per ogni token, andando oltre il semplice RBAC basato su ruoli.

```python
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from fastapi import Security


oauth2_con_scopes = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    scopes={
        "prodotti:lettura": "Leggere prodotti",
        "prodotti:scrittura": "Creare e modificare prodotti",
        "prodotti:eliminazione": "Eliminare prodotti",
        "utenti:gestione": "Gestire utenti",
        "admin": "Accesso completo",
    },
)


async def verifica_scopes(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_con_scopes),
    db: AsyncSession = Depends(get_db),
) -> Utente:
    """Verifica che il token abbia gli scopes richiesti."""
    eccezione = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Scopes insufficienti",
        headers={
            "WWW-Authenticate": f'Bearer scope="{security_scopes.scope_str}"'
        },
    )

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    scopes_token = payload.get("scopes", [])

    for scope_richiesto in security_scopes.scopes:
        if scope_richiesto not in scopes_token and "admin" not in scopes_token:
            raise eccezione

    utente = await db.get(Utente, int(payload["sub"]))
    if not utente:
        raise eccezione

    return utente


# Uso negli endpoint
@router.delete(
    "/{prodotto_id}",
    status_code=204,
)
async def elimina_prodotto(
    prodotto_id: int,
    utente: Utente = Security(
        verifica_scopes,
        scopes=["prodotti:eliminazione"],
    ),
):
    """Richiede lo scope 'prodotti:eliminazione'."""
    ...
```

---

## Rate Limiting avanzato — Sliding Window e Token Bucket

Oltre all'uso di `slowapi` descritto nella sezione FastAPI, comprendere gli algoritmi sottostanti e fondamentale per scegliere la strategia adatta al proprio caso d'uso.

### Algoritmo Sliding Window

La finestra scorrevole evita il problema del "burst al confine" tipico del fixed window. Invece di resettare il contatore a ogni intervallo fisso, considera una finestra mobile che si sposta continuamente nel tempo.

```python
# app/middleware/sliding_window.py
import time
import redis.asyncio as redis

redis_client = redis.from_url("redis://localhost:6379")


async def controlla_rate_limit_sliding(
    chiave: str,
    limite: int,
    finestra_secondi: int,
) -> tuple[bool, dict]:
    """
    Rate limiting con sliding window log su Redis.
    Restituisce (consentito, headers).
    """
    adesso = time.time()
    inizio_finestra = adesso - finestra_secondi

    pipe = redis_client.pipeline()
    # Rimuovi le entry scadute
    pipe.zremrangebyscore(chiave, 0, inizio_finestra)
    # Aggiungi la richiesta corrente
    pipe.zadd(chiave, {str(adesso): adesso})
    # Conta le richieste nella finestra
    pipe.zcard(chiave)
    # Imposta TTL sulla chiave
    pipe.expire(chiave, finestra_secondi)

    risultati = await pipe.execute()
    conteggio = risultati[2]

    consentito = conteggio <= limite
    reset_at = int(adesso + finestra_secondi)

    headers = {
        "X-RateLimit-Limit": str(limite),
        "X-RateLimit-Remaining": str(max(0, limite - conteggio)),
        "X-RateLimit-Reset": str(reset_at),
    }

    if not consentito:
        headers["Retry-After"] = str(finestra_secondi)

    return consentito, headers
```

### Algoritmo Token Bucket

Il token bucket e ideale quando si vuole consentire brevi burst ma limitare la media nel tempo. Il bucket si riempie a una velocita costante; ogni richiesta consuma un token.

```python
# app/middleware/token_bucket.py
import time
import redis.asyncio as redis

redis_client = redis.from_url("redis://localhost:6379")


async def controlla_token_bucket(
    chiave: str,
    capacita: int,
    velocita_riempimento: float,  # token al secondo
) -> tuple[bool, dict]:
    """
    Rate limiting con token bucket su Redis.
    capacita: numero massimo di token nel bucket.
    velocita_riempimento: token aggiunti al secondo.
    """
    adesso = time.time()
    chiave_bucket = f"bucket:{chiave}"

    # Script Lua per atomicita
    script_lua = """
    local chiave = KEYS[1]
    local capacita = tonumber(ARGV[1])
    local velocita = tonumber(ARGV[2])
    local adesso = tonumber(ARGV[3])

    local dati = redis.call('HMGET', chiave, 'tokens', 'ultimo_aggiornamento')
    local tokens = tonumber(dati[1]) or capacita
    local ultimo = tonumber(dati[2]) or adesso

    local delta = adesso - ultimo
    tokens = math.min(capacita, tokens + delta * velocita)

    local consentito = 0
    if tokens >= 1 then
        tokens = tokens - 1
        consentito = 1
    end

    redis.call('HMSET', chiave, 'tokens', tokens, 'ultimo_aggiornamento', adesso)
    redis.call('EXPIRE', chiave, math.ceil(capacita / velocita) * 2)

    return {consentito, math.floor(tokens)}
    """

    risultato = await redis_client.eval(
        script_lua, 1, chiave_bucket, capacita, velocita_riempimento, adesso
    )

    consentito = bool(risultato[0])
    tokens_rimanenti = int(risultato[1])

    headers = {
        "X-RateLimit-Limit": str(capacita),
        "X-RateLimit-Remaining": str(tokens_rimanenti),
    }

    return consentito, headers
```

### Middleware FastAPI per Rate Limiting

```python
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware che applica rate limiting globale con headers standard."""

    async def dispatch(self, request: Request, call_next):
        chiave = f"rl:{request.client.host}"
        consentito, headers = await controlla_rate_limit_sliding(
            chiave, limite=100, finestra_secondi=60
        )

        if not consentito:
            return JSONResponse(
                status_code=429,
                content={
                    "type": "https://api.esempio.it/errori/rate-limit",
                    "title": "Troppe richieste",
                    "status": 429,
                    "detail": "Rate limit superato. Riprova piu tardi.",
                },
                headers=headers,
                media_type="application/problem+json",
            )

        response = await call_next(request)
        for k, v in headers.items():
            response.headers[k] = v
        return response
```

### slowapi — Rate Limiting Dichiarativo con Backend Redis

L'implementazione manuale sopra e utile per capire la meccanica, ma in produzione conviene usare `slowapi`, che wrappa `limits` con integrazione nativa per FastAPI/Starlette. Il vantaggio principale: supporto per backend distribuiti (Redis, Memcached) e limiti dichiarativi per-route.

```python
from fastapi import FastAPI, Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Backend Redis per rate limiting distribuito su piu istanze
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379/1",
    default_limits=["200/hour", "50/minute"],
)

app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


# Limite globale ereditato: 200/hour, 50/minute
@app.get("/prodotti")
async def lista_prodotti():
    return {"prodotti": []}


# Override per-route: endpoint piu sensibile
@app.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request):
    return {"token": "..."}


# Limiti dinamici basati su tier utente
def limite_per_tier(request: Request) -> str:
    api_key = request.headers.get("X-API-Key", "")
    tier = identifica_tier(api_key)  # "free", "pro", "enterprise"
    limiti = {
        "free": "100/hour",
        "pro": "1000/hour",
        "enterprise": "10000/hour",
    }
    return limiti.get(tier, "100/hour")


@app.get("/ricerca")
@limiter.limit(limite_per_tier)
async def ricerca(request: Request, q: str):
    return {"risultati": []}
```

**Storage Redis per ambienti distribuiti** — Quando l'applicazione gira su piu worker o piu nodi dietro un load balancer, il rate limiting in memoria locale non funziona: ogni worker ha il proprio contatore. Configurando `storage_uri="redis://..."`, tutti i worker condividono lo stesso stato dei contatori tramite Redis. Le chiavi hanno TTL automatico allineato alla finestra temporale del limite, quindi non richiedono pulizia manuale. Per alta disponibilita, slowapi supporta anche Redis Sentinel e Redis Cluster tramite la libreria `limits`.

**Identificazione del client** — `get_remote_address` e la key function di default, ma dietro un reverse proxy (Nginx, Traefik, ALB) l'IP diretto sara quello del proxy. In questi casi, usare una key function personalizzata che legge `X-Forwarded-For` o, meglio, identifica il client tramite API key o token JWT per limiti piu precisi e resistenti a IP spoofing.

---

## Paginazione avanzata — Cursor, Link Headers, Pydantic Models

### Modelli Pydantic tipizzati per risposte paginate

Usare Generic per creare modelli di risposta paginata riutilizzabili e type-safe.

```python
from typing import TypeVar, Generic
from pydantic import BaseModel, Field

T = TypeVar("T")


class CursorInfo(BaseModel):
    next_cursor: str | None = None
    prev_cursor: str | None = None
    has_more: bool


class CursorPaginatedResponse(BaseModel, Generic[T]):
    """Risposta paginata cursor-based con tipo generico."""
    data: list[T]
    cursor: CursorInfo
    count: int = Field(description="Numero di elementi restituiti in questa pagina")


class OffsetPaginatedResponse(BaseModel, Generic[T]):
    """Risposta paginata offset-based con tipo generico."""
    data: list[T]
    meta: PaginationMeta
    links: dict[str, str | None]
```

### Link Headers (RFC 8288)

Oltre a restituire i link nel corpo della risposta, lo standard RFC 8288 definisce l'header `Link` per la navigazione tra pagine. Questo approccio e usato da API come GitHub e GitLab.

```python
from fastapi import Response


def aggiungi_link_headers(
    response: Response,
    base_url: str,
    page: int,
    size: int,
    totale: int,
):
    """Aggiunge header Link conformi a RFC 8288 per la paginazione."""
    pagine_totali = (totale + size - 1) // size
    links = []

    links.append(f'<{base_url}?page=1&size={size}>; rel="first"')
    links.append(f'<{base_url}?page={pagine_totali}&size={size}>; rel="last"')

    if page < pagine_totali:
        links.append(f'<{base_url}?page={page + 1}&size={size}>; rel="next"')
    if page > 1:
        links.append(f'<{base_url}?page={page - 1}&size={size}>; rel="prev"')

    response.headers["Link"] = ", ".join(links)
    response.headers["X-Total-Count"] = str(totale)
    response.headers["X-Total-Pages"] = str(pagine_totali)


@router.get("/", response_model=OffsetPaginatedResponse[ProdottoResponse])
async def lista_prodotti(
    response: Response,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Lista prodotti con Link headers RFC 8288."""
    risultato = await pagina_risultati(
        select(Prodotto), db, page, size, "/api/v1/prodotti"
    )

    aggiungi_link_headers(
        response, "/api/v1/prodotti", page, size, risultato.meta.totale
    )

    return risultato
```

### Confronto offset vs cursor

| Caratteristica | Offset/Limit | Cursor-based |
|---------------|--------------|--------------|
| Salto a pagina specifica | Supportato | Non supportato |
| Prestazioni con offset grande | O(n) — peggiora | O(1) — costante |
| Dati consistenti durante la navigazione | No (phantom reads) | Si |
| Complessita di implementazione | Bassa | Media |
| Caso d'uso ideale | Dashboard, admin panel | Feed, timeline, scroll infinito |

---

## HATEOAS — Hypermedia nella pratica

HATEOAS e il vincolo REST piu avanzato e meno implementato. L'idea centrale e che il client non deve costruire gli URI autonomamente: ogni risposta contiene link che indicano le azioni possibili nello stato corrente della risorsa.

### Implementazione pratica

```python
from pydantic import BaseModel


class HATEOASLink(BaseModel):
    href: str
    rel: str
    method: str = "GET"
    title: str | None = None


class OrdineHATEOAS(BaseModel):
    id: int
    stato: str
    totale: str
    _links: list[HATEOASLink]


def genera_links_ordine(ordine_id: int, stato: str) -> list[HATEOASLink]:
    """Genera link HATEOAS dinamici in base allo stato dell'ordine."""
    links = [
        HATEOASLink(
            href=f"/api/v1/ordini/{ordine_id}",
            rel="self",
            method="GET",
            title="Dettaglio ordine",
        ),
    ]

    if stato == "bozza":
        links.extend([
            HATEOASLink(
                href=f"/api/v1/ordini/{ordine_id}",
                rel="update",
                method="PATCH",
                title="Modifica ordine",
            ),
            HATEOASLink(
                href=f"/api/v1/ordini/{ordine_id}/conferma",
                rel="confirm",
                method="POST",
                title="Conferma ordine",
            ),
            HATEOASLink(
                href=f"/api/v1/ordini/{ordine_id}",
                rel="delete",
                method="DELETE",
                title="Elimina ordine",
            ),
        ])
    elif stato == "confermato":
        links.extend([
            HATEOASLink(
                href=f"/api/v1/ordini/{ordine_id}/pagamento",
                rel="payment",
                method="POST",
                title="Procedi al pagamento",
            ),
            HATEOASLink(
                href=f"/api/v1/ordini/{ordine_id}/annulla",
                rel="cancel",
                method="POST",
                title="Annulla ordine",
            ),
        ])
    elif stato == "pagato":
        links.append(
            HATEOASLink(
                href=f"/api/v1/ordini/{ordine_id}/spedizione",
                rel="shipment",
                method="GET",
                title="Traccia spedizione",
            )
        )

    return links
```

Il client puo cosi navigare l'API senza conoscere a priori la struttura degli URI — segue i link offerti dallo stato corrente della risorsa.

### Richardson Maturity Model — I Quattro Livelli di Maturita REST

Leonard Richardson ha proposto un modello a quattro livelli per classificare quanto un'API sia effettivamente RESTful. Comprendere questi livelli aiuta a decidere consapevolmente dove posizionare la propria API.

**Livello 0 — Il Tunnel RPC (The Swamp of POX)**

Un singolo endpoint accetta tutte le richieste. Il metodo HTTP e sempre POST, il corpo della richiesta contiene sia l'operazione sia i dati. SOAP e XML-RPC operano tipicamente a questo livello.

```python
# Livello 0 — un solo endpoint, tutto via POST
@app.post("/api")
async def rpc_tunnel(azione: str, dati: dict):
    if azione == "crea_utente":
        return await crea_utente(dati)
    elif azione == "lista_ordini":
        return await lista_ordini(dati)
    # ...dispatch manuale per ogni operazione
```

**Livello 1 — Risorse Individuali**

Ogni risorsa ha il proprio URI (`/utenti`, `/ordini/{id}`), ma il verbo HTTP non viene sfruttato in modo semantico — spesso tutto passa ancora per POST.

**Livello 2 — Verbi HTTP + Codici di Stato**

Le risorse usano GET, POST, PUT, PATCH, DELETE con i corretti codici di risposta (201 Created, 204 No Content, 404 Not Found). La stragrande maggioranza delle API REST in produzione opera a questo livello, ed e il punto di equilibrio ideale tra pragmatismo e conformita allo standard.

```python
# Livello 2 — verbi HTTP semantici + codici corretti
@app.get("/ordini/{ordine_id}", response_model=OrdineResponse)
async def dettaglio_ordine(ordine_id: int):
    ordine = await repository.trova_per_id(ordine_id)
    if not ordine:
        raise HTTPException(status_code=404, detail="Ordine non trovato")
    return ordine

@app.post("/ordini", status_code=201, response_model=OrdineResponse)
async def crea_ordine(payload: CreaOrdineRequest):
    return await repository.crea(payload)

@app.delete("/ordini/{ordine_id}", status_code=204)
async def elimina_ordine(ordine_id: int):
    await repository.elimina(ordine_id)
```

**Livello 3 — Hypermedia Controls (HATEOAS)**

Le risposte includono link a transizioni di stato valide. Il client non ha bisogno di conoscere la struttura degli URI a priori: scopre le operazioni disponibili seguendo i link forniti dalla risposta stessa. Il codice HATEOAS mostrato nella sezione precedente implementa esattamente questo livello.

**Quale livello scegliere?**

Il Livello 2 e il punto ottimale per la maggior parte dei progetti. Offre un design chiaro, prevedibile e ben supportato da ogni framework e client HTTP. Il Livello 3 (HATEOAS) aggiunge valore reale quando l'API ha workflow complessi con transizioni di stato (e-commerce, processo di approvazione, FSM di dominio) o quando i client devono essere disaccoppiati dalla struttura degli URI per facilitare l'evoluzione futura senza breaking changes. Il costo di HATEOAS — generazione dei link, maggiore dimensione delle risposte, complessita del client che deve interpretare i link — va valutato rispetto ai benefici concreti nel proprio caso d'uso.

---

## Validazione avanzata — Pydantic v2

### Discriminated Unions

Le discriminated unions permettono di validare strutture polimorfiche in base a un campo discriminatore. Pydantic v2 le supporta nativamente.

```python
from pydantic import BaseModel, Field
from typing import Literal, Annotated
from annotated_types import Discriminator


class PagamentoCarta(BaseModel):
    tipo: Literal["carta"]
    numero_carta: str = Field(pattern=r"^\d{16}$")
    cvv: str = Field(pattern=r"^\d{3,4}$")
    scadenza: str = Field(pattern=r"^\d{2}/\d{2}$")


class PagamentoBonifico(BaseModel):
    tipo: Literal["bonifico"]
    iban: str = Field(min_length=15, max_length=34)
    intestatario: str


class PagamentoPayPal(BaseModel):
    tipo: Literal["paypal"]
    email: str = Field(pattern=r"^[\w.-]+@[\w.-]+\.\w+$")


TipoPagamento = Annotated[
    PagamentoCarta | PagamentoBonifico | PagamentoPayPal,
    Field(discriminator="tipo"),
]


class CreaOrdine(BaseModel):
    prodotti: list[int] = Field(min_length=1)
    pagamento: TipoPagamento
    note: str | None = None
```

Il client invia `"tipo": "carta"` o `"tipo": "bonifico"` e Pydantic applica automaticamente lo schema corretto, con un messaggio di errore chiaro se il tipo non e riconosciuto.

### Custom Validators con contesto

```python
from pydantic import BaseModel, field_validator, ValidationInfo


class PrenotazioneCreate(BaseModel):
    data_inizio: datetime
    data_fine: datetime
    codice_sconto: str | None = None

    @field_validator("data_fine")
    @classmethod
    def data_fine_dopo_inizio(cls, v: datetime, info: ValidationInfo) -> datetime:
        """Assicura che la data fine sia successiva alla data inizio."""
        if "data_inizio" in info.data and v <= info.data["data_inizio"]:
            raise ValueError(
                "La data di fine deve essere successiva alla data di inizio"
            )
        return v
```

---

## Response Serialization

FastAPI e Pydantic offrono un controllo granulare sulla serializzazione delle risposte.

### response_model con exclude e include

```python
class UtenteDB(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    nome: str
    hash_password: str
    ruolo: str
    attivo: bool
    creato_il: datetime


class UtentePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    creato_il: datetime


class UtenteProfilo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: str
    nome: str
    ruolo: str
    attivo: bool
    creato_il: datetime


# Endpoint con response_model diversi per lo stesso modello DB
@router.get("/utenti/{id}/pubblico", response_model=UtentePublic)
async def profilo_pubblico(id: int):
    """Restituisce solo i campi pubblici (niente email, niente password)."""
    ...


@router.get("/utenti/me", response_model=UtenteProfilo)
async def profilo_privato(utente: Utente = Depends(get_utente_corrente)):
    """Restituisce il profilo completo (senza hash_password)."""
    ...
```

### Alias e Computed Fields

```python
from pydantic import BaseModel, Field, computed_field
from decimal import Decimal


class ProdottoAPI(BaseModel):
    """Schema con alias per compatibilita con naming conventions esterne."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    nome_prodotto: str = Field(alias="nome")
    prezzo_unitario: Decimal = Field(alias="prezzo")
    in_magazzino: bool = Field(alias="disponibile")

    @computed_field
    @property
    def prezzo_con_iva(self) -> Decimal:
        """Campo calcolato: prezzo con IVA al 22%."""
        return round(self.prezzo_unitario * Decimal("1.22"), 2)

    @computed_field
    @property
    def slug(self) -> str:
        """Slug generato dal nome per URL SEO-friendly."""
        return self.nome_prodotto.lower().replace(" ", "-")
```

---

## File Upload e Download

### Upload multipart con validazione

```python
from fastapi import UploadFile, File, HTTPException
import aiofiles
from pathlib import Path
from uuid import uuid4

UPLOAD_DIR = Path("uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
TIPI_CONSENTITI = {"image/jpeg", "image/png", "image/webp", "application/pdf"}


@router.post("/prodotti/{prodotto_id}/allegati")
async def carica_allegato(
    prodotto_id: int,
    file: UploadFile = File(..., description="File da caricare (max 10MB)"),
):
    """Carica un allegato per un prodotto con validazione tipo e dimensione."""
    # Validazione content type
    if file.content_type not in TIPI_CONSENTITI:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo file '{file.content_type}' non consentito. "
                   f"Tipi accettati: {TIPI_CONSENTITI}",
        )

    # Validazione dimensione (lettura incrementale)
    contenuto = await file.read()
    if len(contenuto) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File troppo grande. Massimo: {MAX_FILE_SIZE // 1024 // 1024} MB",
        )

    # Salvataggio con nome univoco
    estensione = Path(file.filename).suffix
    nome_file = f"{uuid4().hex}{estensione}"
    percorso = UPLOAD_DIR / str(prodotto_id) / nome_file

    percorso.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(percorso, "wb") as f:
        await f.write(contenuto)

    return {
        "filename": nome_file,
        "size": len(contenuto),
        "content_type": file.content_type,
        "url": f"/api/v1/files/{prodotto_id}/{nome_file}",
    }
```

### Streaming di file grandi

```python
from fastapi.responses import StreamingResponse
import aiofiles


@router.get("/files/{prodotto_id}/{nome_file}")
async def scarica_file(prodotto_id: int, nome_file: str):
    """Scarica un file in streaming senza caricarlo tutto in memoria."""
    percorso = UPLOAD_DIR / str(prodotto_id) / nome_file

    if not percorso.exists():
        raise HTTPException(status_code=404, detail="File non trovato")

    async def genera_stream():
        async with aiofiles.open(percorso, "rb") as f:
            while chunk := await f.read(8192):
                yield chunk

    return StreamingResponse(
        genera_stream(),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{nome_file}"',
        },
    )
```

### Integrazione con S3

```python
import aioboto3
from contextlib import asynccontextmanager

S3_BUCKET = "mio-bucket-prodotti"
S3_REGION = "eu-south-1"


@asynccontextmanager
async def s3_client():
    session = aioboto3.Session()
    async with session.client("s3", region_name=S3_REGION) as client:
        yield client


@router.post("/prodotti/{prodotto_id}/immagine-s3")
async def carica_su_s3(
    prodotto_id: int,
    file: UploadFile = File(...),
):
    """Carica un file direttamente su S3."""
    chiave = f"prodotti/{prodotto_id}/{uuid4().hex}{Path(file.filename).suffix}"

    async with s3_client() as s3:
        await s3.upload_fileobj(
            file.file,
            S3_BUCKET,
            chiave,
            ExtraArgs={
                "ContentType": file.content_type,
                "ACL": "private",
            },
        )

        # Genera URL pre-firmato con scadenza di 1 ora
        url = await s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": chiave},
            ExpiresIn=3600,
        )

    return {"chiave": chiave, "url_temporaneo": url}
```

---

## WebSocket con FastAPI

FastAPI supporta WebSocket nativamente tramite Starlette. I WebSocket sono ideali per comunicazione bidirezionale in tempo reale: chat, notifiche, dashboard live, giochi multiplayer.

### Endpoint WebSocket base

```python
from fastapi import WebSocket, WebSocketDisconnect


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
):
    """Endpoint WebSocket con gestione connessione e disconnessione."""
    await websocket.accept()
    try:
        while True:
            messaggio = await websocket.receive_text()
            # Echo con conferma
            await websocket.send_json({
                "client_id": client_id,
                "messaggio": messaggio,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    except WebSocketDisconnect:
        print(f"Client {client_id} disconnesso")
```

### Connection Manager per broadcasting

```python
from dataclasses import dataclass, field


@dataclass
class ConnectionManager:
    """Gestisce le connessioni WebSocket attive e il broadcasting."""
    connessioni_attive: dict[str, WebSocket] = field(default_factory=dict)
    stanze: dict[str, set[str]] = field(default_factory=dict)

    async def connetti(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.connessioni_attive[client_id] = websocket

    def disconnetti(self, client_id: str):
        self.connessioni_attive.pop(client_id, None)
        # Rimuovi da tutte le stanze
        for stanza in self.stanze.values():
            stanza.discard(client_id)

    async def invia_personale(self, client_id: str, messaggio: dict):
        ws = self.connessioni_attive.get(client_id)
        if ws:
            await ws.send_json(messaggio)

    async def broadcast(self, messaggio: dict, escludi: str | None = None):
        """Invia a tutti i client connessi, opzionalmente escludendo uno."""
        for cid, ws in self.connessioni_attive.items():
            if cid != escludi:
                try:
                    await ws.send_json(messaggio)
                except Exception:
                    self.disconnetti(cid)

    async def broadcast_stanza(self, stanza: str, messaggio: dict):
        """Invia solo ai client nella stanza specificata."""
        membri = self.stanze.get(stanza, set())
        for cid in membri:
            await self.invia_personale(cid, messaggio)

    def entra_stanza(self, client_id: str, stanza: str):
        if stanza not in self.stanze:
            self.stanze[stanza] = set()
        self.stanze[stanza].add(client_id)


manager = ConnectionManager()


@app.websocket("/ws/chat/{stanza}")
async def chat_websocket(
    websocket: WebSocket,
    stanza: str,
    client_id: str = Query(...),
):
    await manager.connetti(client_id, websocket)
    manager.entra_stanza(client_id, stanza)

    await manager.broadcast_stanza(stanza, {
        "tipo": "sistema",
        "messaggio": f"{client_id} e entrato nella stanza",
    })

    try:
        while True:
            testo = await websocket.receive_text()
            await manager.broadcast_stanza(stanza, {
                "tipo": "messaggio",
                "da": client_id,
                "testo": testo,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
    except WebSocketDisconnect:
        manager.disconnetti(client_id)
        await manager.broadcast_stanza(stanza, {
            "tipo": "sistema",
            "messaggio": f"{client_id} ha lasciato la stanza",
        })
```

---

## GraphQL con Strawberry

Strawberry e la libreria GraphQL per Python che sfrutta i dataclass e i type hints nativi. Si integra nativamente con FastAPI.

### Setup base

```python
# app/graphql/schema.py
import strawberry
from strawberry.fastapi import GraphQLRouter
from datetime import datetime
from decimal import Decimal


@strawberry.type
class ProdottoType:
    id: int
    nome: str
    prezzo: Decimal
    categoria: str
    disponibile: bool
    creato_il: datetime


@strawberry.type
class Query:
    @strawberry.field
    async def prodotto(self, id: int, info: strawberry.types.Info) -> ProdottoType | None:
        db = info.context["db"]
        result = await db.execute(select(Prodotto).where(Prodotto.id == id))
        p = result.scalar_one_or_none()
        if not p:
            return None
        return ProdottoType(
            id=p.id, nome=p.nome, prezzo=p.prezzo,
            categoria=p.categoria, disponibile=p.disponibile,
            creato_il=p.creato_il,
        )

    @strawberry.field
    async def prodotti(
        self,
        info: strawberry.types.Info,
        categoria: str | None = None,
        limit: int = 20,
    ) -> list[ProdottoType]:
        db = info.context["db"]
        query = select(Prodotto)
        if categoria:
            query = query.where(Prodotto.categoria == categoria)
        query = query.limit(limit)
        result = await db.execute(query)
        return [
            ProdottoType(
                id=p.id, nome=p.nome, prezzo=p.prezzo,
                categoria=p.categoria, disponibile=p.disponibile,
                creato_il=p.creato_il,
            )
            for p in result.scalars()
        ]


schema = strawberry.Schema(query=Query)
graphql_app = GraphQLRouter(schema)

# In app/main.py:
# app.include_router(graphql_app, prefix="/graphql")
```

### DataLoader per il problema N+1

Il problema N+1 si verifica quando una query GraphQL risolve una lista di entita, e per ciascuna esegue una query aggiuntiva per caricare una relazione. Con 100 prodotti e le loro categorie, si generano 101 query (1 lista + 100 categorie). DataLoader risolve questo raggruppando le richieste in una singola query batch.

```python
from strawberry.dataloader import DataLoader
from typing import Sequence


async def carica_categorie_batch(
    chiavi: list[int],
) -> Sequence[CategoriaType | None]:
    """Carica multiple categorie in una singola query."""
    async with async_session() as db:
        result = await db.execute(
            select(Categoria).where(Categoria.id.in_(chiavi))
        )
        categorie_map = {c.id: c for c in result.scalars()}
        # IMPORTANTE: restituire nello stesso ordine delle chiavi
        return [
            CategoriaType(
                id=categorie_map[k].id,
                nome=categorie_map[k].nome,
            ) if k in categorie_map else None
            for k in chiavi
        ]


@strawberry.type
class ProdottoConCategoria:
    id: int
    nome: str
    prezzo: Decimal
    categoria_id: int

    @strawberry.field
    async def categoria(self, info: strawberry.types.Info) -> CategoriaType | None:
        """Usa DataLoader: 100 prodotti → 1 query categorie, non 100."""
        loader = info.context["categoria_loader"]
        return await loader.load(self.categoria_id)


# Nel context della request:
async def get_context(request):
    return {
        "db": async_session(),
        "categoria_loader": DataLoader(load_fn=carica_categorie_batch),
    }
```

### Persisted Queries

Le persisted queries riducono la dimensione delle richieste GraphQL e migliorano la sicurezza impedendo l'esecuzione di query arbitrarie. Il client invia solo l'hash della query, non il testo completo.

Strawberry supporta Automatic Persisted Queries (APQ) tramite un'estensione. Il flusso APQ funziona cosi:

1. Il client calcola l'hash SHA-256 della query.
2. Invia la richiesta con solo l'hash (`extensions.persistedQuery.sha256Hash`).
3. Se il server ha la query in cache, la esegue. Altrimenti, restituisce `PERSISTED_QUERY_NOT_FOUND`.
4. Il client re-invia la richiesta completa (hash + query text). Il server la memorizza e la esegue.
5. Le richieste successive usano solo l'hash.

```python
# Implementazione base di un registry di persisted queries
import hashlib


class PersistedQueryStore:
    """Store in memoria per persisted queries. In produzione usare Redis."""

    def __init__(self):
        self._queries: dict[str, str] = {}

    def registra(self, query: str) -> str:
        sha256 = hashlib.sha256(query.encode()).hexdigest()
        self._queries[sha256] = query
        return sha256

    def recupera(self, sha256: str) -> str | None:
        return self._queries.get(sha256)

    def salva(self, sha256: str, query: str):
        # Verifica integrita
        hash_calcolato = hashlib.sha256(query.encode()).hexdigest()
        if hash_calcolato != sha256:
            raise ValueError("Hash non corrispondente alla query")
        self._queries[sha256] = query


# Per la documentazione completa dell'estensione APQ in Strawberry,
# consultare: https://strawberry.rocks/docs/extensions/automatic-persisted-queries
```

---

## Sicurezza API — CORS, CSRF, Sanitizzazione, SQL Injection

### CORS (Cross-Origin Resource Sharing)

CORS controlla quali origini possono accedere all'API dal browser. Una configurazione errata espone l'API a richieste non autorizzate da siti malevoli.

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.esempio.it",
        "https://admin.esempio.it",
    ],
    # MAI usare allow_origins=["*"] con allow_credentials=True
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    expose_headers=["X-Total-Count", "X-RateLimit-Remaining", "Link"],
    max_age=600,  # Cache preflight per 10 minuti
)
```

**Errore comune**: impostare `allow_origins=["*"]` con `allow_credentials=True`. I browser rifiutano questa combinazione per ragioni di sicurezza. Se serve autenticazione via cookie, specificare le origini esatte.

### CSRF per API con cookie auth

Le API che usano cookie per l'autenticazione (invece di Bearer token) sono vulnerabili a CSRF. Il pattern Double Submit Cookie e una contromisura efficace.

```python
import secrets
from fastapi import Request, Response


CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"


async def middleware_csrf(request: Request, call_next):
    """
    Middleware CSRF con Double Submit Cookie.
    Necessario SOLO se l'API usa cookie per l'autenticazione.
    NON necessario per API con Bearer token (il token stesso e la protezione).
    """
    if request.method in ("GET", "HEAD", "OPTIONS"):
        response = await call_next(request)
        # Genera e imposta il cookie CSRF su richieste safe
        if CSRF_COOKIE_NAME not in request.cookies:
            token = secrets.token_hex(32)
            response.set_cookie(
                CSRF_COOKIE_NAME,
                token,
                httponly=False,  # Il JS deve leggerlo
                secure=True,
                samesite="strict",
            )
        return response

    # Per metodi mutanti, verifica che header e cookie corrispondano
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
    header_token = request.headers.get(CSRF_HEADER_NAME)

    if not cookie_token or not header_token or cookie_token != header_token:
        return JSONResponse(
            status_code=403,
            content={"detail": "Token CSRF mancante o non valido"},
        )

    return await call_next(request)
```

### Sanitizzazione dell'input

Anche con Pydantic che valida i tipi, i contenuti testuali possono veicolare attacchi XSS o injection se usati in contesti non sicuri.

```python
import html
import re
from pydantic import BaseModel, field_validator


class CommentoCreate(BaseModel):
    testo: str
    autore: str

    @field_validator("testo", "autore")
    @classmethod
    def sanitizza_testo(cls, v: str) -> str:
        """Rimuovi tag HTML e caratteri pericolosi."""
        # Escape entita HTML
        v = html.escape(v, quote=True)
        # Rimuovi sequenze di controllo Unicode
        v = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", v)
        return v.strip()
```

### Prevenzione SQL Injection

La regola fondamentale: **mai** costruire query SQL concatenando stringhe con input utente. Usare sempre query parametrizzate.

```python
# PERICOLOSO — vulnerabile a SQL injection
query_pericolosa = f"SELECT * FROM prodotti WHERE nome = '{input_utente}'"

# SICURO — query parametrizzata con SQLAlchemy
from sqlalchemy import select, text

# Opzione 1: ORM (sempre sicuro)
query = select(Prodotto).where(Prodotto.nome == input_utente)

# Opzione 2: Raw SQL parametrizzato (sicuro con :bind)
query = text("SELECT * FROM prodotti WHERE nome = :nome")
result = await db.execute(query, {"nome": input_utente})

# Opzione 3: LIKE con escape esplicito
def ricerca_sicura(termine: str):
    """Escape dei caratteri speciali LIKE prima dell'uso."""
    termine_sicuro = (
        termine.replace("%", r"\%")
        .replace("_", r"\_")
        .replace("\\", "\\\\")
    )
    return select(Prodotto).where(
        Prodotto.nome.ilike(f"%{termine_sicuro}%")
    )
```

---

## Testing avanzato — Contract Testing e Fixture Pattern

### Contract Testing con Schemathesis

Il contract testing verifica che l'API rispetti il contratto definito nella specifica OpenAPI. Schemathesis genera automaticamente test basati sullo schema.

```bash
# Installazione
pip install schemathesis

# Esegui contro lo schema OpenAPI dell'app
schemathesis run http://localhost:8000/openapi.json \
    --checks all \
    --hypothesis-max-examples 200 \
    --base-url http://localhost:8000
```

```python
# tests/test_contract.py — contract test programmatici
import schemathesis

schema = schemathesis.from_url("http://localhost:8000/openapi.json")


@schema.parametrize()
def test_api_contract(case):
    """Verifica che ogni endpoint rispetti lo schema OpenAPI dichiarato."""
    response = case.call()
    case.validate_response(response)
```

### Fixture Pattern avanzato

```python
# tests/conftest.py — fixture composabili
import pytest
from typing import AsyncGenerator


@pytest.fixture
async def prodotto_nel_db(
    client: AsyncClient,
    headers_admin: dict,
    prodotto_esempio: dict,
) -> dict:
    """Crea un prodotto nel database e restituisce la risposta."""
    risposta = await client.post(
        "/api/v1/prodotti",
        json=prodotto_esempio,
        headers=headers_admin,
    )
    assert risposta.status_code == 201
    return risposta.json()


@pytest.fixture
async def catalogo_popolato(
    client: AsyncClient,
    headers_admin: dict,
) -> list[dict]:
    """Popola il catalogo con un set rappresentativo di prodotti."""
    prodotti = [
        {"nome": "Laptop Pro", "prezzo": "1299.99", "categoria": "elettronica", "sku": "EL-20001"},
        {"nome": "Mouse Wireless", "prezzo": "29.99", "categoria": "elettronica", "sku": "EL-20002"},
        {"nome": "T-shirt Cotone", "prezzo": "19.99", "categoria": "abbigliamento", "sku": "AB-30001"},
        {"nome": "Jeans Slim", "prezzo": "59.99", "categoria": "abbigliamento", "sku": "AB-30002"},
        {"nome": "Libro Python", "prezzo": "39.99", "categoria": "libri", "sku": "LB-40001"},
    ]
    risultati = []
    for p in prodotti:
        r = await client.post("/api/v1/prodotti", json=p, headers=headers_admin)
        risultati.append(r.json())
    return risultati


class TestFiltriAvanzati:
    """Test che dimostrano l'uso di fixture composte."""

    @pytest.mark.anyio
    async def test_filtra_per_range_prezzo(
        self, client: AsyncClient, catalogo_popolato: list[dict]
    ):
        risposta = await client.get(
            "/api/v1/prodotti",
            params={"prezzo_min": "20", "prezzo_max": "50"},
        )

        dati = risposta.json()
        for prodotto in dati["data"]:
            prezzo = float(prodotto["prezzo"])
            assert 20 <= prezzo <= 50
```

---

## Best Practices

Le best practices seguenti sintetizzano le lezioni apprese dalla progettazione e manutenzione di API in produzione. Non sono regole assolute, ma linee guida che nella stragrande maggioranza dei casi portano a API piu robuste, manutenibili e apprezzate dai consumatori.

1. **Usa sempre HTTPS in produzione.** Le API trasportano dati sensibili — credenziali, dati personali, transazioni. HTTP in chiaro espone tutto al mondo. Non esistono eccezioni accettabili a questa regola.

2. **Progetta l'API dal punto di vista del consumatore, non del database.** Le risorse dell'API non devono corrispondere uno a uno alle tabelle del database. Pensa a cosa serve al client e modella le risposte di conseguenza. Un endpoint `/api/v1/dashboard` che aggrega dati da piu tabelle e perfettamente legittimo.

3. **Valida sempre l'input, mai fidarsi del client.** Ogni dato proveniente dall'esterno e potenzialmente pericoloso. Usa Pydantic o Marshmallow per validare rigorosamente ogni campo. Non limitarti ai tipi: valida anche i range, i pattern, le relazioni tra campi.

4. **Restituisci codici di stato HTTP appropriati e messaggi di errore strutturati.** Un generico 500 per ogni errore rende il debugging impossibile. Usa i codici corretti (400 per input errato, 404 per risorse mancanti, 409 per conflitti) e adotta un formato di errore consistente come RFC 7807.

5. **Implementa paginazione per tutte le liste.** Mai restituire collezioni complete senza limiti. Anche se oggi la tabella ha 10 record, domani ne avra 10.000. La paginazione va implementata dall'inizio, non aggiunta come ripensamento.

6. **Versionamento dell'API fin dal primo giorno.** Anche se pensi che l'API non cambiera mai, inizia con `/api/v1/`. Il costo e zero, il beneficio futuro e enorme. Cambiare la struttura degli URL dopo il deploy e doloroso.

7. **Documenta ogni endpoint con esempi realistici.** La documentazione generata automaticamente da FastAPI e un ottimo punto di partenza, ma arricchiscila con esempi di casi d'uso reali, flussi completi (autenticazione, creazione, aggiornamento, eliminazione) e scenari di errore.

8. **Implementa rate limiting e monitoraggio.** Senza rate limiting, un singolo client malfunzionante puo mettere in ginocchio l'intero servizio. Senza monitoraggio, non saprai che sta succedendo finche gli utenti non si lamentano. Strumenti come Prometheus e Grafana sono indispensabili.

9. **Scrivi test per ogni endpoint, inclusi i casi di errore.** I test non dovrebbero verificare solo il "happy path". Testa i 400, i 401, i 403, i 404, i 409, i 422. Testa i limiti della paginazione. Testa con dati ai confini della validazione. Il testing completo e cio che separa un'API robusta da una fragile.

10. **Separa le responsabilita: routing, business logic e data access.** Il router riceve la richiesta e la valida. Il service implementa la logica di business. Il repository accede ai dati. Questa separazione rende il codice testabile, manutenibile e modificabile senza effetti collaterali imprevisti.

---

## Troubleshooting

### Errori frequenti e soluzioni

| Problema | Causa probabile | Soluzione |
|----------|----------------|-----------|
| 422 senza dettagli utili | Error handler di default FastAPI | Registrare handler RFC 7807 personalizzato |
| CORS bloccato nel browser | Origini non configurate o preflight mancante | Aggiungere middleware CORS con origini esplicite |
| 401 intermittenti | Token JWT scaduto senza refresh | Implementare flusso refresh token |
| Timeout su liste grandi | Paginazione mancante o offset troppo grande | Passare a cursor-based pagination |
| N+1 query in GraphQL | Resolve sequenziale per ogni entita | Usare DataLoader per batch loading |
| Rate limit troppo aggressivo | Chiave rate limit troppo granulare | Usare chiave basata su utente, non IP |
| File upload fallisce per file grandi | Limite body di default (1MB) | Configurare `app = FastAPI(max_request_size=...)` o proxy |
| WebSocket si disconnette | Timeout idle del reverse proxy | Configurare timeout WebSocket nel proxy e implementare ping/pong |

### Debug della validazione Pydantic

Quando un modello Pydantic rifiuta dati apparentemente validi:

```python
from pydantic import ValidationError

dati = {"nome": "Test", "prezzo": "abc", "sku": "formato-errato"}
try:
    ProdottoCreate.model_validate(dati)
except ValidationError as e:
    # Stampa tutti gli errori in formato leggibile
    print(e.json(indent=2))
    # Accedi programmaticamente
    for errore in e.errors():
        print(f"Campo: {errore['loc']} — Tipo: {errore['type']} — Msg: {errore['msg']}")
```

### Debug dei token JWT

```python
from jose import jwt

token = "eyJ..."  # token problematico

# Decodifica senza verificare la firma (solo per debug!)
payload = jwt.get_unverified_claims(token)
print(f"Subject: {payload.get('sub')}")
print(f"Scadenza: {datetime.fromtimestamp(payload['exp'], tz=timezone.utc)}")
print(f"Emesso: {datetime.fromtimestamp(payload.get('iat', 0), tz=timezone.utc)}")
print(f"Scopes: {payload.get('scopes', [])}")

# Verifica se e scaduto
from datetime import datetime, timezone
scadenza = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
if scadenza < datetime.now(timezone.utc):
    print("TOKEN SCADUTO")
```

---

## Esercizi

### Esercizio 1 — CRUD con validazione (Livello base)

Implementare un'API per la gestione di una biblioteca. Risorse: `libri` e `autori` con relazione molti-a-molti. Requisiti:
- Validazione ISBN con regex
- Paginazione offset per la lista libri
- Filtro per genere e anno di pubblicazione
- Almeno 5 test per endpoint

### Esercizio 2 — Autenticazione e autorizzazione (Livello intermedio)

Estendere l'API della biblioteca con:
- Registrazione utente con hash bcrypt
- Login con JWT access + refresh token
- Ruoli: `lettore`, `bibliotecario`, `admin`
- I lettori possono solo leggere; i bibliotecari possono creare/modificare libri; solo admin gestiscono utenti
- Test per ogni scenario di autorizzazione

### Esercizio 3 — Rate limiting e caching (Livello intermedio)

Aggiungere:
- Rate limiting sliding window (50 req/min per lettori, 200 per admin)
- Caching ETag sulle risposte di dettaglio libro
- Caching Redis sulla lista libri con invalidazione automatica alla modifica
- Header `X-RateLimit-*` in ogni risposta

### Esercizio 4 — GraphQL con DataLoader (Livello avanzato)

Creare un layer GraphQL con Strawberry per l'API biblioteca:
- Query: `libro(id)`, `libri(genere, anno)`, `autore(id)`
- DataLoader per la relazione libro-autore
- Mutation per creare un libro con autori associati
- Verificare che N+1 non si verifichi con logging delle query SQL

### Esercizio 5 — API completa production-ready (Livello avanzato)

Costruire un'API completa per un sistema di e-commerce:
- Prodotti, ordini, utenti, pagamenti
- Errori RFC 7807 su tutti gli endpoint
- WebSocket per notifiche stato ordine in tempo reale
- Upload immagini prodotto su storage locale o S3
- Contract testing con Schemathesis
- Documentazione OpenAPI personalizzata con server multipli

---

## Letture e riferimenti

### Specifiche e standard

- RFC 7807 — Problem Details for HTTP APIs: https://datatracker.ietf.org/doc/html/rfc7807
- RFC 9457 — Problem Details for HTTP APIs (revisione 2023): https://datatracker.ietf.org/doc/html/rfc9457
- RFC 8288 — Web Linking (Link headers): https://datatracker.ietf.org/doc/html/rfc8288
- RFC 6838 — Media Type Specifications (content negotiation): https://datatracker.ietf.org/doc/html/rfc6838
- RFC 6749 — OAuth 2.0 Authorization Framework: https://datatracker.ietf.org/doc/html/rfc6749
- RFC 7519 — JSON Web Token (JWT): https://datatracker.ietf.org/doc/html/rfc7519
- OpenAPI Specification 3.1: https://spec.openapis.org/oas/v3.1.0

### Documentazione ufficiale

- FastAPI: https://fastapi.tiangolo.com
- Pydantic v2: https://docs.pydantic.dev/latest/
- Strawberry GraphQL: https://strawberry.rocks/docs
- Flask: https://flask.palletsprojects.com
- httpx: https://www.python-httpx.org
- SQLAlchemy Async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Schemathesis: https://schemathesis.readthedocs.io

### Testi consigliati

- Fielding, R. T. (2000). *Architectural Styles and the Design of Network-based Software Architectures*. Tesi di dottorato, UC Irvine.
- Lauret, A. (2019). *The Design of Web APIs*. Manning Publications.

---

## Cross-link

| Modulo | Relazione con REST API |
|--------|----------------------|
| [08 — Testing](08-testing.md) | Pattern pytest, fixture, coverage per test API |
| [10 — Programmazione asincrona](10-programmazione-asincrona.md) | asyncio, async/await usati da FastAPI e httpx |
| [11 — Web framework](11-web-framework.md) | FastAPI e Flask come framework base |
| [12 — Database](12-database.md) | SQLAlchemy async, sessioni, query ORM |
| [18 — Sicurezza](18-sicurezza.md) | Principi di sicurezza applicati alle API |
| [25 — Performance](25-performance.md) | Ottimizzazione query, caching, profiling |
| [29 — Pydantic e validazione](29-pydantic-e-validazione.md) | Pydantic v2 deep-dive, modelli, validatori |
| [31 — Osservabilita](31-osservabilita-otel-prometheus.md) | Metriche, tracing e logging per API |

---

## Glossario

| Termine | Definizione |
|---------|------------|
| **Bearer Token** | Token di autenticazione trasmesso nell'header `Authorization: Bearer <token>` |
| **CORS** | Cross-Origin Resource Sharing — meccanismo HTTP che controlla l'accesso cross-origin da browser |
| **CRUD** | Create, Read, Update, Delete — le quattro operazioni base sulle risorse |
| **CSRF** | Cross-Site Request Forgery — attacco che forza un browser autenticato a eseguire azioni non volute |
| **Cursor pagination** | Paginazione basata su un puntatore opaco all'ultimo elemento visto, efficiente su dataset grandi |
| **DataLoader** | Pattern per raggruppare richieste di dati (batch) ed evitare il problema N+1 nelle query |
| **ETag** | Entity Tag — hash del contenuto usato per il caching condizionale HTTP |
| **GraphQL** | Linguaggio di query per API che permette al client di richiedere esattamente i dati necessari |
| **HATEOAS** | Hypermedia As The Engine Of Application State — vincolo REST per la navigabilita delle risorse |
| **Idempotenza** | Proprieta per cui ripetere la stessa operazione produce lo stesso risultato |
| **JWT** | JSON Web Token — standard per token di autenticazione firmati (RFC 7519) |
| **N+1 problem** | Anti-pattern dove N entita generano N query aggiuntive per caricare le relazioni |
| **OAuth2** | Framework di autorizzazione che delega l'autenticazione a un authorization server (RFC 6749) |
| **Offset pagination** | Paginazione classica con `page` e `size`, semplice ma inefficiente con offset grandi |
| **OpenAPI** | Specifica standard per descrivere REST API in formato machine-readable (YAML/JSON) |
| **Persisted query** | Query GraphQL pre-registrata, identificata da hash SHA-256 invece che dal testo completo |
| **Problem Details** | Formato standard (RFC 7807/9457) per comunicare errori HTTP in modo machine-readable |
| **Rate limiting** | Meccanismo che limita il numero di richieste in un intervallo di tempo |
| **RBAC** | Role-Based Access Control — autorizzazione basata su ruoli assegnati agli utenti |
| **Refresh token** | Token a lunga scadenza usato per ottenere nuovi access token senza re-autenticazione |
| **REST** | Representational State Transfer — stile architetturale per sistemi distribuiti (Fielding, 2000) |
| **Scope** | Permesso granulare assegnato a un token OAuth2 per limitare l'accesso a risorse specifiche |
| **Sliding window** | Algoritmo di rate limiting che considera una finestra temporale mobile |
| **Token bucket** | Algoritmo di rate limiting che consente burst controllati tramite un "secchio" di token |
| **WebSocket** | Protocollo per comunicazione bidirezionale full-duplex su una singola connessione TCP |

---

> **Nota**: questa guida copre i fondamenti e le pratiche avanzate per la costruzione di REST API professionali in Python. Per approfondimenti specifici, si consiglia di consultare la documentazione ufficiale di [FastAPI](https://fastapi.tiangolo.com), [Flask](https://flask.palletsprojects.com), [Pydantic](https://docs.pydantic.dev) e la specifica [OpenAPI](https://spec.openapis.org/oas/latest.html).
