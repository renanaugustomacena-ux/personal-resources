---
corso: "Sviluppo Web"
fase: "2 — Linguaggi"
modulo: "04"
titolo: "JavaScript Fondamenti"
versione: "ES2024+"
livello: "Base-Intermedio"
prerequisiti:
  - "01 — HTML5"
  - "02 — CSS3"
obiettivi:
  - "Padroneggiare tipi, variabili, scope e hoisting"
  - "Utilizzare funzioni, closure e arrow function"
  - "Manipolare array e oggetti con metodi funzionali"
  - "Comprendere il DOM e gestire eventi"
  - "Gestire codice asincrono con Promise e async/await"
  - "Applicare destructuring, spread/rest e template literal"
tag: [JavaScript, ES2024, DOM, eventi, Promise, async-await, fondamenti]
---

# JavaScript Fondamenti — Guida Completa

> **Modulo 04** · **Aggiornamento:** 2026-05-24

> ### Obiettivi di apprendimento
>
> **Prerequisiti:** [HTML5](01-html5.md), [CSS3](02-css3.md)
>
> Al termine di questo modulo saprai:
> 1. Padroneggiare tipi, variabili, scope e hoisting
> 2. Utilizzare funzioni, closure e arrow function
> 3. Manipolare array e oggetti con metodi funzionali (map, filter, reduce)
> 4. Comprendere il DOM e gestire eventi
> 5. Gestire codice asincrono con Promise e async/await
> 6. Applicare destructuring, spread/rest e template literal
>
> **Tempo stimato:** 6-8 ore · **Livello:** Base-Intermedio

## Idee guida
1. **`const` default; `let` quando muta; mai `var`.**
2. **Strict equality `===` always.**
3. **Async/await > Promise chain.**
4. **Hoisting + closure: comprehended o bug nascoste.**


## Indice

1. [Panoramica](#panoramica)
2. [Variabili, Tipi e Scope](#variabili-tipi-e-scope)
3. [Funzioni e this](#funzioni-e-this)
4. [Oggetti e Prototipi](#oggetti-e-prototipi)
5. [DOM Manipulation e Eventi](#dom-manipulation-e-eventi)
6. [ES6+ Moderno e Moduli](#es6-moderno-e-moduli)
7. [Event Loop](#event-loop)
8. [Best Practices](#best-practices)
9. [ES2024/ES2025 — Nuove Funzionalità](#es20242025--nuove-funzionalità)
10. [Gestione degli Errori — Pattern Avanzati](#gestione-degli-errori--pattern-avanzati)
11. [Espressioni Regolari Avanzate](#espressioni-regolari-avanzate)
12. [Symbol e Well-Known Symbols](#symbol-e-well-known-symbols)
13. [Proxy e Reflect](#proxy-e-reflect)
14. [WeakRef e FinalizationRegistry](#weakref-e-finalizationregistry)
15. [Iteratori e Generatori Avanzati](#iteratori-e-generatori-avanzati)
16. [Structured Clone Algorithm](#structured-clone-algorithm)
17. [Web Workers e SharedArrayBuffer](#web-workers-e-sharedarraybuffer)
18. [Gestione della Memoria e Garbage Collection](#gestione-della-memoria-e-garbage-collection)
19. [Internals del Motore JavaScript (V8)](#internals-del-motore-javascript-v8)

---

## Panoramica

JavaScript è il linguaggio di programmazione più diffuso al mondo per lo sviluppo web. Nato nel 1995, creato da Brendan Eich in appena dieci giorni presso Netscape Communications, è stato inizialmente concepito come linguaggio di scripting leggero per rendere interattive le pagine web. Il nome originale era Mocha, poi rinominato LiveScript e infine JavaScript — una scelta di marketing legata alla popolarità di Java all'epoca, nonostante i due linguaggi abbiano ben poco in comune.

### Breve storia e standard ECMAScript

Nel 1997 JavaScript è stato standardizzato dall'organizzazione ECMA International sotto il nome **ECMAScript** (abbreviato ES). Le versioni più significative dello standard sono:

- **ES3 (1999):** la versione che ha consolidato il linguaggio nei browser per quasi un decennio.
- **ES5 (2009):** ha introdotto strict mode, metodi per gli array come `forEach`, `map`, `filter`, `reduce`, il supporto JSON nativo e i property descriptor.
- **ES6 / ES2015:** la rivoluzione più grande — `let` e `const`, arrow function, classi, template literal, destructuring, Promise, moduli nativi, Symbol, iteratori, generatori e molto altro.
- **ES2016–ES2025:** a partire dal 2016 lo standard segue un ciclo annuale di rilascio. Ogni anno vengono aggiunte funzionalità incrementali come `async`/`await` (ES2017), optional chaining e nullish coalescing (ES2020), top-level await (ES2022), `Array.prototype.toSorted` e `toReversed` (ES2023), `Object.groupBy` (ES2024).

### Ambienti di esecuzione

JavaScript non vive solo nel browser. Gli ambienti di esecuzione principali sono:

- **Browser:** il contesto storico, dove JavaScript interagisce con il DOM, la BOM (Browser Object Model) e le Web API (fetch, localStorage, geolocation, Canvas, Web Workers).
- **Node.js:** runtime lato server basato sul motore V8 di Chrome, rilasciato nel 2009 da Ryan Dahl. Consente di usare JavaScript per backend, CLI, scripting di sistema e molto altro.
- **Deno:** runtime moderno creato dallo stesso Ryan Dahl nel 2018, con supporto nativo a TypeScript, un sistema di permessi granulare e compatibilità con le Web API standard.
- **Bun:** runtime ad alte prestazioni rilasciato nel 2023, scritto in Zig, che punta su velocità estrema di avvio ed esecuzione.

JavaScript è un linguaggio **dinamico**, **debolmente tipizzato**, **multi-paradigma** (supporta programmazione imperativa, funzionale e orientata agli oggetti) e **single-threaded** con un modello di concorrenza basato sull'event loop.

---

## Variabili, Tipi e Scope

### Dichiarazione

In JavaScript esistono tre parole chiave per dichiarare variabili: `var`, `let` e `const`. Comprenderne le differenze è fondamentale.

**`var`** è la keyword originale. Ha scope di funzione (non di blocco), il che significa che una variabile dichiarata con `var` all'interno di un `if` o di un `for` è accessibile anche al di fuori di quel blocco. Inoltre, le dichiarazioni `var` sono soggette a **hoisting**: vengono "sollevate" all'inizio della funzione durante la fase di compilazione, ma il loro valore rimane `undefined` fino alla riga di assegnazione effettiva.

```javascript
console.log(nome); // undefined (hoisting, non errore)
var nome = "Mario";
console.log(nome); // "Mario"
```

**`let`** è stata introdotta con ES6 e ha scope di blocco. Anche `let` è soggetta a hoisting, ma la variabile non è accessibile prima della dichiarazione — si trova nella cosiddetta **Temporal Dead Zone (TDZ)**. Accedere a una variabile `let` prima della sua dichiarazione genera un `ReferenceError`.

```javascript
// console.log(eta); // ReferenceError: Cannot access 'eta' before initialization
let eta = 30;

if (true) {
  let messaggio = "ciao";
  console.log(messaggio); // "ciao"
}
// console.log(messaggio); // ReferenceError: messaggio is not defined
```

**`const`** funziona come `let` per quanto riguarda scope e TDZ, ma richiede un'inizializzazione obbligatoria al momento della dichiarazione e non permette la riassegnazione del binding. Attenzione: `const` non rende immutabile il valore — se il valore è un oggetto o un array, le sue proprietà possono comunque essere modificate.

```javascript
const PI = 3.14159;
// PI = 3; // TypeError: Assignment to constant variable

const utente = { nome: "Luca" };
utente.nome = "Marco"; // Perfettamente valido
// utente = {}; // TypeError: Assignment to constant variable
```

**Quando usare ciascuno:** la regola moderna è semplice — usa `const` per default, passa a `let` solo quando sai che il valore dovrà essere riassegnato. Evita `var` nel codice moderno.

### Tipi Primitivi

JavaScript ha sette tipi primitivi e un tipo strutturale (Object).

**string:** sequenze di caratteri Unicode racchiuse tra apici singoli, doppi o backtick (template literal). Le stringhe sono immutabili.

```javascript
const saluto = "Buongiorno";
const nome = 'Renan';
const frase = `${saluto}, ${nome}!`; // "Buongiorno, Renan!"
```

**number:** JavaScript usa un unico tipo numerico a virgola mobile a 64 bit (IEEE 754 double precision). Questo significa che sia gli interi sia i decimali sono rappresentati dallo stesso tipo. Valori speciali includono `Infinity`, `-Infinity` e `NaN` (Not a Number).

```javascript
console.log(0.1 + 0.2 === 0.3); // false (classico problema floating point)
console.log(Number.isNaN(NaN));  // true
console.log(Number.isFinite(Infinity)); // false
```

**bigint:** introdotto in ES2020, consente di rappresentare numeri interi di grandezza arbitraria. Si crea aggiungendo `n` alla fine del numero.

```javascript
const grande = 9007199254740993n;
console.log(typeof grande); // "bigint"
```

**boolean:** due soli valori, `true` e `false`.

**null:** rappresenta l'assenza intenzionale di un valore. È un valore assegnato esplicitamente dal programmatore.

**undefined:** indica che una variabile è stata dichiarata ma non inizializzata, o che una funzione non restituisce un valore esplicito.

**symbol:** valore unico e immutabile, introdotto in ES6. Usato principalmente come chiave di proprietà per evitare collisioni di nomi.

```javascript
const id = Symbol("id");
const obj = { [id]: 42 };
console.log(obj[id]); // 42
```

**L'operatore `typeof`** restituisce una stringa che indica il tipo dell'operando:

```javascript
typeof "ciao"     // "string"
typeof 42         // "number"
typeof true       // "boolean"
typeof undefined  // "undefined"
typeof null       // "object"  (bug storico, mai corretto)
typeof Symbol()   // "symbol"
typeof 10n        // "bigint"
typeof {}         // "object"
typeof []         // "object"  (usare Array.isArray() per verificare)
typeof function(){} // "function"
```

**Type coercion — `==` vs `===`:** l'operatore `==` (uguaglianza astratta) esegue conversione di tipo implicita prima del confronto, mentre `===` (uguaglianza stretta) confronta senza conversione. Le regole di coercion implicita sono complesse e fonte di bug.

```javascript
0 == ""        // true (entrambi convertiti a 0)
0 == "0"       // true
"" == "0"      // false
null == undefined // true (caso speciale)
null === undefined // false
false == "0"   // true
false == ""    // true
```

Regola d'oro: **usa sempre `===` e `!==`**, tranne in rari casi dove `== null` è intenzionale per controllare sia `null` che `undefined`.

**Valori truthy e falsy:** in contesto booleano, i seguenti valori sono **falsy**: `false`, `0`, `-0`, `0n`, `""` (stringa vuota), `null`, `undefined`, `NaN`. Tutto il resto è **truthy**, inclusi `[]` (array vuoto), `{}` (oggetto vuoto) e `"0"` (stringa con zero).

### Scope

**Global scope:** le variabili dichiarate al di fuori di qualsiasi funzione o blocco sono globali. Nel browser, le variabili globali dichiarate con `var` diventano proprietà dell'oggetto `window`.

**Function scope:** le variabili dichiarate con `var` dentro una funzione sono accessibili ovunque all'interno di quella funzione, ma non all'esterno.

**Block scope:** le variabili dichiarate con `let` e `const` sono confinate al blocco `{}` in cui sono definite — un `if`, un `for`, un semplice blocco di codice.

**Lexical scope (scope lessicale):** JavaScript determina lo scope delle variabili in base alla posizione nel codice sorgente, non in base a dove vengono chiamate le funzioni. Una funzione interna ha accesso alle variabili della funzione esterna in cui è stata definita.

**Closure:** una closure si crea quando una funzione interna mantiene un riferimento alle variabili dello scope della funzione esterna, anche dopo che quest'ultima ha terminato la sua esecuzione. Le closure sono uno dei concetti più potenti di JavaScript.

```javascript
function creaContatore() {
  let conteggio = 0;
  return {
    incrementa() { return ++conteggio; },
    decrementa() { return --conteggio; },
    valore() { return conteggio; }
  };
}

const contatore = creaContatore();
console.log(contatore.incrementa()); // 1
console.log(contatore.incrementa()); // 2
console.log(contatore.decrementa()); // 1
// conteggio non è accessibile direttamente dall'esterno
```

Esempio pratico — generatore di ID univoci:

```javascript
function generatoreId(prefisso = "id") {
  let sequenza = 0;
  return function () {
    sequenza++;
    return `${prefisso}_${sequenza}`;
  };
}

const nuovoId = generatoreId("utente");
console.log(nuovoId()); // "utente_1"
console.log(nuovoId()); // "utente_2"
```

**IIFE (Immediately Invoked Function Expression):** un pattern classico (meno comune nel codice moderno con i moduli) che crea uno scope isolato eseguendo immediatamente una funzione anonima.

```javascript
const modulo = (function () {
  const privato = "non accessibile fuori";
  return {
    pubblico: "accessibile",
    leggiPrivato() { return privato; }
  };
})();

console.log(modulo.pubblico);        // "accessibile"
console.log(modulo.leggiPrivato());   // "non accessibile fuori"
```

### Closure e Scope Chain — Approfondimento

Per comprendere a fondo le closure è necessario capire come JavaScript risolve le variabili attraverso la **scope chain** (catena degli scope).

**Come funziona la scope chain:** quando una funzione viene creata, il motore JavaScript salva un riferimento all'**ambiente lessicale** (Lexical Environment) corrente nel record interno `[[Environment]]` della funzione. Questo ambiente contiene le variabili locali e un puntatore all'ambiente lessicale esterno (outer). Quando il codice accede a una variabile, il motore la cerca prima nell'ambiente locale; se non la trova, risale al `[[Environment]]` esterno, poi all'esterno di quello, fino all'ambiente globale. Se la variabile non esiste neanche lì, viene lanciato un `ReferenceError`.

```javascript
const globale = "G";

function esterna() {
  const varEsterna = "E";

  function intermedia() {
    const varIntermedia = "I";

    function interna() {
      const varInterna = "L";
      // Scope chain di interna():
      // 1. Locale: { varInterna: "L" }
      // 2. intermedia: { varIntermedia: "I" }
      // 3. esterna: { varEsterna: "E" }
      // 4. Globale: { globale: "G" }
      console.log(varInterna, varIntermedia, varEsterna, globale);
    }
    interna();
  }
  intermedia();
}
esterna(); // "L" "I" "E" "G"
```

**Closure e loop — il problema classico con `var`:** una delle trappole più insidiose di JavaScript riguarda le closure create dentro un loop con `var`. Poiché `var` ha scope di funzione (non di blocco), tutte le closure condividono la stessa variabile.

```javascript
// PROBLEMA: tutte le callback vedono lo stesso valore di i
for (var i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 100);
}
// Output: 3, 3, 3 (non 0, 1, 2!)
// Al momento dell'esecuzione delle callback, il loop è terminato e i === 3

// SOLUZIONE 1: let (scope di blocco — ogni iterazione ha il proprio i)
for (let i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 100);
}
// Output: 0, 1, 2

// SOLUZIONE 2: IIFE (pre-ES6, cattura il valore corrente)
for (var i = 0; i < 3; i++) {
  (function (j) {
    setTimeout(() => console.log(j), 100);
  })(i);
}
// Output: 0, 1, 2
```

**Closure e gestione della memoria:** le closure mantengono in vita le variabili catturate. In applicazioni complesse, closure che catturano oggetti grandi possono causare memory leak se non vengono rilasciate.

```javascript
// Potenziale memory leak: la closure cattura l'intero scope
function creaProcessore() {
  const datiPesanti = new ArrayBuffer(50 * 1024 * 1024); // 50 MB
  const id = "proc-001";

  // Questa closure cattura sia 'id' sia 'datiPesanti'
  // anche se usa solo 'id'
  return function () {
    console.log(`Processore: ${id}`);
  };
}

// Soluzione: ristrutturare per catturare solo il necessario
function creaProcessoreSicuro() {
  const datiPesanti = new ArrayBuffer(50 * 1024 * 1024);
  const id = "proc-001";
  elabora(datiPesanti); // usa i dati pesanti qui

  // Questa closure cattura solo 'id' — datiPesanti può essere raccolto dal GC
  return function () {
    console.log(`Processore: ${id}`);
  };
}
```

**Pattern avanzati con closure:** le closure sono alla base di molti pattern fondamentali — moduli, currying, partial application e memoizzazione.

```javascript
// Currying con closure
function curry(fn) {
  return function curried(...args) {
    if (args.length >= fn.length) {
      return fn.apply(this, args);
    }
    return function (...args2) {
      return curried.apply(this, args.concat(args2));
    };
  };
}

const somma = curry((a, b, c) => a + b + c);
somma(1)(2)(3);    // 6
somma(1, 2)(3);    // 6
somma(1)(2, 3);    // 6
```

### Strutture Dati

#### Array

Gli array in JavaScript sono oggetti ordinati e indicizzati. I metodi più importanti si dividono in **mutanti** (modificano l'array originale) e **non-mutanti** (restituiscono un nuovo array).

```javascript
const numeri = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

// map — trasforma ogni elemento, restituisce nuovo array
const doppi = numeri.map(n => n * 2); // [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]

// filter — filtra elementi in base a una condizione
const pari = numeri.filter(n => n % 2 === 0); // [2, 4, 6, 8, 10]

// reduce — riduce l'array a un singolo valore
const somma = numeri.reduce((acc, n) => acc + n, 0); // 55

// find / findIndex — trova il primo elemento (o indice) che soddisfa la condizione
const primoMaggiore = numeri.find(n => n > 5);      // 6
const indice = numeri.findIndex(n => n > 5);          // 5

// some / every — verificano se almeno uno / tutti soddisfano la condizione
numeri.some(n => n > 9);  // true
numeri.every(n => n > 0); // true

// flat / flatMap — appiattisce array annidati
[[1, 2], [3, 4]].flat();                  // [1, 2, 3, 4]
[1, 2, 3].flatMap(n => [n, n * 10]);      // [1, 10, 2, 20, 3, 30]

// includes — verifica la presenza di un elemento
numeri.includes(5); // true

// forEach — itera senza restituire nulla (effetti collaterali)
numeri.forEach(n => console.log(n));

// sort — ordina l'array IN PLACE (mutante!)
const nomi = ["Carlo", "Anna", "Bruno"];
nomi.sort(); // ["Anna", "Bruno", "Carlo"]

// Per ordinamento numerico serve una funzione di confronto
[10, 1, 21, 2].sort((a, b) => a - b); // [1, 2, 10, 21]

// splice — rimuove/inserisce elementi IN PLACE (mutante)
const lettere = ["a", "b", "c", "d"];
lettere.splice(1, 2, "x", "y"); // lettere diventa ["a", "x", "y", "d"]

// slice — estrae una porzione senza mutare l'originale
const originale = [1, 2, 3, 4, 5];
const porzione = originale.slice(1, 3); // [2, 3]

// at — accesso per indice, supporta indici negativi
const arr = [10, 20, 30, 40];
arr.at(-1); // 40
arr.at(0);  // 10

// toSorted / toReversed (ES2023) — versioni non-mutanti di sort e reverse
const disordinato = [3, 1, 2];
const ordinato = disordinato.toSorted((a, b) => a - b); // [1, 2, 3]
// disordinato resta [3, 1, 2]

const inverso = [1, 2, 3].toReversed(); // [3, 2, 1]
```

#### Object

```javascript
// Creazione
const persona = { nome: "Giulia", eta: 28, citta: "Roma" };

// Accesso alle proprietà
persona.nome;       // "Giulia"
persona["eta"];     // 28

// Destructuring
const { nome, eta, citta } = persona;

// Spread — copia superficiale e merge
const aggiornato = { ...persona, eta: 29 };

// Metodi statici utili
Object.keys(persona);    // ["nome", "eta", "citta"]
Object.values(persona);  // ["Giulia", 28, "Roma"]
Object.entries(persona);  // [["nome","Giulia"], ["eta",28], ["citta","Roma"]]

const copia = Object.assign({}, persona, { professione: "ingegnere" });

// Object.freeze — rende l'oggetto immutabile (shallow)
const config = Object.freeze({ apiUrl: "https://api.esempio.it", timeout: 5000 });
// config.apiUrl = "altro"; // silenziosamente ignorato (errore in strict mode)
```

#### Map e Set

**Map** è una collezione di coppie chiave-valore dove le chiavi possono essere di qualsiasi tipo (a differenza degli oggetti, dove le chiavi sono sempre stringhe o Symbol).

```javascript
const mappa = new Map();
mappa.set("nome", "Renan");
mappa.set(42, "risposta");
mappa.set(true, "attivo");

mappa.get("nome"); // "Renan"
mappa.has(42);     // true
mappa.size;        // 3
mappa.delete(true);

for (const [chiave, valore] of mappa) {
  console.log(`${chiave}: ${valore}`);
}
```

**Set** è una collezione di valori unici, senza duplicati.

```javascript
const insieme = new Set([1, 2, 3, 3, 4, 4, 5]);
console.log(insieme.size); // 5
insieme.add(6);
insieme.has(3);   // true
insieme.delete(1);

// Rimuovere duplicati da un array
const conDuplicati = [1, 1, 2, 3, 3];
const unici = [...new Set(conDuplicati)]; // [1, 2, 3]
```

#### WeakMap e WeakSet

**WeakMap** e **WeakSet** funzionano in modo simile a Map e Set, ma le loro chiavi (WeakMap) o valori (WeakSet) devono essere oggetti e sono riferimenti deboli. Se non esistono altri riferimenti all'oggetto, il garbage collector può liberare la memoria. Non sono iterabili e non hanno la proprietà `size`. Sono utili per associare metadati a oggetti senza impedirne la garbage collection.

```javascript
const metadati = new WeakMap();
let elemento = { id: 1 };
metadati.set(elemento, { cliccato: true });
elemento = null; // il garbage collector può liberare sia l'oggetto sia i metadati
```

---

## Funzioni e this

### Funzioni

JavaScript offre diversi modi per definire funzioni, ciascuno con comportamenti specifici.

**Function declaration** — soggetta a hoisting completo (può essere chiamata prima della sua definizione nel codice). Ha un proprio `this` e un oggetto `arguments`.

```javascript
function saluta(nome) {
  return `Ciao, ${nome}!`;
}
```

**Function expression** — assegnata a una variabile, non è soggetta a hoisting (la variabile esiste ma è `undefined` o nella TDZ).

```javascript
const saluta = function (nome) {
  return `Ciao, ${nome}!`;
};
```

**Arrow function (ES6)** — sintassi compatta, non ha un proprio `this` (eredita quello lessicale), non ha l'oggetto `arguments` e non può essere usata come constructor.

```javascript
const saluta = (nome) => `Ciao, ${nome}!`;
const somma = (a, b) => a + b;
const processa = (dati) => {
  const risultato = dati.map(d => d * 2);
  return risultato;
};
```

**Parametri di default** — consentono di definire valori predefiniti per i parametri.

```javascript
function creaUtente(nome, ruolo = "lettore", attivo = true) {
  return { nome, ruolo, attivo };
}
creaUtente("Luca"); // { nome: "Luca", ruolo: "lettore", attivo: true }
```

**Rest parameters (`...args`)** — raccolgono un numero variabile di argomenti in un array.

```javascript
function sommaArgomenti(...numeri) {
  return numeri.reduce((acc, n) => acc + n, 0);
}
sommaArgomenti(1, 2, 3, 4); // 10
```

**Spread operator** — espande un iterabile nei singoli elementi.

```javascript
const numeri = [3, 7, 1, 9];
Math.max(...numeri); // 9

const unito = [...[1, 2], ...[3, 4]]; // [1, 2, 3, 4]
```

**Destructuring nei parametri** — estrae direttamente le proprietà dagli argomenti.

```javascript
function mostraUtente({ nome, eta, citta = "Sconosciuta" }) {
  console.log(`${nome}, ${eta} anni, vive a ${citta}`);
}
mostraUtente({ nome: "Giulia", eta: 28 });
// "Giulia, 28 anni, vive a Sconosciuta"
```

### this Binding

Il valore di `this` in JavaScript dipende da **come** la funzione viene chiamata, non da dove viene definita (con l'eccezione delle arrow function).

**Contesto globale:** al di fuori di qualsiasi funzione, `this` si riferisce all'oggetto globale (`window` nel browser, `globalThis` in modo universale). In strict mode, `this` è `undefined` nelle funzioni regolari chiamate senza contesto.

```javascript
console.log(this === window); // true (nel browser, al livello globale)

function mostraThis() {
  "use strict";
  console.log(this); // undefined
}
mostraThis();
```

**Metodo di un oggetto:** quando una funzione è chiamata come metodo di un oggetto, `this` si riferisce a quell'oggetto.

```javascript
const utente = {
  nome: "Marco",
  saluta() {
    console.log(`Ciao, sono ${this.nome}`);
  }
};
utente.saluta(); // "Ciao, sono Marco"
```

**Constructor (`new`):** quando una funzione è chiamata con `new`, `this` si riferisce al nuovo oggetto creato.

```javascript
function Persona(nome) {
  this.nome = nome;
}
const p = new Persona("Anna"); // this si riferisce al nuovo oggetto
console.log(p.nome); // "Anna"
```

**Binding esplicito — `call`, `apply`, `bind`:**

```javascript
function presenta(saluto, punteggiatura) {
  console.log(`${saluto}, sono ${this.nome}${punteggiatura}`);
}
const obj = { nome: "Luca" };

presenta.call(obj, "Ciao", "!");    // "Ciao, sono Luca!"
presenta.apply(obj, ["Ciao", "!"]); // "Ciao, sono Luca!"

const presentaLuca = presenta.bind(obj, "Ciao");
presentaLuca("!"); // "Ciao, sono Luca!"
```

**Arrow function — `this` lessicale:** le arrow function non hanno un proprio `this`. Ereditano il `this` dallo scope circostante al momento della definizione.

```javascript
const squadra = {
  nome: "Alpha",
  membri: ["Ada", "Bob", "Cara"],
  elenca() {
    // Arrow function eredita this da elenca()
    this.membri.forEach(m => {
      console.log(`${m} appartiene a ${this.nome}`);
    });
  }
};
squadra.elenca();
// "Ada appartiene a Alpha"
// "Bob appartiene a Alpha"
// "Cara appartiene a Alpha"
```

**Errore comune:** estrarre un metodo da un oggetto perde il binding.

```javascript
const utente = {
  nome: "Sara",
  saluta() { console.log(`Ciao, ${this.nome}`); }
};
const fn = utente.saluta;
fn(); // "Ciao, undefined" (this è globale o undefined in strict mode)

// Soluzioni
const fnBound = utente.saluta.bind(utente);
fnBound(); // "Ciao, Sara"
```

---

## Oggetti e Prototipi

### Oggetti

**Pattern di creazione degli oggetti:**

```javascript
// Literal
const auto = { marca: "Fiat", modello: "Panda" };

// Object.create — crea un oggetto con un prototipo specifico
const animale = { tipo: "mammifero", respira() { return true; } };
const cane = Object.create(animale);
cane.razza = "Labrador";
cane.respira(); // true (ereditato dal prototipo)

// Factory function
function creaPersona(nome, eta) {
  return {
    nome,
    eta,
    saluta() { return `Sono ${this.nome}`; }
  };
}
```

**Property descriptor:** ogni proprietà di un oggetto ha attributi nascosti che ne controllano il comportamento.

```javascript
const obj = {};
Object.defineProperty(obj, "nome", {
  value: "immutabile",
  writable: false,     // non può essere riassegnato
  enumerable: true,    // appare nei cicli for...in e Object.keys
  configurable: false  // non può essere cancellato o riconfigurato
});
obj.nome = "altro"; // silenziosamente ignorato (errore in strict mode)

const descrittore = Object.getOwnPropertyDescriptor(obj, "nome");
// { value: "immutabile", writable: false, enumerable: true, configurable: false }
```

**Getter e setter:**

```javascript
const temperatura = {
  _celsius: 0,
  get fahrenheit() {
    return this._celsius * 9 / 5 + 32;
  },
  set fahrenheit(f) {
    this._celsius = (f - 32) * 5 / 9;
  }
};
temperatura.fahrenheit = 212;
console.log(temperatura._celsius); // 100
```

**Computed property names:**

```javascript
const campo = "email";
const utente = {
  nome: "Renan",
  [campo]: "renan@esempio.it",
  [`get${campo.charAt(0).toUpperCase() + campo.slice(1)}`]() {
    return this[campo];
  }
};
console.log(utente.getEmail()); // "renan@esempio.it"
```

### Prototipi

JavaScript usa un modello di ereditarietà **prototipale**: ogni oggetto ha un riferimento interno a un altro oggetto chiamato il suo prototipo. Quando si accede a una proprietà che non esiste sull'oggetto, JavaScript risale la **catena dei prototipi** fino a trovarla o fino a raggiungere `null`.

```javascript
const animale = {
  vivo: true,
  mangia() { return "Sto mangiando"; }
};

const gatto = Object.create(animale);
gatto.miagola = function () { return "Miao!"; };

console.log(gatto.vivo);     // true (dal prototipo)
console.log(gatto.mangia()); // "Sto mangiando" (dal prototipo)
console.log(gatto.miagola()); // "Miao!" (proprietà propria)
```

**`__proto__` vs `prototype`:** `__proto__` è il riferimento interno al prototipo di un'istanza. `prototype` è una proprietà delle funzioni constructor e contiene l'oggetto che diventerà il `__proto__` delle istanze create con `new`.

```javascript
function Veicolo(tipo) {
  this.tipo = tipo;
}
Veicolo.prototype.descrivi = function () {
  return `Sono un ${this.tipo}`;
};

const moto = new Veicolo("motociclo");
console.log(moto.descrivi());             // "Sono un motociclo"
console.log(moto.__proto__ === Veicolo.prototype); // true
```

### Classi (ES6+)

Le classi ES6 sono **zucchero sintattico** sopra il sistema prototipale. Sotto il cofano funzionano esattamente con i prototipi, ma offrono una sintassi più chiara e familiare.

```javascript
class Animale {
  // Proprietà privata (ES2022)
  #nome;

  // Proprietà statica
  static conteggio = 0;

  constructor(nome, verso) {
    this.#nome = nome;
    this.verso = verso;
    Animale.conteggio++;
  }

  // Getter
  get nome() {
    return this.#nome;
  }

  // Metodo di istanza
  parla() {
    return `${this.#nome} fa ${this.verso}`;
  }

  // Metodo statico
  static totale() {
    return `Ci sono ${Animale.conteggio} animali`;
  }
}

class Cane extends Animale {
  #razza;

  constructor(nome, razza) {
    super(nome, "Bau"); // chiama il constructor della classe padre
    this.#razza = razza;
  }

  // Override del metodo
  parla() {
    return `${super.parla()}! Sono un ${this.#razza}`;
  }
}

const rex = new Cane("Rex", "Pastore Tedesco");
console.log(rex.parla());     // "Rex fa Bau! Sono un Pastore Tedesco"
console.log(rex.nome);        // "Rex" (attraverso il getter)
console.log(Cane.totale());   // "Ci sono 1 animali" (ereditato dalla classe padre)
```

**Pattern Mixin:** JavaScript non supporta l'ereditarietà multipla, ma i mixin offrono una soluzione elegante per comporre comportamenti.

```javascript
const Serializzabile = (Base) => class extends Base {
  toJSON() {
    return JSON.stringify(this);
  }
  static fromJSON(json) {
    return Object.assign(new this(), JSON.parse(json));
  }
};

const Validabile = (Base) => class extends Base {
  valida() {
    for (const [chiave, valore] of Object.entries(this)) {
      if (valore === null || valore === undefined) {
        throw new Error(`Campo ${chiave} non valido`);
      }
    }
    return true;
  }
};

class Prodotto extends Serializzabile(Validabile(class {})) {
  constructor(nome, prezzo) {
    super();
    this.nome = nome;
    this.prezzo = prezzo;
  }
}

const p = new Prodotto("Laptop", 999);
p.valida();       // true
p.toJSON();       // '{"nome":"Laptop","prezzo":999}'
```

### Catena dei Prototipi — Internals

Per comprendere a fondo il sistema prototipale è utile esaminare come il motore JavaScript risolve le proprietà e come si struttura la catena.

**Ogni oggetto ha uno slot interno `[[Prototype]]`** che punta al suo prototipo. Questo slot è accessibile (in modo non standard) tramite `__proto__` o con i metodi standard `Object.getPrototypeOf()` e `Object.setPrototypeOf()`. La catena termina quando `[[Prototype]]` è `null`.

```javascript
// La catena completa di un array
const arr = [1, 2, 3];

// arr → Array.prototype → Object.prototype → null
Object.getPrototypeOf(arr) === Array.prototype;           // true
Object.getPrototypeOf(Array.prototype) === Object.prototype; // true
Object.getPrototypeOf(Object.prototype) === null;            // true

// Quando si chiama arr.toString():
// 1. Cerca toString in arr → non trovato
// 2. Cerca toString in Array.prototype → trovato! (Array.prototype.toString)
// Quando si chiama arr.hasOwnProperty("length"):
// 1. Cerca in arr → no
// 2. Cerca in Array.prototype → no
// 3. Cerca in Object.prototype → trovato! (Object.prototype.hasOwnProperty)
```

**Property shadowing:** quando un oggetto e il suo prototipo hanno una proprietà con lo stesso nome, la proprietà dell'oggetto "nasconde" quella del prototipo.

```javascript
const base = { tipo: "base", saluta() { return `Sono ${this.tipo}`; } };
const derivato = Object.create(base);
derivato.tipo = "derivato"; // shadowing: nasconde base.tipo

derivato.saluta(); // "Sono derivato" — this si riferisce a derivato
base.saluta();     // "Sono base"

// hasOwnProperty verifica se la proprietà è propria (non ereditata)
derivato.hasOwnProperty("tipo");   // true — proprietà propria
derivato.hasOwnProperty("saluta"); // false — ereditata dal prototipo
```

**Performance della catena prototipale:** la ricerca di proprietà risale tutta la catena fino a trovare la proprietà o raggiungere `null`. Catene profonde rallentano l'accesso alle proprietà. In pratica, i motori moderni mitigano questo con le Hidden Classes e le Inline Caches (vedi sezione V8), ma è comunque buona pratica mantenere catene poco profonde (2-3 livelli massimo).

**`Object.create(null)` — oggetti senza prototipo:** creare oggetti con prototipo `null` elimina tutti i metodi ereditati da `Object.prototype` (`toString`, `hasOwnProperty`, `constructor`). Questo pattern è usato per creare dizionari puri, sicuri da prototype pollution.

```javascript
const dizionario = Object.create(null);
dizionario.chiave = "valore";
dizionario.toString; // undefined — nessun metodo ereditato
// Sicuro da prototype pollution: nessun rischio che chiavi come
// "__proto__", "constructor", "toString" confliggano con metodi ereditati

// Confronto con un oggetto normale
const normale = {};
normale.toString; // function toString() { ... } — ereditato da Object.prototype
```

**Relazione tra classi ES6 e prototipi:** le classi sono zucchero sintattico, ma il meccanismo è identico.

```javascript
class Animale {
  constructor(nome) { this.nome = nome; }
  parla() { return `${this.nome} parla`; }
}

class Cane extends Animale {
  abbaia() { return `${this.nome} abbaia`; }
}

// Equivale esattamente a:
// Cane.prototype.__proto__ === Animale.prototype
Object.getPrototypeOf(Cane.prototype) === Animale.prototype; // true
// Cane.__proto__ === Animale (per l'ereditarietà dei metodi statici)
Object.getPrototypeOf(Cane) === Animale; // true

const rex = new Cane("Rex");
// rex → Cane.prototype → Animale.prototype → Object.prototype → null
```

---

## DOM Manipulation e Eventi

### Selezione del DOM

Il DOM (Document Object Model) è la rappresentazione ad albero del documento HTML. JavaScript può leggere, modificare, aggiungere e rimuovere nodi dal DOM.

```javascript
// Selezione singola — restituisce il primo elemento trovato
const titolo = document.getElementById("titolo-principale");
const primo = document.querySelector(".card"); // selettore CSS
const bottone = document.querySelector("button[data-azione='salva']");

// Selezione multipla — restituisce una NodeList o HTMLCollection
const tutteLeCard = document.querySelectorAll(".card"); // NodeList (statica)
const classi = document.getElementsByClassName("attivo"); // HTMLCollection (live)
const paragrafi = document.getElementsByTagName("p"); // HTMLCollection (live)

// querySelectorAll restituisce una NodeList statica — iterabile con forEach
tutteLeCard.forEach(card => console.log(card.textContent));

// getElementsByClassName restituisce una HTMLCollection live — non ha forEach
// Convertire in array: [...classi] oppure Array.from(classi)
```

### Modifica del DOM

```javascript
// Creare elementi
const nuovoDiv = document.createElement("div");
nuovoDiv.textContent = "Contenuto sicuro"; // solo testo, nessun rischio XSS
nuovoDiv.classList.add("card", "evidenziata");
nuovoDiv.setAttribute("data-id", "42");
nuovoDiv.dataset.categoria = "principale"; // equivale a data-categoria="principale"

// innerHTML — ATTENZIONE: rischio XSS se si inseriscono dati non sanitizzati
// MAI usare innerHTML con input dell'utente senza sanitizzazione
const contenitore = document.getElementById("contenitore");
contenitore.innerHTML = "<p>Contenuto HTML statico</p>"; // OK per HTML statico

// Inserimento nel DOM
contenitore.appendChild(nuovoDiv);

// insertBefore — inserisce prima di un nodo di riferimento
const riferimento = contenitore.firstChild;
contenitore.insertBefore(nuovoDiv, riferimento);

// Metodi moderni
contenitore.append(nuovoDiv, "testo");   // accetta più nodi e stringhe
contenitore.prepend(nuovoDiv);           // inserisce all'inizio
contenitore.before(nuovoDiv);            // inserisce prima del contenitore stesso
contenitore.after(nuovoDiv);             // inserisce dopo il contenitore stesso

// Rimozione
contenitore.removeChild(nuovoDiv); // classico
nuovoDiv.remove();                 // moderno

// classList — gestione delle classi CSS
nuovoDiv.classList.add("visibile");
nuovoDiv.classList.remove("nascosto");
nuovoDiv.classList.toggle("attivo");     // aggiunge se assente, rimuove se presente
nuovoDiv.classList.contains("visibile"); // true
```

**DocumentFragment per operazioni batch:** quando si devono inserire molti elementi, è più efficiente usare un DocumentFragment per evitare reflow multipli del layout.

```javascript
const frammento = document.createDocumentFragment();
const dati = ["Elemento 1", "Elemento 2", "Elemento 3", "Elemento 4"];

dati.forEach(testo => {
  const li = document.createElement("li");
  li.textContent = testo;
  frammento.appendChild(li);
});

// Un solo reflow quando il frammento viene inserito nel DOM
document.getElementById("lista").appendChild(frammento);
```

### Eventi

**addEventListener e removeEventListener:**

```javascript
function gestisciClick(evento) {
  console.log("Cliccato!", evento.target);
}

const bottone = document.getElementById("btn");
bottone.addEventListener("click", gestisciClick);

// Per rimuovere, serve un riferimento alla stessa funzione
bottone.removeEventListener("click", gestisciClick);
```

**Proprietà dell'oggetto Event:**

```javascript
elemento.addEventListener("click", function (e) {
  e.target;        // l'elemento che ha originato l'evento
  e.currentTarget; // l'elemento a cui è collegato il listener (può essere diverso da target)
  e.type;          // "click"
  e.timeStamp;     // quando è avvenuto l'evento
  e.clientX;       // posizione X del mouse rispetto al viewport
  e.clientY;       // posizione Y del mouse rispetto al viewport
});
```

**Fasi dell'evento — capture, target, bubble:** gli eventi nel DOM attraversano tre fasi. Prima **scendono** dall'elemento radice verso il target (capturing), poi raggiungono il **target**, infine **risalgono** dal target verso la radice (bubbling). Per default, i listener ascoltano nella fase di bubbling.

```javascript
// Terzo parametro true per ascoltare in fase di capturing
document.getElementById("esterno").addEventListener("click", () => {
  console.log("Esterno — capturing");
}, true);

document.getElementById("interno").addEventListener("click", () => {
  console.log("Interno — bubbling");
});
```

**Event delegation:** invece di aggiungere un listener a ogni elemento figlio, se ne aggiunge uno all'elemento padre. Questo pattern è efficiente e gestisce automaticamente gli elementi aggiunti dinamicamente.

```javascript
document.getElementById("lista-todo").addEventListener("click", (e) => {
  // Verifica che il click sia avvenuto su un elemento con la classe "elimina"
  if (e.target.matches(".elimina")) {
    const li = e.target.closest("li");
    li.remove();
  }

  if (e.target.matches(".completa")) {
    e.target.closest("li").classList.toggle("completato");
  }
});
```

**preventDefault() e stopPropagation():**

```javascript
// preventDefault — impedisce il comportamento predefinito
document.getElementById("form-login").addEventListener("submit", (e) => {
  e.preventDefault(); // impedisce l'invio del form e il ricaricamento della pagina
  // Gestione personalizzata dell'invio
});

// stopPropagation — impedisce la propagazione verso altri elementi
document.getElementById("modale").addEventListener("click", (e) => {
  e.stopPropagation(); // il click non raggiunge lo sfondo
});
```

**Custom events:**

```javascript
// Creare e dispatchare eventi personalizzati
const eventoPersonalizzato = new CustomEvent("prodottoAggiunto", {
  detail: { id: 42, nome: "Laptop", prezzo: 999 },
  bubbles: true,    // l'evento risale il DOM
  cancelable: true  // può essere cancellato con preventDefault
});

document.getElementById("carrello").addEventListener("prodottoAggiunto", (e) => {
  console.log(`Aggiunto: ${e.detail.nome} — ${e.detail.prezzo}€`);
});

document.getElementById("btn-aggiungi").dispatchEvent(eventoPersonalizzato);
```

**Eventi comuni di riferimento:**

- **Mouse:** `click`, `dblclick`, `mouseover`, `mouseout`, `mouseenter` (non fa bubbling), `mouseleave` (non fa bubbling), `mousedown`, `mouseup`, `contextmenu`.
- **Tastiera:** `keydown`, `keyup` (nota: `keypress` è deprecato).
- **Form:** `input` (ad ogni modifica), `change` (alla perdita del focus dopo una modifica), `submit`, `focus`, `blur`, `reset`.
- **Documento/finestra:** `DOMContentLoaded` (DOM pronto, prima del caricamento di immagini e CSS), `load` (tutto caricato), `scroll`, `resize`, `beforeunload`.
- **Touch:** `touchstart`, `touchmove`, `touchend`, `touchcancel`.

---

## ES6+ Moderno e Moduli

### Funzionalita ES6+

**Template literal:** stringhe delimitazioni da backtick che supportano interpolazione e multilinea.

```javascript
const nome = "Renan";
const multilinea = `
  Ciao ${nome},
  questo testo rispetta
  la formattazione su più righe.
`;

// Tagged template literal
function evidenzia(strings, ...valori) {
  return strings.reduce((risultato, str, i) => {
    return risultato + str + (valori[i] ? `<mark>${valori[i]}</mark>` : "");
  }, "");
}
const risultato = evidenzia`Benvenuto ${nome}, hai ${3} messaggi`;
// "Benvenuto <mark>Renan</mark>, hai <mark>3</mark> messaggi"
```

**Destructuring — array, object, annidato:**

```javascript
// Array destructuring
const [primo, secondo, ...resto] = [10, 20, 30, 40, 50];
// primo = 10, secondo = 20, resto = [30, 40, 50]

// Scambio di variabili senza variabile temporanea
let a = 1, b = 2;
[a, b] = [b, a]; // a = 2, b = 1

// Object destructuring con rinomina e valori di default
const risposta = { status: 200, dati: { utenti: [] }, errore: null };
const { status: codiceStato, dati: { utenti }, messaggio = "OK" } = risposta;
// codiceStato = 200, utenti = [], messaggio = "OK"

// Destructuring annidato
const configurazione = {
  server: { host: "localhost", porta: 3000 },
  database: { url: "mongodb://localhost", nome: "app" }
};
const { server: { host, porta }, database: { nome: nomeDb } } = configurazione;
// host = "localhost", porta = 3000, nomeDb = "app"
```

**Optional chaining (`?.`):** consente di accedere in sicurezza a proprietà profondamente annidate senza verificare manualmente l'esistenza di ogni livello.

```javascript
const utente = { profilo: { indirizzo: { citta: "Milano" } } };

// Senza optional chaining
const citta1 = utente && utente.profilo && utente.profilo.indirizzo && utente.profilo.indirizzo.citta;

// Con optional chaining
const citta2 = utente?.profilo?.indirizzo?.citta; // "Milano"
const cap = utente?.profilo?.indirizzo?.cap;       // undefined (nessun errore)

// Funziona anche con metodi e array
const risultato = utente?.metodoInesistente?.(); // undefined
const elemento = arr?.[0]; // accesso sicuro al primo elemento
```

**Nullish coalescing (`??`):** restituisce l'operando destro solo se quello sinistro è `null` o `undefined` (a differenza di `||` che considera anche `0`, `""` e `false` come valori da sostituire).

```javascript
const porta = 0;
console.log(porta || 3000); // 3000 (0 è falsy)
console.log(porta ?? 3000); // 0 (0 non è null né undefined)

const nome = "";
console.log(nome || "Anonimo"); // "Anonimo"
console.log(nome ?? "Anonimo"); // ""
```

**Logical assignment operators (ES2021):**

```javascript
let a = null;
a ??= "default";   // a = "default" (assegna solo se a è null/undefined)

let b = 0;
b ||= 10;          // b = 10 (assegna se b è falsy)

let c = "valore";
c &&= "nuovo";     // c = "nuovo" (assegna solo se c è truthy)
```

### ES Modules

I moduli ES nativi consentono di organizzare il codice in file separati con import ed export espliciti.

```javascript
// math.js — Named export
export const PI = 3.14159;
export function somma(a, b) { return a + b; }
export function moltiplica(a, b) { return a * b; }

// logger.js — Default export
export default class Logger {
  log(messaggio) { console.log(`[LOG] ${messaggio}`); }
  errore(messaggio) { console.error(`[ERRORE] ${messaggio}`); }
}

// app.js — Import
import Logger from "./logger.js";                    // default import
import { somma, PI } from "./math.js";               // named import
import { moltiplica as moltiplica } from "./math.js"; // con alias
import * as math from "./math.js";                    // import namespace

const logger = new Logger();
logger.log(`PI vale ${PI}`);
logger.log(`2 + 3 = ${somma(2, 3)}`);
```

**Dynamic import — `import()`:** consente di caricare moduli in modo asincrono, utile per il code-splitting e il caricamento condizionale.

```javascript
async function caricaModulo(tipo) {
  if (tipo === "grafico") {
    const { renderGrafico } = await import("./moduli/grafico.js");
    renderGrafico(dati);
  } else if (tipo === "tabella") {
    const { renderTabella } = await import("./moduli/tabella.js");
    renderTabella(dati);
  }
}

// Utile anche per il lazy loading nell'HTML
// <script type="module"> nel tag script abilita i moduli ES nel browser
```

**Pattern dei moduli:** i moduli ES sostituiscono i vecchi pattern come il Revealing Module Pattern e le IIFE per l'incapsulamento del codice, offrendo un sistema nativo di dipendenze e una chiara separazione tra codice pubblico ed interno.

### Iteratori e Symbol

**Symbol.iterator** definisce il protocollo di iterazione. Qualsiasi oggetto con un metodo `[Symbol.iterator]()` che restituisce un oggetto con un metodo `next()` è un iterabile.

```javascript
// Iterabile personalizzato — intervallo di numeri
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

const numeri = new Intervallo(1, 5);
for (const n of numeri) {
  console.log(n); // 1, 2, 3, 4, 5
}

// Spread funziona con gli iterabili
console.log([...new Intervallo(1, 3)]); // [1, 2, 3]
```

**Iterabili built-in:** String, Array, Map, Set, TypedArray e NodeList implementano tutti il protocollo iterabile. Sono utilizzabili con `for...of`, spread operator, destructuring e `Array.from()`.

```javascript
// for...of funziona con qualsiasi iterabile
for (const carattere of "Ciao") {
  console.log(carattere); // "C", "i", "a", "o"
}

for (const [chiave, valore] of new Map([["a", 1], ["b", 2]])) {
  console.log(chiave, valore); // "a" 1, "b" 2
}
```

---

## Event Loop

L'event loop e il concetto fondamentale che consente a JavaScript di essere **single-threaded** pur gestendo operazioni asincrone in modo efficiente. Comprendere il suo funzionamento è essenziale per scrivere codice asincrono corretto.

### Call Stack

Il call stack (pila di chiamate) è una struttura LIFO (Last In, First Out) dove JavaScript tiene traccia dell'esecuzione delle funzioni. Quando una funzione viene chiamata, un frame viene aggiunto in cima allo stack. Quando la funzione restituisce un valore, il frame viene rimosso.

```javascript
function terza() { console.log("terza"); }
function seconda() { terza(); }
function prima() { seconda(); }
prima();

// Call stack (dal basso verso l'alto):
// 1. prima()
// 2. seconda()   (aggiunta sopra prima)
// 3. terza()     (aggiunta sopra seconda)
// 4. console.log (aggiunta sopra terza, eseguita, rimossa)
// 3. terza()     (completata, rimossa)
// 2. seconda()   (completata, rimossa)
// 1. prima()     (completata, rimossa)
// Stack vuoto
```

### Task Queue (Macrotask)

Le callback di operazioni come `setTimeout`, `setInterval`, eventi del DOM e I/O vengono inserite nella **task queue** (coda dei macrotask). L'event loop prende una task dalla coda e la esegue solo quando il call stack e vuoto.

### Microtask Queue

Le microtask hanno **priorita superiore** rispetto ai macrotask. La coda dei microtask viene svuotata completamente prima di passare al prossimo macrotask. Le microtask includono: callback di Promise (`.then`, `.catch`, `.finally`), `queueMicrotask()` e `MutationObserver`.

### requestAnimationFrame

`requestAnimationFrame` viene eseguito prima del prossimo repaint del browser, tipicamente a 60fps. Non appartiene ne alla coda dei macrotask ne a quella dei microtask, ma ha una propria coda che viene processata tra i cicli di rendering.

### setTimeout / setInterval

`setTimeout(fn, 0)` non esegue la funzione immediatamente — la inserisce nella task queue, che viene processata solo dopo che il call stack e vuoto e tutte le microtask sono state completate. Il ritardo minimo effettivo e di circa 4ms nei browser moderni per i timer annidati.

```javascript
console.log("1 — sincrono");

setTimeout(() => console.log("2 — macrotask (setTimeout)"), 0);

Promise.resolve().then(() => console.log("3 — microtask (Promise)"));

queueMicrotask(() => console.log("4 — microtask (queueMicrotask)"));

console.log("5 — sincrono");

// Output garantito:
// 1 — sincrono
// 5 — sincrono
// 3 — microtask (Promise)
// 4 — microtask (queueMicrotask)
// 2 — macrotask (setTimeout)
```

### Visualizzazione dell'ordine di esecuzione

Ecco un esempio piu complesso che illustra l'interazione tra tutte le code:

```javascript
console.log("A — sincrono");

setTimeout(() => {
  console.log("B — macrotask 1");
  Promise.resolve().then(() => console.log("C — microtask dentro macrotask 1"));
}, 0);

setTimeout(() => {
  console.log("D — macrotask 2");
}, 0);

Promise.resolve()
  .then(() => {
    console.log("E — microtask 1");
    return Promise.resolve();
  })
  .then(() => console.log("F — microtask 2"));

queueMicrotask(() => console.log("G — microtask 3"));

console.log("H — sincrono");

// Ordine di esecuzione:
// A — sincrono          (call stack)
// H — sincrono          (call stack)
// E — microtask 1       (coda microtask)
// G — microtask 3       (coda microtask)
// F — microtask 2       (coda microtask, generata dalla catena di E)
// B — macrotask 1       (coda macrotask)
// C — microtask dentro macrotask 1  (microtask generata dentro B)
// D — macrotask 2       (coda macrotask)
```

La regola fondamentale: **codice sincrono → tutte le microtask → un macrotask → tutte le microtask → prossimo macrotask → ...** e cosi via.

### Interazione con il Rendering Pipeline del Browser

Nel browser, l'event loop non gestisce solo codice JavaScript — coordina anche il rendering della pagina. Il ciclo completo di un frame (a ~60fps, ogni ~16.6ms) segue questo ordine:

1. **Macrotask** — esegue un macrotask dalla coda (timer, eventi I/O, eventi DOM)
2. **Microtask** — svuota completamente la coda dei microtask
3. **requestAnimationFrame** — esegue le callback rAF registrate
4. **Style/Layout/Paint** — il browser ricalcola stili, layout e ridisegna il frame
5. **requestIdleCallback** — se rimane tempo nel frame, esegue le callback idle

Questo ordine ha implicazioni pratiche importanti:

```javascript
// requestAnimationFrame — sincronizzato con il rendering
// Ideale per animazioni fluide e letture del layout
function animazione() {
  elemento.style.transform = `translateX(${posizione}px)`;
  posizione += 2;
  if (posizione < 300) {
    requestAnimationFrame(animazione);
  }
}
requestAnimationFrame(animazione);

// requestIdleCallback — lavoro a bassa priorità nel tempo residuo del frame
// Ideale per analytics, pre-fetching, lavoro differibile
requestIdleCallback((deadline) => {
  while (deadline.timeRemaining() > 0 && codaPendente.length > 0) {
    elaboraElemento(codaPendente.shift());
  }
}, { timeout: 2000 }); // timeout: esegui comunque entro 2 secondi
```

### Starvation e Long Task

**Microtask starvation:** poiché la coda dei microtask viene svuotata completamente prima di passare al prossimo macrotask o al rendering, un ciclo infinito di microtask blocca l'interfaccia utente.

```javascript
// PERICOLO: starvation — blocca il rendering indefinitamente
function cicloInfinito() {
  Promise.resolve().then(cicloInfinito);
}
// cicloInfinito(); // NON FARE: il browser si blocca

// Le microtask possono generare altre microtask, e TUTTE devono
// essere completate prima che il browser possa renderizzare
```

**Long Task:** qualsiasi task che blocca il main thread per più di 50ms è considerata una "long task" e degrada l'interattività (INP, Time to Interactive). La Long Tasks API consente di monitorarle:

```javascript
const osservatore = new PerformanceObserver((lista) => {
  for (const entry of lista.getEntries()) {
    console.warn(`Long Task: ${entry.duration.toFixed(1)}ms`, entry);
  }
});
osservatore.observe({ type: "longtask", buffered: true });

// Strategia: spezzare il lavoro pesante in chunk con yield al main thread
async function elaboraPesante(elementi) {
  for (let i = 0; i < elementi.length; i++) {
    elaboraElemento(elementi[i]);

    // Ogni 100 elementi, cede il controllo al main thread
    if (i % 100 === 0) {
      await new Promise(resolve => setTimeout(resolve, 0));
    }
  }
}
```

### queueMicrotask — Quando e perché usarlo

`queueMicrotask()` è il modo standard per accodare una microtask senza creare una Promise. È più leggero di `Promise.resolve().then()` e ha una semantica più chiara sull'intento.

```javascript
// Caso d'uso: garantire consistenza nell'ordine di esecuzione
// di callback che possono essere sincrone o asincrone
function caricaDati(chiave, callback) {
  const cachato = cache.get(chiave);
  if (cachato) {
    // Senza queueMicrotask, la callback verrebbe eseguita sincronamente,
    // creando inconsistenza con il caso asincrono
    queueMicrotask(() => callback(cachato));
  } else {
    fetch(`/api/${chiave}`)
      .then(r => r.json())
      .then(dati => {
        cache.set(chiave, dati);
        callback(dati);
      });
  }
}
```

---

## Best Practices

1. **Usa `const` per default, `let` quando serve riassegnare, mai `var`.** La costanza del binding aiuta a ragionare sul codice. `var` introduce complessita inutile con il suo scope di funzione e l'hoisting.

2. **Usa sempre `===` e `!==` al posto di `==` e `!=`.** L'uguaglianza stretta evita le regole di coercion implicita che sono fonte di bug sottili e difficili da diagnosticare. L'unica eccezione ragionevole e `valore == null` per controllare contemporaneamente `null` e `undefined`.

3. **Preferisci le arrow function per callback e funzioni anonime.** Le arrow function sono piu concise e, soprattutto, ereditano il `this` lessicale, eliminando una delle fonti piu comuni di errori in JavaScript. Usa le function declaration per le funzioni con nome al livello di modulo.

4. **Sfrutta il destructuring per estrarre valori da oggetti e array.** Il destructuring rende il codice piu leggibile e dichiarativo. Combinato con valori di default, riduce la necessita di controlli manuali di esistenza.

5. **Valida e sanitizza sempre l'input dell'utente, specialmente prima di inserirlo nel DOM.** Non usare mai `innerHTML` con dati non fidati. Preferisci `textContent` per il testo semplice e crea gli elementi programmaticamente con `createElement` per strutture HTML complesse.

6. **Usa la event delegation invece di aggiungere listener individuali a molti elementi.** Aggiungere un singolo listener al contenitore padre e filtrare per `e.target` e piu performante, richiede meno memoria e gestisce automaticamente gli elementi aggiunti dinamicamente.

7. **Organizza il codice in moduli ES con import/export espliciti.** I moduli nativi offrono incapsulamento, gestione chiara delle dipendenze, analisi statica per il tree-shaking e un modo standard di strutturare applicazioni di qualsiasi dimensione.

8. **Comprendi l'event loop e la differenza tra microtask e macrotask.** Sapere in quale ordine vengono eseguite le operazioni asincrone e fondamentale per evitare race condition, blocchi dell'interfaccia utente e comportamenti inattesi.

9. **Usa `Optional chaining` (`?.`) e `Nullish coalescing` (`??`) per accessi sicuri.** Questi operatori moderni eliminano lunghe catene di controlli condizionali e distinguono correttamente tra valori assenti (`null`/`undefined`) e valori legittimamente falsy come `0` o `""`.

10. **Scrivi codice immutabile quando possibile.** Preferisci `toSorted`, `toReversed`, `map`, `filter` e lo spread operator ai metodi mutanti come `sort`, `reverse` e `splice`. L'immutabilita riduce gli effetti collaterali, semplifica il debugging e rende il codice piu prevedibile, specialmente nelle applicazioni complesse con stato condiviso.

---

## ES2024/ES2025 — Nuove Funzionalità

Le specifiche ECMAScript 2024 (ES15) e ECMAScript 2025 (ES16) introducono funzionalità che semplificano pattern comuni, migliorano la gestione asincrona e aprono la strada a una manipolazione più moderna di date, dati e metaprogrammazione. Di seguito le aggiunte più rilevanti.

### Object.groupBy e Map.groupBy (ES2024)

Il raggruppamento di elementi di un array è un'operazione estremamente comune — basti pensare al raggruppamento di prodotti per categoria, utenti per ruolo, o log per livello di severità. Prima di ES2024, la soluzione idiomatica era un `reduce` manuale:

```javascript
// Pre-ES2024: reduce manuale
const prodotti = [
  { nome: "Laptop", categoria: "elettronica", prezzo: 999 },
  { nome: "Cuffie", categoria: "elettronica", prezzo: 79 },
  { nome: "Sedia", categoria: "arredamento", prezzo: 250 },
  { nome: "Scrivania", categoria: "arredamento", prezzo: 400 },
];

const perCategoria = prodotti.reduce((acc, p) => {
  (acc[p.categoria] ??= []).push(p);
  return acc;
}, {});
```

Con ES2024 esiste un metodo statico dedicato:

```javascript
// ES2024: Object.groupBy — restituisce un oggetto con prototipo null
const raggruppati = Object.groupBy(prodotti, p => p.categoria);
// {
//   elettronica: [{ nome: "Laptop", ... }, { nome: "Cuffie", ... }],
//   arredamento: [{ nome: "Sedia", ... }, { nome: "Scrivania", ... }]
// }

// Map.groupBy — restituisce una Map, utile con chiavi non-stringa
const perFasciaPrezzo = Map.groupBy(prodotti, p => p.prezzo > 200 ? "alto" : "basso");
perFasciaPrezzo.get("alto");  // [Laptop, Sedia, Scrivania]
perFasciaPrezzo.get("basso"); // [Cuffie]
```

`Object.groupBy` restituisce un oggetto con prototipo `null` (nessun metodo ereditato da `Object.prototype`), rendendo il risultato sicuro come dizionario. `Map.groupBy` è preferibile quando le chiavi di raggruppamento non sono stringhe o quando serve preservare l'ordine di inserimento con semantica Map.

### Promise.withResolvers (ES2024)

Prima di ES2024, creare una Promise con resolve/reject controllabili dall'esterno richiedeva un pattern verboso e soggetto a errori:

```javascript
// Pre-ES2024: pattern manuale
let resolve, reject;
const promise = new Promise((res, rej) => {
  resolve = res;
  reject = rej;
});
// resolve e reject sono ora disponibili fuori dal constructor
```

`Promise.withResolvers()` elimina il boilerplate:

```javascript
// ES2024: Promise.withResolvers
const { promise, resolve, reject } = Promise.withResolvers();

// Caso d'uso: wrapper di un event emitter
function aspettaEvento(emitter, evento, timeoutMs = 5000) {
  const { promise, resolve, reject } = Promise.withResolvers();

  const timer = setTimeout(() => {
    emitter.removeListener(evento, handler);
    reject(new Error(`Timeout: evento "${evento}" non ricevuto in ${timeoutMs}ms`));
  }, timeoutMs);

  function handler(dati) {
    clearTimeout(timer);
    resolve(dati);
  }

  emitter.once(evento, handler);
  return promise;
}
```

Questo pattern è particolarmente utile per code asincrone, pool di risorse, adattatori di API basate su callback e qualsiasi scenario dove il punto di risoluzione della Promise è separato dal punto di creazione.

### Temporal API (Stage 3 — Proposta avanzata)

La Temporal API è una proposta in Stage 3 (candidata alla standardizzazione) che rivoluziona la gestione di date, orari e fusi orari in JavaScript. L'oggetto `Date` nativo ha difetti ben documentati: parsing ambiguo, mutabilità, assenza di supporto per fusi orari e aritmetica calendaria inaffidabile. Temporal introduce tipi immutabili, separazione netta tra date di calendario, orari, istanti e valori con fuso orario.

```javascript
// NOTA: richiede polyfill (temporal-polyfill) — il supporto nativo nei browser
// è ancora dietro flag sperimentali (stato: maggio 2025)

// Temporal.PlainDate — data di calendario senza ora e senza fuso orario
const data = Temporal.PlainDate.from("2025-06-15");
const traUnMese = data.add({ months: 1 }); // 2025-07-15 (immutabile)

// Temporal.PlainTime — orario senza data
const ora = Temporal.PlainTime.from("14:30:00");

// Temporal.PlainDateTime — data + ora senza fuso orario
const dataOra = Temporal.PlainDateTime.from("2025-06-15T14:30:00");

// Temporal.ZonedDateTime — data + ora + fuso orario
const riunione = Temporal.ZonedDateTime.from({
  timeZone: "Europe/Rome",
  year: 2025,
  month: 6,
  day: 15,
  hour: 14,
  minute: 30,
});

// Temporal.Instant — punto assoluto nel tempo (come un timestamp)
const adesso = Temporal.Now.instant();
const unix = adesso.epochMilliseconds;

// Temporal.Duration — durata con aritmetica precisa
const durata = Temporal.Duration.from({ hours: 2, minutes: 30 });
const totaleMinuti = durata.total({ unit: "minutes" }); // 150

// Confronto tra fusi orari — risolve il problema DST
const roma = Temporal.ZonedDateTime.from("2025-03-30T02:30[Europe/Rome]");
const tokio = roma.withTimeZone("Asia/Tokyo");
// Conversione corretta con gestione automatica dell'ora legale
```

I tipi principali di Temporal sono: `Instant` (punto assoluto nel tempo), `ZonedDateTime` (istante + fuso orario + calendario), `PlainDate`, `PlainTime`, `PlainDateTime` (valori "di parete" senza fuso), `PlainYearMonth`, `PlainMonthDay` e `Duration`. Tutti sono immutabili — ogni operazione restituisce un nuovo oggetto.

### Decoratori (ES2025)

I decoratori standardizzati forniscono una sintassi dichiarativa per modificare il comportamento di classi, metodi, accessor e proprietà. La proposta TC39 definisce un'API coerente che sostituisce le implementazioni non standard di Babel e TypeScript experimental decorators.

```javascript
// Decoratore di metodo: logging automatico
function log(target, context) {
  const nomeMetodo = context.name;
  return function (...args) {
    console.log(`[LOG] ${nomeMetodo}(${args.join(", ")})`);
    const risultato = target.call(this, ...args);
    console.log(`[LOG] ${nomeMetodo} → ${risultato}`);
    return risultato;
  };
}

// Decoratore di metodo: memoization
function memo(target, context) {
  const cache = new Map();
  return function (...args) {
    const chiave = JSON.stringify(args);
    if (cache.has(chiave)) return cache.get(chiave);
    const risultato = target.call(this, ...args);
    cache.set(chiave, risultato);
    return risultato;
  };
}

class Calcolatore {
  @log
  somma(a, b) {
    return a + b;
  }

  @memo
  fibonacci(n) {
    if (n <= 1) return n;
    return this.fibonacci(n - 1) + this.fibonacci(n - 2);
  }
}

const calc = new Calcolatore();
calc.somma(3, 4);     // Log: somma(3, 4) → 7
calc.fibonacci(40);   // Calcolato una volta, poi servito dalla cache
```

I decoratori ricevono due argomenti: il `target` (il valore decorato) e un oggetto `context` con metadati come `name`, `kind` (il tipo: `"method"`, `"class"`, `"field"`, `"accessor"`, `"getter"`, `"setter"`) e `access` (per leggere/scrivere il valore). Possono restituire un nuovo valore che sostituisce l'originale.

**Stato attuale:** i decoratori sono in Stage 3 e utilizzabili tramite Babel (`@babel/plugin-proposal-decorators` con opzione `version: "2023-11"`) o TypeScript 5.0+ con `"experimentalDecorators": false` (la nuova semantica TC39, diversa dai legacy decorators).

### Pipeline Operator `|>` (Stage 2 — Proposta)

L'operatore pipeline è una proposta in Stage 2 (non ancora standardizzata) che migliora la leggibilità delle composizioni di funzioni. La proposta attuale segue la semantica "Hack-style", dove `%` (o un altro token placeholder) rappresenta il valore in transito.

```javascript
// Senza pipeline — lettura dall'interno verso l'esterno
const risultato = formatta(arrotonda(filtra(caricaDati(), soglia), 2));

// Con pipeline (proposta Hack-style) — lettura da sinistra a destra
const risultato = caricaDati()
  |> filtra(%, soglia)
  |> arrotonda(%, 2)
  |> formatta(%);

// Esempio pratico con trasformazione di stringhe
const slug = titolo
  |> %.trim()
  |> %.toLowerCase()
  |> %.replace(/\s+/g, "-")
  |> %.replace(/[^a-z0-9-]/g, "")
  |> `articolo-${%}`;
```

**Stato attuale:** Stage 2 (maggio 2025). Non utilizzabile in produzione senza transpiler. Babel supporta la proposta tramite `@babel/plugin-proposal-pipeline-operator` con l'opzione `{ proposal: "hack", topicToken: "%" }`. La proposta potrebbe subire modifiche significative prima della standardizzazione.

### Altre funzionalità ES2024/ES2025 di rilievo

**`RegExp` flag `v` (unicodeSets) — ES2024:** il flag `v` sostituisce il flag `u` aggiungendo supporto per operazioni sugli insiemi di caratteri Unicode (intersezione `&&`, differenza `--`, unione), proprietà di stringa Unicode e classi di caratteri annidate.

```javascript
// Intersezione: lettere greche che sono anche maiuscole
const grecoMaiuscolo = /[\p{Script=Greek}&&\p{Uppercase_Letter}]/v;
grecoMaiuscolo.test("Σ"); // true
grecoMaiuscolo.test("σ"); // false

// Differenza: cifre decimali tranne lo zero
const cifreSenzaZero = /[\p{Decimal_Number}--0]/v;
cifreSenzaZero.test("5"); // true
cifreSenzaZero.test("0"); // false
```

**`Atomics.waitAsync` — ES2024:** versione asincrona di `Atomics.wait`, utile nel main thread dove `Atomics.wait` sincrono è bloccato.

**`ArrayBuffer.prototype.resize` e `ArrayBuffer.prototype.transfer` — ES2024:** consentono di ridimensionare buffer in-place e trasferire la proprietà di un buffer senza copiare i dati.

**`Set` methods — ES2025:** nuovi metodi per operazioni insiemistiche: `union`, `intersection`, `difference`, `symmetricDifference`, `isSubsetOf`, `isSupersetOf`, `isDisjointFrom`.

```javascript
const a = new Set([1, 2, 3, 4]);
const b = new Set([3, 4, 5, 6]);

a.union(b);              // Set {1, 2, 3, 4, 5, 6}
a.intersection(b);       // Set {3, 4}
a.difference(b);         // Set {1, 2}
a.symmetricDifference(b); // Set {1, 2, 5, 6}
a.isSubsetOf(b);          // false
a.isDisjointFrom(new Set([7, 8])); // true
```

**`Iterator.prototype` helpers — ES2025:** metodi lazy su iteratori nativi (`map`, `filter`, `take`, `drop`, `flatMap`, `reduce`, `forEach`, `toArray`, `some`, `every`, `find`).

```javascript
// Lazy evaluation — i valori vengono processati uno alla volta
function* numeriNaturali() {
  let n = 1;
  while (true) yield n++;
}

const primiDieciPari = numeriNaturali()
  .filter(n => n % 2 === 0)
  .take(10)
  .toArray();
// [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
```

**`RegExp.escape` — ES2025:** metodo statico che esegue l'escape di caratteri speciali in una stringa per l'uso sicuro in espressioni regolari dinamiche.

```javascript
const inputUtente = "prezzo (EUR) [2024]";
const pattern = new RegExp(RegExp.escape(inputUtente));
// Equivalente a /prezzo \(EUR\) \[2024\]/
// Previene injection accidentale in pattern regex
```

---

## Gestione degli Errori — Pattern Avanzati

La gestione degli errori è un aspetto cruciale della robustezza del codice. JavaScript offre diversi meccanismi, dal classico `try/catch` a pattern più sofisticati ispirati alla programmazione funzionale.

### try/catch/finally — Pattern completi

```javascript
// Pattern base con gestione granulare
async function caricaRisorsa(url) {
  let risposta;
  try {
    risposta = await fetch(url);
    if (!risposta.ok) {
      throw new Error(`HTTP ${risposta.status}: ${risposta.statusText}`);
    }
    return await risposta.json();
  } catch (errore) {
    if (errore instanceof TypeError) {
      // Errore di rete (nessuna connessione, DNS fallito, CORS)
      console.error(`Errore di rete per ${url}:`, errore.message);
    } else if (errore instanceof SyntaxError) {
      // Risposta non è JSON valido
      console.error(`Risposta non valida da ${url}:`, errore.message);
    } else {
      // Errore HTTP o altro
      console.error(`Errore durante il caricamento di ${url}:`, errore.message);
    }
    return null;
  } finally {
    // Eseguito sempre, sia in caso di successo sia di errore
    console.log(`Richiesta a ${url} completata`);
  }
}
```

### Error.cause (ES2022)

`Error.cause` consente di annidare errori preservando il contesto originale. È fondamentale per il debugging in catene di chiamate profonde.

```javascript
async function salvaUtente(dati) {
  try {
    const validati = validaInput(dati);
    return await database.insert(validati);
  } catch (errore) {
    throw new Error("Impossibile salvare l'utente", { cause: errore });
  }
}

// Nel punto di cattura finale
try {
  await salvaUtente(formData);
} catch (errore) {
  console.error(errore.message);       // "Impossibile salvare l'utente"
  console.error(errore.cause.message); // "Violazione vincolo UNIQUE su email"
  // La causa può essere annidata a più livelli
  console.error(errore.cause.cause);   // errore originale del driver DB
}
```

### Errori personalizzati

Creare classi di errore specifiche migliora la gestione e il debugging.

```javascript
class ErroreApplicazione extends Error {
  constructor(messaggio, { codice, contesto, causa } = {}) {
    super(messaggio, { cause: causa });
    this.name = "ErroreApplicazione";
    this.codice = codice;
    this.contesto = contesto;
    this.timestamp = new Date().toISOString();
  }
}

class ErroreValidazione extends ErroreApplicazione {
  constructor(campo, valore, regola) {
    super(`Validazione fallita per "${campo}": ${regola}`, {
      codice: "VALIDATION_ERROR",
      contesto: { campo, valore, regola },
    });
    this.name = "ErroreValidazione";
  }
}

class ErroreAutorizzazione extends ErroreApplicazione {
  constructor(risorsa, azione) {
    super(`Non autorizzato: ${azione} su ${risorsa}`, {
      codice: "AUTHORIZATION_ERROR",
      contesto: { risorsa, azione },
    });
    this.name = "ErroreAutorizzazione";
  }
}

// Uso
function validaEmail(email) {
  if (typeof email !== "string" || !email.includes("@")) {
    throw new ErroreValidazione("email", email, "deve contenere @");
  }
}
```

### Result Pattern (ispirato a Rust)

Il Result Pattern evita le eccezioni per errori attesi, restituendo un oggetto che rappresenta successo o fallimento. È particolarmente utile per funzioni che possono fallire in modo prevedibile.

```javascript
// Result type semplice
function ok(valore) { return { ok: true, valore }; }
function err(errore) { return { ok: false, errore }; }

function parseJSON(testo) {
  try {
    return ok(JSON.parse(testo));
  } catch (e) {
    return err(`JSON non valido: ${e.message}`);
  }
}

function validaEta(input) {
  const eta = Number(input);
  if (Number.isNaN(eta)) return err("Non è un numero");
  if (eta < 0 || eta > 150) return err("Età fuori intervallo (0-150)");
  return ok(eta);
}

// Uso: nessun try/catch necessario per errori attesi
const risultato = parseJSON(inputUtente);
if (risultato.ok) {
  elaboraDati(risultato.valore);
} else {
  mostraErrore(risultato.errore);
}

// Composizione di Result
function registraUtente(dati) {
  const emailResult = validaEmail(dati.email);
  if (!emailResult.ok) return emailResult;

  const etaResult = validaEta(dati.eta);
  if (!etaResult.ok) return etaResult;

  return ok({ email: emailResult.valore, eta: etaResult.valore });
}
```

---

## Espressioni Regolari Avanzate

Le espressioni regolari in JavaScript hanno ricevuto miglioramenti significativi nelle versioni recenti dello standard, trasformandole da uno strumento basilare a un sistema potente per l'elaborazione testuale.

### Named Capture Groups (ES2018)

I gruppi di cattura nominati rendono le regex auto-documentanti e il codice di estrazione più leggibile.

```javascript
const patternData = /(?<anno>\d{4})-(?<mese>\d{2})-(?<giorno>\d{2})/;
const match = patternData.exec("2025-06-15");
const { anno, mese, giorno } = match.groups;
// anno = "2025", mese = "06", giorno = "15"

// In replace, i gruppi nominati si riferiscono con $<nome>
const isoToEuropeo = "2025-06-15".replace(
  /(?<a>\d{4})-(?<m>\d{2})-(?<g>\d{2})/,
  "$<g>/$<m>/$<a>"
);
// "15/06/2025"
```

### Lookbehind Assertions (ES2018)

Completano le lookahead assertions consentendo di verificare cosa precede il match senza includerlo nel risultato.

```javascript
// Lookbehind positivo: (?<=...) — il pattern deve essere preceduto da...
const prezzi = "€100 $200 €300 £400";
const soloEuro = prezzi.match(/(?<=€)\d+/g); // ["100", "300"]

// Lookbehind negativo: (?<!...) — il pattern NON deve essere preceduto da...
const nonDollaro = prezzi.match(/(?<!\$)\d+/g); // ["100", "00", "300", "400"]
// Nota: "00" catturato perché le cifre dopo $ non sono precedute da $
```

### Flag `s` (dotAll) e Flag `d` (hasIndices)

```javascript
// Flag s — il punto (.) matcha anche \n
const multilinea = /inizio.+fine/s;
multilinea.test("inizio\nfine"); // true (senza 's' sarebbe false)

// Flag d — restituisce gli indici di inizio/fine di ogni cattura
const pattern = /(?<parola>\w+)/d;
const risultato = pattern.exec("ciao mondo");
risultato.indices[0];          // [0, 4] — indici del match completo
risultato.indices.groups.parola; // [0, 4] — indici del gruppo nominato
```

### Pattern regex comuni in produzione

```javascript
// Validazione email (semplificata — per validazione completa usare una libreria)
const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

// Estrazione di tutti i link da HTML
const linkRegex = /href="(?<url>https?:\/\/[^"]+)"/g;
const html = '<a href="https://esempio.it">Link</a>';
for (const { groups } of html.matchAll(linkRegex)) {
  console.log(groups.url); // "https://esempio.it"
}

// matchAll — restituisce un iteratore di tutti i match (ES2020)
const testo = "Errore 404: pagina non trovata. Errore 500: server.";
const errori = [...testo.matchAll(/Errore (?<codice>\d+): (?<desc>[^.]+)/g)];
errori.map(m => m.groups); // [{ codice: "404", desc: "pagina non trovata" }, ...]
```

### String.prototype.replaceAll e metodi correlati

`replaceAll` (ES2021) sostituisce tutte le occorrenze di una stringa senza richiedere il flag `g` su una regex. `match`, `matchAll`, `search`, `split` e `replace` accettano tutti regex come argomento.

```javascript
const testo = "foo-bar-baz-foo";

// replaceAll con stringa — sostituisce tutte le occorrenze
testo.replaceAll("foo", "qux"); // "qux-bar-baz-qux"

// replaceAll con regex — richiede il flag g
testo.replaceAll(/foo/g, "qux"); // "qux-bar-baz-qux"

// replace con funzione di sostituzione — per trasformazioni dinamiche
"camelCase".replace(/[A-Z]/g, (lettera) => `_${lettera.toLowerCase()}`);
// "camel_case"

// split con regex — per tokenizzazione complessa
"uno, due;   tre|quattro".split(/[,;|]\s*/);
// ["uno", "due", "tre", "quattro"]
```

### Costruzione sicura di regex dinamiche

Quando si costruiscono regex a partire da input utente, è fondamentale eseguire l'escape dei caratteri speciali per prevenire injection accidentali. Con ES2025, `RegExp.escape()` risolve questo problema in modo nativo. In assenza del supporto nativo, è necessario implementare l'escape manualmente.

```javascript
// Pre-ES2025: escape manuale
function escapeRegExp(stringa) {
  return stringa.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

const termineUtente = "prezzo (EUR)";
const regexSicura = new RegExp(escapeRegExp(termineUtente), "i");
regexSicura.test("Il prezzo (EUR) è 42"); // true
```

---

## Symbol e Well-Known Symbols

I Symbol, introdotti in ES6, sono valori primitivi unici e immutabili. Oltre ai Symbol creati dal programmatore, JavaScript definisce dei **well-known Symbols** che personalizzano il comportamento interno del linguaggio.

### Symbol come chiavi di proprietà

I Symbol garantiscono l'unicità delle chiavi, eliminando il rischio di collisioni di nomi — fondamentale per librerie, plugin e metadati.

```javascript
// Due symbol con la stessa descrizione sono comunque diversi
const s1 = Symbol("id");
const s2 = Symbol("id");
console.log(s1 === s2); // false

// I Symbol non appaiono in for...in, Object.keys, JSON.stringify
const utente = {
  nome: "Ada",
  [Symbol("ruolo")]: "admin",
  [Symbol("sessione")]: "abc123",
};
Object.keys(utente);                    // ["nome"]
Object.getOwnPropertySymbols(utente);   // [Symbol(ruolo), Symbol(sessione)]
Reflect.ownKeys(utente);                // ["nome", Symbol(ruolo), Symbol(sessione)]
```

### Symbol.for — Registro globale

`Symbol.for(chiave)` crea o recupera un Symbol dal registro globale condiviso. Due chiamate con la stessa chiave restituiscono lo stesso Symbol, anche tra diversi realm (es. iframe, Web Worker).

```javascript
const globale1 = Symbol.for("app.evento.click");
const globale2 = Symbol.for("app.evento.click");
console.log(globale1 === globale2); // true

Symbol.keyFor(globale1); // "app.evento.click"
Symbol.keyFor(Symbol("locale")); // undefined — non è nel registro globale
```

### Well-Known Symbols

I well-known Symbols sono proprietà statiche di `Symbol` che controllano operazioni fondamentali del linguaggio:

```javascript
// Symbol.iterator — definisce il protocollo di iterazione (già visto sopra)
// Symbol.asyncIterator — definisce il protocollo di iterazione asincrona

// Symbol.toPrimitive — controlla la conversione a tipo primitivo
class Valuta {
  constructor(importo, codice) {
    this.importo = importo;
    this.codice = codice;
  }

  [Symbol.toPrimitive](hint) {
    if (hint === "number") return this.importo;
    if (hint === "string") return `${this.importo} ${this.codice}`;
    return this.importo; // default
  }
}
const prezzo = new Valuta(42.50, "EUR");
console.log(+prezzo);       // 42.5 (hint "number")
console.log(`${prezzo}`);   // "42.5 EUR" (hint "string")
console.log(prezzo + 10);   // 52.5 (hint "default")

// Symbol.hasInstance — personalizza il comportamento di instanceof
class NumeroPositivo {
  static [Symbol.hasInstance](valore) {
    return typeof valore === "number" && valore > 0;
  }
}
console.log(42 instanceof NumeroPositivo);  // true
console.log(-1 instanceof NumeroPositivo);  // false

// Symbol.toStringTag — personalizza Object.prototype.toString
class MioSet {
  get [Symbol.toStringTag]() { return "MioSet"; }
}
console.log(Object.prototype.toString.call(new MioSet())); // "[object MioSet]"

// Symbol.species — controlla il tipo restituito dai metodi derivati
class ArraySpeciale extends Array {
  static get [Symbol.species]() { return Array; }
}
const speciale = new ArraySpeciale(1, 2, 3);
const filtrato = speciale.filter(n => n > 1);
console.log(filtrato instanceof ArraySpeciale); // false
console.log(filtrato instanceof Array);         // true

// Symbol.isConcatSpreadable — controlla il comportamento con Array.concat
const nonSpreadable = [4, 5, 6];
nonSpreadable[Symbol.isConcatSpreadable] = false;
console.log([1, 2, 3].concat(nonSpreadable)); // [1, 2, 3, [4, 5, 6]]
```

---

## Proxy e Reflect

Proxy e Reflect sono gli strumenti di metaprogrammazione di JavaScript. Un `Proxy` avvolge un oggetto e intercetta le operazioni fondamentali (lettura, scrittura, cancellazione, chiamata di funzione), mentre `Reflect` fornisce i metodi corrispondenti per eseguire il comportamento originale in modo sicuro.

### Creazione di un Proxy

Un Proxy riceve un oggetto `target` e un `handler` con delle **trappole** (trap): funzioni che intercettano operazioni specifiche.

```javascript
const handler = {
  get(target, prop, receiver) {
    console.log(`Lettura di "${String(prop)}"`);
    return Reflect.get(target, prop, receiver);
  },
  set(target, prop, valore, receiver) {
    console.log(`Scrittura di "${String(prop)}" = ${valore}`);
    return Reflect.set(target, prop, valore, receiver);
  },
  deleteProperty(target, prop) {
    console.log(`Cancellazione di "${String(prop)}"`);
    return Reflect.deleteProperty(target, prop);
  },
};

const dati = new Proxy({}, handler);
dati.nome = "Renan";   // Log: Scrittura di "nome" = Renan
console.log(dati.nome); // Log: Lettura di "nome" → "Renan"
delete dati.nome;       // Log: Cancellazione di "nome"
```

### Pattern pratici con Proxy

**Validazione automatica dei tipi:**

```javascript
function creaValidato(schema) {
  return new Proxy({}, {
    set(target, prop, valore) {
      if (!(prop in schema)) {
        throw new Error(`Proprietà sconosciuta: "${prop}"`);
      }
      const tipo = schema[prop];
      if (typeof valore !== tipo) {
        throw new TypeError(`"${prop}" deve essere ${tipo}, ricevuto ${typeof valore}`);
      }
      return Reflect.set(target, prop, valore);
    },
  });
}

const utente = creaValidato({ nome: "string", eta: "number", attivo: "boolean" });
utente.nome = "Ada";   // OK
utente.eta = 30;       // OK
// utente.eta = "trenta"; // TypeError: "eta" deve essere number
// utente.telefono = "123"; // Error: Proprietà sconosciuta: "telefono"
```

**Oggetto reattivo (pattern alla base di Vue.js 3):**

```javascript
function reattivo(target, callback) {
  return new Proxy(target, {
    set(obj, prop, valore) {
      const vecchio = obj[prop];
      const risultato = Reflect.set(obj, prop, valore);
      if (vecchio !== valore) {
        callback(prop, vecchio, valore);
      }
      return risultato;
    },
  });
}

const stato = reattivo({ contatore: 0 }, (prop, vecchio, nuovo) => {
  console.log(`${prop}: ${vecchio} → ${nuovo}`);
  // Qui si aggiornerebbe il DOM
});
stato.contatore++;  // Log: contatore: 0 → 1
```

**Proprietà con valori di default:**

```javascript
const conDefault = new Proxy({}, {
  get(target, prop) {
    return prop in target ? target[prop] : `[${prop} non definito]`;
  },
});
conDefault.nome = "Ada";
console.log(conDefault.nome);    // "Ada"
console.log(conDefault.cognome); // "[cognome non definito]"
```

### Reflect API

`Reflect` fornisce 13 metodi statici che corrispondono alle trappole del Proxy. A differenza degli operatori tradizionali, i metodi di `Reflect` restituiscono valori booleani di successo/fallimento invece di lanciare eccezioni.

```javascript
const obj = { x: 1 };

// Reflect vs operatori tradizionali
Reflect.has(obj, "x");           // true — equivalente a "x" in obj
Reflect.ownKeys(obj);            // ["x"] — combina Object.keys + Symbol
Reflect.defineProperty(obj, "y", { value: 2 }); // true/false, non lancia eccezioni
Reflect.apply(Math.max, null, [1, 2, 3]); // 3 — equivalente a Math.max.apply(null, [1,2,3])
Reflect.construct(Date, [2025, 5, 15]);   // equivalente a new Date(2025, 5, 15)
```

### Le 13 trappole del Proxy

Un handler Proxy può intercettare 13 operazioni fondamentali, ciascuna corrispondente a un metodo di `Reflect`:

| Trappola | Operazione intercettata | Esempio trigger |
|---|---|---|
| `get` | Lettura di proprietà | `obj.prop`, `obj["prop"]` |
| `set` | Scrittura di proprietà | `obj.prop = valore` |
| `has` | Operatore `in` | `"prop" in obj` |
| `deleteProperty` | Operatore `delete` | `delete obj.prop` |
| `apply` | Chiamata di funzione | `fn()`, `fn.call()`, `fn.apply()` |
| `construct` | Operatore `new` | `new Classe()` |
| `getPrototypeOf` | `Object.getPrototypeOf` | `Object.getPrototypeOf(obj)` |
| `setPrototypeOf` | `Object.setPrototypeOf` | `Object.setPrototypeOf(obj, proto)` |
| `isExtensible` | `Object.isExtensible` | `Object.isExtensible(obj)` |
| `preventExtensions` | `Object.preventExtensions` | `Object.preventExtensions(obj)` |
| `getOwnPropertyDescriptor` | `Object.getOwnPropertyDescriptor` | Descrittore proprietà |
| `defineProperty` | `Object.defineProperty` | Definizione proprietà |
| `ownKeys` | `Object.keys`, `Reflect.ownKeys` | Enumerazione chiavi |

**Invarianti del Proxy:** le trappole devono rispettare vincoli di coerenza (invariants) imposti dalla specifica ECMAScript. Ad esempio, la trappola `get` non può restituire un valore diverso da quello reale se la proprietà del target è non-writable e non-configurable. Queste invarianti garantiscono che i Proxy non possano violare le garanzie fondamentali del linguaggio.

**Pattern: Proxy revocabile** per accesso temporaneo a risorse:

```javascript
const { proxy, revoke } = Proxy.revocable({ segreto: "dati-sensibili" }, {
  get(target, prop) {
    console.log(`Accesso a "${String(prop)}"`);
    return Reflect.get(target, prop);
  },
});

proxy.segreto;  // "dati-sensibili" — funziona normalmente
revoke();       // revoca il proxy
// proxy.segreto; // TypeError: Cannot perform 'get' on a proxy that has been revoked
// Utile per token di accesso temporaneo, sessioni, API con scadenza
```

**Pattern: Proxy su funzione con trappola `apply`:**

```javascript
function creaThrottled(fn, intervalloMs) {
  let ultimaChiamata = 0;
  return new Proxy(fn, {
    apply(target, thisArg, args) {
      const adesso = Date.now();
      if (adesso - ultimaChiamata >= intervalloMs) {
        ultimaChiamata = adesso;
        return Reflect.apply(target, thisArg, args);
      }
    },
  });
}

const salvaThrottled = creaThrottled(salvaDati, 1000);
// salvaThrottled(dati) — eseguita al massimo una volta al secondo
```

---

## WeakRef e FinalizationRegistry

Oltre a `WeakMap` e `WeakSet` (già trattati nella sezione Strutture Dati), JavaScript offre `WeakRef` e `FinalizationRegistry` per scenari avanzati di gestione della memoria.

### WeakRef — Riferimenti deboli espliciti

`WeakRef` crea un riferimento debole a un oggetto. Il riferimento non impedisce al garbage collector di liberare l'oggetto quando non ci sono più riferimenti forti.

```javascript
// Cache con scadenza automatica via garbage collection
class CacheDebole {
  #cache = new Map();

  set(chiave, valore) {
    this.#cache.set(chiave, new WeakRef(valore));
  }

  get(chiave) {
    const ref = this.#cache.get(chiave);
    if (!ref) return undefined;

    const valore = ref.deref(); // restituisce l'oggetto o undefined se raccolto
    if (valore === undefined) {
      this.#cache.delete(chiave); // pulizia della entry stale
    }
    return valore;
  }
}

let oggettoPesante = { dati: new ArrayBuffer(10 * 1024 * 1024) }; // 10 MB
const cache = new CacheDebole();
cache.set("buffer", oggettoPesante);

console.log(cache.get("buffer")); // { dati: ArrayBuffer(10485760) }
oggettoPesante = null; // l'unico riferimento forte è rimosso
// In un momento futuro (non deterministico), cache.get("buffer") → undefined
```

### FinalizationRegistry — Callback post-garbage-collection

`FinalizationRegistry` registra una callback che viene invocata quando un oggetto viene raccolto dal garbage collector. Utile per il cleanup di risorse esterne associate a oggetti JavaScript.

```javascript
const registro = new FinalizationRegistry((valoreMantenuto) => {
  console.log(`Oggetto con ID "${valoreMantenuto}" raccolto dal GC`);
  // Qui si libererebbero risorse esterne (handle di file, connessioni, ecc.)
});

function creaRisorsa(id) {
  const risorsa = { id, dati: new ArrayBuffer(1024 * 1024) };
  registro.register(risorsa, id); // id è il "held value" passato alla callback
  return risorsa;
}

let r = creaRisorsa("risorsa-42");
r = null; // Eventualmente: "Oggetto con ID "risorsa-42" raccolto dal GC"
```

**Avvertenze critiche:** il garbage collector non è deterministico — la callback potrebbe essere invocata molto dopo la rimozione del riferimento, o mai durante la vita del programma. Non usare `WeakRef` o `FinalizationRegistry` per logica di business critica. Preferire sempre il cleanup esplicito (pattern `dispose()` o `using` con Explicit Resource Management). Questi strumenti sono indicati per cache opzionali, diagnostica e ottimizzazione della memoria in scenari specifici.

---

## Iteratori e Generatori Avanzati

La sezione ES6+ ha introdotto il protocollo iteratore e gli iterabili personalizzati. Qui approfondiamo i generatori, la delegazione con `yield*` e gli iteratori asincroni.

### Funzioni generatore — Controllo di flusso lazy

Una funzione generatore (`function*`) produce un iteratore che genera valori on-demand con `yield`. L'esecuzione si sospende a ogni `yield` e riprende alla successiva chiamata di `.next()`.

```javascript
function* intervallo(inizio, fine, passo = 1) {
  for (let i = inizio; i <= fine; i += passo) {
    yield i;
  }
}

// Lazy: i valori vengono calcolati solo quando richiesti
const gen = intervallo(1, 1000000);
console.log(gen.next()); // { value: 1, done: false }
console.log(gen.next()); // { value: 2, done: false }
// Non consuma memoria per tutti i milioni di valori

// Comunicazione bidirezionale con next(valore)
function* accumulatore() {
  let totale = 0;
  while (true) {
    const valore = yield totale;
    if (valore === null) return totale; // return termina il generatore
    totale += valore;
  }
}

const acc = accumulatore();
acc.next();      // { value: 0, done: false } — prima chiamata avvia il generatore
acc.next(10);    // { value: 10, done: false }
acc.next(20);    // { value: 30, done: false }
acc.next(null);  // { value: 30, done: true }
```

### yield* — Delegazione a sotto-generatori

`yield*` delega l'iterazione a un altro iterabile o generatore, componendo generatori in modo modulare.

```javascript
function* cifre() { yield* [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]; }
function* lettereMinuscole() {
  for (let c = 97; c <= 122; c++) yield String.fromCharCode(c);
}
function* lettereMaiuscole() {
  for (let c = 65; c <= 90; c++) yield String.fromCharCode(c);
}

function* caratteriAlfanumerici() {
  yield* cifre();
  yield* lettereMinuscole();
  yield* lettereMaiuscole();
}

// Traversal ricorsivo di alberi con yield*
function* visitaAlbero(nodo) {
  yield nodo.valore;
  if (nodo.figli) {
    for (const figlio of nodo.figli) {
      yield* visitaAlbero(figlio);
    }
  }
}

const albero = {
  valore: 1,
  figli: [
    { valore: 2, figli: [{ valore: 4 }, { valore: 5 }] },
    { valore: 3, figli: [{ valore: 6 }] },
  ],
};
console.log([...visitaAlbero(albero)]); // [1, 2, 4, 5, 3, 6]
```

### Generatori asincroni e for-await-of

I generatori asincroni (`async function*`) combinano la lazy evaluation dei generatori con le operazioni asincrone. Si iterano con `for await...of`.

```javascript
// Paginazione automatica con generatore asincrono
async function* paginazioneAPI(urlBase, perPagina = 10) {
  let pagina = 1;
  let haProssima = true;

  while (haProssima) {
    const risposta = await fetch(`${urlBase}?page=${pagina}&limit=${perPagina}`);
    const dati = await risposta.json();

    for (const elemento of dati.risultati) {
      yield elemento;
    }

    haProssima = dati.prossimaPagina !== null;
    pagina++;
  }
}

// Consumo: una pagina alla volta, on-demand
for await (const utente of paginazioneAPI("https://api.esempio.it/utenti")) {
  console.log(utente.nome);
  if (utente.nome === "target") break; // interrompe lazy, nessuna pagina superflua
}

// Stream di eventi del server (SSE / WebSocket)
async function* streamEventi(url) {
  const eventSource = new EventSource(url);
  const { promise, resolve } = Promise.withResolvers();
  const coda = [];

  eventSource.onmessage = (evento) => {
    coda.push(JSON.parse(evento.data));
    resolve();
  };

  try {
    while (true) {
      await promise;
      while (coda.length > 0) {
        yield coda.shift();
      }
    }
  } finally {
    eventSource.close();
  }
}
```

---

## Structured Clone Algorithm

L'algoritmo di clonazione strutturata è il meccanismo interno usato dal browser per copiare valori complessi in diversi contesti: `postMessage` (Web Workers, iframe), IndexedDB, e la funzione globale `structuredClone()` introdotta nei browser moderni e in Node.js 17+.

### structuredClone — Deep copy nativa

`structuredClone()` crea una copia profonda di un valore, supportando tipi che `JSON.parse(JSON.stringify())` non gestisce.

```javascript
const originale = {
  data: new Date("2025-01-01"),
  dati: new Uint8Array([1, 2, 3]),
  regex: /pattern/gi,
  mappa: new Map([["chiave", "valore"]]),
  insieme: new Set([1, 2, 3]),
  annidato: { profondo: { valore: 42 } },
  // Gestisce anche riferimenti circolari
};
originale.circolare = originale;

const copia = structuredClone(originale);

// Copia profonda verificata
console.log(copia.data instanceof Date);        // true
console.log(copia.data !== originale.data);      // true (oggetto diverso)
console.log(copia.annidato.profondo.valore);     // 42
console.log(copia.circolare === copia);           // true (circolarità preservata)
console.log(copia.mappa.get("chiave"));          // "valore"
```

### Confronto tra metodi di copia

| Metodo | Profondità | Riferimenti circolari | Tipi speciali | Funzioni |
|---|---|---|---|---|
| `{ ...obj }` / `Object.assign` | Shallow | No | No | Copia ref |
| `JSON.parse(JSON.stringify())` | Deep | Errore | Perde Date, Map, Set, RegExp, undefined | Perse |
| `structuredClone()` | Deep | Sì | Date, Map, Set, RegExp, ArrayBuffer, Blob | Errore (DataCloneError) |
| lodash `_.cloneDeep()` | Deep | Sì | La maggior parte | Copia |

### Tipi non clonabili con structuredClone

Non tutti i tipi JavaScript sono compatibili con l'algoritmo di clonazione strutturata. Lanciano `DataCloneError`:

- **Funzioni** e closure
- **Elementi DOM** (`HTMLElement`, `Node`)
- **Proxy** — gli oggetti Proxy non sono clonabili
- **Symbol** — i Symbol come chiavi o valori non sono supportati
- **WeakMap** e **WeakSet**
- **Promise** — le promise non sono clonabili

```javascript
// Trasferimento (transfer) — sposta la proprietà del buffer senza copiare
const buffer = new ArrayBuffer(1024);
const copia = structuredClone(buffer, { transfer: [buffer] });
console.log(buffer.byteLength);  // 0 — il buffer originale è stato svuotato
console.log(copia.byteLength);   // 1024 — i dati sono stati trasferiti
```

---

## Web Workers e SharedArrayBuffer

JavaScript è single-threaded, ma i Web Workers consentono di eseguire codice in thread separati, evitando di bloccare il main thread (e quindi l'interfaccia utente) durante operazioni computazionalmente pesanti.

### Tipi di Worker

**Dedicated Worker:** un worker dedicato a un singolo script. Comunica con il main thread tramite `postMessage`.

```javascript
// main.js
const worker = new Worker("./worker.js");

worker.postMessage({ tipo: "calcola", dati: [1, 2, 3, 4, 5] });

worker.onmessage = (evento) => {
  console.log("Risultato dal worker:", evento.data);
};

worker.onerror = (errore) => {
  console.error("Errore nel worker:", errore.message);
};

// worker.js
self.onmessage = (evento) => {
  const { tipo, dati } = evento.data;

  if (tipo === "calcola") {
    // Operazione pesante che non blocca il main thread
    const risultato = dati.reduce((acc, n) => {
      // Simulazione calcolo pesante
      let somma = acc;
      for (let i = 0; i < 1000000; i++) { somma += n * 0.000001; }
      return somma;
    }, 0);

    self.postMessage({ tipo: "risultato", valore: risultato });
  }
};
```

**Shared Worker:** condiviso tra più tab/finestre della stessa origine. Comunica tramite `MessagePort`.

**Service Worker:** proxy di rete per caching offline, push notification e sincronizzazione in background. Vive indipendentemente dalla pagina.

### SharedArrayBuffer — Memoria condivisa

`SharedArrayBuffer` consente a main thread e worker di condividere la stessa area di memoria, senza il costo della serializzazione/copia di `postMessage`. Richiede che la pagina sia **cross-origin isolated** (intestazioni `Cross-Origin-Opener-Policy: same-origin` e `Cross-Origin-Embedder-Policy: require-corp`).

```javascript
// main.js — crea e condivide il buffer
const buffer = new SharedArrayBuffer(1024); // 1 KB di memoria condivisa
const vista = new Int32Array(buffer);

const worker = new Worker("./worker-shared.js");
worker.postMessage(buffer); // non viene copiato, viene condiviso

// worker-shared.js — accede alla stessa memoria
self.onmessage = (evento) => {
  const vista = new Int32Array(evento.data);
  vista[0] = 42; // Il main thread vede immediatamente questa modifica
};
```

### Atomics — Sincronizzazione tra thread

Senza sincronizzazione, l'accesso concorrente a `SharedArrayBuffer` causa race condition. `Atomics` fornisce operazioni atomiche (indivisibili) e primitive di sincronizzazione.

```javascript
const buffer = new SharedArrayBuffer(4);
const vista = new Int32Array(buffer);

// Operazioni atomiche — non possono essere interrotte
Atomics.store(vista, 0, 100);        // scrittura atomica
const val = Atomics.load(vista, 0);  // lettura atomica: 100
Atomics.add(vista, 0, 10);           // incremento atomico: 110
Atomics.sub(vista, 0, 5);            // decremento atomico: 105
Atomics.exchange(vista, 0, 200);     // scambia e restituisce il vecchio: 105

// Compare-and-swap — modifica solo se il valore corrente è quello atteso
Atomics.compareExchange(vista, 0, 200, 300); // se è 200, diventa 300

// wait / notify — sincronizzazione tra thread (solo nei Worker, non nel main thread)
// Worker A (in attesa):
Atomics.wait(vista, 0, 300);  // blocca finché vista[0] === 300
// Worker B (notifica):
Atomics.store(vista, 0, 400);
Atomics.notify(vista, 0, 1);  // sveglia un thread in attesa

// waitAsync — versione asincrona (utilizzabile anche nel main thread, ES2024)
const { value } = Atomics.waitAsync(vista, 0, 400);
value.then(() => console.log("Il valore è cambiato"));
```

---

## Gestione della Memoria e Garbage Collection

La gestione della memoria in JavaScript è automatica: il runtime alloca memoria quando servono nuovi valori e la libera quando non sono più raggiungibili. Comprendere questo meccanismo è essenziale per evitare memory leak e ottimizzare le prestazioni.

### Il modello di memoria JavaScript

La memoria è divisa in due aree principali:

- **Stack:** valori primitivi e riferimenti a oggetti. Accesso rapido, dimensione fissa per frame di esecuzione. Viene ripulito automaticamente quando la funzione esce dallo stack.
- **Heap:** oggetti, array, funzioni e closure. Dimensione dinamica, gestito dal garbage collector.

```javascript
// Stack: primitivi
let x = 42;       // 42 è sullo stack
let y = x;        // y riceve una copia di 42 (indipendente)

// Heap: oggetti
let a = { valore: 42 }; // l'oggetto è nell'heap, 'a' contiene un riferimento
let b = a;               // b è un altro riferimento allo stesso oggetto nell'heap
b.valore = 100;
console.log(a.valore);   // 100 — a e b puntano allo stesso oggetto
```

### Algoritmi di Garbage Collection

I motori JavaScript moderni (V8, SpiderMonkey, JavaScriptCore) usano una combinazione di strategie:

**Mark-and-Sweep (Marca e Spazza):** il GC parte dalle radici (variabili globali, stack delle chiamate, closure attive) e marca tutti gli oggetti raggiungibili. Gli oggetti non marcati vengono liberati. Questo è l'algoritmo principale.

**Generational Collection (Raccolta generazionale):** la maggior parte degli oggetti ha vita breve. Il GC divide l'heap in due generazioni: **Young Generation** (nursery) per oggetti appena creati, raccolta frequente; **Old Generation** (tenured) per oggetti sopravvissuti a più cicli, raccolta meno frequente. Gli oggetti promossi dalla young alla old generation subiscono la "tenuring".

**Incremental e Concurrent GC:** per evitare pause percettibili, i motori moderni eseguono il mark-and-sweep in modo incrementale (in piccoli passi interleaved con il codice dell'applicazione) e concorrente (in thread separati).

### Cause comuni di Memory Leak

```javascript
// 1. Listener di eventi non rimossi
class Componente {
  constructor() {
    this.handler = () => this.aggiorna();
    window.addEventListener("resize", this.handler);
  }
  distruggi() {
    window.removeEventListener("resize", this.handler); // ESSENZIALE
  }
}

// 2. Closure che catturano più del necessario
function creaHandler(datiPesanti) {
  const contesto = datiPesanti; // cattura l'intero oggetto nella closure
  return () => console.log(contesto.id);
  // MEGLIO: estrarre solo ciò che serve
  // const id = datiPesanti.id;
  // return () => console.log(id);
}

// 3. Timer non cancellati
const id = setInterval(() => {
  // Questo callback e tutto ciò che cattura resta in memoria
  aggiornaDati();
}, 1000);
// clearInterval(id); — necessario quando il componente viene rimosso

// 4. Riferimenti a elementi DOM rimossi
const cache = {};
function registraElemento(el) {
  cache[el.id] = el; // se l'elemento viene rimosso dal DOM, resta in cache
}
// Soluzione: usare WeakMap con l'elemento come chiave
```

### Strumenti di diagnostica

I browser moderni offrono strumenti potenti per analizzare l'uso della memoria:

- **Chrome DevTools > Memory:** heap snapshot per fotografare lo stato dell'heap, allocation timeline per seguire le allocazioni nel tempo, allocation sampling per profilare la memoria con overhead minimo.
- **`performance.memory`** (solo Chrome): proprietà non-standard che espone `usedJSHeapSize`, `totalJSHeapSize` e `jsHeapSizeLimit`.
- **`PerformanceObserver`** con `measure` e `mark`: per correlare uso di memoria con sezioni specifiche del codice.

---

## Internals del Motore JavaScript (V8)

V8 è il motore JavaScript sviluppato da Google, usato in Chrome, Node.js, Deno e numerosi altri contesti. Comprendere la sua architettura interna aiuta a scrivere codice che il motore può ottimizzare efficacemente.

### Pipeline di compilazione a quattro livelli

V8 utilizza una pipeline di compilazione progressiva (tiered compilation) con quattro livelli, dove il codice viene promosso a livelli di ottimizzazione superiori man mano che viene eseguito più frequentemente:

**1. Ignition (Interprete):** il codice sorgente viene analizzato dal parser, trasformato in un AST (Abstract Syntax Tree) e poi compilato in **bytecode** da Ignition. Il bytecode è una rappresentazione intermedia compatta, più veloce da generare rispetto al codice macchina. Ignition esegue il bytecode direttamente e raccoglie **feedback di tipo** (type feedback) — informazioni sui tipi effettivamente usati dalle variabili e dalle operazioni.

**2. Sparkplug (Compilatore baseline):** quando una funzione viene eseguita ripetutamente ("warm"), Sparkplug la compila direttamente dal bytecode al codice macchina nativo, senza applicare ottimizzazioni. Il risultato è codice macchina veloce da generare ma non ottimizzato. Sparkplug è stato introdotto nel 2021 per colmare il gap tra l'interprete e il compilatore ottimizzante.

**3. Maglev (Compilatore mid-tier):** introdotto in Chrome 117 (2023), Maglev è un compilatore SSA (Static Single Assignment) che opera sul bytecode con il feedback di tipo raccolto da Ignition. È circa 10 volte più lento di Sparkplug nella compilazione, ma produce codice significativamente più veloce. Occupa la posizione intermedia tra Sparkplug e TurboFan.

**4. TurboFan (Compilatore ottimizzante):** quando una funzione è "hot" (eseguita molte migliaia di volte), TurboFan la compila con ottimizzazioni aggressive: inlining di funzioni, eliminazione di codice morto, constant folding, motion di invarianti del loop, specializzazione basata sul feedback di tipo. TurboFan converte il bytecode in un grafo intermedio ("sea of nodes"), applica le ottimizzazioni e genera codice macchina altamente performante.

### Deottimizzazione (Bailout)

Se le assunzioni di tipo fatte da TurboFan vengono violate a runtime, il codice ottimizzato viene scartato e l'esecuzione torna al bytecode di Ignition — questo è il **bailout** (deottimizzazione). Le deottimizzazioni sono costose e causano cali di prestazioni.

```javascript
// Causa deottimizzazione: tipi inconsistenti
function somma(a, b) { return a + b; }
somma(1, 2);       // TurboFan specializza per numeri
somma(3, 4);       // confermato: numeri
somma("ciao", "!"); // DEOTTIMIZZAZIONE — la specializzazione numerica è invalida

// Meglio: mantenere tipi coerenti
function sommaNumeri(a, b) { return a + b; }   // sempre numeri
function concatenaStr(a, b) { return a + b; }   // sempre stringhe
```

### Hidden Classes e Inline Caches

V8 assegna una **Hidden Class** (chiamata internamente "Map") a ogni oggetto. Oggetti con la stessa struttura (stesse proprietà aggiunte nello stesso ordine) condividono la stessa Hidden Class, consentendo accessi alle proprietà veloci tramite offset fisso anziché lookup nel dizionario.

```javascript
// BUONO: tutti gli oggetti hanno la stessa Hidden Class
function creaPunto(x, y) {
  return { x, y }; // stessa struttura → stessa Hidden Class
}
const p1 = creaPunto(1, 2);
const p2 = creaPunto(3, 4);

// CATTIVO: Hidden Class diverse per la stessa "forma" logica
const q1 = { x: 1, y: 2 };
const q2 = { y: 4, x: 3 }; // ordine diverso → Hidden Class diversa!

// CATTIVO: aggiungere proprietà dopo la creazione
const r = { x: 1 };
r.y = 2; // transizione di Hidden Class, rallenta gli accessi futuri
```

**Inline Caches (IC):** nei punti di accesso alle proprietà, V8 mantiene una cache che ricorda la Hidden Class dell'ultimo oggetto visto. Se gli oggetti successivi hanno la stessa Hidden Class (monomorfico), l'accesso è estremamente veloce. Se più Hidden Class diverse passano per lo stesso punto (polimorfico), la performance degrada. Oltre 4 Hidden Class diverse, il punto diventa megamorfico e V8 cade nel lookup generico lento.

### Sviluppi recenti di V8 (2025)

- **Compile Hints (aprile 2025):** V8 consente di fornire suggerimenti espliciti al parser su quali funzioni compilare eagerly, riducendo il tempo di avvio delle applicazioni web complesse.
- **Uscita dal "Sea of Nodes" (marzo 2025):** V8 sta esplorando alternative alla rappresentazione interna "sea of nodes" di TurboFan per migliorare la velocità di compilazione e la manutenibilità del codice.
- **Mutable heap numbers (febbraio 2025):** ottimizzazione che riduce le allocazioni nell'heap per valori numerici mutabili, migliorando le prestazioni di codice numericamente intensivo.

### Consigli pratici per scrivere codice ottimizzabile da V8

Comprendere gli internals di V8 si traduce in regole pratiche:

**Mantenere tipi stabili:** la specializzazione di tipo è alla base delle ottimizzazioni di TurboFan. Funzioni chiamate sempre con gli stessi tipi di argomenti generano codice macchina ottimale. Mescolare tipi causa deottimizzazioni.

**Inizializzare tutte le proprietà nel constructor:** aggiungere proprietà dopo la creazione causa transizioni di Hidden Class. Inizializzare tutto nel constructor (anche con `undefined`) consente a V8 di stabilizzare la Hidden Class fin dall'inizio.

```javascript
// BUONO: Hidden Class stabile dall'inizio
class Punto {
  constructor(x = 0, y = 0, z = 0) {
    this.x = x;
    this.y = y;
    this.z = z; // tutte le proprietà inizializzate
  }
}

// CATTIVO: aggiunta dinamica di proprietà
class PuntoDinamico {
  constructor(x, y) {
    this.x = x;
    this.y = y;
  }
  aggiungiZ(z) {
    this.z = z; // transizione di Hidden Class → rallentamento
  }
}
```

**Evitare `delete` sulle proprietà degli oggetti:** l'operatore `delete` causa una transizione di Hidden Class all'indietro, forzando V8 a passare al modo dizionario (slow properties) per quell'oggetto. Preferire l'assegnazione a `undefined`.

```javascript
// CATTIVO: forza il passaggio a modalità dizionario
delete oggetto.proprietà;

// MEGLIO: mantiene la Hidden Class intatta
oggetto.proprietà = undefined;
```

**Usare array con tipi omogenei:** V8 ottimizza gli array in base al tipo degli elementi. Un array di soli numeri interi usa una rappresentazione compatta (SMI — Small Integer). Inserire un valore di tipo diverso (stringa, float, `undefined`) causa una transizione a un tipo di array meno efficiente, irreversibile per quell'istanza.

```javascript
// BUONO: array omogeneo di interi (SMI)
const numeri = [1, 2, 3, 4, 5];

// CATTIVO: array con "buchi" (holey)
const conBuchi = [1, , 3]; // il buco forza un tipo meno efficiente

// CATTIVO: mescolare tipi
const misto = [1, "due", 3.0, null]; // tipo più generico, accesso più lento
```

---

## Esercizi

### Esercizio 1 — Manipolazione di array e oggetti con metodi funzionali

**Obiettivo:** Padroneggiare i metodi funzionali di array e le tecniche di manipolazione immutabile degli oggetti.

- Dato un array di oggetti che rappresentano prodotti (`{ id, nome, prezzo, categoria, disponibile }`), scrivere funzioni pure per:
  - Filtrare i prodotti disponibili di una data categoria (`filter`)
  - Calcolare il prezzo medio dei prodotti filtrati (`reduce`)
  - Creare un nuovo array con prezzi scontati del 20% senza mutare l'originale (`map` + spread)
  - Raggruppare i prodotti per categoria in un oggetto (`reduce` o `Object.groupBy`)
  - Ordinare per prezzo decrescente senza mutare l'array originale (`toSorted`)
- Ogni funzione deve essere pura: nessun effetto collaterale, nessuna mutazione dell'input
- Scrivere almeno 3 test (con `console.assert` o un test runner) per verificare il comportamento

### Esercizio 2 — Closure, scope e IIFE

**Obiettivo:** Comprendere in profondita closure e scope chain attraverso implementazioni pratiche.

- Implementare una funzione `creaContatore(valoreIniziale)` che restituisce un oggetto con metodi `incrementa()`, `decrementa()`, `reset()` e `valore()` usando una closure per mantenere lo stato privato
- Implementare una funzione `memoize(fn)` che memorizza i risultati delle chiamate precedenti in una cache interna (Map) e restituisce il risultato cachato se gli argomenti sono identici
- Implementare un modulo con IIFE (Immediately Invoked Function Expression) che espone un'API pubblica per gestire una lista di task (aggiungi, rimuovi, filtra per stato, conta) mantenendo i dati privati
- Dimostrare il problema classico del `var` in un loop con `setTimeout` e la soluzione con `let` o closure
- Per ogni implementazione, spiegare con un commento quale variabile viene "catturata" dalla closure

### Esercizio 3 — Manipolazione DOM e gestione eventi

**Obiettivo:** Costruire un componente interattivo manipolando il DOM con JavaScript vanilla e applicando event delegation.

- Creare una lista di task (todo list) interattiva senza framework:
  - Input per aggiungere nuove task con validazione (non vuoto, max 100 caratteri)
  - Ogni task mostra testo, checkbox per completamento e bottone elimina
  - Filtri "Tutte", "Attive", "Completate" che nascondono/mostrano le task
  - Contatore delle task attive rimanenti, aggiornato in tempo reale
- Utilizzare un singolo event listener sul contenitore padre con event delegation (filtrare per `e.target`)
- Creare tutti gli elementi con `document.createElement()` — vietato `innerHTML` con dati utente
- Persistere le task in `localStorage` con serializzazione JSON e ricaricarle al refresh
- La navigazione completa deve funzionare da tastiera (Tab, Enter, Spazio)

### Esercizio 4 — Programmazione asincrona con Promise e async/await

**Obiettivo:** Gestire flussi asincroni complessi usando Promise e async/await con gestione errori robusta.

- Implementare una funzione `fetchConRetry(url, maxTentativi, delayMs)` che riprova la richiesta in caso di errore fino a `maxTentativi` con delay esponenziale (`delayMs * 2^tentativo`)
- Creare una funzione `caricaInParallelo(urls)` che scarica piu risorse in parallelo con `Promise.all()` e gestisce gli errori individuali con `Promise.allSettled()`
- Implementare un timeout per fetch: se la risposta non arriva entro N millisecondi, la Promise deve essere rigettata con un errore specifico (usare `Promise.race` con un timer)
- Creare una funzione `pipeline(valore, ...funzioniAsync)` che esegue una serie di funzioni asincrone in sequenza, passando il risultato di ciascuna alla successiva
- Gestire tutti gli errori con `try/catch` e loggare messaggi utili (URL, tentativo, tipo di errore)
- Testare con la API pubblica `https://jsonplaceholder.typicode.com/`

### Esercizio 5 — Mini-applicazione SPA con moduli ES

**Obiettivo:** Costruire una Single Page Application minimale usando moduli ES nativi, gestione stato e routing hash.

- Strutturare il progetto in moduli ES separati: `router.js`, `state.js`, `api.js`, `components/` (almeno 3 componenti), `utils.js`
- Implementare un router hash-based che ascolta `hashchange` e renderizza il componente corretto: Home, Lista, Dettaglio
- Creare un modulo stato centralizzato con pattern pub/sub: `getState()`, `setState(partial)`, `subscribe(listener)` — ogni modifica notifica i subscriber
- Recuperare dati da `https://jsonplaceholder.typicode.com/` (posts e users) con fetch e caching locale (evitare richieste duplicate)
- Ogni componente deve essere una funzione che riceve lo stato e restituisce un elemento DOM (non stringhe HTML)
- Gestire gli stati di caricamento (spinner), errore (messaggio utente) e vuoto (messaggio "nessun risultato")
- Aggiungere `<script type="module">` nel HTML e verificare che il tutto funzioni senza bundler

---

## Letture e Riferimenti

### Documentazione ufficiale

- **MDN Web Docs — JavaScript** — Riferimento completo per il linguaggio: sintassi, built-in objects, API del browser. <https://developer.mozilla.org/en-US/docs/Web/JavaScript> (consultato: 2026-05-24)
- **MDN Web Docs — JavaScript Guide** — Tutorial strutturato dai fondamenti alle funzionalita avanzate. <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide> (consultato: 2026-05-24)
- **ECMAScript Language Specification (ECMA-262)** — Specifica ufficiale del linguaggio JavaScript. <https://tc39.es/ecma262/> (consultato: 2026-05-24)
- **MDN Web Docs — Web APIs (DOM)** — Documentazione delle API DOM per la manipolazione del documento. <https://developer.mozilla.org/en-US/docs/Web/API/Document_Object_Model> (consultato: 2026-05-24)
- **MDN Web Docs — Fetch API** — Riferimento per l'API moderna di richieste HTTP. <https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API> (consultato: 2026-05-24)
- **TC39 Proposals** — Proposte attive per nuove funzionalita del linguaggio JavaScript. <https://github.com/tc39/proposals> (consultato: 2026-05-24)

### Libri e approfondimenti

- Flanagan D., *JavaScript: The Definitive Guide* (7th ed.), O'Reilly, 2020.
- Simpson K., *You Don't Know JS Yet* (serie), self-published, 2020.
- Haverbeke M., *Eloquent JavaScript* (4th ed.), No Starch Press, 2024.

---

## Riferimenti Incrociati

| Modulo | Relazione |
|---|---|
| [01 — HTML5](01-html5.md) | JavaScript manipola il DOM generato dal parser HTML e gestisce eventi sugli elementi |
| [02 — CSS3](02-css3.md) | JavaScript modifica dinamicamente custom properties CSS e classi per aggiornare la presentazione |
| [05 — JavaScript Avanzato](05-javascript-avanzato.md) | Approfondisce prototipi, event loop, Web Workers e metaprogrammazione introdotti qui |
| [06 — TypeScript](06-typescript.md) | TypeScript aggiunge tipizzazione statica al JavaScript fondamentale trattato in questo modulo |
| [10 — Node.js](10-nodejs.md) | Node.js esegue JavaScript lato server, riutilizzando la stessa sintassi e le stesse API del linguaggio |
| [15 — Testing Web](15-testing-web.md) | I test verificano il comportamento delle funzioni e dei componenti JavaScript |

---

## Glossario

| Termine | Definizione |
|---|---|
| **Hoisting** | Comportamento per cui le dichiarazioni di variabili (`var`) e funzioni vengono spostate all'inizio del loro scope durante la compilazione. |
| **Closure** | Funzione che mantiene un riferimento alle variabili del suo scope lessicale esterno, anche dopo che la funzione esterna ha terminato l'esecuzione. |
| **Arrow function** | Sintassi concisa per le funzioni (`() => {}`) che eredita il `this` dal contesto lessicale anziche definirne uno proprio. |
| **Destructuring** | Sintassi per estrarre valori da array (`[a, b] = arr`) o proprieta da oggetti (`{ nome, eta } = obj`) in variabili separate. |
| **Spread operator** | Operatore `...` che espande un iterabile nei suoi elementi individuali, usato per copiare array/oggetti o passare argomenti. |
| **Promise** | Oggetto che rappresenta il risultato futuro (risolto o rigettato) di un'operazione asincrona. |
| **async/await** | Sintassi che permette di scrivere codice asincrono con aspetto sincrono, dove `await` sospende l'esecuzione fino alla risoluzione della Promise. |
| **Event delegation** | Pattern che utilizza un singolo event listener su un elemento padre per gestire eventi di tutti i figli, sfruttando il bubbling. |
| **Event loop** | Meccanismo del runtime JavaScript che gestisce l'esecuzione di codice, eventi e callback in un singolo thread. |
| **Microtask** | Task ad alta priorita (Promise `.then`, `queueMicrotask`) eseguita prima del prossimo rendering e prima di qualsiasi macrotask in coda. |
| **Macrotask** | Task a priorita normale (`setTimeout`, `setInterval`, eventi I/O) processata dall'event loop dopo l'esaurimento delle microtask. |
| **Template literal** | Stringa delimitata da backtick (`` ` ``) che supporta interpolazione (`${expr}`) e multilinea senza concatenazione. |
| **Optional chaining** | Operatore `?.` che accede a proprieta annidate restituendo `undefined` anziche lanciare un errore se un valore intermedio e `null` o `undefined`. |
| **Nullish coalescing** | Operatore `??` che restituisce l'operando destro solo quando il sinistro e `null` o `undefined`, a differenza di `||` che reagisce a tutti i valori falsy. |
| **Scope chain** | Catena di ambienti lessicali attraverso cui il motore JavaScript risale per risolvere i riferimenti a variabili, dal locale al globale. |
| **Proxy** | Oggetto wrapper che intercetta e ridefinisce operazioni fondamentali (lettura, scrittura, cancellazione) su un oggetto target tramite funzioni handler dette trappole. |
| **Reflect** | Oggetto built-in che fornisce metodi statici corrispondenti alle trappole del Proxy, usato per eseguire il comportamento originale in modo sicuro. |
| **Symbol** | Tipo primitivo unico e immutabile, usato come chiave di proprietà per evitare collisioni. I well-known Symbols controllano il comportamento interno del linguaggio. |
| **WeakRef** | Riferimento debole a un oggetto che non impedisce al garbage collector di liberare la memoria occupata dall'oggetto referenziato. |
| **FinalizationRegistry** | Registro che consente di eseguire una callback quando un oggetto viene raccolto dal garbage collector, utile per il cleanup di risorse esterne. |
| **Generatore** | Funzione speciale (`function*`) che può sospendere e riprendere la propria esecuzione tramite `yield`, producendo valori on-demand (lazy evaluation). |
| **structuredClone** | Funzione globale che crea una copia profonda di un valore usando l'algoritmo di clonazione strutturata, supportando tipi complessi e riferimenti circolari. |
| **Web Worker** | Thread separato dal main thread in cui eseguire codice JavaScript pesante senza bloccare l'interfaccia utente, comunicando tramite messaggi. |
| **SharedArrayBuffer** | Buffer di memoria condiviso tra main thread e worker senza copia, che richiede `Atomics` per l'accesso sincronizzato e cross-origin isolation. |
| **Hidden Class** | Struttura interna di V8 (chiamata "Map") assegnata agli oggetti con la stessa forma, che consente accessi alle proprietà ottimizzati tramite offset fisso. |
| **Decoratore** | Funzione che modifica dichiarativamente il comportamento di classi, metodi o proprietà (proposta ES2025 Stage 3), applicata con la sintassi `@`. |
| **Result Pattern** | Pattern di gestione errori che restituisce un oggetto `{ ok, valore/errore }` anziché lanciare eccezioni, per errori attesi e prevedibili. |
| **Temporal API** | Proposta (Stage 3) che introduce tipi immutabili per date, orari e fusi orari, sostituendo l'oggetto `Date` con un'API moderna e corretta. |
| **Deottimizzazione** | Processo in cui il motore V8 scarta il codice macchina ottimizzato e torna all'interprete bytecode quando le assunzioni di tipo vengono violate a runtime. |