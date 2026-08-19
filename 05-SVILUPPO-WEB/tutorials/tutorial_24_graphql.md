# Tutorial 24 — GraphQL: Dal Principiante all'Esperto

> **Companion a:** `24-graphql-guida-completa.md`
> **Scope:** schema-first e SDL · tipi, interfacce, union, input · query, mutation e subscription · la catena dei resolver · N+1 e DataLoader · propagazione del null · errori parziali e union di errore · autorizzazione al campo · complessità, profondità e attacchi con alias · paginazione a cursore · cache normalizzata · Federation · codegen e osservabilità
> **Prerequisiti:** `tutorial_06_typescript.md`, `tutorial_11_api_design.md`, `tutorial_12_database_web.md`, `tutorial_22_rate_limiting_edge.md` — sai progettare un'API, scrivere query efficienti e limitare il traffico
> **Durata stimata:** 6-8 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** GraphQL spec (ottobre 2021) · Apollo Server 4 · Apollo Client 3 · GraphQL Yoga 5 · DataLoader 2 · Prisma 6

---

## Indice Generale

- **[Parte A — Basi Assolute](#parte-a--basi-assolute)**
  - [A1. Il problema che GraphQL risolve](#a1-il-problema-che-graphql-risolve)
  - [A2. Lo schema è il contratto](#a2-lo-schema-è-il-contratto)
  - [A3. Query, mutation, subscription](#a3-query-mutation-subscription)
  - [A4. I resolver e la catena](#a4-i-resolver-e-la-catena)
  - [A5. N+1: il difetto strutturale, e DataLoader](#a5-n1-il-difetto-strutturale-e-dataloader)
- **[Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)**
  - [B1. Il null che si propaga verso l'alto](#b1-il-null-che-si-propaga-verso-lalto)
  - [B2. Errori parziali, e l'union di errore](#b2-errori-parziali-e-lunion-di-errore)
  - [B3. Autorizzare al campo, non alla rotta](#b3-autorizzare-al-campo-non-alla-rotta)
  - [B4. GraphQL espone un linguaggio](#b4-graphql-espone-un-linguaggio)
  - [B5. Alias e batching: gli attacchi che aggirano il limite](#b5-alias-e-batching-gli-attacchi-che-aggirano-il-limite)
  - [B6. Paginazione: cursore contro offset](#b6-paginazione-cursore-contro-offset)
  - [B7. La cache, che non è quella di HTTP](#b7-la-cache-che-non-è-quella-di-http)
  - [B8. Subscription: cosa cambia](#b8-subscription-cosa-cambia)
  - [B9. Federation: quando un solo schema non basta](#b9-federation-quando-un-solo-schema-non-basta)
- **[Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)**
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: l'API del portale in GraphQL](#c2-mini-progetto-lapi-del-portale-in-graphql)
- **[Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)**
  - [D1. Testare uno schema](#d1-testare-uno-schema)
  - [D2. Codegen: i tipi che non si scrivono](#d2-codegen-i-tipi-che-non-si-scrivono)
  - [D3. Osservare per campo, non per endpoint](#d3-osservare-per-campo-non-per-endpoint)
  - [D4. Migrare da REST, e il BFF](#d4-migrare-da-rest-e-il-bff)
  - [D5. Quando NON serve GraphQL](#d5-quando-non-serve-graphql)
- **[Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)**

---

## Mappa concettuale

```
   CLIENT                                            SERVER
     │  POST /graphql                                   │
     │  { query, variables, operationName }              │
     ├──────────────────────────────────────────────────►│
     │                                    ① PARSE        │  sintassi
     │                                    ② VALIDATE     │  contro lo schema
     │                                       + profondità · complessità
     │                                    ③ EXECUTE      │  resolver per campo
     │◄──────────────────────────────────────────────────┤
     │  { data, errors, extensions }                      │
     │  200 anche quando errors è pieno                   │

   LO SCHEMA          tipi · interfacce · union · input · direttive
   I RESOLVER         (parent, args, context, info) → valore o Promise
   IL PERICOLO        un campo = una query → N+1, e lo risolve DataLoader
   LA SUPERFICIE      il client scrive la query: profondità, complessità,
                      alias e batch vanno limitati dal server
```

---

# Parte A — Basi Assolute

---

## A1. Il problema che GraphQL risolve

> **Analogia:** il menù fisso e quello à la carte. Con REST ordini il "menù del giorno": arriva tutto, anche il contorno che non volevi, e se ti serve il dolce devi fare una seconda ordinazione. Con GraphQL scrivi tu cosa vuoi nel piatto, e arriva quello.

```
LO SCHERMO: nome utente, avatar, ultimi 3 post, e per ogni post il
numero di commenti.

  REST                                    chiamate
    GET /utenti/42                          1
    GET /utenti/42/post?limit=3             1
    GET /post/{id}/commenti/count           3
                                          ────
                                            5, in due giri di rete —
                                            e la prima risposta porta
                                            trenta campi per usarne due

  GraphQL                                   1
    una query che descrive esattamente la forma dello schermo
```

```
I DUE PROBLEMI CHE PORTANO A GRAPHQL, e hanno nomi precisi

  OVER-FETCHING   la risposta contiene campi che non servono. Costa
                  banda, e su rete mobile si vede.
  UNDER-FETCHING  la risposta non basta, e serve un'altra chiamata
                  che dipende dalla prima. Costa LATENZA, ed è il
                  problema serio: le chiamate si accodano.

⚠ E IL PREZZO, che va detto subito: il client scrive la query, quindi
  il server non sa più in anticipo cosa gli verrà chiesto. Sparisce
  la cache HTTP (§B7), sparisce il "una rotta, un costo prevedibile"
  (§B4), e ogni campo diventa un punto in cui autorizzare (§B3).
```

---

## A2. Lo schema è il contratto

Lo schema si scrive in SDL (Schema Definition Language), e viene **prima** dei resolver. È il punto di verità fra chi scrive il client e chi scrive il server.

```graphql
type Utente {
  id: ID!
  nome: String!
  email: String        # nullable: solo il proprietario lo vede (§B3)
  post(primi: Int = 10): [Post!]!
  creatoIl: DateTime!  # scalare custom
}

type Post {
  id: ID!
  titolo: String!
  corpo: String!
  autore: Utente!
  commenti(primi: Int = 20): [Commento!]!
}

type Query {
  utente(id: ID!): Utente        # può non esistere → nullable
  post(id: ID!): Post
  cercaPost(testo: String!): [Post!]!
}
```

```
IL PUNTO ESCLAMATIVO È LA DECISIONE PIÙ PESANTE DELLO SCHEMA

  [Post!]!   la lista c'è sempre, e nessun elemento è null
  [Post!]    la lista può essere null, ma se c'è è piena
  [Post]!    la lista c'è, e può contenere null
  [Post]     tutto può essere null

⚠ IL `!` NON È "UN CAMPO OBBLIGATORIO": è una PROMESSA che il server
  fa. Se un resolver di un campo non-null fallisce, GraphQL non può
  restituire null lì — e il null risale, portandosi via il genitore
  (§B1). Un `!` messo a caso su un campo che dipende da un servizio
  esterno significa che quel servizio può cancellare metà risposta.

➜ LA REGOLA CHE FUNZIONA: `!` su ciò che è strutturalmente sempre
  presente — l'id, il titolo, la lista che al peggio è vuota.
  Nullable su ciò che dipende da un permesso, da una rete, o
  dall'esistenza di qualcosa.
```

```graphql
# INTERFACE — campi comuni, tipi diversi
interface Contenuto {
  id: ID!
  autore: Utente!
}

type Post implements Contenuto { id: ID!, autore: Utente!, titolo: String! }
type Commento implements Contenuto { id: ID!, autore: Utente!, testo: String! }

# UNION — tipi senza niente in comune, per un risultato eterogeneo
union RisultatoRicerca = Post | Commento | Utente

# INPUT — un tipo che si usa come argomento. Non può contenere
# oggetti di output, e questa separazione non è burocrazia: un tipo
# di output porta campi calcolati che non hanno senso in entrata.
input FiltroPost {
  autoreId: ID
  dopo: DateTime
  tag: [String!]
}
```

⚠ Ogni interfaccia e ogni union ha bisogno di un `resolveType` (o di un campo `__typename` nel dato) che dica al server quale tipo concreto sta restituendo. Senza, l'esecuzione fallisce a runtime con un errore che non menziona mai il tipo mancante.

---

## A3. Query, mutation, subscription

```graphql
# Il client descrive la forma. `$id` è una VARIABILE: mai
# interpolare valori nel testo della query, per lo stesso motivo per
# cui non si interpola in SQL (§B4).
query PaginaUtente($id: ID!, $quantiPost: Int!) {
  utente(id: $id) {
    nome
    post(primi: $quantiPost) {
      titolo
      # ALIAS: lo stesso campo due volte, con nomi diversi
      recenti: commenti(primi: 3) { testo }
      totale: numeroCommenti
    }
  }
}
```

```graphql
# I FRAMMENTI evitano di ripetere la stessa selezione, e sono il
# modo in cui un componente dichiara di cosa ha bisogno: ogni
# componente porta il suo frammento, e la pagina li compone.
fragment DatiAutore on Utente {
  id
  nome
  avatar
}

query Feed {
  post(primi: 10) {
    titolo
    autore { ...DatiAutore }
    commenti(primi: 5) {
      testo
      autore { ...DatiAutore }
    }
  }
}
```

```
LE TRE OPERAZIONI, E UNA DIFFERENZA CHE CONTA

  query          lettura: i campi di primo livello vanno in PARALLELO
  mutation       scrittura: i campi di primo livello vanno in
                 SEQUENZA, nell'ordine scritto — è l'unica garanzia
                 d'ordine che la specifica dà
  subscription   un flusso di eventi nel tempo (§B8)

⚠ LA DISTINZIONE NON È APPLICATA DAL MOTORE: niente impedisce a un
  resolver di `Query` di scrivere sul database. Se lo fa, due campi
  di query in parallelo scrivono in parallelo, e il client che manda
  la stessa query due volte scrive due volte. La convenzione va
  rispettata dal codice, perché nessuno la verifica.
```

```graphql
# Una mutation restituisce ciò che ha cambiato, così il client
# aggiorna la sua cache senza rileggere (§B7)
type Mutation {
  creaPost(input: CreaPostInput!): CreaPostRisultato!
  eliminaPost(id: ID!): EliminaPostRisultato!
}
```

---

## A4. I resolver e la catena

Un resolver è una funzione che produce il valore di **un campo**. Riceve sempre gli stessi quattro argomenti.

```typescript
type Risolutore<Padre, Argomenti, Risultato> = (
  padre: Padre,        // il valore risolto dal campo GENITORE
  argomenti: Argomenti,// gli argomenti di QUESTO campo
  contesto: Contesto,  // uguale per tutta la richiesta: utente, loader, db
  info: GraphQLResolveInfo, // l'AST della query: quali campi sono chiesti
) => Risultato | Promise<Risultato>
```

```typescript
export const risolutori = {
  Query: {
    // `padre` è undefined: è la radice
    utente: (_padre, { id }: { id: string }, ctx: Contesto) =>
      ctx.loader.utentePerId.load(id),
  },

  Utente: {
    // `padre` è l'Utente risolto sopra. Questo resolver esiste solo
    // perché `post` non è una proprietà dell'oggetto utente.
    post: (padre: Utente, { primi }: { primi: number }, ctx: Contesto) =>
      ctx.loader.postPerAutore.load({ autoreId: padre.id, primi }),

    // ⚠ Il campo esiste nello schema come nullable: se chi chiede
    //   non è il proprietario, si restituisce null invece di
    //   sollevare un errore che cancellerebbe il resto (§B1, §B3)
    email: (padre: Utente, _a, ctx: Contesto) =>
      ctx.utente?.id === padre.id ? padre.email : null,
  },
}
```

```
LA CATENA, PASSO PER PASSO — query { utente(id:"1") { post { titolo } } }

  1. Query.utente   → { id: "1", nome: "Ada", … }
  2. Utente.post    ← riceve quell'oggetto come `padre`
                    → [ {id:"7", …}, {id:"9", …} ]
  3. Post.titolo    ← riceve ogni post come `padre`
                    → non c'è un resolver: il DEFAULT RESOLVER legge
                      `padre.titolo` e basta

⚠ IL DEFAULT RESOLVER È LA RAGIONE per cui uno schema di venti tipi
  ha cinque resolver: si scrivono solo i campi che NON sono già una
  proprietà dell'oggetto restituito dal genitore.

➜ E IL PUNTO 3 SI RIPETE PER OGNI POST. È da qui che nasce l'N+1.
```

---

## A5. N+1: il difetto strutturale, e DataLoader

> **Analogia:** dieci persone in ufficio che vogliono un caffè. Puoi scendere dieci volte, una per ciascuno, oppure raccogliere le ordinazioni e scendere una volta sola. Il bar è lo stesso; cambia quante volte fai le scale.

```
IL PROBLEMA: il resolver di un campo viene chiamato UNA VOLTA PER
ELEMENTO del genitore. Nessuno lo scrive: è come funziona il motore.

  query { post(primi: 10) { titolo autore { nome } } }

  Query.post     → SELECT * FROM post LIMIT 10            1 query
  Post.autore    → SELECT * FROM utente WHERE id = 3     ┐
  Post.autore    → SELECT * FROM utente WHERE id = 7     │ 10 query
  …                                                       ┘
                                                    ─────
                                                     11 query per 10 post
                                                   1001 per 1000

⚠ E CON I POST DI TRE AUTORI DIVERSI, la stessa riga viene letta
  più volte: l'N+1 di GraphQL è peggiore di quello di un ORM, perché
  non c'è un punto solo dove metterci una join.
```

```typescript
// DataLoader fa due cose: accumula le chiamate di un tick dell'event
// loop in un array (BATCHING), e ricorda i risultati per la durata
// della richiesta (CACHING).
import DataLoader from 'dataloader'

export function creaLoader(db: PrismaClient) {
  return {
    utentePerId: new DataLoader<string, Utente | Error>(async (ids) => {
      const utenti = await db.utente.findMany({ where: { id: { in: [...ids] } } })
      const perId = new Map(utenti.map((u) => [u.id, u]))

      // ⚠ L'ORDINE È UN CONTRATTO: l'array restituito deve avere la
      //   stessa lunghezza e lo stesso ordine di `ids`. Restituire
      //   direttamente il risultato del database mescola i dati fra
      //   gli utenti — ed è un bug di sicurezza, non di prestazioni.
      return ids.map((id) => perId.get(id) ?? new Error(`utente ${id} assente`))
    }),
  }
}
```

```
LE QUATTRO REGOLE DEL DATALOADER
  1. UNA ISTANZA PER RICHIESTA, creata nella context factory. Un
     singleton condiviso serve a un utente i dati cachati per un
     altro, e la cache non scade mai.
  2. L'ORDINE DELL'ARRAY DI RITORNO È IL CONTRATTO (sopra).
  3. GLI ELEMENTI MANCANTI sono un `Error` in quella posizione, non
     un `null` silenzioso.
  4. IL BATCH VA LIMITATO: `maxBatchSize`, o una query con
     diecimila id in un `IN` blocca il database.

➜ RISULTATO: due query invece di undici, e la seconda è una sola
  anche con mille post.
```

⚠ DataLoader risolve il caso "molte chiavi, una tabella". Non risolve la lista annidata con argomenti diversi per elemento — `commenti(primi: 3)` su venti post sono venti query diverse. Lì serve una query sola con `ROW_NUMBER()` o `LATERAL`, oppure si accetta il costo e lo si limita nello schema.

---

# Parte B — Comprensione Profonda

---

## B1. Il null che si propaga verso l'alto

```
LA REGOLA DELLA SPECIFICA: se il resolver di un campo NON-NULL
restituisce null o solleva un errore, GraphQL non può metterci null.
Allora annulla il campo GENITORE. Se anche quello è non-null,
risale ancora. Fino a `data: null` se serve.

  type Post { autore: Utente! }        ← non-null
  type Query { post: [Post!]! }        ← non-null, e gli elementi pure

  Se UN autore su venti non si risolve:
    · Post.autore non può essere null
    · quel Post non può essere null (è [Post!])
    · la lista non può essere null (è [Post!]!)
    · ➜ `data.post` diventa null. VENTI POST SPARISCONO PER UNO.
```

```graphql
# ❌ Il campo dipende da un servizio esterno, ed è dichiarato non-null
type Post {
  titolo: String!
  raccomandati: [Post!]!   # chiama un servizio di raccomandazione
}

# ✅ Ciò che può fallire è nullable, e la lista al peggio è vuota
type Post {
  titolo: String!
  raccomandati: [Post!]    # null significa "non disponibile ora"
}
```

```
COME SI DECIDE, IN UNA DOMANDA SOLA
  "se questo campo fallisce, ha senso restituire il resto?"
    sì  ► nullable
    no  ► non-null

  L'id di un post: se non c'è, il post non ha senso ► `ID!`
  Le raccomandazioni: la pagina funziona senza ► nullable
  Il numero di like da un servizio esterno: nullable
  Una lista che può essere vuota: `[X!]!` va benissimo — vuota non
    è null

⚠ QUESTO RENDE LO SCHEMA UNA DECISIONE DI AFFIDABILITÀ, non solo di
  forma. È la ragione per cui molti schemi maturi hanno meno `!` di
  quanti se ne aspetterebbe chi arriva da TypeScript.
```

---

## B2. Errori parziali, e l'union di errore

```
GRAPHQL RISPONDE 200 ANCHE QUANDO QUALCOSA È ANDATO STORTO. Il
codice HTTP dice se il TRASPORTO ha funzionato, non se la query è
riuscita — e un client che controlla solo `response.ok` non vede
mai un errore.

{
  "data": { "utente": { "nome": "Ada", "post": null } },
  "errors": [{
    "message": "Non autorizzato",
    "path": ["utente", "post"],
    "extensions": { "code": "FORBIDDEN" }
  }]
}

➜ `data` E `errors` CONVIVONO. Il client deve guardare entrambi, e
  `path` gli dice esattamente quale campo manca.
```

```typescript
// Il formattatore centralizza due cose: il codice stabile che il
// client può leggere, e ciò che NON deve uscire.
export function formattaErrore(errore: GraphQLFormattedError, originale: unknown) {
  const codice = errore.extensions?.['code'] ?? 'INTERNAL_SERVER_ERROR'

  // ⚠ IN PRODUZIONE LO STACK NON ESCE MAI. Nemmeno il messaggio
  //   originale di un errore inatteso: contiene nomi di tabelle,
  //   query, percorsi di file.
  if (codice === 'INTERNAL_SERVER_ERROR') {
    const riferimento = registraEIdentifica(originale) // nei log, con l'id
    return { message: 'Errore interno', extensions: { code: codice, riferimento } }
  }

  return { message: errore.message, path: errore.path, extensions: { code: codice } }
}
```

```graphql
# L'UNION DI ERRORE: gli errori PREVISTI diventano parte dello
# schema invece di finire in `errors`. Il client li gestisce con
# `__typename`, e il compilatore lo obbliga a coprirli tutti.
union RisultatoAccesso = AccessoRiuscito | CredenzialiErrate | AccountBloccato

type CredenzialiErrate { messaggio: String! }
type AccountBloccato { messaggio: String!, sbloccoIl: DateTime! }

type Mutation {
  accedi(email: String!, password: String!): RisultatoAccesso!
}
```

⚠ L'union di errore vale per ciò che *fa parte del dominio* — credenziali sbagliate, quota esaurita, conflitto di versione. Un guasto del database resta in `errors`: non è un esito previsto, e metterlo nello schema costringe ogni client a gestirlo come se lo fosse.

---

## B3. Autorizzare al campo, non alla rotta

```
IN REST L'AUTORIZZAZIONE STA SULLA ROTTA: `GET /utenti/42` passa o
non passa. In GraphQL non ci sono rotte — c'è una query che tocca
venti campi di sei tipi, e ognuno ha regole diverse.

  query {
    utente(id: "42") {
      nome        ← pubblico
      email       ← solo il proprietario
      stipendio   ← solo HR
      post {
        bozza     ← solo l'autore
      }
    }
  }

➜ L'UNICO POSTO DOVE L'AUTORIZZAZIONE È CORRETTA È IL RESOLVER DEL
  CAMPO. Metterla nella query di primo livello lascia scoperti tutti
  i percorsi che arrivano allo stesso tipo da un'altra direzione.
```

```typescript
// Il pattern che rende difficile dimenticarsene: un involucro che
// si applica al resolver, non un `if` che qualcuno deve ricordare
export function conPermesso<P, A, R>(
  puo: (padre: P, ctx: Contesto) => boolean | Promise<boolean>,
  risolutore: Risolutore<P, A, R>,
): Risolutore<P, A, R | null> {
  return async (padre, argomenti, ctx, info) =>
    (await puo(padre, ctx)) ? risolutore(padre, argomenti, ctx, info) : null
}

export const risolutoriUtente = {
  Utente: {
    email: conPermesso((u, ctx) => ctx.utente?.id === u.id, (u) => u.email),
    stipendio: conPermesso((_, ctx) => ctx.utente?.ruolo === 'hr', (u) => u.stipendio),
  },
}
```

```
⚠ TRE ERRORI CHE SI VEDONO OVUNQUE

  1. AUTORIZZARE SOLO ALLA RADICE. `Query.utente` protetto, ma
     `Post.autore` restituisce lo stesso tipo e nessuno lo guarda:
     si arriva ai dati dalla porta di servizio.
  2. SOLLEVARE UN ERRORE SU UN CAMPO NON-NULL. Il null risale (§B1)
     e cancella l'intera risposta invece di nascondere un campo.
     ➜ i campi soggetti a permesso vanno NULLABLE.
  3. DISTINGUERE "non esiste" DA "non è tuo". Due messaggi diversi
     permettono di enumerare le risorse: la risposta dev'essere la
     stessa (tutorial_13 §B7).
```

⚠ L'introspection va spenta in produzione — è quella che permette a chiunque di scaricare l'intero schema con una query — e insieme vanno spenti i *field suggestions*, il "did you mean `stipendio`?" che il motore aggiunge agli errori di validazione: da solo ricostruisce lo schema campo per campo.

---

## B4. GraphQL espone un linguaggio

```
LA DIFFERENZA CHE CAMBIA TUTTO: in REST il costo di `GET /post` lo
decidi tu. In GraphQL il costo lo decide CHI SCRIVE LA QUERY, e le
query possibili sono infinite.

  query {
    post(primi: 100) {
      commenti(primi: 100) {
        autore { post(primi: 100) { commenti(primi: 100) { … } } }
      }
    }
  }

  Una query di quindici righe, cento milioni di righe lette.
  Nessuna riga di codice è sbagliata: è lo schema che lo permette.
```

```typescript
// ① PROFONDITÀ — la prima difesa, e la più economica: si applica
//    prima di eseguire qualunque resolver
import depthLimit from 'graphql-depth-limit'

// ② COMPLESSITÀ — un costo per campo, sommato prima dell'esecuzione.
//    Il moltiplicatore di lista è la parte che conta: una lista di
//    100 elementi costa 100 volte i suoi figli.
import { getComplexity, simpleEstimator, fieldExtensionsEstimator } from 'graphql-query-complexity'

export const pluginComplessita = {
  async requestDidStart() {
    return {
      async didResolveOperation({ request, document, schema }) {
        const costo = getComplexity({
          schema,
          query: document,
          variables: request.variables,
          estimators: [fieldExtensionsEstimator(), simpleEstimator({ defaultComplexity: 1 })],
        })
        if (costo > 1000) {
          throw new GraphQLError(`Query troppo costosa: ${costo}, massimo 1000`, {
            extensions: { code: 'QUERY_TOO_COMPLEX', costo },
          })
        }
      },
    }
  },
}
```

```graphql
# Il costo si dichiara NELLO SCHEMA, accanto al campo: è l'unico
# posto dove non si dimentica quando il campo cambia.
type Query {
  post(primi: Int = 20): [Post!]!
    @complexity(moltiplicatore: "primi", valore: 2)
  generaReport(intervallo: Intervallo!): Report!
    @complexity(valore: 500)   # un job pesante
}
```

```
LE QUATTRO DIFESE, IN ORDINE DI COSTO CRESCENTE
  1. PROFONDITÀ MASSIMA (7-10): costa nulla, ferma la ricorsione
  2. COMPLESSITÀ MASSIMA: ferma le liste larghe e i campi costosi
  3. TETTO SUGLI ARGOMENTI DI LISTA: `primi` con un massimo, sempre.
     Senza, `primi: 100000` passa la complessità se il peso è basso.
  4. PERSISTED QUERIES: il client manda un hash, e il server esegue
     solo le query dell'elenco. È l'unica difesa COMPLETA — nessuna
     query arbitraria arriva mai — e va bene quando i client sono
     tuoi. Con un'API pubblica non è praticabile.

⚠ IL TIMEOUT PER RICHIESTA VA COMUNQUE MESSO: la complessità è una
  stima statica, e una query da costo 50 può fare una scansione di
  tabella se manca un indice.
```

---

## B5. Alias e batching: gli attacchi che aggirano il limite

```
IL RATE LIMITING DEL TUTORIAL 22 CONTA LE RICHIESTE HTTP. GraphQL
ha due modi di fare molte operazioni in UNA richiesta HTTP, e li
consente per progetto.

① ALIAS — lo stesso campo N volte, in una query PIATTA

   mutation {
     t1: accedi(email: "a@b.it", password: "aaa") { token }
     t2: accedi(email: "a@b.it", password: "bbb") { token }
     …
     t500: accedi(email: "a@b.it", password: "zzz") { token }
   }

   ➜ profondità 1: il depth limit non lo vede. Costo per campo
     basso: la complessità può non vederlo. UNA richiesta HTTP:
     il rate limiter non lo vede.

② ARRAY BATCHING — più operazioni in un array JSON

   [ {"query": "…"}, {"query": "…"}, … ]

   ➜ stesso effetto, per la stessa ragione.
```

```typescript
// LE TRE DIFESE, e servono tutte e tre
export const server = new ApolloServer({
  schema,
  // ① Il batching HTTP si spegne se non serve davvero
  allowBatchedHttpRequests: false,
  plugins: [
    {
      async requestDidStart() {
        return {
          // ② Il limite si conta per OPERAZIONE, non per richiesta:
          //    è il gancio che il tutorial 22 non poteva avere
          async didResolveOperation({ document, contextValue }) {
            const quante = contaCampiRadice(document)
            if (quante > 10) {
              throw new GraphQLError('Troppe operazioni in una query')
            }
            await limitatore.consuma(contextValue.chiave, quante)
          },
        }
      },
    },
  ],
})
```

```
③ E GLI ALIAS DEVONO COSTARE. Un estimatore che conta il campo una
  volta sola per nome è cieco agli alias: il conteggio va fatto
  sulle SELEZIONI dell'AST, non sui nomi di campo distinti. Le
  librerie serie lo fanno; vale la pena verificarlo con una query
  di prova invece di fidarsi.

⚠ SUI CAMPI SENSIBILI — accesso, invio di codici, reimpostazione
  password — il limite non basta comunque: quelle mutation vanno
  contate anche per EMAIL TENTATA, esattamente come in REST
  (tutorial_22 §A5). Un attaccante che manda cinque tentativi per
  richiesta da mille IP resta sotto ogni soglia per richiesta.
```

---

## B6. Paginazione: cursore contro offset

```
IL PROBLEMA DELL'OFFSET, con un esempio

  pagina 1: LIMIT 20 OFFSET 0   → post 1-20
  … nel frattempo qualcuno pubblica un post nuovo, che va in cima …
  pagina 2: LIMIT 20 OFFSET 20  → il post che era 20° è ora 21°,
                                  e viene mostrato DUE VOLTE

  E al contrario, se un post viene cancellato, uno sparisce senza
  essere mai stato mostrato.

➜ IL CURSORE non è una posizione, è un SEGNAPOSTO: "dammi quelli
  dopo questo". Inserimenti e cancellazioni non lo spostano.
```

```graphql
# La forma Relay: verbosa, e standard. Vale la pena adottarla anche
# senza Relay, perché tutti gli strumenti la riconoscono.
type PostConnection {
  edges: [PostEdge!]!
  pageInfo: PageInfo!
  totalCount: Int      # nullable: su tabelle grandi il COUNT è caro
}

type PostEdge {
  node: Post!
  cursor: String!      # opaco: il client non lo interpreta
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}
```

```typescript
export async function risolviPost(
  _padre: unknown,
  argomenti: { primi?: number; dopo?: string },
  ctx: Contesto,
): Promise<PostConnection> {
  // ⚠ IL TETTO NON È FACOLTATIVO (§B4): senza, `primi: 1000000`
  const quanti = Math.min(argomenti.primi ?? 20, 100)
  const cursore = argomenti.dopo ? decodificaCursore(argomenti.dopo) : undefined

  // Si chiede UNO IN PIÙ: la sua presenza è `hasNextPage`, senza
  // bisogno di un COUNT
  const righe = await ctx.db.post.findMany({
    take: quanti + 1,
    ...(cursore && { cursor: { id: cursore }, skip: 1 }),
    orderBy: [{ creatoIl: 'desc' }, { id: 'desc' }],
  })

  const altre = righe.length > quanti
  const edges = righe.slice(0, quanti).map((p) => ({ node: p, cursor: codificaCursore(p.id) }))

  return {
    edges,
    pageInfo: {
      hasNextPage: altre,
      hasPreviousPage: Boolean(argomenti.dopo),
      startCursor: edges[0]?.cursor ?? null,
      endCursor: edges.at(-1)?.cursor ?? null,
    },
  }
}
```

```
⚠ TRE DETTAGLI CHE FANNO LA DIFFERENZA

  1. L'ORDINAMENTO DEVE ESSERE TOTALE. `ORDER BY creatoIl DESC` con
     due post allo stesso istante salta o ripete righe: serve un
     secondo criterio univoco, e l'id va benissimo.
  2. IL CURSORE È OPACO, e va trattato come tale: base64 di un
     valore interno. Se il client lo interpreta, non puoi più
     cambiare l'ordinamento senza rompere i suoi segnalibri.
  3. `totalCount` NULLABLE, e calcolato solo se richiesto: un COUNT
     su dieci milioni di righe costa più di tutta la pagina.

➜ L'OFFSET RESTA GIUSTO in un caso: quando serve "vai a pagina 7",
  cioè in una tabella amministrativa su dati che non cambiano sotto
  le dita. Il cursore non sa saltare a una pagina arbitraria.
```

---

## B7. La cache, che non è quella di HTTP

```
COSA SI PERDE PASSANDO A GRAPHQL

  · TUTTO È POST /graphql ► la CDN non può cachare per URL
  · il corpo cambia a ogni query ► `ETag` e `Last-Modified` non
    hanno più un significato utile
  · una risposta contiene dati con freschezze diverse — il profilo
    cambia ogni mese, il contatore ogni secondo — e `Cache-Control`
    ne esprime una sola

➜ LA CACHE SI SPOSTA IN DUE POSTI: il CLIENT, normalizzata per
  entità, e il SERVER, per campo.
```

```typescript
// LA CACHE NORMALIZZATA DEL CLIENT: gli oggetti si conservano per
// IDENTITÀ, non per query. Lo stesso utente letto da tre query
// diverse è UNA voce, e un aggiornamento le aggiorna tutte.
const cache = new InMemoryCache({
  typePolicies: {
    // ⚠ SENZA `id` E `__typename` NELLA SELEZIONE, Apollo non può
    //   normalizzare e conserva l'oggetto dentro la query: due
    //   copie che divergono, ed è il bug "ho aggiornato il nome e
    //   una parte della pagina mostra ancora il vecchio".
    Utente: { keyFields: ['id'] },
    Query: {
      fields: {
        post: {
          // Le pagine successive si FONDONO invece di sostituirsi
          keyArgs: ['filtro'],
          merge: (esistenti = { edges: [] }, entranti) => ({
            ...entranti,
            edges: [...esistenti.edges, ...entranti.edges],
          }),
        },
      },
    },
  },
})
```

```
E SUL SERVER, la cache per campo: si dichiara nello schema, e il
motore calcola il TTL della risposta come il MINIMO fra quelli dei
campi selezionati.

  type Post @cacheControl(maxAge: 300) {
    titolo: String!
    visualizzazioni: Int! @cacheControl(maxAge: 5)
  }

  ➜ una query che chiede solo il titolo è cachabile 300 secondi;
    una che chiede anche le visualizzazioni, 5.

⚠ `scope: PRIVATE` SU TUTTO CIÒ CHE DIPENDE DALL'UTENTE, sempre.
  Un solo campo personalizzato marcato pubblico finisce nella cache
  condivisa, e viene servito a un altro utente — è lo stesso
  incidente del tutorial 22 §B8, con una superficie più grande
  perché qui i campi si combinano in modi imprevisti.
```

Le **persisted queries** riportano indietro una parte di ciò che si è perso: se la query è un hash e arriva in GET, la CDN torna a poter cachare per URL. È il motivo per cui vale la pena adottarle anche solo per le query pubbliche.

---

## B8. Subscription: cosa cambia

```
UNA SUBSCRIPTION È UN WEBSOCKET (tutorial_23) con un protocollo
sopra: `graphql-transport-ws`. Tutto ciò che vale lì vale qui —
handshake, heartbeat, backpressure, scaling con pub/sub — più
qualcosa di specifico.
```

```typescript
export const risolutoriSubscription = {
  Subscription: {
    postPubblicato: {
      // `subscribe` restituisce un AsyncIterator; `resolve` dà
      // forma a ogni evento
      subscribe: (_p, { canale }: { canale: string }, ctx: Contesto) => {
        // ⚠ L'AUTORIZZAZIONE VA QUI, all'iscrizione, e va
        //   RIVERIFICATA se l'evento porta dati sensibili: una
        //   subscription dura ore, e i permessi cambiano (§23.B3)
        if (!ctx.puoLeggere(canale)) throw new GraphQLError('Non autorizzato')
        return ctx.pubsub.asyncIterator([`POST:${canale}`])
      },
      resolve: (evento: { postId: string }, _a, ctx: Contesto) =>
        ctx.loader.postPerId.load(evento.postId),
    },
  },
}
```

```
⚠ QUATTRO COSE CHE VANNO SAPUTE PRIMA DI USARLE

  1. IL TOKEN VA NEL `connectionParams`, non nell'URL: il protocollo
     ha un messaggio di inizializzazione apposta, e così non finisce
     nei log (§23.B2).
  2. L'EVENTO PORTA UN ID, NON L'OGGETTO. Pubblicare l'oggetto
     intero significa che chi si è iscritto riceve campi che non
     può vedere: il `resolve` lo rilegge, e i permessi si applicano.
  3. IL PUB/SUB IN MEMORIA È PER UN PROCESSO SOLO. Con più istanze
     serve Redis, con lo stesso limite di consegna del §23.B7.
  4. IL COSTO È UNA CONNESSIONE APERTA PER CLIENT. Per un
     aggiornamento ogni pochi secondi il polling costa meno di
     tutto questo, e non ha nessuno dei suoi problemi.
```

---

## B9. Federation: quando un solo schema non basta

```
IL PROBLEMA ORGANIZZATIVO, non tecnico: quattro squadre su uno
schema solo. Ogni modifica tocca lo stesso repository, ogni rilascio
aspetta gli altri, e il file dei resolver è di ventimila righe.

  FEDERATION: ogni squadra possiede un SUBGRAPH — schema, resolver,
  rilasci propri — e un ROUTER li compone in un SUPERGRAPH che il
  client vede come un grafo solo.

   client ──► router ──┬──► subgraph utenti     (squadra A)
                       ├──► subgraph catalogo   (squadra B)
                       └──► subgraph ordini     (squadra C)
```

```graphql
# subgraph utenti — possiede il tipo
type Utente @key(fields: "id") {
  id: ID!
  nome: String!
  email: String
}

# subgraph ordini — ESTENDE lo stesso tipo senza conoscerne i campi
type Utente @key(fields: "id") {
  id: ID!
  ordini(primi: Int = 10): [Ordine!]!   # aggiunto qui
}
```

```typescript
// Il reference resolver: il router passa la chiave, il subgraph
// restituisce l'entità. È il punto di giunzione fra i grafi.
export const risolutoriRiferimento = {
  Utente: {
    __resolveReference: (riferimento: { id: string }, ctx: Contesto) =>
      ctx.loader.utentePerId.load(riferimento.id),
  },
}
```

```
⚠ IL COSTO, che va valutato prima di adottarla

  · UN N+1 FRA SERVIZI: il router risolve venti riferimenti con una
    chiamata `_entities` al subgraph, ma quel subgraph deve avere
    il suo DataLoader — altrimenti l'N+1 si sposta di un livello e
    diventa più difficile da vedere
  · UNA LATENZA CHE SI SOMMA: il piano di esecuzione può avere
    passi sequenziali, e il p99 è la somma dei p99
  · UN COMPONENTE IN PIÙ da gestire, versionare e monitorare
  · LA COMPOSIZIONE PUÒ FALLIRE al rilascio: due subgraph che
    definiscono lo stesso campo in modo incompatibile bloccano
    TUTTI, ed è la ragione per cui serve un controllo in CI

➜ NON SERVE CON UNA SQUADRA SOLA. Con una, la Federation aggiunge
  un router e toglie niente: lo schema modulare in un repository
  solo fa lo stesso lavoro senza il costo.
```

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — L'API che fa mille query

**Obiettivo:** una query da quindici righe genera 1.847 query al database. Trovare le tre cause.

```typescript
// I resolver, in produzione da tre mesi
export const risolutori = {
  Query: {
    post: (_p, { primi }: { primi: number }) => db.post.findMany({ take: primi }),
  },
  Post: {
    autore: (post: Post) => db.utente.findUnique({ where: { id: post.autoreId } }),
    commenti: (post: Post) => db.commento.findMany({ where: { postId: post.id } }),
    numeroLike: (post: Post) => db.like.count({ where: { postId: post.id } }),
  },
  Commento: {
    autore: (c: Commento) => db.utente.findUnique({ where: { id: c.autoreId } }),
  },
}
```

```
LA DIAGNOSI — tre cause che si moltiplicano
 1. NESSUN DATALOADER: ogni resolver di campo fa la sua query, una
    per elemento del genitore (§A5). Con 100 post e 5 commenti
    ciascuno: 1 + 100 + 100 + 100 + 500 + 500 = 1.301 query.
 2. GLI STESSI AUTORI LETTI DECINE DI VOLTE: dieci post dello
    stesso autore sono dieci `findUnique` identiche, e nemmeno il
    database le riconosce come tali.
 3. `primi` SENZA TETTO: `post(primi: 10000)` è accettato, e i
    numeri sopra si moltiplicano per cento (§B4, §B6).
```

```typescript
// LA SOLUZIONE — un loader per relazione, creato per richiesta
export function creaLoader(db: PrismaClient) {
  return {
    utentePerId: new DataLoader<string, Utente | Error>(async (ids) => {
      const righe = await db.utente.findMany({ where: { id: { in: [...ids] } } })
      const perId = new Map(righe.map((u) => [u.id, u]))
      return ids.map((id) => perId.get(id) ?? new Error(`utente ${id} assente`))
    }, { maxBatchSize: 500 }),

    // Le relazioni "molti" raggruppano invece di mappare
    commentiPerPost: new DataLoader<string, Commento[]>(async (postIds) => {
      const righe = await db.commento.findMany({ where: { postId: { in: [...postIds] } } })
      const perPost = new Map<string, Commento[]>()
      for (const c of righe) perPost.set(c.postId, [...(perPost.get(c.postId) ?? []), c])
      return postIds.map((id) => perPost.get(id) ?? [])
    }),

    // Anche i conteggi si accorpano: un GROUP BY invece di N COUNT
    likePerPost: new DataLoader<string, number>(async (postIds) => {
      const gruppi = await db.like.groupBy({
        by: ['postId'],
        where: { postId: { in: [...postIds] } },
        _count: true,
      })
      const perPost = new Map(gruppi.map((g) => [g.postId, g._count]))
      return postIds.map((id) => perPost.get(id) ?? 0)
    }),
  }
}

export const risolutoriCorretti = {
  Query: {
    // 3. Il tetto, sempre
    post: (_p, { primi }: { primi: number }, ctx: Contesto) =>
      ctx.db.post.findMany({ take: Math.min(primi ?? 20, 100) }),
  },
  Post: {
    autore: (p: Post, _a, ctx: Contesto) => ctx.loader.utentePerId.load(p.autoreId),
    commenti: (p: Post, _a, ctx: Contesto) => ctx.loader.commentiPerPost.load(p.id),
    numeroLike: (p: Post, _a, ctx: Contesto) => ctx.loader.likePerPost.load(p.id),
  },
  Commento: {
    autore: (c: Commento, _a, ctx: Contesto) => ctx.loader.utentePerId.load(c.autoreId),
  },
}
```

```
# VERIFICA — si contano le query, non si stimano
# Con il logging di Prisma acceso, la stessa query di prima:
#   prima → 1.847 query
#   dopo  → 4 (post, utenti, commenti, like) più una per gli autori
#           dei commenti che non erano già in cache
# ⚠ E il loader va creato NELLA CONTEXT FACTORY: se è un singleton,
#   il test passa e in produzione un utente vede i dati di un altro.
```

---

### Esercizio 2 — La query che ha spento il database

**Obiettivo:** un incidente notturno. Il server GraphQL è quello predefinito. Trovare i quattro buchi.

```typescript
// La configurazione in produzione
export const server = new ApolloServer({
  typeDefs,
  resolvers,
})

// E la query che è arrivata alle 3:47
// mutation { a1: accedi(email:"admin@x.it", password:"…") { token }
//            a2: accedi(email:"admin@x.it", password:"…") { token }
//            … a800: … }
```

```
LA DIAGNOSI — quattro buchi, e nessuno richiede codice per essere
sfruttato
 1. NESSUN LIMITE DI PROFONDITÀ: una query ricorsiva a venti
    livelli è accettata (§B4)
 2. NESSUN LIMITE DI COMPLESSITÀ né tetto sugli argomenti di lista
 3. GLI ALIAS AGGIRANO IL RATE LIMITING: 800 tentativi di accesso
    in UNA richiesta HTTP, e il limitatore ne conta una (§B5)
 4. INTROSPECTION ATTIVA: chi ha scritto la query ha prima
    scaricato lo schema completo, campo per campo
```

```typescript
// LA SOLUZIONE — quattro difese, dalla più economica alla più cara
import depthLimit from 'graphql-depth-limit'

export const server = new ApolloServer({
  typeDefs,
  resolvers,

  // 4. Lo schema non si scarica, e il motore non suggerisce i nomi
  //    dei campi negli errori di validazione
  introspection: false,

  // 3. Il batching in array si spegne: non serve quasi mai
  allowBatchedHttpRequests: false,

  // 1. La profondità, prima di eseguire qualunque resolver
  validationRules: [depthLimit(8)],

  plugins: [
    pluginComplessita, // 2. il costo, con il moltiplicatore di lista
    {
      async requestDidStart() {
        return {
          async didResolveOperation({ document, contextValue }) {
            // 3. Il limite si conta sulle SELEZIONI, non sulle
            //    richieste HTTP: è ciò che rende visibili gli alias
            const operazioni = contaSelezioniRadice(document)
            if (operazioni > 10) throw new GraphQLError('Troppe operazioni')

            // E le mutation sensibili si contano anche per
            // argomento, non solo per chiamante (§B5)
            for (const tentativo of estraiAccessi(document, contextValue)) {
              await limitatorePerEmail.consuma(tentativo.email)
            }
            await limitatorePerChiave.consuma(contextValue.chiave, operazioni)
          },
        }
      },
    },
  ],
})
```

```
# VERIFICA — le quattro prove
# 1. una query annidata a 9 livelli → errore di validazione
# 2. `post(primi: 100000)` → rifiutata per complessità
# 3. la mutation con 800 alias → rifiutata al primo controllo, e le
#    prime 5 con la stessa email esauriscono il limite per email
# 4. una query di introspection → campo `__schema` sconosciuto
```

---

### Esercizio 3 — Il campo che cancella la risposta

**Obiettivo:** una pagina mostra "nessun dato" quando un solo utente su cinquanta non ha il permesso. Trovare le tre cause.

```graphql
# Lo schema
type Post {
  id: ID!
  titolo: String!
  autore: Utente!
  bozzaInterna: String!
}

type Query {
  post(primi: Int): [Post!]!
}
```

```typescript
// I resolver
export const risolutori = {
  Post: {
    bozzaInterna: (post: Post, _a, ctx: Contesto) => {
      if (ctx.utente?.id !== post.autoreId) {
        throw new GraphQLError('Non sei l’autore di questo post')
      }
      return post.bozzaInterna
    },
  },
}
```

```
LA DIAGNOSI — tre cause, e la prima è nello SCHEMA
 1. `bozzaInterna: String!` È NON-NULL. L'errore non può diventare
    null lì, quindi annulla il Post; il Post è `[Post!]`, quindi
    annulla la lista; la lista è `!`, quindi `data.post` è null.
    UN PERMESSO MANCANTE CANCELLA CINQUANTA POST (§B1).
 2. L'AUTORIZZAZIONE SOLLEVA invece di nascondere: su un campo
    soggetto a permesso la risposta giusta è null (§B3).
 3. IL MESSAGGIO DISTINGUE i casi e cita il campo: dice a chi sonda
    l'API che quel campo esiste ed è dell'autore.
```

```graphql
# LA SOLUZIONE — parte dallo schema, non dai resolver
type Post {
  id: ID!
  titolo: String!
  autore: Utente!
  # 1. Nullable: null significa "non visibile", ed è un esito
  #    previsto, non un guasto
  bozzaInterna: String
}
```

```typescript
// 2. e 3. L'involucro del §B3: restituisce null, non sceglie il
//    messaggio, e non c'è modo di dimenticarsene scrivendo un
//    resolver nuovo
export const risolutoriCorretti = {
  Post: {
    bozzaInterna: conPermesso(
      (post: Post, ctx: Contesto) => ctx.utente?.id === post.autoreId,
      (post: Post) => post.bozzaInterna,
    ),
  },
}
```

```
# VERIFICA — con un utente che possiede 1 post su 50
# prima: `data.post` è null, la pagina è vuota
# dopo:  50 post, `bozzaInterna` valorizzato su uno e null sugli
#        altri 49, e nessuna voce in `errors`
# ⚠ E il test va scritto con DUE utenti: con uno solo, il caso che
#   rompe non si presenta mai.
```

---

## C2. Mini-progetto: l'API del portale in GraphQL

**Obiettivo:** l'API del portale aziendale del corso, con le difese che questo tutorial ha reso obbligatorie.

```
IL PROGETTO — cosa deve avere

  1. SCHEMA
     · `!` solo su ciò che è strutturalmente sempre presente (§B1)
     · union di errore sulle mutation con esiti previsti (§B2)
     · connection Relay su ogni lista, con tetto su `primi` (§B6)
  2. CONTESTO
     · utente dalla sessione, DataLoader creati QUI (§A5)
     · una chiave di limite per richiesta (§B5)
  3. DIFESE
     · profondità 8 · complessità 1000 · batch HTTP spento
     · introspection e field suggestions spenti in produzione
     · limite per operazione, e per email sulle mutation di accesso
  4. AUTORIZZAZIONE
     · `conPermesso` sui campi, mai solo sulla radice (§B3)
     · campi soggetti a permesso NULLABLE
  5. OSSERVABILITÀ
     · durata e conteggio per CAMPO, non per endpoint (§D3)
     · il costo calcolato registrato su ogni richiesta
```

```typescript
// server.ts — l'ossatura
export const contesto = async ({ req }: { req: Request }): Promise<Contesto> => {
  const utente = await utenteDaSessione(req)
  return {
    utente,
    db: prisma,
    // ⚠ NUOVI A OGNI RICHIESTA: è la regola 1 del §A5
    loader: creaLoader(prisma),
    chiave: utente ? `utente:${utente.id}` : `ip:${ipAffidabile(req)}`,
    puoLeggere: (canale: string) => verificaCanale(utente, canale),
  }
}

export const server = new ApolloServer<Contesto>({
  schema: applicaDirettive(makeExecutableSchema({ typeDefs, resolvers })),
  introspection: process.env['NODE_ENV'] !== 'production',
  allowBatchedHttpRequests: false,
  validationRules: [depthLimit(8)],
  formatError: formattaErrore,
  plugins: [pluginComplessita, pluginLimite, pluginMetricheCampo],
})
```

```graphql
# schema.graphql — la mutation con union di errore e il tetto
type Mutation {
  creaPost(input: CreaPostInput!): CreaPostRisultato!
}

union CreaPostRisultato = PostCreato | ErroreValidazione | QuotaEsaurita

type PostCreato { post: Post! }
type ErroreValidazione { campi: [ErroreCampo!]! }
type QuotaEsaurita { limite: Int!, ripristinoIl: DateTime! }

type Query {
  post(primi: Int = 20, dopo: String, filtro: FiltroPost): PostConnection!
}
```

```
# ESTENSIONI, in ordine di utilità
# 1. Le persisted queries (§B4): tolgono le query arbitrarie e
#    riportano la cache di CDN
# 2. Il codegen (§D2) su schema e operazioni, con il controllo in CI
#    che rompe la build quando lo schema cambia in modo incompatibile
# 3. Le subscription (§B8) solo se serve davvero il tempo reale:
#    per un aggiornamento ogni pochi secondi il polling costa meno
```

---

# Parte D — Approfondimento per Esperti

---

## D1. Testare uno schema

```
TRE LIVELLI, E COPRONO COSE DIVERSE

  SCHEMA      lo schema compone? I tipi referenziati esistono? Non
              ci sono modifiche incompatibili rispetto alla versione
              in produzione? Costa millisecondi, e va in CI.
  RESOLVER    la funzione da sola, con un contesto finto. È dove si
              testa l'autorizzazione: due utenti, non uno.
  OPERAZIONE  la query completa contro il server, con un database
              vero (Testcontainers, tutorial_15 §D2). È l'unico
              livello che vede la propagazione del null (§B1).
```

```typescript
import { describe, it, expect } from 'vitest'
import { ApolloServer } from '@apollo/server'

describe('bozzaInterna', () => {
  it('è null per chi non è l’autore, e non cancella la lista', async () => {
    const server = new ApolloServer({ schema })
    const risposta = await server.executeOperation(
      { query: 'query { post(primi: 50) { id bozzaInterna } }' },
      { contextValue: contestoFinto({ utenteId: 'altro' }) },
    )

    const corpo = risposta.body as { singleResult: { data: never; errors?: never[] } }
    // Il controllo che conta: la LISTA c'è ancora
    expect(corpo.singleResult.data.post).toHaveLength(50)
    expect(corpo.singleResult.data.post[0].bozzaInterna).toBeNull()
    expect(corpo.singleResult.errors).toBeUndefined()
  })
})
```

```
⚠ IL TEST CHE MANCA QUASI SEMPRE è il CONTROLLO DI COMPATIBILITÀ
  DELLO SCHEMA in CI: `rover subgraph check`, o un confronto con lo
  schema in produzione. Rimuovere un campo, renderlo non-null, o
  restringere un enum rompe i client già rilasciati — e in GraphQL
  non c'è un `/v2` dove nasconderlo. Il ciclo corretto è
  DEPRECARE (`@deprecated(reason: …)`), misurare che nessuno lo usa
  più (§D3), e solo allora rimuovere.
```

---

## D2. Codegen: i tipi che non si scrivono

```
IL PROBLEMA: lo schema è tipizzato, ma i resolver e il client sono
codice normale. Un campo rinominato nello schema non rompe niente
a compilazione — rompe a runtime, in produzione, sul campo che
nessuno usava nei test.

➜ IL CODEGEN GENERA I TIPI DALLO SCHEMA: i resolver diventano
  type-safe rispetto al contratto, e le query del client pure.
```

```yaml
# codegen.yml
schema: ./src/schema.graphql
documents: ./src/**/*.graphql   # le operazioni del client
generates:
  ./src/generato/resolver.ts:
    plugins: [typescript, typescript-resolvers]
    config:
      contextType: ../contesto#Contesto
      # ⚠ I MAPPER SONO LA PARTE CHE FA LA DIFFERENZA: dicono che il
      #   resolver di `Utente` restituisce la RIGA del database, non
      #   il tipo GraphQL. Senza, il codegen pretende che il resolver
      #   restituisca già i campi relazionali risolti — e si finisce
      #   per mettere `any` ovunque, perdendo tutto il vantaggio.
      mappers:
        Utente: '@prisma/client#Utente as UtenteDb'
        Post: '@prisma/client#Post as PostDb'
  ./src/generato/operazioni.ts:
    plugins: [typescript, typescript-operations, typed-document-node]
```

⚠ Il codice generato non va modificato a mano e non va letto come documentazione: va committato (così la build non dipende da un servizio esterno) e rigenerato in CI con un controllo che il risultato sia identico. Se differisce, qualcuno ha cambiato lo schema senza rigenerare.

---

## D3. Osservare per campo, non per endpoint

```
LE METRICHE PER ENDPOINT NON DICONO NIENTE: c'è un endpoint solo, e
la sua latenza media è la media di query che non hanno niente in
comune. Le metriche di GraphQL sono per OPERAZIONE e per CAMPO.

  durata per operationName ► richiede che le operazioni SIANO
      nominate: una query anonima è invisibile, e va rifiutata in
      produzione proprio per questo
  durata per campo ► dice QUALE resolver è lento, ed è l'unica
      metrica che porta direttamente alla riga da correggere
  conteggio per campo ► è ciò che permette di deprecare: si rimuove
      quando il contatore è a zero da un mese (§D1)
  costo calcolato ► la distribuzione dice se il limite del §B4 è
      tarato bene: se il p99 è a 40 su un tetto di 1000, il tetto
      non protegge da niente
  errori per `path` ► un campo che fallisce spesso è visibile solo
      così: la richiesta è comunque 200
```

```typescript
// Il plugin: `didResolveOperation` per l'operazione, `executionDidStart`
// per i campi
export const pluginMetricheCampo = {
  async requestDidStart() {
    return {
      async executionDidStart() {
        return {
          willResolveField({ info }) {
            const inizio = process.hrtime.bigint()
            return () => {
              const durataMs = Number(process.hrtime.bigint() - inizio) / 1e6
              // ⚠ L'etichetta è tipo.campo, MAI un valore di
              //   argomento: gli id come etichetta fanno esplodere
              //   la cardinalità della serie temporale
              metriche.osserva('graphql.campo.durata_ms', durataMs, {
                campo: `${info.parentType.name}.${info.fieldName}`,
              })
            }
          },
        }
      },
    }
  },
}
```

⚠ `willResolveField` viene chiamato per **ogni campo di ogni elemento**: su una lista di mille post sono migliaia di misurazioni per richiesta. In produzione si campiona — una richiesta su cento — oppure si misura solo dove c'è un resolver esplicito, saltando i campi risolti dal default.

---

## D4. Migrare da REST, e il BFF

```
LA MIGRAZIONE CHE FUNZIONA È INCREMENTALE, e non tocca il backend
per prima cosa.

  1. GraphQL DAVANTI a REST: i resolver chiamano gli endpoint che
     già esistono. Zero rischio sul backend, e il client guadagna
     subito la query unica.
  2. Si migrano al database diretto i campi dove l'HTTP interno
     costa (le liste, che sono quelle con l'N+1 peggiore).
  3. REST resta per ciò che GraphQL fa male: caricamento di file,
     webhook in entrata, integrazioni di terzi, e tutto ciò che deve
     essere cachabile da una CDN.

⚠ AL PASSO 1 L'N+1 DIVENTA UN N+1 DI CHIAMATE HTTP, che costa dieci
  volte quello sul database. Il DataLoader serve dal primo giorno,
  con un endpoint interno che accetta una lista di id — e se non
  esiste, va aggiunto prima di cominciare.
```

```
IL BFF (Backend For Frontend) È UN CASO A PARTE, ed è dove GraphQL
rende di più: uno strato per client — web, mobile, tv — che compone
i servizi interni e serve esattamente ciò che quello schermo mostra.

  ✅ lo schema è modellato sull'INTERFACCIA, non sul dominio: è la
     forma in cui GraphQL è più naturale
  ✅ i client sono tuoi, quindi le persisted queries (§B4) sono
     praticabili e tolgono la superficie di attacco
  ❌ un componente in più da gestire, e la tentazione di metterci
     logica di dominio che appartiene ai servizi
```

---

## D5. Quando NON serve GraphQL

```
GRAPHQL AGGIUNGE: uno schema da mantenere, un motore di esecuzione
in mezzo, il DataLoader dappertutto, la cache HTTP da sostituire,
quattro difese contro un linguaggio che hai esposto, e
un'osservabilità che non è quella che sai già leggere.

NON SERVE QUANDO
  ❌ un solo client, sviluppato dalla stessa squadra del server:
     l'endpoint che restituisce esattamente ciò che serve lo fa
     meglio, e senza schema
  ❌ l'API è pubblica e va cachata da una CDN: si perde il
     vantaggio più grande di HTTP per un guadagno di banda
  ❌ le operazioni sono comandi, non letture: "annulla l'ordine"
     non è un grafo, e una mutation che restituisce un booleano è
     un endpoint REST travestito
  ❌ i dati sono file o flussi: il caricamento in GraphQL è un
     ripiego, e il presigned URL resta la risposta giusta

SERVE DAVVERO QUANDO
  ✅ ci sono molti client con esigenze diverse, e ognuno vuole una
     forma diversa degli stessi dati
  ✅ i dati sono un grafo vero, e l'interfaccia lo attraversa in
     modi che cambiano spesso
  ✅ il collo di bottiglia è il numero di giri di rete, non la
     banda: è il caso mobile
  ✅ le squadre sono tante e il grafo va composto (§B9)
```

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
GRAPHQL — Mappa dei concetti

LO SCHEMA
├── è il contratto, e viene prima dei resolver
├── il `!` è una PROMESSA, non un vincolo di validazione: dove non
│     puoi mantenerla, il campo va nullable
├── interfacce e union hanno bisogno di `resolveType`
└── gli input sono tipi a parte: un tipo di output porta campi
      calcolati che in entrata non hanno senso

L'ESECUZIONE
├── un resolver per campo, con (padre, argomenti, contesto, info)
├── il default resolver legge la proprietà del genitore: si scrivono
│     solo i campi che non ci sono già
├── i campi di primo livello di una query vanno in PARALLELO, quelli
│     di una mutation in SEQUENZA
└── un campo si risolve UNA VOLTA PER ELEMENTO → N+1

DATALOADER
├── una istanza PER RICHIESTA, nella context factory, e l'ordine
│     dell'array di ritorno è il contratto
├── `maxBatchSize`, o un `IN` con diecimila id
└── non risolve le liste annidate con argomenti diversi per elemento

IL NULL
├── un errore su un campo non-null annulla il GENITORE, e risale
├── un campo soggetto a permesso va NULLABLE e restituisce null
└── la domanda è sempre: "se fallisce, ha senso restituire il resto?"

GLI ERRORI
├── 200 anche con `errors` pieno: il client guarda entrambi, e
│     `path` gli dice quale campo manca
├── union di errore per gli esiti PREVISTI, `errors` per i guasti
└── in produzione niente stack, niente messaggi interni

LA SUPERFICIE
├── il client scrive la query: il costo non è più tuo
├── profondità · complessità · tetto sugli argomenti di lista ·
│     persisted queries — in quest'ordine di costo
├── gli ALIAS e il BATCH aggirano il rate limiting per richiesta:
│     si conta per OPERAZIONE, e per argomento sui campi sensibili
├── introspection e field suggestions spenti in produzione
└── un timeout comunque: la complessità è una stima statica

I DATI
├── cursore, non offset: l'offset salta e ripete sotto scrittura
├── l'ordinamento dev'essere TOTALE, e il cursore opaco
├── la cache HTTP non c'è più: normalizzata sul client (serve `id` e
│     `__typename`), per campo sul server, e `PRIVATE` su tutto ciò
│     che dipende dall'utente
└── subscription = WebSocket + protocollo: vale il tutorial_23, più
      l'evento che porta un id e non l'oggetto

ORGANIZZAZIONE
├── Federation serve a molte SQUADRE, non a molti servizi
├── il codegen con i mapper, e il controllo in CI che lo schema non
│     rompa i client
└── metriche per operazione e per campo: l'endpoint è uno solo
```

---

## Checklist di competenze

**Parte A — Basi**

- [ ] Sai spiegare over-fetching e under-fetching, e quale dei due costa di più
- [ ] Scrivi uno schema in SDL e sai cosa promette ogni `!`
- [ ] Distingui interface, union e input, sai quando serve
      `resolveType`, e perché i campi di una mutation vanno in
      sequenza e quelli di una query no
- [ ] Sai cosa riceve un resolver nei suoi quattro argomenti
- [ ] Sai perché un default resolver esiste e quando va sostituito
- [ ] Riconosci un N+1 leggendo i resolver, e scrivi un DataLoader
      che rispetta l'ordine e vive una richiesta sola

**Parte B — Comprensione**

- [ ] Sai come il null si propaga e quanto può cancellare
- [ ] Decidi nullable o non-null con la domanda dell'affidabilità
- [ ] Sai perché una risposta è 200 anche con errori, e usi l'union
      di errore per gli esiti previsti
- [ ] Autorizzi al campo restituendo null, e sai perché farlo solo
      alla radice lascia una porta di servizio
- [ ] Configuri profondità, complessità e tetto sugli argomenti
- [ ] Sai perché alias e batching aggirano il rate limiting per richiesta
- [ ] Implementi una connection a cursore con ordinamento totale
- [ ] Sai perché la cache HTTP non funziona, cosa la sostituisce, e
      cosa serve perché quella del client normalizzi
- [ ] Sai cosa cambia in una subscription rispetto a un WebSocket nudo
- [ ] Sai a quale problema risponde la Federation, e cosa costa

**Parte C — Pratica**

- [ ] Hai portato una query da 1.847 chiamate a poche
- [ ] Hai chiuso quattro buchi di un server con la configurazione predefinita
- [ ] Hai impedito a un permesso mancante di cancellare una risposta
- [ ] Hai costruito un'API con schema, difese, autorizzazione e metriche

**Parte D — Esperto**

- [ ] Testi ai tre livelli, con due utenti dove c'è un permesso, e
      hai un controllo di compatibilità dello schema in CI
- [ ] Generi i tipi dallo schema, con i mapper configurati
- [ ] Misuri per operazione e per campo, campionando
- [ ] Sai migrare da REST in modo incrementale, e cosa lasciare a REST
- [ ] Sai dire quando GraphQL non serve

---

## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| Nessun DataLoader | N+1 su ogni campo relazionale | Un loader per relazione, creato per richiesta |
| `!` su un campo che può fallire | Il null risale e cancella il genitore | Nullable su ciò che dipende da permessi o rete |
| Sollevare un errore per negare un permesso | Cancella la risposta invece del campo | Campo nullable che restituisce null |
| Autorizzare solo alla radice | Si arriva agli stessi dati da un altro percorso | Il permesso sul resolver del campo |
| Nessun limite di profondità o complessità | Una query di quindici righe legge cento milioni di righe | Profondità, complessità e tetto sugli argomenti |
| Rate limiting per richiesta HTTP | Alias e batch fanno 800 operazioni in una richiesta | Conteggio per operazione, e per argomento sui campi sensibili |
| Introspection attiva in produzione | Lo schema si scarica con una query | Spenta, insieme ai field suggestions |
| Paginazione a offset su dati che cambiano | Righe saltate e righe ripetute | Cursore, con ordinamento totale |
| `PUBLIC` su un campo personalizzato | La CDN serve i dati di un utente a un altro | `scope: PRIVATE` su tutto ciò che dipende dall'utente |
| Pubblicare l'oggetto in una subscription | Chi è iscritto riceve campi che non può vedere | Pubblicare l'id, e rileggere nel `resolve` |
| Stack trace negli errori | Nomi di tabelle e percorsi di file al client | Messaggio generico più un riferimento nei log |

---

## Troubleshooting rapido

**`data` è null e la pagina è vuota per un solo campo**
- Causa: errore su un campo non-null, e il null è risalito
- Fix: leggere `errors[].path` per trovarlo; rendere nullable ciò che può fallire

**`Cannot return null for non-nullable field`**
- Causa: il resolver restituisce null su un campo `!`
- Fix: correggere il resolver, o lo schema — la scelta è quella del §B1

**Il database fa migliaia di query per una richiesta**
- Causa: N+1, nessun DataLoader
- Fix: un loader per relazione, con il logging delle query acceso per contare

**Il client mostra dati vecchi dopo una mutation**
- Causa: la mutation non restituisce l'oggetto aggiornato, o manca `id`
- Fix: restituire l'entità con `id` e `__typename`; verificare le `typePolicies`

**La paginazione salta o ripete righe**
- Causa: offset su dati che cambiano, oppure ordinamento non totale
- Fix: cursore, e un secondo criterio univoco nell'`ORDER BY`

**Il rate limiting non ferma un attacco evidente**
- Causa: conteggio per richiesta HTTP, e l'attacco usa alias o batch
- Fix: contare le selezioni radice; limitare anche per argomento sulle mutation sensibili

**La build passa e in produzione un campo è `undefined`**
- Causa: schema cambiato senza rigenerare i tipi
- Fix: codegen in CI, con confronto del risultato; controllo di compatibilità dello schema

---

## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_25_nextjs.md` | GraphQL dentro un'applicazione App Router, e cosa cambia con i Server Component |
| `tutorial_23_websocket_security.md` | Il trasporto sotto le subscription, con tutte le sue trappole |
| `tutorial_12_database_web.md` | Le query che il DataLoader accorpa, e gli indici che le rendono veloci |
| `tutorial_11_api_design.md` | Le decisioni di contratto che valgono in REST e in GraphQL allo stesso modo |

---

## Risorse di riferimento

**Specifiche:** [GraphQL Specification](https://spec.graphql.org/), in particolare la sezione *Execution* per la propagazione del null · [GraphQL over HTTP](https://github.com/graphql/graphql-over-http), che standardizza ciò che ogni server faceva a modo suo · [Relay Cursor Connections](https://relay.dev/graphql/connections.htm)

**Documentazione:** [Apollo Server](https://www.apollographql.com/docs/apollo-server/) e [Apollo Client](https://www.apollographql.com/docs/react/), la cui pagina sulla cache normalizzata vale da sola la lettura · [GraphQL Yoga](https://the-guild.dev/graphql/yoga-server) · [DataLoader](https://github.com/graphql/dataloader) · [GraphQL Code Generator](https://the-guild.dev/graphql/codegen)

**Sicurezza:** [OWASP — GraphQL Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/GraphQL_Cheat_Sheet.html), la lista di controllo più completa in circolazione · [Apollo — Security best practices](https://www.apollographql.com/docs/apollo-server/security/authentication/)

---

> **Fine del Tutorial 24 — GraphQL**
>
> Prossimo tutorial: `tutorial_25_nextjs.md`
