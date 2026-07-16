# Tutorial: REST API Professionali con FastAPI — Dal Principiante all'Esperto

> **Companion to:** `13-rest-api.md`
> **Scope:** Principi REST (Richardson Maturity Model), HTTP verbs semantics, status codes
> completi, HATEOAS, API versioning, FastAPI CRUD completo, Pydantic v2 schemas,
> dependency injection, autenticazione JWT (access/refresh token), OAuth2 scopes, RBAC,
> pagination (offset vs cursor), filtering, sorting, rate limiting (sliding window, token
> bucket), caching (ETags, Redis), OpenAPI customization, testing API, WebSocket, GraphQL
> con Strawberry, sicurezza (CORS, CSRF, SQL injection), contract testing.
> **Prerequisiti:** `tutorial_11_web_framework.md` + `tutorial_12_database.md` completati
> **Durata stimata:** 35-45 ore
> **Lingua:** Italiano

---

## Indice Generale

### PARTE A — BASI ASSOLUTE
- [A1: Cos\'e una REST API?](#a1)
- [A2: I 6 Principi REST](#a2)
- [A3: HTTP Verbs — GET, POST, PUT, PATCH, DELETE](#a3)
- [A4: Status Codes — Il Semaforo dell\'API](#a4)
- [A5: Il Primo CRUD Completo con FastAPI](#a5)
- [A6: Pydantic Schemas per Request e Response](#a6)

### PARTE B — COMPRENSIONE PROFONDA
- [B1: Autenticazione JWT — Chi Sei?](#b1)
- [B2: Autorizzazione e RBAC — Cosa Puoi Fare?](#b2)
- [B3: OAuth2 — Accedi con Google](#b3)
- [B4: Pagination — Non Caricare 10.000 Record](#b4)
- [B5: Filtering, Sorting, Search — Query Params Professionali](#b5)
- [B6: API Versioning — Come Evolvere senza Rompere](#b6)
- [B7: Rate Limiting — Proteggersi dagli Abusi](#b7)
- [B8: Caching — Rispondere piu Velocemente](#b8)
- [B9: Error Handling Professionale — RFC 7807](#b9)
- [B10: OpenAPI/Swagger Customization](#b10)
- [B11: Testing delle API](#b11)
- [B12: HATEOAS e Richardson Maturity Model](#b12)

### PARTE C — ESERCIZI (12 esercizi guidati)
### PARTE D — APPROFONDIMENTO ESPERTI
### PARTE E — RIEPILOGO, CHECKLIST E GLOSSARIO

---

## Introduzione — Perche Questo Tutorial?

Hai completato il tutorial_11 (Web Framework) e il tutorial_12 (Database). Sai gia fare
un\'applicazione Flask o FastAPI base che risponde a richieste HTTP e interagisce con un
database. Ottimo punto di partenza.

Ma c\'e una differenza enorme tra "un\'applicazione che risponde a HTTP" e "una REST API
professionale". E\' la stessa differenza tra saper guidare una macchina e saper progettare
una rete stradale: le competenze di base ci sono, ma il design sistemico manca completamente.

Un\'API ben progettata ha le seguenti caratteristiche:

**Prevedibile** — uno sviluppatore che usa la tua API per la prima volta riesce a indovinare
come funzionano gli endpoint che non ha mai visto, basandosi su quelli che ha gia usato.
Se `GET /api/v1/prodotti/42` restituisce un prodotto, allora `GET /api/v1/utenti/7`
restituisce un utente. Il pattern e universale.

**Robusta** — gestisce errori in modo strutturato e consistente. Non restituisce HTML di
errore in risposta a JSON malformato. Non restituisce 500 per tutto. Restituisce messaggi
di errore machine-readable, con codici e descrizioni standardizzati (formato RFC 7807).

**Sicura** — autentica chi fa la richiesta, autorizza cosa puo fare, valida tutto
l\'input, limita il numero di richieste per prevenire abusi, non espone dati interni.

**Scalabile** — funziona con 10 utenti e con 10 milioni di utenti senza cambiare
l\'interfaccia. La statelessness e la cache permettono di aggiungere server in modo
trasparente al client.

**Versionabile** — quando l\'API deve cambiare (e cambiera sempre), i client esistenti
non smettono di funzionare. La nuova versione convive con la vecchia durante la
transizione.

Questo tutorial ti porta da "so fare una risposta HTTP" a "so progettare e implementare
un\'API REST professionale". Ogni concetto viene spiegato con un\'analogia del mondo reale,
poi implementato con codice completo, testato con comandi curl, e verificato con pytest.

---

## Prerequisiti Tecnici

Prima di proseguire, assicurati di avere dimestichezza con:

1. **Python async/await** — FastAPI e asincrono. Se `async def` e `await` ti sembrano
   alieni, studia prima il tutorial_10 (Programmazione Asincrona).

2. **SQLAlchemy ORM base** — useremo SQLAlchemy async. Il tutorial_12 copre questo.

3. **Pydantic BaseModel base** — sai definire un modello Pydantic semplice. Qui
   approfondiamo validator, computed_field, discriminated unions.

4. **HTTP fondamenti** — sai cosa sono GET, POST, header, body JSON. Il tutorial_11
   ha coperto questo.

---

## Setup Ambiente di Sviluppo

```bash
# Crea un ambiente virtuale dedicato
python -m venv venv_rest
source venv_rest/bin/activate       # Linux / Mac
venv_rest\Scripts\activate          # Windows

# Installa tutte le dipendenze del tutorial
pip install "fastapi[all]==0.115.0"
pip install "sqlalchemy[asyncio]==2.0.36"
pip install "aiosqlite==0.20.0"
pip install "asyncpg==0.30.0"
pip install "python-jose[cryptography]==3.3.0"
pip install "passlib[bcrypt]==1.7.4"
pip install "python-multipart==0.0.12"
pip install "redis==5.2.0"
pip install "slowapi==0.1.9"
pip install "httpx==0.27.2"
pip install "pytest==8.3.3"
pip install "anyio[trio]==4.6.2"
pip install "aiofiles==24.1.0"

# Avvia il server di sviluppo
uvicorn app.main:app --reload --port 8000
```

La struttura del progetto che costruiremo durante il tutorial:

```
negozio_api/
├── app/
│   ├── __init__.py
│   ├── main.py              # Entrypoint, lifespan, middleware globali
│   ├── config.py            # Configurazione (Settings con Pydantic Settings)
│   ├── dependencies.py      # Dependency injection (DB session, auth)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py          # Base declarativa SQLAlchemy
│   │   └── prodotto.py      # ORM model Prodotto
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── prodotto.py      # Pydantic: ProdottoCreate, ProdottoUpdate, ProdottoResponse
│   │   └── auth.py          # Pydantic: Token, TokenPair, LoginRequest
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── prodotti.py      # Endpoints CRUD prodotti
│   │   └── auth.py          # Endpoints login, refresh, logout
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── jwt.py           # Logica JWT: crea_token, verifica_token
│   │   └── dependencies.py  # Deps: get_utente_corrente, richiedi_ruolo
│   ├── middleware/
│   │   ├── request_id.py    # Aggiunge X-Request-ID a ogni richiesta
│   │   └── timing.py        # Misura e logga la durata delle richieste
│   └── errors/
│       └── handlers.py      # Handler RFC 7807 per HTTPException e ValidationError
├── tests/
│   ├── conftest.py          # Fixture: client, db, token_admin, prodotto_esempio
│   ├── test_prodotti.py     # Test CRUD prodotti
│   └── test_auth.py         # Test login, refresh, autorizzazione
├── alembic/                 # Migrazioni database
└── pyproject.toml
```

---

<a id="a1"></a>
## A1: Cos\'e una REST API? Il Contratto tra Client e Server

### L\'analogia del ristorante

Immagina di entrare in un ristorante. Tra te (il cliente) e la cucina (il sistema che
prepara il cibo) c\'e un intermediario fondamentale: il **menu** e il **cameriere**.

Il **menu** definisce il contratto:
- Cosa puoi ordinare — gli endpoint disponibili (`/api/v1/prodotti`, `/api/v1/ordini`)
- Come e strutturato ogni piatto — lo schema JSON della risposta
- Le regole — non puoi ordinare un piatto che non e nel menu (404 Not Found)

Il **cameriere** e il contratto vivente:
- Riceve la tua richiesta in modo standardizzato (`GET /api/v1/prodotti/42`)
- La porta in cucina (il database, la business logic) senza che tu ci vada direttamente
- Porta indietro il risultato nel formato atteso (JSON strutturato)
- Ti avvisa se hai sbagliato qualcosa ("Questo piatto non esiste" = 404)
- Non ti permette di accedere direttamente alla cucina (incapsula l\'implementazione)

**La REST API e il cameriere + il menu**: definisce cosa si puo fare, come farlo,
e cosa aspettarsi in risposta. Il cuoco (database, logica di business, infrastruttura)
non e mai esposto direttamente al cliente.

### Cosa significa REST?

**REST** = **Re**presentational **S**tate **T**ransfer

Coniato da Roy Fielding nella sua tesi di dottorato all\'UC Irvine nel 2000. Non e un
protocollo (come HTTP, FTP, SMTP) ne uno standard formale come SOAP. E uno **stile
architetturale**: un insieme di vincoli che, se rispettati, producono sistemi scalabili,
semplici e interoperabili.

La parola chiave e **Representational**: quando chiedi `GET /api/v1/prodotti/42`, il
server non ti manda l\'oggetto Python interno, non ti da accesso al record PostgreSQL
grezzo. Ti manda una **rappresentazione** dello stato corrente di quella risorsa —
tipicamente JSON.

```
Risorsa reale (nel database):
  Record: id=42, nome="Laptop", prezzo=999.99, categoria_id=3, ...

Rappresentazione (JSON che ricevi):
  {
    "id": 42,
    "nome": "Laptop ProBook 450",
    "prezzo": "999.99",
    "categoria": "elettronica",
    "disponibile": true
  }
```

Il server decide cosa includere nella rappresentazione e come strutturarla. La risorsa
puo avere 50 colonne nel database, ma la rappresentazione mostra solo i 10 campi
rilevanti per il client.

### REST vs SOAP vs GraphQL vs gRPC

| Tecnologia | Paradigma | Protocollo | Formato dati | Quando usarla |
|-----------|-----------|-----------|-------------|---------------|
| **REST** | Risorse + verbi HTTP | HTTP/1.1, HTTP/2 | JSON (de facto) | API web pubbliche, mobile backend, microservizi |
| **SOAP** | RPC con contratto WSDL | HTTP, SMTP, JMS | XML obbligatorio | Sistemi bancari legacy, enterprise con WS-Security |
| **GraphQL** | Query su grafo dati | HTTP | JSON | App mobili (risparmio banda), frontend con query variabili |
| **gRPC** | RPC tipizzato con Protobuf | HTTP/2 | Protobuf (binario) | Comunicazione interna microservizi, streaming |

**Quando scegliere REST:**
- Stai costruendo un\'API pubblica consumata da clienti eterogenei
- Vuoi sfruttare la cache HTTP (CDN, browser cache)
- Il tuo team deve debuggare con curl o Postman
- Vuoi documentazione OpenAPI auto-generata (FastAPI lo fa automaticamente)

**Quando considerare GraphQL:**
- Client diversi (web, iOS, Android) hanno bisogno di subset diversi degli stessi dati
- Vuoi eliminare il problema dell\'over-fetching (ricevere piu dati del necessario)
- La flessibilita delle query vale la complessita aggiuntiva

**Quando considerare gRPC:**
- Comunicazione interna tra microservizi ad alta frequenza
- Hai bisogno di streaming bidirezionale
- La latenza minima e la dimensione ridotta dei payload sono critiche

**Per questo tutorial:** REST con FastAPI. E lo standard del settore, richiesto nella
quasi totalita delle posizioni backend, comprensibile da qualunque client HTTP.

### La Struttura di Richiesta/Risposta HTTP

Ogni interazione con una REST API passa per HTTP. La struttura e sempre la stessa:

**Richiesta (Client → Server):**
```
METODO /percorso?query_params HTTP/1.1
Host: api.esempio.it
Content-Type: application/json
Authorization: Bearer <token>

{body JSON opzionale}
```

**Risposta (Server → Client):**
```
HTTP/1.1 CODICE DESCRIZIONE
Content-Type: application/json
Header-Aggiuntivo: valore

{body JSON opzionale}
```

**Esempio reale — creazione prodotto:**

```http
POST /api/v1/prodotti HTTP/1.1
Host: api.negozio.it
Content-Type: application/json
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.xyz

{
  "nome": "Laptop ProBook 450",
  "prezzo": 999.99,
  "categoria": "elettronica",
  "sku": "EL-12345"
}
```

Risposta:
```http
HTTP/1.1 201 Created
Content-Type: application/json
Location: /api/v1/prodotti/42

{
  "id": 42,
  "nome": "Laptop ProBook 450",
  "prezzo": "999.99",
  "categoria": "elettronica",
  "sku": "EL-12345",
  "disponibile": true,
  "creato_il": "2026-07-15T10:30:00Z",
  "aggiornato_il": "2026-07-15T10:30:00Z"
}
```

Ogni elemento ha un significato preciso:
- `POST` — sto creando una nuova risorsa
- `201 Created` — la risorsa e stata creata (non `200 OK` che e generico)
- `Location: /api/v1/prodotti/42` — dove trovare la nuova risorsa
- `creato_il`, `aggiornato_il` — generati dal server, non dal client

---

<a id="a2"></a>
## A2: I 6 Principi REST con Esempi Concreti

### Perche I Vincoli Esistono

Roy Fielding non ha inventato REST in astratto. Ha osservato perche il Web funzionava
(e funziona) con miliardi di utenti, browser eterogenei e server distribuiti in tutto
il mondo, senza coordinamento centrale, e ha formalizzato quei principi.

I "vincoli" di REST sono le proprieta che il Web aveva gia e che lo rendevano scalabile.
Se costruisci la tua API rispettando quegli stessi vincoli, ottieni le stesse proprieta.

### Vincolo 1: Client-Server (Separazione dei Ruoli)

**Principio:** Client e server sono entita separate che comunicano solo tramite
l\'interfaccia API. Il server non sa niente dell\'UI; il client non sa niente del DB.

**Analogia della televisione:**
Una stazione TV trasmette un segnale DVB-T2 standardizzato. Non sa niente del televisore
che lo riceve: se e un Sony da 75" del 2026 o un Samsung da 32" del 2015. Il televisore
non sa niente di come viene prodotto il programma. Il contratto e il segnale televisivo
standardizzato. Questa separazione permette a qualunque TV di ricevere qualunque canale.

**Beneficio concreto:**
```
SENZA separazione Client-Server:
  Il backend genera HTML con template Jinja2
  Se voglio aggiungere un\'app mobile, devo riscrivere tutto il backend
  Se voglio cambiare il frontend da React a Vue, rischio di rompere il backend

CON separazione Client-Server (REST API):
  Il backend risponde solo con JSON strutturato
  Il frontend React consuma quell\'API JSON
  L\'app iOS consuma la stessa API JSON
  L\'app Android consuma la stessa API JSON
  Un altro microservizio consuma la stessa API JSON
  → Un backend, N client diversi, tutti indipendenti
```

**Come si manifesta in FastAPI:**
```python
# Il server non sa niente di chi lo chiama. Risponde sempre con JSON puro.
@app.get("/api/v1/prodotti/{id}")
async def dettaglio_prodotto(id: int, db: AsyncSession = Depends(get_db)):
    prodotto = await db.get(Prodotto, id)
    if not prodotto:
        raise HTTPException(status_code=404, detail="Prodotto non trovato")
    return ProdottoResponse.model_validate(prodotto)
    # → puro JSON, niente HTML, niente template, niente logica UI
```

### Vincolo 2: Stateless (Senza Stato di Sessione)

**Principio:** Ogni richiesta deve essere autosufficiente: deve contenere TUTTE le
informazioni necessarie per elaborarla. Il server non conserva memoria tra richieste.

**Analogia del cassiere con amnesia:**
Ogni volta che ti avvicini allo sportello, il cassiere non ricorda chi sei. Devi
ripresentarti da zero: mostrare il documento, dire il numero di conto, spiegare cosa
vuoi. Noioso per te, ma significa che qualunque cassiere libero puo servirti — non
sei "legato" a uno specifico. Se uno va in pausa, un altro ti gestisce senza problemi.

**Perche e critico per la scalabilita:**

```
SCENARIO SENZA STATELESS — sessioni server-side:

  1. Client fa POST /login
     → Server-A crea sessione in memoria: {"session_abc123": {user_id: 7, ruolo: "admin"}}

  2. Client fa GET /prodotti con cookie session_abc123
     → Server-A gestisce OK (la sessione e qui)

  3. Load balancer manda la richiesta a Server-B
     → Server-B cerca "session_abc123" nella sua memoria → NON TROVATA!
     → ERRORE: "Sessione scaduta" anche se l\'utente si e loggato 5 minuti fa

  SOLUZIONI BRUTTE:
  a) Sticky sessions (il client viene sempre mandato allo stesso server)
     → Se quel server cade, TUTTE le sue sessioni si perdono
     → Impossibile scalare orizzontalmente in modo uniforme
  b) Sessioni condivise in Redis/database
     → Funziona, ma aggiunge complessita e un single point of failure
     → Non e piu "stateless" — lo stato e semplicemente spostato

SCENARIO CON STATELESS — JWT token:

  1. Client fa POST /login con {username, password}
     → Server genera un JWT token: eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI3IiwicnVvbG8i...
     → Il token contiene user_id=7, ruolo="admin", scadenza=tra30min, firma crittografica

  2. Client fa GET /prodotti con header Authorization: Bearer eyJ...
     → Qualunque server nel cluster verifica la firma JWT → VALIDA
     → Legge user_id=7 e ruolo="admin" dal token stesso
     → Nessuna query al DB per verificare la sessione

  VANTAGGI:
  → Qualunque server puo gestire qualunque richiesta
  → Aggiungi 100 server al cluster: zero configurazione aggiuntiva
  → Se un server cade: le richieste vanno agli altri, nessun utente e "perso"
```

**Nota importante:** Stateless NON significa che non puoi avere un database. Il DB e lo
stato persistente condiviso — e separato dal processo web. Il server web non mantiene
stato di sessione tra richieste HTTP.

**Come si manifesta in FastAPI:**
```python
# SBAGLIATO: stato nel server (dizionario in memoria)
_sessioni: dict[str, dict] = {}

@app.post("/login")
async def login(cred: Credenziali):
    utente = autentica(cred)
    session_id = secrets.token_hex(32)
    _sessioni[session_id] = {"user_id": utente.id}   # STATO NEL SERVER!
    return {"session_id": session_id}

# CORRETTO: tutto lo stato nel JWT token (viaggia con il client)
@app.post("/login", response_model=TokenPair)
async def login(cred: Credenziali, db: AsyncSession = Depends(get_db)):
    utente = await autentica_utente(db, cred.username, cred.password)
    if not utente:
        raise HTTPException(status_code=401, detail="Credenziali non valide")
    # Token JWT: contiene user_id, ruolo, scadenza, firma crittografica
    # Il server non salva niente — tutto e nel token che porta il client
    return crea_coppia_token(utente.id, utente.ruolo)
```

### Vincolo 3: Cacheable (Memorizzabile in Cache)

**Principio:** Le risposte devono dichiarare esplicitamente se possono essere messe in
cache. Il client, il browser, o un intermediario (CDN, proxy) possono riutilizzare
risposte precedenti senza fare una nuova richiesta al server.

**Analogia del giornale:**
Ogni mattina compri il giornale e leggi le notizie. Poi lo butti. Il giorno dopo compri
un altro giornale. Ma se il giornalista ti dice "le notizie di ieri sono ancora valide,
non e successo niente di nuovo", potresti riusare il giornale di ieri. Risparmieresti
tempo e soldi.

Il caching HTTP funziona esattamente cosi: il server dice "questa risposta e valida per
N secondi — non devi richiederla prima di allora". Il client la memorizza e la riutilizza.

**Headers di caching:**
```http
# Risposta valida 1 ora per chiunque (CDN puo servirla)
HTTP/1.1 200 OK
Cache-Control: public, max-age=3600

# Risposta valida 5 minuti, solo per questo utente specifico (non CDN)
HTTP/1.1 200 OK
Cache-Control: private, max-age=300

# Non mettere mai in cache (dati sensibili, real-time)
HTTP/1.1 200 OK
Cache-Control: no-store

# ETag: hash del contenuto per caching condizionale
HTTP/1.1 200 OK
ETag: "a3f8c2d1"
# Il client la prossima volta invia:
# If-None-Match: "a3f8c2d1"
# Se invariato → server risponde 304 Not Modified (zero body, risparmio banda)
```

**Impatto pratico del caching:**
```
SENZA CACHING — lista categorie (cambiano 1 volta a settimana):
  1.000 utenti/minuto richiedono GET /api/v1/categorie
  → 1.000 query SQL al minuto
  → 1.000 JSON serializzati al minuto
  → database sotto stress per dati quasi immutabili

CON CACHING (Cache-Control: public, max-age=3600):
  Prima richiesta: query SQL, JSON serializzato, risposta inviata, CDN la memorizza
  Richieste successive nelle prossime 3600 secondi:
  → CDN risponde direttamente (0 query SQL, 0 cariche server applicativo)
  → Il server gestisce solo 1 richiesta ogni ora per quella risorsa
  → Il database e sollevato dal carico
```

**Implementazione in FastAPI:**
```python
from fastapi import Response

@app.get("/api/v1/categorie")
async def lista_categorie(response: Response, db: AsyncSession = Depends(get_db)):
    # Le categorie cambiano raramente: 1 ora di cache pubblica
    response.headers["Cache-Control"] = "public, max-age=3600"
    result = await db.execute(select(Categoria))
    return result.scalars().all()

@app.get("/api/v1/utenti/me/profilo")
async def profilo_personale(
    response: Response,
    utente: Utente = Depends(get_utente_corrente),
):
    # Profilo personale: cache privata, 5 minuti
    response.headers["Cache-Control"] = "private, max-age=300"
    return utente

@app.get("/api/v1/saldo")
async def saldo_conto(response: Response, utente: Utente = Depends(get_utente_corrente)):
    # Dati finanziari real-time: MAI in cache
    response.headers["Cache-Control"] = "no-store"
    return {"saldo": await calcola_saldo(utente.id)}
```

### Vincolo 4: Uniform Interface (Interfaccia Uniforme)

**Principio:** Tutte le API REST usano la stessa interfaccia standardizzata. Non importa
se gestisce prodotti, utenti o ordini — il modo di interagirci e sempre lo stesso.

**Analogia USB:**
Qualunque dispositivo USB (tastiera, mouse, disco, webcam, altoparlante) usa lo stesso
connettore fisico standardizzato. Non esiste un connettore diverso per ogni marca. Questa
uniformita rende qualunque dispositivo compatibile con qualunque computer.

**Perche e la proprieta piu importante:**
```
# Un developer impara una volta come funziona un\'API REST.
# Poi puo usare QUALSIASI altra API REST senza ri-imparare il contratto.

# Imparo che GET /api/v1/prodotti/42 restituisce un prodotto.
# Senza documentazione aggiuntiva, so gia che:
GET /api/v1/utenti/7          → restituisce un utente
GET /api/v1/ordini/15         → restituisce un ordine
GET /api/v1/categorie/3       → restituisce una categoria
PATCH /api/v1/prodotti/42     → aggiorna parzialmente il prodotto 42
DELETE /api/v1/ordini/15      → elimina l\'ordine 15

# Il pattern e IDENTICO per ogni risorsa.
```

**Le 4 componenti del vincolo Uniform Interface:**

**4a. Identificazione delle risorse via URI:**
```
/api/v1/prodotti              → collezione "prodotti"
/api/v1/prodotti/42           → prodotto specifico id=42
/api/v1/prodotti/42/immagini  → le immagini del prodotto 42
/api/v1/utenti/7/ordini       → gli ordini dell\'utente 7
```

**4b. Manipolazione tramite rappresentazioni:**
Il client invia una rappresentazione dello stato desiderato; il server applica il
cambiamento alla risorsa reale.
```python
# Il client non dice "aggiorna la colonna 'prezzo' nella tabella 'prodotti'"
# Dice "voglio che il prodotto 42 abbia questa rappresentazione"
PATCH /api/v1/prodotti/42
{ "prezzo": 799.99 }
```

**4c. Messaggi auto-descrittivi:**
Ogni messaggio contiene tutto il necessario per essere interpretato: metodo HTTP,
Content-Type, Authorization, Accept.

**4d. HATEOAS** — le risposte contengono link alle azioni disponibili (vedi B12).

### Vincolo 5: Layered System (Sistema a Strati)

**Principio:** Il client non sa se sta parlando direttamente con il server finale
o con un intermediario. N strati possono esistere tra client e server.

**Architettura tipica in produzione:**
```
Client Browser / App Mobile
      |
      v  (HTTPS)
CDN (Cloudflare / Fastly)
  - Serve risorse cacheggiabili
  - Protezione DDoS
  - TLS termination
      |
      v
API Gateway (Kong / AWS API Gateway)
  - Rate limiting globale
  - Autenticazione API key
  - Routing verso i servizi
      |
      v
Load Balancer (Nginx / AWS ALB)
  - Distribuisce traffico tra istanze
      |
      +--------> FastAPI Instance 1
      +--------> FastAPI Instance 2
      +--------> FastAPI Instance 3
                      |
                      v
                 PostgreSQL (primario)
                 Redis (cache)
                 S3 (storage file)
```

Il client chiama sempre `https://api.negozio.it` — non sa nulla degli strati intermedi.
Puoi aggiungere strati, rimuoverli, spostarli senza che il client cambi una riga di codice.

### Vincolo 6: Code on Demand (Opzionale)

**Principio:** Il server puo inviare codice eseguibile (JavaScript) al client che lo
esegue localmente. E l\'unico vincolo opzionale — quasi mai applicabile alle API REST pure.

**Quando si vede:** Le Single Page Application (React, Vue, Angular) sono un esempio:
il server invia JavaScript che il browser esegue. Per API backend pure, raramente usato.

### Riepilogo — I 6 Vincoli REST

| Vincolo | Obbl. | Beneficio | Violazione tipica |
|---------|-------|-----------|------------------|
| Client-Server | SI | Frontend e backend evolvono indipendentemente | Template HTML da API REST |
| Stateless | SI | Scalabilita orizzontale illimitata | Sessioni in memoria del server |
| Cacheable | SI | Performance, riduzione carico | Cache-Control header assente |
| Uniform Interface | SI | Prevedibilita, interoperabilita | Verbi negli URL, pattern inconsistenti |
| Layered System | SI | Flessibilita infrastrutturale | Assunzione di contatto diretto |
| Code on Demand | NO | Estensibilita client | (opzionale, raramente rilevante) |

---

<a id="a3"></a>
## A3: HTTP Verbs — Il Significato di GET, POST, PUT, PATCH, DELETE

### L\'analogia dell\'archivio fisico

Immagina un archivio fisico pieno di faldoni — ogni faldone e una risorsa. Il
bibliotecario (la tua API) gestisce l\'accesso. Le operazioni possibili:

| Operazione all\'archivio | Metodo HTTP | Semantica |
|------------------------|------------|-----------|
| "Fammi una fotocopia" | **GET** | Leggi senza modificare |
| "Aggiungi questo nuovo fascicolo" | **POST** | Crea una nuova risorsa |
| "Togli questo faldone, metti quest\'altro completo" | **PUT** | Sostituisci interamente |
| "Correggi solo questo paragrafo" | **PATCH** | Aggiornamento parziale |
| "Distruggi questo documento" | **DELETE** | Eliminazione permanente |

Due proprieta importanti:

**Idempotente:** Fare la stessa operazione N volte produce lo stesso risultato della prima.
- GET e idempotente: leggere N volte lo stesso record = stesso risultato
- PUT e idempotente: impostare il nome a "Laptop Pro" N volte = sempre "Laptop Pro"
- DELETE e idempotente: eliminare qualcosa gia eliminato = stesso risultato (risorsa assente)
- POST NON e idempotente: fare POST N volte crea N risorse distinte!

**Sicuro:** Non produce effetti collaterali sul server.
- Solo GET e "sicuro" (non modifica dati)
- Tutti gli altri (POST, PUT, PATCH, DELETE) modificano lo stato

### GET — Leggere (sicuro, idempotente)

**Status code di successo:** `200 OK`

**Quando usarlo:**
- Leggere elemento singolo: `GET /api/v1/prodotti/42`
- Leggere lista con filtri: `GET /api/v1/prodotti?categoria=elettronica&page=1`
- Cercare: `GET /api/v1/prodotti?q=laptop&sort=prezzo&order=asc`
- Relazioni: `GET /api/v1/utenti/7/ordini`

**Implementazione in FastAPI:**
```python
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter(prefix="/api/v1/prodotti", tags=["prodotti"])


@router.get(
    "/{prodotto_id}",
    response_model=ProdottoResponse,
    summary="Dettaglio prodotto",
    responses={
        200: {"description": "Prodotto trovato"},
        404: {"description": "Prodotto non trovato"},
    },
)
async def dettaglio_prodotto(
    prodotto_id: int = Path(
        ...,
        gt=0,
        description="ID del prodotto (deve essere > 0)",
        example=42,
    ),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Prodotto).where(Prodotto.id == prodotto_id)
    )
    prodotto = result.scalar_one_or_none()

    if prodotto is None:
        raise HTTPException(
            status_code=404,
            detail=f"Prodotto con id {prodotto_id} non trovato",
        )

    return prodotto
```

**Curl — tutti gli scenari:**
```bash
# 1. GET prodotto esistente → 200 OK
curl -s -X GET "http://localhost:8000/api/v1/prodotti/42" \
  -H "Accept: application/json" | python -m json.tool

# Output atteso (200 OK):
# {
#   "id": 42,
#   "nome": "Laptop ProBook 450",
#   "prezzo": "999.99",
#   "categoria": "elettronica",
#   "sku": "EL-12345",
#   "disponibile": true,
#   "creato_il": "2026-07-15T10:30:00Z",
#   "aggiornato_il": "2026-07-15T10:30:00Z"
# }

# 2. GET prodotto NON esistente → 404 Not Found
curl -s -X GET "http://localhost:8000/api/v1/prodotti/99999" \
  -H "Accept: application/json"
# Output: { "detail": "Prodotto con id 99999 non trovato" }

# 3. GET con id negativo → 422 Unprocessable Entity (validazione Path)
curl -s -X GET "http://localhost:8000/api/v1/prodotti/-5"
# Output: errore di validazione (id deve essere > 0)

# 4. GET lista con filtri
curl -s -X GET "http://localhost:8000/api/v1/prodotti?categoria=elettronica&page=1&size=5"
# Output: lista paginata JSON
```

**Regole d\'oro per GET:**
1. Non includere MAI un body in una richiesta GET
2. Non modificare MAI dati in un handler GET — viola il vincolo "sicuro"
3. Usa query parameters per filtri e ordinamento, non path parameters
4. Dichiara Cache-Control nelle risposte che possono essere cacheggiabili

### POST — Creare (non idempotente)

**Status code di successo:** `201 Created` (non `200 OK`!)

**Quando usarlo:**
- Creare nuovo elemento: `POST /api/v1/prodotti`
- Login (crea token): `POST /api/v1/auth/login`
- Azioni/transizioni che non si mappano su CRUD: `POST /api/v1/ordini/42/conferma`
- Upload file: `POST /api/v1/prodotti/42/immagini`

**Perche POST non e idempotente:**
```
Primo POST /api/v1/prodotti con {"nome": "Laptop", "sku": "EL-001"}
→ Crea prodotto ID=1

Secondo POST /api/v1/prodotti con {"nome": "Laptop", "sku": "EL-001"}
→ Dipende dalla logica: errore 409 (se SKU univoco) O crea prodotto ID=2 (duplicato)

→ Il risultato e DIVERSO dalle due chiamate: non e idempotente
```

**Implementazione in FastAPI:**
```python
@router.post(
    "/",
    response_model=ProdottoResponse,
    status_code=201,
    summary="Crea un nuovo prodotto",
    responses={
        201: {"description": "Prodotto creato con successo"},
        409: {"description": "SKU gia esistente"},
        422: {"description": "Dati di input non validi"},
        401: {"description": "Non autenticato"},
    },
)
async def crea_prodotto(
    dati: ProdottoCreate,
    db: AsyncSession = Depends(get_db),
    utente: Utente = Depends(get_utente_corrente),
):
    # Verifica unicita SKU
    esistente = await db.execute(
        select(Prodotto).where(Prodotto.sku == dati.sku)
    )
    if esistente.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail=f"Prodotto con SKU '{dati.sku}' gia esistente",
        )

    prodotto = Prodotto(**dati.model_dump())
    db.add(prodotto)
    await db.flush()
    await db.refresh(prodotto)
    return prodotto
```

**Curl — tutti gli scenari:**
```bash
# 1. POST successo → 201 Created
curl -s -X POST "http://localhost:8000/api/v1/prodotti" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nome": "Laptop ProBook 450",
    "descrizione": "Intel i7, 16GB RAM, SSD 512GB",
    "prezzo": 999.99,
    "categoria": "elettronica",
    "sku": "EL-12345"
  }' | python -m json.tool
# Output: { "id": 1, "nome": "Laptop ProBook 450", ... }

# 2. POST con SKU duplicato → 409 Conflict
curl -s -X POST "http://localhost:8000/api/v1/prodotti" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"nome": "Altro Laptop", "prezzo": 799, "categoria": "elettronica", "sku": "EL-12345"}'
# Output: { "detail": "Prodotto con SKU 'EL-12345' gia esistente" }

# 3. POST con dati invalidi → 422 Unprocessable Entity
curl -s -X POST "http://localhost:8000/api/v1/prodotti" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"nome": "X", "prezzo": -100, "sku": "formato-errato"}'
# Output: lista dettagliata degli errori di validazione

# 4. POST senza autenticazione → 401 Unauthorized
curl -s -X POST "http://localhost:8000/api/v1/prodotti" \
  -H "Content-Type: application/json" \
  -d '{"nome": "Laptop", "prezzo": 999, "categoria": "elettronica", "sku": "EL-99999"}'
# Output: { "detail": "Not authenticated" }
```

### PUT — Sostituire Interamente (idempotente)

**Status code di successo:** `200 OK`

**Regola d\'oro:** PUT richiede TUTTI i campi della risorsa. I campi mancanti vengono
azzerati al loro valore di default.

**Differenza visiva PUT vs PATCH:**
```
Stato attuale del prodotto 42:
  nome: "Laptop ProBook 450"
  prezzo: 999.99
  categoria: "elettronica"
  disponibile: true
  descrizione: "Intel i7, RAM 16GB"

PUT con { "nome": "Laptop Elite", "prezzo": 1299.99 }
  → nome: "Laptop Elite"         ← cambiato
  → prezzo: 1299.99              ← cambiato
  → categoria: null              ← AZZERATO (non era nel body PUT)
  → disponibile: null            ← AZZERATO
  → descrizione: null            ← AZZERATO

PATCH con { "prezzo": 1299.99 }
  → nome: "Laptop ProBook 450"   ← INVARIATO
  → prezzo: 1299.99              ← cambiato
  → categoria: "elettronica"     ← INVARIATO
  → disponibile: true            ← INVARIATO
  → descrizione: "Intel i7..."   ← INVARIATO
```

**Implementazione:**
```python
@router.put(
    "/{prodotto_id}",
    response_model=ProdottoResponse,
    summary="Sostituisce interamente un prodotto",
)
async def sostituisci_prodotto(
    dati: ProdottoCreate,        # Tutti i campi OBBLIGATORI
    prodotto_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Prodotto).where(Prodotto.id == prodotto_id)
    )
    prodotto = result.scalar_one_or_none()
    if not prodotto:
        raise HTTPException(status_code=404, detail=f"Prodotto {prodotto_id} non trovato")

    # Aggiorna TUTTI i campi (nessuna eccezione)
    for campo, valore in dati.model_dump().items():
        setattr(prodotto, campo, valore)

    await db.flush()
    await db.refresh(prodotto)
    return prodotto
```

**Curl:**
```bash
# PUT — sostituzione completa (body completo obbligatorio)
curl -s -X PUT "http://localhost:8000/api/v1/prodotti/42" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nome": "Laptop ProBook 450 G10",
    "descrizione": "Modello 2026, Intel Core Ultra 7",
    "prezzo": 1199.99,
    "categoria": "elettronica",
    "sku": "EL-12345",
    "disponibile": true
  }'
# Output (200 OK): prodotto con tutti i campi aggiornati
```

### PATCH — Aggiornamento Parziale (preferito per update)

**Status code di successo:** `200 OK`

**Il segreto: `model_dump(exclude_unset=True)` in Pydantic v2**

```python
# Schema per PATCH: TUTTI i campi opzionali
class ProdottoUpdate(BaseModel):
    nome: str | None = None
    descrizione: str | None = None
    prezzo: Decimal | None = None
    categoria: str | None = None
    disponibile: bool | None = None

# Quando il client invia {"prezzo": 799.99}:
dati = ProdottoUpdate.model_validate({"prezzo": 799.99})

# CON model_dump() — SBAGLIATO per PATCH:
dati.model_dump()
# → {"nome": None, "descrizione": None, "prezzo": 799.99, "categoria": None, "disponibile": None}
# Sovrascrive tutti i campi con None!

# CON model_dump(exclude_unset=True) — CORRETTO per PATCH:
dati.model_dump(exclude_unset=True)
# → {"prezzo": 799.99}
# Solo il campo effettivamente inviato dal client!
```

**Implementazione:**
```python
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
    result = await db.execute(
        select(Prodotto).where(Prodotto.id == prodotto_id)
    )
    prodotto = result.scalar_one_or_none()
    if not prodotto:
        raise HTTPException(status_code=404, detail=f"Prodotto {prodotto_id} non trovato")

    # exclude_unset=True: aggiorna SOLO i campi presenti nella richiesta
    for campo, valore in dati.model_dump(exclude_unset=True).items():
        setattr(prodotto, campo, valore)

    await db.flush()
    await db.refresh(prodotto)
    return prodotto
```

**Curl:**
```bash
# PATCH — aggiorna solo il prezzo
curl -s -X PATCH "http://localhost:8000/api/v1/prodotti/42" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"prezzo": 799.99}'
# Output: prodotto con solo il prezzo cambiato, tutto il resto invariato

# PATCH — disabilita il prodotto
curl -s -X PATCH "http://localhost:8000/api/v1/prodotti/42" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"disponibile": false}'

# PATCH — aggiorna nome e descrizione contemporaneamente
curl -s -X PATCH "http://localhost:8000/api/v1/prodotti/42" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"nome": "Laptop ProBook 450 PREMIUM", "descrizione": "Edizione speciale 2026"}'
```

### DELETE — Eliminare (idempotente)

**Status code di successo:** `204 No Content` — nessun body nella risposta!

**Perche 204 e non 200:** Il codice 204 segnala esplicitamente "operazione riuscita,
ma non c\'e niente da restituire". Distingue da 200 (operazione riuscita con dati)
e da 404 (risorsa non trovata). I client ben scritti non si aspettano body con 204.

**Idempotenza del DELETE:**
```
Prima chiamata: DELETE /api/v1/prodotti/42
→ Prodotto 42 eliminato → 204 No Content

Seconda chiamata: DELETE /api/v1/prodotti/42
→ Prodotto 42 non esiste piu
→ Comportamento 1 (stricto): 404 Not Found
→ Comportamento 2 (idempotente): 204 No Content (gia eliminato = stesso risultato finale)
```
La scelta dipende dal design. Per operazioni idempotenti pure, restituisci sempre 204.

**Soft delete vs hard delete:**
```python
# Hard delete: elimina fisicamente il record
async def hard_delete(id: int, db: AsyncSession):
    prodotto = await db.get(Prodotto, id)
    await db.delete(prodotto)

# Soft delete: marca come eliminato (preferito per dati importanti)
async def soft_delete(id: int, db: AsyncSession):
    prodotto = await db.get(Prodotto, id)
    prodotto.eliminato_il = datetime.now(timezone.utc)
    # Il record rimane nel DB, ma e invisibile alle query normali
    # SELECT * FROM prodotti WHERE eliminato_il IS NULL
```

**Implementazione:**
```python
@router.delete(
    "/{prodotto_id}",
    status_code=204,
    summary="Elimina un prodotto",
    responses={
        204: {"description": "Prodotto eliminato con successo"},
        404: {"description": "Prodotto non trovato"},
    },
)
async def elimina_prodotto(
    prodotto_id: int = Path(..., gt=0),
    db: AsyncSession = Depends(get_db),
    utente: Utente = Depends(richiedi_ruolo("admin")),
):
    result = await db.execute(
        select(Prodotto).where(Prodotto.id == prodotto_id)
    )
    prodotto = result.scalar_one_or_none()

    if not prodotto:
        raise HTTPException(
            status_code=404,
            detail=f"Prodotto {prodotto_id} non trovato",
        )

    await db.delete(prodotto)
    # NESSUN return → FastAPI risponde automaticamente 204 No Content
```

**Curl:**
```bash
# DELETE — elimina prodotto → 204 No Content
curl -s -o /dev/null -w "%{http_code}" \
  -X DELETE "http://localhost:8000/api/v1/prodotti/42" \
  -H "Authorization: Bearer $TOKEN"
# Output: 204

# Verifica eliminazione → 404 Not Found
curl -s -X GET "http://localhost:8000/api/v1/prodotti/42"
# Output: { "detail": "Prodotto 42 non trovato" }

# DELETE senza autorizzazione admin → 403 Forbidden
curl -s -X DELETE "http://localhost:8000/api/v1/prodotti/42" \
  -H "Authorization: Bearer $TOKEN_UTENTE_NORMALE"
# Output: { "detail": "Ruolo 'utente' non autorizzato. Ruoli richiesti: admin" }
```

### Tabella Riassuntiva Metodi HTTP

| Metodo | Semantica | Idempotente | Sicuro | Status OK | Body req | Body resp |
|--------|-----------|-------------|--------|-----------|----------|-----------|
| GET | Leggi | SI | SI | 200 OK | NO | SI |
| POST | Crea | NO | NO | 201 Created | SI | SI |
| PUT | Sostituisci tutto | SI | NO | 200 OK | SI | SI |
| PATCH | Aggiorna parte | NO* | NO | 200 OK | SI | SI |
| DELETE | Elimina | SI | NO | 204 No Content | NO | NO |

*PATCH puo essere reso idempotente con idempotency keys (vedere Parte D).

### I 5 Errori piu Comuni con i Metodi HTTP

**Errore 1 — Verbi negli URL:**
```
# SBAGLIATO (stile RPC):
POST /api/v1/getProdotti
POST /api/v1/creaProdotto
GET  /api/v1/prodotti/42/update
POST /api/v1/eliminaProdotto?id=42

# CORRETTO (stile REST):
GET    /api/v1/prodotti
POST   /api/v1/prodotti
PATCH  /api/v1/prodotti/42
DELETE /api/v1/prodotti/42
```

**Errore 2 — Status code sbagliato:**
```python
# SBAGLIATO: 200 per creazione
@router.post("/prodotti")
async def crea_prodotto(dati: ProdottoCreate):
    prodotto = Prodotto(**dati.model_dump())
    return prodotto    # restituisce 200 di default — SBAGLIATO

# CORRETTO: 201 per creazione
@router.post("/prodotti", status_code=201)
async def crea_prodotto(dati: ProdottoCreate):
    prodotto = Prodotto(**dati.model_dump())
    return prodotto    # restituisce 201 Created — CORRETTO
```

**Errore 3 — Body nel DELETE:**
```python
# SBAGLIATO: DELETE con body
@router.delete("/{id}")
async def elimina(id: int):
    await rimuovi_dal_db(id)
    return {"messaggio": "eliminato", "id": id}   # 200 con body

# CORRETTO: 204 No Content
@router.delete("/{id}", status_code=204)
async def elimina(id: int):
    await rimuovi_dal_db(id)
    # Nessun return
```

**Errore 4 — PATCH senza exclude_unset:**
```python
# SBAGLIATO: aggiorna tutti i campi compresi None
@router.patch("/{id}")
async def update(dati: ProdottoUpdate, id: int):
    for campo, valore in dati.model_dump().items():   # include None!
        setattr(prodotto, campo, valore)               # azzera campi non forniti

# CORRETTO: aggiorna solo i campi forniti
@router.patch("/{id}")
async def update(dati: ProdottoUpdate, id: int):
    for campo, valore in dati.model_dump(exclude_unset=True).items():
        setattr(prodotto, campo, valore)
```

**Errore 5 — GET che modifica dati:**
```python
# SBAGLIATO: GET con side effect
@router.get("/{id}")
async def vedi_prodotto(id: int, db: AsyncSession = Depends(get_db)):
    prodotto = await db.get(Prodotto, id)
    prodotto.views += 1    # VIOLA il vincolo "sicuro" di GET!
    await db.commit()
    return prodotto

# CORRETTO: side effect in background task
@router.get("/{id}")
async def vedi_prodotto(
    id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    prodotto = await db.get(Prodotto, id)
    # Il contatore si aggiorna DOPO la risposta, non blocca il client
    background_tasks.add_task(incrementa_views, id)
    return prodotto
```

