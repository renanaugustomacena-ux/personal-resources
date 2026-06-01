---
corso: "Automazioni e Flussi di Lavoro"
fase: "2 — Scripting e Integrazione"
modulo: 4
titolo: "Integrazione API"
versione: "1.0"
livello: "Avanzato"
prerequisiti:
  - "Moduli 01-03"
  - "HTTP/REST/JSON, status code, methods, headers"
obiettivi:
  - "Implementare pattern di autenticazione API (API key, OAuth 2.0, JWT, mTLS)"
  - "Gestire rate limit con backoff esponenziale e circuit breaker"
  - "Progettare integrazione con pagination cursor-based e gestione stato"
  - "Confrontare webhook vs polling e scegliere in base al contesto"
  - "Applicare contract testing e validazione OpenAPI per integrazioni affidabili"
tag: [api, rest, oauth, jwt, webhook, rate-limit, integrazione, contract-testing]
---

# Integrazione API — Guida Completa

> **Modulo del corso:** Automazioni e Flussi di Lavoro
> **Posizione:** Fase 2 — API & integrazione · Modulo 04
> **Prerequisiti:** Modulo 01-03; HTTP/REST/JSON, status code, methods, headers.
> **Obiettivi:** auth pattern (API key, OAuth, JWT, mTLS); rate limit + backoff; pagination; webhook vs polling; testing API.
> **Tempo:** lettura 90-120 min · lab 240 min
> **Livello:** competent → proficient
> **Ultimo aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Implementare pattern di autenticazione API (API key, OAuth 2.0, JWT, mTLS)
> 2. Gestire rate limit con backoff esponenziale e circuit breaker
> 3. Progettare integrazione con pagination cursor-based e gestione stato
> 4. Confrontare webhook vs polling e scegliere in base al contesto
> 5. Applicare contract testing e validazione OpenAPI per integrazioni affidabili
>
> **Prerequisiti:** [Modulo 01](01-fondamenti-automazione.md), [Modulo 02](02-piattaforme-low-code.md), [Modulo 03](03-scripting-automazione.md) -- HTTP/REST/JSON, status code, methods, headers
> **Tempo stimato:** 5-6 ore · **Livello:** Avanzato

## Idee guida

1. **Webhook > polling 90% delle volte.** Polling costa banda, latenza, rate limit. Webhook arriva quando serve.
2. **Rate limit non e errore: e segnale.** 429 + Retry-After = backoff esponenziale, non ignore.
3. **Pagination breakable: cursor-based >> offset-based.** Offset si rompe se i dati cambiano fra pagine.
4. **API key in header, mai in URL.** URL finiscono nei log, nei browser history, nei referer.
5. **Test contro sandbox/mock, non prod.** Production data e prezioso; sandbox e gratis.

---

## Indice

1. [Panoramica](#panoramica)
2. [Fondamenti REST API](#fondamenti-rest-api)
   - [Metodi HTTP](#metodi-http)
   - [Struttura Request/Response](#struttura-requestresponse)
   - [Autenticazione API](#autenticazione-api)
   - [Paginazione](#paginazione)
   - [Rate Limiting](#rate-limiting)
3. [GraphQL](#graphql)
   - [Fondamenti](#fondamenti)
   - [Query Pratiche](#query-pratiche)
   - [Strumenti GraphQL](#strumenti-graphql)
4. [Webhook](#webhook)
   - [Architettura](#architettura)
   - [Implementazione Receiver](#implementazione-receiver)
   - [Webhook Comuni](#webhook-comuni)
5. [API Comuni per IT Automation](#api-comuni-per-it-automation)
   - [Microsoft Graph API](#microsoft-graph-api)
   - [Jira/Atlassian API](#jiraatlassian-api)
   - [Slack API](#slack-api)
   - [ServiceNow API](#servicenow-api)
6. [Progettazione Integrazioni Robuste](#progettazione-integrazioni-robuste)
7. [Strumenti](#strumenti)
8. [Best Practices](#best-practices)

---

## Panoramica

Le API (Application Programming Interface) rappresentano la spina dorsale dell'automazione moderna. Ogni volta che un sistema deve comunicare con un altro — che si tratti di recuperare dati da un database remoto, inviare una notifica, creare un ticket o sincronizzare informazioni tra piattaforme — lo fa attraverso un'API. Senza API, l'automazione sarebbe limitata a operazioni locali su una singola macchina, e l'intero ecosistema di servizi cloud, piattaforme SaaS e microservizi semplicemente non potrebbe esistere.

Nel contesto dell'automazione IT, le API permettono di orchestrare processi complessi che attraversano decine di sistemi diversi. Un singolo flusso di lavoro automatizzato potrebbe interrogare un CMDB per ottenere informazioni su un server, aprire un ticket su Jira, inviare una notifica su Slack, eseguire un playbook Ansible e aggiornare un dashboard Grafana — tutto attraverso chiamate API.

### Tipologie di API

**REST (Representational State Transfer)** è lo standard de facto per le API web. Si basa sul protocollo HTTP e utilizza risorse identificate da URL, con operazioni espresse tramite i metodi HTTP standard. La sua semplicità e la vasta adozione lo rendono la scelta predefinita per la maggior parte delle integrazioni.

**GraphQL** è un linguaggio di query per API sviluppato da Facebook. A differenza di REST, dove ogni endpoint restituisce una struttura dati fissa, GraphQL permette al client di specificare esattamente quali dati desidera ricevere. Questo elimina il problema dell'over-fetching (ricevere più dati del necessario) e dell'under-fetching (dover fare più chiamate per ottenere tutti i dati).

**SOAP (Simple Object Access Protocol)** è un protocollo più anziano, basato su XML, ancora diffuso in ambito enterprise e nei sistemi legacy. Offre un sistema di tipizzazione rigoroso tramite WSDL (Web Services Description Language) e supporta funzionalità avanzate come transazioni e sicurezza a livello di messaggio (WS-Security). Sebbene più complesso di REST, rimane necessario quando si integrano sistemi bancari, governativi o ERP datati.

**gRPC (Google Remote Procedure Call)** utilizza Protocol Buffers per la serializzazione dei dati ed HTTP/2 per il trasporto. Offre prestazioni superiori rispetto a REST grazie alla serializzazione binaria, supporto nativo per lo streaming bidirezionale e generazione automatica del codice client. È la scelta preferita per la comunicazione tra microservizi ad alte prestazioni.

Per l'automazione IT quotidiana, REST e webhook coprono la stragrande maggioranza dei casi d'uso. GraphQL sta guadagnando terreno, specialmente nelle API di GitHub e Shopify. SOAP si incontra ancora nei sistemi enterprise legacy, mentre gRPC è più comune nelle architetture a microservizi interne.

---

## Fondamenti REST API

REST è un'architettura basata su risorse. Ogni risorsa (un utente, un ticket, un server) è identificata da un URL univoco, e le operazioni su di essa sono espresse tramite i metodi HTTP standard. Questa semplicità concettuale è ciò che rende REST così potente e diffuso.

### Metodi HTTP

I metodi HTTP definiscono il tipo di operazione da eseguire su una risorsa.

**GET** — Recupera una risorsa o un elenco di risorse. Non deve mai modificare lo stato del server. È idempotente: chiamarlo più volte produce sempre lo stesso risultato.

```http
GET /api/v1/users/42 HTTP/1.1
Host: api.example.com
Accept: application/json
```

Casi d'uso: recuperare il profilo di un utente, elencare i ticket aperti, ottenere lo stato di un server.

**POST** — Crea una nuova risorsa. Non è idempotente: ogni chiamata potrebbe creare una risorsa diversa.

```http
POST /api/v1/users HTTP/1.1
Host: api.example.com
Content-Type: application/json

{
  "nome": "Mario Rossi",
  "email": "mario.rossi@example.com",
  "ruolo": "operatore"
}
```

Casi d'uso: creare un nuovo utente, aprire un ticket, avviare un processo.

**PUT** — Sostituisce interamente una risorsa esistente. È idempotente: inviare la stessa richiesta più volte produce lo stesso stato finale.

```http
PUT /api/v1/users/42 HTTP/1.1
Host: api.example.com
Content-Type: application/json

{
  "nome": "Mario Rossi",
  "email": "mario.rossi@nuovodominio.com",
  "ruolo": "amministratore"
}
```

Casi d'uso: aggiornare completamente il profilo di un utente, sostituire una configurazione.

**PATCH** — Modifica parzialmente una risorsa esistente. È generalmente idempotente, anche se l'implementazione può variare.

```http
PATCH /api/v1/users/42 HTTP/1.1
Host: api.example.com
Content-Type: application/json

{
  "ruolo": "amministratore"
}
```

Casi d'uso: aggiornare un singolo campo, cambiare lo stato di un ticket.

**DELETE** — Elimina una risorsa. È idempotente: eliminare una risorsa già eliminata non produce errori (idealmente restituisce 204 o 404).

```http
DELETE /api/v1/users/42 HTTP/1.1
Host: api.example.com
```

Casi d'uso: eliminare un utente, chiudere un ticket, rimuovere una configurazione.

**Idempotenza** — Un'operazione è idempotente quando eseguirla più volte produce lo stesso risultato della singola esecuzione. GET, PUT, PATCH e DELETE sono idempotenti per design. POST non lo è. Questa distinzione è fondamentale per l'automazione: se un'operazione idempotente fallisce a metà, è possibile ripeterla senza rischi. Per POST, è necessario implementare meccanismi di deduplica come le idempotency key.

### Struttura Request/Response

#### Header

Gli header HTTP trasportano metadati essenziali per la comunicazione tra client e server.

**Content-Type** specifica il formato del corpo della richiesta:
- `application/json` — formato standard per le API REST moderne
- `application/x-www-form-urlencoded` — dati di form HTML
- `multipart/form-data` — upload di file
- `application/xml` — per API SOAP o legacy

**Authorization** contiene le credenziali di autenticazione:
- `Authorization: Bearer eyJhbGciOiJSUzI1NiIs...` — token JWT o OAuth
- `Authorization: Basic dXNlcjpwYXNz` — Basic Auth (base64 di user:password)
- `X-API-Key: abc123def456` — chiave API (header personalizzato)

**Accept** indica al server quale formato di risposta il client preferisce:
- `Accept: application/json`
- `Accept: application/xml`
- `Accept: text/plain`

Altri header comuni nell'automazione:
- `User-Agent` — identifica il client (utile per il debug)
- `X-Request-ID` — identificativo univoco della richiesta (fondamentale per il tracciamento)
- `If-None-Match` / `ETag` — caching condizionale

#### Codici di Stato HTTP

I codici di stato comunicano il risultato di una richiesta. Conoscerli è essenziale per gestire correttamente le risposte nelle automazioni.

**2xx — Successo**
- `200 OK` — richiesta completata con successo (risposta con corpo)
- `201 Created` — risorsa creata con successo (tipicamente dopo POST)
- `202 Accepted` — richiesta accettata ma non ancora completata (operazioni asincrone)
- `204 No Content` — successo senza corpo nella risposta (tipicamente dopo DELETE)

**3xx — Reindirizzamento**
- `301 Moved Permanently` — la risorsa è stata spostata permanentemente
- `302 Found` — reindirizzamento temporaneo
- `304 Not Modified` — la risorsa non è cambiata (caching con ETag)

**4xx — Errore del Client**
- `400 Bad Request` — la richiesta è malformata o contiene dati non validi
- `401 Unauthorized` — autenticazione mancante o non valida
- `403 Forbidden` — autenticato ma non autorizzato per questa operazione
- `404 Not Found` — la risorsa richiesta non esiste
- `409 Conflict` — conflitto con lo stato attuale della risorsa
- `422 Unprocessable Entity` — dati sintatticamente corretti ma semanticamente non validi
- `429 Too Many Requests` — superato il rate limit

**5xx — Errore del Server**
- `500 Internal Server Error` — errore generico del server
- `502 Bad Gateway` — il server upstream ha restituito una risposta non valida
- `503 Service Unavailable` — servizio temporaneamente non disponibile
- `504 Gateway Timeout` — il server upstream non ha risposto in tempo

Per l'automazione, la distinzione chiave è: gli errori 4xx indicano un problema nella richiesta (da correggere nel codice), mentre gli errori 5xx e 429 indicano problemi temporanei (da gestire con retry).

#### Query Parameters vs Path Parameters

I **path parameters** identificano una risorsa specifica e fanno parte dell'URL:

```
GET /api/v1/projects/42/issues/7
              ^^^^^^^^^^^^^^^^^^^^
              path parameters: project_id=42, issue_id=7
```

I **query parameters** filtrano, ordinano o paginano i risultati e vengono aggiunti dopo il `?`:

```
GET /api/v1/issues?status=open&priority=high&page=2&per_page=50
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                   query parameters
```

Regola generale: usare path parameters per l'identificazione della risorsa e query parameters per operazioni di filtraggio, ordinamento e paginazione.

### Autenticazione API

L'autenticazione è il primo ostacolo da superare quando si integra un'API. Ogni servizio può adottare meccanismi diversi, ma le strategie fondamentali sono poche.

#### API Key

Il metodo più semplice: una stringa segreta che identifica il client. Può essere passata come header o come query parameter.

```python
import requests

# API Key nell'header (metodo preferito)
headers = {
    "X-API-Key": "la-tua-chiave-segreta",
    "Content-Type": "application/json"
}
response = requests.get("https://api.example.com/v1/data", headers=headers)

# API Key come query parameter (meno sicuro, visibile nei log)
response = requests.get(
    "https://api.example.com/v1/data",
    params={"api_key": "la-tua-chiave-segreta"}
)
```

Vantaggi: semplicità. Svantaggi: nessun meccanismo di scadenza o rotazione automatica, e se la chiave viene compromessa bisogna rigenerarla manualmente.

#### Basic Auth

Trasmette username e password codificati in Base64 nell'header Authorization. Semplice ma meno sicuro: le credenziali viaggiano ad ogni richiesta.

```python
import requests
from requests.auth import HTTPBasicAuth

response = requests.get(
    "https://api.example.com/v1/data",
    auth=HTTPBasicAuth("utente", "password")
)
```

Utilizzato ancora da Jira Server, Jenkins e altri strumenti enterprise on-premise.

#### Bearer Token / JWT

Un token (spesso JWT — JSON Web Token) viene ottenuto tramite un processo di autenticazione iniziale e poi utilizzato per le richieste successive.

Un JWT è composto da tre parti separate da punti:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6Ik1hcmlvIiwiaWF0IjoxNTE2MjM5MDIyfQ.
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c

[HEADER].[PAYLOAD].[SIGNATURE]
```

- **Header**: algoritmo di firma e tipo di token
- **Payload**: claims (dati) come `sub` (soggetto), `exp` (scadenza), `iat` (emissione), più claims personalizzati
- **Signature**: firma crittografica per verificare l'integrità

Il flusso di refresh token è fondamentale per le automazioni di lunga durata:

```python
import requests
import time

class APIClient:
    def __init__(self, base_url, client_id, client_secret):
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expiry = 0

    def _get_token(self):
        """Ottiene o rinnova il token di accesso."""
        response = requests.post(
            f"{self.base_url}/oauth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
        )
        response.raise_for_status()
        data = response.json()
        self.access_token = data["access_token"]
        # Rinnova 60 secondi prima della scadenza effettiva
        self.token_expiry = time.time() + data["expires_in"] - 60

    def _ensure_token(self):
        """Verifica che il token sia valido, altrimenti lo rinnova."""
        if not self.access_token or time.time() >= self.token_expiry:
            self._get_token()

    def request(self, method, endpoint, **kwargs):
        """Esegue una richiesta autenticata con refresh automatico."""
        self._ensure_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self.access_token}"
        response = requests.request(
            method,
            f"{self.base_url}{endpoint}",
            headers=headers,
            **kwargs
        )
        # Se il token è scaduto, rinnova e riprova
        if response.status_code == 401:
            self._get_token()
            headers["Authorization"] = f"Bearer {self.access_token}"
            response = requests.request(
                method,
                f"{self.base_url}{endpoint}",
                headers=headers,
                **kwargs
            )
        return response
```

#### OAuth 2.0

OAuth 2.0 è lo standard per l'autorizzazione delegata. Permette a un'applicazione di accedere alle risorse di un utente su un altro servizio senza conoscerne le credenziali.

**Authorization Code Flow** — il flusso più sicuro, per applicazioni web con backend:

1. L'applicazione reindirizza l'utente al provider (es. Google, Microsoft)
2. L'utente approva l'accesso
3. Il provider reindirizza al callback URL con un authorization code
4. L'applicazione scambia il code per un access token (server-to-server)
5. L'access token viene usato per le chiamate API

**Client Credentials Flow** — per comunicazione machine-to-machine senza intervento utente:

```python
import requests

def get_m2m_token(token_url, client_id, client_secret, scope):
    """Ottiene un token con Client Credentials Flow (machine-to-machine)."""
    response = requests.post(
        token_url,
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": scope,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    response.raise_for_status()
    return response.json()["access_token"]

# Esempio: Microsoft Graph API
token = get_m2m_token(
    token_url="https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token",
    client_id="il-tuo-client-id",
    client_secret="il-tuo-client-secret",
    scope="https://graph.microsoft.com/.default"
)
```

**PKCE (Proof Key for Code Exchange)** — estensione dell'Authorization Code Flow per applicazioni native o SPA dove il client secret non può essere tenuto al sicuro:

```python
import hashlib
import base64
import secrets

# 1. Genera il code_verifier (stringa casuale)
code_verifier = secrets.token_urlsafe(64)

# 2. Calcola il code_challenge (hash SHA-256 del verifier)
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b"=").decode()

# 3. Invia il code_challenge nella richiesta di autorizzazione
auth_url = (
    f"https://provider.com/authorize"
    f"?client_id={client_id}"
    f"&response_type=code"
    f"&redirect_uri={redirect_uri}"
    f"&code_challenge={code_challenge}"
    f"&code_challenge_method=S256"
    f"&scope=openid profile email"
)

# 4. Dopo il redirect, scambia il code per il token includendo il verifier
token_response = requests.post(
    "https://provider.com/token",
    data={
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "code_verifier": code_verifier,
    }
)
```

#### Esempio Completo: Implementazione OAuth 2.0

```python
"""
Implementazione completa di un client OAuth 2.0 con supporto per
Authorization Code Flow e refresh automatico dei token.
"""
import requests
import time
import json
from pathlib import Path
from urllib.parse import urlencode


class OAuth2Client:
    def __init__(self, provider_config, token_storage_path="tokens.json"):
        self.auth_url = provider_config["auth_url"]
        self.token_url = provider_config["token_url"]
        self.client_id = provider_config["client_id"]
        self.client_secret = provider_config["client_secret"]
        self.redirect_uri = provider_config["redirect_uri"]
        self.scope = provider_config["scope"]
        self.token_storage = Path(token_storage_path)
        self.tokens = self._load_tokens()

    def _load_tokens(self):
        """Carica i token salvati su disco."""
        if self.token_storage.exists():
            return json.loads(self.token_storage.read_text())
        return {}

    def _save_tokens(self):
        """Salva i token su disco per persistenza tra le esecuzioni."""
        self.token_storage.write_text(json.dumps(self.tokens, indent=2))

    def get_authorization_url(self, state=None):
        """Genera l'URL per il consenso dell'utente."""
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": self.scope,
        }
        if state:
            params["state"] = state
        return f"{self.auth_url}?{urlencode(params)}"

    def exchange_code(self, authorization_code):
        """Scambia l'authorization code per access e refresh token."""
        response = requests.post(
            self.token_url,
            data={
                "grant_type": "authorization_code",
                "code": authorization_code,
                "redirect_uri": self.redirect_uri,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
        )
        response.raise_for_status()
        self.tokens = response.json()
        self.tokens["obtained_at"] = time.time()
        self._save_tokens()
        return self.tokens

    def refresh_access_token(self):
        """Rinnova l'access token usando il refresh token."""
        if "refresh_token" not in self.tokens:
            raise ValueError("Nessun refresh token disponibile. Riautenticare.")

        response = requests.post(
            self.token_url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.tokens["refresh_token"],
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            }
        )
        response.raise_for_status()
        new_tokens = response.json()
        # Alcuni provider restituiscono un nuovo refresh token, altri no
        if "refresh_token" not in new_tokens:
            new_tokens["refresh_token"] = self.tokens["refresh_token"]
        self.tokens = new_tokens
        self.tokens["obtained_at"] = time.time()
        self._save_tokens()
        return self.tokens

    def get_valid_token(self):
        """Restituisce un access token valido, rinnovandolo se necessario."""
        if not self.tokens.get("access_token"):
            raise ValueError("Nessun token disponibile. Eseguire autenticazione.")

        expires_in = self.tokens.get("expires_in", 3600)
        obtained_at = self.tokens.get("obtained_at", 0)
        # Rinnova 120 secondi prima della scadenza
        if time.time() >= obtained_at + expires_in - 120:
            self.refresh_access_token()

        return self.tokens["access_token"]

    def authenticated_request(self, method, url, **kwargs):
        """Esegue una richiesta HTTP autenticata con gestione automatica dei token."""
        token = self.get_valid_token()
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"

        response = requests.request(method, url, headers=headers, **kwargs)

        if response.status_code == 401:
            self.refresh_access_token()
            token = self.tokens["access_token"]
            headers["Authorization"] = f"Bearer {token}"
            response = requests.request(method, url, headers=headers, **kwargs)

        return response
```

### Paginazione

Quando un'API restituisce potenzialmente migliaia di risultati, la paginazione divide la risposta in pagine gestibili. Gestire correttamente la paginazione è fondamentale per le automazioni che devono elaborare grandi volumi di dati.

#### Paginazione Offset-Based

Il metodo più comune e intuitivo. Si specifica un offset (da dove iniziare) e un limit (quanti elementi per pagina).

```python
def fetch_all_offset_based(base_url, headers, per_page=100):
    """Recupera tutti i risultati con paginazione offset-based."""
    all_results = []
    page = 1

    while True:
        response = requests.get(
            base_url,
            headers=headers,
            params={"page": page, "per_page": per_page}
        )
        response.raise_for_status()
        data = response.json()

        if not data["results"]:
            break

        all_results.extend(data["results"])

        # Controlla se ci sono altre pagine
        if page * per_page >= data.get("total_count", 0):
            break

        page += 1

    return all_results
```

Svantaggio: se i dati vengono inseriti o eliminati tra una pagina e l'altra, è possibile saltare elementi o riceverne di duplicati.

#### Paginazione Cursor-Based

Utilizza un cursore opaco (spesso un ID o un timestamp codificato) per indicare la posizione corrente. Più affidabile della paginazione offset in presenza di dati che cambiano frequentemente.

```python
def fetch_all_cursor_based(base_url, headers, per_page=100):
    """Recupera tutti i risultati con paginazione cursor-based."""
    all_results = []
    cursor = None

    while True:
        params = {"limit": per_page}
        if cursor:
            params["cursor"] = cursor

        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        all_results.extend(data["results"])

        # Il cursore per la pagina successiva
        cursor = data.get("next_cursor")
        if not cursor:
            break

    return all_results
```

#### Paginazione Link Header

Alcune API (GitHub, per esempio) utilizzano l'header `Link` nella risposta per indicare gli URL delle pagine successive, precedenti, prima e ultima.

```
Link: <https://api.github.com/repos/org/repo/issues?page=2>; rel="next",
      <https://api.github.com/repos/org/repo/issues?page=14>; rel="last"
```

```python
import re

def fetch_all_link_header(url, headers):
    """Recupera tutti i risultati seguendo gli header Link."""
    all_results = []

    while url:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        all_results.extend(response.json())

        # Estrai l'URL della pagina successiva dall'header Link
        link_header = response.headers.get("Link", "")
        url = None
        for part in link_header.split(","):
            if 'rel="next"' in part:
                match = re.search(r'<(.+?)>', part)
                if match:
                    url = match.group(1)

    return all_results
```

### Rate Limiting

Ogni API impone limiti sul numero di richieste consentite in un intervallo di tempo. Superare questi limiti provoca errori `429 Too Many Requests` e, in casi estremi, il blocco temporaneo dell'accesso. Per le automazioni che elaborano grandi volumi di dati, la gestione del rate limiting è indispensabile.

#### Comprendere i Rate Limit

La maggior parte delle API comunica i limiti tramite header nella risposta:

```
X-RateLimit-Limit: 5000          # Richieste massime nel periodo
X-RateLimit-Remaining: 4987      # Richieste rimanenti
X-RateLimit-Reset: 1709312400    # Timestamp UNIX del reset
Retry-After: 60                  # Secondi da attendere (su 429)
```

#### Strategia di Retry con Exponential Backoff e Jitter

L'exponential backoff è la strategia standard per gestire errori temporanei e rate limiting. Il jitter (componente casuale) previene il problema del "thundering herd" quando più client riprovano simultaneamente.

```python
import time
import random
import requests
from functools import wraps


def retry_with_backoff(
    max_retries=5,
    base_delay=1.0,
    max_delay=60.0,
    retryable_statuses=(429, 500, 502, 503, 504),
):
    """
    Decoratore per retry con exponential backoff e jitter.

    Args:
        max_retries: numero massimo di tentativi
        base_delay: ritardo iniziale in secondi
        max_delay: ritardo massimo in secondi
        retryable_statuses: codici di stato HTTP da considerare recuperabili
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    response = func(*args, **kwargs)

                    if response.status_code not in retryable_statuses:
                        return response

                    if attempt == max_retries:
                        return response

                    # Usa Retry-After se disponibile
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        delay = float(retry_after)
                    else:
                        # Exponential backoff con jitter
                        delay = min(base_delay * (2 ** attempt), max_delay)
                        delay = delay * (0.5 + random.random())

                    print(
                        f"[Retry] Tentativo {attempt + 1}/{max_retries}, "
                        f"status={response.status_code}, "
                        f"attesa={delay:.1f}s"
                    )
                    time.sleep(delay)

                except requests.exceptions.ConnectionError as e:
                    last_exception = e
                    if attempt == max_retries:
                        raise
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    delay = delay * (0.5 + random.random())
                    print(
                        f"[Retry] Errore di connessione, tentativo {attempt + 1}, "
                        f"attesa={delay:.1f}s"
                    )
                    time.sleep(delay)

            raise last_exception or Exception("Numero massimo di retry raggiunto")

        return wrapper
    return decorator


@retry_with_backoff(max_retries=5, base_delay=1.0)
def api_call(url, headers):
    return requests.get(url, headers=headers)


class RateLimitHandler:
    """Gestore proattivo del rate limiting basato sugli header della risposta."""

    def __init__(self, safety_margin=0.1):
        self.safety_margin = safety_margin  # 10% di margine di sicurezza

    def check_and_wait(self, response):
        """Controlla i limiti e attende se necessario prima di procedere."""
        remaining = response.headers.get("X-RateLimit-Remaining")
        limit = response.headers.get("X-RateLimit-Limit")
        reset = response.headers.get("X-RateLimit-Reset")

        if remaining is None or reset is None:
            return

        remaining = int(remaining)
        limit = int(limit) if limit else 1000
        reset_time = int(reset)

        # Se abbiamo usato più del 90% del budget, rallenta
        threshold = int(limit * self.safety_margin)
        if remaining <= threshold:
            wait_seconds = max(0, reset_time - time.time()) + 1
            print(
                f"[RateLimit] Rimanenti: {remaining}/{limit}. "
                f"Attesa di {wait_seconds:.0f}s fino al reset."
            )
            time.sleep(wait_seconds)
```

---

## GraphQL

### Fondamenti

GraphQL è un linguaggio di query per API che offre un'alternativa potente e flessibile a REST. Invece di endpoint multipli che restituiscono strutture dati fisse, GraphQL espone un singolo endpoint attraverso il quale il client può richiedere esattamente i dati di cui ha bisogno.

**Schema** — Lo schema GraphQL definisce i tipi di dati disponibili, le relazioni tra di essi e le operazioni possibili. È il contratto tra client e server.

```graphql
type User {
  id: ID!
  nome: String!
  email: String!
  ruolo: String!
  tickets: [Ticket!]!
}

type Ticket {
  id: ID!
  titolo: String!
  stato: String!
  priorita: String!
  assegnato: User
  creato_il: DateTime!
}

type Query {
  user(id: ID!): User
  users(ruolo: String, limit: Int): [User!]!
  ticket(id: ID!): Ticket
  tickets(stato: String, priorita: String): [Ticket!]!
}

type Mutation {
  createTicket(input: CreateTicketInput!): Ticket!
  updateTicketStato(id: ID!, stato: String!): Ticket!
}
```

**Query** — Le query leggono dati. Il client specifica esattamente quali campi vuole ricevere.

**Mutation** — Le mutation modificano dati (equivalente di POST, PUT, PATCH, DELETE in REST).

**Subscription** — Le subscription permettono al client di ricevere aggiornamenti in tempo reale quando i dati cambiano (via WebSocket).

**Vantaggi rispetto a REST:**
- Nessun over-fetching: si ricevono solo i campi richiesti
- Nessun under-fetching: dati correlati possono essere ottenuti in una singola query
- Schema fortemente tipizzato con documentazione intrinseca
- Introspection: il client può interrogare lo schema stesso per scoprire le API disponibili

**Introspection** — GraphQL permette di interrogare lo schema per scoprire tipi, campi e operazioni disponibili:

```graphql
{
  __schema {
    types {
      name
      description
      fields {
        name
        type { name }
      }
    }
  }
}
```

### Query Pratiche

#### Query Base con Variabili

```graphql
# Query con variabili per recuperare un utente e i suoi ticket
query GetUserWithTickets($userId: ID!, $ticketStatus: String) {
  user(id: $userId) {
    nome
    email
    tickets(stato: $ticketStatus) {
      id
      titolo
      priorita
      creato_il
    }
  }
}

# Variabili (passate separatamente)
{
  "userId": "42",
  "ticketStatus": "open"
}
```

#### Mutation

```graphql
mutation CreateNewTicket($input: CreateTicketInput!) {
  createTicket(input: $input) {
    id
    titolo
    stato
    assegnato {
      nome
    }
  }
}

# Variabili
{
  "input": {
    "titolo": "Server DB-01 non raggiungibile",
    "priorita": "alta",
    "assegnatoId": "42",
    "descrizione": "Il server DB-01 non risponde al ping dalla rete interna."
  }
}
```

#### Fragment

I fragment permettono di riutilizzare selezioni di campi comuni:

```graphql
fragment TicketBase on Ticket {
  id
  titolo
  stato
  priorita
  creato_il
}

query DashboardData {
  ticketAperti: tickets(stato: "open") {
    ...TicketBase
    assegnato { nome }
  }
  ticketUrgenti: tickets(priorita: "critica") {
    ...TicketBase
    assegnato { nome email }
  }
}
```

#### Gestione Errori

Le risposte GraphQL includono sempre un campo `errors` se qualcosa va storto, anche quando parte della query ha successo:

```json
{
  "data": {
    "user": {
      "nome": "Mario Rossi",
      "email": "mario@example.com"
    }
  },
  "errors": [
    {
      "message": "Non hai i permessi per accedere ai ticket",
      "locations": [{ "line": 5, "column": 5 }],
      "path": ["user", "tickets"],
      "extensions": {
        "code": "FORBIDDEN"
      }
    }
  ]
}
```

### Strumenti GraphQL

**GraphiQL e Apollo Studio** — IDE interattivi per esplorare schemi GraphQL, scrivere query con autocompletamento e visualizzare la documentazione. Apollo Studio offre inoltre monitoraggio delle performance e gestione degli schemi in produzione.

**Python con gql:**

```python
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

transport = RequestsHTTPTransport(
    url="https://api.example.com/graphql",
    headers={"Authorization": "Bearer il-tuo-token"},
    verify=True,
)

client = Client(transport=transport, fetch_schema_from_transport=True)

query = gql("""
    query GetTickets($stato: String!) {
        tickets(stato: $stato) {
            id
            titolo
            priorita
            assegnato { nome }
        }
    }
""")

result = client.execute(query, variable_values={"stato": "open"})
for ticket in result["tickets"]:
    print(f"[{ticket['priorita']}] {ticket['titolo']} -> {ticket['assegnato']['nome']}")
```

**curl:**

```bash
curl -X POST https://api.example.com/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer il-tuo-token" \
  -d '{
    "query": "query { users(ruolo: \"admin\") { nome email } }"
  }'
```

---

## Webhook

### Architettura

I webhook invertono il modello tradizionale di comunicazione API. Invece del **modello pull** (il client interroga periodicamente il server per verificare se ci sono aggiornamenti), i webhook implementano un **modello push**: il server notifica automaticamente il client quando si verifica un evento specifico.

Questa inversione è fondamentale per l'automazione reattiva. Invece di eseguire polling ogni 30 secondi per verificare se un ticket è stato aggiornato (spreco di risorse e latenza fino a 30 secondi), un webhook notifica immediatamente il sistema quando l'aggiornamento avviene.

**Anatomia di un webhook:**
- **URL di callback**: l'endpoint HTTP del ricevente che il server chiamerà
- **Payload**: i dati dell'evento, tipicamente in formato JSON
- **Header**: metadati come il tipo di evento, timestamp e firma per la verifica
- **Secret**: chiave condivisa per la verifica dell'autenticità del messaggio (HMAC)

### Implementazione Receiver

Un ricevitore webhook deve essere un endpoint HTTP accessibile pubblicamente, capace di processare le notifiche in modo rapido e sicuro.

#### Endpoint Flask/FastAPI

```python
"""Ricevitore webhook con FastAPI, verifica della firma e gestione idempotente."""
import hmac
import hashlib
import json
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Header
from typing import Optional

app = FastAPI()

# In produzione, usare Redis o un database
processed_events = set()

WEBHOOK_SECRET = "il-tuo-secret-condiviso"


def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verifica la firma HMAC-SHA256 del payload.
    Previene attacchi dove un attore malevolo invia webhook falsificati.
    """
    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()

    # Confronto a tempo costante per prevenire timing attacks
    return hmac.compare_digest(f"sha256={expected}", signature)


@app.post("/webhooks/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None),
    x_github_event: Optional[str] = Header(None),
    x_github_delivery: Optional[str] = Header(None),
):
    """Endpoint per ricevere webhook da GitHub."""
    body = await request.body()

    # 1. Verifica la firma
    if not x_hub_signature_256:
        raise HTTPException(status_code=401, detail="Firma mancante")

    if not verify_signature(body, x_hub_signature_256, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Firma non valida")

    # 2. Gestione idempotenza (previene elaborazione duplicata)
    delivery_id = x_github_delivery
    if delivery_id in processed_events:
        return {"status": "already_processed", "delivery_id": delivery_id}

    # 3. Processa l'evento
    payload = json.loads(body)
    event_type = x_github_event

    if event_type == "push":
        handle_push(payload)
    elif event_type == "pull_request":
        handle_pull_request(payload)
    elif event_type == "issues":
        handle_issue(payload)
    else:
        print(f"Evento non gestito: {event_type}")

    # 4. Registra l'evento come processato
    processed_events.add(delivery_id)

    # 5. Rispondi rapidamente (< 10 secondi)
    return {"status": "ok", "event": event_type}


def handle_push(payload):
    """Gestisce un evento push."""
    repo = payload["repository"]["full_name"]
    branch = payload["ref"].split("/")[-1]
    commits = len(payload.get("commits", []))
    print(f"Push su {repo}/{branch}: {commits} commit")


def handle_pull_request(payload):
    """Gestisce un evento pull request."""
    action = payload["action"]
    pr = payload["pull_request"]
    print(f"PR #{pr['number']} {action}: {pr['title']}")


def handle_issue(payload):
    """Gestisce un evento issue."""
    action = payload["action"]
    issue = payload["issue"]
    print(f"Issue #{issue['number']} {action}: {issue['title']}")
```

#### Requisiti Fondamentali per i Receiver

1. **Rispondi rapidamente**: restituire una risposta `200 OK` entro pochi secondi. Se l'elaborazione richiede tempo, accettare il webhook e processarlo in modo asincrono (coda di messaggi)
2. **Verifica la firma**: non fidarsi mai di un webhook senza verificare la firma HMAC
3. **Gestisci l'idempotenza**: i provider potrebbero inviare lo stesso webhook più volte (retry su timeout). Usare l'ID di delivery per deduplicare
4. **Gestisci i retry**: se il receiver restituisce un errore (5xx), il provider riproverà. Assicurarsi che la logica sia idempotente

### Webhook Comuni

#### GitHub Webhooks

GitHub può notificare su push, pull request, issue, release e molti altri eventi. La configurazione avviene nelle impostazioni del repository o dell'organizzazione.

Eventi più utili per l'automazione:
- `push` — trigger per CI/CD
- `pull_request` — review automatiche, test, deploy di preview
- `issues` — sincronizzazione con sistemi di ticketing
- `release` — trigger per deploy in produzione

#### Stripe Webhooks

Stripe notifica su eventi di pagamento, abbonamento, fatturazione e altro. Essenziale per automazioni finanziarie.

```python
import stripe

@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Firma non valida")

    if event["type"] == "payment_intent.succeeded":
        payment = event["data"]["object"]
        print(f"Pagamento ricevuto: {payment['amount'] / 100}€")
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        print(f"Abbonamento cancellato: {subscription['id']}")

    return {"status": "ok"}
```

#### Slack Webhooks

**Incoming Webhooks** — invio di messaggi a un canale Slack tramite URL:

```python
import requests

SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/T.../B.../xxx"

def send_slack_notification(text, channel=None, blocks=None):
    """Invia una notifica su Slack tramite incoming webhook."""
    payload = {"text": text}
    if blocks:
        payload["blocks"] = blocks

    response = requests.post(SLACK_WEBHOOK_URL, json=payload)
    response.raise_for_status()

# Esempio: notifica di allarme
send_slack_notification(
    text="Allarme: CPU al 95% su server PROD-WEB-01",
    blocks=[
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Allarme Critico* :rotating_light:\n"
                        "CPU al *95%* su `PROD-WEB-01`\n"
                        "Durata: 5 minuti consecutivi"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Vedi Dashboard"},
                    "url": "https://grafana.example.com/d/server-metrics"
                }
            ]
        }
    ]
)
```

---

## API Comuni per IT Automation

### Microsoft Graph API

Microsoft Graph è il punto di accesso unificato ai servizi Microsoft 365: utenti, gruppi, email, calendari, Teams, SharePoint e molto altro. È probabilmente l'API più importante per l'automazione in ambienti aziendali Microsoft.

**Autenticazione** — Richiede la registrazione di un'applicazione su Azure AD (Entra ID):

1. Registrare l'applicazione nel portale Azure
2. Configurare i permessi (delegati per azioni per conto dell'utente, applicazione per machine-to-machine)
3. Generare un client secret o certificato
4. Utilizzare il Client Credentials Flow per l'automazione

```python
import requests

class MicrosoftGraphClient:
    def __init__(self, tenant_id, client_id, client_secret):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.token = None

    def authenticate(self):
        """Ottiene un token di accesso tramite Client Credentials Flow."""
        response = requests.post(
            f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "https://graph.microsoft.com/.default",
            }
        )
        response.raise_for_status()
        self.token = response.json()["access_token"]

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def list_users(self, department=None):
        """Elenca gli utenti, opzionalmente filtrati per dipartimento."""
        url = f"{self.base_url}/users"
        params = {"$select": "displayName,mail,department,jobTitle"}
        if department:
            params["$filter"] = f"department eq '{department}'"
        response = requests.get(url, headers=self._headers(), params=params)
        response.raise_for_status()
        return response.json()["value"]

    def create_user(self, user_data):
        """Crea un nuovo utente in Azure AD."""
        response = requests.post(
            f"{self.base_url}/users",
            headers=self._headers(),
            json=user_data
        )
        response.raise_for_status()
        return response.json()

    def add_user_to_group(self, group_id, user_id):
        """Aggiunge un utente a un gruppo Azure AD."""
        response = requests.post(
            f"{self.base_url}/groups/{group_id}/members/$ref",
            headers=self._headers(),
            json={
                "@odata.id": f"https://graph.microsoft.com/v1.0/users/{user_id}"
            }
        )
        response.raise_for_status()

    def send_mail(self, sender, to, subject, body):
        """Invia un'email tramite Microsoft Graph."""
        response = requests.post(
            f"{self.base_url}/users/{sender}/sendMail",
            headers=self._headers(),
            json={
                "message": {
                    "subject": subject,
                    "body": {"contentType": "HTML", "content": body},
                    "toRecipients": [
                        {"emailAddress": {"address": addr}} for addr in to
                    ],
                }
            }
        )
        response.raise_for_status()


# Esempio: provisioning automatizzato di un nuovo dipendente
def onboard_new_employee(graph, employee_info):
    """Automatizza il provisioning di un nuovo dipendente."""
    # 1. Crea l'utente
    user = graph.create_user({
        "accountEnabled": True,
        "displayName": employee_info["nome"],
        "mailNickname": employee_info["username"],
        "userPrincipalName": f"{employee_info['username']}@azienda.com",
        "passwordProfile": {
            "forceChangePasswordNextSignIn": True,
            "password": employee_info["password_temporanea"],
        },
        "department": employee_info["dipartimento"],
        "jobTitle": employee_info["ruolo"],
    })

    # 2. Aggiungi ai gruppi appropriati
    for group_id in employee_info["gruppi"]:
        graph.add_user_to_group(group_id, user["id"])

    # 3. Invia email di benvenuto
    graph.send_mail(
        sender="hr@azienda.com",
        to=[f"{employee_info['username']}@azienda.com"],
        subject="Benvenuto in azienda!",
        body=f"<h1>Benvenuto, {employee_info['nome']}!</h1>"
             f"<p>Il tuo account e' stato creato con successo.</p>"
    )

    return user
```

### Jira/Atlassian API

L'API di Jira è fondamentale per l'automazione dei processi di sviluppo e supporto. Permette di creare, aggiornare e interrogare issue, progetti e board.

**Autenticazione** — Per Jira Cloud si usa un API token (generato dal profilo Atlassian) con Basic Auth:

```python
import requests
from requests.auth import HTTPBasicAuth

class JiraClient:
    def __init__(self, base_url, email, api_token):
        self.base_url = base_url.rstrip("/")
        self.auth = HTTPBasicAuth(email, api_token)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def search_issues(self, jql, max_results=50):
        """Cerca issue con JQL (Jira Query Language)."""
        response = requests.get(
            f"{self.base_url}/rest/api/3/search",
            auth=self.auth,
            headers=self.headers,
            params={"jql": jql, "maxResults": max_results}
        )
        response.raise_for_status()
        return response.json()["issues"]

    def create_issue(self, project_key, summary, description, issue_type="Task",
                     priority="Medium", labels=None, assignee_id=None):
        """Crea una nuova issue su Jira."""
        fields = {
            "project": {"key": project_key},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}]
                    }
                ]
            },
            "issuetype": {"name": issue_type},
            "priority": {"name": priority},
        }
        if labels:
            fields["labels"] = labels
        if assignee_id:
            fields["assignee"] = {"accountId": assignee_id}

        response = requests.post(
            f"{self.base_url}/rest/api/3/issue",
            auth=self.auth,
            headers=self.headers,
            json={"fields": fields}
        )
        response.raise_for_status()
        return response.json()

    def transition_issue(self, issue_key, transition_name):
        """Cambia lo stato di una issue (es. da 'To Do' a 'In Progress')."""
        # Prima, trova l'ID della transizione
        response = requests.get(
            f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions",
            auth=self.auth,
            headers=self.headers
        )
        response.raise_for_status()
        transitions = response.json()["transitions"]
        transition_id = None
        for t in transitions:
            if t["name"].lower() == transition_name.lower():
                transition_id = t["id"]
                break

        if not transition_id:
            raise ValueError(
                f"Transizione '{transition_name}' non trovata per {issue_key}"
            )

        response = requests.post(
            f"{self.base_url}/rest/api/3/issue/{issue_key}/transitions",
            auth=self.auth,
            headers=self.headers,
            json={"transition": {"id": transition_id}}
        )
        response.raise_for_status()


# Esempio: creazione automatica di ticket da un allarme di monitoraggio
def create_incident_ticket(jira, alert):
    """Crea un ticket Jira da un allarme di monitoraggio."""
    severity_map = {
        "critical": "Highest",
        "warning": "High",
        "info": "Medium"
    }

    issue = jira.create_issue(
        project_key="OPS",
        summary=f"[{alert['severity'].upper()}] {alert['title']}",
        description=(
            f"Allarme ricevuto dal sistema di monitoraggio.\n\n"
            f"Host: {alert['host']}\n"
            f"Servizio: {alert['service']}\n"
            f"Messaggio: {alert['message']}\n"
            f"Timestamp: {alert['timestamp']}"
        ),
        issue_type="Bug",
        priority=severity_map.get(alert["severity"], "Medium"),
        labels=["auto-generated", "monitoring", alert["severity"]],
    )

    return issue
```

### Slack API

L'API di Slack è essenziale per le notifiche e la comunicazione automatizzata nei flussi di lavoro IT.

```python
import requests

class SlackClient:
    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.base_url = "https://slack.com/api"
        self.headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json",
        }

    def send_message(self, channel, text, blocks=None, thread_ts=None):
        """Invia un messaggio su un canale Slack."""
        payload = {
            "channel": channel,
            "text": text,
        }
        if blocks:
            payload["blocks"] = blocks
        if thread_ts:
            payload["thread_ts"] = thread_ts

        response = requests.post(
            f"{self.base_url}/chat.postMessage",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        if not data["ok"]:
            raise Exception(f"Errore Slack: {data['error']}")
        return data

    def send_alert(self, channel, title, message, severity="warning", fields=None):
        """Invia un messaggio di allarme formattato con block kit."""
        color_map = {
            "critical": "#FF0000",
            "warning": "#FFA500",
            "info": "#0099FF",
            "ok": "#00FF00"
        }

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": title}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": message}
            },
        ]

        if fields:
            field_blocks = []
            for key, value in fields.items():
                field_blocks.append({
                    "type": "mrkdwn",
                    "text": f"*{key}:*\n{value}"
                })
            blocks.append({"type": "section", "fields": field_blocks})

        # Aggiungi la barra colorata tramite un attachment
        payload = {
            "channel": channel,
            "text": f"[{severity.upper()}] {title}",
            "attachments": [{"color": color_map.get(severity, "#808080"), "blocks": blocks}],
        }

        response = requests.post(
            f"{self.base_url}/chat.postMessage",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()


# Esempio: notifica di allarme
slack = SlackClient(bot_token="xoxb-...")
slack.send_alert(
    channel="#ops-alerts",
    title="Disco quasi pieno",
    message="Il disco `/data` su `PROD-DB-01` ha raggiunto il *92%* di utilizzo.",
    severity="warning",
    fields={
        "Host": "`PROD-DB-01`",
        "Disco": "`/data`",
        "Utilizzo": "92% (230GB / 250GB)",
        "Stima esaurimento": "~48 ore"
    }
)
```

### ServiceNow API

ServiceNow espone una Table API REST che permette di interagire con qualsiasi tabella del sistema: incident, change request, CMDB e molto altro.

```python
import requests
from requests.auth import HTTPBasicAuth

class ServiceNowClient:
    def __init__(self, instance, username, password):
        self.base_url = f"https://{instance}.service-now.com/api/now"
        self.auth = HTTPBasicAuth(username, password)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def get_records(self, table, query=None, limit=100, fields=None):
        """Recupera record da una tabella ServiceNow."""
        params = {"sysparm_limit": limit}
        if query:
            params["sysparm_query"] = query
        if fields:
            params["sysparm_fields"] = ",".join(fields)

        response = requests.get(
            f"{self.base_url}/table/{table}",
            auth=self.auth,
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()["result"]

    def create_record(self, table, data):
        """Crea un nuovo record in una tabella ServiceNow."""
        response = requests.post(
            f"{self.base_url}/table/{table}",
            auth=self.auth,
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()["result"]

    def update_record(self, table, sys_id, data):
        """Aggiorna un record esistente."""
        response = requests.patch(
            f"{self.base_url}/table/{table}/{sys_id}",
            auth=self.auth,
            headers=self.headers,
            json=data
        )
        response.raise_for_status()
        return response.json()["result"]

    def create_incident(self, short_description, description, urgency=2,
                        impact=2, category=None, assignment_group=None,
                        caller_id=None):
        """Crea un nuovo incident."""
        data = {
            "short_description": short_description,
            "description": description,
            "urgency": str(urgency),
            "impact": str(impact),
        }
        if category:
            data["category"] = category
        if assignment_group:
            data["assignment_group"] = assignment_group
        if caller_id:
            data["caller_id"] = caller_id

        return self.create_record("incident", data)


# Esempio: creazione automatica di un incident da un allarme
def create_snow_incident_from_alert(snow, alert):
    """Crea un incident ServiceNow da un allarme di monitoraggio."""
    urgency_map = {"critical": 1, "warning": 2, "info": 3}

    incident = snow.create_incident(
        short_description=f"[AUTO] {alert['title']}",
        description=(
            f"Incident creato automaticamente dal sistema di monitoraggio.\n\n"
            f"Dettagli allarme:\n"
            f"  Host: {alert['host']}\n"
            f"  Servizio: {alert['service']}\n"
            f"  Severita': {alert['severity']}\n"
            f"  Messaggio: {alert['message']}\n"
            f"  Timestamp: {alert['timestamp']}\n\n"
            f"Dashboard: {alert.get('dashboard_url', 'N/D')}"
        ),
        urgency=urgency_map.get(alert["severity"], 2),
        impact=urgency_map.get(alert["severity"], 2),
        category="Infrastructure",
        assignment_group="Server Operations",
    )

    return incident
```

---

## Progettazione Integrazioni Robuste

Le integrazioni API in produzione devono gestire errori, interruzioni e comportamenti imprevisti. Questa sezione copre i pattern architetturali che rendono le integrazioni affidabili.

### Circuit Breaker Pattern

Il circuit breaker previene il sovraccarico di un servizio che sta già avendo problemi. Come un interruttore elettrico, "apre il circuito" dopo un certo numero di errori consecutivi, evitando di inviare ulteriori richieste a un servizio in difficolta'.

```python
import time
from enum import Enum


class CircuitState(Enum):
    CLOSED = "closed"        # Funzionamento normale
    OPEN = "open"            # Circuito aperto, richieste bloccate
    HALF_OPEN = "half_open"  # Test di ripresa


class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=30,
                 success_threshold=3):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    def can_execute(self):
        """Verifica se e' possibile eseguire una richiesta."""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                return True
            return False
        else:  # HALF_OPEN
            return True

    def record_success(self):
        """Registra una richiesta riuscita."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
        else:
            self.failure_count = 0

    def record_failure(self):
        """Registra una richiesta fallita."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

    def execute(self, func, *args, **kwargs):
        """Esegue una funzione protetta dal circuit breaker."""
        if not self.can_execute():
            raise Exception(
                f"Circuit breaker APERTO. Prossimo tentativo tra "
                f"{self.recovery_timeout - (time.time() - self.last_failure_time):.0f}s"
            )
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise
```

### Retry con Exponential Backoff

Gia' trattato nella sezione Rate Limiting, il pattern di retry con backoff esponenziale e jitter e' il metodo standard per gestire errori transitori. La regola fondamentale: ritentare solo errori recuperabili (5xx, timeout, errori di rete). Non ritentare mai errori 4xx (tranne 429).

### Dead Letter Queue

Quando un messaggio o un evento non puo' essere elaborato dopo tutti i tentativi di retry, va salvato in una "dead letter queue" (coda per messaggi non elaborabili) per analisi successiva e rielaborazione manuale.

```python
import json
import sqlite3
from datetime import datetime


class DeadLetterQueue:
    """Coda per eventi non elaborabili, con supporto per rielaborazione."""

    def __init__(self, db_path="dead_letters.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS dead_letters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                event_type TEXT,
                payload TEXT NOT NULL,
                error_message TEXT,
                attempts INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_attempt_at TIMESTAMP,
                resolved_at TIMESTAMP
            )
        """)
        self.conn.commit()

    def add(self, source, payload, error_message, event_type=None, attempts=0):
        """Aggiunge un evento non elaborabile alla coda."""
        self.conn.execute(
            """INSERT INTO dead_letters
               (source, event_type, payload, error_message, attempts, last_attempt_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (source, event_type, json.dumps(payload), error_message,
             attempts, datetime.utcnow().isoformat())
        )
        self.conn.commit()

    def get_unresolved(self, source=None, limit=50):
        """Recupera gli eventi non risolti per rielaborazione."""
        query = "SELECT * FROM dead_letters WHERE resolved_at IS NULL"
        params = []
        if source:
            query += " AND source = ?"
            params.append(source)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        cursor = self.conn.execute(query, params)
        return cursor.fetchall()

    def mark_resolved(self, letter_id):
        """Segna un evento come risolto."""
        self.conn.execute(
            "UPDATE dead_letters SET resolved_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), letter_id)
        )
        self.conn.commit()
```

### Idempotency Key

Per operazioni non idempotenti (come POST), le idempotency key garantiscono che la stessa operazione non venga eseguita due volte, anche in caso di retry.

```python
import uuid

def create_resource_idempotent(client, url, data):
    """Crea una risorsa con idempotency key per prevenire duplicati."""
    idempotency_key = str(uuid.uuid4())
    response = client.post(
        url,
        json=data,
        headers={"Idempotency-Key": idempotency_key}
    )
    return response
```

### Logging e Monitoraggio

Ogni integrazione deve produrre log strutturati per diagnosticare problemi:

```python
import logging
import json
import time

logger = logging.getLogger("api_integration")

def log_api_call(method, url, status_code, duration_ms, request_id=None,
                 error=None):
    """Produce un log strutturato per ogni chiamata API."""
    log_data = {
        "event": "api_call",
        "method": method,
        "url": url,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        "request_id": request_id,
        "timestamp": time.time(),
    }
    if error:
        log_data["error"] = str(error)
        logger.error(json.dumps(log_data))
    elif status_code >= 400:
        logger.warning(json.dumps(log_data))
    else:
        logger.info(json.dumps(log_data))
```

### Gestione del Versioning delle API

Le API evolvono nel tempo. Una buona strategia di integrazione deve gestire le diverse versioni:

- Specificare sempre la versione nell'URL (`/api/v2/...`) o negli header (`Accept: application/vnd.api+json;version=2`)
- Monitorare i deprecation header (`Sunset`, `Deprecation`)
- Mantenere la compatibilita' con la versione minima supportata
- Pianificare la migrazione quando una versione viene deprecata

### Data Transformation e Mapping

Quando si collegano sistemi diversi, e' necessario trasformare i dati da un formato all'altro:

```python
def map_jira_to_servicenow(jira_issue):
    """Trasforma una issue Jira nel formato di un incident ServiceNow."""
    priority_map = {
        "Highest": 1,
        "High": 2,
        "Medium": 3,
        "Low": 4,
        "Lowest": 5
    }

    return {
        "short_description": jira_issue["fields"]["summary"],
        "description": (
            f"Importato da Jira: {jira_issue['key']}\n\n"
            f"{jira_issue['fields'].get('description', 'Nessuna descrizione')}"
        ),
        "urgency": str(priority_map.get(
            jira_issue["fields"]["priority"]["name"], 3
        )),
        "external_reference": jira_issue["key"],
        "category": "Application",
    }
```

---

## Strumenti

### Postman e Insomnia

**Postman** e' lo strumento di riferimento per testare e documentare le API. Permette di creare collezioni di richieste organizzate, definire variabili d'ambiente (sviluppo, staging, produzione), scrivere test automatizzati in JavaScript e generare documentazione. Le collezioni possono essere condivise con il team e integrate nelle pipeline CI/CD tramite Newman (il runner da riga di comando di Postman).

**Insomnia** e' un'alternativa piu' leggera con un'eccellente interfaccia per GraphQL, supporto nativo per gRPC e un sistema di plugin estensibile. E' ideale per chi preferisce uno strumento meno complesso di Postman.

Entrambi supportano:
- Importazione/esportazione OpenAPI e cURL
- Gestione automatica dei token OAuth
- Variabili d'ambiente e interpolazione
- Test pre/post-request

### curl e HTTPie

**curl** e' lo strumento da riga di comando universale per le richieste HTTP. Indispensabile per debug, script e automazione:

```bash
# GET con autenticazione
curl -s -H "Authorization: Bearer $TOKEN" \
  https://api.example.com/v1/users | jq .

# POST con body JSON
curl -X POST https://api.example.com/v1/tickets \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"titolo": "Test", "priorita": "alta"}'

# Visualizzare solo gli header di risposta
curl -I https://api.example.com/v1/health

# Verbose per il debug
curl -v https://api.example.com/v1/status
```

**HTTPie** e' un'alternativa a curl con una sintassi piu' intuitiva e output formattato e colorato:

```bash
# GET con autenticazione
http GET api.example.com/v1/users Authorization:"Bearer $TOKEN"

# POST con body JSON (sintassi naturale)
http POST api.example.com/v1/tickets \
  titolo="Test" priorita="alta" \
  Authorization:"Bearer $TOKEN"
```

### mitmproxy

**mitmproxy** e' un proxy HTTP/HTTPS interattivo per intercettare, ispezionare e modificare il traffico di rete. Fondamentale per il debug delle integrazioni API quando le cose non funzionano come previsto. Permette di vedere esattamente cosa viene inviato e ricevuto, inclusi header, body e tempi di risposta.

Casi d'uso nel debugging delle integrazioni:
- Verificare esattamente quale richiesta viene inviata dal codice
- Ispezionare le risposte del server senza modificare il codice
- Simulare risposte di errore per testare la gestione degli errori
- Registrare il traffico per analisi successive

### Swagger e OpenAPI

**OpenAPI Specification** (ex Swagger) e' lo standard per descrivere le API REST in modo machine-readable. Un file OpenAPI (YAML o JSON) definisce endpoint, parametri, tipi di dati, autenticazione e risposte.

**Swagger UI** genera automaticamente documentazione interattiva da un file OpenAPI, permettendo di testare le API direttamente dal browser.

**Swagger Codegen** e **OpenAPI Generator** generano automaticamente codice client (SDK) in decine di linguaggi a partire da un file OpenAPI, eliminando la necessita' di scrivere manualmente il codice di integrazione.

Vantaggi per l'automazione:
- Documentazione sempre aggiornata (generata dal codice)
- Validazione automatica delle richieste e risposte
- Generazione automatica di client SDK
- Contratto formale tra provider e consumer dell'API

---

## Best Practices

1. **Esternalizzare sempre le credenziali.** Non inserire mai API key, token o secret direttamente nel codice sorgente. Utilizzare variabili d'ambiente, file `.env` (esclusi dal version control), o un secrets manager dedicato (HashiCorp Vault, AWS Secrets Manager, Azure Key Vault). In un contesto CI/CD, usare i secret nativi della piattaforma (GitHub Secrets, GitLab CI Variables).

2. **Implementare retry con exponential backoff su ogni integrazione.** Gli errori transitori sono inevitabili: timeout di rete, sovraccarichi temporanei, deploy del servizio remoto. Un meccanismo di retry con backoff esponenziale e jitter deve essere presente su ogni chiamata API. Senza retry, un'automazione che funziona al 99,9% fallira' comunque una volta su mille — inaccettabile per sistemi critici.

3. **Verificare sempre le risposte dell'API.** Non dare per scontato che una richiesta sia andata a buon fine. Controllare il codice di stato HTTP, validare la struttura della risposta JSON e gestire esplicitamente ogni caso di errore. Un campo mancante nella risposta non deve causare un crash silenzioso ma un errore tracciabile.

4. **Usare timeout espliciti su ogni richiesta.** Una richiesta senza timeout puo' bloccare indefinitamente un'automazione. Impostare sempre un connect timeout (tipicamente 5-10 secondi) e un read timeout (tipicamente 30-60 secondi). Per operazioni di lunga durata, considerare pattern asincroni (polling con `202 Accepted`).

   ```python
   response = requests.get(url, timeout=(5, 30))  # (connect, read)
   ```

5. **Versionare le integrazioni insieme al codice.** Le configurazioni API (URL, endpoint, mapping dei campi) devono essere versionati nel repository, non gestiti manualmente. Quando un'API cambia, la modifica deve essere tracciata in un commit, testata e distribuita come qualsiasi altra modifica al codice.

6. **Loggare ogni interazione API.** Ogni richiesta e risposta deve produrre un log strutturato con metodo, URL, codice di stato, durata e request ID. In caso di errore, includere il corpo della risposta. Questi log sono essenziali per diagnosticare problemi in produzione. Attenzione a non loggare mai credenziali, token o dati sensibili.

7. **Progettare per l'idempotenza.** Ogni automazione deve essere sicura da rieseguire. Se un flusso fallisce a meta', deve essere possibile riavviarlo senza creare duplicati o effetti collaterali. Utilizzare idempotency key per le operazioni POST, controllare l'esistenza delle risorse prima di crearle e implementare la gestione degli eventi duplicati nei receiver webhook.

8. **Utilizzare paginazione corretta per le operazioni bulk.** Non tentare mai di recuperare tutti i record in una singola chiamata. Implementare correttamente la paginazione (preferibilmente cursor-based) e aggiungere ritardi tra le pagine per rispettare i rate limit. Un'automazione che scarica migliaia di record senza paginazione puo' causare timeout, esaurire la memoria o essere bloccata dal rate limiter.

9. **Testare le integrazioni con mock e ambienti di staging.** Non testare mai le integrazioni direttamente in produzione. Utilizzare librerie di mocking (responses, httpretty per Python; nock per Node.js) per i test unitari, e ambienti sandbox o staging forniti dai provider per i test di integrazione. Simulare esplicitamente gli errori (timeout, 500, 429) per verificare che la gestione degli errori funzioni correttamente.

10. **Monitorare proattivamente le integrazioni.** Non aspettare che un utente segnali un problema. Implementare health check periodici su ogni integrazione, allarmi su tassi di errore anomali, metriche sulla latenza delle chiamate e alert sulla prossima scadenza dei certificati e dei token. Un dashboard dedicato alle integrazioni API deve mostrare in tempo reale lo stato di salute di ogni collegamento.

---

> **Nota**: Questo documento fornisce una base solida per l'integrazione API nell'ambito dell'automazione IT. Gli esempi di codice sono in Python per la loro leggibilita' e diffusione, ma i concetti e i pattern si applicano a qualsiasi linguaggio di programmazione. Per approfondimenti su specifiche API o pattern architetturali, consultare la documentazione ufficiale dei singoli servizi e le risorse elencate nella sezione strumenti.

---

## Esercizi

1. **Lab — REST client production-grade.** Implementa client Python con: retry exponential backoff, rate limit handling (429), cursor pagination, schema validation (pydantic), logging strutturato.
2. **Lab — webhook receiver vs polling.** Stesso scenario (sync nuovo ordine Stripe), implementa entrambi. Confronta latenza, costo, complessita.
3. **Stretch — OpenAPI to SDK.** Da spec OpenAPI di una API pubblica (Stripe, GitHub, Slack), genera SDK Python via `openapi-python-client`, valida funzionante.

## Auto-valutazione

1. API key vs OAuth vs JWT: quando uno o l'altro?
2. Cursor vs offset pagination: quale e robusto?
3. Cosa fare al ricevere 429?
4. Webhook vs polling: criteri di scelta.
5. mTLS: cos'e e quando si usa?

## Letture primarie consigliate

- RFC 6749 — OAuth 2.0. Vedi `00-BIBLIOGRAFIA.md`.
- RFC 7807 — Problem Details for HTTP APIs.
- Stripe API Reference. https://stripe.com/docs/api
- Python `httpx`. https://www.python-httpx.org/

## Collegamenti incrociati

- Modulo 15 — `15-webhook-security-hmac-verifica.md`: webhook security.
- Modulo 17 — `17-retry-idempotency-pattern.md`: retry pattern dettaglio.
- Modulo 20 — `20-oauth2-flows-refresh-token-automazione.md`: OAuth flows.

## Glossario locale

| Termine | Definizione |
|---|---|
| **REST** | Representational State Transfer; stile architetturale HTTP. |
| **OAuth** | Standard auth delegata (RFC 6749). |
| **JWT** | JSON Web Token (RFC 7519). |
| **mTLS** | Mutual TLS; client + server presentano cert. |
| **Rate limit** | Limite richieste/secondo. |
| **Backoff exponential** | Retry interval che cresce esponenzialmente. |
| **Cursor pagination** | Token opaco che indica posizione. |
| **Offset pagination** | Numero di skip; fragile. |
| **Webhook** | Push da server a client su evento. |
| **Polling** | Pull periodico dal client. |
| **Sandbox** | Ambiente di test isolato dal produzione. |
