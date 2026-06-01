---
corso: "Sviluppo Web"
fase: "2 — Linguaggi"
modulo: "05"
titolo: "JavaScript Avanzato"
versione: "ES2024+"
livello: "Intermedio-Avanzato"
prerequisiti:
  - "04 — JavaScript Fondamenti"
obiettivi:
  - "Padroneggiare prototipi, classi e ereditarieta"
  - "Utilizzare pattern avanzati: module, observer, proxy, iterator"
  - "Comprendere event loop, microtask e macrotask"
  - "Implementare Web Workers e SharedArrayBuffer"
  - "Gestire memoria e performance con WeakRef e FinalizationRegistry"
  - "Applicare metaprogrammazione con Proxy e Reflect"
tag: [JavaScript-avanzato, prototipi, event-loop, Proxy, Web-Workers, metaprogrammazione]
---

# JavaScript Avanzato — Guida Completa

> **Modulo 05** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [JavaScript Fondamenti](04-javascript-fondamenti.md)
>
> Al termine di questo modulo saprai:
> 1. Padroneggiare prototipi, classi e ereditarieta in JavaScript
> 2. Utilizzare pattern avanzati: module, observer, proxy, iterator
> 3. Comprendere event loop, microtask e macrotask
> 4. Implementare Web Workers e SharedArrayBuffer
> 5. Gestire memoria e performance con WeakRef e FinalizationRegistry
> 6. Applicare metaprogrammazione con Proxy e Reflect
>
> **Tempo stimato:** 6-8 ore · **Livello:** Intermedio-Avanzato

## Idee guida
1. **CORS: preflight cache + Private Network Access.**
2. **Web Workers per CPU-heavy senza block UI.**
3. **WeakMap/WeakRef per memory hygiene.**
4. **Iterator + AsyncIterator: streaming data clean.**


## Indice

1. [Panoramica](#panoramica)
2. [Programmazione Asincrona](#programmazione-asincrona)
3. [Memory Management e Garbage Collection](#memory-management-e-garbage-collection)
4. [Programmazione Funzionale](#programmazione-funzionale)
5. [Metaprogramming](#metaprogramming)
6. [Generatori e Iteratori](#generatori-e-iteratori)
7. [Design Pattern JavaScript](#design-pattern-javascript)
8. [Pattern Moderni](#pattern-moderni)
9. [Performance](#performance)
10. [Best Practices](#best-practices)
11. [Sistema di Moduli — Deep Dive](#sistema-di-moduli--deep-dive)
12. [Strategie di Gestione degli Errori](#strategie-di-gestione-degli-errori)
13. [Testing Avanzato](#testing-avanzato)

---

## Panoramica

JavaScript avanzato comprende un insieme di concetti, pattern e tecniche che vanno oltre la sintassi di base del linguaggio. Padroneggiare questi argomenti permette di scrivere codice più robusto, performante e manutenibile, qualità essenziali per lo sviluppo di applicazioni moderne di qualsiasi scala.

Questa guida esplora in profondità la programmazione asincrona, la gestione della memoria, la programmazione funzionale, il metaprogramming, i generatori, i design pattern classici e moderni, le tecniche di ottimizzazione delle performance e le best practice consolidate dalla comunità di sviluppatori. Ogni sezione include esempi pratici e spiegazioni dettagliate pensate per fornire una comprensione solida e applicabile nel lavoro quotidiano.

I prerequisiti per affrontare questo materiale includono una buona conoscenza delle basi di JavaScript: variabili, tipi di dato, funzioni, oggetti, array, classi, scope, closure e il funzionamento dell'event loop. Si consiglia di aver completato lo studio dei fondamenti prima di procedere.

L'evoluzione di JavaScript negli ultimi anni ha introdotto funzionalità che hanno trasformato radicalmente il modo di scrivere applicazioni. Le specifiche ECMAScript vengono aggiornate annualmente, e ogni versione porta miglioramenti significativi al linguaggio. Tra le aggiunte più rilevanti per lo sviluppo avanzato troviamo le Promise e async/await (ES2015-2017), i Proxy e Reflect (ES2015), i generatori (ES2015), i moduli nativi (ES2015), gli operatori di optional chaining e nullish coalescing (ES2020), e il top-level await (ES2022). Comprendere queste funzionalità nel contesto dei pattern architetturali è ciò che distingue uno sviluppatore JavaScript avanzato.

---

## Programmazione Asincrona

La programmazione asincrona è il cuore di JavaScript moderno. Poiché JavaScript è single-threaded, le operazioni che richiedono tempo (richieste di rete, lettura di file, timer) vengono gestite in modo non bloccante attraverso meccanismi asincroni.

### Callback Pattern

I callback rappresentano il meccanismo asincrono originale di JavaScript. Un callback è semplicemente una funzione passata come argomento a un'altra funzione, che verrà invocata al completamento di un'operazione.

**Error-first callbacks**: la convenzione stabilita da Node.js prevede che il primo parametro del callback sia riservato all'errore, mentre i parametri successivi contengano i dati risultanti.

```javascript
function leggiFile(percorso, callback) {
  fs.readFile(percorso, 'utf8', (errore, dati) => {
    if (errore) {
      callback(errore, null);
      return;
    }
    callback(null, dati);
  });
}

leggiFile('/dati/config.json', (errore, contenuto) => {
  if (errore) {
    console.error('Impossibile leggere il file:', errore.message);
    return;
  }
  console.log('Contenuto:', contenuto);
});
```

**Callback hell**: quando le operazioni asincrone dipendono l'una dall'altra, i callback annidati generano una struttura profondamente indentata, difficile da leggere e mantenere. Questo fenomeno è noto come "callback hell" o "pyramid of doom".

```javascript
// Esempio di callback hell
ottieniUtente(id, (errore, utente) => {
  if (errore) return gestisciErrore(errore);
  ottieniOrdini(utente.id, (errore, ordini) => {
    if (errore) return gestisciErrore(errore);
    ottieniDettagli(ordini[0].id, (errore, dettagli) => {
      if (errore) return gestisciErrore(errore);
      mostraRisultato(dettagli);
    });
  });
});
```

Questo problema è stato risolto con l'introduzione delle Promise.

### Promise

Una Promise rappresenta il risultato futuro di un'operazione asincrona. Può trovarsi in tre stati: **pending** (in attesa), **fulfilled** (risolta con successo) o **rejected** (rifiutata con errore).

**Costruttore Promise**: la funzione executor riceve due callback — `resolve` per il successo e `reject` per l'errore.

```javascript
const promessa = new Promise((resolve, reject) => {
  const operazioneRiuscita = true;

  if (operazioneRiuscita) {
    resolve({ messaggio: 'Operazione completata' });
  } else {
    reject(new Error('Operazione fallita'));
  }
});
```

**then(), catch(), finally()**: metodi per gestire il risultato della Promise.

```javascript
fetch('https://api.esempio.com/utenti')
  .then(risposta => {
    if (!risposta.ok) {
      throw new Error(`Errore HTTP: ${risposta.status}`);
    }
    return risposta.json();
  })
  .then(utenti => {
    console.log('Utenti ricevuti:', utenti.length);
    return utenti;
  })
  .catch(errore => {
    console.error('Richiesta fallita:', errore.message);
  })
  .finally(() => {
    console.log('Richiesta terminata (successo o errore)');
  });
```

**Metodi statici delle Promise**: permettono di orchestrare più operazioni asincrone in parallelo.

```javascript
const promesse = [
  fetch('/api/utenti'),
  fetch('/api/prodotti'),
  fetch('/api/ordini')
];

// Promise.all - attende TUTTE, fallisce se anche una sola fallisce
Promise.all(promesse)
  .then(risposte => console.log('Tutte completate'))
  .catch(errore => console.error('Almeno una fallita'));

// Promise.allSettled - attende TUTTE, non fallisce mai
Promise.allSettled(promesse)
  .then(risultati => {
    risultati.forEach(r => {
      if (r.status === 'fulfilled') {
        console.log('Successo:', r.value);
      } else {
        console.log('Errore:', r.reason);
      }
    });
  });

// Promise.race - restituisce la PRIMA che si risolve o rifiuta
Promise.race(promesse)
  .then(primaRisposta => console.log('Prima risposta ricevuta'));

// Promise.any - restituisce la PRIMA che si risolve con successo
Promise.any(promesse)
  .then(primoSuccesso => console.log('Primo successo'))
  .catch(errore => console.log('Tutte fallite:', errore));
```

**Promise chaining**: ogni chiamata a `.then()` restituisce una nuova Promise, permettendo di concatenare operazioni in sequenza leggibile.

```javascript
function elaboraDati(idUtente) {
  return ottieniUtente(idUtente)
    .then(utente => ottieniProfilo(utente.profiloId))
    .then(profilo => arricchisciProfilo(profilo))
    .then(profiloCompleto => salvaProfilo(profiloCompleto));
}
```

**Pattern di gestione degli errori**: è buona pratica centralizzare la gestione degli errori alla fine della catena e creare errori personalizzati per distinguere i diversi tipi di fallimento.

```javascript
class ErroreRete extends Error {
  constructor(messaggio, codiceStato) {
    super(messaggio);
    this.name = 'ErroreRete';
    this.codiceStato = codiceStato;
  }
}

fetch('/api/dati')
  .then(risposta => {
    if (!risposta.ok) {
      throw new ErroreRete('Richiesta fallita', risposta.status);
    }
    return risposta.json();
  })
  .catch(errore => {
    if (errore instanceof ErroreRete) {
      console.error(`Errore di rete (${errore.codiceStato}): ${errore.message}`);
    } else {
      console.error('Errore generico:', errore.message);
    }
  });
```

### async/await

La sintassi `async/await`, introdotta in ES2017, rappresenta zucchero sintattico costruito sopra le Promise. Permette di scrivere codice asincrono con un aspetto simile a quello sincrono.

```javascript
async function caricaDatiUtente(id) {
  try {
    const rispostaUtente = await fetch(`/api/utenti/${id}`);
    if (!rispostaUtente.ok) {
      throw new Error(`Utente non trovato: ${rispostaUtente.status}`);
    }
    const utente = await rispostaUtente.json();

    const rispostaOrdini = await fetch(`/api/ordini?utenteId=${utente.id}`);
    const ordini = await rispostaOrdini.json();

    return { utente, ordini };
  } catch (errore) {
    console.error('Errore nel caricamento:', errore.message);
    throw errore;
  }
}
```

**Esecuzione parallela**: quando le operazioni sono indipendenti tra loro, si possono eseguire in parallelo usando `Promise.all` combinato con `await`.

```javascript
async function caricaDashboard() {
  // ERRATO: esecuzione sequenziale non necessaria
  const utenti = await fetch('/api/utenti').then(r => r.json());
  const prodotti = await fetch('/api/prodotti').then(r => r.json());

  // CORRETTO: esecuzione parallela
  const [utenti2, prodotti2] = await Promise.all([
    fetch('/api/utenti').then(r => r.json()),
    fetch('/api/prodotti').then(r => r.json())
  ]);

  return { utenti: utenti2, prodotti: prodotti2 };
}
```

**Top-level await**: nei moduli ES, è possibile utilizzare `await` direttamente al livello superiore, senza incapsulare il codice in una funzione async.

```javascript
// modulo.mjs
const configurazione = await fetch('/config.json').then(r => r.json());
export default configurazione;
```

### Fetch API

La Fetch API è l'interfaccia moderna per effettuare richieste HTTP nel browser e in ambienti come Node.js (dalla versione 18+).

**Utilizzo base per i metodi HTTP principali**:

```javascript
// GET
const risposta = await fetch('https://api.esempio.com/risorse');
const dati = await risposta.json();

// POST con body JSON
const nuovaRisorsa = await fetch('https://api.esempio.com/risorse', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer token123'
  },
  body: JSON.stringify({ nome: 'Nuova risorsa', tipo: 'esempio' })
});

// PUT per aggiornamento
await fetch('https://api.esempio.com/risorse/1', {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ nome: 'Risorsa aggiornata' })
});

// DELETE
await fetch('https://api.esempio.com/risorse/1', {
  method: 'DELETE'
});
```

**Headers e FormData**: per inviare file o dati di form si utilizza `FormData`.

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('descrizione', 'Documento allegato');

const risposta = await fetch('/api/upload', {
  method: 'POST',
  body: formData
  // Non impostare Content-Type: il browser lo gestisce automaticamente
});
```

**Gestione degli errori**: `fetch` non rifiuta la Promise per errori HTTP (4xx, 5xx), ma solo per errori di rete. Bisogna controllare manualmente `response.ok`.

```javascript
async function richiestaConControllo(url, opzioni = {}) {
  const risposta = await fetch(url, opzioni);

  if (!risposta.ok) {
    const corpo = await risposta.text();
    throw new Error(
      `HTTP ${risposta.status} ${risposta.statusText}: ${corpo}`
    );
  }

  const contentType = risposta.headers.get('content-type');
  if (contentType?.includes('application/json')) {
    return risposta.json();
  }
  return risposta.text();
}
```

**AbortController per la cancellazione**: permette di annullare richieste in corso, utile per evitare race condition e risparmiare risorse.

```javascript
const controller = new AbortController();

// Annulla dopo 5 secondi (timeout)
const timeoutId = setTimeout(() => controller.abort(), 5000);

try {
  const risposta = await fetch('/api/dati-pesanti', {
    signal: controller.signal
  });
  clearTimeout(timeoutId);
  const dati = await risposta.json();
} catch (errore) {
  if (errore.name === 'AbortError') {
    console.log('Richiesta annullata');
  } else {
    throw errore;
  }
}
```

**Streaming delle risposte**: per dati di grandi dimensioni, è possibile leggere la risposta come stream.

```javascript
const risposta = await fetch('/api/file-grande');
const reader = risposta.body.getReader();
const decoder = new TextDecoder();
let risultato = '';

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  risultato += decoder.decode(value, { stream: true });
  console.log('Chunk ricevuto:', value.length, 'bytes');
}
```

### Pattern Asincroni Avanzati

#### Promise.withResolvers

Introdotto in ES2024, `Promise.withResolvers()` estrae `resolve` e `reject` dal costruttore Promise, eliminando la necessità del wrapper callback. Questo pattern è particolarmente utile quando la risoluzione della Promise avviene in un contesto diverso da quello di creazione.

```javascript
// Prima di ES2024: callback wrapper obbligatorio
function creaPromessaEsportabile() {
  let resolve, reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

// ES2024: sintassi nativa
const { promise, resolve, reject } = Promise.withResolvers();

// Caso d'uso: risolvere da un event listener
const { promise: attesaClick, resolve: completaClick } = Promise.withResolvers();
document.getElementById('conferma').addEventListener('click', () => {
  completaClick({ confermato: true, timestamp: Date.now() });
}, { once: true });

const risultato = await attesaClick;
```

#### Pattern Avanzati con i Promise Combinators

Oltre all'uso base di `Promise.all` e `Promise.race`, i combinatori possono essere composti per implementare pattern di concorrenza sofisticati.

```javascript
// Timeout pattern con Promise.race
function conTimeout(promessa, ms, messaggioErrore = 'Timeout') {
  const timeout = new Promise((_, reject) =>
    setTimeout(() => reject(new Error(messaggioErrore)), ms)
  );
  return Promise.race([promessa, timeout]);
}

// Retry con backoff esponenziale
async function conRitentativo(fn, opzioni = {}) {
  const { maxTentativi = 3, ritardoBaseMs = 1000, fattore = 2 } = opzioni;

  for (let tentativo = 0; tentativo < maxTentativi; tentativo++) {
    try {
      return await fn();
    } catch (errore) {
      if (tentativo === maxTentativi - 1) throw errore;
      const ritardo = ritardoBaseMs * Math.pow(fattore, tentativo);
      const jitter = ritardo * (0.5 + Math.random() * 0.5);
      await new Promise(r => setTimeout(r, jitter));
    }
  }
}

// Concorrenza limitata: esegui N promesse alla volta
async function poolConcorrente(tasks, maxConcorrenti = 5) {
  const risultati = [];
  const inEsecuzione = new Set();

  for (const [indice, task] of tasks.entries()) {
    const promessa = task().then(risultato => {
      inEsecuzione.delete(promessa);
      return risultato;
    });
    inEsecuzione.add(promessa);
    risultati[indice] = promessa;

    if (inEsecuzione.size >= maxConcorrenti) {
      await Promise.race(inEsecuzione);
    }
  }

  return Promise.all(risultati);
}

// Utilizzo: scarica 100 URL ma max 5 alla volta
const urls = Array.from({ length: 100 }, (_, i) => `https://api.esempio.com/item/${i}`);
const tasks = urls.map(url => () => fetch(url).then(r => r.json()));
const dati = await poolConcorrente(tasks, 5);
```

#### Async Iterators e for-await-of Avanzato

Gli async iterator estendono il protocollo iterator per gestire flussi di dati asincroni. A differenza dei generatori sincroni, ogni chiamata a `next()` restituisce una Promise di `{ value, done }`.

```javascript
// Async iterator manuale per polling
function pollingIterator(url, intervalloMs, signal) {
  return {
    [Symbol.asyncIterator]() {
      let fermato = false;
      signal?.addEventListener('abort', () => { fermato = true; });

      return {
        async next() {
          if (fermato) return { done: true };
          await new Promise(r => setTimeout(r, intervalloMs));
          if (fermato) return { done: true };

          const risposta = await fetch(url, { signal });
          const dati = await risposta.json();
          return { value: dati, done: false };
        },
        async return() {
          fermato = true;
          return { done: true };
        }
      };
    }
  };
}

// Consumo con for-await-of e AbortController
const controller = new AbortController();
setTimeout(() => controller.abort(), 30000); // ferma dopo 30s

for await (const stato of pollingIterator('/api/stato', 2000, controller.signal)) {
  console.log('Stato aggiornato:', stato);
  if (stato.completato) break;
}
```

```javascript
// Async generator per paginazione automatica
async function* paginaAutomatica(urlBase, dimensionePagina = 20) {
  let pagina = 1;
  let ciSonoAltrePagine = true;

  while (ciSonoAltrePagine) {
    const risposta = await fetch(
      `${urlBase}?_page=${pagina}&_limit=${dimensionePagina}`
    );
    const dati = await risposta.json();

    if (dati.length === 0) {
      ciSonoAltrePagine = false;
    } else {
      yield* dati; // yield ogni elemento individualmente
      pagina++;
      ciSonoAltrePagine = dati.length === dimensionePagina;
    }
  }
}

// Consumo: tutti i post paginati come un unico flusso
for await (const post of paginaAutomatica('https://api.esempio.com/posts')) {
  elaboraPost(post);
}
```

#### AbortController e AbortSignal — Pattern Avanzati

`AbortController` va oltre la semplice cancellazione di fetch. Le API moderne di `AbortSignal` permettono composizione, timeout e coordinamento tra operazioni multiple.

```javascript
// AbortSignal.timeout(): crea un signal che si attiva dopo N millisecondi
const risposta = await fetch('/api/dati', {
  signal: AbortSignal.timeout(5000) // timeout automatico di 5 secondi
});

// AbortSignal.any(): combina più signal in uno solo
function operazioneConCancellazione(signalUtente) {
  // L'operazione si annulla se l'utente cancella OPPURE dopo 10s
  const signalCombinato = AbortSignal.any([
    signalUtente,
    AbortSignal.timeout(10000)
  ]);

  return fetch('/api/operazione-lunga', { signal: signalCombinato });
}

// Pattern di cancellazione gerarchica
class GestoreOperazioni {
  #controllerPrincipale = new AbortController();

  creaOperazioneFiglia() {
    const controllerFiglio = new AbortController();
    // Il figlio si cancella se il padre si cancella
    this.#controllerPrincipale.signal.addEventListener('abort', () => {
      controllerFiglio.abort(this.#controllerPrincipale.signal.reason);
    });
    return controllerFiglio;
  }

  annullaTutto(motivo) {
    this.#controllerPrincipale.abort(motivo);
  }
}

// Utilizzo con addEventListener e cleanup
const controller2 = new AbortController();
elemento.addEventListener('click', gestoreClick, { signal: controller2.signal });
elemento.addEventListener('mouseover', gestoreHover, { signal: controller2.signal });
// Un singolo abort rimuove TUTTI i listener registrati con questo signal
controller2.abort();
```

#### Concorrenza Strutturata

La concorrenza strutturata è un paradigma che garantisce che le operazioni asincrone figlie non sopravvivano al loro scope genitore. In JavaScript, questo pattern viene implementato manualmente combinando `AbortController`, `Promise.allSettled` e `using` (la nuova dichiarazione di Explicit Resource Management, ES2024+).

```javascript
// Pattern di concorrenza strutturata manuale
async function conScopeAsincrono(fn) {
  const controller = new AbortController();

  try {
    return await fn(controller.signal);
  } finally {
    controller.abort(); // annulla tutto quando lo scope termina
  }
}

// Utilizzo: tutte le operazioni figlie muoiono con il genitore
await conScopeAsincrono(async (signal) => {
  const [utenti, prodotti] = await Promise.all([
    fetch('/api/utenti', { signal }).then(r => r.json()),
    fetch('/api/prodotti', { signal }).then(r => r.json())
  ]);
  return { utenti, prodotti };
});
// Se una fetch fallisce, l'altra viene automaticamente annullata

// Explicit Resource Management (Symbol.asyncDispose)
class RisorsaCancellabile {
  #controller = new AbortController();

  get signal() { return this.#controller.signal; }

  async [Symbol.asyncDispose]() {
    this.#controller.abort();
    // Cleanup addizionale: chiudi connessioni, rilascia lock, ecc.
  }
}

// Con la sintassi "await using" (ES2024+)
async function operazione() {
  await using risorsa = new RisorsaCancellabile();
  const dati = await fetch('/api/stream', { signal: risorsa.signal });
  return dati.json();
} // risorsa.[Symbol.asyncDispose]() chiamato automaticamente
```

---

## Memory Management e Garbage Collection

Comprendere come JavaScript gestisce la memoria è fondamentale per scrivere applicazioni performanti e prive di memory leak.

**Ciclo di vita della memoria**: ogni valore in JavaScript attraversa tre fasi — allocazione (quando viene creato), utilizzo (lettura e scrittura) e deallocazione (quando non è più necessario). L'allocazione e la deallocazione avvengono automaticamente, a differenza di linguaggi come C o C++.

**Strategie di Garbage Collection**:

- **Reference counting**: il metodo più semplice. Ogni oggetto mantiene un contatore dei riferimenti che lo puntano. Quando il contatore raggiunge zero, l'oggetto viene deallocato. Il limite principale è l'incapacità di gestire i riferimenti circolari.

- **Mark-and-sweep**: l'algoritmo utilizzato dai motori JavaScript moderni. Il GC parte dalla radice (global object, stack) e "marca" tutti gli oggetti raggiungibili. Successivamente, "spazza via" tutti gli oggetti non marcati. Questo approccio gestisce correttamente i riferimenti circolari.

**Memory leak comuni**: le cause più frequenti di perdita di memoria in JavaScript includono i seguenti scenari.

```javascript
// 1. Variabili globali accidentali
function creaLeakGlobale() {
  variabileDimenticata = 'Questa diventa globale!'; // manca "let" o "const"
}

// 2. Timer non rimossi
const intervalloId = setInterval(() => {
  const elemento = document.getElementById('output');
  if (elemento) {
    elemento.textContent = new Date().toLocaleString();
  }
  // Se l'elemento viene rimosso dal DOM, l'intervallo continua a girare
}, 1000);
// Soluzione: clearInterval(intervalloId) quando non serve più

// 3. Closure che trattengono riferimenti
function creaGestore() {
  const datiPesanti = new Array(1000000).fill('dati');
  return function() {
    // Questa closure mantiene in vita 'datiPesanti' anche se non lo usa
    console.log('Gestore chiamato');
  };
}

// 4. Nodi DOM distaccati
let riferimentoElemento = document.getElementById('pulsante');
document.body.removeChild(riferimentoElemento);
// L'elemento è rimosso dal DOM ma il riferimento in JS lo mantiene in memoria
// Soluzione: riferimentoElemento = null;
```

**WeakRef e FinalizationRegistry**: strumenti avanzati per scenari dove si necessita di riferimenti deboli che non impediscono la garbage collection.

```javascript
// WeakRef: riferimento debole a un oggetto
let oggettoOriginale = { dati: 'valore importante' };
const riferimentoDebole = new WeakRef(oggettoOriginale);

// Accesso al valore (potrebbe essere null se GC lo ha raccolto)
const valore = riferimentoDebole.deref();
if (valore) {
  console.log('Oggetto ancora disponibile:', valore.dati);
} else {
  console.log('Oggetto raccolto dal GC');
}

// FinalizationRegistry: esegue callback quando un oggetto viene raccolto
const registro = new FinalizationRegistry((identificatore) => {
  console.log(`Oggetto "${identificatore}" raccolto dal GC`);
  // Pulizia risorse esterne (chiudere connessioni, ecc.)
});

let risorsa = { connessione: 'database' };
registro.register(risorsa, 'connessione-db');
risorsa = null; // Quando il GC lo raccoglie, il callback viene invocato
```

**Performance API per la misurazione della memoria**:

```javascript
// Disponibile in Chrome/Chromium
if (performance.measureUserAgentSpecificMemory) {
  const memoryInfo = await performance.measureUserAgentSpecificMemory();
  console.log('Memoria utilizzata:', memoryInfo.bytes);
}

// API legacy (non standard ma ampiamente supportata)
if (performance.memory) {
  console.log('Heap totale:', performance.memory.totalJSHeapSize);
  console.log('Heap utilizzato:', performance.memory.usedJSHeapSize);
  console.log('Limite heap:', performance.memory.jsHeapSizeLimit);
}
```

**Debugging con Chrome DevTools**: la scheda Memory di Chrome DevTools offre tre strumenti principali. L'**Heap Snapshot** cattura un'istantanea dello heap e permette di esplorare tutti gli oggetti in memoria. L'**Allocation Timeline** registra le allocazioni nel tempo, evidenziando gli oggetti che non vengono deallocati. L'**Allocation Sampling** fornisce un campionamento a basso impatto sulle performance, utile per analisi prolungate in produzione. La strategia tipica prevede di acquisire uno snapshot, eseguire l'operazione sospetta, acquisire un secondo snapshot e confrontare le differenze per identificare gli oggetti che avrebbero dovuto essere deallocati.

### Pattern Avanzati con WeakRef e FinalizationRegistry

#### Cache Elastica con WeakRef

Le cache tradizionali con `Map` crescono senza limite. Combinando `WeakRef` con `FinalizationRegistry` si costruisce una cache che si adatta automaticamente alla pressione di memoria del sistema.

```javascript
class CacheElastica {
  #cache = new Map();
  #registro = new FinalizationRegistry((chiave) => {
    // Quando il GC raccoglie il valore, rimuovi la chiave dalla Map
    const ref = this.#cache.get(chiave);
    if (ref && ref.deref() === undefined) {
      this.#cache.delete(chiave);
    }
  });

  set(chiave, valore) {
    // Wrappa il valore in un oggetto per renderlo tracciabile dal GC
    const wrapper = { dati: valore };
    this.#cache.set(chiave, new WeakRef(wrapper));
    this.#registro.register(wrapper, chiave);
    return wrapper;
  }

  get(chiave) {
    const ref = this.#cache.get(chiave);
    if (!ref) return undefined;
    const wrapper = ref.deref();
    return wrapper ? wrapper.dati : undefined; // null se il GC ha raccolto
  }

  get dimensione() {
    // Conta solo le entry ancora vive
    let conteggio = 0;
    for (const [, ref] of this.#cache) {
      if (ref.deref() !== undefined) conteggio++;
    }
    return conteggio;
  }
}

const cache = new CacheElastica();
cache.set('utente:42', { nome: 'Marco', dati: new ArrayBuffer(1024 * 1024) });
// Se la memoria è sotto pressione, il GC può raccogliere i valori
// e il FinalizationRegistry pulisce le chiavi dalla Map
```

#### Gestione Risorse Esterne con FinalizationRegistry

`FinalizationRegistry` è utile per rilasciare risorse esterne (handle di file, connessioni, sottoscrizioni) quando l'oggetto JavaScript associato viene deallocato. **Attenzione**: il timing di esecuzione del callback è non deterministico. Non usarlo per logica critica — è una rete di sicurezza, non un meccanismo primario di cleanup.

```javascript
class PoolConnessioni {
  #connessioniAttive = new Map();
  #registro = new FinalizationRegistry((idConnessione) => {
    console.warn(`Connessione ${idConnessione} raccolta dal GC senza close()`);
    // Cleanup di emergenza — dovrebbe essere stato fatto esplicitamente
    this.#chiudiConnessioneRaw(idConnessione);
  });

  crea(config) {
    const id = crypto.randomUUID();
    const connessione = this.#apriConnessioneRaw(config);
    this.#connessioniAttive.set(id, connessione);

    const wrapper = { id, query: (sql) => connessione.exec(sql) };
    this.#registro.register(wrapper, id);
    return wrapper;
  }

  #apriConnessioneRaw(config) { /* ... */ }
  #chiudiConnessioneRaw(id) { /* ... */ }
}
```

#### Strumenti per la Rilevazione di Memory Leak

La rilevazione dei memory leak richiede strumenti specializzati e una metodologia sistematica.

**Chrome DevTools — Memory Panel**: offre tre modalità di analisi. L'*Heap Snapshot* cattura l'intero heap e permette di filtrare per costruttore, cercare oggetti specifici e identificare i "retainer" — gli oggetti che impediscono la garbage collection. L'*Allocation Instrumentation on Timeline* registra le allocazioni nel tempo e evidenzia gli oggetti che rimangono in memoria dopo che avrebbero dovuto essere deallocati. L'*Allocation Sampling* è adatto al monitoraggio in produzione per il suo basso overhead.

**Strategia a tre snapshot**: la tecnica più efficace per individuare leak consiste in tre passaggi. Primo: cattura uno snapshot iniziale (baseline). Secondo: esegui l'operazione sospetta più volte (navigazione di pagina, apertura e chiusura di dialog, ecc.). Terzo: cattura un secondo snapshot e confronta con il primo. Gli oggetti che crescono monotonicamente tra gli snapshot sono candidati leak. Un terzo snapshot dopo ulteriori ripetizioni conferma il trend.

```javascript
// Profilazione programmatica della memoria in Node.js
import v8 from 'node:v8';
import { writeFileSync } from 'node:fs';

function catturaDump(nome) {
  const filename = `${nome}-${Date.now()}.heapsnapshot`;
  writeFileSync(filename, v8.writeHeapSnapshot());
  console.log(`Heap dump salvato: ${filename}`);
}

// Cattura snapshot prima e dopo l'operazione sospetta
catturaDump('prima');
await operazioneSospetta();
globalThis.gc?.(); // richiede --expose-gc
catturaDump('dopo');
```

**`performance.measureUserAgentSpecificMemory()`**: API cross-origin aware disponibile in contesti con COOP/COEP headers. Misura la memoria attribuita a ogni origin, utile per identificare leak causati da iframe o script di terze parti.

---

## Programmazione Funzionale

La programmazione funzionale in JavaScript enfatizza l'uso di funzioni pure, l'immutabilità dei dati e la composizione di funzioni per costruire programmi complessi a partire da componenti semplici.

### Concetti

**Pure function**: una funzione pura restituisce sempre lo stesso output per lo stesso input e non produce effetti collaterali.

```javascript
// Pura: nessun effetto collaterale, risultato prevedibile
function somma(a, b) {
  return a + b;
}

// Impura: modifica stato esterno
let contatore = 0;
function incrementa() {
  contatore++; // Effetto collaterale
  return contatore;
}
```

**Immutabilità**: i dati non vengono modificati, ma si creano nuove copie con le modifiche applicate.

```javascript
// Mutazione (da evitare)
const utente = { nome: 'Marco', eta: 30 };
utente.eta = 31;

// Immutabilità (preferibile)
const utenteAggiornato = { ...utente, eta: 31 };

// Array immutabili
const numeri = [1, 2, 3];
const nuoviNumeri = [...numeri, 4]; // [1, 2, 3, 4]
const senzaPrimo = numeri.slice(1); // [2, 3]
```

**Higher-order function**: una funzione che accetta funzioni come argomenti o restituisce una funzione.

```javascript
function creaMultiplicatore(fattore) {
  return function(numero) {
    return numero * fattore;
  };
}

const doppio = creaMultiplicatore(2);
const triplo = creaMultiplicatore(3);

console.log(doppio(5));  // 10
console.log(triplo(5));  // 15
```

**Function composition**: combinare funzioni semplici per crearne di più complesse.

```javascript
const compose = (...funzioni) =>
  (valore) => funzioni.reduceRight((acc, fn) => fn(acc), valore);

const pipe = (...funzioni) =>
  (valore) => funzioni.reduce((acc, fn) => fn(acc), valore);

const aggiungiIva = (prezzo) => prezzo * 1.22;
const arrotonda = (numero) => Math.round(numero * 100) / 100;
const formattaPrezzo = (prezzo) => `${prezzo.toFixed(2)} EUR`;

const calcolaPrezzo = pipe(aggiungiIva, arrotonda, formattaPrezzo);
console.log(calcolaPrezzo(100)); // "122.00 EUR"
```

**Currying e partial application**: il currying trasforma una funzione che accetta più argomenti in una sequenza di funzioni che accettano un singolo argomento ciascuna.

```javascript
// Currying
const curry = (fn) => {
  const arita = fn.length;
  return function curried(...args) {
    if (args.length >= arita) {
      return fn(...args);
    }
    return (...altriArgs) => curried(...args, ...altriArgs);
  };
};

const sommaC = curry((a, b, c) => a + b + c);
console.log(sommaC(1)(2)(3));    // 6
console.log(sommaC(1, 2)(3));    // 6

// Partial application
function parziale(fn, ...argsIniziali) {
  return function(...argsRimanenti) {
    return fn(...argsIniziali, ...argsRimanenti);
  };
}

const logConPrefisso = parziale(console.log, '[APP]');
logConPrefisso('Server avviato'); // [APP] Server avviato
```

**Point-free style**: scrivere funzioni senza menzionare esplicitamente i dati su cui operano.

```javascript
// Con punto (riferimento esplicito al dato)
const numeriPari = numeri.filter(n => eParI(n));

// Point-free
const numeriPari2 = numeri.filter(ePari);
```

### Array come Funzionale

I metodi `map`, `filter` e `reduce` degli array sono i mattoni fondamentali della programmazione funzionale in JavaScript.

```javascript
const prodotti = [
  { nome: 'Laptop', prezzo: 999, categoria: 'elettronica' },
  { nome: 'Libro', prezzo: 15, categoria: 'cultura' },
  { nome: 'Tastiera', prezzo: 79, categoria: 'elettronica' },
  { nome: 'Penna', prezzo: 2, categoria: 'cancelleria' }
];

// Pipeline funzionale con map, filter, reduce
const totaleElettronica = prodotti
  .filter(p => p.categoria === 'elettronica')
  .map(p => p.prezzo)
  .reduce((totale, prezzo) => totale + prezzo, 0);

console.log(totaleElettronica); // 1078
```

**Pipeline pattern**: implementazione di una funzione `pipe` per elaborare dati attraverso trasformazioni sequenziali.

```javascript
const pipeline = (...trasformazioni) =>
  (datiIniziali) => trasformazioni.reduce(
    (dati, trasforma) => trasforma(dati),
    datiIniziali
  );

const elaboraProdotti = pipeline(
  (prodotti) => prodotti.filter(p => p.prezzo > 10),
  (prodotti) => prodotti.map(p => ({ ...p, prezzoIva: p.prezzo * 1.22 })),
  (prodotti) => prodotti.sort((a, b) => b.prezzoIva - a.prezzoIva)
);

const risultato = elaboraProdotti(prodotti);
```

**Concetto di transducer**: i transducer compongono trasformazioni senza creare array intermedi, migliorando le performance su grandi dataset. L'idea è separare la logica di trasformazione dal meccanismo di iterazione e accumulo.

```javascript
// Transducer semplificato
const mapT = (fn) => (reducer) => (acc, val) => reducer(acc, fn(val));
const filterT = (pred) => (reducer) => (acc, val) =>
  pred(val) ? reducer(acc, val) : acc;

const componiTransducer = (...xforms) =>
  xforms.reduce((a, b) => (reducer) => a(b(reducer)));

const xform = componiTransducer(
  filterT(n => n % 2 === 0),
  mapT(n => n * 10)
);

const risultato2 = [1, 2, 3, 4, 5].reduce(xform((acc, val) => [...acc, val]), []);
// [20, 40]
```

### Librerie

**Lodash/fp** fornisce una versione function-first, data-last delle utilità Lodash, ideale per la composizione funzionale. Le funzioni sono automaticamente curried e accettano i dati come ultimo argomento, rendendo naturale la composizione tramite `pipe` e `compose`.

```javascript
// Esempio con Lodash/fp
import { pipe, filter, map, sortBy, take } from 'lodash/fp';

const topProdottiCostosi = pipe(
  filter(p => p.disponibile),
  sortBy('prezzo'),
  map(p => p.nome),
  take(5)
);

const risultato = topProdottiCostosi(catalogo);
```

**Ramda** è progettata fin dall'inizio per la programmazione funzionale, con tutte le funzioni automaticamente curried e composte secondo il paradigma data-last. Offre un'ampia gamma di funzioni per lavorare con lenti (per accesso immutabile a strutture dati annidate), transducer nativi e utilità per la manipolazione funzionale di oggetti e array.

```javascript
// Esempio concettuale con Ramda
import * as R from 'ramda';

const ottieniNomiAttivi = R.pipe(
  R.filter(R.prop('attivo')),
  R.map(R.prop('nome')),
  R.sort(R.ascend(R.identity))
);
```

Entrambe le librerie offrono un ricco ecosistema di funzioni utilitarie immutabili e componibili. La scelta tra le due dipende dal contesto: Lodash/fp è preferibile quando si usa già Lodash nel progetto, mentre Ramda è ideale per progetti con un forte orientamento funzionale fin dall'inizio.

### Pattern Monadici in JavaScript

I pattern monadici forniscono un modo strutturato per gestire computazioni che possono fallire, produrre valori opzionali o avere effetti collaterali, mantenendo la componibilità funzionale.

#### Maybe (Option)

Il container `Maybe` incapsula un valore che potrebbe essere assente, eliminando i controlli `null`/`undefined` sparsi nel codice.

```javascript
class Maybe {
  #valore;
  constructor(valore) { this.#valore = valore; }

  static of(valore) { return new Maybe(valore); }
  static empty() { return new Maybe(null); }

  isNothing() {
    return this.#valore === null || this.#valore === undefined;
  }

  map(fn) {
    return this.isNothing() ? Maybe.empty() : Maybe.of(fn(this.#valore));
  }

  flatMap(fn) {
    return this.isNothing() ? Maybe.empty() : fn(this.#valore);
  }

  getOrElse(valorePredefinito) {
    return this.isNothing() ? valorePredefinito : this.#valore;
  }

  filter(predicato) {
    if (this.isNothing()) return Maybe.empty();
    return predicato(this.#valore) ? this : Maybe.empty();
  }
}

// Accesso sicuro a proprietà nidificate
const ottieniCitta = (utente) =>
  Maybe.of(utente)
    .map(u => u.indirizzo)
    .map(i => i.citta)
    .getOrElse('Città non specificata');

ottieniCitta({ indirizzo: { citta: 'Roma' } }); // "Roma"
ottieniCitta({ indirizzo: {} });                  // "Città non specificata"
ottieniCitta(null);                                // "Città non specificata"
```

#### Either (Result)

`Either` rappresenta una computazione che può riuscire (`Right`) o fallire (`Left`), trasportando informazioni sull'errore senza lanciare eccezioni.

```javascript
class Either {
  #valore;
  #isRight;

  constructor(valore, isRight) {
    this.#valore = valore;
    this.#isRight = isRight;
  }

  static right(valore) { return new Either(valore, true); }
  static left(errore) { return new Either(errore, false); }

  map(fn) {
    return this.#isRight ? Either.right(fn(this.#valore)) : this;
  }

  flatMap(fn) {
    return this.#isRight ? fn(this.#valore) : this;
  }

  fold(fnErrore, fnSuccesso) {
    return this.#isRight ? fnSuccesso(this.#valore) : fnErrore(this.#valore);
  }
}

// Pipeline che gestisce errori senza try/catch
function validaEmail(email) {
  return email.includes('@')
    ? Either.right(email)
    : Either.left('Email non valida: manca @');
}

function normalizzaEmail(email) {
  return Either.right(email.trim().toLowerCase());
}

const risultato = validaEmail('Utente@Email.COM')
  .flatMap(normalizzaEmail)
  .map(email => ({ email, verificata: false }))
  .fold(
    errore => ({ successo: false, errore }),
    dati => ({ successo: true, dati })
  );
// { successo: true, dati: { email: 'utente@email.com', verificata: false } }
```

#### Composizione Avanzata e Kleisli Composition

La composizione Kleisli permette di comporre funzioni che restituiscono container monadici (Maybe, Either, Promise) come se fossero funzioni semplici.

```javascript
// Kleisli composition per funzioni che restituiscono Maybe
const composeK = (...fns) =>
  (valore) => fns.reduce(
    (acc, fn) => acc.flatMap(fn),
    Maybe.of(valore)
  );

const ottieniPrimoProdotto = composeK(
  utente => Maybe.of(utente.carrello),
  carrello => Maybe.of(carrello.articoli),
  articoli => articoli.length > 0 ? Maybe.of(articoli[0]) : Maybe.empty(),
  articolo => Maybe.of(articolo.nome)
);
```

#### Transducer Avanzati

I transducer separano la logica di trasformazione dal meccanismo di riduzione, permettendo di comporre pipeline efficienti senza array intermedi. Questo pattern diventa critico su dataset con centinaia di migliaia di elementi.

```javascript
// Transducer completi con supporto per early termination
const RIDOTTO = Symbol('ridotto');
const ridotto = (valore) => ({ [RIDOTTO]: true, valore });
const nonRidotto = (v) => v?.[RIDOTTO] ? v.valore : v;

const mapT = (fn) => (passo) => (acc, val) => passo(acc, fn(val));
const filterT = (pred) => (passo) => (acc, val) =>
  pred(val) ? passo(acc, val) : acc;
const takeT = (n) => (passo) => {
  let contatore = 0;
  return (acc, val) => {
    if (contatore >= n) return ridotto(acc);
    contatore++;
    return passo(acc, val);
  };
};

function trasduce(xform, reducer, init, collezione) {
  const passoTrasformato = xform(reducer);
  let acc = init;
  for (const val of collezione) {
    acc = passoTrasformato(acc, val);
    if (acc?.[RIDOTTO]) return acc.valore;
  }
  return acc;
}

// Pipeline: filtra pari, moltiplica per 10, prendi i primi 3
const xform = (r) => filterT(n => n % 2 === 0)(mapT(n => n * 10)(takeT(3)(r)));
const risultatoT = trasduce(
  xform,
  (acc, val) => [...acc, val],
  [],
  [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
);
// [20, 40, 60] — nessun array intermedio creato, iterazione fermata al terzo
```

---

## Metaprogramming

Il metaprogramming permette di scrivere codice che manipola o estende il comportamento di altro codice a runtime. JavaScript offre strumenti potenti per questo paradigma.

### Proxy

Un `Proxy` crea un wrapper attorno a un oggetto target, intercettando le operazioni fondamentali tramite le "trap" definite nell'handler.

```javascript
// Proxy base con trap get e set
const utente = { nome: 'Anna', eta: 28 };

const utenteProxy = new Proxy(utente, {
  get(target, proprietà, receiver) {
    console.log(`Lettura proprietà: ${String(proprietà)}`);
    return Reflect.get(target, proprietà, receiver);
  },

  set(target, proprietà, valore, receiver) {
    console.log(`Scrittura: ${String(proprietà)} = ${valore}`);
    if (proprietà === 'eta' && (typeof valore !== 'number' || valore < 0)) {
      throw new TypeError('L\'età deve essere un numero positivo');
    }
    return Reflect.set(target, proprietà, valore, receiver);
  },

  has(target, proprietà) {
    console.log(`Controllo esistenza: ${String(proprietà)}`);
    return Reflect.has(target, proprietà);
  },

  deleteProperty(target, proprietà) {
    if (proprietà === 'nome') {
      throw new Error('La proprietà "nome" non può essere eliminata');
    }
    return Reflect.deleteProperty(target, proprietà);
  }
});
```

**Casi d'uso avanzati**:

```javascript
// Validazione automatica
function creaOggettoValidato(schema) {
  return new Proxy({}, {
    set(target, prop, valore) {
      if (schema[prop]) {
        const { tipo, richiesto, min, max } = schema[prop];
        if (tipo && typeof valore !== tipo) {
          throw new TypeError(`${prop} deve essere di tipo ${tipo}`);
        }
        if (min !== undefined && valore < min) {
          throw new RangeError(`${prop} deve essere >= ${min}`);
        }
        if (max !== undefined && valore > max) {
          throw new RangeError(`${prop} deve essere <= ${max}`);
        }
      }
      target[prop] = valore;
      return true;
    }
  });
}

const prodotto = creaOggettoValidato({
  prezzo: { tipo: 'number', min: 0 },
  nome: { tipo: 'string' }
});

prodotto.nome = 'Tastiera';   // OK
prodotto.prezzo = 79;          // OK
// prodotto.prezzo = -5;       // RangeError

// Proprietà virtuali e dati reattivi
function reattivo(oggetto, callback) {
  return new Proxy(oggetto, {
    set(target, prop, valore) {
      const vecchioValore = target[prop];
      target[prop] = valore;
      if (vecchioValore !== valore) {
        callback(prop, valore, vecchioValore);
      }
      return true;
    }
  });
}

const stato = reattivo({ contatore: 0 }, (prop, nuovo, vecchio) => {
  console.log(`${prop} cambiato: ${vecchio} -> ${nuovo}`);
  // Aggiorna la UI
});
stato.contatore = 1; // "contatore cambiato: 0 -> 1"
```

**Trap apply e construct**: intercettano rispettivamente la chiamata a funzione e l'uso di `new`.

```javascript
function logChiamate(fn) {
  return new Proxy(fn, {
    apply(target, thisArg, args) {
      console.log(`Chiamata ${target.name} con args:`, args);
      const risultato = Reflect.apply(target, thisArg, args);
      console.log(`Risultato:`, risultato);
      return risultato;
    },
    construct(target, args) {
      console.log(`Costruzione ${target.name} con args:`, args);
      return Reflect.construct(target, args);
    }
  });
}
```

### Reflect

L'oggetto `Reflect` fornisce metodi statici che corrispondono esattamente alle trap del Proxy. Il suo utilizzo all'interno delle trap garantisce il comportamento predefinito corretto e una migliore gestione degli errori rispetto all'accesso diretto alle proprietà. `Reflect.get`, `Reflect.set`, `Reflect.has`, `Reflect.deleteProperty`, `Reflect.apply` e `Reflect.construct` sono i metodi più utilizzati. La ragione principale per preferire Reflect è la coerenza: restituisce valori booleani per le operazioni di modifica anziché lanciare eccezioni, rendendo il codice più prevedibile.

### Symbol

I Symbol sono valori primitivi unici, spesso usati come chiavi di proprietà per evitare collisioni.

**Well-known symbols**: symbol predefiniti che personalizzano il comportamento degli oggetti.

```javascript
// Symbol.iterator: rende un oggetto iterabile
class Intervallo {
  constructor(inizio, fine) {
    this.inizio = inizio;
    this.fine = fine;
  }

  [Symbol.iterator]() {
    let corrente = this.inizio;
    const fine = this.fine;
    return {
      next() {
        if (corrente <= fine) {
          return { value: corrente++, done: false };
        }
        return { done: true };
      }
    };
  }
}

for (const n of new Intervallo(1, 5)) {
  console.log(n); // 1, 2, 3, 4, 5
}

// Symbol.toPrimitive: controlla la conversione a primitivo
class Valuta {
  constructor(importo, divisa) {
    this.importo = importo;
    this.divisa = divisa;
  }

  [Symbol.toPrimitive](suggerimento) {
    if (suggerimento === 'number') return this.importo;
    if (suggerimento === 'string') return `${this.importo} ${this.divisa}`;
    return this.importo;
  }
}

const prezzo = new Valuta(42.50, 'EUR');
console.log(+prezzo);      // 42.5
console.log(`${prezzo}`);  // "42.50 EUR"

// Symbol.toStringTag: personalizza Object.prototype.toString
class MiaCollezione {
  get [Symbol.toStringTag]() {
    return 'MiaCollezione';
  }
}
console.log(Object.prototype.toString.call(new MiaCollezione()));
// [object MiaCollezione]

// Symbol.hasInstance: personalizza instanceof
class NumeroPositivo {
  static [Symbol.hasInstance](valore) {
    return typeof valore === 'number' && valore > 0;
  }
}
console.log(5 instanceof NumeroPositivo);  // true
console.log(-3 instanceof NumeroPositivo); // false
```

**Symbol registry**: `Symbol.for()` crea symbol condivisi globalmente, recuperabili tramite la stessa chiave.

```javascript
const s1 = Symbol.for('chiave.condivisa');
const s2 = Symbol.for('chiave.condivisa');
console.log(s1 === s2); // true

console.log(Symbol.keyFor(s1)); // "chiave.condivisa"
```

### Catalogo Completo dei Proxy Trap

Un Proxy può intercettare 13 operazioni fondamentali. Ogni trap corrisponde a un metodo interno dell'oggetto definito dalla specifica ECMAScript.

| Trap | Operazione intercettata | Invocata da |
|---|---|---|
| `get(target, prop, receiver)` | Lettura di proprietà | `obj.prop`, `obj['prop']`, `Reflect.get()` |
| `set(target, prop, value, receiver)` | Scrittura di proprietà | `obj.prop = val`, `Reflect.set()` |
| `has(target, prop)` | Operatore `in` | `'prop' in obj`, `Reflect.has()` |
| `deleteProperty(target, prop)` | Operatore `delete` | `delete obj.prop`, `Reflect.deleteProperty()` |
| `apply(target, thisArg, args)` | Chiamata a funzione | `fn()`, `fn.call()`, `fn.apply()`, `Reflect.apply()` |
| `construct(target, args, newTarget)` | Operatore `new` | `new Fn()`, `Reflect.construct()` |
| `getOwnPropertyDescriptor(target, prop)` | Descriptor di proprietà | `Object.getOwnPropertyDescriptor()` |
| `defineProperty(target, prop, desc)` | Definizione proprietà | `Object.defineProperty()` |
| `getPrototypeOf(target)` | Lettura prototipo | `Object.getPrototypeOf()`, `instanceof` |
| `setPrototypeOf(target, proto)` | Modifica prototipo | `Object.setPrototypeOf()` |
| `isExtensible(target)` | Controllo estensibilità | `Object.isExtensible()` |
| `preventExtensions(target)` | Blocco estensioni | `Object.preventExtensions()` |
| `ownKeys(target)` | Enumerazione chiavi | `Object.keys()`, `Object.getOwnPropertyNames()`, `for...in` |

**Invarianti**: i trap devono rispettare invarianti definite dalla specifica. Ad esempio, `get` non può restituire un valore diverso da quello reale per proprietà non configurabili e non scrivibili. `has` non può nascondere proprietà non configurabili. `ownKeys` deve includere tutte le proprietà non configurabili. Violare queste invarianti causa un `TypeError` a runtime.

```javascript
// Esempio: Proxy con trap ownKeys per filtrare proprietà private
const oggettoConPrivate = {
  nome: 'API pubblica',
  _chiaveSegreta: 'valore-segreto',
  _tokenInterno: 'abc123',
  versione: '2.0'
};

const proxyFiltrato = new Proxy(oggettoConPrivate, {
  ownKeys(target) {
    return Reflect.ownKeys(target).filter(k =>
      typeof k === 'string' && !k.startsWith('_')
    );
  },
  getOwnPropertyDescriptor(target, prop) {
    if (typeof prop === 'string' && prop.startsWith('_')) return undefined;
    return Reflect.getOwnPropertyDescriptor(target, prop);
  }
});

console.log(Object.keys(proxyFiltrato)); // ['nome', 'versione']
console.log(JSON.stringify(proxyFiltrato)); // {"nome":"API pubblica","versione":"2.0"}
```

### Catalogo dei Metodi Reflect

`Reflect` fornisce metodi statici 1:1 con i Proxy trap. Il vantaggio rispetto alle operazioni dirette è la coerenza: restituiscono `boolean` per operazioni di modifica anziché lanciare eccezioni, e garantiscono il forwarding corretto del `receiver` nella catena prototipale.

| Metodo Reflect | Equivalente diretto | Differenza principale |
|---|---|---|
| `Reflect.get(target, prop, receiver)` | `target[prop]` | Rispetta il receiver per getter ereditati |
| `Reflect.set(target, prop, val, receiver)` | `target[prop] = val` | Restituisce `boolean`, rispetta setter |
| `Reflect.has(target, prop)` | `prop in target` | Forma funzionale dell'operatore `in` |
| `Reflect.deleteProperty(target, prop)` | `delete target[prop]` | Restituisce `boolean` anziché `true`/throw |
| `Reflect.apply(fn, thisArg, args)` | `Function.prototype.apply.call(fn, ...)` | Più sicuro — non dipende da `Function.prototype` |
| `Reflect.construct(Target, args, newTarget)` | `new Target(...args)` | Supporta `newTarget` per subclassing |
| `Reflect.ownKeys(target)` | `Object.getOwnPropertyNames(target).concat(Object.getOwnPropertySymbols(target))` | Singola chiamata per tutte le chiavi |
| `Reflect.defineProperty(target, prop, desc)` | `Object.defineProperty()` | Restituisce `boolean` anziché throw |

```javascript
// Pattern: Reflect per forwarding sicuro nei trap
const handler = {
  get(target, prop, receiver) {
    const valore = Reflect.get(target, prop, receiver);
    if (typeof valore === 'function') {
      return function(...args) {
        console.log(`Chiamata metodo: ${String(prop)}`);
        return Reflect.apply(valore, this === receiver ? target : this, args);
      };
    }
    return valore;
  }
};
```

### Decorators (TC39 Stage 3)

I decorator sono funzioni che modificano classi, metodi, accessor o campi al momento della definizione. La proposta TC39 Stage 3 è supportata da TypeScript 5.0+ e Babel, con una sintassi stabile che si avvicina alla finalizzazione nello standard.

```javascript
// Decorator di metodo: logging automatico
function log(target, context) {
  if (context.kind === 'method') {
    return function(...args) {
      console.log(`→ ${context.name}(${args.map(a => JSON.stringify(a)).join(', ')})`);
      const risultato = target.call(this, ...args);
      console.log(`← ${context.name} = ${JSON.stringify(risultato)}`);
      return risultato;
    };
  }
}

// Decorator di metodo: memoizzazione
function memo(target, context) {
  if (context.kind === 'method') {
    const cache = new Map();
    return function(...args) {
      const chiave = JSON.stringify(args);
      if (cache.has(chiave)) return cache.get(chiave);
      const risultato = target.call(this, ...args);
      cache.set(chiave, risultato);
      return risultato;
    };
  }
}

// Decorator di classe: sealed
function sealed(target, context) {
  if (context.kind === 'class') {
    Object.seal(target);
    Object.seal(target.prototype);
    return target;
  }
}

// Decorator di campo: validazione
function positivo(target, context) {
  if (context.kind === 'field') {
    return function(valoreIniziale) {
      if (typeof valoreIniziale !== 'number' || valoreIniziale < 0) {
        throw new RangeError(`${context.name} deve essere positivo`);
      }
      return valoreIniziale;
    };
  }
}

// Utilizzo combinato
@sealed
class Prodotto {
  @positivo prezzo;

  constructor(nome, prezzo) {
    this.nome = nome;
    this.prezzo = prezzo;
  }

  @log
  @memo
  calcolaSconto(percentuale) {
    return this.prezzo * (1 - percentuale / 100);
  }
}
```

I decorator vengono applicati dal basso verso l'alto (il decoratore più vicino al metodo viene eseguito per primo), ma la funzione risultante viene invocata dall'alto verso il basso. Nell'esempio sopra, `memo` wrappa il metodo originale, e poi `log` wrappa il risultato di `memo`.

**context.kind** indica il tipo di elemento decorato: `'class'`, `'method'`, `'getter'`, `'setter'`, `'field'`, o `'accessor'`. Il campo `context.name` contiene il nome dell'elemento, `context.static` indica se è statico, e `context.private` se è privato.

---

## Generatori e Iteratori

### Iteratori

Il protocollo **iterator** richiede che un oggetto implementi un metodo `next()` che restituisce `{ value, done }`. Il protocollo **iterable** richiede che l'oggetto implementi `[Symbol.iterator]()` restituendo un iterator.

```javascript
// Iterabile personalizzato: lista collegata
class Nodo {
  constructor(valore, prossimo = null) {
    this.valore = valore;
    this.prossimo = prossimo;
  }
}

class ListaCollegata {
  constructor() {
    this.testa = null;
  }

  aggiungi(valore) {
    this.testa = new Nodo(valore, this.testa);
    return this;
  }

  [Symbol.iterator]() {
    let corrente = this.testa;
    return {
      next() {
        if (corrente) {
          const valore = corrente.valore;
          corrente = corrente.prossimo;
          return { value: valore, done: false };
        }
        return { done: true };
      },
      return() {
        corrente = null;
        return { done: true };
      }
    };
  }
}

const lista = new ListaCollegata();
lista.aggiungi(3).aggiungi(2).aggiungi(1);
for (const valore of lista) {
  console.log(valore); // 1, 2, 3
}
```

### Generatori

Le funzioni generatore (`function*`) producono iteratori con una sintassi più concisa, sospendendo l'esecuzione a ogni `yield`.

```javascript
function* contatoreInfinito(inizio = 0) {
  let n = inizio;
  while (true) {
    yield n++;
  }
}

// Lazy evaluation: i valori vengono generati solo quando richiesti
const contatore = contatoreInfinito(1);
console.log(contatore.next().value); // 1
console.log(contatore.next().value); // 2

// Sequenze infinite utili
function* fibonacci() {
  let a = 0, b = 1;
  while (true) {
    yield a;
    [a, b] = [b, a + b];
  }
}

// Prendi i primi 10 numeri di Fibonacci
function prendi(generatore, n) {
  const risultati = [];
  for (const valore of generatore) {
    risultati.push(valore);
    if (risultati.length >= n) break;
  }
  return risultati;
}

console.log(prendi(fibonacci(), 10));
// [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
```

**Comunicazione bidirezionale**: `yield` può ricevere valori passati tramite `next(valore)`.

```javascript
function* accumulatore() {
  let totale = 0;
  while (true) {
    const valore = yield totale;
    if (valore === null) break;
    totale += valore;
  }
  return totale;
}

const acc = accumulatore();
acc.next();          // { value: 0, done: false } (avvia il generatore)
acc.next(10);        // { value: 10, done: false }
acc.next(20);        // { value: 30, done: false }
acc.next(null);      // { value: 30, done: true }
```

**Delegazione con yield***: permette a un generatore di delegare parte della sua iterazione a un altro iterabile.

```javascript
function* generaNumeri() {
  yield* [1, 2, 3];
}

function* generaLettere() {
  yield* 'abc';
}

function* generaTutto() {
  yield* generaNumeri();
  yield '-separatore-';
  yield* generaLettere();
}

console.log([...generaTutto()]);
// [1, 2, 3, '-separatore-', 'a', 'b', 'c']
```

**Generatori asincroni**: combinano generatori e async/await per iterare su flussi di dati asincroni.

```javascript
async function* flussoEventi(url) {
  const risposta = await fetch(url);
  const reader = risposta.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    yield decoder.decode(value);
  }
}

// Consumo con for await...of
async function elaboraFlusso() {
  for await (const chunk of flussoEventi('/api/stream')) {
    console.log('Chunk ricevuto:', chunk);
  }
}
```

---

## Design Pattern JavaScript

### Creazionali

**Module pattern**: utilizza le closure per creare uno scope privato, esponendo solo un'interfaccia pubblica.

```javascript
const GestoreCarrello = (() => {
  // Stato privato
  const articoli = [];

  // Metodi privati
  function calcolaTotale() {
    return articoli.reduce((sum, art) => sum + art.prezzo * art.quantita, 0);
  }

  // Interfaccia pubblica
  return {
    aggiungi(prodotto, quantita = 1) {
      const esistente = articoli.find(a => a.id === prodotto.id);
      if (esistente) {
        esistente.quantita += quantita;
      } else {
        articoli.push({ ...prodotto, quantita });
      }
    },
    rimuovi(prodottoId) {
      const indice = articoli.findIndex(a => a.id === prodottoId);
      if (indice > -1) articoli.splice(indice, 1);
    },
    totale: () => calcolaTotale(),
    conteggio: () => articoli.length
  };
})();
```

**Factory function**: funzione che crea e restituisce oggetti senza usare `new` o classi.

```javascript
function creaLogger(prefisso, livello = 'info') {
  const livelli = { debug: 0, info: 1, warn: 2, error: 3 };

  return {
    log(messaggio) {
      if (livelli[livello] <= livelli.info) {
        console.log(`[${prefisso}] ${messaggio}`);
      }
    },
    error(messaggio) {
      console.error(`[${prefisso}] ERRORE: ${messaggio}`);
    },
    impostaLivello(nuovoLivello) {
      livello = nuovoLivello;
    }
  };
}

const logApp = creaLogger('APP');
const logDb = creaLogger('DATABASE', 'warn');
```

**Singleton con WeakMap**: garantisce che una classe abbia una sola istanza.

```javascript
const istanze = new WeakMap();

class Database {
  constructor(config) {
    if (istanze.has(Database)) {
      return istanze.get(Database);
    }
    this.config = config;
    this.connessione = null;
    istanze.set(Database, this);
  }

  async connetti() {
    if (!this.connessione) {
      this.connessione = await creaConnessione(this.config);
    }
    return this.connessione;
  }
}
```

**Builder**: costruisce oggetti complessi passo dopo passo.

```javascript
class QueryBuilder {
  #tabella = '';
  #condizioni = [];
  #campi = ['*'];
  #limite = null;
  #ordinamento = null;

  from(tabella) {
    this.#tabella = tabella;
    return this;
  }

  select(...campi) {
    this.#campi = campi;
    return this;
  }

  where(condizione) {
    this.#condizioni.push(condizione);
    return this;
  }

  limit(n) {
    this.#limite = n;
    return this;
  }

  orderBy(campo, direzione = 'ASC') {
    this.#ordinamento = `${campo} ${direzione}`;
    return this;
  }

  build() {
    let query = `SELECT ${this.#campi.join(', ')} FROM ${this.#tabella}`;
    if (this.#condizioni.length) {
      query += ` WHERE ${this.#condizioni.join(' AND ')}`;
    }
    if (this.#ordinamento) query += ` ORDER BY ${this.#ordinamento}`;
    if (this.#limite) query += ` LIMIT ${this.#limite}`;
    return query;
  }
}

const query = new QueryBuilder()
  .from('utenti')
  .select('nome', 'email')
  .where('eta > 18')
  .where('attivo = true')
  .orderBy('nome')
  .limit(10)
  .build();
```

### Strutturali

**Facade**: fornisce un'interfaccia semplificata a un sottosistema complesso.

```javascript
class ApiFacade {
  #baseUrl;
  #headers;

  constructor(baseUrl, token) {
    this.#baseUrl = baseUrl;
    this.#headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
  }

  async #richiesta(metodo, percorso, body = null) {
    const opzioni = { method: metodo, headers: this.#headers };
    if (body) opzioni.body = JSON.stringify(body);

    const risposta = await fetch(`${this.#baseUrl}${percorso}`, opzioni);
    if (!risposta.ok) throw new Error(`HTTP ${risposta.status}`);
    return risposta.json();
  }

  ottieniUtenti() { return this.#richiesta('GET', '/utenti'); }
  creaUtente(dati) { return this.#richiesta('POST', '/utenti', dati); }
  aggiornaUtente(id, dati) { return this.#richiesta('PUT', `/utenti/${id}`, dati); }
  eliminaUtente(id) { return this.#richiesta('DELETE', `/utenti/${id}`); }
}
```

**Decorator funzionale**: aggiunge comportamento a una funzione senza modificarla.

```javascript
function conCache(fn, duratMs = 60000) {
  const cache = new Map();

  return function(...args) {
    const chiave = JSON.stringify(args);
    if (cache.has(chiave)) {
      const { valore, scadenza } = cache.get(chiave);
      if (Date.now() < scadenza) return valore;
    }
    const risultato = fn.apply(this, args);
    cache.set(chiave, { valore: risultato, scadenza: Date.now() + duratMs });
    return risultato;
  };
}

function conRitentativo(fn, maxTentativi = 3) {
  return async function(...args) {
    for (let i = 0; i < maxTentativi; i++) {
      try {
        return await fn.apply(this, args);
      } catch (errore) {
        if (i === maxTentativi - 1) throw errore;
        await new Promise(r => setTimeout(r, 1000 * Math.pow(2, i)));
      }
    }
  };
}

const ottieniDati = conRitentativo(conCache(fetch), 3);
```

**Adapter**: converte l'interfaccia di un componente in un'altra interfaccia attesa dal codice consumatore.

```javascript
// Adapter per normalizzare API diverse
class AdapterLocalStorage {
  async get(chiave) {
    const valore = localStorage.getItem(chiave);
    return valore ? JSON.parse(valore) : null;
  }

  async set(chiave, valore) {
    localStorage.setItem(chiave, JSON.stringify(valore));
  }

  async delete(chiave) {
    localStorage.removeItem(chiave);
  }
}

class AdapterIndexedDB {
  constructor(nomeDb) { this.nomeDb = nomeDb; }

  async get(chiave) {
    const db = await this.#apriDb();
    // ... logica IndexedDB
  }

  async set(chiave, valore) { /* ... */ }
  async delete(chiave) { /* ... */ }

  async #apriDb() { /* ... */ }
}

// Entrambi espongono la stessa interfaccia
function creaStorage(tipo) {
  return tipo === 'local'
    ? new AdapterLocalStorage()
    : new AdapterIndexedDB('app-storage');
}
```

### Comportamentali

**Observer / PubSub**: disaccoppia i componenti permettendo la comunicazione tramite eventi.

```javascript
class EventEmitter {
  #ascoltatori = new Map();

  on(evento, callback) {
    if (!this.#ascoltatori.has(evento)) {
      this.#ascoltatori.set(evento, new Set());
    }
    this.#ascoltatori.get(evento).add(callback);
    // Restituisce funzione per rimuovere il listener
    return () => this.off(evento, callback);
  }

  off(evento, callback) {
    this.#ascoltatori.get(evento)?.delete(callback);
  }

  emit(evento, ...dati) {
    this.#ascoltatori.get(evento)?.forEach(cb => {
      try {
        cb(...dati);
      } catch (errore) {
        console.error(`Errore in listener "${evento}":`, errore);
      }
    });
  }

  once(evento, callback) {
    const wrapper = (...args) => {
      this.off(evento, wrapper);
      callback(...args);
    };
    return this.on(evento, wrapper);
  }
}

const bus = new EventEmitter();
const rimuovi = bus.on('utente:login', (utente) => {
  console.log('Utente connesso:', utente.nome);
});
bus.emit('utente:login', { nome: 'Anna' });
rimuovi(); // Rimuove il listener
```

**Strategy**: incapsula algoritmi intercambiabili.

```javascript
const strategieOrdinamento = {
  perNome: (a, b) => a.nome.localeCompare(b.nome),
  perPrezzo: (a, b) => a.prezzo - b.prezzo,
  perPrezzoDesc: (a, b) => b.prezzo - a.prezzo,
  perPopolarita: (a, b) => b.vendite - a.vendite
};

function ordinaProdotti(prodotti, strategia = 'perNome') {
  const fn = strategieOrdinamento[strategia];
  if (!fn) throw new Error(`Strategia "${strategia}" non trovata`);
  return [...prodotti].sort(fn);
}
```

**Command**: incapsula un'operazione come oggetto, abilitando undo/redo.

```javascript
class GestoreComandi {
  #cronologia = [];
  #posizione = -1;

  esegui(comando) {
    // Rimuovi comandi futuri se siamo tornati indietro
    this.#cronologia.splice(this.#posizione + 1);
    comando.esegui();
    this.#cronologia.push(comando);
    this.#posizione++;
  }

  annulla() {
    if (this.#posizione < 0) return;
    this.#cronologia[this.#posizione].annulla();
    this.#posizione--;
  }

  ripeti() {
    if (this.#posizione >= this.#cronologia.length - 1) return;
    this.#posizione++;
    this.#cronologia[this.#posizione].esegui();
  }
}

class ComandoModificaTesto {
  constructor(editor, nuovoTesto) {
    this.editor = editor;
    this.nuovoTesto = nuovoTesto;
    this.testoPrecedente = null;
  }

  esegui() {
    this.testoPrecedente = this.editor.contenuto;
    this.editor.contenuto = this.nuovoTesto;
  }

  annulla() {
    this.editor.contenuto = this.testoPrecedente;
  }
}
```

**State machine**: gestisce transizioni di stato in modo prevedibile.

```javascript
class MacchinaAStati {
  #stato;
  #transizioni;

  constructor(statoIniziale, transizioni) {
    this.#stato = statoIniziale;
    this.#transizioni = transizioni;
  }

  get stato() { return this.#stato; }

  invia(evento) {
    const config = this.#transizioni[this.#stato];
    if (!config || !config[evento]) {
      throw new Error(
        `Transizione "${evento}" non valida dallo stato "${this.#stato}"`
      );
    }

    const { prossimo, azione } = config[evento];
    if (azione) azione();
    this.#stato = prossimo;
    return this.#stato;
  }
}

const semaforo = new MacchinaAStati('rosso', {
  rosso:    { cambia: { prossimo: 'verde',  azione: () => console.log('Via!') } },
  verde:    { cambia: { prossimo: 'giallo', azione: () => console.log('Attenzione!') } },
  giallo:   { cambia: { prossimo: 'rosso',  azione: () => console.log('Alt!') } }
});
```

#### State Machine con XState

XState è la libreria di riferimento per le macchine a stati in JavaScript. Implementa statechart (macchine a stati gerarchiche), il modello ad attori e la gestione degli effetti collaterali in modo deterministico e testabile.

```javascript
import { createMachine, createActor } from 'xstate';

// Definizione della macchina a stati per un form multi-step
const formMachine = createMachine({
  id: 'form',
  initial: 'datiPersonali',
  context: {
    nome: '',
    email: '',
    indirizzo: '',
    errori: {}
  },
  states: {
    datiPersonali: {
      on: {
        AVANTI: {
          target: 'contatto',
          guard: 'datiPersonaliValidi'
        },
        AGGIORNA: {
          actions: 'aggiornaCampo'
        }
      }
    },
    contatto: {
      on: {
        AVANTI: { target: 'conferma', guard: 'contattoValido' },
        INDIETRO: 'datiPersonali',
        AGGIORNA: { actions: 'aggiornaCampo' }
      }
    },
    conferma: {
      on: {
        INVIA: 'invio',
        INDIETRO: 'contatto'
      }
    },
    invio: {
      invoke: {
        src: 'inviaForm',
        onDone: 'successo',
        onError: 'errore'
      }
    },
    successo: { type: 'final' },
    errore: {
      on: { RIPROVA: 'invio' }
    }
  }
});

// Creazione dell'attore e sottoscrizione
const attore = createActor(formMachine);
attore.subscribe((stato) => {
  console.log('Stato corrente:', stato.value);
  aggiornUI(stato);
});
attore.start();
attore.send({ type: 'AGGIORNA', campo: 'nome', valore: 'Anna' });
attore.send({ type: 'AVANTI' });
```

I vantaggi di XState rispetto a una macchina a stati manuale includono: la visualizzazione grafica delle transizioni (via Stately.ai), la gestione esplicita degli stati impossibili (uno stato `invio` non può ricevere `AGGIORNA`), il supporto per stati paralleli e gerarchici, e il testing deterministico — ogni sequenza di eventi produce sempre lo stesso risultato.

#### Mediator Pattern

Il pattern Mediator centralizza la comunicazione tra componenti, riducendo le dipendenze dirette tra di essi. Mentre l'Observer accoppia il publisher ai subscriber (anche se debolmente), il Mediator introduce un coordinatore esplicito.

```javascript
class Mediator {
  #colleghi = new Map();

  registra(nome, componente) {
    this.#colleghi.set(nome, componente);
    componente.mediator = this;
  }

  invia(mittente, destinatario, messaggio) {
    const componente = this.#colleghi.get(destinatario);
    if (componente) {
      componente.ricevi(mittente, messaggio);
    }
  }

  broadcast(mittente, messaggio) {
    for (const [nome, componente] of this.#colleghi) {
      if (nome !== mittente) {
        componente.ricevi(mittente, messaggio);
      }
    }
  }
}

// Componenti che comunicano solo attraverso il mediator
class ChatRoom extends Mediator {
  registraUtente(nome) {
    const utente = {
      nome,
      ricevi(da, msg) {
        console.log(`[${this.nome}] Messaggio da ${da}: ${msg}`);
      },
      invia(a, msg) {
        this.mediator.invia(this.nome, a, msg);
      },
      broadcast(msg) {
        this.mediator.broadcast(this.nome, msg);
      }
    };
    this.registra(nome, utente);
    return utente;
  }
}

const chat = new ChatRoom();
const anna = chat.registraUtente('Anna');
const marco = chat.registraUtente('Marco');
anna.invia('Marco', 'Ciao!');
marco.broadcast('Riunione alle 15');
```

---

## Pattern Moderni

**Reactive programming**: la programmazione reattiva tratta i flussi di dati come stream da trasformare e combinare. RxJS è la libreria di riferimento in JavaScript e introduce il concetto di Observable, un flusso di valori nel tempo su cui applicare operatori come `map`, `filter`, `mergeMap`, `debounceTime` e `switchMap`. A differenza delle Promise, un Observable può emettere più valori nel tempo e supporta la cancellazione nativa.

```javascript
// Concetto base (semplificato, senza RxJS)
class Observable {
  constructor(sottoscrivi) {
    this._sottoscrivi = sottoscrivi;
  }

  subscribe(osservatore) {
    return this._sottoscrivi(osservatore);
  }

  pipe(...operatori) {
    return operatori.reduce((obs, op) => op(obs), this);
  }

  static fromEvent(elemento, evento) {
    return new Observable(osservatore => {
      const gestore = (e) => osservatore.next(e);
      elemento.addEventListener(evento, gestore);
      return { unsubscribe: () => elemento.removeEventListener(evento, gestore) };
    });
  }
}
```

**State management pattern**: la gestione centralizzata dello stato segue spesso il pattern Flux/Redux: uno store unico, azioni descrittive, reducer puri e sottoscrizioni per notificare la UI delle modifiche.

```javascript
function creaStore(reducer, statoIniziale) {
  let stato = statoIniziale;
  const ascoltatori = new Set();

  return {
    getState: () => stato,
    dispatch(azione) {
      stato = reducer(stato, azione);
      ascoltatori.forEach(fn => fn(stato));
    },
    subscribe(fn) {
      ascoltatori.add(fn);
      return () => ascoltatori.delete(fn);
    }
  };
}

function contaReducer(stato = 0, azione) {
  switch (azione.type) {
    case 'INCREMENTA': return stato + 1;
    case 'DECREMENTA': return stato - 1;
    case 'RESET': return 0;
    default: return stato;
  }
}

const store = creaStore(contaReducer, 0);
store.subscribe(stato => console.log('Nuovo stato:', stato));
store.dispatch({ type: 'INCREMENTA' }); // Nuovo stato: 1
```

**Middleware pattern**: i middleware intercettano e trasformano i dati in un punto della pipeline di elaborazione, comunemente usati nei framework per server HTTP.

```javascript
function creaPipeline() {
  const middleware = [];

  return {
    use(fn) {
      middleware.push(fn);
    },
    async esegui(contesto) {
      let indice = 0;

      async function prossimo() {
        if (indice < middleware.length) {
          const fn = middleware[indice++];
          await fn(contesto, prossimo);
        }
      }

      await prossimo();
      return contesto;
    }
  };
}

const pipeline = creaPipeline();
pipeline.use(async (ctx, next) => {
  ctx.inizio = Date.now();
  await next();
  console.log(`Tempo: ${Date.now() - ctx.inizio}ms`);
});
pipeline.use(async (ctx, next) => {
  ctx.dati = await fetch(ctx.url).then(r => r.json());
  await next();
});
```

**Plugin system**: consente di estendere un'applicazione senza modificare il codice sorgente.

```javascript
class App {
  #plugin = [];
  #hooks = new Map();

  use(plugin) {
    this.#plugin.push(plugin);
    plugin.installa(this);
    return this;
  }

  registraHook(nome, callback) {
    if (!this.#hooks.has(nome)) {
      this.#hooks.set(nome, []);
    }
    this.#hooks.get(nome).push(callback);
  }

  async eseguiHook(nome, contesto) {
    const hooks = this.#hooks.get(nome) || [];
    for (const hook of hooks) {
      await hook(contesto);
    }
  }
}

// Plugin di esempio
const pluginAutenticazione = {
  installa(app) {
    app.registraHook('prima-richiesta', async (ctx) => {
      const token = ctx.headers?.authorization;
      if (!token) throw new Error('Non autorizzato');
      ctx.utente = await verificaToken(token);
    });
  }
};

const miaApp = new App();
miaApp.use(pluginAutenticazione);
```

---

## Performance

L'ottimizzazione delle performance è cruciale per l'esperienza utente. Le tecniche seguenti coprono gli scenari piu comuni.

**Debounce e throttle**: limitano la frequenza di esecuzione di una funzione.

```javascript
// Debounce: esegue dopo che l'utente smette di agire
function debounce(fn, ritardo) {
  let timerId;
  return function(...args) {
    clearTimeout(timerId);
    timerId = setTimeout(() => fn.apply(this, args), ritardo);
  };
}

// Throttle: esegue al massimo una volta ogni N millisecondi
function throttle(fn, intervallo) {
  let ultimaEsecuzione = 0;
  return function(...args) {
    const adesso = Date.now();
    if (adesso - ultimaEsecuzione >= intervallo) {
      ultimaEsecuzione = adesso;
      fn.apply(this, args);
    }
  };
}

// Utilizzo
const cercaDebounced = debounce((query) => {
  fetch(`/api/cerca?q=${query}`);
}, 300);

const gestisciScrollThrottled = throttle(() => {
  aggiornaPosizioneScroll();
}, 100);

inputRicerca.addEventListener('input', (e) => cercaDebounced(e.target.value));
window.addEventListener('scroll', gestisciScrollThrottled);
```

**Web Worker per operazioni CPU-intensive**: i Web Worker eseguono codice in un thread separato, evitando di bloccare la UI.

```javascript
// worker.js
self.onmessage = function(evento) {
  const { dati, operazione } = evento.data;

  if (operazione === 'ordina') {
    const risultato = dati.sort((a, b) => a - b);
    self.postMessage({ risultato });
  }

  if (operazione === 'filtra') {
    const risultato = dati.filter(n => controlloComplesso(n));
    self.postMessage({ risultato });
  }
};

// main.js
const worker = new Worker('worker.js');

worker.postMessage({
  operazione: 'ordina',
  dati: arrayEnorme
});

worker.onmessage = (evento) => {
  console.log('Ordinamento completato:', evento.data.risultato);
};

// Terminazione del worker quando non serve più
worker.terminate();
```

**requestAnimationFrame per le animazioni**: sincronizza le animazioni con il refresh rate del display per movimenti fluidi.

```javascript
function animaElemento(elemento, proprieta, daValore, aValore, durataMs) {
  const inizio = performance.now();

  function frame(tempoCorrente) {
    const trascorso = tempoCorrente - inizio;
    const progresso = Math.min(trascorso / durataMs, 1);

    // Easing function (ease-out)
    const easing = 1 - Math.pow(1 - progresso, 3);
    const valoreCorrente = daValore + (aValore - daValore) * easing;

    elemento.style[proprieta] = `${valoreCorrente}px`;

    if (progresso < 1) {
      requestAnimationFrame(frame);
    }
  }

  requestAnimationFrame(frame);
}
```

**Virtual scrolling**: per liste con migliaia di elementi, il virtual scrolling renderizza solo gli elementi visibili nella viewport, riducendo drasticamente il numero di nodi DOM.

```javascript
// Implementazione semplificata del virtual scrolling
class VirtualScroller {
  constructor(contenitore, altezzaElemento, totalElementi, renderElemento) {
    this.contenitore = contenitore;
    this.altezzaElemento = altezzaElemento;
    this.totalElementi = totalElementi;
    this.renderElemento = renderElemento;

    // Contenitore con altezza totale simulata
    this.altezzaTotale = totalElementi * altezzaElemento;
    contenitore.style.overflow = 'auto';
    contenitore.style.position = 'relative';

    this.spazio = document.createElement('div');
    this.spazio.style.height = `${this.altezzaTotale}px`;
    contenitore.appendChild(this.spazio);

    contenitore.addEventListener('scroll', () => this.aggiorna());
    this.aggiorna();
  }

  aggiorna() {
    const scrollTop = this.contenitore.scrollTop;
    const altezzaVisibile = this.contenitore.clientHeight;

    const primoIndice = Math.floor(scrollTop / this.altezzaElemento);
    const ultimoIndice = Math.min(
      primoIndice + Math.ceil(altezzaVisibile / this.altezzaElemento) + 1,
      this.totalElementi
    );

    // Renderizza solo gli elementi visibili
    const elementiVisibili = [];
    for (let i = primoIndice; i < ultimoIndice; i++) {
      elementiVisibili.push(this.renderElemento(i));
    }
    // Aggiorna il DOM con i soli elementi visibili
  }
}
```

Il concetto prevede di calcolare quali elementi sono visibili in base alla posizione di scroll, renderizzare solo quelli e utilizzare un contenitore con altezza totale simulata per mantenere la scrollbar proporzionata. Librerie come `react-virtual` (TanStack Virtual) o `vue-virtual-scroller` implementano questo pattern in modo efficiente e gestiscono anche elementi con altezze variabili.

**Code splitting con dynamic import**: carica il codice solo quando necessario, riducendo il bundle iniziale.

```javascript
// Import statico: incluso nel bundle iniziale
import { funzioneBase } from './modulo-base.js';

// Dynamic import: caricato solo quando necessario
async function caricaEditor() {
  const { EditorAvanzato } = await import('./editor-avanzato.js');
  return new EditorAvanzato();
}

// Route-based splitting
const routes = {
  '/': () => import('./pagine/home.js'),
  '/profilo': () => import('./pagine/profilo.js'),
  '/impostazioni': () => import('./pagine/impostazioni.js')
};

async function naviga(percorso) {
  const caricaModulo = routes[percorso];
  if (caricaModulo) {
    const modulo = await caricaModulo();
    modulo.default.render();
  }
}
```

**Tree shaking**: i bundler moderni (webpack, Rollup, esbuild) eliminano automaticamente il codice non utilizzato quando si usano moduli ES. Per abilitarlo correttamente si deve usare `import/export` anziché `require/module.exports`, evitare effetti collaterali a livello di modulo e contrassegnare i pacchetti come `"sideEffects": false` nel `package.json` quando appropriato.

### Ottimizzazione per il JIT Compiler

I motori JavaScript moderni (V8 in Chrome/Node.js, SpiderMonkey in Firefox, JavaScriptCore in Safari) utilizzano compilatori JIT (Just-In-Time) che trasformano il codice JavaScript in codice macchina ottimizzato durante l'esecuzione. Comprendere come funziona il JIT permette di scrivere codice che il motore può ottimizzare efficacemente.

#### Hidden Classes (Shapes/Maps)

V8 assegna una "hidden class" (chiamata internamente *Map* o *Shape*) a ogni oggetto in base alle sue proprietà e all'ordine in cui sono state aggiunte. Oggetti con la stessa struttura condividono la stessa hidden class, permettendo al motore di ottimizzare l'accesso alle proprietà.

```javascript
// OTTIMALE: stessa forma, stessa hidden class
function creaUtenteBuono(nome, eta) {
  return { nome, eta }; // sempre le stesse proprietà, stesso ordine
}
const u1 = creaUtenteBuono('Anna', 28);
const u2 = creaUtenteBuono('Marco', 35);
// u1 e u2 condividono la hidden class → accesso veloce

// PROBLEMATICO: forme diverse, hidden class diverse
function creaUtenteCattivo(nome, eta, extra) {
  const utente = { nome };
  if (eta) utente.eta = eta;      // proprietà condizionale
  if (extra) utente.extra = extra; // ordine diverso
  return utente;
}
// Ogni combinazione produce una hidden class diversa → nessuna ottimizzazione

// EVITARE: delete cambia la hidden class e forza Dictionary Mode
const oggetto = { a: 1, b: 2, c: 3 };
delete oggetto.b; // V8 abbandona la hidden class, passa a Dictionary Mode
// Alternativa: oggetto.b = undefined; (mantiene la hidden class)
```

#### Inline Caching e Stati IC

L'inline caching (IC) è il meccanismo con cui V8 memorizza la posizione di una proprietà nella hidden class per evitare ricerche ripetute. Ogni sito di accesso a proprietà attraversa tre stati.

**Monomorfico** (1 shape): il sito accede sempre a oggetti con la stessa hidden class. V8 genera un controllo singolo e un caricamento diretto — la modalità più veloce.

**Polimorfico** (2-4 shapes): il sito incontra alcune forme diverse. V8 genera una catena lineare di controlli — ancora ragionevolmente veloce.

**Megamorfico** (>4 shapes): il sito incontra troppe forme diverse. V8 abbandona l'ottimizzazione per quel sito e usa una lookup generica nella hash table — significativamente più lento.

```javascript
// MONOMORFICO: tutti gli oggetti hanno la stessa forma
function calcolaArea(forma) {
  return forma.larghezza * forma.altezza;
}

// Se chiamata sempre con { larghezza, altezza }, il sito è monomorfico
calcolaArea({ larghezza: 10, altezza: 5 });
calcolaArea({ larghezza: 20, altezza: 8 });
// V8 ottimizza con un singolo controllo di hidden class

// MEGAMORFICO: forme eterogenee nello stesso sito
function elabora(obj) {
  return obj.valore; // se obj ha 5+ forme diverse, diventa megamorfico
}
elabora({ valore: 1 });
elabora({ valore: 2, extra: true });
elabora({ tipo: 'a', valore: 3 });
elabora({ x: 0, y: 0, valore: 4 });
elabora({ valore: 5, timestamp: Date.now(), id: 'abc' });
// Dopo 4+ forme, V8 marca il sito come megamorfico
```

#### Pattern JIT-Friendly

```javascript
// 1. Inizializza tutte le proprietà nel costruttore, stesso ordine
class Punto {
  constructor(x = 0, y = 0, z = 0) {
    this.x = x;
    this.y = y;
    this.z = z;
    // NON aggiungere proprietà dopo la costruzione
  }
}

// 2. Evita di cambiare tipo a una variabile
let valore = 42;     // V8 assume "number"
valore = 'stringa';  // V8 de-ottimizza — il tipo è cambiato

// 3. Array omogenei: mantieni lo stesso tipo
const numeri = [1, 2, 3, 4, 5];       // PACKED_SMI — velocissimo
numeri.push(3.14);                      // passa a PACKED_DOUBLE
numeri.push('stringa');                 // passa a PACKED_ELEMENTS — lento

// 4. Evita array "holey" (con buchi)
const denso = [1, 2, 3, 4, 5];        // PACKED — veloce
const bucato = [1, , 3, , 5];         // HOLEY — V8 deve controllare i buchi
const bucato2 = new Array(100);        // HOLEY — preferisci Array.from

// 5. Funzioni piccole e calde: V8 le inline automaticamente
function distanza(a, b) {
  return Math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2);
}
// Funzioni piccole chiamate spesso vengono "inlined" nel codice chiamante
```

---

## Best Practices

1. **Preferire `const` e `let` a `var`**: `const` per valori che non cambiano riferimento, `let` per variabili che necessitano di riassegnazione. `var` introduce problemi di hoisting e scope che generano bug difficili da individuare. L'uso consistente di `const` comunica l'intenzione del codice e previene riassegnazioni accidentali.

2. **Gestire sempre gli errori nelle operazioni asincrone**: ogni Promise deve avere un `.catch()` o essere racchiusa in un blocco `try/catch`. Le Promise non gestite generano `UnhandledPromiseRejection` che in Node.js possono terminare il processo. Implementare gestori globali come `window.addEventListener('unhandledrejection', handler)` come rete di sicurezza.

3. **Evitare la mutazione degli oggetti condivisi**: creare copie con lo spread operator o `structuredClone()` prima di modificare oggetti passati come parametri. La mutazione di dati condivisi rende il codice imprevedibile e genera bug difficili da riprodurre, specialmente in contesti asincroni dove l'ordine di esecuzione non e deterministico.

4. **Scrivere funzioni piccole e con un'unica responsabilità**: ogni funzione dovrebbe fare una sola cosa e farla bene. Funzioni brevi sono più facili da testare, riutilizzare e comprendere. Se una funzione supera le 20-30 righe o richiede più di 3-4 parametri, probabilmente andrebbe suddivisa.

5. **Usare i tipi quando possibile**: TypeScript o JSDoc con `@ts-check` forniscono type-safety che previene intere categorie di bug. Anche senza TypeScript, documentare i parametri attesi con JSDoc migliora l'esperienza di sviluppo grazie all'autocompletamento e alla documentazione inline dell'editor.

6. **Implementare pattern di cleanup per le risorse**: ogni `addEventListener` deve avere il corrispondente `removeEventListener`, ogni `setInterval` il suo `clearInterval`, ogni connessione il suo `close`. I framework moderni offrono meccanismi dedicati (come `useEffect` con la funzione di cleanup in React). Trascurare il cleanup porta inevitabilmente a memory leak.

7. **Evitare l'ottimizzazione prematura, ma conoscere i pattern costosi**: non ottimizzare fino a quando la misurazione non dimostra un collo di bottiglia. Tuttavia, evitare fin dall'inizio pattern notoriamente costosi come la creazione di oggetti in loop caldi, il DOM thrashing (letture e scritture DOM alternate) e le espressioni regolari compilate ripetutamente.

8. **Strutturare il codice in moduli coesi**: ogni modulo dovrebbe avere una responsabilità chiara e dipendenze minime. Usare `import/export` ES modules, preferire l'esportazione nominativa a quella default per una migliore ricercabilità e refactoring. Organizzare i file per funzionalità (feature) piuttosto che per tipo tecnico (tutti i controller insieme, tutti i servizi insieme).

9. **Adottare naming convention consistenti e descrittive**: usare `camelCase` per variabili e funzioni, `PascalCase` per classi e componenti, `UPPER_SNAKE_CASE` per costanti. I nomi delle funzioni dovrebbero descrivere l'azione eseguita (`calcolaTotale`, `validaEmail`), i nomi delle variabili dovrebbero descrivere il contenuto (`listaUtenti`, `conteggioOrdini`). Un codice ben denominato riduce drasticamente la necessità di commenti.

10. **Testare il codice in modo sistematico**: scrivere unit test per le funzioni pure e la logica di business, test di integrazione per i flussi principali e test end-to-end per i percorsi critici dell'utente. Seguire il pattern AAA (Arrange, Act, Assert) per strutturare i test. Utilizzare framework come Jest, Vitest o il test runner nativo di Node.js. Il codice senza test e codice che non si ha il coraggio di modificare.

---

## Sistema di Moduli — Deep Dive

Il sistema di moduli JavaScript ha attraversato un'evoluzione significativa, dai pattern ad hoc (IIFE, revealing module) a CommonJS (CJS) in Node.js, fino agli ECMAScript Modules (ESM) come standard del linguaggio. Comprendere l'interoperabilità tra questi sistemi e le funzionalità moderne è essenziale per lo sviluppo professionale.

### ESM vs CJS: Differenze Fondamentali

| Caratteristica | ESM (`import`/`export`) | CJS (`require`/`module.exports`) |
|---|---|---|
| Valutazione | Statica — analizzata prima dell'esecuzione | Dinamica — eseguita a runtime |
| Binding | Live binding — l'import riflette le modifiche | Copia del valore al momento del require |
| Top-level `this` | `undefined` | `module.exports` |
| Top-level `await` | Supportato | Non supportato |
| Tree shaking | Possibile (import statici) | Impossibile (require dinamici) |
| File extension (Node.js) | `.mjs` o `"type": "module"` in package.json | `.cjs` o default senza `"type"` |
| `__filename` / `__dirname` | Non disponibile — usare `import.meta.url` | Disponibile come globale |

```javascript
// ESM: equivalente di __dirname
import { fileURLToPath } from 'node:url';
import { dirname } from 'node:path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ESM: import.meta contiene metadati del modulo
console.log(import.meta.url);      // "file:///percorso/modulo.mjs"
console.log(import.meta.resolve('./lib.js')); // risolve il percorso
```

### Interoperabilità ESM/CJS

L'interoperabilità tra ESM e CJS ha regole precise che, se ignorate, causano errori a runtime.

**ESM può importare CJS**: Node.js esegue il modulo CJS in modo sincrono e wrappa `module.exports` come export default.

```javascript
// libreria-cjs.cjs
module.exports = { utilita: () => 'risultato' };
module.exports.VERSION = '1.0';

// consumatore-esm.mjs
import libreria from './libreria-cjs.cjs';     // intero module.exports come default
console.log(libreria.utilita());                // 'risultato'

// Named imports funzionano solo se Node.js riesce a fare static analysis
import { utilita } from './libreria-cjs.cjs';   // funziona in molti casi
```

**CJS non può require() ESM (tradizionalmente)**: poiché ESM supporta top-level await, è intrinsecamente asincrono. La soluzione storica era `await import()`.

```javascript
// consumatore-cjs.cjs — prima di Node 22
async function carica() {
  const { default: modulo } = await import('./modulo-esm.mjs');
  return modulo;
}

// Node 22+: require() di ESM è supportato (sperimentale)
// Funziona solo se il modulo ESM NON usa top-level await
const modulo = require('./modulo-esm.mjs'); // Node 22+ con --experimental-require-module
```

**Dual package pattern**: per librerie che devono supportare sia ESM che CJS, il `package.json` usa il campo `exports` con conditional exports.

```json
{
  "name": "mia-libreria",
  "exports": {
    ".": {
      "import": "./dist/esm/index.mjs",
      "require": "./dist/cjs/index.cjs",
      "types": "./dist/types/index.d.ts"
    },
    "./utils": {
      "import": "./dist/esm/utils.mjs",
      "require": "./dist/cjs/utils.cjs"
    }
  }
}
```

### Dynamic Import

`import()` è un'espressione (non una dichiarazione) che restituisce una Promise del namespace del modulo. A differenza degli import statici, può essere usata ovunque — in condizionali, loop, funzioni.

```javascript
// Caricamento condizionale basato sull'ambiente
const logger = await import(
  process.env.NODE_ENV === 'production'
    ? './logger-prod.js'
    : './logger-dev.js'
);

// Caricamento di moduli basato su input dell'utente
async function caricaPlugin(nome) {
  try {
    const plugin = await import(`./plugins/${nome}.js`);
    return plugin.default;
  } catch (errore) {
    if (errore.code === 'ERR_MODULE_NOT_FOUND') {
      console.warn(`Plugin "${nome}" non trovato, uso fallback`);
      return await import('./plugins/fallback.js').then(m => m.default);
    }
    throw errore;
  }
}

// Preload: avvia il download senza attendere
const moduloPromise = import('./modulo-pesante.js');
// ... altro codice ...
const modulo = await moduloPromise; // il download è già partito
```

### Import Maps

Le import map permettono di controllare la risoluzione dei moduli direttamente nel browser, senza bundler. Sono supportate da tutti i browser moderni dal 2023.

```html
<script type="importmap">
{
  "imports": {
    "lodash": "https://cdn.jsdelivr.net/npm/lodash-es@4.17.21/lodash.js",
    "react": "https://esm.sh/react@18",
    "react-dom": "https://esm.sh/react-dom@18",
    "@mia-app/": "./src/",
    "#utils": "./src/lib/utils.js"
  },
  "scopes": {
    "/vendor/": {
      "lodash": "https://cdn.jsdelivr.net/npm/lodash-es@4.17.15/lodash.js"
    }
  }
}
</script>

<script type="module">
// Ora funziona senza bundler — la import map risolve i bare specifier
import _ from 'lodash';
import React from 'react';
import { formatta } from '#utils';
import { Header } from '@mia-app/components/Header.js';
</script>
```

Il campo `scopes` permette di avere risoluzioni diverse per moduli caricati da percorsi specifici — utile per gestire versioni multiple della stessa dipendenza senza conflitti.

### Import Attributes (ex Import Assertions)

Le import attributes (rinominate da "assertions" a "attributes" nella proposta TC39) permettono di specificare metadati sull'importazione, come il tipo atteso del modulo.

```javascript
// Importare JSON come modulo
import config from './config.json' with { type: 'json' };
console.log(config.database.host);

// Dynamic import con attributi
const traduzioni = await import('./it-IT.json', { with: { type: 'json' } });

// Importare CSS come modulo (con Constructable Stylesheets)
import stili from './componente.css' with { type: 'css' };
document.adoptedStyleSheets = [...document.adoptedStyleSheets, stili];
```

La keyword `with` ha sostituito la precedente `assert` (deprecata). Le import attributes forniscono un meccanismo di sicurezza: il runtime verifica che il tipo dichiarato corrisponda al tipo effettivo del modulo, prevenendo l'esecuzione accidentale di codice mascherato da JSON o CSS.

### Raccomandazioni per la Migrazione a ESM

La migrazione da CJS a ESM richiede attenzione a diversi aspetti pratici. Aggiungere `"type": "module"` al `package.json` rende tutti i file `.js` ESM per default — i file CJS residui devono essere rinominati in `.cjs`. Le variabili globali CJS (`__dirname`, `__filename`, `require`, `module`, `exports`) non sono disponibili in ESM e devono essere sostituite con `import.meta.url` e le utility di `node:path` e `node:url`. I file di configurazione (`.eslintrc.js`, `jest.config.js`, `tailwind.config.js`) potrebbero richiedere l'estensione `.cjs` se il tool non supporta ancora ESM. Il campo `exports` in `package.json` deve essere aggiornato con entry point espliciti. Testare la compatibilità con le dipendenze è critico: alcune librerie CJS-only potrebbero non funzionare correttamente con il default import ESM. La strategia raccomandata nel 2025 è adottare ESM per tutti i nuovi progetti e migrare gradualmente i progetti esistenti, mantenendo la compatibilità dual-package tramite il campo `exports` durante la transizione.

---

## Strategie di Gestione degli Errori

Una strategia di gestione degli errori robusta è la differenza tra un'applicazione che fallisce in modo comprensibile e una che presenta comportamenti inspiegabili. JavaScript moderno offre strumenti per costruire catene di errori informative, gestori globali e gerarchie di errori personalizzati.

### Error.cause — Catene di Errori

Introdotto in ES2022, il parametro `cause` nel costruttore `Error` permette di creare catene di errori che preservano il contesto originale attraverso i layer dell'applicazione.

```javascript
// Layer di accesso dati
async function queryDatabase(sql) {
  try {
    return await db.execute(sql);
  } catch (errore) {
    throw new Error(`Query fallita: ${sql}`, { cause: errore });
  }
}

// Layer di servizio
async function ottieniUtente(id) {
  try {
    return await queryDatabase(`SELECT * FROM utenti WHERE id = ${id}`);
  } catch (errore) {
    throw new Error(`Impossibile ottenere utente ${id}`, { cause: errore });
  }
}

// Layer API
async function gestisciRichiesta(req, res) {
  try {
    const utente = await ottieniUtente(req.params.id);
    res.json(utente);
  } catch (errore) {
    // Navigazione della catena di cause
    console.error('Errore API:', errore.message);
    let causa = errore.cause;
    while (causa) {
      console.error('  Causato da:', causa.message);
      causa = causa.cause;
    }
    res.status(500).json({ errore: 'Errore interno del server' });
  }
}
```

```javascript
// Helper per estrarre l'intera catena di cause
function catenaErrori(errore) {
  const catena = [];
  let corrente = errore;
  while (corrente) {
    catena.push({
      nome: corrente.name,
      messaggio: corrente.message,
      stack: corrente.stack
    });
    corrente = corrente.cause;
  }
  return catena;
}

// Helper per logging strutturato della catena
function logCatenaErrori(errore, logger = console) {
  const catena = catenaErrori(errore);
  logger.group(`Errore: ${catena[0].messaggio}`);
  catena.forEach((livello, indice) => {
    const prefisso = indice === 0 ? 'Errore primario' : `Causa (livello ${indice})`;
    logger.error(`${prefisso}: [${livello.nome}] ${livello.messaggio}`);
  });
  logger.groupEnd();
}
```

La catena di cause non viene visualizzata automaticamente da `console.error()`. È necessario attraversarla esplicitamente. Questo design è intenzionale: permette ai livelli superiori dell'applicazione di decidere quanta profondità esporre nei log e quali dettagli nascondere nelle risposte rivolte all'utente finale.

**Best practice per Error.cause**: usare `cause` quando si rielancia un errore a un livello di astrazione superiore, aggiungendo contesto specifico del layer corrente. Non concatenare ogni errore minore — catene troppo profonde rendono il debugging più confuso, non meno.

### Gerarchia di Errori Personalizzati

Definire errori specifici per dominio permette di implementare logica di gestione differenziata nei catch block.

```javascript
// Base per errori applicativi
class ErroreApplicazione extends Error {
  constructor(messaggio, opzioni = {}) {
    super(messaggio, { cause: opzioni.cause });
    this.name = this.constructor.name;
    this.codice = opzioni.codice ?? 'ERRORE_GENERICO';
    this.timestamp = new Date().toISOString();
  }
}

class ErroreValidazione extends ErroreApplicazione {
  constructor(campo, messaggio, opzioni = {}) {
    super(messaggio, opzioni);
    this.codice = opzioni.codice ?? 'VALIDAZIONE_FALLITA';
    this.campo = campo;
  }
}

class ErroreAutorizzazione extends ErroreApplicazione {
  constructor(messaggio, opzioni = {}) {
    super(messaggio, opzioni);
    this.codice = opzioni.codice ?? 'NON_AUTORIZZATO';
    this.statusHttp = 403;
  }
}

class ErroreRisorsaNonTrovata extends ErroreApplicazione {
  constructor(risorsa, id, opzioni = {}) {
    super(`${risorsa} con id "${id}" non trovato`, opzioni);
    this.codice = 'NON_TROVATO';
    this.risorsa = risorsa;
    this.idRisorsa = id;
    this.statusHttp = 404;
  }
}

// Gestione tipizzata nel catch
try {
  await aggiornaUtente(id, dati);
} catch (errore) {
  if (errore instanceof ErroreValidazione) {
    mostraErroreCampo(errore.campo, errore.message);
  } else if (errore instanceof ErroreRisorsaNonTrovata) {
    mostraNotifica(`${errore.risorsa} non trovato`);
  } else if (errore instanceof ErroreAutorizzazione) {
    reindirizzaLogin();
  } else {
    segnalaErroreNonPrevisto(errore);
  }
}
```

### Gestori Globali

I gestori globali catturano errori che sfuggono a tutti i blocchi `try/catch` locali. Sono una rete di sicurezza, non un sostituto della gestione esplicita.

```javascript
// Browser: errori sincroni non catturati
window.addEventListener('error', (evento) => {
  console.error('Errore globale:', evento.message);
  console.error('File:', evento.filename, 'Riga:', evento.lineno);
  // Invia al servizio di monitoraggio
  inviaATelemetria({
    tipo: 'errore_non_catturato',
    messaggio: evento.message,
    stack: evento.error?.stack,
    url: evento.filename,
    riga: evento.lineno,
    colonna: evento.colno
  });
  // evento.preventDefault() — impedisce il log in console
});

// Browser: Promise rejection non gestite
window.addEventListener('unhandledrejection', (evento) => {
  console.error('Promise rejection non gestita:', evento.reason);
  inviaATelemetria({
    tipo: 'promise_non_gestita',
    motivo: evento.reason?.message ?? String(evento.reason),
    stack: evento.reason?.stack
  });
  evento.preventDefault();
});

// Node.js: equivalenti
process.on('uncaughtException', (errore, origin) => {
  console.error(`Eccezione non catturata (${origin}):`, errore);
  // In produzione: log, cleanup e termina il processo
  process.exit(1);
});

process.on('unhandledRejection', (motivo, promise) => {
  console.error('Promise rejection non gestita:', motivo);
});
```

### Pattern Safe-Try (Result Pattern senza Monade)

Un pattern leggero ispirato a Go e Rust che evita `try/catch` ripetitivi restituendo una tupla `[errore, risultato]`.

```javascript
async function safeTry(fn) {
  try {
    const risultato = await fn();
    return [null, risultato];
  } catch (errore) {
    return [errore, null];
  }
}

// Utilizzo: elimina i try/catch nidificati
async function caricaPaginaUtente(id) {
  const [errUtente, utente] = await safeTry(() => ottieniUtente(id));
  if (errUtente) return { errore: 'Utente non trovato' };

  const [errOrdini, ordini] = await safeTry(() => ottieniOrdini(utente.id));
  if (errOrdini) return { utente, ordini: [], avviso: 'Ordini non disponibili' };

  return { utente, ordini };
}
```

---

## Testing Avanzato

Il testing avanzato in JavaScript moderno va oltre il semplice `expect(valore).toBe(atteso)`. Comprende strategie di mocking per moduli ESM, snapshot testing, testing di codice asincrono complesso e la configurazione di ambienti di test realistici.

### Vitest — Il Test Runner Moderno

Vitest è un test runner ESM-first costruito su Vite. A differenza di Jest (che simula ESM tramite trasformazioni CJS), Vitest esegue il codice attraverso la pipeline di moduli di Vite, supportando nativamente `import.meta`, top-level `await` e file `.mjs`. La configurazione è condivisa con `vite.config`, eliminando duplicazione.

```javascript
// vitest.config.js — condivide la configurazione con Vite
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,           // describe, it, expect globali
    environment: 'jsdom',     // o 'node', 'happy-dom'
    coverage: {
      provider: 'v8',        // o 'istanbul'
      reporter: ['text', 'html', 'lcov'],
      thresholds: {
        branches: 80,
        functions: 80,
        lines: 80,
        statements: 80
      }
    },
    include: ['src/**/*.{test,spec}.{js,ts}'],
    setupFiles: ['./tests/setup.js']
  }
});
```

### Mocking di Moduli ESM

Il mocking di moduli ESM presenta sfide specifiche perché i namespace ESM sono sealed objects — non è possibile sovrascrivere i loro export direttamente. Vitest risolve questo problema con `vi.mock()`, che trasforma gli import statici in dinamici e registra i mock prima del caricamento del modulo.

```javascript
// modulo-sotto-test.js
import { ottieniDati } from './servizio-api.js';
import { formatta } from './utils.js';

export async function caricaERenderizza(id) {
  const dati = await ottieniDati(id);
  return formatta(dati);
}

// modulo-sotto-test.test.js
import { describe, it, expect, vi } from 'vitest';

// Mock dell'intero modulo
vi.mock('./servizio-api.js', () => ({
  ottieniDati: vi.fn()
}));

// Mock parziale: mantieni le implementazioni reali eccetto quelle specificate
vi.mock('./utils.js', async (importOriginal) => {
  const modulo = await importOriginal();
  return {
    ...modulo,
    formatta: vi.fn((dati) => `MOCK: ${JSON.stringify(dati)}`)
  };
});

import { ottieniDati } from './servizio-api.js';
import { caricaERenderizza } from './modulo-sotto-test.js';

describe('caricaERenderizza', () => {
  it('chiama ottieniDati e formatta il risultato', async () => {
    ottieniDati.mockResolvedValue({ nome: 'Test', id: 1 });

    const risultato = await caricaERenderizza(1);

    expect(ottieniDati).toHaveBeenCalledWith(1);
    expect(risultato).toContain('MOCK:');
  });

  it('gestisce errori del servizio', async () => {
    ottieniDati.mockRejectedValue(new Error('Network error'));

    await expect(caricaERenderizza(1)).rejects.toThrow('Network error');
  });
});
```

```javascript
// Spy mode: osserva senza sostituire
vi.mock('./analytics.js', { spy: true });

import { tracciaEvento } from './analytics.js';
// tracciaEvento è automaticamente uno spy — l'implementazione reale viene eseguita
// ma puoi verificare le chiamate
expect(tracciaEvento).toHaveBeenCalledWith('pagina_vista', { url: '/' });
```

### Snapshot Testing

Lo snapshot testing cattura l'output di una funzione o componente e lo confronta con una versione salvata in precedenza. È efficace per regressioni su output complessi (alberi DOM, oggetti di configurazione, risposte API).

```javascript
import { describe, it, expect } from 'vitest';

// Snapshot su file: salvato in __snapshots__/
describe('generaConfig', () => {
  it('produce la configurazione corretta per produzione', () => {
    const config = generaConfig('produzione');
    expect(config).toMatchSnapshot();
    // Prima esecuzione: crea lo snapshot
    // Esecuzioni successive: confronta con lo snapshot salvato
  });
});

// Inline snapshot: il valore viene scritto direttamente nel test
describe('formattaData', () => {
  it('formatta date in italiano', () => {
    const risultato = formattaData(new Date('2024-03-15'));
    expect(risultato).toMatchInlineSnapshot(`"15 marzo 2024"`);
  });
});

// Snapshot personalizzato con serializzatore
expect.addSnapshotSerializer({
  test(valore) { return valore instanceof ErroreApplicazione; },
  serialize(valore) {
    return `ErroreApplicazione { codice: "${valore.codice}", messaggio: "${valore.message}" }`;
  }
});
```

**Quando usare snapshot testing**: per output stabili e deterministic (configurazioni, HTML renderizzato, alberi di oggetti). **Quando evitarlo**: per valori che cambiano spesso (timestamp, ID casuali) — estraili o normalizzali prima dello snapshot.

### Testing di Codice Asincrono Complesso

```javascript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

describe('operazioni asincrone', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('debounce ritarda l\'esecuzione', async () => {
    const fn = vi.fn();
    const debouncedFn = debounce(fn, 300);

    debouncedFn('a');
    debouncedFn('b');
    debouncedFn('c');

    expect(fn).not.toHaveBeenCalled();

    await vi.advanceTimersByTimeAsync(300);

    expect(fn).toHaveBeenCalledOnce();
    expect(fn).toHaveBeenCalledWith('c'); // solo l'ultima chiamata
  });

  it('polling si ferma con AbortController', async () => {
    const controller = new AbortController();
    const mockFetch = vi.fn().mockResolvedValue({ stato: 'in_corso' });

    const promessaPolling = avviaPolling(mockFetch, 1000, controller.signal);

    await vi.advanceTimersByTimeAsync(3000);
    expect(mockFetch).toHaveBeenCalledTimes(3);

    controller.abort();
    await expect(promessaPolling).resolves.toEqual({ annullato: true });
  });
});

// Testing di async generator
describe('paginatore async', () => {
  it('itera su tutte le pagine', async () => {
    const risultati = [];
    for await (const pagina of paginatore('/api/dati', 10)) {
      risultati.push(...pagina);
      if (risultati.length >= 25) break;
    }
    expect(risultati.length).toBe(25);
  });
});
```

### Coverage e Metriche di Qualità

La copertura del codice misura quale percentuale del codice sorgente viene eseguita durante i test. V8 coverage provider (nativo nel runtime) e Istanbul (basato su strumentazione) sono le due opzioni principali in Vitest.

```bash
# Esegui test con report di copertura
npx vitest run --coverage

# Opzioni nel vitest.config.js — vedi configurazione sopra
```

Le quattro metriche principali sono: **Statements** (percentuale di istruzioni eseguite), **Branches** (percentuale di rami condizionali attraversati), **Functions** (percentuale di funzioni chiamate) e **Lines** (percentuale di righe eseguite). Un obiettivo realistico è l'80% su tutte le metriche, con attenzione particolare alla copertura dei branch — la metrica più significativa per la rilevazione di bug.

**V8 provider vs Istanbul**: il provider V8 utilizza la copertura nativa del runtime, con overhead quasi nullo e risultati accurati per il codice effettivamente eseguito. Istanbul strumenta il codice sorgente inserendo contatori prima dell'esecuzione, con maggior overhead ma supporto per trasformazioni di codice complesse. Per progetti TypeScript/ESM, V8 è generalmente preferibile.

### Testing Pattern: Arrange-Act-Assert nel Contesto Avanzato

Il pattern AAA (Arrange-Act-Assert) rimane fondamentale anche nel testing avanzato, ma la complessità di ciascuna fase aumenta con il codice sotto test.

```javascript
describe('CacheElastica', () => {
  it('restituisce undefined per elementi raccolti dal GC', async () => {
    // Arrange
    const cache = new CacheElastica();
    let oggettoGrande = { dati: new ArrayBuffer(10 * 1024 * 1024) };
    cache.set('chiave', oggettoGrande);

    // Act
    oggettoGrande = null; // rimuovi il riferimento forte
    // Nota: non è possibile forzare il GC in modo deterministico nei test
    // Questo test verifica il comportamento quando il valore è ancora presente
    const valore = cache.get('chiave');

    // Assert
    expect(valore).toBeDefined();
    expect(valore.dati).toBeInstanceOf(ArrayBuffer);
  });

  it('restituisce undefined per chiavi inesistenti', () => {
    // Arrange
    const cache = new CacheElastica();

    // Act
    const valore = cache.get('inesistente');

    // Assert
    expect(valore).toBeUndefined();
  });
});
```

### Vitest vs Jest: Criteri di Scelta

La scelta tra Vitest e Jest dipende dal contesto del progetto.

**Preferire Vitest quando**: il progetto usa già Vite come build tool, il codice è ESM-first, si desidera condividere la configurazione del bundler con quella dei test, oppure si lavora con framework moderni come SvelteKit, Nuxt 3 o Astro che integrano Vitest nativamente.

**Preferire Jest quando**: il progetto ha una suite di test Jest matura e funzionante, si lavora con React Native (dove l'integrazione Jest è più consolidata), oppure il team ha esperienza consolidata con l'ecosistema Jest (jest-dom, testing-library) e la migrazione non porterebbe benefici tangibili.

**Caratteristiche condivise**: entrambi supportano snapshot testing, mocking, watch mode, coverage reporting e integrazione con CI/CD. La sintassi dei test è quasi identica, rendendo una migrazione relativamente indolore quando necessaria.

---

## Esercizi

### Esercizio 1 — Prototipi, classi e ereditarieta

**Obiettivo:** Comprendere la catena prototipale di JavaScript e la sua relazione con la sintassi `class`.

- Implementare una gerarchia di classi per un sistema di forme geometriche:
  - Classe base `Forma` con proprietà `colore` e metodo `descriviti()` che restituisce una stringa descrittiva
  - Classe `Rettangolo extends Forma` con `larghezza` e `altezza`, metodi `area()` e `perimetro()`
  - Classe `Cerchio extends Forma` con `raggio`, metodi `area()` e `perimetro()`
  - Classe `Quadrato extends Rettangolo` che accetta solo un lato
- Reimplementare la stessa gerarchia usando solo prototipi (`Object.create`, `Function.prototype`) senza la keyword `class`
- Dimostrare con `Object.getPrototypeOf()` e `instanceof` che entrambe le implementazioni producono la stessa catena prototipale
- Aggiungere un campo privato `#id` (auto-incrementante) alla classe base e un getter pubblico
- Scrivere test che verificano il comportamento polimorfico: un array di forme miste deve poter chiamare `area()` su ogni elemento

### Esercizio 2 — Iterator, generator e async iteration

**Obiettivo:** Implementare pattern di iterazione personalizzati usando il protocollo iterator e i generatori.

- Creare una classe `Range` che implementa il protocollo iterable (`Symbol.iterator`) per generare numeri da `start` a `end` con `step` configurabile, usabile con `for...of` e spread
- Implementare un generatore `function* fibonacci()` che produce la sequenza di Fibonacci infinitamente, usabile con destructuring (`const [a, b, c] = fibonacci()`) e con un helper `take(n, iterable)` che estrae i primi N valori
- Creare un async generator `async function* paginatore(urlBase, pageSize)` che fetcha pagine di dati da un'API REST (`https://jsonplaceholder.typicode.com/posts?_page=N&_limit=M`) e le yield una alla volta
- Consumare il paginatore con `for await...of` e mostrare i risultati incrementalmente nel DOM
- Implementare un generatore `function* pipeline(...trasformazioni)` che applica una sequenza di funzioni di trasformazione a ogni valore in ingresso (compose lazy)

### Esercizio 3 — Event loop, microtask e scheduling

**Obiettivo:** Dimostrare una comprensione pratica dell'event loop e delle priorita di esecuzione.

- Scrivere un programma che produce il seguente output nell'ordine corretto, usando `console.log` con label:
  - Codice sincrono, `Promise.resolve().then()`, `queueMicrotask()`, `setTimeout(..., 0)`, `requestAnimationFrame()`, `MessageChannel` — predire l'ordine prima di eseguire
- Implementare una funzione `eseguiConYield(tasks)` che esegue un array di task CPU-intensive cedendo il controllo al browser ogni N millisecondi (usando `scheduler.yield()` dove disponibile, o fallback con `setTimeout(0)`) per evitare il blocco dell'interfaccia
- Creare una demo visiva: un contatore che si aggiorna nel DOM ogni 100ms con `setInterval`, mentre un bottone avvia un calcolo pesante (es. ordinamento di un array di 1M elementi) — dimostrare che senza `eseguiConYield` il contatore si blocca, con `eseguiConYield` continua
- Implementare una funzione `debounce(fn, delayMs)` e una `throttle(fn, intervalMs)` da zero (senza librerie), testando con eventi `input` e `scroll`

### Esercizio 4 — Proxy, Reflect e metaprogrammazione

**Obiettivo:** Utilizzare Proxy e Reflect per implementare pattern avanzati di metaprogrammazione.

- Creare un Proxy validatore che intercetta `set` su un oggetto e verifica i tipi a runtime: `{ nome: "string", eta: "number", email: "string" }` — il set deve rigettare con `TypeError` se il tipo non corrisponde
- Implementare un Proxy di logging che registra tutte le operazioni `get`, `set` e `deleteProperty` su un oggetto con timestamp, nome della proprieta e valore
- Creare un oggetto "osservabile" con Proxy che notifica i listener registrati quando una proprieta cambia (pattern Observer reattivo): `const obs = osservabile({ conteggio: 0 }); obs.subscribe('conteggio', (nuovo, vecchio) => ...)`
- Implementare una funzione `deepFreeze(obj)` che usa Proxy ricorsivo per rendere un oggetto profondamente immutabile, lanciando errore su qualsiasi tentativo di scrittura a qualsiasi livello di nesting
- Utilizzare `Reflect.ownKeys()`, `Reflect.get()` e `Reflect.set()` al posto degli equivalenti diretti nei trap del Proxy

### Esercizio 5 — Web Workers e comunicazione concorrente

**Obiettivo:** Implementare un sistema di calcolo concorrente usando Web Workers con comunicazione strutturata.

- Creare un Worker dedicato che riceve un array di numeri e calcola statistiche (media, mediana, deviazione standard, min, max) senza bloccare il main thread
- Implementare un pool di Worker (3 istanze) con una coda di task: il main thread invia task, il pool li distribuisce ai Worker disponibili e raccoglie i risultati in ordine
- Utilizzare `SharedArrayBuffer` e `Atomics` per implementare un contatore condiviso tra main thread e Worker, con incrementi atomici e `Atomics.wait`/`Atomics.notify` per la sincronizzazione
- Creare un Worker che processa immagini: riceve un `ImageData` via `postMessage` con transfer (non copia), applica un filtro (scala di grigi o blur) e restituisce il risultato
- Implementare una gestione errori robusta: timeout per Worker che non rispondono entro 5 secondi, `onerror` handler, terminazione pulita con `worker.terminate()`
- Misurare con `performance.now()` la differenza di tempo tra elaborazione sincrona e parallela con i Worker

### Esercizio 6 — Sistema di Moduli e Interoperabilità

**Obiettivo:** Comprendere in profondità il sistema di moduli JavaScript e le differenze tra ESM e CJS.

- Creare un pacchetto npm locale con dual export (ESM e CJS) usando il campo `exports` in `package.json`. Il pacchetto deve esporre una funzione `formattaData(date, locale)` e una costante `VERSION`
- Creare un progetto consumer ESM (`"type": "module"`) e uno CJS (senza `"type"`) che importano entrambi il pacchetto. Verificare che gli import funzionino correttamente in entrambi i contesti
- Implementare un sistema di plugin con dynamic `import()`: una classe `PluginManager` che carica plugin da una directory, ciascun plugin esporta un metodo `installa(app)` e un oggetto `metadata` con nome e versione
- Creare una pagina HTML con una import map che mappa bare specifier a CDN (es. `lodash-es` da `esm.sh`). Importare e usare le funzioni senza bundler
- Scrivere un modulo che importa JSON tramite import attributes (`with { type: 'json' }`) e verifica che il contenuto sia validato prima dell'uso
- Dimostrare la differenza tra live bindings ESM e copie CJS: esportare un contatore che si incrementa, importarlo da entrambi i sistemi e verificare che solo ESM rifletta gli aggiornamenti

### Esercizio 7 — Gestione Errori e Error.cause

**Obiettivo:** Implementare una strategia di gestione errori completa con catene di cause e gestori globali.

- Creare una gerarchia di errori personalizzati: `ErroreApplicazione` (base), `ErroreValidazione` (con campo e regola violata), `ErroreRete` (con status HTTP e body), `ErroreAutorizzazione` (con ruolo richiesto)
- Implementare una funzione `safeTry(fn)` che restituisce `[errore, risultato]` — testare con operazioni asincrone che possono fallire in modi diversi
- Costruire un middleware di gestione errori per un'applicazione Express-like che: logga la catena completa delle cause, restituisce risposte HTTP appropriate per ogni tipo di errore, e sanitizza i messaggi per non esporre dettagli interni al client
- Implementare un gestore globale `window.addEventListener('unhandledrejection', ...)` che cattura Promise non gestite e le invia a un servizio di telemetria (simulato con `console.table`)
- Creare una funzione `arricchisciErrore(errore, contesto)` che aggiunge metadati (timestamp, requestId, userId) a un errore usando `Error.cause` senza perdere lo stack trace originale
- Scrivere test che verificano la corretta propagazione delle cause attraverso 3+ livelli di astrazione

### Esercizio 8 — Testing Avanzato con Vitest

**Obiettivo:** Padroneggiare le tecniche di testing avanzato con Vitest, inclusi mocking ESM, snapshot testing e copertura.

- Configurare un progetto con Vitest e coverage V8. Impostare le soglie minime all'80% su tutte le metriche. Scrivere un modulo `calcolatrice.js` con operazioni base e raggiungere il 100% di copertura
- Implementare un modulo `servizio-utenti.js` che importa un modulo `api-client.js`. Scrivere test che mockano `api-client.js` con `vi.mock()`, verificando che il servizio gestisca correttamente risposte di successo, errori di rete e timeout
- Creare test con snapshot per una funzione `generaReport(dati)` che produce un oggetto complesso. Usare sia snapshot su file che inline snapshot. Verificare che aggiornamenti al formato del report vengano catturati come diff nello snapshot
- Testare codice asincrono con timer finti (`vi.useFakeTimers()`): una funzione `debounce` e una `retry` con backoff esponenziale. Usare `vi.advanceTimersByTimeAsync` per controllare il passaggio del tempo
- Implementare un mock parziale con `importOriginal()` per un modulo di utilità: mockare solo la funzione `fetch` interna lasciando invariate le altre esportazioni
- Scrivere test per un async generator che pagina risultati da un'API. Verificare che emetta tutti gli elementi e si fermi alla pagina vuota

---

## Letture e Riferimenti

### Documentazione ufficiale

- **MDN Web Docs — JavaScript** — Riferimento completo per sintassi avanzata, built-in objects e API del runtime. <https://developer.mozilla.org/en-US/docs/Web/JavaScript> (consultato: 2026-05-24)
- **ECMAScript Language Specification (ECMA-262)** — Specifica normativa del linguaggio, inclusi Proxy, Reflect, iteratori e generatori. <https://tc39.es/ecma262/> (consultato: 2026-05-24)
- **MDN Web Docs — Web Workers API** — Documentazione per Worker dedicati, SharedWorker e comunicazione tra thread. <https://developer.mozilla.org/en-US/docs/Web/API/Web_Workers_API> (consultato: 2026-05-24)
- **MDN Web Docs — Proxy** — Guida e riferimento per i Proxy handler e i trap disponibili. <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Proxy> (consultato: 2026-05-24)
- **MDN Web Docs — Iterators and Generators** — Documentazione del protocollo iterable/iterator e dei generatori. <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Iterators_and_generators> (consultato: 2026-05-24)
- **WHATWG HTML Living Standard — Web Workers** — Specifica normativa per i Web Workers. <https://html.spec.whatwg.org/multipage/workers.html> (consultato: 2026-05-24)
- **MDN Web Docs — AbortController** — Documentazione per AbortController, AbortSignal.any() e AbortSignal.timeout(). <https://developer.mozilla.org/en-US/docs/Web/API/AbortController> (consultato: 2026-05-24)
- **MDN Web Docs — Import Maps** — Guida all'uso delle import map per la risoluzione dei moduli nel browser. <https://developer.mozilla.org/en-US/docs/Web/HTML/Element/script/type/importmap> (consultato: 2026-05-24)
- **TC39 Proposal — Decorators** — Proposta Stage 3 per i decoratori JavaScript. <https://github.com/tc39/proposal-decorators> (consultato: 2026-05-24)
- **TC39 Proposal — Explicit Resource Management** — Proposta per `using`/`await using` e Symbol.dispose/Symbol.asyncDispose. <https://github.com/tc39/proposal-explicit-resource-management> (consultato: 2026-05-24)
- **Vitest Documentation** — Guida ufficiale al test runner ESM-first costruito su Vite. <https://vitest.dev/guide/> (consultato: 2026-05-24)
- **XState Documentation** — Documentazione per la libreria di macchine a stati e statechart. <https://stately.ai/docs/xstate> (consultato: 2026-05-24)
- **Node.js — ECMAScript Modules** — Documentazione ufficiale per i moduli ESM in Node.js, inclusa l'interoperabilità CJS. <https://nodejs.org/api/esm.html> (consultato: 2026-05-24)

### Libri e approfondimenti

- Flanagan D., *JavaScript: The Definitive Guide* (7th ed.), O'Reilly, 2020.
- Simpson K., *You Don't Know JS Yet: Scope & Closures* (2nd ed.), self-published, 2020.
- Rauschmayer A., *JavaScript for Impatient Programmers*, self-published, 2024.
- Rauschmayer A., *Exploring JavaScript* (ES2025 Edition), self-published, 2025.

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [04 — JavaScript Fondamenti](04-javascript-fondamenti.md) | Prerequisito diretto: questo modulo approfondisce concetti introdotti nei fondamenti |
| [06 — TypeScript](06-typescript.md) | TypeScript aggiunge tipizzazione statica ai pattern avanzati (generics per iterator, utility types per Proxy) |
| [10 — Node.js](10-nodejs.md) | Node.js espone Worker Threads con API analoga ai Web Workers del browser |
| [17 — Performance Web](17-performance-web.md) | Web Workers e scheduling ottimale prevengono il blocco del main thread e migliorano INP |
| [14 — Sicurezza Web](14-sicurezza-web.md) | SharedArrayBuffer richiede header COOP/COEP; Proxy puo implementare validazione input a runtime |
| [15 — Testing Web](15-testing-web.md) | I pattern avanzati (generatori, Proxy, Worker) richiedono strategie di test specifiche |

---

## Glossario

| Termine | Definizione |
|---|---|
| **Prototipo** | Oggetto da cui un altro oggetto eredita proprieta e metodi, accessibile tramite `Object.getPrototypeOf()` o la proprieta `__proto__`. |
| **Event loop** | Meccanismo che coordina l'esecuzione di codice sincrono, microtask e macrotask in un runtime JavaScript single-threaded. |
| **Microtask** | Task ad alta priorita (Promise callback, `queueMicrotask`) processata prima del prossimo rendering e prima di qualsiasi macrotask. |
| **Generator** | Funzione dichiarata con `function*` che puo sospendere la propria esecuzione con `yield` e riprenderla, restituendo un iteratore. |
| **Iterator protocol** | Contratto che richiede un metodo `next()` che restituisce `{ value, done }`, permettendo l'iterazione con `for...of`. |
| **Proxy** | Oggetto wrapper che intercetta le operazioni fondamentali (get, set, delete, ecc.) su un target tramite trap handler. |
| **Reflect** | Namespace che espone metodi corrispondenti ai trap dei Proxy, fornendo il comportamento predefinito delle operazioni su oggetti. |
| **Web Worker** | Thread separato dal main thread del browser che esegue JavaScript in background senza accesso al DOM. |
| **SharedArrayBuffer** | Buffer di memoria condiviso tra main thread e Worker, accessibile simultaneamente da piu thread. |
| **Atomics** | Namespace che fornisce operazioni atomiche (load, store, add, wait, notify) su `SharedArrayBuffer` per la sincronizzazione tra thread. |
| **WeakRef** | Riferimento debole a un oggetto che non impedisce la garbage collection dell'oggetto referenziato. |
| **FinalizationRegistry** | API che registra callback da invocare quando un oggetto viene raccolto dal garbage collector, utile per il cleanup di risorse. |
| **Transfer** | Meccanismo di `postMessage` che trasferisce la proprieta di un buffer al destinatario senza copiarlo, con costo O(1). |
| **Debounce** | Pattern che ritarda l'esecuzione di una funzione fino a quando non si verifica una pausa nell'invocazione di durata specificata. |
| **Throttle** | Pattern che limita la frequenza di esecuzione di una funzione a un massimo di una volta per intervallo di tempo specificato. |
| **AbortController** | API che genera un `AbortSignal` utilizzabile per annullare operazioni asincrone come fetch, event listener e timer. |
| **AbortSignal** | Oggetto che rappresenta un segnale di cancellazione. `AbortSignal.timeout()` e `AbortSignal.any()` permettono composizione e timeout. |
| **Import Map** | Blocco `<script type="importmap">` che mappa bare specifier a URL effettivi, permettendo l'uso di moduli ESM nel browser senza bundler. |
| **Import Attributes** | Sintassi `with { type: 'json' }` nelle dichiarazioni import che specifica il tipo atteso del modulo importato per sicurezza. |
| **Hidden Class** | Struttura interna (chiamata Map o Shape in V8) assegnata a oggetti con la stessa forma, che permette al motore JIT di ottimizzare l'accesso alle proprietà. |
| **Inline Caching** | Meccanismo del motore JIT che memorizza la posizione delle proprietà nella hidden class per evitare lookup ripetute. |
| **Megamorfico** | Stato di un sito di accesso a proprietà che incontra più di 4 hidden class diverse, causando l'abbandono dell'ottimizzazione JIT. |
| **Decorator** | Funzione che modifica classi, metodi, accessor o campi al momento della definizione. Proposta TC39 Stage 3, supportata da TypeScript e Babel. |
| **Error.cause** | Proprietà ES2022 del costruttore Error che permette di creare catene di errori preservando il contesto originale dell'eccezione. |
| **Concorrenza strutturata** | Paradigma che garantisce che le operazioni asincrone figlie non sopravvivano al loro scope genitore, tipicamente implementato con AbortController. |
| **Transducer** | Funzione di trasformazione componibile che opera indipendentemente dal meccanismo di riduzione, evitando la creazione di collezioni intermedie. |
| **Monade** | Pattern funzionale (Maybe, Either, IO) che incapsula un valore in un contesto e fornisce `map` e `flatMap` per la composizione di operazioni. |
| **Vitest** | Test runner ESM-first costruito su Vite, con supporto nativo per import.meta, top-level await e mocking di moduli ESM. |
| **Snapshot Testing** | Tecnica di testing che cattura l'output di una funzione e lo confronta con una versione salvata per rilevare regressioni. |
| **XState** | Libreria per macchine a stati e statechart che implementa il modello ad attori per la gestione deterministica della logica applicativa. |
| **Promise.withResolvers** | Metodo ES2024 che restituisce `{ promise, resolve, reject }`, permettendo di risolvere la Promise al di fuori del callback costruttore. |
