---
corso: "Sviluppo Web"
fase: "4 — Backend"
modulo: "11"
titolo: "API Design"
versione: "REST / GraphQL / gRPC / OpenAPI 3.1"
livello: "Intermedio-Avanzato"
prerequisiti:
  - "10 — Node.js"
  - "06 — TypeScript"
obiettivi:
  - "Progettare API RESTful seguendo best practice e convenzioni"
  - "Documentare API con OpenAPI 3.1 e generare client/server"
  - "Implementare versioning, pagination e HATEOAS"
  - "Progettare schemi GraphQL e risolvere problemi N+1"
  - "Comprendere gRPC per comunicazione inter-servizio"
  - "Applicare rate limiting, caching e idempotency"
tag: [API-design, REST, GraphQL, gRPC, OpenAPI, versioning, pagination]
---

# API Design

> **Modulo 11** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [Node.js](10-nodejs.md), [TypeScript](06-typescript.md)
>
> Al termine di questo modulo saprai:
> 1. Progettare API RESTful seguendo best practice e convenzioni
> 2. Documentare API con OpenAPI 3.1 e generare client/server
> 3. Implementare versioning, pagination e HATEOAS
> 4. Progettare schemi GraphQL e risolvere problemi N+1
> 5. Comprendere gRPC per comunicazione inter-servizio
> 6. Applicare rate limiting, caching e idempotency
>
> **Tempo stimato:** 6-8 ore · **Livello:** Intermedio-Avanzato

## Idee guida
1. **REST levels (Richardson Maturity Model).** Level 3 = HATEOAS.
2. **Cursor pagination > offset.** Robust to mutations.
3. **DataLoader batching per N+1.** GraphQL essential.
4. **GraphQL persisted queries: server-side allowlist; performance + security.**
5. **RFC 7807 Problem Details: errori HTTP standardizzati.**


## Panoramica

Il termine **API** (Application Programming Interface) indica un contratto formale che definisce come due sistemi software comunicano tra loro. Un'API ben progettata rappresenta uno degli asset più duraturi di un'architettura software: mentre le interfacce utente cambiano frequentemente e le implementazioni interne vengono riscritte, le API tendono a sopravvivere per anni o decenni. Per questa ragione, investire tempo nella progettazione accurata di un'API non è un lusso, ma una necessità strategica.

La progettazione di API moderne si articola su diversi paradigmi — REST, GraphQL, gRPC, WebSocket — ciascuno con punti di forza specifici e contesti d'uso ottimali. REST domina le API pubbliche grazie alla sua semplicità e aderenza agli standard HTTP. GraphQL eccelle quando i client hanno esigenze di dati eterogenee e vogliono evitare over-fetching. gRPC è la scelta preferita per la comunicazione inter-servizio ad alte prestazioni. WebSocket abilita la comunicazione bidirezionale in tempo reale.

Questa guida esplora ciascun paradigma in profondità, affrontando aspetti trasversali come l'autenticazione, il versionamento, il rate limiting, il caching e le best practice che distinguono un'API mediocre da un'API eccellente.

---

## REST API Design

REST (Representational State Transfer) è uno stile architetturale definito da Roy Fielding nella sua dissertazione del 2000. Non è un protocollo né uno standard, ma un insieme di vincoli architetturali che, quando rispettati, producono sistemi scalabili, affidabili e facili da comprendere.

### Resource Naming

La progettazione degli URI è il fondamento di ogni REST API. Le risorse devono essere identificate da sostantivi plurali, mai da verbi, poiché le azioni vengono espresse tramite i metodi HTTP.

```
# Corretto — sostantivi plurali
GET    /api/v1/users
GET    /api/v1/users/42
GET    /api/v1/users/42/orders
GET    /api/v1/users/42/orders/7

# Errato — verbi nell'URI
GET    /api/v1/getUsers
POST   /api/v1/createUser
DELETE /api/v1/deleteUser/42
```

Convenzioni fondamentali per il naming delle risorse:

- Utilizzare **kebab-case** per URI multi-parola: `/api/v1/order-items` anziché `/api/v1/orderItems`.
- Evitare nesting eccessivo oltre due livelli: `/users/42/orders` è accettabile, `/users/42/orders/7/items/3/reviews` è troppo profondo. In quest'ultimo caso, promuovere le sotto-risorse a risorse di primo livello: `/order-items/3/reviews`.
- Utilizzare **query parameters** per il filtraggio, non segmenti di path: `/users?role=admin` anziché `/users/role/admin`.
- Non includere mai estensioni di file negli URI (`.json`, `.xml`). Il formato di risposta si negozia tramite l'header `Accept`.
- Mantenere coerenza assoluta: se una risorsa è `orders`, non alternare con `order` o `Orders` in endpoint diversi.

### HTTP Methods

Ogni metodo HTTP ha una semantica precisa che deve essere rispettata rigorosamente:

| Metodo | Semantica | Idempotente | Safe | Corpo richiesta | Corpo risposta |
|---------|-----------|-------------|------|-----------------|----------------|
| `GET` | Legge una risorsa o collezione | Sì | Sì | No | Sì |
| `POST` | Crea una nuova risorsa | No | No | Sì | Sì |
| `PUT` | Sostituisce interamente una risorsa | Sì | No | Sì | Sì |
| `PATCH` | Aggiorna parzialmente una risorsa | Sì* | No | Sì | Sì |
| `DELETE` | Elimina una risorsa | Sì | No | Opzionale | Opzionale |
| `HEAD` | Come GET ma senza corpo risposta | Sì | Sì | No | No |
| `OPTIONS` | Descrive le opzioni di comunicazione | Sì | Sì | No | Sì |

*`PATCH` è idempotente solo se implementato correttamente (ad esempio con JSON Merge Patch RFC 7396).

La distinzione tra `PUT` e `PATCH` è cruciale. `PUT` sostituisce l'intera risorsa: se un campo non è incluso nel body, viene rimosso o impostato al valore predefinito. `PATCH` modifica solo i campi specificati, lasciando invariati gli altri.

```javascript
// PUT — sostituzione completa
PUT /api/v1/users/42
{
  "name": "Marco Rossi",
  "email": "marco@example.com",
  "role": "editor"         // tutti i campi devono essere presenti
}

// PATCH — aggiornamento parziale (JSON Merge Patch)
PATCH /api/v1/users/42
Content-Type: application/merge-patch+json
{
  "role": "admin"          // solo il campo da modificare
}
```

### Status Codes

I codici di stato HTTP comunicano l'esito di una richiesta in modo standardizzato. Un uso corretto dei codici è essenziale per la comprensibilità dell'API.

**Codici 2xx — Successo:**

| Codice | Significato | Uso tipico |
|--------|-------------|------------|
| `200 OK` | Richiesta riuscita | GET, PUT, PATCH riusciti |
| `201 Created` | Risorsa creata | POST riuscito, con header `Location` |
| `202 Accepted` | Richiesta accettata, elaborazione asincrona | Operazioni long-running |
| `204 No Content` | Successo senza corpo risposta | DELETE riuscito |

**Codici 3xx — Redirezione:**

| Codice | Significato | Uso tipico |
|--------|-------------|------------|
| `301 Moved Permanently` | Risorsa spostata definitivamente | Migrazione endpoint |
| `304 Not Modified` | Risorsa non modificata | Caching con ETag/If-None-Match |

**Codici 4xx — Errore client:**

| Codice | Significato | Uso tipico |
|--------|-------------|------------|
| `400 Bad Request` | Richiesta malformata | Validazione fallita |
| `401 Unauthorized` | Autenticazione mancante o non valida | Token assente o scaduto |
| `403 Forbidden` | Autenticato ma non autorizzato | Permessi insufficienti |
| `404 Not Found` | Risorsa non trovata | ID inesistente |
| `405 Method Not Allowed` | Metodo HTTP non supportato | POST su risorsa read-only |
| `409 Conflict` | Conflitto con stato attuale | Aggiornamento concorrente |
| `422 Unprocessable Entity` | Sintassi corretta ma semantica errata | Regole business violate |
| `429 Too Many Requests` | Rate limit superato | Throttling |

**Codici 5xx — Errore server:**

| Codice | Significato | Uso tipico |
|--------|-------------|------------|
| `500 Internal Server Error` | Errore generico del server | Bug non gestiti |
| `502 Bad Gateway` | Risposta non valida dall'upstream | Errore del servizio a monte |
| `503 Service Unavailable` | Servizio temporaneamente non disponibile | Manutenzione, sovraccarico |
| `504 Gateway Timeout` | Timeout dall'upstream | Servizio a monte lento |

### Richardson Maturity Model — Approfondimento

Il **Richardson Maturity Model** (RMM), concepito da Leonard Richardson e reso popolare da Martin Fowler, classifica le API web in quattro livelli di maturità REST, dal livello 0 (nessuna aderenza ai principi REST) al livello 3 (REST completo con hypermedia). Comprendere questo modello è fondamentale per valutare quanto un'API sia effettivamente "RESTful" e dove investire per migliorarla.

**Livello 0 — The Swamp of POX (Plain Old XML/JSON):** Il servizio espone un singolo endpoint e utilizza un unico metodo HTTP (tipicamente POST) per tutte le operazioni. Le azioni vengono specificate nel corpo della richiesta. Questo è il pattern tipico dei servizi SOAP e delle RPC over HTTP.

```
POST /api/service
{ "action": "getUser", "userId": 42 }

POST /api/service
{ "action": "createOrder", "productId": 7, "quantity": 2 }
```

A questo livello, HTTP è utilizzato solo come meccanismo di trasporto, senza sfruttarne la semantica. Non c'è distinzione tra risorse diverse, e il caching HTTP è impossibile poiché tutte le richieste sono POST allo stesso URL.

**Livello 1 — Risorse:** Il servizio introduce il concetto di risorse individuali, ciascuna con il proprio URI. Tuttavia, continua a utilizzare un singolo metodo HTTP (tipicamente POST) per tutte le operazioni.

```
POST /api/users
{ "action": "get", "id": 42 }

POST /api/orders
{ "action": "create", "productId": 7 }
```

Il miglioramento rispetto al livello 0 è la separazione delle responsabilità: ogni risorsa ha un indirizzo proprio, il che facilita la comprensione e il routing. Ma la semantica delle operazioni è ancora affidata al corpo della richiesta.

**Livello 2 — Verbi HTTP:** L'API utilizza i metodi HTTP appropriati per ciascuna operazione: GET per leggere, POST per creare, PUT/PATCH per aggiornare, DELETE per eliminare. Questo livello sfrutta appieno la semantica HTTP, abilitando il caching nativo (le risposte GET sono cacheable), la safety (GET non modifica lo stato) e l'idempotenza (PUT e DELETE producono lo stesso risultato se ripetuti).

```
GET    /api/users/42       → legge l'utente
POST   /api/users           → crea un utente
PUT    /api/users/42       → aggiorna l'utente
DELETE /api/users/42       → elimina l'utente
```

La maggior parte delle API REST in produzione si posiziona al livello 2. Questo livello è spesso sufficiente per le esigenze pratiche e rappresenta un buon equilibrio tra aderenza ai principi REST e pragmatismo implementativo.

**Livello 3 — Hypermedia (HATEOAS):** Il livello più maturo aggiunge link ipermediali nelle risposte, permettendo al client di scoprire dinamicamente le azioni disponibili e le transizioni di stato possibili. A questo livello, il client non ha bisogno di conoscere a priori la struttura degli URL né le transizioni di stato: tutto viene comunicato dall'API stessa.

La transizione dal livello 2 al livello 3 è il salto più significativo e il meno adottato in pratica. Il vantaggio principale è l'estremo disaccoppiamento tra client e server: il server può modificare la struttura degli URL, aggiungere o rimuovere azioni e cambiare i workflow senza rompere i client esistenti, purché i client seguano i link anziché hard-codarli.

### HATEOAS

HATEOAS (Hypermedia As The Engine Of Application State) è il vincolo REST più avanzato e meno implementato. Prescrive che le risposte dell'API includano link ipermediali che guidano il client attraverso le transizioni di stato disponibili, eliminando la necessità di hard-coding degli URL nel client.

```json
{
  "id": 42,
  "name": "Marco Rossi",
  "email": "marco@example.com",
  "status": "active",
  "_links": {
    "self": {
      "href": "/api/v1/users/42",
      "method": "GET"
    },
    "update": {
      "href": "/api/v1/users/42",
      "method": "PUT"
    },
    "deactivate": {
      "href": "/api/v1/users/42/deactivate",
      "method": "POST"
    },
    "orders": {
      "href": "/api/v1/users/42/orders",
      "method": "GET"
    }
  }
}
```

I vantaggi principali di HATEOAS includono: l'API diventa auto-documentante poiché il client scopre dinamicamente le azioni disponibili; il disaccoppiamento tra client e server aumenta perché i client non hanno bisogno di conoscere a priori la struttura degli URL; la gestione dei permessi diventa implicita perché i link vengono inclusi solo se l'utente è autorizzato a eseguire l'azione corrispondente. Lo svantaggio principale è l'aumento della dimensione delle risposte e la complessità aggiuntiva nell'implementazione.

### Versioning

Il versionamento dell'API garantisce la retrocompatibilità quando si introducono breaking changes. Le tre strategie principali sono trattate in dettaglio nella sezione dedicata più avanti. La più comune per le REST API è il **versioning tramite URL path**:

```
GET /api/v1/users
GET /api/v2/users
```

### Paginazione Offset-Based

La paginazione offset-based è la più intuitiva. Il client specifica quanti record saltare (`offset`) e quanti restituirne (`limit`).

```
GET /api/v1/products?offset=40&limit=20
```

```json
{
  "data": [ /* 20 prodotti */ ],
  "pagination": {
    "offset": 40,
    "limit": 20,
    "total": 523,
    "has_next": true,
    "has_prev": true
  },
  "_links": {
    "self":  { "href": "/api/v1/products?offset=40&limit=20" },
    "next":  { "href": "/api/v1/products?offset=60&limit=20" },
    "prev":  { "href": "/api/v1/products?offset=20&limit=20" },
    "first": { "href": "/api/v1/products?offset=0&limit=20" },
    "last":  { "href": "/api/v1/products?offset=520&limit=20" }
  }
}
```

**Limiti della paginazione offset-based:** quando i dati sottostanti cambiano tra una richiesta e l'altra, il client può ricevere duplicati o perdere record. Inoltre, per valori di offset elevati, il database deve scorrere tutti i record precedenti, causando degradazione delle prestazioni con dataset molto grandi (il cosiddetto problema dello "deep pagination").

### Paginazione Cursor-Based

La paginazione cursor-based risolve i problemi della paginazione offset. Invece di un offset numerico, utilizza un cursore opaco (tipicamente un ID codificato in Base64) che punta a un record specifico nel dataset.

```
GET /api/v1/products?cursor=eyJpZCI6NDB9&limit=20
```

```json
{
  "data": [ /* 20 prodotti */ ],
  "pagination": {
    "limit": 20,
    "has_next": true,
    "next_cursor": "eyJpZCI6NjB9",
    "has_prev": true,
    "prev_cursor": "eyJpZCI6Mzl9"
  }
}
```

Il cursore è opaco per il client: non deve interpretarlo né costruirlo manualmente. Questo dà al server la libertà di cambiare la strategia di paginazione senza impattare i client. La paginazione cursor-based è la scelta consigliata per feed infiniti, timeline social e qualsiasi scenario con dataset grandi e in continuo aggiornamento. Lo svantaggio è che non consente di saltare direttamente a una pagina specifica.

### Paginazione Keyset

La paginazione **keyset** (detta anche "seek method") è la strategia di paginazione più performante a livello di database. Mentre la paginazione cursor-based definisce il contratto tra API e client (il cursore è un token opaco), la paginazione keyset descrive l'implementazione a livello di query: utilizza una clausola `WHERE` con operatori di confronto anziché `OFFSET`, consentendo al database di utilizzare gli indici per saltare direttamente al punto corretto nel dataset.

```sql
-- Offset-based (degrada con offset grandi)
SELECT * FROM products ORDER BY created_at DESC LIMIT 20 OFFSET 10000;
-- Il database deve scorrere e scartare 10000 righe prima di restituire le 20 desiderate

-- Keyset-based (prestazioni costanti indipendentemente dalla posizione)
SELECT * FROM products
WHERE (created_at, id) < ('2025-11-15T10:30:00Z', 'prod_abc')
ORDER BY created_at DESC, id DESC
LIMIT 20;
-- Il database usa l'indice su (created_at, id) per saltare direttamente al punto corretto
```

La paginazione keyset richiede un indice composto sulle colonne di ordinamento. Il cursore esposto all'API è tipicamente la codifica Base64 dei valori delle colonne di ordinamento dell'ultimo record restituito. La combinazione **cursor (API) + keyset (database)** è la strategia ottimale: il cursore opaco nasconde i dettagli implementativi al client, mentre il keyset garantisce prestazioni costanti O(log n) indipendentemente dalla posizione nel dataset.

Il principale svantaggio della paginazione keyset è che non supporta il salto a una pagina arbitraria (non esiste il concetto di "pagina 47") e richiede un ordinamento stabile su colonne indicizzate. Per dataset che richiedono navigazione libera per pagina (ad esempio un'interfaccia amministrativa con tabella paginata), la paginazione offset rimane l'alternativa pragmatica.

### Filtering e Sorting

Il filtraggio e l'ordinamento devono seguire convenzioni prevedibili e coerenti:

```
# Filtro semplice
GET /api/v1/products?category=electronics&status=available

# Filtro con operatori
GET /api/v1/products?price[gte]=10&price[lte]=100
GET /api/v1/products?created_at[after]=2025-01-01

# Ricerca testuale
GET /api/v1/products?search=laptop+gaming

# Ordinamento (prefisso - per discendente)
GET /api/v1/products?sort=price        # ascendente
GET /api/v1/products?sort=-price       # discendente
GET /api/v1/products?sort=-created_at,name  # multiplo

# Selezione campi (sparse fieldsets)
GET /api/v1/products?fields=id,name,price
```

La selezione dei campi (`fields`) è particolarmente utile per ridurre la dimensione delle risposte e migliorare le prestazioni, soprattutto per client mobile con banda limitata.

### Formato Errore RFC 7807

La RFC 7807 (Problem Details for HTTP APIs) definisce un formato standard per comunicare gli errori nelle API HTTP. Adottare questo standard elimina la necessità di inventare formati proprietari e facilita l'interoperabilità.

```json
{
  "type": "https://api.example.com/problems/validation-error",
  "title": "Errore di validazione",
  "status": 422,
  "detail": "La richiesta contiene campi non validi. Consulta il campo 'errors' per i dettagli.",
  "instance": "/api/v1/users",
  "errors": [
    {
      "field": "email",
      "message": "Formato email non valido",
      "rejected_value": "marco@@example"
    },
    {
      "field": "age",
      "message": "Il valore deve essere compreso tra 18 e 120",
      "rejected_value": -5
    }
  ]
}
```

I campi standard RFC 7807 sono:

- **`type`**: URI che identifica il tipo di problema. Dovrebbe puntare a documentazione leggibile.
- **`title`**: Descrizione breve e leggibile del tipo di problema. Non deve cambiare tra occorrenze diverse dello stesso tipo.
- **`status`**: Il codice di stato HTTP.
- **`detail`**: Spiegazione specifica per questa occorrenza del problema.
- **`instance`**: URI che identifica l'occorrenza specifica del problema (opzionale).

Il Content-Type della risposta deve essere `application/problem+json`.

### RFC 9457 — Evoluzione di Problem Details

La **RFC 9457** è il successore ufficiale della RFC 7807, pubblicata come Internet Standard (non più solo Proposed Standard). È **retrocompatibile** al 100%: qualsiasi implementazione conforme a RFC 7807 è automaticamente conforme a RFC 9457. Le principali novità introdotte dalla RFC 9457 includono:

- **Registrazione dei tipi di problema**: incoraggia l'uso di un registro di tipi di errore comuni per promuovere l'interoperabilità tra API diverse. Anziché inventare un URI `type` per ogni errore, le API possono riferirsi a tipi standard registrati presso IANA.
- **Chiarimenti sulla semantica di `type`**: il campo `type` con valore `about:blank` indica che il problema non ha semantica aggiuntiva oltre a quella del codice di stato HTTP. Questo è il valore predefinito quando `type` è omesso.
- **Estensioni tipizzate**: la specifica formalizza il meccanismo per estendere i Problem Details con campi aggiuntivi specifici del dominio (come il campo `errors` nell'esempio precedente), garantendo che le estensioni non conflicchino con i campi standard.
- **Supporto XML migliorato**: oltre al formato JSON (`application/problem+json`), la specifica definisce chiaramente il formato XML (`application/problem+xml`) per i contesti che lo richiedono.

L'adozione della RFC 9457 è raccomandata per tutte le nuove API. Per le API esistenti basate su RFC 7807, la migrazione è trasparente e non richiede modifiche al codice client.

---

## GraphQL

GraphQL, sviluppato da Facebook e rilasciato come open source nel 2015, è un linguaggio di query per API e un runtime per eseguire quelle query. A differenza di REST, dove il server definisce la struttura delle risposte, in GraphQL è il client a specificare esattamente quali dati necessita.

### Schema Definition Language

Lo schema è il contratto fondamentale di ogni API GraphQL. Definisce i tipi disponibili, le relazioni tra essi e le operazioni possibili.

```graphql
# Tipi scalari personalizzati
scalar DateTime
scalar Email

# Enum
enum UserRole {
  ADMIN
  EDITOR
  VIEWER
}

enum OrderStatus {
  PENDING
  CONFIRMED
  SHIPPED
  DELIVERED
  CANCELLED
}

# Tipi principali
type User {
  id: ID!
  name: String!
  email: Email!
  role: UserRole!
  avatar: String
  orders(first: Int = 10, after: String): OrderConnection!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type Product {
  id: ID!
  name: String!
  description: String
  price: Float!
  category: Category!
  inStock: Boolean!
}

type Category {
  id: ID!
  name: String!
  products(first: Int = 20, after: String): ProductConnection!
}

type Order {
  id: ID!
  user: User!
  items: [OrderItem!]!
  total: Float!
  status: OrderStatus!
  createdAt: DateTime!
}

type OrderItem {
  product: Product!
  quantity: Int!
  unitPrice: Float!
}

# Paginazione stile Relay (connection pattern)
type OrderConnection {
  edges: [OrderEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type OrderEdge {
  node: Order!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

# Input types
input CreateUserInput {
  name: String!
  email: Email!
  role: UserRole = VIEWER
}

input ProductFilterInput {
  category: ID
  minPrice: Float
  maxPrice: Float
  inStock: Boolean
  search: String
}
```

### Queries

Le query permettono ai client di richiedere esattamente i dati necessari, risolvendo il problema dell'over-fetching tipico delle REST API.

```graphql
# Query che richiede solo i campi necessari
query GetUserWithRecentOrders {
  user(id: "42") {
    name
    email
    orders(first: 5) {
      edges {
        node {
          id
          total
          status
          createdAt
          items {
            product {
              name
            }
            quantity
          }
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
    }
  }
}

# Query con variabili e direttive
query SearchProducts(
  $filter: ProductFilterInput
  $first: Int = 20
  $after: String
  $includeCategory: Boolean = false
) {
  products(filter: $filter, first: $first, after: $after) {
    edges {
      node {
        id
        name
        price
        inStock
        category @include(if: $includeCategory) {
          name
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
    totalCount
  }
}
```

### Mutations

Le mutation rappresentano operazioni di scrittura: creazione, aggiornamento ed eliminazione di dati.

```graphql
# Mutation per creare un utente
mutation CreateUser($input: CreateUserInput!) {
  createUser(input: $input) {
    user {
      id
      name
      email
      role
    }
    errors {
      field
      message
    }
  }
}

# Mutation per aggiornare lo stato di un ordine
mutation UpdateOrderStatus($orderId: ID!, $status: OrderStatus!) {
  updateOrderStatus(orderId: $orderId, status: $status) {
    order {
      id
      status
      updatedAt
    }
    errors {
      field
      message
    }
  }
}
```

Il pattern consigliato per le mutation prevede sempre di restituire sia l'oggetto modificato sia un array di errori, permettendo al client di gestire il risultato in modo uniforme indipendentemente dall'esito.

### Subscriptions

Le subscription abilitano la comunicazione in tempo reale, permettendo al client di ricevere aggiornamenti automatici quando si verificano eventi specifici sul server. Vengono implementate tipicamente tramite WebSocket.

```graphql
# Subscription per aggiornamenti sugli ordini
subscription OnOrderStatusChanged($userId: ID!) {
  orderStatusChanged(userId: $userId) {
    order {
      id
      status
      updatedAt
    }
    previousStatus
  }
}

# Subscription per nuovi messaggi in una chat
subscription OnNewMessage($channelId: ID!) {
  newMessage(channelId: $channelId) {
    id
    content
    sender {
      name
      avatar
    }
    createdAt
  }
}
```

### Resolvers

I resolver sono le funzioni che popolano i dati per ogni campo dello schema. Ogni campo dello schema ha un resolver corrispondente (anche se nella maggior parte dei casi il resolver predefinito è sufficiente).

```javascript
const resolvers = {
  Query: {
    user: async (parent, { id }, context) => {
      // Verifica autenticazione
      if (!context.currentUser) {
        throw new AuthenticationError('Autenticazione richiesta');
      }

      const user = await context.dataSources.userAPI.getUser(id);
      if (!user) {
        throw new UserInputError('Utente non trovato', {
          argumentName: 'id'
        });
      }
      return user;
    },

    products: async (parent, { filter, first, after }, context) => {
      return context.dataSources.productAPI.getProducts({
        filter,
        first,
        after
      });
    }
  },

  Mutation: {
    createUser: async (parent, { input }, context) => {
      try {
        const user = await context.dataSources.userAPI.createUser(input);
        return { user, errors: [] };
      } catch (error) {
        return {
          user: null,
          errors: [{ field: error.field, message: error.message }]
        };
      }
    }
  },

  // Resolver per campi relazionali — risolve il problema N+1
  User: {
    orders: async (user, { first, after }, context) => {
      // Utilizzo di DataLoader per batching automatico
      return context.dataSources.orderAPI.getOrdersByUser(
        user.id,
        { first, after }
      );
    }
  },

  Subscription: {
    orderStatusChanged: {
      subscribe: (parent, { userId }, context) => {
        return context.pubsub.asyncIterator(
          `ORDER_STATUS_${userId}`
        );
      }
    }
  }
};
```

### Apollo Server

Apollo Server è il server GraphQL più popolare nell'ecosistema JavaScript/TypeScript. Offre integrazione con Express, Fastify, AWS Lambda e altre piattaforme.

```javascript
import { ApolloServer } from '@apollo/server';
import { expressMiddleware } from '@apollo/server/express4';
import { makeExecutableSchema } from '@graphql-tools/schema';
import express from 'express';

const app = express();
const schema = makeExecutableSchema({ typeDefs, resolvers });

const server = new ApolloServer({ schema });
await server.start();

app.use(
  '/graphql',
  express.json(),
  expressMiddleware(server, {
    context: async ({ req }) => {
      const currentUser = await authenticateToken(req.headers.authorization);
      return {
        currentUser,
        dataSources: {
          userAPI: new UserAPI(),
          productAPI: new ProductAPI()
        }
      };
    }
  })
);

app.listen(4000, () => {
  console.log('Server GraphQL avviato su http://localhost:4000/graphql');
});
```

### Relay vs Apollo Client

La scelta del client GraphQL ha implicazioni significative sull'architettura dell'applicazione frontend.

**Apollo Client** è la scelta più comune per la sua flessibilità e curva di apprendimento accessibile. Offre un cache normalizzato, gestione ottimistica degli aggiornamenti e supporto completo per query, mutation e subscription. La sua API è intuitiva e si integra bene con qualsiasi framework frontend.

**Relay** (sviluppato da Meta) è più opinionato e richiede che lo schema GraphQL segua convenzioni specifiche: il connection pattern per la paginazione, identificatori globali univoci per tutti gli oggetti e node interface. In cambio, Relay offre prestazioni superiori grazie alla compilazione ahead-of-time delle query, gestione automatica della paginazione e un compilatore che ottimizza le query eliminando ridondanze.

| Caratteristica | Apollo Client | Relay |
|---------------|--------------|-------|
| Curva di apprendimento | Graduale | Ripida |
| Flessibilità schema | Alta | Richiede convenzioni specifiche |
| Paginazione | Manuale | Automatica con connection pattern |
| Compilazione query | Runtime | Ahead-of-time |
| Dimensione bundle | ~33 KB (gzip) | ~27 KB (gzip) |
| Framework | Qualsiasi | Ottimizzato per React |
| Adatto per | Progetti di tutte le dimensioni | Applicazioni React su larga scala |

---

## gRPC

gRPC (Google Remote Procedure Call) è un framework RPC ad alte prestazioni sviluppato da Google. Utilizza HTTP/2 come protocollo di trasporto e Protocol Buffers come formato di serializzazione, offrendo prestazioni significativamente superiori rispetto alle API REST basate su JSON.

### Protocol Buffers

Protocol Buffers (protobuf) è un meccanismo di serializzazione binaria language-neutral e platform-neutral. I messaggi protobuf sono più compatti e veloci da serializzare/deserializzare rispetto a JSON.

```protobuf
// user_service.proto
syntax = "proto3";

package ecommerce;

import "google/protobuf/timestamp.proto";
import "google/protobuf/empty.proto";

// Enum per il ruolo utente
enum UserRole {
  USER_ROLE_UNSPECIFIED = 0;
  USER_ROLE_ADMIN = 1;
  USER_ROLE_EDITOR = 2;
  USER_ROLE_VIEWER = 3;
}

// Messaggio User
message User {
  string id = 1;
  string name = 2;
  string email = 3;
  UserRole role = 4;
  google.protobuf.Timestamp created_at = 5;
  google.protobuf.Timestamp updated_at = 6;
}

// Request e Response messages
message GetUserRequest {
  string id = 1;
}

message ListUsersRequest {
  int32 page_size = 1;
  string page_token = 2;
  string filter = 3;
}

message ListUsersResponse {
  repeated User users = 1;
  string next_page_token = 2;
  int32 total_count = 3;
}

message CreateUserRequest {
  string name = 1;
  string email = 2;
  UserRole role = 3;
}

```

Ogni campo ha un numero identificativo univoco (field number) che viene utilizzato nella codifica binaria. Una volta assegnato, questo numero non deve mai essere cambiato per mantenere la retrocompatibilità.

### Service Definition

I servizi gRPC definiscono i metodi RPC disponibili, ciascuno con il tipo di request e response.

```protobuf
// Definizione del servizio
service UserService {
  // Unary RPC — richiesta singola, risposta singola
  rpc GetUser(GetUserRequest) returns (User);
  rpc CreateUser(CreateUserRequest) returns (User);
  rpc UpdateUser(UpdateUserRequest) returns (User);
  rpc DeleteUser(GetUserRequest) returns (google.protobuf.Empty);

  // Server streaming — il server invia un flusso di risposte
  rpc ListUsers(ListUsersRequest) returns (stream User);

  // Client streaming — il client invia un flusso di richieste
  rpc UploadUserPhotos(stream UploadPhotoRequest) returns (UploadPhotoResponse);

  // Bidirectional streaming — flusso bidirezionale
  rpc Chat(stream ChatMessage) returns (stream ChatMessage);
}

message UploadPhotoRequest {
  string user_id = 1;
  bytes photo_data = 2;
  string filename = 3;
}

message UploadPhotoResponse {
  int32 uploaded_count = 1;
  repeated string photo_urls = 2;
}

message ChatMessage {
  string sender_id = 1;
  string content = 2;
  google.protobuf.Timestamp timestamp = 3;
}
```

### Streaming

gRPC supporta quattro pattern di comunicazione, e lo streaming è ciò che lo distingue maggiormente da REST:

**Unary RPC** è il pattern classico: una richiesta, una risposta. Equivale a una chiamata HTTP tradizionale.

**Server streaming** consente al server di inviare un flusso continuo di messaggi in risposta a una singola richiesta del client. Utile per scaricare dataset grandi, ricevere aggiornamenti in tempo reale o log streaming.

**Client streaming** permette al client di inviare un flusso di messaggi al server, che risponde con un singolo messaggio al termine. Utile per upload di file in chunk o invio di dati telemetrici in batch.

**Bidirectional streaming** consente a entrambe le parti di inviare flussi di messaggi indipendentemente. Le due parti possono leggere e scrivere in qualsiasi ordine, ideale per chat, giochi multiplayer o scenari di comunicazione bidirezionale continua.

```javascript
// Implementazione Node.js con @grpc/grpc-js
import grpc from '@grpc/grpc-js';
import protoLoader from '@grpc/proto-loader';

const packageDefinition = protoLoader.loadSync('user_service.proto', {
  keepCase: true,
  longs: String,
  enums: String,
  defaults: true,
  oneofs: true
});

const proto = grpc.loadPackageDefinition(packageDefinition).ecommerce;

// Implementazione del server
const server = new grpc.Server();

server.addService(proto.UserService.service, {
  // Unary
  getUser: async (call, callback) => {
    try {
      const user = await db.users.findById(call.request.id);
      callback(null, user);
    } catch (error) {
      callback({
        code: grpc.status.NOT_FOUND,
        message: `Utente ${call.request.id} non trovato`
      });
    }
  },

  // Server streaming
  listUsers: async (call) => {
    const users = await db.users.find(call.request.filter);
    for (const user of users) {
      call.write(user);
    }
    call.end();
  },

  // Bidirectional streaming
  chat: (call) => {
    call.on('data', (message) => {
      // Broadcast a tutti i client connessi
      const response = {
        sender_id: message.sender_id,
        content: message.content,
        timestamp: { seconds: Date.now() / 1000 }
      };
      call.write(response);
    });

    call.on('end', () => {
      call.end();
    });
  }
});

server.bindAsync(
  '0.0.0.0:50051',
  grpc.ServerCredentials.createInsecure(),
  () => { server.start(); }
);
```

### Deadline e Timeout

I **deadline** sono uno degli aspetti più critici e meno compresi di gRPC. Un deadline specifica il tempo massimo che un client è disposto ad attendere per il completamento di una RPC. Se la RPC non si completa entro il deadline, viene terminata con l'errore `DEADLINE_EXCEEDED`. A differenza dei timeout HTTP tradizionali, i deadline gRPC vengono **propagati** automaticamente attraverso la catena di servizi: se il servizio A chiama il servizio B che chiama il servizio C, il deadline originale viene rispettato lungo l'intera catena, prevenendo sprechi di risorse su operazioni che il client ha già abbandonato.

```javascript
// Client — impostare un deadline di 5 secondi
const deadline = new Date();
deadline.setSeconds(deadline.getSeconds() + 5);

client.getUser({ id: '42' }, { deadline }, (error, response) => {
  if (error && error.code === grpc.status.DEADLINE_EXCEEDED) {
    console.error('La richiesta ha superato il tempo massimo');
  }
});
```

La regola fondamentale è: **impostare sempre un deadline**. Una RPC senza deadline può rimanere in attesa indefinitamente, consumando risorse sul server e rendendo il sistema fragile. I deadline devono essere calibrati in base alla complessità dell'operazione: operazioni semplici di lettura possono avere deadline di 1-3 secondi, operazioni di scrittura 5-10 secondi, e operazioni batch o di aggregazione 30-60 secondi.

### Interceptor

Gli interceptor in gRPC sono l'equivalente dei middleware in Express: funzioni che intercettano le chiamate RPC per eseguire logica trasversale come logging, autenticazione, metriche e tracing. gRPC supporta interceptor sia lato client che lato server, e il loro ordine di esecuzione è determinato dall'ordine di registrazione.

```javascript
// Interceptor di logging lato server
function loggingInterceptor(methodDescriptor, call) {
  const startTime = Date.now();
  const method = methodDescriptor.path;

  // Wrappare il callback originale per intercettare la risposta
  const originalHandler = methodDescriptor.handler;
  return function(call, callback) {
    const wrappedCallback = (error, response) => {
      const duration = Date.now() - startTime;
      const status = error ? error.code : grpc.status.OK;
      console.log(JSON.stringify({
        method,
        status,
        duration_ms: duration,
        timestamp: new Date().toISOString()
      }));
      callback(error, response);
    };
    originalHandler(call, wrappedCallback);
  };
}

// Interceptor di autenticazione tramite metadata
function authInterceptor(call, callback) {
  const metadata = call.metadata;
  const token = metadata.get('authorization')[0];

  if (!token) {
    callback({
      code: grpc.status.UNAUTHENTICATED,
      message: 'Token di autenticazione mancante'
    });
    return;
  }

  try {
    const user = verifyToken(token);
    // Propagare l'identità nei metadata per i servizi downstream
    call.metadata.set('x-user-id', user.id);
    callback(null);
  } catch (err) {
    callback({
      code: grpc.status.UNAUTHENTICATED,
      message: 'Token non valido o scaduto'
    });
  }
}
```

Gli interceptor comuni in un'architettura gRPC di produzione includono: logging strutturato di ogni chiamata RPC, propagazione dei trace ID per il distributed tracing, validazione dei token di autenticazione, raccolta di metriche (latenza, tasso di errore per metodo), e circuit breaking per prevenire cascade failure.

### Metadata

I metadata in gRPC sono l'equivalente degli header HTTP: coppie chiave-valore che accompagnano le richieste e le risposte RPC. I metadata vengono utilizzati per trasmettere informazioni contestuali come token di autenticazione, request ID, informazioni di tracing e configurazioni specifiche della richiesta. A differenza dei dati nel body del messaggio protobuf, i metadata non richiedono una definizione nello schema e possono essere aggiunti dinamicamente.

```javascript
// Client — inviare metadata con la richiesta
const metadata = new grpc.Metadata();
metadata.set('authorization', `Bearer ${token}`);
metadata.set('x-request-id', crypto.randomUUID());
metadata.set('x-client-version', '2.1.0');

client.getUser({ id: '42' }, metadata, (error, response) => {
  // gestire la risposta
});

// Server — leggere e propagare metadata
function getUser(call, callback) {
  const requestId = call.metadata.get('x-request-id')[0];
  const clientVersion = call.metadata.get('x-client-version')[0];

  // Metadata di risposta (trailer)
  const responseMetadata = new grpc.Metadata();
  responseMetadata.set('x-request-id', requestId);
  responseMetadata.set('x-processing-time-ms', '12');
  call.sendMetadata(responseMetadata);

  // logica di business...
}
```

### Health Checking

gRPC definisce un protocollo standard di health checking (specifica `grpc.health.v1.Health`) che permette ai load balancer e agli orchestratori (Kubernetes, Envoy) di verificare lo stato di salute dei servizi gRPC. Il servizio di health checking espone un metodo `Check` che restituisce lo stato del servizio: `SERVING` (pronto), `NOT_SERVING` (non disponibile) o `UNKNOWN`.

```protobuf
// health.proto — specifica standard gRPC
syntax = "proto3";
package grpc.health.v1;

message HealthCheckRequest {
  string service = 1;
}

message HealthCheckResponse {
  enum ServingStatus {
    UNKNOWN = 0;
    SERVING = 1;
    NOT_SERVING = 2;
  }
  ServingStatus status = 1;
}

service Health {
  rpc Check(HealthCheckRequest) returns (HealthCheckResponse);
  rpc Watch(HealthCheckRequest) returns (stream HealthCheckResponse);
}
```

Il metodo `Watch` permette ai client di ricevere aggiornamenti continui sullo stato di salute, consentendo reazioni immediate ai cambiamenti senza polling. Ogni servizio dovrebbe implementare il health checking e verificare le proprie dipendenze critiche (database, cache, servizi upstream) nel metodo `Check`.

---

## WebSocket

Il protocollo WebSocket (RFC 6455) stabilisce un canale di comunicazione bidirezionale full-duplex su una singola connessione TCP. A differenza di HTTP, dove ogni interazione richiede una nuova richiesta, WebSocket mantiene una connessione persistente che permette a server e client di scambiare messaggi in qualsiasi momento.

### Protocollo

La connessione WebSocket inizia con un handshake HTTP, dopodiché il protocollo viene "upgradata" a WebSocket:

```
// Richiesta di upgrade del client
GET /chat HTTP/1.1
Host: api.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13

// Risposta del server
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

Dopo l'handshake, la comunicazione avviene tramite frame binari leggeri, con overhead minimo (2-14 byte per frame rispetto agli header HTTP che possono superare i 700 byte).

### Casi d'Uso

WebSocket è la scelta ottimale per scenari che richiedono comunicazione in tempo reale a bassa latenza:

- **Chat e messaggistica**: messaggi istantanei, indicatori di digitazione, stato di lettura.
- **Notifiche push**: aggiornamenti in tempo reale senza polling.
- **Dashboard live**: grafici e metriche aggiornati in tempo reale.
- **Collaborazione in tempo reale**: editor collaborativi, whiteboard condivise.
- **Gaming multiplayer**: sincronizzazione dello stato di gioco tra i giocatori.
- **Trading finanziario**: aggiornamenti dei prezzi in tempo reale, esecuzione ordini.
- **IoT**: streaming di dati da sensori e dispositivi.

### Socket.IO

Socket.IO è una libreria che astrae WebSocket aggiungendo funzionalità essenziali per applicazioni di produzione: riconnessione automatica, fallback a HTTP long-polling, rooms e namespaces per organizzare la comunicazione, e acknowledgement per confermare la ricezione dei messaggi.

```javascript
// Server — socket-io-server.js
import { Server } from 'socket.io';
import { createServer } from 'http';
import express from 'express';

const app = express();
const httpServer = createServer(app);

const io = new Server(httpServer, {
  cors: {
    origin: 'https://app.example.com',
    methods: ['GET', 'POST']
  },
  pingInterval: 25000,
  pingTimeout: 20000
});

// Middleware di autenticazione
io.use(async (socket, next) => {
  const token = socket.handshake.auth.token;
  try {
    const user = await verifyToken(token);
    socket.data.user = user;
    next();
  } catch (err) {
    next(new Error('Autenticazione fallita'));
  }
});

// Namespace per la chat
const chatNamespace = io.of('/chat');

chatNamespace.on('connection', (socket) => {
  console.log(`Utente connesso: ${socket.data.user.name}`);

  // Entrare in una room
  socket.on('join:room', async (roomId, callback) => {
    socket.join(roomId);
    const history = await getMessageHistory(roomId, 50);
    callback({ status: 'ok', history });
  });

  // Invio messaggio con acknowledgement
  socket.on('message:send', async (data, callback) => {
    const message = {
      id: generateId(),
      content: data.content,
      sender: socket.data.user,
      roomId: data.roomId,
      timestamp: new Date()
    };

    await saveMessage(message);

    // Broadcast a tutti nella room tranne il mittente
    socket.to(data.roomId).emit('message:new', message);

    // Conferma al mittente
    callback({ status: 'ok', messageId: message.id });
  });

  // Indicatore di digitazione
  socket.on('typing:start', (roomId) => {
    socket.to(roomId).emit('typing:update', {
      user: socket.data.user.name,
      isTyping: true
    });
  });

  socket.on('disconnect', (reason) => {
    console.log(`Utente disconnesso: ${reason}`);
  });
});

httpServer.listen(3000);
```

```javascript
// Client — socket-io-client.js
import { io } from 'socket.io-client';

const socket = io('https://api.example.com/chat', {
  auth: { token: 'jwt-token-here' },
  reconnection: true,
  reconnectionAttempts: 10,
  reconnectionDelay: 1000
});

socket.on('connect', () => {
  socket.emit('join:room', 'room-123', (response) => {
    console.log('Messaggi precedenti:', response.history);
  });
});

socket.on('message:new', (message) => {
  displayMessage(message);
});

socket.emit('message:send',
  { roomId: 'room-123', content: 'Ciao a tutti!' },
  (response) => {
    if (response.status === 'ok') markAsSent(response.messageId);
  }
);
```

---

## OpenAPI / Swagger

OpenAPI Specification (OAS) è lo standard de facto per descrivere le REST API in modo machine-readable. Originariamente noto come Swagger Specification, è stato donato alla OpenAPI Initiative (sotto la Linux Foundation) nel 2015. La versione corrente è la 3.1, che allinea lo schema dei dati con JSON Schema.

### Specifica

Un documento OpenAPI descrive completamente un'API: endpoint, parametri, formati di richiesta e risposta, autenticazione e metadati.

```yaml
# openapi.yaml
openapi: 3.1.0

info:
  title: E-Commerce API
  description: API per la gestione di un e-commerce
  version: 1.2.0
  contact:
    name: Team API
    email: api@example.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://api.example.com/v1
    description: Produzione
  - url: https://staging-api.example.com/v1
    description: Staging
  - url: http://localhost:3000/v1
    description: Sviluppo locale

tags:
  - name: Users
    description: Gestione utenti
  - name: Products
    description: Catalogo prodotti

security:
  - BearerAuth: []

paths:
  /users:
    get:
      tags: [Users]
      summary: Lista utenti
      description: Restituisce una lista paginata di utenti
      operationId: listUsers
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            minimum: 1
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
        - name: role
          in: query
          schema:
            $ref: '#/components/schemas/UserRole'
      responses:
        '200':
          description: Lista utenti restituita con successo
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: array
                    items:
                      $ref: '#/components/schemas/User'
                  pagination:
                    $ref: '#/components/schemas/Pagination'
        '401':
          $ref: '#/components/responses/Unauthorized'

    post:
      tags: [Users]
      summary: Crea utente
      operationId: createUser
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateUserRequest'
      responses:
        '201':
          description: Utente creato con successo
          headers:
            Location:
              schema:
                type: string
              description: URI della risorsa creata
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/User'
        '422':
          $ref: '#/components/responses/ValidationError'

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    User:
      type: object
      required: [id, name, email, role]
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
          minLength: 2
          maxLength: 100
        email:
          type: string
          format: email
        role:
          $ref: '#/components/schemas/UserRole'
        createdAt:
          type: string
          format: date-time

    UserRole:
      type: string
      enum: [admin, editor, viewer]

    CreateUserRequest:
      type: object
      required: [name, email]
      properties:
        name:
          type: string
          minLength: 2
        email:
          type: string
          format: email
        role:
          $ref: '#/components/schemas/UserRole'
          default: viewer

    Pagination:
      type: object
      properties:
        page:
          type: integer
        limit:
          type: integer
        total:
          type: integer
        totalPages:
          type: integer

    ProblemDetail:
      type: object
      properties:
        type:
          type: string
          format: uri
        title:
          type: string
        status:
          type: integer
        detail:
          type: string
        instance:
          type: string

  responses:
    Unauthorized:
      description: Autenticazione richiesta
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetail'
    ValidationError:
      description: Errore di validazione
      content:
        application/problem+json:
          schema:
            $ref: '#/components/schemas/ProblemDetail'
```

### Code Generation

Uno dei vantaggi più significativi di OpenAPI è la possibilità di generare codice automaticamente dalla specifica. Questo approccio, noto come **contract-first** o **API-first**, garantisce che l'implementazione sia sempre allineata con la documentazione.

Strumenti principali per la generazione di codice:

- **openapi-generator**: genera client SDK in oltre 50 linguaggi, server stubs e documentazione.
- **swagger-codegen**: il generatore originale, supporta numerosi linguaggi.
- **orval**: specializzato per TypeScript, genera client con integrazione React Query o SWR.
- **openapi-typescript**: genera tipi TypeScript dallo schema OpenAPI.

```bash
# Generare un client TypeScript con openapi-generator
npx openapi-generator-cli generate \
  -i openapi.yaml \
  -g typescript-axios \
  -o ./generated/api-client

# Generare tipi TypeScript con openapi-typescript
npx openapi-typescript openapi.yaml -o ./src/types/api.d.ts

# Generare client con React Query hooks tramite orval
npx orval --config orval.config.ts
```

**Orval** merita un approfondimento perché genera non solo i tipi TypeScript ma anche hook React Query (o SWR, Vue Query, Angular) pronti all'uso, client Axios tipizzati, mock MSW (Mock Service Worker) per il testing, e validatori Zod dallo schema. Questo approccio elimina completamente il boilerplate di data fetching, garantendo che il codice frontend sia sempre sincronizzato con la specifica API.

**OpenAPI 3.1** introduce allineamento completo con JSON Schema Draft 2020-12, che abilita funzionalità come `nullable` sostituito da `type: ["string", "null"]`, il supporto nativo per `$dynamicRef` e `$dynamicAnchor`, la possibilità di usare `const` per valori fissi, e il supporto per `prefixItems` negli array. Questa convergenza con JSON Schema significa che gli strumenti di validazione JSON Schema possono essere utilizzati direttamente sugli schemi OpenAPI 3.1 senza adattamenti.

### Documentazione

Il documento OpenAPI alimenta strumenti di documentazione interattiva che permettono agli sviluppatori di esplorare e testare l'API direttamente dal browser:

- **Swagger UI**: l'interfaccia classica, permette di eseguire richieste direttamente dalla documentazione.
- **Redoc**: documentazione elegante in formato a tre colonne, ottima per API pubbliche.
- **Scalar**: alternativa moderna a Swagger UI con un'interfaccia più curata, temi personalizzabili, client HTTP integrato e supporto nativo per OpenAPI 3.1. Particolarmente popolare nel 2024-2025 per la qualità dell'esperienza sviluppatore e la facilità di integrazione in framework come .NET, Fastify e Express.
- **Stoplight Elements**: componenti React per incorporare la documentazione in qualsiasi applicazione web.

L'approccio consigliato è mantenere la specifica OpenAPI come single source of truth e generare automaticamente sia la documentazione sia il codice da essa. Questo elimina lo scollamento tra documentazione e implementazione, un problema cronico nello sviluppo di API.

---

## API Gateway

Un API Gateway è un componente architetturale che funge da punto di ingresso unico per tutte le richieste verso i servizi backend. Centralizza funzionalità trasversali che altrimenti dovrebbero essere implementate individualmente in ogni servizio.

### Rate Limiting

Il rate limiting protegge i servizi backend dal sovraccarico imponendo limiti al numero di richieste che un client può effettuare in un intervallo di tempo. L'API Gateway comunica lo stato del rate limit tramite header standard:

```
HTTP/1.1 200 OK
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 742
X-RateLimit-Reset: 1703980800

# Quando il limite viene superato:
HTTP/1.1 429 Too Many Requests
Retry-After: 45
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1703980800
```

Gli algoritmi di rate limiting più comuni sono:

- **Fixed Window**: conta le richieste in finestre temporali fisse (es. 1000 richieste/minuto). Semplice ma soggetto a burst al confine tra due finestre.
- **Sliding Window**: calcola il rate su una finestra mobile, eliminando il problema dei burst al confine. Più preciso ma richiede più risorse.
- **Token Bucket**: il client dispone di un "secchio" di token che si riempie a un rate costante. Ogni richiesta consuma un token. Permette burst controllati.
- **Leaky Bucket**: le richieste entrano in una coda che viene svuotata a rate costante. Garantisce un output uniforme ma può introdurre latenza.

### Autenticazione

L'API Gateway centralizza la validazione dell'autenticazione, evitando che ogni microservizio debba implementare la propria logica di verifica dei token. Tipicamente, il gateway valida il JWT o l'API key, e inoltra ai servizi backend un header con l'identità dell'utente autenticato.

```
Client → API Gateway (valida JWT) → Backend Service (riceve X-User-Id header)
```

Questo pattern semplifica enormemente i servizi backend che possono fidarsi dell'identità fornita dal gateway senza dover accedere al servizio di autenticazione.

### Load Balancing

L'API Gateway distribuisce il traffico tra multiple istanze dei servizi backend utilizzando diverse strategie:

- **Round Robin**: distribuisce le richieste ciclicamente tra le istanze disponibili. Semplice ed efficace quando le istanze hanno capacità simili.
- **Least Connections**: inoltra la richiesta all'istanza con meno connessioni attive. Ideale quando le richieste hanno durata variabile.
- **Weighted Round Robin**: assegna pesi diversi alle istanze in base alla loro capacità, indirizzando più traffico verso le istanze più potenti.
- **IP Hash**: utilizza l'indirizzo IP del client per determinare l'istanza di destinazione, garantendo session affinity.
- **Health Check**: monitora continuamente lo stato delle istanze e rimuove automaticamente dal pool quelle non responsive.

Soluzioni API Gateway diffuse includono Kong, AWS API Gateway, Azure API Management, NGINX e Envoy.

### Pattern Backend-for-Frontend (BFF)

Il pattern **Backend-for-Frontend** (BFF) prevede la creazione di un servizio backend dedicato per ogni tipo di client (web, mobile, IoT). Invece di avere un unico API gateway monolitico che serve tutti i client, ogni BFF è ottimizzato per le esigenze specifiche del suo client: il BFF mobile restituisce payload compatti con i campi essenziali, il BFF web fornisce dati ricchi per dashboard complesse, il BFF IoT gestisce comunicazione a basso consumo di banda.

```
Browser Web ─── BFF Web ──┐
                           ├── Microservizio Utenti
App Mobile ─── BFF Mobile ─┤
                           ├── Microservizio Ordini
Dashboard ─── BFF Admin ───┘
                           └── Microservizio Prodotti
```

Ogni BFF aggrega le chiamate a microservizi multipli, trasforma i dati nel formato ottimale per il client e gestisce la logica specifica del client (caching, gestione sessione, retry policy). Il vantaggio principale è l'indipendenza: il team mobile può evolvere il proprio BFF senza impattare il team web e viceversa. Lo svantaggio è la duplicazione potenziale di logica tra i BFF, mitigabile con librerie condivise per la logica di dominio comune.

### Pattern di Aggregazione

Il gateway di aggregazione combina risposte da microservizi multipli in una singola risposta per il client, riducendo il numero di round-trip di rete. Questo pattern è particolarmente utile quando una singola vista dell'interfaccia utente richiede dati da servizi diversi.

```javascript
// Gateway di aggregazione — composizione di risposte
app.get('/api/v1/dashboard', async (req, res) => {
  // Chiamate parallele ai microservizi
  const [userProfile, recentOrders, recommendations] = await Promise.all([
    fetch('http://user-service/users/me'),
    fetch('http://order-service/orders?limit=5'),
    fetch('http://recommendation-service/for-user/me'),
  ]);

  // Composizione in una singola risposta ottimizzata
  res.json({
    user: await userProfile.json(),
    recentOrders: await recentOrders.json(),
    recommendations: await recommendations.json(),
  });
});
```

Il gateway di aggregazione deve implementare timeout indipendenti per ciascun servizio downstream e strategie di degradazione graceful: se il servizio raccomandazioni non risponde, il dashboard viene comunque restituito con la sezione raccomandazioni vuota o con dati di fallback.

### Sidecar Proxy

Il pattern **sidecar** distribuisce le funzionalità del gateway a livello di singolo servizio, anziché centralizzarle in un punto di ingresso unico. Ogni microservizio viene deployato con un proxy sidecar (tipicamente Envoy) che gestisce trasversalmente autenticazione, TLS termination, rate limiting, circuit breaking, retry e osservabilità. L'insieme dei sidecar proxy forma un **service mesh** (come Istio o Linkerd) che offre le stesse funzionalità di un gateway centralizzato ma in modo distribuito e senza single point of failure.

---

## Autenticazione API

L'autenticazione è il processo di verifica dell'identità di chi effettua una richiesta API. Diversi meccanismi offrono livelli differenti di sicurezza, complessità e flessibilità.

### API Key

Le API Key sono il meccanismo più semplice: una stringa segreta inclusa in ogni richiesta, tipicamente come header.

```
GET /api/v1/products HTTP/1.1
Host: api.example.com
X-API-Key: sk_live_a1b2c3d4e5f6g7h8i9j0
```

Le API Key sono adatte per l'autenticazione server-to-server e per identificare l'applicazione chiamante piuttosto che l'utente finale. Sono semplici da implementare e gestire, ma non devono mai essere esposte nel codice frontend poiché chiunque le possieda può impersonare il client. Le API Key devono essere trasmesse esclusivamente tramite HTTPS e ruotate periodicamente.

### JWT (JSON Web Token)

JWT è uno standard (RFC 7519) per creare token di accesso che incorporano claim (affermazioni) sull'utente in formato JSON, firmati crittograficamente per garantirne l'integrità.

```
// Struttura JWT: Header.Payload.Signature

// Header (Base64URL)
{
  "alg": "RS256",
  "typ": "JWT",
  "kid": "key-2025-01"
}

// Payload (Base64URL)
{
  "sub": "user-42",
  "name": "Marco Rossi",
  "email": "marco@example.com",
  "roles": ["admin", "editor"],
  "iat": 1703894400,
  "exp": 1703898000,
  "iss": "https://auth.example.com",
  "aud": "https://api.example.com"
}

// Utilizzo nell'header Authorization
GET /api/v1/users HTTP/1.1
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

La scelta dell'algoritmo di firma è cruciale. **HS256** (HMAC con SHA-256) utilizza una chiave simmetrica condivisa tra chi emette e chi verifica il token. **RS256** (RSA con SHA-256) utilizza una coppia di chiavi asimmetrica: la chiave privata firma il token, la chiave pubblica lo verifica. RS256 è preferibile in architetture distribuite perché solo il server di autenticazione possiede la chiave privata, mentre i servizi che verificano il token necessitano solo della chiave pubblica.

Un pattern fondamentale è l'uso di **access token** (breve durata, 15-60 minuti) combinati con **refresh token** (lunga durata, giorni/settimane). Quando l'access token scade, il client utilizza il refresh token per ottenerne uno nuovo senza richiedere all'utente di autenticarsi nuovamente.

### OAuth 2.0

OAuth 2.0 (RFC 6749) è un framework di autorizzazione che permette a un'applicazione terza di ottenere accesso limitato a un servizio HTTP, per conto dell'utente proprietario della risorsa oppure per conto proprio.

I quattro ruoli definiti da OAuth 2.0 sono:

- **Resource Owner**: l'utente che possiede i dati e autorizza l'accesso.
- **Client**: l'applicazione che richiede accesso alle risorse.
- **Authorization Server**: emette i token dopo aver autenticato l'utente e ottenuto il suo consenso.
- **Resource Server**: ospita le risorse protette e accetta i token di accesso.

Il flusso più sicuro e consigliato per le applicazioni web moderne è l'**Authorization Code Flow con PKCE** (Proof Key for Code Exchange):

```
1. Il client genera un code_verifier casuale e il suo code_challenge (SHA-256)
2. Il client reindirizza l'utente all'Authorization Server con il code_challenge
3. L'utente si autentica e autorizza l'accesso
4. L'Authorization Server restituisce un authorization_code al client
5. Il client scambia il code + code_verifier per un access_token
6. L'Authorization Server verifica il code_verifier e emette i token
```

```
// Passo 2 — Richiesta di autorizzazione
GET https://auth.example.com/authorize?
  response_type=code&
  client_id=app-123&
  redirect_uri=https://app.example.com/callback&
  scope=read:users write:orders&
  state=random-csrf-token&
  code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM&
  code_challenge_method=S256

// Passo 5 — Scambio del code per il token
POST https://auth.example.com/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=AUTH_CODE_RECEIVED&
redirect_uri=https://app.example.com/callback&
client_id=app-123&
code_verifier=dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk
```

### OpenID Connect (OIDC)

OpenID Connect è un layer di identità costruito sopra OAuth 2.0. Mentre OAuth 2.0 gestisce solo l'autorizzazione (cosa il client puo fare), OIDC aggiunge l'autenticazione (chi e l'utente).

OIDC introduce il concetto di **ID Token**, un JWT che contiene informazioni sull'identità dell'utente autenticato:

```json
{
  "iss": "https://auth.example.com",
  "sub": "user-42",
  "aud": "app-123",
  "exp": 1703898000,
  "iat": 1703894400,
  "nonce": "random-nonce",
  "name": "Marco Rossi",
  "email": "marco@example.com",
  "email_verified": true,
  "picture": "https://example.com/avatar/42.jpg"
}
```

OIDC definisce anche un endpoint standard **UserInfo** (`/.well-known/openid-configuration`) che permette di ottenere informazioni aggiuntive sull'utente e un endpoint di **discovery** che descrive tutti gli endpoint e le capacità del provider. Questo meccanismo di discovery rende OIDC particolarmente adatto per scenari di federazione dell'identità.

### Mutual TLS (mTLS)

Il **Mutual TLS** (mTLS) estende il TLS standard richiedendo che sia il server che il client presentino un certificato X.509 durante l'handshake. Nel TLS tradizionale, solo il server dimostra la propria identità al client; con mTLS, entrambe le parti si autenticano reciprocamente. Questo meccanismo è fondamentale per la comunicazione **zero-trust** tra microservizi e per le API ad alta sicurezza (finanza, sanità, infrastruttura critica).

```
Handshake mTLS:
1. Client → Server: ClientHello
2. Server → Client: ServerHello + Certificato Server
3. Server → Client: CertificateRequest (richiede il certificato client)
4. Client → Server: Certificato Client + ClientKeyExchange
5. Server verifica il certificato client contro la CA fidata
6. Connessione stabilita — entrambe le parti autenticate
```

mTLS è complementare a OAuth 2.0: mTLS verifica **chi** è il client (identità a livello di trasporto), mentre OAuth verifica **cosa** il client è autorizzato a fare (autorizzazione a livello applicativo). Il pattern **certificate-bound access token** (RFC 8705) combina i due meccanismi: il token di accesso OAuth è legato crittograficamente al certificato TLS del client, rendendo il token inutilizzabile se presentato da un client con un certificato diverso.

I certificati client per mTLS devono avere durata breve (ore o giorni, non anni), essere emessi da una Certificate Authority interna dedicata, essere ruotati automaticamente (con strumenti come cert-manager in Kubernetes o Vault PKI), e mai condivisi tra servizi diversi — ogni servizio deve avere il proprio certificato con un Subject distinto.

### OAuth Scopes — Progettazione Granulare

Gli **scope** OAuth definiscono i permessi specifici che un token di accesso concede. La progettazione degli scope è un aspetto critico della sicurezza dell'API: scope troppo ampi violano il principio del privilegio minimo, scope troppo granulari rendono l'UX di autorizzazione confusa e l'implementazione complessa.

La convenzione più diffusa utilizza il formato `risorsa:azione`:

```
read:users          — leggere profili utente
write:users         — creare e aggiornare utenti
delete:users        — eliminare utenti
read:orders         — leggere ordini
write:orders        — creare ordini
admin:users         — operazioni amministrative sugli utenti
```

Le best practice per la progettazione degli scope includono: seguire una gerarchia logica dove `admin:users` implica `write:users` che implica `read:users`; documentare esplicitamente ogni scope nella specifica OpenAPI; richiedere solo gli scope strettamente necessari durante l'autorizzazione (principio del privilegio minimo); validare gli scope su ogni endpoint, non solo al momento dell'emissione del token; utilizzare scope separati per operazioni sensibili (ad esempio `write:payments` distinto da `write:orders`).

---

## Versionamento

Il versionamento delle API e fondamentale per evolverle senza rompere i client esistenti. Esistono tre strategie principali, ciascuna con compromessi diversi.

### URL Path Versioning

La versione è parte dell'URL path. È la strategia più comune e visibile.

```
GET /api/v1/users
GET /api/v2/users
```

**Vantaggi**: immediatamente visibile, facile da capire, semplice da implementare routing e caching, permette di eseguire versioni diverse in parallelo.

**Svantaggi**: viola il principio REST secondo cui un URI dovrebbe identificare una risorsa (non la sua versione), richiede aggiornamento di tutti i link nei client quando si migra a una nuova versione.

### Header Versioning

La versione è specificata in un header HTTP personalizzato.

```
GET /api/users HTTP/1.1
Host: api.example.com
Accept: application/vnd.example.v2+json

# Oppure con header personalizzato
GET /api/users HTTP/1.1
X-API-Version: 2
```

**Vantaggi**: gli URI rimangono puliti e stabili, segue meglio i principi REST, la versione è metadata della richiesta.

**Svantaggi**: meno visibile e più difficile da testare (non si può semplicemente incollare l'URL nel browser), complicata la configurazione del caching, richiede che il client gestisca gli header.

### Query Parameter Versioning

La versione è un query parameter.

```
GET /api/users?version=2
```

**Vantaggi**: facile da aggiungere senza cambiare la struttura degli URL, si può testare direttamente dal browser.

**Svantaggi**: può confondersi con i parametri di query funzionali, può complicare il caching poiché il parametro di versione influenza la cache key.

La strategia consigliata per la maggior parte dei casi è l'**URL path versioning** per la sua semplicità e chiarezza. Indipendentemente dalla strategia scelta, è fondamentale documentare chiaramente la politica di deprecazione: per quanto tempo le versioni vecchie saranno supportate, come i client verranno notificati delle deprecazioni e qual è il timeline di migrazione.

### Gestione della Deprecazione

La deprecazione di una versione API deve essere comunicata con largo anticipo e gestita in modo progressivo. I meccanismi standard includono:

**Sunset Header (RFC 8594):** indica la data dopo la quale l'endpoint non sarà più disponibile.

```
HTTP/1.1 200 OK
Sunset: Sat, 01 Nov 2026 00:00:00 GMT
Deprecation: true
Link: <https://api.example.com/v2/users>; rel="successor-version"
```

**Politica di deprecazione consigliata:**
1. **Annuncio**: documentare la deprecazione almeno 6-12 mesi prima della rimozione.
2. **Warning header**: aggiungere l'header `Deprecation: true` e `Sunset` a tutte le risposte della versione deprecata.
3. **Monitoraggio**: tracciare l'utilizzo della versione deprecata per identificare i client che devono migrare.
4. **Comunicazione diretta**: notificare proattivamente i consumatori dell'API tramite email o webhook di notifica.
5. **Fallback graduale**: prima della rimozione, restituire risposte con header di avviso per un periodo, poi passare a risposte 410 Gone.

### Evoluzione Senza Versioning

Quando possibile, è preferibile evolvere l'API senza introdurre nuove versioni. Le modifiche **additive** sono retrocompatibili e non richiedono una nuova versione: aggiungere nuovi campi opzionali alle risposte, aggiungere nuovi endpoint, aggiungere nuovi query parameter opzionali, aggiungere nuovi valori a un enum (se i client gestiscono correttamente i valori sconosciuti). Le modifiche **breaking** richiedono una nuova versione: rimuovere o rinominare campi esistenti, cambiare il tipo di un campo, rendere obbligatorio un campo precedentemente opzionale, cambiare il formato di una risposta, rimuovere un endpoint. GraphQL adotta nativamente questo approccio tramite la direttiva `@deprecated`, che permette di contrassegnare campi come deprecati senza rimuoverli, guidando i client verso le alternative.

### Rate Limiting Differenziato per Versione

Le versioni deprecate dell'API possono avere limiti di rate più restrittivi rispetto alle versioni correnti, incentivando la migrazione. Ad esempio, la versione v1 deprecata può avere un limite di 100 richieste/minuto, mentre la versione v2 corrente ha un limite di 1000 richieste/minuto.

---

## Rate Limiting e Throttling

Rate limiting e throttling sono meccanismi complementari per proteggere un'API dall'abuso e garantire un'equa distribuzione delle risorse tra i client.

Il **rate limiting** definisce un limite massimo di richieste per unità di tempo. Quando il limite viene superato, le richieste vengono rifiutate con codice `429 Too Many Requests`.

Il **throttling** rallenta progressivamente le richieste anziché rifiutarle immediatamente, introducendo ritardi crescenti man mano che il client si avvicina al limite.

```javascript
// Implementazione rate limiting con Redis e sliding window
async function rateLimiter(req, res, next) {
  const clientId = req.headers['x-api-key'] || req.ip;
  const windowMs = 60 * 1000;
  const maxRequests = 100;
  const now = Date.now();
  const key = `ratelimit:${clientId}`;

  // Pipeline Redis per atomicità
  const pipeline = redis.pipeline();
  pipeline.zremrangebyscore(key, 0, now - windowMs);
  pipeline.zadd(key, now, `${now}-${Math.random()}`);
  pipeline.zcard(key);
  pipeline.expire(key, Math.ceil(windowMs / 1000));

  const results = await pipeline.exec();
  const requestCount = results[2][1];

  res.set('X-RateLimit-Limit', maxRequests);
  res.set('X-RateLimit-Remaining', Math.max(0, maxRequests - requestCount));
  res.set('X-RateLimit-Reset', Math.ceil((now + windowMs) / 1000));

  if (requestCount > maxRequests) {
    res.set('Retry-After', Math.ceil(windowMs / 1000));
    return res.status(429).json({
      type: 'https://api.example.com/problems/rate-limit-exceeded',
      title: 'Rate limit superato',
      status: 429,
      detail: `Limite di ${maxRequests} richieste al minuto superato.`
    });
  }

  next();
}
```

Una buona strategia di rate limiting prevede limiti differenziati per piano tariffario (free, pro, enterprise), per endpoint (gli endpoint di scrittura hanno limiti più bassi) e per tipo di autenticazione (le richieste autenticate hanno limiti più alti delle richieste anonime). È importante comunicare chiaramente i limiti nella documentazione e attraverso gli header di risposta, e fornire un endpoint dedicato per consultare lo stato corrente dei propri limiti.

### Confronto degli Algoritmi di Rate Limiting

| Algoritmo | Burst | Precisione | Memoria | Complessità | Utilizzato da |
|-----------|-------|------------|---------|-------------|---------------|
| Fixed Window | Burst al confine | Bassa | Minima (1 contatore) | Molto bassa | Soluzioni semplici |
| Sliding Window Log | No burst | Altissima | Alta (un timestamp per richiesta) | Media | API critiche |
| Sliding Window Counter | Burst limitato | Alta | Bassa (2 contatori) | Bassa | Cloudflare, Redis |
| Token Bucket | Burst controllato | Alta | Bassa (contatore + timestamp) | Bassa | Amazon, Stripe |
| Leaky Bucket | No burst | Alta | Bassa (contatore + coda) | Media | Shopify |

**Token Bucket in dettaglio:** il bucket ha una capacità massima di N token e viene rifornito a un rate costante (ad esempio 10 token/secondo). Ogni richiesta consuma un token. Se il bucket è vuoto, la richiesta viene rifiutata. Questo permette burst brevi (fino alla capacità del bucket) seguiti da un rate costante, un comportamento desiderabile per la maggior parte delle API.

**Sliding Window Counter:** è un ibrido tra fixed window e sliding window log. Mantiene due contatori (finestra corrente e finestra precedente) e calcola il rate come media pesata tra le due finestre in base alla posizione temporale all'interno della finestra corrente. Offre un buon compromesso tra precisione e consumo di memoria.

Per la maggior parte delle API, il **sliding window counter** offre il miglior equilibrio tra accuratezza, semplicità implementativa e basso consumo di risorse. Il **token bucket** è preferibile quando si vogliono permettere burst controllati. Il **leaky bucket** è ideale per scenari dove si richiede un output strettamente uniforme senza alcun burst.

---

## Caching

Il caching è uno degli strumenti più efficaci per migliorare le prestazioni e ridurre il carico sui server. HTTP fornisce meccanismi di caching sofisticati che ogni API ben progettata dovrebbe sfruttare.

### ETags

L'Entity Tag (ETag) è un identificatore opaco assegnato dal server a una specifica versione di una risorsa. Quando il client richiede nuovamente la risorsa, include l'ETag nell'header `If-None-Match`. Se la risorsa non è cambiata, il server risponde con `304 Not Modified` senza corpo, risparmiando banda e tempo di elaborazione.

```
// Prima richiesta
GET /api/v1/products/42 HTTP/1.1

HTTP/1.1 200 OK
ETag: "a1b2c3d4e5"
Content-Type: application/json

{ "id": 42, "name": "Laptop", "price": 999.99 }

// Richieste successive
GET /api/v1/products/42 HTTP/1.1
If-None-Match: "a1b2c3d4e5"

HTTP/1.1 304 Not Modified
ETag: "a1b2c3d4e5"
// Nessun corpo — il client usa la versione in cache
```

Gli ETag sono anche fondamentali per gestire gli **aggiornamenti concorrenti** (optimistic locking): il client include l'ETag nell'header `If-Match` di una richiesta PUT/PATCH, e il server rifiuta l'aggiornamento con `412 Precondition Failed` se la risorsa è stata modificata nel frattempo da un altro client.

```
// Aggiornamento con optimistic locking
PUT /api/v1/products/42 HTTP/1.1
If-Match: "a1b2c3d4e5"
Content-Type: application/json

{ "name": "Laptop Gaming", "price": 1099.99 }

// Se la risorsa è stata modificata da qualcun altro:
HTTP/1.1 412 Precondition Failed
// Il client deve ricaricare la risorsa e riprovare
```

### Cache-Control

L'header `Cache-Control` offre un controllo granulare su come e per quanto tempo le risposte possono essere memorizzate nella cache a diversi livelli (browser, CDN, proxy).

```
// Risorsa pubblica cacheable per 1 ora
Cache-Control: public, max-age=3600

// Risorsa privata (solo cache del browser, non CDN)
Cache-Control: private, max-age=600

// Nessun caching
Cache-Control: no-store

// Rivalidazione obbligatoria ad ogni richiesta
Cache-Control: no-cache
// (nonostante il nome, no-cache NON disabilita la cache;
//  obbliga il client a rivalidare con il server prima di usare la cache)

// Cache stale accettabile per 5 minuti durante rivalidazione
Cache-Control: public, max-age=3600, stale-while-revalidate=300

// Cache stale accettabile per 1 giorno in caso di errore del server
Cache-Control: public, max-age=3600, stale-if-error=86400
```

Strategie di caching consigliate per tipo di risorsa API:

| Tipo di risorsa | Cache-Control consigliato |
|----------------|--------------------------|
| Lista prodotti (catalogo) | `public, max-age=300, stale-while-revalidate=60` |
| Dettaglio prodotto | `public, max-age=600` + ETag |
| Profilo utente | `private, max-age=60` + ETag |
| Dati sensibili (pagamento) | `no-store` |
| Risorse statiche (immagini) | `public, max-age=31536000, immutable` |
| Risultati di ricerca | `public, max-age=60, stale-while-revalidate=30` |
| Operazioni di scrittura (POST/PUT/DELETE) | Non cacheable (il metodo stesso invalida la cache) |

Un pattern avanzato consiste nel combinare `stale-while-revalidate` con ETag: la cache serve immediatamente la versione stale al client (per una risposta istantanea) mentre rivalidare in background la risorsa con il server. Questo offre la migliore esperienza utente possibile in termini di velocità percepita.

---

## tRPC — Type Safety End-to-End

tRPC (TypeScript Remote Procedure Call) rappresenta un cambio di paradigma nella comunicazione client-server per applicazioni full-stack TypeScript. A differenza di REST e GraphQL, dove il contratto tra client e server è definito da una specifica esterna (OpenAPI, SDL GraphQL), tRPC inferisce i tipi direttamente dal codice server, eliminando qualsiasi layer di serializzazione manuale, code generation o schema separato.

### Architettura e Funzionamento

tRPC si basa su un concetto fondamentale: se client e server condividono lo stesso runtime TypeScript, i tipi possono essere condivisi direttamente attraverso l'inferenza di tipo del compilatore. Il server definisce **procedure** (query, mutation, subscription) organizzate in **router**, e il client accede a queste procedure con autocompletamento e type-checking completi senza alcun passo intermedio di generazione.

```typescript
// server/trpc.ts — inizializzazione
import { initTRPC, TRPCError } from '@trpc/server';
import { z } from 'zod';

const t = initTRPC.context<{ userId: string | null }>().create();

export const router = t.router;
export const publicProcedure = t.procedure;

// Middleware di autenticazione riutilizzabile
const isAuthenticated = t.middleware(({ ctx, next }) => {
  if (!ctx.userId) {
    throw new TRPCError({ code: 'UNAUTHORIZED' });
  }
  return next({ ctx: { userId: ctx.userId } });
});

export const protectedProcedure = t.procedure.use(isAuthenticated);
```

```typescript
// server/routers/user.ts — definizione del router
import { z } from 'zod';
import { router, publicProcedure, protectedProcedure } from '../trpc';

export const userRouter = router({
  // Query — lettura dati
  getById: publicProcedure
    .input(z.object({ id: z.string().uuid() }))
    .query(async ({ input }) => {
      const user = await db.user.findUnique({ where: { id: input.id } });
      if (!user) throw new TRPCError({ code: 'NOT_FOUND' });
      return user; // il tipo viene inferito automaticamente
    }),

  // Mutation — scrittura dati
  updateProfile: protectedProcedure
    .input(z.object({
      name: z.string().min(2).max(100),
      bio: z.string().max(500).optional(),
    }))
    .mutation(async ({ input, ctx }) => {
      return db.user.update({
        where: { id: ctx.userId },
        data: input,
      });
    }),

  // Query con output tipizzato esplicitamente
  list: publicProcedure
    .input(z.object({
      cursor: z.string().optional(),
      limit: z.number().min(1).max(100).default(20),
    }))
    .query(async ({ input }) => {
      const items = await db.user.findMany({
        take: input.limit + 1,
        cursor: input.cursor ? { id: input.cursor } : undefined,
        orderBy: { createdAt: 'desc' },
      });
      const hasMore = items.length > input.limit;
      return {
        items: hasMore ? items.slice(0, -1) : items,
        nextCursor: hasMore ? items[items.length - 1].id : null,
      };
    }),
});
```

```typescript
// client — utilizzo con inferenza automatica dei tipi
import { trpc } from './utils/trpc';

// Il tipo di `user` è inferito automaticamente dal return type della query
const { data: user } = trpc.user.getById.useQuery({ id: '...' });
// user.name — TypeScript conosce il tipo esatto
// user.nonExistent — errore di compilazione immediato

// La mutation ha input tipizzato — errore se i campi non corrispondono
const updateMutation = trpc.user.updateProfile.useMutation();
updateMutation.mutate({ name: 'Marco' }); // OK
updateMutation.mutate({ name: 42 });       // errore di compilazione
```

### Validazione Runtime con Zod

La combinazione tRPC + Zod garantisce sicurezza sia a compile-time che a runtime. Zod funge da ponte tra la validazione runtime (i dati effettivi che arrivano dal client) e la tipizzazione statica (i tipi che TypeScript verifica durante la compilazione). Quando si definisce uno schema Zod come input di una procedura tRPC, si ottengono simultaneamente la validazione dei dati in ingresso e l'inferenza dei tipi TypeScript, senza duplicazione.

### Quando Scegliere tRPC

tRPC è la scelta ottimale quando il progetto soddisfa tutte le seguenti condizioni: client e server sono entrambi in TypeScript; il team controlla sia il frontend che il backend (monorepo o organizzazione unica); l'API è interna e non necessita di essere consumata da client in altri linguaggi. Quando l'API deve essere pubblica o consumata da client non-TypeScript, REST con OpenAPI o GraphQL rimangono scelte più appropriate. tRPC non è un sostituto universale, ma eccelle nel suo dominio specifico.

### tRPC vs REST vs GraphQL

| Aspetto | tRPC | REST + OpenAPI | GraphQL |
|---------|------|----------------|---------|
| Type safety | Inferenza automatica, zero codegen | Richiede code generation | Richiede code generation |
| Setup iniziale | Minimo | Specifica + generatore | Schema SDL + resolver + codegen |
| Curva di apprendimento | Bassa (se si conosce TypeScript) | Bassa | Media-alta |
| Client non-TypeScript | Non supportato nativamente | Eccellente (multi-linguaggio) | Buono (multi-linguaggio) |
| API pubbliche | Non consigliato | Standard de facto | Buona alternativa |
| Caching HTTP | Limitato | Nativo | Complesso |
| Ecosistema | In rapida crescita | Maturo e consolidato | Maturo |

---

## GraphQL vs REST — Criteri Decisionali

La scelta tra GraphQL e REST non dovrebbe essere ideologica ma basata su criteri oggettivi legati al contesto del progetto. Entrambi i paradigmi hanno punti di forza e debolezze specifiche, e la decisione ottimale dipende da variabili come la natura dei client, la complessità delle relazioni tra dati, le competenze del team e i requisiti di performance.

### Quando Preferire REST

REST è la scelta preferibile quando l'API è pubblica e consumata da client eterogenei (linguaggi diversi, team esterni); quando le risorse hanno una struttura semplice e prevedibile, con relazioni poco profonde; quando il caching HTTP nativo è un requisito critico per le prestazioni; quando il team ha esperienza consolidata con REST e non ha familiarità con GraphQL; quando l'API serve principalmente operazioni CRUD con poca variabilità nelle query; quando la semplicità operativa è prioritaria (monitoring, debugging, logging sono più diretti con REST). Le API di Stripe, Twilio e la maggior parte dei servizi cloud pubblici sono RESTful, a conferma della solidità di questo approccio per API pubbliche su larga scala.

### Quando Preferire GraphQL

GraphQL eccelle quando i client hanno esigenze di dati molto eterogenee (un'app mobile richiede un sottoinsieme minimo dei dati, un dashboard web richiede aggregazioni complesse); quando l'applicazione ha relazioni profonde e interconnesse tra entità (social network, sistemi di content management); quando si vuole eliminare il problema dell'over-fetching e dell'under-fetching tipico di REST; quando il frontend necessita di iterazione rapida senza attendere modifiche al backend; quando si vogliono aggregare dati da microservizi multipli in un unico endpoint (GraphQL come API gateway); quando le subscription in tempo reale sono un requisito nativo. Aziende come GitHub, Shopify e Airbnb utilizzano GraphQL per le loro API rivolte agli sviluppatori, dove la flessibilità delle query è un vantaggio competitivo.

### Matrice Decisionale

| Criterio | REST | GraphQL |
|----------|------|---------|
| Semplicità di implementazione | Alta | Media |
| Caching HTTP nativo | Nativo e trasparente | Richiede soluzioni ad hoc |
| Flessibilità per il client | Bassa (endpoint fissi) | Alta (query personalizzate) |
| Over/Under-fetching | Problema comune | Risolto by design |
| Curva di apprendimento team | Bassa | Media-alta |
| Monitoraggio e debugging | Semplice (un URL = un'operazione) | Complesso (tutte le query vanno a POST /graphql) |
| Evoluzione senza versioning | Difficile (richiede nuove versioni) | Naturale (deprecazione campi) |
| Protezione da query abusive | Non necessaria | Essenziale (depth limit, cost analysis) |
| Upload file | Nativo (multipart) | Richiede workaround |
| Documentazione standardizzata | OpenAPI maturo | Strumenti GraphQL dedicati |

### Approccio Ibrido

Molte architetture moderne combinano REST e GraphQL strategicamente: REST per le API pubbliche stabili e ben definite, GraphQL come layer di aggregazione interno per il frontend. Un API gateway può esporre endpoint REST verso l'esterno e tradurre le richieste in query GraphQL verso i microservizi interni, offrendo il meglio di entrambi i paradigmi.

---

## Webhook Design

I webhook implementano il pattern di comunicazione **push-based**: invece di richiedere al client di effettuare polling periodico per verificare lo stato di una risorsa, il server notifica proattivamente il client quando si verifica un evento rilevante. Questo pattern riduce drasticamente il traffico di rete, la latenza percepita e il carico computazionale su entrambe le parti.

### Architettura di un Sistema Webhook

Un sistema webhook robusto comprende tre componenti principali: il **producer** (il servizio che emette gli eventi), il **delivery system** (il meccanismo di consegna con retry e persistenza) e il **consumer** (l'endpoint del client che riceve e processa gli eventi).

```
Evento → Producer → Coda persistente → Delivery Engine → HTTP POST → Consumer
                                              ↓
                                    Retry con backoff esponenziale
                                              ↓
                                    Dead Letter Queue (dopo N fallimenti)
```

### Formato del Payload

Il payload del webhook deve seguire una struttura standardizzata e prevedibile. Ogni evento deve includere un identificatore univoco, il tipo di evento, un timestamp e i dati associati.

```json
{
  "id": "evt_a1b2c3d4e5f6",
  "type": "order.completed",
  "created_at": "2025-11-15T14:30:00Z",
  "api_version": "2025-11-01",
  "data": {
    "object": {
      "id": "ord_xyz789",
      "amount": 9999,
      "currency": "EUR",
      "customer_id": "cus_abc123",
      "status": "completed"
    },
    "previous_attributes": {
      "status": "processing"
    }
  }
}
```

Il campo `previous_attributes` è particolarmente utile per gli eventi di aggiornamento, poiché permette al consumer di comprendere esattamente cosa è cambiato senza dover confrontare con il proprio stato locale.

### Verifica della Firma

La verifica della firma è **obbligatoria** per garantire che il webhook provenga effettivamente dal producer e non sia stato manomesso. Il pattern standard utilizza HMAC-SHA256 con un secret condiviso.

```javascript
import crypto from 'node:crypto';

function verifyWebhookSignature(rawBody, signatureHeader, secret) {
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(rawBody, 'utf8')
    .digest('hex');

  const receivedSignature = signatureHeader.replace('sha256=', '');

  // Confronto timing-safe per prevenire timing attacks
  return crypto.timingSafeEqual(
    Buffer.from(expectedSignature, 'hex'),
    Buffer.from(receivedSignature, 'hex')
  );
}

// Middleware Express — DEVE usare il raw body, non il JSON parsato
app.post('/webhooks', express.raw({ type: 'application/json' }), (req, res) => {
  const signature = req.headers['x-webhook-signature'];
  if (!verifyWebhookSignature(req.body, signature, WEBHOOK_SECRET)) {
    return res.status(401).json({ error: 'Firma non valida' });
  }

  // Rispondere immediatamente con 202 Accepted
  res.status(202).json({ received: true });

  // Processare l'evento in modo asincrono
  processWebhookAsync(JSON.parse(req.body.toString()));
});
```

Un errore comune è utilizzare il body JSON già parsato per la verifica della firma: la serializzazione JSON non è deterministica (l'ordine delle chiavi può variare), quindi la firma deve essere calcolata sul **raw body** esattamente come ricevuto.

### Idempotenza del Consumer

I webhook vengono consegnati **at-least-once**: il producer potrebbe reinviare lo stesso evento in caso di timeout di rete o mancata ricezione della risposta. Il consumer deve quindi essere idempotente, processando ogni evento al massimo una volta indipendentemente dal numero di consegne.

```javascript
async function processWebhookAsync(event) {
  // Controllo idempotenza — atomico con la logica di business
  const processed = await db.transaction(async (tx) => {
    const existing = await tx.webhookEvent.findUnique({
      where: { eventId: event.id }
    });
    if (existing) return null; // già processato

    // Processare l'evento
    const result = await handleEvent(event, tx);

    // Registrare l'evento come processato nella stessa transazione
    await tx.webhookEvent.create({
      data: { eventId: event.id, processedAt: new Date() }
    });

    return result;
  });
}
```

### Retry con Backoff Esponenziale

Il producer deve implementare una strategia di retry con backoff esponenziale e jitter per gestire i fallimenti temporanei senza sovraccaricare il consumer.

```
Tentativo 1: immediato
Tentativo 2: 1s + jitter casuale (0-500ms)
Tentativo 3: 4s + jitter
Tentativo 4: 16s + jitter
Tentativo 5: 64s + jitter
Tentativo 6: 256s + jitter
... fino a un massimo di 24 ore, poi Dead Letter Queue
```

Il consumer deve rispondere con `2xx` per indicare ricezione riuscita (anche se il processamento avverrà in modo asincrono), `4xx` per errori permanenti (payload non valido — il producer non dovrebbe riprovare), `5xx` per errori temporanei (il producer riproverà con backoff).

### Dead Letter Queue

Dopo l'esaurimento di tutti i tentativi di retry, gli eventi non consegnati devono essere salvati in una **Dead Letter Queue** (DLQ). La DLQ è essenziale per non perdere eventi critici e permette l'ispezione manuale, il reprocessamento selettivo e il monitoraggio: una DLQ in crescita è un segnale di allarme che indica problemi sistemici nel consumer.

---

## API Testing

Il testing delle API è un pilastro della qualità del software, con approcci complementari che coprono livelli diversi dello stack di verifica: unit test per la logica di business, integration test per il comportamento end-to-end degli endpoint, e contract test per garantire la compatibilità tra servizi.

### Contract Testing con Pact

Il **contract testing** verifica che le interazioni tra un consumer (il client) e un provider (il server API) rispettino un contratto concordato, senza richiedere che entrambi i servizi siano in esecuzione contemporaneamente. Questo approccio è fondamentale nelle architetture a microservizi, dove i deploy indipendenti possono introdurre incompatibilità non rilevabili dai test tradizionali.

**Pact** è lo strumento di riferimento per il contract testing consumer-driven. Il flusso di lavoro si articola in due fasi:

1. **Lato consumer**: si definiscono le interazioni attese (richiesta e risposta) e si genera un file **pact** (contratto) che descrive queste aspettative.
2. **Lato provider**: si verifica che il servizio reale soddisfi tutti i contratti generati dai consumer.

```javascript
// test/consumer.pact.test.js — lato consumer
import { PactV4 } from '@pact-foundation/pact';

const provider = new PactV4({
  consumer: 'OrderService',
  provider: 'UserService',
});

describe('UserService API Contract', () => {
  it('restituisce un utente per ID', async () => {
    await provider
      .addInteraction()
      .given('utente con ID 42 esiste')
      .uponReceiving('richiesta GET per utente 42')
      .withRequest('GET', '/api/v1/users/42', (builder) => {
        builder.headers({ Accept: 'application/json' });
      })
      .willRespondWith(200, (builder) => {
        builder.headers({ 'Content-Type': 'application/json' });
        builder.jsonBody({
          id: '42',
          name: 'Marco Rossi',
          email: 'marco@example.com',
        });
      })
      .executeTest(async (mockServer) => {
        const response = await fetch(
          `${mockServer.url}/api/v1/users/42`,
          { headers: { Accept: 'application/json' } }
        );
        const user = await response.json();
        expect(user.name).toBe('Marco Rossi');
      });
  });
});
```

Il vantaggio chiave del contract testing è la **velocità**: i test girano in isolamento, senza dipendenze di rete o servizi esterni, e rilevano le incompatibilità prima del deploy in produzione.

### API Testing con Hurl

**Hurl** è uno strumento a riga di comando per testare API HTTP utilizzando un formato di file dichiarativo, leggibile e versionabile. Hurl combina la semplicità di cURL con la potenza di un test runner completo, supportando assertion, variabili, cattura di valori dalle risposte e concatenamento di richieste.

```hurl
# test/api/users.hurl — test di un flusso completo

# 1. Creare un utente
POST http://localhost:3000/api/v1/users
Content-Type: application/json
{
  "name": "Anna Verdi",
  "email": "anna@example.com"
}
HTTP 201
[Captures]
user_id: jsonpath "$.id"
[Asserts]
header "Location" exists
jsonpath "$.name" == "Anna Verdi"
jsonpath "$.email" == "anna@example.com"
jsonpath "$.createdAt" exists

# 2. Leggere l'utente creato
GET http://localhost:3000/api/v1/users/{{user_id}}
HTTP 200
[Asserts]
jsonpath "$.id" == {{user_id}}
jsonpath "$.name" == "Anna Verdi"

# 3. Aggiornare l'utente
PATCH http://localhost:3000/api/v1/users/{{user_id}}
Content-Type: application/merge-patch+json
{
  "name": "Anna Bianchi"
}
HTTP 200
[Asserts]
jsonpath "$.name" == "Anna Bianchi"

# 4. Eliminare l'utente
DELETE http://localhost:3000/api/v1/users/{{user_id}}
HTTP 204

# 5. Verificare che l'utente non esista più
GET http://localhost:3000/api/v1/users/{{user_id}}
HTTP 404
```

Hurl viene eseguito dalla riga di comando con `hurl --test test/api/*.hurl` e si integra facilmente in pipeline CI/CD. Il formato testuale è ideale per il code review e il versionamento in Git.

### Strategia di Testing API Completa

Una strategia di testing API robusta combina diversi livelli di verifica:

| Livello | Strumento | Cosa Verifica | Quando Eseguire |
|---------|-----------|---------------|-----------------|
| Unit test | Jest, Vitest | Logica di business, validazione | Ad ogni commit |
| Integration test | Supertest, Hurl | Endpoint completi con database | Ad ogni PR |
| Contract test | Pact | Compatibilità tra servizi | Ad ogni PR |
| Load test | k6, Artillery | Prestazioni sotto carico | Prima del rilascio |
| Security test | OWASP ZAP | Vulnerabilità | Periodicamente |

---

## Pattern di Idempotenza

L'idempotenza è la proprietà per cui un'operazione produce lo stesso risultato indipendentemente dal numero di volte in cui viene eseguita. Nelle API, l'idempotenza è cruciale per gestire i retry sicuri: se una richiesta fallisce a causa di un timeout di rete, il client deve poter reinviare la stessa richiesta senza rischiare effetti collaterali come pagamenti duplicati o creazione di record multipli.

### Idempotenza Naturale dei Metodi HTTP

I metodi GET, PUT e DELETE sono naturalmente idempotenti per definizione. `GET /users/42` restituisce sempre lo stesso utente. `PUT /users/42 { "name": "Marco" }` imposta sempre lo stesso stato, indipendentemente da quante volte viene invocato. `DELETE /users/42` elimina la risorsa la prima volta e restituisce 404 (o 204) nelle chiamate successive — il risultato netto è lo stesso.

Il metodo POST è l'unico metodo comune non naturalmente idempotente: ogni invocazione può creare una nuova risorsa. Questo è problematico in scenari dove il client non riceve la risposta a causa di un errore di rete e non sa se la richiesta è stata elaborata o meno.

### Idempotency Key Pattern

Il pattern **Idempotency Key** (adottato da Stripe, PayPal, Adyen e molti altri) risolve il problema dell'idempotenza per le operazioni POST. Il client genera un UUID univoco e lo include in ogni richiesta. Il server verifica se una richiesta con la stessa chiave è già stata elaborata e, in caso affermativo, restituisce la stessa risposta senza rieseguire l'operazione.

```javascript
// Middleware idempotency key — implementazione con Redis
async function idempotencyMiddleware(req, res, next) {
  if (req.method !== 'POST') return next();

  const idempotencyKey = req.headers['idempotency-key'];
  if (!idempotencyKey) return next();

  const cacheKey = `idempotency:${req.path}:${idempotencyKey}`;

  // Verificare se la richiesta è già stata elaborata
  const cached = await redis.get(cacheKey);
  if (cached) {
    const { statusCode, body, headers } = JSON.parse(cached);
    Object.entries(headers).forEach(([k, v]) => res.set(k, v));
    return res.status(statusCode).json(body);
  }

  // Acquisire un lock distribuito per prevenire race condition
  const lockKey = `lock:${cacheKey}`;
  const lockAcquired = await redis.set(lockKey, '1', 'NX', 'EX', 30);
  if (!lockAcquired) {
    return res.status(409).json({
      type: 'https://api.example.com/problems/concurrent-request',
      title: 'Richiesta concorrente in elaborazione',
      status: 409,
      detail: 'Una richiesta con la stessa Idempotency-Key è in elaborazione.'
    });
  }

  // Intercettare la risposta per salvarla in cache
  const originalJson = res.json.bind(res);
  res.json = (body) => {
    const responseData = {
      statusCode: res.statusCode,
      body,
      headers: { 'content-type': 'application/json' }
    };
    // TTL di 24 ore — le chiavi scadono automaticamente
    redis.set(cacheKey, JSON.stringify(responseData), 'EX', 86400);
    redis.del(lockKey);
    return originalJson(body);
  };

  next();
}
```

La chiave di idempotenza deve essere un UUID v4 generato dal client, univoca per ogni operazione logica distinta e riutilizzata solo in caso di retry della stessa operazione. Il server deve conservare le risposte associate alle chiavi per un periodo ragionevole (tipicamente 24-48 ore) prima di eliminarle.

### Idempotenza nelle Operazioni Finanziarie

Per le operazioni finanziarie (pagamenti, rimborsi, trasferimenti), l'idempotenza non è un'ottimizzazione ma un requisito di correttezza. Un pagamento duplicato è un difetto critico con conseguenze legali e reputazionali. In questi contesti, l'idempotency key deve essere abbinata a una verifica di consistenza: se la stessa chiave viene inviata con un body diverso, il server deve rifiutare la richiesta con `422 Unprocessable Entity` anziché restituire la risposta precedente, poiché potrebbe trattarsi di un errore del client.

---

## Operazioni Bulk

Le operazioni bulk permettono ai client di eseguire più operazioni in una singola richiesta HTTP, riducendo l'overhead di rete e migliorando le prestazioni per aggiornamenti massivi.

### Pattern di Progettazione

Esistono due approcci principali per le operazioni bulk:

**Approccio collezione** — un singolo endpoint accetta un array di operazioni dello stesso tipo:

```
POST /api/v1/products/bulk
Content-Type: application/json
Idempotency-Key: batch-2025-11-15-001

{
  "operations": [
    { "action": "create", "data": { "name": "Prodotto A", "price": 29.99 } },
    { "action": "create", "data": { "name": "Prodotto B", "price": 49.99 } },
    { "action": "update", "id": "prod_123", "data": { "price": 39.99 } },
    { "action": "delete", "id": "prod_456" }
  ]
}
```

**Approccio batch JSON** — ispirato alle Batch API di Google e Facebook, ogni operazione è una richiesta HTTP virtuale:

```json
{
  "requests": [
    { "method": "POST", "url": "/api/v1/products", "body": { "name": "Prodotto A" } },
    { "method": "PATCH", "url": "/api/v1/products/123", "body": { "price": 39.99 } },
    { "method": "DELETE", "url": "/api/v1/products/456" }
  ]
}
```

### Gestione del Successo Parziale

Il problema più complesso nelle operazioni bulk è la gestione del successo parziale: alcune operazioni riescono e altre falliscono. La risposta deve comunicare chiaramente lo stato di ciascuna operazione individuale.

```json
{
  "status": "partial_success",
  "summary": {
    "total": 4,
    "succeeded": 3,
    "failed": 1
  },
  "results": [
    { "index": 0, "status": 201, "data": { "id": "prod_789", "name": "Prodotto A" } },
    { "index": 1, "status": 201, "data": { "id": "prod_790", "name": "Prodotto B" } },
    { "index": 2, "status": 200, "data": { "id": "prod_123", "price": 39.99 } },
    {
      "index": 3,
      "status": 404,
      "error": {
        "type": "https://api.example.com/problems/not-found",
        "title": "Risorsa non trovata",
        "detail": "Il prodotto prod_456 non esiste."
      }
    }
  ]
}
```

Il codice di stato HTTP della risposta complessiva deve essere `200 OK` (operazione bulk completata) indipendentemente dallo stato delle singole operazioni. Utilizzare `207 Multi-Status` è un'alternativa valida derivata da WebDAV. Non utilizzare mai `201` o `204` per le risposte bulk, poiché lo stato complessivo non corrisponde a nessuna singola operazione.

### Limiti e Best Practice

Le operazioni bulk devono avere un limite massimo di operazioni per richiesta (tipicamente 100-1000), documentato nella specifica API. Le operazioni devono essere elaborate in modo atomico (tutte o nessuna) oppure con semantica best-effort (successo parziale), e la scelta deve essere documentata esplicitamente. L'idempotency key deve coprire l'intera operazione bulk, non le singole sotto-operazioni. Per batch molto grandi (migliaia di operazioni), considerare un approccio asincrono: il server accetta la richiesta con `202 Accepted` e fornisce un endpoint di polling per monitorare lo stato dell'elaborazione.

---

## Best Practices

Le seguenti dieci best practice sintetizzano i principi fondamentali per progettare API di alta qualità.

### 1. Progettazione API-First

Progettare l'API prima di scrivere qualsiasi codice. Definire lo schema OpenAPI, condividerlo con i team consumer per raccogliere feedback, iterare sul design e solo successivamente procedere con l'implementazione. L'approccio API-first previene costose riscritture, allinea i team sulla struttura dei dati e permette lo sviluppo parallelo di frontend e backend utilizzando mock server generati dalla specifica.

### 2. Coerenza Assoluta

La coerenza è la qualità piu importante di un'API. Adottare e documentare convenzioni rigide per naming (camelCase vs snake_case), formato delle date (ISO 8601), struttura delle risposte, gestione degli errori, paginazione e autenticazione. Ogni endpoint dell'API deve sembrare progettato dalla stessa persona. Un client che ha imparato a usare un endpoint deve poter prevedere il comportamento di tutti gli altri.

### 3. Idempotenza e Idempotency Key

Le operazioni di creazione (POST) non sono naturalmente idempotenti: se il client reinvia la stessa richiesta a causa di un timeout di rete, il server potrebbe creare duplicati. Il pattern **Idempotency Key** risolve questo problema: il client include un header `Idempotency-Key` con un UUID univoco, e il server garantisce che richieste con la stessa chiave producano lo stesso risultato indipendentemente dal numero di invii.

```
POST /api/v1/payments HTTP/1.1
Idempotency-Key: 7c4a8d09-ca95-4178-838d-5b4e8b2c1a3f
Content-Type: application/json

{ "amount": 99.99, "currency": "EUR" }
```

### 4. Validazione e Messaggi di Errore Utili

Validare rigorosamente ogni input e restituire messaggi di errore che aiutino concretamente lo sviluppatore a correggere il problema. Ogni errore dovrebbe indicare quale campo è invalido, perché è invalido e quale valore è stato ricevuto. Adottare il formato RFC 7807 per una struttura standardizzata. Mai esporre stack trace, query SQL o dettagli interni del server nei messaggi di errore.

### 5. Paginazione Obbligatoria

Non restituire mai collezioni senza limiti. Ogni endpoint che restituisce una lista deve supportare la paginazione con un limite massimo ragionevole (tipicamente 100 elementi). Includere sempre metadati di paginazione nella risposta (total, has_next, cursori). Scegliere paginazione cursor-based per dataset grandi e in continuo aggiornamento, offset-based per dataset stabili dove il conteggio totale e la navigazione per pagina sono utili.

### 6. Versionamento sin dal Primo Giorno

Includere la versione nell'API fin dalla prima release, anche se non si prevede di introdurre breaking changes a breve. Il costo di aggiungere il versionamento retroattivamente è ordini di grandezza superiore a quello di includerlo dall'inizio. Documentare una politica chiara di deprecazione (per esempio: le versioni vecchie sono supportate per 12 mesi dopo il rilascio della versione successiva).

### 7. Rate Limiting Trasparente

Implementare il rate limiting e comunicare chiaramente i limiti attraverso la documentazione, gli header di risposta (`X-RateLimit-*`) e un endpoint dedicato per consultare lo stato dei propri limiti. Differenziare i limiti per piano tariffario, tipo di endpoint e livello di autenticazione. Fornire sempre l'header `Retry-After` nelle risposte 429 per indicare al client quando può riprovare.

### 8. Documentazione Viva e Interattiva

La documentazione deve essere generata automaticamente dalla specifica OpenAPI ed essere sempre sincronizzata con l'implementazione. Includere esempi realistici per ogni endpoint (non valori placeholder come "string" o 0), casi d'errore documentati, guide di quickstart, snippet di codice in diversi linguaggi e un ambiente sandbox dove gli sviluppatori possono sperimentare senza impattare la produzione.

### 9. Sicurezza come Requisito Non Negoziabile

Utilizzare sempre HTTPS senza eccezioni. Implementare autenticazione robusta (OAuth 2.0 + PKCE per applicazioni web, API Key per server-to-server). Validare e sanitizzare ogni input per prevenire injection. Implementare CORS correttamente, limitando le origini permesse. Non esporre mai informazioni sensibili nei log, negli URL o nei messaggi di errore. Utilizzare header di sicurezza appropriati (`Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options`). Implementare il principio del privilegio minimo: ogni token deve avere solo gli scope necessari.

### 10. Monitoraggio, Logging e Osservabilita

Ogni richiesta API deve generare un **request ID** univoco (restituito nell'header `X-Request-Id`) che permetta di tracciare l'intera catena di elaborazione attraverso tutti i servizi coinvolti. Monitorare metriche chiave: latenza (p50, p95, p99), tasso di errore per endpoint, tasso di utilizzo del rate limit, dimensione delle risposte. Impostare alert per anomalie e degradazioni delle prestazioni. Implementare health check endpoint (`GET /health`) che verifichino la connettività con le dipendenze critiche (database, cache, servizi esterni). I log devono essere strutturati (JSON), includere il request ID e non contenere mai dati sensibili degli utenti.

---

## Riepilogo Comparativo dei Paradigmi

| Aspetto | REST | GraphQL | gRPC | WebSocket |
|---------|------|---------|------|-----------|
| Protocollo | HTTP/1.1 o HTTP/2 | HTTP (POST unico) | HTTP/2 | TCP (dopo upgrade HTTP) |
| Formato dati | JSON (tipicamente) | JSON | Protocol Buffers (binario) | Qualsiasi (testo/binario) |
| Tipizzazione | Debole (OpenAPI opzionale) | Forte (schema obbligatorio) | Forte (protobuf obbligatorio) | Nessuna (a carico del dev) |
| Caching HTTP | Nativo | Complesso (POST unico) | Non applicabile | Non applicabile |
| Streaming | Limitato (SSE) | Subscription | Nativo (4 pattern) | Nativo (bidirezionale) |
| Over/Under-fetching | Comune | Risolto by design | N/A (RPC oriented) | N/A |
| Curva apprendimento | Bassa | Media | Alta | Media |
| Caso d'uso ideale | API pubbliche, CRUD | Client eterogenei, mobile | Microservizi interni | Tempo reale, chat, gaming |
| Tooling | Maturo e vasto | In crescita | Buono, multi-linguaggio | Maturo |

La scelta del paradigma non è esclusiva: molte architetture moderne combinano REST per le API pubbliche, gRPC per la comunicazione tra microservizi, GraphQL come layer di aggregazione per il frontend e WebSocket per il tempo reale. La chiave è scegliere il paradigma giusto per ogni contesto, evitando di adottare una tecnologia per moda anziché per necessità architetturale.

---

## Esercizi

### Esercizio 1 — Specifica OpenAPI 3.1 per un servizio di gestione libreria

**Obiettivo:** Progettare un'API RESTful partendo dal contratto prima dell'implementazione (API-first design).

Scrivere una specifica OpenAPI 3.1 completa per un servizio di gestione libreria con le seguenti risorse:

- `books` — con campi `id`, `title`, `author`, `isbn`, `publishedYear`, `genre`, `availableCopies`
- `members` — con campi `id`, `name`, `email`, `membershipType` (basic, premium), `registeredAt`
- `loans` — con campi `id`, `bookId`, `memberId`, `borrowedAt`, `dueDate`, `returnedAt`

Requisiti della specifica:
- Definire tutti gli endpoint CRUD per ciascuna risorsa con metodi HTTP appropriati
- Utilizzare `$ref` per i componenti riutilizzabili (schemi, parametri, risposte di errore)
- Implementare cursor pagination per le liste (`GET /books?cursor=...&limit=20`)
- Documentare i codici di errore con RFC 7807 Problem Details
- Aggiungere security scheme OAuth 2.0 con scope `read:books`, `write:books`, `manage:loans`
- Includere almeno 2 esempi realistici per ogni endpoint
- Validare la specifica con `@redocly/cli lint`

### Esercizio 2 — REST API con versioning e HATEOAS

**Obiettivo:** Implementare un'API REST di livello 3 (Richardson Maturity Model) con evoluzione controllata.

Costruire un'API REST per un sistema e-commerce con:

- Versioning tramite URL path (`/api/v1/`, `/api/v2/`) con almeno un breaking change tra v1 e v2 (es. rinominare un campo, cambiare la struttura di una risposta)
- Risposte HATEOAS con link `_links` che guidino il client attraverso le transizioni di stato:
  ```json
  {
    "id": 42,
    "status": "pending",
    "_links": {
      "self": { "href": "/api/v2/orders/42" },
      "confirm": { "href": "/api/v2/orders/42/confirm", "method": "POST" },
      "cancel": { "href": "/api/v2/orders/42/cancel", "method": "POST" },
      "items": { "href": "/api/v2/orders/42/items" }
    }
  }
  ```
- Content negotiation con header `Accept` per JSON e CSV
- ETag e `If-None-Match` per caching condizionale
- Idempotency key (`Idempotency-Key` header) per le operazioni POST
- Sunset header (`Sunset: Sat, 01 Nov 2026 00:00:00 GMT`) per endpoint deprecati di v1
- Test che verifichino la corretta generazione dei link HATEOAS in base allo stato della risorsa

### Esercizio 3 — Schema GraphQL con DataLoader e persisted queries

**Obiettivo:** Progettare e implementare un'API GraphQL risolvendo il problema N+1 e proteggendo il server.

Implementare un server GraphQL (Apollo Server o Mercurius su Fastify) per un social network semplificato:

- Schema con tipi `User`, `Post`, `Comment`, `Like` con relazioni bidirezionali
- Query: `users`, `user(id)`, `posts(filter, pagination)`, `post(id)`
- Mutation: `createPost`, `editPost`, `deletePost`, `addComment`, `toggleLike`
- Subscription: `onNewComment(postId)`, `onNewLike(postId)`
- Risolvere il problema N+1 con DataLoader per le relazioni `User.posts`, `Post.comments`, `Post.likes`
- Implementare query depth limiting (max 5 livelli) e query cost analysis
- Configurare persisted queries con allowlist lato server (APQ o hash-based)
- Aggiungere un campo `@deprecated(reason: "Use fullName instead")` per dimostrare l'evoluzione dello schema
- Test con query che verifichino che le query non consentite vengano rifiutate

### Esercizio 4 — Gateway API con rate limiting differenziato e circuit breaker

**Obiettivo:** Implementare pattern di resilienza e protezione a livello di API gateway.

Costruire un API gateway (Express o Fastify) che faccia da proxy verso 3 microservizi simulati:

- `/api/users` → servizio utenti (porta 3001)
- `/api/products` → servizio prodotti (porta 3002)
- `/api/orders` → servizio ordini (porta 3003)
- Rate limiting differenziato: utenti anonimi 30 req/min, utenti autenticati basic 100 req/min, utenti premium 500 req/min
- Header `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` in ogni risposta
- Circuit breaker per ogni backend: dopo 5 errori consecutivi, lo stato diventa `open` e restituisce 503 per 30 secondi, poi passa a `half-open` con una singola richiesta di prova
- Request correlation ID propagato a tutti i microservizi downstream
- Aggregazione di metriche: latenza per servizio (p50, p95, p99), tasso di errore, stato del circuit breaker
- Endpoint `/api/health` che aggreghi lo stato di salute dei 3 servizi
- Test che simulino il fallimento di un servizio e verifichino il comportamento del circuit breaker

### Esercizio 5 — Definizione gRPC con proto e client/server in Node.js

**Obiettivo:** Comprendere gRPC come alternativa ad alta prestazione per comunicazione inter-servizio.

Implementare un servizio gRPC per un sistema di inventario:

- Definire il file `.proto` con:
  - Service `InventoryService` con RPC: `GetProduct` (unary), `ListProducts` (server streaming), `UpdateStock` (unary), `BulkUpdateStock` (client streaming), `WatchStockChanges` (bidirectional streaming)
  - Message types con campi tipizzati, enumerazioni per `ProductCategory` e `StockStatus`
  - Validazione con `buf lint`
- Implementare il server gRPC in Node.js con `@grpc/grpc-js`
- Implementare il client con chiamate a tutti e 4 i pattern di streaming
- Aggiungere interceptor per logging, autenticazione tramite metadata e timeout
- Implementare un adapter REST-to-gRPC con `grpc-gateway` pattern (proxy HTTP che traduca le richieste REST in chiamate gRPC)
- Confrontare le prestazioni (latenza, throughput) tra l'endpoint REST e la chiamata gRPC diretta con un benchmark di almeno 1000 richieste
- Documentare i trade-off osservati tra REST e gRPC nel contesto del progetto

---

## Letture e Riferimenti

### Documentazione ufficiale

- **OpenAPI Specification 3.1** — specifica completa per la descrizione di API RESTful. https://spec.openapis.org/oas/v3.1.0 (consultato: 2026-05-24)
- **RFC 9110 — HTTP Semantics** — definizione dei metodi HTTP, status code e header semantici. https://www.rfc-editor.org/rfc/rfc9110 (consultato: 2026-05-24)
- **RFC 7807 — Problem Details for HTTP APIs** — formato standard per errori HTTP strutturati. https://www.rfc-editor.org/rfc/rfc7807 (consultato: 2026-05-24)
- **GraphQL Specification** — specifica ufficiale del linguaggio di query GraphQL. https://spec.graphql.org/ (consultato: 2026-05-24)
- **gRPC Documentation** — guida ufficiale per la comunicazione inter-servizio con Protocol Buffers. https://grpc.io/docs/ (consultato: 2026-05-24)
- **RFC 6749 — OAuth 2.0 Authorization Framework** — specifica del protocollo OAuth 2.0 per l'autenticazione API. https://www.rfc-editor.org/rfc/rfc6749 (consultato: 2026-05-24)
- **JSON:API Specification** — convenzione per la costruzione di API JSON con relazioni e paginazione. https://jsonapi.org/format/ (consultato: 2026-05-24)
- **Richardson Maturity Model** — i quattro livelli di maturità delle API REST. https://martinfowler.com/articles/richardsonMaturityModel.html (consultato: 2026-05-24)

### Libri e approfondimenti

- Lauret, Arnaud, *The Design of Web APIs*, Manning, 2019.
- Sturgeon, Phil, *Build APIs You Won't Hate*, LeanPub, 2023.
- Biehl, Matthias, *API Design Patterns*, Manning, 2024.

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [10 — Node.js](10-nodejs.md) | Prerequisito: Express e Fastify sono i framework principali per implementare le API progettate |
| [06 — TypeScript](06-typescript.md) | Prerequisito: tipizzazione statica per contratti API, generazione client tipizzati da OpenAPI |
| [12 — Database Web](12-database-web.md) | Le API espongono dati persistiti su database; design dello schema influenza il design degli endpoint |
| [13 — Autenticazione e Autorizzazione](13-autenticazione-autorizzazione.md) | OAuth 2.0, JWT e API key proteggono gli endpoint API |
| [14 — Sicurezza Web](14-sicurezza-web.md) | Rate limiting, CORS, input validation e security headers per la protezione delle API |
| [24 — GraphQL Guida Completa](24-graphql-guida-completa.md) | Approfondimento dedicato al paradigma GraphQL introdotto in questo modulo |

---

## Glossario

| Termine | Definizione |
|---|---|
| **REST** | Representational State Transfer: stile architetturale per API basato su risorse, metodi HTTP e statelessness. |
| **GraphQL** | Linguaggio di query per API che consente al client di richiedere esattamente i dati necessari, evitando over-fetching. |
| **gRPC** | Framework RPC ad alte prestazioni di Google basato su HTTP/2 e Protocol Buffers per la serializzazione binaria. |
| **OpenAPI** | Specifica standard per descrivere API RESTful in formato YAML o JSON, utilizzata per generare documentazione e client. |
| **HATEOAS** | Hypermedia As The Engine Of Application State: principio REST per cui le risposte includono link alle transizioni disponibili. |
| **Idempotenza** | Proprietà per cui un'operazione produce lo stesso risultato indipendentemente dal numero di volte in cui viene eseguita. |
| **Rate Limiting** | Meccanismo che limita il numero di richieste per client in un intervallo temporale per proteggere il server. |
| **Cursor Pagination** | Tecnica di paginazione basata su un puntatore opaco anziché su offset numerico, robusta rispetto a inserimenti concorrenti. |
| **Content Negotiation** | Meccanismo HTTP per cui client e server concordano il formato della risposta tramite header `Accept` e `Content-Type`. |
| **Circuit Breaker** | Pattern di resilienza che interrompe le chiamate a un servizio degradato, evitando il cascading failure. |
| **DataLoader** | Libreria per il batching e caching delle query in GraphQL, risolvendo il problema delle query N+1. |
| **Protocol Buffers** | Formato di serializzazione binaria di Google, utilizzato da gRPC per definire contratti di servizio tipizzati. |
| **Problem Details** | Formato standard (RFC 7807) per rappresentare errori HTTP in modo strutturato e machine-readable. |
| **ETag** | Header HTTP che identifica una versione specifica di una risorsa, utilizzato per caching condizionale e concurrency control. |
| **tRPC** | Framework RPC per TypeScript che inferisce i tipi direttamente dal codice server, eliminando la necessità di code generation o schemi separati. |
| **mTLS** | Mutual TLS: estensione di TLS dove sia client che server presentano certificati X.509, autenticando entrambe le parti della connessione. |
| **Webhook** | Meccanismo di notifica push-based in cui il server invia una richiesta HTTP POST al client quando si verifica un evento, evitando la necessità di polling. |
| **Idempotency Key** | UUID univoco incluso dal client nelle richieste POST per garantire che la stessa operazione non venga eseguita più di una volta in caso di retry. |
| **BFF** | Backend-for-Frontend: pattern architetturale che prevede un servizio backend dedicato per ogni tipo di client (web, mobile, IoT). |
| **Keyset Pagination** | Tecnica di paginazione a livello database che utilizza clausole WHERE con operatori di confronto anziché OFFSET, garantendo prestazioni costanti. |
| **Contract Testing** | Approccio di testing che verifica la compatibilità tra consumer e provider di un'API senza richiedere l'esecuzione simultanea di entrambi i servizi. |
| **Dead Letter Queue** | Coda che raccoglie messaggi (webhook, eventi) che hanno fallito tutti i tentativi di consegna, preservandoli per ispezione e reprocessamento. |
| **Deadline (gRPC)** | Tempo massimo che un client è disposto ad attendere per il completamento di una RPC, propagato automaticamente attraverso la catena di servizi. |
| **Interceptor (gRPC)** | Funzione che intercetta le chiamate RPC per eseguire logica trasversale come logging, autenticazione, metriche e tracing. |
| **Sunset Header** | Header HTTP (RFC 8594) che indica la data dopo la quale un endpoint API non sarà più disponibile, utilizzato per comunicare la deprecazione. |
| **Token Bucket** | Algoritmo di rate limiting che utilizza un bucket virtuale di token rifornito a rate costante, permettendo burst controllati fino alla capacità del bucket. |
