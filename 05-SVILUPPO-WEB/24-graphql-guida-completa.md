---
corso: "Sviluppo Web Full-Stack"
fase: "7 — Architetture Avanzate"
modulo: 24
titolo: "GraphQL — Guida Completa"
versione: "GraphQL June 2018 Spec / Apollo 4.x / Yoga 5.x"
livello: "Avanzato"
prerequisiti: ["11-api-design", "06-typescript"]
obiettivi:
  - "Progettare schema GraphQL schema-first con type system fortemente tipizzato"
  - "Implementare resolver efficienti con DataLoader per evitare N+1"
  - "Configurare Apollo Server/Client con cache normalizzata"
  - "Applicare autenticazione, autorizzazione e limiti di complessità"
  - "Scalare con Apollo Federation e subscription real-time"
tag: [graphql, apollo, schema, resolvers, dataloader, federation, subscriptions]
---

# GraphQL — Guida Completa

> **Modulo 24** · **Versione:** 1.0 · **Aggiornamento:** 2026-05-24

> **Obiettivi di apprendimento**
>
> 1. Progettare schema GraphQL schema-first con type system fortemente tipizzato
> 2. Implementare resolver efficienti con DataLoader per evitare N+1
> 3. Configurare Apollo Server/Client con cache normalizzata
> 4. Applicare autenticazione, autorizzazione e limiti di complessità
> 5. Scalare con Apollo Federation e subscription real-time
>
> **Prerequisiti:** [API Design](11-api-design.md), [TypeScript](06-typescript.md)
> **Tempo stimato:** 6-8 ore · **Livello:** Avanzato

## Idee guida

1. **Schema-first: il contratto precede l'implementazione.** Lo schema GraphQL è il punto di verità tra client e server — definirlo prima di scrivere qualsiasi resolver.
2. **Chiedi esattamente ciò che serve, niente di più.** Il client specifica la forma della risposta, eliminando over-fetching e under-fetching per design.
3. **Un singolo endpoint, un type system fortemente tipizzato.** Tutto transita da `/graphql` — lo schema è la documentazione vivente dell'API.
4. **DataLoader è obbligatorio: senza batching, N+1 è inevitabile.** Ogni resolver che accede a dati deve passare per un DataLoader.
5. **Defense in depth: complessità, profondità, rate limiting.** GraphQL espone un linguaggio di query — limitarlo è un obbligo di sicurezza, non un'opzione.

---

## Indice

1. [Fondamenti GraphQL](#1-fondamenti-graphql)
2. [Type System e Schema Design](#2-type-system-e-schema-design)
3. [Query, Mutation e Subscription](#3-query-mutation-e-subscription)
4. [Architettura dei Resolver](#4-architettura-dei-resolver)
5. [Apollo Server](#5-apollo-server)
6. [Apollo Client](#6-apollo-client)
7. [Alternative: Yoga, Mercurius, Pothos, URQL](#7-alternative-yoga-mercurius-pothos-urql)
8. [Autenticazione e Autorizzazione](#8-autenticazione-e-autorizzazione)
9. [Performance e Ottimizzazione](#9-performance-e-ottimizzazione)
10. [Paginazione](#10-paginazione)
11. [Subscription e Real-Time](#11-subscription-e-real-time)
12. [Apollo Federation](#12-apollo-federation)
13. [Code Generation](#13-code-generation)
14. [Testing](#14-testing)
15. [GraphQL vs REST](#15-graphql-vs-rest)
16. [Sicurezza](#16-sicurezza)
17. [Gestione File](#17-gestione-file)
18. [Error Handling](#18-error-handling)
19. [Tooling](#19-tooling)
20. [Troubleshooting](#20-troubleshooting)
21. [FAQ](#21-faq)
22. [Best Practice e Anti-Pattern](#22-best-practice-e-anti-pattern)
23. [Esercizi Pratici](#23-esercizi-pratici)
24. [Glossario](#24-glossario)
25. [Letture e Risorse](#25-letture-e-risorse)

---

## 1. Fondamenti GraphQL

GraphQL è un linguaggio di query per API e un runtime per eseguire tali query, creato da Facebook nel 2012 e rilasciato come standard aperto nel 2015. A differenza di REST, dove il server determina la forma della risposta, in GraphQL è il client a specificare esattamente quali dati servono e in quale struttura.

Il modello mentale corretto non è "un endpoint per risorsa" (REST) ma "un grafo di dati con un punto di ingresso unico". Il client naviga il grafo dichiarando la forma desiderata; il server risolve ogni nodo del grafo attraverso funzioni chiamate **resolver**.

### 1.1 Principi Architetturali

**Un singolo endpoint.** Tutte le operazioni transitano da `POST /graphql`. Non esistono endpoint separati per risorse diverse. Questo semplifica il routing, il middleware e la configurazione del proxy, ma sposta la complessità nella gestione della query stessa.

**Schema come contratto.** Lo schema GraphQL è un documento SDL (Schema Definition Language) che definisce ogni tipo, campo, argomento e relazione esposti dall'API. È simultaneamente la specifica, la documentazione e la validazione dell'API. Qualsiasi query che non rispetta lo schema viene rifiutata dal runtime prima ancora che un resolver venga invocato.

**Tipizzazione forte.** Ogni campo ha un tipo dichiarato. Il runtime valida le query contro lo schema a compile-time (o request-time), garantendo che i client non possano richiedere campi inesistenti o passare argomenti del tipo sbagliato.

**Introspezione.** Lo schema è interrogabile a runtime tramite query speciali (`__schema`, `__type`), abilitando tooling automatico come GraphiQL, code generation e validazione client. Questa caratteristica deve essere **disabilitata in produzione** per ragioni di sicurezza.

### 1.2 Schema-First vs Code-First

Esistono due filosofie per definire lo schema GraphQL:

**Schema-first** (SDL-first): si scrive lo schema in SDL e poi si implementano i resolver che lo soddisfano. Vantaggi: il contratto è leggibile, i team possono concordare sull'API prima di implementare, i tool di code generation partono dallo schema.

```graphql
# schema.graphql — scritto a mano
type User {
  id: ID!
  name: String!
  email: String!
  posts: [Post!]!
}

type Query {
  user(id: ID!): User
  users(limit: Int = 10, offset: Int = 0): [User!]!
}
```

**Code-first**: lo schema è generato dal codice TypeScript/JavaScript. Vantaggi: un'unica source of truth nel codice, type safety completa, refactoring più sicuro.

```typescript
// Con Pothos (code-first builder)
import SchemaBuilder from '@pothos/core';

const builder = new SchemaBuilder({});

const UserType = builder.objectRef<UserModel>('User');

builder.objectType(UserType, {
  fields: (t) => ({
    id: t.exposeID('id'),
    name: t.exposeString('name'),
    email: t.exposeString('email'),
    posts: t.field({
      type: [PostType],
      resolve: (user, _args, ctx) => ctx.loaders.postsByUser.load(user.id),
    }),
  }),
});
```

Nessuno dei due approcci è intrinsecamente superiore. Schema-first è preferito per API pubbliche dove il contratto è il deliverable primario. Code-first è preferito per team che lavorano interamente in TypeScript e vogliono type safety end-to-end.

### 1.3 L'Execution Model

Quando una query arriva al server GraphQL, il runtime esegue questi passaggi:

1. **Parsing** — La stringa della query viene trasformata in un AST (Abstract Syntax Tree).
2. **Validation** — L'AST viene validato contro lo schema. Campi inesistenti, tipi sbagliati, argomenti mancanti vengono rifiutati con errori specifici.
3. **Execution** — L'AST validato viene attraversato in profondità. Per ogni campo, il runtime invoca il resolver corrispondente. I resolver vengono eseguiti in parallelo dove possibile (campi fratelli), in sequenza dove necessario (campi padre-figlio).
4. **Response** — I risultati di tutti i resolver vengono assemblati nella struttura richiesta dal client e serializzati in JSON.

```
Query string → Parse → AST → Validate → Execute resolvers → JSON response
```

Questo modello ha implicazioni importanti: la validazione avviene prima dell'esecuzione (fail-fast), i resolver sono lazy (eseguiti solo se il campo è richiesto), e la forma della risposta rispecchia esattamente la forma della query.

---

## 2. Type System e Schema Design

Il type system di GraphQL è il fondamento su cui poggia l'intera API. Ogni elemento esposto dall'API deve avere un tipo dichiarato nello schema.

### 2.1 Tipi Scalari

I tipi scalari sono i leaf node del grafo — rappresentano valori atomici.

**Scalari built-in:**

| Scalare | Descrizione | Esempio |
|---------|-------------|---------|
| `Int` | Intero con segno a 32 bit | `42` |
| `Float` | Numero a virgola mobile IEEE 754 | `3.14` |
| `String` | Sequenza di caratteri UTF-8 | `"hello"` |
| `Boolean` | `true` o `false` | `true` |
| `ID` | Identificatore univoco, serializzato come stringa | `"abc-123"` |

**Scalari custom:** quando i tipi built-in non bastano, si definiscono scalari custom con logica di serializzazione, parsing e validazione.

```graphql
scalar DateTime
scalar EmailAddress
scalar URL
scalar JSON
scalar PositiveInt
scalar Currency
```

```typescript
import { GraphQLScalarType, Kind } from 'graphql';

const DateTimeScalar = new GraphQLScalarType({
  name: 'DateTime',
  description: 'ISO 8601 datetime string',
  serialize(value: Date): string {
    return value.toISOString();
  },
  parseValue(value: string): Date {
    const date = new Date(value);
    if (isNaN(date.getTime())) {
      throw new TypeError(`Invalid DateTime: ${value}`);
    }
    return date;
  },
  parseLiteral(ast): Date {
    if (ast.kind !== Kind.STRING) {
      throw new TypeError('DateTime must be a string');
    }
    return new Date(ast.value);
  },
});
```

Librerie come `graphql-scalars` forniscono decine di scalari custom pre-validati (email, URL, UUID, date, valute). Preferire queste implementazioni testate a implementazioni custom quando possibile.

### 2.2 Object Types

Gli object type sono il cuore dello schema — rappresentano le entità del dominio.

```graphql
type User {
  id: ID!
  username: String!
  email: String!
  displayName: String
  avatar: URL
  role: UserRole!
  createdAt: DateTime!
  updatedAt: DateTime!
  posts(first: Int = 10, after: String): PostConnection!
  followers: [User!]!
  followersCount: Int!
}

type Post {
  id: ID!
  title: String!
  content: String!
  slug: String!
  status: PostStatus!
  author: User!
  tags: [Tag!]!
  comments(first: Int = 10, after: String): CommentConnection!
  commentsCount: Int!
  publishedAt: DateTime
  createdAt: DateTime!
}
```

Regole di design per object types:

- **Non-null per default.** Usare `!` per tutti i campi che il server garantisce sempre presenti. Riservare la nullabilità solo per campi genuinamente opzionali.
- **Campi derivati accanto ai dati.** `followersCount` accanto a `followers` evita che il client debba contare localmente una lista potenzialmente paginata.
- **Nessun campo che espone dettagli di implementazione.** Mai `databaseId`, `_internalStatus` o simili nello schema pubblico.

### 2.3 Enum Types

Gli enum definiscono un insieme chiuso di valori validi.

```graphql
enum UserRole {
  ADMIN
  EDITOR
  AUTHOR
  VIEWER
}

enum PostStatus {
  DRAFT
  REVIEW
  PUBLISHED
  ARCHIVED
}

enum SortDirection {
  ASC
  DESC
}
```

Gli enum sono essenziali per la type safety — il runtime rifiuta qualsiasi valore non presente nell'enum. Preferire enum a stringhe libere ogni volta che l'insieme dei valori è finito e noto.

### 2.4 Interface Types

Le interfacce definiscono un insieme di campi che più tipi devono implementare.

```graphql
interface Node {
  id: ID!
}

interface Timestamped {
  createdAt: DateTime!
  updatedAt: DateTime!
}

type User implements Node & Timestamped {
  id: ID!
  name: String!
  email: String!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type Post implements Node & Timestamped {
  id: ID!
  title: String!
  content: String!
  createdAt: DateTime!
  updatedAt: DateTime!
}
```

L'interfaccia `Node` (un singolo campo `id: ID!`) è un pattern universale reso celebre dalla Relay specification. Permette di implementare il refetching di qualsiasi entità dato il suo ID globale.

### 2.5 Union Types

Le union rappresentano un tipo che può essere uno tra diversi tipi concreti, senza campi in comune.

```graphql
union SearchResult = User | Post | Comment | Tag

type Query {
  search(query: String!): [SearchResult!]!
}
```

Il client discrimina il tipo concreto con `__typename` o inline fragment:

```graphql
query SearchAll {
  search(query: "GraphQL") {
    __typename
    ... on User {
      id
      name
      email
    }
    ... on Post {
      id
      title
      slug
    }
    ... on Comment {
      id
      body
    }
  }
}
```

La differenza tra interface e union: le interfacce condividono campi, le union no. Se i tipi hanno campi in comune, usare un'interfaccia. Se non hanno nulla in comune, usare una union.

### 2.6 Input Types

Gli input type servono per strutturare gli argomenti di mutation e query complesse. Non possono essere usati come tipi di output.

```graphql
input CreateUserInput {
  username: String!
  email: EmailAddress!
  displayName: String
  role: UserRole = VIEWER
}

input UpdateUserInput {
  username: String
  email: EmailAddress
  displayName: String
  role: UserRole
}

input PostFilterInput {
  status: PostStatus
  authorId: ID
  tagSlugs: [String!]
  publishedAfter: DateTime
  publishedBefore: DateTime
  search: String
}

input PaginationInput {
  first: Int = 10
  after: String
}
```

Pattern critico: **separare sempre `Create*Input` da `Update*Input`**. Nel create, i campi obbligatori sono non-null. Nell'update, tutti i campi sono nullable (il client invia solo ciò che vuole modificare).

### 2.7 Directives

Le directive sono annotazioni che modificano il comportamento dello schema o dell'esecuzione.

**Directive built-in:**

```graphql
# @deprecated — segna un campo come deprecato
type User {
  name: String! @deprecated(reason: "Use displayName instead")
  displayName: String!
}

# @skip e @include — condizionano l'inclusione di un campo nella query
query UserProfile($withPosts: Boolean!) {
  user(id: "1") {
    name
    posts @include(if: $withPosts) {
      title
    }
  }
}

# @specifiedBy — indica la specifica per uno scalare custom
scalar EmailAddress @specifiedBy(url: "https://html.spec.whatwg.org/#valid-e-mail-address")
```

**Directive custom** — usate per autenticazione, caching, validazione:

```graphql
directive @auth(requires: UserRole = ADMIN) on FIELD_DEFINITION | OBJECT
directive @cacheControl(maxAge: Int!, scope: CacheControlScope = PUBLIC) on FIELD_DEFINITION | OBJECT
directive @rateLimit(max: Int!, window: String!) on FIELD_DEFINITION
directive @validate(max: Int, min: Int, pattern: String) on ARGUMENT_DEFINITION | INPUT_FIELD_DEFINITION

type Query {
  users: [User!]! @auth(requires: ADMIN) @rateLimit(max: 100, window: "1m")
  publicPosts: [Post!]! @cacheControl(maxAge: 300)
}
```

L'implementazione di una directive custom richiede un **schema transformer** che intercetta la risoluzione dei campi annotati:

```typescript
import { mapSchema, getDirective, MapperKind } from '@graphql-tools/utils';
import { defaultFieldResolver, GraphQLSchema } from 'graphql';

function authDirectiveTransformer(schema: GraphQLSchema): GraphQLSchema {
  return mapSchema(schema, {
    [MapperKind.OBJECT_FIELD]: (fieldConfig) => {
      const authDirective = getDirective(schema, fieldConfig, 'auth')?.[0];
      if (!authDirective) return fieldConfig;

      const requiredRole = authDirective.requires;
      const originalResolve = fieldConfig.resolve ?? defaultFieldResolver;

      fieldConfig.resolve = async (source, args, context, info) => {
        if (!context.user) {
          throw new AuthenticationError('Not authenticated');
        }
        if (!hasRole(context.user, requiredRole)) {
          throw new ForbiddenError(`Requires role: ${requiredRole}`);
        }
        return originalResolve(source, args, context, info);
      };

      return fieldConfig;
    },
  });
}
```

---

## 3. Query, Mutation e Subscription

GraphQL definisce tre tipi di operazione radice: **Query** (lettura), **Mutation** (scrittura), **Subscription** (streaming).

### 3.1 Query

Le query sono operazioni di sola lettura. Il client specifica esattamente i campi desiderati.

```graphql
# Query semplice
query GetUser {
  user(id: "42") {
    id
    name
    email
  }
}

# Query con variabili
query GetUser($userId: ID!) {
  user(id: $userId) {
    id
    name
    email
    posts(first: 5) {
      edges {
        node {
          id
          title
          publishedAt
        }
      }
    }
  }
}

# Query con fragment (riuso di selezioni)
fragment UserBasicFields on User {
  id
  name
  email
  avatar
}

query Dashboard {
  me {
    ...UserBasicFields
    role
  }
  recentPosts(first: 10) {
    edges {
      node {
        id
        title
        author {
          ...UserBasicFields
        }
      }
    }
  }
}
```

**Fragment:** i fragment sono il meccanismo di riuso delle selezioni. Definiscono un insieme di campi su un tipo e possono essere inclusi in qualsiasi selezione su quel tipo. Sono essenziali per evitare duplicazione nelle query complesse e sono il fondamento su cui opera il code generation.

### 3.2 Mutation

Le mutation rappresentano operazioni di scrittura — creazione, aggiornamento, cancellazione.

```graphql
type Mutation {
  createUser(input: CreateUserInput!): CreateUserPayload!
  updateUser(id: ID!, input: UpdateUserInput!): UpdateUserPayload!
  deleteUser(id: ID!): DeleteUserPayload!
  publishPost(id: ID!): PublishPostPayload!
  addComment(input: AddCommentInput!): AddCommentPayload!
}

# Payload pattern — ogni mutation restituisce un payload dedicato
type CreateUserPayload {
  user: User
  errors: [MutationError!]!
}

type MutationError {
  field: String
  message: String!
  code: ErrorCode!
}
```

Convenzioni per le mutation:

- **Input pattern:** un singolo argomento `input` con un input type dedicato. Questo permette di aggiungere campi alla mutation senza breaking changes.
- **Payload pattern:** ogni mutation restituisce un payload type dedicato con il risultato e eventuali errori. Mai restituire direttamente il tipo dell'entità.
- **Naming:** verbo + sostantivo (`createUser`, `publishPost`, `addComment`). Mai nomi ambigui come `handleUser` o `processPost`.

```graphql
# Query con variabili per la mutation
mutation CreateNewUser($input: CreateUserInput!) {
  createUser(input: $input) {
    user {
      id
      name
      email
    }
    errors {
      field
      message
      code
    }
  }
}

# Variabili
{
  "input": {
    "username": "marco_rossi",
    "email": "marco@example.com",
    "displayName": "Marco Rossi"
  }
}
```

### 3.3 Subscription

Le subscription abilitano lo streaming di dati in tempo reale dal server al client.

```graphql
type Subscription {
  postPublished: Post!
  commentAdded(postId: ID!): Comment!
  userStatusChanged(userId: ID!): UserStatus!
  notificationReceived: Notification!
}

# Client-side
subscription OnNewComment($postId: ID!) {
  commentAdded(postId: $postId) {
    id
    body
    author {
      name
      avatar
    }
    createdAt
  }
}
```

Le subscription verranno approfondite nella sezione dedicata [11. Subscription e Real-Time](#11-subscription-e-real-time).

### 3.4 Alias e Operazioni Multiple

Gli alias permettono di rinominare i campi nella risposta, utile per richiedere lo stesso campo con argomenti diversi.

```graphql
query ComparePosts {
  recentPosts: posts(sort: RECENT, first: 5) {
    id
    title
  }
  popularPosts: posts(sort: POPULAR, first: 5) {
    id
    title
  }
}
```

Risposta:

```json
{
  "data": {
    "recentPosts": [{ "id": "1", "title": "..." }],
    "popularPosts": [{ "id": "5", "title": "..." }]
  }
}
```

---

## 4. Architettura dei Resolver

I resolver sono funzioni che calcolano il valore di ogni campo nello schema. La loro architettura determina le prestazioni e la manutenibilità dell'intera API.

### 4.1 Anatomia di un Resolver

Ogni resolver riceve quattro argomenti:

```typescript
type ResolverFn<TResult, TParent, TContext, TArgs> = (
  parent: TParent,    // Valore restituito dal resolver del campo padre
  args: TArgs,        // Argomenti passati al campo nella query
  context: TContext,  // Oggetto condiviso tra tutti i resolver (DB, auth, loaders)
  info: GraphQLResolveInfo  // Metadati sull'esecuzione (AST, schema, path)
) => TResult | Promise<TResult>;
```

```typescript
const resolvers = {
  Query: {
    user: async (_parent, { id }, context) => {
      return context.dataSources.users.findById(id);
    },
    users: async (_parent, { limit, offset, filter }, context) => {
      return context.dataSources.users.findMany({ limit, offset, filter });
    },
  },
  User: {
    posts: async (user, { first, after }, context) => {
      return context.loaders.postsByAuthor.load({
        authorId: user.id,
        first,
        after,
      });
    },
    followersCount: async (user, _args, context) => {
      return context.loaders.followersCount.load(user.id);
    },
  },
};
```

### 4.2 Resolver Chain

I resolver formano una catena: il valore restituito dal resolver padre diventa il primo argomento (`parent`) del resolver figlio.

```
Query.user(_, {id: "42"}, ctx) → { id: "42", name: "Marco", ... }
  └─ User.posts(user, {first: 5}, ctx) → [Post, Post, ...]
       └─ Post.author(post, _, ctx) → { id: "7", name: "..." }
       └─ Post.comments(post, {first: 10}, ctx) → [Comment, ...]
            └─ Comment.author(comment, _, ctx) → { id: "3", ... }
```

**Default resolver:** se non si definisce un resolver per un campo, GraphQL usa un resolver di default che restituisce `parent[fieldName]`. Questo significa che per campi semplici che corrispondono a proprietà dell'oggetto padre non serve scrivere resolver.

### 4.3 Context Object

Il context è l'oggetto condiviso tra tutti i resolver di una singola richiesta. È il luogo canonico per:

- **Utente autenticato** — `context.user`
- **DataSource e database** — `context.dataSources`, `context.db`
- **DataLoader** — `context.loaders`
- **Request metadata** — `context.requestId`, `context.ip`

```typescript
// Creazione del context per ogni richiesta
const server = new ApolloServer({
  typeDefs,
  resolvers,
});

const { url } = await startStandaloneServer(server, {
  context: async ({ req }) => {
    const token = req.headers.authorization?.replace('Bearer ', '');
    const user = token ? await verifyToken(token) : null;

    return {
      user,
      requestId: crypto.randomUUID(),
      db: prisma,
      loaders: createLoaders(),
      dataSources: {
        users: new UserDataSource(prisma),
        posts: new PostDataSource(prisma),
      },
    };
  },
});
```

**Regola critica:** il context deve essere ricreato per ogni richiesta. Mai condividere DataLoader o stato mutabile tra richieste diverse.

### 4.4 DataLoader — N+1 Prevention

Il problema N+1 è il nemico numero uno delle performance GraphQL. Si manifesta quando un campo relazionale viene risolto con una query separata per ogni elemento della lista.

```
# Senza DataLoader — N+1 query
Query.users → SELECT * FROM users LIMIT 10              (1 query)
  User[0].posts → SELECT * FROM posts WHERE author_id=1  (1 query)
  User[1].posts → SELECT * FROM posts WHERE author_id=2  (1 query)
  ...
  User[9].posts → SELECT * FROM posts WHERE author_id=10 (1 query)
# Totale: 11 query per 10 utenti. Con 1000 utenti → 1001 query.
```

DataLoader risolve il problema con **batching** e **caching per richiesta:**

```typescript
import DataLoader from 'dataloader';

function createLoaders() {
  return {
    // Batch: raccoglie tutti gli ID richiesti in un tick,
    // poi esegue una singola query
    userById: new DataLoader<string, User>(async (ids) => {
      const users = await prisma.user.findMany({
        where: { id: { in: [...ids] } },
      });
      // CRITICO: restituire i risultati nello stesso ordine degli ID
      const userMap = new Map(users.map((u) => [u.id, u]));
      return ids.map((id) => userMap.get(id) ?? new Error(`User ${id} not found`));
    }),

    postsByAuthor: new DataLoader<string, Post[]>(async (authorIds) => {
      const posts = await prisma.post.findMany({
        where: { authorId: { in: [...authorIds] } },
      });
      const grouped = new Map<string, Post[]>();
      for (const post of posts) {
        const list = grouped.get(post.authorId) ?? [];
        list.push(post);
        grouped.set(post.authorId, list);
      }
      return authorIds.map((id) => grouped.get(id) ?? []);
    }),
  };
}
```

```
# Con DataLoader — batch query
Query.users → SELECT * FROM users LIMIT 10                             (1 query)
  DataLoader raccoglie: [1, 2, 3, ..., 10]
  → SELECT * FROM posts WHERE author_id IN (1, 2, 3, ..., 10)          (1 query)
# Totale: 2 query, indipendentemente dal numero di utenti.
```

**Regole DataLoader:**

1. **Un'istanza per richiesta.** Creare i DataLoader nella context factory, mai come singleton.
2. **L'ordine conta.** La funzione batch deve restituire i risultati nello stesso ordine degli ID di input.
3. **Errori per elemento.** Se un ID non esiste, restituire un `Error` nella posizione corrispondente, non `null`.
4. **Caching per richiesta.** DataLoader cacha automaticamente i risultati per la durata della richiesta — la stessa entità richiesta due volte produce una sola query.

### 4.5 Data Sources

Il pattern Data Source astrae l'accesso ai dati dietro un'interfaccia coerente.

```typescript
class UserDataSource {
  private db: PrismaClient;

  constructor(db: PrismaClient) {
    this.db = db;
  }

  async findById(id: string): Promise<User | null> {
    return this.db.user.findUnique({ where: { id } });
  }

  async findMany(opts: {
    limit: number;
    offset: number;
    filter?: UserFilter;
  }): Promise<User[]> {
    return this.db.user.findMany({
      where: this.buildWhere(opts.filter),
      take: opts.limit,
      skip: opts.offset,
      orderBy: { createdAt: 'desc' },
    });
  }

  async create(input: CreateUserInput): Promise<User> {
    return this.db.user.create({ data: input });
  }

  async update(id: string, input: UpdateUserInput): Promise<User> {
    return this.db.user.update({
      where: { id },
      data: input,
    });
  }

  async delete(id: string): Promise<boolean> {
    await this.db.user.delete({ where: { id } });
    return true;
  }

  private buildWhere(filter?: UserFilter) {
    if (!filter) return {};
    return {
      ...(filter.role && { role: filter.role }),
      ...(filter.search && {
        OR: [
          { name: { contains: filter.search, mode: 'insensitive' } },
          { email: { contains: filter.search, mode: 'insensitive' } },
        ],
      }),
    };
  }
}
```

---

## 5. Apollo Server

Apollo Server è il server GraphQL più diffuso nell'ecosistema JavaScript/TypeScript. Dalla versione 4, è framework-agnostico — si integra con Express, Fastify, Koa, standalone HTTP, Lambda, CloudFlare Workers.

### 5.1 Setup Base

```typescript
import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { readFileSync } from 'fs';

// Schema SDL
const typeDefs = readFileSync('./schema.graphql', 'utf-8');

// Resolvers
const resolvers = {
  Query: {
    users: async (_parent, args, context) => {
      return context.dataSources.users.findMany(args);
    },
  },
  Mutation: {
    createUser: async (_parent, { input }, context) => {
      const user = await context.dataSources.users.create(input);
      return { user, errors: [] };
    },
  },
};

const server = new ApolloServer({
  typeDefs,
  resolvers,
  introspection: process.env.NODE_ENV !== 'production',
  plugins: [
    process.env.NODE_ENV === 'production'
      ? ApolloServerPluginLandingPageDisabled()
      : ApolloServerPluginLandingPageLocalDefault(),
  ],
});

const { url } = await startStandaloneServer(server, {
  listen: { port: 4000 },
  context: async ({ req }) => ({
    user: await authenticateRequest(req),
    loaders: createLoaders(),
    dataSources: createDataSources(),
  }),
});

console.log(`Server ready at ${url}`);
```

### 5.2 Integrazione con Express

```typescript
import express from 'express';
import http from 'http';
import cors from 'cors';
import { ApolloServer } from '@apollo/server';
import { expressMiddleware } from '@apollo/server/express4';
import { ApolloServerPluginDrainHttpServer } from '@apollo/server/plugin/drainHttpServer';

const app = express();
const httpServer = http.createServer(app);

const server = new ApolloServer({
  typeDefs,
  resolvers,
  plugins: [ApolloServerPluginDrainHttpServer({ httpServer })],
});

await server.start();

app.use(
  '/graphql',
  cors<cors.CorsRequest>({
    origin: ['https://app.example.com'],
    credentials: true,
  }),
  express.json({ limit: '1mb' }),
  expressMiddleware(server, {
    context: async ({ req }) => ({
      user: await authenticateRequest(req),
      loaders: createLoaders(),
      dataSources: createDataSources(),
    }),
  }),
);

await new Promise<void>((resolve) =>
  httpServer.listen({ port: 4000 }, resolve),
);
```

### 5.3 Plugin System

I plugin di Apollo Server intercettano il ciclo di vita della richiesta.

```typescript
import type { ApolloServerPlugin } from '@apollo/server';

const loggingPlugin: ApolloServerPlugin = {
  async requestDidStart(requestContext) {
    const start = Date.now();
    const { query, operationName } = requestContext.request;

    return {
      async didResolveOperation(ctx) {
        console.log(`Operation: ${ctx.operationName}`);
      },
      async didEncounterErrors(ctx) {
        for (const error of ctx.errors) {
          console.error(`GraphQL Error: ${error.message}`, {
            operationName: ctx.operationName,
            path: error.path,
            extensions: error.extensions,
          });
        }
      },
      async willSendResponse() {
        const duration = Date.now() - start;
        console.log(`${operationName ?? 'anonymous'}: ${duration}ms`);
      },
    };
  },
};

// Query complexity plugin
const complexityPlugin: ApolloServerPlugin = {
  async requestDidStart() {
    return {
      async didResolveOperation(ctx) {
        const complexity = calculateComplexity(ctx.document, ctx.schema);
        if (complexity > MAX_COMPLEXITY) {
          throw new GraphQLError(
            `Query complexity ${complexity} exceeds maximum ${MAX_COMPLEXITY}`,
            { extensions: { code: 'QUERY_TOO_COMPLEX', complexity } },
          );
        }
      },
    };
  },
};
```

### 5.4 Caching con Apollo

```graphql
# Direttiva @cacheControl nello schema
type Query {
  publicPosts: [Post!]! @cacheControl(maxAge: 300)
}

type Post @cacheControl(maxAge: 600) {
  id: ID!
  title: String!
  content: String!
  author: User! @cacheControl(maxAge: 60)
}
```

```typescript
import responseCachePlugin from '@apollo/server-plugin-response-cache';
import { KeyvAdapter } from '@apollo/utils.keyvadapter';
import Keyv from 'keyv';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  plugins: [
    responseCachePlugin({
      cache: new KeyvAdapter(new Keyv('redis://localhost:6379')),
      sessionId: (ctx) => ctx.request.http?.headers.get('authorization') ?? null,
    }),
  ],
});
```

### 5.5 Error Handling in Apollo Server

```typescript
import { GraphQLError } from 'graphql';

// Errori business con codici specifici
class NotFoundError extends GraphQLError {
  constructor(entity: string, id: string) {
    super(`${entity} with id ${id} not found`, {
      extensions: {
        code: 'NOT_FOUND',
        entity,
        id,
      },
    });
  }
}

class ValidationError extends GraphQLError {
  constructor(field: string, message: string) {
    super(message, {
      extensions: {
        code: 'VALIDATION_ERROR',
        field,
      },
    });
  }
}

class AuthenticationError extends GraphQLError {
  constructor(message = 'Not authenticated') {
    super(message, {
      extensions: { code: 'UNAUTHENTICATED' },
    });
  }
}

class ForbiddenError extends GraphQLError {
  constructor(message = 'Forbidden') {
    super(message, {
      extensions: { code: 'FORBIDDEN' },
    });
  }
}

// Uso nei resolver
const resolvers = {
  Query: {
    user: async (_parent, { id }, context) => {
      if (!context.user) throw new AuthenticationError();
      const user = await context.dataSources.users.findById(id);
      if (!user) throw new NotFoundError('User', id);
      return user;
    },
  },
};
```

---

## 6. Apollo Client

Apollo Client è la libreria client GraphQL più completa per React e altri framework frontend.

### 6.1 Setup e Configurazione

```typescript
import {
  ApolloClient,
  InMemoryCache,
  HttpLink,
  ApolloLink,
  from,
} from '@apollo/client';

const httpLink = new HttpLink({
  uri: 'https://api.example.com/graphql',
  credentials: 'include',
});

const authLink = new ApolloLink((operation, forward) => {
  const token = localStorage.getItem('auth_token');
  operation.setContext(({ headers = {} }) => ({
    headers: {
      ...headers,
      authorization: token ? `Bearer ${token}` : '',
    },
  }));
  return forward(operation);
});

const errorLink = onError(({ graphQLErrors, networkError }) => {
  if (graphQLErrors) {
    for (const { message, extensions } of graphQLErrors) {
      if (extensions?.code === 'UNAUTHENTICATED') {
        // Redirect to login
        window.location.href = '/login';
      }
      console.error(`[GraphQL Error]: ${message}`);
    }
  }
  if (networkError) {
    console.error(`[Network Error]: ${networkError.message}`);
  }
});

const client = new ApolloClient({
  link: from([errorLink, authLink, httpLink]),
  cache: new InMemoryCache({
    typePolicies: {
      Query: {
        fields: {
          posts: {
            keyArgs: ['filter'],
            merge(existing, incoming, { args }) {
              if (!args?.after) return incoming;
              return {
                ...incoming,
                edges: [...(existing?.edges ?? []), ...incoming.edges],
              };
            },
          },
        },
      },
    },
  }),
  defaultOptions: {
    watchQuery: {
      fetchPolicy: 'cache-and-network',
      errorPolicy: 'all',
    },
  },
});
```

### 6.2 Query con Hooks

```tsx
import { useQuery, gql } from '@apollo/client';

const GET_USERS = gql`
  query GetUsers($first: Int!, $after: String, $filter: UserFilterInput) {
    users(first: $first, after: $after, filter: $filter) {
      edges {
        node {
          id
          name
          email
          avatar
          role
        }
      }
      pageInfo {
        hasNextPage
        endCursor
      }
      totalCount
    }
  }
`;

function UserList() {
  const { data, loading, error, fetchMore } = useQuery(GET_USERS, {
    variables: { first: 20 },
    notifyOnNetworkStatusChange: true,
  });

  if (error) return <ErrorBanner message={error.message} />;
  if (loading && !data) return <Skeleton />;

  const { edges, pageInfo } = data.users;

  return (
    <>
      <ul>
        {edges.map(({ node }) => (
          <UserCard key={node.id} user={node} />
        ))}
      </ul>
      {pageInfo.hasNextPage && (
        <button
          onClick={() =>
            fetchMore({
              variables: { after: pageInfo.endCursor },
            })
          }
          disabled={loading}
        >
          Carica altri
        </button>
      )}
    </>
  );
}
```

### 6.3 Mutation con Hooks

```tsx
import { useMutation, gql } from '@apollo/client';

const CREATE_USER = gql`
  mutation CreateUser($input: CreateUserInput!) {
    createUser(input: $input) {
      user {
        id
        name
        email
      }
      errors {
        field
        message
        code
      }
    }
  }
`;

function CreateUserForm() {
  const [createUser, { loading }] = useMutation(CREATE_USER, {
    update(cache, { data: { createUser } }) {
      if (createUser.errors.length > 0) return;

      cache.modify({
        fields: {
          users(existingUsers = { edges: [] }) {
            const newUserRef = cache.writeFragment({
              data: createUser.user,
              fragment: gql`
                fragment NewUser on User {
                  id
                  name
                  email
                }
              `,
            });
            return {
              ...existingUsers,
              edges: [{ node: newUserRef }, ...existingUsers.edges],
            };
          },
        },
      });
    },
    onError(error) {
      console.error('Mutation failed:', error.message);
    },
  });

  const handleSubmit = async (formData: FormData) => {
    const { data } = await createUser({
      variables: {
        input: {
          username: formData.get('username'),
          email: formData.get('email'),
        },
      },
    });

    if (data?.createUser.errors.length > 0) {
      // Gestire errori di validazione
    }
  };

  return <form onSubmit={handleSubmit}>{/* campi */}</form>;
}
```

### 6.4 Optimistic Updates

Gli optimistic update mostrano il risultato atteso immediatamente, prima che il server confermi.

```typescript
const [toggleLike] = useMutation(TOGGLE_LIKE, {
  optimisticResponse: {
    toggleLike: {
      __typename: 'Post',
      id: postId,
      isLiked: !currentlyLiked,
      likesCount: currentlyLiked ? likesCount - 1 : likesCount + 1,
    },
  },
  update(cache, { data }) {
    cache.modify({
      id: cache.identify({ __typename: 'Post', id: postId }),
      fields: {
        isLiked: () => data.toggleLike.isLiked,
        likesCount: () => data.toggleLike.likesCount,
      },
    });
  },
});
```

### 6.5 Reactive Variables e Local State

```typescript
import { makeVar, useReactiveVar } from '@apollo/client';

// Stato locale reattivo
const currentThemeVar = makeVar<'light' | 'dark'>('light');
const cartItemsVar = makeVar<CartItem[]>([]);

// Uso nei componenti
function ThemeToggle() {
  const theme = useReactiveVar(currentThemeVar);
  return (
    <button onClick={() => currentThemeVar(theme === 'light' ? 'dark' : 'light')}>
      {theme}
    </button>
  );
}

// Integrazione con la cache
const cache = new InMemoryCache({
  typePolicies: {
    Query: {
      fields: {
        currentTheme: {
          read() {
            return currentThemeVar();
          },
        },
        cartItems: {
          read() {
            return cartItemsVar();
          },
        },
      },
    },
  },
});
```

---

## 7. Alternative: Yoga, Mercurius, Pothos, URQL

### 7.1 GraphQL Yoga

GraphQL Yoga (The Guild) è un server GraphQL leggero, compatibile con tutti i runtime JavaScript (Node.js, Deno, Bun, Cloudflare Workers, edge).

```typescript
import { createServer } from 'node:http';
import { createYoga, createSchema } from 'graphql-yoga';

const yoga = createYoga({
  schema: createSchema({
    typeDefs: /* GraphQL */ `
      type Query {
        hello(name: String): String!
      }
    `,
    resolvers: {
      Query: {
        hello: (_, { name }) => `Hello ${name ?? 'World'}`,
      },
    },
  }),
  maskedErrors: process.env.NODE_ENV === 'production',
  graphiql: process.env.NODE_ENV !== 'production',
});

const server = createServer(yoga);
server.listen(4000, () => {
  console.log('Yoga ready on http://localhost:4000/graphql');
});
```

Vantaggi di Yoga rispetto ad Apollo Server: subscription WebSocket/SSE out-of-the-box, file upload multipart nativo, plugin Envelop per modularità, dimensione bundle ridotta, supporto edge runtime.

### 7.2 Mercurius (Fastify)

Mercurius è il plugin GraphQL ufficiale per Fastify — la scelta naturale per chi usa Fastify come framework HTTP.

```typescript
import Fastify from 'fastify';
import mercurius from 'mercurius';

const app = Fastify({ logger: true });

await app.register(mercurius, {
  schema: typeDefs,
  resolvers,
  graphiql: process.env.NODE_ENV !== 'production',
  subscription: true,
  jit: 1, // JIT compilation dopo 1 esecuzione
  cache: true,
  context: (req) => ({
    user: req.user,
    loaders: createLoaders(),
  }),
});

await app.listen({ port: 4000 });
```

Vantaggi: JIT compilation dei resolver (prestazioni superiori), integrazione nativa Fastify lifecycle, federation support, subscription WebSocket integrato.

### 7.3 Pothos (Code-First)

Pothos è il builder code-first più ergonomico per TypeScript. Type safety completa senza code generation.

```typescript
import SchemaBuilder from '@pothos/core';
import PrismaPlugin from '@pothos/plugin-prisma';
import RelayPlugin from '@pothos/plugin-relay';
import type PrismaTypes from '@pothos/plugin-prisma/generated';

const builder = new SchemaBuilder<{
  PrismaTypes: PrismaTypes;
  Context: GraphQLContext;
}>({
  plugins: [PrismaPlugin, RelayPlugin],
  prisma: { client: prisma },
  relayOptions: {
    clientMutationId: 'omit',
    cursorType: 'String',
  },
});

builder.prismaObject('User', {
  fields: (t) => ({
    id: t.exposeID('id'),
    name: t.exposeString('name'),
    email: t.exposeString('email'),
    posts: t.relatedConnection('posts', {
      cursor: 'id',
      query: () => ({ orderBy: { createdAt: 'desc' } }),
    }),
  }),
});

builder.queryType({
  fields: (t) => ({
    user: t.prismaField({
      type: 'User',
      nullable: true,
      args: { id: t.arg.id({ required: true }) },
      resolve: (query, _root, { id }) =>
        prisma.user.findUnique({ ...query, where: { id } }),
    }),
  }),
});

export const schema = builder.toSchema();
```

### 7.4 URQL (Client)

URQL è un'alternativa ad Apollo Client, più leggera e modulare.

```typescript
import { Client, cacheExchange, fetchExchange } from '@urql/core';
import { authExchange } from '@urql/exchange-auth';

const client = new Client({
  url: 'https://api.example.com/graphql',
  exchanges: [
    cacheExchange,
    authExchange(async (utils) => ({
      addAuthToOperation(operation) {
        const token = getToken();
        if (!token) return operation;
        return utils.appendHeaders(operation, {
          Authorization: `Bearer ${token}`,
        });
      },
      didAuthError(error) {
        return error.graphQLErrors.some(
          (e) => e.extensions?.code === 'UNAUTHENTICATED',
        );
      },
      async refreshAuth() {
        const newToken = await refreshToken();
        setToken(newToken);
      },
    })),
    fetchExchange,
  ],
});
```

```tsx
// Uso con React
import { useQuery, useMutation } from 'urql';

function UserList() {
  const [result, reexecute] = useQuery({
    query: GET_USERS,
    variables: { first: 20 },
  });

  const { data, fetching, error } = result;

  if (error) return <p>Error: {error.message}</p>;
  if (fetching) return <Skeleton />;
  return <ul>{/* render users */}</ul>;
}
```

### 7.5 Tabella Comparativa

| Aspetto | Apollo Server | Yoga | Mercurius |
|---------|--------------|------|-----------|
| Runtime | Node.js | Node, Deno, Bun, Edge | Node (Fastify) |
| Schema approach | SDL + code-first | SDL + code-first | SDL |
| Subscription | Plugin separato | Built-in (WS + SSE) | Built-in (WS) |
| File upload | Plugin | Built-in | Plugin |
| JIT | No | No | Si |
| Federation | Si (Gateway) | Si (via Hive) | Si |
| Bundle size | ~700KB | ~200KB | ~150KB |
| Licensing | Elastic v2 | MIT | MIT |

| Aspetto | Apollo Client | URQL | Relay |
|---------|--------------|------|-------|
| Bundle size (min+gz) | ~35KB | ~8KB | ~30KB |
| Cache | Normalized | Document + Normalized | Normalized (strict) |
| Learning curve | Media | Bassa | Alta |
| Framework support | React, Vue, Angular, Svelte | React, Vue, Svelte | React |
| Ecosystem | Vastissimo | Buono | Facebook-centric |

---

## 8. Autenticazione e Autorizzazione

### 8.1 Context-Based Authentication

L'autenticazione in GraphQL avviene nel context factory — il resolver non dovrebbe mai gestire direttamente il parsing del token.

```typescript
// Context factory
async function createContext({ req }: { req: Request }): Promise<GraphQLContext> {
  const token = req.headers.get('authorization')?.replace('Bearer ', '');

  let user: AuthUser | null = null;
  if (token) {
    try {
      const payload = await verifyJWT(token);
      user = await getUserFromPayload(payload);
    } catch {
      // Token invalido — user resta null, non lanciare errore qui.
      // I resolver decidono se l'autenticazione è obbligatoria.
    }
  }

  return {
    user,
    loaders: createLoaders(user),
    dataSources: createDataSources(),
  };
}
```

### 8.2 Field-Level Authorization

L'autorizzazione a livello di campo permette di controllare l'accesso granularmente.

```typescript
const resolvers = {
  User: {
    email: (user, _args, context) => {
      // Solo l'utente stesso o un admin possono vedere l'email
      if (context.user?.id === user.id || context.user?.role === 'ADMIN') {
        return user.email;
      }
      return null; // oppure throw new ForbiddenError()
    },
    privateNotes: (user, _args, context) => {
      if (context.user?.id !== user.id) {
        throw new ForbiddenError('Cannot access private notes of another user');
      }
      return user.privateNotes;
    },
  },
};
```

### 8.3 Auth via Directive

```graphql
directive @auth(requires: UserRole = VIEWER) on FIELD_DEFINITION | OBJECT
directive @owner on FIELD_DEFINITION

type Query {
  me: User! @auth
  users: [User!]! @auth(requires: ADMIN)
  adminDashboard: Dashboard! @auth(requires: ADMIN)
}

type User {
  id: ID!
  name: String!
  email: String! @auth
  privateData: String @owner
}
```

```typescript
// Implementazione del transformer @auth
function authDirectiveTransformer(schema: GraphQLSchema): GraphQLSchema {
  return mapSchema(schema, {
    [MapperKind.OBJECT_FIELD]: (fieldConfig, _fieldName, typeName) => {
      const authDirective = getDirective(schema, fieldConfig, 'auth')?.[0];
      if (!authDirective) return fieldConfig;

      const requiredRole = authDirective.requires ?? 'VIEWER';
      const originalResolve = fieldConfig.resolve ?? defaultFieldResolver;

      fieldConfig.resolve = async (source, args, context, info) => {
        if (!context.user) {
          throw new AuthenticationError('Authentication required');
        }

        const roleHierarchy = ['VIEWER', 'AUTHOR', 'EDITOR', 'ADMIN'];
        const userRoleIndex = roleHierarchy.indexOf(context.user.role);
        const requiredRoleIndex = roleHierarchy.indexOf(requiredRole);

        if (userRoleIndex < requiredRoleIndex) {
          throw new ForbiddenError(
            `Field ${typeName}.${info.fieldName} requires role ${requiredRole}`,
          );
        }

        return originalResolve(source, args, context, info);
      };

      return fieldConfig;
    },
  });
}
```

### 8.4 Pattern: Auth Middleware Layer

Per progetti grandi, centralizzare l'autorizzazione in un middleware layer dedicato:

```typescript
import { shield, rule, and, or, allow, deny } from 'graphql-shield';

const isAuthenticated = rule()((parent, args, ctx) => {
  return ctx.user !== null;
});

const isAdmin = rule()((parent, args, ctx) => {
  return ctx.user?.role === 'ADMIN';
});

const isOwner = rule()((parent, args, ctx) => {
  return parent.userId === ctx.user?.id || parent.id === ctx.user?.id;
});

const permissions = shield(
  {
    Query: {
      me: isAuthenticated,
      users: isAdmin,
      publicPosts: allow,
    },
    Mutation: {
      createPost: isAuthenticated,
      deleteUser: isAdmin,
    },
    User: {
      email: or(isOwner, isAdmin),
      privateData: isOwner,
    },
  },
  {
    fallbackRule: deny,
    allowExternalErrors: true,
  },
);
```

---

## 9. Performance e Ottimizzazione

### 9.1 Query Complexity Analysis

Ogni campo nella query ha un costo computazionale. L'analisi della complessità assegna un peso a ogni campo e rifiuta query che superano un budget.

```typescript
import { createComplexityLimitRule } from 'graphql-validation-complexity';

// Regola di validazione
const complexityRule = createComplexityLimitRule(1000, {
  scalarCost: 1,
  objectCost: 2,
  listFactor: 10,
  onCost: (cost) => {
    console.log(`Query complexity: ${cost}`);
  },
  formatErrorMessage: (cost) =>
    `Query complexity ${cost} exceeds maximum allowed 1000`,
});

// Oppure con graphql-query-complexity
import { getComplexity, simpleEstimator, fieldExtensionsEstimator } from 'graphql-query-complexity';

const complexity = getComplexity({
  schema,
  query: documentAST,
  variables,
  estimators: [
    fieldExtensionsEstimator(),
    simpleEstimator({ defaultComplexity: 1 }),
  ],
});
```

### 9.2 Depth Limiting

Limitare la profondità massima delle query previene query ricorsive che esplodono esponenzialmente.

```typescript
import depthLimit from 'graphql-depth-limit';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  validationRules: [depthLimit(7)],
});
```

Esempio di query pericolosa bloccata dal depth limit:

```graphql
# Profondità 7 — bloccata con limit a 6
query DeeplyNested {
  user(id: "1") {                    # depth 1
    posts {                          # depth 2
      comments {                     # depth 3
        author {                     # depth 4
          posts {                    # depth 5
            comments {               # depth 6
              author {               # depth 7 — BLOCCATA
                name
              }
            }
          }
        }
      }
    }
  }
}
```

### 9.3 Persisted Queries

Le persisted queries sostituiscono il testo completo della query con un hash, riducendo la banda e migliorando la sicurezza.

**Automatic Persisted Queries (APQ):**

```typescript
// Client — Apollo Client
import { createPersistedQueryLink } from '@apollo/client/link/persisted-queries';
import { sha256 } from 'crypto-hash';

const persistedQueryLink = createPersistedQueryLink({ sha256 });

const client = new ApolloClient({
  link: from([persistedQueryLink, httpLink]),
  cache: new InMemoryCache(),
});
```

Flusso APQ:
1. Il client calcola lo SHA256 della query e invia solo l'hash.
2. Se il server ha la query in cache, la esegue.
3. Se no, risponde con `PersistedQueryNotFound`.
4. Il client reinvia la richiesta con hash + testo completo.
5. Il server cacha la query per le richieste future.

**Server-side persisted queries (allowlist):** in produzione, la soluzione più sicura è un allowlist fisso di query conosciute. Qualsiasi query non presente nell'allowlist viene rifiutata.

```typescript
// Generare l'allowlist a build time
const allowedQueries = new Map<string, string>();
// Popolare da file generati dal code generator

const server = new ApolloServer({
  typeDefs,
  resolvers,
  plugins: [{
    async requestDidStart() {
      return {
        async didResolveOperation(ctx) {
          const hash = ctx.request.extensions?.persistedQuery?.sha256Hash;
          if (hash && !allowedQueries.has(hash)) {
            throw new GraphQLError('Query not in allowlist', {
              extensions: { code: 'PERSISTED_QUERY_NOT_FOUND' },
            });
          }
        },
      };
    },
  }],
});
```

### 9.4 Response Caching

```typescript
// Cache a livello di campo con @cacheControl
// maxAge in secondi, scope: PUBLIC o PRIVATE
type Query {
  publicPosts: [Post!]! @cacheControl(maxAge: 300, scope: PUBLIC)
  me: User! @cacheControl(maxAge: 0, scope: PRIVATE)
}

// Cache a livello HTTP con CDN
// Apollo Server imposta l'header Cache-Control basato sulle direttive @cacheControl
```

### 9.5 Query Batching

```typescript
// Client — Apollo Client con batch link
import { BatchHttpLink } from '@apollo/client/link/batch-http';

const batchLink = new BatchHttpLink({
  uri: 'https://api.example.com/graphql',
  batchMax: 10,        // max 10 operazioni per batch
  batchInterval: 20,   // attendi 20ms per accumulare
});
```

Attenzione: il batching lato client aggiunge latenza (il `batchInterval`) a ogni singola query in cambio di ridurre il numero di richieste HTTP. Valutare se il trade-off è vantaggioso per il caso d'uso specifico.

### 9.6 CDN Caching per GraphQL

Il caching a livello CDN è tradizionalmente problematico con GraphQL perché tutte le richieste viaggiano come `POST` verso un singolo endpoint. Le **persisted queries** (sezione 9.3) sbloccano il caching CDN trasformando le richieste in `GET` con un hash deterministico:

```
GET /graphql?extensions={"persistedQuery":{"version":1,"sha256Hash":"abc123..."}}
```

**Configurazione Cache-Control nel resolver:**

```typescript
import { GraphQLResolveInfo } from 'graphql';

const resolvers = {
  Query: {
    products: async (_parent, _args, context, _info) => {
      // Imposta hint di cache nella risposta
      context.res.setHeader('Cache-Control', 'public, max-age=300, s-maxage=600');
      context.res.setHeader('Vary', 'Accept-Encoding, Authorization');
      return context.dataSources.productAPI.getAll();
    },
  },
};
```

**Strategie di edge caching:**

| Soluzione | Approccio | Vantaggi |
|-----------|-----------|----------|
| **Stellate** | Proxy GraphQL-aware davanti al server | Invalidazione granulare per tipo/campo, analytics integrati |
| **Fastly** | VCL/Compute@Edge con parsing della query | Latenza bassissima, rete globale, purge istantaneo |
| **CloudFlare Workers** | Worker che analizza la query e gestisce cache KV | Flessibilità programmatica, Workers KV per APQ map |
| **Grafbase** | Edge runtime nativo GraphQL | Cache automatica per tipo, deploy globale |

**Header `Vary` e best practice:**

Il header `Vary` è cruciale per evitare che risposte personalizzate vengano servite a utenti sbagliati:

```
Vary: Authorization, Accept-Language, Accept-Encoding
```

- **Senza `Authorization` nel `Vary`:** la CDN potrebbe servire dati di un utente autenticato a un visitatore anonimo
- **Senza `Accept-Language`:** risposte localizzate mischiate tra locale diverse
- **Surrogato di cache key:** alcune CDN supportano `Surrogate-Key` per invalidazione selettiva per entity type

**Distinzione cache HTTP vs cache normalizzata client:**

```
┌──────────────┐    ┌──────────┐    ┌──────────────┐    ┌──────────┐
│  Client App  │───▶│ CDN Edge │───▶│ API Gateway  │───▶│  Server  │
│ (norm cache) │    │(HTTP GET)│    │  (APQ map)   │    │(resolver)│
└──────────────┘    └──────────┘    └──────────────┘    └──────────┘
       ▲                  ▲
   cache L1           cache L2
 (per-entity)      (per-response)
```

- **L1 — Normalized cache (Apollo, URQL):** deduplica entità per `__typename:id`, aggiorna automaticamente tutte le view che referenziano la stessa entità
- **L2 — CDN / HTTP cache:** memorizza l'intera risposta JSON; più veloce ma meno granulare, richiede invalidazione esplicita

**Cache-Control scope con `@cacheControl`:**

```graphql
type Product @cacheControl(maxAge: 600, scope: PUBLIC) {
  id: ID!
  name: String!
  price: Float! @cacheControl(maxAge: 60)  # prezzo cambia più spesso
  reviews: [Review!]! @cacheControl(maxAge: 120, scope: PRIVATE)
}
```

Apollo Server calcola automaticamente il `maxAge` complessivo della risposta come il **minimo** tra tutti i campi richiesti. Se `price` ha `maxAge: 60` e `name` ha `maxAge: 600`, la risposta intera ottiene `Cache-Control: max-age=60`.

---

## 10. Paginazione

### 10.1 Cursor-Based Pagination (Relay Spec)

La paginazione cursor-based è il gold standard per GraphQL. Resistente a inserimenti e cancellazioni concorrenti, non ha i problemi di offset shifting.

```graphql
# Connection spec (Relay)
type PostConnection {
  edges: [PostEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type PostEdge {
  node: Post!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

type Query {
  posts(
    first: Int
    after: String
    last: Int
    before: String
    filter: PostFilterInput
  ): PostConnection!
}
```

```typescript
// Implementazione resolver con cursor (Prisma)
async function resolvePosts(
  _parent: unknown,
  args: { first?: number; after?: string; filter?: PostFilter },
  ctx: Context,
): Promise<PostConnection> {
  const take = Math.min(args.first ?? 20, 100); // max 100 per pagina
  const cursor = args.after ? decodeCursor(args.after) : undefined;

  const posts = await ctx.db.post.findMany({
    where: buildWhere(args.filter),
    take: take + 1, // +1 per determinare hasNextPage
    ...(cursor && { cursor: { id: cursor }, skip: 1 }),
    orderBy: { createdAt: 'desc' },
  });

  const hasNextPage = posts.length > take;
  const edges = posts.slice(0, take).map((post) => ({
    node: post,
    cursor: encodeCursor(post.id),
  }));

  return {
    edges,
    pageInfo: {
      hasNextPage,
      hasPreviousPage: !!args.after,
      startCursor: edges[0]?.cursor ?? null,
      endCursor: edges[edges.length - 1]?.cursor ?? null,
    },
    totalCount: await ctx.db.post.count({ where: buildWhere(args.filter) }),
  };
}

function encodeCursor(id: string): string {
  return Buffer.from(`cursor:${id}`).toString('base64url');
}

function decodeCursor(cursor: string): string {
  const decoded = Buffer.from(cursor, 'base64url').toString('utf-8');
  return decoded.replace('cursor:', '');
}
```

### 10.2 Offset-Based Pagination

Più semplice del cursor, adatto per dataset statici dove la navigazione "pagina N" è necessaria.

```graphql
type PaginatedPosts {
  items: [Post!]!
  totalCount: Int!
  page: Int!
  pageSize: Int!
  totalPages: Int!
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
}

type Query {
  paginatedPosts(
    page: Int = 1
    pageSize: Int = 20
    filter: PostFilterInput
  ): PaginatedPosts!
}
```

```typescript
async function resolvePaginatedPosts(
  _parent: unknown,
  args: { page: number; pageSize: number; filter?: PostFilter },
  ctx: Context,
): Promise<PaginatedPosts> {
  const pageSize = Math.min(args.pageSize, 100);
  const skip = (args.page - 1) * pageSize;

  const [items, totalCount] = await Promise.all([
    ctx.db.post.findMany({
      where: buildWhere(args.filter),
      take: pageSize,
      skip,
      orderBy: { createdAt: 'desc' },
    }),
    ctx.db.post.count({ where: buildWhere(args.filter) }),
  ]);

  const totalPages = Math.ceil(totalCount / pageSize);

  return {
    items,
    totalCount,
    page: args.page,
    pageSize,
    totalPages,
    hasNextPage: args.page < totalPages,
    hasPreviousPage: args.page > 1,
  };
}
```

### 10.3 Quando usare quale

| Criterio | Cursor | Offset |
|----------|--------|--------|
| Dataset in continuo aggiornamento | Si | No (offset shifting) |
| Navigazione "vai a pagina N" | No | Si |
| Infinite scroll | Si | Possibile |
| Performance con offset grande | O(1) | O(n) — degrada |
| Complessità implementativa | Media | Bassa |
| Mobile / feed social | Si | No |
| Dashboard admin / tabelle | Possibile | Si |

---

## 11. Subscription e Real-Time

### 11.1 WebSocket Subscriptions

Il meccanismo classico per le subscription GraphQL usa WebSocket con il protocollo `graphql-ws`.

```typescript
// Server — con graphql-ws
import { createServer } from 'http';
import { WebSocketServer } from 'ws';
import { useServer } from 'graphql-ws/lib/use/ws';
import { ApolloServer } from '@apollo/server';
import { ApolloServerPluginDrainHttpServer } from '@apollo/server/plugin/drainHttpServer';

const httpServer = createServer(app);
const wsServer = new WebSocketServer({
  server: httpServer,
  path: '/graphql',
});

const serverCleanup = useServer(
  {
    schema,
    context: async (ctx) => {
      const token = ctx.connectionParams?.authorization as string;
      const user = token ? await verifyToken(token) : null;
      return { user, loaders: createLoaders() };
    },
    onConnect: async (ctx) => {
      const token = ctx.connectionParams?.authorization as string;
      if (!token || !(await verifyToken(token))) {
        return false; // Rifiuta la connessione
      }
    },
    onDisconnect: (_ctx, code, reason) => {
      console.log(`Client disconnected: ${code} ${reason}`);
    },
  },
  wsServer,
);

const server = new ApolloServer({
  schema,
  plugins: [
    ApolloServerPluginDrainHttpServer({ httpServer }),
    {
      async serverWillStart() {
        return {
          async drainServer() {
            await serverCleanup.dispose();
          },
        };
      },
    },
  ],
});
```

### 11.2 PubSub per Subscription

```typescript
import { PubSub } from 'graphql-subscriptions';

// In produzione usare Redis PubSub, non in-memory
// import { RedisPubSub } from 'graphql-redis-subscriptions';
const pubsub = new PubSub();

const EVENTS = {
  POST_PUBLISHED: 'POST_PUBLISHED',
  COMMENT_ADDED: 'COMMENT_ADDED',
  USER_STATUS_CHANGED: 'USER_STATUS_CHANGED',
} as const;

const resolvers = {
  Mutation: {
    publishPost: async (_parent, { id }, ctx) => {
      const post = await ctx.dataSources.posts.publish(id);
      pubsub.publish(EVENTS.POST_PUBLISHED, { postPublished: post });
      return { post, errors: [] };
    },
    addComment: async (_parent, { input }, ctx) => {
      const comment = await ctx.dataSources.comments.create(input);
      pubsub.publish(EVENTS.COMMENT_ADDED, {
        commentAdded: comment,
        postId: input.postId,
      });
      return { comment, errors: [] };
    },
  },
  Subscription: {
    postPublished: {
      subscribe: () => pubsub.asyncIterableIterator([EVENTS.POST_PUBLISHED]),
    },
    commentAdded: {
      subscribe: withFilter(
        () => pubsub.asyncIterableIterator([EVENTS.COMMENT_ADDED]),
        (payload, variables) => payload.postId === variables.postId,
      ),
    },
  },
};
```

### 11.3 SSE come Alternativa

Server-Sent Events sono unidirezionali (server → client) e funzionano su HTTP standard. Più semplici di WebSocket, supportati nativamente da GraphQL Yoga.

```typescript
// GraphQL Yoga supporta SSE out-of-the-box
// Il client si connette con EventSource o fetch streaming
const yoga = createYoga({
  schema,
  // Le subscription usano SSE per default in Yoga
});
```

### 11.4 Subscription vs Polling vs SSE

| Aspetto | WebSocket Sub | SSE | Polling |
|---------|--------------|-----|---------|
| Direzione | Bidirezionale | Server → Client | Client → Server |
| Protocollo | WS (upgrade HTTP) | HTTP standard | HTTP standard |
| Latenza | ~0ms (push) | ~0ms (push) | Intervallo polling |
| Proxy/CDN friendly | No (spesso) | Si | Si |
| Complessità server | Alta | Media | Bassa |
| Scalabilità | PubSub necessario | Facile | Facile ma costoso |
| Caso ideale | Chat, gaming, collab | Notifiche, feed | Dashboard, dati lenti |

---

## 12. Apollo Federation

Apollo Federation permette di comporre un singolo grafo GraphQL (supergraph) da più servizi indipendenti (subgraph).

### 12.1 Architettura

```
Client → Gateway/Router → Subgraph A (Users)
                        → Subgraph B (Posts)
                        → Subgraph C (Comments)
```

Il **Router** (Apollo Router, scritto in Rust) riceve le query dal client, pianifica l'esecuzione distribuita tra i subgraph, aggrega i risultati e restituisce la risposta unificata.

### 12.2 Subgraph Definition

```graphql
# Subgraph Users
extend schema @link(url: "https://specs.apollo.dev/federation/v2.5",
  import: ["@key", "@shareable", "@external"])

type User @key(fields: "id") {
  id: ID!
  name: String!
  email: String!
  role: UserRole!
}

type Query {
  user(id: ID!): User
  me: User
}
```

```graphql
# Subgraph Posts — estende User definito in Users subgraph
extend schema @link(url: "https://specs.apollo.dev/federation/v2.5",
  import: ["@key", "@external", "@requires"])

type User @key(fields: "id") {
  id: ID!
  posts: [Post!]!
  postsCount: Int!
}

type Post @key(fields: "id") {
  id: ID!
  title: String!
  content: String!
  author: User!
  publishedAt: DateTime
}

type Query {
  post(id: ID!): Post
  posts(first: Int, after: String): PostConnection!
}
```

### 12.3 Reference Resolvers

Ogni subgraph deve implementare un `__resolveReference` per i tipi che estende:

```typescript
// Subgraph Posts — resolver per User
const resolvers = {
  User: {
    __resolveReference: async (reference, ctx) => {
      // reference.id arriva dal subgraph Users
      return ctx.loaders.userPosts.load(reference.id);
    },
    posts: async (user, _args, ctx) => {
      return ctx.dataSources.posts.findByAuthor(user.id);
    },
    postsCount: async (user, _args, ctx) => {
      return ctx.dataSources.posts.countByAuthor(user.id);
    },
  },
};
```

### 12.4 Supergraph Composition

```yaml
# supergraph-config.yaml
federation_version: =2.5
subgraphs:
  users:
    routing_url: http://users-service:4001/graphql
    schema:
      subgraph_url: http://users-service:4001/graphql
  posts:
    routing_url: http://posts-service:4002/graphql
    schema:
      subgraph_url: http://posts-service:4002/graphql
  comments:
    routing_url: http://comments-service:4003/graphql
    schema:
      subgraph_url: http://comments-service:4003/graphql
```

```bash
# Composizione con rover CLI
rover supergraph compose --config ./supergraph-config.yaml > supergraph.graphql

# Avvio Apollo Router
APOLLO_ROUTER_SUPERGRAPH_PATH=./supergraph.graphql ./router
```

### 12.5 Federation v2 — Directive Avanzate

Federation v2 introduce un insieme di directive che vanno ben oltre `@key` e `@external`, permettendo un controllo granulare su ownership, migrazione e composizione dei campi tra subgraph.

**`@shareable`** — dichiara che un campo può essere risolto da più subgraph. Senza `@shareable`, un campo definito in più subgraph causa un errore di composizione.

```graphql
# Subgraph Users
type User @key(fields: "id") {
  id: ID!
  name: String! @shareable
  email: String!
}

# Subgraph Reviews — può risolvere User.name autonomamente
type User @key(fields: "id") {
  id: ID!
  name: String! @shareable
}
```

**`@provides`** — indica che un subgraph può fornire un campo normalmente risolto da un altro subgraph, evitando una chiamata di rete aggiuntiva al subgraph proprietario.

```graphql
# Subgraph Reviews — quando il client richiede review.author.name,
# il subgraph Reviews può risolvere name localmente senza chiamare Users
type Review @key(fields: "id") {
  id: ID!
  body: String!
  author: User! @provides(fields: "name")
}

type User @key(fields: "id") {
  id: ID! @external
  name: String! @external
}
```

Il resolver corrispondente nel subgraph Reviews deve effettivamente restituire il campo `name` quando risolve `author`:

```typescript
const resolvers = {
  Review: {
    author: (review) => ({
      __typename: 'User',
      id: review.authorId,
      name: review.authorName, // disponibile localmente nel DB del subgraph Reviews
    }),
  },
};
```

**`@requires`** — indica che un campo dipende da campi esterni. Il Router recupera i campi richiesti dal subgraph proprietario prima di invocare il resolver del campo dipendente.

```graphql
# Subgraph Shipping — calcola il costo di spedizione basandosi su peso e dimensioni
# che sono proprietà del subgraph Products
type Product @key(fields: "id") {
  id: ID! @external
  weight: Float @external
  dimensions: String @external
  shippingCost: Float @requires(fields: "weight dimensions")
}
```

Il Router esegue un query plan in due fasi: prima recupera `weight` e `dimensions` dal subgraph Products, poi li passa come campi del `parent` al resolver `shippingCost` nel subgraph Shipping.

**`@override`** — migra la ownership di un campo da un subgraph a un altro. Essenziale per migrazioni incrementali senza downtime.

```graphql
# Subgraph Users (originale) — definisce User.email
type User @key(fields: "id") {
  id: ID!
  name: String!
  email: String!
}

# Subgraph Accounts (nuovo) — prende ownership di email
type User @key(fields: "id") {
  id: ID!
  email: String! @override(from: "users")
}
```

Dalla Federation v2.7 in poi, `@override` supporta la **migrazione progressiva** con il parametro `label`, che permette di instradare una percentuale di traffico al nuovo subgraph:

```graphql
type User @key(fields: "id") {
  id: ID!
  email: String! @override(from: "users", label: "percent(25)")
}
```

In questo esempio, il 25% delle richieste per `User.email` viene instradato al subgraph Accounts, il restante 75% continua a essere risolto dal subgraph Users. La percentuale può essere incrementata gradualmente fino al 100%.

**`@interfaceObject`** — introdotta in Federation v2.3. Permette a un subgraph di estendere un'interfaccia del supergraph senza conoscere tutti i tipi che la implementano.

```graphql
# Subgraph Media — definisce l'interfaccia
interface Media @key(fields: "id") {
  id: ID!
  title: String!
  url: String!
}

type Image implements Media @key(fields: "id") {
  id: ID!
  title: String!
  url: String!
  width: Int!
  height: Int!
}

type Video implements Media @key(fields: "id") {
  id: ID!
  title: String!
  url: String!
  duration: Int!
}

# Subgraph Analytics — aggiunge viewCount all'interfaccia
# senza dover conoscere Image, Video, etc.
type Media @key(fields: "id") @interfaceObject {
  id: ID!
  viewCount: Int!
}
```

Il subgraph Analytics non deve implementare `Image` e `Video` separatamente — `@interfaceObject` istruisce il Router che questo tipo è un'interfaccia nel supergraph, e il campo `viewCount` viene reso disponibile su tutti i tipi che la implementano.

**`@context` e `@fromContext`** — introdotte in Federation v2.8. Permettono di passare valori di contesto tra subgraph attraverso il query plan, senza esporre questi valori come campi dello schema.

```graphql
# Subgraph Tenants — definisce un contesto "tenantInfo"
extend schema
  @link(url: "https://specs.apollo.dev/federation/v2.8", import: ["@key", "@context"])
  @context(name: "tenantInfo")

type Tenant @key(fields: "id") {
  id: ID!
  region: String!
}

# Subgraph Products — usa il contesto per filtrare i prodotti per regione
extend schema
  @link(url: "https://specs.apollo.dev/federation/v2.8", import: ["@key", "@fromContext"])

type Product @key(fields: "id") {
  id: ID!
  name: String!
  price(region: String! @fromContext(field: "$tenantInfo { region }")): Float!
}
```

### 12.6 Query Planning e Performance del Router

Il Router (Apollo Router, Cosmo Router, Hive Gateway) è il componente che trasforma una query client in un **query plan** — una sequenza ottimizzata di fetch paralleli e sequenziali ai subgraph coinvolti.

**Esempio di query plan:**

```
QueryPlan {
  Sequence {
    Fetch(service: "users") {
      { user(id: "42") { id name email } }
    }
    Parallel {
      Fetch(service: "posts") {
        { ... on User { posts { id title } } }
      }
      Fetch(service: "reviews") {
        { ... on User { reviews { id rating } } }
      }
    }
  }
}
```

Il Router determina automaticamente quali fetch possono essere parallelizzati e quali devono essere sequenziali (quando un subgraph dipende da dati prodotti da un altro).

**Entity caching al livello del Router** — il Router può cachare le risposte delle entity resolution, evitando chiamate ripetute ai subgraph per le stesse entità:

```yaml
# router.yaml — configurazione entity caching
supergraph:
  path: ./supergraph.graphql
  listen: 0.0.0.0:4000

preview_entity_cache:
  enabled: true
  redis:
    urls: ["redis://localhost:6379"]
  subgraph:
    all:
      enabled: true
      ttl: 60s
    subgraphs:
      users:
        ttl: 300s  # utenti cambiano raramente
      posts:
        ttl: 30s   # post cambiano più frequentemente
```

**Metriche del query plan** — monitorare il numero di fetch per query, la latenza per subgraph e il tasso di cache hit è fondamentale per identificare query plan inefficienti. Un query plan con più di 5-6 fetch sequenziali è un segnale che lo schema potrebbe beneficiare di `@provides` per ridurre i round-trip.

---

## 13. Code Generation

### 13.1 GraphQL Code Generator

GraphQL Code Generator genera tipi TypeScript, hook React, documenti tipizzati e SDK partendo dallo schema e dalle operazioni.

```yaml
# codegen.ts
import type { CodegenConfig } from '@graphql-codegen/cli';

const config: CodegenConfig = {
  schema: 'http://localhost:4000/graphql',
  documents: ['src/**/*.graphql', 'src/**/*.tsx'],
  generates: {
    'src/generated/graphql.ts': {
      plugins: [
        'typescript',
        'typescript-operations',
        'typescript-react-apollo',
      ],
      config: {
        strictScalars: true,
        scalars: {
          DateTime: 'string',
          EmailAddress: 'string',
          URL: 'string',
          JSON: 'Record<string, unknown>',
        },
        withHooks: true,
        withComponent: false,
        enumsAsTypes: true,
      },
    },
    'src/generated/schema.graphql': {
      plugins: ['schema-ast'],
    },
  },
  hooks: {
    afterAllFileWrite: ['prettier --write'],
  },
};

export default config;
```

```bash
# Esecuzione
npx graphql-codegen --config codegen.ts

# Watch mode durante lo sviluppo
npx graphql-codegen --config codegen.ts --watch
```

### 13.2 Uso dei Tipi Generati

```tsx
// Prima (senza codegen) — tipi manuali, error-prone
const GET_USER = gql`query GetUser($id: ID!) { user(id: $id) { id name } }`;
const { data } = useQuery(GET_USER, { variables: { id: '42' } });
// data è any — nessuna type safety

// Dopo (con codegen) — tutto tipizzato
import { useGetUserQuery } from './generated/graphql';

function UserProfile({ userId }: { userId: string }) {
  const { data, loading, error } = useGetUserQuery({
    variables: { id: userId },
  });

  // data.user è tipizzato come { id: string; name: string; ... }
  // variables è tipizzato — errori di tipo a compile time
  return <h1>{data?.user?.name}</h1>;
}
```

### 13.3 Server-Side Codegen (per Resolver)

```yaml
# codegen per resolver types
generates:
  src/generated/resolvers-types.ts:
    plugins:
      - typescript
      - typescript-resolvers
    config:
      contextType: '../context#GraphQLContext'
      mappers:
        User: '../models#UserModel'
        Post: '../models#PostModel'
      useIndexSignature: true
```

Risultato: i resolver sono tipizzati end-to-end — argomenti, context, return type.

---

## 14. Testing

### 14.1 Schema Testing

Validare che lo schema sia corretto e non introduca breaking changes.

```typescript
import { buildSchema, validateSchema } from 'graphql';
import { readFileSync } from 'fs';

describe('GraphQL Schema', () => {
  it('should be valid', () => {
    const sdl = readFileSync('./schema.graphql', 'utf-8');
    const schema = buildSchema(sdl);
    const errors = validateSchema(schema);
    expect(errors).toHaveLength(0);
  });

  it('should not have breaking changes from previous version', () => {
    const oldSchema = buildSchema(readFileSync('./schema.prev.graphql', 'utf-8'));
    const newSchema = buildSchema(readFileSync('./schema.graphql', 'utf-8'));

    const breakingChanges = findBreakingChanges(oldSchema, newSchema);
    expect(breakingChanges).toHaveLength(0);
  });
});
```

### 14.2 Resolver Unit Testing

```typescript
import { createMockContext } from './test-utils';

describe('User resolvers', () => {
  it('should return user by ID', async () => {
    const mockUser = { id: '1', name: 'Marco', email: 'marco@example.com' };
    const ctx = createMockContext({
      dataSources: {
        users: { findById: vi.fn().mockResolvedValue(mockUser) },
      },
    });

    const result = await resolvers.Query.user(null, { id: '1' }, ctx, {} as any);

    expect(result).toEqual(mockUser);
    expect(ctx.dataSources.users.findById).toHaveBeenCalledWith('1');
  });

  it('should throw NotFoundError for non-existent user', async () => {
    const ctx = createMockContext({
      dataSources: {
        users: { findById: vi.fn().mockResolvedValue(null) },
      },
      user: { id: '1', role: 'VIEWER' },
    });

    await expect(
      resolvers.Query.user(null, { id: '999' }, ctx, {} as any),
    ).rejects.toThrow(NotFoundError);
  });

  it('should throw AuthenticationError when not authenticated', async () => {
    const ctx = createMockContext({ user: null });

    await expect(
      resolvers.Query.user(null, { id: '1' }, ctx, {} as any),
    ).rejects.toThrow(AuthenticationError);
  });
});
```

### 14.3 Integration Testing con Apollo Server

```typescript
import { ApolloServer } from '@apollo/server';
import assert from 'assert';

describe('GraphQL API Integration', () => {
  let server: ApolloServer;

  beforeAll(() => {
    server = new ApolloServer({ typeDefs, resolvers });
  });

  it('should execute a query successfully', async () => {
    const response = await server.executeOperation(
      {
        query: `
          query GetUser($id: ID!) {
            user(id: $id) {
              id
              name
              email
            }
          }
        `,
        variables: { id: '1' },
      },
      {
        contextValue: createTestContext({ user: testAdmin }),
      },
    );

    assert(response.body.kind === 'single');
    expect(response.body.singleResult.errors).toBeUndefined();
    expect(response.body.singleResult.data?.user).toEqual({
      id: '1',
      name: 'Marco Rossi',
      email: 'marco@example.com',
    });
  });

  it('should handle mutation with validation errors', async () => {
    const response = await server.executeOperation(
      {
        query: `
          mutation CreateUser($input: CreateUserInput!) {
            createUser(input: $input) {
              user { id }
              errors { field message code }
            }
          }
        `,
        variables: {
          input: { username: '', email: 'invalid-email' },
        },
      },
      {
        contextValue: createTestContext({ user: testAdmin }),
      },
    );

    assert(response.body.kind === 'single');
    const { data } = response.body.singleResult;
    expect(data?.createUser.user).toBeNull();
    expect(data?.createUser.errors).toHaveLength(2);
  });
});
```

### 14.4 Mocking per Testing

```typescript
import { addMocksToSchema } from '@graphql-tools/mock';
import { makeExecutableSchema } from '@graphql-tools/schema';

const schema = makeExecutableSchema({ typeDefs });

const mockedSchema = addMocksToSchema({
  schema,
  mocks: {
    DateTime: () => new Date().toISOString(),
    EmailAddress: () => 'test@example.com',
    URL: () => 'https://example.com',
    User: () => ({
      id: () => crypto.randomUUID(),
      name: () => 'Mock User',
      role: () => 'VIEWER',
    }),
  },
});
```

---

## 15. GraphQL vs REST

### 15.1 Matrice Comparativa

| Aspetto | REST | GraphQL |
|---------|------|---------|
| Endpoint | Multipli (`/users`, `/posts`) | Singolo (`/graphql`) |
| Over-fetching | Comune | Eliminato by design |
| Under-fetching | Comune (richiede N richieste) | Eliminato (query unica) |
| Versionamento | URL (`/v1/`, `/v2/`) o header | Evoluzione schema (deprecation) |
| Caching HTTP | Nativo (GET + Cache-Control) | Complesso (POST unico) |
| Tipizzazione | Opzionale (OpenAPI) | Obbligatoria (schema) |
| File upload | Nativo (multipart) | Richiede spec aggiuntiva |
| Real-time | SSE, WebSocket (separato) | Subscription (integrato) |
| Curva apprendimento | Bassa | Media |
| Tooling maturo | Molto maturo | In crescita |
| Codici di stato HTTP | Semantici (200, 404, 500) | Sempre 200 (errori nel body) |
| Documentazione | Swagger/OpenAPI | Schema introspection |
| Mobile performance | Peggiore (over-fetching) | Migliore (query precise) |

### 15.2 Quando Scegliere Cosa

**Scegliere REST quando:**
- API pubblica con consumer eterogenei
- Caching HTTP è essenziale (CDN, browser cache)
- L'API è prevalentemente CRUD semplice
- Il team non ha esperienza GraphQL
- Le risorse sono ben definite e stabili

**Scegliere GraphQL quando:**
- Client diversi necessitano dati diversi (mobile vs web vs partner)
- Il dominio ha relazioni complesse e nested
- Ridurre le richieste di rete è prioritario (mobile, high latency)
- Il frontend evolve rapidamente (nuove view, nuovi dati)
- Serve real-time tramite subscription
- Type safety end-to-end è desiderata

### 15.3 BFF Pattern (Backend for Frontend)

Il BFF combina REST e GraphQL: un layer GraphQL davanti a servizi REST esistenti.

```
Mobile App → GraphQL BFF (mobile) → REST Services
Web App    → GraphQL BFF (web)    → REST Services
Partner    → REST API pubblica    → REST Services
```

```typescript
// BFF resolver che aggrega REST services
const resolvers = {
  Query: {
    dashboard: async (_parent, _args, ctx) => {
      const [user, orders, notifications] = await Promise.all([
        fetch(`${USER_SERVICE}/users/${ctx.user.id}`).then((r) => r.json()),
        fetch(`${ORDER_SERVICE}/users/${ctx.user.id}/orders?limit=5`).then((r) => r.json()),
        fetch(`${NOTIFICATION_SERVICE}/users/${ctx.user.id}/notifications?unread=true`).then((r) => r.json()),
      ]);

      return { user, recentOrders: orders, unreadNotifications: notifications };
    },
  },
};
```

### 15.4 Migrazione REST → GraphQL

Strategia incrementale:

1. **Layer di wrapper:** creare resolver GraphQL che chiamano gli endpoint REST esistenti.
2. **Coesistenza:** REST e GraphQL servono contemporaneamente. I nuovi client usano GraphQL, i vecchi restano su REST.
3. **Migrazione graduale:** spostare la logica dai controller REST ai resolver GraphQL.
4. **Deprecazione REST:** quando tutti i client sono migrati, deprecare gli endpoint REST.

```typescript
// Fase 1: GraphQL wrapper su REST
const resolvers = {
  Query: {
    user: async (_parent, { id }) => {
      const response = await fetch(`${REST_API}/users/${id}`);
      if (!response.ok) throw new NotFoundError('User', id);
      return response.json();
    },
  },
};
```

---

## 16. Sicurezza

### 16.1 Query Allowlisting

In produzione, accettare solo query conosciute e pre-approvate.

```typescript
// Middleware allowlist
function queryAllowlistPlugin(allowedHashes: Set<string>): ApolloServerPlugin {
  return {
    async requestDidStart() {
      return {
        async didResolveOperation(ctx) {
          if (process.env.NODE_ENV !== 'production') return;

          const hash = createHash('sha256')
            .update(ctx.request.query ?? '')
            .digest('hex');

          if (!allowedHashes.has(hash)) {
            throw new GraphQLError('Query not allowed', {
              extensions: { code: 'QUERY_NOT_ALLOWED' },
            });
          }
        },
      };
    },
  };
}
```

### 16.2 Disabilitare Introspection in Produzione

L'introspezione espone l'intero schema a chiunque. In produzione, deve essere disabilitata.

```typescript
const server = new ApolloServer({
  typeDefs,
  resolvers,
  introspection: process.env.NODE_ENV !== 'production',
});
```

Se si usa Yoga:

```typescript
import { useDisableIntrospection } from '@graphql-yoga/plugin-disable-introspection';

const yoga = createYoga({
  plugins: [
    process.env.NODE_ENV === 'production'
      ? useDisableIntrospection()
      : undefined,
  ].filter(Boolean),
});
```

### 16.3 Rate Limiting per Query

```typescript
import { GraphQLError } from 'graphql';

const rateLimitMap = new Map<string, { count: number; resetAt: number }>();

function rateLimitPlugin(maxRequests: number, windowMs: number): ApolloServerPlugin {
  return {
    async requestDidStart(ctx) {
      return {
        async didResolveOperation() {
          const key = ctx.contextValue.user?.id ?? ctx.contextValue.ip;
          const now = Date.now();
          const entry = rateLimitMap.get(key);

          if (!entry || entry.resetAt < now) {
            rateLimitMap.set(key, { count: 1, resetAt: now + windowMs });
            return;
          }

          entry.count++;
          if (entry.count > maxRequests) {
            throw new GraphQLError('Rate limit exceeded', {
              extensions: {
                code: 'RATE_LIMITED',
                retryAfter: Math.ceil((entry.resetAt - now) / 1000),
              },
            });
          }
        },
      };
    },
  };
}

// In produzione usare Redis per il rate limiting distribuito
```

### 16.4 Injection Prevention

GraphQL è resistente alla SQL injection per design se si usano variabili (mai interpolazione di stringhe). Tuttavia, bisogna proteggere i resolver:

```typescript
// SBAGLIATO — interpolazione di stringhe → SQL injection
const resolvers = {
  Query: {
    search: async (_parent, { query }) => {
      // PERICOLOSO: query iniettata direttamente
      return db.raw(`SELECT * FROM posts WHERE title LIKE '%${query}%'`);
    },
  },
};

// CORRETTO — query parametrizzata
const resolvers = {
  Query: {
    search: async (_parent, { query }, ctx) => {
      return ctx.db.post.findMany({
        where: { title: { contains: query, mode: 'insensitive' } },
      });
    },
  },
};
```

### 16.5 Field Suggestions Disabling

Di default, GraphQL suggerisce campi simili a quelli sbagliati. In produzione, questo rivela la struttura dello schema.

```typescript
// Disabilitare i suggerimenti di campo
const server = new ApolloServer({
  typeDefs,
  resolvers,
  includeStacktraceInErrorResponses: false,
  formatError: (formattedError) => {
    // Rimuovere suggerimenti in produzione
    if (process.env.NODE_ENV === 'production') {
      const { message } = formattedError;
      if (message.includes('Did you mean')) {
        return { ...formattedError, message: 'Invalid field' };
      }
    }
    return formattedError;
  },
});
```

### 16.6 Checklist Sicurezza

- [ ] Introspection disabilitata in produzione
- [ ] Depth limit configurato (max 7-10)
- [ ] Query complexity limit configurato
- [ ] Rate limiting attivo
- [ ] Persisted queries / allowlist in produzione
- [ ] Field suggestions disabilitate in produzione
- [ ] Stack trace rimosse dalle risposte di errore
- [ ] Input validation sui resolver
- [ ] Query parametrizzate (no string interpolation)
- [ ] CORS configurato restrittivamente
- [ ] Timeout sulle richieste
- [ ] Max request body size configurato

### 16.7 Batching Attacks e Resource Exhaustion

Oltre alla complessità e profondità delle query, esistono vettori d'attacco specifici che sfruttano il **batching** e gli **alias** per aggirare i limiti di rate limiting tradizionali.

**Array Batching Attack:**

Il protocollo GraphQL consente di inviare un array di operazioni in un singolo request HTTP:

```json
[
  { "query": "mutation { login(user: \"admin\", pass: \"pass1\") { token } }" },
  { "query": "mutation { login(user: \"admin\", pass: \"pass2\") { token } }" },
  { "query": "mutation { login(user: \"admin\", pass: \"pass3\") { token } }" }
]
```

Un attaccante può inviare migliaia di tentativi di brute-force in una singola richiesta HTTP, aggirando il rate limiter che conta le richieste HTTP anziché le operazioni GraphQL.

**Mitigazione — limitare la dimensione del batch:**

```typescript
import { ApolloServer } from '@apollo/server';

const server = new ApolloServer({
  typeDefs,
  resolvers,
  allowBatchedHttpRequests: true,  // false per disabilitare completamente
  // Plugin per limitare batch size
  plugins: [
    {
      async requestDidStart() {
        return {
          async didResolveOperation(requestContext) {
            // Rate limit per operazione, non per HTTP request
            await perOperationRateLimiter.consume(
              requestContext.contextValue.clientIp
            );
          },
        };
      },
    },
  ],
});
```

**Alias-Based Field Duplication Attack:**

Un singolo documento GraphQL può duplicare lo stesso campo costoso usando alias:

```graphql
query AliasAttack {
  a1: expensiveField(input: "x1")
  a2: expensiveField(input: "x2")
  a3: expensiveField(input: "x3")
  # ... ripetuto centinaia di volte
  a500: expensiveField(input: "x500")
}
```

Questo bypassa i limiti di profondità (la query è piatta) e può aggirare l'analisi di complessità se il costo per campo è basso ma il campo è I/O-intensive.

**Mitigazione — conteggio alias e costo aggregato:**

```typescript
import { createComplexityPlugin } from 'graphql-query-complexity';

const complexityPlugin = createComplexityPlugin({
  estimators: [
    // Ogni alias conta come invocazione separata
    fieldExtensionsEstimator(),
    simpleEstimator({ defaultComplexity: 1 }),
  ],
  maximumComplexity: 1000,
  onComplete: (complexity: number) => {
    console.log(`Query complexity: ${complexity}`);
  },
});
```

**Resource Exhaustion via Subscription Flooding:**

```graphql
# Un client apre centinaia di subscription simultanee
subscription S1 { orderUpdated(storeId: "1") { id status } }
subscription S2 { orderUpdated(storeId: "2") { id status } }
# ...
```

**Mitigazione:**

```typescript
const wsServer = new WebSocketServer({ server: httpServer });

useServer(
  {
    schema,
    context: async (ctx) => {
      const subscriptionCount = activeSubscriptions.get(ctx.connectionParams?.clientId) || 0;
      if (subscriptionCount >= MAX_SUBSCRIPTIONS_PER_CLIENT) {
        throw new Error('Subscription limit exceeded');
      }
      return { clientId: ctx.connectionParams?.clientId };
    },
    onSubscribe: (_ctx, msg) => {
      // Validazione complessità anche per subscription
      const complexity = calculateComplexity(msg.payload.query);
      if (complexity > MAX_SUBSCRIPTION_COMPLEXITY) {
        return [new GraphQLError('Subscription too complex')];
      }
    },
  },
  wsServer
);
```

**Checklist difesa batching:**

- [ ] Batch HTTP disabilitato o limitato a N operazioni (es. 5-10)
- [ ] Rate limiting per operazione GraphQL, non per richiesta HTTP
- [ ] Conteggio alias incluso nel calcolo di complessità
- [ ] Limite massimo di subscription per connessione WebSocket
- [ ] Timeout per subscription inattive
- [ ] Monitoraggio del rapporto operazioni/richiesta per rilevare anomalie

---

## 17. Gestione File

### 17.1 Multipart Upload (graphql-upload)

La specifica GraphQL Multipart Request permette l'upload diretto di file via GraphQL.

```graphql
scalar Upload

type Mutation {
  uploadAvatar(file: Upload!): UploadPayload!
  uploadAttachments(files: [Upload!]!): UploadPayload!
}

type UploadPayload {
  url: String
  errors: [MutationError!]!
}
```

```typescript
// Server — con graphql-upload (GraphQL Yoga lo supporta nativamente)
import { processRequest } from 'graphql-upload-ts';

const resolvers = {
  Mutation: {
    uploadAvatar: async (_parent, { file }, ctx) => {
      const { createReadStream, filename, mimetype } = await file;

      // Validazione
      const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
      if (!allowedTypes.includes(mimetype)) {
        return {
          url: null,
          errors: [{ field: 'file', message: 'Tipo non supportato', code: 'INVALID_FILE_TYPE' }],
        };
      }

      const stream = createReadStream();
      const key = `avatars/${ctx.user.id}/${Date.now()}-${filename}`;
      const url = await uploadToS3(stream, key, mimetype);

      return { url, errors: [] };
    },
  },
};
```

### 17.2 Presigned URL Pattern (Consigliato)

Per file grandi, il pattern presigned URL è superiore: il client carica direttamente allo storage (S3, GCS) senza passare per il server GraphQL.

```graphql
type Mutation {
  generateUploadUrl(
    filename: String!
    contentType: String!
    contentLength: Int!
  ): PresignedUploadPayload!

  completeUpload(
    key: String!
    filename: String!
  ): CompleteUploadPayload!
}

type PresignedUploadPayload {
  uploadUrl: String!
  key: String!
  errors: [MutationError!]!
}
```

```typescript
const resolvers = {
  Mutation: {
    generateUploadUrl: async (_parent, { filename, contentType, contentLength }, ctx) => {
      if (!ctx.user) throw new AuthenticationError();

      // Validazione lato server
      const maxSize = 10 * 1024 * 1024; // 10MB
      if (contentLength > maxSize) {
        return {
          uploadUrl: '',
          key: '',
          errors: [{ message: 'File troppo grande (max 10MB)', code: 'FILE_TOO_LARGE' }],
        };
      }

      const key = `uploads/${ctx.user.id}/${crypto.randomUUID()}-${filename}`;
      const uploadUrl = await s3.getSignedUrl('putObject', {
        Bucket: BUCKET,
        Key: key,
        ContentType: contentType,
        ContentLength: contentLength,
        Expires: 300, // 5 minuti
      });

      return { uploadUrl, key, errors: [] };
    },

    completeUpload: async (_parent, { key, filename }, ctx) => {
      // Verificare che il file esista in S3
      // Creare il record nel database
      const file = await ctx.db.file.create({
        data: { key, filename, userId: ctx.user.id },
      });
      return { file, errors: [] };
    },
  },
};
```

Flusso:
1. Client chiama `generateUploadUrl` → riceve presigned URL.
2. Client carica il file direttamente a S3 via PUT.
3. Client chiama `completeUpload` per confermare.

Vantaggi: il server GraphQL non gestisce lo stream binario, nessun limite di body size sul server GraphQL, upload paralleli, resume possibile.

---

## 18. Error Handling

### 18.1 Struttura degli Errori GraphQL

La specifica GraphQL definisce un formato standard per gli errori:

```json
{
  "data": null,
  "errors": [
    {
      "message": "User not found",
      "locations": [{ "line": 2, "column": 3 }],
      "path": ["user"],
      "extensions": {
        "code": "NOT_FOUND",
        "entity": "User",
        "id": "999"
      }
    }
  ]
}
```

### 18.2 Risultati Parziali

GraphQL supporta risultati parziali — alcuni campi possono risolversi anche se altri falliscono.

```json
{
  "data": {
    "user": {
      "id": "1",
      "name": "Marco",
      "posts": null
    }
  },
  "errors": [
    {
      "message": "Posts service temporarily unavailable",
      "path": ["user", "posts"],
      "extensions": { "code": "SERVICE_UNAVAILABLE" }
    }
  ]
}
```

I campi nullable possono fallire senza invalidare l'intera risposta. I campi non-null propagano l'errore al campo padre più vicino che sia nullable.

### 18.3 Error Codes Standardizzati

```typescript
enum ErrorCode {
  // Autenticazione / Autorizzazione
  UNAUTHENTICATED = 'UNAUTHENTICATED',
  FORBIDDEN = 'FORBIDDEN',
  TOKEN_EXPIRED = 'TOKEN_EXPIRED',

  // Validazione
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  INVALID_INPUT = 'INVALID_INPUT',

  // Risorse
  NOT_FOUND = 'NOT_FOUND',
  ALREADY_EXISTS = 'ALREADY_EXISTS',
  CONFLICT = 'CONFLICT',

  // Limiti
  RATE_LIMITED = 'RATE_LIMITED',
  QUERY_TOO_COMPLEX = 'QUERY_TOO_COMPLEX',
  QUERY_TOO_DEEP = 'QUERY_TOO_DEEP',

  // Server
  INTERNAL_ERROR = 'INTERNAL_ERROR',
  SERVICE_UNAVAILABLE = 'SERVICE_UNAVAILABLE',
  UPSTREAM_ERROR = 'UPSTREAM_ERROR',
}
```

### 18.4 Error Formatting

```typescript
const server = new ApolloServer({
  typeDefs,
  resolvers,
  formatError: (formattedError, error) => {
    // Log errore completo server-side
    console.error({
      message: formattedError.message,
      code: formattedError.extensions?.code,
      path: formattedError.path,
      stack: error instanceof Error ? error.stack : undefined,
    });

    // In produzione, mascherare errori interni
    if (process.env.NODE_ENV === 'production') {
      if (formattedError.extensions?.code === 'INTERNAL_SERVER_ERROR') {
        return {
          message: 'An internal error occurred',
          extensions: { code: 'INTERNAL_ERROR' },
        };
      }
      // Rimuovere stack trace
      const { extensions, ...rest } = formattedError;
      const { stacktrace, ...safeExtensions } = extensions ?? {};
      return { ...rest, extensions: safeExtensions };
    }

    return formattedError;
  },
});
```

### 18.5 Union Error Pattern

Un approccio alternativo è modellare gli errori nello schema con union types:

```graphql
type User {
  id: ID!
  name: String!
}

type NotFoundError {
  message: String!
  entityType: String!
  id: ID!
}

type ValidationErrors {
  errors: [FieldError!]!
}

type FieldError {
  field: String!
  message: String!
}

union UserResult = User | NotFoundError | ValidationErrors

type Query {
  user(id: ID!): UserResult!
}
```

```graphql
query GetUser {
  user(id: "999") {
    ... on User {
      id
      name
    }
    ... on NotFoundError {
      message
      entityType
    }
    ... on ValidationErrors {
      errors {
        field
        message
      }
    }
  }
}
```

Vantaggi: errori tipizzati nello schema, il client sa esattamente quali errori aspettarsi, code generation produce discriminated unions.

---

## 19. Tooling

### 19.1 GraphiQL

IDE integrato per esplorare e testare query GraphQL, fornito da molti server (Apollo, Yoga, Mercurius).

Funzionalità chiave:
- Autocompletamento basato sullo schema
- Documentazione automatica dallo schema
- History delle query
- Variabili e header configurabili
- Prettier integrato

### 19.2 Apollo Studio

Piattaforma SaaS per governance dello schema in team:
- **Schema registry:** versioning, changelog, breaking change detection
- **Explorer:** IDE avanzato con team collaboration
- **Metrics:** latenza, error rate, field usage per query
- **Checks:** CI/CD validation di schema changes
- **Contracts:** varianti dello schema per consumer diversi

### 19.3 Rover CLI

```bash
# Introspect schema da endpoint
rover graph introspect http://localhost:4000/graphql > schema.graphql

# Check breaking changes
rover subgraph check my-graph@prod --schema ./schema.graphql --name users

# Publish subgraph schema
rover subgraph publish my-graph@prod --schema ./schema.graphql --name users \
  --routing-url http://users-service:4001/graphql
```

### 19.4 Postman e Insomnia

Entrambi supportano GraphQL con:
- Autocompletamento dallo schema
- Variabili e environment
- Test automatizzati
- Collection condivisibili

Configurazione minima: URL dell'endpoint + body con `query` e `variables`.

### 19.5 ESLint per GraphQL

```bash
npm install @graphql-eslint/eslint-plugin
```

```javascript
// .eslintrc.js — regole per file .graphql
module.exports = {
  overrides: [
    {
      files: ['*.graphql'],
      parser: '@graphql-eslint/eslint-plugin',
      plugins: ['@graphql-eslint'],
      rules: {
        '@graphql-eslint/known-type-names': 'error',
        '@graphql-eslint/no-unreachable-types': 'warn',
        '@graphql-eslint/require-description': ['warn', { types: true }],
        '@graphql-eslint/naming-convention': [
          'error',
          {
            types: 'PascalCase',
            FieldDefinition: 'camelCase',
            EnumValueDefinition: 'UPPER_CASE',
          },
        ],
      },
    },
  ],
};
```

### 19.6 Monitoring e Observability

Un'infrastruttura GraphQL matura richiede osservabilità a tre livelli: **tracing distribuito**, **metriche per campo** e **alerting basato su anomalie**.

**Integrazione OpenTelemetry:**

```typescript
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { GraphQLInstrumentation } from '@opentelemetry/instrumentation-graphql';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';

const provider = new NodeTracerProvider();
provider.addSpanProcessor(
  new BatchSpanProcessor(
    new OTLPTraceExporter({ url: 'http://otel-collector:4318/v1/traces' })
  )
);
provider.register();

// Instrumentazione automatica dei resolver GraphQL
const graphqlInstrumentation = new GraphQLInstrumentation({
  depth: 2,                    // profondità span nei resolver
  allowValues: false,          // non loggare variabili (sicurezza)
  mergeItems: true,            // unifica item di lista in un singolo span
});
graphqlInstrumentation.enable();
```

Ogni risoluzione di campo genera uno span con attributi `graphql.field.name`, `graphql.field.type` e `graphql.operation.name`. Questo permette di individuare resolver lenti con precisione.

**Metriche per campo — field-level analytics:**

```typescript
import { plugin } from 'graphql-yoga';

const fieldMetricsPlugin = plugin({
  onExecute({ args }) {
    const startTimes = new Map<string, number>();

    return {
      onResolverCalled({ info }) {
        const fieldPath = `${info.parentType.name}.${info.fieldName}`;
        startTimes.set(fieldPath, performance.now());
      },
      onResolverDone({ info }) {
        const fieldPath = `${info.parentType.name}.${info.fieldName}`;
        const start = startTimes.get(fieldPath);
        if (start) {
          const duration = performance.now() - start;
          // Esporta a Prometheus, Datadog, etc.
          histogram.observe(
            { field: fieldPath, operation: args.operationName },
            duration / 1000
          );
        }
      },
    };
  },
});
```

**Dashboard essenziali:**

| Metrica | Descrizione | Soglia alert |
|---------|-------------|--------------|
| `graphql.operation.duration` | Latenza end-to-end per operazione | p99 > 2s |
| `graphql.resolver.duration` | Tempo per singolo resolver | p99 > 500ms |
| `graphql.operation.error_rate` | Percentuale di operazioni con errori | > 5% |
| `graphql.depth` | Profondità media delle query | > 8 |
| `graphql.complexity` | Complessità media calcolata | > 500 |
| `graphql.deprecated_field.usage` | Chiamate a campi deprecati | > 0 (alert informativo) |

**Apollo Studio / GraphOS metriche automatiche:**

Se si usa Apollo Router, le metriche di tracing vengono inviate automaticamente ad Apollo Studio. Configurazione minima nel `router.yaml`:

```yaml
telemetry:
  apollo:
    endpoint: https://usage-reporting.api.apollographql.com
    apollo_key: "${APOLLO_KEY}"
    apollo_graph_ref: "my-graph@production"
  exporters:
    tracing:
      otlp:
        enabled: true
        endpoint: http://otel-collector:4317
    metrics:
      prometheus:
        enabled: true
        listen: 0.0.0.0:9090
        path: /metrics
```

### 19.7 GraphQL over HTTP Specification

La specifica **GraphQL over HTTP** (attualmente alla versione draft, mantenuta dalla GraphQL Foundation) standardizza il trasporto di operazioni GraphQL su HTTP, risolvendo ambiguità storiche tra implementazioni diverse.

**Content-Type di richiesta e risposta:**

| Direzione | Content-Type | Note |
|-----------|-------------|------|
| Request body | `application/json` | Standard consolidato |
| Response (legacy) | `application/json` | Compatibilità retroattiva |
| Response (spec) | `application/graphql-response+json` | **Raccomandato** — permette al client di distinguere una risposta GraphQL da un errore generico del gateway |

**Negoziazione content-type:**

```http
POST /graphql HTTP/1.1
Accept: application/graphql-response+json, application/json
Content-Type: application/json

{"query": "{ products { id name } }"}
```

Il server deve rispondere con `application/graphql-response+json` se il client lo accetta, altrimenti fallback a `application/json`.

**GET per query (read-only operations):**

La specifica definisce il supporto GET per operazioni di sola lettura, abilitando il caching HTTP nativo:

```http
GET /graphql?query=%7B%20products%20%7B%20id%20name%20%7D%20%7D HTTP/1.1
Accept: application/graphql-response+json
```

Regole GET:
- **Solo query**, mai mutation o subscription
- Parametri via query string: `query`, `variables` (JSON-encoded), `operationName`, `extensions`
- Il server **DEVE** rifiutare mutation via GET con status `405 Method Not Allowed`
- Abilitare GET solo con persisted queries in produzione (evita URL arbitrariamente lunghi)

**Semantica dei codici di stato HTTP:**

| Status | Quando usarlo |
|--------|---------------|
| `200 OK` | Risposta GraphQL valida (anche se contiene `errors` parziali) |
| `400 Bad Request` | Documento GraphQL non parsabile o validazione fallita |
| `405 Method Not Allowed` | Mutation via GET |
| `406 Not Acceptable` | Client non accetta nessun content-type supportato |
| `415 Unsupported Media Type` | Request body in formato non supportato |

**Attenzione critica:** storicamente molte implementazioni restituiscono `200` anche per errori di parsing. La specifica raccomanda `400` quando l'operazione non può essere eseguita affatto (errori di sintassi, variabili mancanti obbligatorie, tipo di operazione non permesso).

**Implementazione conforme con Yoga:**

```typescript
import { createYoga, createSchema } from 'graphql-yoga';
import { createServer } from 'node:http';

const yoga = createYoga({
  schema: createSchema({ typeDefs, resolvers }),
  // Yoga è conforme alla spec GraphQL over HTTP per default
  // GET abilitato automaticamente per query
  // application/graphql-response+json supportato
  maskedErrors: true,        // nasconde dettagli interni
  batching: { limit: 10 },  // limita batch size
  cors: {
    origin: ['https://app.example.com'],
    methods: ['GET', 'POST'],
  },
});

const server = createServer(yoga);
server.listen(4000);
```

---

## 20. Troubleshooting

### Problema 1: N+1 Query

**Sintomo:** latenza che cresce linearmente con il numero di elementi in una lista. Log del database mostra centinaia di query identiche con ID diverso.

**Causa:** resolver per campi relazionali che eseguono una query per ogni elemento.

**Soluzione:** DataLoader. Ogni campo relazionale deve passare per un DataLoader che fa batch delle richieste. Vedere la sezione [4.4 DataLoader](#44-dataloader--n1-prevention).

---

### Problema 2: Circular References nello Schema

**Sintomo:** `Maximum call stack size exceeded` o loop infinito durante l'esecuzione.

**Causa:** tipo A referenzia tipo B che referenzia tipo A. Non è un problema nello schema (GraphQL lo supporta), ma diventa problema se il client non limita la profondità.

**Soluzione:** depth limit sul server (max 7-10). Il client deve usare fragment e non annidare ricorsivamente.

---

### Problema 3: Cache Invalidation con Apollo Client

**Sintomo:** dopo una mutation, la UI non si aggiorna. I dati stale restano visibili.

**Causa:** Apollo Client non sa automaticamente quali query invalidare dopo una mutation.

**Soluzione:** usare `update`, `refetchQueries` o `cache.modify` nella mutation.

```typescript
const [createPost] = useMutation(CREATE_POST, {
  refetchQueries: [{ query: GET_POSTS }],
  // Oppure
  update(cache, { data }) {
    cache.modify({
      fields: {
        posts(existing) { /* merge new data */ },
      },
    });
  },
});
```

---

### Problema 4: Memory Leak con Subscription

**Sintomo:** il server consuma sempre più memoria nel tempo. Le connessioni WebSocket non vengono chiuse.

**Causa:** subscription non vengono unsubscribed dal client, PubSub listeners si accumulano.

**Soluzione:** implementare heartbeat, timeout di connessione, cleanup del PubSub.

```typescript
// Cleanup automatico dopo inattività
onConnect: (ctx) => {
  ctx.extra.timeout = setTimeout(() => {
    ctx.extra.socket.close(4408, 'Connection timeout');
  }, 30 * 60 * 1000); // 30 minuti
},
onSubscribe: (ctx) => {
  clearTimeout(ctx.extra.timeout);
},
```

---

### Problema 5: Errore "Cannot return null for non-nullable field"

**Sintomo:** `Cannot return null for non-nullable field User.name`

**Causa:** un resolver restituisce `null` per un campo marcato come `!` (non-null) nello schema.

**Soluzione:** o il resolver deve garantire un valore, o il campo deve essere nullable nello schema. Verificare che il database non contenga valori null per colonne che lo schema dichiara non-null.

---

### Problema 6: CORS Error con GraphQL

**Sintomo:** `Access-Control-Allow-Origin` error nel browser.

**Causa:** il server GraphQL non gestisce la preflight OPTIONS o non include gli header CORS corretti.

**Soluzione:**

```typescript
app.use(
  '/graphql',
  cors({
    origin: ['https://app.example.com'],
    credentials: true,
    methods: ['POST', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization'],
  }),
  expressMiddleware(server, { context }),
);
```

---

### Problema 7: Variabili non passate alla Query

**Sintomo:** i resolver ricevono `undefined` per gli argomenti.

**Causa:** le variabili sono dichiarate nella query ma non passate nel payload JSON, o il nome non corrisponde.

**Soluzione:** verificare che il payload contenga `{ "query": "...", "variables": { ... } }` con i nomi corretti. Le variabili nella query si dichiarano con `$`, nel JSON senza `$`.

---

### Problema 8: Schema Stitching vs Federation — Conflitti

**Sintomo:** tipi duplicati, resolver che non vengono chiamati, campi mancanti nel supergraph.

**Causa:** confusione tra schema stitching (deprecato) e Federation v2.

**Soluzione:** migrare a Federation v2. Usare `@key` per entity resolution, `@shareable` per campi condivisi tra subgraph.

---

### Problema 9: Upload File non Funziona

**Sintomo:** `Upload` scalar non riconosciuto, file è `undefined` nel resolver.

**Causa:** il middleware di parsing multipart non è configurato o l'ordine dei middleware è sbagliato.

**Soluzione:** usare `graphql-upload-ts` con il middleware prima di Apollo Server, o usare GraphQL Yoga che supporta upload nativamente.

---

### Problema 10: Query Troppo Lenta — Timeout

**Sintomo:** la query va in timeout dopo 30s.

**Causa:** query complessa che attraversa molti nodi del grafo, o mancanza di indici nel database.

**Soluzione:** analizzare la query con Apollo Studio o logging custom. Verificare: DataLoader attivo? Indici database presenti? Complessità della query entro i limiti?

---

### Problema 11: Enum Value non Riconosciuto

**Sintomo:** `Expected type UserRole, found "admin".`

**Causa:** gli enum in GraphQL sono case-sensitive. `admin` non corrisponde a `ADMIN`.

**Soluzione:** usare il valore esatto come definito nello schema: `ADMIN`, non `admin` o `Admin`.

---

### Problema 12: DataLoader Restituisce Risultati nell'Ordine Sbagliato

**Sintomo:** i dati sono associati agli utenti sbagliati.

**Causa:** la funzione batch del DataLoader non restituisce i risultati nello stesso ordine degli ID di input.

**Soluzione:** creare una Map dagli ID e mappare nel medesimo ordine degli input. Vedere il pattern nella sezione [4.4](#44-dataloader--n1-prevention).

---

### Problema 13: Apollo Client Cache — __typename Mancante

**Sintomo:** la cache normalizzata non funziona, gli oggetti non vengono riconosciuti.

**Causa:** `__typename` è necessario per la normalizzazione della cache. Se disabilitato o mancante, Apollo Client non può identificare gli oggetti.

**Soluzione:** non disabilitare `addTypename` (è attivo per default). Se si usano `fetchPolicy: 'no-cache'`, la cache viene bypassata interamente.

---

### Problema 14: Type Collision in Federation

**Sintomo:** `Type "User" already defined in another subgraph`

**Causa:** due subgraph definiscono lo stesso tipo senza usare `@key` per la entity resolution.

**Soluzione:** usare `@key(fields: "id")` per marcare i tipi come entity condivise. Usare `@shareable` per campi definiti in più subgraph.

---

### Problema 15: Hot Reload non Rileva Cambiamenti nello Schema

**Sintomo:** modifiche allo schema SDL non si riflettono nel server.

**Causa:** il file SDL è stato letto una sola volta all'avvio. `readFileSync` non viene rieseguito.

**Soluzione:** in sviluppo, usare `nodemon --watch schema.graphql` o strumenti come `graphql-yoga` che supportano il ricaricamento dello schema.

---

### Problema 16: Subscription non Riceve Messaggi

**Sintomo:** la connessione WebSocket è aperta ma nessun messaggio arriva.

**Causa:** il topic del PubSub nel subscribe non corrisponde a quello del publish, o `withFilter` filtra tutto.

**Soluzione:** verificare che le costanti dei topic siano identiche tra `publish` e `subscribe`. Debuggare il predicato di `withFilter`.

---

### Problema 17: Performance Degradata con Query Grandi

**Sintomo:** query che restituiscono migliaia di oggetti sono lente.

**Causa:** assenza di paginazione, serializzazione JSON di payload enormi.

**Soluzione:** implementare paginazione obbligatoria con limite massimo (es. `first: 100`). Mai consentire query senza limit.

---

### Problema 18: Fragment Spread su Tipo Sbagliato

**Sintomo:** `Fragment "UserFields" cannot be spread here as objects of type "Post" can never be of type "User"`

**Causa:** un fragment definito su un tipo viene usato in una selezione su un tipo diverso e incompatibile.

**Soluzione:** verificare che il fragment sia definito sul tipo corretto. Usare inline fragment (`... on User`) se il tipo è un membro di una union.

---

### Problema 19: Circular Dependency nei Moduli (Code-First)

**Sintomo:** `ReferenceError: Cannot access 'UserType' before initialization`

**Causa:** in approccio code-first, `UserType` referenzia `PostType` che referenzia `UserType` — circular import.

**Soluzione:** usare `lazy resolution` — passare una funzione che restituisce il tipo.

```typescript
// Con Pothos — la risoluzione lazy è gestita automaticamente
// Con graphql-js, usare thunk:
fields: () => ({
  posts: { type: new GraphQLList(PostType) },
})
```

---

### Problema 20: Errore di Serializzazione Custom Scalar

**Sintomo:** `DateTime cannot represent value: [object Object]`

**Causa:** il resolver restituisce un oggetto che il custom scalar non sa serializzare (es. un Prisma DateTime che non è un `Date` standard).

**Soluzione:** verificare che il valore restituito dal resolver corrisponda al tipo atteso dalla funzione `serialize` del custom scalar.

---

### Problema 21: Apollo Client Refetch non Aggiorna la UI

**Sintomo:** `refetch()` viene chiamato ma la UI non cambia.

**Causa:** `fetchPolicy: 'cache-first'` — se la cache ha dati, non aggiorna la UI anche dopo refetch.

**Soluzione:** usare `fetchPolicy: 'cache-and-network'` o chiamare `refetch()` che forza una network request indipendentemente dalla policy.

---

## 21. FAQ

**D1: GraphQL sostituisce REST?**

No. GraphQL e REST risolvono problemi diversi. REST eccelle per API pubbliche, caching HTTP nativo e semplicità. GraphQL eccelle per client eterogenei, relazioni complesse e riduzione delle richieste di rete. Molte architetture usano entrambi.

---

**D2: Come gestire il versionamento in GraphQL?**

GraphQL non usa versionamento per URL. L'approccio è l'evoluzione continua dello schema: aggiungere nuovi campi, deprecare quelli vecchi con `@deprecated`, rimuoverli dopo un periodo di grazia. Il code generation e i breaking change check in CI prevengono rotture accidentali.

---

**D3: GraphQL è più lento di REST?**

No intrinsecamente. Una query GraphQL che richiede gli stessi dati di un endpoint REST ha performance comparabili. GraphQL può essere più veloce se elimina over-fetching o riduce il numero di round-trip. Può essere più lento se la query è eccessivamente complessa o il batching non è implementato (N+1).

---

**D4: Serve un database specifico per GraphQL?**

No. GraphQL è agnostico rispetto al data source. Funziona con PostgreSQL, MongoDB, MySQL, API REST, file, servizi gRPC, qualsiasi cosa. I resolver sono il layer di astrazione.

---

**D5: Come si gestisce l'upload di file in GraphQL?**

Due approcci: (1) multipart upload diretto via `graphql-upload` — semplice ma il server deve gestire lo stream. (2) Presigned URL — il server genera un URL firmato, il client carica direttamente allo storage. Il secondo è preferito per file grandi. Vedere la sezione [17. Gestione File](#17-gestione-file).

---

**D6: Posso usare GraphQL con microservizi?**

Si. Apollo Federation permette di comporre un supergraph da più subgraph (microservizi), ciascuno responsabile di un dominio. Il Router gestisce la distribuzione delle query.

---

**D7: Come si testa un'API GraphQL?**

Schema testing (validità dello schema), unit testing dei resolver (mock delle dipendenze), integration testing con `server.executeOperation()`, E2E testing con Playwright o simili. Vedere la sezione [14. Testing](#14-testing).

---

**D8: GraphQL è sicuro?**

Non per default. GraphQL espone un linguaggio di query — senza limiti, un attaccante può costruire query che esplodono esponenzialmente. Serve: depth limiting, complexity analysis, rate limiting, persisted queries, introspection disabilitata in produzione. Vedere la sezione [16. Sicurezza](#16-sicurezza).

---

**D9: Qual è la differenza tra DataLoader e caching?**

DataLoader fa **batching** (raggruppa query nella stessa richiesta) e **caching per richiesta** (la stessa entità richiesta due volte produce una sola query). Non è un cache persistente. Il caching vero (Redis, CDN) è una strategia complementare per evitare query ripetute tra richieste diverse.

---

**D10: Quando usare subscription vs polling?**

Subscription: dati che cambiano frequentemente e devono apparire immediatamente (chat, notifiche, gioco in tempo reale). Polling: dati che cambiano raramente o dove la latenza di qualche secondo è accettabile (dashboard, analytics). SSE: alternativa leggera a WebSocket quando la comunicazione è unidirezionale.

---

**D11: Come gestire la paginazione con cursor opachi?**

Il cursor è un valore opaco (tipicamente base64 dell'ID o di un timestamp) che il client non deve interpretare. Il server lo decodifica per determinare il punto di partenza della pagina successiva. Questo rende il cursor resistente a cambiamenti nello schema del database.

---

**D12: Apollo Server o Yoga?**

Apollo Server: ecosistema più maturo, Apollo Studio integration, plugin ricco. Yoga: più leggero, supporta edge runtime (Cloudflare Workers, Deno), subscription SSE nativo, licenza MIT. Per progetti enterprise con Apollo Gateway/Federation, Apollo Server. Per tutto il resto, Yoga è un'alternativa solida.

---

**D13: Come evitare lo schema bloat?**

Principi: (1) ogni campo deve avere un consumer reale — non aggiungere campi "perché potrebbe servire". (2) Usare field usage analytics per identificare e deprecare campi inutilizzati. (3) Preferire pochi tipi ben strutturati a molti tipi poco usati.

---

**D14: Qual è la differenza tra interface e union?**

Interface: i tipi implementanti condividono campi comuni. Union: i tipi non hanno campi in comune. Usare interface quando i tipi hanno una struttura simile (es. `Node` con `id`). Usare union quando sono completamente diversi (es. `SearchResult = User | Post | Tag`).

---

**D15: Come funziona la normalizzazione della cache in Apollo Client?**

Apollo Client identifica ogni oggetto nella cache con `__typename:id`. Quando una query restituisce un `User` con `id: "42"`, Apollo aggiorna tutte le query che referenziano lo stesso `User:42`. Questo permette aggiornamenti automatici della UI quando i dati cambiano tramite mutation.

---

**D16: Code-first o schema-first?**

Schema-first: contratto leggibile, team alignment, ideale per API pubbliche. Code-first (Pothos, Nexus): type safety completa in TypeScript, refactoring più sicuro, ideale per team full-stack TypeScript. Non esiste una risposta universale — dipende dal contesto.

---

## 22. Best Practice e Anti-Pattern

### Best Practice

1. **Schema-first per API pubbliche.** Definire il contratto prima dell'implementazione. Condividere lo schema con i consumer per feedback early.

2. **DataLoader per ogni campo relazionale.** Senza eccezioni. Anche se oggi la lista ha 3 elementi, domani ne avrà 3000.

3. **Payload pattern per le mutation.** Restituire un tipo dedicato con `{ result, errors }`, mai il tipo dell'entità direttamente.

4. **Input type dedicati per ogni mutation.** `CreateUserInput` e `UpdateUserInput` sono tipi distinti. Mai riusare lo stesso input type per operazioni diverse.

5. **Paginazione obbligatoria per le liste.** Ogni campo che restituisce un array deve avere un limite massimo. Mai consentire query unbounded.

6. **Non-null per default.** Usare `!` per tutti i campi che il server garantisce. La nullabilità è l'eccezione, non la regola.

7. **Usare enum invece di stringhe.** Per ogni campo con un insieme finito di valori.

8. **Code generation.** Generare tipi TypeScript dallo schema. Nessun tipo manuale.

9. **Persisted queries in produzione.** Riduce banda, migliora sicurezza.

10. **Monitorare field usage.** Deprecare e rimuovere campi inutilizzati.

### Anti-Pattern

1. **CRUD mapping diretto.** Non creare lo schema come mirror del database. Lo schema rappresenta il dominio applicativo, non le tabelle.

2. **Generic resolver "catch-all".** Un singolo resolver che gestisce qualsiasi tipo per dinamicità — sacrifica type safety e leggibilità.

3. **Business logic nei resolver.** I resolver devono essere sottili: validazione input, chiamata al service layer, formattazione output. La business logic vive nei service.

4. **Esporre ID interni del database.** Usare ID opachi (UUID o base64) nello schema pubblico, mai auto-increment integer.

5. **Schema come wrapper 1:1 del database.** Lo schema deve riflettere il dominio dell'utente, non la struttura del database. Aggregare, derivare, nascondere dove necessario.

6. **Ignorare la complessità delle query.** Senza limiti di profondità e complessità, un attaccante può costruire query che mandano in ginocchio il server.

7. **Non-null ovunque senza pensare.** Se un servizio esterno può fallire, il campo deve essere nullable per consentire risultati parziali.

8. **Subscription per tutto.** Le subscription hanno un costo (connessioni persistenti, PubSub). Usarle solo quando il polling non è adeguato.

9. **Schema monolitico gigante.** In un sistema grande, usare Federation per dividere lo schema tra team.

10. **Mancanza di documentazione nello schema.** Ogni tipo, campo e argomento deve avere una descrizione.

```graphql
# ANTI-PATTERN — schema senza descrizioni
type User {
  id: ID!
  name: String!
}

# BEST PRACTICE — schema documentato
"""
Un utente registrato nella piattaforma.
"""
type User {
  "Identificatore univoco opaco."
  id: ID!
  "Nome visualizzato pubblicamente."
  name: String!
  "Indirizzo email. Visibile solo all'utente stesso e agli admin."
  email: String!
}
```

---

## 23. Esercizi Pratici

### Esercizio 1 — Schema Design per Blog

**Obiettivo:** progettare lo schema GraphQL per una piattaforma blog.

**Requisiti:**
- Utenti con ruoli (admin, editor, author, viewer)
- Post con status (draft, review, published, archived)
- Commenti annidati (reply a commenti)
- Tag e categorie
- Paginazione cursor-based per post e commenti

**Deliverable:** file `schema.graphql` completo con query, mutation, tipi e input.

**Criteri di valutazione:**
- Uso corretto di non-null
- Input type separati per create/update
- Payload pattern per le mutation
- Enum per valori finiti
- Documentazione nello schema

---

### Esercizio 2 — Resolver con DataLoader

**Obiettivo:** implementare i resolver per lo schema dell'esercizio 1, con DataLoader per tutte le relazioni.

**Setup:** Node.js + TypeScript + Apollo Server + Prisma + PostgreSQL.

**Requisiti:**
- DataLoader per `posts.author`, `post.comments`, `user.posts`
- Nessuna query N+1 (verificare con logging delle query DB)
- Paginazione cursor-based funzionante
- Error handling con `GraphQLError`

**Verifica:** abilitare il query logging di Prisma e dimostrare che una query che restituisce 20 post con i rispettivi autori esegue al massimo 3 query SQL.

---

### Esercizio 3 — Autenticazione e Autorizzazione

**Obiettivo:** aggiungere autenticazione JWT e autorizzazione role-based al server dell'esercizio 2.

**Requisiti:**
- Mutation `login(email, password)` che restituisce un JWT
- Context factory che estrae e verifica il JWT dall'header `Authorization`
- Directive `@auth(requires: Role)` implementata come schema transformer
- Campi `email` e `privateData` visibili solo al proprietario o admin
- Test che verificano: accesso anonimo bloccato, accesso con ruolo insufficiente bloccato, accesso autorizzato permesso

---

### Esercizio 4 — Apollo Client con Cache

**Obiettivo:** costruire un client React che consuma l'API GraphQL.

**Setup:** React + TypeScript + Apollo Client + GraphQL Code Generator.

**Requisiti:**
- Lista post con paginazione cursor-based (infinite scroll)
- Dettaglio post con commenti
- Mutation "crea post" con aggiornamento ottimistico della lista
- Mutation "toggle like" con optimistic response
- Reactive variable per tema light/dark
- Code generation: tutti i hook generati, nessun tipo manuale

---

### Esercizio 5 — Subscription Real-Time

**Obiettivo:** implementare un sistema di commenti real-time.

**Requisiti:**
- Subscription `commentAdded(postId: ID!)` con WebSocket
- PubSub con `withFilter` per filtrare per `postId`
- Client React che aggiorna automaticamente la lista commenti
- Autenticazione sulla connessione WebSocket
- Heartbeat e timeout di connessione

---

### Esercizio 6 — Security Hardening

**Obiettivo:** rendere sicuro il server GraphQL per la produzione.

**Checklist implementativa:**
- [ ] Introspection disabilitata in `NODE_ENV=production`
- [ ] Depth limit a 7
- [ ] Query complexity limit a 1000
- [ ] Rate limiting: 100 query/minuto per utente autenticato, 20/minuto per anonimi
- [ ] Persisted queries con allowlist
- [ ] Field suggestions disabilitate in produzione
- [ ] Stack trace rimosse dalle risposte
- [ ] CORS configurato con origin specifiche
- [ ] Input validation sui resolver
- [ ] Max body size 1MB

**Verifica:** tentare ogni vettore di attacco e verificare che venga bloccato.

---

### Esercizio 7 — Apollo Federation

**Obiettivo:** scomporre l'applicazione blog in 3 subgraph federati.

**Architettura:**
- Subgraph Users: autenticazione, profili, ruoli
- Subgraph Posts: creazione, pubblicazione, tag
- Subgraph Comments: commenti, moderazione

**Requisiti:**
- Entity resolution con `@key`
- Campi cross-subgraph (Post.author risolto dal subgraph Users)
- Apollo Router configurato
- Test E2E che verificano query cross-subgraph

---

### Esercizio 8 — Migrazione REST → GraphQL

**Obiettivo:** creare un layer BFF GraphQL davanti a un'API REST esistente.

**Setup:** un'API REST mock con endpoint `/users`, `/posts`, `/comments`.

**Requisiti:**
- Schema GraphQL che aggrega i 3 endpoint REST
- Resolver che chiamano l'API REST via `fetch`
- DataLoader per batch delle richieste REST
- Paginazione GraphQL che wrappa la paginazione REST
- Confronto performance: quante richieste HTTP servono per la stessa view con REST vs GraphQL

---

## 24. Glossario

| Termine | Definizione |
|---------|-------------|
| **SDL** | Schema Definition Language. Linguaggio dichiarativo per definire lo schema GraphQL. |
| **Resolver** | Funzione che calcola il valore di un campo nello schema. |
| **DataLoader** | Libreria per batching e caching per-request, previene N+1. |
| **Introspection** | Capacità di interrogare lo schema a runtime (`__schema`, `__type`). |
| **Fragment** | Blocco riusabile di selezione campi su un tipo specifico. |
| **Directive** | Annotazione che modifica il comportamento di schema o esecuzione (`@deprecated`, `@auth`). |
| **Input Type** | Tipo usato esclusivamente come argomento di query/mutation. |
| **Union** | Tipo che può essere uno tra diversi tipi concreti senza campi condivisi. |
| **Interface** | Tipo astratto che definisce campi che i tipi concreti devono implementare. |
| **Subscription** | Operazione che apre uno stream di dati real-time dal server. |
| **PubSub** | Pattern publish-subscribe per emettere e ricevere eventi (usato nelle subscription). |
| **Persisted Query** | Query pre-registrata sul server, identificata da hash invece che dal testo completo. |
| **APQ** | Automatic Persisted Queries. Protocollo di negoziazione automatica tra client e server. |
| **Federation** | Architettura per comporre un supergraph da più subgraph indipendenti. |
| **Subgraph** | Servizio GraphQL che contribuisce una porzione dello schema federato. |
| **Supergraph** | Schema composto risultante dalla composizione di più subgraph. |
| **Router/Gateway** | Servizio che riceve le query client e le distribuisce ai subgraph appropriati. |
| **Code Generation** | Processo di generazione automatica di tipi e hook dal schema e dalle operazioni. |
| **Depth Limit** | Regola di validazione che limita la profondità massima di una query. |
| **Complexity Analysis** | Calcolo del costo computazionale di una query basato sui campi richiesti. |
| **N+1 Problem** | Anti-pattern dove N entità figlie generano N query separate al database. |
| **Normalized Cache** | Cache che identifica gli oggetti per `__typename:id` e li deduplicata. |
| **Optimistic Response** | Aggiornamento immediato della UI prima della conferma del server. |
| **BFF** | Backend for Frontend. Layer intermedio che adatta l'API backend alle esigenze del frontend. |
| **Connection Spec** | Specifica Relay per la paginazione cursor-based (edges, nodes, pageInfo). |
| **Payload Pattern** | Convenzione che wrappa il risultato di una mutation in un tipo dedicato con errori. |

---

## 25. Letture e Risorse

### Specifiche e Documentazione Ufficiale

- GraphQL Specification. https://spec.graphql.org/
- Apollo Server Documentation. https://www.apollographql.com/docs/apollo-server/
- Apollo Client Documentation. https://www.apollographql.com/docs/react/
- GraphQL Yoga Documentation. https://the-guild.dev/graphql/yoga-server
- Relay Specification — Connections. https://relay.dev/graphql/connections.htm
- Mercurius Documentation. https://mercurius.dev/
- Pothos Documentation. https://pothos-graphql.dev/

### Librerie e Strumenti

- DataLoader — https://github.com/graphql/dataloader
- GraphQL Code Generator — https://the-guild.dev/graphql/codegen
- GraphQL Tools — https://the-guild.dev/graphql/tools
- graphql-scalars — https://the-guild.dev/graphql/scalars
- graphql-shield — https://github.com/dimatill/graphql-shield
- graphql-ws — https://github.com/enisdenjo/graphql-ws
- URQL Documentation — https://urql.dev/

### Articoli e Approfondimenti

- Principled GraphQL. https://principledgraphql.com/
- Production Ready GraphQL (libro, Marc-Andre Giroux). https://productionreadygraphql.com/
- Apollo Federation Specification. https://www.apollographql.com/docs/federation/
- GraphQL Cursor Connections Specification. https://relay.dev/graphql/connections.htm
- GraphQL Multipart Request Specification. https://github.com/jaydenseric/graphql-multipart-request-spec

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [11 — API Design](11-api-design.md) | REST vs GraphQL, OpenAPI e scelta architetturale tra paradigmi |
| [06 — TypeScript](06-typescript.md) | Type safety end-to-end con Code Generation e tipi GraphQL |
| [13 — Autenticazione](13-autenticazione-autorizzazione.md) | JWT, OAuth 2.0 e autorizzazione role-based nei resolver |
| [12 — Database Web](12-database-web.md) | Prisma/Drizzle come data layer per resolver GraphQL |
| [14 — Sicurezza Web](14-sicurezza-web.md) | Depth limiting, complexity analysis e protezione introspection |
| [15 — Testing Web](15-testing-web.md) | Test di resolver, integration test e mocking di schema GraphQL |
