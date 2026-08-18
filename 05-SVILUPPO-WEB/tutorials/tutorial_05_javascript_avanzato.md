# Tutorial 05 — JavaScript Avanzato: Dal Principiante all'Esperto

> **Companion a:** `05-javascript-avanzato.md`
> **Scope:** Callback e Promise, `async`/`await`, Fetch e `AbortController`, pattern asincroni (concorrenza limitata, retry con backoff, cancellazione), programmazione funzionale, `Proxy` e `Reflect`, decoratori, design pattern in JavaScript, Web Workers e `SharedArrayBuffer`, sistema dei moduli e interoperabilità ESM/CJS, strategie di gestione degli errori, performance e ottimizzazione per il JIT, testing con Vitest
> **Prerequisiti:** `tutorial_04_javascript_fondamenti.md` — closure, `this`, prototipi, event loop, generatori
> **Durata stimata:** 30-38 ore di studio + esercizi
> **Lingua:** Italiano — termini tecnici in inglese preservati
> **Stack:** ECMAScript 2024+ · browser evergreen · Node.js LTS · Vitest 2.x

---

## Indice Generale

- [Parte A — Basi Assolute](#parte-a--basi-assolute)
  - [A1. Il problema che l'asincronia risolve](#a1-il-problema-che-lasincronia-risolve)
  - [A2. Dai callback alle Promise](#a2-dai-callback-alle-promise)
  - [A3. `async` e `await`](#a3-async-e-await)
  - [A4. I combinatori di Promise](#a4-i-combinatori-di-promise)
  - [A5. Fetch: richieste HTTP fatte bene](#a5-fetch-richieste-http-fatte-bene)
  - [A6. Cancellare con `AbortController`](#a6-cancellare-con-abortcontroller)
- [Parte B — Comprensione Profonda](#parte-b--comprensione-profonda)
  - [B1. Pattern asincroni: concorrenza, retry, deduplicazione](#b1-pattern-asincroni-concorrenza-retry-deduplicazione)
  - [B2. Programmazione funzionale in JavaScript](#b2-programmazione-funzionale-in-javascript)
  - [B3. `Proxy` e `Reflect`](#b3-proxy-e-reflect)
  - [B4. Design pattern che valgono la pena](#b4-design-pattern-che-valgono-la-pena)
  - [B5. Web Workers](#b5-web-workers)
  - [B6. Il sistema dei moduli: ESM, CJS e interoperabilità](#b6-il-sistema-dei-moduli-esm-cjs-e-interoperabilità)
  - [B7. Strategie di gestione degli errori](#b7-strategie-di-gestione-degli-errori)
  - [B8. Performance: misurare prima di ottimizzare](#b8-performance-misurare-prima-di-ottimizzare)
- [Parte C — Esercizi Pratici Guidati](#parte-c--esercizi-pratici-guidati)
  - [C1. Esercizi progressivi con soluzione](#c1-esercizi-progressivi-con-soluzione)
  - [C2. Mini-progetto: client di chat in tempo reale](#c2-mini-progetto-client-di-chat-in-tempo-reale)
- [Parte D — Approfondimento per Esperti](#parte-d--approfondimento-per-esperti)
  - [D1. Decoratori](#d1-decoratori)
  - [D2. `SharedArrayBuffer` e `Atomics`](#d2-sharedarraybuffer-e-atomics)
  - [D3. Import map e import attributes](#d3-import-map-e-import-attributes)
  - [D4. Testing avanzato con Vitest](#d4-testing-avanzato-con-vitest)
- [Parte E — Riepilogo, Checklist e Prossimi Passi](#parte-e--riepilogo-checklist-e-prossimi-passi)

---

## Mappa concettuale

```
                        JAVASCRIPT AVANZATO
                                 │
      ┌──────────────────────────┼──────────────────────────┐
      │                          │                          │
┌─────▼──────────┐     ┌─────────▼──────────┐    ┌──────────▼─────────┐
│   ASINCRONIA   │     │    FUNZIONALE      │    │  METAPROGRAMMAZIONE│
│                │     │                    │    │                    │
│ callback       │     │ funzioni pure      │    │ Proxy              │
│  └ piramide    │     │  └ stesso input,   │    │  └ 13 trappole     │
│ Promise        │     │    stesso output   │    │  └ get set has     │
│  ├ pending     │     │  └ nessun effetto  │    │     deleteProperty │
│  ├ fulfilled   │     │    collaterale     │    │ Reflect            │
│  └ rejected    │     │ immutabilità       │    │  └ l'operazione    │
│ async/await    │     │ composizione       │    │     predefinita    │
│  └ zucchero    │     │  └ pipe, compose   │    │ Symbol             │
│    su Promise  │     │ currying           │    │ decoratori         │
│ combinatori    │     │ closure come stato │    │  └ @log @cache     │
│  ├ all         │     │                    │    │                    │
│  ├ allSettled  │     │                    │    │                    │
│  ├ race        │     │                    │    │                    │
│  └ any         │     │                    │    │                    │
└─────┬──────────┘     └──────────┬─────────┘    └──────────┬─────────┘
      │                           │                         │
      └───────────────────────────┼─────────────────────────┘
                                  │
      ┌───────────────────────────┼─────────────────────────┐
      │                           │                         │
┌─────▼──────────┐     ┌──────────▼─────────┐    ┌──────────▼─────────┐
│   CONCORRENZA  │     │      MODULI        │    │      ERRORI        │
│                │     │                    │    │                    │
│ Web Worker     │     │ ESM ≠ CJS          │    │ cause              │
│  └ thread vero │     │  └ statico vs      │    │  └ la catena       │
│ postMessage    │     │    dinamico        │    │ gerarchia propria  │
│  └ structured  │     │ interoperabilità   │    │ Result pattern     │
│    clone       │     │  └ import default  │    │ gestori globali    │
│ SharedArrayBuf │     │ import map         │    │  └ error           │
│  └ memoria     │     │ import attributes  │    │  └ unhandled-      │
│    condivisa   │     │  └ with { type }   │    │     rejection      │
│ Atomics        │     │                    │    │                    │
│  └ wait/notify │     │                    │    │                    │
└────────────────┘     └────────────────────┘    └────────────────────┘
```

---

# Parte A — Basi Assolute

---

## A1. Il problema che l'asincronia risolve

> **Analogia:** un ristorante con un cameriere solo. Se prende un ordine, va in cucina e resta lì a guardare il cuoco finché il piatto non è pronto, tutti gli altri tavoli aspettano. Il cameriere efficiente prende l'ordine, lo consegna in cucina, e nel frattempo serve gli altri: quando il piatto è pronto la cucina lo chiama. JavaScript ha un cameriere solo — un thread — e l'asincronia è il modo in cui evita di restare fermo ad aspettare.

```javascript
// ❌ SINCRONO — il thread resta bloccato per tutta la durata.
//    Nel browser: clic, animazioni e rendering congelati.
function scaricaBloccante(url) {
  const richiesta = new XMLHttpRequest()
  richiesta.open('GET', url, false) // false = sincrono
  richiesta.send() // ← qui il mondo si ferma
  return richiesta.responseText
}

// ✅ ASINCRONO — il thread torna libero, il risultato arriva dopo
async function scarica(url) {
  const risposta = await fetch(url)
  return risposta.text()
}
```

Le operazioni che in JavaScript sono asincrone hanno tutte una cosa in comune: **non le esegue JavaScript**. La rete la gestisce il sistema operativo, il disco pure, un timer lo gestisce il browser. JavaScript chiede e va avanti; quando il risultato è pronto, il lavoro riprende attraverso l'event loop visto in `tutorial_04_javascript_fondamenti.md`.

```
Cosa è asincrono, e perché:

  rete (fetch, WebSocket)      → la gestisce lo stack di rete del sistema
  timer (setTimeout)           → li gestisce il browser
  file (Node: fs.promises)     → li gestisce il sistema operativo
  database                     → li gestisce un altro processo
  animazioni (rAF)             → le gestisce il compositor
  lettura di file dell'utente  → la gestisce il browser

Cosa NON è asincrono, e non lo diventa mettendoci async:
  un ciclo su un milione di elementi
  un calcolo pesante
  JSON.parse di un file enorme
      → per questi serve un Web Worker (vedi B5)
```

---

## A2. Dai callback alle Promise

### Il callback, e il suo limite

```javascript
// Il pattern storico di Node.js: l'errore come primo parametro
function leggiConfigurazione(percorso, callback) {
  fs.readFile(percorso, 'utf8', (errore, contenuto) => {
    if (errore) return callback(errore)

    try {
      callback(null, JSON.parse(contenuto))
    } catch (errore) {
      callback(errore)
    }
  })
}
```

```javascript
// ❌ La piramide della sventura: ogni passo aggiunge un livello,
//    e la gestione dell'errore si ripete identica in ognuno.
recuperaUtente(id, (errore, utente) => {
  if (errore) return gestisci(errore)

  recuperaOrdini(utente.id, (errore, ordini) => {
    if (errore) return gestisci(errore)

    recuperaDettagli(ordini[0].id, (errore, dettagli) => {
      if (errore) return gestisci(errore)

      recuperaSpedizione(dettagli.spedizioneId, (errore, spedizione) => {
        if (errore) return gestisci(errore)

        mostra(spedizione)
      })
    })
  })
})
```

Il problema non è l'indentazione: è che **non si può restituire un valore** e non si può usare `try/catch`. Il flusso di controllo del linguaggio non funziona.

### La Promise

Una Promise è un oggetto che rappresenta un valore **non ancora disponibile**. Ha tre stati, e una transizione sola.

```
   pending  ────────►  fulfilled   (risolta con un valore)
      │
      └──────────────►  rejected    (rifiutata con un motivo)

  Una volta uscita da pending, lo stato NON cambia più:
  la Promise è "settled" e il valore è fissato.
```

```javascript
// Creare una Promise: il costruttore riceve una funzione
// con due callback, risolvi e rifiuta.
function attendi(millisecondi) {
  return new Promise((risolvi) => {
    setTimeout(risolvi, millisecondi)
  })
}

function caricaImmagine(url) {
  return new Promise((risolvi, rifiuta) => {
    const immagine = new Image()
    immagine.addEventListener('load', () => risolvi(immagine))
    immagine.addEventListener('error', () =>
      rifiuta(new Error(`Immagine non caricata: ${url}`)),
    )
    immagine.src = url
  })
}
```

```javascript
// Consumarla
caricaImmagine('/img/logo.svg')
  .then((immagine) => {
    console.log('caricata', immagine.naturalWidth)
    return immagine
  })
  .catch((errore) => {
    console.error(errore.message)
  })
  .finally(() => {
    nascondiIndicatoreCaricamento()
  })
```

### Il concatenamento appiattisce la piramide

```javascript
// La stessa catena di prima, senza annidamento
// e con UNA gestione dell'errore per tutto.
recuperaUtente(id)
  .then((utente) => recuperaOrdini(utente.id))
  .then((ordini) => recuperaDettagli(ordini[0].id))
  .then((dettagli) => recuperaSpedizione(dettagli.spedizioneId))
  .then((spedizione) => mostra(spedizione))
  .catch(gestisci) // cattura QUALUNQUE rifiuto della catena
```

La regola che rende possibile il concatenamento: **`then` restituisce sempre una Promise nuova**, e se il callback restituisce una Promise, quella viene attesa prima di proseguire.

```javascript
// ❌ SBAGLIATO — senza return, il passo successivo riceve undefined
recuperaUtente(id)
  .then((utente) => {
    recuperaOrdini(utente.id) // manca return
  })
  .then((ordini) => {
    console.log(ordini) // undefined
  })

// ✅ CORRETTO
recuperaUtente(id)
  .then((utente) => recuperaOrdini(utente.id))
  .then((ordini) => console.log(ordini))
```

### `Promise.resolve` e `Promise.reject`

```javascript
// Promise già risolte, utili per uniformare le firme
Promise.resolve(42).then((v) => console.log(v)) // 42
Promise.reject(new Error('no')).catch((e) => console.log(e.message))

// Una funzione che a volte ha già il valore in cache
function recuperaConCache(id) {
  if (cache.has(id)) {
    return Promise.resolve(cache.get(id)) // sempre una Promise
  }
  return fetch(`/api/dati/${id}`).then((r) => r.json())
}
```

### `Promise.withResolvers`

```javascript
// ES2024: espone risolvi e rifiuta all'esterno del costruttore.
// Utile quando la risoluzione avviene in un altro punto del codice.
function creaAttesaEvento(bersaglio, nomeEvento, timeout = 5000) {
  const { promise, resolve, reject } = Promise.withResolvers()

  const scadenza = setTimeout(
    () => reject(new Error(`Evento ${nomeEvento} non arrivato entro ${timeout} ms`)),
    timeout,
  )

  bersaglio.addEventListener(
    nomeEvento,
    (evento) => {
      clearTimeout(scadenza)
      resolve(evento)
    },
    { once: true },
  )

  return promise
}
```

Prima di `withResolvers` lo stesso si otteneva dichiarando due variabili fuori dal costruttore e assegnandole dentro — funzionava, ma era più verboso e meno chiaro.

---

## A3. `async` e `await`

`async`/`await` non introduce un meccanismo nuovo: è sintassi sopra le Promise, che permette di scrivere codice asincrono con il flusso di controllo normale del linguaggio.

```javascript
// Le due forme sono equivalenti

// Con .then()
function caricaProfiloConThen(id) {
  return recuperaUtente(id)
    .then((utente) => recuperaOrdini(utente.id).then((ordini) => ({ utente, ordini })))
    .catch((errore) => {
      registra(errore)
      throw errore
    })
}

// Con async/await
async function caricaProfilo(id) {
  try {
    const utente = await recuperaUtente(id)
    const ordini = await recuperaOrdini(utente.id)
    return { utente, ordini }
  } catch (errore) {
    registra(errore)
    throw errore
  }
}
```

### Le regole

```javascript
// 1. Una funzione async restituisce SEMPRE una Promise
async function numero() {
  return 42
}
console.log(numero()) // Promise { 42 }, non 42

// 2. await sospende la funzione, non il thread
async function esempio() {
  console.log('prima')
  await attendi(1000) // il thread è libero per 1 secondo
  console.log('dopo')
}

// 3. throw dentro una funzione async rifiuta la Promise
async function fallisce() {
  throw new Error('errore')
}
fallisce().catch((e) => console.log(e.message)) // 'errore'

// 4. await funziona su qualunque "thenable", non solo sulle Promise
await { then: (risolvi) => risolvi(42) } // 42

// 5. await su un valore non-Promise lo avvolge e cede comunque il controllo
await 42 // il resto della funzione diventa una microtask
```

### L'errore che raddoppia i tempi di attesa

```javascript
// ❌ SBAGLIATO — sequenziale: le tre richieste sono indipendenti
//    ma vengono eseguite una dopo l'altra. Tempo: 300 ms.
async function caricaSequenziale() {
  const utenti = await fetch('/api/utenti').then((r) => r.json()) // 100 ms
  const prodotti = await fetch('/api/prodotti').then((r) => r.json()) // 100 ms
  const ordini = await fetch('/api/ordini').then((r) => r.json()) // 100 ms
  return { utenti, prodotti, ordini }
}

// ✅ CORRETTO — parallelo: partono insieme. Tempo: ~100 ms.
async function caricaParallelo() {
  const [utenti, prodotti, ordini] = await Promise.all([
    fetch('/api/utenti').then((r) => r.json()),
    fetch('/api/prodotti').then((r) => r.json()),
    fetch('/api/ordini').then((r) => r.json()),
  ])
  return { utenti, prodotti, ordini }
}
```

**Quando il sequenziale è giusto:** quando il secondo passo ha bisogno del risultato del primo. `await` in sequenza non è un errore di per sé — lo è quando le operazioni sono indipendenti.

```javascript
// ❌ SBAGLIATO — await dentro un ciclo: N richieste una dopo l'altra
async function caricaTuttiSbagliato(id) {
  const risultati = []
  for (const singolo of id) {
    risultati.push(await recupera(singolo)) // N × latenza
  }
  return risultati
}

// ✅ CORRETTO quando l'ordine non conta e N è ragionevole
async function caricaTutti(id) {
  return Promise.all(id.map((singolo) => recupera(singolo)))
}

// ⚠ Con N grande, Promise.all apre N connessioni insieme:
//    serve un limite di concorrenza. Vedi B1.
```

### Top-level `await`

```javascript
// configurazione.js — await fuori da una funzione async.
// Il modulo diventa asincrono: chi lo importa attende.
const risposta = await fetch('/api/configurazione')

export const configurazione = await risposta.json()
```

```javascript
// main.js — l'import attende che configurazione.js sia pronto
import { configurazione } from './configurazione.js'

console.log(configurazione.porta)
```

Va usato con parsimonia: un modulo che attende la rete al caricamento ritarda tutto ciò che dipende da lui, e in un albero di dipendenze l'effetto si propaga.

---

## A4. I combinatori di Promise

```javascript
const promesse = [recupera('/a'), recupera('/b'), recupera('/c')]
```

| Combinatore | Risolve quando | Rifiuta quando | Risultato |
|---|---|---|---|
| `Promise.all` | **tutte** risolvono | **la prima** che rifiuta | array dei valori |
| `Promise.allSettled` | tutte sono concluse | **mai** | array di `{status, value/reason}` |
| `Promise.race` | **la prima** si conclude | la prima si conclude rifiutando | il valore della prima |
| `Promise.any` | **la prima** che risolve | **tutte** rifiutano | il primo valore |

### `Promise.all` — tutto o niente

```javascript
try {
  const [utenti, prodotti] = await Promise.all([
    recupera('/api/utenti'),
    recupera('/api/prodotti'),
  ])
} catch (errore) {
  // Basta UN fallimento per arrivare qui.
  // ⚠ Le altre richieste NON vengono annullate: continuano
  //    e il loro risultato viene scartato.
  console.error('almeno una richiesta è fallita', errore)
}
```

### `Promise.allSettled` — quando i fallimenti parziali sono accettabili

```javascript
const esiti = await Promise.allSettled([
  recupera('/api/utenti'),
  recupera('/api/prodotti'),
  recupera('/api/statistiche'), // questo può fallire senza bloccare il resto
])

const riusciti = esiti.filter((e) => e.status === 'fulfilled').map((e) => e.value)

const falliti = esiti
  .map((e, indice) => ({ e, indice }))
  .filter(({ e }) => e.status === 'rejected')

for (const { e, indice } of falliti) {
  console.warn(`Richiesta ${indice} fallita:`, e.reason.message)
}
```

È la scelta corretta per una dashboard: se il grafico delle statistiche non carica, il resto della pagina deve comunque comparire.

### `Promise.race` — il primo che arriva

```javascript
// Il caso d'uso classico: un timeout
function conTimeout(promessa, millisecondi) {
  return Promise.race([
    promessa,
    new Promise((_, rifiuta) =>
      setTimeout(() => rifiuta(new Error(`Timeout dopo ${millisecondi} ms`)), millisecondi),
    ),
  ])
}

const dati = await conTimeout(recupera('/api/lenta'), 3000)
```

```javascript
// ⚠ race con una promessa già rifiutata rifiuta subito,
//    anche se le altre avrebbero avuto successo.
await Promise.race([Promise.reject(new Error('subito')), attendi(10).then(() => 'ok')])
// rifiuta con 'subito'
```

### `Promise.any` — il primo che riesce

```javascript
// Provare più fonti, tenere la prima che risponde
try {
  const dati = await Promise.any([
    recupera('https://cdn1.esempio.it/dati.json'),
    recupera('https://cdn2.esempio.it/dati.json'),
    recupera('https://origine.esempio.it/dati.json'),
  ])
} catch (errore) {
  // AggregateError: tutte hanno fallito
  console.error('nessuna fonte disponibile')
  for (const singolo of errore.errors) {
    console.error(' -', singolo.message)
  }
}
```

`Promise.any` rifiuta con un `AggregateError`, che espone tutti gli errori in `.errors`. È l'unico combinatore che lo fa.

---

## A5. Fetch: richieste HTTP fatte bene

```javascript
const risposta = await fetch('/api/fatture')
const dati = await risposta.json()
```

Due righe, e già contengono l'errore più diffuso.

### `fetch` non rifiuta sugli errori HTTP

```javascript
// ❌ SBAGLIATO — un 404 o un 500 NON fanno rifiutare la Promise.
//    fetch rifiuta solo per errori di RETE: connessione caduta,
//    DNS irrisolto, CORS bloccato, richiesta annullata.
try {
  const risposta = await fetch('/api/inesistente')
  const dati = await risposta.json() // SyntaxError: la risposta è HTML
} catch (errore) {
  // Qui arriva un errore di parsing, non il 404
}

// ✅ CORRETTO — verificare sempre risposta.ok
async function recupera(url, opzioni) {
  const risposta = await fetch(url, opzioni)

  if (!risposta.ok) {
    // Provare a leggere il corpo dell'errore: molte API
    // restituiscono un JSON con il dettaglio
    let dettaglio = null
    try {
      dettaglio = await risposta.json()
    } catch {
      dettaglio = await risposta.text().catch(() => null)
    }

    throw new ErroreHttp(risposta, dettaglio)
  }

  return risposta
}

class ErroreHttp extends Error {
  constructor(risposta, dettaglio) {
    super(`${risposta.status} ${risposta.statusText} — ${risposta.url}`)
    this.name = 'ErroreHttp'
    this.stato = risposta.status
    this.url = risposta.url
    this.dettaglio = dettaglio
  }

  get eRipetibile() {
    // 408 timeout, 429 troppe richieste, 5xx errori del server
    return this.stato === 408 || this.stato === 429 || this.stato >= 500
  }
}
```

### Le opzioni che contano

```javascript
const risposta = await fetch('/api/fatture', {
  method: 'POST',

  headers: {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  },

  body: JSON.stringify({ cliente: 'Rossi', importo: 1200 }),

  // Invia i cookie:
  //   'same-origin' (default) → solo stessa origine
  //   'include'               → anche cross-origin, richiede
  //                             Access-Control-Allow-Credentials sul server
  //   'omit'                  → mai
  credentials: 'same-origin',

  // 'cors' (default) | 'no-cors' | 'same-origin'
  mode: 'cors',

  // 'default' | 'no-store' | 'reload' | 'no-cache' | 'force-cache'
  cache: 'no-store',

  // 'follow' (default) | 'error' | 'manual'
  redirect: 'follow',

  // Quanto dell'indirizzo di provenienza trasmettere
  referrerPolicy: 'strict-origin-when-cross-origin',

  // Per la cancellazione: vedi A6
  signal: controller.signal,
})
```

```javascript
// ⚠ Con FormData NON impostare Content-Type:
//    il browser deve generare il boundary di multipart/form-data.
await fetch('/api/allegati', {
  method: 'POST',
  body: new FormData(modulo), // niente headers
})
```

### Leggere il corpo, una volta sola

```javascript
const risposta = await fetch('/api/dati')

// Il corpo è uno stream: si può leggere UNA VOLTA
await risposta.json() // oppure
await risposta.text() //
await risposta.blob() //
await risposta.arrayBuffer() //
await risposta.formData() //

// ❌ La seconda lettura fallisce
// TypeError: Body has already been consumed

// ✅ Per leggerlo due volte, clonare PRIMA
const copia = risposta.clone()
const testo = await copia.text()
const dati = await risposta.json()
```

### Leggere a pezzi, per i download lunghi

```javascript
// Mostrare l'avanzamento di un download
async function scaricaConAvanzamento(url, alProgresso) {
  const risposta = await fetch(url)
  if (!risposta.ok) throw new ErroreHttp(risposta, null)

  const totale = Number(risposta.headers.get('Content-Length')) || 0
  const lettore = risposta.body.getReader()
  const pezzi = []
  let ricevuti = 0

  while (true) {
    const { done, value } = await lettore.read()
    if (done) break

    pezzi.push(value)
    ricevuti += value.length
    if (totale > 0) alProgresso(ricevuti / totale)
  }

  return new Blob(pezzi)
}
```

---

## A6. Cancellare con `AbortController`

Una richiesta partita e non più necessaria continua a occupare una connessione e a consumare dati. Peggio: se arriva dopo una più recente, può sovrascrivere il risultato giusto con uno vecchio.

```javascript
const controller = new AbortController()

// Passare il segnale alla richiesta
fetch('/api/lenta', { signal: controller.signal })
  .then((r) => r.json())
  .catch((errore) => {
    if (errore.name === 'AbortError') {
      console.log('annullata volontariamente')
      return // NON è un errore da segnalare all'utente
    }
    throw errore
  })

// Annullare
controller.abort()
```

### Il pattern della ricerca con suggerimenti

È il caso in cui la cancellazione non è un'ottimizzazione ma una correzione: senza, una risposta lenta può arrivare dopo una veloce e mostrare risultati sbagliati.

```javascript
let controllerCorrente = null

async function cerca(termine) {
  // Annulla la richiesta precedente, se ancora in corso
  controllerCorrente?.abort()
  controllerCorrente = new AbortController()

  try {
    const risposta = await fetch(`/api/cerca?q=${encodeURIComponent(termine)}`, {
      signal: controllerCorrente.signal,
    })
    if (!risposta.ok) throw new ErroreHttp(risposta, null)

    const risultati = await risposta.json()
    mostraRisultati(risultati)
  } catch (errore) {
    if (errore.name === 'AbortError') return // atteso: ignora
    mostraErrore(errore)
  }
}

campo.addEventListener('input', debounce((evento) => cerca(evento.target.value), 300))
```

### Timeout con `AbortSignal.timeout`

```javascript
// La forma moderna, senza costruire il controller a mano
const risposta = await fetch('/api/dati', {
  signal: AbortSignal.timeout(5000),
})

// Combinare più segnali: annulla se scade il tempo O se l'utente annulla
const controllerUtente = new AbortController()

const risposta2 = await fetch('/api/dati', {
  signal: AbortSignal.any([controllerUtente.signal, AbortSignal.timeout(10_000)]),
})
```

```javascript
// Distinguere il timeout dall'annullamento dell'utente
try {
  await fetch(url, { signal: AbortSignal.timeout(5000) })
} catch (errore) {
  if (errore.name === 'TimeoutError') {
    mostraErrore('Il server non ha risposto in tempo.')
  } else if (errore.name === 'AbortError') {
    // annullata dall'utente: nessun messaggio
  } else {
    throw errore
  }
}
```

### `AbortController` non è solo per `fetch`

```javascript
// Rimuove tutti i listener registrati con lo stesso segnale
const controller = new AbortController()

elemento.addEventListener('click', gestore, { signal: controller.signal })
window.addEventListener('resize', gestore, { signal: controller.signal })
document.addEventListener('keydown', gestore, { signal: controller.signal })

controller.abort() // tutti e tre rimossi

// Nel proprio codice asincrono
async function operazioneLunga({ signal }) {
  for (const elemento of moltiElementi) {
    // throwIfAborted solleva AbortError se il segnale è stato attivato
    signal?.throwIfAborted()
    await elabora(elemento)
  }
}
```

---

# Parte B — Comprensione Profonda

---

## B1. Pattern asincroni: concorrenza, retry, deduplicazione

`Promise.all` su mille elementi apre mille richieste insieme: il browser ne accoda la maggior parte, il server può rifiutarle, e la memoria cresce. Servono strumenti più precisi.

### Concorrenza limitata

```javascript
/**
 * Esegue le operazioni con al massimo N in volo contemporaneamente.
 * Restituisce i risultati nell'ordine degli elementi in ingresso.
 */
async function conConcorrenza(elementi, operazione, limite = 5) {
  const risultati = new Array(elementi.length)
  let prossimo = 0

  /** Un "operaio": prende il prossimo elemento libero finché ce n'è. */
  async function operaio() {
    while (prossimo < elementi.length) {
      const indice = prossimo++
      risultati[indice] = await operazione(elementi[indice], indice)
    }
  }

  // Avvia N operai in parallelo; ognuno consuma dalla stessa coda
  const operai = Array.from({ length: Math.min(limite, elementi.length) }, operaio)
  await Promise.all(operai)

  return risultati
}
```

```javascript
// Uso: 500 immagini, al massimo 6 richieste insieme
const metadati = await conConcorrenza(
  urlImmagini,
  async (url) => {
    const risposta = await fetch(url, { method: 'HEAD' })
    return { url, dimensione: risposta.headers.get('Content-Length') }
  },
  6,
)
```

La variante che non interrompe tutto al primo errore:

```javascript
async function conConcorrenzaTollerante(elementi, operazione, limite = 5) {
  const esiti = new Array(elementi.length)
  let prossimo = 0

  async function operaio() {
    while (prossimo < elementi.length) {
      const indice = prossimo++
      try {
        esiti[indice] = { status: 'fulfilled', value: await operazione(elementi[indice], indice) }
      } catch (errore) {
        esiti[indice] = { status: 'rejected', reason: errore }
      }
    }
  }

  await Promise.all(Array.from({ length: Math.min(limite, elementi.length) }, operaio))
  return esiti
}
```

### Retry con backoff esponenziale e jitter

```javascript
/**
 * Ritenta un'operazione con attese crescenti.
 *
 * Il jitter — la componente casuale — non è un dettaglio:
 * senza, mille client che falliscono insieme ritentano tutti
 * nello stesso istante e riproducono il picco che ha causato
 * il problema. È il fenomeno noto come thundering herd.
 */
async function conRitentativi(
  operazione,
  {
    tentativiMassimi = 3,
    attesaIniziale = 500,
    attesaMassima = 30_000,
    fattore = 2,
    ripetibile = () => true,
    signal,
  } = {},
) {
  let ultimoErrore = null

  for (let tentativo = 1; tentativo <= tentativiMassimi; tentativo++) {
    signal?.throwIfAborted()

    try {
      return await operazione(tentativo)
    } catch (errore) {
      ultimoErrore = errore

      // Un annullamento non si ritenta mai
      if (errore.name === 'AbortError') throw errore

      // Un 400 non migliora ritentando: solo gli errori
      // transitori vanno ripetuti
      if (!ripetibile(errore)) throw errore

      if (tentativo === tentativiMassimi) break

      const attesaBase = Math.min(attesaIniziale * fattore ** (tentativo - 1), attesaMassima)
      // Jitter completo: un valore casuale fra 0 e l'attesa calcolata
      const attesa = Math.random() * attesaBase

      await new Promise((risolvi, rifiuta) => {
        const temporizzatore = setTimeout(risolvi, attesa)
        signal?.addEventListener(
          'abort',
          () => {
            clearTimeout(temporizzatore)
            rifiuta(signal.reason)
          },
          { once: true },
        )
      })
    }
  }

  throw new Error(`Fallito dopo ${tentativiMassimi} tentativi`, { cause: ultimoErrore })
}
```

```javascript
// Uso
const dati = await conRitentativi(() => recupera('/api/instabile'), {
  tentativiMassimi: 4,
  ripetibile: (errore) => errore.eRipetibile ?? errore.name === 'TypeError',
  signal: AbortSignal.timeout(30_000),
})
```

```
Le attese, con attesaIniziale 500 e fattore 2:

  tentativo 1 fallisce → attende fra 0 e 500 ms
  tentativo 2 fallisce → attende fra 0 e 1000 ms
  tentativo 3 fallisce → attende fra 0 e 2000 ms
  tentativo 4 fallisce → si arrende

Il jitter fa sì che mille client non ripartano insieme.
```

### Deduplicazione delle richieste in volo

```javascript
/**
 * Se la stessa richiesta è già in corso, restituisce la Promise
 * esistente invece di aprirne una seconda.
 *
 * Il caso: tre componenti della pagina chiedono lo stesso profilo
 * utente al montaggio. Senza deduplicazione, tre richieste identiche.
 */
function creaDeduplicatore(operazione, chiaveDa = (...a) => JSON.stringify(a)) {
  const inVolo = new Map()

  return function (...argomenti) {
    const chiave = chiaveDa(...argomenti)

    if (inVolo.has(chiave)) {
      return inVolo.get(chiave)
    }

    const promessa = operazione(...argomenti).finally(() => {
      // Rimuovere SEMPRE, anche in caso di errore:
      // altrimenti un fallimento resta memorizzato per sempre
      inVolo.delete(chiave)
    })

    inVolo.set(chiave, promessa)
    return promessa
  }
}

const recuperaProfilo = creaDeduplicatore((id) => recupera(`/api/utenti/${id}`))

// Tre chiamate contemporanee → UNA sola richiesta di rete
const [a, b, c] = await Promise.all([
  recuperaProfilo(42),
  recuperaProfilo(42),
  recuperaProfilo(42),
])
```

### Interruttore automatico

```javascript
/**
 * Quando un servizio è chiaramente giù, smette di interrogarlo
 * per un periodo invece di accumulare timeout.
 *
 *   chiuso     → le richieste passano
 *   aperto     → falliscono subito, senza toccare la rete
 *   semiaperto → passa una richiesta di prova
 */
function creaInterruttore(operazione, { soglia = 5, attesaRipristino = 30_000 } = {}) {
  let stato = 'chiuso'
  let fallimentiConsecutivi = 0
  let riapribileDa = 0

  return async function (...argomenti) {
    if (stato === 'aperto') {
      if (Date.now() < riapribileDa) {
        throw new Error('Servizio non disponibile (interruttore aperto)')
      }
      stato = 'semiaperto'
    }

    try {
      const risultato = await operazione(...argomenti)
      // Successo: si richiude e si azzera il conteggio
      stato = 'chiuso'
      fallimentiConsecutivi = 0
      return risultato
    } catch (errore) {
      fallimentiConsecutivi++

      if (stato === 'semiaperto' || fallimentiConsecutivi >= soglia) {
        stato = 'aperto'
        riapribileDa = Date.now() + attesaRipristino
      }

      throw errore
    }
  }
}
```

### Coda con priorità

```javascript
/**
 * Le operazioni con priorità più alta vengono servite prima,
 * a parità di limite di concorrenza.
 */
function creaCoda({ concorrenza = 3 } = {}) {
  const inAttesa = []
  let attive = 0

  function prossimo() {
    if (attive >= concorrenza || inAttesa.length === 0) return

    // Ordina per priorità decrescente, poi per ordine di arrivo
    inAttesa.sort((a, b) => b.priorita - a.priorita || a.sequenza - b.sequenza)
    const compito = inAttesa.shift()

    attive++
    compito
      .operazione()
      .then(compito.risolvi, compito.rifiuta)
      .finally(() => {
        attive--
        prossimo()
      })
  }

  let sequenza = 0

  return {
    aggiungi(operazione, priorita = 0) {
      const { promise, resolve, reject } = Promise.withResolvers()
      inAttesa.push({ operazione, priorita, sequenza: sequenza++, risolvi: resolve, rifiuta: reject })
      prossimo()
      return promise
    },

    get inCoda() {
      return inAttesa.length
    },

    get inEsecuzione() {
      return attive
    },
  }
}

const coda = creaCoda({ concorrenza: 2 })

coda.aggiungi(() => recupera('/api/miniatura/1'), 0)
coda.aggiungi(() => recupera('/api/immagine-visibile'), 10) // servita per prima
```

---

## B2. Programmazione funzionale in JavaScript

JavaScript non è un linguaggio funzionale, ma ha ciò che serve: funzioni di prima classe, closure, e metodi di array che non modificano l'originale.

### Funzioni pure

```javascript
// PURA: stesso input → stesso output, nessun effetto collaterale
function calcolaTotale(righe, aliquota) {
  return righe.reduce((somma, r) => somma + r.prezzo * r.quantita, 0) * (1 + aliquota)
}

// IMPURA: dipende da uno stato esterno e lo modifica
let aliquotaGlobale = 0.22
let ultimoTotale = 0

function calcolaTotaleImpura(righe) {
  ultimoTotale = righe.reduce((s, r) => s + r.prezzo * r.quantita, 0) * (1 + aliquotaGlobale)
  console.log('calcolato', ultimoTotale) // anche questo è un effetto
  return ultimoTotale
}
```

```
Perché le funzioni pure valgono la pena:

  · si testano senza preparare uno stato: chiami e verifichi
  · si possono memoizzare, perché il risultato dipende solo dagli argomenti
  · si possono eseguire in parallelo o in un Worker
  · leggendo la firma sai tutto ciò che la funzione tocca
  · un bug è localizzato: se l'output è sbagliato, la causa è dentro

Le funzioni impure servono comunque: I/O, DOM, rete, log.
L'architettura che funziona è concentrarle ai bordi, e tenere
puro il nucleo che contiene la logica.
```

### Immutabilità

```javascript
const fatture = [
  { id: 1, cliente: 'Rossi', pagata: false },
  { id: 2, cliente: 'Bianchi', pagata: false },
]

// ❌ MUTAZIONE — chi teneva un riferimento vede cambiare i dati
//    sotto i piedi, senza essere avvisato
function segnaPagataSbagliato(elenco, id) {
  const fattura = elenco.find((f) => f.id === id)
  fattura.pagata = true
  return elenco
}

// ✅ IMMUTABILE — chi aveva l'array precedente lo conserva intatto
function segnaPagata(elenco, id) {
  return elenco.map((f) => (f.id === id ? { ...f, pagata: true } : f))
}
```

```javascript
// Gli aggiornamenti immutabili più frequenti
const elenco = [1, 2, 3]

// aggiungere
;[...elenco, 4]
elenco.concat(4)

// rimuovere per indice
elenco.toSpliced(1, 1)
elenco.filter((_, i) => i !== 1)

// sostituire per indice
elenco.with(1, 99)

// ordinare
elenco.toSorted((a, b) => a - b)
elenco.toReversed()

// Su oggetti annidati, ogni livello va ricreato
const stato = { utente: { profilo: { nome: 'Anna' } } }

const nuovoStato = {
  ...stato,
  utente: {
    ...stato.utente,
    profilo: { ...stato.utente.profilo, nome: 'Marco' },
  },
}
```

Con strutture profonde questo diventa illeggibile; è il problema che librerie come Immer risolvono permettendo di scrivere codice apparentemente mutabile che produce copie immutabili.

### Composizione

```javascript
/** Da destra a sinistra, come la notazione matematica f(g(x)). */
const componi =
  (...funzioni) =>
  (valore) =>
    funzioni.reduceRight((acc, f) => f(acc), valore)

/** Da sinistra a destra: si legge nell'ordine in cui accade. */
const incanala =
  (...funzioni) =>
  (valore) =>
    funzioni.reduce((acc, f) => f(acc), valore)

const rimuoviSpazi = (s) => s.trim()
const inMinuscolo = (s) => s.toLowerCase()
const sostituisciSpazi = (s) => s.replaceAll(/\s+/g, '-')
const soloAmmessi = (s) => s.replaceAll(/[^a-z0-9-]/g, '')

const creaSlug = incanala(rimuoviSpazi, inMinuscolo, sostituisciSpazi, soloAmmessi)

console.log(creaSlug('  Fattura 2026 / Rossi!  ')) // 'fattura-2026--rossi'
```

```javascript
// Versione asincrona
const incanalaAsync =
  (...funzioni) =>
  async (valore) => {
    let acc = valore
    for (const f of funzioni) acc = await f(acc)
    return acc
  }

const elaboraOrdine = incanalaAsync(
  validaOrdine,
  calcolaSpedizione,
  applicaSconto,
  salvaSuDatabase,
  inviaConferma,
)
```

### Currying e applicazione parziale

```javascript
// Currying: una funzione di N argomenti diventa N funzioni di uno
const moltiplica = (a) => (b) => a * b

const raddoppia = moltiplica(2)
const triplica = moltiplica(3)

console.log([1, 2, 3].map(raddoppia)) // [2, 4, 6]

// Utile per specializzare una funzione generica
const filtraPerCampo = (campo) => (valore) => (elenco) =>
  elenco.filter((elemento) => elemento[campo] === valore)

const soloDelCliente = filtraPerCampo('cliente')
const soloRossi = soloDelCliente('Rossi')

console.log(soloRossi(fatture))
```

```javascript
// Applicazione parziale con bind: il primo argomento è this
function registra(livello, modulo, messaggio) {
  console.log(`[${livello}] ${modulo}: ${messaggio}`)
}

const errore = registra.bind(null, 'ERRORE')
const errorePagamenti = errore.bind(null, 'pagamenti')

errorePagamenti('carta rifiutata') // [ERRORE] pagamenti: carta rifiutata
```

### Il pattern del risultato, senza eccezioni

```javascript
/**
 * Un risultato che rappresenta successo o fallimento come VALORE.
 * Chi chiama non può ignorare l'errore: deve guardare .ok.
 */
const Ok = (valore) => ({ ok: true, valore })
const Errore = (errore) => ({ ok: false, errore })

/** Applica una funzione solo se il risultato è positivo. */
const mappa = (funzione) => (risultato) =>
  risultato.ok ? Ok(funzione(risultato.valore)) : risultato

/** Come mappa, ma la funzione restituisce a sua volta un risultato. */
const concatena = (funzione) => (risultato) =>
  risultato.ok ? funzione(risultato.valore) : risultato

// Le validazioni, ognuna indipendente e testabile
const validaNonVuoto = (campo) => (valore) =>
  valore?.trim() ? Ok(valore.trim()) : Errore(`${campo} è obbligatorio`)

const validaLunghezza = (minimo) => (valore) =>
  valore.length >= minimo ? Ok(valore) : Errore(`Servono almeno ${minimo} caratteri`)

const validaEmail = (valore) =>
  valore.includes('@') && valore.includes('.') ? Ok(valore) : Errore('Indirizzo non valido')

// La catena si ferma al primo errore, senza try/catch
const validaCampoEmail = (valore) =>
  [concatena(validaLunghezza(5)), concatena(validaEmail)].reduce(
    (acc, passo) => passo(acc),
    validaNonVuoto('email')(valore),
  )

console.log(validaCampoEmail('anna@example.it')) // { ok: true, valore: 'anna@example.it' }
console.log(validaCampoEmail('anna')) // { ok: false, errore: 'Servono almeno 5 caratteri' }
console.log(validaCampoEmail('')) // { ok: false, errore: 'email è obbligatorio' }
```

---

## B3. `Proxy` e `Reflect`

Un `Proxy` avvolge un oggetto e intercetta le operazioni fondamentali: lettura, scrittura, cancellazione, verifica di esistenza. `Reflect` fornisce le implementazioni predefinite di quelle stesse operazioni.

```javascript
const bersaglio = { nome: 'Anna', eta: 34 }

const osservato = new Proxy(bersaglio, {
  get(oggetto, proprieta, ricevitore) {
    console.log(`letta ${String(proprieta)}`)
    // Reflect.get fa esattamente ciò che avrebbe fatto l'accesso normale,
    // compresa la gestione corretta di getter e catena prototipale
    return Reflect.get(oggetto, proprieta, ricevitore)
  },

  set(oggetto, proprieta, valore, ricevitore) {
    console.log(`scritta ${String(proprieta)} = ${valore}`)
    return Reflect.set(oggetto, proprieta, valore, ricevitore)
  },
})

osservato.nome // 'letta nome'
osservato.eta = 35 // 'scritta eta = 35'
```

### Le trappole

```
Le tredici trappole, e l'operazione che intercettano:

  get                        oggetto.x
  set                        oggetto.x = v
  has                        'x' in oggetto
  deleteProperty             delete oggetto.x
  ownKeys                    Object.keys, for...in, spread
  getOwnPropertyDescriptor   Object.getOwnPropertyDescriptor
  defineProperty             Object.defineProperty
  getPrototypeOf             Object.getPrototypeOf, instanceof
  setPrototypeOf             Object.setPrototypeOf
  isExtensible               Object.isExtensible
  preventExtensions          Object.preventExtensions
  apply                      funzione(...)     ← solo su funzioni
  construct                  new Funzione(...) ← solo su funzioni
```

### Casi d'uso reali

```javascript
// 1. Validazione all'assegnazione
function conValidazione(oggetto, regole) {
  return new Proxy(oggetto, {
    set(bersaglio, proprieta, valore, ricevitore) {
      const regola = regole[proprieta]

      if (regola && !regola.verifica(valore)) {
        throw new TypeError(`${String(proprieta)}: ${regola.messaggio}`)
      }

      return Reflect.set(bersaglio, proprieta, valore, ricevitore)
    },
  })
}

const utente = conValidazione(
  { nome: '', eta: 0 },
  {
    nome: { verifica: (v) => typeof v === 'string' && v.length > 0, messaggio: 'non può essere vuoto' },
    eta: { verifica: (v) => Number.isInteger(v) && v >= 0 && v < 150, messaggio: 'deve essere fra 0 e 149' },
  },
)

utente.nome = 'Anna' // ok
// utente.eta = -5      // TypeError: eta: deve essere fra 0 e 149
```

```javascript
// 2. Valore predefinito per le chiavi mancanti
function conPredefinito(costruttorePredefinito) {
  return new Proxy(
    {},
    {
      get(bersaglio, proprieta) {
        if (!(proprieta in bersaglio) && typeof proprieta === 'string') {
          bersaglio[proprieta] = costruttorePredefinito()
        }
        return Reflect.get(bersaglio, proprieta)
      },
    },
  )
}

const conteggi = conPredefinito(() => 0)
conteggi.rossi++ // nessun controllo di esistenza
conteggi.rossi++
console.log(conteggi.rossi) // 2

const gruppi = conPredefinito(() => [])
gruppi.milano.push('Anna') // l'array viene creato al volo
```

```javascript
// 3. Intercettare gli errori di battitura sulle proprietà
function severo(oggetto, nome = 'oggetto') {
  return new Proxy(oggetto, {
    get(bersaglio, proprieta, ricevitore) {
      if (typeof proprieta === 'string' && !(proprieta in bersaglio)) {
        throw new ReferenceError(`${nome}.${proprieta} non esiste`)
      }
      return Reflect.get(bersaglio, proprieta, ricevitore)
    },
  })
}

const configurazione = severo({ porta: 3000, host: 'localhost' }, 'configurazione')
console.log(configurazione.porta) // 3000
// configurazione.prta              // ReferenceError: configurazione.prta non esiste
```

```javascript
// 4. Reattività — il meccanismo alla base di Vue 3
function reattivo(oggetto, alCambiamento) {
  return new Proxy(oggetto, {
    get(bersaglio, proprieta, ricevitore) {
      const valore = Reflect.get(bersaglio, proprieta, ricevitore)
      // Reattività profonda: anche gli oggetti annidati
      return valore && typeof valore === 'object' ? reattivo(valore, alCambiamento) : valore
    },

    set(bersaglio, proprieta, valore, ricevitore) {
      const precedente = bersaglio[proprieta]
      const esito = Reflect.set(bersaglio, proprieta, valore, ricevitore)

      if (!Object.is(precedente, valore)) {
        alCambiamento(proprieta, valore, precedente)
      }
      return esito
    },

    deleteProperty(bersaglio, proprieta) {
      const esito = Reflect.deleteProperty(bersaglio, proprieta)
      alCambiamento(proprieta, undefined, bersaglio[proprieta])
      return esito
    },
  })
}

const stato = reattivo({ conteggio: 0, utente: { nome: 'Anna' } }, (chiave, nuovo) =>
  console.log(`${String(chiave)} → ${nuovo}`),
)

stato.conteggio = 1 // 'conteggio → 1'
stato.utente.nome = 'Marco' // 'nome → Marco'  ← anche in profondità
```

### Perché `Reflect` e non l'operazione diretta

```javascript
// ❌ SBAGLIATO — bersaglio[proprieta] ignora il ricevitore:
//    un getter che usa this legge dall'oggetto originale
//    invece che dal proxy, e la reattività non scatta
const proxySbagliato = new Proxy(bersaglio, {
  get(oggetto, proprieta) {
    return oggetto[proprieta]
  },
})

// ✅ CORRETTO — Reflect.get inoltra il ricevitore
const proxyCorretto = new Proxy(bersaglio, {
  get(oggetto, proprieta, ricevitore) {
    return Reflect.get(oggetto, proprieta, ricevitore)
  },
})
```

```javascript
// Reflect.set restituisce un booleano, l'assegnazione no.
// In strict mode la trappola set DEVE restituire true,
// o l'assegnazione solleva TypeError.

// ❌ Manca il return: undefined è falsy → TypeError in strict mode
const setSbagliato = new Proxy(bersaglio, {
  set(oggetto, proprieta, valore) {
    oggetto[proprieta] = valore
  },
})

// ✅
const setCorretto = new Proxy(bersaglio, {
  set(oggetto, proprieta, valore, ricevitore) {
    return Reflect.set(oggetto, proprieta, valore, ricevitore)
  },
})
```

### I limiti dei Proxy

```javascript
// 1. Costano: ogni accesso passa dalla trappola.
//    Su un ciclo caldo la differenza si misura.

// 2. L'identità cambia
const oggetto = {}
const proxy = new Proxy(oggetto, {})
console.log(proxy === oggetto) // false

// 3. Non intercettano tutto: le proprietà private con #
//    e gli slot interni (Map, Set, Date) non passano dalle trappole
class ConPrivato {
  #segreto = 42
  leggi() {
    return this.#segreto
  }
}
const conProxy = new Proxy(new ConPrivato(), {})
// conProxy.leggi()   // TypeError: il metodo non trova il campo privato

// 4. Non sono revocabili di default; per farlo serve Proxy.revocable
const { proxy: revocabile, revoke } = Proxy.revocable({ a: 1 }, {})
console.log(revocabile.a) // 1
revoke()
// revocabile.a            // TypeError: proxy revocato
```

---

## B4. Design pattern che valgono la pena

Molti pattern classici esistono per aggirare limiti che JavaScript non ha. Questi cinque risolvono problemi reali.

### Strategy: sostituire i condizionali con una mappa

```javascript
// ❌ La catena che cresce a ogni formato nuovo
function esporta(dati, formato) {
  if (formato === 'csv') {
    return dati.map((r) => Object.values(r).join(',')).join('\n')
  } else if (formato === 'json') {
    return JSON.stringify(dati, null, 2)
  } else if (formato === 'tsv') {
    return dati.map((r) => Object.values(r).join('\t')).join('\n')
  }
  throw new Error(`Formato sconosciuto: ${formato}`)
}

// ✅ Una mappa di strategie: aggiungere un formato non tocca
//    la funzione, e ogni strategia si testa da sola
const STRATEGIE_ESPORTAZIONE = {
  csv: (dati) => dati.map((r) => Object.values(r).join(',')).join('\n'),
  tsv: (dati) => dati.map((r) => Object.values(r).join('\t')).join('\n'),
  json: (dati) => JSON.stringify(dati, null, 2),
  ndjson: (dati) => dati.map((r) => JSON.stringify(r)).join('\n'),
}

function esportaConStrategia(dati, formato) {
  const strategia = STRATEGIE_ESPORTAZIONE[formato]
  if (!strategia) {
    throw new Error(
      `Formato sconosciuto: ${formato}. Disponibili: ${Object.keys(STRATEGIE_ESPORTAZIONE).join(', ')}`,
    )
  }
  return strategia(dati)
}
```

### Observer con `EventTarget`

```javascript
// EventTarget è nativo: non serve scrivere un emettitore di eventi
class GestoreCarrello extends EventTarget {
  #righe = []

  aggiungi(prodotto, quantita = 1) {
    const esistente = this.#righe.find((r) => r.prodotto.id === prodotto.id)

    if (esistente) {
      esistente.quantita += quantita
    } else {
      this.#righe = [...this.#righe, { prodotto, quantita }]
    }

    this.dispatchEvent(
      new CustomEvent('carrello:modificato', {
        detail: { righe: this.righe, totale: this.totale },
      }),
    )
  }

  get righe() {
    return structuredClone(this.#righe)
  }

  get totale() {
    return this.#righe.reduce((s, r) => s + r.prodotto.prezzo * r.quantita, 0)
  }
}

const carrello = new GestoreCarrello()

carrello.addEventListener('carrello:modificato', (evento) => {
  aggiornaContatore(evento.detail.righe.length)
})

carrello.addEventListener('carrello:modificato', (evento) => {
  aggiornaTotale(evento.detail.totale)
})
```

Il vantaggio di `EventTarget` sull'emettitore scritto a mano: `once`, `signal` e `AbortController` funzionano già, e chi conosce gli eventi del DOM non deve imparare un'API nuova.

### Repository: isolare l'accesso ai dati

```javascript
/**
 * Chi usa il repository non sa se i dati vengono da un'API,
 * da IndexedDB o da un array in memoria. È ciò che rende
 * possibile testare senza rete.
 */
class RepositoryFatture {
  #recupera

  constructor({ recupera = globalThis.fetch } = {}) {
    this.#recupera = recupera
  }

  async elenca({ cliente, pagata, pagina = 1, perPagina = 50 } = {}) {
    const parametri = new URLSearchParams({ pagina, perPagina })
    if (cliente) parametri.set('cliente', cliente)
    if (pagata !== undefined) parametri.set('pagata', String(pagata))

    const risposta = await this.#recupera(`/api/fatture?${parametri}`)
    if (!risposta.ok) throw new ErroreHttp(risposta, null)

    return risposta.json()
  }

  async trova(id) {
    const risposta = await this.#recupera(`/api/fatture/${id}`)
    if (risposta.status === 404) return null
    if (!risposta.ok) throw new ErroreHttp(risposta, null)
    return risposta.json()
  }

  async salva(fattura) {
    const nuova = fattura.id === undefined
    const risposta = await this.#recupera(
      nuova ? '/api/fatture' : `/api/fatture/${fattura.id}`,
      {
        method: nuova ? 'POST' : 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(fattura),
      },
    )
    if (!risposta.ok) throw new ErroreHttp(risposta, null)
    return risposta.json()
  }
}

// Nei test, un finto fetch al posto di quello vero
const repositoryFinto = new RepositoryFatture({
  recupera: async () => new Response(JSON.stringify({ elementi: [] }), { status: 200 }),
})
```

### Modulo con stato privato

```javascript
// Le proprietà private con # rendono privato ciò che prima
// richiedeva le closure — e senza il costo di una funzione
// per ogni istanza.
class ArchivioLocale {
  #prefisso
  #serializza
  #deserializza

  constructor(prefisso, { serializza = JSON.stringify, deserializza = JSON.parse } = {}) {
    this.#prefisso = prefisso
    this.#serializza = serializza
    this.#deserializza = deserializza
  }

  #chiave(nome) {
    return `${this.#prefisso}:${nome}`
  }

  leggi(nome, predefinito = null) {
    try {
      const grezzo = localStorage.getItem(this.#chiave(nome))
      return grezzo === null ? predefinito : this.#deserializza(grezzo)
    } catch {
      return predefinito
    }
  }

  scrivi(nome, valore) {
    try {
      localStorage.setItem(this.#chiave(nome), this.#serializza(valore))
      return true
    } catch (errore) {
      // QuotaExceededError, o modalità privata su alcuni browser
      console.warn('Scrittura non riuscita', errore)
      return false
    }
  }

  rimuovi(nome) {
    localStorage.removeItem(this.#chiave(nome))
  }
}
```

### Costruttore fluente, quando i parametri sono molti

```javascript
class CostruttoreRichiesta {
  #url
  #opzioni = { headers: {} }

  constructor(url) {
    this.#url = url
  }

  metodo(m) {
    this.#opzioni.method = m
    return this
  }

  intestazione(nome, valore) {
    this.#opzioni.headers[nome] = valore
    return this
  }

  json(corpo) {
    this.#opzioni.body = JSON.stringify(corpo)
    this.#opzioni.headers['Content-Type'] = 'application/json'
    return this
  }

  timeout(millisecondi) {
    this.#opzioni.signal = AbortSignal.timeout(millisecondi)
    return this
  }

  async invia() {
    const risposta = await fetch(this.#url, this.#opzioni)
    if (!risposta.ok) throw new ErroreHttp(risposta, null)
    return risposta.json()
  }
}

const esito = await new CostruttoreRichiesta('/api/fatture')
  .metodo('POST')
  .intestazione('X-Richiesta-Id', crypto.randomUUID())
  .json({ cliente: 'Rossi', importo: 1200 })
  .timeout(5000)
  .invia()
```

---

## B5. Web Workers

Un Worker esegue JavaScript su un **thread separato**. È l'unico modo di fare un calcolo pesante senza congelare l'interfaccia.

```javascript
// src/main.js
const lavoratore = new Worker(new URL('./calcolo.worker.js', import.meta.url), {
  type: 'module',
})

lavoratore.postMessage({ tipo: 'analizza', dati: milioneDiRighe })

lavoratore.addEventListener('message', (evento) => {
  const { tipo, risultato, avanzamento } = evento.data

  if (tipo === 'avanzamento') aggiornaBarra(avanzamento)
  if (tipo === 'completato') mostraRisultato(risultato)
})

lavoratore.addEventListener('error', (evento) => {
  console.error('errore nel worker:', evento.message, evento.filename, evento.lineno)
})

// Terminarlo quando non serve più: un Worker vivo consuma memoria
// lavoratore.terminate()
```

```javascript
// src/calcolo.worker.js
// Dentro un Worker NON esistono: document, window, localStorage.
// Esistono: fetch, IndexedDB, WebSocket, la maggior parte delle API.

self.addEventListener('message', (evento) => {
  const { tipo, dati } = evento.data

  if (tipo !== 'analizza') return

  const totale = dati.length
  const aggregati = new Map()

  for (let i = 0; i < totale; i++) {
    const riga = dati[i]
    const chiave = riga.categoria
    aggregati.set(chiave, (aggregati.get(chiave) ?? 0) + riga.importo)

    // Segnalare l'avanzamento ogni 10.000 righe
    if (i % 10_000 === 0) {
      self.postMessage({ tipo: 'avanzamento', avanzamento: i / totale })
    }
  }

  self.postMessage({
    tipo: 'completato',
    risultato: Object.fromEntries(aggregati),
  })
})
```

### Il costo del passaggio dei dati

```javascript
// postMessage usa l'algoritmo di clonazione strutturata:
// i dati vengono COPIATI, non condivisi. Su oggetti grandi
// la copia costa, e per un attimo la memoria è doppia.

// ✅ Trasferire invece di copiare: il buffer passa di proprietà
//    al Worker e diventa inutilizzabile nel thread di partenza.
const buffer = new ArrayBuffer(64 * 1024 * 1024)
lavoratore.postMessage({ buffer }, [buffer]) // il secondo argomento

console.log(buffer.byteLength) // 0  ← trasferito, non più utilizzabile
```

```
Cosa si può trasferire (zero copia):
  ArrayBuffer · MessagePort · ImageBitmap · OffscreenCanvas
  ReadableStream · WritableStream

Cosa NON si può clonare, e fa fallire postMessage:
  funzioni · Symbol · nodi del DOM · Proxy
  oggetti con metodi (i metodi si perdono, restano i dati)
```

### `MessageChannel` per una comunicazione strutturata

```javascript
// Un canale dedicato, invece di distinguere i messaggi per tipo
const canale = new MessageChannel()

lavoratore.postMessage({ tipo: 'canale' }, [canale.port2])

canale.port1.addEventListener('message', (evento) => {
  console.log('dal worker:', evento.data)
})
canale.port1.start()
```

### Richiesta e risposta con Promise

```javascript
/**
 * Avvolge un Worker in un'interfaccia a Promise:
 * chi chiama non vede i messaggi, vede una funzione asincrona.
 */
function creaClienteWorker(percorso) {
  const lavoratore = new Worker(percorso, { type: 'module' })
  const inAttesa = new Map()
  let prossimoId = 0

  lavoratore.addEventListener('message', (evento) => {
    const { id, risultato, errore } = evento.data
    const richiesta = inAttesa.get(id)
    if (!richiesta) return

    inAttesa.delete(id)
    if (errore) {
      richiesta.rifiuta(Object.assign(new Error(errore.message), errore))
    } else {
      richiesta.risolvi(risultato)
    }
  })

  return {
    chiama(metodo, argomenti, trasferibili = []) {
      const id = prossimoId++
      const { promise, resolve, reject } = Promise.withResolvers()
      inAttesa.set(id, { risolvi: resolve, rifiuta: reject })
      lavoratore.postMessage({ id, metodo, argomenti }, trasferibili)
      return promise
    },

    termina() {
      lavoratore.terminate()
      for (const { rifiuta } of inAttesa.values()) {
        rifiuta(new Error('Worker terminato'))
      }
      inAttesa.clear()
    },
  }
}

const cliente = creaClienteWorker(new URL('./calcolo.worker.js', import.meta.url))
const esito = await cliente.chiama('aggrega', [dati])
```

### I tre tipi di Worker

```
Dedicated Worker    un thread per una pagina
                    new Worker(...)

Shared Worker       condiviso fra più schede della stessa origine
                    new SharedWorker(...)
                    utile per una connessione WebSocket sola

Service Worker      proxy di rete, persiste oltre la pagina
                    caching offline, notifiche push
                    vedi tutorial_18_pwa_tecnologie_avanzate.md
```

**Quando un Worker conviene:** calcoli oltre i 50 ms, analisi di file grandi, crittografia, compressione, elaborazione di immagini. **Quando no:** il passaggio dei dati costa, e per operazioni brevi il costo supera il beneficio.

---

## B6. Il sistema dei moduli: ESM, CJS e interoperabilità

### Le differenze che producono errori

```javascript
// ESM: risoluzione STATICA, prima dell'esecuzione.
// L'import è sollevato: viene risolto prima di qualunque riga.
import { funzione } from './modulo.js'

funzione()
```

```javascript
// CJS: risoluzione a RUNTIME.
// require è una chiamata normale: può stare dentro un if.
const { funzione } = require('./modulo.js')

funzione()
```

```javascript
// ❌ In ESM questo è un errore di sintassi:
//    gli import non possono essere condizionali
// if (condizione) {
//   import { x } from './a.js'
// }

// ✅ L'import dinamico sì
if (condizione) {
  const { x } = await import('./a.js')
}
```

### Importare CJS da ESM

```javascript
// Un modulo CommonJS ha un solo export: module.exports.
// Da ESM arriva come export DI DEFAULT.

// modulo-cjs.cjs
// module.exports = { a: 1, b: 2 }

// ❌ Gli export con nome non sempre funzionano:
//    Node prova ad analizzarli staticamente e non sempre ci riesce
// import { a, b } from './modulo-cjs.cjs'

// ✅ Import di default, sempre affidabile
import moduloCjs from './modulo-cjs.cjs'
const { a, b } = moduloCjs
```

```javascript
// createRequire, quando serve require dentro un modulo ESM
import { createRequire } from 'node:module'
const require = createRequire(import.meta.url)

const pacchetto = require('./package.json')
```

### Da CJS non si importa ESM in modo sincrono

```javascript
// ❌ require di un modulo ESM fallisce:
//    ERR_REQUIRE_ESM
// const modulo = require('./modulo-esm.js')

// ✅ Import dinamico, che restituisce una Promise
async function carica() {
  const modulo = await import('./modulo-esm.js')
  return modulo.funzione()
}
```

### Gli equivalenti di `__dirname` e `__filename`

```javascript
// In ESM non esistono. Da Node 20.11 ci sono gli equivalenti diretti:
console.log(import.meta.dirname)
console.log(import.meta.filename)

// La forma compatibile con versioni precedenti
import { fileURLToPath } from 'node:url'
import { dirname } from 'node:path'

const percorsoFile = fileURLToPath(import.meta.url)
const cartella = dirname(percorsoFile)

// Risolvere un percorso relativo al modulo
const percorsoDati = new URL('./dati.json', import.meta.url)
```

### Gli export condizionali del `package.json`

```json
{
  "name": "@azienda/libreria",
  "type": "module",
  "exports": {
    ".": {
      "types": "./dist/indice.d.ts",
      "import": "./dist/indice.js",
      "require": "./dist/indice.cjs",
      "default": "./dist/indice.js"
    },
    "./utility": {
      "types": "./dist/utility.d.ts",
      "import": "./dist/utility.js"
    },
    "./package.json": "./package.json"
  },
  "sideEffects": false
}
```

```
Due campi che vale la pena capire:

  "exports"      dichiara COSA è importabile. Ciò che non è
                 elencato diventa inaccessibile, anche se il file
                 esiste. È una funzionalità, non un limite:
                 impedisce a chi usa la libreria di dipendere
                 da percorsi interni che cambieranno.

  "sideEffects"  con false, dichiari che importare un modulo
                 non produce effetti collaterali. È ciò che
                 permette al bundler di eliminare il codice
                 non usato — il tree shaking.
                 Se un file registra qualcosa o importa CSS,
                 va elencato:  "sideEffects": ["*.css"]
```

---

## B7. Strategie di gestione degli errori

### Una gerarchia propria

```javascript
/** La radice: permette di distinguere i propri errori da quelli altrui. */
class ErroreApplicativo extends Error {
  constructor(messaggio, opzioni = {}) {
    super(messaggio, opzioni)
    this.name = this.constructor.name
    this.codice = opzioni.codice ?? 'ERRORE_GENERICO'
    this.contesto = opzioni.contesto ?? {}
    // Rimuove il costruttore dalla traccia, dove supportato
    Error.captureStackTrace?.(this, this.constructor)
  }

  /** Forma serializzabile, per i log e le risposte HTTP. */
  toJSON() {
    return {
      name: this.name,
      codice: this.codice,
      message: this.message,
      contesto: this.contesto,
      cause: this.cause instanceof Error ? this.cause.message : this.cause,
    }
  }
}

class ErroreValidazione extends ErroreApplicativo {
  constructor(campi, opzioni = {}) {
    const elenco = Object.keys(campi).join(', ')
    super(`Validazione fallita: ${elenco}`, { ...opzioni, codice: 'VALIDAZIONE' })
    this.campi = campi
  }
}

class ErroreAutorizzazione extends ErroreApplicativo {
  constructor(risorsa, azione, opzioni = {}) {
    super(`Non autorizzato: ${azione} su ${risorsa}`, { ...opzioni, codice: 'AUTORIZZAZIONE' })
    this.risorsa = risorsa
    this.azione = azione
  }
}

class ErroreNonTrovato extends ErroreApplicativo {
  constructor(tipo, id, opzioni = {}) {
    super(`${tipo} ${id} non trovato`, { ...opzioni, codice: 'NON_TROVATO' })
    this.tipo = tipo
    this.id = id
  }
}
```

```javascript
// La gestione diventa una tabella, non una catena di if
const GESTORI = new Map([
  [ErroreValidazione, (e) => ({ stato: 422, corpo: { errori: e.campi } })],
  [ErroreAutorizzazione, (e) => ({ stato: 403, corpo: { messaggio: e.message } })],
  [ErroreNonTrovato, () => ({ stato: 404, corpo: { messaggio: 'Risorsa non trovata' } })],
])

function traduciErrore(errore) {
  for (const [Tipo, gestore] of GESTORI) {
    if (errore instanceof Tipo) return gestore(errore)
  }

  // Ciò che non conosci non va esposto all'utente
  console.error('errore non gestito', errore)
  return { stato: 500, corpo: { messaggio: 'Errore interno' } }
}
```

### La catena delle cause

```javascript
/** Stampa la catena completa, dal più esterno al più interno. */
function descriviCatena(errore) {
  const righe = []
  let corrente = errore
  let livello = 0

  while (corrente && livello < 10) {
    righe.push(`${'  '.repeat(livello)}${corrente.name}: ${corrente.message}`)
    corrente = corrente.cause
    livello++
  }

  return righe.join('\n')
}
```

```javascript
// L'uso: ogni livello aggiunge il proprio contesto senza
// cancellare quello sottostante
async function elaboraOrdine(id) {
  try {
    const ordine = await caricaOrdine(id)
    return await addebitaPagamento(ordine)
  } catch (errore) {
    throw new ErroreApplicativo(`Ordine ${id} non elaborato`, {
      cause: errore,
      codice: 'ORDINE_FALLITO',
      contesto: { ordineId: id },
    })
  }
}
```

```
# Output atteso di descriviCatena:
ErroreApplicativo: Ordine 4271 non elaborato
  ErroreHttp: 502 Bad Gateway — https://pagamenti.esempio.it/addebita
    TypeError: fetch failed
```

### `safeTry`: risultati senza monadi

```javascript
/**
 * Converte una funzione che può sollevare in una che restituisce
 * una tupla [errore, valore]. È il pattern di Go, e funziona bene
 * quando l'errore è un esito previsto.
 */
async function safeTry(promessa) {
  try {
    return [null, await promessa]
  } catch (errore) {
    return [errore, null]
  }
}

// L'uso: nessun try/catch annidato, e l'errore non si può ignorare
async function caricaPagina(id) {
  const [erroreUtente, utente] = await safeTry(recuperaUtente(id))
  if (erroreUtente) return mostraErrore('Utente non disponibile', erroreUtente)

  const [erroreOrdini, ordini] = await safeTry(recuperaOrdini(utente.id))
  if (erroreOrdini) {
    // Un fallimento parziale accettabile: si prosegue senza ordini
    console.warn('ordini non caricati', erroreOrdini)
    return disegna({ utente, ordini: [] })
  }

  return disegna({ utente, ordini })
}
```

### I gestori globali

```javascript
// src/telemetria.js — la rete di sicurezza

const CODA_ERRORI = []
let invioProgrammato = false

function registraErrore(dettagli) {
  CODA_ERRORI.push({
    ...dettagli,
    quando: new Date().toISOString(),
    url: location.href,
    agente: navigator.userAgent,
  })

  if (!invioProgrammato) {
    invioProgrammato = true
    // Raggruppare gli invii evita una richiesta per errore
    setTimeout(svuotaCoda, 2000)
  }
}

function svuotaCoda() {
  invioProgrammato = false
  if (CODA_ERRORI.length === 0) return

  const lotto = CODA_ERRORI.splice(0, CODA_ERRORI.length)

  // sendBeacon sopravvive alla chiusura della pagina, fetch no
  const corpo = JSON.stringify({ errori: lotto })
  if (navigator.sendBeacon) {
    navigator.sendBeacon('/api/telemetria', new Blob([corpo], { type: 'application/json' }))
  } else {
    fetch('/api/telemetria', { method: 'POST', body: corpo, keepalive: true }).catch(() => {})
  }
}

// Errori JavaScript non catturati
window.addEventListener('error', (evento) => {
  registraErrore({
    tipo: 'errore',
    messaggio: evento.message,
    file: evento.filename,
    riga: evento.lineno,
    colonna: evento.colno,
    traccia: evento.error?.stack,
  })
})

// Risorse che non si caricano (immagini, script, CSS).
// Questi eventi NON fanno bubbling: serve la fase di cattura.
window.addEventListener(
  'error',
  (evento) => {
    if (evento.target !== window) {
      registraErrore({
        tipo: 'risorsa',
        elemento: evento.target.tagName,
        url: evento.target.src || evento.target.href,
      })
    }
  },
  true,
)

// Promise rifiutate senza .catch()
window.addEventListener('unhandledrejection', (evento) => {
  registraErrore({
    tipo: 'promise',
    messaggio: evento.reason?.message ?? String(evento.reason),
    traccia: evento.reason?.stack,
  })
  evento.preventDefault() // evita il messaggio nella console
})

// Invio anche quando la pagina viene chiusa
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') svuotaCoda()
})
```

---

## B8. Performance: misurare prima di ottimizzare

### Gli strumenti di misura

```javascript
// performance.now(): monotono e ad alta risoluzione.
// Date.now() può andare all'indietro se l'orologio di sistema cambia.
const inizio = performance.now()
operazione()
console.log(`${(performance.now() - inizio).toFixed(2)} ms`)

// mark e measure: le misure compaiono nel pannello Performance
performance.mark('analisi:inizio')
analizzaDati()
performance.mark('analisi:fine')
performance.measure('analisi', 'analisi:inizio', 'analisi:fine')

for (const misura of performance.getEntriesByType('measure')) {
  console.log(misura.name, misura.duration.toFixed(2))
}
```

```javascript
// PerformanceObserver: osserva senza interrogare
const osservatore = new PerformanceObserver((elenco) => {
  for (const voce of elenco.getEntries()) {
    if (voce.duration > 50) {
      console.warn(`Long task: ${voce.duration.toFixed(0)} ms`, voce.attribution)
    }
  }
})

osservatore.observe({ entryTypes: ['longtask', 'measure'] })
```

Un *long task* è un compito che occupa il thread principale per oltre 50 ms: durante quel tempo la pagina non risponde ai clic. È la metrica che spiega la maggior parte delle interfacce percepite come lente.

### Un benchmark onesto

```javascript
/**
 * Confronta due implementazioni. Il riscaldamento non è opzionale:
 * le prime esecuzioni girano nell'interprete, e misurarle
 * confronta il compilatore, non il codice.
 */
function confronta(implementazioni, { iterazioni = 100_000, riscaldamento = 5_000 } = {}) {
  const esiti = []

  for (const [nome, funzione] of Object.entries(implementazioni)) {
    for (let i = 0; i < riscaldamento; i++) funzione()

    // Tre esecuzioni, si tiene la mediana: attenua il rumore
    const tempi = []
    for (let ripetizione = 0; ripetizione < 3; ripetizione++) {
      const inizio = performance.now()
      for (let i = 0; i < iterazioni; i++) funzione()
      tempi.push(performance.now() - inizio)
    }

    tempi.sort((a, b) => a - b)
    esiti.push({ nome, millisecondi: tempi[1] })
  }

  esiti.sort((a, b) => a.millisecondi - b.millisecondi)
  const migliore = esiti[0].millisecondi

  for (const { nome, millisecondi } of esiti) {
    const rapporto = (millisecondi / migliore).toFixed(2)
    console.log(`${nome.padEnd(28)} ${millisecondi.toFixed(1).padStart(8)} ms  ×${rapporto}`)
  }

  return esiti
}
```

### Le ottimizzazioni che hanno un effetto reale

```javascript
// 1. La complessità algoritmica batte ogni micro-ottimizzazione
const grande = Array.from({ length: 50_000 }, (_, i) => ({ id: i }))
const cercati = Array.from({ length: 5_000 }, (_, i) => i * 7)

// ❌ O(n × m) — con questi numeri, 250 milioni di confronti
const lento = cercati.filter((id) => grande.some((e) => e.id === id))

// ✅ O(n + m) — un solo passaggio per costruire l'indice
const indice = new Set(grande.map((e) => e.id))
const veloce = cercati.filter((id) => indice.has(id))

// 2. Evitare il lavoro ripetuto nei cicli
// ❌ Intl.NumberFormat costruito a ogni giro
// righe.map((r) => new Intl.NumberFormat('it-IT').format(r.importo))

// ✅ Costruito una volta
const formattatore = new Intl.NumberFormat('it-IT')
// righe.map((r) => formattatore.format(r.importo))

// 3. Ridurre i passaggi sull'array quando è grande
// ❌ Tre passaggi e due array intermedi
// const esito = dati.filter(a).map(b).filter(c)

// ✅ Un passaggio solo
// const esito = dati.reduce((acc, x) => { ... }, [])

// 4. Non forzare il layout dentro un ciclo
// ❌ Ogni lettura di offsetHeight dopo una scrittura forza
//    un ricalcolo sincrono del layout: è il layout thrashing
for (const elemento of elementi) {
  elemento.style.height = `${elemento.offsetHeight * 2}px`
}

// ✅ Leggere tutto, poi scrivere tutto
const altezze = elementi.map((e) => e.offsetHeight)
for (const [indice, elemento] of elementi.entries()) {
  elemento.style.height = `${altezze[indice] * 2}px`
}
```

### Il criterio

```
L'ordine in cui cercare i problemi di prestazioni:

  1. La rete            richieste inutili, payload enormi,
                        assenza di cache
  2. L'algoritmo        O(n²) dove basterebbe O(n)
  3. Il rendering       layout thrashing, animazioni che
                        richiedono paint
  4. Il thread          long task che bloccano l'interazione
  5. La memoria         leak che degradano nel tempo
  6. Il micro-codice    ← quasi mai il problema

Ottimizzare al livello 6 prima di aver escluso i livelli 1-5
produce codice meno leggibile in cambio di guadagni impercettibili.
```

---

# Parte C — Esercizi Pratici Guidati

---

## C1. Esercizi progressivi con soluzione

### Esercizio 1 — Convertire una piramide di callback

**Obiettivo:** riscrivere una catena di callback con `async`/`await`, aggiungendo la gestione degli errori e il parallelismo dove le operazioni sono indipendenti.

```javascript
// PARTENZA — quattro livelli, gestione dell'errore ripetuta,
// e tre richieste indipendenti eseguite in sequenza
function caricaCruscotto(idUtente, callback) {
  recuperaUtente(idUtente, (errore, utente) => {
    if (errore) return callback(errore)

    recuperaOrdini(utente.id, (errore, ordini) => {
      if (errore) return callback(errore)

      recuperaFatture(utente.id, (errore, fatture) => {
        if (errore) return callback(errore)

        recuperaNotifiche(utente.id, (errore, notifiche) => {
          if (errore) return callback(errore)

          callback(null, { utente, ordini, fatture, notifiche })
        })
      })
    })
  })
}
```

```javascript
// SOLUZIONE

/**
 * Le tre richieste dopo l'utente sono INDIPENDENTI fra loro:
 * dipendono solo da utente.id. Vanno in parallelo.
 */
async function caricaCruscotto(idUtente, { signal } = {}) {
  // Passo 1: necessariamente sequenziale, serve utente.id
  const utente = await recuperaUtente(idUtente, { signal })

  // Passo 2: le tre in parallelo. allSettled invece di all,
  // perché un fallimento parziale non deve svuotare la pagina.
  const [esitoOrdini, esitoFatture, esitoNotifiche] = await Promise.allSettled([
    recuperaOrdini(utente.id, { signal }),
    recuperaFatture(utente.id, { signal }),
    recuperaNotifiche(utente.id, { signal }),
  ])

  const problemi = []

  function valoreOppure(esito, predefinito, nome) {
    if (esito.status === 'fulfilled') return esito.value
    problemi.push({ sezione: nome, errore: esito.reason })
    return predefinito
  }

  return {
    utente,
    ordini: valoreOppure(esitoOrdini, [], 'ordini'),
    fatture: valoreOppure(esitoFatture, [], 'fatture'),
    notifiche: valoreOppure(esitoNotifiche, [], 'notifiche'),
    problemi,
  }
}
```

```javascript
// L'uso, con annullamento e timeout
const controller = new AbortController()

async function mostraCruscotto(idUtente) {
  try {
    const cruscotto = await caricaCruscotto(idUtente, {
      signal: AbortSignal.any([controller.signal, AbortSignal.timeout(10_000)]),
    })

    disegna(cruscotto)

    for (const { sezione, errore } of cruscotto.problemi) {
      console.warn(`Sezione ${sezione} non disponibile:`, errore.message)
      mostraAvvisoParziale(sezione)
    }
  } catch (errore) {
    if (errore.name === 'AbortError') return
    if (errore.name === 'TimeoutError') return mostraErrore('Il server non risponde.')
    mostraErrore('Impossibile caricare il cruscotto.')
  }
}
```

```
# Cosa è cambiato, e perché:
#
# 1. QUATTRO livelli di annidamento → zero.
#    Il codice si legge dall'alto in basso.
#
# 2. QUATTRO gestioni identiche dell'errore → una sola,
#    nel try del chiamante.
#
# 3. Le tre richieste indipendenti erano SEQUENZIALI.
#    Con 100 ms di latenza ciascuna:
#      prima:  100 + 100 + 100 + 100 = 400 ms
#      dopo:   100 + max(100, 100, 100) = 200 ms
#
# 4. allSettled invece di all: se le notifiche falliscono,
#    la dashboard mostra comunque ordini e fatture.
#    Con Promise.all, un solo fallimento avrebbe svuotato tutto.
#
# 5. AbortSignal.any combina annullamento dell'utente e timeout:
#    l'utente che cambia pagina non lascia richieste appese.
#
# L'ERRORE DA NON FARE nella conversione:
#   mettere tutti e quattro gli await in sequenza.
#   È la traduzione letterale del callback, e conserva
#   il difetto peggiore dell'originale.
```

---

### Esercizio 2 — Recupero con concorrenza limitata e ritentativi

**Obiettivo:** scaricare 200 risorse con al massimo 6 richieste in volo, ritentando quelle che falliscono per motivi transitori.

```javascript
// SOLUZIONE

class ErroreHttp extends Error {
  constructor(risposta) {
    super(`${risposta.status} ${risposta.statusText} — ${risposta.url}`)
    this.name = 'ErroreHttp'
    this.stato = risposta.status
  }

  get eRipetibile() {
    return this.stato === 408 || this.stato === 429 || this.stato >= 500
  }
}

/** Attende, ma si interrompe subito se il segnale viene attivato. */
function attendi(millisecondi, signal) {
  return new Promise((risolvi, rifiuta) => {
    const temporizzatore = setTimeout(risolvi, millisecondi)
    signal?.addEventListener(
      'abort',
      () => {
        clearTimeout(temporizzatore)
        rifiuta(signal.reason)
      },
      { once: true },
    )
  })
}

async function conRitentativi(operazione, { tentativiMassimi = 3, attesaIniziale = 300, signal } = {}) {
  let ultimoErrore = null

  for (let tentativo = 1; tentativo <= tentativiMassimi; tentativo++) {
    signal?.throwIfAborted()

    try {
      return await operazione()
    } catch (errore) {
      ultimoErrore = errore

      if (errore.name === 'AbortError') throw errore
      if (errore instanceof ErroreHttp && !errore.eRipetibile) throw errore
      if (tentativo === tentativiMassimi) break

      // Backoff esponenziale con jitter completo
      const base = attesaIniziale * 2 ** (tentativo - 1)
      await attendi(Math.random() * base, signal)
    }
  }

  throw new Error(`Fallito dopo ${tentativiMassimi} tentativi`, { cause: ultimoErrore })
}

/**
 * N operai consumano dalla stessa coda: la concorrenza
 * resta costante anche quando le operazioni hanno durate diverse.
 */
async function conConcorrenza(elementi, operazione, { limite = 6, signal } = {}) {
  const esiti = new Array(elementi.length)
  let prossimo = 0

  async function operaio() {
    while (prossimo < elementi.length) {
      signal?.throwIfAborted()

      const indice = prossimo++
      try {
        esiti[indice] = { status: 'fulfilled', value: await operazione(elementi[indice], indice) }
      } catch (errore) {
        if (errore.name === 'AbortError') throw errore
        esiti[indice] = { status: 'rejected', reason: errore }
      }
    }
  }

  await Promise.all(Array.from({ length: Math.min(limite, elementi.length) }, operaio))
  return esiti
}
```

```javascript
// La composizione: concorrenza limitata + ritentativi + avanzamento
async function scaricaTutto(url, { limite = 6, alProgresso, signal } = {}) {
  let completati = 0

  const esiti = await conConcorrenza(
    url,
    async (singolo) => {
      const dati = await conRitentativi(
        async () => {
          const risposta = await fetch(singolo, { signal })
          if (!risposta.ok) throw new ErroreHttp(risposta)
          return risposta.json()
        },
        { tentativiMassimi: 3, signal },
      )

      completati++
      alProgresso?.(completati / url.length)
      return dati
    },
    { limite, signal },
  )

  return {
    riusciti: esiti.filter((e) => e.status === 'fulfilled').map((e) => e.value),
    falliti: esiti
      .map((e, indice) => ({ e, url: url[indice] }))
      .filter(({ e }) => e.status === 'rejected')
      .map(({ e, url }) => ({ url, errore: e.reason })),
  }
}
```

```javascript
// Uso
const indirizzi = Array.from({ length: 200 }, (_, i) => `/api/risorse/${i}`)

const { riusciti, falliti } = await scaricaTutto(indirizzi, {
  limite: 6,
  alProgresso: (frazione) => aggiornaBarra(Math.round(frazione * 100)),
  signal: AbortSignal.timeout(120_000),
})

console.log(`${riusciti.length} riusciti, ${falliti.length} falliti`)
for (const { url, errore } of falliti) {
  console.warn(url, errore.message)
}
```

```
# Output atteso:
196 riusciti, 4 falliti
/api/risorse/37 Fallito dopo 3 tentativi
/api/risorse/91 404 Not Found — /api/risorse/91
...
```

```
# Le decisioni di progetto:
#
# CONCORRENZA A OPERAI, non a lotti.
#   Con Promise.all su lotti da 6, il lotto successivo parte
#   solo quando l'ULTIMO del lotto precedente è finito:
#   una richiesta lenta blocca cinque operai inattivi.
#   Con gli operai, chi finisce prende subito il prossimo.
#
# JITTER COMPLETO (Math.random() * base) invece di base fissa.
#   Duecento richieste che falliscono per un 503 momentaneo
#   ritenterebbero tutte nello stesso millisecondo, riproducendo
#   il picco. È il thundering herd.
#
# RIPETIBILE SOLO SE HA SENSO.
#   Un 404 non diventa 200 ritentando. Un 400 nemmeno.
#   Ritentare quelli spreca tempo e carica il server.
#
# AbortError PROPAGATO, non trasformato in un esito fallito.
#   L'annullamento non è un fallimento della singola risorsa:
#   è la fine dell'intera operazione.
#
# ESITI PER INDICE, non per ordine di completamento.
#   esiti[indice] conserva la corrispondenza con l'input,
#   che con gli operai si perderebbe.
```

---

### Esercizio 3 — Prevedere l'ordine dell'event loop con async

**Obiettivo:** dire l'ordine esatto, poi eseguire.

```javascript
// PROBLEMA
async function a() {
  console.log('a1')
  await b()
  console.log('a2')
}

async function b() {
  console.log('b1')
  await null
  console.log('b2')
}

console.log('inizio')

setTimeout(() => console.log('timeout'), 0)

a()

Promise.resolve()
  .then(() => console.log('p1'))
  .then(() => console.log('p2'))
  .then(() => console.log('p3'))

console.log('fine')
```

```
# SOLUZIONE: inizio a1 b1 fine b2 p1 a2 p2 p3 timeout
#
# Il ragionamento:
#
# ── FASE SINCRONA ────────────────────────────────────────────
#   'inizio'
#   setTimeout → MACROTASK M1
#   a() parte SINCRONA:
#     'a1'
#     await b() → b() parte SINCRONA:
#       'b1'
#       await null → il resto di b (stampa 'b2') diventa
#                    la MICROTASK m1
#       b() restituisce una Promise pending
#     await su quella Promise → il resto di a (stampa 'a2')
#                               attende che b si risolva
#   Promise.resolve().then(...) → MICROTASK m2 ('p1')
#   'fine'
#
#   Stampato: inizio, a1, b1, fine
#   Coda microtask: [m1='b2', m2='p1']
#
# ── SVUOTAMENTO DEI MICROTASK ────────────────────────────────
#   m1 → 'b2'
#        b() termina e la sua Promise si risolve.
#        Questo sblocca l'await in a(), che accoda
#        il proprio proseguimento: m3 ('a2') IN FONDO.
#
#   m2 → 'p1'
#        il .then concatenato accoda m4 ('p2') in fondo.
#
#   m3 → 'a2'
#
#   m4 → 'p2'
#        accoda m5 ('p3').
#
#   m5 → 'p3'
#
#   Stampato: inizio a1 b1 fine b2 p1 a2 p2 p3
#
# ── MACROTASK ────────────────────────────────────────────────
#   M1 → 'timeout'
#
#
# IL PUNTO CHE CONFONDE:
#   'a2' arriva DOPO 'p1' anche se a() è stata chiamata prima.
#   Il motivo: quando b() si risolve (durante m1), il
#   proseguimento di a() viene accodato IN FONDO alla coda,
#   dove m2 ('p1') era già in attesa.
#
#   Attendere una funzione async costa un giro di coda in più
#   rispetto ad attendere una Promise già risolta.
```

```javascript
// La variante che dimostra il costo dell'attesa annidata
async function conAwaitAnnidato() {
  await Promise.resolve()
  await Promise.resolve()
  await Promise.resolve()
  console.log('tre await')
}

Promise.resolve()
  .then(() => console.log('then 1'))
  .then(() => console.log('then 2'))
  .then(() => console.log('then 3'))
  .then(() => console.log('then 4'))

conAwaitAnnidato()

// Output: then 1, then 2, then 3, tre await, then 4
// Ogni await consuma un giro della coda dei microtask.
```

---

### Esercizio 4 — Un `Proxy` che registra e valida

**Obiettivo:** costruire un wrapper che intercetti lettura, scrittura e cancellazione di un oggetto di configurazione, validando i valori e segnalando gli accessi a chiavi inesistenti.

```javascript
// SOLUZIONE

/**
 * Avvolge un oggetto di configurazione con:
 *   · validazione all'assegnazione
 *   · errore sulle chiavi inesistenti (intercetta i refusi)
 *   · sola lettura dopo il congelamento
 *   · registro di tutti gli accessi, per il debug
 */
function creaConfigurazione(valoriIniziali, schema, { nome = 'configurazione' } = {}) {
  const registro = []
  let congelata = false

  function valida(chiave, valore) {
    const regola = schema[chiave]
    if (!regola) return

    if (regola.tipo && typeof valore !== regola.tipo) {
      throw new TypeError(
        `${nome}.${chiave}: atteso ${regola.tipo}, ricevuto ${typeof valore}`,
      )
    }

    if (regola.valori && !regola.valori.includes(valore)) {
      throw new RangeError(
        `${nome}.${chiave}: valore non ammesso "${valore}". ` +
          `Ammessi: ${regola.valori.join(', ')}`,
      )
    }

    if (regola.verifica && !regola.verifica(valore)) {
      throw new RangeError(`${nome}.${chiave}: ${regola.messaggio ?? 'valore non valido'}`)
    }
  }

  // Validare anche i valori iniziali: un errore nella
  // configurazione predefinita deve emergere subito
  for (const [chiave, valore] of Object.entries(valoriIniziali)) {
    valida(chiave, valore)
  }

  const proxy = new Proxy({ ...valoriIniziali }, {
    get(bersaglio, chiave, ricevitore) {
      // I Symbol passano senza controlli: servono a
      // Symbol.toPrimitive, Symbol.iterator e simili
      if (typeof chiave === 'symbol') {
        return Reflect.get(bersaglio, chiave, ricevitore)
      }

      // I metodi di servizio non sono chiavi di configurazione
      if (chiave === '__registro') return [...registro]
      if (chiave === '__congela') {
        return () => {
          congelata = true
        }
      }

      if (!(chiave in bersaglio)) {
        throw new ReferenceError(
          `${nome}.${chiave} non esiste. ` +
            `Chiavi disponibili: ${Object.keys(bersaglio).join(', ')}`,
        )
      }

      registro.push({ operazione: 'lettura', chiave, quando: performance.now() })
      return Reflect.get(bersaglio, chiave, ricevitore)
    },

    set(bersaglio, chiave, valore, ricevitore) {
      if (congelata) {
        throw new TypeError(`${nome} è congelata: ${String(chiave)} non modificabile`)
      }

      valida(chiave, valore)

      registro.push({
        operazione: 'scrittura',
        chiave,
        precedente: bersaglio[chiave],
        valore,
        quando: performance.now(),
      })

      // Reflect.set inoltra il ricevitore e restituisce
      // il booleano che la trappola deve restituire
      return Reflect.set(bersaglio, chiave, valore, ricevitore)
    },

    deleteProperty(bersaglio, chiave) {
      if (congelata) {
        throw new TypeError(`${nome} è congelata: ${String(chiave)} non eliminabile`)
      }

      registro.push({ operazione: 'cancellazione', chiave, quando: performance.now() })
      return Reflect.deleteProperty(bersaglio, chiave)
    },

    // has intercetta l'operatore 'in'
    has(bersaglio, chiave) {
      return Reflect.has(bersaglio, chiave)
    },

    // ownKeys nasconde i metodi di servizio da Object.keys e spread
    ownKeys(bersaglio) {
      return Reflect.ownKeys(bersaglio)
    },
  })

  return proxy
}
```

```javascript
// Uso
const configurazione = creaConfigurazione(
  {
    porta: 3000,
    host: 'localhost',
    ambiente: 'sviluppo',
    livelloLog: 'info',
    timeout: 5000,
  },
  {
    porta: {
      tipo: 'number',
      verifica: (v) => Number.isInteger(v) && v > 0 && v < 65536,
      messaggio: 'deve essere una porta valida (1-65535)',
    },
    host: { tipo: 'string' },
    ambiente: { valori: ['sviluppo', 'collaudo', 'produzione'] },
    livelloLog: { valori: ['debug', 'info', 'warn', 'error'] },
    timeout: {
      tipo: 'number',
      verifica: (v) => v >= 100 && v <= 60_000,
      messaggio: 'deve essere fra 100 e 60000 ms',
    },
  },
)

// Lettura normale
console.log(configurazione.porta) // 3000

// Scrittura valida
configurazione.porta = 8080
console.log(configurazione.porta) // 8080

// Le tre validazioni
try {
  configurazione.porta = 'ottomila'
} catch (errore) {
  console.log(errore.message) // configurazione.porta: atteso number, ricevuto string
}

try {
  configurazione.porta = 99999
} catch (errore) {
  console.log(errore.message) // configurazione.porta: deve essere una porta valida (1-65535)
}

try {
  configurazione.ambiente = 'staging'
} catch (errore) {
  console.log(errore.message)
  // configurazione.ambiente: valore non ammesso "staging".
  // Ammessi: sviluppo, collaudo, produzione
}

// Il refuso viene intercettato invece di restituire undefined
try {
  console.log(configurazione.prota)
} catch (errore) {
  console.log(errore.message)
  // configurazione.prota non esiste.
  // Chiavi disponibili: porta, host, ambiente, livelloLog, timeout
}

// Congelamento
configurazione.__congela()
try {
  configurazione.porta = 9000
} catch (errore) {
  console.log(errore.message) // configurazione è congelata: porta non modificabile
}

// Il registro degli accessi
console.log(configurazione.__registro.filter((v) => v.operazione === 'scrittura'))
```

```
# Output atteso:
3000
8080
configurazione.porta: atteso number, ricevuto string
configurazione.porta: deve essere una porta valida (1-65535)
configurazione.ambiente: valore non ammesso "staging". Ammessi: sviluppo, collaudo, produzione
configurazione.prota non esiste. Chiavi disponibili: porta, host, ambiente, livelloLog, timeout
configurazione è congelata: porta non modificabile
[ { operazione: 'scrittura', chiave: 'porta', precedente: 3000, valore: 8080, quando: ... } ]
```

```
# I punti che fanno funzionare il Proxy:
#
# Reflect INVECE dell'operazione diretta.
#   Reflect.set inoltra il 'ricevitore' e restituisce il booleano
#   che la trappola deve restituire. Scrivendo bersaglio[chiave] = valore
#   e dimenticando il return, in strict mode l'assegnazione
#   solleva TypeError.
#
# I SYMBOL PASSANO SENZA CONTROLLI.
#   Senza il controllo su typeof chiave === 'symbol', qualunque
#   operazione che consulti Symbol.toPrimitive o Symbol.iterator —
#   console.log compreso — solleverebbe ReferenceError.
#
# LA VALIDAZIONE DEI VALORI INIZIALI.
#   Uno schema che accetta la configurazione predefinita
#   sbagliata non serve a nulla: l'errore emergerebbe
#   solo alla prima riassegnazione.
#
# IL REGISTRO È UNA COPIA.
#   __registro restituisce [...registro]: chi lo legge
#   non può modificarlo.
#
# QUANDO NON usare un Proxy per questo:
#   in un ciclo caldo, ogni accesso passa dalla trappola.
#   Per una configurazione letta all'avvio va benissimo;
#   per un oggetto letto un milione di volte al secondo, no.
```

---

### Esercizio 5 — Web Worker con interfaccia a Promise

**Obiettivo:** spostare un'elaborazione pesante su un thread separato, esponendo un'API che chi chiama usa come una normale funzione asincrona.

```javascript
// SOLUZIONE — src/aggregazione.worker.js

/**
 * Le operazioni disponibili. Ognuna è una funzione pura:
 * riceve dati, restituisce dati, non tocca nulla di esterno.
 */
const OPERAZIONI = {
  aggrega(righe, { campoChiave, campoValore }) {
    const totali = new Map()

    for (const riga of righe) {
      const chiave = riga[campoChiave]
      totali.set(chiave, (totali.get(chiave) ?? 0) + riga[campoValore])
    }

    return [...totali.entries()]
      .map(([chiave, totale]) => ({ chiave, totale }))
      .sort((a, b) => b.totale - a.totale)
  },

  statistiche(numeri) {
    const ordinati = [...numeri].sort((a, b) => a - b)
    const n = ordinati.length
    const somma = ordinati.reduce((s, v) => s + v, 0)
    const media = somma / n

    const varianza = ordinati.reduce((s, v) => s + (v - media) ** 2, 0) / n

    function percentile(p) {
      const posizione = (n - 1) * p
      const basso = Math.floor(posizione)
      const alto = Math.ceil(posizione)
      return basso === alto
        ? ordinati[basso]
        : ordinati[basso] + (posizione - basso) * (ordinati[alto] - ordinati[basso])
    }

    return {
      conteggio: n,
      somma,
      media,
      mediana: percentile(0.5),
      deviazione: Math.sqrt(varianza),
      p95: percentile(0.95),
      p99: percentile(0.99),
      minimo: ordinati[0],
      massimo: ordinati[n - 1],
    }
  },
}

self.addEventListener('message', async (evento) => {
  const { id, metodo, argomenti } = evento.data

  try {
    const operazione = OPERAZIONI[metodo]
    if (!operazione) {
      throw new Error(
        `Metodo sconosciuto: ${metodo}. Disponibili: ${Object.keys(OPERAZIONI).join(', ')}`,
      )
    }

    const risultato = await operazione(...argomenti)
    self.postMessage({ id, risultato })
  } catch (errore) {
    // Un Error non è clonabile: va scomposto nei suoi campi
    self.postMessage({
      id,
      errore: { name: errore.name, message: errore.message, stack: errore.stack },
    })
  }
})
```

```javascript
// SOLUZIONE — src/cliente-worker.js

/**
 * Avvolge un Worker in un'interfaccia a Promise.
 * Chi chiama scrive: await cliente.chiama('aggrega', [dati, opzioni])
 * e non vede mai un postMessage.
 */
export function creaClienteWorker(percorso, { concorrenzaMassima = 1 } = {}) {
  const lavoratori = Array.from({ length: concorrenzaMassima }, () => ({
    istanza: new Worker(percorso, { type: 'module' }),
    occupato: false,
  }))

  const inAttesa = new Map()
  const coda = []
  let prossimoId = 0

  for (const lavoratore of lavoratori) {
    lavoratore.istanza.addEventListener('message', (evento) => {
      const { id, risultato, errore } = evento.data
      const richiesta = inAttesa.get(id)

      lavoratore.occupato = false
      if (richiesta) {
        inAttesa.delete(id)
        if (errore) {
          const ricostruito = new Error(errore.message)
          ricostruito.name = errore.name
          ricostruito.stack = errore.stack
          richiesta.rifiuta(ricostruito)
        } else {
          richiesta.risolvi(risultato)
        }
      }

      serviCoda()
    })

    lavoratore.istanza.addEventListener('error', (evento) => {
      lavoratore.occupato = false
      // Un errore del worker non è associabile a una richiesta:
      // rifiuta tutto ciò che è in volo
      for (const [id, richiesta] of inAttesa) {
        richiesta.rifiuta(new Error(`Errore nel worker: ${evento.message}`))
        inAttesa.delete(id)
      }
      serviCoda()
    })
  }

  function serviCoda() {
    while (coda.length > 0) {
      const libero = lavoratori.find((l) => !l.occupato)
      if (!libero) return

      const compito = coda.shift()
      libero.occupato = true
      inAttesa.set(compito.id, compito)
      libero.istanza.postMessage(
        { id: compito.id, metodo: compito.metodo, argomenti: compito.argomenti },
        compito.trasferibili,
      )
    }
  }

  return {
    chiama(metodo, argomenti = [], trasferibili = []) {
      const { promise, resolve, reject } = Promise.withResolvers()

      coda.push({
        id: prossimoId++,
        metodo,
        argomenti,
        trasferibili,
        risolvi: resolve,
        rifiuta: reject,
      })

      serviCoda()
      return promise
    },

    termina() {
      for (const lavoratore of lavoratori) lavoratore.istanza.terminate()
      for (const richiesta of inAttesa.values()) {
        richiesta.rifiuta(new Error('Worker terminato'))
      }
      inAttesa.clear()
      coda.length = 0
    },
  }
}
```

```javascript
// L'uso, con il confronto che dimostra il beneficio
import { creaClienteWorker } from './cliente-worker.js'

const cliente = creaClienteWorker(new URL('./aggregazione.worker.js', import.meta.url), {
  concorrenzaMassima: navigator.hardwareConcurrency ?? 4,
})

const righe = Array.from({ length: 2_000_000 }, (_, i) => ({
  categoria: `cat-${i % 50}`,
  importo: Math.random() * 1000,
}))

// Un'animazione che rivela se il thread principale è bloccato
const indicatore = document.querySelector('#indicatore')
let angolo = 0
function ruota() {
  angolo = (angolo + 6) % 360
  indicatore.style.transform = `rotate(${angolo}deg)`
  requestAnimationFrame(ruota)
}
ruota()

// ❌ Sul thread principale: l'indicatore si ferma per tutta l'elaborazione
console.time('thread principale')
const suThread = aggregaSincrono(righe)
console.timeEnd('thread principale')

// ✅ Nel worker: l'indicatore continua a girare
console.time('worker')
const nelWorker = await cliente.chiama('aggrega', [
  righe,
  { campoChiave: 'categoria', campoValore: 'importo' },
])
console.timeEnd('worker')

cliente.termina()
```

```
# Output atteso:
thread principale: 1840.21 ms   ← e l'indicatore resta immobile
worker: 2210.55 ms              ← e l'indicatore gira fluido
```

```
# LA LETTURA CORRETTA DI QUESTI NUMERI:
#
# Il worker è PIÙ LENTO in tempo assoluto: 2210 contro 1840 ms.
# La differenza è il costo della clonazione strutturata —
# due milioni di oggetti copiati all'andata e il risultato
# copiato al ritorno.
#
# Eppure il worker è la scelta giusta, perché la metrica
# che conta per l'utente NON è il tempo totale: è se
# l'interfaccia risponde. Nel primo caso la pagina è
# congelata per 1,8 secondi; nel secondo non lo è mai.
#
# QUANDO IL WORKER NON CONVIENE:
#   · operazioni sotto i 50 ms: il costo del passaggio domina
#   · dati enormi da copiare e risultato piccolo
#     → valutare di generare i dati DENTRO il worker
#   · l'operazione richiede il DOM (nel worker non esiste)
#
# COME RIDURRE IL COSTO DEL PASSAGGIO:
#   · trasferire ArrayBuffer invece di clonare oggetti:
#       lavoratore.postMessage({ buffer }, [buffer])
#     Il trasferimento è a costo zero, ma il buffer
#     diventa inutilizzabile nel thread di partenza.
#   · usare un SharedArrayBuffer, dove i requisiti di
#     isolamento dell'origine lo permettono (vedi D2)
#   · far leggere i dati al worker direttamente
#     (fetch e IndexedDB funzionano nei worker)
#
# navigator.hardwareConcurrency dà il numero di core:
# aprire più worker di quelli disponibili non accelera nulla
# e consuma memoria.
```

---

### Esercizio 6 — Gerarchia di errori e catena delle cause

**Obiettivo:** costruire una gerarchia di errori che permetta di distinguere i casi, conservare la causa originale e produrre una risposta HTTP corretta.

```javascript
// SOLUZIONE — src/errori.js

export class ErroreApplicativo extends Error {
  constructor(messaggio, { causa, codice = 'ERRORE_GENERICO', contesto = {} } = {}) {
    super(messaggio, { cause: causa })
    this.name = this.constructor.name
    this.codice = codice
    this.contesto = contesto
    this.quando = new Date().toISOString()
    Error.captureStackTrace?.(this, this.constructor)
  }

  /** Lo stato HTTP corrispondente. Le sottoclassi lo ridefiniscono. */
  get statoHttp() {
    return 500
  }

  /** Ciò che l'utente può vedere. Non espone dettagli interni. */
  get messaggioPubblico() {
    return 'Si è verificato un errore.'
  }

  toJSON() {
    return {
      name: this.name,
      codice: this.codice,
      message: this.message,
      contesto: this.contesto,
      quando: this.quando,
      causa: this.cause instanceof Error ? this.cause.toJSON?.() ?? this.cause.message : this.cause,
    }
  }
}

export class ErroreValidazione extends ErroreApplicativo {
  constructor(campi, opzioni = {}) {
    super(`Validazione fallita su: ${Object.keys(campi).join(', ')}`, {
      ...opzioni,
      codice: 'VALIDAZIONE',
    })
    this.campi = campi
  }

  get statoHttp() {
    return 422
  }

  get messaggioPubblico() {
    return 'Alcuni campi non sono corretti.'
  }
}

export class ErroreNonTrovato extends ErroreApplicativo {
  constructor(tipo, identificativo, opzioni = {}) {
    super(`${tipo} ${identificativo} non trovato`, { ...opzioni, codice: 'NON_TROVATO' })
    this.tipo = tipo
    this.identificativo = identificativo
  }

  get statoHttp() {
    return 404
  }

  get messaggioPubblico() {
    return 'Risorsa non trovata.'
  }
}

export class ErroreAutorizzazione extends ErroreApplicativo {
  constructor(azione, risorsa, opzioni = {}) {
    super(`Non autorizzato: ${azione} su ${risorsa}`, { ...opzioni, codice: 'AUTORIZZAZIONE' })
    this.azione = azione
    this.risorsa = risorsa
  }

  get statoHttp() {
    return 403
  }

  get messaggioPubblico() {
    return 'Non hai i permessi per questa operazione.'
  }
}

export class ErroreServizioEsterno extends ErroreApplicativo {
  constructor(servizio, opzioni = {}) {
    super(`Il servizio ${servizio} non ha risposto correttamente`, {
      ...opzioni,
      codice: 'SERVIZIO_ESTERNO',
    })
    this.servizio = servizio
  }

  get statoHttp() {
    return 502
  }

  get messaggioPubblico() {
    return 'Un servizio esterno non è disponibile. Riprova fra qualche minuto.'
  }
}
```

```javascript
// src/diagnostica.js

/** Percorre la catena delle cause, dal più esterno al più interno. */
export function catenaDelleCause(errore, profonditaMassima = 10) {
  const catena = []
  let corrente = errore
  let livello = 0

  while (corrente instanceof Error && livello < profonditaMassima) {
    catena.push({
      livello,
      name: corrente.name,
      message: corrente.message,
      codice: corrente.codice ?? null,
      contesto: corrente.contesto ?? null,
    })
    corrente = corrente.cause
    livello++
  }

  return catena
}

export function descriviCatena(errore) {
  return catenaDelleCause(errore)
    .map(({ livello, name, message }) => `${'  '.repeat(livello)}${name}: ${message}`)
    .join('\n')
}

/** Cerca nella catena il primo errore di un tipo dato. */
export function trovaNellaCatena(errore, Tipo) {
  let corrente = errore
  while (corrente instanceof Error) {
    if (corrente instanceof Tipo) return corrente
    corrente = corrente.cause
  }
  return null
}
```

```javascript
// L'uso: ogni livello aggiunge contesto senza cancellare quello sotto

import {
  ErroreApplicativo,
  ErroreNonTrovato,
  ErroreServizioEsterno,
  ErroreValidazione,
} from './errori.js'
import { descriviCatena, trovaNellaCatena } from './diagnostica.js'

async function recuperaCliente(id) {
  const risposta = await fetch(`/api/clienti/${id}`)

  if (risposta.status === 404) {
    throw new ErroreNonTrovato('Cliente', id)
  }

  if (!risposta.ok) {
    throw new ErroreServizioEsterno('anagrafica', {
      contesto: { stato: risposta.status, url: risposta.url },
    })
  }

  return risposta.json()
}

async function creaFattura(datiFattura) {
  const campiInvalidi = {}
  if (!datiFattura.clienteId) campiInvalidi.clienteId = 'obbligatorio'
  if (!(datiFattura.importo > 0)) campiInvalidi.importo = 'deve essere positivo'

  if (Object.keys(campiInvalidi).length > 0) {
    throw new ErroreValidazione(campiInvalidi)
  }

  try {
    const cliente = await recuperaCliente(datiFattura.clienteId)
    return { ...datiFattura, cliente, numero: generaNumero() }
  } catch (errore) {
    // Si aggiunge contesto, si CONSERVA la causa
    throw new ErroreApplicativo('Fattura non creata', {
      causa: errore,
      codice: 'FATTURA_NON_CREATA',
      contesto: { clienteId: datiFattura.clienteId, importo: datiFattura.importo },
    })
  }
}

// Il gestore centrale: una funzione, non una catena di if
function rispondiAErrore(errore) {
  if (errore instanceof ErroreApplicativo) {
    // Il log interno contiene tutto
    console.error(descriviCatena(errore))
    console.error(JSON.stringify(errore.toJSON(), null, 2))

    // La risposta all'utente contiene solo ciò che può vedere
    const corpo = { codice: errore.codice, messaggio: errore.messaggioPubblico }
    if (errore instanceof ErroreValidazione) corpo.campi = errore.campi

    return { stato: errore.statoHttp, corpo }
  }

  console.error('errore non gestito', errore)
  return { stato: 500, corpo: { codice: 'INTERNO', messaggio: 'Errore interno.' } }
}
```

```javascript
// Test
try {
  await creaFattura({ clienteId: 9999, importo: 1200 })
} catch (errore) {
  console.log(descriviCatena(errore))

  // La catena permette di reagire alla causa PROFONDA,
  // non solo a quella superficiale
  const nonTrovato = trovaNellaCatena(errore, ErroreNonTrovato)
  if (nonTrovato) {
    console.log(`Suggerimento: verificare l'esistenza del ${nonTrovato.tipo} ${nonTrovato.identificativo}`)
  }

  const risposta = rispondiAErrore(errore)
  console.log(risposta.stato, risposta.corpo)
}
```

```
# Output atteso:
ErroreApplicativo: Fattura non creata
  ErroreNonTrovato: Cliente 9999 non trovato
Suggerimento: verificare l'esistenza del Cliente 9999
500 { codice: 'FATTURA_NON_CREATA', messaggio: 'Si è verificato un errore.' }
```

```
# I punti che rendono utile questa gerarchia:
#
# CAUSA CONSERVATA.
#   Senza { causa: errore }, il messaggio sarebbe solo
#   "Fattura non creata" e nessuno saprebbe che il cliente
#   non esiste. È l'errore più costoso nella diagnosi.
#
# DUE MESSAGGI DISTINTI.
#   message contiene il dettaglio tecnico, per i log.
#   messaggioPubblico contiene ciò che l'utente può vedere.
#   Confonderli espone dettagli interni o dà messaggi inutili.
#
# LO STATO HTTP SULLA CLASSE.
#   Il tipo di errore SA quale stato gli corrisponde.
#   L'alternativa — una tabella nel gestore — si desincronizza
#   appena qualcuno aggiunge un tipo.
#
# trovaNellaCatena.
#   Permette di reagire alla causa profonda anche quando
#   è avvolta da tre livelli. instanceof sull'errore esterno
#   non basterebbe.
#
# LA GERARCHIA NON DEVE ESSERE PROFONDA.
#   Un livello di base e cinque o sei sottoclassi coprono
#   praticamente ogni applicazione. Gerarchie a quattro
#   livelli diventano difficili da ricordare, e nessuno
#   le usa correttamente.
```

---

## C2. Mini-progetto: client di chat in tempo reale

L'esercizio chiave del modulo: un client di chat con WebSocket, riconnessione automatica, coda dei messaggi non inviati e il pattern Observer per la distribuzione degli eventi.

### Cosa deve fare

1. Connettersi a un server WebSocket e gestire la caduta della connessione.
2. Riconnettersi automaticamente con backoff esponenziale e jitter.
3. Accodare i messaggi scritti mentre la connessione è assente, e inviarli alla riconnessione.
4. Distribuire gli eventi con `EventTarget`, senza che i componenti si conoscano fra loro.
5. Rilevare le connessioni morte con un battito cardiaco.
6. Ripulire tutto con un solo `AbortController`.

### `src/connessione.js`

```javascript
// src/connessione.js
// Il trasporto: sa solo di WebSocket, riconnessione e coda.
// Non sa nulla di messaggi di chat.

/**
 * Stati della connessione:
 *   'disconnesso'   → nessuna connessione, nessun tentativo in corso
 *   'connessione'   → tentativo in corso
 *   'connesso'      → operativa
 *   'riconnessione' → attesa prima del prossimo tentativo
 *   'chiuso'        → chiusa volontariamente, nessuna riconnessione
 */
export class ConnessioneWebSocket extends EventTarget {
  #url
  #protocolli
  #socket = null
  #stato = 'disconnesso'
  #tentativi = 0
  #coda = []
  #controller = new AbortController()
  #temporizzatoreRiconnessione = null
  #temporizzatoreBattito = null
  #temporizzatorePong = null

  #opzioni

  constructor(url, { protocolli = [], ...opzioni } = {}) {
    super()
    this.#url = url
    this.#protocolli = protocolli
    this.#opzioni = {
      attesaIniziale: 500,
      attesaMassima: 30_000,
      tentativiMassimi: Infinity,
      intervalloBattito: 25_000,
      attesaPong: 5_000,
      dimensioneMassimaCoda: 100,
      ...opzioni,
    }
  }

  get stato() {
    return this.#stato
  }

  get connesso() {
    return this.#stato === 'connesso'
  }

  get messaggiInCoda() {
    return this.#coda.length
  }

  #cambiaStato(nuovo, dettaglio = {}) {
    if (this.#stato === nuovo) return
    const precedente = this.#stato
    this.#stato = nuovo
    this.dispatchEvent(
      new CustomEvent('stato', { detail: { precedente, attuale: nuovo, ...dettaglio } }),
    )
  }

  connetti() {
    if (this.#stato === 'connesso' || this.#stato === 'connessione') return
    if (this.#controller.signal.aborted) {
      throw new Error('Connessione chiusa definitivamente: creane una nuova')
    }

    this.#cambiaStato('connessione')

    try {
      this.#socket = new WebSocket(this.#url, this.#protocolli)
    } catch (errore) {
      // Un URL malformato solleva subito
      this.#cambiaStato('disconnesso', { errore })
      this.#programmaRiconnessione()
      return
    }

    const { signal } = this.#controller

    this.#socket.addEventListener(
      'open',
      () => {
        this.#tentativi = 0
        this.#cambiaStato('connesso')
        this.#avviaBattito()
        this.#svuotaCoda()
      },
      { signal },
    )

    this.#socket.addEventListener(
      'message',
      (evento) => {
        // Il pong del battito non riguarda chi usa la connessione
        if (evento.data === 'pong') {
          clearTimeout(this.#temporizzatorePong)
          return
        }

        this.dispatchEvent(new CustomEvent('messaggio', { detail: evento.data }))
      },
      { signal },
    )

    this.#socket.addEventListener(
      'error',
      () => {
        // L'evento error del WebSocket non porta dettagli utili:
        // il motivo vero arriva con 'close'
        this.dispatchEvent(new CustomEvent('errore', { detail: { fase: this.#stato } }))
      },
      { signal },
    )

    this.#socket.addEventListener(
      'close',
      (evento) => {
        this.#fermaBattito()
        this.#socket = null

        // 1000 = chiusura normale, 1001 = pagina in chiusura:
        // non sono errori e non richiedono riconnessione
        const volontaria = evento.code === 1000 || evento.code === 1001

        if (volontaria || this.#controller.signal.aborted) {
          this.#cambiaStato('chiuso', { codice: evento.code, motivo: evento.reason })
          return
        }

        this.#cambiaStato('disconnesso', { codice: evento.code, motivo: evento.reason })
        this.#programmaRiconnessione()
      },
      { signal },
    )
  }

  #programmaRiconnessione() {
    if (this.#controller.signal.aborted) return

    if (this.#tentativi >= this.#opzioni.tentativiMassimi) {
      this.#cambiaStato('chiuso', { motivo: 'tentativi esauriti' })
      return
    }

    this.#tentativi++

    // Backoff esponenziale con jitter: senza il jitter, mille client
    // disconnessi dallo stesso guasto ritenterebbero nello stesso istante
    const base = Math.min(
      this.#opzioni.attesaIniziale * 2 ** (this.#tentativi - 1),
      this.#opzioni.attesaMassima,
    )
    const attesa = base / 2 + Math.random() * (base / 2)

    this.#cambiaStato('riconnessione', { tentativo: this.#tentativi, fraMillisecondi: attesa })

    this.#temporizzatoreRiconnessione = setTimeout(() => this.connetti(), attesa)
  }

  /**
   * Il battito rileva le connessioni morte: una connessione TCP
   * può restare aperta a livello di sistema anche quando il server
   * non risponde più. Senza battito, il client resta in attesa
   * di messaggi che non arriveranno mai.
   */
  #avviaBattito() {
    this.#fermaBattito()

    this.#temporizzatoreBattito = setInterval(() => {
      if (this.#socket?.readyState !== WebSocket.OPEN) return

      this.#socket.send('ping')

      this.#temporizzatorePong = setTimeout(() => {
        // Nessun pong: la connessione è morta anche se sembra aperta
        this.#socket?.close(4000, 'nessuna risposta al battito')
      }, this.#opzioni.attesaPong)
    }, this.#opzioni.intervalloBattito)
  }

  #fermaBattito() {
    clearInterval(this.#temporizzatoreBattito)
    clearTimeout(this.#temporizzatorePong)
    this.#temporizzatoreBattito = null
    this.#temporizzatorePong = null
  }

  /**
   * Invia, oppure accoda se la connessione non è pronta.
   * Restituisce true se è stato inviato subito.
   */
  invia(dati) {
    const testo = typeof dati === 'string' ? dati : JSON.stringify(dati)

    if (this.#socket?.readyState === WebSocket.OPEN) {
      this.#socket.send(testo)
      return true
    }

    if (this.#coda.length >= this.#opzioni.dimensioneMassimaCoda) {
      // La coda ha un limite: senza, una disconnessione lunga
      // farebbe crescere la memoria senza fine
      this.#coda.shift()
      this.dispatchEvent(new CustomEvent('coda-piena'))
    }

    this.#coda.push(testo)
    this.dispatchEvent(new CustomEvent('accodato', { detail: { inCoda: this.#coda.length } }))
    return false
  }

  #svuotaCoda() {
    if (this.#coda.length === 0) return

    const daInviare = this.#coda.splice(0, this.#coda.length)
    for (const testo of daInviare) {
      if (this.#socket?.readyState === WebSocket.OPEN) {
        this.#socket.send(testo)
      } else {
        // La connessione è caduta durante lo svuotamento:
        // rimetti in coda ciò che resta
        this.#coda.unshift(testo)
        break
      }
    }

    this.dispatchEvent(new CustomEvent('coda-svuotata', { detail: { inviati: daInviare.length } }))
  }

  /** Chiude definitivamente e libera tutto. */
  chiudi(codice = 1000, motivo = 'chiusura richiesta') {
    clearTimeout(this.#temporizzatoreRiconnessione)
    this.#fermaBattito()

    // Un solo abort rimuove TUTTI i listener registrati con il segnale
    this.#controller.abort()

    if (this.#socket?.readyState === WebSocket.OPEN) {
      this.#socket.close(codice, motivo)
    }

    this.#socket = null
    this.#coda.length = 0
    this.#cambiaStato('chiuso', { motivo })
  }
}
```

### `src/chat.js`

```javascript
// src/chat.js
// Il dominio: sa di messaggi, utenti e stanze.
// Non sa nulla di WebSocket: parla con la connessione tramite eventi.

import { ConnessioneWebSocket } from './connessione.js'

export class ClientChat extends EventTarget {
  #connessione
  #stanza
  #utente
  #messaggi = []
  #inAttesaDiConferma = new Map()
  #controller = new AbortController()

  constructor(url, { stanza, utente }) {
    super()
    this.#stanza = stanza
    this.#utente = utente
    this.#connessione = new ConnessioneWebSocket(url)

    const { signal } = this.#controller

    this.#connessione.addEventListener(
      'messaggio',
      (evento) => this.#gestisciMessaggio(evento.detail),
      { signal },
    )

    this.#connessione.addEventListener(
      'stato',
      (evento) => {
        this.dispatchEvent(new CustomEvent('connessione', { detail: evento.detail }))

        if (evento.detail.attuale === 'connesso') {
          this.#connessione.invia({ tipo: 'entra', stanza: this.#stanza, utente: this.#utente })
        }
      },
      { signal },
    )

    this.#connessione.addEventListener(
      'accodato',
      (evento) => {
        this.dispatchEvent(new CustomEvent('accodato', { detail: evento.detail }))
      },
      { signal },
    )
  }

  get messaggi() {
    return [...this.#messaggi]
  }

  get statoConnessione() {
    return this.#connessione.stato
  }

  connetti() {
    this.#connessione.connetti()
  }

  /**
   * Invia un messaggio con conferma ottimistica: compare subito
   * come "in invio", e diventa "inviato" quando il server conferma.
   */
  inviaMessaggio(testo) {
    const pulito = testo.trim()
    if (pulito === '') return null

    const messaggio = {
      id: crypto.randomUUID(),
      tipo: 'messaggio',
      stanza: this.#stanza,
      autore: this.#utente,
      testo: pulito,
      quando: new Date().toISOString(),
      stato: 'in-invio',
    }

    this.#messaggi.push(messaggio)
    this.#inAttesaDiConferma.set(messaggio.id, messaggio)
    this.dispatchEvent(new CustomEvent('messaggio', { detail: messaggio }))

    const inviatoSubito = this.#connessione.invia(messaggio)

    if (inviatoSubito) {
      // Se il server non conferma entro 10 secondi, segnala il dubbio
      setTimeout(() => {
        const ancoraInAttesa = this.#inAttesaDiConferma.get(messaggio.id)
        if (ancoraInAttesa) {
          ancoraInAttesa.stato = 'non-confermato'
          this.dispatchEvent(new CustomEvent('messaggio-aggiornato', { detail: ancoraInAttesa }))
        }
      }, 10_000)
    } else {
      messaggio.stato = 'in-coda'
      this.dispatchEvent(new CustomEvent('messaggio-aggiornato', { detail: messaggio }))
    }

    return messaggio
  }

  #gestisciMessaggio(grezzo) {
    let dati
    try {
      dati = JSON.parse(grezzo)
    } catch (errore) {
      // Un messaggio malformato non deve chiudere la connessione
      this.dispatchEvent(
        new CustomEvent('errore', { detail: { motivo: 'messaggio non analizzabile', grezzo } }),
      )
      return
    }

    switch (dati.tipo) {
      case 'conferma': {
        const messaggio = this.#inAttesaDiConferma.get(dati.id)
        if (messaggio) {
          messaggio.stato = 'inviato'
          messaggio.idServer = dati.idServer
          this.#inAttesaDiConferma.delete(dati.id)
          this.dispatchEvent(new CustomEvent('messaggio-aggiornato', { detail: messaggio }))
        }
        break
      }

      case 'messaggio': {
        // Ignora l'eco dei propri messaggi: sono già in elenco
        if (dati.autore?.id === this.#utente.id) break

        const messaggio = { ...dati, stato: 'ricevuto' }
        this.#messaggi.push(messaggio)
        this.dispatchEvent(new CustomEvent('messaggio', { detail: messaggio }))
        break
      }

      case 'presenza':
        this.dispatchEvent(new CustomEvent('presenza', { detail: dati }))
        break

      case 'errore':
        this.dispatchEvent(new CustomEvent('errore', { detail: dati }))
        break

      default:
        console.warn('tipo di messaggio sconosciuto:', dati.tipo)
    }
  }

  chiudi() {
    this.#controller.abort()
    this.#connessione.chiudi()
  }
}
```

### `src/main.js`

```javascript
// src/main.js — l'interfaccia

import { ClientChat } from './chat.js'

const elencoMessaggi = document.querySelector('#messaggi')
const modulo = document.querySelector('#modulo-invio')
const campo = document.querySelector('#campo-messaggio')
const statoConnessione = document.querySelector('#stato-connessione')
const annunci = document.querySelector('#annunci')

const utente = {
  id: crypto.randomUUID(),
  nome: localStorage.getItem('chat:nome') ?? 'Ospite',
}

const chat = new ClientChat('wss://esempio.it/chat', { stanza: 'generale', utente })

function proteggi(testo) {
  return String(testo).replace(
    /[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c],
  )
}

const ETICHETTE_STATO = {
  'in-invio': 'in invio…',
  'in-coda': 'in attesa di connessione',
  inviato: 'inviato',
  'non-confermato': 'consegna non confermata',
  ricevuto: '',
}

function elementoMessaggio(messaggio) {
  const voce = document.createElement('li')
  voce.dataset.id = messaggio.id
  voce.className = messaggio.autore.id === utente.id ? 'mio' : 'altrui'

  voce.innerHTML = `
    <span class="autore">${proteggi(messaggio.autore.nome)}</span>
    <p class="testo">${proteggi(messaggio.testo)}</p>
    <time datetime="${messaggio.quando}">
      ${new Date(messaggio.quando).toLocaleTimeString('it-IT', {
        hour: '2-digit',
        minute: '2-digit',
      })}
    </time>
    <span class="stato">${ETICHETTE_STATO[messaggio.stato] ?? ''}</span>
  `
  return voce
}

// Il pattern Observer in azione: ogni componente ascolta ciò
// che gli interessa, senza conoscere gli altri.

chat.addEventListener('messaggio', (evento) => {
  const eraInFondo =
    elencoMessaggi.scrollHeight - elencoMessaggi.scrollTop - elencoMessaggi.clientHeight < 50

  elencoMessaggi.append(elementoMessaggio(evento.detail))

  // Scorri solo se l'utente stava già guardando il fondo:
  // strappare la vista a chi sta leggendo indietro è fastidioso
  if (eraInFondo) {
    elencoMessaggi.scrollTop = elencoMessaggi.scrollHeight
  }
})

chat.addEventListener('messaggio-aggiornato', (evento) => {
  const messaggio = evento.detail
  const voce = elencoMessaggi.querySelector(`[data-id="${messaggio.id}"] .stato`)
  if (voce) voce.textContent = ETICHETTE_STATO[messaggio.stato] ?? ''
})

chat.addEventListener('connessione', (evento) => {
  const { attuale, tentativo, fraMillisecondi } = evento.detail

  const testi = {
    connessione: 'Connessione in corso…',
    connesso: 'Connesso',
    disconnesso: 'Disconnesso',
    riconnessione: `Riconnessione fra ${Math.round(fraMillisecondi / 1000)} s (tentativo ${tentativo})`,
    chiuso: 'Connessione chiusa',
  }

  statoConnessione.textContent = testi[attuale] ?? attuale
  statoConnessione.dataset.stato = attuale

  // I cambi di stato importanti vanno annunciati
  if (attuale === 'connesso' || attuale === 'disconnesso') {
    annunci.textContent = testi[attuale]
  }

  // Il campo resta utilizzabile anche da disconnessi:
  // i messaggi vengono accodati
  campo.disabled = attuale === 'chiuso'
})

chat.addEventListener('accodato', (evento) => {
  annunci.textContent = `Messaggio in coda (${evento.detail.inCoda} in attesa)`
})

chat.addEventListener('presenza', (evento) => {
  const { utente: chi, azione } = evento.detail
  annunci.textContent = `${chi.nome} è ${azione === 'entrato' ? 'entrato' : 'uscito'}`
})

chat.addEventListener('errore', (evento) => {
  console.error('errore della chat', evento.detail)
})

modulo.addEventListener('submit', (evento) => {
  evento.preventDefault()
  const inviato = chat.inviaMessaggio(campo.value)
  if (inviato) {
    campo.value = ''
    campo.focus()
  }
})

// Chiusura pulita quando la pagina viene lasciata.
// visibilitychange è l'unico evento affidabile su mobile:
// beforeunload e unload non scattano quando l'app viene chiusa.
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') {
    // Non chiudere: la scheda potrebbe tornare visibile.
    // Il battito rileverà eventuali problemi.
  }
})

window.addEventListener('pagehide', () => chat.chiudi())

chat.connetti()
```

### Verifica

```
# I controlli, in ordine:
#
# 1. RICONNESSIONE
#    Ferma il server. La barra di stato deve mostrare
#    "Riconnessione fra N s (tentativo 1)", poi 2, poi 3,
#    con attese CRESCENTI e non identiche fra un client e l'altro.
#    Riavvia il server: la riconnessione avviene da sola.
#
# 2. CODA DEI MESSAGGI
#    Con il server fermo, scrivi tre messaggi.
#    · compaiono subito con stato "in attesa di connessione"
#    · alla riconnessione passano a "inviato"
#    · l'ordine è preservato
#
# 3. BATTITO
#    Simula una connessione morta: in DevTools → Network,
#    attiva la modalità offline SENZA chiudere il socket.
#    Dopo intervalloBattito + attesaPong (30 s) il client
#    deve accorgersene e riconnettersi. Senza battito,
#    resterebbe in attesa per sempre.
#
# 4. NESSUN LEAK
#    Apri e chiudi la chat venti volte.
#    DevTools → Memory → due heap snapshot a confronto:
#    il numero di WebSocket e di listener non deve crescere.
#    È ciò che l'AbortController garantisce.
#
# 5. LIMITE DELLA CODA
#    Con il server fermo, invia 150 messaggi.
#    La coda si ferma a 100 e scarta i più vecchi:
#    senza il limite, la memoria crescerebbe senza fine.
#
# 6. SCORRIMENTO
#    Scorri indietro nella cronologia e ricevi un messaggio:
#    la vista NON deve saltare in fondo. Torna in fondo
#    e ricevi un altro messaggio: ora deve seguire.
```

```
# I meccanismi del tutorial usati, e dove:
#
#   EventTarget           ConnessioneWebSocket e ClientChat lo estendono:
#                         Observer senza scrivere un emettitore
#   AbortController       un abort rimuove tutti i listener del socket
#   backoff + jitter      #programmaRiconnessione
#   coda con limite       #coda, per sopravvivere alle disconnessioni lunghe
#   campi privati #       lo stato interno non è raggiungibile
#   separazione a livelli connessione.js non sa cosa sia un messaggio,
#                         chat.js non sa cosa sia un WebSocket
#   Promise.withResolvers non serve qui: gli eventi sono più adatti
#                         di una Promise a un flusso continuo
#   conferma ottimistica  il messaggio compare subito, lo stato
#                         si aggiorna quando il server risponde
```

---

# Parte D — Approfondimento per Esperti

---

## D1. Decoratori

I decoratori sono funzioni che modificano classi, metodi, campi o accessori al momento della definizione. La proposta è allo stadio 3 di TC39: richiedono un transpiler (TypeScript 5+, Babel), ma la forma è ormai stabile.

```javascript
/**
 * Un decoratore di metodo riceve il metodo originale e un contesto
 * che descrive cosa sta decorando. Restituisce il sostituto.
 */
function registra(originale, contesto) {
  const nome = String(contesto.name)

  return function (...argomenti) {
    console.log(`→ ${nome}(${argomenti.map((a) => JSON.stringify(a)).join(', ')})`)
    const inizio = performance.now()

    try {
      const risultato = originale.apply(this, argomenti)

      // Un metodo async restituisce una Promise: va gestita
      if (risultato instanceof Promise) {
        return risultato.then(
          (valore) => {
            console.log(`← ${nome} in ${(performance.now() - inizio).toFixed(1)} ms`)
            return valore
          },
          (errore) => {
            console.log(`✗ ${nome} fallito: ${errore.message}`)
            throw errore
          },
        )
      }

      console.log(`← ${nome} in ${(performance.now() - inizio).toFixed(1)} ms`)
      return risultato
    } catch (errore) {
      console.log(`✗ ${nome} fallito: ${errore.message}`)
      throw errore
    }
  }
}
```

```javascript
/** Decoratore con argomenti: una funzione che RESTITUISCE un decoratore. */
function memorizza({ durata = 60_000 } = {}) {
  return function (originale, contesto) {
    // Una cache per ISTANZA, non condivisa fra tutte:
    // una WeakMap sull'oggetto evita che le istanze si vedano
    const cachePerIstanza = new WeakMap()

    return function (...argomenti) {
      if (!cachePerIstanza.has(this)) cachePerIstanza.set(this, new Map())
      const cache = cachePerIstanza.get(this)

      const chiave = JSON.stringify(argomenti)
      const voce = cache.get(chiave)

      if (voce && Date.now() - voce.quando < durata) {
        return voce.valore
      }

      const valore = originale.apply(this, argomenti)
      cache.set(chiave, { valore, quando: Date.now() })
      return valore
    }
  }
}

/** Decoratore che limita la frequenza di chiamata. */
function limitaA(chiamateAlSecondo) {
  const intervalloMinimo = 1000 / chiamateAlSecondo

  return function (originale, contesto) {
    const ultimaChiamata = new WeakMap()

    return function (...argomenti) {
      const adesso = Date.now()
      const precedente = ultimaChiamata.get(this) ?? 0

      if (adesso - precedente < intervalloMinimo) {
        throw new Error(
          `${String(contesto.name)}: limite di ${chiamateAlSecondo} chiamate al secondo superato`,
        )
      }

      ultimaChiamata.set(this, adesso)
      return originale.apply(this, argomenti)
    }
  }
}
```

```typescript
// L'uso: la logica trasversale sparisce dai metodi
class ServizioFatture {
  #repository

  constructor(repository) {
    this.#repository = repository
  }

  @registra
  @memorizza({ durata: 30_000 })
  async calcolaTotale(clienteId) {
    const fatture = await this.#repository.elenca({ cliente: clienteId })
    return fatture.reduce((somma, f) => somma + f.importo, 0)
  }

  @registra
  @limitaA(2)
  async inviaSollecito(fatturaId) {
    return this.#repository.inviaSollecito(fatturaId)
  }
}
```

```
L'ordine di applicazione: dal BASSO verso l'ALTO.

  @registra              ← applicato per secondo (avvolge)
  @memorizza(...)        ← applicato per primo
  async calcolaTotale()

  Risultato: registra(memorizza(calcolaTotale))

  Il log quindi registra ANCHE le chiamate servite dalla cache.
  Invertendo l'ordine, la cache avvolgerebbe il log e i
  colpi in cache non comparirebbero. La differenza conta.
```

### Decoratori di campo, accessore e classe

```typescript
/** Campo: riceve un inizializzatore, restituisce il sostituto. */
function predefinito(valore) {
  return function (_originale, contesto) {
    return function (valoreIniziale) {
      return valoreIniziale ?? valore
    }
  }
}

/** Accessore: riceve { get, set }. */
function soloLetturaDopoInizializzazione(originale, contesto) {
  return {
    get: originale.get,
    set(valore) {
      if (this[`#${String(contesto.name)}Impostato`]) {
        throw new TypeError(`${String(contesto.name)} è già stato impostato`)
      }
      originale.set.call(this, valore)
    },
  }
}

/**
 * Classe: riceve il costruttore e può restituirne un altro.
 *
 * Il vincolo generico non è decorativo: senza, il tipo restituito
 * è una classe anonima e TypeScript rifiuta il decoratore con
 *   TS1270: Decorator function return type is not assignable
 * Legando il ritorno a T, il sostituto resta assegnabile all'originale.
 */
function sigillata<T extends new (...argomenti: any[]) => object>(
  originale: T,
  contesto: ClassDecoratorContext,
): T {
  return class extends originale {
    constructor(...argomenti: any[]) {
      super(...argomenti)
      Object.seal(this)
    }
  }
}

@sigillata
class Configurazione {
  @predefinito(3000)
  porta

  @predefinito('localhost')
  host
}
```

### `addInitializer`

```typescript
/**
 * Il contesto espone addInitializer: registra codice da eseguire
 * alla costruzione dell'istanza. È il modo per legare i metodi
 * senza scrivere bind nel costruttore.
 */
function legato(originale, contesto) {
  contesto.addInitializer(function () {
    this[contesto.name] = originale.bind(this)
  })
  return originale
}

class Componente {
  nome = 'pannello'

  @legato
  gestisciClic() {
    console.log(this.nome) // this è sempre l'istanza
  }
}

const c = new Componente()
const estratto = c.gestisciClic
estratto() // 'pannello' — funziona anche estratto
```

### Configurazione del transpiler

```json
// tsconfig.json — TypeScript 5+ usa la sintassi standard
{
  "compilerOptions": {
    "target": "ES2022",
    "experimentalDecorators": false
  }
}
```

`experimentalDecorators: false` è importante: `true` attiva la vecchia sintassi sperimentale, incompatibile con quella standard. I due sistemi differiscono nella firma dei decoratori e non sono intercambiabili.

---

## D2. `SharedArrayBuffer` e `Atomics`

Un `SharedArrayBuffer` è memoria **condivisa** fra il thread principale e i Worker: nessuna copia, nessun trasferimento.

### I requisiti di sicurezza

```
Dopo Spectre, SharedArrayBuffer richiede che la pagina sia
"cross-origin isolated". Servono due intestazioni HTTP:

  Cross-Origin-Opener-Policy: same-origin
  Cross-Origin-Embedder-Policy: require-corp

E ogni risorsa di terze parti deve dichiarare
  Cross-Origin-Resource-Policy: cross-origin
oppure essere caricata con crossorigin.

Senza, SharedArrayBuffer non è disponibile: il costruttore
non esiste. È una limitazione seria, che va valutata prima
di progettare un'architettura che ci si appoggi.
```

```javascript
// Verificare prima di usarlo
if (!globalThis.crossOriginIsolated) {
  console.warn('Pagina non isolata: SharedArrayBuffer non disponibile')
  // Ripiegare sul passaggio con clonazione o trasferimento
}
```

```javascript
// vite.config.js — le intestazioni in sviluppo
export default {
  server: {
    headers: {
      'Cross-Origin-Opener-Policy': 'same-origin',
      'Cross-Origin-Embedder-Policy': 'require-corp',
    },
  },
}
```

### Memoria condivisa

```javascript
// src/main.js
const buffer = new SharedArrayBuffer(1024 * 1024 * 4) // 4 MB
const vista = new Float64Array(buffer)

// Riempimento nel thread principale
for (let i = 0; i < vista.length; i++) vista[i] = Math.random()

const lavoratore = new Worker(new URL('./somma.worker.js', import.meta.url), { type: 'module' })

// Il buffer NON viene copiato: entrambi i thread vedono
// la stessa memoria fisica
lavoratore.postMessage({ buffer })
```

```javascript
// src/somma.worker.js
self.addEventListener('message', (evento) => {
  const vista = new Float64Array(evento.data.buffer)

  let somma = 0
  for (let i = 0; i < vista.length; i++) somma += vista[i]

  // Le modifiche alla vista sono visibili anche al thread principale
  self.postMessage({ somma })
})
```

### `Atomics`: operazioni indivisibili

Con la memoria condivisa arrivano le corse critiche: due thread che leggono, modificano e riscrivono la stessa cella possono perdere un aggiornamento.

```javascript
// ❌ CORSA CRITICA — leggi, incrementa, scrivi non è indivisibile.
//    Due worker possono leggere lo stesso valore e scriverne
//    uno solo: un incremento va perso.
vista[0] = vista[0] + 1

// ✅ Atomics.add è indivisibile: nessun aggiornamento si perde
Atomics.add(vista, 0, 1)
```

```javascript
// Le operazioni disponibili
Atomics.add(vista, indice, valore) // somma, restituisce il precedente
Atomics.sub(vista, indice, valore)
Atomics.and(vista, indice, valore)
Atomics.or(vista, indice, valore)
Atomics.xor(vista, indice, valore)
Atomics.exchange(vista, indice, valore) // scrive, restituisce il precedente
Atomics.compareExchange(vista, indice, atteso, nuovo) // solo se corrisponde
Atomics.load(vista, indice) // lettura indivisibile
Atomics.store(vista, indice, valore) // scrittura indivisibile
```

### Un lucchetto costruito con `compareExchange`

```javascript
/**
 * Mutua esclusione con attesa attiva.
 * Serve per proteggere sezioni critiche brevissime:
 * per attese lunghe l'attesa attiva brucia CPU.
 */
class Lucchetto {
  #vista

  constructor(sharedArrayBuffer, offset = 0) {
    this.#vista = new Int32Array(sharedArrayBuffer, offset, 1)
  }

  acquisisci() {
    // Prova a passare da 0 a 1. Se il valore era già 1,
    // qualcun altro ha il lucchetto: riprova.
    while (Atomics.compareExchange(this.#vista, 0, 0, 1) !== 0) {
      // Attesa bloccante: DISPONIBILE SOLO nei Worker,
      // sul thread principale solleverebbe TypeError
      Atomics.wait(this.#vista, 0, 1)
    }
  }

  rilascia() {
    Atomics.store(this.#vista, 0, 0)
    // Sveglia un thread in attesa
    Atomics.notify(this.#vista, 0, 1)
  }

  conLucchetto(operazione) {
    this.acquisisci()
    try {
      return operazione()
    } finally {
      this.rilascia()
    }
  }
}
```

```javascript
// Atomics.waitAsync: la variante non bloccante,
// utilizzabile anche sul thread principale
const esito = Atomics.waitAsync(vista, 0, 1, 5000)

if (esito.async) {
  const stato = await esito.value // 'ok' | 'timed-out'
  console.log(stato)
} else {
  console.log(esito.value) // 'not-equal': il valore era già cambiato
}
```

### Quando conviene davvero

```
SharedArrayBuffer conviene quando:
  · i dati sono numerici e omogenei (Float64Array, Int32Array)
  · sono grandi: decine di MB, dove la clonazione costa
  · più worker devono leggere gli stessi dati contemporaneamente
  · il calcolo è lungo rispetto al passaggio

NON conviene quando:
  · i dati sono oggetti strutturati: andrebbero serializzati
    manualmente in un buffer numerico
  · un solo worker li usa: il TRASFERIMENTO di un ArrayBuffer
    è a costo zero e non richiede l'isolamento
  · i requisiti COOP/COEP romperebbero integrazioni esistenti
    (widget di terze parti, iframe, script pubblicitari)

Il caso d'uso tipico: elaborazione di immagini, audio,
simulazioni numeriche, e WebAssembly con memoria condivisa.
```

---

## D3. Import map e import attributes

### Import map

Permettono di usare gli specificatori nudi (`import ... from 'lodash'`) nel browser, senza bundler.

```html
<script type="importmap">
  {
    "imports": {
      "lodash-es": "https://esm.sh/lodash-es@4.17.21",
      "@app/": "/src/",
      "utility": "/src/utility/indice.js"
    },
    "scopes": {
      "/legacy/": {
        "lodash-es": "https://esm.sh/lodash-es@3.10.1"
      }
    }
  }
</script>

<script type="module">
  import { debounce } from 'lodash-es'
  import { formatta } from '@app/formattazione.js'
</script>
```

```
Due dettagli operativi:

  · L'import map va PRIMA di qualunque <script type="module">.
    Un modulo già risolto non viene rimappato.

  · "scopes" permette versioni diverse per parti diverse
    dell'applicazione: il codice sotto /legacy/ riceve
    lodash 3, tutto il resto riceve lodash 4.
    È il modo di far convivere due versioni durante una migrazione.
```

```html
<!-- Con l'integrità, per le dipendenze da CDN -->
<script type="importmap">
  {
    "imports": {
      "lodash-es": "https://esm.sh/lodash-es@4.17.21"
    },
    "integrity": {
      "https://esm.sh/lodash-es@4.17.21": "sha384-oqVuAfXRKap7fdgcCY5uykM6+R9GqQ8K/uxy9rx7HNQlGYl1kPzQho1wx4JwY8wC"
    }
  }
</script>
```

### Import attributes

```javascript
// Importare JSON come modulo, dichiarando il tipo.
// L'attributo NON è opzionale: senza, il browser rifiuta
// il modulo se il Content-Type non è JavaScript.
// È una difesa contro l'esecuzione di contenuti scambiati per script.
import configurazione from './configurazione.json' with { type: 'json' }

// Importare CSS come CSSStyleSheet costruibile
import fogli from './componente.css' with { type: 'css' }
document.adoptedStyleSheets = [...document.adoptedStyleSheets, fogli]

// Import dinamico con attributi
const { default: dati } = await import('./dati.json', { with: { type: 'json' } })
```

```javascript
// In Node.js la sintassi è la stessa
import pacchetto from './package.json' with { type: 'json' }
console.log(pacchetto.version)
```

La sintassi precedente usava `assert` invece di `with`; è stata sostituita perché gli attributi non si limitano ad asserire, possono cambiare come il modulo viene interpretato. Il codice che usa `assert` va aggiornato.

---

## D4. Testing avanzato con Vitest

```powershell
pnpm add -D vitest @vitest/coverage-v8 happy-dom
```

```javascript
// vitest.config.js
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'node', // 'happy-dom' o 'jsdom' per i test del DOM
    globals: false, // import espliciti: più chiaro da dove viene cosa
    setupFiles: ['./test/preparazione.js'],

    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      exclude: ['**/*.config.js', '**/generato/**', '**/*.test.js'],
      thresholds: {
        // Soglie per FILE, non solo globali: una media alta
        // può nascondere un file critico senza test
        perFile: true,
        statements: 80,
        branches: 75,
        functions: 80,
      },
    },
  },
})
```

### Testare il codice asincrono

```javascript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { conRitentativi } from '../src/ritentativi.js'

describe('conRitentativi', () => {
  beforeEach(() => {
    // I timer finti rendono il test istantaneo e deterministico:
    // senza, un test sul backoff durerebbe secondi reali
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('restituisce il valore al primo tentativo riuscito', async () => {
    const operazione = vi.fn().mockResolvedValue('ok')

    const esito = await conRitentativi(operazione)

    expect(esito).toBe('ok')
    expect(operazione).toHaveBeenCalledTimes(1)
  })

  it('ritenta e riesce al terzo tentativo', async () => {
    const operazione = vi
      .fn()
      .mockRejectedValueOnce(new Error('primo'))
      .mockRejectedValueOnce(new Error('secondo'))
      .mockResolvedValue('finalmente')

    const promessa = conRitentativi(operazione, { attesaIniziale: 100 })

    // Avanza i timer finti: le attese del backoff scattano subito
    await vi.runAllTimersAsync()

    await expect(promessa).resolves.toBe('finalmente')
    expect(operazione).toHaveBeenCalledTimes(3)
  })

  it('non ritenta gli errori non ripetibili', async () => {
    const errore = Object.assign(new Error('400'), { eRipetibile: false })
    const operazione = vi.fn().mockRejectedValue(errore)

    await expect(
      conRitentativi(operazione, { ripetibile: (e) => e.eRipetibile }),
    ).rejects.toThrow('400')

    expect(operazione).toHaveBeenCalledTimes(1)
  })

  it('conserva l ultimo errore come causa', async () => {
    const originale = new Error('sempre fallito')
    const operazione = vi.fn().mockRejectedValue(originale)

    const promessa = conRitentativi(operazione, { tentativiMassimi: 2, attesaIniziale: 10 })
    await vi.runAllTimersAsync()

    await expect(promessa).rejects.toMatchObject({ cause: originale })
  })
})
```

### Mocking dei moduli ESM

```javascript
import { describe, it, expect, vi, beforeEach } from 'vitest'

// vi.mock è SOLLEVATO in cima al file: si applica anche se
// scritto dopo gli import. La factory non può referenziare
// variabili esterne dichiarate dopo.
vi.mock('../src/api.js', () => ({
  recuperaUtente: vi.fn(),
  recuperaOrdini: vi.fn(),
}))

// L'import va DOPO vi.mock, e riceve la versione finta
const { recuperaUtente, recuperaOrdini } = await import('../src/api.js')
const { caricaCruscotto } = await import('../src/cruscotto.js')

describe('caricaCruscotto', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('carica le sezioni indipendenti in parallelo', async () => {
    recuperaUtente.mockResolvedValue({ id: 1, nome: 'Anna' })
    recuperaOrdini.mockResolvedValue([{ id: 10 }])

    const esito = await caricaCruscotto(1)

    expect(esito.utente.nome).toBe('Anna')
    expect(esito.ordini).toHaveLength(1)
  })

  it('sopravvive al fallimento di una sezione', async () => {
    recuperaUtente.mockResolvedValue({ id: 1, nome: 'Anna' })
    recuperaOrdini.mockRejectedValue(new Error('servizio giù'))

    const esito = await caricaCruscotto(1)

    expect(esito.utente).toBeDefined()
    expect(esito.ordini).toEqual([])
    expect(esito.problemi).toHaveLength(1)
  })
})
```

```javascript
// vi.importActual: sostituire solo una parte del modulo
vi.mock('../src/utility.js', async (importaOriginale) => {
  const originale = await importaOriginale()
  return {
    ...originale,
    // Solo questa è finta; il resto è quello vero
    generaId: vi.fn(() => 'id-fisso-per-i-test'),
  }
})
```

### Testare `fetch` senza rete

```javascript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

describe('recupera', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('solleva ErroreHttp su una risposta non ok', async () => {
    fetch.mockResolvedValue(
      new Response(JSON.stringify({ messaggio: 'non trovato' }), {
        status: 404,
        statusText: 'Not Found',
        headers: { 'Content-Type': 'application/json' },
      }),
    )

    await expect(recupera('/api/x')).rejects.toMatchObject({
      name: 'ErroreHttp',
      stato: 404,
    })
  })

  it('propaga AbortError senza trasformarlo', async () => {
    fetch.mockRejectedValue(
      Object.assign(new Error('The operation was aborted'), { name: 'AbortError' }),
    )

    await expect(recupera('/api/x')).rejects.toMatchObject({ name: 'AbortError' })
  })
})
```

Per casi più complessi, MSW intercetta a livello di rete e permette di scrivere gestori realistici invece di finte risposte. È trattato in `tutorial_15_testing_web.md`.

### Test basati su proprietà

```javascript
import { it, expect } from 'vitest'
import fc from 'fast-check'

it('conConcorrenza preserva ordine e lunghezza per qualunque input', async () => {
  await fc.assert(
    fc.asyncProperty(
      fc.array(fc.integer(), { maxLength: 200 }),
      fc.integer({ min: 1, max: 20 }),
      async (elementi, limite) => {
        const esito = await conConcorrenza(elementi, async (n) => n * 2, limite)

        expect(esito).toHaveLength(elementi.length)
        expect(esito).toEqual(elementi.map((n) => n * 2))
      },
    ),
    { numRuns: 200 },
  )
})
```

Un test basato su proprietà genera centinaia di input casuali e, quando ne trova uno che rompe la proprietà, lo **riduce** al caso minimo che ancora fallisce. Trova i casi limite che nessuno scrive a mano: l'array vuoto, il limite maggiore della lunghezza, gli elementi duplicati.

### Snapshot, usati bene

```javascript
import { it, expect } from 'vitest'

it('formatta il riepilogo', () => {
  const riepilogo = generaRiepilogo(datiDiProva)

  // Inline: lo snapshot è nel file di test, visibile in revisione
  expect(riepilogo).toMatchInlineSnapshot(`
    {
      "insoluto": 890,
      "totale": 4530,
      "clienti": 3,
    }
  `)
})
```

```
Gli snapshot su file separato hanno un difetto: in una pull request
nessuno li legge, e "aggiorna gli snapshot" diventa un riflesso
automatico che nasconde le regressioni.

toMatchInlineSnapshot li mette nel file di test, dove la modifica
è visibile nel diff. È la forma da preferire per gli oggetti piccoli.
```

### Il criterio per cosa testare

```
Da testare per primo, in ordine:

  1. La logica che gestisce denaro, date e permessi
  2. I casi limite: vuoto, null, zero, negativo, molto grande
  3. Gli errori: cosa succede quando la rete cade a metà
  4. Le regressioni: ogni bug corretto diventa un test

Da NON testare:
  · che un mock restituisca ciò che gli hai detto di restituire
  · i dettagli implementativi che cambieranno al primo refactoring
  · il codice di libreria

La percentuale di copertura non è un obiettivo. Una copertura
del 90% con test che asseriscono i propri mock vale meno
del 50% con test sui casi che fanno perdere soldi.
```

---

# Parte E — Riepilogo, Checklist e Prossimi Passi

---

## Riepilogo concettuale

```
JAVASCRIPT AVANZATO — Mappa dei concetti

ASINCRONIA
├── Cosa è asincrono: rete, timer, disco, database
│   └── NON lo è un ciclo lungo: per quello serve un Worker
├── Promise: pending → fulfilled | rejected, transizione UNICA
│   └── then restituisce SEMPRE una Promise nuova
├── async/await = zucchero sull'stesse Promise
│   ├── una funzione async restituisce SEMPRE una Promise
│   ├── await sospende la FUNZIONE, non il thread
│   └── await in sequenza su operazioni INDIPENDENTI
│         è l'errore che raddoppia i tempi
├── Combinatori
│   ├── all        tutte, o la prima che fallisce
│   ├── allSettled tutte, mai rifiuta      ← per i fallimenti parziali
│   ├── race       la prima che si conclude ← per i timeout
│   └── any        la prima che RIESCE      ← AggregateError se tutte falliscono
└── Promise.withResolvers (ES2024) per risolvere dall'esterno

FETCH
├── NON rifiuta su 404 e 500: verificare SEMPRE risposta.ok
│   └── rifiuta solo per errori di rete, CORS, annullamento
├── Il corpo si legge UNA volta: clone() per leggerlo due
├── Con FormData NON impostare Content-Type
└── AbortController
    ├── AbortSignal.timeout(ms)
    ├── AbortSignal.any([...]) per combinare
    ├── signal.throwIfAborted() nel proprio codice
    └── AbortError NON è un errore da mostrare all'utente

PATTERN ASINCRONI
├── Concorrenza a OPERAI, non a lotti
│     i lotti lasciano operai inattivi ad attendere il più lento
├── Retry con backoff esponenziale + JITTER
│     senza jitter: thundering herd
│     ritentare solo ciò che può migliorare (5xx, 429, 408)
├── Deduplicazione delle richieste in volo
│     rimuovere dalla mappa nel finally, anche in caso di errore
├── Interruttore automatico: chiuso → aperto → semiaperto
└── Coda con priorità

FUNZIONALE
├── Funzioni pure: stesso input → stesso output, nessun effetto
│     → testabili, memoizzabili, parallelizzabili
│     Gli effetti ai BORDI, il nucleo puro
├── Immutabilità: toSorted, toSpliced, with, map, filter
├── Composizione: pipe (sinistra→destra), compose (destra→sinistra)
├── Currying e applicazione parziale
└── Result pattern: l'errore come VALORE, non come eccezione

PROXY E REFLECT
├── 13 trappole: get set has deleteProperty ownKeys apply construct…
├── Reflect SEMPRE, non l'operazione diretta
│     inoltra il ricevitore, restituisce il booleano richiesto
├── I Symbol vanno lasciati passare senza controlli
├── Casi d'uso: validazione, valori predefiniti, refusi, reattività
└── Costano: ogni accesso passa dalla trappola

DESIGN PATTERN
├── Strategy → una mappa al posto della catena di if
├── Observer → EventTarget nativo, con once e signal inclusi
├── Repository → isola l'accesso ai dati, rende testabile senza rete
├── Modulo → campi privati # invece delle closure
└── Costruttore fluente → quando i parametri sono molti

WEB WORKERS
├── Thread vero: niente document, niente window
├── postMessage CLONA (structured clone): costa
│     trasferire ArrayBuffer è a costo zero, ma lo svuota
├── Il worker può essere PIÙ LENTO in tempo totale
│     e comunque giusto: l'interfaccia resta reattiva
└── navigator.hardwareConcurrency per il numero di worker

MODULI
├── ESM statico → tree shaking. CJS dinamico → no
├── CJS da ESM: import di DEFAULT, non con nome
├── ESM da CJS: solo import() dinamico
├── import.meta.dirname / .filename (Node 20.11+)
└── package.json: "exports" limita, "sideEffects" abilita il tree shaking

ERRORI
├── Gerarchia propria con statoHttp e messaggioPubblico distinti
├── cause conserva la catena: senza, la causa vera sparisce
├── trovaNellaCatena per reagire alla causa PROFONDA
├── safeTry [errore, valore] quando l'errore è previsto
└── Gestori globali: error (anche in cattura per le risorse),
      unhandledrejection, sendBeacon per l'invio

PERFORMANCE
└── L'ordine in cui cercare: rete → algoritmo → rendering
      → thread → memoria → micro-codice (quasi mai)
```

---

## Checklist di competenze

Segna ✓ quando sei sicuro di ogni competenza.

**Parte A — Basi**

- [ ] Sai distinguere cosa è asincrono per natura da cosa non lo diventa con `async`
- [ ] Sai perché la piramide di callback è un problema di flusso di controllo, non di indentazione
- [ ] Conosci i tre stati di una Promise e sai che la transizione è unica
- [ ] Sai perché `then` senza `return` interrompe la catena
- [ ] Sai riconoscere gli `await` sequenziali su operazioni indipendenti
- [ ] Scegli il combinatore giusto fra `all`, `allSettled`, `race` e `any`
- [ ] Sai perché `fetch` non rifiuta su un 404 e verifichi sempre `risposta.ok`
- [ ] Sai perché con `FormData` non si imposta `Content-Type`
- [ ] Usi `AbortController` per la ricerca con suggerimenti e sai perché serve
- [ ] Distingui `AbortError` da `TimeoutError` e trattai diversamente

**Parte B — Comprensione**

- [ ] Implementi la concorrenza limitata a operai e sai perché batte i lotti
- [ ] Sai perché il jitter nel backoff non è opzionale
- [ ] Sai quali errori vanno ritentati e quali no
- [ ] Implementi la deduplicazione e sai perché va rimossa nel `finally`
- [ ] Sai cosa fa un interruttore automatico e quando serve
- [ ] Sai riconoscere una funzione pura e perché conviene
- [ ] Scrivi aggiornamenti immutabili anche su strutture annidate
- [ ] Sai comporre funzioni con `pipe` e sai perché si preferisce a `compose`
- [ ] Conosci le principali trappole di un `Proxy`
- [ ] Sai perché serve `Reflect` e cosa succede senza il `return` in `set`
- [ ] Sai perché i Symbol vanno lasciati passare nella trappola `get`
- [ ] Sostituisci una catena di `if` con una mappa di strategie
- [ ] Usi `EventTarget` invece di scrivere un emettitore di eventi
- [ ] Sai cosa un Worker può e non può fare, e quanto costa il passaggio dei dati
- [ ] Sai perché un Worker più lento può essere la scelta giusta
- [ ] Sai importare CommonJS da ESM e viceversa
- [ ] Sai a cosa servono `exports` e `sideEffects` nel `package.json`
- [ ] Costruisci una gerarchia di errori con `cause`
- [ ] Sai perché `message` e `messaggioPubblico` devono restare distinti
- [ ] Conosci l'ordine in cui cercare i problemi di prestazioni

**Parte C — Pratica**

- [ ] Hai convertito la piramide di callback introducendo il parallelismo
- [ ] Hai composto concorrenza limitata e ritentativi
- [ ] Hai previsto correttamente l'ordine dell'esercizio 3 prima di eseguirlo
- [ ] Hai costruito il `Proxy` di configurazione e verificato le tre validazioni
- [ ] Hai misurato la differenza fra thread principale e Worker con un'animazione
- [ ] Hai costruito il client di chat e verificato la riconnessione con backoff

**Parte D — Esperto**

- [ ] Sai l'ordine di applicazione dei decoratori e perché conta
- [ ] Sai a cosa serve `addInitializer`
- [ ] Conosci i requisiti COOP/COEP di `SharedArrayBuffer`
- [ ] Sai perché `vista[0] = vista[0] + 1` è una corsa critica
- [ ] Sai quando `SharedArrayBuffer` conviene rispetto al trasferimento
- [ ] Sai perché un'import map va prima di ogni `<script type="module">`
- [ ] Sai perché gli import attributes sono una difesa e non una formalità
- [ ] Usi i timer finti per testare il backoff senza attese reali
- [ ] Sai perché `vi.mock` è sollevato e cosa comporta
- [ ] Sai perché `toMatchInlineSnapshot` è preferibile agli snapshot su file
- [ ] Sai perché la percentuale di copertura non è un obiettivo

---

## Anti-pattern da evitare

| Anti-pattern | Problema | Soluzione |
|---|---|---|
| `await` in sequenza su operazioni indipendenti | Somma le latenze invece di sovrapporle | `Promise.all` |
| `await` dentro un ciclo su N elementi | N richieste sequenziali | `Promise.all` con `map`, o concorrenza limitata |
| `Promise.all` su centinaia di elementi | Apre tutte le connessioni insieme | Concorrenza limitata a operai |
| `Promise.all` dove basta un successo parziale | Un fallimento svuota tutta la pagina | `Promise.allSettled` |
| Non verificare `risposta.ok` | Un 404 arriva come errore di parsing | `if (!risposta.ok) throw` |
| `Content-Type` con `FormData` | Il boundary manca: il server non separa i campi | Lasciare che sia il browser a impostarlo |
| Leggere il corpo due volte | `TypeError: Body has already been consumed` | `risposta.clone()` prima |
| Ricerca con suggerimenti senza annullamento | Una risposta lenta sovrascrive una recente | `AbortController` per richiesta |
| Trattare `AbortError` come un errore | Messaggi di errore per azioni volontarie | Riconoscerlo e uscire in silenzio |
| Retry senza jitter | Thundering herd: tutti ritentano insieme | `Math.random() * base` |
| Ritentare un 400 o un 404 | Non migliora, e carica il server | Ritentare solo 408, 429 e 5xx |
| Deduplicazione senza `finally` | Un fallimento resta in cache per sempre | Rimuovere la voce nel `finally` |
| `then` senza `return` | Il passo successivo riceve `undefined` | `return` esplicito, o arrow senza graffe |
| `bersaglio[chiave]` in una trappola Proxy | Ignora il ricevitore, rompe i getter e la reattività | `Reflect.get(bersaglio, chiave, ricevitore)` |
| Trappola `set` senza `return` | `TypeError` in strict mode | `return Reflect.set(...)` |
| Proxy che blocca i Symbol | `console.log` e lo spread sollevano errori | Lasciare passare `typeof chiave === 'symbol'` |
| Proxy in un ciclo caldo | Ogni accesso passa dalla trappola | Usarli dove gli accessi sono rari |
| Catena di `if` per selezionare un comportamento | Cresce a ogni caso, e va toccata ogni volta | Mappa di strategie |
| Emettitore di eventi scritto a mano | Manca `once`, `signal`, e la gestione degli errori | `EventTarget` |
| `postMessage` di oggetti enormi | La clonazione costa e raddoppia la memoria | Trasferire `ArrayBuffer`, o generare i dati nel worker |
| Worker per operazioni sotto i 50 ms | Il passaggio costa più del calcolo | Eseguire sul thread principale |
| Worker mai terminato | Consuma memoria per tutta la vita della pagina | `terminate()` alla dismissione |
| `require` di un modulo ESM | `ERR_REQUIRE_ESM` | `await import()` |
| Import con nome da un modulo CJS | Non sempre analizzabile staticamente | Import di default, poi destrutturazione |
| `catch` che rilancia perdendo l'originale | La causa vera sparisce dai log | `new Error(msg, { cause: errore })` |
| Un messaggio solo per log e per utente | Espone dettagli interni, o non dice nulla | `message` tecnico, `messaggioPubblico` per l'utente |
| Gerarchia di errori a quattro livelli | Nessuno la ricorda, nessuno la usa bene | Una base e cinque o sei sottoclassi |
| `beforeunload` per la pulizia su mobile | Non scatta quando l'app viene chiusa | `visibilitychange` e `pagehide` |
| WebSocket senza battito | Una connessione morta sembra aperta per sempre | Ping e attesa del pong |
| Coda dei messaggi senza limite | La memoria cresce durante una disconnessione lunga | Limite con scarto dei più vecchi |
| Ottimizzare il micro-codice per primo | Guadagno impercettibile, leggibilità persa | Rete, algoritmo, rendering, poi il resto |
| Test che asserisce il proprio mock | Non verifica nulla del codice reale | Testare il comportamento osservabile |
| Copertura come obiettivo | Test scritti per la percentuale, non per i bug | Coprire prima ciò che fa perdere soldi |

---

## Troubleshooting rapido

**`TypeError: Failed to fetch`**
- Causa: errore di rete, CORS bloccato, o richiesta annullata
- Fix: DevTools → Network per distinguere. Se la richiesta non compare affatto, è CORS in fase di preflight

**Una richiesta annullata compare come errore all'utente**
- Causa: `AbortError` trattato come un fallimento qualunque
- Fix: `if (errore.name === 'AbortError') return` prima di mostrare qualcosa

**`TypeError: Body has already been consumed`**
- Causa: il corpo della risposta è uno stream leggibile una volta sola
- Fix: `risposta.clone()` prima della prima lettura

**Il server riceve un corpo vuoto con `FormData`**
- Causa: `Content-Type` impostato a mano: manca il boundary
- Fix: rimuovere l'intestazione e lasciare che sia il browser a generarla

**Le richieste partono tutte insieme e il server risponde 429**
- Causa: `Promise.all` su un array grande
- Fix: concorrenza limitata; e rispettare l'intestazione `Retry-After`

**Il retry peggiora la situazione invece di risolverla**
- Causa: nessun jitter, oppure si ritentano errori non transitori
- Fix: jitter completo, e `ripetibile` che esclude i 4xx diversi da 408 e 429

**`Promise.all` non annulla le altre richieste quando una fallisce**
- Causa: è il comportamento previsto — `all` non cancella nulla
- Fix: un `AbortController` condiviso, e `abort()` nel `catch`

**Una trappola `set` del Proxy solleva `TypeError`**
- Causa: la trappola non restituisce `true` in strict mode
- Fix: `return Reflect.set(bersaglio, chiave, valore, ricevitore)`

**`console.log` su un oggetto con Proxy solleva un errore**
- Causa: la trappola `get` non lascia passare i Symbol
- Fix: `if (typeof chiave === 'symbol') return Reflect.get(...)` in cima

**Il Worker non parte: `Failed to construct 'Worker'`**
- Causa: percorso relativo non risolto dal bundler
- Fix: `new Worker(new URL('./file.worker.js', import.meta.url), { type: 'module' })`

**`DataCloneError` in `postMessage`**
- Causa: si sta inviando qualcosa di non clonabile — funzione, Symbol, nodo del DOM, Proxy
- Fix: inviare solo dati; ricostruire i metodi dall'altra parte

**`SharedArrayBuffer is not defined`**
- Causa: la pagina non è cross-origin isolated
- Fix: intestazioni COOP e COEP; verificare con `globalThis.crossOriginIsolated`

**`ERR_REQUIRE_ESM`**
- Causa: `require()` di un modulo che dichiara `"type": "module"`
- Fix: `await import()`, oppure convertire il chiamante a ESM

**`__dirname is not defined in ES module scope`**
- Causa: `__dirname` non esiste in ESM
- Fix: `import.meta.dirname`, o `fileURLToPath(import.meta.url)`

**Il tree shaking non elimina il codice non usato**
- Causa: manca `"sideEffects": false`, oppure gli import sono dinamici
- Fix: dichiarare `sideEffects` elencando i file che ne hanno

**Il test sul backoff dura secondi reali**
- Causa: timer veri invece che finti
- Fix: `vi.useFakeTimers()` e `await vi.runAllTimersAsync()`

**`vi.mock` non ha effetto**
- Causa: il modulo è stato importato staticamente prima del mock, oppure il percorso non corrisponde
- Fix: `await import()` dopo `vi.mock`; verificare che il percorso sia identico a quello del codice sotto test

**Il WebSocket resta "aperto" ma non arriva nulla**
- Causa: connessione morta a livello applicativo, TCP ancora aperto
- Fix: battito con ping e attesa del pong, e chiusura forzata se non risponde

---

## Prossimi passi

| Modulo | Collegamento con questo tutorial |
|---|---|
| `tutorial_06_typescript.md` | Tipizzare Promise, generici e risultati; `satisfies` e i tipi condizionali |
| `tutorial_07_react.md` | `useEffect` e la pulizia con `AbortController`; TanStack Query e la deduplicazione |
| `tutorial_10_nodejs.md` | Lo stesso linguaggio sul server: stream, worker threads, diagnostica |
| `tutorial_11_api_design.md` | Il server che risponde alle richieste costruite qui; retry e idempotenza |
| `tutorial_15_testing_web.md` | MSW, Playwright e il testing dei componenti |
| `tutorial_17_performance_web.md` | Long task, INP e il profiling del thread principale |
| `tutorial_23_websocket_security.md` | Autenticazione, validazione dei frame e scalabilità del client di chat |

---

## Risorse di riferimento

**Specifiche e documentazione:**
- [MDN — Using Promises](https://developer.mozilla.org/it/docs/Web/JavaScript/Guide/Using_promises)
- [MDN — Fetch API](https://developer.mozilla.org/it/docs/Web/API/Fetch_API)
- [MDN — Web Workers](https://developer.mozilla.org/it/docs/Web/API/Web_Workers_API)
- [MDN — Proxy](https://developer.mozilla.org/it/docs/Web/JavaScript/Reference/Global_Objects/Proxy)
- [TC39 — Decorators](https://github.com/tc39/proposal-decorators) — la proposta, allo stadio 3
- [Node.js — Modules: Packages](https://nodejs.org/api/packages.html) — `exports`, `imports`, condizioni

**Approfondimenti:**
- [Jake Archibald — In The Loop](https://www.youtube.com/watch?v=cCOL7MC4Pl0) — l'event loop, con le animazioni
- [web.dev — Optimize long tasks](https://web.dev/articles/optimize-long-tasks) — `scheduler.yield` e la cessione del controllo
- [Lin Clark — A cartoon intro to ArrayBuffers and SharedArrayBuffers](https://hacks.mozilla.org/2017/06/a-cartoon-intro-to-arraybuffers-and-sharedarraybuffers/)

**Strumenti:**
- [Vitest](https://vitest.dev/) — test runner, documentazione completa
- [fast-check](https://fast-check.dev/) — test basati su proprietà
- [Comlink](https://github.com/GoogleChromeLabs/comlink) — Worker con un'interfaccia a Promise, già pronta
- [es-module-shims](https://github.com/guybedford/es-module-shims) — import map dove non sono supportate

**Libri:**
- Kyle Simpson, *You Don't Know JS Yet: Async & Performance* — disponibile gratuitamente
- Nicolás Bevacqua, *Practical Modern JavaScript* — moduli, iterazione, proxy

---

> **Fine del Tutorial 05 — JavaScript Avanzato**
>
> Prossimo tutorial: `tutorial_06_typescript.md`
